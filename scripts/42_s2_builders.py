#!/usr/bin/env python
"""S2 dopant builders (geometry only): unrelaxed isovalent substitutions in the 233-atom FA19Cs1Pb20I60 host
and its 232-atom V_I partner, as specified in results/objective2/s2/S2_BUILDERS_DESIGN.md (BUILDER_VERSION s2b-2;
the changes from s2b-1 are listed in section 15 of the design, "Review and fixes").

Library (section 1 of the design): build_a_molecular (GA, DMA, AA), build_a_atomic (Cs, Rb), build_b (Sr, Ca),
build_x_atomic (Cl), build_x_molecular (SCN), build (dispatch through REGISTRY), resolve_poses (the 'sampled'
set), build_paired (D_j on the host leg, D_j+V on the vacancy leg), list_sites, validate (checks V1-V10).
Output is an UNRELAXED starting structure. No calculator is created or evaluated here: no MACE, MD, relaxation,
NEB or QE. Distances, rankings and frames use ase.geometry.find_mic (true minimum image), never pp.mic.

    python scripts/42_s2_builders.py --self-test [--members all] [--report FILE]
    python scripts/42_s2_builders.py sites --host results/fa_host/pool_v3_harmonised/m30.extxyz --dopant SCN
    python scripts/42_s2_builders.py build --host results/fa_host/pool_v3_harmonised/m30.extxyz --dopant DMA \\
        --site 128 --pose sampled --out <dir outside results/objective2/dopant_shell> --allow-provisional
"""
import argparse, dataclasses, hashlib, importlib.util, itertools, json, os, sys, tempfile, time, zlib
from dataclasses import dataclass

import numpy as np
from ase import Atoms
from ase.data import atomic_numbers
from ase.geometry import find_mic
from ase.io import read, write

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import checks  # noqa: E402


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


pp = _load("pp", "22_paired_pilot.py")            # fa_molecule, build_pair, migrating_index, MIG_TAG
s29 = _load("s29", "29_dopant_shell_scan.py")     # ga_at_carbon, ref_vacancy_position (imports no model)
a07 = _load("a07", "07_fa_host_cell.py")          # _random_rotation (Shoemake quaternion, 07:208-218)

BUILDER_VERSION = "s2b-2"
DOPANT_TAG = 77                    # [M] any tag other than 0 and pp.MIG_TAG (99)
N_HOST = 233                        # FA19Cs1Pb20I60; the V_I partner has 232
SUPERCELL_P = ((-2, 1, 2), (2, 1, 2), (2, 2, -1))   # results/fa_host/fa_host_build.json "supercell_P"
B_SITE = ("Pb", "Sr", "Ca")         # B-site cations: the X frame and pb8 anchor use these ("Pb" in an undoped host)
B_Z = np.array([atomic_numbers[e] for e in B_SITE])
X_SITE = ("I", "Cl")
FA_SYMS = sorted(["C", "N", "N", "H", "H", "H", "H", "H"])

# Valence electrons per pslibrary 1.0.0 US PBE file. Pb, I, C, N, H, Cs, Sr: confirmed by archived S1 inputs.
# Cl, S, Ca, Rb: expected values, to be verified against each UPF z_valence on the node (design section 2).
VALENCE = {"Pb": 14, "I": 7, "C": 4, "N": 5, "H": 1, "Cs": 9, "Sr": 10, "Cl": 7, "S": 6, "Ca": 10, "Rb": 9}
FORMAL_UNIT = {"FA": 1, "GA": 1, "DMA": 1, "AA": 1, "Cs": 1, "Rb": 1, "Pb": 2, "Sr": 2, "Ca": 2,
               "I": -1, "Cl": -1, "SCN": -1}

# Registry (design section 2). n = (atoms in the host leg, atoms in the V leg); dval = valence-electron change.
REGISTRY = {
    "GA":  {"site": "A", "replaces": "FA", "builder": "a_molecular", "delta": {"N": 1, "H": 1},
            "n": (235, 234), "dval": 6, "centre": "retained FA C"},
    "DMA": {"site": "A", "replaces": "FA", "builder": "a_molecular", "delta": {"C": 1, "N": -1, "H": 3},
            "n": (236, 235), "dval": 2, "centre": "N"},
    "AA":  {"site": "A", "replaces": "FA", "builder": "a_molecular", "delta": {"C": 1, "H": 2},
            "n": (236, 235), "dval": 6, "centre": "C1 (amidinium)"},
    "Cs":  {"site": "A", "replaces": "FA", "builder": "a_atomic", "delta": {"C": -1, "N": -2, "H": -5, "Cs": 1},
            "n": (226, 225), "dval": -10, "centre": "Cs"},
    "Rb":  {"site": "A", "replaces": "FA", "builder": "a_atomic", "delta": {"C": -1, "N": -2, "H": -5, "Rb": 1},
            "n": (226, 225), "dval": -10, "centre": "Rb"},
    "Sr":  {"site": "B", "replaces": "Pb", "builder": "b", "delta": {"Pb": -1, "Sr": 1},
            "n": (233, 232), "dval": -4, "centre": "site"},
    "Ca":  {"site": "B", "replaces": "Pb", "builder": "b", "delta": {"Pb": -1, "Ca": 1},
            "n": (233, 232), "dval": -4, "centre": "site"},
    "Cl":  {"site": "X", "replaces": "I", "builder": "x_atomic", "delta": {"I": -1, "Cl": 1},
            "n": (233, 232), "dval": 0, "centre": "site"},
    "SCN": {"site": "X", "replaces": "I", "builder": "x_molecular", "delta": {"I": -1, "S": 1, "C": 1, "N": 1},
            "n": (235, 234), "dval": 8, "centre": "C"},
}
PROVISIONAL = {"DMA": "[U] C-N, C-N-C (cation geometry unverified)", "AA": "[S] Cannon et al. 1976 (secondary)",
               "Cl:shift": "[S] Pb-Cl 2.837 A (Poglitsch & Weber 1987, secondary)",
               "SCN": "[V] values without an archived CIF (design section 4: treat as [S]); Bondi radii [S]"}

# ---------------------------------------------------------------- geometry parameters (enter GEOM_SHA)
# Section 4 of the design. Every value carries its source there; [M] = modelling choice.
GEOM = {
    "GA": {"d_CN": 1.33, "d_NH": 1.01, "u": 0.34, "w": 0.95},        # S1 recipe 22:96-103 = 29:128-132 (frozen)
    "DMA": {"d_CN": 1.49, "a_CNC": 114.0,                            # [U] provisional
            "d_NH": 1.020, "a_HNH": 109.47,                          # host FA mean N-H [R]; tetrahedral [M]
            "d_CH": 1.094, "a_NCH": 109.47},                         # host FA mean C-H [R]; anti H, C2v [M]
    "AA": {"d_C1N": 1.307, "d_C1C2": 1.477,                          # Cannon, White & Willis 1976 [S]
           "a_NCN": 121.0, "a_NCC": 119.5,                           # [S] rounded [M]; planar CCN2
           "d_NH": 1.020, "a_CNH": 120.0, "a_HNH": 120.0,            # [R]; 120 deg as make_guanidinium (04:98-111)
           "d_CH": 1.094, "a_CCH": 109.47, "methyl_dihedral": 90.0},  # one H perpendicular to the plane [M], Cs
    "A_ion": {"offset": 0.30,                                        # displaced Cs/Rb starts along +-Q [M]
              # a displaced start may not bring the ion closer to an X than min(host A-X minimum, the centred
              # start's nearest A-X): no relaxed native Cs in the pool is closer than 4.000 A to an I [R] (s2b-2)
              "displaced_rule": "nearest A-X >= min(host_min A-X, centred nearest A-X)"},
    "Cl": {"d_PbCl": 2.837},                                         # cubic MAPbCl3 [S]; one-sided shift [M]
    "SCN": {"d_SC": 1.639, "d_CN": 1.172, "a_SCN": 180.0,            # Pb(SCN)2, COD 2106398 [V]; linear [M]
            "r_ref_S": 3.066, "r_ref_N": 2.734, "window": 0.15,      # bound contact [V] +- [M]
            "a_min": 90.0, "c_min": 3.066,                           # [M]
            # s2b-2: an end is bound iff it lies in the distance window; an in-window end with angle < a_min is
            # ambiguous coordination and the pose is rejected (design section 15, finding 3)
            "bound_rule": "distance window; in-window end with Pb-E-C < a_min rejects the pose",
            "grid_s": [-1.2, 1.2, 0.3], "grid_l": [0.0, 0.25, 0.5, 1.0, 1.5, 2.0],
            "step_psi": 15, "step_phi": 15, "step_theta": 10, "tie_A": 1e-6},
    "frames": {"x_third_b_min": 5.0, "tie_rad": 1e-9},
    "redundancy_deg": 20.0,                                          # [M], not the 29:410 tolerance
    # build_paired: |host[vi] - vpos| < vac_excl on both partner modes; relaxed partners: every inorganic atom
    # (B, X, A ions) within 2.0 A of its unrelaxed V-cell counterpart, about half the shortest host I...I (4.045 A),
    # so an index shift between two iodides is always caught [M] (s2b-2)
    "pairing": {"relaxed_inorganic_max_A": 2.0},
}
# Clash filter (design section 6): thr = f x the shortest non-bonded intermolecular contact of the class pair over
# the relaxed pool [R, 36 members]; class Y (SCN atoms) uses Bondi sums (rule below).
# s2b-2: the H-X pair is split by the heavy atom the H is bonded to. In the host only N-H donors make the short
# H...I contacts (N-H 2.571 A; C-H 2.876 A) [R], so one H-X threshold let methyl C-H sit at N-H...I distances.
# The other H pairs are set by cage spacing, not by contacts, and stay pooled over both kinds of H.
CLASH = {
    "f": 0.90, "f_w": 0.80, "floor": 0.65, "vac_excl": 1.2,
    "class_map": {"H": "H", "C": "O", "N": "O", "Cs": "A", "Rb": "A", "I": "X", "Cl": "X",
                  "Pb": "B", "Sr": "B", "Ca": "B", "S": "Y"},
    "h_split": "H-X only: HN (H bonded to N, donor) and HC (H bonded to C); other H pairs pooled",
    "host_min": {"HN-X": 2.571, "HC-X": 2.876, "H-H": 2.818, "H-O": 3.339, "H-B": 3.544, "H-A": 4.534,
                 "O-X": 3.548, "O-O": 3.995, "O-B": 4.362, "O-A": 5.198, "A-X": 4.000, "A-B": 5.342,
                 "X-X": 4.045},
    "bondi": {"H": 1.20, "C": 1.70, "N": 1.55, "S": 1.80, "I": 1.98},   # Bondi 1964 [S]
    # class Y (s2b-2): f_w x Bondi only for the hydrogen-bond pairs (acceptor ends S, N against H); every other
    # Y pair (C of SCN against H; S, C, N against organic C/N and against I) uses f x Bondi, because the closest
    # non-hydrogen-bonded host contacts lie at 0.90-1.06 of their Bondi sums (H(C)...I 0.904, N...I 1.005,
    # I...I 1.021, C...I 1.057 [R]; the N-H...I hydrogen bond is at 0.808)
    "y_rule": {"acceptor_H": "f_w", "other": "f", "acceptors": ["S", "N"]},
    "hbond_diag_A": 3.0,                    # diagnostic only: dopant N-H with an X within 3.0 A (677/684 host FA)
    "untested": ["X-B", "A-A", "B-B"],      # X-B, Y-B: section 5 rules; A-A: Cs-Cs separation recorded instead
    "Y-A": "A-X",                           # Y-A uses the A-X threshold
    "exempt": ["GA"],                       # S1 recipe reaches H-I 1.99 A: clash thresholds report only
}
CLASS_ORDER = "HOAXBY"
BOND_CUT = {("C", "N"): 1.6, ("C", "H"): 1.25, ("H", "N"): 1.25, ("C", "C"): 1.7, ("C", "S"): 2.0}  # 38:59-66; [M]


def _canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


GEOM_SHA = hashlib.sha256(_canon({"geom": GEOM, "clash": CLASH, "bond_cut": {"-".join(k): v for k, v in
                                                                            BOND_CUT.items()}}).encode()).hexdigest()


def pair_key(p, q, hsub=""):
    """Class-pair key; an H-X pair takes the H subclass ('N' or 'C', s2b-2): HN-X or HC-X."""
    k = "-".join(sorted((p, q), key=CLASS_ORDER.index))
    if k == "H-X":
        if hsub not in ("N", "C"):
            raise Refused("an H-X pair needs the H subclass (H bonded to N or to C)")
        return f"H{hsub}-X"
    return k


def thr_table():
    """Section 6 thresholds (A), thr = f x host minimum."""
    return {k: CLASH["f"] * v for k, v in CLASH["host_min"].items()}


THR = thr_table()

# Orientation classes (design section 5): body y and body x in Q coordinates; z = x cross y.
_r2, _r3, _r6 = np.sqrt(2.0), np.sqrt(3.0), np.sqrt(6.0)
CLASSES = {
    "c100f": ([1, 0, 0], [0, 1, 0]),
    "c100d": ([1, 0, 0], [0, 1 / _r2, 1 / _r2]),
    "c110a": ([1 / _r2, 1 / _r2, 0], [0, 0, 1]),
    "c110b": ([1 / _r2, 1 / _r2, 0], [1 / _r2, -1 / _r2, 0]),
    "c111m": ([1 / _r3, 1 / _r3, 1 / _r3], [1 / _r6, 1 / _r6, -2 / _r6]),
    "c111n": ([1 / _r3, 1 / _r3, 1 / _r3], [1 / _r2, -1 / _r2, 0]),
}
ORBIT_SIZE = {"c100f": 12, "c100d": 12, "c110a": 12, "c110b": 12, "c111m": 24, "c111n": 24}
C2Y = np.diag([-1.0, 1.0, -1.0])       # body-frame C2 about y (the polar axis)
C2Z = np.diag([-1.0, -1.0, 1.0])       # body-frame C2 about z (plane normal): inherit_flip = R . C2(z)
G_MOL = (np.eye(3), C2Y)               # G = C2(y) for DMA, and for the AA skeleton (methyl rotor ignored) [M]


def _o24():
    """The 24 proper signed permutation matrices, in a fixed enumeration order."""
    out = []
    for perm in itertools.permutations(range(3)):
        for sg in itertools.product((1, -1), repeat=3):
            g = np.zeros((3, 3))
            for r in range(3):
                g[r, perm[r]] = sg[r]
            if np.linalg.det(g) > 0:
                out.append(g)
    assert len(out) == 24
    return out


O24 = _o24()


class Refused(ValueError):
    """A request the builders refuse: invalid site, policy, token or flag."""


class Inadmissible(Exception):
    """A pose that fails the clash filter (V7) or, on the V leg, no longer realises its host-leg pose."""

    def __init__(self, report, msg=None):
        super().__init__(msg or report.get("reason") or "inadmissible pose")
        self.report = report


class BuildError(AssertionError):
    """A validity check other than the clash filter failed: a builder defect, never a pose property."""

    def __init__(self, report):
        bad = [k for k in sorted(report) if k.startswith("V") and isinstance(report[k], dict)
               and not report[k].get("passed", True) and k != "V7"]
        super().__init__(f"validity checks failed: {bad} " + "; ".join(str(report[k].get("reason")) for k in bad))
        self.report = report


@dataclass(frozen=True)
class Built:
    atoms: Atoms        # calc None; no constraints; arrays numbers, positions, tags only
    token: str          # registry key
    site: int           # input index of the replaced site atom: FA carbon / Pb / I
    centre: int         # dopant-centre index in atoms
    members: tuple      # every dopant atom in atoms (whole-molecule grouping)
    deleted: tuple      # sorted input indices removed
    added: tuple        # range(len(input) - len(deleted), len(atoms)), in the template's atom order
    modified: tuple     # retained input indices whose symbol or position changed (Sr, Ca, Cl)
    old_to_new: dict    # every surviving input index -> new index
    delta: dict         # exact element-count change
    pose: dict          # resolved orientation/anchor record, JSON-serialisable
    report: dict        # validity checks V1-V10


# ---------------------------------------------------------------- small geometry helpers
def mic(v, cell):
    """True minimum-image vectors (ase find_mic) for v of shape (n, 3)."""
    return find_mic(np.atleast_2d(v), cell, pbc=True)[0]


def unit(v):
    return v / np.linalg.norm(v)


def angle_deg(a, b):
    return float(np.degrees(np.arccos(np.clip(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)), -1.0, 1.0))))


def dihedral_deg(p0, p1, p2, p3):
    b0, b1, b2 = p0 - p1, p2 - p1, p3 - p2
    b1n = unit(b1)
    v, w = b0 - (b0 @ b1n) * b1n, b2 - (b2 @ b1n) * b1n
    return float(np.degrees(np.arctan2(np.cross(b1n, v) @ w, v @ w)))


def omega(R1, R2, G=G_MOL):
    """Misorientation (rad) modulo the body group G: min_h arccos((tr(R1^T R2 h) - 1) / 2)."""
    return min(float(np.arccos(np.clip((np.trace(R1.T @ R2 @ h) - 1.0) / 2.0, -1.0, 1.0))) for h in G)


def pc_frame(cell):
    """Pseudo-cubic frame Q (rows = pc axes): the polar factor U V^T of A = P^-1 . cell = U S V^T."""
    A = np.linalg.inv(np.array(SUPERCELL_P, float)) @ np.asarray(cell, float)
    U, _, Vt = np.linalg.svd(A)
    Q = U @ Vt
    if np.linalg.det(Q) < 0:
        raise Refused("pseudo-cubic frame is improper (left-handed cell)")
    return Q


def fold(pos, cell):
    """Fold appended atoms into [0,1): pos - floor(s) @ cell, then recompute s from the folded positions and
    correct, by one lattice vector, any component that round-off left at s >= 1 or s < -1e-12 (V9 tolerance).
    s2b-1 tested s - floor(s) before the subtraction, so s = 1.0 could survive within ~1e-14 of a plane."""
    inv = np.linalg.inv(cell)
    s = pos @ inv
    sh = np.floor(s)
    sh[(s - sh) >= 1.0] += 1.0
    P = pos - sh @ cell
    for _ in range(3):
        sf = P @ inv
        corr = (sf >= 1.0).astype(float) - (sf < -1e-12).astype(float)
        if not corr.any():
            return P
        P = P - corr @ cell
    raise BuildError({"V9": {"passed": False, "reason": "fold did not converge"}})


def frac(pos, cell):
    return pos @ np.linalg.inv(cell)


def _syms(at):
    return at.get_chemical_symbols()


def _b_indices(at):
    return np.flatnonzero(np.isin(at.numbers, B_Z))


def _nearest(at, i, idx):
    """find_mic vectors and distances from atom i to the atoms idx, ordered by (distance, index)."""
    v = mic(at.positions[idx] - at.positions[i], at.cell.array)
    d = np.linalg.norm(v, axis=1)
    o = np.lexsort((idx, d))
    return idx[o], v[o], d[o]


def pairwise(at, ia, ib):
    """True-MIC distance matrix between index sets ia and ib."""
    ia, ib = np.asarray(ia, int), np.asarray(ib, int)
    if not len(ia) or not len(ib):
        return np.zeros((len(ia), len(ib)))
    D = (at.positions[ib][None, :, :] - at.positions[ia][:, None, :]).reshape(-1, 3)
    return find_mic(D, at.cell.array, pbc=True)[1].reshape(len(ia), len(ib))


def h_subclass(at):
    """Per atom: 'N' or 'C' for an H (its nearest C or N by true MIC: the heavy atom it is bonded to), else ''.
    The nearest partner, not the 1.25 A cut-off, decides, so a rattled N-H (T11) keeps its class; an H with no C
    or N within 1.6 A (the 38:59-66 C-N cut-off) has no clash class in s2b-2 and is refused."""
    s = np.array(_syms(at))
    out = np.full(len(at), "", dtype="<U1")
    H = np.flatnonzero(s == "H")
    CN = np.flatnonzero((s == "C") | (s == "N"))
    if not len(H):
        return out
    if not len(CN):
        raise Refused("H atoms without any C or N partner")
    D = pairwise(at, H, CN)
    k = D.argmin(axis=1)
    dmin = D[np.arange(len(H)), k]
    if (dmin >= BOND_CUT[("C", "N")]).any():
        raise Refused(f"H {[int(h) for h in H[dmin >= BOND_CUT[('C', 'N')]]]}: no C or N within 1.6 A")
    out[H] = s[CN[k]]
    return out


# ---------------------------------------------------------------- templates (body frame; y polar, xy plane)
def _rot_axis(n, t):
    """Rotation by t (rad) about the unit axis n (Rodrigues)."""
    n = unit(np.asarray(n, float))
    K = np.array([[0, -n[2], n[1]], [n[2], 0, -n[0]], [-n[1], n[0], 0]])
    return np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * K @ K


def _rz(t):
    c, s = np.cos(t), np.sin(t)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def _ry(t):
    c, s = np.cos(t), np.sin(t)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def _methyl(Cp, ref, t_deg, d_ch, n0):
    """Three methyl H on carbon Cp: angle ref-Cp-H = t_deg, C-H = d_ch; n0 = the unit perpendicular direction of
    the first H (perpendicular to the ref-Cp axis); the others follow at +-120 deg about that axis."""
    d = unit(Cp - ref)
    t = np.radians(t_deg)
    out = []
    for tau in (0.0, 120.0, 240.0):
        ta = np.radians(tau)
        n = np.cos(ta) * n0 + np.sin(ta) * np.cross(d, n0)
        out.append(Cp + d_ch * (-np.cos(t) * d + np.sin(t) * n))
    return out


def _template_raw(token):
    if token == "DMA":
        g = GEOM["DMA"]
        al, be = np.radians(g["a_CNC"] / 2), np.radians(g["a_HNH"] / 2)
        N = np.zeros(3)
        C1 = g["d_CN"] * np.array([np.sin(al), -np.cos(al), 0.0])
        C2 = C2Y @ C1
        HN1 = g["d_NH"] * np.array([0.0, np.cos(be), np.sin(be)])
        HN2 = g["d_NH"] * np.array([0.0, np.cos(be), -np.sin(be)])
        p = C2 - N - ((C2 - N) @ unit(C1 - N)) * unit(C1 - N)      # towards C' perpendicular to the C-N axis
        H1 = _methyl(C1, N, g["a_NCH"], g["d_CH"], -unit(p))         # first H anti to C' (H-C-N-C' = 180)
        H2 = [C2Y @ h for h in H1]                                  # C2(y) image: exact C2v template
        return "NCCHHHHHHHH", np.array([N, C1, C2, HN1, HN2] + H1 + H2)
    if token == "AA":
        g = GEOM["AA"]
        al = np.radians(g["a_NCC"])
        C1 = np.zeros(3)
        C2 = g["d_C1C2"] * np.array([0.0, 1.0, 0.0])
        Na = g["d_C1N"] * np.array([-np.sin(al), np.cos(al), 0.0])
        Nb = C2Y @ Na
        b = unit(C1 - Na)
        HNa = [Na + g["d_NH"] * (_rz(np.radians(sg * g["a_CNH"])) @ b) for sg in (1, -1)]
        HNb = [C2Y @ h for h in HNa]
        n0 = _ry(0.0) @ np.array([0.0, 0.0, 1.0])                  # first methyl H along +z (dihedral 90 deg)
        HC = _methyl(C2, C1, g["a_CCH"], g["d_CH"], n0)
        return "CNNCHHHHHHH", np.array([C1, Na, Nb, C2] + HNa + HNb + HC)
    raise KeyError(token)


def template(token):
    """(symbols, body coordinates with the unweighted centroid at the origin) for DMA or AA."""
    syms, X = _template_raw(token)
    return syms, X - X.mean(axis=0)


def template_internals(token):
    """Internal coordinates of the table (design section 4): (kind, atom indices, value)."""
    if token == "DMA":
        g = GEOM["DMA"]
        L = [("d", (0, 1), g["d_CN"]), ("d", (0, 2), g["d_CN"]), ("a", (1, 0, 2), g["a_CNC"]),
             ("d", (0, 3), g["d_NH"]), ("d", (0, 4), g["d_NH"]), ("a", (3, 0, 4), g["a_HNH"]),
             ("t", (5, 1, 0, 2), 180.0), ("t", (8, 2, 0, 1), 180.0)]
        for c, hs in ((1, (5, 6, 7)), (2, (8, 9, 10))):
            L += [("d", (c, h), g["d_CH"]) for h in hs] + [("a", (0, c, h), g["a_NCH"]) for h in hs]
        return L
    if token == "AA":
        g = GEOM["AA"]
        L = [("d", (0, 1), g["d_C1N"]), ("d", (0, 2), g["d_C1N"]), ("d", (0, 3), g["d_C1C2"]),
             ("a", (1, 0, 2), g["a_NCN"]), ("a", (1, 0, 3), g["a_NCC"]), ("a", (2, 0, 3), g["a_NCC"]),
             ("t", (8, 3, 0, 1), g["methyl_dihedral"])]
        for n, hs in ((1, (4, 5)), (2, (6, 7))):
            L += [("d", (n, h), g["d_NH"]) for h in hs] + [("a", (0, n, h), g["a_CNH"]) for h in hs]
            L += [("a", (hs[0], n, hs[1]), g["a_HNH"])]
        L += [("d", (3, h), g["d_CH"]) for h in (8, 9, 10)] + [("a", (0, 3, h), g["a_CCH"]) for h in (8, 9, 10)]
        L += [("p", (0, 1, 2, 3, 4, 5, 6, 7), 0.0)]               # planar skeleton (out-of-plane distance)
        return L
    if token == "SCN":
        g = GEOM["SCN"]
        return [("d", (0, 1), g["d_SC"]), ("d", (1, 2), g["d_CN"]), ("a", (0, 1, 2), g["a_SCN"])]
    if token == "GA":
        # The recipe's w = n(NCN) x u has |w| < 1 when C-H leaves the NCN plane, so N-H and the angles vary
        # slightly between sites (about 109.7 and 140.6 deg); only C-N is fixed. V5 re-evaluates the recipe instead.
        return [("d", (0, 1), GEOM["GA"]["d_CN"])]
    return []


def measure_internals(P, spec):
    """Evaluate internal coordinates on contiguous coordinates P; returns [(kind, idx, target, value, err)]."""
    out = []
    for kind, ix, val in spec:
        if kind == "d":
            got = float(np.linalg.norm(P[ix[1]] - P[ix[0]]))
        elif kind == "a":
            got = angle_deg(P[ix[0]] - P[ix[1]], P[ix[2]] - P[ix[1]])
        elif kind == "t":
            got = abs(dihedral_deg(*(P[k] for k in ix)))
        else:                                                         # planarity: max distance from the best plane
            S = P[list(ix)] - P[list(ix)].mean(axis=0)
            got = float(np.abs(S @ np.linalg.svd(S)[2][-1]).max())
        out.append((kind, ix, float(val), got, abs(got - float(val))))
    return out


# ---------------------------------------------------------------- sites, anchors and local frames
def _bonded_unit(at, c):
    """Organic unit of carbon c by bonding (38:59-66): N < 1.6 A from C, H < 1.25 A from C or those N."""
    s = np.array(_syms(at))
    N, H = np.flatnonzero(s == "N"), np.flatnonzero(s == "H")
    ns = N[pairwise(at, [c], N)[0] < BOND_CUT[("C", "N")]]
    dh = pairwise(at, np.r_[c, ns].astype(int), H)
    hc = H[dh[0] < BOND_CUT[("C", "H")]]
    hn = [H[row < BOND_CUT[("H", "N")]] for row in dh[1:]]
    return [int(x) for x in ns], [int(x) for x in hc], [[int(x) for x in r] for r in hn]


def fa_target(at, c):
    """Check that index c is the carbon of an intact, untagged FA; return (mol, Na, Nb, H_C, v) where mol is the
    sorted 8-atom pp.fa_molecule grouping and v the find_mic vectors from C to mol (mol order)."""
    s = _syms(at)
    if not (0 <= int(c) < len(at)):
        raise Refused(f"A site {c}: index out of range")
    c = int(c)
    if s[c] != "C":
        raise Refused(f"A site {c} is {s[c]}, not an FA carbon (the native Cs and non-carbon sites are excluded)")
    mol = pp.fa_molecule(at, c)
    if sorted(s[i] for i in mol) != FA_SYMS:
        raise Refused(f"C{c} is not an intact FA unit under pp.fa_molecule: {sorted(s[i] for i in mol)}")
    tags = np.asarray(at.get_tags())
    if any(int(tags[i]) == DOPANT_TAG for i in mol):
        raise Refused(f"C{c} belongs to a dopant (tag {DOPANT_TAG})")
    ns, hc, hn = _bonded_unit(at, c)
    bonded = sorted([c] + ns + hc + [h for r in hn for h in r])
    if len(ns) != 2 or len(hc) != 1 or [len(r) for r in hn] != [2, 2] or bonded != mol:
        raise Refused(f"C{c}: bonded unit (N {ns}, H(C) {hc}, H(N) {hn}) is not the FA grouping {mol}")
    v = mic(at.positions[mol] - at.positions[c], at.cell.array)
    kn = [k for k, i in enumerate(mol) if s[i] == "N"]
    kh = [k for k, i in enumerate(mol) if s[i] == "H"]
    k_hc = min(kh, key=lambda k: (float(np.linalg.norm(v[k])), mol[k]))   # the FA's own C-H (as 29:124-126)
    return mol, kn[0], kn[1], k_hc, v


def fa_frame(v, ka, kb, khc):
    """FA frame R = [e1 e2 e3]: e1 = unit(v(Nb) - v(Na)); e2 = C-H component perpendicular to e1; e3 = e1 x e2."""
    e1 = unit(v[kb] - v[ka])
    h = v[khc]
    e2 = unit(h - (h @ e1) * e1)
    return np.column_stack([e1, e2, np.cross(e1, e2)])


def pb8(at, c):
    """C plus the mean find_mic vector to the 8 nearest B-site cations; octant test in frame Q."""
    idx, v, d = _nearest(at, c, _b_indices(at))
    v8 = v[:8]
    w = v8 @ pc_frame(at.cell.array).T
    octs = {tuple(bool(x) for x in (r > 0)) for r in w}
    return at.positions[c] + v8.mean(axis=0), len(octs) == 8, [int(x) for x in idx[:8]]


def a_anchor(at, c, mol, v, anchor):
    if anchor == "fa_centroid":
        return at.positions[c] + v.mean(axis=0)
    if anchor == "fa_carbon":
        return at.positions[c].copy()
    if anchor == "pb8_centroid":
        p, ok, idx = pb8(at, c)
        if not ok:
            raise Refused(f"C{c}: the 8 nearest Pb do not occupy the 8 octants of Q (pb8_centroid undefined)")
        return p
    raise Refused(f"unknown anchor {anchor!r}")


def x_frame(at, i):
    """X frame at iodide i: Pba < Pbb (the two nearest B, by index), a = unit(Pba -> Pbb), b from the Q axis
    cyclically after the bond axis k, projected perpendicular to a; c = a x b."""
    cell = at.cell.array
    Q = pc_frame(cell)
    bi = _b_indices(at)
    idx, v, d = _nearest(at, i, bi)
    if len(d) < 3 or d[2] <= GEOM["frames"]["x_third_b_min"]:
        raise Refused(f"X site {i}: third-nearest Pb at {d[2]:.3f} A <= {GEOM['frames']['x_third_b_min']} A")
    ka, kb = sorted((0, 1), key=lambda k: idx[k])
    va, vb = v[ka], v[kb]
    a = unit(vb - va)
    chk = mic(at.positions[idx[kb]] - at.positions[idx[ka]], cell)[0]      # find_mic(Pbb - Pba), as specified
    assert np.abs(chk - (vb - va)).max() < 1e-9, "Pb-Pb bridge is not the minimum image"
    qa = np.abs(Q @ a)
    k = int(np.argmax(qa))
    q = Q[(k + 1) % 3]
    b = unit(q - (q @ a) * a)
    return {"pba": int(idx[ka]), "pbb": int(idx[kb]), "va": va, "vb": vb, "a": a, "b": b, "c": np.cross(a, b),
            "k": k, "qa": float(qa[k]), "qa_next": float(np.sort(qa)[-2]), "d3": float(d[2]),
            "d_pbpb": float(np.linalg.norm(vb - va)), "Q": Q}


def _mig_policy(at, i, mig, mig_index):
    """Resolve the migrating iodide of this leg (explicit index, else the MIG_TAG atom) and apply the policy."""
    if mig not in ("forbid", "allow"):
        raise Refused(f"mig must be 'forbid' or 'allow', not {mig!r}")
    if mig_index is None:
        hits = np.flatnonzero(np.asarray(at.get_tags()) == pp.MIG_TAG)
        if len(hits) > 1:
            raise Refused(f"{len(hits)} atoms carry the MIG tag")
        mig_index = int(hits[0]) if len(hits) else None
    replaced = mig_index is not None and int(i) == int(mig_index)
    if replaced and mig == "forbid":
        raise Refused(f"X site {i} is the migrating iodide; refused under mig='forbid' (path/NEB use)")
    return (None if mig_index is None else int(mig_index)), bool(replaced)


def _x_target(at, i, vpos):
    """An X target is an iodide that is not the vacancy iodide. vpos is required (s2b-2): without it the
    X != vi test could not run, and a direct builder call silently substituted the vacancy iodide."""
    s = _syms(at)
    if not (0 <= int(i) < len(at)) or s[int(i)] != "I":
        raise Refused(f"X site {i} is not an iodide")
    if vpos is None:
        raise Refused("X builders need vpos (the member's vacancy position) for the X != vi test")
    dv = float(np.linalg.norm(mic(at.positions[int(i)] - vpos, at.cell.array)[0]))
    if dv < CLASH["vac_excl"]:
        raise Refused(f"X site {i} is the vacancy site (d = {dv:.3f} A from vpos)")


# ---------------------------------------------------------------- assembly
def _assemble(at, token, site, *, deleted=(), mods=None, new_syms="", new_pos=None, member_old=(),
              centre=("old", None), pose=None, wrap_new=True):
    cell = at.cell.array
    n0 = len(at)
    deleted = tuple(sorted({int(k) for k in deleted}))
    dset = set(deleted)
    keep = [k for k in range(n0) if k not in dset]
    old_to_new = {k: n for n, k in enumerate(keep)}
    numbers = at.numbers[keep].copy()
    positions = at.positions[keep].copy()
    tags = np.asarray(at.get_tags(), int)[keep].copy()
    mods = mods or {}
    for k, (sym, pos) in mods.items():
        if sym is not None:
            numbers[old_to_new[k]] = atomic_numbers[sym]
        if pos is not None:
            positions[old_to_new[k]] = pos
    for k in member_old:
        tags[old_to_new[k]] = DOPANT_TAG
    if new_syms:
        P = np.asarray(new_pos, float).reshape(-1, 3)
        if wrap_new:
            P = fold(P, cell)
        numbers = np.r_[numbers, [atomic_numbers[x] for x in new_syms]]
        positions = np.r_[positions, P]
        tags = np.r_[tags, [DOPANT_TAG] * len(new_syms)]
    atoms = Atoms(numbers=numbers, positions=positions, cell=cell.copy(), pbc=at.pbc.copy())
    atoms.set_tags(tags)
    added = tuple(range(len(keep), len(atoms)))
    kind, j = centre
    cen = old_to_new[j] if kind == "old" else len(keep) + j
    members = tuple(sorted(old_to_new[k] for k in member_old)) + added
    return Built(atoms, token, int(site), int(cen), members, deleted, added, tuple(sorted(mods)), old_to_new,
                 dict(REGISTRY[token]["delta"]), pose or {}, {})


def _finish(base, built, vpos, wrapped=True):
    rep = validate(base, built, vpos=vpos, wrapped=wrapped)
    built = dataclasses.replace(built, report=rep)
    if not rep["valid"]:
        raise BuildError(rep)
    if not rep["admissible"]:
        raise Inadmissible(rep, f"{built.token} pose {built.pose.get('name')}: {rep['V7'].get('reason')}")
    return built


def _reg(token):
    if token not in REGISTRY:
        raise Refused(f"unknown dopant token {token!r} (known: {', '.join(REGISTRY)})")
    return REGISTRY[token]


def _pose_name(token, pose):
    if isinstance(pose, dict):
        return pose["name"]
    if pose in (None, "inherit"):
        if token == "SCN":
            raise Refused("SCN has no 'inherit' pose (there is no molecular frame to inherit); name a binding class")
        return {"Cs": "centred", "Rb": "centred", "Cl": "centred", "Sr": "swap", "Ca": "swap"}.get(token, "inherit")
    return str(pose)


# ---------------------------------------------------------------- A site: molecular cations (GA, DMA, AA)
def _class_frame(name):
    y, x = (np.array(t, float) for t in CLASSES[name])
    return np.column_stack([x, y, np.cross(x, y)])


def class_orbit(name):
    """Orbit {g F : g in O} deduplicated modulo G (first member in the enumeration order of O kept)."""
    F = _class_frame(name)
    out = []
    for gi, g in enumerate(O24):
        M = g @ F
        if not any(min(np.abs(M - M2 @ h).max() for h in G_MOL) < 1e-9 for _, M2 in out):
            out.append((gi, M))
    return out


def _rank_orbit(name, R_inh, Q):
    """Orbit members by misorientation from the inherit frame; ties (< 1e-9 rad) by the enumeration of O."""
    orb = [(gi, M, omega(R_inh, Q.T @ M)) for gi, M in class_orbit(name)]
    rest, ranked = list(orb), []
    tol = GEOM["frames"]["tie_rad"]
    while rest:
        wmin = min(r[2] for r in rest)
        pick = min((r for r in rest if r[2] - wmin < tol), key=lambda r: r[0])
        ranked.append(pick); rest.remove(pick)
    return ranked


def _ga_recipe(at, c, mol, ka, kb, khc, v):
    """S1 GA recipe (22:96-103 = 29:128-132), evaluated with find_mic vectors."""
    g = GEOM["GA"]
    cpos = at.positions[c]
    nvec = [v[ka], v[kb]]
    vch = v[khc]
    n_new = cpos + vch / np.linalg.norm(vch) * g["d_CN"]
    pn = np.cross(nvec[0], nvec[1]); pn /= np.linalg.norm(pn)
    u = vch / np.linalg.norm(vch); w = np.cross(pn, u)
    h1 = n_new + (g["u"] * u + g["w"] * w) * g["d_NH"]
    h2 = n_new + (g["u"] * u - g["w"] * w) * g["d_NH"]
    return np.array([n_new, h1, h2])


def _mol_rotation(at, pose, R_inh):
    Q = pc_frame(at.cell.array)
    M = np.array(pose["M"], float)
    if pose["frame"] == "fa":
        return R_inh @ M
    if pose["frame"] == "Q":
        return Q.T @ M
    raise Refused(f"unknown pose frame {pose['frame']!r}")


def build_a_molecular(at, c, token, pose="inherit", *, anchor=None, vpos=None, wrap_new=True):
    """GA (S1 recipe), DMA or AA on the FA whose carbon is c. pose: 'inherit', 'inherit_flip', a class name
    (c100f ...; realised by the admissible orbit member nearest the inherit frame) or a resolved pose dict.
    anchor: None = fa_centroid for DMA/AA; GA has no anchor (the S1 recipe) and refuses one (s2b-2)."""
    reg = _reg(token)
    if reg["builder"] != "a_molecular":
        raise Refused(f"{token} is not an A-site molecular cation")
    mol, ka, kb, khc, v = fa_target(at, c)
    c = int(c)
    s = _syms(at)
    name = _pose_name(token, pose)
    R_inh = fa_frame(v, ka, kb, khc)
    if token == "GA":
        if name != "inherit":
            raise Refused("GA has only the S1 recipe ('inherit') in s2b-2")
        if anchor is not None:
            raise Refused(f"GA has no anchor option (the S1 recipe builds on the retained FA C); got {anchor!r}")
        new = _ga_recipe(at, c, mol, ka, kb, khc, v)
        member_old = [k for k in mol if k != mol[khc]]
        rec = {"token": "GA", "mode": "s1_recipe", "name": "inherit", "anchor": "S1 recipe (retained FA C)",
               "frame": "fa", "deleted_h_input": int(mol[khc])}
        b = _assemble(at, token, c, deleted=(mol[khc],), new_syms="NHH", new_pos=new, member_old=member_old,
                      centre=("old", c), pose=rec, wrap_new=wrap_new)
        _out_indices(b)
        return _finish(at, b, vpos, wrap_new)
    syms, body = template(token)
    anchor = anchor or "fa_centroid"
    if isinstance(pose, dict):
        cands = [dict(pose)]
        anchor = pose.get("anchor", anchor)
    elif name == "inherit":
        cands = [{"mode": "inherit", "name": "inherit", "frame": "fa", "M": np.eye(3).tolist()}]
    elif name == "inherit_flip":
        cands = [{"mode": "inherit_flip", "name": "inherit_flip", "frame": "fa", "M": C2Z.tolist()}]
    elif name in CLASSES:
        Q = pc_frame(at.cell.array)
        ranked = _rank_orbit(name, R_inh, Q)
        cands = [{"mode": "class", "name": name, "frame": "Q", "M": M.tolist(), "g_index": gi, "orbit_rank": r,
                  "orbit_size": len(ranked), "omega_inherit_deg": float(np.degrees(w))}
                 for r, (gi, M, w) in enumerate(ranked)]
    else:
        raise Refused(f"unknown pose {name!r} for {token}")
    anc = a_anchor(at, c, mol, v, anchor)
    last = None
    for k, p in enumerate(cands):
        R = _mol_rotation(at, p, R_inh)
        rec = dict(p, token=token, anchor=anchor, R_lab=R.tolist(), anchor_pos=anc.tolist(),
                   omega_inherit_deg=float(np.degrees(omega(R_inh, R))))
        if p.get("mode") == "class":
            rec["tried"] = k + 1
        b = _assemble(at, token, c, deleted=mol, new_syms=syms, new_pos=anc + body @ R.T, centre=("new", 0),
                      pose=rec, wrap_new=wrap_new)
        try:
            return _finish(at, b, vpos, wrap_new)
        except Inadmissible as e:
            last = e
    if name in CLASSES:
        why = f"{token} {name}: infeasible at site C{c} (all {len(cands)} orbit members clash)"
    else:
        why = f"{token} {name} at C{c}: {last.report['V7'].get('reason')}"
    raise Inadmissible(dict(last.report, reason=why))


# ---------------------------------------------------------------- A site: atomic ions (Cs, Rb)
A_ION_POSES = ["centred"] + [f"q{k}{sg}" for k in range(3) for sg in "+-"]


def build_a_atomic(at, c, token, pose="inherit", *, anchor=None, vpos=None, wrap_new=True):
    """Cs+ or Rb+ replacing the FA whose carbon is c: centred on the anchor (None = pb8_centroid), or displaced
    0.30 A along +-Q. A displaced start that brings the ion closer to an X than min(host A-X minimum, the
    centred start's nearest A-X) is inadmissible (s2b-2; validate, V7 rule 'A-X displaced')."""
    reg = _reg(token)
    if reg["builder"] != "a_atomic":
        raise Refused(f"{token} is not an A-site atomic ion")
    mol, ka, kb, khc, v = fa_target(at, c)
    c = int(c)
    name = _pose_name(token, pose)
    anchor = anchor or "pb8_centroid"
    if isinstance(pose, dict):
        anchor = pose.get("anchor", anchor)
    if name not in A_ION_POSES:
        raise Refused(f"unknown pose {name!r} for {token} (one of {A_ION_POSES})")
    anc = a_anchor(at, c, mol, v, anchor)
    off = np.zeros(3)
    if name != "centred":
        Q = pc_frame(at.cell.array)
        off = (1.0 if name[2] == "+" else -1.0) * GEOM["A_ion"]["offset"] * Q[int(name[1])]
    rec = {"token": token, "mode": "centred" if name == "centred" else "displaced", "name": name, "frame": "Q",
           "anchor": anchor, "anchor_pos": anc.tolist(), "offset": off.tolist()}
    b = _assemble(at, token, c, deleted=mol, new_syms=[token], new_pos=[anc + off],
                  centre=("new", 0), pose=rec, wrap_new=wrap_new)
    return _finish(at, b, vpos, wrap_new)


# ---------------------------------------------------------------- B site (Sr, Ca)
def build_b(at, pb, token, pose="inherit", *, vpos=None):
    """Sr2+ or Ca2+ on Pb index pb: symbol swap at the Pb's own position (29:376-379)."""
    reg = _reg(token)
    if reg["builder"] != "b":
        raise Refused(f"{token} is not a B-site dopant")
    pb = int(pb)
    if not (0 <= pb < len(at)) or _syms(at)[pb] != "Pb":
        raise Refused(f"B site {pb} is not a Pb")
    name = _pose_name(token, pose)
    if name != "swap":
        raise Refused(f"{token} has only the symbol-swap pose")
    rec = {"token": token, "mode": "swap", "name": "swap", "frame": "site"}
    b = _assemble(at, token, pb, mods={pb: (token, None)}, member_old=(pb,), centre=("old", pb), pose=rec)
    return _finish(at, b, vpos)


# ---------------------------------------------------------------- X site: Cl
CL_POSES = ["centred", "shift_a", "shift_b"]


def build_x_atomic(at, i, token, pose="inherit", *, mig="forbid", mig_index=None, vpos=None):
    """Cl- on iodide i: centred (symbol swap) or shifted to Pb_t + 2.837 A unit(X - Pb_t), t = a or b."""
    reg = _reg(token)
    if reg["builder"] != "x_atomic":
        raise Refused(f"{token} is not an X-site atomic ion")
    _x_target(at, i, vpos)
    i = int(i)
    name = _pose_name(token, pose)
    if name not in CL_POSES:
        raise Refused(f"unknown pose {name!r} for {token} (one of {CL_POSES})")
    mig_index, replaced = _mig_policy(at, i, mig, mig_index)
    fr = x_frame(at, i)
    x0 = at.positions[i]
    pos = None
    if name != "centred":
        vt = fr["va"] if name == "shift_a" else fr["vb"]
        pos = x0 + vt - GEOM["Cl"]["d_PbCl"] * vt / np.linalg.norm(vt)
    rec = {"token": token, "mode": "centred" if name == "centred" else "shift", "name": name, "frame": "x",
           "pb_t_input": None if name == "centred" else fr["pba" if name == "shift_a" else "pbb"],
           "mig": mig, "mig_index_input": mig_index, "replaced_migrating_iodide": replaced}
    b = _assemble(at, token, i, mods={i: (token, pos)}, member_old=(i,), centre=("old", i), pose=rec)
    _out_indices(b)
    return _finish(at, b, vpos)


def _out_indices(b):
    """Index spaces (s2b-2): every '<key>_input' index of the pose (input numbering) gets '<key>_out', its index
    in the built cell (None if that atom was deleted). s2b-1 stored only input indices, under unlabelled keys."""
    for k in [k for k in b.pose if k.endswith("_input")]:
        v = b.pose[k]
        b.pose[k[:-6] + "_out"] = None if v is None else b.old_to_new.get(int(v))


def _x_v10(fr, old_to_new):
    return {"x_frame": {"pba_input": fr["pba"], "pbb_input": fr["pbb"], "pba_out": old_to_new.get(fr["pba"]),
                        "pbb_out": old_to_new.get(fr["pbb"]), "third_b_A": round(fr["d3"], 4), "k": fr["k"],
                        "qa": round(fr["qa"], 6), "qa_next": round(fr["qa_next"], 6),
                        "d_pbpb_A": round(fr["d_pbpb"], 4)}}


# ---------------------------------------------------------------- X site: SCN
SCN_CLASSES = {1: "S:a", 2: "S:b", 3: "S:ab", 4: "N:a", 8: "N:b", 9: "SN:ab", 6: "SN:ba"}
SCN_CODE = {v: k for k, v in SCN_CLASSES.items()}
R_ENV = 8.5            # A: environment radius of the SCN search (reach 3.97 A + largest threshold 3.6 A + margin)


def scn_grid():
    g = GEOM["SCN"]
    lo, hi, st = g["grid_s"]
    sg = np.round(lo + st * np.arange(int(round((hi - lo) / st)) + 1), 12)
    lg = np.array(g["grid_l"], float)
    psi = np.arange(0, 360, g["step_psi"])
    th = np.arange(0, 181, g["step_theta"])
    ph = np.arange(0, 360, g["step_phi"])
    return sg, lg, psi, th, ph


def scn_positions(x0, fr, p):
    """S, C, N (append order) for parameters p in the X frame fr: C = X + s a + l (cos psi b + sin psi c);
    rod direction S->N u = cos th a + sin th (cos ph b + sin ph c)."""
    g = GEOM["SCN"]
    psi, th, ph = np.radians([p["psi_deg"], p["theta_deg"], p["phi_deg"]])
    a, b, c = fr["a"], fr["b"], fr["c"]
    C = x0 + p["s"] * a + p["l"] * (np.cos(psi) * b + np.sin(psi) * c)
    u = np.cos(th) * a + np.sin(th) * (np.cos(ph) * b + np.sin(ph) * c)
    return np.array([C - g["d_SC"] * u, C, C + g["d_CN"] * u])


def _y_threshold(e_sym, env_sym):
    """Threshold of an SCN atom (class Y) against an environment atom: ('sec6', thr) | ('pb', thr).
    s2b-2: f_w x Bondi only for the hydrogen-bond pairs (S or N against H); f x Bondi for every other pair
    (the C of SCN against H, and S, C, N against organic C/N and against I)."""
    cm = CLASH["class_map"]
    ce = cm.get(env_sym)
    if ce is None:
        raise Refused(f"no clash class for {env_sym}")
    if ce == "B":
        g = GEOM["SCN"]
        return "pb", (g["c_min"] if e_sym == "C" else g[f"r_ref_{e_sym}"] - g["window"])
    if ce == "A":
        return "sec6", THR[CLASH["Y-A"]]
    if ce == "H" or ce == "O" or env_sym == "I":
        yr = CLASH["y_rule"]
        fac = CLASH[yr["acceptor_H"]] if (ce == "H" and e_sym in yr["acceptors"]) else CLASH[yr["other"]]
        return "sec6", fac * (CLASH["bondi"][e_sym] + CLASH["bondi"][env_sym])
    raise Refused(f"no class-Y threshold for SCN against {env_sym} (multi-dopant cells are outside s2b-2)")


def threshold(t_class, t_sym, e_sym, t_h="", e_h=""):
    """(kind, thr) for a tested atom against an environment atom: kind 'sec6' (clash pair entering the
    clearance), 'pb' (SCN-Pb rule of section 5) or 'untested' (floor only). t_h, e_h: H subclass ('N'/'C')."""
    if t_class == "Y":
        return _y_threshold(t_sym, e_sym)
    ce = CLASH["class_map"].get(e_sym)
    if ce is None:
        raise Refused(f"no clash class for {e_sym}")
    if ce == "Y":
        raise Refused("SCN in the environment: multi-dopant cells are outside s2b-2")
    key = pair_key(t_class, ce, t_h if t_class == "H" else e_h)
    if key in CLASH["untested"]:
        return "untested", None
    return "sec6", THR[key]


def scn_bound(S, C, N, vt):
    """Coordination of the ends to a Pb at local vector vt (s2b-2): an end is bound iff |d - r_ref| <= window
    (distance only); the angle Pb-E-C is reported, and an in-window end with angle < a_min is 'ambiguous'
    (the pose is rejected). s2b-1 also required the angle for 'bound', so an end inside the window at a small
    angle was labelled unbound."""
    g = GEOM["SCN"]
    out = {}
    for e, P in (("S", S), ("N", N)):
        d = float(np.linalg.norm(vt - P))
        cosang = float((vt - P) @ (C - P) / (d * np.linalg.norm(C - P)))
        ang = float(np.degrees(np.arccos(np.clip(cosang, -1, 1))))
        out[e] = bool(abs(d - g[f"r_ref_{e}"]) <= g["window"])
        out[e + "_d"] = d
        out[e + "_ang"] = ang
        out[e + "_ambiguous"] = bool(out[e] and cosang > float(np.cos(np.radians(g["a_min"]))))
    return out


def scn_search(at, i, *, vpos, _full=False):
    """Deterministic grid search at iodide i (design section 5): per binding class, the admissible pose with
    the largest minimum clearance (section 6 pairs), ties within 1e-6 A by grid order. Returns
    (best: {class: params}, stats); with _full=True also the per-grid-point arrays (self-test T12)."""
    g = GEOM["SCN"]
    cell = at.cell.array
    _x_target(at, i, vpos)
    fr = x_frame(at, i)
    x0 = at.positions[int(i)]
    s = np.array(_syms(at))
    env = np.array([k for k in range(len(at)) if k != int(i)])
    v = mic(at.positions[env] - x0, cell)
    keep = np.linalg.norm(v, axis=1) < R_ENV
    env, v = env[keep], v[keep]
    # at most one image of any atom within R_ENV of X: the local vectors give exact minimum-image distances
    from ase.geometry import minkowski_reduce
    assert np.linalg.norm(minkowski_reduce(cell)[0], axis=1).min() > 2 * R_ENV
    thr6 = {e: np.full(len(env), -np.inf) for e in "SCN"}
    thrpb = {e: np.full(len(env), -np.inf) for e in "SCN"}
    for k, es in enumerate(s[env]):
        for e in "SCN":
            kind, t = _y_threshold(e, es)
            (thr6 if kind == "sec6" else thrpb)[e][k] = t
    isb = np.isin(s[env], B_SITE)
    third = isb & (env != fr["pba"]) & (env != fr["pbb"])
    vvac = mic(vpos - x0, cell)[0]
    sg, lg, psi, th, ph = scn_grid()
    a, b, c = fr["a"], fr["b"], fr["c"]
    pr, tr, fr_ = np.radians(psi), np.radians(th), np.radians(ph)
    Cp = (sg[:, None, None, None] * a + lg[None, :, None, None] * (np.cos(pr)[None, None, :, None] * b
                                                                   + np.sin(pr)[None, None, :, None] * c)).reshape(-1, 3)
    U = (np.cos(tr)[:, None, None] * a + np.sin(tr)[:, None, None] * (np.cos(fr_)[None, :, None] * b
                                                                     + np.sin(fr_)[None, :, None] * c)).reshape(-1, 3)
    nC, nU = len(Cp), len(U)
    vv2 = (v ** 2).sum(1)

    def dist(P):                         # (m, n_env) Euclidean distances from local points P
        return np.sqrt(np.maximum((P ** 2).sum(1)[:, None] + vv2[None, :] - 2.0 * P @ v.T, 0.0))
    dC = dist(Cp)
    clrC = (dC - thr6["C"]).min(1)
    okC = (dC - thrpb["C"]).min(1) >= 0
    okC &= np.linalg.norm(Cp - vvac, axis=1) >= CLASH["vac_excl"]
    clear = np.empty(nC * nU); code = np.zeros(nC * nU, np.uint8); ok = np.zeros(nC * nU, bool)
    amb = np.zeros(nC * nU, bool)
    n_third = 0
    cmax = np.cos(np.radians(g["a_min"]))
    chunk = 48
    for i0 in range(0, nC, chunk):
        Cc = Cp[i0:i0 + chunk]
        m = len(Cc)
        S = (Cc[:, None, :] - g["d_SC"] * U[None]).reshape(-1, 3)
        N = (Cc[:, None, :] + g["d_CN"] * U[None]).reshape(-1, 3)
        dS, dN = dist(S), dist(N)
        cl = np.minimum((dS - thr6["S"]).min(1), (dN - thr6["N"]).min(1))
        cl = np.minimum(cl, np.repeat(clrC[i0:i0 + m], nU))
        okp = ((dS - thrpb["S"]).min(1) >= 0) & ((dN - thrpb["N"]).min(1) >= 0) & np.repeat(okC[i0:i0 + m], nU)
        okp &= (np.linalg.norm(S - vvac, axis=1) >= CLASH["vac_excl"]) & \
               (np.linalg.norm(N - vvac, axis=1) >= CLASH["vac_excl"])
        thw = (np.abs(dS[:, third] - g["r_ref_S"]) <= g["window"]).any(1) | \
              (np.abs(dN[:, third] - g["r_ref_N"]) <= g["window"]).any(1)
        Uu = np.tile(U, (m, 1))
        cd = np.zeros(m * nU, np.uint8)
        am = np.zeros(m * nU, bool)
        for bit_s, bit_n, vt in ((1, 4, fr["va"]), (2, 8, fr["vb"])):
            for bit, P, r, sgn in ((bit_s, S, g["r_ref_S"], 1.0), (bit_n, N, g["r_ref_N"], -1.0)):
                w = vt - P
                d = np.linalg.norm(w, axis=1)
                cosang = sgn * (w * Uu).sum(1) / d          # C - S = +d_SC u ; C - N = -d_CN u
                inw = np.abs(d - r) <= g["window"]          # bound = distance window only (s2b-2)
                cd |= np.where(inw, bit, 0).astype(np.uint8)
                am |= inw & (cosang > cmax)                # in the window below a_min: ambiguous
        sl = slice(i0 * nU, (i0 + m) * nU)
        clear[sl], code[sl], amb[sl] = cl, cd, am
        ok[sl] = (cl >= 0) & okp & ~thw & ~am & np.isin(cd, list(SCN_CLASSES))
        n_third += int((thw & (cl >= 0) & okp & (cd > 0)).sum())
    stats = {"n_grid": int(nC * nU), "n_env": int(len(env)), "n_clash_free": int(((clear >= 0)).sum()),
             "n_no_bound_end": int(((clear >= 0) & (code == 0)).sum()), "n_third_pb_window": n_third,
             "n_ambiguous": int(((clear >= 0) & amb).sum()),
             "n_mu_N": int((code == 12).sum()),
             "n_impossible": int((~amb & ~np.isin(code, [0] + list(SCN_CLASSES))).sum()),
             "d_pbpb_A": round(fr["d_pbpb"], 4), "per_class": {}, "max_clearance_A": {}}
    best = {}
    for k, nm in SCN_CLASSES.items():
        msk = ok & (code == k)
        stats["per_class"][nm] = int(msk.sum())
        if not msk.any():
            continue
        M = clear[msk].max()
        stats["max_clearance_A"][nm] = float(M)
        idx = int(np.flatnonzero(msk & (clear >= M - g["tie_A"]))[0])
        iC, iU = divmod(idx, nU)
        i_s, rem = divmod(iC, len(lg) * len(psi))
        i_l, i_p = divmod(rem, len(psi))
        i_t, i_f = divmod(iU, len(ph))
        best[nm] = {"s": float(sg[i_s]), "l": float(lg[i_l]), "psi_deg": int(psi[i_p]), "theta_deg": int(th[i_t]),
                    "phi_deg": int(ph[i_f]), "grid_index": idx, "grid_ijk": [i_s, i_l, i_p, i_t, i_f],
                    "clearance_A": float(clear[idx])}
    if fr["d_pbpb"] > 2 * (g["r_ref_S"] + g["window"]):
        stats["S:ab"] = f"excluded by geometry: d(Pba,Pbb) {fr['d_pbpb']:.3f} > {2 * (g['r_ref_S'] + g['window']):.3f} A"
        assert "S:ab" not in best
    if _full:
        return best, stats, {"clear": clear, "code": code, "ok": ok, "ambiguous": amb}
    return best, stats


def build_x_molecular(at, i, token, pose, *, mig="forbid", mig_index=None, vpos=None, wrap_new=True,
                      _search=None):
    """SCN- on iodide i (the I is deleted; S, C, N appended). pose: a binding class (S:a, S:b, S:ab, N:a, N:b,
    SN:ab, SN:ba; resolved by the grid search) or a resolved pose dict (evaluated in this cell's own X frame)."""
    reg = _reg(token)
    if reg["builder"] != "x_molecular":
        raise Refused(f"{token} is not an X-site molecular anion")
    _x_target(at, i, vpos)
    i = int(i)
    name = _pose_name(token, pose)
    if name not in SCN_CODE:
        raise Refused(f"unknown SCN binding class {name!r} (one of {list(SCN_CODE)})")
    mig_index, replaced = _mig_policy(at, i, mig, mig_index)
    fr = x_frame(at, i)
    if isinstance(pose, dict):
        p = {k: pose[k] for k in ("s", "l", "psi_deg", "theta_deg", "phi_deg")}
        extra = {k: pose[k] for k in ("grid_index", "grid_ijk", "clearance_A") if k in pose}
    else:
        best, stats = _search if _search is not None else scn_search(at, i, vpos=vpos)
        if name not in best:
            why = stats.get(name) if name == "S:ab" and "S:ab" in stats else "no admissible grid pose"
            raise Inadmissible({"reason": f"SCN {name}: infeasible at site I{i} ({why})", "search": stats})
        p = {k: best[name][k] for k in ("s", "l", "psi_deg", "theta_deg", "phi_deg")}
        extra = {k: best[name][k] for k in ("grid_index", "grid_ijk", "clearance_A")}
    x0 = at.positions[i]
    new = scn_positions(x0, fr, p)
    rec = dict(p, **extra, token=token, mode="scn", name=name, frame="x", pba_input=fr["pba"], pbb_input=fr["pbb"],
               mig=mig, mig_index_input=mig_index, replaced_migrating_iodide=replaced)
    b = _assemble(at, token, i, deleted=(i,), new_syms="SCN", new_pos=new, centre=("new", 1), pose=rec,
                  wrap_new=wrap_new)
    _out_indices(b)
    return _finish(at, b, vpos, wrap_new)


# ---------------------------------------------------------------- dispatch
_ACCEPT = {"a_molecular": {"anchor", "vpos", "wrap_new"}, "a_atomic": {"anchor", "vpos", "wrap_new"},
           "b": {"vpos"}, "x_atomic": {"mig", "mig_index", "vpos"},
           "x_molecular": {"mig", "mig_index", "vpos", "wrap_new", "_search"}}
_BUILDERS = {"a_molecular": build_a_molecular, "a_atomic": build_a_atomic, "b": build_b,
             "x_atomic": build_x_atomic, "x_molecular": build_x_molecular}


def build(at, token, site, pose="inherit", **kw):
    """Dispatch through REGISTRY; keyword arguments that do not apply to the token's builder must be None."""
    reg = _reg(token)
    acc = _ACCEPT[reg["builder"]]
    bad = [k for k, v in kw.items() if k not in acc and v is not None]
    if bad:
        raise Refused(f"{token}: options {bad} do not apply to this builder")
    return _BUILDERS[reg["builder"]](at, site, token, pose, **{k: v for k, v in kw.items() if k in acc and v is not None})


# ---------------------------------------------------------------- clash filter (design section 6)
def _lab(sym, hsub):
    """Atom label of the pair-minimum record: H(N), H(C) or the element."""
    return f"H({hsub})" if sym == "H" else sym


def clash_check(at, token, tested, members, vpos=None):
    """Tested (appended and moved/modified) atoms against every retained non-member atom, by true MIC.
    Records the minimum distance of every tested-label/environment-label pair (s2b-2: H(N)-I, H(C)-I, S-I,
    C-H(N) ...) and the hydrogen-bond diagnostic: dopant N-H with an X within hbond_diag_A."""
    cell = at.cell.array
    s = _syms(at)
    hs = h_subclass(at)
    mem = set(int(k) for k in members)
    env = np.array([k for k in range(len(at)) if k not in mem], int)
    isx = np.array([CLASH["class_map"].get(s[e]) == "X" for e in env], bool)
    cache, fails, pmin = {}, [], {}
    out = {"min_margin_A": float("inf"), "worst": None, "floor_ok": True, "vac_ok": True, "scn_pb_ok": True,
           "nearest_vpos_A": None, "a_a_separation_A": None}
    n_don = n_don_hb = 0
    for t in tested:
        ct = "Y" if token == "SCN" else CLASH["class_map"][s[t]]
        d = np.linalg.norm(mic(at.positions[env] - at.positions[t], cell), axis=1)
        if s[t] == "H" and hs[t] == "N":
            n_don += 1
            n_don_hb += bool(isx.any() and d[isx].min() < CLASH["hbond_diag_A"])
        for e, de in zip(env, d):
            key = (ct, s[t], s[e], hs[t], hs[e])
            if key not in cache:
                cache[key] = threshold(*key)
            kind, thr = cache[key]
            pl = f"{_lab(s[t], hs[t])}-{_lab(s[e], hs[e])}"
            if de < pmin.get(pl, float("inf")):
                pmin[pl] = float(de)
            if de < CLASH["floor"]:
                out["floor_ok"] = False
                fails.append({"tested": int(t), "env": int(e), "rule": "floor", "d_A": round(float(de), 4)})
            if kind == "sec6":
                m = float(de - thr)
                if m < out["min_margin_A"]:
                    out["min_margin_A"] = m
                    out["worst"] = {"tested": int(t), "env": int(e), "pair": pl,
                                    "d_A": round(float(de), 4), "thr_A": round(float(thr), 4)}
                if m < 0:
                    fails.append({"tested": int(t), "env": int(e), "rule": pl,
                                  "d_A": round(float(de), 4), "thr_A": round(float(thr), 4)})
            elif kind == "pb" and de < thr:
                out["scn_pb_ok"] = False
                fails.append({"tested": int(t), "env": int(e), "rule": "SCN-Pb", "d_A": round(float(de), 4),
                              "thr_A": round(float(thr), 4)})
        if ct == "A":
            others = [k for k in env if CLASH["class_map"].get(s[k]) == "A"]
            if others:
                out["a_a_separation_A"] = round(float(pairwise(at, [t], others).min()), 4)
        if vpos is not None:
            dv = float(np.linalg.norm(mic(at.positions[t] - vpos, cell)[0]))
            out["nearest_vpos_A"] = dv if out["nearest_vpos_A"] is None else min(out["nearest_vpos_A"], dv)
            if dv < CLASH["vac_excl"]:
                out["vac_ok"] = False
                fails.append({"tested": int(t), "rule": "vacancy", "d_A": round(dv, 4)})
    out["passed"] = bool(not fails)
    out["n_fail"] = len(fails)
    out["fails"] = fails[:6]
    out["fail_rules"] = sorted({f["rule"] for f in fails})
    out["reason"] = None if not fails else f"{len(fails)} contact(s) below threshold, first {fails[0]}"
    if out["min_margin_A"] == float("inf"):
        out["min_margin_A"] = None
    # pair minima by environment class with H split (H(N), H(C)) and X pooled: e.g. 'H(C)-X', 'S-X', 'C-H(N)'
    agg = {}
    for pl, v in pmin.items():
        a_, b_ = pl.split("-", 1)
        cb = b_ if b_.startswith("H(") else CLASH["class_map"].get(b_, b_)
        k = f"{a_}-{cb}"
        agg[k] = round(min(agg.get(k, float("inf")), v), 4)
    out["pair_min_A"] = dict(sorted(agg.items()))
    out["donor_H_X_lt_diag"] = [n_don_hb, n_don]          # [dopant N-H with an X < 3.0 A, dopant N-H]
    return out


def _a_displaced_rule(at, built, rep7):
    """s2b-2 rule for displaced Cs/Rb starts: the ion's nearest X may not be closer than min(host A-X minimum,
    the centred start's nearest X), so a blind +-Q step cannot create a contact shorter than any native Cs-I."""
    if built.token not in ("Cs", "Rb") or built.pose.get("mode") != "displaced":
        return
    s = np.array(_syms(at))
    X = np.flatnonzero(np.isin(s, X_SITE))
    d_disp = float(pairwise(at, [built.centre], X).min())
    d_cen = float(np.linalg.norm(mic(at.positions[X] - np.asarray(built.pose["anchor_pos"]), at.cell.array),
                                 axis=1).min())
    floor_ = min(CLASH["host_min"]["A-X"], d_cen)
    rep7["displaced_nearest_X_A"] = round(d_disp, 4)
    rep7["centred_nearest_X_A"] = round(d_cen, 4)
    if d_disp < floor_:
        f = {"tested": int(built.centre), "rule": "A-X displaced", "d_A": round(d_disp, 4), "thr_A": round(floor_, 4)}
        rep7["fails"] = (rep7["fails"] + [f])[:6]
        rep7["n_fail"] += 1
        rep7["passed"] = False
        rep7["fail_rules"] = sorted(set(rep7["fail_rules"]) | {"A-X displaced"})
        rep7["reason"] = rep7["reason"] or f"displaced start closes an A-X contact: {f}"


# ---------------------------------------------------------------- topology helpers (V6)
ORGANIC = ("C", "N", "H", "S")


def bond_graph(at, idx):
    """Edges {(i, j)} among the indices idx under BOND_CUT (true MIC)."""
    idx = [int(k) for k in idx]
    s = _syms(at)
    D = pairwise(at, idx, idx)
    E = set()
    for a in range(len(idx)):
        for b in range(a + 1, len(idx)):
            cut = BOND_CUT.get(tuple(sorted((s[idx[a]], s[idx[b]]))))
            if cut is not None and D[a, b] < cut:
                E.add((min(idx[a], idx[b]), max(idx[a], idx[b])))
    return E


def count_intact_fa(at, exclude=()):
    """Carbons (not in exclude) whose bonded unit is an intact FA: 2 N, 1 H on C, 2 H on each N, no excluded atom."""
    s = np.array(_syms(at))
    ex = set(int(k) for k in exclude)
    n = 0
    for c in np.flatnonzero(s == "C"):
        if int(c) in ex:
            continue
        ns, hc, hn = _bonded_unit(at, int(c))
        unit_ = [int(c)] + ns + hc + [h for r in hn for h in r]
        if len(ns) == 2 and len(hc) == 1 and [len(r) for r in hn] == [2, 2] and not (set(unit_) & ex) \
                and len(set(unit_)) == 8:
            n += 1
    return n


def template_edges(token):
    if token in ("DMA", "AA"):
        syms, body = template(token)
        E = set()
        for a in range(len(syms)):
            for b in range(a + 1, len(syms)):
                cut = BOND_CUT.get(tuple(sorted((syms[a], syms[b]))))
                if cut is not None and np.linalg.norm(body[a] - body[b]) < cut:
                    E.add((a, b))
        return E
    return None


EXPECTED_EDGES = {"DMA": {(0, 1), (0, 2), (0, 3), (0, 4), (1, 5), (1, 6), (1, 7), (2, 8), (2, 9), (2, 10)},
                  "AA": {(0, 1), (0, 2), (0, 3), (1, 4), (1, 5), (2, 6), (2, 7), (3, 8), (3, 9), (3, 10)},
                  "SCN": {(0, 1), (1, 2)}}


# ---------------------------------------------------------------- validity checks V1-V10 (design section 8)
def _contiguous(at, centre, idx):
    return at.positions[centre] + mic(at.positions[list(idx)] - at.positions[centre], at.cell.array)


def validate(base, built, *, vpos=None, wrapped=True):
    """V1-V10 on a built structure. valid = every check except V7 (and the SCN pose part of V10); admissible =
    V7 (report only for GA) and, for SCN, the binding class and third-Pb rules of section 5."""
    tok = built.token
    reg = REGISTRY[tok]
    at = built.atoms
    cell = base.cell.array
    rep = {"token": tok, "pose": built.pose.get("name")}
    o2n = built.old_to_new
    mem = set(built.members)
    # V1 composition and changed hash
    rep["V1"] = checks.check_composition(base, at, built.delta, label=tok)
    # V2 atom counts
    dn = reg["n"][0] - N_HOST
    n_exp = len(base) - len(built.deleted) + len(built.added)
    ok = len(at) == n_exp == len(base) + dn and tuple(built.added) == tuple(range(len(base) - len(built.deleted), len(at)))
    if len(base) in (N_HOST, N_HOST - 1):
        ok = ok and len(at) == reg["n"][0 if len(base) == N_HOST else 1]
    rep["V2"] = {"passed": bool(ok), "n": len(at), "expected": n_exp,
                 "reason": None if ok else f"{len(at)} atoms, expected {n_exp}"}
    # V3 isovalence and parity
    sb, sa = _syms(base), _syms(at)
    e0, e1 = sum(VALENCE[x] for x in sb), sum(VALENCE[x] for x in sa)
    nB = sum(x in B_SITE for x in sa)
    nX = sum(x in X_SITE for x in sa) + sa.count("S")
    n_vac = 3 * nB - nX
    dval = sum(VALENCE[e] * k for e, k in built.delta.items())
    ok = (FORMAL_UNIT[reg["replaces"]] == FORMAL_UNIT[tok] and e1 - e0 == dval == reg["dval"]
          and n_vac in (0, 1) and e1 % 2 == n_vac % 2)
    rep["V3"] = {"passed": bool(ok), "electrons": e1, "n_vacancy": n_vac, "dval": e1 - e0,
                 "formal_removed": FORMAL_UNIT[reg["replaces"]], "formal_added": FORMAL_UNIT[tok],
                 "reason": None if ok else "isovalence or parity violated"}
    # V4 index map, retained atoms, tags, MIG
    im = checks.check_index_map(o2n, len(base), len(at), removed=built.deleted, label=tok)
    keep = sorted(o2n)
    bt, nt = np.asarray(base.get_tags(), int), np.asarray(at.get_tags(), int)
    nonmem = [k for k in keep if o2n[k] not in mem]
    memret = [k for k in keep if o2n[k] in mem]
    nn = [o2n[k] for k in nonmem]
    ok_nm = (np.array_equal(base.positions[nonmem], at.positions[nn]) and np.array_equal(base.numbers[nonmem], at.numbers[nn])
             and np.array_equal(bt[nonmem], nt[nn]))
    unmod = [k for k in memret if k not in set(built.modified)]
    ok_mem = (np.array_equal(base.positions[unmod], at.positions[[o2n[k] for k in unmod]])
              and np.array_equal(base.numbers[unmod], at.numbers[[o2n[k] for k in unmod]])
              and bool(np.all(nt[list(mem)] == DOPANT_TAG)) and all(o2n[k] == n for n, k in enumerate(keep)))
    hits = np.flatnonzero(bt == pp.MIG_TAG)
    ok_mig, mig_note = True, "no MIG tag in the input"
    if len(hits) == 1:
        m = int(hits[0])
        if m in set(built.deleted) or o2n.get(m) in mem:
            ok_mig = built.pose.get("mig") == "allow" and bool(built.pose.get("replaced_migrating_iodide"))
            mig_note = "MIG iodide replaced (mig='allow')"
        else:
            ok_mig = int(nt[o2n[m]]) == pp.MIG_TAG
            mig_note = "MIG tag survives"
    ok_mig = ok_mig and int((nt == pp.MIG_TAG).sum()) <= len(hits)
    ok = im["passed"] and ok_nm and ok_mem and ok_mig
    rep["V4"] = {"passed": bool(ok), "index_map": im["passed"], "non_members_bitwise": bool(ok_nm),
                 "members": bool(ok_mem), "mig": mig_note,
                 "reason": None if ok else f"index map {im['reason']}; non-members {ok_nm}; members {ok_mem}; mig {ok_mig}"}
    # V5 template geometry (rigid placement exact to round-off)
    errs, rmsd = [], 0.0
    if tok in ("DMA", "AA"):
        P = _contiguous(at, built.centre, built.added)
        errs = measure_internals(P, template_internals(tok))
        syms, body = template(tok)
        X = P - P.mean(axis=0)
        H = body.T @ X
        U_, _, Vt = np.linalg.svd(H)
        Dm = np.diag([1.0, 1.0, np.sign(np.linalg.det(Vt.T @ U_.T))])
        Rk = Vt.T @ Dm @ U_.T
        rmsd = float(np.sqrt(((X - body @ Rk.T) ** 2).sum(1).mean()))
        ok = list(sa[k] for k in built.added) == list(syms)
    elif tok == "GA":
        P = _contiguous(at, built.centre, [built.centre] + list(built.added))
        errs = measure_internals(P, template_internals("GA"))
        try:                                            # against its own recipe constants, from the input
            mol, ka, kb, khc, v = fa_target(base, built.site)
            ref = _ga_recipe(base, built.site, mol, ka, kb, khc, v)
            rmsd = float(np.linalg.norm(mic(at.positions[list(built.added)] - ref, cell), axis=1).max())
            ok = built.deleted == (mol[khc],)
        except Refused:
            ok, rmsd = False, float("inf")
    elif tok == "SCN":
        P = _contiguous(at, built.centre, built.added)
        errs = measure_internals(P, template_internals("SCN"))
        ok = [sa[k] for k in built.added] == ["S", "C", "N"]
    else:
        ok = True
    dmax = max([e[4] for e in errs if e[0] in ("d", "p")], default=0.0)
    amax = max([e[4] for e in errs if e[0] in ("a", "t")], default=0.0)
    ok = ok and dmax <= 1e-6 and amax <= 1e-4 and rmsd <= 1e-6
    rep["V5"] = {"passed": bool(ok), "max_bond_err_A": dmax, "max_angle_err_deg": amax, "rmsd_A": rmsd,
                 "reason": None if ok else f"template deviates: {dmax:.2e} A, {amax:.2e} deg, rmsd {rmsd:.2e}"}
    # V6 topology
    org = [k for k in range(len(at)) if sa[k] in ORGANIC]
    E = bond_graph(at, org)
    memo = sorted(k for k in mem if sa[k] in ORGANIC)
    dop_E = {e for e in E if e[0] in mem and e[1] in mem}
    cross = {e for e in E if (e[0] in mem) != (e[1] in mem)}
    if tok in EXPECTED_EDGES:
        exp_E = {(min(built.added[a], built.added[b]), max(built.added[a], built.added[b])) for a, b in EXPECTED_EDGES[tok]}
        ok_g = dop_E == exp_E and (tok not in ("DMA", "AA") or template_edges(tok) == EXPECTED_EDGES[tok])
    elif tok == "GA":
        Ns = [k for k in memo if sa[k] == "N"]
        ok_g = (len(memo) == 10 and len(dop_E) == 9 and all((min(built.centre, n), max(built.centre, n)) in dop_E for n in Ns)
                and len(Ns) == 3)
    else:
        ok_g = not memo and not dop_E
    fa0 = count_intact_fa(base)
    fa1 = count_intact_fa(at, exclude=mem)
    ok_fa = fa1 == fa0 - (1 if reg["site"] == "A" else 0)
    ok = ok_g and not cross and ok_fa
    rep["V6"] = {"passed": bool(ok), "dopant_graph": bool(ok_g), "dopant_host_bonds": sorted(cross)[:4],
                 "intact_fa": [fa0, fa1], "reason": None if ok else f"graph {ok_g}, cross {sorted(cross)[:4]}, FA {fa0}->{fa1}"}
    # V7 clash filter
    tested = list(built.added) + [o2n[k] for k in built.modified]
    rep["V7"] = clash_check(at, tok, tested, built.members, vpos)
    _a_displaced_rule(at, built, rep["V7"])
    rep["V7"]["exempt"] = tok in CLASH["exempt"]
    # V8 cell, pbc, calculator, constraints, arrays
    ok = (np.array_equal(at.cell.array, base.cell.array) and np.array_equal(at.pbc, base.pbc) and at.calc is None
          and not at.constraints and set(at.arrays) <= {"numbers", "positions", "tags"})
    rep["V8"] = {"passed": bool(ok), "arrays": sorted(at.arrays), "reason": None if ok else "cell/pbc/calc/arrays"}
    # V9 appended atoms inside [0, 1) (wrap_new)
    sf = frac(at.positions[list(built.added)], cell) if built.added else np.zeros((0, 3))
    ok = bool(((sf >= -1e-12) & (sf < 1.0)).all()) or not wrapped
    rep["V9"] = {"passed": ok, "applies": bool(wrapped), "min_s": float(sf.min()) if len(sf) else None, "max_s": float(sf.max()) if len(sf) else None,
                 "reason": None if ok else "appended atom outside [0,1)"}
    # V10 site checks
    v10, ok, scn_ok = {}, True, True
    try:
        if reg["site"] == "A":
            fa_target(base, built.site)
            _, octs, _ = pb8(base, built.site)
            v10["pb8_octants"] = bool(octs)
            ok = bool(octs)
        elif reg["site"] == "B":
            ok = sb[built.site] == "Pb"
        else:
            _x_target(base, built.site, vpos)
            fr = x_frame(base, built.site)
            v10["x_frame"] = _x_v10(fr, o2n)["x_frame"]
            mi = built.pose.get("mig_index_input")
            if len(hits) == 1 and mi != int(hits[0]):
                ok = False; v10["mig_index_mismatch"] = [mi, int(hits[0])]
            if mi is not None and int(mi) == built.site:
                ok = ok and built.pose.get("mig") == "allow" and bool(built.pose.get("replaced_migrating_iodide"))
            elif built.pose.get("replaced_migrating_iodide"):
                ok = False
            if built.pose.get("mig_index_out") != (None if mi is None else o2n.get(int(mi))):
                ok = False; v10["mig_index_out_mismatch"] = True
            if tok == "SCN":
                iS, iC, iN = built.added
                Pc = _contiguous(at, iC, [iS, iC, iN])
                pa = Pc[1] + mic(at.positions[o2n[fr["pba"]]] - at.positions[iC], cell)[0]
                pbp = Pc[1] + mic(at.positions[o2n[fr["pbb"]]] - at.positions[iC], cell)[0]
                ba, bb = scn_bound(Pc[0], Pc[1], Pc[2], pa), scn_bound(Pc[0], Pc[1], Pc[2], pbp)
                code = (1 if ba["S"] else 0) | (2 if bb["S"] else 0) | (4 if ba["N"] else 0) | (8 if bb["N"] else 0)
                ambiguous = any(x[e + "_ambiguous"] for x in (ba, bb) for e in "SN")
                g = GEOM["SCN"]
                others = [o2n[k] for k in np.flatnonzero(np.isin(base.numbers, B_Z)) if int(k) not in (fr["pba"], fr["pbb"])]
                dS3 = pairwise(at, [iS], others)[0]; dN3 = pairwise(at, [iN], others)[0]
                third = bool((np.abs(dS3 - g["r_ref_S"]) <= g["window"]).any() or (np.abs(dN3 - g["r_ref_N"]) <= g["window"]).any())
                cls = SCN_CLASSES.get(code)
                sab_ok = cls != "S:ab" or fr["d_pbpb"] <= 2 * (g["r_ref_S"] + g["window"])
                scn_ok = cls == built.pose.get("name") and not third and sab_ok and code != 12 and not ambiguous
                v10["scn"] = {"class": cls, "code": code, "third_pb_window": third, "S_ab_bound_ok": bool(sab_ok),
                              "ambiguous": bool(ambiguous),
                              "bound_a": {k: (round(x, 4) if isinstance(x, float) else x) for k, x in ba.items()},
                              "bound_b": {k: (round(x, 4) if isinstance(x, float) else x) for k, x in bb.items()},
                              "passed": bool(scn_ok)}
    except Refused as e:
        ok = False; v10["refused"] = str(e)
    rep["V10"] = dict(v10, passed=bool(ok), reason=None if ok else f"site check failed {v10}")
    rep["valid"] = bool(all(rep[f"V{k}"]["passed"] for k in (1, 2, 3, 4, 5, 6, 8, 9, 10)))
    v7 = rep["V7"]
    # s2b-2: the GA exemption covers the clash thresholds only; the 0.65 A floor and the 1.2 A vacancy exclusion
    # hold for every token (s2b-1 let an exempt GA pass both)
    rep["admissible"] = bool((v7["passed"] or (v7["exempt"] and v7["floor_ok"] and v7["vac_ok"])) and scn_ok)
    if not scn_ok:
        rep["V7"] = dict(rep["V7"], reason=(rep["V7"].get("reason") or "") + f" SCN pose rule: {v10.get('scn')}")
    return rep


# ---------------------------------------------------------------- host/vacancy pairing (design section 7)
def to_vac(vi):
    vi = int(vi)
    return lambda j: int(j) if int(j) < vi else int(j) - 1


def build_paired(host, vac, vi, token, site, pose, *, vpos=None, mig="forbid", anchor=None, wrap_new=True,
                 partners="unrelaxed", _search=None):
    """D_j on the host at site j and D_j+V on the vacancy cell at to_vac(j); the pose is resolved on the host leg
    and evaluated in the V leg's own frame. partners='relaxed' (warm-start partners, 29:377-382) drops the bitwise
    position identity and re-checks the V leg for admissibility (Inadmissible = the pair is rejected)."""
    reg = _reg(token)
    vi, site = int(vi), int(site)
    if partners not in ("unrelaxed", "relaxed"):
        raise Refused(f"partners must be 'unrelaxed' or 'relaxed', not {partners!r}")
    if _syms(host)[vi] != "I" or not np.array_equal(np.delete(host.numbers, vi), vac.numbers):
        raise Refused("the V cell is not the host with only vi deleted (numbers)")
    if not (np.array_equal(host.cell.array, vac.cell.array) and np.array_equal(host.pbc, vac.pbc)):
        raise Refused("host and V cells differ")
    if partners == "unrelaxed" and not np.array_equal(np.delete(host.positions, vi, axis=0), vac.positions):
        raise Refused("the V cell is not the host with only vi deleted (positions, bitwise)")
    if vpos is None:
        if partners == "relaxed":
            raise Refused("relaxed partners need the member's own (unrelaxed) vpos")
        vpos = host.positions[vi].copy()
    # s2b-2: vi must be the iodide at vpos in both modes (the numbers test cannot tell two iodides apart), and
    # relaxed partners must keep every inorganic atom near its counterpart (an index shift between iodides
    # moves at least one I slot by >= 4.045 A, the host I...I minimum)
    dvi = float(np.linalg.norm(mic(host.positions[vi] - vpos, host.cell.array)[0]))
    if dvi >= CLASH["vac_excl"]:
        raise Refused(f"host atom vi={vi} is {dvi:.3f} A from vpos (>= {CLASH['vac_excl']} A): wrong vacancy index")
    if partners == "relaxed":
        inorg = ~np.isin(np.delete(host.numbers, vi), [atomic_numbers[e] for e in ("C", "N", "H", "S")])
        dd = np.linalg.norm(mic(vac.positions[inorg] - np.delete(host.positions, vi, axis=0)[inorg],
                                host.cell.array), axis=1)
        lim = GEOM["pairing"]["relaxed_inorganic_max_A"]
        if dd.max() >= lim:
            raise Refused(f"relaxed partners: an inorganic atom moves {dd.max():.3f} A (>= {lim} A) between the host "
                          f"minus vi and the V cell: not the same member, or the wrong vi")
    if site == vi:
        raise Refused(f"site {site} is the vacancy iodide vi (29:273 would silently return another atom)")
    tv = to_vac(vi)
    mig_v = pp.migrating_index(vac)
    mig_h = mig_v + (1 if mig_v >= vi else 0)
    common = {"vpos": vpos, "anchor": anchor if reg["site"] == "A" else None,
              "wrap_new": wrap_new if reg["builder"] in ("a_molecular", "a_atomic", "x_molecular") else None}
    kh, kv = dict(common), dict(common)
    if reg["site"] == "X":
        kh.update(mig=mig, mig_index=mig_h, _search=_search if reg["builder"] == "x_molecular" else None)
        kv.update(mig=mig, mig_index=mig_v)
    try:
        bh = build(host, token, site, pose, **kh)
    except Inadmissible as e:
        raise Inadmissible(dict(e.report, leg="host"), f"host leg: {e}")
    try:
        bv = build(vac, token, tv(site), bh.pose, **kv)
    except Inadmissible as e:
        raise Inadmissible(dict(e.report, leg="V", reason=f"V leg: {e}; pair rejected"))
    assert tuple(tv(k) for k in bh.deleted) == bv.deleted, "deleted atoms do not map host -> V"
    assert tuple(tv(k) for k in bh.modified) == bv.modified, "modified atoms do not map host -> V"
    assert len(bh.added) == len(bv.added)
    nkh = len(bh.atoms) - len(bh.added)
    if bh.centre < nkh:
        c_old = [k for k, n in bh.old_to_new.items() if n == bh.centre][0]
        assert bv.centre == bv.old_to_new[tv(c_old)], "retained centre does not map"
    else:
        assert bh.centre - bv.centre == 1, "appended centre offset is not 1"
    if reg["site"] == "X":
        assert bh.pose["mig_index_input"] == mig_h and bv.pose["mig_index_input"] == mig_v
        assert bh.pose["replaced_migrating_iodide"] == bv.pose["replaced_migrating_iodide"]
    for b, base in ((bh, host), (bv, vac)):
        assert checks.check_index_map(b.old_to_new, len(base), len(b.atoms), removed=b.deleted)["passed"]
    if partners == "unrelaxed":
        assert np.array_equal(bh.atoms.positions[list(bh.added)], bv.atoms.positions[list(bv.added)]), \
            "appended atoms differ between unrelaxed partners"
        mh = [bh.old_to_new[k] for k in bh.modified]; mv = [bv.old_to_new[k] for k in bv.modified]
        assert np.array_equal(bh.atoms.positions[mh], bv.atoms.positions[mv])
    return bh, bv


def vacancy_context(host, pool_dir, vac_ref):
    """(vac, vpos, vi, mig_vac) for a pool member: reference vacancy from s29.ref_vacancy_position, V cell from
    pp.build_pair; vi re-derived by find_mic (29:271-272) and checked against pp.build_pair's choice."""
    ref = s29.ref_vacancy_position(pool_dir, vac_ref)
    vac, vpos, mig = pp.build_pair(host, ref, None, None)
    cell = host.cell.array
    iod = np.flatnonzero(np.array(_syms(host)) == "I")
    vi = int(iod[np.argmin(find_mic(host.positions[iod] - ref, cell, pbc=True)[1])])
    if not np.array_equal(host.positions[vi], vpos):
        raise Refused("pp.build_pair (pp.mic) and find_mic choose different vacancy iodides")
    return vac, vpos, vi, int(mig)


# ---------------------------------------------------------------- sampled poses (design section 5)
def sampled_names(token):
    if token == "GA":
        return ["inherit"]
    if token in ("DMA", "AA"):
        return ["inherit", "inherit_flip"] + list(CLASSES)
    if token in ("Cs", "Rb"):
        return list(A_ION_POSES)
    if token in ("Sr", "Ca"):
        return ["swap"]
    if token == "Cl":
        return list(CL_POSES)
    return list(SCN_CODE)


def resolve_poses(host, token, site, *, label, n_random=0, vpos=None, mig="forbid", mig_index=None, anchor=None,
                  log=None, _search=None):
    """The 'sampled' set on the host leg, in a fixed order; only admissible poses are kept, every rejection is
    appended to log. DMA/AA: inherit, inherit_flip, the six classes, n_random Haar draws (omega >= 20 deg to every
    earlier pose). Cs/Rb: centred + 6 displaced. Cl: centred, shift_a, shift_b. SCN: one per feasible class.
    label is the random-pose seed key f"{member}_{token}{site}" (design section 5), not a file label: with
    n_random > 0 it must end in f"_{token}{site}" (s2b-2). n_random > 0 is refused for tokens without random poses."""
    reg = _reg(token)
    if n_random and token not in ("DMA", "AA"):
        raise Refused(f"{token} has no random poses; n_random={n_random} would be ignored")
    if n_random and not (isinstance(label, str) and label.endswith(f"_{token}{int(site)}")
                         and len(label) > len(f"_{token}{int(site)}")):
        raise Refused(f"seed key {label!r} is not of the form '<member>_{token}{int(site)}'")
    log = [] if log is None else log
    kw = {"vpos": vpos}
    if reg["site"] == "A":
        kw["anchor"] = anchor
    if reg["site"] == "X":
        kw.update(mig=mig, mig_index=mig_index)
        if token == "SCN":
            kw["_search"] = _search if _search is not None else scn_search(host, site, vpos=vpos)
    out, Rs = [], []
    tol = np.radians(GEOM["redundancy_deg"])

    def attempt(p, nm):
        try:
            b = build(host, token, site, p, **kw)
        except Inadmissible as e:
            log.append({"pose": nm, "status": "inadmissible", "reason": str(e)})
            return None
        if token in ("DMA", "AA"):
            R = np.array(b.pose["R_lab"])
            close = [(q["name"], float(np.degrees(omega(R, R2)))) for q, R2 in zip(out, Rs) if omega(R, R2) < tol]
            if close:
                log.append({"pose": nm, "status": "redundant", "reason": f"omega < 20 deg to {close}"})
                return None
            Rs.append(R)
        out.append(b.pose)
        return b

    for nm in sampled_names(token):
        attempt(nm, nm)
    if n_random:
        rng = np.random.default_rng(zlib.crc32(label.encode()))
        kept = draws = 0
        while kept < n_random and draws < 50 * n_random:
            M = a07._random_rotation(rng)
            p = {"mode": "random", "name": f"r{kept}", "frame": "Q", "M": M.tolist(), "draw": draws,
                 "label": label, "numpy": np.__version__}
            draws += 1
            if attempt(p, f"r{kept} (draw {draws - 1})") is not None:
                kept += 1
        if kept < n_random:
            log.append({"pose": "random", "status": "short", "reason": f"{kept}/{n_random} kept in {draws} draws"})
    return out


# ---------------------------------------------------------------- sites
def list_sites(host, token, *, vi, vpos):
    """[(index, true-MIC distance to vpos)] of the eligible sites of the token's sublattice, nearest first."""
    reg = _reg(token)
    s = np.array(_syms(host))
    if reg["site"] == "A":
        cand = []
        for c in np.flatnonzero(s == "C"):
            try:
                fa_target(host, int(c)); cand.append(int(c))
            except Refused:
                pass
    elif reg["site"] == "B":
        cand = [int(k) for k in np.flatnonzero(s == "Pb")]
    else:
        cand = [int(k) for k in np.flatnonzero(s == "I") if int(k) != int(vi)]
    d = find_mic(host.positions[cand] - vpos, host.cell.array, pbc=True)[1]
    return sorted(((j, float(x)) for j, x in zip(cand, d)), key=lambda t: (t[1], t[0]))


# ---------------------------------------------------------------- CLI
POOL = "results/fa_host/pool_v3_harmonised"
VAC_REF = "results/fa_host/fa19cspb20i59_232_vI.extxyz"
FORBIDDEN_OUT = os.path.join("results", "objective2", "dopant_shell")


def _rel(path):
    """Repository-relative path, or the bare file name outside the repository (no absolute paths in outputs)."""
    p = os.path.abspath(path)
    return os.path.relpath(p, ROOT) if p.startswith(ROOT + os.sep) else os.path.basename(p)


def is_provisional(token, name):
    return token in ("DMA", "AA", "SCN") or (token == "Cl" and str(name).startswith("shift"))


INDEX_MAP_NOTE = ("Index spaces. Output (doped-leg) numbering: centre, members, added, and every pose or V10 key "
                  "ending in '_out'. Input (partner-cell) numbering: site, deleted, modified, and every key ending in "
                  "'_input'. old_to_new maps every surviving input index to its output index; keep = "
                  "sorted(old_to_new) is the basin_dev correspondence (29:172-197); host -> V is j -> j if j < vi "
                  "else j - 1.")


def _leg_record(b):
    v7 = b.report["V7"]
    return {"centre": b.centre, "members": list(b.members), "deleted": list(b.deleted), "added": list(b.added),
            "modified": list(b.modified), "old_to_new": {str(k): v for k, v in b.old_to_new.items()},
            "valid": b.report["valid"], "admissible": b.report["admissible"],
            "checks_passed": {f"V{k}": b.report[f"V{k}"]["passed"] for k in range(1, 11)},
            "clash_min_margin_A": v7["min_margin_A"], "clash_worst": v7["worst"],
            "pair_min_A": v7["pair_min_A"], "donor_H_X_lt_3A": v7["donor_H_X_lt_diag"],
            "a_a_separation_A": v7["a_a_separation_A"], "V10": b.report["V10"]}


def _write_atomic_extxyz(path, atoms):
    tmp = path + ".tmp.extxyz"
    write(tmp, atoms, format="extxyz")
    os.replace(tmp, path)


def cmd_sites(a):
    host = read(a.host)
    vac, vpos, vi, mig = vacancy_context(host, a.pool, a.vac_ref)
    mig_h = mig + (1 if mig >= vi else 0)
    print(f"# {_rel(a.host)}  token {a.dopant} (site {_reg(a.dopant)['site']})  vi {vi}  MIG iodide {mig_h} (host index)")
    for j, d in list_sites(host, a.dopant, vi=vi, vpos=vpos):
        print(f"{j:4d}  {d:7.3f}" + ("  MIG (needs --mig allow)" if j == mig_h and _reg(a.dopant)["site"] == "X" else ""))
    return 0


def out_is_forbidden(path):
    """True if path is, or lies under, results/objective2/dopant_shell. s2b-1 compared absolute path strings, so a
    case variant (case-insensitive APFS) or a symlink passed. Now: realpath with normcase, and then os.path.samefile
    for every existing ancestor of the resolved path."""
    forb = os.path.realpath(os.path.join(ROOT, FORBIDDEN_OUT))
    p = os.path.realpath(os.path.abspath(path))
    nc = os.path.normcase
    if nc(p) == nc(forb) or nc(p).startswith(nc(forb) + os.sep):
        return True
    if not os.path.exists(forb):
        return False
    q = p
    while True:
        if os.path.exists(q) and os.path.samefile(q, forb):
            return True
        parent = os.path.dirname(q)
        if parent == q:
            return False
        q = parent


def _existing_label_files(out, label):
    """Files of this label already in out: leg files {label}o<k>_novac|vac.extxyz and the manifest."""
    import re
    if not os.path.isdir(out):
        return []
    pat = re.compile(re.escape(label) + r"(o\d+_(novac|vac)\.extxyz|_manifest\.json)")
    return sorted(f for f in os.listdir(out) if pat.fullmatch(f))


def cmd_build(a):
    import re
    tok = a.dopant
    reg = _reg(tok)
    out = os.path.abspath(a.out)
    if out_is_forbidden(out):
        raise Refused(f"--out may not lie under {FORBIDDEN_OUT} (WP3 in progress)")
    # options that do not apply are refused, not silently ignored and recorded (s2b-2)
    if a.anchor is not None and (reg["site"] != "A" or tok == "GA"):
        raise Refused(f"--anchor does not apply to {tok}")
    if a.n_random and tok not in ("DMA", "AA"):
        raise Refused(f"--n-random does not apply to {tok} (no random poses)")
    if a.n_random and a.pose != "sampled":
        raise Refused("--n-random needs --pose sampled")
    if a.mig != "forbid" and reg["site"] != "X":
        raise Refused(f"--mig does not apply to {tok} (not an X-site dopant)")
    host = read(a.host)
    stem = os.path.splitext(os.path.basename(a.host))[0]
    member = a.member or stem
    if not re.fullmatch(r"[A-Za-z0-9]+", member):
        raise Refused(f"member {member!r}: letters and digits only")
    seed_key = f"{member}_{tok}{int(a.site)}"     # design section 5; independent of --label (s2b-2)
    label = a.label or seed_key
    if not re.fullmatch(r"[A-Za-z0-9]+(_[A-Za-z0-9]+)*", label):
        raise Refused(f"label {label!r}: letters, digits and single underscores only")
    stale = _existing_label_files(out, label)
    if stale:
        raise Refused(f"--out already holds {len(stale)} file(s) of label {label} ({stale[0]} ...): choose another "
                      "--label or --out (files of an earlier run are never overwritten or mixed)")
    names = sampled_names(tok) if a.pose == "sampled" else [_pose_name(tok, a.pose)]
    prov = [n for n in names if is_provisional(tok, n)]
    if prov and not a.allow_provisional:
        raise Refused(f"{tok} poses {prov} use provisional parameters ({PROVISIONAL.get(tok) or PROVISIONAL['Cl:shift']});"
                      " rerun with --allow-provisional to build them (the flag is recorded)")
    vac, vpos, vi, mig_v = vacancy_context(host, a.pool, a.vac_ref)
    mig_h = mig_v + (1 if mig_v >= vi else 0)
    site = int(a.site)
    tv = to_vac(vi)
    log = []
    if a.pose == "sampled":
        poses = resolve_poses(host, tok, site, label=seed_key, n_random=a.n_random, vpos=vpos, mig=a.mig,
                              mig_index=mig_h if reg["site"] == "X" else None,
                              anchor=a.anchor if reg["site"] == "A" else None, log=log)
    else:
        poses = [a.pose]
    legs = []
    for p in poses:
        try:
            bh, bv = build_paired(host, vac, vi, tok, site, p, vpos=vpos, mig=a.mig,
                                  anchor=a.anchor if reg["site"] == "A" else None)
        except Inadmissible as e:
            log.append({"pose": p if isinstance(p, str) else p.get("name"), "status": "inadmissible", "reason": str(e)})
            continue
        legs.append((bh, bv))
    if not legs:
        raise Inadmissible({"reason": f"no admissible pose: {log}"})
    os.makedirs(out, exist_ok=True)
    if _existing_label_files(out, label):                 # re-check just before writing
        raise Refused(f"files of label {label} appeared in --out during the build; nothing written")
    rows = []
    for k, (bh, bv) in enumerate(legs):
        f0, f1 = f"{label}o{k}_novac.extxyz", f"{label}o{k}_vac.extxyz"
        _write_atomic_extxyz(os.path.join(out, f0), bh.atoms)
        _write_atomic_extxyz(os.path.join(out, f1), bv.atoms)
        rows.append({"k": k, "pose": bh.pose, "pose_vac_leg": bv.pose, "files": {"novac": f0, "vac": f1},
                     "provisional": is_provisional(tok, bh.pose.get("name")),
                     "replaced_migrating_iodide": bool(bh.pose.get("replaced_migrating_iodide", False)),
                     "host_leg": _leg_record(bh), "vac_leg": _leg_record(bv)})
    import ase
    man = {"builder_version": BUILDER_VERSION, "geom_sha": GEOM_SHA, "numpy": np.__version__, "ase": ase.__version__,
           "status": "UNRELAXED starting structures (not minima; no energies)",
           "host": _rel(a.host), "host_sha256": hashlib.sha256(host.positions.tobytes() + host.numbers.tobytes()).hexdigest(),
           "pool": _rel(a.pool), "vac_ref": _rel(a.vac_ref), "token": tok, "sublattice": reg["site"],
           "site_host": site, "site_vac": tv(site), "vacancy_host_index": vi, "vpos": np.round(vpos, 6).tolist(),
           "d_dopant_vacancy_A": round(float(np.linalg.norm(mic(host.positions[site] - vpos, host.cell.array)[0])), 4),
           "mig_policy": a.mig, "mig_host": mig_h, "mig_vac": mig_v, "label": label, "member": member,
           "seed_key": seed_key, "pose_request": a.pose,
           "n_random": a.n_random, "anchor": a.anchor if reg["site"] == "A" else None,
           "allow_provisional": bool(a.allow_provisional), "provisional_entries": {k: PROVISIONAL[k] for k in PROVISIONAL
                                                                                    if k.split(':')[0] == tok},
           "Q": pc_frame(host.cell.array).tolist(), "legs": rows, "rejected": log,
           "index_map_note": INDEX_MAP_NOTE}
    s29.dump_atomic(man, os.path.join(out, f"{label}_manifest.json"))
    for r in rows:
        print(f"{label}o{r['k']}: {r['pose']['name']:<13} -> {r['files']['novac']}, {r['files']['vac']}"
              f"  (clash margin {r['host_leg']['clash_min_margin_A']})")
    for r in log:
        print(f"  rejected {r['pose']}: {r['status']} ({r['reason'][:120]})")
    print(f"manifest -> {os.path.join(a.out, label + '_manifest.json')}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="S2 dopant builders (geometry only; design results/objective2/s2/"
                                             "S2_BUILDERS_DESIGN.md)")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--members", default="m30", help="self-test hosts: m30 (default), 'all' (m00-m35) or a comma list")
    ap.add_argument("--report", default=None, help="self-test: admissibility report path (default: a temporary dir)")
    sub = ap.add_subparsers(dest="cmd")
    for nm in ("sites", "build"):
        sp = sub.add_parser(nm)
        sp.add_argument("--host", required=True, help="pool member extxyz (the 233-atom host)")
        sp.add_argument("--dopant", required=True, choices=sorted(REGISTRY))
        sp.add_argument("--pool", default=POOL, help="pool dir; its parent holds fa19cs1_pb20i60_233.extxyz")
        sp.add_argument("--vac-ref", default=VAC_REF)
        if nm == "build":
            sp.add_argument("--site", type=int, required=True, help="host index: FA carbon / Pb / I")
            sp.add_argument("--pose", default="inherit", help="inherit | sampled | a pose name (c100f, q0+, shift_a, S:a ...)")
            sp.add_argument("--label", default=None, help="file label only; default <member>_<TOKEN><site>")
            sp.add_argument("--member", default=None, help="pool member name for the random-pose seed key "
                                                           "<member>_<TOKEN><site>; default the host file stem")
            sp.add_argument("--out", required=True)
            sp.add_argument("--n-random", type=int, default=0)
            sp.add_argument("--anchor", default=None, choices=["fa_centroid", "fa_carbon", "pb8_centroid"])
            sp.add_argument("--mig", default="forbid", choices=["forbid", "allow"])
            sp.add_argument("--allow-provisional", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test(a.members, a.report)
    try:
        if a.cmd == "sites":
            return cmd_sites(a)
        if a.cmd == "build":
            return cmd_build(a)
    except Refused as e:
        print(f"REFUSED: {e}; nothing written", file=sys.stderr)
        return 1
    except Inadmissible as e:
        print(f"INADMISSIBLE: {e}; nothing written", file=sys.stderr)
        return 1
    ap.print_help()
    return 2


# ---------------------------------------------------------------- self-test (real pool files; no calculator)
# Literal copies of the design (self-test pins; a change to the code must also change these, and the design)
GEOM_SHA_PIN = {"s2b-1": "76809b4fd1a79f633af916945b5a0baf686b8c7744ddf50a3cd013689dba1dea",
                "s2b-2": "58ebbd29fdf179417269818f6fc31b7d55622164929a40778c49208e1cdafedf"}
SEC4_DESIGN = {"GA": {"d_CN": 1.33, "d_NH": 1.01, "u": 0.34, "w": 0.95},
               "DMA": {"d_CN": 1.49, "a_CNC": 114.0, "d_NH": 1.020, "a_HNH": 109.47, "d_CH": 1.094, "a_NCH": 109.47},
               "AA": {"d_C1N": 1.307, "d_C1C2": 1.477, "a_NCN": 121.0, "a_NCC": 119.5, "d_NH": 1.020, "a_CNH": 120.0,
                      "a_HNH": 120.0, "d_CH": 1.094, "a_CCH": 109.47, "methyl_dihedral": 90.0},
               "A_ion": {"offset": 0.30}, "Cl": {"d_PbCl": 2.837},
               "SCN": {"d_SC": 1.639, "d_CN": 1.172, "a_SCN": 180.0, "r_ref_S": 3.066, "r_ref_N": 2.734,
                       "window": 0.15, "a_min": 90.0, "c_min": 3.066}}
SCN_EXPECTED = {49: set(), 138: set(), 175: {"S:a", "S:b", "N:b"}}     # s2b-2 class Y and bound rules [R]
SCN_I175_GRID = {"S:a": 312110, "S:b": 236029, "N:b": 366338}         # pinned largest-clearance grid points
THR_DESIGN = {"HN-X": 2.314, "HC-X": 2.588, "H-H": 2.536, "H-O": 3.005, "H-B": 3.190, "H-A": 4.081, "O-X": 3.193,
              "O-O": 3.596, "O-B": 3.926, "O-A": 4.678, "A-X": 3.600, "A-B": 4.808, "X-X": 3.641}
POOL_ANCHOR_R = {"fa_off_mean": 0.235, "fa_off_sd": 0.102, "cs_off_mean": 0.132, "cs_off_max": 0.294,
                 "fa_pb8_nearest_I_min": 3.881, "fa_pb8_nearest_I_max": 4.521}      # design section 3 [R]
_DMA_ALL = ["inherit", "inherit_flip"] + list(CLASSES) + ["r0", "r1"]
_ION_ALL = list(A_ION_POSES)
T4_PINNED = {                                       # kept poses per T4 case, m30, n_random 2 (s2b-2) [R]
    "GA@128": ["inherit"], "GA@188": ["inherit"], "DMA@128": _DMA_ALL, "DMA@188": _DMA_ALL,
    "AA@128": ["c100f", "c100d", "c110b", "c111m", "c111n", "r0", "r1"],
    "AA@188": ["c100f", "c100d", "c110a", "c110b", "c111m", "c111n", "r0", "r1"],
    "Cs@128": _ION_ALL, "Cs@188": _ION_ALL, "Rb@128": _ION_ALL, "Rb@188": _ION_ALL,
    "Sr@124": ["swap"], "Sr@136": ["swap"], "Sr@76": ["swap"], "Ca@124": ["swap"], "Ca@136": ["swap"], "Ca@76": ["swap"],
    "Cl@49": list(CL_POSES), "Cl@138": list(CL_POSES), "Cl@175": list(CL_POSES),
    "SCN@49": [], "SCN@138": [], "SCN@175": ["S:a", "S:b", "N:b"]}
A_TOKENS = [t for t, r in REGISTRY.items() if r["site"] == "A"]


def _straddles(at, c):
    mol = pp.fa_molecule(at, c)
    raw = at.positions[mol] - at.positions[c]
    return bool(np.abs(raw - mic(raw, at.cell.array)).max() > 1e-6)


def _invariant(X, syms, Rm, idx):
    """Rm maps the atoms idx onto themselves (to 1e-9 A) under a symbol-preserving permutation."""
    idx = list(idx)
    p = []
    for k in idx:
        y = Rm @ X[k]
        dd = np.linalg.norm(X[idx] - y, axis=1)
        j = idx[int(np.argmin(dd))]
        if dd.min() > 1e-9 or syms[j] != syms[k]:
            return False
        p.append(j)
    return len(set(p)) == len(idx)


def pool_class_minima(paths):
    """Shortest non-bonded intermolecular contact per class pair (design section 6), bonds excluded: the Pb-I
    first shell (6 nearest I of each Pb) and intramolecular pairs of the bonded organic units (38:59-66)."""
    mins = {}
    for f in paths:
        at = read(f)
        s = np.array(_syms(at))
        d = at.get_all_distances(mic=True)
        mol = -np.ones(len(at), int)
        C, N, H = (np.flatnonzero(s == e) for e in ("C", "N", "H"))
        for k, c in enumerate(C):
            ns = N[d[c, N] < BOND_CUT[("C", "N")]]
            hs = H[(d[np.r_[c, ns]][:, H] < BOND_CUT[("C", "H")]).any(0)]
            mol[np.r_[c, ns, hs]] = k
        same = (mol[:, None] == mol[None, :]) & (mol[:, None] >= 0)
        np.fill_diagonal(same, True)
        I = np.flatnonzero(s == "I")
        for p in np.flatnonzero(s == "Pb"):
            sh = I[np.argsort(d[p, I])[:6]]
            same[p, sh] = same[sh, p] = True
        cls = np.array([CLASH["class_map"][x] for x in s])
        CN = np.r_[C, N]
        hsub = np.array([("N" if s[CN[np.argmin(d[k, CN])]] == "N" else "C") if s[k] == "H" else "" for k in range(len(s))])
        for a_, b_ in itertools.combinations_with_replacement("HOAXB", 2):
            m = (cls[:, None] == a_) & (cls[None, :] == b_) & ~same
            if not m.any():
                continue
            if {a_, b_} == {"H", "X"}:                              # s2b-2: H-X split by the bonded heavy atom
                for hh in ("N", "C"):
                    mh = m & ((hsub[:, None] == hh) | (hsub[None, :] == hh))
                    if mh.any():
                        mins[f"H{hh}-X"] = min(mins.get(f"H{hh}-X", 99.0), float(d[mh].min()))
                continue
            k = pair_key(a_, b_)
            mins[k] = min(mins.get(k, 99.0), float(d[m].min()))
    return mins


def pool_anchor_stats(paths):
    """Section 3 [R] anchor figures with the code under test (a_anchor): FA off-centring |fa_centroid - pb8| over
    every FA, native Cs off-centring |Cs - pb8(Cs)|, and the nearest I to the pb8 anchor of every FA site."""
    fa, cs, nI = [], [], []
    for f in paths:
        at = read(f)
        s = np.array(_syms(at))
        I = np.flatnonzero(s == "I")
        for c in np.flatnonzero(s == "C"):
            mol, ka, kb, khc, v = fa_target(at, int(c))
            p8 = a_anchor(at, int(c), mol, v, "pb8_centroid")
            fa.append(float(np.linalg.norm(mic(a_anchor(at, int(c), mol, v, "fa_centroid") - p8, at.cell.array)[0])))
            nI.append(float(np.linalg.norm(mic(at.positions[I] - p8, at.cell.array), axis=1).min()))
        k = int(np.flatnonzero(s == "Cs")[0])
        p, ok, _ = pb8(at, k)
        assert ok
        cs.append(float(np.linalg.norm(mic(at.positions[k] - p, at.cell.array)[0])))
    return {"fa_off_mean": float(np.mean(fa)), "fa_off_sd": float(np.std(fa)), "cs_off_mean": float(np.mean(cs)),
            "cs_off_max": float(np.max(cs)), "fa_pb8_nearest_I_min": float(np.min(nI)),
            "fa_pb8_nearest_I_max": float(np.max(nI)), "n_fa": len(fa), "n_cs": len(cs)}


def _stabiliser_order(F):
    """Order of {g in O_h : g F = F h for some h in the body C2v group} (design section 5, review finding 4)."""
    Oh = O24 + [-g for g in O24]
    C2v = (np.eye(3), C2Y, np.diag([1.0, 1.0, -1.0]), np.diag([-1.0, 1.0, 1.0]))
    return sum(any(np.abs(g @ F - F @ h).max() < 1e-9 for h in C2v) for g in Oh)


def _omega_OG(F1, F2):
    """Misorientation of two class frames modulo the cage group O and the body group G (deg)."""
    return min(float(np.degrees(np.arccos(np.clip((np.trace(F1.T @ g @ F2 @ h) - 1.0) / 2.0, -1.0, 1.0))))
               for g in O24 for h in G_MOL)


def self_test(members="m30", report=None):
    import traceback
    from collections import Counter
    t0 = time.time()
    names = [f"m{k:02d}" for k in range(36)] if members == "all" else [m.strip() for m in members.split(",")]
    pool, vac_ref = os.path.join(ROOT, POOL), os.path.join(ROOT, VAC_REF)
    results, ctxs, shared = [], {}, {"pairs": []}
    if report:
        os.makedirs(os.path.dirname(os.path.abspath(report)), exist_ok=True)
    work = tempfile.mkdtemp(prefix="s2b_selftest_", dir=os.path.dirname(os.path.abspath(report)) if report else None)

    def ctx(nm):
        if nm not in ctxs:
            host = read(os.path.join(pool, f"{nm}.extxyz"))
            vac, vpos, vi, mig = vacancy_context(host, pool, vac_ref)
            ctxs[nm] = {"host": host, "vac": vac, "vpos": vpos, "vi": vi, "mig": mig,
                        "mig_h": mig + (1 if mig >= vi else 0), "tv": to_vac(vi), "name": nm}
        return ctxs[nm]

    def case(name, fn):
        t = time.time()
        try:
            msg = fn()
            results.append((name, True))
            print(f"PASS {name}: {msg}  [{time.time() - t:.1f} s]", flush=True)
        except Exception as e:                                       # noqa: BLE001 (report every failure)
            results.append((name, False))
            print(f"FAIL {name}: {type(e).__name__}: {e}  [{time.time() - t:.1f} s]", flush=True)
            traceback.print_exc(limit=4)

    print(f"42_s2_builders self-test: {BUILDER_VERSION}, GEOM_SHA {GEOM_SHA}, numpy {np.__version__}, members {names}")
    m30 = ctx("m30")
    sA = list_sites(m30["host"], "DMA", vi=m30["vi"], vpos=m30["vpos"])
    sB = list_sites(m30["host"], "Sr", vi=m30["vi"], vpos=m30["vpos"])
    sX = list_sites(m30["host"], "Cl", vi=m30["vi"], vpos=m30["vpos"])
    PLAN = {"A": [128, sA[-1][0]], "B": [124, 136, sB[-1][0]], "X": [49, 138, sX[-1][0]]}

    def mig_of(tok, site):
        return "allow" if REGISTRY[tok]["site"] == "X" and site == m30["mig_h"] else "forbid"

    # ---- T1 templates, groups, thresholds, frames
    def t1():
        n = 0
        for tok in ("DMA", "AA"):
            syms, body = template(tok)
            errs = measure_internals(body, template_internals(tok))
            bad = [e for e in errs if e[4] > 1e-9]
            assert not bad, f"{tok} internals off the table: {bad[:3]}"
            assert template_edges(tok) == EXPECTED_EDGES[tok], f"{tok} bond graph"
            assert np.abs(body.mean(0)).max() < 1e-12
            n += len(errs)
        sd, bd = template("DMA")
        assert _invariant(bd, sd, C2Y, range(11)), "DMA not C2(y)-invariant"
        assert _invariant(bd, sd, np.diag([1.0, 1.0, -1.0]), range(11)) and _invariant(bd, sd, np.diag([-1.0, 1.0, 1.0]), range(11))
        assert abs(bd[3, 0] - bd[0, 0]) < 1e-12 and abs(bd[4, 0] - bd[0, 0]) < 1e-12, "DMA NH2 not in the yz plane"
        assert bd[3, 1] > bd[0, 1] > bd[1, 1] and bd[2, 1] < bd[0, 1], "DMA NH2 bisector not along +y away from C"
        sa, ba = template("AA")
        assert _invariant(ba, sa, C2Y, range(8)), "AA skeleton not C2(y)-invariant"
        assert not _invariant(ba, sa, C2Y, range(11)), "full AA template must not be C2(y)-invariant (Cs)"
        assert _invariant(ba, sa, np.diag([-1.0, 1.0, 1.0]), range(11)), "AA template not Cs (mirror yz)"
        assert ba[3, 1] > ba[0, 1] > ba[1, 1] and ba[2, 0] > ba[0, 0] > ba[1, 0], "AA axis convention"
        hh = float(np.linalg.norm(ba[4:8][:, None] - ba[8:11][None], axis=2).min())
        _, raw = _template_raw("AA")
        alt = _methyl(raw[3], raw[0], GEOM["AA"]["a_CCH"], GEOM["AA"]["d_CH"], np.array([1.0, 0.0, 0.0]))
        hh_in = float(np.linalg.norm(raw[4:8][:, None] - np.array(alt)[None], axis=2).min())
        assert abs(hh - 2.32) < 0.005 and abs(hh_in - 2.20) < 0.005, (hh, hh_in)
        orb = {k: len(class_orbit(k)) for k in CLASSES}
        assert orb == ORBIT_SIZE, orb
        for k in CLASSES:
            F = _class_frame(k)
            assert np.abs(F.T @ F - np.eye(3)).max() < 1e-12 and np.linalg.det(F) > 0
        assert set(THR) == set(THR_DESIGN), (sorted(THR), sorted(THR_DESIGN))
        for k, v in THR_DESIGN.items():
            assert abs(THR[k] - v) <= 5e-4 + 1e-12, (k, THR[k], v)
        # class Y (s2b-2): f_w x Bondi for S/N...H only; f x Bondi for C...H and every pair with I or organic C/N
        ex = {("N", "H"): 2.20, ("S", "H"): 2.40, ("C", "H"): 2.61, ("N", "I"): 3.177, ("C", "I"): 3.312,
              ("S", "I"): 3.402, ("N", "N"): 2.79, ("S", "C"): 3.15}
        for (e, h), v in ex.items():
            assert abs(_y_threshold(e, h)[1] - v) < 5e-4, (e, h, _y_threshold(e, h))
        # section 4 parameters and the frozen hash (review finding: neither was pinned)
        for tok, tab in SEC4_DESIGN.items():
            for k, v in tab.items():
                assert GEOM[tok][k] == v, f"GEOM[{tok}][{k}] = {GEOM[tok][k]} != design {v}"
        assert GEOM_SHA == GEOM_SHA_PIN[BUILDER_VERSION], f"GEOM_SHA {GEOM_SHA} != pinned {GEOM_SHA_PIN[BUILDER_VERSION]}"
        # orientation classes (review findings): the six frames are pairwise >= 20 deg apart modulo O and G;
        # stabiliser orders in O_h are 4 (c100*, c110*: isolated) and 2 (c111m, c111n: interior points of
        # one-parameter mirror families whose ends, y on [001] and [110], have order 4)
        Fs = {k: _class_frame(k) for k in CLASSES}
        wmin = min(_omega_OG(Fs[a_], Fs[b_]) for a_, b_ in itertools.combinations(CLASSES, 2))
        assert wmin > GEOM["redundancy_deg"], f"two class frames within {wmin:.2f} deg modulo O and G"
        st = {k: _stabiliser_order(F) for k, F in Fs.items()}
        assert st == {"c100f": 4, "c100d": 4, "c110a": 4, "c110b": 4, "c111m": 2, "c111n": 2}, st
        a54, a35 = np.degrees(np.arctan(np.sqrt(2.0))), np.degrees(np.arctan(1.0 / np.sqrt(2.0)))
        for k, ax in (("c111m", [0.0, 0.0, 1.0]), ("c111n", [1.0, 0.0, 0.0])):
            fam = {t: _stabiliser_order(Fs[k] @ _rot_axis(ax, np.radians(t))) for t in (5.0, 10.0, 20.0, a35, 40.0, a54, -a35)}
            assert fam[a54] == 4 and fam[-a35] == 4 and all(o == 2 for t, o in fam.items() if t not in (a54, -a35)), (k, fam)
        # inherit_flip is a 180 deg turn modulo G (never redundant with inherit), and C2Z is the body z turn
        assert abs(np.degrees(omega(np.eye(3), C2Z)) - 180.0) < 1e-9 and np.array_equal(C2Z, np.diag([-1.0, -1.0, 1.0]))
        # fold (review finding): coordinates within 1e-15 to 1e-12 of a lattice plane land in [-1e-12, 1)
        cell30 = m30["host"].cell.array
        rngf = np.random.default_rng(zlib.crc32(b"T1 fold"))
        nf = 0
        for eps in (0.0, 1e-16, 1e-15, 1e-14, 1e-13, 1e-12):
            S = rngf.random((3000, 3))
            ax_ = np.arange(3000) % 3
            S[np.arange(3000), ax_] = rngf.integers(-2, 3, 3000) + rngf.choice([-1.0, 1.0], 3000) * eps * rngf.random(3000)
            sf = frac(fold(S @ cell30, cell30), cell30)
            assert ((sf >= -1e-12) & (sf < 1.0)).all(), f"fold leaves s outside [-1e-12, 1) at eps {eps}"
            nf += len(S)
        # H subclass of the host: 4 N-H and 1 C-H per FA
        hsub = h_subclass(m30["host"])
        assert (int((hsub == "N").sum()), int((hsub == "C").sum())) == (76, 19)
        js = json.load(open(os.path.join(ROOT, "results/fa_host/fa_host_build.json")))
        assert [list(r) for r in SUPERCELL_P] == js["supercell_P"]
        Qs = [pc_frame(read(os.path.join(pool, f"m{k:02d}.extxyz")).cell.array) for k in range(36)
              if os.path.exists(os.path.join(pool, f"m{k:02d}.extxyz"))]
        assert all(np.array_equal(Q, Qs[0]) for Q in Qs), "pool cells differ"
        return (f"{n} template coordinates to 1e-9; DMA C2v, AA skeleton C2(y), full AA Cs; AA H(N)..H(C) {hh:.3f} "
                f"(in-plane rotamer {hh_in:.3f}) A; orbits {list(orb.values())}; stabiliser orders {list(st.values())}; "
                f"classes >= {wmin:.1f} deg apart mod O,G; thresholds, class-Y sums, section 4 table and GEOM_SHA "
                f"{GEOM_SHA[:16]} as pinned; fold of {nf} near-plane points in range; Q identical over {len(Qs)} cells")

    # ---- T2 GA regression against s29.ga_at_carbon
    def t2():
        n = 0
        for nm in names:
            c = ctx(nm)
            host, vac, vi, vpos, tv = c["host"], c["vac"], c["vi"], c["vpos"], c["tv"]
            carbons = [j for j, _ in list_sites(host, "GA", vi=vi, vpos=vpos)]
            assert len(carbons) == 19, f"{nm}: {len(carbons)} FA"
            for cc in carbons:
                for base, j in ((host, cc), (vac, tv(cc))):
                    ref, c_new, i_ch = s29.ga_at_carbon(base, j)
                    nk = len(base) - 1
                    for wrap in (False, True):
                        b = build_a_molecular(base, j, "GA", wrap_new=wrap, vpos=vpos)
                        assert b.deleted == (i_ch,) and b.centre == c_new and len(b.atoms) == len(ref)
                        assert np.array_equal(b.atoms.numbers, ref.numbers)
                        assert np.array_equal(b.atoms.positions[:nk], ref.positions[:nk])
                        tb, tr = np.asarray(b.atoms.get_tags()), np.asarray(ref.get_tags())
                        mem = set(b.members)
                        non = [k for k in range(len(ref)) if k not in mem]
                        assert np.array_equal(tb[non], tr[non]), "non-member tags differ"
                        assert all(tb[k] == DOPANT_TAG and tr[k] == 0 for k in mem), "member tags: 77 in 42, 0 in 29"
                        dd = b.atoms.positions[nk:] - ref.positions[nk:]
                        err = (np.linalg.norm(dd, axis=1) if not wrap else np.linalg.norm(mic(dd, base.cell.array), axis=1)).max()
                        assert err <= 1e-12, f"{nm} C{j}: appended atoms differ by {err:.2e} A (wrap {wrap})"
                build_paired(host, vac, vi, "GA", cc, "inherit", vpos=vpos)
                n += 1
        return f"{n} FA carbons x host/V legs x raw/wrapped match s29.ga_at_carbon (appended <= 1e-12 A); paired legs bitwise"

    # ---- T3 Sr regression against copy-and-swap
    def t3():
        n = 0
        for nm in names:
            c = ctx(nm)
            host, vac, vi, vpos, tv = c["host"], c["vac"], c["vi"], c["vpos"], c["tv"]
            for pb in np.flatnonzero(np.array(_syms(host)) == "Pb"):
                pb = int(pb)
                for base, j in ((host, pb), (vac, tv(pb))):
                    b = build_b(base, j, "Sr", vpos=vpos)
                    ref = base.copy(); ref.symbols[j] = "Sr"
                    assert np.array_equal(b.atoms.numbers, ref.numbers) and np.array_equal(b.atoms.positions, ref.positions)
                    tr = np.asarray(ref.get_tags()).copy(); tr[j] = DOPANT_TAG
                    assert np.array_equal(np.asarray(b.atoms.get_tags()), tr)
                build_paired(host, vac, vi, "Sr", pb, "inherit", vpos=vpos)
                n += 1
        return f"{n} Pb x host/V legs equal copy-and-swap exactly; tags equal except {DOPANT_TAG} on Sr"

    # ---- T4 every token on m30, inherit and sampled poses
    def t4():
        host, vac, vi, vpos = m30["host"], m30["vac"], m30["vi"], m30["vpos"]
        assert m30["vi"] == 127 and m30["mig_h"] == 138
        assert sA[0][0] == 128 and [j for j, _ in sB[:2]] == [136, 124]
        assert sX[0][0] == 138 and abs(sX[0][1] - 4.285) < 5e-4
        nonmig = [x for x in sX if x[0] != 138]
        assert nonmig[0][0] == 49 and abs(nonmig[0][1] - 4.327) < 5e-4 and sX[-1][0] == 175
        rep = {"builder_version": BUILDER_VERSION, "geom_sha": GEOM_SHA, "member": "m30", "vi": vi,
               "mig_host": m30["mig_h"], "plan": PLAN, "f": CLASH["f"], "f_w": CLASH["f_w"], "cases": []}
        lines, n, kept = [], 0, {}
        for tok, reg in REGISTRY.items():
            for site in PLAN[reg["site"]]:
                mig = mig_of(tok, site)
                log = []
                srch = scn_search(host, site, vpos=vpos) if tok == "SCN" else None
                poses = resolve_poses(host, tok, site, label=f"m30_{tok}{site}", n_random=2 if tok in ("DMA", "AA") else 0,
                                      vpos=vpos, mig=mig, mig_index=m30["mig_h"] if reg["site"] == "X" else None,
                                      log=log, _search=srch)
                assert poses or tok == "SCN", f"{tok}@{site}: no admissible pose ({log})"
                rows = []
                for p in poses:
                    bh, bv = build_paired(host, vac, vi, tok, site, p, vpos=vpos, mig=mig)
                    for b, n_exp in ((bh, reg["n"][0]), (bv, reg["n"][1])):
                        assert b.report["valid"] and b.report["admissible"], (tok, site, p["name"])
                        assert len(b.atoms) == n_exp and b.delta == reg["delta"]
                    shared["pairs"].append((tok, site, mig, p, bh, bv))
                    rows.append({"pose": p["name"], "margin_host_A": bh.report["V7"]["min_margin_A"],
                                 "margin_vac_A": bv.report["V7"]["min_margin_A"], "worst_host": bh.report["V7"]["worst"],
                                 "V7_passed_host": bh.report["V7"]["passed"], "pair_min_host_A": bh.report["V7"]["pair_min_A"],
                                 "donor_H_X_lt_3A_host": bh.report["V7"]["donor_H_X_lt_diag"]})
                    n += 1
                cse = {"token": tok, "site": site, "mig": mig, "kept": rows, "rejected": log}
                if tok == "SCN":
                    got = {p["name"] for p in poses}
                    cse["scn_stats"] = srch[1]
                    assert got == SCN_EXPECTED[site], f"SCN I{site}: classes {sorted(got)} != design {sorted(SCN_EXPECTED[site])}"
                rep["cases"].append(cse)
                kept[f"{tok}@{site}"] = [p["name"] for p in poses]
                lines.append(f"{tok}@{site}:{len(poses)}")
        path = report or os.path.join(work, "t4_admissibility.json")
        s29.dump_atomic(rep, path)
        shared["report"] = path
        print("    T4 kept poses " + " ".join(lines))
        assert kept == T4_PINNED, f"kept poses differ from the pinned s2b-2 set: {kept}"
        # orientation definitions (design section 5; review finding: four non-equivalent mutants passed).
        # (a) inherit against the FA, recomputed independently from the host, at every m30 FA site
        cell = host.cell.array
        s_ = _syms(host)
        n_or = 0
        for c, _ in sA:
            mol, ka, kb, khc, v = fa_target(host, c)
            R = fa_frame(v, ka, kb, khc)
            anc = a_anchor(host, c, mol, v, "fa_centroid")
            hc = [k for k in mol if s_[k] == "H" and np.linalg.norm(mic(host.positions[k] - host.positions[c], cell)[0]) < 1.25]
            Ns = sorted(k for k in mol if s_[k] == "N")
            assert len(hc) == 1 and len(Ns) == 2
            vch = mic(host.positions[hc[0]] - host.positions[c], cell)[0]
            vnn = mic(host.positions[Ns[1]] - host.positions[Ns[0]], cell)[0]
            for tok in ("DMA", "AA"):
                P = anc + template(tok)[1] @ R.T
                if tok == "DMA":       # NH2 bisector along the former C-H; C-N-C on the FA N-C-N (C1 on the Nb side)
                    assert angle_deg((P[3] - P[0]) + (P[4] - P[0]), vch) < 1.0, (c, "DMA NH2 bisector")
                    assert (P[1] - P[2]) @ vnn > 0 and ((P[1] + P[2]) / 2 - P[0]) @ vch < 0, (c, "DMA C-N-C")
                else:                  # C1->C2 along the former C-H, Na/Nb on the FA Na/Nb sides
                    assert angle_deg(P[3] - P[0], vch) < 1.0, (c, "AA C1-C2")
                    assert (P[2] - P[1]) @ vnn > 0 and ((P[1] + P[2]) / 2 - P[0]) @ vch < 0, (c, "AA N side")
                n_or += 1
        n_flip = n_cls = n_tie = 0
        Q = pc_frame(cell)
        for tok, site, mig, p, bh, bv in shared["pairs"]:
            if tok not in ("DMA", "AA"):
                continue
            mol, ka, kb, khc, v = fa_target(host, site)
            R_inh = fa_frame(v, ka, kb, khc)
            Rp = np.array(p["R_lab"])
            if p["name"] == "inherit":       # the builder places exactly anc + body R^T
                P = a_anchor(host, site, mol, v, "fa_centroid") + template(tok)[1] @ R_inh.T
                assert np.linalg.norm(mic(bh.atoms.positions[list(bh.added)] - P, cell), axis=1).max() < 1e-12
                n_tie += 1
            if p["name"] == "inherit_flip":  # (b) a 180 deg turn modulo G, R_inh . C2(z)
                assert abs(np.degrees(omega(R_inh, Rp)) - 180.0) < 1e-6 and np.abs(Rp - R_inh @ C2Z).max() < 1e-12
                n_flip += 1
            if p.get("mode") == "class":     # (c) no admissible orbit member is nearer the inherit frame
                F = _class_frame(p["name"])
                w_real = omega(R_inh, Rp)
                assert abs(np.degrees(w_real) - p["omega_inherit_deg"]) < 1e-9
                orb = []                     # the orbit {g F}, deduplicated modulo G in the enumeration order of O
                for g in O24:
                    Mg = g @ F
                    if not any(np.abs(Mg - M2 @ h).max() < 1e-9 for M2 in orb for h in G_MOL):
                        orb.append(Mg)
                assert len(orb) == ORBIT_SIZE[p["name"]]
                for Mg in orb:
                    if omega(R_inh, Q.T @ Mg) < w_real - 1e-9:
                        try:
                            build(host, tok, site, {"mode": "class", "name": p["name"], "frame": "Q", "M": Mg.tolist()},
                                  vpos=vpos)
                            raise AssertionError(f"{tok}@{site} {p['name']}: a nearer admissible orbit member exists")
                        except Inadmissible:
                            pass
                n_cls += 1
        assert n_flip >= 2 and n_cls >= 20 and n_tie >= 2, (n_flip, n_cls, n_tie)
        return (f"{n} admissible paired poses, V1-V10 on both legs, registry delta and counts; kept poses as pinned; "
                f"SCN classes as the design at I49/I138/I175; inherit vs FA at {n_or} (site, token); {n_tie} inherit "
                f"builds = anchor + body; {n_flip} flips at 180 deg; {n_cls} class representatives nearest admissible; "
                f"report -> {path}")

    # ---- T5 pairing for every T4 case
    def t5():
        host, vac, vi = m30["host"], m30["vac"], m30["vi"]
        tv = m30["tv"]
        hv = {k: tv(k) for k in range(len(host)) if k != vi}
        assert checks.check_index_map(hv, len(host), len(vac), removed={vi})["passed"]
        n = 0
        for tok, site, mig, p, bh, bv in shared["pairs"]:
            for b, base in ((bh, host), (bv, vac)):
                assert checks.check_index_map(b.old_to_new, len(base), len(b.atoms), removed=b.deleted)["passed"]
                inv = {v_: k for k, v_ in b.old_to_new.items()}
                assert checks.check_index_map(inv, len(b.atoms), len(base), removed=b.added)["passed"]
                keep = sorted(b.old_to_new)
                assert all(b.old_to_new[k] == i for i, k in enumerate(keep))
                um = [k for k in keep if k not in set(b.modified)]
                assert np.array_equal(b.atoms.positions[[b.old_to_new[k] for k in um]], base.positions[um])
            if tok == "GA":
                assert sorted(bh.old_to_new) == [k for k in range(len(host)) if k != bh.deleted[0]]
            assert tuple(tv(k) for k in bh.deleted) == bv.deleted and tuple(tv(k) for k in bh.modified) == bv.modified
            ks = [k for k in bh.old_to_new if k != vi]
            assert np.array_equal(bh.atoms.positions[[bh.old_to_new[k] for k in ks]],
                                  bv.atoms.positions[[bv.old_to_new[tv(k)] for k in ks]])
            assert np.array_equal(bh.atoms.positions[list(bh.added)], bv.atoms.positions[list(bv.added)])
            if bh.pose.get("replaced_migrating_iodide"):
                try:
                    pp.migrating_index(bv.atoms)
                    raise AssertionError("MIG tag survived a replaced migrating iodide")
                except AssertionError as e:
                    assert "expected exactly 1" in str(e)
            else:
                im = pp.migrating_index(bv.atoms)
                assert im == bv.old_to_new[m30["mig"]]
            n += 1
        return f"{n} pairs: to_vac maps, check_index_map both directions, keep correspondence, partner atoms and appended atoms bitwise, MIG resolves"

    # ---- T6 refusals
    def t6():
        host, vac, vi, vpos = m30["host"], m30["vac"], m30["vi"], m30["vpos"]
        n = 0

        def refused(fn, exc=Refused, what="", msg=None):
            nonlocal n
            try:
                fn()
            except exc as e:
                if msg is not None and msg not in str(e):
                    raise AssertionError(f"{what}: refused for another reason: {e}")
                n += 1
                return e
            raise AssertionError(f"not refused: {what}")
        for tok in ("Cl", "SCN"):
            refused(lambda: build_paired(host, vac, vi, tok, vi, "centred" if tok == "Cl" else "S:a", vpos=vpos), ValueError, f"{tok} at vi")
            refused(lambda: build_x_atomic(host, vi, "Cl", vpos=vpos), ValueError, "Cl at vpos", "vacancy site")
            refused(lambda: build_paired(host, vac, vi, tok, 138, "centred" if tok == "Cl" else "S:a", vpos=vpos), Refused,
                    f"{tok} MIG forbid", "migrating iodide")
            # s2b-2: an X builder without vpos is refused (s2b-1 accepted the vacancy iodide silently)
            refused(lambda: build(host, tok, vi, "centred" if tok == "Cl" else "S:a"), Refused, f"{tok} without vpos", "need vpos")
            refused(lambda: build(host, tok, 49, "centred" if tok == "Cl" else "S:a"), Refused, f"{tok} without vpos", "need vpos")
        refused(lambda: build_x_atomic(host, 49, "Cl"), Refused, "build_x_atomic without vpos", "need vpos")
        refused(lambda: scn_search(host, 49, vpos=None), Refused, "scn_search without vpos", "need vpos")
        refused(lambda: build_x_atomic(vac, m30["mig"], "Cl", vpos=vpos), Refused, "MIG tag under forbid on the V leg",
                "migrating iodide")
        refused(lambda: build(host, "DMA", 232), Refused, "native Cs")
        dm = build(host, "DMA", 128, vpos=vpos)
        dmc = [k for k in dm.members if dm.atoms.get_chemical_symbols()[k] == "C"]
        for k in dmc:
            refused(lambda: build(dm.atoms, "Cs", k), Refused, "DMA carbon")
        ga = build(host, "GA", 128, vpos=vpos)
        refused(lambda: build(ga.atoms, "AA", ga.centre), Refused, "tagged GA carbon")
        ga29, cnew, _ = s29.ga_at_carbon(host, 128)
        refused(lambda: build(ga29, "Cs", cnew), Refused, "untagged GA (non-FA) carbon")
        # the DOPANT_TAG rule on its own: an intact FA whose 8 atoms carry tag 77 (only the tag rule can refuse it)
        ht = host.copy(); tg = np.asarray(ht.get_tags()).copy(); tg[pp.fa_molecule(host, 128)] = DOPANT_TAG; ht.set_tags(tg)
        refused(lambda: build(ht, "Cs", 128, vpos=vpos), Refused, "tagged intact FA", f"tag {DOPANT_TAG}")
        refused(lambda: build(host, "K", 128), Refused, "unknown token")
        refused(lambda: build_paired(host, vac, vi, "MA", 128, "inherit"), Refused, "unknown token (paired)")
        refused(lambda: build(host, "Sr", 128), Refused, "B site on a C")
        refused(lambda: build(host, "Cl", 124, vpos=vpos), Refused, "X site on a Pb", "not an iodide")
        refused(lambda: build(host, "SCN", 49, "inherit", vpos=vpos), Refused, "SCN inherit", "no 'inherit'")
        refused(lambda: build(host, "GA", 128, "c100f"), Refused, "sampled GA")
        # options that do not apply are refused (s2b-2), not silently ignored and recorded
        refused(lambda: build(host, "GA", 128, anchor="pb8_centroid", vpos=vpos), Refused, "GA anchor", "no anchor")
        refused(lambda: resolve_poses(host, "Cs", 128, label="m30_Cs128", n_random=5, vpos=vpos), Refused, "Cs n_random",
                "no random poses")
        refused(lambda: resolve_poses(host, "DMA", 128, label="m30_DMA128_rep", n_random=2, vpos=vpos), Refused,
                "seed key not <member>_<TOKEN><site>", "seed key")
        # build_paired V-cell guards (s2b-1 never exercised them; relaxed mode accepted a wrong vi)
        v1 = vac.copy(); v1.positions[5] += np.array([1e-6, 0.0, 0.0])
        refused(lambda: build_paired(host, v1, vi, "Sr", 124, "swap", vpos=vpos), Refused, "V cell moved 1e-6 A", "positions")
        wrong = 125 if _syms(host)[125] == "I" and np.array_equal(np.delete(host.numbers, 125), vac.numbers) else None
        assert wrong is not None, "m30 indices 125-127 are expected to be I, I, I"
        vw = host.copy(); del vw[wrong]
        refused(lambda: build_paired(host, vw, vi, "Sr", 124, "swap", vpos=vpos), Refused, "wrong iodide deleted", "positions")
        refused(lambda: build_paired(host, vw, wrong, "Sr", 124, "swap", vpos=vpos), Refused, "wrong vi (unrelaxed)",
                "wrong vacancy index")
        rng = np.random.default_rng(zlib.crc32(b"T6 relaxed"))
        hr = host.copy(); hr.positions = host.positions + rng.normal(0.0, 0.05, host.positions.shape)
        vr = vac.copy(); vr.positions = vac.positions + rng.normal(0.0, 0.05, vac.positions.shape)
        refused(lambda: build_paired(hr, vr, wrong, "Cl", 126, "centred", vpos=vpos, partners="relaxed"), Refused,
                "wrong vi (relaxed)", "wrong vacancy index")
        hr2 = hr.copy(); hr2.positions[wrong] = vpos + 0.1        # vpos check passes; the I slots are still shifted
        refused(lambda: build_paired(hr2, vr, wrong, "Cl", 126, "centred", vpos=vpos, partners="relaxed"), Refused,
                "wrong vi (relaxed, vpos-consistent)", "inorganic atom moves")
        try:                                                       # the true vi passes the guards (not Refused)
            build_paired(hr, vr, vi, "Cl", 126, "centred", vpos=vpos, partners="relaxed")
        except Inadmissible:
            pass
        # absolute limits of section 6: the 1.2 A vacancy exclusion and the 0.65 A floor (never exercised in s2b-1)
        dmv = build(vac, "DMA", m30["tv"](128), "inherit_flip", vpos=vpos)
        vfake = dmv.atoms.positions[dmv.added[5]] + np.array([0.5, 0.0, 0.0])
        e = refused(lambda: build(vac, "DMA", m30["tv"](128), "inherit_flip", vpos=vfake), Inadmissible, "DMA near vpos")
        assert e.report["V7"]["fail_rules"] == ["vacancy"], e.report["V7"]["fail_rules"]
        gav = build(host, "GA", 128, vpos=vpos)
        e = refused(lambda: build(host, "GA", 128, vpos=gav.atoms.positions[gav.added[0]] + np.array([0.5, 0.0, 0.0])),
                    Inadmissible, "GA near vpos (the GA exemption does not cover the vacancy exclusion)")
        assert "vacancy" in e.report["V7"]["fail_rules"] and e.report["V7"]["exempt"]
        hf = host.copy()
        mol, ka, kb, khc, v = fa_target(host, 128)
        ncs = int(np.flatnonzero(np.array(_syms(host)) == "Cs")[0])
        hf.positions[ncs] = a_anchor(host, 128, mol, v, "pb8_centroid") + np.array([0.3, 0.0, 0.0])
        e = refused(lambda: build(hf, "Cs", 128, "centred", vpos=vpos), Inadmissible, "Cs 0.3 A from the native Cs")
        assert e.report["V7"]["fail_rules"] == ["floor"], e.report["V7"]["fail_rules"]
        hg = host.copy(); hg.positions[ncs] = gav.atoms.positions[gav.added[1]] + np.array([0.4, 0.0, 0.0])
        e = refused(lambda: build(hg, "GA", 128, vpos=vpos), Inadmissible, "GA H 0.4 A from an atom (floor holds for GA)")
        assert "floor" in e.report["V7"]["fail_rules"]
        # pb8 octant test: reflect one of the 8 nearest Pb of C128 through a Q plane (same distance, octant doubled)
        Qm = pc_frame(host.cell.array)
        idx8, v8, _ = _nearest(host, 128, _b_indices(host))
        w = v8[0] @ Qm.T; w[0] = -w[0]
        ho = host.copy(); ho.positions[idx8[0]] = host.positions[128] + w @ Qm
        refused(lambda: build(ho, "Cs", 128, vpos=vpos), Refused, "pb8 octants", "octants")
        tmp = os.path.join(work, "t6")
        hp = os.path.join(pool, "m30.extxyz")
        import contextlib, io, shutil

        def cli(argv):
            o, e = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(o), contextlib.redirect_stderr(e):
                rc = main(argv)
            return rc, o.getvalue() + e.getvalue()
        for tok, site, pose in (("DMA", 128, "inherit"), ("AA", 128, "c100f"), ("Cl", 49, "shift_a"), ("SCN", 49, "S:a"),
                                ("Cl", 49, "sampled")):
            out = os.path.join(tmp, f"{tok}_{site}")
            rc, txt = cli(["build", "--host", hp, "--dopant", tok, "--site", str(site), "--pose", pose, "--out", out])
            assert rc == 1 and "--allow-provisional" in txt and not os.path.exists(out), (tok, rc, txt)
            n += 1
        out = os.path.join(tmp, "ok")
        rc, txt = cli(["build", "--host", hp, "--dopant", "Cl", "--site", "49", "--pose", "shift_a", "--out", out,
                       "--allow-provisional"])
        assert rc == 0 and json.load(open(os.path.join(out, "m30_Cl49_manifest.json")))["allow_provisional"] is True, txt
        forb = os.path.join(ROOT, FORBIDDEN_OUT)
        before = sorted(os.listdir(forb)) if os.path.isdir(forb) else None
        bad = os.path.join(forb, "s2_should_not_exist")
        assert out_is_forbidden(bad) and out_is_forbidden(forb) and not out_is_forbidden(tmp)
        rc, txt = cli(["build", "--host", hp, "--dopant", "Sr", "--site", "124", "--out", bad])
        assert rc == 1 and "may not lie under" in txt and not os.path.exists(bad)
        # case variants (case-insensitive APFS) and a symlink resolve to the protected directory: refused
        n_guard = 0
        for var in (os.path.join(ROOT, "results", "objective2", "Dopant_Shell", "x"),
                    os.path.join(ROOT, "results", "Objective2", "dopant_shell", "x")):
            par = os.path.dirname(var)
            if os.path.exists(par) and os.path.isdir(forb) and os.path.samefile(par, forb):
                assert out_is_forbidden(var), var
                rc, txt = cli(["build", "--host", hp, "--dopant", "Sr", "--site", "124", "--out", var])
                assert rc == 1 and "may not lie under" in txt, txt
                n_guard += 1
        if os.path.isdir(forb):
            os.makedirs(tmp, exist_ok=True)
            lnk = os.path.join(tmp, "link_to_dopant_shell")
            os.symlink(forb, lnk)
            assert out_is_forbidden(os.path.join(lnk, "x", "y"))
            rc, txt = cli(["build", "--host", hp, "--dopant", "Sr", "--site", "124", "--out", os.path.join(lnk, "x")])
            assert rc == 1 and "may not lie under" in txt, txt
            os.unlink(lnk)
            n_guard += 1
        assert before is None or sorted(os.listdir(forb)) == before, "dopant_shell listing changed"
        rc, txt = cli(["build", "--host", hp, "--dopant", "Cl", "--site", "138", "--out", os.path.join(tmp, "mig")])
        assert rc == 1 and "migrating iodide" in txt and not os.path.exists(os.path.join(tmp, "mig")), txt
        # options that do not apply (CLI)
        for argv, why in ((["--dopant", "GA", "--site", "128", "--anchor", "pb8_centroid"], "--anchor"),
                          (["--dopant", "Cs", "--site", "128", "--pose", "sampled", "--n-random", "3"], "--n-random"),
                          (["--dopant", "Sr", "--site", "124", "--mig", "allow"], "--mig")):
            o_ = os.path.join(tmp, "opt")
            rc, txt = cli(["build", "--host", hp, "--out", o_] + argv)
            assert rc == 1 and why in txt and "does not apply" in txt and not os.path.exists(o_), (argv, txt)
            n += 1
        # a second run with the same label into the same --out is refused; the first run's files are unchanged
        o2 = os.path.join(tmp, "rerun")
        rc, txt = cli(["build", "--host", hp, "--dopant", "Sr", "--site", "124", "--out", o2])
        assert rc == 0, txt
        snap_files = {f: open(os.path.join(o2, f), "rb").read() for f in os.listdir(o2)}
        rc, txt = cli(["build", "--host", hp, "--dopant", "Sr", "--site", "136", "--out", o2, "--label", "m30_Sr124"])
        assert rc == 1 and "already holds" in txt, txt
        assert {f: open(os.path.join(o2, f), "rb").read() for f in os.listdir(o2)} == snap_files
        # the random-pose seed is the canonical key <member>_<TOKEN><site>, not --label
        Rr = []
        for lab in (None, "m30_DMA128_rep"):
            o3 = os.path.join(tmp, "seed_" + (lab or "default"))
            argv = ["build", "--host", hp, "--dopant", "DMA", "--site", "128", "--pose", "sampled", "--n-random", "2",
                    "--out", o3, "--allow-provisional"] + (["--label", lab] if lab else [])
            rc, txt = cli(argv)
            assert rc == 0, txt
            man = json.load(open(os.path.join(o3, f"{lab or 'm30_DMA128'}_manifest.json")))
            assert man["seed_key"] == "m30_DMA128"
            Rr.append([r["pose"]["R_lab"] for r in man["legs"] if r["pose"]["mode"] == "random"])
        assert len(Rr[0]) == 2 and Rr[0] == Rr[1], "random poses depend on --label"
        n += 5 + n_guard
        shutil.rmtree(tmp)
        snap = (host.positions.copy(), host.numbers.copy(), np.asarray(host.get_tags()).copy(), len(host))
        mol, ka, kb, khc, v = fa_target(host, 128)
        hit = None
        for tok, ax, deg in itertools.product(("DMA", "AA"), range(3), range(15, 360, 15)):
            Rm = _rot_axis(np.eye(3)[ax], np.radians(deg))      # about body x, y or z of the inherit frame
            try:
                build(host, tok, 128, {"mode": "test", "name": f"rot{'xyz'[ax]}{deg}", "frame": "fa", "M": Rm.tolist()},
                      vpos=vpos)
            except Inadmissible as e:
                hit = (f"{tok} rotated {deg} deg about body {'xyz'[ax]}", e.report["V7"]["worst"])
                break
        assert hit is not None, "no rotation of DMA or AA at C128 clashes"
        assert (np.array_equal(host.positions, snap[0]) and np.array_equal(host.numbers, snap[1])
                and np.array_equal(np.asarray(host.get_tags()), snap[2]) and len(host) == snap[3]), "input changed"
        n += 1
        return f"{n} refusals (vi, MIG forbid, native Cs, dopant and non-FA carbons, unknown tokens, provisional CLI, " \
               f"dopant_shell out); {hit[0]} raises Inadmissible ({hit[1]['pair']} {hit[1]['d_A']} A), input unchanged"

    # ---- T7 periodic boundaries and translation equivariance
    def t7():
        n_str = n_b = n_in = 0
        for nm in names:
            c = ctx(nm)
            host, vac, vi, vpos = c["host"], c["vac"], c["vi"], c["vpos"]
            for cc, _ in list_sites(host, "GA", vi=vi, vpos=vpos):
                if not _straddles(host, cc):
                    continue
                n_str += 1
                for tok in A_TOKENS:
                    try:
                        build_paired(host, vac, vi, tok, cc, "inherit", vpos=vpos)
                        n_b += 1
                    except Inadmissible:
                        n_in += 1                       # valid (V1-V6, V8-V10 passed before V7), clashing
        allp = [os.path.join(pool, f"m{k:02d}.extxyz") for k in range(36)]
        tot = strad = 0
        for f in allp:
            at = read(f)
            for cc in np.flatnonzero(np.array(_syms(at)) == "C"):
                tot += 1; strad += _straddles(at, int(cc))
        assert (strad, tot) == (267, 684), (strad, tot)
        host, vac, vi, vpos = m30["host"], m30["vac"], m30["vi"], m30["vpos"]
        cell = host.cell.array
        ref = s29.ref_vacancy_position(pool, vac_ref)
        aa_first = next(p["name"] for t_, s_, _, p, _, _ in shared["pairs"] if t_ == "AA" and s_ == 128)
        specs = {128: [("GA", 128, "inherit"), ("DMA", 128, "inherit"), ("DMA", 128, "c110b"), ("DMA", 128, "c111m"),
                       ("AA", 128, aa_first), ("Cs", 128, "centred"), ("Cs", 128, "q2-"), ("Rb", 128, "q0+"),
                       ("Sr", 124, "swap")],
                 175: [("Cl", 175, "centred"), ("Cl", 175, "shift_a"), ("Cl", 175, "shift_b"), ("SCN", 175, "S:a"),
                       ("SCN", 175, "S:b"), ("SCN", 175, "N:b"), ("Ca", 136, "swap")]}   # s2b-2: SCN infeasible at I49
        worst, n_t = 0.0, 0
        for atom, sp in specs.items():
            for k in range(3):
                T = (0.999 - frac(host.positions[atom], cell)[k]) * cell[k]
                h2 = host.copy(); h2.positions = host.positions + T; h2.wrap()
                assert abs(frac(h2.positions[atom], cell)[k] - 0.999) < 1e-9
                vac2, vpos2, vi2, mig2 = vacancy_context_from_ref(h2, ref + T)
                assert vi2 == vi and mig2 == m30["mig"]
                for tok, site, pose in sp:
                    b1 = build_paired(host, vac, vi, tok, site, pose, vpos=vpos)
                    b2 = build_paired(h2, vac2, vi2, tok, site, pose, vpos=vpos2)
                    for x1, x2 in zip(b1, b2):
                        assert np.array_equal(x1.atoms.numbers, x2.atoms.numbers)
                        e = float(np.linalg.norm(mic(x2.atoms.positions - (x1.atoms.positions + T), cell), axis=1).max())
                        worst = max(worst, e)
                        assert e <= 1e-10, f"{tok}@{site} {pose} axis {k}: {e:.2e} A"
                        for key in ("name", "g_index", "grid_index", "s", "l", "psi_deg", "theta_deg", "phi_deg", "pb_t_input",
                                    "pb_t_out", "pba_out", "pbb_out"):
                            assert x1.pose.get(key) == x2.pose.get(key), (tok, key, x1.pose.get(key), x2.pose.get(key))
                    n_t += 1
        return (f"{n_str} straddling FA x {len(A_TOKENS)} A tokens ({n_b} admissible, {n_in} valid but clashing); pool "
                f"{strad}/{tot} straddle; {n_t} translated builds (C128, I175 at s = 0.999 per axis) equal modulo the "
                f"lattice to {worst:.1e} A with the same poses and SCN grid points")

    # ---- T8 determinism of the sampled set
    def t8():
        host, vpos = m30["host"], m30["vpos"]
        msg = []
        for tok in ("DMA", "AA"):
            p1 = resolve_poses(host, tok, 128, label=f"m30_{tok}128", n_random=3, vpos=vpos)
            p2 = resolve_poses(host, tok, 128, label=f"m30_{tok}128", n_random=3, vpos=vpos)
            assert _canon(p1) == _canon(p2), "resolve_poses is not deterministic"
            p3 = resolve_poses(host, tok, 128, label=f"m05_{tok}128", n_random=3, vpos=vpos)
            r1 = [np.array(p["R_lab"]) for p in p1 if p["mode"] == "random"]
            r3 = [np.array(p["R_lab"]) for p in p3 if p["mode"] == "random"]
            assert len(r1) == len(r3) == 3 and all(np.abs(a_ - b_).max() > 1e-3 for a_, b_ in zip(r1, r3))
            for ps in (p1, p3):
                Rs = [np.array(p["R_lab"]) for p in ps]
                w = min(np.degrees(omega(Rs[i], Rs[j])) for i in range(len(Rs)) for j in range(i))
                assert w >= GEOM["redundancy_deg"] - 1e-9, w
            p0 = resolve_poses(host, tok, 128, label=f"m30_{tok}128", n_random=0, vpos=vpos)
            assert _canon([p for p in p1 if p["mode"] != "random"]) == _canon(p0)
            msg.append(f"{tok} {len(p0)} classed + 3 random")
        return "; ".join(msg) + "; identical on repeat, label-dependent random members, pairwise omega >= 20 deg, classes independent of n_random"

    # ---- T9 class minima of the pool
    def t9():
        paths = [os.path.join(pool, f"m{k:02d}.extxyz") for k in range(36)]
        if not all(os.path.exists(p) for p in paths):
            print("    WARN T9: pool incomplete; class minima not recomputed")
            return "WARN (pool absent)"
        mins = pool_class_minima(paths)
        diff = {k: round(mins[k] - v, 4) for k, v in CLASH["host_min"].items()}
        assert all(abs(x) <= 1e-3 for x in diff.values()), diff
        # section 3 anchor figures [R], with the code under test (a_anchor, pb8): the review found them unasserted
        an = pool_anchor_stats(paths)
        assert (an["n_fa"], an["n_cs"]) == (684, 36), an
        dan = {k: round(an[k] - v, 4) for k, v in POOL_ANCHOR_R.items()}
        assert all(abs(x) <= 1e-3 for x in dan.values()), dan
        return (f"{len(diff)} class minima over 36 members equal the table to 1e-3 A (max |diff| "
                f"{max(abs(x) for x in diff.values()):.4f}; HN-X {mins['HN-X']:.3f}, HC-X {mins['HC-X']:.3f}); B-B "
                f"{mins['B-B']:.3f}, X-B {mins['X-B']:.3f} A; anchors: FA off-centring {an['fa_off_mean']:.3f} +- "
                f"{an['fa_off_sd']:.3f}, Cs {an['cs_off_mean']:.3f} (max {an['cs_off_max']:.3f}), nearest I to pb8 "
                f"{an['fa_pb8_nearest_I_min']:.3f}-{an['fa_pb8_nearest_I_max']:.3f} A, as section 3 to 1e-3")

    # ---- T10 parity and formal charge
    def t10():
        host, vac = m30["host"], m30["vac"]
        e_h = sum(VALENCE[x] for x in _syms(host)); e_v = sum(VALENCE[x] for x in _syms(vac))
        assert (e_h, e_v) == (1070, 1063)
        rows = [f"    {'token':<5} {'dval':>5} {'host e-':>8} {'V e-':>6} {'parity':>12} {'q removed/added':>16}"]
        seen = set()
        for tok, site, mig, p, bh, bv in shared["pairs"]:
            if tok in seen:
                continue
            seen.add(tok)
            r3h, r3v = bh.report["V3"], bv.report["V3"]
            assert r3h["passed"] and r3v["passed"] and r3h["electrons"] % 2 == 0 and r3v["electrons"] % 2 == 1
            assert r3h["dval"] == r3v["dval"] == REGISTRY[tok]["dval"] and r3h["dval"] % 2 == 0
            assert r3h["formal_removed"] == r3h["formal_added"]
            rows.append(f"    {tok:<5} {r3h['dval']:>+5d} {r3h['electrons']:>8d} {r3v['electrons']:>6d} {'even / odd':>12} "
                        f"{r3h['formal_removed']:>+7d} / {r3h['formal_added']:+d}")
        assert seen == set(REGISTRY)
        print("\n".join(rows))
        return f"host 1070 (even), V 1063 (odd); every token isovalent with an even delta on both legs"

    # ---- T11 relaxed-partner emulation (rattled, non-identical partners)
    def t11():
        host, vac, vi, vpos, tv = m30["host"], m30["vac"], m30["vi"], m30["vpos"], m30["tv"]
        rng = np.random.default_rng(zlib.crc32(b"T11 m30"))
        hr = host.copy(); hr.positions = host.positions + rng.normal(0.0, 0.05, host.positions.shape)
        vr = vac.copy(); vr.positions = vac.positions + rng.normal(0.0, 0.05, vac.positions.shape)
        ng = 0
        for cc, _ in list_sites(hr, "GA", vi=vi, vpos=vpos):
            for base, j in ((hr, cc), (vr, tv(cc))):
                ref, c_new, i_ch = s29.ga_at_carbon(base, j)
                b = build_a_molecular(base, j, "GA", wrap_new=False, vpos=vpos)
                nk = len(base) - 1
                assert b.deleted == (i_ch,) and b.centre == c_new and np.array_equal(b.atoms.positions[:nk], ref.positions[:nk])
                assert np.linalg.norm(b.atoms.positions[nk:] - ref.positions[nk:], axis=1).max() <= 1e-12
            ng += 1
        acc, rej_h, rej_v, bdot = Counter(), Counter(), Counter(), 1.0
        for tok, reg in REGISTRY.items():
            for site in PLAN[reg["site"]]:
                mig = mig_of(tok, site)
                nms = sampled_names(tok)
                srch = scn_search(hr, site, vpos=vpos) if tok == "SCN" else None
                if tok == "SCN":
                    nms = list(srch[0])
                for nm in nms:
                    # only Inadmissible is a rejection, split by leg; Refused (an eligibility or validity defect)
                    # propagates and fails the case (s2b-1 counted both, on either leg, as V-leg rejections)
                    try:
                        bh, bv = build_paired(hr, vr, vi, tok, site, nm, vpos=vpos, mig=mig, partners="relaxed", _search=srch)
                    except Inadmissible as e:
                        assert e.report.get("leg") in ("host", "V"), e.report.get("leg")
                        (rej_h if e.report["leg"] == "host" else rej_v)[tok] += 1
                        continue
                    for b in (bh, bv):
                        assert b.report["valid"] and b.report["admissible"]
                    for key in ("name", "frame", "M", "anchor", "offset", "s", "l", "psi_deg", "theta_deg", "phi_deg"):
                        assert bh.pose.get(key) == bv.pose.get(key), (tok, nm, key)
                    if reg["site"] == "X":
                        d = float(x_frame(hr, site)["b"] @ x_frame(vr, tv(site))["b"])
                        bdot = min(bdot, d)
                        assert d > 0.99, (tok, site, d)
                    if bh.added:
                        assert not np.array_equal(bh.atoms.positions[list(bh.added)], bv.atoms.positions[list(bv.added)])
                    acc[tok] += 1
        # SCN may lose every host-feasible class on the rattled V leg (margins of a few 0.01 A); the others may not
        assert all(acc[t] > 0 for t in REGISTRY if t != "SCN"), (acc, rej_h, rej_v)
        shared["t11"] = {"accepted": dict(acc), "rejected_host": dict(rej_h), "rejected_V": dict(rej_v)}
        return (f"GA = s29 on {ng} FA of both rattled legs; V leg re-evaluated in its own frame: accepted {dict(acc)}, "
                f"rejected on the host leg {dict(rej_h)}, on the V leg {dict(rej_v)}; min b_H.b_V {bdot:.5f}")

    # ---- T12 non-template geometry
    def t12():
        host, vac, vpos, vi = m30["host"], m30["vac"], m30["vpos"], m30["vi"]
        cell = host.cell.array
        Q = pc_frame(cell)
        sy = np.array(_syms(host))
        rng = np.random.default_rng(zlib.crc32(b"T12 m30"))
        n_cl = n_ad = 0; qmin, qnext, dbmax = 1.0, 0.0, 0.0
        for i in np.flatnonzero(sy == "I"):
            i = int(i)
            fr = x_frame(host, i)
            qmin, qnext = min(qmin, fr["qa"]), max(qnext, fr["qa_next"])
            h2 = host.copy()
            for k in (fr["pba"], fr["pbb"]):
                h2.positions[k] += 1e-4 * unit(rng.normal(size=3))
            fr2 = x_frame(h2, i)
            assert (fr2["pba"], fr2["pbb"]) == (fr["pba"], fr["pbb"])
            dbmax = max(dbmax, float(np.linalg.norm(fr2["b"] - fr["b"])))
            if i == vi:
                continue
            for nm, t in (("shift_a", "pba"), ("shift_b", "pbb")):
                try:
                    b = build_x_atomic(host, i, "Cl", nm, mig="allow", vpos=vpos)
                except Inadmissible:
                    continue
                n_ad += 1
                pbt = host.positions[fr[t]]
                v1 = mic(b.atoms.positions[b.centre] - pbt, cell)[0]
                v2 = mic(host.positions[i] - pbt, cell)[0]
                assert abs(np.linalg.norm(v1) - GEOM["Cl"]["d_PbCl"]) <= 1e-9
                assert np.linalg.norm(np.cross(unit(v1), unit(v2))) <= 1e-9 and v1 @ v2 > 0
                assert b.pose["pb_t_input"] == fr[t] and b.atoms.get_chemical_symbols()[b.pose["pb_t_out"]] == "Pb"
            n_cl += 2
        assert qmin > 0.95 and dbmax < 1e-3, (qmin, dbmax)
        # anchors recomputed independently (ase get_distances; bonding by the 38:59-66 cut-offs) at every m30 FA
        n_anc = 0
        for c in np.flatnonzero(sy == "C"):
            c = int(c)
            d = host.get_distances(c, range(len(host)), mic=True)
            ns = [k for k in np.flatnonzero(sy == "N") if d[k] < 1.6]
            dh = [host.get_distances(int(x), np.flatnonzero(sy == "H"), mic=True) for x in [c] + ns]
            hs = sorted({int(np.flatnonzero(sy == "H")[j]) for row in dh for j in np.flatnonzero(row < 1.25)})
            unit8 = [c] + ns + hs
            assert len(unit8) == 8
            vv = host.get_distances(c, unit8, mic=True, vector=True)
            fa_ind = host.positions[c] + vv.mean(axis=0)
            pbs = np.flatnonzero(sy == "Pb")
            dp = host.get_distances(c, pbs, mic=True)
            p8 = pbs[np.argsort(dp, kind="stable")[:8]]
            pb_ind = host.positions[c] + host.get_distances(c, p8, mic=True, vector=True).mean(axis=0)
            mol, ka, kb, khc, v = fa_target(host, c)
            assert np.abs(a_anchor(host, c, mol, v, "fa_centroid") - fa_ind).max() < 1e-12, (c, "fa_centroid")
            assert np.abs(a_anchor(host, c, mol, v, "pb8_centroid") - pb_ind).max() < 1e-12, (c, "pb8_centroid")
            n_anc += 1
        # displaced Cs/Rb: exactly 0.30 A along +-Q, and (s2b-2) never closer to an X than min(4.000, centred)
        n_ion = n_rule = 0
        X = np.flatnonzero(np.isin(sy, X_SITE))
        for tok in ("Cs", "Rb"):
            for site, _ in sA:
                mol, ka, kb, khc, v = fa_target(host, site)
                anc = a_anchor(host, site, mol, v, "pb8_centroid")
                d_cen = float(np.linalg.norm(mic(host.positions[X] - anc, cell), axis=1).min())
                for nm in A_ION_POSES[1:]:
                    try:
                        b = build_a_atomic(host, site, tok, nm, vpos=vpos)
                    except Inadmissible as e:
                        n_rule += "A-X displaced" in e.report["V7"]["fail_rules"]
                        continue
                    off = mic(b.atoms.positions[b.centre] - anc, cell)[0]
                    assert abs(np.linalg.norm(off) - 0.30) <= 1e-9
                    sg = 1.0 if nm[2] == "+" else -1.0
                    assert abs(sg * (off @ Q[int(nm[1])]) / 0.30 - 1.0) <= 1e-9
                    dx = float(pairwise(b.atoms, [b.centre], np.flatnonzero(np.isin(b.atoms.get_chemical_symbols(), X_SITE))).min())
                    assert dx >= min(CLASH["host_min"]["A-X"], d_cen) - 1e-12, (tok, site, nm, dx, d_cen)
                    n_ion += 1
        assert n_rule > 0, "the displaced A-X rule never fired on m30 (expected at C164)"
        # SCN: the class label equals the coordination recomputed from the atoms (distance windows only), every
        # non-bound end lies outside the window of Pba and Pbb, bound ends have angle >= a_min, and the output
        # indices pba_out/pbb_out name the bound Pb in the written cell
        n_scn = 0
        g = GEOM["SCN"]
        for tok, site, mig, p, bh, bv in shared["pairs"]:
            if tok != "SCN":
                continue
            for b in (bh, bv):
                sc = b.report["V10"]["scn"]
                code = SCN_CODE[p["name"]]
                sa_ = b.atoms.get_chemical_symbols()
                iS, iC, iN = b.added
                assert sa_[b.pose["pba_out"]] == "Pb" and sa_[b.pose["pbb_out"]] == "Pb"
                got = 0
                for bit_s, bit_n, pk in ((1, 4, "pba_out"), (2, 8, "pbb_out")):
                    for bit, ie, e in ((bit_s, iS, "S"), (bit_n, iN, "N")):
                        dv_ = mic(b.atoms.positions[b.pose[pk]] - b.atoms.positions[ie], cell)[0]
                        de = float(np.linalg.norm(dv_))
                        if abs(de - g[f"r_ref_{e}"]) <= g["window"]:
                            got |= bit
                            vc = mic(b.atoms.positions[iC] - b.atoms.positions[ie], cell)[0]
                            assert angle_deg(dv_, vc) >= g["a_min"] - 1e-9, (p["name"], pk, e)
                        else:
                            assert de > g[f"r_ref_{e}"] + g["window"], (p["name"], pk, e, de)
                assert got == code, (p["name"], got, code)
                assert sc["code"] == code and not sc["ambiguous"] and sc["code"] != 12 and not sc["third_pb_window"]
                n_scn += 1
            if not bv.pose["replaced_migrating_iodide"]:
                assert bv.atoms.get_tags()[bv.pose["mig_index_out"]] == pp.MIG_TAG
        # SCN selection rule: the largest admissible clearance in each class, first grid point within tie_A
        n_sel = 0
        for site in PLAN["X"]:
            best, st, F = scn_search(host, site, vpos=vpos, _full=True)
            for k, nm in SCN_CLASSES.items():
                msk = F["ok"] & (F["code"] == k)
                if not msk.any():
                    assert nm not in best
                    continue
                M = float(F["clear"][msk].max())
                first = int(np.flatnonzero(msk & (F["clear"] >= M - g["tie_A"]))[0])
                assert best[nm]["clearance_A"] == M and best[nm]["grid_index"] == first, (site, nm)
                assert not F["ambiguous"][first]
                n_sel += 1
            if site == 175:
                assert {k: v["grid_index"] for k, v in best.items()} == SCN_I175_GRID, {k: v["grid_index"] for k, v in best.items()}
        for cse in json.load(open(shared["report"]))["cases"]:
            if "scn_stats" in cse:
                st = cse["scn_stats"]
                assert st["n_mu_N"] == 0 and st["n_impossible"] == 0 and st["n_grid"] == 590976
        return (f"shifted Cl at 2.837 A and collinear in {n_ad}/{n_cl} admissible starts (59 non-vacancy m30 X sites); "
                f"anchors equal independent recomputation at {n_anc} FA; {n_ion} displaced Cs/Rb exactly 0.30 A along "
                f"+-Q, none closer to an X than min(4.000 A, centred) ({n_rule} rejected by that rule); {n_scn} SCN legs: "
                f"class = distance coordination, non-bound ends outside the windows, *_out indices on the bound Pb; "
                f"{n_sel} SCN classes take the largest admissible clearance (I175 grid points pinned); X frame "
                f"|q_k.a| >= {qmin:.4f}, next <= {qnext:.4f}, b moves {dbmax:.1e} under a 1e-4 A Pb rattle")

    for nm_, fn in (("T1 templates", t1), ("T2 GA regression", t2), ("T3 Sr regression", t3), ("T4 tokens on m30", t4),
                    ("T5 pairing", t5), ("T6 refusals", t6), ("T7 PBC", t7), ("T8 determinism", t8),
                    ("T9 pool minima", t9), ("T10 parity", t10), ("T11 relaxed partners", t11),
                    ("T12 non-template geometry", t12)):
        case(nm_, fn)
    ok_mace = "mace" not in sys.modules
    print(f"{'PASS' if ok_mace else 'FAIL'} no-model: 'mace' {'not ' if ok_mace else ''}in sys.modules "
          f"(torch {'imported' if 'torch' in sys.modules else 'not imported'}); work files in {work}")
    results.append(("no-model", ok_mace))
    nf = sum(not ok for _, ok in results)
    print(f"SELF-TEST {'PASS' if not nf else 'FAIL'} ({len(results)} cases, {nf} failed, {time.time() - t0:.0f} s)")
    return 1 if nf else 0


def vacancy_context_from_ref(host, ref):
    """As vacancy_context, for an explicit reference vacancy position (translation test T7)."""
    vac, vpos, mig = pp.build_pair(host, ref, None, None)
    iod = np.flatnonzero(np.array(_syms(host)) == "I")
    vi = int(iod[np.argmin(find_mic(host.positions[iod] - ref, host.cell.array, pbc=True)[1])])
    assert np.array_equal(host.positions[vi], vpos)
    return vac, vpos, vi, int(mig)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
"""S2 cells (Stage 0, module A): sites, free regions, cell construction, frozen-region MACE relaxations, the
validity checks 1-5, distinct minima, labels, records, layout, hygiene and the MACE loader of S2.

Binding specification: results/objective2/s2/S2_PLAN.md (commit ae6402e), sections 4 (sites, far pairs, regions,
index transfer, region_id), 5 (host relaxation, V+_Rj, D_j and D_j+V, frozen relaxation, validity checks 1-5,
records, labels), 9 (pose starts, distinct minima, geometry only), 11 (calibration sites, the m05 draw and census,
the A2 order and the final-geometry checks 2-5), 2 (the Pb-Cl rule for the shifted Cl starts) and 17 items 2-4;
S2_BUILDERS_DESIGN.md sections 3, 9, 11 and 16 (answers 1, 3, 4, 6, 8, 9). The interface (function names, record
schemas, layout) follows the Stage-0 interface specification; tags I-n, N-n and X-n are those of that
specification, and I-An / N-An are the interpretations and implementation notes added by this module (NOTES below).

What this module never does. No S2 cell (any pilot or production cell of any host) is evaluated by a calculator
here or in the self-test: a calculator is attached only to synthetic cells or to the reference cells
results/fa_host/fa19cs1_pb20i60_233.extxyz and fa19cspb20i59_232_vI.extxyz (N-1). The job runner accepts the mock
harmonic calculator only for the members 'ref233' and 'synthetic', and MACE only under a node root /data (N-2).
mace, torch and e3nn are imported only inside load_mace(), which no self-test calls; every geometry-only path ends
with the assertion that "mace" is not in sys.modules. MACE energies are written only into cell records under the
key E_mace_eV, which load_record() strips unless blind=False (spec 12.2 item 3); structure files carry no
calculator results and the FIRE log carries step counts and forces only (N-A4).

Library (loaded by importlib as c46, as scripts/42 loads 22 and 29):
    sites      host_context, ref_context, rank_sites, site_sets, assert_site_tables, c1_sites, label_sites
    regions    build_region, region_id, to_vac_map, free_in_cell, cell_maps, assert_fixed_at_host
    cells      make_vacancy, build_pair, pair_record, build_host_leg, pose_starts, pbcl_value, apply_pbcl_override
    relax      relax_host (scripts/29 relax_staged), relax_frozen (ASE FIRE, FixAtoms outside R_j), MockHarmonic
    validity   check_converged, check_refill, check_dopant_on_site, check_topology, check_partner, validity,
               validity_a2
    minima     distinct_minima, fa_skeletons
    labels     LABEL_RE, WORK_RE, REF_RE, make_label, make_work_id, parse_label, parse_work_id, check_label,
               check_work_id, a2_order, campaign_of, c1_label_sets
    records    cell_record, load_record, dump_public, hygiene_violations, sha256_atoms, Layout
    model      foundation_path, foundation_check, load_mace

From the repository root:
    python scripts/46_s2_cells.py --self-test [--work DIR]
    python scripts/46_s2_cells.py sites --member m30
    python scripts/46_s2_cells.py <relax-host|region|build-vac|build-pair|relax|validate|distinct|validate-a2> \
        --job JOB.json
JOB.json (written by scripts/50): {"action", "campaign", "root", "member", "work_id" (relax-host, relax, validate),
"site" (region, build-vac, build-pair, distinct), "token" and "start" p<n> (build-pair, distinct), "leg" (distinct),
"starts" (distinct, optional), "partners" (build-pair; default 'relaxed'), "allow_provisional", "pbcl_record",
"m05_cal", "calc" ('mace' | 'mock-harmonic'), "threads"}. Every path is derived from "root" by Layout; the spec keys
"kind", "pose" and "region", if given, must agree with what is derived (fail-closed). Completion markers: region
record, cells/<id>/vac_start.json, pair record, cells/<id>/record.json, cells/<id>/validity.json, distinct record.
Exit 0 = done (record written; a rejected pair is a record with status 'rejected'), 3 = refused or fail-closed
STOP, 1 = unexpected error.
"""
import argparse, dataclasses, hashlib, importlib.util, json, os, platform, re, subprocess, sys, tempfile, time, types, zlib
from dataclasses import dataclass

import numpy as np
from ase import Atoms
from ase.calculators.calculator import Calculator, all_changes
from ase.geometry import find_mic
from ase.io import read, write

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


b42 = _load("b42", "42_s2_builders.py")            # builders s2b-2 (loads 22 as pp and 29 as s29)
pp, s29 = b42.pp, b42.s29                          # never loaded a second time (spec 1.2)
a38 = _load("a38", "38_wp2e_displacement.py")      # molecule (by bonding), kabsch_deg
HELPERS = {"42": b42, "22": pp, "29": s29, "38": a38}

# ---------------------------------------------------------------- builder freeze (plan sections 0, 17; answer 3)
GEOM_SHA_S2B2 = "58ebbd29fdf179417269818f6fc31b7d55622164929a40778c49208e1cdafedf"
if b42.BUILDER_VERSION != "s2b-2" or b42.GEOM_SHA != GEOM_SHA_S2B2:
    raise RuntimeError(f"scripts/42 is {b42.BUILDER_VERSION} with GEOM_SHA {b42.GEOM_SHA}; S2 is frozen at s2b-2 "
                       f"{GEOM_SHA_S2B2} (S2_PLAN.md sections 0 and 17); refusing to load")

# ---------------------------------------------------------------- constants (spec 2.1; plan section in each comment)
VI = 127                                            # section 4: the vacancy iodide of every member
TOKENS = ("Sr", "Ca", "Cl", "Cs", "GA")             # section 2
SUBLATTICE = {"Sr": "B", "Ca": "B", "Cl": "X", "Cs": "A", "GA": "A"}
TOKENS_OF = {"B": ("Sr", "Ca"), "A": ("Cs", "GA"), "X": ("Cl",)}
CONTROL, DECISIVE = "Sr", ("Ca", "Cl", "Cs", "GA")
MULTI_START = ("Cs", "Cl")                          # sections 2, 9: only these have starts other than the default
PILOTS = ("m30", "m05")                             # section 3
# Section 3 draw, executed 2026-11-03: rank -> (member, zlib.crc32(("S2n-host-" + member).encode())). Literal copy.
DRAW = (("m06", 18472929), ("m02", 108272632), ("m16", 402845344), ("m12", 527379129), ("m32", 760825915),
        ("m26", 858766691), ("m22", 876771706), ("m23", 1128614380), ("m33", 1516140717), ("m13", 1751652911),
        ("m17", 1862655542), ("m03", 1903373166), ("m07", 1981738871), ("m15", 2165030682), ("m11", 2254863107),
        ("m19", 2294149937), ("m09", 2443625072), ("m01", 2675788354), ("m29", 2744164594), ("m25", 2854677721),
        ("m35", 3007176088), ("m31", 3025148289), ("m34", 3292196110), ("m28", 3566702692), ("m20", 3662420054),
        ("m24", 3709983823), ("m08", 3869373158), ("m00", 3900340948))
DRAW_EXCLUDED = ("m30", "m05", "m04", "m10", "m14", "m18", "m27", "m21")   # section 3 eligible set (28)
FIRST_CUT_A = {"B": 5.0, "A": 6.0}                  # section 4: B d < 5.0, A d < 6.0; X = the 8 nearest
X_FIRST_N = 8
# Section 4 gaps, as stated over the pool (rounded); asserted per host with half a last digit of tolerance (I-1):
# B next Pb >= 6.72; A first <= 5.46, next FA >= 7.22; X 8th <= 5.119, 9th >= 5.484.
GAPS = {"B_next_min": 6.715, "A_first_max": 5.465, "A_next_min": 7.215, "X_8th_max": 5.1195, "X_9th_min": 5.4835}
FIRST_SHELL = {"B": (124, 136), "A": (28, 92, 128), "X": (49, 53, 90, 102, 125, 126, 137, 138)}
FAR_MIN_A = {"B": 8.5, "A": 9.0, "X": 9.0}          # section 4: far pair beyond these (strict)
# Section 4 executed site lists: member -> (role, migrating I, Cs-v, B far pair, A far pair, X far pair); each
# far pair (f1, d1), (f2, d2) with distances to 2 dp. Literal copy of the plan table.
SITE_TABLE = {
    "m30": ("pilot", 138, 4.52, ((76, 11.81), (172, 11.55)), ((188, 11.25), (164, 10.87)), ((175, 12.77), (186, 11.91))),
    "m05": ("pilot", 53, 4.25, ((76, 11.96), (172, 11.47)), ((188, 10.86), (164, 10.48)), ((175, 12.95), (222, 11.99))),
    "m06": ("rank 1", 53, 4.22, ((76, 11.77), (172, 11.68)), ((200, 10.96), (164, 10.69)), ((175, 12.93), (222, 12.00))),
    "m02": ("rank 2", 126, 4.35, ((76, 11.93), (172, 11.53)), ((188, 10.91), (152, 10.87)), ((175, 12.70), (186, 11.81))),
    "m16": ("rank 3", 138, 4.54, ((76, 11.86), (172, 11.58)), ((164, 10.80), (188, 10.79)), ((175, 12.86), (222, 11.93))),
    "m12": ("rank 4", 126, 4.17, ((76, 11.96), (172, 11.53)), ((68, 10.96), (200, 10.56)), ((175, 12.79), (222, 11.95))),
    "m32": ("rank 5", 49, 4.42, ((76, 11.90), (172, 11.70)), ((200, 10.65), (188, 10.57)), ((175, 13.02), (222, 11.94))),
    "m26": ("rank 6", 126, 4.08, ((76, 11.97), (172, 11.54)), ((68, 11.12), (164, 10.94)), ((175, 12.77), (222, 11.40))),
    "m22": ("rank 7", 53, 4.54, ((76, 11.79), (172, 11.70)), ((16, 10.56), (4, 10.56)), ((175, 12.77), (186, 11.83))),
    "m23": ("rank 8", 90, 4.44, ((172, 11.84), (76, 11.70)), ((200, 10.71), (4, 10.48)), ((175, 12.84), (186, 11.92))),
    "m33": ("rank 9", 126, 4.20, ((76, 11.94), (172, 11.59)), ((68, 10.87), (200, 10.73)), ((175, 12.33), (222, 11.71))),
    "m13": ("rank 10", 126, 4.15, ((76, 11.86), (172, 11.46)), ((188, 10.60), (164, 10.52)), ((175, 12.64), (222, 11.79))),
    "m17": ("rank 11", 138, 4.04, ((76, 11.93), (172, 11.59)), ((200, 10.65), (188, 10.62)), ((175, 12.79), (222, 11.69))),
    "m03": ("rank 12", 53, 4.16, ((76, 11.96), (172, 11.67)), ((188, 10.75), (68, 10.40)), ((175, 13.00), (222, 11.95))),
}
TABLE_TOL_A = 0.005 + 1e-9                          # the table is rounded to 2 dp
FAR4_TABLE = {"m30": {"B": (76, 172, 24, 148), "A": (188, 164, 176, 200), "X": (175, 186, 222, 174)},
              "m05": {"B": (76, 172, 24, 64), "A": (188, 164, 152, 68), "X": (175, 222, 186, 174)}}
CAL_SITES = {"m30": {"B": 136, "A": 128, "X": 138}, "m05": {"B": 124, "A": 28, "X": 49}}    # section 11
# Section 11 m05 draw (executed 2026-11-03): sites ordered by zlib.crc32(("S2n-cal-m05-" + label).encode()).
M05_DRAW_ORDER = {"A": ((28, 684900801), (92, 737407252)),
                  "X": ((49, 299187232), (138, 1029408902), (125, 1525794170), (137, 2917438743),
                        (126, 3287848128), (90, 3718773449), (102, 4137890395))}
M05_CENSUS_A = {"B": {124: 3.27, 136: 3.28}, "A": {28: 5.03, 128: 4.78, 92: 5.11}, "X": {49: 4.63, 53: 4.31}}
M05_REGION_SIZES = {("B", 124): 70, ("A", 28): 58, ("X", 49): 59}        # section 11, unrelaxed m05 member
M30_REGION_SIZES_XCHECK = {("B", 136): 69, ("A", 128): 49, ("X", 138): 58, ("B", 76): 107}   # architect census
POSE_SITES = {"Cs": (128, 188), "Cl": (138, 175)}   # section 9, m30: nearest and farthest FA; MIG and farthest I
G1_SITES = {"Cl": 138, "Ca": 136}                   # section 7, m30 host-leg cells
SPIN_SITES = {"Cl": 175, "Ca": 76}                  # section 7, m30 farthest sites (noise-pilot D_f+V cells)
SR_FAR_SITE = 76                                    # section 11, m30 Sr far quartet
REGION_RADIUS_A = 6.0                               # section 4; strict d < 6.0 as scripts/40 (I-2)
REFILL_MIN_A = 1.2                                  # section 5 check 2: fail if any I or Cl has d <= 1.2
VAC_DELETE_MAX_A = 1.2                              # section 5: the deleted I127 within 1.2 A of the unrelaxed v (I-3)
DOPANT_MAX_A = 1.0                                  # section 5 check 3: displacement < 1.0 (strict)
ORG_BOND_CUT = {("C", "N"): 1.6, ("C", "C"): 1.7, ("H", "N"): 1.25, ("C", "H"): 1.25}   # check 4, bond iff d < cut
ORG_INORG_MIN = {"H": 1.25, "C": 1.6, "N": 1.6}     # check 4: fail if d <= value to any inorganic atom (I-A1)
ORGANIC = ("C", "N", "H")
INORGANIC = ("Pb", "I", "Cl", "Cs", "Sr", "Ca")     # check 4
HOST_INORGANIC = ("Pb", "I", "Cs")                  # section 4 region rule ("inorganic atom (Pb, I, Cs)")
FLOOR_A = 0.65                                      # check 4: fail if any pair d < 0.65 ("below 0.65 A")
PARTNER_CUT_A, PARTNER_DR_A, PARTNER_ROT_DEG = 6.0, 0.25, 20.0     # check 5: gated beyond 6.0; pass iff < bounds
DISTINCT_DR_A, DISTINCT_ROT_DEG = 0.25, 20.0        # section 9: distinct iff > bounds
FMAX, STEPS = 0.01, 10000                           # section 5: one FIRE run, ASE defaults
HOST_STAGES, HOST_STEPS = (0.02, 0.01, 0.005), 10000
THREADS, MAX_CONCURRENT_MACE = 6, 10
FOUNDATION_SHA256 = "01bfe22100139f424713cf921144e5509cbe353d67aa9fa1be9c6e1e0ed35845"   # section 5
FOUNDATION_FILE = "20231203mace128L1_epoch199model"
MACE_VERSION = "0.3.16"
MACE_Z_REQUIRED = frozenset({1, 6, 7, 17, 20, 38, 53, 55, 82})
PBCL_DEFAULT_A = 2.837                              # section 2
PBCL_RECORD = "results/objective2/s2/stage0/pbcl_source.json"
PBCL_DECISIONS = ("confirmed_2.837", "use_source_value", "provisional_2.837")
NODE_ROOT = "/data"
REF_HOST = "results/fa_host/fa19cs1_pb20i60_233.extxyz"
REF_VAC = "results/fa_host/fa19cspb20i59_232_vI.extxyz"
REF_MEMBERS = ("ref233", "synthetic")              # the only members a mock calculator may touch (N-1)
RECORD_SCHEMAS = {"region": "s2-region-1", "pair": "s2-pair-1", "cell": "s2-cell-1", "vac_start": "s2-vacstart-1",
                  "distinct": "s2-distinct-1", "validity": "s2-validity-1", "mace": "s2-mace-1",
                  "a2validity": "s2-a2validity-1"}
MOCK_K, MOCK_SIGMA_A = 5.0, 0.02                    # mock harmonic: eV/A^2; seeded offset of the free atoms (A)

NOTES = {
    "I-1": "section 4 gaps asserted per host at the plan's rounded pool figures widened by half a last digit",
    "I-2": "region 'within 6.0 A' is d < 6.0 (as scripts/40)",
    "I-3": "the deleted I127 lies within 1.2 A of the UNRELAXED member's v (the relaxed-host test is trivial)",
    "I-4": "host convergence = relax_staged's final-stage flag AND the strict max|F| < 0.005",
    "I-5": "partner gating by relaxed-host positions (organic atoms at their molecule's C) from the relaxed-host "
           "centre; FA = molecules with 2 N found in the parent; appended dopant atoms not compared",
    "I-6/X-6": "host valid iff the 0.005 stage converges AND check 4 against the pool member passes",
    "I-7": "the A2 host cell of region j is s2r_<h>_host<L><j>",
    "I-8": "o<k> per leg; o0 reserved for p0 and kept as a minimum only if p0 is valid; map o<k> -> p<n> recorded",
    "I-9": "Refused on relaxed partners rejects the pair like Inadmissible (site missing for that dopant)",
    "I-39": "mig='allow' at every X site",
    "N-1": "calculators only on synthetic or reference cells (job runner: members ref233/synthetic)",
    "N-2": "MACE only under the node root /data",
    "N-3": "work ids p<n> number the starts in b42.sampled_names order; p0 is the default pose",
    "N-13": "46 enforces --allow-provisional for the shifted Cl starts (42 enforces it only in its CLI)",
    "X-2": "a verified Pb-Cl other than 2.837 A moves the shifted Cl along the s2b-2 direction to the source value, "
           "re-validated V1-V10; start_override and start_sha recorded beside GEOM_SHA",
    "I-A1": "check 4 'within 1.25 / 1.6 A' (organic-inorganic) fails at d <= value, as the spec reads check 2's "
            "'within 1.2 A'; the floor is the literal 'below 0.65 A' (fails at d < 0.65)",
    "I-A2": "check 3 compares the dopant centre with its position in the cell's own builder output (the start of "
            "its relaxation); for A2 with the A1 builder output",
    "I-A3": "ranking ascending by (round(d, 6), index): f1 = last, f2 = second last (no current set depends on it)",
    "I-A4": "check 4 for an A2 cell compares with the start of its A1 relaxation (pool member for host_R); equal to "
            "comparing with the A2 start whenever the A1 cell is valid (topology equality is transitive)",
    "N-A1": "relax_staged's log line (which prints MACE energies) is suppressed; energies only under E_mace_eV",
    "N-A2": "the V+ cell keeps the MIG tag that pp.build_pair sets on the relaxed host; the unrelaxed member's "
            "migrating iodide is recorded beside it (with mig='allow' no admissibility outcome depends on it)",
    "N-A3": "the four farthest sites are also asserted beyond the far bound (fail-closed; over the pool they lie "
            "at >= 9.73 / 10.14 / 10.45 A, section 4)",
    "N-A4": "structure files carry no calculator results; the FIRE log has step and max|F| only; files are read "
            "back from disk before use, so bitwise fixed-atom identity holds against the stored relaxed host",
    "N-A5": "hygiene: JSON refuses any '$'; code is scanned for '$' next to a digit (shell variables are not "
            "currency)",
    "N-A6": "job completion markers: region record, cells/<id>/vac_start.json, pair record, cells/<id>/record.json, "
            "cells/<id>/validity.json, pairs/<h>_<T><j>_<leg>.distinct.json",
    "N-A7": "the Pb-Cl record is checked for internal consistency (decision vs value and level) fail-closed",
    "N-A8": "verified Pb-Cl starts carry the record's level as their tag; provisional starts '[M] starting point'",
    "N-A9": "c1_sites without an explicit m05_cal uses the plan's drawn sites and says so (source field)",
    "N-A10": "every record of this module is written through dump_public (hygiene) atomically",
    "N-A11": "a structure with an element outside C, N, H and INORGANIC is refused by check 4 (no S2 cell has one)",
    "N-A12": "job kind, pose and region keys are derived from the work id and Layout; given values must agree",
    "N-A13": "X-2 override built from the centred Cl, so the shifted starts' admissibility is judged at the source "
             "Pb-Cl only (at d = 2.837 A it reproduces the s2b-2 shifted build to 1e-12 A)",
    "I-F1": "section 11 final-geometry validity (review F1): validate-a2 runs checks 2-5 (host_R: 4) on the final "
            "geometry of an A2 relaxation against the final geometry of its partner (D and V+_R vs host_R, D+V vs "
            "V+_R), with the A1 start for checks 3 and 4 (I-A2, I-A4); a partner without a final geometry: the check "
            "is not evaluated (validate-a2 refuses to run without it, round-2 R2V-1), and the quartet is invalid "
            "through the missing partner",
    "N-A15": "hygiene (review F10): a JSON record may carry no URL and no internet host name (any scheme://, or a "
             "dotted name ending in com, org, net, edu, gov, cn or uk; module names such as ase.io are not host "
             "names); sources are cited by reference and DOI",
    "N-A14": "labels: o0 always names the p0 cell (single-start tokens and default-pose production get o0 at once); "
             "in a multi-start leg o0 is a kept minimum only if p0 is valid (I-8)",
}


class S2Error(RuntimeError):
    """Fail-closed STOP: a plan rule or an invariant of this module does not hold."""


Refused, Inadmissible, BuildError = b42.Refused, b42.Inadmissible, b42.BuildError


# ---------------------------------------------------------------- small helpers
def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sha256_atoms(at):
    """sha256 of positions and numbers bytes, as scripts/29 'host_sha256'."""
    return hashlib.sha256(np.ascontiguousarray(at.positions).tobytes() +
                          np.ascontiguousarray(at.numbers).tobytes()).hexdigest()


def dist_to(at, p):
    """True minimum-image distance of every atom of at to the point p (ase find_mic)."""
    return find_mic(at.positions - np.asarray(p, float), at.cell.array, pbc=True)[1]


def dvec(at, a, b_pos):
    """find_mic vector from point b_pos to atom a."""
    return find_mic(np.atleast_2d(at.positions[a] - b_pos), at.cell.array, pbc=True)[0][0]


def mic_norm(v, cell):
    return float(find_mic(np.atleast_2d(v), cell, pbc=True)[1][0])


def _syms(at):
    return np.array(at.get_chemical_symbols())


def _rel(path):
    """Repository-relative path, or the bare file name outside the repository (no absolute path in a record)."""
    p = os.path.abspath(path)
    return os.path.relpath(p, ROOT) if p.startswith(ROOT + os.sep) else os.path.basename(p)


def _repo(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def no_model():
    """Every geometry-only path ends here (plan section 17 item 2; spec 1.2)."""
    assert "mace" not in sys.modules, "mace was imported on a geometry-only path"
    return True


# ---------------------------------------------------------------- hygiene (spec 5.4) and atomic writes
def _hygiene_patterns():
    # Built from pieces so that this file does not match its own patterns when it is scanned.
    sl = "/"
    pats = [("local path (" + sl + "Users)", re.compile(sl + "Users" + sl)),
            ("local path (" + sl + "private)", re.compile(sl + "private" + sl)),
            ("local path (" + sl + "home)", re.compile(sl + "home" + sl)),
            ("local path (" + sl + "tmp)", re.compile(r"(?<![\w.])" + sl + "tmp" + sl)),
            ("work-area word", re.compile("scr" + "atch", re.I)),
            ("environment word", re.compile("v" + "env", re.I)),
            ("IPv4 address", re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")),
            ("e-mail address", re.compile(r"[A-Za-z0-9._%+-]+" + chr(64) + r"[A-Za-z0-9-]+\.[A-Za-z][A-Za-z.]+")),
            ("instance or disk id", re.compile(r"\b(?:i|d)-[0-9a-z]{10,}\b")),
            ("currency symbol", re.compile("[\u00a5\u20ac\u00a3\u5143]")),
            ("currency code", re.compile(r"\b(?:" + "US" + "D|" + "CN" + "Y|" + "RM" + r"B)\b"))]
    return pats


# JSON records only (N-A15): no URL and no internet host name. Code may name a scheme (the spot URL is read at run
# time, never written), so these two are not applied to kind 'code'.
_HYGIENE_JSON = [("URL", re.compile(r"\b[a-z][a-z0-9+.-]*" + ":" + "//", re.I)),
                 ("host name", re.compile(r"\b(?:[a-z0-9-]+\.)+(?:com|org|net|edu|gov|cn|uk)\b",
                                          re.I))]


_HYGIENE = _hygiene_patterns()


def hygiene_violations(text, *, kind="json"):
    """Names of the public-repository rules the text breaks (spec 5.4). kind 'json' refuses any dollar sign;
    kind 'code' (scripts, wrappers) flags a dollar sign only next to a digit, i.e. an amount (N-A5)."""
    out = [f"{name}: {m.group(0)!r}" for name, rx in _HYGIENE for m in [rx.search(text)] if m]
    if kind == "json":
        out += [f"{name}: {m.group(0)!r}" for name, rx in _HYGIENE_JSON for m in [rx.search(text)] if m]
    dollar = re.compile(r"\$" if kind == "json" else r"\$\s?\d|\d\s?\$")
    m = dollar.search(text)
    if m:
        out.append(f"currency symbol: {m.group(0)!r}")
    return out


def _write_text_atomic(text, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        fh.write(text); fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp, path)


def dump_public(obj, path):
    """Serialise obj (indent 1, unrounded floats), refuse it if it breaks a hygiene rule, write it atomically."""
    text = json.dumps(obj, indent=1)
    bad = hygiene_violations(text, kind="json")
    if bad:
        raise S2Error(f"{os.path.basename(path)}: refused by the hygiene rules: {bad}")
    _write_text_atomic(text, path)
    return path


def _strip_mace(obj):
    if isinstance(obj, dict):
        return {k: _strip_mace(v) for k, v in obj.items() if k != "E_mace_eV"}
    if isinstance(obj, list):
        return [_strip_mace(v) for v in obj]
    return obj


def load_record(path, *, blind=True):
    """A record of this module; blind (default) removes every E_mace_eV at any depth. Only scripts/48 evaluate
    passes blind=False (spec 12.2 item 3)."""
    rec = json.load(open(path))
    return _strip_mace(rec) if blind else rec


def write_cell(path, atoms):
    """Write a structure (extxyz, tags kept, no calculator, no constraint) atomically; return the read-back
    Atoms, which is what every later step uses (positions are stored to 1e-8 A; N-A4)."""
    x = Atoms(numbers=atoms.numbers.copy(), positions=atoms.positions.copy(), cell=atoms.cell.array.copy(),
              pbc=atoms.pbc.copy())
    tags = np.asarray(atoms.get_tags(), int)
    if tags.any():
        x.set_tags(tags)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp.extxyz"
    write(tmp, x, format="extxyz")
    with open(tmp, "rb+") as fh:
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    return read_cell(path)


def read_cell(path):
    at = read(path, format="extxyz")
    at.calc = None
    at.set_constraint()
    return at


def git(*args):
    try:
        p = subprocess.run(["git", "-C", ROOT, *args], capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return p.stdout.decode() if p.returncode == 0 else None


def code_state():
    """sha256 of this script and of the numbered scripts it loads; git head and whether the tree is clean."""
    sha = {"46": sha256_file(os.path.abspath(__file__))}
    sha.update({k: sha256_file(os.path.abspath(m.__file__)) for k, m in HELPERS.items()})
    head, st = git("rev-parse", "HEAD"), git("status", "--porcelain")
    return {"script_sha256": sha, "git": None if head is None or st is None else
            {"head": head.strip(), "clean": st.strip() == ""}}


def versions(extra=None):
    import ase
    v = {"ase": ase.__version__, "numpy": np.__version__, "python": platform.python_version()}
    v.update(extra or {})
    return v


# ---------------------------------------------------------------- sites (plan section 4)
@dataclass(frozen=True)
class Ctx:
    """One pool member or the reference cell, unrelaxed: host, its V partner (pp.build_pair, MIG-tagged), the
    member's own v, the vacancy index and the migrating iodide (V and host numbering)."""
    member: str
    host: Atoms
    vac: Atoms
    vpos: np.ndarray
    vi: int
    mig_vac: int
    mig_host: int


def pool_path(member):
    if not re.fullmatch(r"m(0\d|[12]\d|3[0-5])", str(member)):
        raise S2Error(f"{member!r} is not a pool member m00-m35")
    return os.path.join(ROOT, b42.POOL, f"{member}.extxyz")


def host_context(member, *, pool=None, vac_ref=None):
    """Ctx of a pool member (b42.vacancy_context); asserts vi == VI and that the deleted atom is an I."""
    if member == "ref233":
        return ref_context()
    path = pool_path(member)
    if pool is not None:
        path = os.path.join(pool, f"{member}.extxyz")
    pool = pool or os.path.join(ROOT, b42.POOL)
    vac_ref = vac_ref or os.path.join(ROOT, b42.VAC_REF)
    host = read(path)
    vac, vpos, vi, mig = b42.vacancy_context(host, pool, vac_ref)
    if vi != VI or host.get_chemical_symbols()[vi] != "I":
        raise S2Error(f"{member}: vacancy index {vi} ({host.get_chemical_symbols()[vi]}), the plan has I{VI}")
    return Ctx(member, host, vac, np.array(vpos, float), int(vi), int(mig), int(mig) + (1 if mig >= vi else 0))


def ref_point():
    return s29.ref_vacancy_position(os.path.join(ROOT, b42.POOL), os.path.join(ROOT, b42.VAC_REF))


def ref_context():
    """Ctx of the 233/232 reference pair: the 232 file must equal the 233 file minus I127 bitwise; the V cell is
    pp.build_pair's (it carries the MIG tag that b42.build_paired needs)."""
    host = read(os.path.join(ROOT, REF_HOST))
    vfile = read(os.path.join(ROOT, REF_VAC))
    vac, vpos, mig = pp.build_pair(host, ref_point(), None, None)
    s = _syms(host)
    iod = np.flatnonzero(s == "I")
    vi = int(iod[np.argmin(dist_to(host, ref_point())[iod])])
    if vi != VI or not np.array_equal(host.positions[vi], vpos):
        raise S2Error(f"reference cell: vacancy index {vi}, expected {VI}")
    if not (np.array_equal(vac.numbers, vfile.numbers) and np.array_equal(vac.positions, vfile.positions)
            and np.array_equal(np.delete(host.positions, vi, axis=0), vfile.positions)):
        raise S2Error("reference cells: the 232-atom file is not the 233-atom file minus I127 (bitwise)")
    return Ctx("ref233", host, vac, np.array(vpos, float), vi, int(mig), int(mig) + (1 if mig >= vi else 0))


def _site_token(L):
    return {"B": "Sr", "A": "Cs", "X": "Cl"}[L]


def rank_sites(ctx, L):
    """[(index, unrounded true-MIC distance to v)] of every eligible site of sublattice L, ascending by
    (round(d, 6), index) (section 4; I-A3)."""
    s = b42.list_sites(ctx.host, _site_token(L), vi=ctx.vi, vpos=ctx.vpos)
    return sorted(((int(j), float(d)) for j, d in s), key=lambda t: (round(t[1], 6), t[0]))


def site_sets(ctx):
    """Section 4 site sets of one member: first shell, far pair (f1 farthest, f2), the four farthest (noise pilot)
    and the 19 production sites; asserts the first-shell sets, the gaps and the far bounds (S2Error otherwise)."""
    out = {"member": ctx.member, "vi": ctx.vi, "mig_host": ctx.mig_host}
    for L in "BAX":
        r = rank_sites(ctx, L)
        d = [x[1] for x in r]
        if L == "X":
            first = [j for j, _ in r[:X_FIRST_N]]
            if not (d[X_FIRST_N - 1] <= GAPS["X_8th_max"] and d[X_FIRST_N] >= GAPS["X_9th_min"]):
                raise S2Error(f"{ctx.member} X: 8th I {d[7]:.4f} A, 9th {d[8]:.4f} A violate the section 4 gap")
        else:
            first = [j for j, x in r if x < FIRST_CUT_A[L]]
            k = len(first)
            if L == "B" and not (k == 2 and d[2] >= GAPS["B_next_min"]):
                raise S2Error(f"{ctx.member} B: {k} Pb below 5.0 A, next at {d[k]:.4f} A (section 4 gap)")
            if L == "A" and not (k == 3 and d[2] <= GAPS["A_first_max"] and d[3] >= GAPS["A_next_min"]):
                raise S2Error(f"{ctx.member} A: {k} FA below 6.0 A, 3rd {d[2]:.4f}, next {d[3]:.4f} A (section 4 gap)")
        if sorted(first) != sorted(FIRST_SHELL[L]):
            raise S2Error(f"{ctx.member} {L}: first shell {sorted(first)} != section 4 {sorted(FIRST_SHELL[L])}")
        far = [r[-1][0], r[-2][0]]
        far4 = [x[0] for x in r[-4:][::-1]]
        for j, x in r[-4:]:                          # far pair beyond the bound; the four farthest too (N-A3)
            if not x > FAR_MIN_A[L]:
                raise S2Error(f"{ctx.member} {L}{j}: {x:.4f} A is not beyond the far bound {FAR_MIN_A[L]} A")
        if L == "X" and ctx.mig_host not in first:
            raise S2Error(f"{ctx.member}: the migrating iodide I{ctx.mig_host} is not in the X first shell")
        out[L] = {"ranked": r, "first": sorted(first), "far": far, "far4": far4,
                  "production": sorted(first) + far, "d": {j: x for j, x in r}}
    cs = np.flatnonzero(_syms(ctx.host) == "Cs")
    if len(cs) != 1:
        raise S2Error(f"{ctx.member}: {len(cs)} Cs atoms, expected the one native Cs")
    out["cs_v_A"] = float(dist_to(ctx.host, ctx.vpos)[cs[0]])
    if not out["cs_v_A"] < FIRST_CUT_A["A"]:
        raise S2Error(f"{ctx.member}: the native Cs lies {out['cs_v_A']:.3f} A from v, not in the A first shell")
    return out


def assert_site_tables(member, sets):
    """The section 4 table row of the member (far-pair indices and order exact, distances to the 2 dp of the
    table, migrating iodide, Cs-v) and, for the pilots, the four-farthest table; S2Error on any mismatch."""
    if member not in SITE_TABLE:
        raise S2Error(f"{member} has no row in the section 4 table")
    role, mig, csv, *pairs = SITE_TABLE[member]
    if sets["mig_host"] != mig:
        raise S2Error(f"{member}: migrating iodide I{sets['mig_host']}, table I{mig}")
    if abs(sets["cs_v_A"] - csv) > TABLE_TOL_A:
        raise S2Error(f"{member}: Cs-v {sets['cs_v_A']:.4f} A, table {csv}")
    for L, pair in zip("BAX", pairs):
        got = sets[L]["far"]
        if got != [pair[0][0], pair[1][0]]:
            raise S2Error(f"{member} {L}: far pair {got}, table {[p[0] for p in pair]}")
        for j, dt in pair:
            if abs(sets[L]["d"][j] - dt) > TABLE_TOL_A:
                raise S2Error(f"{member} {L}{j}: {sets[L]['d'][j]:.4f} A, table {dt}")
    if member in FAR4_TABLE:
        for L in "BAX":
            if tuple(sets[L]["far4"]) != FAR4_TABLE[member][L]:
                raise S2Error(f"{member} {L}: four farthest {sets[L]['far4']}, table {FAR4_TABLE[member][L]}")
    return True


def m05_cal_sites(m05_cal=None):
    """The m05 calibration sites (B, A, X): the plan's draw unless the Stage-0 admissibility check chose the next
    site in draw order (section 11); any other choice is refused."""
    cal = dict(CAL_SITES["m05"]) if m05_cal is None else {k: int(v) for k, v in m05_cal.items()}
    if cal.get("B") != 124:
        raise S2Error(f"m05 B calibration site must be Pb124 (chosen, not drawn; no fallback): {cal}")
    for L in "AX":
        if cal.get(L) not in [j for j, _ in M05_DRAW_ORDER[L]]:
            raise S2Error(f"m05 {L} calibration site {cal.get(L)} is not in the section 11 draw order")
    return cal


def c1_sites(member, *, m05_cal=None, sets=None):
    """C1 sites of a pilot (sections 7-11): noise (four farthest per sublattice), calibration (= start set),
    and on m30 the pose, G1, spin and Sr far-quartet sites, each asserted against its defining rule."""
    if member not in PILOTS:
        raise S2Error(f"{member} is not a pilot host")
    sets = sets or site_sets(host_context(member))
    cal = dict(CAL_SITES["m30"]) if member == "m30" else m05_cal_sites(m05_cal)
    out = {"member": member, "noise": {L: list(sets[L]["far4"]) for L in "BAX"}, "cal": cal,
           "cal_source": "plan" if member == "m30" or m05_cal is None else "stage-0 admissibility",
           "pose": {}, "g1": {}, "spin": {}, "sr_far": None}
    if member == "m05" and m05_cal is None:
        out["cal_source"] = "plan draw (stage-0 admissibility choice not supplied)"       # N-A9
    for L, j in cal.items():
        if j not in sets[L]["first"]:
            raise S2Error(f"{member} calibration site {L}{j} is not first-shell")
    nearest_fa = sets["A"]["ranked"][0][0]
    if nearest_fa != 128:
        raise S2Error(f"{member}: the nearest FA is {nearest_fa}, the plan's FA128 (sections 9, 11)")
    if member == "m30":
        if sets["mig_host"] != CAL_SITES["m30"]["X"]:
            raise S2Error("m30: the migrating iodide is not I138 (section 11)")
        far = {L: sets[L]["far"][0] for L in "BAX"}
        if not (POSE_SITES["Cs"] == (nearest_fa, far["A"]) and POSE_SITES["Cl"] == (sets["mig_host"], far["X"])
                and SPIN_SITES == {"Cl": far["X"], "Ca": far["B"]} and SR_FAR_SITE == far["B"]):
            raise S2Error(f"m30: pose/spin/far sites {POSE_SITES}, {SPIN_SITES}, {SR_FAR_SITE} do not follow sections "
                          f"7, 9 and 11 (nearest FA {nearest_fa}, farthest {far})")
        out.update({"pose": {"Cs": {"near": POSE_SITES["Cs"][0], "far": POSE_SITES["Cs"][1]},
                             "Cl": {"near": POSE_SITES["Cl"][0], "far": POSE_SITES["Cl"][1]}},
                    "g1": dict(G1_SITES), "spin": dict(SPIN_SITES), "sr_far": SR_FAR_SITE})
    else:
        if sets["mig_host"] == cal["X"]:
            raise S2Error("m05: the X calibration site must not be the migrating iodide (section 11)")
    return out


def label_sites(member, sets=None):
    """Sites a label may name on a host: first shell plus far pair (production) or the four farthest (pilots)."""
    sets = sets or site_sets(host_context(member))
    key = "far4" if member in PILOTS else "far"
    return {L: set(sets[L]["first"]) | set(sets[L][key]) for L in "BAX"}


def site_roles(member, L, j, sets, c1=None):
    roles = []
    if j in sets[L]["first"]:
        roles.append("first")
    if j in sets[L]["far"]:
        roles.append("far")
    if member in PILOTS and j in sets[L]["far4"]:
        roles.append("far4")
    if c1:
        if c1["cal"].get(L) == j:
            roles.append("cal")
        for t, p in c1["pose"].items():
            if SUBLATTICE[t] == L and p["near"] == j:
                roles.append("pose_near")
            if SUBLATTICE[t] == L and p["far"] == j:
                roles.append("pose_far")
    return roles


def sublattice_of(at, j):
    s = at.get_chemical_symbols()[int(j)]
    if s not in ("Pb", "C", "I"):
        raise S2Error(f"site {j} is {s}, not a Pb, FA carbon or I")
    return {"Pb": "B", "C": "A", "I": "X"}[s]


# ---------------------------------------------------------------- labels (plan section 5; spec 3)
IDX = r"(?:0|[1-9]\d*)"
BODY = (r"(?P<host>m\d\d)_(?:"
        r"(?P<hostcell>host)(?:(?P<hL>[BAX])(?P<hj>" + IDX + r"))?"
        r"|V(?P<vL>[BAX])(?P<vj>" + IDX + r")"
        r"|(?P<tok>Sr|Ca|Cl|Cs|GA)(?P<j>" + IDX + r")o(?P<k>" + IDX + r")_(?P<leg>novac|vac))")
LABEL_RE = re.compile(r"(?P<prefix>s2spin|s2g1|s2r|s2)_" + BODY + r"(?P<q0>_q0)?(?:_e(?P<ecut>50|60))?")
WORK_RE = re.compile(r"s2_(?P<host>m\d\d|ref233)_(?:(?P<hostcell>host)|V(?P<vL>[BAX])(?P<vj>" + IDX + r")"
                     r"|(?P<tok>Sr|Ca|Cl|Cs|GA)(?P<j>" + IDX + r")p(?P<n>" + IDX + r")_(?P<leg>novac|vac))")
REF_RE = re.compile(r"(?P<prefix>s2tp|s2smoke)_ref232_(?P<name>[a-z0-9]+)")
REF_NAMES = {"s2smoke": ("n1", "n3", "rst", "rst64", "rst2x32"),     # the C1 rows of section 16 (c1_label_sets)
             "s2tp": ("np48", "np64", "np32a", "np32b")}
G1_LABELS = ("s2g1_m30_host_e60", "s2g1_m30_Cl138o0_novac_e60", "s2g1_m30_Cl138o0_novac_e50",
             "s2g1_m30_Ca136o0_novac_e60", "s2g1_m30_Ca136o0_novac_e50")
SPIN_LABELS = ("s2spin_m30_Cl175o0_vac", "s2spin_m30_Ca76o0_vac")
LABEL_HOSTS = tuple(PILOTS) + tuple(m for m, _ in DRAW)


def n_starts(token):
    return len(b42.sampled_names(token))


def parse_label(label):
    """Fields of an S2 QE label (LABEL_RE or REF_RE, fullmatch) with the derived sublattice, cell kind, vacancy
    flag and tot_charge class (+1 for a vacancy cell, 0 for a vacancy-free cell and for _q0 rows)."""
    m = REF_RE.fullmatch(label)
    if m:
        return {"label": label, "prefix": m["prefix"], "ref": True, "name": m["name"], "host": "ref232",
                "kind": "ref", "vacancy": True, "tot_charge": 1}
    m = LABEL_RE.fullmatch(label)
    if not m:
        raise S2Error(f"{label!r} is not an S2 label (section 5 grammar)")
    g = m.groupdict()
    out = {"label": label, "prefix": g["prefix"], "ref": False, "host": g["host"], "q0": bool(g["q0"]),
           "ecut": None if g["ecut"] is None else int(g["ecut"]), "token": None, "k": None, "leg": None,
           "L": None, "j": None}
    if g["hostcell"]:
        out.update({"kind": "host", "L": g["hL"], "j": None if g["hj"] is None else int(g["hj"])})
    elif g["vL"]:
        out.update({"kind": "V", "L": g["vL"], "j": int(g["vj"])})
    else:
        out.update({"kind": "D" if g["leg"] == "novac" else "DV", "token": g["tok"], "L": SUBLATTICE[g["tok"]],
                    "j": int(g["j"]), "k": int(g["k"]), "leg": g["leg"]})
    out["vacancy"] = out["kind"] in ("V", "DV")
    out["tot_charge"] = 1 if out["vacancy"] and not out["q0"] else 0
    return out


def check_label(label, sites=None):
    """Grammar and semantic constraints of spec 3.1 (S2Error otherwise). sites: {host: {L: set}} restricts j to the
    section 4 sites of each host (label_sites)."""
    p = parse_label(label)
    if p["ref"]:                                     # reference rows: any REF_RE name (spec 3.1)
        return p
    pre, h, kind = p["prefix"], p["host"], p["kind"]
    if h not in LABEL_HOSTS:
        raise S2Error(f"{label}: host {h} is neither a pilot nor in the section 3 draw")
    if pre == "s2g1":
        if label not in G1_LABELS:
            raise S2Error(f"{label}: not one of the five G1 labels (section 7)")
    elif pre == "s2spin":
        if label not in SPIN_LABELS:
            raise S2Error(f"{label}: not one of the two spin rows (section 7)")
    elif p["ecut"] is not None:
        raise S2Error(f"{label}: _e<cut> only on s2g1_ labels")
    if p["q0"] and not (pre == "s2" and p["vacancy"]):
        raise S2Error(f"{label}: _q0 only on an s2_ vacancy cell (V or _vac; section 10)")
    if pre == "s2" and kind == "host" and p["L"] is not None:
        raise S2Error(f"{label}: an s2_ host label has no site")
    if pre == "s2r":
        if h not in PILOTS:
            raise S2Error(f"{label}: A2 relaxations run on the pilot hosts only (section 11)")
        if kind == "host" and p["L"] is None:
            raise S2Error(f"{label}: an A2 host cell names its region, s2r_<h>_host<L><j> (I-7)")
        if p["k"] not in (None, 0):
            raise S2Error(f"{label}: A2 cells are at the default pose only (o0; section 11)")
    if p["token"] is not None:
        if p["k"] >= n_starts(p["token"]):
            raise S2Error(f"{label}: o{p['k']} exceeds the {n_starts(p['token'])} starts of {p['token']}")
        if p["k"] >= 1 and p["token"] not in MULTI_START:
            raise S2Error(f"{label}: {p['token']} has one start (o0 only; section 2)")
    if sites is not None and p["L"] is not None and p["j"] is not None:
        allowed = sites.get(h, {}).get(p["L"])
        if allowed is None or p["j"] not in allowed:
            raise S2Error(f"{label}: {p['L']}{p['j']} is not a section 4 site of {h}")
    return p


def make_label(prefix, host, kind, *, L=None, j=None, token=None, k=None, leg=None, q0=False, ecut=None):
    """Build an S2 QE label; kind 'host' (with L, j for s2r_), 'V', 'D', 'DV' (leg from the kind)."""
    if kind == "host":
        body = "host" + ("" if L is None else f"{L}{int(j)}")
    elif kind == "V":
        body = f"V{L}{int(j)}"
    elif kind in ("D", "DV"):
        body = f"{token}{int(j)}o{int(k)}_{'novac' if kind == 'D' else 'vac'}"
        if leg is not None and leg != ("novac" if kind == "D" else "vac"):
            raise S2Error(f"kind {kind} with leg {leg}")
    else:
        raise S2Error(f"unknown label kind {kind!r}")
    lab = f"{prefix}_{host}_{body}" + ("_q0" if q0 else "") + ("" if ecut is None else f"_e{int(ecut)}")
    if not LABEL_RE.fullmatch(lab):
        raise S2Error(f"{lab!r} does not match the label grammar")
    return lab


def make_work_id(host, kind, *, L=None, j=None, token=None, n=None, leg=None):
    if kind == "host":
        wid = f"s2_{host}_host"
    elif kind == "V":
        wid = f"s2_{host}_V{L}{int(j)}"
    elif kind in ("D", "DV"):
        wid = f"s2_{host}_{token}{int(j)}p{int(n)}_{'novac' if kind == 'D' else 'vac'}"
    else:
        raise S2Error(f"unknown work-id kind {kind!r}")
    if not WORK_RE.fullmatch(wid):
        raise S2Error(f"{wid!r} does not match the work-id grammar")
    return wid


def parse_work_id(wid):
    m = WORK_RE.fullmatch(wid)
    if not m:
        raise S2Error(f"{wid!r} is not an S2 work id")
    g = m.groupdict()
    out = {"work_id": wid, "host": g["host"], "token": None, "n": None, "leg": None}
    if g["hostcell"]:
        out.update({"kind": "host", "L": None, "j": None})
    elif g["vL"]:
        out.update({"kind": "V", "L": g["vL"], "j": int(g["vj"])})
    else:
        out.update({"kind": "D" if g["leg"] == "novac" else "DV", "token": g["tok"], "L": SUBLATTICE[g["tok"]],
                    "j": int(g["j"]), "n": int(g["n"]), "leg": g["leg"]})
    out["start"] = None if out["n"] is None else f"p{out['n']}"
    return out


def check_work_id(wid, sites=None):
    p = parse_work_id(wid)
    if p["host"] not in LABEL_HOSTS + ("ref233",):
        raise S2Error(f"{wid}: host {p['host']} is neither a pilot, a drawn host nor ref233")
    if p["token"] is not None and p["n"] >= n_starts(p["token"]):
        raise S2Error(f"{wid}: p{p['n']} exceeds the {n_starts(p['token'])} starts of {p['token']}")
    if sites is not None and p["j"] is not None:
        allowed = sites.get(p["host"], {}).get(p["L"])
        if allowed is None or p["j"] not in allowed:
            raise S2Error(f"{wid}: {p['L']}{p['j']} is not a section 4 site of {p['host']}")
    return p


def label_of_start(work_id, k):
    """The QE label of a dopant cell whose start is kept as minimum o<k>."""
    p = parse_work_id(work_id)
    return make_label("s2", p["host"], p["kind"], token=p["token"], j=p["j"], k=k)


def _region_cells(h, L, j, tokens):
    out = [make_label("s2r", h, "host", L=L, j=j), make_label("s2r", h, "V", L=L, j=j)]
    for t in tokens:
        out += [make_label("s2r", h, "D", token=t, j=j, k=0), make_label("s2r", h, "DV", token=t, j=j, k=0)]
    return out


def a2_order(m05_cal=None):
    """The fixed A2 orders of section 11: C2 (m30; 10) and C4 (26), labels in run order."""
    c = m05_cal_sites(m05_cal)
    q = _region_cells("m30", "B", 136, ("Sr",))
    c2 = [q[1], q[0], q[2], q[3]] + [_region_cells("m30", "B", 76, ())[0], _region_cells("m30", "B", 76, ())[1],
                                     make_label("s2r", "m30", "D", token="Sr", j=76, k=0),
                                     make_label("s2r", "m30", "DV", token="Sr", j=76, k=0)] + \
        [make_label("s2r", "m30", "D", token="Ca", j=136, k=0), make_label("s2r", "m30", "DV", token="Ca", j=136, k=0)]
    c4 = (_region_cells("m30", "X", 138, ("Cl",)) + _region_cells("m30", "A", 128, ("Cs", "GA")) +
          _region_cells("m05", "B", c["B"], ("Sr", "Ca")) + _region_cells("m05", "X", c["X"], ("Cl",)) +
          _region_cells("m05", "A", c["A"], ("Cs", "GA")))
    assert len(c2) == 10 and len(c4) == 26 and len(set(c2 + c4)) == 36
    return {"c2": c2, "c4": c4}


def campaign_of(label, state=None):
    """c1/c2/c3/c4 of a QE label or work id: reference rows, G1, spin and pilot cells are C1; A2 labels by the
    fixed lists; production-host cells C3 (state['stage0'] production lists when given)."""
    if REF_RE.fullmatch(label):
        return "c1"
    p = parse_label(label) if LABEL_RE.fullmatch(label) else parse_work_id(label)
    if p.get("prefix") in ("s2g1", "s2spin"):
        return "c1"
    if p.get("prefix") == "s2r":
        lists = a2_order((state or {}).get("stage0", {}).get("m05_cal"))
        for c, l in lists.items():
            if label in l:
                return c
        raise S2Error(f"{label}: an A2 label outside the section 11 orders")
    if p["host"] in PILOTS or p["host"] == "ref233":
        return "c1"
    prod = ((state or {}).get("stage0") or {}).get("production_n10" if (state or {}).get("n") == 10 else "production_n8")
    if prod:                                          # a state with a production list decides; else draw ranks 1-12
        if p["host"] in prod:
            return "c3"
        raise S2Error(f"{label}: host {p['host']} is not in the production list of the state")
    if p["host"] in [m for m, _ in DRAW[:12]]:
        return "c3"
    raise S2Error(f"{label}: host {p['host']} is outside draw ranks 1-12")


def c1_label_sets(m05_cal=None, sites=None):
    """Every C1 QE label and work id (spec 3.3), with the pose pilot at its upper bound (every start a kept
    minimum). sites: {member: site_sets} (computed if absent; geometry only)."""
    sites = sites or {p: site_sets(host_context(p)) for p in PILOTS}
    c1 = {p: c1_sites(p, m05_cal=m05_cal, sets=sites[p]) for p in PILOTS}
    out = {"smoke": [f"s2smoke_ref232_{x}" for x in ("n1", "n3", "rst")],
           "tp": [f"s2tp_ref232_{x}" for x in REF_NAMES["s2tp"]], "g1": list(G1_LABELS), "spin": list(SPIN_LABELS),
           "noise": {}, "step0": ["s2_m30_VB136", "s2_m30_Sr136o0_vac"], "pose": [], "q0": [],
           "a2": a2_order(m05_cal), "work": {"host": [], "V": [], "noise": [], "start_set": [], "pose_extra": []}}
    for p in PILOTS:
        lab = [make_label("s2", p, "host")]
        for L in "BAX":
            for f in c1[p]["noise"][L]:
                lab.append(make_label("s2", p, "V", L=L, j=f))
                for t in TOKENS_OF[L]:
                    lab += [make_label("s2", p, "D", token=t, j=f, k=0), make_label("s2", p, "DV", token=t, j=f, k=0)]
                    out["work"]["noise"] += [make_work_id(p, "D", token=t, j=f, n=0),
                                             make_work_id(p, "DV", token=t, j=f, n=0)]
        out["noise"][p] = lab
        out["work"]["host"].append(make_work_id(p, "host"))
        out["work"]["V"] += [make_work_id(p, "V", L=L, j=f) for L in "BAX" for f in c1[p]["noise"][L]]
        for L, j in c1[p]["cal"].items():
            out["work"]["V"].append(make_work_id(p, "V", L=L, j=j))
            for t in TOKENS_OF[L]:
                out["work"]["start_set"] += [make_work_id(p, "D", token=t, j=j, n=0),
                                             make_work_id(p, "DV", token=t, j=j, n=0)]
    for t, s in c1["m30"]["pose"].items():
        for where, j in s.items():
            for n in range(n_starts(t)):
                if n == 0 and where == "far":
                    continue                          # the far defaults are noise single points (section 9)
                out["pose"] += [make_label("s2", "m30", "D", token=t, j=j, k=n),
                                make_label("s2", "m30", "DV", token=t, j=j, k=n)]
                if n:
                    out["work"]["pose_extra"] += [make_work_id("m30", "D", token=t, j=j, n=n),
                                                  make_work_id("m30", "DV", token=t, j=j, n=n)]
    for q in ("VB136", "Sr136o0_vac", "Ca136o0_vac", "VB76", "Sr76o0_vac", "VX138", "Cl138o0_vac", "VA128",
              "Cs128o0_vac", "GA128o0_vac"):
        out["q0"].append(f"s2_m30_{q}_q0")
    return out


# ---------------------------------------------------------------- regions and index transfer (plan section 4)
def region_id(member, site, free):
    """sha256 of the canonical JSON of {member, site, sorted free host indices} (section 4)."""
    free = sorted(int(i) for i in free)
    return hashlib.sha256(json.dumps({"free": free, "member": member, "site": int(site)}, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def host_molecules(at):
    """{carbon: (molecule atoms, N atoms)} by bonding (scripts/38 molecule); every organic atom in one molecule."""
    sym, cell = _syms(at), at.cell.array
    mols = {int(c): a38.molecule(at, int(c), sym, cell) for c in np.flatnonzero(sym == "C")}
    flat = sorted(i for m, _ in mols.values() for i in m)
    if flat != [int(i) for i in np.flatnonzero(np.isin(sym, ORGANIC))]:
        raise S2Error("organic atoms are not assigned to exactly one molecule")
    return mols


def build_region(host_relaxed, member, site, *, vi=VI, roles=None, host_work_id=None):
    """Region R_j of section 4 on the S2-relaxed host: centres I127 and site j (relaxed-host positions); every
    inorganic atom (Pb, I, Cs) with d < 6.0 A of either centre; molecules free or fixed whole by their carbon."""
    at, site = host_relaxed, int(site)
    sym, cell = _syms(at), at.cell.array
    if sym[vi] != "I" or site == vi:
        raise S2Error(f"{member}: region of site {site} with vacancy index {vi} ({sym[vi]})")
    L = sublattice_of(at, site)
    if not set(sym) <= set(HOST_INORGANIC) | set(ORGANIC):
        raise S2Error(f"{member}: host contains {sorted(set(sym))}; a region is built on an undoped host only")
    mols = host_molecules(at)
    if L == "A" and len(mols[site][1]) != 2:
        raise S2Error(f"{member}: A site {site} is not an FA carbon")
    cen = {"v": at.positions[vi].copy(), "site": at.positions[site].copy()}
    d = np.minimum(dist_to(at, cen["v"]), dist_to(at, cen["site"]))
    org = np.isin(sym, ORGANIC)
    inorg = [int(i) for i in np.flatnonzero(~org & (d < REGION_RADIUS_A))]
    cfree = sorted(c for c in mols if d[c] < REGION_RADIUS_A)
    free = sorted(inorg + [i for c in cfree for i in mols[c][0]])
    out_inorg = [int(i) for i in np.flatnonzero(~org) if int(i) not in set(inorg)]
    cout = [c for c in mols if c not in set(cfree)]
    ext = lambda f, idx: float(f(d[idx])) if len(idx) else None
    return {"schema": RECORD_SCHEMAS["region"], "member": member, "site": site, "sublattice": L,
            "site_roles": roles or [], "radius_A": REGION_RADIUS_A,
            "rule": "inorganic (Pb, I, Cs) with d < 6.0 A of either centre; organic molecules whole by C",
            "vacancy_index": vi, "centres": {k: [float(x) for x in v] for k, v in cen.items()},
            "free": free, "n_free": len(free), "inorganic_free": inorg, "molecule_carbons_free": cfree,
            "margins_A": {"inorganic_inside_max": ext(max, inorg), "inorganic_outside_min": ext(min, out_inorg),
                          "C_inside_max": ext(max, cfree), "C_outside_min": ext(min, cout)},
            "host_source": {"work_id": host_work_id, "sha256": sha256_atoms(at)},
            "region_id": region_id(member, site, free)}


def check_region_record(reg):
    if reg.get("schema") != RECORD_SCHEMAS["region"] or reg["region_id"] != region_id(reg["member"], reg["site"],
                                                                                        reg["free"]):
        raise S2Error(f"region record of {reg.get('member')} {reg.get('site')}: schema or region_id does not match")
    return reg


def to_vac_map(vi=VI):
    """host -> V: j -> j if j < vi else j - 1; vi has no image."""
    vi = int(vi)

    def f(j):
        j = int(j)
        if j == vi:
            raise S2Error(f"atom {vi} is the deleted vacancy iodide")
        return j if j < vi else j - 1
    return f


def _from_vac(vi=VI):
    return lambda jv: int(jv) if int(jv) < vi else int(jv) + 1


def _leg_maps(built):
    """(old_to_new {int: int}, members [int], centre int | None) of a b42.Built, of a pair-record leg dict or of any
    object with old_to_new and members (centre is needed by check 3 only)."""
    if isinstance(built, dict):
        c = built.get("centre")
        return ({int(k): int(v) for k, v in built["old_to_new"].items()}, [int(m) for m in built["members"]],
                None if c is None else int(c))
    c = getattr(built, "centre", None)
    return ({int(k): int(v) for k, v in dict(built.old_to_new).items()}, [int(m) for m in built.members],
            None if c is None else int(c))


def free_in_cell(region, cell_kind, *, built=None, vi=VI):
    """The region's free set in the numbering of a cell (section 4 'Transfer'): host as is; V by to_vac (I127
    drops); D through the host-leg old_to_new; D+V through to_vac and the V-leg old_to_new. Deleted atoms drop out,
    every dopant member is free."""
    fh = sorted(int(i) for i in region["free"])
    tv = to_vac_map(vi)
    if cell_kind == "host":
        return fh
    base = [tv(i) for i in fh if i != vi]
    if cell_kind == "V":
        return sorted(base)
    if cell_kind not in ("D", "DV") or built is None:
        raise S2Error(f"free_in_cell: kind {cell_kind!r} needs the built leg")
    o2n, members, _ = _leg_maps(built)
    src = fh if cell_kind == "D" else base
    image = sorted(o2n[i] for i in src if i in o2n)
    retained = set(o2n.values())
    for m in members:                                 # a retained dopant atom lies at the site, inside its region
        if m in retained and m not in set(image):
            raise S2Error(f"dopant member {m} is retained but outside the region image")
    extra = [m for m in members if m not in set(image)]
    free = sorted(set(image) | set(members))
    if len(free) != len(image) + len(extra) or not set(members) <= set(free):
        raise S2Error("free_in_cell: inconsistent image")
    return free


def cell_maps(cell_kind, *, built=None, n_host=None, vi=VI):
    """(cell -> host, cell -> parent) index maps of a cell's retained atoms. Parent: the relaxed host for V and D,
    the relaxed V+_Rj for D+V."""
    fv = _from_vac(vi)
    if cell_kind == "host":
        idm = {i: i for i in range(int(n_host))}
        return idm, idm
    if cell_kind == "V":
        m = {jv: fv(jv) for jv in range(int(n_host) - 1)}
        return m, m
    o2n, _, _ = _leg_maps(built)
    inv = {n: o for o, n in o2n.items()}
    if cell_kind == "D":
        return inv, inv
    if cell_kind == "DV":
        return {n: fv(o) for n, o in inv.items()}, inv
    raise S2Error(f"cell_maps: unknown kind {cell_kind!r}")


def assert_fixed_at_host(cell, free, host_relaxed, cell_to_host):
    """Every fixed atom sits at its relaxed-host position bitwise (fail-closed before every relaxation)."""
    fixed = np.setdiff1d(np.arange(len(cell)), np.asarray(sorted(free), int))
    missing = [int(i) for i in fixed if int(i) not in cell_to_host]
    if missing:
        raise S2Error(f"fixed atoms without a host counterpart: {missing[:5]}")
    hidx = np.array([cell_to_host[int(i)] for i in fixed], int)
    if not (np.array_equal(cell.positions[fixed], host_relaxed.positions[hidx])
            and np.array_equal(cell.numbers[fixed], host_relaxed.numbers[hidx])):
        bad = int(np.abs(cell.positions[fixed] - host_relaxed.positions[hidx]).max(axis=1).argmax())
        raise S2Error(f"fixed atom {int(fixed[bad])} is not at its relaxed-host position (bitwise)")
    return int(fixed.size)


# ---------------------------------------------------------------- cell construction (plan sections 5, 7, 9)
def make_vacancy(host_relaxed, ctx, *, info=None):
    """V+_Rj start: the relaxed host minus I127 by pp.build_pair (reference vacancy point as scripts/29); asserts
    that the deleted atom is index VI, an I, within 1.2 A of the unrelaxed v (I-3) and that V is the host minus VI
    bitwise. Returns (V cell with pp.build_pair's MIG tag, migrating iodide in V numbering)."""
    vac, vpos_r, mig = pp.build_pair(host_relaxed, ref_point(), None, None)
    sym = _syms(host_relaxed)
    iod = np.flatnonzero(sym == "I")
    vi = int(iod[np.argmin(dist_to(host_relaxed, ref_point())[iod])])
    if vi != VI or sym[vi] != "I" or not np.array_equal(host_relaxed.positions[vi], vpos_r):
        raise S2Error(f"{ctx.member}: pp.build_pair deleted atom {vi}, the plan's I{VI}")
    if not (np.array_equal(np.delete(host_relaxed.positions, vi, axis=0), vac.positions)
            and np.array_equal(np.delete(host_relaxed.numbers, vi), vac.numbers)):
        raise S2Error(f"{ctx.member}: the V cell is not the relaxed host minus I{VI} (bitwise)")
    d = mic_norm(host_relaxed.positions[vi] - ctx.vpos, host_relaxed.cell.array)
    if not d < VAC_DELETE_MAX_A:
        raise S2Error(f"{ctx.member}: relaxed I{VI} lies {d:.3f} A from the unrelaxed v (>= {VAC_DELETE_MAX_A} A)")
    if info is not None:
        info.update({"deleted": vi, "d_to_unrelaxed_v_A": d, "mig_vac": int(mig), "mig_vac_unrelaxed": ctx.mig_vac,
                     "mig_agrees_with_unrelaxed": int(mig) == ctx.mig_vac})                       # N-A2
    return vac, int(mig)


def pbcl_value(path=PBCL_RECORD, *, allow_provisional):
    """The section 2 Pb-Cl rule from the Stage-0 record (scripts/52). Missing record -> S2Error (no shifted start
    is built); 'provisional_2.837' needs allow_provisional (else Refused). The record is checked fail-closed (N-A7)."""
    p = _repo(path)
    if not os.path.exists(p):
        raise S2Error(f"{path}: no Pb-Cl source record; shifted Cl starts are not built (section 2)")
    r = json.load(open(p))
    dec, used = r.get("decision"), r.get("value_used_A")
    level = (r.get("source") or {}).get("level")
    src = r.get("d_PbCl_from_source_A")
    if dec not in PBCL_DECISIONS or not r.get("date"):
        raise S2Error(f"{path}: decision {dec!r} or date missing")
    out = {"decision": dec, "record_sha256": sha256_file(p), "level": level, "allow_provisional": bool(allow_provisional)}
    if dec == "confirmed_2.837":
        if not (str(level).startswith("[S]") and src is not None and abs(float(src) - PBCL_DEFAULT_A) < 1e-12
                and abs(float(used) - PBCL_DEFAULT_A) < 1e-12):
            raise S2Error(f"{path}: 'confirmed_2.837' with level {level!r}, source {src}, used {used}")
        out.update({"d": PBCL_DEFAULT_A, "tag": level, "override": None})
    elif dec == "use_source_value":
        if not (str(level).startswith("[S]") and src is not None and abs(float(src) - PBCL_DEFAULT_A) >= 1e-12
                and 2.5 < float(src) < 3.3 and abs(float(used) - float(src)) < 1e-12):
            raise S2Error(f"{path}: 'use_source_value' with level {level!r}, source {src}, used {used}")
        out.update({"d": float(src), "tag": level, "override": {"Cl:d_PbCl": float(src)}})        # X-2
    else:
        if not (abs(float(used) - PBCL_DEFAULT_A) < 1e-12 and r.get("allow_provisional_required") is True):
            raise S2Error(f"{path}: 'provisional_2.837' with used {used}, allow_provisional_required "
                          f"{r.get('allow_provisional_required')}")
        if not allow_provisional:
            raise Refused("shifted Cl starts at the provisional 2.837 A need --allow-provisional (section 2)")
        out.update({"d": PBCL_DEFAULT_A, "tag": "[M] starting point", "override": None})
    return out


def apply_pbcl_override(built, base, d, vpos, *, name=None):
    """X-2: place the shifted Cl at Pb_t + d unit(X - Pb_t), the s2b-2 direction in this leg's own X frame, and
    re-validate V1-V10 (scripts/42 validate); refused unless valid and admissible. built is the s2b-2 shifted start
    or the centred Cl of the same site (then name = 'shift_a' | 'shift_b'), so that admissibility is judged at the
    source distance only, never at 2.837 A."""
    name = name or built.pose.get("name")
    if built.token != "Cl" or built.pose.get("mode") not in ("shift", "centred") or name not in ("shift_a", "shift_b"):
        raise S2Error("the Pb-Cl override applies to the shifted Cl starts only")
    fr = b42.x_frame(base, built.site)
    t, vt = (fr["pba"], fr["va"]) if name == "shift_a" else (fr["pbb"], fr["vb"])
    pos = base.positions[built.site] + vt - float(d) * vt / np.linalg.norm(vt)
    at = built.atoms.copy()
    at.positions[built.old_to_new[built.site]] = pos
    ov = {"Cl:d_PbCl": float(d)}
    pose = dict(built.pose, mode="shift", name=name, pb_t_input=int(t), pb_t_out=built.old_to_new.get(int(t)),
                d_PbCl_A=float(d), start_override=ov,
                start_sha=hashlib.sha256(canon({"GEOM_SHA": b42.GEOM_SHA, "override": ov}).encode()).hexdigest())
    b2 = dataclasses.replace(built, atoms=at, pose=pose, report={})
    rep = b42.validate(base, b2, vpos=vpos)
    if not rep["valid"]:
        raise BuildError(rep)
    if not rep["admissible"]:
        raise Inadmissible(rep, f"Cl {pose['name']} at d_PbCl {d}: {rep['V7'].get('reason')}")
    return dataclasses.replace(b2, report=rep)


def _pose_name(token, start):
    n = int(str(start).lstrip("p"))
    names = b42.sampled_names(token)
    if not 0 <= n < len(names):
        raise S2Error(f"{token}: start {start} outside the {len(names)} starts")
    return names[n]


def build_pair(host_rel, vac_rel, ctx, token, site, pose, *, partners, pbcl=None):
    """D_j and D_j+V by b42.build_paired (mig 'allow' at every X site, I-39; vpos = the member's unrelaxed v).
    A shifted Cl start needs the Pb-Cl rule (pbcl_value); with an X-2 override both legs are moved and re-checked.
    Inadmissible / Refused propagate (the caller rejects the pair, I-9)."""
    L = SUBLATTICE[token]
    name = pose if isinstance(pose, str) else pose["name"]
    shifted = token == "Cl" and str(name).startswith("shift")
    if shifted and pbcl is None:
        raise S2Error("a shifted Cl start needs the section 2 Pb-Cl record (pbcl_value)")
    if shifted and pbcl["override"]:                  # X-2: from the centred pair, each leg in its own X frame
        bh0, bv0 = b42.build_paired(host_rel, vac_rel, VI, token, int(site), "centred", vpos=ctx.vpos, mig="allow",
                                    partners=partners)
        bh = apply_pbcl_override(bh0, host_rel, pbcl["d"], ctx.vpos, name=name)
        try:
            bv = apply_pbcl_override(bv0, vac_rel, pbcl["d"], ctx.vpos, name=name)
        except Inadmissible as e:
            raise Inadmissible(dict(e.report, leg="V"), f"V leg: {e}; pair rejected")
        if partners == "unrelaxed" and not np.array_equal(bh.atoms.positions[bh.centre], bv.atoms.positions[bv.centre]):
            raise S2Error("override: the Cl differs between unrelaxed partners")
        return bh, bv
    return b42.build_paired(host_rel, vac_rel, VI, token, int(site), pose, vpos=ctx.vpos,
                            mig="allow" if L == "X" else "forbid", partners=partners)


def _leg_rec(b, work_id):
    rep = b.report
    return {"work_id": work_id, "centre": int(b.centre), "members": [int(m) for m in b.members],
            "deleted": [int(x) for x in b.deleted], "added": [int(x) for x in b.added],
            "modified": [int(x) for x in b.modified], "old_to_new": {str(k): int(v) for k, v in b.old_to_new.items()},
            "builder_report": {"valid": rep["valid"], "admissible": rep["admissible"],
                               "checks_passed": {f"V{k}": rep[f"V{k}"]["passed"] for k in range(1, 11)}}}


def pair_record(host_rel, vac_rel, ctx, token, site, start, *, partners, pbcl=None, parents=None):
    """(s2-pair-1 record, Built host leg | None, Built V leg | None). A rejected pair (Inadmissible or Refused,
    I-9) has status 'rejected' and no legs."""
    name = _pose_name(token, start)
    n = int(str(start).lstrip("p"))
    tv = to_vac_map()
    w = {lg: make_work_id(ctx.member, "D" if lg == "novac" else "DV", token=token, j=site, n=n) for lg in ("novac", "vac")}
    shifted = token == "Cl" and name.startswith("shift")
    rec = {"schema": RECORD_SCHEMAS["pair"], "member": ctx.member, "token": token, "site": int(site),
           "site_vac": tv(site), "sublattice": SUBLATTICE[token], "start": f"p{n}", "pose_name": name,
           "is_default_pose": n == 0, "partners": partners, "status": None, "rejection": None, "legs": None,
           "pose": None, "pose_vac_leg": None,
           "builder": {"BUILDER_VERSION": b42.BUILDER_VERSION, "GEOM_SHA": b42.GEOM_SHA,
                       "mig": "allow" if SUBLATTICE[token] == "X" else None, "replaced_migrating_iodide": False,
                       "provisional": bool(shifted and pbcl and pbcl["decision"] == "provisional_2.837"),
                       "allow_provisional": bool(pbcl and pbcl["allow_provisional"]),
                       "pbcl": None if not shifted else {"d_PbCl_A": pbcl["d"], "tag": pbcl["tag"],
                                                         "decision": pbcl["decision"], "override": pbcl["override"],
                                                         "record_sha256": pbcl["record_sha256"]}},
           "parents": parents or {}}
    try:
        bh, bv = build_pair(host_rel, vac_rel, ctx, token, site, name, partners=partners, pbcl=pbcl)
    except (Inadmissible, Refused) as e:
        leg = getattr(e, "report", {}).get("leg") if isinstance(e, Inadmissible) else None
        rec.update({"status": "rejected", "rejection": {"exception": type(e).__name__, "leg": leg, "reason": str(e)}})
        return rec, None, None
    rec.update({"status": "built", "pose": bh.pose, "pose_vac_leg": bv.pose,
                "legs": {"novac": _leg_rec(bh, w["novac"]), "vac": _leg_rec(bv, w["vac"])}})
    rec["builder"]["replaced_migrating_iodide"] = bool(bh.pose.get("replaced_migrating_iodide", False))
    return json.loads(json.dumps(rec, default=_np_scalar)), bh, bv


def _np_scalar(x):
    """JSON fallback for numpy scalars and arrays in builder records (values unchanged)."""
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, np.ndarray):
        return x.tolist()
    raise TypeError(f"not JSON serialisable: {type(x).__name__}")


def build_host_leg(host_rel, ctx, token, site):
    """G1 cell (section 7): the unrelaxed host-leg cell of the default pose on the S2-relaxed host, as the call
    build_paired makes for its host leg (Cl with mig 'allow' and the MIG iodide of make_vacancy in host numbering)."""
    if SUBLATTICE[token] == "X":
        _, mig_v = make_vacancy(host_rel, ctx)
        return b42.build(host_rel, token, int(site), "inherit", vpos=ctx.vpos, mig="allow",
                         mig_index=mig_v + (1 if mig_v >= VI else 0))
    return b42.build(host_rel, token, int(site), "inherit", vpos=ctx.vpos)


def pose_starts(host_rel, ctx, token, site, *, pbcl=None, mig_host=None, log=None):
    """The starts of section 9 on the host leg, each tagged p<n> (b42.sampled_names order): Sr, Ca, GA the default;
    Cs b42.resolve_poses (centred and every admissible +-0.30 A start); Cl centred and the two shifted starts, which
    need the Pb-Cl rule (pbcl_value; X-2 override re-checked here). Rejections are appended to log."""
    log = [] if log is None else log
    if token not in MULTI_START:
        return [{"start": "p0", "n": 0, "name": b42.sampled_names(token)[0], "default": True, "tag": None}]
    if token == "Cl" and pbcl is None:
        raise S2Error("shifted Cl starts need the section 2 Pb-Cl record (pbcl_value)")
    kw = {"vpos": ctx.vpos}
    if token == "Cl":
        kw.update(mig="allow", mig_index=ctx.mig_host if mig_host is None else int(mig_host))
    names = b42.sampled_names(token)
    if token == "Cl" and pbcl["override"]:            # X-2: admissibility of the shifted starts at the source value
        kept = []
        for nm in names:
            try:
                b = b42.build(host_rel, "Cl", int(site), "centred", **kw)
                if nm != "centred":
                    apply_pbcl_override(b, host_rel, pbcl["d"], ctx.vpos, name=nm)
                kept.append({"name": nm})
            except Inadmissible as e:
                log.append({"pose": nm, "status": "inadmissible", "reason": str(e)})
    else:
        kept = b42.resolve_poses(host_rel, token, int(site), label=f"{ctx.member}_{token}{int(site)}", log=log, **kw)
    out = []
    for p in kept:
        n = names.index(p["name"])
        st = {"start": f"p{n}", "n": n, "name": p["name"], "default": n == 0, "tag": None}
        if token == "Cl" and n:
            st.update({"tag": pbcl["tag"], "d_PbCl_A": pbcl["d"], "override": pbcl["override"]})
        out.append(st)
    return out


# ---------------------------------------------------------------- relaxations (plan section 5)
class MockHarmonic(Calculator):
    """Self-test and mock-campaign calculator: E = k/2 sum |mic(r - r0)|^2, F = -k mic(r - r0). Used only on
    synthetic and reference cells (N-1)."""
    implemented_properties = ["energy", "free_energy", "forces"]

    def __init__(self, r0, k=MOCK_K):
        super().__init__()
        self.r0, self.k = np.array(r0, float), float(k)

    def calculate(self, atoms=None, properties=("energy",), system_changes=all_changes):
        super().calculate(atoms, properties, system_changes)
        dv = find_mic(self.atoms.positions - self.r0, self.atoms.cell.array, pbc=True)[0]
        e = 0.5 * self.k * float((dv ** 2).sum())
        self.results = {"energy": e, "free_energy": e, "forces": -self.k * dv}


def mock_calc(atoms, key, free=None, sigma=MOCK_SIGMA_A):
    """A MockHarmonic whose minimum is the start shifted by a seeded offset on the free atoms (zlib.crc32(key))."""
    rng = np.random.default_rng(zlib.crc32(key.encode()))
    idx = np.arange(len(atoms)) if free is None else np.asarray(sorted(free), int)
    r0 = atoms.positions.copy()
    r0[idx] += rng.normal(0.0, sigma, (len(idx), 3))
    return MockHarmonic(r0)


def relax_host(atoms, calc, work_id, *, pool_member=None, log=None):
    """Whole-cell, fixed-cell host relaxation by scripts/29 relax_staged (FIRE defaults, stages 0.02/0.01/0.005,
    10 000 steps per stage). Valid iff the 0.005 stage converged (relax_staged's flag), max|F| < 0.005 strictly
    (I-4) and check 4 against the pool member passes (I-6, X-6). Returns (relaxed Atoms, tags 0; record parts)."""
    start = Atoms(numbers=atoms.numbers.copy(), positions=atoms.positions.copy(), cell=atoms.cell.array.copy(),
                  pbc=atoms.pbc.copy())
    t0 = time.time()
    at, rec, _ = s29.relax_staged(start, calc, work_id, lambda s: None, list(HOST_STAGES), HOST_STEPS)   # N-A1
    F = at.get_forces()
    fmax = float(np.linalg.norm(F, axis=1).max())
    stages = [{"fmax_target": s["fmax_target"], "steps": s["steps"], "converged": s["converged"], "fmax": s["fmax"],
               "E_mace_eV": s["E_eV"]} for s in rec["stages"]]
    out = Atoms(numbers=at.numbers.copy(), positions=at.positions.copy(), cell=at.cell.array.copy(), pbc=at.pbc.copy())
    out.set_tags([0] * len(out))
    relax = {"optimizer": "ASE FIRE, default parameters, restarted per stage (scripts/29 relax_staged)",
             "fmax_eVA": HOST_STAGES[-1], "fmax_stages_eVA": list(HOST_STAGES), "steps_cap": HOST_STEPS,
             "steps_cap_is": "per stage", "steps": int(sum(s["steps"] for s in stages)),
             "stage_flag": bool(rec["converged"]), "fmax_final_free_eVA": fmax, "held_max_dr_A": 0.0,
             "wall_s": round(time.time() - t0, 1), "stages": stages, "E_mace_eV": float(rec["E_eV"])}
    c1 = check_host_converged(relax)
    relax["converged"] = c1["passed"]
    c4 = check_topology(pool_member if pool_member is not None else start, out)
    val = {"checks": {"1": c1, "2": None, "3": None, "4": c4, "5": None}, "valid": bool(c1["passed"] and c4["passed"]),
           "failed": [int(k) for k, c in (("1", c1), ("4", c4)) if not c["passed"]]}
    if log:
        log(f"{work_id}: host relaxation {c1['steps']} steps, max|F| {fmax:.4f} eV/A, valid {val['valid']}")
    return out, {"relax": relax, "validity": val}


def relax_frozen(atoms, calc, free, *, fmax=FMAX, steps=STEPS, logfile=None):
    """One ASE FIRE run with default parameters to fmax over the free atoms (FixAtoms on every other atom), at most
    `steps` steps (section 5). converged is ASE's strict test (last-step convergence counts); asserts that it agrees
    with max|F_free| < fmax, that a non-converged run stopped at the cap, and that no fixed atom moved (bitwise).
    Returns (relaxed Atoms frozen in a SinglePointCalculator, record)."""
    from ase.calculators.singlepoint import SinglePointCalculator
    from ase.constraints import FixAtoms
    from ase.optimize import FIRE
    n = len(atoms)
    free = np.array(sorted({int(i) for i in free}), int)
    if not free.size or free.min() < 0 or free.max() >= n:
        raise S2Error("relax_frozen: empty or out-of-range free set")
    fixed = np.setdiff1d(np.arange(n), free)
    start = atoms.copy()
    at = Atoms(numbers=atoms.numbers.copy(), positions=atoms.positions.copy(), cell=atoms.cell.array.copy(),
               pbc=atoms.pbc.copy())
    at.set_tags(np.asarray(atoms.get_tags(), int))
    if fixed.size:
        at.set_constraint(FixAtoms(indices=fixed))
    at.calc = calc
    trace = []
    t0 = time.time()
    with FIRE(at, logfile=None) as opt:              # ASE defaults; energies never logged (N-A4)
        opt.attach(lambda: trace.append(float(np.linalg.norm(at.get_forces(), axis=1).max())), interval=1)
        converged = bool(opt.run(fmax=fmax, steps=steps))
        nsteps = int(opt.get_number_of_steps())
    E1 = float(at.get_potential_energy())
    F1 = at.get_forces(apply_constraint=False).copy()
    ff = float(np.linalg.norm(F1[free], axis=1).max())
    assert abs(ff - float(np.linalg.norm(at.get_forces(), axis=1).max())) < 1e-12, "FIRE criterion != free atoms"
    assert converged == (ff < fmax) and (converged or nsteps == steps), (converged, ff, nsteps)
    if fixed.size and not np.array_equal(at.positions[fixed], start.positions[fixed]):
        raise S2Error("relax_frozen: a fixed atom moved")
    dr = find_mic(at.positions - start.positions, at.cell.array, pbc=True)[1]
    if logfile:
        _write_text_atomic("".join(f"{k} {x:.6f}\n" for k, x in enumerate(trace)), logfile)
    snap = at.copy(); snap.set_constraint()
    snap.calc = SinglePointCalculator(snap, energy=E1, forces=F1)
    rec = {"optimizer": "ASE FIRE, default parameters", "fmax_eVA": fmax, "steps_cap": steps, "steps": nsteps,
           "converged": converged, "fmax_final_free_eVA": ff, "held_max_dr_A": 0.0, "n_free": int(free.size),
           "n_fixed": int(fixed.size), "max_dr_free_A": float(dr[free].max()), "wall_s": round(time.time() - t0, 1),
           "E_mace_eV": E1}
    return snap, rec


# ---------------------------------------------------------------- validity checks 1-5 (plan section 5; 11 for A2)
def check_converged(relax_rec):
    """Check 1: FIRE stopped with max|F| < fmax over the free atoms (strict; last-step convergence passes)."""
    st = int(relax_rec["steps"])
    f = float(relax_rec["fmax_final_free_eVA"])
    ok = bool(relax_rec["converged"]) and f < float(relax_rec["fmax_eVA"]) and st <= int(relax_rec["steps_cap"])
    return {"passed": ok, "steps": st, "fmax_final_free_eVA": f, "strict": True}


def check_host_converged(relax_rec):
    """Check 1 of the host (I-4): relax_staged's flag for the 0.005 stage AND the strict max|F| < 0.005 over all
    atoms, the stage within its 10 000-step cap."""
    last = relax_rec["stages"][-1]
    f = float(relax_rec["fmax_final_free_eVA"])
    ok = (abs(float(last["fmax_target"]) - HOST_STAGES[-1]) < 1e-12 and bool(last["converged"])
          and bool(relax_rec["stage_flag"]) and f < HOST_STAGES[-1] and int(last["steps"]) <= HOST_STEPS)
    return {"passed": bool(ok), "steps": int(relax_rec["steps"]), "fmax_final_free_eVA": f, "strict": True,
            "stage_flag": bool(relax_rec["stage_flag"]), "stages_converged": [s["converged"] for s in relax_rec["stages"]]}


def check_refill(cell, v_relaxed):
    """Check 2 (vacancy cells): no X-site atom (I or Cl) within 1.2 A of v (relaxed-host I127); fail at d <= 1.2."""
    s = _syms(cell)
    X = np.flatnonzero(np.isin(s, ("I", "Cl")))
    d = dist_to(cell, v_relaxed)[X]
    k = int(np.argmin(d))
    return {"passed": bool(d[k] > REFILL_MIN_A), "min_X_to_v_A": float(d[k]), "species": str(s[X[k]]),
            "index": int(X[k])}


def check_dopant_on_site(start, final, centre):
    """Check 3: the dopant centre atom lies less than 1.0 A from its builder position (I-A2)."""
    if centre is None:
        raise S2Error("check 3 needs the dopant centre index of the built leg")
    disp = mic_norm(final.positions[int(centre)] - start.positions[int(centre)], start.cell.array)
    return {"passed": bool(disp < DOPANT_MAX_A), "centre": int(centre), "displacement_A": disp}


def _org_bonds(at, org):
    s = _syms(at)
    D = b42.pairwise(at, org, org)
    cut = np.zeros_like(D)
    for a in range(len(org)):
        for b in range(a + 1, len(org)):
            cut[a, b] = ORG_BOND_CUT.get(tuple(sorted((s[org[a]], s[org[b]]))), 0.0)
    ia, ib = np.nonzero(np.triu(D < cut, 1))
    return {(int(org[a]), int(org[b])) for a, b in zip(ia, ib)}


def check_topology(start, final):
    """Check 4 (graph topology): organic bond set (C-N < 1.6, C-C < 1.7, N-H and C-H < 1.25 A) equal to the start's;
    no H within 1.25 A and no C or N within 1.6 A of an inorganic atom (fail at d <= value, I-A1); no pair below
    0.65 A; composition (numbers, in order) unchanged."""
    if len(start) != len(final) or not np.array_equal(start.numbers, final.numbers):
        return {"passed": False, "composition_equal": False, "bonds_start": None, "bonds_final": None,
                "bonds_added": [], "bonds_lost": [], "h_inorganic_min_A": None, "cn_inorganic_min_A": None,
                "min_pair_A": None}
    s = _syms(final)
    if not set(s) <= set(ORGANIC) | set(INORGANIC):
        raise S2Error(f"check 4: elements {sorted(set(s) - set(ORGANIC) - set(INORGANIC))} are outside the plan")  # N-A11
    org = np.flatnonzero(np.isin(s, ORGANIC))
    ino = np.flatnonzero(np.isin(s, INORGANIC))
    E0, E1 = _org_bonds(start, org), _org_bonds(final, org)
    emin = {e: (float(b42.pairwise(final, org[s[org] == e], ino).min()) if (s[org] == e).any() and len(ino) else None)
            for e in ORG_INORG_MIN}
    hmin = emin["H"]
    cnmin = min((emin[e] for e in ("C", "N") if emin[e] is not None), default=None)
    allp = b42.pairwise(final, np.arange(len(final)), np.arange(len(final)))
    np.fill_diagonal(allp, np.inf)
    pmin = float(allp.min())
    ok = (E0 == E1 and all(v is None or v > ORG_INORG_MIN[e] for e, v in emin.items()) and pmin >= FLOOR_A)
    return {"passed": bool(ok), "composition_equal": True, "bonds_start": len(E0), "bonds_final": len(E1),
            "bonds_added": sorted(map(list, E1 - E0)), "bonds_lost": sorted(map(list, E0 - E1)),
            "h_inorganic_min_A": hmin, "cn_inorganic_min_A": cnmin, "min_pair_A": pmin}


def _rel_skeleton(P, idx, cell):
    return find_mic(P[idx] - P[idx[0]], cell, pbc=True)[0]


def check_partner(child, parent, child_to_parent, *, host_relaxed, child_to_host, centre_host, free_child):
    """Check 5: every free child atom more than 6.0 A from the defect of this step (its relaxed-host position, an
    organic atom by its molecule's carbon, I-5) stays near its parent position: inorganic |dr| < 0.25 A; FA carbon
    |dr| < 0.25 A and Kabsch rotation of C-N-N < 20 deg (scripts/38). Within 6.0 A the same measures are reported."""
    cell = child.cell.array
    cs, ps = _syms(child), _syms(parent)
    free = set(int(i) for i in free_child)
    p2c = {int(p): int(c) for c, p in child_to_parent.items()}
    dh = dist_to(host_relaxed, centre_host)
    acc = {"gated": {"inorganic": [], "fa": []}, "within_6A_reported": {"inorganic": [], "fa": []}}
    for i in sorted(free):
        if i not in child_to_parent or cs[i] in ORGANIC:
            continue                                   # appended dopant atoms have no parent; organics by molecule
        d_h = float(dh[child_to_host[i]])
        dr = mic_norm(child.positions[i] - parent.positions[child_to_parent[i]], cell)
        acc["gated" if d_h > PARTNER_CUT_A else "within_6A_reported"]["inorganic"].append(
            {"index": i, "d_host_A": d_h, "dr_A": dr})
    for cp in np.flatnonzero(ps == "C"):
        mol, ns = a38.molecule(parent, int(cp), ps, cell)
        if len(ns) != 2:
            continue                                   # FA only (I-5)
        sk = [int(cp)] + [int(x) for x in ns]
        if any(x not in p2c for x in sk) or p2c[int(cp)] not in free:
            continue                                   # deleted (Cs on this FA) or fixed whole
        cc = [p2c[x] for x in sk]
        d_h = float(dh[child_to_host[cc[0]]])
        dr = mic_norm(child.positions[cc[0]] - parent.positions[sk[0]], cell)
        rot = a38.kabsch_deg(_rel_skeleton(parent.positions, sk, cell), _rel_skeleton(child.positions, cc, cell))
        acc["gated" if d_h > PARTNER_CUT_A else "within_6A_reported"]["fa"].append(
            {"carbon": cc[0], "d_host_A": d_h, "dr_carbon_A": dr, "rot_deg": rot})

    def summary(g):
        mi = max(g["inorganic"], key=lambda r: r["dr_A"], default=None)
        mc = max(g["fa"], key=lambda r: r["dr_carbon_A"], default=None)
        mr = max(g["fa"], key=lambda r: r["rot_deg"], default=None)
        return {"n_inorganic": len(g["inorganic"]), "n_fa": len(g["fa"]),
                "max_dr_inorganic_A": None if mi is None else mi["dr_A"],
                "max_dr_fa_carbon_A": None if mc is None else mc["dr_carbon_A"],
                "max_rot_fa_deg": None if mr is None else mr["rot_deg"],
                "worst": {"inorganic": mi, "fa_carbon": mc, "fa_rotation": mr}}
    g = summary(acc["gated"])
    ok = (all(r["dr_A"] < PARTNER_DR_A for r in acc["gated"]["inorganic"])
          and all(r["dr_carbon_A"] < PARTNER_DR_A and r["rot_deg"] < PARTNER_ROT_DEG for r in acc["gated"]["fa"]))
    return {"passed": bool(ok), "gated": g, "within_6A_reported": summary(acc["within_6A_reported"])}


def _centre_host(region, kind):
    return np.array(region["centres"]["v" if kind == "V" else "site"], float)


def validity(kind, *, relax_rec, start, final, region, host_relaxed, parent=None, built=None, pool_member=None,
             parent_work_id=None):
    """Checks 1-5 of section 5 for one A1 cell (spec 6.6 table): host 1 (+4 vs the pool member); V+ 1, 2, 4, 5 vs
    the relaxed host (centre v); D 1, 3, 4, 5 vs the relaxed host (centre j); D+V 1, 2, 3, 4, 5 vs the relaxed V+_Rj
    (centre j). Returns {"checks", "valid", "failed"}."""
    if kind == "host":
        c = {"1": check_host_converged(relax_rec), "2": None, "3": None,
             "4": check_topology(pool_member if pool_member is not None else start, final), "5": None}
    else:
        free = free_in_cell(region, kind, built=built)
        c2h, c2p = cell_maps(kind, built=built, n_host=len(host_relaxed))
        par = host_relaxed if kind in ("V", "D") else parent
        if par is None:
            raise S2Error("validity of a D+V cell needs its relaxed V+_Rj parent")
        v = np.array(region["centres"]["v"], float)
        c = {"1": check_converged(relax_rec),
             "2": check_refill(final, v) if kind in ("V", "DV") else None,
             "3": check_dopant_on_site(start, final, _leg_maps(built)[2]) if kind in ("D", "DV") else None,
             "4": check_topology(start, final),
             "5": dict(check_partner(final, par, c2p, host_relaxed=host_relaxed, child_to_host=c2h,
                                     centre_host=_centre_host(region, kind), free_child=free),
                       parent=parent_work_id, centre="v" if kind == "V" else "site j")}
    failed = [int(k) for k, x in c.items() if x is not None and not x["passed"]]
    return {"checks": c, "valid": not failed, "failed": failed}


def validity_a2(kind, *, start, final, region, host_relaxed, parent_final=None, built=None):
    """Section 11: checks 2-5 on A2 final geometries (host_R: check 4 only), partner check between the final
    geometries of child and parent (D vs host_R, V+ vs host_R, D+V vs V+_R); start = the start of the cell's A1
    relaxation (I-A4)."""
    if kind == "host":
        c = {"2": None, "3": None, "4": check_topology(start, final), "5": None}
    else:
        if parent_final is None:
            raise S2Error("validity_a2 needs the parent's A2 final geometry")
        free = free_in_cell(region, kind, built=built)
        c2h, c2p = cell_maps(kind, built=built, n_host=len(host_relaxed))
        c = {"2": check_refill(final, np.array(region["centres"]["v"], float)) if kind in ("V", "DV") else None,
             "3": check_dopant_on_site(start, final, _leg_maps(built)[2]) if kind in ("D", "DV") else None,
             "4": check_topology(start, final),
             "5": check_partner(final, parent_final, c2p, host_relaxed=host_relaxed, child_to_host=c2h,
                                centre_host=_centre_host(region, kind), free_child=free)}
    failed = [int(k) for k, x in c.items() if x is not None and not x["passed"]]
    return {"checks": c, "valid": not failed, "failed": failed}


def atoms_with_positions(template, positions):
    """A copy of template (numbers, cell, tags) at other positions, e.g. an A2 final geometry parsed by 47."""
    x = Atoms(numbers=template.numbers.copy(), positions=np.asarray(positions, float), cell=template.cell.array.copy(),
              pbc=template.pbc.copy())
    x.set_tags(np.asarray(template.get_tags(), int))
    return x


# ---------------------------------------------------------------- distinct minima (plan section 9; geometry only)
def fa_skeletons(at, carbons):
    """[[C, Na, Nb]] of the FA molecules with these carbons (scripts/38 molecule; FA = 2 N)."""
    sym, cell = _syms(at), at.cell.array
    out = []
    for c in carbons:
        _, ns = a38.molecule(at, int(c), sym, cell)
        if len(ns) == 2:
            out.append([int(c)] + sorted(int(x) for x in ns))
    return out


def _min_difference(a, b, cell):
    da = max((mic_norm(a["atoms"].positions[i] - b["atoms"].positions[i], cell) for i in a["dopant_idx"]), default=0.0)
    fr, fd = 0.0, 0.0
    for sk in a["fa"]:
        fd = max(fd, mic_norm(a["atoms"].positions[sk[0]] - b["atoms"].positions[sk[0]], cell))
        fr = max(fr, a38.kabsch_deg(_rel_skeleton(b["atoms"].positions, sk, cell),
                                    _rel_skeleton(a["atoms"].positions, sk, cell)))
    distinct = da > DISTINCT_DR_A or fd > DISTINCT_DR_A or fr > DISTINCT_ROT_DEG
    return {"max_dopant_dr_A": da, "max_fa_carbon_dr_A": fd, "max_fa_rot_deg": fr, "distinct": bool(distinct)}


def distinct_minima(cells):
    """Section 9, one leg: the valid relaxed starts in start order (p0 first); a minimum is kept iff, against EVERY
    minimum kept before it, some dopant atom differs by > 0.25 A or some free FA by > 0.25 A (carbon) or > 20 deg
    (Kabsch C-N-N). Returns {"kept", "map" o<k> -> p<n>, "pairs", "excluded"}: o0 only if p0 is valid (I-8)."""
    if not cells:
        return {"kept": [], "map": {}, "pairs": [], "excluded": []}
    cells = [c if "fa" in c else dict(c, fa=fa_skeletons(c["atoms"], c["free_fa_carbons"])) for c in cells]
    order = [int(str(c["start"]).lstrip("p")) for c in cells]
    if order != sorted(order) or len(set(order)) != len(order):
        raise S2Error(f"distinct_minima: starts not in start order: {[c['start'] for c in cells]}")
    ref = cells[0]
    for c in cells[1:]:
        if not (np.array_equal(c["atoms"].numbers, ref["atoms"].numbers) and list(c["dopant_idx"]) == list(ref["dopant_idx"])
                and [list(x) for x in c["fa"]] == [list(x) for x in ref["fa"]]):
            raise S2Error(f"distinct_minima: {c['start']} is not comparable with {ref['start']} (atoms, dopant, FA)")
    cell = ref["atoms"].cell.array
    kept, pairs, excl = [], [], [c["start"] for c in cells if not c.get("valid", True)]
    for c in cells:
        if not c.get("valid", True):
            continue
        ok = True
        for k in kept:
            m = _min_difference(c, k, cell)
            pairs.append(dict(m, a=c["start"], b=k["start"]))
            ok = ok and m["distinct"]
        if ok:
            kept.append(c)
    mp, k = {}, 1
    for c in kept:
        if c["start"] == "p0":
            mp["o0"] = "p0"
        else:
            mp[f"o{k}"] = c["start"]; k += 1
    return {"kept": [c["start"] for c in kept], "map": mp, "pairs": pairs, "excluded": excl}


# ---------------------------------------------------------------- layout (spec 5)
class Layout:
    """Paths of the node work tree (kind 'node', root /data) or of the repository archive (kind 'archive', root
    results/objective2/s2). Paths only; nothing is created."""

    def __init__(self, kind="node", root=NODE_ROOT):
        if kind not in ("node", "archive"):
            raise S2Error(f"layout kind {kind!r}")
        self.kind, self.root = kind, str(root)
        self.work = os.path.join(self.root, "work", "s2") if kind == "node" else self.root

    def _c(self, c):
        if c not in ("c1", "c2", "c3", "c4"):
            raise S2Error(f"campaign {c!r}")
        return os.path.join(self.work, c)

    def campaign_dir(self, c):
        return self._c(c)

    def cell_dir(self, c, work_id):
        if self.kind == "archive":
            raise S2Error("archived structures are in <campaign>/structures.tar.gz")
        return os.path.join(self._c(c), "cells", work_id)

    def cell_file(self, c, work_id, which):
        return os.path.join(self.cell_dir(c, work_id), {"start": "start.extxyz", "relaxed": "relaxed.extxyz",
                                                          "job": "job.json", "attempts": "attempts.json",
                                                          "fire": "fire.log", "vac_start": "vac_start.json",
                                                          "validity": "validity.json"}[which])

    def record(self, c, work_id):
        if self.kind == "archive":
            return os.path.join(self._c(c), "records", f"{work_id}.json")
        return os.path.join(self.cell_dir(c, work_id), "record.json")

    def region(self, c, member, L, j):
        return os.path.join(self._c(c), "regions", f"{member}_{L}{int(j)}.json")

    def pair(self, c, h, T, j, n):
        return os.path.join(self._c(c), "pairs", f"{h}_{T}{int(j)}p{int(n)}.json")

    def distinct(self, c, h, T, j, leg):
        return os.path.join(self._c(c), "pairs", f"{h}_{T}{int(j)}_{leg}.distinct.json")

    def qe_stage(self, c, label):
        return os.path.join(self._c(c), "qe_stage", label)

    def sp_dir(self, c, label):
        if self.kind == "archive":
            return os.path.join(self._c(c), "raw")
        return os.path.join(self.root, "jobs", f"s2{c}", label)

    def sp_out(self, c, label):
        return os.path.join(self.sp_dir(c, label), f"{label}.out" + (".gz" if self.kind == "archive" else ""))

    def sp_meta(self, c, label):
        return os.path.join(self.sp_dir(c, label), f"{label}.meta.json")

    def a2_dir(self, c, label):
        return os.path.join(self._c(c), "raw") if self.kind == "archive" else os.path.join(self._c(c), "a2", label)

    def a2_parts(self, c, label):
        """Existing part outputs <label>.p<n>.out(.gz) in part order."""
        d = self.a2_dir(c, label)
        rx = re.compile(re.escape(label) + r"\.p([1-9]\d*)\.out" + (r"\.gz" if self.kind == "archive" else ""))
        got = sorted(((int(m.group(1)), f) for f in (os.listdir(d) if os.path.isdir(d) else [])
                      for m in [rx.fullmatch(f)] if m))
        return [os.path.join(d, f) for _, f in got]

    def gate(self, c, name):
        return os.path.join(self._c(c), "gates", f"{name}.json")

    def state(self, c=None):
        return os.path.join(self.work, "state.json") if self.kind == "node" else \
            os.path.join(self._c(c), "state_end.json")

    def ledger_dir(self, c=None):
        return os.path.join(self.work, "ledger") if self.kind == "node" else os.path.join(self._c(c), "ledger.json")

    def spot_dir(self):
        if self.kind == "archive":
            raise S2Error("no spot directory in the archive")
        return os.path.join(self.work, "spot")


# ---------------------------------------------------------------- records (spec 4.3)
CELL_KEYS = ("work_id", "labels", "campaign", "member", "role", "cell_kind", "leg", "site", "site_cell",
             "sublattice", "site_roles", "token", "start", "pose_id", "is_default_pose", "k_min", "region_id", "free",
             "n_free", "n_fixed", "parent", "pair", "builder", "model", "relax", "validity", "files", "sha256",
             "geometry_sha256", "attempts", "code")


def cell_record(**fields):
    """The s2-cell-1 record (spec 4.3); every key of CELL_KEYS required, nothing else accepted."""
    missing = [k for k in CELL_KEYS if k not in fields]
    extra = [k for k in fields if k not in CELL_KEYS]
    if missing or extra:
        raise S2Error(f"cell record: missing {missing}, unknown {extra}")
    rec = {"schema": RECORD_SCHEMAS["cell"], **{k: fields[k] for k in CELL_KEYS}, "written": now()}
    return json.loads(json.dumps(rec))


def role_of(member):
    return "reference" if member == "ref233" else "synthetic" if member == "synthetic" else \
        "pilot" if member in PILOTS else "production"


# ---------------------------------------------------------------- MACE loader (plan section 5; never in a self-test)
def foundation_path():
    """The file mace_mp(model='medium') resolves in mace 0.3.16: XDG_CACHE_HOME (or ~/.cache) + /mace/ + the
    foundation file name (computed by hand; nothing is imported)."""
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return os.path.join(base, "mace", FOUNDATION_FILE)


def foundation_check(path=None):
    """s2-mace-1 part: basename, bytes, sha256 against FOUNDATION_SHA256 (no import of mace; no path recorded)."""
    p = path or foundation_path()
    ok = os.path.isfile(p)
    sha = sha256_file(p) if ok else None
    return {"schema": RECORD_SCHEMAS["mace"], "file": os.path.basename(p), "bytes": os.path.getsize(p) if ok else None,
            "sha256": sha, "expected_sha256": FOUNDATION_SHA256, "passed": bool(ok and sha == FOUNDATION_SHA256)}


def load_mace(threads=THREADS):
    """Zero-shot MACE-MP-0 medium: the foundation file must have the section 5 sha256 before anything is imported;
    OMP/MKL threads, torch threads; mace_mp(model='medium', device='cpu', default_dtype='float64'); asserts mace
    0.3.16, float64 parameters on cpu, the resolved file = foundation_path() (so it never downloads), and the S2
    atomic numbers covered. Returns (calculator, info)."""
    chk = foundation_check()
    if not chk["passed"]:
        raise S2Error(f"foundation file {chk['file']}: sha256 {chk['sha256']} != {FOUNDATION_SHA256}")
    for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[k] = str(int(threads))
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    import torch
    torch.set_num_threads(int(threads))
    import e3nn, mace
    from mace.calculators import mace_mp
    from mace.calculators.foundations_models import mace_mp_urls
    from mace.tools.utils import get_cache_dir
    if mace.__version__ != MACE_VERSION:
        raise S2Error(f"mace {mace.__version__}, the plan's {MACE_VERSION}")
    name = "".join(c for c in os.path.basename(mace_mp_urls["medium"]) if c.isalnum() or c in "_")
    resolved = os.path.join(str(get_cache_dir()), name)
    if os.path.realpath(resolved) != os.path.realpath(foundation_path()):
        raise S2Error("mace_mp('medium') resolves another file than the checked foundation file")
    calc = mace_mp(model="medium", device="cpu", default_dtype="float64")
    params = [p for m in calc.models for p in m.parameters()]
    if not all(p.dtype == torch.float64 for p in params) or any(str(p.device) != "cpu" for p in params):
        raise S2Error("MACE parameters are not float64 on cpu")
    zs = {int(z) for z in calc.models[0].atomic_numbers.tolist()}
    if not MACE_Z_REQUIRED <= zs:
        raise S2Error(f"MACE does not cover Z {sorted(MACE_Z_REQUIRED - zs)}")
    if torch.get_num_threads() != int(threads):
        raise S2Error(f"torch threads {torch.get_num_threads()} != {threads}")
    info = {"sha256": chk["sha256"], "file": chk["file"], "dtype": "float64", "device": "cpu", "threads": int(threads),
            "atomic_numbers_covered": sorted(zs), "z_required_ok": True,
            "versions": versions({"mace": mace.__version__, "torch": torch.__version__, "e3nn": e3nn.__version__})}
    return calc, info


# ---------------------------------------------------------------- jobs (spec 6.10; run by scripts/50 on the node)
def load_job(path):
    job = json.load(open(path))
    for k in ("action", "campaign", "root", "member"):
        if k not in job:
            raise S2Error(f"job {os.path.basename(path)}: no {k!r}")
    return job


def _guard(job):
    """Before anything is read or written: the mock harmonic calculator only on reference/synthetic members (N-1);
    MACE only under the node root /data and never on them (N-2)."""
    calc = job.get("calc")
    if calc == "mock-harmonic":
        if job["member"] not in REF_MEMBERS:
            raise S2Error(f"{job['member']}: a mock calculator never touches a pool member (N-1)")
    elif calc == "mace":
        if os.path.normpath(str(job["root"])) != NODE_ROOT:
            raise S2Error(f"MACE runs only under the node root {NODE_ROOT} (N-2)")
        if job["member"] in REF_MEMBERS:
            raise S2Error("no MACE job on a reference or synthetic member")
    else:
        raise S2Error(f"job calc {calc!r}: 'mace' or 'mock-harmonic'")


def _calc_for(job, cell, key, free=None):
    _guard(job)
    if job["calc"] == "mock-harmonic":
        return mock_calc(cell, key, free), {"mock": "harmonic", "k_eVA2": MOCK_K, "sigma_A": MOCK_SIGMA_A,
                                            "seed": "zlib.crc32(work_id)"}
    return load_mace(int(job.get("threads", THREADS)))


def _attempts(L, c, wid):
    p = L.cell_file(c, wid, "attempts")
    return json.load(open(p)) if os.path.exists(p) else []


def _host_files(L, c, member):
    wid = make_work_id(member, "host")
    p = L.cell_file(c, wid, "relaxed")
    if not os.path.exists(L.record(c, wid)) or not os.path.exists(p):
        raise S2Error(f"{wid}: no host record or relaxed structure yet")
    return wid, read_cell(p), load_record(L.record(c, wid))


def _pool_start(member):
    return read(os.path.join(ROOT, REF_HOST)) if member == "ref233" else read(pool_path(member))


def job_relax_host(job, calc=None):
    L, c, m = Layout("node", job["root"]), job["campaign"], job["member"]
    if calc is None:
        _guard(job)
    wid = make_work_id(m, "host")
    if job.get("work_id", wid) != wid:
        raise S2Error(f"relax-host: work id {job.get('work_id')} != {wid}")
    pool = _pool_start(m)
    start = write_cell(L.cell_file(c, wid, "start"), pool)
    model = None
    if calc is None:
        calc, model = _calc_for(job, start, wid)
    out, parts = relax_host(start, calc, wid, pool_member=pool)
    rel = write_cell(L.cell_file(c, wid, "relaxed"), out)
    rec = cell_record(work_id=wid, labels=[make_label("s2", m, "host")] if m not in REF_MEMBERS else [],
                      campaign=c, member=m, role=role_of(m), cell_kind="host", leg=None, site=None, site_cell=None,
                      sublattice=None, site_roles=[], token=None, start=None, pose_id=None, is_default_pose=None,
                      k_min=None, region_id=None, free=list(range(len(start))), n_free=len(start), n_fixed=0,
                      parent={"work_id": None, "map": None, "pool_member_sha256": sha256_atoms(pool)}, pair=None,
                      builder={"BUILDER_VERSION": b42.BUILDER_VERSION, "GEOM_SHA": b42.GEOM_SHA, "partners": None},
                      model=model or {"mock": "supplied"}, relax=parts["relax"], validity=parts["validity"],
                      files={"start": os.path.relpath(L.cell_file(c, wid, "start"), L.campaign_dir(c)),
                             "relaxed": os.path.relpath(L.cell_file(c, wid, "relaxed"), L.campaign_dir(c))},
                      sha256={"start": sha256_file(L.cell_file(c, wid, "start")),
                              "relaxed": sha256_file(L.cell_file(c, wid, "relaxed"))},
                      geometry_sha256={"start": sha256_atoms(start), "relaxed": sha256_atoms(rel)},
                      attempts=_attempts(L, c, wid), code=code_state())
    dump_public(rec, L.record(c, wid))
    return rec


def job_region(job):
    L, c, m = Layout("node", job["root"]), job["campaign"], job["member"]
    hwid, host, hrec = _host_files(L, c, m)
    ctx = host_context(m)
    sets = site_sets(ctx)
    j = int(job["site"])
    Ls = sublattice_of(host, j)
    if j not in label_sites(m, sets)[Ls] and m not in REF_MEMBERS:
        raise S2Error(f"{m}: {Ls}{j} is not a section 4 site")
    roles = site_roles(m, Ls, j, sets, c1_sites(m, m05_cal=job.get("m05_cal"), sets=sets) if m in PILOTS else None)
    reg = build_region(host, m, j, roles=roles, host_work_id=hwid)
    reg["host_source"]["valid"] = bool(hrec["validity"]["valid"])
    dump_public(reg, L.region(c, m, Ls, j))
    return reg


def _region_of(L, c, m, j, host):
    Ls = sublattice_of(host, j)
    p = L.region(c, m, Ls, j)
    if not os.path.exists(p):
        raise S2Error(f"no region record {os.path.basename(p)}")
    reg = check_region_record(load_record(p))
    if reg["host_source"]["sha256"] != sha256_atoms(host):
        raise S2Error(f"region {m} {Ls}{j}: built on another relaxed host")
    return reg


def job_build_vac(job):
    L, c, m, j = Layout("node", job["root"]), job["campaign"], job["member"], int(job["site"])
    hwid, host, _ = _host_files(L, c, m)
    reg = _region_of(L, c, m, j, host)
    ctx = host_context(m)
    wid = make_work_id(m, "V", L=reg["sublattice"], j=j)
    info = {}
    vac, mig = make_vacancy(host, ctx, info=info)
    st = write_cell(L.cell_file(c, wid, "start"), vac)
    rec = {"schema": RECORD_SCHEMAS["vac_start"], "work_id": wid, "member": m, "site": j, "region_id": reg["region_id"],
           "parent": hwid, **info, "start_sha256": sha256_file(L.cell_file(c, wid, "start")),
           "start_geometry_sha256": sha256_atoms(st), "written": now()}
    dump_public(rec, L.cell_file(c, wid, "vac_start"))
    return rec


def job_build_pair(job):
    L, c, m, j, T = Layout("node", job["root"]), job["campaign"], job["member"], int(job["site"]), job["token"]
    start = job.get("start", "p0")
    n = int(str(start).lstrip("p"))
    hwid, host, _ = _host_files(L, c, m)
    reg = _region_of(L, c, m, j, host)
    if reg["sublattice"] != SUBLATTICE[T]:
        raise S2Error(f"{T} at {reg['sublattice']}{j}")
    vwid = make_work_id(m, "V", L=reg["sublattice"], j=j)
    vp = L.cell_file(c, vwid, "relaxed")
    if not os.path.exists(L.record(c, vwid)) or not os.path.exists(vp):
        raise S2Error(f"{vwid}: no relaxed V+_Rj yet")
    vac = read_cell(vp)
    ctx = host_context(m)
    name = _pose_name(T, start)
    pbcl = None
    if T == "Cl" and name.startswith("shift"):
        pbcl = pbcl_value(job.get("pbcl_record", PBCL_RECORD), allow_provisional=bool(job.get("allow_provisional")))
    rec, bh, bv = pair_record(host, vac, ctx, T, j, start, partners=job.get("partners", "relaxed"), pbcl=pbcl,
                              parents={"novac": hwid, "vac": vwid})
    rec["region_id"] = reg["region_id"]
    if rec["status"] == "built":
        for lg, b in (("novac", bh), ("vac", bv)):
            wid = rec["legs"][lg]["work_id"]
            st = write_cell(L.cell_file(c, wid, "start"), b.atoms)
            rec["legs"][lg]["start_sha256"] = sha256_file(L.cell_file(c, wid, "start"))
            rec["legs"][lg]["start_geometry_sha256"] = sha256_atoms(st)
    dump_public(rec, L.pair(c, m, T, j, n))
    return rec


def job_relax(job, calc=None):
    L, c, m = Layout("node", job["root"]), job["campaign"], job["member"]
    if calc is None:
        _guard(job)
    wid = job["work_id"]
    p = parse_work_id(wid)
    if p["host"] != m:
        raise S2Error(f"{wid} is not a cell of {m}")
    if p["kind"] == "host":
        return job_relax_host(job, calc)
    hwid, host, _ = _host_files(L, c, m)
    reg = _region_of(L, c, m, p["j"], host)
    start = read_cell(L.cell_file(c, wid, "start"))
    built, pair_path, parent, pwid, leg = None, None, host, hwid, None
    if p["kind"] == "V":
        vs = load_record(L.cell_file(c, wid, "vac_start"))
        if vs["start_sha256"] != sha256_file(L.cell_file(c, wid, "start")) or vs["region_id"] != reg["region_id"]:
            raise S2Error(f"{wid}: start file or region differ from the V+ build record")
        site_cell = to_vac_map()(p["j"])
        token, pose_id, k_min = None, None, None
        labels = [] if m in REF_MEMBERS else [make_label("s2", m, "V", L=p["L"], j=p["j"])]
    else:
        leg = p["leg"]
        pair_path = L.pair(c, m, p["token"], p["j"], p["n"])
        pr = load_record(pair_path)
        if pr["status"] != "built":
            raise S2Error(f"{wid}: the pair was rejected; no cell to relax")
        built = pr["legs"][leg]
        if built["start_sha256"] != sha256_file(L.cell_file(c, wid, "start")) or pr["region_id"] != reg["region_id"]:
            raise S2Error(f"{wid}: start file or region differ from the pair record")
        if p["kind"] == "DV":
            pwid = pr["parents"]["vac"]
            parent = read_cell(L.cell_file(c, pwid, "relaxed"))
        o2n = {int(k): v for k, v in built["old_to_new"].items()}
        site_cell = o2n.get(p["j"] if p["kind"] == "D" else to_vac_map()(p["j"]))
        token, pose_id, k_min = p["token"], pr["pose_name"], 0 if p["n"] == 0 else None
        labels = [label_of_start(wid, 0)] if p["n"] == 0 and m not in REF_MEMBERS else []
        pair_path = os.path.relpath(pair_path, L.campaign_dir(c))
    free = free_in_cell(reg, p["kind"], built=built)
    c2h, _ = cell_maps(p["kind"], built=built, n_host=len(host))
    n_fixed = assert_fixed_at_host(start, free, host, c2h)
    model = None
    if calc is None:
        calc, model = _calc_for(job, start, wid, free)
    final, rr = relax_frozen(start, calc, free, logfile=L.cell_file(c, wid, "fire"))
    rel = write_cell(L.cell_file(c, wid, "relaxed"), final)
    val = validity(p["kind"], relax_rec=rr, start=start, final=rel, region=reg, host_relaxed=host, parent=parent,
                   built=built, parent_work_id=pwid)
    sets = site_sets(host_context(m))
    c1 = c1_sites(m, m05_cal=job.get("m05_cal"), sets=sets) if m in PILOTS else None
    rec = cell_record(work_id=wid, labels=labels if m not in REF_MEMBERS else [], campaign=c, member=m,
                      role=role_of(m), cell_kind=p["kind"], leg=leg, site=p["j"], site_cell=site_cell,
                      sublattice=p["L"], site_roles=site_roles(m, p["L"], p["j"], sets, c1), token=token,
                      start=p["start"], pose_id=pose_id, is_default_pose=None if token is None else p["n"] == 0,
                      k_min=k_min, region_id=reg["region_id"], free=free, n_free=len(free), n_fixed=n_fixed,
                      parent={"work_id": pwid, "map": "to_vac" if p["kind"] == "V" else "old_to_new"},
                      pair=pair_path, builder={"BUILDER_VERSION": b42.BUILDER_VERSION, "GEOM_SHA": b42.GEOM_SHA,
                                               "partners": None if built is None else load_record(
                                                   L.pair(c, m, p["token"], p["j"], p["n"]))["partners"]},
                      model=model or {"mock": "supplied"}, relax=rr, validity=val,
                      files={k: os.path.relpath(L.cell_file(c, wid, k), L.campaign_dir(c)) for k in ("start", "relaxed")},
                      sha256={k: sha256_file(L.cell_file(c, wid, k)) for k in ("start", "relaxed")},
                      geometry_sha256={"start": sha256_atoms(start), "relaxed": sha256_atoms(rel)},
                      attempts=_attempts(L, c, wid), code=code_state())
    dump_public(rec, L.record(c, wid))
    return rec


def job_validate(job):
    """Checks 1-5 recomputed from the files of one relaxed cell (geometry only); written beside the record."""
    L, c, m, wid = Layout("node", job["root"]), job["campaign"], job["member"], job["work_id"]
    p = parse_work_id(wid)
    rec = load_record(L.record(c, wid))
    start, final = read_cell(L.cell_file(c, wid, "start")), read_cell(L.cell_file(c, wid, "relaxed"))
    if p["kind"] == "host":
        val = validity("host", relax_rec=rec["relax"], start=start, final=final, region=None, host_relaxed=final,
                       pool_member=_pool_start(m))
        if not rec["relax"]["converged"] == val["checks"]["1"]["passed"]:
            raise S2Error(f"{wid}: recomputed check 1 differs from the record")
    else:
        _, host, _ = _host_files(L, c, m)
        reg = _region_of(L, c, m, p["j"], host)
        built, parent, pwid = None, host, make_work_id(m, "host")
        if p["kind"] in ("D", "DV"):
            pr = load_record(L.pair(c, m, p["token"], p["j"], p["n"]))
            built = pr["legs"][p["leg"]]
            if p["kind"] == "DV":
                pwid = pr["parents"]["vac"]
                parent = read_cell(L.cell_file(c, pwid, "relaxed"))
        val = validity(p["kind"], relax_rec=rec["relax"], start=start, final=final, region=reg, host_relaxed=host,
                       parent=parent, built=built, parent_work_id=pwid)
    out = {"schema": RECORD_SCHEMAS["validity"], "work_id": wid, "validity": val,
           "agrees_with_record": val["valid"] == rec["validity"]["valid"] and val["failed"] == rec["validity"]["failed"],
           "written": now()}
    dump_public(out, L.cell_file(c, wid, "validity"))
    if not out["agrees_with_record"]:
        raise S2Error(f"{wid}: recomputed validity {val['failed']} != record {rec['validity']['failed']}")
    return out


def job_distinct(job):
    """Section 9 for one leg: the kept minima of every relaxed start of (member, token, site, leg)."""
    L, c, m, T, j, leg = (Layout("node", job["root"]), job["campaign"], job["member"], job["token"], int(job["site"]),
                          job["leg"])
    hwid, host, _ = _host_files(L, c, m)
    reg = _region_of(L, c, m, j, host)
    starts = job.get("starts") or sorted(
        (f"p{int(mm.group(1))}" for f in os.listdir(os.path.dirname(L.pair(c, m, T, j, 0)))
         for mm in [re.fullmatch(re.escape(f"{m}_{T}{j}") + r"p(\d+)\.json", f)] if mm), key=lambda s: int(s[1:]))
    cells, info = [], {}
    kind = "D" if leg == "novac" else "DV"
    for st in starts:
        n = int(st[1:])
        pr = load_record(L.pair(c, m, T, j, n))
        if pr["status"] != "built":
            info[st] = "pair rejected"
            continue
        wid = pr["legs"][leg]["work_id"]
        if not os.path.exists(L.record(c, wid)):
            raise S2Error(f"{wid}: no relaxation record yet")
        rec = load_record(L.record(c, wid))
        built = pr["legs"][leg]
        o2n = {int(k): v for k, v in built["old_to_new"].items()}
        # the free FA of R_j, found in the leg's partner (relaxed host or V+_Rj) and mapped into the cell; the
        # molecule the dopant replaced (Cs) drops out
        base = host if leg == "novac" else read_cell(L.cell_file(c, pr["parents"]["vac"], "relaxed"))
        hv = (lambda i: i) if leg == "novac" else to_vac_map()
        sks = fa_skeletons(base, [hv(cc) for cc in reg["molecule_carbons_free"]])
        fa = [[o2n[x] for x in sk] for sk in sks if all(x in o2n for x in sk)]
        cells.append({"start": st, "atoms": read_cell(L.cell_file(c, wid, "relaxed")),
                      "dopant_idx": built["members"], "fa": fa, "valid": bool(rec["validity"]["valid"]),
                      "work_id": wid})
        info[st] = "valid" if rec["validity"]["valid"] else f"invalid {rec['validity']['failed']}"
    res = distinct_minima(cells)
    out = {"schema": RECORD_SCHEMAS["distinct"], "member": m, "token": T, "site": j, "leg": leg, "kind": kind,
           "region_id": reg["region_id"], "starts": starts, "status": info, **res,
           "labels": {} if m in REF_MEMBERS else
           {o: label_of_start(make_work_id(m, kind, token=T, j=j, n=int(pn[1:])), int(o[1:]))
            for o, pn in res["map"].items()},
           "work_ids": {o: make_work_id(m, kind, token=T, j=j, n=int(pn[1:])) for o, pn in res["map"].items()},
           "written": now()}
    dump_public(out, L.distinct(c, m, T, j, leg))
    return out


def job_validate_a2(job):
    """Section 11, 'Validity on the final geometries' (I-F1): checks 2-5 on the final geometry of one A2 relaxation
    (host_R: check 4 only), geometry only. scripts/50 writes the final geometries (positions of the last configuration
    read with scripts/47 read='final_geom', on the A2 start as template) and names every file in job["files"]:
    start (the start of the cell's A1 relaxation: builder output, or the pool member for host_R; I-A4), final,
    parent_final (the final geometry of the section 11 partner: host_R for V+_R and D, V+_R for D+V; None if the
    partner has no final geometry), host_relaxed (the S2-relaxed host), region (the region record), pair (D, D+V).
    Without the partner's final geometry check 5 cannot be evaluated: the job is refused (S2Error), so a recorded
    check-5 failure always comes from an evaluated check; scripts/50 skips such a check job, and the quartet is
    invalid through the missing partner (round-2 R2V-1). Writes the s2-a2validity-1 record to job["out"]."""
    f = job["files"]
    kind, label = job["kind"], job["label"]
    if kind not in ("host", "V", "D", "DV"):
        raise S2Error(f"validate-a2: kind {kind!r}")
    reg = check_region_record(load_record(f["region"]))
    host = read_cell(f["host_relaxed"])
    if reg["host_source"]["sha256"] != sha256_atoms(host):
        raise S2Error(f"{label}: the region record was built on another relaxed host")
    if int(reg["site"]) != int(job["site"]):
        raise S2Error(f"{label}: region of site {reg['site']}, job site {job['site']}")
    start, final = read_cell(f["start"]), read_cell(f["final"])
    if len(start) != len(final) or not np.array_equal(start.numbers, final.numbers) or \
            not np.allclose(start.cell.array, final.cell.array, rtol=0, atol=1e-9):
        raise S2Error(f"{label}: the final geometry is not a configuration of the A1 cell (atoms or cell differ)")
    built = None
    if kind in ("D", "DV"):
        pr = load_record(f["pair"])
        if pr.get("status") != "built" or pr.get("region_id") not in (None, reg["region_id"]):
            raise S2Error(f"{label}: pair record not built or of another region")
        built = pr["legs"][job["leg"]]
    parent = read_cell(f["parent_final"]) if f.get("parent_final") else None
    if kind != "host" and parent is None:
        # round-2 R2V-1: check 5 needs the partner's final geometry; without it the check is not evaluated (never a
        # recorded failure): the caller must not run the job, and the quartet is invalid through the missing partner
        raise S2Error(f"{label}: validate-a2 of kind {kind} needs the section 11 partner's final geometry "
                      "(check 5 cannot be evaluated without it)")
    val = validity_a2(kind, start=start, final=final, region=reg, host_relaxed=host, parent_final=parent, built=built)
    out = {"schema": RECORD_SCHEMAS["a2validity"], "label": label, "kind": kind, "site": int(job["site"]),
           "token": job.get("token"), "leg": job.get("leg"), "region_id": reg["region_id"],
           "parent_label": job.get("parent_label"), "validity": val,
           "geometry_sha256": {"start": sha256_atoms(start), "final": sha256_atoms(final),
                               "parent_final": None if parent is None else sha256_atoms(parent),
                               "host_relaxed": sha256_atoms(host)},
           "rule": "S2_PLAN.md section 11: section 5 checks 2-5 on the final geometries (host_R: check 4); partner "
                   "check between the final geometries of child and parent", "written": now()}
    dump_public(out, job["out"])
    return out


JOBS = {"relax-host": job_relax_host, "region": job_region, "build-vac": job_build_vac, "build-pair": job_build_pair,
        "relax": job_relax, "validate": job_validate, "distinct": job_distinct, "validate-a2": job_validate_a2}


def _check_job(job):
    """Keys of the spec's JOB.json that 46 derives itself (kind, pose, region) must agree when they are given
    (fail-closed; N-A12)."""
    if job.get("work_id") and job.get("kind"):
        k = parse_work_id(job["work_id"])["kind"]
        if job["kind"] != k:
            raise S2Error(f"job kind {job['kind']!r} != {k!r} of {job['work_id']}")
    if job["action"] == "build-pair" and job.get("pose") is not None:
        n = int(str(job.get("start", "p0")).lstrip("p"))
        ok = {_pose_name(job["token"], n)} | ({"inherit"} if n == 0 else set())
        if job["pose"] not in ok:
            raise S2Error(f"job pose {job['pose']!r} != start p{n} of {job['token']} ({sorted(ok)})")
    if job.get("region") and job.get("site") is not None:
        Ls = SUBLATTICE[job["token"]] if job.get("token") else \
            (parse_work_id(job["work_id"])["L"] if job.get("work_id") else None)
        want = None if Ls is None else os.path.basename(Layout("node", job["root"]).region(job["campaign"],
                                                                                           job["member"], Ls, job["site"]))
        if want is not None and os.path.basename(str(job["region"])) != want:
            raise S2Error(f"job region {job['region']!r} is not the region of {job['member']} {Ls}{job['site']}")


def run_job(job, calc=None):
    act = job["action"]
    if act not in JOBS:
        raise S2Error(f"unknown job action {act!r}")
    _check_job(job)
    if act in ("relax-host", "relax"):
        out = JOBS[act](job, calc)
        if job.get("calc") != "mace":
            no_model()
        return out
    out = JOBS[act](job)
    no_model()
    return out


# ---------------------------------------------------------------- CLI
def cmd_sites(a):
    ctx = host_context(a.member)
    sets = site_sets(ctx)
    if a.member in SITE_TABLE:
        assert_site_tables(a.member, sets)
    print(f"# {a.member}: vi {ctx.vi}, migrating iodide I{ctx.mig_host} (host numbering), Cs-v {sets['cs_v_A']:.3f} A")
    for L in "BAX":
        s = sets[L]
        print(f"{L}: first {s['first']}  far {[(j, round(s['d'][j], 3)) for j in s['far']]}  "
              f"four farthest {s['far4']}")
    if a.member in PILOTS:
        print(json.dumps(c1_sites(a.member, sets=sets), indent=1, default=str))
    no_model()
    print("tables asserted; 'mace' not in sys.modules")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="S2 cells (Stage 0 module A; S2_PLAN.md sections 4, 5, 9, 11)")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--work", default=None, help="self-test: parent directory of the temporary work tree")
    sub = ap.add_subparsers(dest="cmd")
    sp = sub.add_parser("sites"); sp.add_argument("--member", required=True)
    for nm in JOBS:
        sp = sub.add_parser(nm); sp.add_argument("--job", required=True)
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test(a.work)
    if a.cmd is None:
        ap.print_help(); return 2
    try:
        if a.cmd == "sites":
            return cmd_sites(a)
        job = load_job(a.job)
        if job["action"] != a.cmd:
            raise S2Error(f"job action {job['action']!r} != subcommand {a.cmd!r}")
        run_job(job)
        print(f"{a.cmd}: done")
        return 0
    except (S2Error, Refused, BuildError, AssertionError) as e:
        print(f"STOP ({type(e).__name__}): {e}", file=sys.stderr)
        return 3


# ---------------------------------------------------------------- self-test (plan section 17 item 2; spec 6.11)
def _nudge_to(value_fn, target, op, max_iter=80):
    """Move a construction parameter from the boundary value by a doubling step (from one ulp) until the computed
    value satisfies op(value, target), so that a boundary case tests the comparison, not floating round-off.
    Returns (parameter, computed value); the parameter stays within about 1e-10 of the boundary."""
    up = op(target + 1.0, target)
    x, step = float(target), abs(np.spacing(float(target)))
    for _ in range(max_iter):
        v = value_fn(x)
        if op(v, target):
            assert abs(x - target) < 1e-9 * max(1.0, abs(target)), (x, target)
            return x, v
        x = float(target) + (step if up else -step)
        step *= 2.0
    raise AssertionError("boundary construction did not converge")


def _rotate_about(P, centre, axis, deg):
    a = np.asarray(axis, float) / np.linalg.norm(axis)
    t = np.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    R = np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * K @ K
    return centre + (P - centre) @ R.T


def self_test(work=None):
    import traceback
    t0 = time.time()
    results = []
    tmp = tempfile.mkdtemp(prefix="s2cells_selftest_", dir=work)

    def case(name, fn):
        t = time.time()
        try:
            msg = fn()
            results.append((name, True))
            print(f"PASS {name}: {msg}  [{time.time() - t:.1f} s]", flush=True)
        except Exception as e:                       # noqa: BLE001 (every failure is reported)
            results.append((name, False))
            print(f"FAIL {name}: {type(e).__name__}: {e}  [{time.time() - t:.1f} s]", flush=True)
            traceback.print_exc(limit=5)

    print(f"46_s2_cells self-test: {b42.BUILDER_VERSION}, GEOM_SHA {b42.GEOM_SHA}, ase/numpy {versions()}")
    ctx = {}

    def C(m):
        if m not in ctx:
            ctx[m] = host_context(m)
        return ctx[m]
    sets = {}

    def S(m):
        if m not in sets:
            sets[m] = site_sets(C(m))
        return sets[m]

    def t_constants():
        # literal copies of the plan text (sections 2-5, 9, 11): a change to a constant must also change these
        pins = {"VI": (VI, 127), "PILOTS": (PILOTS, ("m30", "m05")), "MULTI_START": (MULTI_START, ("Cs", "Cl")),
                "FIRST_CUT_A": (FIRST_CUT_A, {"B": 5.0, "A": 6.0}), "FAR_MIN_A": (FAR_MIN_A, {"B": 8.5, "A": 9.0, "X": 9.0}),
                "REGION_RADIUS_A": (REGION_RADIUS_A, 6.0), "REFILL_MIN_A": (REFILL_MIN_A, 1.2),
                "VAC_DELETE_MAX_A": (VAC_DELETE_MAX_A, 1.2), "DOPANT_MAX_A": (DOPANT_MAX_A, 1.0),
                "ORG_BOND_CUT": (ORG_BOND_CUT, {("C", "N"): 1.6, ("C", "C"): 1.7, ("H", "N"): 1.25, ("C", "H"): 1.25}),
                "ORG_INORG_MIN": (ORG_INORG_MIN, {"H": 1.25, "C": 1.6, "N": 1.6}),
                "INORGANIC": (INORGANIC, ("Pb", "I", "Cl", "Cs", "Sr", "Ca")), "FLOOR_A": (FLOOR_A, 0.65),
                "PARTNER": ((PARTNER_CUT_A, PARTNER_DR_A, PARTNER_ROT_DEG), (6.0, 0.25, 20.0)),
                "DISTINCT": ((DISTINCT_DR_A, DISTINCT_ROT_DEG), (0.25, 20.0)), "FMAX_STEPS": ((FMAX, STEPS), (0.01, 10000)),
                "HOST": ((HOST_STAGES, HOST_STEPS), ((0.02, 0.01, 0.005), 10000)),
                "THREADS": ((THREADS, MAX_CONCURRENT_MACE), (6, 10)), "MACE_VERSION": (MACE_VERSION, "0.3.16"),
                "FOUNDATION_SHA256": (FOUNDATION_SHA256,
                                      "01bfe22100139f424713cf921144e5509cbe353d67aa9fa1be9c6e1e0ed35845"),
                "MACE_Z_REQUIRED": (MACE_Z_REQUIRED, {1, 6, 7, 17, 20, 38, 53, 55, 82}),
                "PBCL_DEFAULT_A": (PBCL_DEFAULT_A, 2.837), "CAL_SITES": (CAL_SITES, {"m30": {"B": 136, "A": 128, "X": 138},
                                                                                    "m05": {"B": 124, "A": 28, "X": 49}}),
                "POSE_SITES": (POSE_SITES, {"Cs": (128, 188), "Cl": (138, 175)}),
                "G1_SPIN": ((G1_SITES, SPIN_SITES, SR_FAR_SITE), ({"Cl": 138, "Ca": 136}, {"Cl": 175, "Ca": 76}, 76))}
        for k, (got, lit) in pins.items():
            assert got == lit, f"{k}: {got} != plan {lit}"
        assert len(DRAW) == 28 and [r for r in range(1, 29)] == list(range(1, len(DRAW) + 1))
        elig = [f"m{k:02d}" for k in range(36) if f"m{k:02d}" not in DRAW_EXCLUDED]
        got = sorted(((zlib.crc32(("S2n-host-" + m).encode()), m) for m in elig))
        assert [(m, c) for c, m in got] == list(DRAW), "section 3 draw differs"
        for L, order in M05_DRAW_ORDER.items():
            excl = {"A": 128, "X": 53}[L]
            labs = [(zlib.crc32(("S2n-cal-m05-" + ("FA" if L == "A" else "I") + str(j)).encode()), j)
                    for j in FIRST_SHELL[L] if j != excl]
            assert [(j, c) for c, j in sorted(labs)] == list(order), f"section 11 m05 draw {L} differs"
        assert b42.GEOM_SHA == GEOM_SHA_S2B2 and b42.BUILDER_VERSION == "s2b-2"
        assert b42.sampled_names("Cs") == ["centred", "q0+", "q0-", "q1+", "q1-", "q2+", "q2-"]
        assert b42.sampled_names("Cl") == ["centred", "shift_a", "shift_b"]
        assert all(b42.REGISTRY[t]["site"] == SUBLATTICE[t] for t in TOKENS)
        assert set(TOKENS) == {CONTROL, *DECISIVE} and set(MULTI_START) <= set(TOKENS)
        return "section 3 draw (28, crc32) and section 11 m05 draws reproduced; s2b-2 pinned; registry agrees"

    def t_sites():
        hosts = list(SITE_TABLE)
        for m in hosts:
            assert_site_tables(m, S(m))
            for L in "BAX":
                assert len(S(m)[L]["production"]) == {"B": 4, "A": 5, "X": 10}[L]
        n = sum(len(S(m)[L]["production"]) for m in hosts for L in "BAX")
        assert n == 19 * 14
        return f"14 hosts: first shells, gaps, far pairs (order, 2 dp), migrating I, Cs-v, four farthest (m30, m05)"

    def t_census():
        s = S("m05")
        for L, tab in M05_CENSUS_A.items():
            for j, dt in tab.items():
                assert abs(s[L]["d"][j] - dt) <= TABLE_TOL_A, (L, j, s[L]["d"][j], dt)
        assert s["mig_host"] == 53 and S("m30")["A"]["ranked"][0][0] == 128 == s["A"]["ranked"][0][0]
        sizes, xs = {}, {}
        for (L, j), n in M05_REGION_SIZES.items():
            sizes[f"{L}{j}"] = build_region(C("m05").host, "m05", j)["n_free"]
            assert sizes[f"{L}{j}"] == n, (L, j, sizes[f"{L}{j}"], n)
        for (L, j), n in M30_REGION_SIZES_XCHECK.items():
            xs[f"{L}{j}"] = build_region(C("m30").host, "m30", j)["n_free"]
            assert xs[f"{L}{j}"] == n, (L, j, xs[f"{L}{j}"], n)
        c05, c30 = c1_sites("m05", sets=s), c1_sites("m30", sets=S("m30"))
        assert c05["cal"] == {"B": 124, "A": 28, "X": 49} and c30["cal"] == {"B": 136, "A": 128, "X": 138}
        assert c30["pose"]["Cs"] == {"near": 128, "far": 188} and c30["spin"] == {"Cl": 175, "Ca": 76}
        for bad in ({"B": 136, "A": 28, "X": 49}, {"B": 124, "A": 128, "X": 49}, {"B": 124, "A": 28, "X": 53}):
            try:
                c1_sites("m05", m05_cal=bad, sets=s)
                raise AssertionError(f"m05_cal {bad} accepted")
            except S2Error:
                pass
        assert c1_sites("m05", m05_cal={"B": 124, "A": 92, "X": 138}, sets=s)["cal"]["A"] == 92
        return f"m05 census to 0.005 A; regions m05 {sizes} (section 11); m30 cross-check {xs}; c1 sites"

    def t_regions():
        rep = []
        for m in PILOTS:
            cx = C(m)
            host, vac = cx.host, cx.vac
            for L, j in CAL_SITES[m].items():
                reg = build_region(host, m, j)
                rid = reg["region_id"]
                assert rid == region_id(m, j, list(reversed(reg["free"]))) == region_id(m, j, reg["free"])
                assert rid != region_id(m, j + 1, reg["free"]) and rid != region_id("m31", j, reg["free"])
                assert VI in reg["free"] and set(reg["free"]) >= set(reg["inorganic_free"])
                mols = host_molecules(host)
                for cc in reg["molecule_carbons_free"]:
                    assert set(mols[cc][0]) <= set(reg["free"])           # whole molecules
                fV = free_in_cell(reg, "V")
                tv = to_vac_map()
                assert len(fV) == reg["n_free"] - 1 and fV == sorted(tv(i) for i in reg["free"] if i != VI)
                assert all(i - 1 in fV for i in reg["free"] if i > VI) and all(i in fV for i in reg["free"] if i < VI)
                c2h, _ = cell_maps("V", n_host=len(host))
                assert_fixed_at_host(vac, fV, host, c2h)
                for T in TOKENS_OF[L]:
                    bh, bv = build_pair(host, vac, cx, T, j, "inherit", partners="unrelaxed")
                    for kind, b, base in (("D", bh, host), ("DV", bv, vac)):
                        f = free_in_cell(reg, kind, built=b)
                        ns_ = types.SimpleNamespace(old_to_new=dict(b.old_to_new), members=list(b.members))
                        assert free_in_cell(reg, kind, built=ns_) == f == free_in_cell(
                            reg, kind, built=json.loads(json.dumps(_leg_rec(b, "x"))))
                        assert set(b.members) <= set(f)
                        src = reg["free"] if kind == "D" else fV
                        img = [b.old_to_new[i] for i in src if i in b.old_to_new]
                        assert len(f) == len(img) + len([mm for mm in b.members if mm not in set(img)])
                        c2h, c2p = cell_maps(kind, built=b, n_host=len(host))
                        assert_fixed_at_host(b.atoms, f, host, c2h)
                        if T == "GA":
                            assert b.centre in f and all(a in f for a in b.added)
                        if T == "Cs":
                            assert all(i not in b.old_to_new for i in b.deleted) and b.added[0] in f
                            assert len(b.deleted) == 8
                    rep.append(f"{m} {T}{j}")
        bad = dict(build_region(C("m30").host, "m30", 136)); bad["free"] = bad["free"][:-1]
        try:
            check_region_record(bad)
            raise AssertionError("an edited region record was accepted")
        except S2Error:
            pass
        return f"region_id deterministic, order-free, site/member specific; host->V->doped transfer for {len(rep)} pairs"

    def t_labels():
        st = {p: label_sites(p, S(p)) for p in PILOTS}
        ls = c1_label_sets(sites={p: S(p) for p in PILOTS})
        sp = (ls["g1"] + ls["spin"] + ls["noise"]["m30"] + ls["noise"]["m05"] + ls["step0"] + ls["pose"] + ls["q0"])
        a2 = ls["a2"]["c2"] + ls["a2"]["c4"]
        ref = ls["smoke"] + ls["tp"] + ["s2smoke_ref232_rst64", "s2smoke_ref232_rst2x32"]
        for lab in sp + a2 + ref:
            check_label(lab, st)
        assert len(sp) == len(set(sp)), "duplicate C1 single-point labels"
        assert len(ls["g1"]) == 5 and len(ls["spin"]) == 2 and len(ls["noise"]["m30"]) == 53 == len(ls["noise"]["m05"])
        assert len(ls["q0"]) == 10 and len(ls["pose"]) == 36 and len(ls["step0"]) == 2
        spin_partners = ["s2_m30_Cl175o0_vac", "s2_m30_Ca76o0_vac"]
        assert set(spin_partners) <= set(ls["noise"]["m30"]) and "s2_m30_Cs188o0_vac" in ls["noise"]["m30"]
        w = ls["work"]
        assert (len(w["host"]), len(w["V"]), len(w["noise"]), len(w["start_set"]), len(w["pose_extra"])) == \
            (2, 30, 80, 20, 32), {k: len(v) for k, v in w.items()}
        allw = sum(w.values(), [])
        assert len(allw) == len(set(allw))
        for x in allw:
            check_work_id(x, st)
        assert a2 == ["s2r_m30_VB136", "s2r_m30_hostB136", "s2r_m30_Sr136o0_novac", "s2r_m30_Sr136o0_vac",
                      "s2r_m30_hostB76", "s2r_m30_VB76", "s2r_m30_Sr76o0_novac", "s2r_m30_Sr76o0_vac",
                      "s2r_m30_Ca136o0_novac", "s2r_m30_Ca136o0_vac", "s2r_m30_hostX138", "s2r_m30_VX138",
                      "s2r_m30_Cl138o0_novac", "s2r_m30_Cl138o0_vac", "s2r_m30_hostA128", "s2r_m30_VA128",
                      "s2r_m30_Cs128o0_novac", "s2r_m30_Cs128o0_vac", "s2r_m30_GA128o0_novac", "s2r_m30_GA128o0_vac",
                      "s2r_m05_hostB124", "s2r_m05_VB124", "s2r_m05_Sr124o0_novac", "s2r_m05_Sr124o0_vac",
                      "s2r_m05_Ca124o0_novac", "s2r_m05_Ca124o0_vac", "s2r_m05_hostX49", "s2r_m05_VX49",
                      "s2r_m05_Cl49o0_novac", "s2r_m05_Cl49o0_vac", "s2r_m05_hostA28", "s2r_m05_VA28",
                      "s2r_m05_Cs28o0_novac", "s2r_m05_Cs28o0_vac", "s2r_m05_GA28o0_novac", "s2r_m05_GA28o0_vac"]
        neg = ["s2_m30_VB128", "s2_m30_Sr128o0_vac", "s2_m30_Cl76o0_vac", "s2_m30_Sr136o0_novac_q0",
               "s2_m30_host_q0", "s2r_m30_Cs128o1_vac", "s2r_m30_host", "s2r_m21_VB136", "s2g1_m05_host_e60",
               "s2g1_m30_Cl175o0_novac_e60", "s2spin_m30_Cl175o0_vac_q0", "s2spin_m30_Cl175o0_novac",
               "s2_m30_VB0136", "s2_m30_Sr136o00_vac", "s2_m30_Rb128o0_vac", "s2_m30_Sr136o1_vac",
               "s2_m30_Cs128o7_vac", "s2_m30_Cl138o3_vac", "s2_m30_hostB136", "s2_m30_VB136_e50", "s2_m04_host",
               "s2_m30_VX127", "s2_m30_VB24_e60", "s2r_m30_VB136_q0", "s2tp_ref233_np48", "s2_m30_SR136o0_vac",
               "s2_m06_VB24", "S2_m30_host", "s2_m30_host ", "s2_m30_Sr136o0_vac_q0_e60"]
        sites_all = dict(st); sites_all["m06"] = label_sites("m06", S("m06"))
        for x in neg:
            try:
                check_label(x, sites_all)
                raise AssertionError(f"accepted {x}")
            except S2Error:
                pass
        for x in ["s2_m30_Cs128p7_vac", "s2_m30_Sr136p1_vac", "s2_m30_VB0", "s2_ref233_VB136x"]:
            try:
                check_work_id(x, st)
                raise AssertionError(f"accepted work id {x}")
            except S2Error:
                pass
        a33 = _load("a33", "33_finetune_dataset.py")
        for x in sp + a2 + ref + allw:
            assert not any(pt.fullmatch(x) for pt in a33.PATTERNS.values()), f"{x} matches a scripts/33 pattern"
        pl = parse_label("s2_m30_Sr136o0_vac_q0")
        assert pl["tot_charge"] == 0 and pl["vacancy"] and parse_label("s2_m30_VB136")["tot_charge"] == 1
        assert parse_label("s2r_m30_hostB136")["kind"] == "host" and parse_label("s2g1_m30_host_e60")["ecut"] == 60
        assert campaign_of("s2r_m30_VB136") == "c2" and campaign_of("s2r_m05_VA28") == "c4"
        assert campaign_of("s2_m06_host") == "c3" and campaign_of("s2_m30_Cs128p3_vac") == "c1"
        st_ = {"stage0": {"production_n8": ["m06"], "m05_cal": {"B": 124, "A": 92, "X": 49}}, "n": 8}
        assert campaign_of("s2r_m05_VA92", st_) == "c4"
        for x, s_ in (("s2r_m05_VA28", st_), ("s2_m02_host", st_)):
            try:
                campaign_of(x, s_)
                raise AssertionError(f"campaign of {x}")
            except S2Error:
                pass
        return (f"{len(sp)} C1 single-point labels, {len(a2)} A2, {len(ref)} reference, {len(allw)} work ids pass; "
                f"{len(neg)} negative labels refused; none matches scripts/33 PATTERNS")

    def t_validity():
        host = read(os.path.join(ROOT, REF_HOST))
        cell = host.cell.array
        s = _syms(host)
        v = host.positions[VI].copy()
        vac = read(os.path.join(ROOT, REF_VAC))
        out = []
        # check 1
        base = {"converged": True, "steps": 10000, "steps_cap": 10000, "fmax_eVA": 0.01, "fmax_final_free_eVA": 0.0099}
        assert check_converged(base)["passed"], "last-step convergence must pass"
        assert check_converged(dict(base, steps=57))["passed"]
        assert not check_converged(dict(base, converged=False, fmax_final_free_eVA=0.0101))["passed"]
        assert not check_converged(dict(base, fmax_final_free_eVA=0.01))["passed"], "strict test"
        out.append("1")
        # check 2: an I (and a Cl) moved to 1.2000 A of v fails, 1.2001 passes
        i = int(np.flatnonzero(_syms(vac) == "I")[0])
        e = np.array([1.0, 0.0, 0.0])

        def at_d(x, sym="I"):
            a = vac.copy(); a.positions[i] = v + x * e
            if sym != "I":
                a.symbols[i] = sym
            return a
        x, dv_ = _nudge_to(lambda x: dist_to(at_d(x), v)[i], REFILL_MIN_A, lambda a_, b_: a_ <= b_)
        assert not check_refill(at_d(x), v)["passed"] and not check_refill(at_d(x, "Cl"), v)["passed"]
        assert check_refill(at_d(1.2001), v)["passed"] and check_refill(at_d(1.2001, "Cl"), v)["passed"]
        assert check_refill(vac, v)["passed"] and check_refill(at_d(x, "Cl"), v)["species"] == "Cl"
        out.append(f"2 (I and Cl at {dv_:.16f} A fail)")
        # check 3
        c = 136

        def moved(x):
            a = host.copy(); a.positions[c] = host.positions[c] + x * e; return a
        assert check_dopant_on_site(host, moved(0.999), c)["passed"]
        x1, _ = _nudge_to(lambda x: check_dopant_on_site(host, moved(x), c)["displacement_A"], 1.0, lambda a_, b_: a_ >= b_)
        assert not check_dopant_on_site(host, moved(x1), c)["passed"]
        out.append("3")
        # check 4
        assert check_topology(host, host)["passed"]
        rng = np.random.default_rng(1)
        jit = host.copy(); ino = np.flatnonzero(np.isin(s, INORGANIC))
        jit.positions[ino] += rng.normal(0, 0.01, (len(ino), 3))
        assert check_topology(host, jit)["passed"]
        C0 = int(np.flatnonzero(s == "C")[0])
        mol, ns = a38.molecule(host, C0, s, cell)
        lost = host.copy(); lost.positions[ns[0]] = host.positions[C0] + 1.7 * (dvec(host, ns[0], host.positions[C0]) /
                                                                               np.linalg.norm(dvec(host, ns[0], host.positions[C0])))
        r = check_topology(host, lost); assert not r["passed"] and r["bonds_lost"]
        # an inorganic atom (an I) brought along the C -> H direction to d of the FA's C-H hydrogen: the organic
        # graph is untouched, so only the organic-inorganic rule can fire
        hc = [k for k in mol if s[k] == "H" and mic_norm(host.positions[k] - host.positions[C0], cell) < 1.25][0]
        u = dvec(host, hc, host.positions[C0]); u = u / np.linalg.norm(u)
        i2 = int(np.flatnonzero(s == "I")[3])

        def near_h(x):
            a = host.copy(); a.positions[i2] = host.positions[C0] + mic_norm(host.positions[hc] - host.positions[C0],
                                                                            cell) * u + x * u
            return a
        r = check_topology(host, near_h(1.24))
        assert not r["passed"] and r["h_inorganic_min_A"] < 1.25 and not r["bonds_lost"] and not r["bonds_added"]
        xb, _ = _nudge_to(lambda x: check_topology(host, near_h(x))["h_inorganic_min_A"], 1.25, lambda a_, b_: a_ <= b_)
        assert not check_topology(host, near_h(xb))["passed"]
        assert check_topology(host, near_h(1.2501))["passed"]
        pb = int(np.flatnonzero(s == "Pb")[0])

        def near_pb(x):
            a = host.copy(); a.positions[i2] = host.positions[pb] + x * e; return a
        r = check_topology(host, near_pb(0.64)); assert not r["passed"] and r["min_pair_A"] < 0.65
        xf, vf = _nudge_to(lambda x: check_topology(host, near_pb(x))["min_pair_A"], 0.65, lambda a_, b_: a_ < b_)
        assert not check_topology(host, near_pb(xf))["passed"]
        xg, vg = _nudge_to(lambda x: check_topology(host, near_pb(x))["min_pair_A"], 0.65, lambda a_, b_: a_ >= b_)
        assert check_topology(host, near_pb(xg))["passed"]
        comp = host.copy(); comp.symbols[i2] = "Cl"
        r = check_topology(host, comp); assert not r["passed"] and not r["composition_equal"]
        out.append(f"4 (lost C-N; H at 1.24 and 1.2500 A of an I fail, 1.2501 passes; pairs at 0.64 and {vf:.16f} A "
                   f"fail, {vg:.16f} A passes; composition)")
        # check 5: inorganic beyond 6 A moved 0.2499 passes / 0.25 fails; FA rotated 19.9 passes / 20.0 fails
        cen = host.positions[136]
        dh = dist_to(host, cen)
        ident = {k: k for k in range(len(host))}
        far_i = int([k for k in np.flatnonzero(s == "I") if dh[k] > 7.0][0])
        near_i = int([k for k in np.flatnonzero(s == "I") if dh[k] < 5.0 and k != VI][0])
        allf = list(range(len(host)))

        def p5(child):
            return check_partner(child, host, ident, host_relaxed=host, child_to_host=ident, centre_host=cen,
                                 free_child=allf)

        def mv(k, x):
            a = host.copy(); a.positions[k] = host.positions[k] + x * e; return a
        assert p5(mv(far_i, 0.2499))["passed"]
        x2, _ = _nudge_to(lambda x: mic_norm(mv(far_i, x).positions[far_i] - host.positions[far_i], cell), 0.25,
                          lambda a_, b_: a_ >= b_)
        assert not p5(mv(far_i, x2))["passed"]
        r = p5(mv(near_i, 0.5)); assert r["passed"] and r["within_6A_reported"]["max_dr_inorganic_A"] >= 0.5 - 1e-9
        cf = [int(k) for k in np.flatnonzero(s == "C") if dh[k] > 7.0][0]
        cn = [int(k) for k in np.flatnonzero(s == "C") if dh[k] < PARTNER_CUT_A][0]

        def rot(cc, deg):
            m_, ns_ = a38.molecule(host, cc, s, cell)
            a = host.copy()
            P = host.positions[cc] + find_mic(host.positions[m_] - host.positions[cc], cell, pbc=True)[0]
            ax = np.cross(P[m_.index(ns_[0])] - P[0], P[m_.index(ns_[1])] - P[0])
            a.positions[m_] = _rotate_about(P, P[0], ax, deg)
            return a
        assert p5(rot(cf, 19.9))["passed"]
        d20, got = _nudge_to(lambda x: p5(rot(cf, x))["gated"]["max_rot_fa_deg"], 20.0, lambda a_, b_: a_ >= b_)
        assert not p5(rot(cf, d20))["passed"]
        r = p5(rot(cn, 30.0)); assert r["passed"] and r["within_6A_reported"]["max_rot_fa_deg"] > 29.9
        out.append(f"5 (0.2499/0.25 A, 19.9/{got:.12f} deg gated; within 6 A reported only)")
        return "; ".join(out)

    def t_validity_wrap():
        cx = ref_context()
        host, vac = cx.host, cx.vac
        reg = build_region(host, "ref233", 136)
        rr = {"converged": True, "steps": 10, "steps_cap": 10000, "fmax_eVA": 0.01, "fmax_final_free_eVA": 0.005}
        vV = validity("V", relax_rec=rr, start=vac, final=vac, region=reg, host_relaxed=host)
        assert vV["valid"] and vV["checks"]["3"] is None and vV["checks"]["2"]["passed"]
        bh, bv = build_pair(host, vac, cx, "Sr", 136, "inherit", partners="unrelaxed")
        vD = validity("D", relax_rec=rr, start=bh.atoms, final=bh.atoms, region=reg, host_relaxed=host, built=bh)
        vDV = validity("DV", relax_rec=rr, start=bv.atoms, final=bv.atoms, region=reg, host_relaxed=host, parent=vac,
                       built=bv)
        assert vD["valid"] and vDV["valid"] and vD["checks"]["2"] is None and vDV["checks"]["5"]["passed"]
        moved = bv.atoms.copy(); moved.positions[bv.centre] += [1.1, 0, 0]
        vbad = validity("DV", relax_rec=rr, start=bv.atoms, final=moved, region=reg, host_relaxed=host, parent=vac,
                        built=bv)
        assert not vbad["valid"] and 3 in vbad["failed"]
        a2 = validity_a2("DV", start=bv.atoms, final=bv.atoms, region=reg, host_relaxed=host, parent_final=vac, built=bv)
        assert a2["valid"] and "1" not in a2["checks"]
        assert validity_a2("host", start=host, final=host, region=reg, host_relaxed=host)["valid"]
        return "validity() and validity_a2() apply the spec 6.6 table (host, V, D, D+V; A2 without check 1)"

    def t_distinct():
        host = read(os.path.join(ROOT, REF_HOST))
        s, cell = _syms(host), host.cell.array
        dop = [int(np.flatnonzero(s == "Cs")[0])]
        fa_c = [int(k) for k in np.flatnonzero(s == "C")][:4]
        fa = fa_skeletons(host, fa_c)
        e = np.array([0.0, 1.0, 0.0])

        def cell_(start, ddop=0.0, rotc=None, deg=0.0, valid=True):
            a = host.copy()
            a.positions[dop[0]] += ddop * e
            if rotc is not None:
                m_, ns_ = a38.molecule(host, rotc, s, cell)
                P = host.positions[rotc] + find_mic(host.positions[m_] - host.positions[rotc], cell, pbc=True)[0]
                a.positions[m_] = _rotate_about(P, P[0], [0, 0, 1], deg)
            return {"start": start, "atoms": a, "dopant_idx": dop, "fa": fa, "valid": valid}
        r = distinct_minima([cell_("p0"), cell_("p1")]); assert r["kept"] == ["p0"] and r["map"] == {"o0": "p0"}
        r = distinct_minima([cell_("p0"), cell_("p1", 0.26)]); assert r["kept"] == ["p0", "p1"] and r["map"]["o1"] == "p1"
        x, _ = _nudge_to(lambda x: mic_norm(cell_("p1", x)["atoms"].positions[dop[0]] - host.positions[dop[0]], cell),
                         0.25, lambda a_, b_: a_ <= b_)
        r = distinct_minima([cell_("p0"), cell_("p1", x)]); assert r["kept"] == ["p0"]
        r = distinct_minima([cell_("p0"), cell_("p1", rotc=fa_c[0], deg=21.0)]); assert r["kept"] == ["p0", "p1"]
        # greedy: A kept, B distinct from A kept, C distinct from B but not from A -> not kept
        r = distinct_minima([cell_("p0"), cell_("p2", 0.4), cell_("p3", 0.1)])
        assert r["kept"] == ["p0", "p2"], r["kept"]
        # invalid default: no o0; the first kept non-default minimum is o1
        r = distinct_minima([cell_("p0", valid=False), cell_("p1", 0.3), cell_("p2", 0.31)])
        assert "o0" not in r["map"] and r["map"] == {"o1": "p1"} and r["excluded"] == ["p0"]
        try:
            distinct_minima([cell_("p1"), cell_("p0")])
            raise AssertionError("out-of-order starts accepted")
        except S2Error:
            pass
        return "identical 1; 0.26 A 2; 0.25 A 1; 21 deg 2; greedy against every kept minimum; invalid default no o0"

    def t_relax():
        cx = ref_context()
        reg = build_region(cx.host, "ref233", 136)
        free = free_in_cell(reg, "V")
        c2h, _ = cell_maps("V", n_host=len(cx.host))
        assert_fixed_at_host(cx.vac, free, cx.host, c2h)
        calc = mock_calc(cx.vac, "selftest_V136", free)
        fin, rec = relax_frozen(cx.vac, calc, free)
        fixed = np.setdiff1d(np.arange(len(cx.vac)), free)
        assert np.array_equal(fin.positions[fixed], cx.vac.positions[fixed]) and rec["converged"]
        assert rec["max_dr_free_A"] > 0.005 and check_converged(rec)["passed"]
        calc = mock_calc(cx.vac, "selftest_V136", free)
        fin3, rec3 = relax_frozen(cx.vac, calc, free, steps=3)
        assert not rec3["converged"] and rec3["steps"] == 3 and not check_converged(rec3)["passed"]
        assert np.array_equal(fin3.positions[fixed], cx.vac.positions[fixed])
        hz, parts = relax_host(cx.host, mock_calc(cx.host, "selftest_host"), "s2_ref233_host", pool_member=cx.host)
        assert parts["validity"]["valid"] and parts["relax"]["stages"][-1]["fmax_target"] == 0.005
        return (f"mock FIRE: {rec['steps']} steps, {len(free)} free / {len(fixed)} fixed (bitwise), steps=3 not "
                f"converged; staged host relaxation valid ({parts['relax']['steps']} steps)")

    def t_poses():
        cx = C("m30")
        out = []
        for j in POSE_SITES["Cs"]:
            st = pose_starts(cx.host, cx, "Cs", j)
            assert [x["name"] for x in st] == b42.T4_PINNED[f"Cs@{j}"] and [x["start"] for x in st] == \
                [f"p{n}" for n in range(7)]
            out.append(f"Cs@{j} {len(st)}")
        try:
            pose_starts(cx.host, cx, "Cl", 138)
            raise AssertionError("shifted Cl without the Pb-Cl rule")
        except S2Error:
            pass
        miss = os.path.join(tmp, "no_such_pbcl.json")
        try:
            pbcl_value(miss, allow_provisional=True)
            raise AssertionError("missing Pb-Cl record accepted")
        except S2Error:
            pass
        rec = {"schema": "s2-pbcl-1", "source": {"level": "unverified"}, "d_PbCl_from_source_A": None,
               "decision": "provisional_2.837", "value_used_A": 2.837, "tag_for_shifted_starts": "[M] starting point",
               "allow_provisional_required": True, "date": "2026-11-03"}
        pth = os.path.join(tmp, "pbcl_prov.json"); json.dump(rec, open(pth, "w"))
        try:
            pbcl_value(pth, allow_provisional=False)
            raise AssertionError("provisional without the flag")
        except Refused:
            pass
        pb = pbcl_value(pth, allow_provisional=True)
        for j in POSE_SITES["Cl"]:
            st = pose_starts(cx.host, cx, "Cl", j, pbcl=pb)
            assert [x["name"] for x in st] == ["centred", "shift_a", "shift_b"]
            assert [x["tag"] for x in st] == [None, "[M] starting point", "[M] starting point"]
            pr, bh, bv = pair_record(cx.host, cx.vac, cx, "Cl", j, "p1", partners="unrelaxed", pbcl=pb)
            assert pr["status"] == "built" and pr["builder"]["provisional"] and pr["builder"]["pbcl"]["tag"] == \
                "[M] starting point"
            out.append(f"Cl@{j} 3 [M]")
        src = dict(rec, source={"level": "[S] primary verified"}, d_PbCl_from_source_A=2.8375,
                   decision="use_source_value", value_used_A=2.8375, allow_provisional_required=False)
        pth2 = os.path.join(tmp, "pbcl_src.json"); json.dump(src, open(pth2, "w"))
        pb2 = pbcl_value(pth2, allow_provisional=False)
        assert pb2["override"] == {"Cl:d_PbCl": 2.8375}
        for nm in ("shift_a", "shift_b"):
            bh, bv = build_pair(cx.host, cx.vac, cx, "Cl", 138, nm, partners="unrelaxed", pbcl=pb2)
            for b, base in ((bh, cx.host), (bv, cx.vac)):
                pt = b.atoms.positions[b.old_to_new[b.pose["pb_t_input"]]]
                vcl = find_mic(np.atleast_2d(b.atoms.positions[b.centre] - pt), base.cell.array, pbc=True)[0][0]
                vx = find_mic(np.atleast_2d(base.positions[b.site] - base.positions[b.pose["pb_t_input"]]),
                              base.cell.array, pbc=True)[0][0]
                assert abs(np.linalg.norm(vcl) - 2.8375) < 1e-9 and vcl @ vx > 0
                assert np.linalg.norm(np.cross(vcl, vx)) / (np.linalg.norm(vcl) * np.linalg.norm(vx)) < 1e-9
                assert b.report["valid"] and b.report["admissible"] and b.pose["start_override"] == {"Cl:d_PbCl": 2.8375}
        out.append("Cl override 2.8375 A collinear, V1-V10 valid")
        # the override path (from the centred Cl) at d = 2.837 A reproduces the s2b-2 shifted build on both legs
        for j in POSE_SITES["Cl"]:
            for nm in ("shift_a", "shift_b"):
                rh, rv = b42.build_paired(cx.host, cx.vac, VI, "Cl", j, nm, vpos=cx.vpos, mig="allow")
                c0h, c0v = b42.build_paired(cx.host, cx.vac, VI, "Cl", j, "centred", vpos=cx.vpos, mig="allow")
                for r_, c0, base in ((rh, c0h, cx.host), (rv, c0v, cx.vac)):
                    o = apply_pbcl_override(c0, base, PBCL_DEFAULT_A, cx.vpos, name=nm)
                    assert np.abs(o.atoms.positions - r_.atoms.positions).max() < 1e-12
                    assert np.array_equal(o.atoms.numbers, r_.atoms.numbers)
                    assert all(o.pose[k] == v for k, v in r_.pose.items()), (nm, j)
        pb3 = dict(pb2, d=3.4, override={"Cl:d_PbCl": 3.4})                  # synthetic: shifts barely move the Cl
        n_kept = len(pose_starts(cx.host, cx, "Cl", 175, pbcl=pb3))
        assert n_kept == 3
        out.append("override at 2.837 A == s2b-2 shift (1e-12 A, pose keys) at I138 and I175")
        for bad in (dict(src, value_used_A=2.837), dict(src, source={"level": "unverified"}),
                    dict(rec, decision="confirmed_2.837", source={"level": "[S] primary verified"},
                         d_PbCl_from_source_A=2.8375), dict(rec, date=None)):
            p3 = os.path.join(tmp, "pbcl_bad.json"); json.dump(bad, open(p3, "w"))
            try:
                pbcl_value(p3, allow_provisional=True)
                raise AssertionError(f"inconsistent Pb-Cl record accepted: {bad}")
            except S2Error:
                pass
        g1 = [build_host_leg(cx.host, cx, t, j) for t, j in G1_SITES.items()]
        assert all(b.report["valid"] and b.report["admissible"] for b in g1)
        assert g1[0].pose["replaced_migrating_iodide"] is True
        return "; ".join(out) + "; Pb-Cl record checks; G1 host-leg cells"

    def t_jobs():
        root = os.path.join(tmp, "node")
        Ly = Layout("node", root)
        base = {"campaign": "c1", "root": root, "member": "ref233", "calc": "mock-harmonic", "threads": 1}
        run_job(dict(base, action="relax-host", work_id="s2_ref233_host"))
        run_job(dict(base, action="region", site=136))
        run_job(dict(base, action="region", site=128))
        for j in (136, 128):
            run_job(dict(base, action="build-vac", site=j))
            wid = make_work_id("ref233", "V", L=sublattice_of(read(os.path.join(ROOT, REF_HOST)), j), j=j)
            run_job(dict(base, action="relax", work_id=wid))
        recs = []
        hrel = read_cell(Ly.cell_file("c1", "s2_ref233_host", "relaxed"))
        kept = pose_starts(hrel, ref_context(), "Cs", 128)
        nd = [x["n"] for x in kept if x["n"]][0]       # the first admissible displaced start on the relaxed host
        for T, j, n in (("Sr", 136, 0), ("Cs", 128, 0), ("Cs", 128, nd)):
            pr = run_job(dict(base, action="build-pair", token=T, site=j, start=f"p{n}", partners="relaxed"))
            assert pr["status"] == "built", pr["rejection"]
            for lg in ("novac", "vac"):
                rec = run_job(dict(base, action="relax", work_id=pr["legs"][lg]["work_id"]))
                recs.append(rec)
                v = run_job(dict(base, action="validate", work_id=pr["legs"][lg]["work_id"]))
                assert v["agrees_with_record"]
        assert all(r["validity"]["checks"]["4"]["passed"] for r in recs)
        d = run_job(dict(base, action="distinct", token="Cs", site=128, leg="vac"))
        assert d["kept"][0] == "p0" or not recs[3]["validity"]["valid"]
        hrec = load_record(Ly.record("c1", "s2_ref233_host"))
        assert "E_mace_eV" not in json.dumps(hrec) and "E_mace_eV" in json.dumps(
            load_record(Ly.record("c1", "s2_ref233_host"), blind=False))
        for fn in os.listdir(os.path.join(root, "work", "s2", "c1", "regions")):
            assert not hygiene_violations(open(os.path.join(root, "work", "s2", "c1", "regions", fn)).read())
        # section 11 final-geometry checks (validate-a2, I-F1) on the reference cells, the A1 relaxed cells standing in
        # for A2 final geometries: every kind passes; a far inorganic atom moved 0.30 A fails check 5; a job without
        # the partner's final geometry is refused (check 5 not evaluable, round-2 R2V-1); a final of other atoms is
        # refused
        va = dict(base, action="validate-a2", campaign="c2")
        cf = lambda w, k: Ly.cell_file("c1", w, k)
        hw, vw = "s2_ref233_host", "s2_ref233_VB136"
        dw, dvw = "s2_ref233_Sr136p0_novac", "s2_ref233_Sr136p0_vac"
        common = {"host_relaxed": cf(hw, "relaxed"), "region": Ly.region("c1", "ref233", "B", 136),
                  "pair": Ly.pair("c1", "ref233", "Sr", 136, 0)}
        outd = os.path.join(tmp, "a2v")
        rows = (("host", None, None, hw, None), ("V", None, None, vw, cf(hw, "relaxed")),
                ("D", "Sr", "novac", dw, cf(hw, "relaxed")), ("DV", "Sr", "vac", dvw, cf(vw, "relaxed")))
        got = {}
        for kind, T, lg, w, par in rows:
            o = run_job(dict(va, label=f"s2r_m30_{kind}", kind=kind, site=136, token=T, leg=lg, out=os.path.join(
                outd, f"{kind}.json"), files=dict(common, start=cf(w, "start"), final=cf(w, "relaxed"), parent_final=par)))
            got[kind] = o["validity"]
            assert o["validity"]["valid"], (kind, o["validity"]["failed"])
        assert got["host"]["failed"] == [] and got["host"]["checks"]["5"] is None and got["DV"]["checks"]["2"]["passed"]
        dv = read_cell(cf(dvw, "relaxed"))
        reg136 = load_record(common["region"])
        prl = load_record(common["pair"])["legs"]["vac"]
        free = free_in_cell(reg136, "DV", built=prl)
        c2h, _ = cell_maps("DV", built=prl, n_host=len(hrel))
        dh = dist_to(hrel, np.array(reg136["centres"]["site"]))
        far = [i for i in free if _syms(dv)[i] in HOST_INORGANIC and dh[c2h[i]] > PARTNER_CUT_A + 0.5][0]
        moved = dv.copy(); moved.positions[far] += np.array([0.30, 0.0, 0.0])
        mf = write_cell(os.path.join(outd, "dv_moved.extxyz"), moved)
        o = run_job(dict(va, label="s2r_m30_DVmoved", kind="DV", site=136, token="Sr", leg="vac",
                         out=os.path.join(outd, "moved.json"),
                         files=dict(common, start=cf(dvw, "start"), final=os.path.join(outd, "dv_moved.extxyz"),
                                    parent_final=cf(vw, "relaxed"))))
        assert o["validity"]["failed"] == [5] and abs(o["validity"]["checks"]["5"]["gated"]["max_dr_inorganic_A"] - 0.30) < 0.05
        for kind_np, T_np, lg_np, w_np in (("DV", "Sr", "vac", dvw), ("V", None, None, vw), ("D", "Sr", "novac", dw)):
            try:                                                   # round-2 R2V-1: no partner -> refused, never [5]
                run_job(dict(va, label=f"s2r_m30_{kind_np}noparent", kind=kind_np, site=136, token=T_np, leg=lg_np,
                             out=os.path.join(outd, f"nopar_{kind_np}.json"),
                             files=dict(common, start=cf(w_np, "start"), final=cf(w_np, "relaxed"), parent_final=None)))
                raise AssertionError(f"validate-a2 of kind {kind_np} without the partner's final geometry was run")
            except S2Error:
                assert not os.path.exists(os.path.join(outd, f"nopar_{kind_np}.json"))
        try:
            run_job(dict(va, label="s2r_m30_wrong", kind="D", site=136, token="Sr", leg="novac", out=os.path.join(
                outd, "wrong.json"), files=dict(common, start=cf(dw, "start"), final=cf(dvw, "relaxed"),
                                                parent_final=cf(hw, "relaxed"))))
            raise AssertionError("a final geometry of other atoms was accepted")
        except S2Error:
            pass
        del mf
        # guards: a mock never on a pool member; MACE never off the node root; derived keys must agree
        for bad in (dict(base, member="m30", action="relax-host", work_id="s2_m30_host"),
                    dict(base, calc="mace", action="relax-host", work_id="s2_ref233_host"),
                    dict(base, action="relax", work_id=recs[0]["work_id"], kind="DV"),
                    dict(base, action="build-pair", token="Cs", site=128, start="p0", pose="q0+"),
                    dict(base, action="build-pair", token="Cs", site=128, start="p0", region="regions/ref233_A92.json")):
            try:
                run_job(bad)
                raise AssertionError(f"job accepted: {bad['member']} {bad['calc']}")
            except S2Error:
                pass
        assert not os.path.exists(Ly.record("c1", "s2_m30_host"))
        return (f"mock pipeline on ref233: host, 2 regions, 2 V+, 3 pairs (6 cells), validate, distinct "
                f"{d['map']}; validate-a2 (host, V, D, D+V pass; far atom moved 0.30 A fails check 5; V, D, D+V "
                f"without the partner refused, no record; other atoms refused); MACE energies blinded; pool member "
                f"and off-node MACE refused")

    def t_hygiene():
        sl = "/"
        bad = [sl + "Users" + sl + "x", sl + "private" + sl + "var", sl + "home" + sl + "u", " " + sl + "tmp" + sl + "a",
               "scr" + "atch", "v" + "env", "10." + "0.0.1", "a" + chr(64) + "b.org", "i-" + "uf66abcdefgh12",
               "\u00a5", "US" + "D 5", "\u20ac", "5" + chr(36), "\u5143"]
        for t in bad:
            assert hygiene_violations(t), t
        for t in ("https" + ":" + "//example", "see materials.example" + ".edu", "pubs.example" + ".org/x"):
            assert hygiene_violations(t) and not hygiene_violations(t, kind="code"), t       # N-A15: JSON only
        assert not hygiene_violations("doi 10.1063/1.453467; scripts/46_s2_cells.py; results/fa_host/x.extxyz")
        assert hygiene_violations("x" + chr(36) + "y")                   # json: any dollar
        assert not hygiene_violations("PY=" + chr(36) + "PY_BIN", kind="code")      # a shell variable (N-A5)
        assert hygiene_violations("cost 5" + chr(36), kind="code")
        ok = ["/data/work/s2", "/data/jobs/s2c1", "/usr/local/bin/run_qe.sh", "/data/pseudo", "0.3.16", "2.837"]
        for t in ok:
            assert not hygiene_violations(t), (t, hygiene_violations(t))
        own = open(os.path.abspath(__file__)).read()
        assert not hygiene_violations(own, kind="code"), hygiene_violations(own, kind="code")
        try:
            dump_public({"p": sl + "Users" + sl + "x"}, os.path.join(tmp, "h.json"))
            raise AssertionError("dump_public wrote a local path")
        except S2Error:
            assert not os.path.exists(os.path.join(tmp, "h.json"))
        L1, L2 = Layout("node"), Layout("archive", "results/objective2/s2")
        assert L1.sp_out("c1", "s2_m30_host") == "/data/jobs/s2c1/s2_m30_host/s2_m30_host.out"
        assert L1.record("c3", "s2_m06_host") == "/data/work/s2/c3/cells/s2_m06_host/record.json"
        assert L2.record("c1", "s2_m30_host") == "results/objective2/s2/c1/records/s2_m30_host.json"
        assert L2.sp_out("c1", "s2_m30_host") == "results/objective2/s2/c1/raw/s2_m30_host.out.gz"
        return "each forbidden pattern caught, node paths pass, this script is clean, dump_public refuses; layout"

    def t_model():
        p = foundation_path()
        assert os.path.basename(p) == FOUNDATION_FILE and os.path.join("mace", FOUNDATION_FILE) in p
        chk = foundation_check(os.path.join(tmp, "absent_model"))
        assert not chk["passed"] and chk["file"] == "absent_model"
        return f"foundation path resolved by hand ({FOUNDATION_FILE}); load_mace not called"

    for name, fn in (("constants", t_constants), ("sites-14-hosts", t_sites), ("m05-census", t_census),
                     ("regions-transfer", t_regions), ("labels", t_labels), ("validity-checks", t_validity),
                     ("validity-table", t_validity_wrap), ("distinct-minima", t_distinct),
                     ("relax-frozen-mock", t_relax), ("pose-starts", t_poses), ("jobs-mock", t_jobs),
                     ("hygiene-layout", t_hygiene), ("model-loader", t_model)):
        case(name, fn)
    print("NOTES (interpretations, implementation notes, conflicts implemented here):")
    for k, v in NOTES.items():
        print(f"  {k}: {v}")
    case("no-model", lambda: no_model() and "'mace' not in sys.modules")
    nf = sum(not ok for _, ok in results)
    print(f"SELF-TEST {'PASS' if not nf else 'FAIL'} ({len(results)} cases, {nf} failed, {time.time() - t0:.0f} s)")
    return 1 if nf else 0


if __name__ == "__main__":
    sys.exit(main())

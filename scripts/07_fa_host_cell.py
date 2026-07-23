#!/usr/bin/env python3
"""Lane 2 / W2-1 — FA0.95Cs0.05PbI3 host cell building (EXPLORATORY / QUARANTINED).

Builds the black alpha (pseudo-cubic) formamidinium-lead-iodide host for the
Objective 1B production-host exploration:

  1. formamidinium cation FA+ = [CH(NH2)2]+ (CH5N2, 8 atoms), planar sp2 C;
  2. 12-atom pseudo-cubic FAPbI3 parent (1 FA + 1 Pb + 3 I), a ~ 6.35 A;
  3. MACE-MP-0 relaxation of the parent (zero-shot, CPU ok for 12 atoms);
  4. det=20 supercell enumeration: enumerate integer transformation matrices with
     |det| = 20, score by deviation-from-cubic (ASE find_optimal_cell_shape /
     get_deviation_from_optimal_cell_shape), pick the most isotropic — NOT a
     default 2x2x5. Record candidate scores + matrices + element-count asserts;
  5. build FA19Cs1Pb20I60 = 233 atoms (5% Cs on the A-site), and the V_I-carved
     232-atom cell.

EXPLORATORY discipline (EXECUTION_GUIDE Part 3): every output is tagged
exploratory; MACE here is zero-shot and charge-agnostic, so it only seeds
structures — no barrier/dynamics claims. The FA orientation ensemble (W2-2, MD)
and the zero-shot FA NEB baseline distribution (W2-3) need the GPU and are
deferred while the 5090 is unavailable.

Usage:
  python scripts/07_fa_host_cell.py --outdir results/fa_host --device cpu
"""
import argparse
import json
from pathlib import Path

import numpy as np
from ase import Atoms
from ase.build import find_optimal_cell_shape, get_deviation_from_optimal_cell_shape
from ase.io import read, write

ROOT = Path(__file__).resolve().parent.parent

# alpha-FAPbI3 pseudo-cubic lattice parameter (experimental ~6.35 A; Weller 2015)
A_PSEUDOCUBIC = 6.35


def make_formamidinium(center=(0, 0, 0), rot=None):
    """Planar formamidinium cation [CH(NH2)2]+ (8 atoms: C H5 N2).

    Central sp2 C bonded to one H and two N (N-C-N ~120 deg); each N carries two
    H. Bond lengths: C-N 1.33, C-H 1.09, N-H 1.01 A. Built in the xy-plane, then
    optionally rotated (3x3) and translated to `center`.
    """
    dCN, dCH, dNH = 1.33, 1.09, 1.01
    syms = ["C"]
    pos = [np.array([0.0, 0.0, 0.0])]
    # C bonds at 120 deg: H_c up (+y), N1 at 210 deg, N2 at 330 deg
    ang_Hc = 90.0
    ang_N = [210.0, 330.0]
    # H on central C
    th = np.deg2rad(ang_Hc)
    syms.append("H"); pos.append(dCH * np.array([np.cos(th), np.sin(th), 0.0]))
    for aN in ang_N:
        th = np.deg2rad(aN)
        uN = np.array([np.cos(th), np.sin(th), 0.0])
        N = dCN * uN
        syms.append("N"); pos.append(N)
        back = -uN                       # N->C direction
        for sgn in (+1, -1):             # two H per N at +/-120 deg from N->C, in-plane
            a = np.deg2rad(120 * sgn)
            R = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
            uH = R @ back
            syms.append("H"); pos.append(N + dNH * uH)
    pos = np.array(pos)
    if rot is not None:
        pos = pos @ np.asarray(rot).T
    pos = pos + np.asarray(center, float)
    return syms, pos


def make_parent(a=A_PSEUDOCUBIC, fa_rot=None):
    """12-atom pseudo-cubic FAPbI3: Pb at origin, I at edge midpoints, FA at body
    centre (the A-site). Cell is cubic a x a x a."""
    cell = np.eye(3) * a
    syms = ["Pb"]
    pos = [np.array([0.0, 0.0, 0.0])]
    # iodine at the three Pb-I-Pb edge midpoints
    for shift in ([0.5, 0, 0], [0, 0.5, 0], [0, 0, 0.5]):
        syms.append("I"); pos.append(np.array(shift) * a)
    atoms = Atoms(syms, positions=pos, cell=cell, pbc=True)
    # FA cation, C placed at the A-site (body centre); default flat orientation,
    # tilted slightly so it is not artificially aligned to a mirror plane
    if fa_rot is None:
        from numpy import cos, sin, deg2rad
        t = deg2rad(35.0)
        fa_rot = np.array([[cos(t), -sin(t), 0], [sin(t), cos(t), 0], [0, 0, 1]])
    fsyms, fpos = make_formamidinium(center=np.array([0.5, 0.5, 0.5]) * a, rot=fa_rot)
    atoms += Atoms(fsyms, positions=fpos)
    return atoms


def relax_mace(atoms, device="cpu", fmax=0.05, steps=300, model="medium"):
    from mace.calculators import mace_mp
    from ase.optimize import FIRE
    from ase.filters import FrechetCellFilter
    atoms = atoms.copy()
    atoms.calc = mace_mp(model=model, device=device, default_dtype="float64", dispersion=False)
    e0 = atoms.get_potential_energy()
    # relax cell + positions (parent lattice parameter is a guess)
    dyn = FIRE(FrechetCellFilter(atoms), logfile=None)
    conv = dyn.run(fmax=fmax, steps=steps)
    e1 = atoms.get_potential_energy()
    return atoms, {"E_initial_eV": float(e0), "E_relaxed_eV": float(e1),
                   "converged": bool(conv), "fmax": fmax}


def _shortest_lattice_vector(L, rng=3):
    """Shortest nonzero lattice vector of the lattice whose rows are L (Å).
    For a supercell holding exactly ONE point defect (and one Cs), this equals
    the nearest periodic-image distance == the Cs-Cs distance == the V_I-V_I
    distance == the defect-isolation radius. This, NOT cell-vector-length
    isotropy, is the quantity that controls defect self-interaction."""
    best = 1e9
    for m in np.ndindex(*(2 * rng + 1,) * 3):
        n = np.array(m) - rng
        if not n.any():
            continue
        best = min(best, float(np.linalg.norm(n @ L)))
    return best


def _cell_lengths_angles(L):
    lens = np.linalg.norm(L, axis=1)
    ang = []
    for i, j in [(1, 2), (0, 2), (0, 1)]:
        c = np.dot(L[i], L[j]) / (lens[i] * lens[j])
        ang.append(float(np.degrees(np.arccos(np.clip(c, -1, 1)))))
    return lens.tolist(), ang


def _hnf_det(n):
    """Every distinct index-n sublattice once, as upper-triangular HNF matrices."""
    mats = []
    for a in range(1, n + 1):
        if n % a:
            continue
        for c in range(1, n // a + 1):
            if (n // a) % c:
                continue
            f = n // (a * c)
            for b in range(c):
                for d in range(f):
                    for e in range(f):
                        mats.append(np.array([[a, b, d], [0, c, e], [0, 0, f]]))
    return mats


def enumerate_det20(parent_cell, target_size=20, topk=8):
    """Enumerate ALL index-20 sublattices (HNF) and rank by defect isolation.

    Primary score: d_min = shortest periodic lattice vector = nearest image /
    Cs-Cs / V_I-V_I distance (maximise -> defect least self-interacting). We keep
    the ASE find_optimal_cell_shape 'sc'/'fcc' cells too, and the naive 2x2x5 slab
    for contrast, so the record shows why a near-isotropic cell wins. The chosen
    cell maximises d_min while staying isotropic in cell-vector length (a cell that
    buys 0.1 A of d_min by stretching one axis to 35 A is rejected)."""
    ref = []
    # ASE optimal-shape references (may be non-triangular; that's fine)
    for shape in ("sc", "fcc"):
        P = np.array(find_optimal_cell_shape(parent_cell, target_size, shape), dtype=int)
        ref.append((f"optimal_{shape}", P))
    ref.append(("naive_2x2x5", np.diag([2, 2, 5])))
    ref.append(("naive_1x4x5", np.diag([1, 4, 5])))

    def describe(label, P):
        L = np.dot(P, parent_cell)
        lens, ang = _cell_lengths_angles(L)
        return {"label": label, "P": P.tolist(), "det": int(round(abs(np.linalg.det(P)))),
                "lengths_A": [round(x, 3) for x in lens], "angles_deg": [round(x, 2) for x in ang],
                "aniso": round(max(lens) / min(lens), 3),
                "d_min_A": round(_shortest_lattice_vector(L), 3)}

    # full HNF sweep, ranked by d_min then isotropy
    hnf = [describe(f"hnf_{i}", P) for i, P in enumerate(_hnf_det(target_size))]
    hnf.sort(key=lambda c: (-c["d_min_A"], c["aniso"], np.mean([abs(a - 90) for a in c["angles_deg"]])))
    best_hnf = hnf[0]
    best_hnf = dict(best_hnf, label="best_isolation")

    refs = [describe(lbl, P) for lbl, P in ref]
    # Selection pool = HNF sweep + ASE optimal-shape references. The ASE
    # find_optimal_cell_shape cells are generally NON-triangular (rotated/mixed
    # basis) and so are NOT in the upper-triangular HNF list, yet they are often
    # the most isotropic index-20 cells — so they must be eligible for 'chosen'.
    pool = hnf + [c for c in refs if not c["label"].startswith("naive")]
    # chosen = the MOST ISOTROPIC cell (lowest cell-vector anisotropy) whose defect
    # isolation d_min is within 1.0 A of the global maximum. For defect/NEB work an
    # isotropic cell (no short axis -> no strong vacancy-image interaction along one
    # direction) is worth more than the last ~0.1 A of d_min: a cell that buys extra
    # d_min by stretching one axis to 35 A is explicitly rejected here.
    dmax = max(c["d_min_A"] for c in pool)
    isotropic_top = sorted([c for c in pool if c["d_min_A"] >= dmax - 1.0],
                           key=lambda c: (c["aniso"], -c["d_min_A"],
                                          np.mean([abs(a - 90) for a in c["angles_deg"]])))
    chosen = dict(isotropic_top[0], label="chosen")
    # candidate table for the record: chosen + best_isolation + refs (dedup by P)
    table, seen = [], set()
    for c in [chosen, best_hnf] + refs:
        key = tuple(map(tuple, c["P"]))
        if key not in seen:
            seen.add(key); table.append(c)
    return chosen, table


def _random_rotation(rng):
    """Uniformly random 3x3 rotation matrix (Shoemake quaternion method)."""
    u1, u2, u3 = rng.random(3)
    q = np.array([np.sqrt(1 - u1) * np.sin(2 * np.pi * u2),
                  np.sqrt(1 - u1) * np.cos(2 * np.pi * u2),
                  np.sqrt(u1) * np.sin(2 * np.pi * u3),
                  np.sqrt(u1) * np.cos(2 * np.pi * u3)])
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def randomize_fa_orientations(atoms, seed=0):
    """Rotate each FA cation about its own C by an independent random rotation.
    Breaks the artificial dipole order of the as-built (all-identical-orientation)
    cell. Operates in place on a copy; returns the new Atoms. FA grouping is by
    proximity to each C (same logic as the Cs substitution)."""
    rng = np.random.default_rng(seed)
    at = atoms.copy()
    sym = np.array(at.get_chemical_symbols())
    c_idx = np.flatnonzero(sym == "C")
    n_all = np.flatnonzero(sym == "N")
    h_all = np.flatnonzero(sym == "H")
    for c in c_idx:
        nn = n_all[np.argsort(at.get_distances(c, n_all, mic=True))[:2]]
        mol = [int(c)] + [int(x) for x in nn]
        hC = h_all[np.argsort(at.get_distances(int(c), h_all, mic=True))[0]]
        mol.append(int(hC))
        for N in nn:
            hN = h_all[np.argsort(at.get_distances(int(N), h_all, mic=True))[:2]]
            mol += [int(x) for x in hN]
        mol = sorted(set(mol))
        if len(mol) != 8:
            continue
        R = _random_rotation(rng)
        cpos = at.positions[c].copy()
        # rotate the whole molecule rigidly about its C (use MIC vectors so a
        # molecule wrapped across the boundary stays intact)
        for a in mol:
            v = at.get_distance(int(c), int(a), mic=True, vector=True)
            at.positions[a] = cpos + R @ v
    at.wrap()
    return at


def build_supercell(parent, P, n_cs=1):
    """Make the det=20 supercell from parent (all-FA), then substitute n_cs FA -> Cs.

    Cs goes on the A-site FA whose C is closest to the supercell centre (a defined,
    reproducible pick). Returns the 233-atom FA19Cs1Pb20I60 cell.
    """
    from ase.build import make_supercell
    sc = make_supercell(parent, np.array(P))
    sym = np.array(sc.get_chemical_symbols())
    n_pb = int((sym == "Pb").sum())
    assert n_pb == 20, f"expected 20 Pb, got {n_pb}"
    # identify FA molecules by their C atoms
    c_idx = np.flatnonzero(sym == "C")
    assert len(c_idx) == 20, f"expected 20 FA (C atoms), got {len(c_idx)}"
    centre = sc.cell.array.sum(0) / 2
    order = c_idx[np.argsort(np.linalg.norm(sc.positions[c_idx] - centre, axis=1))]
    cs_carbons = list(order[:n_cs])

    # For each Cs-designated FA, delete its 8 atoms (C + attached H/N) and place a Cs
    # at the C position. Group the molecule by proximity to its C.
    to_delete = []
    cs_positions = []
    for catom in cs_carbons:
        cpos = sc.positions[catom]
        # a FA is C + 2N + 5H within ~2.6 A path; collect the nearest N/H cluster
        mol = [int(catom)]
        n_all = np.flatnonzero(sym == "N")
        h_all = np.flatnonzero(sym == "H")
        # 2 nearest N to this C
        nn = n_all[np.argsort(sc.get_distances(catom, n_all, mic=True))[:2]]
        mol += [int(x) for x in nn]
        # 1 H on C (nearest H to C) + 2 H on each N (nearest H to each N)
        hC = h_all[np.argsort(sc.get_distances(catom, h_all, mic=True))[0]]
        mol.append(int(hC))
        for N in nn:
            hN = h_all[np.argsort(sc.get_distances(int(N), h_all, mic=True))[:2]]
            mol += [int(x) for x in hN]
        mol = sorted(set(mol))
        assert len(mol) == 8, f"FA molecule grouping got {len(mol)} atoms, expected 8"
        to_delete += mol
        cs_positions.append(cpos.copy())

    keep = [i for i in range(len(sc)) if i not in set(to_delete)]
    new = sc[keep]
    for cpos in cs_positions:
        new += Atoms("Cs", positions=[cpos])
    return new


def element_counts(atoms):
    from collections import Counter
    return dict(Counter(atoms.get_chemical_symbols()))


def check_pb_coordination(atoms, cutoff=3.7):
    """Minimum-image Pb-I coordination for every Pb. Returns (list of CN, all_six).
    A perovskite framework has every Pb 6-fold; boundary octahedra look 'cut' in a
    single-cell render but MIC counting is the real test."""
    sym = np.array(atoms.get_chemical_symbols())
    pb = np.flatnonzero(sym == "Pb")
    ii = np.flatnonzero(sym == "I")
    cns = [int((atoms.get_distances(int(p), ii, mic=True) < cutoff).sum()) for p in pb]
    return cns, all(cn == 6 for cn in cns)


def relax_supercell(atoms, device="cpu", fmax=0.05, steps=400, model="medium", relax_cell=False):
    """Relax atomic positions (and optionally the cell) with zero-shot MACE.
    relax_cell=False -> positions only at fixed (parent-derived) cell = fixed-lattice
    mode; relax_cell=True -> zero-pressure cell+positions."""
    from mace.calculators import mace_mp
    from ase.optimize import FIRE
    at = atoms.copy()
    at.calc = mace_mp(model=model, device=device, default_dtype="float64", dispersion=False)
    e0 = at.get_potential_energy()
    if relax_cell:
        from ase.filters import FrechetCellFilter
        dyn = FIRE(FrechetCellFilter(at), logfile=None)
    else:
        dyn = FIRE(at, logfile=None)
    conv = dyn.run(fmax=fmax, steps=steps)
    return at, {"E_initial_eV": float(e0), "E_relaxed_eV": float(at.get_potential_energy()),
                "converged": bool(conv), "relax_cell": relax_cell, "fmax": fmax}


def carve_vacancy(atoms):
    """Remove one iodine nearest the cell centre -> the 232-atom V_I cell."""
    sym = np.array(atoms.get_chemical_symbols())
    i_idx = np.flatnonzero(sym == "I")
    centre = atoms.cell.array.sum(0) / 2
    vac = i_idx[np.argmin(np.linalg.norm(atoms.positions[i_idx] - centre, axis=1))]
    out = atoms.copy()
    del out[int(vac)]
    return out, int(vac)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--outdir", default=str(ROOT / "results" / "fa_host"))
    p.add_argument("--device", default="cpu")
    p.add_argument("--no-relax", action="store_true")
    p.add_argument("--n-orient", type=int, default=8, help="FA orientation ensemble size")
    p.add_argument("--relax-cell", action="store_true",
                   help="relax supercell cell too (zero-pressure); default fixed lattice")
    args = p.parse_args()
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)

    record = {"tag": "EXPLORATORY / QUARANTINED — Lane 2 W2-1",
              "note": ("zero-shot MACE; structures only, no barrier/dynamics claims. "
                       "The Cs cell is a PERIODIC 5% Cs substitution model, NOT a random "
                       "alloy or SQS — one Cs repeats through the periodic boundary."),
              "a_pseudocubic_guess_A": A_PSEUDOCUBIC,
              "model_label": "periodic 5% Cs substitution model (FA0.95Cs0.05PbI3 composition)"}

    # 1-2. parent
    parent = make_parent()
    write(outdir / "fa_parent_unrelaxed.extxyz", parent)
    record["parent_formula"] = parent.get_chemical_formula()
    record["parent_natoms"] = len(parent)
    assert len(parent) == 12, f"parent should be 12 atoms, got {len(parent)}"

    # 3. relax parent
    if not args.no_relax:
        relaxed, relax_meta = relax_mace(parent, device=args.device)
        write(outdir / "fa_parent_relaxed.extxyz", relaxed)
        record["parent_relax"] = relax_meta
        record["parent_cell_relaxed_A"] = relaxed.cell.lengths().tolist()
        record["parent_cell_angles_relaxed"] = relaxed.cell.angles().tolist()
        parent_for_sc = relaxed
    else:
        parent_for_sc = parent

    # 4. det=20 enumeration — full HNF sweep ranked by defect isolation (d_min)
    chosen, table = enumerate_det20(parent_for_sc.cell.array, target_size=20)
    record["det20_table"] = table
    record["det20_chosen"] = chosen
    print("det=20 candidates (d_min = nearest-image / Cs-Cs / V_I-V_I distance):")
    print("  label            d_min  aniso  lengths(A)            angles(deg)")
    for c in table:
        print(f"  {c['label']:16s} {c['d_min_A']:5.2f}  {c['aniso']:.2f}   "
              f"{c['lengths_A']}  {c['angles_deg']}")

    # 5. build pristine supercell (as-built = ordered FA); assert stoichiometry
    sc0 = build_supercell(parent_for_sc, chosen["P"], n_cs=1)
    ec = element_counts(sc0)
    assert ec.get("Pb") == 20 and ec.get("I") == 60 and ec.get("Cs") == 1, f"stoich fail: {ec}"
    assert ec.get("C") == 19 and ec.get("N") == 38 and ec.get("H") == 95, f"FA count fail: {ec}"
    assert len(sc0) == 233, f"expected 233 atoms, got {len(sc0)}"
    record["supercell_P"] = chosen["P"]
    record["supercell_formula"] = sc0.get_chemical_formula()
    record["supercell_natoms"] = len(sc0)
    record["supercell_elements"] = ec

    # supercell geometry + Cs-Cs distance (== d_min for 1 Cs/cell)
    lens, ang = _cell_lengths_angles(sc0.cell.array)
    record["supercell_lengths_A"] = [round(x, 3) for x in lens]
    record["supercell_angles_deg"] = [round(x, 2) for x in ang]
    record["cs_cs_min_distance_A"] = round(_shortest_lattice_vector(sc0.cell.array), 3)

    # 6. FA orientation ensemble — sample N independent random-orientation sets,
    # relax each, report the energy spread (breaks artificial dipole order).
    ensemble = []
    if not args.no_relax:
        print(f"\nFA orientation ensemble (n={args.n_orient}, relax_cell={args.relax_cell}):")
        for k in range(args.n_orient):
            sck = randomize_fa_orientations(sc0, seed=k) if k > 0 else sc0.copy()
            rlx, meta = relax_supercell(sck, device=args.device, relax_cell=args.relax_cell)
            cns, all6 = check_pb_coordination(rlx)
            cn_p, nh_p = None, None
            fa_ok = _fa_intact(rlx)
            entry = {"seed": k, "orientation": "as_built" if k == 0 else f"random_{k}",
                     "E_relaxed_eV": meta["E_relaxed_eV"], "converged": meta["converged"],
                     "pb_all_6fold": all6, "pb_cn_min": min(cns), "pb_cn_max": max(cns),
                     "fa_intact": fa_ok}
            write(outdir / f"fa_ensemble_{k:02d}.extxyz", rlx)
            ensemble.append(entry)
            print(f"  seed {k:2d} ({entry['orientation']:10s}) E={meta['E_relaxed_eV']:.3f} eV "
                  f"conv={meta['converged']} Pb6={all6} FA_ok={fa_ok}")
        Es = np.array([e["E_relaxed_eV"] for e in ensemble])
        rel = (Es - Es.min()) * 1000  # meV above lowest
        for e, r in zip(ensemble, rel):
            e["dE_above_min_meV"] = float(r)
        record["fa_ensemble"] = ensemble
        record["fa_ensemble_summary"] = {
            "n": len(ensemble), "E_spread_meV": float((Es.max() - Es.min()) * 1000),
            "E_min_eV": float(Es.min()), "lowest_seed": int(Es.argmin()),
            "all_pb_6fold": bool(all(e["pb_all_6fold"] for e in ensemble)),
            "all_fa_intact": bool(all(e["fa_intact"] for e in ensemble))}
        print(f"  -> ensemble energy spread {(Es.max()-Es.min())*1000:.1f} meV; "
              f"lowest = seed {int(Es.argmin())}")
        # the production pristine cell = lowest-energy orientation
        best_cell = read(str(outdir / f"fa_ensemble_{int(Es.argmin()):02d}.extxyz"))
    else:
        best_cell = sc0
        record["fa_ensemble"] = "skipped (--no-relax)"
    write(outdir / "fa19cs1_pb20i60_233.extxyz", best_cell)

    # 7. carve V_I from the production (lowest-E) cell -> FA19CsPb20I59, 232 atoms
    vac_cell, vac_idx = carve_vacancy(best_cell)
    write(outdir / "fa19cspb20i59_232_vI.extxyz", vac_cell)
    ecv = element_counts(vac_cell)
    record["vacancy_cell_formula"] = vac_cell.get_chemical_formula()
    record["vacancy_cell_natoms"] = len(vac_cell)
    record["vacancy_removed_I_index"] = vac_idx
    record["vacancy_elements"] = ecv
    assert len(vac_cell) == 232 and ecv.get("I") == 59, f"vacancy cell fail: {len(vac_cell)}, {ecv}"

    # final coordination audit on the production pristine cell
    cns, all6 = check_pb_coordination(best_cell)
    from collections import Counter
    record["production_pb_coordination"] = dict(Counter(cns))
    record["production_all_pb_6fold"] = all6

    json.dump(record, open(outdir / "fa_host_build.json", "w"), indent=2)
    print(f"\n[fa_host] pristine {record['supercell_formula']} (233) -> "
          f"V_I {record['vacancy_cell_formula']} (232)")
    print(f"[fa_host] chosen P={chosen['P']}  d_min(Cs-Cs)={record['cs_cs_min_distance_A']} A  "
          f"all Pb 6-fold={all6}")
    print(f"[fa_host] cell {record['supercell_lengths_A']} A  {record['supercell_angles_deg']} deg")


def _fa_intact(atoms):
    """True if every FA has C-N in [1.25,1.45] and N-H in [0.95,1.15] (no dissociation)."""
    sym = np.array(atoms.get_chemical_symbols())
    ci = np.flatnonzero(sym == "C"); ni = np.flatnonzero(sym == "N"); hi = np.flatnonzero(sym == "H")
    if len(ci) == 0:
        return True
    for c in ci:
        cn = sorted(atoms.get_distances(int(c), ni, mic=True))[:2]
        if not all(1.25 <= x <= 1.45 for x in cn):
            return False
    for n in ni:
        nh = sorted(atoms.get_distances(int(n), hi, mic=True))[:2]
        if not all(0.95 <= x <= 1.15 for x in nh):
            return False
    return True


if __name__ == "__main__":
    main()

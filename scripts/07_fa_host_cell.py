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
from ase.io import write

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


def enumerate_det20(parent_cell, target_size=20, topk=8):
    """Enumerate near-cubic det=20 supercells. Uses ASE find_optimal_cell_shape
    for the best simple-cubic and body/face-centred targets, and records the
    deviation score of each, plus a couple of obvious 'naive' choices (2x2x5,
    1x4x5) for contrast."""
    cands = []
    for shape in ("sc", "fcc"):
        P = find_optimal_cell_shape(parent_cell, target_size, shape)
        P = np.array(P, dtype=int)
        dev = float(get_deviation_from_optimal_cell_shape(np.dot(P, parent_cell), shape))
        cands.append({"label": f"optimal_{shape}", "P": P.tolist(),
                      "det": int(round(np.linalg.det(P))), "target_shape": shape,
                      "deviation": dev})
    # naive diagonal choices for contrast (scored against 'sc')
    for diag, name in ([(2, 2, 5), "naive_2x2x5"], [(1, 4, 5), "naive_1x4x5"],
                       [(2, 2, 5), None]):
        if name is None:
            continue
        P = np.diag(diag).astype(int)
        dev = float(get_deviation_from_optimal_cell_shape(np.dot(P, parent_cell), "sc"))
        cands.append({"label": name, "P": P.tolist(), "det": int(np.prod(diag)),
                      "target_shape": "sc", "deviation": dev})
    # dedupe by P, sort by deviation (lower = more cubic)
    seen, uniq = set(), []
    for c in sorted(cands, key=lambda x: x["deviation"]):
        key = tuple(map(tuple, c["P"]))
        if key not in seen:
            seen.add(key); uniq.append(c)
    return uniq[:topk]


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
    args = p.parse_args()
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)

    record = {"tag": "EXPLORATORY / QUARANTINED — Lane 2 W2-1",
              "note": "zero-shot MACE; structures only, no barrier/dynamics claims",
              "a_pseudocubic_guess_A": A_PSEUDOCUBIC}

    # 1-2. parent
    parent = make_parent()
    write(outdir / "fa_parent_unrelaxed.extxyz", parent)
    record["parent_formula"] = parent.get_chemical_formula()
    record["parent_natoms"] = len(parent)
    record["parent_elements"] = element_counts(parent)
    assert len(parent) == 12, f"parent should be 12 atoms, got {len(parent)}"

    # 3. relax
    if not args.no_relax:
        relaxed, relax_meta = relax_mace(parent, device=args.device)
        write(outdir / "fa_parent_relaxed.extxyz", relaxed)
        record["relax"] = relax_meta
        record["parent_cell_relaxed_A"] = relaxed.cell.lengths().tolist()
        record["parent_cell_angles_relaxed"] = relaxed.cell.angles().tolist()
        parent_for_sc = relaxed
    else:
        parent_for_sc = parent

    # 4. det=20 enumeration
    cands = enumerate_det20(parent_for_sc.cell.array, target_size=20)
    record["det20_candidates"] = cands
    best = cands[0]
    record["det20_chosen"] = best
    print("det=20 candidates (deviation, lower=more cubic):")
    for c in cands:
        print(f"  {c['label']:14s} det={c['det']} dev={c['deviation']:.4f}  P={c['P']}")

    # 5. build FA19Cs1Pb20I60 + carve V_I
    sc = build_supercell(parent_for_sc, best["P"], n_cs=1)
    write(outdir / "fa19cs1_pb20i60_233.extxyz", sc)
    record["supercell_P"] = best["P"]
    record["supercell_formula"] = sc.get_chemical_formula()
    record["supercell_natoms"] = len(sc)
    record["supercell_elements"] = element_counts(sc)
    # element-count asserts: 20 Pb, 60 I, 1 Cs, 19 FA -> C19 H95 N38
    ec = element_counts(sc)
    assert ec.get("Pb") == 20 and ec.get("I") == 60 and ec.get("Cs") == 1, f"stoich fail: {ec}"
    assert ec.get("C") == 19 and ec.get("N") == 38 and ec.get("H") == 95, f"FA count fail: {ec}"
    assert len(sc) == 233, f"expected 233 atoms, got {len(sc)}"

    vac_cell, vac_idx = carve_vacancy(sc)
    write(outdir / "fa19cs1_pb20i60_232_vI.extxyz", vac_cell)
    record["vacancy_cell_natoms"] = len(vac_cell)
    record["vacancy_removed_I_index"] = vac_idx
    assert len(vac_cell) == 232

    json.dump(record, open(outdir / "fa_host_build.json", "w"), indent=2)
    print(f"\n[fa_host] parent {record['parent_formula']} -> supercell "
          f"{record['supercell_formula']} ({len(sc)} atoms) -> V_I {len(vac_cell)}")
    print(f"[fa_host] chosen P={best['P']} (dev={best['deviation']:.4f}) -> {outdir}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Where does a WP2e DFT relaxation put its energy? (PLAN amendment k item 2)

Reads a pw.x relax trajectory started from a MACE band image and reports, against the starting
(MACE) geometry:
  * per-atom displacement |dr| (minimum image, net translation removed) binned by the distance to
    the nearer defect centre (vacancy site, dopant), and the share of sum |dr|^2 beyond --rcut;
  * the rotation of every FA C->N-midpoint axis, and the rigid-body (Kabsch) rotation of every FA/GA
    C-N skeleton, versus its distance to the defects (molecules found by bonding: C, its N within
    1.6 A, the H within 1.25 A of either; 8 atoms for FA, 10 for GA);
  * the energy trajectory.
It also writes two "partition" structures and their QE single-point inputs (scripts/30):
    near_only : atoms within --rcut of a defect at their relaxed positions, the rest at MACE positions
    far_only  : the reverse
so that F(near_only) - F(start) and F(far_only) - F(start) show which region carries the
relaxation energy (the two need not add up to the total; the coupling is reported as the rest).
Outcome for m30 GA (2026-10-28): both partitions cost +4.5 to +5.3 eV, because a cut by atom
splits FA molecules whose C and H fall on different sides (N-H stretched to 1.48 A, max force
9.5 eV/A); the partition energies measure the torn bonds, not the regions, and are not used.

Energy attribution that has no boundary term (added 2026-10-28, after the partition result;
post hoc): the work done on each atom along the actual BFGS path,
    W_i = - sum_k 1/2 (F_i^k + F_i^(k+1)) . (r_i^(k+1) - r_i^k)        (trapezoid rule)
sums to E(final) - E(start) up to the discretisation error, which is reported (closure). The
attribution is path-dependent and assigns each interaction to the atoms on which its force acts;
it is reported per distance shell, per region (FA/GA molecules assigned by their C), for the
first 10 BFGS steps and for the rest. (Until 2026-10-28 the molecules came from scripts/22
fa_molecule, which takes 2 N and so left one N and one H of the GA with their own distance; both
lie in the 0-4 A shell, so no shell or region total changed when this was fixed.)

    python scripts/38_wp2e_displacement.py --relax relax_m30_GA_img0.out --host 30 --system GA \
        --bands <band dir> --out <dir> [--jobs /data/jobs/wp2e_part]
"""
import argparse, csv, json, os, importlib.util
import numpy as np
from ase.io import read, write
from ase.geometry import find_mic

HERE = os.path.dirname(os.path.abspath(__file__))
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def centres(at, system, vpos):
    """Vacancy site and, for doped cells, the dopant position (GA carbon with 3 N; the Sr atom)."""
    s = np.array(at.get_chemical_symbols()); cell = at.cell.array
    out = {"vacancy": vpos}
    if system == "Sr":
        out["dopant"] = at.positions[int(np.flatnonzero(s == "Sr")[0])]
    elif system == "GA":
        N = np.flatnonzero(s == "N")
        for c in np.flatnonzero(s == "C"):
            if (find_mic(at.positions[N] - at.positions[c], cell, pbc=True)[1] < 1.6).sum() == 3:
                out["dopant"] = at.positions[c]
    return out


def molecule(at, c, sym, cell):
    """Atoms of the organic cation whose carbon is c, by bonding: N < 1.6 A from C, H < 1.25 A from C or N."""
    near = lambda i, idx, r: idx[find_mic(at.positions[idx] - at.positions[i], cell, pbc=True)[1] < r]
    ns = near(c, np.flatnonzero(sym == "N"), 1.6)
    hs = np.unique(np.concatenate([near(x, np.flatnonzero(sym == "H"), 1.25) for x in np.r_[c, ns]]))
    mol = sorted([int(c)] + [int(x) for x in ns] + [int(x) for x in hs])
    assert (len(ns), len(mol)) in ((2, 8), (3, 10)), f"C{c}: {len(ns)} N, {len(mol)} atoms"
    return mol, [int(x) for x in ns]


def kabsch_deg(P, Q):
    """Rotation angle of the best rigid superposition of centred point sets P -> Q."""
    P = P - P.mean(axis=0); Q = Q - Q.mean(axis=0)
    U, _, Vt = np.linalg.svd(P.T @ Q)
    D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))])
    R = Vt.T @ D @ U.T
    return float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--relax", required=True)
    ap.add_argument("--host", type=int, required=True)
    ap.add_argument("--system", choices=["undoped", "GA", "Sr"], required=True)
    ap.add_argument("--bands", required=True)
    ap.add_argument("--pool", default="results/fa_host/pool_v3_harmonised")
    ap.add_argument("--vac-ref", default="results/fa_host/pool_v2/fa19cspb20i59_232_vI.extxyz")
    ap.add_argument("--rcut", type=float, default=6.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--jobs", default=None, help="write the two partition single points here")
    a = ap.parse_args()
    a29 = _load("a29", "29_dopant_shell_scan.py"); pp = a29.pp
    h = f"m{a.host:02d}"
    tr = read(a.relax, index=":", format="espresso-out")
    start = read(os.path.join(a.bands, f"band_{a.system}_{h}.extxyz"), index=0)
    cell = start.cell.array
    assert start.get_chemical_symbols() == tr[0].get_chemical_symbols()
    assert find_mic(tr[0].positions - start.positions, cell, pbc=True)[1].max() < 1e-4, "trajectory does not start at the band frame"
    host = read(os.path.join(a.pool, f"{h}.extxyz"))
    _, vpos, _ = pp.build_pair(host, a29.ref_vacancy_position(a.pool, a.vac_ref), None, None)
    cen = centres(start, a.system, vpos)
    fin = tr[-1]
    dv = find_mic(fin.positions - start.positions, cell, pbc=True)[0]
    dv -= dv.mean(axis=0)                                  # remove net translation
    dr = np.linalg.norm(dv, axis=1)
    dmin = np.min([find_mic(start.positions - c, cell, pbc=True)[1] for c in cen.values()], axis=0)
    sym = np.array(start.get_chemical_symbols())
    shells = [(0, 4), (4, 6), (6, 8), (8, 10), (10, 99)]
    by_shell = []
    for lo, hi in shells:
        m = (dmin >= lo) & (dmin < hi)
        by_shell.append({"shell_A": [lo, hi], "n": int(m.sum()), "mean_dr_A": round(float(dr[m].mean()), 4) if m.any() else None,
                         "max_dr_A": round(float(dr[m].max()), 4) if m.any() else None,
                         "share_sum_dr2": round(float((dr[m] ** 2).sum() / (dr ** 2).sum()), 4)})
    rots, mols = [], {}
    for c in np.flatnonzero(sym == "C"):
        mol, ns = molecule(start, int(c), sym, cell); mols[int(c)] = mol
        rel = lambda P: find_mic(P[[c] + ns] - P[c], cell, pbc=True)[0]     # C-N skeleton, unwrapped about C
        def ax(P):
            v = rel(P)[1:].mean(axis=0); return v / np.linalg.norm(v)
        axis = float(np.degrees(np.arccos(np.clip(ax(start.positions) @ ax(fin.positions), -1, 1)))) if len(ns) == 2 else None
        rots.append({"C": int(c), "d_A": round(float(dmin[c]), 2), "n_N": len(ns), "kind": "FA" if len(ns) == 2 else "GA",
                     "rot_deg": round(axis, 2) if axis is not None else None,            # FA C->N-midpoint axis
                     "rigid_rot_deg": round(kabsch_deg(rel(start.positions), rel(fin.positions)), 2)})
    E = np.array([x.get_potential_energy() for x in tr])
    near = dmin < a.rcut
    # path work per atom (trapezoid), split at BFGS step 10
    W = np.zeros((2, len(start)))
    for k in range(len(tr) - 1):
        step = find_mic(tr[k + 1].positions - tr[k].positions, cell, pbc=True)[0]
        W[int(k >= 10)] += -0.5 * np.einsum("ij,ij->i", tr[k].get_forces() + tr[k + 1].get_forces(), step)
    W *= 1000                                                   # meV
    dmol = dmin.copy()                                          # organic atoms take their molecule's C distance
    for c, mol in mols.items():
        dmol[mol] = dmin[c]
    work = {"closure_meV": round(float(W.sum() - (E[-1] - E[0]) * 1000), 2),
            "total_meV": round(float(W.sum()), 1), "first10_meV": round(float(W[0].sum()), 1),
            "rest_meV": round(float(W[1].sum()), 1), "by_shell_molecule_assigned": [], "region": {}}
    for lo, hi in shells:
        m = (dmol >= lo) & (dmol < hi)
        work["by_shell_molecule_assigned"].append({"shell_A": [lo, hi], "n": int(m.sum()),
            "W_meV": round(float(W[:, m].sum()), 1), "W_first10_meV": round(float(W[0, m].sum()), 1),
            "W_rest_meV": round(float(W[1, m].sum()), 1),
            "W_organic_meV": round(float(W[:, m & np.isin(sym, ["C", "N", "H"])].sum()), 1)})
    for name, m in (("near", dmol < a.rcut), ("far", dmol >= a.rcut)):
        work["region"][name] = {"n": int(m.sum()), "W_meV": round(float(W[:, m].sum()), 1),
                                "W_first10_meV": round(float(W[0, m].sum()), 1), "W_rest_meV": round(float(W[1, m].sum()), 1),
                                "share": round(float(W[:, m].sum() / W.sum()), 4)}
    fa = [r for r in rots if r["kind"] == "FA"]
    res = {"relax": os.path.basename(a.relax), "host": h, "system": a.system, "n_steps": len(tr),
           "E_relax_meV": round(float((E[-1] - E[0]) * 1000), 1),
           "E_trajectory_meV_every10": [round(float((e - E[0]) * 1000), 1) for e in E[::10]],
           "last20_slope_meV_per_step": round(float((E[-1] - E[-21]) * 1000 / 20), 3) if len(E) > 21 else None,
           "rcut_A": a.rcut, "n_near": int(near.sum()), "n_far": int((~near).sum()),
           "share_sum_dr2_far": round(float((dr[~near] ** 2).sum() / (dr ** 2).sum()), 4),
           "by_shell": by_shell,
           "fa_rotation": {"n": len(fa), "measure": "FA C->N-midpoint axis", "max_deg": max(r["rot_deg"] for r in fa),
                           "d_A_at_max": max(fa, key=lambda r: r["rot_deg"])["d_A"],
                           "n_over_10deg": sum(r["rot_deg"] > 10 for r in fa),
                           "n_over_10deg_far": sum(r["rot_deg"] > 10 and r["d_A"] >= a.rcut for r in fa),
                           "rigid_n_over_10deg": sum(r["rigid_rot_deg"] > 10 for r in fa),
                           "ga": [r for r in rots if r["kind"] == "GA"],
                           "rows": rots},
           "path_work": work}
    os.makedirs(a.out, exist_ok=True)
    tag = f"{h}_{a.system}_img0"
    json.dump(res, open(os.path.join(a.out, f"wp2e_displacement_{tag}.json"), "w"), indent=1)
    with open(os.path.join(a.out, f"wp2e_atoms_{tag}.csv"), "w", newline="") as fh:      # per-atom source data
        w = csv.writer(fh); w.writerow(["index", "symbol", "d_A", "d_molecule_A", "dr_A", "W_meV", "W_first10_meV"])
        for i in range(len(start)):
            w.writerow([i, sym[i], f"{dmin[i]:.4f}", f"{dmol[i]:.4f}", f"{dr[i]:.4f}", f"{W[:, i].sum():.4f}", f"{W[0, i]:.4f}"])
    with open(os.path.join(a.out, f"wp2e_trajectory_{tag}.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["scf_cycle", "F_minus_F0_meV", "fmax_eVA"])
        for k, x in enumerate(tr):
            w.writerow([k, f"{(E[k] - E[0]) * 1000:.3f}", f"{np.linalg.norm(x.get_forces(), axis=1).max():.4f}"])
    if a.jobs:
        a30 = _load("a30", "30_qe_singlepoint.py")
        for name, mask in (("near_only", near), ("far_only", ~near)):
            x = start.copy(); x.calc = None
            x.positions[mask] = start.positions[mask] + find_mic(fin.positions[mask] - start.positions[mask], cell, pbc=True)[0]
            write(os.path.join(a.out, f"part_{tag}_{name}.extxyz"), x)
            a30.write_input(x, f"part_{tag}_{name}", os.path.join(a.jobs, f"part_{tag}_{name}"))
    print(json.dumps({k: v for k, v in res.items() if k not in ("fa_rotation", "E_trajectory_meV_every10", "path_work")}, indent=1))
    print("FA rotation:", {k: v for k, v in res["fa_rotation"].items() if k != "rows"})
    print("path work:", json.dumps(work, indent=1))


if __name__ == "__main__":
    main()

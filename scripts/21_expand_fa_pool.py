#!/usr/bin/env python
"""Objective B: expand the FA-orientation host pool to >=20 candidates.

Generation route matches the existing members 0-7 exactly: randomise every FA molecular
orientation about its own centroid, then relax with MACE. This is deliberate. The proposal
calls for orientations drawn from MLIP-MD snapshots, which samples the thermal
distribution; random-seed + relax samples local minima instead. Switching route mid-pool
would make new members non-comparable with the existing ones, and the paired design needs
one homogeneous pool. Route is recorded in the manifest so the limitation travels with the
data.

Each candidate must pass structural acceptance BEFORE it can host a barrier calculation:
  - relaxation converged
  - every Pb still 6-fold coordinated (no collapsed octahedron)
  - every FA molecule intact (C-N bonds preserved, no dissociation)
  - composition unchanged

    python scripts/21_expand_fa_pool.py --n-new 14 --start-seed 8
"""
import argparse, json, os, sys
import numpy as np
from ase.io import read, write
from ase.optimize import FIRE

FA_CN_MAX = 1.65   # C-N covalent bond cutoff, A
PB_I_CUT = 4.0     # Pb-I first-shell cutoff, A


def fa_groups(atoms):
    """Group C/N/H into FA molecules by connectivity from each carbon."""
    sym = np.array(atoms.get_chemical_symbols())
    pos = atoms.positions
    cell = atoms.cell.array
    inv = np.linalg.inv(cell)

    def mic(dv):
        f = dv @ inv
        f -= np.round(f)
        return f @ cell

    groups = []
    for ci in np.where(sym == "C")[0]:
        d = np.linalg.norm(mic(pos - pos[ci]), axis=1)
        n_idx = [int(j) for j in np.where((sym == "N") & (d < FA_CN_MAX + 0.25))[0]]
        h_idx = [int(j) for j in np.where((sym == "H") & (d < 2.4))[0]]
        # hydrogens bonded to those nitrogens
        for nj in n_idx:
            dn = np.linalg.norm(mic(pos - pos[nj]), axis=1)
            h_idx += [int(j) for j in np.where((sym == "H") & (dn < 1.35))[0]]
        groups.append({"C": int(ci), "N": sorted(set(n_idx)), "H": sorted(set(h_idx))})
    return groups


def randomise_orientations(atoms, rng):
    """Rigid-body random rotation of every FA about its own centroid."""
    at = atoms.copy()
    for g in fa_groups(at):
        idx = [g["C"]] + g["N"] + g["H"]
        if len(idx) < 4:
            continue
        p = at.positions[idx]
        cen = p.mean(axis=0)
        # uniform random rotation via QR of a gaussian matrix (Haar measure)
        q, r = np.linalg.qr(rng.normal(size=(3, 3)))
        q *= np.sign(np.diag(r))
        if np.linalg.det(q) < 0:
            q[:, 0] *= -1
        at.positions[idx] = (p - cen) @ q.T + cen
    return at


def structural_accept(at, ref_counts):
    """Structural acceptance. Returns (ok, reasons, diagnostics)."""
    from collections import Counter
    reasons = []
    sym = np.array(at.get_chemical_symbols())
    cell = at.cell.array
    inv = np.linalg.inv(cell)

    def mic(dv):
        f = dv @ inv
        f -= np.round(f)
        return f @ cell

    if Counter(sym) != ref_counts:
        reasons.append("composition changed")

    pb = np.where(sym == "Pb")[0]
    iod = np.where(sym == "I")[0]
    cns = []
    for p in pb:
        d = np.linalg.norm(mic(at.positions[iod] - at.positions[p]), axis=1)
        cns.append(int((d < PB_I_CUT).sum()))
    if cns and min(cns) < 6:
        reasons.append(f"Pb undercoordinated (min CN {min(cns)})")

    groups = fa_groups(at)
    n_fa = len(groups)
    intact = all(len(g["N"]) == 2 for g in groups)
    if not intact:
        reasons.append("FA dissociated (a C lacks 2 N)")

    return (not reasons), reasons, {"pb_cn_min": min(cns) if cns else None,
                                    "pb_cn_max": max(cns) if cns else None,
                                    "n_fa": n_fa, "fa_intact": intact}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="results/fa_host/fa19cs1_pb20i60_233.extxyz")
    ap.add_argument("--out", default="results/fa_host")
    ap.add_argument("--n-new", type=int, default=14)
    ap.add_argument("--start-seed", type=int, default=8)
    ap.add_argument("--fmax", type=float, default=0.03)
    ap.add_argument("--steps", type=int, default=1500)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--dtype", default="float64")
    args = ap.parse_args()

    from collections import Counter
    from mace.calculators import mace_mp
    calc = mace_mp(model="medium", device=args.device, default_dtype=args.dtype)

    base = read(args.host)
    ref_counts = Counter(base.get_chemical_symbols())
    os.makedirs(args.out, exist_ok=True)
    rows = []
    for k in range(args.n_new):
        seed = args.start_seed + k
        rng = np.random.RandomState(seed)
        at = randomise_orientations(base, rng)
        at.calc = calc
        opt = FIRE(at, logfile=None)
        opt.run(fmax=args.fmax, steps=args.steps)
        fmax = float(np.abs(at.get_forces()).max())
        E = float(at.get_potential_energy())
        ok, reasons, diag = structural_accept(at, ref_counts)
        conv = bool(opt.converged())
        accept = ok and conv
        row = {"seed": seed, "orientation": f"random_{seed}", "E_relaxed_eV": E,
               "converged": conv, "fmax": round(fmax, 4),
               "nsteps": int(opt.get_number_of_steps()),
               "accepted": accept, "reject_reasons": reasons, **diag,
               "route": "random FA orientation + MACE relax (matches members 0-7)"}
        rows.append(row)
        if accept:
            w = at.copy(); w.calc = None
            write(f"{args.out}/fa_ensemble_{seed:02d}.extxyz", w)
        print(f"  seed {seed:2d}: E={E:.4f} eV fmax={fmax:.4f} conv={conv} "
              f"pbCN={diag['pb_cn_min']}-{diag['pb_cn_max']} fa_intact={diag['fa_intact']} "
              f"-> {'ACCEPT' if accept else 'REJECT ' + '; '.join(reasons)}")
        sys.stdout.flush()

    acc = [r for r in rows if r["accepted"]]
    E = np.array([r["E_relaxed_eV"] for r in acc])
    out = {"route": "random FA orientation + MACE relax",
           "route_note": ("Matches members 0-7. NOT MLIP-MD snapshots: this samples local "
                          "minima, not the thermal orientation distribution. Recorded so "
                          "the limitation travels with the data."),
           "level": f"MACE-MP-0 medium, {args.device.upper()}, {args.dtype}",
           "fmax": args.fmax, "n_attempted": len(rows), "n_accepted": len(acc),
           "E_min_eV": float(E.min()) if len(E) else None,
           "E_spread_meV": float((E.max() - E.min()) * 1000) if len(E) else None,
           "rows": rows}
    json.dump(out, open(f"{args.out}/fa_pool_expansion.json", "w"), indent=1)
    print(f"\naccepted {len(acc)}/{len(rows)} new candidates")


if __name__ == "__main__":
    main()

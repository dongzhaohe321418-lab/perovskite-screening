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
# Minimum allowed separation between atoms in DIFFERENT molecules/framework after a
# trial rotation. The relaxed host's own closest INTERMOLECULAR contact sets the scale;
# 2.0 A is below every such contact in the relaxed cell but far above the 0.3-0.7 A
# overlaps that produced nonsense MACE energies in the first attempt.
MIN_SEP_A = 2.0


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


def _rand_rot(rng):
    """Uniform random rotation via QR of a gaussian matrix (Haar measure)."""
    q, r = np.linalg.qr(rng.normal(size=(3, 3)))
    q *= np.sign(np.diag(r))
    if np.linalg.det(q) < 0:
        q[:, 0] *= -1
    return q


def randomise_orientations(atoms, rng, *, min_sep=MIN_SEP_A, max_tries=200):
    """Rigid random rotation of every FA ABOUT ITS OWN CARBON, using MIC vectors.

    This reproduces `randomize_fa_orientations` in scripts/07_fa_host_cell.py, which built
    the existing members 0-7. Two details are load-bearing and were both wrong in my first
    attempt, which accepted 0 of 14 candidates and put the 3 eventual survivors 8.2 eV
    above the existing pool (whose own spread is 0.35 eV):

      * PIVOT ON THE CARBON, not the molecular centroid. The C sits in the A-site cage and
        must stay there. A centroid pivot displaces it by up to twice the C-to-centroid
        offset -- and that offset is itself meaningless for a molecule wrapped across the
        periodic boundary, where a naive mean of raw coordinates lands nowhere near the
        molecule. Doing this to all 19 FA at once is what cost 8 eV.
      * BUILD THE MOLECULE FROM MIC VECTORS relative to the C, so a wrapped molecule stays
        intact through the rotation.

    Clash rejection is retained on top (the original had none): a trial rotation is accepted
    only if every atom stays >= `min_sep` from every atom outside its own molecule. The
    relaxed host's closest FA-to-framework contact is 2.65 A, so 2.0 A admits real
    orientations while excluding the 0.3-0.7 A overlaps that produce nonsense MACE forces.
    """
    at = atoms.copy()
    n_kept = 0
    for g in fa_groups(at):
        idx = [g["C"]] + g["N"] + g["H"]
        c = g["C"]
        if len(idx) < 4:
            continue
        others = np.setdiff1d(np.arange(len(at)), idx)
        cpos = at.positions[c].copy()
        # MIC vectors from the carbon keep a boundary-wrapped molecule intact
        vecs = np.array([at.get_distance(int(c), int(a), mic=True, vector=True) for a in idx])
        placed = False
        for _ in range(max_tries):
            trial = cpos + vecs @ _rand_rot(rng).T
            # minimum-image separation of the trial molecule from everything else
            dv = at.positions[others][None, :, :] - trial[:, None, :]
            cell = at.cell.array
            f = dv @ np.linalg.inv(cell)
            f -= np.round(f)
            d = np.linalg.norm(f @ cell, axis=2)
            if d.min() >= min_sep:
                at.positions[idx] = trial
                placed = True
                break
        if not placed:
            n_kept += 1          # leave this molecule as it was rather than force a clash
    at.wrap()
    if n_kept:
        print(f"    ({n_kept} FA kept original orientation -- no clash-free rotation found)")
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

#!/usr/bin/env python
"""
Gate-6 noise floor: the UNDOPED iodide-vacancy migration barrier across FA-orientation
ensemble members of the FA_0.95Cs_0.05PbI3 host.

Why this is the first Objective-2 measurement. A dopant ranking is only meaningful if
the between-dopant differences exceed the within-host configurational spread. That
spread has never been measured for this host, so no dEa can currently be called
significant. This script measures it: same composition, same vacancy, only the FA
orientations differ.

MACE-level, EXPLORE tier. No DFT, no ranking.

Usage:
  python scripts/17_fa_ensemble_noise_floor.py --members 0 1 2 3 --images 5 --fmax 0.05
"""
from __future__ import annotations
import argparse, json, os, time
import numpy as np
from ase.io import read, write
from ase.mep import NEB
from ase.optimize import FIRE
from ase.constraints import FixAtoms


def find_vacancy(pristine, vac):
    pi = pristine.positions[np.array(pristine.get_chemical_symbols()) == "I"]
    vi = vac.positions[np.array(vac.get_chemical_symbols()) == "I"]
    cell = pristine.cell.array
    inv = np.linalg.inv(cell)
    best = None
    for p in pi:
        f = (vi - p) @ inv
        f -= np.round(f)
        dmin = np.linalg.norm(f @ cell, axis=1).min()
        if best is None or dmin > best[0]:
            best = (dmin, p)
    return best[1]


def nearest_iodide(atoms, target, exclude=()):
    sym = np.array(atoms.get_chemical_symbols())
    cell = atoms.cell.array
    inv = np.linalg.inv(cell)
    best = None
    for i in np.where(sym == "I")[0]:
        if i in exclude:
            continue
        f = (atoms.positions[i] - target) @ inv
        f -= np.round(f)
        d = np.linalg.norm(f @ cell)
        if best is None or d < best[1]:
            best = (int(i), float(d))
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host-dir", default="results/fa_host")
    ap.add_argument("--out", default="results/objective2/noise_floor")
    ap.add_argument("--members", type=int, nargs="+", default=[0, 1, 2, 3])
    ap.add_argument("--images", type=int, default=5, help="interior images")
    ap.add_argument("--fmax", type=float, default=0.05)
    ap.add_argument("--steps", type=int, default=80)
    ap.add_argument("--relax-endpoints", action="store_true", default=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    from mace.calculators import mace_mp
    calc = mace_mp(model="medium", device="cpu", default_dtype="float64")

    pristine = read(f"{args.host_dir}/fa19cs1_pb20i60_233.extxyz")
    vac_ref = read(f"{args.host_dir}/fa19cspb20i59_232_vI.extxyz")
    vpos = find_vacancy(pristine, vac_ref)

    results = []
    for mem in args.members:
        t0 = time.time()
        mpath = f"{args.host_dir}/fa_ensemble_{mem:02d}.extxyz"
        host = read(mpath) if os.path.exists(mpath) else pristine

        # Build the SAME vacancy in this member: remove the iodide closest to vpos.
        vi, dv = nearest_iodide(host, vpos)
        ini = host.copy()
        del ini[vi]

        # Migrating ion: the iodide nearest the vacancy in the resulting cell.
        mig, dm = nearest_iodide(ini, vpos)
        fin = ini.copy()
        fin.positions[mig] = vpos            # hop into the vacancy

        for at in (ini, fin):
            at.calc = mace_mp(model="medium", device="cpu", default_dtype="float64")
        if args.relax_endpoints:
            for at in (ini, fin):
                FIRE(at, logfile=None).run(fmax=args.fmax, steps=args.steps)

        images = [ini] + [ini.copy() for _ in range(args.images)] + [fin]
        for im in images:
            im.calc = mace_mp(model="medium", device="cpu", default_dtype="float64")
        neb = NEB(images, climb=True, allow_shared_calculator=False,
                  method='improvedtangent')
        neb.interpolate(mic=True)
        opt = FIRE(neb, logfile=None)
        opt.run(fmax=args.fmax, steps=args.steps)

        E = np.array([im.get_potential_energy() for im in images])
        Ea_fwd = float(E.max() - E[0])
        Ea_bwd = float(E.max() - E[-1])
        results.append({
            "member": mem, "removed_I_index": vi, "d_removed_to_ref_A": round(dv, 3),
            "migrating_I_index": mig, "hop_distance_A": round(dm, 3),
            "Ea_forward_eV": Ea_fwd, "Ea_backward_eV": Ea_bwd,
            "dE_endpoints_eV": float(E[-1] - E[0]),
            "converged": bool(opt.converged()), "nsteps": int(opt.get_number_of_steps()),
            "profile_eV": [float(x - E[0]) for x in E],
            "wall_s": round(time.time() - t0, 1), "tier": "EXPLORE",
        })
        write(f"{args.out}/band_member_{mem:02d}.extxyz", images)
        print(f"  member {mem}: Ea = {Ea_fwd*1000:7.1f} meV  "
              f"(converged={opt.converged()}, {opt.get_number_of_steps()} steps, "
              f"{time.time()-t0:.0f}s)")

    Ea = np.array([r["Ea_forward_eV"] for r in results]) * 1000
    summary = {
        "tier": "EXPLORE", "level": "MACE-MP-0 medium, CPU, float64, CI-NEB improvedtangent",
        "host": "FA0.95Cs0.05PbI3 233-atom det20 cell, V_I",
        "n_members": len(results),
        "Ea_mean_meV": float(Ea.mean()), "Ea_std_meV": float(Ea.std(ddof=1)) if len(Ea) > 1 else None,
        "Ea_min_meV": float(Ea.min()), "Ea_max_meV": float(Ea.max()),
        "Ea_spread_meV": float(Ea.max() - Ea.min()),
        "note": ("Gate-6 noise floor: within-host configurational spread of the UNDOPED "
                 "barrier. A dopant dEa smaller than this spread is not resolvable in "
                 "this host at this level."),
        "members": results,
    }
    json.dump(summary, open(f"{args.out}/noise_floor.json", "w"), indent=1)
    print(f"\nEa across members (meV): {np.round(Ea,1)}")
    print(f"mean {Ea.mean():.1f} | std {Ea.std(ddof=1) if len(Ea)>1 else float('nan'):.1f} "
          f"| spread {Ea.max()-Ea.min():.1f} meV")
    return summary


if __name__ == "__main__":
    main()

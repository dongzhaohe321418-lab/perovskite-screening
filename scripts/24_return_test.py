#!/usr/bin/env python
"""Local-stability RETURN TEST for asymmetric-well initial endpoints (PI protocol).

For each rejected asymmetric-well path: perturb the relaxed INITIAL endpoint along the
initial -> first-NEB-image direction, both signs, amplitudes 0.02 and 0.05 A (4 tests),
re-relax, and check whether it returns to the initial basin.

  PASS (metastable): all 4 perturbations relax back (max per-atom displacement from the
       unperturbed endpoint < RETURN_TOL and energy within E_TOL) -> the forward barrier
       from this state is a well-defined screening quantity.
  FAIL: any perturbation slides to a lower configuration -> not a definable hop origin.

Usage: python 24_return_test.py --rerun-dir <out dir> --rejected <basin_summary_v2.json>
"""
import argparse, json, os, sys, time
import numpy as np
from ase.io import read
from ase.optimize import FIRE

RETURN_TOL_A = 0.15    # max per-atom displacement to count as "same configuration"
E_TOL_MEV = 5.0        # and energy within this of the unperturbed endpoint

def mic(dv, cell):
    inv = np.linalg.inv(cell)
    f = dv @ inv
    f -= np.round(f)
    return f @ cell

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rerun-dir", required=True)
    ap.add_argument("--rejected", required=True)
    ap.add_argument("--fmax", type=float, default=0.02)
    ap.add_argument("--steps", type=int, default=2000)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out", default="return_test.json")
    a = ap.parse_args()

    from mace.calculators import mace_mp
    def make_calc():
        return mace_mp(model="medium", device=a.device, default_dtype="float64")

    rej = [r for r in json.load(open(a.rejected)) if r.get("asym_well")]
    print(f"{len(rej)} asymmetric-well paths to test")
    results = []
    for r in rej:
        t0 = time.time()
        band = read(f"{a.rerun_dir}/band_{r['system']}_m{r['member']:02d}.extxyz", ":")
        ini, img1 = band[0], band[1]
        cell = ini.cell.array
        # perturbation direction: initial -> first interior image, normalised per-atom field
        dvec = mic(img1.positions - ini.positions, cell)
        nrm = np.linalg.norm(dvec)
        if nrm < 1e-8:
            results.append({**{k: r[k] for k in ("member","system")}, "verdict": "SKIP_degenerate"})
            continue
        # INCIDENT: v1 scaled by sqrt(N) ("per-atom RMS = amp"), giving TOTAL displacements
        # of 0.31/0.76 A -- 24-61% of the initial->image-1 segment, and PAST image 1 for
        # three paths, with single-atom moves up to 0.65 A (>> RETURN_TOL 0.15 A). Every
        # NOT_A_MINIMUM verdict from that version was void: it tested "does a large step
        # along the path roll downhill" (it does, trivially), not local stability.
        # Correct scaling: amp = the LARGEST single-atom displacement. max-atom move equals
        # amp exactly (0.02/0.05 A), always < RETURN_TOL, and the perturbation is small
        # relative to every segment.
        dhat = dvec / np.linalg.norm(dvec, axis=1).max()
        ref = ini.copy(); ref.calc = make_calc()
        E0 = ref.get_potential_energy()
        outcomes = []
        for amp in (0.02, 0.05):
            for sign in (+1, -1):
                t = ini.copy()
                t.positions = t.positions + sign * amp * dhat  # max single-atom move = amp
                t.calc = make_calc()
                opt = FIRE(t, logfile=None)
                opt.run(fmax=a.fmax, steps=a.steps)
                disp = np.linalg.norm(mic(t.positions - ini.positions, cell), axis=1).max()
                dE = (t.get_potential_energy() - E0) * 1000
                returned = bool(disp < RETURN_TOL_A and abs(dE) < E_TOL_MEV)
                outcomes.append({"amp_A": amp, "sign": sign, "max_disp_A": round(float(disp), 3),
                                 "dE_meV": round(float(dE), 2), "returned": returned,
                                 "converged": bool(opt.converged())})
        n_ret = sum(o["returned"] for o in outcomes)
        verdict = "METASTABLE" if n_ret == 4 else ("MARGINAL" if n_ret >= 2 else "NOT_A_MINIMUM")
        results.append({**{k: r[k] for k in ("member","system")},
                        "E0_eV": float(E0), "outcomes": outcomes,
                        "n_returned": n_ret, "verdict": verdict,
                        "wall_s": round(time.time() - t0, 1)})
        print(f"  m{r['member']:02d} {r['system']:<8} {verdict} ({n_ret}/4)  {time.time()-t0:5.0f}s")
        sys.stdout.flush()
        json.dump(results, open(a.out, "w"), indent=1)
    n_meta = sum(1 for x in results if x.get("verdict") == "METASTABLE")
    print(f"\nMETASTABLE {n_meta} | MARGINAL {sum(1 for x in results if x.get('verdict')=='MARGINAL')} "
          f"| NOT_A_MINIMUM {sum(1 for x in results if x.get('verdict')=='NOT_A_MINIMUM')}")

if __name__ == "__main__":
    main()

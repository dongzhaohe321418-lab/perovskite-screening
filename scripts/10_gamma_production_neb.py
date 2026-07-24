#!/usr/bin/env python3
"""Production MACE CI-NEB for the gamma-P1 V_I edge hop — upgrades the exploratory
tracer (scripts/01, no convergence metadata) to a production reference with full
metadata + a 5->7 interior-image densification check (per review).

Also serves Stage 2.2: this is the well-defined MACE reference path the DFT explore
path's d_max is measured against. Charge-agnostic zero-shot MACE-MP-0 (quasi-neutral
PES) — a path/mechanism reference, NOT a charge-state barrier.

Uses the endpoints of the existing frozen band (regression_saddle_path.extxyz frames
0 and 6), re-relaxes them tight (fmax<=0.02), and runs CI-NEB at 5 and 7 interior
images, recording FIRE convergence, final max NEB force, barrier, and saddle for each.

Usage:
  python 10_gamma_production_neb.py --band results/objective1/regression_saddle_path.extxyz \
      --outdir results/objective1/dft/gamma_production_neb --device cuda
"""
import argparse, json
from pathlib import Path
import numpy as np
from ase.io import read, write
from ase.mep import NEB
from ase.optimize import FIRE

FMAX_EP = 0.02
FMAX_NEB = 0.03


def build_calcs(n, model, device, dtype):
    from mace.calculators import mace_mp
    return [mace_mp(model=model, device=device, default_dtype=dtype, dispersion=False)
            for _ in range(n)]


def run_neb(initial, final, calcs, n_interior, fmax_ep=FMAX_EP, fmax_neb=FMAX_NEB):
    initial = initial.copy(); final = final.copy()
    initial.calc = calcs[0]
    c1 = FIRE(initial, logfile=None).run(fmax=fmax_ep, steps=1000)
    final.calc = calcs[-1]
    c2 = FIRE(final, logfile=None).run(fmax=fmax_ep, steps=1000)
    images = [initial] + [initial.copy() for _ in range(n_interior)] + [final]
    for im, c in zip(images, calcs):
        im.calc = c
    neb = NEB(images, climb=False, k=0.1)
    neb.interpolate(method="idpp", mic=True)
    conv1 = FIRE(neb, logfile=None).run(fmax=2 * fmax_neb, steps=600)
    neb.climb = True
    conv2 = FIRE(neb, logfile=None).run(fmax=fmax_neb, steps=600)
    energies = np.array([im.get_potential_energy() for im in images])
    # Production convergence metric = the max PERPENDICULAR true force across interior
    # images (what NEB actually converges) — NOT the raw force, which is dominated by
    # the along-path spring component and would misleadingly read ~0.16 eV/A at a
    # converged saddle. tangents by the improved-tangent estimate (finite-diff proxy).
    def perp_fmax(images):
        pos = [im.get_positions() for im in images]
        worst = 0.0
        for i in range(1, len(images) - 1):
            f = images[i].get_forces()
            tau = pos[i + 1] - pos[i - 1]
            tau /= (np.linalg.norm(tau) + 1e-12)
            fperp = f - np.sum(f * tau) * tau
            worst = max(worst, float(np.sqrt((fperp**2).sum(axis=1).max())))
        return worst
    fmax_perp = perp_fmax(images)
    fmax_raw = max(np.sqrt((im.get_forces()**2).sum(axis=1).max()) for im in images[1:-1])
    prof = (energies - energies[0]) * 1000
    return {"n_interior": n_interior, "n_total": len(images),
            "profile_meV": [round(float(x), 1) for x in prof],
            "saddle_image": int(np.argmax(energies)),
            "Ea_fwd_meV": round(float((energies.max() - energies[0]) * 1000), 1),
            "Ea_bwd_meV": round(float((energies.max() - energies[-1]) * 1000), 1),
            "endpoints_converged": bool(c1 and c2),
            "neb_converged": bool(conv2),
            "final_max_perp_force_eV_A": round(float(fmax_perp), 4),
            "final_max_raw_force_eV_A": round(float(fmax_raw), 4),
            "fmax_ep": fmax_ep, "fmax_neb": fmax_neb}, images


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--band", required=True)
    p.add_argument("--outdir", default="gamma_production_neb")
    p.add_argument("--device", default="cuda")
    p.add_argument("--model", default="medium")
    p.add_argument("--dtype", default="float64")
    args = p.parse_args()
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)

    band = read(args.band, index=":")
    initial, final = band[0], band[-1]
    print(f"[neb] endpoints from {args.band}: {len(band)} frames, {len(initial)} atoms")

    calcs = build_calcs(9, args.model, args.device, args.dtype)  # enough for 7 interior + 2
    results = {}
    for n_int in (5, 7):
        res, images = run_neb(initial, final, calcs[:n_int + 2], n_int)
        write(outdir / f"gamma_neb_band_{n_int}int.extxyz", images)
        results[f"{n_int}_interior"] = res
        print(f"[neb] {n_int} interior: Ea_fwd={res['Ea_fwd_meV']} meV saddle=img{res['saddle_image']} "
              f"neb_conv={res['neb_converged']} perpF={res['final_max_perp_force_eV_A']} "
              f"rawF={res['final_max_raw_force_eV_A']}")

    # densification check: barrier shift 5->7
    d = results["7_interior"]["Ea_fwd_meV"] - results["5_interior"]["Ea_fwd_meV"]
    summary = {"tag": "production MACE reference (zero-shot MACE-MP-0, charge-agnostic)",
               "host": "gamma-P1 tilted gamma-like CsPbI3 2x2x2 V_I",
               "results": results,
               "densification_shift_5to7_meV": round(float(d), 1),
               "note": ("Upgrades the scripts/01 tracer to production convergence + metadata. "
                        "Charge-agnostic quasi-neutral PES; path/mechanism reference, not a "
                        "charge-state barrier. Reference path for the Stage-2.2 d_max comparison.")}
    json.dump(summary, open(outdir / "gamma_production_neb.json", "w"), indent=2)
    print(f"[neb] densification 5->7 interior: {d:+.1f} meV")
    print(f"[neb] done -> {outdir}")


if __name__ == "__main__":
    main()

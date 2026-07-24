#!/usr/bin/env python3
"""Lane 2 / W2-2 — FA orientation ensemble via MLIP-MD (EXPLORATORY / QUARANTINED).

Runs a 300 K NVT MD trajectory on the pure-FA 2x2x2 (96-atom) parent with zero-shot
MACE-MP-0, extracts decorrelated frames, quench-relaxes each (fixed lattice), and
keeps >=8 orientation configs that pass structure checks. Per EXECUTION_GUIDE W2-2:
MD is used ONLY to sample FA orientations, not for any kinetic/dynamical claim
(zero-shot rotational barriers are not validated).

Structure checks per frame:
  * FA intact (C-N ~1.3 A, N-H ~1.0 A, no dissociation);
  * N-H...I contacts sane (>= ~2.0 A, no clash);
  * PbI6 framework intact (every Pb 6-fold under minimum image);
  * no non-perovskite reconstruction (Pb-I connectivity preserved).

Usage:
  python 08_fa_md_ensemble.py --infile fa_pure_2x2x2_96.extxyz --outdir fa_md \
      --T 300 --ps 30 --timestep 1.0 --sample-every-ps 3 --device cuda
"""
import argparse, json
from pathlib import Path
import numpy as np
from ase.io import read, write


def check_structure(atoms, pb_cut=3.7, hi_clash=2.0):
    """Return (ok, report) from minimum-image structure checks."""
    sym = np.array(atoms.get_chemical_symbols())
    rep = {}
    # FA integrity: C-N and N-H bond ranges
    c_idx = np.flatnonzero(sym == "C"); n_idx = np.flatnonzero(sym == "N")
    h_idx = np.flatnonzero(sym == "H"); i_idx = np.flatnonzero(sym == "I")
    pb_idx = np.flatnonzero(sym == "Pb")
    # each C should bond 2 N (FA = CH(NH2)2)
    cn_ok = True; cn_vals = []
    for c in c_idx:
        d = atoms.get_distances(int(c), n_idx, mic=True)
        near = np.sort(d)[:2]; cn_vals.extend(near.tolist())
        if not (near < 1.6).all():
            cn_ok = False
    rep["CN_range"] = [round(float(min(cn_vals)), 3), round(float(max(cn_vals)), 3)]
    rep["FA_CN_ok"] = bool(cn_ok)
    # N-H: each N should have >=1 H within 1.2 A
    nh_ok = True; nh_vals = []
    for n in n_idx:
        d = atoms.get_distances(int(n), h_idx, mic=True)
        near = np.sort(d)[:2]; nh_vals.extend(near.tolist())
        if (d < 1.2).sum() < 1:
            nh_ok = False
    rep["NH_range"] = [round(float(min(nh_vals)), 3), round(float(max(nh_vals)), 3)]
    rep["FA_NH_ok"] = bool(nh_ok)
    # H...I closest contact (clash check)
    hi_min = 9.9
    for h in h_idx:
        hi_min = min(hi_min, float(atoms.get_distances(int(h), i_idx, mic=True).min()))
    rep["min_HI_A"] = round(hi_min, 3)
    rep["HI_no_clash"] = bool(hi_min >= hi_clash)
    # Pb coordination (6-fold under MIC)
    cns = [int((atoms.get_distances(int(p), i_idx, mic=True) < pb_cut).sum()) for p in pb_idx]
    rep["pb_coordination"] = cns
    rep["all_pb_6fold"] = bool(all(cn == 6 for cn in cns))
    ok = cn_ok and nh_ok and rep["HI_no_clash"] and rep["all_pb_6fold"]
    return ok, rep


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--infile", required=True)
    p.add_argument("--outdir", default="fa_md")
    p.add_argument("--T", type=float, default=300.0)
    p.add_argument("--ps", type=float, default=30.0, help="total MD ps")
    p.add_argument("--timestep", type=float, default=1.0, help="fs")
    p.add_argument("--sample-every-ps", type=float, default=3.0)
    p.add_argument("--equilib-ps", type=float, default=5.0, help="discard leading ps")
    p.add_argument("--device", default="cuda")
    p.add_argument("--model", default="medium")
    p.add_argument("--seed", type=int, default=1234)
    args = p.parse_args()
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)

    from mace.calculators import mace_mp
    from ase import units
    from ase.md.langevin import Langevin
    from ase.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary
    from ase.optimize import FIRE

    atoms = read(args.infile)
    calc = mace_mp(model=args.model, device=args.device, default_dtype="float64", dispersion=False)
    atoms.calc = calc

    rng = np.random.default_rng(args.seed)
    MaxwellBoltzmannDistribution(atoms, temperature_K=args.T, rng=rng)
    Stationary(atoms)

    dt = args.timestep * units.fs
    dyn = Langevin(atoms, dt, temperature_K=args.T, friction=0.02, rng=rng)

    n_steps = int(args.ps * 1000 / args.timestep)
    sample_stride = int(args.sample_every_ps * 1000 / args.timestep)
    equilib_steps = int(args.equilib_ps * 1000 / args.timestep)

    traj_frames = []
    log = {"T": args.T, "ps": args.ps, "timestep_fs": args.timestep,
           "sample_every_ps": args.sample_every_ps, "equilib_ps": args.equilib_ps,
           "n_steps": n_steps, "samples": []}

    step_counter = {"n": 0}
    def sample():
        s = step_counter["n"]
        if s >= equilib_steps and (s - equilib_steps) % sample_stride == 0:
            snap = atoms.copy()
            snap.info["md_step"] = s
            snap.info["md_ps"] = round(s * args.timestep / 1000, 2)
            snap.info["epot_eV"] = float(atoms.get_potential_energy())
            snap.info["T_inst"] = float(atoms.get_temperature())
            traj_frames.append(snap)
    dyn.attach(sample, interval=1)
    def tick():
        step_counter["n"] += 1
    dyn.attach(tick, interval=1)

    print(f"[md] {args.ps} ps at {args.T} K, dt {args.timestep} fs, "
          f"sample every {args.sample_every_ps} ps after {args.equilib_ps} ps equilib")
    for chunk in range(10):
        dyn.run(n_steps // 10)
        print(f"[md] {(chunk+1)*10}%  step {step_counter['n']}  "
              f"T={atoms.get_temperature():.0f}K  E={atoms.get_potential_energy():.2f}")

    write(outdir / "fa_md_traj_samples.extxyz", traj_frames)
    print(f"[md] extracted {len(traj_frames)} raw samples")

    # quench-relax each sampled frame (fixed lattice) and structure-check
    kept = []
    for k, frame in enumerate(traj_frames):
        f = frame.copy(); f.calc = calc
        dyn2 = FIRE(f, logfile=None)
        conv = dyn2.run(fmax=0.05, steps=300)
        ok, rep = check_structure(f)
        rec = {"sample": k, "md_ps": frame.info["md_ps"],
               "E_relaxed_eV": float(f.get_potential_energy()),
               "converged": bool(conv), "passed": bool(ok), **rep}
        log["samples"].append(rec)
        if ok and conv:
            f.info["src_md_ps"] = frame.info["md_ps"]
            f.info["config_id"] = len(kept)
            write(outdir / f"fa_orient_{len(kept):02d}.extxyz", f)
            kept.append(rec)
        print(f"[quench] sample {k} ps={frame.info['md_ps']:5.1f} "
              f"E={rec['E_relaxed_eV']:.2f} pass={ok} pb6={rep['all_pb_6fold']} "
              f"minHI={rep['min_HI_A']}")

    log["n_kept"] = len(kept)
    E = [r["E_relaxed_eV"] for r in kept]
    log["ensemble_E_spread_meV"] = (max(E) - min(E)) * 1000 if len(E) > 1 else 0.0
    json.dump(log, open(outdir / "fa_md_ensemble.json", "w"), indent=2)
    print(f"\n[md] kept {len(kept)} configs passing structure checks -> {outdir}")
    print(f"[md] ensemble energy spread: {log['ensemble_E_spread_meV']:.1f} meV")


if __name__ == "__main__":
    main()

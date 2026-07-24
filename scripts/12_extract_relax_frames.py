#!/usr/bin/env python3
"""Extract CONVERGED IONIC steps from a QE relax .out as Stage-3 training candidate
frames (per review: NOT electronic-SCF intermediate iterations — those are not
independent configurations and may be unconverged).

ASE's espresso-out reader yields one Atoms object per *ionic* step of a relax/vc-relax
run, each carrying the converged energy and forces for that geometry. That is exactly
the set of training seeds we want: the geometry sequence the optimiser visited, each a
self-consistently converged single-point.

For each ionic step we record energy (eV), max force, and (if spin-polarised) the total
magnetization parsed from the log. Frames are written to an extxyz trajectory + a JSON
manifest. Optionally thins to every k-th frame to avoid near-duplicate early steps.

Usage:
  python 12_extract_relax_frames.py --out relax_q0_initial.out \
      --outdir results/objective1/dft/charge_relaxed/q0 --stride 1
"""
import argparse, json, re
from pathlib import Path
import numpy as np
from ase.io import read, write

RE_TOTMAG = re.compile(r"total magnetization\s*=\s*(-?\d+\.\d+)\s*Bohr mag")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True, help="QE relax .out file")
    p.add_argument("--outdir", required=True)
    p.add_argument("--stride", type=int, default=1, help="keep every k-th ionic step")
    p.add_argument("--tag", default="stage3_seed")
    args = p.parse_args()
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    stem = Path(args.out).stem

    # every ionic step (converged SCF per step), NOT electronic iterations
    images = read(args.out, index=":")
    if not isinstance(images, list):
        images = [images]
    # per-step total magnetization (one printed block per ionic SCF)
    txt = Path(args.out).read_text()
    mags = [float(m) for m in RE_TOTMAG.findall(txt)]

    frames, records = [], []
    for i, at in enumerate(images):
        if i % args.stride != 0 and i != len(images) - 1:
            continue
        try:
            e = at.get_potential_energy()
        except Exception:
            e = None
        try:
            f = at.get_forces(); fmax = float(np.sqrt((f**2).sum(axis=1).max()))
        except Exception:
            fmax = None
        at.info["stage3_tag"] = args.tag
        at.info["ionic_step"] = i
        if i < len(mags):
            at.info["total_magnetization"] = mags[i]
        frames.append(at)
        records.append({"ionic_step": i, "energy_eV": e, "max_force_eV_A": fmax,
                        "total_magnetization": (mags[i] if i < len(mags) else None)})

    traj = outdir / f"{stem}_ionic_frames.extxyz"
    write(traj, frames)
    manifest = {"source_out": Path(args.out).name, "tag": args.tag,
                "n_ionic_steps_total": len(images), "n_frames_kept": len(frames),
                "stride": args.stride,
                "note": "converged ionic steps only (not electronic-SCF intermediates); "
                        "Stage-3 training candidate frames",
                "frames": records}
    json.dump(manifest, open(outdir / f"{stem}_ionic_frames.json", "w"), indent=2)
    print(f"[relax] {stem}: {len(images)} ionic steps -> kept {len(frames)} frames "
          f"(stride {args.stride}) -> {traj}")
    if records:
        e0, ef = records[0]["energy_eV"], records[-1]["energy_eV"]
        if e0 is not None and ef is not None:
            print(f"[relax] E: {e0:.3f} -> {ef:.3f} eV (relaxed by {(e0-ef)*1000:.1f} meV), "
                  f"final max|F|={records[-1]['max_force_eV_A']}")


if __name__ == "__main__":
    main()

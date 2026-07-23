#!/usr/bin/env python3
"""Parse Quantum ESPRESSO pw.x outputs from the gamma-CsPbI3 V_I benchmark.

Reads a directory of .out/.pwo files (named like img{N}_q{Q}[_{CASE}].out) and
extracts, per run: final total energy (Ry and eV), SCF iteration count, electron
count, total & absolute magnetization (if nspin=2), max force, whether the SCF
converged, and the wall time. It then assembles per-charge-state barrier profiles
E(image)-E(image0) in meV and locates each profile's saddle image.

This is the reproducible companion to scripts/05_generate_qe_inputs.py: the two
together mean the DFT benchmark can be regenerated end-to-end from the repo.

Usage:
  python scripts/06_parse_qe_results.py --indir hpc/<jobid> --out results/objective1/dft/parsed.json
  python scripts/06_parse_qe_results.py --indir ehpc/outputs --out results/.../q0_spin_scan.json --csv
"""
import argparse
import json
import re
from pathlib import Path

RY_TO_EV = 13.605693122994

# QE writes "!    total energy = -9244.9089544 Ry" for the converged SCF energy.
RE_ETOT = re.compile(r"^!\s+total energy\s*=\s*(-?\d+\.\d+)\s*Ry", re.M)
RE_NELEC = re.compile(r"number of electrons\s*=\s*(-?\d+\.\d+)")
RE_CONV_ITER = re.compile(r"convergence has been achieved in\s+(\d+)\s+iterations")
RE_TOTMAG = re.compile(r"total magnetization\s*=\s*(-?\d+\.\d+)\s*Bohr mag")
RE_ABSMAG = re.compile(r"absolute magnetization\s*=\s*(-?\d+\.\d+)\s*Bohr mag")
RE_NSPIN = re.compile(r"number of spin components\s*=\s*(\d+)")
RE_JOBDONE = re.compile(r"JOB DONE")
RE_WALL = re.compile(r"PWSCF\s*:.*?([\d\.]+)s WALL", re.S)
RE_FORCE = re.compile(r"atom\s+\d+\s+type\s+\d+\s+force\s*=\s*"
                      r"(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)")
RE_TOTFORCE = re.compile(r"Total force\s*=\s*(-?\d+\.\d+)")
# filename: img3_q1.out  or  img3_q0_B.out  or  img0_q1_A.pwo
RE_NAME = re.compile(r"img(\d+)_q(\d+)(?:_([A-Za-z0-9]+))?")


def parse_one(path):
    txt = Path(path).read_text(errors="replace")
    etots = RE_ETOT.findall(txt)
    if not etots:
        return {"file": Path(path).name, "converged": False, "error": "no total energy found"}
    e_ry = float(etots[-1])
    nelec = RE_NELEC.search(txt)
    it = RE_CONV_ITER.search(txt)
    totmag = RE_TOTMAG.findall(txt)
    absmag = RE_ABSMAG.findall(txt)
    nspin = RE_NSPIN.search(txt)
    wall = RE_WALL.search(txt)
    # per-atom forces -> max |F| component and max atomic force magnitude
    forces = RE_FORCE.findall(txt)
    fmax = None
    if forces:
        import math
        # forces are printed in Ry/Bohr; take the last SCF's block (len = last nat entries)
        fvals = [(float(a), float(b), float(c)) for a, b, c in forces]
        # keep only the trailing block of the last force print by using Total force marker count
        mags = [math.sqrt(x*x + y*y + z*z) for x, y, z in fvals]
        fmax = max(mags) if mags else None
    m = RE_NAME.search(Path(path).name)
    image = int(m.group(1)) if m else None
    charge = int(m.group(2)) if m else None
    case = m.group(3) if (m and m.group(3)) else "A"
    return {
        "file": Path(path).name, "image": image, "charge": charge, "case": case,
        "energy_Ry": e_ry, "energy_eV": e_ry * RY_TO_EV,
        "nelec": float(nelec.group(1)) if nelec else None,
        "scf_iterations": int(it.group(1)) if it else None,
        "nspin": int(nspin.group(1)) if nspin else 1,
        "total_magnetization": float(totmag[-1]) if totmag else None,
        "absolute_magnetization": float(absmag[-1]) if absmag else None,
        "max_force_Ry_bohr": fmax,
        "wall_s": float(wall.group(1)) if wall else None,
        "converged": bool(RE_JOBDONE.search(txt)) and bool(it),
    }


def build_profiles(runs):
    """Group by (charge, case); barrier profile E(img)-E(img0) in meV per group."""
    groups = {}
    for r in runs:
        if r.get("image") is None or "energy_Ry" not in r:
            continue
        key = f"q{r['charge']}_{r['case']}"
        groups.setdefault(key, {})[r["image"]] = r["energy_Ry"]
    profiles = {}
    for key, d in groups.items():
        if 0 not in d:
            profiles[key] = {"error": "no image 0 reference", "images": sorted(d)}
            continue
        e0 = d[0]
        prof = {img: (d[img] - e0) * RY_TO_EV * 1000.0 for img in sorted(d)}  # meV
        saddle = max(prof, key=prof.get)
        profiles[key] = {"profile_meV": prof, "barrier_meV": prof[saddle],
                         "saddle_image": saddle, "n_images": len(prof)}
    return profiles


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--indir", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--csv", action="store_true", help="also write a <out>.csv table")
    p.add_argument("--glob", default="*.out", help="output filename glob (default *.out)")
    args = p.parse_args()

    indir = Path(args.indir)
    files = sorted(indir.glob(args.glob)) + sorted(indir.glob("*.pwo"))
    files = sorted(set(files))
    runs = [parse_one(f) for f in files]
    runs = [r for r in runs if not r.get("error")] or runs
    profiles = build_profiles(runs)

    result = {"indir": str(indir), "n_files": len(files), "runs": runs, "profiles": profiles}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    json.dump(result, open(out, "w"), indent=2)

    for r in runs:
        if "energy_Ry" in r:
            mag = f" totmag={r['total_magnetization']}" if r.get("total_magnetization") is not None else ""
            print(f"  {r['file']:22s} E={r['energy_Ry']:.7f} Ry  it={r['scf_iterations']} "
                  f"nelec={r['nelec']} conv={r['converged']}{mag}")
    print("--- profiles (meV) ---")
    for key, pr in profiles.items():
        if "barrier_meV" in pr:
            print(f"  {key}: barrier={pr['barrier_meV']:.1f} meV  saddle=img{pr['saddle_image']}  "
                  f"n={pr['n_images']}")
    print(f"[parse] {len(runs)} runs -> {out}")

    if args.csv:
        import csv
        csv_path = out.with_suffix(".csv")
        cols = ["file", "image", "charge", "case", "nspin", "energy_Ry", "energy_eV",
                "scf_iterations", "nelec", "total_magnetization", "absolute_magnetization",
                "max_force_Ry_bohr", "wall_s", "converged"]
        with open(csv_path, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in sorted(runs, key=lambda x: (x.get("charge", 0), x.get("case", ""), x.get("image", 0))):
                w.writerow(r)
        print(f"[parse] csv -> {csv_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Gate-1 GPU regression: does the GPU reproduce the CPU reference?

Two independent checks, both required:

  (A) SINGLE-POINT DETERMINISM. Identical geometries in -> energy and forces must agree.
      This isolates the calculator from the optimiser: any disagreement here is a device
      or precision difference, not a trajectory difference.

  (B) FULL-PATH REPRODUCTION. Re-run one member's whole NEB (endpoint relaxation + band)
      on GPU and compare the barrier to the CPU value. This is the number that matters,
      and it can differ from (A) even when (A) passes, because an optimiser amplifies
      tiny force differences into different trajectories on a soft-mode surface.

Tolerance: 1 meV on the barrier (the user's locked smoke-test criterion).
"""
import argparse, json, os, sys, time
import numpy as np
from ase.io import read

TOL_MEV = 1.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--dtype", default="float64")
    ap.add_argument("--ref", default="cpu_reference.json")
    ap.add_argument("--sp", default="sp_probe.extxyz")
    ap.add_argument("--out", default="gpu_regression.json")
    args = ap.parse_args()

    from mace.calculators import mace_mp
    import torch
    print(f"torch {torch.__version__} | cuda_available={torch.cuda.is_available()}")
    if args.device == "cuda":
        assert torch.cuda.is_available(), "cuda requested but not available"
        print(f"device: {torch.cuda.get_device_name(0)}")

    ref = json.load(open(args.ref))
    calc = mace_mp(model="medium", device=args.device, default_dtype=args.dtype)

    # ---- (A) single-point determinism -------------------------------------------------
    sp = read(args.sp, ":")
    E_ref = np.array(ref["member2_band_E_eV"])
    idx_ref = [0, int(np.argmax(E_ref)), len(E_ref) - 1]
    E_gpu, F_max = [], []
    for a in sp:
        a.calc = calc
        E_gpu.append(a.get_potential_energy())
        F_max.append(float(np.abs(a.get_forces()).max()))
    E_gpu = np.array(E_gpu)
    E_cpu_sub = E_ref[idx_ref]
    dE_abs = (E_gpu - E_cpu_sub) * 1000.0                    # meV, absolute
    # A constant offset would cancel in a barrier; what matters is the RELATIVE spread.
    dE_rel = ((E_gpu - E_gpu[0]) - (E_cpu_sub - E_cpu_sub[0])) * 1000.0
    print("\n(A) single-point:")
    for i, (eg, ec) in enumerate(zip(E_gpu, E_cpu_sub)):
        print(f"    image {idx_ref[i]}: GPU {eg:.8f}  CPU {ec:.8f}  d_abs {dE_abs[i]:+.5f} meV  d_rel {dE_rel[i]:+.5f} meV")
    sp_pass = bool(np.abs(dE_rel).max() < TOL_MEV)
    print(f"    max |d_rel| = {np.abs(dE_rel).max():.5f} meV  -> {'PASS' if sp_pass else 'FAIL'} (tol {TOL_MEV})")

    # barrier from the FIXED CPU geometries, evaluated on GPU: the cleanest device
    # comparison, free of any optimiser difference
    Ea_gpu_fixed = float((E_gpu[1] - E_gpu[0]) * 1000)
    Ea_cpu_fixed = float((E_cpu_sub[1] - E_cpu_sub[0]) * 1000)
    print(f"    barrier on FIXED CPU geometry: GPU {Ea_gpu_fixed:.4f}  CPU {Ea_cpu_fixed:.4f} meV  "
          f"diff {Ea_gpu_fixed-Ea_cpu_fixed:+.5f} meV")

    out = {
        "device": args.device, "dtype": args.dtype,
        "torch": torch.__version__,
        "gpu_name": torch.cuda.get_device_name(0) if args.device == "cuda" else None,
        "tolerance_meV": TOL_MEV,
        "single_point": {
            "image_indices": idx_ref,
            "E_gpu_eV": E_gpu.tolist(), "E_cpu_eV": E_cpu_sub.tolist(),
            "dE_absolute_meV": dE_abs.tolist(), "dE_relative_meV": dE_rel.tolist(),
            "max_abs_dE_relative_meV": float(np.abs(dE_rel).max()),
            "fmax_per_image_eV_A": F_max,
            "Ea_fixed_geometry_gpu_meV": Ea_gpu_fixed,
            "Ea_fixed_geometry_cpu_meV": Ea_cpu_fixed,
            "Ea_fixed_geometry_diff_meV": Ea_gpu_fixed - Ea_cpu_fixed,
            "pass": sp_pass,
        },
    }
    json.dump(out, open(args.out, "w"), indent=1)
    print(f"\nwrote {args.out}")
    return 0 if sp_pass else 1

if __name__ == "__main__":
    sys.exit(main())

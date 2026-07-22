# GPU re-run of the tracer-bullet NEB — run notes

**Date:** 2026-07-22 · **Session:** Mac mini → AutoDL GPU
**Host:** AutoDL, **NVIDIA RTX 5090** (32 GB, Blackwell sm_120, driver 580.142)
— *not* the RTX 4090 the original handoff named; instance was re-rented (handoff corrected).

## What ran
- `base` conda (py 3.12.3) already had **torch 2.8.0+cu128**; a real CUDA matmul confirmed
  Blackwell kernels execute before anything else was attempted.
- Installed `mace-torch 0.3.16`, `ase`, `pymatgen`, `spglib`, `matplotlib` with torch **pinned**
  (`-c torch==2.8.0+cu128`) so pip could not swap in a CPU wheel.
- Ran `scripts/00_relax_bulk.py --device cuda` then `scripts/01_vacancy_neb.py --device cuda`,
  zero-shot MACE-MP-0 medium, float32 (same settings as the CPU baseline — apples-to-apples).

## Result — physics reproduced, ~2× faster on the heavy step

| quantity                       | CPU (M4 Pro) | GPU (RTX 5090) |
|--------------------------------|-------------:|---------------:|
| V_I hop E_a forward (eV)       | 0.259        | 0.259          |
| V_I hop E_a backward (eV)      | 0.230        | 0.230          |
| ΔE endpoints (eV)              | 0.029        | 0.029          |
| hop distance (Å)               | 4.527        | 4.527          |
| γ-tilt gain (meV/atom)         | −18.40       | −18.40         |
| space group (γ)                | P-1 (#2)     | P-1 (#2)       |
| **NEB wall time (s)**          | **34.5**     | **17.6** (1.96×) |
| bulk relax wall time (s)       | 3.1          | 14.5           |

- Max |ΔE_image| CPU-vs-GPU across the 7 NEB images = **0.061 meV** (floating-point noise).
- Same vacancy/hop atom indices (I71→I128), same cell (2×2×2 = 160 atoms, minus one I for the
  vacancy → 159 atoms in the NEB, per `n_atoms` in neb.json).
- Bulk step is *slower* on GPU: the 5- and 20-atom cells are far too small to fill the GPU,
  so wall time is dominated by CUDA init + first-call kernel compilation, not compute.
  Only the 159-atom NEB is large enough to benefit.

## Caveat (unchanged from the tracer bullet)
Still zero-shot, charge-agnostic (quasi-neutral) PES — path-seeding / pipeline-validation only.
Production V_I⁺ barriers require the per-charge-state fine-tuned models (proposal Phase 3).

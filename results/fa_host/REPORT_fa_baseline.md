# FA host baseline — Lane 2 / W2-1 (EXPLORATORY / QUARANTINED)

> **Status tag: EXPLORATORY.** Everything here is zero-shot MACE-MP-0 structure
> building. It does **not** enter any production claim or ranking. Per
> EXECUTION_GUIDE Part 3, Lane-2 products are inputs to Stage 4 only, after a DFT
> audit. No barrier, mobility, or dynamics claim is made in this document.

Built 2026-07-23 by `scripts/07_fa_host_cell.py`. Driver produces the parent cell,
the det=20 supercell enumeration with scoring, and the V_I-carved cell; all
structures are in this directory.

## W2-1a — Pseudo-cubic FAPbI₃ parent

12-atom black α/pseudo-cubic parent: Pb at the origin, I at the three Pb–I–Pb
edge midpoints, one formamidinium cation FA⁺ = [CH(NH₂)₂]⁺ (CH₅N₂, 8 atoms) at the
A-site body centre, hand-placed and tilted 35° off the mirror plane. Relaxed
(cell + positions) with zero-shot MACE-MP-0 medium, float64, on CPU.

| quantity | value |
|---|---|
| parent formula | CH₅I₃N₂Pb (12 atoms) |
| relaxed lattice a,b,c (Å) | 6.519, 6.511, 6.509 |
| relaxed angles (°) | 90.0, 90.0, 88.6 |
| E relax (eV) | −55.037 → −55.262 (converged, fmax 0.05) |
| FA integrity | C–N 1.316–1.320 Å, N–H 1.016–1.022 Å (intact) |
| Pb–I bonds | 3.25–3.27 Å |

The relaxed a ≈ 6.51 Å sits ~2.6% above the experimental α-FAPbI₃ pseudo-cubic
a ≈ 6.35 Å (Weller et al. 2015) — consistent with MACE-MP-0's known lattice
over-softening, and acceptable for a structure-seeding parent. FA did not
dissociate; the PbI₆ framework is intact.

## W2-1b — det=20 supercell enumeration (scored, not defaulted)

Per the guide's explicit instruction **not to default to 2×2×5**, we enumerate
integer transformation matrices with |det| = 20 and score each by its
deviation-from-cubic (ASE `find_optimal_cell_shape` / length-deviation metric;
lower = more isotropic).

| candidate | det | deviation ↓ | transformation matrix P |
|---|---|---|---|
| **optimal_fcc (chosen)** | 20 | **0.0232** | [[−2, 1, 2], [2, 1, 2], [2, 2, −1]] |
| optimal_sc | 20 | 0.1107 | [[2, 0, −2], [−2, 2, −1], [0, 2, 2]] |
| naive 2×2×5 | 20 | 0.9196 | diag(2, 2, 5) |
| naive 1×4×5 | 20 | 1.1532 | diag(1, 4, 5) |

The chosen fcc-target transform is **~40× more isotropic** than the naive 2×2×5
slab (0.023 vs 0.92). Its cell-vector lengths are nearly equal (19.4/19.6/19.8 Å),
which minimises the periodic self-interaction of a point defect — the property
that matters for a migration-barrier supercell — at the cost of skewed cell
angles (an expected feature of a non-diagonal supercell, not a defect).

## W2-1c — Target composition FA₁₉Cs₁Pb₂₀I₆₀ + vacancy

From the chosen supercell (20 formula units), one A-site FA is replaced by Cs
(the FA whose C is nearest the cell centre — a reproducible pick), giving 5% Cs:

| cell | formula | atoms | asserts |
|---|---|---|---|
| pristine | C₁₉H₉₅CsI₆₀N₃₈Pb₂₀ | 233 | 20 Pb, 60 I, 1 Cs, 19 FA (C₁₉N₃₈H₉₅) ✓ |
| V_I carved | (−1 I nearest centre) | 232 | one iodide removed ✓ |

`x_Cs = 1/20 = 5%`, matching the FA₀.₉₅Cs₀.₀₅PbI₃ target. All element-count
asserts are enforced in the driver and pass.

![FA host structures: relaxed pseudo-cubic parent (left) and the 233-atom det=20 FA19Cs1Pb20I60 supercell (right)]({{artifact:art_cf7fb785-e29d-4dc7-99fa-717dd66edf3d}})

## Files

- `fa_parent_relaxed.extxyz` — MACE-relaxed 12-atom pseudo-cubic parent
- `fa19cs1_pb20i60_233.extxyz` — pristine 233-atom det=20 supercell
- `fa19cs1_pb20i60_232_vI.extxyz` — V_I-carved 232-atom cell
- `fa_host_build.json` — full build record (candidates, scores, matrices, asserts)
- `fa_host_structures.png` — parent + supercell render

## Deferred (GPU-gated — pending 5090 availability)

The RTX 5090 (AutoDL) is unavailable (multiple-demand contention). The two
GPU-dependent Lane-2 sub-tasks are **not started** and are explicitly pending:

- **W2-2 FA orientation ensemble** — 2×2×2 (96-atom) pure-FA MLIP-MD at 300 K NVT,
  20–50 ps, frame extraction + quench → ≥8 decorrelated orientation configs with
  structure checks. Needs GPU (MD throughput).
- **W2-3 zero-shot FA baseline distribution** — one V_I octahedron-edge CI-NEB per
  orientation config → the Eₐ distribution (N, mean, std, range) that sizes the
  Stage 4/5 sampling budget. Needs the W2-2 ensemble.

When the 5090 returns: `ssh autodl nvidia-smi` to re-confirm the GPU, rsync the
repo, and run these on GPU. Until then the parent + supercell here are the
GPU-free deliverable.

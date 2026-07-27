# Objective 2 — CURRENT STATUS (canonical index)

**Updated 2026-07-27. This file names the authoritative result for each question; anything
it does not name is historical.**

| question | authoritative document |
|---|---|
| paired pilot statistics (GA/Sr) | `paired_pilot/RERUN_RESULT.md` + `rerun_results.json` |
| why 35 paths were rejected | `paired_pilot/BASIN_IDENTIFICATION.md` (v2) |
| barrier definition + result tiers | `BARRIER_DEFINITION.md` |
| host pool | `../fa_host/pool_v2/POOL_EXPANSION.md` (18 members, used alone) |
| noise floor / sampling baseline | new-pool undoped: n=6, mean 216.2, sd 83.9 meV (planning value) |
| GPU validity | `gpu_regression/GATE1_GPU_REGRESSION.md` |
| automated gates | `../../scripts/checks.py` + `20_test_checks.py` (44 assertions) |

**Superseded / historical (do not cite):** `paired_pilot/PAIRED_PILOT.md` (retracted first
run; retraction record only), `AUDIT_RESPONSE.md` (the audit that triggered the rerun),
`noise_floor/NOISE_FLOOR_REPORT.md` (OLD 8-member pool; its sigma=73.3 does not apply to
pool_v2).

**Return test: COMPLETE** (`paired_pilot/RETURN_TEST_RESULT.md`, raw record
`paired_pilot/return_test/return_test_v2.json`, trajectories
`paired_pilot/return_test/return_test_bands.tar.gz`). 23 of 27 asymmetric-well endpoints are
verified metastable by **displacement alone** (< 0.15 Å; the 5 meV energy criterion was
retired as miscalibrated). Band classes: 5 `pure_hop_asymmetric` (admitted), 11
`hop_plus_FA_reorientation` (separate distribution), 6 `band_collapsed`, 1
`endpoint_energy_unconverged`, 4 `multi_basin_ambiguous`.

**Current pool:** pure-hop admissible **24 of 54**; paired rate **7/18 = 0.389** for both GA
and Sr. At n = 7: GA +29.2 meV (95% CI −29.5 to +87.8), Sr +13.7 meV (−36.3 to +63.8) —
**neither resolvable**, no ranking.

**Next batch (approved shape, not yet launched):** 26 hosts × 3 systems = **78 paths ≈ 3.0
GPU-h** to reach n = 10 pairs per dopant. `hop_plus_FA_reorientation` results are stored and
analysed separately and never enter the pure-hop ranking.

**In flight:** Objective 1 band-edge discriminators P1/P2 (job `32d8fd27`).

**Standing prohibitions:** no ranking from EXPLORE-tier data; no mixing mechanism labels or
result tiers in one distribution; no cross-theory-fingerprint comparisons; old 8-member and
new 18-member pools never merged.

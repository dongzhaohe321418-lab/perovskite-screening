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

**In flight:** return test on the 27 asymmetric-well endpoints (scripts/24_return_test.py)
— gates the sequential expansion to 10 pairs/dopant per `BARRIER_DEFINITION.md`.

**Standing prohibitions:** no ranking from EXPLORE-tier data; no mixing mechanism labels or
result tiers in one distribution; no cross-theory-fingerprint comparisons; old 8-member and
new 18-member pools never merged.

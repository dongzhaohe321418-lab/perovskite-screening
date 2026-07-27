# Objective 2 — CURRENT STATUS (canonical index)

**Updated 2026-07-27 (late). This file names the authoritative result for each question;
anything it does not name is historical.**

## Headline

**GA is EQUIVALENT to no effect at the 10× rate scale** — n = 9 pairs, mean +7.3 meV,
95% CI [−24.0, +38.5], TOST p = 0.0024, and n = 9 meets the 7 required by the χ² variance
bound. First adequately-powered result in the project.
**Sr is SUGGESTIVE-EQUIVALENT** — n = 10, mean −1.8, CI [−48.4, +44.8], TOST p = 0.0104,
but requires 16 pairs under its variance bound. Sr's spread is driven by two
configurations (m14, m20) that pass every gate and are kept.

**No ranking. Both are indistinguishable from zero and from each other. MLIP level only.**

| question | authoritative document |
|---|---|
| paired result (GA/Sr) | `paired_pilot/CORPUS84_RESULT.md` + `corpus84/` raw records |
| host pool | `../fa_host/pool_v3_harmonised/` (28 members, fmax 0.02) + `../fa_host/POOL_HOMOGENEITY.md` |
| why paths are rejected | `paired_pilot/BASIN_IDENTIFICATION.md` (v2) |
| endpoint metastability | `paired_pilot/RETURN_TEST_RESULT.md` + `corpus84/return_test_84.json` |
| barrier definition + tiers | `BARRIER_DEFINITION.md` |
| GPU validity | `gpu_regression/GATE1_GPU_REGRESSION.md` |
| automated gates | `../../scripts/checks.py` + `20_test_checks.py` (61 assertions) |

**Superseded / historical (do not cite):** `paired_pilot/PAIRED_PILOT.md` (retracted first
run), `paired_pilot/RERUN_RESULT.md` and `RETURN_TEST_RESULT.md` statistics (18-host pool —
their *method* stands, their n = 7 numbers are superseded by the 28-host corpus),
`AUDIT_RESPONSE.md`, `noise_floor/NOISE_FLOOR_REPORT.md` (old 8-member pool).

**In flight:** Objective 1 q = 0 geometry relaxation (job `e1319fa5`) — testing whether
lattice relaxation localises the electron into a polaron. See
`../objective1/dft/charge_relaxed/Q0_RESOLVED.md`.

**Standing prohibitions:** no ranking from EXPLORE-tier data; no mixing mechanism labels or
result tiers in one distribution; no cross-theory-fingerprint comparisons; pools of
different relaxation depth never merged.

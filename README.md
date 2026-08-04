# Perovskite screening — γ-CsPbI₃ / FA-perovskite iodine-vacancy migration

**This README is a navigation page only. Results live in the files it links; nothing here is a
result. Last restructured 2026-07-28.**

## Where to look

| you want | go to |
|---|---|
| **Every current scientific conclusion** (one row per question) | [`RESULTS_INDEX.md`](RESULTS_INDEX.md) |
| Objective 2 (GA/Sr additive screening) canonical status | [`results/objective2/CURRENT_STATUS.md`](results/objective2/CURRENT_STATUS.md) |
| Objective 1 (charge-state migration) gate + status | [`results/objective1/dft/charge_relaxed/Q0_NEB_GATE.md`](results/objective1/dft/charge_relaxed/Q0_NEB_GATE.md) |
| Full audit record incl. all retractions | [`EXPERIMENT_AUDIT.md`](EXPERIMENT_AUDIT.md) |
| Governing execution rules (PI) | [`NEXT_STEP_GUIDE.md`](NEXT_STEP_GUIDE.md) |
| Historical / superseded documents | [`archive/`](archive/) — every file carries a `SUPERSEDED` banner |
| Regression suite (52 groups; every check pins a real past incident) | [`scripts/20_test_checks.py`](scripts/20_test_checks.py) |

## The three sub-projects in this repository

1. **Objective 1 — V_I charge-state migration barriers (DFT, active).** Are V_I⁰ and V_I⁺
   migration barriers separable at PBE+D3(BJ) level in the disordered γ-like host?
   Both q=0 endpoints converged; NEB gated behind
   `results/objective1/dft/charge_relaxed/Q0_NEB_GATE.md`.
2. **Objective 2 — additive screening (MACE, active).** Do GA⁺ or Sr²⁺ change the iodine-vacancy
   migration barrier at the 10×-rate scale? Answer so far: both practically equivalent to no
   effect (108 paths, 36 hosts). `results/objective2/CURRENT_STATUS.md`.
3. **`xrd/` — INDEPENDENT sub-project** (experimental XRD passivator screen). It shares no
   evidence chain with Objectives 1–2. Its own `xrd/README.md` applies; nothing there supports
   or is supported by the migration-barrier work.

Early-stage material (the original MACE tracer-bullet pipeline, `results/dopant_screen/`,
`results/fa_host/REPORT_fa_baseline.md`, `literature_survey/`) is retained for provenance and
indexed in `RESULTS_INDEX.md` under "historical".

## Ground rules that hold everywhere

- Barriers computed at different theory fingerprints are never compared.
- MACE-level numbers are never presented as DFT or experiment.
- A job is described as *running* only after its preflight passed and output exists.
- Every correction leaves the superseded record in place, marked, never overwritten.

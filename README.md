# Perovskite screening — γ-CsPbI₃ / FA-perovskite iodine-vacancy migration

**This README is a navigation page only. Results live in the files it links; nothing here is a
result. Last restructured 2026-07-28.**

## Where to look

| you want | go to |
|---|---|
| **Every current scientific conclusion** (one row per question) | [`RESULTS_INDEX.md`](RESULTS_INDEX.md) |
| Objective 2 (GA/Sr additive screening) canonical status | [`results/objective2/CURRENT_STATUS.md`](results/objective2/CURRENT_STATUS.md) |
| Objective 1 (charge-state migration) status — barriers EXTRACTED 2026-08-05 | [`results/objective1/dft/charge_relaxed/CHARGE_STATE_ANCHOR.md`](results/objective1/dft/charge_relaxed/CHARGE_STATE_ANCHOR.md) + [`results/objective1/dft/charge_relaxed/barrier_extraction_record.json`](results/objective1/dft/charge_relaxed/barrier_extraction_record.json) · entry gate (passed): [`results/objective1/dft/charge_relaxed/Q0_NEB_GATE.md`](results/objective1/dft/charge_relaxed/Q0_NEB_GATE.md) |
| Full audit record incl. all retractions | [`EXPERIMENT_AUDIT.md`](EXPERIMENT_AUDIT.md) |
| Governing execution rules (PI) | [`NEXT_STEP_GUIDE.md`](NEXT_STEP_GUIDE.md) |
| Historical / superseded documents | [`archive/`](archive/) — every file carries a `SUPERSEDED` banner |
| Regression suite (54 groups; every check pins a real past incident) | [`scripts/20_test_checks.py`](scripts/20_test_checks.py) |

*(Table note 2026-10-05: the Objective 1 row previously read "gate + status" and routed only to
the Q0 NEB gate file, which is the pre-launch entry gate. The current status authority is
`results/objective1/dft/charge_relaxed/CHARGE_STATE_ANCHOR.md` (EXTRACTED) with
`results/objective1/dft/charge_relaxed/barrier_extraction_record.json`, as named in
`RESULTS_INDEX.md` Q2.)*

## The three sub-projects in this repository

1. **Objective 1 — V_I charge-state migration barriers (DFT, active).** Are V_I⁰ and V_I⁺
   migration barriers separable at PBE+D3(BJ) level in the ~~disordered γ-like host~~
   159-atom γ-like CsPbI₃ cell? *(Wording corrected 2026-10-05 to the scope stated in
   `results/objective1/dft/charge_relaxed/CHARGE_STATE_ANCHOR.md`, which separates this cell
   from the disordered FA ensemble of Objective 2.)*
   ~~Both q=0 endpoints converged; NEB gated behind
   `results/objective1/dft/charge_relaxed/Q0_NEB_GATE.md`.~~ *(Superseded 2026-10-05: the gate
   passed and the PI gave the go on 2026-07-28; both production CI-NEB legs converged (q=0 36
   iterations, q=+1 37 iterations; `results/objective1/dft/charge_relaxed/PRODUCTION_NEB_STATUS.md`).
   Barriers were extracted 2026-08-05: V_I⁰ 185.6 meV, V_I⁺¹ 181.7 meV, difference −3.9 meV
   (bare PBE+D3, FNV residual pending). The two are indistinguishable at this level and the
   Tyagi ordering is NOT reproduced. See
   `results/objective1/dft/charge_relaxed/CHARGE_STATE_ANCHOR.md`.)*
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

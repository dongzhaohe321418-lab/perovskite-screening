# fr implementation: the analyst's decisions on the round-4 re-review (2026-11-12)

Basis: the round-4 re-review of workflow w739j3tt0 (blinding-and-plan and regression lenses; the mutation lens was
still running when this file was written, and its survivors will be decided in a later file). Round 4 left no
critical or major finding. Three minor findings remain; each is decided below. FR_IMPL_DECISIONS_R1.md and
FR_IMPL_DECISIONS_R3.md stay in force.

## Fixes

- **R4-1 (minor; the run-CLI blinding test misses a print from inside the evaluation; mutants C1-C3 of
  the round-4 blinding harness).** In scripts/49 `t_fr`, pin the whole captured output of every run-CLI case, not only the count of
  decision lines: for each run, `rc == 0` and `text.strip().splitlines()` equals the expected decision lines exactly;
  for each refusal row, exactly one line, equal to the expected refusal text. Mutants C1 (a print of |dF| in
  `step0_eval`), C2 (a print of |δ_far| in `fr2_eval` on failure) and C3 (an unconditional print in `fr2_eval`) must
  each be caught.
- **R4-2 (minor; the N-FR8 disagreement Stop sends the operator to read gates/FR.json directly).** gates/FR.json
  holds the FR-2 values once FR-1 has passed, so the Stop must keep the operator on the allow-list. Reword it to name
  the reading route, for example: "runner's early stop <fs> (N-FR8): not applied; read decision.FR of gates/FR.json
  through s2b/guard.py GateLeaves only (S2B §7)". Check the section number against S2B_PLAN.md, keep the text
  hygiene-clean, and let the existing z29/z31 'disagrees' rows assert the new wording. Grep every other new fr message
  that names a file under gates/, fr/raw/ or a part output, and apply the same rule.
- **R4-3 (minor; `archive --campaign fr` accepts an --out under c1/ or c3/).** For campaign fr only (C1-C4 stay
  byte-identical), refuse, before anything is written, an --out whose real path lies inside
  <repo>/results/objective2/s2 unless its first component under that directory is `fr`. Reuse fr_inputs.py's
  `_under`/`out_refusal` logic, with the case-variant and symlink handling of F9. Self-test rows: --out .../s2/c3 and
  .../s2/c1/x refused with nothing written; .../s2/fr accepted.

## Order of work

R4-2 first (operator-facing), then R4-3, then R4-1. Then every regression command and self-test, and the mutants of
the round-4 blinding harness (C1-C3) and the round-4 regression harness (the archive demo) against a fresh copy that leaves out blinded paths.

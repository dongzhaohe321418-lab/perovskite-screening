# E implementation: the analyst's rulings after E's two review rounds (2026-11-12)

Basis: workflow wmz6ceu0b (engineers A-C, three reviewers per round, fix rounds 1-2). Round 2 ended with no critical
or major finding. Twenty-six minor findings were fixed. The rulings below settle every item the fix reports and the
traceability note (C-1 to C-5, R-1 to R-6) left to the analyst. No value was read to make any of them. E_DECISIONS_R1.md
stays in force.

## Rulings that change E's code (applied in the integration round, in W)

- **ER2-1 (RF-25 scope).** The item-4 label also covers the C1 gate statistics of A1 E_b that block 3 prints. These are
  gate N's `sigma_far_meV` rows (B3.gateN.*) and XC-GATEN-SIGMA, and the pose gate's `a_pose_meV`, `delta_near_meV`
  and `delta_far_meV` rows (B3.pose.gate.*) and XC-POSE. Set `has_a1=True` on them and add them to C4's pinned set.
  Reason: each is a spread or a difference of A1 E_b, so it is no better validated than an A1 E_b is. Labelling more
  is the conservative reading.
- **ER2-2 (double label on the Pb76 quartet).** On an FR-pass route, a row that carries L_FAR ("far quartet invalid
  (check 5, VB76); …") does not also carry L_FRVALID. On FR-fail routes it keeps L_ITEM4 beside L_FAR, since both
  statements are true there. XC-DSUM-FAR, the cross-check of δ_far(Pb76), carries L_FAR as B1.delta does. Reason: the
  plan's FR-pass label lists only A1 E_b values (S2B:623-631), and δ_far(Pb76) is not among them. Printing "valid"
  beside "not valid" on one value invites a misreading. E_b^A1(Pb76) itself (B1.EbA1) keeps L_FRVALID on FR-pass
  routes, as the plan states.
- **ER2-3 (item-7 fallback labels).** The fallback adds the labels blocks 1-2 attach to the same values. These are
  L_FAR on `result.Eb_A2_meV.far` from both K3 files, and L_FR2 on all three `result.FR2.*` values when
  `decision.FR.outcome` is the FR-2 failure. L_FALLBACK stays first.

Each change needs a self-test assertion that fails on the round-2 code.

## Rulings with no code change (recorded in amendment 2026-11-12a, item 11)

- **ER2-4 (STOP before the fr campaign commit; fix-2 finding 4).** E refuses on this route (exit 2, nothing written),
  as fix round 2 made it. Should such a STOP become final, a dated amendment decides what E prints. Reason: on this
  route no fr cell has run, S2B_LAST is undefined and RF-3 cannot be checked. Speculative code for a route with no
  data is not worth its risk.
- **ER2-5 (`--stop-note` with `--hinge`).** Accepted. The hinge run on an FR-STOP route names the same stop note.
- **ER2-6 (phase-0 order).** Accepted. Admission (route, stop note, block 4, verify records, hinge preconditions,
  commits, rerun cause) runs before the imports and integrity checks, so a refusal never writes. This is stricter
  than spec §6.2's order and changes no output.
- **ER2-7 (rerun acceptance).** Kept strict. A rerun cause must be a self-test case that passes on the fixed code and
  fails on the earlier code with an AssertionError or an EIntegrity, and E's files must differ between the two. A
  case that needs a helper the fix introduced must assert on E's behaviour through interfaces present in the earlier
  code (the CLI, the output text, a synthetic archive). Reason: the rerun rule guards against post-hoc changes after
  E's output has been seen. A failure caused only by a missing name shows no defect.
- **ER2-8 (C-1, RF-3 and `commit_history[].to`).** `.to` is a listed non-energy leaf. RF-3 is checked at
  `start_commit`, at `commit`, and at the `to` of every entry from the one that reached `start_commit` onward. The C1
  and C2 entries that `fr/campaign.json` copies are outside the check. `.via` is not listed: the set-aside evidence
  no longer depends on the history (fix round 2, finding 5).
- **ER2-9 (C-2, step-0 evaluations).** "Each fr step-0 evaluation that ran" (amendment item 3) reads "each
  evaluation in force". Attempt 1's files lie under `fr/step0_attempt1/` and are never opened. E lists their names
  only, which the blinding rule permits, to show the set-aside, and prints attempt 1 through
  `decision.fr_step0.attempt1.*`. Attempt 1's step-0 values stay unread, because the fix that caused the repeat
  invalidated them.
- **ER2-10 (C-3).** Accepted. The E figure reads E's named output text for its build assertions only, and draws only
  from the CSVs E writes.
- **ER2-11 (C-4).** The stop note must state "the fr STOP is final". The fr operations note uses this phrase.
- **ER2-12 (C-5, engineer B's deviations 1-6 and 9, and engineer C's `status.<FR label>` meta rows).** Accepted as
  reviewed in rounds 1-2. None changes a value, a reading or a label chosen by a value.
- **ER2-13 (wording).**
  - L_FR1 gains "FR quartet invalid (no final-geometry check, <cell>); reported only; not valid", and its not-run
    variant gains the kinds "not started" and "no configuration".
  - After a final STOP before gate FR, a complete FA188 quartet's values carry "gate FR not evaluated (final STOP in
    fr); reported only; not valid".
  - The header after a STOP names the first FR cell that is not complete: "stopped at <cell> (<stop reason>)".
- **ER2-14 (hinge run).** Accepted, option (a): the hinge run prints every failed block 1-3 cross-check in full, or
  "none failed".
- **ER2-15 (presentation).** The block 4 and 5 stub lines carry no header, since they print no value. "Full
  precision" is the shortest repr of the double, and digits beyond about 1e-8 meV are floating-point noise; the S2b
  result note says so once. The unreachable header fallback (M45) stays.

## Integration (R-2, R-5)

After the fr fix round ends: copy E's six files and the E figure into W, then apply ER2-1 to ER2-3. Re-check the
FR literals (B12) and the step-0 set-aside layout against W's final `scripts/50`. The `.used.<t>[.n]` route files of
R3-4 and R3-10 must not break E's layout or OpenAudit. Then rerun E's full self-test in W.

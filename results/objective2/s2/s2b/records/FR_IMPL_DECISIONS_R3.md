# fr implementation: the analyst's decisions on the round-2 re-review (2026-11-12)

Basis: the round-2 re-review of workflow wcbss1i3q (mutation, regression, blinding-and-plan lenses). All 14 round-2
findings were resolved. One major and eight minor findings remain, plus one info item. Each is decided below. The
round-1 decisions (FR_IMPL_DECISIONS_R1.md, F1-F10, T1-T10) stay in force, except where an item below amends F5.

## Fixes

- **R3-1 (major; fr_inputs D4 identity never shown to fail; mutants Q60, Q61, Q39, Q43).** Fix as the reviewer
  proposes. In the self-test, on a copy of the synthetic node tree, edit one free index of the C1 region file of the
  FR host, and separately one field of the C1 pair file. For each, assert that `write` exits 1 and prints DIFFERS,
  that `fr_inputs.json` has `region_equal` (or `pair_equal`) False, and that `compare` against a good output returns
  1 naming the A-side identity line. Also assert that `compare(out_A, out_64)` returns 1 and names `ranks_expected`,
  so that META_FREE cannot silently absorb the rank count. Each assertion must fail on the corresponding mutant.
- **R3-2 (minor; refused --out trees tested only through the module constants; Q37, Q38).** Pin the literals in the
  self-test: `ARCHIVE_TREES == ("c1", "c2", "c3", "fr")` and `NODE_WORK == "/data/work/s2"`, and add refusal rows built
  from literal paths (`/data/work/s2/fr/d4` and a `.../s2/c3/x` row).
- **R3-3 (minor; leftover rule's outcome and history conditions untested; Q15, Q16).** Add the z29 rows the reviewer
  lists: with campaign_commit, history and fix note unchanged, fr_step0 at pass and at fail_final gives the Stop
  "fr/STEP0_FIX refused" with state.json byte-identical and the file kept; at repeat_pending, a changed `via` or `to`
  of the last history entry gives the same Stop.
- **R3-4 (minor, three reviewers; STEP0_NO_ERROR has no leftover rule). Amends F5.** Mirror `fr_fix_leftover`: a
  STEP0_NO_ERROR is the leftover of the applied route when fr_step0 is fail_final with `no_error_found` True, its note
  equals the file's text `.strip()[:300]`, and STEP0_FIX is absent. `fr_route_files` admits it, and the start renames
  it `.used.<t>` with no state change and one campaign.log line saying so (no value, hygiene-clean). Any other
  STEP0_NO_ERROR at a state other than fail_pending_fix stays a Stop, and its message must be accurate (it must not
  say "nothing was recorded" when the state shows the route applied). Test both crash windows in z31 as z29 does for
  STEP0_FIX: a start cut before its save leaves state.json byte-identical and the file kept, and the next start
  completes; a start cut after its save leaves a leftover that the next start renames with no state change.
  Reason for amending F5: F5's purpose is that no route file is ever unapplied or ambiguous; a leftover of an applied
  route is neither, and the same crash class was closed for STEP0_FIX in round 2.
- **R3-5 (minor; N-FR4 key isolation tests only campaigns.c2; Q47).** Add rows to z29's protected-change tuple:
  campaigns.c3 to 'running', campaigns.c1 to 'running', and an added campaigns.c4. Each must be named in the N-FR4
  Stop, with state.json byte-identical.
- **R3-6 (minor; fa_needs_exchange never tested with an FA failing both readings; Q36).** In t_check5_invariant, add
  a gated FA whose carbon moves 0.30 A, and one whose rotation exceeds 20 deg both as written and exchanged. Assert
  that neither is in fa_needs_exchange, that check 5 fails under both readings, and that invariant_only is False.
  The default (non-exchange) output must stay byte-identical.
- **R3-7 (info; recovered STEP0_FIX route leaves no campaign.log line).** Log one line in the leftover branch (the
  applied route's leftover renamed, repeat_pending since the last history entry's time). In fr_step0_repeat, log the
  directory the attempt-1 files actually went to, or that they had already been moved aside; never name a directory
  that was not created. Lines carry no value and pass the hygiene check.
- **R3-8 (minor; the scripts/49 run CLI output is not covered by a blinding test; K1, K21).** In t_fr, add a CLI
  case with stdout and stderr captured: run `main(["run", "--gate", g, "--campaign", "fr", ...])` for fr_step0 and FR
  with a result holding every WITHHELD_S2B field set to sentinel values, and the gate file written to a temporary
  path; add one refusal per FR-2 and step-0 GateRefused path with sentinel F planted. Assert that no WITHHELD_S2B
  name and no sentinel value appears in the captured output. Each assertion must fail on K1 and K21.
- **R3-9 (minor; the STEP0_NO_ERROR text is not hygiene-checked).** In the fr branch of preconditions, before any
  save, Stop when `c46.hygiene_violations(text)` is non-empty. The Stop names fr/STEP0_NO_ERROR and the rules broken
  (not the offending text), with no state change and no rename. Add a z31 row with a dollar sign and one with an IPv4
  address in the note. C2's path stays unchanged (C2 is done; its code stays byte-identical).
- **R3-10 (open risk of round 2; `.used.<t>` names made in the same second overwrite each other).** On the fr route
  files only (CAMPAIGN_COMMIT, STEP0_FIX, STEP0_NO_ERROR), never overwrite an existing `.used.<t>`: choose the first
  free name `.used.<t>`, `.used.<t>.1`, `.used.<t>.2`, ... Test it with a pre-existing `.used.<t>` at a fixed clock.

## Not changed

- The c1-c4 refusal without a readable state.json (round-2 item 10) stays: N4 sends any C1-C4 start to 8bff03e.
- The casefold over-refusal of `--out` on the node's case-sensitive volume stays (fail-closed).
- Q32 is equivalent (the only caller of fr_scan requires `not a2_stopped()`); no test.

## Order of work

R3-1 first (the only major). Then R3-4 and R3-9 (runner behaviour), then the test items. After the edits, run every
regression command and self-test, and the previous mutation harnesses (the round-2 mutation and blinding harnesses) against a fresh
copy that leaves out blinded paths: every survivor named above (Q15, Q16, Q36, Q37, Q38, Q39, Q43, Q47, Q60, Q61, K1,
K21) must now be caught.

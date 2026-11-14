# S2b campaign commit: integration rulings (2026-11-12)

Basis: E (workflow wmz6ceu0b, rulings E_DECISIONS_R2.md), the §6b FR geometry read (fr_geom_read.py), the FR figure
(FIG_DECISIONS_R3.md) and the fr runner (FR_IMPL_DECISIONS_R1/R3/R4.md) now sit in one tree, W. No value was read to
make any ruling below.

## IX-1. One definition of a final STOP of fr

E (ER2-11, OP-19), the FR figure (FG-2) and the §6b read must agree on when a STOP of fr is final. The rule is E's: a
STOP is final only through a stop note, a committed, clean, dated note under results/objective2/s2/ (not under
s2b/) that states "the fr STOP is final" (`e_eval.stop_note_ok` and `e_eval.Run.note_ok`).

- **fr_geom_read.py** replaces its bare `--final-stop` flag with `--stop-note NOTE`. On fr status 'stopped' the read
  requires a valid stop note (the same three tests as E: path rule, phrase, ISO date; committed and clean, text from
  HEAD); the header records the note's path and sha256 in place of "(--final-stop: FR's final stop)". A stop note on
  status 'done' is refused, as `--final-stop` on 'done' is now. The self-test gains: 'stopped' with no note, with a
  note lacking the phrase, with a note under s2b/, with an uncommitted or edited note (each refused, exit 3, nothing
  written), and with a valid note (read, header with sha256). The phrase and rules are pinned against e_eval.py.
- **The FR figure**: FG-2.
- **The operations note** states the order on every route: verify, then the §6b read, then the FR figure build, then
  E; on a STOP, the stop note is committed first and the same note is passed to all three.

## IX-2. Integration checks owed by E (E_DECISIONS_R2, Integration)

After ER2-1 to ER2-3, recheck against W's final scripts/50 and scripts/49: the FR literals of E (B12: cell labels,
FR order, gate names, outcome strings, the 50 meV bound), the step-0 set-aside layout (fr/step0_attempt1/{gates,
gates_applied}/ and the node's discarded/step0_attempt1_<t>/), and the `.used.<t>[.n]` names of R3-4 and R3-10 for
CAMPAIGN_COMMIT, STEP0_FIX and STEP0_NO_ERROR, which E's layout checks and OpenAudit must accept and never open. Each
mismatch is fixed in E with a self-test assertion that fails on the old code.

## IX-3. Concurrency in W

Four engineers edit disjoint files of W at once: the runner (scripts/49, scripts/50), E (s2b/e_*.py,
figures/fig_s2b_e_fk.py), the FR figure (figures/fig_s2b_fr.py) and the §6b read (c2_diagnostic/fr_geom_read.py).
None edits another's files. A self-test failure that traces to another engineer's file is rerun after a pause and
reported, never fixed across the boundary.

## Rulings on review round 1 (binding on fix engineer 1)

Basis: review 1 of workflow wt1moq84t (blinding, plan and cross-tool lens; regression lens), the operations-note
writer's report (draft 2), and the round-4 mutation review of workflow w739j3tt0. No value was read to make any ruling
below. Fix engineer 1 applies IX-4 to IX-9 and FR_IMPL_DECISIONS_R5.md together with the review-1 findings. Where a
ruling below decides a finding, the ruling governs. Every code change needs a self-test assertion that fails on the
code before it (a revert mutant).

- **IX-4 (major; a final STOP after a recorded FR outcome).** S2B §1 counts "a final STOP in fr" as "FR fails",
  whatever gate FR recorded before the STOP. Option (a) of the finding is adopted, as follows.
  - **E.** On every route with fr status 'stopped' and a valid stop note:
    - item4 is L_ITEM4, never L_FRVALID;
    - FR is not counted among the valid far references.
  - **E's header** on such a route:
    - If gate FR or the step-0 final (STEP0_NO_ERROR) was recorded before the STOP, the header names that decision
      in the plan's words, then the STOP:
      - "fail (FR-1, <cell>, <reason>); then a final STOP (<stop reason>)", where <cell> is the cell gate FR
        recorded;
      - "fail (FR-2); then a final STOP (…)";
      - "fail (step-0 final; gate not evaluated); then a final STOP (…)";
      - "pass at gate FR; then a final STOP (…); counted as FR fails (S2B §1)".
    - Otherwise ER2-13 stands: "stopped at <first FR cell not complete> (<stop reason>)".
  - **The FR figure** draws the same decision, cell and reason, and the same STOP. On a recorded pass, its FR state
    reads as E's header does, never "pass" alone.
  - **The §6b read** is unchanged.
  - **Self-tests.** E and the figure each gain synthetic stopped-fr scenarios with a valid note:
    - gate FR recorded as FR-1 fail at a cell (end rule);
    - FR-2 fail;
    - pass;
    - STEP0_NO_ERROR then a STOP.
  - **Pin.** The figure's self-test loads W's e_eval, as `_pin_e_eval` does, and asserts on the same archives that
    E's header FR part and the figure's FR state name the same decision, cell and reason.
  - **Operations note.** A STOP whose cause can be cleared is relaunched to CAMPAIGN_DONE. A stop note is written only
    for a STOP that cannot be cleared. After a gate FR pass it turns the pass into "FR fails".
  - Recorded as amendment 2026-11-12a item 13.
- **IX-5 (minor; "step-0 repeat prepared, not recorded").** The figure follows E. On a stopped fr, it accepts
  fr/step0_attempt1/ without a STEP0_FIX history entry under exactly the conjuncts of E's s0_set_aside, and draws the
  step-0 row as "repeat prepared, not recorded". Add one scenario, pinned against E on the same archive. The
  operations note says this route is relaunched, since the runner's R3-7 path completes the repeat, rather than made
  final.
- **IX-6 (minor plus the operations-note loophole; the stop-note path).** One fixed path,
  `results/objective2/s2/FR_STOP_NOTE.md`, is the only stop note any reader of fr accepts.
  - **Constant.** E holds it as a constant beside STOP_PHRASE; the figure and the §6b read pin it against E.
  - **Refusals.** Any other path is refused, each tool by its own convention (E exit 2, the §6b read exit 3, a named
    need() in the figure), with nothing written.
  - **Tests that stay.** Tracked; clean; text read from HEAD; the phrase; an ISO date. In addition, `git cat-file -t
    HEAD:<path>` must print "blob".
  - **Self-test rows.**
    - Refused: S2B_PLAN.md and FR_OPERATIONS.md, each holding the phrase on one line with a date; a glob path such as
      `results/objective2/s2/FR_STOP_NO*.md` with the fixed file present.
    - Accepted: the fixed path.
  - **Effect.** This closes the glob finding, and the loophole that S2B_PLAN.md (amendment item 12) or the operations
    note would pass as a stop note. The operations note may then carry the phrase on one line.
  - Amendment item 12 is amended to name the path.
- **IX-7 (minor; `--stop-note` on a done fr).** E refuses it (exit 2, nothing written), as the figure and the §6b read
  do. Add a D-group case.
- **IX-8 (minor; the verify output).** In scripts/49 `t_fr`:
  - capture stdout and stderr of both verify calls and assert the exact line lists;
  - add a mutant that prints inside verify for an FR gate;
  - confirm that mutants N4_02, N4_03 and N4_04 of the round-4 mutation harness are caught by R4-1's pinned output.
  verify_fr.txt is published before E, so its text must be pinned as fully as the run output is.
- **IX-9 (information state; part_d_read and c1/structures.tar.gz).**
  - **What happened.** Two agent runs executed `part_d_read.py --self-test` in W, which links the real c1 through the
    committed blinded loader:
    - the round-4 regression run;
    - the integration round's runner and §6b engineers.
    The analyst read the round-4 log (664 bytes). It holds the two pass lines and rc=0, with synthetic test numbers
    only. No value was read.
  - **Plan.** The plan permits c1/structures.tar.gz through committed tools. The S2b result note records these runs
    in its information state.
  - **From now on.** Agents run only fr_geom_read's five cases that need no C1 archive. The analyst runs the full
    fr_geom_read and part_d_read self-tests.
  - **Code.** No change, except that the `--without-wp2e` docstring must say that it still reads the real C1 structure
    archive through part_d_read's loader.
  - The figure's QA imports from the external nature-figure toolkit stay, as for the C1 and C2 figures. The operations
    note lists the toolkit as a dependency of the figure self-tests.

## Rulings on fix round 1 and review round 2 (2026-11-13; binding on the round-3 fix engineer)

Basis:
- the fix-1 report and its five items for the analyst;
- review 2 of workflow wt1moq84t (23 findings over four lenses);
- fix engineer 2's partial edits, left when the laptop slept.

No value was read to make any ruling below. The numbers F1 to F23 refer to the list of 23 findings given to fix
engineer 2.

- **IX-10 (fix-1 item 1; `fr_outcome` at a STOP).** Approved.
  - **What the runner records.** `Runner.begin_stop` records `fr_outcome` in fr/campaign.json at every STOP of fr.
    The value is the outcome the recorded decisions already fix (gate FR applied, or the step-0 final), and null
    otherwise. C1–C4 are unchanged.
  - **What it is.** A decision label, never a value. E and the figure read it as a listed non-energy leaf.
  - Recorded in amendment item 13.
- **IX-11 (fix-1 item 2; F1, F6, F12; "repeat prepared, not recorded" at either step-0 cell).** IX-5 is extended to
  @2.
  - **Acceptance.** At each cell, the figure accepts a repeat prepared but not recorded under exactly the conditions
    on which E accepts it at that cell: at @4, E's s0_set_aside; at @2, the conjuncts of E's rf12_step0 and block 2.
  - **Drawing and pin.** The figure draws "repeat prepared, not recorded" and is pinned against E on the same
    archive, at both cells.
- **IX-12 (fix-1 item 3; labels on "pass at gate FR; then a final STOP").** A new label, L_FRSTOP: "gate FR passed,
  then a final STOP in fr (S2B section 1); reported only; not valid".
  - **Which values.** On that route, every FR-quartet value E prints that carries no item-4 label carries L_FRSTOP
    instead of L_FRVALID or no label. This covers E_b^A2(FA188) and the three result.FR2 values.
  - **A1 values** keep L_ITEM4.
  - **The figure** prints no value, so it is unchanged.
  - **Test.** The C1v pass variant asserts the label on each such row, and a mutant that drops it is caught.
- **IX-13 (fix-1 item 4; new fixed strings).** The analyst lists every new fixed string verbatim in amendment item 14,
  from the final code. The round-3 fix engineer's report lists them all, with file and line: labels, header
  templates, row names, refusal and Stop texts, and log lines.
- **IX-14 (F2; a STOP before the fr campaign commit).** All three readers refuse it, as E does under ER2-4. The
  figure and the §6b read refuse with nothing written. Each has a self-test row, pinned as IX-6 is.
- **IX-15 (F3; gate FR written but not applied, the N-FR8 or N-FR4 "not applied" Stops).**
  - **What the route means.** It shows a disagreement between the runner and the gate, which is a defect. It is
    resolved by a dated fix and a relaunch, never by a stop note.
  - **Refusals.** On a stopped fr whose gates/FR.json exists without its applied copy, E and the figure refuse with
    a named refusal and nothing written. E may keep INT-STRUCT if nothing is written. The §6b read refuses too.
  - **Existence test.** It is by name only (`os.path.exists`); the gate file is never opened.
  - **Tests.** Self-test rows in each tool. The operations note states the route.
- **IX-16 (F4, F8, F9; pins between the figure, E and the runner).**
  - The figure's E_REASON words and its 'check' reason are pinned against E, by loading E's source with `ast`.
  - The "FR step-0 repeat prepared" log line the figure parses is pinned against scripts/50.
  - A mutant on either side must be caught.
- **IX-17 (F5, F7, F10, F11).** Fixed as the findings propose, each with a failing-on-old assertion.
- **IX-18 (F13–F23; the operations note).** Draft 3, `FR_OPERATIONS_DRAFT3.md`, is written from draft 2 after the code
  is final. It carries:
  - IX-4 to IX-17, including:
    - the one stop-note path `results/objective2/s2/FR_STOP_NOTE.md`, whose phrase may now stand on one line;
    - a STOP whose cause can be cleared is relaunched, not made final;
    - the unrecorded repeat is relaunched;
    - the "not applied" Stops are fixed and relaunched;
    - `fr_outcome` at a STOP.
  - Route 7 of §8 keyed on the decisions and the stop note. C3b starts only after FR passes and fr ends done.
  - Step-0 diagnosis from inputs only: fr_inputs compare, D1–D4, the pw.x input files, and the value-free log lines.
    A diagnosis that needs an output waits for E.
  - The gates.log reading rule, made one an operator can follow without reading the exception message.
  - The archive command with `--stage` and the pull layout.
  - What verify_fr.txt shows, including the expected gate FR digest difference on IX-4 routes.
  - The figure's unguarded reads, and the toolkit dependency.
  - The A2-record reading route.
  - The dry-run check, defined as C1 and C2 used it: a dry-run rsync after the pull that lists no difference.
  - Fresh provenance (the final sha256 of each tool) and a consistent D1.

**Partial fix-2 state.** Fix engineer 2 died with edits in four files of W, made after its snapshot
of W at the fix-1 state (a private copy):
- scripts/50: F10 rows;
- e_selftest.py: F5, F7, F11;
- fig_s2b_fr.py: F1, F2, F9;
- fr_geom_read.py: F2.
None of these was verified. The round-3 fix engineer diffs W against that snapshot and audits every edit. It
completes or reverts each, then finishes the rest.

## Rulings on review round 3 and fix round 4 (2026-11-13; the analyst, before the S2b campaign commit)

Basis: workflow wd4iffpgl (fix 3; reviews 3 over the regression, blinding and test-strength lenses; operations note
draft 3 and its review; fix 4; verification). Fix 4 resolved R2, R4-R6 and R9-R17 and left two decisions; the
verification confirmed them and found one test defect. No value was read to make any ruling below.

- **IX-19 (R1, R8; the route after a "not applied" STOP).** Option (b): such a STOP is not evaluated at this commit.
  - **Scope.** Every STOP at which a gate file was written by scripts/49 and the runner stopped before applying it:
    gate FR (N-FR4, N-FR8) and the fr_step0 gates at @2 and @4 (IX-20).
  - **What follows.** The operator stops. There is no relaunch, no route file and no stop note. Nothing in the fr tree
    on the node is changed, no fr archive is committed, and none of the three readers runs. FR stays unevaluated
    until a dated amendment of `S2B_PLAN.md`, written before any fr value is read, rules on the route. That amendment
    may admit a reviewed fix commit and the runner route that relaunches it.
  - **Why (b).** The route shows a defect: the runner and the gate disagree. The runner and gate code pass 66 and 17
    self-test cases, and the disagreement checks are mutation-tested. A runner route for a defect that should not
    occur would cost another review round now, against a cost of zero unless it occurs; it would then be built
    against the actual defect.
  - **Texts.** The readers' refusal texts ("resolved by a dated fix and a relaunch, never by a stop note") stay as
    written: the dated amendment is what admits that fix and relaunch. IX-15 and IX-18 ("fixed and relaunched") are
    read with this ruling. Recorded in amendment item 14.
- **IX-20 (R3, R7; fr_step0 written but not applied).** No refusal by name in the readers at this commit.
  - **Why.** A name-only test exists: at @2, `gates/fr_step0.json` without `gates_applied/gate_fr_step0_2.json`; at @4,
    `gates_applied/gate_fr_step0_4.inputs.json` without `gate_fr_step0_4.gate.json`. But a step-0 gate that did not
    complete leaves the same names. A refusal by name would also bar that STOP from being made final, where its cause
    cannot be cleared.
  - **The defence instead.** The stop note is written by the analyst. Before writing it, the analyst lists by name
    (never opening) `fr/gates/`, `fr/gates_applied/` and the attempt-1 markers, and reads the stop reason through the
    filter of D-C2-5. A "not applied" reason, at any gate, goes to IX-19 and never receives a stop note. The
    operations note gives the check and states the real trade-off. Recorded in amendment item 14.
- **IX-21 (fix 4's R17 deviation).** Confirmed. A step-0 STOP and an unrecorded step-0 repeat are relaunched. They
  are made final only when their cause cannot be cleared, with the reason in the stop note. This matches IX-4 and
  IX-11 and supersedes IX-5's and IX-18's "is relaunched".
- **IX-22 (fix 4's R9 deviation).** Approved. On the held end-rule STOP route only, after verify, the operator may
  read the two flags `end_rule.stop` and `end_rule.stop_raised` of the failing cell's A2 record through GuardedS2b.
  Both are booleans and carry no value. They show that `mark_stop_raised` rewrote the record, which is the expected
  digest difference of D-C2-6. Recorded in amendment item 14.
- **IX-23 (the verifier's finding; `src_patched`).** Fixed by the analyst (test code only). `src_patched` raises
  `MutantNotApplied`, and `run()` counts such a mutant as a failure ("NOT APPLIED"), never as caught. Checked with the
  verifier's mutant SP01, a rewrite of e_eval.py with the same meaning: C1q now reports
  "aside_at4_only: NOT APPLIED", and the suite exits 1.
- **IX-24 (IX-13 made proportionate; the code's ruling codes).**
  - **Item number.** IX-13's "amendment item 14" is item 15. Item 14 holds the routes (IX-11, IX-14, IX-15, IX-19 to
    IX-22).
  - **What is listed verbatim.** Amendment item 15 lists, verbatim, the new strings that label or head E's output or
    name a route in it: labels, header templates and route rows. The other new strings (refusal, Stop, need() and log
    texts) are fixed by the campaign commit itself, which comes before any fr value. Item 15 cites them by file and
    function.
  - **The design records are published.** The code cites rulings by code (IX-, OP-, RF-, ER2-, FG-, R3- to R5-, D-C2-).
    So the records that define them are committed beside the code, under `results/objective2/s2/s2b/records/`. These
    are the E and fr implementation specifications and the E, figure, fr and integration decisions. The operations
    note is committed as `FR_OPERATIONS.md`. Only the lines that name agents' work areas or local paths are reworded,
    and a README says which. All were written before any value they govern was read.
- **Observation (analyst's visual check of the 41 synthetic FR figures; no change).** On a done fr, the FR figure's
  gate-FR state names the kind ("fail (FR-1): V, check"), and its detail column lists the failed checks ("V: final
  geometry fails check(s) [5]"). E's header and the figure's STOP-route state name the reason ("check 5"). Both are
  accurate and pinned by their self-tests. A change to the figure's state words and pins now carries more risk than
  its benefit, so it is left as it is. The FR note quotes E's header.

## Rulings on the final text review (2026-11-14; the analyst, before the S2b campaign commit)

Basis: two independent reviews of amendment items 13-15, the operations note and the published records, by the lenses
"records and publication safety" (workflow wury8rte0) and "amendment against the code" (workflow w2me8fvbn). No value
was read to make any ruling below.

- **IX-25 (corrections).**
  - **IX-12.** L_FRSTOP is carried by E_b^A2(FA188) in block 2 and by `result.FR2.Eb_A2_meV` wherever E prints it
    (XC-FR2 for both gate-FR files, and the item-7 fallback). `result.FR2.Eb_A1_meV` and `result.FR2.delta_far_meV`
    keep the item-4 label. "The three result.FR2 values" in IX-12 was wrong; the code was right.
  - **IX-20.** The stated reason holds at @4 only. At @2, a step-0 gate that did not complete leaves no
    `gates/fr_step0.json` (scripts/49 writes it last), and a "not applied" STOP there is an integrity failure for E
    (RF-12). The @2 case is left to the analyst's check, so that both cells are treated alike.
  - **Records.** The published records reword every agent work area and harness name, and keep the workflow-run ids
    for traceability. The README says that review-finding, mutant and code-map ids are defined only in the private
    reports. It also distinguishes the older "round-3/round-5" R-codes of scripts/50, and places the D-C2- codes in
    `C2_OPERATIONS.md`.
  - **Code comments.** Two comments in `e_eval.py` that cited L_FRSTOP as "amendment item 14" now cite item 13. E's
    full self-test, the FR figure's self-test and both §6b runs are repeated on the changed file.
  - **Amendment.** The header's basis and precedence now cover §§1, 2, 6b, 7 and 11. Item 13 states where L_FRSTOP
    applies and how a pass is named. Item 15 adds the done variant of B2.step0.no_error and the fallback lines.
- **IX-26 (the later amendment after a "not applied" STOP; refines IX-19).**
  - **The risk.** An N-FR8 reason names gate FR's outcome, cell and kind. A fix that chooses which side, runner or
    gate, has the defect may therefore decide FR's outcome, and the analyst would write it knowing which choice gives
    which outcome.
  - **The rule fixed now.** The later amendment may only:
    - admit a fix shown by a synthetic self-test case that fails at the campaign commit and passes on the fix,
      through interfaces present at the campaign commit (as item 11 requires of E's reruns), with the defective side
      decided by §§1-2, the amendment and the code's specification and never by the FR outcome; the relaunch evaluates
      the gate again, and that decision stands;
    - or make the STOP final, so that FR fails.
  - **Backstop.** If neither has been committed 60 days after the STOP, the STOP is final and FR fails (§1).
  - **The unevaluated state** is a state of §1 in which no route applies and E may not run. Recorded in amendment
    item 14.

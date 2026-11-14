# S2b campaign fr: operating decisions, recorded before fr starts (2026-11-14)

`fr` is the far-site reference FR of `S2B_PLAN.md` §2: the Cs quartet at m30 FA188. This is the operations note that
`S2B_PLAN.md` §1 and §9 step 3 require before the campaign. It is committed as `results/objective2/s2/FR_OPERATIONS.md`
at the S2b campaign commit, together with the runner code, the §6b tool, E's code and the FR figure, before fr starts
and before any fr value exists. It re-adopts `C2_OPERATIONS.md` (OPS2) for fr in substance and states, provision by
provision, what is kept, adapted or superseded. It cannot change any rule of `S2B_PLAN.md`; where the two differ,
`S2B_PLAN.md` and its amendment 2026-11-12a govern.

**Basis.**
- An implementation specification drafted from the code at `4d27d2d`, the runner, gate and node changes built from it,
  and four rounds of adversarial code review (regression, plan conformance and blinding, test strength by injected
  mutations).
- **Separate deliverables before the FR boot** (S2B §9 step 3), each with its own self-tests and review: the FR
  geometry-read tool of §6b (`c2_diagnostic/fr_geom_read.py`), E's blocks 1-3 and 5 with the block-4 stub and the
  E figure (`s2b/e_*.py`, `figures/fig_s2b_e_fk.py`), the FR figure (`figures/fig_s2b_fr.py`), and amendment
  2026-11-12a of `S2B_PLAN.md`, which settles the points of §7 that E's code needs and is committed before that code.
- **Integration.** The four parts were integrated in one tree. Three integration reviews followed (blinding, plan and
  cross-tool consistency; regression and integration; test strength by injected mutations; this note), with four
  rounds of fixes. Twenty-six integration rulings, IX-1 to IX-26, decide the findings of these reviews and of a final
  review of the amendment, this note and the published records. The route after a "not applied" STOP is ruled by
  IX-19, IX-20 and IX-26 (§2, D-C2-3). This note carries the rulings that bind
  operations:
  - one definition of a final STOP for the §6b read, the FR figure and E: one stop note at one fixed path, refused on
    a done fr (IX-1, IX-6, IX-7; §8);
  - a final STOP after a recorded FR outcome is "FR fails" (IX-4, IX-12);
  - the step-0 repeat prepared but not recorded, at either step-0 cell (IX-5, IX-11);
  - `fr_outcome` recorded at every STOP of fr (IX-10);
  - the readers' refusals of a STOP before the campaign commit and of gate FR written but not applied (IX-14, IX-15);
  - a "not applied" STOP of any gate is not evaluated until a dated amendment rules on it under a rule fixed now,
    with a 60-day backstop after which FR fails; and the analyst's check before a stop note (IX-19, IX-20, IX-26);
  - a step-0 STOP and an unrecorded repeat are relaunched unless their cause cannot be cleared (IX-21);
  - the operating rules of IX-18 and IX-22 (§§2, 3, 5 and 8).
- The specifications and the rulings that the code cites are committed under `s2b/records/` (IX-24); the reviews are
  kept in the private record folder. The analyst, who was delegated by the PI on 2026-11-03, decided every open point.

**Information state.** Everything that `S2B_PLAN.md` §0 lists as known, and the G2 output
(`c2_diagnostic/g2_output.txt`, commit `4d27d2d`). The FR geometry read (§6b) has not run. Every choice in this note was
made knowing G2. None of them selects a cell, a reading, a tolerance or a gate; those are fixed by `S2B_PLAN.md`.

Labels: [I] marks the analyst's inference or arithmetic. [R] marks a recorded result, with its file. [C] marks a
statement about the code at this commit, with the function and, where one exists, the runner note (N-FR1 to N-FR8 of
`scripts/50`).

## 1. What fr runs

- **Commit.**
  - fr runs at the S2b campaign commit, the commit that adds this note. The runner admits it once, through
    `fr/CAMPAIGN_COMMIT`, written as `<40-hex commit> <YYYY-MM-DD> results/objective2/s2/FR_OPERATIONS.md`
    [C: `scripts/50` `check_commit_s2b`, `s2b_route`; N-FR2].
  - The checks: three tokens; the commit equal to HEAD; the date in the form YYYY-MM-DD; the note a relative path under
    `results/objective2/s2/`, tracked, changed between `8bff03e` and HEAD, and containing the date; `8bff03e` an
    ancestor of HEAD; `qe_queue.sh`, `chain.sh` and `s2_run_qe.sh` unchanged from it; C2 done; the line clean under the
    hygiene check of `scripts/46`. A refusal is a STOP that names every reason and records nothing [C: `s2b_route`]. It
    is cleared by removing every reason it names (a corrected line, a clean checkout or a new commit, as the reason
    requires) and a relaunch (§2, D-C2-3).
  - The date token must therefore occur in this note: it is 2026-11-14, the date in this note's title.
  - `state.commit` stays `8bff03e`, the C1 and C2 commit. `campaign_commit.fr` and a `commit_history` entry (with `via`
    and `campaign`) record the new one, in one save, before the file is renamed [C: `s2b_accept`]. `fr/campaign.json`
    then records it as `commit`, and as `start_commit` from its first save after it [C: `set_campaign`].
  - After that, a new HEAD is accepted only through `fr/STEP0_FIX`, after a failed step-0 check (§2, D-C2-2). No
    other route admits one at this commit (§2, D-C2-3) [C: `check_commit_s2b`, `fr_route_files`].
  - At this checkout c1-c4 cannot be started. A c1-c4 start returns 2 and writes nothing, before the lock, any
    directory or any log line, when C2 is done and HEAD is not `8bff03e` (or git fails), and on the node also when
    `state.json` cannot be read [C: `s2b_refusal`, `run`; N-FR3].
  - `ehpc/node/s2_campaign.sh` starts fr only; any other id is a usage error, exit 2. `s2_relaunch.sh` knows all five
    ids (c1-c4 and fr), but it starts the running campaign through `s2_campaign.sh`, so at this checkout it can
    relaunch only fr. Any c1-c4 action needs a checkout at `8bff03e`.
- **Relaxations.** Four, one at a time, at the A2 layout recorded in the state (64 ranks [R: `C1_RESULT.md` §3.5]; a
  2x32 layout is a STOP [C: `preconditions`; N-FR1]), in this order (`FR_ORDER`):
  1. host_R(A188), from the S2-relaxed host;
  2. V⁺_R(A188), then its checks 2, 4 and 5 against host_R;
  3. Cs D(A188), then its check against host_R;
  4. Cs D+V⁺(A188), then its check against V⁺_R.
- **Early stop** [C: `scripts/49` `fr_progress`; `scripts/50` `fr_scan`, `a2_phase`; N-FR1, N-FR5].
  - A cell starts only after the check of the cell before it is recorded. `fr_progress` names the next cell at every
    tick, and only that cell is launched.
  - The first cell that ends without acceptance, ends without a final-geometry check, or fails its check ends FR. The
    runner writes `fr_stop` {at, kind} once, also when the last cell fails in the gate phase. Every cell not started is
    recorded as not_run_gate, with the reason "FR early stop at <cell> (<kind>; S2B section 2)".
  - After a hard-cap refusal the refused cell keeps its not_started_cap record and the later cells are not_run_gate.
- **Check 5.** Every fr §11 check runs with the invariant reading of S2B §2 (X4), which decides. The record also keeps
  the reading as written and flags a pass that needs the invariant reading; any other reading is a STOP
  [C: `run_a2v`; `scripts/46` `validity_a2`; N-FR7].
- **The graph** has 11 jobs besides the runner's two node checks (UPF and node scripts): 4 relaxations, 4 §11 checks
  and 3 gates [C: `graph_fr`, `expected_counts`].
- **Gates, applied by the node as they fall.**
  - `fr_step0` at k = 0 of V⁺_R(A188) (@2) and of Cs D+V⁺(A188) (@4), against the C1 single points `s2_m30_VA188` and
    `s2_m30_Cs188o0_vac`, with the tolerance |dF| ≤ 0.5 meV [C: `scripts/49` `FR_STEP0_PAIRS`, `step0_eval`;
    `scripts/47` `STEP0_TOL_MEV`]. Each evaluation takes exactly one cell.
  - `FR` after the four checks: FR-1, then FR-2 only if FR-1 passed. FR-1 passing without the step-0 pass at D+V⁺ is a
    refusal, which the runner turns into a STOP. A missing FR-2 value is a refusal too; FR-2 passes only at
    |δ_far(FA188)| ≤ 50 meV [C: `scripts/49` `evaluate_gate` (FR), `fr2_eval`, `fr2_decide`].
  - FR is not evaluated when step-0 is final (X6): `gate:FR` is then skipped, and `scripts/49` refuses it as well
    [C: `scripts/50` `status`; `scripts/49` `evaluate_gate`; N-FR8].
  - An fr gate decision that disagrees with `fr_stop` (gate FR), or that holds a key or field outside the decision
    lists (either gate), is a STOP before it is applied: a "not applied" STOP (§2, D-C2-3 and D-C2-5)
    [C: `run_gate`, `s2b_decision_check`; N-FR4, N-FR8].
- **Cost** [I; S2B §8].
  - 22-58 node-h for the four relaxations, 6-29 node-h if FR stops at host_R or after the V⁺-host pair, and up to 72
    with a step-0 repeat. A relaxation of the 201 configurations allowed takes at most 15.6 h at the C2 maximum of 4.65
    min per configuration.
  - The remaining S2 budget is 428.1 node-h against the 520 node-h hard cap.
  - The estimate is updated from each relaxation's measured wall time (§4).

## 2. OPS2 provisions for fr

- **D-C2-1 (no code change): kept in substance.** No recorded suggestion of `STAGE0.md` §7 is applied. The only code
  changes are those of the S2b campaign commit; the changes to `scripts/46`, `scripts/47` and `ehpc/` are listed in §5.
- **D-C2-2 (after a step-0 STOP): adapted.**
  - A failure kills the running part and STOPs with a message that names both routes [C: `run_gate`; N-FR6]. After it
    the operator never starts fr plainly. A start at `fr_step0` fail_pending_fix without a route file is itself a STOP
    [C: `preconditions`], so the one repeat that S2B §2 allows cannot be lost by accident. A step-0 STOP is relaunched
    through one of its two routes. It is made final, by a stop note, only when D-C2-3 finds that its cause cannot be
    cleared through either route: for example, an error that is found but whose fix changes a node script that
    `s2b_route` keeps unchanged (`qe_queue.sh`, `chain.sh`, `s2_run_qe.sh`), so that `fr/STEP0_FIX` is refused and
    `fr/STEP0_NO_ERROR` would be untrue. The stop note then gives the analyst's dated reason [I].
  - The only routes are these two, each with a dated analyst decision:
    - **`fr/STEP0_FIX`**, written as `<40-hex new commit> <YYYY-MM-DD> <note path>`, with the checkout at that commit.
      It passes the checks of `fr/CAMPAIGN_COMMIT` (§1), with `campaign_commit.fr` as the ancestor: the commit must
      descend strictly from it, and the note must be tracked, under `results/objective2/s2/`, contain the date and be
      changed between the two commits [C: `s2b_route`]. It is accepted only at fail_pending_fix.
    - **What the repeat does** [C: `fr_step0_repeat`, `discard_checks`; N-FR6]. The failed cell's `a2/<label>`,
      `gates/fr_step0.json` and that gate's marker trio go to `fr/discarded/step0_attempt1_<t>/`. The node-check
      records go aside, so the UPF and node-script checks run again, first, at the new commit. One save then records
      `campaign_commit.fr`, the history entry, and `fr_step0` repeat_pending with the note and `attempt1`
      {attempts, outcome, cell}. Only then is the file renamed. Only that cell reruns, from k = 0; the other cells keep
      their records. The log line reads "FR step-0 repeat prepared: <cell>: <n> of its 5 attempt-1 paths moved to
      discarded/step0_attempt1_<t>; <cell> reruns from k = 0 (attempt 2)", or says that none was left to move.
    - **What is archived.** The attempt-1 gate file and marker trio are published under
      `fr/step0_attempt1/{gates,gates_applied}/` [C: `archive`]. The attempt-1 A2 directory stays on the node: the pull
      leaves it out (§8) and the archive takes nothing from it. Neither is read before E.
      - E lists the names under `fr/step0_attempt1/gates_applied/` only, and prints attempt 1 through
        `decision.fr_step0.attempt1.*` (amendment 2026-11-12a, item 11) [C: `e_eval` `Run.route_fr`].
      - The FR figure tests the existence of `fr/step0_attempt1/`. On a stopped fr without a STEP0_FIX entry it also
        tests the existence of one attempt-1 marker by its name (@2 or @4). It never opens or lists the folder
        [C: `fig_s2b_fr` `fr_gates`, `set_aside_2`, `set_aside_4`].
    - **`fr/STEP0_NO_ERROR`**, a dated note. The date is the operator's rule; the code checks the text against the
      hygiene rules of `scripts/46`, both as written and as a JSON string. A text that breaks a rule gives the STOP
      "fr/STEP0_NO_ERROR refused: its text breaks the hygiene rules of scripts/46 (<rules>; D-C2-4) (N-FR6); nothing
      was recorded", which names the rules and never the text; the state and the file are unchanged
      [C: `preconditions`]. A clean text sets `fr_step0` to fail_final with `no_error_found` and the note (the
      stripped text, at most 300 characters); one save, then the rename. Step-0 is then final, `gate:FR` is skipped,
      and FR ends as "fail (step-0 final; gate not evaluated)" [C: `preconditions`, `status`, `fr_outcome`].
    - **After STEP0_NO_ERROR,** `gates/fr_step0.json` and its applied copy keep fail_pending_fix. Only the state, and so
      `fr/state_end.json`, holds fail_final with `no_error_found` [C: `preconditions`]. E accepts this on the
      step-0-final route only and prints it as the row `B2.step0.no_error`; the FR figure draws "fail (fail_final: no
      error found)".
    - **STEP0_NO_ERROR, then a STOP.** A STOP publishes no `state_end.json`. The runner's `begin_stop` records
      `fr_outcome` "fail (step-0 final; gate not evaluated)" in `fr/campaign.json` (IX-10). E takes the step-0 final
      from that leaf and prints the stop variant of `B2.step0.no_error`; the figure takes it from the runner's log line
      or from that leaf [C: `begin_stop`, `stop_outcome`; `e_eval` `Run.stop_decision`; `fig_s2b_fr` `fr_gates`].
  - **A repeat prepared but not recorded is relaunched** (IX-5, IX-11). `fr_step0_repeat` moves the attempt-1 paths
    first and saves the state after. A start cut short between the two, or a STOP raised there, leaves the paths
    moved, `fr/STEP0_FIX` in place and no STEP0_FIX entry in `commit_history`. The operator relaunches at the STEP0_FIX
    commit: the start takes the route again, moves what is left, logs "none of its 5 attempt-1 paths left to move
    (moved aside by an earlier start cut short before its save, or absent)" (or the number it moved), and makes the
    save [C: `check_commit_s2b`, `fr_step0_repeat`; N-FR6]. Such a STOP is relaunched, not made final, unless D-C2-3
    finds that its cause cannot be cleared through this route (for example, a defect inside `fr_step0_repeat` that
    recurs at every relaunch); the stop note then gives the analyst's dated reason. If an archive of this state were
    read, E would print "step-0 repeat prepared, not recorded" (row `B2.step0.repeat`), and the figure would draw
    "repeat prepared, not recorded" at the cell concerned, @2 or @4, under the same conditions as E
    [C: `e_eval` `Run.rf12_step0`, `Run.block2`; `fig_s2b_fr` `set_aside_2`, `set_aside_4`].
  - **A start cut short between its save and its rename** leaves the route file behind. The next start renames it
    with no state change [C: `fr_fix_leftover`, `fr_noerror_leftover`, `check_commit_s2b`, `preconditions`]:
    - a `CAMPAIGN_COMMIT` is renamed if it names `campaign_commit.fr`, and is a STOP otherwise;
    - a `STEP0_FIX` is such a leftover when `fr_step0` is repeat_pending with the file's note, the file names
      `campaign_commit.fr`, and the last history entry came to that commit by `fr/STEP0_FIX` with that note. Log line:
      "fr/STEP0_FIX: the applied route's leftover renamed .used, no state change (N-FR6); fr_step0 repeat_pending since
      <time>";
    - a `STEP0_NO_ERROR` is such a leftover when `fr_step0` is fail_final with `no_error_found`, its note equals the
      file's stripped text (at most 300 characters), and `fr/STEP0_FIX` is absent. Log line: "fr/STEP0_NO_ERROR: the
      applied route's leftover renamed .used, no state change (N-FR6); FR step-0 fail_final since an earlier start".
  - **Every other route file is a STOP** that names the file and changes no state: both files together, or either file
    while `fr_step0` is not fail_pending_fix. When the state records that route as applied earlier, the STOP says so
    [C: `fr_route_files`].
  - **Used names.** A route file (`CAMPAIGN_COMMIT`, `STEP0_FIX`, `STEP0_NO_ERROR`) is renamed to the first free name of
    `.used.<t>`, `.used.<t>.1`, `.used.<t>.2`, …, where `<t>` is the clock second; an earlier one is never
    overwritten [C: `rename_used`]. These names stay on the node: the archive publishes a fixed list of files
    [C: `archive`].
  - **One repeat for FR as a whole.** After a repeat every later step-0 evaluation is attempt 2, and an attempt-2
    failure is final. So a repeat at V⁺_R followed by a failure at D+V⁺ is final [C: `scripts/50` `gate_inputs`
    (fr_step0); `scripts/49` `step0_eval`]. S2B §2 allows "one repeat on the same cell"; this reading is the stricter
    one.
  - **The fix is diagnosed from inputs only** (IX-18). S2B §1 closes the guard's allow-list and S2B §0 keeps every fr
    DFT energy unread until E. So D-C2-10's read of the failing step-0 dF is not re-adopted [C: `s2b/guard.py`, no
    step-0 mode]. The evidence is this, and nothing else:
    - `decision.fr_step0` (which cell, which attempt, which outcome), read through GateLeaves (D-C2-5);
    - the D-C2-5 fields of the failed cell's A2 record, read through GuardedS2b (D-C2-5);
    - the pw.x input files of the failed cell: `a2/<label>/<label>.p<n>.in` and `<label>.meta.json`. The part-1 input is
      compared by sha256 with the `in_sha256` that D4 recorded for that cell in `fr_inputs.json`. A fresh
      `s2b/fr_inputs.py write` at the campaign commit is compared with D4's output by `fr_inputs.py compare` (§3, D4).
      Of the C1 single point only its input file is opened;
    - D1-D3 (§3), repeated: the checkout, the node scripts, pw.x and mpirun, the UPF files;
    - the runner's value-free records: the lines of `campaign.log` (read through the stop-reason filter of D-C2-5),
      `interruptions.jsonl`, and the part's exit code and launch record (`<label>.p<n>.rc`, `<label>.p<n>.launch.json`).
    No fr part output is opened, paged or grepped before E: not `<label>.p<n>.out` or its `.runlog`, in `a2/` or under
    any `discarded/`, and no `*.out.gz`. The runner moved the failed part's output aside as "output not read"
    [C: `settle_gate_kill`, `a2_discard`]. If the inputs show no writer or input error, no error has been found in the
    sense of S2B §2, and the analyst writes `fr/STEP0_NO_ERROR`. A diagnosis that needs an output waits for E and
    changes no decision.
  - The watcher never relaunches after a STOP: `s2_relaunch.sh` refuses while any `<campaign>/CAMPAIGN_STOPPED`
    exists, fr included [C: `s2_relaunch.sh`]. It then prints each CAMPAIGN_STOPPED in full, so its output is read
    only through the stop-reason filter of D-C2-5: the operator runs it as `bash
    /data/work/ps_s2/ehpc/node/s2_relaunch.sh 2>&1 | s2filt`.
- **D-C2-3 (STOPs that need a code or data fix): adapted** (IX-4, IX-15; amendment 2026-11-12a, item 13).
  - **A STOP whose cause can be cleared is relaunched to CAMPAIGN_DONE, never made final.** Among them:
    - the operator's STOP, "SIGINT received: stopped by the operator", also at the disk rule of D-C2-8
      [C: `housekeeping`];
    - the spot-poller STOPs, "spot endpoint not reachable: …" and "the spot poller keeps ending after a good poll …"
      [C: `spot_check`, `housekeeping`];
    - a held end-rule STOP (N-F36: an unconverged_early end of class nstep, other_end or pw_error). It is raised after
      the free jobs that are ready, gate FR among them if its inputs have ended. The STOP marks it raised in the cell's
      A2 record, so a relaunch does not raise it again, and fr reaches CAMPAIGN_DONE with the cell's recorded end rule
      [C: `a2_finalise`, `hold_from_record`, `loop`, `begin_stop`, `mark_stop_raised`; `scripts/47` `end_rule`].
      - The human check that the STOP reason names (pw_error: "a human rules out an infrastructure cause, N-B4";
        other_end: "JOB DONE without a known end marker (N-B4)"; nstep: "the nstep mapping is wrong (I-48)") is made
        from value-free evidence only: the error-routine name in the reason, the part's exit code and launch record
        (`<label>.p<n>.rc`, `<label>.p<n>.launch.json`), a CRASH marker, `interruptions.jsonl`, the node's system logs
        and D1-D3 (§3). The part output is never opened (D-C2-2).
      - No runner route reruns a cell whose record is final: a RESOLVE applies only to an end in the current boot that
        the runner could not explain, which is never finalised before it [C: `a2_ended`, `a2_resolve`]. The relaunch
        therefore ends fr at CAMPAIGN_DONE with FR-1 failed at that cell (end rule unconverged_early), whatever the
        check finds, and the finding is recorded in the FR note (§4). An nstep end shows a runner defect and still
        ends FR as failed (S2B §2: the first cell that ends without acceptance) [I];
    - a STOP before the runner recorded the fr campaign commit: a refused `fr/CAMPAIGN_COMMIT`, a checkout that is not
      clean or a stray route file at the first start. Its cause is removed (a corrected line is checked by D-C2-4) and
      fr is relaunched. Such a STOP recorded no commit, so `fr/campaign.json` holds `start_commit` and `commit` null
      until a start records the commit [C: `check_commit`, `check_commit_s2b`, `fr_route_files`, `s2b_route`,
      `set_campaign`];
    - a STOP whose cause lies in the checkout or on the node and is removed without a change of code or of a recorded
      file, such as a checkout that is not clean or at another HEAD;
    - the step-0 STOP, through one of its two routes, and a start at fail_pending_fix without one (D-C2-2);
    - the repeat prepared but not recorded (D-C2-2);
    - an interruption (§13) and a RESOLVE of a job, as the runner's own routes provide.
  - **The "not applied" STOPs are never made final, and at this commit no runner route clears them** (IX-15). Their
    reasons end "(N-FR4): not applied", "(N-FR4, N-FR8): not applied" or "(N-FR8): not applied; …": the scripts/49 run
    wrote the gate file, and the runner stopped before its applied copy and marker [C: `run_gate`,
    `s2b_decision_check`; N-FR4, N-FR8]. They show a disagreement between the runner and the gate code, which is a
    defect (§1, Gates), resolved by a dated fix and a relaunch, never by a stop note (IX-15). No runner route at this
    commit admits that fix:
    - the decision was never applied, so `fr_step0` keeps its earlier outcome and `fr/STEP0_FIX` is refused (it is
      accepted only at fail_pending_fix);
    - `fr/CAMPAIGN_COMMIT` admits a commit once, and any other HEAD is the STOP "checkout HEAD … is not the recorded fr
      campaign commit";
    - a relaunch at the same commit evaluates the gate again with the same code and STOPs again
      [C: `check_commit_s2b`, `fr_route_files`].

    On such a STOP the operator therefore stops: no relaunch, no route file and no stop note; nothing in the fr tree
    on the node is changed, and no fr archive is committed (§8). The pull, the dry-run check and the node stop still
    follow (§8 step 1); the archive and verify may be made on the laptop and are left uncommitted.

    **Such a STOP is not evaluated** (IX-19, IX-26; amendment 2026-11-12a, item 14). FR stays unevaluated: a state of
    S2B §1 in which no route applies and E may not run. Neither the §6b read, the FR figure nor E is run. The state
    ends only by a dated amendment of `S2B_PLAN.md`, written before any fr value is read, that does one of two things:
    - it admits a fix commit, and a runner route that relaunches fr at it. A synthetic self-test case shows the fix: it
      fails at the campaign commit and passes on the fix. The defective side, runner or gate, is decided by S2B §§1-2,
      the amendment and the code's specification, never by the FR outcome that either choice would give (an N-FR8
      reason names gate FR's outcome). The relaunch evaluates the gate again, and that decision stands;
    - or it makes the STOP final, and FR fails.

    If neither has been committed 60 days after the STOP, the STOP is final and FR fails (S2B §1). The readers'
    refusal texts ("resolved by a dated fix and a relaunch, never by a stop note") describe the first of these
    routes.
    - **Why no route now** [I]. A "not applied" STOP shows a defect that the self-tests of scripts/49 and scripts/50
      (17 and 66 cases, with the disagreement checks mutation-tested) exclude as far as tests can. A runner route for
      it would need another review round before the FR boot, and is built better against the actual defect if one
      occurs.
    - **Gate FR.** The §6b read, the FR figure and E refuse a stopped fr whose `gates/FR.json` exists without
      `gates_applied/gate_FR.gate.json`. The test is by name only, before the stop note is read, and nothing is
      written [C: `e_eval` `gate_fr_unapplied`, `Run.route_admit`; `fr_geom_read` `gate_fr_unapplied`, `when_ok`;
      `fig_s2b_fr` `gate_fr_unapplied`, `a2_stop_state`].
    - **Gate fr_step0** (a "not applied" STOP at @2 or @4; IX-20, IX-25). The readers do not refuse it by name.
      - At @4 the name test would be `gates_applied/gate_fr_step0_4.inputs.json` without
        `gates_applied/gate_fr_step0_4.gate.json` (`run_gate` writes the inputs file first). A step-0 gate that did not
        complete ("gate fr_step0 did not complete (exit …)") leaves the same names. A refusal by name would therefore
        also bar that STOP from being made final where its cause cannot be cleared [C: `run_gate`].
      - At @2 the name test would be `gates/fr_step0.json` without `gates_applied/gate_fr_step0_2.json`. A gate that
        did not complete there leaves no `gates/fr_step0.json`, because `scripts/49` writes it last. E already fails a
        "not applied" STOP at @2 as an integrity error (RF-12). The @2 case is left to the analyst's check, so that
        both cells are treated alike [C: `scripts/49` `main`; `e_eval` `Run.rf12_step0`].
      - Given a stop note, the §6b read would read, the FR figure would draw the gate as not reached, and E would fail
        its integrity checks in phase 0b (INT-STRUCT or INT-FR-SHA), writing its failure report and spending attempt
        1 [C: `e_eval` `Run.rf12_step0`, `Run.int_fr`]. The defence is the analyst's check before any stop note
        (§8): a "not applied" reason, at any gate, is treated as above and is made final only by the amendment or
        the backstop of item 14.
  - **Any other fr STOP is final.** It is one whose cause needs a change of code or data that no runner route admits.
    FR then fails (S2B §1, route table). Only a dated amendment of `S2B_PLAN.md`, written before any value it affects is
    read, could provide otherwise.
  - **A STOP is final only through its stop note** (§8): one committed, clean, dated note at the one fixed path that
    states it. Without one, the §6b read, the FR figure and E each refuse a stopped fr and write nothing.
  - **A stop note turns a recorded gate FR pass into "FR fails"** (IX-4). S2B §1 counts a final STOP in fr as "FR
    fails", whatever gate FR recorded before it. E's header then reads "pass at gate FR; then a final STOP (<reason>);
    counted as FR fails (S2B §1)". No A1 tier and no class follow, and E reads blocks 1-3. Every FR-quartet value E
    prints without the item-4 label carries "gate FR passed, then a final STOP in fr (S2B section 1); reported only;
    not valid" (L_FRSTOP, IX-12) [C: `e_eval` `Run.header_fr_part`, `Run.frstop_pass`]. A stop note is therefore
    written only after a relaunch has been ruled out, and never for a "not applied" STOP.
- **D-C2-4 (operator notes): kept.** Every operator note (CAMPAIGN_COMMIT, STEP0_FIX, STEP0_NO_ERROR, RESOLVE, a
  manual ledger entry) passes the hygiene check of `scripts/46` (kind 'json', the default) on the laptop before it is
  written on the node. These notes enter public JSON. The runner also refuses a CAMPAIGN_COMMIT, STEP0_FIX or
  STEP0_NO_ERROR that breaks a rule [C: `s2b_route`, `preconditions`]. The stop note (§8) is a repository file and
  passes the same check (kind 'code') before its commit.
- **D-C2-5 (what the operator reads): adapted.** The operator reads decisions, counts and timings only.
  - **A2 records.** Of an fr A2 record only the D-C2-5 fields are read: `status`, `end_rule.outcome`, `end_rule.end`,
    `n_config`, `converged_at_k`, `wall_h`, `min_per_config`, `restarts`, `reruns_from_zero` and the number of
    `interruptions`; on the route of D-C2-6 that needs them, after verify, also the two flags `end_rule.stop` and
    `end_rule.stop_raised`, booleans with no value (IX-22; amendment 2026-11-12a, item 14). `dF_200_180_meV` is never
    read. S2B §1 requires every tool that reads an fr A2 record
    before E to read it through the guard. So the fields are read by name through `s2b/guard.py` GuardedS2b, on the node
    and on the laptop alike; a withheld field raises [C: `GuardedS2b`, `guarded_s2b`]. `guard.py` loads
    `figures/fig_s2_c2_a2.py`, which imports numpy, so the interpreter is the node's mace-environment Python
    (`/data/miniforge3/envs/mace/bin/python`, as `s2_status.sh` uses it) on the node and the repository's Python
    environment on the laptop, written `<python>` below. For example, at the repository root:

    ```
    <python> -B - <path of <label>.a2.json> <<'EOF'
    import importlib.util as u, sys
    s = u.spec_from_file_location("g", "results/objective2/s2/s2b/guard.py"); g = u.module_from_spec(s)
    s.loader.exec_module(g)
    r = g.guarded_s2b(sys.argv[1]); e = r.get("end_rule") or {}
    print(r.get("status"), e.get("outcome"), e.get("end"), *(r.get(k) for k in ("n_config", "converged_at_k",
          "wall_h", "min_per_config", "restarts", "reruns_from_zero")), len(r.get("interruptions") or []))
    EOF
    ```

    An A2 record is never printed whole, paged, grepped or opened in an editor.
  - **Gate files.** Of the fr gate files only `decision.*` and the three reason lists `result.checks_failed`,
    `result.end_rule_failed` and `result.cells_not_run` are read, through the S2b guard (`s2b/guard.py`, GateLeaves).
    An allowed path whose subtree holds a withheld field raises. There is no step-0 exception [C: `GateLeaves`].
  - **When.** While fr runs, only the stop decision `fr_stop` {at, kind} and the gate decisions are read. The three
    reason lists, like the validity leaves, are read only after `CAMPAIGN_DONE` or the final STOP and after verify
    (S2B §2) [I].
  - **The status line.** The second `status` line, "state (S2b):", may be read while fr runs. It holds
    `campaign_commit`, `fr_stop`, and the decision fields of `fr_step0` and `FR` only [C: `cmd_status`].
  - **STOP texts.** The one new fr STOP that names a gate file names the reading route, not the file. When gate FR
    disagrees with `fr_stop`, the STOP ends "(N-FR8): not applied; read decision.FR of gates/FR.json through
    s2b/guard.py GateLeaves only (S2B section 1)" [C: `s2b_decision_check`]. `gates/FR.json` holds the FR-2 values
    once FR-1 has passed, so it is never opened directly. The other new fr messages name only the set-aside directory
    or the operator's own route files.
  - **`gates_applied/gates.log`** holds stdout and stderr of the `scripts/49` run command [C: `run_gate`]. After the
    STOP "gate <g> did not complete (exit <rc>): see gates_applied/gates.log", the operator reads only the output of
    these two commands, on the node:

    ```
    cd /data/work/s2/fr/gates_applied
    grep -E '^(REFUSED: GateRefused: |(fr_step0|FR): decision )' gates.log
    grep -oE '^[A-Za-z_][A-Za-z0-9_.]*:' gates.log | sort | uniq -c
    ```

    The first prints whole lines of the two shapes the `scripts/49` self-test pins for fr, "<gate>: decision {…};
    written <path>" and "REFUSED: GateRefused: <message>", none of which holds a value [C: `scripts/49` `main`;
    self-test `t_fr`]. The second prints only the name before the first colon of each line, so an exception is read
    by its type (for example "ValueError:"), never by its message. The exit code comes from the STOP text. Nothing
    else in `gates.log` is read.
  - **Stop reasons.** A STOP reason can quote an exception: "unexpected error <Type>: <message>" [C: `run`], and the
    message can run over several lines. It reaches `CAMPAIGN_STOPPED` (unredacted), `campaign.json` `stop_reason`,
    `campaign.log` (with the traceback), `driver.out` (the runner's stdout and stderr), the output of `s2_relaunch.sh`
    and the log tail that `s2_status.sh` prints [C: `begin_stop`, `run`, `cmd_status`; `s2_campaign.sh`,
    `s2_relaunch.sh`]. `jobs46/jobs46.log` holds the `scripts/46` line "STOP (<Type>): <message>" [C: `scripts/46`
    `main`]. Each of these, and the stderr of verify and of the field comparator (D-C2-6), is read only through this
    filter, which fails closed:

    ```
    s2filt() {
      sed -E \
        -e 's/(unexpected error [A-Za-z_][A-Za-z0-9_.]*).*/\1: [not read]/' -e t \
        -e 's/(STOP \([A-Za-z_][A-Za-z0-9_.]*\)).*/\1: [not read]/' -e t \
        -e 's/((failed during a stop or exit|not removed): [A-Za-z_][A-Za-z0-9_.]*).*/\1: [not read]/' -e t \
        -e '/^ *\[[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\] /b' \
        -e '/^([^ ]*\/CAMPAIGN_STOPPED: )?[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z /b' \
        -e '/^(runner|state|state \(S2b\)|node-hours|c[1-4]|fr|stop_reason): /b' \
        -e '/^[a-z0-9-]+: done$/b' \
        -e '/^(stopped for a human|KEEP_ALIVE from before this boot)/b' \
        -e 's/^([A-Za-z_][A-Za-z0-9_.]*): .*/\1: [not read]/' -e t \
        -e 's/.*/[line not read]/'
    }
    ```

    - An exception quoted by the runner ("unexpected error <Type>"), by `scripts/46` ("STOP (<Type>)") or by a
      last-resort report keeps its type only. A line that begins with a name and a colon, such as a traceback's last
      line, keeps the name only.
    - A runner log line (stamped "[<UTC time>] ") and a `CAMPAIGN_STOPPED` line (stamped "<UTC time> ") are kept
      whole, since the runner writes no value into them (N-FR7, N-FR8). So are the status lines of `s2_status.sh`, a
      `campaign.json` `stop_reason` printed through GuardedS2b after the prefix "stop_reason: ", a `scripts/46` line
      "<command>: done", and the two fixed lines of `s2_relaunch.sh` that precede or follow a stopped campaign's
      reason.
    - Every other line, the traceback, the second line of a message and any shape not listed here among them, reads
      "[line not read]".
    - It uses only `sed -E` constructs that GNU sed (the node) and BSD sed (the laptop) share. It was run with BSD sed
      on synthetic text holding a sentinel in every message shape above (several lines, a lowercase `error` type,
      `BadGzipFile`, `TimeoutExpired`, `StopIteration`, a traceback, a last-resort report): no sentinel was printed
      [I].

    A `CAMPAIGN_STOPPED` of more than one line (`wc -l`, not displayed) holds a message over several lines, and is a
    stop for the analyst. `campaign.json` `stop_reason` is printed for the filter, at the repository root on the
    laptop, as:

    ```
    <python> -B - results/objective2/s2/fr/campaign.json <<'EOF' | s2filt
    import importlib.util as u, sys
    s = u.spec_from_file_location("g", "results/objective2/s2/s2b/guard.py"); g = u.module_from_spec(s)
    s.loader.exec_module(g)
    print("stop_reason:", g.guarded_s2b(sys.argv[1]).get("stop_reason"))
    EOF
    ```

    The stop note quotes a reason by the filter's output only, so an exception by its type.
  - The validity leaves of fr records (`validity_final.*`, both readings) are read only after `CAMPAIGN_DONE` or the
    final STOP (§8) and after verify. The runner's log says only that the checks were evaluated [C: `run_a2v`; N-FR7].
- **D-C2-6 (verifying the archive): adapted.**
  - **The verify record.** On the laptop, at the repository root, after the archive (§8 step 2):

    ```
    python -B scripts/49_s2_gates.py verify --archive results/objective2/s2 --campaign fr \
        > <stage>/verify_fr.out 2> <stage>/verify_fr.err
    echo "exit $?" >> <stage>/verify_fr.out
    ```

    Stdout, then the line "exit <code>", becomes `results/objective2/s2/fr_verify/verify_fr.txt`, as `verify_c2.txt`
    was made. If `verify_fr.err` is not empty (`test -s`), the analyst stops before the commit; it is displayed only
    through the stop-reason filter of D-C2-5 (`s2filt < <stage>/verify_fr.err`). The record is committed unedited
    before the §6b read.
    E (amendment 2026-11-12a, item 10) and the §6b read require it committed and clean; the FR figure requires it to
    exist [C: `e_eval` `Run.verify_records`; `fr_geom_read` `when_ok`; `fig_s2b_fr` `a2_stop_state`].
  - **What it shows.** `verify` re-derives the gate files under `gates/` only: `gates/fr_step0.json`, which holds the
    last step-0 evaluation, and `gates/FR.json`. It prints "OK   fr <gate>" or "DIFF fr <gate>" for each, then "verify
    fr: <n> gate files, <m> differ". It exits 0 only when there is at least one file and every file reproduces
    [C: `scripts/49` `verify`; its self-test pins these lines]. A STOP before any gate gives "verify fr: 0 gate files,
    0 differ" and exit 1; that record is committed as it is.
  - **The field comparator.** At the repository root, with the same handling of its two streams:

    ```
    python -B results/objective2/s2/c2_verify/verify_fields.py --archive results/objective2/s2 --campaign fr \
        > <stage>/verify_fields_fr.out 2> <stage>/verify_fields_fr.err
    ```

    It is unchanged (sha256 `e27d1126…49e4`). It re-derives `gates/*.json` and every `gates_applied/*.gate.json`, so
    both step-0 copies. For each it prints whether decision, result and inputs digest are equal and the key paths of a
    differing result; for a differing digest it lists the opened files with another content hash and those opened on
    one side only; never a value [C: `verify_fields` `main`]. It keys each opened file by its path relative to the
    layout's root, which differs between the node (`work/s2/fr/…`) and the archive (`fr/…`) [C: `scripts/49`
    `Reader`]. So, for a differing digest, every opened file is listed as opened on one side only ("node only" and
    "archive only"), and the list of files with another content hash reads "none", as at each of the five digest
    differences of C2 [R: `c2_verify/verify_fields_c2.txt`]. A non-empty `verify_fields_fr.err` is handled as
    `verify_fr.err` is. Its stdout is kept beside the verify record as
    `fr_verify/verify_fields_fr.txt`, as for C2.
  - **Expected differences** [I]. These are accepted when they are the only differences:
    - the `fr_step0` inputs digest of every step-0 file present: verify's `gates/fr_step0.json` (the last evaluation,
      @2 or @4) and the comparator's `gates/fr_step0.json`, `gates_applied/gate_fr_step0_2.gate.json` and
      `gates_applied/gate_fr_step0_4.gate.json`, for the reason D-C2-6 gives: the node read the A2 output while it was
      still being written. If a step-0 result itself differs, only its k = 0 fields are compared, and a difference there
      is a stop;
    - on a held end-rule STOP route, gate FR's inputs digest in verify's `gates/FR.json` and in the comparator's
      `gates/FR.json` and `gates_applied/gate_FR.gate.json`. When the STOP was raised after gate FR was applied,
      `mark_stop_raised` rewrote the failing cell's A2 record after gate FR had read it [C: `begin_stop`,
      `mark_stop_raised`; `scripts/49` `Reader`]. This can occur on a route relaunched to CAMPAIGN_DONE and on a final
      STOP after a recorded FR outcome (IX-4). The difference is accepted when the comparator shows decision equal and
      result equal for both FR files, and the failing cell's A2 record has `end_rule.stop` and `end_rule.stop_raised`
      both true, read through GuardedS2b (D-C2-5), which shows that `mark_stop_raised` rewrote it. The comparator
      cannot name the rewritten file (above).
  - Otherwise gate FR is expected to reproduce. Any difference in an `fr_step0` or `FR` decision, or in FR's result, is
    a stop for the analyst. No code is changed. fr has no projection gate [C: `graph_fr`].
  - The attempt-1 gate files under `fr/step0_attempt1/` are not re-derived (their A2 inputs stay on the node) and are
    not read.
- **D-C2-7 (publication): adapted by S2B §1 and X15.**
  - The fr archive is committed to this public repository after verify. Inside `results/objective2/s2`,
    `archive --campaign fr` writes only to its fr tree. Before anything is read or written it refuses an `--out` whose
    real path lies inside `results/objective2/s2`, of this checkout or of any checkout that path runs through, unless
    its first component there is exactly `fr`. The test is made on strings, casefolded and by file identity, with
    links followed [C: `archive_out_refusal`, `_below`, `archive`; N-FR3].
  - The archive holds raw energies and values already combined: the step-0 `dF_meV` (attempt 1 too, after a repeat),
    FR's `Eb_A1_meV`, `Eb_A2_meV` and `delta_far_meV` when FR-1 passed, and any plateau difference. The blinding rests
    on the guard, on not opening these fields and on not combining the raw energies until E.
- **D-C2-8 (disk): superseded by S2B §9 step 9 (X17),** which now covers the fr tree too, including the attempt-1 A2
  files of a step-0 repeat under `fr/discarded/`. The 50 GB rule is kept: if less than 50 GB is free on the node's data
  disk at a relaxation end, the operator stops fr (SIGINT) for the analyst. Space may then be freed only outside the
  C1, C2, C3 and fr trees, and each deletion is recorded as a file listing. Then fr is relaunched (D-C2-3).
- **D-C2-9 (accepted as the code reads them): adapted.**
  - The step-0 repeat reruns only the failed cell (above), not the campaign from its first relaxation.
  - An operator stop is SIGINT followed by the drain; there is no pause that keeps restart data [C: `run`]. It is
    cleared by a relaunch (D-C2-3).
  - `fr_step0@2` survives as its applied-gate copy (`gates_applied/gate_fr_step0_2.gate.json`) after `fr_step0@4`
    overwrites `gates/fr_step0.json` [C: `run_gate`].
  - A relaunch does not rerun the node checks. The operator runs D1-D3 (§3) before every relaunch. The one exception is
    a STEP0_FIX start, which moves the check records aside so that the checks run again [C: `discard_checks`].
  - A relaxation that ends with no configuration k = 0 cannot be accepted, so FR ends at it, and its step-0 gate is
    recorded as skipped [C: `deps_state`, `status`].
- **D-C2-10 and the Reading rule: re-adopted for fr, with the FR note in place of the C2 result note (§4).** Their
  lapse at E follows the dated notice appended to OPS2.
- **D-C2-11 and D-C2-12 (the figure): adapted in §4.**

## 3. Pre-launch checks D1-D4 (read-only, on the node)

D1-D3 run before the first launch and before every relaunch. D4 runs once, before the first launch.
- **D1 (checkout and commit).**
  - HEAD equals the commit of `fr/CAMPAIGN_COMMIT` (the first launch, and a relaunch after a STOP before the runner
    recorded the campaign commit, D-C2-3), of `fr/STEP0_FIX` (the start of a repeat) or `campaign_commit.fr` (any
    other relaunch), and `git status --porcelain` is empty.
  - `8bff03e` is an ancestor of HEAD, and `git diff --numstat 8bff03e HEAD -- scripts/46_s2_cells.py
    scripts/47_s2_qe.py ehpc/` equals §5. The `--numstat` lines are compared, because the bars of `--stat` depend on
    the terminal width. After a STEP0_FIX the fix note lists any further change.
  - `ehpc/node/qe_queue.sh`, `chain.sh` and `s2_run_qe.sh` are unchanged from `8bff03e`.
  - `s2_status.sh` (its output read through the stop-reason filter of D-C2-5) shows the runner not running and
    KEEP_ALIVE absent, `commit` still `8bff03e…`, and campaigns c1 done, c2 done, c3 not_run. Before the first launch
    there is no `campaign_commit.fr`, nor at a relaunch after a STOP before the runner recorded it. At any other
    relaunch except the start of a repeat, `campaign_commit.fr` equals HEAD. At the start of a repeat it is still the
    earlier commit, and HEAD is the STEP0_FIX commit.
  - At the first launch, `fr/CAMPAIGN_COMMIT` holds exactly the hygiene-checked line.
- **D2 (node scripts and pw.x).**
  - The sha256 of the node copies of `run_qe.sh`, `qe.sh`, `qe_queue.sh`, `chain.sh` and `s2_run_qe.sh` equal the
    `files.*.sha256` of `c1/nodescripts_check.json`, and the two set-up copies (`qe_queue.sh`, `chain.sh`) equal the
    checkout's `ehpc/node` copies. The runner's own check compares the same [C: `nodescripts_check`].
  - pw.x reports v.7.5. The sha256 of the pw.x and mpirun binaries is recorded at the first launch in the private
    operations log and compared at every relaunch.
- **D3 (UPF).** The sha256 and md5 of every S2 UPF file, Cs included, equal `c1/upf_check.json`. The runner repeats
  this at fr's first start and at the start of a step-0 repeat, never at another relaunch [C: `run_check`, `status`,
  `discard_checks`].
- **D4 (dry run of the FR inputs; S2B §9 step 4).** On the node, `s2b/fr_inputs.py write --source node --root /data
  --state <the node's state.json>` runs twice, with `--repo` at an export of `8bff03e` and at the new checkout, each
  `--out` outside the S2 work tree.
  - Each `write` rebuilds the region and the pair, compares them with `c1/regions` and `c1/pairs`, and writes the four
    FR part-1 inputs as `scripts/50` `a2_launch` does, at the ranks of the state's A2 layout. It exits 1 if the region
    or the pair differs [C: `fr_inputs` `write`].
  - `s2b/fr_inputs.py compare <out at 8bff03e> <out at this commit>` must print "compare: 4 FR inputs, 0 differ" and
    exit 0: every `.p1.in` byte-identical, every `.meta.json` equal outside campaign and time [C: `fr_inputs`
    `compare`].
  - An `--out` under the S2 work tree, the C1 tree or an archive tree is refused before anything is read or written
    [C: `fr_inputs` `out_refusal`].
  - D4 on the node is decisive, because it runs with the node's ase and ranks. No energy and no fr A2 record is read.
    Its outputs are kept, because a step-0 diagnosis compares with them (§2, D-C2-2).

## 4. The FR note (D-C2-10 and D-C2-11 adapted; recorded before any fr value exists)

The FR note is the short note of S2B §9 step 4.
- **When.** Counts and timings (D-C2-5) may be read while fr runs. Everything else below is read once, after
  `CAMPAIGN_DONE` or the final STOP with its stop note, and after verify, in the order of §8.
- **Reported, per relaxation of the attempt in force.** As D-C2-10: the record status; for a complete record the
  end-rule outcome, and its `end` class for unconverged_early; `n_config`, `converged_at_k`, checks 2-5 on the final
  geometry with the failed checks named, `restarts`, `reruns_from_zero`, the number of interruptions, the MPI rank
  count, `wall_h` and `min_per_config`. For check 5 both readings are given, and which one decided.
- **Gates,** each in the state fixed by the D-C2-10 file mapping:
  - `fr_step0@2` and `@4`: pass; fail, with its outcome; skipped; not reached; repeat prepared, not recorded (D-C2-2).
    After STEP0_NO_ERROR the state in force is fail_final with `no_error_found`, while the gate copies keep
    fail_pending_fix (§2, D-C2-2). It is taken from `fr/state_end.json` at CAMPAIGN_DONE, and after a STOP from
    `fr_outcome` in `fr/campaign.json` or the runner's log line. The step-0 values are not reported here. E prints them
    in block 2, from each evaluation's own gate copy, with its recompute where the cell is complete (amendment
    2026-11-12a, item 3).
  - **FR at CAMPAIGN_DONE:** pass; fail (FR-1), with the first failure {cell, kind} and the reason lists; fail (FR-2);
    fail (step-0 final; gate not evaluated). The outcome is `fr_outcome` in `campaign.json`, which the runner derives
    from the decisions alone [C: `fr_outcome`, `finish`].
  - **FR after a final STOP:** the decision recorded before the STOP, then the STOP (IX-4; amendment 2026-11-12a,
    item 13). At every STOP of fr, `begin_stop` records in `campaign.json` the `fr_outcome` that the recorded decisions
    already fix (gate FR applied, or the step-0 final), else null (IX-10) [C: `begin_stop`, `stop_outcome`].
    - E's header reads "fail (FR-1, <cell>, <reason>); then a final STOP (<stop reason>)", "fail (FR-2); then a final
      STOP (…)", "fail (step-0 final; gate not evaluated); then a final STOP (…)" or "pass at gate FR; then a final
      STOP (…); counted as FR fails (S2B §1)" [C: `e_eval` `Run.header_fr_part`, `Run.decided_part`].
    - The figure's FR row carries the same text, with the cell named by its role and "(S2B section 1)", and draws it
      as a failure [C: `fig_s2b_fr` `fr_gates`, `plot`].
    - Only when no decision was recorded before the STOP does E's header read "stopped at <first FR cell not complete>
      (<stop reason>)" and the figure's row "not reached (after a final STOP)".
    - E and the figure each assert that `fr_outcome` agrees with the gate files [C: `e_eval` `Run.stop_decision`;
      `fig_s2b_fr` `fr_gates`]. FR's line names the stop note.
- **A1 validity** of the start cells, from the C1 records read with the blinded loader of `scripts/46`, labelled
  "reported only". FR's `result.a1_invalid_reported` is not on the guard's allow-list and is not read.
- **The S2B §1 consequence of the branch taken.**
  - **FR fails** when fr ends done with `fr_outcome` other than pass, and after any final STOP, whatever `fr_outcome`
    reads (IX-4): no A1 tier and no class, E reads blocks 1-3, the hinge block stays blind.
  - **FR passes** only when fr ends done with `fr_outcome` pass: C3b follows (S2B §9 step 5), and the A1-tier labels of
    S2B §1 are printed. The bracketed clause is printed only when a cell of the quartet has
    `validity_final.invariant_only` true in its record. This is the set that FR's `result.invariant_only` lists, which
    the guard does not hand out.
- **Cost.**
  - **Planning reference.** S2B §8: 5.5-14.4 h per relaxation, 22-58 node-h for the four.
  - **Measured against it.** `n_config` against the cap of 201 configurations, `min_per_config` against 4.19-4.65 min
    [R: `C2_RESULT.md`], and fr node-hours against 22-58 node-h (or 6-29 after an early stop; up to 72 with a step-0
    repeat).
  - **fr node-hours.** As D-C2-10: the sum of `boots[].hours` over the boots whose `campaigns` include fr, manual rows
    listed separately. The tail of the boot that ended C2 is counted at FR's first boot (S2B §8) and listed separately.
    The cumulative S2 `H_spent_h` is given against the 520 node-h cap.
  - **Uncovered node-hours** and the **running estimate** as D-C2-10, with "the cells still to run" in place of
    8 − k.
- **Step-0 repeat.** If the check was repeated: the STEP0_FIX commit, its note path and diff stat, from
  `commit_history`; the attempt-1 decision, from `decision.fr_step0.attempt1` of the gate in force; the attempt-1
  relaxation lines of the archived `campaign.log`, before "FR step-0 repeat prepared"; their node-hours. The attempt-1
  files are not read.
- **The not_run c3.** The sha256 of the private not_run c3 files and their verify line (S2B §9 step 4).
- **Not read before E.** Every fr DFT energy: any F(k) of an fr relaxation, the step-0 `dF_meV` (both attempts), the
  F of the two C1 reference single points, FR's `Eb_A1_meV`, `Eb_A2_meV` and `delta_far_meV`, and the plateau
  differences. Only FR-2's decision is read. The note says where these values are held in the public archive.
- **The figure** (`figures/fig_s2b_fr.py`, nature-figure, Python backend), adapted from D-C2-11 and D-C2-12. It is
  committed with its self-tests on synthetic archives before any fr record is read on the laptop.
  - **a: force criterion.** As D-C2-11 panel a, one line per fr relaxation of the attempt in force, with the same
    force-only reader, build asserts, end glyphs and threshold. The free atoms are those of `c1/regions/m30_A188.json`
    (64) and of the A1 start records. Colour shows the cell role.
  - **b: gates.** The strip of `fr_step0@2`, `fr_step0@4` and FR, each in its state (above). No step-0 or FR-2 value
    is read or plotted. A check-5 pass that needs the invariant reading is flagged in FR's detail, on a pass and on an
    FR-1 or FR-2 failure alike. After a final STOP, FR's state names the decision recorded before it (above) and is
    drawn as a failure, and its detail names the stop note. No wrapped line holds a single word.
  - **c: cost.** `n_config`, `min_per_config` and the fr node-hours, as D-C2-11 panel c, without the projection strip.
    The S2B §8 band is 6-29 node-h when Cs D(A188) never started, else 22-58; with a step-0 repeat, a lighter band
    extends it to 72.
  - **When it is built** [C: `a2_stop_state`, `stop_note`]. `--build` refuses unless `fr/campaign.json` reads 'done'
    or 'stopped' and `fr_verify/verify_fr.txt` exists. On 'stopped' it refuses, before the stop note is read, a
    campaign whose `start_commit` and `commit` are both null (IX-14) and gate FR written but not applied (IX-15). It
    then requires `--stop-note NOTE` and applies E's tests to it, the fixed path among them (§8). On 'done' it refuses
    a stop note (IX-7). `state_end.json` must exist exactly when fr is done. The note's path and the sha256 of its HEAD
    text go into `source_data/fig_s2b_fr_b_stop.csv`.
  - **Blinding.** Every fr JSON file the build opens is read through `s2b/guard.py`: A2 records, `campaign.json`,
    `state_end.json`, `completeness.json`, `HARD_CAP.json` and `ledger.json` through GuardedS2b, gate files and their
    copies and markers through GateLeaves. Part outputs are read by their force rows only. The build also reads,
    outside the guard:
    - the archived `logs/campaign.log`, whole, for the STEP0_NO_ERROR and "repeat prepared" lines. It is the log the
      archive scrubbed by the hygiene check, and the runner writes no gate result or energy into it (N-FR7, N-FR8)
      [C: `_log_lines`; `scripts/50` `archive`];
    - `c1/smoke.json` (the restart mapping), the region file `c1/regions/m30_A188.json` and `c2/ledger.json` (C2's
      public ledger: boots, campaigns and hours), with `json.load` [C: `relaxations`, `free_source`, `cost`];
    - the C1 start records, through the blinded loader of `scripts/46` [C: `free_source`];
    - the stop note, through git [C: `stop_note`];
    - the attempt-1 folder and one attempt-1 marker, by existence only (§2, D-C2-2).
    The self-test's audit hook fails on any other fr JSON file opened outside the guard, any part output opened
    outside the force-only reader, and any attempt-1 path opened or listed.
    - After a final STOP, FR's state and its source data quote `campaign.json` `stop_reason` as it stands; the runner
      redacts it for hygiene only [C: `fr_gates`; `scripts/50` `begin_stop`, `public_text`]. E's header quotes it
      too [C: `e_eval` `Run.header_fr_part`]. A reason that quotes an exception message would therefore reach the
      figure, which is read before E; §8 stops such a route before step 4.
  - **QA.** As D-C2-11: panel alignment, PDF text ≥ 5 pt, the collision audit, and source data with no energy column.
    These three audits come from the external nature-figure toolkit (the figure's `QA_DIR`), as for the C1 and C2
    figures (IX-9). The figure's self-test requires the toolkit and fails without it; the plot runs its audits when it
    is present [C: `plot`, `qa`].

## 5. Inputs at the S2b commit (S2B §9 step 3)

- **The diff of `scripts/46`, `scripts/47` and `ehpc/` between `8bff03e` and this commit** [C]. Output of
  `git diff --stat 8bff03e -- scripts/46_s2_cells.py scripts/47_s2_qe.py ehpc/` on the tree that becomes this commit
  (80 columns, as git prints when not attached to a terminal), re-taken on 2026-11-14 after the last integration fix:

  ```
   ehpc/EHPC_REBUILD_GUIDE.md |   2 +-
   ehpc/node/s2_campaign.sh   |   8 +-
   ehpc/node/s2_relaunch.sh   |   8 +-
   scripts/46_s2_cells.py     | 219 ++++++++++++++++++++++++++++++++++++++++++---
   4 files changed, 217 insertions(+), 20 deletions(-)
  ```

  The same diff as `git diff --numstat` (the form D1 compares):

  ```
  1	1	ehpc/EHPC_REBUILD_GUIDE.md
  5	3	ehpc/node/s2_campaign.sh
  6	2	ehpc/node/s2_relaunch.sh
  205	14	scripts/46_s2_cells.py
  ```

  - `scripts/46`: the `fr` campaign id in `Layout`; the opt-in invariant reading of check 5 (`check_partner`
    `exchange_n`, `validity_a2` `check5_reading`, passed through by `job_validate_a2`), with its note S2B-X4 and
    self-test cases. The default output is unchanged.
  - `scripts/47`: unchanged.
  - `ehpc/node`: `s2_campaign.sh` starts fr only; `s2_relaunch.sh` adds fr to its list of campaigns.
  - `ehpc/EHPC_REBUILD_GUIDE.md`: one line, in which a placeholder replaced a host address (commit `732cb4c`, merged
    before the S2b plan). It is documentation and no node script.
- **The byte-identical input check.** `s2b/fr_inputs.py --self-test` writes the four FR part-1 inputs with the region
  and pair builders, `write_cell` and the QE input writer at `8bff03e` and at this commit, and compares them. It ran
  after the last integration fix, with `--repo-a` an export of `8bff03e` (`git archive 8bff03e scripts
  results/fa_host`) and `--repo-b` a copy of the tree that becomes this commit, both without `c2/` and the blinded C1
  paths; exit 0. `fr_inputs.py` has sha256 `f891f77e621e072a820c17abe9e895a35469a2aff4b2de7b9c2ffe9d435d5800`. Its
  result line, with the two temporary directories written as `<A>` and `<B>`:

  ```
  fr_inputs self-test passed: the region, pair and four part-1 inputs rebuilt and written at <A> and <B> are
  identical, and so are those from the archive source on a synthetic archive (8 structures); 4 inputs equal
  scripts/50 Runner.a2_launch's; ranks from the state's a2_layout (48, and 64 in fr_inputs.json and every meta
  record); 2 edited C1 records (a region free index, a pair field) give exit 1, DIFFERS and a failing A-side identity
  line; other ranks are named (ranks_expected); a campaign-only meta difference is allowed, a meta field and an input
  byte are reported; the refused trees pinned as literals; 13 refusals (an --out under an archive tree, a link to one,
  a case variant of one, the --root work tree or --c1; another --ranks; 2x32) with nothing written; identity refusals
  of an aliased spelling: 1
  ```

  (One line in the output; wrapped here.)
- **Provenance: the tools at this commit.** The sha256 of each file and its line count, taken from the tree that
  becomes this commit after the last integration fix. New or changed for S2b:

  | file | lines | sha256 |
  |---|---|---|
  | `scripts/46_s2_cells.py` | 3014 | `0fcfc3366fcc59225aa35de849cf5885c17c8a6ada110820a64edfc40b496425` |
  | `scripts/49_s2_gates.py` | 2996 | `1b94921498615ee50a451bc7e6d0076710ff3feab236201272ec7c4d64670c3b` |
  | `scripts/50_s2_campaign.py` | 9278 | `4f74dd4d1906040d036b69bee53b2cf2dd871faff57916931948ebb1fe1658c7` |
  | `ehpc/node/s2_campaign.sh` | 27 | `eaabce05cc9ab96c34880401bbbafd27bd800eb2ee1dcc8207eebd1cd9d6b49b` |
  | `ehpc/node/s2_relaunch.sh` | 58 | `4cfe7ba1525dc0f881fd3a8c7edf2525b39b32881a760c83a4eaa08ba3c74f13` |

  | file under `results/objective2/s2/` | lines | sha256 |
  |---|---|---|
  | `s2b/guard.py` | 405 | `bb33ab1266871999f288c48fb6c696d6ad8bcd60165c510e3a14aa1cec7a29eb` |
  | `s2b/fr_inputs.py` | 492 | `f891f77e621e072a820c17abe9e895a35469a2aff4b2de7b9c2ffe9d435d5800` |
  | `s2b/e_eval.py` | 2655 | `1349eddcffc9218a1bd9f2f3fe4646db7ae981e1c86b65828cccb21aeff95cf9` |
  | `s2b/e_guard.py` | 984 | `383a3f44df05648e96f931a040970679db4250d5e65332a577108d4763dd2786` |
  | `s2b/e_read.py` | 791 | `1911f2b95ad8e8777cd83545b6ebbd1581410bc6e8ff6e73eb8b26fb1e898b48` |
  | `s2b/e_block4.py` | 57 | `32e84bfd6b9c49c280c07b5a055dfed11ef31b5861b86f94da676925d9ec7f68` |
  | `s2b/e_selftest.py` | 6138 | `17494aa8be2775030fe65a944dcea4eb98b8be27caa12ac3f023f5098f3a1862` |
  | `figures/fig_s2b_e_fk.py` | 915 | `651d18874eb1dd4d5841a435d6df1fea22f27577326b22cabc202c756a1dc7d5` |
  | `figures/fig_s2b_fr.py` | 3496 | `f700508f5c7bbf341e34bf8f7d44062b169c9d9ec7482972e6b944b6e7f83f44` |
  | `c2_diagnostic/fr_geom_read.py` | 3274 | `347f8580a26e48e711522e4a399e861d4baf5f5ed78a27efba8fcfdb0bb6410a` |

  Unchanged by this commit, and used by fr's tools:

  | file | lines | sha256 |
  |---|---|---|
  | `scripts/47_s2_qe.py` | 2278 | `ace31dd3fb5ca6fe08cfda1172f35f1bddd9933fd7a4d53d8cd4402838532c39` |

  | file under `results/objective2/s2/` | lines | sha256 |
  |---|---|---|
  | `c2_diagnostic/part_d_read.py` | 528 | `baf8a4c5d339db94f1ed440d62d77b1fabbff29aa29f70ddd6a8a79444949f79` |
  | `c2_diagnostic/check5_diag.py` | 444 | `f5596923c2d264f2141972a2aff68cc4cd8571f0d78cbe3dda5b3a692f2f1d30` |
  | `figures/fig_s2_c2_a2.py` | 1081 | `5ba761c13345d66e0d44bda8e3b999cbd4c3156f1e654914ceb5c8a524849640` |
  | `c2_verify/verify_fields.py` | 66 | `e27d1126fbeabb57bd3f70dd4329add6d4d7d2c5510b2c4fd51f44bd2a7849e4` |

  The final lines of the self-tests run on this tree are kept in the private record folder. The full self-tests of
  `fr_geom_read.py` and `part_d_read.py`, which read the C1 structure archive through the committed blinded loader,
  are run by the analyst (IX-9).

## 6. The projection at the FR decision (S2B §8)

FR is the first of the four projection points. fr does not compute it [C: `graph_fr` has no projection gate]. It is
computed after FR ends and before any c3b cell, by the committed c3b code, from the ledger at FR's end, and recorded
as the FR-decision projection. If FR fails, no campaign follows and nothing is projected [I].

## 7. Where the code reads S2B (recorded so that the FR note can cite it)

- The guard's allow-list for fr gate files is exactly S2B §1's: `decision.*` and the three reason lists
  [C: `s2b/guard.py` `GATE_LEAVES`, `GateLeaves`]. fr A2 records are read by field name through GuardedS2b
  [C: `GuardedS2b`].
- Cells after a hard-cap refusal are not_run_gate (S2B §2); the refused cell keeps its not_started_cap record
  [C: `a2_phase`; N-FR5].
- A plain start at `fr_step0` fail_pending_fix is a STOP (§2, D-C2-2) [C: `preconditions`].
- One step-0 repeat for FR as a whole (§2, D-C2-2) [C: `gate_inputs`, `step0_eval`].
- A route file left by an applied route is renamed with no state change; any other stray route file is a STOP
  [C: `fr_route_files`; N-FR6].
- No STOP sends the operator to an fr gate file outside the guard [C: `s2b_decision_check`; N-FR8].
- After `campaign_commit.fr` is recorded, a new HEAD is admitted only through `fr/STEP0_FIX` at `fr_step0`
  fail_pending_fix; no runner route admits the fix of a "not applied" STOP (§2, D-C2-3) [C: `check_commit_s2b`,
  `fr_route_files`].
- Inside `results/objective2/s2` the fr archive lands only in `fr/` [C: `archive_out_refusal`; N-FR3].
- FR's outcome is `fr_outcome` in `campaign.json`, from the decisions only: at CAMPAIGN_DONE (none derivable: a STOP,
  nothing written), and at every STOP of fr as the outcome the decisions already fix, else null (IX-10)
  [C: `fr_outcome`, `finish`, `stop_outcome`, `begin_stop`; N-FR8].
- A STOP of fr is final only through its stop note, the one file `results/objective2/s2/FR_STOP_NOTE.md`, tested
  alike by the §6b read, the FR figure and E, each of which refuses a stop note on a done fr (§8; IX-1, IX-6, IX-7).
- The three readers refuse, before the stop note is read and with nothing written, a stopped fr whose `campaign.json`
  has `start_commit` and `commit` null (IX-14) and one whose gate FR was written but not applied (IX-15)
  [C: `e_eval` `Run.route_admit`; `fr_geom_read` `when_ok`; `fig_s2b_fr` `a2_stop_state`].

## 8. After fr ends: the order of work on every route

- **Is a STOP final?** On a STOP the analyst reads its reason (through the filter of D-C2-5) and decides by D-C2-3. A
  STOP whose cause can be cleared is relaunched to CAMPAIGN_DONE. A "not applied" STOP is neither relaunched nor made
  final: it is not evaluated, and the work stops there, with no stop note and no reader run, until a dated amendment
  rules on it under the rule of amendment item 14, or its 60-day backstop makes it final (D-C2-3; IX-19, IX-26). Only
  a STOP that cannot be cleared receives a stop note, which turns any recorded gate FR pass into "FR fails" (IX-4).
- **The check before a stop note** (IX-20). Before writing the note, the analyst:
  - lists by name only, never opening a file, `fr/gates/`, `fr/gates_applied/` and the attempt-1 markers of the stage
    copy or the node;
  - confirms that the reason, read through the filter, is not a "not applied" reason of any gate. Such reasons end
    "(N-FR4): not applied", "(N-FR4, N-FR8): not applied" or "(N-FR8): not applied; …";
  - confirms that every gate with a `gates_applied/<id>.inputs.json` either has its `<id>.gate.json` or is the gate
    the reason names as not completed.

  If any of the three fails, no stop note is written and the work stops for the analyst's dated ruling.
- **The reason the readers print.** The FR figure and E quote `campaign.json` `stop_reason` as it stands (§4). Before
  step 4 on a STOP route, the analyst prints it through GuardedS2b after the prefix "stop_reason: " and reads it only
  through the filter of D-C2-5. If the filter leaves anything other than the whole reason (a "[not read]" or a
  "[line not read]"), the reason quotes an exception message, and the work stops before the §6b read, the figure and
  E for the analyst's dated ruling [I].
- **The stop note** (IX-6; amendment 2026-11-12a, item 12):
  - the one file `results/objective2/s2/FR_STOP_NOTE.md`, added in a commit after the fr campaign commit. All three
    readers refuse every other path before git is asked: E with exit 2, the §6b read with exit 3, the figure with its
    need() "stop note: fixed path";
  - with an ISO date (YYYY-MM-DD), the STOP's reason as the filter of D-C2-5 shows it (an exception by its type
    only), the decision recorded before the STOP, if any, and why D-C2-3 makes the STOP final;
  - stating, on one line and with single spaces, "the fr STOP is final". The readers match this phrase in any case, but
    with single spaces only;
  - clean under the hygiene check (D-C2-4), committed, and never edited after its commit.
- **The test** [C: `e_eval` `stop_note_ok`, `Run.note_ok`, `Run.route_admit`; `fr_geom_read` `note_path_ok`,
  `note_text`, `final_stop`; `fig_s2b_fr` `stop_note`, `a2_stop_state`]. The three tools apply E's test: the fixed
  path, given as a normalised repository-relative path; tracked and unchanged in the tree; `git cat-file -t
  HEAD:<path>` prints "blob"; the text read from HEAD holds the phrase and an ISO date. Each tool records the path and
  the sha256 of the HEAD text. Each refuses a stopped fr without a valid stop note, and a stop note on a done fr
  (IX-7), and writes nothing.
- **Two routes the readers refuse before the stop note is read** (IX-14, IX-15): a stopped fr whose `campaign.json`
  has `start_commit` and `commit` null, and a stopped fr whose gate FR was written but not applied.
  - The first is a STOP before the runner recorded the campaign commit (a refused `fr/CAMPAIGN_COMMIT`, a checkout
    that is not clean, a stray route file). It is cleared by removing its cause and relaunching (D-C2-3).
  - The second is a "not applied" STOP. No runner route at this commit clears it; it is not evaluated until a dated
    amendment rules on it (D-C2-3; IX-19). So is the "not applied" STOP of gate fr_step0, which the readers do not
    refuse by name; the check before a stop note excludes it (IX-20).
  - On either route the archive is not committed (step 3) until the route is cleared or ruled on: a relaunch after
    that commit would change `fr/` after the commit that E takes as the fr archive commit. Left as it is, either route
    stops the work after the pull, the archive and verify, which are made but not committed. There is no §6b read,
    figure or E until the route is cleared or a dated amendment rules on it (amendment 2026-11-12a, items 11 and 14).
- **The order** (IX-1; amendment 2026-11-12a, item 12). The same order holds on every route. On a STOP the stop note
  is committed before step 4, and the same note is named to all three tools.
  1. **Pull, the dry-run check and the node stopped at once** (S2B §9 step 4).
     - The pull copies the node's `/data/work/s2/fr/` to `<stage>/work/fr/` with `rsync -a`, and `/data/jobs/s2fr/` to
       `<stage>/jobs/s2fr/` if it exists. `<stage>` is a private directory outside the repository; nothing in it is
       opened except by `archive`. The attempt-1 A2 directory of a step-0 repeat stays on the node: the pull excludes
       `/discarded/step0_attempt1_*/a2/` [I].
     - **The dry-run check**, as C1 and C2 made it [R: `C1_RESULT.md`, `C2_RESULT.md`]: the same rsync commands run
       again with `--dry-run --itemize-changes` and list no file.
     - The operator may set `/data/KEEP_ALIVE` again to guard the pull against the idle self-stop, as for C1, and
       removes it before the node is stopped.
  2. **Archive** (D-C2-7), on the laptop at the repository root:
     `python -B scripts/50_s2_campaign.py archive --stage <stage> --campaign fr --out results/objective2/s2/fr`
     [C: `archive`, `archive_out_refusal`; `--stage` and `--out` are required]. `--out` must be new or empty.
  3. **Verify** (D-C2-6): `fr_verify/verify_fr.txt` and the field comparator's output. The archive and both verify
     records are then committed unedited; the archive is public after verify (S2B §1).
     - The whole `fr/` tree that `archive` wrote is added in one commit, which E takes as the fr archive commit: the
       one commit that adds `fr/campaign.json`. The verify records may go into the same commit or a later one.
     - Nothing under `fr/` is changed, re-added or archived again after that commit. E reads every fr file it opens
       as a blob of that commit and requires `fr/` unchanged from it to HEAD; otherwise it fails INT-SHA in phase 1,
       writing its failure report and spending the attempt [C: `e_eval` `Run.archive_commit`, `Run.int_sha`].
  4. **The §6b read:** `python -B results/objective2/s2/c2_diagnostic/fr_geom_read.py --read`, with `--stop-note
     results/objective2/s2/FR_STOP_NOTE.md` on a STOP. It refuses unless the verify record and the fr archive are
     committed unedited at HEAD, and while `c3b/` or `s2b/E_output.txt` exists [C: `when_ok`]. It writes
     `c2_diagnostic/fr_geom_read_output.txt`, which is committed unedited.
  5. **The FR figure:** `python -B results/objective2/s2/figures/fig_s2b_fr.py --build`, with the same `--stop-note`
     on a STOP, then the plot (`fig_s2b_fr.py` without options) (§4). Committed.
  6. **The FR note** (§4), committed.
  7. **By route,** keyed on the status of `fr/campaign.json` first and then on `fr_outcome`, as E keys its own route
     [C: `e_eval` `Run.route_admit`]. C3b starts only after FR passes and fr ends done. E runs as its docstring
     gives it, `python -B -I`, with Python 3.12 or later (`tarfile.data_filter`); an older interpreter is refused
     with nothing written [C: `e_eval` `Run.phase0_start`]. `-I` keeps the script's directory and the user's
     site-packages off `sys.path`.
     - **Status 'stopped', with the stop note:** route FR-STOP, whatever `fr_outcome` reads (IX-4). E runs on a clean
       tree, at the repository root, `python -B -I results/objective2/s2/s2b/e_eval.py --run --stop-note
       results/objective2/s2/FR_STOP_NOTE.md` (blocks 1-3). A later hinge run on this route names the same note
       (amendment 2026-11-12a, item 11). C3b never follows.
     - **Status 'done', `fr_outcome` other than pass:** route FR-FAIL. E runs on a clean tree, at the repository root,
       `python -B -I results/objective2/s2/s2b/e_eval.py --run` (S2B §9 steps 6-7).
     - **Status 'done', `fr_outcome` pass:** C3b follows (S2B §9 step 5). E runs only after the later campaigns,
       with block 4.

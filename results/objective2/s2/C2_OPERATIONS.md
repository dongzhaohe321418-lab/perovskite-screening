# S2 campaign 2 (C2): operating decisions, recorded before C2 starts (2026-11-05)

C2 is the A2 calibration on the pilot host m30 (`S2_PLAN.md` §11). This note records the analyst's decisions on how C2 is operated. It was committed before the C2 runner started and before any C2 value existed. It changes no rule of `S2_PLAN.md` or `STAGE0.md`. Where the code leaves a choice to the operator, it fixes that choice in advance.

**Basis.**
- A C2 operator runbook was drafted from the code at the campaign commit and reviewed through three adversarial lenses (code correctness, safety and blinding, completeness). It is kept in the private record folder with its review record.
- Its 21 open items were decided by the analyst, who was delegated by the PI on 2026-11-03.

Labels: [I] marks the analyst's inference or arithmetic.

## 1. What C2 runs

- **Commit.** C2 runs at the S2 campaign commit `8bff03e`, as recorded in C1's state, with no redeployment.
  - The runner fixes one commit across campaigns (`scripts/50` `check_commit`).
  - In C2 a new HEAD is accepted only through `c2/STEP0_FIX`, after a failed step-0 check.
- **Relaxations.** There are 8 A2 relaxations, one at a time, at 64 ranks (C1 throughput gate). The order is fixed (`C2_ORDER`):
  - VB136, hostB136, Sr136 D, Sr136 D+V;
  - hostB76, VB76, Sr76 D, Sr76 D+V.
  - The Ca136 pair is not run: Ca failed G1 (`C1_RESULT.md` §3.1).
  - The graph has 23 jobs: 2 checks, 8 relaxations, 8 section-11 checks and 5 gates.
- **Gates (§11), applied by the node as they fall.**
  - step-0 at k = 0 of relaxations 1 and 4;
  - K2 at the end of relaxation 1;
  - the cost projection after relaxation 4;
  - K3 after the checks of relaxations 1-8.
- **Cost [I].**
  - At the C1-measured 64-rank rate (13.10 configurations per node-hour), 8 relaxations take about 40-86 node-h, with a median of about 54.
  - That is about 2-4 days of continuous running, with no allowance for interruptions.
  - The estimate is updated from relaxation 1's measured wall time.
  - The hard cap stays at 520 node-h, against 20.6 spent.

## 2. Decisions

- **D-C2-1 (no code change).** No recorded suggestion of `STAGE0.md` §7 is applied (`C1_RESULT.md` §5).
- **D-C2-2 (after a step-0 STOP).** After any step-0 STOP the operator never starts C2 plainly.
  - A plain start with neither a STEP0_FIX at a new HEAD nor STEP0_NO_ERROR would mark every pending relaxation not_run_gate and end C2. That would lose the one repeat that §11 allows [code trace].
  - The only routes are these two:
    - `c2/STEP0_FIX`, written as `<40-hex new commit> <YYYY-MM-DD of the dated note> <repository-relative note path>`, with the checkout at that commit;
    - `c2/STEP0_NO_ERROR`, with a dated note.
  - Each needs a dated analyst decision. The watcher never relaunches after a STOP.
- **D-C2-3 (STOPs that need a code or data fix).** Any such C2 STOP ends in "stop and re-plan" by a new amendment. No C2 analogue of `c1/NODE_FIX` is added, because the runner refuses a commit change.
- **D-C2-4 (operator notes).** Every operator note (STEP0_FIX, STEP0_NO_ERROR, RESOLVE, a manual ledger entry) is passed through the hygiene check of `scripts/46` on the laptop before it is written on the node. These notes enter public JSON.
- **D-C2-5 (what the operator reads).** The operator reads decisions, counts and timings only. The blinding rule of §17 is unchanged.
  - Of an A2 record only these fields are read: `status`, `end_rule.outcome`, `end_rule.end`, `n_config`, `converged_at_k`, `wall_h`, `min_per_config`, `restarts`, `reruns_from_zero` and the number of `interruptions`. `dF_200_180_meV` is never read. (Made precise on 2026-11-05, before C2 started; the earlier text named `end_rule.outcome` only.)
  - Of the step-0 and K3 gate files only the decision is read, never `dF_meV`, `Eb_A2_meV` or `value_meV`. The one exception is a step-0 STOP (D-C2-10).
- **D-C2-6 (verifying the archive: `scripts/49 verify --campaign c2`).** The comparison is read field by field (result, decision, inputs digest) with the field comparator of D-C2-10. It prints equal or differ and, on a difference, the key paths and the names of the opened files, never a value.
  - Two differences are expected from the code, and are accepted if they are the only ones:
    - **step-0, inputs digest only.** The node read the A2 output while it was still being written; the archive holds the finished file. If the step-0 result itself differs, only its k = 0 fields are compared, and a difference there is a stop.
    - **The projection's rows.** The archive holds all complete A2 records, and the node held four. The node's decision is in force (N-D1).
  - Any difference in K2 or K3, or in a step-0 decision, is a stop for the analyst. No code is changed.
- **D-C2-7 (publication).** The C2 archive is committed to this public repository after C2, as C1's was. C2 is A2-I on the pilot host. The blinding of §17 covers production and A2-II (C4) cells. The archive holds raw energies, which stay visible in output files by design. It also holds values already combined: both quartet E_b^A2 values and the K3 value (`gates/K3.json` and its copy under `gates_applied/`), and a signed plateau difference in each A2 record that reached k = 200. The blinding rests on not opening these fields and not combining the raw energies (D-C2-10).
- **D-C2-8 (disk).** Nothing under the C2 directory is deleted before C4 ends, because C4 reads the C2 wall times. If less than 50 GB is free on the node's data disk at a relaxation end, the operator stops for the analyst.
- **D-C2-9 (accepted as the code reads them).**
  - The step-0 repeat restarts C2 at relaxation 1 (I-D1).
  - The operator has no pause that keeps restart data: an operator stop is SIGINT followed by the drain.
  - step0@1 survives as its applied-gate record after step0@4 overwrites `gates/step0.json`.
  - A relaunch does not rerun the node checks. The operator repeats the read-only node-script and UPF comparisons before every relaunch.
  - A relaxation that ends with no configuration k = 0 skips its step-0 gate instead of failing it. If this happens it is reported.

## 3. Reporting (recorded before any C2 value exists)

These two decisions fix in advance what the C2 result note reads, reports and plots. Before they were committed, they went through three rounds of adversarial review: four lenses (blinding, code, scientific rigour, completeness), a check of the revision, and a final check against the code and the C1 archive. They also make D-C2-5 to D-C2-7 precise.

**Reading rule.**
- A value is *read* when it reaches the analyst by any route: printed, plotted, written or used in a computation; through a diff, log or web view; or through a reviewer, sub-agent or tool. Holding a file in memory is not reading it.
- The gate code of `scripts/49`, its `verify`, the field comparator below (which re-runs that gate code) and the force-only reader of D-C2-11 may compute what they need. The analyst sees only their decisions, their equal-or-differ lines, the force curves and the result leaf fields that D-C2-10 lists by name.
- Until the one evaluation:
  - **Leaf fields only.** Fields are read by full name at leaf level only, for example `decision.K3`, `result.checks_failed`, `end_rule.outcome`. A parent such as K3's `result` or an A2 record's `end_rule` is never printed.
  - **No views of the protected files.** No gate file, A2 record or raw A2 output is printed whole, paged, grepped, or shown in any diff view, whether by `git diff`, `git show`, `git log -p`, `gh pr diff` or a web page. Raw A2 outputs are opened only by `scripts/49` and the force-only reader. The reader is developed on the public WP2e relaxation output (`dopant_shell/wp2e/relax_m30_GA_img0.out.gz`), not on C2 outputs.
  - **Reviewers.** Every reviewer or sub-agent that works on C2 material receives the not-read list below as a binding constraint. It checks gates only through `scripts/49 verify` and the field comparator.

- **D-C2-10 (what the C2 result note reads and reports).**
  - **When.**
    - Counts and timings (D-C2-5) may be read while C2 runs.
    - At a step-0 STOP, the analyst reads `result.cells.<SP>.dF_meV` and `passed` of the failing step-0 gate file, by name, for the D-C2-2 decision, and records them in the dated note.
    - Everything else under "Reported" is read once, after `CAMPAIGN_DONE` or the final STOP of C2 and after the archive has been verified (D-C2-6), for this note only.
  - **Reported.**
    - **Per relaxation of the attempt in force.**
      - The record status: complete, killed_by_gate, not_run_gate, not_started_cap or missing. A record that is still pending at a final STOP is reported as "stopped at k = k_last".
      - For a complete record, the end-rule outcome, and its `end` class for unconverged_early.
      - From the A2 record: `n_config`, `converged_at_k`, checks 2-5 on the final geometry (with the failed checks named), `restarts`, `reruns_from_zero`, the number of interruptions, the MPI rank count, `wall_h` and `min_per_config`.
    - **Gates.** Each C2 gate is reported in a state fixed by this mapping, taken from the files the runner writes:
      - **Applied.** An applied-gate file exists in `gates_applied/`: the gate's own state, as below.
      - **Not reached.** No applied-gate file, and either A2 was stopped by an earlier applied decision (K2 fail, step-0 fail_pending_fix or fail_final, K3 other than pass), or the gate's relaxation is not_run_gate or not_started_cap.
      - **Skipped (no k = 0).** No applied-gate file, A2 not stopped, and the gate's relaxation ended (complete, missing or killed_by_gate) with no `k0_seen` and `n_config` < 1 in its A2 record. This applies to step-0 only.
      - **After a final STOP.** The same rules apply. A gate with no applied-gate file is not reached unless the skipped rule applies.
      - **Note.** The `completeness.json` status 'skipped' covers both not reached and skipped, so it is not used to tell them apart.
      - step-0@1 and step-0@4:
        - pass;
        - fail, with its outcome (fail_pending_fix, fail_final). A cell with no value is "fail: value missing".
        - skipped, when its relaxation ended without a configuration k = 0 (D-C2-9);
        - not reached.
      - K2: pass; fail, with the end-rule outcome; not reached.
      - Projection: "no cut", or "cuts \<ids\>; c4_run \<true/false\>"; not reached.
      - K3:
        - pass;
        - fail (fail_replan), with `checks_failed`. An empty list means that the value was ≤ +25.7 meV, which is the content of the decision itself.
        - not evaluable (a1_only), with `end_rule_failed`;
        - not reached.
    - **Step-0.** The |F(k = 0) − F(SP)| of each cell against 0.5 meV, at each attempt. Attempt 1 is read from `c2/step0_attempt1/` if the check was repeated.
    - **A1 validity.** The A1 validity of the K2 and K3 start cells (`a1_valid_reported`, `a1_invalid_reported`), labelled "reported only" (I-10, I-11).
    - **The §11 consequence of the branch taken.**
      - K2 fail or step-0 fail_final: A2 stops, C3 runs, and S2 reports the A1 tier only.
      - K3 not evaluable: A2 stops, C3 runs, and S2 reports the A1 tier only.
      - K3 fail: production stops and S2 is re-planned.
    - **Projection.**
      - `P_initial_h`, each applied cut with `P_before_h` and `P_after_h`, and `c4_run`.
      - The largest df_δ still attainable with Ca removed: 4 with no cut, 3 after cut 1, at most 2 after cut 2 or a later cut (`C1_RESULT.md` §5a). If cut 2 or a later one applies, the note says that C4 can then yield no validated class (C5 needs df_δ ≥ 3).
    - **Cost.**
      - **Planning reference.** 65-141 configurations per relaxation, median about 89 (`S2_PLAN.md` §16 [I]). At the C1 64-rank rate of 13.10 configurations per node-hour (4.58 min per configuration, C1 throughput gate), that is 4.96-10.76 h per relaxation, median about 6.8 h, and 40-86 node-h for the eight [I]. This is the §1 range per relaxation, not an updated one.
      - **Measured against it.** `n_config` against the configuration range and the cap of 201 configurations; `min_per_config` against 4.58 min; C2 node-hours against 40-86 node-h.
      - **C2 node-hours.** The sum of `boots[].hours` over the boots whose `campaigns` include c2, in the last C2 `ledger.json`.
        - Manual ledger rows, which carry no `campaigns`, are listed separately.
        - A c2-tagged boot that started before the C1 `CAMPAIGN_DONE` (`c1/logs/campaign.log`) is split at that time, and only its later part counts as C2 [I]. This happens when C2 is launched in C1's last boot. The build asserts that every other c2-tagged boot started after it.
        - The cumulative S2 `H_spent_h` is given beside the C2 total, against the 520 node-h cap.
        - After a STOP, the ledger snapshot time is stated. Later node-hours come from the next ledger and are labelled.
      - **Uncovered node-hours.** `wall_h` counts only the parts of the kept trajectory. Node-hours not covered by any `wall_h` are reported as one line: gaps, lost parts, reruns and a discarded step-0 attempt.
      - **Running estimate.** After relaxation k, the estimate is the C2 node-hours so far + (8 − k) × the mean `wall_h` of the completed C2 relaxations [I].
    - **Step-0 repeat.** If the check was repeated, the note also gives:
      - the STEP0_FIX commit and its note path, from the commit history of `state_end.json` (or of `campaign.json` if that is absent), and the diff stat from `git diff --stat <from> <to>`;
      - the attempt-1 gate decisions;
      - the attempt-1 relaxations, from the archived `campaign.log` lines before "step-0 repeat prepared": "\<label\>: complete, N configurations, end rule \<outcome\>", "\<label\>: killed_by_gate (…)" and "\<label\>: missing (…)". The relaxation that the failing step-0 killed is reported as "killed by the step-0 gate; configuration count not archived";
      - their node-hours: the hours of c2-tagged boots up to the attempt-1 line "STOP: no child running; runner exits", with a boot that spans that time split at it [I]. Idle time after that STOP until the node stopped is attempt-1 overhead and goes in the uncovered node-hours line.
      - The attempt-1 A2 records stay on the node (I-D1) and are not read.
  - **Not read before the one evaluation (§17 item 6).**
    - The K3 value E_b^A2(Pb136) − E_b^A2(Pb76) (`result.value_meV`) and the two quartet values (`result.Eb_A2_meV`). Only the K3 decision and its reason lists are reported.
    - δ_{Sr,m30} and δ_far.
    - Every relaxation energy F(k = 0) − F(final), and any single F(k) of a C2 relaxation or of a step-0 reference single point.
    - The E_b^A1 of any A2 start-set quartet other than the gate-N value at Pb76; in particular E_b^A1(Pb136).
    - The plateau difference `end_rule.dF_200_180_meV`. The outcome accepted_plateau already states |F(200) − F(180)| ≤ 3 meV.
    - **Note statement.** The note says where these values are held in the public archive (D-C2-7), and that the blinding rests on not opening those fields and not combining the raw energies.
  - **Reason [I].**
    - **§17 does not require it.** §17 has the K3 gate read both quartets, but it does not require the analyst to read the K3 value, and §15 does not list it among the reported items. Withholding it is stricter than §17.
    - **K3 is close to δ.** With the known A1 E_b at Pb76 (−5.0 meV, `C1_RESULT.md` §6), the K3 value fixes δ_{Sr,m30} − δ_far + E_b^A1(Pb136) + 5.0 meV.
      - A coarse proxy for E_b^A1(Pb136) is already known: WP2d's raw Sr hinge E_b, +127.7 meV at q = +1 on the WP1 geometry (`dopant_shell/WP2D_RESULT.md`). So the K3 value carries coarse information on the calibration, and E_b^A1(Pb136) is withheld with it.
    - **Judgement still to come.** C4 can still need the analyst's judgement: a RESOLVE of an end-rule case (`scripts/50`), or a stop-and-replan (D-C2-3). The K3 value and the plateau differences are therefore read at the one evaluation, together with δ.
    - **What is safe to read.** The step-0 values are differences between two calculations of one geometry and carry no binding information. The force maxima, counts and timings cannot be combined into an energy difference at the resolution of δ.
  - **Field comparator.**
    - **Tool.** `verify_fields.py`, a laptop operator tool in the private record folder; sha256 `e27d1126fbeabb57bd3f70dd4329add6d4d7d2c5510b2c4fd51f44bd2a7849e4` at this commit.
    - **What it does.** For every file in `c2/gates/` and `c2/gates_applied/`, it re-runs `evaluate_gate` from the file's `state_in`, `inputs_in` and `c1_in`. For decision, result and inputs digest it prints only equal or differ. On a difference it prints the key paths and the names of the opened files, never a value.
    - **Test.** On the C1 archive it printed equal for all ten gate files (decision, result and digest). That output is kept beside the tool in the private record.
    - **Publication.** The tool is published unchanged with the C2 result (D-C2-7).
    - **Not covered.** The attempt-1 gate files under `c2/step0_attempt1/` cannot be re-derived from the archive, because their A2 inputs stay on the node (I-D1). They are reported as recorded.
- **D-C2-11 (the C2 figure, fixed before the data).**
  - **Script and inputs.** `figures/fig_s2_c2_a2.py` (nature-figure, Python backend). It reads:
    - `c2/raw` (A2 part inputs and outputs, A2 records);
    - `c2/gates`, `c2/gates_applied` and `c2/step0_attempt1` (if present);
    - `c2/state_end.json` or `c2/campaign.json` (the A2 stop state), `c2/ledger.json` and `c2/logs/campaign.log`;
    - `c1/smoke.json` (the restart mapping), `c1/regions` and `c1/records` (free-atom counts) and `c1/logs/campaign.log`.
  - **a (hero): force criterion; energies not shown.** The largest Cartesian force component on the free atoms against configuration k, one line per relaxation of the attempt in force, on a log axis.
    - **Free atoms.**
      - They are the ATOMIC_POSITIONS rows of part 1's input that carry no if_pos flags. The writer writes `0 0 0` on fixed atoms only (`scripts/47`).
      - The build asserts that their number equals `n_free` of the start source the runner used: the region file for host_R (70 at Pb136, 100 at Pb76), and `c1/records/<a1_start_of(label)>.json` for V⁺_R, D and D+V⁺ (69 or 70 at Pb136, 99 or 100 at Pb76). It also equals nat − n_fixed, and the set is the same in every part.
      - Whether pw.x 7.5 zeroes the printed forces of fixed atoms is not established. The curve uses the free atoms whatever pw.x does.
    - **Force-only reader.**
      - k is taken from `parse_relax(read="counts")`, which reads no value.
      - For each counted configuration, the force rows are read with `scripts/47` `_segment` and `_read_forces`. The '!' energy line is never parsed.
      - Build asserts:
        - `READS["F"] == 0` and `READS["ase"] == 0` at exit;
        - the k values of each line are 0 … `n_config` − 1 of its A2 record;
        - no source-data column holds an energy;
        - at k = `converged_at_k` of every accepted_converged line, which is its last point, the largest printed free-atom component in Ry/au, before any unit conversion, is ≤ 7.8 × 10⁻⁴.
    - **Ends.** Each line ends in a glyph taken from its record:
      - filled circle: accepted_converged;
      - triangle: accepted_plateau;
      - cross: unconverged_cap;
      - square, labelled with its `end` class: unconverged_early;
      - open end: stopped at k = k_last.
    - **Other marks.**
      - Restart part boundaries are ticks.
      - Relaxation 1 is labelled "K2".
      - A killed, not-run or missing relaxation appears in the legend with its status and no line.
      - Colour shows the quartet (Pb136 or Pb76). Line style shows the cell role (host_R, V⁺_R, D, D+V⁺).
    - **Threshold.** forc_conv_thr is drawn at 7.8 × 10⁻⁴ Ry/bohr, 0.02005 eV/Å with the `scripts/47` constants, and labelled in both units. k = 200 is also marked.
    - **Caption.** It says that pw.x ends a relaxation when the change in F between consecutive configurations is below 10⁻⁵ Ry and every free force component is below the threshold. Only the second criterion is drawn.
    - **Axes.** Log y from 10⁻³ to 10 eV/Å; x from −2 to 202.
  - **b: gates.**
    - **Step-0.** The step-0 |ΔF| of each cell and attempt, on a linear axis from 0 to 1 meV, with the 0.5 meV threshold.
    - **Gate strip.** Below it, the five C2 gates (step-0@1, K2, step-0@4, projection, K3), each in its state from D-C2-10. K3 is shown by its state only.
    - **Caption.** The step-0 values are point values from one pair of calculations each. There is no replicate, so no interval is drawn.
  - **c: cost.** Three strips:
    - `n_config` per relaxation, linear 0-210, with the 65-141 band and a line at 201;
    - `min_per_config`, linear 0-10 min, with a line at 4.58 min;
    - P after relaxation 4, linear 0-600 node-h, with a line at 520. It shows `P_initial_h` and each applied cut's `P_after_h`.
      - The terms of P are recomputed as `projection({**plan_work(state_in, "after4", done=<labels of a2_completed>), **result.inputs, "a2_completed": a2_completed})`, with `state_in` from the projection's applied-gate file.
      - The build asserts that this gives `P_initial_h`.
  - **All panels.** A value outside an axis is drawn as an edge arrow with its value printed. If C2 stops early, the figure shows what ran, and every gate carries its state.
  - **QA.**
    - The QA of the C1 figure applies: panel alignment, PDF text ≥ 5 pt, the collision audit and source data.
    - Build asserts re-derive every plotted gate state:
      - step-0 from `cells.*.passed` and the outcome;
      - K2 with `k2_eval` from relaxation 1's record;
      - the projection as above;
      - K3 from `decision.K3` and its reason lists only;
      - not reached or skipped by the file rule of D-C2-10, from `gates_applied/`, the state and the A2 records.
- **D-C2-12 (implementation of D-C2-11; recorded on 2026-11-05, before any C2 value exists).**
  - **Script.** `figures/fig_s2_c2_a2.py`. It was developed only on the public WP2e output and on synthetic archives built from it. `--self-test` builds 15 such archives and checks the gate states, the status wording and that the withheld fields do not reach the output. Five more archives must fail a named build assert. Two review rounds checked the script against this section and against `scripts/47`, `49` and `50`; every confirmed finding is fixed.
  - **Blinding.**
    - A2 records, gate files, `state_end.json` and `HARD_CAP.json` are read through a guard. A field is read by its name. Reading `dF_200_180_meV`, `value_meV` or `Eb_A2_meV` raises an error. A guarded object cannot be iterated or printed.
    - The C1 start records are read with the blinded loader of `scripts/46`, which removes every MACE energy.
  - **Decisions taken where the runner allows more than D-C2-10 names [I].**
    - **Step-0 after STEP0_NO_ERROR.** The gate file keeps `fail_pending_fix`, and only the A2 stop state holds `fail_final` (`scripts/50` preconditions). The step-0 outcome in force is therefore read from `state_end.json` (leaf `step0.outcome`, `step0.no_error_found`). If that file is absent, it is read from the runner's `STEP0_NO_ERROR` log line. The state is shown as "fail (fail_final: no error found)". In every other case the build asserts that the state and the last step-0 gate file agree.
    - **K2 after a RESOLVE 'unconverged'.** The gate re-reads the outputs and can record `incomplete` where the record says `unconverged_early`. The build then checks the two decisions with `k2_eval` and shows "fail (\<record outcome\>, operator; gate read incomplete)". A relaxation 1 refused by the hard cap is shown as "fail (\<gate outcome\>; record: not_started_cap)".
    - **Relaxations without an A2 record.**
      - The runner writes a record only for the first job the hard cap refuses. The refused relaxation, and every later one without a record, is shown as "not started (cap)" (from `HARD_CAP.json`).
      - Any other relaxation without a record at a final STOP is "not started (no record)".
      - A pending record with no configuration is "stopped before k = 0".
    - **Projection.** The strip keeps the D-C2-10 wording. cut_order's entry "no applicable cut left" goes to the detail column and to the sequence line of panel c.
    - **Edge arrows.** Every point outside an axis gets an arrow. The arrow glyphs differ from the end glyphs. In panel a the value is printed at the extreme of each excursion and at an end outside the axis.
    - **Cost line.** Manual ledger rows are those with `manual: true`. A ledger that is not complete is flagged with its count of problems and of untimed boots.
  - **Presentation.**
    - Cells are labelled host, V, D and D+V, with "V: iodide vacancy, q = +1" in the legend title. Mathtext sub- and superscripts would fall below 5 pt, and Arial has no superscript plus.
    - The threshold is labelled 0.00078 Ry/bohr = 0.02005 eV/Å, from the `scripts/47` constants that `--build` writes into the source data.
    - The end-glyph legend sits under panel a.

## Dated notice (2026-11-12): status under S2b

Appended under `S2B_PLAN.md` (the commit that adds it), §1. The text above is not edited.
- **For the S2b A2 campaigns `fr` and `c4b`,** this note is re-adopted in substance through the operations note
  committed before each campaign. Those notes cannot change any rule of `S2B_PLAN.md`.
- **D-C2-10 and the Reading rule** lapse at the S2b evaluation E for its blocks 1-3: the far quartet, FR, and MACE with
  the deferred C1 items. They stay in force for the hinge-block items (relaxations 1-4, E_b^A1/A2(Pb136), δ_Sr,m30, the
  step-0 reference F, the Pb136 MACE items) until that block is read (`S2B_PLAN.md` §7).
- **D-C2-8 (disk)** ends only when E has run, its archives have been re-verified, and the hinge block has been read or
  a later pre-registration has taken custody of the C2 tree (`S2B_PLAN.md` §9 step 9).

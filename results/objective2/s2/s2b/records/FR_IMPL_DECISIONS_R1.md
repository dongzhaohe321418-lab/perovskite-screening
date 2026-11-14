# Analyst decisions on the first review of the fr implementation (2026-11-12)

Source: `fr_impl_r1_output.json` (workflow w4vqse0y3): the engineer's report and three reviews
(regression, plan and blinding, test strength with 42 injected mutations). Worktree at 4d27d2d plus the uncommitted
diff. Every finding is decided below. "Fix" items are applied by the fix engineer; "Note" items go into the fr
operations note, which the analyst writes.

## Code fixes

- **F1 (plan lens 1, major). Remove the step-0 STOP mode from `s2b/guard.py`.** Delete `step0_stop`, `_stop_paths`
  and every admission of `result.cells.<SP>.dF_meV` or `.passed`. GateLeaves must be exactly the plan's list:
  `decision.*` and the three named reason lists. S2B §1 says no operations note may alter the guard rules, and §0's
  forward rule keeps every fr DFT energy unread until E, so the OPS2 re-adoption cannot reinstate the D-C2-10 read.
  A step-0 failure is diagnosed from the decision (which cell, which attempt) and from non-energy evidence (pw.x
  logs, environment, inputs), never from dF. Check that the fr_step0 decision itself holds no dF or F value.
- **F2 (plan lens 6).** `GateLeaves.get` raises Blinded when the subtree it would return contains any key of
  `WITHHELD_S2B`, at any depth (dict or list element).
- **F3 (plan lens 2).** Drop `invariant_only` from `decision.FR`. Keep it only as the label list in
  `result.invariant_only`, which E reads after verify. Update `s2b_decision_check`, the runner logs, `cmd_status` and
  the self-tests.
- **F4 (plan lens 3).** STEP0_FIX must name a commit that is a strict descendant of `campaign_commit.fr`
  (head != cc and is-ancestor(cc, head)). For both dated routes (fr/CAMPAIGN_COMMIT and fr/STEP0_FIX), the note path
  must appear in `git diff --name-only <ancestor> <head>`, as well as being tracked and containing the date. Add a
  NodeBackend helper for the changed paths; the MockBackend answers from config lists (see T1).
- **F5 (plan lens 4; tests lens 7).** At fail_pending_fix, STEP0_FIX and STEP0_NO_ERROR both present is a Stop.
  STEP0_NO_ERROR is renamed `.used.<t>` once it has set fail_final. A STEP0_NO_ERROR (or STEP0_FIX) present while
  fr_step0 is not fail_pending_fix is a Stop naming the file, with no state change.
- **F6 (plan lens 5).** With `exchange_n=True`, `check_partner` also reports the invariant rotation summary:
  `max_rot_fa_invariant_deg` and its worst row (object, rotation, rotation exchanged) in `gated` and in
  `within_6A_reported`. The default output stays byte-identical.
- **F7 (regression lens 1; plan lens 7).** `evaluate_gate` binds gates to campaigns: fr_step0 and FR only for
  campaign fr, and campaign fr only for those two gates; otherwise GateRefused, before anything is read or written.
  `verify --campaign fr` follows from this. Tests in `t_fr`. The C2 verify output must stay byte-identical.
- **F8 (regression lens 2).** If the protected-state digest trips inside `begin_stop`, raise a Stop that names the
  changed protected key, and still persist `campaigns.fr = "stopped"`: reload state.json from disk and save only that
  key, through the same protection. state.json and campaign.json must agree afterwards. Test it.
- **F9 (regression lens 3; plan lens 10; tests lens 10).** `s2b/fr_inputs.py`:
  - refuse an `--out` whose real path lies under `--c1`, under `<repo>/results/objective2/s2/{c1,c2,c3,fr}`, or under
    `/data/work/s2`;
  - take the ranks from `state.a2_layout` when a state file is given, and refuse a `--ranks` that differs from it;
  - the archive source is analyst-only: say so in the docstring and the `--help` text, and exercise it in the
    self-test on a synthetic `structures.tar.gz` and records built in a temporary directory (never the real C1);
  - compare its `.p1.in` with what `Runner.a2_launch` writes for the same FR job on a mock tree (spawn stubbed).
- **F10 (plan lens 8).** At `finish()` for fr, `campaign.json` records `fr_outcome`, one of "pass", "fail (FR-1)",
  "fail (FR-2)", "fail (step-0 final; gate not evaluated)", derived from decisions only. The FR state key is not
  written by this.

## Test gaps to close (tests lens)

- **T1 (major).** MockBackend git answers come from config lists (`git_ancestors`, `git_tracked_paths`,
  `git_changed`, the changed-path lists of F4), so arguments matter. z29: refuse a STEP0_FIX whose commit does not
  descend from `campaign_commit.fr`; accept one that does. Add a real-git unit case (z19 style, in a temporary
  repository): commits A -> B and a side commit C; is_ancestor(A,B) True, (B,A) False, (B,C) False; tracked True/False;
  unchanged True/False; the changed-path helper of F4.
- **T2 (major).** A STEP0_FIX repeat at D+V+ (`@4`): plant both marker trios and assert that exactly
  `a2/s2r_m30_Cs188o0_vac/...`, `gates/fr_step0.json` and the `gate_fr_step0_4` trio move, and that the `_2` trio and
  the other cells stay.
- **T3 (major).** The guard canary plants every field of `WITHHELD_S2B - fig.WITHHELD` in synthetic A2 and validity
  records, nested in a dict and inside a list element; each `get` raises and `open()` on the parent raises. Track
  record hits apart from gate-file hits and assert that each covers all of `WITHHELD_S2B`.
- **T4.** The `fr_next` launch filter: call `a2_phase` directly with no runnable a2v job and `fr_next is None`; nothing
  launches. With `fr_next` set to the third cell, only that cell launches.
- **T5.** `run_a2v` Stops on a validity without `check5_reading`, and the record gets no `validity_final`.
- **T6.** `gate_inputs(@4)` gives attempt 2 for `{"outcome": "pass", "repeat": True}`.
- **T7.** With F5: STEP0_NO_ERROR at pass and at repeat_pending Stops and leaves the state unchanged.
- **T8 (replaces "STOP mode on two cells").** In a failed fr_step0 file with one and with two cells, every
  `result.cells.*.dF_meV` and `.passed` raises.
- **T9.** After the mock CAMPAIGN_DONE, run `g49.evaluate_gate("FR", ...)` on the runner-written records (FR-1 fails
  at V+, so no energy is opened) and assert its decision equals `(fr_stop.at, fr_stop.kind)`.
- **T10.** As in F9, last item.

## Notes for the fr operations note (analyst)

- N1 (plan lens 1): D-C2-10's read of the failing step-0 dF is not re-adopted for fr; S2B §1 governs.
- N2 (engineer; plan lens): one step-0 repeat for FR as a whole (spec §10.2).
- N3 (plan lens 9): the §8 projection at the FR decision is computed after FR ends and before any c3b cell, with
  inputs fixed at FR's end; if FR fails there is nothing to project.
- N4 (regression lens 4): `s2_campaign.sh` at the S2b commit starts fr only; any c1-c4 action needs a checkout at
  8bff03e. c1-c4 starts at another HEAD return 2 and write nothing.
- N5 (regression lens 5): `status` prints a second "state (S2b):" line with decisions only.
- N6 (engineer): D4 (fr_inputs pair comparison) is decisive on the node, with the node's ase and ranks.
- N7 (plan lens 11): the §6b tools, E blocks 1-3 and 5 and this note are separate deliverables before the FR boot.

## Process

- The tests reviewer overwrote another agent's `base` copy in a shared work area. Every agent from now on works
  only in its own uniquely named private work directory.

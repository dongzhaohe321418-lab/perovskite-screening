# FR figure (figures/fig_s2b_fr.py): the analyst's rulings after review round 2 (2026-11-12)

Basis: workflow w0vdps3rh (engineer, two review rounds with a science-plan-blinding lens and a test-strength lens,
two fix rounds). Fix round 2 left the file at sha256 5077bcef… (2647 lines) in W4, with no review of its own. The
rulings below settle the three choices fix round 2 left to the analyst and add one small change. No value was read to
make any of them.

## Rulings

- **FG-1 (band after an early stop with a step-0 repeat).** Accepted as fix round 2 made it: the lighter band runs
  from 29 to 72 node-hours, labelled as the plan's bound on an FR failure with a step-0 repeat. Reason: S2B_PLAN.md
  §8 (lines 771 and 775) gives "on FR failure 6-58 (with a repeat, up to 72)"; a figure that hides the plan's own
  bound would understate it.
- **FG-2 (when a STOP is final).** A STOP of fr is final only through the stop note E reads (E_DECISIONS_R2 ER2-11;
  OP-19 of E_IMPLEMENTATION_SPEC.md): a committed, clean, dated note under results/objective2/s2/ (not under s2b/)
  that states "the fr STOP is final". The figure takes `--stop-note NOTE` (a normalised repository-relative path)
  and applies the same tests as E: `e_eval.stop_note_ok` (same phrase, same date rule, same location rule) and the
  committed-and-clean test of `e_eval.Run.note_ok` (tracked, unchanged in the tree, text read from HEAD). The
  self-test may run the git test on a synthetic repository. On a stopped fr campaign:
  - with no valid stop note, every build refuses with a named need() (the step-0-pending refusal of fix round 2
    becomes one case of this rule);
  - with a valid stop note, the STOP is drawn as final, including at a step-0 fail_pending_fix with no route taken,
    and the source data records the note's path and sha256.
  The self-test pins the figure's phrase and rules against `e_eval.py` (STOP_PHRASE, ISO_DATE and `stop_note_ok`)
  once both files sit in one tree, and adds scenarios for: a stop without a note (refused), with a note lacking the
  phrase (refused), with a note under s2b/ (refused), and with a valid note at a step-0 fail_pending_fix (drawn,
  sha256 in the source data). Reason: E and the figure must agree on which STOP is final; a figure built on a STOP
  that is not final would show a provisional state as a result.
- **FG-3 (identical-atom flag on FR failures).** Kept on FR-1 and FR-2 failures as well as on a pass. Reason: S2B §2
  (line 267) flags every check-5 pass that needs the invariant reading, whatever the FR outcome, and §1 (line 160)
  attaches the same words to the FR label.
- **FG-4 (cosmetic).** In the pass scenario FR's detail wraps a lone "D" onto a second line. Reword or rewrap so no
  line holds a single token; all QA gates must still pass.

## Review round 3

The integrated file in W gets a third review (science, plan and blinding; test strength) with the rules of rounds
1-2, focused on the fix round 2 changes and FG-1 to FG-4. Every fix needs a self-test assertion that fails on the
code before it.

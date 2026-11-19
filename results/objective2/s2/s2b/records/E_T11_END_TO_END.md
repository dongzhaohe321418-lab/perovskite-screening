# E, block 4: independent review of the integration and an end-to-end test (2026-11-17)

Written on 2026-11-17, while campaign c3b runs and before any c3b file has left the node. No S2b energy has been read.
This record changes no file of E: `e_eval.py`, `e_guard.py`, `e_read.py`, `e_block4.py` and `e_selftest.py` are
those of the c3b campaign commit `e5883d5` (and of `840ad22`), so E needs no `--amendment` on its account.

## 1. The review

A second reader reviewed, by reading only, the integration of block 4 into `e_eval.py`, case T10 and the STOP rule
of amendment 2026-11-16a (the parts that amendment lists as "no second reader"). Result: no blocking defect; by
reading, the six edits of `e_eval.py` and `tier_route` print no wrong value or label, hide no failed cross-check
and admit no wrong stop note. Findings:

1. **Major.** No test ran block 4's own `tier_route`, `build_tier_table` and `e_guard.C3bAccess` inside a real run
   of E on files of the real format. T7 to T9 use a stand-in for the run object; T10 runs E but takes the table from
   that stand-in and the route from a test double. The admission of the 544 c3b single-point labels at the exit audit
   was not exercised. The first real execution of that path would have been the evaluation itself.
2. **Minor.** Six ways in which T10 could pass on wrong code (labels on rows without the far-site label, a
   cross-check with no result, a double count of a cross-check, the note comparison of `route_admit`, no exit code
   asserted on the stop run, `assert_closed` asserted by presence only).
3. **Minor.** The `assert_closed()` call at the exit cannot detect a c3b file opened after block 4 on the admitted
   routes: such a file is logged as opened in block 4.
4. **Minor.** A hinge run on the route C3B-STOP does not compare the stop note with the standing output.

## 2. Case T11 (answers finding 1 and parts of finding 2)

T11 runs E (`e_eval.execute`) with the real `e_block4` on a throwaway repository on which FR passed, against a
private c3b archive that the runner's own code writes in a child process (`scripts/46` `cell_record`; `scripts/50`
`synthetic_state`, `c3b_site_table` and `archive`; `scripts/49` `c3b_tier`), with planted energies. It covers:

1. route C4B-NOTRUN: exit 0; the tier rebuilt from E's printed rows equals an independent computation on the planted
   energies; every c3b record and single point is opened in block 4 only; the 544 labels are in E's read audit; every
   private file is in the manifest class; the far-site label is exactly on the A1 rows;
2. a record changed after the manifest: INT-SHA at the exit, exit 3;
3. a c3b record opened during block 3: INT-READS, exit 3;
4. route C3B-NOTIER, with cells without a result (an absent record, a pending cell, a given-up cell, an absent job, a
   rejected pair);
5. route C3B-STOP: no `state_end.json`; refused without the stop note, admitted with it; exit 0; the state
   cross-check printed "not evaluated".

It was written by a third person, who had read E's code but not the plan; its cell names and host list come from
`e_block4.py` and were checked against the runner's state and graph. It is independent of block 4 as code, not as
a reading of the plan.

**Result.** The author's run (a copy of `840ad22`): T11 passes; its 10 broken variants are all stopped; the whole
self-test gives 95 of 95 cases and 269 broken variants, 1 not caught (`A9/worktrees_unlisted`, known since amendment
2026-11-16a; it needs a second git worktree). The analyst repeated both runs on 2026-11-17 in a copy holding the E
files and scripts of `e5883d5`: T11 passes with 10 of 10 variants stopped (91 s); whole self-test 95 of 95 cases,
269 variants, 1 not caught (the same). **No defect of `e_block4.py`, `e_guard.py`, `e_eval.py` or `e_read.py`
was found.**

## 3. Why T11 is a patch beside E and not a case inside `e_selftest.py`

`e_selftest.py` is one of E's files. E refuses to run when one of its files differs between the last S2b campaign
commit and HEAD, unless a dated amendment is named (`S2B_PLAN.md` §7; `e_eval.py` `commits_admit`). Committing
T11 into the file would send the one evaluation through that amendment route for the sake of a test. T11 is
therefore kept as a patch: `E_T11_e2e.patch` (sha256 `2e5771a830158abc93dbe4181a92f607cba1532df7f62400908192cab6303669`),
with the author's log `E_T11_e2e_log.txt` (one word of its line 36 was replaced for the repository's
hygiene scan; nothing else was edited). To repeat: in a copy of the repository at `e5883d5` or later,
`git apply` the patch and run `python -B -I results/objective2/s2/s2b/e_selftest.py --case T11 --repo <the repository>`.

## 4. One reading made here

On C3B-NOTIER, E prints e_h(j) for a valid quartet at a host that is not a valid host for the dopant, beside the
line that says so. `S2B_PLAN.md` §7 block 4 lists "per host: e_h(j)" without restricting it to valid hosts, and
`S2_PLAN.md` §12 restricts Y_h, not the per-site print. The print is therefore kept. By reading `_compose`, such a
value enters no Y_h, no pooled statistic and no class; no test shows that.

## 5. What remains untested before E

- Real pw.x outputs of c3b: T11's outputs come from the `scripts/47` generator. The runner's own loop did not
  produce T11's archive; `campaign.json`, gate, pair, region and meta files are written by hand to the runner's key
  sets.
- A c3b file opened after block 4 (finding 3), and a hinge run on C3B-STOP (finding 4). Neither is fixed. A hinge run
  on C3B-STOP is not made without a dated amendment that settles the comparison of the stop note.
- Tampering of a single-point output or of a pair file; a private root other than `results/objective2/s2`.
- An fr with a step-0 repeat before c3b. The DFT residual forces that block 4 prints are compared with the planted
  rows for two single points only (the test's own comment), not for all 544. (Both gaps
  were named in the test author's first notes and dropped from the delivered ones; restored here on 2026-11-19.)
- The remaining T10 escapes of finding 2 that T11 does not reach (the note comparison of `route_admit` with
  near-miss paths; other fail outcomes of fr).
- A defect in these places is expected to show as a refusal or as a failure before output, to which the rules of
  `S2B_PLAN.md` §7 apply. That expectation is not a tested property.

# S3a pre-registration: how the review findings were handled

Record for `results/objective2/s2/S3A_HINGE_PLAN.md`, written 2026-11-26 by the analyst before the note was
committed. The reviews are `S3A_PREREG_REVIEW.md` (round 1, on the first draft) and `S3A_PREREG_REVIEW_ROUND2.md`
(round 2, on the revised draft), by an independent sub-task that did not see the hinge and ran no part of E. The
committed note is the revised draft with the round-2 points applied. No hinge value had been read when any of
these texts was written.

## Round 1

| Finding | Handling in the committed note |
|---|---|
| B1 end states of the run | adopted: new section 5a (refusal, exit 0, exit 1, exit 3, code error) |
| B2 the frozen text | adopted: section 8 step 2 (the record states the commit, blob id and sha256 of the note) |
| B3 size of the 2 k_BT threshold | adopted: section 4 derives it from values public before E, with the disclosure and the two reported-only comparisons (25.7 and 72.7 meV) |
| M1 S1 is raw | adopted: section 3 and the wording of the S1 readings |
| M2 objections missing from section 7 | adopted: section 7 rewritten with the five objections |
| M3 outcome rules decided later work | adopted: outcomes now contribute to the decision of `S2B_RESULT.md` section 12; information state lists the per-host Sr values and the other classes |
| M4 backstop and withdrawal | adopted: section 8 step 7 |
| M5 pre-flight conditions | adopted: section 8 step 3 (the archive condition added in round 2) |
| M6 "never been read" | adopted: "not read, by the project's records" |
| M7 parsing rule fixed after the read | adopted: section 8 step 6; the parser `s3a_read.py` is committed with the evaluation record |
| M8 bite of the test | adopted: section 6, with the reviewer's arithmetic re-computed by the analyst |
| M9 title and question | adopted |
| m1, m4, m6, m7, m8, m10, m11, m12 | adopted as proposed |
| m2 grounds of the expectation | adopted in the round-2 form: the three block-1 and block-2 values are listed and used nowhere |
| m3 "binds" joined to "no repulsion" | adopted: outcome O4; the asymmetry of the allowance is stated as intended (section 4) |
| m5 the 51.4 band of S1 | kept as a description, said to enter no outcome |
| m9 label on the S1 row | adopted, corrected in round 2 (rows `B5.EbA1` and `B5.delta`) |

## Round 2

| Finding | Handling in the committed note |
|---|---|
| N1 "ends in ok" can be undefined | adopted: the rule is "no row of the four carries 'cross-check failed'"; the parser tests that string |
| N2 circular pre-flight; two scopes of "no change" | adopted: HEAD may be a later commit that changes only the record; a refusal is removed without changing the note |
| N3 δ_far values said to be used | adopted: listed and used nowhere |
| N4 which rows carry E's label | adopted |
| N5 gaps (code-error rerun ending in exit 3; missing line in an exit-3 file; tools in a rerun) | adopted |
| N6 withdrawal and other files | adopted in step 7. Checked for this commit: of the files it adds, only the note has a plan status line in its first 40 lines |
| N7 archives unchanged | adopted, in the form "no difference from the commit at which E's attempt 1 ran (`98bb606`)", which E's integrity check then passed |

## Not done

- No third review round was made on the final text; the round-2 changes are the reviewer's own proposed wordings,
  with the one change of form noted under N7.
- Nothing of E was executed in the reviews; that the tool admits the note is a reading of its source. A refusal
  costs nothing and reads nothing (section 5a item 1).
- The parser was written after round 1 and was not seen by the reviewer; its self-test on invented texts is
  committed with it.

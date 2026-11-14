# fr implementation: the analyst's decisions on the round-4 mutation review (2026-11-12)

Basis: the mutation lens of workflow w739j3tt0 (its round-4 mutation harness). Of 169 union mutants, 166 are caught and 3 are
equivalent (Q32, V3_03, V3_04). Its 16 new mutants leave 12 survivors; for each, the reviewer showed a demo that
passes on the base and catches the mutant. No value was read to make any decision below. FR_IMPL_DECISIONS_R1, R3 and
R4 stay in force. Fix engineer 1 of the integration workflow (wt1moq84t) applies these items in W. They change test
code only, unless a row shows a production defect.

## Fixes (each as the reviewer's demo, in its private harness)

- **R5-1 (N4_05).** In z30 and the (fr) mock-node case, assert that campaign.log holds no validity-leaf key on any
  line. Use, for example, `not re.search(r"'valid':|\"valid\":|valid_as_written|validity_final", clog)`, in addition
  to the exact early-stop line.
- **R5-2 (N4_02, N4_03, N4_04).** Closed by R4-1 if its pinned output catches them. Run the three mutants against W's
  scripts/49. If any survives, add D02 or D04 of the demo (the whole decision-run output, and the validity words in the
  refusal-text check). See also IX-8.
- **R5-3 (N4_11, N4_12).** Add the two z29 rows of D11 and D12. A STEP0_FIX or CAMPAIGN_COMMIT leftover present with
  the checkout at another HEAD must Stop, naming the recorded fr campaign commit, with state.json byte-identical.
- **R5-4 (N4_01).** Add the z31 row of D01. Its STEP0_NO_ERROR text is clean raw but breaks the host-name rule as
  JSON. Assert `c46.hygiene_violations(text) == []` for it, so that only the JSON-dump reading refuses it.
- **R5-5 (N4_06, N4_07, N4_10).** In z31:
  - start good_ne with a newline (D06);
  - add a row where the stored note is a proper prefix of a text of 300 characters or fewer (D10). It must Stop with
    state.json unchanged and the file kept.
- **R5-6 (N4_09).** In fr_inputs.py's identity loop, also call `compare(outs[0], ox)`, and assert rc 1 and the line
  "DIFF B: region and pair rebuilt equal to c1".
- **R5-7 (N4_08).** Add the removal row of D08, `campaigns.c3` popped, to z29's protected-change tuple. The N-FR4 Stop
  must name it.

## Not changed

- The equivalent mutants Q32, V3_03 and V3_04 need no test.
- The reviewer's major finding (part_d_read's self-test run in the real tree) is an information-state matter. It is
  ruled in INTEGRATION_DECISIONS.md IX-9, and no code changes.

## Check

After the edits, run the reviewer's union harness and N4 harness against a fresh copy of W
without blinded paths. Every N4 survivor above must now be caught, and no mutant caught before may survive.

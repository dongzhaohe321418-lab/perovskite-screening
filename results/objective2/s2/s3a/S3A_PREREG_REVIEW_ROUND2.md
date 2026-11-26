# S3a pre-registration: review, round 2 (fix check)

Reviewer's report, 2026-11-26. Text checked: the revised draft (sha256 `7c502ac86007714d97b8e20b2733c35b6e849035367fbeaedbf9878e2efe8aee`) (193 lines), against the round-1 review
and `e_eval.py` at `7336e39`.

**Done less than asked.** `e_eval.py` was not run (by instruction); the tool's three text tests were re-typed and
applied. The handling note, the evaluation record and the parser `s3a_read.py` were not seen. The plan documents
were not re-read beyond the lines quoted in round 1. The blind is intact: no forbidden path was opened and I have
seen no hinge energy.

## 1. Round-1 findings against the revised text

| Finding | Status | Lines of the revised text | Remark |
|---|---|---|---|
| B1 end states of the run | resolved in substance | 96-111 | two residues: N1, N5 |
| B2 frozen text | resolved | 146-152 | one residue: N2 |
| B3 size of the 2 k_BT threshold | resolved | 55-65 | derivation and disclosure as proposed |
| M1 S1 is raw | resolved | 46-48, 72-74 | |
| M2 section 7 objections | resolved | 126-139 | |
| M3 outcome consequences; information state | resolved | 83-92; 34-37; 7 | "decision" dropped from line 7 |
| M4 backstop and withdrawal | resolved | 181-188 | one residue: N6 |
| M5 procedure | partly | 153-166, 169 | the condition "c1/, c2/ and fr/ unchanged since their archive commits" was not taken up (N7); N2 |
| M6 "never been read" | resolved | 4-5, 16, 22-24 | |
| M7 parsing rule | resolved | 174-180 | checked against the code, section 3 |
| M8 bite of the test | resolved | 113-122 | |
| M9 title and question | resolved | 1, 15-18 | |
| m1 information state | resolved | 20, 34-40 | |
| m2 grounds of the expectation | partly | 38-40 against 115-121 | N3 |
| m3 O3 joined two cases | resolved | 66-67, 89-92 | |
| m4 rounding | resolved | 50-51 | |
| m5 unused S1 band | resolved | 71 | |
| m6 "class other than a null" | resolved | 13-14 | |
| m7 WP2c and WP2d values | resolved | 30-33 | Pb64 confirmed as WP2d's far site |
| m8 hinge difference | resolved | 52 | |
| m9 label on the S1 row | partly | 48-49 | N4 |
| m10 name "S3a" | resolved | 7-8 | |
| m11 departure named | resolved | 171-173 | |
| m12 "contradicts" defined | resolved | 116-117 | |

## 2. New defects

**Admission tests re-applied to the revised text: all pass.** Deny-list: no match for
`results/objective2/s2/S3A_HINGE_PLAN.md`. Status-line test: line 3 matches, within the first 40 lines.
`E_hinge_output.txt` is named. The note contains its own path. With the status line changed to "WITHDRAWN" the
status-line test fails, as step 7 intends.

**N1 (a rule that can be undefined; the wording was mine). Lines 102-105, "ends in 'ok'".** Two of the four rows do
not end in "ok" when they pass. XC-DSUM-HINGE and XC-MACEPILOT-A1 are written with `has_a1=True`
(`e_eval.py` 2262-2263, 2283-2284), so `Out.row` appends the item-4 label after ": ok" (296-297, 313). The public
`E_output.txt` line 312 shows the form: "...: ok  -- far quartet invalid ...". Read literally, a passing row then
neither "ends in ok" nor "carries cross-check failed", and exit 1 has no rule.
- Proposed text: "The readings apply only if no row of XC-STEP0-C2, XC-K3HINGE, XC-DSUM-HINGE and XC-MACEPILOT-A1
  carries 'cross-check failed'; equivalently, each of the four prints '0 failed' in the CROSS-CHECKS summary. If
  one of them carries it, the outcome is OX."

**N2 (contradiction and a circular condition). Lines 98-100, 150-151, 153-155.**
- Line 154 requires "HEAD at the commit that adds the record", but line 153 has the pre-flight "recorded in the
  evaluation record" and lines 98-99 append a dated line to the record after a refusal. Either act needs a later
  commit, after which line 154 can no longer hold.
- Line 99 forbids changes to "sections 3 to 5a" only; lines 150-151 forbid any change to the file.
- Proposed text. Line 154: "HEAD at the commit that adds the record, or at a later commit that changes only the
  record". Line 153: "the conditions are listed in the record; their results are appended to it before the run".
  Line 99: "removed without changing this file".

**N3 (inconsistency). Lines 38-40 against 115-121.** The information state says δ_far(Pb76) and δ_far(FA188) are
used "as the planning scatter in the pass-probability statement of section 6". Section 6 uses only the public
planning s_δ and names only WP2c, WP2d and the tier as grounds.
- Proposed text for lines 38-40: "δ_far(Pb76) = 21.28 meV (invalid quartet), δ_far(FA188) = −2.16 meV and
  E_b^A2(Pb76) = 16.27 meV (invalid quartet) are listed and used nowhere."

**N4 (inaccuracy). Lines 48-49, "E's label on these rows".** "These rows" are `B5.EbA2` and `B5.delta`. The label is
attached to `B5.EbA1` and `B5.delta`; `B5.EbA2` carries none (kind `Eb_A2`, no `has_a1`; `e_eval.py` 296-297,
2199-2202; item 4 is L_FRVALID on this route, line 1183).
- Proposed text: "E's label on the rows `B5.EbA1` and `B5.delta`, ...".

**N5 (gaps in section 5a and step 6). Lines 106-111, 159, 176.**
- Line 110: the case "the rerun after a code error ends with exit 3" has no rule. `S2B_PLAN.md` line 962 gives one:
  attempt 1's output stands. Proposed addition: "If that rerun ends with exit 3, the readings of attempt 1 stand and
  the code error is reported beside them."
- Line 176 gives OX whenever a line is missing, which is also true of an exit-3 file; line 106 gives a rerun first.
  Proposed: "in an output whose last line is 'E exit code: 0' or 'E exit code: 1'".
- Line 159 ("E's eight tools are unchanged since `e5883d5`") cannot hold for a rerun, which the tool admits only
  after a change of E's files under `--amendment` (`e_eval.py` 862-864, 1305-1317). Proposed: "for a rerun, changed
  only by the dated fix".

**N6 (withdrawal can fail to restore the backstop). Lines 185-187.** The tool refuses the cause `backstop` if any
file added since E passes its tests, not only this note (`e_eval.py` 1403-1405). Step 1 adds files under `s3a/`,
which is not on the deny-list. The round-1 review and this report have no plan status line in their first 40 lines
(checked), so neither passes. The handling note, the evaluation record and the parser were not checked.
- Proposed addition to step 7: "and no other file added since `7336e39` has the status line of a plan in its first
  40 lines together with the name of the hinge output."

**N7 (a dropped pre-flight condition; M5).** If `c1/`, `c2/` or `fr/` differs from its archive commit, the run ends
in INT-SHA with exit 3 (`e_eval.py` 2355-2357) and spends the first of two attempts. Proposed bullet: "`c1/`, `c2/`
and `fr/` show no difference from their archive commits (`git diff --quiet`, which prints nothing)."

No other new ambiguity or contradiction with the plan documents was found. The outcomes O1 to O4 partition the
real line; OX is defined by section 5a and step 6.

## 3. The parsing rule of step 6 against the code

Consistent. The row writer (`e_eval.py` 291, 313) and the three calls (2198-2202):

```python
def row(self, block, rid, kind, text, *, values=None, labels=(), has_a1=False, indent="  "):
    ...
    r.line = indent + text + ("  -- " + "; ".join(t for _, t in uniq) if uniq else "")

o.line(" 5.2 The quartet and gate values")
o.row(5, "B5.EbA1", "Eb_A1", f"E_b^A1(Pb136) from k = 0 = {fm(a1)} meV", values={"Eb_A1_meV": a1})
o.row(5, "B5.EbA2", "Eb_A2", f"E_b^A2(Pb136) = {fm(a2)} meV", values={"Eb_A2_meV": a2})
o.row(5, "B5.delta", "delta", f"δ_Sr,m30 = E_b^A2 − E_b^A1 = {fm(d)} meV", values={"delta_meV": d},
      has_a1=True)
```

- **Indentation.** No `indent` is passed, so each line begins with the default two spaces. The section line has one
  leading space, as the note quotes it.
- **Leading strings.** The three strings of step 6 and the section title are character for character the strings
  of the code (each found once in both).
- **Minus signs.** The formula uses U+2212 in the code and in the note. The number comes from `fm`, `"%.2f" % x`
  (202-203), which writes an ASCII hyphen; the note's pattern `-?\d+\.\d\d` uses an ASCII hyphen. `"%.2f"` can
  write "-0.00", which the note covers, and "nan", which fails the pattern and gives OX.
- **After " meV".** `B5.EbA2` ends there. `B5.EbA1` and `B5.delta` continue with "  -- far-site reference: FR, m30
  FA188, valid". The parser must therefore not anchor the pattern at the end of the line; the note's wording
  ("before ' meV'") allows this.
- **Uniqueness.** Within 5.2 the only other line that starts with "E_b^A2(Pb136)" is `B5.hingediff`, which continues
  with " − E_b^A2(Pb76)" and does not match.

## 4. Not checked

The handling note, the evaluation record, the parser and its test text; any execution of the tool; the private
root; the checkout of the run; `c1/`, `c2/` and `fr/` against their archive commits.

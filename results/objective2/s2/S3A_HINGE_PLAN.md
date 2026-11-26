# S3a: the raw E_b of Sr at the one first-shell quartet that was relaxed with DFT in a constrained region (m30, Pb136), before and after that relaxation

**Status: PLAN (S3a).** Written on 2026-11-26 by the analyst, an AI assistant to whom the PI delegated the research
direction, after the one evaluation E of S2b (attempt 1, 2026-11-24) and before the hinge block of E has been read
by the project. This note is the "later pre-registration that names it as data" of `S2B_PLAN.md` section 7. It
names as data the deferred hinge block, which E writes to `results/objective2/s2/s2b/E_hinge_output.txt`. It
changes no class, gate or control of S2 or S2b. S3a is the pre-registration that follows S2b; it is not the
roadmap's stage S3 (hop barriers).

## 1. Question

E's tier is fixed-geometry: each cell is relaxed with the MACE-MP-0 potential and scored by one DFT single point
(A1). E labels every tier value "relaxation bias not bounded". For Sr, the control dopant and the only dopant for
which E's tier resolves an interaction, one first-shell quartet was also relaxed with DFT in C2 (tier A2): Sr at
Pb136 of the pilot host m30, relaxations 1 to 4. That relaxation is constrained: only the atoms of the region
R(Pb136) move, from the A1 geometry. Its energies have not been read. The question is whether, at that quartet of
a pilot host, the raw E_b is still repulsive after the constrained relaxation, and how far the raw A1 value is from
the raw A2 value. It is not a test of E's class, which rests on eight other hosts.

## 2. Information state

- **Not read, by the project's records** (`C2_RESULT.md` section 8; `S2B_RESULT.md` section 6): the energies of
  relaxations 1 to 4 and the single points of the Pb136 cells of m30. The c1 and c2 archives are public, so this
  rests on the project's reading discipline and cannot be verified from outside.
- **Public before E, and used in sections 3 to 5.** k_BT = 25.7 meV (`S2_PLAN.md` line 40). The four hinge
  relaxations are complete, accepted by the end rule and valid (`C2_RESULT.md` section 2). Raw far-site E_b of Sr
  on m30 at q = +1 and fixed geometry: −5.0 meV at Pb76 (`C1_RESULT.md` section 6) and +3.2 meV at Pb64
  (`dopant_shell/WP2D_RESULT.md`). The planning scatter of a relaxation bias, s_δ = 10 to 21 meV (`S2_PLAN.md`
  lines 88-91).
- **Public before E, and used for the expectation only.** At this site, at a different fixed geometry (the
  whole-cell WP1 MACE geometry, one far site Pb64): +129.4 meV far-referenced at q = 0 (`WP2C_RESULT.md`), and at
  q = +1 +127.7 meV raw, +124.5 meV far-referenced (`WP2D_RESULT.md`). The raw q = +1 value is the closest public
  analogue of S2.
- **The published tier of S2b** (governed by this section; `S2B_PLAN.md` section 7, "Scope"). This note rules that
  it enters no statistic, threshold or selection. Used as planning information only: the Sr tier (mean 123.65 meV,
  interval [60.44, 186.86] meV) for the expectation; the per-host Sr values, m06 included (−0.40 meV), and the
  classes of Cl, Cs and GA, only to name the alternatives for node time in section 5.
- **Values read at E (part c).** δ_far(Pb76) = 21.28 meV (invalid quartet), δ_far(FA188) = −2.16 meV and
  E_b^A2(Pb76) = 16.27 meV (invalid quartet) are listed and used nowhere.

## 3. Statistics (fixed now)

- S2 = E_b^A2(Pb136), in meV, as E prints it (row `B5.EbA2`).
- S1 = δ_Sr,m30 = E_b^A2(Pb136) − E_b^A1(Pb136), in meV, as E prints it (row `B5.delta`).
- Both are raw, not far-referenced. The far reference of Sr at A2 (Pb76) is invalid by check 5, and no other far
  site of Sr was relaxed. The relaxation bias of a far-referenced value is δ_Sr,m30 − δ_far(Sr), and no valid
  δ_far of Sr exists; S1 bounds the bias of the raw first-shell value only. E's label on the rows `B5.EbA1`
  and `B5.delta`, "far-site reference: FR, m30 FA188, valid", refers to the Cs A-site reference.
- The statistics are the printed two-decimal values (`S2B_PLAN.md` line 634). This differs from `S2_PLAN.md` line
  720 (unrounded values) by at most 0.005 meV; the hinge run writes no unrounded E_b.
- Reported, in no reading: E_b^A1(Pb136); E_b^A2(Pb136) − E_b^A2(Pb76), which rests on an invalid quartet; the
  per-relaxation items; the zero-shot MACE value; the WP2c comparison.

## 4. Thresholds, derived from values public before E

- 25.7 meV is k_BT, the resolution that S2 set for a first-shell interaction.
- 51.4 meV = k_BT + a, with a = 25.7 meV for the missing far reference. Derivation: the largest public raw far-site
  value of Sr on m30 is 5.0 meV in magnitude, and the planning scatter of its shift on relaxation is up to 21 meV;
  5.0 + 21 = 26.0 meV, which is k_BT to within 0.3 meV. The allowance covers the largest public far value plus one
  planning standard deviation. It is not a 95 % bound: that would be 5.0 + 2 × 21 = 47 meV, a threshold of 72.7 meV.
- **Disclosure.** When this was written the analyst knew E_b^A2(Pb76) = 16.27 meV and δ_far(Pb76) = 21.28 meV
  (invalid quartet; read at E). The derivation does not use them. Whether the choice was influenced by them cannot
  be shown. S2 is therefore also reported against 25.7 meV (no allowance) and 72.7 meV; these two comparisons enter
  no reading and no outcome.
- The binding band below has no allowance, while the repulsion band has one. The asymmetry is intended: the note
  asks whether a repulsion stands, and a raw value below −25.7 meV contradicts it with or without an allowance.

## 5. Readings (exhaustive; fixed now)

On S1 (a description; only the first band enters an outcome):
- |S1| ≤ 25.70: "raw A1 is within k_BT of raw A2 at the hinge".
- 25.70 < |S1| ≤ 51.40: "raw A1 differs from raw A2 by between k_BT and 2 k_BT at the hinge".
- |S1| > 51.40: "raw A1 differs from raw A2 by more than 2 k_BT at the hinge".

On S2:
- S2 > 51.40: "the raw E_b of Sr is repulsive after the constrained relaxation at the m30 hinge, with a margin of
  k_BT for the missing far reference".
- 25.70 < S2 ≤ 51.40: "repulsive on the raw value; the margin for the far reference is not met".
- −25.70 ≤ S2 ≤ 25.70: "no repulsion beyond k_BT after the constrained relaxation at the m30 hinge".
- S2 < −25.70: "the raw E_b of Sr is attractive after the constrained relaxation at the m30 hinge".

Outcome, and what it contributes to the decision of `S2B_RESULT.md` section 12 on node time. That decision is
taken with the D3(BJ) study and the diagnosis of host m06, not by this note alone:
- **O1, "supported at the hinge"**: S2 > 51.40 and |S1| ≤ 25.70. The hinge gives no ground to place a relaxed Sr
  quartet ahead of other uses of node time.
- **O2, "supported in sign, not in size"**: S2 > 25.70 and not O1. The Sr class of E is reported with S1 at the
  one quartet tested. One relaxed Sr quartet at a production host is put to the PI with its cost.
- **O3, "not supported at the hinge"**: −25.70 ≤ S2 ≤ 25.70. No text of the project states an Sr repulsion beyond
  the fixed-geometry tier. A relaxed Sr test at production hosts is proposed to the PI as the next pre-registration.
- **O4, "contradicted at the hinge"**: S2 < −25.70. As O3, and the contradiction in sign is stated wherever the Sr
  class of E is reported.

No outcome changes a class of E, which stays a fixed-geometry class with its label.

## 5a. End states of the run

1. **Refusal (exit 2).** Nothing is written and nothing is read. A refusal is not the run. Its cause is recorded in
   a dated line appended to the evaluation record and removed without changing this file; if that is
   impossible the note is withdrawn (section 8, step 7).
2. **Exit 0.** The readings and the outcome of section 5 apply.
3. **Exit 1.** The readings apply only if no row of XC-STEP0-C2, XC-K3HINGE, XC-DSUM-HINGE and XC-MACEPILOT-A1
   carries "cross-check failed"; equivalently, each of the four prints "0 failed" in the CROSS-CHECKS summary. If
   one of them carries it, the outcome is **OX, "not evaluable"**: S1 and S2 are reported with that label, no
   reading of section 5 is stated, and no consequence for later work is drawn from this note. Any other failed
   cross-check is reported and does not change the reading.
4. **Exit 3.** No hinge value is printed. One rerun follows under the failure rules of `S2B_PLAN.md` section 7.
   Its file, `E_hinge_output_attempt2.txt`, is then the data named by this note, under the same rules. If it also
   ends with exit 3 the outcome is OX, "not read: E failed". The gate-recorded value (`c2/gates/K3.json`,
   `result.Eb_A2_meV.hinge`) is not opened under this note.
5. **A code error found after output.** The readings are taken from the rerun; both outputs are archived and both
   sets of readings are reported. If that rerun ends with exit 3, the readings of attempt 1 stand and the code
   error is reported beside them.

## 6. Expectation and the bite of the test (stated before the read; not a rule)

- The analyst expects O1: S2 between +80 and +170 meV and |S1| below 25.7 meV. Grounds: WP2c and WP2d at this site
  (public before E) and, as planning information, the production tier. A contradiction is any outcome other than
  O1, or S2 outside +80 to +170 meV; it is reported as such.
- On values public before E and a relaxation bias centred on zero with the planning s_δ (normal; E_b^A1(Pb136)
  between the WP2c flank value +95.6 meV and the WP2d proxy +127.7 meV), the S2 condition is met with a probability
  above 0.98, and |S1| ≤ 25.7 meV with probability 0.99, 0.91 and 0.78 at s_δ = 10, 15 and 21 meV. O1 therefore has
  a prior probability of about 0.78 to 0.99 and is weak evidence. O2, O3 or O4 would be the informative results.
  (The reviewer's arithmetic, checked by the analyst.)

## 7. What a result here can and cannot show

- The quartet is the most favourable case for agreement between A1 and A2 that the project could have chosen: the
  pilot host m30, the WP2c hinge site, where fixed-geometry DFT had already given +129.4 meV (q = 0,
  far-referenced) and +127.7 meV (q = +1, raw), and the only host-dopant set that passed WP2c criterion 4. The site
  was fixed by `S2_PLAN.md` (lines 73 and 553) with those values known; it was not chosen by this note.
- A2 is a constrained relaxation: 69 or 70 atoms of the region R(Pb136) move, the other atoms stay at their
  MACE-MP-0 positions, and each relaxation starts from the A1 geometry. A result here speaks to a local,
  region-restricted DFT relaxation only.
- S1 and S2 are raw. A raw E_b at q = +1 carries an alignment offset that `WP2D_RESULT.md` calls unquantified; the
  public far-site values (−5.0 and +3.2 meV) suggest it is small on m30 at fixed geometry, and nothing measures it
  after relaxation.
- One host, which is not a production host; one of the two first-shell Pb sites (the hinge, not the flank Pb124);
  one pose; PBE without D3 or spin-orbit coupling; one k-point; n = 1, so no interval.
- O1 would not show that the A1 class of Sr holds after relaxation at the eight production hosts, would not explain
  host m06, and would say nothing about any other dopant.

## 8. Procedure

1. This note is committed after `s2b/E_output.txt` (commit `7336e39`) and after an independent review of its draft.
   The review and the handling of each finding are committed with it in `results/objective2/s2/s3a/`, as
   `S3A_PREREG_REVIEW.md` and `S3A_PREREG_REVIEW_HANDLING.md`.
2. The rules are the text of this file at the last commit that changes it before the evaluation record is added.
   The evaluation record, `results/objective2/s2/S3A_HINGE_EVAL.md`, is added in a later commit. It contains the
   path `results/objective2/s2/S3A_HINGE_PLAN.md` in full, the hash of the last commit that changed this file, the
   git blob id and the sha256 of this file, the command of step 4, the pre-flight of step 3 and the statement that
   no hinge value has been read. This file is not changed after the record is added, except by the notices of
   step 7. The result note verifies that the blob of this file at the HEAD printed on line 1 of the hinge output is
   the blob the record states; a read under any other text is reported as void.
3. **Pre-flight.** The conditions are listed in the evaluation record; their results are appended to it before
   the run. None of them opens a hinge file:
   - a full clone (the objects of `8bff03e` present), HEAD at the commit that adds the record or at a later commit
     that changes only the record, `git status --porcelain --untracked-files=all` empty;
   - `s2b/E_output.txt` in the working tree is the committed public copy (sha256 `30804fef…afb5`, `S2B_RESULT.md`
     section 9), with one adding commit; the unedited file is kept outside the working tree;
   - no `E_hinge_output*.txt` and no `figures/source_data/fig_s2b_e_fk_hinge*.csv` exist;
   - `scripts/46` to `50` and E's eight tools are unchanged since `e5883d5` (for a rerun, changed only by the
     dated fix); `C3B_NOTE.md` and the verify records are committed and clean; the parser of step 6 lives outside
     `s2b/`;
   - `c1/`, `c2/` and `fr/` show no difference from the commit at which E's attempt 1 ran, `98bb606`
     (`git diff --quiet`, which prints nothing);
   - the private root holds the c3b archive whose manifest hash is the line of `C3B_NOTE.md`; no c3 or c4b entry in
     either root;
   - `--prereg` and `--prereg-eval` are given as repository-relative paths; the record contains this note's path
     character for character;
   - the interpreter of E's attempt 1: Python 3.12.16, numpy 2.5.4, scipy 1.18.1, ase 3.29.0;
   - standard output is captured to a file.
4. The hinge run, once:
   `python -B -I results/objective2/s2/s2b/e_eval.py --hinge --hinge-cause prereg --prereg results/objective2/s2/S3A_HINGE_PLAN.md --prereg-eval results/objective2/s2/S3A_HINGE_EVAL.md --private-root <private root>`.
5. `E_hinge_output.txt`, `fig_s2b_e_fk_hinge.csv` and `fig_s2b_e_fk_hinge_meta.csv` are committed. As for
   `E_output.txt`, the one line that prints the local path of the private root is replaced by "<private root>" in
   the public copy; the sha256 of the unedited file is published and the unedited file is kept privately. This is a
   departure from `S2B_PLAN.md` section 7 ("committed unedited"), dated 2026-11-26, as for `E_output.txt`
   (`S2B_RESULT.md` section 9).
6. S2, S1 and E_b^A1(Pb136) are the numbers on the three lines of " 5.2 The quartet and gate values" that begin,
   after two spaces, with "E_b^A2(Pb136) = ", "δ_Sr,m30 = E_b^A2 − E_b^A1 = " and "E_b^A1(Pb136) from k = 0 = ". In an
   output whose last line is "E exit code: 0" or "E exit code: 1", each must occur once and match `-?\d+\.\d\d`
   before " meV"; otherwise the outcome is OX. The number is read as a
   decimal ("-0.00" as 0) and compared with 25.70 and 51.40. S1 is the printed δ, not the difference of the two
   printed E_b. The parser, `results/objective2/s2/s3a/s3a_read.py`, is committed with the evaluation record and
   tested there on an invented text. The readings are reported in `results/objective2/s2/S3A_HINGE_RESULT.md`,
   which quotes the three lines.
7. **Backstop of this note** (it replaces 2027-06-30; `S2B_PLAN.md` section 7): 2026-12-31, UTC. The run of step 4
   is made on or before that date, always with `--hinge-cause prereg`; from the commit of this note the tool
   refuses the cause `backstop`. A run after that date is made under the same rules and reported as a departure.
   The final stop of this note is the commit of `S3A_HINGE_RESULT.md`.
   **Withdrawal** is possible only before any hinge value has been read, for a reason stated in a dated notice in
   this file. In the same commit the status line becomes "Status: WITHDRAWN", so that the tool no longer treats
   this file as a pre-registration and the 2027-06-30 backstop of `S2B_PLAN.md` applies again; no other file added
   since `7336e39` has the status line of a plan in its first 40 lines together with the name of the hinge output. `S2B_PLAN.md` has no
   rule for a withdrawn pre-registration; this one is this note's own, named here.

## 9. After the read

The hinge values are then values read at an evaluation. They may not enter a statistic, threshold or selection of a
later pre-registration; they may inform its planning, listed in its information state.

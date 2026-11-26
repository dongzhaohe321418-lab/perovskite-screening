# Adversarial review of the draft pre-registration `S3A_HINGE_PLAN.md` (S3a, the hinge read)

Reviewer's report, 2026-11-26. Draft reviewed: the first draft (sha256 `33eee83cbb8b693d1f6f2e39934bf10dcd400b0fdb5eb2bd2fec4da007a0b1c7`) (106 lines). Repository: anonymous
clone of `perovskite-screening`, branch `feat/dopant-shell-dft-validation`, HEAD `7336e39`.

## 0. What was done less than asked, and the state of the blind

- **Nothing was executed from `e_eval.py`.** Every statement about what the tool admits rests on reading its source
  (`e_eval.py`, and the functions of `e_block4.py`, `e_read.py`, `e_guard.py` that the hinge route calls). The verdict
  "the tool will admit the note" is therefore a reading of the code, not a test. Two regular expressions of the tool
  (`NOTE_DENY`, `STATUS_PLAN`) and the string test were re-typed and applied to the draft text and the two proposed
  paths; that is the only code run against the draft.
- **Read in part only:** `e_guard.py`, `e_read.py`, `e_block4.py` and `e_selftest.py` (targeted searches and the
  functions named below, not the whole files); `S2_PLAN.md` (lines 36-54, 70-93, 129-165, 392-404, 549-655, 718-760,
  1290-1297, 1406-1416); `S2B_PLAN.md` (lines 14-20, 86-104, 284-296, 513-530, 618-634, 690-754, 830-841, 958-976,
  1148-1158); `C1_RESULT.md` (one line of section 6); `WP2C_RESULT.md` and `WP2D_RESULT.md` (the m30 rows and the
  method caveats). `C2_RESULT.md` sections 0-2, 4, 7, 8 and `S2B_RESULT.md` sections 1-4, 6, 9-12 were read in full.
- **Not verified because it would touch blind or private material:** that `c1/`, `c2/` and `fr/` are unchanged since
  their archive commits; the private root and the c3b archive; the checkout in which the hinge run will be made.
- **The blind.** No file under `results/objective2/s2/c2/`, `c1/records`, `c1/raw`, `c1/gates*` or `fr/`, and no file
  whose name contains "B136", "Sr136" or "Ca136", was opened, searched, hashed or printed. I have seen no hinge
  energy. One search of the public `s2b/E_output.txt` for the string "136" was too broad and displayed residual-force
  lines of A1 cells outside Pb136 (atom index 136 in other cells) and step counts of the far quartet; these are
  public rows of block 1 and block 3 and contain no Pb136 quantity.
- **Provisional numbers.** The pass probabilities in finding M8 are my own arithmetic under a stated assumption
  (zero-mean normal relaxation bias with the planning s_δ); they are illustrations, not results.

## 1. Verdict in brief

The draft is admissible to the tool as written, its two statistics are exactly two rows that block 5 prints, and
its bands partition the real line. It is not yet fit to commit. Three points would leave the reading undefined or
open to choice after the read (blockers B1-B3). Nine points leave the reading defined but exposed to a serious
objection or in conflict with the plan documents (M1-M9). Twelve are matters of wording and citation (m1-m12).

| Question | Short answer | Findings |
|---|---|---|
| 1. Admission by the tool | Yes, by source reading. The procedure omits several conditions of the run. | section 2; B2, M5, M4 |
| 2. S1 and S2 against block 5 | Exact match in name, unit, sign and "raw". S1 is raw as well, which the draft does not say. | section 3; M1, M7 |
| 3. "Later use" | No statistic uses an E value. The size of the 2 k_BT threshold is not justified without one. Information state incomplete. | B3, M3, m1, m2 |
| 4. Forking paths | Bands exhaustive and exclusive. End states of the run (exit 1, exit 3, attempt 2, two failures) have no rule. | B1, M7, m3, m4 |
| 5. Scientific adequacy | Defensible only as a one-sided screen with a one-SD margin. Section 7 omits the strongest objections. | B3, M1, M2, M8 |
| 6. Over-claims and contradictions | Title, "never been read", "DFT relaxation", outcome consequences against `S2B_RESULT.md` section 12. | M3, M6, M9, m5-m12 |

## 2. Question 1: admission by `e_eval.py --hinge --hinge-cause prereg`

Conditions in the order the code applies them (`e_eval.py`, line numbers at `7336e39`).

| # | Condition | Code | Draft as written, at the proposed paths |
|---|---|---|---|
| 1 | Python >= 3.12 with `tarfile.data_filter` | 641-642 | not stated in the draft (M5) |
| 2 | clean tree, untracked files included (`git status --porcelain --untracked-files=all`) | 645-646 | not stated (M5) |
| 3 | no `E_hinge_output.txt`, no `fig_s2b_e_fk_hinge.csv`, no `fig_s2b_e_fk_hinge_meta.csv`; the first hinge run takes no `--rerun-cause` | 780-796, 732-734 | holds at `7336e39` (names listed only) |
| 4 | no c3 entry in a root; the private root not under the public root | 655-657 | depends on the checkout (M5) |
| 5 | route admission: `fr/campaign.json` done; FR pass, so `e_block4.tier_route` runs: `--private-root` is required, no c4b entry in either root, c3b done with `c4b_run` false, `C3B_NOTE.md` and `c3b_verify/verify_c3b.txt` committed and clean, the private c3b manifest complete | 930-997; `e_block4.py` `tier_route` | the command of step 3 carries `--private-root`; the rest is not stated (M5) |
| 6 | verify records of c2 and fr committed and clean | 999-1008 | holds at `7336e39` if untouched |
| 7 | a standing evaluation output exists and contains "BLOCK 5. Hinge block: not opened" | 1338-1346, 1378-1380 | holds: `E_output.txt` line 6864, last line "E exit code: 0" |
| 8 | `E_output.txt` tracked, unchanged in the working tree, with exactly one adding commit | 736-741, 1381-1385 | one adding commit, `7336e39` (checked with `git log --no-renames --diff-filter=A`) |
| 9 | deny-list: the note is not `S2B_PLAN.md`, `S2_PLAN.md`, `*_OPERATIONS.md`, `*_RESULT.md`, `*_DIAGNOSTIC.md`, anything under `s2b/`, an E output or the E figure | 136-137, 1352-1353 | `results/objective2/s2/S3A_HINGE_PLAN.md` matches neither pattern (regex applied: False, False) |
| 10 | the note is a normalised repository-relative path, tracked, clean, a blob of HEAD | 800-813 | pass `--prereg results/objective2/s2/S3A_HINGE_PLAN.md`, not an absolute or `./` path |
| 11 | the note has exactly one adding commit, strictly after the commit that added `E_output.txt` | 1355-1360 | holds if first committed on top of `7336e39` and never deleted, re-added or renamed |
| 12 | the note's adding commit is dated (UTC) before 2027-06-30 | 117, 1361-1362 | holds |
| 13 | a line among the first 40 matches `\bStatus: PLAN\b` | 141, 1363-1364 | line 3 of the draft: "**Status: PLAN (S3a).**" matches |
| 14 | the text contains `E_hinge_output.txt` | 1365-1366 | 3 occurrences |
| 15 | the record is tracked, clean, has exactly one adding commit, strictly after the note's adding commit | 1390-1393 | step 2 of the draft; the record cannot share the note's commit |
| 16 | the record contains the `--prereg` argument as a substring | 1394-1395 | the draft says only "names it" (M5) |
| 17 | commits: E's files present at the fr and c3b campaign commits; `scripts/46-50` and E's eight tools unchanged from S2B_LAST (`e5883d5`) to HEAD, else `--amendment` | 1262-1322 | `git diff --stat e5883d5 7336e39` over the 13 paths is empty; must stay so (M5) |
| 18 | phase 0b and phase 1: imports at `8bff03e` from the object store, numpy, scipy, ase; every file opened under a root equals its archive-commit or HEAD blob | 690-712, 2317-2357 | needs a full clone and untouched archives (M5) |

What the tool does **not** check, and the note must therefore fix itself:
- It reads the note and the record as blobs of HEAD at the time of the run (800-813). The text may change between
  its first commit and the run without any refusal (B2).
- It takes no hash of `E_output.txt`. The public copy with line 84 replaced is accepted as the standing output,
  provided the working-tree file is byte-identical to the committed public copy; if the checkout still holds the
  unedited file at that path, the clean-tree test refuses the run (645; 739-740, "is not committed unedited").
- It does not know this note's own backstop (2026-12-31). Once a file that passes conditions 9-14 exists at HEAD,
  the cause `backstop` is refused for good (1403-1405) (M4).
- A refusal is exit 2 with nothing written (631-636). It spends no attempt and reads no hinge value.

## 3. Question 2: S1 and S2 against what block 5 prints

| Draft | Row printed in hinge mode | Code | Plan |
|---|---|---|---|
| S2 = E_b^A2(Pb136), raw, meV | `B5.EbA2`: "E_b^A2(Pb136) = %.2f meV", from the final F of relaxations 1-4, `eb()` = ((F_DV − F_D) − (F_V − F_host)) × 1000 | 2195, 2200; 251-255 | `S2B_PLAN.md` 699-702; `S2_PLAN.md` 37, 140 (positive = repulsion) |
| S1 = δ_Sr,m30 = E_b^A2 − E_b^A1, meV | `B5.delta`: "δ_Sr,m30 = E_b^A2 − E_b^A1 = %.2f meV" | 2196, 2201-2202 | `S2_PLAN.md` 39, section 11 "δ" (A2 − A1, E_b^A1 from the k = 0 F) |
| E_b^A1(Pb136), reported | `B5.EbA1`: "E_b^A1(Pb136) from k = 0 = %.2f meV" | 2194, 2199 | `S2B_PLAN.md` 629, 700 |
| E_b^A2(Pb136) − E_b^A2(Pb76), reported | `B5.hingediff`, label "not a K3 decision; K3 failed on validity" | 2224-2226; 163 | `S2B_PLAN.md` 702 |

Names, units, sign and "raw" agree with the draft. Three points the draft leaves out:
- **Precision.** The rows print two decimals (`fm`, 202-203; `S2B_PLAN.md` 634). No unrounded E_b is written
  anywhere in the hinge output; the CSV holds F(k) curves only (2547-2571). "As E prints it" is therefore the only
  tool-derived form, but `S2_PLAN.md` line 720 says "All statistics use unrounded values" (m4).
- **S1 is raw too.** It is the difference of two raw values at one site; δ_far is not subtracted (M1).
- **Labels.** On this route `B5.EbA1` and `B5.delta` will carry "far-site reference: FR, m30 FA188, valid"
  (296-297; `S2B_PLAN.md` 632). That label refers to the Cs A-site reference and must not be read as "S1 is
  far-referenced" (m9).

---

## 4. Findings

### Blockers (the reading could be undefined, or open to choice after the read)

**B1. The readings cover the values but not the end states of the run.**
- Evidence. Draft lines 19 ("From `E_hinge_output.txt`"), 90-92 ("once"; "E's own rules apply to a failure or a
  rerun"). Tool: exit 1 when any cross-check fails, with every value printed (`e_eval.py` 1446, 2384-2392;
  `S2B_PLAN.md` 739-740); exit 3 on an integrity failure or an exception, with a failure report that prints no value
  and, in hinge mode, no fallback (2446-2451: the fallback is for `mode == "evaluation"` only); a rerun writes
  `E_hinge_output_attempt2.txt` and "There is no third" (780-790; `S2B_PLAN.md` 966); a value that cannot be formed
  raises in block 5 and ends as exit 3 (251-255, 2194-2196).
- Why it matters. (i) After exit 1 the analyst holds S1 and S2 beside a failed cross-check and no rule says whether
  the readings apply. That is a choice made with the values in view. (ii) After a rerun the data are in a file the
  note does not name. (iii) After two failures the hinge can never be read by E's block 5, and the note is silent.
- Proposed text, new section 5a "End states of the run":
  > 1. **Refusal (exit 2).** Nothing is written and nothing is read. A refusal is not the run. Its cause is recorded
  >    in the evaluation record and removed without changing sections 3 to 5a of this note; if that is impossible
  >    the note is withdrawn (section 8, step 6).
  > 2. **Exit 0.** The readings and the outcome of section 5 apply.
  > 3. **Exit 1.** The readings apply only if every row of XC-STEP0-C2, XC-K3HINGE, XC-DSUM-HINGE and
  >    XC-MACEPILOT-A1 ends in "ok". If one of them carries "cross-check failed", the outcome is **OX, "not
  >    evaluable"**: S1 and S2 are reported with that label, no reading of section 5 is stated, and no consequence
  >    for later work is drawn from this note. Any other failed cross-check (XC-MACE-COUNT; a row of blocks 1 to 3)
  >    is reported and does not change the reading.
  > 4. **Exit 3.** No hinge value is printed. One rerun follows under `S2B_PLAN.md` lines 728-729 and 966. Its file,
  >    `E_hinge_output_attempt2.txt`, is then the data named by this note, under the same rules. If it also ends
  >    with exit 3 the outcome is OX, "not read: E failed". The gate-recorded value
  >    (`c2/gates/K3.json`, `result.Eb_A2_meV.hinge`) is not opened under this note.
  > 5. **A code error found after output** (`S2B_PLAN.md` 737-738, 962). The readings are taken from the rerun;
  >    both outputs are archived and both sets of readings are reported.

**B2. The frozen text is not identified, and the tool does not freeze it.**
- Evidence. Draft lines 87-88 allow the review's findings and "their handling" to enter "the same commit or the
  next". The tool reads the note as the HEAD blob at run time (`e_eval.py` 800-813, 1354) and tests only its adding
  commit (1355-1360). An edit of sections 3-5 after the first commit, or after the record, is accepted silently.
- Why it matters. A reader cannot tell which text bound the read.
- Proposed text, replacing step 2 of section 8:
  > 2. The rules are the text of this file at the last commit that changes it before the evaluation record is
  >    added. The evaluation record, `results/objective2/s2/S3A_HINGE_EVAL.md`, is added in a later commit. It
  >    contains the path `results/objective2/s2/S3A_HINGE_PLAN.md` in full, that commit's hash, the git blob id and
  >    the sha256 of this file, the command of step 3, and the statement that no hinge value has been read. This
  >    file is not changed after the record is added, except by the notices of step 6. The result note verifies
  >    that the blob of this file at the HEAD printed on line 1 of the hinge output is the blob the record states;
  >    a read under any other text is reported as void.

**B3. The size of the 2 k_BT threshold is not "justified without any value read at E".**
- Evidence. Draft lines 40-45: "the missing far reference is allowed one k_BT. The size of that allowance is a
  choice". `S2B_PLAN.md` 747-748: no "gate threshold ... may be selected by such a value. Each must be justified
  without it." The draft's own information state (lines 26-28) records that the analyst knew
  E_b^A2(Pb76) = 16.27 meV and δ_far(Pb76) = 21.28 meV (`E_output.txt` 307-308) when the allowance was set. Both lie
  just inside one k_BT. With 16.27 known, the K3 test of `S2_PLAN.md` 644-645 (difference > +25.7) is equivalent to
  S2 > 41.97 meV, which lies between the draft's two thresholds.
- Why it matters. "A choice" is not a justification, and the one value of the missing far reference that exists
  (invalid, read at E) happens to be covered by the chosen allowance. The plan's rule asks for a derivation that
  stands without it. One exists in values public before E.
- Proposed text for the second bullet of section 4:
  > - 51.4 meV = k_BT + a, with a = 25.7 meV for the missing far reference. Derivation from values public before E
  >   only: the raw far-site E_b of Sr on m30 at q = +1 and fixed geometry is −5.0 meV at Pb76 (`C1_RESULT.md`
  >   section 6) and +3.2 meV at Pb64 (`WP2D_RESULT.md`, "How much of the far-site offset it explains"); the planning
  >   scatter of a relaxation bias is s_δ = 10 to 21 meV (`S2_PLAN.md` lines 88-91); 5.0 + 21 = 26.0 meV, which is
  >   k_BT to within 0.3 meV. The allowance thus covers the largest public far value plus one planning standard
  >   deviation of its shift on relaxation. It is not a 95 % bound: that would be 5.0 + 2 × 21 = 47 meV, a threshold
  >   of 72.7 meV.
  > - Disclosure. When this was written the analyst knew E_b^A2(Pb76) = 16.27 meV and δ_far(Pb76) = 21.28 meV
  >   (invalid quartet; read at E). The derivation does not use them. Whether the choice was influenced by them
  >   cannot be shown. S2 is therefore also reported against 25.7 meV (no allowance) and 72.7 meV; these two
  >   comparisons enter no reading and no outcome.
- If the lead prefers to keep "a choice" without a derivation, `S2B_PLAN.md` line 751 requires a named, dated
  departure in this note.

### Major (the reading is defined, but exposed to a serious objection or in conflict with the plan documents)

**M1. S1 is raw as well, and the draft treats it as the relaxation bias of the class.**
- Evidence. Draft lines 34, 50-52, 61. `e_eval.py` 2194-2196: δ = a2 − a1 at Pb136 alone. `S2_PLAN.md` 136-145:
  the tier statistic Y_h is far-referenced, so its relaxation bias is δ(first shell) − δ(far); section 11
  "Separability" (lines 649-652) adds |δ_far| when it is resolved; amendment 11a line 1411 writes the K3 margin
  in terms of "δ_Sr,m30 − δ_far". No valid δ_far of Sr exists.
- Why it matters. O1 requires |S1| ≤ k_BT with no allowance, while S2 receives one for the same missing term. O1
  would be read as "A1 is within k_BT of A2", which is true of the raw site value only.
- Proposed text. Section 3, S1: add "S1 is a difference of raw values. The relaxation bias of a far-referenced
  value is δ_Sr,m30 − δ_far(Sr), and no valid δ_far of Sr exists; S1 bounds the bias of the raw first-shell value
  only." Section 5, readings on S1: "raw A1 is within k_BT of raw A2 at the hinge", and likewise for the other two.

**M2. Section 7 omits the strongest objections to reading O1 as support for the A1 Sr class.**
- Evidence and objections, in the order a referee would raise them:
  1. *Best-case selection with the answer partly known.* Pb136 on m30 was chosen as "the WP2c hinge"
     (`S2_PLAN.md` 553), a site "whose S1 DFT values are known" (line 73): +129.4 meV far-referenced at q = 0
     (`WP2C_RESULT.md` line 51) and +127.7 meV raw at q = +1 (`WP2D_RESULT.md` line 44; `S2_PLAN.md` 1294 calls it
     "a coarse proxy for E_b^A1(Pb136)"). m30 was kept "for WP2c/2d continuity" and is the host that lacks the
     zero-shot overestimate (lines 70-72); m30 Sr is the only host-dopant set that passed WP2c criterion 4
     (`WP2C_RESULT.md` lines 8-10). The draft's line 83 says only that the site "was not chosen by this note".
  2. *A2 is a constrained relaxation from the A1 geometry.* "atoms outside R_j fixed" (`S2_PLAN.md` 591); 69 or 70
     free atoms of 232 or 233 (`C2_RESULT.md` lines 78-81, 87); the start is the A1 geometry (line 590). The
     frozen shell stays at MACE-MP-0 positions, and the relaxed minimum is the one nearest the MACE start. O1 would
     show stability against a local, region-restricted DFT relaxation, not against DFT relaxation in general.
  3. *The raw value carries an offset the project itself calls unquantified.* `WP2D_RESULT.md` lines 28-32: the
     alignment term "does not cancel in raw E_b(+1)"; raw q = +1 values "carry an unquantified offset of this kind".
  4. *One of two first-shell B site types.* The shell mean of E is over Pb124 and Pb136 (`S2_PLAN.md` 259;
     `e_block4.py` FIRST); `S2_PLAN.md` 579-580 allows "a hinge-flank difference of δ". The flank has no A2 cell.
  5. *The weak point of E's class is host heterogeneity, which the hinge cannot address.* m06 gives Y_h = −0.40 meV
     against 114.25 to 166.47 meV elsewhere (`S2B_RESULT.md` 104-107). Draft line 82 mentions m06 in half a clause.
- Proposed text, replacing section 7:
  > - The quartet is the most favourable case for agreement between A1 and A2 that the project could have chosen:
  >   the pilot host m30, the WP2c hinge site, where fixed-geometry DFT had already given +129.4 meV (q = 0,
  >   far-referenced, WP2c) and +127.7 meV (q = +1, raw, WP2d), and the only host-dopant set that passed WP2c
  >   criterion 4. The site was fixed by `S2_PLAN.md` (lines 73, 553) with those values known.
  > - A2 is a constrained relaxation: 69 or 70 atoms of the region R(Pb136) move, the other atoms stay at their
  >   MACE-MP-0 positions, and each relaxation starts from the A1 geometry. A result here speaks to a local,
  >   region-restricted DFT relaxation only.
  > - S1 and S2 are raw. A raw E_b at q = +1 carries an alignment offset that `WP2D_RESULT.md` calls unquantified;
  >   the public far-site values (−5.0 and +3.2 meV) suggest it is small on m30 at fixed geometry, and nothing
  >   measures it after relaxation. E_b^A2(Pb136) − E_b^A2(Pb76) is printed beside S2, rests on an invalid quartet
  >   and enters nothing.
  > - One host, which is not a production host; one of the two first-shell Pb sites (the hinge, not the flank
  >   Pb124); one pose; PBE without D3 or spin-orbit coupling; one k-point; n = 1, so no interval.
  > - O1 would not show that the A1 class of Sr holds after relaxation at the eight production hosts, would not
  >   explain host m06, and would say nothing about any other dopant.

**M3. The outcome rules decide next work that `S2B_RESULT.md` reserves, and use E values the information state
does not list.**
- Evidence. Draft lines 61-62 (O1: "No DFT relaxation campaign is planned for Sr ... or to host m06"), 66-67 (O3: a
  relaxed test "becomes the next pre-registration"). `S2B_RESULT.md` 161-168: the D3(BJ) study, this
  pre-registration and the m06 diagnosis follow, and "Whether node time is spent on relaxed quartets is decided
  after the three items above." The m06 value and the classes of Cl, Cs and GA are read at E and appear in
  the outcome rules, but the information state (lines 26-29) lists only the Sr tier and three block-1 and block-2
  values. `S2B_PLAN.md` 749-750: "Each use must be listed in that pre-registration's information state."
- Why it matters. O1 rests on n = 1 at the best-case site (M2) and would close the question of a relaxed Sr test
  before two of the three inputs exist. It also contradicts the opening line "It changes no ... decision of S2 or
  S2b".
- Proposed text for the outcome paragraph:
  > Outcome, and what it contributes to the decision of `S2B_RESULT.md` section 12, which is taken with the
  > D3(BJ) study and the diagnosis of host m06 and not by this note alone:
  > - **O1**: the hinge gives no ground to place a relaxed Sr quartet ahead of other uses of node time.
  > - **O2**: the Sr class of E is reported with S1 at the one quartet tested; one relaxed Sr quartet at a
  >   production host is put to the PI with its cost.
  > - **O3**: no text of the project states an Sr repulsion beyond the fixed-geometry tier; a relaxed Sr test at
  >   production hosts is proposed to the PI as the next pre-registration.
  And add to the information state: "the classes of Cl, Cs and GA and the per-host Sr values, m06 included (−0.40
  meV): used only to name the alternatives for node time in section 5."

**M4. The note's backstop has no defined effect, and withdrawal leaves the tool in a state the draft does not
describe.**
- Evidence. Draft lines 98-100. `S2B_PLAN.md` 717-718: the later pre-registration "replaces the backstop below
  with its own dated backstop, no later than its final stop". `e_eval.py` 1397-1406: `--hinge-cause backstop` is
  refused while any file added since E passes the pre-registration tests; nothing in the tool knows 2026-12-31. A
  withdrawn note that keeps "Status: PLAN" in its first 40 lines still blocks the 2027-06-30 backstop and is still
  accepted by `--hinge-cause prereg`.
- Why it matters. The draft does not say what happens on 2027-01-01 if no run was made, the "final stop" is not
  defined, and "the hinge stays unread under the rules of `S2B_PLAN.md`" is not true of the tool after a withdrawal.
- Proposed text for step 6:
  > 6. **Backstop of this note** (it replaces 2027-06-30; `S2B_PLAN.md` lines 717-718): 2026-12-31, UTC. The run of
  >    step 3 is made on or before that date, always with `--hinge-cause prereg`; from the commit of this note the
  >    tool refuses the cause `backstop`. A run after that date is made under the same rules and reported as a
  >    departure. The final stop of this note is the commit of `S3A_HINGE_RESULT.md`.
  >    **Withdrawal** is possible only before any hinge value has been read, for a reason stated in a dated notice
  >    in this file. In the same commit the status line becomes "Status: WITHDRAWN", so that the tool no longer
  >    treats this file as a pre-registration and the 2027-06-30 backstop of `S2B_PLAN.md` applies again.
  >    `S2B_PLAN.md` has no rule for a withdrawn pre-registration; this one is this note's own, named here.

**M5. The procedure omits conditions without which the run is refused or fails.**
- Evidence. Section 2 of this review, conditions 1-6, 8, 10, 16-18.
- Why it matters. A refusal costs nothing, but an integrity failure in phase 0b or phase 1 (exit 3) spends the first
  of two attempts (B1).
- Proposed text, new step 2a "Pre-flight, recorded in the evaluation record; none of these opens a hinge file":
  > - a full clone (the objects of `8bff03e` present), HEAD at or after the commit that adds the record,
  >   `git status --porcelain --untracked-files=all` empty;
  > - `s2b/E_output.txt` in the working tree is the committed public copy (sha256 `30804fef...`, `S2B_RESULT.md`
  >   section 9); the unedited file is kept outside the repository; `git log --no-renames --diff-filter=A` names one
  >   commit for it;
  > - no `E_hinge_output*.txt` and no `figures/source_data/fig_s2b_e_fk_hinge*.csv` exist;
  > - `scripts/46` to `50`, the five files of E, `figures/fig_s2b_e_fk.py`, `figures/fig_s2_c2_a2.py` and
  >   `c2_diagnostic/check5_diag.py` are unchanged since `e5883d5`; `c1/`, `c2/` and `fr/` are unchanged since their
  >   archive commits; `C3B_NOTE.md` and the three verify records are committed and clean; the parser of step 5
  >   lives outside `s2b/`;
  > - the private root holds the c3b archive whose manifest hash is the one line of `C3B_NOTE.md`; no c3 or c4b
  >   entry in either root;
  > - `--prereg` and `--prereg-eval` are given as repository-relative paths; the record contains the note's path
  >   character for character; neither file is ever deleted, re-added or renamed;
  > - the interpreter of E's attempt 1: Python 3.12.16, numpy 2.5.4, scipy 1.18.1, ase 3.29.0 (`E_output.txt`
  >   line 83);
  > - standard output is captured to a file: the tool echoes the whole text, block 5 included.
  And in step 4: "`E_hinge_output.txt`, `fig_s2b_e_fk_hinge.csv` and `fig_s2b_e_fk_hinge_meta.csv` are committed."

**M6. "Never been read" and "Not known to anyone" cannot be verified.**
- Evidence. Draft lines 4-5, 14, 30. `C2_RESULT.md` 217-218: "The archive is public by design (D-C2-7). The
  blinding rests on not opening these fields and not combining the raw energies."
- Proposed text for line 30: "**Not read, by the project's records** (`C2_RESULT.md` section 8; `S2B_RESULT.md`
  section 6): the energies of relaxations 1 to 4 and the single points of the Pb136 cells of m30. The c1 and c2
  archives are public, so this rests on the project's reading discipline and cannot be verified from outside."
  Lines 4-5 and 14: "has been read by the project" in place of "by anyone"; "have not been read".

**M7. The parsing rule is fixed after the read.**
- Evidence. Draft lines 96-97: "a script that parses the three printed values". The statistics are two. E_b^A2(Pb136)
  is printed in three rows (`B5.EbA2`, `B5.wp2c`, `XC-K3HINGE`) and δ in two (`B5.delta`, `XC-DSUM-HINGE`). Values
  are printed with an ASCII hyphen, the formula with U+2212 (`e_eval.py` 2199-2202).
- Proposed text for step 5:
  > 5. S2, S1 and E_b^A1(Pb136) are the numbers on the three lines of " 5.2 The quartet and gate values" that begin,
  >    after two spaces, with "E_b^A2(Pb136) = ", "δ_Sr,m30 = E_b^A2 − E_b^A1 = " and "E_b^A1(Pb136) from k = 0 = ".
  >    Each must occur once and match `-?\d+\.\d\d` before " meV"; otherwise the outcome is OX. The number is read as
  >    a decimal ("-0.00" as 0) and compared with 25.70 and 51.40. S1 is the printed δ, not the difference of the two
  >    printed E_b, which may differ from it by 0.01 meV. The parser is committed with the evaluation record and is
  >    tested there on an invented text; the result note quotes the three lines.

**M8. The expectation is stated, the bite of the test is not.**
- Evidence. Draft lines 73-75. Amendment 11a of `S2_PLAN.md` (lines 1410-1415) found the K3 value test "close to
  certain to pass" on the same public proxies and concluded that "every admission route has a gate with bite".
- Illustration (my arithmetic, provisional; δ taken as normal with mean 0 and SD s_δ, E_b^A1(Pb136) at the WP2c low
  end +95.6 or the WP2d proxy +127.7 meV): P(S2 > 51.4) = 0.98 to 1.00; P(|S1| ≤ 25.7) = 0.99, 0.91 and 0.78 at
  s_δ = 10, 15 and 21 meV; P(O1) is the same to three decimals. The S2 leg has almost no bite; the S1 leg carries
  the test.
- Why it matters. On public values alone, under that assumption, O1 has a probability of about 0.78 to 0.99. Its
  evidential weight is correspondingly small, and a reader should be told so before the read.
- Proposed text added to section 6: "On values public before E (WP2c, WP2d, the planning s_δ of `S2_PLAN.md` lines
  88-91) and a relaxation bias centred on zero, O1 has a probability of about 0.78 to 0.99; the S2 condition alone is
  met with a probability above 0.98. O1 is therefore weak evidence; O2 or O3 would be the informative results."

**M9. The title and section 1 claim more than the quartet can test.**
- Evidence. Draft line 1: "does the fixed-geometry Sr result survive DFT relaxation". The fixed-geometry Sr result
  of E is a far-referenced mean over eight production hosts (`S2B_RESULT.md` line 52); m30 is not among them
  (`e_block4.py` PROD8). Lines 13-15: "relaxed with DFT (A2)", "after relaxation", without the constraint (M2,
  item 2).
- Proposed title: "S3a: the raw E_b of Sr at the one first-shell quartet that was relaxed with DFT in a constrained
  region (m30, Pb136), before and after that relaxation". Section 1, last sentence: "The question is whether, at
  that quartet of a pilot host, the raw E_b is still repulsive after the constrained relaxation and how far the raw
  A1 value is from the raw A2 value. It is not a test of E's class, which rests on eight other hosts."

### Minor

- **m1. Section 2 is the information state that `S2B_PLAN.md` 749-753 requires and should be named so.** The tier
  is not "a value read at E" in the sense of line 752; it "is governed by the next pre-registration's information
  state". Proposed: head the section "2. Information state"; split the third bullet into "The published tier of
  S2b (governed by this section, `S2B_PLAN.md` section 7, 'Scope'): this note rules that it enters no statistic,
  threshold or selection" and "Values read at E (part c): E_b^A2(Pb76), δ_far(Pb76), δ_far(FA188)".
- **m2. Lines 28-29 against lines 73-74.** The three block-1 and block-2 values are said to "inform the expectation
  of section 6", but section 6 names only WP2c and the tier. Proposed for section 6: "Grounds: WP2c and WP2d at this
  site (public before E); as planning information, the production tier (for S2) and δ_far(Pb76) = 21.28 meV and
  δ_far(FA188) = −2.16 meV as the planning s_δ of a pass-probability statement (for S1; `S2B_PLAN.md` line 749).
  E_b^A2(Pb76) = 16.27 meV is listed and used nowhere."
- **m3. O3 joins "no repulsion" and "binds".** A value below −25.7 meV reverses the sign of E's class at the one
  quartet tested. Proposed: "**O4, 'contradicted at the hinge'**: S2 < −25.7", with O3 restricted to
  −25.7 ≤ S2 ≤ 25.7. The binding band has no allowance for the far reference while the repulsion band has one;
  state that the asymmetry is intended, or use −51.4.
- **m4. Rounding.** Add to section 3: "The statistics are the printed two-decimal values (`S2B_PLAN.md` line 634).
  This differs from `S2_PLAN.md` line 720 (unrounded values) by at most 0.005 meV; no unrounded E_b is written by
  the hinge run."
- **m5. The 51.4 band of S1 (lines 51-52) enters no outcome.** Keep it as a description and say so, or drop it.
- **m6. Line 13, "the only dopant with a class other than a null".** E printed "no first-shell interaction beyond
  k_BT" for Cl, "not resolved" for Cs and "no class" for GA (`E_output.txt` 2505-2507). Proposed: "the only dopant
  for which E's tier resolves an interaction".
- **m7. Line 24, the WP2c value.** Add what makes it "different": "q = 0, whole-cell WP1 MACE geometry, one far
  site (Pb64); its raw value is +174.3 meV and includes the neutral-cell band term. The closest public analogue of
  S2 is WP2d's raw q = +1 value at the same geometry, +127.7 meV (far-referenced +124.5 meV)."
- **m8. Lines 19-21 against line 81.** E_b^A2(Pb136) − E_b^A2(Pb76) is listed under "Data named by this note" and
  then "enters nothing". Move it to "Reported, in no reading".
- **m9. The label on the S1 row.** Add to step 5: "E's label on the E_b^A1 and δ rows, 'far-site reference: FR, m30
  FA188, valid', refers to the Cs A-site reference; S1 and S2 are raw."
- **m10. The name "S3a".** `S2B_PLAN.md` line 18: "The roadmap's S3 is a different stage" (hop barriers,
  `SCREENING_ROADMAP.md` 357-361). Add one sentence: "S3a is the pre-registration that follows S2b; it is not the
  roadmap's stage S3."
- **m11. Step 4 repeats E's departure from "committed unedited" (`S2B_PLAN.md` line 525) without naming it.**
  Proposed: "This is a departure from `S2B_PLAN.md` section 7 ('committed unedited'), dated 2026-11-26, as for
  `E_output.txt` (`S2B_RESULT.md` section 9)."
- **m12. "If the read contradicts this" (line 74) is not defined.** Proposed: "A contradiction is any outcome other
  than O1, or S2 outside +80 to +170 meV."

## 5. What I did not check

1. Any behaviour of `e_eval.py` by execution; the self-test; the end-to-end hinge case of `e_selftest.py`
   (line 5720) was located, not read.
2. `e_guard.py` and `e_read.py` beyond the hinge allow-list entries and `c3_entries`; in particular the leaf lists of
   `read_relaxation` and `extend_c1_table_hinge`, and whether block 5 can raise on the real archive.
3. Whether `c1/`, `c2/` and `fr/` at HEAD equal their archive commits (INT-SHA); the private root, the c3b manifest
   and census; the checkout, interpreter and ignore rules of the machine that will make the run.
4. Whether any hinge energy has in fact been read by anyone; this cannot be checked.
5. The figure script `fig_s2b_e_fk.py` in hinge mode, and whether the repository's hygiene scan accepts the hinge
   output with one line replaced.
6. `S2_PLAN.md` outside the line ranges listed in section 0, including section 17 (blinding) and section 18 (power);
   `C2_OPERATIONS.md` (D-C2-10); `FR_RESULT.md`; `C2_DIAGNOSTIC.md`; the roadmap beyond its S3 lines.
7. The physical soundness of the constrained-relaxation protocol itself, the choice of functional, and whether a
   2 k_BT or a 72.7 meV threshold is the better one; finding B3 asks only that the size be derived and disclosed.
8. The quoted values of the draft were checked against the sources named in it (25.7; −5.0; +129.4; 123.65 and
   [60.44, 186.86]; 16.27; 21.28; −2.16; the four hinge relaxations complete and valid). Nothing else in the draft
   was recomputed.

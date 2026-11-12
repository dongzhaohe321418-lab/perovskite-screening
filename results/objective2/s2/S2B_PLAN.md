# S2b pre-registration: an independent far-site reference at m30 FA188, then the A1 tier and the calibration (route D after the C2 K3 failure)

**Status: PLAN (S2b).** Written on 2026-11-11 by the analyst, an AI assistant to whom the PI delegated the S2 research
direction on 2026-11-03 (`S2_DECISION.md`, "Who decided").
- **When.** After the part-d read of amendment 2026-11-11a (`C2_DIAGNOSTIC.md`, commit `57a1afb`, 21:38), and before
  any value of that amendment's part-c list was read. It was revised on 2026-11-12, before its commit, after four
  review rounds (§12).
- **Binding** from the commit that adds it.
- **Changes** are appended as dated amendments, each written before any value it affects is read.
- **Precedence.** Where this file is silent, `S2_PLAN.md` governs. Where they differ, this file governs S2b.

**Conventions.**
- Dates and times are UTC.
- P:n is line n of `S2_PLAN.md` at `1f8e496`; the file has been unchanged since. 11a is that amendment.
- OPS2 is `C2_OPERATIONS.md`, OPS3 is `C3_OPERATIONS.md`, and S0 is `STAGE0.md`.
- [46:n]-[50:n] are lines of `scripts/46`-`50` at `8bff03e`.
- Tags as in P:17-23.
- "The next pre-registration" is whatever study follows S2b. The roadmap's S3 is a different stage.

**Summary.**
- **FR.** S2b first runs one far-site reference quartet, Cs at m30 FA188. Its free region shares no atom with the
  failed Pb76 region beyond the vacancy sphere common to every region. The V⁺-host pair runs first, and FR stops early
  at the first failure (§2).
- **Gate FR** requires the quartet to be valid and |δ_far(FA188)| ≤ 50 meV. Its stated pass probability is
  0.10-0.26 under Jeffreys priors and 0.10-0.19 under uniform ones, and 0.073 at the row-wise minimum (§5).
- **If FR passes,** the A1-tier production C3b follows (§3), then the calibration C4b (§4).
- **If FR fails,** S2 ends without a tier.
- **Reads before E** (each once, by committed tools):
  - G2, a geometry diagnostic of the Pb76 pairs (§6);
  - the FR geometry read (§6b).
- **E, the one evaluation** (§7):
  - It always reads the far half of the withheld C2 values, and every C1 MACE value and deferred C1 item except those
    of the five Pb136 cells, which belong to the hinge block. When C3b ran, it also reads the production MACE values.
  - The hinge half of the C2 values stays blind unless C4b ends with df_δ ≥ 3.

## 0. Information state (11a, part e, item 6)

**Known when this file was written** [R]:
- **Everything listed in P:42-127.**
- **11a part a**, with what its writer knew:
  - the WP2d hinge proxy of +127.7 meV;
  - E_b^A1(Pb76) = −5.0 meV;
  - the in-campaign read of the VB76 check line;
  - the private drafts of the re-plan rejected between 2026-11-09 and 11-11, with their two review rounds.
- **The C1 results** (`C1_RESULT.md`): every pilot value read by the C1 gates. These include:
  - the per-site A1 E_b at the four farthest sites of each sublattice on m30 and m05, among them Cs at FA188 on m30;
  - the pose pilot at FA188 (Cs). Every admissible start reached the default minimum, and two shifted starts were
    inadmissible (`C1_RESULT.md` §3.4).
- **The C2 record** (`C2_RESULT.md`): counts, timings, end rules, validity leaves, gate decisions, `checks_failed`,
  step-0 values and force curves.
- **Every part-d output** (`C2_DIAGNOSTIC.md`; `c2_diagnostic/part_d_read_output.txt`, items 1-5 in full):
  - **The failed pair.** VB76 against hostB76 had 14 gated objects. Two failed: I 209 (0.381 Å) and FA 212 (0.463 Å
    and 24.7°; 177.1° with the nitrogens exchanged). The other twelve stayed at or below 0.183 Å and 13.0°.
  - **The passing far pairs.** They had 16 and 15 gated objects, with at most 0.078 and 0.067 Å and at most 2.0°.
  - **Item 5.** The displacement from the S2-relaxed host exceeded 0.25 Å from k = 156 (I 209). The FA 212 carbon
    exceeded 0.25 Å from k = 158, and its rotation exceeded 20° from k = 172. These are measured against a reference,
    not child against parent. `C2_DIAGNOSTIC.md` line 95 misstates the FA crossing; it is corrected by an erratum
    appended at the S2b commit.
  - **The [I] observations of that note.** The V⁺_R check gates the site sphere. The failure came late, with the force
    near its threshold. Reproducibility is untested.
- **The region geometry** (`c1/regions/*.json`; established after the part-d read):
  - **Shared vacancy sphere.** Every far region on m30 and m05 contains the same 37 atoms of the vacancy sphere
    (inorganic 3, 49, 53, 90, 102, 124-127, 136-138, 232; FA 28, 92, 128). Subtracting it from R(Pb76) gives exactly
    the 14 gated objects of part-d item 3.
  - **Overlap with R(Pb76) on m30, beyond the 37:**

    | region | shared free atoms | of VB76's 14 gated objects, gated again | failing objects |
    |---|---|---|---|
    | X175 | 38 | 10 | I 209 gated; FA 212 fixed |
    | B172 | 25 | 4 | neither |
    | X186 | 8 | 1 | neither |
    | A188 | 0 | 0 | both fixed |
    | A164 | 0 | 0 | both fixed |

  - **Overlap with R(B76) on m05:** A164 shares 0 atoms; A188 and X222 share 8 each.
  - **I175** bridges Pb76 (3.29 Å) and Pb172 (3.27 Å).
  - **R(B136)** contains the same 37-atom vacancy sphere. So the far-block and FR-block energies read at E bear
    weakly on the hinge host and V⁺ legs [I].
  - **I175 is excluded by the overlap rule** of §2, although at 12.77 Å it is the only m30 far site that P counts as
    separable (P:653-656). S2b accepts a non-separable A far site, as P accepted Pb76, in exchange for independence
    from R(Pb76) [I].
  - **The FA188 gated set.** The FR V⁺-host check 5 gates 20 objects beyond the vacancy sphere: inorganic 24, 25, 27,
    36, 37, 91, 100, 160, 162, 163, 172, 174, 184-187, 196-198, and FA188. The equal-charge checks gate the
    vacancy-sphere objects. For comparison, VB136 gated 5 objects (I 139; FA 40, 56, 104, 140).
- **The private record of S2b:**
  - the analyst's start notes, with a prior P(valid far quartet) of 0.25-0.4;
  - the design panel;
  - the decisions R1, R2, R3 and R3a;
  - drafts 1-3 and their three reviews (§12).

**Not read before E** (11a part c, by rule):
- **D-C2-10, "Not read before the one evaluation"** (OPS2):
  - the K3 value and both quartet E_b^A2;
  - δ_Sr,m30 and δ_far(Pb76);
  - every C2 relaxation energy and F(k);
  - F of the two step-0 reference single points;
  - E_b^A1 of every A2 start-set quartet other than gate N's Pb76 value;
  - the plateau differences.
- **The MACE energies:** every C1 E_mace_eV, and the MACE ledger of P §15 with its determinism row.
- **The C1 items deferred to the one evaluation:** the q = 0 link rows (P §10) and the pilots' zero-shot MACE values.
- **After E,** the only part-c values still unread are the block-5 items, and only if block 5 was not opened. Every
  other part-c item is printed in exactly one of blocks 1-3.
- **Forward rule.** Every E_mace_eV and every DFT energy of fr, c3b and c4b stays unread until E, enforced by the
  guard of §1.
- **Reviewers.** Every reviewer or sub-agent that works on S2b material receives this list as binding.

**Choices made knowing the part-d outputs and the facts above.**
- **The far reference:**
  - the site FA188, its rule and the dopant Cs;
  - m30 as host;
  - "no other far site is tried";
  - the rejection of each alternative in §2.
- **Gate FR:**
  - FR's form (validity plus a 50 meV value test);
  - FR's replacement of K3 and of "δ_far valid", and δ_far(FA188) in the separability rule;
  - the prior convention, the per-pair unit and the exposure table of §5.
- **Order and stops:**
  - probe-first, with the early stop;
  - a final step-0 failure ending FR (X6);
  - C3b and C4b only after FR passes;
  - the C4b early stop and the collapsed cut order;
  - the allowance.
- **Reads and reporting:**
  - the per-dopant labels of §1;
  - the split of E into blocks, and the trigger and deferral of the hinge block;
  - the ΔF_tail windows of §7;
  - G2, its objects, its k = 0 square and its reading;
  - the FR geometry read;
  - dropping the transplant single points;
  - the rule on later use.
- **Production:** n = 8.
- **Notes:** the in-substance re-adoption of OPS2 (fr, c4b), OPS3 (c3b) and `D3BJ_AMENDMENT.md`, with the extended
  guard and the publication rule.

**Tolerances fixed now** (items 1, 3, 6):
- check 5: 0.25 Å, 20°, gating beyond 6.0 Å; the invariant reading as D5's (§2);
- the end rule: k ≤ 200, plateau 3 meV;
- FR-2: 50 meV;
- C5: df_δ ≥ 3 and |δ̄_d| ≤ 50 meV;
- step-0: 0.5 meV;
- integrity: 10⁻⁶ Å and 10⁻⁶ meV.

No item-3 gate is needed, because no warm start is used.

## 1. Scope, routes and labels (item 7)

**The question** is unchanged (P:129-157).

| route | condition | delivers |
|---|---|---|
| A1 tier | FR passes; C3b ends with valid hosts | the A1 tier with classes under rule V (P:725-730, 739-761), labelled as below |
| calibrated tier | as above, and C4b ends with df_δ ≥ 3; C1-C5 | validated classes (P:762-777) |
| FR fails (any part; "fail (step-0 final; gate not evaluated)"; a hard-cap refusal; a final STOP in fr) | — | no A1 tier, no class (item 4); E reads blocks 1-3; the hinge block stays blind |
| C3b final STOP (OPS3 D-C3-12), or C3b ends with no A1 tier computable for any decisive dopant | — | as "FR fails", except that FR's pass is reported; C4b is not run |
| C4b final STOP, C4b ends with df_δ < 3, or C4b not run by cut 2 | — | the A1 tier stands; C4b δ (if any) reported only; the hinge block stays blind |
| C4b ends with df_δ ≥ 3, but C1 or C5 fails | — | the A1 tier stands; no validated class; the C4b δ and the hinge block are reported only |

**Labels of the A1 tier, printed on every A1 class and value.**
- **For every dopant:** "fixed-geometry DFT; relaxation bias not bounded. Far-site A2 reference valid at pilot host
  m30, FA188 only (Cs, A f₁, 11.25 Å; S2b FR)[; check 5 passed only under the identical-atom reading]. Invalid at m30
  Pb76 (Sr, B f₁, 11.81 Å; C2, check 5). Valid far references: 1 of 2. No production-host far site is tested at A2. S2
  K3: fail_replan; its value test (P:644-646) was not reached, and no A2 test of the first shell gates this tier."
  - The bracketed clause is printed only when §2 flags it.
- **Per dopant, appended** (the m30 far pairs, P:281):
  - Sr: "B far pair (Pb76, Pb172) untested at A2 (Pb76 invalid)";
  - Cl: "X far pair (I175, I186) untested at A2";
  - GA: "A f₁ (FA188) tested with Cs only; f₂ (FA164) untested";
  - Cs: "A f₂ (FA164) untested".
- **The calibrated tier** replaces "fixed-geometry DFT; relaxation bias not bounded" with the validated-class label of
  `S2_DECISION.md` §7, and keeps every other sentence.

**Re-adopted notes and guards (rules of this file; no operations note may alter them).**
- **Operations notes.** OPS2 is re-adopted for the A2 campaigns `fr` and `c4b`, and OPS3 for `c3b`, in substance.
  Before each S2b campaign an operations note is committed that states, provision by provision, what is kept, adapted
  or superseded.
- **The guard (D-C2-12, extended).**
  - Until E, every tool that reads an fr or c4b A2 record, validity record or gate file reads it through the D-C2-12
    `Guarded` class. The OPS2 exceptions remain: the runner, the `scripts/49` gate code and its verify, and the field
    comparator.
  - For the FR and C4b gate files the guard is an allow-list. Only `decision.*` and the named reason lists can be read:
    failed checks, end-rule failures, and cells not run.
  - For fr and c4b A2 records, WITHHELD is extended by the exact name of every energy field the S2b code writes.
  - A canary self-test on synthetic fr and c4b archives shows that each such field raises.
- **Publication.**
  - The fr archive is public after verify (as D-C2-7). Its blinding rests on the guard and on not combining raw
    energies.
  - The c3b and c4b archives stay private until E (as D-C3-1 and P:964).
- **`D3BJ_AMENDMENT.md`** stays in force in substance: the D3(BJ) row is not reported. Its sensitivity study runs after
  E's output is written.
  - It uses E's printed tables and the sha256 of E's output file in place of `s2_eval.json`.
  - Cells: every cell whose PBE energy enters an E_b that E prints (blocks 1-4; block 5 only once read). Geometries:
    the A1 single points from `cells/<id>/relaxed.extxyz` of C1 or C3b; F(0) from the A2 start; F(final) from
    `a2/<label>/<label>.final.extxyz` of c2, fr or c4b, with the k_last check against E's table.
  - On a branch without a tier the study covers only the E_b that E prints.
  - Classes and controls are recomputed with E's own functions, never by `scripts/48` assemble.
- **Dated notices appended at the S2b commit.**
  - **To S2_PLAN.md:** a pointer to S2b and to X1-X17.
  - **To OPS2:**
    - D-C2-8 ends as §9 step 9 sets out;
    - D-C2-10 and the Reading rule lapse at E for blocks 1-3;
    - they stay in force for the hinge-block items until that block is read.
  - **To OPS3:** re-adopted for c3b through its operations note; the not_run c3 stays private.
  - **To `D3BJ_AMENDMENT.md`:** as above.
  - **To `C2_DIAGNOSTIC.md`:** the erratum of §0.

## 2. The far-site reference FR

**Cells.** m30, at the A far site FA188, Cs at the default pose (p0):
- host_R(A188);
- V⁺_R(A188);
- Cs D(A188);
- Cs D+V⁺(A188).

**Inputs, all in the public C1 archive** [R, by file name]:
- the region `c1/regions/m30_A188.json`: 64 free atoms, 32 inorganic and 4 FA (28, 92, 128 in the vacancy sphere;
  FA188 in the site sphere);
- the pair `c1/pairs/m30_Cs188p0.json`;
- the A1 starts `cells/s2_m30_VA188`, `cells/s2_m30_Cs188p0_novac` and `_vac`;
- host_R from the S2-relaxed host `cells/s2_m30_host`;
- for step-0, the C1 single points `s2_m30_VA188` and `s2_m30_Cs188o0_vac`.

**The rule that fixes the site and the dopant** [M; written after the K3 failure and the part-d read, and disclosed].
1. Take the far sites of m30 (P:281).
2. Keep those whose free region shares no atom with R(Pb76) beyond the 37-atom vacancy sphere. This uses only the
   region files and the identity of the failed quartet (`checks_failed`), not any part-d object or value.
3. Of those, take the farthest from v. If two tie within 0.01 Å, take the lower index.
4. Take the first decisive dopant listed for that site's sublattice in §11's region list (P:630-632), at the default
   pose.

Step 2 gives A188 (11.25 Å) and A164 (10.87 Å). Step 3 gives FA188, which is also the A f₁ (P:272-275). Step 4 gives
Cs. A164 is not run: S2b runs one far reference.

**The kind of cell for item 5.** "A far-reference quartet at an m30 far site whose region is disjoint from R(Pb76)
beyond the vacancy sphere." It is defined by geometry, and the rule selects within it.

**Why this design** [I].
- **Independence.** An independent second test must not re-gate or re-free the failed atoms. At FA188 both failing
  objects are fixed, and no gated object of VB76 is gated again.
- **Successor.** Item 4 allows a stated successor far reference.
- **Pb76 still counts.** Its failure appears in every label ("1 of 2").
- **Bite.** FR passes with a stated probability of 0.07-0.26 (§5).
- **What is not covered.** Sr's B far pair is labelled untested.
- **The gated set differs from Pb76's.** The A region lowers the gated FA from 7 to 1 and raises the gated inorganic
  atoms from 7 to 19. Both kinds failed once in VB76. The sublattice follows from the overlap rule, not from the object
  class.
- **Separability.** FA188 lies within 12.0 Å, as Pb76 did, so separability is not expected to first order
  (P:653-660). As in the plan, it enters through a_far at the calibrated tier.
- **Host.** m30 is kept because the hinge quartet and the original far reference are on m30.

**Protocol.** §11 unchanged (P:590-615):
- the settings of §6;
- start from the A1 geometry, and for host_R from the S2-relaxed host;
- q = +1 for V⁺ and D+V⁺;
- atoms outside R fixed;
- k ≤ 200;
- the end rule;
- the interruptions rule of §13.

**Validity.**
- §11 checks 2-5 on the final geometries.
- Check 5 is read invariantly under the exchange of identical atoms, and that reading decides (11a e item 2, fixed
  before the part-d read).
  - The invariant reading is D5's (`c2_diagnostic/check5_diag.py` at `966aa75`): the FA rotation is the minimum over
    exchanging the two nitrogens with their hydrogens.
  - Carbon, dopant and inorganic displacements are as written.
  - There is no exchange of inorganic atoms or of whole molecules.
- Both readings are reported, and a pass that needs the invariant reading is flagged.

**Step-0.**
- At k = 0 of V⁺_R(A188) and of Cs D+V⁺(A188), |F(k = 0) − F(C1 single point)| ≤ 0.5 meV.
- A failure stops FR. As P:636-638 provides, one repeat on the same cell is allowed, after a dated fix that changes
  no rule. The repeat reruns only the cell whose check failed, from k = 0, and its attempt-1 files are set aside
  unread.
- If no error is found, or the repeat fails, step-0 is final, and FR ends as "fail (step-0 final; gate not
  evaluated)". This departs from P:639, because item 4 forbids an A1 tier without a far reference (X6).

**Order and early stop** [M; applied by committed runner code].
1. host_R(A188).
2. V⁺_R(A188), then its checks 2, 4 and 5 against host_R.
3. Only if that pair is valid: Cs D(A188), then its check against host_R.
4. Then Cs D+V⁺(A188), then its check against V⁺_R.

- **What ends FR as failed:** the first cell that ends without acceptance (unconverged_cap, unconverged_early, missing
  after the §13 reruns, or a hard-cap refusal), or a failed check.
- Cells not started are recorded as not_run_gate.
- During the campaign the operator reads only the stop decision, by field name. The validity leaves are read after
  CAMPAIGN_DONE and verify (D-C2-5, D-C2-10).

**Gate FR** (fail-closed; the admission gate of both routes; evaluated by committed gate code):
- **FR-1:** the four cells are accepted and the quartet is valid.
- **FR-2:** |δ_far(FA188)| ≤ 50 meV.
  - δ_far(FA188) = E_b^A2(FA188) − E_b^A1(FA188), with E_b^A1 from the k = 0 F (P:618-621).
  - 50 meV is C5's admission bound (P:771). FR-2 checks for gross far-site bias. It is not a bound at k_BT, because one
    quartet cannot separate a bias from noise.
  - Only FR-2's decision is read before E.
- **FR replaces K3** (P:644-648) and, in C5, "δ_far valid" (P:771-772).
- **At the calibrated tier, δ_far(FA188) enters only through the separability rule of §4** (P:649-650 unchanged):
  a_far = |δ_far(FA188)| when that exceeds t_{df_δ}(0.975)·s_δ.
  - Because FR-2 admits only |δ_far| ≤ 50 meV, a_far can be non-zero only when s_δ < 50/t: 15.7 meV at df_δ = 3, and
    18.0 meV at df_δ = 4.
  - Otherwise an admitted far bias of up to 50 meV enters no interval. FR-2 only truncates P's rule; it loosens nothing.
  - The coverage figures of P:658-660 (B site, df_δ = 5, no truncation) do not describe S2b.
  - The A1 tier has no far allowance (P:727). Its label "relaxation bias not bounded" covers this.
- **The record.** Pb76 keeps its C2 record. "Valid far references: k of 2" and "S2 K3: fail_replan" stand beside every
  result. No other far site is tried in S2b.

**Options considered and rejected** [I]:
- **Cl at m30 I175** (draft 1): it re-gates I 209 and fixes FA 212, so it is a partial replication.
- **m30 Pb172:** it shares 4 gated objects.
- **m30 I186:** it shares 1.
- **Three new B far quartets with at least 2 of 3 valid:**
  - 79-143 node-h before a decision;
  - a low end of 0.02-0.03 under §5's convention (q from §5, validity only, P = 3q² − 2q³);
  - B172 re-gates 4 objects.
- **Warm-started children at Pb76:** items 2, 3 and 5, and part f.
- **A reported-only production after an FR failure:** it would spend 67-82 node-h without a tier and remove the chance
  of a later blind admission.
- **Transplant single points:** not run, because of their boot and code cost. The ΔF_tail windows of §7 are reported
  only and do not replace a transplant bound.

## 3. Production C3b (only after FR passes)

- **As P §12, with these adaptations:**
  - n = 8 (the C1 n rule);
  - no Ca (G1);
  - default poses (the pose rule);
  - the production hosts of P §3 in draw order.
- **Per host:** 1 host relaxation, 67 frozen MACE relaxations (19 V⁺_Rj; Sr 8, Cs 10, GA 10, Cl 20) and 68 single
  points.
- **Validity:** valid quartets and valid hosts as P:678-690, with check 5 read invariantly. Both readings are
  reported for every C3b check 5, with the count of passes that need the invariant reading, and every affected quartet
  and host value is flagged.
- **Blinding:** P:964-970 until E. The archive stays private until E.
- **A final STOP** follows the routes of §1.

## 4. Calibration C4b (only after FR passes and C3b ends)

- **Cells.** §11's C4 without Ca, in the order of P:630-632, 24 relaxations:
  - m30 X (I138): 4;
  - m30 A (FA128): 6;
  - m05 B (Pb124): 4;
  - m05 X (I49): 4;
  - m05 A (FA28): 6.
- **Protocol, validity and δ** as in §2 and P:590-626. Step-0 and the FR order do not apply.
- **Precondition.** C4b runs only if C3b ended with an A1 tier computable for at least one decisive dopant. It also
  requires K2 pass, the C2 step-0 pass and gate N for Sr, all as recorded in C2, with FR in place of K3. The C2 keys
  stay as recorded and are not read by the fr, c3b or c4b preconditions, which read new keys.
- **Attainable df_δ** = Σ_d max(0, m_d^max − 1), over Sr, Cl, Cs and GA. This is P's df_δ (P:733-734): a dopant
  counts only if m_d ≥ 1. Here m_d^max is the number of d's calibration δ not yet lost (0, 1 or 2).
  - δ_Sr,m30 (the valid C2 hinge quartet) counts as one δ for Sr.
  - A δ is lost on any end-rule or validity failure of its own pair or of its region's shared host_R or V⁺_R, or on a
    cut.
- **Early stop.** C4b stops once the attainable df_δ falls below 3. This uses only end-rule and validity outcomes and
  is applied by committed code. One committed function computes the stop, C5's df_δ and the "C4b ends with df_δ ≥ 3"
  trigger. When every cell is decided, the attainable df_δ equals the realised df_δ.
- **C5:** m_d ≥ 1, df_δ ≥ 3 and |δ̄_d| ≤ 50 meV, with FR (both parts) in place of "δ_far valid".
- **Separability:** as in §2 (P:649-650 unchanged).
- **δ_Sr,m30** enters δ̄_Sr and s²_δ as P:732-736 provides. It is read only in E's hinge block.

## 5. Gates and their pass probabilities (item 1)

**Reading of item 1.**
- Every admission route must pass at least one fail-closed gate whose stated pass probability lies within 0.05-0.95.
- Integrity stops (step-0, UPF hashes) and positive controls (Sr "repels") are not admission gates in this sense.
- Item 1 is applied to the gate FR as a whole, under the adopted reading below.
- FR-2 alone (0.92-1.00) would not meet item 1. As with K3 (P:1415), FR's bite is FR-1's validity.

**Model for FR [MC, before any S2b data].**
- **Prior.** One prior convention for every row: Jeffreys, with uniform as the stated variant.
- **Each row** is the posterior predictive given the C2 evidence. Independence between rows is assumed, which is a
  simplification.
- **The checks 2-4 row** reads "accepted without a non-cap end-rule failure, not missing after §13, and checks 2-4
  passed". In C2: 8 of 8, with no BFGS or SCF end, none missing, and 3 interruptions all recovered.
- **Step-0** passes with probability 1. In C2, 2 of 2 passed at 0.0 meV, and one repeat is allowed.

| factor | evidence | Jeffreys | uniform |
|---|---|---|---|
| no cell reaches the cap (a capped cell is counted as failing, which is conservative) | lognormal fit to the four C2 far counts (log-mean 5.059, log-SD 0.159); joint predictive to plug-in | 0.644-0.773 | same |
| checks 2-4 on four new cells | 8 of 8 C2 A2 cells | 0.821 | 0.692 |
| V⁺-host check 5, per pair | far 0 of 1 / pooled with the hinge, 1 of 2 | 0.25 / 0.50 | 0.33 / 0.50 |
| both equal-charge pairs | 4 of 4 | 0.825 | 0.714 |
| FR-2 at 50 meV | δ_far ~ N(μ, s_δ), μ 0-20 meV (P:658-660), s_δ 10-21 meV (P:88-91) | 0.923-1.000 | same |

**FR** = 0.101-0.262 under Jeffreys and 0.098-0.191 under uniform. The range spans the cap interval, the evidence
pool for check 5 (far 0 of 1 to pooled 1 of 2) and FR-2's interval. Taking each row's least favourable value gives
0.073.

**Unit of the V⁺-host row.** The row is per pair, not per object.
- **Why.** The two VB76 failures are one event: one cell left the common reference late, while its partner stayed
  close. I 209 and the FA 212 carbon crossed 0.25 Å from the reference at k = 156 and 158 of 192, with the force near
  its threshold. Other gated objects of the same cell moved too (I 78, 0.183 Å; FA 68, 13.0°).
- Treating objects as independent would count one drift twice, and would multiply over objects that move together.
- **Exposure sensitivity** (the FA188 check gates 20 objects; VB76 gated 14):

| reading of the V⁺-host row | Jeffreys | uniform | FR (Jeffreys) | FR (uniform) | least favourable |
|---|---|---|---|---|---|
| per pair, far 0 of 1 / pooled 1 of 2 (adopted) | 0.25 / 0.50 | 0.33 / 0.50 | 0.101-0.262 | 0.098-0.191 | 0.073 |
| drift then crossing: E[1−π] + E[π]·E[(1−ρ)^20], with ρ from 2 of 14 | 0.33 | 0.38 | 0.13-0.17 | 0.11-0.15 | 0.095 |
| one failure event per cell (1 of 14, scaled to 20) | 0.26 | 0.18 | 0.10-0.14 | 0.05-0.07 | 0.052 |
| independent objects (2 of 14, scaled to 20; not adopted) | 0.10 | 0.07 | 0.04-0.05 | 0.02-0.03 | 0.020 |

The adopted, drift-then-crossing and one-event readings lie within 0.05-0.95. The independent-object readings do not,
and they are rejected for the reason above.

**The first decision,** the V⁺-host pair alone after two relaxations, passes with 0.16-0.39 under the adopted reading.
This uses the two-cell cap (0.773-0.879), checks 2-4 on two cells (0.818-0.897) and check 5 (0.25-0.50).

**FR-2's operating characteristic** (s_δ = 10 / 21 meV):

| μ (meV) | P(pass) |
|---|---|
| 0 | 1.00 / 0.98 |
| 20 | 1.00 / 0.92 |
| 50 | 0.50 / 0.50 |
| 70 | 0.02 / 0.17 |

**The calibrated route** has a second gate in the band: C5's df_δ ≥ 3.
- **Model:**
  - each near-site quartet is valid with probability p;
  - the shared host_R and V⁺_R of a region pass together with probability √p, and each dopant pair with probability
    √p.
- **p** is estimated at 0.75, the Jeffreys posterior mean from the one valid near-site quartet of C2 (1 of 1), with a
  range of 0.60-0.90.

| p | P(df_δ ≥ 3) | after cut 1: p⁵ |
|---|---|---|
| 0.60 | 0.22 | 0.08 |
| 0.75 | 0.49 | 0.24 |
| 0.90 | 0.83 | 0.59 |

**Controls** (not the bite):
- the A1-tier controls, 0.90-0.99 (P §18);
- C1 at the calibrated tier: 0.82 at df_δ = 3 and s_δ = 20 meV (P:908-911, with Ca). The higher values assume
  df_δ = 5: 0.97 (P:910) and 1.00 at s_δ = 10 meV (P:1053). None was computed for S2b's dopant set, which has
  df_δ ≤ 4.

## 6. G2: the vector double difference at the Pb76 far pairs (geometry only; reported only)

**Purpose.** Whether the site-sphere response of the undoped pair (VB76 against hostB76) recurs in the doped pair
(Sr76o0_vac against Sr76o0_novac). E_b(Pb76) contains both responses, with opposite signs (P:140).

**Inputs** (a closed list):
- The four C2 final geometries, as members `a2/<label>/<label>.final.extxyz` of `c2/structures.tar.gz`, read in
  memory. Each is checked against its record's `final_geometry.sha256`, read as a guarded leaf.
- The four k = 0 geometries, which are the C1 A1 cells: `cells/s2_m30_host`, `s2_m30_VB76`, `s2_m30_Sr76p0_novac`
  and `_vac`, `relaxed.extxyz`.
- `c1/pairs/m30_Sr76p0.json`.
- The 14 gated host indices of part-d item 3: FA 4, 16, 68, 152, 176, 200, 212; I 2, 77, 78, 79, 175, 209; Pb 76.

**Maps** (P §4).
- **Index maps:**
  - host index j to V index: j for j < 127, j − 1 for j > 127; j = 127 is refused;
  - D index: the novac leg's `old_to_new` applied to j;
  - D+V index: the vac leg's `old_to_new` applied to the V index.
- **Elements.** Element equality is asserted, with the dopant member exempt. Pb76 maps to Sr, labelled "dopant site".
- **FA skeletons.** Each FA is found in hostB76 by its carbon and the two nitrogens within 1.6 Å, and then mapped.
- **Frame.** The minimum image is taken in each leg, without alignment. Instead, the fixed atoms of the four cells are
  asserted to agree within 10⁻⁶ Å.
- **Anchors.** D5's gated set must equal the list above, and |Δr_V| and the FA rotations must reproduce part-d item 3
  at print precision: I 209 0.381 Å; FA 212 0.463 Å, 24.7° and 177.1°.

**Printed per object, for the final geometries and again for the k = 0 geometries:**
- Δr_V = r(V) − r(host) and Δr_D = r(D+V) − r(D);
- |Δr_V|, |Δr_D| and |Δr_D − Δr_V|, to 0.001 Å;
- cos(Δr_V, Δr_D), printed only when both lengths are at least 0.02 Å, otherwise "n/a";
- for FA: angle(R_V), angle(R_D) and the angle of R_D R_V⁻¹, to 0.1°. Two labellings are printed: the nitrogen
  labelling carried from the host, and the labelling that minimises the angle within each leg.

**Reading** (described, not sorted into branches):
- whether Δr_D ≈ Δr_V for I 209 and FA 212, and for the other twelve objects: |Δr_D − Δr_V| against |Δr_V|;
- the cosines;
- the FA relative angles;
- the same at k = 0.
- G2 is geometry only and bounds no energy. Whether the VB76 response cancels in E_b(Pb76) also depends on how the
  dopant changes the local stiffness, which G2 does not measure.

**Tool.** A new file in `c2_diagnostic/`. It imports the part-d tools unchanged.
- **Self-tests** on synthetic legs built from the public reference cell:
  - a zero double difference;
  - a pure common translation;
  - a 30° FA turn in one leg only;
  - an index after I127;
  - a displacement across the periodic boundary;
  - the Pb-to-dopant member;
  - a non-identity leg map;
  - a quaternion check: equal rotations give 0°, and equal angles about different axes give a non-zero angle.
- **Discipline.** It reads through the D-C2-12 guard and reads no energy. It asserts that no calculator is loaded. Its
  `--read` refuses uncommitted code.
- **One run.** It prints HEAD, the tool hashes and the K3 part of E's header with "FR: not yet run". It runs once,
  and its output is published unedited.
- No choice of this file depends on it.

## 6b. The FR geometry read (geometry only; reported only)

**When.** Once, after CAMPAIGN_DONE or FR's final stop and after verify, before C3b and before E.

**What it prints.**
- Item 1 of 11a part d (integrity) for every complete FR record.
- Items 2-5 for every FR pair whose check 5 was evaluated, passing or failing: V⁺-host, D-host, D+V⁺-V⁺, up to the
  early stop.
  - Item 2 compares the record with D5 under the deciding (invariant) reading, and R46 with D5 as written.
  - Item 4's reference is the S2-relaxed host for the V⁺ and D children, and the A1 V⁺_R(A188) geometry for the D+V⁺
    child.
- A mismatch in item 1 is printed, and the read ends.

**Tools.** `c2_diagnostic/`, generalised in a dated commit without changing the part-d files.
- Self-tests cover the C2 cases plus an A-site substitution map: one FA (8 atoms) is deleted and Cs added, using
  `old_to_new` of `c1/pairs/m30_Cs188p0.json`.
- G (the positions reader) is admitted for this purpose only as a reader of the raw fr outputs, under the conditions
  of the force-only reader (D-C2-11).
- Its output is published unedited.

## 7. E: the one evaluation of S2b

**When E may run.** E refuses to run unless one of these holds:
- FR has failed (§1, any part);
- c3b has ended and c4b has ended, stopped early, been cut or was not run;
- there was a final STOP in fr, c3b or c4b.

**Run discipline.**
- E refuses a dirty tree. It prints HEAD and the sha256 of its tools, and it refuses to overwrite an existing output.
- It runs once, after the archives of the last campaign have passed verify.
- **Output.** E writes `results/objective2/s2/s2b/E_output.txt` itself, with its exit code on the last line. A rerun
  under the rules below writes `E_output_attempt2.txt`, and a third attempt is refused.
  - Each output is committed unedited before the adversarial check: privately while the c3b and c4b archives are
    private, and publicly with the S2b result note.
  - The D3BJ study uses the output's sha256.
- **Two phases.** E computes every block, every integrity check and every cross-check in memory, and writes its whole
  output in one pass. So every failure is a failure before output.

**Code.**
- **When committed.** New code outside `scripts/`, committed with self-tests and reviewed. Blocks 1-3 and 5 are
  committed before FR is launched; block 4 before C3b. The figure script `figures/fig_s2b_e_fk.py` is committed with
  E.
- **Raw outputs.** A2 outputs are read with `scripts/47 parse_relax(read="full")`, with these arguments and checks:
  - mapping = `c1/smoke.json["mapping"]` (S2b runs the same node pw.x, which the D1-D3 pre-checks assert);
  - k_cap = 200; ranks from the record; label;
  - assertions: ks = 0 … n_config − 1, and k_last = converged_at_k (or 200 at the cap);
  - F(final) = F at k_last.
- **The E guard.** E reads every C2, fr, c3b and c4b A2 record, validity record and gate file only through EGuarded,
  a subclass of the D-C2-12 `Guarded`.
  - **How it works.** It holds a closed allow-list of full leaf paths for each mode. It refuses parents, iteration,
    printing, comparison, `open()` and any path not on the list.
  - **Never on any list:** the module-level WITHHELD (unchanged), `end_rule.dF_200_180_meV`, `state_in`, `inputs_in`,
    `c1_in` and `inputs_opened`. `gate_K3.inputs.json` is not opened.
  - **Far mode** (every run):
    - from `c2/gates/K3.json` and `c2/gates_applied/gate_K3.gate.json`: `decision.K3`, `result.checks_failed`,
      `result.Eb_A2_meV.far`;
    - from `c2/gates_applied/gate_K3.json`: `decision`, `gate_file_sha256`;
    - from the records of relaxations 5-8: `n_config`, `converged_at_k`, `k_last`, `final_geometry.k`,
      `final_geometry.sha256`, `restarts`, `reruns_from_zero`, `status`, `end_rule.outcome`;
    - from the records of relaxations 1-4: `n_config`, `end_rule.outcome`.
  - **`result.value_meV`** is tested only with `is None`. A non-null value is never printed: E stops and treats it as a
    hinge item.
  - **FR mode** (every run): the same record leaves for every FR cell; from the FR gate files, `decision.*`, the reason
    lists, and the recorded δ_far(FA188), E_b^A1(FA188) and E_b^A2(FA188) under their exact field names, for the
    cross-check.
  - **Tier and C4b modes** (block 4): the same record leaves for every c3b and c4b cell, and the C4b gate's decision and
    df_δ.
  - **Hinge mode** (block 5 only): `result.Eb_A2_meV.hinge`, and the far-mode record leaves for relaxations 1-4.
  - **C1 side of the hinge deferral.** Outside block 5, `load_record(blind=False)` is refused for `s2_m30_VB136`,
    `s2_m30_Sr136p0_novac`/`_vac` and `s2_m30_Ca136p0_novac`/`_vac`, and no `c1/raw` output of a Pb136 cell is opened.
    Both are asserted at load and at exit.
- **Imports, read-only, at `8bff03e`.**
  - From `scripts/48`: leg_F, quartet_a1, host_values, pooled_delta, tier_a1, tier_cal, classify, heterogeneity,
    cal_heterogeneity, c2_noise, dopant_specific, required_hosts, path_work, _mace_eb, _mace_pilot, _determinism and
    _wp2c_values.
  - From `scripts/49`: separability, t_ppf, sign_required, boltzmann_meV and g1_pass.
  - No evaluate or assemble entry point of `scripts/48` is run, and E never runs in a root that holds c3.
- **New code** is limited to:
  - the table builder;
  - validity, with S2b cells under the invariant reading;
  - C5 with FR;
  - a_far(δ_far(FA188));
  - the composition of C1-C5 without Ca;
  - the ranking, with Bonferroni over the 10 pairs as P:783. q* is kept as planned (`C1_RESULT.md` §3.1);
  - the labels;
  - the block logic.
- **MACE records.** C1 and c3b records are read with `load_record(blind=False)` in blocks 3-5 only.
- **Self-tests** (P §17 item 2 carried over):
  - an independent recomputation of every statistic, to 10⁻⁶ meV;
  - the planted classes, including the −100 and −80 meV X-site cases;
  - the refusals: control not repelling, df_δ < 3, |δ̄_d| > 50 meV, the dopant-specific rule;
  - assertions that each block prints with its labels: the item-4 label, the MACE label, "not formed" and "no A2 cell";
  - planted synthetic archives for every row of §1 and §11. Each asserts which blocks print, that block 5 is not
    opened when its trigger fails, that the header stands in every block and in the figure caption, and that the item-4
    string sits beside every A1 E_b with no class field on an FR-fail route;
  - binding cases:
    - |δ_far(FA188)| = 50.000 meV passes FR-2 and 50.001 meV fails it;
    - a_far fires and does not fire on either side of its threshold, taken from FA188 and never from Pb76;
    - δ_Sr,m30 comes from the hinge quartet;
    - an invariant-only pass counts as valid and is flagged;
    - df_δ = 2 gives no validated class;
    - "C4b not run" gives the A1 tier only;
  - blocks 3 and 5 hold 160 C1 MACE labels between them (155 + 5) and are disjoint. A planted Pb136 record printed in
    block 3 fails the test, and a planted Pb136 E_mace_eV and Pb136 raw single point do not reach the output in a run
    without block 5;
  - a MACE canary: E_mace_eV on synthetic records is printed with its label, and every other reader still raises
    (S0:965);
  - the EGuarded allow-lists.
  No self-test opens an archive file of C2 or S2b.

**Integrity checks** (on failure E prints only check names, key paths and file names, never a value, and exits
non-zero):
- the sha256 of each opened file against the verified archive;
- sha256(`c2/gates/K3.json`) equals `gate_file_sha256` in `gate_K3.json`;
- both K3 files give decision.K3 = fail_replan, with identical `checks_failed`;
- the parsed configuration counts and k_last against the records;
- the last parsed configuration against the final geometry, within 10⁻⁶ Å;
- no output of relaxations 1-4 opened outside hinge mode;
- no calculator module loaded, both at load and at exit;
- the `scripts/47` READS counters. They are recorded before and after each `parse_relax` call. READS["ase"] may rise
  only during a read="full" call, by the number of parts of that relaxation holding a kept configuration. READS["F"]
  rises only for relaxations of the blocks being run;
- the commits. E records the C2 and S2b campaign commits and prints the diff of `scripts/46`-`50` between them. It
  refuses if `scripts/46`-`50` or its own files differ between the S2b campaign commit and HEAD without a dated
  amendment.

**Header, printed on every block, on the E figure caption and on the S2b result note:** "S2 K3: fail (fail_replan);
checks_failed: s2r_m30_VB76, check 5 (C2_RESULT.md). S2b FR: <pass | fail (FR-1, cell, reason) | fail (FR-2) |
stopped at cell (reason)>. Valid far references: k of 2." G2 prints the K3 part with "FR: not yet run".

**The item-4 label.** While FR has not passed, every A1 E_b that E prints carries "S2 K3 failed (far quartet
invalid); A1 not validated against A2 at the far site". Such a value is reported only and receives no class. This
covers:
- E_b^A1(Pb76) and its difference from −5.0 meV;
- E_b^A1(FA188);
- every DFT A1 E_b beside a MACE value, and every q = 0 E_b;
- E_b^A1(Pb136) at a deferred hinge read.

If FR passed, these values carry "far-site reference: FR, m30 FA188, valid".

**Precision.** F to 10⁻⁶ eV. E_b, δ and relaxation energies to 0.01 meV.

**Blocks** (each printed with fixed labels, whatever the values):

1. **Far block** (always). For relaxations 5-8:
   - **Per relaxation:**
     - F(0), F(final), the relaxation energy, and n_config, restarts and reruns, cross-checked against
       `C2_RESULT.md` §2;
     - the path-work and displacement attribution by shell (P:804-805);
     - the F(k) − F(final) curves.
   - **ΔF_tail** = F(k_last − 36) − F(final), at k = 128 (hostB76), 156 (VB76), 105 (Sr76o0_novac) and 99
     (Sr76o0_vac). For VB76 also F(158) − F(final) and F(172) − F(final). Labelled "path energy of the whole region
     over the window; not attributable to the failing objects; bounds no E_b error; reported only".
   - **The quartet:**
     - E_b^A1(Pb76) from k = 0, beside C1's −5.0 meV with the difference at full precision;
     - E_b^A2(Pb76);
     - δ_far(Pb76), labelled "far quartet invalid (check 5, VB76); reported only; not valid".
   - **Cross-checks:**
     - E_b^A2(Pb76) against `result.Eb_A2_meV.far`, to 10⁻⁶ meV;
     - δ equals the signed sum of the four relaxation energies, to 10⁻⁶ meV;
     - "plateau differences: none", from n_config ≤ 200 and `end_rule.outcome` in all eight records (read as leaves in
       far mode for relaxations 1-4 as well).
2. **FR block** (always). For every FR cell that ran:
   - the per-relaxation items of block 1;
   - E_b^A1(FA188), E_b^A2(FA188) and δ_far(FA188), when the quartet is complete;
   - a cross-check against gate FR's result, to 10⁻⁶ meV;
   - labels on the failing branches: "FR quartet invalid (check n, cell); reported only; not valid", or "FR-2 failed
     (|δ_far(FA188)| > 50 meV in one quartet; bias and site scatter not separable); reported only".
3. **MACE and deferred-C1 block** (always). It excludes the energies of Pb136 cells, DFT or MACE, and every quantity
   formed from them; those are in block 5.
   - **Every E_mace_eV**, at any depth, of the 155 C1 MACE records that are not Pb136 cells: 2 hosts, 29 V⁺_R, 80
     noise-pilot cells, 16 start-set cells and 28 pose-start cells. This includes the per-stage values of the two host
     relaxations.
   - **The zero-shot MACE E_b** of every C1 quartet, including the pose-pilot aggregates at m30 Cs128, Cs188, Cl138 and
     Cl175 ([48:788-799]). Each is printed beside its DFT A1 E_b, or "no A1 DFT value" where none exists.
   - **The q = 0 link rows** (P §10) not at Pb136. A row that C1's single points cannot form is printed "not formable
     from C1 single points (no A2 cell)": GA at FA128, and the q = +1 comparators at FA128 and I138. When C4b ran,
     block 4 prints these rows where the C4b k = 0 F completes them.
   - **The determinism check** (P §5).
   - **The DFT residual forces of every A1 cell,** Pb136 cells included (forces are not part c): per-atom norms, RMS and
     max.
   - **The invalid-cell table** for C1, C2 (VB76, [5]) and FR.
   - Every zero-shot MACE row is labelled "zero-shot MACE, not re-admitted".
4. **Tier block** (only if C3b ended with an A1 tier computable).
   - **The A1 tier** under P §14, with the labels of §1 and the ranking.
   - **P §15 items:**
     - per host: e_h(j), raw E_b, the far-site values, Y_h and Δ_h;
     - per dopant: Ē_d(j) and G_d;
     - the invalid-cell table over C3b, FR and C4b;
     - the required hosts;
     - the zero-shot MACE E_b of every production quartet.
   - **For C3b:** the DFT residual forces of the A1 cells (P §15), and the check-5 reading counts of §3.
   - **Far-bias sensitivity, reported only:** δ_far(FA188) beside every class at both tiers. I^A1_d, I_d and U_d are
     recomputed with |δ_far(FA188)| added, and each class that would change is flagged "sensitive to the far bias at
     FA188 (one quartet, Cs, A site; reported only)".
   - **Whenever C4b ran,** at any df_δ: the per-relaxation items of block 1 for every C4b relaxation, and the WP2c
     comparisons at FA128 (m30) and Pb124 (m05). A quartet that was cut or stopped early is printed "no S2 A2 cell (cut n
     / early stop)".
   - **If C4b ended with df_δ ≥ 3:** the calibrated tier, the shared-region sensitivity (P:792-796) and the
     plateau-excluded intervals.
   - **If C4b ended with df_δ < 3:** the C4b δ are reported only, without δ_Sr,m30.
   - An item that cannot be formed is printed with its reason: "not formed", "no S2 A2 cell", "C4b not run", or "cut n /
     early stop".
5. **Hinge block** (only if C4b ended with df_δ ≥ 3, counted from validity leaves alone with Sr's C2 hinge quartet
   counted valid; E prints that count before opening this block).
   - **Relaxations 1-4:** the per-relaxation items of block 1, including path work and ΔF_tail at k = 42, 46, 44 and 38.
   - **The quartet and gate values:**
     - E_b^A1(Pb136), E_b^A2(Pb136) and δ_Sr,m30;
     - F of the step-0 reference single points;
     - E_b^A2(Pb136) − E_b^A2(Pb76), labelled "not a K3 decision; K3 failed on validity".
   - **Pb136 comparisons and MACE:**
     - the q = 0 link rows at Pb136. For Ca, print "not formable: no F of Ca D(136)".
     - the WP2c comparison at Pb136.
     - the E_mace_eV of the five Pb136 records (V⁺_R; Sr and Ca D and D+V⁺);
     - the zero-shot MACE E_b of Sr at Pb136, beside E_b^A1(Pb136);
     - the zero-shot MACE E_b of Ca at Pb136, printed "no DFT A1 E_b (Ca failed G1)".
   - **The cross-check** against `result.Eb_A2_meV.hinge`.

**No other P §10 or §15 item is dropped.** The D3(BJ) row stays withdrawn. An item that cannot be formed is printed
with its reason.

**If the hinge block is not opened,** it stays unread. The deferred read is a single run of E's committed block 5 in
hinge mode, at a recorded commit. It writes `results/objective2/s2/s2b/E_hinge_output.txt` and goes through the same
integrity phase. It is exempt from "runs once". It happens at the first of:
- the evaluation of a later pre-registration that names it as data, in rules committed before 2027-06-30. That
  pre-registration replaces the backstop below with its own dated backstop, no later than its final stop;
- 2027-06-30.

**The figure** `figures/fig_s2b_e_fk.py`.
- F(k) − F(final) for every relaxation read, on a symlog y axis with a linear threshold of 0.1 meV.
- It marks the restart parts, the ΔF_tail windows, and, for VB76, k = 156, 158 and 172.
- Its source data is `figures/source_data/fig_s2b_e_fk.csv`.
- QA as for the C1 and C2 figures.

**Failure and rerun rules.**
- **A failure before output.** The tool is fixed in a dated commit, with a self-test that fails on the earlier code,
  and run again once.
- **A second failure before output** (the item-7 fallback).
  - The gate-recorded values are printed by leaf name through the guard, labelled "recorded by gate code; not
    cross-checked (E failed twice)". These are `result.Eb_A2_meV.far` and gate FR's recorded values, and `.hinge` only if
    block 5's trigger held.
  - Every other part-c value, and the tier, is reported as "not read: E failed".
  - A dated amendment, committed within 30 days and before any later pre-registration commits its rules, may change
    only E's code. A self-test must fail on the earlier code and pass on the fix. One more run follows.
- **A code error found after output** is handled as P:960-963. A rerun after an error that changes no rule is not a
  second evaluation. Its cause and diff are listed, and both outputs are archived.
- **A failed cross-check** is printed with "cross-check failed", and no value is suppressed. The one exception is
  `value_meV`.
- **G2 and the FR geometry read** follow the same rules.

**Later use.**
- **Read values.** No value read at E, by G2, by the FR geometry read or by part d may enter a statistic of a later
  pre-registration. A statistic is any quantity on which a gate, class, interval or admission depends.
  - The exception is the hinge block, if it is still unread when that pre-registration commits its rules.
- **Selections.** No admission route, gate threshold, validity bound, or set of sites or dopants of a later
  pre-registration may be selected by such a value. Each must be justified without it.
- **Planning.** Planning quantities may use these values: cost, cell size, and the planning s_δ in pass-probability
  statements. Each use must be listed in that pre-registration's information state.
- **Departures.** Any departure from this rule is a named, dated departure in that pre-registration.
- **Scope.** "A value read at E" means the part-c values and the outputs of G2, §6b and part d. S2b's own published
  tier is governed by the next pre-registration's information state. Values public before E (the C1 results, the C2
  record) are governed by 11a e5-e6; recomputing them at E does not bring them under this rule.

## 8. Budget, projection and cuts

**Remaining.**
- 520 − 91.92 = 428.1 node-h. The cap of P §16 binds S2 and S2b (11a e6).
- The tail of the boot that ended C2 is counted by the ledger at FR's boot. If FR never boots, a manual ledger row
  from the console stop time closes S2's total.

**Unit costs** [I, from C2]:
- an FR relaxation: 5.5 h (the C2 hinge minimum) to 14.4 h (the C2 far maximum);
- a C4b relaxation (near-site regions of 50-70 free atoms, like the hinge's 69-70): 5.5-9.0 h. This is the C2 hinge
  range of 5.50-6.11 h (`C2_RESULT.md` §2), with a margin to 9.0 h for the A regions;
- C3b = 544 × (6.39-6.74 min) + 536 × (1-2 min) + host relaxations of up to 3.3 h.

| stage | node-h |
|---|---|
| FR (6-29 if it stops at host_R or after the V⁺-host pair; a step-0 repeat reruns one cell) | 22-58 (repeat: up to 72) |
| C3b | 67-82 |
| C4b (24 relaxations) | 132-216 |
| allowance: A_FR = A_C4b = 201 × 4.65 min = 15.6 h each; R = 5% of the planned remainder | 42-49 |
| **total S2b** | 263-405; on FR failure 6-58 (with a repeat, up to 72), plus A_FR |

**Projection.**
- P (P:885) + U, where U = Σ over A2 campaigns not yet ended of max(0, A_c − spent_c) + R.
  - spent_c is the ledger node-h of campaign c's reruns from k = 0 and of its discarded parts.
  - R = 0.05 × (P − H_spent).
- It is recomputed at four points: the FR decision, the start of C3b, the start of C4b, and after the fourth C4b
  relaxation.
- c̄ and τ̄ are taken over the completed A2 relaxations of the campaign being projected. Before C4b has any, they are
  the C2 hinge values.

**Cut order** while P + U > 520 (never undone):
1. GA on m05. This leaves the largest df_δ at 3, and P(df_δ ≥ 3) then falls to p⁵.
2. C4b not run: the A1 tier only.

Without Ca, P's cuts 2-4 (P:894-896) would each leave df_δ ≤ 2 (`C1_RESULT.md` §5a). C5 could then not pass, so those
cuts are not used.

FR and C3b are protected. The hard cap (P:915-916) is unchanged.

## 9. Order of work

1. **Commit this file,** together with the dated notices of §1 and the erratum of §0.
2. **G2.** Commit the tool with its self-tests, read once, and publish.
3. **Before FR, all committed with self-tests and a code review:**
   - the operations note for `fr`;
   - the runner support for `fr`:
     - state and ledger continued;
     - new keys, with the C2 keys never overwritten;
     - the new HEAD accepted by a dated route;
     - the launch and relaunch scripts;
     - the early stop and step-0 for fr;
     - gate FR;
     - check 5 read invariantly;
   - the extended guard and its canary;
   - the generalised part-d tools of §6b;
   - each S2b operations note lists the choices made knowing G2 and the FR geometry read;
   - E's blocks 1-3 and 5;
   - a laptop self-test showing that the region and pair builders, `write_cell` and the QE input writer give
     byte-identical inputs for the four FR cells at `8bff03e` and at the S2b campaign commit, with a dated note listing
     the diff of `scripts/46`-`47` and `ehpc/`.
4. **FR boot or boots.**
   - The node restart routine (the PI logs in).
   - The node checkout is updated to the S2b commit by the dated route.
   - The D1-D3 pre-checks, extended to the new commit, and a dry run of the FR inputs.
   - Launch.
   - At FR's end: pull, the dry-run check, and the node stopped at once.
   - Then, on the laptop: archive (public), verify, the FR geometry read (§6b) and a short FR note (counts, decisions,
     labels). The note also publishes the sha256 of the private not_run c3 files and their verify line.
5. **If FR passes.**
   - Before C3b: the operations note and code for `c3b`, and E's block 4.
   - C3b, with the node stopped after it. Then archive (private), verify in a root without c3, and a short note.
   - The operations note and code for `c4b`.
   - C4b, with the projections, and the node stopped after it. Then archive (private), verify, and a short note.
6. **If FR fails:** go directly to step 7.
7. **E,** then an adversarial check, the S2b result note with its figures, and a roadmap update. Then the D3BJ study.
   - The result note reports E's blocks by reference, with their labels, together with the FR note and the outputs
     of G2 and §6b.
   - It states where the hinge values are held and what triggers their read.
   - It draws no inference beyond description and the readings of §§6, 6b and 11.
8. **The not_run c3 archive stays private.** `scripts/48`'s entry points are never run on S2 data.
9. **D-C2-8 retention** (the C1, C2 and C3 trees kept on the node) ends only when all of these hold:
   - E has run;
   - its archives have been re-verified;
   - the hinge block has been read, or a later pre-registration has taken custody of the C2 tree.
   Any deletion is recorded as a file listing.

## 10. Departures from S2_PLAN and earlier notes (item 5)

| id | departure | rule departed | kind |
|---|---|---|---|
| X1 | C3 and C4 as planned are not run; `c3b` and `c4b` replace them | P:956 | S2 campaigns |
| X2 | the far reference is the Cs quartet at m30 FA188 | P:584-585, 622, 628-629, 649-652, 771-772, 919-920 | far-reference quartets at m30 far sites disjoint from R(Pb76) beyond the vacancy sphere (§2) |
| X3 | K3 retired; gate FR | P:644-648 | the far reference |
| X4 | check 5 read invariantly (D5's reading) | P:370-376 | every check first evaluated in S2b |
| X5 | FR order and early stop; C3b and C4b only after FR passes; C4b early stop | P:627-632 | S2b A2 relaxations and campaigns |
| X6 | a final step-0 failure (including "no error found") ends FR as failed | P:639 | FR |
| X7 | E replaces the one evaluation; `scripts/48` entry points never run on S2 data; only the functions named in §7 are imported | P:959-963; 11a b.2 | the S2b evaluation |
| X8 | E reads E_mace_eV in blocks 3-5 | spec 12.2 item 3 [46:19, 355-356]; S0:965 (N-C12) | E |
| X9 | the D-C2-10 blinding ends at E for blocks 1-3; the hinge block is deferred | P:964-970; OPS2 D-C2-10 | E |
| X10 | G2 and the FR geometry read: further geometry reads, with G admitted for raw fr outputs | 11a part d, "Once" and "for this purpose only" (P:1350, 1356-1357) | G2, §6b |
| X11 | E admitted as a reader of raw C2 and S2b A2 outputs, A2 records and gate files, under its guard | OPS2 Reading rule (OPS2:64-70) | E |
| X12 | cut order, allowance and projection points | P:882-914 | projections |
| X13 | new campaign ids at a new campaign commit | [50:2356-2377]; OPS3 | S2b campaigns |
| X14 | the not_run c3 archive stays private | OPS3 D-C3-1 exception | c3 |
| X15 | the FR archive is public; the c3b and c4b archives are private until E | OPS2 D-C2-7; OPS3 D-C3-1 | S2b archives |
| X16 | the D3BJ sensitivity study runs on E's output | `D3BJ_AMENDMENT.md` "Pre-registered sensitivity study" | D3BJ |
| X17 | D-C2-8 (disk) ends as in §9 step 9, not "before C4 ends" | OPS2 D-C2-8; OPS3 extension | node trees |

No C2 cell is rerun. The settings, regions, check bounds, end rule and cap are unchanged.

## 11. What each outcome leads to

| outcome | reading | next step |
|---|---|---|
| FR stops at the V⁺-host check 5 | a second check-5 failure of a charge-contrast pair at a far site independent of R(Pb76); failing objects listed; cause (charged-cell response or optimiser drift) not established | the next pre-registration redefines the charge-contrast partner check or the far reference before its data, using E, G2 and §6b |
| FR stops on the cap, the plateau, unconverged_early, a missing cell, a hard-cap refusal, an equal-charge pair or checks 2-4 | another failure mode | the next pre-registration decides after its diagnostic |
| fail (step-0 final; gate not evaluated) | an integrity stop | find the writer or input error; the next pre-registration |
| FR-1 passes only under the invariant reading | FR passes; flagged in every label | as FR passes |
| FR-1 passes, FR-2 fails | \|δ_far(FA188)\| > 50 meV in one quartet (bias and site scatter not separable; P(fail \| μ = 0) ≤ 0.02) | far-referencing at A1 not admitted as designed |
| C3b final STOP, or no A1 tier computable | no A1 tier | as FR fails, with FR's pass reported; C4b not run |
| FR passes; C4b ends with df_δ < 3, a final STOP, or is not run by cut 2 | the A1 tier stands | C4b δ (if any) reported only; the hinge block stays blind |
| C4b ends with df_δ ≥ 3, but C1 or C5 fails | the A1 tier stands; no validated class | C4b δ and the hinge block reported only |
| everything passes | the calibrated tier | as S2_PLAN |

## 12. Review record

| round | what | findings | outcome |
|---|---|---|---|
| design panel | three proposals (information-first, rigour-first, physics-first); two judges (compliance; cost) | the compliance judge chose rigour-first, with fatal flaws named in information-first: a second site after a failure, and Pb76 not counted; the cost judge chose information-first and asked that Pb76 be counted beside FR and the site be fixed by rule | physics-first rejected by both (items 2 and 5, part f); see answers below |
| review of draft 1 (FR at I175) | four lenses, each finding checked by a skeptic | 26 major or critical, 24 survived | I175's overlap with Pb76 led to draft 2 |
| review of draft 2 (close-out) | three lenses, with skeptics | 22 major or critical, all survived, some downgraded | the A far pair's independence, the prior-mixing artefact, item 4's successor clause, the hinge deferral, and E's specification led to draft 3 |
| verification of draft 3 | checklists against rounds 1-2, plus a fresh adversarial pass, with skeptics | 18 major survived, plus about 54 minor | draft 4; each finding has a decision in R3a |
| verification of draft 4 | a checklist against verification 3, plus an internal-consistency pass, with skeptics | 4 major (the ASE counter, the closed allow-list, the attainable-df convention, the second-failure fallback), plus 46 minor | draft 5 |

**Answers to the judges' main objections.**
1. **The site is fixed by the rule of §2,** which uses only the region files and `checks_failed`. The site set is
   closed ("no other far site is tried"). Item 4 allows a stated successor.
2. **Pb76 is not counted inside FR-1.** A rule requiring both references valid fails with certainty and has no bite.
   A rule requiring at least 1 of 2 is FR-1 itself. Pb76 is carried in every label as "Valid far references: k of 2",
   and in the header of every E block.
3. **A reported-only production after an FR failure** is declined as the analyst's choice, for the reason given in §2.
4. **The FA188 successor itself.** The round-2 DA3 and DA4 verifiers advised against an FA188 successor. R3 adopted it
   as the analyst's judgement, for the reasons given in §2.

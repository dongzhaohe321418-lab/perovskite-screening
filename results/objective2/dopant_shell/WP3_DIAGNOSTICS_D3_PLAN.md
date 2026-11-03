# WP3 post hoc diagnostic D3 — plan (2026-11-03)

This plan was written and committed before any interpolated-point single point of D3 was computed. It
adds one diagnostic to `WP3_DIAGNOSTICS_PLAN.md` (d69fe75). The D1 and D2 results are in
`WP3_DIAGNOSTICS.md` (581d020).

**Design review.** Two lenses reviewed a first draft and returned 34 findings. Seven were rated "error". They
concerned:
- the single-point count;
- the geometric null of the work gauge;
- a resolution rule fixed by already-known values;
- a majority vote without margin;
- reading guidance;
- a stopping rule.

**What changed as a result.**
- The verdict of the draft ("mainly local" or not) is dropped, chiefly because of the geometric null and
  the margin problem. D3 is a pre-specified **description**.
- A check of the second draft found 2 of the 34 only partly addressed, plus 16 further points. All are
  applied here.

## 1. Status, scope and limits

- **Post hoc and reported only.** Nothing here changes a WP3 verdict, a threshold or the outcome
  (amendment m item 4). No model is validated or chosen.
- **What D3 is not.**
  - It does not answer D2's Q4, which stays "cannot be read" and is not answered retroactively.
  - It does not run the test that `WP3_RESULT.md` §8 reason 7 names (a line integral of the model − DFT
    force residual). Reason 7 therefore stays "origin not established".
  - It describes where the fine-tuned model books its change of one energy difference, relative to the
    zero-shot model. It says nothing about whether that change moves the model towards DFT, and nothing
    about the recipe beyond description.
- **The quantity.** Per band, the change on fine-tuning of S = E(i*) − E(0):
  ΔS = [E_FT(i*) − E_FT(0)] − [E_ZS(i*) − E_ZS(0)].
  - **i\*** is the DFT argmax image of D2 (images 2–4, raw F): image 3 in 35 bands and image 2 in 2
    (m21_GA, m21_Sr).
  - **Name.** ΔS is called the "segment change", as `segment_change_meV` in `scripts/44`.
  - **Relation to the WP3 E_a change.** In 6 bands a model's own argmax differs from i* (7 model–band
    differences): m05_undoped, m05_GA, m15_GA, m15_Sr, m21_GA and m21_Sr. There ΔS differs from the WP3
    change E_a(FT) − E_a(ZS). The exact link is reported per band:
    E_a change = ΔS + [E_FT(i*_FT) − E_FT(i*)] − [E_ZS(i*_ZS) − E_ZS(i*)].
  - **Correction to `WP3_DIAGNOSTICS.md` §4.** At 581d020 it said "7 bands". It is corrected in place, in
    the commit of this plan, to "6 bands (7 model–band differences)".
- **E_a and i\***.
  - Both keep their WP3/D2 definitions (images 2–4).
  - Here E_a is computed directly from the new image points, as the maximum over images 2–4 of E_i − E_0
    (as `scripts/44` `argmax`). `scripts/39` `Ea` is not called, because it needs image 6, for which D3
    computes no single point.
  - Energies at image 1 or at interpolated points never enter E_a or i*.
- **Scope.**
  - **Models.** The two MACE models only: the zero-shot `mace_mp` medium and `wp3/run2/wp3.model`, with
    D2's sha256 checks.
  - **Not attempted** (they would need new DFT): the model error against DFT (D2c) and the DFT closure
    (D2a).
  - **Not used.** Segments beyond i* are not attributed, except the beside extension of §3. Image 5 is not
    used. Image 6 is read for geometry only, to identify the hopping I and the hop midpoint, as in D2.
- **Compute.** Laptop single points only, MACE float64 on CPU, 4 threads: 2442 single points in all (§3).
- **Plan file.** This file is `results/objective2/dopant_shell/WP3_DIAGNOSTICS_D3_PLAN.md`.

## 2. What was seen before this plan, and how to read D3

**Seen in the repository** (`d2_path_attribution.json`, `diag_console.log` or `WP3_DIAGNOSTICS.md`):
- **D2a.** It resolved no band. The DFT path-work closure through images 0, 2 and 3 (0 and 2 in two bands)
  is −41.9 to −144.7 meV. The per-segment and per-band closures of all three levels were also seen.
- **The coarse per-band D2b and D2c values** (not a reading): group works, sums, segment and direct
  changes, and local shares.
  - The coarse D2b local share exceeds 0.5 in 33 of 37 bands. The four exceptions are m21_GA,
    m32_undoped, m32_GA and m32_Sr.
  - The median local share is 1.13.
  - The group means are hop_I −36.9, inorganic_near −32.9, inorganic_far +17.5, organic_near −6.7 and
    organic_far −1.8 meV.
  - The D2c all-band summary was also seen.
- **Argmax differences.** Those between each model and DFT.
- **Image 1.** Zero-shot single points at image 1 for four bands (m05_undoped, m12_undoped, m30_GA,
  m27_Sr), and the closures through image 1 at one interval per segment. These are coarse D3 path points.

**Seen in the design-review output** (geometry only, all 37 bands; these are not new D3 results).
- **Displacements.**
  - The largest per-atom displacement per segment of 0..4 is at most 0.97 Å.
  - The hopping I moves 0.16–0.97 Å per segment.
  - H moves at most 0.29 Å.
  - The chord 0 → 2 moves atoms up to 1.09–1.43 Å.
- **Image 1 close to image 0.** Image 1 lies only 0.21–0.40 Å from image 0 in m15_undoped, m20_undoped,
  m20_GA, m32_GA and m14_Sr.
- **Wrapping.** No atom wraps between images.
- **Displacement share.** Along 0..i*, hop_I plus the inorganic atoms within 6 Å carry 0.53–0.96 of
  Σ|Δr|² (median 0.84); the hopping I alone carries 0.47–0.88 (median 0.78). D3d's displacement values
  and the local displacement share D_g are therefore known before D3.
- **Stored band-file values.** They are consistent with D2: the zero-shot differences 0–2, 2–3 and 3–4
  agree within 2 × 10⁻⁶ meV.

**How to read D3.**
- **Not independent of D2b.** D3 shares the models, the image forces, the groups and the segment with D2b,
  so agreement with the coarse picture is weak evidence.
- **The coarse D2b values are path C at n = 1, not path P.** D2b attributed along the chord 0 → 2 → i*,
  so its values are the n = 1 values of path C (§3), while D3's primary path P runs through image 1.
- **Where the information lies:**
  - (i) group contributions in meV with error estimates, once the quadrature is resolved;
  - (ii) the comparison with how the zero-shot barrier work itself is distributed;
  - (iii) the comparison with a second, path-free gauge (site energies);
  - (iv) the size of the path dependence (P against C);
  - (v) how far the seen coarse D2b values were from their converged values on the same path.
- **What is expected anyway.** A large local ΔW relative to the far and organic groups is expected, because
  the local atoms carry most of the displacement. On its own it would not show that fine-tuning changed
  "local physics".

## 3. The paths

- **Bands.** The 37 bands of D2: 18 training, 3 m21 and 16 test.
  - **Not independent.** Up to three systems share a host framework, so summaries are given by band and
    by host.
  - **Training bands.** In the 18 training bands the fine-tuned model was fitted at images 0, 2, 3, 4 and
    6 (and at host MD and rattled frames). It was not fitted at image 1 or at any path point. The
    training-split summaries therefore describe the model partly away from its fitted geometries.
    Differences between splits are not a generalisation measure.
- **Images used.**
  - Images 0, 1, 2, 3 and 4: single points for both models in every band.
  - Image 6: geometry only.
  - Image 5: not used.
- **Band path P (primary).** P runs 0 → 1 → 2 → … → i*, piecewise linear in Cartesian positions.
  - Each segment k → k+1 has the minimum-image displacement Δr_k (`ase.geometry.find_mic`, band cell).
  - Each segment is divided into n = 8 equal steps of Δr_k/8.
  - The path points are r_k + (j/8)·Δr_k, j = 0…8, with the stored images as j = 0 and j = 8.
- **Chord path C (sensitivity).** C is the straight chord 0 → 2 (image 1 skipped, as in D2), followed by
  P's segments 2 → … → i*, all at n = 8. For the two i* = 2 bands, C is the chord 0 → 2 alone.
- **Path dependence.** ΔW_g(P, 0→i*) − ΔW_g(C, 0→i*) (§7).
- **The 2 → 3 extension for the two i* = 2 bands** (beside, no rule).
  - P and C are each extended 2 → 3 at n = 8, so that the change to image 3 (the zero-shot CI-NEB image) is
    also attributed.
  - It is reported separately for P and C, outside every criterion and summary.
  - Criteria 1–2, D3a, D3d and §7 use the paths to i* only.
- **Single points per model and band.**
  - Images 0–4: 5.
  - Interior points of the P segments 0→1, 1→2 and 2→3: 21. For i* = 2 bands, the 2→3 points are the
    extension.
  - Interior points of the chord 0→2: 7.

  That is 33 per model and band, 1221 per model and 2442 in all, and the script asserts the count. The
  n = 4 and n = 2 points are subsets of the n = 8 points.

## 4. Quantities

**D3a, quadrature.** Computed per model (zero-shot, fine-tuned) and per path (P, C, to i*).
- **The work.** W = −Σ ½(F_a + F_b)·(r_b − r_a) over successive points, per atom before summation, at
  n = 8, 4 and 2.
- **The closure.** The closure W − [E(end) − E(0)], per segment and in total. For a conservative model it
  is the quadrature error.
- **The error estimate.** For every work quantity X (ΔW_g, W_ZS,g, W_FT,g and the totals):
  - **e(X) = |X8 − X4|/3.** This is the asymptotic error estimate of the n = 8 trapezoid value X8. It is
    an estimate, not a bound.
  - **The Richardson value X_R = X8 + (X8 − X4)/3.** Its error is not estimated. When the convergence ratio
    is in [2, 8], it lies within [−(4/7)·e, +2·e].
  - **Error used in statements.** Statements use the conservative |X8 − X4|.
- **Convergence ratios** (reported for every X): closure4/closure8, and (X2 − X4)/(X4 − X8).

**D3b, the work gauge.**
- **Per group.** For each of the five D2 groups g (§5), the work of the force change along P:
  ΔW_g = −∫ ΔF_g · dr, with ΔF = F_FT − F_ZS. It is reported as X8, X_R and e.
- **The identity.**
  - Σ_g ΔW_g = W_FT − W_ZS on the same points.
  - The closure of the sum against ΔS is closure_FT − closure_ZS.
  - Both are asserted to 1e-9 meV. They add no information beyond D3a.
- **Comparators per band and group**, in one table:
  - ΔW_g;
  - the zero-shot work W_ZS,g and the fine-tuned work W_FT,g along P (X_R and e);
  - the displacement share D_g = Σ_{i∈g} Σ_steps |δr_i|² / Σ_all;
  - the ratio ΔW_g/W_ZS,g, wherever |W_ZS,g| ≥ 5 meV.

  No other comparison is drawn.
- **Cancellation.** Let L = ΔW(hop_I) + ΔW(inorganic_near) and N = the sum of the other three groups. The
  ratio κ = (|L| + |N|)/|L + N| is reported per band. It is ill-conditioned where |ΔS| is small.

**D3c, the site-energy gauge (path-free).**
- **Per-atom energies.** MACE gives per-atom energies ε_i: the calculator property `energies`, which keeps
  the E0s. The script asserts this property is used, not `node_energy`.
- **Per group.** Δε_g = Σ_{i∈g} {[ε_i^FT(i*) − ε_i^FT(0)] − [ε_i^ZS(i*) − ε_i^ZS(0)]}. The E0s cancel in
  each difference.
- **Asserted, within 1e-6 eV.** Σ_i ε_i = E at every point, and Σ_g Δε_g = ΔS.
- **What it is.** This is the model's own energy partition. It is a different gauge from the work and is
  not unique physically. Both gauges come from the same two models, so they are not independent checks
  of each other.

**D3d, path regularity** (reported, no rule).
- **Energy excess.** Per model and segment of P, with λ ∈ [0, 1] along the segment:
  - **Hermite interpolant.** H(λ) is the cubic Hermite interpolant with E at both images and
    dE/dλ(0) = −F_k·Δr_k, dE/dλ(1) = −F_{k+1}·Δr_k (eV per unit λ).
  - **Excess.** The excess is max_j [E(λ_j) − H(λ_j)] over the interior points. Beside it is the largest
    E(λ_j) above the higher of the two bracketing images.
- **Geometry.** Along 0..i* of P and C, model-independent:
  - the largest per-atom displacement per segment;
  - at every interior point, the shortest intramolecular bond (by the image-0 molecule partition) and the
    shortest distance of any pair, against the shortest at the images.
- **The 6 Å crossings.** The number of atoms whose distance to the hop midpoint crosses 6 Å at any path
  point of P between image 0 and i*.

## 5. Groups

- **The five groups of D2.** They are defined at image 0, by minimum-image distance to the hop midpoint
  r_I(0) + ½ mic(r_I(6) − r_I(0)):
  - **hop_I**, the I with the largest 0 → 6 displacement;
  - **inorganic_near**, the other inorganic atoms with d < 6 Å;
  - **inorganic_far**, the inorganic atoms with d ≥ 6 Å;
  - **organic_near** and **organic_far**, whole molecules by their C (`scripts/38` `molecule()`).
- **Membership.** It stays as at image 0 along the whole path.
- **Molecule check.** The script asserts that the molecule partition is the same at every image 0..i* and
  at every interior point of P and C.

## 6. Resolution

**Criteria.** A band is **resolved** if both of the following hold on P to i*. Every failed criterion is
recorded per band.
1. **For both models, at n = 8:**
   - the total closure is at most 2 meV in magnitude;
   - closure4/closure8 lies in [2, 8], unless |closure8| < 0.5 meV.
2. **For every group:**
   - |ΔW_g,8 − ΔW_g,4| ≤ 3 meV, that is e(ΔW_g) ≤ 1 meV;
   - (ΔW_g,2 − ΔW_g,4)/(ΔW_g,4 − ΔW_g,8) lies in [2, 8], unless |ΔW_g,4 − ΔW_g,8| < 0.3 meV.

**Path C.** It is assessed by the same two criteria. A band enters the path-dependence summary (§7 item 4)
only if both P and C meet them. The number of resolved bands whose C fails is reported.

**Unresolved bands.**
- They keep their per-band values in the JSON, with status and failed criteria.
- No summary over unresolved bands is computed.

**Exclusion report** (a check on selection). For the excluded and the resolved bands, by host and split, the
report gives:
- the criteria failed;
- ΔS;
- the coarse D2b `groups_meV` (seen; not a reading).

**What the statements cover.**
- They are about the resolved bands only.
- **No cut on |ΔS|.** Shares are not used for any statement (§7), so a small ΔS needs no exclusion.
- **No resolved band.** If no band is resolved, only the per-band values and the exclusion report are
  given.

## 7. What is reported (pre-specified; no verdict)

**Summaries over the resolved bands.** They are given overall, by split (training, m21, test) and by host.
"By host" means one row per host plus the mean of the host means.
1. **ΔW_g.** Per group: the mean, median and range of ΔW_g (Richardson, meV), and the mean of |ΔW_g,8 − ΔW_g,4|.
2. **Δε_g.** The same for Δε_g.
3. **Comparators.** Per group:
   - the mean of W_ZS,g and W_FT,g (Richardson, with the mean |X8 − X4|);
   - the number of resolved bands in which e(W_ZS,g) or e(W_FT,g) exceeds 1 meV;
   - the median displacement share D_g;
   - the median and range of ΔW_g/W_ZS,g where |W_ZS,g| ≥ 5 meV.
4. **Path dependence.** Per group, over bands where both P and C are resolved, the mean and the largest
   |ΔW_g(P) − ΔW_g(C)|. Beside it, the mean of e(P) + e(C).
5. **The seen coarse values against their converged values.** Per group:
   - ΔW_g(C, Richardson) − D2b `groups_meV` (the quadrature error of the seen values on the same path);
   - ΔW_g(P, Richardson) − D2b `groups_meV`.

   Each is summarised by the median and the largest absolute value.
6. **Cancellation.** The median κ, and the number of bands with κ > 2.
7. **D3a.** For P and C: the median and largest |closure8|, and the median closure4/closure8.

**What the write-up may state** about where the change is booked. It is limited to these summaries. For
each group:
- the mean ΔW_g and Δε_g, with their spread;
- **the sign comparison of the two gauges.**
  - It is stated as agreement or disagreement only when both |means| exceed a margin. The margin is
    max(2 meV, 2 × the standard error over bands), and for the work gauge the mean |ΔW_g,8 − ΔW_g,4| is
    added.
  - Otherwise the write-up says "sign not resolved".
  - Beside it, the per-band count of groups whose signs agree is given.
- how ΔW_g compares with W_ZS,g, in meV and through the ratio of item 3.

**No verdict.** No "mainly local", "mainly far" or other binary verdict is drawn. Shares of a signed sum
are not used.

**Few resolved bands.** If fewer than 10 bands resolve, the summaries are still given, labelled "few
resolved bands", and nothing is densified further under this plan.

## 8. Checks (fail-closed unless marked)

1. **Models and packages.** The model-file sha256 values equal D2's. The package versions (mace, torch,
   ase, numpy) equal those D2 records.
2. **This plan.**
   - `results/objective2/dopant_shell/WP3_DIAGNOSTICS_D3_PLAN.md` is committed, and the script records the
     commit hash.
   - The script refuses to run if the file differs from that commit.
3. **Band files.**
   - The sha256 of all 37 band files is recorded.
   - Each file has 7 frames, with the same cell and the same species in every image.
   - For every step between successive images 0..4, and for the chord 0 → 2:
     - the minimum-image displacement equals the raw displacement;
     - max |Δr| < 2 Å;
     - r_start + Δr ≡ r_end within 1e-8 Å.
   - The 0 → 6 displacement (3.6–4.2 Å for the hopping I) serves only for the hop midpoint and is not
     subject to the 2 Å bound.
4. **Image geometry.** Images 0, 2, 3, 4 and 6 equal the D2 dataset frames: positions and cell within
   1e-6 Å, numbers identical (the `scripts/44` cross-check).
5. **Stored values, zero-shot model, images 0–4.**
   - The total energy equals the band file's stored energy within 1e-6 eV (the `scripts/39` tolerance).
   - Every per-atom energy equals the stored per-atom `energies` within 1e-6 eV.
   - The largest force difference against the stored forces is reported, not gated.
6. **D2 reproduction.**
   - Per model, the image energy differences 0→2, 2→3 and 3→4 and the coarse W of D2a (`segments_beside`
     dE_meV and W_meV) are reproduced within 1e-3 meV.
   - The coarse D2b `groups_meV` and the hop_I index are reproduced.
   - i* is recomputed from the dataset raw F (`REF_energy_raw`) and must equal D2's.
7. **Identities.** The work identity (1e-9 meV) and the site-energy sums (1e-6 eV).
8. **Molecules.** The molecule partition is unchanged along the paths (§5).
9. **Single points.** The count equals 2442.
10. **Reported, not gated.** The eight scratch image-1 closures of `WP3_DIAGNOSTICS.md` §4 are recomputed
    from the new image-1 points: zero-shot, one interval per segment, 0 → 2 and full path, four bands.

## 9. Runs, stopping and reporting

**Stopping rule.**
- n, the bounds, the criteria and the reported summaries are final. A denser path or a changed bound would
  be a new post hoc plan.
- Development runs use no real band; otherwise they are logged as scratch runs with their values kept.

**Reruns.**
- A rerun is allowed only to fix a code defect.
- Every full run is logged with its script sha256 and its value differences from the previous run.
- The recorded run is the last run after review.

**Code and outputs.**
- **Code.** `scripts/45_wp3_d3_dense_path.py`, reusing the group, displacement, molecule and model-loading
  code of `scripts/44`.
- **Outputs.** `wp3/diagnostics/d3_dense_path.json` and `wp3/diagnostics/d3_console.log`.
- **JSON fields.** They mirror `d2_path_attribution.json`:
  - **head:** script sha256, plan commit, git state, versions, model files, input files and band-file
    sha256 values;
  - `departures_from_plan`, `interpretations_of_plan` and `additions_to_plan`;
  - **per band:** the images, i*, the D3a–D3d values, the E_a link, status and failed criteria;
  - **summaries:** the §7 summaries, over resolved bands only.

**Write-up.** A section is added to `WP3_DIAGNOSTICS.md` with the §7 summaries, every departure and the
exclusion report.

**Figure.** One nature-figure figure:
- (a) D3a convergence: |closure8| against |closure4| per model, band and path, with the 1/4 line;
- (b) per-group ΔW_g of the resolved bands, as a strip plot with error estimates, beside W_ZS,g;
- (c) per-group ΔW_g against Δε_g (the two gauges);
- (d) path dependence: ΔW_g(P) against ΔW_g(C).

**Pointers.** The pointers in `WP3_RESULT.md` §8 reason 7 and in the roadmap read: "Post hoc D3
(`WP3_DIAGNOSTICS.md`): a description of where the fine-tuned model books its change of E(i*) − E(0)
along a densified band path, in two gauges; no verdict; reason 7's named test (model − DFT residual)
not run."

**Checking.** An adversarial check before commit.

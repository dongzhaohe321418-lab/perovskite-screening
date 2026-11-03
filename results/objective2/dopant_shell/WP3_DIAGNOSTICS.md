# WP3 post hoc diagnostics D1, D2 and D3 — result (2026-11-03)

**Status.** These diagnostics are post hoc and reported only. They follow `WP3_DIAGNOSTICS_PLAN.md`, which
was committed at d69fe75 before any D1 or D2 value was computed.
- **D3** follows `WP3_DIAGNOSTICS_D3_PLAN.md`, committed at ddb352b before any of its interpolated-point
  single points was computed. It is a pre-specified description with no verdict (§10).
- Nothing here changes a WP3 verdict, a threshold or the outcome. The WP3 outcome stays **No
  improvement** (`WP3_RESULT.md`; amendment m item 4).
- No model is validated, selected, saved or used further.

## 1. Summary

- **Q1 (D1): no.** None of the 20 kept checkpoints of run2 has all five m21 far-referenced E_b errors below
  25 meV with the Sr hinge and flank signs right.
  - **First-shell check.** None meets that condition on the two first-shell Sr sites alone either.
  - **Reading.** The plan's reading therefore applies: **the collapse of the first-shell Sr E_b is a
    property of the training, not of the selection.**
  - **Caveat.** The plan's five-site rule cannot discriminate here: the m21 Sr_mid site fails at every
    checkpoint and at the zero-shot start. The reading rests on the first-shell-only check.
  - **Size of the difference.** The selection still mattered in size. The loss-selected epoch 82 has
    twice the m21 E_b RMS of the best kept checkpoint (63.8 against 31.3 meV, epoch 7), although no kept
    checkpoint comes within 25 meV at both first-shell sites.
- **Q2 (D1), as planned.** The first-shell Sr errors first exceed 25 meV in magnitude at the start, not
  late in training:
  - at Initial for the two flank sites (+25.9 and +36.1 meV, before any training);
  - at kept epoch 0 for the two hinge sites (+165.9 and +150.9 meV), a positive overshoot while the force
    RMSE was above its Initial value.
- **Q2, the collapse (an addition to the plan).** The direction in which the model ends is an error below
  −25 meV.
  - **Onsets.** Its onsets are at epoch 4 (m21 flank, exact), in (4, 6] (m21 hinge) and in (8, 11] (both
    m05 sites).
  - **Against the force-RMSE fall.** They come after 56–78% of the Initial → epoch-82 fall of the m21 force
    RMSE, and after its steepest part (epochs 1–3).
  - **Against the energy RMSE.** The whole-cell energy RMSE falls over the same epochs, so the collapse
    cannot be assigned to the force term alone.
  - **No lasting recovery.** The only return is the m21 hinge at kept epoch 7 (−19.4 meV). From kept
    epoch 11 on, no first-shell Sr error at m21 or m05 is within 25 meV.
- **Q3 (D1).** Over the 20 kept checkpoints, the logged m21 loss and the m21 E_b RMS do not rank the
  checkpoints alike: Spearman's ρ = −0.12 (descriptive, no test).
  - **Course.** The relation is not monotonic. The E_b RMS is highest at kept epochs 0 and 2, lowest at
    3–8 (31.3–38.2 meV) and higher again from 11 on (47.4–77.5 meV).
  - **Against zero-shot.** All 20 checkpoints are above the zero-shot model's 29.1 meV.
- **Q4 (D2): cannot be read.**
  - **No band resolved.** The DFT path-work closure exceeds the 20 meV rule in all 37 bands (−41.9 to
    −144.7 meV).
  - **Where the error sits.** It is in the 0 → 2 segment. Image 1, which has no frame, lies on every
    0 → i* path. The two conservative models show the same error, so it is a discretisation error of the
    path sampling.
  - **The literal rule.** The plan's literal rule would give "mixed", vacuously (§5).
- **D3 (§10): a description, no verdict.**
  - **Quadrature.** With 8 intervals per segment, all 37 bands are resolved on the band path through
    image 1 (P). Both models close to 0.745 meV or less on P, and to 2.094 meV or less on D2a's path
    through images 0, 2 and 3 (C); closure4/closure8 is 3.97–4.03 on P and 3.86–4.18 on C in every band.
    For the two models the coarse D2a closures were therefore quadrature error (the segment 3 → 4, used by
    fine-tuned m05_undoped and m05_GA, was not densified). DFT has no values at image 1 or between images,
    so Q4 is unchanged.
  - **The change.** Fine-tuning changes E(i\*) − E(0) by ΔS = −46.89 ± 4.74 meV (mean ± SE over bands;
    negative in all 37). In the work gauge the group means are −23.25 ± 4.34 (hop_I), −31.49 ± 2.97
    (inorganic < 6 Å), +15.30 ± 1.55 (inorganic ≥ 6 Å), −5.93 ± 2.62 (organic < 6 Å) and −1.52 ± 2.57 meV
    (organic ≥ 6 Å).
  - **The second gauge.** The MACE site energies give +27.91 ± 4.17, −136.24 ± 5.28, +82.09 ± 4.76,
    −22.61 ± 7.80 and +1.96 ± 6.09 meV. By the plan's margin rule the signs disagree for hop_I, agree for
    the two inorganic groups and for organic < 6 Å (just above its margin), and are not resolved for
    organic ≥ 6 Å.
  - **The seen coarse values.** On their own path (C), the coarse D2b hop_I values lay a median 18.4 meV
    below their converged values (largest |difference| 49.3 meV, in a band whose C is not resolved;
    42.9 meV over the 31 bands with C resolved); for the other four groups the median difference is
    1.0 meV or less (largest 5.8 meV).
  - **Caveats.** Both gauges come from the same two models, and D3 shares its inputs with D2b. A large work
    change for hop_I and inorganic < 6 Å taken together is expected anyway: together they carry a median
    0.84 of Σ|Δr|², known before D3. Bands share hosts, and the standard errors treat them as independent.
- **For WP3_RESULT.md §8.**
  - **Reason 6** (a checkpoint chosen on a force-dominated m21 loss): no other choice among the kept
    checkpoints would have met the first-shell condition. Unkept epochs were not evaluated, and any
    reselection on m21 would itself be unvalidated.
  - **Reason 7** (the systematic barrier lowering): its origin remains unattributed. D3 describes where
    the fine-tuned model books its change of E(i\*) − E(0), without a verdict. It does not rerun reason 7's
    named test (a line integral of the model − DFT force residual), which D2 ran (D2c) and which cannot be
    read (§4).

## 2. What was run

- **Code.** `scripts/44_wp3_diagnostics.py` (sha256
  f13f0308e677783ddca79c2fc0f564535e327cf76b0397780884f29088c12b4a), run as `all` on the laptop. This is
  the recorded run (see the §5 run record).
  - MACE in float64 on CPU, 4 threads.
  - No MD, relaxation, training or QE.
- **Outputs.**
  - `wp3/diagnostics/d1_checkpoints.json` and `wp3/diagnostics/d2_path_attribution.json`.
  - The console log `wp3/diagnostics/diag_console.log`, which holds this one run.
- **Single points.** 1658 in all: zero-shot 217 and `wp3.model` 201 (counted at the calculators), and
  checkpoints 1240 (20 × 62 frames, by construction).
- **Inputs.**
  - **The ten numerical input files**, each listed with its sha256 in the JSON heads (`input_files`):
    - the dataset: `wp3/dataset/{train,valid,test}.xyz`, `E0s.json` and `dataset_meta.json`;
    - the run2 training log;
    - `wp3.model` (sha256 3f7bf6f5…65d2ca);
    - `wp3_eval.json`;
    - the WP2c selection and structures.
  - **The model files** (`model_files`): `wp3.model` and the zero-shot foundation file (sha256 01bfe221…).
  - **The 20 kept checkpoints**: off-repository, `<CKPT_DIR>`, each with its sha256 in
    `d1_checkpoints.json`.
  - **Unhashed inputs.** The archived QE outputs and the band geometries (`../bands`, off-repository) are
    not hashed. They are tied to the hashed dataset by the fail-closed cross-check.
  - **Git state.** The JSON git block records head d69fe75. Of the five scripts used and the ten hashed
    inputs, only `scripts/44` was uncommitted.
- **Checkpoint loading.**
  - **What a checkpoint holds.** Each checkpoint is a mace-torch 0.3.16 `{model, optimizer,
    lr_scheduler}` dict saved inside `ema.average_parameters()`. Its `model` therefore holds the EMA
    weights, the same weights the logged per-epoch eval used.
  - **How it is loaded.** Each state_dict is loaded with `strict=True` into a copy of the `wp3.model`
    module whose floating tensors were first set to NaN. The script then asserts that the calculator's
    module holds every checkpoint tensor bitwise.
  - **Epoch identity.** `lr_scheduler.last_epoch` equals the epoch of the file name for all 20.

**Checks.** In each part (D1, then D2), every gated check passed before any value of that part was printed
(fail-closed). The plan's two D1 checks are listed first; the last row is reported only.

| Check | Result |
|---|---|
| D1 check 1 (plan): epoch 82 against `wp3.model` on the 31 m21 frames, tolerance 1e-6 eV and eV/Å | max \|ΔE\| = 0, max \|ΔF\| = 0; state_dict bitwise equal |
| D1 check 2 (plan): logged m21 RMSE_E/atom and RMSE_F of every checkpoint, tolerance 0.5% | max relative difference 1.7 × 10⁻¹² (the log is not rounded, contrary to the plan's note) |
| Checkpoint set | the 20 files are exactly the plan's epochs, and exactly the epochs at which the logged m21 loss reached a new minimum (running minimum from epoch 0) |
| Dataset against the archived QE outputs and geometries | 62 (D1) and 155 further (D2) frames; F, E_F and E′ exact; forces within 5.0 × 10⁻⁹ eV/Å (extxyz rounding); positions and cell bitwise equal |
| Reproduction of `wp3_eval.json` item 5 (zero-shot and epoch 82; m21 and m05) | 126 numbers per host, max difference 0.0 meV; 96 exact leaves (classes, signs, booleans) |
| Reproduction of the 37 band E_a values of `wp3_eval.json` (D2) | 222 numbers, max difference 0.0 meV |
| Zero-shot against the logged Initial record (reported, not gated) | RMSE_F relative difference 3.7 × 10⁻¹⁵; RMSE_E/atom 3.3 × 10⁻¹⁰ after replacing the foundation E0s by `E0s.json` |

## 3. D1 — checkpoint trajectory (reason 6)

**How to read the table.**
- **Errors.** Far-referenced E_b errors are model − DFT, on raw F energies (F is the DFT free energy), in
  meV.
- **Logged values.** Loss, RMSE_E per atom and RMSE_F (the force RMSE) are the logged m21 eval values.
- **Initial** is the zero-shot model.
- **E_b RMS** is over the five non-far sites of each host.
- **Not evaluated.** The epochs that are not listed were not evaluated.

| Model | m21 loss | RMSE_E/atom (meV) | RMSE_F (meV/Å) | m21 Sr hinge | m21 Sr flank | m21 Sr mid | m21 E_b RMS | m05 Sr hinge | m05 Sr flank | m05 E_b RMS |
|---|---|---|---|---|---|---|---|---|---|---|
| Initial | 0.3321 | 0.333 | 79.8 | +23.8 | +25.9 | −43.0 | 29.1 | +21.7 | +36.1 | 23.3 |
| 0 | 9.6662 | 15.834 | 108.8 | +165.9 | +131.0 | −65.7 | 100.3 | +150.9 | +161.6 | 100.5 |
| 2 | 5.2671 | 11.894 | 69.3 | +182.7 | +157.1 | −58.1 | 111.0 | +175.6 | +193.9 | 120.0 |
| 3 | 0.6786 | 3.952 | 49.6 | +46.4 | +15.6 | −60.2 | 36.0 | +59.0 | +54.6 | 45.6 |
| 4 | 0.6383 | 3.963 | 41.5 | −15.2 | −40.4 | −56.5 | 32.0 | +11.0 | −6.1 | 25.3 |
| 6 | 0.5437 | 3.530 | 43.9 | −32.4 | −55.5 | −53.4 | 38.2 | +5.4 | −7.3 | 21.6 |
| 7 | 0.3495 | 2.850 | 34.8 | −19.4 | −38.5 | −50.0 | 31.3 | +18.4 | +6.0 | 21.5 |
| 8 | 0.1061 | 1.256 | 30.6 | −31.2 | −42.9 | −53.1 | 35.6 | +7.1 | −2.7 | 17.2 |
| 11 | 0.0808 | 1.000 | 29.4 | −68.8 | −75.7 | −50.0 | 52.9 | −27.7 | −37.4 | 24.5 |
| 15 | 0.0729 | 1.035 | 25.9 | −93.7 | −94.7 | −48.1 | 66.2 | −62.6 | −73.1 | 44.5 |
| 26 | 0.0584 | 0.969 | 22.1 | −100.1 | −94.6 | −44.1 | 67.5 | −68.5 | −80.7 | 48.1 |
| 27 | 0.0549 | 0.903 | 22.4 | −98.1 | −93.2 | −46.3 | 67.0 | −67.3 | −80.8 | 47.7 |
| 31 | 0.0409 | 0.742 | 20.4 | −115.5 | −108.4 | −49.8 | 76.6 | −84.9 | −99.4 | 58.8 |
| 33 | 0.0350 | 0.594 | 21.0 | −101.2 | −92.7 | −46.5 | 66.2 | −75.8 | −86.5 | 52.1 |
| 35 | 0.0275 | 0.528 | 18.5 | −96.2 | −88.8 | −47.4 | 62.9 | −69.6 | −80.5 | 48.6 |
| 56 | 0.0245 | 0.510 | 17.2 | −99.0 | −90.8 | −38.1 | 63.9 | −79.6 | −80.0 | 50.9 |
| 59 | 0.0198 | 0.408 | 16.4 | −121.5 | −112.4 | −41.6 | 77.5 | −93.9 | −104.5 | 63.5 |
| 77 | 0.0194 | 0.373 | 16.7 | −65.5 | −60.4 | −41.6 | 47.4 | −42.8 | −37.9 | 26.8 |
| 80 | 0.0191 | 0.388 | 16.4 | −97.9 | −91.2 | −46.1 | 66.4 | −69.1 | −71.2 | 45.1 |
| 81 | 0.0154 | 0.276 | 15.7 | −95.1 | −89.3 | −44.7 | 65.6 | −66.2 | −68.5 | 43.3 |
| 82 | 0.0148 | 0.252 | 15.6 | −93.0 | −87.8 | −42.0 | 63.8 | −64.4 | −64.5 | 41.6 |

The DFT far-referenced E_b (raw F) are:
- m21: Sr hinge +136.7, Sr flank +131.7, Sr mid +63.3 meV;
- m05: Sr hinge +105.7, Sr flank +116.1 meV.

**Other data.**
- **Errors at every site.** The absolute E_a, paired ΔE_a and all five E_b errors of every model, on both
  bases, are in `d1_checkpoints.json` (`models.<model>.quantities`).
- **Kept checkpoints.** The kept checkpoints are the epochs at which the m21 loss reached a new minimum,
  counted from epoch 0, not from Initial. The zero-shot loss (0.332) is lower than that of kept epochs 0–7.

**Q1. Is there a kept checkpoint whose m21 E_b errors are all below 25 meV in magnitude, with the Sr hinge
and flank signs right? No.**
- **Rule.** No checkpoint meets the rule.
- **Signs.** The sign condition never binds: the Sr hinge and flank signs agree with DFT at every
  checkpoint, and only the magnitudes fail.
- **Best checkpoint.** The smallest maximum |error| over the five m21 sites is at epoch 7: 50.0 meV. It
  fails at Sr_flank (−38.5) and Sr_mid (−50.0).
- **Selected checkpoint.** The loss-selected epoch 82 has max |error| 93.0 meV and fails at all five
  sites.
- **Sites failing per checkpoint.** Between 2 and 5 of the five sites have |error| ≥ 25 meV at each
  checkpoint.
- **The zero-shot model** also fails, at 3 sites (max 43.0 meV). Among them is the first-shell flank,
  marginally (+25.9 meV).
- **Caveat.** m21 Sr_mid, which is not a first-shell site, fails at every kept checkpoint (−38.1 to
  −65.7 meV) and at Initial (−43.0 meV). So no checkpoint could meet the plan's rule, whatever happened at
  the first-shell sites.
- **First-shell check.** The same condition on the two first-shell Sr sites alone is met by no
  checkpoint. This is an addition to the plan, and the reading rests on it.
- **Reading (plan).** The collapse of the first-shell Sr E_b is a property of the training, not of the
  selection.

**Q2. At which epoch do the first-shell Sr E_b errors first exceed 25 meV in magnitude, and how does that
compare with the fall of the m21 force RMSE?**
- **Brackets.** The epochs between kept checkpoints were not evaluated, so each onset is located only to
  its bracket (previous kept model, onset].
- **Fall fraction.** This is the share of the Initial → epoch-82 fall of the logged m21 RMSE_F
  (79.8 → 15.6 meV/Å) reached at the onset, given as a range over the logged epochs of the bracket.
  - It is negative at epoch 0 (−0.45): the force RMSE was then above its Initial value.
  - It is −0.67 at epoch 1, the peak (122.5 meV/Å).
- **Column 3** is the plan's quantity. Columns 4 and 5 are additions (§5).

| Host, site | Initial | First \|error\| > 25 meV (plan) | First error < −25 meV (fall fraction) | \|error\| > 25 meV from then on |
|---|---|---|---|---|
| m21 Sr hinge | +23.8 | epoch 0 (+165.9; fall fraction −0.45) | (4, 6] (0.56–0.63) | from epoch 8 (0.77) |
| m21 Sr flank | +25.9 | already at Initial | epoch 4, exact (0.60) | from epoch 4 |
| m05 Sr hinge | +21.7 | epoch 0 (+150.9; −0.45) | (8, 11] (0.69–0.78) | from (8, 11] |
| m05 Sr flank | +36.1 | already at Initial | (8, 11] (0.69–0.78) | from (8, 11] |

- **The plan's reading.**
  - The two flank sites already exceed 25 meV at Initial, before any training.
  - The two hinge sites first exceed it at kept epoch 0, as a positive overshoot. At that point both RMSE_F
    (108.8 meV/Å; 122.5 at epoch 1) and RMSE_E per atom (15.8 meV, against 0.33 at Initial) were far above
    their Initial values.
  - The overshoot of the first-shell Sr errors lasts to kept epoch 3, where three of the four are still
    above +25 meV. It is largest at kept epoch 2 (up to +193.9 meV, m05 flank). Epoch 1 was not
    evaluated.
  - So, as the plan asked it, the onset comes before the fall of the force RMSE, not during it.
- **The collapse** (an addition to the plan) is the direction in which the model ends, below −25 meV. Its
  onsets lie in (3, 11].
  - **The force RMSE.** At the onsets, 56–78% of the Initial → epoch-82 fall of RMSE_F is complete. Its
    midpoint (47.7 meV/Å) is first reached at epoch 4. The steepest part of the fall, from the epoch-1 peak
    of 122.5 meV/Å to 49.6 meV/Å at epoch 3, precedes every onset.
  - **The energy RMSE.** The whole-cell energy RMSE falls over the same bracket: RMSE_E per atom goes from
    3.95 meV at epoch 3 to 1.00 meV at epoch 11.
  - **Consequence.** The collapse cannot be assigned to the force term alone from these data.
- **No lasting recovery.**
  - The m21 hinge returns once, to −19.4 meV at kept epoch 7. It stays beyond 25 meV from kept epoch 8 on.
  - From kept epoch 11 on, no first-shell Sr error at m21 or m05 is within 25 meV.
  - Over that span the logged m21 RMSE_F falls from 29.4 to 15.6 meV/Å. That is 47% of its epoch-11 value,
    and the last 21.5% of the Initial → epoch-82 fall.
  - **Spread.** Over the 12 later kept checkpoints (epochs 15–82), the first-shell errors spread over
    51–67 meV per site: m21 hinge −65.5 to −121.5 meV, m05 hinge −42.8 to −93.9 meV.
  - **No consistent drift.** Least-squares slopes over kept epochs 15–82 are +0.12 to +0.33 meV per epoch.
    They rest largely on epoch 77 (0.00 to +0.19 without it). Over kept epochs 11–82 they lie between −0.09
    and +0.10.
- **m05 as training data.** At m05, whose binding frames are training data, the first-shell Sr errors lie
  within 18.4 meV of zero at kept epochs 4–8. They are below −25 meV by kept epoch 11 and stay there.

**Q3. Do the m21 loss and the m21 E_b RMS rank the 20 checkpoints alike? No (as read here).**
- **ρ.** Spearman's ρ = −0.12 (average ranks; scipy gives the same). It is descriptive, with no test, for
  20 non-independent checkpoints.
- **The reading is an interpretation.** The plan sets no threshold for "alike". Reading a ρ near zero as
  "not alike" is an interpretation (§5).
- **What the loss ranking means here.** The kept checkpoints are the epochs at which the m21 loss reached a
  new minimum, so the loss ranks them in reverse epoch order. ρ is therefore also the negative of the rank
  correlation between epoch and E_b RMS.
- **Shape.** The relation is not monotonic.
  - The m21 E_b RMS is highest at kept epochs 0 and 2 (100.3 and 111.0 meV).
  - It is lowest at 3–8 (31.3–38.2 meV).
  - It is higher again from 11 on (47.4–77.5 meV).
- **Kept epochs ≥ 3 alone.** Over these 18 checkpoints ρ = −0.53. This is a post hoc description, not a
  reading, and it depends on the cut:
  - it reflects the step between kept epochs 3–8 (low E_b RMS, higher loss) and ≥ 11 (higher E_b RMS);
  - from kept epoch 8 on, ρ = −0.05 (14 checkpoints);
  - from 11 on, ρ = +0.18 (13 checkpoints).
- **Range.** The m21 E_b RMS spans 31.3 (epoch 7) to 111.0 meV (epoch 2). Every checkpoint is above the
  zero-shot 29.1 meV.

## 4. D2 — attribution of the barrier change along the band path (reason 7)

**The bands and atom groups.**
- **Bands.** All 37 bands with frames at images 0, 2, 3, 4 and 6: 18 training, 3 m21 and 16 test.
- **The path.** The rule quantity uses the path 0 → i* through the images with frames: 0, 2 and 3 (DFT
  i* = 3 in 35 bands) or 0 and 2 (i* = 2 in 2 bands). Image 6 serves only to identify the hopping I.
- **Hopping I.** The hopping I is unambiguous in every band: its displacement from image 0 to image 6 is
  3.62–4.17 Å, and that of the next I is at most 0.54 Å.
- **The 6 Å groups.**
  - Other inorganic atoms (besides the hopping I) within 6 Å of the hop midpoint: 11–14 per band.
  - Organic molecules within 6 Å: 1–3 per band.

**D2a, the closure check.**
- **Definition.** The closure is W(i*) − [E(i*) − E(0)], with W = −Σ_k ½(F_k + F_k+1)·Δr_k over the
  available images.
- **What it measures.** When the forces are minus the gradient of the energy (F = −∇E), the closure is the
  trapezoid quadrature error of the line integral along the straight segments between images.
  - For both MACE models this holds exactly.
  - For DFT it holds to within SCF and force convergence. The forces are the q = 0 forces, the negative
    derivatives of the raw F (q = 0) used as E.
- **The table.** It gives the closure in meV, as RMS over the 37 bands with the range in brackets. The
  single-segment closures are reported beside the plan and carry no rule.

| Level | 0→2 | 2→3 | 3→4 | 0→i* (own argmax) |
|---|---|---|---|---|
| DFT (raw F) | 79.2 (−142.4 to −35.1) | 5.7 (−14.3 to +0.1) | 2.6 (−1.4 to +6.6) | 83.2 (−144.7 to −41.9) |
| zero-shot | 66.3 (−104.3 to −14.7) | 6.7 (−20.7 to +3.1) | 3.7 (−11.6 to +6.6) | 69.4 (−107.7 to −24.6) |
| fine-tuned | 85.9 (−144.6 to −37.5) | 2.2 (−4.1 to +4.6) | 3.8 (−8.2 to +6.4) | 85.7 (−145.0 to −33.4) |

- **No band is resolved.** The DFT closure exceeds 20 meV in magnitude in 37 of 37 bands. Every closure
  to i* is negative, at all three levels.
- **The error is in the 0 → 2 segment**, which spans the missing image 1.
  - The 2 → 3 and 3 → 4 segments close to 2.2–6.7 meV in RMS.
  - Single bands reach up to 14.3 meV for DFT and 20.7 meV for zero-shot on 2 → 3.
- **It is a discretisation error, not a data or sign error.**
  - The two models are conservative by construction. Their closures have the same size and sign as
    DFT's.
  - The 2 → 3 and 3 → 4 segments close to a few meV in RMS at all three levels.
- **Scratch check with image 1.** This check is not part of the outputs. It used the zero-shot model only,
  on four bands: m05 undoped, m12 undoped, m30 GA and m27 Sr.
  - **Provenance.** The 0 → 2 values were first obtained in a development probe, before the first full
    run, and were reproduced in the final check (§8). The full-path values come from the final check only.
  - **0 → 2 segment.** Adding image 1 shrank the closures from −69.3, −89.2, −79.8 and −102.9 meV to
    −19.0, −25.7, −30.8 and −23.7 meV.
  - **Full path.** The full-path closures to i* = 3 went from −74.9, −93.5, −87.6 and −105.6 meV to −24.6,
    −30.0, −38.6 and −26.5 meV. **Image 1 alone does not bring any of the four within 20 meV.**
  - **Later, D3 (§10.1).** On the path through image 1 densified to 8 intervals per segment, both models
    close to 0.745 meV or less, with closure4/closure8 3.97–4.03 in every band. These zero-shot image-1
    closures, like the coarse D2a closures of both models (on the chord path C, |closure8| at most
    2.094 meV at n = 8; at most 2.106 meV on the segment 0 → 2 alone), are therefore quadrature error. DFT
    has no values at image 1 or between images, so Q4 is unchanged.

**D2b and D2c.**
- **No resolved-band result.** No band is resolved, so there is none.
- **Per-band values.** They are kept in `d2_path_attribution.json` with status "not resolved", as the plan
  requires.
- **The all-37-band summary.** It is written beside them as an addition: `summary.D2b.all_37_bands_beside`
  and `summary.D2c.all_37_bands_beside`.
  - It is **not a Q4 reading and is not interpreted here**.
  - **Its error.** Its error is the difference of two levels' quadrature errors. This holds exactly for the
    closure on the DFT segment, RMS 21.7 meV.
  - **Against the direct E_a change.** That change also carries the argmax differences in 6 bands (7
    model–band differences; corrected from "7 bands" on 2026-11-03 with the D3 plan). There the summed D2b
    attribution closes to RMS 21.7 meV (max 49.1 meV), against a mean |direct change| of 46.3 meV.
  - **Against converged values (D3, §10.4).** On its own path (C), the coarse hop_I value of ΔW_g lay a
    median 18.4 meV below its converged value (C_R − D2b; largest |difference| 49.3 meV, in a band whose C
    is not resolved). For the other four groups the median difference is 1.0 meV or less (largest
    5.8 meV). Summed over the five groups, these differences are minus the n = 1 closure difference of
    the two models on C (RMS 21.7 meV, as above), to within the Richardson residual.

**Q4. Is the systematic E_a lowering carried mainly by the hopping I and its first shell, or by the far
field and the organic sublattice? It cannot be read: no band is resolved.**
- **The literal rule.** The plan's literal rule ("otherwise mixed") would give "mixed", but only
  vacuously: with 0 resolved bands, neither count can exceed half of them.
- **Recording.** This is recorded as the one departure from the plan (§5). The D2c count beside Q4 is
  likewise empty.

## 5. Departures, interpretations and additions

**Where they are recorded.** Most items are also listed in the JSONs (`departures_from_plan`,
`interpretations_of_plan`, `additions_to_plan`). Some are recorded only elsewhere:
- item 4 (the midpoint epoch) and item 9 are in the JSON definitions or fields;
- item 6 can be inferred only by matching the Q3 losses with `models.*.logged_m21.loss`;
- item 7: the E0 swap is in a check note, and the reasoning is in this document only;
- the tie rule of item 10 is in the code;
- items 11 and 19 are new in this document.

**Departure.**
1. With no resolved band, Q4 is reported as "cannot be read", not as the plan's literal "mixed". The
   literal result is kept beside it as `plan_literal_reading`.

**Interpretations of the plan's wording.**
2. **Q2 scan order.** "First exceed 25 meV" is scanned in training order with Initial first, so a site
   already above 25 meV before training is answered "Initial".
3. **Q2 brackets.** Each onset is located only to its kept-epoch bracket.
4. **Q2 fall.** "The fall of the m21 force RMSE" is described by:
   - the fraction of the Initial → epoch-82 fall reached at the onset, as a range over the bracket;
   - the first epoch at or below its midpoint.
5. **Q1 signs.** "Signs right" is `scripts/39` `sites()` `sign_agree`. The first-shell Sr sites are the
   WP2c sites named Sr_hinge and Sr_flank, matched by name; a missing name stops the run.
6. **Q3 loss.** Q3 uses the logged m21 loss, the quantity the selection used.
7. **Zero-shot comparison.**
   - The zero-shot model carries the foundation E0s, and the training log's Initial uses `E0s.json`.
   - The E0s cancel in E_a, ΔE_a and E_b, so check 2 is applied to the checkpoints only.
   - Initial is compared after the swap, and reported only.
8. **D2 rule and i*.** "Resolved" is |DFT closure| ≤ 20 meV, with i* each level's own argmax (DFT on
   raw F). D2b and D2c use the DFT i*.
9. **D2b direct change.** The "direct E_a change" of D2b is E_a(fine-tuned) − E_a(zero-shot), each at its
   own argmax (the WP3 quantity). The change on the DFT segment is given beside it.
10. **D2 groups and shares.**
    - The hop midpoint is r_I(0) + ½ mic(r_I(6) − r_I(0)). "Near" is d < 6 Å, at image 0.
    - Molecules are found by `scripts/38` `molecule()` and assigned whole by their C. The script asserts
      that the five groups partition the atoms.
    - Shares are of the summed attribution. A share of exactly 0.5 counts for neither side.
11. **Q3 "alike".** The plan sets no threshold. ρ = −0.12 is read as "not alike".

**Additions (extra checks, or results reported beside).**
12. Q2: the first error below −25 meV, the first epoch from which |error| stays above 25 meV, and the same
    onsets for both sites together (an addition in the D1 JSON).
13. The first-shell-only Q1 condition and the computed Q1 caveat (§3). The first-shell-only condition is
    less strict than the plan's rule.
14. The checkpoint-set and improving-epoch identity, and the `last_epoch` identity.
15. The NaN-prefilled loading with its bitwise check.
16. The dataset-against-QE cross-check, and the two reproductions of `wp3_eval.json`.
17. The per-segment closures, and the D2c and per-split counts beside Q4.
18. The all-37-band D2b/D2c summaries, which are not a reading.
19. The Q3 shape and ρ over kept epochs ≥ 3, and the Q2 late-drift slopes. These are written in this
    document only, as post hoc descriptions.

**Run record.** Four full runs wrote into `wp3/diagnostics/`. Each recorded the script sha256 in its
console header (times in UTC, 2026-11-03).

| Run | Script sha256 | What happened to it |
|---|---|---|
| 09:48 | eb96c9d8… | Its JSONs (not kept) labelled the all-band block with a Q4-style verdict, and its outputs were deleted. Its console output matched the 10:03 run's, apart from the header. |
| 10:03 | d027b16e… | Code reviews A and B examined it (§6). |
| 10:51 | ee966ff5… | The rerun after the review fix pass. |
| 11:09 | f13f0308… | The final run, recorded in this document. It followed a change to one console phrase: an onset in a kept-epoch bracket is printed as "an epoch in (a, b]". |

- **Scratch runs.** Two development runs and the reviewers' reruns wrote to scratch only.
- **The console log.** The log is appended to, so it was cleared before the final run and holds that run
  only. The earlier runs' console captures were kept in scratch.
- **Values across runs.**
  - The 10:51 and 11:09 runs agree in every JSON value except the script sha256. Their console logs differ
    only in that sha, the header time and the onset wording.
  - Against the 10:03 run, the one changed answer is the intended review fix A2: the Q2 literal onset of
    the flank sites became "Initial" instead of epoch 0.
- **Effort.** The plan named no single-point count. The 1658 single points took about 13 minutes per full
  run.

## 6. Review record

**Implementation review.** Two adversarial code reviews ran on the 10:03 run:
- A, plan conformance and physics. It recomputed three bands and two checkpoints independently.
- B, reproduction and provenance. It made two byte-identical reruns, a fresh loader and an independent QE
  parse of all 328 dataset frames.

Neither found a wrong value. Their ten findings were all accepted and fixed:

| Finding | Problem | Fix |
|---|---|---|
| A1 | Q4 with no resolved band departs from the literal rule | Recorded as a departure; the literal result kept beside |
| A2 | The literal Q2 onset of the flank sites omitted Initial | Answered "Initial" |
| A3 | The Q2 onsets are only bracketed | Brackets and fall-fraction ranges recorded |
| A4 | The Q1 rule cannot discriminate (Sr_mid) | Caveat computed and recorded |
| A5 | A vacuous `all()` in the Q1 sign test | Sites asserted by name |
| A6 | The all-band share counts read like a Q4 verdict | Renamed `not_a_reading_share_counts`, with the closure scale attached |
| B1 | The model provenance block of `d1_checkpoints.json` was overwritten by a key collision | Renamed `model_files`; a no-collision assertion added |
| B2 | Input files without hashes | sha256 and git status of all ten inputs recorded |
| B3 | Check 1 could not detect a loader that did nothing | NaN-prefilled copy and a bitwise check added |
| B4 | Bytecode written into `scripts/__pycache__` | `sys.dont_write_bytecode` set |

**Final check.** The adversarial check of this document, the figure and the outputs is recorded in §8.

## 7. Interpretation (not pre-registered; nothing here is tested)

**Reason 6 (selection).**
- **Within the kept checkpoints, no choice would have met the condition.** The best on m21 E_b (epoch 7)
  still has a Sr flank error of −38.5 meV, 13.5 meV beyond the bound. The zero-shot model has the lowest
  m21 E_b RMS of all 21 models.
- **The choice mattered in size.**
  - The loss-selected epoch 82 has twice the m21 E_b RMS of epoch 7 (63.8 against 31.3 meV).
  - Its first-shell errors are about −90 meV, against −19 and −38 meV at epoch 7.
  - The E_b RMS at kept epochs 3–8 is lower than at every later kept epoch, the selected one included.
- **Unkept epochs.** These had a higher m21 loss than the last kept one and were not evaluated. A better
  E_b at one of them cannot be excluded. From kept epoch 11 on, however, both m21 first-shell errors are at
  or below −60.4 meV at every kept checkpoint.
- **A held-out set would be needed.** Selecting on E_b would need a held-out E_b set; m21 has already
  served for selection.

**What the trajectory adds to reason 1** (the effective energy weight on near-equilibrium frames). It is
consistent with that reason but does not test it.
- **The m05 course.**
  - At m05 (training frames) the first-shell Sr errors are near zero at kept epochs 4–8.
  - From kept epoch 11 on they lie at −28 to −105 meV.
  - Meanwhile the logged m21 force and energy RMSEs fall overall (29.4 → 15.6 meV/Å; 1.00 → 0.25 meV per
    atom), though not monotonically.
- **What it is consistent with.** A fit in which continued training improves what the loss weights while
  these energy differences between training frames move away from their labels.
  - The data show the two together, not a trade-off.
  - No training-set loss or per-frame m05 fit is reported here.
- **Late scatter.** Over kept epochs 15–82 the first-shell errors spread over 51–67 meV per site, with no
  consistent drift. This is consistent with a loss that constrains these differences weakly.

**The early overshoot** is an observation relevant to the recipe of roadmap option C, not a test.
- The m21 force RMSE rose above its Initial value at epochs 0 and 1 (108.8 and 122.5 meV/Å).
- At kept epochs 0 and 2 the first-shell Sr errors overshot by +131 to +194 meV. Epoch 1 was not
  evaluated.
- The first epochs therefore moved the model's predictions away from those of the foundation model before
  the fit recovered. No distance in weight space was measured.
- A smaller first step is one candidate recipe change, for example a warm-up or a lower initial learning
  rate. It has not been tried.

**Reason 7 (the barrier lowering)** remains unattributed.
- **The path is too coarse.** The path through images 0, 2 and 3 is too coarse for a 20 meV attribution.
  Adding image 1 alone did not bring any of four checked bands within 20 meV (zero-shot, §4).
- **D2b needs no DFT.** An attribution of the fine-tuning change (D2b) needs only model single points,
  for two reasons:
  - both models are conservative, so a denser path (image 1 and points between images) can make their
    quadrature error small;
  - a closure rule on the two model levels would replace the DFT-based rule.

  That would be a new analysis, post hoc with respect to D2. It would need its own plan before
  computation.
- **D2c needs DFT.** An attribution of the model error against DFT (D2c) would need DFT forces at image 1,
  and probably at points between images.

## 8. Final check

**How the check ran.** One adversarial round ran with four independent lenses (numbers, plan conformance,
figure, provenance and public-repository hygiene). It reported 55 findings: 5 rated "error", 22
"imprecise" and 28 "minor".
- **No computed value was wrong.**
  - The D1 and D2a tables were recomputed from the JSONs.
  - The source-data CSVs reproduce the plotted values.
  - The script sha256 matches the JSONs, the console log and this document.
  - The input hashes match the files.
  - The new files contain no local paths, user names, host names, IP addresses or instance ids.
- **The image-1 scratch check was reproduced independently** (§4).

**Accepted and applied.**
- **"Recovery" wording.** "No recovery" was wrong: the m21 hinge returns to −19.4 meV at kept epoch 7.
  The text now says "no lasting recovery" and states the exception.
- **"Main fall".** "Within the main fall" of the force RMSE was undefined and misleading. It is replaced by
  the fall fractions (56–78%) and the statement that the steepest part of the fall precedes the onsets.
- **Literal Q2 answer.** It is now given first (Initial or epoch 0). The collapse onsets are marked as an
  addition.
- **Overshoot span.** It is corrected to kept epochs 0–3 (largest at 2; epoch 1 not evaluated). The
  roadmap no longer puts the +194 meV value in "the first two epochs".
- **Size of the selection effect.** It is now stated (63.8 against 31.3 meV), with the Q3 shape and
  ρ = −0.53 over kept epochs ≥ 3 as post hoc descriptions (cut-dependent: −0.05 from epoch 8 on, +0.18
  from 11 on). The Q3 "not alike" reading is listed as an interpretation.
- **Causal wording.** It is removed from §7 and from the roadmap ("consistent with", not "shows" or
  "would therefore have to"). "Without trend" is replaced by "no consistent drift", with the slopes and
  their sensitivity to epoch 77 and to the window.
- **Path description.** It is corrected to images 0, 2 and 3 (image 6 identifies the hopping I). All four
  bands of the image-1 scratch check are now given; none comes within 20 meV.
- **WP3_RESULT and roadmap pointers.** The `WP3_RESULT.md` pointer for reason 6 now names the
  first-shell-only check. The roadmap restricts "not a remedy" to the kept checkpoints.
- **§2 and §5.** The inputs, the single-point count, the checks header and the run record (all four full
  runs) are corrected, and §5 is aligned with what the JSONs record.
- **Figure.**
  - Panel a now draws epochs 96–99.
  - Panel b joins kept checkpoints with dotted lines only and states the literal Q2 onsets.
  - The shaded bracket is labelled an addition.
  - The bound bands are neutral grey, and m05 is orange (no longer close to the zero-shot colour).
  - Subscripts are set in upright Arial, and "force RMSE" replaces RMSE_F, since F also names the energy
    basis.
  - The epoch-7 point sits above the zero-shot diamond.
  - The jitter of d no longer encodes band order; i* and the rule unit are stated.
  - The source data no longer flag Initial as kept and now include the GA sites.
  - The axes are created in label order.
  - The figure QA was rerun: alignment PASS, PDF text ≥ 5.25 pt, collisions 0 fail and 0 warn.
- **Commit identity.** The commit is made under the GitHub no-reply address of the repository owner,
  because the default identity carried the local host name. Earlier commits are unchanged.

**Second round.** A second round (two lenses: text, figure) checked the revisions.
- **Result.** It found no error, but 16 imprecise or minor points in the text and 12 in the figure.
- **Text, applied.**
  - **Drift.** The weak drift after epoch 11 rested on epoch 77 and on the window, so it now reads "no
    consistent drift".
  - **ρ = −0.53.** Its cut-dependence is stated.
  - **Path description.** It is corrected in the roadmap and in `WP3_RESULT.md`.
  - **WP3_RESULT pointer.** The reason-6 pointer now states the size of the selection effect.
  - **Image-1 provenance.** The scratch values' provenance is corrected: the full-path values come from
    the final check only.
  - **Physics.** The sign convention and the DFT caveat of the closure are stated.
  - **Wording.** Smaller fixes cover the run record, the checks header, the recording list of §5 and
    several roundings.
- **Figure, applied.**
  - **Fall fractions.** The onset fall fractions are 56–78%; 47% is the bracket's open left end.
  - **Shading.** It is the union of the onset brackets, (3, 6] and (8, 11], in neutral grey.
  - **Panel b.** It states the first-shell-only Q1 result. The four series are offset horizontally, Sr_mid
    has markers, and the connector legend reads "joins evaluated models only".
  - **Axis.** linscale is 1.
  - **Labels.** Panel c names the lowest-RMS epoch, and d's x label is corrected.
  - **QA rerun.** Alignment PASS, PDF text ≥ 5.25 pt, collisions 0 fail and 0 warn.

**Not changed.** Absolute local paths in six files committed earlier (not part of this change) are left
for a separate clean-up. They are noted for the PI.

## 9. Files

- **Plan.** `WP3_DIAGNOSTICS_PLAN.md` (d69fe75).
- **Code.** `scripts/44_wp3_diagnostics.py`.
- **Outputs.** `wp3/diagnostics/d1_checkpoints.json`, `wp3/diagnostics/d2_path_attribution.json` and
  `wp3/diagnostics/diag_console.log`.
- **Figure.** `figures/fig_wp3_diagnostics.{py,pdf,png,svg,tiff}`, with:
  - its layout-QA records `fig_wp3_diagnostics.alignment.{json,svg}` and `.collision-audit.json`;
  - its source data `figures/source_data/fig_wp3_diagnostics_*.csv`.

  The panels are:
  - a: the logged m21 force RMSE of every epoch, with the kept checkpoints and the brackets of the collapse
    onsets;
  - b (Q1, Q2): the first-shell Sr E_b errors at m21 and m05 for Initial and the 20 kept checkpoints, with
    m21 Sr_mid;
  - c (Q3): the m21 E_b RMS against the logged m21 loss;
  - d (Q4, D2a): the path-work closure per segment and to i*, for the 37 bands.
- **Not committed** (off-repository):
  - the 20 checkpoints (`<CKPT_DIR>`);
  - the band geometries (`../bands`).
- **D3.** Plan, code, outputs and figure: §10.12.

## 10. D3 — where the fine-tuned model books its change of E(i\*) − E(0) (post hoc, descriptive)

**Status.** D3 follows `WP3_DIAGNOSTICS_D3_PLAN.md`, committed at ddb352b before any interpolated-point
single point was computed.
- **What it is.** A pre-specified description, reported only, with **no verdict** (plan §7). No "mainly
  local", "mainly far" or other binary reading is drawn, and no share of a signed sum is used.
- **What it is not.**
  - It does not answer Q4, which stays "cannot be read" (§4); Q4 is not answered retroactively.
  - It does not run the test that `WP3_RESULT.md` §8 reason 7 names (a line integral of the model − DFT
    force residual), so reason 7 stays "origin not established".
  - It says nothing about whether the fine-tuning change moves the model towards DFT (no new DFT was
    computed), and nothing about the recipe beyond description.
- **Nothing here changes** a WP3 verdict, a threshold or the outcome (**No improvement**).

### 10.1 Summary

- **The quantity.** Per band, ΔS = [E_FT(i\*) − E_FT(0)] − [E_ZS(i\*) − E_ZS(0)], with i\* the DFT argmax
  image of D2 (image 3 in 35 bands, image 2 in m21_GA and m21_Sr). ΔS is negative in all 37 bands: mean
  −46.89 ± 4.74 meV (SE over bands), median −41.3, range −130.1 to −6.0 meV.
- **Resolution.** All 37 bands are resolved on the band path P (plan §6); no band is excluded. The chord
  path C is not resolved in 6 of them, so the path-dependence summary uses 31 bands:
  - m12_undoped, m12_Sr, m27_undoped and m27_Sr: fine-tuned |closure8| 2.01–2.09 meV, above the 2 meV
    bound;
  - m30_undoped and m30_Sr: hop_I convergence ratio 1.71 and 1.88, outside [2, 8].
- **D3a, the quadrature is resolved on P.** The median |closure8| is 0.39 (zero-shot) and 0.33 meV
  (fine-tuned), and the largest 0.745 meV. closure4/closure8 is 3.97–4.03 on P and 3.86–4.18 on C in every
  band (medians 4.00 and 4.01): the h² error of the trapezoid rule, which tends to zero for a conservative
  model. With the images alone (one interval per segment, n = 1), the closures of the two models are
  −46.0 to −10.2 meV on P and −145.0 to −24.6 meV on C.
  - **For the two models only.** For conservative models the closure is quadrature error by construction
    (§4). D3 shows that it converges as h², with no data, sign or wrapping defect, on D2a's path C as on P
    (C at n = 8: largest 1.78 meV zero-shot and 2.09 meV fine-tuned). The D2a model closures ran to each
    model's own argmax; the segment 3 → 4 (fine-tuned m05_undoped and m05_GA) was not densified. This says
    nothing about DFT, which has no values at image 1 or between images, and does not answer Q4.
- **The work gauge, ΔW_g** (Richardson, P; mean ± SE over the 37 bands, meV): hop_I −23.25 ± 4.34,
  inorganic < 6 Å −31.49 ± 2.97, inorganic ≥ 6 Å +15.30 ± 1.55, organic < 6 Å −5.93 ± 2.62 and
  organic ≥ 6 Å −1.52 ± 2.57. The mean |ΔW_g,8 − ΔW_g,4| is 0.15 meV or less per group.
- **The site-energy gauge, Δε_g** (same order): +27.91 ± 4.17, −136.24 ± 5.28, +82.09 ± 4.76,
  −22.61 ± 7.80 and +1.96 ± 6.09 meV. The site energies sum to ΔS in every band (within 1.2 × 10⁻⁸ meV);
  the Richardson work terms sum to W_FT − W_ZS, which differs from ΔS by the closure difference, by less
  than 0.01 meV (less than 0.24 meV at n = 8).
- **Sign comparison of the two gauges** (plan §7 margin rule; §10.3):
  - hop_I: **disagree** (work −23.25, site energy +27.91; by host 3 agree, 7 disagree, 4 not resolved);
  - inorganic < 6 Å: **agree**;
  - inorganic ≥ 6 Å: **agree**;
  - organic < 6 Å: **agree**, with |mean ΔW_g| = 5.93 meV just above its 5.25 meV margin; it is "sign not
    resolved" in the training and test splits, and per band the signs agree in 22 of 37;
  - organic ≥ 6 Å: **sign not resolved**.
  - The SE treats the 37 bands as independent; up to three share a host.
  - **Per band**, the signs of all five groups agree in 5 bands, four in 17, three in 8, two in 6 and one
    in 1. By group they agree in 12 (hop_I), 37, 35, 22 and 24 of the 37 bands.
- **Size against the zero-shot work.** The zero-shot work of the hopping I along P has mean +210.4 meV
  (item 3); the ratio of its fine-tuning change to it, ΔW_g/W_ZS,g, has median −0.09 (range −0.37 to
  +0.19; |W_ZS,g| ≥ 5 meV in all 37 bands). For the other four groups the mean zero-shot work is +2.0, −3.4, −7.6 and −35.7 meV, and
  the ratio is defined (|W_ZS,g| ≥ 5 meV) in 5, 9, 19 and 36 of the 37 bands.
- **Path dependence** (31 bands with both P and C resolved): mean |ΔW_g(P) − ΔW_g(C)| is 0.39–1.95 meV
  per group, largest 10.89 meV (hop_I, m14_Sr). This is well above the conservative quadrature error (mean
  |X8 − X4|(P) + |X8 − X4|(C) 0.50 meV or less; mean e(P) + e(C) 0.17 meV or less). The mean signed
  difference P − C is −1.18 to +1.18 meV per group.
- **The seen coarse D2b values against their converged values.** On the same path C, the coarse hop_I
  values of D2b lay a median 18.4 meV below their converged values (C_R − D2b; largest |difference|
  49.3 meV, in m12_undoped, whose C is not resolved; 42.9 meV over the 31 bands with C resolved). For the
  other four groups the median difference is 1.0 meV or less in magnitude and the largest 5.8 meV.
- **Cancellation.** The median κ is 1.40, and κ > 2 in 13 of 37 bands. κ is ill-conditioned where |ΔS| is
  small (plan §4); the two largest, 12.0 and 11.6, are in m10_undoped and m04_undoped, where |ΔS| is 12.7
  and 6.7 meV (§10.3).
- **D3d, regularity.** On P the energy profile is close to its cubic Hermite interpolant (excess −0.06 to
  +3.83 meV, zero-shot; −0.04 to +2.61 meV, fine-tuned). The largest per-atom displacement per segment of
  P is 0.21–0.97 Å, and no interior point of P or C has a pair closer than 1.006 Å.
- **How to read it** (plan §2).
  - D3 shares the models, image forces, groups and segment with D2b, so agreement with the coarse
    picture is weak evidence.
  - A large ΔW for hop_I and inorganic < 6 Å taken together is expected anyway: together they carry a
    median 0.84 of Σ|Δr|² (hop_I alone 0.78, inorganic < 6 Å 0.065). These displacement shares were known
    before D3 (plan §2).
  - Both gauges come from the same two models, and the site-energy partition is the model's own, not
    unique physically; they are not independent checks of each other.
  - Up to three bands share a host. In the 18 training bands the fine-tuned model was fitted at images 0,
    2, 3, 4 and 6, not at image 1 or at any path point, so the training-split values describe it partly
    away from its fitted geometries. Differences between splits are not a generalisation measure.

### 10.2 What was run

- **Code.** `scripts/45_wp3_d3_dense_path.py` (sha256
  866f01f5c74b6c23db03f3aa654355cfc0e5a13b807f19814875672bb9eaa3a5), reusing the group, displacement,
  molecule and model-loading code of `scripts/44` (and `scripts/38`/`39` helpers). MACE in float64 on CPU,
  4 threads, laptop; no MD, relaxation, training or QE.
- **Outputs.** `wp3/diagnostics/d3_dense_path.json` (sha256 559a6777…) and `wp3/diagnostics/d3_console.log`
  (033e2c8e…), which holds the recorded run only.
- **Single points.** 2442: 1221 per model, 33 per model and band (images 0–4; 21 interior points of the P
  segments 0→1, 1→2, 2→3; 7 of the chord 0→2).
- **Inputs.** The dataset, the WP2c selection, `d2_path_attribution.json`, `wp3.model`, the plan and the
  37 band files, each with its sha256 in the JSON head. The archived QE outputs, read by the check-4
  cross-check, are not hashed (`input_files.note`). Package versions (mace 0.3.16, torch 2.14.1, ase
  3.29.0, numpy 2.5.4) and the model sha256 values equal D2's. Git head ddb352b; of the six scripts used
  and the eight hashed inputs inside the repository, only `scripts/45` was uncommitted (JSON `git`).

**Checks** (plan §8; fail-closed except 10). No interpolated point was evaluated before checks 1–6 and 8
had passed on the images.

| Check | Result |
|---|---|
| 1 Models and packages | sha256 zero-shot 01bfe221…, fine-tuned 3f7bf6f5… and the four package versions equal D2's |
| 2 Plan | committed at ddb352b, identical to that commit and to HEAD; no local change |
| 3 Band files | 37 bands, 7 frames, same cell and species; steps 0→1 … 3→4 and 0→2: max \|mic − raw\| 2.8 × 10⁻¹⁶ Å, max \|Δr\| 1.428 Å, max \|r + Δr − r_end\| 5.6 × 10⁻¹⁷ Å |
| 4 Image geometry against the dataset | 185 frames; positions and cell bitwise equal, and the dataset's DFT energies and forces equal the archived QE outputs (max \|ΔF\| 5.0 × 10⁻⁹ eV/Å) (the `scripts/44` cross-check) |
| 5 Stored zero-shot values, images 0–4 | max \|ΔE\| 1.4 × 10⁻⁹ eV, max \|Δε_i\| 6.8 × 10⁻⁸ eV (tolerance 10⁻⁶); max \|ΔF\| 7.6 × 10⁻⁷ eV/Å (reported) |
| 6 D2 reproduction | 925 numbers (D2a `segments_beside`, D2b `groups_meV`, `segment_change_meV`, `direct_meV`, i\*, hop_I, group sizes): max difference 9.8 × 10⁻¹⁵ meV (tolerance 10⁻³); i\* from raw F equals D2's in all 37 bands |
| 7 Identities | work 2.0 × 10⁻¹³ meV; Σε_i = E 7.3 × 10⁻¹¹ eV; Σ_g Δε_g = ΔS 1.1 × 10⁻⁸ meV; E_a link 0; property `energies` (with E0s), not `node_energy` |
| 8 Molecules | partition unchanged at 1184 path points of P, C and the extensions |
| 9 Single points | 2442 (1221 + 1221), as planned |
| 10 Image-1 scratch closures of §4 (reported) | all eight recomputed within 0.042 meV of the values in §4 |

**Run record** (plan §9; every run logged with its script sha256 and its value differences). The
development runs used real bands, so they are kept as scratch runs with their values, off-repository in
the private WP3 record folder (`WP3_RESULT.md` §9 item 26), with a SHA256SUMS list. No choice of n, bound,
criterion or summary was open after them (plan §9).

| Run (UTC) | Script sha256 | Bands | Exit | Note |
|---|---|---|---|---|
| 12:54 dev1 | d27ae4fb… | m21_GA, m05_undoped | 0 | scratch; values identical to the 13:01 run (0 of 2026 numeric leaves differ; 112 geometry-list leaves exist only in the 13:01 run) |
| 12:57 dev2 | 6f377c36… | m30_GA, m27_Sr, m21_Sr, m12_undoped | 0 | scratch; largest difference from the 13:01 run 2.8 × 10⁻¹⁴ meV (1.2 × 10⁻¹¹ in a convergence ratio); statuses equal |
| 13:00 full | 6f377c36… | — | 7 | code defect (a TypeError in the `--bands-only` check) before check 3; no band read, no value; its console log, written into the output folder, was moved out by hand before the next run |
| 13:01 full | 18a8dc72… | 37 | 0 | the run reviewed by A and B |
| 13:32 review B | 18a8dc72… | 37 | 0 | scratch reproduction; JSON byte-identical to the 13:01 run |
| 14:07, 14:08 fix-round dev | 866f01f5… | none; m21_GA, m05_undoped | 5; 0 | a fail-path test that reads no band; then 0 of 2138 values differ from the 13:01 run |
| 14:11 full | 866f01f5… | 37 | 0 | **recorded run**; no value differs from the 13:01 run (0 of 36 487 numeric leaves, 544 of them compared at their moved keys); keys moved and head text changed (§10.9) |

Reviewer B also ran 22 gate tests in scratch (on m21_GA where a band was needed): 19 injected faults, each
stopping with the intended exit code (2–7), and 3 unchanged controls (exit 0). Reviewer A recomputed three
bands with independent code (198 single points; §10.9).

**Departures, interpretations and additions.**
- **Departures from the plan: none** (`departures_from_plan` is empty).
- **Interpretations of the plan's wording** (18, all in `interpretations_of_plan`). Among those that
  shape the numbers:
  - path points are r_k + (j/8)Δr_k with Δr_k by `find_mic`, and the quadrature step is Δr_k/n;
  - statements, the ΔW_g/W_ZS,g ratio, its 5 meV threshold and κ use Richardson values;
  - a convergence ratio with a zero denominator is null and falls under its criterion's exemption; bounds
    are inclusive;
  - item 5 is summarised over the P-resolved bands (37), including the 6 whose C is not resolved;
  - sign comparison: SE = SD (ddof 1)/√n; "exceed" is strict; with n < 2 the sign is "not resolved"; it
    is given for every subset;
  - "mean of host means" averages every mean statistic over the 14 hosts with equal weight; medians,
    ranges and counts are per host only;
  - D_g is summed over the n = 8 steps of P;
  - item 4 gives the mean and largest |difference|, with the signed mean beside; item 7 is given per model
    over the P-resolved bands, so its C rows include the 6 bands whose C is not resolved;
  - the definitions of the 6 Å crossings, the shortest bond and the Hermite excess (over j = 1…7);
  - the 2 → 3 extension carries its criterion values but no status, and enters no criterion or summary.
- **Additions** (12, all in `additions_to_plan`): the `--bands-only` development option (refused for the
  default output folder); the evaluation order above; extra D2 reproductions and the assertion that the
  new n = 1 quadrature equals `scripts/44` `path_work`; assertions on i\*, on the plan commit, on the
  `energies` property and on the E_a link; n = 1 values beside n = 8, 4, 2; Hermite values for the chord
  0 → 2 and the extension segment, beside D3d; D_g also along C, and Δε_g and ΔS to image 3 for the two
  extension bands; the molecule check at the extension points, and beside it at image 4; the console log
  written only after exit 0; ΔS, the summed ΔW and SE beside the plan's statistics.
- **Computed for this write-up** from the per-band values, not in `summaries`: the per-band
  closure4/closure8 ranges, the n = 1 closure ranges on P and C, the range of the summed-work residual, the per-host tallies of the sign
  statements, the per-group per-band sign counts, item 5 over the 31 bands with C resolved, the bands of
  the largest values, the D3d ranges and counts, the image-0 distances of the 6 Å crossings and the
  displacement share of hop_I and inorganic < 6 Å together.

### 10.3 D3a–D3c summaries over the 37 resolved bands (plan §7 items 1–3, 6, 7)

**Items 1 and 2.** ΔW_g is the Richardson value on P; Δε_g the site-energy gauge (meV).

| Group | ΔW_g mean ± SE | median | range | mean \|ΔW8 − ΔW4\| | Δε_g mean ± SE | median | range |
|---|---|---|---|---|---|---|---|
| hop_I | −23.25 ± 4.34 | −19.8 | −71.8 to +19.9 | 0.15 | +27.91 ± 4.17 | +28.1 | −51.3 to +74.9 |
| inorganic < 6 Å | −31.49 ± 2.97 | −29.2 | −65.9 to −2.5 | 0.04 | −136.24 ± 5.28 | −138.9 | −186.9 to −51.9 |
| inorganic ≥ 6 Å | +15.30 ± 1.55 | +14.1 | −7.9 to +43.6 | 0.02 | +82.09 ± 4.76 | +71.6 | +39.9 to +155.5 |
| organic < 6 Å | −5.93 ± 2.62 | −1.8 | −40.4 to +19.3 | 0.02 | −22.61 ± 7.80 | −14.9 | −136.0 to +72.7 |
| organic ≥ 6 Å | −1.52 ± 2.57 | −3.4 | −39.4 to +54.1 | 0.01 | +1.96 ± 6.09 | −12.9 | −66.7 to +84.2 |
| sum (ΔW: W_FT − W_ZS; Δε: = ΔS) | −46.89 ± 4.74 | −41.3 | −130.1 to −6.0 | 0.17 | −46.89 ± 4.74 | −41.3 | −130.1 to −6.0 |

**Sign comparison** (plan §7). A statement needs both |means| above their margins: max(2 meV, 2 SE), plus
the mean |ΔW_g,8 − ΔW_g,4| for the work gauge.

| Group | \|mean ΔW_g\| | margin | \|mean Δε_g\| | margin | Statement |
|---|---|---|---|---|---|
| hop_I | 23.25 | 8.82 | 27.91 | 8.33 | disagree |
| inorganic < 6 Å | 31.49 | 5.99 | 136.24 | 10.56 | agree |
| inorganic ≥ 6 Å | 15.30 | 3.11 | 82.09 | 9.53 | agree |
| organic < 6 Å | 5.93 | 5.25 | 22.61 | 15.60 | agree |
| organic ≥ 6 Å | 1.52 | 5.15 | 1.96 | 12.17 | sign not resolved |

**Item 3, comparators** (meV; W_ZS,g and W_FT,g are Richardson values on P, with the mean |X8 − X4| in
brackets).

| Group | mean W_ZS,g | mean W_FT,g | bands with e(W_ZS,g) or e(W_FT,g) > 1 meV | median D_g | ΔW_g/W_ZS,g where \|W_ZS,g\| ≥ 5 meV: n; median (range) |
|---|---|---|---|---|---|
| hop_I | +210.4 (1.45) | +187.1 (1.34) | 0 | 0.778 | 37; −0.09 (−0.37 to +0.19) |
| inorganic < 6 Å | +2.0 (0.14) | −29.5 (0.18) | 0 | 0.065 | 5; −6.88 (−10.65 to −2.33) |
| inorganic ≥ 6 Å | −3.4 (0.05) | +11.9 (0.07) | 0 | 0.027 | 9; −2.27 (−4.52 to +1.20) |
| organic < 6 Å | −7.6 (0.02) | −13.5 (0.02) | 0 | 0.049 | 19; +0.91 (−3.18 to +4.11) |
| organic ≥ 6 Å | −35.7 (0.01) | −37.2 (0.01) | 0 | 0.071 | 36; +0.16 (−1.23 to +1.97) |

The ratio is large where W_ZS,g is small; it is a scale comparison only.

**Item 6, cancellation.** κ = (|L| + |N|)/|L + N|, L = ΔW(hop_I) + ΔW(inorganic < 6 Å): median 1.40,
κ > 2 in 13 of 37 bands (largest m10_undoped 12.0 and m04_undoped 11.6, where |ΔS| is 12.7 and 6.7 meV).

**Item 7, D3a** (meV; over the 37 P-resolved bands, so the C rows include the 6 bands whose C is not
resolved).

| Path | Model | median \|closure8\| | largest \|closure8\| | median closure4/closure8 |
|---|---|---|---|---|
| P | zero-shot | 0.39 | 0.74 | 4.00 |
| P | fine-tuned | 0.33 | 0.73 | 4.00 |
| C | zero-shot | 1.13 | 1.78 | 4.01 |
| C | fine-tuned | 1.18 | 2.09 | 4.01 |

**By split** (mean ΔW_g on P and mean Δε_g, meV). Per-split medians and ranges are in
`summaries.by_split`; items 3–7 are in the table after the host table.

| Split | n | ΔW_g: hop_I | in < 6 | in ≥ 6 | org < 6 | org ≥ 6 | Δε_g: hop_I | in < 6 | in ≥ 6 | org < 6 | org ≥ 6 | mean ΔS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| training | 18 | −37.1 | −36.2 | +17.7 | −5.3 | −5.9 | +28.5 | −142.4 | +94.0 | −34.7 | −12.1 | −66.7 |
| m21 | 3 | +16.7 | −13.9 | +7.5 | −11.3 | −14.3 | +55.2 | −119.3 | +75.0 | −14.1 | −12.3 | −15.4 |
| test | 16 | −15.1 | −29.5 | +14.1 | −5.7 | +5.8 | +22.2 | −132.5 | +70.1 | −10.7 | +20.5 | −30.5 |

- Sign statements by split: training and test as overall for hop_I (disagree) and the two inorganic groups
  (agree), with both organic groups "sign not resolved"; m21 (n = 3) agree for hop_I and the two inorganic
  groups, both organic groups "sign not resolved".
- The splits differ in their bands and hosts; the differences are not a generalisation measure (plan §3).

**By host** (mean ΔW_g on P and mean Δε_g, meV; per-host medians and ranges are in `summaries.by_host`).

| Host | n | ΔW_g: hop_I | in < 6 | in ≥ 6 | org < 6 | org ≥ 6 | Δε_g: hop_I | in < 6 | in ≥ 6 | org < 6 | org ≥ 6 | mean ΔS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| m05 | 3 | −2.9 | −65.2 | +13.9 | −21.7 | −4.0 | +15.2 | −148.1 | +117.0 | −31.9 | −32.3 | −80.1 |
| m06 | 3 | −57.3 | −38.8 | +14.8 | −5.2 | −5.9 | +43.0 | −152.1 | +95.2 | −45.8 | −32.7 | −92.4 |
| m08 | 3 | −23.3 | −31.0 | +18.3 | −0.6 | −7.7 | +34.4 | −150.4 | +70.2 | +16.4 | −14.9 | −44.3 |
| m12 | 3 | −16.0 | −49.4 | +8.8 | +8.7 | −4.3 | +58.0 | −168.7 | +86.3 | −62.8 | +35.2 | −52.1 |
| m15 | 3 | −54.7 | −16.8 | +17.8 | −2.9 | +15.5 | −15.6 | −108.7 | +78.7 | +16.6 | −12.1 | −41.0 |
| m20 | 3 | −68.7 | −15.6 | +32.7 | −9.9 | −28.8 | +35.7 | −126.2 | +116.4 | −100.5 | −16.0 | −90.4 |
| m21 | 3 | +16.7 | −13.9 | +7.5 | −11.3 | −14.3 | +55.2 | −119.3 | +75.0 | −14.1 | −12.3 | −15.4 |
| m30 | 3 | −15.9 | −20.0 | +18.6 | −26.4 | +1.9 | +15.4 | −124.7 | +46.3 | −9.6 | +30.8 | −41.8 |
| m32 | 3 | +11.8 | −14.3 | +15.8 | −33.2 | −3.5 | +22.2 | −90.0 | +105.7 | −18.7 | −42.7 | −23.5 |
| m10 | 2 | −39.4 | −39.2 | +11.6 | −2.3 | +42.3 | +20.0 | −133.7 | +67.2 | −50.3 | +69.7 | −27.0 |
| m18 | 2 | −3.5 | −55.6 | +22.0 | +6.2 | +3.5 | +30.1 | −178.1 | +56.5 | +19.0 | +45.1 | −27.4 |
| m04 | 2 | −22.2 | −25.7 | +23.2 | +16.4 | −6.8 | −6.2 | −176.5 | +64.4 | +71.3 | +31.8 | −15.1 |
| m14 | 2 | −17.2 | −29.6 | −5.3 | +5.8 | +0.2 | +34.7 | −146.3 | +95.1 | −83.9 | +54.4 | −46.0 |
| m27 | 2 | −32.4 | −34.8 | +9.3 | +17.9 | +9.8 | +42.4 | −103.6 | +49.4 | +1.1 | −19.4 | −30.1 |
| **mean of host means** | 14 hosts | −23.2 | −32.1 | +14.9 | −4.2 | −0.2 | +27.5 | −137.6 | +80.2 | −20.9 | +6.1 | −44.8 |

Sign statements per host (n = 2–3; agree / disagree / sign not resolved, out of 14 hosts): hop_I 3 / 7 / 4;
inorganic < 6 Å 13 / 0 / 1; inorganic ≥ 6 Å 12 / 1 / 1; organic < 6 Å 5 / 3 / 6; organic ≥ 6 Å
4 / 3 / 7.

**Items 3–7 by split and by host** (hop_I for items 3–5; meV). Item 4 is over the bands of the subset with
both P and C resolved. Medians and counts have no mean of host means (§10.2). Item 3's means of W_ZS,g and
W_FT,g, its e > 1 meV count and median D_g per subset, and all values of the other groups, are in
`summaries.by_split`, `summaries.by_host` and `summaries.by_host_mean_of_host_means` (hop_I host means of
W_ZS,g and W_FT,g: +209.7 and +186.5 meV).

| Subset | n | item 3: ΔW/W_ZS median (n) | item 4: mean \|P − C\| (n) | item 5: C_R − D2b median (largest \|·\|) | item 6: median κ; κ > 2 | item 7: P median \|closure8\| ZS / FT |
|---|---|---|---|---|---|---|
| training | 18 | −0.18 (18) | 1.46 (16) | +21.7 (49.3) | 1.37; 2 | 0.35 / 0.30 |
| m21 | 3 | +0.19 (3) | 0.31 (3) | +20.7 (22.0) | 2.36; 2 | 0.22 / 0.24 |
| test | 16 | −0.08 (16) | 3.01 (12) | +6.2 (27.0) | 2.58; 9 | 0.46 / 0.36 |
| m05 | 3 | −0.02 (3) | 2.58 (3) | −9.5 (11.0) | 1.00; 0 | 0.31 / 0.24 |
| m06 | 3 | −0.29 (3) | 0.54 (3) | +27.5 (29.5) | 1.38; 0 | 0.31 / 0.25 |
| m08 | 3 | −0.09 (3) | 1.88 (3) | +19.3 (22.6) | 1.44; 0 | 0.32 / 0.28 |
| m12 | 3 | −0.05 (3) | 0.01 (1) | +48.8 (49.3) | 1.44; 0 | 0.47 / 0.49 |
| m15 | 3 | −0.35 (3) | 1.95 (3) | +24.0 (26.9) | 2.74; 2 | 0.36 / 0.30 |
| m20 | 3 | −0.27 (3) | 0.81 (3) | +8.3 (20.8) | 1.00; 0 | 0.73 / 0.72 |
| m21 | 3 | +0.19 (3) | 0.31 (3) | +20.7 (22.0) | 2.36; 2 | 0.22 / 0.24 |
| m30 | 3 | −0.04 (3) | 4.71 (1) | −1.1 (11.5) | 1.00; 0 | 0.53 / 0.34 |
| m32 | 3 | +0.06 (3) | 1.47 (3) | +18.4 (18.8) | 1.33; 1 | 0.39 / 0.39 |
| m10 | 2 | −0.30 (2) | 0.96 (2) | +3.1 (5.1) | 7.32; 2 | 0.32 / 0.22 |
| m18 | 2 | −0.02 (2) | 0.71 (2) | +9.4 (11.5) | 3.37; 2 | 0.33 / 0.26 |
| m04 | 2 | −0.11 (2) | 4.60 (2) | +14.3 (18.8) | 7.57; 2 | 0.42 / 0.42 |
| m14 | 2 | −0.08 (2) | 7.19 (2) | −14.6 (26.2) | 1.06; 0 | 0.47 / 0.35 |
| m27 | 2 | −0.13 (2) | — (0) | +24.9 (27.0) | 3.50; 2 | 0.47 / 0.45 |
| **mean of host means** | 14 hosts | — | 2.13 (13 hosts) | — | — | — |

### 10.4 Path dependence and the seen coarse values (plan §7 items 4 and 5)

**Item 4.** Over the 31 bands with both P and C resolved (meV; Richardson values).

| Group | mean \|ΔW_g(P) − ΔW_g(C)\| | largest | mean signed (P − C) | mean e(P) + e(C) | mean \|X8 − X4\|(P) + \|X8 − X4\|(C) |
|---|---|---|---|---|---|
| hop_I | 1.95 | 10.89 | −0.16 | 0.17 | 0.50 |
| inorganic < 6 Å | 1.58 | 4.79 | +1.18 | 0.04 | 0.11 |
| inorganic ≥ 6 Å | 1.19 | 2.09 | −1.18 | 0.02 | 0.07 |
| organic < 6 Å | 0.94 | 4.01 | +0.20 | 0.03 | 0.08 |
| organic ≥ 6 Å | 0.39 | 2.16 | −0.04 | 0.01 | 0.02 |

**Item 5.** The seen coarse D2b `groups_meV` (path C at n = 1) against the converged values, over the 37
P-resolved bands (6 of them with C not resolved): median signed difference and largest |difference|, meV.
C_R − D2b is the quadrature error of the seen values on their own path. Over the 31 bands whose C is also
resolved (computed for this write-up), C_R − D2b for hop_I has median +17.6 meV (largest 42.9 meV); for
the other groups the medians stay at 1.0 meV or less (largest 5.8 meV).

| Group | C_R − D2b: median | largest | P_R − D2b: median | largest |
|---|---|---|---|---|
| hop_I | +18.4 | 49.3 | +18.0 | 47.3 |
| inorganic < 6 Å | +0.4 | 5.8 | +1.6 | 5.0 |
| inorganic ≥ 6 Å | −1.0 | 2.1 | −2.1 | 3.5 |
| organic < 6 Å | +0.2 | 5.4 | +0.7 | 5.9 |
| organic ≥ 6 Å | +0.2 | 2.6 | +0.2 | 3.8 |

### 10.5 The E_a link and the 2 → 3 extension

**E_a link** (plan §1). In the 6 bands where a model's own argmax differs from i\* (7 model–band
differences), E_a change = ΔS + [E_FT(i\*_FT) − E_FT(i\*)] − [E_ZS(i\*_ZS) − E_ZS(i\*)] (meV; identity
asserted, difference 0).

| Band | i\* | own argmax ZS, FT | E_a change | ΔS | FT term | ZS term |
|---|---|---|---|---|---|---|
| m05_undoped | 3 | 3, 4 | −63.62 | −73.92 | +10.30 | 0 |
| m05_GA | 3 | 3, 4 | −72.61 | −82.83 | +10.22 | 0 |
| m15_GA | 3 | 3, 2 | −50.32 | −60.41 | +10.09 | 0 |
| m15_Sr | 3 | 3, 2 | −11.66 | −20.83 | +9.17 | 0 |
| m21_GA | 2 | 3, 2 | −22.77 | −12.25 | 0 | +10.52 |
| m21_Sr | 2 | 3, 3 | −14.04 | −5.95 | +7.16 | +15.25 |

**The 2 → 3 extension** (m21_GA, m21_Sr; beside, no status, in no summary). To image 3, ΔS is −23.69 and
−14.04 meV.
- ΔW_g on P_ext (hop_I, inorganic < 6, ≥ 6, organic < 6, ≥ 6): m21_GA +16.7 / −12.8 / +6.2 / −17.9 / −16.0;
  m21_Sr +23.9 / −25.4 / +6.7 / −6.1 / −13.0 meV.
- ΔW_g on C_ext (same order): m21_GA +16.8 / −13.7 / +6.9 / −18.0 / −15.7; m21_Sr +23.7 / −27.2 / +7.9 /
  −5.6 / −12.8 meV.
- Δε_g to image 3: m21_GA +53.7 / −117.1 / +102.8 / −28.9 / −34.2; m21_Sr +64.2 / −139.6 / +70.8 /
  −17.3 / +8.0 meV.

### 10.6 D3d, path regularity (reported, no rule)

- **Hermite excess on P** (37 bands, segments to i\*): −0.06 to +3.83 meV (zero-shot), −0.04 to +2.61 meV
  (fine-tuned). Beside it, on the chord 0 → 2: 1.67–14.21 and 4.11–16.36 meV.
- **Interior points above the higher bracketing image.** In 33 model–segment cases an interior point of P
  lies above both its images, all in the segment 2 → 3. The largest excesses are 2.93 meV (zero-shot,
  m04_Sr) and 8.81 meV (fine-tuned, m27_Sr). E_a and i\* are defined on the images only (plan §1); these
  values do not enter them.
- **The two extension segments 2 → 3** (beside, outside D3d): Hermite excess 0.13–0.57 meV; an interior
  point lies above both images in all four model–band cases (3.02–5.35 meV).
- **Geometry** (model-independent). The largest per-atom displacement per segment is 0.21–0.97 Å on P and
  1.09–1.43 Å on the chord 0 → 2 of C. At the interior points, the shortest intramolecular bond and the
  shortest pair distance differ from those at the images by −0.0021 to +0.0031 Å on P and −0.0067 to
  +0.0031 Å on C. The shortest pair at any interior point is 1.010 Å on P and 1.006 Å on C.
- **6 Å crossings.** 19 atoms in 16 bands (0–2 per band) cross 6 Å from the hop midpoint somewhere on P
  between image 0 and i\*. All of them lie within 0.11 Å of 6 Å at image 0 (5.899–6.048 Å). Group
  membership stays as at image 0 (plan §5).

### 10.7 Exclusion report (plan §6)

- **No band is excluded** on P, in any split or host: training 18 of 18, m21 3 of 3, test 16 of 16
  resolved; each of the 14 hosts has all its bands resolved. No criterion failed on P, so the check on
  selection is vacuous: the resolved set is the whole D2 set, and its ΔS and seen coarse D2b values are
  those of all 37 bands (ΔS per band in §10.8; D2b `groups_meV` per band in `exclusion_report.by_host` and
  `.by_split`).
- **C not resolved** in 6 resolved bands (two bands each of hosts m12, m27 and m30), listed in §10.1. They
  are left out of item 4 only.
- **ΔS and the seen coarse D2b values** of the resolved bands are given per band in
  `exclusion_report.by_host` and `.by_split`. By split, ΔS runs from −130.1 to −20.8 meV (training),
  −27.9 to −6.0 meV (m21) and −60.6 to −6.7 meV (test).

### 10.8 Per-band values

ΔS, ΔW_g (Richardson, P) and Δε_g in meV; κ; and the status of C. Every band is resolved on P.

| Band | Split | i\* | ΔS | ΔW_g: hop_I | in < 6 | in ≥ 6 | org < 6 | org ≥ 6 | Δε_g: hop_I | in < 6 | in ≥ 6 | org < 6 | org ≥ 6 | κ | C |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| m05_undoped | training | 3 | −73.9 | +1.2 | −64.3 | +12.4 | −21.9 | −1.4 | +20.2 | −147.9 | +114.0 | −33.4 | −26.7 | 1.00 | resolved |
| m05_GA | training | 3 | −82.8 | −4.4 | −65.9 | +16.1 | −24.4 | −4.3 | +8.9 | −143.4 | +114.5 | −32.8 | −30.1 | 1.00 | resolved |
| m05_Sr | training | 3 | −83.4 | −5.6 | −65.5 | +13.0 | −18.9 | −6.4 | +16.6 | −152.9 | +122.4 | −29.4 | −40.1 | 1.00 | resolved |
| m06_undoped | training | 3 | −73.0 | −59.7 | −27.1 | +16.3 | +3.3 | −5.9 | +26.8 | −145.1 | +65.3 | −2.9 | −17.1 | 1.38 | resolved |
| m06_GA | training | 3 | −130.1 | −54.1 | −58.6 | +14.0 | −21.8 | −9.7 | +74.9 | −157.7 | +155.5 | −136.0 | −66.7 | 1.00 | resolved |
| m06_Sr | training | 3 | −74.2 | −58.1 | −30.9 | +14.1 | +2.9 | −2.1 | +27.4 | −153.6 | +64.7 | +1.5 | −14.1 | 1.40 | resolved |
| m08_undoped | training | 3 | −39.4 | −17.2 | −29.2 | +13.8 | −0.6 | −6.1 | +38.9 | −147.2 | +69.5 | +12.4 | −12.9 | 1.36 | resolved |
| m08_GA | training | 3 | −54.6 | −33.7 | −32.9 | +23.6 | −0.3 | −11.3 | +22.4 | −160.6 | +71.6 | +27.3 | −15.3 | 1.44 | resolved |
| m08_Sr | training | 3 | −39.1 | −18.9 | −31.0 | +17.4 | −0.8 | −5.8 | +41.9 | −143.5 | +69.5 | +9.4 | −16.5 | 1.55 | resolved |
| m12_undoped | training | 3 | −54.4 | −14.0 | −52.5 | +8.9 | +6.5 | −3.4 | +60.6 | −174.7 | +92.0 | −69.5 | +37.1 | 1.44 | not resolved: FT \|closure8\| 2.06 meV |
| m12_GA | training | 3 | −40.5 | −19.9 | −37.5 | +9.7 | +12.2 | −5.0 | +56.1 | −152.8 | +80.4 | −53.8 | +29.6 | 1.83 | resolved |
| m12_Sr | training | 3 | −61.4 | −13.9 | −58.1 | +7.8 | +7.5 | −4.7 | +57.2 | −178.6 | +86.4 | −65.1 | +38.8 | 1.35 | not resolved: FT \|closure8\| 2.06 meV |
| m15_undoped | training | 3 | −41.9 | −56.2 | −22.1 | +21.3 | −2.7 | +17.9 | +7.9 | −138.9 | +107.1 | +15.7 | −33.7 | 2.74 | resolved |
| m15_GA | training | 3 | −60.4 | −63.8 | −25.8 | +15.4 | −4.1 | +17.9 | −3.4 | −135.3 | +63.5 | +18.3 | −3.5 | 1.97 | resolved |
| m15_Sr | training | 3 | −20.8 | −44.0 | −2.5 | +16.8 | −1.8 | +10.7 | −51.3 | −51.9 | +65.5 | +15.9 | +0.9 | 3.46 | resolved |
| m20_undoped | training | 3 | −96.2 | −71.8 | −13.2 | +43.6 | −15.4 | −39.4 | +28.1 | −127.1 | +127.2 | −97.9 | −26.5 | 1.00 | resolved |
| m20_GA | training | 3 | −96.1 | −67.4 | −16.5 | +35.7 | −19.2 | −28.8 | +23.4 | −126.8 | +133.5 | −128.7 | +2.5 | 1.00 | resolved |
| m20_Sr | training | 3 | −79.0 | −66.9 | −17.2 | +18.7 | +4.7 | −18.3 | +55.7 | −124.6 | +88.7 | −74.9 | −23.9 | 1.13 | resolved |
| m21_undoped | m21 | 3 | −27.9 | +13.7 | −18.5 | +7.6 | −14.8 | −15.9 | +58.1 | −135.7 | +105.2 | −30.4 | −25.1 | 1.00 | resolved |
| m21_GA | m21 | 2 | −12.3 | +17.8 | −8.8 | +7.2 | −14.2 | −14.3 | +52.2 | −104.0 | +74.1 | −10.4 | −24.1 | 2.46 | resolved |
| m21_Sr | m21 | 2 | −6.0 | +18.5 | −14.5 | +7.6 | −5.0 | −12.6 | +55.3 | −118.2 | +45.9 | −1.4 | +12.4 | 2.36 | resolved |
| m30_undoped | test | 3 | −43.3 | −26.0 | −12.4 | +17.9 | −23.7 | +0.9 | +35.0 | −138.7 | +45.6 | −14.7 | +29.5 | 1.00 | not resolved: hop_I ratio 1.71 |
| m30_GA | test | 3 | −47.9 | −12.7 | −23.5 | +24.7 | −40.4 | +3.9 | +22.6 | −156.5 | +53.2 | −18.0 | +50.7 | 1.00 | resolved |
| m30_Sr | test | 3 | −34.3 | −9.2 | −24.0 | +13.2 | −15.1 | +0.8 | −11.4 | −79.0 | +39.9 | +4.0 | +12.2 | 1.00 | not resolved: hop_I ratio 1.88 |
| m32_undoped | test | 3 | −11.0 | +19.9 | −11.2 | +10.4 | −29.9 | −0.1 | +31.4 | −90.4 | +99.6 | −14.9 | −36.8 | 2.57 | resolved |
| m32_GA | test | 3 | −46.2 | +1.6 | −19.9 | +25.0 | −40.2 | −12.7 | +1.5 | −89.4 | +125.8 | −24.1 | −60.0 | 1.00 | resolved |
| m32_Sr | test | 3 | −13.3 | +14.0 | −11.8 | +12.0 | −29.6 | +2.2 | +33.5 | −90.1 | +91.6 | −17.0 | −31.2 | 1.33 | resolved |
| m10_undoped | test | 3 | −12.7 | −42.3 | −40.6 | +19.0 | −2.9 | +54.1 | +19.5 | −132.9 | +66.8 | −50.2 | +84.2 | 12.04 | resolved |
| m10_GA | test | 3 | −41.3 | −36.5 | −37.8 | +4.2 | −1.8 | +30.5 | +20.5 | −134.4 | +67.6 | −50.4 | +55.3 | 2.60 | resolved |
| m18_undoped | test | 3 | −23.3 | −3.5 | −52.3 | +22.0 | +6.7 | +3.8 | +30.7 | −174.1 | +47.3 | +24.9 | +47.9 | 3.79 | resolved |
| m18_GA | test | 3 | −31.6 | −3.6 | −58.9 | +22.1 | +5.7 | +3.2 | +29.5 | −182.1 | +65.6 | +13.1 | +42.4 | 2.96 | resolved |
| m04_undoped | test | 3 | −6.7 | −22.0 | −20.4 | +22.8 | +17.7 | −4.9 | −6.4 | −172.2 | +64.5 | +72.7 | +34.7 | 11.60 | resolved |
| m04_Sr | test | 3 | −23.5 | −22.4 | −31.1 | +23.7 | +15.1 | −8.8 | −6.0 | −180.7 | +64.4 | +69.8 | +28.9 | 3.55 | resolved |
| m14_undoped | test | 3 | −60.6 | −14.5 | −49.8 | −2.7 | +5.9 | +0.4 | +59.6 | −186.9 | +74.6 | −79.7 | +71.8 | 1.12 | resolved |
| m14_Sr | test | 3 | −31.5 | −19.8 | −9.4 | −7.9 | +5.7 | −0.1 | +9.7 | −105.7 | +115.6 | −88.1 | +37.0 | 1.00 | resolved |
| m27_undoped | test | 3 | −26.4 | −31.7 | −31.4 | +7.9 | +19.3 | +9.5 | +42.3 | −95.1 | +45.1 | +2.5 | −21.1 | 3.79 | not resolved: FT \|closure8\| 2.01 meV |
| m27_Sr | test | 3 | −33.8 | −33.0 | −38.1 | +10.7 | +16.5 | +10.1 | +42.5 | −112.1 | +53.7 | −0.2 | −17.7 | 3.21 | not resolved: FT \|closure8\| 2.09 meV |

### 10.9 Review record

**Implementation review.** Two adversarial code reviews ran on the 13:01 run:
- A, plan conformance, physics and numerics. It recomputed m05_undoped, m21_GA and m30_Sr with its own
  code (own minimum image, interpolation, groups, molecules, Hermite solve and calculators; 198 single
  points): all 1463 compared quantities agree with the JSON; the largest difference is 1.5 × 10⁻⁸ meV (a
  Hermite excess), and ratios, distances, indices and criterion outcomes agree to the same or better in
  their own units.
- B, reproduction and provenance. Its full rerun gave a byte-identical JSON; its 19 injected faults each
  stopped with the intended exit code; every input sha256 matched.

Neither found a wrong value. Their four findings were accepted and fixed:

| Finding | Problem | Fix |
|---|---|---|
| A1 | The extension kept a pass/fail flag under a key that says it has no status | Only the criterion values are kept |
| A2 | `D3d.hermite` also held the chord 0 → 2 and the extension segment | D3d holds P to i\* only; the chord and the extension segment moved beside it |
| B1 | The run log gave no value differences for the 13:01 run | Differences recorded against the development runs (none computable against the failed run) |
| B2 | The failed run's console log had been written into the output folder and moved by hand; the run records lived only in volatile scratch | Console log written only after exit 0; run records copied, with a SHA256SUMS list, to the private WP3 record folder outside the session workspace (`WP3_RESULT.md` §9 item 26) |

The fix round reran the full script to fix these code defects (A1, A2 and the code part of B2), as plan §9
allows, giving the 14:11 recorded run. No value changed. 544 leaves moved to new keys (the chord and
extension Hermite entries and the extension criterion values); 148 `in_P_to_i_star` flags and 92 extension
flags were dropped. Text changed only in `script_sha256`, interpretation 18, addition 8, the new addition
11 and `definitions`.

**Final check.** The adversarial check of this section, the figure and the pointers is recorded below
(§10.11).

### 10.10 Figure

- **`figures/fig_wp3_d3`** (nature-figure, Python; 183 × 146.5 mm). Every plotted and printed number is
  read from the JSON at plot time. The script asserts the JSON sha256, the script sha256 and the plan
  commit, recomputes every printed plan summary from the plotted values and asserts that it equals the
  JSON. The printed additions (the closure signs and the count above 2 meV in a, the largest bar in b, the
  clearances in c, the band of the largest |P − C| in d) are computed from the same values.
  - **a (D3a).** |closure8| against |closure4| for 37 bands × 2 models × 2 paths (n = 148), log-log, with
    the ratio-4 line (h²), the [2, 8] window, the 2 meV bound and the 0.5 meV exemption level. All
    closures are negative; the four points above 2 meV are fine-tuned closures on C.
  - **b (D3b).** ΔW_g (Richardson, P) per group for the 37 bands, beside the zero-shot work W_ZS,g on the
    same axis, both with ±|X8 − X4| bars (all 370 inside the markers; largest 0.65 meV for ΔW_g and
    2.7 meV for W_ZS,g, hopping I, m20_GA); ticks are means; D is the median displacement share D_g.
  - **c (D3b against D3c).** ΔW_g against Δε_g (n = 185), with the group means ± the plan's sign margins
    and, in brackets, |mean| − margin for each gauge. There is no y = x line: the gauges are different
    partitions, and the plan compares signs only.
  - **d (item 4).** ΔW_g(P) against ΔW_g(C) for the 31 bands with both resolved (n = 155), with the y = x
    line; the 6 bands whose C is not resolved are not drawn (their values are in the source data).
- **QA.** Render-time alignment gate PASS (4 comparisons). validate_figure.py: 19 pass, 2 documented
  warnings (FONT-GLYPH-FLOOR: subscripts only in 7.5 pt text; LEGEND-LABEL-CASE: lower-case labels as in
  the other WP3 figures). PDF text ≥ 5.25 pt. Collision audit 0 fail, 0 warn. Only Arial is embedded. A
  rerun gives byte-identical outputs.
- **Review.** One agent built the figure; two adversarial lenses (numbers and plan conformance; visual,
  statistical honesty and QA) found no error. Their 20 findings (12 minor, 8 suggestions) were all applied
  and are listed in the script's docstring.

### 10.11 Final check

Three independent lenses checked this section, the new D3 text in §1 and §4 and the two pointers against
the JSON, the plan and the run records before commit.
- **Numbers.** Every summary, table cell and derived statement was recomputed from the per-band values of
  the JSON, including all 592 cells of §10.8; the D3d values were checked as look-ups (the JSON keeps no
  interior-point energies); the checks table, the run record and the hashes were checked against the JSON
  checks block, the console log, the run log and the files. No wrong number or sign was found.
- **Plan conformance and rigour.** Two errors, both of wording, now corrected:
  - the D3a statement cited path P for D2a's closures, which were on path C; both paths are now given,
    with the per-band ratio ranges and the own-argmax limit;
  - the path-dependence bullet compared a 31-band mean |difference| with a 37-band SE, a comparison the
    plan does not make; it is removed, and the conservative |X8 − X4| is quoted.
- **Provenance.** One error, now corrected: the run records had been copied only within the session
  workspace. They are now in the private record folder, with a SHA256SUMS list.
- **Minor findings applied.**
  - Wording: spreads added in §1; medians no longer read as bounds; the 0.745 meV bound.
  - Added values: the largest item-5 difference comes from a band whose C is not resolved, so the
    31-band values are given beside it; the geometry on C; C_ext; the extension Hermite values; items
    3–7 by split and by host.
  - Plan reporting: the exclusion report is stated to be vacuous; the interpretation and addition lists
    are completed; the values computed only for this write-up are listed.
  - Caveats: host non-independence, displacement shares known before D3, and the fitted images.
  - Records: the run-record value-difference counts, the check-4 detail and the units of reviewer A's
    comparison.
- **Final pass on the corrected text.** Two further lenses (the corrected text against the data and the
  figure; consistency, rigour and hygiene of the whole change) found no error. Their 20 findings (14
  minor, 6 suggestions) were all applied:
  - upper bounds rounded up (2.094, 1.2 × 10⁻⁸ meV);
  - the 0 → 2 segment bound;
  - reason 7's named test was run by D2 and is not rerun here;
  - the §1 caveats and 31-band value;
  - the κ conditioning note;
  - the mean-of-host-means row of the items 3–7 table;
  - the figure's bar and review counts;
  - the scope of the numbers check;
  - the commit identity (the GitHub no-reply address).

  The hygiene scan of all 22 files (raw text, PDF streams, PNG, TIFF and SVG metadata) found no local
  path, user or host name, IP, cloud identifier or e-mail address.

### 10.12 Files

- **Plan.** `WP3_DIAGNOSTICS_D3_PLAN.md` (ddb352b).
- **Code.** `scripts/45_wp3_d3_dense_path.py`.
- **Outputs.** `wp3/diagnostics/d3_dense_path.json` and `wp3/diagnostics/d3_console.log`.
- **Figure.** `figures/fig_wp3_d3.{py,pdf,png,svg,tiff}`, with:
  - its layout-QA records `fig_wp3_d3.alignment.{json,svg}` and `.collision-audit.json`;
  - its source data `figures/source_data/fig_wp3_d3_*.csv` (8 files).
- **Not committed** (off-repository): the run log and the development and review runs with their values
  (private WP3 record folder, `WP3_RESULT.md` §9 item 26); the band geometries (`../bands`).

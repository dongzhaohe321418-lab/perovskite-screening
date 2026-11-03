# WP3 post hoc diagnostics D1 and D2 — result (2026-11-03)

**Status.** These diagnostics are post hoc and reported only. They follow `WP3_DIAGNOSTICS_PLAN.md`, which
was committed at d69fe75 before any D1 or D2 value was computed.
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
- **For WP3_RESULT.md §8.**
  - **Reason 6** (a checkpoint chosen on a force-dominated m21 loss): no other choice among the kept
    checkpoints would have met the first-shell condition. Unkept epochs were not evaluated, and any
    reselection on m21 would itself be unvalidated.
  - **Reason 7** (the systematic barrier lowering): its origin remains unattributed.

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

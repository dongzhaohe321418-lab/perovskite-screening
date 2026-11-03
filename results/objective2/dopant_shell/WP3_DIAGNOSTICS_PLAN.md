# WP3 post hoc diagnostics D1 and D2 — plan (2026-11-03)

This plan was written and committed before any D1 or D2 value was computed. The repository at commit
fa94731 records the WP3 outcome, **No improvement** (`WP3_RESULT.md`).

## Status and limits

- **Post hoc and reported only.** Nothing here changes a WP3 verdict, a threshold or the outcome
  (amendment m item 4: Outcomes fail-closed).
- **Nothing is validated.** No model is validated or chosen by these diagnostics. A checkpoint
  that looks better on m21 would still be a different, unvalidated model (item 4: "any other model
  is new and unvalidated"). m21 has already served for model selection, and the 7 test hosts are
  used up.
- **Purpose.** To test two of the candidate reasons that `WP3_RESULT.md` §8 lists as untested:
  - reason 6: a checkpoint chosen on a force-dominated m21 loss;
  - reason 7: a systematic lowering of the absolute barriers whose origin is not established.

  The results inform the recipe question of roadmap option C (update 2026-11-03). They do not
  choose among the S2 options; that choice is the PI's.
- **Compute.** Laptop single points only, with MACE in float64 on CPU: no MD, no relaxation, no
  training and no QE.
- **Inputs.** Only committed or already-archived files:
  - the dataset files `wp3/dataset/{train,valid,test}.xyz`, which hold the DFT positions, forces,
    raw F, E′ and E_F of every frame;
  - `wp3/run2/wp3.model`;
  - the 20 kept checkpoints of run2, off-repository in the analysis staging directory;
  - the zero-shot foundation model.

## D1 — checkpoint trajectory (reason 6)

- **Models.**
  - The 20 kept checkpoints of run2: epochs 0, 2, 3, 4, 6, 7, 8, 11, 15, 26, 27, 31, 33, 35, 56,
    59, 77, 80, 81 and 82, the epochs at which the m21 loss improved.
  - The zero-shot model ("Initial").

  Each checkpoint's weights are loaded into the architecture of `wp3.model`.
- **Checks before any value is read.** The script stops if either check fails.
  - The epoch-82 checkpoint must reproduce the energies and forces of `wp3.model` on all 31 m21
    frames to within 1e-6 eV and 1e-6 eV/Å.
  - Every checkpoint's m21 RMSE_E per atom and RMSE_F must equal the values that mace logged for
    that epoch in `run2/results/wp3_run-123_train.txt`, to within 0.5% (the log rounds).
- **Frames.**
  - m21: the 31 valid frames, from which the 3 bands and the 5 far-referenced E_b sites are built.
  - m05: the 16 binding frames, plus the m05 band frames needed for its 3 bands. These are training
    frames, so they measure fit quality.
- **Quantities per model.** They are computed with the `scripts/39` functions (`Ea`, `pair`,
  `sites`).
  - Absolute E_a errors of the m21 and m05 bands, on raw F and on E′.
  - Paired ΔE_a errors (GA and Sr), on both bases.
  - Far-referenced E_b errors at the 5 non-far sites of m21 and of m05, on raw F.
  - For each host, the RMS of those 5 E_b errors.
- **Questions, and how each is read.**
  - **Q1.** Is there a kept checkpoint whose m21 E_b errors are all below 25 meV in magnitude, with
    the Sr hinge and flank signs right?
    - **If yes:** selecting on the whole-cell m21 loss passed over a checkpoint that was better on
      this quantity (reason 6 contributes).
    - **If no:** the collapse of the first-shell Sr E_b is a property of the training, not of the
      selection.
  - **Q2.** At which epoch do the first-shell Sr E_b errors at m21 and at m05 first exceed 25 meV
    in magnitude? How does that epoch compare with the fall of the m21 force RMSE?
  - **Q3.** Do the m21 loss and the m21 E_b RMS rank the 20 checkpoints alike? Spearman's ρ is
    reported, with no test, as a description of 20 non-independent checkpoints.
- **Selection.** No checkpoint is selected, saved as a model or used further.

## D2 — attribution of the barrier change along the band path (reason 7)

- **Bands.** All bands with frames at images 0, 2, 3, 4 and 6:
  - 18 training bands (6 hosts × 3 systems);
  - 3 m21 bands;
  - 16 test bands (m30/m32 and the item-1′ hosts).
- **The path quantity.** Let i* be the image (2, 3 or 4) at which each model's E_a is defined, its
  own argmax. For a path 0 → … → i* through the available images, and with Δr the change of
  minimum-image positions between successive images, the work of a force field F is
  W(i*) = −Σ_k ½ (F_k + F_{k+1}) · Δr_k, the trapezoid rule over the images.
- **D2a, the closure check.**
  - For each model and for DFT (raw F), the closure is W(i*) − [E(i*) − E(0)].
  - This measures the discretisation error of a path with images 1 and 5 missing.
  - **Rule.** A band whose DFT closure exceeds 20 meV in magnitude is reported as "not resolved" in
    D2b and D2c.
- **D2b, the fine-tuning change.**
  - The change of E_a on fine-tuning is attributed to atoms through the work of the force
    difference, −Σ_k ½ (ΔF_k + ΔF_{k+1}) · Δr_k with ΔF = F_finetuned − F_zero-shot. The same i* is
    used, the DFT argmax image, so that both models are compared on one path segment.
  - The atom groups are:
    - the hopping I, the I whose displacement from image 0 to image 6 is largest;
    - the other inorganic atoms within 6 Å of the hop midpoint;
    - the inorganic atoms beyond 6 Å;
    - organic molecules within 6 Å, assigned whole by their C;
    - organic molecules beyond 6 Å.

  - **Reported.** Each group's share of the change, and the closure of the summed attribution
    against the direct E_a change.
- **D2c, the model error.** The same attribution of the fine-tuned E_a error against DFT, with
  ΔF = F_finetuned − F_DFT on raw F, over the same atom groups.
- **Q4, and how it is read.**
  - **The question.** Is the systematic E_a lowering (37 of 37 bands in WP3) carried mainly by the
    hopping I and its first shell, or by the far field and the organic sublattice?
  - **"Mainly local."** The hopping I and the inorganic atoms within 6 Å carry more than half the
    summed change, in more than half the resolved bands.
  - **"Mainly far or organic."** The same, for the groups beyond 6 Å or the organic groups.
  - **Otherwise** the result is "mixed".
  - The attribution is path-dependent, as in WP2e (amendment l item 3). It assigns each
    interaction to the atoms on which its force acts.

## Reporting

- **Code and outputs.** The code is `scripts/44_wp3_diagnostics.py`. Its outputs are
  `wp3/diagnostics/d1_checkpoints.json` and `wp3/diagnostics/d2_path_attribution.json`, with a
  console log.
- **Figure.** One figure, made with the nature-figure workflow: a figure contract, source data
  and the QA gates.
- **Write-up.** A short result, `WP3_DIAGNOSTICS.md`, that answers Q1–Q4 by the readings above.
  It lists every departure from this plan.
- **Checking.** An adversarial check before commit.

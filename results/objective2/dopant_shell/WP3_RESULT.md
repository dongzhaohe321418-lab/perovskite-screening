# WP3 — fine-tuned MACE-MP-0 against DFT on held-out hosts: criterion 6 and the S2 adoption rule (2026-11-03)

## 1. Summary

**Pre-registered outcome (PLAN amendment m item 4): No improvement.** It is fixed by adoption
condition (a), which failed. All five conditions (a)–(e) fail (`wp3/wp3_outcome.json`, step 8).

- **Criterion 6 (amendment m item 3): No improvement.** Force RMSE fell (i); the paired ΔE_a RMS
  rose on raw F and on E′ (ii); and the far-referenced E_b RMS rose (iii). **Criterion 6 as
  amended by h** ((i), (ii) on raw F, (iii)) also gives **No improvement**. Item 5's wording for a
  fail applies: the sample is 4 pairs, 5 sites and 46 frames, and the fail is never a reason to
  adopt, to change a threshold or to re-run.
- **Adoption (a)–(c): not met.**
  - (a) fails with criterion 6.
  - (b) fails: the 9-pair RMS on E′ is 30.9 meV against a bound of 20 meV, and m32 GA and m10 GA
    change class.
  - (c) fails: the Sr hinge and Sr flank errors are −117.8 and −98.5 meV, and the Sr flank sign is
    lost.
- **Adoption (d) and (e): fail.** Item 4 requires both to be run and reported whatever (a)–(c)
  give (§5–6); they could not have changed the outcome.
  - (d): in all six frozen-far-field relaxations the residual DFT force on the free atoms has an
    RMS of 0.053–0.058 eV/Å, against a bound of 0.05. The max condition (< 0.2 eV/Å) and every
    other condition are met. At the zero-shot minimum the free-atom RMS is 0.142–0.160 eV/Å.
  - (e): 10 of the 12 MD runs pass. m30 and m32 undoped at 450 K each have one frame (t = 900 and
    3600 fs of 5000) that fails the organic bonding-pattern test. A post hoc diagnosis (§6) finds
    in each a formamidinium C–H stretched to 1.252 and 1.262 Å, past the test's 1.25 Å cut-off.
- **For S2.** By item 4, S1 ends without a validated potential, and zero-shot MACE is not
  re-admitted. S2 therefore proceeds as in roadmap update 2026-10-28 (S1 status after
  WP2c/2d/2e), consequence 1: "either DFT
  for the decisive quantities or a coarser, dopant-ranking metric whose tolerance matches the
  errors measured here". The choice between these is not made here (see
  `../SCREENING_ROADMAP.md`, update 2026-11-03).
- **Item 6 not run.** Because the outcome is not Validated, item 6 (the WP1 map with the
  fine-tuned model) is not run. Amendment m item 6 decided in advance that this is recorded as a
  deviation from the WP3 row.

The fine-tuned model fitted forces about six times better than zero-shot MACE-MP-0, on every test
frame. It did not reproduce the DFT energy differences that S1 tests. At the m30 Sr hinge site its
far-referenced E_b is +11.6 meV, against +129.4 meV at DFT and +123.0 meV for zero-shot MACE. At its
own relaxed minima its residual DFT forces are 2.5–3.0 times lower than at the zero-shot minima (free
atoms of the frozen-far-field cells; whole cell of the unconstrained ones). On a common component scale,
however, the whole-cell residuals at its unconstrained minima are 2.2–2.4 times its force error on the
image-0 test frames of the same six cells (§5).

All new DFT values are single points at fixed geometries.
- **§3–4 and §7.** These are zero-shot MACE NEB images and WP1 minima.
- **§5.** These are the fine-tuned model's relaxed cells, with two references:
  - the image-0 single points (zero-shot minima);
  - the final step of the WP2e DFT relaxation of m30 GA image 0 (the "DFT minimum", the only
    DFT-relaxed geometry used). The numbers in §3–4 and
§7 come from `wp3/wp3_eval.json`, the one run of `scripts/39` at the note commit, unless another
source is named. The numbers in §5 come from `wp3/wp3b_result.json` and those in §6 from
`wp3/wp3md_result.json`.

## 2. What was run

Everything follows amendment m item 7, steps 1–8. Times are UTC.

1. **Step 1.** `scripts/39` ran in gate-only mode at c02c872 (`gate_only_step1.json`: git head,
   no uncommitted file), whose scripts 29–41 are those of eb92910 (c02c872 adds only the runbook
   and its run-control helpers in `scripts/wp3_runbook/`), and passed (commit 0b79b9c). Scripts
   29–41 are unchanged from eb92910 through c1d0ace (`git diff` is empty).
2. **Frames.** `scripts/35` used the item-1d defaults: 1500 MD steps, a 15 eV/Å bound, and the six
   training hosts. It ran as six per-host processes, followed by the literal all-host command
   (§9 item 3).
   - **Records.** 96 records (`wp3/frames/frames_report.json`); 95 passed the checks.
   - **Rejected.** m06_Sr_md450 failed the topology check (minimum distance 0.966 Å; MACE fmax
     6.664 eV/Å).
   - **Accepted, by kind.** rat05f and rat10f: 24 each. md300: 24. md450: 23.
   - **Accepted, by system.** Undoped + V: 24. GA + V: 24. Sr + V: 23. Pristine: 24.
   - **Ranges.** MACE fmax: rat05f 0.29–0.63, rat10f 0.60–1.64, md300 3.20–5.56 and md450
     4.11–7.33 eV/Å. Minimum interatomic distance: 0.907–1.015 Å.
   - **Minimum count.** W = 95, so the 60-frame minimum of item 1d is met.
3. **DFT single points.** 153 were run at the WP2b settings:
   - 95 WP3 frames;
   - 50 item-1′ band images;
   - 8 q = +1 checks.

   Every output has JOB DONE and a converged SCF. Iterations were 13–23 (WP3), 13–14 (item 1′) and
   13 (checks). No job needed a resubmission: the archive holds no `.tryN` or `.gaveup` file. No
   item-1′ job was re-run.

   The QE chain ran from 2026-10-29 02:50:44 to 20:02:15, which is 6.7 min per single point
   (`run2/node_logs/step2.log`).
4. **Dataset** (`scripts/33`, run once in the node checkout at c391d61; `wp3/dataset/dataset_meta.json`).
   - **Split.**
     - Train, 201 frames: 90 band, 16 binding (m05), 48 rattle and 47 MD.
     - Valid, 31 frames (m21): 15 band and 16 binding.
     - Test, 96 frames: 30 m30/m32 band, 16 m30 binding and 50 item-1′ band.
     - No output was unmatched or skipped. The 36 non-matching outputs are the 28 item-1b
       exclusions and the 8 `chk_` checks.
   - **The q = +1 check** (item 1c; v = F(q = 0) − E_F(q = 0) − F(q = +1)).
     - **(a) passed**, at −1.127 meV. The E′ basis was therefore used.
     - **(b) passed for Sr** (−4.548 meV) and **failed for undoped** (−104.065 meV).
       v(m05_undoped_md450) is −155.29 meV; the other seven v lie between −48.13 and −56.66 meV.
     - **The rule in force.** Item 1c's rule for "(a) passes, (b) fails" therefore applies. The 71
       WP3 vacancy frames carry `config_energy_weight = 0` and keep their forces. The
       energy-labelled training frames are n_E = 130: 90 band, 16 binding and the 24 vacancy-free
       WP3 frames.
   - **Constants.**
     - E_F,ref = 3.3447 eV, equal to the median of the 30 training undoped band frames.
     - c_Sr = −2.174 meV and c_GA = −18.851 meV (E′).
     - The E0s are the foundation E0s plus 4-column offsets fitted over 106 band and binding
       frames (rank 4; residual RMS 82.2 meV).
   - **Loss weights.**
     - L_F = 0.017577 (eV/Å)² and L_E = 2.5017 × 10⁻⁵ (eV/atom)², with N̄ = 232.76.
     - Hence w_E = 70 000 (unrounded 70 260.7) and w_F = 100.
     - Amendment m item 2 gave an indicative w_E ≈ 6.7 × 10⁶, computed from the 106 band and
       binding frames alone. It was labelled indicative, and the rule was applied as written. The
       reason for the difference is in §8.
   - **Start-check reference.** Zero-shot on `valid.xyz` gives 0.333419 meV/atom and
     79.81902 meV/Å, equal to the pre-registered 0.3334 and 79.819.
5. **Training** (`run2/node_logs/`, `run2/logs/`, `run2/results/`).
   - **Software.** `mace_run_train` from mace-torch 0.3.16 (torch 2.14.1+cpu, e3nn 0.4.4). The
     foundation file was passed by path (sha256 01bfe221…ed35845), with
     `--multiheads_finetuning False`.
   - **Settings.**
     - Numerics: float64 on CPU.
     - Loss: weighted, w_E 70000 and w_F 100.
     - Optimiser: Adam with AMSGrad, lr 0.005, weight decay 5e-7 and clip 10.
     - Schedule: ReduceLROnPlateau (factor 0.8, patience 50); EMA 0.99.
     - Run: batch 2, 100 epochs, seed 123, evaluation every epoch, `--keep_checkpoints`.
   - **Pre-flight.** All ten log checks passed (`preflight.txt`).
   - **Threads.** The 2-epoch timing runs took 1333, 948 and 781 s at 8, 16 and 32 threads, so
     T = 32.
   - **run1.**
     - It started at 2026-10-29 20:59:37 and passed the start check: RMSE_F 79.8190 meV/Å and
       RMSE_E_per_atom 0.33342 meV/atom.
     - It was lost to a node loss: a hard stop with no shutdown sequence (read by the operator as
       a spot reclaim; no termination notice was recorded). The last results write was at
       2026-10-30 04:51:30, and the node booted again at 07:15:00.
     - It was discarded, and the identical command was run from scratch (`restarts.txt`; §9 item
       11).
   - **run2.**
     - It started at 07:26:13. Its start check passed at 07:26:43 with values identical to run1's.
     - It finished at 15:05:21. The 100 epochs took 7 h 36 min, about 4.6 min each; item 2 had
       expected 8–15 min per epoch.
   - **Selected epoch: 82.**
     - The log says "Loaded Stage one model from epoch 82".
     - The 20 kept checkpoints are exactly the epochs that improved. Epoch 82 is the highest of
       them and has the lowest m21 loss of the 100 epochs.
   - **m21 (validation), Initial → epoch 82.**
     - Loss: 0.332138 → 0.0147533.
     - RMSE_E_per_atom: 0.3334 → 0.2520 meV/atom.
     - RMSE_F: 79.819 → 15.601 meV/Å.
     - Host-wide offset: +49.27 → −25.44 meV/cell.
       - **Reading stated (amendment m names this quantity without defining it).** It is the mean
         of E_model − REF_energy over the 31 m21 frames, the reading of the note tool. It cancels
         in every within-host ΔE_a and far-referenced E_b.
       - At epoch 82 the SD over the frames is 52.73 meV/cell, and the RMSE with the offset
         removed is 0.22694 meV/atom.
   - **Final error table** (rounded by mace). Train: 0.8 meV/atom and 30.7 meV/Å. Valid: 0.3
     meV/atom and 15.6 meV/Å.
6. **5a (technical failure).** None was found. Losses were finite, and the selected model is finite
   on the 31 m21 frames (`techfail.txt`). There was no retry.
7. **5b (model note).**
   - The note is `wp3/MODEL_NOTE_2026-11-03.md`, committed on its own as CNOTE = c1d0ace.
   - `wp3.model` has sha256 `3f7bf6f5aaaadc72d3954b56dfe3b7bcf5878b0f1be0c115e56c8bcaec65d2ca`
     (13 298 559 bytes). The committed `wp3/run2/wp3.model` has this hash.
   - The note records scripts 39/40/41 at 4c1aaa8 (`scripts/39` sha256 59232da1…). They are
     identical at the training checkout c391d61.
8. **Step 6.** `scripts/39` ran once in full mode, on the analysis laptop at CNOTE with a clean
   tree, from 2026-11-03 00:07:07 to 00:11:16 (`wp3/step6_scripts39.log`).
   - **Run.** The basis was E′, taken from both the argument and `dataset_meta.json`. It used 4
     threads, no cache, and 233 single points per arm. It exited with code 0.
   - **Reproduction gate: PASS.**
     - The frame energies of the 30, 16 and 50 gate frames matched to a maximum of 0, 2.2 × 10⁻¹⁰
       and 1.1 × 10⁻⁹ eV.
     - All 19 stated comparators matched within tolerance, and the 3 exact items matched.
   - **Test frames.** All 96 matched their QE inputs within 10⁻⁶ Å. The evaluated label set
     equals `test.xyz`.
   - **No re-run.** `scripts/39` was not changed and step 6 was not repeated.
9. **Step 7 (node, at C6; `node_step7.sh`).** It ran from 00:22:02 to 07:33:01, with one spot
   reclaim (§5, "Run record").
   - Region and zero-shot comparator: reproduced.
   - 12 relaxations: 6 frozen-far-field (`wp3b_`) and 6 unconstrained (`wp3bu_`).
   - 12 MD runs.
   - 12 QE single points.

   No STOP occurred.
10. **7e and step 8 (analysis laptop, at 602e487; scripts 39, 40 and 41 and their helpers
    unmodified).**
    - **Archive.** The step-7 QE campaign, the two work directories, and the driver's state
      directory, log, rerun list and console output were copied from the node. The copies were
      compared with the node by sha256 and found byte-identical:
      - the QE campaign, 49 files;
      - the relaxation work directory, 97;
      - the MD work directory, 48;
      - the driver's state directory, 162;
      - the driver's log, rerun list and console output.

      The QE files were archived with `rb_archive.sh` (24 files).
    - **Analyses.** `scripts/40 analyse` and `scripts/41 analyse --commit 4c1aaa8` ran once each.
      Then `scripts/39 --outcome-only` ran, which loads no model and reads no QE file. It gave
      "(a) False; (b) not met; (c) not met; (d) fail; (e) fail; OUTCOME: No improvement".
    - **After step 8.** The node was stopped at about 07:44 (§9 item 30). Local paths and the node
      host name were then redacted (§9 item 26), and the diagnostic `scripts/43` was written and
      run (§9 item 27).
11. **Order of work** (git; each commit is the parent of the next).

   | commit | time (2026-11-03) | content |
   |---|---|---|
   | c391d61 | — | node checkout during steps 3–5a (`step34.log`: "start; repo c391d61") |
   | 498062d, 1687267, b9a6a8d | before CNOTE | step-7 tools, the step-3 archive, the S2 builders (§9 item 14) |
   | 4c1aaa8 | 00:06:03 | run2 archive: model, logs, results, node logs; m21 values only |
   | c1d0ace (CNOTE) | 00:06:45 | the model note, alone |
   | 5cf6c5f (C6) | 00:12:48 | `wp3_eval.json` and the step-6 console log only |
   | 602e487 | 01:27:35 | the figure `figures/fig_wp3_criterion6.*`, read from `wp3_eval.json` |
   | the WP3-result commit | after 07:33 | step-7 archive and results, `wp3_outcome.json`, `scripts/43`, the (d)/(e) figure, this result and the roadmap update |

   Before step 7 the node checkout was fast-forwarded from c391d61 to C6, clean (§9 item 2).

## 3. Criterion 6 (pre-registered; decisive for adoption (a))

| statistic | zero-shot (comparator fixed in amendment m) | fine-tuned | strictly below? |
|---|---|---|---|
| (i) force RMSE, 46 m30/m32 frames (eV/Å) | 0.086809 | 0.014945 | yes |
| — of which 30 band / 16 WP2c frames | 0.088867 / 0.082823 | 0.015283 / 0.014290 | |
| (ii) paired ΔE_a RMS, 4 pairs, raw F (meV) | 23.647 | 32.757 | **no** |
| (ii) paired ΔE_a RMS, 4 pairs, E′ (meV) | 38.191 | 42.817 | **no** |
| (iii) far-referenced E_b RMS, 5 m30 sites, raw F (meV) | 28.412 | 69.376 | **no** |

**Verdicts.**
- Criterion 6 (item 3): **No improvement**.
- Criterion 6 as amended by h: **No improvement**.

A pass needs all of the decisive statistics strictly below zero-shot. The verdict is decided by
(ii) and (iii); it does not hang on the E′ condition added in amendment m.

**Reported beside the verdict (not gated).**
- **(i) over all 96 test frames:** 0.088367 → 0.015226 eV/Å (5.8-fold).
- **(ii) over all 9 test pairs:** raw F 20.534 → 26.655 meV; E′ 31.022 → 30.856 meV.
- **(iii) on E′:** 27.810 → 70.536 meV.
- **(iii) per dopant.**
  - raw F: Sr 9.203 → 88.705 and GA 43.487 → 15.155 meV;
  - E′: Sr 8.685 → 89.921 and GA 42.666 → 17.591 meV.
- **Share of the (iii) sum of squares carried by GA128:** 0.893 → 0.002.

**(ii) per pair (meV; error = model − DFT; class −1 / 0 / +1 at ±59.5 meV).**

| pair | DFT raw F | DFT E′ | ΔE_a zero-shot | ΔE_a fine-tuned | error raw, ZS → FT | error E′, ZS → FT | class DFT / ZS / FT |
|---|---|---|---|---|---|---|---|
| m30 GA | +94.8 | +94.2 | +72.5 | +67.9 | −22.2 → −26.9 | −21.6 → −26.3 | +1 / +1 / +1 |
| m30 Sr | −2.9 | +36.8 | −32.6 | −23.7 | −29.8 → −20.8 | −69.5 → −60.5 | 0 / 0 / 0 |
| m32 GA | −46.8 | −45.1 | −63.2 | −98.3 | −16.4 → −51.5 | −18.1 → −53.2 | 0 / −1 / −1 |
| m32 Sr | −25.5 | −15.8 | −1.3 | −3.5 | +24.2 → +22.0 | +14.5 → +12.3 | 0 / 0 / 0 |

- **Which pairs got worse.** |error| grows at m30 GA and m32 GA and shrinks at the two Sr pairs, on
  both bases.
- **Where the fine-tuned sum of squares sits** (computed from the JSON). On raw F, m32 GA carries
  62%. On E′, m30 Sr carries 50% and m32 GA 39%.
- **Item 5's conditional power figure does not apply.** Item 5 gave a raw pass probability of 0.95
  for a negative m30 Sr E′ error, under independent zero-mean normal E′ errors with SD 10 meV. The
  fine-tuned E′ errors lie far outside that premise: 4-pair RMS 42.8 meV, mean −31.9 meV. The m30
  Sr E′ error is negative (−60.5 meV), and raw F still fails, mainly through m32 GA (62% of the
  raw sum of squares).

**(iii) per site, m30 (meV; far-referenced; error = model − DFT).**

| site | DFT raw F | zero-shot | fine-tuned | error raw, ZS → FT | DFT E′ | error E′, ZS → FT | near sign DFT / ZS / FT |
|---|---|---|---|---|---|---|---|
| Sr136 (hinge) | +129.4 | +123.0 | +11.6 | −6.4 → −117.8 | +129.8 | −6.8 → −118.2 | + / + / + |
| Sr124 (flank) | +95.6 | +109.6 | −3.0 | +14.1 → −98.5 | +98.2 | +11.5 → −101.1 | + / + / **−** |
| Sr52 (mid) | +1.2 | −2.7 | −3.4 | −3.8 → −4.6 | +4.3 | −6.9 → −7.7 | — |
| GA128 (near) | +35.5 | −24.6 | +28.3 | −60.0 → −7.2 | +33.2 | −57.7 → −4.9 | + / **−** / + |
| GA212 (mid) | +42.3 | +29.0 | +22.1 | −13.3 → −20.2 | +46.5 | −17.5 → −24.4 | — |

The model E_b is the same on both bases; only the DFT reference changes.

**Number of items that improve (fine-tuned |error| < zero-shot |error|).**
- Test-frame force RMSE: 96 of 96 (per-frame ratio 5.1–6.5).
- Pairs: 5 of 9 on raw F and 6 of 9 on E′.
- Sites: 1 of 5 on either basis (GA128).
- Absolute E_a of the 16 test bands: 6 on raw F and 9 on E′.
- Every per-frame, per-pair and per-site value for both models is in `wp3_eval.json`
  (`reported.per_frame_force_rmse_eVA`, `adoption.b`, `reported.per_site`).

**Power (item 5, as recorded in the JSON).**
- The 4 pairs share one undoped band per host, and the 5 sites share one far site per dopant, so
  each test carries about 3 independent errors.
- No significance test is attempted. The smallest one-sided sign-flip p is 1/16 on 4 pairs and
  1/32 on 5 sites.
- Criterion 6 alone is not the gate; (b)–(e) are.

## 4. Adoption (a)–(c) (pre-registered; amendment m item 4)

**(a) Not met.** Criterion 6 gives No improvement.

**(b) Not met.** The test runs over the 9 test pairs on E′, with the DFT class also taken from E′.

| pair | DFT E′ (class) | ΔE_a zero-shot | ΔE_a fine-tuned | error E′, ZS → FT | class FT | DFT raw F (class) | error raw, ZS → FT |
|---|---|---|---|---|---|---|---|
| m30 GA | +94.2 (+1) | +72.5 | +67.9 | −21.6 → −26.3 | +1 | +94.8 (+1) | −22.2 → −26.9 |
| m30 Sr | +36.8 (0) | −32.6 | −23.7 | −69.5 → −60.5 | 0 | −2.9 (0) | −29.8 → −20.8 |
| m32 GA | −45.1 (0) | −63.2 | −98.3 | −18.1 → −53.2 | **−1** | −46.8 (0) | −16.4 → −51.5 |
| m32 Sr | −15.8 (0) | −1.3 | −3.5 | +14.5 → +12.3 | 0 | −25.5 (0) | +24.2 → +22.0 |
| m10 GA | +66.8 (+1) | +66.5 | +37.9 | −0.3 → −28.8 | **0** | +64.9 (+1) | +1.6 → −26.9 |
| m18 GA | −52.6 (0) | −30.1 | −38.4 | +22.5 → +14.2 | 0 | −52.9 (0) | +22.8 → +14.5 |
| m04 Sr | −34.3 (0) | −7.4 | −24.2 | +26.9 → +10.1 | 0 | −39.1 (0) | +31.7 → +14.9 |
| m14 Sr | −100.8 (−1) | −139.8 | −110.7 | −39.0 → −9.9 | −1 | −141.4 (−1) | +1.6 → +30.7 |
| m27 Sr | +2.9 (0) | +11.8 | +4.4 | +9.0 → +1.5 | 0 | +6.3 (0) | +5.6 → −1.9 |

The E′ columns decide (b). The two raw-F columns (`adoption.b.reported_raw_F_beside`) are reported
beside it, as item 4 requires, and decide nothing. The model ΔE_a and class are the same on both
bases, and so is the DFT class of every one of the 9 pairs.

- **Result.** RMS(model − DFT) is 30.856 meV for the fine-tuned model, against the 20 meV bound.
  Two pairs change class: m32 GA (DFT 0, model −1) and m10 GA (DFT +1, model 0).
- **Zero-shot on the same 9 pairs.** RMS 31.022 meV, with one class change (m32 GA).
- **Reported beside it (decides nothing).** On raw F the RMS is 26.655 meV fine-tuned and 20.534
  meV zero-shot. The class changes are the same (fine-tuned m32 GA and m10 GA; zero-shot m32 GA).
  The m30/m32 4-pair E′ RMS is 42.817 against 38.191 meV.
- **Item-1′ pairs.** All five are complete (none missing).

**(c) Not met.** One host (m30), 5 sites, raw F.
- **The 25 meV bound.** Errors are −117.8 (Sr136), −98.5 (Sr124), −4.6 (Sr52), −7.2 (GA128) and
  −20.2 meV (GA212). Two of the five exceed 25 meV; the largest |error| is 117.8 meV.
- **Near-site signs.** The Sr hinge sign agrees (+11.6 against +129.4 meV). The Sr flank sign
  **disagrees** (−3.0 against +95.6 meV). The GA near sign agrees (+28.3 against +35.5 meV).
- **Zero-shot comparison** (disclosed in item 4). Zero-shot failed (c) on GA128 alone (−60.0 meV,
  sign disagreeing).

**Power (item 5, as recorded) and the error budget (item 4, not quoted).**
- **(b) power.** Under independent zero-mean normal errors, a model with a true RMS of 30 (25) meV
  meets the RMS part of (b) with probability 0.09 (0.24) on 9 pairs. The figures are 0.22 (0.37) on
  4 pairs and 0.02 (0.13) on the 18 pairs of criterion 3.
- **(c) power.** A model with a true error SD of 15 meV fails "all 5 < 25 meV" with probability
  0.40, assuming zero-mean errors. The raw-basis Sr expectation of item 1c does not apply, because
  the basis is E′.
- **Error budget.** `scripts/39` computed the item-4 budget (`wp3_eval.json`
  `reported.error_budget`, `quoted` = false). It is **not quoted**, because item 4 quotes it only if
  the outcome is Validated.

## 5. Adoption (d): WP3b frozen-far-field relaxations (pre-registered; amendment m item 4) — fail

**(d) fails** (`wp3/wp3b_result.json`, written by `scripts/40 analyse`: verdict "fail", 6 reasons;
figure `fig_wp3_adoption_de`, panels a–c).
All six cells fail on the same condition, the RMS of the residual DFT force over the free atoms. No
other fail condition occurred.

- **Cells and free region.** Image 0 of undoped, GA and Sr for m30 and m32: 6 cells at fixed cell.
  - **The region.** There is one free region per host, the same in its three cells. It holds every
    atom within 6.0 Å (start geometry, minimum image) of any of three points: the vacancy site, the
    Sr atom of the Sr cell and the GA carbon of the GA cell.
  - **Molecules.** They are freed whole, by the distance of their C.
  - **The free sets.** 81, 83 and 81 atoms (25 inorganic and 7 molecules).
  - **Reproduction.** The driver's region step reproduced these sets as amendment m states them
    (`step7.log` 00:22:05: "matches PLAN … True"). Its `region_id` (c069486c…, a hash computed by
    `scripts/40 region`, not fixed in advance) is carried by all 12 relaxation records.
- **Relaxation and single point.** Each cell is relaxed with FIRE and the selected model in float64
  to fmax 0.01 eV/Å on the free atoms, with at most 10 000 steps. One `scripts/30` single point
  follows (`wp3b_<host>_<system>_img0`).
- **Pass/fail per cell.**
  - **Pass condition.** The residual DFT force over the free atoms (per-atom norms) must have RMS
    < 0.05 and max < 0.2 eV/Å.
  - **Fail conditions.**
    - the step cap is reached;
    - an I lies within 1.2 Å of the vacancy site;
    - the Sr atom or the GA carbon moves by 1.0 Å or more;
    - the organic topology check fails;
    - an SCF does not converge.

  (d) passes only if all six cells pass.

**Result per cell** (DFT forces as per-atom norms, eV/Å; the zero-shot comparator is the DFT force
at image 0, the zero-shot MACE minimum; ratio = zero-shot RMS / fine-tuned RMS).

| cell | free atoms | attempts | FIRE steps | free-atom residual, RMS / max | zero-shot image 0, RMS / max | ratio of RMS | nearest I to vacancy site (Å) | dopant displacement (Å) |
|---|---|---|---|---|---|---|---|---|
| m30 undoped | 81 | 2 | 428 | **0.0543** / 0.151 | 0.153 / 0.332 | 2.82 | 4.12 | — |
| m30 GA | 83 | 2 | 606 | **0.0579** / 0.148 | 0.142 / 0.270 | 2.45 | 4.03 | 0.19 |
| m30 Sr | 81 | 2 | 453 | **0.0551** / 0.154 | 0.160 / 0.337 | 2.90 | 4.12 | 0.03 |
| m32 undoped | 81 | 2 | 512 | **0.0526** / 0.121 | 0.157 / 0.360 | 2.98 | 4.03 | — |
| m32 GA | 83 | 1 | 646 | **0.0556** / 0.124 | 0.148 / 0.365 | 2.67 | 4.10 | 0.24 |
| m32 Sr | 81 | 1 | 441 | **0.0540** / 0.118 | 0.160 / 0.374 | 2.97 | 4.02 | 0.02 |

- **The failing statistic.** The free-atom RMS lies 5–16% above the 0.05 eV/Å bound in every cell
  (0.0526–0.0579). The max condition is met in every cell (0.118–0.154 against 0.2).
- **The other conditions.** All met in every cell.
  - Every relaxation converged (max force on the free atoms < 0.01 eV/Å) in 428–646 steps, far
    from the cap.
  - The nearest I to the vacancy site is 4.02–4.12 Å.
  - The GA carbon moved 0.19–0.24 Å and the Sr atom 0.02–0.03 Å.
  - The organic topology is unchanged.
  - Every SCF converged at the first submission: 14 iterations in each `wp3b_` cell, and 13–14
    over all 12 step-7 single points.
- **Against zero-shot** (the comparator; not a rule). The free-atom RMS is 2.5–3.0 times lower than
  at the zero-shot minimum. The values reproduce the amendment-m figures (0.142–0.160 / 0.270–0.374).
- **Component scale** (computed here from the JSON). Dividing by √3 turns a per-atom-norm RMS into a
  component RMS. The free-atom RMS of 0.053–0.058 eV/Å is then 0.030–0.033 eV/Å, about twice the
  component force RMSE of 0.0149 eV/Å on the 46 m30/m32 test frames (criterion 6 (i)). Those two
  numbers are not over the same atoms.
  - **Like for like.** The image-0 test frames of the same six cells have a per-frame component
    RMSE of 0.0136–0.0150 eV/Å (`wp3_eval.json` `reported.per_frame_force_rmse_eVA`, whole cell).
  - **The unconstrained minima.** Their whole-cell residuals below are 0.033–0.034 eV/Å on the
    component scale, 2.2–2.4 times those values.

**Reported, not gating.**

| cell | whole cell, RMS / max | zero-shot image 0, whole cell | surface (C distance), RMS / max (n) | surface (own distance), RMS / max (n) | relaxed − image 0: model ΔE / DFT ΔF, raw (meV) | model − DFT (meV) |
|---|---|---|---|---|---|---|
| m30 undoped | 0.128 / 0.382 | 0.152 / 0.354 | 0.0590 / 0.151 (47) | 0.0554 / 0.151 (32) | −244.5 / −224.1 | −20.4 |
| m30 GA | 0.129 / 0.372 | 0.149 / 0.369 | 0.0608 / 0.148 (47) | 0.0571 / 0.148 (32) | −251.8 / −202.3 | −49.4 |
| m30 Sr | 0.129 / 0.380 | 0.155 / 0.354 | 0.0589 / 0.154 (47) | 0.0531 / 0.154 (32) | −249.1 / −234.3 | −14.7 |
| m32 undoped | 0.136 / 0.455 | 0.156 / 0.385 | 0.0567 / 0.121 (47) | 0.0566 / 0.121 (34) | −386.8 / −368.5 | −18.3 |
| m32 GA | 0.136 / 0.458 | 0.153 / 0.380 | 0.0567 / 0.124 (47) | 0.0575 / 0.124 (34) | −435.6 / −361.4 | −74.2 |
| m32 Sr | 0.136 / 0.446 | 0.157 / 0.383 | 0.0559 / 0.118 (47) | 0.0540 / 0.118 (35) | −377.1 / −352.0 | −25.1 |

- **Whole cell.** The far atoms stay at their image-0 positions, so the whole-cell residual (RMS
  0.128–0.136) is dominated by the far field. It is not a WP3b statistic.
- **Surface sets.** Item 4 does not define "the free atoms within 1 Å of the 6 Å surface", so both
  readings are reported:
  - each molecule at its C distance (47 atoms);
  - each atom at its own distance (32–35 atoms).

  The max on either set equals the free-atom max in every cell.
- **Relaxation energies.** The DFT free energy falls in all six relaxations (202–369 meV). The model
  overestimates the fall in all six, by 15–74 meV.
  - **Basis.** The comparison is on raw F, as item 4 specifies (`scripts/40`).
  - **On E′.** The model's targets for vacancy cells were E′. The DFT Fermi level falls by 0.2–8.7
    meV in these relaxations (computed here from the QE outputs), so on E′ the overestimates are
    18–80 meV.
- **Dopant − undoped relaxation energy per host** (model / DFT, meV):
  - m30: GA −7.3 / +21.8 and Sr −4.6 / −10.2;
  - m32: GA −48.8 / +7.2 and Sr +9.6 / +16.5.

**The six unconstrained relaxations** (`wp3bu_`; reported; the whole-cell residual is criterion 5 as
pre-registered).

| cell | FIRE steps | whole cell, RMS / max | free atoms, RMS / max | minimum − image 0: model ΔE / DFT ΔF, raw (meV) | model − DFT (meV) | beyond 6 Å: max \|Δr\| (Å) / max FA rotation (°) |
|---|---|---|---|---|---|---|
| m30 undoped | 1288 | 0.0574 / 0.141 | 0.0589 / 0.141 | −1025.7 / −843.0 | −182.7 | 1.07 / 43.3 |
| m30 GA | 1223 | 0.0588 / 0.140 | 0.0629 / 0.140 | −982.6 / −766.7 | −215.9 | 1.10 / 42.6 |
| m30 Sr | 1497 | 0.0582 / 0.145 | 0.0604 / 0.145 | −1069.8 / −888.4 | −181.4 | 1.18 / 44.8 |
| m32 undoped | 2069 | 0.0569 / 0.133 | 0.0565 / 0.122 | −1293.8 / −1151.1 | −142.7 | 1.54 / 25.4 |
| m32 GA | 2021 | 0.0577 / 0.139 | 0.0582 / 0.124 | −1335.8 / −1155.0 | −180.9 | 1.53 / 24.7 |
| m32 Sr | 1933 | 0.0575 / 0.137 | 0.0581 / 0.129 | −1260.2 / −1117.0 | −143.2 | 1.53 / 23.8 |

- **Convergence.** All six converged, and none was flagged.
- **Criterion 5 as pre-registered.** It is not met by any cell. The whole-cell RMS is 0.057–0.059
  eV/Å against 0.05; the max condition (< 0.2) is met.
- **Energies.** The model overestimates the DFT lowering by 143–216 meV on raw F. The Fermi level
  falls by 17–28 meV, so on E′ the overestimates are 161–238 meV.
- **Basin measures.** None of the six stays within the amendment-c bounds (0.25 Å and 20°) beyond
  6 Å: the far field moves by up to 1.07–1.54 Å, and FA rotate by up to 23.8–44.8°. The WP2e DFT
  relaxation of m30 GA image 0 likewise reorganised the whole cell (FA rotations up to 42.9°,
  `WP2E_RESULT.md`).
- **Dopant − undoped** (model / DFT, meV):
  - m30: GA +43.1 / +76.3 and Sr −44.2 / −45.4;
  - m32: GA −42.1 / −3.9 and Sr +33.6 / +34.1.
- **Scope** (item 4, recorded in the JSON). A WP3b pass is not criterion 5. An S2 protocol that
  relaxes whole cells needs criterion 5 on all atoms of a fine-tuned full-cell minimum,
  pre-registered for that protocol. The `wp3bu_` values do not meet this requirement.

**The WP2e minimum** (m30 GA image 0; `wp3b_result.json` `wp2e_minimum`; reported).
- **E_model(DFT minimum) − E_model(image 0).** Fine-tuned −868.3 meV; DFT −977.3 meV; zero-shot
  +227.0 meV (zero-shot values reproduced).
- **Model force at the DFT minimum**, whole cell, per-atom norms. Fine-tuned: RMS 0.052, max 0.170
  eV/Å (component RMS 0.030). Zero-shot: 0.115, 0.260 and 0.067 eV/Å.
- **E_model(DFT minimum) − E_model(final `wp3bu_m30_GA_img0`).** +114.3 meV: on its own energy
  surface the fine-tuned model places its whole-cell minimum 114 meV below the DFT minimum.
- **The fine-tuned minimum at DFT level** (computed here; raw F). It lies 766.7 meV below image 0,
  which is 78% of the 977.3 meV of the DFT relaxation. At DFT level the order is therefore reversed:
  the fine-tuned minimum lies 210.6 meV above the DFT minimum. Both values use the same electronic
  settings (R point, 50/400 Ry, Gaussian smearing 0.005 Ry).

**Run record** (`wp3/step7/step7.log`, `step7_reruns.list`; times 2026-11-03 UTC).
- **Duration.** The driver ran from 00:22:02 to 07:33:01. The region and the zero-shot comparator
  passed at 00:22:05 and 00:22:15. `wp2e_minimum.json` was written and checked at 00:22:21.
- **Spot reclaim.** A spot termination notice was recorded at 00:26:23, for termination at
  00:31:21. It cut the 10 relaxations then running (all six `wp3bu_` and four `wp3b_`).
  - **The restart.** The operator restarted the node from the instance console and relaunched the
    driver with `wp3_relaunch.sh`. The driver restarted on the new boot (81c114d9) at 00:47:03.
  - **The classification.** At 00:47:06 the driver classified every first attempt as cause
    spot-reclaim. Its evidence was the notice recorded in boot 06740b92 and that boot's own system
    journal, which shows no system-level shutdown (10 lines in `step7_reruns.list`).
    - **Which boot.** In the list's wording, "that boot" is boot 06740b92. The classifier
      (`bin/cls.py` `boot_cause` in `step7_state.tar.gz`) reads the journal of the boot in which
      the attempt was launched.
  - **The relaunch.** At 00:47:07 (`step7_reruns.list`) it relaunched them with the identical
    command and `--rerun-cause spot-reclaim`, as attempt 2 of at most 3. Each second attempt
    recorded its start at 00:47:12.
  - **The partial outputs.** `scripts/40` moved each first attempt's partial output to
    `relax/discarded/<label>.attempt1`, unread. The only partial output was the FIRE log.
  - **The two cells that ran once.** `wp3b_m32_GA` and `wp3b_m32_Sr` had not started.
    - **Why.** The ten relaxations launched at 00:22:16–00:22:21 used 60 of the driver's 64-thread
      budget (6 threads each), and none had ended when the notice came. After a notice the driver
      also starts nothing for 1800 s within that boot.
    - **After the reboot.** The ten reruns took the budget again. The driver launched the two cells
      at 01:04:04 and 01:04:10 (`step7.log`), as soon as the `wp3b_m30_undoped` and `wp3b_m30_Sr`
      reruns ended. Their records give 01:04:08 and 01:04:14 as their start. Each ran once.
  - **What was not affected.** No MD run or QE job.
- **Wall times** (6 threads each). The `wp3b_` relaxations took 17–27 min and the `wp3bu_`
  relaxations 50–83 min.
- **QE.** The 12 single points ran in one chain from 06:08:40 to 07:32:55 (6.5–7.2 min wall each).
  All 12 had JOB DONE at the first submission, with no `.tryN` or `.gaveup` file.

**Readings stated** (runbook step 8 items 2–4; `wp3b_result.json` `notes`).
- **FIRE reading (item 2).** One FIRE run to fmax 0.01 eV/Å, with the 10 000-step cap bounding the
  whole relaxation. Item 4 names one fmax and one cap. The two restarted FIRE stages of protocol
  v2.1 (0.02 then 0.01 eV/Å) are not used.
- **Step-cap rule (item 2).** A cell fails if FIRE stops at the cap without max |F| < 0.01 eV/Å over
  the gated atoms (ASE's strict test). Converging on the last allowed step is not a fail. The rule
  was not exercised: the most steps taken were 646 (`wp3b_`) and 2069 (`wp3bu_`).
- **Surface sets (item 3).** Both readings are reported, as above.
- **Basin measures (item 3).**
  - `scripts/29 basin_dev` against image 0, over the atoms more than 6 Å (own distance) from all
    three fixed points (amendment c item 1).
  - The same measures over exactly the non-free atoms.
  - The bounds (0.25 Å, 20°) are reported, not gated.
- **QE resubmission times from file mtimes (item 4).** No `wp3b_` or `wp3bu_` job was resubmitted,
  so this reading was not exercised.

**Scope.** (d) cannot change the outcome, and it validates nothing for S2.

## 6. Adoption (e): MD stability (pre-registered; amendment m item 4 (e)) — fail

**(e) fails** (`wp3/wp3md_result.json`, written by `scripts/41 analyse --commit 4c1aaa8`, the note's
`scripts_commit`; figure `fig_wp3_adoption_de`, panels d–e). 10 runs pass, 2 fail and none is unevaluable. The rule is that (e) passes only if
all 12 pass.

- **Runs.** 12 runs: the 6 WP3b cells at 300 K and 450 K. Each is 5 ps of fixed-cell Langevin MD
  with the selected model: 1 fs steps, friction 0.01 fs⁻¹, a Maxwell–Boltzmann start and a crc32
  label seed.
- **Pass.** Every frame at 100 fs intervals (51 frames) must pass two sets of checks.
  - `scripts/35 sane()`:
    - composition unchanged;
    - the organic bonding pattern of the start;
    - no contact below 0.65 Å;
    - model max force below 15 eV/Å.
  - The inorganic checks of `scripts/41`:
    - no I–I distance below 3.0 Å;
    - in Sr cells, the Sr nearer its start than the start of any Pb;
    - in GA cells, the GA carbon nearer its start than the start of any other C or of any Cs.

| run | verdict | first failing frame (fs) | min I–I (Å) | min Pb–I (Å) | min Sr–I (Å) | max displacement, Sr / GA carbon (Å) | max C–H, diagnostic (Å) |
|---|---|---|---|---|---|---|---|
| m30 undoped 300 K | pass | — | 3.72 | 2.815 | — | — | 1.1914 |
| m30 undoped 450 K | **fail** | 900 | 3.48 | 2.770 | — | — | 1.2518 |
| m30 GA 300 K | pass | — | 3.71 | 2.794 | — | 0.89 | 1.1985 |
| m30 GA 450 K | pass | — | 3.41 | 2.784 | — | 1.16 | 1.2269 |
| m30 Sr 300 K | pass | — | 3.71 | 2.834 | 2.948 | 0.59 | 1.1955 |
| m30 Sr 450 K | pass | — | 3.56 | 2.753 | 2.904 | 0.63 | 1.2357 |
| m32 undoped 300 K | pass | — | 3.57 | 2.866 | — | — | 1.2161 |
| m32 undoped 450 K | **fail** | 3600 | 3.50 | 2.784 | — | — | 1.2615 |
| m32 GA 300 K | pass | — | 3.72 | 2.851 | — | 0.86 | 1.1959 |
| m32 GA 450 K | pass | — | 3.53 | 2.772 | — | 0.88 | 1.2329 |
| m32 Sr 300 K | pass | — | 3.72 | 2.839 | 2.882 | 0.54 | 1.2108 |
| m32 Sr 450 K | pass | — | 3.52 | 2.772 | 2.922 | 1.06 | 1.2261 |

The minimum distances and the displacements are over the 51 frames. The last column comes from the
post hoc diagnostic below.

- **The two failures.** m30 undoped at 450 K fails at t = 900 fs, and m32 undoped at 450 K at
  t = 3600 fs.
  - Each is the only failing frame of its 51, and each fails the organic bonding-pattern test alone.
  - There is no contact below 0.65 Å, no model force at or above 15 eV/Å and no I–I distance below
    3.0 Å.
- **The inorganic checks.** All 12 runs pass them.
  - The shortest I–I is 3.41 Å (m30 GA, 450 K).
  - The Sr atom and the GA carbon stay nearer their own start than any alternative start site.
- **Run record.** Every run completed its 5000 steps at the first attempt (8 threads; 1.9–2.9 h
  wall each). No rerun took place: the MD runs started only after the reclaim, between 01:07:51 and
  04:11:49.
- **Reported, not gating** (`reported_not_gating`, over all 12 runs).
  - Minimum distances: I–I 3.407 Å, Pb–I 2.753 Å and Sr–I 2.882 Å.
  - Largest displacements: Sr 1.063 Å and the GA carbon 1.162 Å.
  - A vacancy hop is not a failure; none is diagnosed here.

**Which bond failed** (post hoc, reported only; `scripts/43_wp3_md_bond_diagnostic.py` →
`wp3/step7/md_bond_diagnostic.json`, written after the verdict).
- **Check.** `scripts/43` restates the organic part of `sane()`. It reproduces the recorded
  `topology_ok` of all 612 frames.
- **The failing frames.** In both, one formamidinium methine H lies beyond the 1.25 Å cut-off from
  its own C:
  - H117 at 1.2518 Å from C116 (m30);
  - H17 at 1.2615 Å from C16 (m32).

  That C therefore counts no H, and that H no C or N, which breaks the pattern.
  - The H's next C or N is an N of the same molecule, at 2.17–2.18 Å.
  - Its nearest I is at 2.86 Å (m30) and 2.85 Å (m32).
  - The instantaneous whole-cell temperatures of the two frames are 458 and 493 K. The run means over
    t > 0 are 484 and 478 K (computed here from the per-frame `T_inst_K` of the MD records in
    `wp3/step7/wp3md_work.tar.gz`).
  - In both runs the frames 100 fs before and after pass. In them the same C–H is 1.14–1.16 Å.
- **C–H statistics** (frames t > 0, 50 per run; each H assigned to its nearest C or N).
  - At 450 K: 1.0990 ± 0.0383 Å (n = 5600, max 1.2615 Å); 2 of the 5600 reach 1.25 Å.
  - At 300 K: 1.0973 ± 0.0311 Å (n = 5600, max 1.2161 Å); none reaches 1.25 Å.
  - The largest N–H is 1.209 Å (450 K).
- **Sampled temperature** (frames t > 0). The pooled and per-element values are from
  `md_bond_diagnostic.json` `sampled_temperature_K`. The per-run means were computed here from the
  per-frame `T_inst_K` of the MD records in `wp3md_work.tar.gz`.
  - **The whole cell.** The MD ran warmer than its set points: the instantaneous temperature
    averages 323.1 K and 482.2 K, and every run lies above its set point (run means 318.8–327.0 K
    and 477.8–487.8 K).
  - **By element.** The excess sits in the organic atoms. Their kinetic temperature is 339, 334
    and 331 K (H, C, N) at 300 K, and 500, 495 and 501 K at 450 K. Pb and I sit at the set point:
    300 and 297 K, and 446 and 450 K.
  - **Cause.** Not investigated. The protocol (ASE Langevin, 1 fs, friction 0.01 fs⁻¹) is the
    pre-registered one, the same as in `scripts/35`.
- **The verdict stands.** Item 4 requires every frame to pass `sane()` with its pre-registered
  cut-offs, and its Outcomes are exhaustive and fail-closed. Item 4 allows a rerun only after an
  interruption, never a change of settings.

**Errata to state** (runbook step 8 item 6).
- The shortest I–I in the 106 band and binding training frames is 4.0346 Å (m06_GA_img4), not 4.04 Å
  as amendment m says (`wp3md_result.json` `reported_not_gating`).
- "A–A ≥ 6.28 Å" does not hold for C/Cs. Check 3 is unaffected.
- **Added here** (geometry only, computed from `wp3/dataset/train.xyz` with minimum-image distances).
  - **What amendment m says.** It states the 4.04 Å for "any training DFT frame".
  - **Context.** It was written before any WP3 DFT single point existed. `scripts/41`, committed
    before training, restricts the value to the 106 band and binding frames.
  - **The erratum.** Read literally, the statement is wrong for the training set as built. The WP3
    MD frames reach I–I 3.520 Å (m20_GA_md450), and the rattle frames 3.848 Å
    (m15_undoped_rat10f). So the shortest I–I over all 201 training frames is 3.520 Å.
  - **Against the MD runs.** Every MD minimum I–I above (3.41–3.72 Å) lies below the 4.03 Å of the
    106 frames. Four 450 K runs also go below 3.520 Å: m30 GA (3.407 Å), m30 undoped (3.483 Å),
    m32 undoped (3.500 Å) and m32 Sr (3.516 Å).

## 7. Reported, not gated

**Absolute E_a error of the 16 test bands** (meV; model − DFT; E_a = maximum over images 2–4 of
E_i − E_0).

| band | DFT E_a raw / E′ | raw: ZS → FT | E′: ZS → FT |
|---|---|---|---|
| m30 undoped | 211.2 / 190.4 | +8.9 → −34.4 | +29.7 → −13.6 |
| m30 GA | 306.0 / 284.6 | −13.4 → −61.3 | +8.0 → −39.9 |
| m30 Sr | 208.3 / 227.2 | −20.9 → −55.2 | −39.8 → −74.1 |
| m32 undoped | 177.2 / 156.8 | −2.0 → −13.0 | +18.4 → +7.4 |
| m32 GA | 130.4 / 111.7 | −18.3 → −64.5 | +0.4 → −45.8 |
| m32 Sr | 151.7 / 141.0 | +22.3 → +9.0 | +33.0 → +19.7 |
| m10 undoped | 44.5 / 24.9 | +41.4 → +28.7 | +61.0 → +48.3 |
| m10 GA | 109.4 / 91.7 | +43.1 → +1.8 | +60.8 → +19.5 |
| m18 undoped | 199.2 / 181.0 | −2.1 → −25.4 | +16.1 → −7.2 |
| m18 GA | 146.3 / 128.4 | +20.7 → −10.9 | +38.6 → +7.0 |
| m04 undoped | 135.4 / 114.6 | +4.0 → −2.7 | +24.8 → +18.1 |
| m04 Sr | 96.3 / 80.3 | +35.7 → +12.1 | +51.7 → +28.1 |
| m14 undoped | 237.1 / 213.9 | +3.0 → −57.6 | +26.2 → −34.4 |
| m14 Sr | 95.8 / 113.2 | +4.6 → −26.9 | −12.8 → −44.3 |
| m27 undoped | 269.4 / 266.4 | −1.6 → −28.0 | +1.4 → −25.0 |
| m27 Sr | 275.7 / 269.3 | +4.0 → −29.9 | +10.4 → −23.5 |

- **Summary** (computed from the JSON).
  - raw F: mean (RMS) +8.1 (20.7) zero-shot against −22.4 (35.2) fine-tuned;
  - E′: +20.5 (32.9) against −10.0 (33.6).
- **Change on fine-tuning.** The fine-tuned − zero-shot change is negative in all 16 bands (mean
  −30.5 meV), and it is the same on both bases.
- **Item-5 coverage.** Item 5 does not name a basis for its +59 meV trigger. `scripts/39`, committed
  in eb92910 before any item-1′ DFT existed, reads it on raw F, the basis of the item-5 +59 to
  +117 meV figures. On that reading no item-1′ band triggers it (largest zero-shot error +43.1 meV,
  m10 GA), so there is no unseen-host evidence on the low-barrier overestimate (coverage point 1).
  On E′, m10 undoped (+61.0) and m10 GA (+60.8 meV) exceed +59 meV. Their fine-tuned changes
  (−12.7 and −41.3 meV) are reported beside it and gate nothing.
- **Item-5 coverage note, as recorded.** Criterion 6 and (b) test paired ΔE_a, in which a host-wide
  overestimate largely cancels. (iii) and (c) rest mainly on one GA site, whose far reference has a
  MACE-level SD of 28 meV and no DFT noise floor.
  - **How it applies here** (computed from the JSON). The GA-site statement describes the
    zero-shot comparator (GA128 share of the (iii) sum of squares 0.893; 0.002 for the fine-tuned
    model). For the fine-tuned model, (iii) and (c) are decided by the two first-shell Sr sites.
    They carry about 98% of the (iii) sum of squares, and their errors (−117.8 and −98.5 meV) are
    4.7 and 3.9 times the 25 meV bound. They share the Pb64 far reference with Sr52, whose error
    is −4.6 meV.

**m30 (img3 − img0)(Sr − undoped)** (meV).
- DFT: +40.154 at q = +1, +36.835 on E′ and −2.865 at q = 0 (stated in amendment m: +40.2, +36.8,
  −2.9).
- Zero-shot −32.648; fine-tuned −23.657.

The fine-tuned value moves 9.0 meV towards DFT but stays below all three DFT values.

**Item-5 quantities (labels as in the JSON).**
- **m21: "(validation): selected the checkpoint, so not independent; its GA and Sr DFT maxima are
  unbracketed".**
  - Absolute E_a error, raw F: undoped +59.7 → +31.8; GA† +59.7 → +36.9; Sr† +89.4 → +75.3 meV.
    On E′: +80.7 → +52.8, +75.8 → +53.0 and +101.5 → +87.4 meV.
  - Paired ΔE_a error, raw F: GA −0.1 → +5.1; Sr +29.7 → +43.5 meV. On E′: −5.0 → +0.2 and
    +20.8 → +34.6 meV.
  - Far-referenced E_b error, raw F:
    - Sr136 +23.8 → −93.0; Sr124 +25.9 → −87.8; Sr0 −43.0 → −42.0;
    - GA128 +21.5 → +28.5; GA104 +26.1 → +38.0 meV;
    - RMS 29.1 → 63.8 meV (E′ 24.3 → 61.4).
  - The fine-tuned far-referenced E_b at the Sr hinge and flank is +43.8 and +43.9 meV, against
    DFT +136.7 and +131.7 meV.
- **Training hosts m05, m06, m08, m12, m15 and m20: "training host: fit quality".**
  - **18 bands, absolute E_a error.** raw F: mean (RMS) +49.4 (66.1) → −15.1 (36.4) meV; E′: +59.1
    (76.9) → −5.4 (37.4) meV. The change is negative in all 18 bands (−11.7 to −130.1 meV). This
    includes m08 and m12, where zero-shot already agreed with DFT within 35 meV
    (`WP2B_RESULT.md` §4); there the fine-tuned errors are −5.3 to −72.9 meV.
  - **12 pairs, ΔE_a error RMS.** raw F 34.6 → 27.4 meV; E′ 44.3 → 36.3 meV. On E′, m06 GA changes
    class for the fine-tuned model only, and m15 Sr for both.
  - **m05 sites, far-referenced E_b error, raw F.**
    - Sr136 +21.7 → −64.4; Sr124 +36.1 → −64.5; Sr48 +2.8 → +9.3;
    - GA128 +27.1 → −11.7; GA40 +13.8 → +10.3 meV;
    - RMS 23.3 → 41.6 meV (E′ 17.8 → 50.5).
  - The fine-tuned m05 Sr hinge E_b is +41.3 meV, against DFT +105.7 (raw) and +122.0 meV (E′, the
    training basis).

## 8. Interpretation (not pre-registered; nothing here is tested unless a check is stated)

**What is measured.**
- **Forces improved everywhere.** The force RMSE fell 5.8-fold on the 46 decisive frames, and fell
  on every one of the 96 test frames.
- **The energy differences S1 tests did not improve.** Over the 4 decisive pairs, the paired ΔE_a
  RMS rose on both bases. The m30 E_b RMS rose from 28.4 to 69.4 meV.
- **The Sr–vacancy near-shell E_b collapsed at every host where it was measured:**
  - m05 (training): +41.3 against DFT +105.7;
  - m21 (validation): +43.8 against +136.7;
  - m30 (test): +11.6 against +129.4 meV.
- **The model also fits its own training energies poorly.** Its training-band absolute E_a errors
  have an RMS of 36–37 meV, and its m05 first-shell Sr E_b errors are −64 and −65 meV (raw) and −81
  and −77 meV (E′). These are
  energy differences between energy-labelled training frames, so the failure is at least partly
  one of fit, not only of transfer to new hosts.
- **The absolute E_a changes in one direction.** The fine-tuned model lowered the absolute E_a in
  all 37 bands evaluated (18 training, 3 m21, 16 test), on hosts with and without the zero-shot
  overestimate.

**Candidate reasons, each checked against the data where possible.**

1. **The effective energy weight on near-equilibrium frames was small. This is the most consistent
   with the data; it is not tested.**
   - **Where L_E came from.** The w_E rule of item 2 balances the energy and force terms at the
     start of training. L_E included the 24 vacancy-free WP3 frames, whose residuals (DFT target −
     zero-shot) average +3.7 eV (md300) and +5.6 eV (md450) per cell
     (`dataset_meta.json` diagnostics; residual RMS 3368 meV).
   - **Computed from those diagnostics with N = 233.** These 24 frames carry 99.7% of L_E. The 106
     band and binding frames (residual RMS 82.2 meV) carry 0.3%. This reproduces L_E to 0.01%.
   - **Consequence for w_E.** w_E came out at 7.0 × 10⁴, against the 6.7 × 10⁶ that item 2 gave as
     indicative for the 106 frames alone. L_E rose about 200-fold (1.25 × 10⁻⁷ → 2.50 × 10⁻⁵
     (eV/atom)²), and L_F rose 2.1-fold (8.36 × 10⁻³ → 1.76 × 10⁻² (eV/Å)²); the net factor is
     about 95. The 106 frames enter both L_F values, so the rise in L_F comes from the 95 WP3
     frames, whose zero-shot force residuals are therefore larger on average (inferred from the two
     values, not measured per frame here).
   - **What that weight means per frame** (illustration, not a measurement). At w_E = 7 × 10⁴, a
     30 meV per-cell energy error in a 233-atom frame adds about 5% of the loss of a 15 meV/Å force
     error. At 6.7 × 10⁶ it would add about 4.9 times that loss.
   - **Measured on m21 at Initial.** The energy term is about 1.2% of the loss: the reported loss
     equals 0.50–0.52 × [w_E·RMSE_E/atom² + w_F·RMSE_F²] in all 101 records.
   - **Measured on m21 per-cell scatter.** The frame-to-frame scatter of the per-cell energy error
     fell only from 60.0 to 52.7 meV (SD over 31 frames: Initial from the results file and the
     `scripts/33` mean residual; epoch 82 from the model note). RMSE_F fell 5.1-fold.
   - **Consistency.** All of this fits a fit driven by the forces and by the multi-eV offsets of
     the off-equilibrium frames, with tens-of-meV differences between near-equilibrium frames
     weakly constrained.
   - **What would test it.** The same recipe with w_E computed from the band and binding frames
     only, or with the vacancy-free WP3 frames at energy weight 0, compared on the training hosts
     and m21. A new model can no longer be validated on the used test hosts.
2. **Energy weight 0 on the 71 WP3 vacancy frames (the q = +1 (b) failure). Not supported as the
   cause of a weaker energy fit.**
   - **Counterfactual** (computed from the same diagnostics). Had (b) passed, those frames would
     have entered L_E with residual RMS 2987–3246 meV, and w_E would have been about 2.0 × 10⁴, not
     7.0 × 10⁴.
   - **What the failure did remove.** The energy labels of off-equilibrium vacancy cells, which
     criterion 6 does not probe directly.
   - **Operator's reading of the failure** (not tested; no decision rests on it beyond item 1c):
     in the 450 K MD frame the vacancy electron may occupy a state other than the delocalised band
     state.
3. **The E′ targets. Not supported as the cause of the E_b collapse.**
   - **E_b.** At the six first-shell Sr sites of m05, m21 and m30, the DFT far-referenced E_b
     differs between E′ and raw F by at most 16.3 meV (m05 hinge; 0.4 meV at m30 hinge). The
     fine-tuned errors are 64–118 meV.
   - **ΔE_a.** It worsened on both bases, so the basis does not account for it either.
   - **One mechanism the data cannot exclude.** The vacancy-cell energies are E′, but their forces
     are the q = 0 forces. The mismatch (≈ ∇E_F) is 6.5–9.8 meV/Å component RMS on the nine m30
     WP2d frames (item 1c). That is 43–66% of the fine-tuned force RMSE of 14.9 meV/Å on the 46
     m30/m32 frames, so at the fine-tuned accuracy the two targets are no longer mutually consistent at the level
     the model resolves.
   - **What would test it.** The recipe on raw F, or the force residual at the Pb pair flanking the
     vacancy.
4. **The class constants c_D. Excluded.** They cancel in every within-band ΔE_a and far-referenced
   E_b (item 1c).
5. **Only 130 energy-labelled frames. Partly.**
   - **What the labels cover.** The energy information on dopant–vacancy binding comes from one
     host. The only dopant cells without a vacancy are the 7 m05 binding frames.
   - **Why scarcity is not the whole story.** The model does not fit those m05 quartets either: its
     m05 E′ Sr E_b errors are −80.7 and −77.1 meV, against zero-shot +5.4 and +23.5 meV. Scarcity
     alone would predict a good fit on m05 and poor transfer.
6. **A checkpoint chosen on a force-dominated m21 loss. Checked; not supported on whole-cell
   energies.**
   - **What the selection picked.** Epoch 82 has the lowest m21 RMSE_E_per_atom of the 100 epochs
     (0.2520; next 0.2764 at epoch 81) as well as the lowest loss. Its energy share of the m21 loss
     is about 15%; across epochs the share ranges from 15% to 99%.
   - **Why this does not settle it.** RMSE_E_per_atom is a whole-cell measure dominated by the
     offset and the scatter, not by E_b or ΔE_a. Whether another kept checkpoint has better m21
     E_b is unknown.
   - **What would test it** (a diagnostic only): evaluating the 20 kept checkpoints on the m21
     quartets. They are kept off-repository.
   - **Post hoc, 2026-11-03.** This diagnostic has since been run as D1 (`WP3_DIAGNOSTICS.md`).
     - **The condition.** No kept checkpoint meets the m21 E_b condition, nor the same condition on the two
       first-shell Sr sites alone. The five-site rule cannot discriminate, because m21 Sr_mid fails at every
       checkpoint and at zero-shot.
     - **Better m21 E_b.** Several kept checkpoints have a better m21 E_b than the selected epoch 82 (RMS
       31.3 meV at epoch 7, against 63.8 meV), but none meets the condition.
7. **A systematic lowering of the absolute barriers. Observed; its origin is not established.**
   - **What is observed.** E_a fell in 37 of 37 bands. Zero-shot overestimated the low-barrier
     training hosts by up to +117 meV, so a lowering is what those targets ask for. But the
     lowering also appears on training hosts m08 and m12, where zero-shot already agreed with DFT
     within 35 meV, and on the test hosts.
   - **What follows.** The lowering is not fitted band by band. Where it differs between the two
     bands of a pair, it enters ΔE_a: at m32 it is −11.0 meV for undoped and −46.2 meV for GA,
     which is the −35.1 meV change of the m32 GA pair error.
   - **What would test it.** A line integral of the model − DFT force residual along the band
     images, which would show whether the lowering follows from the force residuals.
   - **Post hoc, 2026-11-03.** This was run as D2 (`WP3_DIAGNOSTICS.md`). It cannot be read: the path
     0 → i* through the images with DFT frames (0, 2, 3; 0, 2 in two bands) does not close to 20 meV in any
     band.
8. **The local model against the band term. Not separable with these data.** On E′ the band term is
   removed frame by frame, so a local model can in principle represent the targets. Yet the m30 Sr
   E′ pair error stays large (−69.5 → −60.5 meV).

**The Sr hinge E_b and the WP1 headline.**
- **What the headline rests on.** The WP1 headline is that Sr repels the vacancy, with near − far
  +141.7 meV. It is a zero-shot MACE result. WP2c confirmed the repulsion at DFT on the MACE
  geometries: +95.6 to +136.7 meV at the six first-shell sites. Zero-shot MACE reproduced the m30
  hinge value to −6.4 meV, but it still fails criterion 4 (6 of 15 sites above 25 meV; first-shell
  Sr overestimated by +19.2 meV on average, WP2c).
- **What the fine-tuned model gives.**
  - m30 hinge +11.6 and flank −3.0 meV;
  - m21 +43.8 and +43.9 meV;
  - the training host m05 +41.3 and +51.6 meV.

  It therefore would not reproduce the DFT-confirmed repulsion, and it reverses the sign at one
  test site.
- **What follows for WP1 and WP2c.** Neither rests on the fine-tuned model, and their conclusions
  are unchanged by WP3.
- **What follows for adoption.** A lower force RMSE alone would have been a misleading reason to
  adopt this model. Item 5 had anticipated this ("Force RMSE is almost certain to fall"; "criterion
  6 alone is therefore not the gate").
- **The GA near site.** The one site that improved is GA128 (−60.0 → −7.2 meV, sign now agreeing).
  It is one site whose far reference has a MACE-level SD of 28 meV. At m21 the GA site errors
  worsened (+21.5 → +28.5 and +26.1 → +38.0 meV).

**Adoption (d) and (e).**
- **(d) misses on one statistic, by 5–16%.**
  - **What is within reach.** The free-atom max is well inside its bound. The RMS is 2.5–3.0 times
    lower than at the zero-shot minimum.
  - **The force error at the model's own minima.** It is about twice the error on the test frames.
    Over the whole cell of the same six cells, the component RMS is 0.033–0.034 eV/Å at the
    unconstrained minima, against 0.0136–0.0150 eV/Å on the image-0 test frames (2.2–2.4 times).
    On these six m30/m32 cells, the test frames, which are zero-shot geometries, therefore
    understate the force error at the model's own minima.
  - **Relaxation energies.** The model overestimates the DFT relaxation energy in all 12
    relaxations. On raw F, as item 4 specifies, the overestimate is 15–74 meV with the far field
    frozen and 143–216 meV without. On E′, the model's training basis for vacancy cells, it is
    18–80 and 161–238 meV.
  - **Not tested.** Whether another recipe would pass.
- **The WP2e cell.** For this one cell (m30 GA image 0), fine-tuning corrected the sign of
  E(WP2e DFT minimum) − E(image 0).
  - **Zero-shot.** Single points on the WP2e path (amendment m, Information state and item 4;
    reproduced in step 7) place the DFT minimum 227 meV above image 0, which is zero-shot MACE's own
    relaxed minimum.
  - **Fine-tuned.** The fine-tuned model is not at a minimum at image 0: it relaxes 983 meV from
    there. It places the DFT minimum 868 meV below image 0 (DFT 977 meV, raw F).
  - **Its own minimum.** At DFT level it recovers 78% of the DFT relaxation energy, but still lies
    211 meV above the DFT minimum.

  This is one cell and a reported quantity; the model is not adopted.
- **(e) fails by a cut-off crossing, not by a dissociation or a proton transfer.**
  - **The geometry.** The H stays nearest its own C.
    - Its next C or N is an N of the same molecule, 2.17 Å (m30) and 2.18 Å (m32) away.
    - Its nearest I is 2.86 and 2.85 Å away; an H–I bond would be about 1.6 Å.
    - In the frames 100 fs before and after, the same C–H is 1.14–1.16 Å, and both pass.
  - **The thermal scaling.** The C–H SD grows by a factor of 1.23 from 300 to 450 K. Classical
    vibration gives √(450/300) = 1.22 at the set points, and 1.21 at the sampled H kinetic
    temperatures (339 and 500 K, §6).
  - **Illustration (not a measurement).** Take a classical harmonic C–H stretch of 3000–3100 cm⁻¹
    (reduced mass 0.93 u).
    - **At the set points.** Its SD is 0.034–0.035 Å at 450 K and 0.028–0.029 Å at 300 K. The
      model's values (0.038 and 0.031 Å) are 7–12% larger, as for a stretch near 2800 cm⁻¹.
    - **At the sampled H kinetic temperatures** (500 and 339 K). Its SD is 0.036–0.037 and
      0.030–0.031 Å, close to the model's values.
    - **So.** The illustration cannot separate a softer model C–H from the warmer sampling (§6).
      Differences between molecules add little: the within-bond SDs (ddof 1, as the pooled values)
      are 0.0382 and 0.0308 Å (computed here from the trajectories in `wp3md_work.tar.gz`).
  - **The tail.** At 450 K the distribution is skewed towards long bonds.
    - **Long side.** 49 of the 5600 samples lie at or above 1.20 Å, against 23.5 for a normal
      distribution with the same mean and SD.
    - **Short side.** 10 lie below 1.00 Å, against 27.4 (counts from the histogram source data of
      the figure, panel e).
    - **The two crossings.** They belong to this tail: the cut-off lies 3.9 SD above the mean, and
      a normal distribution gives 0.23 crossings.
    - **Reading.** The skew is the direction an anharmonic bond would give.
  - **What is not known.** Whether DFT MD would cross the cut-off as often. No DFT MD exists here.
  - **The training frames.** The frame generation with zero-shot MACE-MP-0 also lost one 450 K
    frame to the same test (m06_Sr_md450, §2 item 2). Its cause was not diagnosed.
  - **The cut-off is not revised.** It is part of `scripts/35 sane()`, which item 4 pre-registers as
    the (e) test, and item 4's Outcomes are fail-closed.

## 9. Deviations and disclosures

Times are UTC. None of these is a departure that changes how a verdict is decided. Items 3, 4, 6
and 22 shaped the training data or the loss weights: item 3 by a disclosed run-control choice,
items 4, 6 and 22 by the pre-registered rules. Their effect on the model is not tested (§8).

1. **Node loss during step 2.**
   - **What was cut.** The node stopped hard at 2026-10-28 21:02 (last journal entry 21:02:53),
     eight minutes after the first step-2 start (20:54), with no shutdown sequence. The operator
     read this as a spot reclaim; no termination notice was recorded. Step 2 was relaunched at
     21:10.
   - **Recovery.** `scripts/35` resumed and skipped the labels already recorded. The in-progress MD
     of the first md300 frame of each host was restarted from its label seed; 12 rattle frames had
     already been written. No frame was rejected or regenerated because of the node loss.
2. **Node checkout moves.**
   - **During step 2.** The checkout moved from 0b79b9c to c391d61 by a fast-forward. That diff
     touches only the runbook, the node drivers, the input-check helper `rb_verify_inputs.py` (which
     now also checks the WP3 inputs) and the review notes, not scripts 29–41. `step2.log` records
     0b79b9c and `step34.log` records c391d61.
   - **Mixed versions within step 2.** The running step-2 driver kept its pre-move code: its
     installed copy was replaced by a new file, which the running process does not read. Its 2d
     input check called the post-move `rb_verify_inputs.py`, which also checked the 95 WP3 inputs:
     ALL INPUT CHECKS PASS (50 item-1′, 8 `chk_`, 95 WP3; operator's log, 2026-10-29 02:50:44).
   - **Before step 7.** After the archive check of item 10, the checkout was fast-forwarded from
     c391d61 to C6 = 5cf6c5f, clean (runbook A.4.3).
3. **`scripts/35` ran as six per-host processes** (runbook, "Node drivers").
   - **Equivalence.** The rattle frames are bitwise those of one all-host process. The MD frames are
     statistically equivalent, not bitwise, because thread-order rounding differs.
   - **Literal command.** The item-1d all-host command was then run on the merged directory. It
     added nothing: "95 written, 1 rejected", with the report unchanged.
4. **One frame rejected.** m06_Sr_md450 was rejected by `scripts/35` and not regenerated, so
   W = 95.
5. **No item-1′ re-run or resubmission** (runbook step 8 item 8). No QE job of the step-2
   campaigns (wp3, wp3x and wp3chk: the WP3 frames, item 1′ and the q = +1 checks) was resubmitted
   (`step34.log`: "item-1' re-runs and resubmissions: 0"; no `.tryN` or `.gaveup` file in
   `wp3/raw`, `wp3/test_extra/raw` or `wp3/chk/raw`). Step 7 is reported in §5.
6. **The q = +1 check (b) failed for undoped** (§2 item 4). The 71 WP3 vacancy frames therefore
   carry energy weight 0, as item 1c prescribes.
7. **Driver rules that did not arise: D1–D5** (`scripts/wp3_runbook/review_2026-10-28/PATCH_NOTES.md`).
   These are the drivers' readings of items 1′, 1e and 2 where the runbook or the amendment left a
   choice. None of them was exercised.
   - **D1.** An interrupted item-1′ re-run is resubmitted once, following amendment m over the
     runbook's earlier wording. No item-1′ re-run occurred.
   - **D2.** The training driver stops for a human at any second abnormal end, even with a
     different cause, which is stricter than item 2's "same cause twice". The only interruption was
     run1's node loss, which is not an abnormal end.
   - **D3.** A run with no Initial record by the 2-epoch timing at T plus 30 min is killed and
     recorded as `[abnormal end]`. Both runs had their Initial record at the start check, 30 s
     after starting.
   - **D4.** `scripts/33` is re-run only if an earlier run was cut short. It ran once (2026-10-29
     20:02:53 to 20:08:30); the relaunch re-used its dataset.
   - **D5.** Equal whole-second timing wall times go to the fewest threads. T = 32 won by a clear
     margin.
8. **The m21 host-wide offset.** It is the mean of E_model − REF_energy over the 31 m21 frames,
   which is the note tool's reading of item 2 "Reporting".
9. **Network interruption.** At about 19:45–19:56 on 2026-10-29 the connection between the laptop
   and the node dropped. The node did not reboot and no job was affected.
10. **Archive check before step 7** (runbook A.4.3). The node-side archive copies are kept
    off-repository until this result is final. Before step 7, the 407 node-checkout copies (frames,
    raw, test_extra, chk and dataset) were byte-identical to C6, and so were the 5 files of the
    node's training copy of the dataset (`ds`).
11. **Training interruption and an operator slip.**
    - **The event.** run1 was lost shortly after 2026-10-30 04:51:30, the last write to its
      results file. It was a hard stop with no shutdown sequence, read by the operator as a spot
      reclaim; no termination notice was recorded (only the step-7 driver polls for one). The
      operator's log dates the stop at 04:50:11 from the system journal, 79 s before that write;
      the journal's last entry need not mark the stop. The driver classified the loss as
      `[node loss]` from the boot time. Item 2 treats both causes the same way: the run is
      discarded, and the identical command runs from scratch. The commit message of 4c1aaa8 calls it
      "a spot reclaim at epoch 95", repeating the operator's reading; `restarts.txt` and the model
      note say "node loss". These describe the same event.
    - **The slip.** Before the relaunch, the operator printed the last three lines of run1's
      results file and counted its evaluation records, to see how far run1 had got. This showed:
      - two training-batch losses at epoch 95 (7.31 and 13.29);
      - 96 evaluation records (Initial and epochs 0–94).

      The operator also listed the last three names of run1's checkpoint directory
      (`ls run1/checkpoints | tail -3`: `epoch-81`, `epoch-82`, `epoch-8`, in the locale's collation
      order, in which any epoch from 83 to 99 would have been listed after `epoch-82`). Because a
      checkpoint is written only when the m21 loss improves (item 2), this listing showed that run1's
      last m21 improvement was at epoch 82, with no value; it is part of the slip. The operator's log
      first recorded this as "checkpoints up to epoch 94", which conflated the checkpoints with the
      evaluation records; the listing above is what was seen.
      No m21 validation metric of run1 was read.
    - **Effect.** This departs from item 2's "discarded unread". run1 is not used. run2 ran the
      identical command, and its checkpoint was selected by mace-torch from run2's own records.
12. **Path redaction of `wp3_eval.json`.**
    - **What changed.** As written by `scripts/39`, the file held two absolute local paths, in
      `arms.zeroshot.model_file` and `arms.finetuned.model_file`. Only those two strings were
      replaced, with `~/.cache/mace/…` and `<MAC_STAGE>/run/wp3.model`. A JSON comparison shows no
      other field differs.
    - **The original** (sha256 88e7db00…0f451d4c) is kept off-repository.
    - **The console log** `step6_scripts39.log` was committed with the local path prefixes removed.
13. **Session gap.** No operator action took place between 2026-10-30 15:06 and 2026-11-02 23:57.
    Training had finished at 15:05 and the node stopped itself at 16:05. The gap only delayed 5b
    and step 6. The model was copied with its sha256 checked; the checkpoints were copied with an
    empty `rsync -c` dry run.
14. **Commits between the training checkout (c391d61) and CNOTE.**
    - **The commits.**
      - 498062d: step-7 driver, note tool and runbook appendix.
      - 1687267: the step-3 archive.
      - b9a6a8d: the S2 builders.
      - 4c1aaa8: the run2 archive.
    - **What they touch.** `git diff c391d61 c1d0ace -- scripts` lists only `scripts/42_s2_builders.py`
      and the `scripts/wp3_runbook/` tools. b9a6a8d touches only
      `results/objective2/s2/S2_BUILDERS_DESIGN.md` and `scripts/42_s2_builders.py`, so it changes
      no WP3 input.
    - **Why b9a6a8d came before CNOTE.** Between CNOTE and C6 only `results/` and a `scripts/39` fix
      may change.
15. **Step-7 driver warnings** (2026-11-03 00:22:02, at the driver's start; operator's log). There
    were two.
    - **`step6_scripts39.log`.** Between CNOTE and C6 it changed as well as `wp3_eval.json`. It is
      the step-6 console log, committed with C6. Files under `results/` may change in that window;
      it is listed here as the driver requires.
    - **Keep-alive file present.** This is the procedure: the operator kept the keep-alive file
      while the node waited for 5b and step 6 (runbook A.4.1), and removed it once the driver had
      logged "preconditions PASS" (A.4.4), at 00:22:03.
16. **Order of the float64 assertions** (runbook step 8 item 1). Item 3 asks both for float64 to be
    asserted for both arms before any frame and for the fine-tuned model not to be loaded before the
    gate passes. Both cannot hold. `scripts/39` kept the gate order:
    - the zero-shot arm is asserted before its first (gate) frame;
    - the fine-tuned arm is asserted when it is built after the gate, before its first frame.
17. **`scripts/33` fail-closed rules** (runbook step 8 item 5; `dataset_meta.json` `script_rules`).
    - **The rules.**
      - stops on a pending q = +1 job, or on a pattern label whose retry is pending;
      - (b) fails if both the md450 and the md300 frame of m05 X are rejected;
      - exactly the 96 item-1d labels (1500 steps, 15 eV/Å);
      - charge neutrality of every dataset output, and the electron count of every `chk_` output;
      - frame = archived QE input within 10⁻⁶ Å;
      - config_type and archive location;
      - W < 60 writes only the metadata.
    - **Outcome.** None stopped the script.
18. **QE input text** (runbook step 8 item 7).
    - **The runbook's statement.** The item-1′ and `chk_` inputs differ from the WP2b inputs only by
      an explicit `tot_charge` line (0.0 or 1.0) and by the `pseudo_dir` spacing.
    - **Checked here** on one input of each of WP3, item 1′ and `chk_` against WP2b
      m05_undoped_img0. Apart from the prefix and the geometry, only the `tot_charge` line differs.
19. **Commit-message errors.**
    - The title of 1687267 says "154 QE single points". The archive holds 153 (95 + 50 + 8); 154
      was the planned count before m06_Sr_md450 was rejected.
    - For 4c1aaa8, see item 11. Its message also gives 627 MB for "the 20 kept checkpoints"; that
      is the size of 21 files, the 20 checkpoints and `wp3_run-123.model` (`checkpoint_files.txt`).
    - The title of 0b79b9c says "gate-only at eb92910". The run record names c02c872, whose
      scripts 29–41 are those of eb92910 (§2 item 1).
20. **Where step 6 ran.** Step 6 ran on the analysis laptop, as the runbook prescribes, with
    mace-torch 0.3.16 and the `scripts/39` default of 4 threads (the runbook command sets no
    thread count). The training ran on the node at 32 threads. The reproduction
    gate covered the zero-shot arm only (§2 item 8).
21. **After the training relaunch.** node_step34 repeated the input checks and the pre-flight (both
    PASS) and re-used the archived dataset and the timing result. The node dataset files equal the
    committed ones (item 10).
22. **Indicative w_E.** Item 2's indicative w_E (≈ 6.7 × 10⁶) is about 95 times the value used
    (7.0 × 10⁴; unrounded 70 260.7). The rule itself was followed; §8 gives the reason for the difference.
23. **Item 6 not run.** Amendment m item 6 decided this in advance as a deviation from the WP3 row,
    because the outcome is not Validated.
24. **Timestamps of the mace log.** The training log (`run2/logs/*.log`) uses the node's local
    clock, 8 h ahead of the UTC times in `run2/node_logs/`.
25. **Spot reclaim during step 7** (§5, "Run record").
    - **What it cut.** Ten relaxations were cut. The driver reran them with cause spot-reclaim, as
      the "Interrupted jobs" rule prescribes. It classified the cause from the recorded termination
      notice and the system journal of the reclaimed boot (06740b92). The operator restarted the
      node and relaunched the driver; no decision on a cause was needed.
    - **The partial outputs.** Each was a FIRE log only, moved aside unread by `scripts/40`.
    - **What the operator did with them.** The sha256 comparison with the node (§2 item 10) and a
      string search for host names and local paths (it prints file names only) also covered
      `relax/discarded/`. No value from a discarded file was read.
26. **Path and host-name redaction of the step-7 outputs.** The method is that of item 12.
    - **What changed.** As written, `wp3b_result.json`, `wp3md_result.json` and `wp3_outcome.json`
      held absolute local paths (the repository root and the staging directory) and the node's
      host name (in each relaxation attempt record and in each of the 10 rerun records). Only those substrings were replaced, with
      `<REPO>`, `<MAC_STAGE>` and `<NODE_HOST>`.
    - **The proof.** A leaf-by-leaf JSON comparison shows that nothing else differs. The leaves
      replaced are 37 in `wp3b_result.json`, 12 in `wp3md_result.json` and 3 in `wp3_outcome.json`
      (`wp3/step7/REDACTION.json`).
    - **The originals.** The sha256 values of the files as written are 0110a41d…270b
      (`wp3b_result.json`), 17f89140…feaa (`wp3md_result.json`) and 0a4cd1d2…ae9d
      (`wp3_outcome.json`). `wp3_outcome.json` records the first two in `adoption.d.file_sha256`
      and `adoption.e.file_sha256`, so those two values refer to the unredacted files.
      `eval_json.file_sha256` (dda75f63…) equals the committed `wp3_eval.json`.
    - **The work-directory tarballs.** They hold copies of the 145 node files, with the host name
      replaced in the 36 JSON records that carry it. Each tarball has a manifest that gives every
      file's node and archived sha256. No trajectory or QE file was changed: each `trajectory_sha256`
      in the MD records matches its archived trajectory.
    - **Where the originals are.**
      - **The three JSON files and `wp3_eval.json`.** Their originals (sha256 above, and 88e7db00…
        for `wp3_eval.json`) are kept off-repository, in a private record folder on the analysis
        laptop, outside the session workspace. That folder also holds the operator's log and the
        two review summaries, with a SHA256SUMS list. A further copy goes to the node's data disk
        at its next boot.
      - **The unredacted work directories and the driver's state directory.** They remain on the
        node's data disk.
      - **The state directory in the repository.** It is also archived, unredacted, as
        `wp3/step7/step7_state.tar.gz` (162 files, with a manifest). It holds the launch records,
        cause files, spot notice, heartbeats and poller log, and contains no host name or local
        path.
27. **Post hoc diagnostic** (`scripts/43_wp3_md_bond_diagnostic.py`). It was written after the (e)
    verdict, to find which bond failed. It reads only the archived MD tarball, loads no model and
    gates nothing. It stops unless its restated topology test reproduces the recorded `topology_ok`
    of every frame, which it does (612 frames). In these runs `topology_ok` equals the frame verdict,
    because no other check failed in any frame. After the review of item 32 it was extended to
    report the sampled temperatures (§6); its other outputs are unchanged.
28. **Console logs of 7e and step 8.** The logs are `wp3/step7/step7e_scripts40.log`,
    `step7e_scripts41.log` and `step8_outcome.log`. Only the repository-root prefix of one line of
    the last was removed.
29. **Repository state during the analyses.** The 7e and step-8 commands ran at 602e487.
    - **What the records show.** Each script records that its own files and helpers were
      unmodified: `git.uncommitted` is empty in all three results. `scripts/40` also records
      `script_equals_head` true, and `scripts/41` records `analysing_files_equal_reference` true.
      These keys cover no other file.
    - **What else existed.** Untracked at the time were the step-7 archive being written, the
      draft of this result and the roadmap update. The roadmap update was kept in a separate draft
      file and appended to `SCREENING_ROADMAP.md` only after step 8.
30. **Node stopped after the archive.** After the byte comparison of §2 item 10, the node was
    stopped (economical mode) at about 07:44, about 11 min after STEP7_DONE. The node-side archive
    copies of §9 item 10 remain on its data disk. So do the unredacted step-7 work directories and
    the driver's state directory (item 26).
31. **The MD ran warmer than its set points** (§6, "Sampled temperature").
    - **What.** The organic atoms sampled kinetic temperatures 10–13% above the set point; Pb and I
      did not. This is disclosed because the (e) failures occurred at 450 K in C–H bonds.
    - **Status.** The cause was not investigated. The protocol is the pre-registered one (item 4;
      the same as the frame generation of `scripts/35`), and the verdict is unchanged.
32. **Review before commit.** An eight-agent adversarial check reviewed this result, the roadmap
    update, the redaction and the figure: four reviewers, each with an independent verifier.
    - **Reproduced.** Every number in §5–6 was recomputed from the primary files. This covers the
      residual forces, from the QE outputs and the region file; the redaction, leaf by leaf and
      file by file; the tarballs against their manifests and the node copies; and `scripts/43`, by
      rerunning it.
    - **Corrected in the first round.**
      - why two relaxations ran once (the thread budget);
      - the restart and relaunch times and their sources;
      - which journal the reclaim classification read;
      - that amendment m fixes the region sets, not a region id;
      - the definition of the free region;
      - the SCF iteration count;
      - the scale of the force-error comparison, and its like-for-like values;
      - the raw-F basis of the relaxation energies, with the E′ values;
      - the DFT-level order of the WP2e and fine-tuned minima (210.6 meV);
      - the source of the zero-shot WP2e value;
      - the geometry values of the failing H;
      - the harmonic SD (0.036 → 0.035 Å), and the skew counts in place of a two-event tail
        argument;
      - the erratum on the training I–I;
      - the rule that keeps the (e) verdict (item 4, not item 5);
      - what `scripts/43` checks (item 27);
      - the scope of the scripts' git keys (item 29);
      - the order of the node stop (§2 item 10);
      - where the originals are kept (item 26);
      - in the figure, the key's fill scope, the "DFT ΔF, raw" label and the 300 K tint.
    - **Second round.** A four-agent round (two checkers, two verifiers) rechecked the corrections
      and the whole document. It found no wrong number. It tightened wording and sources: the
      launch times of the two single-run cells, the scope of §1, the within-bond SD convention, the
      sources of the run means, the boot named in the rerun list, and the file list.
    - **Added.**
      - the sampled temperatures (item 31);
      - the driver's state directory as an archive;
      - the panel map of the figure.

## 10. Files

- **Plan and run control.**
  - `PLAN.md`, amendment 2026-10-28m (not edited since 84da73b).
  - `WP3_RUNBOOK.md`.
  - `scripts/wp3_runbook/` (node drivers, helpers, `review_2026-10-28/PATCH_NOTES.md`,
    `review_2026-10-29/NOTES.md`).
- **Frames.** `wp3/frames/` (95 extxyz files and `frames_report.json`).
- **QE single points.** `wp3/raw/` (WP3), `wp3/test_extra/raw/` (item 1′) and `wp3/chk/raw/`
  (q = +1 checks), as `<label>.{in,out}.gz`.
- **Dataset.** `wp3/dataset/` (`train.xyz`, `valid.xyz`, `test.xyz`, `E0s.json`,
  `dataset_meta.json`).
- **Training (run2).** `wp3/run2/`:
  - `wp3.model`, sha256 3f7bf6f5…65d2ca;
  - `logs/`, `results/wp3_run-123_train.txt` and `checkpoint_files.txt`. The 20 kept checkpoints
    and `wp3_run-123.model` (21 files, 627 MB) are not committed.
  - `node_logs/`: `train_command.txt`, `timing.txt`, `restarts.txt`, `preflight.txt`,
    `startcheck_run{1,2}.txt`, `step2.log`, `step34.log`, `techfail.txt` and `versions.txt`.
- **Model note.** `wp3/MODEL_NOTE_2026-11-03.md` (CNOTE c1d0ace).
- **Evaluation.**
  - Step 1: `wp3/gate_only_step1.{json,log}`.
  - Step 6: `wp3/wp3_eval.json` and `wp3/step6_scripts39.log` (C6 5cf6c5f).
  - Scripts: `scripts/33`, `35`, `39`, `40` and `41`; post hoc, reported only: `scripts/43`.
- **Figure.** `figures/fig_wp3_criterion6.{py,pdf,png,svg,tiff}`, with source data in
  `figures/source_data/fig_wp3_criterion6_*.csv` (602e487). The panels are:
  - a: criterion 6;
  - b: (ii) per pair;
  - c: adoption (b);
  - d: adoption (c);
  - e: absolute E_a, reported.
- **Step 7 and step 8.**
  - `wp3/wp3b/raw/`: the 12 `wp3b_` and `wp3bu_` single points, as `<label>.{in,out}.gz`.
  - Results: `wp3/wp3b_result.json` ((d)), `wp3/wp3md_result.json` ((e)) and
    `wp3/wp3_outcome.json` (step 8), redacted (§9 item 26).
  - `wp3/step7/`:
    - the driver's `step7.log` and `step7_reruns.list`;
    - `wp3b_work.tar.gz`, the `scripts/40` work directory: region, zero-shot comparator, the 12
      relaxation records and their attempt records, the staged QE inputs (`<label>.qe/`), final
      structures, FIRE logs, `wp2e_minimum.json` and the discarded partial FIRE logs;
    - `wp3md_work.tar.gz`, the `scripts/41` work directory: the 12 MD records, their attempt
      records and their 51-frame trajectories;
    - `step7_state.tar.gz`, the driver's state directory (§9 item 26);
    - the manifests `*.MANIFEST.tsv` and `REDACTION.json`;
    - the console logs of 7e and step 8;
    - `md_bond_diagnostic.json` (`scripts/43`).
- **Figure (d) and (e).** `figures/fig_wp3_adoption_de.{py,pdf,png,svg,tiff}` and its layout-QA
  records `fig_wp3_adoption_de.alignment.{json,svg}` and `.collision-audit.json`, with source data
  in `figures/source_data/fig_wp3_adoption_de_*.csv`. Panel letters are not condition letters. The
  panels are:
  - a, condition (d): free-atom residual DFT force, RMS against max, from zero-shot image 0 to the
    fine-tuned frozen-far-field minimum;
  - b, (d): free-atom RMS per cell against the bound, beside the `wp3bu_` whole-cell RMS
    (criterion 5, reported);
  - c, (d), reported: relaxation energies, model ΔE against DFT ΔF (raw F), with the WP2e DFT
    minimum for both models;
  - d, condition (e): every checked frame of the 12 MD runs;
  - e, (e), post hoc: the C–H distance distribution at 300 and 450 K.
- **Roadmap.** `../SCREENING_ROADMAP.md`, update 2026-11-03.

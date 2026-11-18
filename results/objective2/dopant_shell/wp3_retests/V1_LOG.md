# WP3-V1 operations log

- 2026-11-15 00:37Z: foundation file downloaded from the mace-mp GitHub release (mace_mp_0,
  2023-12-03-mace-128-L1_epoch-199.model); sha256 01bfe22100139f424713cf921144e5509cbe353d67aa9fa1be9c6e1e0ed35845,
  equal to WP3's MODEL_NOTE_2026-11-03.md.
- Local environment `mace316`: Python 3.12, torch 2.14.1, mace-torch 0.3.16, e3nn 0.4.4, ase 3.29.0 (as the node).
- **G-train PASS** (00:40-00:47Z, `gtrain/`, unchanged WP3 command, 16 threads): Initial loss 0.33213836 and epoch-0
  validation loss 9.66622193, both equal to run2's log to all printed digits. Stopped after epoch 0 (the gate needs
  only these two). Local epoch time about 6.1 min.
- **G-eval PASS** (`eval_v1.py`, `geval.json`): from test.xyz labels, ZS and WP3 reproduce criterion 6 (i), (ii) raw,
  (iii) raw all/Sr/GA of wp3_eval.json to within 3e-8 (10 of 10 values). No QE output was opened.
- 2026-11-15 ~00:52Z: V1 training started (`run_v1/`, `--energy_weight 6700000.0`, otherwise the WP3 command).
- 2026-11-15 ~09:45Z (before any V1 test value): `--keep_checkpoints` keeps only epochs whose validation loss improved
  (14 kept at epoch ~85; as run2). The prespec's "final epoch (99)" exists only if epoch 99 improves. Ruling, made now:
  if it does not exist, the last kept checkpoint stands in for it, labelled "last kept (epoch N)". The primary
  model remains mace-torch's selection (`wp3v1.model`).
- 2026-11-15 11:06Z: V1 training done (exit 0). Lowest validation loss at epoch 64 (0.56037; epoch 82 0.58820, epoch 99
  0.61974); mace-torch selected epoch 64 -> `run_v1/wp3v1.model`, sha256
  9827174aa284587a49880476291db220ea959da3a9c78ee4cf502ff4e18fda59. Epoch 99 did not improve and was not kept, so the
  "last kept" stand-in is epoch 64 itself: V1 has one model.
- **V1 result (prespec section 5), `v1_eval.json`:** P1 (Sr far-ref E_b RMS, 3 m30 sites) ZS 9.20 / WP3 88.71 /
  V1 98.62 meV; P2 28.41 / 69.38 / 77.33 meV; P3 86.81 / 14.94 / 33.14 meV/A; P4 23.65 / 32.76 / 47.89 meV.
  m30 Sr hinge (DFT +129.4): ZS +123.0, WP3 +11.6, V1 +1.1 meV; flank (DFT +95.6): +109.6, -3.0, -17.0 meV.
  **Reading: "collapse persists" (P1 > 50 meV).** H1 is refuted: the energy-weight dilution does not explain the Sr
  collapse. P3 < 86.81, so no force-energy trade-off flag. V2 is not required by the prespec; V1 settles H1.
- **D-V1a (post hoc, reported only; `diag_trainhost.py`, `diag_trainhost_m05.json`).** On the training host m05,
  whose Sr quartets are in train.xyz with energy labels, the far-referenced Sr hinge E_b is: label E' +122.0 (raw
  +105.7); ZS +127.4; WP3 +41.3; V1 +31.1 meV. Flank: E' +128.7 (raw +116.1); ZS +152.1; WP3 +51.6; V1 +35.3 meV.
  The fine-tuned models do not reproduce the Sr-vacancy repulsion even on frames they were trained on.
- **D-V1b (post hoc; `diag_cancel.py`, `diag_cancel.json`).** Non-far-referenced Sr136 E_b error, model - DFT raw:
  ZS -34.1 (m05) / -41.8 (m30); WP3 -135.5 / -155.0; V1 -143.5 / -166.0 meV. The fine-tuned error is systematic (same
  sign and size on the training and the test host), not a loss of error cancellation; an earlier in-session guess of
  "decorrelated per-cell errors" is not supported. ZS per-cell residuals (mean +7.86e7 meV, i.e. about 78.6 keV; corrected 2026-11-15 from a mis-stated "~78 eV") are absolute-reference offsets that
  cancel in a composition-balanced E_b and say nothing about correlation.
- Sun Nov 15 11:16:33 UTC 2026: V1b training started (`run_v1b/`, `v1b/train.xyz`: 24 pristine MD/rattle frames at
  config_energy_weight 0, checked: 201 frames, labels/positions/forces/energies identical, 106 energy-labelled).
  Initial: head: Default, loss=0.73195413, RMSE_E_per_atom=    0.33 meV, RMSE_F=   79.82 meV / A
- 2026-11-15 21:15Z: V1b training done (exit 0); selection epoch 77 (validation loss 1.22556); `run_v1b/wp3v1b.model`
  sha256 3ea731ecc87a39ab414e54e0cddde6a0504364935d9ca792ac2c1dbe1a16e6a2.
- **V1b result (V1B_PRESPEC), `v1b_eval.json`:** P1 125.62 meV (ZS 9.20, V1 98.62); P2 101.17; P3 21.35 meV/A; P4 39.70
  meV. **Reading: collapse persists (P1 > 50).** D-V1a on m05 (raw): Sr hinge label +105.7, V1b +0.5; flank +116.1,
  V1b +6.0 meV (`diag_trainhost_m05_v1b.json`). Neither energy-weight change helps; by the prespec V2 is the remaining
  recipe test.
- **D-V1c (post hoc; `diag_labels.py`).** Hypothesis: band and binding frames are near-duplicate structures with
  inconsistent labels. Not supported: same-composition pairs differ by RMSD 0.26-0.56 A (max 1.2-1.8 A), and the band
  frame is 0.13-0.82 eV higher in raw F in every pair (the soft FA landscape, cf. WP2e). Other pairs differ in species
  order and were not compared.
- **Standing (2026-11-15 21:30Z).** Three single-head fine-tunes on the same 201 frames (w_E 7e4; 6.7e6; 6.7e6 with the
  24 pristine off-equilibrium frames at energy weight 0) all lose the Sr-vacancy repulsion, on the test host and on
  their own training quartet, and the loss grows as the energy fit of the band/binding frames is emphasised. Cause
  not identified. Remaining recipe test: V2, multi-head replay (needs the MP replay subset).
- 2026-11-15 22:23Z, V2 timing (`v2_timing/`, num_samples_pt 10000, filter none): replay 9000 train + 1000 valid MP
  frames, fine-tuning set upsampled 4x by mace-torch; about 3460 of about 4900 batches of epoch 0 in 57 min, so about
  81 min per epoch and about 135 h for 100 epochs > 48 h. **By V2_PRESPEC the fallback applies: num_samples_pt 2000,
  filter_type_pt combinations.** Decided on wall time only; no V2 metric was read. Timing run stopped.
- 2026-11-15 22:23Z: first V2 launch refused by mace-torch (filter_type_pt combinations needs an element list); an
  infrastructure fix, no step ran. 22:26Z V2 started (`run_v2/`) with `--atomic_numbers [1,6,7,38,53,55,82]` (the 7
  training elements, the keys of E0s.json). Replay: 1800 train + 200 valid MP frames; lr 1e-4 and EMA set by the
  protocol. **Correction to V2_PRESPEC wording:** mace-torch's `combinations` filter is not "a subset of the training
  elements"; its replay set contains other elements as well (the filtered element list includes Li, Be, B, O, F, ...).
  V2 is therefore "mace-torch combinations replay, 2000 samples", as run. The prespec file is left as written.

## 2026-11-17 — V2 result; V3 started

- V2 finished 04:46Z 17 Nov (selected epoch 99, the last). Model `run_v2/wp3v2.model`, sha256
  7fcccdc53d677ceaa48485b0187b28718a098e5b2b2c45b133972b0881176efc. The command line carries lr 0.005 / EMA 0.99, but
  the multihead mode overrides it: log line 5 "Multihead finetuning mode, setting learning rate to 0.0001 and EMA to
  True", line 70 "Learning rate: 0.0001".
- `v2_eval.json`: P1 (m30 Sr far-referenced E_b error, RMS) 15.17 meV (zero-shot 9.20, WP3 88.71, V1 98.61, V1b
  125.62) -> V2_PRESPEC reading "collapse avoided". P3 force RMSE 49.95 meV/A (zero-shot 86.81, WP3 14.94) -> above the
  45 meV/A caution of V3_PRESPEC: V2 counts as under-trained. m30 all-site 15.59 (ZS 28.41), GA 16.21 (ZS 43.49).
  m21 worse than zero-shot: all 54.05 (29.07), Sr 40.68 (32.06), GA 69.44 (23.90); post hoc, unexplained.
- No m05 (D-V1a) evaluation of V2 yet.
- Correction: V1 P1 is 98.6149 meV in `v1_eval.json` (98.61, not the 98.62 logged earlier).
- V3 (WP3 command with only `--lr 0.0001`, name wp3v3) started 12:19Z 17 Nov in `run_v3`; epoch 9 at 13:21Z
  (RMSE_E 0.56 meV/atom, RMSE_F 26.70 meV/A; about 6.1 min per epoch).

## 2026-11-17 22:41Z — V3 finished; read-out by V3_PRESPEC

- Training ended 22:41:41Z, exit 0, 100 epochs; selected epoch 91 (log: "Loaded Stage one model from epoch 91").
  Model `run_v3/wp3v3.model`, sha256 71b5d99e1140d81559cebf7b5ffa9700a5c71a678c5dac5a0c26c3e654550cba. 43 checkpoints
  kept.
- `python -B eval_v1.py --out v3_eval.json V3=run_v3/wp3v3.model` (env mace316), exit 0:
  **P1 = 47.04 meV** (m30 Sr far-referenced E_b error RMS; ZS 9.20, WP3 88.71, V1 98.61, V1b 125.62, V2 15.17);
  **P3 = 15.76 meV/A** (ZS 86.81, WP3 14.94, V2 49.95). (ii) raw 22.11 meV (ZS 23.65, WP3 32.76).
  m30: Sr hinge +68.5 (DFT +129.4), flank +42.5 (DFT +95.6), mid -9.3 (DFT +1.2); GA 7.13 (ZS 43.49); all 36.71.
  m21: Sr 34.12 (ZS 32.06), GA 48.49 (ZS 23.90), all 40.49 (ZS 29.07).
- **Reading (rule fixed 2026-11-16):** P1 is neither <= 25 ("learning rate is the cause") nor > 50 ("not the learning
  rate"), and P3 <= 45, so the run is not under-trained: the outcome is the fourth line, **"partial"**; the checkpoint
  trajectory is reported (`traj_v3.py` -> `v3_traj.json/csv`, running). Joint rule with V2: V2 keeps the repulsion but
  counts as under-trained (P3 49.95 > 45); V3 keeps the sign and about half of the hinge value at WP3-level forces.
  Neither branch of the joint rule ("both keep" / "only V2" / "neither") is met cleanly; reported as undecided.
- Post hoc observations (not in the rule): P1 = 47.04 lies 3 meV under the 50 meV line, on 3 sites of one host and
  one seed; m21 GA is worse than zero-shot in V2 and V3 as it is in WP3 (33.57).
- Summary of all arms: `retests_summary.json`.

## 2026-11-17 23:35Z — corrections and trajectory

- Correction to the entry above: 42 checkpoints were kept (epochs 0 to 91), not 43; the directory listing counted the
  file `wp3v3_run-123.model` as well.
- `python -B traj_v3.py` (22:44-22:55Z, exit 0): `v3_traj.json`, `v3_traj.csv`; the row "selected" reproduces
  `v3_eval.json` (m30 hinge +68.5, flank +42.5; m21 +96.9, +110.5). m05 (training host): hinge +79.0 (label +105.7),
  flank +88.3 (label +116.1). m30 hinge by checkpoint: +118.3 (epoch 0), minimum +59.8, +68.4 at epoch 91.
- mace-torch 0.3.16, `mace/cli/run_train.py` lines 204-210: the multihead branch sets lr 0.0001, EMA True, EMA decay
  0.99999 (read from the installed source for the V2 record).
- The note `WP3_RETESTS.md`, its table and the files it names are published under
  `results/objective2/dopant_shell/wp3_retests/` with absolute paths replaced by placeholders.

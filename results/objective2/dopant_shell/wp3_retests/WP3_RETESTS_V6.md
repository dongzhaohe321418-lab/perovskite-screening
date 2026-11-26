# WP3 re-test V6 — replay with the optimiser settings of V3 (2026-11-24)

Addendum to `WP3_RETESTS.md` and `WP3_RETESTS_V4V5.md`. **Post hoc and diagnostic only; no model is adopted.** Every
number below is copied by code from the json or csv file named beside it, or from the training log.

## 1. Summary

- **Pre-specification:** `V6_PRESPEC_2026-11-24.md`, committed and pushed before the run (commit `c76d99d`), with
  execution note 1 (commit `1c0836f`, before any read-out): a first launch failed before training, the replay
  subset was given with three key names changed, and gate G-replay was read as passed on the equal initial losses.
- **Result by the pre-specified reading: "under-trained".** P3 = 54.55 meV/Å, above the 45 meV/Å line;
  P1 = 21.84 meV (`v6_eval.json`). In the words of the pre-specification: "replay with these settings does not
  reach WP3-level forces in 100 epochs; no further arm follows from this note."
- **What it does not show.** P1 is low, but so is the zero-shot model's (9.20 meV at
  P3 = 86.81 meV/Å). The test was built to compare P1 at WP3-level forces, and V6 did not reach them. V6 is
  therefore no evidence that replay protects the repulsion at WP3-level forces. That question stays open, as
  after V2.
- Both replay arms (V2, V6) are under-trained; the single-head arms at the same learning rate (V3, V5) reach
  WP3-level forces and lose about half of the repulsion. No arm has both.

| Arm | replay | learning rate | EMA decay | P1 (meV) | P3 (meV/Å) | m30 GA (meV) | m21 Sr (meV) | m21 GA (meV) | ΔE_a pairs (meV) |
|---|---|---|---|---|---|---|---|---|---|
| zero-shot | – | – | – | 9.20 | 86.81 | 43.49 | 32.06 | 23.90 | 23.65 |
| V2 | yes | 1e-4 | 0.99999 | 15.17 | 49.95 | 16.21 | 40.68 | 69.44 | 40.66 |
| V6 | yes | 1e-4 | 0.99 | 21.84 | 54.55 | 14.67 | 43.88 | 70.86 | 42.09 |
| V3 | no | 1e-4 | 0.99 | 47.04 | 15.76 | 7.13 | 34.12 | 48.49 | 22.11 |
| V5 | no | 1e-4 | 0.99 | 54.84 | 15.37 | 7.53 | 39.83 | 46.74 | 20.98 |

P1: error RMS of the far-referenced Sr E_b over the 3 non-far m30 Sr sites. P3: force RMSE over the 46 m30/m32 test
frames. Sources: `retests_summary.json` (zero-shot, V2, V3), `v5_eval.json` (V5), `v6_eval.json` (V6).

## 2. The run

- Machine: the project's compute node (x86, 64 cores); mace-torch 0.3.16, torch 2.14.1, e3nn 0.4.4. Command:
  `run_v6/train_command.txt`. Log: `run_v6/logs/wp3v6_run-123.log` (its clock is UTC+8).
- Started 2026-11-24T00:49:10Z; "Training complete" at 23:01:52Z (log); 100 epochs. The process was suspended from
  01:44:14Z to 02:33:21Z for the cross-instance reruns of S2b (roadmap, update 2026-11-24 (b) item 3); epoch 4 spans
  the pause. Wall-clock times of V6 are not a timing result.
- Selected model: the checkpoint of epoch 63, chosen by mace-torch (the lowest validation loss of the head Default,
  0.02127857). sha256 of `wp3v6.model`: `79aa9119db9554df0159b63a75e07337c3029f10e0b98bc7b1a455a9ae8a9a1b`. The model and
  the checkpoints are not in the repository.
- **Gate G-replay:** execution note 1 of the pre-specification.
- **Gate G-eval2** (the evaluator on the node, on the foundation model): P1 = 9.20 meV,
  P3 = 86.81 meV/Å (`v6_node_zs_eval.json`), the values required (9.20 and 86.81). Met. sha256 of the
  evaluator on the node equal to `eval_retests.py` of this folder
  (`a13446bdb926fdbc3b71570aeb9e250086f46323ab654579cf84f59c9ac8df45`).

## 3. Read-outs and readings (rules of `V6_PRESPEC_2026-11-24.md`)

- P1 = 21.84 meV; P3 = 54.55 meV/Å; head "Default".
- Class by V3's rule: "**under-trained**" (P3 > 45 meV/Å).
- "replay protects at this rate" needs P3 ≤ 45: not read. "no resolved effect" and "replay worse" need P3 ≤ 45: not
  read. The one reading that applies is "under-trained".
- By the pre-specification no further arm follows from this note.

## 4. Reported, not read by a rule

- m30 Sr sites, model against DFT (meV; `v6_eval.json`): hinge +140.7 against
  +129.4; flank +131.7 against +95.6.
  The flank is over-estimated by 36.1 meV.
- m21 (the validation host): Sr error RMS 43.88 meV, GA 70.86 meV,
  against 32.06 and 23.90 meV zero-shot: worse than the
  foundation model on both.
- Kept checkpoints (7; `v6_traj.csv`, script `traj_v6.py`), far-referenced Sr E_b in meV, model:

| checkpoint | m30 hinge | m30 flank | m21 hinge | m21 flank | m05 hinge | m05 flank |
|---|---|---|---|---|---|---|
| selected | 140.70 | 131.65 | 171.41 | 172.22 | 139.58 | 155.55 |
| epoch-0 | 130.38 | 117.43 | 167.21 | 164.03 | 134.23 | 159.21 |
| epoch-1 | 143.06 | 131.53 | 178.83 | 174.59 | 143.15 | 171.92 |
| epoch-2 | 153.29 | 144.40 | 189.77 | 184.05 | 155.56 | 179.57 |
| epoch-36 | 139.93 | 135.07 | 177.97 | 176.54 | 141.59 | 163.92 |
| epoch-44 | 136.73 | 135.99 | 176.26 | 175.32 | 141.11 | 160.88 |
| epoch-56 | 145.34 | 139.17 | 177.84 | 180.52 | 146.96 | 163.36 |
| epoch-63 | 140.70 | 131.65 | 171.41 | 172.22 | 139.58 | 155.55 |
| DFT | 129.36 | 95.56 | 136.72 | 131.73 | 105.70 | 116.07 |

  "selected" equals the checkpoint of epoch 63, as it must. No checkpoint shows the loss of the Sr repulsion that
  V3 to V5 show; every kept checkpoint lies above the DFT value in all six columns (the repulsion is over-estimated).
- From the training log (validation set, per epoch, 100 epochs):
  - head Default: RMSE_F between 48.11 (epoch 96) and 63.16 meV/Å (epoch 27), from 79.82 before training. The final
    table of mace-torch gives RMSE_F 107.3 meV/Å on the 201 training frames and 51.5 meV/Å on validation.
  - head pt_head (the replay data): loss 5.77738917 before training, 7.45961701 after epoch 0 (the lowest of the
    run) and 9.46571491 at epoch 99; RMSE_F 113.12 meV/Å before training and 190.14 at epoch 99. The fit of the
    replay data became worse during the run.
  - So neither head was fitted well at these settings. Why (the weights of the two heads, the batch size, the
    small replay subset of 2000 configurations) was not examined.

## 5. Limits

The used test set; P1 on 3 sites of one host; one seed; another machine than V1 to V5 (confounded with the arm);
a replay subset of 2000 configurations with three key names changed; one suspension of 49 minutes. The trajectory
script for a multi-head run was first used here and reproduces the selected model's values of `v6_eval.json`
(m30 hinge and flank) at the tag "selected".

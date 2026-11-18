# Why the fine-tuned MACE models lose the Sr–vacancy repulsion: post hoc diagnosis (2026-11-16)

**Status.** Every analysis below is post hoc and descriptive. No training was run; no verdict or threshold changes.

## 0. Deviations, checks and what was not examined

- **D3 is reduced.** The task limit (only the 48 binding frames per model) excludes the band, MD and rattle training frames. Per-cell residuals are given for config_type `binding`, host m05 (16 cells) only; for the whole training set only mace's final error table is quoted.
- **Energies only** (`compute_force=False`); force RMSEs are the logged m21 values.
- **Kept checkpoints only** (WP3 20, V1 14, V1b 12); other epochs were never saved.
- **WP3 values were recomputed**, because m30 and per-cell residuals were needed. They reproduce `WP3_DIAGNOSTICS.md` §3 (epochs 0, 11, 82; four sites; 0.1 meV), `diag_trainhost_m05_v1b.json` (8 values) and the Sr sites of `v1_eval.json` and `v1b_eval.json`. Each selected-epoch checkpoint gives the energies of its `.model` file exactly.
- **Provisional.** The Sr–vacancy distance takes the vacancy as the midpoint of the two B sites with fewest iodides within 4.0 Å; it is nominal for mid-hop band images 2–4. The band end-point contrast (§4) assumes that the Sr and undoped bands of a host are the same hop; not verified.
- **Zero-shot residuals** use E0s.json in place of the foundation E0s; E_b is unaffected.
- **Also read:** `private/wp3_v1/v1b/train.xyz` (V1b energy weights).
- **Process.** Two analysis cells were held by the platform's safety check; one ran after the user's approval, the other was cleared on resubmission. Model evaluation took 1076 s.
- **Not examined:** `run_v2/`, `cache/`, every `*.out.gz`, all blinded folders; `WP2C_RESULT.md`, `V1_PRESPEC`, scripts 33 and 39, `diag_cancel.json`; any model on band, MD or rattle frames.

**Sources.** D1: [eb_trajectory.csv]({{artifact:644d8f75-78a7-4fac-84b6-734935d74452}}). D2: [d2_m05_residuals.csv]({{artifact:281a6fe6-737e-41b0-8526-eb68c4bae082}}). D3: [d3_fit_quality.json]({{artifact:d79bd352-480f-4135-80a8-77c7d291d130}}). D4: [d4_coverage_summary.json]({{artifact:6a2a0255-d0bd-4dc2-a183-a0292f75153c}}), [d4_frames.json]({{artifact:7122d422-2671-4ace-9af4-19a5a28cd339}}). All energies and checkpoint hashes: [binding48_energies.json]({{artifact:677b9c8f-3ec6-4ad5-941b-cf56bd7b3949}}). DFT values are the `REF_energy_raw` and `REF_energy` labels of the dataset `.xyz` files; logged curves are `results/*_train.txt` of `run2`, `run_v1`, `run_v1b`.

## 1. D1 — trajectory

Far-referenced Sr E_b, hinge/flank, meV; RMSE_E in meV/atom, RMSE_F in meV/Å (logged, m21). All kept checkpoints are in the CSV.

| Model, epoch | m05 (train) | m21 (valid) | m30 (test) | m21 RMSE_E / RMSE_F |
|---|---|---|---|---|
| DFT raw F | +106/+116 | +137/+132 | +129/+96 | – |
| DFT E′ | +122/+129 | +131/+136 | +130/+98 | – |
| Zero-shot | +127/+152 | +161/+158 | +123/+110 | 0.33 / 79.8 |
| WP3 0 | +257/+278 | +303/+263 | +252/+260 | 15.83 / 108.8 |
| WP3 4 | +117/+110 | +122/+91 | +101/+87 | 3.96 / 41.5 |
| WP3 8 | +113/+113 | +106/+89 | +83/+61 | 1.26 / 30.6 |
| WP3 11 | +78/+79 | +68/+56 | +42/+20 | 1.00 / 29.4 |
| WP3 15 | +43/+43 | +43/+37 | +15/-7 | 1.04 / 25.9 |
| WP3 82 (sel.) | +41/+52 | +44/+44 | +12/-3 | 0.25 / 15.6 |
| V1 0 | +99/+106 | +104/+92 | +79/+86 | 1.92 / 372.6 |
| V1 4 | +65/+63 | +69/+43 | +35/+20 | 2.25 / 47.6 |
| V1 30 | +14/+6 | +4/-8 | -29/-37 | 0.60 / 84.2 |
| V1 64 (sel.) | +31/+35 | +34/+29 | +1/-17 | 0.38 / 34.8 |
| V1b 0 | +114/+129 | +130/+120 | +121/+117 | 3.27 / 157.7 |
| V1b 4 | +28/+26 | +33/+10 | -4/-3 | 2.44 / 48.7 |
| V1b 17 | -22/-29 | -27/-27 | -42/-48 | 1.36 / 30.5 |
| V1b 77 (sel.) | +0/+6 | +1/-11 | -41/-40 | 0.60 / 21.5 |

![E_b trajectory]({{artifact:857a106a-b5d9-4a77-8894-5496665cf5f4}})

- **The first optimiser step is violent.** The batch loss goes from 4.71 to 359.8 (WP3) and 2197.4 (V1, V1b) at batch 2. Logged m21 RMSE_E rises from 0.33 to 38.1 meV/atom (WP3, epoch 1); RMSE_F reaches 372.6 meV/Å (V1, epoch 0).
- **The repulsion survives that disruption.** At the first kept checkpoint the m05 hinge is +256.6 (WP3, an overshoot), +98.5 (V1) and +114.5 meV (V1b). WP3 is within 19 meV of the raw label at kept epochs 4–8.
- **It is then lost progressively, over roughly epochs 4–30.** WP3: +78.0 at epoch 11, +43.1 at 15. V1: +65.0 at 4, +14.0 at 30. V1b: +28.3 at 4, −22.5 at 17.
- **A noisy plateau follows.** Mean m05 hinge: WP3 +35.3 (epochs ≥ 15; range +11.8 to +62.9), V1 +30.7 (≥ 30), V1b −5.5 (≥ 17). m21 follows m05 (+38.6, +30.2, −5.3); m30 lies lower (+10.2, −1.6, −36.6).
- **Against the validation curves.** In WP3 the fall between epochs 8 and 15 comes while RMSE_F goes from 30.6 to 25.9 and RMSE_E from 1.26 to 1.04, after the steep part of both curves. In V1 and V1b RMSE_E never returns to the zero-shot 0.33 (best 0.38 and 0.60); over V1's last six epochs it ranges from 0.41 to 1.04, that is 95–242 meV per cell.
- **The learning rate never decays:** 0.005 in the optimiser state of all 46 checkpoints.

## 2. D2 — which cells move (m05, label basis, meV)

Host and V cells cancel in a far-referenced E_b. Its error is [r(D_near+V) − r(D_far+V)] − [r(D_near) − r(D_far)], with r = model − `REF_energy`; the two brackets are the columns "D+V cells" and "D cells". Hinge site; the flank behaves alike.

| Model, epoch | Hinge error | D+V cells | D cells | Far-quartet error |
|---|---|---|---|---|
| Zero-shot | +5.4 | -4.0 | +9.4 | +0.0 |
| WP3 0 | +134.6 | +170.4 | -35.7 | -8.0 |
| WP3 4 | -5.3 | -3.0 | -2.3 | -18.3 |
| WP3 82 | -80.7 | -107.2 | +26.5 | -15.2 |
| V1 0 | -23.5 | +7.3 | -30.8 | -24.8 |
| V1 64 | -90.9 | -111.3 | +20.4 | -13.1 |
| V1b 0 | -7.5 | -8.8 | +1.3 | -14.6 |
| V1b 77 | -121.5 | -149.2 | +27.7 | -11.0 |

- **The Sr-adjacent D+V cells carry the loss.** Plateau means of the D+V term: −108.2 (WP3), −110.3 (V1), −144.6 meV (V1b). The vacancy-free Sr cells contribute +21.5, +18.9 and +17.1 meV, the other way.
- **The far quartet is untouched.** Its non-far-referenced E_b error stays between −28.6 and −0.3 meV at all 46 checkpoints, although the host residual reaches 4197 meV and the Sr-class offset relative to the host ranges from −1798 to +1429 meV.
- **Same pattern in the three runs**, deeper where band and binding energies weigh more: selected-model hinge error −80.7 (WP3), −90.9 (V1), −121.5 meV (V1b).
- **The models contradict their own training labels.** The m05 mid − hinge contrast is −143.0 meV in the E′ labels; it is −159.6 (zero-shot), −67.0 (WP3), −52.7 (V1) and −21.1 meV (V1b) in the models.

## 3. D3 — fit quality on the m05 binding cells (selected models, meV)

Class means of r; number of cells in brackets.

| Model | host | V | Sr (4) | Sr+V (4) | GA (3) | GA+V (3) | SD of 16 | within-class SD | max \|r\| |
|---|---|---|---|---|---|---|---|---|---|
| Zero-shot + E0s.json | +22 | +65 | -1 | +46 | -6 | +50 | 29.5 | 15.0 | 65 |
| WP3 (82) | -38 | -85 | -4 | -107 | -6 | -34 | 53.1 | 36.8 | 159 |
| V1 (64) | -105 | -171 | +77 | -48 | -32 | -73 | 78.4 | 37.7 | 171 |
| V1b (77) | -222 | -134 | -41 | -25 | +3 | +111 | 95.2 | 52.5 | 222 |

- **Per-cell precision is 53–95 meV (SD), worse than the starting model's 29.5 meV** and of the size of the 100–150 meV signal. SD over the 16 cells of the other hosts (zero-shot/WP3/V1/V1b): m21 31/39/68/117; m30 57/47/69/128 meV.
- **Most of that scatter is common to a class** and cancels in E_b (far quartet within 29 meV, §2). The near-site error is systematic, not a loss of error cancellation, as D-V1b of `V1_LOG.md` found.
- **Whole training set** (mace's final table, all 201 frames including energy-weight-0 frames): RMSE_E 0.8, 0.9, 4.1 meV/atom; RMSE_F 30.7, 54.8, 43.0 meV/Å (WP3, V1, V1b). Residuals by config_type and host beyond m05 binding were not computed (§0).

## 4. D4 — coverage: energy-labelled training frames containing Sr

Counts are the same in the three runs; V1b differs only in dropping the energy labels of the 24 vacancy-free MD and rattle frames (106 against 130 energy-labelled frames).

| Host | Sr, no V | Sr adjacent (Å) | mid-hop images | Sr ≥ 7 Å (Å) | force-only Sr+V | end-point contrast E′ (meV) |
|---|---|---|---|---|---|---|
| m05 | 4 | 3 (3.47, 3.51, 3.52) | 3 | 3 (7.22, 7.27, 9.74) | 4 | -166.1 |
| m06 | 0 | 1 (3.45) | 3 | 1 (7.23) | 3 | -82.2 |
| m08 | 0 | 1 (3.42) | 3 | 1 (7.13) | 4 | -134.0 |
| m12 | 0 | 1 (3.46) | 3 | 1 (7.23) | 4 | -63.3 |
| m15 | 0 | 2 (3.38, 3.46) | 3 | 0 (–) | 4 | +146.9 (*) |
| m20 | 0 | 1 (3.55) | 3 | 1 (7.30) | 4 | -36.9 |

(*) Both end points adjacent; not an adjacent-against-far contrast.

- **Sr without a vacancy exists only on m05** (4 frames; their substitution energies spread by an SD of 11.7 meV).
- **The premise that other hosts hold Sr only next to the vacancy is not accurate.** Band image 6 places Sr 7.1–7.3 Å from the vacancy on four of the five other hosts. With the undoped band as control, each carries one energy-labelled adjacent-against-7 Å contrast.
- **Those labels have the repulsive sign** (provisional, §0): mean −79.1 meV over m06, m08, m12, m20, and −166.1 meV on m05, against −149.7 meV for the m05 binding-frame equivalent (mid − flank, E′).
- **Answer.** Outside m05 the training set identifies how the interaction differs between adjacent and 7 Å, from one pair of frames per host. It does not identify the substitution energy, nor the interaction against a 9.7 Å reference. Coverage is thin but not empty, and the labels examined do not ask for the collapse.

## 5. D5 — ranked causes and the next experiment

1. **Progressive forgetting under a constant learning rate of 0.005 (the working hypothesis, amended).** *For:* the first-step blow-up; eV-scale class-offset swings; no decay in 100 epochs; a per-cell fit worse than the starting model; plateau values near zero. *Against the original wording:* the repulsion is not destroyed in the first epochs; it is present just after the disruption and is lost over epochs 4–30.
2. **A systematic pull in the loss as trained** (force term, E′ energies with q = 0 forces, or mid-hop band energies). *For:* a stable plateau of one sign in three runs. *Against:* the m05 quartets and the band end-point labels both ask for repulsion, and a 95-fold higher energy weight did not restore it. Untested: no model was evaluated on band frames.
3. **Coverage.** *For:* §4. *Against:* the failure occurs on m05 itself, and the starting model already had the interaction.
4. **Random per-cell error.** *Against:* far quartet stable to 29 meV; same sign at six sites.
5. **Label basis and c_D.** Excluded: c_D(Sr) is −2.174 meV and cancels; the bases differ by at most 16.3 meV (`WP3_RESULT.md` §8 item 3).
6. **Checkpoint selection.** Not the cause: no kept checkpoint on the plateau comes within 40 meV of the m05 label.

**Next training experiment (not run).** The WP3 command unchanged (single head, w_E 70 000, EMA 0.99, seed 123, the same 201 frames) except `--lr 1e-4`, with the 48 binding frames evaluated at every kept checkpoint (about 22 s each). Stop once m21 RMSE_F ≤ 30 meV/Å or at 40 epochs (about 4 h at the 6.1 min per epoch of `V1_LOG.md`).

- **Cause 1 predicts:** no blow-up at batch 2; m05 and m21 hinge E_b ≥ about +90 meV when RMSE_F reaches 30 meV/Å.
- **Cause 2 predicts:** the hinge E_b declines as RMSE_F falls (below about +60 meV at 30 meV/Å), with the same D+V signature and a stable far quartet.
- **Cause 3 predicts:** m05 retained, m21 and m30 lost.
- **If RMSE_F stays above about 45 meV/Å** the run is under-trained and uninformative; repeat at 5e-4.
- **With V2:** both keep the repulsion, learning rate; only V2 keeps it, replay; both lose it, data or targets.
- **Caution on V2** (inferred; `run_v2/` not opened). Its EMA decay of 0.99999 has a time constant of 1e5 updates, against 10 050 updates in a WP3-length run. A retained E_b in V2 should count only if its force RMSE has fallen.

A check without training would also help: energies of the 90 training band frames at the four models (about 4 min), to see whether the models reproduce the band end-point contrasts. It lies outside this task's 48-frame limit.

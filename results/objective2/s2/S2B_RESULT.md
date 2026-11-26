# S2b result note

S2 K3: fail (fail_replan); checks_failed: s2r_m30_VB76, check 5 (C2_RESULT.md). S2b FR: pass. Valid far references: 1 of 2.

Written 2026-11-26, after E (attempt 1, 2026-11-24), its independent check and the cross-instance check. By
`S2B_PLAN.md` section 9 step 7 this note reports E's blocks by reference, with their labels, and draws no inference
beyond description and the readings of the plan. Every number below is copied from `s2b/E_output.txt` unless a
source is named. The FR note is `FR_RESULT.md`; the outputs of G2 and of the section 6b read are
`c2_diagnostic/g2_output.txt` and `c2_diagnostic/fr_geom_read_output.txt`.

## 1. What ran

- E ran once: attempt 1, 2026-11-24T01:16:15Z, at commit `98bb606b030d4f1da28a23b44152a0e0c0bf0e19`, route C4B-NOTRUN
  (fr done, FR pass; c3b done, an A1 tier computable; C4b not run by decision, amendment 2026-11-16a).
- Last line: "E exit code: 0". Every integrity check is "ok"; every cross-check is "ok" (one XC-PARTS item "not
  evaluated", as printed).
- sha256: `E_output.txt` `3273f0a2241ecd4cc636f073f7bbfac6666db6719102de7440df03419ed34e12`; `fig_s2b_e_fk.csv`
  `53c57942348620c296794bc473d0be80ad980ee837ca2a65b01158e0bce81e56`; `fig_s2b_e_fk_meta.csv`
  `b2277c3bc9630d0cacf39e62c678520bc49fb62e99138dc51e8d5a89787ad7ad`.
- Archives read: c1, c2 and fr (public); c3b (private; `MANIFEST.sha256` sha256
  `5279cdd3d5d67e714bb3733eca8a454c47baa9b24d54c4f82b634c0ce97aa68c`, `C3B_NOTE.md`; verify record "verify c3b: 3 gate
  files, 0 differ").

## 2. Block 1, far block (C2 relaxations 5-8; m30, Sr at Pb76)

- E_b^A1(Pb76) = -5.01 meV (gate N of C1: -5.0 meV); E_b^A2(Pb76) = 16.27 meV; δ_far(Pb76) = 21.28 meV.
- This far reference is invalid (K3: s2r_m30_VB76 fails check 5), so these values are reported only.
- Per-relaxation items, the tail differences and the cross-checks: `E_output.txt`, block 1, sections 1.1 to 1.4.

## 3. Block 2, FR block (m30, Cs at FA188)

- E_b^A1(FA188) = -12.01 meV; E_b^A2(FA188) = -14.17 meV; δ_far(FA188) = -2.16 meV. FR-1 and FR-2 pass, as the
  decision recorded on the node (XC-FR1-DEC, XC-FR2-DEC ok).
- Per-relaxation items and step 0: block 2, sections 2.1 to 2.4. The FR note is `FR_RESULT.md`.

## 4. Block 3, MACE and deferred-C1 block

Reported by reference: the q = 0 rows (Sr76, Cl138, Cs128, GA128), the invalid cells of C1, C2 and FR, the
zero-shot MACE E_b of the pilot cells (noise, start set, pose), the DFT residual forces of the A1 cells outside
Pb136, the pose-pilot spreads, determinism and the throughput row (`E_output.txt`, block 3; coverage list at the
end of the output). Pb136 items are excluded from block 3 and deferred to block 5.

## 5. Block 4, the A1 tier of C3b (8 production hosts; MACE geometry, DFT single point)

Label on every value: "far-site reference: FR, m30 FA188, valid; fixed-geometry DFT; relaxation bias not bounded.
Far-site A2 reference valid at pilot host m30, FA188 only [...]. Valid far references: 1 of 2. No production-host
far site is tested at A2. S2 K3: fail_replan; its value test was not reached, and no A2 test of the first shell
gates this tier." No calibrated tier is formed (C4b not run), so no class below is a validated class.

| dopant | n_d | mean Y (meV) | s_Y (meV) | I^A1 (meV) | A1-tier class printed by E |
|---|---|---|---|---|---|
| Sr | 8 | 123.65 | 53.60 | [60.44, 186.86] | repels |
| Cl | 7 | 0.95 | 15.78 | [-20.05, 21.94] | no first-shell interaction beyond k_BT |
| Cs | 7 | -21.35 | 29.01 | [-59.96, 17.25] | not resolved |
| GA | 6 | -13.20 | 9.50 | [-27.98, 1.58] | no class (A1-tier control failed: C4); rule V: not resolved |

- Y_h per host (meV; "-" = not a valid host for that dopant):

| host | Sr | Cl | Cs | GA |
|---|---|---|---|---|
| m06 | -0.40 | - | - | - |
| m02 | 155.03 | 4.50 | 22.94 | -4.86 |
| m16 | 116.53 | -3.47 | -20.49 | -13.26 |
| m12 | 114.25 | 12.05 | -15.98 | -29.05 |
| m32 | 133.92 | 6.41 | -14.08 | -9.03 |
| m26 | 166.47 | -8.68 | -51.84 | -4.16 |
| m22 | 158.25 | 22.38 | -5.85 | - |
| m23 | 145.17 | -26.55 | -64.18 | -18.83 |

- Invalid cells: nine, all on check 5 under both readings (seven in m06, one in m22, one in m26); no cell is valid
  under the identical-atom reading only. m06 is not a valid host for Cl, Cs and GA, m22 not for GA.
- Ranking (reported only; interval quantile 0.9975): Sr - Cl 140.43 [96.48, 184.38]; Sr - Cs 162.73 [102.64,
  222.82]; Sr - GA 151.76 [121.52, 182.00]; Cl - Cs 22.30 [-10.53, 55.13]; Cl - GA 10.57 [-23.40, 44.55]; Cs - GA
  -10.74 [-70.23, 48.75] meV.
- Far-bias sensitivity (|δ_far(FA188)| = 2.16 meV added to every half-width): no displayed class changes.
- Controls: gate N, C2 and C3 true for all four; C4 true for Sr, Cl, Cs and false for GA (6 of 8 hosts); no
  heterogeneity flag; the dopant-specific rule applies to none.
- Required hosts for t·s_Y/√n < k_BT (and < k_BT/2): Sr 31 (113); Cl 6 (13); Cs 12 (36); GA 4 (7).
- Per-site values, zero-shot MACE E_b beside every DFT value, and the DFT residual forces of the 544 cells:
  sections 4.2, 4.3 and 4.6.
- Figures: `figures/fig_s2b_e_block4_Yh.png` (Y_h per host and dopant, the mean and I^A1; host m06 marked; band
  ±k_BT = ±25.7 meV; script `figures/fig_s2b_e_block4_Yh.py`, which parses E's output) and E's own figure of the
  relaxations it read, `figures/fig_s2b_e_fk.png` (script `figures/fig_s2b_e_fk.py`, from E's source data). Both
  captions carry the header line of this note. The E figure was rendered without its panel-alignment audit, which
  was not available on the machine that built it; the QA of the C1 and C2 figures is to that extent not met.

## 6. Block 5, the hinge

Not opened. Deferred and unread: C2 relaxations 1-4 (the Pb136 quartet of m30), E_b^A1(Pb136), E_b^A2(Pb136),
δ_Sr,m30, and the other Pb136 items that E lists under block 5. They stay in the public c1 and c2 archives and are
read by `E_hinge_output.txt` at the first of: the evaluation of a later pre-registration that names them as data, in
rules committed before 2027-06-30; or 2027-06-30.

## 7. The independent check of block 4 (after E; changes nothing in E)

Report: `s2b/records/E_ADVERSARIAL_CHECK.md`. Its statements, in its own terms:

- **Block 4 stands as printed.** Of 41 300 quantities recomputed from the 544 raw outputs and the records with an
  independent parser, 41 295 agree at the printed precision. The five that differ: the count "files listed in
  c3b/MANIFEST.sha256: 2551" (the manifest lists 2550 files; the printed number includes the manifest itself), and
  four bounds of the far-bias sensitivity that differ by 0.01 meV because δ_far is printed to two decimals.
- The nine invalid cells, n_d = 8, 7, 7, 6 and the four classes are reproduced from the plan's text. No value from
  an invalid cell or an invalid host enters a pooled statistic.
- **Host m06 is an outlier for Sr** (post hoc). Y_h = -0.40 meV against 114.25 to 166.47 meV at the other seven
  hosts (their mean 141.37, SD 20.51 meV). m06 carries most of s_Y: without it I^A1 would be [114.08, 168.67]. The
  zero-shot MACE values of the same geometries are lowest at m06 as well. "Sr repels" holds with any one host left
  out (lowest lower bound 44.30 meV) and at each first-shell site separately. Why m06 differs is not established.
- **The Cl class sits close to a boundary** (post hoc). With any one of five hosts left out, or at an interval
  quantile above 0.9970, rule V gives "not resolved". The class describes the mean over the shell and the hosts:
  22 of the 55 valid per-site values of Cl exceed k_BT in magnitude (range -160.10 to +88.43 meV).
- Per-site t(0.975) intervals are printed for all 16 sites and are not adjusted for their number; only the two Sr
  sites exclude zero under every adjustment tried.
- The raw E_b of the nine quartets with an invalid cell are not printed by E ("not formed"); from the complete
  single points they are all negative, -17.27 to -295.28 meV. They enter nothing.
- Not checked by it: the identity of the archived inputs with the hashes of the meta files (its corrected check was
  not run), a recomputation of check 5 from the structures, the label texts, and E's files other than
  `e_block4.py`. The geometry description of m06 was not run.

## 8. The cross-instance check (after E; rule in the roadmap update 2026-11-24 (b))

- 75 of the 544 single points ran on the first instance of the compute node (all 68 of m06 and 7 of m02); 469 on
  the second.
- Eight single points were run again on the second instance: the m06 Sr quartet at site 124, `s2_m02_host`,
  `s2_m02_VA92`, and two controls of the second instance. All eight print the archived total energy digit for digit
  at 1e-8 Ry, from inputs that are byte-identical to the archived ones (`c3b_verify/cross_instance_check.csv`).
  Reading by the rule: "reproducible across the instances at this sample" (6 of 75).
- The list was fixed after E had run and before the per-host rows of block 4 were read; the reruns were launched
  after those rows (among them the raw E_b of the m06 quartet) had been read. The check is therefore not blind.
- The m06 Sr value is therefore not an effect of the instance at this sample.

## 9. What is public, what stays private, and one deviation

1. **`s2b/E_output.txt` in this repository differs from the file E wrote in one line.** Line 84 of the original
   prints the absolute path of the private root on the machine that ran E; the repository admits no local path.
   In the public copy that path is replaced by "<private root>" and nothing else is changed. sha256 of the file E
   wrote: `3273f0a2241ecd4cc636f073f7bbfac6666db6719102de7440df03419ed34e12`; of the public copy:
   `30804fefabc8fff35866cbcec5d8dccf8ee0f9f67b2b5d80e95bc66f8dadafb5`. The original is kept privately as a commit
   made before this note. This is a deviation from "committed unedited" (`S2B_PLAN.md` section 7), decided by the
   analyst under the PI's delegation and stated here. The two source-data files of E's figure are unedited.
2. **The c3b archive stays private for now** (about 29 MB of raw outputs and records). Its manifest hash is public
   in `C3B_NOTE.md`. Publishing it is left to a later decision; nothing in this note depends on it.
3. The comparison table and the scripts of the independent check are kept with the private archive.

## 10. Corrections to earlier records

- `C3B_NOTE.md` (not edited; E recorded its sha256): 75, not 76, single points ran on the first instance;
  "published" in the campaign log is a submission, so its intervals are between submissions; three first tries
  are archived. (Roadmap update 2026-11-24 (b).)
- Roadmap update 2026-11-24 (b), item 3: two earlier versions each gave half of the sequence in which the rerun
  list was fixed and E's per-host rows were read; the version of commit `a266674` states the sequence.
- E's output: the manifest count label (section 7). No rerun of E follows from it.
- `C3B_NOTE.md` section 9 announces the cross-instance check as planned; it has been made (section 8).

## 11. What this note does not claim

- No class here is validated against relaxed DFT (A2) in the first shell; the tier is fixed-geometry.
- One of two far references is valid, at a pilot host; no production-host far site is tested at A2.
- The hinge (δ for Sr at m30) is unread.
- The post hoc analyses of section 7 are descriptions; none changes a class of E.

## 12. What follows

- The fixed-geometry D3(BJ) sensitivity study pre-registered in `D3BJ_AMENDMENT.md`, which this note releases.
- A pre-registration that names the hinge as data, so that the one relaxed first-shell quartet of Sr can be read
  against rules fixed in advance.
- A post hoc diagnosis of host m06 from the archived geometries.
- No DFT relaxation campaign (C4b) is scheduled. Whether node time is spent on relaxed quartets is decided after
  the three items above.

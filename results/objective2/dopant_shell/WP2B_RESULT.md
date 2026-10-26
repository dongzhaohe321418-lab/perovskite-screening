# WP2b — zero-shot MACE-MP-0 vs fixed-geometry DFT on the corpus NEB bands (2026-10-26)

**Pre-registered verdicts (PLAN criteria 3 and 5; amendments a, g, h).**
- **Criterion 3 FAILS**: RMS(MACE − DFT) of the paired ΔE_a = 31.2 meV > 20 meV, and 3 of the 18
  pairs change class across the ±59.5 meV band. Under the corpus E_a definition (sensitivity, §2)
  it also fails (RMS 27.0 meV, 4 crossings).
- **Criterion 5 FAILS** at every MACE stationary point (0/54 minima, 0/27 saddles).
- Consequences, as pre-registered: the MACE corpus numbers are downgraded; the corpus equivalence
  claim is re-stated at DFT level (§3); and, because criterion 5 failed, the single-point energies
  must carry the WP2e relaxation bias as an error bar. **WP2e is still running, so every DFT value
  here — and the §3 re-statement — is provisional and has no such error bar yet.** All DFT values
  are single points on MACE geometries: a fixed-path diagnostic, not relaxed DFT barriers.

## 1. What was computed

9 hosts (m05, m06, m08, m12, m15, m20, m21, m30, m32) × {undoped, GA, Sr} × MACE CI-NEB images
{0, 2, 3, 4, 6} = 135 QE single points, all converged (13–14 SCF iterations: 14 in 115, 13 in 20),
plus the three WP2a sensitivity rows (14, 14 and 23 iterations). Plain PBE, pslibrary 1.0.0 US,
50/400 Ry, one k-point at the folded R point, Gaussian 0.005 Ry, nspin 1, free energy F throughout
(`scripts/30`). MACE-MP-0 medium (float64) recomputed on the identical frames (`scripts/32`).
**E_a** = max over images {2, 3, 4} of E_i − E_0 along the MACE path (the definition of `scripts/32`
as first committed, e1556a9, before any WP2b result; it is negative when image 0 is not a DFT
minimum). ΔE_a = E_a(dopant) − E_a(undoped) in the same host. Raw inputs/outputs: `wp2b/raw/`;
analysis: `wp2b/wp2b_validation.json`, `wp2b/wp2b_frames.csv`; figure: `figures/fig_wp2b_validation.*`.

## 2. Criterion 3 — paired ΔE_a (meV)

| host | dopant | ΔE_a DFT (F) | ΔE_a DFT (σ→0) | ΔE_a MACE | MACE − DFT | class DFT / MACE | ΔE_a DFT, corpus def. |
|---|---|---|---|---|---|---|---|
| m05 | GA | -13.7 | -14.2 | -11.4 | +2.3 | +0 / +0 | -13.7 |
| m05 | Sr | -61.0 | -62.1 | -30.2 | +30.9 | -1 / +0 | -61.0 |
| m06 | GA | -40.2 | -39.6 | -17.0 | +23.3 | +0 / +0 | -40.2 |
| m06 | Sr | +0.8 | -0.4 | +19.2 | +18.4 | +0 / +0 | +0.8 |
| m08 | GA | +11.1 | +11.0 | +4.5 | -6.5 | +0 / +0 | +11.1 |
| m08 | Sr | -38.4 | -39.1 | -14.7 | +23.7 | +0 / +0 | -38.4 |
| m12 | GA | -15.9 | -15.9 | -38.0 | -22.1 | +0 / +0 | -15.9 |
| m12 | Sr | -8.2 | -9.1 | +13.8 | +22.0 | +0 / +0 | -8.2 |
| m15 | GA | +79.2 | +78.7 | +71.7 | -7.5 | +1 / +1 | +56.7 |
| m15 | Sr | +110.3 | +109.9 | +7.9 | -102.5 | +1 / +0 | +87.8 |
| m20 | GA | +53.0 | +52.7 | +33.7 | -19.3 | +0 / +0 | +37.2 |
| m20 | Sr | +132.9 | +133.0 | +129.3 | -3.6 | +1 / +1 | +117.1 |
| m21 | GA † | -14.3 | -14.7 | -14.3 | -0.1 | +0 / +0 | -14.3 |
| m21 | Sr † | -37.4 | -38.4 | -7.8 | +29.7 | +0 / +0 | -33.8 |
| m30 | GA | +94.8 | +93.7 | +72.5 | -22.2 | +1 / +1 | +94.8 |
| m30 | Sr | -2.9 | -5.5 | -32.6 | -29.8 | +0 / +0 | -2.9 |
| m32 | GA | -46.8 | -46.7 | -63.2 | -16.4 | +0 / -1 | -46.8 |
| m32 | Sr | -25.5 | -27.1 | -1.3 | +24.2 | +0 / +0 | -25.5 |
class: −1 below −59.5, 0 inside, +1 above +59.5 meV. † the DFT maximum lies at image 2 and still
rises towards the unsampled image 1, so the fixed-path DFT E_a of that band (m21 GA, m21 Sr) is a
lower bound (the bracketing assumption of amendment a holds for MACE in all 27 bands, not for DFT
in these two).

**RMS(MACE − DFT) = 31.2 meV, mean −3.1 meV; crossings: m05 Sr, m15 Sr, m32 GA. Verdict: fail**,
decided on raw F (amendment h item 1). Secondary, not a criterion: RMS 15.9 meV for GA and 41.1 meV
for Sr. σ→0 energies (E₀ = F + TS/2, reported beside F because the degauss row failed, §6) change
the paired ΔE_a by at most 2.7 meV (2.65 meV, m30 Sr; mean −0.6 meV).

**Definition sensitivity.** The corpus defines E_a as E.max() − E_0 over every image, including
image 0, so it is never negative (`scripts/22`). Applied to the sampled images {0, 2, 3, 4, 6} it
changes the three bands whose fixed-path DFT "barrier" is negative (last column) and gives RMS
27.0 meV, mean +1.0 meV, and 4 crossings (m05 Sr, m15 GA, m15 Sr, m32 GA): still a fail.

## 3. Pre-registered consequence — the corpus claim at DFT level (provisional)

Same test as the corpus (`paired_pilot/CORPUS108_RESULT.md`: Student-t 95% CI of the paired ΔE_a
entirely inside ±59.5 meV; TOST p), on the 9 WP2b pairs per dopant. **Sample:** these are 9 of
the 11 corpus GA pairs (m10, m18 have no DFT value) and 9 of the 12 corpus Sr pairs (m04, m14, m27
have none; m14, the most extreme corpus pair at −139.8 meV, is a hinge-Sr host by the corpus
construction). The margin is (59.5 − |widest CI bound|)/59.5.

| | DFT, pre-registered E_a (F) | DFT (σ→0) | DFT, corpus E_a def. | MACE, same 9 pairs | MACE corpus (n = 11 / 12) |
|---|---|---|---|---|---|
| GA | +11.9 ± 51.7; CI [−27.8, +51.6]; 13.3% margin; TOST p 0.012 | CI [−27.8, +51.1]; 14.1% | CI [−28.4, +43.7]; 26.5% | CI [−31.6, +40.2]; 32.5% | CI [−25.0, +38.6]; 35.1% |
| Sr | +7.9 ± 67.6; CI [−44.1, **+59.8**]; **outside by 0.3 meV**; TOST p 0.026 | CI [−45.5, +59.1]; 0.6% | CI [−41.8, +49.8]; 16.4% | CI [−28.0, +46.6]; 21.7% | CI [−42.2, +33.6]; 29.1% |

(mean ± sd in meV; CI = 95% Student-t.)

- **GA**: on fixed MACE paths the DFT single-point ΔE_a lies inside ±59.5 meV under every
  definition (13.3–26.5% margin), against 32.5% for MACE on the same 9 pairs. Provisional until the
  WP2e error bar exists; not a statement about relaxed DFT barriers.
- **Sr**: under the pre-registered definition the 95% CI misses the band by 0.3 meV (F) or meets it
  with 0.6% margin (σ→0); under the corpus definition, which floors the three negative fixed-path
  barriers at 0, it is inside with 16.4% margin. **Equivalence of Sr to no effect is therefore not
  established at DFT level: the verdict depends on the E_a definition and the smearing estimator,
  each within a few meV.** Of the drop from the corpus's 29.1% margin, 7.4 points come from the
  change of sample (MACE on these 9 pairs: 21.7%) and the rest from the change of level.

## 4. Diagnostics (exploratory; none changes a verdict)

- **MACE minima are not DFT minima.** Residual DFT force RMS 0.143–0.175 eV/Å (max 0.33–0.45 eV/Å)
  at every image 0/6, and the same at image 3; the residual sits mainly on the FA cation (WP2a).
  Per-frame force RMSE MACE vs DFT: median 0.091 eV/Å (0.082–0.101).
- **Fixed-path DFT "barriers" can be negative.** m15 undoped −22.5, m20 undoped −15.8, m21 Sr −3.6
  meV: along these MACE paths the DFT energy falls from image 0 (m15 undoped image 6 lies 279 meV
  below image 0). In m21 (GA, Sr) the DFT maximum is at image 2, outside the bracket (†).
- **m15 Sr.** Its error (−102.5 meV) is specific to the Sr band: the same undoped band (E_a −22.5
  meV) gives a GA-pair error of only −7.5 meV, because MACE overestimates the m15 undoped and GA
  barriers by 70–78 meV but puts the Sr barrier 25 meV below DFT. This matches the placement
  pattern below.
- **MACE overestimates the along-path barrier where it is low.** For m05, m06, m20 and m21 the MACE
  E_a exceeds DFT by 59–117 meV in all three systems (m15: by 70–78 meV for undoped and GA, but
  25 meV below DFT for Sr); for m08, m12, m30 and m32 they agree within 35 meV:

| host | E_a DFT undoped / GA / Sr | E_a MACE undoped / GA / Sr |
|---|---|---|
| m05 | 83.5 / 69.8 / 22.5 | 170.1 / 158.7 / 140.0 |
| m06 | 133.1 / 92.9 / 134.0 | 192.1 / 175.1 / 211.3 |
| m08 | 199.2 / 210.3 / 160.8 | 209.3 / 213.8 / 194.6 |
| m12 | 248.5 / 232.7 / 240.4 | 238.3 / 200.3 / 252.1 |
| m15 | -22.5 / 56.7 / 87.8 | 55.1 / 126.8 / 63.0 |
| m20 | -15.8 / 37.2 / 117.1 | 71.3 / 105.0 / 200.5 |
| m21 | 33.8 / 19.6† / -3.6† | 93.6 / 79.2 / 85.8 |
| m30 | 211.2 / 306.0 / 208.3 | 220.1 / 292.6 / 187.4 |
| m32 | 177.2 / 130.4 / 151.7 | 175.2 / 112.0 / 173.9 |
- **The Sr error depends on the Sr placement (exploratory; n = 2 vs 7).** Sr sits on the Pb nearest
  the vacancy, which is the hinge Pb holding the migrating iodide in m15 and m30 and the far-side
  Pb in the other seven WP2b hosts (re-derived with the corpus construction; cf. the uncontrolled
  factor noted on 2026-10-18). Far-side Sr: MACE − DFT = +30.9, +18.4, +23.7, +22.0, −3.6, +29.7,
  +24.2 meV (mean +20.7: MACE systematically less favourable than DFT). Hinge Sr: −102.5 (m15) and
  −29.8 (m30). Hinge share: 2/9 here, 3/12 in the corpus Sr set (m14 added), 16/36 in the pool.
  WP2c tests hinge and flank Sr sites explicitly.
- **Fermi-level shift of the neutral-vacancy cell (amendments g, h).** Dopant-induced shift of the
  raw E_F (not potential-aligned; at m05 semicore alignment changed it by up to ~10 meV) at image 0:
  GA +17.3 meV (12.4–21.2), Sr +54.8 meV (39.8–68.0). For Sr its change from image 0 to 3 is −14.4
  meV on average (−3.4 to −40.8; −40.8 and −39.7 in the two hinge hosts). Over all 9 Sr pairs it
  correlates with the error (Pearson r = 0.85), carried by the two hinge hosts, with the sign
  opposite to the single-electron expectation (removing it would raise the Sr error RMS from 41.1
  to 55.0 meV): it does not explain the hinge errors. In the 7 far-side hosts it has the expected
  sign (r = −0.67), and removing it would lower their mean error from +20.7 to +13.7 meV (RMS 23.3 →
  16.5 meV): a candidate contribution to the far-side offset. Reported, not used.

## 5. What this does and does not show

- It shows that zero-shot MACE-MP-0 does not reproduce the DFT energy differences along its own
  paths to the pre-registered 20 meV under either E_a definition, and that its stationary points
  carry DFT forces three times the gate. The MACE corpus numbers are downgraded accordingly.
- It does not give relaxed DFT barriers, and the §3 re-statement is provisional. With residual
  forces of ~0.16 eV/Å RMS, the single-point energies carry a relaxation bias of unknown size and
  sign. WP2e (DFT relaxation of the m30 image-0 endpoints of all three systems, now running)
  estimates the endpoint part of it for one host; the saddle-side relaxation is not covered. A
  DFT-NEB on a subset of hosts, or a fine-tuned potential (WP3) whose minima pass criterion 5, is
  needed before any barrier difference is stated at DFT accuracy.

## 6. WP2a sensitivity rows (amendment c item 6), m30 undoped, R point

- degauss 0.0025 vs 0.005 Ry: F(img3) − F(img0) = 216.09 vs 211.21 meV, a shift of **+4.9 meV > 3
  meV: fails**. As pre-registered, the σ→0 estimate E₀ = F + TS/2 is reported beside F (§2, §3);
  all campaigns stay at 0.005 Ry for consistency. E₀ is not σ-converged at these widths: it moves
  by 5.6 meV between the two smearings (214.3 / 219.9 meV), more than F. The production single-band
  E_3 − E_0 therefore lies 6.5–8.7 meV below the best σ→0 estimates (E₀ at 0.0025 Ry: 219.9 meV; F
  extrapolated in σ²: 217.7 meV). The ≤ 2.7 meV F/E₀ difference on the paired ΔE_a (§2) compares two
  estimators at one smearing; the smearing sensitivity of the paired ΔE_a itself was not tested.
- nspin 2 vs 1 (img0): total magnetisation 0.01 μB, F higher by 1.6 meV: no magnetic solution;
  nspin 1 stands.

## 7. Verification

Every number and statement in a first draft was recomputed from the raw outputs by an adversarial
check (43 agents, 264 claims, two skeptics per finding, completeness critic). It found the E_a
definition difference from the corpus, the sample difference behind the margin comparison, the
missing provisional status under criterion 5, an incorrect reading of the m15 pair, the far-side
band-term split, the unbracketed m21 maxima, an over-strong smearing statement and several
0.1 meV double-rounding errors; all are corrected above, and `scripts/32` now differences unrounded
energies and stores three decimals.

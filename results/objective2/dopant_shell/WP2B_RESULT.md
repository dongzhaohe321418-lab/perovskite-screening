# WP2b — zero-shot MACE-MP-0 vs fixed-geometry DFT on the corpus NEB bands (2026-10-26)

**Pre-registered verdicts (PLAN criteria 3 and 5, amendments a, g, h): criterion 3 FAILS
(RMS error of the paired ΔE_a 31.2 meV > 20 meV; 3 of 18 pairs change class across the ±59.5 meV
band). Criterion 5 FAILS at every MACE stationary point (0/54 minima, 0/27 saddles).** As
pre-registered, the corpus equivalence result is re-stated at DFT level (§3) and the MACE
numbers are downgraded. The DFT values are single points on MACE geometries: a fixed-path
diagnostic, not relaxed DFT barriers (§5).

## 1. What was computed

9 hosts (m05, m06, m08, m12, m15, m20, m21, m30, m32) × {undoped, GA, Sr} × MACE CI-NEB images
{0, 2, 3, 4, 6} = 135 QE single points, all converged (14 SCF iterations each), plus the three
WP2a sensitivity rows. Plain PBE, pslibrary 1.0.0 US, 50/400 Ry, one k-point at the folded R point,
Gaussian 0.005 Ry, nspin 1, free energy F throughout (`scripts/30`). MACE-MP-0 medium (float64)
recomputed on the identical frames (`scripts/32`). E_a = max over images {2, 3, 4} of E_i − E_0
along the MACE path; ΔE_a = E_a(dopant) − E_a(undoped) in the same host. Raw inputs/outputs:
`wp2b/raw/`; analysis: `wp2b/wp2b_validation.json`, `wp2b/wp2b_frames.csv`; figure:
`figures/fig_wp2b_validation.*`.

## 2. Criterion 3 — paired ΔE_a (meV)

| host | dopant | ΔE_a DFT (F) | ΔE_a DFT (σ→0) | ΔE_a MACE | MACE − DFT | class DFT / MACE |
|---|---|---|---|---|---|---|
| m05 | GA | -13.7 | -14.2 | -11.4 | +2.3 | +0 / +0 |
| m05 | Sr | -61.0 | -62.1 | -30.1 | +30.9 | -1 / +0 |
| m06 | GA | -40.2 | -39.6 | -17.0 | +23.3 | +0 / +0 |
| m06 | Sr | +0.8 | -0.4 | +19.2 | +18.4 | +0 / +0 |
| m08 | GA | +11.1 | +11.0 | +4.5 | -6.5 | +0 / +0 |
| m08 | Sr | -38.4 | -39.0 | -14.7 | +23.7 | +0 / +0 |
| m12 | GA | -15.9 | -15.9 | -38.0 | -22.1 | +0 / +0 |
| m12 | Sr | -8.2 | -9.1 | +13.8 | +22.0 | +0 / +0 |
| m15 | GA | +79.2 | +78.7 | +71.7 | -7.5 | +1 / +1 |
| m15 | Sr | +110.3 | +109.9 | +7.8 | -102.5 | +1 / +0 |
| m20 | GA | +53.0 | +52.7 | +33.7 | -19.3 | +0 / +0 |
| m20 | Sr | +132.9 | +133.0 | +129.3 | -3.6 | +1 / +1 |
| m21 | GA | -14.3 | -14.7 | -14.3 | -0.1 | +0 / +0 |
| m21 | Sr | -37.4 | -38.4 | -7.8 | +29.6 | +0 / +0 |
| m30 | GA | +94.8 | +93.7 | +72.5 | -22.2 | +1 / +1 |
| m30 | Sr | -2.9 | -5.5 | -32.6 | -29.8 | +0 / +0 |
| m32 | GA | -46.8 | -46.7 | -63.2 | -16.4 | +0 / -1 |
| m32 | Sr | -25.5 | -27.1 | -1.3 | +24.2 | +0 / +0 |
class: −1 below −59.5, 0 inside, +1 above +59.5 meV. **RMS(MACE − DFT) = 31.2 meV, mean −3.1 meV;
band crossings: m05 Sr, m15 Sr, m32 GA. Verdict: fail** (amendment h item 1: decided on raw F; the
band-term estimates of §4 are never used to reclassify). Secondary, not a criterion: RMS 15.9 meV
for GA and 41.1 meV for Sr. σ→0 energies (E₀ = F + TS/2, reported beside F because the degauss row
failed, §6) change the paired ΔE_a by at most 2.6 meV (mean −0.6 meV).

## 3. Pre-registered consequence — the corpus claim at DFT level

Same test as the corpus (`paired_pilot/CORPUS108_RESULT.md`: Student-t 95% CI of the paired ΔE_a
entirely inside ±59.5 meV; TOST p), on the 9 WP2b pairs per dopant:

| | DFT on MACE path (F) | DFT (σ→0) | MACE, same 9 pairs |
|---|---|---|---|
| GA | +11.9 ± 51.7 (sd); CI [−27.8, +51.6]; inside; TOST p 0.012 | CI [−27.8, +51.1]; inside | CI [−31.6, +40.2]; inside |
| Sr | +7.9 ± 67.6; CI [−44.1, **+59.8**]; **not inside**; TOST p 0.026 | CI [−45.5, +59.1]; inside | CI [−28.0, +46.6]; inside |

**GA remains equivalent to no effect at DFT level (13% margin). For Sr the upper CI bound sits on
the margin (59.1–59.8 meV depending on the smearing treatment): equivalence is not demonstrated
with any margin at DFT level**, against a 29% margin in the MACE corpus. The DFT spread is larger
than the MACE spread for Sr (sd 67.6 vs 48.5 meV), driven by m15 (below).

## 4. Diagnostics (exploratory; none changes a verdict)

- **MACE minima are not DFT minima.** Residual DFT force RMS 0.143–0.175 eV/Å (max 0.33–0.45 eV/Å)
  at every image 0/6, and the same at image 3. The residual sits mainly on the FA cation (WP2a).
  Per-frame force RMSE MACE vs DFT: median 0.091 eV/Å (0.082–0.101).
- **Fixed-path DFT "barriers" can be negative.** m15 undoped −22.5, m20 undoped −15.8, m21 Sr −3.6
  meV: along these MACE paths the DFT energy falls from image 0 (m15 undoped image 6 lies 279 meV
  below image 0). The m15 Sr pair (+110 meV DFT) is therefore dominated by the undoped band, not by
  Sr. In m21 (GA, Sr) the DFT maximum is at image 2, not 3.
- **MACE overestimates the along-path barrier where it is low.** For m05, m06, m20 and m21 the MACE
  E_a exceeds DFT by 59–117 meV in all three systems (m15: by 70–78 meV for undoped and GA, but
  25 meV below DFT for Sr); for m08, m12, m30 and m32 they agree within 35 meV:

| host | E_a DFT undoped / GA / Sr | E_a MACE undoped / GA / Sr |
|---|---|---|
| m05 | 83.5 / 69.8 / 22.5 | 170.1 / 158.7 / 140.0 |
| m06 | 133.1 / 92.9 / 134.0 | 192.1 / 175.1 / 211.3 |
| m08 | 199.2 / 210.3 / 160.8 | 209.3 / 213.8 / 194.6 |
| m12 | 248.5 / 232.7 / 240.3 | 238.3 / 200.3 / 252.1 |
| m15 | -22.5 / 56.7 / 87.8 | 55.1 / 126.8 / 63.0 |
| m20 | -15.8 / 37.2 / 117.1 | 71.3 / 105.0 / 200.5 |
| m21 | 33.8 / 19.6 / -3.6 | 93.6 / 79.2 / 85.8 |
| m30 | 211.2 / 306.0 / 208.3 | 220.1 / 292.6 / 187.4 |
| m32 | 177.2 / 130.4 / 151.7 | 175.2 / 112.0 / 173.9 |
- **The Sr error depends on the Sr placement (exploratory, n = 2 vs 7).** Sr sits on the Pb nearest
  the vacancy, which is the "hinge" Pb holding the migrating iodide in m15 and m30 and the far-side
  Pb in the other seven hosts (re-derived with the corpus construction; cf. the uncontrolled factor
  noted on 2026-10-18). Far-side Sr: MACE − DFT = +30.9, +18.4, +23.7, +22.0, −3.6, +29.6, +24.2 meV
  (mean +20.7: MACE systematically less favourable than DFT). Hinge Sr: −102.5 (m15) and −29.8 (m30).
  WP2c tests hinge and flank Sr sites explicitly.
- **Band term of the neutral-vacancy electron (amendments g, h).** Dopant-induced Fermi-level shift
  at image 0: GA +17.3 meV (12.4–21.2), Sr +54.8 meV (39.8–68.0). Its change from image 0 to 3 for Sr
  is −14.4 meV on average (−3.4 to −40.8; −40.8 and −39.7 in the two hinge hosts). It correlates with
  the Sr error (Pearson r = 0.85, n = 9, carried by the two hinge hosts), but with the opposite sign
  to the single-electron expectation (removing it would raise the Sr error RMS from 41.1 to 55.0
  meV), so it does not explain the MACE error. Reported, not used.

## 5. What this does and does not show

- It shows that zero-shot MACE-MP-0 does not reproduce the DFT energy differences along its own
  paths to the pre-registered 20 meV, and that its stationary points carry DFT forces three times
  the gate. The MACE corpus numbers are downgraded accordingly.
- It does not give relaxed DFT barriers. With residual forces of ~0.16 eV/Å RMS at the endpoints,
  the single-point energies carry a relaxation bias of unknown size; WP2e (DFT relaxation of the
  m30 image-0 endpoints of all three systems, now running) bounds it for one host. A DFT-NEB on a
  subset of hosts, or a fine-tuned potential (WP3) whose minima pass criterion 5, is required before
  any barrier difference is stated at DFT accuracy.

## 6. WP2a sensitivity rows (amendment c item 6), m30 undoped, R point

- degauss 0.0025 vs 0.005 Ry: F(img3) − F(img0) = 216.09 vs 211.21 meV, a shift of **+4.9 meV > 3
  meV: fails**. As pre-registered, the σ→0 estimate E₀ = F + TS/2 is reported beside F (above); all
  campaigns stay at 0.005 Ry for consistency. E₀ itself moves by 5.6 meV between the two smearings
  (214.3 / 219.9 meV), so the smearing uncertainty of a single band's E_3 − E_0 is ~5 meV; on paired
  ΔE_a the F/E₀ difference is ≤ 2.6 meV (§2).
- nspin 2 vs 1 (img0): total magnetisation 0.01 μB, F higher by 1.6 meV: no magnetic solution;
  nspin 1 stands.

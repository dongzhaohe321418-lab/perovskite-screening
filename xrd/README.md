> **INDEPENDENT SUB-PROJECT.** This directory is an experimental XRD passivator screen. It shares **no evidence chain** with the migration-barrier work (Objectives 1–2) in the rest of this repository — nothing here supports or is supported by the GA/Sr screening or the q=0/q=+1 NEB campaign. Repo-level navigation: `../RESULTS_INDEX.md`.

# Perovskite screening — XRD analysis log

Analysis of powder/thin-film XRD for the **control** perovskite sample.

| | |
|---|---|
| Sample | `perovskite#control##20260726-095651_100` |
| Scan | 5.00–50.00° 2θ, 0.05° step, 901 points |
| Radiation | Cu Kα (λ₁ = 1.540598 Å, Kα₂ modelled at 1:2) |
| Counts | 36,290 total; raw integer counts, Poisson-weighted throughout |
| Instrument | benchtop Cu Kα (**assumed** — see *Accuracy*) |
| Analysed | 2026-07-26 |

Run with `python analysis/xrd_analysis.py data/raw/<file>.txt`.

---

## Headline results

**Status: PROVISIONAL** — no instrument standard scan, no bare-substrate scan.

| Quantity | Value | Interval | Class |
|---|---|---|---|
| **Domain size D** (volume-weighted) | **43.7 nm** | 41.9 – 46.4 nm | statistical 68% CI |
| ↳ same D, instrument-width sensitivity | 43.7 nm | 38.4 – 50.3 nm | systematic (do **not** merge with above) |
| Microstrain ε | *not reported* | −2.3σ | suppressed by gate — insignificant and negative |
| Effective pseudo-cubic a | 6.2969 Å | ±0.0011 Å formal / **±0.0033 Å** model | Birge 3.00, χ²ᵣ = 9.01 |
| Zero-point offset | −0.089° | ±0.0058° formal / ±0.017° model | sample displacement |
| Degree of crystallinity | 49 – 65% | bounded range | **not** a point value |
| Bragg / total scattered | 21.9% | — | fixed-protocol comparative index |
| PbI₂-compatible peak (001) | **detected** | p = 6.4×10⁻¹⁴ (bootstrap) | 2.7% of perovskite Bragg intensity |
| Peak-to-background (220) | 64 | — | data quality |

Two uncertainty classes are reported separately throughout and must not be
combined: **±2.2 nm statistical** (counting + profile) versus
**38–50 nm systematic** (assumed instrumental resolution). They answer
different questions — the first is reproducibility on this instrument, the
second is accuracy against an absolute scale.

---

## 1. Phase identification

Eight reflections index on a pseudo-cubic perovskite cell with
N = h²+k²+l² = 1, 2, 3, 4, 5, 6, 8, 9 — every N allowed for a primitive cubic
cell is present, none missing, and no extra perovskite lines. Maximum
|observed − calculated| position residual is **0.027°**, i.e. about half a step.

Two genuine non-perovskite reflections were found (see §4 for why the detection
test matters):

| 2θ_obs | d (Å) | FWHM | area | assignment | Δd vs reference |
|---|---|---|---|---|---|
| 12.594° | 6.974 | 0.30° | 9.5 | **PbI₂ (001)**, 2H polytype | −0.005 Å |
| 30.199° | 2.948 | 0.47° | 25.9 | substrate (In₂O₃/ITO 222) | +0.027 Å |

The match is Δd = 0.005 Å against the 2H-PbI₂ (001) spacing (c = 6.979 Å).
Only the 001 line appears — expected, since PbI₂ platelets lie flat and the
basal reflection dominates. But **one reflection is not a phase
identification**, so the correct phrasing is **"PbI₂-compatible peak
detected"**, not "PbI₂ identified". And because the phase is textured, an
intensity ratio cannot be converted to a weight fraction; the honest statement
is relative: this peak carries **2.7%** of the perovskite Bragg intensity.

**Correction to an earlier figure in this log:** a combined minor-phase total
of 9.65% was recorded at one point (2.71% film + 6.94% substrate). That wrongly counted the 30.2° substrate
line as a film phase. A substrate reflection is not a secondary phase of the
film, and the film-only impurity total is **2.7%**. The pipeline now tags every
non-perovskite reflection `origin='film'` or `'substrate'` and excludes the
latter from impurity totals.

The 30.2° line is 2.4× broader than every perovskite reflection (0.47° vs
0.16–0.25°) and does not index on the perovskite cell, so it is not a perovskite
or PbI₂ feature. It matches In₂O₃/ITO (222). **This assignment is provisional** —
confirming it needs a bare-substrate scan, which is the cheapest useful
follow-up measurement.

### Lattice parameter: two different uncertainties

The refinement returns χ²ᵣ = 9.01, i.e. position residuals ~3× the fitted
errors. That is a **model discrepancy, not scatter**, so the formal error
understates the true uncertainty and must not be quoted alone:

> effective pseudo-cubic **a = 6.2969 Å**; formal fit uncertainty
> **±0.0011 Å**; model / peak-splitting uncertainty **±0.0033 Å**
> (Birge ratio √χ²ᵣ = 3.00)

Report the model-scaled value. The cause is expected at 0.05° steps:
room-temperature MAPbI₃ is tetragonal (I4/mcm) with pseudo-cubic axes differing
by ~1% (a_pc ≈ 6.26, c/2 ≈ 6.32 Å), unresolved here. So **"pseudo-cubic
effective cell" is the correct phrasing and this analysis cannot claim
Pm-3m.** Absence of the tetragonal superlattice line near 23.5° (p = 0.83) is
consistent with either a cubic phase or an unresolved tetragonal one.

## 2. Crystallinity

Two different questions get conflated under "crystallinity", and only one of
them is answerable from a single scan.

**Absolute degree of crystallinity: 46–60%, and the range is irreducible here.**
The amorphous fraction is inferred from a broad halo under the Bragg peaks, but
a very broad Gaussian is mathematically degenerate with the flat instrumental
background (air scatter, detector dark counts, fluorescence). Fitting
`A·exp(−2θ/τ) + c + halo` to the 597 peak-free channels improves χ²ᵣ from 3.78
(no halo) to 1.93–2.49 (halo present), so **a diffuse component is real** — but
its width runs to whatever bound it is given, and the recovered DOC tracks that
bound directly:

| halo σ limit | 3° | 4° | 5° | 6° | 8° |
|---|---|---|---|---|---|
| DOC | 61% | 57% | 53% | 51% | 47% |

Quoting a single DOC from this scan would be quoting the choice of bound.
Separating the halo from the flat background requires a bare-substrate scan or a
wider 2θ range.

**Comparative crystallinity: use these instead.** The correct name is
**fixed-protocol comparative crystallinity index** — these are *not*
background-independent. They still depend on scan range, the flat background,
dwell time, film thickness and instrument flux. They are valid for
control-vs-treatment **only** at identical instrument, optics, step, dwell,
sample area and normalisation (enforced by `protocol_key`):

- total perovskite Bragg intensity = **362 counts·deg**
- Bragg / total scattered = **21.9%**
- peak-to-background at 220 = **64**

## 3. Crystallite size and its accuracy

Instrumental broadening was removed by Thompson–Cox–Hastings pseudo-Voigt
deconvolution (Gaussian components in quadrature, Lorentzian components
linearly) rather than by naive FWHM subtraction, and sizes come from the
**integral breadth** β rather than FWHM, which removes the shape-dependent
Scherrer constant K.

Williamson–Hall gives a **negative** slope at −2.3σ. Negative microstrain is
unphysical, and dropping the strain term barely changes the fit quality
(χ²ᵣ 3.62 → 3.85). **The pure-size model is therefore adopted**; there is no
evidence of microstrain in this sample, and any size extracted from a WH
intercept (30.9 nm) is biased low by fitting a spurious slope.

### What actually limits the accuracy

The instrumental resolution function is assumed, not measured, and that
assumption — not counting statistics — dominates the error budget:

| assumed instrumental FWHM scale | 0.5× | 0.7× | 1.0× | 1.3× | 1.5× |
|---|---|---|---|---|---|
| D from intensity-weighted β (**adopted**) | 38.4 | 40.2 | **43.7** | 50.1 | 50.3 nm |
| D from mean of per-peak Scherrer | 41.5 | 44.9 | 53.6 | 101.4 | 107.3 nm |

**The choice of estimator matters more than the input data.** The
intensity-weighted integral breadth moves only 38→50 nm across a ±50% error in
the assumed instrument width, because it is dominated by the broad reflections
that retain size information. The arithmetic mean of per-peak Scherrer sizes
diverges (to >100 nm) because narrow reflections have their sample broadening
driven toward zero, sending individual D values toward infinity. **Reported
Scherrer sizes that average over reflections are unstable in exactly this way**,
which is why 43.6 nm — not the 55.9 nm per-peak mean — is the adopted value.

Error budget from 8000 Monte-Carlo draws (sampling peak-width errors, profile
mixing η, instrumental width ±25%, η_inst 0.30–0.80, K 0.89–1.00):

- statistical only: ±2.1 nm (5%)
- statistical + systematic: ±3.0 nm (7%)
- the instrumental assumption contributes ~49% of the total variance

**A LaB₆ or Si standard scan on this instrument would cut the size uncertainty
roughly in half** and is the single highest-value follow-up.

### Caveat on interpretation

This is **X-ray crystallite (domain) size, not SEM grain size.** The two differ
whenever grains are polycrystalline or contain low-angle boundaries; XRD
domain size is a lower bound on grain size and the two commonly disagree by
2–10× in perovskite films. Do not compare 43.6 nm against an SEM number
without saying which quantity each is.

Note also that per-reflection sizes span 37–84 nm with an angular trend. With
strain excluded, this residual scatter is most likely anisotropic domain shape
(plus the texture in §4) — resolvable only with an anisotropic broadening model
and more reflections than 8.

## 4. Texture — and a methodological correction

Harris texture coefficients were computed against a **calculated** random-powder
reference (multiplicity × Lorentz-polarisation × |F_hkl|², with Cromer–Mann
scattering factors and Pb/I/MA thermal factors), not against relative
intensities alone. This matters: the strongest observed reflection is 220, while
the strongest *calculated* reflection is 100 — so an eyeball comparison of peak
heights would have inverted the conclusion.

TC ranges 0.22 (100) to 2.39 (300), against 1.0 for a random powder: the film is
**strongly textured**, with ⟨hh0⟩/⟨h00⟩ planes over-represented and low-index
100/200 under-represented. Two consequences: relative peak intensities cannot be
used for phase quantification in this film, and the PbI₂ figure in §1 is a
relative index rather than a weight percent.

**Locked conventions** — TC values are only commensurable between samples
computed identically, so these are frozen in the pipeline and must not vary
within a comparison set:

1. reference intensity = multiplicity × Lorentz-polarisation × |F_hkl|²
2. multiplicity from the cubic reflection table (6, 12, 8, 6, 24, 24, 12, 6)
3. |F_hkl| from Cromer–Mann factors at the **same** wavelength and refined cell
4. reflection family fixed to N = 1, 2, 3, 4, 5, 6, 8, 9 (all eight)
5. substrate-overlapping reflections excluded (here: 30.2°)
6. normalisation TC / mean(TC) = 1 over the reflections actually used

Because (6) normalises over the reflections used, a differing reflection set
silently rescales every TC — which is why the family and the exclusions are
fixed rather than chosen per sample.

### Detection: why the first pass was wrong

The initial screen used area/σ_area from the global multi-peak fit and rejected
the 12.6° line at SNR 3.0 — recording "no PbI₂ detected, <1 wt%". **That was
wrong.** In a multi-peak fit, a weak peak's area is strongly anti-correlated
with the shared background parameters, which inflates its reported error and
hides real reflections.

Replacing it with a likelihood-ratio test against a local linear background
(Bonferroni-corrected over the candidate positions) reverses the call
decisively: PbI₂ (001) gives Δχ² = 75.0. Two candidates near 21.15° and 26.33°
survive a raw p < 0.05 cut but fail Bonferroni and are treated as noise.

### The LRT null needs bootstrap calibration

The asymptotic χ²(3) distribution does **not** strictly apply here: the added
peak amplitude is bounded at A ≥ 0 and its position is searched over a window,
which is a boundary-constrained, non-regular problem. A parametric bootstrap
(Poisson resampling under the fitted local background, 250 draws) recovers an
effective dof of **1.96–2.96** across candidates, below the nominal 3.

All values below are read from `results/peak_table.csv` (same run). `2θ_seed` is
the candidate position tested; `2θ_fit` the fitted centroid:

| 2θ_seed | 2θ_fit | Δχ² | p (asymptotic) | p (bootstrap) | eff. dof | call |
|---|---|---|---|---|---|---|
| 12.60° | 12.5945° | 75.01 | 3.60×10⁻¹⁶ | 6.39×10⁻¹⁴ | 2.71 | **detected** (PbI₂-compatible) |
| 30.05° | 30.1990° | 93.76 | 3.41×10⁻²⁰ | 6.57×10⁻¹⁷ | 2.26 | **detected** (substrate) |
| 21.05° | 21.1507° | 12.86 | 4.96×10⁻³ | 5.19×10⁻³ | 2.70 | fails Bonferroni (α = 3.6×10⁻³) |
| 26.35° | 26.3308° | 13.32 | 3.99×10⁻³ | 3.75×10⁻³ | 2.90 | fails Bonferroni |

**The size of the correction is the opposite of what I first assumed.** The
bootstrap/asymptotic ratio is ×178 at 12.6° and ×1.9×10³ at 30.05°, but only
×1.05 and ×0.94 for the two marginal candidates — i.e. the calibration is large
deep in the tail and negligible near α, where it even goes *both* directions.
So it does **not** change any call here: the two detections stay overwhelming
and both marginal candidates still fail Bonferroni on either statistic. The
reason to keep the bootstrap is that the far-tail p-values would otherwise be
overstated by 2–3 orders of magnitude, not that it rescues borderline calls.

Note the bootstrap p-value is floored by the number of draws: the empirical
floor here is 1/(N+1) ≈ 4×10⁻³, so values far below that come from the
gamma-tail extrapolation fitted to the null, not from direct counting. Raise
`n_boot` before relying on a bootstrap p-value near α.

**Detection is now by bootstrap-calibrated likelihood-ratio test, never by
fitted-area SNR.**

## 5. Standardised pipeline (skill)

This analysis is now the standard measurement layer for Objective 2 XRD,
published as the **`perovskite-xrd-protocol`** skill with three modes:

- **`single`** — phase ID, effective cell, size, impurities, texture
- **`compare control treated`** — paired deltas with split uncertainties
- **`batch`** — additive / concentration series against a reference

Fixed comparison output: Δa_pc (with zero-point drift separated from real
lattice shift), instrument-corrected ΔD, film impurity / perovskite Bragg
ratio, TC changes, Bragg integral, Bragg/total, peak/background, DOC range,
per-item statistical and systematic uncertainty, and a
`VALID / PROVISIONAL / NOT_COMPARABLE` status.

Hard quality gates, each verified against this dataset:

| Gate | Behaviour |
|---|---|
| wavelength or step undeclared | halts lattice **and** size (`NOT_COMPARABLE`); explicit opt-in required to assume |
| no instrument standard | size flagged conditional |
| protocol mismatch (e.g. dwell 1 s vs 4 s) | absolute-intensity rows → `NOT_COMPARABLE` |
| WH slope insignificant or negative | microstrain suppressed, returns `None` |
| single impurity reflection | wt% blocked with a reason string |
| no bare-substrate scan | 30.2° stays `PROVISIONAL` |

The instrumental systematic is largely **common-mode** on one instrument, so ΔD
between control and treated is better determined than either absolute D — the
comparison mode reports this explicitly.

## 6. Limitations

1. Instrumental resolution assumed, not measured → dominant systematic on D (§3).
2. Absolute DOC is bounded (49–65%), not determined (§2). Use the comparative indices.
3. The 30.2° assignment to ITO/In₂O₃ needs a bare-substrate scan to confirm.
4. "Cubic" is an effective cell; tetragonal splitting is below this resolution (§1).
5. PbI₂ reported as a *relative* Bragg-intensity index, not a weight fraction,
   and phrased "PbI₂-compatible" — the phase is textured and only one
   reflection is observed.
6. Kα₂ intensity ratio fixed at 0.5 and the doublet separation held at the
   Bragg-law value rather than refined.
7. No absorption/thin-film or surface-roughness correction; texture makes
   intensity-based quantification unreliable regardless.

## 7. Recommended next measurements

1. **LaB₆ / Si standard scan** — halves the crystallite-size uncertainty.
2. **Bare substrate scan** — confirms the 30.2° line and pins the flat
   background, which would collapse the DOC range.
3. **Longer count time or wider 2θ** — the weakest reflections carry the
   anisotropy information; 2θ > 50° would add reflections for an anisotropic
   size model.
4. **SEM** for grain size, reported separately from the XRD domain size.

---

## Files

```
data/raw/          as-measured 2θ / counts
analysis/          xrd_analysis.py — full reproducible pipeline
results/           peak_table.csv, summary_metrics.csv, texture_coefficients.csv
figures/           xrd_summary.png
```

`results/peak_table.csv` carries every fitted peak with its candidate seed,
seed-to-fit offset, likelihood-ratio Δχ², asymptotic **and** bootstrap
p-values, effective dof, empirical bootstrap floor, and phase label —
including the rejected candidates, so every detection decision in this log is
auditable against the file. p-values are written at full precision
(`%.10g`); do not round them in place, as small values collapse to 0.

## Progress log

- **2026-07-26** — Control sample analysed. Pseudo-Voigt profile fitting with
  Kα doublet; pseudo-cubic indexing of 8 reflections; TCH deconvolution;
  Williamson–Hall; Monte-Carlo error budget. Established D = 43.6 ± 3.0 nm,
  a = 6.2969 ± 0.0033 Å, no significant microstrain, PbI₂ present at 2.6% of
  perovskite Bragg intensity, film strongly textured.
  Two corrections made during analysis, both now encoded in the pipeline:
  detection moved from fitted-area SNR to a likelihood-ratio test (recovered
  PbI₂, initially missed); Monte-Carlo draws no longer discarded wholesale when
  a single reflection falls sub-instrumental (was truncating the large-D tail).
  Next: standard scan + bare-substrate scan before treated samples.
- **2026-07-26 (review pass)** — Tightened before standardising, after review.
  Five substantive changes: (i) lattice error now reports formal ±0.0011 Å and
  model-scaled ±0.0033 Å separately (Birge 3.00) instead of one number;
  (ii) D reports statistical CI 41.9–46.4 nm and instrument-sensitivity range
  38.4–50.3 nm as distinct classes, never merged; (iii) Bragg/total renamed
  *fixed-protocol comparative* index — it is not background-independent, and a
  `protocol_key` now blocks absolute-intensity comparison across differing
  acquisition conditions; (iv) LRT calibrated by parametric bootstrap —
  effective dof 2.0–2.9, not 3, so asymptotic p-values are anti-conservative
  (PbI₂ unaffected at p = 6.4×10⁻¹⁴; correction is large in the far tail, ×178–1900,
  but negligible near α, so no call changes);
  (v) **substrate/film separation fixed** — the 9.65% "minor phase" figure
  (2.71% film + 6.94% substrate) wrongly counted the 30.2° substrate line as a
  film phase; film-only impurity is **2.71%**.
  Texture conventions frozen (family, multiplicity, LP, |F|, exclusions,
  normalisation). Packaged as the `perovskite-xrd-protocol` skill with
  single/compare/batch modes and six hard gates, each verified against this
  dataset (including a deliberate dwell-mismatch and an undeclared-wavelength
  test). DOC range shifted 46–60% → 49–65% after the background model was
  corrected to exclude the substrate peak from the Bragg total.
- **2026-07-26 (audit fix)** — Two export defects found by review of the saved
  tables, both now fixed at the source and re-published in the skill.
  (i) *Merge bug*: detection statistics were joined onto fitted peaks via a
  `round(1)` key, which silently dropped every row whose fitted centroid crossed
  a rounding boundary relative to its seed — 21.05→21.151, 26.35→26.331 and
  30.05→30.199, i.e. the substrate line and both marginal candidates left blank
  in `xrd/results/peak_table.csv` while the README quoted precise values for them. Replaced
  with a nearest-seed tolerance join (`attach_detection`) that also exports
  `seed_offset` and `detection_unmatched`; all 14 rows now populated.
  (ii) *Precision loss*: `.round(6)` on export flattened p-values like 3.6×10⁻¹⁶
  to `0.0`. Tables now written via `write_peak_table` at `%.10g`.
  The README detection table has been replaced with values read back from the
  saved CSV: 12.60° p_boot = 6.39×10⁻¹⁴ (was quoted 4×10⁻¹⁴), 30.05° seed /
  30.199° fit p_boot = 6.57×10⁻¹⁷ (was quoted 7×10⁻¹⁸ — an order of magnitude
  out, and mislabelled by its fitted rather than seed position), effective dof
  range 1.96–2.96 (was 2.0–2.9). **Interpretation also corrected**: the
  bootstrap/asymptotic ratio is ×178–1900 deep in the tail but ×0.94–1.05 near
  α, so calibration does *not* rescue marginal calls — its value is preventing
  overstated far-tail significance. No detection call changed.

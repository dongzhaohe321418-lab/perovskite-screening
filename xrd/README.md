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

| Quantity | Value | 68% CI | Notes |
|---|---|---|---|
| **Crystallite size D** (volume-weighted) | **43.6 nm** | 40.9 – 46.9 | integral-breadth, pure-size model — **adopted** |
| ↳ statistical error only | 43.9 nm | 42.0 – 46.3 | counting statistics + profile shape |
| ↳ envelope for ±50% error in instrumental width | 43.7 nm | 38.4 – 50.3 | dominant systematic |
| Microstrain ε | −0.03% | −0.05 – −0.02 | **−2.3σ → not significant** |
| Lattice parameter a (pseudo-cubic) | 6.2969 Å | ±0.0033 | 8 reflections, zero-shift refined |
| Zero-point offset | −0.089° | ±0.017 | sample displacement |
| Degree of crystallinity | 46 – 60% | — | model-dependent, **not** a single number |
| Bragg / total scattered intensity | 21.9% | — | background-independent, transferable |
| PbI₂ (001) | **detected** | — | 2.6% of perovskite Bragg intensity |
| Peak-to-background (220) | 68 | — | data quality |

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

The PbI₂ assignment is solid: Δd = 0.005 Å against the 2H-PbI₂ (001) spacing
(c = 6.979 Å). Only the 001 line appears, which is expected — PbI₂ platelets
lie flat on the substrate, so the basal reflection dominates. Because the phase
is strongly textured, an intensity-ratio weight fraction would be unreliable;
the honest statement is a **relative** one: PbI₂ contributes 2.6% of the
perovskite Bragg intensity.

The 30.2° line is 2.4× broader than every perovskite reflection (0.47° vs
0.16–0.25°) and does not index on the perovskite cell, so it is not a perovskite
or PbI₂ feature. It matches In₂O₃/ITO (222). **This assignment is provisional** —
confirming it needs a bare-substrate scan, which is the cheapest useful
follow-up measurement.

`a = 6.2969 Å` sits in the normal pseudo-cubic MAPbI₃ range. Note the lattice
refinement returns χ²ᵣ = 9.0, i.e. position residuals ~3× the fitted
uncertainties. At 0.05° steps this is expected: room-temperature MAPbI₃ is
tetragonal (I4/mcm), whose pseudo-cubic axes differ by ~1% (a_pc ≈ 6.26,
c/2 ≈ 6.32 Å). That splitting is unresolved here, so **"cubic" is an effective
description, not a space-group determination.** The absence of the tetragonal
superlattice line near 23.5° (p = 0.86) is consistent with either a genuinely
cubic phase or an unresolved tetragonal one.

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

**Relative crystallinity: use these instead.** They are background-model
independent and directly comparable across identically-measured samples, which
is what a control-vs-treatment screen actually needs:

- total perovskite Bragg intensity = **362 counts·deg**
- Bragg / total scattered = **21.9%**
- peak-to-background at 220 = **68**

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
used for phase quantification in this film, and the PbI₂ fraction in §1 is a
relative index rather than a weight percent.

### Detection: why the first pass was wrong

The initial screen used area/σ_area from the global multi-peak fit and rejected
the 12.6° line at SNR 3.0 — recording "no PbI₂ detected, <1 wt%". **That was
wrong.** In a multi-peak fit, a weak peak's area is strongly anti-correlated
with the shared background parameters, which inflates its reported error and
hides real reflections.

Replacing it with a likelihood-ratio test against a local linear background
(Δχ² on 3 dof, Bonferroni-corrected over 9 candidate positions, α = 0.0056)
reverses the call decisively: PbI₂ (001) gives Δχ² = 75, **p = 4×10⁻¹⁶**. The
30.2° substrate line likewise moves from "excluded" to Δχ² = 94, p = 8×10⁻²¹.
Two candidates at 21.2° and 26.3° survive the raw p < 0.05 cut but fail
Bonferroni and are treated as noise.

**Detection is now done by likelihood-ratio test, never by fitted-area SNR.**

## 5. Limitations

1. Instrumental resolution assumed, not measured → dominant systematic on D (§3).
2. Absolute DOC is bounded (46–60%), not determined (§2). Use the relative indices.
3. The 30.2° assignment to ITO/In₂O₃ needs a bare-substrate scan to confirm.
4. "Cubic" is an effective cell; tetragonal splitting is below this resolution (§1).
5. PbI₂ quantified relative to perovskite Bragg intensity, not as a weight
   fraction — the phase is textured and only one reflection is observed.
6. Kα₂ intensity ratio fixed at 0.5 and the doublet separation held at the
   Bragg-law value rather than refined.
7. No absorption/thin-film or surface-roughness correction; texture makes
   intensity-based quantification unreliable regardless.

## 6. Recommended next measurements

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

`results/peak_table.csv` carries every fitted peak with its likelihood-ratio
Δχ², p-value and phase label — including the rejected candidates, so the
detection decisions are auditable.

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

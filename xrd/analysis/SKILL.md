---
name: perovskite-xrd-protocol
description: Fixed-protocol XRD measurement layer for perovskite thin films — phase ID, effective pseudo-cubic lattice, crystallite size, PbI2/impurity indices, and texture, with statistical / systematic / model-discrepancy uncertainties kept separate and hard quality gates. Three modes — single sample, control-vs-treatment pair, and additive/concentration batch. Use for any control or additive XRD scan in an additive-screening workflow, or whenever a Scherrer size, degree of crystallinity, or phase fraction is requested from a thin-film pattern.
---

# Perovskite thin-film XRD: fixed-protocol measurement layer

This is a **comparative measurement tool**, not a Rietveld refinement. Its
purpose is to make control-vs-additive comparisons defensible, and to *refuse*
to emit precise-looking single numbers whose value is actually set by an
unstated assumption.

Helpers are loaded into the Python kernel automatically when this skill loads.

## The four rules this skill enforces

1. **Never merge uncertainty classes.** Statistical (counting + profile),
   systematic (instrumental resolution), and model-discrepancy (unresolved
   peak splitting) are reported as separate intervals. A single "±" that
   blends them is a misrepresentation.
2. **Degree of crystallinity is a RANGE, never a point value.** A broad
   amorphous halo is mathematically degenerate with the flat instrumental
   background; the recovered DOC tracks whatever halo-width bound you impose.
3. **Detection is by likelihood-ratio test, never by fitted-area SNR.** In a
   multi-peak fit a weak peak's area is anti-correlated with the shared
   background, inflating its error and hiding real reflections.
4. **No wt% from one reflection of a textured phase.** Report integrated
   Bragg-intensity ratios instead.

## Modes

### `single` — one sample
```python
meta = scan_meta(wavelength=1.540598, step=0.05, dwell=1.0, tth_range=(5,50),
                 instrument='benchtop Cu Ka', optics='Bragg-Brentano',
                 sample_area='10x10 mm', normalisation='none',
                 standard_scan=None,      # path to LaB6/Si scan if you have one
                 bare_substrate=None,     # path to bare-substrate scan
                 label='control')
res = analyse_single('scan.txt', meta=meta)
print("\n".join(report_lines(res)))
```
Returns `lattice`, `size`, `crystallinity`, `texture`, `impurities`,
`detection`, `gates`, `status`, `protocol_key`.

### `compare` — control vs treated
```python
c = analyse_single('control.txt', meta=meta_c)
t = analyse_single('treated.txt', meta=meta_t)
cmp = compare_pair(c, t, 'control', 'treated')
cmp.attrs['status']   # VALID / PROVISIONAL / NOT_COMPARABLE
```
Fixed output rows: `a_pseudocubic_A` (+ `zero_shift_deg` and
`a_shift_beyond_zero_drift`, so zero-point drift is separated from a real
lattice shift), `D_nm_instrument_corrected`, `microstrain_percent`,
`film_impurity_over_perovskite_pct`, `bragg_integrated`, `bragg_over_total`,
`peak_over_background`, `DOC_range_percent`, `texture_TC_spread` and
per-reflection `TC_hkl`. Each row carries `stat_uncertainty`,
`syst_uncertainty` and its own `status`.

The instrumental systematic is largely **common-mode** on one instrument, so
ΔD is more reliable than either absolute D. Say so when reporting.

### `batch` — additive / concentration series
```python
results, summary, comparisons = analyse_batch(
    [{'label':'control','path':'c.txt'},
     {'label':'0.5pct','path':'a.txt'},
     {'label':'1.0pct','path':'b.txt'}],
    meta=meta, reference_label='control')
```

## Hard quality gates

| Condition | Consequence |
|---|---|
| wavelength or step not declared | **HALT** lattice + size; `status=NOT_COMPARABLE`. Override only with `allow_assumed_wavelength=True`, which flags the assumption |
| no instrument standard scan | size reported as **conditional**; gate note attached |
| control/treated `protocol_key` differ | absolute-intensity rows marked `NOT_COMPARABLE` |
| WH slope insignificant or negative | `microstrain_percent=None`; reporting suppressed |
| single impurity reflection | `wt_percent=None` with a blocked-reason string |
| no bare-substrate scan | substrate-overlapping assignments stay `PROVISIONAL` |

`protocol_key` fingerprints wavelength, step, dwell, range, instrument, optics,
sample area and normalisation. Absolute intensities compare **only** on an
exact match.

## Uncertainty reporting

**Lattice.** `refine_pseudocubic` returns `e_a_formal` (weights at face value)
and `e_a_model` (formal × Birge ratio √χ²ᵣ). Report the model-scaled value:

> effective pseudo-cubic a = 6.2969 Å; formal fit uncertainty ±0.0011 Å;
> model/peak-splitting uncertainty ±0.0033 Å (Birge 3.0)

Room-temperature MAPbI₃ is tetragonal with ~1% pseudo-cubic axis difference,
usually unresolved at 0.05° steps — a large Birge ratio is expected and is
*why* the model-scaled error is the honest one. **This never determines a
space group.**

**Size.** `size_analysis` returns `D_nm`, `stat_ci68`, and `syst_range`:

> D = 43.7 nm; statistical 68% CI 41.9–46.3 nm; instrument-width
> sensitivity 38.4–50.3 nm

Use the intensity-weighted integral breadth (`D_nm`), not a mean of per-peak
Scherrer values — the latter diverges (>100 nm) as narrow peaks approach the
instrumental width. This is **X-ray domain size, not SEM grain size**; the two
differ by 2–10× in perovskite films.

**Crystallinity.** `comparative_index_bragg_over_total` is a
*fixed-protocol comparative crystallinity index* — **not**
background-independent. It depends on scan range, flat background, dwell, film
thickness and instrument flux. Valid for control-vs-treatment at identical
protocol only.

## Detection and calibration

`detect_phases` runs `lrt_bootstrap` at each candidate position with
Bonferroni correction over the number tested. Because the added amplitude is
bounded at A≥0 and the position is searched over a window, the asymptotic
χ²(3) null does **not** hold — the parametric bootstrap recovers an effective
dof near 2.0–2.9, so asymptotic p-values are **anti-conservative** for weak
candidates. Set `calibrate=False` only for a quick look.

Phrase a single-reflection identification as **"PbI₂-compatible peak
detected"**, not "PbI₂ quantified".

## Texture conventions (locked — do not vary between compared samples)

- reference I_calc = multiplicity × Lorentz-polarisation × |F_hkl|²
- multiplicity from `MULT_BY_N`; |F| from `structure_factor` at the same
  wavelength and refined cell
- reflection family fixed to `TEXTURE_FAMILY` (N = 1,2,3,4,5,6,8,9)
- reflections overlapping the substrate are excluded via `exclude_tth`
- TC normalised so mean(TC) = 1 over the reflections actually used

Compare TC only between samples analysed with the same family and exclusions —
a differing reflection set changes the normalisation and makes TC values
incommensurable. Because the strongest *observed* peak may not be the
strongest *calculated* one, never infer texture from raw peak heights.

## Substrate vs film

`impurity_report` tags each detected non-perovskite reflection as
`origin='film'` or `'substrate'`. Use `film_impurity_pct(imp)` for the
impurity total — a substrate line is not a secondary phase of the film and
must not inflate an impurity ratio. Substrate candidates are auto-flagged by
anomalous width (>1.8× median film FWHM); pass `substrate_tth=[...]`
explicitly when known.

## Exporting tables (audit trail)

Two traps, both hit in practice:

- **Join detection stats by tolerance, not a rounded key.** A fitted centroid
  can round differently from its candidate seed (seed 30.05 -> fit 30.199), and
  a `round(n)` merge key silently drops exactly those rows, leaving blank
  detection columns. Use `attach_detection(pk, det, tol=0.4)`; it also emits
  `seed_offset` and `detection_unmatched` so a bad join is visible.
- **Never round p-value columns.** `.round(6)` collapses 1e-16 to `0.0` and
  destroys the evidence. Use `write_peak_table(pk, path)`, which rounds only
  well-conditioned columns and writes floats at `%.10g`.

The bootstrap p-value is floored by draw count at ~1/(n_boot+1); values far
below that come from the gamma-tail fit, not direct counting. Raise `n_boot`
before trusting a bootstrap p near alpha. Calibration shifts the FAR tail
strongly (x10^2-10^3) but is near-neutral close to alpha, so it rarely changes
a borderline call -- it prevents overstating far-tail significance.

## Reporting checklist

- [ ] lattice quoted with formal **and** model-scaled uncertainty, "effective
      pseudo-cubic", no space-group claim
- [ ] size quoted with statistical CI **and** instrument-sensitivity range,
      unmerged, labelled domain (not grain) size
- [ ] DOC quoted as a range with the degeneracy stated
- [ ] crystallinity index called "fixed-protocol comparative", protocol listed
- [ ] impurity as integrated Bragg ratio, film-only, no wt%
- [ ] microstrain reported only if the WH slope is significant and positive
- [ ] `status` (VALID / PROVISIONAL / NOT_COMPARABLE) stated with its reason

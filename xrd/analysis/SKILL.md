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

### `series` — a set of scans measured together (**the default**)

`analyse_series(...)` — headers, integrity, protocol identity, substrate
referencing, geometry verdicts, then per-sample analysis. Use this whenever
more than one scan is on the table. See "The standing protocol" below.

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

## The standing protocol — run this every time

`analyse_series(files, substrate_seed, reference_label=...)` executes the whole
procedure below in one call and returns a per-quantity status. Prefer it over
calling the stages by hand; the stages exist so you can inspect, not so you can
skip.

```python
files = {'control': 'ctrl.txt', 'P1': 'p1.txt', ...}   # .mdi sidecars auto-read
res = analyse_series(files, substrate_seed=30.25, reference_label='control')
print("\n".join(series_report_lines(res)))
res['comparison'].to_csv('comparison.csv', index=False, float_format='%.10g')
```

**Step 0 — metadata from the instrument, never from memory.**
`read_mdi_header()` takes wavelength, step, dwell and range from the `.mdi`
sidecar. The declared Cu Ka value is typically the WEIGHTED MEAN (1.54184 A),
not Ka1 (1.540598 A); assuming Ka1 biases every d-spacing and the refined cell
with it. No header and no hand-supplied metadata -> lattice and size HALT.

**Step 1 — prove the data is what it claims to be.**
`verify_txt_against_mdi()` compares the two-column `.txt` against the counts
embedded in the `.mdi` (ignoring footer tokens after `npoints`). A mismatch sets
`status = NOT_COMPARABLE`. Run this before analysing, not after.

**Step 2 — protocol identity across the set.** `protocol_key()` fingerprints
wavelength, step, dwell, range, instrument, optics and normalisation. If the
keys differ, absolute-intensity comparison is forbidden and only within-scan
ratios may be reported.

**Step 3 — reference every scan to the substrate.** The substrate under each
film is physically identical, so its reflection is a built-in control.
`substrate_reference()` fits it in every scan and returns the per-sample
`zero_offset` to subtract before any lattice comparison. Treat it as a
DIFFERENTIAL reference only: the observed angle can sit a constant offset from
its literature value (sample height, transparency, geometry), so it does not
calibrate absolute angle.

**Step 4 — let the substrate decide what is comparable.**
`geometry_diagnostics()` runs two tests and they are not advisory:

| test | what it means | consequence |
|---|---|---|
| perovskite shift vs substrate shift, slope ~1 and \|r\| high | film peaks move WITH the substrate — a common geometric offset, not a lattice change | `Delta-a` = **NOT COMPARABLE** |
| film FWHM vs substrate FWHM, r positive | instrumental contribution differed between scans | `Delta-D` = **NOT COMPARABLE** |

**Is the reference sample included in the regression?** Yes, and it must be.
Subtracting a reference is a rigid translation of both axes, and slope and r are
translation-invariant — the fitted line is identical whether you regress shifts
or absolute angles. The reference lands on (0, 0) because that is where the
coordinate origin was put, not because a point was invented; dropping it would
discard a real measurement. `geometry_diagnostics()` additionally returns
`leave_one_out` (refit with each sample removed in turn, re-referenced to
another film) and `leave_one_out_stable`, so a verdict resting on one scan is
flagged rather than assumed away.

It also reports whether the substrate line is BROADER than the film peaks. When
it is, its width is set by the substrate's own grain size, so it cannot serve as
a resolution standard — deconvolving it sends the apparent size to infinity.
That divergence is a diagnostic, not a bug to work around.

**Step 5 — per sample**, on seeds tracked by each scan's own offset: fit,
bootstrap-calibrated detection, lattice, size, texture, impurities,
crystallinity — all as specified in the sections above.

**Step 6 — report only what survives.** Ratios measured inside one scan
(PbI2/perovskite, perovskite/substrate) cancel alignment and beam-intensity
drift and stay valid even when Step 4 rules out `Delta-a` and `Delta-D`. Check a
ranking against a second normalisation before believing it; if the order is
unchanged, say so with the rank correlation.

### Non-negotiables

1. **A quantity the diagnostics rule out is reported as NOT COMPARABLE, never
   quietly omitted and never quietly reported.** The negative result is the
   finding.
2. **Never merge a statistical interval with a systematic range.** They answer
   different questions. `stat_ci68` and `syst_range` stay separate fields, and
   separate bars in any figure.
3. **Lattice error is two numbers**: `e_a_formal` and `e_a_model` (Birge-scaled).
   A pseudo-cubic effective cell is never a space-group claim.
4. **No weight fraction from a single reflection of a textured phase.** Report a
   relative Bragg-intensity index and say "PbI2-compatible".
5. **Every claim in a figure title or report line is checked against the array it
   plots before rendering.** If the data says 2 of 3, the title says 2 of 3.
6. **State n.** One scan per film is n = 1; put it in the figure.

### Deliverables for every run

- `comparison.csv (not committed)` — one row per sample, every quantity with its status column
- `xrd/results/peak_table.csv` via `write_peak_table()` — full-precision p-values, never rounded
- `xrd/results/geometry_diagnostics.csv` — substrate drift/width evidence behind the verdicts
- a figure whose panels show the diagnostics, not only the results
- a dated entry in the experiment record, and a push to the project repo

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

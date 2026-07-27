# XRD measurement protocol (standing — follow for every batch)

Version 2026-07-26. Applies to all perovskite thin-film XRD in this project.
Implemented and enforced by the `perovskite-xrd-protocol` skill; this document
is the human-readable statement of the same rules.

## At the instrument

Everything below assumes the scans are comparable. That is a property of how
they were acquired, not something analysis can recover.

1. **One session, one alignment.** Measure a whole comparison set without
   re-seating the stage or changing sample height between films. This is the
   single most important step: the 2026-07-26 passivator batch lost Δa and ΔD
   entirely to height drift between scans, and nothing in the analysis could
   recover them.
2. **Identical acquisition across the set** — wavelength, range, step, dwell,
   slits, optics, monochromator, sample area. Any difference forbids
   absolute-intensity comparison.
3. **Keep the `.mdi` sidecars.** They carry the declared wavelength, step and
   dwell. Do not re-type these by hand.
4. **Two extra scans per batch, both cheap:**
   - **bare substrate** — pins the substrate contribution and confirms
     substrate-overlapping assignments (otherwise they stay PROVISIONAL)
   - **LaB₆ or Si standard** — gives a true instrumental resolution function,
     which is what turns crystallite size from conditional into absolute
5. **Replicates.** One scan per film is n = 1. Two films per condition would let
   run-to-run scatter be measured instead of assumed.

## Analysis — one call

```python
res = analyse_series(files, substrate_seed=<substrate 2θ>, reference_label='control')
print("\n".join(series_report_lines(res)))
```

The stages it runs, in order, and why each exists:

| # | stage | why |
|---|---|---|
| 0 | read `.mdi` headers | declared Cu Kα is the weighted mean 1.54184 Å, not Kα₁ 1.540598 Å; assuming Kα₁ biases every d-spacing |
| 1 | verify `.txt` against `.mdi` counts | catches truncated or edited exports before they become results |
| 2 | protocol-identity fingerprint | differing acquisition ⇒ absolute intensities not comparable |
| 3 | substrate referencing | the substrate is identical under every film, so its line is a built-in control |
| 4 | geometry diagnostics | decides whether Δa and ΔD are real or instrumental |
| 5 | per-sample analysis | fit, calibrated detection, lattice, size, texture, impurities |
| 6 | comparative indices | within-scan ratios, which survive alignment drift |

### The two diagnostics that decide what may be reported

- **Position.** Regress each film's perovskite 100 shift on its substrate shift.
  Slope ≈ 1 with high r means the film peaks moved *with* the substrate — a
  common geometric offset, not a lattice change ⇒ **Δa NOT COMPARABLE**.
- **Width.** Correlate film peak width with substrate peak width. The substrate
  cannot broaden, so a positive correlation means the instrumental contribution
  differed between scans ⇒ **ΔD NOT COMPARABLE**.

If the substrate line is *broader* than the film peaks, it is grain-size limited
and cannot serve as a resolution standard; attempting to deconvolve it drives
apparent size to infinity. That divergence is the diagnostic working, not a bug.

## Reporting rules (non-negotiable)

1. A quantity the diagnostics rule out is reported as **NOT COMPARABLE** —
   never quietly omitted, never quietly reported. The negative result is a
   finding and usually the most useful one.
2. **Statistical intervals and systematic ranges are never merged.** They answer
   different questions and get separate fields and separate bars.
3. Lattice error is **two numbers**: formal fit and model-scaled (Birge). An
   effective pseudo-cubic cell is never a space-group claim.
4. **No wt% from a single reflection of a textured phase.** Report a relative
   Bragg-intensity index and phrase it "PbI₂-compatible".
5. Crystallinity is a **fixed-protocol comparative index**, not an absolute, and
   DOC is a bounded range, not a point value.
6. Detection is by **bootstrap-calibrated likelihood-ratio test**, never fitted-
   area SNR. Never round p-values on export.
7. Texture conventions are **locked**: fixed reflection family, multiplicity,
   Lorentz–polarisation, structure factors at the same wavelength and cell,
   substrate-overlapping reflections excluded, TC normalised to mean 1.
8. **Microstrain is suppressed** unless the Williamson–Hall slope is significant
   and positive.
9. **Every claim in a figure title or a report line is checked against the array
   it plots before rendering.** If the data says 2 of 3, the title says 2 of 3.
10. **State n.** One scan per film is n = 1; put it in the figure.

## Deliverables per batch

- `comparison.csv` — one row per sample, each quantity with its status
- `peak_table.csv` — full-precision p-values via `write_peak_table()`
- `geometry_diagnostics.csv` — the substrate evidence behind the verdicts
- a figure whose panels show the diagnostics, not only the results
- a dated entry in this repo's record, and a push

## Why this exists

Two batches produced numbers that looked precise and were not. The control scan
gave a confident crystallite size whose value moved 38→50 nm with an assumed
instrumental width. The passivator batch gave an apparent lattice spread of
0.011 A (4 of 5 films above control, 1 below -- scatter, not a contraction) and
a 3.9x spread in apparent domain size; both were alignment artifacts.
In each case the assumption, not the sample, set the number. The protocol exists
to make that failure visible automatically rather than after review.

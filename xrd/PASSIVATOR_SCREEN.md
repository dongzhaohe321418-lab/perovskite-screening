# Passivator screen — XRD comparison (Generations-0726)

Six films on ITO: control plus five spin-coated passivators (P1–P5), per the
supplied measurement note. Analysed with the `perovskite-xrd-protocol` skill.

| | |
|---|---|
| Instrument | DX-27Mini, 40 kV / 10 mA, slits 1°/1°/0.03 mm, monochromator ON |
| Scan | 5.00–50.00° 2θ, 0.05° step, 0.3 s/step, 901 points |
| Wavelength | 1.54184 Å (Cu Kα weighted mean, **declared in the .mdi headers**) |
| Protocol | **identical across all six** — absolute-intensity comparison permitted |
| Data integrity | every `.txt` verified byte-identical to the counts in its `.mdi` |

## Headline

**All six films are the same pseudo-cubic perovskite phase.** Eight reflections
(N = 1,2,3,4,5,6,8,9) index in every sample, with no unindexed film reflections.

**The single most important finding is negative: the apparent lattice and
crystallite-size differences between these samples are instrumental artifacts,
not material differences.** The ITO substrate is physically identical under
every film, so its diffraction line is a built-in control — and it moves.

## 1. The geometry problem (read this before any comparison)

The ITO (222) line drifts **0.35° across the six scans** and its width varies
**71%**, on a substrate that cannot change. Both are alignment/sample-height
effects, and they contaminate exactly the two quantities most often quoted from
a passivator screen.

| sample | ITO shift vs control (°) | ITO FWHM (°) | perovskite median FWHM (°) | apparent D (nm) |
|---|---|---|---|---|
| control | +0.0000 | 0.459 | 0.207 | 46.731 |
| P1 | +0.0686 | 0.359 | 0.157 | 87.704 |
| P2 | +0.1374 | 0.458 | 0.285 | 32.931 |
| P3 | +0.3502 | 0.662 | 0.380 | 22.647 |
| P4 | +0.0274 | 0.446 | 0.319 | 27.635 |
| P5 | +0.0397 | 0.340 | 0.166 | 79.046 |

Two diagnostics establish the artifact:

- **Positions.** Perovskite 100 shift vs ITO shift: **slope 1.08, r = 0.985**
  (220: slope 1.14, r = 0.993). The film peaks move essentially one-for-one with
  the substrate peak. A real lattice change would move the film peaks while
  leaving ITO fixed.
- **Widths.** ITO FWHM correlates with perovskite median FWHM at **r = +0.87**,
  and with apparent D at **r = −0.79**. The samples that look "more crystalline"
  are the ones whose substrate line is also sharpest.

After referencing every pattern to its own ITO line, the pseudo-cubic parameter
spans **6.2987–6.3096 Å** (spread 0.011 Å) against a largest model uncertainty of
**0.0076 Å** — i.e. comparable to, not clearly exceeding, the uncertainty. **No
lattice change is established.** Note also that the ITO line sits a nearly
constant 0.32 ± 0.03° from its literature position in all six scans, so it works
as a *relative* reference but not as an absolute angle standard.

**Crystallite size is reported but NOT comparable.** The apparent range is
23–88 nm, but attempting to correct for the varying instrumental contribution
diverges: the ITO line is *broader* than the film peaks in five of six samples,
so its width is dominated by ITO's own grain size and cannot serve as a
resolution standard. Under every correction model tried, the ordering was
unstable. Marked `NOT_COMPARABLE`.

## 2. What survives — PbI₂ content

Intensity ratios measured within a single scan are immune to alignment and flux
drift, because both peaks see the same geometry. This is the one comparison the
dataset supports cleanly.

| sample | PbI₂ 001 2θ | Δχ² | p (bootstrap) | % of perovskite Bragg | call |
|---|---|---|---|---|---|
| control | 12.594° | 75.0 | 4.33e-14 | 2.66 | **detected** |
| P1 | 12.746° | 132.3 | 1.01e-23 | 3.85 | **detected** |
| P2 | 12.803° | 77.5 | 3.88e-15 | 3.40 | **detected** |
| P3 | 13.055° | 11.0 | 2.32e-02 | 1.14 | **below detection** |
| P4 | 12.694° | 23.2 | 1.39e-04 | 1.73 | **detected** |
| P5 | 12.650° | 344.6 | 5.17e-64 | 10.04 | **detected** |

Robustness checks, all passed:

- Ordering is **identical** whether PbI₂ is referenced to all eight perovskite
  reflections or to the nearest one (100, 2.6° away) — Spearman ρ = 1.00.
- PbI₂ % **anti-correlates** with the misalignment proxy (r = −0.69): the
  highest values come from the best-aligned scans, so the trend is not
  manufactured by geometry.

**Conclusion.** P5 shows ~10% PbI₂, roughly **4× the control** — a substantial
excess. P1 and P2 sit modestly above control (3.9%, 3.4%). P4 is below control
(1.7%). P3 falls **below the detection threshold** (p = 0.023 against a
Bonferroni α = 0.0042) — the only sample with no PbI₂-compatible peak.

Since PbI₂ at the surface is where a spin-coated passivator acts, the P5 vs P3
contrast is the most chemically informative result here: opposite extremes of
surface PbI₂ under nominally similar treatments.

## 3. Comparative crystallinity (same protocol, so admissible)

| sample | perovskite Bragg | perovskite/ITO | vs control | Bragg/total | max TC |
|---|---|---|---|---|---|
| control | 368 | 15.18 | +0% | 0.230 | 2.38 |
| P1 | 357 | 16.29 | +7% | 0.227 | 2.46 |
| P2 | 315 | 14.87 | -2% | 0.213 | 2.73 |
| P3 | 267 | 8.98 | -41% | 0.225 | 3.67 |
| P4 | 349 | 13.88 | -9% | 0.223 | 3.07 |
| P5 | 336 | 16.31 | +7% | 0.224 | 3.05 |

Using the internally-normalised **perovskite/ITO** ratio, P1, P2 and P5 are
within ±7% of control — no meaningful change. **P3 is down 41%**, the only
sample outside noise, consistent with its broader peaks and lower total counts
(26.6 k vs 33–36 k elsewhere). P4 is down 9%, marginal.

`Bragg/total` is flat (0.213–0.230) across all six, i.e. **no passivator
measurably amorphised the film.** Degree of crystallinity ranges 41–67% but is
bounded-only in every sample (halo width degenerate with the flat background),
so it is not used for ranking.

All six films are **strongly textured** (max TC 2.4–3.7 vs 1.0 for a random
powder), with 100 consistently under-represented (TC 0.17–0.22). Texture
therefore prohibits converting any intensity ratio to a weight fraction.

## 4. Status per quantity

| quantity | status | reason |
|---|---|---|
| Phase identity | **VALID** | all six index on the same cell |
| PbI₂ / perovskite ratio | **VALID** (P3 provisional) | within-scan ratio, ordering robust |
| Comparative crystallinity | **VALID** | protocol identical across scans |
| Texture coefficients | **VALID** | locked convention, substrate excluded |
| Lattice parameter Δa | **NOT COMPARABLE** | shifts track ITO 1:1 |
| Crystallite size ΔD | **NOT COMPARABLE** | width tracks ITO (r = +0.87) |
| Absolute DOC | **bounded range only** | halo/background degeneracy |
| Microstrain | **suppressed** | WH slope insignificant in all samples |

## 5. What to do next

1. **Re-run the six scans in one session without touching sample height**, or
   add an internal standard (Si powder) to each film. Without this, Δa and ΔD
   from this series are not recoverable — this is the binding limitation.
2. **Bare-ITO scan** — pins the substrate contribution and confirms the 30.2°
   assignment (currently provisional on d-spacing alone).
3. **LaB₆ / Si standard** — gives a true resolution function, so size becomes
   absolute rather than conditional.
4. Repeat P5 and P3 to confirm the PbI₂ extremes, which are the only
   material-level differences this dataset establishes.

## Files

```
data/raw/generations-0726/    six .txt + .mdi pairs + measurement note
results/passivator_comparison.csv      per-sample metrics with status flags
results/passivator_peak_tables.csv     every fitted peak, all samples
results/passivator_texture.csv         texture coefficients
results/geometry_diagnostics.csv       ITO drift/width evidence
figures/xrd_passivator_comparison.png
```

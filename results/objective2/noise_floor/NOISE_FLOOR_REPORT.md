# Gate-6 noise floor — MEASURED

**The number that was missing.** Gate 6 requires that a dopant ranking be published only
where between-dopant separation exceeds the within-host configurational spread. That
spread had never been measured for this host, so no ΔE_a could be called resolvable.
It is now measured, and it is large enough to determine the screening design.

## Method

Undoped iodide-vacancy migration in FA₀.₉₅Cs₀.₀₅PbI₃ (233-atom det-20 cell), CI-NEB with
5 interior images at MACE-MP-0 medium, `improvedtangent`. Identical composition, identical
vacancy site, **only the FA orientations differ** between members — so the spread is purely
configurational.

Endpoints were relaxed in a dedicated stage (fmax 0.02, up to 800 steps) *before* the band,
because this host has soft molecular-rotation modes; relaxing them at the band's own budget
leaves them above the first interior image and makes E_a a difference from a non-minimum.

## Result

| member | E_a (meV) | gate |
|---|---|---|
| 0 | (718.5) | **rejected** — endpoints not minima, saddle at an endpoint, band unconverged |
| 1 | (0.0) | **rejected** — saddle at image 0; lowest interior 269 meV *below* the initial state |
| 2 | 309.9 | valid |
| 3 | 210.4 | valid |
| 4 | 179.4 | valid |
| 5 | 196.1 | valid |
| 6 | 105.2 | valid |
| 7 | 279.6 | valid |

All six valid members place the saddle at the midpoint image with converged bands.

**Noise floor: spread 204.7 meV, σ = 73.3 meV, mean 213.4 meV, IQR 183.6-262.3 meV** (6 valid of 8).

## Consequence 1 — methodology, not physics, is the binding constraint

    noise floor σ    = 73.3 meV
    10× rate at 300 K = 59.5 meV

The configurational noise is **1.2× larger than the effect size we are trying to
detect** (73.3 / 59.5 = 1.23). A single configuration has a standard error of 73 meV —
larger than the entire signal. **Single-configuration screening cannot work in this host**,
at any level of theory.

**Do not conflate the two ratios.** σ = 73.3 meV gives **1.2×** the threshold and is the
figure that governs resolvability, because the standard error of a mean scales with σ. The
full-range *spread* of 204.7 meV gives 3.4×, but a range over 6 samples is not an
uncertainty and must not be quoted as the margin by which the floor exceeds the threshold.
The 1.2× figure is the one to cite.

## Consequence 2 — required sampling depth

For a doped-vs-undoped comparison with n configurations each, SE(difference) = σ√(2/n).
Requiring 2·SE ≤ 59.5 meV gives

**n ≥ 13 configurations per dopant.**

| n | 2·SE (meV) | resolves 10× rate? |
|---|---|---|
| 1 | 207 | no |
| 5 | 93 | no |
| 8 | 73 | no |
| **13** | **59** | **yes** |
| 20 | 46 | yes |

## Consequence 3 — this independently confirms the revised gate 4

The GA orientation spread measured from the existing anchor was **207.2 meV** across three
orientations. The undoped noise floor here is **204.7 meV** across six members. These are
the same magnitude — the "GA orientation effect" is statistically indistinguishable from
the host's own configurational noise. Two independent routes now say the GA anchor cannot
serve as pipeline validation until it is re-measured as a distribution against this
baseline.

## Consequence 4 — compute requirement

Measured cost: 646-2215 s per path on 12 CPU cores including the endpoint stage (~25 min
mean). At the required depth, 13 dopants × 13 configurations = 169 paths ≈ **70 h** of
local CPU. The GPU host (`ssh:autodl`) is currently unreachable — connection closed — so
screening at defensible sampling depth is **blocked on GPU access**, not on method.

This is a scheduling constraint worth surfacing: the pre-screen is cheap *per path* but the
required depth is set by the noise floor, and that makes it a GPU-scale job.

## What this does not establish

This is the *undoped* baseline at MACE level. It says nothing about any dopant, and MACE
noise is not DFT noise — the DFT screening will need its own floor, which will be far more
expensive to measure. The floor also assumes the 8 MD-drawn members represent the thermal
FA-orientation distribution; if they under-sample it, the true floor is larger.

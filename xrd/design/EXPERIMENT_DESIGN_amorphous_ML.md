# Quantifying crystalline quality and the amorphous phase in FA<sub>0.95</sub>Cs<sub>0.05</sub>PbI<sub>3</sub>: an XRD + machine-learning experiment design

Drafted 2026-08-04, from a coverage analysis of the 79-paper index you supplied,
diffraction-angle calculations for the FA/Cs system, and a feasibility estimate
of the degradation kinetics. Every number is reproducible from `design_calcs.py`.

---

## 1. Three judgements that will decide whether this works

### 1.1 The gap you identified is real, and wider than you think

Cross-tabulating your 79 papers by keyword:

| Topic (exact keyword in title) | Papers / 79 |
|---|---|
| amorphous | **0** |
| PDF / total scattering | **0** |
| Rietveld or crystallinity | **1** |
| machine learning | **1** |
| in situ / operando | 3 |
| humidity | 3 |

Broadening the terms does not rescue the picture: allowing *glass* and *disorder*
alongside *amorphous* reaches 2; allowing *crystallite*, *texture* and *strain*
alongside *Rietveld/crystallinity* reaches 11 — but those 11 are strain- and
texture-engineering papers, not crystallinity quantification. Under either
counting the intersections are empty.

Every intersection that matters is empty: amorphous ∩ total scattering = 0,
in situ ∩ humidity = 0, ML ∩ crystallinity = 0, FA/Cs ∩ δ-phase = 0. A literature
check agrees: existing work either extracts a grain size from one peak via
Scherrer, or treats the amorphous component as an unquantified systematic. One
review states outright that amorphous phases in a thin film introduce an error
that the standard analysis cannot bound.

**So the topic stands up. But the gap exists mostly for methodological reasons,
not because nobody wanted the answer.**

### 1.2 A laboratory diffractometer cannot measure absolute amorphous content

The standard route to amorphous quantification is the internal-standard method —
mix in a known mass of ZnO or similar. It assumes a **powder**: something you can
homogenise, with enough diffracting volume. A thin film fails all three
conditions. You cannot mix in a standard, the diffracting volume is tiny, and
the amorphous halo is mathematically degenerate with substrate and air
scattering. I hit exactly this on the control sample earlier in this project:
the recovered crystallinity tracked whatever width bound I imposed on the halo,
landing anywhere between 46% and 65%.

**If "absolute amorphous fraction" is the target, this experiment will fail.**

What to measure instead (this design adopts these):

| Not measurable | Measurable |
|---|---|
| Absolute amorphous volume fraction | **Relative amorphous index** under a fixed protocol, and its **time derivative** |
| "Properties" of the amorphous phase | **Shape parameters** of the diffuse halo (centre, width, asymmetry) vs T and RH |
| Absolute crystallinity | **Change** in Bragg/total, same film compared against itself |

The distinction matters: absolute values are governed by unstated assumptions,
whereas **changes within one film under one protocol** are robust. What you
actually want to study — how the amorphous region evolves with environment —
needs only the latter.

### 1.3 Your ML goal hides two problems whose data requirements differ 50-fold

Separate them or the sample size will be wrong.

**Problem A (forward / kinetics)**: `(T, RH, t) → phase fractions`.
Effective sample size = **number of independent films**. Nine time points on one
film are not nine independent samples — they are strongly autocorrelated, and
treating them as independent understates the uncertainty by roughly 3×.

**Problem B (inverse / pattern decoding)**: `diffraction pattern → phase fractions + microstructure`.
Effective sample size = number of patterns, and patterns **can be simulated
without limit**. This is the only part where deep learning genuinely applies.

| Films | Fitting a physical model (Ea, m, k₀, Avrami n) | Training a black-box NN |
|---|---|---|
| 12 | 3 observations per parameter — marginal | impossible |
| 40 | 10 per parameter — sufficient | insufficient |
| 60 | 15 per parameter — comfortable | still insufficient |

**Recommendation: solve A with a physical model (Bayesian fit) and B with ML
trained on simulated patterns. Do not try to train an end-to-end black box on a
few dozen films.**

---

## 2. Your material: the diagnostic window is already computed

FA<sub>0.95</sub>Cs<sub>0.05</sub>PbI<sub>3</sub>, Vegard interpolation gives
a = **6.3529 Å** (FAPbI₃ 6.3620, α-CsPbI₃ 6.1800).

The three competing phases separate inside **a single 11–15° window**:

| Phase | hkl | d (Å) | 2θ (°) |
|---|---|---|---|
| δ-FAPbI₃ (yellow, hexagonal) | 010 | 7.500 | **11.80** |
| PbI₂ (2H) | 001 | 6.979 | **12.68** |
| α-perovskite (cubic) | 100 | 6.353 | **13.94** |

Spacings of 0.88° and 1.26° against a typical 0.20° peak width — **4–6× separation,
no overlap**.

This is the key convenience of the design: **one 4° window tracks all three
phases simultaneously**, in a 2–3 minute scan, which is what makes
time-resolved in situ measurement practical. Reserve the full 5–50° scan for
selected time points.

Remaining α reflections: 110 = 19.76°, 111 = 24.27°, 200 = 28.09°,
210 = 31.49°, 211 = 34.58°.

---

## 3. The time-scale problem (solve this before anything else)

Estimating half-life t₅₀ from Arrhenius × RH power law, anchored at
85 °C / 85 %RH → 100 h:

t₅₀ (hours), Ea = 0.75 eV, RH exponent = 2:

| | 15% | 35% | 55% | 75% | 85% |
|---|---|---|---|---|---|
| 25 °C | 427159 | 78458 | 31772 | 17086 | 13303 |
| 40 °C | 105512 | 19380 | 7848 | 4220 | 3286 |
| 55 °C | 29617 | 5440 | 2203 | 1185 | **922** |
| 70 °C | 9290 | 1706 | **691** | **372** | **289** |
| 85 °C | 3211 | **590** | **239** | **128** | **100** |

**A 4272-fold span.** Within a 30-day budget only 5 points of a uniform 5×5 grid
yield a complete curve; 14 will not move at all — those films are indistinguishable
from day one after a month on the shelf.

Worse: **how many points are feasible swings between 3 and 25 depending on Ea and
m, which you do not know in advance.**

| Ea (eV) | m=1 | m=2 | m=3 |
|---|---|---|---|
| 0.50 | 11 | 8 | 6 |
| 0.75 | 8 | 5 | 5 |
| 1.10 | 7 | 4 | 4 |

**So the grid cannot be fixed up front. Calibrate the kinetics on a few films
first, then place the grid.**

---

## 4. Recommended design: three stages

### Stage 0 — Method foundation (2 weeks, ~10 films)

Skip this and none of the later numbers can be interpreted.

1. **Bare-substrate scans** (≥3 per substrate type): the ITO/glass scattering
   background. Without it the amorphous halo cannot be separated from substrate
   diffuse scattering — the exact problem that arose on the control sample.
2. **LaB₆ or Si standard**: the real instrumental resolution function. Without it
   crystallite size is a conditional value only; size can move ±30% with the
   assumed instrumental width.
3. **Repeatability baseline**: one film measured 5× without moving it →
   instrument repeatability; 5 films from one batch measured once each → batch
   scatter. **The second number defines the threshold for "a real change"**, and
   without it any ML is fitting noise.
4. **Thickness normalisation** (profilometry or XRR): Bragg intensity scales with
   diffracting volume, so a 10% thickness difference propagates straight into the
   result.

### Stage 1 — Kinetics calibration (2 weeks, 12 films)

Six points along a T line and six along an RH line, 11–15° window only, densely
sampled in time:

- T sweep: 55 / 65 / 75 / 85 / 95 °C at fixed RH = 60%
- RH sweep: 30 / 45 / 60 / 75 / 85 % at fixed T = 75 °C

**Purpose**: fit Ea and m. Only then does Stage 2's grid have a basis.

**Decision point**: if Ea lands in 0.6–1.0 eV and m in 1–3, continue as below.
If either is far outside (e.g. m < 0.5, meaning humidity is not the driver),
stop and redesign.

### Stage 2 — Main experiment (4–6 weeks, 40–48 films)

**Place conditions on iso-rate contours, not on a uniform T/RH grid.** Use the
Stage 1 parameters to solve for (T, RH) combinations whose t₅₀ falls at
6 h / 24 h / 72 h / 168 h / 480 h. Every film then completes its curve within
budget, and T and RH effects stay separable by design.

Sample each film in time at **t/t₅₀ = 0.05, 0.15, 0.35, 0.7, 1.0, 1.5, 2.5, 4.0**
(logarithmic). A fixed clock-time grid misses the whole process in fast
conditions and wastes points in slow ones.

At each time point:
- **Fast scan** 11–15°, 0.02° step, 2–3 min (three-phase tracking)
- At t/t₅₀ = 0, 0.35, 1.0, 4.0 additionally a **full scan** 5–50°, 40 min
  (texture, microstructure, amorphous halo)

**Two replicate films per condition** — the minimum for reporting an error bar.

**Volume**: ~20 conditions × 2 = 40 films, ~360 fast + 160 full scans.
Instrument time ≈ **11 h fast + 107 h full ≈ 5 days of occupancy**, spread over
6 weeks.

---

## 5. What to extract (this determines whether the ML is possible)

The same quantities from every pattern, each with an uncertainty:

**Crystalline phases**
- Three-phase integrated intensity ratios: α/(α+δ+PbI₂), δ/α, PbI₂/α —
  **within-scan ratios, immune to alignment and flux drift**
- α pseudo-cubic a (formal and model uncertainties reported separately)
- Peak width → crystallite size (report the statistical interval and the
  instrumental systematic range as two numbers, never merged)
- Texture coefficients under a locked convention (multiplicity, LP, structure
  factors at the same wavelength, same reflection family)

**Amorphous phase (where the novelty is)**
- Diffuse halo **centre, width, asymmetry**, fitted to the residual after
  subtracting the bare-substrate scan
- **Relative amorphous index** = diffuse integral / (diffuse + Bragg integral),
  comparable only under a fixed protocol
- **d(index)/dt** — far more robust than the absolute value, and the quantity
  that actually carries the physics

**Quality gates (every pattern must pass)**
- Substrate peak shifted > 0.05° → flag the point, forbid its use for lattice comparison
- Substrate peak width changed > 20% → forbid its use for size comparison
- Thickness not measured → forbid absolute-intensity comparison

---

## 6. The ML: two separate tracks

### Track A — physical model + Bayesian inference (on the 40-film data)

Avrami-type conversion with an Arrhenius-RH rate:
```
α(t) = exp(-(k·t)^n),  k = k₀·exp(-Ea/kT)·(RH/100)^m
```
Fit hierarchically, with film-to-film variation as a random effect, so parameters
and batch scatter are estimated together. The output is a **posterior over Ea, m
and n**, not a point estimate.

40 films is adequate for 4 parameters (10 independent observations each).

### Track B — pattern-decoding network (trained on simulation, validated on your data)

This is the part where deep learning earns its place:
1. Forward-simulate patterns from the known structures (three phases × phase
   fractions × crystallite sizes × texture × amorphous halo × noise) → 10⁵
   training patterns without touching the diffractometer
2. Train a 1D CNN: pattern → (phase fractions, crystallite size, amorphous index)
3. **Use your 40 films as the validation set, never as training data**
4. The decisive test: is the error on real patterns comparable to the error on
   simulated ones? If it degrades sharply, the simulation is missing a real
   instrument or sample effect and needs to be extended

The payoff: once trained, analysing a new pattern goes from ~20 minutes of manual
fitting to ~0.1 s. That is ML's real contribution here.

### What not to do

Train an end-to-end `(T,RH,t) → properties` network on 40 films. You are more
than an order of magnitude short; it will overfit and it will not extrapolate —
and extrapolation (predicting untested conditions) is precisely what you want.

---

## 7. In situ vs ex situ

**Do at least one line in situ** (environmental chamber on the diffractometer):

- Ex situ (remove → measure → return) injects a thermal and humidity step every
  cycle, and the δ↔α transition in FA-based perovskites is sensitive to exactly
  that. You may end up measuring the handling, not the ageing.
- Time resolution is limited by the handling cycle, so fast conditions
  (t₅₀ < 24 h) miss the early stage entirely.
- The early stage is where the amorphous phase changes fastest.

Without a chamber: at minimum run **the full time series on one film** rather
than sacrificing a film per time point, and log the handling times and ambient
conditions.

---

## 8. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Amorphous halo inseparable from substrate scattering | **high** | Stage 0 bare-substrate scans; report only relative index and its derivative |
| Kinetics fall outside expectation, grid fails | medium | Two-stage design with a decision point after Stage 1 |
| Batch scatter exceeds the treatment effect | **high** | Quantify scatter in Stage 0; compare within batch; ≥2 replicates |
| Handling perturbation dominates the signal | medium | In situ chamber, or full series on one film |
| δ and PbI₂ peaks merge once broadened | low | Computed: 0.88° apart, would need FWHM > 0.4° to overlap |
| Sample size insufficient for ML | **high** | Track A physical model; Track B trained on simulation |

---

## 9. If you can only do one thing

**Do Stage 0 + Stage 1 (4 weeks, 22 films).**

Stage 0's bare-substrate and standard scans are the precondition for every
quantitative statement; without them the whole project reports conditional
values. Stage 1 yields Ea and m, which is a publishable result on its own and
decides whether Stage 2 is worth running.

Committing 40 films to the main experiment before those two stages is a gamble,
because where the grid should sit depends on parameters you do not yet know.

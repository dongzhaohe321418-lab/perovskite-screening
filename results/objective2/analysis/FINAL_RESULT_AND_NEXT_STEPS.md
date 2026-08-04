# Final result and recommended next experiments

**Scope.** Objective-2 / MLIP side only, from data already committed and (except where noted)
independently audited. **No Q2 production CI-NEB barrier is read, quoted, or implied.** The
q=0/q=+1 barriers remain unextracted, `publish_claim` remains DENIED and un-retried, and the ban
on claiming reproduction of the Tyagi charge-state ordering stands.

---

## 1. The result

**Neither additive suppresses iodine migration, and the null is informative rather than
underpowered.**

| | GA | Sr |
|---|---|---|
| paired n | 11 | 12 |
| mean ΔE_a vs undoped | **+6.8 meV** | **−4.3 meV** |
| 95% CI | [−25.0, +38.6] | [−42.2, +33.6] |
| p (paired t / Wilcoxon) | 0.644 / 0.765 | 0.807 / 0.733 |
| power at the 10× target (59.5 meV) | 0.96 | 0.88 |
| **10× target excluded by the CI** | **yes** | **yes** |

Both intervals are *narrower* than the effect the project was designed to detect, so a 10×
suppression would very probably have been observed. It was not. No GA-vs-Sr ranking is claimed —
the two intervals overlap almost entirely.

## 2. Why — and this is the substantive finding

On the balanced 9-host subset admissible in all three systems, decomposing E_a:

| contribution | SD (meV) |
|---|---|
| **host configuration** | **57.3** |
| residual | 29.7 |
| **dopant identity** | **4.6** |

**The host term exceeds the dopant term by 12.3×.** Per-system means differ by 9.3 meV while the
host configurations span 151.7 meV; the dopant factor is indistinguishable from zero (ANOVA
F=0.046, p=0.955; Friedman p=0.895).

So the equivalence is **structural, not a measurement failure**: at these concentrations the
additive perturbs the migration barrier an order of magnitude less than the host's own
configurational disorder does. Two consequences that matter for how this system is studied:

1. **Any screen that samples hosts unpaired is measuring host noise.** The residual SD alone
   (29.7 meV) exceeds either dopant mean. The paired design is what makes the comparison possible.
2. **A single-configuration calculation cannot answer this question**, no matter how converged.
   One host draws from a 152 meV distribution.

## 3. What predicts the barrier — nothing yet, honestly

Seven structural/convergence predictors were tested against E_a on the 49 admissible paths.
Three reached raw p<0.05 (hop distance d_max, NEB fmax, NEB nsteps). **None survives
Holm–Bonferroni correction for the seven tests actually performed** (smallest corrected p = 0.16).

| predictor | r | raw p | Holm p |
|---|---|---|---|
| hop distance d_max | +0.28 | 0.050 | 0.21 |
| NEB nsteps | −0.32 | 0.027 | 0.16 |
| NEB fmax | −0.29 | 0.041 | 0.21 |
| other four | — | ≥0.12 | ≥0.35 |

A three-term regression reaches R²=0.26 with d_max and nsteps individually significant — but that
is the *same data* fitted with more parameters, not independent evidence, and fmax/nsteps are
properties of the optimiser rather than of the barrier. **d_max is recorded as a hypothesis for
pre-registered testing, not as a finding.** The physical reading — a longer hop costs more — is
plausible, which is exactly why it needs an out-of-sample test rather than a p-value from the
screen that generated it.

## 4. Recommended next experiments, in priority order

Cost basis: **measured 70 s median per path** at MLIP level over the 49 admissible paths.

### P1 — Expand the paired corpus to n≈50 (GA) / n≈72 (Sr). ~2 GPU-hours.
The single highest-value action. Takes the resolution from "no 10× effect" to "no 20 meV effect,"
which is the scale at which an additive could still matter for device lifetime. Requires
**4.3× / 6.0×** the current members. At 70 s/path this is hours, not days — the corpus is
cheap and the statistics are the binding constraint, which is an unusually favourable position.
Sample hosts from the same 36-member harmonised ensemble and keep the pairing.

### P2 — Pre-register the d_max test on the new members. Free, rides on P1.
Fix the hypothesis (**E_a increases with d_max**), the single test, and α=0.05 *before* running
P1, then evaluate on the new members only. A single pre-registered test needs **n≈97** for 80%
power at the observed r=0.28; screening seven predictors again would need **n≈152**. P1 at n≈72
gets most of the way; combining P1's new members with the existing 49 reaches ~120 and would
settle it. If it confirms, the design lever moves from *chemistry* to *geometry* — which
additives that widen the iodine channel, not which additives bind iodine.

### P3 — Check the concentration axis before abandoning additives. ~2 GPU-hours.
The 12.3× host dominance is at **one** doping level. The honest statement is "no effect at this
concentration," not "no effect." A 2–3× concentration series on ~20 paired hosts tests whether the
dopant term scales at all. If the dopant SD stays near 4.6 meV while concentration triples, the
additive route is closed on evidence rather than by inference from a single point.

### P4 — Re-anchor the MLIP against DFT on the extremes. ~1 day of DFT.
Every number above is MACE-MP-0 level and not transferable. Two host configurations — the 48 meV
minimum and the 293 meV maximum — recomputed at the production DFT level would bound whether the
152 meV host spread is physical or a potential artifact. **This is the one result that would
change how everything above should be read**, and it is the cheapest possible test of it: 2
calculations, not 49.

### P5 — Do NOT expand the Stage-3 seed set from NEB frames. Blocked, and correctly.
The NEB archives hold 39 iterations × 5 images of converged frames — far more training data than
the 12 endpoint frames currently used. Their per-image energies **are** the gate-withheld barrier,
so they stay out until extraction is authorized. If more seeds are needed before then, run fresh
endpoint relaxations at other hosts; do not mine the NEB archive.

## 5. What is NOT resolved, stated plainly

- **The Q2 charge-state question.** Both production CI-NEB legs converged (q=0: 36 iterations;
  q=+1: 37; all path forces ≤0.05 eV/Å; `JOB DONE`), raw outputs and hash chains committed. The
  barriers are **not extracted**. This is gated, not unfinished.
- **The FNV charged-defect correction** is PENDING: the converged charge densities exist for all
  five images of both legs (197 MB/image, remote scratch, **perishable**), but the `pp.x`
  potential step was DENIED. If that scratch space is reclaimed, this becomes a re-run of both
  NEB legs rather than post-processing.
- **F-025 and F-026 were never independently closed.** See `EXPERIMENT_AUDIT.md` — the extraction
  guard's third version has been audited by no one, and my own worst-case test of it is
  self-testing, which is the evidence class the auditor twice found insufficient.
- **A 20 meV additive effect.** Not excluded. That is what P1 is for.

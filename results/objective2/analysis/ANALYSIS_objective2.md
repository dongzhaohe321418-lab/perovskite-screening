# Objective 2 analysis — the host configuration, not the additive, sets the barrier

**Scope, stated first.** This document analyses **only** data already committed and
independently audited: the 108-path MLIP paired corpus, its admission classes, and the
Stage-3 seed frames. It reads **no** Q2 production CI-NEB output. No barrier from the
q=0/q=+1 production legs is extracted, quoted, or implied here, and the prohibition on
claiming reproduction of the Tyagi charge-state ordering is untouched.

**Reproduction check before analysis.** Every published statistic was re-derived from
`paired_raw_108.json` + `admission_108.json` rather than restated: GA n=11, mean +6.8,
sd 47.4 meV and Sr n=12, mean −4.3, sd 59.6 meV, with the **member lists and all 23
per-pair values matching to 0.05 meV**. The auditor independently recomputed the same
values in CYCLE-000010. Admission classes recount exactly: 49 admissible, 34 strict,
15 recovered pure-hop, 5 excluded capped.

## The result

| | GA | Sr |
|---|---|---|
| paired n | 11 | 12 |
| mean ΔE_a vs undoped | **+6.8 meV** | **−4.3 meV** |
| 95% CI | [−25.0, +38.6] | [−42.2, +33.6] |
| p (paired t / Wilcoxon) | 0.644 / 0.765 | 0.807 / 0.733 |
| widest CI bound | 38.6 meV | 42.2 meV |
| **excludes the 10× target (59.5 meV)** | **yes** | **yes** |

Both additives are **null at this sample size, and the null is informative rather than
merely underpowered**: the confidence intervals are narrower than the effect the project
was designed to detect. Power at the 10× target is 0.96 (GA) and 0.88 (Sr) — both above
the conventional 0.80 — so a 10× suppression would very probably have been seen. It was
not.

**What the design could and could not have resolved** (simulated power, two-sided α=0.05,
verified by Monte-Carlo rather than a non-central-t approximation that returned NaN at
these effect sizes):

| | GA | Sr |
|---|---|---|
| minimum detectable effect at 80% power | 44 meV | 53 meV |
| n needed for the 10× target | 8 | 10 |
| n needed for a 20 meV effect | 47 | 72 |

So the corpus is adequately powered for the design target and **badly** underpowered for a
20 meV effect — roughly 4–6× more paired members would be needed. That is the honest
boundary of this dataset: it rules out the large effect, and says nothing about a small one.

## Why: the host term dominates

Restricting to the **9 host configurations admissible in all three systems** gives a
balanced 9×3 paired design, and decomposing E_a into host + system + residual:

| contribution | SD (meV) |
|---|---|
| host configuration | **57.3** |
| residual | 29.7 |
| dopant identity | **4.6** |

**The host term exceeds the dopant term by 12.3×.** The per-system means differ by only
9.3 meV across undoped/GA/Sr while the host configurations span 151.7 meV. The dopant
factor is indistinguishable from zero on this balanced design (ANOVA F=0.046, p=0.955;
Friedman p=0.895).

Note the residual SD is 29.7 meV — **not** small, and larger than either dopant mean. The
paired design is what makes the additive comparison meaningful at all: comparing
unpaired system means would drown a real effect in the host spread.

Per-system distributions over the admissible set are near-identical, which is the same
result seen from a different angle:

| system | n | E_a mean ± sd (meV) | range | saddle at image 3 | NEB fmax |
|---|---|---|---|---|---|
| undoped | 17 | 166.7 ± 70.8 | 55–268 | 100% | ≤0.0500 |
| GA | 17 | 169.4 ± 67.2 | 48–293 | 100% | ≤0.0500 |
| Sr | 15 | 169.5 ± 65.7 | 63–280 | 100% | ≤0.0498 |

Every admissible path puts its saddle at the midpoint image, so the barrier differences
are not an artifact of paths peaking at different points along the coordinate.

## Interpretation, bounded

The screening question was whether GA or Sr suppresses iodine migration. On this corpus the
answer is **no measurable suppression, with the 10× design target excluded** — and the
reason is structural: at these concentrations the additive perturbs the migration barrier
far less than the host's own configurational disorder does. A screen that varies the
additive while sampling hosts unpaired would be measuring host noise.

These are **MLIP-level** barriers (MACE-MP medium), not DFT, and the values are not
comparable across theory levels. Nothing here bears on the charge-state question.

## Stage-3 seed set

12 frames × 159 atoms parsed from the q=0 **endpoint relaxation** trajectories only, at the
production theory level (PBE+D3(BJ), degauss 0.005, Γ, nspin=1, conv_thr 1e-8):

- fmax 0.0399–0.0810 eV/Å (median 0.0548) — matches the manifest's declared range
- energy span 27.1 meV
- sources: `q0_initial.out.gz`, `q0_final_ns1.out.gz` — **no NEB-derived frame**, verified
  by source tag

The NEB archives hold far more converged frames, and they stay excluded: their per-image
energies *are* the gate-withheld barrier, so including them would smuggle it into a
training file.

## Files

- `paired_effects.csv` — all 23 pairs, per-member, with strict/recovered flag
- `analysis_summary.csv` — the two tables above as data
- `analysis_stats.json` — full statistics incl. provenance and the reproduction check
- `objective2_variance.png` — the three-panel figure

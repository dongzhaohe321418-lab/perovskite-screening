# 84-path harmonised corpus — GA reaches statistical sufficiency, and the answer is NULL

**First result in this project with adequate statistical power. GA: n = 9 paired
differences, mean +7.3 meV, 95% CI [-23.9, +38.5] — the entire interval lies inside
the ±59.5 meV significance band, and n = 9 meets the 7 required by the pessimistic variance
bound. This is an equivalence result: GA does not change the iodide migration barrier at the
order-of-magnitude-rate scale. It is not "underpowered".**

Corpus: 28 harmonised hosts × 3 systems = 84 paths (job `13fabdfd`), MACE-MP-0 medium,
float64, RTX 5090.

## Integrity audit, run before any statistics

| check | result |
|---|---|
| rows / unique member–system combos | 84 / 84, no duplicates |
| required fields present | all |
| magnitude blow-ups (\|E\| > 3 eV) | **0** |
| bands not converged | **0** |
| endpoints at target (fmax ≤ 0.02, under 800 steps) | 79 of 84 |

The 5 endpoints that hit the step cap or exceeded fmax 0.02 (`m04-GA`, `m23-Sr`,
`m23-undoped`, `m24-GA`, `m24-Sr`) are **excluded**, not silently used.

## Admission

Strict-gate valid: 30 of 84. Of the 49 remaining rejections, 30 are asymmetric wells and 27
have an interior saddle; the return test (displacement-only, ±0.02/0.05 Å) verified **21 of
27 as metastable**, of which **10 are pure asymmetric hops** and 11 are
`hop_plus_FA_reorientation` — kept as a separate distribution, never pooled.

**Pure-hop admissible: 40 of 84 (0.476).**

## Result

| | GA | Sr |
|---|---|---|
| paired n | **9** | **10** |
| mean ΔE_a (forward) | **+7.3 meV** | **-1.8 meV** |
| paired sd | 40.6 meV | 65.2 meV |
| 95% CI (Student-t) | [-23.9, +38.5] | [-48.4, +44.8] |
| TOST equivalence (±59.5 meV) | **p = 0.0024** | p = 0.0104 |
| σ 95% upper bound (χ²) | 77.8 meV | 119.0 meV |
| n required by that bound | **7 → MET at 9** | 16 → **short by 6** |
| status | **EQUIVALENT** | **SUGGESTIVE-EQUIVALENT** |

Host forward barriers over the same admissible set: n = 13, mean 162.8, sd 69.6 meV.
Pairing reduces the spread for both (69.6 → 40.6 GA, → 65.2 Sr), confirming the paired
design works.

**A correction made during this analysis:** I first wrote that Sr's CI "extends beyond the
threshold on both sides". It does not — [-48.4, +44.8] is inside ±59.5 and Sr's TOST also
passes. The real distinction is the variance-bound requirement: GA meets its own (9 ≥ 7),
so its equivalence claim survives even if the true σ sits at the top of its confidence
interval; Sr does not (10 < 16), so its equivalence is provisional pending ~6 more pairs.

## Sr's variance is driven by two configurations — both of them RESCUED, not gate-passing

`m14` gives −139.8 meV and `m20` gives +129.3 meV.

**Correction.** An earlier version of this report said both "pass every gate". That was
false and is retracted. Checking `paired_raw_84.json`: `Sr_m14` has
`gate_endpoints.passed = False` ("initial endpoint above its adjacent interior image by
71.2 meV"), and `undoped_m20` likewise ("…by 124.4 meV"). Both entered the statistic through
the **return-test rescue** route, not the strict gate. My keep/remove argument claimed there
was no distinction available to justify removing them; there was one, and I missed it.

What the two paths *do* have: converged bands, endpoints relaxed to fmax ≤ 0.02, interior
saddles at image 3, and a verified-metastable initial endpoint (all four perturbations
returned). So they are not artefacts — but they are rescued members, and that is where the
variance concentrates.

### Admission route by pair

| | strict-only pairs | pairs involving ≥1 rescued member |
|---|---|---|
| GA | 5 | 4 |
| Sr | 6 | 4 |

### Sensitivity to the rescue route

| | all pairs | strict-only |
|---|---|---|
| GA | n = 9, mean +7.3, sd 40.6 | n = 5, mean −17.9, **sd 16.7**, CI [−38.5, +2.8] |
| Sr | n = 10, mean −1.8, sd 65.2 | n = 6, mean −1.3, **sd 19.4**, CI [−21.6, +19.0] |

Both means stay well inside the ±59.5 meV band under either treatment, and the strict-only
subsets are *much* tighter. **The equivalence conclusion is robust to the rescue route** —
if anything the rescued paths are what inflate the spread, so the all-pairs figures are the
conservative ones and are what the headline reports.

The two outliers are **kept** — they are verified-metastable paths with converged bands, and
removing them would be selection on outcome. But the honest statement is that Sr's spread is
driven by two *rescued* configurations, not that Sr's effect is configuration-dependent in
some established physical sense. Whether the rescue route systematically admits
higher-variance paths is a testable question (it has 8 instances here) and is flagged for
the next expansion, not claimed.

## What may and may not be said

**May:** GA does not shift the iodide migration barrier at the 10× rate scale in this host
(equivalence, TOST p = 0.0024, adequately powered). The paired design demonstrably reduces
configurational noise. The pure-hop admissible fraction is 0.476.

**May not:** any ranking of GA against Sr — both are statistically indistinguishable from
zero and from each other. Any claim about Sr's equivalence as settled. Any transfer of these
MLIP-level numbers to a DFT-level statement. Any pooling of the `hop_plus_FA_reorientation`
distribution with the pure-hop statistic.

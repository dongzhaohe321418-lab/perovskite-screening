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

## Sr's variance is driven by two configurations — and that is the finding

`m14` gives −139.8 meV and `m20` gives +129.3 meV. Both pass every gate: bands converged,
endpoints at fmax ≤ 0.02, interior saddles at image 3. Excluding them would drop Sr's sd
from 65.2 to 16.9 meV — which is exactly why they are **kept**: there is no defensible
criterion for removing them beyond inconvenience.

The physical reading: Sr's effect on the barrier is strongly **configuration-dependent**
where GA's is not (GA's largest deviation is +71.7 meV, and its sd is 40.6 across 9 pairs).
Whether that reflects real Sr–vacancy coupling in particular FA arrangements or MLIP
sensitivity on those two hosts is not decidable at this level of theory, and is flagged
rather than claimed.

## What may and may not be said

**May:** GA does not shift the iodide migration barrier at the 10× rate scale in this host
(equivalence, TOST p = 0.0024, adequately powered). The paired design demonstrably reduces
configurational noise. The pure-hop admissible fraction is 0.476.

**May not:** any ranking of GA against Sr — both are statistically indistinguishable from
zero and from each other. Any claim about Sr's equivalence as settled. Any transfer of these
MLIP-level numbers to a DFT-level statement. Any pooling of the `hop_plus_FA_reorientation`
distribution with the pure-hop statistic.

# 108-path merged corpus — both additives equivalent to no effect by the CI test

**36 hosts × 3 systems = 108 paths. Both GA and Sr now have 95% confidence intervals lying
entirely inside the ±59.5 meV significance band, and both meet their variance-bound sample
requirement. The CI test — not the sample-size threshold — is what carries these claims, for
the reason given in §5.**

## 1. Provenance and the pooling decision

Two batches: the 84-path corpus (job `13fabdfd`, hosts m00–m27) and the 24-path extension
(job `41ac4172`, hosts m28–m35). Identical driver settings, identical MACE-MP-0 medium /
float64 / RTX 5090, identical 7-image bands.

**Pooling was not automatic.** The extension's strict-gate yield was 4/24 against 30/84 in the
first batch, a visible difference that had to be explained first:

| | strict pass | endpoint-not-a-minimum | other |
|---|---|---|---|
| 84-batch | 30 | 38 | 16 |
| 24-batch | 4 | 15 | 5 |

Fisher exact on pass/fail: **odds ratio 2.78, p = 0.0867** — consistent with chance at these
sample sizes, and the rejection-reason profile is the same shape in both. The host pool also
passed its own homogeneity gate (−31.5 meV, Welch p = 0.6422, 0.20σ, all energies and fmax
measured — see `../../fa_host/pool_v3_harmonised/HOST_MANIFEST.md`). Pooling proceeds on that
basis.

## 2. Integrity pass on the merged set, run before any statistics

| check | result |
|---|---|
| total rows | **108** (84 + 24) |
| unique member–system combos | **108**, zero duplicates |
| images per band | **[7]** — identical across both batches |
| bands not converged | **0** |
| magnitude blow-ups (\|E\| > 3 eV) | **0** |
| capped/over-target rows leaking into the admissible set | **0** — exclusion held |
| admissible rows above the 0.02 endpoint target | **0** |

The five rows excluded from the first batch (`m04-GA`, `m23-Sr`, `m23-undoped`, `m24-GA`,
`m24-Sr`) were verified absent from the admissible set. The extension contributed **zero**
exclusions (max endpoint fmax exactly 0.0200 on both ends).

## 3. Admission

    strict-gate valid, both batches (capped excluded)     34
    pure-hop recovered via return test                     15   (10 from batch 1, 5 from batch 2)
    ----------------------------------------------------------
    pure-hop admissible                                    49 / 108 = 0.454

Extension return test: **14 of 14 candidates verified metastable** (56 perturbation
relaxations, all converged, median max displacement 0.032 Å), of which 5 are
`pure_hop_asymmetric` and 9 are `hop_plus_FA_reorientation` — the latter kept as a separate
distribution, never pooled.

## 4. Result

| | GA | Sr |
|---|---|---|
| paired n | **11** (was 9) | **12** (was 10) |
| members | [5, 6, 8, 10, 12, 15, 18, 20, 21, 30, 32] | [4, 5, 6, 8, 12, 14, 15, 20, 21, 27, 30, 32] |
| individual ΔE_a (meV) | [-11.4, -17.0, 4.5, 66.5, -38.0, 71.7, -30.1, 33.7, -14.3, 72.5, -63.2] | [-7.4, -30.2, 19.2, -14.7, 13.8, -139.8, 7.9, 129.3, -7.8, 11.8, -32.6, -1.3] |
| mean ΔE_a | **+6.8 meV** (was +7.3) | **-4.3 meV** (was -1.8) |
| paired sd | 47.4 meV (was 40.6) | 59.6 meV (was 65.2) |
| **95% CI (Student-t)** | **[-25.0, +38.6]** | **[-42.2, +33.6]** |
| entire CI inside ±59.5 meV | **yes — 35% margin** | **yes — 29% margin** |
| TOST equivalence p | **0.0021** | **0.0042** |
| σ 95% upper bound (χ²) | 83.1 meV | 101.2 meV |
| n required by that bound | 8 → **MET at 11** | 12 → **MET at 12** |

## 5. Sr's threshold cleared MOSTLY MECHANICALLY — the CI is what carries the claim

The χ² requirement falls as n rises even at constant variance. Decomposing Sr's drop from
n_req 16 to 12:

    n=12 with the OLD sd (65.2 meV) -> n_req 14      => 2 points from sample size alone
    n=12 with the NEW sd (59.6 meV) -> n_req 12      => 2 points from variance actually falling

So **half the clearing is mechanical**. The variance did fall (65.2 → 59.6 meV), which is real
but small. Per the rule agreed with the PI, the judgement therefore rests on the confidence
interval:

- **GA**: widest CI excursion 38.6 meV against the 59.5 meV threshold → **35% margin**.
- **Sr**: widest CI excursion 42.2 meV → **29% margin**. Equivalent by the CI test, but with
  noticeably less room than GA.

## 6. Sensitivity to the rescue route

| | all pairs | strict-only |
|---|---|---|
| GA | n=11, mean +6.8, sd 47.4, CI [−25.0, +38.6] | n=6, mean −2.8, sd 39.8, CI [−44.6, +39.0] |
| Sr | n=12, mean −4.3, sd 59.6, CI [−42.2, +33.6] | n=7, mean −5.8, **sd 21.3**, CI [−25.4, +13.9] |

Admission route per pair: GA 6 strict / 5 with ≥1 rescued member; Sr 7 strict / 5. Both means
stay inside the band under either treatment. Sr's strict-only subset is much tighter
(sd 21.3 vs 59.6), consistent with the rescued paths carrying the variance — so the all-pairs
figures reported above are the conservative ones.

## 7. What may and may not be said

**May:** under the current FA-host ensemble (36 harmonised members, fmax 0.02), the pure-hop
barrier definition, and the MACE-MP-0 potential-energy surface, **both GA and Sr change the
iodide migration barrier by an amount practically equivalent to zero within ±59.5 meV**
(a 10× hop-rate scale). GA's margin is the larger of the two.

**May not:** any GA-vs-Sr ranking — both are statistically indistinguishable from zero and from
each other. Any claim that either additive has no effect on FAPbI₃ migration in general. Any
presentation of these MACE numbers as DFT or experimental barriers. Any pooling of the
`hop_plus_FA_reorientation` distribution into this statistic. Any citation of the n_req
threshold as evidence that Sr's effect is small (§5).

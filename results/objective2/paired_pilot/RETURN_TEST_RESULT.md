# Priority A — local-stability return test: RESULT

**23 of 27 asymmetric-well initial endpoints are verified metastable local minima. The
low pass rate was never an endpoint problem. But only 16 of those 23 currently have a
usable band, and only 5 are pure hops — so the pure-hop admissible pool grows from 19 to
24 of 54 (0.352 → 0.444), not to 46.**

## Protocol (as specified)

Perturb the relaxed initial endpoint along the initial→image-1 direction (minimum-image),
both signs, amplitudes 0.02 and 0.05 Å, fixed cell; re-relax with the endpoint protocol
(fmax 0.02, 2000 steps); compare to the original basin.

**v1 of this test was void and was cancelled.** It scaled the direction by √N ("per-atom
RMS = amp"), giving total displacements of 0.31/0.76 Å — 24–61% of the whole initial→image-1
segment, past image 1 for three paths, with single-atom moves to 0.65 Å against a 0.15 Å
return tolerance. It measured "does a large step along the path roll downhill" (trivially
yes for an exothermic hop), not local stability. v2 normalises by the max per-atom
displacement, so the largest atomic move equals the amplitude exactly. Regression test [13]
added.

**One further criterion correction, made after seeing the data.** v2's return test combined
a displacement check (<0.15 Å) with an energy check (|ΔE| < 5 meV). The energy check was the
binding one — it failed 81 of 108 relaxations — and it was miscalibrated: endpoints are
converged to fmax = 0.02 eV/Å, which leaves up to *232 × 0.02 × 0.03 ≈ 139 meV* of residual
descent available at a 0.03 Å displacement. Tens of meV at sub-0.05 Å displacement is an
incomplete relaxation finishing, not a basin change.

**This criterion choice is consequential and produced the headline result — stated plainly
rather than minimised.** With the energy rule: 27 of 108 relaxations pass and **2 of 27**
endpoints are metastable. Without it: 103 of 108 and **23 of 27**. Seventy-six relaxation
verdicts and twenty-one endpoint verdicts turn on this decision. An earlier version of this
report claimed dropping it "changes nothing about which relaxations pass"; that was false
and is retracted.

What justifies the choice is narrower and does hold: **the energy rule reclassifies no basin
change.** All 5 relaxations that left the basin (displacement ≥ 0.15 Å) already fail on
displacement, and 0 of them would have been caught by energy alone. So every one of the 76
flips is a structure that stayed put geometrically (median displacement 0.037 Å) while
finishing its relaxation energetically — which is precisely what the fmax = 0.02 eV/Å
convergence leaves on the table, and not evidence of a basin change. The criterion is
retired because it measures relaxation completeness, not basin identity.

## Result

| outcome | n | meaning |
|---|---|---|
| **verified metastable** | **23** | all 4 perturbations relax back inside 0.15 Å |
| multi_basin_ambiguous | 4 | outcome depends on amplitude or sign (m04-undoped, m04-Sr, m10-Sr, m17-undoped) |

Of the 108 perturbation relaxations: 39 relaxed back *inside* the perturbation amplitude,
64 stayed nearby, 5 left the neighbourhood. All converged.

## But a metastable endpoint does not make the band usable

Seven of the 23 have a band whose maximum sits at image 0 — no forward barrier. That looked
like a contradiction, so I checked the geometry rather than labelling them barrierless:

    m11-GA  image1 max atom move 0.285 A, 18 atoms >0.15 A
    m14-und 0.247 A, 13 atoms      m14-Sr 0.243 A, 16 atoms
    m16-und 0.302 A, 11 atoms      m16-Sr 0.321 A, 13 atoms
    m15-Sr  0.193 A,  2 atoms      m17-GA 0.048 A,  0 atoms

For six of them image 1 sits 4–6× further than the perturbation ever probed: the endpoint
is a genuine minimum **and** the band's interior images collapsed into a different, lower
channel. Label `band_collapsed` — recoverable by recomputing the band (more images / tighter
spring), not by rejecting the endpoint. m17-GA is different: image 1 is 0.048 Å away, inside
the perturbation scale, yet 32.8 meV lower — the endpoint is force-converged but not
energy-converged, exactly the residual-descent effect above. Label
`endpoint_energy_unconverged`.

## Final classification of the 27

| label | n | admissible now? |
|---|---|---|
| `pure_hop_asymmetric` | **5** | **yes — enters the pure-hop statistic** |
| `hop_plus_FA_reorientation` | **11** | yes, as a **separate** distribution — never pooled |
| `band_collapsed` | 6 | no — recoverable with a recomputed band |
| `endpoint_energy_unconverged` | 1 | no — recoverable with a tighter endpoint |
| `multi_basin_ambiguous` | 4 | no — excluded pending an explicit basin protocol |

### The 5 recovered pure asymmetric hops

| path | E_a forward | E_a reverse | ΔE endpoints |
|---|---|---|---|
| m00 undoped | 172.2 meV | 276.6 meV | −104.4 meV |
| m03 Sr | 268.2 | 377.5 | −109.3 |
| m06 GA | 102.9 | 234.0 | −131.0 |
| m09 undoped | 96.2 | 179.0 | −82.8 |
| m15 undoped | 43.0 | 276.6 | −233.6 |

## Effect on the sampling plan — recomputed from PAIRS

Pure-hop admissible paths: 24 of 54 (0.444, up from 0.352). But the plan must use the
**paired** rate, computed by requiring both members of a pair to be admissible:

| | before recovery | after recovery |
|---|---|---|
| GA valid pairs | 4 | **7** (members 3, 5, 6, 8, 9, 10, 15) |
| Sr valid pairs | 4 | **7** (members 0, 3, 5, 6, 8, 9, 12) |
| paired rate per host | 0.222 | **0.389** |
| hosts for n = 10 pairs | 45 | **26** |
| paths (3 systems) | 135 | **78** ≈ 3.0 GPU-h at 137 s/path |

**Cost correction (self-caught).** The 26-host / 78-path / 3.0 GPU-h figure counts *all* 26
hosts. Eighteen already exist and their paths are the n = 7 data — they are not recomputed.
The **incremental** batch is **8 new host members → 24 new paths ≈ 0.9 GPU-h**, plus pool
generation. The 78-path figure is the total corpus size at n = 10, not the work remaining.

## Statistics at n = 7 (forward barriers, pure-hop only)

| | GA | Sr |
|---|---|---|
| n pairs | 7 | 7 |
| mean ΔE_a | +29.2 meV | +13.7 meV |
| paired sd | 63.4 meV | 54.2 meV |
| 95% CI (Student-t) | [-29.5, +87.8] | [-36.3, +63.8] |
| σ 95% upper bound (χ²) | 139.5 meV | 119.3 meV |
| n required (upper bound) | 22 | 16 |
| **resolvable at ±59.5 meV?** | **no** | **no** |

Host spread over the same admissible set: n = 9, mean 178.7, sd 92.8 meV.
Pairing reduces the spread for both (92.8 → 63.4 for GA, → 54.2 for Sr), confirming
the paired design works — but both confidence intervals still straddle zero, and neither
mean approaches the 59.5 meV significance scale. **No ranking, and no directional claim
about either dopant.**

Note these ΔE_a are *forward* barriers under the newly adopted definition, so they are not
directly comparable to the earlier saddle-minus-initial values computed before the
asymmetric paths were admitted.

## Claims allowed / prohibited

- Allowed: the asymmetric wells are overwhelmingly real metastable states (23/27); the
  rejection pool was not an endpoint-relaxation artefact.
- Prohibited: pooling `hop_plus_FA_reorientation` with pure hops; any ranking (still n≈4
  pairs); treating 0.444 as the paired pass rate.

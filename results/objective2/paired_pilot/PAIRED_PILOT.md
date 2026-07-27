# Objective C — undoped / GA / Sr paired pilot

**54 paths run (18 host members × 3 systems). 18 passed the validity gates.
Neither dopant is resolvable at this sample size — and the pilot's job was to establish
that, not to rank them.**

Level: MACE-MP-0 medium, CUDA, float64, CI-NEB improvedtangent. Tier: **EXPLORE**. No
ranking is published.

## Result

| | GA | Sr |
|---|---|---|
| valid pairs | 2 | 4 |
| paired ΔE_a (meV) | [-34.2, 85.8] | [-58.4, 31.8, -12.8, 0.3] |
| mean | +25.8 meV | -9.8 meV |
| **s_ΔEa** | **84.9 meV** | **37.4 meV** |
| SE | 60.0 meV | 18.7 meV |
| 95% CI | [-91.8, +143.5] meV | [-46.4, +26.9] meV |
| updated n required | **9** | **2** |
| verdict | NOT RESOLVABLE | NOT RESOLVABLE |

Both confidence intervals straddle zero and lie inside the ±59.5 meV band. There is no
evidence at this n that either dopant changes the barrier by a resolvable amount, and no
ranking may be drawn.

## Does pairing work? Yes for Sr, no for GA

This is the pilot's primary question, and the two dopants answer it differently.

    unpaired sigma (undoped host):  73.3 meV
    Sr  s_dEa:                      37.4 meV   -> pairing REDUCES variance
    GA  s_dEa:                      84.9 meV   -> pairing does NOT help

For **Sr** the paired difference is roughly half as variable as the raw barrier, so the
host-configuration term is cancelling as intended. The required sample size falls from
n ≥ 13 (unpaired) to **n ≥ 2**.

For **GA** the paired scatter is *larger* than the host's own. Pairing can only remove
variance the two legs share; if the dopant itself perturbs the migration channel differently
in each orientation, that variance is introduced by the dopant and survives the subtraction.
GA⁺ is substantially larger than the FA⁺ it replaces, so this is a plausible physical
reading — but with n = 2 it is a hypothesis, not a finding.

**Consequence for the screening design:** the sample size cannot be set once for all
dopants. It must be set per dopant from that dopant's own s_ΔEa. A large A-site substituent
may need many times the sampling a small B-site one does.

## Validity yield, and a gate that had to be added mid-analysis

18 of 54 paths passed. The dominant rejection is an endpoint lying above its adjacent
interior image by 30-130 meV — the NEB finds interior configurations below an endpoint.

**Why is not established, and this dataset cannot settle it.** Two readings compete:

- *physical* — in a soft multi-basin host the endpoints are minima in their own basin but
  not the relevant minima connected by the path, so 33% is the honest yield of the method;
- *numerical* — the endpoint relaxations did not reach their force target, so the endpoints
  are simply under-relaxed.

Separating them needs the achieved endpoint `fmax` per path, and **this run does not carry
it**: the per-endpoint recording was added to `scripts/22_paired_pilot.py` *after* the job
was submitted, so all 54 rows in `paired_results.json` lack the `endpoint_relax` field. The
requested settings were `--endpoint-fmax 0.02 --endpoint-steps 800`; what was *achieved* is
unrecorded.

Two spot checks from single runs outside this set are consistent with the physical reading
but far too few to establish it:

| run | initial fmax | final fmax | steps used (cap 800) |
|---|---|---|---|
| local validation, new-pool m00 undoped | 0.0168 | 0.0142 | 197 / 435 |
| discriminator, old-pool member 2 | 0.0175 | 0.0185 | 269 / 254 |

**Action:** the next run records `endpoint_relax` per path, at which point the readings
separate directly — rejected paths with converged endpoints support the physical reading;
rejected paths sitting at the step cap mean the budget is simply too small. Until then the
33% yield is reported as an observation, not a diagnosis.

**3 paths were caught as MLIP failures**, including one GA band with E_a = 77,400 meV
and interior images at −323,356 meV. Both shape gates passed it: the profile rises then
falls, and only one atom moves. The gates test ordering, not magnitude. A magnitude bound
(3 eV, well above any halide-perovskite migration barrier) now rejects these.

This matters beyond bookkeeping: **the +1034 meV GA outlier that dominated an earlier
interim read was itself one of these blow-ups.** Had it survived, it would have inflated
GA's s_ΔEa to 585 meV and implied n ≥ 387 — an artefact presented as a physical finding
about a large cation blocking the channel.

## What is needed next

1. **More pairs.** Only 2 GA and 4 Sr pairs survived from 18 members. At a 33% yield,
   reaching n = 10 valid pairs needs ~30 members per system.
2. **Per-dopant sample sizes**, from each dopant's own s_ΔEa rather than one global n.
3. **Understand the GA scatter** before screening large A-site substituents — with n = 2,
   whether it is physical or methodological is genuinely open.
4. **Record `endpoint_relax` per path** (already in the script, missing from this run) so
   the 33% yield can be attributed to the landscape or to the relaxation budget.

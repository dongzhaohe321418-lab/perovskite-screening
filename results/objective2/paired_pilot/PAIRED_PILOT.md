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
interior image by 30-130 meV: the NEB finds configurations below endpoints that had
themselves converged to fmax ≤ 0.02. In a soft multi-basin host the endpoints are minima in
their own basin but not the relevant minima connected by the path. That is a property of the
system, not a numerical failure, and 33% is the honest yield of this method here.

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

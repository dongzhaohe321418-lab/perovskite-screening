# Paired pilot RERUN — clean data supersedes the retracted run

**54 paths rerun with the fixed driver (tag-tracked migrating ion, convergence-required
validity, force norms). Every question the audit left open is now answered with measured
data. Neither dopant shows a resolvable effect; the sampling arithmetic is now trustworthy.**

Level: MACE-MP-0 medium, CUDA, float64, CI-NEB improvedtangent. Tier: EXPLORE. No ranking.

## Integrity checks run before reading any statistics

| check | result |
|---|---|
| all 54 rows carry endpoint_relax / valid_shape_only / converged_all / migrating_index_doped | **54/54** |
| GA migrating index shifts by exactly 1 on all 8 previously-broken members | **8/8** |
| bands with \|E_a\| > 3 eV (the retracted run had 3) | **none** |
| Sr values identical to the retracted run (Sr was unaffected — a free reproducibility check) | **yes, to 0.1 meV** |

The disappearance of all three magnitude blow-ups once the correct atom is moved **confirms
they were the index bug**, not out-of-distribution MLIP behaviour. That retraction stands,
now with positive evidence.

## The P2 question is settled: the yield is the landscape, not the budget

The previous run could not distinguish "endpoints under-relaxed" from "genuine multi-basin
landscape" because it never recorded the achieved endpoint force. This run does:

| | |
|---|---|
| endpoints hitting the 2000-step cap | **0 / 54** |
| both endpoints converged | **54 / 54** |
| achieved endpoint fmax (per-atom norm) | mean 0.0197, worst 0.0200 (target 0.02) |
| rejected paths that are fully converged | **34 / 35** |

Every endpoint reached its force target with room to spare, yet 35 paths still fail the
shape gates — converged calculations whose band finds interior configurations below an
endpoint. **The endpoints are minima of their own basin but not the relevant minima
connected by the path.** Per the audit's P2 fork, this is the multi-basin branch: the next
methodological step for the invalid paths is basin identification (does an FA reorientation
accompany the hop?), not a bigger relaxation budget.

## Paired statistics (Student-t, χ² bound on σ — per the corrected protocol)

| | GA | Sr |
|---|---|---|
| valid pairs | 4 (m03, m05, m08, m10) | 4 (m05, m06, m08, m12) |
| paired ΔE_a (meV) | −34.2, +3.8, +41.1, +85.8 | −58.4, +31.8, −12.8, +0.3 |
| mean | +24.1 | −9.8 |
| s_ΔEa | 51.4 | 37.4 |
| 95% CI (t, df=3) | [−57.6, +105.8] | [−69.3, +49.8] |
| 95% upper bound on σ | 150.0 | 109.2 |
| n required (point → bound) | 3 → 26 | 2 → 14 |
| verdict | **not resolvable** | **not resolvable** |

Undoped baseline in this pool: n = 6, mean 216.2 meV, sd 83.9 meV.

**GA's picture changed materially with the bug fixed.** The retracted run showed GA scatter
(84.9) exceeding the host's own — the basis for the "large cation disrupts the channel"
hypothesis. With the correct atom moving, GA's s_ΔEa is **51.4 meV, below the 83.9 meV host
scatter**: pairing now works for GA too. m05, the member behind the +1034 meV artefact,
contributes +3.8 meV. The disruption hypothesis is **withdrawn**, not merely unproven — the
clean data point the other way.

## Sampling arithmetic (observed paired rates)

Both dopants now pass 4/18 pairs = 0.222, twice the independence expectation (0.333² =
0.111): undoped and doped failures cluster on the same members here too. Hosts for 10 valid
pairs: **45 per dopant** (~3.4 GPU-h each at the measured 137 s/path, undoped leg shared).

## What remains true

Neither dopant is resolvable at n = 4, and the χ² bounds say the *final* n cannot be set
from these estimates — they are planning numbers. The next screening tranche should target
n ≈ 10 pairs per dopant and re-derive n from the tighter s_ΔEa that gives.

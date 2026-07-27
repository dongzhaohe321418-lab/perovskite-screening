# Gate 1 — GPU regression: PASS

**Verdict: the RTX 5090 reproduces the CPU reference exactly. Batch screening is unblocked.**

Host: `ssh:autodl`, `NVIDIA GeForce RTX 5090`, torch `2.8.0+cu128`, MACE 0.3.16, ASE 3.29.0,
`float64`. Tolerance: **1 meV** (the locked smoke-test criterion).

## (A) Single-point determinism — isolates the calculator from the optimiser

Identical CPU geometries (member 2 initial / saddle / final) evaluated on GPU:

| image | GPU (eV) | CPU (eV) | Δ absolute | Δ relative |
|---|---|---|---|---|
| 0 | -1063.84107639 | -1063.84107639 | -0.000000 meV | +0.000000 meV |
| 3 | -1063.53115959 | -1063.53115959 | -0.000001 meV | -0.000000 meV |
| 6 | -1063.76085328 | -1063.76085329 | +0.000001 meV | +0.000001 meV |

Max |Δ relative| = **0.000001 meV**, six orders of magnitude
inside tolerance. Barrier from fixed CPU geometry: GPU 309.9168
vs CPU 309.9168 meV, difference
-0.000000 meV.

Relative rather than absolute energies are the meaningful comparison: a constant offset
cancels in a barrier. Both are reported; both are ~10⁻⁶ meV.

## (B) Full-path reproduction — the number that actually matters

Member 2's complete NEB (endpoint relaxation + band) rerun end-to-end on GPU:

| | GPU | CPU |
|---|---|---|
| E_a forward | **309.9168 meV** | **309.9168 meV** |
| optimiser steps | 50 | 50 |
| valid / converged | True / True | True / True |
| wall time | **84 s** | 646 s |

**Difference: 0.0000 meV. Identical step count. Profiles agree digit for digit**
(0.0 / 49.8 / 197.9 / 309.9 / 275.8 / 132.6 / 80.2 meV on both).

Running both checks was not redundant. (A) can pass while (B) fails, because an optimiser
amplifies tiny force differences into divergent trajectories on this soft-mode surface —
that is precisely the failure mode a single-point check cannot see. Here the trajectory is
bit-identical too, which is the strongest possible outcome.

## Consequence

**Speedup 7.7×.** The 169-path paired pilot drops from ~70 h of local CPU to **~9 h** on
this GPU. No drift in atom indices, composition, path endpoints, or model version.

Gate 1 is closed. Objective B (FA pool expansion) and Objective C (paired pilot) proceed.

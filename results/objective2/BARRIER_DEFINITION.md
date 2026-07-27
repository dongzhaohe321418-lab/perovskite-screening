# Barrier definition — ADOPTED (2026-07-27)

**Primary screening metric:**

> The **forward barrier** from an initial state *verified as a local minimum* (return
> test) to the hop saddle, recording alongside it: (a) the final-state energy relative to
> the initial state (endpoint asymmetry), and (b) a mechanism label.

Rationale: in a disordered FA host the two iodide sites connected by a hop are generically
inequivalent; forward and reverse barriers need not match, and a final state 50–563 meV
lower is part of the material's local environment, not an error to symmetrise away.

## Admission rule for the 27 asymmetric-well paths

An initial endpoint enters the screening statistic only after passing the **return test**
(scripts/24_return_test.py): perturbations of ±0.02 and ±0.05 Å per-atom RMS along the
initial→first-image direction must all relax back to the initial basin (< 0.15 Å, < 5 meV).
Fail → not a definable hop origin → excluded from the pure-hop statistic.

## Mechanism labels

| label | meaning | in screening ranking? |
|---|---|---|
| `iodide_hop` | pure hop, FA orientations essentially unchanged | yes |
| `iodide_hop+FA_reorientation` | ≥1 FA atom displaced >0.8 Å between endpoints | kept, separate distribution — never mixed into the pure-hop ranking |

## Two result tiers (locked)

| tier | definition | use |
|---|---|---|
| **equilibrium forward barrier** | FA relaxes freely with each endpoint; forward/reverse barriers, asymmetry and mechanism label recorded | **primary screening**, initial state must pass the return test |
| conditional pure-hop barrier | FA orientations constrained to isolate the iodide hop | mechanism diagnostics only, on a few representative members; never mixed with tier 1 in a ranking |

## Sequential sampling plan (locked)

1. Return test on the 27 asymmetric-well paths → update the effective paired pass rate.
2. Expand to ~10 valid pairs per dopant (45 shared hosts ≈ 135 paths ≈ 5 GPU-h + margin).
3. Recompute Student-t intervals and χ² variance bounds at n≈10.
4. Only if |mean ΔE_a| > 59.5 meV *and* the uncertainty is below that scale → expand
   further / discuss ranking. Current bounds (GA ≤ 26 pairs, Sr ≤ 14) are planning
   ceilings, not commitments.

## Objective 1 boundary (unchanged)

HPC remains restricted to small static benchmarks for q=0 (projection + IPR done;
convergence ladder closed; supercell-size test is the open decision). No full q=0/q=+1
CI-NEB until a theory scheme delivers reliable forces — regardless of Objective 2's GPU
pipeline being healthy.

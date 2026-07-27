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
(scripts/24_return_test.py): perturbations of ±0.02 and ±0.05 Å (scaled so the *largest
single-atom move* equals the amplitude) along the initial→first-image direction must all
relax back to within **0.15 Å** of the initial configuration. **Displacement is the sole
criterion** — an energy tolerance was tried and retired as miscalibrated against the
endpoints' own fmax = 0.02 eV/Å convergence (see `paired_pilot/RETURN_TEST_RESULT.md`);
ΔE is recorded for diagnosis only. Fail → excluded from the pure-hop statistic.

Passing the return test is necessary but **not sufficient** for a usable barrier: the band
must also have an interior saddle. Endpoints that are metastable but whose band collapsed
into another channel are labelled `band_collapsed` and are recoverable by recomputing the
band, not by rejecting the endpoint.

## Mechanism labels

| label | meaning | in screening ranking? |
|---|---|---|
| `iodide_hop` | pure hop, FA orientations essentially unchanged | yes |
| `iodide_hop+FA_reorientation` | ≥1 FA atom displaced >0.8 Å between endpoints | kept, separate distribution — never mixed into the pure-hop ranking (currently 11 paths) |
| `band_collapsed` | endpoint metastable, band relaxed into another channel | excluded until the band is recomputed (6 paths) |
| `multi_basin_ambiguous` | return-test outcome depends on amplitude or sign | excluded pending an explicit basin protocol (4 paths) |

## Two result tiers (locked)

| tier | definition | use |
|---|---|---|
| **equilibrium forward barrier** | FA relaxes freely with each endpoint; forward/reverse barriers, asymmetry and mechanism label recorded | **primary screening**, initial state must pass the return test |
| conditional pure-hop barrier | FA orientations constrained to isolate the iodide hop | mechanism diagnostics only, on a few representative members; never mixed with tier 1 in a ranking |

## Sequential sampling plan (locked)

1. ~~Return test on the 27 asymmetric-well paths~~ **DONE** (2026-07-27): 23/27 verified
   metastable; 5 pure hops recovered into the statistic. Paired rate 0.222 → **0.389**.
2. Expand to ~10 valid pairs per dopant: **26 shared hosts ≈ 78 paths ≈ 3.0 GPU-h** at the
   measured 137 s/path, plus margin. (Supersedes the pre-return-test 45/135/5 estimate.)
3. Recompute Student-t intervals and χ² variance bounds at n≈10.
4. Only if |mean ΔE_a| > 59.5 meV *and* the uncertainty is below that scale → expand
   further / discuss ranking. Current bounds (GA ≤ 26 pairs, Sr ≤ 14) are planning
   ceilings, not commitments.

## Objective 1 boundary (unchanged)

HPC remains restricted to small static benchmarks for q=0 (projection + IPR done;
convergence ladder closed; supercell-size test is the open decision). No full q=0/q=+1
CI-NEB until a theory scheme delivers reliable forces — regardless of Objective 2's GPU
pipeline being healthy.

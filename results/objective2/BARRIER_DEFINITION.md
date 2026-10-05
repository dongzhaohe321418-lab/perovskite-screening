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

*(2026-10-05: the 11/6/4 "currently" counts above are from the 54-path, 18-host return test of
2026-07-27, `paired_pilot/RETURN_TEST_RESULT.md`. In the final 108-path corpus the separate
`hop_plus_FA_reorientation` distribution is 20 paths: 11 from the 84-batch
(`paired_pilot/CORPUS84_RESULT.md`) + 9 from the 24-path extension
(`paired_pilot/CORPUS108_RESULT.md` §3).)*

## Two result tiers (locked)

| tier | definition | use |
|---|---|---|
| **equilibrium forward barrier** | FA relaxes freely with each endpoint; forward/reverse barriers, asymmetry and mechanism label recorded | **primary screening**, initial state must pass the return test |
| conditional pure-hop barrier | FA orientations constrained to isolate the iodide hop | mechanism diagnostics only, on a few representative members; never mixed with tier 1 in a ranking |

## Sequential sampling plan (locked)

1. ~~Return test on the 27 asymmetric-well paths~~ **DONE** (2026-07-27): 23/27 verified
   metastable; 5 pure hops recovered into the statistic. Paired rate 0.222 → **0.389**.
2. ~~Expand to ~10 valid pairs per dopant:~~ **DONE** (2026-07-28; marked 2026-10-05): expanded
   to 36 hosts / 108 paths, GA n=11, Sr n=12, see `paired_pilot/CORPUS108_RESULT.md`. Original
   plan, retained: **26 shared hosts ≈ 78 paths ≈ 3.0 GPU-h** at the
   measured 137 s/path, plus margin. (Supersedes the pre-return-test 45/135/5 estimate.)
   **Incremental cost is smaller:** 18 hosts already exist, so only **8 new members →
   24 new paths ≈ 0.9 GPU-h** are required; 78 is the total corpus at n = 10.
3. ~~Recompute Student-t intervals and χ² variance bounds at n≈10.~~ **DONE** (2026-07-28;
   marked 2026-10-05): recomputed at GA n=11 / Sr n=12, 95% CIs [−25.0, +38.6] / [−42.2, +33.6]
   meV, χ² sample requirement met (8 at 11; 12 at 12), see `paired_pilot/CORPUS108_RESULT.md` §4.
4. Only if |mean ΔE_a| > 59.5 meV *and* the uncertainty is below that scale → expand
   further / discuss ranking. Current bounds (GA ≤ 26 pairs, Sr ≤ 14) are planning
   ceilings, not commitments.
   *(2026-10-05: not triggered: |mean ΔE_a| 6.8 / 4.3 meV < 59.5 meV and both 95% CIs lie
   inside ±59.5 meV, `paired_pilot/CORPUS108_RESULT.md` §4; the ceilings above are historical
   planning figures. Next-stage sampling is set by `analysis/NEXT_EXPERIMENT_DESIGN.md` v2.)*

## Objective 1 boundary (unchanged)

HPC remains restricted to small static benchmarks for q=0 (projection + IPR done;
convergence ladder closed; supercell-size test is the open decision). No full q=0/q=+1
CI-NEB until a theory scheme delivers reliable forces — regardless of Objective 2's GPU
pipeline being healthy.

*(Superseded 2026-10-05: the PI authorized the production q=0/q=+1 CI-NEB on 2026-07-28; both
legs converged (q=0 36 / q=+1 37 iterations,
`../objective1/dft/charge_relaxed/PRODUCTION_NEB_STATUS.md`) and the barriers were extracted
2026-08-05 (V_I⁰ 185.6 / V_I⁺¹ 181.7 meV, difference −3.9 meV bare PBE+D3, FNV residual
pending), see `../objective1/dft/charge_relaxed/CHARGE_STATE_ANCHOR.md`.)*

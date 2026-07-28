# Host pool expansion +8 (28 → 36) — homogeneity gate passed before pooling

**Purpose: push Sr from n = 10 toward its variance-bound sample requirement. GA is already
adequate (n = 9 vs required 7).**

## The homogeneity gate, run BEFORE pooling

This is the check that caught the earlier failed expansion, where new members sat 643 meV
below the existing pool at 2.24σ (p < 1e-4) because the two batches had been relaxed to
different force targets.

| | existing `pool_v3_harmonised` (18 with recorded energies) | new 8 |
|---|---|---|
| mean E (eV) | −1065.9719 ± 0.1338 | −1066.0085 ± 0.1707 |
| offset | — | **−36.6 meV** |
| Welch t / p | — | **t = 0.54, p = 0.6018** |
| separation | — | **0.24σ** |

**Same population, poolable without harmonisation.** The reason this worked: identical
sampler (carbon-pivot rotation with minimum-image vectors) *and* identical `fmax = 0.02`.
Relaxation depth is part of the pool's identity, which is the rule adopted after the earlier
failure.

Acceptance of the new members: **8/8**, all with fmax ≤ 0.0192, all Pb 6-fold coordinated,
all 19 FA molecules intact. Installed as `m28`–`m35`; record in `expansion_plus8.json`.

## Expected effect on the statistics

At the observed pair yield (Sr 0.357/host, GA 0.321/host), 8 hosts should add ~3 Sr and
~2.6 GA pairs, taking Sr to n ≈ 13 and GA to n ≈ 12.

## A property of the sample-size criterion, flagged rather than exploited

The variance-bound requirement **falls as n rises even when the variance does not change**,
because the χ² upper bound on σ tightens with degrees of freedom. Holding sd at exactly the
observed 65.2 meV:

    n=10 -> sigma_hi 119.0 -> n_req 16   (short)
    n=12 -> sigma_hi 110.7 -> n_req 14   (short)
    n=13 -> sigma_hi 107.6 -> n_req 13   (MET -- self-clearing)
    n=20 -> sigma_hi  95.2 -> n_req 10   (MET)

So Sr's criterion will likely read "met" at n = 13 without any new evidence that its effect
is small. **The Sr write-up must therefore report the substantive question — does the CI stay
inside ±59.5 meV as n grows — and must not present a mechanically-clearing threshold as
evidence.** The pre-registered criterion stands as agreed; this records a property of it, not
a change to it.

This does not weaken GA's result, which passes on three independent grounds: n = 9 against a
required 7, a CI well inside the band, and TOST p = 0.0024.

## Invocation failures — third instance, now guarded

The first submission of this expansion exited 0 having produced nothing: I passed `--base`
and `--seed`, while the script defines `--host` and `--start-seed`. That is the third job in
this project lost to an invented flag (previously a missing module, and a non-existent
`--pristine`).

Two guards added:

1. Every job script now verifies each flag against the driver's own `--help` before running,
   exiting 3 if any is absent.
2. A produced-nothing check exits 4 rather than reporting success — which immediately caught
   my own second error: the guard globbed `m*.extxyz` while the script writes
   `fa_ensemble_*.extxyz`, so the run had in fact succeeded (8/8 accepted) and the guard
   misfired. Both are fixed; the misfire is recorded because a guard that lies is worse than
   no guard.
3. Regression test [19] asserts the exact flag set each driver accepts, and that `--base`
   and `--seed` are *not* accepted — so a rename breaks the test rather than a job.

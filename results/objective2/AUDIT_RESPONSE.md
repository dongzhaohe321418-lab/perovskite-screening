# Audit response — all seven findings confirmed

**Every claim in the audit checks out against the data, including one arithmetic error I
made while evaluating the previous round. Nothing is rebutted. The paired pilot's GA arm is
retracted pending a rerun.**

---

## Critical — GA migrating-iodide index bug: CONFIRMED, exact list match

I reproduced the driver's sequence on all 18 members and compared the deleted hydrogen's
index against the migrating iodide's:

    affected: [0, 1, 5, 6, 8, 13, 16, 17]   (n = 8)
    audit:    [0, 1, 5, 6, 8, 13, 16, 17]   (n = 8)   -> exact match

The mechanism is exactly as described: `build_pair` records the migrating iodide as a bare
integer, the GA substitution then deletes an FA hydrogen, and every index above it shifts
down by one — so `fin.positions[mig] = vpos` displaces the wrong atom whenever the deleted H
sits below the migrating iodide. Sr is unaffected (a B-site swap deletes nothing).

**This is the same class of bug I fixed in `scripts/18` and failed to carry across to
`scripts/22`.** The earlier fix remapped indices explicitly; the new driver reintroduced the
raw-index assumption.

### The MLIP blow-up attribution is retracted

    blow-ups: [(m05, GA), (m16, GA), (m17, GA)]
    all GA:                     True
    all in the affected set:    True

All three are in the index-shifted set. I attributed them to MACE failing on
out-of-distribution geometry and wrote that into the report and the commit message. **Moving
the wrong atom is a sufficient explanation and must be excluded first.** The magnitude gate
that catches them is still correct and stays; the *cause* is now unattributed.

### Fix

Tracking by tag rather than by index. ASE tags survive deletion and insertion, so the atom
is resolved in the *doped* cell regardless of what was edited:

    MIG_TAG = 99                      # set in build_pair, before any substitution
    mig_d = migrating_index(doped)    # asserts exactly one tag, and that it is an iodide

Verified on all 8 affected members plus the 2 that were accidentally fine: the tag resolves
to the same physical atom in every case, where the naive index would have mis-targeted 8.

**The two surviving GA pairs (m03, m10) are not affected** — but n = 2 supported no
conclusion anyway, and with the other 8 arms invalid the GA arm as a whole is retracted.

## High — validity never required convergence: CONFIRMED

The gate was `ge["passed"] and gc["passed"]` — pure shape. Endpoint convergence, NEB
convergence, and the final NEB force were not required. Now enforced jointly:

    ep["all_converged"] = (both endpoints converged AND both endpoint fmax <= target
                           AND NEB converged AND final NEB fmax <= target)
    valid = shape_gates AND all_converged

`valid_shape_only` is retained as a separate field so the two are never conflated again.

## High — endpoint `fmax` used the component max: CONFIRMED

    recorded:  np.abs(forces).max()                 <- max over COMPONENTS
    ASE uses:  np.linalg.norm(forces, axis=1).max() <- max over per-atom VECTOR NORMS

For an isotropic force the norm is √3 larger. A force of (0.012, 0.012, 0.012) passes a
0.02 component test and fails the correct norm test. Fixed for both endpoints and the band.

## High — noise floor is from the wrong pool: CONFIRMED

σ = 73.3 meV comes from the old 8-member pool; the pilot runs on the new 18-member pool,
and the repository already documents that these are different distributions. Recomputed on
the new pool's own six valid undoped paths:

    mean 216.2 meV | sd 83.9 meV | range 223.3 meV   (audit: 216.2 / 83.9 / 223.3)

So on the correct baseline: Sr's paired 37.4 meV is clearly below host scatter; GA's
84.9 meV is indistinguishable from it.

### An arithmetic error of my own, caught here

Checking this claim I computed "n ≥ 8" for the unpaired design on the new pool. That is
wrong — it applies the *paired* formula. For an unpaired comparison the standard error of a
difference is s·√(2/n), giving n ≥ 2(2s/T)²:

    old pool sigma 73.3 -> 13   (my original figure; correct)
    new pool sigma 83.9 -> 16   (the audit's figure; correct)
    my "8" used (2s/T)^2 -- the paired formula -- and was wrong

Six undoped paths is still too few for a final noise model; these are planning numbers.

## High — paired-rate budget: CONFIRMED (already corrected)

Confirmed and fixed in the previous round: observed paired rates 2/18 (GA) and 4/18 (Sr),
giving 90 and 45 hosts for 10 pairs, not ~30. **But those rates were measured with the GA
index bug live and without a convergence requirement**, so the GA figure in particular must
be re-measured after the rerun rather than trusted.

## Medium — stale repository state: CONFIRMED

- `checks.py` docstring still described the superseded "below every interior image"
  criterion — **fixed**, and it now states why that criterion was wrong.
- `scripts/22` default `--pool`/`--vac-ref` point at two structure files that exist in my
  workspace only because a shell step copied them; **they were never committed**, so a
  fresh clone fails on the default command. Now committed.
- `STATUS.md`, `PROGRESS.md`, and the `ACCEPTANCE_GATE.md` attempt log are behind.

---

## What this changes in the conclusions

| claim | status |
|---|---|
| Sr paired ΔE_a = −9.8 meV, s = 37.4 meV, not resolvable | stands (Sr unaffected by the bug) |
| Pairing reduces variance for Sr | stands, and strengthens against the correct σ = 83.9 |
| GA paired ΔE_a = +25.8 meV, s = 84.9 meV | **retracted** — 8 of 18 arms invalid |
| "GA scatter may be a large cation blocking the channel" | **retracted** — untestable on this data |
| Three MLIP blow-ups from out-of-distribution geometry | **retracted** — all in index-shifted arms |
| GA needs 90 hosts, Sr 45 | Sr stands; GA must be re-measured |
| Validity yield 33% | must be re-measured under the convergence requirement |

## Execution order (adopted from the audit)

1. **P0, local CPU** — done in this pass: tag-based migrating-atom tracking, convergence
   required for validity, force norms, docstring, committed structure files, and 14 new
   test assertions covering the index bug, the force metric, Student-t, and paired rates
   (39 total, all passing). Remaining: refresh `STATUS.md` and `PROGRESS.md`.
2. **P1, GPU 2-6 h** — rerun all 54 paths on the same 18 members. Not just the 8 broken GA
   arms: no path in the existing set recorded a true endpoint `fmax`, so none can be
   audited against the new criterion.
3. **P2** — read the rerun's endpoint diagnostics. Endpoints at the step cap means the
   relaxation budget is the problem; converged endpoints with lower adjacent interior
   images means genuine multi-basin behaviour, and then a single barrier number is mixing
   mechanisms and the iodide hop must be separated from hop-plus-FA-reorientation.
4. **P3, HPC 8-12 h** — `projwfc.x`, spin density and IPR on q0C/q0D; then a calibrated
   DFT+U benchmark **run together with a spatial seed** (a uniform U penalises the two Pb
   sites identically and cannot by itself break the Pb139/Pb70 degeneracy, which is the
   original failure mode). Accept only if forces reproduce to <0.01 eV/Å from two different
   starting densities.
5. **P4** — full CI-NEB only after that. If no affordable treatment gives reliable forces,
   stop and report "q=0 static energies only; charge-state barrier not obtainable" rather
   than compute a barrier from forces known to be unreliable.

> # SUPERSEDED — archived 2026-07-28
>
> Benchmark ladder plan; executed, rungs recorded, question closed.
>
> **Current authority: `results/objective1/dft/charge_relaxed/Q0_RESOLVED.md`.** This file is retained verbatim below for provenance; do not cite it as current.

# q=0 static benchmark — plan, acceptance criteria, and HPC budget

**Purpose.** Find a treatment that gives the q=0 state **reliable atomic forces**, not just
a stable energy. Forces are the binding constraint: the current state's energy is stable to
0.24 meV, but an unconverged SCF gives forces that cannot drive an endpoint relaxation or a
NEB. Until that is fixed, no DFT migration barrier can be reported for q=0.

**Instrument.** Each candidate is tested with a *single static SCF* on the q=0 initial
endpoint (~1.7 h on 2 nodes). That is 1/40th of a CI-NEB, so the whole ladder can be
screened for less than one production path.

## What is already excluded

| ruled out | why |
|---|---|
| more mixing/`beta` tuning at the current level | three attempts, three plateaus at 1.6-5×10⁻³ Ry |
| spatial spin seeding | done — resolved the *site* question (Pb 139 ≡ Pb 70 to 0.04 meV), did not converge |
| **HSE06** | **~25× cost. One CI-NEB ≈ 71 days; both charge states ≈ 142 days. Out on wall-clock alone.** |

## The ladder, cheapest first

| # | treatment | rel. cost | 1 SCF | changes theory level? |
|---|---|---|---|---|
| 1 | `degauss` 0.005 → 0.001 Ry, smearing | 1.0× | 1.7 h | no (same functional; numerics only) |
| 2 | fixed occupations + `diagonalization='cg'` | 1.0× | 1.7 h | no |
| 3 | DFT+U on Pb 6p, calibrated not guessed | 1.15× | 2.0 h | **yes** |
| 4 | cDFT, constrained charge on the Pb pair | 1.3× | 2.2 h | **yes** |

Rungs 1-2 are tried first *because they change nothing*: if either works, the q=+1 leg
already computed at PBE+D3(BJ) remains valid and only the q=0 leg is new. Rungs 3-4 force a
full recomputation of both legs.

Rationale for rung 1: the gap state sits **0.230 eV** below the conduction edge, and
`degauss` = 0.005 Ry = 0.068 eV is roughly a third of that — wide enough to put fractional
charge in both spin channels. At 0.001 Ry = 0.0136 eV the separation is ~17× the smearing
width, which should make the half-filled solution inaccessible to the smearing.

Rationale for rung 2: `davidson` is the current diagonaliser and it re-orders
near-degenerate states between iterations; `cg` is slower per step but more stable on a
near-degenerate manifold — a plausible cause of a residual that plateaus while the energy
does not move.

## Acceptance criteria — force reliability, not energy stability

A rung **passes** only if all four hold:

1. **SCF converges** to `conv_thr` = 10⁻⁸ Ry, i.e. the residual *descends* rather than
   plateauing. This is the criterion every attempt so far has failed.
2. **Forces are reproducible**: the same geometry re-run from a different starting density
   (e.g. from the q=+1 density vs from atomic superposition) gives a max force difference
   below **0.01 eV/Å** — one fifth of the 0.05 eV/Å NEB tolerance. An SCF that converges to
   different forces depending on where it started is not usable.
3. **The gap state is still there and localised**: `projwfc.x` shows the defect level with
   its weight on the two Pb dangling bonds. A "fix" that converges by delocalising the
   electron has changed the physics, not solved the problem.
4. **The moment is physical**: total magnetisation 1.00 μ_B, and |m| relative drift below
   2% over the last 5 iterations (the automated check in `scripts/checks.py`).

Criterion 2 is the one that matters most and has never been tested — every previous attempt
failed criterion 1 first, so force reliability was never reached.

## HPC budget

| stage | cost |
|---|---|
| rungs 1-2 (both, in one job) | ~3.5 h |
| rung 3 or 4, if needed | ~2.2 h |
| force-reproducibility re-run for whichever rung passes | ~2 h |
| **static benchmark total** | **~8 h** |
| then: q=0 + q=+1 endpoint relaxations at the winning level | ~14 h |
| then: 2 × CI-NEB at the winning level | **~136 h (5.7 days)** |

The static benchmark is ~6% of the campaign it gates. Running it first is the whole point:
committing 5.7 days of CI-NEB to an unvalidated treatment is the expensive mistake.

**If every rung fails**, the honest outcome is to report q=0 as *static-energy only* and the
DFT barrier as unavailable at any level this cluster can reach — not to run a NEB on
unreliable forces.

## Theory-level bookkeeping

Whichever rung wins, its fingerprint is recorded via `theory_fingerprint()` in
`scripts/checks.py`, and `check_comparable()` will refuse any comparison against a leg
computed at a different level. If rung 3 or 4 wins, **the q=+1 explore path already computed
becomes a starting geometry only — its energies are not reusable.**


---

# Benchmark results (2026-07-27)

## Rung 1 — `degauss` 0.005 → 0.001 Ry: **FAILED**, and informatively so

Stopped at 31 iterations.

| | |
|---|---|
| accuracy | plateaued ~4.6×10⁻³ Ry, then **oscillated** (3.0×10⁻³ → 7.2×10⁻³) |
| total magnetisation | 0.94 (free under smearing; physical value 1.00) |
| absolute magnetisation | **rose** 1.20 → 2.68, worse than any fixed-occupation run |
| automated check | FAIL — 57.2% relative drift over the last 5 iterations |

The hypothesis was that `degauss` = 0.068 eV is roughly a third of the 0.230 eV gap-state
separation, wide enough to put fractional charge in both spin channels. At 0.0136 eV that
separation is ~17× the smearing width and the half-filled solution should be inaccessible.
It still did not converge, and |m| drifted further from the physical value than before.

**This rules out smearing width as the cause.** The obstacle is not how the occupations are
broadened — it is the near-degenerate manifold itself. That is a genuine negative result,
not merely a failed run.

## Rung 2 — `cg` diagonalisation: **NOT VIABLE ON COST**

Stopped at 3 iterations, before any numerical verdict.

    measured:  1155 s per SCF iteration (19.3 min)
    davidson:  ~150 s per iteration     (2.5 min)
    -> cg is 8x slower per iteration on this system

| target | wall time |
|---|---|
| 40 iterations (where davidson plateaued) | 12.8 h |
| 150 iterations (the cap) | **48 h** |
| one CI-NEB (~40 SCF-equivalents) | **~80 days** |
| both charge states | **~160 days** |

A static SCF was budgeted at 1.7-2.2 h. One rung at 48 h is 24× that, for a ladder whose
entire justification was being cheap relative to the campaign it gates. And the cost
compounds into the production run: cg hits the *same wall-clock wall that already excluded
HSE06*. **Even if it converged, it could not be used** — so there is no value in paying 48 h
to find out.

Recorded as *not viable on cost*, which is a different verdict from rung 1's *tested and
failed*. If a future machine makes cg affordable, the hypothesis it tests — that davidson's
re-ordering of near-degenerate states is what stalls the residual — remains untested and
plausible.

## Where this leaves the ladder

Both no-theory-change rungs are now closed. Every remaining option (DFT+U, cDFT, hybrid)
**changes the theory level and therefore forces the q=+1 leg to be recomputed identically**,
per criterion 3. The cheap escape route is exhausted.

The honest position: the q=0 state supports **static energies only**. Its forces are not
reliable, so no DFT migration barrier can be reported for q=0 — and consequently no
charge-state comparison — until a theory-level change is made and *both* legs are rerun.

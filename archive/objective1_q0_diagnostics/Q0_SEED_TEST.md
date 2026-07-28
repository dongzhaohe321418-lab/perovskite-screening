> # SUPERSEDED — archived 2026-07-28
>
> Seeded polaron test interim note; final bounded analysis lives in Q0_POLARON_EXCLUDED.md.
>
> **Current authority: `results/objective1/dft/charge_relaxed/Q0_POLARON_EXCLUDED.md`.** This file is retained verbatim below for provenance; do not cite it as current.

# q=0 spin localisation — spatial-seed test (criterion 2)

## The methodological finding that unblocked this

`q0C` plateaued at an "estimated scf accuracy" of 1.57×10⁻³ Ry (21.4 meV) and never
converged. But the **total energy over its last six iterations spans 5.3×10⁻⁵ Ry = 0.72
meV** — thirty times tighter than QE's own accuracy estimate.

That gap is diagnostic, not cosmetic. QE's accuracy estimate is a bound derived from the
*density* residual. In a system with a near-degenerate spin manifold the density keeps
reshuffling among near-degenerate states, so the residual stays large while the **total
energy of the manifold is essentially fixed**. The practical energy uncertainty is
sub-meV, not 21 meV.

**Consequence:** a plateaued run still yields an energy usable at the 59.5 meV
significance scale. The seed-ordering comparison is therefore viable even though neither
run formally converges. This is what makes criterion 2's fourth bullet answerable rather
than blocked.

The caveat that limits it: an unconverged SCF gives unreliable **forces**, which matters
far more for a NEB than for a single-point energy. So this licenses reading the *ordering*
of two static states — it does not license running a barrier on them.

## What the spatial seed achieved

| | q0B (no seed) | q0C (Pb 139 seed) |
|---|---|---|
| residual floor | 3.4×10⁻³ Ry (46 meV) | **1.56×10⁻³ Ry (21 meV)** |
| iterations to floor | ~100 | **~40** |
| absolute moment | 1.70, settled | **1.51, locked to 2 dp** |
| total energy | not captured | **−9247.624645 Ry** |
| energy stability | — | **0.72 meV over 6 iters** |

The seed improves the residual floor 2.2×, reaches it in a third of the iterations, and
locks the moment tighter. Crucially, q0B and q0C settle at **different** absolute moments
(1.70 vs 1.51) — the near-degenerate solutions *are* distinguishable once a site is chosen.
That is the substantive signal: the problem is site selection, not an inability to form a
localised state at all.

## Criterion 2 scoring for q0C

- **PASS** total moment pinned at 1.00
- **PASS** absolute magnetisation not drifting (1.51, locked)
- **PASS** spin density on a definite site — the seed selected one and it held
- **FAIL** SCF residual descending to `conv_thr` — flat for 20+ iterations

Three of four. The fourth bullet requires the two-seed comparison, which `q0D` (Pb 70)
provides.

## Consistency note, not a result

q0A (`nspin=1`, converged) gives −9247.62661774 Ry against q0C's −9247.624645 Ry, i.e. the
spin-polarised state is **26.8 meV higher**. That would be the wrong sign for a variational
comparison if the two described the same system — but they do not: `nspin=1` forces
fractional occupation of a single orbital, which is not a physical state for an
odd-electron system. No variational ordering is implied and none is claimed.

## Method note

The seed is a **species relabel only**: `Pb1` carries the identical
`Pb.pbe-dn-rrkjus_psl.1.0.0.UPF` (verified in the output: `Pb1 14.00 207.20000`), applied
to exactly one atom, with `starting_magnetization(Pb1) = 0.6`. The Hamiltonian is unchanged
— this is the escalation step that precedes Hubbard U, per the acceptance gate.


---

## Criterion 2, fourth bullet — ANSWERED

Both spatial seeds were run to their plateau and compared.

| | q0C (seed Pb 139) | q0D (seed Pb 70) |
|---|---|---|
| total energy | −9247.624645 Ry | −9247.624642 Ry |
| energy stability | ±0.24 meV | ±0.93 meV |
| absolute moment | 1.51 | 1.58 |
| residual floor | 1.56×10⁻³ Ry | 1.65×10⁻³ Ry |

**Energy difference: +0.04 meV**, against a combined energy noise of 0.96 meV and a
significance threshold of 59.5 meV.

**The two seeds converge to the same state**, not to two orderable metastable states. The
moments agree to 0.07 μ_B and the residual floors coincide. So criterion 2's fourth bullet
is satisfied in its *first* form — there is no site-selection ambiguity to order. This is
consistent with the geometry: Pb 139 and Pb 70 flank the vacancy at 3.45 and 3.51 Å, i.e.
they are near-equivalent by the symmetry of the vacancy environment, so seeding either one
reaches the same physical solution.

That reframes what remains. The barrier to a converged q=0 state is **not** a choice
between competing localisation sites — that question is now closed. It is that the density
mixer cannot close the residual on a manifold whose *total energy is already stationary to
sub-meV*. The two facts together — energy stable to 0.24 meV while the residual sits at
1.6×10⁻³ Ry — say the remaining error lives in a part of the density that barely couples to
the energy.

### Consolidated criterion-2 scoring

- **PASS** total moment pinned at 1.00 (all fixed-occupation runs)
- **PASS** absolute magnetisation not drifting (1.51 / 1.58, locked)
- **PASS** spin density on a definite site, reproducibly
- **PASS** the two seeds agree — same ground state, to 0.04 meV
- **FAIL** SCF residual descending to `conv_thr` — plateaus at ~1.6×10⁻³ Ry

Four of five. The single remaining failure is formal SCF convergence, and its practical
consequence is bounded: for a **static energy** the uncertainty is sub-meV and usable, but
**forces from an unconverged SCF are unreliable**, and a NEB needs forces. So this state
supports single-point energetics and does *not* yet support a migration barrier.

### What this means for the escalation path

The acceptance gate's fallback order put spatial seeding before Hubbard U / hybrids / cDFT,
precisely to avoid a theory-level change if a cheaper fix sufficed. Spatial seeding has now
been tried and has resolved the *site* question without changing the Hamiltonian — but it
did not deliver convergence. The next escalation step is therefore live, and it carries the
consequence the gate already flagged: **any of Hubbard U, hybrid functionals, or cDFT
changes the theory level, so the q=+1 leg must be recomputed identically.**

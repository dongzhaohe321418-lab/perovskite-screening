# Stage-2 acceptance gate — four criteria

> **⚠️ SUPERSEDED ESCALATION ADVICE (2026-07-27).** Any recommendation below to apply a
> Hubbard U is HISTORICAL and must not drive an HPC decision. The spin-free projection
> (`Q0_PROJECTION_RESULT.md`) shows the q=0 half-occupied state is **delocalised** —
> IPR 0.0261 ≈ 38 effective atoms of 159, with the two vacancy-flanking Pb carrying only
> 2.66% and 2.44% — so a U would *impose* a localisation the physics does not support and
> yield an artefact. The convergence ladder (`Q0_CONVERGENCE_LADDER.md`) further shows the
> result is robust to `nbnd` and the Davidson subspace. **The agreed next HPC step is a
> LARGER-SUPERCELL spin-free q=0 SCF + projection**, to decide whether the delocalisation
> is intrinsic or an artefact of periodic images in the 159-atom cell. Until the q=0 state
> and its forces are established: no U, no q=0 relaxation or NEB on q=0 forces, and the
> q=0/q=+1 DFT barrier comparison stays closed.

Set by the PI before the q=0 results land, to keep *numerical* convergence from being
read as a *settled physical solution*. Binding on how every result below is interpreted.

## 1. Numerical convergence is not localisation

`q0A` (eigenvalues / occupations) can only establish **whether an isolated gap state
exists**. It cannot show that the state is spatially localised.

Required additionally: `projwfc.x` site-projected weights (or band-decomposed charge
density) on **Pb 139, Pb 70 and their neighbours**, plus an inverse participation ratio
(IPR) for the defect state. A gap state with delocalised projection is not a localised
polaron and must not be reported as one.

`projwfc.x` is chained after every converged SCF in the campaign job for exactly this.

## 2. Fixed spin count is not fixed spatial localisation

`occupations='fixed'` with `tot_magnetization=1.0` pins n_up − n_down = 1. It says nothing
about *where* the moment sits. Acceptance therefore requires all four:

- SCF residual genuinely stable (monotone descent to `conv_thr`, not a random walk);
- absolute magnetisation no longer drifting between iterations;
- spin density settling on the **same physical site** across iterations;
- seeding from **Pb 139** and from **Pb 70** independently gives either the **same ground
  state**, or **two metastable states that can be energy-ordered**.

Implemented as variants `q0C` (seed Pb 139) and `q0D` (seed Pb 70). The seed is a species
**relabel only** — `Pb1` carries the identical `Pb.pbe-dn-rrkjus_psl.1.0.0.UPF`, so the
Hamiltonian is unchanged; verified one atom relabelled per input.

## 3. Fixed occupations changes the protocol — q=+1 must be recomputed

If the accepted q=0 solution uses `occupations='fixed'`, that is **no longer the
Gaussian-smearing protocol the q=+1 leg was computed under** — `degauss` is inoperative
under fixed occupations.

Then: the **saved geometries and the preserved relaxed path may be reused**, but q=+1
**energies, forces and CI-NEB must be recomputed under the fixed-occupation protocol**.
Anything less breaks the strict-identity requirement that makes the charge-state
comparison admissible at all.

## 4. Two converged CI-NEBs do not equal VALIDATED

On completion the anchor is first marked **`TESTED`**, never directly VALIDATED.

- Upgrade to **`VALIDATED`** only if the barrier *ordering* and *target magnitude* of
  Tyagi et al. are reproduced.
- Otherwise record **`NOT REPRODUCED`** and analyse the differences in theory level,
  structure, and defect definition.

**Order-of-magnitude threshold.** Approximating a 10× rate ratio by the barrier difference
alone, at 300 K and assuming equal prefactors:

    |ΔE_a| ≥ k_B T ln 10 = 59.5 meV  (0.0595 eV)

A separation below this does not support an order-of-magnitude mobility claim even if the
ordering is correct. The equal-prefactor assumption is itself an approximation: a genuine
mobility ordering also requires the hop attempt frequency, which is not computed here.

## Fallback order if q0B/C/D fail

Do **not** jump to Hubbard U. Escalate in this order:

1. **Spatial seeding via species relabel** (identical Pb pseudopotential, different
   species label on Pb 139 / Pb 70). Hamiltonian unchanged. — *running as q0C / q0D*
2. If that fails, compare **constrained DFT**, **hybrid functionals**, and a
   **justified, calibrated U** — and note that each changes the theory level, so **both
   charge states must be recomputed in full** under whichever is adopted.

## Cost accounting

Recorded per job as `node count × elapsed × rate`, with job IDs, retaining **both billing
interpretations** (wall-hour and node-hour). Recorded for the record only — it does not
gate scientific decisions.


---

## Attempt log — q=0 spin localisation

| attempt | setting | total moment | absolute moment | SCF residual | verdict |
|---|---|---|---|---|---|
| 1 | `mixing_beta=0.2`, smearing | collapsed | — | stuck ~5×10⁻³ Ry, 57+ iters | charge sloshing |
| 2 | `beta=0.1`, local-TF, Pb seed 0.05 | **0.87 → 0** | — | stuck ~5×10⁻³ | spin-state collapse |
| 3 | `tot_magnetization=1.0`, smearing | **1.00 held** | wandered 1.5-2.6 | flat 4-7×10⁻³, 30 iters | moment pinned, distribution not |
| A | `nspin=1` **probe** | n/a (no spin) | n/a | **converged, 6.1×10⁻⁷ Ry, 27 iters** | isolated half-occupied gap state |
| B | `occupations='fixed'`, no spatial seed | **1.00 held** | **settled 1.70 ± 0.01** | flat 3.4×10⁻³, 116 iters | **distribution stabilised, SCF still open** |
| C | fixed occ + seed **Pb 139** | running | | | |
| D | fixed occ + seed **Pb 70** | running | | | |

### What attempt B established

Against criterion 2's four requirements: total moment pinned (pass); absolute magnetisation
no longer drifting — settled at 1.70 ± 0.01 after early swings of 2.50-5.52 (**pass, and the
first attempt to achieve this**); SCF residual genuinely stable (**fail** — flat at
3.4×10⁻³ Ry, ~3400× above `conv_thr`, through 116 iterations).

*Caveat on "settled".* |m| was 1.83-1.90 at iteration 47 and 1.69-1.71 at iteration 116 — a
further 0.16 μ_B (9%) of drift. Calling it settled at iteration 47 would have been
premature; the 1.70 ± 0.01 figure is the value at **116** iterations, and only the late-run
plateau supports the "not drifting" verdict. Any |m| quoted from a mid-run snapshot of this
system should be treated as provisional.

So fixed occupations did what it was chosen to do: it removed the fractional-occupation
freedom that let the two spin channels equalise, and the spin *density* stopped wandering.
But the SCF still cannot close. A stationary distribution with a stuck residual is the
signature of two nearly degenerate solutions the density mixer keeps trading between at the
10⁻³ level — which is why attempt B was stopped at 116 rather than run to its 200-step cap:
the remaining iterations could only confirm the plateau.

Attempts C and D are the discriminating test. If the Pb 139-seeded and Pb 70-seeded runs
reach **distinguishable total energies**, the near-degeneracy is resolved and criterion 2's
fourth bullet is satisfiable (two metastable states, energy-ordered). If they reach the same
energy, the ground state is genuinely degenerate between the two sites and the escalation
path in the acceptance gate applies.

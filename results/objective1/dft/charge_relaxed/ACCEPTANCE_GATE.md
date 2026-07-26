# Stage-2 acceptance gate — four criteria

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

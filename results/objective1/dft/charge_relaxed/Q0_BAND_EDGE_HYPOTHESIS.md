# q=0 state — the "gap state" is very likely the conduction band minimum

**A free re-analysis of the existing projection (no new compute) indicates the
half-occupied state is not a defect level at all, but the CBM. If confirmed, V_I⁰ is a
shallow donor, the escalation ladder is misdirected, and the SCF problem has a physical
rather than numerical explanation.**

## Five independent indicators, all from the already-harvested projection

| observable | value | what it implies |
|---|---|---|
| Pb-sublattice uniformity | 31.9 of 32 effective Pb; per-Pb weight 2.69–3.51% (max/min 1.3) | the state covers the *entire* Pb 6p sublattice near-uniformly |
| the two vacancy-flanking Pb | rank **30th and 32nd of 32** by weight | the *least* weight — the opposite of a dangling-bond polaron |
| vs the conduction states above | 701: 31.9 eff. Pb; 702–706: 7.9–20.1 eff. Pb | 701 is *more* delocalised than states above it — the nodeless band-edge form |
| energy above the I-p valence top | 1.632 eV | matches PBE-without-SOC CsPbI₃ (~1.5–1.8 eV); the 0.23 eV to 702 is Γ-point spacing in a finite cell |
| spatial extent | R_g = 10.43 Å vs L_min/2 = 8.81 Å; **66.8%** of weight beyond L_min/2 | two-thirds of the state sits on atoms closer to a periodic image than to the defect |

The last line is decisive for interpretation: this cell **cannot represent** a state of this
extent, whether or not the extent is physical.

## Consequence if confirmed

V_I⁰ is a **shallow donor** — the extra electron occupies the delocalised conduction band
edge with no in-gap level. That explains the SCF pathology exactly: one electron shared
among near-degenerate conduction states which reshuffle between iterations, which is why
mixing, seeding, and fixed occupations all struck the same wall while total energy stayed
stable to sub-meV. It also **removes the premise of the localisation escalation** — there is
no localised state for a Hubbard U to correct, and applying one would manufacture the
localisation it was meant to test.

## Two tests dispatched (job `32d8fd27`)

- **P1 — pristine 160-atom cell.** Vacancy filled (verified: every Pb 6-coordinate, 1408
  electrons = closed shell), spin-free, identical theory level. If its CBM shows the same
  near-uniform Pb-p character, band 701 in the defective cell *is* the CBM.
- **P2 — unconstrained spin.** `nspin=2` on the defective cell with the moment free
  (smearing, no `tot_magnetization`), restarting from q0A's converged density. Every prior
  spin attempt either forced a moment or started cold. If the moment relaxes to ≈0 from a
  good starting density, delocalisation is confirmed rather than a failure to localise.

## Caveat, stated up front

Both tests — and the projection itself — are at the **q=+1 relaxed geometry**. A small
polaron requires lattice relaxation around the localised charge, which has never been
possible here because q=0 forces are unusable. So the finding is: *delocalised at this
geometry*. Whether q=0 lattice relaxation would localise it is **untested**, and the shallow-
donor conclusion is conditional on that.

## Effect on the planned larger-supercell test

The supercell test remains the right next step, but its purpose sharpens: if P1 confirms the
CBM assignment, the supercell is no longer asking "is the delocalisation intrinsic or an
image artefact" — a band edge is delocalised by definition. It would instead ask whether a
*separate*, genuinely localised defect level exists that the 159-atom cell is too small to
resolve. That is a different and more precise question, and worth settling before spending
the larger-cell budget.

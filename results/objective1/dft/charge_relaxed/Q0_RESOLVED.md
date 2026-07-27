# q=0 RESOLVED — the state is the conduction band minimum, and the SCF was never broken

**Both discriminators returned unambiguous answers. The q=0 "spin-SCF convergence problem"
that consumed six attempts was not a numerical pathology: the calculation was being asked
to find a magnetic solution that does not exist at this geometry.**

Job `dd88d5d3`. Claim scope, stated first: **at the q=+1 relaxed geometry, under spin-free
and unconstrained-spin PBE+D3**, the extra electron occupies the delocalised conduction
band minimum, not a vacancy-localised polaron. Lattice relaxation around a localised charge
remains untested — see the caveat at the end.

## P1 — pristine cell: the state IS the CBM

A 160-atom pristine cell (vacancy filled, every Pb 6-coordinate, 1408 electrons = closed
shell), same theory level, spin-free. Three comparisons, as specified:

| | defective cell, band 701 | pristine cell, CBM (band 705) |
|---|---|---|
| energy | 4.3259 eV | **4.3188 eV** |
| gap above valence top | 1.632 eV | **1.556 eV** |
| Pb-p character | 90.8% | **91.4%** |
| effective atoms | 38.3 | **35.6** |

**Per-atom weight overlap on the 159 shared atoms: cosine = 0.9757.** The control matters
here — the pristine CBM against its own neighbouring conduction states gives 0.788 (CBM+1)
and 0.741 (CBM+3). The defect-cell state matches the pristine CBM far better than the
pristine CBM matches states one band away. It is the *same* state, not merely a similarly
uniform one. Uniformity alone would have been weak evidence; the overlap is what settles it.

The added iodide carries **0.00%** of the pristine CBM weight — the vacancy site is
irrelevant to this state, exactly as expected for a band edge.

## P2 — unconstrained spin: the magnetic solution does not exist

`nspin=2` with the moment completely free (smearing, no `tot_magnetization`), restarting
from q0A's converged density:

    total magnetization:    -0.00  0.00  0.00  0.00  0.00  0.00
    absolute magnetization:  0.00  0.00  0.00  0.00  0.00  0.00
    CONVERGED in 6 iterations

Set against every earlier attempt:

| attempt | constraint | iterations | outcome |
|---|---|---|---|
| q0A `nspin=1` | none (no spin freedom) | 27 | converged |
| q0B fixed occ | `tot_mag = 1.0` | 200+ | never converged, residual flat ~3.4×10⁻³ |
| q0C Pb139 seed | `tot_mag = 1.0` | 65+ | never converged, floor 1.6×10⁻³ |
| q0D Pb70 seed | `tot_mag = 1.0` | 42+ | never converged, same floor |
| rung 1 | none, `degauss` 0.001 | 150 | never converged, \|m\| drifting |
| **P2** | **none, moment free** | **6** | **converged, m = 0.00** |

Every attempt that *forced* a moment failed. The one that let the moment go free converged
immediately to zero.

**Energetics confirm the direction:** the forced-magnetic plateau (q0C, −9247.624645 Ry)
sits **24.3 meV above** the converged non-magnetic solution. A converged magnetic solution
could only be lower than its own plateau, and it plateaued above the non-magnetic ground
state, so m = 1 is not the ground state here.

## A retraction I owe

Early in this campaign, when an unconstrained run collapsed to m ≈ 0, I called it "an
unphysical state QE is chasing", reasoning that 1401 electrons (odd) forbid a zero total
moment. **That reasoning was wrong.** Under smearing, fractional occupation of both spin
channels is legitimate, and for an electron entering a delocalised band-edge state it is
the correct answer. The collapse I diagnosed as a failure was the physics giving me the
answer; I then spent four attempts overriding it with `tot_magnetization = 1`. The
convergence "problem" was self-inflicted from that point on.

## What this settles, and what it does not

**Settled.** There is no in-gap defect level at this geometry, so there is nothing for a
Hubbard U to correct — DFT+U is not merely deprioritised, its premise is absent. The
escalation ladder built on "how do we make q=0 localise" was aimed at a state that is not
there. The spin-free q0A result is a *converged, correct* description, not a fallback.

**Not settled.** Everything above is at the **q=+1 relaxed geometry**. A small polaron
forms by lattice distortion around a localised charge; that distortion has never been
computed here because q=0 forces were never trusted. But the reason they were not trusted
was the convergence failure — which is now explained and removed. **q=0 forces from the
converged non-magnetic solution are usable**, so a q=0 geometry relaxation is now possible
and is the natural next step: relax q=0 from the q=+1 geometry and re-project. If the state
stays delocalised, "shallow donor" is earned; if it localises, a polaron exists and the
barrier problem changes shape.

## Consequences for the barrier programme

The q=0/q=+1 comparison is no longer blocked by an unresolved electronic-structure problem.
It is blocked only by not having run the q=0 relaxation and NEB — which is now a matter of
compute, not of method. **This does not license reporting a charge-state ordering**: both
legs must still be relaxed and run at the identical theory level, and the Tyagi-ordering ban
stands until they are.

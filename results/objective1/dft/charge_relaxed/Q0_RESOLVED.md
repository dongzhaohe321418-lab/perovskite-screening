> **Q3 PROVENANCE STATUS — CLOSED / CITABLE (2026-08-03, see
> `results/objective1/dft/charge_relaxed/Q3_CLOSURE_RECORD.md`).** The demotion's lifting
> condition is met: the controller's verified-closed records cover F-006 (CYCLE-000005) and
> F-012/F-013 (CYCLE-000006), and cycles 000010/000011/000016 independently re-ran
> `results/objective1/dft/charge_relaxed/q3_raw/derive_q3.py` in isolated clones, reproducing
> every quoted value (custody, 160→159 mapping, cosine + controls, IPRs, both alignments).
> The banner below this one is the HISTORICAL demotion-era text, retained per the
> preserve-history rule; its "restored only when…" wording described the pre-closure state
> (superseded — audit CYCLE-000019 F-019).

> **[HISTORICAL demotion-era banner — superseded by the CLOSED/CITABLE banner above] Q3 PROVENANCE STATUS (2026-07-31, audit CYCLE-000002 F-006/F-008, CYCLE-000004 F-008):**
> `RESULTS_INDEX.md` names this file as a Q3 authority and marks Q3 **UNVERIFIED / NOT CITABLE**.
> The raw records are committed at `results/objective1/dft/charge_relaxed/q3_raw/`, and
> `results/objective1/dft/charge_relaxed/q3_raw/derive_q3.py` recomputes every value quoted
> here — including the 159-shared-atom cosine, its controls, the IPRs and both valid alignment
> references — from those raws plus a mapping rebuilt from the raw site lists (exit 0 at this
> commit). **[superseded — historical] Citability is restored only when an audit cycle independently re-verifies this**;
> until then every number below is provisionally recomputable, not independently verified.
> *(That condition is now met — see the CLOSED/CITABLE banner at the top of this file.)*

# q=0 RESOLVED — the state is CBM-like, and the SCF was never broken

> **WORDING CORRECTED (see `P1_REFERENCE_AUDIT.md`).** This document originally titled the
> result "the state IS the conduction band minimum" and cited a 7 meV energy agreement
> (pristine 4.3188 vs defective 4.3259 eV). That comparison used raw eigenvalues from two
> separate periodic calculations, which share no common energy zero — it was not valid.
> Re-anchored: VBM-referenced the difference is +75.8 meV, semicore-aligned +52.1 meV
> (one declared convention — defective minus aligned pristine, semicore = mean of the
> lowest 32 bands — implemented and asserted in
> `results/objective1/dft/charge_relaxed/q3_raw/derive_q3.py`; the earlier +75.9 was a
> 0.1 meV rounding artifact, audit CYCLE-000005 F-012). All
> references place the state at the conduction band edge, so the identification stands, but
> at ~50–80 meV resolution rather than 7 meV. The claim is therefore **CBM-like /
> consistent with the pristine CBM**, not identity. The per-atom overlap (cosine 0.9757 vs
> controls 0.788/0.741) and Pb-p character (90.8% vs 91.4%) are unaffected and remain the
> strongest evidence. A new check strengthens the picture: the 229 meV gap above the state
> is the pristine supercell's OWN Γ-point band-edge spacing (311 meV), mildly perturbed —
> so nothing is split off from the conduction manifold and there is no donor level to
> interpret.

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

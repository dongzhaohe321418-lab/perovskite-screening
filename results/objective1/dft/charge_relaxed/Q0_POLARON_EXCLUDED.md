# Polaron test — NO polaron. V_I⁰ is a shallow donor at this level of theory.

**The last open question on the q=0 charge state is closed. A deliberately strong seed —
0.20 Å cage contraction plus a spin moment on the two Pb flanking the vacancy — does not
produce a bound polaron. Decomposing the energy shows why, and shows the conclusion does not
depend on the amplitude chosen.**

## The three calculations

| | geometry | spin | E (Ry) | status |
|---|---|---|---|---|
| **deloc** | undisturbed (= q=+1 relaxed) | non-magnetic | −9247.62643363 | converged, 0 BFGS steps |
| **ELAS** | +0.20 Å contraction | non-magnetic (nspin=1) | −9247.61815625 | converged, 39 iterations |
| **POL** | +0.20 Å contraction | seeded, `starting_magnetization = 0.5` | −9247.61832 | plateau, moment decaying |

`ELAS` uses a byte-identical geometry to `POL` (verified) with the magnetism removed, so the
comparison isolates the two contributions.

## Decomposition

    elastic cost      E(ELAS) − E(deloc)  =  +112.6 meV     (the distortion alone)
    total             E(POL)  − E(deloc)  =  +110.4 meV     (distortion + spin)
    localisation gain = elastic − total   =    +2.2 meV

**The spin polarisation recovers 2% of the elastic cost.** A polaron requires the gain to
*exceed* the cost — it falls short by 110 meV.

## The conclusion is not an artefact of choosing 0.20 Å

Fitting the two terms: k = 112.6/0.20² = **2815 meV/Å²** for the lattice stiffness, and —
under the assumption most favourable to a polaron, that the gain is *linear* in the
displacement (Jahn–Teller-like) — g = 2.2/0.20 = **11.0 meV/Å**. Then E(u) = ku² − gu is
negative only for

    u < g/k = 0.0039 Å,   with a well depth of g²/4k = 0.011 meV.

A binding energy of ~0.01 meV is not a polaron; it is below numerical noise and three orders
of magnitude below room-temperature kT (25.7 meV). The electron–lattice coupling is simply
far too weak relative to the lattice stiffness for **any** amplitude to bind a carrier.

## Three independent signatures agree

1. **Moment decay.** The seeded |m| fell monotonically 1.25 → 0.80 → 0.58 over 129
   iterations. A polaron would consolidate its moment; this one dissolves.
2. **Energy.** POL sat ~110 meV above the delocalised state and did not descend across 90
   iterations, with a residual (~30 meV) far too small to close the gap.
3. **Zero-step relaxation.** From the undistorted geometry, BFGS took **no step at all** —
   the q=0 state exerts no force on the lattice at explore tolerance, with the moment pinned
   at 0.00.

## Where this leaves the q=0 charge state

**V_I⁰ is a shallow donor**: the extra electron occupies the delocalised conduction band
minimum (established separately by the pristine-cell comparison, per-atom weight overlap
cosine 0.976), and no lattice distortion binds it. The label is now *earned* rather than
conditional — the caveat that had been attached to it (an untested lattice-relaxed polaron)
has been tested and excluded.

Consequences:

- **DFT+U remains inappropriate**, now for two independent reasons: there is no in-gap state
  to correct, and no localised solution for it to stabilise.
- **q=0 forces are usable** — the non-magnetic solution converges (6 iterations from a
  matched density) and the relaxation is well-behaved.
- **The q=0 NEB is now a matter of compute, not method.**

## Limits, stated

- Level of theory is **PBE+D3(BJ), Γ-point, 159-atom cell**. Polaron binding is famously
  sensitive to self-interaction error; a hybrid functional could in principle bind what PBE
  does not. That is a theory-level question, and per the standing rule it would require
  re-running *both* charge states identically.
- The seed probed one distortion mode (symmetric contraction of the two flanking Pb). An
  asymmetric or larger-shell mode was not tested, though the 2815 meV/Å² stiffness against
  11 meV/Å coupling makes any mode an unlikely candidate.
- `q0_final` plateaued without converging, so only the *initial* endpoint has a relaxed q=0
  geometry. The NEB needs both.

**This does not license a charge-state ordering.** Both legs must still be relaxed and run at
identical theory level; the ban on claiming the literature ordering stands.

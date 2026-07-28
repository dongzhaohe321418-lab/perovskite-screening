# Polaron test — no thermally significant polaron. V_I⁰ behaves as a shallow donor.

**A deliberately strong seed — 0.20 Å cage contraction plus a spin moment on the two Pb
flanking the vacancy — does not produce a bound polaron: the seeded state sits ~110 meV
*above* the delocalised solution, and that sign is secure (the gap is ~4× the run's own
residual). Decomposing the energy separates a solid, converged elastic cost from a
localisation gain that is *not* resolved, so the amplitude question is answered as a
BOUND rather than settled: even granting twice the SCF residual as coupling, the deepest
possible well is ~8 meV, well under room-temperature kT. A weakly bound state of a few meV
is not excluded by these data — it would be thermally irrelevant either way.**

## The three calculations

| | geometry | spin | E (Ry) | status |
|---|---|---|---|---|
| **deloc** | undisturbed (= q=+1 relaxed) | non-magnetic | −9247.62643363 | converged, 0 BFGS steps |
| **ELAS** | +0.20 Å contraction | non-magnetic (nspin=1) | −9247.61815625 | converged, 39 iterations |
| **POL** | +0.20 Å contraction | seeded, `starting_magnetization = 0.5` | −9247.61832 | plateau, moment decaying |

`ELAS` uses a byte-identical geometry to `POL` (verified) with the magnetism removed, so the
comparison isolates the two contributions.

## Decomposition

    elastic cost      E(ELAS) - E(deloc)  =  +112.6 meV     (the distortion alone)
    total             E(POL)  - E(deloc)  =  +110 meV       (distortion + spin)
    localisation gain = elastic - total    =  a few meV, NOT RESOLVED

**The elastic cost is solid** — both `ELAS` and `deloc` are converged runs. **The
localisation gain is not.** `POL` never converged (129 iterations, residual ~30 meV), and its
energy drifted between sampling windows: the gain reads 7.3 meV from iteration ~83 and
2.3 meV from iteration ~129, a 5 meV swing on a quantity whose own run carries a ~30 meV
residual. The gain is therefore **bounded, not measured**: |gain| ≲ 30 meV.

An earlier version of this report quoted the gain as "+2.2 meV" and derived g = 11.0 meV/Å,
u_crit = 0.0039 Å and a well depth of 0.011 meV from it. Those figures were quoted to a
precision the input does not support and are **retracted**; the bound-based analysis below
replaces them.

**What the numbers do support:** POL sits ~110 meV *above* the delocalised state at
u = 0.20 Å. That gap is ~4× the residual, so its sign is secure — **the seeded distorted
state is not the ground state.** The spin polarisation recovers at most a small fraction of
the 112.6 meV elastic cost, and cannot repay it.

## Is the conclusion sensitive to the 0.20 Å amplitude? — bounded, not excluded

The elastic constant comes from converged runs: k = 112.6/0.20² = **2815 meV/Å²**. For the
coupling, rather than quote an unresolved point value, take the *entire* SCF residual as
localisation gain — the most generous reading possible:

| assumed gain at u = 0.20 Å | g (meV/Å) | u_crit = g/k (Å) | well depth g²/4k (meV) |
|---|---|---|---|
| 30 meV (full residual) | 150 | 0.053 | **2.0** |
| 60 meV (2× residual, deliberately extreme) | 299 | 0.106 | **8.0** |

Even granting twice the residual as coupling, the deepest possible well is **~8 meV — under
one-third of room-temperature kT (25.7 meV)**, and the realistic case (full residual) gives
~2 meV. So a *strongly* bound small polaron is excluded, while a *weakly* bound state of a
few meV cannot be ruled out from these data — it would be thermally irrelevant at operating
temperature either way.

This is weaker than the claim the earlier draft made ("no bound polaron at any amplitude").
The honest version: **no thermally significant polaron**, with the bound set by POL's
convergence rather than by physics. Converging POL to 10⁻⁶ Ry would tighten it, and is the
obvious follow-up if the question ever becomes load-bearing.

## Three independent signatures agree

1. **Moment decay.** The seeded |m| fell monotonically 1.25 → 0.80 → 0.58 over 129
   iterations. A polaron would consolidate its moment; this one dissolves. (This signature
   is qualitative and does not depend on the unresolved energy difference.)
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
  asymmetric or larger-shell mode was not tested.
- **`POL` was never converged.** Its plateau energy bounds the localisation gain rather than
  measuring it, which is why the amplitude analysis above reports an upper bound on the well
  depth instead of a value. This is the weakest link in the argument and the one worth
  closing first if the polaron question becomes load-bearing.
- `q0_final` plateaued without converging, so only the *initial* endpoint has a relaxed q=0
  geometry. The NEB needs both.

**This does not license a charge-state ordering.** Both legs must still be relaxed and run at
identical theory level; the ban on claiming the literature ordering stands.

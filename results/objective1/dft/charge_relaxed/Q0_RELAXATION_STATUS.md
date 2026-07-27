# q=0 geometry relaxation — status

**One endpoint answered, one plateaued, and the decisive polaron test is queued. The
headline: at the initial endpoint, adding the electron produces NO lattice relaxation at
all — but that alone cannot exclude a polaron, and the test that can is running.**

## q0_initial — converged in ZERO BFGS steps

    Energy error   = 7.0E-05 Ry   (criterion 1.0E-04)  PASS
    Gradient error = 1.7E-03 Ry/Bohr (criterion 1.9E-03) PASS
    bfgs converged in 1 scf cycle and 0 bfgs steps
    total magnetization = 0.00 throughout

The q=+1 relaxed geometry is **already a q=0 stationary point** at explore tolerance
(0.044 vs 0.050 eV/Å). The relaxed structure is byte-identical to the input — the lattice
does not move.

Saved: `q0/q0_initial_relaxed.extxyz`, E = −9247.62643363 Ry.

## q0_final — plateaued, energy usable, forces not

138 iterations; the residual flattened at ~1.4×10⁻³ Ry. Over the last 8 iterations the
total energy spread is **4.05 meV (std 1.23 meV)** while the reported accuracy reads
19.3 meV — the same residual-vs-energy discrepancy seen in the earlier seeded runs, about
16× pessimistic. (An earlier draft of this note said "well under a meV"; that overstated it
and is corrected here.)

Plateau energy −9247.62720989 Ry, giving an endpoint asymmetry of **−10.6 meV** (final below
initial) against **+11.9 meV** for the q=+1 pair. This is an *indication*, not a result: it
compares a plateau against a converged value, and the q0_final geometry is unrelaxed. It is
also a within-charge-state comparison and therefore says nothing about charge-state ordering,
which remains closed.

## What zero BFGS steps does NOT prove

Stated plainly because it would be easy to overclaim here:

1. **Tolerance.** A polaron binding of tens of meV can be driven by forces below the
   0.05 eV/Å explore threshold. Zero steps at that tolerance cannot see it.
2. **Basin.** BFGS is a *local* optimiser started from an undistorted, non-magnetic state.
   A small polaron is typically a **separate local minimum** reached only by seeding a
   distortion — a local optimiser will never find it from here. This is the standard failure
   mode of polaron studies.

So the honest statement is: the q=+1 geometry is a q=0 stationary point with no moment,
which is *consistent with* a delocalised shallow donor and *inconsistent with* a polaron
that would form spontaneously from this starting point — but it does not exclude a polaron
in a distinct basin.

## The decisive test (job `652b5174`, queued)

The polaron equivalent of the endpoint return test: seed **both** ingredients and see where
it goes.

- The two Pb flanking the vacancy (indices 139, 70 at 3.446 and 3.511 Å) pulled **0.20 Å
  toward the vacancy** — a cage contraction far larger than the residual force could produce
  spontaneously.
- Those two atoms relabelled `Pb1` with `starting_magnetization = 0.5`. Verified: exactly
  2 atoms relabelled, Pb + Pb1 = 32, **identical pseudopotential** — the Hamiltonian is
  unchanged and this is a spin/geometry seed only.
- Relaxed at **production tolerance** (`forc_conv_thr = 7.8e-4`, fmax 0.02 eV/Å), tighter
  than the explore tier that gave zero steps.

**Returns to the undistorted m = 0 geometry** → no polaron basin exists from a strong seed,
and "shallow donor" is earned at this level of theory.
**Falls into a distinct distorted magnetic minimum** → a polaron exists, the delocalised
result was an artefact of the starting point, and the barrier programme changes shape.

Both outcomes are results. Neither licenses a charge-state ordering.

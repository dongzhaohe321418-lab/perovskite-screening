> # SUPERSEDED — archived 2026-07-28
>
> Numerical convergence ladder; closed (delocalisation numerically robust).
>
> **Current authority: `results/objective1/dft/charge_relaxed/Q0_RESOLVED.md`.** This file is retained verbatim below for provenance; do not cite it as current.

# q=0 numerical-convergence ladder — CLOSED: delocalisation is numerically robust

**Three rungs varying `nbnd` and the Davidson subspace separately all reproduce the
baseline defect state exactly. Per the pre-agreed stop rule (two consecutive rungs with
small change), the ladder is closed: the ~38-effective-atom delocalised state is a
numerically robust conclusion, not an artefact of band truncation or diagonaliser
subspace.**

## Protocol (fixed before running, per the agreed criteria)

- State identified by **wavefunction character** — fractional occupation, else max Pb-p
  weight near E_F — and matched across rungs by **cosine similarity of the per-atom weight
  vector**. Band index is never used for identification (it renumbers when `nbnd` changes;
  here the state happened to stay at 701 because added bands land above it).
- `nbnd` and `diago_david_ndim` varied **separately**, one knob per rung, everything else
  byte-identical to the converged `q0A` reference.
- Recorded per rung: state energy, occupation, Pb-p weight, IPR, weights on Pb139/Pb70.

## Results

| rung | knob | iters | E_tot (Ry) | E_state (eV) | occ | Pb-p | IPR | eff. atoms | Pb139 | Pb70 | cosine vs baseline |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | nbnd 841 (default), ndim 4 | 27 | −9247.62661774 | 4.3259 | 0.5000 | 0.9075 | 0.02608 | 38.3 | 0.0266 | 0.0244 | — |
| N1 | nbnd 900 | 28 | −9247.62661797 | 4.3258 | 0.5000 | 0.9075 | 0.02608 | 38.3 | 0.0266 | 0.0244 | **1.0000** |
| N2 | nbnd 960 | 23 | −9247.62661761 | 4.3260 | 0.5000 | 0.9075 | 0.02608 | 38.3 | 0.0266 | 0.0244 | **1.0000** |
| D1 | diago_david_ndim 8 | 23 | −9247.62661778 | 4.3258 | 0.5000 | 0.9075 | 0.02608 | 38.3 | 0.0266 | 0.0244 | **1.0000** |

Total energies agree to 4×10⁻⁷ Ry across independently converged SCFs; the state's 68
projection coefficients are identical to QE's print precision in all four runs.

**Audited before accepting:** identical metrics across runs is exactly what a
read-the-wrong-file bug would produce. Checked: the three projwfc outputs have distinct
checksums, distinct band counts (841/900/960 blocks), and independently converged SCF
energies differing in the 9th decimal. The identity is genuine — the projection is
converged beyond print precision. **Resolution floor:** coefficient changes below ~0.0005
(QE prints 3 decimals) are invisible; differences smaller than that cannot be excluded.

## Interpretation, per the pre-agreed decision tree

- *"If the result is insensitive to both knobs and the ~38-atom state persists →
  delocalisation is numerically robust."* **This branch.** Band truncation is ruled out
  (N1, N2); diagonaliser subspace is ruled out (D1).
- The remaining open question is **periodic-image coupling**: a 38-atom state in a
  159-atom cell overlaps its own images, and no fixed-cell treatment can distinguish
  intrinsic delocalisation from image-mediated delocalisation. Per the tree: **a larger
  supercell is the next escalation, ahead of hybrid** — hybrid in the current cell cannot
  exclude image coupling and would spend ~weeks to produce an uninterpretable answer.

## One rung failed once, and the diagnosis method matters

D1's first submission died on a namelist error: my rung builder inserted
`diago_david_ndim` into `&SYSTEM`; it belongs in `&ELECTRONS`. Established by test-parsing
on the cluster (a &SYSTEM insertion is rejected, an &ELECTRONS insertion parses through to
a missing-pseudopotential error — far past the namelist stage). Notably, `strings pw.x`
returned nothing for these keys — the second time the strings method has been misleading on
this build. Test-parsing is the reliable discriminator.

## Consequences

1. **The q=0 SCF failure is now fully characterised**: a delocalised Pb-6p
   conduction-manifold state (projection), robust to numerical parameters (this ladder),
   whose near-degenerate reshuffling stalls the spin-polarised residual (attempt history).
2. **No further fixed-cell, PBE-level knob is expected to change the picture.** The cheap
   options are genuinely exhausted now — smearing width, mixing, seeds, fixed occupations,
   band count, Davidson subspace.
3. **Decision for the user**: the next rung is a supercell-size test (e.g. 2× the current
   cell, one static q=0 SCF + projection: does IPR scale with cell size?). That is a
   theory-level-preserving test but a significant memory/wall-clock step on this cluster.

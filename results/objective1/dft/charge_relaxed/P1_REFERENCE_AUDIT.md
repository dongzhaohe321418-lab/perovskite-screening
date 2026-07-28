# P1 audit — energy reference, and why the wording becomes "CBM-like"

**Audit requested by the guide: check that pristine and vacancy cells share theory
parameters, cell parameters and geometry reference; check the energy reference, Pb-p
distribution and per-atom weight overlap; and write the conclusion as "CBM-like" or
"consistent with the pristine CBM" unless all three metrics support the stronger claim.**

The audit changes one number materially and softens the headline. All three metrics do
support the identification — but the energy metric is good to ~76 meV, not the ~7 meV the
raw eigenvalues appeared to show.

## Check 1 — same theory, same cell

| | pristine (P1) | defective (q0A) |
|---|---|---|
| atoms | 160 | 159 |
| cell volume (Å³) | 54529.4666 | 54529.4666 |
| ecutwfc / ecutrho (Ry) | 50 / 400 | 50 / 400 |
| degauss (Ry) | 0.0050 | 0.0050 |
| valence electrons | 1408 | 1401 |

Identical cell, identical cutoffs and smearing; the 7-electron difference is exactly the
removed iodide's valence. **Passes.**

## Check 2 — the energy reference was NOT valid as first reported

Absolute Kohn–Sham eigenvalues from two separate periodic calculations share no common zero:
the average electrostatic potential is fixed by each cell's own G = 0 convention, which
differs when the composition differs. The originally reported agreement — pristine CBM
4.3188 eV vs defective state 4.3259 eV, a 7 meV match — **compared raw eigenvalues across
cells and was therefore not a valid comparison.**

Re-done against two defensible internal references:

| reference | pristine CBM | defective state | difference |
|---|---|---|---|
| raw eigenvalue (**invalid**) | 4.3188 | 4.3259 | +7.1 meV |
| VBM-referenced | +1.5560 above VBM | +1.6319 above VBM | **+75.9 meV** |
| semicore-aligned (mean of lowest 32 bands, −45 meV shift) | 4.2738 | 4.3259 | **+52.1 meV** |

All defensible references agree the state sits at the conduction band edge and place it
slightly *above* the aligned pristine CBM, but they spread over ~70 meV. **The energy metric
supports "at the conduction band edge"; it does not establish "identical to the CBM" at the
tens-of-meV level.**

## Check 3 — is the state split off from the conduction manifold?

This is the discriminator between a band state and a shallow donor *level*. The state sits
229 meV below the next state in the defective cell, which looks like an isolated level — but
the pristine cell shows the same structure:

    pristine  conduction eigenvalues: 4.3188  4.6297  4.6344  4.6423  4.6460  4.6636
              spacings (meV):            311      5       8       4      18
    defective conduction eigenvalues: 4.3259  4.5554  4.6338  4.6659  4.6768  4.6820
              spacings (meV):            229     78      32      11       5

The pristine Γ-point CBM is **already isolated by 311 meV** from a dense manifold above it.
The defective cell's 229 meV is that same intrinsic supercell band-edge spacing, mildly
perturbed (−82 meV) by the defect. **Nothing has been pulled out of the conduction band** —
there is no defect-induced splitting to interpret as a donor level.

## Check 4 — orbital character and spatial overlap (unchanged)

- Pb-p weight: **91.4%** (pristine CBM) vs **90.8%** (defective state).
- Per-atom weight vector cosine similarity: **0.9757**, against controls of 0.788 (pristine
  CBM vs CBM+1) and 0.741 (vs CBM+3) — the match far exceeds the pristine edge's own
  similarity to its neighbours.
- Effective atom count: 35.6 (pristine) vs 38.3 (defective).

**Passes, and this is the strongest of the three metrics.**

## Verdict and the wording that follows

All three metric families support the identification, so the guide's condition for a positive
statement is met — but the *energy* metric's resolution is ~76 meV, so the claim must be
stated at that resolution:

> The half-occupied state in the V_I⁰ cell is **CBM-like**: spatially and in orbital
> character it is essentially the pristine conduction band minimum (per-atom cosine 0.976,
> Pb-p 90.8% vs 91.4%), and its energy is consistent with the pristine CBM to within ~50–80
> meV depending on the alignment reference. It is **not** a deep in-gap defect level, and it
> is **not** split off from the conduction manifold — the 229 meV gap above it is the
> pristine supercell's own band-edge spacing (311 meV), mildly perturbed.

**Retracted:** the earlier title "the state is the conduction band minimum" and the 7 meV
energy agreement. The first overstates the precision the energy comparison supports; the
second was computed across cells without a common reference.

**Unaffected:** every downstream conclusion. The shallow-donor description rests on the
spatial overlap and the polaron bound, not on the eigenvalue agreement; DFT+U remains
inappropriate because there is no in-gap state (confirmed here — the state is at the band
edge, not in the gap); and the q=0 forces remain usable.

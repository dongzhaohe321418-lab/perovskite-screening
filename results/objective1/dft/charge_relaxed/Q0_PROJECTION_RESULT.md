# Criterion 1 — orbital projection of the q=0 defect state

**Result: the state is Pb-6p in character but SPATIALLY DELOCALISED over ~38 effective
atoms. It is not a polaron. This overturns the working hypothesis and removes the
justification for Hubbard U as the next escalation step.**

Source: `projwfc.x` on the converged spin-free probe `q0A` (QE 7.5, 64 ranks / 2 nodes,
`JOB DONE`, no errors, 828 atomic states, 841 bands, full Löwdin analysis).

## First, a correction to the band index

Earlier reports called the defect state **band 700**. Re-parsing `q0A.out` strictly — the
eigenvalue list terminated at `occupation numbers`, the occupation list at
`the Fermi energy is`, giving 841 aligned pairs — shows it is **band 701**:

| band | E (eV) | occupation |
|---|---|---|
| 700 | 2.6940 | 1.0000 |
| **701** | **4.3259** | **0.5000** ← E_F |
| 702 | 4.5554 | 0.0000 |

The energies 4.3259 / 2.6940 / 4.5554 quoted previously were right; the *labels* were off by
one, so 2.6940 eV was described as the valence edge when it is band 700. All five bands in
the window match `projwfc.x` to 0.0000 eV, confirming the indexing.

## The result

*(Cell: 159 atoms, Cs32 Pb32 I95 — the γ-CsPbI₃ V_I supercell. An earlier version of this
report used 232, which is the atom count of the FA-host supercell used for Objective 2, a
different system. Every reference number below is recomputed for 159; the delocalisation
conclusion is unaffected.)*

    band 701, E = 4.3259 eV = E_F, occupation 0.5000, |psi|^2 = 0.971

| quantity | value |
|---|---|
| orbital character | **Pb-p 90.8%**, I-s 9.2% |
| IPR | **0.0261** |
| effective atoms (1/IPR) | **38.3** |
| atoms contributing at all | 64 of **159** |
| weight on Pb139 | 2.66% |
| weight on Pb70 | 2.44% |
| largest single atom | 3.19% (Pb #110, not adjacent to the vacancy) |

Reference points for **this 159-atom cell** (Cs32 Pb32 I95, `number of atoms/cell = 159`
in `q0A.out`; `projwfc.x` resolves exactly 159 distinct atoms): a state spread evenly over
all 159 atoms gives IPR = **0.0063**; a two-atom polaron gives 0.5. At 0.0261 the state is
only ~4x more concentrated than uniform, and ~19x less concentrated than a polaron. The
38.3 effective atoms are **24% of the cell**.

## What this means

**The orbital character is as expected — the escalation ladder aimed at the right
manifold.** Pb-6p dominates at 90.8%, which is what the Hubbard-U proposal assumed.

**But the spatial conclusion is the opposite of what was assumed.** The two Pb atoms
flanking the vacancy carry **2.66% and 2.44%** of the state — no more than a dozen other Pb
atoms across the cell, and *less* than the largest contributor, which is not adjacent to the
vacancy at all. The extra electron is not sitting on the vacancy's dangling bonds. It is
spread across the Pb-6p conduction manifold.

This resolves the question the seeds could not. q0C and q0D agreed to 0.04 meV, and I noted
that energy agreement does not prove a shared wavefunction. The projection explains why they
agree: **there is no site to choose between.** Seeding Pb139 or Pb70 makes no lasting
difference because the state was never localised on either.

## Consequence for the escalation ladder

**Hubbard U is now poorly motivated.** U is an on-site penalty that drives occupations toward
integers on individual atoms. Applied to a state genuinely spread over ~38 atoms it does not
correct a self-interaction error in a localised orbital — it *imposes* a localisation the
underlying physics does not support. It would likely converge, and the result would be an
artefact of the correction.

The earlier requirement that any U run be paired with a spatial seed is therefore moot:
the problem was never that U could not break the Pb139/Pb70 degeneracy. There is no
degeneracy to break.

**Revised reading of the SCF failure.** A residual that plateaus while the total energy is
stable to 0.7 meV, with a delocalised half-occupied state at E_F, is the signature of a
near-degenerate *manifold* of conduction states being reshuffled between iterations — not of
a bistable localised defect. That is consistent with every observation: the smearing-width
rung failed because the problem is not occupation broadening; the spatial seeds agreed
because there is no site to select; the moment stabilised under fixed occupations while the
residual did not, because fixing the count does not stop states trading within a manifold.

**What this does NOT establish.** `q0A` is the spin-free probe. This is the spin-restricted
orbital character; the spin-density distribution requires a converged spin-polarised
calculation, which does not exist — q0C/q0D plateaued and QE writes no save directory
without convergence. A spin-polarised solution could in principle localise where the
restricted one does not, though nothing observed so far suggests it.

## Recommended next step, replacing DFT+U

Given a delocalised conduction-manifold state, the promising treatments are those that fix
the *manifold*, not an on-site orbital:

1. **More empty bands plus a tighter Davidson subspace.** If near-degenerate conduction
   states are being reshuffled, giving the diagonaliser more room to resolve them addresses
   the actual mechanism. Cheap, and changes no theory level, so the existing q=+1 leg stays
   valid — the only remaining option with that property.
2. **A larger supercell.** A state spread over 38 atoms in a 159-atom cell is interacting
   with its periodic images. This may be a finite-size artefact, in which case no
   correction at fixed cell size will fix it.
3. **Hybrid functional** — correct for the self-interaction that delocalises such states,
   but already excluded on wall-clock (~142 days for both legs).

Hubbard U drops from first choice to not recommended on this evidence.

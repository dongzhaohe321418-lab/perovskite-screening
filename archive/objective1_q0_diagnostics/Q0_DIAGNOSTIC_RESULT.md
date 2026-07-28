> # SUPERSEDED — archived 2026-07-28
>
> Interim diagnostic; superseded by the full resolution.
>
> **Current authority: `results/objective1/dft/charge_relaxed/Q0_RESOLVED.md`.** This file is retained verbatim below for provenance; do not cite it as current.

# q=0 spin state — diagnostic result (criterion 1, part 1)

**Status: the electronic origin of the q=0 SCF failure is now identified.** The remaining
question is spatial localisation, which needs `projwfc.x` and is not yet answered.


> **Correction (2026-07-27): the band index and the localisation claim.**
>
> The table below labels the states 699/700/701. Re-parsing `q0A.out` strictly (eigenvalue
> list terminated at `occupation numbers`, occupations at `the Fermi energy is`, giving 841
> aligned pairs) shows the half-occupied state is **band 701**, not 700. The energies
> (4.3259 / 2.6940 / 4.5554 eV) are right; the labels were off by one, so 2.6940 eV is
> band 700, not the valence edge. All five bands in the window match `projwfc.x` to
> 0.0000 eV.
>
> More importantly, `projwfc.x` has now run (see `Q0_PROJECTION_RESULT.md`): the state is
> **Pb-p 90.8% but spatially DELOCALISED**, IPR = 0.0261 ≈ 38 effective atoms, with only
> 2.66% and 2.44% on the two Pb flanking the vacancy. **It is not a polaron**, and the
> phrase "one unpaired electron forced to share a single spatial orbital" below should not
> be read as implying localisation — the 0.5000 occupation is an artefact of the spin-free
> probe (an odd electron count forces half occupancy there).


## What was run

`q0A`: the same V_I⁰ cell at the locked Stage-2 theory level (PBE+D3(BJ), ecut 50/400,
Γ, degauss 0.005), but with `nspin = 1`. Removing all spin freedom removes the failure
mode entirely, so the SCF converges and prints the eigenvalue spectrum. This is a **probe
of the band structure, not a physical solution** — an odd-electron system cannot be
described without spin polarisation.

It converged cleanly: **27 iterations, monotone descent to 6.1×10⁻⁷ Ry**, in sharp
contrast to the three spin-polarised attempts, which random-walked at 4-7×10⁻³ Ry.

## Result: an isolated, half-occupied gap state

| band | energy (eV) | occupation |
|---|---|---|
| 699 | 2.6940 | 1.0000 |
| **700** | **4.3259** | **0.5000** ← E_F |
| 701 | 4.5554 | 0.0000 |

- Isolated from the valence edge by **1.632 eV**
- Isolated from the conduction edge by **0.230 eV**
- Host gap VBM→CBM = **1.861 eV**; the defect level sits **88% of the way up the gap**

The **occupation of exactly 0.5000** is the signature of one unpaired electron forced to
share a single spatial orbital between two spin channels — precisely what `nspin=1`
imposes. In a correct spin-polarised treatment this state splits by exchange into one
occupied spin-up and one empty spin-down level.

## What this settles, and what it does not

**Settled.** The extra electron of V_I⁰ forms a genuine, well-isolated **gap state**. It is
*not* spilling into the conduction manifold. This confirms the fixed-occupations /
Hubbard-U family of fixes is aimed at the right problem: the failure is the *occupation*
of a localised defect level, not a band-alignment pathology.

It also explains why Gaussian smearing failed. With a defect level sitting 0.23 eV below
the conduction edge and `degauss = 0.005 Ry ≈ 0.068 eV`, the smearing function can place
fractional charge in *both* spin channels of that state at negligible cost — which is
exactly the collapse observed (moment 0.87 → 0). Fixed occupations removes that freedom.

**Not settled — and this is criterion 1.** An isolated gap state can still be spatially
*delocalised*. The eigenvalue spectrum cannot distinguish a polaron localised on the Pb
dangling bonds from a state spread over many Pb. That requires site-projected weights
(`projwfc.x`) on Pb 139, Pb 70 and their neighbours, plus an IPR.

`projwfc.x` did **not** run: the campaign used `disk_io = 'low'`, which withholds the
wavefunction data `projwfc.x` needs, and the post-processing step then failed and took the
job's exit code with it (exit 1, after `q0A` itself had exited 0). Fixed by setting
`disk_io = 'medium'` and making the projection step non-fatal, so one failed post-step
cannot discard a converged SCF.

## Next

`q0B` (fixed occupations, no spatial seed), `q0C` (seed on Pb 139), `q0D` (seed on Pb 70)
are running with the fix. Per criterion 2, agreement — or orderable metastability —
between the Pb 139 and Pb 70 seeds is the real test, not convergence of any single one.

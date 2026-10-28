# WP2e — DFT relaxation of a MACE endpoint (m30 GA image 0) (2026-10-28)

**Outcome (PLAN amendments k and l item 3): WP2e is uninformative in its pre-registered form.**

- **What was run.** One of the seven pre-registered relaxations was run: m30 GA, image 0.
- **What it showed.** It lowered F by 977 meV. That energy is spread over the whole cell in
  proportion to the number of atoms: 81% sits beyond 6 Å of both defects. It is not a
  defect-local relaxation.
- **Consequences.** ΔE_relax(dopant) − ΔE_relax(undoped) (amendment c item 5) would mostly measure
  far-field wandering, so the six held relaxations are not run in that form. Criterion 5's error
  bar therefore does not exist. Every DFT single-point statement in WP2b and WP2c keeps its "fixed
  MACE geometry" qualification, and `WP2B_RESULT.md` §3 stays provisional.

## Relaxation

- **Setup.** Fixed-cell BFGS from the MACE band frame (`band_GA_m30.extxyz`, image 0). R point,
  forc_conv_thr 7.8 × 10⁻⁴ Ry/bohr (0.02 eV/Å), otherwise `scripts/30`. Input and output:
  `wp2e/relax_m30_GA_img0.{in,out}.gz`.
- **Convergence.** BFGS converged in 283 SCF cycles and 282 BFGS steps (QE's own count; final max force 0.017 eV/Å, RMS
  0.005 eV/Å; start 0.369 / 0.149 eV/Å).
- **Energy.** E_relax = F(relaxed) − F(start) = **−977.3 meV** (σ→0 estimate −977.4 meV).
  −325 meV came in the first 10 steps and −652 meV over the remaining 272, with a final slope of
  −0.19 meV per step.

## Where the energy and the displacement are (`scripts/38`, `wp2e/wp2e_displacement_m30_GA_img0.json`)

Distances are measured to the nearer of the two defect centres (vacancy site, GA carbon).

| shell (Å) | atoms* | path work W (meV) | W per atom (meV) | of which organic | mean \|Δr\| (Å)** | max \|Δr\| (Å)** |
|---|---|---|---|---|---|---|
| 0–4 | 12 | −36.9 | −3.1 | −31.2 | 0.28 | 0.80 |
| 4–6 | 38 | −152.2 | −4.0 | −88.7 | 0.36 | 1.24 |
| 6–8 | 84 | −357.6 | −4.3 | −306.6 | 0.38 | 1.23 |
| 8–10 | 80 | −326.1 | −4.1 | −262.3 | 0.39 | 1.33 |
| > 10 | 20 | −103.4 | −5.2 | −77.1 | 0.39 | 0.98 |
| **total** | 234 | −976.2 | −4.2 | −765.9 | | |

\* Organic atoms are assigned to the shell of their molecule's C, so the work columns count whole
molecules. \*\* Displacement columns use each atom's own distance (13 / 42 / 72 / 80 / 27 atoms)
and remove the net translation.

- **Path work.** W_i = −Σ_k ½(F_i^k + F_i^(k+1))·Δr_i^k along the actual BFGS path (trapezoid
  rule; post hoc, amendment l item 3). It sums to E_relax within 1.2 meV and has no boundary term.
  The attribution is path-dependent and assigns each interaction to the atoms on which its force
  acts.
- **Near against far.** Within 6 Å of a defect: 50 of 234 atoms (21%), 19% of the energy
  (−189 meV). Beyond 6 Å: 184 atoms, 81% (−787 meV). Even the fast first 10 steps are 74% far
  field.
- **Displacement is flat with distance.** Mean |Δr| does not decay with distance. 78% of Σ|Δr|²
  lies beyond 6 Å.
- **Rotations.** 12 of the 19 C-centred molecules (18 FA and the GA) rotate their C→N axis by more
  than 10°; 10 of those 12 lie beyond 6 Å (max 42.9° at 6.6 Å).
- **Organic sublattice.** It carries 78% of the work with 66% of the atoms. The relaxation is a
  cell-wide reorientation and repacking of the FA sublattice, the DFT counterpart of the
  reference descents seen with MACE (0.2–0.6 eV between fmax 0.02 and 0.005,
  `WP1_PILOT_RESULT.md`).

## The partition single points (not used)

- **What was run.** `scripts/38` also wrote two partition structures: atoms within 6 Å of a
  defect at their relaxed positions with the rest at MACE positions (near_only), and the reverse
  (far_only).
- **Result.** F − F(start) = **+5280 and +4544 meV**, with forces up to 9.5 eV/Å.
- **Why they are meaningless.** A cut by atom splits FA molecules whose atoms fall on different
  sides of 6 Å (N–H stretched from 1.02 to 1.48 Å, C–H from 1.09 to 1.27 Å). The energies measure
  the torn bonds. This is a design error of the partition, recorded in amendment l item 3 and in
  the docstring of `scripts/38`. Raw files: `wp2e/raw/part_*`.

## What follows

- **The held relaxations are not run in the pre-registered form:** undoped and Sr image 0, and
  the m30 Sr-hinge E_b quartet (`*.in.hold` on the node).
- **Proposed post hoc design, WP2e′ (amendment l item 4; not run).** Relaxations with every atom
  beyond 6 Å of both defects fixed at the MACE geometry. The free region is identical within each
  comparison. It ranks below the WP3 DFT single points.
- **The same landscape problem appears at both levels.** Here it is on the DFT side, in WP1 on
  the MACE side (basin hops). A protocol that freezes the far field is needed whichever potential
  is used (`SCREENING_ROADMAP.md`, consequence 2 of the 2026-10-27 update).

Figure: `figures/fig_wp2e_relaxation.*`.

# Minimal viable pipeline: iodine-vacancy migration in CsPbI₃ (MACE-MP-0 CI-NEB)

This is the "Stage 1" minimal pipeline from the dopant-screening roadmap: the
**undoped V_I single hop** in cubic CsPbI₃, computed zero-shot with the
MACE-MP-0 foundation potential and CI-NEB. It establishes the baseline Eₐ that
all future ΔEₐ (dopant) numbers are measured against, and it validates that the
whole toolchain (structure → endpoints → CI-NEB → barrier) runs end to end.

## Method

| Step | Choice | Notes |
|------|--------|-------|
| Structure | Cubic CsPbI₃ (Pm-3̄m), a = 6.289 Å exp. | 2×2×2 supercell = **40 atoms** |
| Potential | MACE-MP-0 `medium`, zero-shot, float64 | no dispersion, CPU |
| Cell relax | FIRE + FrechetCellFilter, fmax 0.02 | MACE a = **6.397 Å** (+1.7 % vs exp.) |
| Defect | Neutral V_I, octahedral-edge hop | d(A→B) = 4.52 Å = a/√2 |
| Endpoints | positions-only relax, fixed cell | symmetric: ΔE_endpoint = 0.000 eV |
| Path | 7 images, IDPP interpolation | improved-tangent tangent |
| Saddle | **CI-NEB** (climbing image), FIRE fmax 0.03 eV/Å | converged 67 steps |

## Result

The MEP is a **symmetric double well**: the migrating iodine relaxes into a
shallow displaced (metastable) minimum at −0.31 eV before crossing the barrier.
Two defensible barrier definitions:

- **Eₐ = 0.46 eV** — saddle relative to the deepest point on the band (the
  metastable well). This is the physically meaningful hop barrier for the
  activated jump and the number to quote.
- Eₐ = 0.15 eV — saddle relative to the ideal-lattice endpoint. Lower because
  the endpoint is *not* the true kinetic starting basin here.

Both sit inside the experimental literature band for MAPbI₃/CsPbI₃ V_I
migration (~0.1–0.6 eV), so the zero-shot MACE-MP-0 baseline is sane.

## Important caveats (from the roadmap's own risk list)

1. **Zero-shot MLIP is initial-screen only.** MACE-MP-0 is trained on
   near-equilibrium configurations; the saddle is exactly where it extrapolates
   worst. This Eₐ must be DFT-checked (and, for screening, active-learning
   fine-tuned) before it is a conclusion — MAE target < 0.03–0.05 eV vs DFT.
2. **Neutral vacancy.** Real V_I is typically +1 charged (V_I⁺); a charged-cell
   calculation with FNV/Freysoldt correction can shift Eₐ by >0.1 eV. This
   neutral run is the methodological warm-up, not the production number.
3. **Finite size.** 40 atoms is the minimum; a 3×3×3 (135-atom) convergence
   check is needed to remove vacancy-image interaction (0.05–0.1 eV effect).

## Relation to the full dopant screen

This is the **Stage-1 baseline** (undoped V_I only). The full dopant ΔEₐ ranking,
pinning-radius curve, mechanism fingerprints, and finite-size + MD cross-check
that build on it live in `../dopant_screen/` (see
`../dopant_screen/REPORT_dopant_screen.md`). The reproducible driver here,
`neb_pipeline.py`, is the same one committed as `scripts/03_dopant_screen_pipeline.py`
(with the base-structure caveat added there). Both use **cubic** CsPbI₃ — not
directly comparable to the tilted γ-phase tracer bullet in `scripts/01_vacancy_neb.py`.

## Files

- `neb_mep.png` — minimum-energy-path plot
- `neb_pipeline.py` — reproducible end-to-end script
- `structures/CsPbI3_222_relaxed.cif` — MACE-relaxed perfect 2×2×2 supercell
- `structures/neb_initial.cif`, `structures/neb_final.cif` — relaxed hop endpoints
- `structures/neb_saddle.cif` — climbing-image saddle configuration
- `structures/neb_path.xyz` — full 7-image converged band

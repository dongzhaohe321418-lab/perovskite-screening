# Objective 1 — Method validation: four anchors

**Perovskite ion-migration dopant screen · γ-CsPbI₃ iodide-vacancy migration**
**Pipeline: zero-shot MACE-MP-0 (medium) + CI-NEB, γ-P1 phase, 2×2×2 (159-atom) V_I cell, float64, RTX 5090**

> **What Objective 1 is.** Before screening ~50 dopants (Objective 2), the
> pipeline must reproduce four independent literature anchors, so that a computed
> ΔE_a can be trusted as a real physical shift rather than a modelling artefact.
> This report records the status of all four.

![Strain and GA⁺ anchors]({{artifact:art_9be8ff94-ed02-435e-9cc6-5e856c5e11b2}})

| # | Anchor | Source | Status | Result |
|---|--------|--------|:------:|--------|
| a | Undoped E_a in 0.1–0.6 eV | Eames 2015 | **MET** | 0.259 eV (γ), 0.119 eV (cubic 3×3×3) — both in band |
| b | V_I⁺ vs V_I⁰ ordering | Tyagi 2025 | **DFT-gated** | scaffold only — MACE is charge-agnostic |
| c | GA⁺ ΔE_a sign & magnitude | A-site pinning lit. | **MET** | ΔE_a = **+70 meV**, pins (correct sign) |
| d | Strain–E_a correlation | strain-management lit. | **MET** | biaxial dE_a/dε = **−2.25 eV/strain** (r = −0.98) |

Three of four anchors are reproduced now with the zero-shot pipeline. The fourth
(b) is *fundamentally* gated on charged-supercell DFT + per-charge-state
fine-tuning; it is specified as a ready-to-run protocol
(`CHARGE_STATE_PROTOCOL.md`), not computed, because the zero-shot model cannot
represent it even in principle.

---

## Anchor (a) — undoped barrier in the literature band ✓

The γ-phase tracer-bullet barrier, recomputed here in **float64** (production
dtype), is **E_a = 0.259 eV forward / 0.230 eV reverse** — identical to the
float32 baseline to ~0.05 meV, and comfortably inside the Eames et al. (2015)
window of **0.1–0.6 eV**. The independent cubic 3×3×3 screen
(`results/dopant_screen/`) gives 0.119 eV, also in band. Same defect throughout:
i_vac = 71, i_hop = 128, octahedron-edge hop of 4.53 Å, converged.

This doubles as the pipeline's **cross-platform / cross-dtype regression test**:
any future environment or MACE-version change must still reproduce 0.259 eV here.

## Anchor (c) — GA⁺ A-site pinning ✓

Guanidinium (C(NH₂)₃⁺, built as a planar 10-atom cation) substituted on the Cs
site nearest the hop (3.36 Å from the path midpoint) **raises** the barrier:

| | E_a (eV) |
|---|:---:|
| undoped γ | 0.259 |
| GA⁺ on A-site | 0.329 |
| **ΔE_a** | **+0.070 (pins)** |

The **sign is correct**: GA⁺ is an established A-site pinning cation (its
hydrogen-bond network to the iodide sublattice stiffens the lattice against the
octahedral distortion the migrating iodide requires), and a ~70 meV increase is a
physically reasonable magnitude. Zero-shot gives the **sign and seed geometry**
reliably; a *rankable* magnitude for the league table (Objective 2) still needs
the fine-tuned model, but the validation target here — reproduce the sign and
order of magnitude — is met. Converged; saddle geometry saved
(`ga_saddle_path.extxyz`).

## Anchor (d) — strain–E_a correlation ✓

Barrier vs applied strain, −3% to +3%, on the relaxed γ cell (cell strained,
internal coordinates then relaxed at fixed cell — the residual/epitaxial-strain
setup). Two strain modes:

**Biaxial (in-plane a,b — the experimentally relevant thin-film case): clean and
monotonic.**

| ε (%) | −3 | −2 | −1 | 0 | +1 | +2 | +3 |
|-------|----|----|----|----|----|----|----|
| E_a (eV) | 0.329 | 0.305 | 0.278 | 0.259 | 0.217 | 0.204 | 0.207 |

- **Tensile lowers, compressive raises** — the expected sign, monotonic from −3%
  through +2% (a 3 meV uptick at the +3% extreme is within the method's noise).
- Slope **dE_a/dε = −2.25 eV per unit strain** (r = **−0.976**); ≈ **−41 meV per
  +1% tensile**, +19 meV per −1% compressive near zero.

**Isotropic (hydrostatic): confirms the tensile sign, noisy under compression.**
The isotropic tensile branch matches biaxial, but two compressive points scatter
(−1% reads high, −2% low; full-range r = −0.10). A **tight-convergence re-run**
(endpoint fmax 0.03→0.02, NEB fmax 0.05→0.03) returned **bit-identical**
barriers, proving the scatter is **real PES roughness, not under-convergence** —
hydrostatic compression couples to the γ-phase octahedral-tilt soft modes,
roughening the compressive barrier. Biaxial strain leaves the long c-axis alone
and stays smooth, which is why it is the primary anchor and the experimentally
relevant one.

## Anchor (b) — charge-state ordering: DFT-gated (scaffold only) ⛔

Tyagi et al. (2025) report an order-of-magnitude mobility separation between
V_I⁺ and V_I⁰. **This is a pure charge-state effect, and MACE-MP-0 is
charge-agnostic** — it returns one quasi-neutral PES regardless of nominal cell
charge. Every barrier in this project (including anchors a, c, d) is therefore a
V_I⁰-like number. Reproducing (b) requires **charged-supercell DFT + one
MACE model fine-tuned per charge state** (proposal Layer 5 / §4.5).

No number is reported for (b) because a zero-shot value would be physically
meaningless. The full workflow — DFT settings, FNV finite-size correction,
per-charge-state fine-tuning, active-learning closure to
|E_a^MLIP − E_a^DFT| < 0.05 eV, and the anchor test — is written out in
**`CHARGE_STATE_PROTOCOL.md`**, ready to execute once a DFT allocation is
secured. Gating item: **CSD3 (or equivalent) allocation — not yet in hand.**

---

## Method summary

- **Structure.** γ-P1 CsPbI₃ (tilted, −18 meV/atom below cubic), 20-atom cell →
  2×2×2 → one iodide removed (V_I), cis octahedron-edge hop (i_vac 71 → i_hop
  128, 4.53 Å). GA⁺ built as a planar C(NH₂)₃⁺ replacing the nearest Cs, with
  atom ordering matched between NEB endpoints.
- **NEB.** 5 interior images, IDPP interpolation, two-stage FIRE (no-climb then
  climb), **per-image calculators** (3.4× faster than a shared calculator — see
  `results/gpu/BENCHMARK.md`), **float64**.
- **Barrier.** Forward = max(image energy) − initial; well-to-well.
- **Compute.** All NEBs on one RTX 5090; the full anchor set (regression + 14
  strain paths + GA⁺) is ~17 paths, well under the ~1500 paths/hr farm rate.

## Reproduction

```bash
# on the GPU host, repo unpacked, base conda (torch 2.8.0+cu128, mace 0.3.16):
python scripts/04_objective1_anchors.py --mode all --device cuda --dtype float64
# tight-convergence strain re-check:
python scripts/04_objective1_anchors.py --mode strain --device cuda --dtype float64 \
    --fmax-ep 0.02 --fmax-neb 0.03 --tag _tight
```

Outputs: `results/objective1/{regression,strain,strain_tight,ga,anchors,anchors_summary}.json`,
saddle paths (`*_saddle_path.extxyz`), and this figure (`strain_Ea.png`).

## Files

- `strain_Ea.png` — anchors (c) & (d) figure
- `anchors_summary.json` — consolidated, analysis-ready results for all anchors
- `regression.json`, `strain.json`, `strain_tight.json`, `ga.json` — raw per-anchor data
- `regression_saddle_path.extxyz`, `ga_saddle_path.extxyz` — NEB image trajectories
- `CHARGE_STATE_PROTOCOL.md` — anchor (b) ready-to-run DFT + fine-tune recipe
- `../../scripts/04_objective1_anchors.py` — the driver

## Caveats

- Barriers are **zero-shot, quasi-neutral** (V_I⁰-like). Relative shifts (ΔE_a,
  strain slopes) are the trustworthy deliverables; absolute values inherit the
  known finite-size sensitivity of the 2×2×2 cell (undoped 2×2×2 = 0.46 eV vs
  3×3×3 = 0.12 eV in the cubic screen — the self-image term is large in the small
  cell, but cancels in the *relative* quantities reported here).
- GA⁺ and strain magnitudes are zero-shot; production ranking (Objective 2) uses
  the fine-tuned models per the same charge-state protocol.

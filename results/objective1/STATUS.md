# Objective 1 — single status table

**This file is the single authoritative status source for Objective 1 (method
validation).** Where README / HANDOFF / DFT_BENCHMARK / anchors_summary disagree
about a completion state, this table wins. Last updated 2026-07-23.

## Anchor (b) headline status — READ THIS FIRST

```
FIXED-GEOMETRY ELECTRONIC COMPARISON:        COMPLETE
RELAXED-CHARGE-STATE MIGRATION BARRIER:      PENDING
```

The charged-supercell DFT machinery runs end-to-end and gives a converged,
self-consistent *fixed-geometry* number (V_I⁰ 141 meV vs V_I⁺ 127 meV on the same
MACE-relaxed neutral geometry). This is **not** Tyagi et al. (2025)'s
order-of-magnitude separation — that requires *relaxed* charged geometries
(charged-cell relaxation at each image, or a charged NEB), which has not been run.

## Status table

| # | date | calc ID | host / phase / supercell | method / model / charge / spin | geometry state | result | status |
|---|---|---|---|---|---|---|---|
| a-zs | 2026-07-22 | `anchors.json:regression` | local CPU / γ-P1 / 2×2×2 (159 at) | MACE-MP-0 medium zero-shot, float64, charge-agnostic | MACE-relaxed CI-NEB | E_a = **0.259 eV** fwd / 0.230 eV bwd; saddle img3 | ✅ pipeline sanity (in 0.1–0.6 eV band) |
| a-dft | 2026-07-23 | `dft_benchmark.json:anchor_a` | ehpc Slurm `comp` / γ-P1 / 2×2×2 | QE 7.5 PBE, US psl-1.0.0, Γ, ecut 50/400, non-spin | fixed-path single-point (MACE geom) | DFT **140.6 meV** vs MACE 259.0 meV (**1.84×**); both saddle img3 | ✅ fixed-geometry complete |
| b-fix | 2026-07-23 | `dft_benchmark.json:anchor_b` | ehpc Slurm `comp` / γ-P1 / 2×2×2 | QE 7.5 PBE, q=0 (1401 e⁻) vs q=+1 (1400 e⁻), non-spin | fixed-path single-point (same neutral geom) | V_I⁰ **140.6** / V_I⁺ **126.6 meV** (ratio 0.90) | ⚠️ FIXED-GEOMETRY COMPLETE / RELAXED PENDING |
| b-spin | 2026-07-23 | job `b520e71a` (spin_scan; 2 nodes/64 ranks) | ehpc Slurm `comp` / γ-P1 / 2×2×2 | QE 7.5 PBE, q=0 nspin 1/2, tot_mag=1, localized-Pb | fixed-path single-point | *in progress* — 3/8 SCFs done (q0 A/B) | 🔄 running |
| c-GA | 2026-07-22 | `anchors_summary.json:anchor_c` | local CPU / γ-P1 / 2×2×2 (168 at) | MACE-MP-0 zero-shot, GA⁺ for Cs, 3 orient × near/far | MACE-relaxed CI-NEB | near +70/+278/+182 meV (spread 207); far −23 meV | ✅ sign robust / magnitude NOT converged |
| d-strain | 2026-07-22 | `anchors_summary.json:anchor_d` | local CPU / γ-P1 / 2×2×2 | MACE-MP-0 zero-shot, biaxial + isotropic strain | MACE-relaxed CI-NEB per strain | biaxial dE_a/dε = **−2.25 eV/strain** (r=−0.98) | ✅ trend reproduced (biaxial); iso branch unresolved |
| fs | 2026-07-22 | `finite_size.json` | local CPU / γ-P1 / 3×3×3 (540 at) | MACE-MP-0 zero-shot vs 2×2×2 | MACE-relaxed CI-NEB | undoped 0.259→0.258 eV; strain −41=−41; GA +70→+335 | ✅ undoped+strain size-converged; GA not |

Legend: ✅ complete · ⚠️ partial (see limits) · 🔄 in progress.

## Per-calculation detail (limits / allowed claim / next step / actual cost)

### a-zs — undoped zero-shot MACE E_a
- **Limits:** zero-shot MACE-MP-0 overestimates the PBE barrier 1.84× (see a-dft); charge-agnostic (quasi-neutral PES). NOT an Eames 2015 reproduction — Eames studied MAPbI₃ (~0.6 eV); 0.1–0.6 eV is the cross-literature band.
- **Allowed claim:** "the zero-shot pipeline gives an E_a in the literature band and reproduces the octahedron-edge mechanism; usable for path seeding and float32/64 regression, not for absolute barriers."
- **Next step:** superseded by fine-tuned models (Stage 3).
- **Actual cost:** ~20 s/path (local CPU), negligible.

### a-dft — undoped DFT-vs-MACE benchmark
- **Limits:** PBE is not ground truth (typically underestimates halide migration barriers; no SOC, GGA delocalization). Single-point on MACE geometry, not a DFT-NEB. Γ-only, one supercell size, non-spin.
- **Allowed claim:** "PBE and MACE-MP-0 disagree by 118 meV at fixed geometry on identical structures; MACE gets the mechanism and saddle location right but is 1.84× too high vs PBE."
- **Next step:** completed by the all-images fixed path (Stage 1.3) + spin/cutoff/k convergence (Stage 1.2).
- **Actual cost:** part of the 8-SCF matrix, ~33 min × 8 SCF on 32 cores ≈ 4.4 core-node-hours (~¥70).

### b-fix — charge-state fixed-geometry comparison
- **Limits:** **Fixed-geometry single-point only.** Removing one electron at fixed nuclei gives a 10% electronic-energy barrier change; this is NOT Tyagi's structural (relaxed) separation. Odd neutral electron count (1401) computed non-spin — the spin treatment is being checked in b-spin.
- **Allowed claim:** "at fixed geometry, V_I⁺ is ~14 meV (10%) lower than V_I⁰; the charged-supercell DFT link now runs end-to-end and is self-consistent." **Forbidden:** any claim of reproducing Tyagi's charge-state ordering.
- **Next step:** relaxed charged endpoints + charged NEB (Stage 2), after Stage 1 locks the theory level.
- **Actual cost:** shared with a-dft (8-SCF matrix).

### b-spin — Stage 1.1 odd-electron spin scan (running)
- **Reproduction gate PASSED (2026-07-23, job b520e71a, 2 nodes/64 ranks):** the
  regenerated inputs reproduce the archived benchmark to ~6 significant decimals —
  img0_q0_A = −9244.90895455 Ry (archived −9244.9089544; Δ ≈ 1.5×10⁻⁷ Ry), img3_q0_A =
  −9244.89861800 Ry (archived −9244.89861758; Δ ≈ 4.2×10⁻⁷ Ry) → **barrier 140.6 meV**
  (matches the archived 140.6 meV to <0.1 meV). Δ is at the SCF-convergence /
  I/O-rounding floor, i.e. physically identical, not bit-identical. Confirms the QE
  generator (`scripts/05`) and that the 64-rank run reproduces the 32-rank energy at
  this precision.
- **Limits:** spin cases (B/C) in progress. If nspin=2 differs from non-spin by
  >10–20 meV, the 141 meV value is downgraded to "preliminary non-spin fixed-path value."
- **Allowed claim:** "the fixed-path benchmark is reproducible from the repo to <1 meV."
- **Next step:** parse magnetization + defect-state occupation of Cases B/C; decide
  production spin setting for Stage 2.
- **Actual cost:** non-spin SCF ~26 min, spin SCF ~65 min WALL; 8-SCF scan ≈ 6–8 h ×
  2 nodes ≈ 0.5–0.7 node-days (~¥100–130 at ¥16.48/node-hr), within the ≤¥400 Stage-1 cap.

### d3 — D3(BJ) dispersion correction (Stage 1.2, COMPLETE)
- **Result:** D3(BJ) computed from geometry alone (charge-independent) raises the
  fixed-path barrier by **+25.3 meV**: PBE+D3 = **165.9 meV** (q=0) / **151.9 meV**
  (q=+1). File `dft/fixed_path/d3_check.json`.
- **Limits:** additive dispersion term on the fixed MACE path (not a self-consistent
  PBE+D3 relaxation). ~18% of the barrier — well above noise.
- **Allowed claim:** "D3 is a non-negligible (+25 meV) contribution; project-wide
  functional locked to **PBE+D3** for γ-CsPbI₃ and FA host (per EXECUTION_GUIDE 1.2)."
- **SOC:** deferred — pseudopotentials are scalar-relativistic (pslibrary US
  scalar-rel); full-relativistic SOC single-points require a separate PP set and are
  recorded here as **SOC DEFERRED** (reason: scalar-rel PP; SOC is a Stage-2+ refinement).

### c-GA — guanidinium A-site pinning
- **Limits:** magnitude NOT converged — configuration-dependent (207 meV spread across 3 orientations) AND size-dependent (+70 meV at 2×2×2 → +335 meV at 3×3×3). n=1 per orientation; H-bond-stiffening mechanism inferred from N–H···I contacts (2.4–2.7 Å), not proven. GA⁺ is a stoichiometric label (MACE charge-agnostic).
- **Allowed claim:** "GA⁺ pins the local V_I hop (sign robust: positive at the near site in all 3 orientations, ~0 at the far control, confirming a local effect)." **Forbidden:** any quantitative pinning strength.
- **Next step:** configurational + size averaging under fine-tuned models; DFT spot-check (Stage 5 pilot, GA⁺ is the positive control).
- **Actual cost:** local CPU, negligible.

### d-strain — strain–E_a correlation
- **Limits:** biaxial branch sign-correct and size-converged (−41 meV/1% at both 2×2×2 and 3×3×3) but NOT strictly monotonic (+3 meV uptick at +3%). Isotropic compressive branch scatters — numerically reproducible (bit-identical tight re-run) but mechanistically unresolved (path-switching / local minima / model artefact, not proven PES roughness).
- **Allowed claim:** "biaxial tensile strain lowers E_a, compressive raises it (dE_a/dε ≈ −2.25 eV/strain, r=−0.98), size-converged." **Forbidden:** treating the isotropic compressive scatter as physical.
- **Next step:** DFT 3-point (−1/0/+1% biaxial) check (Stage 4.4 / deferred).
- **Actual cost:** local CPU, negligible.

### fs — γ-phase finite-size check
- **Limits:** 3×3×3 (~540 atoms) vs 2×2×2; single hop path.
- **Allowed claim:** "undoped absolute E_a and the strain shift are size-converged at 2×2×2; the GA magnitude is NOT (needs the larger cell + averaging)."
- **Next step:** feeds the sampling-budget decision for Stages 4–5.
- **Actual cost:** local CPU, negligible.

## Standing claim bans (from EXECUTION_GUIDE Part 1)

Do not write, anywhere in the repo or proposal, until the gating work is done:
- "we reproduced Tyagi's charge-state mobility ordering" (needs relaxed charged NEB)
- "DFT benchmarked the true migration barrier" (PBE ≠ truth)
- "the true barrier lies between PBE and MACE" (unproven; retracted from DFT_BENCHMARK.md)
- "DFT found the true saddle" (needs all-image evaluation + DFT-NEB)

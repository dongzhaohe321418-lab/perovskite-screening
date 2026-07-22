# Objective 1 — Method pre-validation: four anchors (zero-shot status)

**Perovskite ion-migration dopant screen · γ-CsPbI₃ iodide-vacancy migration**
**Pipeline: zero-shot MACE-MP-0 (medium) + CI-NEB, γ-P1 phase, 2×2×2 V_I cell, float64, RTX 5090**

> **Status in one line.** Three zero-shot qualitative checks are complete: the
> undoped barrier passes a broad physical sanity check, GA⁺ predicts a promising
> positive local barrier shift, and biaxial strain reproduces the expected trend.
> **Strict literature reproduction and quantitative screening-readiness remain
> pending** DFT benchmarking, configurational sampling, finite-size verification,
> and explicit charge-state validation. This is *"the pipeline runs and the
> trends are physical,"* not *"the method is fully validated."*

![Strain and GA⁺ anchors]({{artifact:art_9be8ff94-ed02-435e-9cc6-5e856c5e11b2}})

| # | Anchor (literature system) | Status | Zero-shot result |
|---|--------|:------:|--------|
| a | undoped E_a magnitude — Eames 2015 (**MAPbI₃**) | sanity check ✓ | 0.259 eV — inside the broad lead-halide-perovskite spread, **not** an Eames reproduction |
| b | V_I⁺ vs V_I⁰ ordering — Tyagi 2025 | **protocol ready, calc pending** | not computable zero-shot (charge-agnostic model) |
| c | GA⁺ ΔE_a sign — A-site pinning (**hybrid MA/GA** perovskites) | **preliminary qualitative pass** | ΔE_a = +70 meV, sign correct, **one configuration** |
| d | strain–E_a trend — CsPbI₂Br / CsPbI₃ strain lit. | **trend reproduced (biaxial)** | dE_a/dε = −2.25 eV/strain, r = −0.98 |

**Why the language is careful.** An earlier draft of this report labelled (a),
(c), (d) as "MET" and called the biaxial branch "monotonic." Both overstate the
evidence: these are zero-shot, single-configuration, 0 K NEB results on a
159-atom cell, and none is yet checked against DFT or against the exact system
the cited literature measured. The corrected status below distinguishes *trend
reproduced* (defensible now) from *anchor reproduced* (needs the work in "Next
steps").

---

## Anchor (a) — undoped barrier: physical sanity check ✓ (not an Eames reproduction)

The γ-CsPbI₃ tracer-bullet barrier, recomputed in **float64** (production dtype),
is **E_a = 0.259 eV forward / 0.230 eV reverse** — reproducing the float32
baseline to ~0.05 meV. It lies inside the **broad** range reported for
iodide-vacancy migration across lead-halide perovskites (~0.1–0.6 eV across many
NEB studies; individual reports span roughly 0.08–0.68 eV).

**This is a sanity check, not a reproduction of Eames et al. (2015).** Eames
studied **MAPbI₃** (a different composition) and reported **≈0.6 eV** for iodide
vacancy migration in a large supercell. Our number is a different material
(γ-CsPbI₃), a different phase, a smaller cell, and a zero-shot potential; the
correct claim is *"0.259 eV is a physically reasonable iodide-vacancy barrier for
a lead-halide perovskite,"* not *"we reproduced Eames."* The proposal's shorthand
("Eames 0.1–0.6 eV band") conflates Eames' specific value with the wider
literature spread; this report separates them.

**Endpoint asymmetry.** Forward 0.259 vs reverse 0.230 eV ⇒ the two wells differ
by **0.029 eV**. In the γ-P1 phase the two iodide sites (i_vac 71, i_hop 128) are
**symmetry-inequivalent** and relax slightly differently, so the initial and
final states are not strictly degenerate. All comparisons in this report use the
**forward** barrier consistently.

Value of this anchor: a **cross-platform / cross-dtype regression test**. Any
future environment or MACE-version change must still reproduce 0.259 eV here
(the cubic 3×3×3 screen's 0.119 eV is a separate phase/cell and only a loose
cross-check).

## Anchor (c) — GA⁺ A-site: preliminary qualitative pass (one configuration)

Guanidinium (C(NH₂)₃⁺, planar 10-atom cation) substituted on the Cs site nearest
the hop (3.36 Å from the path midpoint) **raises** the barrier:

| | E_a (eV) |
|---|:---:|
| undoped γ | 0.259 |
| GA⁺ on A-site | 0.329 |
| **ΔE_a** | **+0.070 (raises / pins)** |

The **sign is correct and the magnitude is promising** — GA⁺ is a known A-site
pinning cation, and +70 meV is close to the ~+84 meV effective shift reported for
hybrid systems. But this is **not yet a strict anchor reproduction**, for five
reasons that must be closed before it counts as validated:

1. **System mismatch.** The GA pinning literature is MA₁₋ₓGAₓPbI₃ (GA replaces
   **MA** in a hybrid lattice); here GA replaces **Cs** in all-inorganic
   γ-CsPbI₃.
2. **Observable mismatch.** The literature value is an *effective, multi-path*
   activation energy from temperature-dependent conductivity; ours is a single
   0 K NEB path adjacent to one GA.
3. **Charge is a label, not a physical +1.** MACE-MP-0 has no electron-count
   input, so "GA⁺" here is a stoichiometric/geometric substitution, not an
   explicitly charged molecular cation.
4. **Configurational bias (n = 1).** One GA position and one orientation only —
   no near/far or orientation sampling, so the +70 meV could shift with
   configuration.
5. **Mechanism is a hypothesis.** The H-bond-stiffening picture is untested here;
   it needs N–H···I distances/angles, Pb–I bond-length and octahedral-distortion
   changes at the saddle, and ≥2 orientations to support.

**Concentration.** One Cs of 32 A-sites ⇒ **x_GA = 1/32 = 3.125 %**. The GA cell
with the vacancy has **168 atoms** (159 undoped + 10-atom GA − 1 Cs), not 159.

Status: **preliminary qualitative pass; DFT + configurational validation
pending.** Saddle geometry saved (`ga_saddle_path.extxyz`).

## Anchor (d) — strain–E_a trend: reproduced (biaxial); hydrostatic branch unresolved

Barrier vs applied strain, −3 % to +3 %, on the relaxed γ cell (cell strained,
internal coordinates then relaxed at fixed cell — the residual/epitaxial-strain
setup).

**Biaxial (in-plane a,b — the experimentally relevant thin-film case): trend
reproduced.**

| ε (%) | −3 | −2 | −1 | 0 | +1 | +2 | +3 |
|-------|----|----|----|----|----|----|----|
| E_a (eV) | 0.329 | 0.305 | 0.278 | 0.259 | 0.217 | 0.204 | 0.207 |

- **Tensile lowers, compressive raises** — the expected sign, and the correct
  direction reported for CsPbI₂Br (0.667 eV unstrained → 0.794 compressive /
  0.547 tensile) and for CsPbI₃ generally (universal decrease with tensile
  strain).
- **Monotonic from −3 % through +2 %**, then a **+3 meV uptick at +3 %**
  (0.204 → 0.207). It is therefore *strongly negatively correlated and monotonic
  up to +2 %*, **not** strictly monotonic across the full range. (An MAPbI₃ DFT
  study similarly finds little biaxial change up to +2 % then a steeper drop —
  qualitatively consistent, though a different material.)
- Slope **dE_a/dε = −2.25 eV per unit strain** (r = **−0.976**). Measured as ΔE_a
  relative to the unstrained barrier (0.259 eV), **+1 % tensile lowers E_a by
  ≈ 41 meV** (0.259 → 0.217) and **−1 % compression raises it by ≈ 19 meV**
  (0.259 → 0.278) — one sign convention, both consistent with "tensile lowers,
  compressive raises." The +3 meV uptick is small against the 125 meV range,
  but calling it "within noise" would require a proper error estimate — the
  float32/float64 agreement (~0.05 meV) is a numerical-reproducibility figure,
  **not** a model-error bar — so it is reported here as an unexplained small
  non-monotonicity at the tensile extreme, not dismissed.

**Isotropic (hydrostatic): confirms the tensile sign; compressive branch
unresolved.** The isotropic tensile points track biaxial, but two compressive
points scatter (−1 % reads high, −2 % low; full-range r = −0.10). A
tight-convergence re-run (endpoint fmax 0.03→0.02, NEB fmax 0.05→0.03) returned
**bit-identical** barriers. That proves the result is **numerically reproducible
and convergence-independent** — it does **not** prove the scatter is physical PES
roughness. It could equally be path-switching between competing minimum-energy
paths, the optimiser settling into different local minima, or a zero-shot-model
artefact. **Mechanistically unresolved**; alternative pathway initialisation and
a DFT check are required before interpreting the compressive scatter physically.
Biaxial is the primary anchor because it is smooth *and* the experimentally
relevant case; isotropic is reported as-is.

## Anchor (b) — charge-state ordering: protocol ready, calculation pending ⛔

Tyagi et al. (2025) report an order-of-magnitude mobility separation between
V_I⁺ and V_I⁰. This is a **pure charge-state effect, and MACE-MP-0 is
charge-agnostic** — it has no supercell-charge or electron-count input, so
labelling a cell q = 0 or q = +1 changes nothing in the energy it returns.

Consequently the barriers in this project (including anchors a, c, d) are
**charge-unspecified, neutral-reference predictions — they cannot be assigned to
either V_I⁰ or V_I⁺.** (An earlier draft called them "V_I⁰-like"; that is also
too strong — the model does not explicitly represent the neutral vacancy's
electronic state either.)

Reproducing (b) requires **charged-supercell DFT + one MACE model fine-tuned per
charge state** (proposal Layer 5 / §4.5). **This is the single most important
unvalidated link in the whole method** — it decides whether the pipeline can rank
charged defects at all — not a formality that merely awaits compute. No number is
reported. The full ready-to-run workflow (DFT settings, FNV finite-size
correction, per-charge-state fine-tuning, active-learning closure to
|E_a^MLIP − E_a^DFT| < 0.05 eV, and the anchor test) is in
**`CHARGE_STATE_PROTOCOL.md`**. Gating item: **CSD3 (or equivalent) DFT
allocation — not yet in hand.**

---

## Finite-size sensitivity (open, not closed)

The cubic screen found a large gap between 2×2×2 (0.461 eV) and 3×3×3 (0.119 eV)
cells. This signals **strong finite-size sensitivity**, but two cautions apply:

- The mechanism is **elastic / defect-concentration** (the vacancy's strain field
  overlapping its periodic images), **not** the charged-defect electrostatic
  self-image — these cells are charge-neutral, so the self-image framing used in
  an earlier draft is the wrong one.
- Partial cancellation in *relative* quantities (ΔE_a, strain slopes) is
  *expected* but **not demonstrated** for the γ phase, and especially not for the
  GA case (GA changes the local elastic field) or the strain case (strain changes
  long-range relaxation). It **must be tested explicitly** with a γ-phase 3×3×3
  check on representative undoped / GA / strained cells.

---

## Method summary

- **Structure.** γ-P1 CsPbI₃ (tilted, −18 meV/atom below cubic), 20-atom cell →
  2×2×2 → one iodide removed (V_I, 159 atoms), cis octahedron-edge hop (i_vac 71 →
  i_hop 128, 4.53 Å). GA⁺ = planar C(NH₂)₃⁺ replacing the nearest Cs (168-atom
  cell), atom ordering matched between NEB endpoints.
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

## Next steps (to convert "trends physical" → "method validated")

Before the ~50-dopant Objective 2 ranking, in priority order:

1. **DFT check the undoped and GA paths** — at minimum the endpoints, the MLIP
   saddle, and the two images flanking it, for both.
2. **GA configurational sampling** — 2–3 GA orientations and a near/far GA–path
   distance pair, to test whether the +70 meV is robust or configuration-dependent.
3. **Biaxial DFT 3-point** — −1.5 %, 0, +1.5 % DFT check against the zero-shot
   slope.
4. **γ-phase finite-size check** — same phase, same path, 3×3×3 vs 2×2×2, for
   undoped and one strained/GA case.
5. **V_I⁺ vs V_I⁰ (anchor b)** — the charged-DFT + per-charge-state fine-tune, as
   soon as a DFT allocation lands; it gates whether the pipeline can rank charged
   defects at all.

## Files

- `strain_Ea.png` — anchors (c) & (d) figure
- `anchors_summary.json` — consolidated, analysis-ready results (with honest status flags)
- `regression.json`, `strain.json`, `strain_tight.json`, `ga.json` — raw per-anchor data
- `regression_saddle_path.extxyz`, `ga_saddle_path.extxyz` — NEB image trajectories
- `CHARGE_STATE_PROTOCOL.md` — anchor (b) ready-to-run DFT + fine-tune recipe
- `../../scripts/04_objective1_anchors.py` — the driver

## Caveats (summary)

- Barriers are **zero-shot, charge-unspecified (neutral-reference), single-config,
  0 K, 159-atom** numbers. **Relative** shifts (ΔE_a, strain slopes) are the
  intended deliverables; absolute values and the finite-size cancellation
  assumption are not yet DFT- or size-verified in the γ phase.
- GA⁺ and strain magnitudes are zero-shot and single-configuration; production
  ranking (Objective 2) uses the fine-tuned models per the charge-state protocol.

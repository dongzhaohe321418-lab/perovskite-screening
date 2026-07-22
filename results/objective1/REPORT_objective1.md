# Objective 1 — Method pre-validation: four anchors (zero-shot status)

**Perovskite ion-migration dopant screen · γ-CsPbI₃ iodide-vacancy migration**
**Pipeline: zero-shot MACE-MP-0 (medium) + CI-NEB, γ-P1 phase, 2×2×2 V_I cell, float64, RTX 5090**

> **Status in one line.** Three zero-shot qualitative checks are complete: the
> undoped barrier passes a broad physical sanity check, GA⁺ predicts a robust
> positive *local* barrier shift (sign confirmed across orientation, site, and
> cell size), and biaxial strain reproduces the expected trend. **Strict
> literature reproduction and quantitative screening-readiness remain pending**
> DFT benchmarking and explicit charge-state validation. Two of the review's
> DFT-free next-steps are now closed: **GA configurational sampling** and the
> **γ-phase finite-size check** (below). This is *"the pipeline runs, the trends
> are physical, and the signs are robust,"* not *"the method is fully validated."*

![Strain and GA⁺ anchors]({{artifact:art_9be8ff94-ed02-435e-9cc6-5e856c5e11b2}})

![GA configurational robustness and γ-phase finite-size check]({{artifact:art_65e6a74b-ed60-429b-a7e3-bfc9fd7757e2}})

| # | Anchor (literature system) | Status | Zero-shot result |
|---|--------|:------:|--------|
| a | undoped E_a magnitude — Eames 2015 (**MAPbI₃**) | sanity check ✓ | 0.259 eV — inside the broad lead-halide-perovskite spread, **not** an Eames reproduction |
| b | V_I⁺ vs V_I⁰ ordering — Tyagi 2025 | **protocol ready, calc pending** | not computable zero-shot (charge-agnostic model) |
| c | GA⁺ ΔE_a sign — A-site pinning (**hybrid MA/GA** perovskites) | **sign robust, magnitude not converged** | pins in all 3 orientations (+70…+278 meV) + far control ≈ 0; magnitude configuration- **and** size-dependent |
| d | strain–E_a trend — CsPbI₂Br / CsPbI₃ strain lit. | **trend reproduced (biaxial), size-robust** | dE_a/dε = −2.25 eV/strain, r = −0.98; ΔE_a size-converged (−41 meV at 2×2×2 = 3×3×3) |

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
NEB studies; individual reports span roughly 0.08–0.58 eV).

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
4. **Configurational bias.** *Now tested* (was n = 1).
5. **Mechanism.** *Now probed* with structural fingerprints (below).

**Configurational sampling (post-review).** The GA anchor was re-run over **three
distinct orientations** of the rigid cation at the Cs site nearest the hop, plus
a **far-site control** (GA ~16 Å from the hop). The `--mode ga` driver records
ΔE_a and mechanistic fingerprints (N–H···I contact, Pb–I bonds, octahedral
distortion) at the initial and saddle images for each.

| configuration | GA–hop distance | ΔE_a (meV) | closest N–H···I at saddle |
|---|---:|---:|---:|
| near, xy-plane | 3.36 Å | **+70** | 2.41 Å |
| near, xz-plane | 3.36 Å | **+278** | 2.63 Å |
| near, tilted 60° | 3.36 Å | **+182** | 2.66 Å |
| **far (control)** | 16.12 Å | **−23** | 2.67 Å |

Two findings, one reassuring and one cautionary:

- **The pinning sign is robust; it is a genuinely *local* effect.** All three near
  orientations pin (ΔE_a > 0), and the far control gives ΔE_a ≈ 0 (−23 meV) — a GA
  far from the migration path does not change the barrier, exactly as a local
  pinning mechanism requires. The N–H···I contacts of 2.4–2.7 Å at the saddle
  (well inside a hydrogen-bond length) support the H-bond-stiffening picture.
- **The magnitude is *not* configuration-converged.** Across orientations ΔE_a
  spans **+70 to +278 meV — a 207 meV spread, ~4× variation**. My original
  single-configuration +70 meV was the *smallest* of the three, so it understated
  the effect. A single NEB configuration cannot be trusted for a *rankable*
  pinning magnitude; that needs orientation/position averaging on the fine-tuned
  model.

**Concentration.** One Cs of 32 A-sites ⇒ **x_GA = 1/32 = 3.125 %**. The GA cell
with the vacancy has **168 atoms** (159 undoped + 10-atom GA − 1 Cs), not 159.

Status: **preliminary qualitative pass — sign confirmed robust (orientation +
site + control), magnitude configuration-dependent.** Quantitative pinning
strength remains DFT- and averaging-gated. Data: `ga.json` (all configs +
fingerprints), saddle geometry `ga_saddle_path.extxyz`.

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

## Finite-size check (now tested directly in the γ phase)

The cubic screen had shown a large 2×2×2→3×3×3 gap (0.461 → 0.119 eV), raising
the worry that all these barriers are finite-size-dominated. That check has now
been run **in the γ phase, on the same V_I edge-hop** (`--mode finite_size`):
the identical path in a **3×3×3 (~540-atom)** cell versus the production
**2×2×2 (159-atom)** cell, for undoped / GA-near / biaxial-tensile.

| quantity | 2×2×2 | 3×3×3 | change | verdict |
|---|---:|---:|---:|---|
| **undoped E_a (absolute)** | 0.2590 eV | 0.2585 eV | −0.5 meV | **size-converged** |
| **tensile +1 % ΔE_a** | −41.5 meV | −40.8 meV | +0.7 meV | **cancels cleanly** |
| **GA-near ΔE_a** | +70 meV | +335 meV | **+264 meV** | **does *not* cancel** |

*(Change column computed from the raw `finite_size.json` values, not the rounded display columns; both non-GA deltas are <1 meV.)*

Three distinct outcomes:

1. **The γ undoped barrier is size-converged.** Unlike the cubic screen, the γ
   2×2×2 and 3×3×3 give the same absolute barrier to 1 meV. The cubic
   0.461→0.119 collapse is a property of that (different phase, different hop)
   setup, **not** a general defect of the 2×2×2 cell — the γ production cell is
   fine for the undoped anchor.
2. **The strain slope is finite-size robust.** The tensile ΔE_a is identical
   (−41 meV) at both sizes, so anchor (d)'s deliverable — the *relative* strain
   response — is trustworthy at 2×2×2. Cancellation holds here.
3. **The GA pinning shift is *not* size-converged.** ΔE_a grows from +70 meV
   (2×2×2) to +335 meV (3×3×3). Combined with the 207 meV orientation spread
   above, this means the GA *magnitude* is converged in **neither** configuration
   **nor** cell size. The GA substitution changes the long-range elastic field
   (168/548-atom cells with a bulky molecular cation), and that interacts with
   the vacancy's periodic images differently at each size.

**Mechanism note.** These cells are charge-neutral, so the size dependence is
**elastic / defect-concentration** (overlapping strain fields of the periodic
vacancy and, for GA, the cation), **not** a charged-defect electrostatic
self-image — the "self-image cancels" framing in an earlier draft named the
wrong mechanism. Data: `finite_size.json`.

**Consequence for the anchors.** (a) undoped and (d) strain-slope are
finite-size-safe at 2×2×2; (c) GA magnitude is not, reinforcing that GA needs
configurational **and** size averaging (or a large-cell reference) before a
number is quoted. None of this changes the *signs*, which are the qualitative
deliverables here.

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

The two DFT-free items (2, 4) are now **done** (this update); the remaining three
are DFT-gated and wait on an allocation.

1. **DFT check the undoped and GA paths** — at minimum the endpoints, the MLIP
   saddle, and the two images flanking it, for both. *(DFT-gated.)*
2. ~~**GA configurational sampling**~~ — **DONE.** 3 orientations at the near site
   + far-site control: sign robust (all near pin, far ≈ 0), magnitude spans
   +70…+278 meV (207 meV spread). See Anchor (c) and `ga.json`.
3. **Biaxial DFT 3-point** — −1.5 %, 0, +1.5 % DFT check against the zero-shot
   slope. *(DFT-gated.)*
4. ~~**γ-phase finite-size check**~~ — **DONE.** 3×3×3 vs 2×2×2 for undoped / GA /
   tensile: undoped + strain-slope size-converged, GA magnitude is not. See the
   finite-size section and `finite_size.json`.
5. **V_I⁺ vs V_I⁰ (anchor b)** — the charged-DFT + per-charge-state fine-tune, as
   soon as a DFT allocation lands; it gates whether the pipeline can rank charged
   defects at all. *(DFT-gated — `CHARGE_STATE_PROTOCOL.md`.)*

## Files

- `strain_Ea.png` — anchors (c) & (d) figure (strain sweep + GA barrier overlay)
- `obj1_refine.png` — post-review figure: GA configurational robustness + γ finite-size
- `anchors_summary.json` — consolidated, analysis-ready results (with honest status flags)
- `regression.json`, `strain.json`, `strain_tight.json`, `ga.json`, `finite_size.json` — raw per-anchor data
- `regression_saddle_path.extxyz`, `ga_saddle_path.extxyz` — NEB image trajectories
- `CHARGE_STATE_PROTOCOL.md` — anchor (b) ready-to-run DFT + fine-tune recipe
- `../../scripts/04_objective1_anchors.py` — the driver (`--mode` regression/strain/ga/finite_size/all)

## Caveats (summary)

- Barriers are **zero-shot, charge-unspecified (neutral-reference), single-config,
  0 K, 159-atom** numbers. **Relative** shifts (ΔE_a, strain slopes) are the
  intended deliverables; absolute values and the finite-size cancellation
  assumption are not yet DFT- or size-verified in the γ phase.
- GA⁺ and strain magnitudes are zero-shot and single-configuration; production
  ranking (Objective 2) uses the fine-tuned models per the charge-state protocol.

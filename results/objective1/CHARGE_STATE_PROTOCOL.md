# Charge-state protocol scaffold — anchor (b): V$_\mathrm{I}^{+}$ vs V$_\mathrm{I}^{0}$ ordering

**Status: DFT-GATED — SCAFFOLD ONLY. No compute has been run for this anchor.**
This document is the ready-to-run recipe; it is executed once a DFT allocation
(CSD3 or equivalent) is secured. It exists so that anchor (b) is *specified*, not
*guessed*: the zero-shot MACE pipeline cannot produce this number even in
principle (see §0), so any V$_\mathrm{I}^{+}$ barrier reported before this
protocol runs would be fabricated.

---

## 0. Why this anchor cannot be done zero-shot

Objective 1(b) asks us to reproduce the **order-of-magnitude mobility separation
between the +1 and neutral iodide vacancy** reported by Tyagi et al. (2025). The
distinction is *entirely* a charge-state effect:

- **MACE-MP-0 (and standard MACE architectures generally) are charge-agnostic.**
  The model sees only atomic positions and species; it has no input channel for
  total cell charge or for the localised/delocalised electronic state that
  distinguishes V$_\mathrm{I}^{+}$ from V$_\mathrm{I}^{0}$. Feeding it a
  vacancy supercell returns *one* potential-energy surface — the quasi-neutral
  PES — regardless of the nominal charge we intend.
- Therefore the tracer-bullet and every anchor (a),(c),(d) number in this
  project is a **V$_\mathrm{I}^{0}$-like (quasi-neutral) barrier**. The
  proposal (Layer 5 / §4.5) states this explicitly and prescribes the remedy:
  **one MACE model fine-tuned per charge state**, each trained exclusively on
  charged-supercell DFT of that state.

The workflow below produces the DFT reference data and the two fine-tuned
models, then re-runs the CI-NEB in each to obtain E$_a$(V$_\mathrm{I}^{+}$) and
E$_a$(V$_\mathrm{I}^{0}$) as a like-for-like comparison against Tyagi 2025.

---

## 1. Reference structures (already in hand)

The γ-P1 2×2×2 V$_\mathrm{I}$ edge-hop path is built and validated
(`scripts/04_objective1_anchors.py`, regression E$_a$ = 0.259 eV). The endpoint
and 5 interior NEB images (`regression_saddle_path.extxyz`) are the seed
geometries for the DFT single-points below — no new structure generation is
needed. Each charge state uses the *same* geometries; only the cell charge and
the electronic-structure treatment differ.

---

## 2. DFT reference — settings

Engine: **VASP** (PBE+D3, projector-augmented wave) or **Quantum ESPRESSO**
(SSSP-efficiency PBE) — either is acceptable; VASP settings given here.

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Functional | PBE + D3(BJ) | Consistent with MACE-MP-0 training reference; dispersion matters for the soft γ lattice |
| PAW potentials | Cs_sv, Pb_d, I | semicore states for Cs/Pb |
| ENCUT | 520 eV | 1.3× max ENMAX, converged for halides |
| k-points | Γ-centred 2×2×1 | 2×2×2 supercell is already large; test 3×3×2 on the endpoint |
| Spin | non-spin-polarised for V$_\mathrm{I}^{0}$ closed shell; test collinear if a mid-gap state localises | |
| SItivity | SIGMA 0.05 eV, Gaussian smearing | insulator |
| EDIFF | 1e-6 eV | tight, for defect energetics |
| Dipole correction | LDIPOL/IDIPOL for charged cells | removes spurious field |

**Charge states.** Run each geometry twice:
- **V$_\mathrm{I}^{0}$**: NELECT = neutral (default).
- **V$_\mathrm{I}^{+}$**: NELECT = neutral − 1 (remove one electron). A
  compensating uniform jellium background is added automatically by the code;
  the resulting total energy needs the finite-size correction in §3.

**Scope of single-points.** 7 images × 2 charge states = **14 DFT single-points**
for the barrier, plus:
- bulk (defect-free) supercell in both charge references for the formation-energy
  alignment;
- a q/0 pair at 3×3×3 for the finite-size extrapolation check (§3).

~20–25 single-points total for the first pass. At ~2–6 node-hours each for a
159-atom cell at these settings, budget **~100–150 node-hours** for the DFT leg.

---

## 3. Charged-defect finite-size correction (FNV)

A charged defect in a periodic supercell has a spurious electrostatic
self-interaction with its periodic images plus the jellium background. Correct
with the **Freysoldt–Neugebauer–Van de Walle (FNV)** scheme:

1. Compute the DFT electrostatic potential for the charged and neutral cells.
2. Extract the long-range (point-charge) and short-range parts; align the
   potential far from the defect.
3. Correction energy `E_corr = E_lattice(q, ε, L) − q·ΔV_align`, with the static
   dielectric constant ε of γ-CsPbI₃ (use ε ≈ 18–21 including ionic response;
   take from the same DFT via DFPT, or literature).

Tooling: **`pymatgen.analysis.defects`** (`FreysoldtCorrection`) or **`sxdefectalign`**.
Apply the correction to **every image** of the V$_\mathrm{I}^{+}$ band before
reading off the barrier, since the alignment term varies as the defect charge
redistributes along the path.

Convergence check: repeat the q=+1 correction at 2×2×2 and 3×3×3 and confirm the
corrected formation energy is size-independent to < 50 meV. If not, extrapolate
1/L → 0.

---

## 4. Per-charge-state MLIP fine-tuning

For each charge state independently:

1. **Seed set.** The 14 NEB-image single-points (§2) + a rattled set: apply
   Gaussian displacements (σ = 0.05, 0.1 Å) to each image, 5 configs each → ~70
   more single-points per charge state. These sample the PES *around* the path,
   which is what the NEB optimiser explores.
2. **Fine-tune** MACE-MP-0 medium on that charge state's DFT set only
   (`mace_run_train --foundation_model medium --loss weighted --forces_weight
   100 --energy_weight 10`, `--default_dtype float64`, `--lr 0.001`, ~200 epochs,
   early-stop on a 15% held-out force RMSE). One model per charge state:
   `mace_ft_VI0.model`, `mace_ft_VIp.model`.
3. **Active-learning closure (2–3 cycles).** Run the CI-NEB with the fine-tuned
   model; take the committee/force-uncertainty-ranked images with the largest
   predicted error; DFT them; add to the training set; re-fine-tune. Stop when
   **|E$_a^{\text{MLIP}}$ − E$_a^{\text{DFT}}$| < 0.03–0.05 eV** on the saddle
   image (the proposal's convergence criterion).

---

## 5. Barrier extraction & the anchor test

For each charge state, run `scripts/04_objective1_anchors.py --mode regression`
with the fine-tuned model swapped in for `mace_mp(...)` (add a `--model-path`
branch — one-line change in `build_calcs`), applying the §3 FNV correction to the
V$_\mathrm{I}^{+}$ band energies before the `Ea_forward` reduction.

**Anchor (b) is met when:**
- E$_a$(V$_\mathrm{I}^{+}$) and E$_a$(V$_\mathrm{I}^{0}$) are separated in the
  direction and by the order of magnitude Tyagi et al. (2025) report
  (their headline is that the neutral vacancy is the fast diffuser and the
  charged one is much slower, or vice-versa per their Fig. — **verify the
  direction against the paper before declaring success**; do not hard-code an
  expected sign here);
- the MLIP↔DFT saddle agreement is within 0.03–0.05 eV for both states.

---

## 6. What is needed to start

- [ ] DFT allocation (CSD3 or equivalent) — **the gating item**, not yet secured.
- [ ] VASP or QE license + PAW/pseudopotential library on that cluster.
- [ ] `pymatgen.analysis.defects` + `sxdefectalign` for FNV.
- [ ] γ static dielectric constant ε (DFPT single-point, ~1 node-hour).
- [x] Seed geometries — done (`regression_saddle_path.extxyz`).
- [x] NEB driver ready to accept a fine-tuned model — one-line `--model-path` hook.

Estimated effort once the allocation lands: ~150–250 node-hours DFT + ~1 GPU-day
fine-tuning across both charge states and the AL cycles.

---

*Refs: Tyagi et al. (2025) — charge-state-resolved defect mobilities in halide
perovskites (anchor source). Freysoldt, Neugebauer & Van de Walle (2009),
Phys. Rev. Lett. 102, 016402 — FNV correction. Proposal §4.5 / Layer 5 —
charge-state representation and active-learning closure.*

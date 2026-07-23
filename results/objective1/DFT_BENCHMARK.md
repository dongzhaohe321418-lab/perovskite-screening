# DFT Benchmark of the MACE V_I Migration Barrier

**Anchor (a) — undoped barrier — DONE. Anchor (b) — charge-state separation — partially run (charged saddle pending a quiet box).**

This is the first *ab initio* check of the zero-shot MACE-MP-0 barriers used throughout
Objective 1. It answers the single most important methodological question the peer review
raised: **are the MACE numbers quantitatively trustworthy, or only qualitatively?**

![DFT-vs-MACE benchmark of the undoped V_I barrier]({{artifact:art_272dbdff-70de-4cad-858a-06fd435631b6}})

## Method

Single-point PBE-DFT total energies on the **exact MACE-relaxed NEB geometries** — no
re-relaxation, so the comparison isolates the energy model on identical structures.

| setting | value |
|---|---|
| code | Quantum ESPRESSO 7.5 (CPU, `mpirun -np 24`) |
| functional | PBE |
| pseudopotentials | pslibrary 1.0.0, ultrasoft, scalar-relativistic — Cs.pbe-spn (z=9), Pb.pbe-dn (z=14), I.pbe-n (z=7) |
| plane-wave cutoff | ecutwfc 50 Ry, ecutrho 400 Ry |
| k-points | Γ-only (159-atom 2×2×2 supercell) |
| smearing | Gaussian, 0.01 Ry |
| SCF convergence | 10⁻⁶ Ry |
| geometries | MACE-MP-0 float64 CI-NEB band (`regression_saddle_path.extxyz`), images 0/2/3/4 |

Each SCF: 1401 valence electrons, ~33 iterations, ~35 min on 12–24 cores. Images 2/3/4
bracket the MACE saddle (image 3); evaluating all three lets **DFT locate its own saddle**
rather than assuming it coincides with MACE's.

> **Note on the charged cell (anchor b).** For `tot_charge=+1`, QE adds a uniform
> neutralising background. Absolute charged-cell energies therefore carry a
> cell-dependent offset and are **not** directly comparable to neutral energies.
> The *barrier* E_a(q) = E(saddle) − E(initial) is well-defined regardless, because
> the background term is identical at the two geometries (same cell, same charge) and
> cancels in the difference. No Freysoldt (FNV) correction is needed for barrier
> *heights* — only for absolute formation energies, which we do not report.

## Result — anchor (a), undoped V_I barrier

| image (reaction coord) | DFT ΔE (meV) | MACE ΔE (meV) |
|---|---|---|
| 0 (initial) | 0.0 | 0.0 |
| 2 | 91.8 | 190.6 |
| **3 (saddle)** | **140.6** | **259.0** |
| 4 | 60.8 | 184.6 |

- **DFT barrier = 141 meV. MACE-MP-0 barrier = 259 meV.**
- **MACE overestimates the barrier by 1.84×** (+118 meV) on identical geometries.
- **Both place the saddle at image 3** — MACE gets the mechanism and the transition-state
  location right.
- The full profile shapes track each other (monotone rise to image 3, drop after); MACE is
  systematically *steeper*, not differently shaped.

### What this means

The zero-shot foundation model reproduces the **mechanism** (octahedron-edge hop, saddle
position) but **not the barrier height** — it is high by a factor ~1.8 against PBE. This is
exactly the failure mode the proposal anticipates and the reason Objective 1's ranked ΔE_a
values require a **fine-tuned** MACE model rather than the zero-shot base. It quantifies,
for the first time in this project, *how far off* zero-shot is: close enough to seed paths
and rank mechanisms, too high to report as an absolute barrier.

Two caveats on the DFT reference itself, for honesty:
- **PBE is not ground truth.** PBE typically *underestimates* halide-perovskite migration
  barriers (no SOC, no exact exchange, GGA delocalisation). The true barrier likely sits
  between PBE (141 meV) and MACE (259 meV); the 1.84× ratio is MACE-vs-PBE, not
  MACE-vs-experiment.
- **Single-point, not DFT-relaxed.** The geometries are MACE's. If DFT would relax the
  saddle to a slightly different structure, the DFT barrier could shift; this benchmark
  measures the energy model on fixed structures, which is the correct isolation for
  "is the MACE energy surface right," but is not a full DFT-NEB.

## Result — anchor (b), charge-state separation: INCOMPLETE

The V_I⁺ (charge +1) path was attempted on the same box. The **charged initial state
converged** (img0_q1), but the **charged saddle (img3_q1) did not** — the AutoDL instance
became heavily oversubscribed by other tenants (load average 50–68 on 25 cores), throttling
SCF iterations ~14× and timing out two attempts.

- Charged initial (img0_q1): converged, E = −9245.219 Ry.
- Charged saddle (img3_q1): **not converged** — needs a re-run when the box is quiet.
- **No charge-state number is reported**, because the barrier E_a(q=+1) requires the
  converged saddle. Reporting a partial value would be meaningless.

**This is fully staged to finish**: the eight input files (`imgN_qM.in`) are generated and
the toolchain is validated. One follow-up job of ~2 charged SCFs (~1.5 h on an uncontended
box) completes anchor (b) — the V_I⁺ vs V_I⁰ barrier separation of Tyagi et al. (2025).

## Reproduction

```bash
# on the box (conda env 'qe', pseudos in /root/autodl-tmp/pseudo):
conda activate qe
mpirun --allow-run-as-root -np 24 pw.x -in img3_q1.in > img3_q1.out
# barrier(q=+1) = [E(img3_q1) - E(img0_q1)] * 13.605693 eV/Ry * 1000  (meV)
```

Inputs generated by `scripts/` QE writer from `regression_saddle_path.extxyz`; raw energies
and SCF iteration counts in `dft_benchmark.json`.

## Files

- `dft_benchmark.png` — DFT-vs-MACE barrier profile (anchor a)
- `dft_benchmark.json` — raw QE total energies (Ry), profiles (meV), method block, anchor-b status
- neutral SCF outputs (img0/2/3/4 q0) + charged initial (img0 q1) harvested; charged saddle pending

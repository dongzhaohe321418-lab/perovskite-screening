# Theory-level reconciliation — Stage 2 relaxed NEB vs Stage 1 fixed-path benchmark

**Status: this note resolves an apparent 3.4x barrier discrepancy. It is a theory-level
bookkeeping issue, not a calculation error, and it constrains what may be compared.**

## The observation

| quantity | value |
|---|---|
| MACE-MP-0 gamma barrier (charge-agnostic) | 259 meV |
| Fixed-path single-point PBE, V_I0 | 141 meV |
| Fixed-path single-point PBE, V_I+ | 127 meV |
| **Stage-2 relaxed NEB, V_I+ (iter 6, UNCONVERGED)** | **431 meV, still descending** |

A relaxed minimum-energy path cannot lie above a single-point barrier through the same
endpoints, so 431 vs 127 meV demanded an explanation before any further interpretation.

## Root cause — verified from the QE input files on the cluster

| setting | Stage-1 fixed-path benchmark | Stage-2 relaxed NEB |
|---|---|---|
| dispersion | **none** (plain PBE) | **D3(BJ)**, `vdw_corr='dft-d3'`, `dftd3_version=4` |
| smearing `degauss` | 0.01 Ry | 0.005 Ry |
| geometries | MACE-relaxed, fixed | DFT-relaxed (this work) |

Absolute-energy offset between the two levels, measured on the same initial state:

- relaxed q1_initial (PBE+D3) = -9247.94069589 Ry
- fixed-path img0_q1 (PBE)    = -9245.21873060 Ry
- **difference = 2.721965 Ry = 37.03 eV** — the D3 dispersion sum over the 159-atom cell.

Independently confirmed: the NEB per-image output carries a
`DFT-D3 Dispersion Correction (3-body terms)` block; the benchmark output carries none.
NEB image-1 total energy (-9247.94069556 Ry) reproduces the standalone relaxation
(-9247.94069589 Ry) to 3e-7 Ry, so the two Stage-2 calculations are mutually consistent.

## What the 431 meV therefore contains

Three separable effects, which must not be conflated:

1. **Theory level.** Adding D3 dispersion stiffens the lattice around the migrating
   iodide and raises the saddle relative to plain PBE.
2. **Reference state.** The barrier is now measured from a DFT-relaxed minimum (a deeper
   well) rather than from an unrelaxed MACE geometry.
3. **Incomplete convergence.** At iteration 6 the interior path forces are
   0.43-0.56 eV/A against a `path_thr` of 0.10 eV/A; the barrier is still descending
   (1216 -> 945 -> 544 -> 490 -> 461 -> 431 meV).

## Binding consequences for reporting

- The Stage-1 fixed-path numbers (V_I0 141 meV / V_I+ 127 meV, ratio 0.90) and any
  Stage-2 relaxed number **must not appear in the same comparison table**.
- **No charge-state conclusion may be drawn until V_I0 and V_I+ are both computed at the
  identical theory level** (PBE+D3(BJ), degauss=0.005, DFT-relaxed endpoints). The q=0 leg
  is not yet done, so the charge-state anchor remains **PROVISIONAL**.
- `d_max` measured here (0.462 A) compares a MACE geometry against a **PBE+D3-relaxed**
  geometry. It therefore folds a theory-level change into what is nominally a
  relaxation-magnitude metric, and must be labelled that way rather than as a pure
  "MACE vs DFT relaxation" deviation.

## d_max measurement (interim, from iteration-6 band)

Minimum-image convention applied per atom; MACE band interpolated onto the DFT band's
arc-length reaction coordinate.

| image | s | E_rel (eV) | path force (eV/A) | d(migrating I) A | d(all-atom max) A |
|---|---|---|---|---|---|
| 0 | 0.000 | 0.000 | 0.045 | 0.080 | 0.181 |
| 1 | 0.276 | 0.271 | 0.492 | 0.390 | 0.390 |
| 2 | 0.501 | 0.431 | 0.426 | 0.462 | 0.462 |
| 3 | 0.726 | 0.294 | 0.563 | 0.399 | 0.399 |
| 4 | 1.000 | 0.012 | 0.050 | 0.058 | 0.132 |

- **d_max = 0.462 A**, at the saddle (image 2), driven by the migrating iodide (atom 127).
- Framework atoms track MACE closely (mean deviation 0.044 A), so the **mechanism agrees**:
  a single-ion octahedron-edge hop, one migrating iodide moving 4.22 A (DFT) vs 4.32 A (MACE).
- **This d_max is a lower bound** — the path is not converged, so the final value can only
  grow. The >= 0.4 A threshold for "full CI-NEB is required" is therefore already met.

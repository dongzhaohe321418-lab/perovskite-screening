# WP2a — DFT electronic settings for the FA host: k-sampling (2026-10-25)

**Result: production k-sampling = one k-point at supercell (½,½,½), i.e. the folded primitive R point.**

Frames: m30 undoped, MACE CI-NEB images 0 and 3 (`band_undoped_m30.extxyz`), 232 atoms,
plain PBE, pslibrary 1.0.0 US, 50/400 Ry, Gaussian 0.005 Ry, nspin = 1
(`scripts/30_qe_singlepoint.py`). Node: Aliyun g9ae, 64 MPI ranks. Raw outputs: `wp2a_kpoints/`.

| sampling | k-points | wall time | F(img3) − F(img0) | force RMS diff vs 2×2×2 (img0) | −TS img0 / img3 |
|---|---|---|---|---|---|
| Γ only | 1 | 3.1 min | 214.1 meV | 6.4 meV/Å | −68.7 / −78.8 meV |
| R point (½,½,½) | 1 | 6.4 min | 211.2 meV | 3.3 meV/Å | −65.0 / −71.2 meV |
| Γ-centred 2×2×2 | 8 | 37 min | 213.4 meV | reference | −23.5 / −27.0 meV |

- In this det-20 supercell the primitive R point (both band edges) folds to supercell (½,½,½),
  not Γ (supercell matrix determinant 20). The R-point sampling is the physically correct
  single point and reproduces the 2×2×2 path energy difference within 2.2 meV and forces within
  3.3 meV/Å at 1/6 of the cost. Absolute F per atom differs from 2×2×2 by 0.88 meV/atom (R) and
  1.38 meV/atom (Γ); absolute energies are not used.
- −TS depends strongly on sampling (the odd conduction electron is fractionally occupied) but
  cancels in differences at fixed sampling. F is used throughout; never mix samplings.

## Residual DFT force at the MACE minimum (PLAN criterion 5) — FAILS on this frame

At img0 (a MACE-relaxed endpoint, fmax 0.02 eV/Å in MACE) the DFT force is max 0.354 eV/Å,
RMS 0.152 eV/Å, independent of k-sampling (all three within 0.01 eV/Å). By element
(R point; RMS of |F_MACE − F_DFT| ≈ RMS |F_DFT| because F_MACE ≈ 0):

| element | n | RMS force error (eV/Å) |
|---|---|---|
| Pb | 20 | 0.085 |
| I | 59 | 0.063 |
| Cs | 1 | 0.076 |
| C | 19 | 0.213 |
| N | 38 | 0.249 |
| H | 95 | 0.136 |

The error sits mainly on the FA⁺ cation (stiff intramolecular modes; MACE-MP-0's FA geometry is
not the QE-PBE one), with a smaller framework component. Consequences: single-point energies at
MACE geometries carry a relaxation bias that largely, but not provably, cancels between images
of the same molecules; WP2e (DFT relaxation of endpoints) is triggered; WP3 fine-tuning is
motivated directly by this decomposition. To be confirmed across all WP2b frames.
(Per element, RMS |F_DFT| equals the RMS |F_MACE − F_DFT| above to 0.001 eV/Å for every element
except the single Cs atom, 0.088 vs 0.076 eV/Å; MACE forces at this frame are ≤ 0.017 eV/Å.)

## Figure

`figures/fig_wp2a_kpoints.{pdf,svg,png,tiff}` (183 mm; script `figures/fig_wp2a_kpoints.py`,
source data `figures/source_data/`). **a**, F(img 3) − F(img 0) for each sampling, as the deviation
from Γ-centred 2×2×2 (absolute values labelled). **b**, per-atom-component RMS force deviation from
2×2×2 for images 0 and 3 against wall time of one single point (pw.x WALL, 64 MPI ranks);
dashed line, 2×2×2 wall time. **c**, norm of the R-point DFT force on every atom of the
MACE-relaxed endpoint (m30 undoped image 0, 232 atoms), by element (count in brackets); bar,
per-element RMS; dashed lines, criterion-5 gate (all-atom RMS < 0.05, max < 0.2 eV/Å); points
jittered horizontally only. Each value is one deterministic calculation (SCF conv_thr 1e-8 Ry),
so no replicate error bars exist; one frame pair from one host, so panel c is a single-frame
diagnostic, not a corpus statistic.


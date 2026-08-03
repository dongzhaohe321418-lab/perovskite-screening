# Host manifest — the single ledger for `pool_v3_harmonised`

**Version 2, 2026-07-28. Version 1 contained a member-to-seed misassignment that corrupted
8 of 36 energies and biased the homogeneity gate. Both are corrected below and the error is
documented rather than quietly overwritten.**

## Correction notice — read before using any number here

Version 1 built its energy table by assuming **member index == seed offset**
(`seed_map[8+j]`). That assumption is false: `harmonise.json` shows the harmonised members
`m00`–`m17` correspond to pool_v2 seeds 8–25, so the mapping was shifted. The consequence:

- 8 members (`m18`–`m25`) were assigned energies belonging to **different** members, and those
  values were the **pre-harmonisation** states at `fmax ≈ 0.029–0.030` — the loose relaxation
  depth the project's own standing rule forbids mixing. Each had later been lowered by
  89–277 meV by harmonisation.
- Because those 8 values sit systematically **high**, the existing-pool mean was biased
  upward, which is exactly the direction that produced v1's reported −102.6 meV offset.
- Separately, `fmax_target = 0.02` was written as a **hardcoded literal on every row**. It was
  never measured, so the "relaxation depth is uniform" integrity check asserted something the
  file did not actually check.

**Version 2 uses no index arithmetic, and every value is measured or read from a record — none is inferred from position.** *(Reviewer warn, 2026-08-03: the earlier absolute phrasing "no assumed values" overstated this. v2 does rely on the filename→member mapping being correct, which is a verified assumption, not the absence of one — it is checked against `m00`'s own attached calculator below.)* Energies come from
`harmonise.json` matched **by filename** (`E_after`, post-harmonisation), from
`expansion_plus8.json` for `m28`–`m35`, or from a fresh MACE single point where no trustworthy
record existed (`m18`–`m27`). **Every `fmax` in the table is measured, not assumed.**

Cross-check that the filename mapping is right: `harmonise.json` gives `m00` E_after
= −1066.2244 eV, which equals the value read independently from `m00.extxyz`'s own attached
calculator. v1's misassignment would have given a different number.

## Reconciling the counts

    36 = total members in pool_v3_harmonised (m00-m35)
    28 = members that entered the 84-path corpus (m00-m27); 28 x 3 = 84
     8 = expansion members (m28-m35)
    18 = members whose energy was readable from an attached calculator -- a FILE FORMAT fact,
         not a pool subset. Quoting it as "existing 18" caused the original ambiguity.

## Measured relaxation depth

**fmax range across all 36 members: [0.01250, 0.02000]**, every value ≤ 0.0201, all measured.
The uniformity claim is now backed by measurement. Members `m18`–`m27`, whose energies v1 got
wrong, measure at fmax 0.01567–0.01925 — genuinely at target; the corrupted values were the
issue, not the structures.

## Homogeneity gate — corrected

| | all 28 existing | all 8 new |
|---|---|---|
| mean E (eV) | -1065.9769 ± 0.1392 | -1066.0085 ± 0.1706 |
| range | [-1066.224, -1065.709] | [-1066.210, -1065.658] |
| offset | — | **-31.5 meV** |
| Welch t / p | — | **t = 0.48, p = 0.6422** |
| separation | — | **0.2σ** |

**Same population, poolable.** Comparison of all three versions of this gate:

| version | offset | p | separation | status |
|---|---|---|---|---|
| partial (18 calculator-read members) | −36.6 meV | 0.6018 | 0.24σ | incomplete |
| v1 "full pool" (8 energies corrupted) | −102.6 meV | 0.1632 | 0.59σ | **wrong** |
| **v2 (all measured, correct mapping)** | **-31.5 meV** | **0.6422** | **0.2σ** | **authoritative** |

The corrupted values had inflated the apparent offset roughly threefold. The corrected pool is
*more* homogeneous than v1 claimed, and far from the 643 meV / 2.24σ / p < 1e-4 failure this
gate exists to catch.

## Integrity checks

- **36 unique member IDs**, no gaps m00–m35.
- **Zero duplicate structure hashes** — no host is double-counted.
- **fmax measured for all 36**, max 0.02000 — uniformity verified, not asserted.
- **Energy coverage 36/36**, every value from a measured source (18 harmonise.json E_after,
  8 expansion_plus8.json, 10 fresh MACE single points).

## The ledger

| member | seed | fmax (measured) | E (eV) | energy provenance | sha256[:16] | in 84-corpus |
|---|---|---|---|---|---|---|
| m00 | — | 0.01940 | -1066.2244 | harmonise.json (E_after, measured) | `0b1a9871f4e6bde8` | yes |
| m01 | — | 0.01992 | -1066.0277 | harmonise.json (E_after, measured) | `55a213b3db2d8078` | yes |
| m02 | — | 0.01984 | -1066.1063 | harmonise.json (E_after, measured) | `2218d2a917bc6f85` | yes |
| m03 | — | 0.01994 | -1065.8635 | harmonise.json (E_after, measured) | `a01bef1681b9783b` | yes |
| m04 | — | 0.01961 | -1066.0018 | harmonise.json (E_after, measured) | `983786ed5a73e4c8` | yes |
| m05 | — | 0.02000 | -1066.0618 | harmonise.json (E_after, measured) | `a47bb50095e87c9e` | yes |
| m06 | — | 0.01992 | -1065.8916 | harmonise.json (E_after, measured) | `1b98ee79e259a68f` | yes |
| m07 | — | 0.01880 | -1065.8188 | harmonise.json (E_after, measured) | `045ba4c698fa838a` | yes |
| m08 | — | 0.01959 | -1065.9007 | harmonise.json (E_after, measured) | `4e3649841696883f` | yes |
| m09 | — | 0.01900 | -1066.0199 | harmonise.json (E_after, measured) | `4b32616d8868c11f` | yes |
| m10 | — | 0.01994 | -1065.9638 | harmonise.json (E_after, measured) | `35280b2b9b6cede7` | yes |
| m11 | — | 0.01936 | -1065.7091 | harmonise.json (E_after, measured) | `5dd2f51ceda68501` | yes |
| m12 | — | 0.01980 | -1066.1789 | harmonise.json (E_after, measured) | `32c5bac61c5c396f` | yes |
| m13 | — | 0.01897 | -1066.1047 | harmonise.json (E_after, measured) | `a9f0f69e17827ca5` | yes |
| m14 | — | 0.01982 | -1065.8334 | harmonise.json (E_after, measured) | `015a12f9cecb04a9` | yes |
| m15 | — | 0.01978 | -1065.9516 | harmonise.json (E_after, measured) | `d1380829ec8af780` | yes |
| m16 | — | 0.01985 | -1065.9742 | harmonise.json (E_after, measured) | `5555ff40b824644f` | yes |
| m17 | — | 0.01992 | -1065.8616 | harmonise.json (E_after, measured) | `4dd07ea656e87674` | yes |
| m18 | — | 0.01706 | -1065.9548 | recomputed MACE single-point (measured) | `262dcc81d9a9ec44` | yes |
| m19 | — | 0.01567 | -1066.1904 | recomputed MACE single-point (measured) | `53a24f76dfc66157` | yes |
| m20 | — | 0.01881 | -1065.733 | recomputed MACE single-point (measured) | `a33254de5e8faa42` | yes |
| m21 | — | 0.01622 | -1066.1582 | recomputed MACE single-point (measured) | `4e5153e8c9ea0ee9` | yes |
| m22 | — | 0.01600 | -1065.8669 | recomputed MACE single-point (measured) | `13b2a682ae75994c` | yes |
| m23 | — | 0.01704 | -1066.0301 | recomputed MACE single-point (measured) | `a2f9a22e1a02f56a` | yes |
| m24 | — | 0.01708 | -1066.0075 | recomputed MACE single-point (measured) | `a94b64563cef3e4b` | yes |
| m25 | — | 0.01750 | -1065.8432 | recomputed MACE single-point (measured) | `e1c09dd994d6d2b2` | yes |
| m26 | — | 0.01925 | -1066.1775 | recomputed MACE single-point (measured) | `14a922d6a6bc405d` | yes |
| m27 | — | 0.01682 | -1065.8987 | recomputed MACE single-point (measured) | `9f85b26f0ced198c` | yes |
| m28 | 4242 | 0.01650 | -1065.6579 | expansion_plus8.json | `1491abe77e8b65cd` | NO |
| m29 | 4243 | 0.01800 | -1066.0501 | expansion_plus8.json | `870a6f72871fa850` | NO |
| m30 | 4244 | 0.01250 | -1066.1843 | expansion_plus8.json | `197118045b849235` | NO |
| m31 | 4245 | 0.01910 | -1065.9754 | expansion_plus8.json | `f2ee859782e93977` | NO |
| m32 | 4246 | 0.01850 | -1065.9832 | expansion_plus8.json | `3e84ff47a7a9c9e3` | NO |
| m33 | 4247 | 0.01750 | -1066.2096 | expansion_plus8.json | `d30c28e03c948bc3` | NO |
| m34 | 4248 | 0.01600 | -1065.9487 | expansion_plus8.json | `4fa78fa1d1bc7e4e` | NO |
| m35 | 4249 | 0.01920 | -1066.0586 | expansion_plus8.json | `c8ed8a0d28760b42` | NO |

**Rules going forward.** Append every new member here at creation with seed, source, measured
fmax and hash. Never infer a member's identity from index arithmetic — match by filename.
Never write a convergence target as a literal in a record; measure it. Count sample sizes from
this file, never from prose.

# Host manifest — the single ledger for `pool_v3_harmonised`

**Created because the prose carried two incompatible counts ("existing 18 + new 8" and
"pool 28 → 36"). Both were true of different things and neither was a ledger. This file is
now the only authority on which hosts exist, where each came from, and which have been used.**

## Reconciling the two counts

- **36** = total members in `pool_v3_harmonised` (m00–m35). This is the pool.
- **28** = members that entered the 84-path corpus (m00–m27). 28 × 3 systems = 84 paths.
- **8** = new members from the 2026-07-28 expansion (m28–m35), **not yet in any corpus**.
- **18** = members whose energy was readable from the file's attached calculator when I first
  ran the homogeneity gate. This was a *file-format* fact, not a pool subset, and quoting it
  as "existing 18" was the source of the confusion.

The other 18 energies were recovered from committed expansion records (16) and recomputed as
MACE single points (2, members m26/m27, which appeared in no record). **Coverage is now
36/36.**

## Homogeneity gate, redone on the complete pool

The first gate compared only the 18 members whose energies happened to be readable. On the
full pool:

| | existing 28 | new 8 |
|---|---|---|
| mean E (eV) | −1065.9058 ± 0.1769 | −1066.0085 ± 0.1706 |
| range | [−1066.224, −1065.546] | [−1066.210, −1065.658] |
| offset | — | **−102.6 meV** |
| Welch t / p | — | **t = 1.49, p = 0.1632** |
| separation | — | **0.59σ** |

**Verdict unchanged — same population, poolable.** But the honest comparison is weaker than
the partial one I first reported (−36.6 meV, p = 0.6018, 0.24σ): on the complete pool the
offset is ~3× larger and the separation 0.59σ rather than 0.24σ. Still comfortably
non-significant, and far from the 643 meV / 2.24σ / p < 1e-4 failure that this gate exists to
catch, but the margin is smaller than advertised and the fuller number is the one that
should be cited.

## Integrity checks

- **36 unique member IDs**, no gaps m00–m35.
- **Zero duplicate structure hashes** — no host is double-counted.
- **All members share `fmax = 0.02`**, so relaxation depth is uniform across the pool. This is
  the property whose violation caused the earlier 643 meV split.
- m26/m27 verified at fmax 0.0193 and 0.0168 when recomputed — both at target.

## The ledger

| member | seed | source | fmax target | E (eV) | E provenance | sha256[:16] | in 84-corpus |
|---|---|---|---|---|---|---|---|
| m00 | — | pool_v3_harmonised | 0.02 | -1066.2244 | file calculator | `0b1a9871f4e6bde8` | yes |
| m01 | — | pool_v3_harmonised | 0.02 | -1066.0277 | file calculator | `55a213b3db2d8078` | yes |
| m02 | — | pool_v3_harmonised | 0.02 | -1066.1063 | file calculator | `2218d2a917bc6f85` | yes |
| m03 | — | pool_v3_harmonised | 0.02 | -1065.8635 | file calculator | `a01bef1681b9783b` | yes |
| m04 | — | pool_v3_harmonised | 0.02 | -1066.0018 | file calculator | `983786ed5a73e4c8` | yes |
| m05 | — | pool_v3_harmonised | 0.02 | -1066.0618 | file calculator | `a47bb50095e87c9e` | yes |
| m06 | — | pool_v3_harmonised | 0.02 | -1065.8916 | file calculator | `1b98ee79e259a68f` | yes |
| m07 | — | pool_v3_harmonised | 0.02 | -1065.8188 | file calculator | `045ba4c698fa838a` | yes |
| m08 | 8 | pool_v3_harmonised | 0.02 | -1065.9007 | file calculator | `4e3649841696883f` | yes |
| m09 | 9 | pool_v3_harmonised | 0.02 | -1066.0199 | file calculator | `4b32616d8868c11f` | yes |
| m10 | 10 | pool_v3_harmonised | 0.02 | -1065.9638 | file calculator | `35280b2b9b6cede7` | yes |
| m11 | 11 | pool_v3_harmonised | 0.02 | -1065.7091 | file calculator | `5dd2f51ceda68501` | yes |
| m12 | 12 | pool_v3_harmonised | 0.02 | -1066.1789 | file calculator | `32c5bac61c5c396f` | yes |
| m13 | 13 | pool_v3_harmonised | 0.02 | -1066.1047 | file calculator | `a9f0f69e17827ca5` | yes |
| m14 | 14 | pool_v3_harmonised | 0.02 | -1065.8334 | file calculator | `015a12f9cecb04a9` | yes |
| m15 | 15 | pool_v3_harmonised | 0.02 | -1065.9516 | file calculator | `d1380829ec8af780` | yes |
| m16 | 16 | pool_v3_harmonised | 0.02 | -1065.9742 | file calculator | `5555ff40b824644f` | yes |
| m17 | 17 | pool_v3_harmonised | 0.02 | -1065.8616 | file calculator | `4dd07ea656e87674` | yes |
| m18 | 18 | pool_v3_harmonised | 0.02 | -1065.8752 | fa_pool_expansion.json | `262dcc81d9a9ec44` | yes |
| m19 | 19 | pool_v3_harmonised | 0.02 | -1065.5456 | fa_pool_expansion.json | `53a24f76dfc66157` | yes |
| m20 | 20 | pool_v3_harmonised | 0.02 | -1065.9016 | fa_pool_expansion.json | `a33254de5e8faa42` | yes |
| m21 | 21 | pool_v3_harmonised | 0.02 | -1065.6063 | fa_pool_expansion.json | `4e5153e8c9ea0ee9` | yes |
| m22 | 22 | pool_v3_harmonised | 0.02 | -1065.624 | fa_pool_expansion.json | `13b2a682ae75994c` | yes |
| m23 | 23 | pool_v3_harmonised | 0.02 | -1065.778 | fa_pool_expansion.json | `a2f9a22e1a02f56a` | yes |
| m24 | 24 | pool_v3_harmonised | 0.02 | -1065.8062 | fa_pool_expansion.json | `a94b64563cef3e4b` | yes |
| m25 | 25 | pool_v3_harmonised | 0.02 | -1065.6564 | fa_pool_expansion.json | `e1c09dd994d6d2b2` | yes |
| m26 | — | pool_v3_harmonised | 0.02 | -1066.1775 | recomputed MACE single-point | `14a922d6a6bc405d` | yes |
| m27 | — | pool_v3_harmonised | 0.02 | -1065.8987 | recomputed MACE single-point | `9f85b26f0ced198c` | yes |
| m28 | 4242 | expansion_plus8 (2026-07-28) | 0.02 | -1065.6579 | expansion_plus8.json | `1491abe77e8b65cd` | NO |
| m29 | 4243 | expansion_plus8 (2026-07-28) | 0.02 | -1066.0501 | expansion_plus8.json | `870a6f72871fa850` | NO |
| m30 | 4244 | expansion_plus8 (2026-07-28) | 0.02 | -1066.1843 | expansion_plus8.json | `197118045b849235` | NO |
| m31 | 4245 | expansion_plus8 (2026-07-28) | 0.02 | -1065.9754 | expansion_plus8.json | `f2ee859782e93977` | NO |
| m32 | 4246 | expansion_plus8 (2026-07-28) | 0.02 | -1065.9832 | expansion_plus8.json | `3e84ff47a7a9c9e3` | NO |
| m33 | 4247 | expansion_plus8 (2026-07-28) | 0.02 | -1066.2096 | expansion_plus8.json | `d30c28e03c948bc3` | NO |
| m34 | 4248 | expansion_plus8 (2026-07-28) | 0.02 | -1065.9487 | expansion_plus8.json | `4fa78fa1d1bc7e4e` | NO |
| m35 | 4249 | expansion_plus8 (2026-07-28) | 0.02 | -1066.0586 | expansion_plus8.json | `c8ed8a0d28760b42` | NO |

**Rule going forward:** any new member is appended here at creation with its seed, source,
hash and fmax target, and `in_84_corpus` (or a successor corpus field) is updated when it is
consumed. Sample-size claims must be counted from this file, never from prose.

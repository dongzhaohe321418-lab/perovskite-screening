# Objective 2 — results schema

**Tier discipline.** Every row carries a `tier` field. `EXPLORE` rows may never be
presented as a ranking. Promotion to `PRODUCTION` requires all six entry gates
(`results/objective1/OBJECTIVE2_READINESS_AUDIT.md`) to be met.

## Design rule: the configurational ensemble is a column, not a footnote

The unit of comparison between dopants is a **ΔE_a distribution**, never a single number.
This is enforced structurally: the primary key of the per-path table is

    (dopant, class, host_member, site_rank)

so a single-configuration result is *representationally impossible* to mistake for a
dopant-level result — it is one row of a group, and the group is what gets compared.
This matches the proposal, which already specifies "mechanism-annotated ΔE_a
*distributions*", and it is what gate 6 requires.

## Table 1 — `paths.csv` (one row per computed migration path)

| column | type | meaning |
|---|---|---|
| `path_id` | str | stable hash of the key below |
| `dopant` | str | `Cs_A`, `GA_A`, `Sr_B`, `K_int`, … or `undoped` |
| `class` | str | `A_site`, `B_site_ctrl`, `X_site`, `interstitial`, `none` |
| `host` | str | `FA0.95Cs0.05PbI3_det20_233` or `CsPbI3_gamma_2x2x2` |
| `host_member` | int | FA-orientation ensemble index (0-7) |
| `site_rank` | int | distance-binned site index within the member |
| `d_dopant_vacancy_A` | float | minimum-image separation |
| `charge_state` | int | 0 or +1 |
| `level` | str | `MACE-MP-0`, `PBE+D3(BJ)`, … — never mixed in one comparison |
| `Ea_forward_eV` | float | saddle minus **its own** initial image |
| `Ea_backward_eV` | float | saddle minus **its own** final image |
| `dE_endpoints_eV` | float | endpoint asymmetry |
| `converged` | bool | optimiser converged flag |
| `fmax_final` | float | final force |
| `tier` | str | `EXPLORE` \| `PRODUCTION` |

**Barrier convention.** `Ea` is always each path's own saddle relative to its own
initial state. Absolute total energies are never compared across rows — different
charge states, theory levels, and cells are not on a common energy origin.

## Table 2 — `dopant_summary.csv` (one row per dopant, derived)

| column | meaning |
|---|---|
| `dopant`, `class`, `host`, `charge_state`, `level` | grouping keys |
| `n_paths` | how many configurations entered the distribution |
| `dEa_median_meV`, `dEa_p25_meV`, `dEa_p75_meV` | distribution, not a point value |
| `dEa_spread_meV` | within-dopant configurational spread |
| `noise_floor_meV` | undoped within-host spread (gate-6 baseline) |
| `resolvable` | `dEa_spread` and separation vs `noise_floor` |
| `exceeds_10x_threshold` | \|median ΔE_a\| ≥ 59.5 meV (k_BT ln10 at 300 K) |

`resolvable=False` rows are reported but never ranked.

## Two thresholds, different jobs

- **59.5 meV** — `k_B T ln 10` at 300 K. The *physical* significance floor: below it,
  a barrier shift cannot support an order-of-magnitude rate claim (equal prefactors
  assumed; a true mobility ordering also needs the attempt frequency).
- **noise floor** — the *methodological* floor, measured as the undoped barrier spread
  across FA-orientation members. A ΔE_a below it is not resolvable in this host,
  regardless of physical significance.

A result must clear **both** to enter a ranking.

## Directory layout

```
results/objective2/
  SCHEMA.md                      <- this file
  structures/
    enumeration_manifest.json    <- 156 configs, distance-binned within r_max
  noise_floor/
    noise_floor.json             <- gate-6 baseline
    band_member_XX.extxyz        <- undoped bands per host member
  explore/                       <- MACE pre-screen (EXPLORE only)
  production/                    <- DFT, gated
```

## Known limit of this host cell

The 233-atom det-20 FA cell has a **minimum-image radius of 7.28 Å** (perpendicular
widths 15.98 / 16.09 / 14.55 Å). The proposal states the ΔE_a decay tail extends beyond
~7 Å, so this cell can supply the **ranking** but cannot resolve the **pinning radius** —
the tail begins where the cell stops being trustworthy. Radius extraction stays routed to
≥4×4×4 (≥700-atom) cells, as the proposal already specifies.

Note the cell is *not* the proposal's literal 2×2×5. Both are det = 20 with identical
composition (20 A-sites, one Cs, x = 0.050), but the naive 2×2×5 has anisotropy 2.50 and
a minimum image distance of only 13.0 Å, versus 1.016 and 19.3 Å for the near-cubic cell
that was built. The built cell is the better choice and is retained.

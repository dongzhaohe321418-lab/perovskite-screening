# WP1 depth pilot — result of the pre-registered depth gate (2026-10-27)

**Gate verdict (PLAN amendment c item 2 as revised by j): adopted fmax = 0.01 eV/Å.** Only 10 of 30
pilot rows were valid at 0.005 (20 far-field basin hops), so the reference stage switched to 0.01;
0.02 then failed against 0.01 (max |ΔE_b| 14.9 meV over 28 rows > 5 meV). Production WP1 runs the
doped cells through 0.02 → 0.01 with the 0.005 references of this pilot (amendment h item 4).

## Disclosure: the gate rule was amended after one row had been read

The gate rule and protocol v2.1 come from PLAN amendment j, written after the first pilot row
(m30 Sr@136: E_b 135.3 / 132.5 / 209.8 meV at 0.02 / 0.01 / 0.005, a hop at 0.005) had been read;
PLAN discloses that timing. On these data the amendment changes the outcome. Under the rule in force
before j (amendment c item 2 with 0.005 as reference and v2's final-stage validity, invalid rows
excluded), the 10 rows valid at 0.005 give max deviations of 10.4 meV (0.02) and 8.5 meV (0.01),
both above 5 meV, so **fmax 0.005 would have been adopted**, with 20 of 30 pilot rows (and, by
extension, a large part of production) invalid. Amendment j, motivated by that first row's hop at
0.005, switched the reference to 0.01 and so adopted 0.01. The size of the Sr first-shell effect
does not hinge on this choice (rows valid at both 0.01 and 0.005 differ by ≤ 8.5 meV, against an
effect of ~140 meV), but at 0.005 both m30 first-shell Sr rows would have been invalid (hops).

## Design (as pre-registered, with amendments)

Hosts m30, m21, m05 × {Sr on Pb, GA on FA} × (2 nearest + 3 farthest sites) = 30 rows. Protocol v2.1
(`scripts/29`, amendment j): host and V references relaxed through fmax 0.02 → 0.01 → 0.005 eV/Å;
D_j built on the relaxed host, D_j+V on the relaxed V (warm start); every doped cell relaxed through
the same three stages (FIRE restarted per stage, cap 10000 steps); every validity check (both cells
converged; atoms > 6 Å from both defects within 0.25 Å and 20° FA rotation of the partner; vacancy
not refilled; dopant on site) made at every stage. MACE-MP-0 medium, float64, fixed cell.
E_b(stage) = E[D_j+V] − E[D_j] − E[V] + E[host], doped cells at that stage, references at 0.005.

## References

| host | host steps (0.01 / 0.005) | host ΔE 0.02→0.005 | V steps (0.01 / 0.005) | V ΔE 0.02→0.005 |
|---|---|---|---|---|
| m30 | 871 / 1565 | −216 meV | 1000 / 498 | −207 meV |
| m21 | 1316 / 3612 | −540 meV | 1899 / 373 | −412 meV |
| m05 | 756 / 1528 | −352 meV | 1197 / 6096 | −561 meV |

The references keep descending by 0.2–0.6 eV between fmax 0.02 and 0.005 (cf. `results/fa_host/
POOL_HOMOGENEITY.md`: 0.03 → 0.02 already moved members by up to 0.6 eV): the FA orientational
landscape has no well-defined bottom at these force thresholds. m21 (amendment i) and m05
(amendment j item 3) needed more than the original 3000-step cap; m30's references come from the v2
run (cap 3000, converged). The `references_steps_per_stage` field of `wp1_depth.json` reports 10000
for m30 by fallback, because that run predates the `references_protocol` record; the true cap is 3000.

## Gate

| | 0.02 | 0.01 | 0.005 |
|---|---|---|---|
| rows invalid, Sr (of 15) | 0 | 0 | 7 |
| rows invalid, GA (of 15) | 0 | 2 | 13 |
| reason | — | basin check (displacement) | basin check (all 20; 19 with 0.80–1.33 Å) |

- Valid at 0.005: 10 < 15 → reference stage 0.01 (amendment j item 2).
- 0.02 vs 0.01 on the 28 rows valid at both: max |ΔE_b| = **14.9 meV** (GA; m05 GA164) → 0.02 fails;
  **Sr alone: 2.8 meV**, GA: 14.9 meV. Adopted: **0.01**.
- The deeper stage does not converge E_b either: on the 10 rows valid at both 0.01 and 0.005,
  |ΔE_b| reaches 8.5 meV (m21 Sr64), and a hop at 0.005 shifts E_b by −93 to +206 meV. E_b on
  this landscape therefore carries a stage (relaxation-path) uncertainty of order 5–15 meV that no
  fmax removes; it enters the WP1 map as noise and is measured by criterion 1 (far-site scatter).

Figure: `figures/fig_wp1_depth_gate.*` (a: E_b(0.01) − E_b(0.02); b: invalid rows per stage; c:
E_b(0.005) − E_b(0.01), hops open). Data: `wp1_pilot/shell_m*.json` (all per-stage records),
`wp1_pilot/wp1_depth.json`, `wp1_pilot/v2pilot2_structures.tar.gz` (every stage's structures).

## What the pilot rows already show (not the WP1 result)

These 30 rows are identical to the production rows at the same sites (deterministic relaxation),
but the pre-registered WP1 verdicts (criteria 1 and 2) are made on the full production map only.
At fmax 0.01: Sr on either Pb flanking the vacancy (d ≈ 3.2 Å) gives E_b = +119 to +181 meV in all
three hosts (repulsive); Sr at d > 10 Å gives −11 to +10 meV. GA on the two nearest FA sites gives
−30 to +37 meV (valid rows) with no common sign; GA at d > 10 Å gives −22 to +45 meV.

## Recommendation carried forward (S2 onwards)

Constrain atoms beyond the basin radius to the partner's positions in D_j and D_j+V. That removes
far-field hops by construction and is expected to remove most of the 0.005-stage cost (up to 5257
FIRE steps per doped cell, all in hopping rows). Whether it also removes the stage-to-stage E_b
shifts of rows without hops (up to 14.9 meV) is untested.

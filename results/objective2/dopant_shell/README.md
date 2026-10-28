# S1 — dopant–vacancy interaction and DFT validation of MACE (index)

Plan and decision rules: `PLAN.md` (pre-registered criteria 1–6, dated amendments a–m).

| document | content |
|---|---|
| `WP2A_KPOINTS.md` | DFT settings: R-point k-sampling; MACE minima fail the residual-force gate |
| `WP2B_RESULT.md` | MACE vs DFT on 27 corpus bands: criteria 3 and 5 fail; corpus claim at DFT level (provisional) |
| `WP1_PILOT_RESULT.md` | depth pilot: fmax 0.01 adopted; far-field basin hops; gate-rule disclosure |
| `WP1_RESULT.md` | MACE binding map, 117 rows: Sr repels (+142 meV), GA inconclusive |
| `PLAN.md` amendment k | WP2e relaxations held after cell-wide wandering (−977 meV) |
| `PLAN.md` amendment m | WP3 pre-registration: data, targets (E′), training command, criterion 6, adoption rule (a)–(e) for S2 |
| `WP2C_RESULT.md` | DFT vs MACE E_b at 21 sites: criterion 4 fails (6/15 sites > 25 meV); Sr repulsion holds at DFT (+96 to +137 meV), MACE ~19 meV too high; finite-cell band term |
| `WP2D_RESULT.md` | V_I⁺ at m30: far-referenced E_b charge-state robust; removing the electron changes raw E_b by 87–104% of the Fermi shift (band term, post hoc); ΔE_a proxy shifts 43 meV with charge |
| `WP2E_RESULT.md` | WP2e uninformative: 81% of the −977 meV relaxation energy beyond 6 Å; partition single points invalid; post hoc design proposed (amendment l) |

Data: `wp2a_kpoints/`, `wp2b/` (raw QE files), `wp1_pilot/`, `wp1_production/` (JSON with every
per-stage record; structures as tar.gz), `wp2c/` (raw QE files of WP2c; `wp2cde_dft.json` = WP2c/2d
analysis), `wp2d/` (raw), `wp2e/` (relaxation, partitions, path work), `e0_atoms/`. Figures and source data:
`figures/`. Scripts: `scripts/29`–`38` (see each docstring). Every result document was checked
claim by claim by an adversarial multi-agent review before or after commit; corrections are
recorded in the documents themselves.

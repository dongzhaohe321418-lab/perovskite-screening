# S1 — dopant–vacancy interaction and DFT validation of MACE (index)

Plan and decision rules: `PLAN.md` (pre-registered criteria 1–6, dated amendments a–k).

| document | content |
|---|---|
| `WP2A_KPOINTS.md` | DFT settings: R-point k-sampling; MACE minima fail the residual-force gate |
| `WP2B_RESULT.md` | MACE vs DFT on 27 corpus bands: criteria 3 and 5 fail; corpus claim at DFT level (provisional) |
| `WP1_PILOT_RESULT.md` | depth pilot: fmax 0.01 adopted; far-field basin hops; gate-rule disclosure |
| `WP1_RESULT.md` | MACE binding map, 117 rows: Sr repels (+142 meV), GA inconclusive |
| `PLAN.md` amendment k | WP2e relaxations held after cell-wide wandering (−977 meV) |

Data: `wp2a_kpoints/`, `wp2b/` (raw QE files), `wp1_pilot/`, `wp1_production/` (JSON with every
per-stage record; structures as tar.gz), `wp2e/`, `e0_atoms/`. Figures and source data:
`figures/`. Scripts: `scripts/29`–`38` (see each docstring). Every result document was checked
claim by claim by an adversarial multi-agent review before or after commit; corrections are
recorded in the documents themselves.

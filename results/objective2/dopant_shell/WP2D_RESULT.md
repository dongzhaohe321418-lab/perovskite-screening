# WP2d — charge state of the vacancy, m30 (2026-10-28)

**Pre-registered verdict (amendment c item 4, as amended by g item 1): charge-state robust for both
dopants.**

- **Far-referenced E_b.** E_b(q = +1) − E_b(q = 0) is −4.9 meV at the Sr hinge site and −2.9 meV
  at the GA near site. Both are below 25 meV, and the near-minus-far sign is the same at both
  charges.
- **Scope of the verdict.** At m30, the near-Sr repulsion of the WP1 map therefore carries over to
  V_I⁺. The test covers one host and one near and one far site per dopant, all at the fixed
  neutral MACE geometry.
- **Second result: the barrier-energy difference.** The Sr effect on the energy difference
  img3 − img0 along the MACE path does depend on the charge state: −2.9 meV at q = 0 against
  +40.2 meV at q = +1. That 43.0 meV difference matches the finite-cell band term of the neutral
  cell (−39.7 meV) to within 3.3 meV with F and 6.0 meV with the σ→0 estimate (post hoc
  diagnostic).

## Method

- **Cells.** V_I⁺ cells (tot_charge = +1, even electron count, compensating background) at the
  same geometries as the neutral cells, all from `wp2cde_selection.json`:
  - V;
  - Sr hinge (Pb136) + V and Sr far (Pb64) + V;
  - GA near (FA128) + V and GA far (FA152) + V;
  - band images 0 and 3 of undoped and Sr m30 (amendment f).
- **DFT settings.** Otherwise as in `scripts/30`. 9 single points, all converged.
- **Binding energy.** E_b(+1) = F[D_j+V]⁺ − F[D_j] − F[V]⁺ + F[host]. The image-charge term is
  the same in F[D_j+V]⁺ and F[V]⁺ to first order and cancels. The average-potential (alignment)
  term does not cancel in raw E_b(+1), because the two charged cells differ in composition
  (amendment g item 1). It is site-independent to first order, so it cancels in far-referenced
  E_b(+1), which is what the WP2d rule uses. Raw q = +1 values and raw q0 − q1 therefore carry an
  unquantified offset of this kind.
- **What is not modelled.** No ionic relaxation in the charged state: MACE is charge-agnostic, and
  V_I⁺ relaxes differently from V_I⁰ in reality. No finite-size electrostatic correction is
  applied either; for far-referenced E_b and for differences between images of equal charge it
  cancels to first order.
- **Analysis and data.** `scripts/37`, output `wp2c/wp2cde_dft.json` (`wp2d` block); raw inputs
  and outputs in `wp2d/raw/`.

## Results (meV)

| site | E_b(q=0) raw | E_b(q=+1) raw | q0 − q1 | ΔE_F(q=0) | far-ref q=0 | far-ref q=+1 | far-ref (+1) − (0) |
|---|---|---|---|---|---|---|---|
| Sr hinge (Pb136) | +174.3 | +127.7 | +46.6 | +47.7 | +129.4 | +124.5 | −4.9 |
| Sr far (Pb64) | +44.9 | +3.2 | +41.8 | +48.1 | 0 | 0 | — |
| GA near (FA128) | +15.1 | −5.4 | +20.4 | +19.7 | +35.5 | +32.5 | −2.9 |
| GA far (FA152) | −20.4 | −37.9 | +17.5 | +17.4 | 0 | 0 | — |

**The band term (post hoc diagnostic).** The q0 − q1 and ΔE_F columns, and the band-term row of
the next table, were added to `scripts/37` after the data had been read. The pre-registered WP2d
quantity is the far-referenced difference in the last column.

- **What was measured (m30 only).** Removing the electron changes the raw E_b by 87–104% of the
  Fermi-level shift ΔE_F = E_F(D_j+V) − E_F(V) of the neutral cell. That is what Janak's theorem
  predicts if the raw q = 0 offset is the energy of the extra electron, which is the reading of
  amendment g item 1. The comparison does not test whether that state is delocalised, does not
  test the dilute limit, and cannot separate the band shift from the charged-cell alignment offset
  noted under Method.
- **How much of the far-site offset it explains.** At the m30 Sr far site the electron accounts for
  41.8 of the 44.9 meV raw offset (q = +1: +3.2 meV). The m30 GA far offset is not band term:
  removing the electron makes it larger (−20.4 → −37.9 meV). WP2d did not run at m05, where the
  far-Sr offset (+84.6 meV) exceeds its ΔE_F (+58.0 meV; `WP2C_RESULT.md`).

**ΔE_a proxy on the m30 Sr band (img3 − img0; image 3 is the MACE saddle; this is not a barrier).**

| | Sr − undoped, F(img3) − F(img0) |
|---|---|
| DFT, q = 0 (WP2b frames), F | −2.9 |
| DFT, q = 0, σ→0 estimate E₀ = F + TS/2 | −5.5 |
| DFT, q = +1 (gapped cells, no smearing term) | +40.2 |
| MACE | −32.6 |
| q0 − q1, F | −43.0 |
| q0 − q1, E₀ | −45.7 |
| neutral-cell band term [ΔE_F(img3 − img0)]_Sr − [same]_undoped | −39.7 |

- **The difference is mostly the band term.** The charge-state difference matches the
  neutral-cell band term (−39.7 meV) to within 3.3 meV with F (−43.0 meV) and 6.0 meV with E₀
  (−45.7 meV). The spread comes from the smearing entropy, which only the neutral cells carry.
  In this hinge-Sr host, the vacancy hop
  toward image 3 lowers the conduction band of the Sr cell relative to undoped, and the extra
  electron follows it. This quantifies the term flagged in `WP2B_RESULT.md` §4 (m30: −39.7 meV) as
  an energy, not only a Fermi-level shift.
- **MACE is further from DFT without that electron.** MACE − DFT is −29.8 meV at q = 0 and
  −72.8 meV at q = +1. `WP2B_RESULT.md` §4 already found that the band term does not explain
  MACE's hinge-host errors (the correlation has the opposite sign). This is the direct test, and it
  agrees.
- **What this does not show.** It does not decide which charge state is physical for transport. In
  a real film the iodide vacancy is commonly considered a shallow donor, ionised to V_I⁺; that is
  not tested here. It also gives no barrier: two fixed-path images of one host.

## Consequences

- **E_b transfers between charge states.** The WP1/WP2c binding conclusions are not specific to
  V_I⁰ at the tested sites, so the far-referenced E_b comparison stands for V_I⁺ too.
- **ΔE_a may not.** Paired barrier differences from neutral 20-f.u. cells can carry a band term of
  up to ~40 meV (hinge-Sr hosts), comparable to the ±59.5 meV equivalence band of the corpus test.
  The WP2b criterion-3 verdict (decided on raw neutral-cell values, amendment h item 1) is
  unchanged.
- **For S2 onwards.** Barrier differences should be computed for V_I⁺, or in neutral cells large
  enough for the band term to be negligible. This is a recommendation, not a pre-registered rule.

Figure: panel c of `figures/fig_wp2c_eb_transfer.*`.

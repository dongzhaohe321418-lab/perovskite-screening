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
  +40.2 meV at q = +1. That 43.0 meV difference is almost entirely (92%) the finite-cell band term
  of the neutral cell.

## Method

- **Cells.** V_I⁺ cells (tot_charge = +1, even electron count, compensating background) at the
  same geometries as the neutral cells, all from `wp2cde_selection.json`:
  - V;
  - Sr hinge (Pb136) + V and Sr far (Pb64) + V;
  - GA near (FA128) + V and GA far (FA152) + V;
  - band images 0 and 3 of undoped and Sr m30 (amendment f).
- **DFT settings.** Otherwise as in `scripts/30`. 9 single points, all converged.
- **Binding energy.** E_b(+1) = F[D_j+V]⁺ − F[D_j] − F[V]⁺ + F[host]. The background term enters
  F[D_j+V]⁺ and F[V]⁺ alike and cancels to first order.
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
| GA near (FA128) | +15.1 | −5.3 | +20.4 | +19.7 | +35.5 | +32.5 | −2.9 |
| GA far (FA152) | −20.4 | −37.9 | +17.5 | +17.4 | 0 | 0 | — |

**The band term, measured directly.** Removing the electron changes the raw E_b by 87–104% of
the Fermi-level shift ΔE_F = E_F(D_j+V) − E_F(V) of the neutral cell. This supports the reading of
amendment g item 1: the raw q = 0 offset (+42 to +85 meV at the far Sr sites, `WP2C_RESULT.md`) is
the energy of the delocalised V_I⁰ electron in the dopant-shifted conduction band. At q = +1 the
far-site E_b is +3.2 (Sr) and −37.9 meV (GA).

**ΔE_a proxy on the m30 Sr band (img3 − img0; image 3 is the MACE saddle; this is not a barrier).**

| | Sr − undoped, F(img3) − F(img0) |
|---|---|
| DFT, q = 0 (WP2b frames) | −2.9 |
| DFT, q = +1 | +40.2 |
| MACE | −32.6 |
| q0 − q1 | −43.0 |
| neutral-cell band term [ΔE_F(img3 − img0)]_Sr − [same]_undoped | −39.7 |

- **The difference is the band term.** The charge-state difference (−43.0 meV) matches the
  neutral-cell band term (−39.7 meV) to within 3.3 meV. In this hinge-Sr host, the vacancy hop
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

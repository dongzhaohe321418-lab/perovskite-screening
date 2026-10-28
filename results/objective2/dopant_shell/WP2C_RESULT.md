# WP2c — DFT transfer of the MACE binding energies (2026-10-28)

**Pre-registered verdict (PLAN criterion 4, as amended by g items 1–2 and h item 2): FAIL.**

Criterion 4 asks, for every tested site, that |far-referenced E_b(MACE) − far-referenced
E_b(DFT)| < 25 meV and that the near-minus-far sign agrees.

- **Overall.** 6 of the 15 tested sites miss the 25 meV bound: 3 of 9 for Sr and 3 of 6 for GA.
  The GA near-shell sign disagrees in 2 of 3 hosts. Only one host–dopant set passes (m30 Sr, max
  error 14.1 meV).
- **Sr: what survives.** Sr on either Pb flanking the vacancy repels it at DFT level as well:
  far-referenced DFT E_b is +95.6 to +136.7 meV at all 6 first-shell sites (3/3 hosts).
- **Sr: the size is off.** Zero-shot MACE overestimates that repulsion by +19.2 meV on average
  (−6.4 to +36.1 meV; 5 of 6 sites too high).
- **GA.** There is no consistent DFT sign either. The near site gives −12.1 to +36.3 meV, and
  mid-shell sites give values as large (−45.4 to +42.3 meV).

All DFT values are single points on the MACE-relaxed structures. MACE minima are not DFT minima
(criterion 5 failed in WP2b). The DFT relaxation bias is not available, because WP2e is
uninformative in its pre-registered form (amendment l item 3). These are therefore fixed-geometry
DFT energies, not relaxed DFT binding energies.

## Method

- **Structures.** Script 36 made the selection geometrically, before any E_b had been read
  (amendment f; `wp1_production/wp2cde_selection.json`). Hosts were m30, m21 and m05. For each
  host: Sr on the hinge Pb (the one holding the migrating iodide), the flank Pb, one mid-shell Pb
  and one far-shell Pb; GA on the nearest FA, one mid-shell FA and one far-shell FA. The structures
  are the WP1 production structures: D_j and D_j+V at the adopted stage fmax 0.01 eV/Å, host and V
  at 0.005. The MACE E_b compared below is computed from exactly these four structures.
- **DFT settings.** Plain PBE, pslibrary 1.0.0 US, 50/400 Ry, folded R point, Gaussian
  0.005 Ry, nspin 1, neutral cells, free energy F (`scripts/30`). 48 single points, all converged.
- **Binding energy.** E_b = F[D_j+V] − F[D_j] − F[V] + F[host] (positive = repulsion).
- **Criterion 4.** Evaluated on far-referenced values, E_b(site) − E_b(far site of the same
  dopant, host and level). The raw values are reported beside them.
- **Band residual (amendment h item 2).** [E_F(D_j+V) − E_F(V)] − [same at the far site], from
  the same outputs.
- **Analysis.** `scripts/37_dft_eb_analysis.py`, output `wp2c/wp2cde_dft.json`. Every difference
  is taken unrounded and stored to 3 decimals. Raw inputs and outputs are in `wp2c/raw/`.

## Results (meV)

| host | dopant | site class | site | d (Å) | DFT far-ref | MACE far-ref | MACE − DFT | band residual | DFT raw | MACE raw |
|---|---|---|---|---|---|---|---|---|---|---|
| m30 | Sr | hinge | 136 | 3.17 | +129.4 | +123.0 | −6.4 | −0.4 | +174.3 | +132.5 |
| m30 | Sr | flank | 124 | 3.20 | +95.6 | +109.6 | +14.1 | −2.6 | +140.5 | +119.2 |
| m30 | Sr | mid | 52 | 7.32 | +1.2 | −2.7 | −3.8 | −3.1 | +46.1 | +6.9 |
| m30 | Sr | far | 64 | 9.65 | 0 (ref.) | 0 (ref.) | — | — | +44.9 | +9.6 |
| m21 | Sr | hinge | 136 | 3.28 | +136.7 | +160.5 | +23.8 | +5.4 | +178.4 | +165.1 |
| m21 | Sr | flank | 124 | 3.23 | +131.7 | +157.6 | **+25.9** | −4.1 | +173.4 | +162.2 |
| m21 | Sr | mid | 0 | 7.12 | +63.3 | +20.3 | **−43.0** | +23.3 | +105.0 | +24.9 |
| m21 | Sr | far | 24 | 9.81 | 0 (ref.) | 0 (ref.) | — | — | +41.7 | +4.6 |
| m05 | Sr | hinge | 136 | 3.28 | +105.7 | +127.4 | +21.7 | −16.3 | +190.3 | +156.2 |
| m05 | Sr | flank | 124 | 3.27 | +116.1 | +152.1 | **+36.1** | −12.6 | +200.7 | +180.9 |
| m05 | Sr | mid | 48 | 7.37 | −35.0 | −32.2 | +2.8 | −14.0 | +49.6 | −3.4 |
| m05 | Sr | far | 112 | 9.71 | 0 (ref.) | 0 (ref.) | — | — | +84.6 | +28.8 |
| m30 | GA | near | 128 | 4.15 | +35.5 | −24.6 | **−60.0** | +2.3 | +15.1 | −30.2 |
| m30 | GA | mid | 212 | 7.93 | +42.3 | +29.0 | −13.3 | −4.2 | +21.9 | +23.4 |
| m30 | GA | far | 152 | 10.18 | 0 (ref.) | 0 (ref.) | — | — | −20.4 | −5.6 |
| m21 | GA | near | 128 | 4.44 | +36.3 | +57.7 | +21.5 | +1.2 | −24.5 | −3.3 |
| m21 | GA | mid | 104 | 7.78 | +27.7 | +53.8 | **+26.1** | +0.8 | −33.0 | −7.2 |
| m21 | GA | far | 4 | 10.17 | 0 (ref.) | 0 (ref.) | — | — | −60.7 | −61.0 |
| m05 | GA | near | 128 | 4.78 | −12.1 | +15.0 | **+27.1** | −0.5 | −13.6 | +16.0 |
| m05 | GA | mid | 40 | 8.06 | −45.4 | −31.5 | +13.8 | −0.5 | −46.8 | −30.5 |
| m05 | GA | far | 4 | 10.27 | 0 (ref.) | 0 (ref.) | — | — | −1.4 | +1.0 |

Bold: |MACE − DFT| ≥ 25 meV. Near-shell sign test: Sr agrees at 6/6 sites. GA disagrees in m30
(DFT +35.5, MACE −24.6) and m05 (DFT −12.1, MACE +15.0).

| | n sites | RMS(MACE − DFT) | mean | max | sites ≥ 25 meV | criterion 4 by host |
|---|---|---|---|---|---|---|
| Sr | 9 | 23.9 | +7.9 | 43.0 | 3 | m30 pass, m21 fail, m05 fail |
| GA | 6 | 31.2 | +2.5 | 60.0 | 3 | m30 fail, m21 fail, m05 fail |

## The finite-cell band term

- **Raw far-site values.** The raw DFT E_b at the far Sr sites is +44.9, +41.7 and +84.6 meV,
  against MACE +9.6, +4.6 and +28.8 meV. At those sites Sr raises the Fermi level of the
  neutral-vacancy cell by ΔE_F = E_F(D_j+V) − E_F(V) = +48.1, +43.0 and +58.0 meV.
- **Interpretation.** This is the term anticipated in amendment g item 1. The extra electron of
  V_I⁰ occupies a delocalised conduction-band-like state, and Sr shifts that band throughout the
  20-f.u. cell. WP2d confirms the attribution directly: removing the electron (q = +1) changes the
  raw E_b by 87–104% of ΔE_F (`WP2D_RESULT.md`). A local potential cannot represent this term, and
  it vanishes in the dilute limit. That is why criterion 4 is far-referenced.
- **Far-referencing removes most of it.** The band residual left after far-referencing is ≤ 5.4 meV
  at 11 of the 15 sites. The exceptions are m21 Sr mid (+23.3 meV) and the three m05 Sr sites
  (−12.6 to −16.3 meV). The m05 Sr far site carries a larger Fermi shift than the other m05 Sr sites (58.0
  against 41.7–45.4 meV), so every far-referenced m05 Sr value inherits roughly −14 meV.
- **Diagnostic only (amendment h item 2).** If the residual is assumed to enter E_b one-to-one, as
  WP2d supports, removing it changes the Sr errors to −6.8, +11.5, −6.9 (m30), +29.2, +21.8, −19.7
  (m21) and +5.4, +23.5, −11.2 (m05) meV. That is RMS 17.1 meV, with 1 site ≥ 25 meV (m21 hinge).
  The GA errors are unchanged (RMS 31.0 meV, 3 sites). This is not used to reclassify any site:
  criterion 4 fails either way, because GA fails with or without it.

## Limitations, stated with the result

- **One far site per host and dopant.** Its own MACE − DFT error enters every far-referenced value
  of that host (amendment h item 2). It is not corrected, and no DFT noise floor exists: WP1
  measured far-site scatter only at MACE level (SD 11.1 meV Sr, 28.3 meV GA). For GA that MACE
  scatter is already above the 25 meV tolerance. A single-site GA comparison at 25 meV therefore
  tests the noise of both levels as much as their agreement.
- **Fixed MACE geometry.** Each DFT value inherits MACE's choice of FA basin in every cell. The
  WP2e GA relaxation showed that DFT moves atoms by 0.28–0.39 Å on average in every distance shell,
  cell-wide (`WP2E_RESULT.md`). A relaxed DFT E_b does not exist here.
- **Neutral vacancy.** The charge-state test (WP2d) covers m30 only, at one near and one far site
  per dopant.

## What follows

- **Zero-shot MACE is not validated.** It has now failed criteria 3, 4 and 5, so S1 cannot accept
  zero-shot MACE-MP-0 for either ΔE_a or E_b at the pre-registered 20–25 meV level. The decision
  passes to WP3: does a fine-tuned potential pass criterion 6?
- **The qualitative Sr result stands at the fixed-geometry DFT level.** Sr next to the vacancy is
  repulsive by about 120 meV (mean of the 6 first-shell sites relative to each host's far site).
  At 298 K that corresponds to a suppression of exp(−0.119 eV / k_BT) ≈ 1/100, rather than the
  ≈ 1/250 implied by the MACE map (+141.7 meV, `WP1_RESULT.md`). The argument of `WP1_RESULT.md`
  — the corpus's nearest-site ΔE_a describes a rare configuration — is unchanged.
- **GA remains unclassified** at both levels.

Figure: `figures/fig_wp2c_eb_transfer.*` (a: far-referenced E_b, DFT against MACE, with the
±25 meV band; b: the error against dopant–vacancy distance, with the band-residual diagnostic;
c: the band-term test of WP2d).

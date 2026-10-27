# WP1 — dopant–vacancy binding map at MACE level (2026-10-27)

**Pre-registered verdicts (PLAN criteria 1 and 2; amendments c, d, g, h, i, j), zero-shot
MACE-MP-0 at the adopted depth fmax 0.01 eV/Å:**
- **Sr repels the iodide vacancy.** Criterion 1 passes (far rows n = 30: mean +11.0 meV, SD 11.1
  meV). Near − far = **+141.7 meV**, above 2 × far SD = 22.2 meV, same sign in 3/3 hosts, and above
  k_BT = 25.7 meV at 298 K.
- **GA: inconclusive below the noise floor.** Criterion 1 fails (rows with d > 8 Å, n = 28: mean
  +9.7 meV, SD **28.3 meV > 25**), so per PLAN criterion 1 WP1 is inconclusive for GA. Criterion 2,
  with the amendment-d far shell (d > 9 Å, n = 20, SD 28.2 meV): near − far = −18.6 meV, below
  2 × 28.2 = 56.4 meV, sign in 2/3 hosts: no resolved interaction.

These are MACE-level results. Zero-shot MACE failed the DFT barrier test (WP2b, criterion 3) and
its minima are not DFT minima (criterion 5); the E_b transfer to DFT is tested by WP2c
(criterion 4, running). Nothing here is yet a DFT statement.

## Method

Hosts m30, m21, m05 (the pilot hosts), every Pb site (Sr) and every FA site (GA): 20 + 19 sites
per host, 117 rows. Protocol v2.1 (`scripts/29`): D_j on the relaxed host, D_j+V on the relaxed V
(warm start); doped cells relaxed through fmax 0.02 → 0.01 (FIRE, cap 10000 steps per stage);
references (host, V) reused from the depth pilot at fmax 0.005 (`--ref-from`); every validity
check at every stage. E_b = E[D_j+V] − E[D_j] − E[V] + E[host] (positive = repulsion), taken at the
adopted stage 0.01 (`WP1_PILOT_RESULT.md`). Shells from the unrelaxed minimum-image distance
(amendment d): Sr near d < 5.0 Å (the two Pb flanking the vacancy), far d > 8.5 Å; GA near
d < 6.0 Å (three FA of the vacancy cage), far d > 9.0 Å. Analysis: `scripts/34 --mode map --fmax 0.01`.
Determinism check: the 30 production rows at the pilot sites reproduce the pilot's fmax-0.01
values exactly (max difference 0.0 meV, no validity mismatch).

## Results

| dopant | host | near mean | far median | far SD | near − far mean | n near / far |
|---|---|---|---|---|---|---|
| Sr | m30 | +125.9 | +8.7 | 11.4 | +113.4 | 2 / 10 |
| Sr | m21 | +163.6 | +7.5 | 8.7 | +152.6 | 2 / 10 |
| Sr | m05 | +168.6 | +8.1 | 13.7 | +159.0 | 2 / 10 |
| GA | m30 | +4.4 | +2.2 | 10.4 | +2.5 | 3 / 5 |
| GA | m21 | −26.3 | −3.9 | 25.0 | −17.4 | 3 / 8 |
| GA | m05 | −2.3 | +44.1 | 18.5 | −39.2 | 2 / 7 |

(meV; pooled: Sr near +152.7 / far +11.0; GA near −8.8 / far +9.8.)

- **Sr.** Both flanking Pb sites repel: +119.2 to +180.9 meV. The hinge Pb (holding the migrating
  iodide; Pb136 in all three hosts) and the far-side flank (Pb124) do not differ consistently
  (m30 132.5 vs 119.2; m21 165.1 vs 162.2; m05 156.2 vs 180.9 meV). In m30 the hinge label is a
  tie-break: the migrating iodide (4.285 Å from the vacancy site) beats the next iodide (4.327 Å,
  held by Pb124) by 0.04 Å; in m21 and m05 both candidates belong to Pb136. The m30 label carries
  into the WP2c/2d/2e site selections. Beyond the first shell the map is
  flat: mid shell (6.9–7.7 Å) n = 24, mean +11.2 meV (−3.5 to +33.1); far shell +11.0 ± 11.1 meV.
  The far plateau is positive because in this 233-atom cell (minimum-image radius 7.28 Å) every
  far site still sees periodic vacancy images (amendment c item 3); it is not an asymptotic zero.
  Relative to each host's far median the first-shell mean repulsion is +117 to +160 meV.
- **GA.** The near shell scatters from −49.9 to +36.8 meV, the mid shell has SD 24.4 meV, and the far
  medians differ by 48 meV between hosts (m05 +44.1, m21 −3.9). This scatter is not the
  stage-to-stage relaxation noise: across the 28 far rows the 0.02 → 0.01 change has RMS 8.6 meV
  while E_b at the two stages correlates with r = 0.95 (SD 26.0 and 28.3 meV), and the m05 offset is
  already present at 0.02. It is a persistent site- and host-specific variation whose origin
  (local basin selection on the FA landscape, or a real dependence on the local FA disorder) WP1
  cannot identify.
- **Invalid rows**: 11 of 117, all GA (near 1, mid 6, far 4), all failing the far-field basin check
  at 0.01 on displacement (> 0.25 Å) and none on rotation (≤ 15.6°): 4 clear excursions (m30 GA188
  0.45, GA104 0.55, GA80 0.64, GA68 0.71 Å) and 7 marginal (0.25–0.33 Å), the latter continuous with
  the valid rows (up to 0.247 Å). Excluded, never re-run (amendment d item 5).

Figure: `figures/fig_wp1_binding_map.*` (a: Sr; b: GA; c: per-host near − far against
±2 × pooled far SD; nature-figure QA: alignment and PDF-text audits pass; the collision audit's
six remaining warnings are the statistics text crossing the edge of the light far-shell tint,
reviewed and intended). Data: `wp1_production/` (shell JSONs with every per-stage record,
logs, `wp1_map.json`, `wp1_map_rows.csv`).

## What follows, and what does not

- If the Sr result survives the DFT tests (WP2c, and the charge-state check WP2d), a vacancy next to
  Sr is suppressed by
  exp(−0.142 eV / k_BT) ≈ 0.004 at 298 K relative to a distant one. The corpus measured the barrier
  of exactly that rare configuration (Sr on the Pb nearest the vacancy). Its ΔE_a therefore does not
  describe how Sr changes vacancy transport, which is set by the repulsion (each Sr excludes the
  vacancy from the 6 iodide sites of its octahedron, an excluded fraction ≈ 2x at B-site Sr
  fraction x) and by barriers out of the second shell. That is the reason the
  roadmap uses the binding map plus hop classes as its metric.
- GA cannot be classified at MACE level with this protocol. Lowering the noise needs the frozen-
  far-field construction recommended in `WP1_PILOT_RESULT.md`, or a potential whose minima are
  closer to DFT (WP3).
- Not shown: any DFT-level E_b (WP2c), the charge-state dependence (WP2d), transport rates, or
  anything about real films. The vacancy is MACE's charge-agnostic V_I; the charge question is WP2d.

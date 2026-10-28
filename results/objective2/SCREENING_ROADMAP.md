# Long-term goal: a validated multi-dopant screen for iodide-vacancy transport

**Adopted 2026-10-25 as the project's long-term final goal (PI decision).** Dated roadmap;
estimates are revised in place only by appending dated updates at the bottom.

## Goal

A screen of the proposal's dopant set (`proposal/proposal_v2.tex`, Objective 2: A-site,
B-site, X-site and interstitial additives in FA₀.₉₅Cs₀.₀₅PbI₃) that is (i) built on a
transport-relevant metric, (ii) validated against DFT at the energy scale it claims, and
(iii) statistically resolved over the host's orientational disorder.

## Metric (changed from the 108-path corpus)

Not "ΔE_a of the single hop nearest the dopant" (`scripts/22_paired_pilot.py`), which mixes
physically different sites and cannot see trapping. Per dopant:

1. dopant–vacancy binding map E_b(r) over every dopant site (`scripts/29_dopant_shell_scan.py`);
2. barriers of hops toward / around / away from the dopant for the shells where |E_b| matters;
3. from (1)+(2), an effective vacancy-transport change (trapping/repulsion), reported with its
   host-to-host spread.

## Stages and gates

| stage | content | gate to pass | estimate (as of 2026-10-25) |
|---|---|---|---|
| S1 | method validation on GA/Sr (`dopant_shell/PLAN.md`, WP1–WP3) | PLAN criteria 1–6; decides zero-shot MACE vs fine-tuned MACE | ~1 week |
| S2 | generalise the pipeline: builders for molecular A-site cations (DMA⁺, acetamidinium⁺; orientation sampling), X-site (Cl⁻, SCN⁻ with orientation), B-site (Ca²⁺ …), A-site Cs⁺/Rb⁺; automated binding map + hop classes on the node; per-element pseudopotentials | regression tests per builder; per-chemistry DFT spot checks | 1–2 weeks |
| S3 | pilot on 5 isovalent dopants | metric separates dopants beyond host noise; required hosts per dopant measured (current host noise suggests ≥ 10) | 3–5 days |
| S4a | full **isovalent** screen, ~15–20 dopants | per-dopant DFT spot checks within PLAN criterion 4 | 1–2 weeks of node time, ≈ ¥300–500 |
| S4b | **aliovalent** dopants (Bi³⁺, La³⁺, interstitial K⁺/Rb⁺) | a validated charge-compensation scheme (explicit defect complexes, charge-state-resolved MLIP, or DFT) chosen before any run | separate sub-project, +2–4 weeks |

Best case (S1 accepts zero-shot MACE; isovalent set only): ~3–4 weeks to a validated
15–20-dopant screen. Full set including aliovalent dopants: 6–8+ weeks.

## Standing constraints

MACE is charge-agnostic: no aliovalent dopant enters S4a. No metric value is compared across
theory levels (standing rule 1). Every stage keeps the paired, multi-host design and the
pre-registration discipline of `dopant_shell/PLAN.md`.

## Update 2026-10-27 — S1 status

| WP | status | result |
|---|---|---|
| 2a | done | single R-point k-sampling; degauss row fails (σ→0 reported beside F); nspin 1 |
| 2b | done | **criterion 3 fails** (paired ΔE_a RMS 31.2 meV > 20), **criterion 5 fails** at every MACE stationary point; corpus claim re-stated at DFT level, provisional (`dopant_shell/WP2B_RESULT.md`) |
| 1 | done (MACE) | **Sr repels the vacancy** (first shell +142 meV over the far plateau, 3/3 hosts); GA inconclusive (criterion 1 fails) (`WP1_RESULT.md`, `WP1_PILOT_RESULT.md`) |
| 2c / 2d | running | DFT E_b transfer (criterion 4, far-referenced) and q = +1 check |
| 2e | held (amendment k) | first DFT endpoint relaxation descended 977 meV by cell-wide FA reorientation; near/far partition pending |
| 3 | not started | inputs ready (`scripts/33`, `35`); needs WP2c data |

Consequences for the roadmap:
1. Zero-shot MACE has already failed two S1 gates (criteria 3 and 5), so S2 onwards cannot use it
   as is: either a fine-tuned potential that passes criteria 5 and 6 (WP3), or a protocol that
   does not depend on MACE minima being DFT minima.
2. The dominant methodological obstacle is the soft FA orientational landscape, not the dopant:
   relaxations descend 0.2–1 eV at both MACE and DFT level and far-field basin hops invalidate
   rows. The frozen-far-field construction (`WP1_PILOT_RESULT.md`) becomes the default for S2
   binding maps and must itself be tested at DFT level.
3. The metric change is supported: if Sr's +142 meV repulsion survives DFT, the corpus's
   nearest-hop ΔE_a describes a configuration suppressed ~250-fold at 298 K.
4. Estimate: S1 extends by about one week (WP2c/2d, the WP2e decision, WP3); best case to a
   validated 15–20-dopant isovalent screen is now ~5–6 weeks.

## Update 2026-10-28 — S1 status after WP2c/2d/2e

| WP | status | result |
|---|---|---|
| 2c | done | **criterion 4 fails**: 6 of 15 sites exceed 25 meV (far-referenced); GA near-shell sign disagrees in 2/3 hosts. Sr first-shell repulsion holds at DFT on MACE geometries (+96 to +137 meV); MACE overestimates it by +19 meV on average (`dopant_shell/WP2C_RESULT.md`) |
| 2d | done | far-referenced E_b charge-state robust at m30 (Sr −4.9, GA −2.9 meV); removing the electron changes raw E_b by 87–104% of the neutral-cell Fermi shift, consistent with the raw q = 0 offset being the extra electron's energy (post hoc); the Sr ΔE_a proxy differs by 43 meV between charge states, matching the band term (−39.7 meV) within 3–6 meV (`WP2D_RESULT.md`) |
| 2e | closed (amendment l) | uninformative in the pre-registered form: 81% of the −977 meV DFT relaxation energy lies beyond 6 Å of the defects; criterion 5 has no error bar; frozen-far-field relaxation proposed post hoc (`WP2E_RESULT.md`) |
| 3 | next | frames (`scripts/35`), DFT single points, fine-tune; criterion 6 and the adoption rule (criteria 3–5 thresholds, amendment m) on m30/m32 |

Consequences for the roadmap:
1. **Zero-shot MACE is not validated.** It fails criteria 3, 4 and 5, so S1 cannot accept it for
   ΔE_a or E_b at the 20–25 meV level. WP3 now decides whether S2–S4 run on a fine-tuned
   potential. Criterion 6 alone tests only improvement over zero-shot MACE; adoption for S2 also
   requires the thresholds of criteria 3–5 on the held-out hosts, as the 2026-10-27 update
   (consequence 1) already required, to be fixed in amendment m before WP3. If WP3 also fails, the screen needs either DFT for the decisive
   quantities or a coarser, dopant-ranking metric whose tolerance matches the errors measured here.
2. **Neutral 20-f.u. cells carry a band term.** It is a dopant-dependent energy of the vacancy's
   extra electron: the Fermi-level shift is 13–66 meV, entering raw E_b nearly one-to-one where
   tested (m30), and
   ~40 meV in one paired ΔE_a. S2 onwards should compute
   barrier and binding differences for V_I⁺ or far-referenced, and never compare raw neutral-cell
   E_b with a local potential.
3. **A frozen-far-field protocol is proposed at both levels.** The soft FA landscape is the main
   obstacle at both MACE and DFT level: the DFT relaxation spreads its energy over the whole cell.
   Its DFT-level test (WP2e′, 7 relaxations) ranks below the WP3 single points; whether and when
   it runs will be fixed by a later amendment (amendment l item 4).
4. **Estimate.** S1 now ends with WP3, about 1 week of node time (frames, ~100 single points,
   fine-tuning, re-evaluation). Best case to a validated isovalent screen is unchanged at ~5–6
   weeks, conditional on the fine-tuned potential passing the adoption rule. That estimate excludes
   WP2e′: 7 DFT relaxations, where the one full relaxation run so far took more than a day on the
   node.

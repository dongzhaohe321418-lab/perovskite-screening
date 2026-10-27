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

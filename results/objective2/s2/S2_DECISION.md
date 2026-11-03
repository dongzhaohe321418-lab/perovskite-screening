# S2 decision (2026-11-03): route, staged plan and validation standard

**Status: decision record, written 2026-11-03 before any S2 energy value (MACE or DFT) existed.**
It records a decision and the reasons for it. Every rule it relies on is in `S2_PLAN.md`, the S2
pre-registration, which becomes binding with PLAN amendment n (`dopant_shell/PLAN.md`, "Amendment
2026-11-03n") at the commit that adds both. Where this memo and `S2_PLAN.md` differ, `S2_PLAN.md`
governs. Until that commit no S2 cell is evaluated with any calculator. It was revised the same day,
before the commit and before any S2 value, after three reviews, the analyst's decisions on their
open issues and a review of those decisions (`S2_PLAN.md` §20).

**Who decided.** `SCREENING_ROADMAP.md`, update 2026-11-03, item 4 ("The choice is the PI's") left
the S2 route to the PI. **On 2026-11-03 the PI delegated the choice of research direction to the
analyst (an AI assistant) and approved everything else**, including the Cl/S/Ca/Rb pslibrary
download (`PSEUDOPOTENTIALS_S2.md`). This memo is that choice. It was prepared by a panel (three
proposals with science, rigour and cost lenses, two judges, a refuter and a synthesis), and the
analyst adopted the synthesis. The panel notes are kept off-repository in the private record folder.

Tags: **[R]** measured or recorded in the repository (path, section); **[M]** modelling choice;
**[I]** interpretation or estimate; **[MC]** Monte Carlo under stated assumptions (`S2_PLAN.md` §18),
not a measurement; **[S]** secondary source.

## 1. Decision in brief

- **Route: option D = A1 decides, A2 calibrates.**
  - Every per-host decisive value Y_h is a **PBE single point (A1)** quantity on a zero-shot
    MACE-MP-0 geometry relaxed with the far field frozen. MACE supplies geometries only; none of its
    energies enters a decision.
  - A **frozen-far-field DFT relaxation (A2, the WP2e′ design of PLAN amendment l item 4)** of one
    first-shell quartet per sublattice, on **two pilot hosts**, measures the relaxation bias
    δ = E_b(A2) − E_b(A1). The validated class rests on θ̂ = Ȳ + δ̄, which adds this calibration to
    the A1 mean; the decisive interval combines both.
  - **B** is kept only as a reported ledger (zero-shot MACE E_b on the same cells). **No C, no A3,
    no ΔE_a** in S2.
- **Question.** For Ca (B site), Cl (X site), Cs and GA (A site), does the dopant bind or repel
  V_I⁺ in its first shell, relative to two far sites, by more than k_BT = 25.7 meV (PLAN criterion 2)?
  Sr is the positive control.
- **Order.** A cheap DFT noise-floor pilot first; then A2 kill gates on the control; then A1
  production; then the rest of the calibration. Four node campaigns, with the node stopped after
  each.
- **Cost [I].** About **449 node-h** (360–663 before the cap; **hard cap 520 node-h**), with no
  allowance for interruptions. Calendar about 3–5 weeks from the stage durations of §8
  (20–35.5 days), longer if campaigns wait for a console login [I].
- **What S2 can deliver [MC].** A validated class for effects of about **43–79 meV** (1.7–3.1 k_BT),
  depending on the measured relaxation-bias noise, with no site-type offset of the calibration
  sites (§10). Smaller effects are reported with an upper
  bound, not a class. S2 absorbs roadmap stage S3 (the 5-dopant pilot) and measures the hosts each
  dopant needs.

## 2. Evidence that fixes the route

**Measured [R].**
- **Zero-shot MACE energies are out.** It fails criteria 3, 4 and 5 (`dopant_shell/WP2B_RESULT.md`;
  `dopant_shell/WP2C_RESULT.md`), and amendment m item 4 (Outcomes) does not re-admit it after WP3.
- **No validated potential exists.** WP3 outcome "No improvement"; all of (a)–(e) fail. The
  fine-tuned m30 Sr hinge E_b is +11.6 meV against +129.4 meV at DFT, and the far-referenced E_b RMS
  rose from 28.4 to 69.4 meV while the force RMSE fell 5.8-fold (`dopant_shell/WP3_RESULT.md` §1;
  roadmap update 2026-11-03).
- **The DFT signal is large where it exists.** Sr first-shell E_b at fixed-geometry DFT (WP1 MACE
  minima, q = 0, one far site per host) is +95.6 to +136.7 meV at 6 sites on 3 hosts; host means
  112.5, 134.2 and 110.9 meV (SD 13.0) (`WP2C_RESULT.md`, Results).
- **Far-referenced E_b is charge-robust.** q = +1 minus q = 0 is −4.9 meV (Sr) and −2.9 meV (GA) at
  m30 (`WP2D_RESULT.md`). That q = +1 removes the 13–66 meV band term (roadmap update 2026-10-28,
  consequence 2) is supported by the post hoc WP2d diagnostic at m30 only [I]; q = +1 cells are
  gapped, so the failed degauss row (`WP2B_RESULT.md` §6) does not apply.
- **A1 has no relaxation error bar.** The DFT residual force at the WP2c MACE minima is RMS
  0.12–0.15 and max 0.28–0.36 eV/Å (`WP2C_RESULT.md`); WP2e closed without an error bar
  (amendment l item 3).
- **Whole-cell DFT relaxation is unusable.** 282 BFGS steps, 29.0 h wall at 48 ranks, −977 meV with
  81% of it beyond 6 Å (`WP2E_RESULT.md`; `dopant_shell/wp2e/relax_m30_GA_img0.out.gz`).
- **Unit costs.** 6.74 min per 233-atom single point (153 in 17.19 h at 64 ranks,
  `dopant_shell/wp3/run2/node_logs/step2.log`); 6.15 min per DFT ionic step (WP2e, 283 SCF cycles in
  29.0 h); MACE 0.56–1.0 s per call (`dopant_shell/WP3_RUNBOOK.md`, node drivers); frozen-region
  MACE relaxations 17–27 min at 6 threads, 10 concurrent (`WP3_RESULT.md` §5, fine-tuned model).

**Interpretation [I].**
- DFT must produce every decisive number; MACE can at most supply geometries. That is the remaining
  route named in roadmap update 2026-10-27, consequence 1 ("a protocol that does not depend on MACE
  minima being DFT minima"), provided the geometry dependence is measured, not assumed.
- Binding comes first: a dopant changes long-range V_I transport mainly by trapping or repelling it
  (PLAN "Why"; `WP1_RESULT.md`, "What follows"). Barriers matter only for dopants that bind.

## 3. What was rejected, and why

| option or choice | reason | evidence |
|---|---|---|
| **B as the decisive metric** | Re-admits zero-shot MACE energies after they failed criteria 3–5. Errors are measured only for Sr and GA (largest 60.0 meV; Sr +19.2 meV mean bias), so for Ca or Cl no "matched tolerance" exists without the same per-chemistry DFT that A1 spends. A matched tolerance (≥ 60 meV) resolves only Sr-size effects. | amendment m item 4 (Outcomes); `WP2C_RESULT.md`; roadmap update 2026-11-03, item 3 B |
| **C (new fine-tune)** | The cause of the WP3 failure is untested (`WP3_RESULT.md` §8; reason 1 the most consistent); D1–D3 are post hoc and change nothing. A model covers only H, C, N, Sr, I, Cs and Pb, so Cl and Ca need DFT anyway. WP3 itself cost about 39 node-h of measured work (5.8 + 17.2 + 7.6 + 0.85 + 7.2 h) plus 7.9 h lost to a discarded run [R]; a retry reusing its frames would cost less, with an unknown pass probability [I]. Kept open for later, with S2's ~800 single points and the A2 trajectories as data and ≥ 13 DFT-free hosts preserved. | `WP3_RESULT.md` §8; `WP3_DIAGNOSTICS.md` §§3, 4, 10; roadmap update 2026-11-03, item 3 C |
| **A3 (NEB)** | No cost basis in the repository; barriers are second-order for the S2 question. Deferred to S3, only for dopants classified "binds". | roadmap update 2026-11-03, item 3 A3 |
| **A2 on every cell** | 36 relaxations on two hosts already cost about 330 node-h [I]; all production cells would need thousands. | §8 |
| **A1 alone** | No relaxation error bar, so no validated claim. Kept as the reported "A1 tier". | `WP2C_RESULT.md`; amendment l |
| q = 0 decisive (Proposal 3) | Far-referenced q = 0 keeps band residuals up to +23.3 meV (m21 Sr mid) and −12.6 to −16.3 meV (m05 Sr); the degauss row failed. | `WP2C_RESULT.md`, band term; `WP2B_RESULT.md` §6 |
| T = 60 meV and a "no effect" band ±(60 − b) (Proposal 3) | Set from MACE errors and the ΔE_a band, not from DFT E_b errors; abandons criterion 2's k_BT; can call a 2 k_BT binder "no effect". | PLAN criteria 2–3 |
| MACE-energy pose pre-selection; Stage 3b host top-up (Proposal 3) | MACE energy in a decision; optional stopping without alpha spending. | amendment m item 4 |
| A fixed 15 meV bias allowance (Proposal 1) | 15 meV is a MACE stage-to-stage shift, not a DFT relaxation bias; one quartet per dopant cannot bound a bias (refuter's Monte Carlo: the proposed gate passes with probability 0.55 at zero bias and 0.21 at +30 meV, δ SD 20 meV). | `WP1_PILOT_RESULT.md`, Gate (5–15 meV stage uncertainty) |
| Near and far legs with different free regions (Proposal 1) | Leaves a region-size term in every far-referenced value. | judges 1–2; refuter objection 6 |
| Linear sum of worst-case bias terms on one host (Proposal 2) | Power collapses: at δ SD 20 meV the median allowance is 70 meV and Sr is classified "repels" only 39% of the time. | refuter's Monte Carlo |
| Rb decisive (Proposal 2) | Hypothetical: t = 0.818 / 0.858 < 0.875; not incorporated experimentally [S]. | `S2_BUILDERS_DESIGN.md` §10 |
| Move the whole campaign to a higher cutoff if one element fails G1 (judges) | At 60/480 Ry this adds about a third to the node-hours [I: plane-wave count ∝ E_cut^1.5]. A failing element leaves S2 instead and may return under its own amendment. Standing rule 1 forbids cross-level comparison, not a new fingerprint; the reason here is cost. | roadmap, "Standing constraints" |
| DMA, AA, SCN in S2 | Starts not yet physical: 116 of 141 m30 DMA starts lack an N–H···I contact; AA `inherit` clashes at 15 of 19 m30 sites; SCN has no admissible start at I49 or I138. | `S2_BUILDERS_DESIGN.md` §10 |

## 4. The refuter's objections and how they are handled

| # | objection (severity) | handling (rule in `S2_PLAN.md`) | residual risk |
|---|---|---|---|
| 1 | One A2 quartet per dopant on one host does not bound the bias (**fatal as written**) | A2 on **two hosts** (m30, m05) for every decisive dopant. The bias is *estimated and corrected*, θ̂ = Ȳ + δ̄, with its own variance from the between-host SD of δ (the calibration sites differ between the two hosts, so site is confounded with host) pooled over dopants (df up to 5), combined with host noise by Welch–Satterthwaite. No linear stacking. Claims are limited to the resolution this supports (§10). (§§11, 14) | The pooled SD assumes similar δ noise across chemistries; df ≤ 5 gives wide t. Dopants that share a calibration region share relaxation terms, so the effective df is lower. δ is measured at one first-shell site per sublattice on each pilot host, at different sites on the two hosts (B: Pb136 on m30, Pb124 on m05, the whole B shell; A: FA128 and the drawn FA28; X: the migrating iodide I138 and the drawn I49), so a site-type effect enters s_δ, confounded with host, and is halved in δ̄ (if the drawn site carries the shell-mean δ) but not removed (`S2_PLAN.md` §11; §18, assumptions (i) and (ii)). |
| 2 | DFT noise floor unmeasured; production starts first (**fatal if high; cheap to test**) | **Noise pilot first** (campaign 1): 4 far sites per sublattice × 5 dopants × 2 pilot hosts, 106 single points (about 12 node-h). It gates each dopant (σ_far ≤ 25 meV) and fixes n (8 or 10) before any production cell is computed. The first-shell pilot cells of the same campaign (pose pilot at FA128 and I138, step-0 and q = 0 rows on m30) allow some first-shell E_b on m30 to be formed; they never enter Ȳ, and the pose pilot enters only through a_pose (`S2_PLAN.md` §9). (§8) | Far-site scatter is a proxy for, not the whole of, host-to-host spread. |
| 3 | The shell mean dilutes trapping (**serious**) | The first-shell sites of each sublattice are one orbit of the cubic aristotype (8 X, 4 A, 2 B neighbours of an X site), so the mean is the right estimator of the disorder-averaged interaction [I]. Per-site host means and the Boltzmann aggregate are reported; if they differ by > k_BT the shell is flagged "heterogeneous" and gets no class. "No first-shell interaction beyond k_BT" also requires the Boltzmann shell value G_d > −k_BT, so a shallower single-site trap (one X site at −80 meV is not flagged) cannot receive it. (§14) | A trap at one site in one host is not detectable at n = 8. |
| 4 | m30 is the least representative host (**fixable**) | Second pilot host **m05**, which carries the systematic zero-shot Sr overestimate (+21.7, +36.1 meV) that m30 lacks. Pilot-host E_b values never enter Ȳ; δ, a_pose, a_far and σ_far measured on them enter the decisive rules (`S2_PLAN.md` §§8, 9, 11, 14). (§3) | Two hosts are still two. |
| 5 | Charge state leaves a systematic either way (**serious**) | The target is defined as V_I⁺. A2 relaxes vacancy cells at q = +1, so δ includes the charged-cell relaxation that MACE cannot model; this is a correction, not an error. q = 0 link rows are reported. (§§1, 10) | Whether V_I⁺ is the transport-relevant state is not tested (`WP2D_RESULT.md`). |
| 6 | Inconsistent free regions (**fixable**) | Proposal 2's construction: per site j one region R_j = S(v, 6 Å) ∪ S(j, 6 Å), whole molecules; V⁺ and the dopant cells relaxed in R_j; one frozen far field (the relaxed host) for all cells. (§4) | — |
| 7 | Force residuals do not predict energy-difference errors (**fatal to Proposal 3**) | No force-based trigger. δ is measured for every decisive chemistry. | — |
| 8 | Every host has the native Cs next to the vacancy (**fatal to an unqualified claim**) | Every value is labelled "**Cs-adjacent V_I⁺**". The Cs lies 4.04–5.13 Å from the vacancy site in all 36 members [R]. A Cs-distal vacancy check (Sr and any classified dopant) is an S3 item; it needs new vacancy references in the code. (§3) | S2 says nothing about vacancies without a Cs neighbour: about 81% of them at 5% Cs on the A sites (0.95⁴, four A neighbours per X site) [I]. |
| 9 | Basin hops inside the free region go undetected (**fixable**) | Fail-closed partner check: atoms more than 6.0 Å from the defect added in a step keep < 0.25 Å displacement and, for FA, < 20° rotation against the parent cell, at A1 and A2. (§5) | Genuine reorientation within 6 Å is reported, not gated. |
| 10 | Spot reclaims change the relaxation path (**fixable**) | QE soft exit with restart files keeps the BFGS history; otherwise rerun from the start with identical input, ≤ 2 times; every interruption logged; partial outputs unread. (§13) | Restarted SCF guesses differ slightly [I]. |
| 11 | Conformance: optional stopping, tuned threshold, MACE energies, known values, unreachable class, wording, prerequisites | No hosts added after values exist; k_BT kept; no MACE energy in any decision; m21 and the pilot hosts excluded from the decisive draw; "below k_BT" kept, but unresolved dopants also get an upper bound U; "8 I below the 5.12–5.48 Å gap"; the hard-coded assumptions of `S2_BUILDERS_DESIGN.md` §11 fixed in Stage 0. | — |
| 12 | Cost and scope (**minor**) | A2 step counts are capped (200) with a plateau rule and a kill gate on the first relaxation. S2 delivers a binding classification, not transport rates. The fixed zero-shot MACE-MP-0 lattice (a_pc 6.512 Å, about 2.4% above experiment; not relaxed at PBE; `results/fa_host/REPORT_fa_baseline.md`) and missing SOC are labelled; a D3(BJ) single-point correction is reported (laptop). | Cl and Ca may be over-strained by the expanded lattice [I]. |

## 5. What S2 measures

- **Dopants.** Control Sr. Decisive family {Ca, Cl, Cs, GA} (Bonferroni m = 4). Deferred: Rb, DMA,
  AA, SCN (§3). GA stays for continuity with S1 and to test whether the frozen far field cures its
  S1 noise (`WP1_RESULT.md`, "What follows").
- **Hosts.**
  - Pilot hosts m30 and m05 (noise, pose and calibration pilots). Chosen, not drawn: m30 for WP2c/2d
    continuity, m05 for coverage of the zero-shot error regime (amendment m item 5, Coverage).
    Disclosed; their E_b values never enter Ȳ, but the quantities measured on them do
    (`S2_PLAN.md` §14).
  - Calibration sites (`S2_PLAN.md` §11): Pb136, FA128 and the migrating iodide I138 on m30; Pb124
    (the other first-shell Pb), FA28 and I49 on m05, the last two drawn by a seeded rule executed
    once before any S2 value existed.
  - Production: n = 8 (10 if the noise pilot says so), drawn by a seeded rule from 28 eligible
    members: all 36 minus the pilots, minus the item-1′ hosts m04, m10, m14, m18 and m27 (amendment m
    item 1′, "Isolation"), minus m21 (WP2c E_b known; WP3 checkpoint selection). Two reserves.
  - With the seed string `S2n-host-<member>` the rule gives m06, m02, m16, m12, m32, m26, m22, m23
    (reserves m33, m13), leaving 15 DFT-free hosts for any later C (13 if n = 10). The draw was
    re-executed and is recorded with its crc32 values in `S2_PLAN.md` §3 [R].
  - m32 is a WP3 test host. It is "used up" for validating a model, not for measuring DFT
    (amendment n item 3).
- **Sites** (true MIC, unrelaxed host): first shell B = the 2 flanking Pb (d < 5.0 Å); A = the 3 FA
  of the vacancy cage (d < 6.0 Å; the fourth A site is the native Cs); X = the 8 I below the
  5.12–5.48 Å gap, including the migrating iodide (`mig="allow"`). Far: the 2 farthest sites of the
  sublattice. 19 regions and 76 single points per host.
- **Quantity.** Per host h and dopant d: Y_h = mean over first-shell j of E_b(j) − mean over the two
  far sites, with E_b(j) = F[D_j+V]⁺ − F[D_j] − F[V⁺ in R_j] + F[host].

## 6. Energy level and error control for each decisive quantity

| quantity | level | error terms and how each is controlled |
|---|---|---|
| Y_d = mean_h Y_h (A1 tier) | PBE (`scripts/30` fingerprint + Cl, Ca UPFs), V_I⁺, single points on MACE frozen-far-field geometries | host noise: t over n hosts, Bonferroni m = 4; sign in ≥ ¾ of hosts; noise-floor gate; fail-closed validity; elements gate G1 |
| δ̄_d (calibration) | A2 − A1 on one near quartet per sublattice per pilot host, A1 = configuration 0 of the same relaxation | between-host SD of δ, site confounded with host, pooled over dopants (df ≤ 5); far-site bias tested once (Sr, m30) |
| θ̂_d = Y_d + δ̄_d (**validated tier**) | "frozen-far-field DFT-relaxed E_b, estimated" | SE² = s_Y²/n_d + s_δ²/m_d; Welch–Satterthwaite df; controls C1–C5 |
| pose term | per-leg Boltzmann (298 K) or default pose | m30 pose-pilot rule (≤ 10 meV at each site); the larger of the measured residuals and their difference added as an allowance when the default is kept |
| noise floor σ_far,d | A1 on 4 far sites × 2 pilot hosts | gate σ_far ≤ 25 meV (criterion-1 analogue); sets n |
| element settings | 50/400 vs 60/480 Ry; nspin 2 | ≤ 5 meV; ΔF ≤ 3 meV and \|M\| < 0.1 μB |

A1 and A2 values are never pooled as one distribution (`CURRENT_STATUS.md`, standing prohibitions);
the calibrated value is a defined estimator, labelled as such.

## 7. What "validated" means in S2

- **Validated class** (the only S2 output that may be called validated): for dopant d, "repels",
  "binds" or "no first-shell interaction beyond k_BT" (the last also with the Boltzmann shell value
  G_d > −k_BT), decided by rule V on the calibrated interval θ̂_d ± (t*·SE_d + allowances), with all
  of C1–C5 passing, no heterogeneity flag and no dopant-specific failure rule applying
  (`S2_PLAN.md` §§12, 14):
  - C1 Sr comes out "repels" (else no dopant gets a validated class);
  - C2 noise-floor and far-pair checks pass for d;
  - C3 G1 passes for d's element;
  - C4 valid Y_h in ≥ n − 1 hosts;
  - C5 d is calibrated (≥ 1 valid A2 quartet, pooled df ≥ 3, |δ̄_d| ≤ 50 meV).
- **It validates a class, not a value.** Values are reported as θ̂ with their interval.
- **Label.** "PBE (no D3, no SOC), V_I⁺ adjacent to the native Cs, first-shell mean relative to two
  far sites in a 233-atom FA19Cs1Pb20I60 cell, frozen-far-field (6 Å) DFT-relaxed level estimated
  from fixed-geometry DFT on zero-shot MACE geometries over n hosts with a two-host relaxation
  calibration, calibrated at one first-shell site per sublattice on each of two chosen pilot hosts,
  the sites differing between the two hosts; spans FA orientational disorder at one vacancy site."
  A multi-pose dopant adds "calibration at the default pose" (`S2_PLAN.md` §11).
- **A1 tier** (reported, pre-registered, not "validated"): the same rule on Y_d without
  calibration, labelled "fixed-geometry DFT; relaxation bias not bounded".
- **Not claimed.** Relaxed DFT minima, barriers, ΔE_a, dilute-limit or Cs-distal values, transport
  rates, anything about experiment, aliovalent dopants.

## 8. Staged plan, gates and node-hours

**Unit costs** [R]: single point 6.74 min (64 ranks); DFT ionic step 6.15 min (48 ranks). [I]: A2
needs 64–140 BFGS steps (the WP3b frozen/unconstrained FIRE step ratio 0.23–0.50 transferred to
WP2e's 282 steps; the cap is 200 steps), i.e. 65–141 configurations or 6.7–14.5 h per relaxation,
median 9.1 h, at most 20.6 h at the cap; a frozen-region MACE relaxation costs about 2 min of
node time (20 min at 6 threads, 10 concurrent); a whole-cell host relaxation takes 1.6–3.3 h wall
(WP1 production references [R]) and lies on the critical path of C1 and C3.

| stage | content | node-h (arithmetic) | gate |
|---|---|---|---|
| S2-0 (laptop, 3–4 d) | commit `S2_PLAN.md` + amendment n; drivers, QE writer, analysis script with planted-effect self-test; T4 report archived and `s2b-2` frozen; host and m05 calibration-cell admissibility checked; Pb–Cl source check; MACE file hash; pre-flight (dry-run builds of every campaign-1 cell) | 0 | review; every input built |
| **C1** pilots (1–1.5 d) | UPF sha256 on the node; pw.x smoke tests on the reference cell (nstep cap, exit file, restart; 1.0 h); cutoff check 5 single points (0.7 h); nspin-2 row 2 × 2 (0.45 h); QE throughput row 1.5 h; step-0 single points 0.2 h; **noise pilot** 2 × (1 + 12 + 40) = 106 single points (11.9 h); **pose pilot** ≤ 40 (4.5 h); q = 0 link rows 10 (1.1 h); MACE about 170 frozen relaxations (5.7 h) and 2 host relaxations (1.7 h) | **≈ 29** | G1; gate N (dopants, n); pose rule |
| **C2** A2-I on m30 (3–6 d) | V⁺_R(hinge) [K2], host_R, Sr D, Sr D+V [cost projection]; Sr far quartet [K3]; Ca D, D+V. 10 × 6.7–14.5 h | **≈ 91** (67–145) | step-0 check, K2, K3 |
| **C3** A1 production (4–5 d) | 8 × 76 = 608 single points × 6.74 min = 68.3 h; MACE 8 × 75 × 2 min = 20 h plus the host relaxations (≤ 3.3 h) = 23.3 h. n = 10: 760 single points = 85.4 h + 28.3 h | **≈ 92** (n = 10: 114) | validity; C4 |
| **C4** A2-II (7–16 d) | m30 X (4) + A (6); m05 B (6) + X (4) + A (6): 26 × 6.7–14.5 h | **≈ 237** (173–376) | C5; separability |
| S2-5 (laptop, 2–3 d) | one evaluation; adversarial check; S2 result note; roadmap update | 0 | rule V |
| **total** | | **≈ 449** (360–663; capped at 520) | |

The upper ends exceed the 520 node-h hard cap, so the cut order below applies. No allowance for
interruptions is included: a node loss during an A2 relaxation costs up to 20.6 h, and each spot
reclaim needs a console restart (`S2_PLAN.md` §16).

- **Order of cuts if the projection (after the first 4 A2 relaxations, and again at the start of C3
  and of C4) exceeds 520 h:** GA on m05; then Cs and the A region on m05; then GA on m30; then Cs
  and the A region on m30. Sr, Ca and Cl on both hosts (24 relaxations) are protected. A dopant
  losing a host is calibrated with m_d = 1; one losing both stays at the A1 tier. `S2_PLAN.md` §16
  adds the cuts that apply if these four are not enough (n = 10 → 8, then the multi-pose production
  of Cs and Cl, both only before C3 starts; then C4 is not run, which ends the validated tier); with
  the protected relaxations alone, the n = 8 total is 280–467 h. With cuts 1–4 applied df_δ = 3
  exactly, so one invalid protected quartet ends the validated tier.
- **Comparison** (panel estimates [I]). Proposal 1 ≈ 195 h, Proposal 2 ≈ 290 h, Proposal 3 ≈ 106 h
  (midpoint 125–135 h once its omitted stage is counted), the judges' grafted route ≈ 280 h. The
  increment buys the second calibration host (≈ 146 h, the only way to estimate a between-host bias
  variance) and the noise pilot (≈ 12 h).
- **Possible saving [I].** If the C1 throughput row shows ≥ 15% more configurations per node-hour at
  64 ranks or as two 32-rank jobs, A2 time falls accordingly; no saving is assumed.

## 9. Stopping rules (all fail-closed)

- **K1 (G1).** An element that fails leaves S2's decisive family; no setting is changed to rescue it.
- **Gate N.** σ_far,d > 25 meV → d is "inconclusive below the DFT noise floor" (reported only). If
  Sr itself exceeds 25 meV the protocol stops before A2 and is re-planned.
- **K2.** The first A2 relaxation (m30 V⁺ in the hinge region) is not accepted by the end rule
  (it reaches configuration 200 without a plateau, |F(200) − F(180)| ≤ 3 meV, or ends earlier
  without convergence) → A2 stops; S2 delivers the A1 tier only; any further A2 needs a new
  amendment.
- **K3.** The relaxed, far-referenced m30 Sr hinge E_b is not > +25.7 meV, or a quartet it needs is
  invalid by validity checks 2–5 → A1 is not admissible as a proxy; A2 and production stop and S2
  is re-planned. If a quartet is invalid only by the end rule, K3 cannot be evaluated: A2 stops, C3
  runs, and S2 delivers the A1 tier only, as under K2.
- **Budget.** Hard cap 520 node-h, enforced by the cut order above.
- **No optional stopping.** No host or site is added after any value exists; reserves replace a host,
  and the next m05 calibration site in draw order replaces a drawn one (`S2_PLAN.md` §11), only if
  a required cell cannot be built, before any calculator runs on it. Invalid cells are never rerun
  with other settings.
- **Blinding.** The analysis script is committed before C3 and run once after C4; until then
  production and A2-II values are read only for completeness and validity, and no E_b (DFT or
  zero-shot MACE) of them is computed.

## 10. Power: what S2 can and cannot resolve [MC]

Class threshold |θ| (true value) for a 50%-power call (analytic; n = 8, two calibration hosts,
pooled df 5, Bonferroni m = 4; `S2_PLAN.md` §18):

| s_Y \ s_δ | 5 meV | 10 meV | 15 meV | 20 meV |
|---|---|---|---|---|
| 13 meV | 43 | 52 | 64 | 78 |
| 20 meV | 50 | 55 | 65 | 77 |
| 30 meV | 61 | 63 | 70 | 79 |

- Planning values: s_Y 13 meV is the DFT Sr host-mean SD (WP2c); s_δ is unknown. The WP3b DFT
  dopant − undoped relaxation-energy differences at fine-tuned frozen minima (RMS 15.0 meV) suggest
  10–20 meV [I]; they measure only the vacancy-cell half of δ, so s_δ up to about 21 meV is equally
  consistent with them. At s_δ = 25 / 30 meV the threshold (s_Y 13) is 91 / 105 meV
  (`S2_PLAN.md` §18).
- **Sr control** is classified "repels" with probability ≥ 0.95 for s_δ ≤ 20 meV under rule V alone
  (against 0.39 for Proposal 2's rule and 0.54 for Proposal 1's under comparable assumptions;
  refuter's Monte Carlo); with gate N and C2, which C1 also requires, about 0.9 at σ_far = 15 meV
  and 0.6 at 20 meV (`S2_PLAN.md` §18).
- **A −75 meV binder** is called "binds" with probability 0.99 / 0.92 / 0.71 / 0.46 at s_δ = 5 / 10 /
  15 / 20 meV; a −50 meV binder only 0.52 / 0.30 / 0.16 / 0.10.
- **No false class** occurred at θ = 0 in 6000 draws per case; a dopant-specific bias of +20 meV is
  removed by the calibration.
- n = 10 instead of 8 changes the thresholds by −5.2 to +0.2 meV; the calibration term dominates.
- **Consequence.** S2 can validate effects of about 2–3 k_BT. "No interaction beyond k_BT" is
  reachable only if s_Y and s_δ are both small (probability 0.95 at s_Y = 8 and s_δ = 5 meV, 0.27 at
  s_δ = 10 meV). Every unresolved dopant is reported with its upper bound U.
- **Assumptions behind these numbers.** Independent normal errors; the same δ noise for all
  chemistries; the random part of the shell-level δ bounded by the single-site noise of the
  calibration site. Untested and not fully inside s_δ: (i) the calibration sites have the
  shell-mean δ of their sublattice (both first-shell Pb are calibrated, one per pilot host; for A
  and X the m30 site, the nearest FA or the migrating iodide, and the drawn m05 site differ in type,
  so a site-type effect enters s_δ, confounded with host, and is halved in δ̄ if the drawn site
  carries the shell-mean δ) and (ii) the two chosen pilot hosts have the δ of the production hosts.
  A systematic offset of 10 or 20 meV at the m30-type A and X sites then gives a coverage of the
  nominal 98.75% interval of 0.98–0.99 for Cl and Cs (0.96–0.98 in the least favourable reading),
  against 0.93–0.97 / 0.70–0.92 had the same kind of site been used on both hosts (as it would be
  again if the drawn site carried the same offset). The offset costs mainly power instead, which
  the thresholds above do not include: at s* = 20 meV, Sr "repels" with probability 0.92 instead
  of 0.96 at s_δ = 20 meV, and a −75 meV Cl binder "binds" with 0.51 instead of 0.93 at
  s_δ = 10 meV when the shift of δ̄ points towards zero. Without an offset, shared region terms
  between dopants lower the coverage to 0.973–0.985 in the worst case tested, which bounds the
  familywise error by about 11% rather than 5% (`S2_PLAN.md` §18).

## 11. Main open risks and triggers for a change of route

- **A2 cost or convergence (main risk).** Step counts are extrapolated. The free regions hold 48–71
  atoms at first-shell sites and 62–109 at far sites (m30 Pb76, the Sr far quartet: 100–107),
  against 81–83 in WP3b [R, geometry census of the unrelaxed members and of the WP1-relaxed m30 and
  m05 hosts; the S2-relaxed hosts do not exist yet]. The end-rule risk is reduced by the cap of 200
  steps (analyst decision D2, `S2_PLAN.md` §20): under a lognormal fit to the WP3b step ratios, a
  relaxation needs more than 200 steps with probability about 0.0012 (more than 120: 0.12), so the
  eight relaxations that K3 needs are all accepted without the plateau with probability about 0.99
  at the fitted parameters (0.35 at the former cap of 120); about 0.91–0.96 if each region is
  scaled by its free-atom ratio (the four far-quartet relaxations at Pb76, the largest region, at
  most about 0.02 each), and about 0.79–0.89 when the uncertainty of the six-point fit is also
  included [I]. What remains: these estimates rest on the unverified transfer of FIRE step ratios
  to BFGS; in WP2e F still fell by 16.3 meV over configurations 180–200 (whole cell) and never met
  the 3 meV plateau before it converged at configuration 282 [R], so a relaxation that reaches the
  cap will usually fail the plateau [I]; and a long relaxation costs up to 20.6 h, so the upper end
  of the plan (641 node-h at n = 8) exceeds the hard cap and relies on the cut order. K2, K3
  (which delivers the A1 tier on an end-rule failure) and the cut order bound the loss.
  If K2 fails, the next decision (new amendment) is between a skeleton-fixed calibration (FA C/N
  held, inorganic atoms and dopant free; cheaper, less basin noise, misses organic relaxation) and
  option C trained on S2's DFT cells and tested on fresh hosts.
- **Large δ noise (s_δ > 20 meV).** Then only Sr-size effects are validated; S3 re-plans the
  calibration.
- **Basin divergence in A2** invalidates quartets (partner check), reducing m_d and df.
- **Noise floor above 25 meV** for most dopants → the frozen far field did not cure the S1 noise at
  DFT; more hosts or a different protocol.
- **New chemistries under zero-shot MACE.** Cl or Ca geometries may be poor; A2 measures this as δ,
  and |δ̄| > 50 meV removes the dopant from the validated tier.
- **Scope.** Cs-adjacent vacancy, one vacancy site, fixed MACE-MP-0 lattice (+2.4% against
  experiment), no SOC, 233-atom cell.
- **Operational.** Spot reclaims (resumable drivers, restart rule, keep-alive file during each
  campaign); four boot/stop cycles, plus one console restart per spot reclaim, that need the user's
  console login.
- **Triggers.** A dopant classified "binds" → S3 adds hop barriers (an A3 or A1-on-path pilot) for it;
  s_δ ≤ 10 meV with |δ̄_d| ≤ 10 meV everywhere → S4a can use A1 with a pooled calibration.

## 12. Left out on purpose

ΔE_a and hop classes; NEB; mid-shell maps; Rb, DMA, AA, SCN; aliovalent dopants (S4b); Cs-distal
vacancies; transport model; comparison with experiment; any MACE energy (zero-shot or fine-tuned) in a
decision; any use of the fine-tuned model, even for geometry.

## 13. Sources

Repository (read only; paths relative to `results/objective2/`): `SCREENING_ROADMAP.md` (updates
2026-10-27, 2026-10-28, 2026-11-03 a–c); `dopant_shell/PLAN.md` (criteria; amendments c, d, g, j, l,
m items 1′, 4, 5); `dopant_shell/WP1_RESULT.md`; `dopant_shell/WP1_PILOT_RESULT.md`;
`dopant_shell/WP2B_RESULT.md`; `dopant_shell/WP2C_RESULT.md`; `dopant_shell/WP2D_RESULT.md`;
`dopant_shell/WP2E_RESULT.md`; `dopant_shell/WP3_RESULT.md` §§1, 5, 8;
`dopant_shell/WP3_DIAGNOSTICS.md` §§3, 4, 10; `dopant_shell/WP3_RUNBOOK.md` (node drivers);
`s2/S2_BUILDERS_DESIGN.md` §§1–12; `CURRENT_STATUS.md` (standing prohibitions). The
repository-root `archive/PLAN_AMENDMENTS.md` is superseded and not used. The panel notes (three
proposals, the two judges' verification notes, the refuter's notes and Monte Carlo, and the
synthesis drafts and checks) are kept off-repository in the private record folder; every figure
taken from them that bears on a rule is restated, with its model, in `S2_PLAN.md`.

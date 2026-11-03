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

## Update 2026-10-28 — WP3 pre-registered (PLAN amendment m)

Amendment m fixes WP3 before any WP3 DFT single point, any fine-tuning run of its protocol, or any
fine-tuned prediction on a test host exists. It was checked against the archived data and the
installed mace-torch 0.3.16 source before adoption.

1. **Held-out set.** m30 and m32 as before, plus five corpus pairs that have no DFT yet (GA m10,
   m18; Sr m04, m14, m27; 50 single points): 9 ΔE_a pairs on 7 test hosts. m21 selects the
   checkpoint.
2. **Targets.** Vacancy cells are trained on E′ = F − (E_F − E_F,ref), which removes the
   neutral-cell band term frame by frame. A q = +1 check on training frames decides between E′
   and raw F before training.
3. **Adoption rule for S2.** The fine-tuned model replaces zero-shot MACE only if:
   - (a) criterion 6 shows improvement;
   - (b) on the 9 pairs, RMS ΔE_a < 20 meV with no class change at ±59.5 meV;
   - (c) every far-referenced m30 E_b error is < 25 meV and the near sign agrees;
   - (d) the frozen-far-field relaxations give a residual DFT force RMS < 0.05 and max < 0.2 eV/Å
     on the free atoms;
   - (e) a 5 ps MD stability check passes.

   Otherwise S1 ends without a validated potential. S2 then proceeds as in consequence 1 of the
   update above.
4. **Scope.** A validation covers single points at fixed geometries and forces at
   frozen-far-field vacancy minima. Barriers on the model's own paths and E_b from its own
   relaxations need a further pre-registered DFT check before S2 quotes them with an error budget.
5. **Estimate.** About 150 DFT single points (about 18 node-hours), 13–25 h of training, then 12
   WP3b single points and 12 MD runs. That is still about 1 week of node time.

## Update 2026-11-03 — S1 ends without a validated potential (WP3)

| WP | status | result |
|---|---|---|
| 3 | done; **outcome No improvement** (amendment m item 4) | **Criterion 6: No improvement**, also as amended by h. The force RMSE fell (0.0868 → 0.0149 eV/Å on the 46 m30/m32 frames). The paired ΔE_a RMS rose: 23.6 → 32.8 meV on raw F and 38.2 → 42.8 meV on E′. The far-referenced E_b RMS rose: 28.4 → 69.4 meV. Adoption (a)–(c) are not met. (b): 9-pair RMS 30.9 meV on E′, with class changes at m32 GA and m10 GA. (c): Sr hinge error −117.8 meV and Sr flank error −98.5 meV, with the flank sign lost. (d) fails: in all six frozen-far-field relaxations the free-atom residual DFT force RMS is 0.053–0.058 eV/Å against 0.05 (zero-shot minimum 0.142–0.160). (e) fails: 10 of 12 MD runs pass; m30 and m32 undoped at 450 K each have one frame in which a formamidinium C–H stretches past the 1.25 Å cut-off of the bonding-pattern test (1.252 and 1.262 Å; post hoc diagnosis). All five conditions fail (`dopant_shell/wp3/wp3_outcome.json`). See `dopant_shell/WP3_RESULT.md`. |
| item 6 | not run | The WP1 map with the fine-tuned model is not run, because the outcome is not Validated. Amendment m item 6 recorded this in advance as a deviation from the WP3 row. |

**What stands.**
- **Sr repulsion.** The Sr first-shell repulsion holds at DFT on MACE geometries (WP2c: +95.6 to
  +136.7 meV at 6 sites on 3 hosts). Zero-shot MACE reproduced the m30 hinge value to −6.4 meV
  (zero-shot still fails criterion 4: 6 of 15 sites above 25 meV, and first-shell Sr is
  overestimated by +19.2 meV on average, WP2c).
- **The fine-tuned model does not reproduce it.** It gives +11.6 meV at the m30 hinge and −3.0 meV
  at the flank, and it is not used anywhere.
- **Charge state.** The WP2d charge-state result is unaffected.

Consequences for the roadmap:

1. **S1 ends without a validated potential.** Under amendment m item 4 (Outcomes), it follows that:
   - zero-shot MACE is not re-admitted;
   - the 7 WP3 test hosts and the validation host m21 are used up. A further fine-tune needs new
     held-out hosts, named in an amendment before their DFT exists. Neither the evaluated
     `wp3.model` (sha256 3f7bf6f5…65d2ca) nor any other model is validated. Under item 4, any other
     model (retrained, re-seeded, or given other data or settings) is a new model.
2. **What the earlier consequences now imply for S2.**
   - **Update 2026-10-27, consequence 1** named two routes:
     - "a fine-tuned potential that passes criteria 5 and 6 (WP3)". This route is closed for this
       model, because criterion 6 failed.
     - "a protocol that does not depend on MACE minima being DFT minima". This route remains.
   - **Update 2026-10-28 (S1 status after WP2c/2d/2e), consequence 1** now applies as written:
     "If WP3 also fails, the screen needs either DFT for the decisive quantities or a coarser,
     dopant-ranking metric whose tolerance matches the errors measured here." Amendment m item 4
     refers S2 to exactly this.
   - **Update 2026-10-28 (S1 status after WP2c/2d/2e), consequences 2 and 3** are unchanged.
     - Barrier and binding differences should be computed for V_I⁺ or far-referenced. Raw
       neutral-cell E_b should never be compared with a local potential.
     - The frozen-far-field protocol is still untested at DFT level; update 2026-10-27,
       consequence 2, requires that test. WP2e′ stays unscheduled.
     - WP3b (d) failed, and in any case it concerns the forces of a model that is not adopted.
       It validates nothing for S2. Its `wp3bu_` cells (reported) do not meet criterion 5
       either: the whole-cell RMS is 0.057–0.059 eV/Å.
3. **Options for S2.** They are listed with their costs as far as the repository records them. They
   are not ranked, and they can be combined.
   - **A. DFT for the decisive quantities.**
     - **A1. Fixed-geometry DFT single points on MACE geometries** (the WP2b/WP2c protocol).
       - Cost per single point: about 6.7 min of node time per 233-atom cell at the WP2b settings.
         The WP3 chain ran 153 single points in 17.2 h (`dopant_shell/wp3/run2/node_logs/step2.log`);
         the 2026-10-28 estimate was about 18 node-hours per 150.
       - Cost per quantity:
         - a far-referenced E_b needs about 2 single points per site, plus host and V once per host
           (WP2c: 48 for 21 sites on 3 hosts);
         - a paired ΔE_a on 5 images needs 10 per pair.
       - Limitation: criterion 5 failed, and no relaxation-bias error bar exists (WP2e closed,
         amendment l). These values are fixed-geometry DFT energies, not relaxed DFT values.
     - **A2. DFT relaxations.**
       - Whole cell: the one whole-cell DFT relaxation (m30 GA image 0) took 282 BFGS steps and
         more than a day on the node. It spread −977 meV over the whole cell (`WP2E_RESULT.md`).
       - Frozen far field (WP2e′): not run, so the repository has no cost figure.
     - **A3. DFT barriers on DFT paths (NEB).** None has been run in this repository, so there is no
       cost basis.
     - **New chemistries under any A route** (`s2/S2_BUILDERS_DESIGN.md` §11; `scripts/42`, commit
       b9a6a8d).
       - Pseudopotentials for Cl, S, Ca and Rb are not verified and not on the node. Downloading
         them needs the user's approval.
       - Each new element needs a cutoff spot check.
   - **B. A coarser, dopant-ranking metric whose tolerance matches the measured errors.**
     - **The errors measured for zero-shot MACE against fixed-geometry DFT:**
       - paired ΔE_a: RMS 31.2 meV over the 18 WP2b pairs, with 3 class changes; 20.5 meV (raw F)
         and 31.0 meV (E′) over the 9 WP3 test pairs;
       - far-referenced E_b: 6 of 15 WP2c sites above 25 meV, largest |error| 60.0 meV (m30 GA
         near); first-shell Sr overestimated by +19.2 meV on average;
       - GA near − far at MACE level: −18.6 meV, against a far SD of 28.2 meV (WP1).
     - **(Interpretation, not a measurement.)** At the error level listed above (paired ΔE_a RMS
       about 20–31 meV; E_b errors up to 60 meV), the GA near − far (−18.6 meV) would not be
       resolved; the DFT-confirmed Sr first-shell repulsion (+95.6 to +136.7 meV, WP2c) would be.
     - **Cost.** MACE-level evaluation is cheap next to DFT: 0.56–1.0 s per force call on a
       234-atom cell on the node (`WP3_RUNBOOK.md`, node drivers). The roadmap's S2 gate also
       requires per-chemistry DFT spot checks, priced as under A1.
     - **Open point for the decision.** Amendment m item 4 does not re-admit zero-shot MACE.
       Whether a coarser metric may be computed with it, at a tolerance set from the errors above,
       would itself need a pre-registered rule: the metric, the tolerance and the DFT spot checks,
       fixed before any S2 value exists.
   - **C. A further fine-tune under a new pre-registration.**
     - **Held-out hosts.** It needs new hosts, named before their DFT exists. All five admissible
       corpus pairs without DFT were used by WP3 (amendment m item 1′), so new pairs need hosts
       outside that set.
     - **Recipe.** It needs a recipe that addresses the WP3 failure. The cause of that failure is
       not established: `WP3_RESULT.md` §8 lists candidate reasons, the most consistent being a
       small effective energy weight on near-equilibrium frames. None is tested.
     - **Measured WP3 cost** (node wall time, `dopant_shell/wp3/run2/node_logs/`).
       - `scripts/35` frames: about 5.8 h (`step2.log`, 2026-10-28 20:54 to 2026-10-29 02:50, less
         the 8-min gap of a node loss);
       - 153 DFT single points, about 17 node-hours;
       - training: 7.6 h for run2, the run that was used (100 epochs at 32 threads). A further
         ~7.9 h was lost to run1 (discarded after a node loss), and the three 2-epoch timing runs
         took 51 min;
       - 10 single points per held-out ΔE_a pair;
       - the (d)/(e) checks (step 7): 7.2 h of node wall time (2026-11-03 00:22–07:33,
         including an outage of about 16 min after a spot reclaim);
       - plus pre-flight and the laptop evaluation (step 6: 4 min).
     - **Scope.** A model of this kind covers H, C, N, Sr, I, Cs and Pb only. Each new chemistry
       needs its own validation (amendment m item 4, Scope).
   - **D. Combinations.** For example, a coarse MACE-level ranking with DFT (A1) on the candidates
     it retains. A combination needs its own pre-registered decision rule.
4. **The choice is the PI's.** Choosing among A–D, or any other route, is a PI decision. No S2
   result that depends on the energy level should be produced before that decision and its
   pre-registration.
   - **Independent of the choice.** The S2 builders (`scripts/42`, provisional, geometry only) do
     not depend on it.
   - **Open PI questions.** Thirteen are listed in `s2/S2_BUILDERS_DESIGN.md` §12.
5. **Estimate.** The best case of the 2026-10-28 updates no longer applies: about 5–6 weeks to a
   validated isovalent screen, conditional on a fine-tuned potential passing the adoption rule. A
   revised estimate depends on the option chosen and is not made here.

## Update 2026-11-03 (b) — WP3 post hoc diagnostics D1 and D2

These diagnostics are post hoc and reported only (`dopant_shell/WP3_DIAGNOSTICS.md`; plan d69fe75). They
change nothing in the WP3 outcome or in options A–D above.

- **D1, checkpoint trajectory (`WP3_RESULT.md` §8 reason 6).**
  - **Q1.** No kept checkpoint of run2 gets the five m21 E_b errors below 25 meV. None gets the two
    first-shell Sr sites alone below 25 meV either.
  - **The collapse.** The first-shell Sr E_b errors fall below −25 meV between kept epochs 3 and 11, at the
    training host m05 as at m21. From kept epoch 11 on, none is back within 25 meV.
  - **Q3.** The m21 loss does not rank the kept checkpoints by E_b (Spearman ρ = −0.12, descriptive).
  - **What follows.** Choosing a different one of the kept checkpoints would not have met the condition.
    The size still differs: the m21 E_b RMS is 63.8 meV at the selected epoch 82 and 31.3 meV at epoch 7.
    Unkept epochs were not evaluated.
- **D2, path attribution (reason 7): cannot be read.**
  - **Why.** The path 0 → i* through the band images with DFT frames (0, 2, 3; 0, 2 in two bands) is too
    coarse. The DFT path-work closure is −42 to −145 meV in all 37 bands, against the 20 meV rule.
  - **Image 1.** In a zero-shot check on four bands, adding image 1 alone did not bring any within 20 meV.
  - **Consequence.** The origin of the barrier lowering stays unattributed.
- **For the recipe of option C.** This is interpretation, not tested.
  - **m05 errors.** At m05, whose binding frames are training data, the first-shell Sr errors were within
    18.4 meV of zero at kept epochs 4–8. From epoch 11 on they lay at −28 to −105 meV, while the logged
    m21 force and energy RMSEs fell overall.
  - **The start of training.**
    - In the first epochs the m21 force RMSE rose above its Initial value (79.8 → 122.5 meV/Å at
      epoch 1).
    - The first-shell Sr errors overshot by up to +183 meV at m21 and +194 meV at m05 (kept epoch 2).
  - **Candidate changes.** Two candidate recipe changes are a stronger constraint on these energy
    differences (for example the test proposed under reason 1) and a gentler start. Neither has been
    tried.

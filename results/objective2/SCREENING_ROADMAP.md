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
| S4a | full **isovalent** screen, ~15–20 dopants | per-dopant DFT spot checks within PLAN criterion 4 | 1–2 weeks of node time (cost figure removed 2026-11-17: repository hygiene rule) |
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

## Update 2026-11-03 (c) — WP3 post hoc diagnostic D3

This diagnostic is post hoc and reported only (`dopant_shell/WP3_DIAGNOSTICS.md` §10; plan
`dopant_shell/WP3_DIAGNOSTICS_D3_PLAN.md`, ddb352b). It changes nothing in the WP3 outcome or in options
A–D above. D3 does not rerun reason 7's named test, which D2 ran and which cannot be read (update (b)).

- **Post hoc D3** (`WP3_DIAGNOSTICS.md`): a description of where the fine-tuned model books its change of
  E(i*) − E(0) along a densified band path, in two gauges; no verdict; reason 7's named test (model − DFT
  residual) not run.

## Update 2026-11-03 (d) — S2 route chosen (delegated)

**Who decided.** Item 4 of update 2026-11-03 ("The choice is the PI's") was delegated: on 2026-11-03
the PI delegated the choice of the S2 research direction to the analyst (an AI assistant) and
approved everything else, including the Cl/S/Ca/Rb pseudopotential download. A panel (three
proposals, two judges, a refuter and a synthesis; notes kept off-repository in the private record
folder) prepared the choice, and the analyst adopted it. Decision: `s2/S2_DECISION.md`. Rules:
`s2/S2_PLAN.md`, adopted with `dopant_shell/PLAN.md` amendment n. Pseudopotential record:
`s2/PSEUDOPOTENTIALS_S2.md`. Answers to the 13 builder questions: `s2/S2_BUILDERS_DESIGN.md` §16. No
S2 energy value (MACE or DFT) existed when these were written or when they were revised the same day
after three reviews, the analyst's decisions on their open issues and a review of those decisions
(`s2/S2_PLAN.md` §20).

1. **Route: option D, "A1 decides, A2 calibrates".**
   - Every per-host decisive value Y_h is an A1 quantity: a PBE single point at the S1 fingerprint
     (plus Cl and Ca pseudopotentials), V_I⁺, on a zero-shot MACE-MP-0 geometry relaxed with the far
     field frozen (one 6 Å region per site, shared by the four cells of an E_b quartet).
   - A2 frozen-far-field DFT relaxations of one first-shell quartet per sublattice on two pilot
     hosts (m30, m05), at different first-shell sites on the two hosts (Pb136, FA128 and the
     migrating iodide I138 on m30; Pb124 and the seeded draws FA28 and I49 on m05), estimate the
     relaxation bias δ = E_b(A2) − E_b(A1). The validated class rests on θ̂ = Ȳ + δ̄, which adds
     this A2 calibration to the A1 mean, with a Welch–Satterthwaite interval.
   - Option B survives only as a reported zero-shot ledger; C, A3 and ΔE_a are not part of S2.
2. **Why.**
   - Zero-shot MACE energies are not re-admitted (amendment m item 4), and no validated potential
     exists (update 2026-11-03), so DFT must supply every decisive number. This is the route of update
     2026-10-27, consequence 1, that remains: "a protocol that does not depend on MACE minima being
     DFT minima".
   - A1 alone has no relaxation error bar (WP2e closed without one); A2 everywhere is unaffordable
     (about 9 node-h per relaxation [I]). Measuring the bias on two hosts and correcting for it is the
     cheapest design whose bias term has its own variance.
   - Binding is the first-order transport effect; barriers matter only for binders, so they wait
     for S3.
3. **Question and dopants.** Is V_I⁺ attracted to, repelled by or indifferent to the first shell of
   Ca (B), Cl (X), Cs and GA (A), relative to two far sites, by more than k_BT = 25.7 meV? Sr is the
   positive control. Rb, DMA, AA and SCN are deferred (`s2/S2_BUILDERS_DESIGN.md` §10).
4. **Stages, gates and node-hours** (estimates [I] from measured unit costs: 6.74 min per single
   point, 6.15 min per DFT ionic step):

   | stage | content | gates | node-h |
   |---|---|---|---|
   | S2-0 (laptop) | Stage-0 code with self-tests; T4 report archived, `s2b-2` frozen; host and m05 calibration-cell admissibility; pre-flight | review | 0 |
   | C1 | pw.x smoke tests; elements gate G1 (Cl, Ca: cutoff, valence, spin); DFT noise pilot (106 single points on m30, m05); pose pilot (m30); q = 0 link rows | G1; gate N (σ_far ≤ 25 meV; sets n = 8 or 10); pose rule | ≈ 29 |
   | C2 | A2 on m30: hinge region (Sr, Ca) and the Sr far quartet | K2 (first relaxation converges or plateaus within 200 steps); cost projection; K3 (relaxed Sr hinge E_b > +25.7 meV) | ≈ 91 (67–145) |
   | C3 | A1 production: 8 (or 10) drawn hosts × 76 single points | validity; ≥ n − 1 valid hosts | ≈ 92 (n = 10: 114) |
   | C4 | A2 on the remaining regions of m30 and m05 | calibration controls | ≈ 237 (173–376) |
   | S2-5 (laptop) | one evaluation, adversarial check, result note | rule V with controls C1–C5 | 0 |

   - **Budget.** About 449 node-h (360–663 before the cap, no allowance for interruptions); **hard
     cap 520 node-h**, enforced by a pre-registered cut order that protects the Sr, Ca and Cl
     calibration. The node is stopped after each campaign. Calendar about 3–5 weeks from the stage
     durations of `s2/S2_DECISION.md` §8 (20–35.5 days), longer if campaigns wait for a console
     login [I]. Costs are stated in node-hours only; the currency figure of the S4a row of the
     stages table is not used.
   - **Hosts.** Production m06, m02, m16, m12, m32, m26, m22, m23 (reserves m33, m13), drawn by a
     seeded rule from 28 eligible members. m32 is a WP3 test host, used for DFT measurement only; the
     item-1′ hosts and m21 are excluded (amendment n item 3). 15 DFT-free hosts remain for any later
     option C (13 if n = 10).
5. **What S2 can resolve [MC].**
   - A validated class ("repels", "binds", or "no first-shell interaction beyond k_BT") for effects of
     about 43–79 meV (1.7–3.1 k_BT), depending on the measured bias noise s_δ (5–20 meV) and host
     noise s_Y (13–30 meV), with no site-type offset of the calibration sites. The Sr control is classified "repels" with probability ≥ 0.95 for
     s_δ ≤ 20 meV under rule V alone; with gate N and C2, which control C1 also requires, about 0.9
     at a far-site noise of 15 meV and 0.6 at 20 meV. A −75 meV binder is found with probability
     0.99 / 0.92 / 0.71 / 0.46 at s_δ = 5 / 10 / 15 / 20 meV (`s2/S2_PLAN.md` §18).
   - Unresolved dopants are reported with an upper bound on |θ|. The A1 tier is reported for every
     dopant, labelled "fixed-geometry DFT; relaxation bias not bounded".
   - S2 also measures the DFT noise floor per sublattice and the number of hosts each dopant needs,
     which was the deliverable of S3.
6. **What S2 cannot resolve.**
   - Effects below about 2 k_BT; "no interaction" unless both noise terms are small.
   - Barriers, ΔE_a and hop classes; transport rates; relaxed DFT minima.
   - Vacancies without a Cs neighbour (every pool host has the native Cs in the vacancy cage), other
     vacancy sites, the dilute limit, SOC and dispersion (a D3(BJ) correction is reported only), and
     anything about experiment.
   - Aliovalent dopants (S4b).
7. **Effect on the stages table.** S2 now includes the 5-dopant pilot of S3 and its host-count
   deliverable. S3 becomes: hop barriers and hop classes for any dopant classified "binds" (hop
   classes move from the S2 row to S3), a Cs-distal vacancy check for Sr and every classified
   dopant, and the deferred tokens once their starts are physical.
   The estimates of S3, S4a and S4b are not revised here; they depend on what S2 finds.

## Update 2026-11-05 (a) — S2 campaign 1 done

C1 ran on 2026-11-04/05 at the campaign commit `8bff03e`. It used 20.6 node-h (estimate ≈ 29) over two boots, with one spot interruption that the runner held and resumed. Result note: `s2/C1_RESULT.md`. Archive: `s2/c1/`. Figure: `s2/figures/fig_s2_c1_gates.pdf`. The node's five gate files were recomputed from the archive on the laptop with no difference.

1. **Elements gate G1.**
   - Cl passes.
   - Ca fails on the cutoff part: Δ_cut = +49.4 meV against 5 meV.
   - Ca therefore leaves the decisive family (`s2/S2_PLAN.md` §7). Its production and A2 cells are not run, and it receives no class; its pilot values are reported.
   - The decisive family is now Cl, Cs and GA, with Sr as the control. The family quantile stays at Bonferroni over 4.
   - Without Ca the calibration has df_δ ≤ 4, not 5. Under the unchanged cut order of `s2/S2_PLAN.md` §16, cut 2 (Cs on m05) would now leave df_δ = 2 and end the validated tier (`s2/C1_RESULT.md` §5a) [I].
2. **Gate N.**
   - All five dopants pass. σ_far is 12.4 (Sr), 8.8 (Ca), 17.8 (Cl), 3.8 (Cs) and 5.8 (GA) meV, with df 6 each and the bound at 25 meV.
   - Sr passes, so S2 continues to A2.
   - No decisive dopant lies above 20 meV, so **n = 8**.
3. **Pose rule.** Cs and Cl keep one minimum per leg at both pilot sites. Production uses the default pose, with a_pose = 0.
4. **A2 layout.** 64 ranks: 13.10 configurations per node-hour against 10.60 at 48 ranks.
5. **Next: C2.** C2 is A2 on m30 at the same commit: 8 relaxations, with the Ca136 pair dropped. The step-0, K2, projection and K3 gates apply as pre-registered.

## Update 2026-11-17 — S2 re-planned as S2b; FR passed; production campaign C3b started

This entry is an index. It states decisions and counts only; every value is in the note it names. No S2b energy
has been read: the one evaluation (E, `s2/S2B_PLAN.md` §7) runs after C3b ends.

1. **C2 (2026-11-07 to 2026-11-11): K3 fail_replan.** All eight A2 relaxations on m30 completed. One cell of the far
   quartet failed final-geometry check 5, so K3 failed before its value test and S2 was re-planned
   (`s2/C2_RESULT.md`, `s2/C2_DIAGNOSTIC.md`).
2. **S2b (pre-registered 2026-11-12, `s2/S2B_PLAN.md`).** The far reference is moved to a site whose free region
   holds no mobile organic cation (m30, FA188, Cs), and the production tier is A1: MACE geometries with a 6 Å free
   region, scored by far-referenced DFT single points. Amendments: 2026-11-12a (E's code), 2026-11-16a (C3b without
   C4b in S2b, by decision; the c3b gates and runner; E's block 4), 2026-11-17a (below).
3. **FR (2026-11-15): pass.** The four relaxations of the far-reference quartet completed; gates `fr_step0@2`,
   `fr_step0@4` and FR passed; the geometry read of §6b found all four cells valid under both readings of check 5.
   Cost 23.0 node-h against a plan of 22 to 58 (`s2/FR_RESULT.md`).
4. **C3b (started 2026-11-17).** Eight production hosts, 68 cells each: 8 host relaxations, 536 MACE relaxations of
   V⁺, D and D+V⁺ cells and 544 DFT single points (`s2/C3B_OPERATIONS.md`).
   - The node check at the first c3b commit (`840ad22`) failed in the self-test of `scripts/50` (77 cases, 3 failed).
     Nothing of c3b had started. The three failures were defects of test cases, corrected inside the self-test
     only; amendment 2026-11-17a records the causes, what the corrected test shows and does not, and one deviation
     of the operator (the node was kept running during the diagnosis).
   - At the campaign commit `e5883d5` every check of `s2/C3B_OPERATIONS.md` §5 passed on the node, and the runner
     started on 2026-11-17 at 14:07 UTC with both budget projections applied and no cut. H_spent at the start:
     118.5 node-h of the 520 node-h cap.
   - C4b (the A2 calibration at the production level) is not run in S2b. E follows C3b directly; what E can then
     state is the A1 tier without that calibration (`s2/S2B_PLAN.md`, amendment 2026-11-16a, D-0).
5. **Known limits before E.** Block 4 of E has been tested on synthetic archives only; an end-to-end test on
   real-format files is being written and will be committed, with a dated note, before E runs. An independent static
   review of the integration found no blocking defect and named that gap as its one major finding.
6. **Fine-tuning retests (outside S2b's blinded data).** Three post hoc retests of the WP3 fine-tuning failure have
   run and a fourth is running; they are reported together, under their pre-specified readings, when the fourth ends.

## Update 2026-11-21 — C3b: three spot reclaims, then a change of node; the fine-tuning re-tests are published

This entry is an index and a record of events. No S2b energy has been read; E (`s2/S2B_PLAN.md` §7) runs after C3b ends.

1. **C3b so far.** All 536 MACE relaxations and the 8 host relaxations are recorded (544 records, 2026-11-18). Of the
   544 DFT single points, 76 were published when the runner was restarted on 2026-11-21.
2. **Interruptions.** The spot node was reclaimed three times during C3b: on 2026-11-17 at 14:10 UTC (three minutes
   after the first start), on 2026-11-18 at 14:35 UTC and on 2026-11-19 at 22:28 UTC. The runner recorded each
   termination notice. After each, the campaign was restarted with `ehpc/node/s2_relaunch.sh` in the clean checkout of
   the campaign commit `e5883d5`; the runner re-derives every job from its files, and a published single point is not
   recomputed.
3. **Change of node on 2026-11-21 (an event the plan does not foresee; recorded here before the campaign ends).**
   The operator moved the node from the spot instance to an on-demand instance of the same instance type and CPU
   model. The data disk is the same: the work tree, the checkout, the conda environments of MACE and Quantum
   ESPRESSO and the pseudopotentials are unchanged. The system disk is new: the operating system was installed again
   (kernel 6.8.0-147; before, 6.8.0-139) and the node scripts outside the checkout were installed again.
   - Checked before the restart: the sha256 of the five node scripts against `s2/c1/nodescripts_check.json`; the
     sha256 of `pw.x` and of `mpirun` against the first fr launch; the nine pseudopotential files against
     `s2/c1/upf_check.json`; the unmodified self-tests of `scripts/46`, `47`, `49` and `50` at `e5883d5` on the new
     instance (15, 15, 19 and 77 cases, none failed); the checkout clean before and after.
   - The runner was restarted on 2026-11-21 at 16:42 UTC.
   - **Not checked:** that a single point gives the same energy on the two instances. No single point was computed
     on both, and comparing one would mean reading a c3b energy before E. The single points of host m06 and the first
     of m02 (76 in all) ran on the first instance, the others run on the second: same binaries and libraries, same
     CPU model, another system disk and kernel. The split follows the publication times (before and after
     2026-11-21 16:42 UTC) and is confounded with the host. The c3b result note will state it.
4. **Node-hours.** The system journals of the earlier boots stayed on the old system disk. For a boot without a
   readable journal the ledger takes the assumed bound of `s2/C3B_OPERATIONS.md` §7 (last heartbeat + 60 s + 60 min +
   15 min). This now applies to all 11 earlier boots, so H_spent reads 152.2 h where the journals gave 139.5 h two
   days earlier: an over-count of about 12.6 h, on the safe side of the 520 h cap. Nothing was changed in the ledger
   and no operator entry was made. Expected H_spent at the end of C3b: about 207 h.
5. **The new node has no idle self-stop.** The statements of `s2/C3B_OPERATIONS.md` §7 that rest on it (the resume
   window; the end of an unjournalled boot) describe the first node. The operator stops the new node by hand after
   the pull.
6. **Fine-tuning re-tests (outside S2b's blinded data): published** in `dopant_shell/wp3_retests/`
   (`WP3_RETESTS.md`, `WP3_RETESTS_V4V5.md`). In short: three single-head recipes at learning rate 0.005 lose the
   Sr–vacancy repulsion; multi-head replay keeps it but stays above the pre-set force line; lowering the rate alone
   limits the loss without removing it (two seeds at 1e-4, on either side of the 50 meV class line), and the loss is
   ordered with the rate over 1e-4, 1e-3 and 0.005. The cause is not identified, and no model is adopted.
7. **E, block 4.** The end-to-end test announced on 2026-11-17 is recorded in `s2/s2b/records/E_T11_END_TO_END.md`;
   it found no defect, and E's files are those of `e5883d5`.

## Update 2026-11-24 — C3b ended; private archive and verify made; next steps

No S2b energy has been read. Decisions and counts only.

1. **C3b ended on 2026-11-23 at 23:41 UTC** (CAMPAIGN_DONE) at the campaign commit `e5883d5`: 544 MACE records and
   544 DFT single points complete. Gate `c3b_complete`: true. Gate `c3b_tier`: computable, with valid hosts per
   dopant Sr 8, Cl 7, Cs 7, GA 6 of 8. Cells whose check 5 passes under the invariant reading only: none (V 0, D 0,
   D+V 0). H_spent at the end: 203.8 h of the 520 h cap, of which about 12.6 h is the ledger's over-count recorded
   on 2026-11-21.
2. **One more interruption after the change of node.** On 2026-11-23 at 05:32 UTC the node was shut down in an
   orderly way (the runner received the shutdown signal; not a reclaim, not a crash; who ordered it is not visible
   from the node). The campaign was restarted at 12:01 UTC. C3b had five starts of the runner in all.
3. **Pull, private archive, verify (2026-11-23/24).** The c3b tree was pulled and compared with the node by path,
   size and modification time (10293 files, no difference). The private archive holds 544 labels and 2550 files.
   `scripts/49 verify` in a private root that holds `c3b/` only: 3 gate files, 0 differ. The c3b note, the verify
   record and the result note are committed before E runs.
4. **The cross-instance check announced on 2026-11-21 is still open.** No single point has been recomputed on the
   second instance yet. If it is made, its rule is committed here before any of its energies is read.
5. **Fine-tuning re-test V6** (replay with the optimiser settings of V3) is pre-specified in
   `dopant_shell/wp3_retests/V6_PRESPEC_2026-11-24.md` and runs on the compute node after C3b. Its node time is not
   S2b time; the archived c3b ledger ends with the campaign.

## Update 2026-11-24 (b) — E has run; corrections to the C3b note; rule of the cross-instance check

No value of E is stated here. By `S2B_PLAN.md` section 7 (run discipline) E's output stays private while the c3b
archive is private and becomes public with the S2b result note.

1. **E ran once**, on 2026-11-24 at 01:16 UTC, at commit `98bb606` (attempt 1; route C4B-NOTRUN). Its last line is
   "E exit code: 0": no integrity check and no cross-check failed. sha256 of `E_output.txt`:
   `3273f0a2241ecd4cc636f073f7bbfac6666db6719102de7440df03419ed34e12`. An independent recomputation of block 4 from
   the raw single-point outputs is under way; the S2b result note follows it. Block 5 (the hinge) was not opened.
2. **Corrections to `s2/C3B_NOTE.md`.** The note is not edited, because E recorded its sha256. Found after E, from
   the start time printed in the header of each single-point output:
   - 75 single points, not 76, ran on the first instance of the node: the 68 of m06 and 7 of m02 (host, VB124,
     VB136, VB76, VB172, VA28, VA92). The other 469 ran on the second instance.
   - "published" in the campaign log marks the submission of a single point to the queue, not its end. The
     intervals of section 6 of the note (6.55 and 6.17 min) are therefore intervals between submissions, and the
     counts "per start" of section 5 are submissions.
   - The number of resubmissions, which the note leaves unread: three single points have an archived first try
     (`s2_m02_VA92`, `s2_m02_VA128`, `s2_m22_Sr136o0_vac`), each cut short by an interruption of the node (the
     reclaims of 18 and 19 November and the shutdown of 23 November). Only the completed run of each is a result.
3. **Rule of the cross-instance check** (announced 2026-11-21; fixed here before any rerun exists). Eight single
   points are run again on the second instance, from their archived inputs, with the launcher, binary and 64 MPI
   ranks of the campaign.
   - Six ran on the first instance: the quartet of Sr at site 124 in m06 (`s2_m06_host`, `s2_m06_VB124`,
     `s2_m06_Sr124o0_novac`, `s2_m06_Sr124o0_vac`), `s2_m02_host` and `s2_m02_VA92`. They were chosen by position
     (the first quartet of the first host, the first and the last single point of m02 on that instance). The list
     was fixed on 2026-11-24 at 01:39 UTC (commit `d842834`), after E had run. The sequence, from the commit times
     and the session record: when the list was fixed, the operator had read E's header, sections 4.0, 4.1, 4.3
     to 4.5, 4.7 and 4.8 of block 4 and the lists after it (counts, the invalid cells, the per-dopant and per-site
     means, ranking, sensitivity, cross-checks) and no row of section 4.2; the per-host rows of section 4.2, which print the raw E_b of this m06 quartet (a value formed
     from four of the eight cells), were read a few minutes later, before the reruns were launched at 01:44 UTC.
     So the list was fixed without a cell energy in view, and the reruns were started with one in view. Two earlier
     versions of this item (commits `a962aee` and `4634f8e`) each stated one half of this; this one replaces both.
   - Two are controls that ran on the second instance: `s2_m02_VA128` (its first) and `s2_m23_Cl186o0_vac` (its
     last).
   - Read-out: the difference of the total energy (the line marked "!") between the rerun and the archived output,
     and for the m06 quartet the difference of the raw E_b.
   - Readings: every |ΔE| ≤ 0.1 meV, "reproducible across the instances at this sample"; any first-instance
     |ΔE| > 1 meV with both controls ≤ 0.1 meV, "an instance effect", reported with its size against the intervals
     of E; a control above 0.1 meV, "the rerun itself is not reproducible at 0.1 meV", and the six say nothing
     about the instance; anything else is reported as a small difference without a class.
   - The check changes nothing in E. It is a sample of 6 of 75; it cannot show that all 75 are reproducible.
   - It runs after the fine-tuning re-test V6 has ended, so that the 64 ranks have the node to themselves.
4. **V6 is running** on the node since 2026-11-24 at 00:49 UTC, after a first launch that failed before training;
   the cause, the deviation and the gate as read are in execution note 1 of
   `dopant_shell/wp3_retests/V6_PRESPEC_2026-11-24.md`. The first three epochs took 12.3 to 13.0 min each, which
   projects about 21 h for 100 epochs, under the 30 h of the stopping rule for cost.

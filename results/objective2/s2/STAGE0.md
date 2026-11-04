# S2 Stage 0: code, laptop checks and pre-flight (record of 2026-11-04)

**Status: Stage 0 of `S2_PLAN.md` §17 (items 2–4) is written, self-tested and checked on the laptop, and has been
through six review rounds (§7). After the third (the round-3 fixes on 2026-11-04) it was committed as e257cdf, with
this record and the `s2/stage0/` records, on top of the plan commit ae6402e (§17 item 2). The round-4 changes of
2026-11-04 (§7, round 4) are a dated follow-up to e257cdf, made before any S2 calculation and committed on top of it
as bfaf321. The round-5 changes of 2026-11-04 (§7, round 5) are a dated follow-up to bfaf321, also made before any S2
calculation and committed on top of it as 63a3511. The round-6 changes of 2026-11-04 (§7, round 6) are a dated
follow-up to 63a3511, also made before any S2 calculation and committed on top of it with this record; the commit that
holds them is the S2 campaign code. The analyst's decisions
on the open Stage-0 items are in §9 (D-S0-2 revised and D-S0-9 added after round 2, D-S0-10 on the round-3 reading
I-D9, D-S0-11 on the round-4 readings and D-S0-12, which closes the review loop after round 6, all 2026-11-04,
and implemented as recorded in §7). Any later change before or during the campaigns is a
dated commit recorded in this file; the commit in force is the one each campaign records at its start. **No
S2 cell, pilot or production, of any host has been evaluated by any calculator (MACE, DFT or a mock), and no S2
energy exists.** Calculators were attached only to synthetic cells and to the reference cells
`results/fa_host/fa19cs1_pb20i60_233.extxyz` and `results/fa_host/fa19cspb20i59_232_vI.extxyz` (a mock harmonic
calculator; MACE was never loaded), and every geometry-only path and self-test asserts that `mace` is not in
`sys.modules`. The node was not accessed. Archived S1 QE inputs and outputs were parsed to test the parsers and
to pin the S1 pseudopotential identities; they are not S2 cells.

Tags as in `S2_PLAN.md`: **[R]** read or measured in the repository without a calculator; **[M]** modelling or
implementation choice; **[I]** interpretation; **[S]** secondary source. "§n" is a section of `S2_PLAN.md`;
"design §n" a section of `S2_BUILDERS_DESIGN.md`; "spec" the Stage-0 interface specification (kept
off-repository, with the module reports and the review reports, in the private record folder). Paths are relative
to `results/objective2/` unless they begin with `scripts/`, `ehpc/` or `results/`.

**Interpretations and implementation notes are not rule changes.** Where the plan is silent the code takes the
conservative, fail-closed option and records it as an implementation note (N-); where a rule had to be read it
records an interpretation (I-) with its plan section; where a rule cannot be implemented exactly as written the
closest fail-closed version is implemented and the conflict (X-) is listed in §5 below. Every one is printed by
the module's `--self-test` and listed in Appendix A, generated from the code.

## 1. What Stage 0 built

| file | lines | role | plan sections |
|---|---|---|---|
| `scripts/46_s2_cells.py` (module A) | 2 823 | sites, far pairs and the four farthest sites asserted against the §4 tables; regions R_j (6.0 Å, molecules whole by carbon), `region_id`, index transfer host → V → doped; host relaxation (`scripts/29 relax_staged`, 0.02/0.01/0.005 eV/Å, 10 000 steps); V⁺_Rj (I127, 1.2 Å); D_j and D_j+V by `scripts/42 build_paired`; frozen FIRE relaxation (fmax 0.01 eV/Å over the free atoms, 10 000 steps, `FixAtoms` outside R_j); validity checks 1–5; the §11 final-geometry checks 2–5 (`validate-a2`, refused without the partner's final geometry); distinct minima; pose starts of Cs and Cl with the §2 Pb–Cl rule; labels and work ids; records; node and archive layout; public hygiene; the MACE loader (foundation-file sha256, float64, CPU, threads; never called by a test) | §§2, 4, 5, 9, 11, 17; design §§3, 11, 16 |
| `scripts/47_s2_qe.py` (module B) | 2 278 | the S2 pw.x writer (the `scripts/30` fingerprint unchanged plus the Cl and Ca UPFs; 50/400 and 60/480 Ry; R point; degauss 0.005; `nosym`; conv_thr 10⁻⁸; mixing 0.3; electron_maxstep 200; relax: BFGS, 7.8 × 10⁻⁴ Ry/bohr, 10⁻⁵ Ry, nstep as a parameter, `if_pos 0 0 0` outside R_j, `disk_io 'low'`); X-unit vacancy detection, tot_charge and the `_q0` exception; the valence-electron assertion; the §7 spin seed; UPF identities; single-point and relaxation parsers with read modes (QE's error banner a final end, the queue's transient file states read again); the §11 end rule; the step-0 equivalence; the free atoms' per-atom force norms | §§6, 7, 10–13, 15 |
| `scripts/48_s2_analysis.py` (module C) | 2 999 | rule V at both tiers (δ valid by the §11 rule), the §12 validity and dopant-specific rules, controls C1–C5, ranking, the §15 reported items (with the A1-start sensitivity row of D-S0-2, the count terms of multi-pose legs and the pilot section of the MACE ledger), `assemble` (the only full read of C3/C4 and MACE energies) and the one evaluation with its guards, including the analysis code against the campaign commit (`s2/s2_eval.json`; round 4: the amendment rules, the commit history, complete A2 cells only, the pilots' default-pose Cs and Cl rows; round 5: the evaluation waits for C3 when C4 is not planned, the D3(BJ) row's own amendment, each output's diff named after it) | §§11, 12, 14, 15, 17 |
| `scripts/49_s2_gates.py` (module C) | 2 312 | every decision constant (`RULES`); gates G1, N and the n rule (gate `nrule`), the pose rule, step-0, K2, K3, separability; the §16 projection, cut order, hard-cap rule and throughput choice; the blinded `Reader` and its allow-lists; `verify`; round 4: the 2x32 rate only for a concurrent pair on disjoint cores (I-C13) | §§7–9, 11, 14, 16, 17 |
| `scripts/50_s2_campaign.py` (module D) | 7 332 | job graphs of C1–C4 with counts asserted against the plan; the resumable node runner (flock, keep-alive, spot watcher with a reachability check, MACE and A2 reruns, queue rules, A2 parts with exit files and restarts, the section 11 check jobs, hard cap on pw.x and MACE jobs only, gates, guarded STOP and exit paths, STOPs held until the gates on ended cells have applied, shutdown as an interruption, RESOLVE for A2 and for the pw.x reference runs, `c1/NODE_FIX`, a hung-child watchdog; round 4: every pw.x run outside the queue through the committed launcher, two concurrent copies on disjoint halves of the cores and the throughput pair run together, the node-script hashes, a strict git check, the model load at check:mace, durable held STOPs; round 5: the check records moved aside at a commit change, pollers that never answer STOP, the model-load record's exception name; round 6: pollers that keep ending after a good poll STOP, the moved UPF record's MD5 used until the UPF check passes again); node-hour ledger; laptop archive (refusing names that differ only in case) | §§7–13, 16, 17 |
| `scripts/51_s2_preflight.py` (module D) | 528 | §17 item 4: dry-run builds of every C1 cell and of the C2/C4 start set on the unrelaxed pilots, every C1 single-point and A2 input, the smoke-test and throughput inputs, all checked | §§5–11, 16, 17 |
| `scripts/52_s2_stage0_checks.py` (module E) | 1 295 | §17 item 3: the T4 report and the `s2b-2` freeze, the admissibility check of ranks 1–12 and of the m05 calibration cells, the Pb–Cl record, the laptop MACE hash | §§2, 3, 5, 11, 17 |
| `ehpc/node/s2_campaign.sh`, `s2_relaunch.sh`, `s2_status.sh`, `s2_run_qe.sh` | 25, 54, 13, 36 | start (lock on fd 8, a clean git checkout; a git failure refused), relaunch after a reboot (refuses while the S2 lock is held, any S2 process lives, its own shell and parent excepted, or a campaign is stopped; a refusal, its own or one of `s2_campaign.sh`, removes a KEEP_ALIVE older than the boot; before the first start it refuses with 'no S2 work tree'), status from the lock ('not started' before the first start; never an energy), and the pw.x launcher of every run outside the queue (the node's run_qe.sh with an optional core set for each of two concurrent copies, round 4) | §§13, 16, 17 |
| `s2/stage0/` | 6 records | `t4_admissibility.json`, `s2b2_freeze.json`, `admissibility.json`, `pbcl_source.json`, `mace_laptop.json`, `preflight_c1.json` (§§3, 4 below) | §17 items 3, 4 |

`scripts/22`, 29, 30, 33, 34, 35 and 42 are unchanged (`git diff` is empty) and are loaded through importlib, as
`scripts/42` loads 22 and 29. No new dependency is used (ase, numpy and, lazily, scipy).

**Job graphs** [R, geometry only, `scripts/50 graph`]: C1 has 338 counted jobs: 164 MACE relaxations (2 host,
30 V⁺_R, 80 noise-pilot and 20 start-set dopant, 32 pose-pilot extra) and 161 single points (5 G1, 2 spin, 106
noise-pilot, 2 step-0, 36 pose-pilot, 10 q = 0), i.e. 325 calculator jobs of these kinds, plus 4 smoke-test parts,
4 throughput runs and 5 gates (throughput, G1, N, nrule, pose; the n rule is `nrule`, never `n`, so that no two names
fold to one file on the laptop's case-insensitive volume: round 3, N-F15).
C2 has the 10 A2 relaxations of §11 in their fixed order, one section 11 check job each and 5 gates; C3 at n = 8
has 8 host, 152 V⁺ and 448 dopant relaxations and 608 single points (n = 10: 760 and 760); C4 has the 26 A2
relaxations of §11 and their 26 check jobs. Each count is asserted against the plan under G1 failures, cuts and
pose modes.

## 2. Self-tests

Run from the repository root with the project's Python environment on 2026-11-04, after every fix of §7 (all six
rounds) and the implementation of the post-round-2 decisions D-S0-2 (revised) and D-S0-9 (§§7, 9), all files
present (no module mocked). Each prints its cases, the I/N/X entries it implements and ends with the case
"no-model: 'mace' not in sys.modules". Full logs (they contain local paths) are in the private record folder.

| script | result | what the cases cover |
|---|---|---|
| `scripts/46` | PASS, 14 cases, 9 s | the §3 and §11 draws; site lists of the 14 hosts of the §4 table and the four farthest sites of m30 and m05; the m05 census of §11 (Pb124 3.27, FA28 5.03, I49 4.63 Å; regions 70/58/59 host atoms on the unrelaxed member) and the m30 cross-check (69/49/58/107); region and index-transfer invariants for every token and leg; 161 C1 labels, 36 A2 and 9 reference labels, 164 work ids, 30 refused labels, none matching `scripts/33`; every validity check with a passing and a failing synthetic case at its boundary; distinct-minima cases; FixAtoms honoured by a mock relaxation; pose starts (Cs 7 + 7, Cl 3 + 3, the Pb–Cl override); the job pipeline on the reference cell including `validate-a2` (pass, a far atom moved 0.30 Å failing check 5, V⁺, D and D+V without the partner's final geometry refused with no record, a foreign geometry refused); hygiene; the MACE path computed without importing mace |
| `scripts/47` | PASS, 15 cases, 4 s | inputs and electron counts for the reference cells and every token and leg (host 1070, V 1062, `_q0` 1063; Sr/Ca 1066/1058, Cl 1070/1062, Cs 1060/1052, GA 1076/1068) with 20 refusals; the fingerprint against `scripts/30` (7 single points byte-identical) and line by line against four archived S1 inputs, the deliberate S2 differences listed; the spin seed (Cl 1/7, Ca 1/10, 0.1 elsewhere); the WP2e relaxation (283 configurations, F(120) − F(100) = −58.296 meV, F(200) − F(180) = −16.320 meV, equal to the trajectory CSV within 0.6 µeV; 201 configurations at k_cap 200, end rule unconverged_cap); read modes capturing no value; end-rule boundary cases (3.000 / 3.001 meV); restart concatenation; single-point completeness, with the queue's states between its `mv` and `touch` and a file moved during a read; QE's error banner in the SCF of WP2e configuration 120 (pw_error, unconverged early, STOP) and after k = 200 (cap rule); another input name refused; UPF identities over 376 archived S1 outputs; step-0 at 0.5000 / 0.5001 meV; round 3: the free atoms' per-atom force norms of a single point (N-B18) |
| `scripts/48` | PASS, 22 cases, 2 s | an independent second implementation of every §14 statistic and control decision (1 810 statistics and decisions on five tables: Y_h, Δ_h with SD(Δ_h)/√2 and mean(Δ_h), the per-site t intervals at both tiers, both tiers' intervals and classes, C1–C5, n_d, the validated and the shown A1 class, δ, pooling, ranking; worst difference 3.4 × 10⁻¹³ meV at F ≈ −8 × 10⁴ eV; changing the √2 of C2 or its strict < makes the self-test fail); planted classes (Sr repels, Ca −75 meV binds, null dopants, GA repels); the −100 meV X site flagged and the −80 meV site neither flagged nor "no interaction"; refusals (no repelling control, df_δ = 2, \|δ̄\| 50.001 meV, the dopant-specific rule, now including multi-pose rejected starts); G1, gate-N and pose-cut no-class cases; edge cases; the `assemble` round trip from a synthetic archive written as scripts/46 and 50 write it (`o<k>` labels through the distinct-minima records); round 2: the multi-pose 10% rule over cells (5/336 no trip, 28/160 trip), the heterogeneity flag at its rounding threshold; after round 2 (D-S0-2 revised): an A1-invalid start of an A2 cell, where the §11 rule decides (Ca m_d 2 and every decisive number unchanged; δ_far valid where K3 passes on the same records), and the reported-only A1-start sensitivity row equals the decisive result with that δ dropped; round 3: the boundaries of C2 (24.999975 / 25.000025 meV, \|mean\| 14.999 / 15.001 meV, exactly 25 and 15 meV failing), C4 (7 / 6 of 8), the valid-host thresholds, the sign rule at n = 10 (7/10 not resolved, 8/10 repels), C1 through Sr's C2, C4 and C5, the required hosts against an independent loop; the count term beside an aggregated E_b (3 and 2 kept minima: 10.4205 meV) and the MACE ledger's pilot section; the assemble round trip with the G1, N, nrule and pose files side by side, the pose gate's count term and the force norms reaching `s2_eval.json`; the path-work, determinism, q = 0 and WP2c rows; the analysis-code guard against the campaign commit in a temporary git repository; round 4: the calibrated sign rule on Y_h + δ̄ and the strict class bounds at ±25.7 meV (each of three mutations of rule V makes this case fail), the pilots' Cs and Cl noise rows equal to gate N's E_b with their MACE values, a killed_by_gate A2 cell neither parsed nor given a relaxation energy, the guard's amendment rules (a note outside scripts/, added after the campaign commit, dated on or after it), an amendment recorded with unchanged code, the diff's sha256 and the commit history with the diff stat of each NODE_FIX step; round 5: the one evaluation refused while C3 has not ended and C4 is not planned (K2 fail, step-0 fail_final, K3 a1_only, cut 8 at after4, C3 still running), allowed after C3 ended or recorded not_run, refused with C4 planned; the D3(BJ) row cites only a `--d3bj-amendment` note (one of the campaign commit accepted; under scripts/, uncommitted and undated notes refused), never the code-fix `--amendment`; a rerun's analysis diff beside its own `s2_eval.rerun1.json`, the first one intact (cmd_evaluate with its git guards stubbed) |
| `scripts/49` | PASS, 16 cases, 1 s | the 22 plan pins, the unit costs and the §12 per-host list; every gate with passing, failing and boundary cases (G1 5.000/5.001, 3.000/3.001, M 0.09/0.10; σ 25.000/25.001, df = 2; n rule at 20.000/20.001; pose 10.000/10.001 and the (+10, −10) case; step-0 and its repeat; K2; K3 at 25.7000/25.7001 with the A2 checks, host_R missing with its children's checks skipped (a1_only), the I-C1 text; separability; projection and cut order at after4/c3/c4 with spec §4.9 cut records; hard cap 520.000/520.001; throughput 1.15×/1.1499×); the blinded Reader; gate runners and `verify` on a synthetic archive (round 3: the gate names unique after lower-casing, the old name `n` refused); the real scripts/47 parsers through the Reader; round 4: the 2x32 rate only for two concurrent copies on disjoint cores (I-C13: 90.0% / 89.97% overlap, a solo rerun, shared or missing core sets, shared CPUs, CPUs outside the set) |
| `scripts/50` | PASS, 60 cases, 57 s | a simulated campaign over two boots on the reference cells with a mock MACE, a mock pw.x and the committed `qe_queue.sh` and `chain.sh` (paths rewritten): (a)–(c) single-point completeness; (d) spot notice, exit file and restart (part 2 differs only in `restart_mode` and `nstep`, counters continue, no launch during the hold); (e) the k = 200 stop and the end rule, and the section 11 check failing check 5 on a far atom moved 0.30 Å; (f) an OOM kill without restart data: two reruns, missing, check skipped; (g) a MACE interruption; (h) keep-alive; (j) resume; (l) runner reads; (m) every A2 relaxation scheduled with its check job, K3 waiting for the checks, a K2 stop; (n) the step-0 repeat; (o) scripts/49 K3 on runner-written A2 records; (p) measured walls carried across campaigns, the restart-part cap, the ledger bound, the chain lock; (i) hard cap (after a refusal only pw.x and MACE jobs are swept; a check, a gate and a geometry job stay pending); (k) C1–C4 graph counts; archive; spot URL; hygiene; round 2: (q) checks without a configuration or a partner (K2 fail, C2 CAMPAIGN_DONE, C3 precondition, K3 a1_only), (r) the check after a cap refusal with two copies, (s) A2 ends (pw.x error, unexplained end, RESOLVE, OOM, node loss), (t) STOP and exit paths (full disk, a reason naming a temporary path, SIGTERM and the relaunch decision of `s2_relaunch.sh`), (u) projection inputs, (v) OOM by the command's own pid, (w) the queue state between `mv` and `touch` with the committed queue, N-B9 at every A2 read, (x) the hung-child watchdog; after round 2 (D-S0-9): (y) gates after a hard-cap refusal (relaxation 5 refused, every gate evaluated, K3 a1_only applied, CAMPAIGN_DONE); round 3: (z1) no case-fold collision among the job ids, gate names, gate files, markers, labels and work ids of seven C1–C4 graphs, and archive refusals; (z2) a smoke test ending with QE's error banner (one attempt, missing, the throughput row STOPs naming the smoke tests, a new HEAD refused, then `c1/NODE_FIX` and RESOLVE 'rerun' reach the MACE phase); (z3) an unreachable spot endpoint STOPs before any job; (z4) the smoke test at the A2 layout folded before `smoke2.json`; (z5) a held STOP at 2x32 (K2 cell and K3 cell with the error banner: the running copy gets the exit file and is killed_by_gate within 0.1 s; the bfgs_failed control); (z6) SIGTERM while the K3 gate, validate-a2 or a geometry job runs; (z7) SIGTERM inside the statuses (A2 part and MACE attempt judged at the relaunch as node-loss); (z8) K3 before relaxation 9 at 48 ranks; (z9) OOM evidence by the part's process tree; (z10) the cap refusal persisting across a relaunch (I-D9); (z11) the precondition matrix and the n rule; (z12) the dead status removed and a stale KEEP_ALIVE at a refused relaunch; round 4: (z13) the spot heartbeat at every good poll (a fake clock with the real limits) and a restarted poller's grace; (z14) a spot notice inside one scheduler pass; (z15) RESOLVE into a live run; (z16) smoke tests not affine with slope 1; (z17) two concurrent copies on disjoint halves of the cores through the committed launcher, the throughput pair run together and the 2x32 rate only for such a pair; (z18) the node-script hashes; (z19) git failures; (z20) the rerun budgets after RESOLVE; (z21) OOM evidence for smoke and throughput runs; (z22) the model load at check:mace; (z23) the wrappers before the first start and on a refused start, a manual ledger entry; (z24) a held STOP that survives a shutdown or a second STOP; (z25) a tree recorded before the pw.x ranks; (z26) a relaxation between parts when a gate stops A2; (z27) a gate's exit replacing a 'cap' or 'spot' request; (z2) also `start_commit` and `commit_history` in campaign.json; round 5: (z13) also, after one good poll of the first poller, restarted pollers that never answer (a STOP spot_first_s after the first restart, nothing run); (z22) the child's qualified 'c46.S2Error' named in the record; (z28) a NODE_FIX re-runs the C1 checks at the new commit (a changed launcher recorded with its new sha256 and C2 passing; a committed queue that the node copy does not match STOPs C1 in its check phase); (z2) also the three checks run again after its NODE_FIX; round 6: (z13 d) pollers that each answer once and end (a STOP at the third renewal of the grace, nothing run); (z28) also, after the NODE_FIX, the moved UPF record's Cl/Ca MD5 used until check:upf passes again, and a re-check with other MD5 a STOP |
| `scripts/51` | PASS, 8 cases, 14 s | the pre-flight checks on a subset and five planted errors, each caught (electron count, duplicated label, region id, degauss, shifted Cl without the Pb–Cl record) |
| `scripts/52` | PASS, 11 cases, 3 s | pins, the §3 and §11 draws, admissibility on m30 (one token per sublattice), exception classes, the production-list and m05 fallback logic, the Pb–Cl decision rule (5.674 → confirmed; 5.675 → 2.8375; secondary only → provisional; web addresses kept out of the record), path stripping, the T4 archive and freeze, the laptop MACE check |
| `scripts/42` (unchanged, `s2b-2`) | PASS, 13 cases, 87 s | its own self-test, run again after the round-6 fixes (and inside `scripts/52 t4` in round 2, 90 s); it loads none of scripts/47–50, the only Stage-0 scripts changed in round 3 |

The round-1 reviewers' integration checks were rerun on the round-1 code (§7): the cut-format reproducer now builds the C3
and C4 graphs; the label check finds 241 labels and no disagreement between scripts/46, 49 and 50; the
reviewer's independent statistics check agrees (0 failed); the parser check over the archived S1 outputs agrees;
the reviewer's audit of the 205 pre-flight input files finds 0 problems; K3 on a runner-written A2 record now passes.
The round-2 reviewers' and adjudicators' reproducers were rerun against the original and the final files (logs in
the private record folder): each defect shows on the original files and not on the final ones (the queue race,
the pw.x error banner, the missing-partner and SCF-k0 checks, the cap sweep, the full-disk, hygiene-path and SIGTERM
stops, the C1 timings, the multi-pose cell count, the A1-condition case and the flag assert). The cases added for the
post-round-2 decisions fail on the round-2 files and pass on the final ones: the 48 case "A1 start validity
reported, section 11 decides" against the round-2 scripts/48, and 50 cases (i) and (y) with the round-2 cap sweep
restored (K3 stays 'not started (hard cap)'); logs in the private record folder (round 3).
The round-3 reviewers' and adjudicators' reproducers were rerun against the files before round 3 and the final files
(§7, round 3; logs in the private record folder): each defect shows on the former and not on the latter. Run on the
code before round 3, the twelve new scripts/50 cases (z1)–(z12) and the revised case (s) fail, and so do the new
scripts/48 cases on the defects (assemble round trip, count term and ledger, the evaluation guard); the scripts/48
cases that only add coverage (the extended independent implementation, the boundaries, the reported rows) pass there,
as they should: the code they test was right.
The round-4 cases were spliced into the e257cdf files of scripts/48, 49 and 50 and run there (logs in the private
record folder, round 4): every new scripts/50 case ((z13)–(z27)) and the extended (z2) fail, as do the guard and pilot-row
cases of scripts/48 and the throughput case of scripts/49; (z17), (z21) and (z22) fail on e257cdf because the API they
test is new. The scripts/48 coverage case of R4-C24-6 passes on e257cdf, whose rule was right, and fails on each of the
three mutations it guards against (the calibrated sign rule on Y_h, 'repels' at lo ≥ 25.7 meV, 'binds' at hi ≤ −25.7
meV). The round-3 C1 end-to-end simulation (three boots) was rerun on the final files with the same counts and
decisions as in round 3 (§7, round 3), its archive (161 labels, 330 structures) and `scripts/49 verify` (5 gate files, 0
differ) pass, and the fault scenarios behave as recorded.
The round-5 cases were spliced into the bfaf321 files of scripts/48 and 50 (the round-5 code changes reverted, the new
cases and helpers kept; logs in the private record folder, round 5): (z13), (z22), (z28) and the extended (z2) fail
there, each on its defect, and so do the two new scripts/48 cases (the guard at (i), the D3(BJ) row citing the code-fix note, and, with only
the diff naming reverted, the first evaluation's diff overwritten). The C1 lens' three-boot simulation of the real C1
graph and its NODE_FIX scenario were rerun on the final files: the same gates and decisions as on bfaf321 (G1, gate N,
n = 10, pose, CAMPAIGN_DONE; an archive of 161 labels, 330 structures and 463 JSON files; `scripts/49 verify` 5 gate
files, 0 differ), and after the NODE_FIX the three checks run again.
The round-6 cases were run on the 63a3511 code (the round-6 code changes of scripts/50 reverted, the new cases kept;
logs in the private record folder, round 6): (z13) and (z28) fail there, each on its defect (no STOP and nothing run;
md5_extra None after the NODE_FIX). The three-boot C1 simulation and its NODE_FIX scenario were rerun on the final
files: the same gates, decisions, archive and `scripts/49 verify` result as in round 5 (the round-5 outputs of the
simulation, its gate check and its archive are reproduced byte for byte).

## 3. Laptop checks of §17 item 3

### 3.1 T4 report and the `s2b-2` freeze [R]

`scripts/42_s2_builders.py --self-test --report` was run again (13 cases, 0 failed), last on 2026-11-04 after the
round-2 fixes (`scripts/52 all` with a new report path in the private record folder). The raw report (sha256
`0a77d73e…2841`, identical in every regeneration) holds no path-bearing value; its archived copy with an
`archive` block is `s2/stage0/t4_admissibility.json` (sha256 `e13ac567…107d`; it changes with the sha256 of the
scripts it records and the time of writing, never with a decision), and the raw report and its log are in the
private record folder. The freeze record `s2/stage0/s2b2_freeze.json` records `BUILDER_VERSION` s2b-2,
`GEOM_SHA` `58ebbd29fdf179417269818f6fc31b7d55622164929a40778c49208e1cdafedf` (also recomputed from the frozen
parameters), f = 0.9, f_w = 0.8, the class map with the H split, the class-Y rule, thresholds and host minima, and
the sha256 of the archived and raw reports (design §§6, 16 answer 3). scripts/46 refuses to load unless
scripts/42 is s2b-2 with this `GEOM_SHA`.

### 3.2 Admissibility of draw ranks 1–12 and the production lists [R]

The §3 draw was re-executed (28 eligible members, crc32 order equal to the §3 table). On the unrelaxed pool
member of each of ranks 1–12, every required cell (the 19 sites of §4 × the tokens of their sublattice, both
legs, default poses, `build_paired(..., partners="unrelaxed")`, `mig="allow"` at X sites) was built: **all 12
hosts are admissible** (28 pairs and 56 legs each, no `Inadmissible`, `Refused` or other exception). The lists
are therefore those of §3:

- **n = 8:** production m06, m02, m16, m12, m32, m26, m22, m23; reserves m33, m13.
- **n = 10:** production adds m33 and m13; reserves m17, m03.

`s2/stage0/admissibility.json` holds the per-cell table, the lists (`matches_plan_lists: true`) and status `ok`;
scripts/50 reads the lists from it at the start of C1.

### 3.3 m05 calibration cells [R]

The §11 m05 draw was re-executed (A: FA28, FA92; X: I49, I138, I125, I137, I126, I90, I102, with the §11 crc32
values). Every required cell of Pb124 (Sr, Ca), FA28 (Cs, GA) and I49 (Cl) is admissible, so no fallback is
needed: **the m05 calibration sites are Pb124, FA28 and I49**, as in §11.

### 3.4 Pb–Cl 2.837 Å source check (§2) and the resulting rule

- **What was verified.** By web search only (nothing downloaded or executed), 2026-11-03. The publisher's record
  of Poglitsch & Weber 1987 (J. Chem. Phys. 87, 6373–6378, DOI 10.1063/1.453467) confirms the bibliographic data;
  its abstract states that the crystal structures were determined by X-ray diffraction but gives no lattice
  parameter, and the full text was not read. A curated secondary source (the Duke University Hybrid3 materials
  database, reference entry for this paper, data sets 166–168) quotes cubic CH₃NH₃PbCl₃ (Pm3m, above 178.8 K)
  with a = 5.675 Å [S], so a/2 = 2.8375 Å, which differs from 2.837 Å at the stated digits (0.0005 Å).
- **Level.** [S] secondary; the primary value was not seen.
- **Rule applied** (interpretation I-E1, kept after review): "verified" means read in the primary source. The
  design's tag legend reads [S] as "secondary source only, so recheck before production" and [V] as "checked
  against a primary source", and 2.837 Å is already tagged [S] there (design §4, Cl row). The secondary quotation
  therefore does not verify, the §2 branch "no value can be verified" applies, and **the shifted Cl starts are
  built at 2.837 Å with `--allow-provisional` and labelled [M] starting points** (decision `provisional_2.837` in
  `s2/stage0/pbcl_source.json`; scripts/46 refuses a shifted start without the record and the flag). The centred
  (default) Cl start, every other token and the clash parameters are unaffected.
- **Open for the analyst** (§6): if the paper's structure table is read before any shifted Cl start is built and
  states a = 5.675 Å, §2 requires 2.8375 Å; `scripts/52 pbcl` is then rerun with level "[S] primary verified" and
  scripts/46 applies the X-2 override (§5). The source's web addresses are kept in the off-repository notes.

### 3.5 Laptop MACE foundation file [R]

`20231203mace128L1_epoch199model` (44 422 970 bytes) at the path `mace_mp(model="medium")` resolves in mace-torch
0.3.16 has sha256 `01bfe22100139f424713cf921144e5509cbe353d67aa9fa1be9c6e1e0ed35845`, equal to §5
(`s2/stage0/mace_laptop.json`; versions read from package metadata, mace not imported). The node copy is a C1
item (§8).

## 4. Pre-flight (§17 item 4) [R, geometry only]

`scripts/51_s2_preflight.py run --allow-provisional` (run again on 2026-11-04 after the round-2, round-3 and round-4
fixes; summary equal to the earlier one except its wall time and date) built, on the unrelaxed m30 and m05 members with
`partners="unrelaxed"` (the unrelaxed member standing in for the S2-relaxed host and the `pp.build_pair` vacancy
cell for V⁺_R), every C1 cell of §§7–10 and the C1 start set of §11, both legs: **164 cells and 66 pairs, all
admissible** (all 12 displaced Cs starts at FA128 and FA188 and the 4 shifted Cl starts at I138 and I175 included;
no rejected start). It wrote to a temporary folder outside the repository **161 single-point inputs** (G1 5, spin
2, noise pilot 106, step-0 2, pose pilot 36 (every pose start treated as a kept minimum), q = 0 10), **36 A2
inputs** (C2 10, C4 26; nstep 201 as a placeholder flagged "pending smoke tests", X-3) and **7 reference inputs**
(3 smoke tests, 4 throughput runs, 232-atom cell with the Pb136-like region). Checks: site tables, graph counts,
30 region ids (deterministic, one per (host, site), shared by every cell of the site), the builder (134
checks: V1–V10, admissibility, pair records), electron counts and charges and the writer's namelists (204 inputs each, against `settings_for` and the
literal §6 values), labels (grammar, uniqueness, the plan's lists), the restart input: **failures: none**. Region
sizes: m30 Pb136 69, Pb76 107, FA128 49, I138 58; m05 Pb124 70, FA28 58, I49 59; reference Pb136 70 host atoms.
The path-free summary is `s2/stage0/preflight_c1.json`; the dry-run outputs are not used.

## 5. Conflicts and closest fail-closed versions (for the analyst)

- **X-1 (§15, D3(BJ) row).** The plan fixes a D3(BJ) implementation and version in Stage 0. None exists in the
  environment (ASE's `dftd3` needs an external binary; `dftd3`, `simple-dftd3`, `torch-dftd` are absent) and no
  new dependency may be added. Stage 0 fixes no implementation; scripts/48 reports the row as "not computed".
  Fixing one needs a dated amendment before the one evaluation. Reported-only row; no decision rests on it.
- **X-2 (§2 vs the `s2b-2` freeze).** A verified Pb–Cl other than 2.837 Å cannot be put into scripts/42 (frozen,
  inside `GEOM_SHA`). scripts/46 then builds the shifted Cl from the centred start along the s2b-2 shift direction
  at the source distance, re-validates with `b42.validate` (V1–V10) and records `start_override` and `start_sha`
  beside `GEOM_SHA` (tested at 2.8375 Å; at 2.837 Å it reproduces the s2b-2 shift to 10⁻¹² Å). Not triggered by
  the present record (§3.4).
- **X-3 (§§11, 13, 16, nstep and restart).** The nstep that caps a relaxation at k = 200, its value after a
  restart and whether a restart repeats a configuration are unknown until the C1 smoke tests. No A2 relaxation
  starts until `c1/smoke.json` holds an affine mapping of slope 1 and a restart test that reproduces the
  uninterrupted count; otherwise every interruption uses the rerun rule. The exit-file stop at k = 200 and the
  parser's cut at k = 200 hold whatever the mapping.
- **X-4 (§16, smoke tests "at the A2 MPI layout").** The layout is chosen later in C1. The smoke tests run at 48
  ranks first (before any S2 cell), then the throughput row; if another layout is chosen, the exit and restart
  test is repeated at it before C2.
- **X-5 (hygiene vs the spot endpoint).** The metadata address may appear in no new file. It is read at run time
  from a node-local file, else from the `SPOT_URL=` line of the committed `scripts/wp3_runbook/node_step7.sh`; it
  must start with `http://` and end with `/termination-time`, or the campaign does not start.
- **X-6 (host validity, §5).** §5 states only convergence for the host relaxation; a host whose relaxation broke a
  molecule would pass and every cell built from it would pass check 4 against its broken start. Fail-closed: the
  host is valid iff the 0.005 stage converges and check 4 against the pool member passes. To be confirmed.
- **X-B1 (hygiene vs a QE keyword).** The hygiene word rule matches QE's default `restart_mode` value. Part 1 of a
  relaxation therefore writes no `restart_mode` line (QE's default, the same calculation) and records a fresh start
  as `null`; the restart part adds `restart_mode = 'restart'` and changes nstep, nothing else (§13).
- **Spot hold (§13, N-D6).** During the 1800 s hold after a spot notice no single point is published, but one
  already published may still be started by the committed queue, which cannot be paused without editing it.
- **Hard cap with queued single points (§16, I-D2).** Checked at publication rather than at the queue's own start:
  at most two single points are outstanding and each counts twice its expected time, so the check is never looser
  than one at the real start.
- **Revised readings that change no plan rule but did change spec behaviour** (§7, review F5): the spec's I-10
  (A2 relaxations with an invalid A1 start not run; K2 failing on an A1-invalid start) and I-11 (an A1-invalid K3
  cell giving fail_replan) added conditions the plan does not name. They were replaced by the plan's literal
  rules: every planned A2 relaxation runs; K2 is the end rule of V⁺_R(Pb136); K3 is fail_replan iff the value is
  ≤ 25.7 meV or a quartet fails the §11 final-geometry checks 2–5; the A1 validity of the start cells is reported.
  Under D-S0-2 as revised on 2026-11-04 (§9) the same holds for δ: a δ is valid by §11 alone (its four
  relaxations accepted by the end rule, their final geometries passing checks 2–5), m_d counts these δ, and δ_far
  validity is the K3 quartet validity. The A1 validity of every A2 start cell is reported beside each δ, and rule V
  with the A1-start condition is a reported-only sensitivity row of scripts/48 (`reported.a1_start_sensitivity`);
  no class, gate or decision rests on it (I-10). The round-2 construction (a validated class only when the A1-start
  and §11 readings agree) is withdrawn. (The working interface specification carries a dated note that its I-10,
  I-11 and the gate name `n` are superseded; the round-1 report copy in the private record folder is left as it
  was, with a one-line pointer beside it.)
- **Hard cap after its first refusal (§16, I-D9; round 3, R3C-7): confirmed by the analyst (D-S0-10, §9).** §16 reads "No job
  starts if H_spent plus the job's expected duration … would exceed 520 h; jobs already running finish. Whatever is
  then incomplete is missing." The runner reads it as: after the first refusal in a campaign no further pw.x or MACE
  job of that campaign starts (each is `not_started_cap`), even one whose own expected duration would still fit (a
  2-min MACE relaxation after a refused single point). This is the fail-closed reading (fewer cells, never more node
  time) and the one in force since round 1; it is now recorded as I-D9 and the refusal persists in `HARD_CAP.json`
  across runner starts, so a relaunch gives the same decision (before round 3 it lived in memory only). The literal
  per-job reading (apply the job-start rule to each job and mark only the jobs whose own check fails) is the
  alternative; it would let short jobs run after a long one is refused. Jobs without node-hours are never swept
  either way (N-F14, D-S0-9).

- **Readings added in round 4 (§§13, 16; confirmed by the analyst, D-S0-11, §9).** (a) *Two concurrent 32-rank copies* (§16, I-C13, N-F30):
  the two copies are measured only together, each on one half of the physical cores; a copy that ran without the
  other beside it is run again with it (the first measurement moved aside, not used), and the 2x32 rate is computed only when
  both recorded disjoint core sets and their walls overlap for at least 90% of the shorter one ([M]); otherwise the
  rate is None and the layout is not chosen (48 or 64 ranks), never chosen on evidence that is not the plan's layout.
  (b) *Reruns after an operator's resolution* (§13, N-F33): an operator's 'rerun' after a STOP for a human (a MACE
  exception, a smoke or throughput run resolved after a fix) is not one of the two reruns §13 allows after a reclaim,
  node loss, OOM or wall time, and the attempts before the resolution go aside with it; each such rerun needs a human
  and, for a code cause, a dated commit (D-S0-8). An A2 'rerun' stays counted (I-D6, N-D5: an infrastructure cause).

## 6. Interpretations and implementation notes

All 211 entries, each with its plan section, are in Appendix A (generated from the `NOTES` of the seven scripts).
The ones that carry most weight:

- **Sites and regions (§4).** Gaps asserted at the plan's rounded pool figures widened by half a last digit
  (I-1); "within 6.0 Å" is d < 6.0 (I-2); the deleted I127 is checked against the unrelaxed member's v (I-3);
  `mig="allow"` at every X site (I-39).
- **Validity (§5).** Host convergence is the final-stage flag of `relax_staged` and the strict max|F| < 0.005 eV/Å
  (I-4), and host validity includes check 4 against the pool member (X-6); partner gating by relaxed-host
  positions from the relaxed-host centre (I-5); "within 1.25 / 1.6 Å" fails at d ≤ value, the floor at d < 0.65 Å
  (I-A1); check 3 against the cell's own builder output, for A2 the A1 builder output (I-A2, I-A4); a `Refused`
  on relaxed partners rejects the pair like `Inadmissible` (I-9).
- **§11 final-geometry checks (I-F1).** When an A2 relaxation completes, the runner reads the positions of
  its last configuration (scripts/47 `read="final_geom"`, no energy) and writes `<label>.final.extxyz`; once it and
  its partner (host_R for V⁺_R and D, V⁺_R for D+V) have ended, scripts/46 `validate-a2` runs checks 2–5 (host_R:
  check 4) and `validity_final {valid, failed}` is written into the A2 record. A partner without a final geometry
  (missing, not run, killed, or complete without a configuration) and a relaxation completed without a
  configuration (an SCF failure at k = 0): the check is not evaluated (skipped; `validate-a2` refuses to run without
  the partner), and the quartet is invalid through the missing cell, so K3 is a1_only there (round 2, R2V-1, R2V-2).
  The checks, like the gates, run whatever the hard cap: they complete a relaxation that was allowed to start (N-F8,
  R2V-3; N-F14, D-S0-9). K3 waits for these checks; scripts/48 reads them for every δ, and with the end rule they
  alone decide its validity (I-10, D-S0-2 revised).
- **Labels (§§5, 9).** The A2 host cell of region j is `s2r_<h>_host<L><j>` (I-7); `o<k>` numbers kept minima per
  leg, o0 only for a valid, kept default start (I-8, N-A14); work ids `p<n>` number the starts (N-3).
- **QE (§§6, 11, 13).** tot_charge always written (I-B1); the dopant is its own species by occurring once (I-B2);
  the S1 UPF identity is the MD5 printed in every archived S1 output (one per element, pinned from 376 outputs),
  Cl and Ca by sha256 (I-25); every output must print pw.x 7.5 and the expected rank count (I-26); once
  configuration 200 exists the cap rule decides (I-B4); an nstep end before k = 200 is unconverged early and STOPs
  the campaign (I-48); end-class precedence and unknown ends (N-B4).
- **Gates and statistics (§§8, 9, 14, 16).** A δ is valid by the §11 rule, the A1-start condition entering only a
  reported-only sensitivity row (I-10, D-S0-2 revised); a valid far site for gate N is a valid noise quartet (I-12); a
  missing default or kept-minimum single point makes the pose rule "not met" (I-14); "entirely above" is
  lo > 25.7 meV etc. (I-20); the dopant-specific rule counts cells: the site rule counts a host with any failing cell
  at the site, the 10% rule one cell per default-pose leg and one per relaxed start of a multi-pose leg (round 2,
  STAT-3), rejected p0 pairs counted as failed cells and rejected non-default starts in multi-pose production not
  counted (I-16, I-C10); the A1-tier
  class is shown only when the A1-tier controls pass (I-18); the shared-region sensitivity (I-19); cuts that are
  inapplicable or unavailable at a projection are skipped (I-25b); measured means and fallback unit costs for the
  hard cap (I-21), carried across campaigns from the files (I-F6); the restart part of a started A2 relaxation is
  checked with its remaining configurations (I-F7); a past boot without a readable journal ends at its last
  heartbeat + 60 s + 60 min idle self-stop + 15 min, unless the operator records its stop time (I-F8); the
  projection's C1 MACE timings come from the C1 records through scripts/49 (I-C7b), never from a phase wall (N-F9).
- **Campaign operation (§§12, 13, 16).** Single points published one at a time (N-5); pw.x outside the queue only
  under the global chain lock and with no foreign pw.x alive (N-6); MACE never beside pw.x (N-7); a Python
  exception is a STOP, not an interruption (N-9); only pw.x and MACE jobs are refused by the hard cap, while the
  gates, the §11 checks and the other jobs without node-hours are never swept to 'not started (hard cap)' and run
  whenever their inputs are complete (N-F14, D-S0-9); keep-alive removed at every STOP, first and before any write, at a
  shutdown, at any exit of the runner, and by the spot poller when the runner died without CAMPAIGN_DONE (N-12,
  N-D4; round 2, F1, M2); SIGTERM (a reboot or a stop of the node) is an interruption that leaves the campaign
  running for `s2_relaunch.sh`, SIGINT is the operator's STOP (N-F10); the A2 end classes (I-D6): a pw.x error
  banner is a final end (unconverged early, STOP for a human), and an end without JOB DONE in the current boot
  without an exit request or an OOM kill is a STOP with `RESOLVE` 'unconverged', 'rerun' or 'missing', never an
  automatic rerun (round 2, F2, R2-QE-1); OOM evidence by the command's own pid and, for A2, by pw.x ranks after
  the part's start (I-D7, F4); a hung child (2 h without output, MACE beyond 3 h / 12 h) is a STOP (N-F13); the
  single-point queue's transient file states are read again, and its state between `mv` and `touch` is missing with
  `.gaveup` written by the runner (N-B8, R2-QE-2); the electron count, Cl/Ca MD5 and input name of every
  single-point and A2 output are checked by the runner, the MD5 of every other output (N-B9, R2-QE-3); the step-0 failure and its one repeat (I-D1, I-F3): `c2/STEP0_FIX` with
  the new commit and the dated note restarts C2 at relaxation 1 in state `repeat_pending`, both cells are checked as
  attempt 2, and the attempt-1 A2 and gate files are moved aside; the gate files are archived, the attempt-1 A2
  records and outputs stay on the node (R2V-4); `c2/STEP0_NO_ERROR` records "no error found" (fail_final, A1 tier
  only). Round 3: the n-rule gate is `nrule` and the archive refuses names that differ only in case (N-F15); a
  smoke-test or throughput run that ends with QE's error banner is missing at once, a missing smoke mapping STOPs
  naming the smoke tests, and those runs are resolved by RESOLVE (N-D10, N-F16); a C1 STOP fixed by a committed change
  resumes with `c1/NODE_FIX` (N-F17); no job runs before the spot endpoint has answered, and a lost endpoint STOPs
  (N-F18); the smoke test at the A2 layout is folded into `smoke.json` before `smoke2.json` is written (N-F19); a
  STOP asked for by an A2 end rule is held until the gates and checks on ended cells have applied, so a stopping gate
  kills a running copy at once (N-F20); a shutdown that kills a synchronous child, or finds a child ended, classifies
  nothing (N-F21); a section 11 check ends the scheduler tick, so K3 precedes relaxation 9 (N-F22); OOM evidence by the
  part's own process tree (N-F23); the production list needs a recorded n and C3 the C1 `gate:nrule` marker (N-F24);
  a refused relaunch removes a KEEP_ALIVE older than the boot (N-F25); the hard-cap reading I-D9 (§5). Round 4: every
  pw.x run outside the queue goes through the committed launcher, two concurrent copies run on disjoint halves of the
  cores, the throughput pair always runs together and the 2x32 rate counts only for such a pair (N-F30, I-C13); the
  node-script hashes (N-F31); a git failure is a STOP (N-F32); the rerun budgets after RESOLVE (N-F33); OOM evidence by
  trees that hold the pw.x ranks (N-F34); the model load at check:mace (N-F35); durable held STOPs (N-F36); a gate's exit
  replaces a 'cap' or 'spot' one and a relaxation between parts is discarded unread (N-F37); smoke tests not affine with
  slope 1 STOP inside C1 (N-F38); the heartbeat at every good poll and the restarted poller's grace (N-F18); RESOLVE never
  into a live run (N-F16); a notice inside a scheduler pass holds its later launches (N-11). Round 5: a commit change
  (NODE_FIX, STEP0_FIX) moves the campaign's check records aside, so the checks run again at the new commit (N-F31);
  pollers that end before answering keep the first one's start and STOP (N-F18); the model-load record names a
  qualified exception (N-F35). Round 6: the third renewal of a restarted poller's grace within 300 s is a STOP
  (N-F18); after a commit change the existing C1 outputs are read against the moved UPF record's Cl/Ca MD5 until the
  UPF check has passed again (N-F31, N-B9).
- **Analysis additions (§§9, 15, 17; round 3).** N_D, N_D+V and the count term beside every aggregated E_b and
  Δ_pose (N-F26); the MACE ledger's pilot section (N-F27); the free atoms' per-atom force norms (N-B18, N-F28); the
  one evaluation records the campaign commit beside HEAD and refuses a change of scripts/46–49 without a committed
  dated amendment (N-F29); N-C11 cites §15. Round 4: the amendment must be a note outside scripts/, added after the
  campaign commit and dated on or after it, and is recorded also with unchanged code (N-F29 revised); the commit history
  with the diff of each step (N-F39); only complete A2 cells are read (N-F40); the pilots' Cs and Cl cells are
  default-pose cells (N-F41). Round 5: with C4 not planned the one evaluation waits for C3 to end or to record
  not_run; the D3(BJ) row cites only a `--d3bj-amendment` note; each output's diff is named after its JSON (N-F29, N-C8).

## 7. Review record (2026-11-03/04; rounds 1–3 before the Stage-0 commit, rounds 4–6 after it)

Two reviews of the module code against the plan (one per module set and one of the cross-module hand-offs), each
with its own reproducers; no calculator, no S2 cell. Every finding was reproduced by the fixer before it was
acted on. The two reviews' overlapping findings are merged below (review 1: R1-Fn; review 2: R2-Fn).

| finding | severity | verdict | what was done |
|---|---|---|---|
| R1-F1 = R2-F1: §11 final-geometry checks 2–5 never computed (K3 could never pass, no δ ever valid) | error | applied | I-F1: final geometries written by scripts/50, `validate-a2` in scripts/46, check jobs in the C2/C4 graphs (counted), K3 after the checks, archive of the geometries and check records; tests in 46, 50 (cases e, f, m, o) and 49 |
| R1-F2 = R2-F2: cuts stored as integers by scripts/49 and read as records by scripts/50 (TypeError once a cut applies) | error | applied | one format, the spec §4.9 records `{cut, at, P_before_h, P_after_h}`, read everywhere through `cut_ids`; cross-module reproducer now builds C3 and C4 |
| R1-F3 = R2-F5: a Ca G1 failure removed 16 + 16 per C3 host in the projection (plan §12: 8 + 8) | error | applied | `C3_G1_REMOVAL["Ca"]` = 8/8, pinned against the §12 per-host list; 49 and 50 now agree (544 SPs at n = 8); the spec §11.3 figure was a spec defect |
| R1-F4: in multi-pose production any rejected (inadmissible displaced) start counted as a dopant-specific failure of the site | error | applied | rejections recorded per start; only a rejected p0 counts (I-C10 revised); self-test case |
| R2-F3: the step-0 repeat after a fix could not run (A2 stayed stopped; the fix note and repeat flag were lost) | error | applied | `repeat_pending` state, attempt-1 A2 and gate files moved aside (the gate files archived, the A2 records and outputs kept on the node; corrected in round 2, R2V-4), merged step0 decisions, fix note from inputs or state, `STEP0_NO_ERROR`; cases in 49 and 50 and a fixer reproducer through the real 49 gate |
| R2-F4: kept minima `o<k>` (k ≥ 1) had no MACE validity in `assemble`, so every multi-pose quartet was invalid | error | applied | validity taken through the distinct-minima records' work ids (N-C15); the self-test archive now labels only p0 records, as scripts/46 does |
| R1-F5: I-10/I-11 changed K2/K3 outcomes and skipped A2 relaxations on conditions the plan does not name | minor | applied (conforming option) | every planned A2 relaxation runs; K2 and K3 as the plan states, A1 validity reported; δ needed valid A1 cells until D-S0-2 was revised after round 2 (now the §11 rule only; §5 above, §9) |
| R1-F6: measured walls of the hard-cap rule kept in memory only (C4 used 20.6 h, not the C2 mean) | minor | applied | I-F6: walls loaded from the files of every campaign at each start; test with a C2 record reaching C4 |
| R1-F7: the restart part of a running A2 relaxation checked as a new 20.6 h job | minor | applied | I-F7: checked with the configurations still allowed × the measured wall per configuration |
| R1-F8: an unreadable journal silently dropped the idle hour after a campaign | minor | applied | I-F8: conservative idle-stop bound, overridable by the operator's stop time; test |
| R1-F9: an nstep end before k = 200 recorded as unconverged although caused by a wrong mapping | minor | rejected | §11 says "any other end without QE convergence before k = 200 … the cell is unconverged, it is not rerun"; an nstep end is such an end. The literal rule is kept with the STOP (I-48); the A2 record now also stores the end class and reason, so a dated amendment can address the cell if the mapping was wrong |
| R1-F10: the Pb–Cl decision treats a reliable secondary source as unverified; the record carried a URL with a host name | minor | URL applied; decision kept | web addresses stripped from the record (N-E9) and refused in any JSON record by scripts/46 (N-A15); I-E1 kept with the design-legend justification of §3.4, open for the analyst |
| R1-F11: a missing pose mode was read as "default" (fail-open); `a_pose` written into the state | suggestion | applied | a missing Cs/Cl mode counts as multi-pose and production modes must equal the pose gate under cuts 6/7 (N-C14); `a_pose` stays in the gate output only |
| R2-F6: the global chain lock (N-6) defined but never taken | minor | applied | N-F6: pw.x outside the queue only under the chain lock (passed to the child) and with no foreign pw.x alive; test |
| R2-F7: a restart nstep of 0 possible when c0 ≥ 1 (unexpected-error stop) | minor | applied | N-F7: written as 1; the exit file and the parser cut keep k ≤ 200 |
| R2-F8: the one evaluation parsed A2 relaxations without the C1 smoke mapping | minor | applied | N-C13: the mapping from `c1/smoke.json`; a multi-part relaxation without it is refused |
| R2-F9: `a2_skipped` never written by scripts/50 | suggestion | moot | no A2 relaxation is skipped any more (R1-F5); scripts/49 no longer reads the field |
| R2-F10: `s2_campaign.sh` exited 0 when the lock was held, so a relaunch was logged | suggestion | applied | exits 1 |

Spec defects found and corrected in the code (the spec is a working document; the plan governs): the Ca G1
removal of spec §11.3 (16 → 8); the spec's a2-record `restart_mode` value and its §7.4 "`.out.try1` + `.gaveup`"
queue state (X-B1, N-B8); the spec's single-format cut list (§4.9 records adopted). Record fields added beyond the
spec: A2 records carry `final_geometry` and `validity_final`; the step0 state carries `repeat`, `fix_note` and
`attempt1`; ledger rows carry `end_assumed`.

Not exercised on the laptop (node-only paths): `/proc` and `journalctl` reads (the OOM parser is tested on lines in
the kernel's two formats), `pgrep`, util-linux `flock` (a Python shim stands in), git on the node, the real
`run_qe.sh` and pw.x (in particular that pw.x 7.5 names `<label>.p<n>.in` in "Reading input from" and prints QE's
error banner as its source does), and the two-copy A2 layout (tested at unit level only); the wrappers pass
`bash -n`, and the relaunch decision of `s2_relaunch.sh` runs in the self-test on a copy with its paths rewritten.
The analysis rerun guard of §17 item 6 is untested end to end, since no commit yet contains scripts/48.

### Round 2 (2026-11-04)

Four lenses (the round-1 fixes, statistics, campaign safety, QE inputs), each followed by an adjudicator who
reproduced every finding; items the adjudicators added as missed were reproduced by the fixer before acting (M1, M2,
the stale I-C1 note, the fail-open multi-pose case and the first-failure queue race by running their reproducers;
the non-root-rank QE error by the code trace). No calculator, no S2 cell, no node access. Every fix has a self-test
case; each was shown to fail on the original code by running the reviewers' reproducers against the original files
(logs in the private record folder).

| finding | severity | verdict | what was done |
|---|---|---|---|
| R2V-1: a §11 partner without a final geometry (missing, not run) recorded its children as failing check 5, so K3 gave fail_replan where the plan and I-C1 give a1_only | error | applied | `validate-a2` refuses V⁺_R, D and D+V without the partner's final geometry (a recorded check-5 failure always comes from an evaluated check); the runner skips the check job when the partner ended without one; I-F1, I-C1; 46 jobs-mock, 49 K2/K3, 50 (q) |
| R2V-2: an SCF failure at k = 0 completed the relaxation without a final geometry and its check job STOPped the campaign at every relaunch | error | applied | the check is skipped for a relaxation completed without a configuration; `run_a2v` STOPs only if a recorded final geometry is missing or mismatched; 50 (q): K2 fail, C2 reaches CAMPAIGN_DONE without a STOP, the C3 precondition passes, host_R(136) without a geometry gives K3 a1_only |
| R2V-3: with two copies, a hard-cap refusal swept the pending check of the running relaxation to not_started_cap, so its complete quartet stayed invalid | error | applied | the §11 checks are exempt from the capped sweep (N-F8); 50 (r); generalised after round 2 to every job without node-hours (N-F14, D-S0-9; below) |
| R2V-4: the record said the attempt-1 A2 files of a step-0 repeat are archived; only the gate files are | minor | applied (text) | I-D1, §6 and the R2-F3 row corrected: the attempt-1 A2 records and outputs stay on the node |
| I-C1 stale (missed by the fixes lens; = S2R2-STAT-4): "A1-invalid takes precedence (fail_replan)" contradicted k3_eval and I-11 | minor | applied | I-C1 rewritten; 49 asserts the text |
| S2R2-STAT-1: a valid δ required valid A1 start cells, a condition §11 does not state and which is not fail-closed (one case gave Ca a validated "repels" the §11 rule withholds) | error | applied, fail-closed (conflict with D-S0-2 recorded in §9) | the analyst's reading is kept for every reported number; scripts/48 also evaluates the §11 literal reading and gives a validated class only when both give it (`a1_condition` in the output); A1-invalid starts of A2 cells are listed with the invalid cells; 48 case "A1 condition under both readings". Superseded after round 2 by D-S0-2 as revised (§9; below): the dual-reading construction is withdrawn |
| S2R2-STAT-3 (with the adjudicator's fail-open case): in multi-pose production the 10% rule counted (host, site, leg) units, not cells | error (adjudicated) | applied | the 10% rule counts cells (every relaxed start), the site rule is unchanged; I-16; 48 case: 5/336 does not trip, 28/160 trips and Cs gets no class |
| S2R2-STAT-6: the flag-equality assert could crash the one evaluation by rounding at the threshold | suggestion | applied | the calibrated tier uses the A1 flag and records a rounding flip (I-C12); 48 case at 85.193 meV |
| F1: on a full /data the STOP path raised inside its own handler, leaving KEEP_ALIVE (no idle stop) and orphaned children | error | applied | KEEP_ALIVE removed first, every STOP step guarded, KEEP_ALIVE removed at any exit, and by the poller after a runner death (N-12, N-D4); 50 (t) |
| M2 (missed): a STOP reason quoting a path broke the hygiene rule in campaign.json, so the STOP raised and drain() was skipped | minor | applied | the reason in campaign.json is redacted (`public_text`), the raw text stays in campaign.log; 50 (t) |
| F2 = R2-QE-1 (with the missed non-root-rank case): a pw.x error abort (no JOB DONE) was rerun from k = 0 twice; §11 says not rerun | error | applied | scripts/47 end class `pw_error` (final, unconverged early, STOP for a human; N-B4); the runner STOPs on any end without JOB DONE in the current boot without an exit request or an OOM kill, resolved by RESOLVE 'unconverged', 'rerun' or 'missing' (I-D6, N-D5); case (f) now driven by an OOM kill; 47 end-rule (WP2e prefix + banner, precedence after k = 200), 50 (s) |
| F3: the projection's MACE time per relaxation came from the C1 MACE-phase wall (host wave counted twice, stopped time between boots included) | error | applied | the runner passes only the point and H_spent; scripts/49 derives I-C7b from the C1 records (N-F9, I-24); 50 (u) |
| F4: OOM evidence looked for the wrapper's pid with a regex that could not match | minor | applied | the wrapper writes the command's own pid to `<rc>.pid`; regex fixed; A2 parts by pw.x ranks after the part's start (I-D7); 50 (v), (s) |
| F5: the C1 job count text (325 vs its own list of 338) | minor | applied (text) | §1 |
| F6: two real web host names in a 46 test string | minor | applied | placeholders |
| S1: `pgrep -f` in the wrappers could match the issuing shell | suggestion | applied | the relaunch tests the S2 lock first and excludes its own shell and parent; status reports liveness from the lock; 50 (t) runs the relaunch decision |
| S2: no wall-time limit on any child | suggestion | applied (STOP, nothing killed) | N-F13; 50 (x) |
| S3: the cells of an invalid S2 host still run | suggestion | applied (a reading) | N-F12: they run as planned, scripts/48 applies 'missing for every dopant' |
| S4: the commit check covered the checkout, not necessarily the running code | suggestion | applied | N-F11 |
| M1 (missed): SIGTERM (a reboot) became a STOP and `s2_relaunch.sh` then refused | minor | applied | N-F10: an interruption, campaign left running; SIGINT is the operator's STOP; 50 (t) |
| R2-QE-2 (with the missed first-failure race): a single point read while the queue moved its files STOPped the campaign | minor | applied | retried snapshot; try1 + try2 without .gaveup is missing once it persists and the runner writes .gaveup (N-B8); 47 single-points case, 50 (w) with the committed queue |
| R2-QE-3: the per-output N-B9 checks (Cl/Ca MD5, A2 electron count, A2 input name) had no caller | minor | applied (wired) | the runner passes the C1 MD5 record, the meta electron count and the label at every read; 50 (w) |

Self-test change without a finding: the simulated campaign's k = 200 exit-file case (e) depended on the runner
polling within the mock pw.x's last 2 ms; the mock now slows its last configurations (`tail_delay`).

The records of §§3–4 were regenerated after the round-2 fixes as described there (`scripts/52 all`, then
`scripts/51 run`): the decisions are unchanged (production lists, m05 sites Pb124 / FA28 / I49, Pb–Cl
`provisional_2.837`, raw T4 sha256 `0a77d73e…2841`, `GEOM_SHA` `58ebbd29…dafedf`, laptop MACE sha256
`01bfe221…5845`, pre-flight 164 cells, 66 pairs, 161 + 36 + 7 inputs, no failure); only the recorded script sha256
and the times of writing differ.

### After round 2: the analyst's decisions implemented (2026-11-04)

Two decisions of §9 taken after the round-2 review were implemented in scripts/48, 49 and 50 (no other file changed;
no calculator, no S2 cell, no node access). Each has a self-test case that fails on the round-2 files (§2).

| decision | what was done | cases |
|---|---|---|
| D-S0-2 revised (S2R2-STAT-1): δ validity follows §11 literally | scripts/48: `_a2_quartet`, `deltas` and `delta_far` validate a quartet by the end rule and the §11 final-geometry checks 2–5 only and report `a1_valid` and `a1_starts_valid` beside each δ; `evaluate` no longer re-evaluates under a second reading nor removes a class when two readings disagree (`a1_condition` removed); `a1_start_sensitivity` adds rule V with the A1-start condition to the reported items (`reported.a1_start_sensitivity`, labelled reported only); an A2 cell enters the invalid-cell table only when it is invalid by §11, with the validity of its A1 start beside it; the independent second implementation follows §11; NOTES I-10 in 48, 49 and 50 | 48 "A1 start validity reported, section 11 decides (round-2 STAT-1, D-S0-2 revised)": an A1-invalid start of Ca D(136) leaves Ca at m_d 2, "not resolved", I = [−26.6, 58.6] meV and every decisive number of the all-valid table, while the sensitivity row gives m_d 1, "repels", I = [35.8, 46.2] meV, equal to the decisive result with that δ dropped; an A1-invalid start of the far quartet leaves δ_far valid (K3 passes on the same records) and Sr's validated "repels", and the sensitivity row gives no class (C5) |
| D-S0-9 (round-2 open item N-C7): gates after a hard-cap refusal | scripts/50: `Runner.statuses` sweeps only `CAP_KINDS` (mace, sp, pw, a2) to `not_started_cap`; gates, §11 check jobs, scripts/46 geometry jobs, G1 cells, records and the UPF and foundation checks stay pending and run whenever their inputs are complete; N-F14 added, N-F8, N-D3, the header and the cap log line revised; scripts/49 N-C7 and `job_start_allowed` text | 50 (i): after a refusal a pw.x job is swept, a check, a gate and a G1 job are not; 50 (y): C2 with relaxations 1–4 done and H_spent 515 h: relaxation 5 refused, 5–10 `not_started_cap`, checks 5–8 skipped, all five gates evaluated (K3 a1_only, as scripts/49 gives on the same records), CAMPAIGN_DONE without a STOP, C3 runs and C4 does not; with the round-2 sweep K3 stays 'not started (hard cap)' |

The records of §§3–4 were not regenerated: they hold the sha256 of scripts/46 and 52 only, and the pre-flight
summary depends on scripts/46, 47, 51 and the graph builders of scripts/50, none of which changed (the C1–C4 graph
counts of 50 (k) are unchanged).

### Round 3 (2026-11-04)

Three lenses (C1 end to end, regressions of the round-2 fixes, coverage of every plan rule), each followed by an
adjudicator who reproduced every finding. The three items the adjudicators added as missed were reproduced by the
fixer before acting (the `smoke2.json` write window, the SIGTERM inside the statuses, the Δ_pose count term dropped by
`assemble`). No calculator, no S2 cell, no node access. Every fix has a self-test case that fails on the code before
round 3 (§2), and the reviewers' and adjudicators' reproducers were rerun against the files before round 3 and the
final files (logs in the private record folder, round 3). The C1 end-to-end simulation of the C1 lens (the real C1
graph from a fresh state to CAMPAIGN_DONE over three boots, on this laptop's case-insensitive volume, MACE and pool
single points fabricated, the reference cells through the mock pw.x) was rerun on the final files: the same counts
(164 MACE, 161 single points with the q = 0 row given QE's error banner missing, 4 smoke-test parts and the 2 at the
2x32 layout, 4 throughput runs, 5 gates), the same G1, gate-N and pose values, and now `gate:nrule` applied (n = 10)
with `gates/N.json` and `gates/nrule.json` side by side; the archive of that tree (161 labels, 330 structures) and
`scripts/49 verify` (5 gate files, 0 differ) pass.

(A) Items that affect what C1 runs or decides:

| finding | severity | verdict | what was done | cases |
|---|---|---|---|---|
| R3-C1-1: the gate names N and n differ only in case; on the laptop's case-insensitive volume (pull, archive, verify, the one evaluation) `gates/N.json`/`n.json` and the markers `gate_N*`/`gate_n*` are one file each, so one record is lost; with the n-rule output under the name N, every dopant fails gate N in scripts/48 and no class is awarded at either tier | error | applied | the n rule is the gate `nrule` (scripts/49 `GATE_NAMES`, CLI, allow-list, `evaluate_gate`; scripts/50 `graph_c1`); `archive()` refuses names that differ only in case, a gate file whose `gate` field is not its name and a marker whose `id` is not its file name (N-F15) | 50 (z1); 49 gate runners; 48 assemble round trip (G1, N, nrule and pose files in one directory of this volume: gate N for all five dopants) |
| R3-C1-2: smoke test n1 or n3 missing: the throughput row crashed with `int(None)` at every relaunch; no RESOLVE for pw.x runs | error | applied | an explicit STOP naming the smoke tests; RESOLVE 'rerun <dated note>' or 'missing <note>' for a smoke, smoke2 or throughput run moves its parts, outputs and `tmp/` and the records built on them aside (N-F16) | 50 (z2) |
| R3-C1-3: no way to resume C1 at a fixed commit, which D-S0-8 prescribes | error | applied | `c1/NODE_FIX` ('<new commit> <dated note>'), accepted only for a stopped C1 and the checkout HEAD, logged in `commit_history` (N-F17); the operator's steps in §8 item 8 | 50 (z2): refused without it, accepted with it, refused for a C1 not stopped and in C3 |
| R3-C1-5: a smoke or throughput run ending with QE's error banner was rerun twice and logged as an interruption | minor | applied | a final end: missing at once, not rerun, not an interruption (N-D10, as I-D6) | 50 (z2): one attempt, no interruption |
| R3-C1-7: the spot-endpoint check tested the URL's form only | minor | applied | no job of a campaign before a good poll (200 or 404) of the endpoint; none within 120 s, or a last good poll older than 5 min, is a STOP (N-F18) | 50 (z3); the C1 lens' unreachable-endpoint scenario on the real graph now STOPs after 121 s with nothing run |
| missed (C1 lens): `smoke2.json` was written before its verdict was folded into `smoke.json`; a node loss between the writes left A2 the 48-rank restart verdict | minor | applied (reproduced) | the fold first, `rec:smoke2` done only with `at_layout` for its label, C2 requires `at_layout` at a layout other than 48 (N-F19) | 50 (z4) |
| R3-3: a shutdown SIGTERM while a synchronous child ran (a gate, a geometry job, validate-a2) became a STOP, the relaunch was refused, and the drain logged "still running" | minor | applied | the job stays pending, no marker, no STOP; a real STOP followed by SIGTERM exits as stopped (N-F21) | 50 (z6) |
| missed (regressions lens): the SIGTERM inside the statuses judged a part or attempt the shutdown had killed as an unexplained end in this boot (STOP) | minor | applied (reproduced) | a child found ended while the shutdown flag is set is not classified (A2 part, MACE attempt, pw.x reference run): the relaunch judges it as an earlier-boot interruption (N-F21) | 50 (z7) |
| R3-C1-4: a missing n silently gave 8 production hosts | suggestion (adjudicated) | applied | `production_hosts` needs n of 8 or 10; C3 requires the C1 `gate:nrule` marker (N-F24) | 50 (z11) |
| R3-C1-9: a KEEP_ALIVE left by a runner that died with its node survived a refused relaunch | suggestion | applied | `s2_relaunch.sh` removes a KEEP_ALIVE older than the boot when it refuses (N-F25) | 50 (z12) |

(B) Items that affect only C2–C4 or the analysis (I-D9 applies to every campaign, but at about 29 node-h C1 is far
from the cap):

| finding | severity | verdict | what was done | cases |
|---|---|---|---|---|
| R3-1: at 2x32, a STOP-asking end (QE's error banner, an early nstep, an unknown JOB DONE end) of the K2 cell or a K3 cell raised the STOP before K2/K3 ran; the drain then waited for the running partner to finish and its output was read at the relaunch | error | applied | the STOP is held until no gate, check or other job without node-hours of the phase is ready (the gates on the ended cell apply first), nothing costly starts meanwhile, a stopping gate puts the exit file on every running part at once and the drain records it killed_by_gate (N-F20); the sub-case of an end without JOB DONE in this boot (adjudicated plausible only: a human may answer 'rerun') is unchanged, a STOP for a human | 50 (z5): K2 cell and K3 cell (Sr D+V(76)) with the banner, the running copy killed_by_gate in 0.1 s; the bfgs_failed control unchanged; 50 (s) revised |
| R3C-1: at 48 ranks relaxation 9 (Ca D(136)) was launched in the tick in which the last check before K3 ran | error | applied | a section 11 check ends the scheduler tick (N-F22) | 50 (z8): K3 fail_replan, relaxations 9–10 not_run_gate and never launched; K3 pass, 9 launched after K3 |
| R3-8: OOM evidence by task name could attribute copy A's OOM kill to copy B | suggestion | applied | the process tree of each running part is recorded (launch record, `a2_pids.json`); an OOM is a part's only for its own pids, else the task test without the other copy's pids (N-F23) | 50 (z9) |
| R3-7: the dead status `skipped_a1_invalid` in scripts/49 and 50 (the stale spec copy: refuted by the adjudicator) | suggestion | applied (code) | removed from both; a dated note in the working specification and a pointer in the private record folder | 50 (z12) |
| R3C-2: the independent implementation did not recompute the C2 statistics, the per-site intervals or the control decisions | minor | applied | Δ_h, SD(Δ_h)/√2, mean(Δ_h), the per-site intervals at both tiers, C1–C5, n_d, the validated and the shown class compared at 10⁻⁶ meV on five tables | 48 independent implementation; a mutation of the √2 or of the strict < fails the self-test |
| R3C-3 and the missed item of the coverage lens: N_D, N_D+V and the count term were not reported beside the aggregated E_b, and `assemble` dropped them from Δ_pose | minor | applied (reproduced) | beside every aggregated E_b of the per-site and noise rows, in the pose pilot and `pose_note` (N-F26) | 48 count term and ledger; assemble round trip |
| R3C-4: the zero-shot MACE ledger covered the production and noise-pilot cells only | minor | applied | a pilot section: the m30 and m05 calibration start-set quartets beside the A1 DFT E_b from k = 0 of A2, and the pose-pilot sites (N-F27) | 48 count term and ledger |
| R3C-5: residual forces as RMS and max only | minor | applied | the free atoms' per-atom norms with their indices (scripts/47 N-B18), reaching `s2_eval.json` (N-F28) | 47 single points; 48 assemble round trip |
| R3C-6: the one-evaluation guard did not compare scripts/46–49 with the campaign commit | minor (adjudicated) | applied (adjudicated form) | the campaign commit and the diff recorded beside HEAD; a difference refused unless `--amendment` names a committed, dated note (N-F29) | 48 evaluation guard (temporary git repository) |
| R3C-7: after the first cap refusal every node-hour job was swept, also one that fits, unrecorded as a reading, in memory only | minor | applied as a recorded reading, confirmed (D-S0-10) | I-D9 (§5); the refusal persists in `HARD_CAP.json` across starts | 50 (z10) |
| R3C-9: N-C11 cited §14 for the §15 rule; a comment cited N-D12; the spec's I-10 stale | suggestion | applied | N-C11 §15, N-D10, the working specification's note | Appendix A |
| R3C-10: rules implemented but exercised by no case | suggestion | applied, one part left | the coverage reviewer's tests A–F and exact-threshold C2 cases (48), the precondition matrix (50 (z11)), the K3 order (50 (z8)), the path-work, determinism, q = 0 and WP2c rows (48); the determinism row's displacement against the WP1 structure archive is still exercised by no case | 48 boundaries, reported rows |

Not acted on (not in the adjudicated set handed to the fixer): the regressions lens' remark that a pw.x error end is
finalised before the human of its STOP sees it (so RESOLVE is never read for it), the MACE watchdog limits against
the §5 step caps, a full /data turning published single points into missing cells, and an operator's `kill`
(SIGTERM) being indistinguishable from a shutdown.

The records of §§3–4: scripts/52 and the records it writes depend on scripts/42, 22, 29, 07, `checks.py`, 46 and 52,
none of which changed in round 3, so they were not regenerated (decisions unchanged by construction). The pre-flight
depends on scripts/47 and the graph builders of scripts/50, which changed: `scripts/51 run --allow-provisional` was
run again; its summary equals the earlier one except the wall time (6.6 s) and the time of writing (164 cells, 66
pairs, 161 + 36 + 7 inputs, the same graph counts, failures none).

### Round 4 (2026-11-04, after the Stage-0 commit e257cdf)

A dated follow-up to the committed Stage-0 code, made before any S2 calculation. Three lenses (the C1 path of the
round-3 diff, the node runbook, the C2–C4 and analysis path of the round-3 diff), each followed by an adjudicator who
reproduced every finding. The four items the adjudicators added as missed were reproduced by the fixer on e257cdf
before acting: the spot notice inside one scheduler pass, the 2x32 rate from two walls that never overlapped, and the
gate exit that did not replace an earlier 'cap' or 'spot' request, by running their reproducers; the binding recipe
that works on this node (`taskset` with `--bind-to none`; OpenMPI 5.0.11 refused `--cpu-set` and `--map-by pe-list`), from
the node records of 2026-10-27 (read, not rerun: no node access). No calculator, no S2 cell, no node access. Every fix
has a self-test case that fails on e257cdf: the round-4 cases of scripts/50 ((z13)–(z27) and the extended (z2)), 48 and
49 were spliced into the e257cdf files and fail there, each on its defect, or because the API they test is new: (z17),
(z21) and (z22). The scripts/48 coverage case of R4-C24-6 passes on e257cdf, whose rule was right, and fails on each of
the three mutations it guards against. The reviewers' and adjudicators' reproducers were rerun against e257cdf and the
final files (logs in the private record folder, round 4). Each shows the defect on the former and not on the latter.
The reproducers that start an outage 55 s after a 60-s heartbeat write cannot start one on the final code, whose
heartbeat is never more than one poll old; (z13) uses a fixed clock instead.

(A) Items that affect what C1 runs or decides:

| finding | severity | verdict | what was done | cases |
|---|---|---|---|---|
| R4-C1-1 (node lens): the two concurrent 32-rank throughput copies each ran `mpirun --bind-to core -np 32` through the node's run_qe.sh with no core set, so both were bound from core 0 to the same 32 cores and 32 cores stayed idle; the 2x32 rate (and the layout of every A2 relaxation chosen from it) was biased against 2x32, and at 2x32 every A2 pair would have been time-shared | error | applied | N-F30: every pw.x run outside the queue goes through the committed `ehpc/node/s2_run_qe.sh` (the node's run_qe.sh with an optional core set, used from the checkout); each of two concurrent copies (np32a/np32b, every A2 part at 2x32) runs on one half of the physical cores (lscpu) with `taskset -c <half> mpirun --bind-to none`, a part taking the half no running copy uses; every other run keeps `--bind-to core`; the core set, the CPUs the pw.x ranks were allowed (node /proc) and the interval are recorded | 50 (z17): the simulated campaign's np32a/np32b on 0-31 and 32-63, 12 other runs bound as run_qe.sh; a free half at 2x32 |
| node lens, missed: a copy cut alone (an OOM of one copy, say) was rerun alone after the other had finished, and the 2x32 rate combined two walls that never overlapped | minor (reproduced) | applied | N-F30, I-C13: the two copies always start together (a copy that completed without the other is moved aside to `discarded/paired_<t>`, its measurement not used and not one of its reruns; with the other missing it is skipped); the 2x32 rate is computed by scripts/50 and by scripts/49 only for two copies with recorded, disjoint core sets (and disjoint recorded CPUs) whose walls overlap for at least 90% of the shorter one ([M], `TP_PAIR_OVERLAP`), else it is None and 2x32 is not chosen | 50 (z17): solo rerun, missing or shared core set, shared CPUs give no 2x32 rate; 49 throughput: the same and 90.0% / 89.97% overlap |
| R4-C1-1 (C1 lens): the 5-min staleness rule was measured on a heartbeat written every 60 s, so a 4-min metadata outage STOPped a healthy C1 and the reason misstated the age | minor | applied | N-F18: the poller writes its heartbeat at every good poll | 50 (z13): fake clock with the real limits: a 250-s outage 55 s after the old write, no STOP; 305 s, a STOP stating the true age |
| R4-C1-5 (C1 lens): smoke tests n1 and n3 with JOB DONE but not two configurations apart let C1 run to CAMPAIGN_DONE; C2 then STOPped and neither RESOLVE nor NODE_FIX could act | minor | applied (earlier than proposed: before the exit/restart test, whose restart nstep is derived from n1 and n3, as well as before the throughput row) | N-F38: a STOP naming the smoke tests and the NODE_FIX / RESOLVE path while C1 is open | 50 (z16): n3 converging at k = 1: STOP before the restart test and any throughput run; RESOLVE 'rerun' of n3 then gives slope 1, nstep_first 201 − c0 and the throughput row |
| R4-C1-2 (node lens): the node-only run_qe.sh, qe_queue.sh and chain.sh behind every pw.x run were never compared with the committed copies nor hashed | minor | applied | N-F31: check:nodescripts (no node-hours) records the sha256 of run_qe.sh, the QE profile, qe_queue.sh, chain.sh and s2_run_qe.sh in C1 and STOPs unless the queue, the chain and the launcher equal the checkout's copies; C2–C4 STOP on any hash that differs from the C1 record | 50 (z18): a queue one byte off STOPs C1 in its check phase with no pw.x run; C2 with a changed run_qe.sh STOPs |
| R4-C1-3 (node lens): a git failure in the checkout (a copy without .git, an ownership refusal) was read as a clean checkout with commit '' | minor | applied | N-F32: a STOP in the runner (HEAD must be 40 hex digits), a refusal in `s2_campaign.sh` | 50 (z19) |
| R4-C1-4 (node lens): after RESOLVE 'rerun' a smoke or throughput run had no interruption rerun left; an operator's MACE rerun after an exception used one of the two | minor | applied | N-F33: the attempts before a resolution go aside with it; an operator's MACE rerun is marked `counts: false` | 50 (z20) |
| R4-C1-5 (node lens): the OOM kill of a smoke or throughput rank was logged 'unknown' | suggestion (adjudicated) | applied | N-F34: those runs record their process tree like A2 parts; the A2 rule applies | 50 (z21) |
| R4-C1-6 (node lens): load_mace runs for the first time inside the two host relaxations, about 2.5 h into C1 | suggestion (adjudicated) | applied (the optional runner check) | N-F35: check:mace runs scripts/46 load_mace in a child process after the hash check (the runner never imports mace; no structure is evaluated); a failure STOPs before the smoke tests; §8 item 3 reworded | 50 (z22): on this laptop the empty-cache hash check fails before any child; reported and failing loads |
| R4-C1-7 (node lens): the memory headroom of two 232-atom copies (about 80 GB estimated each, 247 GB on the node) is unestablished | suggestion (plausible) | node check only (as adjudicated: no code; the row is not skipped by a note, since an OOM is already handled fail-closed and the concurrent-pair rule now keeps an OOM of one copy from becoming a solo measurement) | §8 item 9 | — |
| R4-C1-8 (node lens): before the first start `s2_status.sh` said 'running' and `s2_relaunch.sh` 'lock held' | suggestion | applied | 'not started (no /data/work/s2)'; the relaunch refuses with 'no S2 work tree' | 50 (z23) |
| R4-C1-9 (node lens): a boot used only to deploy or to pull has no heartbeat and is not counted | suggestion | applied as a runbook rule | §8 item 10; the ledger already counts manual.json entries | 50 (z23): an entry without a boot id counts and the ledger stays complete |
| R4-C1-2 (C1 lens): a poller restarted after it ended was judged at once against the dead poller's heartbeat | suggestion | applied | N-F18: the restart resets the poller's start, so its first good poll gets 120 s; no restart once a shutdown or STOP began | 50 (z13) |
| R4-C1-3 (C1 lens): a refusal of `s2_campaign.sh` itself inside a relaunch left a stale KEEP_ALIVE | suggestion | applied | N-F25: `s2_relaunch.sh` treats it as its own refusal | 50 (z23): the committed relaunch and campaign wrappers, paths rewritten, a checkout that is not clean |
| R4-C1-4 (C1 lens): a RESOLVE written into a live smoke or throughput run moved the live run's files and a second pw.x could start beside it | suggestion | applied | N-F16: RESOLVE is read only once no part of the run lives | 50 (z15) |
| R4-C1-6 (C1 lens): a commit change through NODE_FIX was not surfaced by campaign.json or scripts/48 | suggestion | applied (report only; the reviewer's refusal of scripts/46–49 changes inside a campaign is not adopted: it goes beyond D-S0-8) | N-F17, N-F39: campaign.json keeps `start_commit` and `commit_history`; scripts/48 reports the history with the diff stat of scripts/46–50 and ehpc/node of each step | 50 (z2); 48 evaluation guard |
| C1 lens, missed: a spot notice written during one scheduler pass did not hold the MACE launches later in the same pass | suggestion (reproduced) | applied | N-11: held() reads the notice itself | 50 (z14): the real C1 graph |

(B) Items that affect only C2–C4 or the analysis:

| finding | severity | verdict | what was done | cases |
|---|---|---|---|---|
| R4-C24-1: the STOP held by the A2 end rule (N-F20) lived in memory only; a SIGTERM or a second STOP within the hold lost it, and the relaunch launched the next relaxation with the mapping the end rule had flagged | error (adjudicated, from minor) | applied | N-F36: the A2 record carries `end_rule.stop_raised: false` until CAMPAIGN_STOPPED holds the reason; every runner start holds it again before any launch; every STOP's reason includes the held ones, which are then marked raised, so an operator's relaunch after that STOP does not raise them again | 50 (z24): (i) pw_error and (iv) nstep before k = 200 with SIGTERM in the hold: the relaunch STOPs with the reason, no launch; (ii) validate-a2 exiting 1 in the hold: both reasons; (iii) the operator's relaunch launches relaxation 4 |
| R4-C24-2: a process tree recorded before the pw.x ranks started made an OOM kill of a rank a false STOP for a human | minor (plausible) | applied | N-F34: the tree is recorded at every tick until it holds the part's pw.x ranks; a tree without pw.x ranks counts as not recorded (the task test, the other copy's pids excluded) | 50 (z25); (z9) unchanged |
| R4-C24-3: a relaxation waiting for its restart part when a gate stopped A2 became killed_by_gate with its output left, archived and parsed | minor | applied | N-F37: discarded unread like a running partner; N-F40: scripts/48 parses only complete A2 relaxations and gives a relaxation energy for complete cells only | 50 (z26); 48 pilot rows and killed A2 cells |
| R4-C24-4: the pilot hosts' Cs and Cl noise-pilot rows fell into the fail-closed multi-pose default and were always invalid; no Cs record on a pilot crashed the evaluation | minor | applied | N-F41: the pilot hosts' Cs and Cl cells are default-pose cells | 48: 40 noise rows equal gate N's E_b, 16 of them Cs and Cl, each with its MACE value |
| R4-C24-5: the amendment guard accepted any committed file with an ISO date (the plan, the changed script itself), dropped an amendment given with unchanged code, and stored only the diff stat | minor | applied | N-F29 revised: a committed, clean note outside scripts/, added or changed after the campaign commit, dated on or after it; recorded also with unchanged code and cited by the D3(BJ) row; the diff's sha256 in s2_eval.json and the diff beside it | 48 evaluation guard |
| R4-C24-6: two mutations of rule V (the calibrated sign rule on Y_h, 'repels' at lo ≥ 25.7) passed the scripts/48 self-test | suggestion | applied (coverage; the code was right) | a calibrated-tier table where the shift by δ̄ decides the class, and the strict class bounds at ±25.7 meV | 48: the case fails on each of three mutations (also hi ≤ −25.7 for 'binds') |
| C2–C4 lens, missed: a stopping gate kept an earlier 'cap' or 'spot' exit request of the running partner, whose output was then read and recorded complete | minor (reproduced) | applied | N-F37: the gate's request replaces it (the prior reason kept) | 50 (z27) |

Nothing was rejected. Not exercised on the laptop, besides the paths listed above (round 1): the launcher's `taskset` and
mpirun recipe with real ranks, the node /proc reads of the process tree and of `Cpus_allowed_list`, lscpu, and
load_mace inside check:mace (its failure path and its record are tested; §8 item 9 gives the node checks).

The records of §§3–4: scripts/52 and the records it writes depend on scripts/42, 22, 29, 07, `checks.py`, 46 and 52,
none of which changed in round 4, so they were not regenerated (decisions unchanged by construction). The pre-flight
depends on scripts/47 and the graph builders of scripts/50; the builders changed (one check job per campaign, which
counts no cell), so `scripts/51 run --allow-provisional` was run again (§4).

### Round 5 (2026-11-04, after the round-4 follow-up bfaf321)

A dated follow-up to bfaf321, made before any S2 calculation. Two lenses (the C1 path and the C2–C4 and analysis path
of the round-4 diff), each followed by an adjudicator who reproduced every finding. The minimal-fix rule of this round:
every adjudicated error and every C1-affecting minor is fixed, C2–C4 minors only when the change is small, suggestions
are recorded. The two items the adjudicators added as missed were reproduced by the fixer on bfaf321 before acting: the
exception name of check:mace, with the real child process against a scripts/46 copy whose load_mace raises S2Error
before any import (no mace or torch imported); the rerun's analysis diff, with cmd_evaluate run twice with its git
guards stubbed. No calculator, no S2 cell, no node access. Every fix has a self-test case that fails on bfaf321 (the
round-5 cases spliced into the bfaf321 code, §2). The reviewers' and adjudicators' reproducers were rerun against
bfaf321 and the final files (logs in the private record folder, round 5): each shows the defect on the former and not
on the latter. The adjudicator's reproducer of R5-2 that changes a node script without a NODE_FIX gives the same STOP on
both, as it should: without a NODE_FIX, C2 must STOP on a changed script.

(A) Items that affect what C1 runs or decides:

| finding | severity | verdict | what was done | cases |
|---|---|---|---|---|
| R5-1 (C1 lens): a spot poller that ended before its first good poll at every restart renewed the 120-s grace at each restart (the round-4 R4-C1-2 reset), so C1 neither started a job nor STOPped while KEEP_ALIVE kept the node up; a round-4 regression (e257cdf STOPs once the last good poll is 5 min old) | minor (error-class by consequence; no node cause found) | applied as adjudicated | N-F18: at a restart the grace is renewed only if the dead poller had a good poll of its own (a heartbeat not older than its start, the 1-s rounding tolerance kept); pollers that never answer keep the first one's start, and spot_check STOPs spot_first_s after it. The round-4 restart cases are unchanged (a dead poller with a 310-s old heartbeat is restarted with its own grace) | 50 (z13 c): after one good poll every restart runs `/usr/bin/false`: a STOP 1.0 s (spot_first_s) after the first restart, nothing run before it; bfaf321: no STOP in 6 s |
| R5-2 (C1 lens): the C1 check records were written once and kept through a NODE_FIX, so after a committed fix of the launcher the C1 record kept the old hash and C2 STOPped at every start on 's2_run_qe.sh changed since the C1 record', with no documented step to clear it; a NODE_FIX changing the committed qe_queue.sh or chain.sh was never compared with the node copy in C1 (adjudicator) | error (adjudicated) | applied as adjudicated, with the optional C2 part | N-F31: a commit change (`c1/NODE_FIX`; `c2/STEP0_FIX`) moves that campaign's upf, nodescripts and mace check records to `<c>/discarded/commit_<t>/` (not archived); the check phase is the first of every graph, so the checks run again at the new commit before any further job, and the C1 record describes the scripts in force at the end of C1 (§8 item 8) | 50 (z28): a NODE_FIX changing s2_run_qe.sh: check pending, the new sha256 recorded, C2 passes; a NODE_FIX changing the committed qe_queue.sh with the node copy old: STOP 'qe_queue.sh differs from the checkout's' in the check phase; a C2 STEP0_FIX moves the C2 records alike; bfaf321: the check stays 'done' (also with only the STEP0_FIX line reverted). 50 (z2): the three checks run again after its NODE_FIX |
| C1 adjudicator, missed (M-1): every S2Error raised in check:mace's child was recorded as 'exit without a traceback': the child loads scripts/46 under the name 'c46', so its traceback ends 'c46.S2Error: …', which the pattern did not match | minor (reproduced by the fixer) | applied | N-F35: the pattern accepts a qualified name; the record names 'S2Error' (and still 'ModuleNotFoundError' for a builtin) | 50 (z22): the failing child prints the qualified name, as the real child does; bfaf321: 'exit without a traceback' |

The self-test of R5-1 starts the failing restarts 1.8 s after the last good poll. A heartbeat within 1 s of a poller's
start counts as that poller's (the existing tolerance for the heartbeat's whole-second time), so within that second a
job may still start; the endpoint then answered less than 2 s before, which is not a defect.

(B) Items that affect only C2–C4 or the analysis (fixed):

| finding | severity | verdict | what was done | cases |
|---|---|---|---|---|
| R5-C24-1: the one-evaluation guard let `evaluate` run straight after C2 whenever C4 was not planned (K2 fail, step-0 fail_final, K3 a1_only, cut 8 at after4) and while C3 was still running, although §17 item 5 runs C3 first; the single evaluation would have used no, or partial, production records (pre-existing since e257cdf) | minor (adjudicated) | applied as adjudicated | N-F29: when C4 is not planned the evaluation needs `c3/state_end.json` (C3 ended) or `c3/campaign.json` with status not_run; otherwise it is refused ('C4 is not planned but C3 has not ended'); `_c4_ended` is in the case namespace, so the case can serve as a rerun cause. Operator rule: after K3 fail_replan, or an Sr gate-N failure, C3 (and for Sr also C2) is started once so that it records not_run (no job; best in the boot that ends the previous campaign) | 48 'one evaluation after C3 when C4 is not planned': refused in the four states and with C3 running; allowed after C3 ended and with C3 not_run; refused with C4 planned; bfaf321: allowed in the first state |
| R5-C24-2: the D3(BJ) row cited whichever `--amendment` was given, so on every planned rerun (which changes scripts/48) the rerun's code-fix note was recorded as the D-S0-4 amendment; a D-S0-4 note committed at or before the campaign commit could never be cited | minor (adjudicated: the inaccurate record is the code-fix citation; refusing an early note as `--amendment` is the round-4 rule for the code-diff role) | applied as adjudicated | N-F29: `--amendment` keeps only the code-diff role; `evaluate --d3bj-amendment PATH` (`d3bj_citation`: committed, clean, outside scripts/, with an ISO date, from any commit up to HEAD) is the only note the D3(BJ) row cites, with its path, sha256 and dates | 48 'D3(BJ) citation and the rerun's analysis diff': a note of the campaign commit cited; under scripts/, uncommitted and undated notes refused; the code-fix note not cited; bfaf321: the code-fix note cited |
| C2–C4 adjudicator, missed: a rerun wrote its analysis diff to the first evaluation's `s2_eval.analysis_diff.patch`, so the first `s2_eval.json` named a diff whose sha256 no longer matched (§17 item 6 'both outputs are archived', N-C8) | minor (reproduced by the fixer) | applied | N-C8: the output path is chosen once (`eval_path`, used by write_eval and for the diff); each diff is named after its own JSON (`s2_eval.rerun<k>.analysis_diff.patch`) and an existing diff file is refused (a diff left by an evaluation that failed before its JSON was written is removed by hand before the retry) | the same 48 case: both JSON files match their own diff files; bfaf321 (only the naming reverted): the first JSON's diff_sha256 no longer matches |

(C) Open before C2: none. Every adjudicated item and both missed items were small enough to fix in this round.

(D) Recorded suggestions (not applied, by the minimal-fix rule):

| finding | severity | verdict | fix instruction |
|---|---|---|---|
| R5-3 (C1 lens): a check:mace failure keeps no message: foundation_check calls mace_load without a log, so the child's output is discarded, the record keeps only the exception's name and the STOP reason is the generic 'the mace check failed' | suggestion (adjudicated) | recorded | `foundation_check(self, log=None)` passes the log to `mace_load`; `run_check` passes `log=os.path.join(self.cdir, 'mace_load.log')` for what == 'mace' (the log stays on the node: the archive publishes a fixed list of files); optionally the hygiene-redacted last traceback line in the record's `problems`, so that it reaches the STOP reason; self-test (z22): a failing child's message is in `c1/mace_load.log` and in no archived JSON. Until then §8 item 3 says how to read the message (a load by hand in the checkout); M-1 makes the recorded name right |

Nothing was rejected. Not exercised on the laptop beyond round 4: nothing new (the round-5 changes are runner logic,
a record's pattern and the analysis CLI, all exercised by the cases above).

The records of §§3–4: scripts/52 and the records it writes depend on scripts/42, 22, 29, 07, `checks.py`, 46 and 52,
none of which changed in round 5, so they were not regenerated (decisions unchanged by construction). The pre-flight
depends on scripts/47 and the graph builders of scripts/50, which did not change in round 5 (the round-5 changes of
scripts/50 are in the runner, the backend's model-load record and the self-test); `scripts/51 run --allow-provisional`
was nevertheless run on the final files: input digest `23b2614f…b6b0` and summary keys equal to `s2/stage0/preflight_c1.json`,
so the record was not rewritten.

### Round 6 (2026-11-04, after the round-5 follow-up 63a3511)

A dated follow-up to 63a3511, made before any S2 calculation. Two lenses (the C1 path and the C2–C4 and analysis path
of the round-5 diff), each followed by an adjudicator who reproduced every finding; no missed item was added. The
minimal-fix rule of round 5 was kept: every adjudicated error and every C1-affecting minor is fixed, C2–C4 minors only
when the change is small, suggestions are recorded. No calculator, no S2 cell, no node access. Each fix has a self-test
case that fails on 63a3511 (the round-6 cases run on the 63a3511 code, §2). The adjudicators' reproducers were rerun
against 63a3511 and the final files (logs in the private record folder, round 6): the poller life cycles with real
poller processes (every poller answering once and then killed: no STOP and 15 restarts in 30 s on 63a3511, a STOP at
the third renewal, 4.0 s, on the final files; pollers that never answer and a healthy poller unchanged), and a full
relaunch of the C1 lens' three-boot simulation with a NODE_FIX and one fabricated Cl single point whose printed Cl MD5
differs from the record (CAMPAIGN_DONE with that output 'done' on 63a3511; on the final files a STOP 'Cl MD5 1111… !=
0000… (UPF identity, I-25)', as on bfaf321; without the planted output the same relaunch reaches CAMPAIGN_DONE).

(A) Items that affect what C1 runs or decides:

| finding | severity | verdict | what was done | cases |
|---|---|---|---|---|
| R6-C1-1 (C1 lens): R5-2 moved `c1/upf_check.json` aside before the relaunch's first `statuses()` pass, so after an accepted NODE_FIX every existing C1 single point was read once without the Cl/Ca MD5 comparison (md5_extra None) and its terminal status cached: an output written with another Cl or Ca file than the recorded one was accepted 'done' and reached the gates, where bfaf321 STOPs (N-B9: the runner passes md5_extra at every read) | minor (adjudicated) | applied (the finding's alternative) | N-F31, N-B9: while `c1/upf_check.json` is absent or has not passed, md5_extra is the newest passed record in `c1/discarded/commit_*/`; when check:upf passes again at the new commit with other Cl/Ca MD5 than the record the outputs were read with, C1 STOPs. The Cl and Ca files are pinned by sha256, so on a correct path the two are equal. The alternative was taken over priming md5_extra inside discard_checks because it also covers a relaunch after a re-check that failed (the record then exists but has not passed) and adds no step between the commit save and the move (R6-C1-3) | 50 (z28): after the NODE_FIX a fresh runner's md5_extra is the moved record's, and a re-check giving other MD5 STOPs naming N-B9; 63a3511: md5_extra None |
| R6-C1-2 (C1 lens): the R5-1 rule still renewed the 120-s grace at every restart when each poller answered once and then ended: the restarted poller had not polled when the same pass's spot_check ran, so nothing was scheduled, and good polls kept coming, so nothing STOPped while KEEP_ALIVE held the node; a round-4 regression that R5-1 did not cover (e257cdf schedules in this regime) | minor (error-class by consequence; no node cause found) | applied as adjudicated | N-F18: the renewals of the grace are counted, and the third within spot_stale_s (300 s) is a STOP 'the spot poller keeps ending after a good poll', raised before any further restart; pollers that never answer (R5-1) and a single renewal (R4-C1-2) keep their recorded behaviour. The round-5 wording of (z13 c) in §2 is corrected: after one good poll of the first poller, restarted pollers that never answer | 50 (z13 d): every poller answers once and ends (a stand-in poller, the real limits): a STOP at the third renewal, nothing run; 63a3511: no STOP in 8 s, nothing run |

(B) Items that affect only C2–C4 or the analysis (fixed): none.

(C) Open before C2: none.

(D) Recorded suggestions (not applied, by the minimal-fix rule):

| finding | severity | verdict | fix instruction |
|---|---|---|---|
| R6-C1-3 (C1 lens): node_fix saves the new commit in state.json before it renames NODE_FIX and before discard_checks (the STEP0_FIX branch alike), so a runner killed between them (SIGKILL, the OOM killer, a power loss; SIGTERM only sets a flag) or failing there (ENOSPC at the makedirs of `discarded/`, a STOP) keeps the old check records at the new commit: the checks stay 'done', C2 then STOPs on 's2_run_qe.sh changed since the C1 record' (the R5-2 defect), and NODE_FIX may stay unconsumed; the window is a few file operations | suggestion (adjudicated) | recorded | call `self.discard_checks('c1')` in node_fix right after the refusals, before the commit_history append, save_state and the NODE_FIX rename, and `self.discard_checks('c2')` in the STEP0_FIX branch of check_commit before the commit_history append and save_state (the move is idempotent: after a kill between the move and the save, the relaunch accepts the NODE_FIX that is still there and finds nothing to move); self-test (z28): os.makedirs raising ENOSPC for the `discarded/` path during check_commit, then a fresh runner's check_commit accepts the NODE_FIX and check:nodescripts is 'pending'. Until then §8 item 9 (*After a NODE_FIX*) says how to recognise and clear it |
| R6-C24-1 (C2–C4 lens): d3bj_citation checks the path with git but reads the text with open(), which follows a committed symbolic link, so a committed link outside scripts/ is cited with the text, sha256 and dates of its target (an untracked file outside the repository, or a note under scripts/); the date pattern also accepts impossible dates (2026-99-99) | suggestion (adjudicated; it needs a deliberately committed link, the repository holds none, and no class, gate or decision depends on the D3(BJ) row, D-S0-4) | recorded | in d3bj_citation, after the 'not committed' check, refuse a path p with `os.path.islink(p) or not os.path.isfile(p)` ('a symbolic link or not a file, not a committed note'); keep only dates that pass `datetime.date.fromisoformat`, so a note whose only dates are impossible is refused as undated; N-F29: 'a regular file, not a symbolic link'; optionally the same in analysis_guard's `--amendment` branch (round 4); self-test (the round-5 case 'D3(BJ) citation and the rerun's analysis diff'): committed `link_out.md` (a link to an untracked file outside the repository), `link_scripts.md` (a link to a note under scripts/) and `baddate.md` ('2026-99-99') refused, `d3bj.md` still cited with ['2026-11-04'] |

Nothing was rejected. Not exercised on the laptop beyond round 5: nothing new (the round-6 changes are runner logic
exercised by the cases and reproducers above).

The records of §§3–4 do not depend on the round-6 changes (runner logic and the self-test of scripts/50; no graph
builder, no scripts/46, 47 or 52 code changed), so they were not regenerated (decisions unchanged by construction);
`scripts/51 run --allow-provisional` was nevertheless run on the final files: input digest `23b2614f…b6b0` and summary
keys equal to `s2/stage0/preflight_c1.json`, so the record was not rewritten.

## 8. What remains for C1 (node items; not Stage 0)

1. **Commit** the Stage-0 code, this record and `s2/stage0/` (§17 item 2), with the round-4 changes (bfaf321), the
   round-5 changes (63a3511) and the round-6 changes as dated follow-up commits (§7, rounds 4–6); check out that commit cleanly as a git checkout at `/data/work/ps_s2` (the first C1
   start records it, later starts must match; a copy without `.git` or any git failure is refused, N-F32).
2. **Pseudopotentials.** Copy `Cl.pbe-n-rrkjus_psl.1.0.0.UPF` and `Ca.pbe-spn-rrkjus_psl.1.0.0.UPF` from the
   private record folder to `/data/pseudo`; `scripts/47 upf-check` checks their sha256 against
   `PSEUDOPOTENTIALS_S2.md`, the S1 files by their MD5 and every z_valence, and records the node sha256 of all nine
   files for C2–C4, before the first pw.x job.
3. **MACE.** The node foundation file must have sha256 `01bfe221…5845` with mace-torch 0.3.16, float64, CPU and
   coverage of Z = 1, 6, 7, 17, 20, 38, 53, 55, 82: check:mace checks the hash and then runs `scripts/46 load_mace` in a
   child process, before the smoke tests (N-F35; no structure is evaluated); load_mace runs again at the start of every
   MACE job. A failed load is recorded with the exception's name (round 5, M-1) but not its message (R5-3, §7 round 5
   (D)): to read it, load the model by hand in the checkout (it builds the calculator and evaluates nothing).
4. **Spot endpoint.** `/data/setup/s2_spot_url` or the committed `node_step7.sh` in the checkout (X-5); the runner
   starts no job until the endpoint has answered (200 or 404) and STOPs if it has not within 120 s, or if its last good
   poll is more than 5 min old (the heartbeat is written at every good poll, N-F18). A poller that ends is restarted;
   pollers that end before answering keep the first one's start, so the runner STOPs 120 s after the first such
   restart (round 5, R5-1); pollers that each answer once and end STOP it at the third restart within 5 min (round 6,
   R6-C1-2).
5. **pw.x smoke tests** on the 232-atom reference cell at 48 ranks, before any S2 cell (§16): nstep 1 and 3, the
   exit-file stop and the restart with `disk_io = 'low'`; they fix the nstep mapping and whether restarts are
   possible (X-3); n1 and n3 that are not two configurations apart STOP C1 before the restart test (N-F38). Only
   counts, files and wall times are read.
6. **Throughput row** (§16): 5 configurations at 48 and 64 ranks and as two 32-rank copies, started together, each on
   one half of the cores (`ehpc/node/s2_run_qe.sh`, N-F30); the A2 layout is the fastest if it beats 48 ranks by at least
   15% (I-22), the 2x32 rate counting only for two copies on disjoint cores that ran together (I-C13), and the exit and
   restart test is repeated at the chosen layout if it is not 48 (X-4).
7. Then the C1 job graph of §1 (host relaxations, MACE phase, single points, gates G1, N, nrule and pose), with the
   keep-alive file present for the whole campaign; the node is stopped after the campaign (§17 item 5).

8. **A C1 STOP that needs a code fix** (D-S0-8; N-F16, N-F17). Commit the fix with a dated note and check it out
   cleanly; write `c1/NODE_FIX` holding '<new commit> <dated note>'; resolve the failed job: a smoke-test or
   throughput run with `smoke/<run>/RESOLVE` or `tp/<run>/RESOLVE` 'rerun <dated note>' (its parts, outputs and
   `tmp/`, its earlier attempts, and `smoke.json` and `smoke2.json`, or `throughput.json` and the throughput gate's
   markers, go to `discarded/resolved_<t>/`; a RESOLVE written while the run lives waits for its end), a MACE attempt
   with `cells/<work id>/RESOLVE` 'rerun <note>' (not one of the two reruns after interruptions, N-F33) or
   'missing <note>'; a failed UPF, node-scripts or foundation check needs nothing (its record is written again at the
   relaunch); then start `s2_campaign.sh c1`. An accepted NODE_FIX moves the three C1 check records to
   `c1/discarded/commit_<t>/`, so the checks run again first, at the new commit (round 5, R5-2): a fix that changes the
   committed `qe_queue.sh` or `chain.sh` needs the node copies in `/data/setup` made equal to the new committed ones
   before the relaunch, or C1 STOPs in its check phase. Until the UPF check has passed again, the existing C1 outputs
   are read against the moved UPF record's Cl/Ca MD5 (round 6, R6-C1-1). A step-0 fix (`c2/STEP0_FIX`) does the same for the C2 records;
   since C2–C4 compare the node scripts with the C1 record, a step-0 fix must not change `ehpc/node` or the node scripts. The runner accepts the new commit only while C1 is stopped and records it
   in `commit_history` (also in `campaign.json`, beside `start_commit`).

9. **Node checks before and during C1** (round 4; each settles a point the laptop cannot, D-S0-8). Run on the node, in
   the S2 checkout, and keep the output in the private record folder.
   - *Pre-launch status* (R4-C1-8): `bash /data/work/ps_s2/ehpc/node/s2_status.sh` prints
     `runner: not started (no /data/work/s2)` before the first start.
   - *The node queue scripts against the committed copies* (R4-C1-2, N-F31; round 5), before C1:
     `cmp /data/setup/qe_queue.sh /data/work/ps_s2/ehpc/node/qe_queue.sh && cmp /data/setup/chain.sh /data/work/ps_s2/ehpc/node/chain.sh`
     prints nothing. Any difference, a comment included, is resolved before the launch: check:nodescripts STOPs C1 on it.
      *Result on the node, 2026-11-04 (before the first C1 start):* qe_queue.sh equal; chain.sh different. The node copy
      (last changed 2026-10-26, after the commit of 2026-10-25 that added it here) passes an optional `NP` to the
      `[np]` argument that the committed qe_queue.sh already documents, `${NP:-}` unquoted, and differs otherwise only in
      two comment lines; with `NP` unset, as it is in the runner's environment (checked over ssh and in a login shell),
      the command is identical. Resolved by a dated commit that replaces `ehpc/node/chain.sh` with the node copy byte for
      byte (sha256 `7d5f0a21…a9402`), so that the repository records the script that runs, and has run every queue on the
      node since 2026-10-26; the node copy, shared with other work, is unchanged. That commit, which also holds this
      note, is the C1 campaign commit (C1 had not started, so no `c1/NODE_FIX` is involved); no S2 code, graph or input
      changed (the pre-flight input digest does not depend on chain.sh; the scripts/50 self-test passes, 60 cases).
   - *The launcher against the node's run_qe.sh* (R4-C1-2, N-F30):
     `diff /usr/local/bin/run_qe.sh /data/work/ps_s2/ehpc/node/s2_run_qe.sh` shows only comments, the `CPUSET`
     branch and the pseudo_dir rewrite through a temporary file. Any other difference, for example in the
     binding, the rank default or the profile, is resolved in a dated, committed change before C1. check:nodescripts then
     records the hashes and compares the queue and the chain (N-F31).
   - *The two-copy recipe* (R4-C1-1, the node lens' missed item), before C1:
     `source /etc/profile.d/qe.sh; for c in 0-31 32-63; do taskset -c $c $QE_ENV/bin/mpirun --bind-to none -np 32 bash -c 'taskset -cp $$' & done; wait`
     must print 32 lines ending `0-31` and 32 ending `32-63` (count them with `| awk '{print $NF}' | sort | uniq -c`).
     If it does not, C1 is not started; the launcher is fixed in a dated, committed change first.
   - *During np32a/np32b* (R4-C1-1; psr counts are not meaningful with `--bind-to none`):
     `for p in $(pgrep -x pw.x); do taskset -cp $p; done | awk '{print $NF}' | sort | uniq -c` shows 32 ranks on
     `0-31` and 32 on `32-63`; the runner records the same as `affinity` in the launch records, and the 2x32 rate is not
     counted if the two overlap (I-C13).
   - *Memory of the pair* (R4-C1-7): during np32a/np32b, `free -g | sed -n 2p` and
     `ps -C pw.x -o rss= | awk '{s+=$NF} END {printf "pw.x RSS %.1f GB\n", s/1048576}'`, recorded with the throughput
     row. Nothing is skipped on this evidence: an OOM is handled by the reruns of N-D10, and a copy is never measured
     alone (N-F30).
   - *Spot poller* (round 5, R5-1): `grep -c 'spot poller had ended' /data/work/s2/c1/campaign.log` stays 0 in a healthy
     campaign; restarts that never reach a good poll STOP the runner 120 s after the first one, and pollers that each
     answer once and end STOP it at the third restart ('the spot poller keeps ending after a good poll', round 6,
     R6-C1-2).
   - *After a NODE_FIX* (round 5, R5-2): `ls /data/work/s2/c1/discarded/commit_*/` holds the old check records, and
     campaign.log shows 'check upf: passed', 'check nodescripts: passed' and 'check mace: passed' again after 'commit
     change after a C1 STOP accepted'. If that line or the three checks are missing after the relaunch while
     state.json holds the new commit (a runner that ended between the commit save and the move, R6-C1-3, §7 round 6
     (D)), stop the runner (SIGINT), move `c1/upf_check.json`, `c1/nodescripts_check.json` and `c1/mace_check.json` to
     `c1/discarded/commit_<epoch>/`, rename a `c1/NODE_FIX` still present to `c1/NODE_FIX.used.<epoch>` and start
     `s2_campaign.sh c1` again: the three checks then run first at the new commit.
10. **Node-hours of boots without a runner** (R4-C1-9, §16 "boot to stop"). Deploy and launch in one boot, and pull
    within 60 min of CAMPAIGN_DONE (the idle self-stop). Any other S2 boot (one used only to deploy or only to pull)
    gets an entry `{"btime": <epoch>, "end": <epoch>, "note": "<what it was for>"}` in
    `/data/work/s2/ledger/manual.json` at the next boot, from `last -x reboot` or `journalctl --list-boots`; the
    ledger counts it.

## 9. Analyst decisions on the open Stage-0 items (2026-11-04, before any S2 calculation)

Decided on 2026-11-04 by the analyst, an AI assistant to whom the PI delegated the S2 choices, and recorded here as
given. D-S0-2 was revised and D-S0-9 added later the same day, after the round-2 review (finding S2R2-STAT-1 and
the open item on N-C7); the revised D-S0-2 replaces the earlier D-S0-2 text and the "For the analyst" paragraph that
set out the round-2 conflict, and both are implemented as recorded in §7 ("After round 2").

- **D-S0-1 Pb–Cl (I-E1; R1-F10, decision part): kept.** The record stays `provisional_2.837` [M] with
  `--allow-provisional`. Reason: the primary text was not read; a secondary value is not a verification under the
  design's tag legend; the two values differ by 0.0005 Å, three orders of magnitude below the 0.30 Å start
  displacements, and each start is relaxed; the m30 pose pilot (plan rule 9) decides whether shifted Cl minima
  matter. If the primary table is read before C1 builds the shifted Cl starts, `scripts/52 pbcl` is rerun first;
  otherwise the provisional value stands for S2.
- **D-S0-2 (revised 2026-11-04, after round-2 finding S2R2-STAT-1; R1-F5) δ validity, K2/K3 and A2.** As given:
  "D-S0-2 (revised) delta validity follows section 11 literally. A quartet is valid iff its four relaxations are
  accepted by the end rule and their final geometries pass the section 11 checks 2-5; m_d counts these deltas
  (section 14). The earlier stricter reading (a valid delta also needs valid A1 start cells) is withdrawn: the plan
  is not silent on quartet validity, and the stricter reading is not fail-closed, because dropping a delta can move
  delta-bar either way and narrow I_d (round-2 S2R2-STAT-1 reproduced a validated 'repels' for Ca that the literal
  reading leaves 'not resolved'). The 'both readings must agree' construction added in round 2 is also withdrawn:
  it adds a condition to rule V that the plan does not contain. The A1 validity of every A2 start cell is reported
  beside each delta, and rule V re-evaluated with the A1-start condition is reported as a sensitivity row in the
  reported-only part (section 15 style); no class, gate or decision rests on it. K2 and K3 are as the plan states
  (unchanged). This keeps delta_far validity identical to the K3 quartet validity, so the plan's own remark ('in
  practice K3 has already stopped A2 in that case') holds." As before, every planned A2 relaxation runs, K2 is the
  §11 end rule and K3 fails (re-plan) only on the value or on the §11 final-geometry checks 2–5. Implemented in
  scripts/48 (I-10; `reported.a1_start_sensitivity`) and in the I-10 notes of scripts/49 and 50.
- **D-S0-3 X-6 host validity: confirmed** (fail-closed: the 0.005 stage converges AND check 4 against the pool
  member passes).
- **D-S0-4 X-1 D3(BJ):** the row stays "not computed"; no dependency is added in Stage 0. Before the one evaluation
  (§17 item 6) a dated amendment either fixes an implementation (installed in its own environment, with version and
  file sha256 recorded) or states that the row is not reported. No class, gate or decision depends on it.
- **D-S0-5 Spot hold and hard cap with queued single points: accepted as recorded.** The exposure is at most two
  published single points (about 2 × 6.74 min at 64 ranks); the cap check counts each twice its expected time.
- **D-S0-6 X-3, X-4: confirmed.** The C1 smoke tests decide the nstep mapping and restarts; no A2 relaxation starts
  before `c1/smoke.json` exists and passes.
- **D-S0-7 R1-F9 rejection: confirmed** (literal §11 end rule; the end class and reason are stored for any later
  dated amendment).
- **D-S0-8 Node-only paths** (not exercisable on the laptop): C1 begins with the UPF check, the node MACE hash, the
  spot-endpoint check, a status call and the pw.x smoke tests on the reference cell before any S2 cell; any failure
  of a node-only path stops the campaign (fail-closed) and is fixed in a dated, committed change before C1 resumes.
  Implemented in round 3 (§7): the resumption at the fixed commit through `c1/NODE_FIX` (N-F17) with the operator's
  steps in §8 item 8 (the failed records resolved by RESOLVE, N-F16), and the spot-endpoint check as a reachability
  check (N-F18).
- **D-S0-9 (2026-11-04, the round-2 open item on N-C7) Gates after a hard-cap refusal.** As given: "after a hard-cap
  refusal, gates (G1, N, n rule, pose rule, step-0, K2, projection, K3, separability) and the section 11 check jobs
  cost no node-hours; they must never be swept to "not started" by the cap. They are evaluated whenever their inputs
  are complete. Only jobs that consume node-hours (pw.x, MACE) are refused by the cap." Implemented in scripts/50 as
  N-F14 (the throughput, c3_complete and c4_end gates and the other jobs without node-hours, i.e. the scripts/46
  geometry jobs, the G1 cells, the smoke and throughput records and the UPF and foundation checks, are treated
  alike) and recorded in scripts/49 N-C7; separability is evaluated by scripts/48 at the one evaluation, outside the
  runner.
- **D-S0-10 (2026-11-04, the round-3 reading I-D9) Hard cap after its first refusal: confirmed.** After the first
  hard-cap refusal in a campaign no further pw.x or MACE job of that campaign starts, and the refusal persists
  across runner starts (`HARD_CAP.json`). Reason: the job-start test of §16 uses each job's expected duration as a
  measured mean, and that mean changes as jobs end; a per-job test would make the set of computed cells depend on
  the order in which the graph reaches its jobs and on the current means, and could admit later a job it had
  refused, against "cuts are never undone" and the single end state of "whatever is then incomplete is missing". The
  confirmed reading never spends more node time than the per-job one, the cells it leaves missing follow the fixed
  graph order and never an energy, and jobs without node-hours still run (D-S0-9). The cut order of §16 is designed
  to keep P at or below 520 node-h, so the cap binds only if the projection was wrong; C1 (about 29 node-h) cannot
  reach it.
- **D-S0-11 (2026-11-04, the round-4 readings of §5) Two concurrent copies and reruns after a resolution:
  confirmed.** (a) The 2x32 rate of the throughput row counts only for two copies that ran on disjoint halves of the
  physical cores and whose walls overlap for at least 90% of the shorter one [M]; otherwise the rate is None and 2x32
  is not chosen. Reason: §16 asks for "two concurrent 32-rank copies", and only a pair that ran together measures the
  contention and memory of the layout that A2 would use; with both copies started in the same tick the overlap is
  the shorter wall, so the 90% bound only absorbs launch jitter and a copy rerun alone can never pass it. The
  failure direction is the planned default (48 ranks, or 64 if faster), never a layout chosen on evidence the plan
  does not describe. (b) An operator's 'rerun' after a STOP for a human (a MACE exception, or a smoke or throughput
  run resolved after a fix) is not one of the two reruns that §13 allows after a reclaim, node loss, OOM or wall
  time. Reason: those two reruns bound infrastructure interruptions; a resolution follows a diagnosed cause, needs a
  human and, for a code cause, a dated commit (D-S0-8), and is made before any output of the job is read (MACE
  energies are not read by the runner, and the smoke and throughput runs yield only counts and wall times), so it
  cannot select on a value. An A2 'rerun' stays counted (I-D6, N-D5).
- **D-S0-12 (2026-11-04, after round 6) The Stage-0 review loop is closed.** Rounds 1–6 found 6, 10, 5, 2, 1 and 0
  adjudicated errors; round 6 found none, and its two C1 minors lie on fault paths (a relaunch after a NODE_FIX, a
  spot poller that keeps ending) and were fixed with 20 lines of code, each with a self-test case that fails on
  63a3511 and the adjudicators' reproducers rerun. Each round's fixes have brought fault-path minors of their own
  (R5-1 from R4-C1-2, R6-C1-1 from R5-2), so a further laptop round on these 20 lines is expected to find more of
  the same kind while the node-only items of §8 item 9 stay unverified. Decision: no round 7; the code at the commit
  that holds this record is the C1 campaign code. The recorded suggestions (R5-3, R6-C1-3, R6-C24-1) are applied, if
  at all, only in dated commits before C2, by D-S0-8 and with a self-test case each. A defect found on the node during
  C1 follows the STOP, dated fix and `c1/NODE_FIX` route of D-S0-8 (§8 item 8); none is fixed in place. Reason: the
  plan's protections against a wrong number (blinding, the gates, rule V, the one evaluation) do not depend on these
  fault paths, every remaining item fails closed (a STOP for a human), and the node checks of §8 item 9 can only be
  settled on the node.

Cross-references: D-S0-1 settles §3.4 and I-E1; D-S0-2 the "Revised readings" bullet of §5, the §11 bullet and the
"Gates and statistics" bullet of §6, I-10/I-11, the R1-F5 and S2R2-STAT-1 rows of §7 and its "After round 2" table;
D-S0-3 X-6; D-S0-4 X-1; D-S0-5 the spot-hold and hard-cap bullets of §5 (N-D6, I-D2); D-S0-6 X-3, X-4; D-S0-7 the
R1-F9 row of §7; D-S0-8 §7 "Not exercised on the laptop" and §8; D-S0-9 N-F14, N-F8, N-D3 and N-C7, the
"Campaign operation" and §11 bullets of §6, the R2V-3 row of §7 and its "After round 2" table, and the round-3
reading I-D9 (§5) with D-S0-10; D-S0-11 the round-4 readings of §5 (I-C13, N-F30, N-F33); D-S0-8 also N-F16 to N-F18 and §8 item 8, and (round 4) N-F30 to N-F38 and §8
items 9 and 10, and (round 5) the re-check of N-F31 at a commit change and §8 items 4, 8 and 9, and (round 6) the renewal limit of
N-F18, the MD5 record of N-F31 after a commit change and §8 items 4, 8 and 9; D-S0-12 closes the review record of §7 (rounds 1–6).

## Appendix A. Every interpretation, implementation note and conflict in the code

Generated from the `NOTES` dictionaries of the seven scripts as they stand in this record (211 entries); each script prints its own with `--self-test`. Ids I-1 to I-48, N-1 to N-13 and X-1 to X-6 are those of the interface specification; I-A/N-A (module A), I-B/N-B/X-B1 (B), I-C/N-C (C), I-D/N-D (D), N-P (pre-flight), I-E/N-E (E) were added by the modules; I-F/N-F by the fixes of the six review rounds (§7; N-F15 to N-F29 and N-B18 in round 3, N-F30 to N-F41 and I-C13 in round 4; round 5 added no id and revised N-F18, N-F29, N-F31, N-F35 and N-C8; round 6 added no id and revised N-F18 and N-F31), N-F14 by the post-round-2 decision D-S0-9 (§9), I-D9 by round 3 as a reading, confirmed by the analyst as D-S0-10 (§§5, 9). A bar inside a text is shown as '/'.

### `scripts/46_s2_cells.py` (module A, cells; 35 entries)

| id | plan section | reading or note |
|---|---|---|
| I-1 | §4 | section 4 gaps asserted per host at the plan's rounded pool figures widened by half a last digit |
| I-2 | §4 | region 'within 6.0 A' is d < 6.0 (as scripts/40) |
| I-3 | §5 | the deleted I127 lies within 1.2 A of the UNRELAXED member's v (the relaxed-host test is trivial) |
| I-4 | §5 | host convergence = relax_staged's final-stage flag AND the strict max/F/ < 0.005 |
| I-5 | §5 check 5 | partner gating by relaxed-host positions (organic atoms at their molecule's C) from the relaxed-host centre; FA = molecules with 2 N found in the parent; appended dopant atoms not compared |
| I-6/X-6 | §5 | host valid iff the 0.005 stage converges AND check 4 against the pool member passes |
| I-7 | §5 labels | the A2 host cell of region j is s2r_&lt;h>_host&lt;L>&lt;j> |
| I-8 | §§5, 9 | o&lt;k> per leg; o0 reserved for p0 and kept as a minimum only if p0 is valid; map o&lt;k> -> p&lt;n> recorded |
| I-9 | §5 | Refused on relaxed partners rejects the pair like Inadmissible (site missing for that dopant) |
| I-39 | §4, answer 8 | mig='allow' at every X site |
| N-1 | header, §17 item 2 | calculators only on synthetic or reference cells (job runner: members ref233/synthetic) |
| N-2 | §5 | MACE only under the node root /data |
| N-3 | §§5, 9 | work ids p&lt;n> number the starts in b42.sampled_names order; p0 is the default pose |
| N-13 | §2 | 46 enforces --allow-provisional for the shifted Cl starts (42 enforces it only in its CLI) |
| X-2 | §2 | a verified Pb-Cl other than 2.837 A moves the shifted Cl along the s2b-2 direction to the source value, re-validated V1-V10; start_override and start_sha recorded beside GEOM_SHA |
| I-A1 | §5 check 4 | check 4 'within 1.25 / 1.6 A' (organic-inorganic) fails at d <= value, as the spec reads check 2's 'within 1.2 A'; the floor is the literal 'below 0.65 A' (fails at d < 0.65) |
| I-A2 | §5 check 3 | check 3 compares the dopant centre with its position in the cell's own builder output (the start of its relaxation); for A2 with the A1 builder output |
| I-A3 | §4 | ranking ascending by (round(d, 6), index): f1 = last, f2 = second last (no current set depends on it) |
| I-A4 | §11 | check 4 for an A2 cell compares with the start of its A1 relaxation (pool member for host_R); equal to comparing with the A2 start whenever the A1 cell is valid (topology equality is transitive) |
| N-A1 | §§5, 17 | relax_staged's log line (which prints MACE energies) is suppressed; energies only under E_mace_eV |
| N-A2 | §§4, 5 | the V+ cell keeps the MIG tag that pp.build_pair sets on the relaxed host; the unrelaxed member's migrating iodide is recorded beside it (with mig='allow' no admissibility outcome depends on it) |
| N-A3 | §4 | the four farthest sites are also asserted beyond the far bound (fail-closed; over the pool they lie at >= 9.73 / 10.14 / 10.45 A, section 4) |
| N-A4 | §§5, 17 | structure files carry no calculator results; the FIRE log has step and max/F/ only; files are read back from disk before use, so bitwise fixed-atom identity holds against the stored relaxed host |
| N-A5 | hygiene rule of Stage 0 | hygiene: JSON refuses any '$'; code is scanned for '$' next to a digit (shell variables are not currency) |
| N-A6 | §§5, 9 | job completion markers: region record, cells/&lt;id>/vac_start.json, pair record, cells/&lt;id>/record.json, cells/&lt;id>/validity.json, pairs/&lt;h>_&lt;T>&lt;j>_&lt;leg>.distinct.json |
| N-A7 | §2 | the Pb-Cl record is checked for internal consistency (decision vs value and level) fail-closed |
| N-A8 | §2 | verified Pb-Cl starts carry the record's level as their tag; provisional starts '[M] starting point' |
| N-A9 | §11 | c1_sites without an explicit m05_cal uses the plan's drawn sites and says so (source field) |
| N-A10 | §5 records | every record of this module is written through dump_public (hygiene) atomically |
| N-A11 | §5 check 4 | a structure with an element outside C, N, H and INORGANIC is refused by check 4 (no S2 cell has one) |
| N-A12 | §5 | job kind, pose and region keys are derived from the work id and Layout; given values must agree |
| N-A13 | §2 | X-2 override built from the centred Cl, so the shifted starts' admissibility is judged at the source Pb-Cl only (at d = 2.837 A it reproduces the s2b-2 shifted build to 1e-12 A) |
| I-F1 | §11 | section 11 final-geometry validity (review F1): validate-a2 runs checks 2-5 (host_R: 4) on the final geometry of an A2 relaxation against the final geometry of its partner (D and V+_R vs host_R, D+V vs V+_R), with the A1 start for checks 3 and 4 (I-A2, I-A4); a partner without a final geometry: the check is not evaluated (validate-a2 refuses to run without it, round-2 R2V-1), and the quartet is invalid through the missing partner |
| N-A15 | hygiene rule of Stage 0 | hygiene (review F10): a JSON record may carry no URL and no internet host name (any scheme://, or a dotted name ending in com, org, net, edu, gov, cn or uk; module names such as ase.io are not host names); sources are cited by reference and DOI |
| N-A14 | §§5, 9 | labels: o0 always names the p0 cell (single-start tokens and default-pose production get o0 at once); in a multi-start leg o0 is a kept minimum only if p0 is valid (I-8) |

### `scripts/47_s2_qe.py` (module B, QE; 26 entries)

| id | plan section | reading or note |
|---|---|---|
| I-25 | §6 | section 6 UPF identity: S1 UPFs by the MD5 printed in every archived S1 output (one per element); Cl, Ca by the sha256 of PSEUDOPOTENTIALS_S2.md; z_valence against the registry; C2-C4 against the C1 sha256 record |
| I-26 | §6 | section 6: every output must print pw.x v.7.5 and the expected MPI rank count, else S2Error (STOP) |
| I-48 | §11 | section 11: a part that ends by nstep before k = 200 is unconverged early (not rerun) and STOPs (mapping wrong) |
| X-3 | §§11, 13, 16 | sections 11, 13, 16: nstep is a parameter of the writer and of restart_input; its values come from the C1 smoke-test mapping; the parser cuts at k = 200 whatever nstep was |
| N-B1 | §6 | section 6 (silent): the composition must equal the label's (host formula, minus I127 if vacancy, plus the registry delta), in addition to the X-unit count and the electron count |
| N-B2 | §13 | section 13 (silent): write_input writes only fresh starts (restart_mode None or QE's default value); a restart part is made only by restart_input, and only restart_mode and nstep may differ from part 1 |
| X-B1 | §13 | spec 5.4 vs QE: the hygiene word rule matches QE's default restart_mode value (the word 'from_' + 'scr' + 'atch'); part 1 therefore writes no restart_mode line (QE default, a fresh start: the same calculation), restart_input adds the line restart_mode = 'restart' and changes nstep (section 13: differs only in restart_mode and nstep), and records give restart_mode null for a fresh start. The spec's a2 record field restart_mode = &lt;that word> (spec 4.5) cannot pass dump_public either |
| N-B4 | §11 | section 11 (silent on precedence): end class of a part: converged > cap > soft exit > nstep > pw.x error routine (QE's errore banner, round-2 R2-QE-1) > BFGS failure > SCF failure > other JOB DONE end > killed; a pw.x error end is unconverged early (section 11: 'any other end without QE convergence ... is not rerun') and STOPs for a human, who rules out an infrastructure cause; a JOB DONE end without a known marker is unconverged early and STOPs for a human (never rerun) |
| N-B5 | §§6, 11, 13 | sections 6, 11, 13: a configuration counts only with its '!' line and a complete force block (nat rows and 'Total force'); a trailing incomplete configuration is not counted (the interrupted one is not completed) |
| N-B6 | §13 | section 13: the part that reaches k = 200 is cut after configuration 200's BFGS block (before the ATOMIC_POSITIONS of configuration 201); nothing after the cut is processed, markers included |
| N-B7 | §13 | spec 7.2 (repeat tolerance): QE prints header positions at 7 decimals in alat units, so a repeated restart configuration is compared at 1e-6 A between ATOMIC_POSITIONS blocks and at 3e-6 A when a copy comes from a header block (spec: 1e-6 A flat); F at 1e-6 Ry, only in the full read |
| N-B8 | §12 | section 12: queue states qe_queue.sh does not leave (.gaveup beside .out, .gaveup without .out.try1 and .out.try2, .out.try2 beside .out without .gaveup, .out.try3, outputs without the input) STOP (S2Error); a snapshot taken while the queue moves files is read again (3 times, 0.5 s apart) first, and .out.try1 + .out.try2 without .out and .gaveup (the queue's state between its mv and touch) is missing once it persists, with gaveup_pending, so the runner writes .gaveup (round-2 R2-QE-2) |
| N-B9 | §6 | section 6: the printed electron count must equal the input's, the printed MD5 of each S1 element must equal UPF_MD5_S1 (Cl, Ca: the C1-recorded MD5, md5_extra) and the output must name its input (&lt;label>.in; A2 part n: &lt;label>.p&lt;n>.in), else STOP; the runner (scripts/50) passes md5_extra at every read, and the electron count and the label at every read of a single-point or A2 output (and of the smoke restart test), so each such output is checked once on the node (round-2 R2-QE-3); smoke and throughput outputs are of the reference cell; scripts/48 and 49 re-read outputs the runner has checked |
| N-B10 | §17 | section 17 (blinding): read modes counted in READS; ASE espresso-out only in the full read; final_geom uses this module's ATOMIC_POSITIONS/header parser, equal to ASE at every WP2e configuration (self-test) |
| N-B11 | §§6, 16 | sections 6, 16: s2_/s2g1_/s2spin_ are single points, s2r_/s2smoke_/s2tp_ relaxations; nstep must be an int in 1..1000; dopant_index only (and always) for s2spin_ |
| N-B16 | §16 | section 16 (spec 3.3): throughput rows only s2tp_ref232_{np48, np64, np32a, np32b}, each at its own rank count (np32a/b: 32, np64: 64, np48: 48); smoke rows any REF_RE name, at 48 ranks except rst64 (64) and rst2x32 (32) or an explicit count |
| N-B17 | §16 | header and section 16: a ref232 row (s2tp_, s2smoke_) must be the stored reference vacancy cell (results/fa_host/fa19cspb20i59_232_vI.extxyz: numbers and cell equal, positions within 1e-6 A); a pool member's V cell has the same composition, so the composition check alone cannot keep S2 cells out |
| N-B18 | §15 | section 15 residual forces (round-3 R3C-5): the full read of a single point gives, for the free atoms, the per-atom force norms (norms_eVA, in the order of their indices) beside RMS and max |
| N-B12 | §11 | section 11: the BFGS-failure texts are the QE messages as known, not seen in a pw.x 7.5 output; an end with JOB DONE and no known marker is caught by N-B4 |
| N-B13 | §13 | section 13: k comes from 'number of scf cycles' (k = N - 1) or 'bfgs converged in N scf cycles'; a later part must continue at k_last + 1 (or repeat k_last if the smoke mapping says so, both copies equal), else the parts are unusable and the relaxation reruns from k = 0; parts after a final end STOP |
| N-B14 | §6 | section 6 (silent): one label, one input: write_input refuses to replace an existing &lt;label>.in whose normalised text differs (rewriting the identical input is allowed) |
| N-B15 | §6 | section 6: ATOMIC_SPECIES carries ASE's default masses (as every S1 input), whatever masses the cell carries; masses do not enter scf or BFGS |
| I-B1 | §6 | section 6: tot_charge is written explicitly in every input, also 0.0 (as scripts/30 writes it) |
| I-B2 | §7 | section 7: 'the dopant atom is its own species' is met by requiring the dopant element to occur exactly once in the spin cell; refused otherwise |
| I-B3 | §6 | section 6: the MD5 that pw.x prints is the md5 of the UPF file bytes (QE md5_from_file); upf_check uses hashlib md5 [I]; every output's printed MD5 is also checked by the runner (N-B9) |
| I-B4 | §11 | section 11: a relaxation whose configuration 200 is complete is judged by the cap rule whatever ended the part (the driver's exit file at k = 200) |

### `scripts/48_s2_analysis.py` (module C, analysis; 31 entries)

| id | plan section | reading or note |
|---|---|---|
| I-10 | §§11, 14 | §§11, 14 (STAGE0 §9, D-S0-2 revised 2026-11-04): delta validity follows §11 literally: a quartet is valid iff its four A2 relaxations are accepted by the end rule and their final geometries pass the §11 checks 2-5 (validity_final written by scripts/50); m_d counts these deltas (§14), so delta_far validity is the K3 quartet validity. The A1 validity of every A2 start cell is reported beside each delta (a1_valid, a1_starts_valid), and rule V re-evaluated with the A1-start condition (a valid delta also needs valid A1 start cells) is a sensitivity row in the reported-only part (reported.a1_start_sensitivity, §15 style); no class, gate or decision rests on it. The round-2 construction (a validated class only when both readings agree) is withdrawn; the runner runs every planned A2 relaxation |
| I-16 | §12 | §12 dopant-specific rule: a first-shell cell (D_j or D_j+V of one start) fails if it fails check 2, 3 or 5 while V+_Rj and the host are valid; a rejected default-start pair counts as one failed cell per leg (I-C10); 'more than a quarter of the production hosts' at site j counts a host with any failing cell at j, '> n/4' with n the production list size; 'more than 10% of d's first-shell cells' counts cells (one per default-pose leg, one per relaxed start of a multi-pose leg: round-2 STAT-3) over the cells with valid V+_Rj and host; the A2 cells (pilot calibration cells, host_R and V+_R valid) enter a second evaluation of the 10% rule; either trip removes every class of d |
| I-17 | §14 | §14: per-site t intervals need n_j >= 2 (else null) |
| I-18 | §14 | §14: the A1-tier class is shown only when the A1-tier controls pass; the rule-V outcome is always reported |
| I-19 | §15 | §15 shared-region sensitivity: regions (B, A, X) with a dopant of two valid pilot-host quartets (m_d = 2) are counted; that count replaces df_delta in nu_d and in the a_far threshold; 0 -> null |
| I-20 | §14 | §14: 'entirely above' is lo > 25.7; 'positive' > 0; 'inside (-25.7, +25.7)' is open; 'G_d above' > -25.7 |
| I-38 | §§9, 12 | §§9, 12: a multi-pose leg aggregates over its kept minima (all valid starts' distinct minima) and needs every kept-minimum SP complete and at least one minimum |
| X-1 | §15 | §15 D3(BJ): no D3 implementation in the environment and no new dependency allowed; the row is reported as not computed (a dated amendment must fix an implementation before the one evaluation) |
| I-C7 | §14 | §14 A1-tier controls: 'Sr repels at the A1 tier' is read as Sr's displayed A1 class being 'repels' (Sr's rule-V outcome with its own C2, C3, C4, no flag and no no-class condition) |
| I-C8 | §14 | §14 C1: Sr's calibrated class counts after the no-class conditions (gate N, G1, dopant-specific rule) |
| I-C9 | §14 | §14 C2: with fewer than two valid production hosts SD(Delta_h) is undefined and C2 fails |
| I-C10 | §12 | §12: a rejected pair of the default start p0 (relaxed partners) counts as a failed unit in both legs (fail-closed); in multi-pose production a rejected non-default start is not a start (§9 'every admissible start') and does not count (review-1 F4) |
| N-C13 | §§6, 11 | §§6, 11: A2 relaxations are parsed with the C1 smoke-test mapping (c1/smoke.json), as by the runner and the gates; a relaxation of more than one part without that record is refused (review-2 F8) |
| N-C14 | §9 | §9: Cs or Cl without a recorded production pose mode counts as multi-pose (fail-closed), and the production modes must equal the pose gate under cuts 6/7 (review-1 F11) |
| N-C15 | §9 | §9: a kept minimum o&lt;k> (k >= 1) takes the MACE validity of the cell its distinct-minima record names (scripts/46 labels only the p0 record; review-2 F4) |
| I-C11 | §12 | §12 with §11: the A2 dopant units count a failure of any of the §11 final-geometry checks 2-5 of D or D+V (fail-closed); the A1 units count checks 2, 3, 5 as written |
| I-C12 | §14 | §14: the heterogeneity flag removes the class at the tier where it fires; Adding delta_bar shifts G_d and mean_j Ebar_d(j) equally, so the flag is evaluated once (A1) and used at both tiers; a calibrated-tier recomputation that differs by rounding at the threshold is recorded, never raised (round-2 STAT-6) |
| N-C6 | §14 | §14: a + b = 0 (no spread at all) leaves the interval undefined: not computed, 'not resolved' |
| N-C7 | §14 | §14 ranking: intervals carry no allowance (a_far, a_pose); reported only |
| N-C8 | §§11, 16 | §17 item 6: a rerun is written beside the first output as s2_eval.rerun&lt;k>.json; s2_eval.json is never overwritten; the analysis diff of each output is named after its own JSON (s2_eval.rerun&lt;k>.analysis_diff.patch) and never overwritten (round 5, the C2-C4 adjudicator's missed item) |
| N-C9 | §15 | §15 plateau-excluded intervals: delta values with a plateau-accepted relaxation (including delta_far) are dropped and delta_bar, s_delta, df_delta, a_far and every calibrated interval recomputed |
| N-C10 | §§11, 14 | §§11, 14: an invalid delta_far fails C5; the reported calibrated interval then carries a_far = 0 |
| N-F26 | §9 | §9 (round-3 R3C-3 and missed item): N_D, N_D+V and the count term k_BT ln(N_D/N_D+V) are reported beside every aggregated (multi-pose) E_b of the per-site rows and beside Delta_pose (the pose gate's near and far records kept by assemble, the pose pilot and pose_note) |
| N-F27 | §15 | §15 (round-3 R3C-4): the zero-shot MACE ledger covers every cell with MACE energies: the production quartets, the noise pilot, and (pilot section) the m30 and m05 calibration start-set quartets beside the A1 DFT E_b from k = 0 of their A2 cells and the m30 pose-pilot sites (default and kept-minima aggregate); all labelled zero-shot MACE, not re-admitted |
| N-F28 | §15 | §15 (round-3 R3C-5): the residual forces of every A1 cell carry the per-atom norms of the free atoms (scripts/47 parse_sp 'free': norms_eVA with their indices) beside RMS and max |
| N-F29 | §17 item 6 | §17 item 6 (round-3 R3C-6; revised in round 4, R4-C24-5): the one evaluation records the campaign commit (the latest state_end.json) beside HEAD with the git diff of scripts/46-49 between them (stat, sha256, and the diff itself beside s2_eval.json); a difference is refused unless --amendment names a committed, clean note outside scripts/ that was added or changed after the campaign commit and carries an ISO date on or after that commit's; a given amendment is checked alike and recorded also when the code is unchanged; the D3(BJ) row cites only a note given as --d3bj-amendment (D-S0-4; round 5, R5-C24-2: committed, clean, outside scripts/, with an ISO date, from any commit up to HEAD); the one evaluation runs only after C4 has ended or, when C4 is not planned, after C3 has ended or recorded not_run (round 5, R5-C24-1) |
| N-F39 | §§13, 17 item 6 | §§13, 17 item 6 (round-4 R4-C1-6): every commit change during the campaigns (state_end commit_history: c1/NODE_FIX, c2/STEP0_FIX) is reported in s2_eval.json analysis_identity with the diff stat of scripts/46-50 and ehpc/node between its two commits; report only, no refusal |
| N-F40 | §16 | §16 'output discarded unread' (round-4 R4-C24-3): only a complete A2 relaxation is parsed; a killed, missing or not-run one has no energies read (its outputs were moved aside unread), and the reported A2 rows give a relaxation energy for complete cells only |
| N-F41 | §§8, 11 | §§8, 11 (round-4 R4-C24-4): the Cs and Cl cells of the pilot hosts (noise pilot, start set) are default-pose cells: their pose mode is 'default', so their reported rows and MACE values use the o0 cells, as gate N does (the m30 pose pilot is reported apart); a pilot host without a Cs or Cl record cannot crash the evaluation |
| N-C11 | §15 | §15 required hosts: the smallest n in 2..1000 with t_{n-1}(q*) s_Y/sqrt(n) below k_BT (and k_BT/2); null when s_Y is undefined or no n <= 1000 suffices |
| N-C12 | §17 | §17: evaluate is a pure function of the table; assemble is the only reader of C3/C4 energies and of the MACE energies (records with blind=False) |

### `scripts/49_s2_gates.py` (module C, gates; 29 entries)

| id | plan section | reading or note |
|---|---|---|
| I-10 | §§11, 14 | §§11, 14 (revised after review F5; STAGE0 §9, D-S0-2 revised 2026-11-04): every planned A2 relaxation runs whatever the validity of its A1 start cell (the plan skips none); A1 validity enters no gate, class or decision: a delta is valid by the §11 rule alone (scripts/48), so delta_far validity is the K3 quartet validity, and the A1 validity of the start cells is reported (K2, K3 here; beside each delta and in the reported-only A1-start sensitivity row of scripts/48); K2 is the end rule of V+_R(Pb136) alone |
| I-11 | §11 | §11 K3 (revised after review F5): fail_replan iff E_b(136) - E_b(76) <= 25.7 meV or a quartet fails the §11 final-geometry checks 2-5 (validity_final); the A1 validity of the 8 start cells is reported only |
| I-F1 | §11 | §11 final-geometry validity: computed by scripts/46 validate-a2 (geometry only) once a relaxation and its §11 partner (host_R for V+_R and D; V+_R for D+V) have ended, from the final positions (scripts/47 read final_geom) and the A1 start, region, relaxed host and pair records; written by scripts/50 into the A2 record as validity_final; a partner without a final geometry (missing, not run, killed, or complete without a configuration): the check is not evaluated (no validity_final), and the quartet is invalid through the missing partner, so K3 is a1_only there (round-2 R2V-1) |
| I-F3 | §11 | §11 step-0 repeat: the decision carries the earlier step0 fields (repeat flag, fix note), so both cells of the repeat are evaluated as attempt 2; the fix note comes from the inputs or the state |
| I-12 | §8 | §8: a valid far site for gate N is a valid noise quartet (four SPs complete, the three MACE relaxations and the host relaxation valid) |
| I-13 | §§8, 17 | §§8, 17: gate N computes DFT values only; the zero-shot MACE values are reported by the one evaluation |
| I-14 | §9 | §9: a missing SP of a default or kept minimum at either pilot site makes the pose rule 'not met' (multi) |
| I-21 | §16 | §16 hard cap: the expected duration is the mean wall of completed jobs of the same kind in S2, else the §16 unit cost (A2 relaxation at the cap value 20.6 h) |
| I-22 | §16 | §16 throughput: rate = configurations per node-hour (two copies: 10 configurations over the longer wall, counted only as I-C13); chosen iff >= 1.15 x the 48-rank rate; a failed run -> 48 |
| I-24 | §16 | §16 projection: H_MACE = remaining frozen relaxations x the C1 MACE node time per frozen relaxation plus one host-relaxation wave while host relaxations remain, both as I-C7b (derived here from the blinded C1 records; scripts/50 passes no phase wall, round-2 F3); tau_SP = mean C1 SP wall |
| I-25b | §16 | §16 cuts: an inapplicable cut (5 at n = 8; 6, 7 without multi-pose) or one unavailable at that projection (5-7 at C4) is skipped and the next cut is tried |
| I-31 | §§7, 16 | §§7, 16: cells whose every dopant was removed (G1 failure, cuts) are not run, region cells included |
| I-C1 | §11 | §11 K3: a K3 relaxation without a complete output (missing after the reruns), or without a final-geometry check (its partner has no final geometry, round-2 R2V-1), is read as 'K3 cannot be evaluated' -> a1_only, like an end-rule failure; a quartet invalid by the §11 final-geometry checks 2-5 takes precedence (fail_replan); the A1 validity of the start cells is reported only (I-11) |
| I-C2 | §16 | §16 projection: tau_bar = sum of node-minutes / sum of configurations of the completed A2 relaxations (node-minutes = wall / concurrent copies), so c_bar x tau_bar is the mean node time of a completed one |
| I-C3 | §16 | §16 projection: multi-pose production enters at its upper bound (Cs 60, Cl 40 extra relaxations and SPs per host); a running A2 relaxation counts in full; with no completed A2 relaxation each planned one costs the cap value 20.6 h |
| I-C4 | §11 | §11 step-0: a missing standalone SP or k = 0 value counts as a failed check; attempt 2 requires a fix note; 'no error found' after attempt 1 gives fail_final; no attempt 3 |
| I-C5 | §16 | §16 throughput: of equal rates 64 ranks precedes two 32-rank copies; a failed 48-rank run gives 48 |
| I-C13 | §16 | §16 throughput (round-4 R4-C1-1 and the node lens' missed item): 'two concurrent 32-rank copies' is measured only by two runs that each recorded a core set, on disjoint cores (and, when recorded, with their pw.x ranks' CPUs disjoint and inside the sets), whose walls overlap for >= 90% of the shorter one ([M], TP_PAIR_OVERLAP); otherwise the 2x32 rate is None and the layout is not chosen (fail-closed: 48 or 64); scripts/50 starts the two copies together on the two halves of the cores (N-F30) |
| I-C6 | §16 | §16 cuts: cuts 1-4 are inapplicable once C4 will not run, and cut 7 once Cl has left the family (G1) |
| N-C1 | §§16, 17 | gate output: inputs_digest = sha256 over (label, content sha256 of the decompressed file, mode), without file paths, so the node and the archive give the same digest |
| N-C2 | §17 | Reader: energy read modes (full, k0, final) never open a production-host (C3) or A2-II (C4) label outside the one evaluation, whatever the allow-list; end_rule mode on C4 labels is allowed (§17) |
| N-C3 | Stage-0 loading rule | scripts/46 and scripts/47 are loaded on first use, not at import |
| N-C4 | §7 | §7 G1: a missing input (SP not complete, magnetisation not printed, UPF record absent or failed) fails that part for the element |
| N-C5 | §8 | §8: a dopant absent from the gate-N input fails gate N; an absent Sr sets sr_stop |
| N-C6 | §16 | §16: cut_order updates the state in place (cuts list, n, multi-pose flags, c4_run) and returns the applied cuts with P before and after each |
| N-C7 | §16 | §16 hard cap: the job kinds of scripts/50 (tp, g1, spin, geometry) are accepted as aliases; only jobs that consume node-hours (pw.x, MACE) are refused by the cap (analyst decision 2026-11-04, round-2 open item N-C7): scripts/50 never submits a gate (G1, N, n rule, pose rule, throughput, step-0, K2, projection, K3, c3_complete, c4_end), a §11 check job or another geometry-only job to job_start_allowed and never sweeps one to 'not started (hard cap)'; each is evaluated whenever its inputs are complete (separability is evaluated by scripts/48 at the one evaluation); 'geometry' (0 h) remains an accepted kind |
| N-C8 | §§11, 16 | CLI run (scripts/50): the step-0 cell, attempt and fix note, the projection point, H_spent (ledger snapshot; an incomplete ledger refuses, I-23) and the C1 timings are derived from the node files; these reads are listed as inputs_opened and do not enter the inputs digest; verify reuses inputs_in |
| N-F15 | §§8, 17 | §§8, 17 (round-3 R3-C1-1): the n rule is the gate 'nrule' (output gates/nrule.json, decision {n}); it was 'n', whose output gates/n.json and markers are the same files as gate N's on a case-insensitive volume (the laptop's APFS, where the pull, verify and the one evaluation run); no two names of GATE_NAMES fold to the same lower-case string (asserted) |
| I-C7b | §16 | §16 projection: the C1 MACE time per frozen relaxation is its mean wall / 10 concurrent relaxations (the §16 unit-cost reading, '17-27 min at 6 threads with 10 concurrent' = about 2 min of node time); a host-relaxation wave costs the longest C1 host wall (both hosts run concurrently) |

### `scripts/50_s2_campaign.py` (module D, campaign; 69 entries)

| id | plan section | reading or note |
|---|---|---|
| X-3 | §§11, 13, 16 | A2 needs c1/smoke.json with an affine nstep mapping of slope 1 and a restart that reproduces the uninterrupted count; otherwise restart_possible is false and every A2 interruption uses the rerun rule |
| X-4 | §16 | smoke tests at 48 ranks first, then the throughput row; if another A2 layout is chosen, the exit/restart smoke test is repeated at it (s2smoke_ref232_rst&lt;layout>) before C2 |
| X-5 | §§13, 16 | spot URL from the node-local /data/setup/s2_spot_url, else the SPOT_URL line of the committed scripts/wp3_runbook/node_step7.sh; it must start with http:// and end with /termination-time |
| I-10 | §§11, 14 | revised after review F5 and by D-S0-2 as revised on 2026-11-04 (STAGE0 section 9): every planned A2 relaxation runs, whatever the validity of its A1 start cell (the plan skips none); A1 validity enters no gate, class or decision (a delta is valid by the section 11 rule alone, scripts/48); it is reported by K2 and K3 (scripts/49) and beside each delta, with a reported-only A1-start sensitivity row (scripts/48) |
| I-F1 | §11 | section 11 final-geometry checks (review F1): when a relaxation completes, the positions of its last configuration (scripts/47 read final_geom, no energy) are written as &lt;label>.final.extxyz; once it and its partner (host_R for V+_R and D, V+_R for D+V) have ended, scripts/46 validate-a2 runs checks 2-5 (host_R: 4) and validity_final {valid, failed} is written into the A2 record; K3 waits for these checks; a partner without a final geometry (missing, not run, killed, or complete without a configuration) and a relaxation completed without a configuration (k_last None, e.g. an SCF failure at k = 0): the check is not evaluated (skipped, no validity_final), the quartet is invalid through the missing cell (round-2 R2V-1, R2V-2) |
| I-F6 | §16 | section 16 hard cap (review F6): the measured walls of every completed job of S2 so far are loaded from the files at each runner start (A2 records, MACE records, single-point outputs in status mode, smoke and throughput records), so expected durations survive a relaunch and carry across campaigns |
| I-F7 | §16 | section 16 'jobs already running finish' (review F7): the restart part of an A2 relaxation that had started is checked against the cap with the expected time of the configurations still allowed (201 - completed) x the measured wall per configuration (else 6.15 min); a rerun from k = 0 counts as a whole relaxation |
| I-F8 | §16 | section 16 node-hours (review F8): a past boot whose journal cannot be read ends at its last heartbeat + 60 s + 60 min (the idle self-stop) + 15 min, unless ledger/manual.json gives its stop time by boot id |
| N-F6 | §§6, 16 | N-6 implemented (review-2 F6): pw.x outside the queue starts only while the runner holds the global chain lock (passed to the child, released when none runs) and no pw.x it did not start is alive |
| N-F7 | §13 | section 13 restart (review-2 F7): a restart nstep below 1 (possible when c0 >= 1) is written as 1; the exit file at k = 200 and the parser's cut at k = 200 keep the cap |
| N-F8 | §16 | section 16 'jobs already running finish' (round-2 R2V-3): the section 11 checks (geometry only, seconds) complete a relaxation that was allowed to start; they run whatever the hard cap, so a cap refusal while a copy runs never leaves a completed relaxation without its validity_final (generalised by N-F14) |
| N-F14 | §16 | section 16 hard cap (analyst decision 2026-11-04, round-2 open item N-C7): only jobs that consume node-hours are refused by the cap and swept to not_started_cap: pw.x (single points, smoke and throughput runs, A2 parts) and MACE (CAP_KINDS); gates (G1, N, n rule, pose rule, throughput, step-0, K2, projection, K3, c3_complete, c4_end), the section 11 check jobs and the other jobs that cost no node-hours (scripts/46 geometry builds, the G1 cells, the smoke and throughput records, the UPF and foundation checks) are never swept and are evaluated whenever their inputs are complete (any end of their dependencies); separability is evaluated by scripts/48 at the one evaluation |
| N-F10 | §13 | section 13 (round-2 M1): SIGTERM (a reboot or a stop of the node) is an interruption, not a STOP: nothing new starts, it is logged in interruptions.jsonl, KEEP_ALIVE is removed, the runner waits for its children and exits with the campaign still 'running' and no CAMPAIGN_STOPPED, so s2_relaunch.sh relaunches it after the boot; an operator's STOP for a human is SIGINT |
| N-F11 | §17 item 2 | section 17 item 2 (round-2 S4): on the node the runner refuses to start unless it is the scripts/50 of the recorded checkout /data/work/ps_s2, so the commit check covers the code that runs |
| N-F12 | §5 | section 5 (round-2 S3, a reading): the cells and single points of a host whose S2 relaxation is invalid still run as planned (the runner reads no validity); scripts/48 applies 'missing for every dopant' through host_valid, so their values are reported only |
| N-F13 | §13 | section 13 'wall time' (round-2 S2): a pw.x output (A2 part, smoke or throughput run, single point) not written for 2 h while its process lives, or a MACE attempt running beyond 3 h (host relaxation 12 h), is a STOP for a human (nothing is killed); the operator ends the process and resolves with RESOLVE |
| N-F9 | §16 | section 16 projection (round-2 F3): the runner passes only the projection point and H_spent; scripts/49 derives tau_SP and the C1 MACE timings from the blinded C1 records (I-C7b: mean frozen-relaxation wall / 10 concurrent, the longest C1 host wall); no campaign phase wall (which would hold the host wave and any stopped time between boots) enters the projection |
| I-21 | §16 | expected durations from scripts/49 expected_hours(kind, measured walls of completed jobs of the kind) |
| I-23 | §16 | a counted boot without btime or heartbeat evidence makes the ledger incomplete: no job starts (STOP) |
| I-28 | §16 | see X-4 |
| I-31 | §§7, 16 | cells whose every dopant was removed (G1 failure, cuts) are not run, region cells included |
| I-48 | §11 | a part that ends by nstep before k = 200 is unconverged early and STOPs the campaign (mapping wrong) |
| N-5 | §12 | single points are published one input at a time (meta first, then &lt;label>.in.part renamed to .in) |
| N-6 | §§6, 16 | A2 relaxations, smoke tests and the throughput row run through the committed ehpc/node/s2_run_qe.sh (the node's run_qe.sh with an optional core set, round 4, N-F30) under the global chain lock |
| N-7 | §§5, 16 | MACE work never runs beside pw.x: phases are strictly ordered within a campaign |
| N-9 | §13 | a MACE attempt that ended with a Python exception (or a refusal) is a STOP for a human, not an interruption |
| N-10 | §§12, 16 | the hard-cap check of a single point uses twice its expected duration (one automatic resubmission) |
| N-11 | §13 | after a spot notice nothing new starts for 1800 s; running children continue; held() reads the notice itself, so a notice written while one scheduler pass runs its synchronous jobs holds every later launch of that pass (round-4 missed item) |
| N-12 | §16 | KEEP_ALIVE is removed at the end of a campaign, at every STOP (first, before any write: round-2 F1), at a shutdown signal, whenever the runner exits, and by the spot poller when the runner died without CAMPAIGN_DONE (SIGKILL, OOM; the poller removes only the file that runner wrote) |
| I-D1 | §11 | section 11 step-0: evaluated as soon as configuration k = 0 of the relaxation is complete; a failure stops A2 at once: the checked relaxation and any running partner are stopped by their exit files and marked killed_by_gate (outputs not read), nothing further starts; fail_pending_fix is a STOP for a human, resumed either with c2/STEP0_FIX ('&lt;new commit> &lt;dated note>'), after which C2 restarts at relaxation 1 for the one repeat (state 'repeat_pending', both cells checked as attempt 2; the attempt-1 A2 files and gate files moved to discarded/step0_attempt1_&lt;t>/; the gate files are archived, the attempt-1 A2 records and outputs stay on the node, round-2 R2V-4), or with c2/STEP0_NO_ERROR (no error found: fail_final, A2 stops, A1 tier only) |
| I-D2 | §16 | section 16 hard cap with queued single points: at most two published single points are incomplete at a time, and a publication is allowed iff H_spent + 2 x expected (each outstanding and the new one) <= 520, which is never below the check at the job's actual start |
| I-D3 | §16 | section 16 two-copy layout: a gate on a finished relaxation does not delay the start of the next one in order; a stopping decision stops every running A2 part (exit file) and marks it killed_by_gate |
| I-D4 | §§9, 12 | sections 9, 12: the default-pose single point (o0) of a pose or multi-pose site is run for the default cell whatever its validity; o&lt;k>=1.. come from the distinct-minima map of scripts/46; a slot without a kept minimum is skipped |
| I-D5 | §13 | section 13 A2: restart data are usable iff the part's output carries the soft-exit marker recorded by the smoke test and every file of smoke.mapping.restart_files exists for the prefix; otherwise rerun from k = 0 with the identical part-1 input, earlier parts and tmp/ moved to discarded/ unread |
| I-D6 | §11 | section 11 end classes: a part that ends by nstep or by the cap exit file at k = 200 is at the cap (end rule applies); converged, BFGS or SCF failure and a pw.x error banner (scripts/47 pw_error: unconverged early, STOP for a human after the gates on ended relaxations, N-F20) end the relaxation; an end without JOB DONE is an interruption only if the part started in an earlier boot, was asked to exit (spot, gate), or its pw.x was OOM-killed; any other end without JOB DONE in this boot (a QE error on a rank whose output is not written, a crash) is a STOP for a human with RESOLVE 'unconverged', 'rerun' or 'missing' (round-2 F2, R2-QE-1), never an automatic rerun |
| I-D7 | §13 | section 13 causes: an attempt that started in an earlier boot without an end is an interruption, cause spot-notice if that boot has a recorded notice, oom if its kernel journal has an OOM kill of the command's own pid (MACE: &lt;rc>.pid written by the wrapper) or of a pw.x rank after the part's start (A2), else node-loss; every cause is rerun alike (round-2 F4) |
| I-D8 | §16 | section 16 smoke tests: on the 232-atom reference cell at q = +1 with the Pb136-like frozen region of the throughput row; n1 (nstep 1) and n3 (nstep 3) fix c0 and the slope; rst stops part 1 by the exit file after k = 0 and restarts it; nstep_first = 201 - c0; nstep after a restart = 201 - completed - c0, valid only if the restart test reproduces the n3 count |
| N-D1 | §§7-11 | gate decisions are applied by updating the state fields named in the gate output's decision; the runner computes no decision |
| N-D2 | §16 | before every gate the ledger snapshot is written to ledger/snapshot.json and &lt;campaign>/ledger.json (scripts/49 may not load this script) |
| N-D3 | §§5, 16 | geometry jobs of scripts/46 (region, build-vac, build-pair, distinct) run synchronously in the runner; they cost no node-hours, so the hard cap never refuses them (N-F14), and the spot hold does not apply to them |
| N-D4 | §§13, 16 | a STOP removes KEEP_ALIVE, writes CAMPAIGN_STOPPED and starts nothing more; the runner waits for its running children (poller and heartbeat kept) and then exits; every step of a STOP is guarded, so a full or read-only /data or a hygiene refusal never keeps the runner from draining (round-2 F1, M2), and the stop reason in campaign.json is redacted to pass the hygiene rules (the raw text stays in campaign.log) |
| N-D5 | §13 | a STOP for one job is resolved by the operator with &lt;job dir>/RESOLVE holding 'rerun &lt;note>' or 'missing &lt;note>' (an A2 relaxation also 'unconverged &lt;note>': section 11, not rerun); it is logged in interruptions.jsonl |
| N-D6 | §13 | during a spot hold no single point is published; one already published may still be started by the queue |
| N-D7 | §17 | every read of a QE output by the runner is logged with its mode in &lt;campaign>/runner_reads.jsonl (status, counts and end_rule only) |
| N-D8 | §11 | superseded by I-F1 (review F1): the runner reads the final positions of each A2 relaxation (final_geom mode, no energy) for the section 11 checks; it reads no other position |
| N-D9 | §12 | C3 G1 failure of Ca removes 8 relaxations and 8 single points per host (the interface spec says 16; the plan's section 12 counts give Ca 8 cells per host); Cl removes 20 dopant and 10 V+ relaxations and 30 single points |
| N-D10 | §§13, 16 | smoke-test and throughput runs cut by an interruption are rerun at most twice (the plan gives no rule); one that ends with QE's error banner (scripts/47 pw_error) is not an interruption: missing at once, not rerun (round-3 R3-C1-5, as I-D6 for A2) |
| N-F15 | §§8, 17 | sections 8, 17 (round-3 R3-C1-1): the n-rule gate is 'nrule' (gate:nrule, gates/nrule.json); with 'n' beside 'N' the gate outputs and gates_applied markers were one file on a case-insensitive volume (the laptop's APFS: pull, archive, verify, the one evaluation); no two job ids, gate names, marker names, labels or work ids of C1-C4 fold to the same lower-case string (asserted), and archive() refuses source names that differ only in case, a gate file whose 'gate' field differs from its name and a marker whose 'id' differs from its file name |
| N-F16 | §16, D-S0-8 | section 16 smoke tests (round-3 R3-C1-2, D-S0-8): the throughput row and A2 need the smoke mapping c0 from n1 and n3; without it the campaign STOPs naming the smoke tests (never an unexpected error); a pw.x reference run (smoke, smoke2, throughput) is resolved by &lt;run dir>/RESOLVE 'rerun &lt;dated note>' (its parts, outputs and tmp/ and the record built on them, smoke.json, smoke2.json or throughput.json with the throughput gate markers, moved to discarded/resolved_&lt;t>/, logged in interruptions.jsonl) or 'missing &lt;note>'; RESOLVE is read only once no part of the run lives, never into a running run (round-4 R4-C1-4) |
| N-F17 | §16, D-S0-8 | D-S0-8 (round-3 R3-C1-3): a C1 STOP that needs a code fix resumes at the fixed commit with c1/NODE_FIX ('&lt;new commit> &lt;dated note>'), accepted only while C1 is stopped (CAMPAIGN_STOPPED present, C1 not done) and when its commit is the checkout HEAD; the change goes to state commit_history and NODE_FIX is renamed NODE_FIX.used.&lt;t>; a NODE_FIX in another campaign or with C1 not stopped is refused; campaign.json keeps the campaign's start_commit beside the commit in force and the commit_history, and scripts/48 reports the history with the diff of scripts/46-50 of each step (round-4 R4-C1-6) |
| N-F18 | §§13, 16, D-S0-8 | sections 13, 16 and D-S0-8 (round-3 R3-C1-7): the spot-endpoint check is a reachability check: no job of a campaign runs until the poller has had a good poll (200 or 404, spot/heartbeat.&lt;boot> newer than the poller's start); none within 120 s, or a last good poll older than 5 min while the campaign runs, is a STOP (a termination notice could not arrive); the heartbeat is written at every good poll, so its age is the age of the last good poll (round-4 R4-C1-1); a poller restarted after it ended gets its own 120 s for its first good poll (the dead poller's heartbeat is not judged), and none is restarted once a shutdown or a STOP began (round-4 R4-C1-2); that grace is renewed only when the dead poller had a good poll of its own, so pollers that end before answering keep the first one's start and STOP 120 s after it (round-5 R5-1); the third such renewal within 300 s is a STOP, so pollers that each answer once and end cannot hold the scheduler (round-6 R6-C1-2) |
| N-F19 | §16 (X-4) | section 16 / X-4 (round-3 missed item): the smoke test at the chosen layout folds its verdict into smoke.json (at_layout, restart_possible false if it fails) before smoke2.json is written, and rec:smoke2 is done only when smoke.json carries at_layout for its label; C2 requires at_layout whenever the A2 layout is not 48 ranks |
| N-F20 | §§11, 16 | sections 11, 16 (round-3 R3-1): an A2 end whose end rule asks for a STOP (pw_error, nstep before k = 200, other_end) is recorded and the STOP is held until no gate, section 11 check or other job without node-hours of the active phase is ready, so step-0, K2, the projection and K3 apply to the ended cell first; no node-hour job starts meanwhile; a gate decision that stops A2 puts the 'gate' exit file on every running A2 part at once (I-D3), and the drain records a part that ends after it as killed_by_gate (outputs moved aside unread) |
| N-F21 | §13 | section 13 / N-F10 (round-3 R3-3 and missed item): a shutdown (SIGTERM) that kills a synchronous child (a scripts/49 gate, a scripts/46 geometry job or validate-a2) leaves that job pending (no marker, no STOP); a child found ended while the shutdown flag is set is not classified (A2 part, MACE attempt, reference pw.x run), so the relaunch judges it as an interruption of an earlier boot; a real STOP followed by SIGTERM still exits as stopped (return 3) |
| N-F22 | §§11, 16 | sections 11, 16 (round-3 R3C-1): a section 11 check ends the scheduler tick like a gate, so the statuses are rebuilt and K3 is applied before the next A2 relaxation can start (at 48 ranks relaxation 9 never starts before K3) |
| N-F23 | §13 | section 13 causes (round-3 R3-8): the runner records the process tree of every running A2 part (descendants of its wrapper, node /proc) in its launch record and in a2_pids.json (kept across reruns); an OOM kill in this boot is the part's interruption only for one of its own pids; without a recorded tree the pw.x task test of I-D7 applies, excluding every pid recorded for another A2 part (the other copy) in this boot; revised in round 4 (N-F34): 'a recorded tree' is one that holds pw.x ranks |
| N-F24 | §3 | section 3 (round-3 R3-C1-4): the production list needs a recorded n of 8 or 10 (the n rule), else S2Error; C3 requires the C1 gates_applied marker of gate:nrule |
| N-F25 | §16 | section 16 keep-alive (round-3 R3-C1-9): s2_relaunch.sh, when it refuses, removes a /data/KEEP_ALIVE older than the current boot (left by a runner killed with its node), so the idle self-stop applies; a refusal of s2_campaign.sh itself inside a relaunch is such a refusal, and without /data/work/s2 (before the first start) the relaunch refuses and s2_status.sh says 'not started' (round-4 R4-C1-3, R4-C1-8) |
| N-F30 | §16 | section 16 throughput row and the 2x32 layout (round-4 R4-C1-1, error, and the node lens' missed items): every pw.x run outside the queue goes through the committed ehpc/node/s2_run_qe.sh (the node's run_qe.sh with an optional core set, used from the checkout); two concurrent 32-rank copies (np32a/np32b and every A2 part at 2x32) each run on one half of the physical cores (lscpu), 'taskset -c &lt;half> mpirun --bind-to none', the recipe confirmed on the node (two separate 'mpirun --bind-to core' both bind from core 0); a part takes the half no running copy uses; every other run is bound as run_qe.sh binds; the core set, the CPUs the pw.x ranks were allowed (node /proc) and the interval are recorded; the two throughput copies always start together (a copy that completed without the other is moved aside, its measurement not used, discarded/paired_&lt;t>, not one of its reruns; one whose partner is missing is skipped), and the 2x32 rate is computed only for two copies on disjoint cores whose walls overlap for >= 90% of the shorter one (scripts/49 I-C13) |
| N-F31 | §16, D-S0-8 | section 16, D-S0-8 (round-4 R4-C1-2): check:nodescripts (no node-hours) records the sha256 of the node scripts behind every pw.x run (run_qe.sh, the QE profile, qe_queue.sh, chain.sh, s2_run_qe.sh) in c1/nodescripts_check.json and STOPs unless the queue, the chain and the launcher equal the checkout's ehpc/node copies byte for byte; C2-C4 STOP on any hash that differs from the C1 record; a commit change (c1/NODE_FIX, c2/STEP0_FIX) moves that campaign's check records to discarded/commit_&lt;t>/, so the UPF, node-script and model checks run again, first, at the new commit (round-5 R5-2); until the UPF check has passed again, md5_extra is the newest passed moved C1 record, and a re-check with other Cl/Ca MD5 is a STOP (round-6 R6-C1-1, N-B9) |
| N-F32 | §17 item 2, D-S0-8 | STAGE0 section 8 item 1, D-S0-8 (round-4 R4-C1-3): a git failure in the checkout (no repository, a copy without .git, git's ownership refusal) is a STOP in the runner and a refusal in s2_campaign.sh; HEAD must be 40 hex digits, never an empty commit read as clean |
| N-F33 | §13 | section 13, N-D10 (round-4 R4-C1-4): RESOLVE 'rerun' of a smoke or throughput run moves the attempts before it (discarded/p&lt;n>_*) aside with the resolution, so the rerun has the two reruns of N-D10; an operator's MACE rerun after a STOP for a human (an exception, N-9) is marked counts false and is not one of the two reruns section 13 allows after a reclaim, node loss, OOM or wall time |
| N-F34 | §13 | section 13 causes (round-4 R4-C1-5, R4-C24-2): a running pw.x part (A2, smoke, throughput) records its process tree with the pw.x ranks among it at every tick until all its ranks are in it, then every 30 s; an OOM kill is the part's only for one of its own recorded pids once pw.x ranks are recorded, else the pw.x task test after its start applies, excluding the pids recorded for another part in that boot |
| N-F35 | §5 | section 5, STAGE0 section 8 item 3 (round-4 R4-C1-6): check:mace checks the foundation file's sha256 and then runs scripts/46 load_mace in a child process (the runner never imports mace): version, float64, cpu, the resolved file, Z coverage and torch threads before the first MACE job, no structure evaluated; a failure STOPs before the smoke tests and costs no MACE attempt; the record names the exception also when the child qualifies it ('c46.S2Error', round-5 M-1) |
| N-F36 | §§11, 16 | sections 11, 16 (round-4 R4-C24-1): the STOP an A2 end rule asks for is durable: the A2 record carries end_rule.stop_raised false until CAMPAIGN_STOPPED holds the reason; every runner start re-holds such a STOP before any launch; every STOP's reason includes the held ones, which are then marked raised (an operator's relaunch after that STOP does not raise them again) |
| N-F37 | §16 | section 16 'killed and its output discarded unread' (round-4 R4-C24-3 and the C2-C4 lens' missed item): a stopping gate's exit request replaces an earlier 'cap' or 'spot' one of a running part (the prior reason kept), so the part is killed_by_gate whatever its end; a relaxation waiting for its restart part when a gate stops A2 is killed_by_gate with its outputs and restart data moved aside unread |
| N-F38 | §16, X-3, D-S0-6 | section 16, X-3, D-S0-6, D-S0-8 (round-4 R4-C1-5): smoke tests n1 and n3 that both end with JOB DONE but do not differ by two configurations (no affine nstep mapping of slope 1) STOP C1 before the exit/restart test and the throughput row, naming the smoke tests and the NODE_FIX / RESOLVE path, so they can be repeated while C1 is open |
| I-D9 | §16 | section 16 hard cap (round-3 R3C-7; a reading, confirmed by the analyst as D-S0-10): 'No job starts if H_spent plus the job's expected duration would exceed 520 h ... Whatever is then incomplete is missing' is read as: after the first refusal in a campaign no further pw.x or MACE job of that campaign starts (each is not_started_cap); the refusal is persisted in HARD_CAP.json and read back at every runner start, so a relaunch gives the same decision; jobs without node-hours are never swept (N-F14) |
| N-D11 | §§8, 11 | a campaign whose preconditions are refused by recorded decisions (e.g. K3 a1_only for C4) is recorded as not_run without booting work; missing evidence for a precondition is a STOP |

### `scripts/51_s2_preflight.py` (module D, pre-flight; 5 entries)

| id | plan section | reading or note |
|---|---|---|
| N-P1 | §17 | the unrelaxed member stands in for the S2-relaxed host and the pp.build_pair vacancy cell for V+_R; the pairs use partners='unrelaxed' (section 17 item 4); nothing built here is used on the node |
| N-P2 | §9 | pose slots: every start of a pose site is treated as a kept minimum (o&lt;k> = p&lt;k>), the 40 single-point upper bound of section 9; a non-default start that the builder rejects is listed, not a failure; a rejected default start is a failure |
| N-P3 | §§11, 16 | A2 inputs of the C2 and C4 start set are written with nstep 201, flagged 'pending smoke tests' (X-3); their free sets come from the stand-in regions |
| N-P4 | §§2, 11 | the m05 calibration sites and the Pb-Cl decision are read from the Stage-0 records (admissibility.json, pbcl_source.json); a provisional Pb-Cl record needs --allow-provisional, else the shifted Cl starts are refused and the pre-flight fails |
| N-P5 | §6 | electron counts and namelists are recomputed here independently of the writer and compared with its record and with the literal section 6 values |

### `scripts/52_s2_stage0_checks.py` (module E, Stage-0 checks; 16 entries)

| id | plan section | reading or note |
|---|---|---|
| I-39 | §4, answer 8 | section 4 / answer 8: mig='allow' at every X site in the admissibility builds (identical to 'forbid' except at the MIG iodide) |
| I-40 | §3 | section 3: a builder exception other than Inadmissible or Refused (BuildError, AssertionError, any other) makes the host not admissible and stops the check for a human (exit 3, production lists null) |
| I-E1 | §2 | section 2 / design sections 1 and 4 ('Verifying a primary source flips the tag'): 'verified' means read in the primary source (the paper, or its publisher's abstract if it states the value); a value read only in a secondary source, even one attributing it to the paper, is not verified, so the decision is provisional_2.837 (shifted Cl starts at 2.837 A, --allow-provisional, [M] starting points); the secondary value is recorded, reported only. Kept after review F10: the design's tag legend reads [S] as 'secondary source only, so recheck before production' and [V] as 'checked against a primary source', and 2.837 A is already tagged [S] there, so a secondary quotation does not verify |
| I-E2 | §2 | section 2 / spec X-2: 'another Pb-Cl distance' is decided at the precision the source states: d = a/2 as an exact decimal of the stated digits; any difference from 2.837 is another distance (a = 5.675 A gives 2.8375 A, not 2.837 A) |
| I-E3 | §3 | section 3: a required cell is one leg of build_paired for a token of the site's sublattice at one of the 19 sites of scripts/46 site_sets (first shell + far pair), default pose ('inherit', resolved by scripts/42 to swap / centred / inherit); Refused counts as not admissible, as Inadmissible |
| I-E4 | §11 | section 11: a drawn m05 site is admissible iff every required cell of it (both legs of each dopant of the sublattice, default poses) builds; the next site in draw order is tried until one is admissible; if none is, or if Pb124 (chosen, no fallback) fails, the check stops for a human |
| I-E5 | §17 | section 17 item 3 / design section 6 'Freeze': the freeze record is stage0/s2b2_freeze.json, holding the frozen clash parameters (f, f_w, class map with the H split, class-Y rule, thresholds, host minima), GEOM_SHA and the sha256 of the archived T4 report; the raw report and its self-test log stay off-repository with their sha256 recorded |
| N-E1 | Stage-0 loading rule | if scripts/46 is absent an in-file stub with literal copies of the plan tables is used and printed as 'MOCKED 46'; outside --self-test a mocked 46 is refused unless --allow-mock-46, and every record then carries 'c46': 'MOCKED' (the final run, with all files present, must regenerate it) |
| N-E2 | §17 item 3 | the T4 report path must lie outside the repository and must not exist yet (no silent reuse of an older report); the full scripts/42 self-test log is written beside it |
| N-E3 | §0 | if draw ranks 1-12 do not give n + 2 admissible hosts for n = 8 or 10, the lists are written as far as they go under 'candidate_lists', flagged short, 'production' is null and the check stops for a human (the plan builds ranks 1-12 only; rank 14, m15, may not enter, section 0) |
| N-E4 | §2 | the Pb-Cl notes are validated: the citation must name Poglitsch & Weber 1987, J. Chem. Phys. 87, 6373 and the phase cubic CH3NH3PbCl3; the lattice parameter is a decimal string so that its stated digits are kept; the level is one of three; anything else is refused |
| N-E5 | §5 | the MACE versions are read from the installed distribution metadata (importlib.metadata), so mace and torch are never imported; the foundation file is located by scripts/46 foundation_path |
| N-E6 | §3 | each built leg must report valid and admissible, carry the registry atom count and the default pose name of its token; any deviation is an error (I-40) |
| N-E7 | §17 item 3 | the archived T4 copy carries an 'archive' block (raw sha256, the JSON pointers of every stripped value, the generator); its own sha256 is in the freeze record |
| N-E9 | hygiene rule of Stage 0 | public hygiene (review F10): web addresses of sources are kept in the off-repository notes; the committed Pb-Cl record cites sources by name and DOI only (scripts/46 refuses a URL or host name in JSON) |
| N-E8 | §11 | the m05 draw is re-executed from the unrelaxed m05 site sets (geometry only) and must equal both scripts/46 M05_DRAW_ORDER and the crc32 values printed in section 11 |

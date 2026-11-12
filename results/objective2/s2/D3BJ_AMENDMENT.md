# D-S0-4 amendment (2026-11-07): the D3(BJ) row is not reported

- **Date.** 2026-11-07.
- **Basis.** D-S0-4 (`STAGE0.md` section 9) and X-1 (`STAGE0.md` section 5) on the D3(BJ) item of `S2_PLAN.md` section 15.
- **When written.** While C2 runs, before C3 and before the one evaluation. No S2 energy, E_b, force or geometry was read or computed for this note.
- **Code.** C1 ran at `8bff03e`, and `C1_RESULT.md` section 5 states that C2 runs at it. The one evaluation takes the campaign commit from the latest `state_end.json` [48:1298-1309]. During C2 only a `c2/STEP0_FIX` after a failed step-0 check can change it [50:2363-2372]; `c1/NODE_FIX` applies only to C1 [50:2390-2391]. This note changes no file under `scripts/` or `ehpc/`.
- **Labels.** [I] marks an inference, [S] a value checked against a cited source, and [UNVERIFIED] a fact that only the node can show. [48:931] means `scripts/48_s2_analysis.py`, line 931, at commit `8bff03e`; 32, 46, 47 and 50 are `scripts/32_dft_validation_analysis.py`, `scripts/46_s2_cells.py`, `scripts/47_s2_qe.py` and `scripts/50_s2_campaign.py`.

## Decision

S2 does not report the fixed-geometry D3(BJ) correction of `S2_PLAN.md` section 15. This is the second branch of D-S0-4: before the one evaluation, a dated amendment "states that the row is not reported". D-S0-4 leaves both branches open, so this is the analyst's choice. No D3 implementation is fixed for the one evaluation, and the row of `s2_eval.json` stays "not computed" [48:931].

Withdrawn for S2:

- the D3(BJ) item of `S2_PLAN.md` section 15;
- the clause "a D3(BJ) single-point correction is reported (laptop)" in row 12 (Cost and scope) of the objections table of `S2_DECISION.md` section 4;
- the D3(BJ) parameters in `S2_PLAN.md` section 19 item 22, which keeps only the required-hosts estimate;
- the parenthesis "a D3(BJ) correction is reported only" in item 6 (What S2 cannot resolve) of the S2 entry of `results/objective2/SCREENING_ROADMAP.md` (line 354 at `8bff03e`). Dispersion stays among what S2 cannot resolve. The roadmap text is not edited; it is kept as the record and read with this note.

Kept as the record: `S2_PLAN.md` section 20 review item 10, and X-1 and N-F29 of `STAGE0.md`. The X-1 text of the row in `s2_eval.json` is read with this note (see "The row" below).

No other rule of `S2_PLAN.md`, `S2_DECISION.md`, `STAGE0.md`, `C2_OPERATIONS.md` or the roadmap changes. No class, gate, control or decision depends on the row (D-S0-4; section 15 is reported only). The validated label stays "PBE (no D3, no SOC)" (`S2_DECISION.md` section 7; [48:57]).

A separate study after the one evaluation is pre-registered at the end of this note. It is not the section 15 row, and it changes no S2 decision.

## Scientific reason

A fixed-geometry D3(BJ) term depends only on the atomic positions, the elements and the cell, for fixed damping parameters and cutoffs. At the S2 geometries it would show how much the two-body dispersion energy (with coordination-dependent C6) changes when V_I+ moves from the two far sites into the dopant's first shell. It would not give a dispersion-relaxed binding energy. It does not see the vacancy's charge or the dopant's electronic structure [I]. It is not the Objective-1 D3 fingerprint, which includes QE's default three-body term, and by standing rule 1 it is never compared with it (`S2_PLAN.md` section 15). Rule V, the gates and every decision are defined on the plain PBE E_b. So the row could qualify a reported value, but never a class, gate or decision (D-S0-4).

## Why the second branch: the analyst's choice

The first branch of D-S0-4 is open. An implementation could be installed in its own environment, with its version and file sha256 recorded, before the one evaluation. The analyst does not take it, for this reason. The one evaluation cannot be repeated except after a code error (`S2_PLAN.md` section 17 item 6): a rerun needs a self-test case that fails on the first code and passes on the fixed code [48:1425-1444]. The row is a constant [48:931]; `scripts/48` computes no dispersion term and only attaches the cited note [48:1447-1448]. A computed row would add new, unreviewed code to the one evaluation. A defect in that code would put the primary PBE result at risk, for a row that qualifies no class, gate or decision.

Other facts that bear on the choice:

1. **The code route.** A change of `scripts/46`-`49` after the campaign commit is accepted at the one evaluation only with its own dated `--amendment` note (N-F29; [48:1320-1372]). The route exists. For a change of the analysis script that is not a code-error fix, it is open only before C3 (`S2_PLAN.md` section 17 item 6; see the next section). This note does not use it.
2. **A side tool.** A tool outside `scripts/` (as the C2 figure script is) could import `scripts/48` and `49` read-only and write values beside `s2_eval.json`, but not into it.
3. **The geometries.** A correction to every E_b reads the four geometries behind each E_b. Until C4 ends, production and A2-II outputs are read only for completeness, validity and the end rule (`S2_PLAN.md` section 17). Until the one evaluation, raw C2 A2 outputs are opened only by `scripts/49` and the force-only reader (`C2_OPERATIONS.md` section 3). A D3 correction to every E_b could therefore come only at or after the one evaluation.
4. **The cost.** No node-hours. The cells number of the order of 10^3, of about 233 atoms each, which is minutes of laptop CPU [I]. The analyst time is one to two days, for the environment, the reader, a self-test and a review round [I].

The study below gives the same numbers from the same geometries, after the one evaluation and without new code in it. A side tool under the first branch would compute what the study computes. The analyst places that computation after the one evaluation and outside the section 15 row, so that no D3 number is attached to the one evaluation.

## No code change: the analyst's practice

This note changes no file under `scripts/` or `ehpc/`. Keeping the reviewed code of the campaign commit for the one evaluation is the analyst's choice for S2. It is not a rule of the plan. The plan and the code allow a dated code change: a rerun after a code error (`S2_PLAN.md` section 17 item 6), a difference in `scripts/46`-`49` with a dated `--amendment` (N-F29; [48:1320-1372], whose docstring says that D-S0-4 foresees such an amendment [48:1325]), and a `c2/STEP0_FIX` commit [50:2363-2372].

One plan rule sets the time for the analysis script. Section 17 item 6 commits it before C3 and runs it once after C4. A change of `scripts/48` that is not a code-error fix is therefore open only before C3. From C3 onwards, only a rerun after a code error changes it. The code does not check this timing [48:1320-1372]; the plan rule binds.

## How the one evaluation cites this note

- **Path.** `results/objective2/s2/D3BJ_AMENDMENT.md`. It is committed, it lies outside `scripts/`, it is a regular file (not a symbolic link), and it carries the ISO date 2026-11-07.
- **Flag.** The one evaluation is run from the repository root, with its `--d3bj-amendment` flag set to the path above, beside its archive and output arguments. The note is not passed as `--amendment`, which keeps only the code-diff role (N-F29). The path is resolved against the current directory [48:1379], hence the run from the root [I].
- **The row.** It reads "not computed", with the reason X-1 and this note's path, sha256 and dates [48:931; 48:1388; 48:1447-1448]. The X-1 text ("a dated amendment must fix an implementation") is the Stage-0 conflict note. D-S0-4, the analyst's decision on X-1, allows either branch. The text is kept, since this note changes no code. With this note cited, the row means "not reported". The S2 result note says so and cites this note.
- **Once only.** The flag belongs to the one evaluation. `s2_eval.json` is never overwritten [48:936-948]. A rerun needs a code error shown by a self-test case [48:1425-1444], so a missing citation cannot be added to `s2_eval.json` later [I].
- **The node.** This note is not deployed to the node. A new commit in the node checkout would stop the runner [50:2356-2377]. That the node checkout stays at the campaign commit is [UNVERIFIED].

## Pre-registered sensitivity study (after the one evaluation)

- **Status.** Pre-registered by this note, which was written before C3 and is committed before the one evaluation. It is not part of `S2_PLAN.md` section 15 or of `s2_eval.json`. It changes no S2 class, gate, control or decision.
- **When.** Only after the one evaluation has written `s2_eval.json`, and after the S2 result note. If the one evaluation is not run, the study is not run.
- **Cells.** Every cell whose PBE energy enters an E_b of `s2_eval.json`, at both tiers, for production hosts and pilots: the four cells D_j+V+, D_j, V+_Rj and host (host_Rj at A2) of each E_b (`S2_PLAN.md` section 1), with every kept minimum of a multi-pose leg.
- **Geometries.** Each PBE cell energy is taken at the archived geometry at which it was computed, from the `structures.tar.gz` of the campaign that holds that geometry [50:4266-4284]. The cell energies that enter an E_b in `scripts/48`, and their geometries, are these.
  - An A1 single point F: the host, V+_Rj, D_j and D_j+V+ cells of an A1 quartet, each kept minimum of a multi-pose leg, the pilots' noise-pilot quartets and the q = 0 cells of `S2_PLAN.md` section 10 [48:196-240; 48:824-838; 48:902-916]. Its geometry is `cells/<work id>/relaxed.extxyz` of that cell in the campaign that computed it (C1 for the pilots, C3 for production), a MACE-MP-0 geometry (`S2_PLAN.md` section 5). A kept minimum uses the cell of its kept start [50:3057-3065].
  - F(0), the k = 0 energy of an A2 relaxation. It is the A1-tier term of each delta and of delta_far [48:302-306; 48:317-321]. It also enters the A1 DFT E_b of the pilot MACE ledger, the WP2c comparison and a q = 0 row whose D cell has no single point [48:786-788; 48:911; 48:922-923]. Its geometry is the A2 start, the cell from which the A2 input is written: the C1 cell `cells/<work id>/relaxed.extxyz` of the A1 cell, or of the S2-relaxed host for host_Rj [50:3881-3887; 50:4064-4072].
  - F(final), the last energy of an A2 relaxation, the A2-tier term [48:305; 48:1127]. Its geometry is `a2/<label>/<label>.final.extxyz` of C2 or C4, the positions of that last configuration (a PBE geometry) [50:3889-3906]. Before any energy is replaced, the study checks that the k of each A2 record's final geometry equals the table's k_last [50:3896-3906; 48:1123-1127]; otherwise it stops.
  - The positions, the elements and the three cell vectors are used as archived [46:361-376], periodic in all three directions. No atom moves and no cell changes. If a cell energy has no archived geometry, its PBE energy is kept unshifted in the copy, and every E_b that uses it, with every class or control computed from that E_b, is listed as not computed. Through the pooled terms one such cell can make many classes not computed; the study lists them all. The cell charge is not an input [I].
- **Package.** simple-dftd3 with its Python API, in its own environment, so that the project environment gains no dependency (X-1). The version is v1.2.1, the release whose parameter table and Python interface were read for this note. If it cannot be installed, the newest release that is at least two weeks old on the day the environment is built is used, and the reason is recorded. The parameters are passed explicitly, with s9 stated in every call, because both routes of the package's Python API default to the three-body term (s9 = 1 when the parameters are given, atm = True when they are loaded by functional name) [S: simple-dftd3 v1.2.1]. ASE's DFTD3 wrapper (ASE 3.29.0) and torch-dftd (v0.5.3) add it only on request (abc = False) [S].
- **Parameters (PBE).**
  - Primary, D3(BJ), two-body: s6 = 1, a1 = 0.4289, s8 = 0.7875, a2 = 4.4407 bohr, s9 = 0 [S: the simple-dftd3 table, citing Grimme, Ehrlich and Goerigk 2011].
  - Variant 1, three-body: the primary parameters with s9 = 1, that is, the package's Axilrod-Teller-Muto (ATM) term, with alp = 14, the package default, compared with the table like the other parameters. In the BJ route alp enters only the ATM term, which the package damps with alp + 2 [S: simple-dftd3 v1.2.1].
  - Variant 2, zero damping, two-body: s6 = 1, s_r,6 = 1.217, s8 = 0.722, with the fixed s_r,8 = 1 and alpha_6 = 14, and s9 = 0 [S: the simple-dftd3 table, citing Grimme et al. 2010].
  - Before the first S2 cell, the code compares s6, a1, s8, a2 and alp (BJ), and s6, s_r,6, s8, s_r,8 and alpha_6 (zero damping), with the PBE entries and defaults of the installed parameter table, and stops if any differs. s9 is not compared: this protocol sets it in every call, to 0 for the primary and variant 2 and to 1 for variant 1.
- **Shift.** For each E_b and each variant, the shift is E_b(F + E_D3) - E_b(F), where every PBE cell energy F is replaced by F + E_D3 at its own geometry. The package's Python API returns E_D3 in hartree [S: simple-dftd3 v1.2.1]. E_D3 is converted to eV with the CODATA 2018 factor, 27.211386245988 eV per hartree, before it is added to F, which `scripts/48` holds in eV [48:171-173; 48:1078; 48:1127]. The factor is twice the Rydberg energy of `scripts/32`, with which every PBE F was converted to eV [32:25; 32:50; 47:212; 47:1120]. For a default-pose E_b this is E_D3[D_j+V+] - E_D3[D_j] - E_D3[V+_Rj] + E_D3[host] (host_Rj at A2). For a multi-pose leg the Boltzmann aggregate of `S2_PLAN.md` section 9 is recomputed with F_i + E_D3,i.
  - Shifted: every A1 single-point F, with every kept-minimum F_i, and F(0) and F(final) of every A2 relaxation.
  - Held at the one evaluation's values: sites; validity, including the A2 end-rule outcome and the plateau flag (from F(180) and F(200); the k = 180 geometry is not archived) [47:1167-1173; 48:1119-1128; 50:4277-4284]; kept minima; n; the pose modes; every gate decision (G1, gate N, the pose rule, K2, K3, the step-0 check and the cuts); the gate-derived quantities in the table [48:1135-1146] (gate N's sigma_far and df, the pose gate's a_pose, Delta_pose values and count terms); the constants; and every MACE energy.
- **Classes.** This uses the `scripts/48` and `scripts/49` code of the commit of the one evaluation, imported read-only, on a copy of the table that `scripts/48` assembles, rebuilt in the project environment from a clean checkout of that commit and the archives that the one evaluation read. Before any energy is replaced, the re-assembled table must have the inputs_digest of `s2_eval.json` [48:1460]; otherwise the study stops. In the copy only the shifted energies are replaced. Only E_b and what `scripts/48` computes from E_b are recomputed: delta and the pooled delta, the separability test and a_far (evaluated from E_b in the one evaluation [48:645-648]), Y_h, the intervals, the heterogeneity test, class_rule_v at both tiers [48:372-382; 48:670-671; 48:677-680], and the controls C1, C2 and C5 and the A1-tier control (Sr repels at A1) [48:492-501; 48:683-684; 48:693-698]. C3, C4, the gate-N part of C2 and the no-class reasons rest on held inputs [48:494; 48:566-577; 48:666-667]. The held gate decisions therefore do not include these four controls, because the code computes them from E_b. The validated class [48:704-717] and the displayed A1 class [48:724-736] then follow.
- **Reported.** In a separate dated note with its own JSON under `results/objective2/s2/d3bj_sensitivity/`, never in `s2_eval.json`: per variant, the shift of each E_b by dopant, host, site and tier; per dopant and tier, class_rule_v, the validated class (at A1, the displayed class) and the four controls above, each with and without the shift; and whether any class changes under the fixed-geometry shift (this does not give the class at a D3-relaxed level). The JSON lists the held quantities. The label is "fixed-geometry D3 sensitivity: not D3-relaxed, not the Objective-1 fingerprint".
- **Environment record.** The package name and version; the sha256 of every installed package file; the Python, ASE and numpy versions; the bohr and hartree conversion constants and their set, CODATA 2018 (0.529177210903 angstrom per bohr, as in [32:26], and the hartree factor above); the real-space (two-body and three-body) and coordination-number cutoffs, left at the defaults of the installed version; the commit of the one evaluation; and the sha256 of `s2_eval.json` and of each `structures.tar.gz` read. The study's code lies outside `scripts/` and `ehpc/`, and it is tested on synthetic periodic cells before any S2 cell is read. In that test one synthetic cell is also computed with the package's ASE calculator, which returns eV. The two results must agree to a relative 1e-6, which allows for ASE's default CODATA 2014 units [S: ASE 3.29.0] and still catches a unit error [I].

## Sources

- S. Grimme, J. Antony, S. Ehrlich and H. Krieg, J. Chem. Phys. 132, 154104 (2010), doi 10.1063/1.3382344 (D3 with zero damping).
- S. Grimme, S. Ehrlich and L. Goerigk, J. Comput. Chem. 32, 1456 (2011), doi 10.1002/jcc.21759 (Becke-Johnson damping).
- simple-dftd3 at tag v1.2.1: its parameter table (`assets/parameters.toml`), for the PBE entries and the defaults, alp = 14 included; its Python interface, for the defaults s9 = 1 and atm = True; its ASE calculator, for the units (lengths in bohr, energy in hartree); and its rational-damping source, for the ATM damping with alp + 2.
- ASE's DFTD3 calculator at ASE 3.29.0 and the torch-dftd calculator at v0.5.3: the three-body term is off by default (abc = False). ASE's units module at 3.29.0, for its default CODATA 2014 units.
- The original dftd3 program of the Grimme group, V3.1 Rev 1 by its banner, in the public copy at tag v3.2.0 of the loriab/dftd3 repository, for the unit of a2.
- The CODATA 2018 values of the hartree energy in eV and of the bohr radius (NIST).
- The PBE values above were checked against the simple-dftd3 parameter table, whose PBE entries cite these two papers, and against the D3 parameter lists of the Grimme group. The papers' own tables were not read. The table gives a2 without a unit. It is in bohr: the original dftd3 program uses a2 without conversion, on coordinates in bohr, and simple-dftd3 takes lengths in bohr [S]. Each source above was read at the version named.

## Dated notice (2026-11-11)

Appended under amendment 2026-11-11a of `S2_PLAN.md` (commit `1f8e496`, part g, step 6). The text above is not edited.

- On 2026-11-11 at 21:10:32 UTC the node recorded K3 = fail_replan (`C2_RESULT.md` §4). C3 recorded not_run at 21:12:09 UTC, with no job, cell or value; its archive is held privately until S2b.
- No one evaluation runs under the plan as it stands (amendment 2026-11-11a, part b). This note therefore has nothing to apply to. It is neither withdrawn nor re-opened; S2b states whether it is re-adopted (part e, item 7).

## Dated notice (2026-11-12): S2b

Appended under `S2B_PLAN.md` (the commit that adds it), §1. The text above is not edited.
- This note stays in force in substance: the D3(BJ) row is not reported.
- Its sensitivity study runs after the S2b evaluation E has written its output. It uses E's printed tables and their
  sha256 digest in place of `s2_eval.json`. Classes and controls are recomputed with E's own functions, never by
  `scripts/48` assemble (`S2B_PLAN.md` X16).
- If no A1 tier is produced, the study has nothing to apply to.

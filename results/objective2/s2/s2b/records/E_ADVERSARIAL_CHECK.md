> Record of the independent check of block 4 of E, made on 2026-11-24 by a sub-task of the project lead and
> committed with `S2B_RESULT.md`. The text is the checker's, unedited except that links to working files are
> replaced by their file names. Its scripts and its comparison table (41 300 rows) are kept with the private
> c3b archive.

# E_ADVERSARIAL_CHECK: independent check of block 4 (A1 tier) of the one-shot evaluation E

Date: 2026-11-24. Checker: independent sub-task of the project lead. E's output: `s2b/E_output.txt` (the unedited file, sha256 `3273f0a2241ecd4cc636f073f7bbfac6666db6719102de7440df03419ed34e12`), block 4 = lines 2019-6863 (cited below as "B4:n", n = line within block 4). Repository commit 98bb606. Private archive `c3b_private_root_2026-11-23`.

## Verdict

1. **Block 4 stands as printed.** No blocker and no numerical error was found: of 41 300 quantities recomputed from the raw c3b data and compared at printed precision, 41 295 agree; the five that differ are one count label (off by one) and four bounds that lie within the rounding of an input which E prints to two decimals.
2. **The four classes, the nine invalid cells and n_d = 8, 7, 7, 6 are reproduced** from the plan's text with my own pw.x parser; no value from an invalid cell or an invalid host enters a pooled statistic or a class.
3. **Three points of reading, not of arithmetic, deserve the lead's attention:** host m06 is an extreme outlier for Sr (cause open; "Sr repels" survives every test made); the Cl class "no first-shell interaction beyond k_BT" is the least robust class and describes a shell-and-host mean that hides large site-level scatter; and the per-site intervals that exclude zero are unadjusted for 16 sites.

## Scope, deviations and how to read this note

- **Data scope of part A: no reduction.** All 544 final single points, all 8 hosts, all 4 dopants; no subsampling.
- **Restriction on file names.** The binding restriction names files containing "B136" or "Sr136". Read literally it covers 24 single points and 24 records of the c3b archive itself (V_B136 and Sr at Pb136 on the eight production hosts). I read these c3b files, because the task requires all 544 single points, E's block 4 prints their values, and the lead's correction names one of them (`s2_m22_Sr136o0_vac`) as part of the result. Nothing outside the c3b archive with such a name was opened, and nothing under `c1/records`, `c1/raw`, `c1/gates*`, `c2/` or `fr/` was opened, searched or hashed.
- **Values taken from E's output, not recomputed** (their sources are outside c3b and blinded to this check): δ_far(FA188) = −2.16 meV (E output line 440); gate N pass for Sr, Cl, Cs, GA (lines 2003-2012); a_pose = 0.00 meV for Cs and Cl, one kept minimum per leg (lines 2013-2016); C3 (G1 for Cl) True (B4:458).
- **Platform holds.** Several of my steps were held because the platform's safety check could not run. Each was raised again unchanged and none was routed around. Two were still held when the lead asked for closure; they are listed under "Not checked" as "held, not run".
- **Two facts supplied by the lead and not checked by me** are marked "(lead)" where used.
- All post hoc analyses (section C) change nothing in E.

## Findings in order of severity

### Blocker
None.

### Major (reading of the result; no error of E)

**M1. Host m06 is an extreme outlier for Sr; the pooled s_Y and the "required hosts" are dominated by it.**
- Evidence: B4:32 `m06 Sr: ... Y_h = -0.40 meV`; own value −0.40 meV (e_h(124) = −23.42, e_h(136) = +22.61; B4:24, B4:26). The other seven hosts: mean 141.37 meV, SD 20.51 meV, range 114.25 to 166.47 meV. m06 lies 6.91 SD of the others below their mean; Grubbs G = 2.314, two-sided p = 0.0052 (normality assumed, n = 8).
- Effect on E's numbers: s_Y,Sr = 53.60 meV (B4:444) against 20.51 meV without m06; I^A1_Sr = [60.44, 186.86] against [114.08, 168.67] without m06.
- The zero-shot MACE values of the same geometries show m06 lowest as well: MACE Y_h(Sr) = 85.79 meV at m06 against 150.99 to 197.83 meV at the other seven; MACE − DFT is 86.19 meV at m06 against 13.88 to 45.65 meV elsewhere.
- m06 also holds seven of the nine invalid cells (B4:9-15).
- Not an artefact of the compute-node instance: (lead) a cross-instance rerun of 8 single points, among them the m06 Sr site-124 quartet, reproduced every archived total energy at 1e-8 Ry. My own, weaker evidence points the same way: the archived first try of `s2_m02_VA128` (started 20 Nov 06:28:32, first instance) and its final run (22 Nov 00:42:53, second instance) print identical SCF total energies over the 10 iterations the first try reached.
- What this does not show: why m06 differs. The geometry description of m06 from the records (which FA molecule moves, sub-threshold check-5 quantities of the Sr cells) was written but its step was held, not run. **Open.**
- Block 4 prints no remark on m06; a reader of 4.3 alone cannot see that one host carries the spread.

**M2. The Cl class "no first-shell interaction beyond k_BT" is correct by rule V but fragile, and its wording is easy to over-read.**
- E: Ȳ_Cl = 0.95 meV, s_Y = 15.78 meV, I^A1 = [−20.05, 21.94] meV, G_d = −1.62 meV (B4:456-459); own values identical.
- Leave-one-host-out: the rule-V class becomes "not resolved" for 5 of the 7 hosts left out (m02, m16, m12, m32, m26; upper or lower bound 26.4 to 28.4 meV in magnitude). Part of this is the loss of one degree of freedom (t rises from 3.521 to 3.810), so it is a statement about margin, not about any one host.
- Quantile: the interval stays inside ±25.7 meV only up to q = 0.9970 (two-sided level 6.0e-3); at the ranking quantile 0.9975 the class would be "not resolved".
- Site level: the 55 valid e_h(j) of Cl range from −160.10 to +88.43 meV; 22 of 55 exceed k_BT in magnitude; the median within-host SD across the eight sites is 42.50 meV against a between-host SD of Y_h of 15.78 meV. The class is a statement about the mean over the shell and over hosts, not about individual first-shell sites.
- By distance rank (iodides ordered by distance from I127 in the relaxed host, a proxy for the plan's ranking) no rank has a t(0.975) interval excluding zero, and e_h(j) shows no trend with distance (r = 0.026, p = 0.853, n = 55, values within a host not independent). The scatter is therefore not explained by a consistent geometric role.
- Not done: a per-host Boltzmann shell value (G within each host, then averaged), which would test directly whether the plan's G_d (host means first, then Boltzmann) hides host-specific trapping sites.

### Minor

**m1. Count label off by one (B4:7).** E prints "files listed in c3b/MANIFEST.sha256: 2551". The manifest lists 2550 files; 2551 is the number of files in the archive including the manifest itself (`e_block4.py` line 331 adds the manifest to the dictionary whose length is printed). All 2550 listed hashes were re-computed and agree, and the manifest's own sha256 equals the line of `C3B_NOTE.md`.

**m2. Cl site 137: the positive per-site mean is conditional on two excluded hosts, and the dopant-specific rule sits exactly at its threshold.**
- E: Ē_Cl(137) = 15.18 meV over n_j = 6, t(0.975) interval [4.21, 26.15] (B4:454); "failed cells 3 of 128; sites over n/4: none" (B4:458).
- Site 137 fails check 5 at 2 of 8 hosts (m06 and m26; B4:9, B4:16). The rule needs "more than a quarter" (S2_PLAN §12), so 2 of 8 does not trigger it; one more host would.
- The raw E_b of the two excluded quartets, from complete single points on the geometries that failed check 5, are −69.52 meV (m06) and −65.94 meV (m26), against a far-referenced mean of +15.18 meV on the six hosts kept (a raw and a far-referenced value differ by the far mean of the host). S2_PLAN §12 itself warns that such failures are not missing at random. This does not change the Cl class (see C2, variant b), but the interval of site 137 should not be read as evidence of repulsion at that site.

**m3. Per-site intervals are unadjusted and are printed for every site (B4:441-471).** S2_PLAN §14 asks for per-site t(0.975) intervals when the shell is flagged heterogeneous; E prints them always, for 16 sites. Under Bonferroni over the sites of one dopant: Cl 49 [−1.45, 49.54] and Cl 137 [−4.13, 34.49] include zero; GA 128 [−24.23, −1.46] still excludes zero; over all 16 sites GA 128 [−30.00, 4.31] includes zero. Only the two Sr sites exclude zero under every adjustment.

**m4. The far-bias sensitivity of 4.5 cannot be reproduced to the last digit from E's own output.** Four of the twelve bounds differ from mine by 0.01 meV (Sr lower 58.28 against 58.29; Cs lower −62.12 against −62.11, upper 19.41 against 19.40, U 62.12 against 62.11; B4:486, B4:488) because δ_far(FA188) is printed as −2.16 only. The twelve printed bounds imply |δ_far| in [2.1553, 2.1570] meV, which is consistent with a value that prints as 2.16. No error; printing δ_far unrounded once would close it.

### Notes

- **n1. Raw E_b of the nine quartets with an invalid cell are not printed** ("not formed", B4:45, 47, 49, 56, 62, 67, 71, 305, 383), although their single points are complete and S2_PLAN §15 lists raw E_b among the reported items. Own values (meV): m06 Cl137 −69.52, Cl138 −99.59, Cl175 −107.73, Cs92 −226.79, Cs164 −151.97, GA92 −295.28, GA200 −142.20; m26 Cl137 −65.94; m22 GA16 −17.27. The seven m06 values are all strongly negative.
- **n2. The appended per-dopant labels name the m30 far pairs** ("X far pair (I175, I186)", "A f₁ (FA188) ... f₂ (FA164)") on values of production hosts whose far pairs differ (X: I175 with I222 in five of the eight hosts; A: eight different pairs, of which only m16 uses the two sites of m30). The strings are the pre-registered ones (S2B_PLAN §1), so E is faithful; a reader may still take them for the sites used.
- **n3. "class no class (A1-tier control failed: C4) (unchanged)" (B4:489)** is awkward wording; no content issue.
- **n4. GA** carries "no class" through C4 (n_d 6 of 8). For the record: all six valid hosts are negative, Ȳ = −13.20 meV, and the rule-V class "not resolved" rests on the lower bound −27.98 meV passing −25.7 meV by 2.3 meV.
- **n5. Smearing term.** −TS is 0 in all 544 outputs, so the choice between F and E is immaterial here.

## A. Independent recomputation

**Method.** Own parser `adv01_parse_pw.py`; energy = the single line of each pw.x output that starts with `!` (`!    total energy = ... Ry`), as S2_PLAN §6 states ("F, the '!' total energy (free energy)"); completeness = `JOB DONE.` and `convergence has been achieved`; forces = the block "Forces acting on atoms (cartesian axes, Ry/au)". The four energies of a quartet are combined in exact decimal arithmetic in Ry and converted with 13.605693122994 eV/Ry (CODATA 2018); forces with 0.529177210903 Å/bohr. Records: `adv02_records.py`. Tier and comparison: `adv03_recompute.py`; log `adv03_log.txt`.

**Raw outputs.** 544 of 544 final outputs complete; each holds exactly one `!` line, one force block, pw.x 7.5, 64 MPI processes, 50/400 Ry; electron counts as S2_PLAN §6 (1070 host and Cl D; 1062 V and Cl D+V; Sr 1066/1058; Cs 1060/1052; GA 1076/1068). None of the three archived first tries holds a `!` line.

**Validity (records, check 5 read invariantly, amendment 2026-11-16a item 5).** The pass flags of all 544 records were re-derived from the recorded quantities and the plan's thresholds; none differs from the stored flag, and the two readings of check 5 never differ (no invariant-only cell). Nine cells are invalid, all on check 5 under both readings, the same nine as B4:9-17:

| cell | max inorganic displacement (Å) | max FA carbon displacement (Å) | max FA rotation (°) |
|---|---|---|---|
| s2_m06_Cl137p0_vac | 0.202 | 0.465 | 30.70 |
| s2_m06_Cl138p0_vac | 0.298 | 0.431 | 28.74 |
| s2_m06_Cl175p0_vac (far) | 0.176 | 0.469 | 32.18 |
| s2_m06_Cs92p0_vac | 0.131 | 0.530 | 35.14 |
| s2_m06_Cs164p0_vac (far) | 0.150 | 0.525 | 37.40 |
| s2_m06_GA92p0_vac | 0.123 | 0.592 | 40.66 |
| s2_m06_GA200p0_vac (far) | 0.163 | 0.448 | 31.60 |
| s2_m22_GA16p0_novac (far) | 0.175 | 0.325 | 16.91 |
| s2_m26_Cl137p0_vac | 0.292 | 0.058 | 6.19 |

Valid hosts: Sr 8; Cl 7 (m06 out: far I175 invalid); Cs 7 (m06 out: far FA164 invalid); GA 6 (m06 out: far FA200; m22 out: far FA16). Equal to B4:6.

**Comparison with E** (table: `e_block4_recomputed.csv`, columns kind, host, dopant, site, value_recomputed, value_E, difference, agree_at_printed_precision, note).

| section | quantities | compared | agree |
|---|---|---|---|
| 4.0 | n_d (4), tier computable, cells, records, single points complete, manifest count | 9 | 8 |
| 4.1 | invalid-cell list and rows, check-5 counts | 14 | 14 |
| 4.2 | site role, raw E_b, e_h(j), MACE E_b, MACE − DFT, host validity, valid first-shell count, far mean, Δ_h, Y_h | 1 056 | 1 056 |
| 4.3 | Ē_d(j), n_j, site intervals, k, G_d, mean_j, flag, n_d, Ȳ, s_Y, t, a_pose, I^A1, U_d, controls, dopant-specific counts, classes, required hosts | 168 | 168 |
| 4.4 | n′, mean D_h, SD, interval (6 pairs) | 30 | 30 |
| 4.5 | I, U_d, class, changed (4 dopants) | 20 | 16 |
| 4.6 | all/free RMS and max, n, free index list, every free-atom norm (544 cells) | 40 002 | 40 002 |
| 4.8 | E_mace_eV leaf count | 1 | 1 |
| total | | 41 300 | 41 295 |

The five differences are m1 (one) and m4 (four). The 192 raw E_b comparisons count the nine invalid quartets as agreeing when both sides have "not formed". The pooled values of 4.3 as recomputed: Sr n 8, Ȳ 123.65, s 53.60, I [60.44, 186.86], repels; Cl n 7, 0.95, 15.78, [−20.05, 21.94], no first-shell interaction beyond k_BT; Cs n 7, −21.35, 29.01, [−59.96, 17.25], not resolved; GA n 6, −13.20, 9.50, [−27.98, 1.58], rule V not resolved, displayed class "no class (A1-tier control failed: C4)".

**Where the plan's text did not suffice and E's code (`e_block4.py`) was consulted.**
1. Display class under a failed A1-tier control. S2_PLAN §14 says the A1-tier controls are "reported with the A1 classes"; that a failed control replaces the class by "no class (A1-tier control failed: …)" is E's composition (lines 609-623). It decides GA's displayed class.
2. The counting of the dopant-specific rule (which cells form the denominator: D and D+V of the first-shell sites over the eight hosts, 32/128/48/48) and the printed form "sites over n/4".
3. What is printed for a quartet with an invalid cell and for a host that is not valid (raw E_b, far mean, Δ_h, e_h(j) "not formed"). S2_PLAN defines e_h(j) whenever the far pair is valid; here every non-valid host has an invalid far pair, so no value depends on this.
4. Unit constants (Ry to eV, bohr to Å) are not in the plan. With CODATA 2018 every value agrees at printed precision.
5. The force RMS ("per-atom norms, RMS and max", §15) was read as the root mean square of the per-atom norms; it agrees with E in all 544 cells.
6. The row formats of block 4.

## B. Internal consistency

- **Counts.** 544 cells, 544 records, 544 complete single points; 536 non-host cells = 527 passing check 5 as written + 9 failing under both readings; 568 E_mace_eV leaves; all equal to E. The manifest count is m1.
- **Invalid values in pools.** E's pooled statistics equal mine, which are built from valid quartets on valid hosts only. Including the excluded material gives different numbers (C2: Cl mean 1.18 or 6.01 against 0.95; GA −18.86 or −21.85 against −13.20), so E's values do not contain it. The nine invalid quartets appear in E only as "not formed".
- **Zero-shot MACE rows.** 192 of 192 MACE E_b and 192 of 192 MACE − DFT entries agree (nine of the latter "not formed" on both sides).
- **Section 4.6.** Compared exhaustively rather than on a sample, so no seed was needed: 544 cells, 2 176 RMS and max values, 36 194 free-atom norms, all free index lists; all agree at six decimals. My force parse also reproduces pw.x's own "Total force" line in every output (largest deviation 5.0e-7 Ry/bohr, the print precision).
- **Provenance** (`adv04_checks.py`; first run, before a correction of one of its checks, see "Not checked"). For all 544 single points: record and meta hashes of the relaxed geometry agree; the sha256 of `relaxed.extxyz` in `structures.tar.gz` equals the record; species order and positions of the pw.x input equal the relaxed geometry (largest difference 0.0 Å; cell 3.6e-15 Å); positions echoed in the pw.x output equal the input (largest difference 1.6e-5 Å, print precision); tot_charge is +1 exactly for the V and D+V cells; one identical set of settings in all 544 inputs (scf, 50/400 Ry, Gaussian 0.005 Ry, nspin 1, nosym, conv_thr 1e-8, mixing_beta 0.3, 200 steps, K_POINTS automatic 1 1 1 1 1 1; no input_dft, no vdw_corr).
- **Node instance.** By the `starts on` header, 75 single points started between 18 Nov 14:28:14 and 20 Nov 06:22:31 (all 68 of m06; s2_m02_host, VB124, VB136, VB76, VB172, VA28, VA92) and 469 between 22 Nov 00:42:53 and 24 Nov 07:35:03, as the lead stated.

## C. Post hoc analyses (none changes E)

Full output: `posthoc_report.txt`; script `adv05_posthoc.py`. Y_h per host (meV):

| host | Sr | Cl | Cs | GA |
|---|---|---|---|---|
| m06 | −0.40 | – | – | – |
| m02 | 155.03 | 4.50 | 22.94 | −4.86 |
| m16 | 116.53 | −3.47 | −20.49 | −13.26 |
| m12 | 114.25 | 12.05 | −15.98 | −29.05 |
| m32 | 133.92 | 6.41 | −14.08 | −9.03 |
| m26 | 166.47 | −8.68 | −51.84 | −4.16 |
| m22 | 158.25 | 22.38 | −5.85 | – |
| m23 | 145.17 | −26.55 | −64.18 | −18.83 |

**C1. Leave-one-host-out** (rule V at q* on the remaining hosts; per-site means and G_d recomputed; controls C2-C4 not re-applied).
- Sr: "repels" in 8 of 8; lowest lower bound 44.30 meV (without m02).
- Cl: "not resolved" in 5 of 7 (see M2); unchanged without m22 or m23.
- Cs: "not resolved" in 7 of 7.
- GA: "not resolved" in 5 of 6; without m12 "no first-shell interaction beyond k_BT" ([−21.85, 1.79]).
- Shows: which classes rest on a margin smaller than the loss of one host. Does not show: robustness at fixed n, since leaving a host out also raises the t quantile.

**C2. Contribution of m06** (and of m22 for GA) if the validity rule were set aside; both variants are outside the plan. (a) only quartets valid by the records, referenced to the one valid far site; (b) every quartet, both far sites.
- Cl: (a) m06 Y = 2.84, n 8, I [−16.06, 18.43], class unchanged; (b) m06 Y = 41.45, I [−18.11, 30.13], "not resolved".
- Cs: (a) −3.02, I [−51.64, 13.51]; (b) −5.47, I [−51.72, 12.98]; "not resolved" both.
- GA: (a) m06 −29.03, m22 −42.69, n 8, mean −18.86, I [−35.03, −2.70]; (b) −52.43, −43.19, mean −21.85, I [−43.19, −0.52]; rule V "not resolved" both, but the interval then excludes zero.
- Shows: excluding m06 by validity does not create the Cl, Cs or GA classes under variant (a). Does not show: what valid geometries at those sites would give; variant (b) uses geometries that failed check 5 and whose raw E_b are large and negative (n1).

**C3. Does m06 look different by instance?** (description, no cause claimed)
- Per-host run diagnostics do not separate m06: mean SCF iterations 13.0 on every host; mean free-atom force RMS 0.1463 eV/Å at m06 against 0.1289 to 0.1465 elsewhere; host-cell force RMS 0.1309 against 0.1234 to 0.1361; median wall time 393 s against 365 to 374 s (the only visible difference); mean |MACE − DFT| over valid quartets 42.84 meV against 33.73 to 39.70 meV.
- Raw far-site E_b at m06: mean −6.78 meV, SD 23.59 (n = 5), inside the range of the other hosts (means −13.89 to 1.79).
- First tries: for all three archived first tries the SCF energies printed before the interruption equal those of the final run (6, 10 and 9 iterations); `s2_m02_VA128` spans the two instances.
- What stands out at m06 is in the results, not in the run diagnostics: the Sr value (M1) and seven invalid D+V cells whose failed check-5 quantities are FA carbon displacements of 0.43 to 0.59 Å with rotations of 29° to 41° (table in A).
- Shows: no sign of an instance effect in the quantities examined; with the lead's rerun, the m06 Sr value is a property of the m06 geometries or of that host. Does not show: which.

**C4. Per-site heterogeneity.** See M2 and m3. Sr: 14 of 16 site values exceed k_BT, site 136 positive in 8 of 8 hosts, site 124 in 7 of 8. Cs: 11 of 21 site values exceed k_BT in magnitude, range −102.44 to 55.44 meV. GA: 3 of 18, range −52.34 to 15.28 meV. Shows: the pooled classes of Cl and Cs average over site values several times larger than their means. Does not show: whether that scatter is physical or A1-geometry noise; the tier is fixed-geometry and E's label says so.

**C5. Dependence on the interval quantile.**
- Sr: "repels" for every q up to 0.99935 (two-sided level 1.3e-3).
- Cl: "no first-shell interaction" up to q = 0.9970; "not resolved" above.
- Cs: "not resolved" for every q from 0.90 upward (the interval would lie inside ±k_BT only below q = 0.647).
- GA: rule V gives "no first-shell interaction" up to q = 0.9883 and "not resolved" at q*; the displayed class is "no class" at any q (C4).
- Shows: Cl and GA sit within a factor of about two in level of a different rule-V class. Does not show: that q* is wrong; it is the pre-registered Bonferroni quantile.

**C6. "Sr repels" survives every analysis made:** leave-one-host-out 8 of 8; without m06 I = [114.08, 168.67]; each site separately at q*: site 124 [49.18, 198.07], site 136 [67.91, 179.44], both above 25.7 meV; quantile up to 0.99935; lower bound with the far bias added 58.28 meV (E: 58.29); positive in 7 of 8 hosts against 6 required.

## D. Other observations

Covered by m1 to m4 and n1 to n5. Nothing in 4.7 (C4b items, all "C4b not run") or 4.8 was found wrong.

## Not checked

- **Held, not run:** the rerun of `adv04_checks.py` after I corrected one of its checks. Its first run compared the plain sha256 of each archived input with `meta.input_sha256` and reported 544 mismatches; that comparison was mine and wrong (the node launcher rewrites the `pseudo_dir` line; the project's invariant is `input_norm_sha256`, `scripts/47_s2_qe.py` lines 663-671). The saved script holds the corrected comparison, which has not been executed. So: **identity of the archived inputs with the inputs recorded in the meta files is not checked.** Every other result of that script quoted above is from the first run.
- **Held, not run:** the description of m06's geometries from the records (worst FA molecule in each invalid cell, gated and within-6 Å check-5 quantities of the Sr cells per host, FIRE step counts, MACE z-score). The m06 question of M1 is open.
- **Not done:** per-host Boltzmann shell values; a variant that adds m26's invalid Cl137 quartet to a valid host; the optional figure; a seeded sample for 4.6 (replaced by the exhaustive comparison).
- **Taken from E, not recomputed:** δ_far(FA188), gate N, a_pose, C3/G1, and the cross-check XC-C3B-STATE (B4:4843).
- **Check 5 was not recomputed from the structures.** Validity is taken from the record leaves; only the consistency of the flags with the recorded quantities was tested.
- **E's code:** only `e_block4.py` was read (lines 1-260, 302-350 and 380-958), plus the hash functions of `scripts/47`. `e_eval.py`, `e_read.py`, `e_guard.py`, `scripts/48` and `scripts/49` were not read; nothing of E was executed or imported.
- **Label texts** after "--" on each row were not compared with the plan's strings, apart from reading those of B4:441-489.
- **The cross-instance rerun of 8 single points** is the lead's statement, not a result of this check.
- Leave-one-host-out and the quantile scan apply rule V only; the A1-tier controls were not re-applied in them.
- The distance ranks of C4/M2 use the relaxed host and I127, not the plan's unrelaxed host and reference vacancy point.

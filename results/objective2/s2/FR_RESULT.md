# FR result note (S2B_PLAN.md section 9 step 4; FR_OPERATIONS.md section 4)

Date: 2026-11-16. Campaign `fr` of stage S2b: the far-reference quartet of Cs at pilot host m30, site FA188 (host_R,
V⁺_R, Cs D, Cs D+V⁺), relaxed at the DFT level with the 6 Å free region. This note reports counts, decisions and
labels only. **No fr DFT energy has been read** (section 7 below).

Sources are marked [R] a public record or source-data file, [O] the output of the section 6b read, [N] the
operator's private log.

## 1. Outcome

- `fr/campaign.json` status: **done** (CAMPAIGN_DONE, 2026-11-15 23:19:43Z) [R: `fig_s2b_fr_b_stop.csv`; N].
- Gate `fr_step0@2` (V⁺_R, k = 0): **pass**, attempt 1. Gate `fr_step0@4` (D+V⁺, k = 0):
  **pass**, attempt 1. No step-0 repeat was prepared or run [R: `fig_s2b_fr_b_gates.csv`].
- Gate FR: **pass** (FR-1 and FR-2 passed (|δ_far| ≤ 50 meV)) [R: `fig_s2b_fr_b_gates.csv`]. Only the decisions were read; the
  step-0 values and FR-2's value are not reported here and were not read.
- Route (FR_OPERATIONS section 8 step 7): status 'done', `fr_outcome` pass. **C3b follows** (S2B section 9 step 5). E
  runs only after the later campaign, with block 4.

## 2. The four relaxations (attempt in force)

| # | label | role | status | end-rule outcome | n_config | converged at k | restarts | reruns from k = 0 | interruptions | MPI ranks | wall h | min per config | free / fixed atoms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `s2r_m30_hostA188` | host | complete | accepted_converged | 82 | 81 | 0 | 1 | 1 | 64 | 5.79 | 4.23 | 64 / 169 |
| 2 | `s2r_m30_VA188` | V | complete | accepted_converged | 82 | 81 | 0 | 0 | 0 | 64 | 5.81 | 4.25 | 63 / 169 |
| 3 | `s2r_m30_Cs188o0_novac` | D | complete | accepted_converged | 81 | 80 | 0 | 0 | 0 | 64 | 5.74 | 4.25 | 57 / 169 |
| 4 | `s2r_m30_Cs188o0_vac` | DV | complete | accepted_converged | 77 | 76 | 0 | 0 | 0 | 64 | 5.42 | 4.22 | 56 / 169 |

[R: `figures/source_data/fig_s2b_fr_a_relaxations.csv`, written by `fig_s2b_fr.py --build` through the S2b guard.]

- All four ended `accepted_converged`; none reached the cap of 201 configurations.
- The one rerun from k = 0 (host_R) followed the one interruption: the node was reclaimed on 2026-11-14 during host_R
  and the cell was started again [N].
- **Checks 2-5 on the final geometry:** every cell valid, with no failed check [O: item 1].
- **Check 5, both readings:** valid as written: true for all four; invariant only: false for all four. The deciding
  reading was the invariant one (S2B section 2), and it was not needed: each cell also passes as written [O: item 1].
  For each of the three pairs the record, the independent recomputation (D5) and the runner's list (R46) agree under
  both readings, with equal lists of gated objects [O: item 2].
- **A1 validity of the start cells** (reported only; C1 records read with the blinded loader of `scripts/46`):
  `s2_m30_VA188`, `s2_m30_Cs188p0_novac` and `s2_m30_Cs188p0_vac` each have `validity.valid` true and no failed check.
  host_R starts from the pristine host with the region of `c1/regions/m30_A188.json`. FR's
  `result.a1_invalid_reported` was not read.

## 3. The section 6b geometry read

Output: `c2_diagnostic/fr_geom_read_output.txt` (sha256 `e75789298906098f806da62325a894ede012c370a0f3403bcf94adc8e0527bdc`), committed unedited; exit 0, items 1-5
printed; verify record sha256 `419a5e33b05704cfb463e3e3ef894ff607f5e29f1a8a174ad12a76d038c733eb`.

- Item 1: no early stop; four cells complete and valid; 17 of 17 integrity checks equal for each; `scripts/49`
  `fr_progress` agrees.
- Item 3 (gated objects against the partner cell): V⁺_R against host_R, 20 objects, largest displacement 0.065 Å,
  FA rotation 1.0° (nitrogen labelling carried from the host); Cs D against host_R, 16 objects, 0.057 Å, 1.5°; Cs D+V⁺ against V⁺_R, 15 objects, 0.064 Å,
  2.5°. Every object passes under both readings.
- Item 4: no failing object.
- Reading: at the site where one C2 charge pair diverged late (S2B section 2), neither the charged pair nor the dopant
  pairs moved apart with the 6 Å free region. This is a statement about geometry only.

**A failure before output, and its fix (S2B section 7).**
- The first `--read` (at `99d8a51`) hung and was interrupted after about 2 h 25 min. Nothing had been printed or written.
- It was started once more, unchanged, under a watchdog that records code locations only (a wrapper calling the
  committed file with the same argument). The watchdog showed a deadlock: `_temporary` called
  `tempfile.gettempdir()` for the first time in the process inside the 'open' audit hook; tempfile resolves its
  directory under a lock that is not re-entrant and opens a probe file, which entered the hook again. That start was
  interrupted too; again nothing was printed or written. Both starts are one failure with one cause.
- Fix, commit `d5ab496` (2026-11-16): one line (`_reading` resolves the temporary directory before the audit context is
  on) and a self-test case that fails on the earlier code (the earlier `_reading` hangs in a fresh process and is
  stopped at the case's 120 s limit). Full self-test: 23 cases, 97 broken variants, passed. No rule, item or printed
  word of the read was changed. Tool sha256 after the fix: `8cd8c93ff4b11c3859f31d8a1c366f7de9ad398aaa58a71b639000541df846b6` (FR_OPERATIONS lists the earlier
  one, `347f8580…6410a`).
- The read then ran once, at `d5ab496`, under the same watchdog wrapper, in 2 s. The tool counts it as attempt 1
  because no earlier output file exists; under S2B section 7 it is the one run that follows a failure before output.
- The other one-shot tools were checked for the same pattern: `s2b/e_eval.py` resolves the temporary directory at
  import, before its guard's hook; the hook of `figures/fig_s2b_fr.py` does not call tempfile.

## 4. Labels (S2B section 1)

FR passed, so the A1 tier that C3b may produce carries, on every class and value: "fixed-geometry DFT; relaxation
bias not bounded. Far-site A2 reference valid at pilot host m30, FA188 only (Cs, A f₁, 11.25 Å; S2b FR). Invalid at
m30 Pb76 (Sr, B f₁, 11.81 Å; C2, check 5). Valid far references: 1 of 2. No production-host far site is tested at A2.
S2 K3: fail_replan; its value test (P:644-646) was not reached, and no A2 test of the first shell gates this tier."
The bracketed clause of that label is **not** printed: no cell of the quartet has `invariant_only` true [O: item 1].
The per-dopant appendices of S2B section 1 are unchanged.

## 5. Cost

| quantity | measured | planning reference (S2B section 8) |
|---|---|---|
| configurations per relaxation | 82, 82, 81, 77 | cap 201 |
| minutes per configuration | 4.23, 4.25, 4.25, 4.22 | 4.19-4.65 (C2) |
| wall hours per relaxation | 5.79, 5.81, 5.74, 5.42 (sum 22.76) | 5.5-14.4 |
| fr node-hours | 23.03 over 2 boots | 22-58 |

- Tail of the boot that ended C2, counted at FR's first boot: 0.040 h. Manual rows: 0. Retimed
  boots: 0. Ledger complete: true; ledger problems: 0 [R: `fig_s2b_fr_c_cost.csv`].
- Cumulative S2 `H_spent_h` at the end of the ledger (CAMPAIGN_DONE): 114.99 of 520 node-h [R]. The node
  stayed up for the pull and was stopped at 2026-11-16 00:32Z; the node's status then gave 116.20 h [N]. That hour is
  not in fr's archived ledger and will appear in the ledger of the next boot's campaign.
- Uncovered node-hours: none found (no problem row). Cells still to run in fr: none.

## 6. Archive, verify and the not_run c3

- Public archive: `results/objective2/s2/fr/` (commit `fd2ef25`): 28 JSON files, 8 raw files, 4 labels, 4 structures.
- Verify (commit `99d8a51`, `fr_verify/`): `OK fr FR`; `DIFF fr fr_step0`; "2 gate files, 1 differ"; exit 1. The field
  comparator shows every decision and result equal; the digest differs for the three step-0 files only, which D-C2-6
  expects (the two evaluations of one gate). Both records are committed as written.
- **The not_run c3** stays private (S2B section 9, "The not_run c3 archive stays private"). sha256 of its files:
  - `c3/campaign.json` `4b4e51e161b9d5ecde145ae02908834aedfb54fdb126cc934c72139183bdb9c6`
  - `c3/interruptions.json` `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`
  - `c3/logs/campaign.log` `50dda3691b15210598d5f9648e321c2377b446bb63ffb949f9426156b09073ca`
  - `c3/runner_reads.json` `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`
  - `c3/structures.tar.gz` `272adeccafe73e7009d51f2ec2be9871db5e0eb14239f483ea429be26c3c6402`
  - Verify line: "verify c3: 0 gate files, 0 differ", exit 1, as expected for a not_run c3 (OPS3 O19).

## 7. Not read before E

Every fr DFT energy: any F(k) of an fr relaxation, the step-0 `dF_meV`, the F of the two C1 reference single
points, FR's `Eb_A1_meV`, `Eb_A2_meV` and `delta_far_meV`, and the plateau differences. Only the decisions of the
gates were read. The values are held in the public archive under `results/objective2/s2/fr/`: the relaxation records
and part outputs in `fr/raw/` (`*.a2.json`, `*.p1.out.gz`) and the gate files in `fr/gates/` and `fr/gates_applied/`.
They remain blinded until E.

## 8. The figure

`figures/fig_s2b_fr.{pdf,svg,png,tiff}` with `figures/source_data/fig_s2b_fr_*.csv` (commit `211079f`): (a) the largest
free-atom force component against k for the four relaxations, 322 force points, no energy; (b) the three gates in
their state; (c) configurations, minutes per configuration and fr node-hours against the planning band.

## 9. Deviations from FR_OPERATIONS

1. **Pull.** The pull ran through the analysis platform's compute channel instead of `laptop_pull.sh` (no rsync from
   the sandbox): a file listing on the node, a tar transfer, and a comparison of the node listing with the local
   stage over 380 files by relative path, size and modification time (0 differences). This compares what
   `rsync --dry-run` compares by default, not content hashes [N].
2. **The section 6b read** failed before output and was fixed and rerun as section 3 describes. The read ran under a
   wrapper that adds a watchdog and nothing else, not as the bare command of section 8 step 4.
3. **Figure QA.** The external figure-audit toolkit is not installed on the machine that drew the figure: the
   panel-alignment audit, the PDF text audit and the collision audit did **not** run ("audit unavailable" in the
   plot's own messages). The source-data files hold no energy column (their headers were read for this note).
4. **A stray file.** On 2026-11-16 a review process wrote one untracked file into the working tree (an index of
   `s2b/e_guard.py`; no data). It was removed before the archive step and was never committed [N].

## 10. What follows

Before C3b (S2B section 9 step 5): the operations note and code for `c3b`, E's block 4 with its self-tests, and the
dated amendment that records the rulings on which they rest, all in one campaign commit made before any c3b value
exists. None of these is committed yet.

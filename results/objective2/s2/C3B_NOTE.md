# C3b: note of the end of the campaign (counts, decisions and timings; no value)

Written 2026-11-24, after CAMPAIGN_DONE, the pull, the archive and its verify, and before the one-shot evaluation E.
This is the c3b note of `S2B_PLAN.md` amendment 2026-11-16a item 7 and the result note of `C3_OPERATIONS.md` D-C3-18
as adapted by `C3B_OPERATIONS.md` section 4. It reports decisions, counts, validity, timings and node-hours. It
holds no energy, no force and no binding energy, and none was read for it.

c3b/MANIFEST.sha256 sha256: 5279cdd3d5d67e714bb3733eca8a454c47baa9b24d54c4f82b634c0ce97aa68c

The line above is the fixed line that E reads (`s2b/e_block4.py` `MANIFEST_LINE`).

## 1. Outcome

- c3b ended with CAMPAIGN_DONE on 2026-11-23T23:41:33Z. The runner's end line is
  "end: {'done': 1591}; CAMPAIGN_DONE; KEEP_ALIVE removed".
- Campaign commit `e5883d59caacfe080a21fa5dc770c69a5b0ca1b8` (start commit the same; recorded 2026-11-17T14:07:35Z from
  `c3b/CAMPAIGN_COMMIT`, note "2026-11-17 results/objective2/s2/C3B_OPERATIONS.md"). No fix route was used.
- The node, by the campaign's own check: MACE model sha256
  `01bfe22100139f424713cf921144e5509cbe353d67aa9fa1be9c6e1e0ed35845`; mace 0.3.16, torch 2.14.1+cpu, e3nn 0.4.4,
  ase 3.29.0, numpy 2.5.4, python 3.12.15; float64, CPU. The checks `upf`, `nodescripts` and `mace` passed.

## 2. Jobs

| category | done | other |
|---|---|---|
| checks | 3 | 0 |
| gates | 4 | 0 |
| MACE host relaxations | 8 | 0 |
| MACE V+ cells | 152 | 0 |
| MACE dopant cells (D and D+V+) | 384 | 0 |
| regions | 152 | 0 |
| vacancy starts | 152 | 0 |
| pairs | 192 | 0 |
| DFT single points | 544 | 0 |
| all | 1591 | 0 |

No job is missing, skipped, rejected or not_started_cap.

## 3. MACE relaxations (validity, step counts and walls only)

All 544 records are converged. The eight hosts are valid.

| host | valid | FIRE steps | wall (h) |
|---|---|---|---|
| m06 | yes | 2928 | 2.08 |
| m02 | yes | 2446 | 1.55 |
| m16 | yes | 2839 | 1.96 |
| m12 | yes | 4115 | 2.91 |
| m32 | yes | 2478 | 1.67 |
| m26 | yes | 3961 | 2.75 |
| m22 | yes | 4272 | 3.15 |
| m23 | yes | 4406 | 3.24 |

The step counts and walls are those of the attempt that completed (attempt 2; section 5).

| cell kind | dopant | valid | invalid | failed check |
|---|---|---|---|---|
| V+ | - | 152 | 0 | |
| D | Sr | 32 | 0 | |
| D | Cl | 80 | 0 | |
| D | Cs | 40 | 0 | |
| D | GA | 39 | 1 | 5 |
| D+V+ | Sr | 32 | 0 | |
| D+V+ | Cl | 76 | 4 | 5 |
| D+V+ | Cs | 38 | 2 | 5 |
| D+V+ | GA | 38 | 2 | 5 |

- The nine invalid cells by host: m06 seven (D+V+: Cl 3, Cs 2, GA 2), m22 one (D, GA), m26 one (D+V+, Cl). Each fails
  check 5 and no other check.
- Cells valid under the invariant reading of check 5 only (the line "c3b_tier invariant-only cells:" of
  `scripts/50 status`): V 0, D 0, DV 0. The two readings of check 5 therefore give the same validity for every cell.
- Pairs: 192 built, 0 rejected. No cell is missing.
- FIRE steps, median and largest: hosts 3444.5 and 4406; V+ 128.5 and 1395; D 116 and 1476; D+V+ 138.5 and 2097.
- Median seconds per FIRE step: hosts 2.52; frozen cells 2.88 (V+), 2.89 (D), 2.85 (D+V+).
- Summed relaxation walls (jobs ran side by side): hosts 19.31 h; V+ 31.86 h; D 29.75 h; D+V+ 37.80 h.

## 4. Gates

- `s2b_projection` at the point fr: P 181.39 h, U 3.32 h, P + U 184.71 h; at the point c3b: P 184.93 h, U 3.32 h,
  P + U 188.25 h; not over the cap of 520 node-h at either point. `points = ["fr", "c3b"]`, `cuts = []`,
  `c4b_run = false`, `c4b_origin` "decision (S2B amendment 2026-11-16a)". The inputs of the projection at c3b:
  H_spent 118.53 h, 0.1058 h per single point, 0.01438 h per frozen relaxation, 1.13 h for the host wave.
- `c3b_complete`: true; 544 of 544 labels complete, none missing.
- `c3b_tier`: computable true; valid hosts n_d: Sr 8, Cl 7, Cs 7, GA 6.
- C4b is not run in S2b (decision D-0, amendment 2026-11-16a). The route for E is therefore C4B-NOTRUN.

## 5. Interruptions and events

- **Spot reclaims.** Termination notices were recorded at 2026-11-17T14:10:28Z, 2026-11-18T14:35:29Z and
  2026-11-19T22:28:25Z. The first ended attempt 1 of all eight host relaxations: eight counted interruptions (cause
  "spot-notice"), each host rerun from the start as attempt 2. No cell has more than one counted interruption, and
  no RESOLVE was written. The second and third fell in the single-point phase.
- **Change of node.** From 2026-11-21 the campaign ran on another instance of the same type with the same data
  disk and a new system disk (first runner start there 2026-11-21T16:42:49Z). All MACE relaxations and 76 single
  points (the 68 of m06 and the first 8 of m02) ran on the first instance; the other 468 single points ran on the
  second.
- **A shutdown of unknown origin.** On 2026-11-23T05:32:21Z the runner received a shutdown signal with no job
  running and exited as designed (an interruption that is not counted and not a STOP). The node was started again
  and the runner resumed at 2026-11-23T12:01:25Z. The cause of the shutdown was not established.
- **Runner starts.** Five: 2026-11-17T14:07:34Z, 2026-11-17T18:01:40Z, 2026-11-19T22:22:27Z, 2026-11-21T16:42:49Z,
  2026-11-23T12:01:25Z. Single points published per start: 0, 75, 1, 357, 111.
- **Before the launch.** The first node check, at commit `840ad22`, failed on three self-test defects; they were fixed
  and the campaign commit became `e5883d5` (`C3B_OPERATIONS.md` section 8; amendment 2026-11-17a).
- No wait of D-C3-10 and no attempt kept under AM-C3-2 appears in the campaign log.

## 6. Single points

- 544 complete; none missing, skipped or not_started_cap.
- The number of resubmissions was not read: the files read for this note hold no counter of it.
- Timing, from the publication times in the campaign log (the interval between successive publications; the single
  points ran one after another): median 6.55 min on the first instance (74 intervals) and 6.17 min on the second
  (466 intervals), against 6.39 and 6.74 min in `C3_OPERATIONS.md` and 6.35 min in the projection. Two longer gaps,
  31.9 h and 6.7 h, are the outages of 18 to 19 November and of 23 November. The wall of each single point was not
  read from its output.

## 7. Phases and node-hours

- Phases by the campaign record: checks and pre-route 2026-11-17T14:07:41Z to 14:08:03Z; MACE 14:08:03Z to
  2026-11-18T06:28:07Z (16.33 h of wall clock, with the outage after the first reclaim); single points to
  2026-11-23T23:41:22Z (137.22 h of wall clock, with the outages); end gates to 23:41:33Z.
- Ledger at the end (2026-11-23T23:41:33Z): H_spent 203.67 h of the cap of 520 node-h; complete, no problem
  recorded. The five boots tagged c3b sum to 78.73 h (3.72, 22.05, 1.45, 39.79 and 11.72 h). Every c3b boot started
  after the end of fr.
- **The ledger over-counts.** The journals of the eleven boots before the change of system disk can no longer be
  read, and the ledger then takes the conservative end of each (last heartbeat + 60 s + 60 min + 15 min). The
  ledger total was 139.52 h at the last reading on the first instance (2026-11-19T22:24Z) and 152.17 h at the first
  reading on the second, before the campaign resumed. Most of that step of 12.65 h is over-count; this is an
  estimate, since the true ends of those boots are no longer recorded. It is inside the 203.67 h. The ledger was
  left as the code writes it; no manual row was added.
- H_spent is above the projection P + U of 188.25 h. The projection holds no term for outages or for the over-count.

## 8. Archive and verify

- Pull: 10 293 files; the listing of the node and the listing of the pulled copy (name, size and modification
  time per file) agree with 0 differences.
- Private archive, written outside every checkout by `scripts/50 archive`: 1457 json files, 1091 raw files, 544
  single-point labels, 1088 structures; `MANIFEST.sha256` lists 2550 files.
- Verify, run in a private root that holds `c3b/` only (`C3B_OPERATIONS.md` section 6):
  `c3b_verify/verify_c3b.txt`, "verify c3b: 3 gate files, 0 differ".
- The archive stays private until E.

## 9. Not checked

- **Reproducibility across the two instances.** No single point was run on both instances. The 76 single points of
  the first instance and the 468 of the second are used together on the assumption that the same binaries on the
  same data disk and processor type give the same energies. A re-run of a few cells of the first instance on the
  second is planned; its rule will be committed before any of its energies is read, and it is read after E.
- The resubmission count (section 6) and the wall of each single point.

## 10. What was read for this note, and what was not

Read: `campaign.json`, `completeness.json`, `interruptions.json`, `ledger.json`, the campaign log, the decision
fields of `state_end.json` that `scripts/50 status` prints, the node-hour and count fields of the `s2b_projection`
gate files, the decision, counts and missing list of `c3b_complete`, the status of the pair records, and, through
the blinded loader of `scripts/46` (which removes every MACE energy), these fields of the cell records: member,
cell kind, token, leg, `validity.valid`, `validity.failed`, `relax.steps`, `relax.converged`, `relax.wall_s`.

Not read: any single-point output, any label file, any MACE energy, `relax.stages`, any force field, the FIRE
traces, the `c3b_tier` gate file. No E_b, Y_h or δ of a production host has been computed, by DFT or by MACE. The raw
production outputs and every MACE energy stay unopened in the private archive until E; the blinding rests on not
opening them and not combining the raw energies.

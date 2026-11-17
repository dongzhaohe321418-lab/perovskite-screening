# S2b production campaign c3b: operating decisions, recorded before c3b starts (2026-11-17)

This note is the operations note that `C3_OPERATIONS.md` section 6 (2026-11-12) announces. It re-adopts
`C3_OPERATIONS.md` (OPS3) for the campaign `c3b`, provision by provision (section 4), and records the rulings of
2026-11-16 (amendment 2026-11-16a of `S2B_PLAN.md`, committed with this note). It cannot change any rule of `S2B_PLAN.md`. It holds decisions,
counts and procedure only: no S2 energy, no result value, no address, host name or instance id.

Every choice in this note was made knowing gate G2 and the read of `S2B_PLAN.md` section 6b (`S2B_PLAN.md` section 9,
"choices made knowing"). It was written without opening `c2/`, any `*.out.gz`, any record, gate file or structure
archive of C1, and nothing of `fr/` beyond what `FR_RESULT.md` reports: the decisions of the gates, the counts, the
validity of the four cells under both readings of check 5, and the geometry read of section 6b. No fr energy has been
read.

## 1. What c3b runs

- **Condition.** c3b runs only after gate FR passed and campaign `fr` ended done (`S2B_PLAN.md` sections 1, 3).
- **Scope.** n = 8 production hosts (the Stage-0 list `production_n8`), default poses, the dopants Sr, Cl, Cs and GA;
  no Ca (G1). Per host: 1 host relaxation, 67 frozen MACE relaxations and 68 single points.
- **Counts, asserted at every graph build (`scripts/50` N-C3B1).** 8 host relaxations, 152 V+ relaxations, 384 dopant
  relaxations, 544 single points, 4 gate evaluations.
- **Gates.** In phase `pre`: `s2b_projection` at the point `fr`, then at the point `c3b`. In phase `gate`:
  `c3b_complete`, then `c3b_tier`. c3b has no other gate, and these gates belong to no other campaign.
- **The site table.** The first-shell and far sites of the eight hosts are geometry only. The table is checked before
  any job: by the runner before the route is consumed and at every graph build (`scripts/49` `c3b_sites_check`, and
  the 544 single-point labels of its quartets equal to those of the graph), and by `scripts/49` at both projection
  points. Gate `c3b_tier` receives the same table at the end.
- **The two projection files.** Both points write `c3b/gates/s2b_projection.json`; the point `c3b` overwrites the
  point `fr`. The evaluation at the point `fr` is kept as `c3b/gates_applied/gate_s2b_projection_fr.gate.json`.
  Verify recomputes the files of `gates/` only, so it reproduces the point `c3b`, not the point `fr`.
- **A projection point evaluated twice.** If the node is lost after a projection decision reached the state and
  before its marker was written, the relaunch evaluates that point again and accepts only the same decision.
- **C4b is not run in S2b, by decision** (amendment 2026-11-16a, D-0). There is no c4b code at the c3b commit. The
  runner refuses a c3b start when a `c4b` tree or a `campaigns.c4b` entry exists. The state records
  `s2b_projection.c4b_run = false` with `s2b_projection.c4b_origin = "decision (S2B amendment 2026-11-16a)"`.
  The route of the evaluation is "C3b ended; C4b not run (decision)".
- **Budget.** `s2b_projection` evaluates P + U, with U = R = 0.05 (P - H_spent): fr has ended and C4b is not run, so no
  A2 allowance is left. H_spent is that of `fr/ledger.json` (complete) at the point `fr` and of the live ledger at the
  point `c3b`. When P + U exceeds 520 node-h nothing can be cut: the decision is not applied, no marker is written and
  the runner stops (section 3, STOP 4). The hard cap of `S2_PLAN.md` section 16 is unchanged.
- **Check 5.** Every c3b relaxation of a V+, D or D+V cell carries `check5_reading = "invariant"` (`S2B_PLAN.md` X4);
  host relaxations do not. The record's `validity` then holds `valid` and `failed` under the invariant reading, and
  `check5_reading`, `valid_as_written`, `failed_as_written` and `invariant_only`, the leaf names that `validity_a2`
  writes. The `scripts/46` self-test on the changed file, with the public reference cell present, passes its
  15 cases, the new case "check5-a1-c3b" among them (analyst, 2026-11-16, in a copy of the tracked files outside the
  blinded paths).

## 2. The c3b campaign commit and its route

- **One commit.** c3b runs at one commit, a strict descendant of the recorded fr campaign commit
  (`campaign_commit.fr`). It is admitted once, by the file `c3b/CAMPAIGN_COMMIT` in the campaign directory of the node,
  which holds exactly one line of three tokens:

      <40-hex commit> 2026-11-17 results/objective2/s2/C3B_OPERATIONS.md

- **What the route checks (`scripts/50` N-C3B3).** The commit is the checkout HEAD; the date is YYYY-MM-DD and occurs in
  this note; this note is tracked at HEAD and changed since `campaign_commit.fr`; `campaign_commit.fr` is an ancestor
  of HEAD and not HEAD itself; `results/objective2/s2/s2b/e_block4.py` is tracked at HEAD and assigns
  `BLOCK4_IMPLEMENTED` exactly once, by the line `BLOCK4_IMPLEMENTED = True` at the start of a line; this note holds
  no date token, open mark or draft mark; `qe_queue.sh`, `chain.sh` and `s2_run_qe.sh` are those of the recorded S2
  commit; C2 is done; the line passes the hygiene check of `scripts/46`. A refusal names every reason and records
  nothing.
- **Checks made before the route is consumed (`scripts/50` N-C3B8).** c3b has no fix route, so the runner first makes
  every check that needs no node work: the preconditions of section 3 item 2; one graph build with the pinned counts;
  the site table; the completeness of `fr/ledger.json`; and a dry evaluation of `s2b_projection` at the point `fr`,
  made by `scripts/49 run --dry-run` in a child process (lead, 2026-11-16: no gate logic runs in the runner's
  process; no gate file is written and no decision applied). A STOP at this stage records no commit. After the remedy, the same commit
  or a new one is admitted by a route file.
- **No fix route.** Later starts need HEAD = `campaign_commit.c3b`. A STOP whose remedy needs a code or data change
  ends c3b in "stop and re-plan" by a dated amendment (OPS3 D-C3-3). The fr route files `STEP0_FIX` and
  `STEP0_NO_ERROR` are not read by c3b.
- **What a c3b runner may write in the state (N-C3B2).** `campaign_commit.c3b`, `s2b_projection`, `c3b_complete`,
  `c3b_tier`, `campaigns.c3b` and new `commit_history` entries. Every other key is protected: a change is a STOP
  naming the key, with nothing written. `K2`, `K3`, `step0`, `cuts` and `c4_run` are never read.

## 3. Refusals and STOPs that are new in c3b

1. **Refused before the runner writes anything (exit 2; N-C3B4).** The launcher `s2_campaign.sh` has by then made
   the directory `c3b/` (which already holds the route file) and `c3b/driver.out`, and has printed "started": the
   refusal text is in `c3b/driver.out`, which the operator reads after every start. The reasons: the state is unreadable; `campaigns.fr` is not
   `done`; there is no `fr/CAMPAIGN_DONE`; `FR.outcome` is not `pass` with `part` null; an `fr_stop` is recorded;
   `fr_step0.outcome` is not `pass`; `fr/campaign.json` does not record status `done` with `fr_outcome` `pass`; or a
   `c4b` tree or `campaigns.c4b` entry exists.
2. **Precondition STOPs (N-C3B4).** c1 or c2 not done; c3 not `not_run`; a c4 campaign state; `scripts/49` mocked or
   without the c3b gates, or `C4B_PLANNED` not false; n not 8 or the n rule not applied; G1 not (Ca false, Cl true);
   a pose of Cs or Cl not `default`; no Stage-0 list of eight hosts.
3. **Decision STOPs (N-C3B5).** A c3b gate decision that holds another key than its own, or other fields than
   (`points`, `cuts`, `c4b_run`, `c4b_origin`), a boolean, or (`computable`, `n_d`), is not applied.
4. **Over the cap (N-C3B5).** `result.over_cap` true, or absent, at either point: not applied, no marker; a relaunch
   evaluates the gate again. No job starts before both points are applied.
5. **Reading of check 5 (N-C3B6).** A record of a V+, D or D+V cell without the invariant reading is a STOP of the
   runner, and gate `c3b_tier` refuses it as well.
6. **End (N-C3B5).** `CAMPAIGN_DONE` is written only when the state holds `s2b_projection` with the points `fr` and
   `c3b` and `c4b_run` false, a boolean `c3b_complete`, and `c3b_tier` with `computable` and `n_d` of Sr, Cl, Cs, GA.
7. **Archive (N-C3B7).** `archive --campaign c3b` refuses an `--out` whose last component is not exactly `c3b`, or
   that lies inside this checkout, under `results/objective2/s2` of any checkout, or below any directory that holds
   `.git`.
8. **Site table (N-C3B8).** A table that `scripts/49` refuses, or whose quartet labels are not the single-point
   labels of the graph, stops c3b before the route is consumed, at a graph build, or at a projection point.

## 4. `C3_OPERATIONS.md`, provision by provision

Where a provision is kept, it applies with "C3" read as "c3b", `c3/` as `c3b/`, `jobs/s2c3` as `jobs/s2c3b`, and "the
one evaluation" as "E" (`S2B_PLAN.md` section 1).

| OPS3 provision | status | for c3b |
|---|---|---|
| section 1: commit, preconditions, graph, gates | adapted | sections 1 and 2 of this note |
| section 1: cost and hard cap | adapted | P + U by `s2b_projection`; H_spent from the fr ledger, then the live one; cap 520 node-h unchanged |
| D-C3-1 publication of the archive | adapted | the c3b archive is private until E (`S2B_PLAN.md` X15); the not_run exception lapses; section 6 |
| D-C3-2 no production start in the boot that ends the previous campaign | kept | c3b starts in a new boot, after fr is pulled, archived, committed and verified; "not_run starts" are superseded by refusal 1 of section 3 |
| D-C3-3 STOPs that need a fix | kept | no fix route (section 2) |
| D-C3-4 completeness with skipped single points | adapted | gate `c3b_complete`, the same test over the 544 labels |
| D-C3-5 reclaims during the host wave | kept | |
| D-C3-6 attempts ended by the shutdown | kept | |
| D-C3-7 what the operator reads | adapted | decisions and counts, and for completeness, validity and timings only; adds the four check-5 leaves, the fields of `s2b_projection`, `c3b_tier.computable` and `c3b_tier.n_d`; no energy and no quartet value |
| D-C3-8 the MACE environment | kept | section 5, check 4 |
| D-C3-9 an invalid host | kept | the host still runs all its cells; `c3b_tier` counts it as not valid |
| D-C3-10 a MACE attempt at its wall limit | kept | see section 7 for the resume window |
| D-C3-11 rerun tally | kept | |
| D-C3-12 a final STOP | kept | the stop note follows `S2B_PLAN.md` section 1: the one file `results/objective2/s2/C3B_STOP_NOTE.md`, committed, holding the phrase "the c3b STOP is final" and an ISO date, and passed to E as `--stop-note` (amendment 2026-11-16a; `s2b/e_block4.py` `tier_route`) |
| D-C3-13 this note | adapted | this note is the note of the route and is committed in the c3b commit |
| D-C3-14 the node is reserved | kept | |
| D-C3-15 the D3(BJ) amendment | superseded | by `S2B_PLAN.md` section 1 |
| D-C3-16 rules carried over from C2 | kept | D-C2-8 as `S2B_PLAN.md` section 9 step 9 (X17) |
| D-C3-17 accepted as the code reads them | adapted | no `STEP0_FIX` route; verify as section 6; node checks of section 5 at the c3b commit |
| D-C3-18 what the result note reports | adapted | adds both projections (P, U, P + U per point), `cuts = []`, `c4b_run = false` with its origin, `n_d` per dopant and the count of invariant-only cells per cell kind (V, D, DV), read from the line "c3b_tier invariant-only cells:" that `scripts/50 status` prints (three counts; no label and no gate file is opened by the operator); "the one evaluation" becomes E |
| AM-C3-1 to AM-C3-3 | kept | re-dated by this note for c3b |
| section 5 (2026-11-11 notice) | kept | the not_run c3 archive stays private (`S2B_PLAN.md` X14) |

## 5. Checks before the launch (all at the c3b commit; a failure is no launch)

1. **Self-tests on the node.** The unmodified self-tests of `scripts/46`, `scripts/47`, `scripts/49` and `scripts/50`
   pass on the node, in the clean checkout at the c3b commit, as committed (no shim, no edited fixture):
   `python -B scripts/<file> --self-test` for each, one process at a time. What ran before this commit, on the changed
   files, in a copy of the tracked files outside the blinded paths with the public fixtures present (analyst,
   2026-11-16): `scripts/46` 15 cases, `scripts/47` 15 cases and `scripts/49` 19 cases, none failed. **The self-test
   of `scripts/50` has not run on the changed file anywhere:** the development sandbox refuses the local socket its
   mock spot endpoint binds. Its ten module-level c3b cases ran there through a harness (15 checks, none failed), and
   a mutation pass over the runner and gate changes caught 130 of 131 single mutations; the survivor (the count of
   544 labels not compared) is judged equivalent by reading, which no test shows. The end-to-end mock campaign of
   the `scripts/50` self-test therefore runs for the first time on the node. A failure there is no launch: the node
   is stopped and the defect is fixed in a dated commit before any route file is written.
2. **Byte identity of the inputs.** `results/objective2/s2/s2b/c3b_inputs.py` (pattern of `fr_inputs.py`), run on the
   node with the scripts of a checkout of `8bff03e` (`--repo`) and with those of the c3b commit, and compared:
   - production side: `c3b_inputs.py dryrun --repo REPO --member m06 --out DIR` (the unrelaxed pool member,
     `partners="unrelaxed"`, no calculator): 19 regions, 24 default-pose pairs and 68 single-point inputs;
   - C1 side: `c3b_inputs.py write-c1 --repo REPO --source node --root /data --state STATE --out DIR`: every region
     and pair of the node's C1 tree rebuilt and equal to its C1 record, and the default-pose single-point inputs;
   - `c3b_inputs.py compare DIR_A DIR_B` for each side: exit 0, "0 differ". A `.meta.json` may differ in `campaign`,
     `written` and `time` only; `scripts/47` is unchanged between the two commits.
   The archive source of `write-c1` is for the analyst only. Both stages of its self-test pass (analyst, 2026-11-16,
   same copy: "0 differ" on the C1 side and on the dry run of 19 regions, 24 pairs and 68 inputs). The two node
   commands above have not run anywhere yet; they run on the node before the route file is written.
3. **Node scripts.** `s2_campaign.sh` accepts `c3b` only; `s2_relaunch.sh` knows `c3b`; `qe_queue.sh`, `chain.sh` and
   `s2_run_qe.sh` are byte-identical with the recorded S2 commit (the route checks this as well).
4. **MACE environment.** As OPS3 D-C3-8.
5. **Block 4.** `s2b/e_block4.py` is implemented (the route refuses the stub). E's self-test at this commit
   (`python -B -I results/objective2/s2/s2b/e_selftest.py`, groups A-D and T): 94 of 94 cases pass and 258 of 259
   broken variants are caught. The one not caught, `A9/worktrees_unlisted`, needs a second git worktree of the
   repository to be detectable; the repository has one (amendment 2026-11-16a, "What was tested").
6. **State.** fr is pulled, archived, committed and verified; the node state shows fr done and FR pass; no `c4b`
   tree exists on the node.
7. **Idle self-stop period.** Confirmed (section 7).
8. **Node dry run, before the route file is written.** In the clean checkout at the c3b commit:
   `python -B scripts/50_s2_campaign.py graph --campaign c3b --state <the node's state.json>` prints the counts
   8 / 152 / 384 / 544 / 4 (it also checks the site table against `scripts/49` and the graph's labels); and
   `python -B scripts/49_s2_gates.py run --gate s2b_projection --campaign c3b --root /data --inputs <file> --dry-run`,
   with `<file>` holding `{"point": "fr", "H_spent_h": <H_spent_h of fr/ledger.json>}`, prints one line `DRY {...}`
   with `"over_cap": false` and writes nothing. The runner repeats these checks itself before it consumes the route
   (section 2).
9. **The private root.** The directory that will receive `c3b/` lies in no checkout: no directory above it holds
   `.git`.
10. **The note is final.** This file holds none of the three marks the route refuses (section 2).

## 6. End of c3b: archive, manifest, verify

- **Archive.** `scripts/50 archive --campaign c3b --out <private root>/c3b`, in no checkout (section 3 item 7). The layout is
  that of the earlier campaigns, unchanged. The last step writes `MANIFEST.sha256`: one line
  `<sha256>  <relative path>` (two spaces) per file of the archive except the manifest itself, sorted by path. The
  archive result records the number of files and the sha256 of the manifest.
- **Fixed line of the c3b note.** The note `results/objective2/s2/C3B_NOTE.md` holds exactly one line
  `c3b/MANIFEST.sha256 sha256: <64 hex>`, the sha256 of the manifest file. E reads the manifest against this line
  (`s2b/e_block4.py` `MANIFEST_LINE`); this wording replaces the runner-side proposal of 2026-11-16.
- **What E requires of the private archive (`s2b/e_block4.py` `tier_route`, at admission; a defect is a refusal with
  nothing written).** The manifest lists every file of `c3b/` but itself, each path once, sorted bytewise by path,
  as `scripts/50` writes it. Every name under `c3b/records`, `c3b/raw`, `c3b/pairs` and `c3b/regions` belongs to the
  production graph. No entry named `c4b` in any form exists under the public or the private root. A file added to
  `c3b/` after the manifest is written (a file browser's metadata file, for example) is a refusal until it is
  removed: the private `c3b/` directory is not opened in a file browser and nothing is written into it by hand.
- **Verify.** Verify of c3b is meant to need the c3b tree alone (its gate inputs are recorded in the tree), so that
  the private root may hold `c3b/` only (`S2B_PLAN.md` section 9 step 5: "verify in a root without c3"). This has
  been shown at the level of `scripts/49` only: in its self-test (case "S2b c3b run CLI") `scripts/49 verify`
  reproduces the three gate files on a synthetic node root after its c1 tree is removed, with the status parser
  replaced. No verify of a real or archived c3b tree has run. Ruling (lead, 2026-11-17): verify is first run in a
  private root that holds `c3b/` only. If it cannot run there because it needs a file of another campaign, it is
  run in a second private directory that also holds copies of the committed public `c1/`, `c2/` and `fr/` archives,
  and the verify record says so in one added first line; the archive that E reads stays the root that holds `c3b/`
  only. The record is `results/objective2/s2/c3b_verify/verify_c3b.txt`: the OK / DIFF lines of `scripts/49 verify`,
  one per gate file, and its summary line "verify c3b: 3 gate files, 0 differ".
- **A final STOP.** The runner publishes no `state_end.json` at a STOP. E admits a stopped c3b without that file,
  requires the stop note of D-C3-12, and checks the two `s2b_projection` leaves below only when the file exists
  (`s2b/e_block4.py` `tier_route`). When c3b is done the file is required.
- **What `c3b/state_end.json` carries for block 4 (interface).** `c3b_tier.computable`;
  `c3b_tier.n_d.{Sr,Cl,Cs,GA}`, the number of valid hosts per dopant by `S2_PLAN.md` lines 680-682 under the invariant
  reading (a host is valid for d when both far quartets of d are valid and at least the minimum number of its
  first-shell quartets on d's sublattice are); `computable` is true when n_d >= 2 for one of Cl, Cs, GA;
  `s2b_projection.{points, cuts, c4b_run, c4b_origin}` with `points = ["fr", "c3b"]`, `cuts = []`,
  `c4b_run = false`.
- **Nothing of c3b is committed before E** except this note, the verify record and the result note of D-C3-18.

## 7. The idle self-stop period of the node

The operator confirmed on 2026-11-17 that the node stops itself after 30 minutes without a job. The code assumes
60 minutes (`IDLE_STOP_S = 3600.0` in `scripts/50`). The constant is not changed. Two things depend on it:

- **The ledger of a boot whose end is not journalled.** Its end is assumed as the last heartbeat + 60 s + 60 min +
  15 min. With a 30-minute period this over-counts H_spent by up to 30 minutes per such boot. The error is on the safe
  side of the cap; `ledger/manual.json` gives the true stop time by boot id and removes it.
- **The resume window of OPS3 D-C3-10.** "The resume follows within about 45 min, before the idle self-stop of 60 min"
  does not hold at 30 minutes. For c3b: the resume follows within about 20 minutes of the end of the drain; otherwise
  the node is taken as stopped and the next start is a new boot.
- **Between the checks of section 5 and the launch.** The checks and the launch are made in one sitting, so that no
  gap of 30 minutes without a job occurs between the last check and the start of the runner.

## 8. Addendum of 2026-11-17: the first node check, and the commit that replaces `840ad22`

Section 5 item 1 says that the self-test of `scripts/50` had not run anywhere. It ran on the node on 2026-11-17 at
`840ad22` and failed: 77 cases, 3 failed. No route file was written and nothing of c3b started. The three failures
are defects of three test cases, not of the runner; amendment 2026-11-17a of `S2B_PLAN.md`, committed with this
addendum, gives the causes, the correction (inside `self_test` only), what the corrected self-test shows (77 cases,
none failed, in a separate clone on the node; the mock c3b campaign reaches CAMPAIGN_DONE) and what it does not.

- **The c3b campaign commit is the commit of this addendum**, not `840ad22`. Section 2 applies to it unchanged.
- **Section 5 applies to it in full.** Every check is repeated in a clean checkout of this commit. In item 2 the
  comparison copy of `8bff03e` must hold `results/objective2/s2/stage0` as well as `scripts` and `results/fa_host`:
  the first C1-side comparison lacked it and printed "4 differ" for the four Cl cells of m30 for that reason alone.
- **One deviation from item 1.** The node was not stopped after the failure; it was kept running without a job while
  the cases were diagnosed (amendment 2026-11-17a). The hours count towards the cap.
- **E's self-test** (item 5) was not repeated for this commit: no file of E changed.

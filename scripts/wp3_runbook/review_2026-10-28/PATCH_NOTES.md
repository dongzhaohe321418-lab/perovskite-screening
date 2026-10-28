<!-- Copied from the review workspace /private/tmp/claude-501/drvreview/patch/ (not kept). Paths below refer to it; the e2e harness and fixtures are not in the repository. The patched files are committed as scripts/wp3_runbook/{node_step2.sh,node_step34.sh,rb_verify_inputs.py}. -->
# WP3 node drivers: consolidated patch proposal (2026-10-28)

Scope: the verified findings on `scripts/wp3_runbook/node_step2.sh` and `node_step34.sh` (repository at
`aab4b03`, branch `feat/dopant-shell-dft-validation`). Nothing in the repository, under `/data` or on the node was
changed. All work is in `/private/tmp/claude-501/drvreview/patch/`.

| file | role | sha256 |
|---|---|---|
| `node_step2.sh` | proposed step-2 driver | `08f9f77aaae4895a89d8c27c615d698fa6424f2e5766b9b0c857ee6b19c2e1a8` |
| `node_step34.sh` | proposed step-3/4 driver | `2bd67ed60da3180dfa97cfaabb52c5255834ec4dae4ca4a08c9eae3b94638c1b` |
| `rb_verify_inputs.py` | proposed 2d helper (the only change that can reach the RUNNING step-2 driver) | `8116e7570f7f207d107715d508b0ca8309203143fa0ec021e1a8ad08718eefb3` |
| `orig/*` | committed copies (`git show HEAD:`; `cmp`-identical to the working tree) | `d7d9d897…` (step2), `37986b19…` (step34), `257b6f04…` (helper) |
| `node_step2.diff`, `node_step34.diff`, `rb_verify_inputs.diff` | `diff -u committed proposed` (also reproduced at the end of this file) | |

`bash -n` passes on both drivers; the helper byte-compiles.

## 1. What to do, in order

1. **`rb_verify_inputs.py`: deploy first, before step 2a ends.** The running driver calls it fresh at line 78 (2d),
   so this is the only way to gate the RUNNING driver against a frame or input lost in the 21:03 hard stop (R3, F5a).
   Commit it together with the drivers, then update the node checkout `/data/work/ps_wp3` (for example
   `git fetch` and then `git checkout <commit>`) before 2d runs. The step-1 scripts (29, 30, 32, 33, 35, 37–41) are
   unchanged, so the hashes that scripts/40 records stay the same. If 2d then fails, the queue never starts: see
   section 3, item R3.
2. **`node_step2.sh`: NO relaunch is needed.** None of its changes alters what the running process still has to do.
   R10, R11/F8/F14 and the lock act only on a relaunch; F10b is backed up by step 3/4's own finality check, and R3 by
   the helper. Install it by atomic rename, never in place (R15). For example: `scp` it to
   `/data/work/wp3_step2.sh.new`, check its sha256, then `mv` it over `/data/work/wp3_step2.sh`. The running bash
   keeps reading its open (old) inode, and only a future relaunch after a reclaim uses the new file. The running
   instance holds no `step2.lock`, so before ANY relaunch check that
   `pgrep -f 'wp3_step2.sh|35_finetune_frames|qe_queue|pw.x'` prints nothing (on a fresh boot it cannot).
3. **`node_step34.sh`: install before `/data/work/wp3/STEP2_DONE` appears (about 20 h away).** Use the same
   `.new` + sha256 + `mv` procedure, and first check that `pgrep -f wp3_step34.sh` prints nothing. The STEP2_DONE
   watcher then starts the new file.
4. Commit the three files and keep the node copies byte-identical to the commit. Then add the runbook text listed in
   section 5. That text is required by item 2: the operator side of the restart protocol, and the reading of
   runbook line 175.

## 2. Decisions this patch makes that a human should confirm

- **D1 (F10a, F1/R7): resubmitting an item-1′ re-run that stopped.** Amendment m item 1′ (PLAN.md lines 530–532)
  gives two allowances: a stop without JOB DONE is resubmitted (as in 1d), and an unconverged SCF is re-run once.
  Runbook line 175 instead says the re-run "counts as the queue's retry". The runbook says the amendment governs
  (lines 12–13), so the patch follows the amendment.
  - An interrupted item-1′ re-run is resubmitted once: proposed `node_step34.sh` lines 44–54.
  - A later stop is given up by the queue's own counter.
  - To keep the runbook reading instead, delete lines 44–54. Every other fix still holds, because the queue then
    gives up on the interrupted re-run, which is also final.
  - Either way, runbook line 175 must be changed to match.
- **D2 (R4): the second abnormal end stops.** The driver auto-restarts after the first non-node-loss abnormal end.
  It stops for a human at the second one even if the two causes differ, which is stricter than item 2's "same cause
  twice". A human who judges the causes different relaunches with `PREV_CAUSE='<cause> <UTC time>'`.
- **D3 (R6): deadline for the Initial record.** A run with no Initial record by (2-epoch timing at T) + 30 min is
  killed. It is recorded as `[abnormal end]`, item 2's "a kill signal".
- **D4 (F9): re-running an interrupted scripts/33.** scripts/33 is re-run only if an earlier run was cut short
  (`s33.done` is absent). The re-run is logged. The cut-short run produced no usable dataset, so this is not a second
  evaluation under m 1e "run once".
- **D5 (F12): timing tie-break.** Equal timing wall times now resolve to the fewest threads. Example: with
  `8 3 / 16 3 / 32 4`, the committed code picks 16 by lexical order and the patch picks 8. State this rule in the
  WP3 note.

## 3. Finding by finding

IDs that occur twice in the input are split: **F5a** is node_step2 line 78 (2d input integrity) and **F5b** is
node_step34 line 36 (archive). **F10a** is qe_queue line 14 (retry counting) and **F10b** is node_step2 line 87
(STEP2_DONE finality). Line numbers marked "p." refer to the proposed file.

**node_step34.sh**

- **F1, R7** (line 22–23: a queue retry was taken for the item-1′ re-run). Fixed at p. line 39. A second re-run is
  now refused only if an earlier `.out.try*` itself holds JOB DONE. qe_queue renames only outputs without JOB DONE,
  and this block renames only outputs with it, so such a try can only be an earlier item-1′ re-run. Evidence:
  - The spec `m18_GA_img4` is attempt 1 FAIL, attempt 2 UNCONV.
  - Committed: `unconverged after a queue retry: no further run`, and item1p.missing has
    `('m18_GA_img4','SCF not converged')` (scen `O0_full`).
  - Patched: `re-run once (out.try2)`, then attempt 3 runs, and only `m04_undoped_img3` (gave up) is missing
    (scen `P0_full`).
  - On relaunch an unconverged re-run is refused with no QE call (`K1d_p_unconv_again_relaunch`).
- **F2, R1** (line 26: the chain ran only when n > 0). The rename loop, the resubmission loop, an unconditional
  idempotent `chain.sh wp3 wp3x wp3chk` and a finality check all run before the marker (p. lines 35–63).
  - Case B, reclaim during the m14_Sr_img3 re-run (`K1_*`). Committed: the truncated `m14_Sr_img3.out.gz` is
    archived with 0 JOB DONE, item1p.missing has `('m14_Sr_img3','no JOB DONE')`, and STEP34_DONE is written.
    Patched: the job is resubmitted, attempt 3 converges and the run ends `done`.
  - Case A, reclaim after the mv and before the queue (`K1b_*`). Committed: `STOP: scripts/33 stopped`, with
    `retry pending (…out.try1.gz) with neither a final output nor a .gaveup`. Patched: the queue runs the job, then
    `done`.
- **F10a** (qe_queue line 14: the item-1′ rename uses up the 1d retry). qe_queue is unchanged. The driver resubmits
  an interrupted re-run once (D1, p. lines 44–54). Only outputs whose earlier tries all hold JOB DONE are renamed;
  once a try without JOB DONE exists, the queue decides. Evidence:
  - `K1_p`: resubmitted, then converged.
  - `K1c_p_resub_fails`: the resubmission fails, giving `.out.try3` + `.gaveup`, and item1p.missing has
    `('m14_Sr_img3','gave up')`.
  - Every attempt stays as `.out.tryN` and is recorded in `item1p_rerun.list` (runbook 2e "Record each such re-run").
- **F10b, step-3/4 side** (chain.sh returns 0 while another queue holds the campaign lock). Before the chain, the
  driver waits on each `/tmp/qe_queue_<c>.lock`, then checks that every input has JOB DONE or a `.gaveup`; otherwise
  it stops (p. lines 56–60). Evidence, `K12_*` (an outside holder of `qe_queue_wp3x.lock` with one wp3x job pending):
  - Committed: the queue log says `already running`, the archive is written and the run ends `STOP: scripts/33 stopped`.
  - Patched: it waits about 5 s, the chain runs the pending job, and the run ends `done`.
- **F3, R2** (line 81: a partial timing.txt was accepted). Lines go to `timing.part`, which is renamed to `timing.txt`
  only after all three runs. A pass that was cut short is logged, its leftovers are removed and all three counts are
  re-timed. A completeness assert sits before T is chosen (p. lines 125–141). Evidence:
  - `K4_*`, a kill during the 16-thread run. Committed: `8 4; -> T=8`, with `timing_16/` and `timing_16.stdout` left
    behind. Patched: `cut short (finished: 8 4;): discarded, all three repeated`, then `8 4;16 3;32 3; -> T=16`.
  - `R2_*`, the 16-thread run fails, then a relaunch. The results are the same, and the committed run also leaves
    both STEP34_STOPPED and STEP34_DONE.
- **F12** (line 88: tie-break). `sort -k2,2n -k1,1n` picks the fewest threads among equal wall times (D5).
- **R4** (line 92: fixed run1, no restart path). Replaced by a loop over `run<n>` (p. lines 143–194):
  - **Discard rule.** An earlier run without `wp3.model` is discarded unread. It is never deleted or reused, and
    `--restart_latest` is never used. The identical `ARGS` command runs in the first free `run<n>`, which is new and
    empty.
  - **Restart record.** Each restart goes to `$W/restarts.txt` as `<UTC> run<k> discarded unread <cause>`, for the
    5b restart list. Causes are classified:
    - `[node loss]`: the node booted after the run started (`/proc/stat` btime > `run<k>.start`). The record also
      gives the last results write.
    - `[abnormal end]`: seen by the driver, with the exit code and a traceback tail.
    - `[start check FAIL]`: corrected by hand first.
    - `[operator] $PREV_CAUSE`: an end the driver cannot classify, or an operator override.
  - **Second abnormal end.** A second `[abnormal end]` stops for a human (D2).
  - **Model present.** A run with `wp3.model` and no driver verdict stops for 5a by hand.
  - **KEEP_ALIVE.** It is touched again at line 111 on every relaunch and kept throughout.
  - Evidence:
    - `K5_*` (reclaim before Initial) and `K6_*` (reclaim mid-training). Committed: `STOP: …/run1 exists`, and
      KEEP_ALIVE is removed. Patched: `run1 discarded unread [node loss] the node booted at …, after run1 started
      at …; last results write …`, then run2 starts in an empty dir (`work_dir_empty_at_start: true`) and the run
      ends `done`.
    - `K6b_p` (no reboot): `STOP: run1 ended without wp3.model while no driver watched it …`. Relaunching with
      PREV_CAUSE gives `[operator] …`, then run2 and `done`.
    - `K7_p` (model written, reclaim before 5a): `STOP: run1 has wp3.model: … run 5a by hand`.
- **F6, R6, F7(1)** (line 97: a death before the Initial record was logged as a start-check FAIL). No Initial record
  now means an abnormal end, with its exit code and traceback in `run<n>.end`, and the deadline of D3 applies
  (p. lines 170–178).
  - Committed (`K8_o`): `STOP: start check FAIL, run killed: Traceback … rb_startcheck.py …`, which is rb_startcheck's
    own FileNotFoundError.
  - Patched (`K8_p`): `run1 [abnormal end] ended before the Initial record, exit 1 … RuntimeError: STUB crash …`.
    The run is discarded, and run2 crashes the same way, giving `STOP: run2: second abnormal end (…; earlier: …)`.
  - `K8b_p`: a crash in run1 only gives one restart, then `done`.
  - `K8c_p`: after the stop, an operator relaunch (PREV_CAUSE) gives run3 and `done`.
  - `R6_pdl_deadline`: a test-only variant with +5 s in place of +1800 s, in which runs hang before Initial. Both are
    killed and recorded, then the second abnormal end stops.
  - Start-check FAIL (`SC_p`): `STOP: start check FAIL (Initial record read)`, and `run1.end` = `[start check FAIL]`.
    After the correction, the relaunch logs `run1 discarded unread [start check FAIL] …`, then run2 and `done`.
  - That test also found an ordering bug in my first draft, now fixed at p. line 153: a start-check-FAIL run could
    already hold `wp3.model` and was then misread as "model written". The driver's own `.end` verdict now takes
    precedence.
- **F7(2)** (lines 108–112: a checker crash was reported as a technical failure). rc 0 means PASS. Lines starting
  `non-finite` mean "technical failure". Anything else means `technical-failure CHECK ERROR, no verdict`
  (p. lines 197–202).
  - `K9_*` (junk model, real rb_techfail; it fails at load, so no MACE evaluation runs). Committed:
    `STOP: technical failure: … UnpicklingError`. Patched: `CHECK ERROR, no verdict`.
  - `K9b_*` (NaN loss): both versions report `technical failure: non-finite loss …`.
- **F5b, R5** (lines 31–37: the archive could not be resumed). `frames_copied`, `archived_<c>` and `s33.done` are
  commit markers, each touched after `sync`. A part with no marker is removed and redone from `/data/jobs` (p. lines
  69–80). `K2_*` is a kill after 37 archived files.
  - Committed: `EXISTS …/m05_GA_md300.in.gz`, `STOP: archive wp3`, and a truncated `.gz` is left behind.
  - Patched: `removed and redone`, all 194 `.gz` files `zcmp`-equal to their sources, then `done`.
- **F9** (silent set -e exits; non-atomic scripts/33 output). Three changes:
  - An ERR trap that calls stop() and logs the exit code, line and command text.
  - An EXIT trap for every other non-zero exit.
  - `s33.done` (p. lines 89–97).
  Evidence:
  - `K3c_*` (hard stop during the scripts/33 write; the meta is truncated to 3000 B). Committed: the 3d python raises
    JSONDecodeError and the driver exits 1 with no STOP line and no STEP34_STOPPED. Patched: `scripts/33 cut short
    earlier: removed, scripts/33 re-run`, then `done`.
  - `R9a_*` (rb_test_hosts.py exits 3). Committed: exit 3 with no log line and no marker. Patched:
    `STOP: unexpected error (exit 3) at line …: TH=$($PY scripts/wp3_runbook/rb_test_hosts.py)`, plus STEP34_STOPPED,
    and KEEP_ALIVE is removed.
- **R9** (exit paths and markers):
  - (a) ERR and EXIT traps, as above.
  - (b) A TERM, HUP or INT exits 143 through the EXIT trap. KEEP_ALIVE is removed only if no training pid is alive
    (`ka_off`). `L3`: a SIGTERM mid-training logs `STOP: unexpected exit 143` and
    `training pid … still running: /data/KEEP_ALIVE kept; finish 4d-5a by hand`.
  - (c) STEP34_STOPPED is cleared at launch (compare `R2_o`, which ends with both markers).
  - (d) A STEP34_DONE guard.
  - (e) The lock (F4).
  - (f) Not changed, deliberately. stop() still removes a KEEP_ALIVE that this launch did not create. After a reclaim
    mid-training, `/data/KEEP_ALIVE` survives on `/data`, and the next stop must clear it so the idle cron can stop
    the node.
- **F4, F14(lock)** (no single-instance lock). `exec 8>>$W/step34.lock; flock -n 8` sits before any stop() call
  (p. line 17). fd 8 is inherited by the chain and the nohup'ed training. A refused instance logs `launch refused`
  and exits 0, never calling stop(), so it cannot remove KEEP_ALIVE under a live run.
  - `L1`: a second instance 1 s later is refused.
  - `L2`: with the driver bash alone SIGKILLed mid-training, a relaunch is refused while the training lives. After
    the training ends, the relaunch stops with `run1 has wp3.model: … run 5a by hand`, and KEEP_ALIVE is removed.
- **R15** (in-place writes). The body is wrapped in `{ … ; exit; }`, so bash parses the whole file before running
  it. The header says how to install. The install procedure is in section 1.
- **R3, F5a (step-3/4 backstop)**. The helper runs again before the archive and stops on a damaged frame or input
  (p. lines 65–68).
  - `I4_*` (an empty `.in` for m08_GA_rat10f, which gave up). Committed: archived, with 3d listing
    `dropped [{'label': 'm08_GA_rat10f', 'reason': 'gave up'}]`, and the run ends `done`; this is the silent 1d drop
    of R3. Patched: `STOP: input check FAILED before the archive`, with
    `m08_GA_rat10f: WP3 frame or input unreadable (ValueError: empty file; … input 0 B)`.
  - `I3_*` (an empty frame). Committed: the archive is written, then scripts/33 crashes. Patched: it stops before
    the archive.

**node_step2.sh** (all changes act only on a relaunch; see section 1, item 2)

- **R10** (line 29: exits at the first failed host while others run). It now waits for every pid, then exits 1 with
  `all others have ended`. `S2_*` (host 15 fails fast, host 20 is slow). Committed: the driver exits after 0.6 s
  while one `35_finetune_frames.py --hosts 20` is still running, and `m20.done` appears afterwards. Patched: it exits
  after 10.3 s with 0 survivors.
- **F4, F14(lock)**. `step2.lock` on fd 8 is inherited by scripts/35 and the chain, and a refused instance exits 0. A
  `STEP2_DONE` guard is added (p. lines 15–16). `S3_*` (a second instance during 2a). Committed: two
  `--hosts 20` writers run at the same time. Patched: `node_step2 already running …`, and one writer. `S4`: a relaunch
  after STEP2_DONE exits at once with no log lines.
- **R11, F8, F14(merge)** (line 45). The merge uses `shutil.rmtree(F); os.makedirs(F)`; the report is absent, so an
  earlier merge was cut short. It also calls `os.sync()` before the report rename and fsyncs the directory after it.
  `S1_*` (a merge cut short: 16 frames and no report). Committed: `FileExistsError` with no log line. Patched:
  `merged 96 records, 96 frames`, then STEP2_DONE.
- **F10b** (line 87). The driver waits for outside queue locks, then requires every input to be final before
  `sync; touch STEP2_DONE` (p. lines 95–103). `S5_*` (an outside holder of `qe_queue_wp3x.lock` for 45 s).
  Committed: STEP2_DONE is written with 0 of 50 wp3x jobs final. Patched: it waits, runs them, reaches 50 of 50, then
  STEP2_DONE.
- **ERR logging** (R9, for step 2). `on_err` logs `STOP: unexpected error … STEP2_DONE not written` (`S6`: a corrupt
  part report). Committed: the last log line is `2a: per-host scripts/35 done`.
- **R15**: brace wrap and header, as for step 3/4.
- **F5a, R3** (line 78: 2d did not check the 96 WP3 inputs). Fixed in `rb_verify_inputs.py`, not in the bash file,
  so that it reaches the running driver. For every ok record it requires:
  - the `/data/jobs/wp3` job dirs are exactly the ok labels;
  - the frame and the input are non-empty;
  - the input equals its frame to 1e-6 Å;
  - for an input not yet run, sha256 equals the fsynced `<label>.meta.json` `input_sha256`. "Not yet run" means no
    `.out`, `.out.try*` or `.gaveup`, and pseudo_dir still `'/data/pseudo'` as scripts/30 line 45 writes it. That last
    condition prevents a false alarm in the instant after `run_qe.sh` has rewritten pseudo_dir and before pw.x has
    created the `.out`.

  Every label is wrapped in try/except and all failures are listed. Evidence:
  - The pristine pre-DFT fixture (96 real scripts/35 inputs with meta, from the integration run) passes.
  - The post-DFT snapshot passes.
  - The fixture with pseudo_dir rewritten and no `.out` passes.
  - The damaged fixture exits 1 and lists all six planted faults: a missing job dir, a stray dir, a truncated input
    (geometry + sha), an empty input, an empty frame, and an input with one byte appended (sha). The committed
    helper prints `ALL INPUT CHECKS PASS` and exits 0 on the damaged fixture.

  A full patched step-2 run (`S0`, with run35 stub inputs) passes 2d with the sha check active.

  **If 2d fails on the node.** The queue has not started, so nothing is dropped. Write it up as an amendment
  question, not as a 1d drop. For a lost `.in` with an intact frame, the input can be rewritten with
  `a30.write_input` and must hash to the meta. For a lost frame, a decision is needed (R3 better_fix 3).

  **Optional read-only check now.** The reviewers' `robustness/integrity/chk_wp3_integrity.py --all` over the six
  `frames_parts/m*` covers the same ground. It is valid only once all six hosts have finished, because labels still
  being generated look like stray dirs.
- **Not done here: fsync in scripts/35** (R3 better_fix 4). scripts/35 is hashed by scripts/40 and is outside the
  two drivers; the new gate catches the loss instead.

## 4. Reproductions (harness: copy of the reviewers' e2e harness, `patch/e2e`; scenario logs in `patch/e2e/scen/<name>/`)

| scenario | committed (`o_`) | proposed (`p_`) |
|---|---|---|
| full run (`O0_full`/`P0_full`) | m18_GA_img4 not re-run; missing `SCF not converged` | re-run, converged; done |
| K1 kill during item-1′ re-run | truncated out.gz archived; `no JOB DONE`; STEP34_DONE | resubmitted (1d), converged; done |
| K1b kill after mv, before queue | STOP scripts/33 `retry pending` | queue runs it; done |
| K1c resubmission fails again | — | `.out.try3` + `.gaveup`; missing `gave up` |
| K12 outside queue holds wp3x lock | archived with pending jobs; STOP scripts/33 | waits, runs them; done |
| K2 kill mid-archive | `EXISTS …`; STOP archive wp3 | removed and redone; 194/194 zcmp-equal; done |
| K3c hard stop in scripts/33 write | JSONDecodeError, no STOP line, no marker | scripts/33 re-run; done |
| R9a set -e failure (rb_test_hosts) | exit 3, no log, no marker | STOP line with command; STEP34_STOPPED |
| K4 kill during 16-thread timing | T=8 from `8 4;`; timing_16 left | all three re-timed; T=16; no leftovers |
| R2 16-thread timing fails, relaunch | T=8 from one point; STOPPED+DONE both | all three re-timed; STOPPED cleared |
| K5/K6 reclaim before Initial / mid-training | STOP `run1 exists`, KEEP_ALIVE removed | `[node loss]` recorded; run2 (empty); done |
| K6b run lost, no reboot | — | STOP needs PREV_CAUSE; then `[operator]`; done |
| K7 reclaim after wp3.model, before 5a | — | STOP: run 5a by hand |
| K8 crash before Initial (every run) | STOP `start check FAIL` (FileNotFoundError) | `[abnormal end]` → run2 → second → STOP |
| K8b crash in run1 only | — | one restart; done |
| SC start-check FAIL then correction | — | `[start check FAIL]` recorded; run2; done |
| K9 junk model (real rb_techfail) | STOP `technical failure: UnpicklingError` | STOP `CHECK ERROR, no verdict` |
| K9b NaN loss | technical failure | technical failure |
| I3 / I4 lost frame / empty input that gave up | crash at scripts/33 / silent `gave up` drop, done | STOP before archive, label listed |
| L1/L2/L3 lock, driver SIGKILL, SIGTERM | (no lock) | refused; refused while training lives; KEEP_ALIVE kept, STOP 143 |
| step 2: S1 merge cut short | FileExistsError, no log line | merge redone; STEP2_DONE |
| step 2: S2 failing host + slow host | exits at 0.6 s, 1 orphan writer | waits (10.3 s), 0 survivors |
| step 2: S3 second instance | 2 concurrent `--hosts 20` writers | refused |
| step 2: S5 outside wp3x queue | STEP2_DONE with 0/50 wp3x final | waits; 50/50; STEP2_DONE |

The K-scenarios above ran while the patch was being finished. After the last two edits (the `.end`-first
ordering at p. line 153, and the `[ -e $o ]` guard at p. line 47), `P0`, `K1`, `K5`, `K7` and `K8b` were re-run on
the final file (`F_*`). All behaved as before, and every step-2 scenario used the final `node_step2.sh`.

Re-run a scenario with `tools/pscen.sh <name> <p|o> '<kill condition>' '<spec line>' '<hook>' '' '<pre>'`,
`tools/lockscen.sh` or `tools/s2prep.sh` plus `tools/launch.py`. The commands are in this session's transcript; the
harness drivers are produced by `tools/mkdrv.sh` from the files here.

**Harness limits**
- **Stubs.** QE, MACE training and the physics of scripts/35 are stubs, and no MACE evaluation ran. rb_techfail's
  MACE step is stubbed, except in K9, which fails at model load.
- **bash version.** The Mac has bash 3.2.57; the node has 5.2.
  - (a) The step-2 harness copy rewrites `"${pids[@]}"` to `${pids[@]+"${pids[@]}"}`, the same substitution as the
    reviewers' `node_step2_b32.sh`. This is not needed on 5.2.
  - (b) In 3.2, `$LINENO` inside the brace group reports the group's last line, which is why the ERR message also
    carries the command text.
  - (c) bash 3.2 exits 0 on a `set -u` error, so the EXIT-trap path for that case could not be exercised. On 5.2
    the exit status is non-zero and on_exit logs `STOP: unexpected exit`. This is expected but untested.
- **Shims.** GNU `date -d @N`/`-r FILE` and `/proc/stat` btime are shimmed; a reboot is simulated by raising btime.
  `flock` is the reviewers' fcntl shim, and fd inheritance by the training was tested (L2).

## 5. Runbook text to add (not edited here)

1. **2e, line 175.** Either "An item-1′ re-run that stops without JOB DONE is resubmitted once with the identical
   input (m 1′, 1d); a second stop is given up", which is D1, or keep the current sentence and drop patch lines
   44–54.
2. **2d.** The check also covers the 96 WP3 inputs (job set, non-empty, geometry, meta sha before the first run), and
   node_step34 repeats it before 3a.
3. **4b.** Timing is all or nothing (`timing.part` → `timing.txt`). Ties go to fewer threads.
4. **Node drivers.** Add:
   - Install a patched driver as `.new` → sha256 → `mv`. Never write onto a running driver.
   - Before a relaunch, check with `pgrep` that no earlier instance or child is alive.
   - After a reclaim, relaunch `node_step34.sh` by hand: a `[node loss]` restart is automatic.
   - When the driver stops asking for it, relaunch with `PREV_CAUSE='<cause> <UTC time>'`.
   - Never delete or reuse a `run<n>`.
   - `restarts.txt` and `item1p_rerun.list` go into the 5b model note and the WP3 result.
5. **Node-restart routine.** After a console restart that is not followed by a driver relaunch,
   `rm -f /data/KEEP_ALIVE`. It survives a reclaim on `/data`. Use this rather than an @reboot cron, which would be
   persistent configuration and needs the user's decision.
6. **4e.** A manual run keeps `/data/KEEP_ALIVE`. If `step34.log` ends with `STOP: unexpected exit 143` while a run
   is alive, wait for it to end, then do 4d–5a by hand.

## 6. Unified diffs (`diff -u committed proposed`)

### node_step2

```diff
--- scripts/wp3_runbook/node_step2.sh (committed, aab4b03)
+++ patch/node_step2.sh (proposed)
@@ -3,12 +3,21 @@
 # 2a  scripts/35: one process per training host into its own --frames dir (same params, label seeds),
 #     merged into one frames dir, then the literal all-host invocation resumes over it (no new frames).
 # 2b  50 item-1' inputs; 2c 8 chk_ inputs; 2d rb_verify_inputs.py must pass; 2e QE chain wp3 wp3x wp3chk.
+# Resumable: relaunch by hand after a reclaim. Never edit this file in place while it runs: install a new copy
+# under another name, then mv it over this path (the running bash keeps reading the old file).
 set -euo pipefail
+{   # the whole body is parsed before any of it runs
 R=/data/work/ps_wp3; PY=/data/miniforge3/envs/mace/bin/python; W=/data/work/wp3; J=/data/jobs
 HOSTS="05 06 08 12 15 20"
-cd $R
 mkdir -p $W/frames_parts $W/logs
+# one instance only; the lock (fd 8) is inherited by scripts/35 and the QE chain, so a relaunch is also refused while
+# a process started by an earlier instance is alive (two scripts/35 writers in one --frames dir clobber each other)
+exec 8>>$W/step2.lock; flock -n 8 || { echo "node_step2 already running, or a process it started holds $W/step2.lock" >&2; exit 0; }
+[ -e $W/STEP2_DONE ] && { echo "STEP2_DONE exists: nothing to do" >&2; exit 0; }
+cd $R
 log(){ echo "[$(date -u +%FT%TZ)] $*" >> $W/step2.log; }
+on_err(){ c=${BASH_COMMAND%%$'\n'*}; log "STOP: unexpected error (exit $1) at line $2: ${c:0:160}; STEP2_DONE not written"; }
+trap 'on_err $? $LINENO' ERR
 log "start; repo $(git rev-parse --short HEAD), dirty: $(git status --porcelain | wc -l)"
 
 # 2b: item-1' inputs (no MACE)
@@ -26,7 +35,8 @@
       > $W/logs/s35_m$h.log 2>&1 && touch $W/frames_parts/m$h.done ) &
   pids+=($!)
 done
-for p in "${pids[@]}"; do wait $p || { log "2a: a scripts/35 process failed (see logs)"; exit 1; }; done
+rc=0; for p in "${pids[@]}"; do wait $p || rc=1; done     # wait for every host, so none is left running on exit
+[ $rc = 0 ] || { log "2a: a scripts/35 process failed (see logs); all others have ended"; exit 1; }
 log "2a: per-host scripts/35 done"
 
 # merge into one frames dir (records in host order, as one all-host process writes them)
@@ -42,16 +52,18 @@
     m["source_sha256"].update(r["source_sha256"])
 labels = [x["label"] for x in m["records"]]
 assert len(labels) == 96 and len(set(labels)) == 96, len(labels)
-F = os.path.join(W, "frames"); os.makedirs(F)
+F = os.path.join(W, "frames"); shutil.rmtree(F, ignore_errors=True); os.makedirs(F)   # no report: an earlier merge was cut short
 n = 0
 for p in parts:
     for f in sorted(glob.glob(os.path.join(p, "*.extxyz"))):
         shutil.copy2(f, F); n += 1
 assert n == sum(x["ok"] for x in m["records"]), (n, sum(x["ok"] for x in m["records"]))
+os.sync()                                            # the frames reach the disk before the report that marks the merge done
 tmp = os.path.join(F, "frames_report.json.tmp")
 with open(tmp, "w") as fh:
     json.dump(m, fh, indent=1); fh.flush(); os.fsync(fh.fileno())
 os.replace(tmp, os.path.join(F, "frames_report.json"))
+fd = os.open(F, os.O_RDONLY); os.fsync(fd); os.close(fd)
 print(f"merged {len(labels)} records, {n} frames")
 EOF
 fi
@@ -80,8 +92,13 @@
 fi
 log "2d: $(tail -1 $W/logs/verify_inputs.log)"
 
-# 2e: the DFT, one 64-rank queue at a time
+# 2e: the DFT, one 64-rank queue at a time (first wait out any queue started outside chain.sh)
 log "2e: chain wp3 wp3x wp3chk started"
+for c in wp3 wp3x wp3chk; do flock /tmp/qe_queue_$c.lock true; done
 /data/setup/chain.sh wp3 wp3x wp3chk
-log "2e: chain finished"
-touch $W/STEP2_DONE
+for i in $J/wp3/*/*.in $J/wp3x/*/*.in $J/wp3chk/*/*.in; do b=${i%.in}
+  grep -qs "JOB DONE" $b.out || [ -e $b.gaveup ] || { log "2e: $(basename $b) has neither a JOB DONE output nor a .gaveup after the chain: STEP2_DONE not written"; exit 1; }
+done
+log "2e: chain finished; every input final"
+sync; touch $W/STEP2_DONE
+exit; }
```

### node_step34

```diff
--- scripts/wp3_runbook/node_step34.sh (committed, aab4b03)
+++ patch/node_step34.sh (proposed)
@@ -1,54 +1,99 @@
 #!/bin/bash
 # WP3 steps 3-4 driver (PLAN amendment m item 7 steps 3-4; WP3_RUNBOOK.md 2e item-1' re-runs, 3a-3c, 4a-4d).
 # Runs on the node as ericdft in the clean checkout, after /data/work/wp3/STEP2_DONE exists.
-# Stops (fail-closed, nothing further started) at: scripts/33 stop or W < 60, a pre-flight FAIL, a start-check
-# FAIL, or a training run that ends without wp3.model. Those cases are handled by hand under amendment m item 2.
+# Stops (fail-closed, nothing further started) at: a QE input not final or not equal to its frame, scripts/33 stop
+# or W < 60, a pre-flight FAIL, a start-check FAIL, a second abnormal end of training, or a training end it cannot
+# classify. Those cases are handled by hand under amendment m item 2.
+# Resumable: after a reclaim, relaunch this file by hand. A training run without wp3.model is discarded unread and
+# the identical command runs from scratch in a new, empty run<n>; each restart is listed with cause and time in
+# $W/restarts.txt. Never edit this file in place while it runs: install a new copy under another name, then mv it.
 set -euo pipefail
+{   # the whole body is parsed before any of it runs
 R=/data/work/ps_wp3; PY=/data/miniforge3/envs/mace/bin/python; MT=/data/miniforge3/envs/mace/bin/mace_run_train
 W=/data/work/wp3; J=/data/jobs; D=$R/results/objective2/dopant_shell; FM=/home/ericdft/.cache/mace/20231203mace128L1_epoch199model
-cd $R
 log(){ echo "[$(date -u +%FT%TZ)] $*" >> $W/step34.log; }
-stop(){ log "STOP: $*"; touch $W/STEP34_STOPPED; rm -f /data/KEEP_ALIVE; exit 1; }
+# one instance only; the lock (fd 8) is inherited by the QE chain and the nohup'ed training, so a relaunch is also
+# refused while a run started by an earlier instance is alive. A reboot releases it.
+exec 8>>$W/step34.lock; flock -n 8 || { log "launch refused: another node_step34, or a process it started, holds step34.lock"; exit 0; }
+[ -e $W/STEP34_DONE ] && { log "launch: STEP34_DONE exists, nothing to do"; exit 0; }
+rm -f $W/STEP34_STOPPED; pid=""
+cd $R
+ka_off(){ if [ -n "$pid" ] && kill -0 $pid 2>/dev/null; then log "training pid $pid still running: /data/KEEP_ALIVE kept; finish 4d-5a by hand"; else rm -f /data/KEEP_ALIVE; fi; }
+stop(){ log "STOP: $*"; touch $W/STEP34_STOPPED; ka_off; exit 1; }
+on_err(){ c=${BASH_COMMAND%%$'\n'*}; stop "unexpected error (exit $1) at line $2: ${c:0:160}"; }
+on_exit(){ rc=$?; { [ $rc = 0 ] || [ -e $W/STEP34_STOPPED ]; } && return; log "STOP: unexpected exit $rc"; touch $W/STEP34_STOPPED; ka_off; }
+trap 'on_err $? $LINENO' ERR
+trap on_exit EXIT
+trap 'exit 143' TERM HUP INT
 [ -e $W/STEP2_DONE ] || stop "STEP2_DONE missing"
 [ "$(sha256sum $FM | cut -c1-64)" = 01bfe22100139f424713cf921144e5509cbe353d67aa9fa1be9c6e1e0ed35845 ] || stop "foundation sha256"
 log "start; repo $(git rev-parse --short HEAD)"
 
-# 2e (item 1'): an SCF that ends with JOB DONE but without convergence is re-run once with identical settings
+# 2e (item 1'): an SCF that ends with JOB DONE but without convergence is re-run once with identical settings.
+# qe_queue renames only outputs WITHOUT JOB DONE and this block only outputs WITH it, so a .out.try* that holds
+# JOB DONE marks an earlier item-1' re-run. Each step is idempotent, so a relaunch after a reclaim resumes it.
 if [ ! -e $W/item1p_rerun.done ]; then
-  n=0
-  for o in $J/wp3x/*/*.out; do
+  for o in $J/wp3x/*/*.out; do b=${o%.out}; L=$(basename $b)
     grep -q "JOB DONE" $o || continue
     grep -q "convergence has been achieved" $o && continue
-    b=${o%.out}; k=$(ls $b.out.try* 2>/dev/null | wc -l || true)
-    [ $k -ge 1 ] && { log "item-1' $(basename $b): unconverged after a queue retry: no further run"; continue; }
-    mv $o $b.out.try$((k+1)); n=$((n+1)); log "item-1' $(basename $b): JOB DONE without SCF convergence -> re-run once (out.try$((k+1)))"
+    grep -qs "JOB DONE" $b.out.try* && { log "item-1' $L: unconverged after its item-1' re-run: no further run"; continue; }
+    k=$(ls $b.out.try* 2>/dev/null | wc -l || true)
+    mv $o $b.out.try$((k+1)); echo "$(date -u +%FT%TZ) $L re-run (unconverged output -> out.try$((k+1)))" >> $W/item1p_rerun.list
+    log "item-1' $L: JOB DONE without SCF convergence -> re-run once (out.try$((k+1)))"
   done
-  [ $n -gt 0 ] && { /data/setup/chain.sh wp3x; log "item-1' re-runs finished ($n)"; }
-  touch $W/item1p_rerun.done
+  # m 1' and 1d: a re-run that stopped without JOB DONE (e.g. a reclaim) is resubmitted once with the identical input.
+  # qe_queue alone would count the item-1' rename as its retry; once a try without JOB DONE exists, the queue decides.
+  for o in $J/wp3x/*/*.out; do b=${o%.out}; L=$(basename $b)
+    [ -e $o ] || continue
+    grep -q "JOB DONE" $o && continue
+    grep -qs "JOB DONE" $b.out.try* || continue
+    f=0; for t in $b.out.try*; do grep -q "JOB DONE" $t || f=$((f+1)); done; [ $f = 0 ] || continue
+    k=$(ls $b.out.try* | wc -l)
+    mv $o $b.out.try$((k+1)); echo "$(date -u +%FT%TZ) $L resubmitted (re-run stopped without JOB DONE -> out.try$((k+1)))" >> $W/item1p_rerun.list
+    log "item-1' $L: re-run stopped without JOB DONE -> resubmitted once with the identical input (m 1d; out.try$((k+1)))"
+  done
+  # every QE input final before the archive: wait out any queue started outside chain.sh, then the (idempotent) chain
+  for c in wp3 wp3x wp3chk; do flock /tmp/qe_queue_$c.lock true; done
+  /data/setup/chain.sh wp3 wp3x wp3chk
+  for i in $J/wp3/*/*.in $J/wp3x/*/*.in $J/wp3chk/*/*.in; do b=${i%.in}
+    grep -qs "JOB DONE" $b.out || [ -e $b.gaveup ] || stop "QE input not final after the chain: $(basename $b) (neither a JOB DONE output nor a .gaveup)"
+  done
+  sync; touch $W/item1p_rerun.done
+  log "item-1' re-runs and resubmissions: $(cat $W/item1p_rerun.list 2>/dev/null | wc -l || true) (item1p_rerun.list); every QE input final"
 fi
 
-# 3a: archive into the checkout (m 1e layout)
-if [ ! -e $D/wp3/frames/frames_report.json ]; then
-  mkdir -p $D/wp3/frames && cp -p $W/frames/*.extxyz $W/frames/frames_report.json $D/wp3/frames/
+# 3a: every input still equals its frame (as at 2d; a frame or input lost in a hard stop is not a 1d drop)
+$PY scripts/wp3_runbook/rb_verify_inputs.py $J $W/frames > $W/logs/verify_inputs_3a.log 2>&1 \
+  || stop "input check FAILED before the archive (logs/verify_inputs_3a.log): a damaged frame or input is an amendment question"
+log "3a: $(tail -1 $W/logs/verify_inputs_3a.log)"
+# 3a: archive into the checkout (m 1e layout). A marker, written after sync, is the commit point of each part.
+if [ ! -e $W/frames_copied ]; then
+  rm -rf $D/wp3/frames; mkdir -p $D/wp3/frames
+  cp -p $W/frames/*.extxyz $W/frames/frames_report.json $D/wp3/frames/; sync; touch $W/frames_copied
 fi
 for c in wp3:raw wp3x:test_extra/raw wp3chk:chk/raw; do src=${c%%:*}; dst=$D/wp3/${c#*:}
   [ -e $W/archived_$src ] && continue
+  [ -e $dst ] && log "3a: $dst without archived_$src (cut short earlier): removed and redone from $J/$src"
+  rm -rf $dst
   bash scripts/wp3_runbook/rb_archive.sh $J/$src $dst >> $W/step34.log 2>&1 || stop "archive $src"
-  touch $W/archived_$src
+  sync; touch $W/archived_$src
 done
 left=$(find $D/wp3 \( -name '*.out' -o -name '*.in' -o -name '*.out.try?' \) | wc -l)
 [ "$left" = 0 ] || stop "uncompressed files in the archive: $left"
 x=$W/v2prod_x; rm -rf $x; mkdir -p $x && tar xzf $D/wp1_production/v2prod_structures.tar.gz -C $x
 log "3a: archived; $(ls $D/wp3/raw | wc -l) wp3, $(ls $D/wp3/test_extra/raw | wc -l) item-1', $(ls $D/wp3/chk/raw | wc -l) chk files"
 
-# 3b-3c: scripts/33, the m 1e command, once
+# 3b-3c: scripts/33, the m 1e command, once (re-run only if an earlier run was cut short: no s33.done)
 TH=$($PY scripts/wp3_runbook/rb_test_hosts.py)
 log "3b: test hosts: $TH"
-if [ ! -e $D/wp3/dataset/dataset_meta.json ]; then
+if [ ! -e $W/s33.done ]; then
+  [ -e $D/wp3/dataset ] && log "3c: dataset dir without s33.done (scripts/33 cut short earlier): removed, scripts/33 re-run"
+  rm -rf $D/wp3/dataset
   $PY scripts/33_finetune_dataset.py --dft results/objective2/dopant_shell \
       --frames ../bands $x/v2prod results/objective2/dopant_shell/wp3/frames \
       --out results/objective2/dopant_shell/wp3/dataset --test-hosts $TH --valid-hosts m21 \
       > $W/logs/s33.log 2>&1 || stop "scripts/33 stopped (see logs/s33.log)"
+  sync; touch $W/s33.done
 fi
 for f in train.xyz valid.xyz test.xyz E0s.json dataset_meta.json; do [ -s $D/wp3/dataset/$f ] || stop "scripts/33 wrote no $f (W < 60 or UNDECIDED)"; done
 $PY - $D/wp3/dataset/dataset_meta.json >> $W/step34.log <<'EOF'
@@ -77,39 +122,84 @@
 $PY scripts/wp3_runbook/rb_preflight.py $P/logs/wp3_run-123.log $DS $FM $WE > $W/logs/preflight.txt 2>&1 || stop "pre-flight FAIL (logs/preflight.txt)"
 log "4a: pre-flight PASS"
 
-# 4b: timing run at 8, 16, 32 threads, 2 epochs each; only wall time is read, outputs deleted
+# 4b: timing run at 8, 16, 32 threads, 2 epochs each; only wall time is read, outputs deleted. timing.txt appears
+# (by mv) only once all three have finished; a pass cut short is discarded and all three are repeated.
 if [ ! -s $W/timing.txt ]; then
-  for T in 8 16 32; do d=$W/timing_$T; rm -rf $d; mkdir $d
+  if [ -e $W/timing.part ] || ls -d $W/timing_[0-9]* > /dev/null 2>&1; then
+    log "4b: an earlier timing pass was cut short (finished: $(tr '\n' ';' < $W/timing.part 2>/dev/null || true)): discarded, all three repeated"
+  fi
+  rm -rf $W/timing.part $W/timing_8 $W/timing_16 $W/timing_32 $W/timing_8.stdout $W/timing_16.stdout $W/timing_32.stdout
+  for T in 8 16 32; do d=$W/timing_$T; mkdir $d
     t0=$(date +%s); OMP_NUM_THREADS=$T $MT "${ARGS[@]}" --max_num_epochs 2 --work_dir $d > $d.stdout 2>&1 || true; t1=$(date +%s)
     [ -s $d/wp3.model ] || stop "timing run at $T threads did not finish (see $d.stdout)"
-    echo "$T $((t1-t0))" >> $W/timing.txt; rm -rf $d $d.stdout
+    echo "$T $((t1-t0))" >> $W/timing.part; rm -rf $d $d.stdout
   done
+  sync; mv $W/timing.part $W/timing.txt
 fi
-T=$(sort -k2 -n $W/timing.txt | head -1 | cut -d' ' -f1)
+[ "$(cut -d' ' -f1 $W/timing.txt | tr '\n' ' ')" = "8 16 32 " ] || stop "timing.txt does not hold exactly the 8, 16 and 32 thread runs"
+T=$(sort -k2,2n -k1,1n $W/timing.txt | head -1 | cut -d' ' -f1)   # fastest; equal wall times: fewer threads
 log "4b: timing (threads, s for 2 epochs): $(tr '\n' ';' < $W/timing.txt) -> T=$T"
 
-# 4c-4d: training with the start check
-RUN=$W/run1; [ -e $RUN ] && stop "$RUN exists"
-mkdir $RUN; cd $RUN
-OMP_NUM_THREADS=$T nohup $MT "${ARGS[@]}" --max_num_epochs 100 --work_dir $RUN > $RUN.stdout 2>&1 &
-pid=$!; echo $pid > $RUN.pid; cd $R
-log "4c: training started, pid $pid, threads $T, run $RUN"
-until grep -qs '"epoch": null' $RUN/results/wp3_run-123_train.txt || ! kill -0 $pid 2>/dev/null; do sleep 30; done
-if $PY scripts/wp3_runbook/rb_startcheck.py $RUN/results/wp3_run-123_train.txt $B > $W/logs/startcheck.txt 2>&1; then
-  log "4d: start check PASS: $(cat $W/logs/startcheck.txt)"
-else
-  kill $pid 2>/dev/null || true; stop "start check FAIL, run killed: $(cat $W/logs/startcheck.txt)"
-fi
-wait $pid || true
-[ -s $RUN/wp3.model ] || stop "training ended without wp3.model (abnormal end: see $RUN.stdout)"
-log "4: training finished; wp3.model sha256 $(sha256sum $RUN/wp3.model | cut -c1-64)"
+# 4c-4d: training with the start check, in a new, empty run<n> (item 2 Interruptions; never --restart_latest).
+# A run that ended without wp3.model is discarded unread and listed in restarts.txt with its cause and time:
+# [node loss] (the node booted after the run started), [abnormal end] (seen by the driver: exception, OOM, kill,
+# non-zero exit), [start check FAIL] (corrected by hand first) or [operator] (relaunch with PREV_CAUSE='<cause>').
+# A second [abnormal end] stops for a human (item 2 Deterministic causes: the same cause twice is a technical failure).
+BT=$(awk '/^btime/{print $2}' /proc/stat)
+while true; do
+  n=1; while [ -e $W/run$n ]; do n=$((n+1)); done; RUN=$W/run$n
+  if [ $n -gt 1 ] && ! grep -qs " run$((n-1)) discarded unread " $W/restarts.txt; then
+    Q=$W/run$((n-1)); q=$(basename $Q)
+    if [ -s $Q.end ]; then cause=$(cat $Q.end)                     # the driver's verdict (a start-check FAIL run is void even with a model)
+    elif [ -s $Q/wp3.model ]; then stop "$q has wp3.model: judge it from its log and run 5a by hand (item 2 'Model written, then abnormal exit')"
+    elif [ "$BT" -gt "$(cat $Q.start 2>/dev/null || echo 9999999999)" ]; then
+      cause="[node loss] the node booted at $(date -u -d @$BT +%FT%TZ), after $q started at $(date -u -d @$(cat $Q.start) +%FT%TZ); last results write $(date -u -r $Q/results/wp3_run-123_train.txt +%FT%TZ 2>/dev/null || echo none)"
+    else cause=""; fi
+    if [ -n "${PREV_CAUSE:-}" ]; then cause="[operator] $PREV_CAUSE${cause:+; driver: $cause}"; PREV_CAUSE=""
+    elif [ -z "$cause" ]; then stop "$q ended without wp3.model while no driver watched it and without a reboot: list its cause, then relaunch with PREV_CAUSE='<cause> <UTC time>'"
+    elif [[ $cause == "[abnormal end]"* ]] && grep -qs "\[abnormal end\]" $W/restarts.txt; then
+      stop "$q: second abnormal end ($cause; earlier: $(grep '\[abnormal end\]' $W/restarts.txt | tail -1)). The same cause twice in succession is a technical failure (item 2); if the causes differ, relaunch with PREV_CAUSE='<cause>'"
+    fi
+    echo "$(date -u +%FT%TZ) $q discarded unread $cause" >> $W/restarts.txt; sync
+    log "4c: $q discarded unread $cause; the identical command runs in $RUN"
+  fi
+  date +%s > $RUN.start; mkdir $RUN; cd $RUN
+  OMP_NUM_THREADS=$T nohup $MT "${ARGS[@]}" --max_num_epochs 100 --work_dir $RUN > $RUN.stdout 2>&1 &
+  pid=$!; echo $pid > $RUN.pid; cd $R
+  log "4c: training started, pid $pid, threads $T, run $RUN"
+  t_end=$(( $(date +%s) + $(awk -v t=$T '$1==t{print $2}' $W/timing.txt) + 1800 ))   # Initial comes before epoch 1
+  until grep -qs '"epoch": null' $RUN/results/wp3_run-123_train.txt || ! kill -0 $pid 2>/dev/null || [ $(date +%s) -ge $t_end ]; do sleep 30; done
+  if ! grep -qs '"epoch": null' $RUN/results/wp3_run-123_train.txt; then     # an abnormal end, not a start-check result
+    why="ended before the Initial record"
+    kill -0 $pid 2>/dev/null && { kill $pid; why="killed by the driver: no Initial record within the 2-epoch time + 30 min"; }
+    rc=0; wait $pid || rc=$?; pid=""
+    echo "[abnormal end] $why, exit $rc, $(date -u +%FT%TZ): $(tail -3 $RUN.stdout | tr '\n' ' ')" > $RUN.end; sync
+    log "4c: $(basename $RUN) $(cat $RUN.end)"; continue
+  fi
+  SC=$W/logs/startcheck_run$n.txt
+  if $PY scripts/wp3_runbook/rb_startcheck.py $RUN/results/wp3_run-123_train.txt $B > $SC 2>&1; then
+    log "4d: start check PASS: $(cat $SC)"
+  else
+    kill $pid 2>/dev/null || true; wait $pid 2>/dev/null || true; pid=""
+    echo "[start check FAIL] $(date -u +%FT%TZ): $(tr '\n' ' ' < $SC)" > $RUN.end; sync
+    stop "start check FAIL (Initial record read), run killed: $(cat $SC). Record and correct the cause (towards m only), then relaunch: $(basename $RUN) is discarded and the identical command runs in a new run (not the retry)"
+  fi
+  rc=0; wait $pid || rc=$?; pid=""
+  if [ -s $RUN/wp3.model ]; then
+    [ $rc = 0 ] || log "4: $(basename $RUN) exited $rc after writing wp3.model: judged from its log (item 2 'Model written, then abnormal exit')"
+    break
+  fi
+  echo "[abnormal end] exit $rc after the start check, $(date -u +%FT%TZ): $(tail -3 $RUN.stdout | tr '\n' ' ')" > $RUN.end; sync
+  log "4c: $(basename $RUN) $(cat $RUN.end)"
+done
+log "4: training finished in $RUN; wp3.model sha256 $(sha256sum $RUN/wp3.model | cut -c1-64); restarts: $(cat $W/restarts.txt 2>/dev/null | wc -l || true) (restarts.txt)"
 
-# 5a: technical-failure check (training log, results file, m21 only)
-if $PY scripts/wp3_runbook/rb_techfail.py $RUN $DS > $W/logs/techfail.txt 2>&1; then
-  log "5a: $(tail -1 $W/logs/techfail.txt)"
-else
-  stop "technical failure: $(tail -3 $W/logs/techfail.txt | tr '\n' ' ')"
-fi
+# 5a: technical-failure check (training log, results file, m21 only); exit 1 with no verdict line is a checker error
+rc=0; $PY scripts/wp3_runbook/rb_techfail.py $RUN $DS > $W/logs/techfail.txt 2>&1 || rc=$?
+if [ $rc = 0 ]; then log "5a: $(tail -1 $W/logs/techfail.txt)"
+elif grep -q '^non-finite' $W/logs/techfail.txt; then stop "technical failure: $(grep '^non-finite' $W/logs/techfail.txt | head -3 | tr '\n' ' ')"
+else stop "technical-failure CHECK ERROR, no verdict (exit $rc; not a technical failure until judged by hand): $(tail -3 $W/logs/techfail.txt | tr '\n' ' ')"; fi
 rm -f /data/KEEP_ALIVE
-touch $W/STEP34_DONE
+sync; touch $W/STEP34_DONE
 log "done"
+exit; }
```

### rb_verify_inputs

```diff
--- scripts/wp3_runbook/rb_verify_inputs.py (committed, aab4b03)
+++ patch/rb_verify_inputs.py (proposed)
@@ -1,10 +1,16 @@
-# RUNBOOK step 2d: check the scripts/30 item-1' and chk_ inputs BEFORE any DFT (run from the repo root).
+# RUNBOOK step 2d: check the scripts/30 item-1' and chk_ inputs and the scripts/35 WP3 inputs BEFORE any DFT
+# (run from the repo root; node_step34 runs it again before the 3a archive).
 #   python rb_verify_inputs.py <jobs root> <scripts/35 frames dir>
 # Every <jobs>/wp3x/<label>/<label>.in must be one of the 50 item-1' labels, every <jobs>/wp3chk/<label>/<label>.in
 # one of the 8 chk_ labels of m 1c (md300 where md450 was rejected); each input's species, cell and positions equal
 # the frame scripts/33 will pair it with (1e-6 A), tot_charge is 0 (item 1') or 1 (chk_), prefix = label,
 # calculation 'scf', and positions carry no if_pos columns.
-import glob, importlib.util, json, os, re, sys
+# WP3: the job dirs under <jobs>/wp3 are exactly the ok records of <frames>/frames_report.json; each frame and input
+# is non-empty and the input equals its frame (1e-6 A); an input not yet run (no .out, .out.try* or .gaveup, and
+# pseudo_dir still as scripts/30 wrote it: run_qe.sh rewrites it in place) has the input_sha256 of its fsynced
+# <label>.meta.json. scripts/35 writes the frame and input without fsync, so a hard stop can leave either empty under
+# an ok record; this catches it before its DFT, instead of it becoming a 1d 'gave up' drop.
+import glob, hashlib, importlib.util, json, os, re, sys
 import numpy as np
 s = importlib.util.spec_from_file_location("a33", "scripts/33_finetune_dataset.py")
 a33 = importlib.util.module_from_spec(s); s.loader.exec_module(a33)
@@ -40,6 +46,26 @@
     bad.append(f"item-1' labels: missing {sorted(set(a33.ITEM1P_LABELS) - got['wp3x'])}, extra {sorted(got['wp3x'] - set(a33.ITEM1P_LABELS))}")
 if got["wp3chk"] != want_chk:
     bad.append(f"chk_ labels: missing {sorted(want_chk - got['wp3chk'])}, extra {sorted(got['wp3chk'] - want_chk)}")
-print(f"{len(got['wp3x'])} item-1' and {len(got['wp3chk'])} chk_ inputs; m05 (b) frames {md}")
+okl = {l for l, v in rec.items() if v is True}
+wd = os.path.join(JOBS, "wp3")
+dirs = {x for x in os.listdir(wd) if os.path.isdir(os.path.join(wd, x))} if os.path.isdir(wd) else set()
+if dirs != okl:
+    bad.append(f"WP3 job dirs: missing {sorted(okl - dirs)}, without an ok record {sorted(dirs - okl)}")
+size = lambda f: os.path.getsize(f) if os.path.exists(f) else "missing"
+for lab in sorted(okl & dirs):
+    b = os.path.join(wd, lab, lab); p = b + ".in"; fx = os.path.join(FR, f"{lab}.extxyz")
+    try:
+        if not (os.path.getsize(fx) > 0 and os.path.getsize(p) > 0):
+            raise ValueError("empty file")
+        at = a33.frame_of("wp3", a33.kind_of(lab)[1], [FR]); sym, cell, pos = a33.input_geometry(p)
+        if sym != at.get_chemical_symbols() or np.abs(cell - at.cell[:]).max() >= 1e-6 or np.abs(pos - at.positions).max() >= 1e-6:
+            bad.append(f"{lab}: WP3 input differs from its frame")
+        ran = os.path.exists(b + ".out") or glob.glob(b + ".out.try*") or os.path.exists(b + ".gaveup")
+        if not ran and re.search(r"pseudo_dir\s*=\s*'/data/pseudo'\s*$", open(p).read(), re.M):   # as scripts/30 wrote it
+            if hashlib.sha256(open(p, "rb").read()).hexdigest() != json.load(open(b + ".meta.json"))["input_sha256"]:
+                bad.append(f"{lab}: WP3 input (not yet run) differs from the input_sha256 of its meta.json")
+    except Exception as e:
+        bad.append(f"{lab}: WP3 frame or input unreadable ({type(e).__name__}: {e}; frame {size(fx)} B, input {size(p)} B)")
+print(f"{len(got['wp3x'])} item-1', {len(got['wp3chk'])} chk_ and {len(okl & dirs)} WP3 inputs; m05 (b) frames {md}")
 print("\n".join(bad) if bad else "ALL INPUT CHECKS PASS")
 sys.exit(1 if bad else 0)
```

# WP3 step-7 tools: design review and test record (2026-10-29)

This is the record for `scripts/wp3_runbook/node_step7.sh`, `rb_model_note.py` and the updated `node_relaunch.sh`,
and for the appendix "The 5a retry and steps 5b–7 with the node drivers" of
`results/objective2/dopant_shell/WP3_RUNBOOK.md` (the former `RUNBOOK_SNIPPET.md`, merged there; the older sections
below call it "the snippet"). Four rounds were run, newest first in this file:
- **R4, the merge review** of the merged appendix, the three tools and this file (this section).
- **R3, the operator's round.**
- **R2F and R2**, the second adversarial round. It covers system-level shutdown evidence, `sudo -n journalctl`, the
  step-6-before-step-7 gate, the archive copies, the retry after a deterministic abnormal end and the install check.
- **Round 1**, the implementation and its first adversarial review.

The test harness is temporary. It was a scratch directory on the laptop, written `<harness>/` below (round 1 in
`<harness>/fix/`, rounds 2 to 4 in `<harness>/r2/fix/`). The laptop clears it, and it is not archived. It is not in
the repository either, because its fixtures include the node's real journal tails, which hold host names and client
addresses. So the logs and outputs this file cites (`selftest.log`, `t_cls.out`, `e2e/scen/<S>.out`,
`final_batch_inputs.sha256`, `r2_reviewed/`, `diffs/` and the rest) cannot be checked later: this file is the
lasting record. A batch also overwrote the outputs of the scenarios it re-ran. R3 overwrote the R2F outputs of H0,
K1, A1, C2 and B2 (their outcome lines match the round-2 copies in `scen/r2_batch/`), and R4 overwrote P, H0, K1,
A1, C2 and B2 again. All tests are synthetic: no MACE evaluation, relaxation, MD, training or QE was run for them.

## R4. Merge review (2026-10-29)

The merge review read the appendix as merged into WP3_RUNBOOK.md, the three tools and this file, against the code,
`node_step34.sh` and PLAN.md amendment m, with three lenses: the runbook's coherence, the code against its
documentation, and the public repository. Of its 45 findings, 6 were rejected by the verifiers and 39 survived. All
39 were applied. Where a proposed fix did not match the code it was corrected, and those corrections are named
below. The operator decided F1 and F3 (coherence), F1, F2, F3, F4 and F9 (code-doc), F5 with F12, F9 (coherence),
F18, H-3 and H-4 to H-7 before the fixes were made (the decisions are recorded in the fix workflow's instructions). The
R4 test records are in `<harness>/r5/`, not in `<harness>/r2/fix/`.

Not touched: git (no add, commit, stash, checkout, reset or push), `.audit/**`, scripts 39, 40 and 41,
`node_step2.sh` and `node_step34.sh` (committed and installed), and the node (no ssh). Only the five files of this
record were edited in the working tree. The harness was changed only by installing the three tools in it.

### R4.1 Per-finding outcome

| id | lens | sev | outcome | what changed | tested by |
|---|---|---|---|---|---|
| F1 | coherence | major | fixed | Step 7: 7a–7d now describe what node_step7 runs, and their code blocks are introduced as the record of its exact invocations (one `--cells <host>_<system>` relax per cell, the unconstrained six first; the MD runs in the same 64-thread pool; `flock` on the wp3b queue lock, then `chain.sh wp3b`, once every relaxation has its record or no attempt left). Reruns go only through `step7/cause.<label>.att<n>`. The never-by-hand list is scripts/40 region, zeroshot and relax, scripts/41 run and chain.sh wp3b. 7c no longer says "wait until all 12 records exist". | text, against `build_cmd`, `spawn`, `RELAX_JOBS` and the 7c block of node_step7.sh |
| F3 | coherence | major | fixed | §A.5: the bold rule holds only once the retry is decided (from `STOP: technical failure`, or from the second-abnormal-end STOP once two reviewers judge the causes the same) until STEP34_DONE. After any other node_step34 STOP the operator starts node_step34 directly, with the exact `setsid nohup` command, with and without `PREV_CAUSE`. | text, against node_step34.sh (`stop`, the PREV_CAUSE branch, the STOP texts) and node_relaunch.sh |
| F5 | coherence | major | fixed | Step 3 is headed as run by node_step34 in the node checkout. A new block copies `frames`, `raw`, `test_extra`, `chk` and `dataset` from the node checkout byte for byte (`rsync -a`), checks the copy (`rsync -anci`, must print nothing; the uncompressed-file `find`) and stages it for a commit before 5b. 3a–3c are marked by hand only and kept as the record of what node_step34 ran (it ran rb_archive.sh on `/data/jobs/<campaign>`, copied `/data/work/wp3/frames`, and ran rb_test_hosts.py and the 3c command). The reviewer's "the commands of 3a–3c are what node_step34 ran" was corrected: the pull and rsync lines of 3a are not. | text, against node_step34.sh lines 65–108 |
| F7 | coherence | major | fixed | §A.5: the two-reviewer check of the hand-made lines comes before `touch STEP34_DONE`, so before the note (and before the WP3 result if the retry fails). | text |
| F8 | coherence | major | fixed | "Driver killed while training runs" now covers node_step34's STOPs that ask for 5a by hand (`has wp3.model`, `CHECK ERROR`) and gives 4d–5a by hand in node_step34's log format: the 4d line, the `4: training finished` line with the restart count, 5a with the exact rb_techfail.py command, the `5a:` line, KEEP_ALIVE and `sync; touch STEP34_DONE`. It also gives the start-check-FAIL and no-model branches (a direct start of node_step34, with `PREV_CAUSE` for the latter). | text, against node_step34.sh lines 149–203 and the parsers of both tools |
| F9 | coherence | minor | fixed | §A.4.3 fetches `<C6>` as the operator does: `git bundle create <MAC_STAGE>/ps_wp3.bundle feat/dopant-shell-dft-validation`, copied as `.new` and `mv`ed over `/data/work/ps_wp3.bundle`, then `bundle verify` and `fetch origin` on the node; the checkout update is `git merge --ff-only <C6>`. The reviewer's incremental bundle and `checkout --detach` were not used: the node checkout is on the branch, and its `origin` is that bundle file. 2.0 item 3 names the node checkout and its `origin`. | text (node facts from the operator; not checkable from the laptop) |
| F10 | coherence | minor | fixed | The appendix is titled "the 5a retry and steps 5b–7 with the node drivers"; the mapping sentence names "WP3_RUNBOOK appendix A.4", "A.5" and "B"; the §A heading names A.4.3–A.4.4 and A.5; the helper-scripts appendix names the appendix explicitly. | text |
| F11 | coherence | minor | fixed | Placeholders: rows for `<YYYY-MM-DD>` and the `run<n>` letters; the node drivers' values of `<NODE_WORK>` and `<NODE_REPO>`; `<run>` is literal. §A.5 says which run each letter names; `techfail_run<k>.txt` throughout. | text |
| F13 | coherence | minor | fixed | §A.4.2: `git log --full-history`, and "any commit other than `<CNOTE>` or a later commit of the kind just described". | text, against pre() |
| F14 | coherence | minor | fixed | KEEP_ALIVE is described the same way in 2.0 item 4, the Keep-alive bullet, §A.4.1 (the wait for 5b and step 6 starts at STEP34_DONE), §A.5 sub-step 7 and §B; both ways of stopping the node are named. | text, against node_step34.sh line 202 |
| F15 | coherence | minor | fixed | §A.4: at the first start the driver adopts nothing; later a relaxation or MD output made outside it STOPs, and is adopted only on `accept`. The reviewer's "after the driver has checked that it was made by the identical command" was corrected: the driver checks the record and the commit; the operator vouches for the command. | text, against `complete_check` in cls.py |
| F23 | coherence | info | fixed | "Do not": the note commit alone, no step 6 before §A.3; no node_step34 start in the decided retry, STEP34_STOPPED never removed by hand; the step-7 commands never by hand. | text |
| F24 | coherence | info | fixed | 7c: an unconverged `wp3b_` SCF is a Fail of (d), an unconverged `wp3bu_` job is reported; neither is re-run. | text, against PLAN item 4 |
| F1 | code-doc | major | fixed | as F3 (coherence). | as F3 |
| F2 | code-doc | major | fixed | Both tools read a 5a file the same way (`techfail_verdict` in rb_model_note.py, `tf_verdict` in node_step7.sh, POSIX awk): exactly one `<N> m21 frames evaluated with <run>/wp3.model` line, then on the next line the pass line (pass, if no `non-finite` line is in the file) or a `non-finite` line (fail, if no pass line is in the file); anything else gives no verdict. Library warnings before or after rb_techfail's lines no longer change the verdict. node_step7's retry check (it grepped anywhere) and main check (`tail -1`) both use it. The note's 5a section shows rb_techfail's own lines. node_step34's own 5a check is reported, not changed (R4.4). | self-test `techfail-warnings`, `retry-techfail-warnings`, `retry-techfail-record-without-failure`, `techfail-no-verdict-draft`; `tf_verdict` on 11 files; P `techfail`, `retry_no_tf` and the PASS cases |
| F3 | code-doc | minor | fixed | node_step7's STOP for a committed incomplete note, and §A.3: a committed note is never changed; write a new note under a new date in a commit of its own, write that commit to NOTE_COMMITTED, and list the committed DRAFT as a deviation. | P `draft`, `draft_edited`, `check_line` (new text) |
| F4 | code-doc | minor | fixed | rb_model_note.py's own errors (no `--run`/`--out`, a wrong `--out` name, an existing `--out` without `--force`) exit 1 with `REFUSED: ...; nothing written`; argparse usage errors stay exit 2. §A.2 documents every exit code, the stdout lines and `--force`; the docstring too. | self-test `out-exists`, `out-exists-force`, `out-name-wrong`, `run-missing` |
| F5 | code-doc | minor | fixed | §A.5.6: `restarts:` is a count, with the command. | text, against node_step34.sh line 195 |
| F6 | code-doc | minor | fixed | §A.5.7: the full command (`cd /data/work/ps_wp3`, `<PY>`, the script path, `2>&1` as node_step34 writes it) and how to read the verdict, a checker error included. | text |
| F7 | code-doc | minor | fixed | §A.4.2: two grep lines, the second for PLAN.md, model notes, `results/fa_host`, `wp2b` and `wp2e`; `--full-history`. | the grep pattern on 9 sample paths |
| F8 | code-doc | minor | fixed | §B "After a reclaim": without STEP34_DONE it acts as for steps 2–4. | text, against node_relaunch.sh |
| F9 | code-doc | minor | fixed | The 7c WARN is neutral ("the evidence does not show a hard stop (<evidence>)"); §B lists all five cases boot_cause returns (a clean shutdown with or without a notice, a notice over 1 h old, and without a notice no heartbeat or a heartbeat over 5 min before the journal's end); the driver's comments say the same. | text, against boot_cause in cls.py |
| F10 | code-doc | minor | fixed | During the retry `wp3_relaunch.sh` only refuses; after a reclaim the operator does the §A.5 interruption steps. §A.5 sub-step 0 installs the committed node_relaunch.sh. | text |
| F11 | code-doc | minor | fixed | The test record now says what the self-test covers and names refusals it does not; 9 cases were added (48). | self-test |
| F12 | code-doc | minor | fixed | with F5 (coherence). | as F5 |
| F14 | code-doc | info | fixed | "in succession" dropped from the STOP description. | text |
| F15 | code-doc | info | fixed (wording) | Only `cause.<label>` or `cause.<label>.att<n>` of the 24 labels are read; other names are never read. | text, against tidy() |
| F16 | code-doc | info | fixed (wording) | "one value each" of the three machine-readable lines; exactly one `note_status: complete`. | text, against pre() |
| F17 | code-doc | info | fixed (wording) | The wp2e gate opens once the file exists and passes its check; it STOPs if the file has gone after `wp2e.ok`. | text, against gate_check and verify_wp2e |
| F18 | code-doc | info | fixed | `neb\.x\|pp\.x` added to node_relaunch.sh's busy pattern; its comment and §B list the QE processes. | bash -n; P relaunch cases |
| F19 | code-doc | info | fixed (wording) | `<CNOTE>`'s parent is "normally" `<CN>`. | text |
| H-2 | public | minor | fixed | The test paragraph says that the driver under test is the repository file rewritten by sed, and which tests ran on the final tools (the self-test, t_cls and P, H0, K1, A1, C2, B2) and which on the R2F versions (the other 34). | text |
| H-3 | public | minor | fixed | Every "snippet"/"RUNBOOK_SNIPPET" reference in the three tools now reads "WP3_RUNBOOK appendix A.4", "A.5" or "B": 7 in rb_model_note.py (two of them in the note body), 10 in node_step7.sh, 2 in node_relaunch.sh. No logic changed. The appendix's mapping sentence is simplified. | P (the changed messages), self-test |
| H-4 | public | minor | fixed | R3.4 says which sha256 values the R3 batch record holds. | text |
| H-5 | public | info | fixed | R3.4: the commit and file hashes and the pids differ, as they are rebuilt every time. | text |
| H-6 | public | info | fixed | R3.2 says its output was not saved; the R2.3 and R2F.6 sentences are marked superseded. | text |
| H-7 | public | info | fixed | The header says the harness is temporary and not archived, and which outputs later batches overwrote. | text |
| H-8 | public | info | applied (optional wording) | "ericdft may run `sudo -n journalctl`" in node_step7.sh (a comment and the journal-check STOP text), §B and R3.2, R2.4. | t_cls (152) |
| H-9 | public | info | fixed | "about 1.2 s, extrapolated from the measured 1.0 s at 8 threads". | text |

Beyond the findings, the laptop paths in this file are written `<harness>/`, and the runbook's 2026-10-28 test
section no longer names its laptop scratch path.

### R4.2 Code changes

- **rb_model_note.py.** `techfail_verdict()` (F2), used by `retry_of()` and `node_files()`; the 5a section of the
  note shows rb_techfail's own lines. `main()`: the tool's own errors exit 1 (F4); `--force` help. The docstring's
  input and exit-code text. "WP3_RUNBOOK appendix A.5" in 7 places (H-3). Self-test: 9 new cases, and the case
  count is counted, not written in.
- **node_step7.sh.** `tf_verdict()` before pre(), used for `logs/techfail.txt` (pass) and `techfail_<run>.txt`
  (fail) (F2). The STOP for a committed incomplete note (F3). The 7c WARN and its comments (F9). The sudo wording
  in a comment and in the journal-check STOP of cls.py (H-8). "WP3_RUNBOOK appendix A.4", "A.5" and "B" in 10
  places (H-3). Nothing else in cls.py, verify.py or poller.py changed.
- **node_relaunch.sh.** `neb\.x|pp\.x` in the busy pattern and the header comment (F18); "WP3_RUNBOOK appendix A.5"
  twice (H-3).

### R4.3 Tests (laptop, bash 3.2, synthetic; no MACE, MD, training or QE)

All on the final three tools, installed in the harness (`<harness>/r2/fix/`), byte-identical to the working-tree
files. Their sha256 (R4.5) was recorded at the start and at the end of the e2e batch and was the same; the R3 copies
are kept in `<harness>/r5/harness_before/` (the sha256 of R3.4).

- **`bash -n`:** both shell files pass.
- **`rb_model_note.py --self-test`:** SELF-TEST PASS, 48 cases: the 39 of R3 and 9 new ones, `techfail-warnings`,
  `retry-techfail-warnings`, `retry-techfail-record-without-failure`, `techfail-no-verdict-draft`,
  `versions-missing-draft`, `out-exists`, `out-exists-force`, `out-name-wrong` and `run-missing`.
- **The R3 tool on the two warning fixtures** (without `--m21-offset`, so both tools write a DRAFT for the offset):
  on `techfail-warnings` the R3 tool also lists "no passed technical-failure check" and shows the 5a file as a
  warning line plus "(NOT a pass)"; on `retry-techfail-warnings` it refuses the retry ("does not show the
  failure"). The R4 tool shows rb_techfail's two lines as a pass in both and accepts the retry.
- **`tf_verdict` of node_step7.sh** on 11 synthetic 5a files: a clean pass and a pass with warnings before and after
  give pass; a failure with warnings gives fail; a pass line followed by a `non-finite` line (P's `techfail`
  mutation), a checker error, another run's verdict, the head line alone, two head lines, `wp3.model.bak`, a
  prefixed head line and a missing file give none.
- **`unit/t_cls.sh`:** 152 checks, 0 failures. Against the R3 output only the time stamps in three `.unused` file
  names differ.
- **e2e P, H0, K1, A1, C2 and B2** (`scen/run_all.sh`), 2026-10-29 14:01:51–14:14:42 UTC:
  - **P:** 85 lines, as in R3: 72 cases (63 STOPs with 0 script calls, 60 of them in pre(), and 9 runs to STEP7_DONE
    with 26 calls) and 4 relaunch cases, each with the same outcome, call count and WARN columns as in R3. Compared
    with the R3 `P.out`, the differences other than hashes, pids and times are only message texts: `draft`,
    `draft_edited` and `check_line` show the new STOP for a committed incomplete note (F3); `nonote`, `ahead`,
    `behind`, `dirty`, `untracked`, `c6_dirty`, `dae_no_end`, `relaunch_mismatch` and the relaunch line of the by-hand
    retry say "WP3_RUNBOOK appendix A.4/A.5/B" (H-3); `retry_no_tf` shows the new text of the `techfail_run1.txt` STOP
    (F2). The other differing lines (`c6_short`, `c6_s39`, `c6_eval_not_full`, `drv_mismatch`, `dae_no_cmd`,
    `dae_log_lr`, `dae_2nd_no_statement`) differ only in a short hash or the time stamp of a `STOP pending` line.
  - **H0:** STEP7_DONE, at most 60 threads in use, 3 journal reads through sudo and none unprivileged.
  - **K1:** 18 RERUN and 2 REISSUE (spot-reclaim, then node-loss), at most 64 threads, STEP7_DONE, 45 journal reads
    through sudo and none unprivileged.
  - **A1:** (a) 6 node-loss classifications, STEP7_DONE; (b) the clean-shutdown STOP, 0 reruns.
  - **C2:** (a) 10 spot-reclaim and (b) 6 node-loss classifications, no STOP.
  - **B2:** (1) the journal STOP in pre(), 0 classified, 0 calls; (2) 6 node-loss, STEP7_DONE.

  H0, K1, A1, C2 and B2 give the same lines as in R3 once hashes, pids and times are normalised.
  `unpriv_all.log` is empty, and no harness process was left after the batch.

The other 34 scenarios, `unit/t_archive.sh` and `unit/t_retry_preflight.sh` were not re-run: the §A.4.3 block and
the §A.5 pre-flight block are unchanged.

### R4.4 What the tests cannot show, and an open point

- `tf_verdict` was run with the laptop's BSD awk only. It uses POSIX awk only, for the node's mawk, which was not
  available on the laptop.
- The warning lines of the self-test are synthetic. Their kind and place (stderr warnings before rb_techfail's
  lines, mace's own stdout notice just before them, a warning at exit after them) follow the node environment's
  output as the review found it.
- **node_step34.sh (frozen, not changed).** Its 5a verdict does not depend on warning lines: exit 0 is a pass, and
  a technical failure is a `^non-finite` line anywhere in `logs/techfail.txt`. But on a pass it logs
  `5a: $(tail -1 logs/techfail.txt)`, so a warning printed after rb_techfail's lines would stand in `step34.log`
  instead of `no technical failure (items checked here)`. STEP34_DONE is still written. Neither tool depends on that
  line: node_step7.sh reads only `logs/techfail.txt`, and rb_model_note.py accepts a pass from either that file or
  the `step34.log` line. A CHECK ERROR STOP quotes `tail -3`, which can show warnings instead of the error; the
  verdict is unaffected. If that happens, list it in the WP3 result.

### R4.5 Final sha256

| file | sha256 |
|---|---|
| `scripts/wp3_runbook/node_step7.sh` | `a8fd3f3805e370ffb6cbf23b42f6738bde110073bec2cdec56ebfbf99beeb873` |
| `scripts/wp3_runbook/node_relaunch.sh` | `6d90693a1b6b631857b8acb5d5135ac6e0d08bbb54c13e24519d5cf93bab8ec5` |
| `scripts/wp3_runbook/rb_model_note.py` | `c47b80d5c25aa23ad87525990408374e276d52b0a22497640efeb214c7088f9d` (R4.6; tested as `aecd3364…` in R4.3) |
| `results/objective2/dopant_shell/WP3_RUNBOOK.md` | `e23ad24e91121ef71492cc59b2cc45af9fff5ecf57a3f0ef5d90c343dc7663ef` (R4.6) |
| `scripts/wp3_runbook/review_2026-10-29/NOTES.md` | not given here: a file cannot hold its own sha256 (it is in the fixer's report) |

Before R4 they were `aa3bc5e8…`, `2c0256c5…` and `d9a637d3…` (R3.4), `4c406054…` (the merged runbook) and
`9dbea390…` (this file).

### R4.6 After the independent check

The independent verifier found no blocker or major issue: one minor issue and seven info items. The operator then
made these changes:
- **The A.5 list.** A blank line now comes before sub-step `0.`, so GitHub renders it as a list item (minor).
- **`rb_model_note.py` `techfail_verdict()`** now reads the 5a file without newline translation and splits lines at
  `\n` only. It therefore treats `\r` exactly as node_step7's awk `tf_verdict` does (info). Tested on two synthetic
  files:
  - an LF file with warnings before and after gives `pass` in both tools;
  - a CRLF file gives `none` (no verdict) in both.
- **Runbook text** (info items):
  - A.5: the `has wp3.model` and `CHECK ERROR` STOPs are finished by hand, without a node_step34 start.
  - §B: KEEP_ALIVE is also kept during a by-hand 4d–5a finish.
  - Step 4: a lead sentence says that node_step34 ran 4a–5a, so the blocks are not to be run with the drivers.
  - 2.0 item 3 explains `<repo>` and the bundle origin.
  - A.3 says how to choose `--date` when a DRAFT was committed the same day.
  - The §B access check uses `sudo -n journalctl --list-boots` instead of `sudo -n true`.

Re-run on the final files:
- `rb_model_note.py --self-test`: SELF-TEST PASS (48 cases).
- The e2e scenario H0 gives STEP7_DONE, with at most 60 threads; the note was made by the final tool (exit 0).

node_step7.sh and node_relaunch.sh did not change after R4.3.

## R3. Operator round

### R3.1 Changes after the round-2 final check

1. **PLAN.md between `<CNOTE>` and `<C6>` now STOPs.** It was only a WARN (R2F.5, E2E-5). PLAN.md is the
   pre-registration: nothing in it changes between the committed note and step 7. Any other path under `results/`
   that changes there is still named in a WARN, WP3_RUNBOOK.md included. The P case `c6_edits_PLAN` now expects the
   STOP.
2. **§A.5 step 5 gives the exact command for the by-hand retry training** (round-2 final check, minor). It mirrors
   node_step34: the next free `run<m>`, `<T>` from timing.txt, `setsid nohup` detached from the ssh session, the
   `.start`, `.pid` and `.stdout` files, and the `start; repo` and `4c` lines.
3. **Commit names in three more runbook places** (round-2 final check, info). 7e is at `<C6>` or later, step 8 is
   at `<C6>` or later, and item 6 is on the node at `<C6>`. The step-6 heading is at `<CNOTE>`.

### R3.2 Checked on the node (2026-10-29, read-only or in /tmp)

- **`_PID=1` probe** (round-2 final check, info). `sudo -n journalctl -b <b> -o short-unix _PID=1 -n 3` was run for
  boots −3, −2 and −1. Each time the last `_PID=1` entry is a `systemd[1]:` line:
  - −3 and −2 (idle self-stop) end `Reached target poweroff.target` then `Shutting down.`;
  - −1 (spot reclaim) ends with session-scope lines.

  systemd-shutdown's own lines carry `SYSLOG_PID=1` and are not `_PID=1` entries. The boot probe therefore works
  as designed, and no change was needed.
- **The §A.5 launch block.** The block was run as a file with `bash`, with a stand-in trainer (a shell script that
  prints its arguments and sleeps) and the work dir /tmp/rbtest. It gave:
  - `$!` was the trainer's own pid, in its own session (`pid = pgid = sid`), so a non-interactive bash makes
    `setsid` exec without forking;
  - the trainer was still alive in a second ssh session after the first had logged out;
  - `--work_dir <run>` became `/tmp/rbtest/run1`;
  - `OMP_NUM_THREADS` was the timing winner, with a tie going to fewer threads (16 for 16/32 at equal time);
  - the `start; repo` and `4c` lines matched node_step34's format.

  /tmp/rbtest was removed afterwards.
- **Journal access.** ericdft may run `sudo -n journalctl`, which works without a tty, and is not in `adm` or
  `systemd-journal`. Unprivileged `journalctl -k -b` is empty. Nothing on the node was changed.

These checks were made in an ssh session on the node. Their output was not saved, so this section is their only
record (R4, H-6).

### R3.3 The decisions of R2F.5, R2.4 and round 1 §3

All are accepted as designed, except R2F.5's E2E-5 (R3.1, item 1). In particular:
- **The journal thresholds.** A journal that ends more than 1800 s before the last heartbeat, or before the launch,
  STOPs; so does an exit 137 less than 300 s old with no OOM line yet, judged with a 60 s OOM margin. Each of these
  STOPs is not kept, so a relaunch classifies the attempt again.
- **`--list-boots` must show at least 2 boots.**
- **A clean shutdown that cuts the QE chain is listed as "undetermined" with a WARN** (E2E-6). On this node a clean
  stop comes only from the idle self-stop or the console. The first cannot fire while pw.x runs; the second is an
  operator's act and is recorded.
- **The operator word `accept` is kept.** It is still checked against `<C6>` and listed.
- **The by-hand retry is checked by two people** before step 7: every hand-made line of §A.5.
- **The node-side archive copies are kept in `/data/work/wp3/archive_node_copy/`** until the WP3 result is written.
- **The m21 host-wide energy offset is the mean of E_model − REF_energy over the 31 m21 frames.** This is the note
  tool's reading of amendment m item 2 'Reporting', and the WP3 result states it.

### R3.4 Tests on the final files

The tests ran on the laptop under bash 3.2, 2026-10-29 12:55–13:15 UTC, with the round-2 harness. The batch record
holds all three sha256 values at the start and node_step7.sh's at the end. node_relaunch.sh and rb_model_note.py
were unchanged since R2F (their harness copies date from 11:01 and 11:03 UTC, before the batch); the merge review
re-checked their sha256 after the batch and found them unchanged (R4, H-4):

| file | sha256 |
|---|---|
| `node_step7.sh` | `aa3bc5e8047e62e34e65809fbb55938a4a06667121e812401f501b725559c359` |
| `node_relaunch.sh` | `2c0256c5beb9c9ca369085b0d080551c5489f6508682d0a392d716c990883b60` (unchanged since R2F) |
| `rb_model_note.py` | `d9a637d3a616261427164c8f6a07919e63488528a0df405af2282d20eab3dbe8` (unchanged since R2F) |

Results:
- **`rb_model_note.py --self-test`:** SELF-TEST PASS, 39 cases.
- **`unit/t_cls.sh`:** 152 checks, 0 failures.
- **The P battery:** 85 output lines, the same as the R2F batch except for two things:
  - the commit and file hashes (the synthetic wp3.model and note sha256, the installed driver's sha256) and the pids,
    which are rebuilt every time (R4, H-5);
  - `c6_edits_PLAN`, which now STOPs in pre() with 0 script calls (R3.1, item 1).
- **Other scenarios** (H0, K1, A1, C2, B2), all as in R2F:
  - **H0:** STEP7_DONE, with at most 60 threads in use.
  - **K1:** spot-reclaim and node-loss reruns, at most 64 threads, 45 journal reads through sudo and none
    unprivileged.
  - **A1:** the real idle-stop tail of boot −3 gives a clean-shutdown STOP.
  - **C2:** user-manager logout lines in the tail give spot-reclaim and node-loss reruns, not a STOP.
  - **B2:** an unreadable journal gives a STOP that is not kept. Once the journal is readable the run reaches
    node-loss and then STEP7_DONE.

The repository version of the appendix was made from `RUNBOOK_SNIPPET.md` (sha256 `cef8b358…`).

---

# R2F. Round 2 after its adversarial review (2026-10-29)

This file is the fixer's record for the round-2 review. The surviving findings were applied to the round-2 files in
`<harness>/r2/fix/`. The round-2 implementer's notes follow, unchanged, after section R2F.6. The
files exactly as reviewed are kept in `r2_reviewed/`.

What was not touched:
- the repository (`.../dopwork/ps`, branch feat/dopant-shell-dft-validation, HEAD c391d61): nothing was edited,
  committed or checked out. `scripts/wp3_runbook/rb_preflight.py` was copied into a test directory and run there
  (`unit/t_retry_preflight.sh`);
- the node: there was no ssh;
- `.audit/**`: nothing was read or written;
- the frozen scripts 39, 40 and 41: unchanged;
- writes outside `r2/fix/`: the note tool's self-test made temporary directories under `$TMPDIR`, each deleted after
  its run. A draft of this section was written in the session scratchpad by mistake and deleted. The e2e note
  generation re-creates `r2/fix/__pycache__`; it was deleted at the end.

## R2F.1 Files and final sha256

| file | sha256 (final, after the review fixes) | sha256 as reviewed (`r2_reviewed/`) |
|---|---|---|
| `node_step7.sh` | `372a319e47a6a42b4b5f66bfe884afb7b40a627b66c93b2c4c2c40e532a996c9` | `d56e716757b90d35f06a34d0ed48aae9db27976cfc0d4f7979e780a967214b8d` |
| `node_relaunch.sh` | `2c0256c5beb9c9ca369085b0d080551c5489f6508682d0a392d716c990883b60` | `2a230a7d34b8acb4e1230d193110bf920e29a7ca8bd256a8ea677c8e2144e779` |
| `rb_model_note.py` | `d9a637d3a616261427164c8f6a07919e63488528a0df405af2282d20eab3dbe8` | `103bd9730421c1ccbecc1652f09b157d7cbc421bb07d3b1f883c88a0395bbb22` |
| `RUNBOOK_SNIPPET.md` | `227bf5b761c897b607c70c54e652dc744fe690112c8780daa03c1a274df47dc2` | `ebb545a15eb47136db14cd06625bb37f424f7f7dfe6d6fecf49a5d4f1485c292` |

- `diffs/r2review_*.diff` hold `diff -u r2_reviewed/<file> <file>` for the four files and for the changed harness
  and unit files. The older `diffs/*.diff` (round 1 to round 2) are unchanged.
- The final e2e batch ran on exactly the first three sha256 values. They were recorded at the start and at the end of
  the batch, in `e2e/final_batch_inputs.sha256`. The unit layers and the self-test ran on the same files.
- `bash -n` passes for both drivers. Python `ast` passes for `rb_model_note.py` and for the three helpers embedded in
  node_step7.sh. The pre() retry check is an inline `$SPY -c` program; it ran in every retry case (P, RVE).

## R2F.2 Per-finding outcome

| id | sev | outcome | what changed | tested by |
|---|---|---|---|---|
| C-1 | minor | fixed (snippet) | The insertion list now also changes three runbook lines: the step-6 heading ends "at `<CNOTE>`", with `git rev-parse HEAD # = <CNOTE>` as the first command; "Steps 7a–7d … at `<C6>`"; and "After a reclaim" excludes node_step34 during the by-hand retry. The §A heading is split per step (5b at `<CN>`, step 6 at `<CNOTE>`, node at `<C6>`). A.4.2 says HEAD must be `<CNOTE>` and that a scripts/39 run at `<CN>` can never be used for step 7. | P `c6_eval_before_note` (git.head = `<CN>`: STOP, 0 calls), the driver behaviour the text now warns of |
| C-2 | minor | fixed | pre(): `git log --full-history --format=%H <CNOTE>..<C6> -- wp3_eval.json` must print exactly `<C6>`, so add, delete and re-add STOPs. `git diff --no-renames --name-only <CNOTE> <git.head>` may list only `results/` and scripts/39, so scripts/32 and 37 at the commit scripts/39 ran at are the note commit's. The snippet gives both checks to the operator. | P `c6_eval_twice`, `c6_head_s37_reverted` (37 changed at git.head, reverted in `<C6>`), `c6_head_s32_reverted` (reverted in its own commit): STOP, 0 calls; `c6_s39` still passes with its WARN |
| E-1 / E2E-1 | minor | fixed | Both tools take the first end of the deterministic pair from node_step34's own STOP line. It must quote a restarts.txt `[abnormal end]` line as `; earlier: <line>). The same cause twice`. Otherwise they refuse. A later abnormal end of the retry is never named. | self-test `dae-retry-with-own-abnormal-restart` (names run1/run2, never run3), `dae-stop-line-quotes-no-restart`; P `dae_ae1_ok`, `dae_rc_ok`, `dae_2nd_ok` (log `earlier: … run1 …`); RVE `dae_ae1` (note text) |
| E-2 | minor | fixed (snippet + node_relaunch.sh) | A.5: never start node_step34 from its STOP until STEP34_DONE, with the reasons; never remove STEP34_STOPPED; after a reclaim only wp3_relaunch.sh. The runbook's direct relaunch is excluded through the insertion list. node_relaunch.sh refuses node_step34 while `train_command_retry.txt` exists without STEP34_DONE (defence in depth, if STEP34_STOPPED was removed). | P relaunch case `P_retry_inprogress_relaunch` (refusal printed, no driver34.out) |
| E-3 | minor | fixed (snippet) | A.5 step 4 is a four-line block: a new empty `preflight_retry`, the `train_command_retry.txt` command with `--work_dir $P --dry_run`, `WE` from `ds/dataset_meta.json`, and `rb_preflight.py … 0.0025`, where every line must PASS. | `unit/t_retry_preflight.sh` (3 OK). The snippet's lines run literally (paths substituted) with a stub `mace_run_train` and the repository's `rb_preflight.py`: 10 PASS; node_step34's own 0.005 dry run FAILs the 0.0025 check |
| E-4 | info | fixed | A.5 has a table of the three verdict formats a retry run may get (`[node loss]`, `[abnormal end] … exit <rc>, <UTC>: <stdout tail>`, `[start check FAIL]`), written to `run<m>.end`, restarts.txt and step34.log. Both tools refuse any other tag on a retry discard. Both check that the selected run's `4c: training started … threads <T>` equals timing.txt's `<T>` (for every run, not only the retry). | self-test `dae-retry-discard-bad-tag`, `dae-retry-threads-not-T`; P `threads_not_T` |
| D-1 | info | fixed (snippet) | A.4.3: the committed archive must be byte copies of the node's files (rsync), not re-made with rb_archive.sh. A new line 5 compares the decompressed content of every differing `.gz`, with guidance (`same content`: note it and go on; `DIFF content` or a non-`.gz` difference: stop). The lines are renumbered. | `unit/t_archive.sh` D-3 (re-gzipped with other mtimes: 4 byte-DIFF, 4 `same content`), D-4 (`DIFF content`); `unit/d_procedure.txt` is the snippet block byte for byte |
| C-3 | info | fixed (snippet) | `git diff --no-renames --name-only <CNOTE> <C6>`. | text |
| F-1 | info | fixed | (a) The installed `/data/work/wp3_relaunch.sh` sha256 is logged beside `git show HEAD:…/node_relaunch.sh`, with a WARN if they differ or the file is missing. It is not a STOP: the script runs no step-7 work. (b) Every FROZEN path must exist at `<CNOTE>`, and every STEP7_CODE/STEP7_DATA path at `<C6>`, before the `git diff --quiet` identity checks. | P `relaunch_mismatch` (WARN, STEP7_DONE), `frozen_path_absent`, `step7_path_absent` (DRV_SED adds a missing path: STOP, 0 calls) |
| EV-1 | minor | fixed | cls.py reads the end of a boot only from time-stamped entries (`^\d{9,}\.\d{6}\s`; indented continuation lines are skipped). It is a STOP, not kept, if no line is time-stamped, or if the journal ends more than 1800 s before the attempt's launch epoch (also for the chain, `--since`). | unit EV-1a (word continuation: node-loss, true end), EV-1b (`    17 0.5 done`: true end, not 1970), EV-1c (the same, stale poller: STOP), EV-1d (`-- No entries --`), EV-1e (journal ends before the launch) |
| EV-2 | minor | fixed | A heartbeat more than 1800 s after the journal's end is a STOP, not kept ("does not cover the end of that boot"). The snippet's node-loss row states both bounds (5 min before, 30 min after) and why. | unit EV-2 (real boot −1 tail 3 h before the heartbeat: STOP), EV-2b (20 min after: node-loss) |
| EV-3 | minor | fixed | `--bootcause` emits `CL_TRANSIENT`. A chain cut whose boot journal cannot be read now STOPs before anything is listed or `.listed` is touched, so the next start classifies it. If the journal is gone for good, the operator writes `step7/cause.chain.C<n>`: it is listed as the operator's cause and renamed `.used` after the list line and marker. (E2E-3, rejected, describes the same defect.) | unit B-7 (`CL_TRANSIENT=1`), B-7b (clean shutdown: `CL_TRANSIENT=0`); RVB2 (STOP, nothing listed, no chain; journal back: node-loss listed, STEP7_DONE); RVB4 (operator file) |
| EV-4 | info | fixed | The kernel journal is read with `-o short-unix`. Only a hit time-stamped at or after the launch epoch less 60 s counts. | unit EV-4 O1–O7 (the reviewer's lines): O6 (an earlier kill of the same pid) is no longer oom |
| EV-5 | info | fixed | (a) journalctl stderr on a successful read goes into the evidence. (b) boot_cause also needs a `-b <boot> _PID=1 -n 1` entry; otherwise a STOP, not kept. (c) pre()'s journal check also needs `--list-boots` to list at least 2 boots (a persistent journal). (d) The snippet's by-hand check covers all three parts. | unit EV-5a, EV-5b, B-8e/f; P `j_one_boot` (STOP, 0 calls) |
| EV-6 | info | fixed | CLEAN (and the systemd[1] test of the journal check) is anchored to the identifier field of the short-unix layout (`^<ts> <host> <ident>`). The round-2 NOTES wording ("anchored at the start of the ident field") was not true of the reviewed regex; it is now. | unit A-0 (sudo's `COMMAND=… systemd[1]: Reached target poweroff.target` and an indented continuation: no match now, matched by the reviewed regex), EV-6 (node-loss) |
| EV-7 | info | fixed | An exit 137 younger than 300 s with a readable kernel journal and no OOM line is a STOP that is not kept, so it is read again at the next start. Every SIGKILL-without-OOM STOP names systemd-oomd/earlyoom. Snippet: both. | unit EV-7 (fresh: not kept; the line then appears: oom), B-5c (15 min old: kept) |
| E2E-2 | minor | fixed | Both tools look at the retry's own discards (between the retry's STOP line and the selected run's start). Each `[abnormal end]` after the first, with a `[node loss]` between them or not, as node_step34 counts them, needs the operator's line `run<a> run<b>: <why the causes differ>` in `retry_causes_differ.txt`. Without it: refused, "the same cause twice is a technical failure of the retry … no second retry". A line naming no such pair is refused too. The note quotes the statements. | self-test `dae-retry-two-abnormal-ends`, `…-causes-differ` (exit 0, quoted), `dae-causes-differ-file-without-pair`, `retry-two-abnormal-ends`(`-causes-differ`); P `dae_2nd_no_statement` (STOP), `dae_2nd_ok` (PASS); RVE `dae_2nd` (the note tool refuses at init: no note commit) |
| E2E-4 | info | fixed (harness) | The review's stubs are adopted: `bin/sudo` exports SUDO_USER and has `ctl/sudo_fail_after N`; `bin/journalctl` gives the system view only through sudo and logs every other call as UNPRIV (also to `unpriv_all.log`, kept across the batch). Added `--list-boots`. | the whole batch: UNPRIV total 0; RVA, RVB |
| E2E-5 | info | partly applied | pre() logs a WARN naming every path changed between `<CNOTE>` and `<C6>` other than `wp3_eval.json`, for the WP3 result. Whether a change to PLAN.md or WP3_RUNBOOK.md should be a STOP is left to the user (R2F.5). | P `c6_edits_PLAN`, RVC `c6_edits_PLAN` (WARN names PLAN.md, STEP7_DONE) |
| E2E-6 | info | applied as a WARN | A chain cut by a clean shutdown is still listed 'cause undetermined' (round-1 behaviour). There is now a WARN in step7.log, and the snippet says so. A STOP was not added: there is no operator word for the chain that it could ask for, and item 1d's one resubmission is the queue's (R2F.5). | RVB3 (the real boot −3 tail: listed, WARN, STEP7_DONE) |

## R2F.3 Tests (laptop, synthetic; no MACE evaluation, relaxation, MD, training or QE)

### Unit layers

- `rb_model_note.py --self-test`: **39 cases, all pass** (`unit/selftest.log`). These are the 30 of round 2 plus 9
  new ones: `dae-retry-with-own-abnormal-restart`, `dae-retry-two-abnormal-ends`, `…-causes-differ`,
  `dae-causes-differ-file-without-pair`, `dae-stop-line-quotes-no-restart`, `dae-retry-discard-bad-tag`,
  `dae-retry-threads-not-T`, `retry-two-abnormal-ends`, `retry-two-abnormal-ends-causes-differ`.
- `unit/t_cls.sh`: **152 checks, 0 failures** (`unit/t_cls.out`). These are the 106 of round 2, adapted, plus 46
  new ones:
  - A-0 on the short-unix layout, with the sudo-quote and continuation lines;
  - B-5c with an old exit status;
  - B-7 and B-7b (`CL_TRANSIENT`);
  - B-8e and B-8f (list of boots);
  - EV-1a–e, EV-2/2b, EV-4 O1–O7, EV-5a/b, EV-6, EV-7/7b.

  `DRV=../r2_reviewed/node_step7.sh bash unit/t_cls.sh` runs the same checks on the classifier as reviewed: **33
  failures** (`unit/t_cls.reviewed.out`), exactly the new checks of EV-1…7, EV-3 and the A-0 anchor cases. The
  adapted round-2 checks were changed only where the fixture had to carry what the fix now requires:
  - six-decimal time stamps;
  - a systemd[1] entry in the cut boot;
  - an older boot for `--list-boots`;
  - an old exit status where the STOP must be kept.
- `unit/t_archive.sh` (D, D-1): **6 checks, 0 failures**, D-3 and D-4 among them.
- `unit/t_retry_preflight.sh` (E-3): **3 checks, 0 failures**.

### End-to-end scenarios (`e2e/scen/<S>.sh`, output `<S>.out`)

The batch ran from 11:18:07 to 12:03:23 UTC: 40 scenarios on the three sha256 values of R2F.1, recorded at both
ends in `e2e/final_batch_inputs.sha256`. Across the whole batch, `unpriv_all.log` recorded **0** journalctl calls
made without sudo, and no harness process was left at the end. RVB was run again at 12:04 after a change to its
own output lines only (the second start's STOP and a list count), on the same three files
(`scen/RVB.rerun.sha256`); its batch output is `RVB.batch.out`. The round-2 batch outputs are kept in
`scen/r2_batch/`. All 33 regression scenarios were compared with them line by line, with times, pids and hashes
normalised. Every difference is one of three things:
- the new log lines (journal boots, relaunch hash);
- the EV-7 wording ("… 2 s ago, and so far no kernel OOM-kill line …: not kept"), in X3 and Z1;
- which job a timed SIGKILL happened to cut (K2, K4, T3). The outcomes are unchanged.

| scenario | finding(s) | fault injected | expected | observed | verdict |
|---|---|---|---|---|---|
| P (72 cases + 4 relaunch cases) | all of C, E, F; regression | one precondition mutation per case | a STOP in pre() with 0 script calls, except the 10 PASS cases (P.sh header) | 62 STOP with 0 calls; 10 PASS to STEP7_DONE with 26 calls. New STOPs: `c6_eval_twice`, `c6_head_s37_reverted`, `c6_head_s32_reverted`, `threads_not_T`, `dae_2nd_no_statement`, `j_one_boot`, `frozen_path_absent`, `step7_path_absent`. New PASS cases: `retry_rc_ok`, `dae_rc_ok`, `dae_ae1_ok` and `dae_2nd_ok` (each logs `earlier: … run1 …`), `c6_edits_PLAN` (WARN names PLAN.md), `relaunch_mismatch` (WARN). The relaunch case during the by-hand retry prints the refusal and starts nothing | pass |
| RVA | E2E-4, A | RV1: the happy path via node_relaunch.sh with KEEP_ALIVE; RV2a–c: the REAL boot −1 tail plus user-manager logout lines; RV2d: the REAL boot −2 tail | STEP7_DONE; node-loss / spot-reclaim; STOP for the clean shutdown | as expected; 0 UNPRIV in each case | pass |
| RVB | B, EV-3, E2E-6 | RVB1: sudo fails after pre(); RVB2: the chain cut, the old boot's journal gone, then back; RVB3: the chain cut by a REAL clean poweroff; RVB4: the journal gone for good, `cause.chain.C1` | RVB1: STOP not kept, then node-loss. RVB2/RVB4: STOP, nothing listed or launched, then listed (node-loss / operator) and STEP7_DONE. RVB3: listed undetermined + WARN | RVB1 as expected. RVB2: (1) STOP, 0 list lines, no `C1.listed`, no new chain, 0 QE runs; (2) QE-INTERRUPTED node-loss, STEP7_DONE. RVB3: WARN, listed, STEP7_DONE. RVB4: listed with the operator's cause, `cause.chain.C1.used`, STEP7_DONE | pass (the reviewed driver listed RVB2 as 'undetermined' at once) |
| RVC | C, F | the review's 16 C/F cases | STOP, except `c6_edits_PLAN` and `keep_alive` | as expected; `c6_edits_PLAN` now logs the WARN naming PLAN.md | pass |
| RVE | E-1, E2E-1, E2E-2 | `dae_2nd`, `dae_2nd_ok`, `dae_ae1` | `dae_2nd` refused by the note tool; the other two accepted, naming run1 then run2 | `dae_2nd`: rb_model_note exit 1 at init ("ended abnormally twice in succession (run3, then run4)"). `dae_2nd_ok`: STEP7_DONE, and the note quotes the statement. `dae_ae1`: the note and step7.log name run1, then run2; run3 is listed only among the retry's discards | pass (the reviewed tools named run3 / run4) |
| RVF | F | an uncommitted driver installed after a hard stop; a relative `$0` | STOP, then STEP7_DONE; STEP7_DONE | as expected | pass |
| H0, PR, A1, B1, B2, B3, G2, C1, C2, F1, F2, G1, I1, K1, K2, K4, K5, L1, N1, N2, N3, O1, Q1, Q2, R1, S1, T3, V1, W1, X1, X2, X3, X5, Z1 | regression (round 1 and round 2) | as in R2.3 below | as in R2.3 | the same outcomes as the round-2 batch (see the comparison above); X3 and Z1 show the EV-7 STOP, resolved by the same operator words | pass |

## R2F.4 Harness changes (after the review)

| change | why |
|---|---|
| Metadata port 18817 → 18829 (`lib.sh`, `mkdrv.sed`); the process markers stay `q7*` (unique to this harness) | no clash with an earlier run of this harness |
| `bin/sudo` and `bin/journalctl` from the review harness (SUDO_USER, `ctl/sudo_fail_after`, UNPRIV view and log), plus `--list-boots` and an anchored `_PID=1` filter; `unpriv_all.log` kept across the batch; `scenario_name` written by `setup` | E2E-4; EV-5 |
| `init.sh`: an earlier boot's journal file; the review's kinds `retry_rc`, `dae_rc`, `dae_ae1`, `dae_2nd`, plus `dae_2nd_ok` (with `retry_causes_differ.txt`); the round-2 copy is `tools/init.sh.r2` | EV-5 (two boots); E-1, E2E-2 |
| `lib.sh show()`: journal reads through sudo and UNPRIV counts | E2E-4 |
| P.sh: 14 new cases and one relaunch case; the WARN and `earlier:` columns | C-2, E-4, E2E-2, F-1, E2E-5, EV-5, E-2 |
| RVA, RVB, RVC, RVE, RVF adopted from the review harness (paths changed; RVB and RVE rewritten for the fixed behaviour, `diffs/r2review_harness_RV_from_review.diff`) | the reviewers' reproductions as regression tests |
| `scen/batch.sh` | sha256 at both ends, UNPRIV total, survivors |
| unit: `jctl_stub.sh` (`--list-boots`, `J/WARN`, anchored `_PID=1`); `t_cls.sh` (`DRV=` override, the A-0 extraction of HEAD+CLEAN, a crash of A-0 counts as a failure); `t_archive.sh` (renumbered lines, D-3, D-4); `t_retry_preflight.sh` (new) | EV-*, D-1, E-3 |

## R2F.5 Decisions a human must confirm (new in this round)

1. **The retry's own abnormal ends (E2E-2).** Each `[abnormal end]` of the retry after its first needs the
   operator's `run<a> run<b>: <why>` line in `retry_causes_differ.txt`. This applies even with a `[node loss]`
   between them, which is how node_step34 counts. Without it, both tools refuse: criterion 6 is not met. A retry
   discard tagged anything other than `[node loss]`, `[abnormal end]` or `[start check FAIL]` is refused.
2. **Threads (E-4).** The selected run's `4c` line must say timing.txt's `<T>`. This applies to every selected run,
   not only the retry.
3. **Journal thresholds (EV-1, EV-2, EV-5, EV-7).** Each case is a STOP that is not kept:
   - 1800 s: a journal ending this long before the poller's last heartbeat, or before the launch;
   - 300 s: an exit 137 younger than this without an OOM line;
   - 60 s: the margin of the OOM time filter.

   pre() also requires `--list-boots` to list at least 2 boots.
4. **E2E-5.** Changes to PLAN.md or WP3_RUNBOOK.md (or anything else under `results/`) between `<CNOTE>` and
   `<C6>` give a WARN only. Should they STOP?
5. **E2E-6.** A clean shutdown that cuts the QE chain is still listed 'cause undetermined', with a WARN, and the
   cut job uses its item-1d resubmission. Should it STOP for a human?
6. **The chain's operator file (EV-3).** `step7/cause.chain.C<n>` resolves a cut chain whose boot journal is gone
   for good. Its text is listed as given.
7. **A re-gzipped archive (D-1).** When the committed `.gz` files differ from the node's only in their gzip header
   (`same content`), the procedure goes on, with a note in the WP3 result.
8. **C-2.** `git log --full-history` makes any second commit after `<CNOTE>` that touches `wp3_eval.json` a STOP,
   a merge commit included (a linear history is expected). A first evaluation that was never committed cannot be
   detected by git; that stays the reviewers' check.
9. **The relaunch script mismatch (F-1)** is a WARN, not a STOP.
10. **node_relaunch.sh** refuses node_step34 whenever `train_command_retry.txt` exists without STEP34_DONE. If a
    retry is abandoned (criterion 6 not met), that file blocks any relaunch of node_step34. That is intended, but
    it means the file must stay as evidence, not be deleted to "unblock".

## R2F.6 What the tests cannot show

- The node's real `journalctl --list-boots` layout. The parser counts rows `<idx> <32-hex id> …`, as in the
  operator's `list_boots.txt`. A different layout would STOP at pre(), which fails closed.
- How journald behaves under memory pressure (EV-7), and the real loss window of journald's sync on a spot
  reclaim. The 1800 s and 300 s margins come from the node's 10-min cron/sysstat cadence and journald's 5-min sync.
- Real scripts/39/40/41, real QE, real sudo and a real mace_run_train. They were not run, by rule. (Superseded in
  part: `sudo -n journalctl` was later run on the node, read-only; see R3.2.)

---


# Round-2 implementer's notes (change list A–H, 2026-10-29; unchanged, as reviewed)

This is the implementer's output for round 2. The baseline is the round-1 result, `<harness>/fix/`,
which is unchanged. All round-2 work is under `<harness>/r2/fix/`.

What was not touched:
- the repository (`.../dopwork/ps`, branch feat/dopant-shell-dft-validation, HEAD c391d61): nothing was edited,
  committed or checked out;
- the node: there was no ssh, and nothing under `/data` was touched;
- `.audit/**`: nothing was read or written;
- the frozen scripts 39, 40 and 41: unchanged.

Two writes went outside `r2/`, and both were removed:
- **Scratch copies.** Three scratch copies of the embedded helpers (`r2_{cls,verify,poller}.py`, in the laptop's temporary directory)
  were written by mistake during a syntax check. They were deleted at once.
- **A bytecode cache in the baseline.** The reproduction in `unit/dae_repro.out` imported the baseline
  `rb_model_note.py`, so Python wrote `<harness>/fix/__pycache__/rb_model_note.cpython-312.pyc`.
  It was deleted at the end. The four baseline files are byte-identical to round 1 (the round-1 sha256 values in
  R2.1 were re-checked after the deletion).

The round-1 notes follow, unchanged, after the round-2 sections.

## R2.1 Files and final sha256

| file | role | sha256 (round 2, final) | round-1 sha256 (baseline) |
|---|---|---|---|
| `node_step7.sh` | step-7 driver (installed as `/data/work/wp3_step7.sh`) | `d56e716757b90d35f06a34d0ed48aae9db27976cfc0d4f7979e780a967214b8d` | `684b49357bc2cb65451b493e2524041f40296328bb2f8acb52c03e465975cb98` |
| `node_relaunch.sh` | relaunch after a reclaim (installed as `/data/work/wp3_relaunch.sh`) | `2a230a7d34b8acb4e1230d193110bf920e29a7ca8bd256a8ea677c8e2144e779` | `5f7a86f9dce181ecf282f9582004342e887ec5da1e5608d5bb4265672a402847` |
| `rb_model_note.py` | 5b model-note tool | `103bd9730421c1ccbecc1652f09b157d7cbc421bb07d3b1f883c88a0395bbb22` | `5f20d1766ccbb191f314e82afc9c43f38fc7aa5b96407ee8dfb176bb2997983b` |
| `RUNBOOK_SNIPPET.md` | proposed runbook text for 5b to 7 | `ebb545a15eb47136db14cd06625bb37f424f7f7dfe6d6fecf49a5d4f1485c292` | `1654450af7080c7864f96c6b5af1967d38d4856dfcda79bbcc665b094af2adab` |

- `diffs/` holds `diff -u <baseline> <round 2>` for each of the four files. It also holds the harness diffs
  (`harness_tools.diff`, `harness_bin.diff`, `harness_scenarios.diff`, `unit_t_cls.sh.diff`).
- The final e2e batch ran on exactly the first three sha256 values above. They were recorded at the start and at the
  end of the batch (`e2e/final_batch_inputs.sha256`). The unit layers ran on the same files.
- `bash -n` passes for both drivers. Python `ast` passes for `rb_model_note.py` and for the three helpers embedded in
  node_step7.sh (cls.py, verify.py, poller.py). The unit test's `cls.py` is byte-identical to the one embedded in the
  final driver.
- `orig/` still holds the round-0 (impl) copies inherited with the baseline copy. They are not round-2 inputs.

## R2.2 Per-item outcome

| item | outcome | what changed | tested by |
|---|---|---|---|
| A | done | See "A: system-level shutdown evidence" below. | unit A-0..A-6 (real fixtures); e2e A1 (real tails), C2, C1(a) |
| B | done | See "B: one journal reader" below. | unit B-1..B-8; e2e B1, B2, B3, C1(b); P `j_sudo_fails`, `j_user_view`, `j_kernel_empty` |
| C | done | See "C: step 6 before step 7" below. | P: 16 `c6_*` cases and 3 relaunch cases; e2e PR (rename), G2 (recorded commit), H0 and every PASS case at `<C6>` |
| D | done | See "D: node_step34's archive copies" below. | `unit/t_archive.sh` (4 checks; the git refusal shown); snippet text = tested file (`diff` empty) |
| E | done | See "E: the retry after a deterministic abnormal end" below. | self-test: 8 new cases (30 in all); the final checker's reproduction (`unit/dae_repro.out`); P `dae_ok` (to STEP7_DONE), `dae_no_end`, `dae_no_cmd`, `dae_log_lr`, `dae_and_techfail`, `retry_no_cmd` |
| F | done | At every start pre() logs `sha256sum $0` (as an absolute path, resolved before the driver's `cd`) and `git show HEAD:scripts/wp3_runbook/node_step7.sh \| sha256sum`. It STOPs if they differ, or if `$0` cannot be read. The comparison runs once HEAD is known to be `<C6>`. The harness commits its own driver copy at `<CN>`, so every scenario exercises the check. | P `drv_mismatch` (STOP, 0 calls); every other scenario passes it (logged hashes equal) |
| G | done | Snippet wording. "Anything else STOPs" now matches the R1 code: a relaxation log that holds a traceback, with an exit status other than 137 or none, unless the launch exited 1 and the log ends with the exception line. The ban on running scripts by hand covers only `scripts/40 relax`/`zeroshot` and `scripts/41 run` on the node; the 7e analyses on the Mac are required. The snippet states that the order 5 → 6 → 7 is now enforced. | text review |
| H | done | `mkdrv.sed`: the scripts/35 marker is rewritten only on `pgrep` lines (`/pgrep/s\|35_finetune_frames\|q735finetune\|g`). FROZEN and STEP7_CODE keep `scripts/35_finetune_frames.py`, and `drv/SED_DIFF.txt` shows the rewrite only in the two pgrep lines. | P `s35_changed`: scripts/35 changed after training gives a STOP (with the round-1 sed, the path became `scripts/fx35finetune.py` and the check passed vacuously) |

### A: system-level shutdown evidence

`cls.py` `CLEAN` now accepts only these lines:
- `systemd[1]: Reached target (shutdown|poweroff|reboot|halt|kexec|final).target`, or the pre-249 form
  `systemd[1]: Reached target (System Power Off|Power-Off|System Reboot|...|Late Shutdown Services).`;
- `systemd[1]: Shutting down.`;
- any `systemd-shutdown[1]:` line;
- `systemd-logind[<pid>]: System is (powering down|rebooting|halting)` or `Power key pressed`.

Each identifier is anchored at the start of the ident field (`(?:^|\s)`).

These are no longer evidence:
- a user manager's (`systemd[<pid> ≠ 1]`) `Reached target shutdown.target - Shutdown.`;
- `systemd-journald: Journal stopped` (journald logs it at a restart too);
- a message that merely quotes "systemd-shutdown".

The classifier reads the boot's last 200 lines (it read 60 in round 1).

On the real fixtures:

| fixture | round-2 regex | round-1 regex |
|---|---|---|
| boot −3 (idle self-stop) | 6 lines match: clean | |
| boot −2 (idle self-stop) | 6 lines match: clean | |
| boot −1 (spot reclaim) | 0 lines match: not clean | |
| unprivileged view of boot −1 | 0 lines match | |
| current-boot user-manager logout lines | 0 lines match | matched `systemd[4462]: Reached target shutdown.target - Shutdown.` |
| a journald restart | 0 lines match | matched |

### B: one journal reader

The driver's `JCTL="sudo -n journalctl"`. Every journal read goes through `cls.py jctl()` with that command. It
returns `(lines, error)`, and an empty answer counts as a failed read. There are three readers of the journal, all
through that function:
- **pre()'s check** (`cls.py --jcheck`): it STOPs unless `sudo -n journalctl -b 0 -q -o short-unix _PID=1 -n 20`
  prints a `systemd[1]:` line and `sudo -n journalctl -k -b 0 -q -n 20` prints a line. The STOP message names the
  failing part and the sudo/journalctl error.
- **`boot_cause()`**: an unreadable boot journal (sudo error, `No such boot ID`, an empty answer, no timestamp) is a
  STOP marked `transient`. Round 1 fell back to the attempt files' mtimes and could give node-loss; that fallback is
  removed. With a notice and an unreadable journal, it is also a STOP, not spot-reclaim.
- **`oom()`**: an unreadable kernel journal after exit 137 is a transient STOP ("whether the OOM killer did it is
  unknown").

A transient STOP is not kept: no `att<n>.cause` is written, so the next start classifies the attempt again. An
operator word for it is applied and kept, without the transient flag. The QE-chain `--bootcause` gets 'undetermined'.

Harness stand-ins:
- `bin/sudo` accepts only `-n`, passes the command through, and fails like sudo when `ctl/sudo_fail` exists;
- `bin/journalctl` handles `-b 0` (the current boot), `_PID=1`, `-o`, and MODE `user` (nothing for `-k` or
  `_PID=1`).

### C: step 6 before step 7

pre() requires the following:
- `STEP6_DONE` holds exactly one line, a 40-hex `<C6>`;
- HEAD = `<C6>`, and the checkout is clean;
- `<CNOTE>` is a strict ancestor of `<C6>`.

Between `<CNOTE>` and `<C6>`:
- `git diff --no-renames --name-only` lists only `results/**`, plus `scripts/39_wp3_evaluate.py`, which is logged as a
  WARN naming its commits;
- no `MODEL_NOTE_*` changes;
- `STEP7_CODE` is byte-identical. It is scripts/40 and 41, the helpers 22, 29, 30, 32, 35, 37, 38 and `checks.py`,
  `scripts/wp3_runbook/node_step7.sh` and `node_relaunch.sh`;
- `STEP7_DATA` is byte-identical. It is the repository data scripts/40 reads: `results/fa_host`, and
  `results/objective2/dopant_shell/wp2b` and `wp2e`.

`wp3_eval.json`:
- it is absent at `<CNOTE>`, and `<C6>`'s own diff adds it;
- at `<C6>` it has `script` = `scripts/39_wp3_evaluate.py` and `mode` = `full`;
- `arms.finetuned.sha256` = the note's model_sha256. This is the field scripts/39 writes (`Arm.info()`) and reads in
  `--outcome-only`. If the field cannot be found, pre() STOPs;
- it is not a stand-in and not a `--cache` run;
- `git.head` is in [`<CNOTE>`, `<C6>`] by ancestry, with nothing uncommitted;
- `script_sha256` = the sha256 of scripts/39 at `<C6>`.

The round-1 note-commit checks stay on `<CNOTE>`:
- one parent, adding only the note;
- `note_status: complete`, the offset recorded, and so on;
- `<CS>` → `<CNOTE>` and the training commit → `<CNOTE>` identity of FROZEN.

The other changes:
- verify.py's commit check (every record, every attempt, `wp2e_minimum.json`) now compares with the checkout HEAD,
  `<C6>`;
- at the first start the driver records `<C6>` in `step7/commit`, and later starts at another commit STOP;
- `node_relaunch.sh`'s step-7 branch needs NOTE_COMMITTED and STEP6_DONE, and prints which is missing;
- snippet §A.4 and §B give the order note → step 6 → `<C6>` → STEP6_DONE → step 7, with KEEP_ALIVE during the wait
  (or a console stop).

### D: node_step34's archive copies

node_step34 writes the archive and dataset into the node checkout. From `node_step34.sh` lines 71–98: `$D/wp3/frames`,
`raw`, `test_extra/raw`, `chk/raw` and `dataset`. They are untracked there.

Nothing on the node reads them after STEP34_DONE, so no path fix is needed:
- training, the pre-flight and 5a use `$DS=/data/work/wp3/ds`, the copy made at line 105, and the retry command's
  expanded paths are the same;
- node_step34 exits at once once STEP34_DONE exists;
- node_step7, scripts/40, scripts/41 and their helpers reference none of these paths (grep).

Snippet §A.4.3 gives nine lines (`unit/d_procedure.txt`, byte-identical to the snippet's block):
- a check that no tracked file is modified, and that the only untracked files are those copies;
- sha256 per file of every node copy against `<C6>`, written to `archive_node_copy.cmp`; the count of copies that
  are not 'same' must be 0;
- `/data/work/wp3/ds` against the committed dataset;
- a check that every committed archive file has a node copy;
- a check that the five directories hold no tracked file;
- `mv` of the five directories to `/data/work/wp3/archive_node_copy/`;
- `git status --porcelain` empty.

Then the checkout is updated to `<C6>`, and HEAD and `status` are checked. The test also shows that git refuses the
update while the copies are present ("untracked working tree files would be overwritten").

### E: the retry after a deterministic abnormal end

`rb_model_note.py`:
- `dae_stops()` finds node_step34's `STOP: run<k>: second abnormal end` before the selected run's `4c: training
  started` line, unless a later `4c: run<k> discarded unread` line marks the PREV_CAUSE path (causes differ: a
  restart, not the retry);
- `retry_dae()` requires `run<k>.end` (an `[abnormal end]`), a first `[abnormal end]` in `restarts.txt`, and
  `train_command_retry.txt` (= the command with `--lr 0.0025`, shared `retry_command()`);
- `build()` requires the log's lr 0.0025 line;
- both retry kinds together, or two such STOPs, are refused (one retry);
- the note's section names both causes (restarts.txt, `run<j>.end`, `run<k>.end`) and the STOP line.

node_step7 `pre()` uses the same awk rule and the same requirements. For both retry kinds it now also checks
`train_command_retry.txt` and the training log's lr line.

Snippet §A.5:
- both ways into the retry, and how to tell same from different causes;
- KEEP_ALIVE for the whole retry training (node_step34's STOP removed it);
- the pre-flight and the by-hand start check (4d);
- the hand-made lines;
- a reclaim during the retry: discarded unread, listed, identical command in a new empty run; the same cause twice
  is a technical failure; no second retry.

On the final checker's reproduction (`final_check/dae/`):
- the round-1 tool refuses it ("Learning rate ... not ('0.005', ...)") even with the `.end` files;
- the round-2 tool refuses it as given ("run2.end ... missing"; the reproduction had not copied it);
- after `run1.end` and `run2.end` are added (snippet A.1), the round-2 tool exits 0 with `run: run3` and the
  retry section.

### Further changes made while implementing (not in the change list)

1. **`--no-renames` in the path rule (C).** With default rename detection, `git diff --name-only` lists only the new
   name of a renamed file. So a file moved from outside `results/` into `results/` between `<CNOTE>` and `<C6>`
   passed the rule. This was shown on the pre-fix driver: `e2e/scen/PR.before_fix.out` has "preconditions PASS" and
   26 script calls. The fix lists both sides. `PR.out` and P `c6_rename_into_results` show a STOP with 0 calls.
2. **`STEP7_DATA` identity, and the `wp3_eval.json` `git.head`/`script_sha256` checks (C).** Step 7 should run
   exactly what the note commit holds, and step 6 should provably come after the note and from the committed
   scripts/39.
3. **`step7/commit` (C).** One step 7 runs at one commit. Without this, a changed STEP6_DONE would surface only later,
   as a verify failure. G2 shows it.
4. **Transient journal STOPs are not kept (B).** Otherwise a passing sudo hiccup would force an operator word.
5. **The pre-249 systemd[1] target messages and `systemd-logind` lines (A),** and 200 tail lines instead of 60.
6. **§A.5 adds the by-hand start check (4d) and the 4d log line.** Round 1's §A.5 omitted them.
7. **§A.4.3 also compares `/data/work/wp3/ds` with the committed dataset (D).** Training used `ds`, and the note tool
   reads the committed dataset.
8. **`$0` is resolved to an absolute path before the driver's `cd` (F).**

## R2.3 Tests (laptop, synthetic; no MACE evaluation, relaxation, MD, training or QE)

### Unit layers

- `rb_model_note.py --self-test`: **30 cases, all pass** (`unit/selftest.log`). These are the 22 of round 1 plus 8
  new ones:
  - `dae-retry` (exit 0, both causes named);
  - `dae-retry-cut-by-a-reclaim` (exit 0, run4);
  - `dae-causes-differ-prev-cause` (exit 0, not a retry, lr 0.005);
  - `dae-without-retry-command`, `dae-without-end-file`, `dae-log-lr-0.005`, `dae-and-techfail-retry`,
    `dae-two-stops` (all exit 1).
- `unit/t_cls.sh`: **106 checks, 0 failures** (`unit/t_cls.out`). The 49 round-1 checks all still pass. 57 checks
  are new:
  - **A-0:** the regex line by line on the 4 real fixture files and 7 constructed line sets, beside the round-1 regex;
  - **A-1/A-2:** real boots −3 and −2 give a STOP for a clean shutdown;
  - **A-3/A-4:** real boot −1 gives node-loss, or spot-reclaim with a notice;
  - **A-5:** boot −1 with user-manager logout lines and a journald restart still gives node-loss or spot-reclaim;
  - **A-6:** boot −3 with a notice is a contradictory-evidence STOP;
  - **B-1:** sudo fails: a STOP, not kept; once readable, node-loss is kept;
  - **B-2:** `No such boot ID` gives a STOP;
  - **B-3:** an empty answer gives a STOP;
  - **B-4:** a notice and an unreadable journal give a STOP, not spot-reclaim;
  - **B-5:** rc 137 and an unreadable kernel journal give a transient STOP; with the OOM line it is oom; readable
    without an OOM line, a kept STOP;
  - **B-6:** an operator word for a transient STOP is applied and kept;
  - **B-7:** `--bootcause` with an unreadable journal gives a STOP;
  - **B-8:** `--jcheck`: ok, sudo fails, user-manager lines only, empty kernel journal, and the read goes through
    `sudo -n`.

  The real fixtures are copied to `unit/real/` and converted to short-unix by `unit/iso2unix.py`; the message text is
  unchanged.
- `unit/t_archive.sh` (D): **4 checks, 0 failures** (`unit/t_archive.out`).
- `unit/dae_repro.out` (E): the final checker's reproduction, before and after.

### End-to-end scenarios (`e2e/scen/<S>.sh`, output `<S>.out`)

The final batch ran from 09:31:13 to 09:59:55 UTC, with 35 scenarios, on the hashes of R2.1 (recorded at both ends in `e2e/final_batch_inputs.sha256`). B1 was re-run at 10:01 on the same three files, after a counter in its own script was made exact (it had also counted the words 'not classified' in the STOP text). Each
scenario starts from a fresh node state (`tools/init.sh`). The clone holds `<CN>` (the harness driver copies and
`rb_model_note.py`), `<CNOTE>` (the note alone, made by the round-2 tool) and `<C6>` (a `wp3_eval.json` with the
fields the driver reads, from `tools/mkc6.sh`; no model evaluated). The installed driver is the committed one. The
scenarios used bash 3.2, the flock/setsid/GNU-date/sudo/journalctl shims and a local metadata endpoint on port 18817.
Hard stops were SIGKILLs of the whole process group, followed by a new boot id.

| scenario | item(s) | fault injected | expected | observed | verdict |
|---|---|---|---|---|---|
| H0 | regression; C, F | none | STEP7_DONE at `<C6>` | STEP7_DONE: 12 relaxation and 12 MD records verified at `<C6>`, 12 JOB DONE, at most 60 threads; the two install hashes in the log are equal; reruns list empty | pass |
| P | B, C, E, F, H; regression | 58 precondition mutations, one per case, plus 3 relaunch cases | a STOP in pre() with 0 script calls, except `ok`, `retry_ok`, `dae_ok` and `c6_s39` (to STEP7_DONE) | 54 cases STOP with 0 calls. Among them: the 16 `c6_*` cases (missing, two lines, short, = `<CNOTE>`, not a descendant, scripts/40 changed, step-7 data changed, note changed, no eval, wrong sha, no sha field, not full mode, made before the note, dirty, renamed into results/); `drv_mismatch`; `j_sudo_fails`, `j_user_view`, `j_kernel_empty`; `dae_no_end`, `dae_no_cmd`, `dae_log_lr`, `dae_and_techfail`; `retry_no_cmd`; `s35_changed`; and the 29 round-1 cases. 4 cases PASS and reach STEP7_DONE (26 calls); `c6_s39` logs the WARN naming the scripts/39 commit. Each relaunch case names the missing marker or markers and starts nothing. | pass |
| PR | C (`--no-renames`) | a tracked file renamed from outside `results/` into `results/` between `<CNOTE>` and `<C6>` | STOP | on the driver before the fix, `PR.before_fix.out`: preconditions PASS, 26 calls (the gap). Final driver: STOP "files outside results/ changed (EXPERIMENT_AUDIT.md)", 0 calls | pass |
| A1 | A | the old boot's journal ends with (a) the REAL boot −1 tail (spot reclaim), (b) the REAL boot −3 tail (idle self-stop) | (a) node-loss reruns, then STEP7_DONE; (b) a STOP for a clean shutdown, no rerun | (a) 6 node-loss classifications, STEP7_DONE; (b) STOP quoting `systemd-shutdown[1]: Sending SIGTERM ...`, 0 reruns, 0 attempts 2 | pass |
| B1 | B | after a hard stop, the old boot's journal is gone (`No such boot ID`) | a STOP per cut attempt: none classified, none kept, nothing launched; with the journal restored, node-loss reruns, then STEP7_DONE | (1) 6 STOP pending 'could not be read', 0 classifications, 0 `att*.cause`, 0 calls; (2) 6 node-loss, STEP7_DONE | pass |
| B2 | B | `sudo -n` fails at the relaunch after a hard stop | a STOP in pre() at the journal check; then fixed, node-loss reruns, then STEP7_DONE | (1) journal STOP, 0 classified, 0 calls; (2) 6 node-loss, STEP7_DONE | pass |
| B3 | B | a relaxation OOM-killed (exit 137 and a kernel line) while `sudo -n` fails | a transient STOP, not kept; then fixed, oom rerun, then STEP7_DONE | (1) STOP "the kernel journal of boot ... could not be read", no `att1.cause`; (2) classified oom from the kernel line, RERUN oom, STEP7_DONE | pass |
| G2 | C (`step7/commit`) | after a hard stop, a new `<C6'>` in STEP6_DONE and the checkout | a STOP, no launch; restoring `<C6>` gives STEP7_DONE | (1) STOP "step 7 started at the commit ...", 0 calls; (2) 6 node-loss, STEP7_DONE | pass |
| C1 | A, B | (a) the node's clean poweroff sequence; (b) the journal answers as without system access at the relaunch | (a) a STOP for a clean shutdown; (b) a STOP in pre() at the journal check | (a) STOP quoting `systemd-shutdown[1]: Syncing ...`; (b) journal STOP, 0 classified, 0 calls | pass (b changed: round 1 classified node-loss from the user view) |
| C2 | A | user-manager logout lines (`systemd[2211]: Reached target shutdown.target - Shutdown.` and others), then a reclaim (a) with, (b) without a notice | (a) spot-reclaim reruns, (b) node-loss reruns, no STOP | (a) 10 spot-reclaim classifications, no STOP; (b) 6 node-loss, no STOP | pass (round 1: STOP) |
| F1 | regression | a foreign pw.x at the start | a STOP in pre() | STOP "a QE process is running" | pass |
| F2 | regression | a foreign pw.x after pool.done | the chain waits | waited about 20 s, then C1; STEP7_DONE | pass |
| G1 | regression | `wp2e_minimum.json` moved away after a hard stop | STOP, nothing launched | STOP "missing although it was written and checked earlier" | pass |
| I1 | regression | a rerun launch cut short before scripts/40 logged its attempt | REISSUE with the original evidence | 12 REISSUE and 8 RERUN; STEP7_DONE | pass |
| K1 | regression | hard stops mid-pool, first with a notice, then without | spot-reclaim, then node-loss | 18 RERUN, 2 REISSUE; at most 64 threads; STEP7_DONE | pass |
| K2 | regression | hard stops in the zeroshot and before wp2e | REISSUE of the single writer | 1 REISSUE; STEP7_DONE | pass |
| K4 | regression | hard stops around the chain | (b) logged only; (c) QE-INTERRUPTED and QE-RESUBMISSION | 1 QE-INTERRUPTED, 1 QE-RESUBMISSION; STEP7_DONE | pass |
| K5 | regression | hard stops during MD | node-loss reruns | 8 RERUN; at most 64 threads; STEP7_DONE | pass |
| L1 | regression | the reruns list is unwritable | a fail-closed STOP before any rerun | STOP "unexpected exit 1"; 0 reruns | pass |
| N1 | regression | a notice during the relaxations, then a reclaim | no launch after the notice | 0 launch records after the notice file; 7 RERUN spot-reclaim; STEP7_DONE | pass |
| N2 | regression | a notice while the pool ends | no chain launch during the hold | hold logged; list empty; STEP7_DONE | pass |
| N3 | regression (DRV_SED) | a notice and no reclaim; NOTICE_HOLD 4 s in the installed and committed copy | the hold, then resume | 0 launches inside the hold; resumed; STEP7_DONE | pass |
| O1 | regression | stray cause files | moved aside, not applied | both `.unused.<time>`; STEP7_DONE | pass |
| Q1 | regression | a QE job fails twice (multi-pass queue) | 2 QE-RESUBMISSION and QE-GAVEUP | as expected; STEP7_DONE | pass |
| Q2 | regression | a QE job fails once (single-pass queue) | a STOP, then the relaunch resubmits | as expected; STEP7_DONE | pass |
| R1 | regression | a hard stop between the record and its queue copy | republished by the identical command | STEP7_DONE | pass |
| S1 | regression | a pending STOP cut short by a reclaim | the relaunch prints the pending reason | prints the pending exception line | pass |
| T3 | regression | three hard stops on the same runs | FINAL (exhausted) | 3 FINAL; STEP7_DONE | pass |
| V1 | regression (C1 of round 1, now at `<C6>`) | outputs made by hand at `<CNOTE>` (MD) and at `<C6>` (relaxation) | (a) a first-start STOP; (b) the MD rejected by the commit check ("not the step-7 commit"), the relaxation ACCEPTED | as expected; STEP7_DONE | pass |
| W1 | regression (DRV_SED) | a hung relaxation, WALL_RELAX 4 s | WARN and STOP; a wall-time rerun | as expected; STEP7_DONE | pass |
| X1 | regression | a relaxation RuntimeError | FINAL and STOP, then the relaunch goes on | as expected; STEP7_DONE (23 done, 1 final) | pass |
| X2 | regression | a relaxation MemoryError; MD OOM kill; MD MemoryError | STOP (oom or final); oom reruns | 3 RERUN; STEP7_DONE | pass |
| X3 | regression | an MD RuntimeError quoting MemoryError; a SIGKILL without OOM (kernel journal readable: the STOP is kept) | a STOP each | operator node-loss RERUN, operator FINAL; STEP7_DONE | pass |
| X5 | regression | a non-fatal traceback, then OOM, or then a hard stop | oom and node-loss reruns | 2 RERUN; STEP7_DONE | pass |
| Z1 | regression | a refused launch; a lost MD record | no automatic re-issue; `retry`/`final` | as in round 1; STEP7_DONE | pass |

Every scenario ends with no harness process left (`survivors:` empty, or the batch-end check). The first full batch
(before the `--no-renames` fix) is kept in `e2e/scen/batch1/` for reference; its outcomes are the same except PR,
which it did not include.

What the e2e run cannot show:
- **Real page-cache loss on a power cut.** A SIGKILL keeps the page cache, so the sync ordering is checked by reading
  the code.
- **The real qe_queue.sh log, real scripts/39/40/41 and a real sudo.** They were not run, by rule; the fakes follow
  their source. That the node's `sudo -n journalctl` behaves as stubbed (system and kernel entries) is the operator's
  measurement of 2026-10-29.
- **`journalctl _PID=1`.** It was not run on the node. If it ever printed nothing there while `-b 0` showed systemd[1]
  lines, pre() would STOP. That fails closed, but would need a one-line change to grep the unfiltered output.
  (Superseded: the probe was run on the node in R3; see R3.2.)

### Harness changes (round 2)

| change | why |
|---|---|
| Paths `…/s7/fix` → `…/s7/r2/fix`; port 18761 → 18817; markers `fx*` → `q7*` (`q740wp3b`, `q741wp3md`, `q7pw.x`, `q7chain.sh`, `q7qe_queue.sh`, `q77-spot-poller`, `q735finetune`) | no collision with the round-1 or final-check harness |
| `bin/sudo` (new); `bin/journalctl` (`-b 0`, `_PID=1`, `-o`, MODE user); `bin/sha256sum` (stdin) | B; F (`git show … \| sha256sum`) |
| `mkdrv.sed`: `JCTL="…/bin/sudo -n …/bin/journalctl"` (absolute: never the real sudo); `/pgrep/s\|35_finetune_frames\|…\|` | B; H |
| `mkdrv.sh`: `DRV_SED` (a scenario's driver patch goes into the copy that is both installed and committed) | F: N3 and W1 used to patch the installed copy only |
| `init.sh`: kinds `complete/draft/retry/dae`; a kernel line and a systemd[1] line in each boot's journal; commits `<CN>`, `<CNOTE>` and `<C6>`; STEP6_DONE | B, C, E, F |
| `mkc6.sh` (new): the step-6 commit, with knobs `C6_SHA`, `C6_HEAD`, `C6_DROP`, `C6_MODE`, `C6_NOMARKER` | C |
| `lib.sh`: `reboot real:<fixture>` (a REAL journal tail, shifted to end at the reboot); `reboot clean` with the node's real sequence; a kernel line per boot; `rebuild`, `at_cnote`, `cn_of`, `gitc`; removals guarded with `${X:?}` | A, C |
| `iso2unix.py`, `fixtures/realjournal/` (copies of the operator's fixtures) | A |
| Scenarios: new A1, B1, B2, B3, G2, PR; P rewritten (58 cases + 3 relaunch cases); C1(b) and C2 now test the round-2 behaviour; N3 and W1 via DRV_SED; V1 comments | every item |

## R2.4 Decisions a human must confirm (round 2)

1. **Journal access through `sudo -n journalctl` (B).** The driver depends on `sudo -n journalctl` working from a
   non-tty process for the whole of step 7, and STOPs if it does not. No group membership or other system setting
   was changed or proposed. A STOP for an unreadable journal is not kept.
2. **The shutdown rule (A).** It accepts the pre-249 systemd[1] messages and `systemd-logind` ("Power key pressed",
   "System is …") as clean-shutdown evidence. A console stop sends the power key. Confirm that this list is
   complete, and that anything else in a boot's last 200 lines is no evidence of a clean shutdown.
3. **The checks between `<CNOTE>` and `<C6>` beyond the change list (C).** Each of these is a STOP; confirm each is
   wanted:
   - the `STEP7_DATA` identity;
   - no `MODEL_NOTE` change;
   - `<C6>` must itself add `wp3_eval.json` (a later commit on top of it does not qualify);
   - `wp3_eval.json`'s `git.head` must lie between `<CNOTE>` and `<C6>`;
   - its `script_sha256` must equal the sha256 of scripts/39 at `<C6>`;
   - `--no-renames`;
   - one step 7 runs at one commit (`step7/commit`).
4. **KEEP_ALIVE during the wait for step 6 (§A.4.1).** The snippet requires it if the node stays up, and offers a
   console stop instead (cheaper for a long wait). The driver still only WARNs while KEEP_ALIVE exists; it never
   removes it. Removing it after `preconditions PASS` is an operator step.
5. **The by-hand retry after a deterministic abnormal end (E, §A.5).**
   - A human judges whether the two causes are the same. node_step34 stops at any second `[abnormal end]`.
   - `run<k>` is never added to `restarts.txt`.
   - The tools tell the retry from a PREV_CAUSE restart only by a later `run<k> discarded unread` line.
   - A two-person check of the hand-made lines is proposed, as in round 1.
6. **Node-side archive copies (D).** They are moved to `/data/work/wp3/archive_node_copy/` and kept until the WP3
   result is written. Whether to delete them afterwards is the user's decision. Any `DIFF` in the comparison stops
   the procedure for a human.
7. **The install check (F).** It covers node_step7.sh only. An installed `wp3_relaunch.sh` that differs from the
   committed one is not detected (it does not run step 7, and node_step7 checks its own preconditions). The snippet
   asks the operator to install both from the commit.

---

# Round 1 notes (baseline `<harness>/fix/NOTES.md`, sections 1-4 unchanged)

Fixer output for `<harness>/impl/`. All work is under `<harness>/fix/`. Nothing in
the repository (`.../dopwork/ps`, branch feat/dopant-shell-dft-validation, HEAD c391d61) was edited, committed or
checked out. Nothing on the node or under `/data` was touched, and no `.audit/**` file was read or written. The frozen
scripts 39, 40 and 41 are unchanged.

## 1. Files and final sha256

| file | role | sha256 (final) | impl sha256 (before) |
|---|---|---|---|
| `fix/node_step7.sh` | step-7 driver (installed as `/data/work/wp3_step7.sh`) | `684b49357bc2cb65451b493e2524041f40296328bb2f8acb52c03e465975cb98` | `3befd79029763dfc88a718ad2ea929daaa43f9ca4b6faf4c3a6093564c794c60` |
| `fix/node_relaunch.sh` | relaunch after a reclaim (installed as `/data/work/wp3_relaunch.sh`) | `5f7a86f9dce181ecf282f9582004342e887ec5da1e5608d5bb4265672a402847` | `487d0a8fa07e1f9d40032da6107cd49750ad6ccf089bda391fdf7d63efb39410` |
| `fix/rb_model_note.py` | 5b model-note tool | `5f20d1766ccbb191f314e82afc9c43f38fc7aa5b96407ee8dfb176bb2997983b` | `21d70c9090256d87f612e402f8d8f12f4d9a363ad605e80c7ef33be0ae2b6a79` |
| `fix/RUNBOOK_SNIPPET.md` | proposed runbook text (also reproduced in section 5) | `1654450af7080c7864f96c6b5af1967d38d4856dfcda79bbcc665b094af2adab` | `2ed8da425473c2926f38e20785559e56dd88fb206bbde2c87d9fdcb1147ee6ef` |

- `fix/orig/` holds the impl copies.
- `fix/diffs/*.diff` holds `diff -u orig fixed` for each file.
- The three code files passed `bash -n` and Python `ast` checks, including the three helpers embedded in
  node_step7.sh (cls.py, verify.py, poller.py).
- The full scenario batch ran on exactly the first three sha256 values above. They were recorded at the start of the
  batch and checked again at its end (`e2e/final_batch_inputs.sha256`).
- After the batch, only one sentence of RUNBOOK_SNIPPET.md changed (the highest thread count seen: 62 → 64).

## 2. Per-finding outcome

Every surviving finding was applied. Line numbers refer to the files in `fix/`.

| id | outcome | what changed | tested by |
|---|---|---|---|
| C1 (major) | fixed | **cls.py `complete_check`.** A record counts as complete only if a node_step7 run-mode launch for the record's attempt exists and its pid equals the attempt's pid. If the launch's pid file was lost, the match is by attempt number. Otherwise the job STOPs: "a complete output that no node_step7 launch made". **verify.py.** The relax and md modes, and wp2e, take `<CNOTE>` and require `git.head == <CNOTE>`, an empty `uncommitted` list and `script_equals_head` true where present. This applies to the scripts/40 record, every attempt entry in it, `wp2e_minimum.json`, the scripts/41 record and every scripts/41 attempt. **First start** (no `7a.started` and an empty `step7/sync`): STOP unless `wp3b/relax`, `wp3md`, `step7/jobs`, `wp3b` (apart from the `relax` dir) and `/data/jobs/wp3b` (apart from `queue.log`) are empty. **Operator word `accept`:** adopts a complete output made outside the driver. It still has to pass verify (so it must have been made at `<CNOTE>`), and it is listed as ACCEPTED. | unit C1-a..f; e2e V1 (a, b, c); P `pre_record`, `pre_zeroshot`, `pre_md` |
| C2 (major) | fixed | **rb_model_note.py.** A DRAFT carries no machine-readable lines; it has `draft-` copies "for reference only". A complete note adds a fourth line, `note_status: complete`. **node_step7.sh `pre()`.** STOP if the note has a DRAFT banner, "NOT COMPUTED" or a `**Check:**` line; if it does not have exactly one `note_status: complete`; or if the line "- Selected model: <x> meV/cell" is missing. **Harness.** The note is now made by the fixed tool with `--m21-offset compute` through its own calculator hook (`e2e/tools/mknote.py`, a stub, no MACE), and the tool must exit 0. The hand edit of a DRAFT is gone. | self-test `no-offset-draft`, `rmse-mismatch-draft` (no machine lines); P `draft`, `draft_edited`, `no_status`, `check_line`, `no_offset` |
| C3 (minor) | fixed | `pre()` STOPs if `foreign_qe` (pw.x, neb.x, pp.x, qe_queue.sh) finds a process. It now also returns the pids in `$QEP`. The check is repeated just before the 7a zeroshot `run_sync`. | F1 (0 fake calls, STOP in pre); P `foreign_qe` |
| C6 (minor) | fixed | In `build()`: a start check that FAILs on the Initial record is refused (exit 1; item 2: void, never evaluated); an unknown basis is refused (exit 1); an RMSE_E_per_atom mismatch over 0.001 meV/atom is added to `draft` (exit 2), and its `**Check:**` bullet is kept. The self-test 'happy' stub now reproduces the selected epoch's RMSE, so it is a real exit-0 case. | self-test `start-check-fail`, `unknown-basis`, `rmse-mismatch-draft`, `happy` |
| C8 (minor) | fixed | `hold_check()`: once `step7/spot/notice.<this boot>` exists, `HOLD=1` for `NOTICE_HOLD` = 1800 s. It is checked in the pool loop, in `schedule()` before every single launch, and in `wait_clear()` before the 7c chain. Running children continue. After 1800 s with no reclaim, a WARN is logged and launches resume. With nothing running and runnable jobs waiting, a hold is not a "no progress" STOP. | N1 (no launch record after the notice file, sub-second mtimes); N2 (no chain launch during the hold, nothing QE-INTERRUPTED); N3 (hold, then resume) |
| C9 (info) | fixed | `FORBIDDEN_PREFIXES` = `--swa`, `--lora`, `--freeze`: any option of these families is refused, e.g. `--swa_lr`, `--lora_rank`, `--lora_alpha`, `--freeze`. Exact options are now anchored at a word start. Remaining gap: argparse abbreviations of the exact-match options (e.g. `--test_f`). The command comes from node_step34's fixed ARGS, which contain none. | self-test `forbidden --freeze`, `--lora_rank`, `--swa_lr` |
| C10 (info) | fixed | The driver variable is renamed `CNOTE`; `<CN>` keeps the runbook's meaning (the note's scripts_commit). The snippet adds a `<CNOTE>` row for the Placeholders table and uses `<CNOTE>` for the note commit and NOTE_COMMITTED. §C and the driver's last log line pass `--commit <CN>` (`$CS`), as the scripts/41 help says. | H0 last log line ("scripts/41 analyse --commit c391d61...") |
| C11 (info) | fixed | Each launch record keeps `evid=` (the original evidence). On a re-issue, cls emits that as `EVID` (used for `--rerun-note`); the re-issue text goes to `DETAIL`, which is used in the log and the REISSUE list line. | unit C11, F09-b; I1 (the re-issued L3's `--rerun-note`, kept by scripts/40 in attempt 2, holds the original node-loss evidence) |
| C12 (info) | fixed | Snippet §A.5 gives the by-hand procedure for the item-2 retry: `techfail_<run>.txt`, `train_command_retry.txt`, the hand-made step34.log lines in node_step34's format, rb_techfail, STEP34_DONE by hand, and a two-person check. Code support is under R8. | P `retry_ok` |
| C13 (info) | no change needed | The reading of the m21 host-wide offset is kept and stated, both in the note text and in the snippet (§A.2: "state it in the WP3 result"). | – |
| R1 (minor) | fixed | `derive()`, relaxation. The exception path (FINAL, or STOP oom/final for a MemoryError) applies only if the launch exited 1 and the last non-blank log line is the first exception line of the last traceback. With rc None or 137, the boot or OOM evidence decides, and the evidence notes the earlier traceback. Any other combination STOPs for a human, with all words allowed. A multi-line exception message also STOPs (fail-closed). | unit R1-a..f; X5 (non-fatal traceback + OOM: oom rerun; + hard stop: node-loss rerun); X1 (a real exception: still FINAL + STOP) |
| R2 (minor) | fixed | Same as C3; also F07. | F1, F2, P `foreign_qe` |
| R4 (minor) | fixed | Same as C2. | as C2 |
| R5 (minor) | fixed | Same as C8: the 7c chain is never started during the hold (`wait_clear`). | N2 |
| R6 (minor) | fixed | `listline …; sync; touch <marker>` now applies to QE-INTERRUPTED, QE-RESUBMISSION, QE-GAVEUP and the new ACCEPTED line, as FINAL already did. | code inspection. On the laptop a SIGKILL keeps the page cache, so the ordering cannot be shown; Q1, Q2 and K4 show the lines. |
| R8 (minor) | fixed | `pre()` takes the note's run from its own "training finished in …/run<n>; …sha256 <SHA>" line. Exactly one other finished run is allowed, and only as the retry's failed run: a "STOP: technical failure" line after it and before run<n> started, and `logs/techfail_<run>.txt` with "with <run>/wp3.model" and a `non-finite` line. rb_model_note.py `node_files`/`retry_of` checks the same things, plus `train_command_retry.txt` (= the command with `--lr 0.005` → `--lr 0.0025` and nothing else) and the log's "Learning rate: 0.0025, weight decay: 5e-07". The note gets a section "Technical failure and the one retry". The procedure is in snippet §A.5. | self-test `retry`, `retry-without-stop-line`, `retry-log-lr-0.005`; P `retry_ok`, `retry_no_stop`, `retry_no_tf`, `retry_two` |
| R9 (info) | fixed | `run_launch()`: an attempt n belongs to the last run-mode launch with `expect == n`. The pid is only a cross-check, and a mismatch STOPs ("made by another process"). | unit R9-a (the reviewer's T4: now classified from L2's boot, a STOP for its clean shutdown), R9-b |
| R10 (info) | fixed | Operator files are per attempt: `step7/cause.<label>.att<n>`. Every STOP line names the file and the words it accepts. Renames (`.used`, `.used.L<s>`, `.unused.<time>`) are followed by a directory fsync. A file that matches no current STOP (old name, other attempt, label not stopped) is moved aside as `.unused.<UTC>`, logged, and never applied. | unit R10-a..c; O1; X3 (a file written for a label that had not yet stopped was moved aside, then the right one applied) |
| R11 (info) | fixed | At pool start, `wp2e.ok` opens the gate only after `verify_wp2e`. If the file is missing, it STOPs. `wp2e_minimum.json` is verified again (model sha, commit) at the end of the pool and at the end. | G1 (STOP, no scripts/40 or 41 call after the relaunch) |
| R12 (info) | fixed | `WALL_RELAX`=36000 s and `WALL_MD`=15000 s (3 × expected). `wall_check()` runs every 60 s; once per launch it logs a WARN and calls `add_stop` naming the pid and `cause.<label>.att<n>`. The driver never kills. | W1 (harness copy with a 4-s limit; operator kill and `wall-time`; rerun; STEP7_DONE) |
| R13 (info) | fixed | `node_relaunch.sh` prints the reasons of the last driver run: its final `STOP:` line, or, if it was cut short while waiting, all its `STOP pending:` lines. `add_stop`/`finish_stop` also append the reasons to `STEP7_STOPPED`. | S1 (prints the pending exception STOP, not the older resolved one) |
| F01 (major) | fixed | Same as C2. | as C2 |
| F04 (minor) | fixed | Same as C8. | N1, N2, N3 |
| F05 (minor) | fixed | Same as R13. | S1 |
| F06 (minor) | fixed | Same as C6 (the mismatch makes a DRAFT, exit 2). | self-test `rmse-mismatch-draft` |
| F07 (minor) | fixed | `pre()` STOP and the zeroshot re-check (as C3). Before 7c, `wait_clear()` waits, with one log line, until no foreign QE process is left; it does not STOP. | F2 (the chain waited about 20 s for a foreign pw.x, then ran) |
| F08 (info) | fixed | QE-INTERRUPTED is listed only if some `<label>.out` has no JOB DONE, no `.gaveup`, and an mtime at or after the cut chain launch's epoch. Otherwise it is logged: "cut short, but no wp3b job was … nothing to list". | K4 (b) logged only; K4 (c) listed with the cut job |
| F09 (info) | fixed | A launch that ended by itself (`.rc` present) without the script logging its attempt is "refused". It is never re-issued automatically, live or not. The STOP accepts `retry`, `final` or (n > 0) a cause in `cause.<label>.att<n>`. The decision is kept in `L<s>.operator`, so it survives a hard stop before the new launch. An MD attempt with status 'complete' and no record accepts only `final`. | unit F09-a..f; Z1 (refused launch: a relaunch without a decision made no launch; `retry` re-issued once; `node-loss` for the lost MD record rejected, `final` accepted) |

## 3. Decisions a human must confirm

1. **Spot-notice hold (C8/R5/F04).** After a recorded notice, nothing new starts for 30 min (`NOTICE_HOLD=1800`).
   After that, launches resume with a WARN.
   - The alternative is to hold until the reclaim, with no limit. But then a false notice idles the node until the
     cost guard stops it.
   - The classifier already STOPs if a notice is more than 1 h older than the end of its boot.
   - The window that remains is one `launch()` (milliseconds), because the check runs before every launch.
2. **Wall-time limits (R12).** The limits are 10 h for a relaxation and 4.2 h for an MD run, each 3 × the expected
   length.
   - The 6-thread rate of about 1.2 s/call is an extrapolation from the measured 1.0 s at 8 threads.
   - When a job passes the limit, the driver STOPs (nothing new starts); it does not only WARN. The operator kills the
     job and gives `wall-time`.
3. **Note tool exit codes (C6/F06).**
   - A start-check FAIL is a refusal (exit 1, no note), not a DRAFT. Item 2 says such a run is void.
   - An unknown basis is also a refusal.
   - An RMSE_E_per_atom mismatch over 0.001 meV/atom makes the note a DRAFT (exit 2).
4. **Machine-readable lines (C2/R4/F01).** The line `note_status: complete` is new, and a DRAFT now has only
   `draft-`-prefixed copies of the lines. This changes the note format that node_step7.sh reads.
5. **Outputs made outside the driver (C1).**
   - The first start STOPs on any existing step-7 output.
   - A complete output needs the launch that made its attempt. If the pid file was lost, the match is by attempt
     number.
   - The new operator word `accept` adopts an output made outside the driver. It must still pass the commit check, so
     it must have been made at `<CNOTE>`, and it is listed as ACCEPTED.
   - Confirm that `accept` should exist at all. The stricter option is "move it aside, always".
6. **The by-hand item-2 retry (R8/C12, snippet §A.5).** Confirm these before they can be relied on:
   - the hand-made step34.log lines and their format;
   - `logs/techfail_<run>.txt` and `train_command_retry.txt`;
   - STEP34_DONE written by hand;
   - the rule that exactly one earlier finished run is allowed, and only after a "STOP: technical failure".

   A two-person check of the hand-made lines is proposed.
7. **Operator cause files (R10).**
   - They are now per attempt (`cause.<label>.att<n>`). The old name `cause.<label>` is moved aside, not applied.
   - The driver renames operator files (used or unused). "Never moves a script output" still holds; operator files are
     not script outputs.
   - New words: `retry` (refused launch) and `accept` (C1).
8. **Foreign QE before 7c (F07).** The driver waits rather than STOPs. `pre()` STOPs if a QE process is alive at
   start.
9. **Relaxation exception rule (R1).** A relaxation end is an exception only if it exited 1 and the exception line is
   the last line of the log. A real exception with a multi-line message therefore STOPs for a human instead of becoming
   FINAL. This is fail-closed, and the operator can give `final`.
10. **Refused launches (F09).** A refused launch is never re-issued automatically; a human gives `retry`, `final` or
    a cause. An MD attempt with status 'complete' and a lost record accepts only `final`.
11. **Placeholders (C10).**
    - Add the `<CNOTE>` row to the WP3_RUNBOOK.md Placeholders table.
    - The runbook's 7e command becomes `scripts/41 analyse --commit <CN>` (scripts_commit). Both commits hold identical
      scripts.
12. **C13 offset reading.** The reading is unchanged: the mean of E_model − REF_energy over the 31 m21 frames. State it
    in the WP3 result.
13. **Rejected findings (not changed).** C4, C5, C7, R3, R7, F02 and F03 were rejected upstream and are left as they
    were. Two scenarios in the table show their behaviour unchanged:
    - C1(b): a journal readable only as a user still gives node-loss;
    - C2: a user-manager "Shutdown" line is still read as a clean shutdown and STOPs (fail-closed).
14. **Commit and install order (unchanged from impl).**
    - Commit `rb_model_note.py`, `node_step7.sh` and `node_relaunch.sh` and the runbook text before the note.
    - Then commit the note on its own (`<CNOTE>`) and update the node checkout.
    - Install the drivers on the node with `.new` + sha256 + `mv`. Nothing on the node was touched by this work.

## 4. Tests (laptop, synthetic; no MACE evaluation, relaxation, MD, training or QE)

### 4.1 `rb_model_note.py --self-test`: 22 cases, all pass (`fix/unit/selftest.log`)

The cases cover:
- happy: exit 0, four machine lines, no DRAFT, stub RMSE consistent;
- `no-offset-draft` and `rmse-mismatch-draft`: exit 2, no machine lines, `draft-` copies;
- `start-check-fail` and `unknown-basis`: exit 1;
- `forbidden --freeze`, `--lora_rank` and `--swa_lr`: exit 1;
- `retry`: exit 0, with the retry section and lr 0.0025;
- `retry-without-stop-line` and `retry-log-lr-0.005`: exit 1;
- the 11 earlier cases: uncommitted script, test-host frame, test table, NaN loss, checkpoint mismatch, log epoch
  mismatch, model sha mismatch, restarts missing, script changed after training, valid hosts, test.xyz path.

### 4.2 Classifier checks: 49 isolated checks, all OK (`fix/unit/t_cls.sh`, output `fix/unit/t_cls.out`)

`cls.py` is extracted verbatim from the final node_step7.sh and run with a journalctl stub. The cases are:
- R1-a..f;
- R9-a (the reviewer's T4) and R9-b;
- R10-a..c;
- F09-a..f;
- C1-a..f;
- C11.

### 4.3 End-to-end scenarios (`fix/e2e/scen/<S>.sh`, output `<S>.out`, logs in `<S>/`): 29 scenarios, final batch 07:03–07:25

Each scenario uses a fresh node state (`tools/init.sh`). It runs the fixed driver under bash 3.2, with the
flock/setsid/GNU-date/journalctl shims and a local metadata endpoint. Hard stops are SIGKILLs of the whole process
group, followed by a new boot id.

| scenario | finding(s) | fault injected | expected | observed | verdict |
|---|---|---|---|---|---|
| H0 | regression, C10 | none | STEP7_DONE, ≤ 64 threads, empty list | STEP7_DONE; 12 relaxation and 12 MD records, 12 JOB DONE; at most 60 threads; last log line `scripts/41 analyse --commit c391d618…` (the note's scripts_commit) | pass |
| P | C2/R4/F01, C3/R2/F07, R8/C12, C1, regression | 31 precondition mutations, one per case, plus a relaunch without NOTE_COMMITTED | a STOP before any script runs; `ok` and `retry_ok` pass | 29 cases STOP with 0 fake calls, among them `draft`, `draft_edited`, `no_status`, `check_line`, `no_offset`, `foreign41`, `foreign_qe`, `retry_no_stop`, `retry_no_tf` and `retry_two`. `pre_record`, `pre_zeroshot` and `pre_md` pass the preconditions, then STOP at the first-start check with 0 fake calls. `ok` and `retry_ok` pass the preconditions (26 calls, STEP7_DONE). The relaunch without NOTE_COMMITTED starts nothing. | pass |
| N1 | C8/R5/F04 | notice during the relaxations; reclaim about 5 s later | no launch after the notice; the running children rerun as spot-reclaim | 0 launch records written after the notice file (the last one 0.28 s before it); 7 cut MD runs rerun as spot-reclaim; STEP7_DONE | pass |
| N2 | C8/R5/F04 | notice while the pool ends | no chain launch during the hold; nothing QE-INTERRUPTED after the reclaim | no C launch existed at the kill; hold logged; reruns list empty; STEP7_DONE | pass |
| N3 | C8 | notice, no reclaim (harness copy with NOTICE_HOLD=4 s) | hold, then resume | hold logged 1 s after the notice; resume 3 s later; 0 launches inside the hold; STEP7_DONE | pass |
| F1 | C3/R2/F07 | foreign pw.x alive at start | STOP in pre(), no MACE | STOP "a QE process is running"; 0 zeroshot calls | pass |
| F2 | F07 | foreign pw.x appears after pool.done | the chain waits | "7c: a QE process outside this driver is running … waits", then C1 20 s later; STEP7_DONE | pass |
| S1 | R13/F05 | a resolved older STOP; a new STOP pending; a reclaim cuts the wait | the relaunch names the pending reason | the relaunch printed only the pending "wp3bu_m30_GA_img0 ended with a Python exception" line | pass |
| W1 | R12 | a hung relaxation (harness copy with a 4-s limit) | WARN and a STOP naming the pid and `cause.<label>.att1`; the driver does not kill | as expected; operator kill and `wall-time` → RERUN attempt 2 (wall-time); STEP7_DONE | pass |
| O1 | R10 | a stray `cause.<label>` (old name), and a cause file for a label never stopped | moved aside and logged, not applied | both moved to `.unused.<time>`; list empty; STEP7_DONE | pass |
| G1 | R11 | after a hard stop, wp2e_minimum.json moved away (wp2e.ok remains) | STOP, nothing launched | STOP "missing although it was written and checked earlier"; 0 scripts/40/41 calls | pass |
| I1 | C11 | a rerun launch cut before scripts/40 logged its attempt | REISSUE; the note keeps the original evidence | REISSUE L3; scripts/40 attempt 2 `note` = the original node-loss evidence; `evid=` in L3.launch; STEP7_DONE | pass |
| X5 | R1 | a non-fatal traceback, then an OOM kill; a non-fatal traceback, then a hard stop | oom and node-loss reruns, no FINAL | `oom` and `node-loss` reruns; STEP7_DONE | pass |
| Z1 | F09 | an MD record lost after status 'complete'; a rerun launch refused (cell lock held) | MD: `node-loss` rejected, `final` accepted. Relaxation: refused-launch STOP, no automatic re-issue; `retry` re-issues once | MD: `'node-loss' is not one of ['final']`, then FINAL. Relaxation: STOP refused; a relaunch without a decision made 0 new launches (2 / 2); `retry` → REISSUE L3 → complete; STEP7_DONE (one MD final) | pass |
| V1 | C1 | (a) before the first start, an MD run made by hand at the pre-note commit; (b) after a start, an MD run by hand at the pre-note commit and a relaxation by hand at `<CNOTE>` | (a) first-start STOP. (b) both STOP. `accept`: the MD is rejected by the commit check, the relaxation is ACCEPTED. MD moved aside → the driver runs it | as expected; STEP7_DONE | pass |
| C1 | regression (rejected F03) | (a) clean shutdown; (b) journal readable as a user only | (a) STOP; (b) unchanged | (a) STOP "clean shutdown"; (b) node-loss reruns, the old behaviour | as before |
| C2 | regression (rejected F02) | a user-manager "Shutdown" line, then a reclaim (a) with (b) without a notice | unchanged (fail-closed STOP) | both STOP | as before |
| K1 | regression, C8 | a hard stop mid-pool with a notice, then one without | spot-reclaim, then node-loss reruns | 12 spot-reclaim and 8 node-loss RERUN, 2 REISSUE; STEP7_DONE; at most 64 threads | pass |
| K2 | regression | hard stops in the zeroshot and before wp2e exists | REISSUE of the single writer; nothing beside it | 1 REISSUE; STEP7_DONE | pass |
| K4 | F08, R6 | hard stops after pool.done, right after C1.launch, during a QE job with a notice, and after 7c.done | (b) logged only; (c) QE-INTERRUPTED and QE-RESUBMISSION | C1: "cut short, but no wp3b job was … nothing to list". C2: QE-INTERRUPTED (spot-reclaim, wp3b_m30_undoped_img0) and QE-RESUBMISSION .out.try1; STEP7_DONE | pass |
| K5 | regression | hard stops during MD and right after the last MD record | node-loss reruns | 8 node-loss reruns; STEP7_DONE | pass |
| X1 | regression (R1) | a relaxation RuntimeError | FINAL, STOP, then the relaunch goes on | as expected; STEP7_DONE with 11 relaxation records | pass |
| X2 | regression (R10) | a relaxation MemoryError; an MD OOM kill; an MD MemoryError | relaxation STOP (oom or final), `oom` via `.att1`; MD oom reruns | as expected; STEP7_DONE | pass |
| X3 | regression (R10) | an MD RuntimeError quoting MemoryError; a relaxation SIGKILL without OOM | a STOP each; `node-loss` and `final` via `.att1` | RERUN node-loss (operator) and FINAL (operator); STEP7_DONE | pass |
| T3 | regression | three hard stops on the same MD run and relaxation | FINAL (exhausted), no STOP | 3 FINAL exhausted; STEP7_DONE | pass |
| R1 | regression | a hard stop between the first record and its queue copy | republished by the identical command | "re-invoked (identical command) to complete the copy"; STEP7_DONE | pass |
| L1 | regression | the reruns list is unwritable | a fail-closed STOP before any rerun | STOP "unexpected exit 1"; 0 reruns started | pass |
| Q1 | regression, R6 | a QE job fails twice (multi-pass queue) | 2 QE-RESUBMISSION and QE-GAVEUP | as expected; STEP7_DONE | pass |
| Q2 | regression | a QE job fails once (single-pass queue) | a fail-closed STOP after the chain; the relaunch resubmits | as expected; STEP7_DONE | pass |

What the e2e run cannot show:
- **Real page-cache loss on a power cut.** A SIGKILL keeps the page cache. The sync ordering (R6, markers) is
  therefore checked by reading the code.
- **The real QE log format.** The real qe_queue.sh and its log are not on the laptop, so the F08 evidence uses only
  the `.out` files.
- **The real scripts/40 and scripts/41.** They were not run, by rule. The fakes follow their source.

### 4.4 Harness (`fix/e2e/`) and what differs from the review harness

The base is `<harness>/review/e2e/`, copied and adapted. Nothing in the repository was touched.
`data/work/ps_wp3.orig` is a fresh local clone at c391d61 with its `origin` remote removed, so nothing can be pushed
anywhere.

| change | why |
|---|---|
| Paths `…/review/e2e` → `…/fix/e2e`; the drivers come from `fix/` (`tools/mkdrv.sh`, `tools/mkdrv.sed`) | test the fixed files |
| Process markers `fx40wp3b`, `fx41wp3md`, `fxpw.x`, `fxchain.sh`, `fxqe_queue.sh`, `fx7-spot-poller`; metadata port 18761 | no collision with any other harness on this Mac; the drivers' pgrep patterns are rewritten to match |
| `mkdrv.sed`: `; TICK=5;` → `; TICK=1;` | the constants line now continues after TICK |
| `tools/fake41.py`: the record and every attempt carry `git_state()` (head and uncommitted of 41 and 35), as the frozen scripts/41 (`rec["git"] = git_state()`, attempt `"git": gs`) | needed by the C1 commit check |
| `tools/fake40.py`: new directive `tbprint <k>` (a non-fatal "Exception ignored in" traceback on stderr) | R1 scenario X5 |
| `tools/init.sh` `complete`/`draft`/`retry`. The note is made by the **fixed** `rb_model_note.py`: `complete` and `retry` through `tools/mknote.py` (the tool's own `_CALC_FACTORY` hook, stub E = REF + 0.2 meV/atom, which matches the results file), with exit 0 required; `draft` without `--m21-offset compute`, with exit 2 required. `retry` adds a failed run1 (finished, then `STOP: technical failure`), `logs/techfail_run1.txt`, `train_command_retry.txt`, the by-hand lines of §A.5 and the lr 0.0025 log line. | C2, R8 |
| `tools/cond_qe_running.sh` | K4 (c) kills while a wp3b job runs |
| Scenarios new: N2, N3, F2, W1, O1, G1, I1, X5, Z1, V1; changed: N1 (sub-second mtimes), P (13 new cases; `foreign41` now uses the harness marker and kills by PID, not `pkill -f`), K4 (c), X2/X3 (per-attempt cause files; X3 writes a file only for a STOP the driver named) | one or more per finding |

The frozen scripts were not modified. The fakes reproduce their file contracts: locks, records, attempt logs with
pid, git and identity, `--rerun-cause` rules, at most 3 attempts, the single writer of `wp2e_minimum.json`, and the QE
input published only after the record. No MACE evaluation, relaxation, MD, training or QE ran on the laptop.

## 5. Runbook snippet

The round-1 verbatim copy is not repeated here: it is superseded by the round-2 `RUNBOOK_SNIPPET.md`. The
round-1 text is `<harness>/fix/RUNBOOK_SNIPPET.md`, and `diffs/RUNBOOK_SNIPPET.md.diff` shows the change.

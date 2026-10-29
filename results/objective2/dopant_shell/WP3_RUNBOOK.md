# WP3 runbook: amendment m item 7, steps 2–8

This runbook covers `results/objective2/dopant_shell/PLAN.md`, amendment 2026-10-28m, item 7 (Order of work),
steps 2–8. It covers item 6 as well, which runs only after a Validated outcome. Run every command from the
repository root unless a step says otherwise. Paths are relative to the repository root unless they are
absolute. Anything in `<...>` is a placeholder.

The helper scripts in the Appendix were all tested on 2026-10-28, but only on SYNTHETIC data: stub frames
and edited copies of archived outputs (see "How this runbook was tested" at the end). None of those
numbers is a WP3 result.

This file is run control, not pre-registration: where it and PLAN.md amendment m differ, the amendment
governs, and any such difference is listed in the WP3 result.

## Placeholders

| placeholder | meaning |
|---|---|
| `<C1>` | the step-1 commit (scripts 29, 33, 34, 39, 40 and 41 committed; gate-only passed there) |
| `<PY>` | Python of the mace-torch **0.3.16** environment. On the node this is `/data/miniforge3/envs/mace/bin/python`; on the Mac, `../venv/bin/python` |
| `<MTRAIN>` | `mace_run_train` of that node environment (`/data/miniforge3/envs/mace/bin/mace_run_train`) |
| `<NODE_REPO>` | a clean checkout of `<C1>` on the node, with the band files at `<NODE_REPO>/../bands` (byte-identical to the Mac's `../bands`). With the node drivers it is `/data/work/ps_wp3`, at the commit the driver ran at. |
| `<NODE_WORK>` | node work directory for everything that is not a QE job (e.g. `/data/work/wp3`). With the node drivers it is `/data/work/wp3` (hard-coded). |
| `<MAC_STAGE>` | Mac staging directory **outside** the repository (pulled campaigns, work dirs, model) |
| `<FM>` | absolute path of the foundation file `20231203mace128L1_epoch199model` on the node |
| `<RUN>` | absolute path of a **new, empty** training directory on the node |
| `<SHA>` | sha256 of `<RUN>/wp3.model`, as recorded in the committed model note |
| `<CN>` | the commit recorded in the model note: scripts 39, 40 and 41 are committed and unchanged there |
| `<CNOTE>` | the commit that adds the model note, on its own. Its parent is normally `<CN>` (node_step7 requires only that `<CN>` is an ancestor of `<CNOTE>`), and scripts 39/40/41 are byte-identical in both. `/data/work/wp3/NOTE_COMMITTED` holds it. |
| `<C6>` | the commit that adds `results/objective2/dopant_shell/wp3/wp3_eval.json`, the output of step 6. It is a descendant of `<CNOTE>`. Between the two, only files under `results/` change, plus a `scripts/39` fix after a step-6 failure, and no commit but `<C6>` touches `wp3_eval.json`. The node checkout is at `<C6>` during step 7, and `/data/work/wp3/STEP6_DONE` holds it. |
| `<T>` | the training thread count fixed by the timing run |
| `<YYYY-MM-DD>` (also `<date>`) | the note's date; the file is `MODEL_NOTE_<YYYY-MM-DD>.md`, which rb_model_note.py and node_step7.sh enforce |
| `run<n>` (also `run<j>`, `run<k>`, `run<m>`, `run<a>`, `run<b>`) | a numbered training directory `<NODE_WORK>/run<n>`; Appendix §A.5 says which run each letter names |

`<run>` in `train_command.txt` and in the two `sed` commands of Appendix §A.5 is literal text (node_step34 writes
`--work_dir <run>`); do not substitute it.

The QE campaigns are `/data/jobs/<campaign>/<label>/<label>.in`, run by `/data/setup/qe_queue.sh` through
`/data/setup/chain.sh`:
- `wp3`: scripts/35 frames;
- `wp3x`: item 1′;
- `wp3chk`: q = +1 checks;
- `wp3b`: WP3b.

The queue reruns an output without JOB DONE once. It renames the failed output `<label>.out.try1`; after
a second failure it writes `<label>.out.try2` and the empty marker `<label>.gaveup`. `run_qe.sh` rewrites
`pseudo_dir` in each input in place. No script compares input text across that line.

Archive layout (item 1e, plus two places that amendment m leaves open):

```
results/objective2/dopant_shell/wp3/frames/            scripts/35 frames + frames_report.json
results/objective2/dopant_shell/wp3/raw/               WP3 <label>.{in,out}.gz, <label>.out.tryN.gz, <label>.gaveup
results/objective2/dopant_shell/wp3/test_extra/raw/    item-1' files, same naming
results/objective2/dopant_shell/wp3/chk/raw/           chk_<frame>_q1 files (my choice; scripts/33 accepts any depth)
results/objective2/dopant_shell/wp3/dataset/           scripts/33 output
results/objective2/dopant_shell/wp3/wp3b/raw/          wp3b_/wp3bu_ QE files (my choice)
```

Keep the scripts/40 and scripts/41 `--work` directories, and the training `<RUN>`, **outside**
`results/objective2/dopant_shell`. If you archive them there, archive them as tarballs. The reason: the
relax work dir holds staged copies `<label>.qe/<label>.in`. Loose copies below the `--dft` root would put
a second input with the same label next to `wp3/wp3b/raw/<label>.in.gz`. scripts/39 `index_inputs` and
scripts/37 `index_outputs` stop when a label occurs twice.

## Step 1 (precondition; not part of this runbook)

1. scripts/40 relaxes with ONE FIRE run to fmax 0.01 eV/Å, at most 10 000 steps (decided 2026-10-28).
   Item 4's Relaxation bullet is the operative text and states one fmax and one cap. The
   Information-state sentence only gives the source of those two numbers (protocol v2.1); the two-stage
   0.02 → 0.01 schedule belongs to item 6. The reading is recorded in every record (`protocol.reading`).
   Commit the changed scripts 29, 33 and 34 and the new 39, 40 and 41 together. scripts/40 hashes 29, 30,
   32, 35, 37 and 38 into every record, and analyse notes uncommitted helpers.
2. Then run the gate:

```
<PY> scripts/39_wp3_evaluate.py --gate-only --out results/objective2/dopant_shell/wp3/gate_only_step1.json   # must exit 0, GATE PASS
```

Note: an `--out` inside `results/objective2/dopant_shell` is refused while scripts 39, 32 or 37 are
uncommitted.

## Step 2: scripts/35, then the DFT (about 154 SCF: 96 + 50 + 8; about 18 node-hours)

### 2.0 Node environment (once)

1. Run `ehpc/node/install_mace.sh`. **That script does not pin the version.** Pin it afterwards:

```
source /data/miniforge3/etc/profile.d/conda.sh && conda activate mace
pip install "mace-torch==0.3.16"
<PY> -c "import mace, torch, e3nn, ase; print(mace.__version__, torch.__version__, e3nn.__version__, ase.__version__)"   # mace must be 0.3.16
```

2. Copy `~/.cache/mace/20231203mace128L1_epoch199model` from the Mac to `<FM>`. Then check its hash:
   `sha256sum <FM>` must print `01bfe22100139f424713cf921144e5509cbe353d67aa9fa1be9c6e1e0ed35845`.
3. Create the checkout:

```
git clone <repo> <NODE_REPO> && cd <NODE_REPO> && git checkout <C1>
```

`<repo>` is any clone source. The drivers' checkout `/data/work/ps_wp3` was cloned from a git bundle, and its `origin`
is the file `/data/work/ps_wp3.bundle` (§A.4.3 of the appendix shows how it is updated).

   Then copy `../bands` next to it. The node drivers' checkout is `/data/work/ps_wp3`. Its remote `origin` is
   the file `/data/work/ps_wp3.bundle`, a git bundle made on the Mac; Appendix §A.4.3 shows how it is updated.
4. `/data/KEEP_ALIVE` is present throughout training (item 2, Keep-alive): `node_step34.sh` creates it
   before the pre-flight and removes it after the technical-failure check. Outside training it is needed
   only while the node is to stay up with nothing running, as while it waits for 5b and step 6 (Appendix
   §A.4.1): since 2026-10-29 the idle cron counts pw.x, a 1-min load above 1 or a login as busy, and after
   60 idle min stops the node in economical mode (StopCharging). Chain the steps so the node does not wait
   on the Mac, and stop it with `python3 /data/setup/ecs_selfstop.py stop` (or from the console) when
   nothing is queued.

### 2a. WP3 frames: scripts/35, ONE process, on the node

```
cd <NODE_REPO>
nohup <PY> scripts/35_finetune_frames.py --hosts 05 06 08 12 15 20 --bands ../bands \
    --frames <NODE_WORK>/wp3_frames --qe /data/jobs/wp3 --threads 8 > <NODE_WORK>/wp3_frames.log 2>&1 &
```

- Keep the defaults (`--md-steps 1500 --fmax-bound 15`): scripts/33 refuses any other `params`.
- Never run per-host scripts/35 processes in parallel into one `--frames`. Each process holds its own
  copy of `frames_report.json` and overwrites the others'.
- A sequential re-invocation with the same settings resumes.
- When the run ends, `frames_report.json` holds 96 records. Rejected frames have `ok: false`, are not
  regenerated (m 1d), and are listed by scripts/33.

### 2b. Item 1′ inputs: 50, with scripts/30 (node or Mac)

```
for hd in m10:GA m18:GA m04:Sr m14:Sr m27:Sr; do h=${hd%%:*}; d=${hd##*:}
  for s in undoped $d; do for k in 0 2 3 4 6; do L=${h}_${s}_img${k}
    <PY> scripts/30_qe_singlepoint.py ../bands/band_${s}_${h}.extxyz@${k} --label $L --out /data/jobs/wp3x/$L
  done; done; done
```

The `@k` is required. scripts/30 does not check that the label matches the index, and it reads the last
frame when no index is given. Step 2d catches either mistake.

### 2c. q = +1 check inputs: 8, with scripts/30 --charge 1 (after 2a, because two of them need its frames)

```
for s in Sr undoped; do
  for k in 0 3; do L=chk_m15_${s}_img${k}_q1
    <PY> scripts/30_qe_singlepoint.py ../bands/band_${s}_m15.extxyz@${k} --charge 1 --label $L --out /data/jobs/wp3chk/$L; done
  L=chk_m05_${s}_img0_q1
  <PY> scripts/30_qe_singlepoint.py ../bands/band_${s}_m05.extxyz@0 --charge 1 --label $L --out /data/jobs/wp3chk/$L
  md=$(<PY> -c "import json; r={x['label']: x['ok'] for x in json.load(open('<NODE_WORK>/wp3_frames/frames_report.json'))['records']}; print(next((k for k in ('md450','md300') if r['m05_${s}_'+k] is True), ''))")
  [ -z "$md" ] && { echo "m05_${s}: md450 and md300 both rejected: no (b) job (scripts/33 rule: (b) fails)"; continue; }
  L=chk_m05_${s}_${md}_q1
  <PY> scripts/30_qe_singlepoint.py <NODE_WORK>/wp3_frames/m05_${s}_${md}.extxyz@0 --charge 1 --label $L --out /data/jobs/wp3chk/$L
done
```

The labels are `chk_<frame label>_q1` (m 1c). Their q = 0 partners are WP2b outputs that already exist
(m15 and m05, image 0 and image 3) and the WP3 md450 (or md300) job of 2a.

### 2d. Check every input before any DFT (no MACE, no QE)

```
<PY> scripts/wp3_runbook/rb_verify_inputs.py /data/jobs <NODE_WORK>/wp3_frames      # must print ALL INPUT CHECKS PASS
```

The check requires:
- exactly the 50 item-1′ labels and the 8 expected `chk_` labels;
- every input equal to the frame that scripts/33 will pair it with (1e-6 Å);
- tot_charge 0 (item 1′) or 1 (`chk_`);
- prefix = label, `scf`, and positions with no if_pos columns;
- for the 96 WP3 inputs: the job directories under `/data/jobs/wp3` are exactly the ok records of
  `frames_report.json`; each frame and input is non-empty and the input equals its frame (1e-6 Å); an input
  not yet run has the `input_sha256` of its `meta.json`. scripts/35 writes frames and inputs without fsync,
  so a hard stop can leave an empty file under an ok record; this check catches it before its DFT, so it
  never becomes a 1d "gave up" drop. A failure here is an amendment question, not a drop.

`node_step34.sh` repeats this check before the 3a archive.

### 2e. Run the DFT

```
nohup /data/setup/chain.sh wp3 wp3x wp3chk > /dev/null 2>&1 &     # one 64-rank queue at a time; logs in /data/jobs/<c>/queue.log
```

Handling of failed and unconverged jobs:
- **No JOB DONE.** The queue resubmits the identical input once, as m 1d and item 1′ require.
- **Item 1′ only (wp3x): JOB DONE without "convergence has been achieved".** Re-run the job once with
  identical settings (item 1′, Completeness). In its job directory:

  ```
  n=$(ls <label>.out.try* 2>/dev/null | wc -l); mv <label>.out <label>.out.try$((n+1))
  ```

  Then restart `chain.sh wp3x`. Item 1′ grants this re-run separately from the 1d resubmission (the
  amendment governs; corrected 2026-10-29). A re-run that stops without JOB DONE (for example, a spot reclaim)
  is resubmitted once with the identical input, and a second stop is given up by the queue. If the job had
  already used its 1d resubmission before the unconverged output, the queue decides at once. A re-run that is
  again unconverged is final: the job is incomplete. Record each re-run and resubmission
  (`node_step34.sh` writes them to `<NODE_WORK>/item1p_rerun.list`).
- **WP3 frames (dropped) and `chk_` jobs (fail their test).** These are never re-run for an unconverged
  SCF.

### Node drivers used for steps 2–4 (2026-10-28)

Steps 2a–2e run as `scripts/wp3_runbook/node_step2.sh`, and steps 2e (item-1′ re-runs), 3a–3c and 4a–5a
as `scripts/wp3_runbook/node_step34.sh`, both in the node checkout `/data/work/ps_wp3`. They run the
commands of this runbook, with two operational differences:
- **scripts/35 per host.** MACE-MP-0 float64 on a 234-atom cell takes 1.0 s per call at 8 threads and
  0.56 s at 32 on the node, so one all-host process would run about 12 h. Six processes run instead, one
  per training host (`--hosts <h> --threads 10`), each into its own `--frames` directory. Seeds come from
  the labels and the settings are identical. The rattle frames are bitwise the same as an all-host
  process would make. The MD frames are statistically equivalent but not bitwise: 1500 Langevin steps are
  chaotic, so thread-order rounding (which differs between any two thread counts, including the default
  5) grows into a different end frame. Their reports are merged in host order into one `frames_report.json`.
  The literal command of m 1d (`--hosts 05 06 08 12 15 20`, defaults) is then run on the merged
  directory: it resumes, adds no frame, and the driver checks that the report is unchanged.
- **Steps 3a–3c on the node.** The archive and `scripts/33` are run in the node checkout, so the node
  does not idle between the DFT and training. The archive and dataset are then copied to the Mac and
  committed.

Operating the drivers (added 2026-10-29, after an adversarial review with stubbed end-to-end tests of every
hard-stop point):
- **Resumable.** Each step leaves a marker written after `sync` (`frames_copied`, `archived_<c>`,
  `s33.done`, `item1p_rerun.done`, `timing.txt`), so a relaunch after a reclaim redoes only the part that
  was cut short. A part without its marker is removed and redone, and the redo is logged.
- **One instance.** Each driver takes a `flock` (`step2.lock`, `step34.lock`), which scripts/35, the QE
  chain and the training inherit. A relaunch is refused while any earlier instance or child is alive.
  Before a relaunch, check with `pgrep` that none is.
- **Installing a new copy.** Write it as `<file>.new`, check its sha256, then `mv` it over the old one. Never
  write onto a running driver: bash reads its script while it runs.
- **After a reclaim.** Relaunch `node_step2.sh` (if step 2 had not finished) and the STEP2_DONE waiter, or
  `node_step34.sh` (if STEP2_DONE exists), with `setsid nohup`. A training run cut short by the reboot is
  classified `[node loss]` from the boot time and restarted automatically in a new, empty `run<n>`.
  `scripts/wp3_runbook/node_relaunch.sh` (installed as `/data/work/wp3_relaunch.sh`) does this. It starts
  nothing while any driver, scripts/35, QE or training process is alive, or after a deliberate STOP.
  During the by-hand item-2 retry (Appendix §A.5) never start `node_step34.sh`; `wp3_relaunch.sh` only refuses
  then. After a reclaim during the retry, do the interruption steps of §A.5 by hand.
- **Training restarts (4e).** A run that ends without `wp3.model` is discarded unread. It is never deleted or
  reused, and the identical command runs in `run<n+1>`. Each restart is listed with its cause and time in
  `<NODE_WORK>/restarts.txt` as one of four kinds:
  - `[node loss]`;
  - `[abnormal end]`, seen by the driver: an exception, OOM, a kill, a non-zero exit, or no Initial record
    within the 2-epoch time + 30 min;
  - `[start check FAIL]`, corrected by hand before the relaunch;
  - `[operator]`.
  The driver stops for a human at a second `[abnormal end]`, even when the causes differ. If the causes
  differ, relaunch it by hand with `PREV_CAUSE='<cause> <UTC time>'` (the command is in Appendix §A.5).
  `restarts.txt` and `item1p_rerun.list` go into the 5b model note and the WP3 result.
- **Keep-alive after a restart.** `/data/KEEP_ALIVE` lives on `/data` and survives a reclaim. After a console
  restart that is not followed by a driver relaunch, run `rm -f /data/KEEP_ALIVE`, except during the by-hand
  retry training (Appendix §A.5, sub-step 2) and while you keep the node up for 5b and step 6 (§A.4.1).
- **Driver killed while training runs** (`step34.log` ends with `STOP: unexpected exit 143`, and KEEP_ALIVE
  is kept), and node_step34's STOPs that ask for 5a by hand (`<run> has wp3.model: judge it from its log and
  run 5a by hand`; `technical-failure CHECK ERROR`). Do 4d–5a by hand, and log each step in node_step34's line
  format (`[<UTC>] ...`, with `<UTC>` from `date -u +%FT%TZ`) in `/data/work/wp3/step34.log`: rb_model_note.py
  and node_step7.sh learn of 4d–5a only from `step34.log`, `logs/techfail.txt` and STEP34_DONE.
  1. If `step34.log` has no `4d: start check PASS` line for the run, do 4d as soon as the Initial record exists
     and append `[<UTC>] 4d: start check PASS: <rb_startcheck.py output>`. On a FAIL, kill the run
     (`kill $(cat /data/work/wp3/run<n>.pid)`), write `[start check FAIL] <UTC>: <rb_startcheck.py output>` to
     `/data/work/wp3/run<n>.end` and start node_step34 by hand (Appendix §A.5): it discards the run and starts
     the identical command in a new run.
  2. Wait for the run to end. If it ends without `wp3.model`, start node_step34 by hand with
     `PREV_CAUSE='<cause> <UTC time>'` (Appendix §A.5): it discards the run and restarts the identical command.
     Judge an abnormal exit after `wp3.model` was written from its log (item 2 'Model written, then abnormal
     exit'). Unless node_step34 logged it already (the CHECK ERROR case), append
     `[<UTC>] 4: training finished in /data/work/wp3/run<n>; wp3.model sha256 <sha256 of its wp3.model>; restarts:
     <number of lines of restarts.txt, 0 if there is none> (restarts.txt)`.
  3. Run 5a as node_step34 does:
     `cd /data/work/ps_wp3 && <PY> scripts/wp3_runbook/rb_techfail.py /data/work/wp3/run<n> /data/work/wp3/ds > /data/work/wp3/logs/techfail.txt 2>&1; echo "exit $?"`.
     Library warnings may stand before or after rb_techfail's own lines; they do not count. Exit 0, with
     `no technical failure (items checked here)` on the line after `<N> m21 frames evaluated with
     /data/work/wp3/run<n>/wp3.model`, is a pass. A `non-finite ...` line there is a technical failure: follow 5a
     and Appendix §A.5. Anything else (for example an import error) gives no verdict: find the cause and run it
     again.
  4. On a pass, append `[<UTC>] 5a: no technical failure (items checked here)`. Remove KEEP_ALIVE unless the node
     is to stay up for 5b and step 6 (§A.4.1), then run `sync; touch /data/work/wp3/STEP34_DONE`.

  Two reviewers check these lines before STEP34_DONE, as for the retry (Appendix §A.5).

## Step 3: archive, then scripts/33 (node_step34, in the node checkout; copied to the Mac and committed)

With the node drivers, 3a–3c have already run in the node checkout `/data/work/ps_wp3`: node_step34 ran the
`rb_archive.sh` lines of 3a on `/data/jobs/wp3`, `wp3x` and `wp3chk`, copied the frames from
`/data/work/wp3/frames`, and ran the `rb_test_hosts.py` line of 3b and the scripts/33 command of 3c there. It
logged the counts, the check outcome and w_E in `step34.log` (`3a:`, `3b:`, `3d:` and `3:` lines). Do not run 3a–3c
again on the Mac: neither `rb_archive.sh` nor scripts/33 (3c runs once). Copy the node's files byte for byte, check
the copy, and commit it before 5b; Appendix §A.4.3 compares the committed files with the node copies before step 7:

```
for d in frames raw test_extra chk dataset; do rsync -a dft:/data/work/ps_wp3/results/objective2/dopant_shell/wp3/$d/ results/objective2/dopant_shell/wp3/$d/; done
for d in frames raw test_extra chk dataset; do rsync -anci dft:/data/work/ps_wp3/results/objective2/dopant_shell/wp3/$d/ results/objective2/dopant_shell/wp3/$d/; done   # must print nothing
find results/objective2/dopant_shell/wp3 \( -name '*.out' -o -name '*.in' -o -name '*.out.try?' \) | head   # must print nothing
git add results/objective2/dopant_shell/wp3/{frames,raw,test_extra,chk,dataset}
```

Commit them, then do 3d (the record) on the copied `dataset_meta.json`. The blocks of 3a–3c below are the by-hand form,
kept as the record of what node_step34 ran.

### 3a. Pull and archive (by hand only; not with the node drivers)

```
dft pull wp3 <MAC_STAGE>/wp3; dft pull wp3x <MAC_STAGE>/wp3x; dft pull wp3chk <MAC_STAGE>/wp3chk
rsync -a dft:<NODE_WORK>/wp3_frames/ results/objective2/dopant_shell/wp3/frames/        # frames + frames_report.json
bash scripts/wp3_runbook/rb_archive.sh <MAC_STAGE>/wp3    results/objective2/dopant_shell/wp3/raw
bash scripts/wp3_runbook/rb_archive.sh <MAC_STAGE>/wp3x   results/objective2/dopant_shell/wp3/test_extra/raw
bash scripts/wp3_runbook/rb_archive.sh <MAC_STAGE>/wp3chk results/objective2/dopant_shell/wp3/chk/raw
find results/objective2/dopant_shell/wp3 \( -name '*.out' -o -name '*.in' -o -name '*.out.try?' \) | head   # must print nothing
x=$(mktemp -d) && tar xzf results/objective2/dopant_shell/wp1_production/v2prod_structures.tar.gz -C $x  # gives $x/v2prod
```

`rb_archive.sh` writes `<label>.in.gz`, `<label>.out.gz` and `<label>.out.tryN.gz`. It copies the empty
`<label>.gaveup` as is (scripts/33, 39 and 40 also accept `.gaveup.gz`), and refuses to overwrite. The
item-1′ outputs are archived but **not analysed** before step 6. Do not open them, or `test.xyz`.

### 3b. The test hosts

An item-1′ host with no converged frame is left out of `--test-hosts`. The helper below reads only
convergence status, no values:

```
TH=$(<PY> scripts/wp3_runbook/rb_test_hosts.py)        # e.g. "m30 m32 m04 m10 m14 m18 m27"
```

### 3c. scripts/33: the 1e command, once, without --allow-missing and without --no-chk-yet

```
<PY> scripts/33_finetune_dataset.py --dft results/objective2/dopant_shell \
    --frames ../bands $x/v2prod results/objective2/dopant_shell/wp3/frames \
    --out results/objective2/dopant_shell/wp3/dataset --test-hosts $TH --valid-hosts m21
```

- **If it stops.** Correct the archive (only to agree with m 1e) and run it again; a stop writes no dataset.
- **W < 60.** Only `dataset_meta.json` is written: a further amendment is needed before training.

### 3d. Record (item 7.3)

```
<PY> - <<'EOF'
import json; m = json.load(open("results/objective2/dopant_shell/wp3/dataset/dataset_meta.json"))
q = m["q1_check"]
print("n", m["n"], "| W", m["wp3"]["W"], "ok", m["wp3"]["ok"], "dropped", m["wp3"]["dropped"], "rejected", [r["label"] for r in m["wp3"]["rejected"]])
print("item-1' found", len(m["item1p"]["found"]), "missing", [(r["label"], r["reason"]) for r in m["item1p"]["missing"]])
print("basis", m["basis"], "| WP3 vacancy frames", m["wp3_vacancy_energy"])
print("(a)", q["a"]["value_meV"], q["a"]["pass"], q["a"]["failures"], "| (b)", {X: (q["b"][X]["frame"], q["b"][X]["value_meV"], q["b"][X]["pass"]) for X in ("Sr", "undoped")})
print("v (meV)", {v["frame"]: v["v_meV"] for v in q["v"]})
print("loss_weights", m["loss_weights"]); print("start_check_reference", m["start_check_reference"])
EOF
```

## Step 4: pre-flight, timing run, training with the start check (node)

With the node drivers, node_step34 ran 4a–5a and made `/data/work/wp3/ds` itself (see "Node drivers used for steps
2–4"). The blocks below record the by-hand form; do not run them then. In particular, never copy the dataset to
`<NODE_WORK>/ds` from the Mac while a training run uses it.

```
rsync -a results/objective2/dopant_shell/wp3/dataset/ dft:<NODE_WORK>/ds/       # from the Mac
# on the node:
DS=<NODE_WORK>/ds
WE=$(<PY> -c "import json; print(json.load(open('$DS/dataset_meta.json'))['loss_weights']['w_E'])")
B=$(<PY> -c "import json; print(json.load(open('$DS/dataset_meta.json'))['basis'])")
ARGS=(--name wp3 --seed 123 --device cpu --default_dtype float64 --foundation_model <FM> --multiheads_finetuning False
  --train_file $DS/train.xyz --valid_file $DS/valid.xyz --E0s $DS/E0s.json --energy_key REF_energy --forces_key REF_forces
  --loss weighted --energy_weight $WE --forces_weight 100 --optimizer adam --amsgrad --lr 0.005 --weight_decay 5e-7
  --clip_grad 10 --scheduler ReduceLROnPlateau --lr_factor 0.8 --scheduler_patience 50 --ema --ema_decay 0.99
  --batch_size 2 --valid_batch_size 2 --patience 2048 --eval_interval 1 --keep_checkpoints)
```

`ARGS` is the item-2 command without `--work_dir` and `--max_num_epochs`.

Rules for every run in this step:
- Paths are absolute.
- None of these is used: `--test_file`, `--test_dir`, `--valid_fraction`, `--pt_train_file`,
  `--force_mh_ft_lr`, `--swa`, `--restart_latest`, `--save_all_checkpoints`, LoRA or freezing.

### 4a. Pre-flight (a configuration check; nothing is trained)

```
mkdir <NODE_WORK>/preflight && <MTRAIN> "${ARGS[@]}" --max_num_epochs 100 --work_dir <NODE_WORK>/preflight --dry_run
<PY> scripts/wp3_runbook/rb_preflight.py <NODE_WORK>/preflight/logs/wp3_run-123.log $DS <FM> $WE      # every line PASS
```

The helper checks the nine log lines of item 2, and that no line contains "multiheads finetuning". It
compares the "Atomic Energies used" dict with `E0s.json` exactly. If a check fails, record the cause,
correct only towards amendment m, and repeat the pre-flight.

### 4b. Timing run (item 2, Threads)

```
for T in 8 16 32; do mkdir <NODE_WORK>/timing_$T
  ( time OMP_NUM_THREADS=$T <MTRAIN> "${ARGS[@]}" --max_num_epochs 2 --work_dir <NODE_WORK>/timing_$T ) 2>&1 | tail -3
done   # read the wall time only, then:
rm -rf <NODE_WORK>/timing_8 <NODE_WORK>/timing_16 <NODE_WORK>/timing_32
```

Choose `<T>` from the wall times: the fastest, and on equal wall times (whole seconds) the fewest threads.
The timing is all or nothing: `node_step34.sh` writes `timing.part` and renames it to `timing.txt` only once
all three runs have finished. A pass cut short (for example by a reclaim) is discarded, logged, and all
three are repeated.

### 4c. Training

`<RUN>` must be new and empty.

```
mkdir <RUN> && cd <RUN> && OMP_NUM_THREADS=<T> nohup <MTRAIN> "${ARGS[@]}" --max_num_epochs 100 --work_dir <RUN> > <RUN>.stdout 2>&1 &
echo $! > <RUN>.pid
```

The run is a single process; mace-torch 0.3.16 has no CPU data-parallel backend.

### 4d. Start check: as soon as the Initial record exists

```
<PY> scripts/wp3_runbook/rb_startcheck.py <RUN>/results/wp3_run-123_train.txt $B
```

The Initial record has `"mode": "eval", "epoch": null`. The check needs RMSE_F 79.819 ± 0.01 meV/Å and
RMSE_E_per_atom 0.3334 ± 0.001 meV/atom (0.3499 on the raw basis).

On a FAIL:
1. Stop the run with `kill $(cat <RUN>.pid)` (the exact PID).
2. Its outputs are not used. Record the cause and correct it (towards m only).
3. Start again in a new empty `<RUN>`. This is not the retry.

### 4e. Interruptions

A spot reclaim, node loss, OOM, wall time or any other abnormal end before `<RUN>/wp3.model` exists has
the same handling:
1. Discard the run unread.
2. List its cause, traceback and time.
3. Run the identical command from scratch in a new empty `<RUN>`.

The same cause twice in succession counts as deterministic: a technical failure (never a spot reclaim or
a node loss). Never use `--restart_latest`. `node_step34.sh` applies this rule as described under "Node
drivers used for steps 2–4": a new `run<n>` per restart, and `restarts.txt`.

## Step 5: technical-failure check; model note

### 5a. Technical-failure check

Use m21 only; no test host.

```
<PY> scripts/wp3_runbook/rb_techfail.py <RUN> $DS        # non-finite losses in the results file/log; wp3.model on the 31 m21 frames
```

A failure in any of the three item-2 ways (with deterministic abnormal ends judged from 4e) has one retry:
- record the cause;
- in a new empty `<RUN>`, run the identical command with `--lr 0.0025` instead of `--lr 0.005`;
- the pre-flight check then needs the lr argument: `rb_preflight.py ... $WE 0.0025`.

If the retry also fails, criterion 6 is "not met (no fine-tuned model)" and the Outcome is No improvement.
node_step34 cannot run the retry (it hard-codes `--lr 0.005`): run it by hand as Appendix §A.5 says, which also covers the retry after a deterministic abnormal end and interruptions of the retry.

### 5b. Model note

Commit it before any test-host prediction, and on its own.

```
sha256sum <RUN>/wp3.model                    # = <SHA>
git status --porcelain -- scripts/39_wp3_evaluate.py scripts/40_wp3b.py scripts/41_wp3_md.py   # must print nothing
git rev-parse HEAD                           # = <CN>
```

Write `results/objective2/dopant_shell/wp3/MODEL_NOTE_<date>.md`, dated, recording:
- `<SHA>` and `<CN>`, the commit of scripts 39, 40 and 41;
- the exact command and `<T>`;
- the mace, torch and e3nn versions, and the seed (123);
- every restart with its cause and time;
- the selected epoch, with its m21 loss, RMSE_E_per_atom and RMSE_F;
- the Initial values and the m21 host-wide energy offset.

Archive with the model: the command, logs, results file, versions, seed, thread count, restarts and
selected epoch. Copy `<RUN>` to `<MAC_STAGE>/run`. `wp3.model` is about 44 MB, so whether to commit it is
your decision; its sha256 is what identifies it. Commit the note.

Write the note with `rb_model_note.py` and commit it on its own, as Appendix §A.1–§A.3 says. That commit is `<CNOTE>`. Then step 6, then the node before step 7 (§A.4).

## Step 6: criterion 6 and adoption (a)–(c), once (Mac, repository root, at `<CNOTE>`)

Step 6 runs after the note commit `<CNOTE>` (Appendix §A.4.2). A scripts/39 run at `<CN>` can never be used for step 7.

```
git rev-parse HEAD                           # = <CNOTE>
sha256sum <MAC_STAGE>/run/wp3.model          # must be <SHA>
<PY> scripts/39_wp3_evaluate.py --model <MAC_STAGE>/run/wp3.model --model-sha256 <SHA> \
    --dataset results/objective2/dopant_shell/wp3/dataset --basis $(<PY> -c "import json; print(json.load(open('results/objective2/dopant_shell/wp3/dataset/dataset_meta.json'))['basis'])")
```

Run it without `--cache`. It writes `results/objective2/dopant_shell/wp3/wp3_eval.json`.

scripts/39, 40 and 41 pass the model path to MACECalculator as a one-element list, so mace-torch 0.3.16
does not expand it with `glob`.

Exit codes:

| code | meaning |
|---|---|
| 0 | done |
| 3 | sha mismatch, nothing evaluated |
| 4 | gate or 46-frame check failed |
| 5 | step-6 check failed before the model was loaded (test-frame inputs or outputs, `test.xyz` label set, `--basis`) |
| 6 | error after the gate |

On a failure (exit 4, 5 or 6):
1. Record the cause.
2. Commit any change to scripts/39; list its diff in the WP3 result.
3. Repeat the step-1 gate-only, then run step 6 again. This re-run is not a second evaluation.

## Step 7: WP3b (d) and MD (e)

Steps 7a–7d run on the node in `/data/work/ps_wp3` at `<C6>`, by `node_step7.sh` only (Appendix §B); the
analyses in 7e run on the Mac. The driver starts only after the note commit and step 6. 7a–7d below describe
what it runs; they are not commands to type. Their code blocks are kept as the record of the exact invocations
(run from `/data/work/ps_wp3`, each with `OMP_NUM_THREADS` and `MKL_NUM_THREADS` set to its thread count and
`OPENBLAS_NUM_THREADS=1`, except region and the chain). The model is `<RUN>/wp3.model` with `<SHA>`.

The driver runs each relaxation as its own `--cells <host>_<system>` invocation (the six unconstrained first,
the script's default 6 threads, one `--work`), and the 12 MD runs in the same 64-thread pool. It starts
`chain.sh wp3b` once every relaxation has its record or has no attempt left and no other QE process runs.
Reruns are resolved only through `/data/work/wp3/step7/cause.<label>.att<n>` (§B, "Resolving a STOP for one
run"). Never run `scripts/40 region`, `zeroshot` or `relax`, `scripts/41 run`, or `chain.sh wp3b` by hand on
the node. zeroshot, relax and scripts/41 run predict the m30/m32 test cells, and region fixes the cells they
read. At its first start the driver STOPs if any step-7 output exists (a region or zeroshot file among them),
and later a relaxation or MD output that it did not launch STOPs it (§B). The chain may run only when no MACE
work runs, and the driver starts it at that point.

### 7a. Region and zero-shot comparator

The driver runs region, then zeroshot (4 threads, never beside a QE process). Each must exit 0 (region: 6.0 Å;
81/83/81), or it STOPs.

```
<PY> scripts/40_wp3b.py region --out <NODE_WORK>/wp3b/wp3b_region.json
<PY> scripts/40_wp3b.py zeroshot --region <NODE_WORK>/wp3b/wp3b_region.json --out <NODE_WORK>/wp3b/wp3b_zeroshot.json
```

### 7b. Relaxations

One invocation per relaxation, all with ONE `--work`, `--unconstrained` for the six `wp3bu_` cells, and never
`--steps` (any value other than 10000 marks a smoke test):

```
<PY> scripts/40_wp3b.py relax --region <NODE_WORK>/wp3b/wp3b_region.json --model <RUN>/wp3.model --model-sha256 <SHA> \
    --work <NODE_WORK>/wp3b/relax --qe /data/jobs/wp3b [--unconstrained] [--rerun-cause <cause> --rerun-note <note>] \
    --cells <host>_<system>
```

The first invocation writes `wp2e_minimum.json` before its first relaxation, and parallel writers of that file
can corrupt it. So the driver runs it alone until that file exists and has passed its check. After that the
other invocations run in parallel, because each cell has a lock.

### 7c. QE single points

The driver starts the chain once every relaxation has its record or has no attempt left, so there is one input
below `/data/jobs/wp3b` per record (§B). It first waits out any queue started outside chain.sh:

```
flock /tmp/qe_queue_wp3b.lock true; /data/setup/chain.sh wp3b
```

It is never started earlier: the queue ends ("all done") as soon as it finds no pending input. A job without
JOB DONE gets one resubmission (queue). An unconverged SCF of a `wp3b_` cell is a Fail of (d); an unconverged
`wp3bu_` job is reported as such. Neither is re-run.

### 7d. MD stability (e)

There are 12 runs, one per invocation, for the hosts m30 and m32, the systems undoped, GA and Sr, and 300 and
450 K. They run in the same 64-thread pool as the relaxations, never alongside the 64-rank QE chain, and never
with `--steps` or `--report-every`:

```
<PY> scripts/41_wp3_md.py run --model <RUN>/wp3.model --model-sha256 <SHA> --host <host> --system <system> --T <300|450> \
    --work <NODE_WORK>/wp3md --threads 8 [--rerun-cause <cause> --rerun-note <note>]
```

Reruns:
- **Interrupted relaxation or MD run.** The driver reruns it with the identical command and the
  `--rerun-cause` that the evidence gives, at most twice (3 attempts). The `--threads` value stays the same,
  and the scripts move partial outputs aside unread. Where the evidence does not decide, the driver STOPs, and
  the operator writes the cause word to `/data/work/wp3/step7/cause.<label>.att<n>` (§B). Never give
  `--rerun-cause` by hand.
- **Ended with an exception.** A relaxation that ended with an exception has no rerun. An MD run that
  ended with an exception accepts only `oom`, and only with a memory error in its traceback.

### 7e. Pull, archive, analyse (Mac, at `<C6>` or later; scripts/41 analyse needs the git history)

```
dft pull wp3b <MAC_STAGE>/wp3b
rsync -a dft:<NODE_WORK>/wp3b/ <MAC_STAGE>/wp3b_work/; rsync -a dft:<NODE_WORK>/wp3md/ <MAC_STAGE>/wp3md/
bash scripts/wp3_runbook/rb_archive.sh <MAC_STAGE>/wp3b results/objective2/dopant_shell/wp3/wp3b/raw
<PY> scripts/40_wp3b.py analyse --region <MAC_STAGE>/wp3b_work/wp3b_region.json --work <MAC_STAGE>/wp3b_work/relax \
    --dft results/objective2/dopant_shell/wp3/wp3b/raw --model-sha256 <SHA> --zeroshot <MAC_STAGE>/wp3b_work/wp3b_zeroshot.json \
    --out results/objective2/dopant_shell/wp3/wp3b_result.json
<PY> scripts/41_wp3_md.py analyse --work <MAC_STAGE>/wp3md --model-sha256 <SHA> --commit <CN> \
    --out results/objective2/dopant_shell/wp3/wp3md_result.json
```

The results carry `pass` true, false or null, and `model_sha256`:
- scripts/40 writes `item` "PLAN amendment m item 4 (d), WP3b";
- scripts/41 writes `check` "WP3 adoption (e): MD stability".

scripts/39 reads exactly these keys. (d) and (e) are run and reported whatever (a)–(c) gave. Archive the
two work directories as tarballs if they are kept under `results/` (see the Archive layout). Also see Appendix §C.

## Step 8: Outcome and WP3 result (Mac, at `<C6>` or later)

```
<PY> scripts/39_wp3_evaluate.py --outcome-only results/objective2/dopant_shell/wp3/wp3_eval.json \
    --wp3b-json results/objective2/dopant_shell/wp3/wp3b_result.json --md-json results/objective2/dopant_shell/wp3/wp3md_result.json
```

This writes `results/objective2/dopant_shell/wp3/wp3_outcome.json`. It loads no model and reads no QE
file, so it is not a second evaluation.

Then write the WP3 result with every verdict, and add the dated roadmap update. State in the result these
readings, which every script discloses:
1. **float64 assertion order** (scripts/39, `float64_assertion`).
2. **scripts/40 FIRE reading** (`protocol.reading`) and step-cap rule.
3. **scripts/40 surface sets and basin-measure reading.**
4. **QE resubmission times from file mtimes** (scripts/40 `time_source`).
5. **scripts/33 fail-closed rules** (`dataset_meta.json` `script_rules`, among them the q = +1 check
   stop and the md450/md300 both-rejected rule).
6. **scripts/41 errata.** The shortest training I–I is 4.0346 Å, not 4.04 Å. 'A–A ≥ 6.28 Å' does not
   hold for C/Cs; check 3 is unaffected.
7. **Item-1′ and `chk_` input text.** It differs from the WP2b inputs only by an explicit
   `tot_charge = 0.0` or `1.0` line and the `pseudo_dir` spacing.
8. **Item-1′ unconverged-SCF re-runs** done under 2e.

## Item 6 (only if the Outcome is Validated; reported only)

Run on the node, at `<C6>`:

```
for M in 30 21; do <PY> scripts/29_dopant_shell_scan.py --member $M --model <RUN>/wp3.model --model-sha256 <SHA> \
    --fmax-stages 0.02 0.01 --steps 10000 --out <NODE_WORK>/wp1ft; done          # references afresh (no --ref-from)
<PY> scripts/34_dopant_shell_analysis.py --mode map --fmax 0.01 --inp <NODE_WORK>/wp1ft --out <NODE_WORK>/wp1ft_map
```

Label every row "fine-tuned-MACE level; whole-cell relaxations, geometry not validated (item 4, Scope)".
The sign rule of criterion 2 is 2 of 2. If the outcome is not Validated, item 6 is not run, and that is
recorded as a deviation (item 6).

## Do not

- Do not edit PLAN.md; amendment m is not edited.
- Do not run scripts/33 again with `--dft results/objective2/dopant_shell` after step 7 has archived
  `wp3b_` outputs there. It stops on their labels (m 1e: only the 28 exclusions and `chk_*` are
  tolerated); this is by design.
- Do not use `--cache`, a stand-in model, `--no-chk-yet` or `--allow-missing` in any real step.
- Do not run any scripts/29, 39, 40 or 41 command with the zero-shot foundation file as `--model`
  outside tests. They label it a stand-in, and scripts/39 refuses it with an `--out` inside `results/`.
- Do not train on, select with, or re-evaluate any frame of m30, m32, m04, m10, m14, m18 or m27 after
  step 6. The test hosts are used up.
- Do not commit anything but the model note in `<CNOTE>`, and do not run step 6 before the checks of Appendix
  §A.3 pass.
- Do not start node_step34.sh from its technical-failure STOP, or from its second-abnormal-end STOP once the
  two causes are judged the same, until STEP34_DONE (Appendix §A.5). Never remove STEP34_STOPPED by hand.
- Do not run `scripts/40 region`, `zeroshot` or `relax`, `scripts/41 run`, or `chain.sh wp3b` by hand on the
  node (Appendix §B).

## How this runbook was tested (2026-10-28, laptop, SYNTHETIC; no QE, MD, relaxation, NEB or training)

Scratch directory: a temporary directory on the laptop (`m_impl/integration/`), not archived.

1. **scripts/35.** The unmodified scripts/35 `main()` ran with mace_mp stubbed to a zero-force
   calculator and Langevin to a no-op, so no MACE evaluation and no MD step took place
   (`tools/run35_stub.py`). It produced 96 frames, `frames_report.json` and 96 QE inputs.
2. **Inputs.** Steps 2b and 2c (`tools/make_inputs.sh`) produced the 50 item-1′ inputs and the 8 `chk_`
   inputs. `rb_verify_inputs.py` passed on them. It also caught an input written from the wrong image
   and a `chk_` input without `--charge 1`.
3. **Synthetic outputs** (`tools/build_dft.py`). These are copies of archived outputs with the header
   geometry rewritten, not DFT. They were archived in the layout above, and `rb_archive.sh` reproduced
   that layout from a mock pulled campaign.
4. **scripts/33.** It ran on this archive with the 1e command form. Zero-shot values came from a cache;
   the WP3 frames got their source frame's cached values (a stub).
   - Basis Eprime with WP3 vacancy frames at weight 0 (the chosen check values: (a) +2, (b) Sr +15,
     undoped +1 meV).
   - 202/31/57 frames, n_E 130.
   - The chk geometry was checked on outputs and inputs.
   - Start-check values 0.3334195 meV/atom and 79.81902 meV/Å.
5. **mace-torch loaders** (no training).
   - The 0.3.16 loader (`load_from_xyz` with the item-2 keys) gave energy weight 0 on exactly the 72
     `energy_weight_zero` frames and force weight 1 on all frames.
   - The `--E0s` loader read `E0s.json` as {1, 6, 7, 38, 53, 55, 82}.
6. **scripts/39 stand-in run.** Full mode with the foundation file as a labelled stand-in, on that
   archive and dataset:
   - the `test.xyz` label set was equal (57);
   - 96 test inputs were checked;
   - the basis was equal;
   - `--outcome-only` mapped the scripts/40 and scripts/41 result files ((d) pass/fail; (e) stand-in →
     cannot be evaluated).
7. **Training-step checkers.** `rb_preflight.py` passed on a 0.3.16 dry-run log and flagged the multihead
   one. `rb_startcheck.py` parsed a results file. `rb_techfail.py` flagged a NaN loss.
8. **Real gate.** `scripts/39 --gate-only` ran for real from the repository root (no cache, 96 zero-shot
   single points): exit 0, GATE PASS.

## Appendix: helper scripts

The helpers are committed in `scripts/wp3_runbook/` (`rb_verify_inputs.py`, `rb_archive.sh`,
`rb_test_hosts.py`, `rb_preflight.py`, `rb_startcheck.py`, `rb_techfail.py`). They read the repository's own
scripts by relative path, so run them from the repository root. They only read files; none runs QE, MD, a
relaxation or training. They are run-control checks of amendment m items 1′, 1e and 2, not analysis code:
no number in the WP3 result is computed by them.

Two more kinds of file are in that folder (2026-10-29):
- `rb_model_note.py` writes the step-5b model note (Appendix "the 5a retry and steps 5b–7", §A). With `--m21-offset compute` it runs 31 MACE single points on the m21 frames of `valid.xyz`, and the m21 host-wide energy offset it computes is reported in the note (item 2 'Reporting'). It reads no test-host data.
- `node_step2.sh`, `node_step34.sh`, `node_step7.sh` and `node_relaunch.sh` are the node drivers ("Node drivers used for steps 2–4" and Appendix "the 5a retry and steps 5b–7", §B). They run the committed scripts, the QE queue and the training, and compute no reported number themselves.

## Appendix: the 5a retry and steps 5b–7 with the node drivers (2026-10-29)

This section is the procedure for the by-hand item-2 retry of 5a, the note tool `scripts/wp3_runbook/rb_model_note.py`, step 6, and the step-7 driver `scripts/wp3_runbook/node_step7.sh` (with the updated `node_relaunch.sh`). The drivers' and tools' messages cite it as "WP3_RUNBOOK appendix A.4", "A.5" and "B": A.4 and A.5 are items 4 and 5 of §A below, and B is §B. In the main text, "Appendix §A", "§B" and "§C" also mean this appendix. The design review, the decisions and the test record are in `scripts/wp3_runbook/review_2026-10-29/NOTES.md`.

**The order of work is now enforced on the node** (PLAN amendment m item 7: 5 note, 6 `scripts/39` once, 7 WP3b and
(e)). node_step7.sh starts step 7 only when both commits are on record: the note commit `<CNOTE>` (NOTE_COMMITTED) and
the step-6 commit `<C6>` that adds `wp3_eval.json` (STEP6_DONE). The node checkout must be at `<C6>`.
`node_relaunch.sh` also requires both markers.

### A. 5b with `rb_model_note.py` (Mac, repository root, at `<CN>`), step 6 (Mac, at `<CNOTE>`), the node before step 7 (A.4.3–A.4.4, before and after updating to `<C6>`), and the item-2 retry by hand (A.5, node)

1. Copy from the node to `<MAC_STAGE>`:
   - the selected `<RUN>` as `<MAC_STAGE>/run`, with `logs/`, `results/` and `checkpoints/`. Leave `checkpoints/`
     out entirely rather than copying part of it.
   - next to it: `train_command.txt`, `timing.txt`, `step34.log`, `restarts.txt` and `item1p_rerun.list` (each only
     if it exists), and `logs/techfail.txt`;
   - after the item-2 retry (A.5), also `train_command_retry.txt` and the failed run's evidence:
     - after a technical failure: `logs/techfail_run<k>.txt` (`run<k>` is the run that failed, A.5);
     - after a deterministic abnormal end: `run<j>.end` and `run<k>.end`, the two runs that ended abnormally;
     - `retry_causes_differ.txt`, if the retry itself ended abnormally more than once (A.5);
   - a `versions.txt` made on the node:

   ```
   <PY> -c "import mace, torch, e3nn; print('mace', mace.__version__); print('torch', torch.__version__); print('e3nn', e3nn.__version__)" > <NODE_WORK>/versions.txt
   ```

2. Write the note:

   ```
   <PY> scripts/wp3_runbook/rb_model_note.py --run <MAC_STAGE>/run --node-files <MAC_STAGE> \
       --dataset results/objective2/dopant_shell/wp3/dataset \
       --out results/objective2/dopant_shell/wp3/MODEL_NOTE_<YYYY-MM-DD>.md --date <YYYY-MM-DD> \
       --m21-offset compute --threads 8
   ```

   - **Exit 0:** the note is complete (stdout: `note -> <out>`). Only this note may be committed.
   - **Exit 2:** the note is a DRAFT (stdout: `DRAFT -> <out> (missing: ...)`); its banner says what is missing or
     needs explaining. Never commit a DRAFT. A DRAFT has no machine-readable lines, only `draft-` copies of them, so
     node_step7.sh refuses it. A DRAFT results when:
     - the selected model's m21 offset was not computed;
     - the torch or e3nn version is missing;
     - no passed 5a was found: neither a `logs/techfail.txt` whose rb_techfail.py lines show the pass for the
       selected run (library warnings before or after them do not count), nor a `5a: no technical failure` line
       after the run's training line in `step34.log`;
     - the single-point RMSE_E_per_atom differs from the selected epoch's record by more than 0.001 meV/atom. That
       points to a wrong model or wrong frames: find out why.

     Fix the cause and run the tool again with `--force`, which overwrites the uncommitted DRAFT. Without
     `--force` an existing `--out` is refused (exit 1). A DRAFT that was committed is never changed: write a new
     note under a new date (A.3).
   - **Exit 2 without a `DRAFT ->` line:** an argparse usage error (an unknown option, or a bad value of
     `--m21-offset` or `--threads`), with a `usage:` message. Nothing is written.
   - **Exit 1:** refused, with the reason (`REFUSED: ...` on stderr); nothing is written. It refuses when:
     - `--run` or `--out` is missing, `--out` is not named `MODEL_NOTE_<YYYY-MM-DD>.md` for `--date <YYYY-MM-DD>`,
       or `--out` exists and `--force` is not given;
     - the Initial record fails the start check (item 2: a void run is never evaluated);
     - the dataset basis is not `Eprime` or `raw`;
     - the command uses an excluded option (`--swa*`, `--lora*`, `--freeze*`, a test set, `--restart_latest`, ...);
     - the run's history shows more than one retry, or a retry without its evidence (A.5);
     - any of the checks listed below fails.
   - `--m21-offset compute` runs 31 MACE single points (float64, cpu, head Default, sha256 checked) on the m21 frames
     of `valid.xyz`. Only m21 data is read. The tool refuses a `valid.xyz` with any other host, opens no `test.xyz`,
     and refuses a training log that holds a test-set error table.
   - The note records:
     - `<SHA>` and `<CN>` (the commit of scripts 39/40/41);
     - the exact command and `<T>`;
     - the versions and the seed;
     - every restart and item-1′ re-run;
     - the item-2 retry, if there was one, with its cause or causes;
     - the selected epoch with its m21 loss, RMSE_E_per_atom and RMSE_F, the Initial values, and the m21 host-wide
       energy offset.
   - The offset is the mean of E_model − REF_energy over the 31 m21 frames. Amendment m names the offset without
     defining it, so this is the note's reading; state it in the WP3 result.
   - The tool also refuses if any of these disagree:
     - the log's "Loaded Stage one model from epoch e";
     - the highest checkpoint;
     - the lowest-loss epoch under mace-torch 0.3.16's strict-improvement rule.
   - It also refuses on any of these:
     - an uncommitted change in scripts 39/40/41 or a helper they load;
     - a change to them since the commit node_step34 trained at;
     - a `restarts.txt` or `item1p_rerun.list` that disagrees with `step34.log`.
   - Do not edit the four machine-readable lines (`model_sha256:`, `scripts_commit:`, `run:`,
     `note_status: complete`). node_step7.sh reads them. It also refuses a note with a DRAFT banner, a `**Check:**`
     line or no computed offset for the selected model.
3. Commit the note **on its own**. Then check that `git show --stat HEAD` lists only
   `results/objective2/dopant_shell/wp3/MODEL_NOTE_<date>.md`. This commit is `<CNOTE>`. The note's
   `scripts_commit` is `<CN>`, normally the parent of `<CNOTE>`, and scripts 39, 40 and 41 are identical in both.

   A committed note is never changed: node_step7.sh accepts only a `<CNOTE>` that adds a new note. If a DRAFT (or
   any note node_step7 refuses) was committed, write a NEW note under a new date (a new
   `MODEL_NOTE_<YYYY-MM-DD>.md`, rb_model_note.py exit 0; the committed name cannot be reused), add it in a commit
   of its own, which is then `<CNOTE>`, and list the committed DRAFT as a deviation in the WP3 result. `--date`
   defaults to today (UTC). If the DRAFT carries today's date, give the next day's date with `--date` and keep the
   real date of writing in the commit message.
4. **Step 6, then the node.**
   1. **While the node waits for 5b and step 6.** After STEP34_DONE the node has nothing to run until step 7.
      node_step34 removed `/data/KEEP_ALIVE` when it wrote STEP34_DONE (and at each STOP, unless a training process
      was still alive), so the idle self-stop (`/usr/local/bin/idle_shutdown.sh`) counts from then. If the node is
      to stay up, `touch /data/KEEP_ALIVE`. Otherwise stop it (`python3 /data/setup/ecs_selfstop.py stop`, or from
      the console) and start it again when it is needed (A.1, A.4.3): everything on `/data` is kept. A long wait
      is cheaper with the node stopped.
   2. **Step 6 on the Mac** (runbook step 6, once), with HEAD = `<CNOTE>`. Run `git rev-parse HEAD` first; it must
      print `<CNOTE>`. scripts 39, 40 and 41 there are those of `<CN>`.
      - scripts/39 records HEAD as `git.head`. node_step7 refuses a `wp3_eval.json` whose `git.head` is not `<CNOTE>`
        or a later commit at which only `results/` and `scripts/39` differ from `<CNOTE>`.
      - So a scripts/39 run at `<CN>` (`git checkout <CN>` to be "at `<CN>`"), or at any commit other than `<CNOTE>`
        or a later commit of the kind just described, can never be used for step 7. scripts/39 runs once, so no
        second evaluation can replace it.

      `scripts/39` writes `results/objective2/dopant_shell/wp3/wp3_eval.json` only on exit 0. On exit 4, 5 or 6 the
      runbook allows the following, and the re-run is not a second evaluation:
      - record the cause (under `results/`);
      - commit a `scripts/39` fix;
      - repeat the step-1 gate-only;
      - run step 6 again, at the new HEAD.

      Then commit `wp3_eval.json`, with any step-6 records under `results/`, in **one** commit. This commit is `<C6>`.
      No other commit after `<CNOTE>` may add, change or remove `wp3_eval.json`: an add, a delete and a re-add would
      hide a second evaluation, and node_step7 STOPs on it. Check:

      ```
      git diff --no-renames --name-only <CNOTE> <C6> | grep -v '^results/' | grep -vxF scripts/39_wp3_evaluate.py    # must print nothing
      git diff --no-renames --name-only <CNOTE> <C6> | grep -E 'MODEL_NOTE_|^results/(fa_host/|objective2/dopant_shell/(PLAN\.md$|wp2b/|wp2e/))'    # must print nothing
      git log --full-history --format=%H <CNOTE>..<C6> -- results/objective2/dopant_shell/wp3/wp3_eval.json    # one line: <C6>
      ```

      The second line covers the paths under `results/` that may not change either: PLAN.md, any model note, and the
      repository data step 7 reads (`results/fa_host`, `wp2b`, `wp2e`). `--full-history` is what node_step7 uses: without
      it, git can hide an add and delete of `wp3_eval.json` on a merged branch.

      node_step7.sh STOPs on anything else. It logs two kinds of WARN:
      - one naming any `scripts/39` commit between the two;
      - one naming every changed path other than `wp3_eval.json` (a change to WP3_RUNBOOK.md shows here).

      A change to `results/objective2/dopant_shell/PLAN.md` between the two STOPs: the pre-registration does not
      change between the committed note and step 7.

      List both, and the scripts/39 diff, in the WP3 result.
   3. **On the node, before updating the checkout: node_step34's archive copies.** node_step34 ran 3a–3c in the
      node checkout. So `results/objective2/dopant_shell/wp3/{frames,raw,test_extra,chk,dataset}` exist there,
      untracked, and the same files are committed in `<C6>`. Git refuses to update the checkout over them, and
      node_step7 STOPs on a checkout that is not clean.

      Nothing on the node reads these copies after STEP34_DONE:
      - training, the pre-flight and 5a (node_step34's, and the by-hand retry's) use `/data/work/wp3/ds`, the copy
        that node_step34 makes before training;
      - step 7 reads neither (scripts/40 and 41 read `../bands`, `results/fa_host`, and `wp2b`/`wp2e` under
        `results/objective2/dopant_shell`).

      So they are compared with the committed files and moved out. The committed archive must be the node's files as
      node_step34 wrote them, copied byte for byte (rsync of the node checkout's directories), not re-made on the Mac
      with `rb_archive.sh`. gzip stores each source file's name and mtime, so a re-made `.gz` differs in its bytes even
      when its content is the same.

      First fetch `<C6>` into the node repository without updating the checkout. The checkout is on branch
      `feat/dopant-shell-dft-validation`, and its remote `origin` is the bundle file `/data/work/ps_wp3.bundle`:

      ```
      git bundle create <MAC_STAGE>/ps_wp3.bundle feat/dopant-shell-dft-validation      # on the Mac, with <C6> on the branch
      rsync -a <MAC_STAGE>/ps_wp3.bundle dft:/data/work/ps_wp3.bundle.new && ssh dft mv /data/work/ps_wp3.bundle.new /data/work/ps_wp3.bundle
      git -C /data/work/ps_wp3 bundle verify /data/work/ps_wp3.bundle && git -C /data/work/ps_wp3 fetch origin   # on the node
      ```

      Then run, in bash, on the node:

      ```
      cd /data/work/ps_wp3 && C=<C6>
      git status --porcelain --untracked-files=no
      git ls-files --others --exclude-standard | grep -v '^results/objective2/dopant_shell/wp3/\(frames\|raw\|test_extra\|chk\|dataset\)/'
      git ls-files --others --exclude-standard -- results/objective2/dopant_shell/wp3 | while IFS= read -r f; do n=$(sha256sum < "$f" | cut -c1-64); if git cat-file -e "$C:$f" 2>/dev/null; then c=$(git show "$C:$f" | sha256sum | cut -c1-64); else c=absent; fi; [ "$n" = "$c" ] && echo "same $f" || echo "DIFF $f node $n commit $c"; done > /data/work/wp3/archive_node_copy.cmp; grep -vc '^same ' /data/work/wp3/archive_node_copy.cmp
      grep '^DIFF .*\.gz node ' /data/work/wp3/archive_node_copy.cmp | while read -r _ f _; do [ "$(gzip -dc "$f" | sha256sum | cut -c1-64)" = "$(git show "$C:$f" 2>/dev/null | gzip -dc 2>/dev/null | sha256sum | cut -c1-64)" ] && echo "same content $f" || echo "DIFF content $f"; done
      for f in /data/work/wp3/ds/*; do g=results/objective2/dopant_shell/wp3/dataset/${f##*/}; [ "$(sha256sum < "$f" | cut -c1-64)" = "$(git show "$C:$g" 2>/dev/null | sha256sum | cut -c1-64)" ] && echo "same ds/${f##*/}" || echo "DIFF ds/${f##*/}"; done
      git ls-tree -r --name-only $C -- results/objective2/dopant_shell/wp3/{frames,raw,test_extra,chk,dataset} | while IFS= read -r f; do [ -e "$f" ] || echo "only in $C: $f"; done
      git ls-files -- results/objective2/dopant_shell/wp3/{frames,raw,test_extra,chk,dataset}
      mkdir /data/work/wp3/archive_node_copy && mv results/objective2/dopant_shell/wp3/{frames,raw,test_extra,chk,dataset} /data/work/wp3/archive_node_copy/
      git status --porcelain
      ```

      What each line must print:
      - Lines 2, 3, 7 and 8 must print nothing:
        - line 2: no tracked file is modified;
        - line 3: no other untracked file;
        - line 7: every committed archive file has a node copy;
        - line 8: those directories hold no tracked file at the current HEAD, so the `mv` removes nothing tracked.
      - Line 4 compares every node copy with `<C6>` by sha256. It prints the number of copies that are not
        byte-identical, which should be `0`. The per-file verdicts are in `/data/work/wp3/archive_node_copy.cmp`.
      - Line 5 matters only if line 4 is not `0`. For each `.gz` that differs, it compares the decompressed contents:
        - `same content <file>`: the committed `.gz` was re-gzipped from the same file. Note it in the WP3 result
          and go on.
        - `DIFF content <file>`: stop.
        - If line 4's count is larger than the number of `same content` lines, a file that is not a `.gz` differs:
          stop.
      - Line 6 must print `same ds/<file>` for each dataset file. The committed dataset (which the note tool read)
        must be the one training used.
      - The last line, after the `mv`, must print nothing.

      On any other `DIFF`, any other output, or an `only in` line, stop and find out why before going on. Keep
      `archive_node_copy/` and its `.cmp` file until the WP3 result is written.

      Then update the checkout: `git -C /data/work/ps_wp3 merge --ff-only <C6>`. Check two things:
      - `git -C /data/work/ps_wp3 rev-parse HEAD` prints `<C6>`;
      - `git status --porcelain` prints nothing.

      Only then:

      ```
      echo <CNOTE> > /data/work/wp3/NOTE_COMMITTED.new && mv /data/work/wp3/NOTE_COMMITTED.new /data/work/wp3/NOTE_COMMITTED
      echo <C6> > /data/work/wp3/STEP6_DONE.new && mv /data/work/wp3/STEP6_DONE.new /data/work/wp3/STEP6_DONE
      ```

      STEP6_DONE must hold exactly one line, the full commit `<C6>`.
   4. **Start step 7** (§B). Once `step7.log` shows `preconditions PASS`, run `rm -f /data/KEEP_ALIVE`. No phase of
      step 7 is idle, and after STEP7_DONE or a STOP the idle self-stop should stop the node.

   Nothing on the node predicts a test host before both markers exist. That includes the 7a zeroshot, which runs
   MACE-MP-0 on the m30 cells. Never run `scripts/40 region`, `zeroshot` or `relax`, or `scripts/41 run`, by hand on
   the node: the driver runs them, and all but region predict the m30/m32 test cells. Nor run `chain.sh wp3b` by
   hand: the driver starts it once no MACE work runs. The 7e analyses on the Mac (`scripts/40 analyse`,
   `scripts/41 analyse`) are required. At its first start the driver adopts nothing it did not start: it STOPs if
   any step-7 output already exists. Later, a relaxation or MD output made outside the driver STOPs; it is adopted
   only on the operator's `accept` (§B), if it was made at `<C6>` by the identical command (the driver checks its
   record and commit).
5. **The item-2 retry (runbook 5a), by hand.** node_step34 cannot run it, because it hard-codes `--lr 0.005`. It
   STOPs, without writing STEP34_DONE, at both item-2 failures it can see:
   - **a technical failure from 5a:** `STOP: technical failure: ...`, after the run's `4: training finished in`
     line;
   - **a deterministic abnormal end:** the second `[abnormal end]`, logged as
     `STOP: run<k>: second abnormal end (<run<k>'s cause>; earlier: <restarts.txt line>)`. node_step34 stops at any
     second abnormal end, so a human compares the two causes: `<NODE_WORK>/run<k>.end`, and the earlier cause, which
     is the restarts.txt line that the STOP line quotes after `earlier:` (and `run<j>.end`). Both tools take the first
     cause of the pair from that quote, never from a later abnormal end of the retry itself.
     - The same cause twice in succession (the same exception, or OOM or wall time again) is a technical failure
       (item 2 'Deterministic causes'). The retry follows.
     - Different causes are not a technical failure. Relaunch node_step34 with `PREV_CAUSE='<cause> <UTC time>'`
       (command below): that is a restart, logged as `run<k> discarded unread [operator] ...`, and no retry.

   In this item, `run<k>` is the run that failed (the finished run that failed 5a, or the run of the second abnormal
   end), `run<j>` the run of the first abnormal end, `run<m>` the retry run (`run<m+1>` its rerun), and `run<a>` and
   `run<b>` two successive abnormal ends of the retry.

   **From node_step34's `STOP: technical failure`, or from its `second abnormal end` STOP once two reviewers have
   judged the two causes the same, until STEP34_DONE, never start node_step34.sh** (`/data/work/wp3_step34.sh`).
   The retry is then decided. node_step34 hard-codes `--lr 0.005`. Started during or after the retry, it would:
   - remove STEP34_STOPPED and, when it stops, KEEP_ALIVE;
   - copy `/data/work/wp3/ds` again under the running retry;
   - discard the retry run and train `--lr 0.005` in its place, outside the one-retry protocol.

   After any other node_step34 STOP (for example a pre-flight FAIL, a start-check FAIL, a second abnormal end whose
   causes differ, or a run that ended while no driver watched it), correct the cause (towards m only) and start
   node_step34 by hand, as its STOP line says, with `PREV_CAUSE` where it asks for one. That is not the retry. The
   exceptions are the `has wp3.model` and `technical-failure CHECK ERROR` STOPs: finish those by hand as the main
   text's "Driver killed while training runs" says, without starting node_step34.
   `wp3_relaunch.sh` starts nothing while STEP34_STOPPED exists, so start node_step34 directly, as ericdft, in the
   form the runbook uses for the other drivers:

   ```
   setsid nohup bash /data/work/wp3_step34.sh > /data/work/wp3/driver34.out 2>&1 < /dev/null &
   PREV_CAUSE='<cause> <UTC time>' setsid nohup bash /data/work/wp3_step34.sh > /data/work/wp3/driver34.out 2>&1 < /dev/null &   # where the STOP asks for PREV_CAUSE
   ```

   node_step34 removes STEP34_STOPPED itself when it starts; never remove it by hand. After a reclaim during the
   retry, do the interruption steps below ("A reclaim, or any other interruption, during the retry") by hand.
   `wp3_relaunch.sh` only refuses then: it starts nothing while STEP34_STOPPED exists, nor, in the committed version,
   while `train_command_retry.txt` exists without STEP34_DONE. The main text's direct relaunch of node_step34
   ("After a reclaim") does not apply.

   Before `touch <NODE_WORK>/STEP34_DONE` (sub-step 7 below), and so before the model note (5b, §A.2), two
   reviewers check every hand-made line below against the run's own files; if the retry fails, they check them
   before the WP3 result. After the note commit, an error in these lines can no longer be corrected in the note.

   0. Install the committed `node_relaunch.sh` as `/data/work/wp3_relaunch.sh` (the version with the
      `train_command_retry.txt` guard), from any commit fetched into the node repository that holds it (§A.4.3 shows
      the fetch; the checkout is not updated for this): `git -C /data/work/ps_wp3 show
      <commit>:scripts/wp3_runbook/node_relaunch.sh > /data/work/wp3_relaunch.sh.new`, check its sha256, then `mv` it
      over `/data/work/wp3_relaunch.sh`.
   1. Keep the failed run's evidence:
      - after a technical failure: `mv <NODE_WORK>/logs/techfail.txt <NODE_WORK>/logs/techfail_run<k>.txt`;
      - after a deterministic abnormal end: leave `<NODE_WORK>/run<j>.end` and `run<k>.end` in place, and do not add
        `run<k>` to `restarts.txt` (it is not a restart).
   2. Run `touch /data/KEEP_ALIVE`, and keep the file for the whole retry training (13–25 h). node_step34's STOP removed
      it, and without it the idle self-stop powers the node off. It is on `/data`, so it survives a reclaim.
   3. Write the retry's exact command. It is `train_command.txt` with `--lr 0.005` replaced by `--lr 0.0025`, and
      nothing else changed:
      `sed 's/--lr 0\.005 /--lr 0.0025 /' <NODE_WORK>/train_command.txt > <NODE_WORK>/train_command_retry.txt`.
   4. **Pre-flight (4a) with the retry command,** as a new `--dry_run` in a new, empty directory. node_step34's
      `<NODE_WORK>/preflight` holds the `--lr 0.005` dry run, which fails the 0.0025 check. The dataset is always
      `/data/work/wp3/ds`, never the checkout's copy. The command line has no quoted arguments, because node_step34
      writes it with `${ARGS[*]}`, so `$c` may be expanded unquoted:

      ```
      cd /data/work/ps_wp3 && P=/data/work/wp3/preflight_retry && mkdir $P
      c=$(sed "s|--work_dir <run>\$|--work_dir $P --dry_run|" /data/work/wp3/train_command_retry.txt); $c > $P.stdout 2>&1
      WE=$(<PY> -c "import json; print(json.load(open('/data/work/wp3/ds/dataset_meta.json'))['loss_weights']['w_E'])")
      <PY> scripts/wp3_runbook/rb_preflight.py $P/logs/wp3_run-123.log /data/work/wp3/ds <FM> $WE 0.0025 > /data/work/wp3/logs/preflight_retry.txt
      ```

      Every line of `logs/preflight_retry.txt` must be PASS. That includes `Learning rate: 0.0025, weight decay: 5e-07`.
   5. Run the retry command with `OMP_NUM_THREADS=<T>` (`<T>` from timing.txt, as node_step34 chose it) in a new,
      empty `<NODE_WORK>/run<m>` (the next free number): `--work_dir <run>` becomes `--work_dir <NODE_WORK>/run<m>`.
      Its `4c` line must say `threads <T>`; both tools check this for the selected run. Start it detached, as
      node_step34 does, so that it survives the end of the ssh session (an ssh logout would otherwise end it with
      SIGHUP: an avoidable abnormal end). Save the block as a file and run it with `bash <file>`. A non-interactive
      bash has no job control, so `setsid` does not fork and `$!` is the training pid:

      ```
      W=/data/work/wp3; cd /data/work/ps_wp3
      n=1; while [ -e $W/run$n ]; do n=$((n+1)); done; RUN=$W/run$n
      T=$(sort -k2,2n -k1,1n $W/timing.txt | head -1 | cut -d' ' -f1)
      c=$(sed "s|--work_dir <run>\$|--work_dir $RUN|" $W/train_command_retry.txt)
      echo "[$(date -u +%FT%TZ)] start; repo $(git rev-parse --short HEAD) (5a retry with --lr 0.0025, run by hand)" >> $W/step34.log
      date +%s > $RUN.start; mkdir $RUN; cd $RUN
      OMP_NUM_THREADS=$T setsid nohup $c > $RUN.stdout 2>&1 < /dev/null &
      pid=$!; echo $pid > $RUN.pid; cd /data/work/ps_wp3
      echo "[$(date -u +%FT%TZ)] 4c: training started, pid $pid, threads $T, run $RUN" >> $W/step34.log; sync
      ps -o pid,args -p $pid      # must show mace_run_train with --lr 0.0025 and --work_dir $RUN
      ```

      Do the start check (4d) by hand as soon as the Initial record exists. A start-check FAIL does not use up the
      retry: kill the run, record and correct the cause (towards m only), list it as below, and start again in a new
      run.
   6. Append these lines to step34.log, in node_step34's line format, each as it happens (the block in step 5
      writes the first two):
      ```
      [<UTC>] start; repo <short HEAD of /data/work/ps_wp3> (5a retry with --lr 0.0025, run by hand)
      [<UTC>] 4c: training started, pid <pid>, threads <T>, run <NODE_WORK>/run<m>
      [<UTC>] 4d: start check PASS: <rb_startcheck.py output>
      [<UTC>] 4: training finished in <NODE_WORK>/run<m>; wp3.model sha256 <sha256>; restarts: <number of lines of restarts.txt> (restarts.txt)
      ```

      The `restarts:` field is a count, as node_step34 writes it: `$(wc -l < /data/work/wp3/restarts.txt)`, or 0
      if there is no restarts.txt.
   7. Run 5a on the retry run as node_step34 does (`<m>` is the retry run's number):

      ```
      cd /data/work/ps_wp3 && <PY> scripts/wp3_runbook/rb_techfail.py /data/work/wp3/run<m> /data/work/wp3/ds > /data/work/wp3/logs/techfail.txt 2>&1; echo "exit $?"
      ```

      Library warnings may stand before or after rb_techfail's own lines; they do not count, and both tools skip
      them. Exit 0, with `no technical failure (items checked here)` on the line after `<N> m21 frames evaluated
      with /data/work/wp3/run<m>/wp3.model`, is a pass. A `non-finite ...` line there is a failure. Anything else
      (for example an import error) gives no verdict: find the cause and run it again.
      - If it passes, append `[<UTC>] 5a: no technical failure (items checked here)` to step34.log, then run
        `sync; touch <NODE_WORK>/STEP34_DONE`. Keep KEEP_ALIVE if the node is to stay up for 5b and step 6 (A.4.1);
        otherwise remove it.
      - If it fails, criterion 6 is "not met (no fine-tuned model)". Step 7 does not run. Remove KEEP_ALIVE.

   **A reclaim, or any other interruption, during the retry.** The item-2 Interruptions rules apply to the retry
   run too:
   - **Discard the run unread.** Never resume it and never use `--restart_latest`. Write its verdict to
     `<NODE_WORK>/run<m>.end` (except for a node loss), and list it in node_step34's format, with one of the three
     tags a retry run may have:

     | end of run<m> | `<verdict>` |
     |---|---|
     | a reclaim or reboot | `[node loss] the node booted at <UTC>, after run<m> started at <UTC>` |
     | any other end without `wp3.model` (exception, OOM, kill, non-zero exit, no Initial record in time) | `[abnormal end] <what happened>, exit <rc>, <UTC of the end>: <last 3 lines of run<m>.stdout>` |
     | a start-check FAIL (the run killed) | `[start check FAIL] <UTC>: <rb_startcheck.py output>` |

     - in `restarts.txt`: `<UTC> run<m> discarded unread <verdict>`;
     - in step34.log: `[<UTC>] 4c: run<m> discarded unread <verdict>; the identical command runs in <NODE_WORK>/run<m+1>`.
   - **Run the identical retry command from scratch** in a new, empty `run<m+1>`, with its own start check and its
     own `start; repo` and `4c: training started` lines.
   - **The same cause twice in succession is a technical failure of the retry.** A spot reclaim or a node loss never
     counts. There is no second retry: criterion 6 is "not met (no fine-tuned model)", and nothing is trained
     after it.
   - **Different causes.** For each `[abnormal end]` of the retry after its first (even with a `[node loss]` between
     them), two reviewers compare its `run<b>.end` with the previous `[abnormal end]`'s `run<a>.end`. Only if the
     causes differ, write one line to `<NODE_WORK>/retry_causes_differ.txt`: `run<a> run<b>: <why the causes differ>`.
     Both tools refuse any later `[abnormal end]` of the retry without that line, and the note quotes it.
   - **node_relaunch.sh does not interfere.** It starts nothing while the training runs, and nothing for steps 3–5
     while STEP34_STOPPED exists or while `train_command_retry.txt` exists without STEP34_DONE.

   The note tool and node_step7.sh accept exactly two patterns, each before the retry run started:
   - (i) one earlier finished run, then `STOP: technical failure`, with its `techfail_run<k>.txt` (rb_techfail.py's
     lines for `run<k>` with a `non-finite` line; warnings around them do not count);
   - (ii) `STOP: run<k>: second abnormal end`, with `run<k>` not discarded afterwards, `run<k>.end` kept, and the
     STOP line's `earlier:` quote matching an `[abnormal end]` line of `restarts.txt`.

   Both patterns also need all of these:
   - `train_command_retry.txt` as above;
   - the training-log line `Learning rate: 0.0025, weight decay: 5e-07`;
   - the retry's own discarded runs tagged only as in the table;
   - for each `[abnormal end]` of the retry after its first, a line in `retry_causes_differ.txt`.

   Both patterns together, or two such STOPs, are refused, because there is one retry. The note's section "Technical
   failure and the one retry" names the failed run, the cause or causes, the retry's discarded runs and any
   statement that two causes differ.

### B. Node driver for step 7 (7a–7d): `scripts/wp3_runbook/node_step7.sh`

**Install.** Install the committed file as `/data/work/wp3_step7.sh`, and the committed `node_relaunch.sh` as
`/data/work/wp3_relaunch.sh`. Use the same method as before: write each as `<file>.new`, check its sha256, then `mv`
it over the old file. Never write onto a running driver. For example:

```
git -C /data/work/ps_wp3 show HEAD:scripts/wp3_runbook/node_step7.sh > /data/work/wp3_step7.sh.new && sha256sum /data/work/wp3_step7.sh.new && mv /data/work/wp3_step7.sh.new /data/work/wp3_step7.sh
```

At every start the driver logs `sha256sum $0` and the sha256 of `git show HEAD:scripts/wp3_runbook/node_step7.sh`,
and it STOPs if the two differ: the installed driver must be the committed one. It also logs the sha256 of
`/data/work/wp3_relaunch.sh` beside that of the committed `node_relaunch.sh`, with a WARN if they differ or the file
is missing. It does not STOP for that, because the relaunch script runs no step-7 work itself.

**Journal access.** The classifier reads the system and kernel journal only through `sudo -n journalctl`, one reader
for all of it (the boot's shutdown evidence and the kernel OOM-kill lines). ericdft may run `sudo -n journalctl`, and
is not in `adm` or `systemd-journal`:
- unprivileged, `journalctl -k -b` prints nothing;
- unprivileged, `journalctl -b` shows only ericdft's own and its user manager's entries.

Before anything runs, the driver STOPs unless all three of these hold:
- `sudo -n journalctl -b 0 -q _PID=1` shows at least one `systemd[1]:` line;
- `sudo -n journalctl -k -b 0 -q` shows at least one kernel line;
- `sudo -n journalctl --list-boots` lists at least two boots. The journal is persistent, so the end of a boot cut by
  a reclaim can be read after the next boot.

To check by hand:

```
sudo -n journalctl --list-boots --no-pager > /dev/null && sudo -n journalctl -b 0 -q _PID=1 -n 3 && sudo -n journalctl -k -b 0 -q -n 3 && sudo -n journalctl --list-boots --no-pager | tail -3
```

Later reads can also fail or be incomplete: a sudo or journalctl error, a boot no longer in the journal, an empty
answer, no time-stamped entry, or no `systemd[1]` entry for that boot. A journal can also fail to cover the end of
its boot: it ends over 30 min before the poller's last heartbeat, or before the attempt's launch. In each case that
attempt STOPs. It is never classified node-loss or anything else from missing evidence. The STOP is not kept: once
the cause is fixed, the next start classifies the attempt again, and an operator word resolves it as for any STOP.
journalctl's warnings on a successful read go into the evidence. Do not add ericdft to `adm` or `systemd-journal`,
or change any other system setting, without the user's decision.

**Start.** Start the driver (as ericdft) once STEP34_DONE, NOTE_COMMITTED and STEP6_DONE exist and the checkout is
at `<C6>` (A.4):

```
setsid nohup bash /data/work/wp3_step7.sh > /data/work/wp3/driver7.out 2>&1 < /dev/null &
```

**After a reclaim,** run `/data/work/wp3_relaunch.sh`.
- It relaunches step 7 when STEP34_DONE, NOTE_COMMITTED and STEP6_DONE exist and step 7 is neither done nor stopped.
  If NOTE_COMMITTED or STEP6_DONE is missing, it says which and starts nothing. Without STEP34_DONE it acts as for
  steps 2–4 ("Node drivers used for steps 2–4", After a reclaim).
- Before STEP34_DONE it never starts node_step34 while `train_command_retry.txt` exists (the by-hand retry, A.5).
- It starts nothing while any of these processes is alive: a driver, scripts/35, scripts/40, scripts/41, QE (pw.x,
  neb.x, pp.x, qe_queue.sh or chain.sh), training, or the step-7 poller.
- If step 7 stopped for a human, it prints the reasons of the driver's last run: its `STOP:` line, or, if a reclaim
  cut short the driver's wait for its children, every `STOP pending:` line. `STEP7_STOPPED` holds the same reasons.

**Preconditions.** Each failure is a STOP before anything runs.

The installation, the journal and the markers:
- the installed driver equals `HEAD:scripts/wp3_runbook/node_step7.sh`;
- the system and kernel journal are readable through `sudo -n journalctl`, and it lists at least two boots;
- `STEP34_DONE` exists;
- `NOTE_COMMITTED` holds `<CNOTE>`, and `STEP6_DONE` holds exactly one line, `<C6>`;
- the checkout is at `<C6>` and clean.

The note commit:
- `<CNOTE>` adds exactly one `MODEL_NOTE_<date>.md` and has one parent;
- the note is complete: no DRAFT banner, no `**Check:**` line and no "NOT COMPUTED". It records the selected model's
  offset. It has one value each of `model_sha256:`, `scripts_commit:` and `run:` (identical repeated lines count as
  one) and exactly one `note_status: complete` line;
- the note's `scripts_commit` (`<CN>`) is an ancestor of `<CNOTE>`;
- scripts 39, 40 and 41, and the helpers 40/41 load (22, 29, 30, 32, 35, 37, 38, `checks.py`), are present at
  `<CNOTE>` and byte-identical in three commits: `<CN>`, the commit node_step34 trained at, and `<CNOTE>`.

Step 6 before step 7:
- `<CNOTE>` is an ancestor of `<C6>`, and not `<C6>` itself;
- between them, nothing outside `results/` changed except a `scripts/39` fix (logged as a WARN), and neither a
  `MODEL_NOTE` nor `PLAN.md` changed. Every other changed path besides `wp3_eval.json` is named in a WARN;
- these are present at `<C6>` and byte-identical at `<CNOTE>` and `<C6>`:
  - scripts 40 and 41, every helper they load, `node_step7.sh` and `node_relaunch.sh`;
  - the repository data step 7 reads: `results/fa_host`, and `wp2b` and `wp2e` under `results/objective2/dopant_shell`;
- `<C6>` itself adds `results/objective2/dopant_shell/wp3/wp3_eval.json`, and it is not present at `<CNOTE>`;
- `<C6>` is the only commit after `<CNOTE>` that adds, changes or removes that file (scripts/39 once);
- that file is a `scripts/39` full-mode result, with no stand-in and no `--cache`. Its `arms.finetuned.sha256`, the
  evaluated model, is `<SHA>`;
- the file was made after the note: its `git.head` is `<CNOTE>`, or a later ancestor of `<C6>`, with nothing
  uncommitted;
- at that `git.head` only `results/` and `scripts/39` differ from `<CNOTE>`, so the scripts/32 and 37 it imports are
  the note commit's;
- it was written by the `scripts/39` committed at `<C6>` (`script_sha256`).

The run:
- `step34.log` has a "training finished in" line for the note's `run`, with the note's sha256, which is also the
  sha256 of its `wp3.model`;
- `logs/techfail.txt` passes for that run;
- its `4c: training started` line says `threads <T>`, the fastest count in timing.txt;
- if that run is the item-2 retry, all of these hold:
  - the run's history matches pattern (i) or (ii) of A.5;
  - `train_command_retry.txt` is the command with `--lr 0.0025`;
  - the training log shows only `Learning rate: 0.0025, weight decay: 5e-07`;
  - for pattern (ii), the first end of the deterministic pair is the restarts.txt line that node_step34's STOP quotes;
  - the retry's own discarded runs are `[node loss]`, `[abnormal end]` or `[start check FAIL]`, and each
    `[abnormal end]` of the retry after its first has its line in `retry_causes_differ.txt`.

  At most one retry is allowed.

The environment:
- `<SHA>` is not the foundation file;
- mace is 0.3.16;
- the cached foundation file has its PLAN hash (zeroshot loads it);
- the six band files exist;
- `/data/jobs/wp3b` holds nothing but the 12 WP3b labels;
- no QE process (pw.x, neb.x, pp.x, qe_queue.sh), and no training or scripts/35/40/41 process, is alive outside the
  driver.

**First start only** (7a never launched):
- The WP3b and MD work directories and `/data/jobs/wp3b` must be empty, and no region or zeroshot file may exist. An
  output made before step 7, by hand and perhaps before the note commit, is never adopted. Move it aside, record why
  for the WP3 result, then relaunch.
- `<C6>` is recorded in `step7/commit`. Every later start must run at that same commit, or it STOPs: the outputs of
  one step 7 come from one commit.

**What it runs and in what order.**

1. **7a.** `scripts/40 region`, then `zeroshot`. Each must exit 0. The zeroshot does not start beside a QE process.
2. **The MACE pool, on 64 threads.**
   - The 12 relaxations: one `--cells <host>_<system>` invocation each, unconstrained first, all with ONE `--work`,
     the script's default 6 threads, and never `--steps`.
   - The 12 MD runs: `--threads 8`, never `--steps` or `--report-every`.
   - Relaxations take priority, and MD runs fill the remaining threads. No more than 64 threads are ever in use: the
     budget is checked before every launch.
   - The first scripts/40 invocation runs alone until `wp2e_minimum.json` exists and has passed its check. It is
     the single writer of that file. The gate opens once the file exists and passes its check, on a relaunch too;
     if the file has gone after it was checked (the marker `step7/wp2e.ok` exists), the driver STOPs.
3. **7c.** `chain.sh wp3b`. It starts once every relaxation has its record or has no attempt left. Before it starts,
   the driver does two things:
   - it waits until no QE process outside the driver runs (including a wp3b queue started outside chain.sh);
   - it checks every input against its record.

**Spot notice.** The driver's poller records a termination notice from the metadata endpoint
(`step7/spot/notice.<boot>`). From then on, nothing new starts for 30 min: neither a MACE job nor the chain. A launch
then would almost certainly be cut short, and would spend one of the run's 3 attempts or the QE job's one
resubmission. Running children go on. After the reclaim, their ends are classified `spot-reclaim`. If the node still
runs 30 min after the notice, the driver logs a WARN and launches resume.

**Why this order.** The QE chain may not run beside MACE work, and the MD needs no relaxation. Putting all MACE work
before the chain gives a wall time of (MACE makespan + QE time). The MD runs fill the threads left idle by the tail
of the relaxations. Running the MD after the chain would add its full length: two 8-wide waves of 5000 steps, about
2 × 1.4 h at 8 threads.

**Resumable.** Every launch is recorded and synced (`step7/jobs/<label>/L<s>.launch`) before its process exists. The
record keeps the cause and its evidence. Every end is classified from evidence (`att<n>.cause`, fsynced, kept), except
a STOP for want of a readable journal, which is not kept. Phase markers, and the markers that stop a list line from
being written twice, are written after `sync`.

**What counts as complete.** A complete output is adopted only if both of these hold:
- a node_step7 launch started the attempt that made it (the attempt's pid is the launch's);
- the record, every attempt entry and `wp2e_minimum.json` were made at `<C6>` with no uncommitted change.

It is then re-checked before the next phase and before STEP7_DONE:

- **Relaxation:** the record (label, model sha, step cap 10 000, region_id, commit), the staged and queued QE input
  (sha256), and the relaxed structure against its input (1e-6 Å).
- **MD run:** the record (label, model sha, protocol, threads 8, commit), the trajectory sha256 and the attempt count.

A damaged complete output STOPs; it is never treated as complete. If only the queue copy of an input is missing,
the driver re-invokes the identical scripts/40 command, which completes the copy. A complete output that no launch
of the driver made STOPs. There are two ways to resolve it:
- move every file of that label aside (work and queue directories), so that the driver runs it itself;
- if it was made at `<C6>` by the identical command, write `accept <note>` (see below). The verifier still checks
  its commit, and the acceptance is listed.

**Reruns.** A rerun uses the scripts' own `--rerun-cause` and `--rerun-note`. The command is otherwise identical
(`--threads` included), and the scripts allow at most 3 attempts per run. The cause comes from evidence only:

| cause | evidence |
|---|---|
| `spot-reclaim` | The attempt started in an earlier boot, and the driver's poller recorded a spot termination notice in that boot (`step7/spot/notice.<boot>`; the metadata endpoint is polled every 5 s and the notice is fsynced). That boot's system journal shows no system-level shutdown. |
| `node-loss` | The attempt started in an earlier boot, and there is no notice. The poller was alive in that boot: its last heartbeat is at most 5 min before, and at most 30 min after, the last entry of the boot's system journal (the node logs cron and sysstat entries at least every 10 min, and journald syncs every 5 min). That journal covers the end of the boot and shows no system-level shutdown. |
| `oom` | The kernel journal of the boot has an OOM-kill line for the process's pid at or after its launch (exit 137), or a scripts/41 traceback holds a memory error. An OOM kill of an earlier holder of the same pid in that boot does not count. |

**Shutdown evidence is system-level only.** The journal is read as `-o short-unix` lines
(`<epoch>.<usec> <host> <identifier>[<pid>]: <message>`), and only an entry's identifier field counts. A message that
quotes such text (for example sudo's `COMMAND=/usr/bin/grep systemd[1]: ...`) is no evidence, and neither is an
indented continuation line of a multi-line message. These entries in the boot's system journal (read through sudo)
count as a clean shutdown:
- `systemd[1]`, the system manager, reaching `shutdown`, `poweroff`, `reboot`, `halt`, `kexec` or `final.target`
  (or the older form of those messages), or logging `Shutting down.`;
- any `systemd-shutdown[1]` line;
- `systemd-logind` logging `System is powering down`, `rebooting` or `halting`, or `Power key pressed`.

These do not count:
- a user manager (`systemd[<pid> ≠ 1]`) reaching its own `shutdown.target - Shutdown.`, as it does at every ssh
  logout;
- `systemd-journald: Journal stopped` (journald logs it at a restart too).

The rule was checked against the node's real journal tails:
- boots −3 and −2, ended by the idle self-stop: clean;
- boot −1, a spot reclaim with no shutdown sequence: not clean, so node-loss, or spot-reclaim with a notice;
- the current boot's user-manager `Shutdown.` lines: not clean.

Each attempt is matched to the last launch that expected it. The pid is only a cross-check: a pid that differs STOPs.

Anything else STOPs for a human:

- a clean shutdown in the system journal (above);
- a journal that cannot be read through `sudo -n journalctl`, holds no time-stamped or `systemd[1]` entry for that
  boot, or does not cover the end of the boot (not kept; see Journal access);
- a SIGTERM (status 'terminated'), which the driver never sends;
- a SIGKILL without OOM evidence. This STOP is not kept if the kernel journal could not be read, or if the exit is
  less than 5 min old, because journald may not have stored the kernel line yet. Either way the next start reads the
  journal again. A kill by systemd-oomd or earlyoom is logged outside the kernel journal, so it also ends here;
- no exit status and no reboot;
- no poller heartbeat;
- a relaxation log that holds a traceback, with an exit status other than 137 or none, unless the launch exited 1
  and the log ends with the exception line. Exit 1 with output after the traceback STOPs. With exit 137 or none,
  the OOM and boot evidence decides.

**Exceptions.** A relaxation or MD run that ends with a Python exception has no rerun (runbook 7d).
- For a relaxation, "ends with" means exit 1 with the exception line as the last line of its log. A traceback
  printed earlier, for example an "Exception ignored in" message, does not decide the end; the boot and OOM evidence
  does.
- The only rerun after an exception is an MD run whose traceback holds a memory error. It reruns with `oom`, as
  scripts/41 allows.
- The first exception end is listed as FINAL and STOPs, so that a systematic failure cannot use up the other runs'
  only attempt.
- A relaxation that ends with a Python MemoryError also STOPs: the runbook (no rerun after an exception) and item 4
  (a rerun after OOM) disagree on it.

**Refused launches.** A launch that the script refused (it exited before logging its attempt) STOPs. It is never
re-issued automatically. A launch cut short by a hard stop before the script logged its attempt is re-issued with
the identical command and the original evidence. No attempt is consumed.

**Hung jobs.** A job that has run for more than 3 times its expected length STOPs for a human, and nothing new
starts. The limits are 10 h for a relaxation (10 000 FIRE steps at about 1.2 s, extrapolated from the measured 1.0 s
at 8 threads) and 4.2 h for an MD run (5000 steps at about 1.0 s). The driver never kills it. If it is hung, kill its
pid (given in the STOP line) and give the cause `wall-time`.

**Resolving a STOP for one run.** The STOP line names the file and the words it accepts:
`/data/work/wp3/step7/cause.<label>.att<n>` (n = the script's attempt count), holding `<word> <note>`.

| word | meaning |
|---|---|
| `spot-reclaim`, `node-loss`, `oom`, `wall-time` | rerun with that cause (for the MemoryError relaxation, only `oom` or `final`) |
| `final` | no further attempt; listed as FINAL |
| `retry` | after a refused launch whose obstacle you removed: re-issue the identical command |
| `accept` | adopt a complete output made outside the driver (verified as above) |

Then relaunch. The driver records the operator's word and note, and the scripts still enforce their own rules. Only
files named `cause.<label>` or `cause.<label>.att<n>` with one of the 24 labels are read. Such a file that matches no
current STOP (another label's, a wrong attempt, the old name without `.att<n>`) is moved aside as `.unused.<time>` and
logged, never applied. A file under any other name (a mistyped label, for example) is never read: check the name
against the STOP line.

To relaunch after any STOP, act on every reason that `wp3_relaunch.sh` prints. Then start the driver directly, which
clears `STEP7_STOPPED`, or remove that marker and run `wp3_relaunch.sh`.

**List for the WP3 result.** `/data/work/wp3/step7_reruns.list` has one line per event, each with its time, cause
and evidence:

- RERUN, with the attempt number;
- REISSUE: a launch cut short before the script logged its attempt (or an operator `retry`), so no attempt was
  consumed;
- FINAL: no further attempt;
- ACCEPTED: a complete output made outside the driver, accepted by the operator;
- QE-INTERRUPTED: the chain was cut short while a wp3b job ran (an output without JOB DONE, written after the chain
  launch), with its cause from the same evidence. A chain launch cut short before any job ran is only logged.
  - If the old boot's journal cannot be read (the same rules as above), the driver STOPs before anything is listed
    or started. Fix the journal access and relaunch. If the journal is gone for good, write the cause to
    `/data/work/wp3/step7/cause.chain.C<n>` and relaunch: it is listed as the operator's cause, and the file is
    renamed `.used`.
  - If the old boot's journal is read but the evidence does not show a hard stop, the cause is listed as
    "undetermined: <evidence>", with a WARN in `step7.log`. That is the case when the boot ended with a clean
    shutdown (with or without a spot notice), when the spot notice is more than 1 h older than the end of the boot's
    journal, and, without a notice, when the poller left no heartbeat in that boot or its last heartbeat is more than
    5 min before the end of the journal. The cut job still uses its one item-1d resubmission. State it in the WP3
    result;
- QE-RESUBMISSION: an `.out.tryN` with its mtime;
- QE-GAVEUP.

**KEEP_ALIVE is not used by step 7.** No phase is idle: 7a and the pool run MACE, so the 1-min load is 6 or more,
and the chain runs pw.x. The driver moves between phases at once. Two waits are short and bounded:
- the 30-min spot-notice hold, after which a reclaim normally follows;
- the wait for a foreign QE process before the chain, during which that process keeps the node busy.

The operator keeps `/data/KEEP_ALIVE` only during the by-hand retry training (A.5), during a by-hand finish of 4d–5a
("Driver killed while training runs"), and while the node waits for 5b and step 6 (A.4.1). It is removed after
`preconditions PASS`. The driver logs a WARN while the file exists. After
STEP7_DONE or a STOP the node is idle, and the idle self-stop may stop it, as intended.

**The driver never:**

- passes `--steps` or `--report-every`;
- kills a child. It waits for every running child before it exits, on a STOP, an error or a SIGTERM. To leave the
  children running unwatched, SIGKILL the driver itself; its lock is held until they end;
- deletes or moves a script output. It only renames operator cause files, once used or found unused;
- starts the chain beside MACE work or another QE process, or MACE work beside a QE process;
- starts anything new after a spot termination notice in the current boot (for 30 min);
- reads the journal other than through `sudo -n journalctl`.

**Single instance.** The lock (`step7.lock`, fd 8) is inherited by every child, so a relaunch is refused while
anything an earlier instance started is alive.

### C. 7e additions

- Also copy `/data/work/wp3/step7_reruns.list` and `step7.log` to `<MAC_STAGE>`, and archive them with the work
  directories.
- The records were made at `<C6>`. In `scripts/41_wp3_md.py analyse`, `--commit <CN>` is the note's
  `scripts_commit`, as the script's help says ("commit of scripts/41 recorded in the model note"). scripts/41 and 35
  are byte-identical at `<CN>`, `<CNOTE>` and `<C6>`, so any of them gives the same result. The driver's last log
  line prints `<CN>` and `<C6>`.

### How these tools were tested (2026-10-29, laptop, SYNTHETIC; no MACE evaluation, no relaxation, no MD, no QE)

The harness was kept on the laptop, outside the repository, in a temporary directory that is not archived: its
fixtures include the node's real journal tails, which hold host names and client addresses. It is the round-1
harness with its own paths, metadata port and process markers. The driver under test is the repository file with
its paths (the sudo and journalctl stand-ins among them), the metadata endpoint, its process names and its poll
tick (5 s to 1 s) rewritten by sed. It has fake scripts/40 and scripts/41 that reproduce the frozen scripts' file
contracts:
- locks and records;
- attempt logs with pid and git state;
- `--rerun-cause` rules and the 3-attempt limit;
- the single writer of `wp2e_minimum.json`;
- the QE input written only after the record.

What was stubbed or shimmed:
- the QE queue, with the node's qe_queue.sh semantics, and run_qe.sh;
- `sudo -n` (a pass-through, or failing as `sudo -n` does without the right, also part-way through a run) and
  `journalctl`. journalctl serves the system and kernel journal of each boot, including the node's real journal
  tails, only when reached through sudo. Without sudo it gives the unprivileged view, and every such call is
  counted: the whole batch made none;
- bash 3.2 was used, with shims for flock, setsid, GNU `date` and the metadata endpoint, which was a local HTTP
  server.

Each scenario's clone holds the three commits `<CN>` (the tools), `<CNOTE>` (the note alone) and `<C6>` (a
`wp3_eval.json` with the fields the driver reads; no model evaluated). The installed driver is the committed one:
each clone commits the rewritten copy that it installs.
Hard stops were SIGKILLs of the whole process group, followed by a new boot id. The model note was made by
`rb_model_note.py` itself; its offset was computed through the self-test calculator hook (a stub, no MACE).

`rb_model_note.py --self-test` runs 48 synthetic cases: the complete note; all four DRAFT kinds; both kinds of retry,
with the refusals that guard them and abnormal ends of the retry itself; 5a files with library warnings before and
after rb_techfail.py's lines; the tool's own errors (exit 1) and `--force`; and a sample of the other refusals (start
check, basis, excluded options, test-host data, checkpoints, sha256, scripts changed). It does not cover every
refusal: for example, a bad timing.txt, a `--seed` other than 123, a malformed `retry_causes_differ.txt` line and a
versions mismatch have no case. The classifier has 152 isolated checks (`unit/t_cls.sh`), among them the real journal
tails, multi-line entries, journal gaps and kernel OOM lines. The archive-copy procedure of A.4.3 ran on a synthetic
node checkout, including a re-gzipped archive (`unit/t_archive.sh`). The retry pre-flight of A.5 ran with a stub
`mace_run_train` and the repository's `rb_preflight.py` (`unit/t_retry_preflight.sh`). The 40 scenarios are listed in
`NOTES.md`. On the final versions of the three tools (`NOTES.md`, R4) the self-test, the 152 classifier checks and
scenarios P, H0, K1, A1, C2 and B2 were re-run. The other 34 scenarios ran on their R2F versions, which lack the
PLAN.md STOP (R3) and the merge-review changes (R4).

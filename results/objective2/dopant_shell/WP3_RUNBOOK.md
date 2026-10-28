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
| `<NODE_REPO>` | a clean checkout of `<C1>` on the node, with the band files at `<NODE_REPO>/../bands` (byte-identical to the Mac's `../bands`) |
| `<NODE_WORK>` | node work directory for everything that is not a QE job (e.g. `/data/work/wp3`) |
| `<MAC_STAGE>` | Mac staging directory **outside** the repository (pulled campaigns, work dirs, model) |
| `<FM>` | absolute path of the foundation file `20231203mace128L1_epoch199model` on the node |
| `<RUN>` | absolute path of a **new, empty** training directory on the node |
| `<SHA>` | sha256 of `<RUN>/wp3.model`, as recorded in the committed model note |
| `<CN>` | the commit recorded in the model note: scripts 39, 40 and 41 are committed and unchanged there |
| `<T>` | the training thread count fixed by the timing run |

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

   Then copy `../bands` next to it.
4. `/data/KEEP_ALIVE` is present throughout training (item 2, Keep-alive): `node_step34.sh` creates it
   before the pre-flight and removes it after the technical-failure check. Outside training it is not
   needed: since 2026-10-29 the idle cron counts pw.x, a 1-min load above 1 or a login as busy, and after
   60 idle min stops the node in economical mode (StopCharging). Chain the steps so the node does not wait
   on the Mac, and stop it with `python3 /data/setup/ecs_selfstop.py stop` when nothing is queued.

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
- **Training restarts (4e).** A run that ends without `wp3.model` is discarded unread. It is never deleted or
  reused, and the identical command runs in `run<n+1>`. Each restart is listed with its cause and time in
  `<NODE_WORK>/restarts.txt` as one of four kinds:
  - `[node loss]`;
  - `[abnormal end]`, seen by the driver: an exception, OOM, a kill, a non-zero exit, or no Initial record
    within the 2-epoch time + 30 min;
  - `[start check FAIL]`, corrected by hand before the relaunch;
  - `[operator]`.
  The driver stops for a human at a second `[abnormal end]`, even when the causes differ. If the causes
  differ, relaunch with `PREV_CAUSE='<cause> <UTC time>'`. `restarts.txt` and `item1p_rerun.list` go into the
  5b model note and the WP3 result.
- **Keep-alive after a restart.** `/data/KEEP_ALIVE` lives on `/data` and survives a reclaim. After a console
  restart that is not followed by a driver relaunch, run `rm -f /data/KEEP_ALIVE`.
- **Driver killed while training runs.** `step34.log` then ends with `STOP: unexpected exit 143`, and
  KEEP_ALIVE is kept. Wait for the run to end, then do 4d–5a by hand.

## Step 3: archive, then scripts/33 (Mac, repository root, at `<C1>`)

### 3a. Pull and archive

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

## Step 6: criterion 6 and adoption (a)–(c), once (Mac, repository root, at `<CN>`)

```
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

Steps 7a–7d run on the node in `<NODE_REPO>` at `<CN>`; the analyses in 7e run on the Mac. The model is
`<RUN>/wp3.model` with `<SHA>`.

### 7a. Region and zero-shot comparator

```
<PY> scripts/40_wp3b.py region --out <NODE_WORK>/wp3b/wp3b_region.json      # must exit 0 (6.0 A; 81/83/81)
<PY> scripts/40_wp3b.py zeroshot --region <NODE_WORK>/wp3b/wp3b_region.json --out <NODE_WORK>/wp3b/wp3b_zeroshot.json   # must exit 0
```

### 7b. Relaxations

Use ONE `--work` for both sets.

```
<PY> scripts/40_wp3b.py relax --region <NODE_WORK>/wp3b/wp3b_region.json --model <RUN>/wp3.model --model-sha256 <SHA> \
    --work <NODE_WORK>/wp3b/relax --qe /data/jobs/wp3b
<PY> scripts/40_wp3b.py relax --region <NODE_WORK>/wp3b/wp3b_region.json --model <RUN>/wp3.model --model-sha256 <SHA> \
    --work <NODE_WORK>/wp3b/relax --qe /data/jobs/wp3b --unconstrained
```

The first invocation writes `wp2e_minimum.json` before its first relaxation. Start the other invocations
only after that file exists: parallel writers of that file can corrupt it. After that, `--cells <host>_<system>`
invocations may run in parallel, because each cell has a lock. Do not add `--steps`: any value other than
10000 marks a smoke test.

### 7c. QE single points

Wait until all 12 records exist; there are then 12 inputs below `/data/jobs/wp3b`.

```
nohup /data/setup/chain.sh wp3b > /dev/null 2>&1 &
```

Do not start it earlier: the queue ends ("all done") as soon as it finds no pending input. A job without
JOB DONE gets one resubmission (queue). An unconverged SCF is a Fail of (d) and is not re-run.

### 7d. MD stability (e)

There are 12 runs, one per invocation. They may run in parallel, but not alongside the 64-rank QE chain.

```
for h in m30 m32; do for s in undoped GA Sr; do for T in 300 450; do
  <PY> scripts/41_wp3_md.py run --model <RUN>/wp3.model --model-sha256 <SHA> --host $h --system $s --T $T \
      --work <NODE_WORK>/wp3md --threads 8
done; done; done
```

Do not add `--steps` or `--report-every`. Reruns:
- **Interrupted relaxation or MD run.** Give the identical command with `--rerun-cause
  {spot-reclaim|node-loss|oom|wall-time}` (and optionally `--rerun-note`), at most twice. The `--threads`
  value must stay the same. The scripts move partial outputs aside unread.
- **Ended with an exception.** A relaxation that ended with an exception has no rerun. An MD run that
  ended with an exception accepts only `oom`, and only with a memory error in its traceback.

### 7e. Pull, archive, analyse (Mac, at `<CN>`; scripts/41 analyse needs the git history)

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
two work directories as tarballs if they are kept under `results/` (see the Archive layout).

## Step 8: Outcome and WP3 result (Mac, at `<CN>` or later)

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

Run on the node, at `<CN>`:

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

## How this runbook was tested (2026-10-28, laptop, SYNTHETIC; no QE, MD, relaxation, NEB or training)

Scratch directory: `/private/tmp/claude-501/m_impl/integration/`.

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

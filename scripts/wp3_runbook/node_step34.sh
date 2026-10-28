#!/bin/bash
# WP3 steps 3-4 driver (PLAN amendment m item 7 steps 3-4; WP3_RUNBOOK.md 2e item-1' re-runs, 3a-3c, 4a-4d).
# Runs on the node as ericdft in the clean checkout, after /data/work/wp3/STEP2_DONE exists.
# Stops (fail-closed, nothing further started) at: a QE input not final or not equal to its frame, scripts/33 stop
# or W < 60, a pre-flight FAIL, a start-check FAIL, a second abnormal end of training, or a training end it cannot
# classify. Those cases are handled by hand under amendment m item 2.
# Resumable: after a reclaim, relaunch this file by hand. A training run without wp3.model is discarded unread and
# the identical command runs from scratch in a new, empty run<n>; each restart is listed with cause and time in
# $W/restarts.txt. Never edit this file in place while it runs: install a new copy under another name, then mv it.
set -euo pipefail
{   # the whole body is parsed before any of it runs
R=/data/work/ps_wp3; PY=/data/miniforge3/envs/mace/bin/python; MT=/data/miniforge3/envs/mace/bin/mace_run_train
W=/data/work/wp3; J=/data/jobs; D=$R/results/objective2/dopant_shell; FM=/home/ericdft/.cache/mace/20231203mace128L1_epoch199model
log(){ echo "[$(date -u +%FT%TZ)] $*" >> $W/step34.log; }
# one instance only; the lock (fd 8) is inherited by the QE chain and the nohup'ed training, so a relaunch is also
# refused while a run started by an earlier instance is alive. A reboot releases it.
exec 8>>$W/step34.lock; flock -n 8 || { log "launch refused: another node_step34, or a process it started, holds step34.lock"; exit 0; }
[ -e $W/STEP34_DONE ] && { log "launch: STEP34_DONE exists, nothing to do"; exit 0; }
rm -f $W/STEP34_STOPPED; pid=""
cd $R
ka_off(){ if [ -n "$pid" ] && kill -0 $pid 2>/dev/null; then log "training pid $pid still running: /data/KEEP_ALIVE kept; finish 4d-5a by hand"; else rm -f /data/KEEP_ALIVE; fi; }
stop(){ log "STOP: $*"; touch $W/STEP34_STOPPED; ka_off; exit 1; }
on_err(){ c=${BASH_COMMAND%%$'\n'*}; stop "unexpected error (exit $1) at line $2: ${c:0:160}"; }
on_exit(){ rc=$?; { [ $rc = 0 ] || [ -e $W/STEP34_STOPPED ]; } && return; log "STOP: unexpected exit $rc"; touch $W/STEP34_STOPPED; ka_off; }
trap 'on_err $? $LINENO' ERR
trap on_exit EXIT
trap 'exit 143' TERM HUP INT
[ -e $W/STEP2_DONE ] || stop "STEP2_DONE missing"
[ "$(sha256sum $FM | cut -c1-64)" = 01bfe22100139f424713cf921144e5509cbe353d67aa9fa1be9c6e1e0ed35845 ] || stop "foundation sha256"
log "start; repo $(git rev-parse --short HEAD)"

# 2e (item 1'): an SCF that ends with JOB DONE but without convergence is re-run once with identical settings.
# qe_queue renames only outputs WITHOUT JOB DONE and this block only outputs WITH it, so a .out.try* that holds
# JOB DONE marks an earlier item-1' re-run. Each step is idempotent, so a relaunch after a reclaim resumes it.
if [ ! -e $W/item1p_rerun.done ]; then
  for o in $J/wp3x/*/*.out; do b=${o%.out}; L=$(basename $b)
    grep -q "JOB DONE" $o || continue
    grep -q "convergence has been achieved" $o && continue
    grep -qs "JOB DONE" $b.out.try* && { log "item-1' $L: unconverged after its item-1' re-run: no further run"; continue; }
    k=$(ls $b.out.try* 2>/dev/null | wc -l || true)
    mv $o $b.out.try$((k+1)); echo "$(date -u +%FT%TZ) $L re-run (unconverged output -> out.try$((k+1)))" >> $W/item1p_rerun.list
    log "item-1' $L: JOB DONE without SCF convergence -> re-run once (out.try$((k+1)))"
  done
  # m 1' and 1d: a re-run that stopped without JOB DONE (e.g. a reclaim) is resubmitted once with the identical input.
  # qe_queue alone would count the item-1' rename as its retry; once a try without JOB DONE exists, the queue decides.
  for o in $J/wp3x/*/*.out; do b=${o%.out}; L=$(basename $b)
    [ -e $o ] || continue
    grep -q "JOB DONE" $o && continue
    grep -qs "JOB DONE" $b.out.try* || continue
    f=0; for t in $b.out.try*; do grep -q "JOB DONE" $t || f=$((f+1)); done; [ $f = 0 ] || continue
    k=$(ls $b.out.try* | wc -l)
    mv $o $b.out.try$((k+1)); echo "$(date -u +%FT%TZ) $L resubmitted (re-run stopped without JOB DONE -> out.try$((k+1)))" >> $W/item1p_rerun.list
    log "item-1' $L: re-run stopped without JOB DONE -> resubmitted once with the identical input (m 1d; out.try$((k+1)))"
  done
  # every QE input final before the archive: wait out any queue started outside chain.sh, then the (idempotent) chain
  for c in wp3 wp3x wp3chk; do flock /tmp/qe_queue_$c.lock true; done
  /data/setup/chain.sh wp3 wp3x wp3chk
  for i in $J/wp3/*/*.in $J/wp3x/*/*.in $J/wp3chk/*/*.in; do b=${i%.in}
    grep -qs "JOB DONE" $b.out || [ -e $b.gaveup ] || stop "QE input not final after the chain: $(basename $b) (neither a JOB DONE output nor a .gaveup)"
  done
  sync; touch $W/item1p_rerun.done
  log "item-1' re-runs and resubmissions: $(cat $W/item1p_rerun.list 2>/dev/null | wc -l || true) (item1p_rerun.list); every QE input final"
fi

# 3a: every input still equals its frame (as at 2d; a frame or input lost in a hard stop is not a 1d drop)
$PY scripts/wp3_runbook/rb_verify_inputs.py $J $W/frames > $W/logs/verify_inputs_3a.log 2>&1 \
  || stop "input check FAILED before the archive (logs/verify_inputs_3a.log): a damaged frame or input is an amendment question"
log "3a: $(tail -1 $W/logs/verify_inputs_3a.log)"
# 3a: archive into the checkout (m 1e layout). A marker, written after sync, is the commit point of each part.
if [ ! -e $W/frames_copied ]; then
  rm -rf $D/wp3/frames; mkdir -p $D/wp3/frames
  cp -p $W/frames/*.extxyz $W/frames/frames_report.json $D/wp3/frames/; sync; touch $W/frames_copied
fi
for c in wp3:raw wp3x:test_extra/raw wp3chk:chk/raw; do src=${c%%:*}; dst=$D/wp3/${c#*:}
  [ -e $W/archived_$src ] && continue
  [ -e $dst ] && log "3a: $dst without archived_$src (cut short earlier): removed and redone from $J/$src"
  rm -rf $dst
  bash scripts/wp3_runbook/rb_archive.sh $J/$src $dst >> $W/step34.log 2>&1 || stop "archive $src"
  sync; touch $W/archived_$src
done
left=$(find $D/wp3 \( -name '*.out' -o -name '*.in' -o -name '*.out.try?' \) | wc -l)
[ "$left" = 0 ] || stop "uncompressed files in the archive: $left"
x=$W/v2prod_x; rm -rf $x; mkdir -p $x && tar xzf $D/wp1_production/v2prod_structures.tar.gz -C $x
log "3a: archived; $(ls $D/wp3/raw | wc -l) wp3, $(ls $D/wp3/test_extra/raw | wc -l) item-1', $(ls $D/wp3/chk/raw | wc -l) chk files"

# 3b-3c: scripts/33, the m 1e command, once (re-run only if an earlier run was cut short: no s33.done)
TH=$($PY scripts/wp3_runbook/rb_test_hosts.py)
log "3b: test hosts: $TH"
if [ ! -e $W/s33.done ]; then
  [ -e $D/wp3/dataset ] && log "3c: dataset dir without s33.done (scripts/33 cut short earlier): removed, scripts/33 re-run"
  rm -rf $D/wp3/dataset
  $PY scripts/33_finetune_dataset.py --dft results/objective2/dopant_shell \
      --frames ../bands $x/v2prod results/objective2/dopant_shell/wp3/frames \
      --out results/objective2/dopant_shell/wp3/dataset --test-hosts $TH --valid-hosts m21 \
      > $W/logs/s33.log 2>&1 || stop "scripts/33 stopped (see logs/s33.log)"
  sync; touch $W/s33.done
fi
for f in train.xyz valid.xyz test.xyz E0s.json dataset_meta.json; do [ -s $D/wp3/dataset/$f ] || stop "scripts/33 wrote no $f (W < 60 or UNDECIDED)"; done
$PY - $D/wp3/dataset/dataset_meta.json >> $W/step34.log <<'EOF'
import json, sys; m = json.load(open(sys.argv[1])); q = m["q1_check"]
print("3d: n", m["n"], "| W", m["wp3"]["W"], "ok", m["wp3"]["ok"], "dropped", m["wp3"]["dropped"], "| basis", m["basis"], "| WP3 vacancy", m["wp3_vacancy_energy"])
print("3d: (a)", q["a"]["value_meV"], q["a"]["pass"], "| (b)", {X: (q["b"][X]["value_meV"], q["b"][X]["pass"]) for X in ("Sr", "undoped")})
print("3d: loss_weights", m["loss_weights"])
EOF
DS=$W/ds; rm -rf $DS; cp -rp $D/wp3/dataset $DS
WE=$($PY -c "import json; print(json.load(open('$DS/dataset_meta.json'))['loss_weights']['w_E'])")
B=$($PY -c "import json; print(json.load(open('$DS/dataset_meta.json'))['basis'])")
log "3: dataset ready; basis $B, w_E $WE"

# 4: item-2 command (without --work_dir and --max_num_epochs); KEEP_ALIVE throughout (item 2, Keep-alive)
touch /data/KEEP_ALIVE
ARGS=(--name wp3 --seed 123 --device cpu --default_dtype float64 --foundation_model $FM --multiheads_finetuning False
  --train_file $DS/train.xyz --valid_file $DS/valid.xyz --E0s $DS/E0s.json --energy_key REF_energy --forces_key REF_forces
  --loss weighted --energy_weight $WE --forces_weight 100 --optimizer adam --amsgrad --lr 0.005 --weight_decay 5e-7
  --clip_grad 10 --scheduler ReduceLROnPlateau --lr_factor 0.8 --scheduler_patience 50 --ema --ema_decay 0.99
  --batch_size 2 --valid_batch_size 2 --patience 2048 --eval_interval 1 --keep_checkpoints)
echo "$MT ${ARGS[*]} --max_num_epochs 100 --work_dir <run>" > $W/train_command.txt

# 4a: pre-flight (--dry_run; nothing trained)
P=$W/preflight; rm -rf $P; mkdir $P
$MT "${ARGS[@]}" --max_num_epochs 100 --work_dir $P --dry_run > $P.stdout 2>&1 || true
$PY scripts/wp3_runbook/rb_preflight.py $P/logs/wp3_run-123.log $DS $FM $WE > $W/logs/preflight.txt 2>&1 || stop "pre-flight FAIL (logs/preflight.txt)"
log "4a: pre-flight PASS"

# 4b: timing run at 8, 16, 32 threads, 2 epochs each; only wall time is read, outputs deleted. timing.txt appears
# (by mv) only once all three have finished; a pass cut short is discarded and all three are repeated.
if [ ! -s $W/timing.txt ]; then
  if [ -e $W/timing.part ] || ls -d $W/timing_[0-9]* > /dev/null 2>&1; then
    log "4b: an earlier timing pass was cut short (finished: $(tr '\n' ';' < $W/timing.part 2>/dev/null || true)): discarded, all three repeated"
  fi
  rm -rf $W/timing.part $W/timing_8 $W/timing_16 $W/timing_32 $W/timing_8.stdout $W/timing_16.stdout $W/timing_32.stdout
  for T in 8 16 32; do d=$W/timing_$T; mkdir $d
    t0=$(date +%s); OMP_NUM_THREADS=$T $MT "${ARGS[@]}" --max_num_epochs 2 --work_dir $d > $d.stdout 2>&1 || true; t1=$(date +%s)
    [ -s $d/wp3.model ] || stop "timing run at $T threads did not finish (see $d.stdout)"
    echo "$T $((t1-t0))" >> $W/timing.part; rm -rf $d $d.stdout
  done
  sync; mv $W/timing.part $W/timing.txt
fi
[ "$(cut -d' ' -f1 $W/timing.txt | tr '\n' ' ')" = "8 16 32 " ] || stop "timing.txt does not hold exactly the 8, 16 and 32 thread runs"
T=$(sort -k2,2n -k1,1n $W/timing.txt | head -1 | cut -d' ' -f1)   # fastest; equal wall times: fewer threads
log "4b: timing (threads, s for 2 epochs): $(tr '\n' ';' < $W/timing.txt) -> T=$T"

# 4c-4d: training with the start check, in a new, empty run<n> (item 2 Interruptions; never --restart_latest).
# A run that ended without wp3.model is discarded unread and listed in restarts.txt with its cause and time:
# [node loss] (the node booted after the run started), [abnormal end] (seen by the driver: exception, OOM, kill,
# non-zero exit), [start check FAIL] (corrected by hand first) or [operator] (relaunch with PREV_CAUSE='<cause>').
# A second [abnormal end] stops for a human (item 2 Deterministic causes: the same cause twice is a technical failure).
BT=$(awk '/^btime/{print $2}' /proc/stat)
while true; do
  n=1; while [ -e $W/run$n ]; do n=$((n+1)); done; RUN=$W/run$n
  if [ $n -gt 1 ] && ! grep -qs " run$((n-1)) discarded unread " $W/restarts.txt; then
    Q=$W/run$((n-1)); q=$(basename $Q)
    if [ -s $Q.end ]; then cause=$(cat $Q.end)                     # the driver's verdict (a start-check FAIL run is void even with a model)
    elif [ -s $Q/wp3.model ]; then stop "$q has wp3.model: judge it from its log and run 5a by hand (item 2 'Model written, then abnormal exit')"
    elif [ "$BT" -gt "$(cat $Q.start 2>/dev/null || echo 9999999999)" ]; then
      cause="[node loss] the node booted at $(date -u -d @$BT +%FT%TZ), after $q started at $(date -u -d @$(cat $Q.start) +%FT%TZ); last results write $(date -u -r $Q/results/wp3_run-123_train.txt +%FT%TZ 2>/dev/null || echo none)"
    else cause=""; fi
    if [ -n "${PREV_CAUSE:-}" ]; then cause="[operator] $PREV_CAUSE${cause:+; driver: $cause}"; PREV_CAUSE=""
    elif [ -z "$cause" ]; then stop "$q ended without wp3.model while no driver watched it and without a reboot: list its cause, then relaunch with PREV_CAUSE='<cause> <UTC time>'"
    elif [[ $cause == "[abnormal end]"* ]] && grep -qs "\[abnormal end\]" $W/restarts.txt; then
      stop "$q: second abnormal end ($cause; earlier: $(grep '\[abnormal end\]' $W/restarts.txt | tail -1)). The same cause twice in succession is a technical failure (item 2); if the causes differ, relaunch with PREV_CAUSE='<cause>'"
    fi
    echo "$(date -u +%FT%TZ) $q discarded unread $cause" >> $W/restarts.txt; sync
    log "4c: $q discarded unread $cause; the identical command runs in $RUN"
  fi
  date +%s > $RUN.start; mkdir $RUN; cd $RUN
  OMP_NUM_THREADS=$T nohup $MT "${ARGS[@]}" --max_num_epochs 100 --work_dir $RUN > $RUN.stdout 2>&1 &
  pid=$!; echo $pid > $RUN.pid; cd $R
  log "4c: training started, pid $pid, threads $T, run $RUN"
  t_end=$(( $(date +%s) + $(awk -v t=$T '$1==t{print $2}' $W/timing.txt) + 1800 ))   # Initial comes before epoch 1
  until grep -qs '"epoch": null' $RUN/results/wp3_run-123_train.txt || ! kill -0 $pid 2>/dev/null || [ $(date +%s) -ge $t_end ]; do sleep 30; done
  if ! grep -qs '"epoch": null' $RUN/results/wp3_run-123_train.txt; then     # an abnormal end, not a start-check result
    why="ended before the Initial record"
    kill -0 $pid 2>/dev/null && { kill $pid; why="killed by the driver: no Initial record within the 2-epoch time + 30 min"; }
    rc=0; wait $pid || rc=$?; pid=""
    echo "[abnormal end] $why, exit $rc, $(date -u +%FT%TZ): $(tail -3 $RUN.stdout | tr '\n' ' ')" > $RUN.end; sync
    log "4c: $(basename $RUN) $(cat $RUN.end)"; continue
  fi
  SC=$W/logs/startcheck_run$n.txt
  if $PY scripts/wp3_runbook/rb_startcheck.py $RUN/results/wp3_run-123_train.txt $B > $SC 2>&1; then
    log "4d: start check PASS: $(cat $SC)"
  else
    kill $pid 2>/dev/null || true; wait $pid 2>/dev/null || true; pid=""
    echo "[start check FAIL] $(date -u +%FT%TZ): $(tr '\n' ' ' < $SC)" > $RUN.end; sync
    stop "start check FAIL (Initial record read), run killed: $(cat $SC). Record and correct the cause (towards m only), then relaunch: $(basename $RUN) is discarded and the identical command runs in a new run (not the retry)"
  fi
  rc=0; wait $pid || rc=$?; pid=""
  if [ -s $RUN/wp3.model ]; then
    [ $rc = 0 ] || log "4: $(basename $RUN) exited $rc after writing wp3.model: judged from its log (item 2 'Model written, then abnormal exit')"
    break
  fi
  echo "[abnormal end] exit $rc after the start check, $(date -u +%FT%TZ): $(tail -3 $RUN.stdout | tr '\n' ' ')" > $RUN.end; sync
  log "4c: $(basename $RUN) $(cat $RUN.end)"
done
log "4: training finished in $RUN; wp3.model sha256 $(sha256sum $RUN/wp3.model | cut -c1-64); restarts: $(cat $W/restarts.txt 2>/dev/null | wc -l || true) (restarts.txt)"

# 5a: technical-failure check (training log, results file, m21 only); exit 1 with no verdict line is a checker error
rc=0; $PY scripts/wp3_runbook/rb_techfail.py $RUN $DS > $W/logs/techfail.txt 2>&1 || rc=$?
if [ $rc = 0 ]; then log "5a: $(tail -1 $W/logs/techfail.txt)"
elif grep -q '^non-finite' $W/logs/techfail.txt; then stop "technical failure: $(grep '^non-finite' $W/logs/techfail.txt | head -3 | tr '\n' ' ')"
else stop "technical-failure CHECK ERROR, no verdict (exit $rc; not a technical failure until judged by hand): $(tail -3 $W/logs/techfail.txt | tr '\n' ' ')"; fi
rm -f /data/KEEP_ALIVE
sync; touch $W/STEP34_DONE
log "done"
exit; }

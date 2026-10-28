#!/bin/bash
# WP3 steps 3-4 driver (PLAN amendment m item 7 steps 3-4; WP3_RUNBOOK.md 2e item-1' re-runs, 3a-3c, 4a-4d).
# Runs on the node as ericdft in the clean checkout, after /data/work/wp3/STEP2_DONE exists.
# Stops (fail-closed, nothing further started) at: scripts/33 stop or W < 60, a pre-flight FAIL, a start-check
# FAIL, or a training run that ends without wp3.model. Those cases are handled by hand under amendment m item 2.
set -euo pipefail
R=/data/work/ps_wp3; PY=/data/miniforge3/envs/mace/bin/python; MT=/data/miniforge3/envs/mace/bin/mace_run_train
W=/data/work/wp3; J=/data/jobs; D=$R/results/objective2/dopant_shell; FM=/home/ericdft/.cache/mace/20231203mace128L1_epoch199model
cd $R
log(){ echo "[$(date -u +%FT%TZ)] $*" >> $W/step34.log; }
stop(){ log "STOP: $*"; touch $W/STEP34_STOPPED; rm -f /data/KEEP_ALIVE; exit 1; }
[ -e $W/STEP2_DONE ] || stop "STEP2_DONE missing"
[ "$(sha256sum $FM | cut -c1-64)" = 01bfe22100139f424713cf921144e5509cbe353d67aa9fa1be9c6e1e0ed35845 ] || stop "foundation sha256"
log "start; repo $(git rev-parse --short HEAD)"

# 2e (item 1'): an SCF that ends with JOB DONE but without convergence is re-run once with identical settings
if [ ! -e $W/item1p_rerun.done ]; then
  n=0
  for o in $J/wp3x/*/*.out; do
    grep -q "JOB DONE" $o || continue
    grep -q "convergence has been achieved" $o && continue
    b=${o%.out}; k=$(ls $b.out.try* 2>/dev/null | wc -l || true)
    [ $k -ge 1 ] && { log "item-1' $(basename $b): unconverged after a queue retry: no further run"; continue; }
    mv $o $b.out.try$((k+1)); n=$((n+1)); log "item-1' $(basename $b): JOB DONE without SCF convergence -> re-run once (out.try$((k+1)))"
  done
  [ $n -gt 0 ] && { /data/setup/chain.sh wp3x; log "item-1' re-runs finished ($n)"; }
  touch $W/item1p_rerun.done
fi

# 3a: archive into the checkout (m 1e layout)
if [ ! -e $D/wp3/frames/frames_report.json ]; then
  mkdir -p $D/wp3/frames && cp -p $W/frames/*.extxyz $W/frames/frames_report.json $D/wp3/frames/
fi
for c in wp3:raw wp3x:test_extra/raw wp3chk:chk/raw; do src=${c%%:*}; dst=$D/wp3/${c#*:}
  [ -e $W/archived_$src ] && continue
  bash scripts/wp3_runbook/rb_archive.sh $J/$src $dst >> $W/step34.log 2>&1 || stop "archive $src"
  touch $W/archived_$src
done
left=$(find $D/wp3 \( -name '*.out' -o -name '*.in' -o -name '*.out.try?' \) | wc -l)
[ "$left" = 0 ] || stop "uncompressed files in the archive: $left"
x=$W/v2prod_x; rm -rf $x; mkdir -p $x && tar xzf $D/wp1_production/v2prod_structures.tar.gz -C $x
log "3a: archived; $(ls $D/wp3/raw | wc -l) wp3, $(ls $D/wp3/test_extra/raw | wc -l) item-1', $(ls $D/wp3/chk/raw | wc -l) chk files"

# 3b-3c: scripts/33, the m 1e command, once
TH=$($PY scripts/wp3_runbook/rb_test_hosts.py)
log "3b: test hosts: $TH"
if [ ! -e $D/wp3/dataset/dataset_meta.json ]; then
  $PY scripts/33_finetune_dataset.py --dft results/objective2/dopant_shell \
      --frames ../bands $x/v2prod results/objective2/dopant_shell/wp3/frames \
      --out results/objective2/dopant_shell/wp3/dataset --test-hosts $TH --valid-hosts m21 \
      > $W/logs/s33.log 2>&1 || stop "scripts/33 stopped (see logs/s33.log)"
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

# 4b: timing run at 8, 16, 32 threads, 2 epochs each; only wall time is read, outputs deleted
if [ ! -s $W/timing.txt ]; then
  for T in 8 16 32; do d=$W/timing_$T; rm -rf $d; mkdir $d
    t0=$(date +%s); OMP_NUM_THREADS=$T $MT "${ARGS[@]}" --max_num_epochs 2 --work_dir $d > $d.stdout 2>&1 || true; t1=$(date +%s)
    [ -s $d/wp3.model ] || stop "timing run at $T threads did not finish (see $d.stdout)"
    echo "$T $((t1-t0))" >> $W/timing.txt; rm -rf $d $d.stdout
  done
fi
T=$(sort -k2 -n $W/timing.txt | head -1 | cut -d' ' -f1)
log "4b: timing (threads, s for 2 epochs): $(tr '\n' ';' < $W/timing.txt) -> T=$T"

# 4c-4d: training with the start check
RUN=$W/run1; [ -e $RUN ] && stop "$RUN exists"
mkdir $RUN; cd $RUN
OMP_NUM_THREADS=$T nohup $MT "${ARGS[@]}" --max_num_epochs 100 --work_dir $RUN > $RUN.stdout 2>&1 &
pid=$!; echo $pid > $RUN.pid; cd $R
log "4c: training started, pid $pid, threads $T, run $RUN"
until grep -qs '"epoch": null' $RUN/results/wp3_run-123_train.txt || ! kill -0 $pid 2>/dev/null; do sleep 30; done
if $PY scripts/wp3_runbook/rb_startcheck.py $RUN/results/wp3_run-123_train.txt $B > $W/logs/startcheck.txt 2>&1; then
  log "4d: start check PASS: $(cat $W/logs/startcheck.txt)"
else
  kill $pid 2>/dev/null || true; stop "start check FAIL, run killed: $(cat $W/logs/startcheck.txt)"
fi
wait $pid || true
[ -s $RUN/wp3.model ] || stop "training ended without wp3.model (abnormal end: see $RUN.stdout)"
log "4: training finished; wp3.model sha256 $(sha256sum $RUN/wp3.model | cut -c1-64)"

# 5a: technical-failure check (training log, results file, m21 only)
if $PY scripts/wp3_runbook/rb_techfail.py $RUN $DS > $W/logs/techfail.txt 2>&1; then
  log "5a: $(tail -1 $W/logs/techfail.txt)"
else
  stop "technical failure: $(tail -3 $W/logs/techfail.txt | tr '\n' ' ')"
fi
rm -f /data/KEEP_ALIVE
touch $W/STEP34_DONE
log "done"

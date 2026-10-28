#!/bin/bash
# WP3 step 2 driver (PLAN amendment m item 7 step 2; WP3_RUNBOOK.md 2a-2e). Runs on the node as ericdft.
# 2a  scripts/35: one process per training host into its own --frames dir (same params, label seeds),
#     merged into one frames dir, then the literal all-host invocation resumes over it (no new frames).
# 2b  50 item-1' inputs; 2c 8 chk_ inputs; 2d rb_verify_inputs.py must pass; 2e QE chain wp3 wp3x wp3chk.
# Resumable: relaunch by hand after a reclaim. Never edit this file in place while it runs: install a new copy
# under another name, then mv it over this path (the running bash keeps reading the old file).
set -euo pipefail
{   # the whole body is parsed before any of it runs
R=/data/work/ps_wp3; PY=/data/miniforge3/envs/mace/bin/python; W=/data/work/wp3; J=/data/jobs
HOSTS="05 06 08 12 15 20"
mkdir -p $W/frames_parts $W/logs
# one instance only; the lock (fd 8) is inherited by scripts/35 and the QE chain, so a relaunch is also refused while
# a process started by an earlier instance is alive (two scripts/35 writers in one --frames dir clobber each other)
exec 8>>$W/step2.lock; flock -n 8 || { echo "node_step2 already running, or a process it started holds $W/step2.lock" >&2; exit 0; }
[ -e $W/STEP2_DONE ] && { echo "STEP2_DONE exists: nothing to do" >&2; exit 0; }
cd $R
log(){ echo "[$(date -u +%FT%TZ)] $*" >> $W/step2.log; }
on_err(){ c=${BASH_COMMAND%%$'\n'*}; log "STOP: unexpected error (exit $1) at line $2: ${c:0:160}; STEP2_DONE not written"; }
trap 'on_err $? $LINENO' ERR
log "start; repo $(git rev-parse --short HEAD), dirty: $(git status --porcelain | wc -l)"

# 2b: item-1' inputs (no MACE)
for hd in m10:GA m18:GA m04:Sr m14:Sr m27:Sr; do h=${hd%%:*}; d=${hd##*:}
  for s in undoped $d; do for k in 0 2 3 4 6; do L=${h}_${s}_img${k}
    [ -e $J/wp3x/$L/$L.in ] || $PY scripts/30_qe_singlepoint.py ../bands/band_${s}_${h}.extxyz@${k} --label $L --out $J/wp3x/$L >> $W/logs/s30.log 2>&1
  done; done; done
log "2b: $(ls $J/wp3x/*/*.in | wc -l) item-1' inputs"

# 2a: scripts/35 per host, in parallel (10 threads each)
pids=()
for h in $HOSTS; do
  [ -e $W/frames_parts/m$h.done ] && continue
  ( $PY scripts/35_finetune_frames.py --hosts $h --bands ../bands --frames $W/frames_parts/m$h --qe $J/wp3 --threads 10 \
      > $W/logs/s35_m$h.log 2>&1 && touch $W/frames_parts/m$h.done ) &
  pids+=($!)
done
rc=0; for p in "${pids[@]}"; do wait $p || rc=1; done     # wait for every host, so none is left running on exit
[ $rc = 0 ] || { log "2a: a scripts/35 process failed (see logs); all others have ended"; exit 1; }
log "2a: per-host scripts/35 done"

# merge into one frames dir (records in host order, as one all-host process writes them)
if [ ! -e $W/frames/frames_report.json ]; then
  $PY - $W "$HOSTS" <<'EOF'
import glob, json, os, shutil, sys
W, hosts = sys.argv[1], sys.argv[2].split()
parts = [os.path.join(W, "frames_parts", f"m{h}") for h in hosts]
reps = [json.load(open(os.path.join(p, "frames_report.json"))) for p in parts]
assert all(r["params"] == reps[0]["params"] for r in reps), "params differ between parts"
m = {"params": reps[0]["params"], "records": [x for r in reps for x in r["records"]], "source_sha256": {}}
for r in reps:
    m["source_sha256"].update(r["source_sha256"])
labels = [x["label"] for x in m["records"]]
assert len(labels) == 96 and len(set(labels)) == 96, len(labels)
F = os.path.join(W, "frames"); shutil.rmtree(F, ignore_errors=True); os.makedirs(F)   # no report: an earlier merge was cut short
n = 0
for p in parts:
    for f in sorted(glob.glob(os.path.join(p, "*.extxyz"))):
        shutil.copy2(f, F); n += 1
assert n == sum(x["ok"] for x in m["records"]), (n, sum(x["ok"] for x in m["records"]))
os.sync()                                            # the frames reach the disk before the report that marks the merge done
tmp = os.path.join(F, "frames_report.json.tmp")
with open(tmp, "w") as fh:
    json.dump(m, fh, indent=1); fh.flush(); os.fsync(fh.fileno())
os.replace(tmp, os.path.join(F, "frames_report.json"))
fd = os.open(F, os.O_RDONLY); os.fsync(fd); os.close(fd)
print(f"merged {len(labels)} records, {n} frames")
EOF
fi
sha_before=$(sha256sum $W/frames/frames_report.json | cut -c1-64)
$PY scripts/35_finetune_frames.py --hosts $HOSTS --bands ../bands --frames $W/frames --qe $J/wp3 > $W/logs/s35_all_resume.log 2>&1
sha_after=$(sha256sum $W/frames/frames_report.json | cut -c1-64)
[ "$sha_before" = "$sha_after" ] || { log "2a: the all-host resume changed frames_report.json"; exit 1; }
log "2a: all-host resume: $(tail -1 $W/logs/s35_all_resume.log); $(ls $J/wp3/*/*.in | wc -l) WP3 inputs"

# 2c: q = +1 check inputs
for s in Sr undoped; do
  for k in 0 3; do L=chk_m15_${s}_img${k}_q1
    [ -e $J/wp3chk/$L/$L.in ] || $PY scripts/30_qe_singlepoint.py ../bands/band_${s}_m15.extxyz@${k} --charge 1 --label $L --out $J/wp3chk/$L >> $W/logs/s30.log 2>&1; done
  L=chk_m05_${s}_img0_q1
  [ -e $J/wp3chk/$L/$L.in ] || $PY scripts/30_qe_singlepoint.py ../bands/band_${s}_m05.extxyz@0 --charge 1 --label $L --out $J/wp3chk/$L >> $W/logs/s30.log 2>&1
  md=$($PY -c "import json; r={x['label']: x['ok'] for x in json.load(open('$W/frames/frames_report.json'))['records']}; print(next((k for k in ('md450','md300') if r['m05_${s}_'+k] is True), ''))")
  if [ -z "$md" ]; then log "2c: m05_${s}: md450 and md300 both rejected: no (b) job"; continue; fi
  L=chk_m05_${s}_${md}_q1
  [ -e $J/wp3chk/$L/$L.in ] || $PY scripts/30_qe_singlepoint.py $W/frames/m05_${s}_${md}.extxyz@0 --charge 1 --label $L --out $J/wp3chk/$L >> $W/logs/s30.log 2>&1
done
log "2c: $(ls $J/wp3chk/*/*.in | wc -l) chk_ inputs"

# 2d: every input checked before any DFT
if ! $PY scripts/wp3_runbook/rb_verify_inputs.py $J $W/frames > $W/logs/verify_inputs.log 2>&1; then
  log "2d: input check FAILED (see logs/verify_inputs.log); no DFT started"; exit 1
fi
log "2d: $(tail -1 $W/logs/verify_inputs.log)"

# 2e: the DFT, one 64-rank queue at a time (first wait out any queue started outside chain.sh)
log "2e: chain wp3 wp3x wp3chk started"
for c in wp3 wp3x wp3chk; do flock /tmp/qe_queue_$c.lock true; done
/data/setup/chain.sh wp3 wp3x wp3chk
for i in $J/wp3/*/*.in $J/wp3x/*/*.in $J/wp3chk/*/*.in; do b=${i%.in}
  grep -qs "JOB DONE" $b.out || [ -e $b.gaveup ] || { log "2e: $(basename $b) has neither a JOB DONE output nor a .gaveup after the chain: STEP2_DONE not written"; exit 1; }
done
log "2e: chain finished; every input final"
sync; touch $W/STEP2_DONE
exit; }

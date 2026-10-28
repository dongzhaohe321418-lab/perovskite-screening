#!/bin/bash
# Relaunch the WP3 node drivers after a reclaim or reboot (WP3_RUNBOOK.md, "Node drivers used for steps 2-4").
# Installed as /data/work/wp3_relaunch.sh; run as ericdft. It starts nothing while any earlier driver, scripts/35,
# QE or training process is alive, or when a driver stopped for a human (STEP34_STOPPED; a step-2 STOP line).
set -euo pipefail
W=/data/work/wp3
busy=$(pgrep -f '^bash /data/work/wp3_step(2|34)\.sh|35_finetune_frames|qe_queue\.sh|pw\.x|mace_run_train' || true)
[ -z "$busy" ] && busy=$(pgrep -f 'until \[ -e /data/work/wp3/STEP2_DONE \]' || true)
[ -n "$busy" ] && { echo "alive: $(echo $busy): nothing started"; exit 1; }
[ -e $W/STEP34_DONE ] && { echo "STEP34_DONE exists: nothing to do"; exit 0; }
[ -e $W/STEP34_STOPPED ] && { echo "node_step34 stopped for a human: $(grep 'STOP:' $W/step34.log | tail -1)"; exit 1; }
if [ -e $W/STEP2_DONE ]; then
  setsid nohup bash /data/work/wp3_step34.sh > $W/driver34.out 2>&1 < /dev/null &
  echo "node_step34 relaunched (pid $!)"
else
  last=$(tail -1 $W/step2.log)
  case "$last" in *STOP:*|*FAILED*|*failed*|*changed*|*"not written"*) echo "node_step2 stopped: $last"; exit 1;; esac
  setsid nohup bash /data/work/wp3_step2.sh > $W/driver.out 2>&1 < /dev/null &
  echo "node_step2 relaunched (pid $!)"
  setsid nohup bash -c 'until [ -e /data/work/wp3/STEP2_DONE ]; do sleep 120; done; bash /data/work/wp3_step34.sh' \
    > $W/driver34.out 2>&1 < /dev/null &
  echo "STEP2_DONE waiter relaunched (pid $!)"
fi
echo "[$(date -u +%FT%TZ)] relaunch after boot at $(date -u -d @$(awk '/^btime/{print $2}' /proc/stat) +%FT%TZ)" >> $W/relaunch.log

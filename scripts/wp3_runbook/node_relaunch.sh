#!/bin/bash
# Relaunch the WP3 node drivers after a reclaim or reboot (WP3_RUNBOOK.md, "Node drivers used for steps 2-4" and
# "Node driver for step 7"). Installed as /data/work/wp3_relaunch.sh; run as ericdft. It starts nothing while any
# earlier driver, scripts/35, QE (pw.x, neb.x, pp.x, the queue or chain), training, scripts/40 or scripts/41 process
# (or the step-7 spot poller) is alive, or when a driver stopped for a human (STEP34_STOPPED, STEP7_STOPPED; a step-2
# STOP line), or while the item-2 retry runs by hand (train_command_retry.txt without STEP34_DONE: node_step34 is never
# relaunched then). For step 7 it prints the reasons of the driver's last run: its STOP line or, if a reclaim cut its
# wait for the children, its 'STOP pending' lines.
# Step 7 is relaunched only after STEP34_DONE, NOTE_COMMITTED (the committed model note <CNOTE>) and STEP6_DONE (the
# commit <C6> that adds scripts/39's wp3_eval.json, with the checkout updated to it) exist: PLAN amendment m item 7,
# step 6 before step 7. node_step7 itself checks both markers and the commits.
set -euo pipefail
W=/data/work/wp3
busy=$(pgrep -f '^bash /data/work/wp3_step(2|34|7)\.sh|35_finetune_frames|40_wp3b\.py|41_wp3_md\.py|step7-spot-poller|qe_queue\.sh|chain\.sh|pw\.x|neb\.x|pp\.x|mace_run_train' || true)
[ -z "$busy" ] && busy=$(pgrep -f 'until \[ -e /data/work/wp3/STEP2_DONE \]' || true)
[ -n "$busy" ] && { echo "alive: $(echo $busy): nothing started"; exit 1; }
if [ -e $W/STEP34_DONE ]; then
  [ -e $W/STEP7_DONE ] && { echo "STEP7_DONE exists: nothing to do (runbook 7e on the Mac)"; exit 0; }
  # the reasons of the LAST driver run: its final STOP line or, if it was cut short while waiting for its children,
  # every 'STOP pending' line (an older, resolved STOP is never shown)
  if [ -e $W/STEP7_STOPPED ]; then
    why=$(awk '/\] start; boot /{p=""} /\] STOP pending: /{p=p $0 "\n"} /\] STOP: /{p=$0 "\n"} END{printf "%s", p}' $W/step7.log 2>/dev/null || true)
    echo "node_step7 stopped for a human; act on every reason, then start it directly (or rm STEP7_STOPPED and rerun this):"
    if [ -n "$why" ]; then printf '%s\n' "$why"; else cat $W/STEP7_STOPPED; fi
    exit 1
  fi
  miss=""; [ -s $W/NOTE_COMMITTED ] || miss="NOTE_COMMITTED (the model note committed on its own, <CNOTE>)"
  [ -s $W/STEP6_DONE ] || miss="${miss:+$miss and }STEP6_DONE (step 6 done: the commit <C6> that adds wp3_eval.json, with the node checkout updated to it)"
  [ -z "$miss" ] || { echo "STEP34_DONE exists; missing: $miss. Step 7 starts only after the note commit and step 6 (PLAN amendment m item 7): nothing started"; exit 0; }
  setsid nohup bash /data/work/wp3_step7.sh > $W/driver7.out 2>&1 < /dev/null &
  echo "node_step7 relaunched (pid $!)"
else
  # the item-2 retry runs by hand (WP3_RUNBOOK appendix A.5): node_step34 hard-codes --lr 0.005 and would discard the retry run
  [ -e $W/train_command_retry.txt ] && { echo "the item-2 retry runs by hand (train_command_retry.txt exists, no STEP34_DONE; WP3_RUNBOOK appendix A.5): node_step34 is never relaunched now; after a reclaim during the retry follow A.5. Nothing started"; exit 1; }
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
fi
echo "[$(date -u +%FT%TZ)] relaunch after boot at $(date -u -d @$(awk '/^btime/{print $2}' /proc/stat) +%FT%TZ)" >> $W/relaunch.log

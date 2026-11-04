#!/bin/bash
# Relaunch the S2 runner after a spot reclaim or a reboot (results/objective2/s2/S2_PLAN.md section 13; Stage-0
# interface spec 9.2 item 10), in the pattern of scripts/wp3_runbook/node_relaunch.sh. Run as the node user:
#     bash /data/work/ps_s2/ehpc/node/s2_relaunch.sh
# It starts nothing while the S2 lock is held (the runner and every child it starts inherit it) or any S2 process is
# alive (the runner, a scripts/46 or 49 job, the spot poller, the QE queue or chain, run_qe.sh, pw.x; this shell and
# the shell that issued it are not counted, so a compound command such as ssh '...; pgrep -x pw.x' does not match
# itself), or while a campaign is stopped for a human (CAMPAIGN_STOPPED: act on its reason, then start
# s2_campaign.sh directly). Otherwise it relaunches s2_campaign.sh for the one campaign that is running
# (campaign.json status "running" and no CAMPAIGN_DONE). The runner re-derives every job's state from its files.
# A shutdown (SIGTERM) leaves the campaign running for this relaunch; a STOP for a human is SIGINT to the runner.
# When it refuses, a /data/KEEP_ALIVE older than this boot (left by a runner that died with its node) is removed, so
# the idle self-stop applies (round-3 R3-C1-9, N-F25); one written in this boot is kept. A refusal of s2_campaign.sh
# itself (a checkout that is not clean, git failing, the lock taken meanwhile) is such a refusal, and before the first
# start (no /data/work/s2) it refuses with that reason (round 4).
set -euo pipefail
W=/data/work/s2; R=/data/work/ps_s2
KA=${W%/work/s2}/KEEP_ALIVE
stale_ka(){
  local bt m
  bt=$(awk '/^btime/{print $NF}' /proc/stat 2>/dev/null || echo "")
  [ -e "$KA" ] && [ -n "$bt" ] || return 0
  m=$(stat -c %Y "$KA" 2>/dev/null || echo "")
  if [ -n "$m" ] && [ "$m" -lt "$bt" ]; then
    rm -f "$KA" && echo "KEEP_ALIVE from before this boot removed (the idle self-stop applies)"
  fi
  return 0
}
refuse(){ echo "$*"; stale_ka; exit 1; }
[ -d "$W" ] || refuse "no S2 work tree $W: nothing to relaunch (start s2_campaign.sh)"
flock -n "$W/s2.lock" true || refuse "the S2 lock $W/s2.lock is held (a runner or a process it started): nothing started"
busy=""
for p in $(pgrep -f '50_s2_campaign\.py|46_s2_cells\.py|49_s2_gates\.py|s2-spot-poller|qe_queue\.sh|chain\.sh|run_qe\.sh|pw\.x' || true); do
  [ "$p" = "$$" ] || [ "$p" = "$PPID" ] || busy="$busy $p"
done
[ -z "$busy" ] || refuse "alive:$busy: nothing started"
stopped=$(ls -d $W/c?/CAMPAIGN_STOPPED 2>/dev/null || true)
if [ -n "$stopped" ]; then
  echo "stopped for a human; act on every reason, then start s2_campaign.sh directly:"
  for f in $stopped; do echo "$f: $(cat "$f")"; done
  stale_ka
  exit 1
fi
run=""
for c in c1 c2 c3 c4; do
  [ -e "$W/$c/campaign.json" ] || continue
  [ -e "$W/$c/CAMPAIGN_DONE" ] && continue
  grep -q '"status": "running"' "$W/$c/campaign.json" && run="$run $c"
done
set -- $run
[ "$#" = 1 ] || refuse "running campaigns:${run:- none}: nothing started (exactly one is needed)"
c=${run# }
bash "$R/ehpc/node/s2_campaign.sh" "$c" || refuse "s2_campaign.sh refused to start $c: nothing started"
echo "[$(date -u +%FT%TZ)] relaunch of $c after boot at $(date -u -d @$(awk '/^btime/{print $NF}' /proc/stat) +%FT%TZ)" >> $W/relaunch.log

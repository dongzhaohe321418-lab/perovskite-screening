#!/bin/bash
# S2 node runner (results/objective2/s2/S2_PLAN.md sections 13, 16 and 17 item 5; Stage-0 interface spec 9.5).
# Usage, as the node user in the clean checkout at the S2 campaign commit:
#     bash /data/work/ps_s2/ehpc/node/s2_campaign.sh c1        (c1, c2, c3 or c4; one campaign per node boot cycle)
# Starts scripts/50_s2_campaign.py run in its own session and returns; the runner's output goes to
# /data/work/s2/<campaign>/driver.out and its log to /data/work/s2/<campaign>/campaign.log. The lock
# /data/work/s2/s2.lock is taken here on fd 8 and inherited by the runner and every child it starts, so a second
# start is refused while anything the first one started is alive; a reboot releases it. The runner itself creates
# /data/KEEP_ALIVE for the whole campaign and removes it at the end or at a STOP (plan section 16).
# After a reclaim or reboot use s2_relaunch.sh, which refuses while any S2 process is alive.
set -euo pipefail
C=${1:-}
case "$C" in c1|c2|c3|c4) ;; *) echo "usage: s2_campaign.sh c1|c2|c3|c4" >&2; exit 2;; esac
R=/data/work/ps_s2; PY=/data/miniforge3/envs/mace/bin/python; W=/data/work/s2
cd "$R"
[ -z "$(git status --porcelain)" ] || { echo "the checkout $R is not clean: nothing started" >&2; exit 1; }
mkdir -p "$W/$C"
exec 8>>"$W/s2.lock"
flock -n 8 || { echo "another S2 runner, or a process it started, holds $W/s2.lock: nothing started" >&2; exit 1; }
export S2_LOCK_FD=8
setsid nohup "$PY" scripts/50_s2_campaign.py run --campaign "$C" --root /data >> "$W/$C/driver.out" 2>&1 < /dev/null &
echo "S2 runner for $C started (pid $!); log $W/$C/campaign.log"

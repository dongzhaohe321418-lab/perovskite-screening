#!/bin/bash
# S2 node runner (results/objective2/s2/S2_PLAN.md sections 13, 16 and 17 item 5; Stage-0 interface spec 9.5).
# Usage, as the node user in the clean checkout at the c3b campaign commit (results/objective2/s2/S2B_PLAN.md,
# amendment 2026-11-16a; results/objective2/s2/C3B_OPERATIONS.md):
#     bash /data/work/ps_s2/ehpc/node/s2_campaign.sh c3b       (c3b only; one campaign per node boot cycle)
# At this commit only the S2b production campaign c3b starts: fr has ended, C4b is not run, and c1-c4 need a checkout
# at the S2 commit 8bff03e (the runner refuses a c1-c4 start at another HEAD after C2 as well, N-FR3).
# Starts scripts/50_s2_campaign.py run in its own session and returns; the runner's output goes to
# /data/work/s2/<campaign>/driver.out and its log to /data/work/s2/<campaign>/campaign.log. The lock
# /data/work/s2/s2.lock is taken here on fd 8 and inherited by the runner and every child it starts, so a second
# start is refused while anything the first one started is alive; a reboot releases it. The runner itself creates
# /data/KEEP_ALIVE for the whole campaign and removes it at the end or at a STOP (plan section 16).
# After a reclaim or reboot use s2_relaunch.sh, which refuses while any S2 process is alive.
set -euo pipefail
C=${1:-}
case "$C" in c3b) ;; *) echo "usage: s2_campaign.sh c3b (the S2b production campaign; fr has ended; c1-c4 need a checkout at 8bff03e)" >&2; exit 2;; esac
R=/data/work/ps_s2; PY=/data/miniforge3/envs/mace/bin/python; W=/data/work/s2
cd "$R"
# a git failure (no repository, a copy without .git, git's ownership refusal) is a refusal, never 'clean' (round 4)
st=$(git status --porcelain) || { echo "git failed in $R: nothing started" >&2; exit 1; }
[ -z "$st" ] || { echo "the checkout $R is not clean: nothing started" >&2; exit 1; }
git rev-parse --verify -q HEAD >/dev/null || { echo "no HEAD in $R (git failed): nothing started" >&2; exit 1; }
mkdir -p "$W/$C"
exec 8>>"$W/s2.lock"
flock -n 8 || { echo "another S2 runner, or a process it started, holds $W/s2.lock: nothing started" >&2; exit 1; }
export S2_LOCK_FD=8
setsid nohup "$PY" scripts/50_s2_campaign.py run --campaign "$C" --root /data >> "$W/$C/driver.out" 2>&1 < /dev/null &
echo "S2 runner for $C started (pid $!); log $W/$C/campaign.log"

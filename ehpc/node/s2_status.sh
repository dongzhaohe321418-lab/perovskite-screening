#!/bin/bash
# S2 status on the node (Stage-0 interface spec 9.5): whether a runner is alive, the decisions recorded in
# /data/work/s2/state.json, job counts by status, node-hours and the last log lines of each campaign, through
# scripts/50_s2_campaign.py status. It never prints an energy.
set -euo pipefail
cd /data/work/ps_s2
# runner liveness from the S2 lock (held by the runner and every child it starts), not from a process pattern that
# the issuing shell's own command line could match
# (before the first start there is no /data/work/s2, and flock cannot open the lock file: not 'running', round 4)
if [ ! -d /data/work/s2 ]; then r="not started (no /data/work/s2)"
elif flock -n /data/work/s2/s2.lock true; then r="not running (S2 lock free)"; else r="running (S2 lock held)"; fi
echo "runner: $r; KEEP_ALIVE: $([ -e /data/KEEP_ALIVE ] && echo present || echo absent)"
exec /data/miniforge3/envs/mace/bin/python scripts/50_s2_campaign.py status --root /data

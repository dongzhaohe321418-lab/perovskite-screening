#!/bin/bash
# Resumable QE queue: runs every *.in under /data/jobs/<campaign>/ (one level of subdirs) that
# has no finished .out. Safe to restart at any time (spot interruptions): finished = "JOB DONE".
# An input whose run ended without JOB DONE is retried once; after a second failure it is
# skipped and marked <name>.gaveup.  Usage: qe_queue.sh <campaign> [np]
C=${1:?campaign}; NP=${2:-}; D=/data/jobs/$C
exec 9>/tmp/qe_queue_$C.lock; flock -n 9 || { echo "queue $C already running"; exit 0; }
while true; do
  next=""
  for f in $(ls "$D"/*/*.in "$D"/*.in 2>/dev/null | sort); do
    b="${f%.in}"; grep -q "JOB DONE" "$b.out" 2>/dev/null && continue
    [ -e "$b.gaveup" ] && continue
    if [ -e "$b.out" ]; then                      # an earlier attempt ended without JOB DONE
      n=$(ls "$b".out.try* 2>/dev/null | wc -l); mv "$b.out" "$b.out.try$((n+1))"
      [ $((n+1)) -ge 2 ] && { touch "$b.gaveup"; echo "[$(date)] gave up $f"; continue; }
    fi
    next=$f; break
  done
  [ -z "$next" ] && { echo "[$(date)] queue $C: all done"; break; }
  /usr/local/bin/run_qe.sh "$next" "$NP" pw.x
  rm -rf "$(dirname "$next")/tmp"
done

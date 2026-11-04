#!/bin/bash
# S2 pw.x launcher for the runs outside the QE queue: the smoke tests, the throughput row and the A2 parts
# (results/objective2/s2/S2_PLAN.md sections 11, 13, 16; round-4 R4-C1-1, N-F30). Run by scripts/50_s2_campaign.py
# from the checkout; the single points keep the node's /usr/local/bin/run_qe.sh through the committed QE queue.
# It is that node script (the copy kept by the node's operations thread, unchanged on the node when read on
# 2026-10-29) with one addition, an optional core set:
#   CPUSET unset: "mpirun --bind-to core -np <nranks>", as run_qe.sh (one copy on the node);
#   CPUSET set:   "taskset -c <CPUSET> mpirun --bind-to none -np <nranks>", for each of two concurrent 32-rank copies
#                 (the throughput row's np32a/np32b and the A2 layout 2x32), so that the copies use disjoint cores. Two
#                 separate mpirun calls with --bind-to core both bind from core 0. This recipe confined the ranks to
#                 the given cores on the node on 2026-10-27 (OpenMPI 5.0.11); --cpu-set and --map-by pe-list were
#                 refused there.
# Usage: s2_run_qe.sh <input.in> <nranks> [pw.x]; output <input>.out next to the input; prints OK/FAILED from
# "JOB DONE", never from the exit code. The other differences from run_qe.sh: the pseudo_dir rewrite goes through a
# temporary file (the same result as GNU sed -i), and the core set is logged.
set -uo pipefail
set +e                                   # an empty grep must not kill the job
CORES=$(lscpu -p=CORE | grep -v '^#' | sort -u | wc -l)   # physical cores (OpenMPI slots)
IN=${1:?input file}; NP=${2:-$CORES}; EXE=${3:-pw.x}
BIND="--bind-to core"
[ "$NP" -gt "$CORES" ] && BIND="--use-hwthread-cpus --bind-to hwthread"   # more ranks than cores needs SMT slots
source /etc/profile.d/qe.sh
export OMP_NUM_THREADS=1                 # all cores to MPI ranks
ulimit -s unlimited 2>/dev/null
cd "$(dirname "$IN")"; IN=$(basename "$IN"); OUT="${IN%.*}.out"
# QE does not expand environment variables in pseudo_dir: rewrite it to the absolute path
sed -E "s|pseudo_dir *= *'[^']*'|pseudo_dir = '$ESPRESSO_PSEUDO'|" "$IN" > "$IN.pd" && mv -f "$IN.pd" "$IN"
if [ -n "${CPUSET:-}" ]; then
  echo "[$(date)] $EXE -np $NP $IN -> $OUT (cores $CPUSET)" | tee -a run.log
  taskset -c "$CPUSET" "$QE_ENV/bin/mpirun" --bind-to none -np "$NP" "$QE_ENV/bin/$EXE" -inp "$IN" > "$OUT" 2>&1 || true
else
  echo "[$(date)] $EXE -np $NP $IN -> $OUT" | tee -a run.log
  "$QE_ENV/bin/mpirun" $BIND -np "$NP" "$QE_ENV/bin/$EXE" -inp "$IN" > "$OUT" 2>&1 || true
fi
if grep -q "JOB DONE" "$OUT"; then echo "[$(date)] OK $OUT" | tee -a run.log
else echo "[$(date)] FAILED $OUT" | tee -a run.log; fi

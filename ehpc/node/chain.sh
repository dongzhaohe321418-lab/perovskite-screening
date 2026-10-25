#!/bin/bash
# Run QE queues strictly one at a time (never two 64-rank queues at once).
# A global flock serialises every chain; inside it, each campaign queue runs to completion.
# Usage: chain.sh c1 [c2 ...]
for c in "$@"; do
  flock /tmp/qe_chain.global.lock /data/setup/qe_queue.sh "$c" >> /data/jobs/$c/queue.log 2>&1
done

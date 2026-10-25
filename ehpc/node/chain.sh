#!/bin/bash
# Run queues one after another (never two 64-rank queues at once). Usage: chain.sh c1 c2 ...
for c in "$@"; do
  while pgrep -f "qe_queue.sh $c" >/dev/null || pgrep -f "qe_queue.sh" >/dev/null; do sleep 30; done
  /data/setup/qe_queue.sh "$c" >> /data/jobs/$c/queue.log 2>&1
done

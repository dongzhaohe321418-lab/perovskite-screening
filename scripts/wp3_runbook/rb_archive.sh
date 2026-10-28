#!/bin/bash
# RUNBOOK step 3a: archive one pulled queue campaign (<src>/<label>/<label>.{in,out,out.tryN,gaveup}) into a flat
# raw directory, as amendment m 1e asks: <label>.in.gz, <label>.out.gz, <label>.out.tryN.gz (gzipped text) and the
# empty <label>.gaveup marker copied as is. Refuses to overwrite. Usage: rb_archive.sh <src campaign dir> <dest raw dir>
set -euo pipefail
src=$1; dst=$2; mkdir -p "$dst"; n=0
for d in "$src"/*/; do
  L=$(basename "$d")
  [ -e "$d$L.in" ] || { echo "SKIP $d (no $L.in)"; continue; }
  for f in "$d$L.in" "$d$L.out" "$d$L".out.try*; do
    [ -e "$f" ] || continue
    t="$dst/$(basename "$f").gz"; [ -e "$t" ] && { echo "EXISTS $t"; exit 1; }
    gzip -c "$f" > "$t"; n=$((n+1))
  done
  if [ -e "$d$L.gaveup" ]; then
    [ -e "$dst/$L.gaveup" ] && { echo "EXISTS $dst/$L.gaveup"; exit 1; }
    cp "$d$L.gaveup" "$dst/"; n=$((n+1))
  fi
done
echo "archived $n files from $src into $dst"


set -uo pipefail
export LC_ALL=C
source $HOME/miniconda3/etc/profile.d/conda.sh
conda activate qe
export OMP_NUM_THREADS=1
IN=q0_cineb.neb.in
EXPECTED=04acee190675ec82c3d5132a61079506955413afcc4c871b39d4c9d6edfd12c7

echo "=== gate: staged input hash must equal the PI-approved hash ==="
ACT=$(sha256sum $IN | cut -d' ' -f1)
[ "$ACT" = "$EXPECTED" ] || { echo "HASH_MISMATCH: $ACT"; exit 2; }
echo "input verified: $ACT"

mkdir -p run && cp $IN run/
sed -i "s|pseudo_dir = '\$HOME/pseudo'|pseudo_dir = '$HOME/pseudo'|" run/$IN

# watcher: append-only archive whenever neb.path advances; parse-before-archive; verify each;
# persistent failure or image-count anomaly stops the whole job with raw outputs preserved
(
  last=""
  while [ ! -f STOP_WATCH ]; do
    sleep 900
    [ -f run/neb.path ] || continue
    h=$(sha256sum run/neb.path | cut -d" " -f1)
    [ "$h" = "$last" ] && continue
    ok=0
    for try in 1 2; do
      if python3 26_neb_harness.py --mode archive --jobdir run --outdir neb_archive \
           --tag auto --ref-extxyz ref.extxyz > arch_last.json 2>&1; then
        python3 26_neb_harness.py --mode verify --outdir neb_archive > verify_last.json 2>&1 && ok=1 && break
      fi
      sleep 120
    done
    if [ $ok -eq 1 ]; then
      grep -q '"n_images": 5' arch_last.json || { echo "IMAGE_COUNT_ANOMALY"; touch STOP_ALL; break; }
      last=$h
    else
      echo "ARCHIVE_FAIL persistent"; cat arch_last.json; touch STOP_ALL; break
    fi
  done
) &
WATCH=$!

cd run
mpirun -np 64 neb.x -inp $IN > neb.out 2>&1 &
NEB=$!
( while kill -0 $NEB 2>/dev/null; do
    [ -f ../STOP_ALL ] && { echo "guard stop"; kill $NEB; break; }
    sleep 300
  done ) &
wait $NEB || true
cd ..
touch STOP_WATCH; wait $WATCH 2>/dev/null || true
[ -f STOP_ALL ] && { echo "JOB_STOPPED_BY_GUARD"; exit 5; }

grep -q "JOB DONE" run/neb.out || { echo "NEB_FAIL"; tail -30 run/neb.out; exit 3; }
python3 26_neb_harness.py --mode archive --jobdir run --outdir neb_archive --tag final \
  --ref-extxyz ref.extxyz > arch_final.json 2>&1 || exit 4
python3 26_neb_harness.py --mode verify --outdir neb_archive > verify_final.json 2>&1 || exit 4
grep -E "neb: convergence|reached the maximum|activation" run/neb.out | tail -4
tar czf neb_archive.tar.gz neb_archive run/neb.out run/neb.dat arch_final.json verify_final.json
echo "PRODUCTION_NEB_COMPLETE"

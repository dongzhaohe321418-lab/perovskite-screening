#!/bin/bash
#SBATCH -J qe-production
#SBATCH -p comp
#SBATCH -N 1
#SBATCH --ntasks-per-node=32
#SBATCH -t 04:00:00
#SBATCH -o %x-%j.out
#SBATCH -e %x-%j.err

set -euo pipefail
export LC_ALL=C
QE_ENV="$HOME/mamba/envs/qe"
export PATH="$QE_ENV/bin:$PATH"
export LD_LIBRARY_PATH="$QE_ENV/lib:${LD_LIBRARY_PATH:-}"
export OMP_NUM_THREADS=1

cd "$SLURM_SUBMIT_DIR"
mpirun -np "$SLURM_NTASKS" "$QE_ENV/bin/pw.x" -in input.pwi > output.pwo

#!/bin/bash
#SBATCH -J qe-multinode
#SBATCH -p comp
#SBATCH -N 2
#SBATCH --ntasks-per-node=2
#SBATCH -t 00:05:00
#SBATCH -o qe-multinode-%j.out
#SBATCH -e qe-multinode-%j.err

set -euo pipefail
export LC_ALL=C
QE_ENV="$HOME/mamba/envs/qe"
export PATH="$QE_ENV/bin:$PATH"
export LD_LIBRARY_PATH="$QE_ENV/lib:${LD_LIBRARY_PATH:-}"
export OMP_NUM_THREADS=1

echo "job_id=$SLURM_JOB_ID"
echo "nodes=$SLURM_JOB_NODELIST"
echo "tasks=$SLURM_NTASKS"
mpirun -np "$SLURM_NTASKS" "$QE_ENV/bin/pw.x" -in h2.pwi > h2-multinode.pwo

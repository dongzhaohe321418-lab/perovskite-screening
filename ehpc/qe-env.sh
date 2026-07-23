export LC_ALL=C
export MAMBA_ROOT_PREFIX="$HOME/mamba"
export QE_ENV="$HOME/mamba/envs/qe"
export PATH="$QE_ENV/bin:$PATH"
export LD_LIBRARY_PATH="$QE_ENV/lib:${LD_LIBRARY_PATH:-}"

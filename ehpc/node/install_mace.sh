#!/bin/bash
set -x
source /data/miniforge3/etc/profile.d/conda.sh
[ -d /data/miniforge3/envs/mace ] || /data/miniforge3/bin/mamba create -y -q -n mace python=3.12 >/dev/null
conda activate mace
pip install -q --timeout 120 torch --index-url https://mirrors.aliyun.com/pytorch-wheels/cpu/ 2>&1 | tail -2 || true
python -c "import torch" 2>/dev/null || pip install -q --timeout 120 torch --index-url https://download.pytorch.org/whl/cpu 2>&1 | tail -2
pip install -q --timeout 120 -i https://pypi.tuna.tsinghua.edu.cn/simple mace-torch ase numpy scipy 2>&1 | tail -2
python -c "import torch, mace, ase; print(\"MACE-ENV-OK torch\", torch.__version__, \"threads\", torch.get_num_threads())"

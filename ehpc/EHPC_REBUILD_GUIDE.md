# E-HPC 重建指南 — 复现已跑通生产 CI-NEB 的 QE-on-Slurm 环境

**目标:** 精确复现这套已经完成两条 159/232-atom 生产 CI-NEB 的 Quantum ESPRESSO + Slurm 环境。
本指南编码了 2026-07 整个 DFT campaign 中逐条验证出的全部配置与陷阱修复——不是泛泛的教程,
而是"照做就能得到与旧环境 bit-for-bit 一致能量"的复现说明。

**故障现状(2026-08-05):** `ssh 139.224.62.26:22 Operation timed out` —— 登录节点本身失联,
不只是 Slurm 控制器。若只是 Slurm 坏、SSH 通,直接跳到 **§B(仅修 Slurm)**;若整机重建,从 **§A** 开始。

---

## 目标环境规格(重建后应达到的状态)

| 项 | 值 | 来源 |
|---|---|---|
| 平台 | Aliyun E-HPC | — |
| 登录节点 | 2 cores, 3.6 GB(thin) | 仅做安装/下载,不跑计算 |
| 计算分区 | `comp`:2 nodes × 32 cores × 62 GB,infinite walltime,无 GRES(纯 CPU) | verified |
| 调度器 | Slurm,`#SBATCH --partition=comp` | — |
| 家目录 | 10 PB Aliyun NAS `/home`,登录+计算节点共享 | 登录节点装的东西计算节点可见 |
| scratch | `/home/ericdft/scratch` | — |
| **网络拓扑** | **计算节点 AIR-GAPPED(无外网),仅登录节点可联网** | CRITICAL |
| OS | 老 CentOS/RHEL7,**GLIBC 2.17** | 决定 conda 安装器版本 |
| QE | 7.5,conda env `qe` | verified `PWSCF v.7.5` |
| MPI | conda-forge OpenMPI(用 `mpirun`,不用 `srun`) | verified |

---

## §A 整机重建(登录节点重装)

### A1. 基本探活(SSH 恢复后第一件事)
```bash
hostname; whoami; uptime; nproc; free -g
ls -d /home/ericdft /home/ericdft/scratch    # NAS home 是否挂载
ldd --version | head -1                        # 确认 GLIBC 版本(应 2.17)
```

### A2. 安装 Miniconda(GLIBC 2.17 关键陷阱)
**最新 Miniconda 需要 GLIBC≥2.28,在这台机器上会失败。** 必须用旧安装器:
```bash
cd $HOME
curl -sSL -o mc.sh https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-py38_4.12.0-Linux-x86_64.sh
bash mc.sh -b -p $HOME/miniconda3
source $HOME/miniconda3/etc/profile.d/conda.sh
```

### A3. 配置国内镜像(conda-forge 直连被墙)
```bash
cat > $HOME/.condarc <<'EOF'
channels:
  - defaults
default_channels:
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r
custom_channels:
  conda-forge: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
EOF
```

### A4. 安装 QE 7.5(含 OpenMPI)
```bash
conda create -n qe -y -c conda-forge qe=7.5
conda activate qe
which pw.x mpirun neb.x pp.x projwfc.x     # 全部应在 $HOME/miniconda3/envs/qe/bin/
pw.x -h 2>&1 | head -3                       # 应打印 PWSCF v.7.5
```
**注意:全部装在共享 NAS home 上**——登录节点装一次,两个计算节点都能用。不要装到本地盘。

### A5. 下载赝势(pslibrary 1.0.0 US scalar-rel PBE)
从 QE 官方源(登录节点可达,返回 200,**不要**用任何网络加速):
```bash
mkdir -p $HOME/pseudo && cd $HOME/pseudo
BASE=https://pseudopotentials.quantum-espresso.org/upf_files
for f in Cs.pbe-spn-rrkjus_psl.1.0.0.UPF \
         Pb.pbe-dn-rrkjus_psl.1.0.0.UPF \
         I.pbe-n-rrkjus_psl.1.0.0.UPF \
         C.pbe-n-rrkjus_psl.1.0.0.UPF \
         H.pbe-rrkjus_psl.1.0.0.UPF \
         N.pbe-n-rrkjus_psl.1.0.0.UPF; do
  curl -sSL -o "$f" "$BASE/$f" && echo "got $f"
done
```
**赝势陷阱(必须核对 z_valence):**
- Cs 用 **`Cs.pbe-spn`**,**不要** `spnl`——spnl 变体 z_valence 损坏为 **-5**。
- 正确 z_valence:Cs=9, Pb=14, I=7, C=4, H=1, N=5。核对:
```bash
for f in Cs.pbe-spn Pb.pbe-dn I.pbe-n C.pbe-n H.pbe N.pbe-n; do
  p=$(ls ${f}*.UPF 2>/dev/null|head -1)
  echo "$p: $(grep -oE 'z_valence="[ ]*[0-9]+\.[0-9]+' "$p"|grep -oE '[0-9]+\.[0-9]+')"
done
```
生产 cutoff:**ecutwfc 50 / ecutrho 400 Ry**。

### A6. 冒烟测试(单原子 Pb SCF,验证 mpirun 通)
在**计算节点**(不是登录节点)跑,因为登录节点太薄:见 §C 的提交模板,用 1-atom Pb SCF,
期望 `JOB DONE`,能量与 AutoDL 端一致到 5 位小数。

---

## §B 仅修 Slurm(SSH 通、`sinfo` 报 connect failure)

症状:`slurm_load_partitions: Unable to contact slurm controller (connect failure)`,
且 `Ignoring ControlMachine since SlurmctldHost is set`。

### B1. 诊断
```bash
scontrol ping                                    # 控制器是否响应
grep -iE "SlurmctldHost|ControlMachine" /etc/slurm/slurm.conf
systemctl status slurmctld 2>/dev/null || sudo systemctl status slurmctld
sinfo -N                                          # 计算节点是否可见
```

### B2. E-HPC 上多为托管调度器
Aliyun E-HPC 的 Slurm 控制器通常跑在一个**独立的管理节点**上,由 E-HPC 控制台管理,
不是你能 `systemctl restart` 的。如果 `scontrol ping` 失败:
1. **优先走 Aliyun E-HPC 控制台**:检查集群状态、管理节点是否宕、是否欠费/被停。
   控制台"重启集群 / 重启调度器"通常能恢复,且**不动共享 NAS home**(QE/赝势/scratch 都在 NAS,安全)。
2. 若你有管理节点 root:`sudo systemctl restart slurmctld`,再 `sudo systemctl restart slurmd`(各计算节点)。
3. `slurm.conf` 的 `SlurmctldHost` 必须指向存活的管理节点主机名;E-HPC 重建集群后该名可能变。

### B3. 关键:共享 NAS home 让重建代价很小
因为 QE env、赝势、scratch 全在 `/home`(10 PB NAS,跨节点共享),**即便重建整个计算集群,
只要 NAS 还挂着,§A4–A5 都不必重做**——重建后 `conda activate qe` 直接可用。这是这套环境最省的一点。

---

## §C 提交模板(踩坑修复已内联,照抄)

每一条都是验证出来的,少一条就可能丢一次计算。

### C1. 生产 SCF/NEB 作业脚本骨架
```bash
#SBATCH --partition=comp
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=32
# 159/232-atom V_I cell 需要 ~132 GB > 单节点 62 GB,必须跨 2 节点

set -uo pipefail
set +e                        # ★ 陷阱1:runner 强制 errexit,必须显式关掉,否则一个空 grep 杀全局
export OMP_NUM_THREADS=1       # ★ 陷阱2:让 32 核全给 MPI rank,不给 OpenMP

# ★ 陷阱3:用 conda qe,绝不用 Intel oneAPI setvars(它在 set -e 下退出非零杀作业)
source $HOME/miniconda3/etc/profile.d/conda.sh && conda activate qe

# ★ 陷阱4:QE 不展开 $HOME,运行时改写 pseudo_dir
sed -i "s|pseudo_dir = '\$HOME/pseudo'|pseudo_dir = '$HOME/pseudo'|" input.in

# ★ 陷阱5:用 conda 的 mpirun -np 64,绝不用 srun --mpi=pmi2(PMIx 不匹配 -> OPAL ERROR)
mpirun -np 64 pw.x -inp input.in > out.pwo 2>&1 || true    # ★ 陷阱6:capped NEB 正常退出非零,|| true 保护

# ★ 陷阱7:成功判据用 grep JOB DONE,不用 exit code
grep -q "JOB DONE" out.pwo && echo "OK" || echo "FAILED"
# ★ 陷阱8:任何进度 grep 都要 || true 守护
NMAG=$(grep -c "absolute magnetization" out.pwo 2>/dev/null || echo 0)
```

### C2. 内存/rank 放置(硬约束)
- 159/232-atom cell:`--nodes=2 --ntasks-per-node=32` + `mpirun -np 64`(32 ranks/node)。
- **不要**用 `--ntasks-per-node=16`——每 rank 内存过大,高 cutoff 会在第一步 Davidson 被 OOM(exit 137)。
- QE 的 "Estimated total dynamical RAM" 是**上界**;132 GB 估算实际能装进 2×62=124 GB,但 >124 GB 有风险,continue-on-error 并盯着。
- 该 cell 一个作业吃满整个集群,**同一时刻只能跑一个**——把多 image 的 SCF 串在一个作业的循环里,别并发提交。

### C3. nspin=2(奇电子 V_I⁰ / CBM-like)
- FA host 的 undoped V_I⁰:1063 电子(奇)→ `nspin=2, tot_magnetization=1`,Pb 上 `starting_magnetization=0.3`,其余 0。
- nspin=2 比 nspin=1 估算更耗内存(两个自旋通道);必要时把 `nbnd` 压到略高于较大自旋通道(`nelup`+few)。`nbnd`/`disk_io` 不改哈密顿量,可安全调。
- **链式后处理必须 `disk_io='medium'`**(`low` 会抑制 projwfc/pp/dos 需要的 `.save`),且后处理步显式非致命(`... || echo FAILED`)。
- **绝不**用不同几何的 nspin=1 密度 restart nspin=2(会发散到 ~10⁶ Ry / ~7000 μB 的数值垃圾);同几何 restart 反而 6 步收敛。无磁物种却出现几 μB 以上磁化就立刻停查。

### C4. 长 SCF 监控
从运行中的 `.out` 读进度,不等作业结束:
```bash
grep 'estimated scf accuracy' out.pwo | tail -5     # 收敛轨迹
grep 'total energy  ' out.pwo | tail -3             # 未收敛迭代无 ! 标记
```

---

## §D scratch 与产物

- `/home/ericdft/scratch/.claude-science/jobs` 每提交一个作业一个目录,**不自动清理**——几天 DFT campaign 可达 151 GB(QE `out/` 波函数占大头)。NAS 10 PB 不急,但删前问,某目录可能是 `neb.path`/`.save` restart 的唯一副本。
- 大文件用作业框架的 `outputs=`(rsync)取回,**不要** base64 过 `call_command`(stdout 有上限,会静默截断成损坏解码)。已完成作业用 `split -b` 分块再拼。

---

## §E 重建后验证清单(逐项打勾才算复现)

- [ ] `conda activate qe && pw.x -h` → `PWSCF v.7.5`
- [ ] 6 个赝势齐全且 z_valence 正确(Cs=9/Pb=14/I=7/C=4/H=1/N=5,Cs 是 **spn** 非 spnl)
- [ ] `sinfo` 显示 `comp` 分区 2 节点 idle
- [ ] 单原子 Pb SCF 跨节点 `mpirun -np 8 pw.x` → `JOB DONE`,能量匹配旧值 5 位小数
- [ ] `/home/ericdft/scratch` 可写
- [ ] 一条 159-atom V_I SCF 用 §C1 骨架 → `JOB DONE`,能量与旧生产值 bit-for-bit 一致

**最后一项通过 = 环境已精确复现,可继续 A2a 及后续 DFT。**

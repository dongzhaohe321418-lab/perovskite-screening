# 阿里云 E-HPC 实际部署与 Mac mini / Claude Science 连接手册

更新日期：2026-07-23。本文记录已经创建的真实环境，不再是创建前的预案。

## 1. 已部署架构

```text
Mac mini
 ├── ssh autodl -> AutoDL GPU / MLIP
 └── ssh ehpc   -> E-HPC 登录节点 -> Slurm comp 队列 -> 2 台计算节点
```

| 项目 | 实际值 |
|---|---|
| 集群名称 | `perovskite-dft` |
| 集群 ID | `ehpc-sh-j9sajnjxye` |
| 地域 / 可用区 | 华东 2（上海）/ `cn-shanghai-o` |
| 部署方式 | 精简 |
| 调度器 | Slurm 22，分区 `comp` |
| 镜像 | CentOS 7.9 64 位 |
| 登录节点 | `ecs.c7nex.large`，2 vCPU / 4 GB |
| 计算节点 | `2 x ecs.c7nex.8xlarge`，每台 32 vCPU / 64 GB |
| 计算资源合计 | 64 vCPU / 128 GB，静态节点 2/2 |
| 公网 IP | `139.224.62.26` |
| 普通用户 | `ericdft` |
| VPC | `vpc-uf6o7m3zuf0udt3rdflrp` (`Claudescience`) |
| 交换机 | `vsw-uf6pecwmx53v2s35a0idi` |
| 安全组 | `ehpc-sg` |
| NAS | `031y61oa5ol6dno1zsz-dbn98.cn-shanghai.nas.aliyuncs.com` |

原定的单台 `ecs.c7nex.16xlarge` 因上海 O 区无库存而创建失败。最终使用两台
32 核节点，总核数和总内存保持 64 vCPU / 128 GB。账号原有按量 vCPU 配额为
50；已申请并获批提升至 66，刚好覆盖 2 核登录节点和 64 核计算节点。

## 2. 成本和关机纪律

- 两台计算节点控制台报价约 `¥16.48/小时`；登录节点、NAS 和 EIP 另计。
- 当前计算节点是静态按量节点，不会在空闲时自动释放；连续运行一天仅计算节点
  约 `¥395.52`。
- 不计算时必须在 E-HPC / ECS 控制台停止或释放计算节点。释放前确认数据已写入
  `/home` 或 `/ehpcdata` 的 NAS；实例本地系统盘不作为科研数据存储。
- 若以后改为自动伸缩，应设置最小节点数 0，并重新评估抢占式实例、库存和配额。

## 3. Mac mini SSH（已完成）

`~/.ssh/config` 已加入：

```sshconfig
Host ehpc
    HostName 139.224.62.26
    Port 22
    User ericdft
    IdentityFile /Users/ericdong/.ssh/id_ed25519
    IdentitiesOnly yes
    ServerAliveInterval 60
    ServerAliveCountMax 3
    StrictHostKeyChecking accept-new
```

公钥已经复制到集群。验证命令：

```bash
ssh ehpc 'whoami; hostname; sinfo'
```

期望结果包含 `ericdft`、登录节点 `manager`，以及 `compute[001-002]` 为 `idle`。

## 4. NAS 与工作目录

实际共享挂载：

```text
/home     <- NAS:/ehpc-sh-j9sajnjxye/home
/opt      <- NAS:/ehpc-sh-j9sajnjxye/opt
/ehpcdata <- NAS:/
```

推荐目录：

```text
/home/ericdft/scratch   计算工作目录 / Claude Science scratch
/home/ericdft/jobs      Slurm 脚本
/home/ericdft/pseudos   SSSP / 元素赝势
/home/ericdft/mamba     micromamba 根目录和 QE 环境
```

所有输入、赝势、检查点和输出都应放在这些 NAS 路径中。

## 5. Quantum ESPRESSO 环境

QE 安装为共享环境：

```text
/home/ericdft/mamba/envs/qe
```

登录后激活：

```bash
export MAMBA_ROOT_PREFIX="$HOME/mamba"
eval "$("$HOME/miniforge3/micromamba" shell hook -s bash)"
micromamba activate qe
pw.x -h | head
```

或在脚本中直接使用：

```bash
QE_ENV="$HOME/mamba/envs/qe"
"$QE_ENV/bin/pw.x" -h | head
```

## 6. Slurm 作业模板

单节点 32 MPI rank：

```bash
#!/bin/bash
#SBATCH -J qe-test
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
```

跨两节点总计 64 rank 时改为：

```bash
#SBATCH -N 2
#SBATCH --ntasks-per-node=32
```

当前 Conda OpenMPI 已通过 `mpirun` 在 Slurm 分配内验证；不要在登录节点直接运行
大规模 `mpirun`。常用命令：

```bash
sinfo
squeue -u "$USER"
sbatch job.sbatch
sacct -j JOB_ID --format=JobID,State,Elapsed,ExitCode
scancel JOB_ID
```

## 7. Claude Science 在 Mac mini 上注册

1. 先在终端验证 `ssh ehpc 'sinfo'` 成功且不再询问密码。
2. Claude Science 打开 `Customize -> Compute`。
3. 新增 SSH 计算后端，地址填写 `ssh:ehpc`（若界面拆分字段，Host 填
   `ehpc`，连接方式选 SSH）。
4. 用户名由 `~/.ssh/config` 提供，为 `ericdft`；不要在 Claude Science 中保存
   root 密码。
5. Working / scratch directory 填：

   ```text
   /home/ericdft/scratch
   ```

6. 初始化或探测命令可用：

   ```bash
   export MAMBA_ROOT_PREFIX="$HOME/mamba"
   export PATH="$HOME/mamba/envs/qe/bin:$PATH"
   ```

7. 保存后做最小测试：运行 `hostname`、`sinfo`、`pw.x -h | head`。

## 8. 赝势与首批 DFT 任务

SSSP 1.3.0 PBE Efficiency 已下载并通过官方 MD5 校验，目录为：

```text
/home/ericdft/pseudos/SSSP_1.3.0_PBE_efficiency
```

钙钛矿主体元素文件：

```text
Cs_pbe_v1.uspp.F.UPF
Pb.pbe-dn-kjpaw_psl.0.2.2.UPF
I.pbe-n-kjpaw_psl.0.2.UPF
```

输入文件中的 `pseudo_dir` 必须指向上述绝对路径，并按候选掺杂元素补齐
`ATOMIC_SPECIES`。归档包保留在 `/home/ericdft/pseudos/`，官方 MD5 为
`a58f1b3373f330179fd0832c48bb9a52`。

首批任务：

1. gamma-CsPbI3 截断能和 k 点收敛；
2. 2x2x2 超胞中的带电 `V_I+` 单点；
3. FNV 修正与超胞尺寸外推；
4. 将结构、能量、力和应力回流到 AutoDL 的 MLIP 数据集。

## 9. 安全与故障检查

- 将 `ehpc-sg` 的 TCP 22 来源收紧到可信公网 IP；家庭出口 IP 变化后同步更新。
- SSH 不通：检查 EIP、安全组和 `ssh -vv ehpc`。
- Slurm 节点异常：`sinfo -R`、`scontrol show node compute001`。
- MPI 作业失败：先用 1 节点 2 rank 最小测试，再扩到 32/64 rank。
- `pw.x` 缺赝势：检查 `pseudo_dir`、文件名和元素覆盖。
- 磁盘文件在计算节点不可见：确认路径位于 `/home`、`/opt` 或 `/ehpcdata`。

密码不写入本文件、SSH 配置、脚本或 Git 仓库。

# 阿里云 E-HPC 配置指南(DFT 腿)

写于 2026-07-23。目标:为钙钛矿掺杂剂筛选项目搭起 DFT 计算腿(Quantum ESPRESSO
+ Slurm),与 AutoDL 的 GPU/MLIP 腿并行。执行环境:Mac mini(claudescience)。

```
Mac mini(指挥部)
 ├── ssh:autodl → RTX 5090(AutoDL)     MLIP:NEB farm / 微调 / MD
 └── ssh:ehpc   → Slurm CPU 集群(E-HPC)  DFT:QE 单点 / 收敛测试 / HSE 抽查
```

地域:华东2(上海)。已知决策:按量付费、精简部署、Slurm。

---

## 0. 前置资源(创建集群前必须存在)

1. **VPC + 交换机**(免费):VPC 网段 `192.168.0.0/16`;交换机**必须在上海
   可用区 O**(与集群同可用区,选错建不出集群),网段 `192.168.0.0/24`。
2. **NAS 文件系统**(通用型)+ 挂载点:NAS 控制台创建,**同样选上海可用区 O**。
   这是所有节点的共享盘,家目录和 scratch 都在上面。

## 1. 创建集群(E-HPC 控制台)

硬件配置页:

| 项 | 值 | 备注 |
|---|---|---|
| 付费类型 | 按量付费 | |
| 部署方式 | 精简 | 管控节点托管,省钱 |
| 登录节点 | ecs.c7nex.large(2c4G)×1 | 唯一常开节点,够用 |
| **计算节点** | **32–64 vCPU 计算型(c8i 档),数量 0** | ⚠️ 2c4G 跑不了 QE;数量填 0,算力全交给弹性伸缩 |
| 系统盘 | ESSD 40GB PL0 | |
| 弹性公网IP | 使用 | mini SSH 全靠它 |
| VPC/交换机 | 选第 0 步建的 | |
| 安全组 | 新建,名 `ehpc-sg`(英文) | |
| 共享存储 | 通用型 NAS,NFS v3,远程目录 `/` | 选第 0 步建的文件系统 |

软件配置页:调度器 **Slurm**;镜像 Alibaba Cloud Linux 3 或 Rocky。
基础配置页:集群名、root 密码(设强密码,之后基本不用)。

**确认提交前核对配置清单总价:改完后应只剩登录节点 ≈¥0.6/小时量级。**

## 2. 建成后立即做的三件事

1. **若向导强制创建了静态计算节点 → 手动释放它**。自动缩容只回收弹性扩出的
   节点,静态节点会 7×24 烧钱;
2. **队列自动伸缩**:队列管理 → 打开自动伸缩,最小节点数 **0**、最大 4,
   扩容实例规格选 32–64 vCPU 计算型,**计费方式选抢占式(Spot)**;
3. **安全组收紧**:`ehpc-sg` 的 22 端口授权对象从 `0.0.0.0/0` 改成家庭宽带
   出口 IP(IP 变了回来改)。

> ⚠️ 配额陷阱:新账号的按量/抢占式 vCPU 配额可能低于 64。若扩容时报配额错误,
> 去「配额中心」把对应实例族的按量 + 抢占式 vCPU 配额提到 ≥128(免费,秒批)。

## 3. 集群用户

控制台 → 集群 → 用户 → 创建用户 `eric`(普通权限,设一次性密码)。
**跑作业用 eric,不用 root。**

## 4. Mac mini 打通 SSH(mini 终端整段粘贴,`<EIP>` 换成登录节点公网 IP)

```bash
grep -q "Host ehpc" ~/.ssh/config 2>/dev/null || cat >> ~/.ssh/config <<'EOF'
Host ehpc
    HostName <EIP>
    Port 22
    User eric
    ServerAliveInterval 60
    StrictHostKeyChecking accept-new
EOF
chmod 600 ~/.ssh/config
ssh-copy-id -i ~/.ssh/id_ed25519.pub ehpc      # 输一次 eric 的密码
ssh ehpc "sinfo && df -h | grep -v tmpfs"       # 验证 Slurm + NAS 挂载路径
```

记下 `df -h` 里 NAS 的实际挂载路径(下称 `<NAS>`,如 `/ehpcdata`)。

## 5. claudescience 注册计算后端

Customize → Compute → 添加 `ssh:ehpc`,**注册时当场填 scratch/working
directory**(AutoDL 的教训):

```
<NAS>/eric/scratch        # 先 ssh ehpc "mkdir -p <NAS>/eric/scratch"
```

必须放 NAS——计算节点是弹性临时机,本地盘不共享不持久。

## 6. 安装 Quantum ESPRESSO(登录节点,装进家目录=装在 NAS 上,全节点可见)

```bash
ssh ehpc
wget -q https://mirrors.tuna.tsinghua.edu.cn/github-release/conda-forge/miniforge/LatestRelease/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh -b -p ~/miniforge3 && ~/miniforge3/bin/conda init bash && source ~/.bashrc
conda create -n qe -c conda-forge qe openmpi -y
conda activate qe && pw.x -h | head -3
```

**赝势**:下载 SSSP PBE Efficiency 赝势库(Materials Cloud;国内慢就逐个从
QE 官网/GBRV 补 Cs/Pb/I 及掺杂剂元素),放 `<NAS>/eric/pseudos/`,输入文件里
`pseudo_dir` 指向它。

性能说明:conda-forge 预编译 QE 足够收敛测试;后期要压性能再用 Intel oneAPI
重编译,不要现在做。

## 7. Slurm 作业模板

`<NAS>/eric/scratch/job_template.sbatch`:

```bash
#!/bin/bash
#SBATCH -J qe-VI-charged
#SBATCH -p comp                # 分区名以 sinfo 为准
#SBATCH -N 1
#SBATCH --ntasks=32            # 与扩容实例 vCPU 一致
#SBATCH -t 04:00:00
source ~/miniforge3/etc/profile.d/conda.sh && conda activate qe
cd $SLURM_SUBMIT_DIR
mpirun -np $SLURM_NTASKS pw.x -in input.pwi > output.pwo
```

`sbatch` 提交 → 自动伸缩现开抢占式节点(2–5 分钟)→ 跑完闲置几分钟自动释放。
常用:`squeue`(排队)、`sacct`(历史)、`scancel <id>`(杀作业)。
抢占式节点偶尔会被回收,作业重提即可——单点计算无状态,天然耐抢占。

## 8. 首批科学任务(衔接 proposal 第 1–2 月)

1. γ-CsPbI₃ 原胞:截断能 / k 点收敛曲线(PBE+D3);
2. 2×2×2 超胞 V_I⁺ 带电单点:FNV 修正(用 `doped` 包生成与分析),
   对照文献 ~0.1 eV 修正量级;
3. 超胞尺寸外推测试(2×2×2 → 3×3×3);
4. 产出的 DFT 数据即是 MLIP 微调训练集的第一批原料(回流到 AutoDL 腿)。

## 9. 成本与纪律

- 常开:登录节点(≈¥0.6/时)+ NAS(几十 GB≈每月几元)+ EIP(按流量,可忽略)
  → **每天约十几元**;
- 计算:只在作业运行时发生;抢占式 64 vCPU ≈ ¥2–4/时。全部 DFT 腿预算估
  **¥1000–2000**(比 MLIP 腿贵一个量级是正常结构);
- 三条铁律:① 确认队列最小节点数=0;② 静态计算节点清零;③ 连续几天不用时
  登录节点也停机(停机不收计算费,数据在 NAS 不丢)。
- E-HPC 是 CSD3 批复前的过渡:Slurm 脚本改个分区名即可整体迁移。

## 10. 故障速查

| 症状 | 第一嫌疑 |
|---|---|
| ssh 连不上 | 安全组 22 端口源 IP 不含当前网络;EIP 填错 |
| 提交作业不扩容 | vCPU 配额不足(配额中心);队列伸缩开关没开 |
| 节点上找不到文件 | 文件放了本地盘而非 NAS;`df -h` 核对 |
| 作业半途消失 | 抢占式被回收,`sacct` 确认后重提 |
| pw.x 报赝势缺失 | `pseudo_dir` 路径或元素赝势文件缺 |

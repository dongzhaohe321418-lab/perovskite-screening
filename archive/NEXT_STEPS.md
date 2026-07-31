> # SUPERSEDED — archived (bannered 2026-07-28)
>
> Early execution guide (Objective 1 → FA screening transition), written before the relaxed-NEB campaign and the paired design.
>
> **Current authority: `NEXT_STEP_GUIDE.md + RESULTS_INDEX.md`.** Retained verbatim below for provenance; do not cite as current.

# 下一步执行指南：从 Objective 1 到 FA₀.₉₅Cs₀.₀₅PbI₃ 筛选

**更新：2026-07-23**

本指南以当前仓库为起点：γ-CsPbI₃ zero-shot CI-NEB、GA构型采样、应变与有限尺寸检查、PBE固定几何DFT、E-HPC集群和文献综述均已完成或部署。本文件规定下一阶段的执行顺序、验收标准和停止条件。

当前一句话定位：

> Pipeline 已跑通；zero-shot趋势有价值；DFT已证明MACE-MP-0的绝对势垒不能直接用于生产排名；电荷态DFT链路已跑通，但尚未得到各自弛豫的q=0/q=+1最小能量迁移路径。

不要在完成 Stage 3 前开始50种候选的正式排行榜。

---

## 1. 当前证据与准确状态

| 模块 | 已有结果 | 目前允许的结论 |
|---|---|---|
| γ-CsPbI₃ baseline | MACE 0.259 eV，159原子、float64 CI-NEB | 脚本、路径生成和数值回归可用；0.259 eV不是最终物理势垒 |
| DFT-vs-MACE | 同一MACE路径上PBE 0.141 eV，MACE 0.259 eV | MACE在该**固定路径**上比PBE高118 meV；不能直接用于绝对势垒排名 |
| 带电固定路径 | q=0为140.6 meV，q=+1为126.6 meV | 固定核坐标下移除电子使该路径低约14 meV；不是Tyagi的完整电荷态迁移比较 |
| GA | 三个near取向均正：+70/+182/+278 meV；far约−23 meV | γ-CsPbI₃内的局域pinning符号稳健；量级构型和尺寸敏感 |
| 应变 | 双轴拉伸降、压缩升；+1%张应变约−41 meV且尺寸一致 | 这是当前最稳健的zero-shot趋势结果 |
| 立方相候选试筛 | Ba/Ca/Sr/Bi/Br在匹配小胞构型中均降势垒 | 是机制探索/筛选tier，不能当最终宿主的生产排名 |

### 仍不能宣称完成的事项

- 完整DFT-NEB势垒：当前是MACE几何上的DFT单点，不是DFT弛豫路径。
- Tyagi电荷态排序：当前是固定几何电子响应，不是q=0/q=+1各自的最小能量路径。
- GA定量效应：尚缺DFT、构型平均和浓度/尺寸收敛。
- FA₀.₉₅Cs₀.₀₅PbI₃结论：尚未建立新宿主的structure/path/charge-state验证。

---

## Stage 0 — 整理、同步并冻结当前证据

### 目标

让GitHub成为唯一可追溯事实源。当前README、`archive/objective1_early/REPORT_objective1.md`、`results/objective1/anchors_summary.json`、`HANDOFF.md (archived, superseded)`和`results/objective1/DFT_BENCHMARK.md`对DFT与anchor (b)的完成度存在不一致表述。

### 执行

```bash
cd ~/Desktop/perovskite-screening
git status --short
git log --oneline --decorate -12
```

逐项检查并决定是否加入版本控制：

```text
EHPC_SETUP.md
HANDOFF.md
results/objective1/dft_benchmark.png
ehpc/
literature_review_2026/
output/pdf/perovskite_stability_review_2026.pdf
```

提交前检查凭据：

```bash
rg -n --hidden -g '!*.pdf' -g '!*.png' \
  '(BEGIN OPENSSH PRIVATE KEY|password\s*=|token\s*=|api[_-]?key\s*=)' .
```

禁止提交：私钥、token、密码、`.ssh/config`、原始wavefunction、`*.save/`和临时SCF目录。可提交：输入文件、Slurm脚本、输入生成器、解析后JSON、图、报告、赝势校验和。

### 建立单一状态表

创建并维护：

```text
results/objective1/STATUS.md
```

每行必须有：日期、计算ID、host/phase/supercell、方法/模型/charge/spin、几何状态（fixed-path或relaxed-path）、结果、局限、允许的主张、下一步。

当前anchor (b)必须写为：

```text
FIXED-GEOMETRY ELECTRONIC COMPARISON: COMPLETE
RELAXED-CHARGE-STATE MIGRATION BARRIER: PENDING
```

### 可复现性补齐

将QE工作流纳入Git，例如：

```text
scripts/05_generate_qe_inputs.py
scripts/06_parse_qe_results.py
ehpc/jobs/*.sbatch
ehpc/inputs/*.in               # 或能完全重建输入的生成器
results/objective1/dft/*.json
results/objective1/dft/README.md
```

记录QE、MPI、赝势名称/来源/SHA256、结构哈希、收敛参数和Slurm资源请求。不要只把输入留在远程机器。

### Stage 0 通过条件

- [ ] 工作区没有未解释的科研结果；
- [ ] 文档对anchor (b)状态一致；
- [ ] QE输入能从仓库重新生成；
- [ ] 没有凭据进入Git；
- [ ] 完成一次清晰的reproducibility提交并push。

---

## Stage 1 — 固定路径DFT benchmark 的方法学收敛

### 目标

确认当前PBE 0.141 eV不是由奇数电子、自旋、展宽、cutoff或k点设置主导。此阶段仍不是完整DFT-NEB，而是为带电NEB确定可信理论设置。

### 1.1 先解决q=0的奇数电子问题

中性缺陷超胞价电子数为：

\[
32\times9+32\times14+95\times7=1401
\]

因此q=0不应默认称为closed shell。对q=0的img0和img3运行：

```text
Case A  当前非自旋设置（旧参考）
Case B  nspin=2, tot_magnetization=1
Case C  合理的替代初始磁化/电子局域初值
```

保存总磁矩、自旋密度、缺陷态占据、img0/img3能量和所得barrier。q=+1有1400电子，也必须检查其电子局域化，而不是只根据电子数假设闭壳层。

若spin-polarised与非自旋势垒差超过10–20 meV，旧141 meV只能称为“preliminary non-spin fixed-path value”。

### 1.2 Smearing、cutoff与k点测试

对q=0和q=+1的img0/img3比较：

```text
Gaussian degauss = 0.010 Ry 与 0.005 Ry
ecutwfc = 50 Ry -> 60 Ry（必要时70 Ry）
ecutrho = 与超软赝势推荐比率一致
Gamma点 -> 适合实际γ-P1超胞的更密k点网格
```

每次只改变一个参数。验收标准：

\[
|E_a^{tight}-E_a^{production}|\le10\ \mathrm{meV}
\]

将最终生产设置写入：

```text
configs/qe_gamma_vi_production.yaml
results/objective1/dft/convergence.csv
results/objective1/dft/convergence.md
```

### 1.3 补齐固定路径的所有图像

当前只算了0/2/3/4。运行所有MACE NEB图像的q=0和q=+1单点，才可以写：

> Image N is the highest-energy structure on the sampled MACE-generated band under PBE single-point evaluation.

在DFT-NEB完成前，禁止写“DFT找到真正鞍点”。

### Stage 1 输出与通过条件

```text
results/objective1/dft/fixed_path/
  q0_spin_scan.csv
  smearing_scan.csv
  cutoff_kpoint_scan.csv
  all_images_q0.json
  all_images_q1.json
  fixed_path_profile.png
  FIXED_PATH_BENCHMARK.md
```

- [ ] q=0自旋状态明确；
- [ ] production smearing/cutoff/kpoint到10 meV内收敛；
- [ ] q=0/q=+1都有完整固定路径曲线；
- [ ] 保存磁矩、占据、力与SCF状态；
- [ ] 文档将141 meV正确称为fixed-path PBE value。

---

## Stage 2 — 完成真实的电荷态迁移路径：Anchor (b)

### 目标

对q=0和q=+1分别得到弛豫迁移路径：

\[
E_a(q)=E_{TS}^{q}-E_{initial}^{q}
\]

这一步才是与Tyagi电荷态迁移行为可比的计算。不要预先强迫数据符合文献；若排序不同，应如实报告并诊断相、超胞、泛函和路径差异。

### 2.1 分开弛豫端点

从相同原子映射与晶胞起点，分别建立：

```text
q0_initial, q0_final, q1_initial, q1_final
```

对每一个：

- 固定晶胞；
- 使用Stage 1确定的spin/occupation设置；
- 离子弛豫至 `fmax <= 0.02 eV/Å`；
- 保存结构、磁矩、局域键长、电子局域化；
- 检查q=0与q=+1是否产生不同Pb–I畸变。

### 2.2 DFT路径的两阶段策略

```text
探索：3个内部图像，非climbing，确认路径类别和计算稳定性
生产：5个内部图像，CI-NEB，分别用于q=0与q=+1
```

最低要求：固定晶胞、同一DFT理论层级、同一赝势/收敛参数、endpoint `fmax <= 0.02 eV/Å`、NEB `fmax <= 0.03–0.05 eV/Å`，并对至少一个电荷态增加图像数进行检查。

每条路径报告：

```text
E_initial, E_final, E_TS
Ea_forward, Ea_reverse, endpoint asymmetry
maximum NEB force
magnetisation / charge localisation for each image
```

### 2.3 带电修正检查

q=+1的主导同电荷项可能在同一晶胞的barrier差中大幅抵消，但不可以直接假设完全为零。检查：

\[
\Delta E_{corr}=E_{corr}^{TS}-E_{corr}^{initial}
\]

最低检查包括初态/鞍点电荷密度、远离缺陷的势对齐、FNV/eFNV修正差；若可承担，在更大胞重复q=+1初态和鞍点单点。

若\(|\Delta E_{corr}|<10\) meV，可写“残余带电修正小于目标精度”；否则纳入最终势垒。

### Anchor (b)通过条件

- [ ] q=0和q=+1都有各自弛豫的端点；
- [ ] 两个电荷态都有收敛DFT路径；
- [ ] spin、占据和局域化已检查；
- [ ] q=+1初态–鞍点修正差已量化；
- [ ] 报告势垒差和不确定度；
- [ ] 对照Tyagi时说明相、超胞、理论层级、0 K NEB与有限温MD的区别。

输出：

```text
results/objective1/dft/charge_relaxed/
  q0/
  q1/
  charge_state_profiles.csv
  charge_state_structural_descriptors.csv
  charge_correction_check.md
  CHARGE_STATE_ANCHOR.md
  charge_state_neb.png
```

最终状态只能为：

```text
ANCHOR_B_REPRODUCED
ANCHOR_B_COMPLETED_DIFFERENT_ORDERING
ANCHOR_B_INCONCLUSIVE
```

---

## Stage 3 — 训练分电荷态的MACE并闭合主动学习

### 目标

建立两个独立模型：

```text
MACE-FT-VI0
MACE-FT-VIp
```

标准MACE-MP-0没有总电荷输入，因此不得用同一个模型仅修改`charge`标签来冒充两种电荷态。

### 3.1 每个电荷态的DFT训练集

至少包括：

- 弛豫端点；
- DFT NEB全部图像；
- 鞍点两侧图像；
- endpoint/saddle的0.03–0.10 Å随机扰动；
- 轻微双轴应变结构；
- 不同局域空位环境和跳跃方向；
- 主动学习发现的高不确定度帧。

每帧保存：energy、forces、cell、stress（若有）、charge state、config type、来源计算ID和DFT输入哈希。

训练/验证/测试按独立路径或独立构型切分，禁止把同一条NEB相邻图像随机分至训练和测试两侧。

### 3.2 训练验收

除全局能量/力误差外，保留路径必须满足：

\[
|E_a^{MLIP}-E_a^{DFT}|<0.05\ \mathrm{eV}
\]

还须检查鞍点机制、barrier ordering、迁移I与邻近Pb/I的力误差，以及两个电荷态不会数值退化为同一PES。

若全局force MAE很低但鞍点barrier误差大于50 meV，模型不通过。

### 3.3 主动学习循环

```text
MLIP NEB/短MD
-> 选择高不确定度或路径异常帧
-> DFT能量+力
-> 加入对应电荷态训练集
-> 重新微调
-> 用保留路径复测
```

通过状态：

```text
GAMMA_CSPBI3_CHARGE_SPECIFIC_MLIP_VALIDATED
```

---

## Stage 4 — 转移到 FA₀.₉₅Cs₀.₀₅PbI₃：Objective 1B

γ-CsPbI₃验证了流程，不能把其势垒直接继承到FA/Cs。

### 4.1 精确组成与结构

精确5% Cs需要20个A位：

\[
\mathrm{FA}_{19}\mathrm{Cs}_{1}\mathrm{Pb}_{20}\mathrm{I}_{60}
\]

一个FA为\(\mathrm{CH_5N_2}\)：完整混合体系233原子，一个I空位后232原子。

要求：使用黑色α/伪立方FA-rich母相；枚举行列式为20的超胞变换矩阵；选择接近各向同性的候选，不默认2×2×5；保存候选评分、变换矩阵和元素计数assert。

### 4.2 FA取向集合

至少准备3个独立弛豫FA取向和1个短MD快照。检查FA是否解离、N–H···I接触、PbI₆骨架、Cs局域环境和空位是否诱发非钙钛矿重构。

### 4.3 最小迁移路径矩阵

对至少三个FA构型，各计算一条Cs-near和一条Cs-far路径：共至少6条。报告最小值、中位数、最大值、范围和near/far差异，而非一个“FA/Cs势垒”。

### 4.4 DFT转移门槛

选择最低、中位数、Cs-near/高势垒三条代表路径，进行端点/鞍点/相邻图像DFT检查；若DFT力显示鞍点不稳定或机制改变，做完整DFT NEB。q=0/q=+1必须在新host重新处理。

通过条件：

- [ ] FA₁₉Cs₁Pb₂₀I₆₀结构和相合理；
- [ ] 至少3个FA取向稳定；
- [ ] 至少6条路径形成分布；
- [ ] 至少3条路径DFT抽查；
- [ ] 代表性barrier的MLIP–DFT误差<0.05 eV；
- [ ] q=0/q=+1处理明确；
- [ ] −1%、0、+1%双轴应变三点完成或说明延后原因。

通过状态：

```text
TARGET_HOST_VALIDATED
```

---

## Stage 5 — 5个候选pilot，随后才是50候选筛选

### 目标

先验证排序是否经得起构型、距离和DFT审计，再扩大筛选规模。

### 每个pilot候选的最低计算集

- 同一host构型的undoped paired control；
- dopant-near与dopant-far hop；
- 至少两个局域构型；
- vacancy binding energy；
- escape barrier；
- 结构稳定性和电荷补偿检查；
- 至少一个代表性DFT抽查。

分别报告：

\[
\Delta E_a^{local}=E_a^{near}-E_a^{control}
\]

\[
E_{bind}=E_{far}-E_{near}
\]

\[
E_{escape}=E_{TS}-E_{near}
\]

提高局部势垒不自动等价于抑制长程迁移；可能只是强烈捕获空位，或打开另一条低势垒绕行路径。

pilot通过条件：top/bottom候选不因构型完全反转；MLIP–DFT误差<0.05 eV；机制与几何/电荷证据一致；候选在补偿和相稳定性上可行。通过后才扩展到约50个候选。

---

## 资源、报告与停止纪律

每次E-HPC任务前后：

```bash
ssh ehpc 'sinfo; squeue -u $USER'
ssh ehpc 'sacct -j JOB_ID --format=JobID,State,Elapsed,ExitCode,MaxRSS'
```

记录每个任务的core-hours、walltime、peak memory、SCF次数、费用估计和输出路径。没有排队任务时，先确保数据同步到NAS/本地Git，再停止不需要的按量节点。

每完成一个Stage，同步更新：

```text
README.md
HANDOFF.md
results/objective1/STATUS.md
results/.../REPORT_*.md
proposal/proposal_v2.tex
```

完成Stage 2前，proposal只允许写：

> Fixed-geometry PBE calculations on a MACE-generated γ-CsPbI₃ path establish a 0.118 eV MACE–PBE discrepancy and motivate charge-specific fine-tuning. Fixed-geometry q=0/q=+1 calculations are complete; relaxed charge-state migration pathways remain in progress.

禁止写：

```text
“we reproduced Tyagi’s charge-state mobility ordering”
“DFT benchmarked the true migration barrier”
“the true barrier lies between PBE and MACE”
```

---

## 总顺序与现在立刻执行的三件事

```text
Stage 0  Git整理、事实统一、QE输入可复现
   ↓
Stage 1  q=0自旋 + smearing/cutoff/k点 + 全固定路径DFT
   ↓
Stage 2  q=0/q=+1各自弛豫端点与DFT-NEB
   ↓
Stage 3  分电荷态MACE微调与主动学习闭环
   ↓
Stage 4  FA0.95Cs0.05PbI3 target-host validation
   ↓
Stage 5  5候选pilot，DFT审计后扩展至50候选
```

立即执行：

1. 整理未提交的E-HPC、DFT图和2026文献综述，完成Stage 0；
2. 在E-HPC上运行q=0 img0/img3的spin-polarised与smearing测试；
3. 只有Stage 1通过后，提交q=0/q=+1各自弛豫端点的Slurm任务。

在这三步完成前，不开启大规模添加剂NEB farm。

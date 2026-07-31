> # SUPERSEDED — archived 2026-07-28
>
> Stage-2 execution guide; superseded by the PI's later guide.
>
> **Current authority: `NEXT_STEP_GUIDE.md`.** This file is retained verbatim below for provenance; do not cite it as current.

# 完整执行指南 — 从 Objective 1 收尾到 FA₀.₉₅Cs₀.₀₅PbI₃ 候选筛选

**版本:2026-07-23 合并版。本文件是唯一权威执行文档,取代并归档以下三份:**
`NEXT_STEPS_FA.md`、《下一步执行指南(Stage 0–5)》、`PLAN_AMENDMENTS.md`。
执行者:Mac mini 上的 claudescience。硬件:AutoDL RTX 5090(MLIP)+
阿里云 E-HPC 2×32 核(DFT)+ NAS。

**一句话定位:** pipeline 已跑通;zero-shot 趋势有价值;DFT 已证明 MACE-MP-0
的绝对势垒不能用于生产排名;电荷态 DFT 链路已通,但尚无各自弛豫的 q=0/q=+1
最小能量路径。**完成 Stage 3 之前不开始 50 候选正式排行榜。**

---

## 第一部分 当前证据与允许的结论

| 模块 | 已有结果 | 目前允许的结论 |
|---|---|---|
| γ-CsPbI₃ baseline | MACE 0.259 eV(159 原子,float64 CI-NEB) | 脚本/路径生成/数值回归可用;0.259 eV 不是最终物理势垒 |
| DFT-vs-MACE | 同一 MACE 路径上 PBE 0.141 eV vs MACE 0.259 eV | MACE 在该**固定路径**上比 PBE 高 118 meV;不可用于绝对排名 |
| 带电固定路径 | q=0:140.6 meV;q=+1:126.6 meV | 固定核坐标下移除电子使该路径降约 14 meV;**不是** Tyagi 的完整电荷态比较 |
| GA | near 三取向 +70/+182/+278 meV;far ≈ −23 meV | 局域 pinning 符号稳健;量级对构型和尺寸敏感 |
| 应变 | 双轴拉降压升;+1% ≈ −41 meV,尺寸一致 | 当前最稳健的 zero-shot 趋势结果 |
| 立方相试筛 | Ba/Ca/Sr/Bi/Br 均降垒 | 机制探索 tier;非生产宿主排名 |

**尚不能宣称:** 完整 DFT-NEB 势垒;Tyagi 电荷态排序;GA 定量效应;
FA₀.₉₅Cs₀.₀₅PbI₃ 的任何结论。

**声明禁令(全程有效):**

```
"we reproduced Tyagi's charge-state mobility ordering"
"DFT benchmarked the true migration barrier"
"the true barrier lies between PBE and MACE"
"DFT found the true saddle"(在全图像评估+DFT-NEB 之前)
```

---

## 第二部分 总体结构:双泳道

**原则:Stage 门槛管"声明和排名",不管"探索性算力"。** 两条泳道吃不同硬件,
互不阻塞:

```
泳道一(E-HPC,声明门槛链,严格串行):
  Stage 0 → Stage 1 → Stage 2 → Stage 3 → Stage 4(DFT 部分)→ Stage 5

泳道二(5090,探索泳道,与泳道一并行):
  FA 母相建胞 → det=20 超胞枚举 → FA 取向系综 → zero-shot FA 基线分布
  (全部产物标注 exploratory/quarantined,不进生产声明,只作 Stage 4 输入)
```

**回归测试规则(全程):** γ-CsPbI₃ 0.259 eV 在任何环境/版本/依赖变更后必须
复现至 <1 meV 才允许继续;FA 基线稳定后同样入库一条 FA 回归路径。

---

## 第三部分 泳道二 — FA 宿主探索(5090,今天即可开工)

### W2-1 母相与超胞

- α/伪立方黑相 FA-rich 母相;12 原子赝立方胞,FA 手工构型,MACE 弛豫;
- **det=20 超胞枚举**:枚举行列式为 20 的变换矩阵,按各向同性评分排序
  (pymatgen/ASE 的 optimal cell shape 工具),不默认 2×2×5;保存候选评分、
  变换矩阵和元素计数 assert;
- 目标组成 FA₁₉Cs₁Pb₂₀I₆₀ = 233 原子(FA = CH₅N₂ 八原子),挖一个 V_I 后 232。

### W2-2 FA 取向系综

- 纯 FA 母相 2×2×2(96 原子)MLIP-MD:300 K NVT,20–50 ps,每 2–5 ps 抽帧,
  淬火弛豫 → **≥8 个去相关取向构型**;
- 检查:FA 未解离、N–H···I 接触合理、PbI₆ 骨架完好、空位未诱发非钙钛矿重构;
- MD 只用于生成取向样本,不做动力学结论(zero-shot 对 FA 转动质量未知)。

### W2-3 zero-shot FA 基线分布

- 8 个构型各跑同一条 V_I 八面体棱边 hop 的 CI-NEB(float64,per-image calc);
- 产出:**Ea 分布(N、均值、标准差、极差)**——散布宽度决定 Stage 4/5 全部
  采样预算,是泳道二最重要的单个数字;
- 与文献 FA 基区间做 sanity 对照;入库 FA 回归路径。

### 泳道二验收

- [ ] det=20 最优超胞选定且有评分记录;
- [ ] ≥8 取向构型通过结构检查;
- [ ] FA 基线 Ea 分布报告(`results/fa_host/REPORT_fa_baseline.md`);
- [ ] 全部文件带 exploratory 标注。

---

## 第四部分 泳道一 · Stage 0 — 整理、同步并冻结证据

### 目标

GitHub 成为唯一可追溯事实源;消除 README/`archive/objective1_early/REPORT_objective1.md`/
`results/objective1/anchors_summary.json`/`HANDOFF.md (archived, superseded)`/`results/objective1/DFT_BENCHMARK.md` 对 anchor (b) 完成度的
不一致表述。

### 执行

```bash
cd ~/Desktop/perovskite-screening
git status --short && git log --oneline --decorate -12
# 凭据扫描(提交前必跑):
rg -n --hidden -g '!*.pdf' -g '!*.png' \
  '(BEGIN OPENSSH PRIVATE KEY|password\s*=|token\s*=|api[_-]?key\s*=)' .
```

**禁止提交:** 私钥、token、密码、`.ssh/config`、wavefunction、`*.save/`、
临时 SCF 目录。**必须提交:** QE 输入(或完全重建输入的生成器)、Slurm 脚本、
解析后 JSON、图、报告、赝势名称/来源/SHA256、结构哈希、收敛参数。

```text
scripts/05_generate_qe_inputs.py
scripts/06_parse_qe_results.py
ehpc/jobs/*.sbatch          ehpc/inputs/*.in
results/objective1/dft/*.json + README.md
```

### 单一状态表

创建 `archive/objective1_early/STATUS.md`,每行含:日期、计算 ID、host/phase/supercell、
方法/模型/charge/spin、几何状态(fixed-path 或 relaxed-path)、结果、局限、
允许的主张、下一步、**实际花费**。anchor (b) 当前必须写为:

```text
FIXED-GEOMETRY ELECTRONIC COMPARISON: COMPLETE
RELAXED-CHARGE-STATE MIGRATION BARRIER: PENDING
```

### 两处文档修正(本 Stage 内完成)

1. `results/objective1/DFT_BENCHMARK.md` 的 "The true barrier likely sits between PBE (141 meV)
   and MACE (259 meV)" → 改为 "PBE and MACE disagree by 118 meV at fixed
   geometry; neither is the converged physical barrier (spin state, path
   relaxation, SOC and finite-T effects unresolved)";
2. 同文件头部 "Anchor (b) — DONE (single-point)" → 改为上面的两行式状态。

### 通过条件

- [ ] 工作区无未解释的科研结果;
- [ ] 全部文档对 anchor (b) 状态一致;
- [ ] QE 输入可从仓库重建;
- [ ] 凭据扫描通过;
- [ ] reproducibility 提交已 push。

---

## 第五部分 Stage 1 — 固定路径 DFT 的方法学收敛

### 目标

确认 141 meV 不被自旋、展宽、cutoff、k 点或色散设置主导;为带电 NEB 锁定
生产理论设置。**本阶段同时锁定全项目泛函层级。**

### 1.1 q=0 奇电子问题(最优先)

中性缺陷超胞价电子 32×9 + 32×14 + 95×7 = **1401(奇数)**,不得默认闭壳层。
对 q=0 的 img0/img3 运行:

```text
Case A  当前非自旋设置(旧参考)
Case B  nspin=2, tot_magnetization=1
Case C  合理替代初始磁化/局域初值
```

保存总磁矩、自旋密度、缺陷态占据、能量与垒。q=+1(1400,偶)同样检查电子
局域化。**若自旋极化与非自旋垒差 >10–20 meV,141 meV 降级为 "preliminary
non-spin fixed-path value"。**

### 1.2 收敛矩阵(每次只动一个参数)

```text
degauss:  0.010 → 0.005 Ry
ecutwfc:  50 → 60(必要时 70)Ry;ecutrho 按超软赝势推荐比率
k 点:    Γ → 适合 γ-P1 超胞的更密网格
D3:      on/off 对照(SCF 后附加项,近零成本)★
SOC:     img0/img3 一对全相对论单点;若不做,STATUS.md 显式写
          "SOC deferred" + 理由 ★
```

★ 为合并版新增。**D3 结论当场锁定:全项目统一 PBE+D3**(FA 宿主必须有 D3;
避免 Stage 3 训练集将来重算),γ-CsPbI₃ 侧同步换轨。

验收:|Ea(tight) − Ea(production)| ≤ 10 meV。生产设置写入
`configs/qe_gamma_vi_production.yaml` + `results/objective1/dft/convergence.{csv,md}`。

### 1.3 补齐固定路径全部图像

当前只有 0/2/3/4。全部图像的 q=0/q=+1 单点跑完后,才允许写
"Image N is the highest-energy structure on the sampled MACE band under PBE"。

### 输出与通过条件

```text
results/objective1/dft/fixed_path/
  q0_spin_scan.csv  smearing_scan.csv  cutoff_kpoint_scan.csv
  d3_soc_check.csv  all_images_q0.json  all_images_q1.json
  fixed_path_profile.png  FIXED_PATH_BENCHMARK.md
```

- [ ] q=0 自旋状态明确;
- [ ] 生产设置收敛至 10 meV 内,含 D3 决定与 SOC 处理;
- [ ] 两个电荷态的完整固定路径曲线;
- [ ] 磁矩/占据/力/SCF 状态入库;
- [ ] 141 meV 在所有文档中称为 fixed-path PBE value。

**预算帽:≤2 节点日(≈¥400)。时间盒:3–5 天(与 Stage 0 合计)。**

---

## 第六部分 Stage 2 — 真实电荷态迁移路径(anchor b)

### 目标

对 q=0 与 q=+1 分别得到弛豫路径的 Ea(q) = E_TS(q) − E_initial(q)。
不预设结果符合 Tyagi;排序不同则如实报告并诊断相/超胞/泛函/路径差异。

### 2.1 分开弛豫端点

`q0_initial, q0_final, q1_initial, q1_final` 各自:固定晶胞;用 Stage 1 锁定的
spin/occupation/D3 设置;离子弛豫至 fmax ≤ 0.02 eV/Å;保存结构、磁矩、局域
键长、电子局域化;比较 q=0/q=+1 的 Pb–I 畸变差异。
**弛豫轨迹的每一步 SCF 全部存档——这是 Stage 3 训练集的种子。**

### 2.2 两阶段路径策略(含预算决策点 ★)

```text
探索:3 内部图像,非 climbing,两个电荷态各一条
决策:测 DFT 探索路径相对 MACE 路径的最大原子位移 d_max
  d_max < 0.15 Å  → 省法:DFT 弛豫端点 + MACE 路径加密单点
                     + 仅 q=+1 全 5 图 CI-NEB(物理主导态优先享受全预算)
  d_max ≥ 0.15 Å 或路径类别改变 → 两个电荷态都上全 CI-NEB
```

硬性要求:固定晶胞、统一理论层级/赝势/收敛参数、endpoint fmax ≤ 0.02、
NEB fmax ≤ 0.03–0.05 eV/Å、至少一个电荷态做图像数加密检查。每条路径报告
E_initial/E_final/E_TS、Ea 正反向、端点不对称、最大 NEB 力、逐图像磁化/电荷局域。

### 2.3 带电修正检查

不得假设 ΔE_corr = E_corr(TS) − E_corr(initial) 为零。最低检查:初态/鞍点电荷
密度、远离缺陷的势对齐、FNV/eFNV 修正差;可承担时在更大胞重复 q=+1 初态与
鞍点单点。|ΔE_corr| < 10 meV 才可写 "residual charged correction below target
precision",否则并入最终势垒。

### 通过条件与输出

- [ ] 两个电荷态各自弛豫端点 + 收敛路径;
- [ ] spin/占据/局域化已检查;
- [ ] ΔE_corr 已量化;
- [ ] 势垒差与不确定度已报告;
- [ ] 对照 Tyagi 时说明相/超胞/理论层级/0 K NEB vs 有限温 MD 的区别。

```text
results/objective1/dft/charge_relaxed/
  q0/  q1/  charge_state_profiles.csv
  charge_state_structural_descriptors.csv
  charge_correction_check.md  CHARGE_STATE_ANCHOR.md  charge_state_neb.png
```

最终状态三选一:`ANCHOR_B_REPRODUCED` / `ANCHOR_B_COMPLETED_DIFFERENT_ORDERING`
/ `ANCHOR_B_INCONCLUSIVE`。

**预算帽:≤¥1500。时间盒:1–2 周。**

---

## 第七部分 Stage 3 — 分电荷态 MACE 微调与主动学习闭环

### 目标

两个独立模型 `MACE-FT-VI0` / `MACE-FT-VIp`。MACE 无总电荷输入,**不得用同一
模型改 charge 标签冒充两个电荷态。**

### 3.1 训练集(每电荷态)

弛豫端点、DFT 路径全部图像、鞍点两侧图像、endpoint/saddle 的 0.03–0.10 Å
随机扰动、轻微双轴应变结构、不同空位环境与跳跃方向、AL 发现的高不确定度帧。
每帧存 energy/forces/cell/stress/charge state/config type/来源计算 ID/输入哈希。
**切分纪律:按独立路径或独立构型切分 train/val/test;禁止同一条 NEB 的相邻
图像跨切分。**

### 3.2 验收

- 保留路径 |Ea(MLIP) − Ea(DFT)| < 0.05 eV;
- 鞍点机制、barrier ordering、迁移 I 与近邻 Pb/I 的力误差合格;
- 两个电荷态模型不数值退化为同一 PES;
- **全局 force MAE 低但鞍点垒误差 >50 meV = 不通过。**

### 3.3 主动学习循环

```text
MLIP NEB/短 MD → 高不确定度/路径异常帧 → DFT 能量+力
→ 加入对应电荷态训练集 → 重新微调 → 保留路径复测
```

通过状态:`GAMMA_CSPBI3_CHARGE_SPECIFIC_MLIP_VALIDATED`。
**时间盒:约 1 周(训练在 5090,DFT 单点走 E-HPC)。**

---

## 第八部分 Stage 4 — FA₀.₉₅Cs₀.₀₅PbI₃ 宿主验证(Objective 1B)

γ-CsPbI₃ 验证的是流程;势垒不继承。泳道二的产出在此转正(补 DFT 审计后)。

### 4.1 结构(泳道二 W2-1 转正)

det=20 最优超胞,FA₁₉Cs₁Pb₂₀I₆₀,元素计数 assert;黑色 α/伪立方母相。

### 4.2 取向集合(W2-2 转正)

≥3 个独立弛豫 FA 取向 + 1 个 MD 快照;结构检查同 W2-2。

### 4.3 最小迁移路径矩阵

≥3 个 FA 构型 × (Cs-near + Cs-far) = **≥6 条路径**。报告 min/median/max/range
与 near−far 差值——**near/far 差值即 ΔEa(Cs),保留 headline 问题框架:
"5% Cs 只稳相还是也钉扎碘迁移?"** 不报告单一 "FA/Cs 势垒"。

### 4.4 DFT 转移门槛

最低/中位/Cs-near 三条代表路径做端点/鞍点/邻图 DFT 检查(PBE+D3,Stage 1
设置);若 DFT 力显示鞍点不稳定或机制改变 → 完整 DFT-NEB。q=0/q=+1 在新宿主
重新处理(至少固定路径对照 + 必要时弛豫)。

### 通过条件

- [ ] 结构与相合理;≥3 取向稳定;
- [ ] ≥6 条路径形成分布;≥3 条 DFT 抽查;
- [ ] 代表路径 MLIP–DFT 误差 <0.05 eV;
- [ ] q=0/q=+1 处理明确;
- [ ] −1%/0/+1% 双轴应变三点完成或书面说明延后理由。

通过状态:`TARGET_HOST_VALIDATED`。

---

## 第九部分 Stage 5 — 六候选 pilot → 50 候选筛选

### pilot 候选(固定名单,含已知答案量尺)

| 候选 | 预期 | 角色 |
|---|---|---|
| GA⁺(A位) | + | 阳性对照;补齐 anchor (c) 定量线 |
| Sr²⁺(B位) | − | 阴性对照(自家初筛 + Arber 双重背书) |
| K⁺(间隙) | + | 文献阳性 |
| 多价间隙(Zhao 2022 机制类) | + | 静电俘获机制代表 |
| 通道阻塞型一例 | ? | 第三机制类代表 |
| Cs⁺(4.3 免费产出) | ? | ΔEa(Cs) headline 问题 |

### 每候选最低计算集

同宿主构型 undoped paired control;dopant-near 与 dopant-far hop;≥2 个局域
构型;vacancy binding energy;escape barrier;结构稳定性与电荷补偿检查;
≥1 个代表性 DFT 抽查。分别报告:

```text
ΔEa_local = Ea(near) − Ea(control)
E_bind    = E(far) − E(near)
E_escape  = E_TS − E(near)
```

**局部垒升高不自动等于抑制长程迁移**——可能只是强俘获空位或打开低垒绕行路径;
三个量一起看。

### 通过条件

top/bottom 候选不因构型反转;MLIP–DFT 误差 <0.05 eV;机制与几何/电荷证据
一致;候选电荷补偿与相稳定性可行。**通过后才扩展至 ~50 候选正式排行榜**
(排名 = 分布统计 + 机制标签 + HSE 电子良性门,按 proposal rev.3 执行)。

---

## 第十部分 资源、报告与停止纪律

### 每次 E-HPC 任务前后

```bash
ssh ehpc 'sinfo; squeue -u $USER'
ssh ehpc 'sacct -j JOB_ID --format=JobID,State,Elapsed,ExitCode,MaxRSS'
```

记录 core-hours、walltime、峰值内存、SCF 次数、费用估计、输出路径。
**队列清空 → 数据同步到 NAS/Git → 节省停机两台计算节点。** 5090 空闲即关机。

### 预算与停止

- Stage 1 ≤ ¥400;Stage 2 ≤ ¥1500;泳道二 <¥200;任一 Stage 超帽 50% → 停下汇报;
- STATUS.md 的"实际花费"列每批次更新。

### 文档同步(每 Stage 完成时)

```text
README.md   HANDOFF.md   results/objective1/STATUS.md
results/.../REPORT_*.md   proposal/proposal_v2.tex(rev.3+)
```

Stage 2 完成前,proposal 关于 DFT 的表述仅允许:

> Fixed-geometry PBE calculations on a MACE-generated γ-CsPbI₃ path establish a
> 0.118 eV MACE–PBE discrepancy and motivate charge-specific fine-tuning.
> Fixed-geometry q=0/q=+1 calculations are complete; relaxed charge-state
> migration pathways remain in progress.

### 日历预期(防跳门槛)

```text
Stage 0–1:3–5 天      Stage 2:1–2 周      Stage 3:约 1 周
Stage 4:约 1 周(泳道二已预热)   Stage 5 pilot:约 1 周
50 候选正式筛选的诚实起点:约 4–6 周后
```

中途不因焦虑跳过任何门槛;探索欲望全部导流到泳道二。

---

## 立即执行(今天)

1. **Stage 0** 全部,含两处文档修正;
2. **泳道二启动**:FA 建胞 + det=20 枚举(5090);
3. **Stage 1.1 提交**:q=0 img0/img3 的 spin 扫描批次,同批附 D3 on/off 对照
   (E-HPC,开机→提交→跑完→节省停机)。

三件事完成前,不开启任何大规模 NEB farm。

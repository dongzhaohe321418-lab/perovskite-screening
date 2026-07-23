# 执行计划修正案(PLAN_AMENDMENTS)

写于 2026-07-23(MacBook Pro 会话)。针对《下一步执行指南:从 Objective 1 到
FA₀.₉₅Cs₀.₀₅PbI₃ 筛选》(Stage 0–5 版)。**裁定:该计划作为主干原样采纳**,
本文件只记录采纳声明、五条结构性修正和三条补充纪律。与原计划冲突处以本文件为准;
未提及处一律按原计划执行。

## A. 采纳声明(原样执行,不再讨论)

- Stage 0 全部:单一事实源 STATUS.md、凭据扫描、QE 输入入库可复现;
- Stage 1.1 奇电子/自旋检查(1401 电子核对无误,这是当前 DFT 基准最优先的洞);
- "全图像单点之前不许谈鞍点"、ΔE_corr 不许假设为零、训练集按路径切分;
- **det=20 超胞各向同性枚举取代 2×2×5**(2×2×5 方案正式撤回——精确 5% 但
  纵横比 2:2:5 的镜像间距畸形);
- E_bind / E_escape / paired-control 的 pilot 指标集;
- 全部 claim 禁令,包括 "the true barrier lies between PBE and MACE"。

### A+. Stage 0 追加两项(执行时并入)

1. `DFT_BENCHMARK.md` 中已存在被禁句 "The true barrier likely sits between PBE
   (141 meV) and MACE (259 meV)" —— 改为 "PBE and MACE disagree by 118 meV at
   fixed geometry; neither is the converged physical barrier (spin state, path
   relaxation, SOC and finite-T effects unresolved)";
2. 同文件头部 "Anchor (b) — DONE (single-point)" 与 STATUS 规范冲突,统一改为
   FIXED-GEOMETRY: COMPLETE / RELAXED-PATH: PENDING 两行式。

## B. 五条结构性修正

### B1. 双泳道并行(修正过度串行化)

**Stage 门槛管声明和排名,不管探索性算力。** 原计划下 5090 将闲置数周。改为:

```
泳道一(E-HPC,声明门槛链): Stage 0 → 1 → 2 → 3   按原计划严格串行
泳道二(5090,探索泳道):    FA 母相建胞 + det=20 超胞枚举评分
                            + FA 取向系综(MD 采样→淬火)
                            + zero-shot FA 基线 Ea 分布(≥8 构型)
                            + 结构合理性检查(FA 不解离、骨架完好)
```

泳道二全部产物标注 `exploratory / quarantined`,不进任何生产声明,只作为
Stage 4 的输入准备。两条泳道吃不同硬件,互不阻塞。

### B2. 泛函层级现在锁定(修正 D3 时序缺陷)

Stage 1 收敛矩阵**新增 D3 on/off 一列**(SCF 后附加项,近零成本)。理由:FA 宿主
必须 PBE+D3;若 Stage 3 训练集用无 D3 的 PBE 生成,Stage 4 面临全量重算。
**当场锁定全项目统一 PBE+D3**,γ-CsPbI₃ 侧同步换轨,Stage 3 起所有训练数据用
统一层级。

SOC:img0/img3 至少做一对全相对论单点;若决定不做,必须在 STATUS.md 显式写
"SOC deferred" 及理由(proposal 承诺过 SOC-sensitivity check,不允许默默跳过)。

### B3. Stage 2 预算分级(修正全 DFT-NEB 的一步到位)

3 图非 climbing 探索跑完后,加一个决策点:**测 DFT 路径相对 MACE 路径的最大
原子位移 d_max**:

- d_max < 0.15 Å → 生产阶段用"DFT 弛豫端点 + MACE 路径加密单点 + 仅 q=+1 全
  CI-NEB"(q=+1 是物理主导电荷态,优先享受全预算);
- d_max ≥ 0.15 Å 或路径类别改变 → 两个电荷态都上全 DFT-NEB(原计划)。

### B4. Stage 5 pilot 候选点名(修正无名单+无动态范围)

固定为六个,构成"已知答案的量尺":

| 候选 | 预期 | 角色 |
|---|---|---|
| GA⁺(A位) | + | 阳性对照;顺带补齐 anchor (c) 的定量线 |
| Sr²⁺(B位) | − | 阴性对照(自家初筛+Arber 双重背书) |
| K⁺(间隙) | + | 文献阳性(Abdi-Jalebi 2018) |
| 多价间隙(Zhao 2022 机制类) | + | 静电俘获机制代表 |
| 通道阻塞型一例 | ? | 第三机制类代表 |
| Cs⁺(Stage 4.3 免费产出) | ? | near/far 差值即 ΔEa(Cs)——保留 "5% Cs 只稳相还是也钉扎" 的 headline 问题框架 |

阳性/阴性对照齐备,排序审计才有标尺。top/bottom 反转判据按原计划。

### B5. 三条补充纪律

1. **预算帽+时间盒**:Stage 1 ≤ 2 节点日(≈¥400);Stage 2 ≤ ¥1500;任一
   Stage 实际花费超帽 50% → 停下汇报。STATUS.md 增加"实际花费"列;
2. **回归测试规则**(原计划遗漏):γ-CsPbI₃ 0.259 eV 在任何环境/版本/依赖变更
   后必须复现至 <1 meV 才允许继续;FA 基线稳定后同样入库一条 FA 回归路径;
3. **日历预期写死,防跳门槛**:Stage 0–1 约 3–5 天,Stage 2 约 1–2 周,
   Stage 3 约 1 周;50 候选正式筛选的诚实起点在 **4–6 周后**。中途不因焦虑
   跳过任何门槛;探索欲望全部导流到泳道二。

## C. 立即执行序列(合并后)

```
今天:   Stage 0(含 A+ 两项)+ 泳道二启动(FA 建胞、det=20 枚举)
本周:   Stage 1(spin 扫描优先;矩阵含 D3 列;SOC 一对单点)
        泳道二:FA 取向系综 + zero-shot 基线分布
下周起: Stage 2(3 图探索 → B3 决策点 → 生产路径)
```

原计划的"立即执行三件事"与本序列一致,增补:第 1 件(Stage 0)包含 A+ 两处
文档修正;第 2 件(spin/smearing 测试)提交批次时同步提交 D3 on/off 对照。

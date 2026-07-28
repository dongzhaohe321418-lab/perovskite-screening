<!-- Supplied by the PI 2026-07-28. This is the governing execution guide; the
     acceptance criteria below take precedence over any earlier plan in this repo. -->

下面可直接作为 `NEXT_STEP_GUIDE.md` 使用。

# 下一步执行指南

## 当前判断

- Objective 2 已得到 GA 在当前模型与采样定义下“实用等效于零效应”的结论；Sr 仍不够精确。
- Objective 1 已排除强、热学显著的 q=0 polaron 候选，但尚未证明所有浅局域态都不存在。
- 不要立即启动 q=0 CI-NEB；先完成 q0 endpoint 的真实收敛与跨几何稳定性验证。

## 优先级 A：完成正在运行的任务

### HPC：P1、P2 与 q0_final

P1 结束后检查：

- pristine 与 vacancy cell 是否使用相同理论参数、胞参数和几何参照；
- q0 band 701 与 pristine CBM 的能量参照、Pb-p 分布和共享原子权重重叠；
- 结论只写为“CBM-like”或“与 pristine CBM 一致”，除非三项指标同时支持。

P2 结束后检查：

- 总磁矩是否自然衰减至接近 0；
- 能量、占据和电荷/自旋密度是否稳定；
- 若出现稳定有限磁矩，停止 q0 NEB 计划，先报告该新态；
- 若仍不收敛，记录失败签名，不把失败解释为局域 polaron。

q0_final 继续至两个 endpoint 都满足：

- 离子力达到预设生产阈值；
- 连续多个 BFGS 步的能量与结构稳定；
- 从保存密度重启后，SCF、力和占据态可重复；
- 不出现 band switching、异常磁矩或 `some spin components not found`。

只有全部通过，q=0 NEB 才可进入准备阶段。

### GPU：完成 8 个新增 host

完成 24 条新增路径后：

- 先运行完整 integrity audit；
- endpoint 未达 force target 的路径明确排除；
- pure hop、return-test recovered hop、hop+FA 三类分别保存；
- 不混合 hop+FA 与 pure-hop；
- 更新 n、均值、Student-t CI、TOST 与 χ² 方差上界。

## 优先级 B：Objective 2 统计结论

### GA

可报告：

> 在当前 FA-host ensemble、pure-hop 定义和 MACE 势能面下，GA 的势垒变化与零在 ±59.5 meV 实用等效范围内。

不可报告：

- “GA 对所有 FAPbI3 迁移都无影响”；
- “GA 优于或劣于 Sr”；
- 将 MACE 数值写成 DFT 或实验势垒。

### Sr

若新增样本后仍未达到 χ² 所需的 n≈16：

- 结论保持为“与零效应相容，证据尚不足以确认等效”；
- 不因均值接近零而宣布无效；
- 根据更新后的方差决定是否继续扩样。

## 优先级 C：巩固 q=0 polaron 边界

当前安全结论是：

> 在当前胞、理论水平和所测试的 0.20 Å cage contraction 下，不存在热学显著的深局域 polaron；几 meV 浅态及其他畸变模式尚未排除。

如果论文需要更强的排除结论，再做小型幅度扫描：

- 固定同一局域畸变模式；
- 至少测试 0、0.05、0.10、0.15、0.20 Å；
- 每点使用相同参考几何、相同收敛标准；
- 只在能量残差明显小于所声称的井深时拟合或讨论井深。

若残差仍约 30 meV，不估计几 meV 的耦合常数、临界位移或井深。

## q=0 NEB 的启动门槛

只有在以下条件全部满足后启动：

1. q=0 initial 与 final endpoint 均真实离子收敛；
2. `nspin=1` 沿多个邻近几何点稳定且可重启；
3. P1/P2 没有发现竞争性局域自旋态；
4. q=0 与 q=+1 使用完全一致的理论指纹；
5. NEB 输入、restart、轨迹归档与状态识别脚本已准备完毕。

任一条件失败时，不消耗大规模 HPC 时间，先解决对应物理或数值问题。

## 论文准备

并行整理三张核心图：

1. 84-path corpus：机制分类、admission route 与 GA/Sr paired effect；
2. return-test：metastable、band-collapsed、FA-reorientation 的路径命运图；
3. q=0：CBM-like state、polaron bound、SCF/geometry stability 的证据链。

主论文目前最稳的核心叙事是：

> FA 取向无序不仅扩大迁移势垒分布，还产生路径非对称与 FA 耦合机制分叉；在经过局域稳定性与机制分层后，GA 在该筛选尺度上与零效应实用等效，而 q=0 vacancy 态表现为接近 CBM 的离域电子，未支持深局域 polaron 图像。
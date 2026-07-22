# HANDOFF — 交接说明(MacBook Pro session → Mac mini session)

写于 2026-07-22。本文件供 Mac mini 上的 claudescience 会话接手项目时阅读。

## 项目是什么

钙钛矿离子迁移抑制掺杂剂的计算筛选(γ-CsPbI₃ 中碘空位迁移垒 ΔE_a,DFT + CI-NEB +
MACE 机器学习势主动学习)。完整方案见 `proposal/proposal_v2.pdf`(12页,v2.1,
含电子良性检查)。

## 当前进度

- **曳光弹已完成**(2026-07-22,MacBook Pro,CPU):zero-shot MACE-MP-0(medium,
  float32),倾斜γ-like CsPbI₃(P-1,比立方相低 −18 meV/atom),159原子 2×2×2 超胞,
  八面体棱边 V_I 跳跃 CI-NEB → **E_a = 0.26 eV(正向)/ 0.23 eV(反向)**。
  文献窗口 0.1–0.6 eV ✓(zero-shot 因 PES softening + 准中性 PES 预期偏低)。
  单条路径耗时 ~40 s(M4 Pro CPU)。
- 结构、脚本、结果都在本仓库(git,2 commits)。`.venv` 未随仓库同步,需重建。

## GPU 资源(AutoDL,已租)

- 实例:**RTX 5090(32 GB,Blackwell sm_120,driver 580.142)**,`ssh -p 27745 root@connect.westc.seetacloud.com`
  > ⚠️ 更正(2026-07-22,Mac mini 会话):原交接误写为 4090,实际本次租用的是 **5090**。
  > 已用真实 GPU matmul(非仅 `cuda.is_available()`)核实 Blackwell sm_120 kernel 可正常执行。
  > 实例关机重开后 GPU 型号也可能变,接手时先 `nvidia-smi` 核对。
- 本机 `~/.ssh/config` 需要有别名(若无请创建,见下),并完成密钥授权:

```
Host autodl
    HostName connect.westc.seetacloud.com
    Port 27745
    User root
    ServerAliveInterval 60
    StrictHostKeyChecking accept-new
```

- **注意**:实例关机重开后端口可能变化,需同步更新此处 Port。
- **花钱纪律**:跑完就在 AutoDL 控制台关机;"释放实例"会删数据;结果以本地为
  唯一权威副本,随做随 rsync 回来。

## Mac mini 接手后的第一批任务

1. `ssh autodl "nvidia-smi"` 验证连通和 4090;
2. 远端装环境(base conda 已自带 torch 2.8.0+cu128、py3.12,已核实 Blackwell 可跑
   ——**只需补装 mace/ase/pymatgen,且切勿让 pip 动 torch**,否则会被换成 CPU 轮子):
   ```bash
   ssh autodl
   echo "torch==2.8.0+cu128" > /tmp/c.txt          # 约束文件钉住现有 GPU torch
   pip install -c /tmp/c.txt mace-torch ase pymatgen spglib matplotlib \
       --index-url https://pypi.tuna.tsinghua.edu.cn/simple
   source /etc/network_turbo    # 之后再开学术加速,给 MACE checkpoint 下载(HF/GitHub)提速
   python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"  # True, RTX 5090
   ```
3. 同步本仓库上去(排除 .venv):
   ```bash
   rsync -avz --exclude .venv ~/Desktop/perovskite-screening/ autodl:/root/autodl-tmp/perovskite-screening/
   ```
4. 在 GPU 上重跑 `scripts/` 里的曳光弹 NEB(device="cuda"),对比 40 s 基线,
   记录加速比;
5. 之后按 proposal 时间表推进 Objective 1 锚点(电荷态排序 vs Tyagi et al. 2025、
   GA⁺ ΔE_a、应变–E_a 曲线)。

## 技术要点(别踩的坑)

- **生产级迁移垒用 float64**(`default_dtype="float64"`);float32 只用于快速预筛。
- zero-shot 只做路径播种,**排名必须用微调后模型**(见 proposal §4.5 两个方框)。
- V_I⁺ 是带电缺陷,MACE 基础模型是电荷不可知的——微调数据必须来自带电超胞 DFT
  (per-charge-state,协议照 Tyagi et al., JPCL 2025)。
- 国内网络:pypi 直连超时用 `--index-url https://pypi.tuna.tsinghua.edu.cn/simple`;
  MACE checkpoint 下载在本地机器上要走 hf-mirror.com(curl -C - 续传循环),
  在 AutoDL 实例上用 network_turbo 即可。
- MACE checkpoint 首次运行会自动下载到 `~/.cache/mace/`。

## Objective 1 进展(2026-07-22,Mac mini 会话;经同行评审下调 + DFT-free 下一步补全)

**定位诚实版**:管线跑通、三个趋势物理合理、**符号稳健**;但严格文献复现和"可
排名的量级"仍待 DFT + 电荷态验证。详见 `results/objective1/REPORT_objective1.md`
(+ `strain_Ea.png`、`obj1_refine.png`、`anchors_summary.json`)。

- **(a) 未掺杂 E_a——物理合理性检查(非 Eames 复现)**:γ float64 = 0.259 eV
  (与 float32 差 ~0.05 meV)。⚠️ Eames 2015 做的是 **MAPbI₃ ≈0.6 eV**,不是
  γ-CsPbI₃;0.1–0.6 eV 是跨文献范围而非 Eames 单值。0.259 eV 落在铅卤钙钛矿碘空位
  迁移的宽范围内,是 sanity check + float32/64 回归基准。端点前/后差 29 meV(γ-P1
  两个 I 位点非等价)。
- **(c) GA⁺ ΔE_a——符号稳健,量级未收敛**(本轮补做构型采样):3 个胍取向 @ 近位
  全部钉扎(**+70/+278/+182 meV**,展布 207 meV),远位对照 **−23 meV ≈ 0**(证明是
  *局域*效应);鞍点 N–H···I 接触 2.4–2.7 Å 支持氢键钉扎机制。原来的单构型 +70 meV
  是三者里最小的。**量级对构型和尺寸都敏感**(见有限尺寸),单构型不能用于排名。
- **(d) 应变–E_a——趋势复现(双轴),且尺寸稳健**:双轴 dE_a/dε = **−2.25 eV/strain
  (r = −0.98)**,拉伸降、压缩升。⚠️ **非严格单调**——−3%→+2% 单调下降,+3% 有
  +3 meV 上翘(自己的 monotone=no 诊断已打印)。各向同性压缩端散(tight-rerun 逐位
  一致 → *数值可复现*,但**机制未定**:可能是路径切换/局域极小/模型 artefact,**不是
  已证实的 PES 粗糙度**)。应变位移尺寸收敛:−41 meV 在 2×2×2 = 3×3×3。
- **(b) V_I⁺ vs V_I⁰ 排序(Tyagi 2025)——DFT 门控,只出协议**:MACE 电荷不可知,
  所有势垒是 *charge-unspecified neutral-reference*(不能叫 "V_I⁰-like");这是整个
  方法**最重要的未验证环节**。完整方案(带电超胞 DFT + FNV + per-charge-state 微调 +
  主动学习)在 `results/objective1/CHARGE_STATE_PROTOCOL.md`,待 CSD3 落地即可跑。

**有限尺寸检查(本轮补做,γ 相直接测)**:3×3×3(~540 原子)vs 2×2×2 同一 V_I 边跳——
未掺杂绝对值尺寸收敛(0.259→0.258 eV,不像 cubic screen 那样塌);应变位移干净抵消
(−41=−41 meV);**GA 量级不抵消**(+70→+335 meV)。→ (a)(d) 在 2×2×2 尺寸安全,(c)
量级需构型 + 尺寸平均。数据 `finite_size.json`。

驱动脚本:`scripts/04_objective1_anchors.py`(γ V_I NEB 驱动,`--mode`
regression/strain/ga/finite_size/all;strain 支持 iso/biax + 可调收敛阈值;ga 支持
取向采样 + near/far 站点 + 机制指纹)。

## 尚未完成 / 下一步

- [x] Objective 1 DFT-free 下一步全部补完:GA 构型采样 (#2) + γ 有限尺寸 (#4)
- [ ] proposal 加入 preliminary results 小节(数字已齐,等写)
- [ ] CSD3 算力申请(DFT 腿,GPU 云替代不了)——门控 (b)、以及 #1 undoped/GA DFT 校核、
      #3 双轴 DFT 三点这三个下一步
- [ ] 精读三篇论文的复现笔记(Eames 2015 / Tyagi 2025 / Arber 2025)


---

## 文献调研:钙钛矿稳定性全景 (Literature Survey — completed 2026-07-22)

对钙钛矿稳定性做了一个广义全景文献调研,产物在 `literature_survey/`,已推送 GitHub (commit 7bdce37)。

**方法**:OpenAlex + arXiv 系统检索(2020–2026 重点窗口 + 奠基工作回溯到 2000),按七个
稳定性通道分七路并行 sub-agent 检索,每路对最高被引论文做一步引文图扩展。所有 DOI 经
CrossRef 核验(146 篇全部解析成功,0 撤稿)。

**语料**:去重后 **146 篇**(原始 160,按归一化 DOI 去重),73/146(50%)为 2020 年后;
13 篇跨主题。七通道:相/成分稳定性、环境降解(水/氧/热/光)、离子迁移与缺陷、应变工程、
钝化/添加剂/掺杂、器件运行稳定性与封装、计算/ML 方法。

**核心论点**(与本项目直接相关):离子迁移是机制枢纽——迁移激活能升高 ~0.2 eV 即可在室温
下把迁移速率压低 ~1000×;应变、成分、钝化策略多半是**通过**抬高迁移势垒来兑现稳定性收益,
且离子迁移是封装唯一无法排除的通道。这正是本仓库掺杂筛选计划(γ-CsPbI₃ 中抑制离子迁移的
掺杂剂)的立论核心。

**产物** (`literature_survey/`):
- `perovskite_stability_review.md` — ~16,000 词全文综述,行内 DOI 引用 + 146 条参考文献附录
- `perovskite_stability_review.pdf` — 5 页presentation精简版(含两张图)
- `perovskite_stability_references.csv` — 主参考表(去重、已核验)
- `figures/` — 发表时间线 + 主题景观图;`sections/` — 七篇分主题综述;`papers/` — 七个分主题 JSON

**说明**:被引数取自检索时的 OpenAlex,存在年龄偏差(近期工作累积被引时间短)。

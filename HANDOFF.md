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

- 实例:RTX 4090,`ssh -p 27745 root@connect.westc.seetacloud.com`
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
2. 远端装环境:
   ```bash
   ssh autodl
   source /etc/network_turbo    # AutoDL 学术加速(GitHub/HuggingFace)
   pip install mace-torch ase pymatgen
   python -c "import torch; print(torch.cuda.is_available())"   # 须为 True
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

## 尚未完成 / 下一步

- [ ] proposal 加入 preliminary results 小节(曳光弹数字,等 GPU 复跑后一起写)
- [ ] CSD3 算力申请(DFT 腿,GPU 云替代不了)
- [ ] Objective 1 四个锚点
- [ ] 精读三篇论文的复现笔记(Eames 2015 / Tyagi 2025 / Arber 2025)

#!/usr/bin/env python
"""Figure S2b-E block 4: the host values Y_h of the A1 tier, per dopant, with the mean and the interval I^A1_d.

Every plotted number is parsed from the committed output of E (s2b/E_output.txt, block 4, sections 4.2 and 4.3);
the script opens no archive file and computes no energy. It writes its source data to
source_data/fig_s2b_e_block4_Yh.csv and the caption, which carries the header line of E, to
fig_s2b_e_block4_Yh.caption.txt. A host that is not a valid host for a dopant has no point. Host m06 is drawn with
an open marker: it is the outlier named in S2B_RESULT.md (a post hoc observation, not a rule of E).

    python -B results/objective2/s2/figures/fig_s2b_e_block4_Yh.py
"""
import csv, os, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
E_OUT = os.path.join(HERE, os.pardir, "s2b", "E_output.txt")
HOSTS = ["m06", "m02", "m16", "m12", "m32", "m26", "m22", "m23"]
DOPANTS = ["Sr", "Cl", "Cs", "GA"]
SITE = {"Sr": "Sr (on Pb)", "Cl": "Cl (on I)", "Cs": "Cs (on FA)", "GA": "GA (on FA)"}
KBT = 25.7                                    # meV, S2_PLAN.md line 40
SHORT = {"repels": "repels", "no first-shell interaction beyond k_BT": "no interaction\nbeyond $k_BT$",
         "not resolved": "not resolved"}


def parse():
    lines = open(E_OUT, encoding="utf-8").read().split("\n")
    a = next(i for i, x in enumerate(lines) if x.startswith("BLOCK 4."))
    b = next(i for i, x in enumerate(lines) if x.startswith("BLOCK 5."))
    header = lines[a + 1].strip()
    y, tier = {}, {}
    for x in lines[a:b]:
        x = x.split("  -- ")[0]
        m = re.match(r"\s+(m\d\d) (Sr|Cl|Cs|GA): .*Y_h = (-?[\d.]+) meV", x)
        if m:
            y[(m.group(1), m.group(2))] = float(m.group(3))
        m = re.match(r"\s+(Sr|Cl|Cs|GA): n_d = (\d+); Ȳ_d = (-?[\d.]+) meV; .*I\^A1_d = \[(-?[\d.]+), (-?[\d.]+)\] meV", x)
        if m:
            tier[m.group(1)] = {"n_d": int(m.group(2)), "mean": float(m.group(3)), "lo": float(m.group(4)),
                                "hi": float(m.group(5))}
        m = re.match(r"\s+(Sr|Cl|Cs|GA): A1-tier class: (.*?); rule V", x)
        if m:
            tier[m.group(1)]["class"] = m.group(2)
    assert set(tier) == set(DOPANTS) and all("class" in t for t in tier.values()), tier
    assert all(sum((h, d) in y for h in HOSTS) == tier[d]["n_d"] for d in DOPANTS)
    return header, y, tier


def main():
    header, y, tier = parse()
    os.makedirs(os.path.join(HERE, "source_data"), exist_ok=True)
    with open(os.path.join(HERE, "source_data", "fig_s2b_e_block4_Yh.csv"), "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["kind", "host", "dopant", "value_meV", "lo_meV", "hi_meV", "n_d", "class"])
        for d in DOPANTS:
            for h in HOSTS:
                if (h, d) in y:
                    w.writerow(["Y_h", h, d, f"{y[(h, d)]:.2f}", "", "", "", ""])
            t = tier[d]
            w.writerow(["tier", "", d, f"{t['mean']:.2f}", f"{t['lo']:.2f}", f"{t['hi']:.2f}", t["n_d"], t["class"]])
    plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False,
                         "font.family": "DejaVu Sans", "axes.titlesize": 8, "xtick.labelsize": 7,
                         "ytick.labelsize": 7})
    fig, ax = plt.subplots(figsize=(5.4, 3.7))
    blue, orange = "#0072B2", "#D55E00"       # Okabe-Ito
    ax.axhspan(-KBT, KBT, color="0.92", zorder=0, lw=0)
    ax.axhline(0, color="0.6", lw=0.6, zorder=1)
    for i, d in enumerate(DOPANTS):
        ys = [(h, y[(h, d)]) for h in HOSTS if (h, d) in y]
        for j, (h, v) in enumerate(ys):
            xx = i - 0.14 + 0.04 * (j - len(ys) / 2)
            if h == "m06":
                ax.plot(xx, v, "o", ms=5, mfc="white", mec=orange, mew=1.2, zorder=4)
                ax.annotate("host m06", xy=(xx, v - 3), xytext=(xx - 0.12, v - 55), color=orange, fontsize=7,
                            ha="left", arrowprops=dict(arrowstyle="-", color=orange, lw=0.6))
            else:
                ax.plot(xx, v, "o", ms=4.5, color=blue, alpha=0.85, mew=0, zorder=3)
        t = tier[d]
        ax.errorbar(i + 0.2, t["mean"], yerr=[[t["mean"] - t["lo"]], [t["hi"] - t["mean"]]], fmt="_", color="k",
                    ms=9, mew=1.4, elinewidth=1.2, capsize=3, zorder=5)
        lab = SHORT.get(t["class"], f"no class\n({t['n_d']} of 8 hosts valid)" if t["class"].startswith("no class") else t["class"])
        ax.text(i + 0.2, t["hi"] + 8, lab, ha="center", va="bottom", fontsize=7)
    ax.text(0.08, -KBT - 3.3, "band: $\\pm k_BT$", va="top", ha="left", fontsize=7, color="0.35")
    ax.text(-0.47, 228, "positive = repulsion", va="top", ha="left", fontsize=7, color="0.35")
    ax.set_xticks(range(4)); ax.set_xticklabels([SITE[d] for d in DOPANTS])
    ax.set_ylabel("Dopant–vacancy binding energy $Y_h$ (meV)", labelpad=6)
    ax.set_xlim(-0.5, 3.5); ax.set_ylim(-85, 235)
    ax.set_title("Only Sr is classed as repelling the iodide vacancy (fixed-geometry tier)", loc="left")
    fig.tight_layout()
    for ext in ("png", "pdf", "svg"):
        fig.savefig(os.path.join(HERE, f"fig_s2b_e_block4_Yh.{ext}"), dpi=300)
    cap = (f"{header} A1 tier of C3b (E block 4): host values Y_h (points; one per valid host), the mean and the "
           "interval I^A1_d (black), and the A1-tier class that E prints. Fixed-geometry DFT; relaxation bias not "
           "bounded; no calibrated tier (C4b not run). Band: ±k_BT = ±25.7 meV. Open marker: host m06 (post hoc "
           "observation). Source: s2b/E_output.txt, sections 4.2 and 4.3; source_data/fig_s2b_e_block4_Yh.csv.\n")
    open(os.path.join(HERE, "fig_s2b_e_block4_Yh.caption.txt"), "w", encoding="utf-8").write(cap)
    print("written", len(y), "host values;", {d: tier[d]["class"] for d in DOPANTS})


if __name__ == "__main__":
    main()

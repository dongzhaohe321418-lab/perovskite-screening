#!/usr/bin/env python
"""Figure WP1: dopant-vacancy binding energy E_b versus dopant-vacancy distance (MACE-MP-0, zero-shot).

Production map (PLAN WP1; amendments c, d, h, j): hosts m30, m21, m05, every Pb site (Sr) and every
FA site (GA), protocol v2.1 at the adopted depth fmax 0.01 eV/A, references at 0.005, E_b =
E[D_j+V] - E[D_j] - E[V] + E[host] (positive = repulsion). Shells from the unrelaxed geometry
(amendment d): Sr near d < 5.0, far d > 8.5 A; GA near d < 6.0, far d > 9.0 A. Open grey symbols:
rows invalid at 0.01 (far-field basin hop), never used. (a) Sr, (b) GA, with the pooled far mean
+/- SD of the valid far rows; (c) per-host near-minus-far against 2 x the pooled far SD (criterion 2).
Each point is one deterministic relaxation pair; no replicate error bars exist.

    python fig_wp1_binding_map.py --build      # source data from ../wp1_production/
    python fig_wp1_binding_map.py
"""
import argparse, csv, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source_data")
PROD = os.path.join(HERE, "..", "wp1_production")
COL = {"Sr": "#c4553a", "GA": "#2f6db5"}
MRK = {"m30": "o", "m21": "s", "m05": "^"}
NEAR = {"Sr": 5.0, "GA": 6.0}
FAR = {"Sr": 8.5, "GA": 9.0}


def build():
    import shutil
    shutil.copy(os.path.join(PROD, "wp1_map_rows.csv"), os.path.join(SRC, "wp1_map_rows.csv"))
    shutil.copy(os.path.join(PROD, "wp1_map.json"), os.path.join(SRC, "wp1_map.json"))
    print("source data copied")


def plot():
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    sys.path.insert(0, os.path.expanduser("~/.claude/skills/nature-figure/scripts"))
    try:      # layout QA from the nature-figure toolkit; optional, it does not touch the data
        from audit_panel_alignment import require_matplotlib_panel_alignment
    except ImportError:
        require_matplotlib_panel_alignment = None
        print("note: panel-alignment audit unavailable; figure rendered without it")
    mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                         "svg.fonttype": "none", "pdf.fonttype": 42, "font.size": 7.5,
                         "axes.spines.right": False, "axes.spines.top": False, "axes.linewidth": 0.8,
                         "legend.frameon": False, "xtick.major.width": 0.8, "ytick.major.width": 0.8})
    R = list(csv.DictReader(open(os.path.join(SRC, "wp1_map_rows.csv"))))
    M = json.load(open(os.path.join(SRC, "wp1_map.json")))["result"]
    fig, ax = plt.subplots(1, 3, figsize=(183 / 25.4, 66 / 25.4))
    fig.subplots_adjust(left=0.065, right=0.985, bottom=0.19, top=0.87, wspace=0.42)

    for k, dop in enumerate(("Sr", "GA")):
        a = ax[k]
        c1, c2 = M[dop]["criterion1"], M[dop]["criterion2"]
        a.axvspan(2.5, NEAR[dop], color="#f4f1ec", lw=0, zorder=0)       # within the x-limits only
        a.axvspan(FAR[dop], 12.5, color="#eef1f4", lw=0, zorder=0)
        fm, fs = c2["far_mean_meV"], c2["far_sd_meV"]
        a.fill_between([FAR[dop], 12.5], fm - fs, fm + fs, color=COL[dop], alpha=0.15, lw=0, zorder=1)
        a.plot([FAR[dop], 12.5], [fm, fm], color=COL[dop], lw=0.8, zorder=2)
        a.axhline(0, color="#4d4d4d", lw=0.6, zorder=1)
        for r in [r for r in R if r["dopant"] == dop]:
            x, y = float(r["d_A"]), float(r["Eb_meV"])
            if r["valid"] == "True":
                a.scatter(x, y, s=16, marker=MRK[r["host"]], color=COL[dop], edgecolor="white", linewidth=0.4, zorder=3)
            else:
                a.scatter(x, y, s=16, marker=MRK[r["host"]], facecolor="none", edgecolor="#9aa3ad", linewidth=0.7, zorder=3)
        a.set_xlim(2.5, 12.5)
        a.set_xlabel("Dopant–vacancy distance (Å)")
        a.set_ylabel(f"E$_b$ ({dop}) (meV)")
        crit1 = "pass" if c1["pass"] else f"fail (SD {c1['sd_meV']:.1f} > 25)"
        a.text(0.30 if dop == "Sr" else 0.97, 0.97,
               f"near − far {c2['near_minus_far_meV']:+.1f} meV\nhosts agreeing {c2['hosts_sign_agree']}\n".replace("-", "−")
               +
               f"criterion 1: {crit1}", transform=a.transAxes, ha="left" if dop == "Sr" else "right", va="top", fontsize=6)
        a.set_title({"Sr": "Sr on Pb sites", "GA": "GA on FA sites"}[dop], fontsize=7.5, pad=4)
    ax[0].set_ylim(-30, 200); ax[1].set_ylim(-75, 140)
    for axx, lo in ((ax[0], -28), (ax[1], -72)):           # shell labels at the bottom (empty there)
        axx.text(2.65, lo, "near", fontsize=6, color="#8a7f6e", va="bottom")
        axx.text(12.35, lo, "far", fontsize=6, color="#6e7a8a", va="bottom", ha="right")

    # (c) per-host near minus far vs 2 x pooled far SD
    c = ax[2]
    for k, dop in enumerate(("Sr", "GA")):
        c2 = M[dop]["criterion2"]; thr = 2 * c2["far_sd_meV"]
        c.add_patch(mpl.patches.Rectangle((k - 0.35, -thr), 0.7, 2 * thr, color=COL[dop], alpha=0.12, lw=0, zorder=0))
        for j, h in enumerate(("m30", "m21", "m05")):
            ph = M[dop]["per_host"][h]
            c.scatter(k + (j - 1) * 0.16, ph["near_minus_far"], s=22, marker=MRK[h], color=COL[dop],
                      edgecolor="white", linewidth=0.4, zorder=3)
        c.plot([k - 0.3, k + 0.3], [c2["near_minus_far_meV"]] * 2, color="#1a1a1a", lw=1.0, zorder=4)
        verdict = c2["verdict"].split(" (")[0]
        c.text(k, 178, verdict, ha="center", va="top", fontsize=6)
    c.axhline(0, color="#4d4d4d", lw=0.6)
    for h, m in MRK.items():               # one legend for all panels, in c's empty upper right
        c.scatter([], [], marker=m, color="#777777", s=14, label=h)
    c.scatter([], [], marker="o", facecolor="none", edgecolor="#9aa3ad", s=14, label="invalid (a, b)")
    c.legend(loc="upper right", bbox_to_anchor=(1.0, 0.88), fontsize=6, ncol=2, handletextpad=0.1,
             columnspacing=0.6, borderaxespad=0.2)
    c.set_xticks([0, 1], ["Sr", "GA"]); c.set_xlim(-0.6, 1.6); c.set_ylim(-80, 180)
    c.set_ylabel("Near − far E$_b$ (meV)")
    c.text(1.55, -76, "shaded: ±2 × pooled far SD", ha="right", va="bottom", fontsize=6, color="#555555")
    c.set_title("Criterion 2 by host", fontsize=7.5, pad=4)

    for lab, axx in zip("abc", ax):
        axx.text(-0.27, 1.12, lab, transform=axx.transAxes, fontsize=8, fontweight="bold", va="top")
    out = os.path.join(HERE, "fig_wp1_binding_map")
    fig.canvas.draw()
    if require_matplotlib_panel_alignment is not None:
        require_matplotlib_panel_alignment(fig, json_out=out + ".alignment.json", overlay_svg=out + ".alignment.svg",
                                           tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True)
    fig.savefig(out + ".pdf"); fig.savefig(out + ".svg"); fig.savefig(out + ".png", dpi=600)
    fig.savefig(out + ".tiff", dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    print("written", out + ".{pdf,svg,png,tiff}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--build", action="store_true"); a = ap.parse_args()
    if a.build:
        build()
    plot()

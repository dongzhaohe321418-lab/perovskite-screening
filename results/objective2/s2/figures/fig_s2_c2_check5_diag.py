#!/usr/bin/env python
"""Figure S2-C2-D: the check-5 diagnostic of amendment 2026-11-11a, part d, drawn from the printed read only.

Source: results/objective2/s2/c2_diagnostic/part_d_read_output.txt (the one part-d read, at 2b4657d). The figure plots
item-5 trajectories and annotates item-3 values; it reads no archive file and computes no new quantity.

  a  VB76 against hostB76, I (host 209): |dr| against the S2-relaxed MACE host at every configuration k of the child
     (VB76) and of the parent (hostB76).
  b  VB76 against hostB76, FA (host 212): rotation of the C-N-N skeleton against the same reference.
  c  Sr76o0_novac against hostB76, I (host 53), the gated inorganic atom of largest child-parent |dr| in that pair.
  d  Sr76o0_vac against VB76, FA (host 92), the gated FA of largest rotation in that pair: its carbon |dr| against the
     A1 V+_R76 geometry.

Each panel states the child-parent value at the final geometries (item 3), which is what check 5 tests. The dashed
line is the check-5 bound; it applies to that child-parent value, not to the curves, which are against a common
reference. Every point is one geometry of one deterministic relaxation: there are no replicates and no intervals.

    python fig_s2_c2_check5_diag.py
"""
import csv, os, re, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "c2_diagnostic", "part_d_read_output.txt")
OUT = os.path.join(HERE, "fig_s2_c2_check5_diag")
CSV = os.path.join(HERE, "source_data", "fig_s2_c2_check5_diag.csv")
P = "s2r_m30_"
PANELS = [  # (pair child, pair parent, object kind, host index, quantity, item-3 child-parent value, bound, unit)
    ("VB76", "hostB76", "I", 209, "dr", None, 0.25, "Å"),
    ("VB76", "hostB76", "FA", 212, "rot", None, 20.0, "°"),
    ("Sr76o0_novac", "hostB76", "I", 53, "dr", None, 0.25, "Å"),
    ("Sr76o0_vac", "VB76", "FA", 92, "dr", None, 0.25, "Å"),
]


def parse(path=SRC):
    """Item-3 rows {(child, host): row} and item-5 series {(child, kind, host, cell): {k: (dr, rot)}}."""
    txt = open(path).read()
    assert txt.startswith("part-d read at 2b4657d") and txt.rstrip().endswith("no calculator loaded"), "source"
    i3, i5 = txt.split("ITEM 3.")[1].split("ITEM 4.")[0], txt.split("ITEM 5.")[1]
    rows, pair = {}, None
    for ln in i3.splitlines():
        m = re.match(r"  (\S+) against (\S+): \d+ gated", ln)
        if m:
            pair = m.group(1)[len(P):]
            continue
        f = ln.split()
        if pair and len(f) >= 9 and f[0] in ("FA", "I", "Pb", "Cs"):
            rot = None if f[5] == "-" else float(f[5])
            rows[(pair, f[0] if f[0] == "FA" else "I" if f[0] == "I" else f[0], int(f[2]))] = \
                {"dr": float(f[4]), "rot": rot, "pass": f[-2] == "pass"}
    series, cur = {}, None
    for ln in i5.splitlines():
        m = re.match(r"  (\S+) against (\S+); (\S+) child \d+ host (\d+); (child|parent) (\S+);", ln)
        if m:
            cur = series.setdefault((m.group(1)[len(P):], m.group(3), int(m.group(4)), m.group(5)), {})
            continue
        f = ln.split()
        if cur is not None and f and f[0].isdigit():
            cur[int(f[0])] = (float(f[1]), float(f[2]) if len(f) > 2 else None)
    return rows, series


def plot():
    import matplotlib as mpl
    mpl.use("Agg")
    import matplotlib.pyplot as plt
    sys.path.insert(0, os.path.expanduser("~/.claude/skills/nature-figure/scripts"))
    try:
        from audit_panel_alignment import require_matplotlib_panel_alignment
    except ImportError:
        require_matplotlib_panel_alignment = None
    mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                         "svg.fonttype": "none", "pdf.fonttype": 42, "font.size": 7, "axes.spines.right": False,
                         "axes.spines.top": False, "axes.linewidth": 0.6, "xtick.major.width": 0.6,
                         "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
                         "svg.hashsalt": "fig_s2_c2_check5_diag"})
    CHILD, PARENT, INK, FAIL, OKC = "#d08a2e", "#7f8790", "#3a3a3a", "#c4553a", "#3a7d5a"
    rows, series = parse()
    out_rows = []
    fig, axs = plt.subplots(2, 2, figsize=(183 / 25.4, 112 / 25.4), sharex=True)
    fig.subplots_adjust(left=0.08, right=0.985, top=0.85, bottom=0.11, hspace=0.42, wspace=0.22)
    for ax, (ch, pa, kind, host, q, _, bound, unit), lab in zip(axs.flat, PANELS, "abcd"):
        r = rows[(ch, kind, host)]
        final = r["rot"] if q == "rot" else r["dr"]
        ok = r["pass"]
        ref = "A1 V (q = +1) geometry at Pb76" if ch == "Sr76o0_vac" else "S2-relaxed MACE host"
        for cell, name, col, ls in (("child", ch, CHILD, "-"), ("parent", pa, PARENT, "--")):
            s = series[(ch, kind, host, cell)]
            k = np.array(sorted(s))
            y = np.array([s[x][1] if q == "rot" else s[x][0] for x in k])
            ax.plot(k, y, color=col, ls=ls, lw=1.1)
            out_rows += [{"panel": lab, "pair": f"{ch} vs {pa}", "object": f"{kind} host {host}", "cell": cell,
                          "label": P + name, "k": int(a), "quantity": "rotation_deg" if q == "rot" else "dr_A",
                          "value": float(b), "reference": ref} for a, b in zip(k, y)]
        ax.axhline(bound, color=INK, lw=0.6, ls=(0, (3, 2)))
        ax.set_xlim(-2, 202)
        ax.set_ylim(0, 30 if q == "rot" else 0.5)
        what = "rotation" if q == "rot" else ("carbon |Δr|" if kind == "FA" else "|Δr|")
        ax.set_ylabel(f"{what} vs reference ({unit})")
        obj = f"{'FA' if kind == 'FA' else 'I'} (host index {host})"
        ax.set_title(f"child {ch} vs parent {pa}: {obj}", fontsize=7, pad=4)
        val = f"{final:.1f}{unit}" if q == "rot" else f"{final:.3f} {unit}"
        ax.text(0.03, 0.95, f"child − parent at the final geometries: {val} ({'pass' if ok else 'FAIL'})",
                transform=ax.transAxes, ha="left", va="top", fontsize=6, color=OKC if ok else FAIL)
        ax.text(0.03, 0.83, f"reference: {ref}", transform=ax.transAxes, ha="left", va="top", fontsize=6,
                color=INK)
    for ax in axs[1]:
        ax.set_xlabel("Configuration k (BFGS step, counted across restarts)")
    from matplotlib.lines import Line2D
    fig.legend([Line2D([], [], color=CHILD, lw=1.1), Line2D([], [], color=PARENT, lw=1.1, ls="--"),
                Line2D([], [], color=INK, lw=0.6, ls=(0, (3, 2)))],
               ["child cell", "parent cell", "check-5 bound (0.25 Å or 20°; it applies to child − parent at the final "
                "geometries, not to these curves)"], loc="upper center", bbox_to_anchor=(0.5, 0.955), ncol=3,
               fontsize=6, frameon=False, handlelength=2.6)
    fig.suptitle("Check 5 at the far site (Pb76): the failing pair and the two passing equal-charge pairs (part-d read)",
                 fontsize=7, y=0.985)
    for ax, lab in zip(axs.flat, "abcd"):
        p = ax.get_position()
        fig.text(p.x0 - 0.055, p.y1 + 0.045, lab, fontsize=8, fontweight="bold", va="top", ha="left")
    if require_matplotlib_panel_alignment is not None:
        require_matplotlib_panel_alignment(fig, json_out=OUT + ".alignment.json", overlay_svg=OUT + ".alignment.svg")
    fig.savefig(OUT + ".pdf", metadata={"CreationDate": None})
    fig.savefig(OUT + ".svg", metadata={"Date": None})
    fig.savefig(OUT + ".png", dpi=600)
    fig.savefig(OUT + ".tiff", dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    os.makedirs(os.path.dirname(CSV), exist_ok=True)
    with open(CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0])); w.writeheader(); w.writerows(out_rows)
    print(f"written {os.path.basename(OUT)}.{{pdf,svg,png,tiff}} and {os.path.basename(CSV)} ({len(out_rows)} rows)")


if __name__ == "__main__":
    plot()

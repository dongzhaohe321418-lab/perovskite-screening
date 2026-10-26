#!/usr/bin/env python
"""Figure WP1 depth gate (PLAN amendment j): how E_b depends on the FIRE fmax stage in the pilot.

Pilot: hosts m30, m21, m05 x {Sr, GA} x (2 nearest + 3 farthest sites) = 30 rows, protocol v2.1
(scripts/29: warm start, stages 0.02 -> 0.01 -> 0.005 eV/A, every validity check at every stage;
references relaxed to 0.005). (a) E_b(0.01) - E_b(0.02) for rows valid at both stages, against
the 5 meV tolerance; (b) rows invalid at each stage (all invalidity was far-field basin hops);
(c) E_b(0.005) - E_b(0.01): rows valid at both (filled) vs rows that hopped at 0.005 (open).
MACE-MP-0 medium, float64; each point is one deterministic relaxation pair.

    python fig_wp1_depth_gate.py --build     # source data from ../wp1_pilot/shell_m*.json
    python fig_wp1_depth_gate.py
"""
import argparse, csv, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source_data")
PILOT = os.path.join(HERE, "..", "wp1_pilot")
COL = {"Sr": "#c4553a", "GA": "#2f6db5"}
MRK = {"m30": "o", "m21": "s", "m05": "^"}
TOL = 5.0


def build():
    rows = []
    for h in ("m30", "m21", "m05"):
        d = json.load(open(os.path.join(PILOT, f"shell_{h}.json")))
        for r in d["rows"]:
            b = r["by_stage"]
            rows.append({"host": h, "dopant": r["dopant"], "site": r["site_host_index"], "d_A": r["d_dopant_vacancy_A"],
                         **{f"Eb_{s}": b[s]["Eb_meV"] for s in ("0.02", "0.01", "0.005")},
                         **{f"valid_{s}": int(b[s]["valid"]) for s in ("0.02", "0.01", "0.005")},
                         **{f"dr_novac_{s}": round(b[s]["basin_novac_vs_host"]["max_dr_A"], 3) for s in ("0.02", "0.01", "0.005")},
                         **{f"dr_vac_{s}": round(b[s]["basin_vac_vs_V"]["max_dr_A"], 3) for s in ("0.02", "0.01", "0.005")}})
    os.makedirs(SRC, exist_ok=True)
    with open(os.path.join(SRC, "wp1_depth_pilot.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("source data written")


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
    R = list(csv.DictReader(open(os.path.join(SRC, "wp1_depth_pilot.csv"))))
    f = lambda r, k: float(r[k]); v = lambda r, s: r[f"valid_{s}"] == "1"
    fig, ax = plt.subplots(1, 3, figsize=(183 / 25.4, 64 / 25.4))
    fig.subplots_adjust(left=0.07, right=0.985, bottom=0.2, top=0.86, wspace=0.45)
    rng = np.random.default_rng(0)                       # horizontal jitter only; values untouched

    # (a) 0.01 vs 0.02
    a = ax[0]
    a.axhspan(-TOL, TOL, color="#eceff2", lw=0, zorder=0)
    for i, dop in enumerate(("Sr", "GA")):
        rr = [r for r in R if r["dopant"] == dop]
        for r in rr:
            x = i + rng.uniform(-0.2, 0.2); y = f(r, "Eb_0.01") - f(r, "Eb_0.02")
            ok = v(r, "0.02") and v(r, "0.01")
            a.scatter(x, y, s=16, marker=MRK[r["host"]], facecolor=COL[dop] if ok else "none", edgecolor=COL[dop],
                      linewidth=0.7, zorder=3)
        both = [f(r, "Eb_0.01") - f(r, "Eb_0.02") for r in rr if v(r, "0.02") and v(r, "0.01")]
        a.text(i, -29, f"max |Δ| {max(map(abs, both)):.1f}\n(n = {len(both)})", ha="center", va="bottom", fontsize=6)
    a.axhline(0, color="#4d4d4d", lw=0.6)
    a.set_xticks([0, 1], ["Sr", "GA"]); a.set_xlim(-0.6, 1.6); a.set_ylim(-30, 45)
    a.set_ylabel("E$_b$(0.01) − E$_b$(0.02) (meV)")
    a.text(0.5, TOL + 0.8, "±5 meV", ha="center", va="bottom", fontsize=6, color="#555555")   # empty gap between groups
    a.set_title("Stage 0.02 → 0.01", fontsize=7.5, pad=4)

    # (b) invalid rows per stage
    b = ax[1]
    st = ("0.02", "0.01", "0.005"); w = 0.36
    for j, dop in enumerate(("Sr", "GA")):
        n = [sum(1 for r in R if r["dopant"] == dop and not v(r, s)) for s in st]
        xs = np.arange(3) + (j - 0.5) * w
        b.bar(xs, n, width=w, color=COL[dop], label=dop, zorder=2)
        for x_, n_ in zip(xs, n):
            b.text(x_, n_ + 0.25, str(n_), ha="center", va="bottom", fontsize=6)
    b.set_xticks(range(3), st); b.set_ylim(0, 16); b.set_yticks([0, 5, 10, 15])
    b.set_xlabel("fmax stage (eV/Å)"); b.set_ylabel("Rows invalid (of 15 per dopant)")
    leg = b.legend(loc="upper left", fontsize=6.5, handlelength=1.0, borderaxespad=0.2)
    b.add_artist(leg)
    hs = [b.scatter([], [], marker=m, facecolor="#777777", edgecolor="#777777", s=14, label=h) for h, m in MRK.items()]
    hs.append(b.scatter([], [], marker="o", facecolor="none", edgecolor="#777777", s=14, label="open: invalid"))
    b.legend(handles=hs, loc="upper left", bbox_to_anchor=(0.0, 0.78), fontsize=6, handletextpad=0.2, borderaxespad=0.2,
             title="markers (a, c)", title_fontsize=6)
    b.set_title("Far-field basin hops", fontsize=7.5, pad=4)

    # (c) 0.005 vs 0.01
    c = ax[2]
    c.axhspan(-TOL, TOL, color="#eceff2", lw=0, zorder=0)
    for i, dop in enumerate(("Sr", "GA")):
        for r in [r for r in R if r["dopant"] == dop and v(r, "0.01")]:
            x = i + rng.uniform(-0.2, 0.2); y = f(r, "Eb_0.005") - f(r, "Eb_0.01")
            ok = v(r, "0.005")
            c.scatter(x, y, s=16, marker=MRK[r["host"]], facecolor=COL[dop] if ok else "none", edgecolor=COL[dop],
                      linewidth=0.7, zorder=3)
    c.axhline(0, color="#4d4d4d", lw=0.6)
    c.set_yscale("symlog", linthresh=10, linscale=0.8)
    c.set_yticks([-100, -10, 0, 10, 100], ["−100", "−10", "0", "10", "100"])
    c.set_xticks([0, 1], ["Sr", "GA"]); c.set_xlim(-0.6, 1.6); c.set_ylim(-150, 300)
    c.set_ylabel("E$_b$(0.005) − E$_b$(0.01) (meV)")
    c.set_title("Stage 0.01 → 0.005", fontsize=7.5, pad=4)

    for lab, axx in zip("abc", ax):
        axx.text(-0.30, 1.13, lab, transform=axx.transAxes, fontsize=8, fontweight="bold", va="top")
    out = os.path.join(HERE, "fig_wp1_depth_gate")
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

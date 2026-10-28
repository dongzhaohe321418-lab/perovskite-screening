#!/usr/bin/env python
"""Figure WP2c/2d: does the MACE binding energy E_b transfer to DFT, and what is the finite-cell band term?

WP2c (PLAN criterion 4, amendments g, h): DFT single points (plain PBE, R point, scripts/30) on the
WP1 MACE-relaxed structures of hosts m30, m21, m05; E_b = E[D_j+V] - E[D_j] - E[V] + E[host]
(positive = repulsion), far-referenced (minus E_b at the far site of the same dopant, host and level).
(a) far-referenced E_b, MACE vs DFT, with the +/-25 meV criterion-4 band; filled = first-shell sites
(Sr hinge/flank, GA near), open = mid-shell sites. (b) MACE - DFT against the unrelaxed
dopant-vacancy distance; grey ticks: the same error after removing the band residual
[E_F(D+V) - E_F(V)] - [same at the far site] one-to-one (diagnostic only, not used by criterion 4).
(c) WP2d (m30): change on removing the V_I0 electron (q = 0 minus q = +1) against the neutral-cell
Fermi-level shift; E_b sites and the img3 - img0 energy difference of the Sr - undoped pair.
Every value is one deterministic single point (or difference of four); no replicate error bars exist.

    python fig_wp2c_eb_transfer.py --build      # source data from ../wp2c/wp2cde_dft.json
    python fig_wp2c_eb_transfer.py
"""
import argparse, csv, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source_data")
DFT = os.path.join(HERE, "..", "wp2c", "wp2cde_dft.json")
COL = {"Sr": "#c4553a", "GA": "#2f6db5"}
MRK = {"m30": "o", "m21": "s", "m05": "^"}
TOL = 25.0


def build():
    d = json.load(open(DFT))
    rows = []
    for h in ("m30", "m21", "m05"):
        for dop in ("Sr", "GA"):
            for name, r in d["wp2c"][h][dop]["rows"].items():
                rows.append({"host": h, "dopant": dop, "site_class": name.split("_")[1], "site": r["site"], "d_A": r["d_A"],
                             "Eb_dft_farref_meV": r["Eb_dft_farref_meV"], "Eb_mace_farref_meV": r["Eb_mace_farref_meV"],
                             "farref_error_meV": r["farref_error_meV"], "band_residual_meV": r["band_residual_meV"],
                             "Eb_dft_raw_meV": r["Eb_dft_meV"], "Eb_mace_raw_meV": r["Eb_mace_meV"], "dEF_meV": r["dEF_meV"]})
    os.makedirs(SRC, exist_ok=True)
    with open(os.path.join(SRC, "wp2c_sites.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    q = d["wp2d"]["m30"]; bt = []
    for dop in ("Sr", "GA"):
        for name, r in q[dop]["rows"].items():
            bt.append({"item": f"E_b {name}", "dopant": dop, "first_shell": int(not name.endswith("_far")),
                       "dEF_q0_meV": r["dEF_q0_meV"], "q0_minus_q1_meV": r["q0_minus_q1_meV"]})
    x = q["dEa_img03"]
    bt.append({"item": "dE(img3-img0) Sr-undoped", "dopant": "pair", "first_shell": "",
               "dEF_q0_meV": x["band_term_q0_meV"], "q0_minus_q1_meV": x["q0_minus_q1_meV"]})
    with open(os.path.join(SRC, "wp2d_bandterm.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(bt[0])); w.writeheader(); w.writerows(bt)
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
    R = list(csv.DictReader(open(os.path.join(SRC, "wp2c_sites.csv"))))
    B = list(csv.DictReader(open(os.path.join(SRC, "wp2d_bandterm.csv"))))
    f = lambda r, k: float(r[k])
    tested = [r for r in R if r["site_class"] != "far"]
    first = lambda r: r["site_class"] in ("hinge", "flank", "near")
    fig, ax = plt.subplots(1, 3, figsize=(183 / 25.4, 66 / 25.4))
    fig.subplots_adjust(left=0.075, right=0.985, bottom=0.19, top=0.87, wspace=0.42)

    def pt(a, x, y, r, s=18):
        fc = COL[r["dopant"]] if first(r) else "white"
        a.scatter(x, y, s=s, marker=MRK[r["host"]], facecolor=fc, edgecolor=COL[r["dopant"]], linewidth=0.8, zorder=3)

    # (a) parity of far-referenced E_b
    a = ax[0]; lim = (-75, 180)
    xx = np.linspace(*lim, 256)                                 # band clipped to the axes box
    a.fill_between(xx, np.clip(xx - TOL, *lim), np.clip(xx + TOL, *lim), color="#eceff2", lw=0, zorder=0)
    a.plot(lim, lim, color="#4d4d4d", lw=0.6, zorder=1)
    for r in tested:
        pt(a, f(r, "Eb_dft_farref_meV"), f(r, "Eb_mace_farref_meV"), r)
    a.set_xlim(lim); a.set_ylim(lim)
    a.set_xticks([-50, 0, 50, 100, 150]); a.set_yticks([-50, 0, 50, 100, 150])
    a.set_xlabel("E$_b$ − E$_b$(far), DFT (meV)"); a.set_ylabel("E$_b$ − E$_b$(far), MACE (meV)")
    a.text(-70, 172, "Sr first shell", fontsize=6, color=COL["Sr"], va="top")
    a.text(-70, 158, "GA", fontsize=6, color=COL["GA"], va="top")
    a.set_title("Far-referenced E$_b$", fontsize=7.5, pad=4)

    # (b) error against distance, with the band-residual diagnostic
    b = ax[1]
    b.axhspan(-TOL, TOL, color="#eceff2", lw=0, zorder=0)
    b.axhline(0, color="#4d4d4d", lw=0.6, zorder=1)
    off = {"m30": -0.12, "m21": 0.0, "m05": 0.12}             # horizontal offset only; values untouched
    for r in tested:
        x = f(r, "d_A") + off[r["host"]]; y = f(r, "farref_error_meV"); yc = y + f(r, "band_residual_meV")
        if abs(yc - y) > 1.0:
            b.plot([x, x], [y, yc], color="#9aa3ad", lw=0.6, zorder=2)
            b.plot([x - 0.12, x + 0.12], [yc, yc], color="#6e7a8a", lw=0.9, zorder=2)
        pt(b, x, y, r)
    b.set_xlim(2.5, 8.6); b.set_ylim(-70, 50)
    b.set_xlabel("Dopant–vacancy distance (Å)"); b.set_ylabel("MACE − DFT, far-referenced (meV)")
    b.text(8.55, 48, "grey tick: band residual removed\n(diagnostic, not used)", ha="right", va="top", fontsize=6, color="#555555")
    b.set_title("Criterion 4: 6 of 15 sites outside ±25 meV", fontsize=7.5, pad=4)

    # (c) WP2d band-term test
    c = ax[2]; lim_c = (-55, 60)
    c.plot(lim_c, lim_c, color="#4d4d4d", lw=0.6, zorder=1)
    c.axhline(0, color="#d0d4d9", lw=0.5, zorder=0)
    for r in B:
        x, y = f(r, "dEF_q0_meV"), f(r, "q0_minus_q1_meV")
        if r["dopant"] == "pair":
            c.scatter(x, y, s=24, marker="D", facecolor="#1a1a1a", edgecolor="#1a1a1a", zorder=3)
            c.annotate("ΔE(img3 − img0),\nSr − undoped", xy=(x, y + 3), xytext=(-53, 13), fontsize=6, va="center", ha="left",
                       arrowprops=dict(arrowstyle="-", color="#555555", lw=0.5, shrinkA=1, shrinkB=1))
        else:
            c.scatter(x, y, s=20, marker="o", facecolor=COL[r["dopant"]] if r["first_shell"] == "1" else "white",
                      edgecolor=COL[r["dopant"]], linewidth=0.8, zorder=3)
    c.text(59, 22, "Sr: hinge, far", fontsize=6, color=COL["Sr"], ha="right", va="center")
    c.text(21, 8, "GA: near, far", fontsize=6, color=COL["GA"], ha="left", va="top")
    c.set_xlim(lim_c); c.set_ylim(lim_c)
    c.set_xticks([-50, -25, 0, 25, 50]); c.set_yticks([-50, -25, 0, 25, 50])
    c.set_xlabel("Neutral-cell Fermi-level shift (meV)"); c.set_ylabel("Change, q = 0 minus q = +1 (meV)")
    c.text(-52, 56, "y = x", fontsize=6, color="#555555", va="top")
    c.set_title("WP2d (m30): the band term", fontsize=7.5, pad=4)

    hs = [c.scatter([], [], marker=m, facecolor="#777777", edgecolor="#777777", s=14, label=h) for h, m in MRK.items()]
    hs.append(c.scatter([], [], marker="o", facecolor="white", edgecolor="#777777", s=14, label="Open: mid (a, b), far (c)"))
    hs.append(mpl.patches.Patch(color="#dfe3e8", label="±25 meV (a, b)"))
    c.legend(handles=hs, loc="lower right", fontsize=6, handletextpad=0.3, borderaxespad=0.2, labelspacing=0.3)   # empty lower right of (c)

    for lab, axx in zip("abc", ax):
        axx.text(-0.27, 1.12, lab, transform=axx.transAxes, fontsize=8, fontweight="bold", va="top")
    out = os.path.join(HERE, "fig_wp2c_eb_transfer")
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

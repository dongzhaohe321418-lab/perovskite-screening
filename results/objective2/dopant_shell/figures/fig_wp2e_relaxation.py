#!/usr/bin/env python
"""Figure WP2e: where the DFT relaxation of a MACE endpoint puts its energy (m30 GA, image 0).

Fixed-cell BFGS (plain PBE, R point, forc_conv_thr 0.02 eV/A) from the MACE band frame; 283 SCF
cycles, converged. (a) F - F(start) along the relaxation (first 10 cycles shaded). (b) Share of
the path work W_i = -sum_k 1/2 (F_i^k + F_i^(k+1)) . dr_i^k (trapezoid rule; sums to the relaxation
energy within 1.2 meV) and share of atoms, per shell of distance to the nearer defect centre
(vacancy site, GA carbon); organic atoms take their molecule's C distance. Per-atom work is printed
above each pair. (c) Per-atom displacement |dr| (net translation removed) against that atom's own
distance, with shell means. One relaxation; no replicate, so no error bars. PLAN amendments k, l.

    python fig_wp2e_relaxation.py --build      # source data from ../wp2e/
    python fig_wp2e_relaxation.py
"""
import argparse, csv, os, shutil, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source_data")
WP2E = os.path.join(HERE, "..", "wp2e")
TAG = "m30_GA_img0"
SHELLS = [(0, 4), (4, 6), (6, 8), (8, 10), (10, 99)]
ORG = {"C", "N", "H"}


def build():
    os.makedirs(SRC, exist_ok=True)
    for f in (f"wp2e_atoms_{TAG}.csv", f"wp2e_trajectory_{TAG}.csv"):
        shutil.copy(os.path.join(WP2E, f), os.path.join(SRC, f))
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
    A = list(csv.DictReader(open(os.path.join(SRC, f"wp2e_atoms_{TAG}.csv"))))
    T = list(csv.DictReader(open(os.path.join(SRC, f"wp2e_trajectory_{TAG}.csv"))))
    d = np.array([float(r["d_A"]) for r in A]); dmol = np.array([float(r["d_molecule_A"]) for r in A])
    dr = np.array([float(r["dr_A"]) for r in A]); W = np.array([float(r["W_meV"]) for r in A])
    org = np.array([r["symbol"] in ORG for r in A])
    k = np.array([int(r["scf_cycle"]) for r in T]); E = np.array([float(r["F_minus_F0_meV"]) for r in T])

    fig, ax = plt.subplots(1, 3, figsize=(183 / 25.4, 62 / 25.4))
    fig.subplots_adjust(left=0.085, right=0.985, bottom=0.2, top=0.86, wspace=0.42)

    # (a) energy trajectory
    a = ax[0]
    a.axvspan(0, 10, color="#eceff2", lw=0, zorder=0)
    a.plot(k, E, color="#1a1a1a", lw=1.0, zorder=2)
    a.axhline(0, color="#9aa3ad", lw=0.5, zorder=1)
    a.set_xlim(0, k.max() + 5); a.set_ylim(-1050, 50)
    a.set_xlabel("SCF cycle (BFGS)"); a.set_ylabel("F − F(start) (meV)")
    a.text(20, -200, f"first 10 cycles (shaded): {E[10]:.0f} meV".replace("-", "−"), fontsize=6, va="center")
    a.text(k.max(), E[-1] + 25, f"{E[-1]:.0f} meV".replace("-", "−"), fontsize=6, ha="right", va="bottom")
    a.set_title("DFT relaxation from MACE geometry", fontsize=7.5, pad=4)

    # (b) share of path work vs share of atoms, per shell (molecule-assigned)
    b = ax[1]; x = np.arange(len(SHELLS)); w = 0.38
    sa = [((dmol >= lo) & (dmol < hi)).sum() / len(dmol) * 100 for lo, hi in SHELLS]
    sw = [W[(dmol >= lo) & (dmol < hi)].sum() / W.sum() * 100 for lo, hi in SHELLS]
    pa = [W[(dmol >= lo) & (dmol < hi)].mean() for lo, hi in SHELLS]
    b.bar(x - w / 2, sa, width=w, color="#c9ced4", label="Atoms", zorder=2)
    b.bar(x + w / 2, sw, width=w, color="#2f6db5", label="Relaxation energy", zorder=2)
    for i in range(len(SHELLS)):
        b.text(x[i], max(sa[i], sw[i]) + 1.2, f"{pa[i]:.1f}".replace("-", "−"), ha="center", va="bottom", fontsize=6)
    b.set_xticks(x, ["0–4", "4–6", "6–8", "8–10", ">10"])
    b.set_xlabel("Distance to nearer defect (Å)"); b.set_ylabel("Share (%)")
    b.set_ylim(0, 48)
    b.legend(loc="upper left", fontsize=6, handlelength=1.0, borderaxespad=0.2)
    b.text(0.98, 0.97, "numbers: path work\nper atom (meV)", transform=b.transAxes, fontsize=6, va="top", ha="right", color="#555555")
    b.set_title("Energy follows atom count", fontsize=7.5, pad=4)

    # (c) per-atom displacement against distance
    c = ax[2]
    c.axvline(6.0, color="#9aa3ad", lw=0.6, ls=(0, (3, 2)), zorder=1)
    c.scatter(d[~org], dr[~org], s=5, color="#c4553a", lw=0, alpha=0.8, zorder=2, label="Pb, I, Cs")
    c.scatter(d[org], dr[org], s=5, color="#2f6db5", lw=0, alpha=0.6, zorder=2, label="C, N, H")
    mids, means = [], []
    for lo, hi in SHELLS:
        m = (d >= lo) & (d < hi)
        mids.append(np.median(d[m])); means.append(dr[m].mean())
    c.plot(mids, means, color="#1a1a1a", lw=1.0, marker="o", ms=3, zorder=3, label="Shell mean")
    c.set_xlim(0, 13); c.set_ylim(0, 1.85); c.set_yticks([0, 0.5, 1.0, 1.5])
    c.set_xlabel("Distance to nearer defect (Å)"); c.set_ylabel("|Δr| (Å)")
    c.text(5.85, 1.82, "6 Å", fontsize=6, color="#555555", va="top", ha="right")
    c.legend(loc="upper right", fontsize=6, handletextpad=0.2, borderaxespad=0.2, markerscale=1.6, ncol=1)
    c.set_title("Displacement does not decay", fontsize=7.5, pad=4)

    for lab, axx in zip("abc", ax):
        axx.text(-0.27, 1.13, lab, transform=axx.transAxes, fontsize=8, fontweight="bold", va="top")
    out = os.path.join(HERE, "fig_wp2e_relaxation")
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

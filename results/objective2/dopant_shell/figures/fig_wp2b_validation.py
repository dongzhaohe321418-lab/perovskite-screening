#!/usr/bin/env python
"""Figure WP2b: zero-shot MACE-MP-0 vs fixed-geometry DFT on the corpus NEB bands.

Panels: (a) paired dE_a = E_a(dopant) - E_a(undoped), MACE vs DFT, with the +/-59.5 meV
equivalence band (criterion 3); (b) E_a along the MACE path, MACE vs DFT, every complete band;
(c) residual DFT force (per-atom RMS) at the MACE minima (images 0, 6) and saddle (image 3) against
the criterion-5 gate; (d) dopant-induced shift of the Fermi level of the neutral V_I cell at
image 0 (the finite-cell band term of PLAN amendment g; raw E_F, not potential-aligned).

DFT: plain PBE, R point, Gaussian 0.005 Ry, nspin 1, F = "! total energy" (scripts/30); MACE:
MACE-MP-0 medium float64 on the same frames (scripts/32). DFT values on MACE geometries are
fixed-path diagnostics, not relaxed DFT barriers. Each point is one deterministic calculation.

    python fig_wp2b_validation.py --build --val <wp2b_validation.json> --dft <QE outputs dir>
    python fig_wp2b_validation.py [--out <dir>]          # plot from source_data/wp2b_*.csv
"""
import argparse, csv, glob, json, os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source_data")
BAND, RMS_GATE, F_GATE = 59.5, 20.0, 0.05
COL = {"undoped": "#9aa3ad", "GA": "#2f6db5", "Sr": "#c4553a"}
MRK = {"undoped": "o", "GA": "o", "Sr": "s"}


def fermi(path):
    t = open(path, errors="replace").read()
    m = re.findall(r"the Fermi energy is\s+([-\d.]+)\s+ev", t)
    return float(m[-1]) if m and "JOB DONE" in t else None


def write_csv(fn, rows):
    with open(os.path.join(SRC, fn), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def build(val, dft):
    d = json.load(open(val))
    os.makedirs(SRC, exist_ok=True)
    write_csv("wp2b_pairs.csv", d["pairs"])
    write_csv("wp2b_bands.csv", [{k: (v if not isinstance(v, list) else " ".join(map(str, v))) for k, v in b.items()}
                                 for b in d["bands"]])
    write_csv("wp2b_frames.csv", d["frames"])
    outs = {os.path.basename(f)[:-4]: f for f in glob.glob(os.path.join(dft, "**", "*.out"), recursive=True)}
    rows = []
    for p in d["pairs"]:                  # pairs = both bands complete (scripts/32)
        h, s = p["host"], p["dopant"]
        for img in (0, 3):
            eu, ed = fermi(outs[f"{h}_undoped_img{img}"]), fermi(outs[f"{h}_{s}_img{img}"])
            rows.append({"host": h, "dopant": s, "image": img, "EF_undoped_eV": eu, "EF_doped_eV": ed,
                         "dEF_meV": round((ed - eu) * 1000, 1)})
    write_csv("wp2b_fermi.csv", rows)
    json.dump({"summary": d["summary"], "source": os.path.abspath(val)},
              open(os.path.join(SRC, "wp2b_summary.json"), "w"), indent=1)
    print("source data written")


def plot(outdir):
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    sys.path.insert(0, os.path.expanduser("~/.claude/skills/nature-figure/scripts"))
    try:      # layout QA from the nature-figure toolkit; optional, it does not touch the data
        from audit_panel_alignment import require_matplotlib_panel_alignment
    except ImportError:
        require_matplotlib_panel_alignment = None
        print("note: panel-alignment audit unavailable; figure rendered without it")
    mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                         "svg.fonttype": "none", "pdf.fonttype": 42, "font.size": 7.5,   # 7.5: sub/superscripts stay >= 5 pt
                         "axes.spines.right": False, "axes.spines.top": False, "axes.linewidth": 0.8,
                         "legend.frameon": False, "xtick.major.width": 0.8, "ytick.major.width": 0.8})
    rd = lambda fn: list(csv.DictReader(open(os.path.join(SRC, fn))))
    P, B, Fr, EF = rd("wp2b_pairs.csv"), rd("wp2b_bands.csv"), rd("wp2b_frames.csv"), rd("wp2b_fermi.csv")
    S = json.load(open(os.path.join(SRC, "wp2b_summary.json")))["summary"]
    c3 = S["criterion3"]

    fig, axs = plt.subplots(2, 2, figsize=(136 / 25.4, 132 / 25.4))
    fig.subplots_adjust(left=0.11, right=0.97, bottom=0.085, top=0.94, wspace=0.42, hspace=0.42)
    a, b, c, d = axs.ravel()
    for ax in axs.ravel():
        ax.set_box_aspect(1)          # equal square plot boxes; parity panels use equal x/y limits

    # (a) paired dE_a parity
    x = np.array([float(p["dEa_dft_meV"]) for p in P]); y = np.array([float(p["dEa_mace_meV"]) for p in P])
    lim = max(100.0, float(np.ceil(np.max(np.abs(np.r_[x, y])) / 20 + 1) * 20))
    a.add_patch(mpl.patches.Rectangle((-BAND, -BAND), 2 * BAND, 2 * BAND, color="#eceff2", zorder=0, lw=0))
    a.plot([-lim, lim], [-lim, lim], color="#4d4d4d", lw=0.6, ls=(0, (3, 2)), zorder=1)
    for s in ("GA", "Sr"):
        m = [p["dopant"] == s for p in P]
        a.scatter(x[m], y[m], s=20, marker=MRK[s], color=COL[s], edgecolor="white", linewidth=0.4, zorder=3,
                  label=f"{s} (n = {int(np.sum(m))})")
    flips = [p for p in P if p["class_dft"] != p["class_mace"]]
    for p in flips:
        a.scatter(float(p["dEa_dft_meV"]), float(p["dEa_mace_meV"]), s=60, facecolor="none", edgecolor="#1a1a1a",
                  linewidth=0.7, zorder=4)
    a.set_xlim(-lim, lim); a.set_ylim(-lim, lim)
    a.set_xlabel("ΔE$_a$ DFT on MACE path (meV)"); a.set_ylabel("ΔE$_a$ MACE (meV)")
    a.legend(loc="lower right", fontsize=6, handletextpad=0.2, borderaxespad=0.2)
    rms = c3["rms_error_meV"]
    a.text(0.03, 0.97, f"{c3['n_pairs']}/{c3['expected']} pairs, RMS {rms:.1f} meV\n"
                        f"{len(flips)} band crossing(s) circled\ncriterion 3: {c3['verdict']}",
           transform=a.transAxes, ha="left", va="top", fontsize=6)
    a.set_title("Paired barrier difference", fontsize=7.5, pad=4)

    # (b) E_a along the MACE path, every complete band
    for s in ("undoped", "GA", "Sr"):
        bb = [r for r in B if r["system"] == s]
        a_ = np.array([float(r["Ea_dft_meV"]) for r in bb]); m_ = np.array([float(r["Ea_mace_meV"]) for r in bb])
        b.scatter(a_, m_, s=16, marker=MRK[s], color=COL[s], edgecolor="white", linewidth=0.4, zorder=3,
                  label=f"{s} (n = {len(bb)})")
    allv = np.array([float(r[k]) for r in B for k in ("Ea_dft_meV", "Ea_mace_meV")])
    lo, hi = min(0.0, float(allv.min()) - 10), float(np.ceil(allv.max() / 50 + 0.5) * 50)
    b.plot([lo, hi], [lo, hi], color="#4d4d4d", lw=0.6, ls=(0, (3, 2)), zorder=1)
    b.set_xlim(lo, hi); b.set_ylim(lo, hi)
    b.set_xlabel("E$_a$ DFT on MACE path (meV)"); b.set_ylabel("E$_a$ MACE (meV)")
    b.legend(loc="lower right", fontsize=6, handletextpad=0.2, borderaxespad=0.2)
    b.set_title("Barrier along the MACE path", fontsize=7.5, pad=4)

    # (c) residual DFT force at MACE stationary points
    rng = np.random.default_rng(0)                      # horizontal jitter only; values untouched
    groups = [("minima\n(img 0, 6)", [r for r in Fr if r["image"] in ("0", "6")]),
              ("saddle\n(img 3)", [r for r in Fr if r["image"] == "3"])]
    for i, (lab, rows) in enumerate(groups):
        for s in ("undoped", "GA", "Sr"):
            v = np.array([float(r["dft_frms_eVA"]) for r in rows if r["system"] == s])
            c.scatter(i + rng.uniform(-0.25, 0.25, v.size), v, s=8, marker=MRK[s], color=COL[s], alpha=0.85,
                      linewidth=0, zorder=2)
        npass = sum(1 for r in rows if float(r["dft_frms_eVA"]) < F_GATE and float(r["dft_fmax_eVA"]) < 0.2)
        c.text(i, 0.012, f"{npass}/{len(rows)} pass", ha="center", va="bottom", fontsize=6, color="#555555")
    c.axhline(F_GATE, color="#c4553a", lw=0.6, ls=(0, (3, 2)))
    c.text(1.45, F_GATE + 0.004, "RMS gate 0.05", ha="right", va="bottom", fontsize=6, color="#c4553a")
    c.set_xticks([0, 1], [g[0] for g in groups]); c.set_xlim(-0.6, 1.6); c.set_ylim(0, 0.2)
    c.set_ylabel("Residual DFT force, RMS (eV/Å)")
    c.set_title("DFT force at MACE stationary points", fontsize=7.5, pad=4)

    # (d) dopant-induced Fermi-level shift of the neutral V_I cell (image 0)
    for i, s in enumerate(("GA", "Sr")):
        v = np.array([float(r["dEF_meV"]) for r in EF if r["dopant"] == s and r["image"] == "0"])
        d.scatter(i + rng.uniform(-0.18, 0.18, v.size), v, s=14, marker=MRK[s], color=COL[s], edgecolor="white",
                  linewidth=0.4, zorder=3)
        if v.size:
            d.plot([i - 0.28, i + 0.28], [v.mean()] * 2, color="#1a1a1a", lw=1.0, zorder=4)
            d.text(i + 0.32, v.mean(), f"{v.mean():+.0f}", ha="left", va="center", fontsize=6)
    d.axhline(0, color="#4d4d4d", lw=0.6)
    d.set_xticks([0, 1], ["GA", "Sr"]); d.set_xlim(-0.6, 1.7)
    d.set_ylabel("E$_F$(doped) − E$_F$(undoped), image 0 (meV)")
    d.set_title("Dopant-induced E$_F$ shift (not aligned)", fontsize=7.5, pad=4)

    for lab, ax in zip("abcd", axs.ravel()):
        ax.text(-0.30, 1.12, lab, transform=ax.transAxes, fontsize=8, fontweight="bold", va="top")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "fig_wp2b_validation")
    fig.canvas.draw()
    if require_matplotlib_panel_alignment is not None:
        require_matplotlib_panel_alignment(fig, json_out=out + ".alignment.json", overlay_svg=out + ".alignment.svg",
                                           tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True)
    fig.savefig(out + ".pdf"); fig.savefig(out + ".svg"); fig.savefig(out + ".png", dpi=600)
    fig.savefig(out + ".tiff", dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    print("written", out + ".{pdf,svg,png,tiff}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--val"); ap.add_argument("--dft")
    ap.add_argument("--out", default=HERE)
    ap.add_argument("--src", default=SRC, help="source-data dir (default figures/source_data)")
    a = ap.parse_args()
    SRC = a.src
    if a.build:
        build(a.val, a.dft)
    plot(a.out)

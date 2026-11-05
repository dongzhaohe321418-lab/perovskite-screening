#!/usr/bin/env python
"""Figure S2-C1: the campaign-1 gates of S2_PLAN sections 7-8 and the A2 layout, as decided on the node.

Claim: all five dopants pass gate N, with a pooled far-site SD of at most 17.8 meV against the
25 meV bound. No member of the decisive family that passed G1 lies above 20 meV, so n = 8.
Cl passes the elements gate G1. Ca fails G1 on the cutoff part (|Delta_cut| = 49.4 meV against
5 meV) and leaves the decisive family (S2_PLAN section 7). A2 runs at 64 ranks.

Data (all committed): the node's gate files results/objective2/s2/c1/gates/{N,G1,throughput}.json,
written by scripts/49_s2_gates.py at the campaign commit 8bff03e. They were re-verified from the
archive on the laptop: 5 gate files, 0 differ. This script recomputes nothing that a gate decided.
It re-derives the pooled SD, the n rule, the G1 bounds and the layout rule from the gate inputs as a
consistency check, and asserts that each equals the gate's decision.

Each point is one deterministic DFT result: a raw E_b combines four PBE single points, SCF to
convergence. There are no replicates, so the figure shows no error bars. The site-to-site scatter
in panel a is the quantity that gate N measures.

Layout QA (optional; it does not touch the data): the panel-alignment and PDF collision audits come from the
external nature-figure toolkit (~/.claude/skills/nature-figure/scripts); the committed .alignment.* and
.collision-audit.json files are its outputs.

    python fig_s2_c1_gates.py --build   # (re)extract source data from the gate files
    python fig_s2_c1_gates.py           # plot from source_data/*.csv
"""
import argparse, csv, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
C1 = os.path.join(HERE, "..", "c1")
SRC = os.path.join(HERE, "source_data")
DOPANTS = ["Sr", "Ca", "Cl", "Cs", "GA"]                 # S2_PLAN section 2: control Sr, decisive Ca Cl Cs GA
DECISIVE = ("Ca", "Cl", "Cs", "GA")
HOSTS = ["m30", "m05"]
GATE_N_MEV, NRULE_MEV, G1_CUT_MEV, G1_SPIN_MEV, TP_FACTOR = 25.0, 20.0, 5.0, 3.0, 1.15   # sections 7, 8; X-4


def gate(name):
    d = json.load(open(os.path.join(C1, "gates", f"{name}.json")))
    assert d["campaign"] == "c1" and d["gate"] == name, name
    return d


def build():
    N, G1, TP = gate("N"), gate("G1"), gate("throughput")
    sites, sig = [], []
    for d in DOPANTS:
        r = N["result"]["dopants"][d]
        dev2, dof = 0.0, 0
        for h in HOSTS:
            hh = r["hosts"][h]
            v = {int(s): float(x) for s, x in hh["per_site_meV"].items()}
            mean = sum(v.values()) / len(v)
            assert abs(mean - hh["offset_meV"]) < 1e-9 and hh["k"] == len(v), (d, h)
            dev2 += sum((x - mean) ** 2 for x in v.values()); dof += len(v) - 1
            for s in sorted(v):
                sites.append({"dopant": d, "host": h, "site": s, "Eb_far_meV": repr(v[s]),
                              "host_mean_meV": repr(hh["offset_meV"])})
        s_re = math.sqrt(dev2 / dof)
        assert abs(s_re - r["sigma_far_meV"]) < 1e-9 and dof == r["df"], (d, s_re, r["sigma_far_meV"])
        sig.append({"dopant": d, "sigma_far_meV": repr(r["sigma_far_meV"]), "df": r["df"],
                    "gateN_pass": r["pass"], "G1_pass": G1["decision"]["G1"].get(d, "not_tested"),
                    "counts_for_n": d in DECISIVE and r["pass"] and G1["decision"]["G1"].get(d, True)})
    assert N["decision"]["gateN"] == {d: True for d in DOPANTS} and N["decision"]["sr_stop"] is False
    n_re = 10 if any(r["counts_for_n"] and NRULE_MEV < float(r["sigma_far_meV"]) <= GATE_N_MEV for r in sig) else 8
    assert gate("nrule")["decision"]["n"] == n_re == 8                      # section 8 n rule
    g1 = []
    for el in ("Cl", "Ca"):
        r = G1["result"][el]
        g1.append({"element": el, "delta_cut_meV": repr(r["delta_cut_meV"]), "dF_spin_meV": repr(r["dF_spin_meV"]),
                   "M_total_muB": r["M_total_muB"], "M_abs_muB": r["M_abs_muB"], "cut_pass": r["cut_pass"],
                   "spin_pass": r["spin_pass"], "valence_pass": r["valence_pass"], "pass": r["pass"]})
        assert r["cut_pass"] == (abs(r["delta_cut_meV"]) <= G1_CUT_MEV)       # section 7 bounds
        assert r["spin_pass"] == (abs(r["dF_spin_meV"]) <= G1_SPIN_MEV and abs(r["M_total_muB"]) < 0.1)
        assert G1["decision"]["G1"][el] == (r["cut_pass"] and r["spin_pass"] and r["valence_pass"])
    tp = [{"layout": k, "rate_config_per_node_h": repr(v), "chosen": k == TP["result"]["choice"]}
          for k, v in TP["result"]["rate_config_per_node_h"].items()]
    rt = TP["result"]["rate_config_per_node_h"]
    best = max(("64", "2x32"), key=lambda k: rt[k])                          # highest rate, if >= 1.15 x rate(48)
    assert TP["result"]["choice"] == (best if rt[best] >= TP_FACTOR * rt["48"] else "48") == "64"
    os.makedirs(SRC, exist_ok=True)
    for fn, rows in (("fig_s2_c1_a_far_sites.csv", sites), ("fig_s2_c1_b_sigma_far.csv", sig),
                     ("fig_s2_c1_c_g1.csv", g1), ("fig_s2_c1_d_throughput.csv", tp)):
        with open(os.path.join(SRC, fn), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("source data written:", len(sites), "far-site values,", len(sig), "dopants")


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
                         "svg.fonttype": "none", "pdf.fonttype": 42, "font.size": 7,
                         "axes.spines.right": False, "axes.spines.top": False, "axes.linewidth": 0.8,
                         "legend.frameon": False, "xtick.major.width": 0.8, "ytick.major.width": 0.8})
    rd = lambda fn: list(csv.DictReader(open(os.path.join(SRC, fn))))
    S, G, E, T = (rd("fig_s2_c1_a_far_sites.csv"), rd("fig_s2_c1_b_sigma_far.csv"),
                  rd("fig_s2_c1_c_g1.csv"), rd("fig_s2_c1_d_throughput.csv"))
    HC = {"m30": "#2f6db5", "m05": "#d08a2e"}                  # host colours
    NEU, FAIL, INK = "#9aa3ad", "#c4553a", "#3a3a3a"
    g1fail = {r["dopant"] for r in G if r["G1_pass"] == "False"}

    fig = plt.figure(figsize=(183 / 25.4, 122 / 25.4))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.15, 1], left=0.075, right=0.985, bottom=0.085, top=0.94,
                          hspace=0.55, wspace=0.55)
    a = fig.add_subplot(gs[0, :]); b = fig.add_subplot(gs[1, 0]); c = fig.add_subplot(gs[1, 1])
    d = fig.add_subplot(gs[1, 2])

    # (a) raw far-site E_b,p(f) per dopant and pilot host; host mean E_p as a bar; gate N reads the spread
    off = {"m30": -0.19, "m05": +0.19}
    for i, dop in enumerate(DOPANTS):
        for h in HOSTS:
            rows = [r for r in S if r["dopant"] == dop and r["host"] == h]
            v = np.array([float(r["Eb_far_meV"]) for r in rows])
            x = i + off[h] + np.linspace(-0.075, 0.075, v.size)     # deterministic spread by site index
            mk = dict(marker="o", s=15, color=HC[h], edgecolor="white", linewidth=0.4) if h == "m30" else \
                dict(marker="s", s=14, facecolor="white", edgecolor=HC[h], linewidth=0.9)
            a.scatter(x, v, zorder=3, **mk)
            m = float(rows[0]["host_mean_meV"])
            a.plot([i + off[h] - 0.13, i + off[h] + 0.13], [m, m], color=HC[h], lw=1.4, zorder=2,
                   solid_capstyle="butt")
        r = next(r for r in G if r["dopant"] == dop)
        a.text(i, 66, f"σ = {float(r['sigma_far_meV']):.1f} meV (df {r['df']})", ha="center", va="bottom",
               fontsize=6, color=INK)
        if dop in g1fail:
            a.text(i, 58.5, "fails G1: no class", ha="center", va="bottom", fontsize=6, color=FAIL)
    a.axhline(0, color=INK, lw=0.6, zorder=1)
    a.set_xlim(-0.55, len(DOPANTS) - 0.45); a.set_ylim(-45, 75)
    a.set_xticks(range(len(DOPANTS)), ["Sr (control)", "Ca", "Cl", "Cs", "GA"])
    a.set_ylabel("Far-site E$_b$ of V$_I^+$ (meV)", fontsize=7.2)   # scripts 0.7 x 7.2 = 5.04 pt
    from matplotlib.legend_handler import HandlerTuple
    hd = [(a.scatter([], [], marker="o", s=15, color=HC["m30"]), a.plot([], [], color=HC["m30"], lw=1.4)[0]),
          (a.scatter([], [], marker="s", s=14, facecolor="white", edgecolor=HC["m05"], linewidth=0.9),
           a.plot([], [], color=HC["m05"], lw=1.4)[0])]
    a.legend(hd, ["Host m30: sites, mean (bar)", "Host m05: sites, mean (bar)"], loc="lower left", fontsize=6,
             ncol=2, handler_map={tuple: HandlerTuple(ndivide=None, pad=0.6)}, handlelength=2.6,
             handletextpad=0.4, columnspacing=1.4, borderaxespad=0.2)
    a.set_title("Noise pilot: raw binding energy at the 4 farthest sites of each sublattice, two pilot hosts",
                fontsize=7, pad=4)

    # (b) pooled far-site SD against gate N (25 meV) and the n rule (20 meV)
    for i, r in enumerate(G):
        s = float(r["sigma_far_meV"])
        counted = r["counts_for_n"] == "True"
        col = INK if counted else NEU
        b.plot([i, i], [0, s], color=col, lw=1.2, zorder=2)
        b.scatter(i, s, s=22, zorder=3, **(dict(facecolor="white", edgecolor=NEU, linewidth=0.9)
                                           if r["dopant"] in g1fail else dict(color=col, edgecolor="white", linewidth=0.4)))
    for yv, lab in ((GATE_N_MEV, "Gate N: σ ≤ 25 meV"), (NRULE_MEV, "n = 10 if a counted σ > 20 meV")):
        b.axhline(yv, color=INK, lw=0.6, ls=(0, (3, 2)), zorder=1)
        b.text(len(G) - 0.5, yv + 0.6, lab, ha="right", va="bottom", fontsize=6, color=INK)
    b.set_xlim(-0.6, len(G) - 0.4); b.set_ylim(0, 30)
    b.set_xticks(range(len(G)), [r["dopant"] for r in G])
    b.set_ylabel("Pooled far-site SD σ$_{far,d}$ (meV)", fontsize=7.2)
    b.set_title("Gate N and the n rule", fontsize=7, pad=4)
    b.text(0.02, 0.99, "dark: counted for n; grey: Sr (control);\nopen: Ca (fails G1)", transform=b.transAxes,
           fontsize=6, color=NEU, va="top")

    # (c) elements gate G1: |Delta| on a log axis, signed value printed; one bound per criterion
    crit = [("delta_cut_meV", "Cutoff\n60 vs 50 Ry", G1_CUT_MEV), ("dF_spin_meV", "Spin\nnspin 2 vs 1", G1_SPIN_MEV)]
    shape = {"Cl": "o", "Ca": "D"}
    for k, (key, lab, bound) in enumerate(crit):
        c.plot([k - 0.32, k + 0.32], [bound, bound], color=INK, lw=0.8, ls=(0, (3, 2)), zorder=1)
        c.text(k + 0.38, bound, f"≤ {bound:.0f}", ha="left", va="center", fontsize=6, color=INK)
        for j, r in enumerate(E):
            v = float(r[key]); x = k + (-0.12 if j == 0 else 0.12)
            assert v != 0.0                                     # log axis: |v| > 0
            inside = abs(v) <= bound
            col = INK if inside else FAIL
            c.scatter(x, abs(v), s=22 if r["element"] == "Cl" else 18, marker=shape[r["element"]], zorder=3,
                      **(dict(color=col, edgecolor="white", linewidth=0.4) if inside else
                         dict(facecolor="white", edgecolor=col, linewidth=1.0)))
            c.annotate(f"{v:+.1f}".replace("-", "\u2212"), (x, abs(v)), xytext=(-3 if j == 0 else 3, -5),
                       textcoords="offset points", ha="right" if j == 0 else "left", va="top", fontsize=6,
                       color=col)
    c.set_yscale("log"); c.set_ylim(0.5, 200); c.set_xlim(-0.5, 1.75)
    c.yaxis.set_major_locator(mpl.ticker.FixedLocator([1, 10, 100]))       # plain labels: no 4.9-pt exponents
    c.yaxis.set_major_formatter(mpl.ticker.FixedFormatter(["1", "10", "100"]))
    c.yaxis.set_minor_formatter(mpl.ticker.NullFormatter())
    c.set_xticks([0, 1], [lab for _, lab, _ in crit])
    c.set_ylabel("|Δ| (meV, log scale)")
    for el in ("Cl", "Ca"):
        c.scatter([], [], s=16, marker=shape[el], color=INK, label=el + (" (fails G1)" if el in g1fail else " (passes)"))
    c.scatter([], [], s=16, marker="o", facecolor="white", edgecolor=FAIL, linewidth=1.0, label="outside bound")
    c.legend(loc="upper right", fontsize=6, handletextpad=0.2, borderaxespad=0.2)
    c.text(0.03, 0.03, "|M| ≤ 0.01 μB; valence matches (both)", transform=c.transAxes, fontsize=6, color=NEU,
           va="bottom")
    c.set_title("Elements gate G1", fontsize=7, pad=4)

    # (d) A2 layout: configurations per node-hour on the 232-atom reference cell (5 configurations each)
    order = ["48", "64", "2x32"]
    rate = {r["layout"]: float(r["rate_config_per_node_h"]) for r in T}
    for i, k in enumerate(order):
        d.bar(i, rate[k], width=0.6, color=INK if k == "64" else NEU, zorder=2)
        d.text(i, rate[k] + 0.25, f"{rate[k]:.2f}", ha="center", va="bottom", fontsize=6, color=INK)
    thr = TP_FACTOR * rate["48"]
    d.axhline(thr, color=INK, lw=0.6, ls=(0, (3, 2)), zorder=3)
    d.text(-0.5, 17.4, f"dashed: 1.15 × rate(48) = {thr:.2f}", ha="left", va="top", fontsize=6, color=INK)
    d.set_xticks(range(3), ["48 ranks", "64 ranks", "2 × 32"]); d.set_xlim(-0.6, 2.6); d.set_ylim(0, 17.5)
    d.set_ylabel("Configurations per node-hour")
    d.set_title("A2 layout: highest rate above dashed", fontsize=7, pad=4)

    for lab, axx in (("a", a), ("b", b), ("c", c), ("d", d)):   # one figure-frame offset: shared anchors align
        p = axx.get_position()
        fig.text(p.x0 - 0.062, p.y1 + 0.045, lab, fontsize=8, fontweight="bold", va="top", ha="left")
    out = os.path.join(HERE, "fig_s2_c1_gates")
    fig.canvas.draw()
    if require_matplotlib_panel_alignment is not None:      # the three bottom panels are the comparable row
        require_matplotlib_panel_alignment(fig, json_out=out + ".alignment.json", overlay_svg=out + ".alignment.svg",
                                           tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True)
    fig.savefig(out + ".pdf", metadata={"CreationDate": None})          # no render date: reproducible outputs
    fig.savefig(out + ".svg", metadata={"Date": None}); fig.savefig(out + ".png", dpi=600)
    fig.savefig(out + ".tiff", dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    print("written", out + ".{pdf,svg,png,tiff}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--build", action="store_true"); a = ap.parse_args()
    if a.build:
        build()
    plot()

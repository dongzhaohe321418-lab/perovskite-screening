#!/usr/bin/env python
"""Figure WP3 / adoption (d) and (e): do the fine-tuned model's own minima and MD runs meet the rule?

Figure contract (written before plotting)
  Results-level question. Does the fine-tuned MACE-MP-0 of WP3 meet adoption conditions (d), DFT forces
    at its frozen-far-field minima, and (e), MD stability (PLAN amendment 2026-10-28m item 4)? Item 4
    requires both to be run and reported whatever (a)-(c) give; neither can change the outcome.
  Core conclusion. Neither is met. (d): in all six cells the free-atom residual DFT force RMS lies just
    above its 0.05 eV/A bound (the max is well inside its bound), although it is 2.5-3.0 times lower than at
    the zero-shot minimum. (e): 10 of 12 runs pass; each of the two undoped 450 K runs has one failing
    frame of 51, in which (post hoc) one formamidinium C-H lies just past the 1.25 A cut-off of the
    bonding-pattern test.
  What would overturn it. (d): free-atom RMS < 0.05 and max < 0.2 eV/A in all six cells. (e): all 612
    frames passing.
  Evidence chain (one role per panel).
    a  Decisive for (d). Free-atom residual DFT force, RMS against max (per-atom norms), for the six
       frozen-far-field minima and, as the comparator item 4 discloses, the DFT force at the zero-shot
       minimum (image 0) of the same cell; the pass region (both below their bounds) shaded.
    b  Decisive for (d), magnified. The free-atom RMS per cell against the bound, with the reported
       whole-cell RMS of the unconstrained minima (criterion 5 as pre-registered, reported only) beside it.
    c  Reported for (d). Relaxation energy, relaxed - image 0: model dE against DFT dF (raw F, as item 4
       specifies) for the 12 model minima, and the two-geometry difference E(DFT minimum) - E(image 0) of the WP2e cell for both
       models (the WP2e-minimum quantity item 4 asks for).
    d  Decisive for (e). Every checked frame of the 12 runs (51 per run, every 100 fs), with the failing
       frames marked.
    e  Post hoc diagnostic for (e), reported only. Distribution of the C-H distances over the frames
       t > 0 at 300 and 450 K (scripts/43), with the 1.25 A cut-off and the two crossings.
  Encoding. Colour = model (zero-shot warm grey, fine-tuned teal, as fig_wp3_criterion6); shape = dopant
    (triangle undoped, circle GA, square Sr); fill, for the fine-tuned relaxations only = relaxation
    (filled frozen far field, open unconstrained); the zero-shot points of a are DFT forces at image 0,
    the zero-shot whole-cell minimum; diamond = the WP2e DFT minimum (m30 GA image 0), evaluated with each
    model; a vermilion cross = failing frame; in e, 300 K is a lighter tint and dashed, 450 K solid.
  Archetype. Quantitative grid, 2 x 3, with a wide timeline (d spans two columns).
  Backend. Python / matplotlib only.
  Export. 183 mm double column; every PDF glyph >= 5 pt; editable text (pdf.fonttype 42, svg.fonttype
    none); pdf, svg, png and tiff (600 dpi); source data source_data/fig_wp3_adoption_de_*.csv; QA: render-
    time alignment gate (1.5 pt, strict, panel labels required), validate_figure.py, audit_pdf_text.py
    (5 pt) and audit_figure_collisions.py on the exported PDF.

Statistics. Every point is one deterministic quantity (a relaxation, a single point or an MD frame); there
are no replicates, error bars or tests. Every cell, run and frame is drawn; n is stated per panel.

Data. Every plotted and printed number is read at plot time from ../wp3/wp3b_result.json,
../wp3/wp3md_result.json, ../wp3/step7/md_bond_diagnostic.json and the archived MD work directory
../wp3/step7/wp3md_work.tar.gz (per-frame records and trajectories; each trajectory checked against its
record's sha256). The bounds of (d) come from wp3b_result.json "thresholds"; the 1.25 A cut-off from
scripts/43 (H_CUT), asserted equal to md_bond_diagnostic.json "cutoffs_A". The e histogram is recomputed
from the trajectories with scripts/43's bonds() and asserted to reproduce the pooled statistics in
md_bond_diagnostic.json. Nothing is typed in.

Backend. plot() selects Agg and measures the text-fit checks at the export resolution (600 dpi), so the
layout does not depend on a display backend.

QA notes. validate_figure.py gives WARN LOG-GUARD for the log axis of e: empty bins are set to NaN before
plotting (np.where), so no zero reaches the log scale. The tick labels of that axis are plain numbers, not
mathtext powers, whose exponents fell below 5 pt in audit_pdf_text.py. The run labels of d set the left
margin (16 mm here, 13 mm in fig_wp3_criterion6). The shaded pass regions start at the axis limits, so
that the collision audit sees no fill beyond the plot area.

    python fig_wp3_adoption_de.py

Review record (2026-11-03; one adversarial round, figure and science lens with an independent verifier;
the source data were reproduced byte for byte and every panel mapping was confirmed)
  1  Fill encoding read as global, but the zero-shot points of a and the diamonds of c are filled. Accepted
     in part: the key now scopes fill to the fine-tuned relaxations ("fine-tuned, frozen far field" /
     "fine-tuned, unconstrained") and the diamond entry reads "(each model)".
  2  Relaxation energies compared on raw F without saying so. Accepted: c's x label reads "DFT dF, raw";
     the E' values are given in WP3_RESULT.md section 5.
  3  Isolated bins of e could not be assigned a temperature by line style alone. Accepted: 300 K is now a
     lighter tint as well as dashed.
  4  The text-fit assertion failed headless (measured at 100 dpi under Agg). Accepted: plot() selects Agg and
     measures at 600 dpi; the key now has two rows (top margin 21 mm).
  5  No panel map in the result and panel letters that collide with condition letters. Accepted: the map is
     in WP3_RESULT.md section 10, with that warning.
"""
import csv, hashlib, importlib.util, io, json, math, os, sys, tarfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WP3 = os.path.join(HERE, "..", "wp3")
REPO = os.path.join(HERE, "..", "..", "..", "..")
SRC = os.path.join(HERE, "source_data")
NAME = "fig_wp3_adoption_de"
ZS_C, FT_C, FAIL_C = "#a48e72", "#0e7a72", "#c0392b"
FT_LIGHT = "#7fbfb8"                     # e: 300 K, a lighter tint of the fine-tuned teal
INK, SOFT, PASS_FILL = "#1a1a1a", "#555555", "#e3f0ed"
MRK = {"undoped": "^", "GA": "o", "Sr": "s"}
SYSTEMS, HOSTS, TEMPS = ("undoped", "GA", "Sr"), ("m30", "m32"), (300, 450)
MINUS = "−"
FIG_WIDTH_MM = 183
L_MM, R_MM, G_MM = 16.0, 3.0, 17.0      # left / right margin (d's run labels), column gutter
T_MM, V_MM, B_MM = 21.0, 19.0, 15.0     # top margin (two-row key), row gap, bottom margin
LAB_DX, LAB_DY = 30.0, 13.0             # panel letter: fixed point offset from the plot-area corner
BIN_A = 0.01                            # e: histogram bin width (A)


def fmt(x, nd=1, signed=False):
    s = f"{x:+.{nd}f}" if signed else f"{x:.{nd}f}"
    return s.replace("-", MINUS)


def write_csv(fn, rows):
    with open(os.path.join(SRC, fn), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def load_s43():
    sp = importlib.util.spec_from_file_location("s43", os.path.join(REPO, "scripts", "43_wp3_md_bond_diagnostic.py"))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def collect():
    """Read and cross-check everything the figure shows; write the source-data CSVs."""
    from ase.io import read
    rb = json.load(open(os.path.join(WP3, "wp3b_result.json")))
    rm = json.load(open(os.path.join(WP3, "wp3md_result.json")))
    dg = json.load(open(os.path.join(WP3, "step7", "md_bond_diagnostic.json")))
    s43 = load_s43()
    th = rb["thresholds"]
    RMS_B, MAX_B = th["free_rms_eVA"], th["free_max_eVA"]
    assert dg["cutoffs_A"]["C-H, N-H, H-(C or N)"] == s43.H_CUT
    out = {"RMS_B": RMS_B, "MAX_B": MAX_B, "H_CUT": s43.H_CUT, "verdict_d": rb["verdict"], "verdict_e": rm["verdict"]}

    # ---- (a, b) the six frozen-far-field cells and the six unconstrained ones -----------------------
    cells = []
    for h in HOSTS:
        for s in SYSTEMS:
            c, u = rb["cells"][f"wp3b_{h}_{s}_img0"], rb["unconstrained"][f"wp3bu_{h}_{s}_img0"]
            fr, z = c["free"], c["zero_shot_img0"]["free"]
            ok = fr["rms_eVA"] < RMS_B and fr["max_eVA"] < MAX_B
            assert c["free_pass"] == ok and (c["status"] == "fail") == (not ok or bool(c["cannot"]))
            assert c["converged"] and c["topology_ok"] and not c["cannot"]
            assert u["criterion5_whole_cell_pass"] == (u["whole_cell"]["rms_eVA"] < RMS_B and u["whole_cell"]["max_eVA"] < MAX_B)
            cells.append({"host": h, "system": s, "label": c["label"], "status": c["status"],
                          "free_rms_eVA": fr["rms_eVA"], "free_max_eVA": fr["max_eVA"], "n_free": fr["n"],
                          "zeroshot_img0_free_rms_eVA": z["rms_eVA"], "zeroshot_img0_free_max_eVA": z["max_eVA"],
                          "unconstrained_label": u["label"], "unconstrained_whole_rms_eVA": u["whole_cell"]["rms_eVA"],
                          "unconstrained_whole_max_eVA": u["whole_cell"]["max_eVA"],
                          "unconstrained_criterion5_pass": u["criterion5_whole_cell_pass"],
                          "dE_relax_model_meV": c["dE_relax_model_meV"], "dE_relax_dft_meV": c["dE_relax_dft_meV"],
                          "unconstrained_dE_relax_model_meV": u["dE_relax_model_meV"],
                          "unconstrained_dE_relax_dft_meV": u["dE_relax_dft_meV"]})
    assert (rb["verdict"] == "fail") == any(c["status"] == "fail" for c in cells)
    write_csv(f"{NAME}_ab_cells.csv", cells)
    out["cells"] = cells

    # ---- (c) relaxation energies and the WP2e minimum -------------------------------------------------
    w = rb["wp2e_minimum"]
    assert w["zero_shot"]["reproduced"] and all(w["zero_shot"]["reproduced"].values()) and not w["missing"]
    erows = [{"kind": k, "label": c[lab], "system": c["system"], "dft_meV": c[dk], "model_meV": c[mk], "model": "finetuned"}
             for c in cells for k, lab, dk, mk in (("frozen far field", "label", "dE_relax_dft_meV", "dE_relax_model_meV"),
                                                   ("unconstrained", "unconstrained_label", "unconstrained_dE_relax_dft_meV",
                                                    "unconstrained_dE_relax_model_meV"))]
    for model, src in (("finetuned", w), ("zeroshot", w["zero_shot"])):
        erows.append({"kind": "WP2e DFT minimum", "label": "m30_GA_img0 (WP2e)", "system": "GA",
                      "dft_meV": w["dft_F_min_minus_img0_meV"], "model_meV": src["dE_dftmin_minus_img0_meV"], "model": model})
    write_csv(f"{NAME}_c_energies.csv", erows)
    out["energies"] = erows

    # ---- (d, e) MD: per-frame records and trajectories from the archived work directory ----------------
    tb = open(os.path.join(WP3, "step7", "wp3md_work.tar.gz"), "rb").read()
    assert hashlib.sha256(tb).hexdigest() == dg["input"]["tar_sha256"]
    files = {}
    with tarfile.open(fileobj=io.BytesIO(tb), mode="r:gz") as tf:
        for m in tf.getmembers():
            if m.isfile():
                files[os.path.basename(m.name)] = tf.extractfile(m).read()
    runs = {r["label"]: r for r in rm["runs"]}
    diag = {r["label"]: r for r in dg["runs"]}
    frows, ch = [], {T: [] for T in TEMPS}
    order = [f"wp3md_{h}_{s}_md{T}" for T in TEMPS for h in HOSTS for s in SYSTEMS]
    assert sorted(order) == sorted(runs) and len(order) == rm["n_runs_expected"]
    for lab in order:
        rec = json.loads(files[lab + ".json"]); r = runs[lab]
        traj = files[rec["trajectory"]]
        assert hashlib.sha256(traj).hexdigest() == rec["trajectory_sha256"] == r["trajectory_sha256"]
        assert rec["ok"] == r["pass"] and rec["first_failure_fs"] == r["first_failure_fs"]
        bad = [f["t_fs"] for f in rec["frames"] if not f["ok"]]
        assert len(bad) == r["n_failing_frames"] and (not bad or bad[0] == r["first_failure_fs"])
        assert bad == [f["t_fs"] for f in diag[lab]["topology_failing_frames"]]     # every failing frame is a topology fail
        for f in rec["frames"]:
            frows.append({"run": lab, "host": r["host"], "system": r["system"], "T_K": r["T_K"], "t_fs": f["t_fs"],
                          "frame_ok": f["ok"], "topology_ok": f["topology_ok"], "min_II_A": f["min_II_A"]})
        for at in read(io.StringIO(traj.decode()), index="1:", format="extxyz"):     # frames t > 0
            ch[r["T_K"]] += list(s43.bonds(at)[0])
    write_csv(f"{NAME}_d_frames.csv", frows)
    for T in TEMPS:      # the recomputed distribution must be the diagnostic's
        st, x = dg["pooled_by_T"][str(T)]["CH"], np.array(ch[T])
        assert x.size == st["n"] and abs(x.mean() - st["mean_A"]) < 1e-12 and abs(x.max() - st["max_A"]) < 1e-12
        assert int((x >= s43.H_CUT).sum()) == st["n_at_or_above_1.25"]
    lo = math.floor(min(min(v) for v in ch.values()) / BIN_A) * BIN_A
    hi = math.ceil(max(max(v) for v in ch.values()) / BIN_A) * BIN_A + 1e-9
    edges = np.round(np.arange(lo, hi + BIN_A, BIN_A), 6)
    hist = {T: np.histogram(ch[T], bins=edges)[0] for T in TEMPS}
    write_csv(f"{NAME}_e_CH_hist.csv", [{"bin_lo_A": edges[i], "bin_hi_A": edges[i + 1],
                                          **{f"count_{T}K": int(hist[T][i]) for T in TEMPS}} for i in range(len(edges) - 1)])
    cross = [(diag[l]["T_K"], f["offending"]) for l in order for f in diag[l]["topology_failing_frames"]]
    crossings = []
    for T, off in cross:
        d = [v for o in off if o["atom"].startswith("H") for v in o["nearest_C_or_N_A"].values()]
        crossings.append((T, min(d)))
    out.update({"order": order, "runs": runs, "frames": frows, "ch": ch, "edges": edges, "hist": hist,
                "crossings": crossings, "pooled": dg["pooled_by_T"], "min_II": rm["reported_not_gating"]["min_II_A"],
                "II_bound": rm["params"]["II_min_A"], "n_pass": rm["n_pass"], "n_fail": rm["n_fail"]})
    return out


def plot(D):
    import matplotlib as mpl
    mpl.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle
    from matplotlib.transforms import ScaledTranslation
    sys.path.insert(0, os.path.expanduser("~/.claude/skills/nature-figure/scripts"))
    try:      # layout QA from the nature-figure toolkit; optional, it does not touch the data
        from audit_panel_alignment import require_matplotlib_panel_alignment
    except ImportError:
        require_matplotlib_panel_alignment = None
        print("note: panel-alignment audit unavailable; figure rendered without it")
    mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                         "svg.fonttype": "none", "pdf.fonttype": 42, "font.size": 7.5,
                         "axes.labelsize": 7.5, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
                         "axes.spines.right": False, "axes.spines.top": False, "axes.linewidth": 0.8,
                         "legend.frameon": False, "xtick.major.width": 0.8, "ytick.major.width": 0.8,
                         "xtick.major.size": 2.5, "ytick.major.size": 2.5})
    W_MM = (FIG_WIDTH_MM - L_MM - R_MM - 2 * G_MM) / 3
    W_PT = W_MM / 25.4 * 72
    FIG_H_MM = T_MM + 2 * W_MM + V_MM + B_MM
    fig = plt.figure(figsize=(FIG_WIDTH_MM / 25.4, FIG_H_MM / 25.4))
    gs = fig.add_gridspec(2, 3, left=L_MM / FIG_WIDTH_MM, right=1 - R_MM / FIG_WIDTH_MM, bottom=B_MM / FIG_H_MM,
                          top=1 - T_MM / FIG_H_MM, wspace=G_MM / W_MM, hspace=V_MM / W_MM)
    a = fig.add_subplot(gs[0, 0]); b = fig.add_subplot(gs[0, 1]); c = fig.add_subplot(gs[0, 2])
    d = fig.add_subplot(gs[1, 0:2]); e = fig.add_subplot(gs[1, 2])
    fits = []
    LIM_GUTTER = 1.0 + (G_MM / 25.4 * 72 - LAB_DX - 3) / W_PT

    def heading(ax, title, sub, limit=LIM_GUTTER):
        s = ax.annotate(sub, (0, 1), xycoords="axes fraction", xytext=(0, 3), textcoords="offset points",
                        fontsize=6.3, color=SOFT, ha="left", va="bottom")
        t = ax.annotate(title, (0, 1), xycoords="axes fraction", xytext=(0, 12), textcoords="offset points",
                        fontsize=7.5, color=INK, ha="left", va="bottom")
        fits.extend([(s, ax, limit), (t, ax, limit)])

    def pt(ax, x, y, col, mk, filled=True, s=22, z=3, dx_pt=0.0):
        tr = ax.transData + ScaledTranslation(dx_pt / 72, 0, fig.dpi_scale_trans)
        ax.scatter(x, y, s=s, marker=mk, facecolor=col if filled else "white", edgecolor=col, linewidth=0.9,
                   zorder=z, transform=tr)

    RMS_B, MAX_B, cells = D["RMS_B"], D["MAX_B"], D["cells"]

    # ---------------- (a) free-atom residual, RMS against max -----------------------------------------
    A_X0 = 0.03
    a.add_patch(Rectangle((A_X0, 0), RMS_B - A_X0, MAX_B, facecolor=PASS_FILL, edgecolor="none", zorder=0))
    a.axvline(RMS_B, color=INK, lw=0.7, ls=(0, (3, 2)), zorder=1)
    a.axhline(MAX_B, color=INK, lw=0.7, ls=(0, (3, 2)), zorder=1)
    for cl in cells:
        a.annotate("", (cl["free_rms_eVA"], cl["free_max_eVA"]), (cl["zeroshot_img0_free_rms_eVA"], cl["zeroshot_img0_free_max_eVA"]),
                   arrowprops=dict(arrowstyle="-|>", color="#b8b8b8", lw=0.6, shrinkA=3.5, shrinkB=3.5, mutation_scale=5), zorder=2)
        pt(a, cl["zeroshot_img0_free_rms_eVA"], cl["zeroshot_img0_free_max_eVA"], ZS_C, MRK[cl["system"]])
        pt(a, cl["free_rms_eVA"], cl["free_max_eVA"], FT_C, MRK[cl["system"]])
    a.set_xlim(A_X0, 0.17); a.set_ylim(0, 0.42)
    a.set_xticks([0.05, 0.10, 0.15]); a.set_yticks([0, 0.1, 0.2, 0.3, 0.4])
    a.set_xlabel("Free-atom DFT force RMS (eV/Å)"); a.set_ylabel("Free-atom DFT force max (eV/Å)")
    a.text(0.031, 0.008, "pass", fontsize=6.3, color=FT_C, ha="left", va="bottom")
    ft_r = [c["free_rms_eVA"] for c in cells]; zs_r = [c["zeroshot_img0_free_rms_eVA"] for c in cells]
    heading(a, "(d) Frozen-far-field minima",
            f"n = {len(cells)} cells; zero-shot minimum → fine-tuned")
    a.text(0.97, 0.04, f"RMS {fmt(min(zs_r), 3)}–{fmt(max(zs_r), 3)}\n→ {fmt(min(ft_r), 3)}–{fmt(max(ft_r), 3)}",
           transform=a.transAxes, fontsize=6.3, color=SOFT, ha="right", va="bottom", linespacing=1.25)

    # ---------------- (b) the RMS against its bound, per cell ------------------------------------------
    xs = np.arange(len(cells))
    b.axhline(RMS_B, color=INK, lw=0.7, ls=(0, (3, 2)), zorder=1)
    B_Y0 = 0.045
    b.axhspan(B_Y0, RMS_B, color=PASS_FILL, zorder=0, lw=0)
    for x, cl in zip(xs, cells):
        pt(b, x, cl["free_rms_eVA"], FT_C, MRK[cl["system"]], True, dx_pt=-3.0)
        pt(b, x, cl["unconstrained_whole_rms_eVA"], FT_C, MRK[cl["system"]], False, dx_pt=3.0)
    b.set_xlim(-0.6, len(cells) - 0.4); b.set_ylim(B_Y0, 0.065)
    b.set_yticks([0.045, 0.05, 0.055, 0.06, 0.065])
    b.set_yticklabels([fmt(v, 3) for v in (0.045, 0.05, 0.055, 0.06, 0.065)])
    b.set_xticks(xs); b.set_xticklabels([{"undoped": "undop.", "GA": "GA", "Sr": "Sr"}[c["system"]] for c in cells])
    b.tick_params(axis="x", length=0)
    for i, h in enumerate(HOSTS):
        b.annotate(h, (3 * i + 1, 0), xycoords=("data", "axes fraction"),
                   xytext=(0, -17), textcoords="offset points", fontsize=6.5, ha="center", va="top")
    b.set_ylabel("Residual DFT force RMS (eV/Å)")
    b.text(len(cells) - 0.45, RMS_B - 0.0004, f"bound {fmt(RMS_B, 2)}", fontsize=6.3, color=INK, ha="right", va="top")
    exc = [100 * (c["free_rms_eVA"] / RMS_B - 1) for c in cells]
    heading(b, "(d) Residual RMS per cell", f"free atoms: {len(cells)} of {len(cells)} above, by {min(exc):.0f}–{max(exc):.0f}%")
    b.text(0.03, 0.97, "filled: free atoms (decisive)\nopen: whole cell, unconstrained\n(criterion 5, reported)",
           transform=b.transAxes, fontsize=6.3, color=SOFT, ha="left", va="top", linespacing=1.25)

    # ---------------- (c) relaxation energies, model against DFT -----------------------------------------
    E = D["energies"]
    lim = (-1450, 350)
    c.plot(lim, lim, color="#9a9a9a", lw=0.7, zorder=1)
    for r in E:
        if r["kind"] == "WP2e DFT minimum":
            pt(c, r["dft_meV"], r["model_meV"], FT_C if r["model"] == "finetuned" else ZS_C, "D", True, s=20, z=4)
        else:
            pt(c, r["dft_meV"], r["model_meV"], FT_C, MRK[r["system"]], r["kind"] == "frozen far field")
    c.set_xlim(*lim); c.set_ylim(*lim)
    tk = [-1200, -800, -400, 0]
    c.set_xticks(tk); c.set_yticks(tk)
    c.set_xticklabels([fmt(v, 0) for v in tk]); c.set_yticklabels([fmt(v, 0) for v in tk])
    c.set_xlabel("DFT ΔF, raw (meV)"); c.set_ylabel("Model ΔE (meV)")
    wz = next(r for r in E if r["kind"] == "WP2e DFT minimum" and r["model"] == "zeroshot")
    wf = next(r for r in E if r["kind"] == "WP2e DFT minimum" and r["model"] == "finetuned")
    c.annotate(f"WP2e: zero-shot {fmt(wz['model_meV'], 0, True)}", (wz["dft_meV"], wz["model_meV"]), xytext=(6, -1),
               textcoords="offset points", fontsize=6.3, color=SOFT, ha="left", va="center")
    c.annotate(f"fine-tuned {fmt(wf['model_meV'], 0)}", (wf["dft_meV"], wf["model_meV"]), xytext=(-1420, -520),
               textcoords="data", fontsize=6.3, color=SOFT, ha="left", va="center",
               arrowprops=dict(arrowstyle="-", color="#b8b8b8", lw=0.6, shrinkA=1, shrinkB=4))
    c.text(0.97, 0.03, "y = x", transform=c.transAxes, fontsize=6.3, color="#9a9a9a", ha="right", va="bottom")
    fe = [r for r in E if r["kind"] != "WP2e DFT minimum"]
    over = [r["model_meV"] - r["dft_meV"] for r in fe]
    assert all(o < 0 for o in over)
    heading(c, "(d) Relaxation energy, reported",
            f"{len(fe)} minima: model below DFT by {fmt(-max(over), 0)}–{fmt(-min(over), 0)} meV")

    # ---------------- (d) every MD frame -----------------------------------------------------------------
    order, runs, frames = D["order"], D["runs"], D["frames"]
    ypos = {lab: len(order) - 1 - i + (0.0 if runs[lab]["T_K"] == TEMPS[1] else 0.8) for i, lab in enumerate(order)}
    for lab in order:
        y = ypos[lab]
        t = np.array([f["t_fs"] for f in frames if f["run"] == lab])
        ok = np.array([f["frame_ok"] for f in frames if f["run"] == lab])
        d.plot([0, t.max()], [y, y], color="#d0d0d0", lw=0.6, zorder=1)
        d.scatter(t[ok], np.full(ok.sum(), y), s=7, marker="|", color=FT_C, linewidths=0.6, zorder=2)
        if (~ok).any():
            d.scatter(t[~ok], np.full((~ok).sum(), y), s=26, marker="x", color=FAIL_C, linewidths=1.1, zorder=3)
    d.set_yticks([ypos[l] for l in order])
    d.set_yticklabels([f"{runs[l]['host']} {runs[l]['system']}" for l in order], fontsize=6.3)
    for tl, l in zip(d.get_yticklabels(), order):      # failing runs: label in the failure colour
        if not runs[l]["pass"]:
            tl.set_color(FAIL_C)
    d.set_ylim(-0.7, max(ypos.values()) + 0.7)
    d.set_xlim(-60, 5060); d.set_xticks(range(0, 5001, 1000))
    d.set_xlabel("MD time (fs)")
    d.tick_params(axis="y", length=0)
    for T in TEMPS:
        ys = [ypos[l] for l in order if runs[l]["T_K"] == T]
        d.annotate(f"{T} K", (1.0, (np.mean(ys) - d.get_ylim()[0]) / (d.get_ylim()[1] - d.get_ylim()[0])), xycoords="axes fraction",
                   xytext=(4, 0), textcoords="offset points", fontsize=6.5, ha="left", va="center", rotation=90,
                   rotation_mode="anchor")
    n_fr = len(frames)
    heading(d, "(e) MD stability: every checked frame",
            f"{len(order)} runs × {n_fr // len(order)} frames; {D['n_pass']} pass, {D['n_fail']} fail (at "
            f"{' and '.join(str(int(f['t_fs'])) for f in frames if not f['frame_ok'])} fs); "
            f"inorganic checks pass (min I–I {fmt(D['min_II'], 2)} Å ≥ {fmt(D['II_bound'], 1)} Å)",
            limit=1.0 + (G_MM / 25.4 * 72 - LAB_DX - 3) / (2 * W_PT + G_MM / 25.4 * 72))

    # ---------------- (e) C-H distribution, post hoc -------------------------------------------------------
    edges, hist = D["edges"], D["hist"]
    for T, ls, col in zip(TEMPS, ("--", "-"), (FT_LIGHT, FT_C)):
        e.stairs(np.where(hist[T] > 0, hist[T], np.nan), edges, color=col, lw=0.9, ls=ls, zorder=2 + (col == FT_C),
                 baseline=None)
    e.set_yscale("log")
    from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter
    e.yaxis.set_major_locator(FixedLocator([1, 10, 100, 1000]))
    e.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))     # plain numbers: no mathtext exponents below 5 pt
    e.yaxis.set_minor_formatter(NullFormatter())
    e.axvline(D["H_CUT"], color=INK, lw=0.7, ls=(0, (3, 2)), zorder=1)
    for T, x in D["crossings"]:
        e.scatter([x], [1.0], s=16, marker="x", color=FAIL_C, linewidths=0.9, zorder=3, clip_on=False)
    e.set_xlim(0.92, 1.30); e.set_ylim(0.6, 3000)
    e.set_xticks([1.0, 1.1, 1.2, 1.3]); e.set_xticklabels([fmt(v, 1) for v in (1.0, 1.1, 1.2, 1.3)])
    e.set_xlabel("C–H distance (Å)"); e.set_ylabel(f"Count per {fmt(BIN_A, 2)} Å bin")
    e.text(D["H_CUT"] - 0.004, 1500, f"cut-off {fmt(D['H_CUT'], 2)}", fontsize=6.3, color=INK, ha="right", va="top")
    p = D["pooled"]
    n450 = p[str(TEMPS[1])]["CH"]
    assert p[str(TEMPS[0])]["CH"]["n_at_or_above_1.25"] == 0 and p[str(TEMPS[0])]["CH"]["n"] == n450["n"]
    e.legend(handles=[Line2D([], [], color=FT_LIGHT, ls="--", lw=0.9, label=f"{TEMPS[0]} K"),
                      Line2D([], [], color=FT_C, ls="-", lw=0.9, label=f"{TEMPS[1]} K")],
             loc="upper left", fontsize=6.3, handlelength=1.8, borderaxespad=0.2)
    heading(e, "(e) C–H distances, post hoc",
            f"n = {n450['n']} per T; {n450['n_at_or_above_1.25']} at ≥ {fmt(D['H_CUT'], 2)} Å, all at {TEMPS[1]} K")

    # ---------------- shared key ------------------------------------------------------------------------------
    sq = dict(ls="none", markersize=4.6, markeredgewidth=0.9)
    key = [Line2D([], [], marker="o", color=ZS_C, mfc=ZS_C, label="Zero-shot MACE-MP-0", **sq),
           Line2D([], [], marker="o", color=FT_C, mfc=FT_C, label="Fine-tuned", **sq),
           Line2D([], [], marker="^", color=INK, mfc="white", label="undoped", **sq),
           Line2D([], [], marker="o", color=INK, mfc="white", label="GA", **sq),
           Line2D([], [], marker="s", color=INK, mfc="white", label="Sr", **sq),
           Line2D([], [], marker="s", color=FT_C, mfc=FT_C, label="fine-tuned, frozen far field", **sq),
           Line2D([], [], marker="s", color=FT_C, mfc="white", label="fine-tuned, unconstrained", **sq),
           Line2D([], [], marker="D", color=INK, mfc=INK, label="WP2e DFT min. (each model)", ls="none", markersize=3.8),
           Line2D([], [], marker="x", color=FAIL_C, label="failing frame", ls="none", markersize=4.6, markeredgewidth=1.1)]
    leg = fig.legend(handles=key, loc="upper center", bbox_to_anchor=(0.5, 1 - 0.6 / FIG_H_MM), ncol=5,
                     fontsize=6.3, handletextpad=0.2, columnspacing=0.9, borderaxespad=0)
    for lab, ax in zip("abcde", (a, b, c, d, e)):
        t = ax.transAxes + ScaledTranslation(-LAB_DX / 72, LAB_DY / 72, fig.dpi_scale_trans)
        ax.text(0, 1, lab, transform=t, fontsize=8, fontweight="bold", ha="left", va="bottom")
    out = os.path.join(HERE, NAME)
    fig.set_dpi(600)                   # measure the text fits at the export resolution
    fig.canvas.draw()
    rnd = fig.canvas.get_renderer()
    for art, ax, lim in fits:
        x1 = ax.transAxes.inverted().transform(art.get_window_extent(rnd).get_points())[1, 0]
        assert x1 <= lim + 1e-3, (art.get_text(), x1, lim)
    lb = leg.get_window_extent(rnd)
    assert lb.x0 >= 0 and lb.x1 <= fig.bbox.width, (lb.x0, lb.x1, fig.bbox.width)
    if require_matplotlib_panel_alignment is not None:
        require_matplotlib_panel_alignment(fig, json_out=out + ".alignment.json", overlay_svg=out + ".alignment.svg",
                                           tolerance_pt=1.5, gutter_tolerance_pt=1.5, require_panel_labels=True,
                                           strict=True)
    fig.savefig(out + ".pdf"); fig.savefig(out + ".svg"); fig.savefig(out + ".png", dpi=600)
    fig.savefig(out + ".tiff", dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    print("written", out + ".{pdf,svg,png,tiff}")


if __name__ == "__main__":
    os.makedirs(SRC, exist_ok=True)
    plot(collect())

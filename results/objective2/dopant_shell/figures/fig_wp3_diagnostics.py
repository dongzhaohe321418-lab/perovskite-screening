#!/usr/bin/env python
"""Figure WP3 diagnostics D1 and D2 (post hoc, reported only): do the kept checkpoints or a path attribution
explain why the fine-tuned model fails on the dopant-vacancy energy differences?

Figure contract (written before plotting; revised after the adversarial check of 2026-11-03)
  Results-level question. WP3_RESULT.md section 8 leaves two candidate reasons untested: a checkpoint chosen
    on a force-dominated m21 loss (reason 6) and a systematic lowering of the absolute barriers of unknown
    origin (reason 7). WP3_DIAGNOSTICS_PLAN.md (d69fe75) pre-specifies D1 (Q1-Q3) and D2 (Q4) for them.
  Core conclusion. No kept checkpoint gets the m21 first-shell Sr E_b right (Q1: no). As planned, Q2's
    onset (first |error| > 25 meV) is Initial for the two flank sites (the zero-shot error, +25.9 and +36.1
    meV) and epoch 0 for the two hinge sites (a positive overshoot, +165.9 and +150.9 meV). The collapse
    (first error below -25 meV, an addition to the plan) has its onsets in the kept-epoch brackets (3, 4],
    (4, 6] and (8, 11], after 56-78% of the Initial -> epoch-82 fall of the m21 force RMSE (the fall runs from
    47% at epoch 3 to 78% at epoch 11); from kept epoch 11 on, no first-shell Sr error at m21 or m05 is back
    within 25 meV. The m21 loss and the
    m21 E_b RMS do not rank the checkpoints alike (Q3, rho = -0.12). The path attribution cannot be read
    (Q4): with image 1 missing from every 0 -> i* path, the DFT path-work closure exceeds the 20 meV rule in
    all 37 bands, and the error sits in the 0 -> 2 segment for the two conservative models as well as for DFT.
  What would overturn it. Q1: a kept checkpoint with both m21 first-shell Sr |E_b error| < 25 meV and right
    signs (the five-site rule cannot discriminate: m21 Sr_mid fails at every checkpoint). Q4: |DFT closure|
    <= 20 meV in a band.
  Evidence chain (one role per panel).
    a  Context for Q2. The logged m21 force RMSE of every epoch (Initial and epochs 0-99), the kept
       checkpoints marked; the kept-epoch brackets of the collapse onsets shaded (their union, (3, 6] and
       (8, 11]).
    b  Decisive for Q1 and Q2. Far-referenced E_b error (raw F energies) of the two first-shell Sr sites at
       m21 and m05 for Initial and the 20 kept checkpoints, with the +-25 meV band; the m21 Sr_mid site,
       which fails at every checkpoint (the Q1 caveat), in grey. Dotted lines only join the evaluated models
       (Initial and the kept checkpoints): the epochs between were not evaluated. The four first-shell series
       are offset horizontally by -3.6, -1.2, +1.2 and +3.6 pt so that coincident values stay visible; the
       values themselves are in the table of WP3_DIAGNOSTICS.md section 3 and in the bc CSV.
    c  Decisive for Q3. The m21 E_b RMS (5 sites) of the 20 checkpoints against their logged m21 loss, with
       Spearman rho, and the zero-shot (Initial) value.
    d  Decisive for Q4 (D2a). The path-work closure of the 37 bands per segment and to i* (each level's own
       argmax; the rule quantity is DFT's), for DFT, zero-shot and fine-tuned.
  Encoding. b: colour = host (m21 validation blue, m05 training orange; legend swatches); marker = site
    (filled circle hinge, open square flank); grey dashed with small dots = m21 Sr_mid. c: teal = fine-tuned checkpoints, warm grey diamond =
    zero-shot (Initial). d: colour = level (DFT ink, zero-shot warm grey, fine-tuned teal, as
    fig_wp3_criterion6); horizontal position within a cloud is a fixed golden-ratio jitter, not band order.
    Bound bands (+-25 meV, +-20 meV) are mid grey; the onset brackets of a and b are a lighter grey (vertical,
    so they do not read as a bound). a, b share the x axis: linear to epoch 10, logarithmic beyond (linscale 1:
    epochs 11-99 take about a third of the width); Initial sits left of epoch 0.
  Archetype. Quantitative grid, 2 x 3: a and b span two columns (a training timeline), c and d one.
  Backend. Python / matplotlib only.
  Export. 183 mm double column; every PDF glyph >= 5 pt; editable text (pdf.fonttype 42, svg.fonttype
    none); mathtext set in Arial, upright; pdf, svg, png and tiff (600 dpi); source data
    source_data/fig_wp3_diagnostics_*.csv; QA: render-time alignment gate (1.5 pt, strict, panel labels
    required), validate_figure.py, audit_pdf_text.py (5 pt) and audit_figure_collisions.py on the exported PDF.

Statistics. Every point is one deterministic quantity (a single point, an energy difference of single points,
or a logged eval record); there are no replicates, error bars or tests. rho in c is descriptive (20
non-independent checkpoints; plan). Every model and band is drawn; n is stated per panel.

Data. Every plotted and printed number is read at plot time from ../wp3/diagnostics/d1_checkpoints.json and
../wp3/diagnostics/d2_path_attribution.json (scripts/44). The 25 meV and 20 meV bounds are the plan's; c's
rho is recomputed here from the plotted values and asserted equal to the JSON's; the shaded bracket of a
and the literal Q2 onsets of b are taken from the Q2 onsets. Nothing is typed in.

Backend. plot() selects Agg and measures the text-fit checks at the export resolution (600 dpi).

QA notes. validate_figure.py gives WARN LOG-GUARD for the log x axis of c: every plotted loss is asserted
positive in collect(). The tick labels of that axis are plain numbers, not mathtext powers. Subscripts
(mathtext) are used only in 7.5 pt text; validate_figure.py's FONT-GLYPH-FLOOR WARN assumes a 6.3 pt
parent, but audit_pdf_text.py measures the smallest glyph in the PDF. The panel axes are created in label
order (a, b, c, d), so the ids of the alignment record are the panel letters.

Review record (2026-11-03; one adversarial round with four lenses: numbers, plan conformance, figure and
provenance). Accepted and applied: the "no recovery" wording (the m21 hinge returns to -19.4 meV at kept
epoch 7); "most of its fall" replaced by the fall fractions; the falsifier is the first-shell-only condition;
panel b joins kept checkpoints with dotted lines only; the shaded bracket is labelled an addition and the
literal Q2 onsets are stated; epochs 96-99 drawn (x to 105); linscale 1.3 instead of 1.6; neutral grey bound
bands; m05 orange instead of ochre (the ochre was close to the zero-shot warm grey); Arial upright mathtext; "force RMSE"
instead of RMSE_F (F is also the energy basis); c's heading reads E_b RMS against loss and the diamond sits
below the checkpoints; Initial no longer flagged kept in the source data; the GA sites added to the bc CSV;
d's jitter no longer encodes band order and its i* and rule are defined; axes created in label order.
Second round (two lenses, no error found): the onset fall fractions are 56-78% (47% is the bracket's open left
end); the flank onset is the zero-shot error, not an overshoot; the shading is the union of the onset brackets
and is a neutral grey; b states the first-shell-only Q1 result; the four series of b are offset; Sr_mid has
markers; the connector legend reads "joins evaluated models only"; host legend entries are swatches; linscale 1;
a's subtitle says the minima run from epoch 0; c names the lowest-RMS epoch by argmin; d's x label.
"""
import csv, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DG = os.path.join(HERE, "..", "wp3", "diagnostics")
SRC = os.path.join(HERE, "source_data")
NAME = "fig_wp3_diagnostics"
ZS_C, FT_C, INK, SOFT = "#a48e72", "#0e7a72", "#1a1a1a", "#555555"
HOST_C = {"m21": "#2b5c8a", "m05": "#d9771e"}
MID_C, BAND_FILL, BAND_TXT, WIN_FILL = "#9a9a9a", "#e2e2e2", "#6a6a6a", "#f3f3f3"
SITES = ("Sr_hinge", "Sr_flank")
SITE_MK = {"Sr_hinge": "o", "Sr_flank": "s"}
HOSTS = ("m21", "m05")
EB_BOUND, CLOSURE_BOUND = 25.0, 20.0      # plan: Q1/Q2 and D2a
X_INIT = -2.5                             # a, b: x position of Initial (left of epoch 0)
X_MAX = 105.0                             # a, b: right limit, beyond the last logged epoch (99)
LINSCALE = 1.0                            # a, b: symlog, decades given to the linear part 0-10
B_SHADE_TOP = 0.78                        # b: top of the bracket shading (axes fraction), below the key
SERIES_DX = {("m21", "Sr_hinge"): -3.6, ("m21", "Sr_flank"): -1.2, ("m05", "Sr_hinge"): 1.2, ("m05", "Sr_flank"): 3.6}
MINUS = "−"
FIG_WIDTH_MM = 183
L_MM, R_MM, G_MM = 15.0, 3.0, 17.0       # left / right margin, column gutter
T_MM, V_MM, B_MM = 14.0, 23.0, 13.0      # top margin, row gap, bottom margin
H_TOP_MM, H_BOT_MM = 44.0, 58.0          # row heights
LAB_DX, LAB_DY = 30.0, 20.5              # panel letter: fixed point offset from the plot-area corner
SUB_LINE = 7.8                           # subtitle line pitch (pt)


def fmt(x, nd=1, signed=False):
    s = f"{x:+.{nd}f}" if signed else f"{x:.{nd}f}"
    return s.replace("-", MINUS)


def write_csv(fn, rows):
    with open(os.path.join(SRC, fn), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def spearman(x, y):
    """Spearman's rho with average ranks (as scripts/44)."""
    def ranks(v):
        v = np.asarray(v, float)
        o = np.argsort(v, kind="mergesort")
        r = np.empty(len(v))
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[o[j + 1]] == v[o[i]]:
                j += 1
            r[o[i:j + 1]] = 0.5 * (i + j) + 1
            i = j + 1
        return r
    return float(np.corrcoef(ranks(x), ranks(y))[0, 1])


def collect():
    """Read and cross-check everything the figure shows; write the source-data CSVs."""
    d1 = json.load(open(os.path.join(DG, "d1_checkpoints.json")))
    d2 = json.load(open(os.path.join(DG, "d2_path_attribution.json")))
    assert d1["script_sha256"] == d2["script_sha256"]
    models = list(d1["models"])
    assert models[0] == "Initial" and [int(m) for m in models[1:]] == sorted(int(m) for m in models[1:])
    epochs = [int(m) for m in models[1:]]

    # ---- (a) logged m21 force RMSE of every epoch -----------------------------------------------------------
    rf = d1["Q2"]["rmse_f_fall"]
    all_ep = sorted((int(k), v) for k, v in rf["logged_rmse_f_meV_A_all_epochs"].items())
    assert [e for e, _ in all_ep] == list(range(len(all_ep))) and all_ep[-1][0] < X_MAX
    for e in epochs:
        assert abs(rf["logged_rmse_f_meV_A_kept"][str(e)] - dict(all_ep)[e]) < 1e-9
        assert abs(d1["models"][str(e)]["logged_m21"]["rmse_f_eVA"] * 1000 - dict(all_ep)[e]) < 1e-9
    write_csv("fig_wp3_diagnostics_a_rmse_f.csv",
              [{"model": "Initial (zero-shot)", "epoch": "", "kept_checkpoint": False,
                "logged_m21_rmse_f_meV_A": rf["initial_meV_A"]}] +
              [{"model": str(e), "epoch": e, "kept_checkpoint": e in epochs, "logged_m21_rmse_f_meV_A": v}
               for e, v in all_ep])

    # ---- (b) first-shell Sr E_b errors; (c) loss against E_b RMS ---------------------------------------------
    eb, rows_b = {}, []
    for h in HOSTS:
        q = d1["Q2"]["hosts"][h]["sites"]
        for nm in SITES:
            err = q[nm]["errors_meV"]
            assert list(err) == models
            for m in models:
                site = d1["models"][m]["quantities"][h]["Eb_farref_raw"][q[nm]["site"]]
                assert site["name"] == nm and abs(site["error_meV"] - err[m]) < 1e-9
            eb[(h, nm)] = [err[m] for m in models]
    by_name = {m: {h: {v["name"]: v["error_meV"] for v in d1["models"][m]["quantities"][h]["Eb_farref_raw"].values()}
                   for h in HOSTS} for m in models}
    assert all(len(by_name[m][h]) == 5 for m in models for h in HOSTS)
    mid = {m: by_name[m]["m21"]["Sr_mid"] for m in models}
    caveat_sites = d1["Q1"]["sites_failing_at_every_checkpoint_not_first_shell_Sr"]
    assert len(caveat_sites) == 1 and "Sr_mid" in caveat_sites[0]
    assert all(abs(mid[m]) >= EB_BOUND for m in models[1:])
    for i, m in enumerate(models):
        q = d1["models"][m]
        rows_b.append({"model": m, "logged_m21_loss": q["logged_m21"]["loss"],
                       **{f"{h}_{nm}_Eb_error_meV": by_name[m][h][nm] for h in HOSTS
                          for nm in ("Sr_hinge", "Sr_flank", "Sr_mid", "GA_near", "GA_mid")},
                       "m21_Eb_rms_meV": q["quantities"]["m21"]["Eb_rms_raw_meV"],
                       "m05_Eb_rms_meV": q["quantities"]["m05"]["Eb_rms_raw_meV"]})
    write_csv("fig_wp3_diagnostics_bc_checkpoints.csv", rows_b)
    loss = [d1["Q3"]["loss"][str(e)] for e in epochs]
    rms = [d1["Q3"]["m21_Eb_rms_raw_meV"][str(e)] for e in epochs]
    for e, l, r in zip(epochs, loss, rms):
        assert abs(d1["models"][str(e)]["logged_m21"]["loss"] - l) < 1e-12
        assert abs(d1["models"][str(e)]["quantities"]["m21"]["Eb_rms_raw_meV"] - r) < 1e-9
    assert min(loss) > 0 and d1["models"]["Initial"]["logged_m21"]["loss"] > 0      # c: log x axis
    rho = spearman(loss, rms)
    assert abs(rho - d1["Q3"]["rho_loss_vs_m21_Eb_rms"]) < 1e-12, (rho, d1["Q3"]["rho_loss_vs_m21_Eb_rms"])
    on = {(h, nm): d1["Q2"]["hosts"][h]["sites"][nm]["onsets"] for h in HOSTS for nm in SITES}
    win = (min(o["negative"]["previous_model"] for o in on.values()), max(o["negative"]["model"] for o in on.values()))
    assert all(isinstance(v, int) for v in win)
    brackets = []                                                       # union of the onset brackets (a, b]
    for lo, hi in sorted({(o["negative"]["previous_model"], o["negative"]["model"]) for o in on.values()}):
        if brackets and lo <= brackets[-1][1]:
            brackets[-1] = (brackets[-1][0], max(hi, brackets[-1][1]))
        else:
            brackets.append((lo, hi))
    onset_ff = (min(o["negative"]["rmse_f_fall_fraction_range"][0] for o in on.values()),
                max(o["negative"]["rmse_f_fall_fraction_range"][1] for o in on.values()))
    fs = [max(abs(eb[("m21", "Sr_hinge")][i]), abs(eb[("m21", "Sr_flank")][i])) for i in range(1, len(models))]
    k = int(np.argmin(fs))
    first_shell_best = (epochs[k], fs[k], "flank" if abs(eb[("m21", "Sr_flank")][k + 1]) >= abs(eb[("m21", "Sr_hinge")][k + 1])
                        else "hinge", eb[("m21", "Sr_flank")][k + 1] if abs(eb[("m21", "Sr_flank")][k + 1]) >= abs(eb[("m21", "Sr_hinge")][k + 1])
                        else eb[("m21", "Sr_hinge")][k + 1])
    assert fs[k] >= EB_BOUND and d1["Q1"]["beside_first_shell_Sr_only"]["checkpoints_meeting"] == []
    lit = {nm: sorted({str(on[(h, nm)]["literal"]["model"]) for h in HOSTS}) for nm in SITES}
    assert all(len(v) == 1 for v in lit.values()), lit                 # the same literal onset at both hosts
    ff = {int(k): v for k, v in rf["fall_fraction_all_epochs"].items()}
    fall_win = (ff[win[0]], max(o["negative"]["rmse_f_fall_fraction_range"][1] for o in on.values()))
    late = [x for (h, nm), y in eb.items() for m, x in zip(models, y) if m != "Initial" and int(m) >= win[1]]
    assert all(abs(x) > EB_BOUND for x in late)                          # none back within 25 meV from epoch 11

    # ---- (d) D2a closures --------------------------------------------------------------------------------------
    LEV = ("dft", "zeroshot", "finetuned")
    SEG = ("0-2", "2-3", "3-4")
    rows_d, clo = [], {lv: {s: [] for s in SEG + ("i*",)} for lv in LEV}
    istar_dft = {}
    for bn, b in d2["bands"].items():
        assert b["status"] == "not resolved" and not b["resolved"]
        for lv in LEV:
            a = b["D2a"][lv]
            for s in SEG:
                clo[lv][s].append(a["segments_beside"][s]["closure_meV"])
            clo[lv]["i*"].append(a["closure_meV"])
            rows_d.append({"band": bn, "split": b["split"], "level": lv, "i_star_own_argmax": a["i_star"],
                           **{f"closure_{s}_meV": a["segments_beside"][s]["closure_meV"] for s in SEG},
                           "closure_to_i_star_meV": a["closure_meV"]})
        istar_dft[b["D2a"]["dft"]["i_star"]] = istar_dft.get(b["D2a"]["dft"]["i_star"], 0) + 1
    write_csv("fig_wp3_diagnostics_d_closures.csv", rows_d)
    nb = len(d2["bands"])
    assert d2["Q4"]["n_resolved"] == 0 and d2["summary"]["D2a"]["n_resolved"] == 0
    assert sum(abs(v) <= CLOSURE_BOUND for v in clo["dft"]["i*"]) == 0
    assert set(istar_dft) <= {2, 3}                                       # the 3-4 segment is on no DFT path
    seg_rms = d2["Q4"]["dft_segment_closure_rms_meV_beside"]
    for s in SEG:
        assert abs(math.sqrt(np.mean(np.square(clo["dft"][s]))) - seg_rms[s]) < 1e-9
    rng = d2["Q4"]["dft_closure_range_meV"]
    assert abs(min(clo["dft"]["i*"]) - rng[0]) < 1e-9 and abs(max(clo["dft"]["i*"]) - rng[1]) < 1e-9
    i82 = epochs.index(82)
    return {"models": models, "epochs": epochs, "all_ep": all_ep, "rf": rf, "eb": eb, "mid": mid,
            "loss": loss, "rms": rms, "rho": rho, "init_loss": d1["models"]["Initial"]["logged_m21"]["loss"],
            "init_rms": d1["models"]["Initial"]["quantities"]["m21"]["Eb_rms_raw_meV"], "win": win,
            "fall_win": fall_win, "lit": lit, "rms82": rms[i82], "q1": d1["Q1"], "clo": clo, "nb": nb,
            "brackets": brackets, "onset_ff": onset_ff, "fsb": first_shell_best,
            "seg": SEG, "lev": LEV, "seg_rms": seg_rms, "rng": rng, "istar_dft": istar_dft}


def plot(D):
    import matplotlib as mpl
    mpl.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter, NullLocator
    from matplotlib.transforms import ScaledTranslation
    sys.path.insert(0, os.path.expanduser("~/.claude/skills/nature-figure/scripts"))
    try:      # layout QA from the nature-figure toolkit; optional, it does not touch the data
        from audit_panel_alignment import require_matplotlib_panel_alignment
    except ImportError:
        require_matplotlib_panel_alignment = None
        print("note: panel-alignment audit unavailable; figure rendered without it")
    mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                         "svg.fonttype": "none", "pdf.fonttype": 42, "font.size": 7.5,
                         "mathtext.fontset": "custom", "mathtext.rm": "Arial", "mathtext.it": "Arial",
                         "mathtext.bf": "Arial:bold", "mathtext.cal": "Arial", "mathtext.sf": "Arial",
                         "mathtext.default": "regular",
                         "axes.labelsize": 7.5, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
                         "axes.spines.right": False, "axes.spines.top": False, "axes.linewidth": 0.8,
                         "legend.frameon": False, "xtick.major.width": 0.8, "ytick.major.width": 0.8,
                         "xtick.major.size": 2.5, "ytick.major.size": 2.5})
    W_MM = (FIG_WIDTH_MM - L_MM - R_MM - 2 * G_MM) / 3
    W_PT = W_MM / 25.4 * 72
    FIG_H_MM = T_MM + H_TOP_MM + V_MM + H_BOT_MM + B_MM
    fig = plt.figure(figsize=(FIG_WIDTH_MM / 25.4, FIG_H_MM / 25.4))
    gs = fig.add_gridspec(2, 3, left=L_MM / FIG_WIDTH_MM, right=1 - R_MM / FIG_WIDTH_MM, bottom=B_MM / FIG_H_MM,
                          top=1 - T_MM / FIG_H_MM, wspace=G_MM / W_MM, hspace=V_MM / ((H_TOP_MM + H_BOT_MM) / 2),
                          height_ratios=[H_TOP_MM, H_BOT_MM])
    a = fig.add_subplot(gs[0, 0:2]); b = fig.add_subplot(gs[1, 0:2], sharex=a)       # label order a, b, c, d
    c = fig.add_subplot(gs[0, 2]); d = fig.add_subplot(gs[1, 2])
    fits = []
    LIM2 = 1.0 + (G_MM / 25.4 * 72 - LAB_DX - 3) / (2 * W_PT + G_MM / 25.4 * 72)
    LIM_R = 1.0 + (R_MM / 25.4 * 72 - 2) / W_PT            # right column: the figure edge

    def heading(ax, title, sub1, sub2, limit):
        for k, s in enumerate((sub2, sub1)):
            t = ax.annotate(s, (0, 1), xycoords="axes fraction", xytext=(0, 3 + k * SUB_LINE),
                            textcoords="offset points", fontsize=6.3, color=SOFT, ha="left", va="bottom")
            fits.append((t, ax, limit))
        t = ax.annotate(title, (0, 1), xycoords="axes fraction", xytext=(0, 4.5 + 2 * SUB_LINE),
                        textcoords="offset points", fontsize=7.5, color=INK, ha="left", va="bottom")
        fits.append((t, ax, limit))

    models, epochs = D["models"], D["epochs"]
    xm = [X_INIT] + epochs
    win = D["win"]

    # ---------------- (a) logged m21 force RMSE, every epoch ----------------------------------------------------
    a.set_xscale("symlog", linthresh=10, linscale=LINSCALE)
    for lo, hi in D["brackets"]:
        a.axvspan(lo, hi, color=WIN_FILL, lw=0, zorder=0)
    ep, rf = zip(*D["all_ep"])
    a.plot(ep, rf, color="#b8b8b8", lw=0.8, zorder=1)
    kept = [dict(D["all_ep"])[e] for e in epochs]
    a.scatter(epochs, kept, s=12, color=FT_C, zorder=3, linewidths=0)
    a.scatter([X_INIT], [D["rf"]["initial_meV_A"]], s=20, marker="D", color=ZS_C, zorder=3, linewidths=0)
    a.axvline(-1.25, color="#d0d0d0", lw=0.6, ls=(0, (1, 1.5)), zorder=0)
    a.set_ylim(0, 130); a.set_yticks([0, 40, 80, 120])
    a.set_ylabel("m21 force RMSE (meV/Å)")
    of = D["onset_ff"]
    a.text(12, 124, f"at the collapse onsets (shaded),\n{of[0] * 100:.0f}–{of[1] * 100:.0f}% of the Initial → epoch-82\n"
           f"force-RMSE fall is complete", fontsize=6.3, color=SOFT, ha="left", va="top", linespacing=1.2)
    a.text(80, D["rf"]["epoch82_meV_A"] + 9, f"epoch 82: {fmt(D['rf']['epoch82_meV_A'])}", fontsize=6.3, color=FT_C,
           ha="right", va="bottom")
    a.text(X_INIT, D["rf"]["initial_meV_A"] + 7, f"{fmt(D['rf']['initial_meV_A'])}", fontsize=6.3, color=ZS_C,
           ha="center", va="bottom")
    heading(a, "Training trajectory (logged m21 eval)",
            f"all 100 logged epochs and Initial (zero-shot); dots: {len(epochs)} kept checkpoints (m21-loss minima from "
            f"epoch 0)",
            "shaded: the kept-epoch brackets " + " and ".join(f"({lo}, {hi}]" for lo, hi in D["brackets"]) +
            f" of the collapse onsets (error < {MINUS}{EB_BOUND:.0f} meV; added to the plan)",
            LIM2)
    plt.setp(a.get_xticklabels(), visible=False)

    # ---------------- (b) first-shell Sr E_b errors ---------------------------------------------------------------
    for lo, hi in D["brackets"]:                        # stops below the legend, so no key text sits on its edge
        b.axvspan(lo, hi, ymax=B_SHADE_TOP, color=WIN_FILL, lw=0, zorder=0)
    b.axhspan(-EB_BOUND, EB_BOUND, color=BAND_FILL, lw=0, zorder=0)
    b.axhline(0, color="#c8c8c8", lw=0.6, zorder=1)
    b.axvline(-1.25, color="#d0d0d0", lw=0.6, ls=(0, (1, 1.5)), zorder=0)
    b.plot(xm, [D["mid"][m] for m in models], color=MID_C, lw=0.8, ls=(0, (3, 2)), marker="o", markersize=1.6,
           zorder=2)
    for nm in ("Sr_flank", "Sr_hinge"):                 # hinge (filled) drawn last, on top of the open flank squares
        for h in HOSTS:
            y = D["eb"][(h, nm)]
            tr = b.transData + ScaledTranslation(SERIES_DX[(h, nm)] / 72, 0, fig.dpi_scale_trans)
            b.plot(xm, y, color=HOST_C[h], lw=0.6, ls=(0, (1, 1.2)), zorder=3, transform=tr)
            b.scatter(xm, y, s=11 if nm == "Sr_hinge" else 12, marker=SITE_MK[nm], transform=tr,
                      facecolor=HOST_C[h] if nm == "Sr_hinge" else "white", edgecolor=HOST_C[h], linewidth=0.8,
                      zorder=5 if nm == "Sr_hinge" else 4)
    b.set_ylim(-140, 210); b.set_yticks([-100, -50, 0, 50, 100, 150, 200])
    b.set_yticklabels([fmt(v, 0) for v in (-100, -50, 0, 50, 100, 150, 200)])
    b.set_xlim(-4.2, X_MAX)
    ticks = [X_INIT, 0, 2, 4, 6, 8, 10, 20, 50, 100]
    b.xaxis.set_major_locator(FixedLocator(ticks))
    b.xaxis.set_major_formatter(FuncFormatter(lambda v, _: "Initial" if v == X_INIT else f"{v:g}"))
    b.xaxis.set_minor_locator(NullLocator())
    b.set_xlabel("Epoch (linear to 10, logarithmic beyond)")
    b.set_ylabel("Far-referenced E$_b$ error (meV)")
    b.text(X_MAX - 3, EB_BOUND - 3, f"±{EB_BOUND:.0f} meV", fontsize=6.3, color=BAND_TXT, ha="right", va="top")
    key = [Patch(facecolor=HOST_C["m21"], edgecolor="none", label="m21 (validation)"),
           Patch(facecolor=HOST_C["m05"], edgecolor="none", label="m05 (training)"),
           Line2D([], [], marker="o", color=INK, mfc=INK, ls="none", markersize=3.4, label="Sr hinge"),
           Line2D([], [], marker="s", color=INK, mfc="white", ls="none", markersize=3.4, label="Sr flank"),
           Line2D([], [], color=MID_C, lw=0.8, ls=(0, (3, 2)), marker="o", markersize=1.6, label="m21 Sr mid (Q1 caveat)"),
           Line2D([], [], color=INK, lw=0.6, ls=(0, (1, 1.2)), label="joins evaluated models only")]
    b.legend(handles=key, loc="upper right", fontsize=6.3, ncol=3, handlelength=1.6, handleheight=0.6,
             columnspacing=1.0, handletextpad=0.4, borderaxespad=0.2)
    q1, lit = D["q1"], D["lit"]
    heading(b, "Q1, Q2: first-shell Sr E$_b$ error per model (raw F energies)",
            f"Q1: none meets the rule, nor its first-shell-only form (closest: epoch {D['fsb'][0]}, m21 {D['fsb'][2]} "
            f"{fmt(D['fsb'][3])} meV)",
            f"Q2 as planned (first |error| > {EB_BOUND:.0f} meV): {lit['Sr_flank'][0]} (flank sites) or epoch "
            f"{lit['Sr_hinge'][0]} (hinge sites), all positive",
            LIM2)

    # ---------------- (c) E_b RMS against loss ---------------------------------------------------------------------
    c.set_xscale("log")
    c.axhline(D["init_rms"], color=ZS_C, lw=0.7, ls=(0, (3, 2)), zorder=1)
    c.scatter([D["init_loss"]], [D["init_rms"]], s=18, marker="D", color=ZS_C, zorder=2, linewidths=0)
    c.scatter(D["loss"], D["rms"], s=14, color=FT_C, zorder=3, linewidths=0)
    lab = {0: (4, 0, "left", "center"), 2: (4, 0, "left", "center"), 7: (-3, 3, "right", "bottom"),
           77: (4, -4, "left", "center"), 82: (0, -5, "center", "top")}
    for e, (dx, dy, ha, va) in lab.items():
        i = D["epochs"].index(e)
        c.annotate(f"{e}", (D["loss"][i], D["rms"][i]), xytext=(dx, dy), textcoords="offset points", fontsize=6.3,
                   color=SOFT, ha=ha, va=va)
    c.annotate("Initial", (D["init_loss"], D["init_rms"]), xytext=(0, -7), textcoords="offset points", fontsize=6.3,
               color=ZS_C, ha="center", va="top")
    c.set_xlim(0.01, 15)
    c.xaxis.set_major_locator(FixedLocator([0.01, 0.1, 1, 10]))
    c.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    c.xaxis.set_minor_formatter(NullFormatter())
    c.set_ylim(0, 125); c.set_yticks([0, 40, 80, 120])
    c.set_xlabel("Logged m21 loss")
    c.set_ylabel("m21 E$_b$ RMS, 5 sites (meV)")
    c.text(0.97, 0.97, f"ρ = {fmt(D['rho'], 2)} (n = {len(epochs)})", transform=c.transAxes, fontsize=6.3, color=INK,
           ha="right", va="top")
    i7 = int(np.argmin(D["rms"]))
    heading(c, "Q3: E$_b$ RMS against loss", f"all {len(epochs)} above zero-shot {fmt(D['init_rms'])} meV",
            f"selected (82) {fmt(D['rms82'])}; lowest ({D['epochs'][i7]}) {fmt(D['rms'][i7])} meV", LIM_R)

    # ---------------- (d) D2a closures ---------------------------------------------------------------------------
    LEV_C = {"dft": INK, "zeroshot": ZS_C, "finetuned": FT_C}
    LEV_DX = {"dft": -0.24, "zeroshot": 0.0, "finetuned": 0.24}
    cats = list(D["seg"]) + ["i*"]
    d.axhspan(-CLOSURE_BOUND, CLOSURE_BOUND, xmin=0.75, xmax=1.0, color=BAND_FILL, lw=0, zorder=0)
    d.axhline(0, color="#c8c8c8", lw=0.6, zorder=1)
    jit = ((np.arange(D["nb"]) * 0.6180339887) % 1.0 - 0.5) * 0.14     # golden-ratio sequence: no band order
    for k, s in enumerate(cats):
        for lv in D["lev"]:
            y = np.array(D["clo"][lv][s])
            d.scatter(k + LEV_DX[lv] + jit, y, s=4, color=LEV_C[lv], linewidths=0, zorder=3 if lv == "dft" else 2,
                      alpha=0.9)
    d.axvline(2.5, color="#d0d0d0", lw=0.6, ls=(0, (1, 1.5)), zorder=0)
    d.set_xlim(-0.5, 3.5)
    d.set_xticks(range(4)); d.set_xticklabels(["0→2", "2→3", "3→4", "0→i*"])
    d.tick_params(axis="x", length=0)
    d.set_ylim(-160, 40); d.set_yticks([-150, -100, -50, 0])
    d.set_yticklabels([fmt(v, 0) for v in (-150, -100, -50, 0)])
    d.set_xlabel("Segment, or path 0→i*")
    d.set_ylabel("Path-work closure (meV)")
    d.text(3.0, CLOSURE_BOUND + 2, f"rule\n±{CLOSURE_BOUND:.0f} meV", fontsize=6.3, color=BAND_TXT, ha="center",
           va="bottom", linespacing=1.15)
    d.legend(handles=[Line2D([], [], marker="o", color=LEV_C[lv], ls="none", markersize=2.6, label=t)
                      for lv, t in zip(D["lev"], ("DFT", "zero-shot", "fine-tuned"))],
             loc="lower center", bbox_to_anchor=(0.5, 0.0), fontsize=6.3, handletextpad=0.1, borderaxespad=0.2)
    sr = D["seg_rms"]
    d.text(1.5, -45, f"DFT RMS (meV)\n0→2  {fmt(sr['0-2'])}\n2→3  {fmt(sr['2-3'])}\n3→4  {fmt(sr['3-4'])}", fontsize=6.3,
           color=INK, ha="center", va="top", linespacing=1.3)
    ist = ", ".join(f"{v} in {n}" for v, n in sorted(D["istar_dft"].items(), key=lambda t: -t[1]))
    heading(d, "Q4 (D2a): closure per band", f"{D['nb']} bands; none within the DFT rule",
            f"i* = E maximum; DFT: {ist}", LIM_R)

    for lb, ax in zip("abcd", (a, b, c, d)):
        t = ax.transAxes + ScaledTranslation(-LAB_DX / 72, LAB_DY / 72, fig.dpi_scale_trans)
        ax.text(0, 1, lb, transform=t, fontsize=8, fontweight="bold", ha="left", va="bottom")
    out = os.path.join(HERE, NAME)
    fig.set_dpi(600)                   # measure the text fits at the export resolution
    fig.canvas.draw()
    rnd = fig.canvas.get_renderer()
    for art, ax, lim in fits:
        x1 = ax.transAxes.inverted().transform(art.get_window_extent(rnd).get_points())[1, 0]
        assert x1 <= lim + 1e-3, (art.get_text(), x1, lim)
    top = max(ax.transAxes.inverted().transform(art.get_window_extent(rnd).get_points())[1, 1] for art, ax, _ in fits
              if ax in (a, c))
    assert top < 1 + T_MM / H_TOP_MM, top          # top headings stay inside the figure
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

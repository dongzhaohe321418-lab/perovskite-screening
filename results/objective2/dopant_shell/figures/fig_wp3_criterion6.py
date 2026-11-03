#!/usr/bin/env python
"""Figure WP3 / criterion 6: did fine-tuning on DFT frames improve MACE-MP-0 on held-out hosts?

Figure contract (written before plotting; revised after review, see the review record at the end)
  Results-level question. Did fine-tuning MACE-MP-0 on the WP3 DFT frames improve it on the held-out
    test hosts (PLAN amendment 2026-10-28m, items 3-5)?
  Core conclusion. Fine-tuning lowered the force RMSE on every test frame, but criterion 6 gives
    "No improvement": over the 4 m30/m32 pairs the paired dE_a RMS rose on raw F and on E', and the
    far-referenced E_b RMS over the 5 m30 sites rose. Adoption (a)-(c) are not met: the 9-pair E' RMS
    of adoption (b) fell only marginally and stays above its bound, two pairs change class, and the Sr
    hinge and flank E_b errors lie far outside the criterion-4 band. The largest failure is the Sr hinge
    site, where the fine-tuned far-referenced E_b loses the first-shell repulsion that DFT shows.
  What would overturn it. All four pre-registered criterion-6 statistics strictly below zero-shot.
  Evidence chain (one role per panel).
    a  Hero, decisive. The four pre-registered criterion-6 statistics, (i) force RMSE over the 46
       m30/m32 frames, (ii) paired dE_a RMS on raw F and (ii) on E' over the 4 m30/m32 pairs, (iii)
       far-referenced E_b RMS over the 5 m30 sites: fine-tuned / zero-shot on a log axis (strictly below
       zero-shot <=> ratio < 1), with the values, the verdict rule and the verdicts from the JSON. The
       small filled diamonds and grey values are the companions PLAN item 3 lists "beside the verdict";
       none is in the criterion-6 verdict. One of them, the 9-pair RMS on E', is also the adoption-(b)
       statistic (decisive for adoption, panel c) and is labelled so. The per-frame force RMSE
       (reported, not gated; PLAN m item 5 calls its fall almost certain) enters a as the number of
       frames that improve; all 96 per-frame values are in source data (a_frames.csv).
    b  Decomposition of (ii), pre-registered (decisive). The signed dE_a error (model - DFT) of each of
       the 4 m30/m32 pairs, on raw F and on E', for both models, with the RMS of each basis: which pairs
       carry the rise in (ii).
    c  Adoption (b), pre-registered. Paired dE_a over the 9 test pairs on E' (its basis), model against
       DFT for both models; shaded cells = same class as DFT under the +/-59.5 meV boundaries, so class
       changes are the points in white cells (circled). The two models of a pair sit 1.8 pt either side
       of the DFT x (a dodge, so that m32 Sr, 2 meV apart, shows both points).
    d  Adoption (c) = the sites of criterion 6(iii), pre-registered. Far-referenced E_b at the 5 non-far
       m30 sites, raw F: DFT bar +/- 25 meV, both models with stems to DFT; locates the failure.
    e  Boundary, reported, not gated. Signed absolute E_a error (model - DFT) on raw F, the basis that
       wp3_eval.json gives for the item-5 coverage figures (E' beside, in source data; the DFT E_a is
       common to both models, so the change on fine-tuning is the same on either basis). Groups: the
       training hosts (fit quality); m21 (validation): selected the checkpoint, so not independent, and
       its GA and Sr DFT maxima are unbracketed (those points carry a dagger); and the 16 test bands.
       Dotted line: the +59 meV item-5 coverage trigger (read from the JSON key), which no item-1'
       zero-shot band exceeds on raw F. Points in each column are swarmed so that none is hidden.
  Encoding. Colour = model (zero-shot warm grey, fine-tuned teal); shape = dopant in b-e (circle GA,
    square Sr, triangle undoped band); open = item-1' host (c, e). This differs on purpose from the
    earlier WP1/WP2 figures, where colour is the dopant (GA blue, Sr red; undoped grey in wp2b) and
    shape the host: here the contrast that matters is the model. The zero-shot colour is a warm grey so
    that it is not the wp2b undoped grey.
  Archetype. Quantitative grid with an asymmetric hero (a spans two of three columns).
  Backend. Python / matplotlib only.
  Export. 183 mm double column; every PDF glyph >= 5 pt; editable text (pdf.fonttype 42, svg.fonttype
    none); pdf, svg, png and tiff (600 dpi); source data source_data/fig_wp3_criterion6_*.csv; QA: render-
    time alignment gate (1.5 pt, strict, panel labels required), validate_figure.py, audit_pdf_text.py
    (5 pt) and audit_figure_collisions.py on the exported PDF.

Statistics. Every point is one deterministic single point or a difference of such. There are no
replicates, error bars or tests: none was run (PLAN m item 5: smallest one-sided sign-flip p is 1/16 on
4 pairs and 1/32 on 5 sites). Every pair, site and band is drawn; n is stated per panel.

Data. Every plotted number and every number printed in the figure is read from ../wp3/wp3_eval.json at
plot time (wp3_eval.json is the single source; nothing is typed in). Derived at plot time: the ratios
fine-tuned / zero-shot (a, positions only), counts, and the largest |error| printed in d. Thresholds:
the +/-59.5 meV class boundary (PLAN amendment g item 2; band_class of scripts/32) is not stored in the
JSON. It is the one typed-in number (a documented exemption): it is asserted to reproduce every
class_model / class_dft in the JSON and to lie inside the bracket those classes allow (largest |dE_a| of
class 0 < 59.5 < smallest |dE_a| of class +/-1; printed at run time). The 25 and 20 meV thresholds of
adoption (c) and (b) and the 59 meV coverage trigger of e are parsed from the JSON keys all_below_25meV,
rms_below_20meV and coverage_item1p_zeroshot_abs_Ea_error_above_59meV, and asserted against those flags
or that list. The JSON fields abs_Ea_error_* are SIGNED errors of the absolute barrier E_a (model - DFT).
Frame groups of a_frames.csv are taken from the labels as scripts/39 forms them (band pattern; hosts of
the 4 criterion-6 pairs; hosts of the other adoption-(b) pairs) and checked against the JSON group
values. Adoption (d) and (e) are still running and are not shown.

QA notes. validate_figure.py may report WARN FONT-GLYPH-FLOOR because it scales the smallest font in the
source by 0.7; mathtext subscripts occur only in 7.5 pt text (5.25 pt glyphs), and audit_pdf_text.py on
the PDF is the check of record for the 5 pt floor. Text widths that the layout depends on (subtitles of
c-e, the left-hand column of a, the shared key) are measured after the draw and asserted to stay inside
their slot.

    python fig_wp3_criterion6.py

Review record (2026-11-03; one review round, twelve findings; "data" and "science" are the review lenses)
  1  data     a labels the 9-pair E' RMS "not gated" while c gates it as adoption (b). Accepted. That
              row's status cell now reads "adoption (b), c" (chosen in code by matching the JSON path
              and value of adoption.b.rms_meV); the reported glyph's legend reads "Reported beside
              criterion 6 (not in its verdict)"; its status in a_criterion6.csv names both roles.
  2  data     e plotted E' where the JSON gives raw F as the item-5 coverage basis. Accepted (reproduced:
              on E' m10 undoped and m10 GA sit above +59 meV, on raw F no item-1' band does). e now plots
              raw F, keeps E' beside in e_bands.csv, draws the +59 meV trigger from the JSON key and
              asserts that the item-1' bands above it on raw F equal the JSON list (empty).
  3  data     The +/-59.5 meV class boundary is typed in. Accepted as information; value unchanged. The
              exemption stays documented here (amendment g item 2), c now cites "amendment g" (the
              full item reference did not fit beside the shaded cell), and the code asserts that 59.5
              lies inside the bracket the 288 JSON classes allow.
  4  science  The m21 caveat lacked "its GA and Sr DFT maxima are unbracketed". Accepted. The m21 tick
              and a note under e are now built from reported.item5.m21.label; the m21 GA and Sr points
              (systems parsed from that label) carry a dagger.
  5  science  Same as 1 (science lens). Accepted; fixed by the change listed under 1.
  6  science  Hidden points in the b inset and in e. Accepted. The b scatter and its inset are gone (see
              9); e is swarmed per column with a minimum centre distance equal to the marker's outer
              size, and the code asserts that every column fits. The same check found the m32 Sr
              zero-shot marker in c mostly under its fine-tuned one (2 meV apart), so c now dodges the
              two models by 1.8 pt about the DFT x.
  7  science  Key shapes clashed with a and b; two grey filled circles. Accepted. The key scopes shape to
              b-e and draws shape glyphs as black outlines; a's reported companions use a small filled
              diamond, a glyph now used nowhere else (b has no diamonds any more). The suggested vertical
              tick was tried and dropped: at a ratio of about 1 (the 9-pair E' row) it vanishes into the
              ratio-1 reference line.
  8  science  Docstring overstated the energy result. Accepted; the core conclusion now states that the
              9-pair E' RMS fell marginally but stays above the bound.
  9  science  b spent a full panel on the near-certain force result and hid the decisive per-pair data.
              Accepted. b now shows the per-pair raw-F and E' errors behind (ii) for both models (n = 4
              each, every point); the per-frame result is the count in a (all values in a_frames.csv).
  10 science  Colour/shape meanings differ from the WP1/WP2 figures. Accepted in part: the zero-shot
              colour is now a warm grey, not the wp2b undoped grey, and the encoding change is stated
              above. Dopant-coloured labels were not added: colour encodes the model here, and the d
              tick labels already name dopant and site.
  11 science  c subtitle ran under d's letter and lacked a unit. Accepted; shortened to
              "RMS <zero-shot> -> <fine-tuned> meV; needs < 20 meV"; every heading is now asserted to
              end at least 3 pt before the next panel letter.
  12 science  Mixed precision in d and a typed count in a. Accepted; d prints site errors at one
              precision (0 dp) in both places, and a formats the number of conditions from the JSON.
"""
import csv, json, math, os, re, sys, textwrap
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL = os.path.join(HERE, "..", "wp3", "wp3_eval.json")
SRC = os.path.join(HERE, "source_data")
NAME = "fig_wp3_criterion6"
CLASS_BOUND = 59.5            # meV; PLAN amendment g item 2; the one typed-in number, asserted against the JSON classes
BAND_RE = re.compile(r"(m\d\d)_(undoped|GA|Sr)_img(\d)$")     # band-frame labels (scripts/39 is_band)
ARMS = ("zeroshot", "finetuned")
ZS_C, FT_C, DFT_C = "#a48e72", "#0e7a72", "#1a1a1a"
INK, SOFT = "#1a1a1a", "#555555"
BAND_FILL, GAIN_FILL = "#eceff2", "#e3f0ed"
MRK = {"GA": "o", "Sr": "s", "undoped": "^"}
MINUS = "−"
FIG_WIDTH_MM = 183
L_MM, R_MM, G_MM = 13.0, 3.0, 17.0      # left / right margin, column gutter
T_MM, V_MM, B_MM = 17.5, 19.0, 21.0     # top margin, row gap, bottom margin
LAB_DX, LAB_DY = 30.0, 13.0             # panel letter: fixed point offset from the plot-area corner
E_S, E_DMIN = 9, 3.8                    # e: marker area (pt^2) and minimum centre distance of the swarm (pt)


def fmt(x, nd=1, signed=False):
    s = f"{x:+.{nd}f}" if signed else f"{x:.{nd}f}"
    return s.replace("-", MINUS)


def tidy(key):
    return key.replace("_", " ")


def band_class(x):
    return int(x > CLASS_BOUND) - int(x < -CLASS_BOUND)


def key_threshold(obj, pattern):
    hits = [k for k in obj if re.fullmatch(pattern, k)]
    assert len(hits) == 1, (pattern, sorted(obj))
    return float(re.fullmatch(pattern, hits[0]).group(1)), hits[0]


def write_csv(fn, rows):
    with open(os.path.join(SRC, fn), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def class_entries(o):
    """Every (dE_a, class) entry anywhere in the JSON: model and DFT of each pair table entry."""
    if isinstance(o, dict):
        if "dEa_model_meV" in o and "class_model" in o:
            yield o["dEa_model_meV"], o["class_model"]
            yield o["dEa_dft_meV"], o["class_dft"]
        for v in o.values():
            yield from class_entries(v)
    elif isinstance(o, list):
        for v in o:
            yield from class_entries(v)


def swarm(y_pt, dmin, step):
    """Deterministic beeswarm: x offsets (pt) such that no two centres are closer than dmin."""
    placed, off = [], [0.0] * len(y_pt)
    for i in sorted(range(len(y_pt)), key=lambda j: y_pt[j]):
        k = 0
        while True:
            hit = next((cx for cx in ([0.0] if k == 0 else [k * step, -k * step])
                        if all((cx - px) ** 2 + (y_pt[i] - py) ** 2 >= dmin ** 2 for px, py in placed)), None)
            if hit is not None:
                break
            k += 1
        off[i] = hit
        placed.append((hit, y_pt[i]))
    return off


def collect(d):
    """Read and cross-check everything the figure shows; write the source-data CSVs."""
    assert d["mode"] == "full" and d["stand_in"] is False and d["gate"]["pass"] is True
    c6, ad, rep, out = d["criterion6"], d["adoption"], d["reported"], {}
    V = c6["values"]
    crit_pairs = list(V["zeroshot"]["ii_raw"])
    assert crit_pairs == list(V["zeroshot"]["ii_Eprime"])
    crit_hosts = list(dict.fromkeys(p.split("_")[0] for p in crit_pairs))
    all_pairs = list(ad["b"]["pairs"])
    item1p_hosts = [h for h in dict.fromkeys(p.split("_")[0] for p in all_pairs) if h not in crit_hosts]
    site_keys = list(V["zeroshot"]["iii_raw"])
    hosts_txt = "/".join(crit_hosts)

    # ---- the one typed-in number: the class boundary must sit inside the bracket the JSON allows ----
    ce = list(class_entries(d))
    assert ce and all(band_class(x) == c for x, c in ce)
    lo0 = max(abs(x) for x, c in ce if c == 0)
    hi1 = min(abs(x) for x, c in ce if c != 0)
    assert lo0 < CLASS_BOUND < hi1
    print(f"class boundary {CLASS_BOUND} meV inside the JSON bracket ({lo0:.2f}, {hi1:.2f}) over {len(ce)} entries")

    # ---- per-frame force RMSE (summarised in a; all values to a_frames.csv) ----------------------------
    pf = rep["per_frame_force_rmse_eVA"]
    wp2c_hosts = {l.split("_")[0] for l in pf if not BAND_RE.match(l)}
    assert len(wp2c_hosts) == 1
    eb_host = wp2c_hosts.pop()
    assert f"({eb_host})" in ad["c"]["label"]
    gname = {"crit": f"{hosts_txt} band images", "wp2c": f"{eb_host} WP2c frames",
             "item1p": "Item-1′ band images"}
    frames = []
    for lab, v in pf.items():
        m, host = BAND_RE.match(lab), lab.split("_")[0]
        g = ("crit" if host in crit_hosts else "item1p" if host in item1p_hosts else None) if m else \
            ("wp2c" if host == eb_host else None)
        assert g is not None, lab
        frames.append({"label": lab, "host": host, "group": g, "group_name": gname[g],
                       "zeroshot_force_rmse_eVA": v["zeroshot"], "finetuned_force_rmse_eVA": v["finetuned"],
                       "ratio_finetuned_over_zeroshot": v["finetuned"] / v["zeroshot"],
                       "finetuned_lower": v["finetuned"] < v["zeroshot"]})
    n_imp = rep["n_improve"]["frames_force_rmse"]
    assert n_imp["n"] == len(frames) == rep["n_test_frames"]
    assert n_imp["n_improve"] == sum(f["finetuned_lower"] for f in frames)
    n46 = d["position_check"]["gate_46"]["n_frames"]
    assert sum(f["group"] in ("crit", "wp2c") for f in frames) == n46
    for arm in ARMS:   # group check: equal-weight pooling of per-frame RMSE vs the JSON (atom counts differ by < 1%)
        for g, key in (("crit", "i_band_eVA"), ("wp2c", "i_wp2c_eVA")):
            x = math.sqrt(np.mean([f[f"{arm}_force_rmse_eVA"] ** 2 for f in frames if f["group"] == g]))
            assert abs(x / V[arm][key] - 1) < 5e-3, (arm, g, x, V[arm][key])
    write_csv(f"{NAME}_a_frames.csv", frames)

    # ---- (a) criterion 6 ---------------------------------------------------------------------------
    cond = c6["conditions"]
    assert c6["ii_bases_in_verdict"] == ["raw", "Eprime"] and list(cond) == ["i", "ii_raw", "ii_Eprime", "iii"]
    nine = rep["ii_all_9_pairs"]
    n9 = nine["raw"]["n_complete"]
    assert n9 == nine["Eprime"]["n_complete"] == len(all_pairs) == ad["b"]["n_pairs"]
    assert ad["b"]["basis"] == c6["basis"] == "Eprime"
    adb_path = f"reported.ii_all_9_pairs.{ad['b']['basis']}"      # the reported companion that adoption (b) gates
    nl = "all" if n_imp["n_improve"] == n_imp["n"] else f"{n_imp['n_improve']}"
    spec = [("i", "(i) Force RMSE", f"eV/Å; pooled, {n46} {hosts_txt} frames", 4,
             (f"reported: {rep['n_test_frames']} test frames, {nl} lower", rep["i_all_test_frames_eVA"]["zeroshot"],
              rep["i_all_test_frames_eVA"]["finetuned"], "reported.i_all_test_frames_eVA")),
            ("ii_raw", "(ii) Paired ΔE$_a$ RMS", f"meV; raw F, {len(crit_pairs)} {hosts_txt} pairs", 1,
             (f"reported: all {n9} test pairs", nine["raw"]["rms_zeroshot_meV"], nine["raw"]["rms_finetuned_meV"],
              "reported.ii_all_9_pairs.raw")),
            ("ii_Eprime", "(ii) Paired ΔE$_a$ RMS", f"meV; E′, {len(crit_pairs)} {hosts_txt} pairs", 1,
             (f"reported: all {n9} test pairs", nine["Eprime"]["rms_zeroshot_meV"], nine["Eprime"]["rms_finetuned_meV"],
              "reported.ii_all_9_pairs.Eprime")),
            ("iii", "(iii) Far-ref. E$_b$ RMS", f"meV; raw F, {len(site_keys)} {eb_host} sites", 1,
             ("reported: E′ basis", c6["iii_Eprime_rms_meV_reported"]["zeroshot"],
              c6["iii_Eprime_rms_meV_reported"]["finetuned"], "criterion6.iii_Eprime_rms_meV_reported"))]
    assert sum(s[4][3] == adb_path for s in spec) == 1
    hero, hero_rows = [], []
    for key, stat, sset, nd, (rdesc, rzs, rft, rpath) in spec:
        c = cond[key]
        assert c["evaluable"] and not c["nonfinite_frames"] and c["strictly_below"] == (c["finetuned"] < c["zeroshot"])
        pos = np.array([c["zeroshot"], c["finetuned"], rzs, rft])
        assert not np.any(pos <= 0), "log axis of (a): ratios need strictly positive values"
        if rpath == adb_path:      # reported beside criterion 6, but it is the adoption-(b) statistic
            assert abs(rft - ad["b"]["rms_meV"]) < 1e-12
            rstat, rstat_csv = "adoption (b), c", ("reported beside criterion 6 (not in its verdict); "
                                                    "also the adoption (b) statistic (decisive for adoption, panel c)")
        else:
            rstat, rstat_csv = "not gated", "reported beside criterion 6 (not in its verdict); not gated"
        hero.append({"key": key, "stat": stat, "set": sset, "nd": nd, "zs": c["zeroshot"], "ft": c["finetuned"],
                     "below": c["strictly_below"], "rdesc": rdesc, "rzs": rzs, "rft": rft, "rstat": rstat})
        unit = "eV/A" if key == "i" else "meV"
        hero_rows.append({"statistic": stat.replace("$", ""), "set": sset.split("; ", 1)[1], "status": "pre-registered (decisive)",
                          "unit": unit, "zeroshot": c["zeroshot"], "finetuned": c["finetuned"],
                          "ratio_finetuned_over_zeroshot": c["finetuned"] / c["zeroshot"],
                          "strictly_below": c["strictly_below"], "json": f"criterion6.conditions.{key}"})
        hero_rows.append({"statistic": stat.replace("$", ""), "set": rdesc.replace("reported: ", ""),
                          "status": rstat_csv, "unit": unit, "zeroshot": rzs, "finetuned": rft,
                          "ratio_finetuned_over_zeroshot": rft / rzs, "strictly_below": "", "json": rpath})
    all_below = all(h["below"] for h in hero)
    assert (c6["verdict"] == "No improvement") == (not all_below)
    assert (c6["verdict_h"] == "No improvement") == (not all(cond[k]["strictly_below"] for k in ("i", "ii_raw", "iii")))
    write_csv(f"{NAME}_a_criterion6.csv", hero_rows)
    status = lambda x: x["status"] if "status" in x else ("met" if x["met"] else "not met")
    verdict = {"verdict": c6["verdict"], "verdict_label": c6["verdict_label"], "verdict_h": c6["verdict_h"],
               "verdict_h_label": c6["verdict_h_label"], "wording": c6["wording"],
               "outcome": d["outcome"]["outcome"], **{f"adoption_{k}": status(ad[k]) for k in "abcde"}}
    write_csv(f"{NAME}_a_verdict.csv", [{"item": k, "value": v} for k, v in verdict.items()])

    # ---- (b) criterion 6 (ii) per pair, raw F and E' -------------------------------------------------
    crit6 = []
    for basis in ("ii_raw", "ii_Eprime"):
        for arm in ARMS:
            e = [V[arm][basis][p]["error_meV"] for p in crit_pairs]
            assert abs(math.sqrt(np.mean(np.square(e))) - cond[basis][arm]) < 1e-9
        for p in crit_pairs:
            z, f = V["zeroshot"][basis][p], V["finetuned"][basis][p]
            assert z["dEa_dft_meV"] == f["dEa_dft_meV"]
            crit6.append({"pair": p, "host": p.split("_")[0], "dopant": p.split("_")[1],
                          "basis": "raw F" if basis == "ii_raw" else "E′", "dEa_dft_meV": z["dEa_dft_meV"],
                          **{f"{a}_{k}": src[k] for a, src in (("zeroshot", z), ("finetuned", f))
                             for k in ("dEa_model_meV", "error_meV")},
                          "finetuned_abs_error_larger": abs(f["error_meV"]) > abs(z["error_meV"]),
                          "json": f"criterion6.values.<arm>.{basis}.{p}"})
    write_csv(f"{NAME}_b_crit6_pairs.csv", crit6)

    # ---- (c) adoption (b): 9 pairs on E' -----------------------------------------------------------
    def entries(src):                                   # every (model, DFT) dE_a entry of a pair table
        for v in src.values():
            yield from ([v] if "dEa_model_meV" in v else [v[a] for a in ARMS])
    tables = [ad["b"]["pairs"], ad["b"]["reported_raw_F_beside"]] + [V[a][k] for a in ARMS for k in ("ii_raw", "ii_Eprime")] \
        + [{p: pp[b] for p, pp in h["pairs"].items()} for h in rep["item5"].values() for b in ("raw", "Eprime")]
    n_checked = 0
    for t in tables:
        for e in entries(t):
            assert band_class(e["dEa_model_meV"]) == e["class_model"] and band_class(e["dEa_dft_meV"]) == e["class_dft"]
            assert abs(e["dEa_model_meV"] - e["dEa_dft_meV"] - e["error_meV"]) < 1e-6
            n_checked += 1
    assert n_checked > 0
    thr_b, kb = key_threshold(ad["b"], r"rms_below_(\d+(?:\.\d+)?)meV")
    pairs, rms = [], {}
    for arm in ARMS:
        errs = [ad["b"]["pairs"][p][arm]["error_meV"] for p in all_pairs]
        rms[arm] = nine["Eprime"][f"rms_{arm}_meV"]
        assert abs(math.sqrt(np.mean(np.square(errs))) - rms[arm]) < 1e-9
    assert abs(rms["finetuned"] - ad["b"]["rms_meV"]) < 1e-9 and ad["b"][kb] == (ad["b"]["rms_meV"] < thr_b)
    changes = {a: [p for p in all_pairs if ad["b"]["pairs"][p][a]["class_model"] != ad["b"]["pairs"][p][a]["class_dft"]] for a in ARMS}
    assert changes["finetuned"] == ad["b"]["class_changes"]
    for p in all_pairs:
        v, r = ad["b"]["pairs"][p], ad["b"]["reported_raw_F_beside"][p]
        assert v["zeroshot"]["dEa_dft_meV"] == v["finetuned"]["dEa_dft_meV"]
        pairs.append({"pair": p, "host": p.split("_")[0], "dopant": p.split("_")[1],
                      "set": "criterion 6 (m30/m32)" if p in crit_pairs else "item-1'",
                      "dEa_dft_Eprime_meV": v["zeroshot"]["dEa_dft_meV"], "class_dft_Eprime": v["zeroshot"]["class_dft"],
                      **{f"{a}_{k}": v[a][k] for a in ARMS for k in ("dEa_model_meV", "error_meV", "class_model")},
                      "dEa_dft_rawF_meV_beside": r["zeroshot"]["dEa_dft_meV"],
                      **{f"{a}_error_rawF_meV_beside": r[a]["error_meV"] for a in ARMS}})
    write_csv(f"{NAME}_c_pairs.csv", pairs)

    # ---- (d) adoption (c): 5 m30 sites, raw F ------------------------------------------------------
    thr_c, kc = key_threshold(ad["c"], r"all_below_(\d+(?:\.\d+)?)meV")
    sites = []
    for s in site_keys:
        z, f = V["zeroshot"]["iii_raw"][s], V["finetuned"]["iii_raw"][s]
        assert z["Eb_dft_farref_meV"] == f["Eb_dft_farref_meV"] and z["name"] == f["name"] and z["near"] == f["near"]
        assert f["error_meV"] == ad["c"]["errors_meV"][s]
        assert abs(f["Eb_model_farref_meV"] - f["Eb_dft_farref_meV"] - f["error_meV"]) < 1e-6
        if f["near"]:
            assert ad["c"]["near_signs_agree"][f["name"]] == f["sign_agree"]
        ze, fe = V["zeroshot"]["iii_Eprime"][s], V["finetuned"]["iii_Eprime"][s]
        sites.append({"site": s, "name": z["name"], "dopant": z["dopant"], "near": z["near"],
                      "Eb_dft_farref_rawF_meV": z["Eb_dft_farref_meV"],
                      **{f"{a}_{k}": src[k] for a, src in (("zeroshot", z), ("finetuned", f))
                         for k in ("Eb_model_farref_meV", "error_meV", "sign_agree")},
                      "Eb_dft_farref_Eprime_meV_beside": ze["Eb_dft_farref_meV"],
                      "zeroshot_error_Eprime_meV_beside": ze["error_meV"], "finetuned_error_Eprime_meV_beside": fe["error_meV"]})
    assert ad["c"][kc] == all(abs(x["finetuned_error_meV"]) < thr_c for x in sites)
    assert abs(ad["c"]["max_abs_error_meV"] - max(abs(x["finetuned_error_meV"]) for x in sites)) < 1e-9
    for arm, key in (("zeroshot", "iii_raw_rms_meV"), ("finetuned", "iii_raw_rms_meV")):
        assert abs(math.sqrt(np.mean([x[f"{arm}_error_meV"] ** 2 for x in sites])) - V[arm][key]) < 1e-9
        assert abs(V[arm][key] - cond["iii"][arm]) < 1e-12
    write_csv(f"{NAME}_d_sites.csv", sites)

    # ---- (e) signed absolute E_a error on raw F, the item-5 coverage basis (reported, not gated) ------
    cov = rep["coverage_item1p_zeroshot_abs_Ea_error_above_59meV"]
    assert cov["basis"].startswith("raw F") and "E' beside" in cov["basis"]
    thr_cov, _ = key_threshold(rep, r"coverage_item1p_zeroshot_abs_Ea_error_above_(\d+(?:\.\d+)?)meV")
    i5 = rep["item5"]
    train = [h for h, v in i5.items() if v["label"].startswith("training host")]
    valid = [h for h in i5 if h not in train]
    assert valid == ["m21"]
    m21_head, m21_rest = i5["m21"]["label"].split(": ", 1)          # "m21 (validation)", "...; its GA and Sr ..."
    m21_p1, m21_p2 = m21_rest.split("; ")
    assert m21_p1.endswith("not independent")
    unbr = re.fullmatch(r"its (.+) DFT maxima are unbracketed", m21_p2)
    assert unbr
    unbr_sys = unbr.group(1).split(" and ")
    assert set(unbr_sys) <= set(MRK)
    train_tag = i5[train[0]]["label"].split(": ", 1)[1]
    assert all(i5[h]["label"] == i5[train[0]]["label"] for h in train)
    bands = []
    for grp, hosts in (("training", train), ("m21", valid)):
        for h in hosts:
            for bk, bv in i5[h]["bands"].items():
                sy = bk.split("_", 1)[1]
                bands.append({"group": grp, "host": h, "band": bk, "system": sy, "item1p": False,
                              "dft_maximum_unbracketed": grp == "m21" and sy in unbr_sys,
                              "label": i5[h]["label"], "Ea_dft_rawF_meV": bv["raw"]["Ea_dft_meV"],
                              **{f"{a}_signed_Ea_error_rawF_meV": bv["raw"][f"abs_Ea_error_{a}_meV"] for a in ARMS},
                              "Ea_dft_Eprime_meV_beside": bv["Eprime"]["Ea_dft_meV"],
                              **{f"{a}_signed_Ea_error_Eprime_meV_beside": bv["Eprime"][f"abs_Ea_error_{a}_meV"] for a in ARMS}})
    for bk, bv in rep["abs_Ea_16_test_bands"].items():
        h = bk.split("_")[0]
        assert h in crit_hosts + item1p_hosts
        bands.append({"group": "test", "host": h, "band": bk, "system": bk.split("_", 1)[1], "item1p": h in item1p_hosts,
                      "dft_maximum_unbracketed": False,
                      "label": "test host (held out)", "Ea_dft_rawF_meV": bv["raw"]["Ea_dft_meV"],
                      **{f"{a}_signed_Ea_error_rawF_meV": bv["raw"][f"abs_Ea_error_{a}_meV"] for a in ARMS},
                      "Ea_dft_Eprime_meV_beside": bv["Eprime"]["Ea_dft_meV"],
                      **{f"{a}_signed_Ea_error_Eprime_meV_beside": bv["Eprime"][f"abs_Ea_error_{a}_meV"] for a in ARMS}})
    for x in bands:      # model E_a is basis-free, so the two bases differ by the DFT shift alone
        sh = x["Ea_dft_Eprime_meV_beside"] - x["Ea_dft_rawF_meV"]
        for a in ARMS:
            assert abs(x[f"{a}_signed_Ea_error_rawF_meV"] - x[f"{a}_signed_Ea_error_Eprime_meV_beside"] - sh) < 1e-6
    above = sorted(x["band"] for x in bands if x["item1p"] and x["zeroshot_signed_Ea_error_rawF_meV"] > thr_cov)
    assert above == sorted(cov["bands"]), (above, cov["bands"])
    write_csv(f"{NAME}_e_bands.csv", bands)

    out.update(hero=hero, verdict=verdict, n_improve=n_imp, crit6=crit6, crit_pairs=crit_pairs, hosts_txt=hosts_txt,
               pairs=pairs, rms=rms, thr_b=thr_b, changes=changes, sites=sites, thr_c=thr_c, bands=bands,
               train=train, train_tag=train_tag, item1p_hosts=item1p_hosts, eb_host=eb_host,
               adoption_c_label=ad["c"]["label"], thr_cov=thr_cov, n_above=len(cov["bands"]),
               m21_head=m21_head, m21_p1=m21_p1, m21_p2=m21_p2, unbr_sys=unbr_sys)
    return out


def plot(D):
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle
    from matplotlib.transforms import ScaledTranslation, blended_transform_factory
    sys.path.insert(0, os.path.expanduser("~/.claude/skills/nature-figure/scripts"))
    try:      # layout QA from the nature-figure toolkit; optional, it does not touch the data
        from audit_panel_alignment import require_matplotlib_panel_alignment
    except ImportError:
        require_matplotlib_panel_alignment = None
        print("note: panel-alignment audit unavailable; figure rendered without it")
    mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                         "svg.fonttype": "none", "pdf.fonttype": 42, "font.size": 7.5,   # 7.5: sub/superscripts stay >= 5 pt
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
    a = fig.add_subplot(gs[0, 0:2]); b = fig.add_subplot(gs[0, 2])
    c = fig.add_subplot(gs[1, 0]); d = fig.add_subplot(gs[1, 1]); e = fig.add_subplot(gs[1, 2])
    fits = []        # (text artist, axes, right-edge limit in axes fraction) checked after the draw
    LIM_GUTTER = 1.0 + (G_MM / 25.4 * 72 - LAB_DX - 3) / W_PT    # a one-column panel's text stops 3 pt short of the next letter

    def heading(ax, title, sub, limit=LIM_GUTTER):
        s = ax.annotate(sub, (0, 1), xycoords="axes fraction", xytext=(0, 3), textcoords="offset points",
                        fontsize=6.3, color=SOFT, ha="left", va="bottom")
        t = ax.annotate(title, (0, 1), xycoords="axes fraction", xytext=(0, 12), textcoords="offset points",
                        fontsize=7.5, color=INK, ha="left", va="bottom")
        fits.extend([(s, ax, limit), (t, ax, limit)])

    def marker(ax, x, y, arm, mk, filled=True, s=20, z=3, dx_pt=0.0):
        col = FT_C if arm == "finetuned" else ZS_C
        tr = ax.transData + ScaledTranslation(dx_pt / 72, 0, fig.dpi_scale_trans)     # dodge in points, data x kept
        ax.scatter(x, y, s=s, marker=mk, facecolor=col if filled else "white", edgecolor=col, linewidth=0.8, zorder=z,
                   transform=tr)

    # ---------------- (a) criterion 6, the hero --------------------------------------------------------
    H, verdict = D["hero"], D["verdict"]
    ratios = [h["ft"] / h["zs"] for h in H] + [h["rft"] / h["rzs"] for h in H]
    lo, hi = 10 ** (math.log10(min(ratios)) - 0.25), 10 ** (math.log10(max(ratios)) + 0.15)
    f0, f1 = 0.37, 0.655                                        # forest column, axes fraction
    dpf = (math.log10(hi) - math.log10(lo)) / (f1 - f0)
    a.set_xscale("log")
    a.set_xlim(10 ** (math.log10(lo) - f0 * dpf), 10 ** (math.log10(hi) + (1 - f1) * dpf))
    ys = [3.3 - 1.1 * k for k in range(len(H))]
    RY = (0.17, -0.14, -0.46)                                   # statistic, decisive set, reported line
    y_bot, y_top = ys[-1] - 0.62, ys[0] + 0.40
    a.set_ylim(y_bot - 0.03, y_top + 0.62)
    bt = blended_transform_factory(a.transAxes, a.transData)
    a.add_patch(Rectangle((lo, y_bot), 1 - lo, y_top - y_bot, facecolor=GAIN_FILL, lw=0, zorder=0))
    a.plot([1, 1], [y_bot, y_top], color="#4d4d4d", lw=0.6, zorder=1)
    a.text(0.93, y_top + 0.2, "fine-tuned lower", ha="right", va="center", fontsize=6, color=SOFT)
    a.text(1.075, y_top + 0.2, "higher", ha="left", va="center", fontsize=6, color=SOFT)
    cols = (0.705, 0.815, 0.93)
    for x, t in zip(cols, ("Zero-shot", "Fine-tuned", "Strictly\nbelow?")):
        a.text(x, y_top + 0.24, t, transform=bt, ha="center", va="center", fontsize=6.3, color=INK, linespacing=1.0)
    for y, h in zip(ys, H):
        r, rr = h["ft"] / h["zs"], h["rft"] / h["rzs"]
        a.text(0, y + RY[0], h["stat"], transform=bt, ha="left", va="center", fontsize=7.5, color=INK)
        a.text(0, y + RY[1], h["set"], transform=bt, ha="left", va="center", fontsize=6.3, color=INK)
        fits.append((a.text(0, y + RY[2], h["rdesc"], transform=bt, ha="left", va="center", fontsize=6, color=SOFT),
                     a, f0 - 0.01))
        a.plot([1, r], [y, y], color=FT_C, lw=1.2, zorder=2, solid_capstyle="butt")
        marker(a, 1, y, "zeroshot", "o", s=24)
        marker(a, r, y, "finetuned", "o", s=30, z=4)
        a.plot([rr], [y + RY[2]], ls="none", marker="D", ms=3.4, mfc=FT_C, mec="white", mew=0.4, zorder=4)
        a.text(cols[0], y, fmt(h["zs"], h["nd"]), transform=bt, ha="center", va="center", fontsize=6.5)
        a.text(cols[1], y, fmt(h["ft"], h["nd"]), transform=bt, ha="center", va="center", fontsize=6.5)
        a.text(cols[2], y, "yes" if h["below"] else "no", transform=bt, ha="center", va="center", fontsize=6.5,
               fontweight="normal" if h["below"] else "bold")
        a.text(cols[0], y + RY[2], fmt(h["rzs"], h["nd"]), transform=bt, ha="center", va="center", fontsize=6, color=SOFT)
        a.text(cols[1], y + RY[2], fmt(h["rft"], h["nd"]), transform=bt, ha="center", va="center", fontsize=6, color=SOFT)
        fits.append((a.text(cols[2], y + RY[2], h["rstat"], transform=bt, ha="center", va="center", fontsize=6,
                            color=SOFT), a, 1.0))
    a.spines["left"].set_visible(False); a.set_yticks([])
    a.spines["bottom"].set_bounds(lo, hi)
    ticks = [t for t in (0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10) if lo <= t <= hi]
    a.set_xticks(ticks, [f"{t:g}" for t in ticks])
    a.xaxis.set_minor_locator(mpl.ticker.NullLocator())
    a.annotate("Fine-tuned ÷ zero-shot", ((f0 + f1) / 2, 0), xycoords="axes fraction", xytext=(0, -13),
               textcoords="offset points", ha="center", va="top", fontsize=7.5)
    a.legend(handles=[Line2D([], [], ls="none", marker="o", ms=4.5, mfc=FT_C, mec=FT_C),
                      Line2D([], [], ls="none", marker="D", ms=3.4, mfc=FT_C, mec="white", mew=0.4)],
             labels=["Pre-registered (decisive)", "Reported beside criterion 6\n(not in its verdict)"],
             loc="upper left", bbox_to_anchor=(0, 0), bbox_transform=a.transAxes, fontsize=6, handletextpad=0.4,
             borderaxespad=0.3, labelspacing=0.3)
    a.annotate(f"Outcome (item 4): {verdict['outcome']}\n"
               f"Adoption (a)–(c): {verdict['adoption_a']}\n"
               f"(d), (e): {verdict['adoption_d']}, not shown",
               (cols[0] - 0.045, 0), xycoords="axes fraction", xytext=(0, -4), textcoords="offset points",
               ha="left", va="top", fontsize=6, color=INK, linespacing=1.15)
    assert verdict["adoption_a"] == verdict["adoption_b"] == verdict["adoption_c"]
    assert verdict["adoption_d"] == verdict["adoption_e"]
    heading(a, f"Criterion 6 on the held-out hosts: {verdict['verdict']} (as amended by h: {verdict['verdict_h']})",
            f"Pre-registered: improvement only if all {len(H)} fine-tuned values are strictly below zero-shot",
            limit=1.0 + (G_MM / 25.4 * 72 - LAB_DX - 3) / ((2 * W_MM + G_MM) / 25.4 * 72))   # stops short of b's letter
    assert verdict["verdict_h_label"] == "criterion 6 as amended by h"

    # ---------------- (b) criterion 6 (ii) per pair, raw F and E' --------------------------------------
    C6, cp = D["crit6"], D["crit_pairs"]
    gx = {"raw F": 0.0, "E′": len(cp) + 0.8}
    hero_ii = {"raw F": next(h for h in H if h["key"] == "ii_raw"), "E′": next(h for h in H if h["key"] == "ii_Eprime")}
    yv = [r_[f"{a_}_error_meV"] for r_ in C6 for a_ in ARMS]
    ylo, yhi = math.floor(min(yv) / 20) * 20 - 10, math.ceil(max(yv) / 20) * 20 + 30
    b.axhline(0, color="#4d4d4d", lw=0.5, zorder=1)
    tks, tkl = [], []
    for basis, x0 in gx.items():
        for k, p in enumerate(cp):
            r_ = next(q for q in C6 if q["pair"] == p and q["basis"] == basis)
            x = x0 + k
            b.plot([x - 0.17, x + 0.17], [r_["zeroshot_error_meV"], r_["finetuned_error_meV"]], color="#c6ccd2", lw=0.6, zorder=2)
            marker(b, x - 0.17, r_["zeroshot_error_meV"], "zeroshot", MRK[r_["dopant"]], s=20)
            marker(b, x + 0.17, r_["finetuned_error_meV"], "finetuned", MRK[r_["dopant"]], s=20, z=4)
            tks.append(x); tkl.append(tidy(p).replace(" ", "\n"))
        hh = hero_ii[basis]
        b.text(x0 + (len(cp) - 1) / 2, yhi - 4, f"{basis}\nRMS {fmt(hh['zs'])} → {fmt(hh['ft'])}", ha="center", va="top",
               fontsize=6, color=SOFT, linespacing=1.15)
    b.set_xlim(-0.6, gx["E′"] + len(cp) - 0.4); b.set_ylim(ylo, yhi)
    b.set_xticks(tks, tkl, fontsize=6)
    b.tick_params(axis="x", length=0)
    b.set_ylabel("ΔE$_a$ error, model − DFT (meV)")
    nlarger = {bs: sum(q["finetuned_abs_error_larger"] for q in C6 if q["basis"] == bs) for bs in gx}
    nl_txt = (f"{nlarger['raw F']} of {len(cp)} per basis" if nlarger["raw F"] == nlarger["E′"]
              else f"{nlarger['raw F']} (raw F), {nlarger['E′']} (E′) of {len(cp)}")
    heading(b, f"(ii) per pair: {len(cp)} {D['hosts_txt']} pairs",
            f"Pre-registered; |error| up in {nl_txt}", limit=1.0 + R_MM / W_MM * 0.9)

    # ---------------- (c) adoption (b): paired dE_a on E' ---------------------------------------------
    P = D["pairs"]
    C_DODGE = {"zeroshot": -1.8, "finetuned": 1.8}   # pt; the two models of a pair sit either side of the DFT x (m32 Sr: 2 meV apart)
    allv = [p[k] for p in P for k in ("dEa_dft_Eprime_meV", "zeroshot_dEa_model_meV", "finetuned_dEa_model_meV")]
    L = math.ceil(max(abs(v) for v in allv) / 25) * 25 + 10
    for x0, w in ((-L, L - CLASS_BOUND), (-CLASS_BOUND, 2 * CLASS_BOUND), (CLASS_BOUND, L - CLASS_BOUND)):
        c.add_patch(Rectangle((x0, x0), w, w, facecolor=BAND_FILL, lw=0, zorder=0))
    c.plot([-L, L], [-L, L], color="#4d4d4d", lw=0.6, ls=(0, (3, 2)), zorder=1)
    for p in P:
        x, filled = p["dEa_dft_Eprime_meV"], p["set"].startswith("criterion")
        c.plot([x, x], [p["zeroshot_dEa_model_meV"], p["finetuned_dEa_model_meV"]], color="#c6ccd2", lw=0.7, zorder=2)
        for arm in ARMS:
            marker(c, x, p[f"{arm}_dEa_model_meV"], arm, MRK[p["dopant"]], filled=filled, s=18, dx_pt=C_DODGE[arm])
    labelled = {}
    for arm in ARMS:
        for name in D["changes"][arm]:
            p = next(q for q in P if q["pair"] == name)
            c.scatter(p["dEa_dft_Eprime_meV"], p[f"{arm}_dEa_model_meV"], s=75, facecolor="none", edgecolor=INK,
                      linewidth=0.6, zorder=5, transform=c.transData + ScaledTranslation(C_DODGE[arm] / 72, 0, fig.dpi_scale_trans))
            labelled.setdefault(name, []).append(p[f"{arm}_dEa_model_meV"])
    for name, yv_ in labelled.items():
        p = next(q for q in P if q["pair"] == name)
        c.annotate(tidy(name), (p["dEa_dft_Eprime_meV"], float(np.mean(yv_))), xytext=(C_DODGE["finetuned"] + 7.5, 0),
                   textcoords="offset points", ha="left", va="center", fontsize=6)     # clear of the dodged ring
    c.text(-0.96 * L, 0.96 * L, f"Shaded: same class as DFT\n(±{fmt(CLASS_BOUND, 1)} meV; amendment g)\n"
           "Circled: class differs from DFT", ha="left", va="top", fontsize=6, color=SOFT, linespacing=1.15)
    c.set_xlim(-L, L); c.set_ylim(-L, L)
    tk = [t for t in range(-100, 101, 50) if abs(t) < L]
    c.set_xticks(tk, [fmt(t, 0) for t in tk]); c.set_yticks(tk, [fmt(t, 0) for t in tk])
    c.set_xlabel("ΔE$_a$, DFT on E′ (meV)"); c.set_ylabel("ΔE$_a$, model (meV)")
    heading(c, f"Adoption (b), {len(P)} test pairs on E′: {D['verdict']['adoption_b']}",
            f"RMS {fmt(D['rms']['zeroshot'])} → {fmt(D['rms']['finetuned'])} meV; needs < {D['thr_b']:g} meV")

    # ---------------- (d) adoption (c): far-referenced E_b at the 5 m30 sites ------------------------
    S, thr = D["sites"], D["thr_c"]
    for i, s in enumerate(S):
        dft = s["Eb_dft_farref_rawF_meV"]
        d.add_patch(Rectangle((i - 0.3, dft - thr), 0.6, 2 * thr, facecolor=BAND_FILL, lw=0, zorder=0))
        d.plot([i - 0.3, i + 0.3], [dft, dft], color=DFT_C, lw=1.2, zorder=3, solid_capstyle="butt")
        for arm, dx in (("zeroshot", -0.13), ("finetuned", 0.13)):
            y = s[f"{arm}_Eb_model_farref_meV"]
            d.plot([i + dx, i + dx], [dft, y], color=FT_C if arm == "finetuned" else ZS_C, lw=0.8, zorder=2)
            marker(d, i + dx, y, arm, MRK[s["dopant"]], s=20, z=4)
            if s["near"] and not s[f"{arm}_sign_agree"]:
                d.scatter(i + dx, y, s=75, facecolor="none", edgecolor=INK, linewidth=0.6, zorder=5)
    d.axhline(0, color="#4d4d4d", lw=0.5, zorder=1)
    for i, s in enumerate(S):            # signed error printed above the site wherever it is outside the band
        for arm, dx in (("zeroshot", -0.13), ("finetuned", 0.13)):
            if abs(s[f"{arm}_error_meV"]) >= thr:
                d.annotate(f"{fmt(s[f'{arm}_error_meV'], 0, signed=True)} meV", (i + dx, s["Eb_dft_farref_rawF_meV"] + thr),
                           xytext=(0, 2.5), textcoords="offset points", ha="center", va="bottom", fontsize=6,
                           color=FT_C if arm == "finetuned" else SOFT)
    d.set_xlim(-0.6, len(S) - 0.4)
    yl = [s[k] for s in S for k in ("Eb_dft_farref_rawF_meV", "zeroshot_Eb_model_farref_meV", "finetuned_Eb_model_farref_meV")]
    d.set_ylim(math.floor((min(yl) - thr) / 20) * 20, math.ceil((max(yl) + thr) / 20) * 20 + 20)
    d.text(len(S) - 0.45, d.get_ylim()[1], f"Band: DFT ± {thr:g} meV\nValue: error outside band\nCircled: first-shell sign\ndiffers from DFT",
           ha="right", va="top", fontsize=6, color=SOFT, linespacing=1.15)
    d.set_xticks(range(len(S)), [f"{tidy(s['name'])}\n{s['site']}" for s in S], fontsize=6)
    d.tick_params(axis="x", length=0)
    d.set_ylabel("E$_b$ − E$_b$(far), raw F (meV)")
    mf = max(abs(s["finetuned_error_meV"]) for s in S)
    heading(d, f"Adoption (c), {D['adoption_c_label']}",
            f"{D['verdict']['adoption_c'].capitalize()}; fine-tuned max |error| {fmt(mf, 0)} meV")

    # ---------------- (e) signed absolute E_a error, raw F (reported, not gated) -------------------------
    Bd = D["bands"]
    groups = [("training", f"Training\n({D['train_tag']})"),
              ("m21", D["m21_head"].replace(" (", "\n(", 1)),
              ("test", "Test\n(held out)")]
    yv = [x[f"{a_}_signed_Ea_error_rawF_meV"] for x in Bd for a_ in ARMS]
    e_lo, e_hi = math.floor(min(yv) / 25) * 25 - 5, math.ceil(max(yv) / 25) * 25 + 5
    ppy = W_PT / (e_hi - e_lo)                     # points per meV; the x axis of e is in points
    offs, half = {}, {}
    for g, _ in groups:                            # swarm each (group, model) column; its half-width in points
        mem = [x for x in Bd if x["group"] == g]
        for arm in ARMS:
            o = swarm([x[f"{arm}_signed_Ea_error_rawF_meV"] * ppy for x in mem], E_DMIN, E_DMIN / 4)
            offs[(g, arm)] = dict(zip((x["band"] for x in mem), o))
            half[(g, arm)] = max(abs(v) for v in o) + E_DMIN / 2
    WG = {"pad": 0.5, "inner": 1.0, "group": 2.5}                          # relative widths of the gaps
    unit = (W_PT - 2 * sum(half.values())) / (2 * WG["pad"] + len(groups) * WG["inner"] + (len(groups) - 1) * WG["group"])
    assert unit >= 2.0, unit                       # every column fits with at least 2 pt between neighbours
    cur, centre, gcentre = WG["pad"] * unit, {}, {}
    for gi, (g, _) in enumerate(groups):
        cur += WG["group"] * unit if gi else 0.0
        centre[(g, "zeroshot")] = cur + half[(g, "zeroshot")]
        cur += 2 * half[(g, "zeroshot")] + WG["inner"] * unit
        centre[(g, "finetuned")] = cur + half[(g, "finetuned")]
        cur += 2 * half[(g, "finetuned")]
        gcentre[g] = (centre[(g, "zeroshot")] + centre[(g, "finetuned")]) / 2
    assert abs(cur + WG["pad"] * unit - W_PT) < 1e-6
    print(f"e: swarm columns fit with {unit:.1f} pt per gap unit")
    pos = {(b_, arm): centre[(g, arm)] + o for (g, arm), od in offs.items() for b_, o in od.items()}
    for x in Bd:
        yz, yf = x["zeroshot_signed_Ea_error_rawF_meV"], x["finetuned_signed_Ea_error_rawF_meV"]
        xz, xf = pos[(x["band"], "zeroshot")], pos[(x["band"], "finetuned")]
        e.plot([xz, xf], [yz, yf], color="#d3d8dd", lw=0.45, zorder=1)
        marker(e, xz, yz, "zeroshot", MRK[x["system"]], filled=not x["item1p"], s=E_S)
        marker(e, xf, yf, "finetuned", MRK[x["system"]], filled=not x["item1p"], s=E_S)
        if x["dft_maximum_unbracketed"]:
            for xx, yy in ((xz, yz), (xf, yf)):
                e.annotate("†", (xx, yy), xytext=(0, 2.4), textcoords="offset points", ha="center", va="bottom",
                           fontsize=6.5, color=INK)
    e.axhline(0, color="#4d4d4d", lw=0.5, zorder=0)
    e.axhline(D["thr_cov"], color="#4d4d4d", lw=0.6, ls=(0, (1, 1.5)), zorder=0)
    above = "none" if D["n_above"] == 0 else f"{D['n_above']} bands"
    e.text(W_PT - 1, e_hi - 2, f"Dotted: item-5\ntrigger, +{D['thr_cov']:g} meV;\nitem-1′ zero-shot\nabove it: {above}",
           ha="right", va="top", fontsize=6, color=SOFT, linespacing=1.15)
    note = textwrap.fill(f"{D['m21_head']}: {D['m21_p1']}; † {D['m21_p2']}", 46)       # from reported.item5.m21.label
    fits.append((e.annotate(note, (0, 0), xycoords="axes fraction", xytext=(0, -31), textcoords="offset points",
                            ha="left", va="top", fontsize=6, color=SOFT, linespacing=1.15), e, 1.0 + R_MM / W_MM * 0.9))
    e.set_xlim(0, W_PT); e.set_ylim(e_lo, e_hi)
    cnt = {g: sum(x["group"] == g for x in Bd) for g, _ in groups}
    e.set_xticks([gcentre[g] for g, _ in groups], [f"{lab}\n{cnt[g]} bands" for g, lab in groups], fontsize=6)
    e.tick_params(axis="x", length=0)
    e.set_ylabel("E$_a$ error, model − DFT, raw F (meV)")
    heading(e, "Absolute barrier error, raw F",
            "Reported, not gated; signed, per band", limit=1.0 + R_MM / W_MM * 0.9)

    # ---------------- shared key, panel letters, QA, export -------------------------------------------
    k_zs = Line2D([], [], ls="none", marker="o", ms=4, mfc=ZS_C, mec=ZS_C, label="Zero-shot MACE-MP-0")
    k_ft = Line2D([], [], ls="none", marker="o", ms=4, mfc=FT_C, mec=FT_C, label="Fine-tuned (WP3)")
    k_dft = Line2D([], [], color=DFT_C, lw=1.2, label="DFT (PBE)")
    k_open = Line2D([], [], ls="none", marker="o", ms=4, mfc="white", mec=FT_C, mew=0.8,
                    label="Open (c, e): item-1′ hosts (" + ", ".join(D["item1p_hosts"]) + ")")
    k_shape = Line2D([], [], ls="none", label="Shape (b–e):")
    k_ga, k_sr, k_un = (Line2D([], [], ls="none", marker=MRK[s_], ms=4 if s_ != "Sr" else 3.8, mfc="white", mec=INK, mew=0.8,
                               label=lab_) for s_, lab_ in (("GA", "GA"), ("Sr", "Sr"), ("undoped", "Undoped (e)")))
    key = [k_zs, k_shape, k_ft, k_ga, k_dft, k_sr, k_open, k_un]      # filled column by column: two rows
    leg = fig.legend(handles=key, loc="upper center", bbox_to_anchor=(0.5, 1 - 0.6 / FIG_H_MM), ncol=4,
                     fontsize=6.5, handletextpad=0.3, columnspacing=1.6, borderaxespad=0, labelspacing=0.35)
    leg.legend_handles[1].set_visible(False)
    for lab, ax in zip("abcde", (a, b, c, d, e)):
        t = ax.transAxes + ScaledTranslation(-LAB_DX / 72, LAB_DY / 72, fig.dpi_scale_trans)
        ax.text(0, 1, lab, transform=t, fontsize=8, fontweight="bold", ha="left", va="bottom")
    out = os.path.join(HERE, NAME)
    fig.canvas.draw()
    rnd = fig.canvas.get_renderer()
    for art, ax, lim in fits:          # text that must stay inside its slot (axes fraction of its own axes)
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
    with open(EVAL) as fh:
        plot(collect(json.load(fh)))

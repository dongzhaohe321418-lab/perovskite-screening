#!/usr/bin/env python
"""Figure WP3 diagnostic D3 (post hoc, reported only; a pre-specified description, no verdict): in which atom
group the fine-tuned model books its change of S = E(i*) - E(0), relative to the zero-shot model, along a
densified band path (totals 0 -> i*; no breakdown along the path), in a work gauge and a site-energy gauge.

Figure contract (written before plotting; revised after the adversarial check of 2026-11-03)
  Results-level question. WP3_DIAGNOSTICS_D3_PLAN.md (ddb352b) section 2 names five places where D3's
    information lies. The figure draws (i)-(iv) of them: (i) group contributions in meV with error estimates
    once the quadrature is resolved, (ii) their comparison with how the zero-shot barrier work is distributed,
    (iii) the comparison with a second, path-free gauge (site energies), (iv) the size of the path dependence
    (P against C). (v), the seen coarse D2b values against their converged values (section 7 item 5), is not
    drawn; it is in the JSON and the write-up. Plan section 9 fixes the four panels below.
  What the figure shows (a description; plan section 7 forbids a verdict). The n = 8 quadrature resolves all 37
    bands on the band path P; on the chord path C, 6 bands are not resolved. Per group, the work change dW_g along
    P is drawn beside the zero-shot group work W_ZS,g, against the site-energy change d_eps_g, and against dW_g
    along C. The statements printed are the plan's own (the counts, the section-7 sign comparison of the two
    gauges from JSON summaries.overall.sign_comparison, the per-band count of groups whose signs agree, the
    item-4 path-dependence summary, the item-3 median displacement share and the item-7 closure summary); the
    numbers printed beside them that are not plan summaries are listed under Data. No binary verdict wording of
    the kinds plan section 7 rules out, and no shares of a signed sum.
  How to read it (plan sections 1 and 2; for the caption).
    - D3 is not independent of D2b: it shares the models, the image forces, the groups and the segment, so
      agreement with the coarse D2b picture is weak evidence.
    - A large dW_g for the hopping I and inorganic < 6 A taken together is expected anyway: together they
      carry a median 0.84 of sum |dr|^2 (hopping I alone 0.78, printed under the group names in b; inorganic
      < 6 A 0.065). These displacement shares were known before D3 (plan section 2). On its own this does not
      show what fine-tuning changed in the model.
    - D3 describes where the fine-tuned model books its change relative to the zero-shot model. It says
      nothing about whether that change moves the model towards DFT (reason 7's named test, a line integral
      of the model - DFT force residual, is not run).
  What would change it. A different JSON (its sha256 is asserted), a band whose P is not resolved (asserted
    absent), or a recomputed summary that differs from the JSON's (asserted equal).
  Evidence chain (one role per panel).
    a  Prerequisite (D3a, plan section 6 criterion 1). |closure8| against |closure4| of the total path work for
       every band, model and path (P, C; to i*): 37 x 2 x 2 = 148 points; all 148 closures (n = 8 and n = 4)
       are negative (asserted; printed). Reference lines: |closure8| = |closure4|/4 (the h^2 trapezoid
       expectation), the ratio window [2, 8] of criterion 1 as a light band, the 2 meV bound on |closure8| and
       the 0.5 meV level below which the ratio test is exempt. The small table in a gives, per path, the item-7
       median closure4/closure8 (both models print the same value; asserted) and the largest |closure8| (the
       larger of the two models' item-7 maxima). The 4 points above 2 meV are all fine-tuned closures on C
       (m12_undoped, m12_Sr, m27_undoped, m27_Sr; printed as a count with model and path); the largest on P is
       0.74 meV.
    b  Primary description (D3b, plan section 7 items 1 and 3). dW_g (Richardson, P) of the 37 resolved bands per
       group, with error bars of the conservative error |X8 - X4| (the plan's error of statements), beside the
       zero-shot group work W_ZS,g (Richardson, P; same error bars); short ink ticks are the means over the 37
       bands (recomputed here and asserted equal to item 1 and item 3 of the JSON). Under each group name: the
       item-3 median displacement share D_g (recomputed from the per-band D_g and asserted equal).
    c  Second gauge (D3c, plan section 7 item 2 and the sign comparison). dW_g (Richardson, P) against d_eps_g per
       band and group (185 points); large markers are the group means (labelled directly) with crosshair bars of
       +- the plan's sign margin (work: max(2 meV, 2 SE) + mean |dW8 - dW4|; site energy: max(2 meV, 2 SE)).
       The bars are a threshold, not a confidence interval. The legend carries the plan's statement per group
       and, in brackets, |mean| - margin for the work and the site-energy gauge (a sign is stated only when
       both are positive). This clearance is printed because the bars cannot show it at the final scale: the
       smallest positive clearance (organic < 6 A, work, 0.7 meV) is 0.5 pt. The subtitle gives the plan's
       per-band count of groups whose two gauges have the same raw sign (no margin).
    d  Sensitivity (plan section 7 item 4). dW_g on P against dW_g on C (both Richardson) for the 31 bands in
       which both paths are resolved (155 points), with y = x. The 6 bands whose C is not resolved (m12_undoped,
       m12_Sr, m27_undoped, m27_Sr, m30_undoped, m30_Sr) are not drawn; their values are in the JSON and in the
       d CSV (drawn = False). The in-panel text gives item 4: per group the mean |P - C| (range over groups), the
       largest |P - C| with its group and band, and beside it the mean of e(P) + e(C) (range over groups).
  Encoding. Each group has one colour and one marker shape, the same in b, c and d. Colour (Okabe-Ito hues):
    hopping I reddish purple; inorganic atoms blue (< 6 A dark blue, >= 6 A sky blue); organic molecules orange
    (< 6 A vermillion, >= 6 A orange). Near and far share a hue family and differ in lightness because near/far
    is one ordered attribute of the same atom class. Shape by atom class: hopping I diamond, inorganic circle,
    organic square (equal filled area). Colour is not the only code: the five group means of c are labelled
    directly, and the two groups whose CIELAB lightness nearly coincides (inorganic >= 6 A, L* 69.8, and organic
    >= 6 A, 70.6) differ in shape. palette_check() computes, and asserts, the smallest CIEDE2000 difference
    between two group colours: 22.2 without simulation, 12.2 (hopping I / inorganic < 6 A) under protanopia,
    12.5 (the organic pair) under deuteranopia and 10.9 (hopping I / organic >= 6 A) under tritanopia
    (Machado et al. 2009, full severity, applied in linear sRGB; D65). a uses the house model colours instead
    (zero-shot warm grey, fine-tuned teal, as fig_wp3_criterion6 and fig_wp3_diagnostics) with path by fill (P
    filled, C open), keyed in the small table inside a; neither colour is in the group palette. The two models'
    closures nearly coincide, so the zero-shot markers are drawn larger and below the fine-tuned ones (size
    encodes nothing else) and all 148 points stay visible. The zero-shot work W_ZS,g in b is drawn filled in
    the same warm grey: it is the zero-shot model's quantity on path P, which is exactly what a filled
    warm-grey marker means in a; open markers occur only in a and mean path C. The single group legend sits in
    c; b names the groups on its axis; d refers to c. Strip positions in b are a fixed golden-ratio jitter (no
    random numbers, not band order).
  Axes. a: log-log with the same length per decade on both axes (|closure8| 0.1-10 meV; the |closure4| range
    starts at 0.4 meV and is computed from the plot-area aspect, asserted after the draw), so the ratio-4 line
    is the 45-degree diagonal through the lower-left corner. b: groups as rows, work as a shared linear x axis
    (dW_g and W_ZS,g in the same meV units: W_ZS of the hopping I reaches about 320 meV, so dW_g is compressed
    in b and read at higher resolution in c and d). c: the same meV-per-mm scale on both axes (computed from the
    panel size), so the wider spread of d_eps_g than of dW_g is not an artefact of the axes; only zero lines
    are drawn. A y = x line is deliberately omitted in c: the plan (section 4, D3c) calls the site energy a
    different gauge, the model's own partition and not unique physically, and its statement (section 7) is a
    sign comparison only; a diagonal would suggest that the two gauges should agree. d: identical x and y
    limits on a square plot area, so y = x is the 45-degree diagonal.
  Archetype. Quantitative grid, 2 x 3 columns: a (1 column) + b (2 columns) on top, c (2 columns) + d (1 column)
    below; the outer columns are equal (a, d) so that d is square.
  Backend. Python / matplotlib only.
  Export. 183 mm double column; every PDF glyph >= 5 pt; editable text (pdf.fonttype 42, svg.fonttype none);
    mathtext set in Arial, upright, subscripts only in 7.5 pt text; pdf, svg, png and tiff (600 dpi); the PDF
    carries no creation date and the SVG no date and a fixed id salt, so a rerun on the same input is
    byte-identical; source data source_data/fig_wp3_d3_*.csv; QA: render-time alignment gate (1.5 pt, strict,
    panel labels required; the figure is not exported if the gate cannot be imported), validate_figure.py,
    audit_pdf_text.py (5 pt) and audit_figure_collisions.py on the exported PDF.

Statistics. Every point is one deterministic quantity of one band (a quadrature of single points of two fixed
models); there are no replicates or tests. The error estimate of a work quantity X is e = |X8 - X4|/3 (the
asymptotic error of the n = 8 trapezoid value; an estimate, not a bound); statements and the bars of b use the
conservative |X8 - X4| around the Richardson value X_R = X8 + (X8 - X4)/3. In b every bar is shorter than the
half-width of its (filled, edgeless) marker along the bar, so the bars are drawn but lie inside the markers:
the largest, 2.7 meV (W_ZS of the hopping I in m20_GA), against 3.3 meV for a diamond at b's scale; on the
circles and squares (2.6 and 2.3 meV) the largest bar is 0.28 meV. The count is computed at render time and
printed in b's subtitle. In c and d no bars are drawn: there every |X8 - X4| of a plotted dW_g (P: at most
0.65 meV; C, drawn bands: at most 1.22 meV) is shorter than the smallest marker half-width at the final scale
(asserted at render time), and d_eps_g has no quadrature error. Means are over 37 bands that are not independent (14 hosts,
up to 3 systems per host; 18 training, 3 m21, 16 test bands); SE = sample SD (ddof 1)/sqrt(n), as the JSON and
the plan's band-level rule. The organic < 6 A "agree" clears its work margin by 0.7 meV only; with 14 hosts
behind the 37 bands, the band-level SE is the plan's choice, not a host-level one. The site-energy partition
is the model's own (MACE per-atom 'energies') and is not unique physically; the two gauges come from the same
two models and are not independent checks of each other.

Data. Every plotted and printed number is read at plot time from ../wp3/diagnostics/d3_dense_path.json (written
by scripts/45_wp3_d3_dense_path.py; the JSON sha256, its recorded script_sha256 and the sha256 of the script
file on disk are asserted). Per-band values are cross-checked between their two JSON locations (comparators and
D3a/D3b blocks; the criterion-1 closure8 and flags of both paths against the D3a totals and the plan's 2 meV,
0.5 meV and [2, 8] constants). Recomputed here from the plotted values and asserted equal to the JSON
summaries: the item-7 medians and maxima, the means of b (items 1 and 3), the item-3 median D_g, the means,
SEs, margins and statements of c, the per-band sign-agreement counts and histogram, and item 4 (mean and
largest |P - C|, mean e(P) + e(C)). Printed numbers that are not plan summaries (additions, computed here from
the same values): the sign of all closures and the count, model and path of the closures above 2 meV (a); the
largest |X8 - X4| and the count of bars inside their markers (b); the clearance |mean| - margin per group and
gauge (c); the band of the largest |P - C| (d). Nothing is typed in.

Groups (plan section 5, D2's): defined at image 0 by minimum-image distance to the hop midpoint; "hopping I" is
the I with the largest 0 -> 6 displacement; "inorganic < 6 A" are the other inorganic atoms within 6 A;
organic groups are whole molecules by their C. dW_g = -int (F_FT - F_ZS)_g . dr along the path (fine-tuned
minus zero-shot); d_eps_g is the fine-tuned minus zero-shot change of the group's site energies between image
0 and i*, sum over g of {[eps^FT(i*) - eps^FT(0)] - [eps^ZS(i*) - eps^ZS(0)]}; W_ZS,g is the zero-shot group
work along P; D_g is the group's share of sum |dr|^2 along P (n = 8).

Backend. plot() selects Agg and measures the text-fit and clearance checks at the export resolution (600 dpi).

QA notes. Every plotted |closure| of the log axes of a is asserted positive and inside the limits in collect();
tick labels are plain numbers, not mathtext powers. Subscripts (mathtext) appear only in 7.5 pt text (titles and
axis labels); validate_figure.py's FONT-GLYPH-FLOOR WARN assumes a 6.3 pt parent for "$_g$", but
audit_pdf_text.py measures the smallest glyph in the PDF (5.25 pt). W_ZS,g is written W$_{ZS{,}g}$ so that
mathtext sets no space after the comma. The ratio-window fill and the ratio-4 line of a are computed inside the
axes limits, so no clipped geometry reaches the heading (the collision audit sees unclipped paths). Asserted
after the draw: the legend and the table of a lie outside the ratio window and off the two bound lines; the
legend of c ends left of the vertical zero line and holds no point; the direct labels of c and the text lines
of d hold no point (marker extent included), the labels and legend of c do not overlap, and the text of d lies
above y = x. b's three-line group labels use line spacing 1.15 (at 1.0 the "< 6 A" and "D =" lines overlapped
in the collision audit). The collision audit's 48 contained fill overlays are text inside the white axes
background (a: 13 legend and table texts, b: 3 legend texts, c: 6 legend texts and 5 labels, d: 8 text lines)
plus, for the 13 texts of a, the bounding box of a's ratio-window polygon, which the text does not reach
(asserted above); they are informational. With no finding, the audit writes no overlay PDF. validate_figure.py
also gives WARN LEGEND-LABEL-CASE for b's lower-case legend labels: lower-case legend entries are the house
style of the WP3 figures (fig_wp3_diagnostics, fig_wp3_criterion6) and of a and c here. d has no zero lines: a vertical zero line would cross its text, and y = x is
its reference. The panel axes are created in label order (a, b, c, d), so the ids of the alignment record are
the panel letters.

Review record (2026-11-03). First build, then one adversarial round with two lenses (numbers and plan
conformance, F1-F10; visual, statistical honesty and QA, V1-V10): 20 findings, none rated error; all accepted.
F1/V2: b's bar note read "<= 2.7 meV" (false by rounding) and counted bars against the fill radius of open
markers; it now prints "max 2.7 meV" and counts against the half-width of the filled marker along the bar
(inside in all 370). F2/V7: d prints item 4's "beside" quantity, the mean e(P) + e(C). F3: d_eps_g is defined as
the fine-tuned minus zero-shot change (docstring and c's x label). F4: the reason for omitting y = x in c no
longer credits the plan with a magnitude statement. F5: the printed additions are listed under Data, and a
prints the item-7 medians and maxima instead of a pooled ratio range. F6: the first sentence says "totals
0 -> i*" and the contract names (v) as not drawn. F7: the plan's reading guidance (not independent of D2b;
local dW expected from the displacement; nothing about DFT) is in the contract, and b prints the item-3 median
D_g. F8: the criterion-1 flags of every point are asserted against the plan constants, and the closure8
cross-check runs for C too. F9: this record. F10: the sha256 of the script file on disk is asserted. V1: c
prints |mean| - margin per group and gauge (legend; c_group_means CSV); the crosshair bars are drawn over the
mean markers, with caps, so every margin end is visible (chosen over shrinking the markers); the claim that the
crosshair alone shows the rule is dropped, and the narrow organic < 6 A clearance is noted under Statistics.
V3: the group means of c are labelled directly, each group has a shape (atom class) as well as a colour, and
palette_check() computes and asserts CIEDE2000 values (the earlier CIE76 values overstated the differences).
V4: W_ZS,g is drawn filled in warm grey (the meaning "zero-shot, P" that a's key gives it), so open markers
mean path C only (chosen over a shape code for path in a, because shape now codes atom class); c's legend glyph
for the means is grey-filled. V5: a states that all closures are negative and that the points above 2 meV are
all fine-tuned closures on C, and its table gives the largest |closure8| per path (P 0.74 meV). V6: c's subtitle
says the per-band count uses raw signs, in the form "5/4/3/2/1/0 ...: 5/17/8/6/1/0". V8: a has the same length
per decade on both axes and larger fine-tuned markers. V9: the alignment gate fails closed. V10: W_ZS,g's
subscript has no space after the comma; b's legend uses no symbol it does not subscript; the QA notes count the
contained overlays by panel; exports are byte-reproducible (checked by a rerun). Consequential changes: c's
legend has no title (the brackets are defined in c's subtitle, which now says "equal axis scales"); three
source-data files are added (a_item7, b_group_summary, d_item4). Kept: the house model colours, the strip layout
of b and the zero lines of c. The CVD simulation needs no extra package (numpy only).
"""
import csv, hashlib, itertools, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(HERE, "..", "wp3", "diagnostics", "d3_dense_path.json")
SCRIPT_FILE = os.path.join(HERE, "..", "..", "..", "..", "scripts", "45_wp3_d3_dense_path.py")
JSON_SHA256 = "559a67774ca507c9c7dc0ab66d991de990fe9fc0208b3aee74431606db677d09"
SCRIPT_SHA256 = "866f01f5c74b6c23db03f3aa654355cfc0e5a13b807f19814875672bb9eaa3a5"
PLAN_COMMIT = "ddb352b63513542df5082565dacfb494f0db5049"
SRC = os.path.join(HERE, "source_data")
NAME = "fig_wp3_d3"
GROUPS = ("hop_I", "inorganic_near", "inorganic_far", "organic_near", "organic_far")
GLAB = {"hop_I": "hopping I", "inorganic_near": "inorganic < 6 Å", "inorganic_far": "inorganic ≥ 6 Å",
        "organic_near": "organic < 6 Å", "organic_far": "organic ≥ 6 Å"}
GTICK = {"hop_I": "hopping I", "inorganic_near": "inorganic\n< 6 Å", "inorganic_far": "inorganic\n≥ 6 Å",
         "organic_near": "organic\n< 6 Å", "organic_far": "organic\n≥ 6 Å"}
GC = {"hop_I": "#CC79A7", "inorganic_near": "#0072B2", "inorganic_far": "#56B4E9",
      "organic_near": "#D55E00", "organic_far": "#E69F00"}             # Okabe-Ito
GMK = {"hop_I": "D", "inorganic_near": "o", "inorganic_far": "o", "organic_near": "s", "organic_far": "s"}
MK_AREA = {"o": 1.0, "s": math.pi / 4, "D": math.pi / 4}   # scatter-size factor: equal filled area to a circle
MODELS, PATHS = ("zeroshot", "finetuned"), ("P", "C")
ZS_C, FT_C, INK, SOFT = "#a48e72", "#0e7a72", "#1a1a1a", "#555555"   # house colours
REF_C, BOUND_C, WIN_FILL, ZERO_C, SEP_C = "#8a8a8a", "#6a6a6a", "#ececec", "#c8c8c8", "#e4e4e4"
MEAN_GLYPH = "#9a9a9a"                    # c: neutral fill of the legend glyph for the group means
CLOSURE_BOUND, RATIO_EXEMPT, RATIO_WIN = 2.0, 0.5, (2.0, 8.0)      # plan section 6, criterion 1
MINUS = "−"
FIG_WIDTH_MM = 183
L_MM, R_MM, G_MM = 15.0, 3.0, 20.0        # left / right margin, column gutter
W_SIDE_MM = 46.0                          # outer columns (a, d); the middle column takes the rest
T_MM, V_MM, B_MM = 14.0, 24.0, 12.5       # top margin, row gap, bottom margin
H_TOP_MM, H_BOT_MM = 50.0, W_SIDE_MM      # row heights (d square)
LAB_DX, LAB_DY = 30.0, 20.5               # panel letter: fixed point offset from the plot-area corner
SUB_LINE = 7.8                            # subtitle line pitch (pt)
YA = (0.1, 10.0)                          # a: |closure8|, two decades
XA = (0.4, 0.4 * 10 ** (math.log10(YA[1] / YA[0]) * W_SIDE_MM / H_TOP_MM))   # a: same length per decade
B_DY, B_JIT = 0.2, 0.2                    # b: strip offset from the group row and jitter width (row units)
S_B, S_CD = 9.0, 7.0                      # marker areas of a circle (pt^2); other shapes scaled by MK_AREA
S_A_ZS, S_A_FT = 22.0, 9.0                # a: zero-shot drawn larger and below fine-tuned (coincident points)
MS_MEAN, MEAN_EW = 4.2, 0.6               # c: group-mean marker size (pt, circle) and edge width
# c: direct labels of the group means, (x, y) in data units (meV) and alignment; leaders run to the means
CLAB = {"hop_I": (96.0, -58.0, "left"), "inorganic_near": (-127.0, -57.0, "left"),
        "inorganic_far": (100.0, -30.0, "left"), "organic_near": (-40.0, -72.0, "right"),
        "organic_far": (30.0, 47.0, "left")}
# Full-severity CVD simulation matrices (Machado, Oliveira and Fernandes 2009), applied in linear sRGB
MACHADO = {"protanopia": [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216],
                          [-0.003882, -0.048116, 1.051998]],
           "deuteranopia": [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413],
                            [-0.011820, 0.042940, 0.968881]],
           "tritanopia": [[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602],
                          [0.004733, 0.691367, 0.303900]]}
CVD_MIN_DE00 = {"none": (22.2, {"organic_near", "organic_far"}),        # quoted in the docstring
                "protanopia": (12.2, {"hop_I", "inorganic_near"}),
                "deuteranopia": (12.5, {"organic_near", "organic_far"}),
                "tritanopia": (10.9, {"hop_I", "organic_far"})}


def fmt(x, nd=1, signed=False):
    s = f"{x:+.{nd}f}" if signed else f"{x:.{nd}f}"
    return s.replace("-", MINUS)


def write_csv(fn, rows):
    with open(os.path.join(SRC, fn), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def golden(n, width):
    """Fixed golden-ratio offsets in [-width/2, width/2): deterministic, decorrelated from band order."""
    return ((np.arange(n) * 0.6180339887) % 1.0 - 0.5) * width


def sha256_file(fn):
    with open(fn, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _lab(hexcol, sim=None):
    """CIELAB (D65) of an sRGB colour, optionally after a CVD simulation in linear sRGB."""
    c = np.array([int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    if sim is not None:
        lin = np.clip(np.array(MACHADO[sim]) @ lin, 0, 1)
    xyz = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750],
                    [0.0193339, 0.1191920, 0.9503041]]) @ lin / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def _de2000(l1, l2):
    """CIEDE2000 colour difference (Sharma, Wu and Dalal 2005)."""
    (L1, a1, b1), (L2, a2, b2) = l1, l2
    cb = (math.hypot(a1, b1) + math.hypot(a2, b2)) / 2
    g = 0.5 * (1 - math.sqrt(cb ** 7 / (cb ** 7 + 25 ** 7)))
    a1p, a2p = (1 + g) * a1, (1 + g) * a2
    c1p, c2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p, h2p = math.degrees(math.atan2(b1, a1p)) % 360, math.degrees(math.atan2(b2, a2p)) % 360
    dh = 0.0 if c1p * c2p == 0 else (h2p - h1p + 180) % 360 - 180
    dHp = 2 * math.sqrt(c1p * c2p) * math.sin(math.radians(dh / 2))
    lbp, cbp = (L1 + L2) / 2, (c1p + c2p) / 2
    if c1p * c2p == 0:
        hbp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbp = (h1p + h2p) / 2
    else:
        hbp = (h1p + h2p + 360) / 2 if h1p + h2p < 360 else (h1p + h2p - 360) / 2
    t = (1 - 0.17 * math.cos(math.radians(hbp - 30)) + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6)) - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    rt = (-math.sin(math.radians(60 * math.exp(-((hbp - 275) / 25) ** 2)))
          * 2 * math.sqrt(cbp ** 7 / (cbp ** 7 + 25 ** 7)))
    sl = 1 + 0.015 * (lbp - 50) ** 2 / math.sqrt(20 + (lbp - 50) ** 2)
    sc, sh = 1 + 0.045 * cbp, 1 + 0.015 * cbp * t
    return math.sqrt(((L2 - L1) / sl) ** 2 + ((c2p - c1p) / sc) ** 2 + (dHp / sh) ** 2
                     + rt * (c2p - c1p) / sc * dHp / sh)


def palette_check():
    """Group palette: the smallest CIEDE2000 difference per vision condition equals the docstring's value (and
    pair); groups whose lightness nearly coincides (|dL*| < 5, greyscale) differ in marker shape."""
    for sim, (val, pair) in CVD_MIN_DE00.items():
        d, a, b = min((_de2000(_lab(GC[a], None if sim == "none" else sim), _lab(GC[b], None if sim == "none"
                                                                                  else sim)), a, b)
                      for a, b in itertools.combinations(GROUPS, 2))
        assert round(d, 1) == val and {a, b} == pair, (sim, d, a, b)
    for a, b in itertools.combinations(GROUPS, 2):
        if abs(_lab(GC[a])[0] - _lab(GC[b])[0]) < 5:
            assert GMK[a] != GMK[b], (a, b)


def sign_rule(dw, deps, a84):
    """Plan section 7 sign comparison as the JSON implements it (SE ddof 1; 'exceed' strict)."""
    n = len(dw)
    mw, me = float(np.mean(dw)), float(np.mean(deps))
    sw, se = float(np.std(dw, ddof=1) / math.sqrt(n)), float(np.std(deps, ddof=1) / math.sqrt(n))
    mw84 = float(np.mean(a84))
    marg_w, marg_e = max(2.0, 2 * sw) + mw84, max(2.0, 2 * se)
    if abs(mw) > marg_w and abs(me) > marg_e:
        st = "agree" if np.sign(mw) == np.sign(me) else "disagree"
    else:
        st = "sign not resolved"
    return {"mean_dW_meV": mw, "se_dW_meV": sw, "mean_abs_8_minus_4_meV": mw84, "margin_dW_meV": marg_w,
            "mean_d_eps_meV": me, "se_d_eps_meV": se, "margin_d_eps_meV": marg_e, "statement": st}


def collect():
    """Read and cross-check everything the figure shows; write the source-data CSVs."""
    raw = open(JSON_FILE, "rb").read()
    assert hashlib.sha256(raw).hexdigest() == JSON_SHA256, "d3_dense_path.json differs from the recorded run"
    J = json.loads(raw)
    assert J["script_sha256"] == SCRIPT_SHA256 and J["plan_file"]["commit"] == PLAN_COMMIT
    assert sha256_file(SCRIPT_FILE) == SCRIPT_SHA256, "scripts/45_wp3_d3_dense_path.py differs from the recorded run"
    assert J["development_subset"] is None and J["part"] == "D3"
    B, S = J["bands"], J["summaries"]
    bands = list(B)
    nb = len(bands)
    assert nb == 37 and S["n_bands"] == nb and S["n_resolved"] == nb and S["overall"]["label"] is None
    assert all(B[bn]["status"] == "resolved" and B[bn]["failed_criteria"] == [] for bn in bands)
    assert S["overall"]["bands"] == bands
    meta = {bn: {"band": bn, "split": B[bn]["split_name"], "host": B[bn]["host"], "system": B[bn]["system"]}
            for bn in bands}

    # ---- (a) total closures, n = 8 and n = 4, per band, model and path ----------------------------------------
    rows_a, A = [], {(p, m): {"c4": [], "c8": []} for p in PATHS for m in MODELS}
    for bn in bands:
        b = B[bn]
        for p in PATHS:
            st = b["status"] if p == "P" else b["status_C"]
            fc = b["failed_criteria"] if p == "P" else b["failed_criteria_C"]
            for m in MODELS:
                t = b["paths"][p]["D3a"][m]["total"]
                c4, c8 = t["closure_meV"]["4"], t["closure_meV"]["8"]
                assert abs(c4 / c8 - t["closure4_over_closure8"]) < 1e-9
                cr = b["paths"][p]["criteria"]["values"]["1"][m]                   # criterion 1, both paths
                assert abs(cr["closure8_meV"] - c8) < 1e-12 and abs(cr["closure4_over_closure8"] - c4 / c8) < 1e-9
                exempt = abs(c8) < RATIO_EXEMPT
                assert cr["abs_closure8_le_2"] == (abs(c8) <= CLOSURE_BOUND)
                assert cr["ratio_exempt_abs_closure8_lt_0p5"] == exempt
                assert cr["ratio_in_2_8_or_exempt"] == (exempt or RATIO_WIN[0] <= c4 / c8 <= RATIO_WIN[1])
                A[(p, m)]["c4"].append(c4); A[(p, m)]["c8"].append(c8)
                rows_a.append({**meta[bn], "path": p, "model": m, "closure8_meV": c8, "closure4_meV": c4,
                               "abs_closure8_meV": abs(c8), "abs_closure4_meV": abs(c4),
                               "closure4_over_closure8": c4 / c8, "abs_closure8_le_2": cr["abs_closure8_le_2"],
                               "ratio_exempt": exempt, "ratio_in_2_8_or_exempt": cr["ratio_in_2_8_or_exempt"],
                               "path_status": st, "path_failed_criteria": "; ".join(fc)})
    write_csv("fig_wp3_d3_a_closures.csv", rows_a)
    allc4 = np.array([r["closure4_meV"] for r in rows_a]); allc8 = np.array([r["closure8_meV"] for r in rows_a])
    assert len(rows_a) == 148
    n_neg = int(np.sum((allc4 < 0) & (allc8 < 0)))
    a4, a8 = np.abs(allc4), np.abs(allc8)
    assert a4.min() > 0 and a8.min() > 0                                                 # a: log axes
    assert XA[0] < a4.min() and a4.max() < XA[1] and YA[0] < a8.min() and a8.max() < YA[1]
    rows_as, a_tab = [], {}
    for p in PATHS:                                                                   # plan section 7 item 7
        for m in MODELS:
            it7 = S["overall"]["item7_D3a"][p][m]
            v = np.abs(A[(p, m)]["c8"])
            med_r = float(np.median(np.array(A[(p, m)]["c4"]) / np.array(A[(p, m)]["c8"])))
            assert abs(np.median(v) - it7["median_abs_closure8_meV"]) < 1e-12
            assert abs(v.max() - it7["max_abs_closure8_meV"]) < 1e-12
            assert abs(med_r - it7["median_closure4_over_closure8"]) < 1e-12
            rows_as.append({"path": p, "model": m, "n": len(v), "median_abs_closure8_meV": float(np.median(v)),
                            "max_abs_closure8_meV": float(v.max()), "median_closure4_over_closure8": med_r})
        meds = {fmt(r["median_closure4_over_closure8"], 2) for r in rows_as if r["path"] == p}
        assert len(meds) == 1, meds                                      # both models print the same median
        a_tab[p] = {"median_ratio": meds.pop(),
                    "max_abs_c8": max(r["max_abs_closure8_meV"] for r in rows_as if r["path"] == p)}
    write_csv("fig_wp3_d3_a_item7.csv", rows_as)
    over = [r for r in rows_a if r["abs_closure8_meV"] > CLOSURE_BOUND]
    assert all(r["path"] == "C" and r["path_status"] == "not resolved" for r in over)
    over_mp = sorted({(r["model"], r["path"]) for r in over})
    c_fail = [bn for bn in bands if B[bn]["status_C"] != "resolved"]
    assert len(c_fail) == S["n_resolved_with_C_not_resolved"] == 6
    assert sorted(r["band"] for r in over) == sorted(bn for bn in c_fail
                                                     if any(f.startswith("1 ") for f in B[bn]["failed_criteria_C"]))

    # ---- (b) dW_g and W_ZS,g on P, D_g; (c) d_eps_g ----------------------------------------------------------
    rows_b, rows_c = [], []
    V = {g: {k: [] for k in ("dW", "dW84", "WZS", "WZS84", "deps", "D")} for g in GROUPS}
    for bn in bands:
        b = B[bn]
        Pb = b["paths"]["P"]
        assert set(Pb["D3b"]["dW"]) == set(GROUPS) | {"total"} and set(b["D3c"]["d_eps_meV"]) == set(GROUPS)
        for g in GROUPS:
            dw, wz, cp = Pb["D3b"]["dW"][g], Pb["D3a"]["zeroshot"]["groups"][g], Pb["D3b"]["comparators"][g]
            assert abs(cp["dW"]["richardson"] - dw["richardson"]) < 1e-12
            assert abs(cp["W_ZS"]["richardson"] - wz["richardson"]) < 1e-12
            assert abs(dw["richardson"] - (dw["n8"] + (dw["n8"] - dw["n4"]) / 3)) < 1e-9
            assert abs(dw["abs_8_minus_4"] - abs(dw["n8"] - dw["n4"])) < 1e-12
            assert abs(Pb["criteria"]["values"]["2"][g]["abs_8_minus_4_meV"] - dw["abs_8_minus_4"]) < 1e-12
            de = b["D3c"]["d_eps_meV"][g]
            V[g]["dW"].append(dw["richardson"]); V[g]["dW84"].append(dw["abs_8_minus_4"])
            V[g]["WZS"].append(wz["richardson"]); V[g]["WZS84"].append(wz["abs_8_minus_4"])
            V[g]["deps"].append(de); V[g]["D"].append(cp["D"])
            rows_b.append({**meta[bn], "group": g, "dW_richardson_meV": dw["richardson"],
                           "dW_abs_8_minus_4_meV": dw["abs_8_minus_4"], "dW_n8_meV": dw["n8"], "dW_n4_meV": dw["n4"],
                           "W_ZS_richardson_meV": wz["richardson"], "W_ZS_abs_8_minus_4_meV": wz["abs_8_minus_4"],
                           "W_ZS_n8_meV": wz["n8"], "W_ZS_n4_meV": wz["n4"], "D_g": cp["D"]})
            rows_c.append({**meta[bn], "group": g, "d_eps_meV": de, "dW_richardson_P_meV": dw["richardson"],
                           "dW_abs_8_minus_4_meV": dw["abs_8_minus_4"],
                           "same_sign": bool(np.sign(dw["richardson"]) == np.sign(de))})
        assert abs(sum(b["D3c"]["d_eps_meV"].values()) - b["dS_meV"]) < 1e-6
    write_csv("fig_wp3_d3_b_group_work.csv", rows_b)
    write_csv("fig_wp3_d3_c_gauges.csv", rows_c)
    V = {g: {k: np.array(v) for k, v in d.items()} for g, d in V.items()}
    it1, it2, it3 = S["overall"]["item1_dW"], S["overall"]["item2_d_eps"], S["overall"]["item3_comparators"]
    sign, rows_bs, rows_cm, Dmed = {}, [], [], {}
    for g in GROUPS:                                       # every plotted mean and statement = the JSON's
        assert it1[g]["n"] == nb and abs(V[g]["dW"].mean() - it1[g]["mean"]) < 1e-9
        assert abs(V[g]["dW84"].mean() - it1[g]["mean_abs_8_minus_4"]) < 1e-12
        assert abs(V[g]["deps"].mean() - it2[g]["mean"]) < 1e-9
        assert abs(V[g]["WZS"].mean() - it3[g]["W_ZS"]["mean"]) < 1e-9
        assert abs(V[g]["WZS84"].mean() - it3[g]["W_ZS"]["mean_abs_8_minus_4"]) < 1e-12
        Dmed[g] = float(np.median(V[g]["D"]))
        assert abs(Dmed[g] - it3[g]["median_D"]) < 1e-12
        rows_bs.append({"group": g, "n_bands": nb, "mean_dW_richardson_meV": V[g]["dW"].mean(),
                        "mean_W_ZS_richardson_meV": V[g]["WZS"].mean(), "median_D_g": Dmed[g],
                        "max_dW_abs_8_minus_4_meV": V[g]["dW84"].max(),
                        "max_W_ZS_abs_8_minus_4_meV": V[g]["WZS84"].max()})
        sign[g] = sign_rule(V[g]["dW"], V[g]["deps"], V[g]["dW84"])
        js = S["overall"]["sign_comparison"][g]
        for k, v in sign[g].items():
            assert (v == js[k]) if k == "statement" else abs(v - js[k]) < 1e-9, (g, k, v, js[k])
        cw = abs(sign[g]["mean_dW_meV"]) - sign[g]["margin_dW_meV"]
        ce = abs(sign[g]["mean_d_eps_meV"]) - sign[g]["margin_d_eps_meV"]
        assert (cw > 0 and ce > 0) == (sign[g]["statement"] != "sign not resolved")
        sign[g].update({"clearance_dW_meV": cw, "clearance_d_eps_meV": ce})
        rows_cm.append({"group": g, "n_bands": nb, **sign[g]})
    write_csv("fig_wp3_d3_b_group_summary.csv", rows_bs)
    write_csv("fig_wp3_d3_c_group_means.csv", rows_cm)
    agree = {bn: sum(int(np.sign(V[g]["dW"][i]) == np.sign(V[g]["deps"][i])) for g in GROUPS)
             for i, bn in enumerate(bands)}
    assert agree == S["overall"]["per_band_groups_sign_agree"]["counts"]
    hist = {str(k): sum(v == k for v in agree.values()) for k in range(len(GROUPS) + 1)}
    assert hist == S["overall"]["per_band_groups_sign_agree"]["histogram"]

    # ---- (d) path dependence, P against C ----------------------------------------------------------------------
    it4 = S["overall"]["item4_path_dependence"]
    both = [bn for bn in bands if B[bn]["status_C"] == "resolved"]
    assert both == it4["bands"] and len(both) == it4["n_both_resolved"] == nb - len(c_fail)
    rows_d, Dd = [], {g: {"P": [], "C": [], "band": [], "e_P": [], "e_C": []} for g in GROUPS}
    for bn in bands:
        b = B[bn]
        for g in GROUPS:
            wp, wc = b["paths"]["P"]["D3b"]["dW"][g], b["paths"]["C"]["D3b"]["dW"][g]
            assert abs(b["paths"]["C"]["D3b"]["comparators"][g]["dW"]["richardson"] - wc["richardson"]) < 1e-12
            assert abs(wp["e"] - wp["abs_8_minus_4"] / 3) < 1e-12 and abs(wc["e"] - wc["abs_8_minus_4"] / 3) < 1e-12
            drawn = bn in both
            if drawn:
                Dd[g]["P"].append(wp["richardson"]); Dd[g]["C"].append(wc["richardson"]); Dd[g]["band"].append(bn)
                Dd[g]["e_P"].append(wp["e"]); Dd[g]["e_C"].append(wc["e"])
            rows_d.append({**meta[bn], "group": g, "status_C": b["status_C"],
                           "failed_criteria_C": "; ".join(b["failed_criteria_C"]), "drawn": drawn,
                           "dW_richardson_P_meV": wp["richardson"], "dW_richardson_C_meV": wc["richardson"],
                           "P_minus_C_meV": wp["richardson"] - wc["richardson"],
                           "dW_abs_8_minus_4_P_meV": wp["abs_8_minus_4"],
                           "dW_abs_8_minus_4_C_meV": wc["abs_8_minus_4"], "e_P_meV": wp["e"], "e_C_meV": wc["e"]})
    write_csv("fig_wp3_d3_d_path_dependence.csv", rows_d)
    pc, rows_ds = {}, []
    for g in GROUPS:
        d = np.abs(np.array(Dd[g]["P"]) - np.array(Dd[g]["C"]))
        ee = np.array(Dd[g]["e_P"]) + np.array(Dd[g]["e_C"])
        assert abs(d.mean() - it4[g]["mean_abs_diff_meV"]) < 1e-9 and abs(d.max() - it4[g]["max_abs_diff_meV"]) < 1e-9
        assert abs(ee.mean() - it4[g]["mean_e_P_plus_e_C_meV"]) < 1e-12
        pc[g] = {"mean": float(d.mean()), "max": float(d.max()), "band": Dd[g]["band"][int(np.argmax(d))],
                 "mean_e": float(ee.mean())}
        rows_ds.append({"group": g, "n_bands_both_resolved": len(d), "mean_abs_P_minus_C_meV": pc[g]["mean"],
                        "max_abs_P_minus_C_meV": pc[g]["max"], "band_of_max": pc[g]["band"],
                        "mean_e_P_plus_e_C_meV": pc[g]["mean_e"]})
    write_csv("fig_wp3_d3_d_item4.csv", rows_ds)
    gmax = max(GROUPS, key=lambda g: pc[g]["max"])
    return {"bands": bands, "nb": nb, "A": A, "a_tab": a_tab, "n_neg": n_neg, "n_over": len(over),
            "over_mp": over_mp, "c_fail": c_fail, "V": V, "Dmed": Dmed, "sign": sign,
            "hist": hist, "Dd": Dd, "pc": pc, "gmax": gmax, "n_both": len(both)}


def load_alignment_gate():
    """The nature-figure render-time alignment gate; fail closed (nothing is exported without it)."""
    sys.path.insert(0, os.path.expanduser("~/.claude/skills/nature-figure/scripts"))
    try:
        from audit_panel_alignment import require_matplotlib_panel_alignment
    except ImportError as exc:
        raise SystemExit(f"panel-alignment gate unavailable ({exc}); nothing exported")
    return require_matplotlib_panel_alignment


def plot(D):
    import matplotlib as mpl
    mpl.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.legend_handler import HandlerTuple
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from matplotlib.ticker import FixedLocator, FuncFormatter, LogLocator, NullFormatter
    from matplotlib.transforms import ScaledTranslation
    mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                         "svg.fonttype": "none", "pdf.fonttype": 42, "font.size": 7.5, "svg.hashsalt": NAME,
                         "mathtext.fontset": "custom", "mathtext.rm": "Arial", "mathtext.it": "Arial",
                         "mathtext.bf": "Arial:bold", "mathtext.cal": "Arial", "mathtext.sf": "Arial",
                         "mathtext.default": "regular",
                         "axes.labelsize": 7.5, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
                         "axes.spines.right": False, "axes.spines.top": False, "axes.linewidth": 0.8,
                         "legend.frameon": False, "xtick.major.width": 0.8, "ytick.major.width": 0.8,
                         "xtick.major.size": 2.5, "ytick.major.size": 2.5,
                         "xtick.minor.width": 0.6, "ytick.minor.width": 0.6,
                         "xtick.minor.size": 1.5, "ytick.minor.size": 1.5})
    W_MID_MM = FIG_WIDTH_MM - L_MM - R_MM - 2 * G_MM - 2 * W_SIDE_MM
    W_WIDE_MM = W_MID_MM + G_MM + W_SIDE_MM
    FIG_H_MM = T_MM + H_TOP_MM + V_MM + H_BOT_MM + B_MM
    PT = 72 / 25.4
    fig = plt.figure(figsize=(FIG_WIDTH_MM / 25.4, FIG_H_MM / 25.4))
    w_avg, h_avg = (2 * W_SIDE_MM + W_MID_MM) / 3, (H_TOP_MM + H_BOT_MM) / 2
    gs = fig.add_gridspec(2, 3, left=L_MM / FIG_WIDTH_MM, right=1 - R_MM / FIG_WIDTH_MM, bottom=B_MM / FIG_H_MM,
                          top=1 - T_MM / FIG_H_MM, wspace=G_MM / w_avg, hspace=V_MM / h_avg,
                          width_ratios=[W_SIDE_MM, W_MID_MM, W_SIDE_MM], height_ratios=[H_TOP_MM, H_BOT_MM])
    a = fig.add_subplot(gs[0, 0]); b = fig.add_subplot(gs[0, 1:3])                    # label order a, b, c, d
    c = fig.add_subplot(gs[1, 0:2]); d = fig.add_subplot(gs[1, 2])
    fits, checks = [], []           # text-fit limits; post-draw clearance checks (callables of the renderer)
    LIM_G = lambda w_mm: 1.0 + (G_MM * PT - LAB_DX - 3) / (w_mm * PT)      # before the next panel's letter
    LIM_R = lambda w_mm: 1.0 + (R_MM * PT - 2) / (w_mm * PT)               # the figure edge

    def heading(ax, title, sub1, sub2, limit):
        for k, s in enumerate((sub2, sub1)):
            t = ax.annotate(s, (0, 1), xycoords="axes fraction", xytext=(0, 3 + k * SUB_LINE),
                            textcoords="offset points", fontsize=6.3, color=SOFT, ha="left", va="bottom")
            fits.append((t, ax, limit))
        t = ax.annotate(title, (0, 1), xycoords="axes fraction", xytext=(0, 4.5 + 2 * SUB_LINE),
                        textcoords="offset points", fontsize=7.5, color=INK, ha="left", va="bottom")
        fits.append((t, ax, limit))

    def log_ticks(ax_axis, lims):
        ax_axis.set_major_locator(FixedLocator([v for v in (0.1, 1, 10) if lims[0] <= v <= lims[1]]))
        ax_axis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
        ax_axis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10)))
        ax_axis.set_minor_formatter(NullFormatter())

    def s_of(g, s):
        return s * MK_AREA[GMK[g]]

    def half_x_pt(g, s):
        """Half-extent (pt) of group g's filled marker along x: circle r, square half-side, diamond half-diagonal."""
        side = math.sqrt(s_of(g, s))
        return {"o": side / 2, "s": side / 2, "D": side / math.sqrt(2)}[GMK[g]]

    def extent(art, rnd):
        """Rendered box of a text (an annotation's text only, without its leader) or a legend."""
        return mpl.text.Text.get_window_extent(art, rnd) if isinstance(art, mpl.text.Text) else \
            art.get_window_extent(rnd)

    def data_bbox(ax, art, rnd):
        """Rendered extent of a text or legend in ax's data coordinates: (x0, y0, x1, y1)."""
        (x0, y0), (x1, y1) = ax.transData.inverted().transform(extent(art, rnd).get_points())
        return x0, y0, x1, y1

    def clear_of_points(ax, art, X, Y, pad_pt, what):
        """Post-draw check: no data point (marker extent pad_pt) inside the rendered box of art."""
        def chk(rnd):
            bb = extent(art, rnd)
            xy = ax.transData.transform(np.column_stack([X, Y]))
            pad = pad_pt * fig.dpi / 72
            inside = ((xy[:, 0] > bb.x0 - pad) & (xy[:, 0] < bb.x1 + pad) &
                      (xy[:, 1] > bb.y0 - pad) & (xy[:, 1] < bb.y1 + pad))
            assert not inside.any(), (what, np.column_stack([X, Y])[inside][:3])
        checks.append(chk)

    nb = D["nb"]
    jit = golden(nb, B_JIT)
    V = D["V"]

    # ---------------- (a) quadrature closure, 8 against 4 steps per segment --------------------------------------
    a.set_xscale("log"); a.set_yscale("log")
    xx = np.geomspace(XA[0], XA[1], 400)          # reference geometry kept inside the axes (no clipped overhang)
    a.fill_between(xx, np.clip(xx / RATIO_WIN[1], *YA), np.clip(xx / RATIO_WIN[0], *YA), color=WIN_FILL, lw=0,
                   zorder=0)
    x4 = np.geomspace(4 * YA[0], XA[1], 400)
    a.plot(x4, x4 / 4, color=REF_C, lw=0.7, zorder=1)
    a.axhline(CLOSURE_BOUND, color=BOUND_C, lw=0.7, ls=(0, (3, 2)), zorder=1)
    a.axhline(RATIO_EXEMPT, color=BOUND_C, lw=0.7, ls=(0, (1, 1.5)), zorder=1)
    MC = {"zeroshot": ZS_C, "finetuned": FT_C}
    MS = {"zeroshot": S_A_ZS, "finetuned": S_A_FT}      # zero-shot larger, so coincident points stay visible
    for p in PATHS:
        for m in MODELS:
            x, y = np.abs(D["A"][(p, m)]["c4"]), np.abs(D["A"][(p, m)]["c8"])
            z = (3 if p == "P" else 2) + (0.5 if m == "finetuned" else 0)
            if p == "P":
                a.scatter(x, y, s=MS[m], color=MC[m], linewidths=0, zorder=z)
            else:
                a.scatter(x, y, s=MS[m], facecolor="none", edgecolor=MC[m], linewidths=0.6, zorder=z)
    a.set_xlim(*XA); a.set_ylim(*YA)
    log_ticks(a.xaxis, XA); log_ticks(a.yaxis, YA)
    a.set_xlabel("|closure4| (meV)")
    a.set_ylabel("|closure8| (meV)")
    leg_a = a.legend(handles=[Line2D([], [], color=BOUND_C, lw=0.7, ls=(0, (1, 1.5)), label="0.5 meV: ratio exempt"),
                              Line2D([], [], color=BOUND_C, lw=0.7, ls=(0, (3, 2)), label="2 meV bound"),
                              Line2D([], [], color=REF_C, lw=0.7, label="ratio 4 (h²)"),
                              Patch(facecolor=WIN_FILL, edgecolor="none", label="ratio 2 to 8")],
                     loc="upper left", fontsize=6.3, handlelength=1.6, handleheight=0.6, handletextpad=0.4,
                     borderaxespad=0.2, labelspacing=0.3, title="ratio: closure4/closure8", title_fontsize=6.3,
                     alignment="left")
    # model x path key with the item-7 summary per path: a small table in the empty lower right
    kx_lab, kx_col, k_row = 0.69, (0.80, 0.925), 0.062
    ky = [0.04 + k_row * i for i in range(5)][::-1]            # header, zero-shot, fine-tuned, median, max
    tab_txt = []
    for j, p in enumerate(PATHS):
        tab_txt.append(a.text(kx_col[j], ky[0], p, transform=a.transAxes, fontsize=6.3, color=SOFT, ha="center",
                              va="center"))
    for i, (m, lab) in enumerate((("zeroshot", "zero-shot"), ("finetuned", "fine-tuned"))):
        yk = ky[1 + i]
        tab_txt.append(a.text(kx_lab, yk, lab, transform=a.transAxes, fontsize=6.3, color=SOFT, ha="right",
                              va="center"))
        a.scatter([kx_col[0]], [yk], s=MS[m], color=MC[m], linewidths=0, transform=a.transAxes, zorder=3,
                  clip_on=False)
        a.scatter([kx_col[1]], [yk], s=MS[m], facecolor="none", edgecolor=MC[m], linewidths=0.6,
                  transform=a.transAxes, zorder=3, clip_on=False)
    for i, (lab, key, nd) in enumerate((("median ratio", "median_ratio", None), ("max |closure8|", "max_abs_c8", 2))):
        yk = ky[3 + i]
        tab_txt.append(a.text(kx_lab, yk, lab, transform=a.transAxes, fontsize=6.3, color=SOFT, ha="right",
                              va="center"))
        for j, p in enumerate(PATHS):
            v = D["a_tab"][p][key]
            tab_txt.append(a.text(kx_col[j], yk, v if nd is None else fmt(v, nd), transform=a.transAxes,
                                  fontsize=6.3, color=SOFT, ha="center", va="center"))
    allx_a = np.concatenate([np.abs(D["A"][k]["c4"]) for k in D["A"]])
    ally_a = np.concatenate([np.abs(D["A"][k]["c8"]) for k in D["A"]])

    def a_outside_window(art, side):
        """Post-draw check: art lies wholly on one side of the ratio window and off the two bound lines."""
        def chk(rnd):
            x0, y0, x1, y1 = data_bbox(a, art, rnd)
            r = [x / y for x in (x0, x1) for y in (y0, y1)]
            assert (min(r) > RATIO_WIN[1]) if side == "below" else (max(r) < RATIO_WIN[0]), (art, r)
            for yl in (CLOSURE_BOUND, RATIO_EXEMPT):
                assert not (y0 < yl < y1), (art, yl)
        checks.append(chk)
    for t in leg_a.get_texts() + [leg_a.get_title()]:            # each legend line, not the legend's box
        a_outside_window(t, "above")
    for t in tab_txt:
        a_outside_window(t, "below")
    clear_of_points(a, leg_a, allx_a, ally_a, math.sqrt(S_A_ZS) / 2, "a legend")
    for t in tab_txt:
        clear_of_points(a, t, allx_a, ally_a, math.sqrt(S_A_ZS) / 2, "a table")
    sign_note = "all < 0" if D["n_neg"] == 4 * nb else f"{D['n_neg']} < 0"
    over_note = (f"|closure8| > 2 meV: {D['n_over']} points, all fine-tuned on C"
                 if D["over_mp"] == [("finetuned", "C")] else f"|closure8| > 2 meV: {D['n_over']} points")
    heading(a, "Path-work closure at 8 and 4 steps", f"{nb} bands × 2 models × 2 paths (n = {4 * nb}), {sign_note}",
            over_note, LIM_G(W_SIDE_MM))

    # ---------------- (b) dW_g beside W_ZS,g along P -------------------------------------------------------------
    b.axvline(0, color=ZERO_C, lw=0.6, zorder=1)
    for k in range(1, len(GROUPS)):
        b.axhline(k - 0.5, color=SEP_C, lw=0.5, zorder=0)
    for k, g in enumerate(GROUPS):
        yw, yz = k - B_DY + jit, k + B_DY + jit
        b.errorbar(V[g]["dW"], yw, xerr=V[g]["dW84"], fmt="none", ecolor=GC[g], elinewidth=0.6, capsize=0, zorder=2)
        b.scatter(V[g]["dW"], yw, s=s_of(g, S_B), marker=GMK[g], color=GC[g], linewidths=0, zorder=3)
        b.errorbar(V[g]["WZS"], yz, xerr=V[g]["WZS84"], fmt="none", ecolor=ZS_C, elinewidth=0.6, capsize=0, zorder=2)
        b.scatter(V[g]["WZS"], yz, s=s_of(g, S_B), marker=GMK[g], color=ZS_C, linewidths=0, zorder=3)
        for xm, yc in ((V[g]["dW"].mean(), k - B_DY), (V[g]["WZS"].mean(), k + B_DY)):
            b.plot([xm, xm], [yc - 0.17, yc + 0.17], color=INK, lw=1.0, zorder=4, solid_capstyle="butt")
    b.set_ylim(len(GROUPS) - 0.5, -0.5)
    b.set_yticks(range(len(GROUPS)))
    b.set_yticklabels([f"{GTICK[g]}\nD = {fmt(D['Dmed'][g], 2)}" for g in GROUPS], linespacing=1.15)
    b.tick_params(axis="y", length=0, pad=3)
    xb = (-150.0, 340.0)
    lo = min(min(V[g]["dW"].min(), V[g]["WZS"].min()) for g in GROUPS)
    hi = max(max(V[g]["dW"].max(), V[g]["WZS"].max()) for g in GROUPS)
    assert xb[0] < lo - 5 and hi + 5 < xb[1], (lo, hi)
    b.set_xlim(*xb)
    bt = [-100, 0, 100, 200, 300]
    b.set_xticks(bt); b.set_xticklabels([fmt(v, 0) for v in bt])
    b.set_xlabel("Work along P, Richardson value (meV)")
    h_dw = tuple(Line2D([], [], marker=GMK[g], color=GC[g], ls="none", markersize=math.sqrt(s_of(g, S_B)), mew=0)
                 for g in GROUPS)
    leg_b = b.legend(handles=[h_dw, Line2D([], [], marker="o", color=ZS_C, ls="none", markersize=3.0, mew=0),
                              Line2D([], [], marker="|", color=INK, ls="none", markersize=5, mew=1.0)],
                     labels=["fine-tuned − zero-shot work (colour: group)", "zero-shot work",
                             f"mean over the {nb} bands"],
                     handler_map={tuple: HandlerTuple(ndivide=None, pad=0.0)}, handlelength=3.2,
                     loc="lower right", fontsize=6.3, handletextpad=0.5, borderaxespad=0.3, labelspacing=0.35)
    pts_b = [(V[g][k], kk - sgn * B_DY + jit) for kk, g in enumerate(GROUPS)
             for k, sgn in (("dW", 1), ("WZS", -1))]
    clear_of_points(b, leg_b, np.concatenate([p[0] for p in pts_b]), np.concatenate([p[1] for p in pts_b]),
                    math.sqrt(S_B) / 2, "b legend")
    heading(b, "ΔW$_g$ per group along P, beside the zero-shot group work W$_{ZS{,}g}$",
            f"{nb} of {nb} bands resolved on P (n = {nb} per strip); groups by distance to the hop midpoint at image 0",
            "BARS", LIM_R(W_WIDE_MM))
    bars_note = fits[-3][0]                                                 # sub2: filled in below

    # ---------------- (c) the two gauges ---------------------------------------------------------------------------
    c.axhline(0, color=ZERO_C, lw=0.6, zorder=1); c.axvline(0, color=ZERO_C, lw=0.6, zorder=1)
    for g in GROUPS:
        c.scatter(V[g]["deps"], V[g]["dW"], s=s_of(g, S_CD), marker=GMK[g], color=GC[g], linewidths=0, alpha=0.9,
                  zorder=2)
    for g in GROUPS:
        sg = D["sign"][g]
        mx, my = sg["mean_d_eps_meV"], sg["mean_dW_meV"]
        c.plot([mx], [my], marker=GMK[g], ls="none", ms=MS_MEAN * math.sqrt(MK_AREA[GMK[g]]), mfc=GC[g], mec=INK,
               mew=MEAN_EW, zorder=5)
        c.errorbar([mx], [my], xerr=[sg["margin_d_eps_meV"]], yerr=[sg["margin_dW_meV"]], fmt="none", ecolor=INK,
                   elinewidth=0.6, capsize=1.3, capthick=0.6, zorder=6)
    xc = (-200.0, 170.0)
    w_c_mm = W_WIDE_MM
    span_y = (xc[1] - xc[0]) * H_BOT_MM / w_c_mm                             # the same meV per mm on both axes
    yc = (-80.0, -80.0 + span_y)
    allx = np.concatenate([V[g]["deps"] for g in GROUPS]); ally = np.concatenate([V[g]["dW"] for g in GROUPS])
    assert xc[0] + 5 < allx.min() and allx.max() < xc[1] - 5 and yc[0] + 5 < ally.min() and ally.max() < yc[1] - 5
    c.set_xlim(*xc); c.set_ylim(*yc)
    ct = [-200, -150, -100, -50, 0, 50, 100, 150]
    c.set_xticks(ct); c.set_xticklabels([fmt(v, 0) for v in ct])
    cy = [-50, 0, 50]
    c.set_yticks(cy); c.set_yticklabels([fmt(v, 0) for v in cy])
    c.set_xlabel("Δε$_g$ (fine-tuned − zero-shot), site-energy gauge (meV)")
    c.set_ylabel("ΔW$_g$, work along P (meV)")
    SAY = {"agree": "signs agree", "disagree": "signs disagree", "sign not resolved": "sign not resolved"}
    sg_lab = {g: f"{GLAB[g]}: {SAY[D['sign'][g]['statement']]} ({fmt(D['sign'][g]['clearance_dW_meV'])}, "
                 f"{fmt(D['sign'][g]['clearance_d_eps_meV'])})" for g in GROUPS}
    eh = c.errorbar([np.nan], [np.nan], xerr=[1.0], yerr=[1.0], fmt="o", ms=MS_MEAN, mfc=MEAN_GLYPH, mec=INK,
                    mew=MEAN_EW, ecolor=INK, elinewidth=0.6, capsize=1.3, capthick=0.6)
    leg_c = c.legend(handles=[Line2D([], [], marker=GMK[g], color=GC[g], ls="none",
                                     markersize=math.sqrt(s_of(g, S_CD)) * 1.2, mew=0) for g in GROUPS] + [eh],
                     labels=[sg_lab[g] for g in GROUPS] + ["group mean ± the plan's sign margin"],
                     loc="upper left", fontsize=6.3, handletextpad=0.4, borderaxespad=0.2, labelspacing=0.25)
    r_c = max(half_x_pt(g, S_CD) for g in GROUPS) * math.sqrt(2)        # a square's corner, conservatively
    clear_of_points(c, leg_c, allx, ally, r_c, "c legend")

    def c_left_of_zero(art):
        def chk(rnd):
            x1_px = extent(art, rnd).x1
            assert x1_px < c.transData.transform((0, 0))[0] - 2 * fig.dpi / 72, ("c legend reaches x = 0", art)
        checks.append(chk)
    c_left_of_zero(leg_c)
    c_labels = []
    for g in GROUPS:                                  # direct labels of the five means, with leaders
        sg = D["sign"][g]
        tx, ty, ha = CLAB[g]
        t = c.annotate(GLAB[g], (sg["mean_d_eps_meV"], sg["mean_dW_meV"]), xytext=(tx, ty), textcoords="data",
                       fontsize=6.3, color=INK, ha=ha, va="center", zorder=7,
                       arrowprops=dict(arrowstyle="-", lw=0.45, color=SOFT, shrinkA=1.5, shrinkB=4.0,
                                       relpos=(0.0 if ha == "left" else 1.0, 0.5)))
        c_labels.append(t)
        clear_of_points(c, t, allx, ally, r_c, f"c label {g}")
        clear_of_points(c, t, [sh["mean_d_eps_meV"] for sh in D["sign"].values()],
                        [sh["mean_dW_meV"] for sh in D["sign"].values()], MS_MEAN, f"c label {g} vs means")

    def no_overlap(arts, what):
        def chk(rnd):
            bbs = [extent(x, rnd) for x in arts]
            for i, j in itertools.combinations(range(len(bbs)), 2):
                assert not bbs[i].overlaps(bbs[j]), (what, i, j)
        checks.append(chk)
    no_overlap(c_labels + [leg_c], "c labels / legend")
    h = D["hist"]
    ks = range(len(GROUPS), -1, -1)
    heading(c, "ΔW$_g$ (work, P) against Δε$_g$ (site energy), per band and group",
            f"n = {len(GROUPS) * nb} ({nb} bands × {len(GROUPS)} groups), equal axis scales; "
            "brackets: |mean| − margin (work, site energy)",
            f"bands with {'/'.join(str(k) for k in ks)} groups of the same sign (raw signs, no margin): "
            f"{'/'.join(str(h[str(k)]) for k in ks)}", LIM_G(w_c_mm))

    # ---------------- (d) path dependence -------------------------------------------------------------------------
    Dd = D["Dd"]
    alld = np.concatenate([np.r_[Dd[g]["P"], Dd[g]["C"]] for g in GROUPS])
    xd = (-80.0, 60.0)
    assert xd[0] + 5 < alld.min() and alld.max() < xd[1] - 3
    d.plot(xd, xd, color=REF_C, lw=0.7, ls=(0, (3, 2)), zorder=1)
    for g in GROUPS:
        d.scatter(Dd[g]["C"], Dd[g]["P"], s=s_of(g, S_CD), marker=GMK[g], color=GC[g], linewidths=0, alpha=0.9,
                  zorder=2)
    d.set_xlim(*xd); d.set_ylim(*xd)
    dt = [-50, 0, 50]
    d.set_xticks(dt); d.set_xticklabels([fmt(v, 0) for v in dt])
    d.set_yticks(dt); d.set_yticklabels([fmt(v, 0) for v in dt])
    d.set_xlabel("ΔW$_g$ along C (meV)")
    d.set_ylabel("ΔW$_g$ along P (meV)")
    pc, gm = D["pc"], D["gmax"]
    means = [pc[g]["mean"] for g in GROUPS]
    mean_e = [pc[g]["mean_e"] for g in GROUPS]
    d_lines = ["dashed: y = x; symbols as c", "per group (meV):", f"mean |P − C| {fmt(min(means))} to {fmt(max(means))}",
               f"largest {fmt(pc[gm]['max'])}", f"({GLAB[gm]}, {pc[gm]['band']})",
               "mean e(P) + e(C),", "e = |X8 − X4|/3:", f"{fmt(min(mean_e), 2)} to {fmt(max(mean_e), 2)}"]
    xd_all = np.concatenate([Dd[g]["C"] for g in GROUPS]); yd_all = np.concatenate([Dd[g]["P"] for g in GROUPS])
    for i, s in enumerate(d_lines):
        t = d.annotate(s, (0.03, 0.97), xycoords="axes fraction", xytext=(0, -7.7 * i), textcoords="offset points",
                       fontsize=6.3, color=SOFT, ha="left", va="top")
        clear_of_points(d, t, xd_all, yd_all, r_c, f"d text line {i}")

        def above_diag(rnd, t=t):
            x0, y0, x1, y1 = data_bbox(d, t, rnd)
            assert y0 > x1 + 3, ("d text reaches y = x", t.get_text(), x1, y0)
        checks.append(above_diag)
    heading(d, "ΔW$_g$ on P against C", f"{D['n_both']} bands, P and C resolved (n = {len(GROUPS) * D['n_both']})",
            f"not drawn: {len(D['c_fail'])} bands with C not resolved", LIM_R(W_SIDE_MM))

    for lb, ax in zip("abcd", (a, b, c, d)):
        t = ax.transAxes + ScaledTranslation(-LAB_DX / 72, LAB_DY / 72, fig.dpi_scale_trans)
        ax.text(0, 1, lb, transform=t, fontsize=8, fontweight="bold", ha="left", va="bottom")

    # c, d: no bars drawn; every |X8 - X4| of a plotted dW_g is shorter than the smallest marker half-width
    r_min = min(half_x_pt(g, S_CD) for g in GROUPS)
    e_c = max(float(V[g]["dW84"].max()) for g in GROUPS) * w_c_mm * PT / (xc[1] - xc[0])
    e_d = max(3 * max(Dd[g][k]) for g in GROUPS for k in ("e_P", "e_C")) * W_SIDE_MM * PT / (xd[1] - xd[0])
    assert e_c < r_min and e_d < r_min, (e_c, e_d, r_min)
    # b: how many error bars reach beyond their (filled, edgeless) marker along x, at the final scale
    pt_per_meV = W_WIDE_MM * PT / (xb[1] - xb[0])
    nbar = 2 * len(GROUPS) * nb
    n_out = sum(int(np.sum(V[g][k] * pt_per_meV > half_x_pt(g, S_B))) for g in GROUPS for k in ("dW84", "WZS84"))
    e_max = max(float(V[g][k].max()) for g in GROUPS for k in ("dW84", "WZS84"))
    bars_note.set_text(f"bars ± |X8 − X4| (max {fmt(e_max)} meV), " +
                       (f"inside the markers in all {nbar}" if n_out == 0 else
                        f"beyond the markers in {n_out} of {nbar}") + "; D: median displacement share")

    out = os.path.join(HERE, NAME)
    fig.set_dpi(600)                   # measure the text fits at the export resolution
    fig.canvas.draw()
    rnd = fig.canvas.get_renderer()
    for art, ax, lim in fits:
        x1 = ax.transAxes.inverted().transform(art.get_window_extent(rnd).get_points())[1, 0]
        assert x1 <= lim + 1e-3, (art.get_text(), x1, lim)
    top = max(ax.transAxes.inverted().transform(art.get_window_extent(rnd).get_points())[1, 1] for art, ax, _ in fits
              if ax in (a, b))
    assert top < 1 + T_MM / H_TOP_MM, top          # top headings stay inside the figure
    for chk in checks:
        chk(rnd)
    bb = a.get_window_extent(rnd)                  # a: the same length per decade on both axes
    per_dec_x = bb.width / math.log10(XA[1] / XA[0]); per_dec_y = bb.height / math.log10(YA[1] / YA[0])
    assert abs(per_dec_x / per_dec_y - 1) < 0.005, (per_dec_x, per_dec_y)
    require_matplotlib_panel_alignment(fig, json_out=out + ".alignment.json", overlay_svg=out + ".alignment.svg",
                                       tolerance_pt=1.5, gutter_tolerance_pt=1.5, require_panel_labels=True,
                                       strict=True)
    fig.savefig(out + ".pdf", metadata={"CreationDate": None})
    fig.savefig(out + ".svg", metadata={"Date": None})
    fig.savefig(out + ".png", dpi=600)
    fig.savefig(out + ".tiff", dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    print("written", NAME + ".{pdf,svg,png,tiff}", "| b bars beyond markers:", n_out, "of", nbar,
          "| max |X8-X4| %.4f meV" % e_max)


if __name__ == "__main__":
    palette_check()
    require_matplotlib_panel_alignment = load_alignment_gate()      # before anything is written
    os.makedirs(SRC, exist_ok=True)
    plot(collect())

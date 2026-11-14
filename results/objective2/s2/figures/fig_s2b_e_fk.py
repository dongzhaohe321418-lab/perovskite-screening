#!/usr/bin/env python
"""Figure S2b-E: F(k) - F(final) of every relaxation that E, the one evaluation of S2b, read (S2B_PLAN.md section 7,
"The figure", S2B:721-725; amendment 2026-11-12a item 10; E_DECISIONS_R1 OP-24; E_IMPLEMENTATION_SPEC section 17).

  a  C2 relaxations 5-8 (E block 1: the far quartet, m30 Pb76, Sr).
  b  The FR cells that ran (E block 2: m30 FA188, Cs). A cell without configurations is listed with its status, not
     drawn.
  c  C4b relaxations (E block 4), only if present; then E block 5 (C2 relaxations 1-4, m30 Pb136), only if E opened
     it. The output of the deferred hinge run (--hinge) has one panel, relaxations 1-4.
  y is symlog with a linear threshold of 0.1 meV (S2B:722); ticks mark the first configuration of each restart part;
  each Delta F_tail window [k_last - 36, k_last] is a light lane with a marker on the curve at k_last - 36; for VB76,
  dashed verticals at k = 156, 158 and 172 (S2B:723); end glyphs follow the record's end rule (as D-C2-11); colour
  shows the quartet and line style the cell (as the C2 figure). x runs from -2 to max(k_last) + 2 in each panel.

Source data. Only E's own figure source data, which E writes in phase 2 (OP-24, A10): figures/source_data/
fig_s2b_e_fk<suffix>.csv (columns block, campaign, order, label, quartet, role, k, part, dF_meV, k_last,
restart_start, tail_k; dF_meV is repr(F(k) - F(final)) in meV) and fig_s2b_e_fk<suffix>_meta.csv (header, e_output,
e_head, attempt, mode, then end_rule.<label> for every relaxation of the CSV and, in an evaluation, status.<label> for
the four FR cells). For the build asserts only, it also reads the E output that the meta names (s2b/<e_output>).

Blinding. The script opens no archive file and computes no energy: every plotted number is one that E printed. Before
any read it installs the archive refusals of S2/s2b/e_guard.py (selftest_block on this checkout's S2 root: c1
records, raw outputs, gates and structures, c2, fr, c3b, c4b), so that an open of an archive path raises before the
operating-system call, in every mode. Helpers are loaded with spec_from_file_location (RF-19).

Build asserts (spec 17), each a refusal (FigRefused) that names the check, the label and the k, never a value:
  the CSV columns and the meta keys; the suffix, mode, attempt and E output name agree; per relaxation the ks are
  contiguous from 0 to k_last, dF_meV is 0 at k_last, tail_k = k_last - 36 (empty when k_last < 36), restart_start
  marks exactly the first k of each later part; every label is a relaxation of its block (FAR, FR, HINGE; others C4b);
  every label is a relaxation printed (status complete) in the named E output, with the same end rule, the same ks,
  every value equal to the printed '%.2f' F(k) - F(final), the same restart marks and the same Delta F_tail ks (156,
  158 and 172 for VB76); every relaxation whose curve E printed is in the CSV; meta.header equals every header line of
  that output; the output's first line carries meta.e_head, meta.mode and meta.attempt; its last line is an exit code
  0 or 1.

QA (nature-figure, Python backend, as for the C1 and C2 figures): the panel-alignment gate runs at render time
(~/.claude/skills/nature-figure/scripts/audit_panel_alignment.py; a single panel is 'not applicable'); afterwards the
static preflight (validate_figure.py on this file), the PDF text audit (audit_pdf_text.py, 5 pt floor) and the
collision audit (audit_figure_collisions.py) run on the exported PDF. The caption (caption(meta)) begins with the
header verbatim (S2B:619); it is written to <out>.caption.txt and into the PDF Subject.

    python -B -I fig_s2b_e_fk.py [--suffix ""|_attempt2|_attempt3|_hinge|_hinge_attempt2]
                 [--src DIR] [--e-output PATH] [--out PREFIX]       # build from E's source data, with the asserts
    python -B -I fig_s2b_e_fk.py --self-test [--keep DIR]           # synthetic CSVs in a temporary directory
"""
import argparse, collections, csv, importlib.util, io, math, os, re, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
S2 = os.path.normpath(os.path.join(HERE, ".."))                          # results/objective2/s2
SRC = os.path.join(HERE, "source_data")
SKILL = os.path.expanduser("~/.claude/skills/nature-figure/scripts")    # layout QA toolkit (optional)


def _load_shared(key, path):
    """One module object per process and file, never through sys.path (RF-19; as e_guard._load_shared)."""
    m = sys.modules.get(key)
    if m is None:
        s = importlib.util.spec_from_file_location(key, path)
        m = importlib.util.module_from_spec(s)
        sys.modules[key] = m
        try:
            s.loader.exec_module(m)
        except BaseException:
            del sys.modules[key]
            raise
    return m


eg = _load_shared("_s2b_e_guard", os.path.join(S2, "s2b", "e_guard.py"))   # the archive refusals and label sets

# ---------------------------------------------------------------- constants (spec 6.2 phase 2, 9, 10, 17)
COLS = ("block", "campaign", "order", "label", "quartet", "role", "k", "part", "dF_meV", "k_last", "restart_start",
        "tail_k")                                                        # e_eval csv_texts (spec 17)
META_KEYS = ("header", "e_output", "e_head", "attempt", "mode")       # spec 17, in this order
SUFFIX = {("evaluation", "1"): "", ("evaluation", "2"): "_attempt2", ("evaluation", "3"): "_attempt3",
          ("hinge", "1"): "_hinge", ("hinge", "2"): "_hinge_attempt2"}    # e_eval SUFFIX (OP-21, OP-22)
E_OUTPUT = {"": "E_output.txt", "_attempt2": "E_output_attempt2.txt", "_attempt3": "E_output_attempt3.txt",
            "_hinge": "E_hinge_output.txt", "_hinge_attempt2": "E_hinge_output_attempt2.txt"}   # S2B:523, 715
TAIL_BACK = 36                                                           # S2B:643; OP-13
VB76, VB76_K = "s2r_m30_VB76", (156, 158, 172)                          # S2B:643-644, 723
FAR = ("s2r_m30_hostB76", "s2r_m30_VB76", "s2r_m30_Sr76o0_novac", "s2r_m30_Sr76o0_vac")          # relaxations 5-8
FR_ORDER = ("s2r_m30_hostA188", "s2r_m30_VA188", "s2r_m30_Cs188o0_novac", "s2r_m30_Cs188o0_vac")  # S2B section 2
HINGE = ("s2r_m30_VB136", "s2r_m30_hostB136", "s2r_m30_Sr136o0_novac", "s2r_m30_Sr136o0_vac")    # relaxations 1-4
assert (FAR, FR_ORDER, HINGE) == (eg.FAR, eg.FR_ORDER, eg.HINGE), "label sets differ from e_guard"
CAMPAIGN = {1: "c2", 2: "fr", 4: "c4b", 5: "c2"}
ROLES = ("host", "V", "D", "DV")
END_GLYPH = {"accepted_converged": ("o", 15), "accepted_plateau": ("^", 17), "unconverged_cap": ("X", 18),
             "unconverged_early": ("s", 13)}                             # as the C2 figure (D-C2-11)
END_TEXT = {"accepted_converged": "accepted: converged", "accepted_plateau": "accepted: plateau",
            "unconverged_cap": "unconverged: cap", "unconverged_early": "unconverged: early end"}
STATUS_TEXT = {"missing": "missing", "killed_by_gate": "killed by a gate", "not_run_gate": "not run (gate)",
               "not_started_cap": "not started (cap)", "pending": "pending", "no record": "no record",
               "complete": "complete; no configuration"}
PANEL_TITLE = {1: "C2 relaxations 5–8 (E block 1): far quartet, m30 Pb76, Sr",
               2: "FR cells that ran (E block 2): m30 FA188, Cs",
               4: "C4b relaxations (E block 4)",
               5: "C2 relaxations 1–4 (E block 5, hinge): m30 Pb136, Sr"}
L_TAIL = ("path energy of the whole region over the window; not attributable to the failing objects; bounds no E_b "
          "error; reported only")                                        # E's L_TAIL (S2B:645)


class FigRefused(Exception):
    """A failed build assert: the check, the label and the k, never a value."""


def refuse(check, label="", k=""):
    raise FigRefused(f"fig_s2b_e_fk refused: {check}" + (f": {label}" if label else "") +
                     (f" at k = {k}" if k != "" else ""))


# ---------------------------------------------------------------- source data
def parse_source(csv_text, meta_text):
    """E's two CSV texts -> (rows, meta); the columns and the meta keys are checked here."""
    r = csv.reader(io.StringIO(csv_text))
    head = next(r, None)
    if tuple(head or ()) != COLS:
        refuse("CSV columns")
    rows = [dict(zip(COLS, x)) for x in r if x]
    if any(len(x) != len(COLS) for x in rows):
        refuse("CSV row length")
    m = list(csv.reader(io.StringIO(meta_text)))
    if not m or m[0] != ["key", "value"] or any(len(x) != 2 for x in m[1:]):
        refuse("meta columns")
    keys = [x[0] for x in m[1:]]
    if tuple(keys[:len(META_KEYS)]) != META_KEYS or len(set(keys)) != len(keys):
        refuse("meta keys")
    if any(not re.fullmatch(r"(end_rule|status)\.s2r_\w+", k) for k in keys[len(META_KEYS):]):
        refuse("meta keys")
    return rows, dict(m[1:])


def read_source(src, suffix):
    """The two CSVs of one E output (opened after the archive refusals are installed)."""
    with open(os.path.join(src, f"fig_s2b_e_fk{suffix}.csv"), encoding="utf-8") as fh:
        c = fh.read()
    with open(os.path.join(src, f"fig_s2b_e_fk{suffix}_meta.csv"), encoding="utf-8") as fh:
        m = fh.read()
    return parse_source(c, m)


def _int(x, check, label="", k=""):
    if not re.fullmatch(r"0|[1-9]\d*", x or ""):
        refuse(check, label, k)
    return int(x)


def curves_of(rows):
    """rows -> OrderedDict label -> {block, campaign, order, quartet, role, k_last, tail_k, k, part, dF, start}."""
    out = collections.OrderedDict()
    for x in rows:
        lab = x["label"]
        if not re.fullmatch(r"s2r_m(30|05)_\w+", lab):
            refuse("label grammar", lab)
        const = (x["block"], x["campaign"], x["order"], x["quartet"], x["role"], x["k_last"], x["tail_k"])
        c = out.get(lab)
        if c is None:
            c = out[lab] = {"const": const, "block": _int(x["block"], "block", lab), "campaign": x["campaign"],
                            "order": _int(x["order"], "order", lab), "quartet": x["quartet"], "role": x["role"],
                            "k_last": _int(x["k_last"], "k_last", lab),
                            "tail_k": None if x["tail_k"] == "" else _int(x["tail_k"], "tail_k", lab),
                            "k": [], "part": [], "dF": [], "start": []}
        elif c["const"] != const:
            refuse("per-relaxation columns not constant", lab)
        k = _int(x["k"], "k", lab)
        c["k"].append(k)
        c["part"].append(_int(x["part"], "part", lab, k))
        try:
            v = float(x["dF_meV"])
        except ValueError:
            v = float("nan")
        if not math.isfinite(v) or repr(v) != x["dF_meV"]:
            refuse("dF_meV is not a finite repr(float)", lab, k)
        c["dF"].append(v)
        if x["restart_start"] not in ("0", "1"):
            refuse("restart_start", lab, k)
        c["start"].append(x["restart_start"] == "1")
    return out


# ---------------------------------------------------------------- build asserts (spec 17); each check is patchable
def chk_contiguous(lab, c):
    if c["k"] != list(range(c["k_last"] + 1)):
        refuse("ks not contiguous from 0 to k_last", lab)


def chk_zero_at_klast(lab, c):
    if c["dF"][-1] != 0.0:
        refuse("dF_meV is not 0 at k_last", lab, c["k_last"])


def chk_tail(lab, c):
    want = c["k_last"] - TAIL_BACK if c["k_last"] >= TAIL_BACK else None
    if c["tail_k"] != want:
        refuse("tail_k is not k_last - 36", lab)


def chk_restarts(lab, c):
    prev = None
    for k, p, s in zip(c["k"], c["part"], c["start"]):
        if prev is not None and p < prev:
            refuse("parts not increasing", lab, k)
        if s != (p > 1 and p != prev):
            refuse("restart_start does not mark the first k of a later part", lab, k)
        prev = p


def chk_block(lab, c, mode):
    b = c["block"]
    sets = {1: FAR, 2: FR_ORDER, 5: HINGE}
    if b not in CAMPAIGN or c["campaign"] != CAMPAIGN[b] or c["role"] not in ROLES:
        refuse("block, campaign or role", lab)
    if mode == "hinge" and b != 5:
        refuse("a hinge-run CSV holds a relaxation outside block 5", lab)
    if b in sets and lab not in sets[b] or b == 4 and lab in FAR + FR_ORDER + HINGE:
        refuse("label not a relaxation of its block", lab)
    if b in sets and c["order"] != sets[b].index(lab) + (5 if b == 1 else 1):
        refuse("order", lab)


def chk_meta(meta, suffix, curves):
    if SUFFIX.get((meta["mode"], meta["attempt"])) != suffix or meta["e_output"] != E_OUTPUT[suffix]:
        refuse("suffix, mode, attempt and E output name disagree")
    if not re.fullmatch(r"[0-9a-f]{40}", meta["e_head"]):
        refuse("e_head")
    er = {k[9:]: v for k, v in meta.items() if k.startswith("end_rule.")}
    if set(er) != set(curves):
        refuse("end_rule rows are not exactly the CSV's relaxations")
    for lab, v in er.items():
        if v not in END_GLYPH:
            refuse("end rule", lab)
    st = {k[7:]: v for k, v in meta.items() if k.startswith("status.")}
    if meta["mode"] == "evaluation":
        if tuple(st) != FR_ORDER:
            refuse("status rows are not the four FR cells")
        for lab, c in curves.items():
            if c["block"] == 2 and st[lab] != "complete":
                refuse("a drawn FR cell is not complete", lab)
    elif st:
        refuse("status rows in a hinge run")


_FIRST = re.compile(r"S2b E, (?:attempt (\d) of the one evaluation|hinge run(?:, attempt (\d))?) \(S2B_PLAN\.md §7\); "
                    r"run at \S+; HEAD ([0-9a-f]{40}); mode (evaluation|hinge)")
_RELAX = re.compile(r"  (\d+)\. (s2r_\w+) \((c2|fr|c4b)\): status (\S+); end rule (\S+); end .*")
_CURVE = re.compile(r"      k (\d+)-(\d+): (.*)")
_MARK = re.compile(r"restart part (\d+) at k = (\d+)")
_TAILL = re.compile(r"  (?:ΔF_tail )?(s2r_\w+): F\((\d+)\) − F\(final\) = (-?\d+\.\d\d) meV(?:  -- .*)?")


def e_facts(text):
    """The E output, as printed (spec 9 output order): first line, header lines, exit code, and per relaxation
    section its number, campaign, status, end rule, printed curve values, restart marks and Delta F_tail lines."""
    lines = text.rstrip("\n").split("\n")
    f = {"first": _FIRST.fullmatch(lines[0]) if lines else None,
         "headers": [x for x in lines if x.startswith("S2 K3: ")],
         "exit": lines[-1] if lines else "", "relax": collections.OrderedDict(), "tails": collections.defaultdict(dict)}
    cur = None
    for x in lines:
        m = _RELAX.fullmatch(x)
        if m:
            lab = m.group(2)
            if lab in f["relax"]:
                refuse("a relaxation printed twice in the E output", lab)
            cur = f["relax"][lab] = {"number": int(m.group(1)), "campaign": m.group(3), "status": m.group(4),
                                     "end_rule": m.group(5), "curve": {}, "marks": {}}
            continue
        if x.startswith("BLOCK ") or re.match(r" \d\.\d ", x):
            cur = None
        m = _TAILL.fullmatch(x)
        if m:
            f["tails"][m.group(1)][int(m.group(2))] = m.group(3)
            continue
        m = _CURVE.fullmatch(x)
        if m and cur is not None:
            vals, *marks = m.group(3).split("  | ")
            ks = list(range(int(m.group(1)), int(m.group(2)) + 1))
            vs = vals.split(" ")
            if len(vs) != len(ks):
                refuse("a printed curve line", "", ks[0])
            cur["curve"].update(zip(ks, vs))
            for mk in marks:
                mm = _MARK.fullmatch(mk.strip())
                if not mm:
                    refuse("a printed restart mark", "", ks[0])
                cur["marks"][int(mm.group(2))] = int(mm.group(1))
    return f


def chk_e_output(meta, curves, text):
    f = e_facts(text)
    m = f["first"]
    if m is None or m.group(3) != meta["e_head"] or m.group(4) != meta["mode"] or \
            (m.group(1) or m.group(2) or "1") != meta["attempt"]:
        refuse("the E output's first line does not carry e_head, mode and attempt")
    if f["exit"] not in ("E exit code: 0", "E exit code: 1"):
        refuse("the E output does not end with exit code 0 or 1")
    if len(f["headers"]) < 2 or any(h != meta["header"] for h in f["headers"]):
        refuse("meta.header is not the E output's header line")
    for lab, c in curves.items():
        p = f["relax"].get(lab)
        if p is None or p["status"] != "complete" or p["campaign"] != c["campaign"]:
            refuse("not printed as a complete relaxation in the E output", lab)
        if p["end_rule"] != meta[f"end_rule.{lab}"]:
            refuse("end rule differs from the E output", lab)
        if sorted(p["curve"]) != c["k"]:
            refuse("ks differ from the printed curve", lab)
        for k, v in zip(c["k"], c["dF"]):
            if "%.2f" % v != p["curve"][k]:
                refuse("a value differs from the printed F(k) - F(final)", lab, k)
        if p["marks"] != {k: q for k, q, s in zip(c["k"], c["part"], c["start"]) if s}:
            refuse("restart parts differ from the printed marks", lab)
        if lab == VB76 and c["block"] == 1 and c["k_last"] < max(VB76_K):   # fix round 2: before the tails, which
            refuse("VB76 k_last below 172", lab)                            # index dF at 158 and 172
        want = set() if c["tail_k"] is None else {c["tail_k"]} | (set(VB76_K[1:]) if lab == VB76 and
                                                                   c["block"] == 1 else set())
        got = f["tails"].get(lab, {})
        if set(got) != want:
            refuse("Delta F_tail ks differ from the printed ones", lab)
        for k, v in got.items():
            if "%.2f" % c["dF"][k] != v:
                refuse("a value differs from the printed Delta F_tail", lab, k)
    for lab, p in f["relax"].items():
        if p["curve"] and lab not in curves:
            refuse("a relaxation whose curve E printed is missing from the CSV", lab)
    return f


CHECKS = ("chk_contiguous", "chk_zero_at_klast", "chk_tail", "chk_restarts")


def panels(meta, curves=None):
    """[(letter, block, [labels])] from the meta (caption) or the curves (plot): a = block 1, b = block 2, then block 4
    and block 5 if present; a hinge run has the one block-5 panel."""
    if curves is None:
        labs = [k[9:] for k in meta if k.startswith("end_rule.")]
        blk = {lab: 1 if lab in FAR else 2 if lab in FR_ORDER else 5 if lab in HINGE else 4 for lab in labs}
    else:
        blk = {lab: c["block"] for lab, c in curves.items()}
    want = [5] if meta["mode"] == "hinge" else [1, 2] + [b for b in (4, 5) if b in blk.values()]
    order = (lambda lab: curves[lab]["order"]) if curves is not None else (lambda lab: 0)
    return [("abcd"[i], b, sorted((lab for lab in blk if blk[lab] == b), key=order)) for i, b in enumerate(want)]


def check(rows, meta, e_text, suffix):
    """Every build assert of spec 17; returns (curves, panels)."""
    curves = curves_of(rows)
    if not curves:
        refuse("no relaxation in the CSV")
    for lab, c in curves.items():
        for name in CHECKS:
            globals()[name](lab, c)
        chk_block(lab, c, meta["mode"])
    chk_meta(meta, suffix, curves)
    chk_e_output(meta, curves, e_text)
    pan = panels(meta, curves)
    if meta["mode"] == "evaluation" and not any(b == 1 and labs for _, b, labs in pan):
        refuse("no block-1 relaxation in an evaluation")
    return curves, pan


# ---------------------------------------------------------------- caption (S2B:619)
def _status(v):
    return STATUS_TEXT.get(v, v)


def caption(meta):
    """The caption: it begins with meta['header'] verbatim (S2B:619-621), then the panel key and the marks."""
    pan = panels(meta)
    run = "the deferred hinge run" if meta["mode"] == "hinge" else "the one evaluation"
    suffix = SUFFIX.get((meta["mode"], meta["attempt"]), "?")
    st = {k[7:]: v for k, v in meta.items() if k.startswith("status.")}
    parts = []
    for letter, b, labs in pan:
        t = f"{letter}, {PANEL_TITLE[b].replace(' (E block', ' (block')}"
        if b == 2:
            miss = [f"{lab} (status {st.get(lab, 'absent')})" for lab in FR_ORDER if lab not in labs]
            t += "; no curve: " + ", ".join(miss) if miss else ""
        parts.append(t)
    vb = any(lab == VB76 for _, b, labs in pan if b == 1 for lab in labs)
    return "\n".join([
        meta["header"], "",
        f"Figure S2b-E. F(k) − F(final) of every relaxation that E read in {run} ({meta['e_output']}, attempt "
        f"{meta['attempt']}, HEAD {meta['e_head']}), against the configuration k counted across restart parts "
        f"(S2B_PLAN.md §7, \"The figure\"). " + "; ".join(parts) + ".",
        "Each curve is F(k) − F(final) in meV of the configurations that E parsed with scripts/47 parse_relax "
        "(read = full) at 8bff03e, as E printed it; F(final) is F at the record's k_last. The y axis is "
        "symmetric-logarithmic and linear within ±0.1 meV (grey band). Colour shows the quartet and line style the "
        "cell (host_R, V⁺_R as V, D, D+V⁺ as D+V; legend: E's order, cell, label). Ticks mark the first "
        "configuration of each restart part. Each light lane spans a ΔF_tail window [k_last − 36, k_last], in the "
        "legend's order, and the open diamond marks F(k_last − 36) − F(final) on its curve; ΔF_tail: " + L_TAIL +
        "."
        + (" For VB76 the dashed verticals mark k = 156, 158 and 172 (S2B:643-644)." if vb else "") +
        " End glyphs show each record's end rule (accepted: converged or plateau; unconverged: cap or early end), as "
        "D-C2-11. Every curve is one deterministic relaxation: there are no replicates and no intervals.",
        f"Source data: figures/source_data/fig_s2b_e_fk{suffix}.csv and fig_s2b_e_fk{suffix}_meta.csv, written by E "
        f"(OP-24)."]) + "\n"


# ---------------------------------------------------------------- plot
QC = {"Pb76": "#d08a2e", "Pb136": "#2f6db5", "FA188": "#7b5ea7"}     # quartet colours (Pb76, Pb136 as the C2 figure)
QC_MORE = ("#8c564b", "#3f8f80", "#b05f8a", "#6b6b6b")                 # C4b quartets, in order of appearance
LS = {"host": "-", "V": (0, (4, 1.6)), "D": (0, (1, 1.3)), "DV": (0, (5, 1.4, 1, 1.4))}       # as the C2 figure
ROLE = {"host": "host", "V": "V", "D": "D", "DV": "D+V"}
NEU, INK, BAND = "#9aa3ad", "#3a3a3a", "#eceff3"
LINTHRESH, LINSCALE = 0.1, 0.6                                          # S2B:722 (meV)
LANE_H, LANE_STEP, LANE_TOP = 0.038, 0.05, 0.975                         # tail lanes, in axes fraction


def _yfmt(v, _pos=None):
    if v == 0:
        return "0"
    a = abs(v)
    s = "%g" % a if a < 1 else "%d" % round(a)
    return ("−" if v < 0 else "") + s


def _ylim(mpl, vals, n_lanes):
    """y limits in symlog space: the data in the lower part, the lanes of the tail windows above it."""
    tr = mpl.scale.SymmetricalLogTransform(10, LINTHRESH, LINSCALE)
    t = tr.transform([min(min(vals), 0.0), max(max(vals), 0.0)])
    span = max(t[1] - t[0], 2 * LINTHRESH)               # transformed units scale with linthresh
    f_bot, f_top = 0.05, LANE_TOP - n_lanes * LANE_STEP - 0.03
    T = span / (f_top - f_bot)
    b = t[0] - f_bot * T
    lo, hi = tr.inverted().transform([b, b + T])
    return float(lo), float(hi)


def _yticks(vals):
    """Decade ticks covering the data only (the lanes above the data carry no y value): 0, +-0.1, ..., up to the
    first decade at or beyond each extreme."""
    lo, hi = min(min(vals), 0.0), max(max(vals), 0.0)
    out = [0.0]
    for s, ext in ((1, hi), (-1, -lo)):
        e = -1
        while ext > 0 and e < 7:
            out.append(s * 10.0 ** e)
            if 10.0 ** e >= ext:
                break
            e += 1
    out.sort()
    if len(out) > 9:                                   # every other decade, keeping 0, +-0.1 and the extremes
        keep = {0.0, 0.1, -0.1, out[0], out[-1]}
        out = [v for v in out if v in keep or round(math.log10(abs(v))) % 2 == 0]
    return out


def _ytick_room(ax, fig, yt, min_pt=8.0):
    """Drop tick labels that would sit closer than min_pt: first +-0.1 (the linear band stays drawn), then every
    other decade (0 and the extremes kept)."""
    for _ in range(4):
        y = [ax.transData.transform((0, v))[1] * 72.0 / fig.dpi for v in yt]
        if len(yt) < 3 or min(b - a for a, b in zip(y, y[1:])) >= min_pt:
            return yt
        if 0.1 in yt or -0.1 in yt:
            yt = [v for v in yt if abs(v) != 0.1]
        else:
            keep = {0.0, yt[0], yt[-1]}
            yt = [v for v in yt if v in keep or round(math.log10(abs(v))) % 2 == 0] if len(yt) > 3 else yt
    return yt


def plot(curves, pan, meta, out, formats=("pdf", "svg", "png", "tiff"), audit=True, inspect=None):
    """The figure. inspect(fig, axes, pan, curves, meta), if given, is called on the drawn figure before it is saved
    and closed (the self-test asserts the plan's marks on the artists; fix round 1)."""
    import matplotlib as mpl
    mpl.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from matplotlib.transforms import ScaledTranslation
    gate = None
    if audit:
        p = os.path.join(SKILL, "audit_panel_alignment.py")
        if os.path.exists(p):                      # layout QA from the nature-figure toolkit; it reads no data
            gate = _load_shared("_s2b_fig_audit_panel_alignment", p).require_matplotlib_panel_alignment
        else:
            print("note: panel-alignment audit unavailable; figure rendered without it")
    mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                         "svg.fonttype": "none", "pdf.fonttype": 42, "font.size": 7, "axes.spines.right": False,
                         "axes.spines.top": False, "axes.linewidth": 0.8, "legend.frameon": False,
                         "xtick.major.width": 0.8, "ytick.major.width": 0.8, "svg.hashsalt": "fig_s2b_e_fk"})
    cap = caption(meta)
    qc, more = dict(QC), list(QC_MORE)
    for c in curves.values():
        if c["quartet"] not in qc:
            qc[c["quartet"]] = more.pop(0) if more else NEU
    st = {k[7:]: v for k, v in meta.items() if k.startswith("status.")}
    n = len(pan)
    W, PH, TOP, BOT, GAP = 7.205, 1.78, 0.30, 0.88, 0.62            # inches: 183 mm wide
    H = TOP + n * PH + (n - 1) * GAP + BOT
    fig = plt.figure(figsize=(W, H))
    gs = fig.add_gridspec(n, 1, left=0.62 / W, right=1 - 1.48 / W, top=1 - TOP / H, bottom=BOT / H,
                          hspace=GAP / PH)
    axes, vb_seen = [], False
    for i, (letter, b, labs) in enumerate(pan):
        ax = fig.add_subplot(gs[i, 0])
        axes.append(ax)
        cs = [curves[lab] for lab in labs]
        tails = [(lab, c) for lab, c in zip(labs, cs) if c["tail_k"] is not None]
        vals = [v for c in cs for v in c["dF"]] or [0.0]
        ax.set_yscale("symlog", linthresh=LINTHRESH, linscale=LINSCALE, base=10)
        yt = _yticks(vals)
        lo, hi = _ylim(mpl, yt, len(tails))           # the outer decades of the data, below the lanes
        ax.set_ylim(lo, hi)
        kmax = max([c["k_last"] for c in cs] or [10])
        ax.set_xlim(-2, kmax + 2)
        ax.axhspan(max(-LINTHRESH, lo), min(LINTHRESH, hi), color=BAND, lw=0, zorder=0)   # inside the limits
        ax.axhline(0, color=NEU, lw=0.5, zorder=1)
        hl, ll = [], []
        for lab, c in zip(labs, cs):
            col, ls = qc[c["quartet"]], LS[c["role"]]
            ax.plot(c["k"], c["dF"], color=col, ls=ls, lw=0.9, zorder=3)
            rk = [k for k, s in zip(c["k"], c["start"]) if s]
            if rk:
                ax.plot(rk, [c["dF"][k] for k in rk], ls="none", marker="|", ms=6, mew=1.0, color=col, zorder=4,
                        gid=f"restart:{lab}")
            mk, sz = END_GLYPH[meta[f"end_rule.{lab}"]]
            ax.scatter([c["k_last"]], [0.0], marker=mk, s=sz, color=col, edgecolor="white", linewidth=0.4,
                       zorder=5, clip_on=False, gid=f"end:{lab}")
            hl.append(Line2D([], [], color=col, ls=ls, lw=0.9))
            short = lab[len("s2r_m30_"):] if lab.startswith("s2r_m30_") else lab
            ll.append(f"{c['order']}  {ROLE[c['role']]}  {short}")
        for j, (lab, c) in enumerate(tails):                       # Delta F_tail windows: lanes in legend order
            col, y1 = qc[c["quartet"]], LANE_TOP - j * LANE_STEP
            ax.axvspan(c["tail_k"], c["k_last"], ymin=y1 - LANE_H, ymax=y1, color=col, alpha=0.16, lw=0, zorder=1)
            ax.plot([c["tail_k"], c["k_last"]], [y1 - LANE_H / 2] * 2, color=col, ls=LS[c["role"]], lw=0.8,
                    transform=ax.get_xaxis_transform(), zorder=2, solid_capstyle="butt")
            ax.scatter([c["tail_k"]], [c["dF"][c["tail_k"]]], marker="D", s=11, facecolor="white", edgecolor=col,
                       linewidth=0.8, zorder=6, gid=f"tail:{lab}")
        if b == 1 and VB76 in labs:                                # S2B:723
            vb_seen = True
            col = qc[curves[VB76]["quartet"]]
            for k in VB76_K:
                ax.axvline(k, color=col, lw=0.6, ls=(0, (3, 2)), zorder=2, gid=f"vb76:{k}")
            tx = ax.get_xaxis_transform()
            for k, ha, dx in ((156, "right", -1.5), (158, "left", 1.5), (172, "left", 1.5)):
                ax.text(k, 1.0, str(k), transform=tx + ScaledTranslation(dx / 72, 2 / 72, fig.dpi_scale_trans),
                        ha=ha, va="bottom", fontsize=6, color=col, clip_on=False)
        if b == 2:                                                 # FR cells without a curve, with their status
            for j, lab in enumerate(FR_ORDER, 1):
                if lab not in labs:
                    hl.append(Line2D([], [], color="none"))
                    v = st.get(lab, "absent")
                    ll.append(f"{j}  {ROLE[ROLES[j - 1]]}  {lab[len('s2r_m30_'):]}\n   " +
                              ("no configuration" if v == "complete" else f"no curve: {_status(v)}"))
            if not labs:
                ax.text(0.5, 0.4, "no FR cell with configurations", transform=ax.transAxes, ha="center",
                        fontsize=7, color=NEU)
        ax.yaxis.set_major_locator(mpl.ticker.FixedLocator(_ytick_room(ax, fig, yt)))
        ax.spines["left"].set_bounds(yt[0], yt[-1])
        ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(_yfmt))
        ax.yaxis.set_minor_locator(mpl.ticker.NullLocator())
        ax.xaxis.set_major_locator(mpl.ticker.MaxNLocator(nbins=10, integer=True))
        ax.set_ylabel("F(k) − F(final) (meV)")
        ax.set_xlabel("Configuration k (counted across restart parts)")
        ax.set_title(PANEL_TITLE[b], loc="left", fontsize=7, pad=4)
        ax.legend(hl, ll, loc="upper left", bbox_to_anchor=(1.015, 1.0), fontsize=6, handlelength=2.6,
                  borderaxespad=0.0, labelspacing=0.55)
        ax.text(0, 1, letter, transform=ax.transAxes + ScaledTranslation(-44 / 72, 6 / 72, fig.dpi_scale_trans),
                fontsize=8, fontweight="bold", va="bottom", ha="left")
    gh = [Line2D([], [], ls="none", marker=END_GLYPH[o][0], ms=math.sqrt(END_GLYPH[o][1]), color=INK,
                 markeredgecolor="white", markeredgewidth=0.4) for o in END_GLYPH]
    gl = [END_TEXT[o] for o in END_GLYPH]
    gh += [Line2D([], [], ls="none", marker="|", ms=6, mew=1.0, color=INK),
           Line2D([], [], ls="none", marker="D", ms=3.3, markerfacecolor="white", markeredgecolor=INK, mew=0.8),
           Patch(facecolor=INK, alpha=0.16, lw=0), Patch(facecolor=BAND, lw=0)]
    gl += ["first configuration of a restart part", "F(k_last − 36) − F(final)",
           "ΔF_tail window [k_last − 36, k_last]",
           "y linear within ±0.1 meV"]
    if vb_seen:
        gh.append(Line2D([], [], color=INK, lw=0.6, ls=(0, (3, 2))))
        gl.append("VB76: k = 156, 158, 172")
    pb = axes[-1].get_position()
    fig.legend(gh, gl, loc="upper left", ncol=5, fontsize=6, bbox_to_anchor=(pb.x0, (BOT - 0.42) / H),
               handletextpad=0.4, columnspacing=1.4, borderaxespad=0.0, handlelength=1.6)
    fig.canvas.draw()
    if inspect is not None:
        inspect(fig, axes, pan, curves, meta)
    if gate is not None:
        gate(fig, json_out=out + ".alignment.json", overlay_svg=out + ".alignment.svg", axes=axes,
             panel_ids=[p[0] for p in pan], tolerance_pt=1.5, gutter_tolerance_pt=1.5, require_panel_labels=True,
             strict=True)
    title = "Figure S2b-E: F(k) - F(final) of every relaxation read by E"
    if "pdf" in formats:
        fig.savefig(out + ".pdf", metadata={"CreationDate": None, "Title": title, "Subject": cap})
    if "svg" in formats:
        fig.savefig(out + ".svg", metadata={"Date": None, "Title": title, "Description": cap})
    if "png" in formats:
        fig.savefig(out + ".png", dpi=600, metadata={"Title": title, "Description": cap})
    if "tiff" in formats:
        fig.savefig(out + ".tiff", dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)
    return cap


def build(src=SRC, suffix="", e_output=None, out=None, formats=("pdf", "svg", "png", "tiff"), audit=True):
    """Read E's source data and the E output it names (after the archive refusals), assert, plot, write the caption."""
    if suffix not in E_OUTPUT:
        refuse("unknown suffix")
    eg.selftest_block([S2])                       # archive refusals for the rest of the process (no archive is read)
    rows, meta = read_source(src, suffix)
    if e_output is None:
        e_output = os.path.join(S2, "s2b", meta["e_output"])
    with open(e_output, encoding="utf-8") as fh:
        e_text = fh.read()
    curves, pan = check(rows, meta, e_text, suffix)
    out = out or os.path.join(HERE, f"fig_s2b_e_fk{suffix}")
    cap = plot(curves, pan, meta, out, formats=formats, audit=audit)
    if not cap.startswith(meta["header"] + "\n"):
        refuse("the caption does not begin with the header")
    with open(out + ".caption.txt", "w", encoding="utf-8") as fh:
        fh.write(cap)
    print("written", out + ".{" + ",".join(tuple(formats) + ("caption.txt",)) + "}")
    return {"curves": curves, "panels": pan, "meta": meta, "caption": cap, "out": out}


# ---------------------------------------------------------------- self-test (synthetic CSVs; no archive is read)
HEAD = "0123456789abcdef0123456789abcdef01234567"
HDR = ("S2 K3: fail (fail_replan); checks_failed: s2r_m30_VB76, check 5 (C2_RESULT.md). S2b FR: fail (FR-1, "
       "s2r_m30_Cs188o0_vac, check 5). Valid far references: 0 of 2.")


def _synthetic_relaxations():
    """Three relaxations: hostB76 (positive, one part), VB76 (k_last 192: the windows at 156, 158 and 172) and the FR
    D cell Cs188o0_novac in three parts (restarts at k = 11 and 21) with negative and positive values, k_last 30
    < 36."""
    def series(n, f):
        v = [round(f(k), 8) for k in range(n)]
        v[-1] = 0.0
        return v
    return [
        dict(block=1, campaign="c2", order=5, label="s2r_m30_hostB76", quartet="Pb76", role="host",
             dF=series(41, lambda k: 25.0 * math.exp(-k / 6.0)), part=[1] * 41),
        dict(block=1, campaign="c2", order=6, label="s2r_m30_VB76", quartet="Pb76", role="V",
             dF=series(193, lambda k: 380.0 * math.exp(-k / 18.0) - 0.002 * (192 - k) * math.sin(k / 9.0)),
             part=[1] * 193),
        dict(block=2, campaign="fr", order=3, label="s2r_m30_Cs188o0_novac", quartet="FA188", role="D",
             dF=series(31, lambda k: -40.0 * (1 - k / 30.0) ** 2 + 3.0 * math.sin(math.pi * k / 30.0)),
             part=[1] * 11 + [2] * 10 + [3] * 10, end_rule="unconverged_early")]


def _synthetic_csv(rels):
    b = io.StringIO()
    w = csv.writer(b, lineterminator="\n")
    w.writerow(COLS)
    for r in rels:
        kl = len(r["dF"]) - 1
        for k, (v, p) in enumerate(zip(r["dF"], r["part"])):
            w.writerow((r["block"], r["campaign"], r["order"], r["label"], r["quartet"], r["role"], k, p, repr(v), kl,
                        int(k > 0 and p != r["part"][k - 1]), kl - TAIL_BACK if kl >= TAIL_BACK else ""))
    return b.getvalue()


def _synthetic_meta(rels, mode="evaluation", attempt="1", suffix=""):
    m = io.StringIO()
    w = csv.writer(m, lineterminator="\n")
    w.writerow(("key", "value"))
    for k, v in (("header", HDR), ("e_output", E_OUTPUT[suffix]), ("e_head", HEAD), ("attempt", attempt),
                 ("mode", mode)):
        w.writerow((k, v))
    for r in sorted(rels, key=lambda r: r["label"]):
        w.writerow((f"end_rule.{r['label']}", r.get("end_rule", "accepted_converged")))
    if mode == "evaluation":
        st = {"s2r_m30_hostA188": "missing", "s2r_m30_VA188": "killed_by_gate",
              "s2r_m30_Cs188o0_novac": "complete", "s2r_m30_Cs188o0_vac": "not_run_gate"}
        for lab in FR_ORDER:
            w.writerow((f"status.{lab}", st[lab]))
    return m.getvalue()


def _synthetic_e_output(rels, mode="evaluation"):
    """An E output in E's printed format (e_eval print_relax and block 1.2; C11 of e_selftest checks the parser
    against real E outputs)."""
    first = ("S2b E, attempt 1 of the one evaluation" if mode == "evaluation" else "S2b E, hinge run") + \
        f" (S2B_PLAN.md §7); run at 2026-11-12T00:00:00Z; HEAD {HEAD}; mode {mode}"
    L = [first, "tools:", HDR, "INTEGRITY", "  INT-PARSE ok (synthetic)"]
    by = collections.OrderedDict()
    for r in rels:
        by.setdefault(r["block"], []).append(r)
    title = {1: "BLOCK 1. Far block: C2 relaxations 5-8 (m30, Pb76)", 2: "BLOCK 2. FR block: m30 FA188, Cs (S2B §2)",
             5: "BLOCK 5. Hinge block: relaxations 1-4 (m30, Pb136) and the Pb136 C1 items"}
    for b, rs in by.items():
        L += [title[b], HDR, f" {b}.1 Per relaxation"]
        for r in rs:
            kl = len(r["dF"]) - 1
            L += [f"  {r['order']}. {r['label']} ({r['campaign']}): status complete; end rule "
                  f"{r.get('end_rule', 'accepted_converged')}; end converged", f"  F(0) = -1.000000 eV",
                  "    F(k) − F(final) (meV):"]
            for k0 in range(0, kl + 1, 10):
                ks = list(range(k0, min(k0 + 10, kl + 1)))
                mark = "".join(f"  | restart part {r['part'][k]} at k = {k}" for k in ks
                               if k > 0 and r["part"][k] != r["part"][k - 1])
                L.append(f"      k {ks[0]}-{ks[-1]}: " + " ".join("%.2f" % r["dF"][k] for k in ks) + mark)
            if b != 1:
                L.append(f"  ΔF_tail {r['label']}: " + (f"F({kl - TAIL_BACK}) − F(final) = "
                         f"{'%.2f' % r['dF'][kl - TAIL_BACK]} meV  -- {L_TAIL}" if kl >= TAIL_BACK else
                         "not formed (k_last < 36)  -- " + L_TAIL))
        if b == 1:
            L.append(" 1.2 ΔF_tail = F(k_last − 36) − F(final) (S2B:643-645)")
            for r in rs:
                kl = len(r["dF"]) - 1
                for kt in [kl - TAIL_BACK] + (list(VB76_K[1:]) if r["label"] == VB76 else []):
                    if kt <= kl:                               # fix round 2: a truncated VB76 (the k_last assert)
                        L.append(f"  {r['label']}: F({kt}) − F(final) = {'%.2f' % r['dF'][kt]} meV  -- {L_TAIL}")
    L += ["BLOCK 3. MACE and deferred-C1 block (Pb136 cells excluded; see block 5)", HDR, "END", "E exit code: 0"]
    return "\n".join(L) + "\n"


def _check_marks(fig, axes, pan, curves, meta):
    """The plan's marks on the drawn artists (S2B:721-723; fix round 1): every panel symlog with a linear threshold
    of 0.1 meV; in panel a the three VB76 verticals at 156, 158 and 172; one restart tick per first configuration of
    a later part; the Delta F_tail marker at (k_last - 36, F(k_last - 36) - F(final)); the end glyph of each
    relaxation's own end rule at (k_last, 0)."""
    import numpy as np
    from matplotlib.markers import MarkerStyle
    by = {}
    for ax in axes:
        assert ax.get_yscale() == "symlog" and ax.yaxis.get_transform().linthresh == 0.1, "symlog linthresh"
        for a in list(ax.lines) + list(ax.collections):
            if a.get_gid():
                by[a.get_gid()] = a
    vb = sorted(k for k in VB76_K if f"vb76:{k}" in by)
    if any(lab == VB76 for _, b, labs in pan if b == 1 for lab in labs):
        assert vb == sorted(VB76_K) and all(list(by[f"vb76:{k}"].get_xdata()) == [k, k] for k in VB76_K), vb
    for lab, c in curves.items():
        rk = [k for k, s in zip(c["k"], c["start"]) if s]
        if rk:
            assert list(by[f"restart:{lab}"].get_xdata()) == rk, lab
        else:
            assert f"restart:{lab}" not in by, lab
        if c["tail_k"] is not None:
            assert by[f"tail:{lab}"].get_offsets().tolist() == [[c["tail_k"], c["dF"][c["tail_k"]]]], lab
        else:
            assert f"tail:{lab}" not in by, lab
        e = by[f"end:{lab}"]
        ms = MarkerStyle(END_GLYPH[meta[f"end_rule.{lab}"]][0])
        want = ms.get_path().transformed(ms.get_transform()).vertices
        got = e.get_paths()[0].vertices
        assert e.get_offsets().tolist() == [[c["k_last"], 0.0]] and got.shape == want.shape and \
            np.allclose(got, want), lab


def _expect(check_word, fn, *a):
    try:
        fn(*a)
    except FigRefused as e:
        if check_word not in str(e):
            raise AssertionError(f"refused for another reason: {e}")
        return
    raise AssertionError(f"not refused: {check_word}")


def _bump_printed(text, label, k):
    """The E text with the printed F(k) - F(final) of one relaxation at k changed by 0.01 meV."""
    lines, inside = text.split("\n"), False
    for i, x in enumerate(lines):
        m = _RELAX.fullmatch(x)
        if m:
            inside = m.group(2) == label
        mc = _CURVE.fullmatch(x)
        if inside and mc and int(mc.group(1)) <= k <= int(mc.group(2)):
            vals, *marks = mc.group(3).split("  | ")
            vs = vals.split(" ")
            j = k - int(mc.group(1))
            vs[j] = "%.2f" % (float(vs[j]) + 0.01)
            lines[i] = f"      k {mc.group(1)}-{mc.group(2)}: " + " ".join(vs) + "".join("  | " + s for s in marks)
            return "\n".join(lines)
    raise AssertionError(f"no printed curve of {label} at k = {k}")


def _variant(rows, label, k, **kw):
    out = []
    for x in rows:
        y = dict(x)
        if x["label"] == label and (k is None or x["k"] == str(k)):
            y.update(kw)
        out.append(y)
    return out


def self_test(keep=None, render=True):
    """Spec 17 self-test on synthetic CSVs (three relaxations, one in three parts with negative values): the build
    succeeds, the caption begins with the header and is the PDF Subject, and each build assert refuses its planted
    violation (a non-zero value at k_last among them; fix round 2: every build assert of chk_restarts, chk_block,
    chk_meta and chk_e_output, the VB76 k_last one now checked before the tails it would index). The archive
    refusals are installed first (RF-9)."""
    eg.selftest_block(eg.real_s2_dirs())
    for s2 in eg.real_s2_dirs():                   # checked without an open
        for rel in ("c2/gates/K3.json", "c1/raw/x.out.gz", "fr/campaign.json", "c1/structures.tar.gz"):
            assert eg.selftest_blocked(os.path.join(s2, rel)), rel
    tmp = tempfile.mkdtemp(prefix="fig_s2b_e_fk_selftest_")
    try:
        rels = _synthetic_relaxations()
        csv_t, meta_t, e_t = _synthetic_csv(rels), _synthetic_meta(rels), _synthetic_e_output(rels)
        rows, meta = parse_source(csv_t, meta_t)
        curves, pan = check(rows, meta, e_t, "")
        assert [(p[0], p[1], p[2]) for p in pan] == [("a", 1, ["s2r_m30_hostB76", "s2r_m30_VB76"]),
                                                     ("b", 2, ["s2r_m30_Cs188o0_novac"])], pan
        assert min(curves["s2r_m30_Cs188o0_novac"]["dF"]) < 0 < max(curves["s2r_m30_Cs188o0_novac"]["dF"])
        cap = caption(meta)
        assert cap.startswith(HDR + "\n") and "VB76 the dashed verticals" in cap and \
            "s2r_m30_VA188 (status killed_by_gate)" in cap, cap[:600]
        # each build assert refuses its planted violation
        kl = "s2r_m30_Cs188o0_novac"
        bad = _variant(rows, kl, 30, dF_meV=repr(0.01))
        _expect("not 0 at k_last", check, bad, meta, e_t, "")
        _expect("not contiguous", check, [x for x in rows if not (x["label"] == kl and x["k"] == "7")], meta, e_t, "")
        _expect("tail_k", check, _variant(rows, "s2r_m30_VB76", None, tail_k="155"), meta, e_t, "")
        _expect("restart_start", check, _variant(rows, kl, 12, restart_start="1"), meta, e_t, "")
        _expect("differs from the printed F(k)", check, rows, meta, _bump_printed(e_t, kl, 4), "")
        _expect("header", check, rows, dict(meta, header=HDR.replace("0 of 2", "1 of 2")), e_t, "")
        _expect("not printed", check, rows, meta, e_t.replace(f"  6. {VB76} (c2)", f"  6. {VB76}x (c2)"), "")
        _expect("missing from the CSV", check, [x for x in rows if x["label"] != "s2r_m30_hostB76"],
                dict((k, v) for k, v in meta.items() if k != "end_rule.s2r_m30_hostB76"), e_t, "")
        _expect("Delta F_tail ks", check, rows, meta, e_t.replace(f"  {VB76}: F(172)", f"  {VB76}: F(171)"), "")
        _expect("suffix", check, rows, meta, e_t, "_attempt2")
        _expect("end rule", check, rows, dict(meta, **{"end_rule.s2r_m30_VB76": "unconverged_plateau"}), e_t, "")
        _expect("block", check, _variant(rows, "s2r_m30_hostB76", None, block="2", campaign="fr"), meta, e_t, "")
        _expect("CSV columns", parse_source, csv_t.replace("tail_k", "tail", 1), meta_t)
        _expect("order", check, _variant(rows, "s2r_m30_VB76", None, order="7"), meta, e_t, "")     # fix round 1
        _expect("drawn FR cell is not complete", check, rows,
                dict(meta, **{"status.s2r_m30_Cs188o0_novac": "killed_by_gate"}), e_t, "")
        # fix round 2: the eight build asserts that no planted violation reached before (F01-F08 of review round 2)
        _expect("parts not increasing", check, _variant(rows, kl, 25, part="2"), meta, e_t, "")
        _expect("outside block 5", check, rows, dict(meta, mode="hinge"), e_t, "")
        h1 = [dict(rels[0], block=5, campaign="c2", order=1, label="s2r_m30_VB136", quartet="Pb136", role="V")]
        rows_h, meta_h = parse_source(_synthetic_csv(h1), _synthetic_meta(h1, mode="hinge", suffix="_hinge") +
                                      "status.s2r_m30_VA188,complete\n")
        _expect("status rows in a hinge run", check, rows_h, meta_h, _synthetic_e_output(h1, mode="hinge"), "_hinge")
        _expect("exit code 0 or 1", check, rows, meta, e_t.replace("E exit code: 0", "E exit code: 3"), "")
        _expect("end rule differs from the E output", check, rows,
                dict(meta, **{f"end_rule.{VB76}": "accepted_plateau"}), e_t, "")
        e_mk = e_t.replace("restart part 2 at k = 11", "restart part 2 at k = 12")
        assert e_mk != e_t
        _expect("restart parts differ", check, rows, meta, e_mk, "")
        t156 = "%.2f" % curves[VB76]["dF"][156]
        e_tl = e_t.replace(f"  {VB76}: F(156) − F(final) = {t156} meV",
                           f"  {VB76}: F(156) − F(final) = {'%.2f' % (float(t156) + 0.01)} meV")
        assert e_tl != e_t
        _expect("printed Delta F_tail", check, rows, meta, e_tl, "")

        def trunc(r):                              # VB76 ending at k = 160 (< 172), its value 0 at k_last
            if r["label"] != VB76:
                return r
            v = list(r["dF"][:161])
            v[-1] = 0.0
            return dict(r, dF=v, part=r["part"][:161])
        rv = [trunc(r) for r in rels]
        rows_v, meta_v = parse_source(_synthetic_csv(rv), _synthetic_meta(rv))
        _expect("VB76 k_last below 172", check, rows_v, meta_v, _synthetic_e_output(rv), "")
        assert len({meta[f"end_rule.{lab}"] for lab in curves}) == 2            # two glyphs to tell apart
        plot(curves, pan, meta, os.path.join(tmp, "marks"), formats=(), audit=False, inspect=_check_marks)
        if render:
            src = os.path.join(tmp, "source_data")
            os.makedirs(src)
            with open(os.path.join(src, "fig_s2b_e_fk.csv"), "w") as fh:
                fh.write(csv_t)
            with open(os.path.join(src, "fig_s2b_e_fk_meta.csv"), "w") as fh:
                fh.write(meta_t)
            with open(os.path.join(tmp, "E_output.txt"), "w") as fh:
                fh.write(e_t)
            out = os.path.join(tmp, "fig_s2b_e_fk")
            r = build(src, "", os.path.join(tmp, "E_output.txt"), out, formats=("pdf",), audit=True)
            with open(out + ".caption.txt") as fh:
                assert fh.read() == r["caption"] and r["caption"].startswith(HDR + "\n")
            with open(out + ".pdf", "rb") as fh:
                pdf = fh.read()
            assert pdf.startswith(b"%PDF") and b"/Subject" in pdf
            try:                                   # the Subject, read back (PyMuPDF, if present)
                import pymupdf
            except ImportError:
                pymupdf = None
            if pymupdf is not None:
                with pymupdf.open(out + ".pdf") as doc:
                    assert doc.metadata["subject"] == r["caption"], "PDF Subject"
            h = [dict(r_, block=5, campaign="c2", order=1, label="s2r_m30_VB136", quartet="Pb136", role="V")
                 for r_ in rels[:1]]                # the hinge run: one panel
            src_h = os.path.join(tmp, "source_data_h")
            os.makedirs(src_h)
            with open(os.path.join(src_h, "fig_s2b_e_fk_hinge.csv"), "w") as fh:
                fh.write(_synthetic_csv(h))
            with open(os.path.join(src_h, "fig_s2b_e_fk_hinge_meta.csv"), "w") as fh:
                fh.write(_synthetic_meta(h, mode="hinge", suffix="_hinge"))
            with open(os.path.join(tmp, "E_hinge_output.txt"), "w") as fh:
                fh.write(_synthetic_e_output(h, mode="hinge"))
            rh = build(src_h, "_hinge", os.path.join(tmp, "E_hinge_output.txt"), os.path.join(tmp, "fig_hinge"),
                       formats=("pdf",), audit=True)
            assert [p[:2] for p in rh["panels"]] == [("a", 5)]
        if keep:
            shutil.copytree(tmp, keep, dirs_exist_ok=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("fig_s2b_e_fk self-test: ok")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Figure S2b-E: F(k) - F(final) of every relaxation read by E")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--keep", default=None, help="self-test: copy the temporary directory here")
    ap.add_argument("--suffix", default="", choices=sorted(E_OUTPUT))
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--e-output", default=None, help="default: S2/s2b/<meta e_output>")
    ap.add_argument("--out", default=None, help="output prefix; default figures/fig_s2b_e_fk<suffix>")
    ap.add_argument("--no-audit", action="store_true", help="skip the render-time panel-alignment gate")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test(keep=a.keep)
    build(a.src, a.suffix, a.e_output, a.out, audit=not a.no_audit)
    return 0


if __name__ == "__main__":
    sys.exit(main())

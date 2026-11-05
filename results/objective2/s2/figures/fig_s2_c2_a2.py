#!/usr/bin/env python
"""Figure S2-C2: the eight A2 pilot relaxations of campaign 2 and the C2 gates, as fixed by C2_OPERATIONS.md D-C2-11.

The figure was fixed before any C2 value existed (D-C2-11). Its claim is stated in the C2 result note, once C2 has
ended and its archive has been verified (D-C2-6, D-C2-10).

  a  Force criterion of each relaxation of the attempt in force: the largest Cartesian force component on the free
     atoms against the configuration k, on a log axis. Energies are neither read nor shown.
  b  Step-0 |F(k = 0) - F(SP)| of each cell and attempt against 0.5 meV, and the state of the five C2 gates.
  c  Cost: configurations and minutes per configuration of each relaxation against the C1-based planning range, and
     the projection P after relaxation 4 against the 520 node-h cap.

Blinding (D-C2-10). The script never reads an energy of a C2 relaxation, the plateau difference, the K3 value or a
quartet E_b. The A2 outputs are read with scripts/47 in count mode (no value) and by their force rows; the '!' lines
are never parsed, and the build asserts that scripts/47 read no value other than forces. A2 records and gate files
are loaded as guarded objects: a field is read by its name, a withheld field raises, and a guarded object cannot be
iterated or printed. K3 is shown by its decision and reason lists only.

Caption points fixed by D-C2-11. pw.x ends a relaxation when the change in F between consecutive configurations is
below 1e-5 Ry and every free force component is below forc_conv_thr; panel a draws only the second criterion, and QE's
own flag, not the curve, decides the end rule. Each step-0 value is a point value from one pair of calculations, and
every other point is one deterministic DFT result: there are no replicates, so no interval is drawn. A value outside an
axis is an edge arrow; in panel a every outside point has an arrow, and the value is printed at the extreme of each
excursion and at an end outside the axis. Status wording follows D-C2-10; a relaxation without an A2 record at a final
STOP is 'not started (no record)', and one refused by the hard cap or after it is 'not started (cap)' (scripts/50
writes a record only for the first refused job). After STEP0_NO_ERROR the step-0 gate file keeps fail_pending_fix and
the A2 stop state holds fail_final; the figure shows 'fail_final: no error found'.

Layout QA (optional; it does not touch the data): the panel-alignment audit comes from the external nature-figure
toolkit (~/.claude/skills/nature-figure/scripts), as for the C1 figure.

    python fig_s2_c2_a2.py --build       # (re)extract source data from the C2 archive, with the build asserts
    python fig_s2_c2_a2.py               # plot from source_data/fig_s2_c2_*.csv
    python fig_s2_c2_a2.py --self-test   # synthetic archives made from the public WP2e output; no C2 file is read
"""
import argparse, calendar, copy, csv, gzip, importlib.util, json, math, os, re, shutil, sys, tempfile, textwrap, time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
S2 = os.path.normpath(os.path.join(HERE, ".."))                          # results/objective2/s2, the archive root
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", "scripts"))
SRC = os.path.join(HERE, "source_data")
WP2E = os.path.normpath(os.path.join(HERE, "..", "..", "dopant_shell", "wp2e", "relax_m30_GA_img0"))
OUT = os.path.join(HERE, "fig_s2_c2_a2")

C2_LABELS = ("s2r_m30_VB136", "s2r_m30_hostB136", "s2r_m30_Sr136o0_novac", "s2r_m30_Sr136o0_vac",
             "s2r_m30_hostB76", "s2r_m30_VB76", "s2r_m30_Sr76o0_novac", "s2r_m30_Sr76o0_vac")    # section 11 (fixed)
GATES = (("step0@1", "gate:step0@1"), ("K2", "gate:K2"), ("step0@4", "gate:step0@4"),
         ("projection", "gate:projection@after4"), ("K3", "gate:K3"))                         # the C2 graph order
STEP0_AT = {"step0@1": ("s2_m30_VB136", "s2r_m30_VB136"), "step0@4": ("s2_m30_Sr136o0_vac", "s2r_m30_Sr136o0_vac")}
TERMINAL = ("complete", "missing", "killed_by_gate", "not_run_gate", "not_started_cap")
N_FREE_PIN = {136: {"host": 70, "V": 69, "D": 70, "DV": 69}, 76: {"host": 100, "V": 99, "D": 100, "DV": 99}}
PLAN_CONFIGS, CAP_CONFIGS, PLAN_MIN, PLAN_C2_H, CAP_H = (65, 141), 201, 4.58, (40, 86), 520.0   # D-C2-10 cost
WITHHELD = frozenset({"dF_200_180_meV", "value_meV", "Eb_A2_meV"})       # read only at the one evaluation
COLUMNS = {    # every source-data column; the step-0 dF is the one energy-valued column (a reported gate quantity)
    "fig_s2_c2_a_force.csv": ["order", "label", "k", "part", "fmax_free_Ry_bohr", "fmax_free_eV_A"],
    "fig_s2_c2_a_relaxations.csv": ["order", "label", "site", "role", "status", "line", "outcome", "end", "n_config",
                                    "k_last", "converged_at_k", "restarts", "reruns_from_zero", "interruptions",
                                    "ranks", "wall_h", "min_per_config", "n_free", "n_fixed", "part_starts",
                                    "status_text"],
    "fig_s2_c2_b_step0.csv": ["gate", "attempt", "cell", "state", "dF_meV", "passed", "outcome"],
    "fig_s2_c2_b_gates.csv": ["gate", "state", "detail", "stops_a2"],
    "fig_s2_c2_c_projection.csv": ["point", "cut", "P_h"],
    "fig_s2_c2_c_cost.csv": ["key", "value"],
    "fig_s2_c2_constants.csv": ["key", "value"]}
_MODS = {}


def modules():
    """scripts/49 and the one scripts/47 and scripts/46 objects it loads (so that READS is the reader's counter)."""
    if not _MODS:
        sys.path.insert(0, SCRIPTS)
        s = importlib.util.spec_from_file_location("g49", os.path.join(SCRIPTS, "49_s2_gates.py"))
        g = importlib.util.module_from_spec(s); s.loader.exec_module(g)
        _MODS.update(g49=g, q47=g.dep("q47"), c46=g.dep("c46"))
        q = _MODS["q47"]
        assert tuple(g.A2_ORDER["c2"][:8]) == C2_LABELS and dict(g.STEP0_PAIRS) == dict(STEP0_AT.values())
        assert {x for q in g.K3_QUARTETS.values() for x in q.values()} == set(C2_LABELS)   # Ca136 left C2 by G1
        assert (q.FORC_CONV_THR, q.K_CAP, q.STEP0_TOL_MEV) == (7.8e-4, 200, 0.5)
        assert abs(q.FORC_CONV_THR * q.RY_EV / q.BOHR_A - 0.02005) < 5e-6 and g.RULES["HARD_CAP_H"] == CAP_H
    return _MODS["g49"], _MODS["q47"], _MODS["c46"]


# ---------------------------------------------------------------- guarded reading (D-C2-10)
class Blinded(PermissionError):
    pass


class Guarded:
    """A C2 A2 record or gate file. Fields are read one by one by name; a withheld field raises; the object is never
    iterated, compared or printed. open() hands a subtree to the gate code only if no withheld field is in it."""
    __slots__ = ("_d", "_p")

    def __init__(self, d, path):
        self._d, self._p = d, path

    def _wrap(self, v, k):
        if isinstance(v, dict):
            return Guarded(v, f"{self._p}/{k}")
        return [self._wrap(x, f"{k}[]") for x in v] if isinstance(v, list) else v

    def get(self, k, default=None):
        if k in WITHHELD:
            raise Blinded(f"{self._p}/{k} is withheld until the one evaluation (D-C2-10)")
        return self._wrap(self._d.get(k, default), k)

    def has(self, k):
        return k in self._d

    def open(self):
        def scan(x):
            if isinstance(x, dict):
                if WITHHELD & set(x):
                    raise Blinded(f"{self._p} holds a withheld field: it is read by field name only")
                for v in x.values():
                    scan(v)
            elif isinstance(x, list):
                for v in x:
                    scan(v)
        scan(self._d)
        return copy.deepcopy(self._d)

    def _refuse(self, *a, **kw):
        raise Blinded(f"{self._p} is read by field name only (D-C2-10)")

    __iter__ = __repr__ = __str__ = __eq__ = __len__ = __contains__ = keys = items = values = _refuse
    __hash__ = None

    def __bool__(self):
        return True


def guarded(path):
    return Guarded(json.load(open(path)), os.path.basename(path)) if os.path.exists(path) else None


def applied(gdir, gid):
    """The applied-gate marker and the gate file the runner kept beside it (scripts/50 run_gate), or None."""
    m = os.path.join(gdir, re.sub(r"[^A-Za-z0-9_.-]", "_", gid) + ".json")
    if not os.path.exists(m):
        return None
    mk, g = guarded(m), guarded(m[:-5] + ".gate.json")
    assert g is not None and mk.get("id") == gid and mk.get("gate") == g.get("gate") and g.get("campaign") == "c2", m
    assert mk.get("decision").open() == g.get("decision").open() and mk.get("attempt") == g.get("attempt"), m
    return {"marker": mk, "gate": g, "attempt": int(g.get("attempt") or 1)}


# ---------------------------------------------------------------- force-only reader (D-C2-11 a)
def free_atoms(q47, in_paths):
    """Free atoms: the ATOMIC_POSITIONS rows without if_pos flags (the writer puts '0 0 0' on fixed atoms only)."""
    sets = []
    for p in in_paths:
        d = q47.parse_input_text(q47.a32.read_text(p))
        nat, rows = int(d["namelists"]["system"]["nat"]), d["cards"]["ATOMIC_POSITIONS"]["rows"]
        assert len(rows) == nat, p
        for i, r in enumerate(rows):
            assert len(r) == 4 or (len(r) == 7 and r[4:] == ["0", "0", "0"]), (p, i, r[4:])
        sets.append((nat, tuple(i for i, r in enumerate(rows) if len(r) == 4)))
    assert sets and all(s == sets[0] for s in sets), "the free-atom set differs between parts"
    return sets[0][0], list(sets[0][1])


def force_curve(q47, label, outs, mapping, ranks, nat, free):
    """k from parse_relax(read='counts') (no value); per configuration, the force rows of _segment / _read_forces."""
    before = dict(q47.READS)
    rel = q47.parse_relax(outs, read="counts", k_cap=q47.K_CAP, mapping=mapping, ranks=ranks, label=label)
    assert dict(q47.READS) == before, "count mode read a value"
    assert rel["usable"], f"{label}: {rel['unusable_reason']}"
    rep = bool((mapping or {}).get("restart_repeats_last", False))
    pts, starts = [], []
    for pi, (path, part) in enumerate(zip(outs, rel["parts"])):
        txt = q47.a32.read_text(path)
        assert q47._header(txt)["nat"] in (None, nat), path         # a part may end before its header
        cfg, _ = q47._segment(txt, nat)
        n = int(part["n_config"])
        kept, ks = cfg[:n], (list(range(part["k_first"], part["k_first"] + n)) if n else [])
        if pi > 0 and rep and kept:                     # a repeated first configuration belongs to the part before
            kept, ks = kept[1:], ks[1:]
        if pi > 0 and ks:
            starts.append(ks[0])
        for k, c in zip(ks, kept):
            f = q47._read_forces(txt, *c["forces"])     # Ry/bohr, as printed
            assert f.shape == (nat, 3), (path, k)
            pts.append((k, float(np.abs(f[free]).max()), pi + 1))
    assert [k for k, _, _ in pts] == rel["ks"], label
    return rel, pts, starts


def free_source(arch, g49, c46, lab):
    """n_free (and n_fixed) of the start source the runner used: the region file for host_R, else the C1 record, read
    with the blinded loader of scripts/46 (it removes every MACE energy)."""
    c = g49.a2_cell(lab)
    if c["kind"] == "host":
        reg = json.load(open(os.path.join(arch, "c1", "regions", f"{c['pilot']}_{c['L']}{c['site']}.json")))
        return int(reg["n_free"]), None
    rec = c46.load_record(os.path.join(arch, "c1", "records", f"{g49.a1_start_of(lab)}.json"))
    assert "E_mace_eV" not in json.dumps(rec)
    return int(rec["n_free"]), int(rec["n_fixed"])


# ---------------------------------------------------------------- build
def _epoch(stamp):
    return float(calendar.timegm(time.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")))


def status_text(row):
    """The D-C2-10 wording of a relaxation's status (a record pending at a final STOP is 'stopped at k = k_last')."""
    st = row["status"]
    if st == "complete":
        return "complete" if row["outcome"] != "unconverged_early" else \
            f"early end, {row['end']}" + ("" if row["k_last"] != "" else ", no configuration")
    if st in TERMINAL or st in ("no record", "not_started_cap"):
        return STATUS[st]
    return f"stopped at k = {row['k_last']}" if row["k_last"] != "" else "stopped before k = 0"


def relaxations(arch, g49, q47, c46):
    c2 = os.path.join(arch, "c2")
    lay = c46.Layout(kind="archive", root=arch)
    mapping = json.load(open(os.path.join(arch, "c1", "smoke.json")))["mapping"]
    hc = guarded(os.path.join(c2, "HARD_CAP.json"))                       # the runner's hard-cap refusal, if any
    capped = hc.get("job") if hc is not None else None
    rows, pts, recs, cap_seen = [], [], {}, False
    for order, lab in enumerate(C2_LABELS, 1):
        c = g49.a2_cell(lab)
        rec = guarded(os.path.join(c2, "raw", f"{lab}.a2.json"))
        recs[lab] = rec
        st = rec.get("status") if rec is not None else "no record"
        cap_seen = cap_seen or st == "not_started_cap" or capped == f"a2:{lab}"
        if rec is None and cap_seen:
            st = "not_started_cap"                    # later jobs refused by the cap get no record (scripts/50)
        er = rec.get("end_rule") if rec is not None else None
        row = {k: "" for k in COLUMNS["fig_s2_c2_a_relaxations.csv"]}
        row.update(order=order, label=lab, site=c["site"], role=c["kind"], status=st, line="none")
        ranks = None
        if rec is not None:
            ranks = rec.get("layout").get("ranks") if rec.get("layout") is not None else None
            assert ranks in (None, 64), (lab, "rank count")                # the C1 throughput layout
            row.update(restarts=rec.get("restarts"), reruns_from_zero=rec.get("reruns_from_zero"),
                       interruptions=len(rec.get("interruptions") or []), ranks="" if ranks is None else ranks)
        if st == "complete":
            row.update(outcome=er.get("outcome"), end=er.get("end") or "", n_config=int(rec.get("n_config")),
                       k_last=rec.get("k_last") if rec.get("k_last") is not None else "",
                       converged_at_k=rec.get("converged_at_k") if rec.get("converged_at_k") is not None else "",
                       wall_h=repr(float(rec.get("wall_h"))), min_per_config=repr(float(rec.get("min_per_config"))))
        outs = lay.a2_parts("c2", lab)
        if rec is None or not outs or not (st == "complete" or st not in TERMINAL):
            row["status_text"] = status_text(row)
            rows.append(row); continue
        names = [os.path.basename(p) for p in outs]
        assert names == [f"{lab}.p{n}.out.gz" for n in range(1, len(outs) + 1)], names
        nat, free = free_atoms(q47, [os.path.join(c2, "raw", f"{lab}.p{n}.in.gz") for n in range(1, len(outs) + 1)])
        nf, nfix = free_source(arch, g49, c46, lab)
        assert len(free) == nf == N_FREE_PIN[c["site"]][c["kind"]], (lab, "free-atom count", len(free), nf)
        assert nfix is None or nat - len(free) == nfix, (lab, "fixed-atom count", nat, nfix)
        rel, cur, starts = force_curve(q47, lab, outs, mapping, ranks, nat, free)
        ks = [k for k, _, _ in cur]
        if st == "complete":
            assert ks == list(range(int(rec.get("n_config")))), (lab, "k values differ from n_config")
            oc = er.get("outcome")
            assert ks or oc == "unconverged_early", (lab, "an accepted or capped relaxation without configurations")
            if oc == "accepted_converged":
                assert rec.get("converged_at_k") == rel["converged_at_k"] == ks[-1], (lab, "converged_at_k")
                assert cur[-1][1] <= q47.FORC_CONV_THR, (lab, "converged above forc_conv_thr", cur[-1][1])
            elif oc in ("accepted_plateau", "unconverged_cap"):
                assert ks[-1] == q47.K_CAP, lab
            elif oc == "unconverged_early":
                assert (ks[-1] if ks else None) == rec.get("k_last") and not rel["qe_converged"], (lab, "k_last")
            row["line"] = "complete"
        else:                                         # pending at a final STOP: its n_config lags until a part ends
            n = int(rec.get("n_config") or 0)
            assert ks[:n] == list(range(n)), (lab, "k values differ from the record's n_config")
            row.update(line="stopped" if ks else "none", k_last=ks[-1] if ks else "")
        row.update(n_free=len(free), n_fixed=nat - len(free), part_starts=" ".join(map(str, starts)))
        row["status_text"] = status_text(row)
        rows.append(row)
        pts += [{"order": order, "label": lab, "k": k, "part": p, "fmax_free_Ry_bohr": repr(f),
                 "fmax_free_eV_A": repr(f * q47.RY_EV / q47.BOHR_A)} for k, f, p in cur]
    return rows, pts, recs


def step0_state(e, sp, tol):
    res = e["gate"].get("result")
    assert res.get("cells").has(sp), sp
    cell = res.get("cells").get(sp)
    dF, ok, oc = cell.get("dF_meV"), cell.get("passed"), res.get("outcome")
    assert ok is (dF is not None and abs(dF) <= tol), (sp, "passed differs from |dF| <= 0.5 meV")
    assert oc == e["marker"].get("decision").get("step0").get("outcome") and int(res.get("attempt")) == e["attempt"]
    if ok:
        assert oc == "pass"
        return "pass", dF, ok, oc
    assert oc in ("fail_pending_fix", "fail_final") and (e["attempt"] == 1 or oc == "fail_final"), oc
    return (f"fail ({oc})" if dF is not None else f"fail: value missing ({oc})"), dF, ok, oc


def step0_in_force(c2):
    """The step-0 outcome of the A2 stop state (state_end.json, leaf fields), else the runner's STEP0_NO_ERROR log
    line: STEP0_NO_ERROR turns fail_pending_fix into fail_final in the state only (scripts/50 preconditions)."""
    st = guarded(os.path.join(c2, "state_end.json"))
    if st is not None and st.get("step0") is not None:
        return st.get("step0").get("outcome"), st.get("step0").get("no_error_found") is True
    log = os.path.join(c2, "logs", "campaign.log")
    ne = os.path.exists(log) and any("STEP0_NO_ERROR: step-0 fail_final" in ln for ln in open(log))
    return ("fail_final" if ne else None), ne


def gates(arch, g49, q47, recs):
    c2 = os.path.join(arch, "c2")
    gdir = os.path.join(c2, "gates_applied")
    s0dir = os.path.join(c2, "step0_attempt1", "gates_applied")
    repeat = os.path.isdir(s0dir)
    out, s0rows, proj, stopped_by, last0 = [], [], [], None, None
    for name, gid in GATES:
        e = applied(gdir, gid)
        state, detail, stops = "not reached", "", False
        if e is None:
            if name in STEP0_AT and stopped_by is None:
                r = recs.get(STEP0_AT[name][1])
                if r is not None and r.get("status") in ("complete", "missing", "killed_by_gate") \
                        and not r.get("k0_seen") and int(r.get("n_config") or 0) < 1:
                    state = "skipped (no k = 0)"
        elif name in STEP0_AT:
            assert e["attempt"] == (2 if repeat else 1), (name, e["attempt"])
            state, dF, ok, oc = step0_state(e, STEP0_AT[name][0], q47.STEP0_TOL_MEV)
            stops, last0 = oc in ("fail_pending_fix", "fail_final"), (len(out), oc, dF, e["attempt"])
        elif name == "K2":
            res, dec = e["gate"].get("result"), e["marker"].get("decision").get("K2")
            oc = res.get("outcome")
            assert g49.k2_eval({"outcome": oc})["K2"] == dec == res.get("K2"), "K2 differs from k2_eval"
            r1 = recs.get(C2_LABELS[0])
            ro = (r1.get("end_rule").get("outcome") if r1.get("status") == "complete" else r1.get("status")) \
                if r1 is not None else None
            assert ro is None or g49.k2_eval({"outcome": ro})["K2"] == dec, "K2 differs from relaxation 1's record"
            state, detail, stops = f"{dec} ({oc})", oc, dec == "fail"
            if ro is not None and oc != ro and r1.get("status") == "complete":   # RESOLVE 'unconverged': the gate
                op = str(r1.get("end_rule").get("end") or "")                      # re-reads the outputs
                assert oc == "incomplete" and op.endswith("(operator)"), "K2 differs from relaxation 1's record"
                state = f"{dec} ({ro}, operator; gate read {oc})"
            elif ro is not None and oc != ro:          # relaxation 1 refused by the hard cap: no usable output
                assert oc in ("missing", "incomplete"), "K2 differs from relaxation 1's record"
                state = f"{dec} ({oc}; record: {ro})"
        elif name == "projection":
            g, dec = e["gate"], e["marker"].get("decision")
            res = g.get("result")
            assert res.get("point") == "after4"
            st_in, inputs = g.get("state_in").open(), res.get("inputs").open()
            a2c = [x.open() for x in res.get("a2_completed")]
            done = [x["label"] for x in a2c]
            for x in a2c:
                r = recs.get(x["label"])
                assert r is not None and r.get("status") == "complete" and int(r.get("n_config")) == x["n_config"] \
                    and math.isclose(float(r.get("wall_h")), x["wall_h"], rel_tol=1e-12), x["label"]

            def project(s):
                return g49.projection({**g49.plan_work(s, "after4", done=done), **inputs, "a2_completed": a2c})["P_h"]
            P0 = float(res.get("P_initial_h"))
            assert math.isclose(project(copy.deepcopy(st_in)), P0, rel_tol=1e-12, abs_tol=1e-9), "P_initial_h"
            st = copy.deepcopy(st_in)
            cuts, rc = g49.cut_order(st, project, "after4"), [x.open() for x in res.get("cuts")]
            assert [c["cut"] for c in cuts] == [c["cut"] for c in rc] and all(
                math.isclose(a[k], b[k], rel_tol=1e-12, abs_tol=1e-9) for a, b in zip(cuts, rc)
                for k in ("P_before_h", "P_after_h")), "projection cuts differ from cut_order"
            assert g49.c4_planned(st) == dec.get("c4_run"), "c4_run differs"
            assert [c["cut"] for c in st.get("cuts") or []] == [c.get("cut") for c in dec.get("cuts") or []]
            ids = [str(c["cut"]) for c in rc if c["cut"] is not None]
            state = f"cuts {', '.join(ids)}; c4_run {str(dec.get('c4_run')).lower()}" if ids else "no cut"
            if any(c["cut"] is None for c in rc):
                detail = "no applicable cut left; the hard-cap job-start rule applies"
            proj = [{"point": "initial", "cut": "", "P_h": repr(P0)}] + \
                [{"point": "after cut", "cut": "" if c["cut"] is None else c["cut"], "P_h": repr(float(c["P_after_h"]))}
                 for c in rc]
        else:                                                              # K3: decision and reason lists only
            res, dec = e["gate"].get("result"), e["marker"].get("decision").get("K3")
            cf, ef = list(res.get("checks_failed") or []), list(res.get("end_rule_failed") or [])
            assert dec == res.get("K3") and dec in ("pass", "fail_replan", "a1_only")
            assert (not cf or dec == "fail_replan") and (cf or not ef or dec == "a1_only"), "K3 reasons"
            state = {"pass": "pass", "a1_only": "not evaluable (a1_only)"}.get(dec) or \
                ("fail (fail_replan): checks failed" if cf else "fail (fail_replan): value ≤ +25.7 meV")
            detail, stops = "; ".join(cf or ef), dec != "pass"
        if stops and stopped_by is None:
            stopped_by = name
        out.append({"gate": name, "state": state, "detail": detail, "stops_a2": stops})
    s_oc, no_err = step0_in_force(c2)
    if last0 is not None and s_oc is not None:                 # the last applied step-0 decision against the state
        i, oc, dF, att = last0
        if oc == "fail_pending_fix" and s_oc == "fail_final":
            assert no_err and att == 1, "step-0 fail_final in the state without STEP0_NO_ERROR"
            out[i]["state"] = ("fail" if dF is not None else "fail: value missing") + " (fail_final: no error found)"
            out[i]["detail"] = "STEP0_NO_ERROR: A2 stops, C3 runs, S2 reports the A1 tier only"
        else:
            assert s_oc == oc, "the step-0 outcome of the state differs from the last step-0 gate file"
    for att, d in ((1, s0dir), (2, gdir)) if repeat else ((1, gdir),):
        for name in STEP0_AT:
            e = applied(d, dict(GATES)[name])
            st0 = next(r["state"] for r in out if r["gate"] == name) if d == gdir else "not reached"
            row = {"gate": name, "attempt": att, "cell": STEP0_AT[name][0], "state": st0, "dF_meV": "", "passed": "",
                   "outcome": ""}
            if e is not None:
                assert e["attempt"] == att, (name, att)
                s, dF, ok, oc = step0_state(e, STEP0_AT[name][0], q47.STEP0_TOL_MEV)
                row.update(state=s if d != gdir else st0, dF_meV="" if dF is None else repr(float(dF)), passed=ok,
                           outcome=oc)
            s0rows.append(row)
    return out, s0rows, proj


def cost(arch):
    """C2 node-hours (D-C2-10): c2-tagged boots of the last C2 ledger; one boot started before the C1 CAMPAIGN_DONE
    is split at that time. Manual rows and rows the ledger could not time (hours None) are listed separately."""
    led = json.load(open(os.path.join(arch, "c2", "ledger.json")))
    done = [ln for ln in open(os.path.join(arch, "c1", "logs", "campaign.log")) if "CAMPAIGN_DONE" in ln]
    t_done = _epoch(re.match(r"\[(\S+)\]", done[-1]).group(1))
    c2h, early, man_n, man_h, nb, prob = 0.0, 0, 0, 0.0, 0, 0
    for b in led["boots"]:
        if b.get("hours") is None:
            prob += 1; continue
        if b.get("manual") is True:
            man_n += 1; man_h += float(b["hours"]); continue
        if "c2" not in (b.get("campaigns") or []):
            continue
        nb += 1
        h = float(b["hours"])
        if float(b["btime"]) < t_done:
            early += 1
            h -= (t_done - float(b["btime"])) / 3600.0
            assert 0.0 <= h <= float(b["hours"]), "a split boot ends before the C1 CAMPAIGN_DONE"
        c2h += h
    assert early <= 1, "more than one c2-tagged boot started before the C1 CAMPAIGN_DONE"
    return [{"key": k, "value": v} for k, v in (
        ("c2_node_h", repr(c2h)), ("c2_boots", nb), ("split_at_c1_done", early == 1), ("manual_rows", man_n),
        ("manual_rows_h", repr(man_h)), ("problem_rows", prob), ("ledger_complete", led.get("complete") is True),
        ("H_spent_h", repr(float(led["H_spent_h"]))), ("ledger_now_utc", led["now_utc"]),
        ("ledger_problems", len(led.get("problems") or [])), ("plan_c2_node_h", f"{PLAN_C2_H[0]}-{PLAN_C2_H[1]}"))]


def build(arch=S2, src=SRC):
    g49, q47, c46 = modules()
    assert not any(v for k, v in q47.READS.items()), "a value was read before the build"
    rows, pts, recs = relaxations(arch, g49, q47, c46)
    gt, s0, proj = gates(arch, g49, q47, recs)
    cs = cost(arch)
    const = [{"key": "forc_conv_thr_Ry_bohr", "value": repr(q47.FORC_CONV_THR)},
             {"key": "forc_conv_thr_eV_A", "value": repr(q47.FORC_CONV_THR * q47.RY_EV / q47.BOHR_A)},
             {"key": "k_cap", "value": q47.K_CAP}, {"key": "step0_tol_meV", "value": repr(q47.STEP0_TOL_MEV)}]
    assert q47.READS["F"] == 0 and q47.READS["ase"] == 0 and set(k for k, v in q47.READS.items() if v) <= {"forces"}
    os.makedirs(src, exist_ok=True)
    for fn, data in (("fig_s2_c2_a_force.csv", pts), ("fig_s2_c2_a_relaxations.csv", rows),
                     ("fig_s2_c2_b_step0.csv", s0), ("fig_s2_c2_b_gates.csv", gt),
                     ("fig_s2_c2_c_projection.csv", proj), ("fig_s2_c2_c_cost.csv", cs),
                     ("fig_s2_c2_constants.csv", const)):
        assert all(list(r) == COLUMNS[fn] for r in data), fn
        with open(os.path.join(src, fn), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLUMNS[fn]); w.writeheader(); w.writerows(data)
    print("source data written:", len(pts), "force points,", sum(r["line"] != "none" for r in rows), "lines,",
          "gates:", "; ".join(f"{r['gate']} {r['state']}" for r in gt))
    return {"rows": rows, "gates": gt, "step0": s0, "projection": proj, "cost": cs, "points": pts}


# ---------------------------------------------------------------- plot
ROLE = {"host": "host", "V": "V", "D": "D", "DV": "D+V"}      # region cells host_R, V+_R, D, D+V+ (S2_PLAN section 11)
STATUS = {"missing": "missing", "killed_by_gate": "killed by a gate", "not_run_gate": "not run (gate)",
          "not_started_cap": "not started (cap)", "no record": "not started (no record)", "complete": "complete"}
SHORT = {**STATUS, "killed_by_gate": "killed (gate)", "not_started_cap": "no start (cap)",
         "no record": "no record"}                                       # short forms that fit left of the band
GATE_NAME = {"step0@1": "Step-0 at 1", "K2": "K2", "step0@4": "Step-0 at 4", "projection": "Projection after 4",
             "K3": "K3"}


def plot(src=SRC, out=OUT, formats=("pdf", "svg", "png", "tiff"), audit=True):
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    sys.path.insert(0, os.path.expanduser("~/.claude/skills/nature-figure/scripts"))
    try:      # layout QA from the nature-figure toolkit; optional, it does not touch the data
        from audit_panel_alignment import require_matplotlib_panel_alignment
    except ImportError:
        require_matplotlib_panel_alignment = None
        print("note: panel-alignment audit unavailable; figure rendered without it")
    mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                         "svg.fonttype": "none", "pdf.fonttype": 42, "font.size": 7, "axes.spines.right": False,
                         "axes.spines.top": False, "axes.linewidth": 0.8,
                         "legend.frameon": False, "xtick.major.width": 0.8, "ytick.major.width": 0.8})
    rd = lambda fn: list(csv.DictReader(open(os.path.join(src, fn))))
    R, P, S0, G, PJ = (rd("fig_s2_c2_a_relaxations.csv"), rd("fig_s2_c2_a_force.csv"), rd("fig_s2_c2_b_step0.csv"),
                       rd("fig_s2_c2_b_gates.csv"), rd("fig_s2_c2_c_projection.csv"))
    C = {r["key"]: r["value"] for r in rd("fig_s2_c2_c_cost.csv")}
    K = {r["key"]: r["value"] for r in rd("fig_s2_c2_constants.csv")}            # scripts/47 values, via --build
    QC = {136: "#2f6db5", 76: "#d08a2e"}                                    # quartet colours
    LS = {"host": "-", "V": (0, (4, 1.6)), "D": (0, (1, 1.3)), "DV": (0, (5, 1.4, 1, 1.4))}
    GL = {"accepted_converged": ("o", 15), "accepted_plateau": ("^", 17), "unconverged_cap": ("X", 18),
          "unconverged_early": ("s", 13)}
    NEU, FAIL, INK = "#9aa3ad", "#c4553a", "#3a3a3a"
    THR = float(K["forc_conv_thr_eV_A"])                                    # forc_conv_thr in eV/A (scripts/47)
    YLO, YHI = 1e-3, 10.0
    name = lambda r: f"{r['order']}  {ROLE[r['role']]} Pb{r['site']}"

    ARROW = {"right": r"$\rightarrow$", "top": r"$\uparrow$", "bottom": r"$\downarrow$"}   # no end glyph uses these

    def edge(ax, x, y, where, txt, col):                                  # a value outside the axis: arrow + value
        if where == "right":
            ax.plot([0.985], [y], marker=ARROW["right"], ms=6, color=col, transform=ax.get_yaxis_transform(),
                    clip_on=False)
            ax.text(0.955, y, txt, transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=6, color=col)
        else:
            yy = 0.975 if where == "top" else 0.025
            ax.plot([x], [yy], marker=ARROW[where], ms=6, color=col, transform=ax.get_xaxis_transform(),
                    clip_on=False)
            if txt:                                    # left of the arrow near k = 200, so it stays on the canvas
                right = x > 170
                ax.text(x - 3 if right else x + 3, yy if where == "top" else 0.07, txt, ha="right" if right else "left",
                        transform=ax.get_xaxis_transform(), va="center", fontsize=6, color=col)

    fig = plt.figure(figsize=(7.205, 6.299))                               # 183 mm x 160 mm
    gs = fig.add_gridspec(3, 3, height_ratios=[1.35, 1.0, 0.62], left=0.075, right=0.985, bottom=0.06, top=0.958,
                          hspace=0.62, wspace=0.42)
    a = fig.add_subplot(gs[0, :]); b1 = fig.add_subplot(gs[1, 0]); b2 = fig.add_subplot(gs[2, 0])
    c1 = fig.add_subplot(gs[1, 1]); c2 = fig.add_subplot(gs[1, 2], sharey=c1); c3 = fig.add_subplot(gs[2, 1:])

    # (a) largest free-atom force component against k; QE's own flag, not this curve, decides the end rule
    hl, ll = [], []
    for r in R:
        o, site = int(r["order"]), int(r["site"])
        lab = name(r) + ("  (K2)" if o == 1 else "")
        if r["status_text"] != "complete":                                 # D-C2-10 wording, made by --build
            lab += f": {r['status_text']}"
        q = [(int(p["k"]), float(p["fmax_free_eV_A"])) for p in P if int(p["order"]) == o]
        if r["line"] == "none" or not q:
            hl.append(Line2D([], [], color="none")); ll.append(lab)
            continue
        k, f = np.array([x for x, _ in q]), np.array([y for _, y in q])
        col = QC[site]
        a.plot(k, f, color=col, ls=LS[r["role"]], lw=0.9, zorder=3)
        for s in (int(x) for x in r["part_starts"].split()):              # restart part boundaries
            a.plot([s], [f[list(k).index(s)]], marker="|", ms=6, mew=1.0, color=col, zorder=4)
        fe = min(max(f[-1], YLO), YHI)                                   # an end outside the axis sits on its edge
        if r["line"] == "complete" and r["outcome"] in GL:
            mk, sz = GL[r["outcome"]]
            a.scatter([k[-1]], [fe], marker=mk, s=sz, color=col, edgecolor="white", linewidth=0.4, zorder=5,
                      clip_on=False)
        elif r["line"] == "stopped":                                     # open end: the record is still pending
            a.scatter([k[-1]], [fe], marker="o", s=15, facecolor="white", edgecolor=col, linewidth=0.9, zorder=5,
                      clip_on=False)
        for sel, where in ((f > YHI, "top"), (f < YLO, "bottom")):       # every outside point gets an edge arrow;
            idx = np.flatnonzero(sel)                                      # the value of each excursion's extreme
            for run in np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1) if idx.size else []:   # and of an outside
                i = run[np.argmax(f[run])] if where == "top" else run[np.argmin(f[run])]          # end is printed
                for j in run:
                    edge(a, k[j], None, where, f"{f[j]:.3g} eV/Å" if j == i or j == len(f) - 1 else "", col)
        hl.append(Line2D([], [], color=col, ls=LS[r["role"]], lw=0.9)); ll.append(lab)
    a.axhline(THR, color=INK, lw=0.6, ls=(0, (3, 2)), zorder=2)
    a.text(1, THR / 1.15, f"forc_conv_thr: {float(K['forc_conv_thr_Ry_bohr']):g} Ry/bohr = {THR:.4g} eV/Å",
           fontsize=6, color=INK, va="top")
    a.axvline(200, color=NEU, lw=0.6, ls=":", zorder=1)
    a.set_yscale("log"); a.set_ylim(YLO, YHI); a.set_xlim(-2, 202)
    a.yaxis.set_major_locator(mpl.ticker.FixedLocator([1e-3, 1e-2, 1e-1, 1, 10]))
    a.yaxis.set_major_formatter(mpl.ticker.FixedFormatter(["0.001", "0.01", "0.1", "1", "10"]))
    a.yaxis.set_minor_formatter(mpl.ticker.NullFormatter())
    a.set_xlabel("Configuration k (BFGS step, counted across restarts); dotted: k = 200 (cap)")
    a.set_ylabel("Largest free-atom force component (eV/Å)")
    a.set_title("A2 relaxations of C2: force criterion against k (energies not shown)", fontsize=7, pad=4)
    a.legend(hl, ll, loc="upper right", bbox_to_anchor=(0.965, 0.94), ncol=2, fontsize=6, handlelength=2.6,
                  columnspacing=1.2, borderaxespad=0.3, title="relaxation in C2 order (V: iodide vacancy, q = +1); "
                  "colour: quartet; line: cell", title_fontsize=6)
    gh = [a.scatter([], [], marker=GL[o][0], s=GL[o][1], color=INK) for o in GL] + \
        [a.scatter([], [], marker="o", s=15, facecolor="white", edgecolor=INK, linewidth=0.9),
         Line2D([], [], marker="|", ms=6, mew=1.0, color=INK, ls="none"),
         Line2D([], [], marker=ARROW["top"], ms=6, color=INK, ls="none")]
    pa = a.get_position()                        # below the axis label, so the plot area stays free for arrows
    fig.legend(gh, ["accepted: converged", "accepted: plateau", "unconverged: cap", "unconverged: early end",
                    "stopped (pending)", "restart", "off-axis value"], loc="upper center", ncol=7, fontsize=6,
               bbox_to_anchor=((pa.x0 + pa.x1) / 2, pa.y0 - 0.052), handletextpad=0.3, columnspacing=1.0,
               borderaxespad=0.0)

    # (b) step-0 |dF| of each cell and attempt (one pair of calculations each: no interval), and the gate strip
    n0 = len(S0)
    for i, r in enumerate(S0):
        y = n0 - 1 - i
        if r["dF_meV"] != "":
            v = float(r["dF_meV"]); ok = r["passed"] == "True"
            if abs(v) > 1.0:
                edge(b1, None, y, "right", f"{v:+.2f}".replace("-", "−"), FAIL)
            else:
                b1.scatter([abs(v)], [y], s=20, zorder=3, **(dict(color=INK, edgecolor="white", linewidth=0.4) if ok
                                                             else dict(facecolor="white", edgecolor=FAIL,
                                                                       linewidth=1.0)))
                b1.annotate(f"{v:+.2f}".replace("-", "−"), (abs(v), y), xytext=(0, 5), textcoords="offset points",
                            ha="left" if abs(v) < 0.08 else "center", fontsize=6, color=INK if ok else FAIL)
        else:
            b1.text(0.53, y, "\n".join(textwrap.wrap(r["state"], 21)), va="center", fontsize=6, linespacing=1.1,
                    color=FAIL if "fail" in r["state"] else NEU)
    b1.axvline(0.5, color=INK, lw=0.6, ls=(0, (3, 2)), zorder=1)
    b1.set_xlim(0, 1); b1.set_ylim(-0.6, n0 - 0.4)
    b1.set_yticks(range(n0), [f"at {r['gate'][-1]}\nattempt {r['attempt']}" for r in S0][::-1])
    b1.set_xlabel("|F(k = 0) − F(SP)| (meV)\ndashed: 0.5 meV")
    b1.set_title("Step-0: at 1, V Pb136; at 4, D+V Pb136", fontsize=7, pad=4)
    b2.set_axis_off(); b2.set_xlim(0, 1)
    b2.text(0, 0, "C2 gates (attempt in force)", fontsize=7, va="top")
    y = 1.35                                                                # in text lines from the top
    for r in G:
        col = FAIL if r["state"].startswith("fail") else \
            INK if r["state"].startswith(("pass", "no cut", "cuts")) else NEU
        b2.text(0, y, GATE_NAME[r["gate"]], fontsize=6, va="top", color=INK)
        w = textwrap.wrap(r["state"], 30)
        b2.text(0.42, y, "\n".join(w), fontsize=6, va="top", color=col, linespacing=1.15)
        y += 1.15 * len(w) + 0.25
    b2.set_ylim(max(y, 8.5), -0.2)

    # (c) cost against the C1-based planning range (S2_PLAN section 16 [I]; D-C2-10)
    ys = {int(r["order"]): 8 - int(r["order"]) for r in R}
    for axx, key, lim, ref in ((c1, "n_config", (0, 210), None), (c2, "min_per_config", (0, 10), PLAN_MIN)):
        if key == "n_config":
            axx.axvspan(*PLAN_CONFIGS, color="#e8ebef", zorder=0, lw=0)
            axx.axvline(CAP_CONFIGS, color=INK, lw=0.6, ls=(0, (3, 2)))
        else:
            axx.axvline(ref, color=INK, lw=0.6, ls=(0, (3, 2)))
        for r in R:
            y = ys[int(r["order"])]
            if r[key] == "":
                if key == "n_config":
                    t = "stopped" if r["status_text"].startswith("stopped") else SHORT.get(r["status"], r["status"])
                    axx.text(lim[0] + 3, y, t, va="center", fontsize=6, color=NEU)
                continue
            v = float(r[key]); col = QC[int(r["site"])]
            mk, sz = GL.get(r["outcome"], ("o", 15))
            if v > lim[1]:
                edge(axx, None, y, "right", f"{v:.3g}", col)
            else:
                axx.scatter([v], [y], marker=mk, s=sz, color=col, edgecolor="white", linewidth=0.4, zorder=3)
        axx.set_xlim(*lim)
    c1.set_ylim(-0.6, 7.6)
    c1.set_yticks([ys[int(r["order"])] for r in R], [name(r) for r in R])
    plt.setp(c2.get_yticklabels(), visible=False)
    c1.set_xlabel("Configurations per relaxation\nband: plan 65–141; dashed: cap 201")
    c2.set_xlabel("Wall minutes per configuration\ndashed: C1 rate, 4.58 min")
    c1.set_title("Cost per relaxation", fontsize=7, pad=4); c2.set_title("Rate (64 ranks)", fontsize=7, pad=4)
    c3.axvline(CAP_H, ymax=0.36, color=INK, lw=0.6, ls=(0, (3, 2)))
    if PJ:                                       # every value is printed in the sequence line; markers carry the id
        seq, beyond = [], []
        for r in PJ:
            v, init = float(r["P_h"]), r["point"] == "initial"
            if r["cut"] == "" and not init:
                seq.append("no applicable cut left"); continue
            ident = "P" if init else str(r["cut"])
            seq.append(f"P = {v:.0f}" if init else f"cut {ident}: {v:.0f}")
            if v > 600:
                beyond.append(f"{ident} {v:.0f}"); continue
            c3.scatter([v], [0.16], s=20, zorder=3, clip_on=False,
                       **(dict(color=INK, edgecolor="white", linewidth=0.4) if init
                          else dict(facecolor="white", edgecolor=INK, linewidth=0.9)))
            c3.annotate(ident, (v, 0.16), xytext=(0, 4), textcoords="offset points", fontsize=6, color=INK,
                        ha="right" if v > 585 else "left" if v < 15 else "center")
        if beyond:
            edge(c3, None, 0.48, "right", ", ".join(beyond), INK)
        ptxt = "Projection: " + " \u2192 ".join(seq)
    else:
        ptxt = "Projection " + next(r["state"] for r in G if r["gate"] == "projection")
    plan = C["plan_c2_node_h"].replace("-", "\u2013")
    c3.text(5, 0.98, f"C2: {float(C['c2_node_h']):.1f} node-h (plan {plan} for the eight); S2 so far "
                     f"{float(C['H_spent_h']):.1f} of 520 node-h (ledger {C['ledger_now_utc']})\n"
                     + ("" if C["ledger_complete"] == "True" else f"Ledger incomplete: {C['ledger_problems']} "
                        f"problem(s), {C['problem_rows']} boot(s) untimed\n") + ptxt,
            fontsize=6, color=INK, va="top", linespacing=1.35)
    c3.set_xlim(0, 600); c3.set_ylim(0, 1); c3.set_yticks([])
    c3.spines["left"].set_visible(False)
    c3.set_xlabel("Projected S2 node-hours P after relaxation 4 (dashed: cap 520)")

    for lab, axx, dx in (("a", a, 0.06), ("b", b1, 0.06), ("c", c1, 0.075)):
        p = axx.get_position()
        fig.text(p.x0 - dx, p.y1 + 0.035, lab, fontsize=8, fontweight="bold", va="top", ha="left")
    fig.canvas.draw()
    if audit and require_matplotlib_panel_alignment is not None:
        require_matplotlib_panel_alignment(fig, json_out=out + ".alignment.json", overlay_svg=out + ".alignment.svg",
                                           axes=[a, b1, c1, c2, b2, c3], panel_ids=["a", "b1", "c1", "c2", "b2", "c3"],
                                           row_groups=[["b1", "c1", "c2"], ["b2", "c3"]], tolerance_pt=1.5,
                                           gutter_tolerance_pt=1.5, strict=True)
    if "pdf" in formats:
        fig.savefig(out + ".pdf", metadata={"CreationDate": None})       # no render date: reproducible outputs
    if "svg" in formats:
        fig.savefig(out + ".svg", metadata={"Date": None})
    if "png" in formats:
        fig.savefig(out + ".png", dpi=600)
    if "tiff" in formats:
        fig.savefig(out + ".tiff", dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)
    print("written", out + ".{" + ",".join(formats) + "}")


# ---------------------------------------------------------------- self-test (synthetic archives; no C2 file is read)
CANARY = {"dF_200_180_meV": 9876.54321, "Eb_A2_meV": {"hinge": 7654.321, "far": 6543.21},   # K3 value 1111.111
          "E_mace_eV": 5432.1}


class _WP2e:
    """The public WP2e relaxation (234 atoms, all free, converged at k = 282) cut into synthetic A2 parts."""

    def __init__(self, q47):
        self.txt, self.inp = q47.a32.read_text(WP2E + ".out.gz"), q47.a32.read_text(WP2E + ".in.gz")
        self.cfg, _ = q47._segment(self.txt, 234)
        assert len(self.cfg) == 283 and self.cfg[-1]["converged"]
        self.h_end = self.txt.index("Self-consistent Calculation")

    def start(self, k):
        return self.h_end if k == 0 else self.cfg[k]["window"][0]

    def header(self, label, n, ranks):
        h = self.txt[:self.h_end].replace("Reading input from relax_m30_GA_img0.in",
                                          f"Reading input from {label}.p{n}.in")
        return re.sub(r"Number of MPI processes:\s+\d+", f"Number of MPI processes:                {ranks}", h)

    def parts(self, label, kind, n, splits, ranks=64):
        """kind: conv (converged at k = n, the WP2e last configuration spliced in), cap (k beyond 200), early (bfgs
        failed after k = n), stopped (killed after k = n), fakeconv (a convergence flag on configuration n), scf0 (SCF
        failure before k = 0), dead (the last restart part ends before its header). splits: the first k of each
        restart part."""
        bounds = [0] + list(splits) + [None]
        out = []
        for j in range(len(bounds) - 1):
            a, b, last = bounds[j], bounds[j + 1], j == len(bounds) - 2
            body = self.header(label, j + 1, ranks)
            if kind == "scf0":
                out.append(body + "\n     convergence NOT achieved after 100 iterations: stopping\n\n   JOB DONE.\n")
                continue
            if last and kind == "dead":
                out.append("mpirun: the launch failed before pw.x started\n")
                continue
            if not last:
                body += self.txt[self.start(a):self.cfg[b - 1]["own_end"]] + "\n     Program stopped by user request\n"
            elif kind == "cap":
                body += self.txt[self.start(a):]
            elif kind == "conv":
                tail = self.txt[self.cfg[282]["window"][0]:]
                tail = re.sub(r"bfgs converged in\s+\d+ scf cycles and\s+\d+ bfgs steps",
                              f"bfgs converged in {n + 1:5d} scf cycles and {n:5d} bfgs steps", tail)
                tail = re.sub(r"number of scf cycles\s+=\s+\d+", f"number of scf cycles    = {n + 1:3d}", tail)
                tail = re.sub(r"number of bfgs steps\s+=\s+\d+", f"number of bfgs steps    = {n:3d}", tail)
                body += (self.txt[self.start(a):self.cfg[n - 1]["own_end"]] if n > a else "") + tail
            elif kind == "fakeconv":                    # a convergence flag on configuration n, whose forces are large
                t = self.txt[self.start(a):self.cfg[n]["own_end"]]
                i = t.index("\n", t.rindex("Total force"))
                body += t[:i] + f"\n\n     bfgs converged in {n + 1:5d} scf cycles and {n:5d} bfgs steps\n" + t[i:] + \
                    "\n   JOB DONE.\n"
            else:
                body += self.txt[self.start(a):self.cfg[n]["own_end"]]
                if kind == "early":
                    body += "\n     bfgs failed after  1 scf cycles and   1 bfgs steps\n\n   JOB DONE.\n"
            out.append(body)
        return out

    def input(self, n_free):
        """The WP2e input with '0 0 0' on every atom from n_free on (the scripts/47 writer's convention)."""
        lines = self.inp.split("\n")
        h = next(i for i, ln in enumerate(lines) if ln.startswith("ATOMIC_POSITIONS"))
        pos = [ln.rstrip() + ("    0   0   0" if i >= n_free else "") for i, ln in enumerate(lines[h + 1:h + 235])]
        return "\n".join(lines[:h + 1] + pos + lines[h + 235:])


def _wj(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)


def _wgz(text, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt", compresslevel=1) as fh:
        fh.write(text)


def _synthetic(root, scen, wp, g49, q47):
    """One synthetic archive: c1 (smoke mapping, start-source counts, CAMPAIGN_DONE) and c2 (parts, records, gates,
    the A2 stop state, the log and the hard-cap refusal when the scenario has them)."""
    c1, c2 = os.path.join(root, "c1"), os.path.join(root, "c2")
    real_c1 = os.path.join(S2, "c1")
    _wj({"mapping": json.load(open(os.path.join(real_c1, "smoke.json")))["mapping"]}, os.path.join(c1, "smoke.json"))
    os.makedirs(os.path.join(c1, "logs"), exist_ok=True)
    open(os.path.join(c1, "logs", "campaign.log"), "w").write(
        "[2026-11-05T07:15:52Z] end: {'done': 1}; CAMPAIGN_DONE; KEEP_ALIVE removed\n")
    for site in (136, 76):
        _wj({"n_free": N_FREE_PIN[site]["host"]}, os.path.join(c1, "regions", f"m30_B{site}.json"))
    for lab in C2_LABELS:
        c = g49.a2_cell(lab)
        nf = N_FREE_PIN[c["site"]][c["kind"]] + scen.get("free_offset", {}).get(lab, 0)
        if c["kind"] != "host":
            _wj({"n_free": nf, "n_fixed": 234 - nf, "relax": {"E_mace_eV": CANARY["E_mace_eV"]}},
                os.path.join(c1, "records", f"{g49.a1_start_of(lab)}.json"))
        spec = scen["relax"].get(lab)
        if spec is None:
            continue
        kind, n, splits, status, outcome = spec
        raw = os.path.join(c2, "raw")
        rec = {"schema": "s2-a2-1", "label": lab, "status": status, "layout": {"ranks": 64, "copies": 1},
               "restarts": len(splits), "reruns_from_zero": 0, "interruptions": [], "parts": []}
        k_last = None
        if kind == "inonly":                                     # a prepared part that never ran
            _wgz(wp.input(N_FREE_PIN[c["site"]][c["kind"]]), os.path.join(raw, f"{lab}.p1.in.gz"))
        elif kind is not None:
            for j, t in enumerate(wp.parts(lab, kind, n, splits), 1):
                _wgz(t, os.path.join(raw, f"{lab}.p{j}.out.gz"))
                _wgz(wp.input(N_FREE_PIN[c["site"]][c["kind"]]), os.path.join(raw, f"{lab}.p{j}.in.gz"))
            k_last = {"cap": q47.K_CAP, "scf0": None, "dead": splits[-1] - 1 if splits else None}.get(kind, n)
        nc = 0 if k_last is None else k_last + 1
        if nc:
            rec["k0_seen"] = True
        if status == "complete":
            wall = max(nc, 1) * 4.6 * 60.0
            conv = kind in ("conv", "fakeconv")
            rec.update(n_config=nc, k_last=k_last, converged_at_k=n if conv else None, qe_converged=conv,
                       wall_h=wall / 3600.0, min_per_config=wall / 60.0 / max(1, nc),
                       end_rule={"outcome": outcome, "dF_200_180_meV": CANARY["dF_200_180_meV"] if nc > 200 else None,
                                 "end": {"early": "bfgs_failed", "scf0": "scf_failed"}.get(kind), "stop": False,
                                 "reason": None, **scen.get("end_extra", {}).get(lab, {})})
        _wj(rec, os.path.join(raw, f"{lab}.a2.json"))
    led = scen["ledger"]
    probs = list(led.get("problems") or []) + ["boot: no btime or no heartbeat" for b in led["boots"]
                                                 if b.get("hours") is None]
    _wj({"schema": "s2-ledger-1", "now_utc": "2026-11-07T10:00:00Z", **led, "problems": probs,
         "complete": not probs}, os.path.join(c2, "ledger.json"))
    if "state" in scen:
        _wj(scen["state"], os.path.join(c2, "state_end.json"))
    if "log" in scen:
        os.makedirs(os.path.join(c2, "logs"), exist_ok=True)
        open(os.path.join(c2, "logs", "campaign.log"), "w").write(scen["log"])
    if "hard_cap" in scen:
        _wj({"schema": "s2-hardcap-1", "job": scen["hard_cap"]}, os.path.join(c2, "HARD_CAP.json"))
    for d, gates_ in (("gates_applied", scen["gates"]), (os.path.join("step0_attempt1", "gates_applied"),
                                                         scen.get("attempt1", {}))):
        for gid, (att, res, dec, extra) in gates_.items():
            base = os.path.join(c2, d, re.sub(r"[^A-Za-z0-9_.-]", "_", gid))
            name = gid.split(":")[1].split("@")[0]
            _wj({"schema": "s2-gate-1", "gate": name, "campaign": "c2", "attempt": att, "result": res,
                 "decision": dec, **extra}, base + ".gate.json")
            _wj({"schema": "s2-gate-applied-1", "id": gid, "gate": name, "rc": 0, "attempt": att, "decision": dec,
                 "applied": "2026-11-06T00:00:00Z"}, base + ".json")


def _s0(sp, dF, att, oc):
    tol = 0.5
    cell = {"dF_meV": dF, "passed": dF is not None and abs(dF) <= tol, "reason": None}
    return (att, {"cells": {sp: cell}, "attempt": att, "fix_note": None, "outcome": oc, "tolerance_meV": tol},
            {"step0": {"attempts": att, "outcome": oc, "repeat": att == 2}}, {})


def _proj(g49, scen_relax, H):
    st = {"G1": {"Cl": True, "Ca": False}, "sr_stop": False, "n": 8, "pose": {"Cs": "default", "Cl": "default"},
          "cuts": [], "a2_layout": "64", "K2": "pass", "step0": {"outcome": "pass", "attempts": 1}}
    a2c = []
    for lab in C2_LABELS[:4]:
        kind, n, _, status, _ = scen_relax[lab]
        if status == "complete" and kind is not None:
            nc = (200 if kind == "cap" else n) + 1
            a2c.append({"label": lab, "n_config": nc, "wall_h": nc * 4.6 * 60.0 / 3600.0, "copies": 1})
    inputs = {"H_spent_h": H, "tau_SP_h": 0.112, "mace_h_per_relax": 0.0033, "host_wave_h": 3.3}
    done = [x["label"] for x in a2c]
    project = lambda s: g49.projection({**g49.plan_work(s, "after4", done=done), **inputs, "a2_completed": a2c})["P_h"]
    s = copy.deepcopy(st); P0 = project(s); cuts = g49.cut_order(s, project, "after4")
    res = {"point": "after4", "P_initial_h": P0, "cuts": cuts, "inputs": inputs, "a2_completed": a2c,
           "work_after": g49.plan_work(s, "after4", done=done)}
    dec = {"cuts": s.get("cuts", []), "n": s.get("n"), "multi_pose_cut": s.get("multi_pose_cut", {}),
           "c4_run": g49.c4_planned(s)}
    return (1, res, dec, {"state_in": st, "inputs_in": inputs})


def _k3(dec, cf=(), ef=()):
    eb = CANARY["Eb_A2_meV"]
    return (1, {"Eb_A2_meV": eb, "value_meV": eb["hinge"] - eb["far"], "checks_failed": list(cf),
                "end_rule_failed": list(ef), "a1_invalid_reported": [], "K3": dec}, {"K3": dec}, {})


def _k2(oc, att=1):
    dec = "pass" if oc in ("accepted_converged", "accepted_plateau") else "fail"
    return (att, {"outcome": oc, "a1_valid_reported": True, "K2": dec}, {"K2": dec}, {})


def self_test(keep=None):
    g49, q47, c46 = modules()
    wp = _WP2e(q47)
    L = C2_LABELS
    NR = (None, None, [], "not_run_gate", None)
    full = {L[0]: ("conv", 120, [60], "complete", "accepted_converged"),
            L[1]: ("cap", None, [], "complete", "accepted_plateau"),
            L[2]: ("conv", 90, [], "complete", "accepted_converged"),
            L[3]: ("cap", None, [150], "complete", "unconverged_cap"),
            L[4]: ("conv", 70, [], "complete", "accepted_converged"),
            L[5]: ("early", 150, [], "complete", "unconverged_early"),
            L[6]: ("conv", 140, [40, 100], "complete", "accepted_converged"),
            L[7]: ("conv", 100, [], "complete", "accepted_converged")}
    ledger = {"H_spent_h": 75.0, "boots": [
        {"btime": _epoch("2026-11-05T06:15:52Z"), "hours": 5.0, "campaigns": ["c1", "c2"]},
        {"btime": _epoch("2026-11-06T00:00:00Z"), "hours": 30.0, "campaigns": ["c2"]},
        {"btime": _epoch("2026-11-06T08:00:00Z"), "end_used": _epoch("2026-11-06T08:30:00Z"), "hours": 0.5,
         "manual": True}]}
    pass1, pass4 = _s0("s2_m30_VB136", 0.12, 1, "pass"), _s0("s2_m30_Sr136o0_vac", -0.31, 1, "pass")
    nothing_after_1 = {"step0@4": "not reached", "projection": "not reached", "K3": "not reached"}
    scen = {
        "full": {"relax": full, "ledger": ledger, "state": {"step0": {"outcome": "pass"}}, "gates": {
            "gate:step0@1": pass1, "gate:K2": _k2("accepted_converged"), "gate:step0@4": pass4,
            "gate:projection@after4": _proj(g49, full, 60.0), "gate:K3": _k3("pass")},
            "expect": {"step0@1": "pass", "K2": "pass (accepted_converged)", "step0@4": "pass", "projection": "no cut",
                       "K3": "pass"}},
        "repeat_k2fail": {"relax": {L[0]: ("cap", None, [], "complete", "unconverged_cap"), **{x: NR for x in L[1:]}},
                          "ledger": ledger, "state": {"step0": {"outcome": "pass", "repeat": True}},
                          "attempt1": {"gate:step0@1": _s0("s2_m30_VB136", 0.83, 1, "fail_pending_fix")},
                          "gates": {"gate:step0@1": _s0("s2_m30_VB136", 0.05, 2, "pass"),
                                    "gate:K2": _k2("unconverged_cap", 2)},
                          "expect": {"step0@1": "pass", "K2": "fail (unconverged_cap)", **nothing_after_1}},
        "skip_cuts_stop": {"relax": {**{x: full[x] for x in L[:3]}, L[3]: (None, None, [], "missing", None),
                                     L[4]: full[L[4]], L[5]: full[L[5]], L[6]: ("stopped", 85, [30], "pending", None),
                                     L[7]: (None, None, [], "not_started_cap", None)},
                           "ledger": {**ledger, "H_spent_h": 480.0},
                           "expect": {"step0@1": "pass", "K2": "pass (accepted_converged)",
                                      "step0@4": "skipped (no k = 0)", "K3": "not reached"}},
        "value_missing": {"relax": {L[0]: ("stopped", 0, [], "killed_by_gate", None), **{x: NR for x in L[1:]}},
                          "ledger": ledger, "state": {"step0": {"outcome": "fail_pending_fix"}},
                          "gates": {"gate:step0@1": _s0("s2_m30_VB136", None, 1, "fail_pending_fix")},
                          "expect": {"step0@1": "fail: value missing (fail_pending_fix)", "K2": "not reached",
                                     **nothing_after_1}},
        "no_error": {"relax": {L[0]: ("stopped", 40, [], "killed_by_gate", None), **{x: NR for x in L[1:]}},
                     "ledger": ledger, "state": {"step0": {"outcome": "fail_final", "no_error_found": True}},
                     "gates": {"gate:step0@1": _s0("s2_m30_VB136", 0.9, 1, "fail_pending_fix")},
                     "expect": {"step0@1": "fail (fail_final: no error found)", "K2": "not reached",
                                **nothing_after_1}},
        "no_error_log": {"relax": {L[0]: ("stopped", 40, [], "killed_by_gate", None), **{x: NR for x in L[1:]}},
                         "ledger": ledger, "log": "[2026-11-06T09:00:00Z] STEP0_NO_ERROR: step-0 fail_final (no error "
                                                  "found); A2 stops (section 11)\n",
                         "gates": {"gate:step0@1": _s0("s2_m30_VB136", 0.9, 1, "fail_pending_fix")},
                         "expect": {"step0@1": "fail (fail_final: no error found)", "K2": "not reached",
                                    **nothing_after_1}},
        "scf_k0": {"relax": {L[0]: ("scf0", None, [], "complete", "unconverged_early"), **{x: NR for x in L[1:]}},
                   "ledger": ledger, "gates": {"gate:K2": _k2("unconverged_early")},
                   "expect": {"step0@1": "skipped (no k = 0)", "K2": "fail (unconverged_early)", **nothing_after_1}},
        "operator_k2": {"relax": {L[0]: ("stopped", 60, [], "complete", "unconverged_early"), **{x: NR for x in L[1:]}},
                        "end_extra": {L[0]: {"end": "killed (operator)"}}, "ledger": ledger,
                        "state": {"step0": {"outcome": "pass"}},
                        "gates": {"gate:step0@1": pass1, "gate:K2": _k2("incomplete")},
                        "expect": {"step0@1": "pass", "K2": "fail (unconverged_early, operator; gate read incomplete)",
                                   **nothing_after_1}},
        "hard_cap": {"relax": {**{x: full[x] for x in L[:4]}, L[4]: (None, None, [], "not_started_cap", None)},
                     "hard_cap": "a2:" + L[4], "ledger": ledger, "state": {"step0": {"outcome": "pass"}},
                     "gates": {"gate:step0@1": pass1, "gate:K2": _k2("accepted_converged"), "gate:step0@4": pass4,
                               "gate:projection@after4": _proj(g49, full, 60.0)},
                     "expect": {"step0@1": "pass", "step0@4": "pass", "projection": "no cut", "K3": "not reached"}},
        "stop_before_k0": {"relax": {L[0]: full[L[0]], L[1]: ("inonly", None, [], "pending", None)},
                           "ledger": {**ledger, "boots": ledger["boots"] + [{"boot_id": "x", "hours": None}]},
                           "state": {"step0": {"outcome": "pass"}},
                           "gates": {"gate:step0@1": pass1, "gate:K2": _k2("accepted_converged")},
                           "expect": {"step0@1": "pass", "K2": "pass (accepted_converged)", "step0@4": "not reached"}},
        "dead_part": {"relax": {L[0]: ("dead", None, [31], "pending", None)}, "ledger": ledger,
                      "state": {"step0": {"outcome": "pass"}}, "gates": {"gate:step0@1": pass1},
                      "expect": {"step0@1": "pass", "K2": "not reached", **nothing_after_1}},
    }
    k3gates = lambda k3: {**scen["full"]["gates"], "gate:K3": k3}
    scen.update({
        "k2_capped": {"relax": {L[0]: (None, None, [], "not_started_cap", None)}, "hard_cap": "a2:" + L[0],
                      "ledger": ledger, "gates": {"gate:K2": _k2("missing")},
                      "expect": {"step0@1": "not reached", "K2": "fail (missing; record: not_started_cap)",
                                 **nothing_after_1}},
        "k3_value": {"relax": full, "ledger": {**ledger, "problems": ["manual entry without btime and end"]},
                     "state": {"step0": {"outcome": "pass"}}, "gates": k3gates(_k3("fail_replan")),
                     "expect": {"K3": "fail (fail_replan): value \u2264 +25.7 meV"}},
        "k3_checks": {"relax": full, "ledger": ledger, "state": {"step0": {"outcome": "pass"}},
                      "gates": k3gates(_k3("fail_replan", cf=[L[3] + ": final geometry fails check(s) [3]"])),
                      "expect": {"K3": "fail (fail_replan): checks failed"}},
        "k3_a1only": {"relax": full, "ledger": ledger, "state": {"step0": {"outcome": "pass"}},
                      "gates": k3gates(_k3("a1_only", ef=[L[5] + ": end rule unconverged_early (status complete)"])),
                      "expect": {"K3": "not evaluable (a1_only)"}},
    })
    s3 = scen["skip_cuts_stop"]
    s3["gates"] = {"gate:step0@1": _s0("s2_m30_VB136", -0.44, 1, "pass"), "gate:K2": _k2("accepted_converged"),
                   "gate:projection@after4": _proj(g49, s3["relax"], 480.0)}
    text = lambda res, i: next(r for r in res["rows"] if r["label"] == L[i])["status_text"]
    tmp = tempfile.mkdtemp(prefix="fig_s2_c2_selftest_")
    try:
        for nm, sc in scen.items():
            root, src = os.path.join(tmp, nm, "s2"), os.path.join(tmp, nm, "source_data")
            _synthetic(root, sc, wp, g49, q47)
            q47.READS.clear()
            res = build(root, src)
            got = {r["gate"]: r["state"] for r in res["gates"]}
            for g, want in sc["expect"].items():
                assert got[g] == want, (nm, g, got[g], want)
            cost_ = {r["key"]: r["value"] for r in res["cost"]}
            assert math.isclose(float(cost_["c2_node_h"]), 34.0, abs_tol=1e-9) and cost_["manual_rows"] == 1
            if nm == "skip_cuts_stop":
                assert got["projection"].startswith("cuts ") and "c4_run" in got["projection"], got["projection"]
                assert text(res, 6) == "stopped at k = 85" and text(res, 7) == "not started (cap)"
            if nm == "repeat_k2fail":
                assert [(r["attempt"], r["state"]) for r in res["step0"]] == [
                    (1, "fail (fail_pending_fix)"), (1, "not reached"), (2, "pass"), (2, "not reached")], res["step0"]
            if nm == "scf_k0":
                assert text(res, 0) == "early end, scf_failed, no configuration"
            if nm == "hard_cap":
                assert [text(res, i) for i in range(4, 8)] == ["not started (cap)"] * 4
            if nm == "stop_before_k0":
                assert text(res, 1) == "stopped before k = 0" and text(res, 2) == "not started (no record)"
                assert cost_["problem_rows"] == 1 and cost_["ledger_complete"] is False
            if nm == "dead_part":
                assert text(res, 0) == "stopped at k = 30"
            if nm == "k2_capped":
                assert [text(res, i) for i in range(8)] == ["not started (cap)"] * 8
            if nm == "k3_value":
                assert cost_["ledger_complete"] is False and cost_["problem_rows"] == 0
                assert cost_["ledger_problems"] == 1
            out = os.path.join(tmp, nm, "fig")
            plot(src, out, formats=("pdf", "svg", "png") if keep else ("pdf", "svg"), audit=True)
            if keep:
                os.makedirs(keep, exist_ok=True)
                for ext in ("pdf", "svg", "png"):
                    shutil.copy(f"{out}.{ext}", os.path.join(keep, f"selftest_{nm}.{ext}"))
            blob = "".join(open(os.path.join(src, f)).read() for f in COLUMNS) + open(out + ".svg").read()
            canaries = (9876.54321, 7654.321, 6543.21, 1111.111, 5432.1)
            near = [x for x in map(float, re.findall(r"\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", blob))
                    if any(abs(x - c) < 0.6 for c in canaries)]
            assert not near, f"a withheld canary value reached the source data or the figure ({near[:3]})"
        src = os.path.join(tmp, "full", "source_data")
        rows = list(csv.DictReader(open(os.path.join(src, "fig_s2_c2_a_force.csv"))))
        for r in rows:
            if r["order"] == "2" and int(r["k"]) in (0, 1, 2, 200):
                r["fmax_free_eV_A"] = "40.0"
            if r["order"] == "5" and int(r["k"]) in (68, 69):
                r["fmax_free_eV_A"] = "0.0005"
        with open(os.path.join(src, "fig_s2_c2_a_force.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLUMNS["fig_s2_c2_a_force.csv"]); w.writeheader(); w.writerows(rows)
        out = os.path.join(tmp, "full", "edge")
        plot(src, out, formats=("pdf", "svg", "png") if keep else ("pdf", "svg"), audit=True)
        if keep:
            for ext in ("pdf", "svg", "png"):
                shutil.copy(f"{out}.{ext}", os.path.join(keep, f"selftest_edge_arrows.{ext}"))
        g = Guarded({"end_rule": {"outcome": "x", "dF_200_180_meV": 1.0}}, "t")
        for bad in (lambda: g.get("end_rule").get("dF_200_180_meV"), lambda: str(g.get("end_rule")),
                    lambda: list(g.get("end_rule")), lambda: g.get("end_rule").open(), lambda: g == g):
            try:
                bad()
            except Blinded:
                continue
            raise AssertionError("the guard let a withheld read through")
        base = scen["full"]
        negs = (("converged above the threshold", {"relax": {**full, L[2]: ("fakeconv", 20, [], "complete",
                                                                            "accepted_converged")}, "gates": {}},
                 "converged above forc_conv_thr"),
                ("free-atom count differs from the start source", {"free_offset": {L[2]: 1}}, "free-atom count"),
                ("P_initial_h differs", {"tamper_P": True}, "P_initial_h"),
                ("K2 differs from the record", {"gates": {**base["gates"], "gate:K2": _k2("unconverged_cap")}},
                 "differs from relaxation 1's record"),
                ("state differs from the step-0 file", {"state": {"step0": {"outcome": "fail_final"}}},
                 "differs from the last step-0 gate file"))
        for why, sc, key in negs:
            root = os.path.join(tmp, "neg", "s2")
            shutil.rmtree(os.path.join(tmp, "neg"), ignore_errors=True)
            sc = {**base, **sc}
            if sc.get("tamper_P"):
                p = copy.deepcopy(sc["gates"]["gate:projection@after4"]); p[1]["P_initial_h"] += 1.0
                sc["gates"] = {**sc["gates"], "gate:projection@after4": p}
            _synthetic(root, sc, wp, g49, q47)
            _expect_fail(lambda: (q47.READS.clear(), build(root, os.path.join(tmp, "neg", "src"))), why, key)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"self-test passed: {len(scen)} synthetic archives, the guard and {len(negs)} negative cases")


def _expect_fail(fn, why, key):
    try:
        fn()
    except (AssertionError, Blinded) as e:
        assert key in str(e), f"{why}: the build failed for another reason: {e}"
        return
    raise AssertionError(f"the build accepted a bad archive ({why})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true"); ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--keep", default=None, help="self-test: copy the synthetic figures into this folder")
    a = ap.parse_args()
    if a.self_test:
        self_test(a.keep); sys.exit(0)
    if a.build:
        build()
    plot()

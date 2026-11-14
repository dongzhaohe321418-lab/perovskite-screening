#!/usr/bin/env python
"""The S2b guard (results/objective2/s2/S2B_PLAN.md section 1, "The guard (D-C2-12, extended)").

Until E, every tool that reads an fr (or c4b) A2 record, validity record or gate file reads it through this guard. The
OPS2 exceptions remain: the runner (scripts/50), the scripts/49 gate code and its verify, and the field comparator.
S2B section 1 makes these guard rules rules of the plan: no operations note may alter them.

  GuardedS2b  an fr A2 record (<label>.a2.json) or validity record (<label>.validity_final.json): the D-C2-12 class
              Guarded of figures/fig_s2_c2_a2.py, loaded unchanged, with WITHHELD extended by the exact name of every
              energy field the S2b code writes (scripts/49 FR_ENERGY_FIELDS) and the F names of its inputs. A field is
              read by its name, a withheld field raises, the object is never iterated, compared or printed, and open()
              hands out a subtree only if it holds no withheld field. Children stay GuardedS2b.
  GateLeaves  an fr gate file (gates/<name>.json), its gates_applied copy (.gate.json) or an applied-gate marker: an
              allow-list of full dotted paths, exactly as S2B section 1 says: decision.* and the named reason lists
              (result.checks_failed, result.end_rule_failed, result.cells_not_run). Every other path raises, parents
              and bookkeeping fields included (result, gate, attempt, state_in, inputs_in, c1_in, opened, ...), and so
              does an allowed path whose subtree holds a withheld field at any depth (a dict key or a key inside a list
              element). There is no step-0 STOP mode: the D-C2-10 read of a failing step-0 dF (OPS2) is not part of
              the S2b guard (S2B sections 0 and 1: every fr DFT energy stays unread until E). A step-0 failure is
              diagnosed from decision.fr_step0 (which cell, which attempt) and from non-energy evidence (pw.x logs,
              environment, inputs), never from dF.

Geometry and values are never computed here. The self-test builds a synthetic fr archive in a temporary directory, in
the record and gate-file shapes that scripts/50 and scripts/49 write; no S2 file is read.

    python results/objective2/s2/s2b/guard.py --self-test
"""
import argparse, copy, importlib.util, json, os, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
S2 = os.path.normpath(os.path.join(HERE, ".."))                          # results/objective2/s2, the archive root
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", "scripts"))


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


fig = _load("fig_s2_c2_a2", os.path.join(S2, "figures", "fig_s2_c2_a2.py"))    # the D-C2-12 guard, unchanged
g49 = _load("g49", os.path.join(SCRIPTS, "49_s2_gates.py"))     # constants only (scripts/46, 47 load on first use)
Blinded = fig.Blinded
INPUT_F = ("F_sp_eV", "F_k0_eV", "F_final_eV")                   # the F of the FR-2 and step-0 inputs (scripts/49)
WITHHELD_S2B = frozenset(set(fig.WITHHELD) | set(g49.FR_ENERGY_FIELDS) | set(INPUT_F))
GATE_LEAVES = ("result.checks_failed", "result.end_rule_failed", "result.cells_not_run")   # with decision.* (S2B 1)


def withheld_in(x):
    """The WITHHELD_S2B keys anywhere in a JSON value (dict keys at any depth, list elements included)."""
    out = set()
    if isinstance(x, dict):
        out |= WITHHELD_S2B & set(x)
        for v in x.values():
            out |= withheld_in(v)
    elif isinstance(x, list):
        for v in x:
            out |= withheld_in(v)
    return out


class GuardedS2b(fig.Guarded):
    """An fr A2 record or validity record: fig_s2_c2_a2.Guarded with WITHHELD_S2B."""
    __slots__ = ()

    def _wrap(self, v, k):
        if isinstance(v, dict):
            return GuardedS2b(v, f"{self._p}/{k}")
        return [self._wrap(x, f"{k}[]") for x in v] if isinstance(v, list) else v

    def get(self, k, default=None):
        if k in WITHHELD_S2B:
            raise Blinded(f"{self._p}/{k} is withheld until E (S2B_PLAN.md section 1)")
        return self._wrap(self._d.get(k, default), k)

    def open(self):
        def scan(x):
            if isinstance(x, dict):
                if WITHHELD_S2B & set(x):
                    raise Blinded(f"{self._p} holds a withheld field: it is read by field name only")
                for v in x.values():
                    scan(v)
            elif isinstance(x, list):
                for v in x:
                    scan(v)
        scan(self._d)
        return copy.deepcopy(self._d)


def guarded_s2b(path):
    return GuardedS2b(json.load(open(path)), os.path.basename(path)) if os.path.exists(path) else None


class GateLeaves:
    """An fr gate file, gates_applied copy or marker, read by full dotted path from a closed list (S2B section 1)."""
    __slots__ = ("_d", "_p")

    def __init__(self, d, path):
        self._d, self._p = d, path

    def allowed(self, path):
        return isinstance(path, str) and (path.startswith("decision.") or path in GATE_LEAVES)

    def get(self, path, default=None):
        if not self.allowed(path):
            raise Blinded(f"{self._p}: {path!r} is not on the allow-list of the S2b guard (S2B_PLAN.md section 1)")
        x = self._d
        for k in path.split("."):
            if k in WITHHELD_S2B:
                raise Blinded(f"{self._p}: {path!r} names a withheld field (S2B_PLAN.md section 1)")
            if not isinstance(x, dict) or k not in x:
                return default
            x = x[k]
        if withheld_in(x):
            raise Blinded(f"{self._p}: {path!r} holds a withheld field: it is not handed out (S2B_PLAN.md section 1)")
        return copy.deepcopy(x)

    def _refuse(self, *a, **kw):
        raise Blinded(f"{self._p} is read by full dotted path only (S2B_PLAN.md section 1)")

    __iter__ = __repr__ = __str__ = __eq__ = __len__ = __contains__ = keys = items = values = open = _refuse
    __hash__ = None

    def __bool__(self):
        return True


def gate_leaves(path):
    return GateLeaves(json.load(open(path)), os.path.basename(path)) if os.path.exists(path) else None


# ---------------------------------------------------------------- self-test (a synthetic fr archive)
def _paths(x, pre=""):
    """Every dotted path of a JSON object (inner nodes and leaves; list elements are not addressed)."""
    out = []
    if isinstance(x, dict):
        for k, v in x.items():
            p = f"{pre}.{k}" if pre else k
            out.append(p)
            out += _paths(v, p)
    return out


def _canary():
    """Every WITHHELD_S2B field planted alone with a readable sibling, in a nested dict and inside a list element
    (the extended fields WITHHELD_S2B - fig.WITHHELD are the subject; the base fields complete the coverage)."""
    fs = sorted(WITHHELD_S2B)
    return {f"n_{f}": {f: 1.0 + i, "ok": i} for i, f in enumerate(fs)}, [{f: 2.0 + i, "ok": i} for i, f in enumerate(fs)]


def _synthetic(root):
    """A synthetic fr archive in the shapes scripts/50 (A2 and validity records, markers) and scripts/49 (s2-gate-1)
    write: an FR quartet that stopped at V+_R (check 5), a passing, a failing and a two-cell failing fr_step0 file, gate
    FR, and the canary fields of WITHHELD_S2B in every record and in one gate file."""
    L = g49.FR_QUARTET
    raw, gates, ga = (os.path.join(root, "fr", x) for x in ("raw", "gates", "gates_applied"))
    for d in (raw, gates, ga):
        os.makedirs(d, exist_ok=True)
    nest, lst = _canary()
    vf = {"valid": False, "failed": [5], "file": "x.validity_final.json", "sha256": "0" * 64, "parent": L["host"],
          "parent_final": True, "check5_reading": "invariant", "valid_as_written": False, "failed_as_written": [5],
          "invariant_only": False}
    recs = {}
    for r, lab in L.items():
        rec = {"schema": "s2-a2-1", "label": lab, "campaign": "fr", "status": "not_run_gate",
               "status_reason": f"FR early stop at {L['V']} (check; S2B section 2)", "parts": []}
        if r in ("host", "V"):
            rec.update({"status": "complete", "n_config": 201, "k_last": 200, "wall_h": 9.5, "min_per_config": 2.8,
                        "parts": [{"n": 1, "end": "cap", "k_last": 200}], "restarts": 0, "reruns_from_zero": 0,
                        "interruptions": [], "k0_seen": True,
                        "end_rule": {"outcome": "accepted_plateau", "dF_200_180_meV": -1.234, "end": "cap", "stop": False,
                                     "reason": None},
                        "final_geometry": {"file": f"{lab}.final.extxyz", "k": 200, "sha256": "1" * 64},
                        "validity_final": dict(vf, valid=(r == "host"), failed=[] if r == "host" else [5])})
        # s2b_list_only: a dict whose only withheld content sits in a list element (open() must scan lists)
        rec.update({"s2b_canary": copy.deepcopy(nest), "s2b_canary_list": copy.deepcopy(lst),
                    "s2b_list_only": {"items": copy.deepcopy(lst), "ok": 1}})
        recs[lab] = rec
        json.dump(rec, open(os.path.join(raw, f"{lab}.a2.json"), "w"))
    val = {"schema": "s2-a2validity-1", "label": L["V"], "kind": "V", "validity": {
        "checks": {"5": {"passed": False, "passed_as_written": False, "fa_needs_exchange": [],
                         "gated": {"n_inorganic": 19, "n_fa": 1, "max_dr_inorganic_A": 0.31}}},
        "valid": False, "failed": [5], "check5_reading": "invariant", "valid_as_written": False, "failed_as_written": [5],
        "invariant_only": False, "s2b_canary": copy.deepcopy(nest), "s2b_list_only": {"items": copy.deepcopy(lst),
                                                                                         "ok": 1}},
        "geometry_sha256": {"final": "2" * 64}, "s2b_canary_list": copy.deepcopy(lst),
        "s2b_list_only": {"items": copy.deepcopy(lst), "ok": 1}}
    json.dump(val, open(os.path.join(raw, f"{L['V']}.validity_final.json"), "w"))
    sp_v, sp_dv = sorted(g49.FR_STEP0_PAIRS, key=lambda s: g49.FR_ORDER.index(g49.FR_STEP0_PAIRS[s]))

    def gate_file(gate, result, decision, inputs):
        return {"schema": "s2-gate-1", "gate": gate, "campaign": "fr", "commit": "e" * 40, "attempt": 1,
                "opened": [{"label": L["V"], "file": f"fr/raw/{L['V']}.p1.out.gz", "sha256": "3" * 64, "mode": "k0"}],
                "inputs_digest": "4" * 64, "result": result, "decision": decision, "written": "2026-11-20T00:00:00Z",
                "state_in": {"commit": "8" * 40, "K3": "fail_replan", "fr_step0": {"outcome": "pass"}},
                "inputs_in": inputs, "c1_in": None, "inputs_opened": []}
    s0_pass = gate_file("fr_step0", {"cells": {sp_v: {"dF_meV": 0.012, "passed": True, "reason": None}}, "attempt": 1,
                                     "fix_note": None, "outcome": "pass", "tolerance_meV": 0.5},
                        {"fr_step0": {"attempts": 1, "outcome": "pass", "repeat": False, "fix_note": None,
                                      "cell": L["V"]}}, {"cells": [sp_v], "attempt": 1, "fix_note": None})
    s0_fail = gate_file("fr_step0", {"cells": {sp_dv: {"dF_meV": 0.731, "passed": False, "reason": None}}, "attempt": 1,
                                     "fix_note": None, "outcome": "fail_pending_fix", "tolerance_meV": 0.5},
                        {"fr_step0": {"attempts": 1, "outcome": "fail_pending_fix", "repeat": False, "fix_note": None,
                                      "cell": L["DV"]}}, {"cells": [sp_dv], "attempt": 1, "fix_note": None})
    s0_fail2 = gate_file("fr_step0", {"cells": {sp_v: {"dF_meV": 0.104, "passed": True, "reason": None},
                                                sp_dv: {"dF_meV": -0.902, "passed": False, "reason": None}},
                                      "attempt": 2, "fix_note": "2026-11-20 x", "outcome": "fail_final",
                                      "tolerance_meV": 0.5},
                         {"fr_step0": {"attempts": 2, "outcome": "fail_final", "repeat": True, "fix_note": "2026-11-20 x",
                                       "cell": L["DV"], "attempt1": {"attempts": 1, "outcome": "fail_pending_fix",
                                                                     "cell": L["DV"]}}},
                         {"cells": [sp_v, sp_dv], "attempt": 2, "fix_note": "2026-11-20 x"})
    fr_fail = gate_file("FR", {"cells": {lab: {"status": recs[lab]["status"], "end_rule": None, "validity_final": None,
                                               "a1_valid": True} for lab in g49.FR_ORDER},
                               "first_failure": {"cell": L["V"], "kind": "check", "end_rule": "accepted_plateau"},
                               "end_rule_failed": [], "checks_failed": [f"{L['V']}: final geometry fails check(s) [5]"],
                               "cells_not_run": [L["D"], L["DV"]], "invariant_only": [], "a1_invalid_reported": [],
                               "FR1": False, "FR2": None},
                        {"FR": {"outcome": "fail", "FR1": False, "FR2": None, "part": "FR-1", "cell": L["V"],
                                "kind": "check"}}, {})
    fr_pass = gate_file("FR", {"cells": {}, "first_failure": None, "end_rule_failed": [], "checks_failed": [],
                               "cells_not_run": [], "invariant_only": [L["V"]], "a1_invalid_reported": [], "FR1": True,
                               "FR2": {"Eb_A1_meV": -12.5, "Eb_A2_meV": -30.25, "delta_far_meV": -17.75,
                                       "bound_meV": 50.0, "passed": True}},
                        {"FR": {"outcome": "pass", "FR1": True, "FR2": True, "part": None, "cell": None, "kind": None}},
                        {})
    # the canary gate file: every WITHHELD_S2B field in result (a dict and a list element), and under decision.* and a
    # named reason list, where only the safety net of GateLeaves.get stops it (S2B section 1)
    canary = gate_file("FR", dict(fr_fail["result"], s2b_canary=copy.deepcopy(nest), s2b_canary_list=copy.deepcopy(lst),
                                  checks_failed=copy.deepcopy(lst)),
                       {"FR": dict(fr_fail["decision"]["FR"], s2b_canary=copy.deepcopy(nest),
                                   s2b_canary_list=copy.deepcopy(lst))}, {})
    files = {"gates/fr_step0.json": s0_fail, "gates/FR.json": fr_fail, "gates_applied/gate_fr_step0_2.gate.json": s0_pass,
             "gates_applied/gate_fr_step0_4.gate.json": s0_fail, "gates_applied/gate_fr_step0_4b.gate.json": s0_fail2,
             "gates_applied/gate_FR.gate.json": fr_pass, "gates_applied/gate_FR_canary.gate.json": canary,
             "gates_applied/gate_FR.json": {"schema": "s2-gate-applied-1", "id": "gate:FR", "gate": "FR", "rc": 0,
                                            "attempt": 1, "decision": fr_fail["decision"], "gate_file_sha256": "5" * 64,
                                            "applied": "2026-11-20T00:00:00Z"}}
    for rel, obj in files.items():
        json.dump(obj, open(os.path.join(root, "fr", rel), "w"))
    return recs, val, files


def self_test():
    tmp = tempfile.mkdtemp(prefix="s2b_guard_")
    try:
        recs, val, files = _synthetic(tmp)
        assert set(g49.FR_ENERGY_FIELDS) <= WITHHELD_S2B and set(fig.WITHHELD) <= WITHHELD_S2B
        assert WITHHELD_S2B - set(fig.WITHHELD) == (set(g49.FR_ENERGY_FIELDS) | set(INPUT_F)) - set(fig.WITHHELD)
        n_raise = n_read = n_open = 0
        rec_hits, gate_hits = set(), set()

        def walk(gobj, d):
            """Every field of a guarded record: a withheld one raises, every other one reads; open() of every dict
            raises iff a withheld field is anywhere in it; children stay guarded."""
            nonlocal n_raise, n_read, n_open
            try:
                o = gobj.open()
                assert not withheld_in(d) and o == d, f"open() handed out a subtree with {sorted(withheld_in(d))}"
            except Blinded:
                assert withheld_in(d), "open() refused a subtree without a withheld field"
                n_open += 1
            for k, v in d.items():
                if k in WITHHELD_S2B:
                    try:
                        gobj.get(k); raise AssertionError(f"withheld field {k} was read")
                    except Blinded:
                        n_raise += 1; rec_hits.add(k)
                    continue
                x = gobj.get(k)
                n_read += 1
                if isinstance(v, dict):
                    assert isinstance(x, GuardedS2b), k
                    walk(x, v)
                elif isinstance(v, list):
                    assert len(x) == len(v)
                    for xe, ve in zip(x, v):
                        if isinstance(ve, dict):
                            assert isinstance(xe, GuardedS2b); walk(xe, ve)
                        else:
                            assert xe == ve
                else:
                    assert x == v, (k, x, v)
        # A2 and validity records: every energy leaf raises, every other field reads, children stay guarded
        for lab in recs:
            g = guarded_s2b(os.path.join(tmp, "fr", "raw", f"{lab}.a2.json"))
            walk(g, recs[lab])
        gv = guarded_s2b(os.path.join(tmp, "fr", "raw", f"{g49.FR_QUARTET['V']}.validity_final.json"))
        walk(gv, val)
        assert rec_hits == WITHHELD_S2B, f"record fields of WITHHELD_S2B not exercised: {sorted(WITHHELD_S2B - rec_hits)}"
        g = guarded_s2b(os.path.join(tmp, "fr", "raw", f"{g49.FR_QUARTET['V']}.a2.json"))
        assert g.get("end_rule").get("outcome") == "accepted_plateau" and g.get("validity_final").get("valid") is False
        assert g.get("validity_final").open()["check5_reading"] == "invariant"          # a subtree without energy
        for f in sorted(WITHHELD_S2B - set(fig.WITHHELD)):                  # the extended fields, one by one
            for parent in (g.get("s2b_canary").get(f"n_{f}"),
                           [x for x in g.get("s2b_canary_list") if f in x._d][0]):
                assert parent.get("ok") is not None
                for fn in (lambda p: p.get(f), lambda p: p.open()):
                    try:
                        fn(parent); raise AssertionError(f"{f}: a get or open() of its parent passed")
                    except Blinded:
                        n_raise += 1
        n_list_only = 0                     # open() of a dict whose withheld fields sit only inside a list element
        for obj in [guarded_s2b(os.path.join(tmp, "fr", "raw", f"{lab}.a2.json")) for lab in recs] + [gv, gv.get("validity")]:
            lo = obj.get("s2b_list_only")
            assert lo.get("ok") == 1 and not (WITHHELD_S2B & set(lo._d)) and withheld_in(lo._d) == WITHHELD_S2B
            try:
                lo.open(); raise AssertionError("open() handed out a dict with withheld fields in a list element")
            except Blinded:
                n_list_only += 1
        assert n_list_only == len(recs) + 2, n_list_only
        refusals = 0
        for obj in (g, g.get("end_rule"), gv):
            for f in (repr, str, len, list, lambda o: o == o, lambda o: "status" in o, lambda o: o.keys(),
                      lambda o: o.items(), lambda o: o.values()):
                try:
                    f(obj); raise AssertionError(f"{f} on a guarded record")
                except Blinded:
                    refusals += 1
        for obj in (g, g.get("end_rule"), gv, gv.get("validity")):
            try:
                obj.open(); raise AssertionError("open() of a subtree with a withheld field")
            except Blinded:
                refusals += 1
        # gate files, copies and markers: the closed allow-list of full dotted paths, and the safety net of get
        allowed_seen = set()
        for rel, obj in files.items():
            gl = gate_leaves(os.path.join(tmp, "fr", rel))
            for p in _paths(obj):
                x = obj
                for k in p.split("."):
                    x = x[k]
                inner = withheld_in(x) | (WITHHELD_S2B & set(p.split(".")))
                if (p.startswith("decision.") or p in GATE_LEAVES) and not inner:
                    assert gl.get(p) == x, (rel, p)
                    allowed_seen.add(p if not p.startswith("decision.") else "decision.*")
                    n_read += 1
                else:
                    try:
                        gl.get(p); raise AssertionError(f"{rel}: {p} was read")
                    except Blinded:
                        n_raise += 1
                        gate_hits.update(inner)
            for p in ("result", "result.FR2", "decision", "state_in", "inputs_in", "c1_in", "opened", "inputs_digest",
                      "written", "commit", "result.cells", "", None, "gate", "attempt", "gate_file_sha256"):
                try:
                    gl.get(p); raise AssertionError(f"{rel}: {p!r} was read")
                except Blinded:
                    refusals += 1
            for f in (repr, str, len, list, lambda o: o == o, lambda o: "gate" in o, lambda o: o.keys(),
                      lambda o: o.open()):
                try:
                    f(gl); raise AssertionError(f"{f} on a gate file")
                except Blinded:
                    refusals += 1
        assert {"result.checks_failed", "result.end_rule_failed", "result.cells_not_run", "decision.*"} == \
            allowed_seen, allowed_seen
        assert gate_hits == WITHHELD_S2B, f"gate-file fields of WITHHELD_S2B not exercised: {sorted(WITHHELD_S2B - gate_hits)}"
        gl = gate_leaves(os.path.join(tmp, "fr", "gates", "FR.json"))
        assert gl.get("decision.FR.outcome") == "fail" and gl.get("decision.FR.kind") == "check" and \
            gl.get("result.cells_not_run") == [g49.FR_QUARTET["D"], g49.FR_QUARTET["DV"]]
        cg = gate_leaves(os.path.join(tmp, "fr", "gates_applied", "gate_FR_canary.gate.json"))
        assert cg.get("decision.FR.outcome") == "fail" and cg.get("decision.FR.s2b_canary.n_F_k0_eV.ok") is not None
        for p in ("decision.FR", "decision.FR.s2b_canary", "decision.FR.s2b_canary_list", "decision.FR.s2b_canary.n_F_k0_eV",
                  "decision.FR.s2b_canary.n_F_k0_eV.F_k0_eV", "result.checks_failed"):
            try:
                cg.get(p); raise AssertionError(f"the canary {p} was read")
            except Blinded:
                refusals += 1
        # no step-0 STOP mode: in a failed fr_step0 file (one cell, two cells) every result.cells.*.dF_meV and .passed
        # raises; the fr_step0 decision itself holds no dF and no F
        n_s0 = 0
        for rel in ("gates/fr_step0.json", "gates_applied/gate_fr_step0_4.gate.json",
                    "gates_applied/gate_fr_step0_4b.gate.json", "gates_applied/gate_fr_step0_2.gate.json"):
            st = gate_leaves(os.path.join(tmp, "fr", rel))
            cells = files[rel]["result"]["cells"]
            for sp in cells:
                for p in (f"result.cells.{sp}.dF_meV", f"result.cells.{sp}.passed", f"result.cells.{sp}"):
                    try:
                        st.get(p); raise AssertionError(f"{rel}: {p} was read")
                    except Blinded:
                        n_s0 += 1
            d0 = st.get("decision.fr_step0")
            assert d0 == files[rel]["decision"]["fr_step0"] and not withheld_in(d0) and \
                not ({"dF_meV", "F_sp_eV", "F_k0_eV"} & set(json.dumps(d0).replace('"', " ").split())), (rel, d0)
        assert n_s0 == 3 * (1 + 1 + 2 + 1), n_s0
        assert not hasattr(GateLeaves, "_stop_paths") and "step0_stop" not in GateLeaves.__init__.__code__.co_varnames
        assert "mace" not in sys.modules
        print(f"guard self-test passed: WITHHELD_S2B = {sorted(WITHHELD_S2B)}; {n_raise} withheld or unlisted reads "
              f"raised (record hits {len(rec_hits)} and gate-file hits {len(gate_hits)} of {len(WITHHELD_S2B)} fields, "
              f"dict keys and list elements), {n_read} allowed reads, {n_open} open() refusals in the walk ({n_list_only} "
              f"of dicts whose withheld fields sit only in a list element), "
              f"{refusals} refusals of parents, repr, ==, iteration, open() and decision subtrees with a withheld field; "
              f"no step-0 STOP mode ({n_s0} step-0 dF, passed and cell reads raised in one- and two-cell files)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="The S2b guard (S2B_PLAN.md section 1)")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test())
    ap.print_help()

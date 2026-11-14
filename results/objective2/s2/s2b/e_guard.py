#!/usr/bin/env python
"""The guard of E, the one evaluation of S2b (results/objective2/s2/S2B_PLAN.md section 7, "The E guard", with
amendment 2026-11-12a items 1-3 and the analyst's decisions E_DECISIONS_R1; E_IMPLEMENTATION_SPEC sections 4.1-4.5).

  EGuarded    a C2, fr, c3b or c4b A2 record, gate file, applied-gate marker, campaign.json or state_end.json: the
              D-C2-12 class Guarded of figures/fig_s2_c2_a2.py (loaded unchanged), read by full dotted leaf path from
              a closed list per mode, kind and file (TABLE). Parents, iteration, printing, comparison, copying,
              pickling, has() and open() raise Blinded. A missing segment gives the unprintable sentinel ABSENT.
  eg_load     the only constructor: a listed file of a listed (mode, kind), read once through OpenAudit; an absent
              listed file gives FILE_ABSENT (RF-12). No *.inputs.json path is accepted.
  R1-R6       the static rules of TABLE, checked at import (INT-GUARD) and by self-test A5.
  C1Access    the C1 side of the hinge deferral (S2B:561-563, 579; amendment item 1, OP-1, OP-2, RF-16): MACE
              records only in blocks 3-5 and Pb136 MACE records only in block 5 of a hinge read; the single points of
              blocks 1-3 (NOISE, POSE, Q0) in blocks 1-5, the Pb136 ones only in block 5 of a hinge read; no G1 or
              spin output in any mode. It
              keeps its own (wid, blind, block) log. There is no force-only reader (OP-1).
  OpenAudit   sys.addaudithook on the 'open' event (builtins.open, io.open, os.open, open_code, pathlib, gzip and
              tarfile all raise it; RF-10): every open under a root or the 8bff03e extraction is logged with its
              sha256 at first open, and the refusals of the plan raise before the real open (writes under a root,
              *.inputs.json, a c3 directory segment (RF-2), step0_attempt1/ and discarded/, the hinge outputs outside
              hinge mode, the Pb136 C1 outputs outside block 5 of a hinge read, every G1 and spin output, and in
              self-test mode every real archive path). A tar-member log records every member read.

Blinding. No energy is read here: EGuarded hands out only listed leaves (every one non-energy except the step-0 dF,
the K3 E_b^A2 and the FR-2 values that S2B section 7 and amendment item 3 name), and the C1 single points are read
by the caller's ReadsAudit (e_read.py). Nothing is written. Helpers are loaded with spec_from_file_location from
this directory (RF-19); this directory is never put on sys.path.

    (imported by e_eval.py, e_read.py and e_selftest.py; self-tests: e_selftest.py groups A and B)
"""
import ast, collections, copy, hashlib, importlib.util, json, os, re, sys, threading

HERE = os.path.dirname(os.path.abspath(__file__))
S2 = os.path.normpath(os.path.join(HERE, ".."))                          # results/objective2/s2, the archive root
REPO = os.path.normpath(os.path.join(S2, "..", "..", ".."))


def _load_shared(key, path):
    """One module object per process and file (RF-19): registered in sys.modules under a private key, never through
    sys.path, so that e_eval, e_read and e_selftest share one TABLE, one audit hook and one fig.Guarded."""
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
    if os.path.realpath(m.__file__) != os.path.realpath(path):
        raise ImportError(f"{key} is loaded from {m.__file__}, not {path}")
    return m


def sibling(name):
    """A helper module of this directory (e_guard, e_read, e_block4, e_selftest) under the key '_s2b_<name>', one
    object per process (RF-19). e_eval.py loads its helpers through this key, so that every module shares them."""
    return _load_shared(f"_s2b_{name}", os.path.join(HERE, f"{name}.py"))


fig = _load_shared("_s2b_e_fig_s2_c2_a2", os.path.join(S2, "figures", "fig_s2_c2_a2.py"))   # D-C2-12, unchanged
Blinded = fig.Blinded
WITHHELD = fig.WITHHELD                    # the module-level WITHHELD, unchanged (S2B:544)


class EError(RuntimeError):
    """A refusal of E (exit 2 in phase 0) or a use of E's interfaces that the plan does not allow."""


class EIntegrity(Exception):
    """A failed integrity check (S2B:603-617): printed by check id, file (or tar:member) and key path, never a value."""

    def __init__(self, check, where="", key=""):
        if check not in INT_IDS:
            raise EError(f"unknown integrity check id {check!r}")
        self.check, self.where, self.key = check, str(where), str(key)
        super().__init__(self.line())

    def line(self):
        return " ".join(x for x in ("INTEGRITY FAILED:", self.check, self.where, self.key) if x)


# spec section 8, closed list
INT_IDS = ("INT-IMPORT", "INT-GUARD", "INT-CALC-LOAD", "INT-CALC-EXIT", "INT-ROOT", "INT-SHA", "INT-SHA-STABLE",
           "INT-K3-SHA", "INT-K3-DEC", "INT-K3-NULL", "INT-FR-SHA", "INT-FR-DEC", "INT-ROUTE", "INT-COMMITS",
           "INT-C1-CENSUS", "INT-PARTS", "INT-PARSE", "INT-NCFG", "INT-KLAST", "INT-FINALK", "INT-FINALSHA",
           "INT-FINALPOS", "INT-CELL", "INT-READS", "INT-HINGE-CLOSED", "INT-PB136-REC", "INT-PB136-RAW",
           "INT-STRUCT", "INT-SP")


class Checks:
    """Pass counts of the integrity checks, printed 'INT-x ok (n)'; a failed check raises EIntegrity at once."""

    def __init__(self):
        self.passed = collections.Counter()

    def require(self, cond, check, where="", key=""):
        if check not in INT_IDS:
            raise EError(f"unknown integrity check id {check!r}")
        if cond is not True:
            raise EIntegrity(check, where, key)
        self.passed[check] += 1


class _Sentinel:
    """ABSENT and FILE_ABSENT: tested with 'is'; never printed, formatted, tested for truth or pickled."""
    __slots__ = ("_name",)

    def __init__(self, name):
        object.__setattr__(self, "_name", name)

    def _refuse(self, *a, **kw):
        raise Blinded(f"{object.__getattribute__(self, '_name')} is a sentinel: test it with 'is' (E guard)")

    __repr__ = __str__ = __format__ = __bool__ = __len__ = __iter__ = __float__ = __int__ = __index__ = _refuse
    __reduce__ = __reduce_ex__ = __getstate__ = _refuse

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self


ABSENT = _Sentinel("ABSENT")               # a listed leaf whose path is not in the file
FILE_ABSENT = _Sentinel("FILE_ABSENT")     # a listed file that does not exist (RF-12)

# ---------------------------------------------------------------- constants (restated literals; asserted at load)
CAMPAIGNS = ("c1", "c2", "fr", "c3b", "c4b")                     # spec section 3; no c3 path can be built
PUBLIC_CAMPAIGNS, PRIVATE_CAMPAIGNS = ("c1", "c2", "fr"), ("c3b", "c4b")
HINGE = ("s2r_m30_VB136", "s2r_m30_hostB136", "s2r_m30_Sr136o0_novac", "s2r_m30_Sr136o0_vac")  # relaxations 1-4
FAR = ("s2r_m30_hostB76", "s2r_m30_VB76", "s2r_m30_Sr76o0_novac", "s2r_m30_Sr76o0_vac")        # relaxations 5-8
FR_QUARTET = {"host": "s2r_m30_hostA188", "V": "s2r_m30_VA188", "D": "s2r_m30_Cs188o0_novac",
              "DV": "s2r_m30_Cs188o0_vac"}                                   # S2B section 2; RF-17 (scripts/49)
FR_ORDER = tuple(FR_QUARTET[r] for r in ("host", "V", "D", "DV"))
FR_STEP0_PAIRS = {"s2_m30_VA188": "s2r_m30_VA188", "s2_m30_Cs188o0_vac": "s2r_m30_Cs188o0_vac"}   # SP -> A2
STEP0_PAIRS = {"s2_m30_VB136": "s2r_m30_VB136", "s2_m30_Sr136o0_vac": "s2r_m30_Sr136o0_vac"}       # C2 (P section 11)
FR_STEP0_AT = {"gate:fr_step0@2": "s2r_m30_VA188", "gate:fr_step0@4": "s2r_m30_Cs188o0_vac"}       # scripts/50
FR_DECISION_KEYS = ("outcome", "FR1", "FR2", "part", "cell", "kind")                               # OP-6 (scripts/50)
FR_STEP0_KEYS = ("attempts", "outcome", "repeat", "fix_note", "cell", "attempt1", "no_error_found", "note")
FR_STEP0_ATTEMPT1_KEYS = ("attempts", "outcome", "cell")
FR_OUTCOMES = ("pass", "fail (FR-1)", "fail (FR-2)", "fail (step-0 final; gate not evaluated)")   # scripts/50
FR_ENERGY_FIELDS = ("Eb_A1_meV", "Eb_A2_meV", "delta_far_meV", "dF_meV")                          # scripts/49
FR_INPUT_F = ("F_sp_eV", "F_k0_eV", "F_final_eV")                                                  # s2b/guard.py
WITHHELD_S2B = frozenset(set(WITHHELD) | set(FR_ENERGY_FIELDS) | set(FR_INPUT_F))   # s2b/guard.py, for the canaries
END_ACCEPTED = ("accepted_converged", "accepted_plateau")                                          # P section 11


def applied_id(gid):
    """The gates_applied stem of a runner job id (scripts/50 run_gate): [^A-Za-z0-9_.-] -> '_'."""
    return re.sub(r"[^A-Za-z0-9_.-]", "_", gid)


FR_S0_2, FR_S0_4 = applied_id("gate:fr_step0@2"), applied_id("gate:fr_step0@4")   # gate_fr_step0_2, gate_fr_step0_4
C2_S0_1, C2_S0_4 = applied_id("gate:step0@1"), applied_id("gate:step0@4")         # gate_step0_1, gate_step0_4

# record leaves: S2B:550-552; amendment item 2 (OP-3, OP-4, RF-13)
REC_BASE = ("n_config", "converged_at_k", "k_last", "final_geometry.k", "final_geometry.sha256", "restarts",
            "reruns_from_zero", "status", "end_rule.outcome")
REC_ADD = ("layout.ranks", "validity_final.valid", "validity_final.failed", "end_rule.end")
REC_FR_ADD = ("validity_final.check5_reading", "validity_final.valid_as_written", "validity_final.failed_as_written",
              "validity_final.invariant_only")
DEC_FR = tuple(f"decision.FR.{k}" for k in FR_DECISION_KEYS)
DEC_FR_STEP0 = tuple(f"decision.fr_step0.{k}" for k in FR_STEP0_KEYS if k != "attempt1") + \
    tuple(f"decision.fr_step0.attempt1.{k}" for k in FR_STEP0_ATTEMPT1_KEYS)


def _cells(sp):
    return (f"result.cells.{sp}.dF_meV", f"result.cells.{sp}.passed")


def _raw(c, labs):
    return tuple(f"{c}/raw/{lab}.a2.json" for lab in labs)


# TABLE[mode][kind] = {"files": explicit root-relative paths, "get": leaves of every file, "get_by_file": {file: extra
# leaves of that file only} (RF-5: one step-0 leaf set per file), "is_none": leaves tested only with 'is None'}
TABLE = {
    "far": {                                                             # every run, the hinge run included
        "k3": {"files": ("c2/gates/K3.json", f"c2/gates_applied/gate_K3.gate.json"),
               "get": ("decision.K3", "result.checks_failed", "result.Eb_A2_meV.far"),
               "is_none": ("result.value_meV",)},                       # S2B:547-548, 553-554
        "k3_marker": {"files": ("c2/gates_applied/gate_K3.json",),
                      "get": ("decision.K3", "gate_file_sha256")},       # OP-5, A2: decision.K3, not decision
        "a2_far": {"files": _raw("c2", FAR), "get": REC_BASE + REC_ADD},              # relaxations 5-8
        "a2_hinge_counts": {"files": _raw("c2", HINGE),
                            "get": ("n_config", "end_rule.outcome") + REC_ADD},       # 1-4; OP-4, RF-13
        "campaign_c2": {"files": ("c2/campaign.json",), "get": ("commit", "status")},  # OP-25
    },
    "fr": {                                                              # every run (S2B:555-557)
        "a2_fr": {"files": _raw("fr", FR_ORDER), "get": REC_BASE + REC_ADD + REC_FR_ADD},
        "fr_gate": {"files": ("fr/gates/FR.json", "fr/gates_applied/gate_FR.gate.json"),
                    "get": DEC_FR + ("result.checks_failed", "result.end_rule_failed", "result.cells_not_run",
                                     "result.FR2.Eb_A1_meV", "result.FR2.Eb_A2_meV", "result.FR2.delta_far_meV",
                                     "result.invariant_only")},          # OP-6, OP-7, OP-8
        "fr_marker": {"files": ("fr/gates_applied/gate_FR.json",), "get": DEC_FR + ("gate_file_sha256",)},
        "fr_step0_gate": {"files": ("fr/gates/fr_step0.json", f"fr/gates_applied/{FR_S0_2}.gate.json",
                                    f"fr/gates_applied/{FR_S0_4}.gate.json"),
                          "get": DEC_FR_STEP0,
                          "get_by_file": {f"fr/gates_applied/{FR_S0_2}.gate.json": _cells("s2_m30_VA188"),
                                          f"fr/gates_applied/{FR_S0_4}.gate.json": _cells("s2_m30_Cs188o0_vac"),
                                          "fr/gates/fr_step0.json": _cells("s2_m30_Cs188o0_vac")}},   # RF-5, A3
        "fr_step0_marker": {"files": (f"fr/gates_applied/{FR_S0_2}.json", f"fr/gates_applied/{FR_S0_4}.json"),
                            "get": DEC_FR_STEP0 + ("gate_file_sha256",)},
        "campaign_fr": {"files": ("fr/campaign.json",),
                        "get": ("status", "commit", "start_commit", "fr_outcome", "stop_reason",
                                "commit_history[].to")},     # OP-25, RF-3 (.to only; .from is never read)
        # integration (IX-2): fr_step0.no_error_found is the non-energy outcome leaf that fr/STEP0_NO_ERROR sets in the
        # state only (W 50 preconditions, N-FR6); the step-0 gate files keep attempt 1's fail_pending_fix
        "state_fr": {"files": ("fr/state_end.json",),
                     "get": ("commit", "campaigns.fr", "campaign_commit.fr", "fr_step0.attempts",
                             "fr_step0.outcome", "fr_step0.cell", "fr_step0.no_error_found") +
                            tuple(f"FR.{k}" for k in FR_DECISION_KEYS) + ("fr_stop.at", "fr_stop.kind")},
    },
    "hinge": {                                                           # block 5 and the hinge run only (S2B:560)
        "k3": {"files": ("c2/gates/K3.json", "c2/gates_applied/gate_K3.gate.json"),
               "get": ("decision.K3", "result.checks_failed", "result.Eb_A2_meV.far", "result.Eb_A2_meV.hinge"),
               "is_none": ("result.value_meV",)},                       # RF-7: .far in far and hinge modes
        "a2_hinge": {"files": _raw("c2", HINGE), "get": REC_BASE + REC_ADD},
        "step0_c2": {"files": ("c2/gates/step0.json", f"c2/gates_applied/{C2_S0_1}.gate.json",
                               f"c2/gates_applied/{C2_S0_4}.gate.json"),
                     "get": ("decision.step0.outcome",),
                     "get_by_file": {f"c2/gates_applied/{C2_S0_1}.gate.json": _cells("s2_m30_VB136"),
                                     f"c2/gates_applied/{C2_S0_4}.gate.json": _cells("s2_m30_Sr136o0_vac"),
                                     "c2/gates/step0.json": _cells("s2_m30_Sr136o0_vac")}},       # RF-5, A3
    },
    "tier": {},                       # block 4 (spec section 13): fixed with the c3b and c4b code, before C3b
    "c4b": {},
}
MODES = tuple(TABLE)

# ---------------------------------------------------------------- static rules R1-R6 (spec 4.3; RF-7)
R1_SEGMENTS = frozenset({"state_in", "inputs_in", "c1_in", "inputs_opened", "opened", "inputs_digest"})
R3_EXCEPTION = ("fr", "fr_gate", "result.FR2.Eb_A2_meV")                # OP-7, amendment item 2
NEVER_FILES = ("HARD_CAP.json", "ledger.json", "graph.json", "completeness.json", "runner_reads.json")   # 4.2
_GLOB = re.compile(r"[*?\[\]{}]")
_PATH_RE = re.compile(r"[A-Za-z0-9_]+(\[\])?(\.[A-Za-z0-9_]+(\[\])?)*")


def leaves(mode, kind, rel, which="get"):
    """The listed leaves of one file of (mode, kind): the kind's list plus the file's own list (RF-5)."""
    t = TABLE[mode][kind]
    if which == "is_none":
        return frozenset(t.get("is_none", ()))
    return frozenset(t.get("get", ())) | frozenset(t.get("get_by_file", {}).get(rel, ()))


def check_table(table):
    """R1-R6 on a TABLE; the first violation raises EIntegrity('INT-GUARD', '<mode>/<kind>', '<rule> <path>')."""
    def bad(mode, kind, rule, what):
        raise EIntegrity("INT-GUARD", f"{mode}/{kind}", f"{rule} {what}")
    for mode, kinds in table.items():
        for kind, t in kinds.items():
            if set(t) - {"files", "get", "get_by_file", "is_none"} or not isinstance(t.get("files"), tuple):
                bad(mode, kind, "R6", "entry shape")
            files = t["files"]
            for f in files:                                              # R6: explicit, no inputs file, no c3
                segs = f.split("/")
                if (_GLOB.search(f) or f.endswith(".inputs.json") or f.startswith("/") or ".." in segs or
                        segs[0] not in CAMPAIGNS or f.endswith(".validity_final.json") or "logs" in segs or
                        any(s.startswith(("step0_attempt1", "discarded")) for s in segs) or segs[-1] in NEVER_FILES):
                    bad(mode, kind, "R6", f)
            if set(t.get("get_by_file", {})) - set(files):
                bad(mode, kind, "R6", "get_by_file names a file outside the list")
            paths = [("get", p) for p in t.get("get", ())] + [("is_none", p) for p in t.get("is_none", ())] + \
                [("get", p) for v in t.get("get_by_file", {}).values() for p in v]
            for which, p in paths:
                if not isinstance(p, str) or not _PATH_RE.fullmatch(p) or "*" in p:
                    bad(mode, kind, "R6", f"path {p!r}")
                segs = [s[:-2] if s.endswith("[]") else s for s in p.split(".")]
                if R1_SEGMENTS & set(segs):
                    bad(mode, kind, "R1", p)
                if "dF_200_180_meV" in segs:
                    bad(mode, kind, "R2", p)
                if segs[-1] in WITHHELD and (mode, kind, p) != R3_EXCEPTION and \
                        not (which == "is_none" and segs[-1] == "value_meV"):
                    bad(mode, kind, "R3", p)
                if "value_meV" in segs and which != "is_none":
                    bad(mode, kind, "R3", p)
                if which == "is_none" and (mode, kind, p) not in (("far", "k3", "result.value_meV"),
                                                                  ("hinge", "k3", "result.value_meV")):
                    bad(mode, kind, "R3", p)                             # value_meV only in an is_none list
                if p == "result.Eb_A2_meV.far" and mode not in ("far", "hinge"):
                    bad(mode, kind, "R4", p)
                if p == "result.Eb_A2_meV.hinge" and mode != "hinge":
                    bad(mode, kind, "R4", p)
                if p.startswith("result.FR2.") and mode != "fr":
                    bad(mode, kind, "R4", p)
                if segs[-1] == "dF_meV":                                 # step-0 values (amendment item 3)
                    sp = segs[2] if len(segs) == 4 and segs[:2] == ["result", "cells"] else None
                    if not ((sp in FR_STEP0_PAIRS and mode == "fr") or (sp in STEP0_PAIRS and mode == "hinge")):
                        bad(mode, kind, "R4", p)
                if "Eb_A2_meV" in segs[:-1] and kind != "k3":
                    bad(mode, kind, "R5", p)
                for s in segs:
                    if s in WITHHELD_S2B and s not in ("Eb_A2_meV", "value_meV", "dF_200_180_meV") and \
                            not (mode == "fr" and p.startswith("result.FR2.")) and \
                            not (s == "dF_meV" and segs[:2] == ["result", "cells"]):
                        bad(mode, kind, "R3", p)                         # an S2b energy name outside its place
    return True


check_table(TABLE)                                      # INT-GUARD at import (spec 4.3)


# ---------------------------------------------------------------- EGuarded (spec 4.1; OP-3..8, RF-7, RF-12)
def _leaf(x, rel, path):
    """A listed leaf value: None, bool, int, float, str, or a deep-copied list of str, int or bool. A dict, or a list
    holding a dict or list, is a parent and is refused; any other type is INT-STRUCT."""
    if isinstance(x, dict) or (isinstance(x, list) and any(isinstance(e, (dict, list)) for e in x)):
        raise Blinded(f"{rel}: {path} is a parent, not a leaf (E guard)")
    if isinstance(x, list):
        if not all(isinstance(e, (str, int)) and not isinstance(e, float) for e in x):
            raise EIntegrity("INT-STRUCT", rel, path)
        return copy.deepcopy(x)
    if x is None or isinstance(x, (bool, int, float, str)):
        return x
    raise EIntegrity("INT-STRUCT", rel, path)


def _walk(d, rel, path):
    """The leaf at a full dotted path, walked on the raw JSON; a 'name[]' segment projects a list of dicts (commit
    history only), which must hold the rest of the path in every element."""
    segs = path.split(".")
    x = d
    for i, s in enumerate(segs):
        if s.endswith("[]"):
            if not isinstance(x, dict) or s[:-2] not in x:
                return ABSENT
            lst = x[s[:-2]]
            if not isinstance(lst, list):
                raise EIntegrity("INT-STRUCT", rel, path)
            out = []
            for e in lst:
                v = _walk(e, rel, ".".join(segs[i + 1:])) if isinstance(e, dict) else ABSENT
                if v is ABSENT or isinstance(v, list):
                    raise EIntegrity("INT-STRUCT", rel, path)
                out.append(v)
            return out
        if not isinstance(x, dict) or s not in x:
            return ABSENT
        x = x[s]
    return _leaf(x, rel, path)


class EGuarded(fig.Guarded):
    """An archive JSON read by full dotted leaf path from the closed list of its mode, kind and file (S2B:540-545)."""
    __slots__ = ("_mode", "_kind")

    def __init__(self, d, path, *, mode, kind):
        fig.Guarded.__init__(self, d, path)
        self._mode, self._kind = mode, kind

    def get(self, path):
        if not isinstance(path, str) or path not in leaves(self._mode, self._kind, self._p):
            raise Blinded(f"{self._p}: {path!r} is not on the {self._mode}/{self._kind} list of the E guard")
        return _walk(self._d, self._p, path)

    def is_none(self, path):
        if not isinstance(path, str) or path not in leaves(self._mode, self._kind, self._p, "is_none"):
            raise Blinded(f"{self._p}: {path!r} is not tested with 'is None' in {self._mode}/{self._kind}")
        x = self._d
        for s in path.split("."):
            if not isinstance(x, dict) or s not in x:
                raise EIntegrity("INT-STRUCT", self._p, path)
            x = x[s]
        return x is None

    def listed(self):
        """The listed get-paths of this file, sorted (a closed list, not the file's keys)."""
        return tuple(sorted(leaves(self._mode, self._kind, self._p)))

    def where(self):
        return self._p

    def _refuse(self, *a, **kw):
        raise Blinded(f"{self._p} is read by full dotted leaf path only (E guard, S2B section 7)")

    has = open = _wrap = _refuse
    __reduce__ = __reduce_ex__ = __copy__ = __deepcopy__ = __getstate__ = __setstate__ = _refuse


def eg_load(L, c, relpath, *, mode, kind, audit=None):
    """The one constructor of EGuarded (spec 4.1; RF-12). L: an ELayout; c: the campaign; relpath: relative to it."""
    rel = f"{c}/{relpath}"
    if rel.endswith(".inputs.json") or ".inputs." in os.path.basename(rel):
        raise Blinded(f"{rel}: inputs files are never opened (S2B:545)")
    if mode not in TABLE or kind not in TABLE[mode]:
        raise Blinded(f"{mode}/{kind} is not a kind of the E guard")
    if rel not in TABLE[mode][kind]["files"]:
        raise Blinded(f"{rel} is not a file of {mode}/{kind}")
    audit = audit or OpenAudit.current()
    if audit is None:
        raise EError("eg_load outside OpenAudit")
    if mode == "hinge" and not audit.hinge:
        raise Blinded(f"{rel}: hinge mode is not open (S2B:560, 696-697)")
    path = L.file(c, relpath)
    if not os.path.exists(path):
        return FILE_ABSENT
    with audit.via(kind):
        with open(path, "rb") as fh:
            data = fh.read()
    return EGuarded(json.loads(data), rel, mode=mode, kind=kind)


# ---------------------------------------------------------------- C1 constants (spec 4.4; map 2 section 2b)
PILOTS, LEGS = ("m30", "m05"), ("novac", "vac")
TOKENS_OF = {"B": ("Sr", "Ca"), "A": ("Cs", "GA"), "X": ("Cl",)}
SUBLATTICE = {"Sr": "B", "Ca": "B", "Cl": "X", "Cs": "A", "GA": "A"}
FAR4 = {"m30": {"B": (76, 172, 24, 148), "A": (188, 164, 176, 200), "X": (175, 186, 222, 174)},
        "m05": {"B": (76, 172, 24, 64), "A": (188, 164, 152, 68), "X": (175, 222, 186, 174)}}   # scripts/46 FAR4_TABLE
CAL = {"m30": {"B": 136, "A": 128, "X": 138}, "m05": {"B": 124, "A": 28, "X": 49}}           # scripts/46 CAL_SITES
POSE_SITES = {"Cs": (128, 188), "Cl": (138, 175)}                                            # scripts/46 POSE_SITES
WORK_RE = re.compile(r"s2_(?P<host>m\d\d|ref233)_(?:(?P<hostcell>host)|V(?P<vL>[BAX])(?P<vj>(?:0|[1-9]\d*))"
                     r"|(?P<tok>Sr|Ca|Cl|Cs|GA)(?P<j>(?:0|[1-9]\d*))p(?P<n>(?:0|[1-9]\d*))_(?P<leg>novac|vac))")


def lab_host(h):
    return f"s2_{h}_host"


def lab_v(h, L, j):
    return f"s2_{h}_V{L}{j}"


def lab_dop(h, tok, j, leg, k=0):
    return f"s2_{h}_{tok}{j}o{k}_{leg}"


PB136_WIDS = ("s2_m30_VB136", "s2_m30_Sr136p0_novac", "s2_m30_Sr136p0_vac", "s2_m30_Ca136p0_novac",
              "s2_m30_Ca136p0_vac")
PB136_SP = ("s2_m30_VB136", "s2_m30_Sr136o0_vac", "s2_m30_VB136_q0", "s2_m30_Sr136o0_vac_q0",
            "s2_m30_Ca136o0_vac_q0")
PB136_LABELS = ("s2_m30_VB136", "s2_m30_Sr136o0_novac", "s2_m30_Sr136o0_vac", "s2_m30_Ca136o0_novac",
                "s2_m30_Ca136o0_vac") + PB136_SP[2:]                  # every C1 label of a Pb136 cell
NEVER_SP = ("s2g1_m30_host_e60", "s2g1_m30_Cl138o0_novac_e50", "s2g1_m30_Cl138o0_novac_e60",
            "s2g1_m30_Ca136o0_novac_e50", "s2g1_m30_Ca136o0_novac_e60", "s2spin_m30_Cl175o0_vac",
            "s2spin_m30_Ca76o0_vac")                                  # OP-2: no G1 or spin output in any mode
NOISE_SP = tuple(sorted({lab_host(p) for p in PILOTS} |
                        {lab_v(p, L, j) for p in PILOTS for L in "BAX" for j in FAR4[p][L]} |
                        {lab_dop(p, t, j, leg) for p in PILOTS for L in "BAX" for j in FAR4[p][L]
                         for t in TOKENS_OF[L] for leg in LEGS}))
POSE_SP = ("s2_m30_Cs128o0_novac", "s2_m30_Cs128o0_vac", "s2_m30_Cl138o0_novac", "s2_m30_Cl138o0_vac")
Q0_SP = ("s2_m30_VB76_q0", "s2_m30_Sr76o0_vac_q0", "s2_m30_VX138_q0", "s2_m30_Cl138o0_vac_q0", "s2_m30_VA128_q0",
         "s2_m30_Cs128o0_vac_q0", "s2_m30_GA128o0_vac_q0")
BLOCK3_SP = frozenset(NOISE_SP) | frozenset(POSE_SP) | frozenset(Q0_SP)
SP_SETS = {"noise": NOISE_SP, "pose": POSE_SP, "q0": Q0_SP, "pb136": PB136_SP, "never": NEVER_SP}
N_SP = 129                                                            # c1/raw stems, listed by name 2026-11-12
CLASSES = ("host", "V", "noise", "startset", "pose_start", "pb136")
CLASS_COUNTS = {"host": 2, "V": 29, "noise": 80, "startset": 16, "pose_start": 28, "pb136": 5}   # 155 + 5 = 160
BLOCK3_CLASSES = ("host", "V", "noise", "startset", "pose_start")
MACE_LEAVES_BLOCK3 = 161                                              # 2 x 4 (host stages) + 153 x 1
assert sum(len(v) for v in SP_SETS.values()) == N_SP == len(set().union(*SP_SETS.values()))
assert sum(CLASS_COUNTS.values()) == 160 and len(NOISE_SP) == 106


def classify_wid(wid):
    """C1 record class (map 2 section 2b; scripts/50 graph_c1 categories with first-definition precedence)."""
    m = WORK_RE.fullmatch(wid)
    if not m:
        raise EIntegrity("INT-C1-CENSUS", f"c1/records/{wid}.json", "WORK_RE")
    g = m.groupdict()
    h = g["host"]
    if h not in PILOTS:
        raise EIntegrity("INT-C1-CENSUS", f"c1/records/{wid}.json", "member")
    if g["hostcell"]:
        return "host"
    if g["vL"]:
        L, j = g["vL"], int(g["vj"])
        return "pb136" if (h, L, j) == ("m30", "B", 136) else "V"
    tok, j, n = g["tok"], int(g["j"]), int(g["n"])
    if h == "m30" and tok in ("Sr", "Ca") and j == 136:
        return "pb136"
    L = SUBLATTICE[tok]
    if n >= 1:
        return "pose_start"
    if j in FAR4[h][L]:
        return "noise"
    if j == CAL[h][L]:
        return "startset"
    raise EIntegrity("INT-C1-CENSUS", f"c1/records/{wid}.json", "class")


def assert_restated(g49, c46):
    """INT-IMPORT: the literals of this module equal the 8bff03e objects (OP-26, amendment item 7)."""
    pins = (("FAR4_TABLE", {p: {L: tuple(v) for L, v in d.items()} for p, d in c46.FAR4_TABLE.items()}, FAR4),
            ("CAL_SITES", c46.CAL_SITES, CAL), ("POSE_SITES", {k: tuple(v) for k, v in c46.POSE_SITES.items()},
                                                POSE_SITES),
            ("WORK_RE", c46.WORK_RE.pattern, WORK_RE.pattern), ("K3_QUARTETS.far", tuple(
                g49.K3_QUARTETS["far"][r] for r in ("host", "V", "D", "DV")), FAR),
            ("K3_QUARTETS.hinge", {g49.K3_QUARTETS["hinge"][r] for r in ("host", "V", "D", "DV")}, set(HINGE)),
            ("A2_ORDER.c2", tuple(g49.A2_ORDER["c2"][:8]), HINGE + FAR), ("STEP0_PAIRS", g49.STEP0_PAIRS, STEP0_PAIRS),
            ("END_ACCEPTED", tuple(g49.RULES["END_ACCEPTED"]), END_ACCEPTED),
            ("TOKENS_OF", {k: tuple(v) for k, v in g49.TOKENS_OF.items()}, TOKENS_OF),
            ("SUBLATTICE", g49.SUBLATTICE, SUBLATTICE), ("PILOTS", tuple(g49.PILOTS), PILOTS),
            ("LEGS", tuple(g49.LEGS), LEGS), ("G1_LABELS", set(c46.G1_LABELS) | set(c46.SPIN_LABELS), set(NEVER_SP)))
    for name, obj, lit in pins:
        if obj != lit:
            raise EIntegrity("INT-IMPORT", "8bff03e", name)
    for p in PILOTS:                                       # every label E builds, against the 8bff03e builders
        if lab_host(p) != g49.lab_host(p):
            raise EIntegrity("INT-IMPORT", "8bff03e", "lab_host")
    for lab in NOISE_SP + POSE_SP:
        m = re.fullmatch(r"s2_(m\d\d)_(?:(host)|V([BAX])(\d+)|([A-Za-z]+?)(\d+)o(\d+)_(novac|vac))", lab)
        h, host, vL, vj, tok, j, k, leg = m.groups()
        ref = g49.lab_host(h) if host else g49.lab_v(h, vL, int(vj)) if vL else g49.lab_dop(h, tok, int(j), leg, int(k))
        if ref != lab:
            raise EIntegrity("INT-IMPORT", "8bff03e", f"label {lab}")
    return True


def check_fr_constants(src49, src50):
    """RF-17, OP-6: the FR literals of this module against HEAD's scripts/49 and 50, parsed with ast and never
    executed. FR_ORDER is the generator tuple(FR_QUARTET[r] for r in (<literal tuple>)) there; only that form is
    accepted. Raises EIntegrity('INT-IMPORT', <file>, <name>)."""
    def assigns(src, fn):
        out = {}
        for node in ast.parse(src).body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                out[node.targets[0].id] = node.value
        return out
    a49, a50 = assigns(src49, "scripts/49_s2_gates.py"), assigns(src50, "scripts/50_s2_campaign.py")

    def lit(a, name, fn):
        if name not in a:
            raise EIntegrity("INT-IMPORT", fn, name)
        try:
            return ast.literal_eval(a[name])
        except ValueError:
            raise EIntegrity("INT-IMPORT", fn, name) from None
    f49, f50 = "scripts/49_s2_gates.py", "scripts/50_s2_campaign.py"
    q = lit(a49, "FR_QUARTET", f49)
    node = a49.get("FR_ORDER")
    try:
        order = ast.literal_eval(node)
    except ValueError:
        ok = (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "tuple" and
              len(node.args) == 1 and isinstance(node.args[0], ast.GeneratorExp))
        g = node.args[0] if ok else None
        ok = ok and len(g.generators) == 1 and isinstance(g.elt, ast.Subscript) and \
            isinstance(g.elt.value, ast.Name) and g.elt.value.id == "FR_QUARTET" and \
            isinstance(g.elt.slice, ast.Name) and isinstance(g.generators[0].target, ast.Name) and \
            g.elt.slice.id == g.generators[0].target.id and not g.generators[0].ifs
        if not ok:
            raise EIntegrity("INT-IMPORT", f49, "FR_ORDER") from None
        order = tuple(q[r] for r in ast.literal_eval(g.generators[0].iter))
    for name, got, want in (("FR_QUARTET", q, FR_QUARTET), ("FR_ORDER", tuple(order), FR_ORDER),
                            ("FR_STEP0_PAIRS", lit(a49, "FR_STEP0_PAIRS", f49), FR_STEP0_PAIRS),
                            ("FR_ENERGY_FIELDS", tuple(lit(a49, "FR_ENERGY_FIELDS", f49)), FR_ENERGY_FIELDS)):
        if got != want:
            raise EIntegrity("INT-IMPORT", f49, name)
    for name, want in (("FR_DECISION_KEYS", FR_DECISION_KEYS), ("FR_STEP0_KEYS", FR_STEP0_KEYS),
                       ("FR_OUTCOMES", FR_OUTCOMES), ("FR_STEP0_AT", FR_STEP0_AT)):
        got = lit(a50, name, f50)
        if (tuple(got) if isinstance(got, (list, tuple)) else got) != want:
            raise EIntegrity("INT-IMPORT", f50, name)
    return True


# ---------------------------------------------------------------- C1Access (spec 4.4; OP-1, OP-2, RF-16, RF-20)
class C1Access:
    """C1 records and single points (S2B:561-563, 579). L: ELayout; c46, q47: the 8bff03e objects; audit:
    OpenAudit; reads: e_read.ReadsAudit (it performs and audits the parse); hinge: block 5 of a hinge read is open."""

    def __init__(self, L, c46, q47, audit, reads, *, hinge=False):
        self.L, self.c46, self.q47, self.audit, self.reads, self.hinge = L, c46, q47, audit, reads, bool(hinge)
        self.log = []                         # (wid, blind, block) per record() call (RF-16)
        self.wids, self.sp_stems, self._blind, self._sp, self.label_wid = (), (), {}, {}, {}

    def open_hinge(self):
        """Block 5 of a hinge read (spec 14.1); one way."""
        self.hinge = True

    def load_census(self):
        """The record and single-point names (listed, never opened here), the classes, and every record loaded with
        blind=True (validity, labels, free set). INT-C1-CENSUS."""
        rdir, sdir = self.L.cdir("c1", "records"), self.L.cdir("c1", "raw")
        names = sorted(os.listdir(rdir))
        if any(not n.endswith(".json") for n in names):
            raise EIntegrity("INT-C1-CENSUS", "c1/records", "file name")
        self.wids = tuple(n[:-5] for n in names)
        self.sp_stems = tuple(sorted(n[:-7] for n in os.listdir(sdir) if n.endswith(".out.gz")))
        self.assert_closed("load")
        for w in self.wids:
            rec = self.record(w, blind=True, block=None)
            if json.dumps(rec).find('"E_mace_eV"') >= 0:
                raise EIntegrity("INT-PB136-REC" if w in PB136_WIDS else "INT-STRUCT", f"c1/records/{w}.json",
                                 "E_mace_eV in a blind record")
            self._blind[w] = rec
            for lab in rec.get("labels") or []:
                if lab in self.label_wid:
                    raise EIntegrity("INT-C1-CENSUS", f"c1/records/{w}.json", f"labels {lab}")
                self.label_wid[lab] = w
        return self

    def blind(self, wid):
        """The blind record of a census wid (loaded once by load_census)."""
        return self._blind[wid]

    def classes(self):
        return {w: classify_wid(w) for w in self.wids}

    def record(self, wid, *, blind, block):
        if not self.wids or wid not in self.wids:
            raise EError(f"{wid} is not a C1 record of the census")
        if not blind:
            if block not in (3, 4, 5):
                raise Blinded(f"{wid}: MACE records are read in blocks 3-5 only (S2B:579)")
            if wid in PB136_WIDS and not (self.hinge and block == 5):
                raise Blinded(f"{wid}: a Pb136 MACE record is read only in block 5 of a hinge read (S2B:561-563)")
        self.log.append((wid, bool(blind), block))
        return self.c46.load_record(self.L.record("c1", wid), blind=bool(blind))

    def base_free(self, label):
        """The free set of a single point's cell record; a _q0 label takes its base record (spec 4.4)."""
        base = label[:-3] if label.endswith("_q0") else label
        w = self.label_wid.get(base)
        if w is None:
            raise EIntegrity("INT-SP", f"c1/raw/{label}", "no cell record for the label")
        return self._blind[w].get("free")

    def allowed_sp(self, block):
        if block in (1, 2, 3, 4):
            return BLOCK3_SP
        if block == 5 and self.hinge:
            return BLOCK3_SP | frozenset(PB136_SP)
        return frozenset()

    def sp_full(self, label, *, block):
        """sp_status, then parse_sp(read='full', free=<base record free>) through the ReadsAudit; cached per label."""
        if label in NEVER_SP:
            raise Blinded(f"{label}: no G1 or spin output is opened by E (OP-2)")
        if label not in self.allowed_sp(block):
            raise Blinded(f"{label}: not a single point of block {block} (S2B:561-563; amendment item 1)")
        if label in self._sp:
            return self._sp[label]
        if label not in self.sp_stems:
            raise EIntegrity("INT-SP", f"c1/raw/{label}.out.gz", "absent")
        q = self.q47
        try:
            st = q.sp_status(self.L.cdir("c1", "raw"), label)
        except (q.S2Error, q.Refused) as e:                      # RF-20
            raise EIntegrity("INT-SP", f"c1/raw/{label}", f"stage sp_status {type(e).__name__}") from None
        if st.get("status") != "complete":
            raise EIntegrity("INT-SP", f"c1/raw/{label}.out.gz", "status")
        free = self.base_free(label)
        r = self.reads.parse_sp(label, self.L.raw("c1", f"{label}.out.gz"), free=free, block=block)
        if r.get("F_eV") is None or r.get("forces") is None or r.get("scf_converged") is not True:
            raise EIntegrity("INT-SP", f"c1/raw/{label}.out.gz", "F_eV, forces, scf_converged")
        out = {"label": label, "status": "complete", "F_eV": r["F_eV"], "forces": copy.deepcopy(r["forces"]),
               "scf_converged": True}
        self._sp[label] = out
        return out

    def assert_closed(self, stage):
        """load: the constants against the classifier and the census (INT-C1-CENSUS); exit: no Pb136 MACE record and no
        Pb136 c1/raw path outside block 5 of a hinge read, and no G1 or spin path (INT-PB136-REC, INT-PB136-RAW)."""
        if stage == "load":
            cls = collections.Counter()
            for w in self.wids:
                cls[classify_wid(w)] += 1
            if dict(cls) != CLASS_COUNTS:
                raise EIntegrity("INT-C1-CENSUS", "c1/records", "class counts")
            if tuple(sorted(w for w in self.wids if classify_wid(w) == "pb136")) != tuple(sorted(PB136_WIDS)):
                raise EIntegrity("INT-C1-CENSUS", "c1/records", "PB136_WIDS")
            if set(self.sp_stems) != set().union(*SP_SETS.values()) or len(self.sp_stems) != N_SP:
                raise EIntegrity("INT-C1-CENSUS", "c1/raw", "single-point stems")
            return True
        if stage != "exit":
            raise EError(f"assert_closed stage {stage!r}")
        for w, b, blk in self.log:
            if w in PB136_WIDS and not b and not (self.hinge and blk == 5):
                raise EIntegrity("INT-PB136-REC", f"c1/records/{w}.json", "blind=False outside block 5")
        for rel, e in self.audit.log.items():
            segs = e["rel"].split("/")
            if e["base"] != "root" or segs[:2] != ["c1", "raw"] or len(segs) != 3:
                continue
            stem = segs[2].split(".")[0]
            if stem in NEVER_SP:
                raise EIntegrity("INT-PB136-RAW", e["rel"], "G1 or spin output opened")
            if stem in PB136_SP and not (e["hinge"] and e["block"] == 5):
                raise EIntegrity("INT-PB136-RAW", e["rel"], "opened outside block 5")
        return True


# ---------------------------------------------------------------- OpenAudit (spec 4.5; RF-2, RF-9, RF-10, RF-11)
C3_NAMES = ("c3", "c3.tar", "c3.tar.gz", "c3.tgz", "c3_notrun")       # RF-2, case-insensitive
C3_DIR_RE = re.compile(r"c3([._-].*)?", re.I)                         # directories and symlinks only (RF-2)
SELFTEST_BLOCKED = ("c1/records", "c1/raw", "c1/gates", "c1/gates_applied", "c1/structures.tar.gz", "c2", "fr",
                    "c3b", "c4b")                                    # spec 4.5, self-test mode
E_OUTPUT_RE = re.compile(r"s2b/E_(output|hinge_output)(_attempt[23])?\.txt|"
                         r"figures/source_data/fig_s2b_e_fk(_attempt[23]|_hinge(_attempt2)?)?(_meta)?\.csv")   # RF-11
_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
_TL = threading.local()
_STATE = {"installed": False, "active": None, "blocked": []}         # one hook per process; blocked: self-test


def _under(rp, base):
    return rp == base or rp.startswith(base.rstrip(os.sep) + os.sep)


def _sha256_file(path):
    h = hashlib.sha256()
    prev = getattr(_TL, "busy", False)
    _TL.busy = True
    try:
        with open(path, "rb") as fh:
            for b in iter(lambda: fh.read(1 << 20), b""):
                h.update(b)
    finally:
        _TL.busy = prev
    return h.hexdigest()


def _hook(event, args):
    if event != "open" or getattr(_TL, "busy", False):
        return
    path = args[0] if args else None
    if path is None or isinstance(path, int):
        return
    try:
        p = os.fsdecode(path)
    except TypeError:
        return
    _TL.busy = True
    try:
        rp = os.path.realpath(p)
    finally:
        _TL.busy = False
    mode = args[1] if len(args) > 1 else None
    flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
    write = bool(flags & _WRITE_FLAGS) or (isinstance(mode, str) and any(ch in mode for ch in "wax+"))
    for base in _STATE["blocked"]:                                   # self-test mode: every real archive path
        if _under(rp, base):
            raise Blinded(f"self-test: a real archive path was opened: {base} (S2B:601)")
    a = _STATE["active"]
    if a is not None:
        a._on_open(rp, mode, write)


def selftest_block(s2_dirs, private_root=None):
    """Self-test mode (spec 4.5): refuse every real archive path under these S2 roots for the rest of the process.
    Returns the list of prefixes added; selftest_unblock removes only those (the real ones are never removed by the
    self-test runner)."""
    _install()
    added = []
    for s2 in s2_dirs:
        for rel in SELFTEST_BLOCKED:
            rp = os.path.realpath(os.path.join(s2, rel))
            if rp not in _STATE["blocked"]:
                _STATE["blocked"].append(rp); added.append(rp)
    if private_root:
        rp = os.path.realpath(private_root)
        if rp not in _STATE["blocked"]:
            _STATE["blocked"].append(rp); added.append(rp)
    return added


def selftest_unblock(added):
    for rp in added:
        if rp in _STATE["blocked"]:
            _STATE["blocked"].remove(rp)


def selftest_blocked(path):
    """True if a path would be refused by the self-test refusals (no open)."""
    rp = os.path.realpath(path)
    return any(_under(rp, b) for b in _STATE["blocked"])


def real_s2_dirs():
    """The S2 archive roots of this checkout, of the main checkout and of its worktrees (listed by name only), for the
    self-test refusals."""
    out = [S2]
    main = REPO.split(os.sep + os.path.join(".claude", "worktrees") + os.sep)[0]
    out.append(os.path.join(main, "results", "objective2", "s2"))
    wt = os.path.join(main, ".claude", "worktrees")
    if os.path.isdir(wt):
        out += [os.path.join(wt, n, "results", "objective2", "s2") for n in sorted(os.listdir(wt))]
    seen, res = set(), []
    for s in out:
        r = os.path.realpath(s)
        if r not in seen:
            seen.add(r); res.append(r)
    return res


def _install():
    if not _STATE["installed"]:
        sys.addaudithook(_hook)                                     # permanent for the process (PEP 578)
        _STATE["installed"] = True


class OpenAudit:
    """The open log and refusals of E (spec 4.5). roots: {"root": S2 root, "private": private root or None};
    tmp: directories logged but not refused (the 8bff03e extraction)."""

    def __init__(self, root, *, private_root=None, tmp=()):
        self.roots = [("root", os.path.realpath(root))] + \
            ([("private", os.path.realpath(private_root))] if private_root else [])
        self.tmp = [os.path.realpath(t) for t in tmp]
        self.log = collections.OrderedDict()   # realpath -> {rel, base, sha256, block, hinge, n, via}
        self.members = []                      # (tar rel, member name, block, hinge)
        self.refused = []                      # (rel, reason)
        self.block, self.hinge, self._via = None, False, None

    @staticmethod
    def current():
        return _STATE["active"]

    def start(self):
        _install()
        if _STATE["active"] is not None and _STATE["active"] is not self:
            raise EError("another OpenAudit is active")
        _STATE["active"] = self
        return self

    def stop(self):
        if _STATE["active"] is self:
            _STATE["active"] = None

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()
        return False

    def add_tmp(self, d):
        self.tmp.append(os.path.realpath(d))

    def set_block(self, n):
        self.block = n

    def open_hinge(self):
        """OpenAudit's hinge allowance (spec 14.1); one way."""
        self.hinge = True

    class _Via:
        def __init__(self, a, kind):
            self.a, self.kind = a, kind

        def __enter__(self):
            self.prev, self.a._via = self.a._via, self.kind

        def __exit__(self, *exc):
            self.a._via = self.prev
            return False

    def via(self, kind):
        return OpenAudit._Via(self, kind)

    def locate(self, rp):
        """('root' | 'private' | 'tmp', base, rel) of a realpath, or None; the longest base wins."""
        best = None
        for kind, base in self.roots + [("tmp", t) for t in self.tmp]:
            if _under(rp, base) and (best is None or len(base) > len(best[1])):
                best = (kind, base, os.path.relpath(rp, base).replace(os.sep, "/"))
        return best

    def refusal(self, rel, write=False, *, base="root"):
        """The reason an open of a root-relative path is refused, or None (pure; no file is touched)."""
        segs = rel.split("/")
        if write:
            return "write under a root"
        if rel.endswith(".inputs.json") or ".inputs." in segs[-1]:
            return "inputs file (S2B:545)"
        if any(C3_DIR_RE.fullmatch(s) for s in segs[:-1]) or segs[-1].lower() in C3_NAMES:
            return "c3 entry (S2B:569; RF-2)"
        if any(s.startswith(("step0_attempt1", "discarded")) for s in segs):
            return "step-0 attempt-1 or discarded output (spec 4.2)"
        if segs[0] not in CAMPAIGNS or len(segs) < 2:
            return None
        if (base == "root") != (segs[0] in PUBLIC_CAMPAIGNS):
            return "campaign under the wrong root (spec section 3)"
        name = segs[-1]
        if name.endswith(".validity_final.json") or (len(segs) == 2 and name in NEVER_FILES) or segs[1] == "logs":
            return "a file E never opens (spec 4.2)"
        if segs[0] == "c2":
            if segs[1] == "gates" and name in ("K2.json", "projection.json"):
                return "a C2 gate file E never opens (spec 4.2)"
            if segs[1] == "gates_applied" and re.match(r"gate_(K2|projection_after4)\.", name):
                return "a C2 gate file E never opens (spec 4.2)"
            if not self.hinge:
                if (segs[1] == "gates" and name == "step0.json") or \
                        (segs[1] == "gates_applied" and name.startswith("gate_step0_")):
                    return "C2 step-0 file outside hinge mode (spec 4.2)"
                if segs[1] == "raw" and name.split(".")[0] in HINGE and \
                        not (name == f"{name.split('.')[0]}.a2.json" and self._via == "a2_hinge_counts"):
                    return "hinge output outside hinge mode (S2B:610)"
        if segs[0] == "c1" and segs[1] == "raw" and len(segs) == 3:
            stem = name.split(".")[0]
            if stem in NEVER_SP:
                return "G1 or spin output (OP-2)"
            if stem in PB136_SP and not (self.hinge and self.block == 5):
                return "Pb136 C1 output outside block 5 (S2B:561-562; amendment item 1)"
        return None

    def _on_open(self, rp, mode, write):
        loc = self.locate(rp)
        if loc is None:
            return
        kind, base, rel = loc
        if kind == "tmp":
            if not write:
                self._log(rp, rel, kind)
            return
        why = self.refusal(rel, write, base=kind)
        if why:
            self.refused.append((rel, why))
            raise Blinded(f"OpenAudit refused {rel}: {why}")
        self._log(rp, rel, kind)

    def _log(self, rp, rel, kind):
        e = self.log.get(rp)
        if e is None:
            if os.path.isdir(rp):
                return
            self.log[rp] = {"rel": rel, "base": kind, "sha256": _sha256_file(rp), "block": self.block,
                            "hinge": self.hinge, "n": 1, "via": self._via}
        else:
            e["n"] += 1

    def log_member(self, tar_rp, name):
        """Record (and refuse, outside hinge mode, a hinge member of c2/structures.tar.gz) a tar member read."""
        loc = self.locate(os.path.realpath(tar_rp))
        rel = loc[2] if loc else os.path.realpath(tar_rp)
        if rel == "c2/structures.tar.gz" and not self.hinge and \
                any(name.startswith(f"a2/{lab}/") for lab in HINGE):
            self.refused.append((f"{rel}:{name}", "hinge member outside hinge mode"))
            raise Blinded(f"OpenAudit refused {rel}:{name}: hinge member outside hinge mode (S2B:610)")
        self.members.append((rel, name, self.block, self.hinge))

    def stable(self):
        """INT-SHA-STABLE: the rel of every logged file whose bytes changed since first open (re-read unhooked)."""
        bad = []
        for rp, e in self.log.items():
            try:
                now = _sha256_file(rp)
            except OSError:
                now = None
            if now != e["sha256"]:
                bad.append(e["rel"])
        return bad

    def sha256_of(self, path):
        e = self.log.get(os.path.realpath(path))
        return None if e is None else e["sha256"]

    def hinge_closed(self):
        """INT-HINGE-CLOSED: (rel, why) of every logged hinge output or member opened outside hinge mode."""
        bad = []
        for e in self.log.values():
            segs = e["rel"].split("/")
            if e["base"] == "root" and segs[:2] == ["c2", "raw"] and len(segs) == 3 and not e["hinge"]:
                stem, name = segs[2].split(".")[0], segs[2]
                if stem in HINGE and not (name == f"{stem}.a2.json" and e["via"] == "a2_hinge_counts"):
                    bad.append((e["rel"], "hinge output"))
        for rel, name, blk, hg in self.members:
            if rel == "c2/structures.tar.gz" and not hg and any(name.startswith(f"a2/{lab}/") for lab in HINGE):
                bad.append((f"{rel}:{name}", "hinge member"))
        return bad

    def classify(self):
        """RF-11: (class, key) per logged file: ('archive', c) for c1/c2/fr files, ('manifest', c) for c3b/c4b,
        ('8bff03e', rel) for the extraction, ('exempt', rel) for E's own outputs, ('head', rel) for any other file under
        the root (a tracked note or verify record: the caller checks it against HEAD). None: no class (INT-SHA)."""
        out = {}
        for rp, e in self.log.items():
            rel, base = e["rel"], e["base"]
            segs = rel.split("/")
            if base == "tmp":
                cl = ("8bff03e", rel)
            elif base == "private":
                cl = ("manifest", segs[0]) if segs[0] in PRIVATE_CAMPAIGNS else None
            elif segs[0] in PUBLIC_CAMPAIGNS and len(segs) > 1:
                cl = ("archive", segs[0])
            elif E_OUTPUT_RE.fullmatch(rel):
                cl = ("exempt", rel)
            else:
                cl = ("head", rel)
            out[rp] = cl
        return out

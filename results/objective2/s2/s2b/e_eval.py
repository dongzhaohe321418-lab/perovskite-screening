#!/usr/bin/env python
"""E, the one evaluation of S2b (results/objective2/s2/S2B_PLAN.md section 7, with amendment 2026-11-12a; the
analyst's decisions E_DECISIONS_R1; E_IMPLEMENTATION_SPEC sections 1, 6-12 and 14-16).

  --run        one evaluation attempt, in three phases.
               Phase 0a, admissibility, refuses (exit 2, nothing written): a dirty tree; an existing output; a root
               holding a c3 entry (RF-2); a route that 'When E may run' (S2B:515-518) does not allow (the fr status
               and outcome, the stop note, block 4 past FR); an archive without its verify record; a commits
               mismatch without a dated amendment, or E's files missing at an S2b campaign commit (RF-3, never
               waivable); an attempt the rerun rules do not allow (RF-6, OP-21, RF-15), the rerun cause included
               (both of its subprocess runs). Every failure of phase 0a is a refusal.
               Phase 0b, only then, runs the integrity checks of phase 0 (the imports, INT-GUARD, INT-ROUTE,
               INT-FR-*, RF-12, INT-COMMITS); a failure there writes the failure report (exit 3).
               Phase 1 computes, in memory, blocks 1-3 and 5 (block 4 through e_block4.py, a stub until C3b), every
               integrity check (any failure ends phase 1: the failure report, exit 3) and every cross-check (a
               failure is printed with 'cross-check failed', exit 1).
               Phase 2 writes the figure source data (temporary file + os.link) and then the attempt file with
               O_EXCL (RF-8); the last line of the file is 'E exit code: <n>'.
  --hinge      the deferred hinge run (S2B:714-719; amendment item 9; RF-1): blocks 1-3 recomputed in memory for
               the header, the Pb76 value and the C1 table, and block 5 printed in hinge mode.
  --self-test  every case of e_selftest.py (groups A-D and T), each with its deliberately broken variants.

Blinding. Every C2, fr, c3b and c4b A2 record, gate file, campaign.json and state_end.json is read through
e_guard.EGuarded by listed leaf (a closed list per mode); C1 MACE records and single points only through
e_guard.C1Access; every open under a root is logged and refused by e_guard.OpenAudit (writes, inputs files, c3
entries, the hinge outputs outside hinge mode, the Pb136 C1 outputs outside block 5 of a hinge read, every G1 and spin
output). Outside hinge mode no output of relaxations 1-4 and no Pb136 C1 output is opened, and the K3 value_meV is
only tested with 'is None'. An integrity failure prints check ids, file names and key paths only; an exception prints
its stage and type only (S2B:603-604). Notes, amendments and verify records are read as git blobs of HEAD. No
calculator is loaded. No entry point of scripts/48 is run and no scripts/49 gate is evaluated.

    python -B -I results/objective2/s2/s2b/e_eval.py --self-test
    python -B -I results/objective2/s2/s2b/e_eval.py --run [--root S2] [--private-root DIR] [--stop-note NOTE]
                 [--rerun-cause CASE --amendment NOTE] [--item7-amendment NOTE]
    python -B -I results/objective2/s2/s2b/e_eval.py --hinge --hinge-cause {prereg,backstop}
                 [--prereg NOTE --prereg-eval REC] [--stop-note NOTE] [--rerun-cause CASE --amendment NOTE]

  --stop-note with --hinge (fix round 1): on the FR-STOP route the hinge run re-validates the stop note at HEAD and
  requires the one the standing output names (S2B:153, 714-719; the spec's --hinge CLI omits it: an amendment line
  is needed).

Fix round 2 (review round 2): the hinge run prints every failed cross-check of blocks 1-3 in full (S2B:739-740);
the RF-1 backstop scan sees a renamed pre-registration (--no-renames) and the NOTE's commit date is taken in UTC; on
FR-STOP a standing output without its stop-note route line refuses the hinge run; a final STOP before the fr campaign
commit is refused with its own reason (open for the analyst); the R-1 set-aside is shown by the @4 attempt-1 marker's
name under fr/step0_attempt1/ (listed, never opened), recorded by STEP0_FIX or not; the STOP header names the first
FR cell not complete; a complete FA188 quartet after a final STOP before gate FR carries L_FRNOTEVAL; recorded gate
and WP2c energies are printed at 0.01 meV; a failed write of the attempt file removes its partial file and the CSVs
(RF-8); er.remove_tree pauses the open hook (rmtree's dir_fd opens).

Integration round (E_DECISIONS_R2 ER2-1 to ER2-3; INTEGRATION_DECISIONS IX-2): the item-4 label also on the C1 gate
statistics of A1 E_b in block 3; a row carrying L_FAR does not also carry L_FRVALID, and XC-DSUM-FAR carries L_FAR;
the item-7 fallback adds L_FAR and L_FR2 after L_FALLBACK; fr/STEP0_NO_ERROR as W's scripts/50 applies it (the gate
files keep attempt 1's fail_pending_fix, fr/state_end.json reads fail_final with no_error_found) is accepted on the
step-0-final route and printed as B2.step0.no_error.

Integration review 1 (INTEGRATION_DECISIONS IX-4, IX-6, IX-7; amendment 2026-11-12a items 12 and 13): the stop note
is the one file STOP_NOTE (results/objective2/s2/FR_STOP_NOTE.md), refused at any other path before git is asked, and
every note E reads must be a blob of HEAD (git cat-file -t), so that a glob or a directory is never read as a note; a
--stop-note on a done fr is refused; on FR-STOP the FR outcome recorded before the STOP (gate FR's files; a fail_final
step-0 decision; after fr/STEP0_NO_ERROR, the fr_outcome W's scripts/50 records in fr/campaign.json at a STOP) is
named in the header ('<decision>; then a final STOP (<reason>)', a pass 'counted as FR fails (S2B §1)'), checked
against fr_outcome (INT-ROUTE), and FR is no valid far reference (0 of 2; item 4 is L_ITEM4, the fallback's too).

Integration review 2 (INTEGRATION_DECISIONS IX-12, IX-15): on 'pass at gate FR; then a final STOP' every FR-quartet
value without the item-4 label (E_b^A2(FA188), its XC-FR2 rows and the fallback's result.FR2.Eb_A2_meV) carries
L_FRSTOP; a stopped fr whose fr/gates/FR.json exists without its gates_applied copy (gate FR written but not applied:
the N-FR4 or N-FR8 'not applied' Stops of W 50 run_gate) is refused, by name only, before the stop note is read.
"""
import argparse, collections, csv, datetime, hashlib, importlib.util, io, json, math, os, re, shutil, subprocess
import sys, tarfile, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
S2 = os.path.normpath(os.path.join(HERE, ".."))
REPO = os.path.normpath(os.path.join(S2, "..", "..", ".."))
# fix round 1: no bytecode under a root is ever read. 'python -B' writes none, but it still reads an existing
# __pycache__/*.pyc, which OpenAudit would log with no HEAD blob (INT-SHA). With a prefix outside every root, every
# module loaded later (check5_diag, e_selftest) is compiled from its tracked source.
sys.pycache_prefix = os.path.join(tempfile.gettempdir(), "e_s2b_pycache")


def _sibling(name):
    """A helper of this directory under the key '_s2b_<name>', one object per process (RF-19; e_guard.sibling)."""
    key = f"_s2b_{name}"
    m = sys.modules.get(key)
    if m is None:
        s = importlib.util.spec_from_file_location(key, os.path.join(HERE, f"{name}.py"))
        m = importlib.util.module_from_spec(s)
        sys.modules[key] = m
        try:
            s.loader.exec_module(m)
        except BaseException:
            del sys.modules[key]
            raise
    return m


eg = _sibling("e_guard")
er = _sibling("e_read")
EError, EIntegrity, Blinded, ABSENT, FILE_ABSENT = eg.EError, eg.EIntegrity, eg.Blinded, eg.ABSENT, eg.FILE_ABSENT

# ---------------------------------------------------------------- constants (spec sections 1, 6, 7, 9, 10, 14)
S2_REL = "results/objective2/s2"
E_FILES = tuple(f"{S2_REL}/s2b/{n}" for n in ("e_eval.py", "e_guard.py", "e_read.py", "e_block4.py", "e_selftest.py")) \
    + (f"{S2_REL}/figures/fig_s2b_e_fk.py",)                                       # spec section 1; RF-3
TOOLS = E_FILES + (f"{S2_REL}/figures/fig_s2_c2_a2.py", f"{S2_REL}/c2_diagnostic/check5_diag.py")   # spec 6.2 item 3
SCRIPTS = tuple(f"scripts/{n}" for n in ("46_s2_cells.py", "47_s2_qe.py", "48_s2_analysis.py", "49_s2_gates.py",
                                         "50_s2_campaign.py"))
C2_COMMIT = "8bff03ede8b9d0f380b6ef373b239e7deb87817f"                            # spec section 7
ARCHIVE_COMMIT = {"c1": "b711f7e8673a75508cb1c6ac14f18d4f7dedfef8", "c2": "1d19eabfc386fb07e128c751318d9e794a4bd58b"}
VERIFY_RECORD = {"c2": f"{S2_REL}/c2_verify/verify_c2.txt", "fr": f"{S2_REL}/fr_verify/verify_fr.txt"}   # OP-18, A10
OUT_DIR, CSV_DIR = "s2b", "figures/source_data"                                  # under the root
EVAL_FILES = ("E_output.txt", "E_output_attempt2.txt", "E_output_attempt3.txt")   # S2B:523-524; OP-21
HINGE_FILES = ("E_hinge_output.txt", "E_hinge_output_attempt2.txt")              # S2B:715; OP-22
SUFFIX = {("evaluation", 1): "", ("evaluation", 2): "_attempt2", ("evaluation", 3): "_attempt3",
          ("hinge", 1): "_hinge", ("hinge", 2): "_hinge_attempt2"}
BACKSTOP = datetime.date(2027, 6, 30)                                            # S2B:719
TOL_MEV, STEP0_MEV, FR2_MAX_MEV = 1e-6, 0.5, 50.0                                # S2B:140-141, 291
NOT_OPENED = "BLOCK 5. Hinge block: not opened"                                  # RF-1
K3_CHECKS_FAILED = ["s2r_m30_VB76: final geometry fails check(s) [5]"]           # INT-K3-DEC; C2_RESULT.md
FAR, HINGE, FR_ORDER, FR_QUARTET = eg.FAR, eg.HINGE, eg.FR_ORDER, eg.FR_QUARTET
ROLES = ("host", "V", "D", "DV")
C2_RESULT = {"s2r_m30_VB136": (79, 78, 0, 1), "s2r_m30_hostB136": (83, 82, 0, 0),
             "s2r_m30_Sr136o0_novac": (81, 80, 0, 0), "s2r_m30_Sr136o0_vac": (75, 74, 0, 0),
             "s2r_m30_hostB76": (165, 164, 0, 0), "s2r_m30_VB76": (193, 192, 0, 0),
             "s2r_m30_Sr76o0_novac": (142, 141, 2, 0),
             "s2r_m30_Sr76o0_vac": (136, 135, 0, 0)}  # C2_RESULT.md §2: n_config, converged_at_k, restarts, reruns
C2_KEYS = ("n_config", "converged_at_k", "restarts", "reruns_from_zero")
TAIL_K = {"s2r_m30_hostB76": 128, "s2r_m30_VB76": 156, "s2r_m30_Sr76o0_novac": 105, "s2r_m30_Sr76o0_vac": 99,
          "s2r_m30_VB136": 42, "s2r_m30_hostB136": 46, "s2r_m30_Sr136o0_novac": 44,
          "s2r_m30_Sr136o0_vac": 38}                                     # S2B:643, 698
VB76_EXTRA_K = (158, 172)                                                        # S2B:644
FR_REASON = {"end_rule": None, "missing": "missing", "not_started_cap": "hard-cap refusal",
             "killed_by_gate": "killed by a gate", "not_run_gate": "not run (gate)",
             "check_not_evaluated": "no final-geometry check"}                   # spec section 9
NOTE_DENY = re.compile(rf"{S2_REL}/(S2B_PLAN\.md|S2_PLAN\.md|[^/]*_OPERATIONS\.md|[^/]*_RESULT\.md|"
                       rf"[^/]*_DIAGNOSTIC\.md|s2b/.*)")                         # RF-1 deny-list
STOP_PHRASE = re.compile(r"the fr STOP is final", re.I)                         # OP-19: what the note must state
STOP_NOTE = f"{S2_REL}/FR_STOP_NOTE.md"            # IX-6 (amendment item 12): the one stop note any reader accepts
ISO_DATE = re.compile(r"\b(20\d\d)-(\d\d)-(\d\d)\b")
STATUS_PLAN = re.compile(r"\bStatus: PLAN\b")                                    # RF-1 ('PLANNED' does not match)
RERUN_FAILS = ("AssertionError", "EIntegrity")    # spec 16: the case itself fails on the earlier code (fix round 1)
ROUTE_STOP_NOTE = re.compile(r"route: FR-STOP \(.*; stop note (.+) sha256 ([0-9a-f]{64})\)")   # M3; round 2: spaces

L = {
    "L_ITEM4": "S2 K3 failed (far quartet invalid); A1 not validated against A2 at the far site",
    "L_FRVALID": "far-site reference: FR, m30 FA188, valid",
    "L_MACE": "zero-shot MACE, not re-admitted",
    "L_FAR": "far quartet invalid (check 5, VB76); reported only; not valid",
    "L_TAIL": "path energy of the whole region over the window; not attributable to the failing objects; bounds no "
              "E_b error; reported only",
    "L_FR2": "FR-2 failed (|δ_far(FA188)| > 50 meV in one quartet; bias and site scatter not separable); "
             "reported only",
    # fix round 2 (needs an amendment line, as OP-29): a complete FA188 quartet after a final STOP before gate FR
    "L_FRNOTEVAL": "gate FR not evaluated (final STOP in fr); reported only; not valid",
    # integration review 2 (IX-12; amendment item 13): an FR-quartet value without the item-4 label after a gate FR
    # pass that a final STOP turned into 'FR fails' (S2B §1)
    "L_FRSTOP": "gate FR passed, then a final STOP in fr (S2B section 1); reported only; not valid",
    "L_NOFORM_C1": "not formable from C1 single points (no A2 cell)",
    "L_NOA1": "no A1 DFT value",
    "L_NOA2": "no S2 A2 cell",
    "L_C4BNOTRUN": "C4b not run",
    "L_HINGE_DIFF": "not a K3 decision; K3 failed on validity",
    "L_CA_Q0": "not formable: no F of Ca D(136)",
    "L_CA_MACE": "no DFT A1 E_b (Ca failed G1)",
    "L_FALLBACK": "recorded by gate code; not cross-checked (E failed twice)",
    "L_NOTREAD": "not read: E failed",
    "L_XFAIL": "cross-check failed",
    "L_Q0": "q = 0 link row (§10), reported only",
    "L_WP2C": "WP2c: whole-cell WP1 MACE geometry, q = 0, one far site (different protocol)",
    "L_A1TIER": "fixed-geometry DFT; relaxation bias not bounded. Far-site A2 reference valid at pilot host m30, FA188 "
                "only (Cs, A f₁, 11.25 Å; S2b FR){clause}. Invalid at m30 Pb76 (Sr, B f₁, 11.81 Å; C2, check 5). "
                "Valid far references: 1 of 2. No production-host far site is tested at A2. S2 K3: fail_replan; its "
                "value test (P:644-646) was not reached, and no A2 test of the first shell gates this tier.",
}
L_A1TIER_CLAUSE = "; check 5 passed only under the identical-atom reading"     # S2B:160, 163
STEP0_GATE = "recorded by gate code"                                            # amendment item 3


def L_FR1(kind, cell, detail):
    """OP-29: the check and end-rule variants, and the not-run variant. Fix round 1: a complete quartet whose FR-1
    failure is check_not_evaluated (RF-4) takes the check variant's form with the header's reason, not the not-run
    variant (the wording needs an amendment line: OP-29 fixes the strings)."""
    if kind == "check":
        return f"FR quartet invalid (check {detail}, {cell}); reported only; not valid"
    if kind == "end_rule":
        return f"FR quartet invalid (end rule {detail}, {cell}); reported only; not valid"
    if kind == "check_not_evaluated":
        return f"FR quartet invalid (no final-geometry check, {cell}); reported only; not valid"
    return f"FR quartet incomplete ({cell} {kind}); reported only; not valid"


def L_NOTFORMED(reason):
    return f"not formed ({reason})"


# ---------------------------------------------------------------- formatting (spec section 9, Precision)
def fe(x):
    return "%.6f" % x                                     # eV


def fm(x):
    return "%.2f" % x                                     # meV


def fmr(x):
    """A recorded energy-type value (gate leaves, WP2c E_b): '%.2f meV' (S2B:633), 'none' for None, else its text
    (fix round 2: no raw repr)."""
    if isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x):
        return f"{fm(x)} meV"
    return "none" if x is None else str(x)


def fa(x):
    return "%.4f" % x                                     # A


def fa2(x):
    return "%.6f" % x                                     # A^2


def ff(x):
    return "%.6f" % x                                     # eV/A


def fr3(x):
    return "%.3e" % x                                     # residuals


def full(x):
    return repr(float(x))                                 # "full precision" (S2B:647)


def S(x):
    """A listed leaf, printable (ABSENT and FILE_ABSENT by name; they refuse every other use)."""
    if x is ABSENT:
        return "absent"
    if x is FILE_ABSENT:
        return "absent (no file)"
    if isinstance(x, list):
        return "[" + ", ".join(str(v) for v in x) + "]"
    return str(x)


def close(a, b, tol=None):
    tol = TOL_MEV if tol is None else tol                # looked up at call time
    return isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and \
        not isinstance(b, bool) and math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tol


def eb(F):
    """E_b in meV from {role: F (eV)}: ((F_DV - F_D) - (F_V - F_h)) x 1000, the differences first [49:272-277]."""
    if any(F.get(r) is None for r in ROLES):
        return None
    return ((F["DV"] - F["D"]) - (F["V"] - F["host"])) * 1000.0


def role_of(lab):
    return {"host": "host", "V": "V", "D": "D", "DV": "DV"}[er.a2_cell(lab)["kind"]]


def checks_str(failed):
    return ", ".join(str(x) for x in failed) if isinstance(failed, list) else S(failed)


# ---------------------------------------------------------------- rows and the text (spec section 9, Rows)
class Row:
    """One printed item: block, id, kind, values, label ids, text (S2B section 7, 'Blocks'); no class field."""
    __slots__ = ("block", "id", "kind", "values", "labels", "text", "has_a1", "line")

    def __init__(self, block, rid, kind, text, values, labels, has_a1):
        self.block, self.id, self.kind, self.text = block, rid, kind, text
        self.values, self.labels, self.has_a1 = dict(values or {}), tuple(labels), bool(has_a1)
        self.line = None                                  # the printed line, labels included (set by Out.row)


KINDS = ("F", "relax_energy", "Eb_A1", "Eb_A2", "delta", "dF_tail", "path_work", "curve", "Eb_mace", "E_mace", "Eb_q0",
         "Eb_q1", "forces", "determinism", "invalid", "status", "xcheck", "note")


class Out:
    """The lines and rows of one block; labels are added by kind (spec section 9) and by RF-25 (has_a1)."""

    def __init__(self, item4, xcs):
        self.item4, self.xcs = item4, xcs                # item4: 'L_ITEM4' or 'L_FRVALID'; xcs: shared (id, ok)
        self.lines, self.rows = [], []

    def line(self, s=""):
        self.lines.append(s)

    def row(self, block, rid, kind, text, *, values=None, labels=(), has_a1=False, indent="  "):
        if kind not in KINDS:
            raise EError(f"row kind {kind!r}")
        labs = []
        far = any((lab if isinstance(lab, str) else lab[0]) == "L_FAR" for lab in labels)
        if (kind in ("Eb_A1", "Eb_q0", "Eb_q1") or has_a1) and not (far and self.item4 == "L_FRVALID"):
            labs.append((self.item4, L[self.item4]))     # S2B:623-631; RF-25. ER2-2: on an FR-pass route a row
            #                                              carrying L_FAR does not also carry L_FRVALID (S2B:623-631
            #                                              lists only A1 E_b); on FR-fail routes L_ITEM4 stays beside it
        if kind in ("E_mace", "Eb_mace", "determinism"):
            labs.append(("L_MACE", L["L_MACE"]))
        if kind == "dF_tail":
            labs.append(("L_TAIL", L["L_TAIL"]))
        for lab in labels:
            labs.append(lab if isinstance(lab, tuple) else (lab, L[lab]))
        seen, uniq = set(), []
        for i, t in labs:
            if (i, t) not in seen:
                seen.add((i, t)); uniq.append((i, t))
        uniq.sort(key=lambda x: x[0] != "L_XFAIL")      # 'cross-check failed' first, then the item-4 label (RF-25)
        r = Row(block, rid, kind, text, values, [i for i, _ in uniq], has_a1 or kind in ("Eb_A1", "Eb_q0", "Eb_q1"))
        self.rows.append(r)
        r.line = indent + text + ("  -- " + "; ".join(t for _, t in uniq) if uniq else "")
        self.lines.append(r.line)
        return r

    def xc(self, block, xid, ok, text, *, values=None, indent="  ", has_a1=False, labels=()):
        """A cross-check (spec section 15): its values and residual; a failure adds L_XFAIL, suppresses nothing.
        has_a1: the row prints an A1 E_b or a difference that contains one (RF-25; S2B:623-629): the item-4 label.
        labels: the labels of the value it checks (ER2-2: XC-DSUM-FAR carries L_FAR as B1.delta does)."""
        self.xcs.append((xid, ok))
        if ok is True:
            return self.row(block, xid, "xcheck", f"{xid}: {text}: ok", values=values, labels=labels, indent=indent,
                            has_a1=has_a1)
        if ok is False:
            return self.row(block, xid, "xcheck", f"{xid}: {text}", values=values, labels=("L_XFAIL",) + tuple(labels),
                            indent=indent, has_a1=has_a1)
        return self.row(block, xid, "xcheck", f"{xid}: {text}", values=values, labels=labels, indent=indent,
                        has_a1=has_a1)


def resid(a, b):
    if not close(a, b, float("inf")):
        return "|Δ| not formed"
    return f"|Δ| = {fr3(abs(a - b))} meV (tolerance {TOL_MEV:g} meV)"


# ---------------------------------------------------------------- git and the environment
class Git:
    """git -C <repo> <args> -> (rc, stdout bytes); rc outside ok raises EError (injectable by the self-test)."""

    def __init__(self, repo):
        self.repo = repo

    def __call__(self, *args, ok=(0,), stdin=None):
        r = subprocess.run(["git", "-C", self.repo, *args], input=stdin, capture_output=True)
        if r.returncode not in ok:
            raise EError(f"git {' '.join(a for a in args[:2] if not a.startswith('-'))} failed (exit {r.returncode})")
        return r.returncode, r.stdout

    def out(self, *args):
        return self(*args)[1].decode()

    def head(self):
        return self.out("rev-parse", "HEAD").strip()

    def porcelain(self, *paths):
        return self.out("status", "--porcelain", "--untracked-files=all", *(("--",) + paths if paths else ()))

    def exists(self, c, path):
        return self("cat-file", "-e", f"{c}:{path}", ok=(0, 1, 128))[0] == 0

    def kind(self, c, path):
        """The object type of c:path ('blob', 'tree', ...), or None if there is none (IX-6: a pathspec such as a glob
        names no object, so that git show cannot print a commit in its place)."""
        rc, b = self("cat-file", "-t", f"{c}:{path}", ok=(0, 128))
        return b.decode().strip() if rc == 0 else None

    def show(self, c, path):
        rc, b = self("show", f"{c}:{path}", ok=(0, 128))
        return b if rc == 0 else None

    def tracked(self, path):
        return self("ls-files", "--error-unmatch", "--", path, ok=(0, 1))[0] == 0

    def added(self, path):
        """[(commit, committer date)] of the commits that added path, newest first (no rename detection: a renamed
        file is added by its rename commit; fix round 2)."""
        return [tuple(x.split(" ", 1)) for x in self.out("log", "--no-renames", "--diff-filter=A", "--format=%H %cI",
                                                         "--", path).splitlines() if x.strip()]

    def added_since(self, c):
        """Every path added in a commit of c..HEAD, the new name of a renamed file included (--no-renames; RF-1
        backstop scan, fix round 2); NUL-separated, so that a name with a space stays whole."""
        b = self("log", "--no-renames", "--diff-filter=A", "--name-only", "-z", "--format=", f"{c}..HEAD")[1]
        return sorted({x.strip("\n") for x in b.decode().split("\0") if x.strip("\n")})

    def cdate(self, c):
        return datetime.datetime.fromisoformat(self.out("show", "-s", "--format=%cI", c).strip())

    def is_ancestor(self, a, b):
        return self("merge-base", "--is-ancestor", a, b, ok=(0, 1))[0] == 0

    def strictly_after(self, a, b):
        """Commit a is strictly after commit b (b an ancestor of a, a != b)."""
        return a != b and self.is_ancestor(b, a)

    def diff_quiet(self, a, b, paths):
        return self("diff", "--quiet", a, b, "--", *paths, ok=(0, 1))[0] == 0

    def ls_tree(self, c, prefix):
        out = {}
        for line in self.out("ls-tree", "-r", c, "--", prefix).splitlines():
            meta, path = line.split("\t", 1)
            out[path] = meta.split()[2]
        return out


class Env:
    """Where E runs. Run mode: this checkout, its git, the real UTC clock. The self-test injects a throwaway git
    repository, the synthetic roots, the shared 8bff03e extraction, a clock, the WP1 directory and block 4."""

    def __init__(self, *, repo, root, private_root=None, git=None, objects_repo=None, ex=None, wp1_dir=None,
                 clock=None, selftest=False, c2_commit=C2_COMMIT, archive_commit=None, block4=None, python=None,
                 hooks=None, echo=True, code_dir=HERE):
        self.repo, self.root, self.private_root = os.path.abspath(repo), os.path.abspath(root), private_root
        self.git = git or Git(self.repo)
        self.objects_repo = objects_repo or self.repo
        self.ex, self.wp1_dir, self.clock, self.selftest = ex, wp1_dir, clock, bool(selftest)
        self.c2_commit, self.archive_commit = c2_commit, dict(archive_commit or ARCHIVE_COMMIT)
        self.block4, self.python = block4, python or sys.executable
        self.hooks, self.echo, self.code_dir = dict(hooks or {}), echo, code_dir

    def now(self):
        """The UTC time; an injected clock only under --self-test (RF-1)."""
        if self.clock is not None:
            if not self.selftest:
                raise EError("an injected clock outside --self-test (RF-1)")
            return self.clock()
        return datetime.datetime.now(datetime.timezone.utc)

    def rel(self, path):
        """The repository-relative path of an absolute path (refused outside the repository)."""
        r = os.path.relpath(os.path.abspath(path), self.repo).replace(os.sep, "/")
        if r.startswith("../") or r == "..":
            raise EError(f"{path} is outside the repository")
        return r


def git_blob_of_file(path):
    """git blob id and sha256 of a file, read once in chunks (INT-SHA)."""
    h, s = hashlib.sha1(), hashlib.sha256()
    h.update(b"blob %d\0" % os.path.getsize(path))
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b); s.update(b)
    return h.hexdigest(), s.hexdigest()


def exit_code_of(text):
    lines = [x for x in text.rstrip("\n").split("\n")]
    m = re.fullmatch(r"E exit code: (\d)", lines[-1]) if lines else None
    return int(m.group(1)) if m else None


def head_of(text):
    m = re.search(r"\bHEAD ([0-9a-f]{40})\b", text.split("\n", 1)[0])
    return m.group(1) if m else None


def hinge_trigger(route_id, b4=None, ctx=None):
    """Spec 14.1: block 5 opens iff C4b ended with df_delta >= 3 (counted by block 4's committed function)."""
    if route_id != "C4B-ENDED":
        reason = {"FR-FAIL": "C4b not run", "FR-STOP": "C4b not run", "C3B-STOP": "C4b not run",
                  "C3B-NOTIER": "C4b not run", "C4B-NOTRUN": "C4b not run", "C4B-STOP": "C4b final STOP"}
        return {"held": False, "df_delta": None, "reason": reason.get(route_id, "C4b not run")}
    n = b4.c4b_df_delta_validity(ctx)["df_delta"]
    if isinstance(n, bool) or not isinstance(n, int):
        raise EIntegrity("INT-STRUCT", "e_block4.c4b_df_delta_validity", "df_delta")
    return {"held": n >= 3, "df_delta": n, "reason": None}


def fr2_pass(delta_meV):
    """FR-2 (S2B:291): |delta_far(FA188)| <= 50 meV; a missing value fails."""
    return delta_meV is not None and abs(delta_meV) <= FR2_MAX_MEV


def valid_far_refs(dec):
    """'Valid far references: k of 2': k counts the valid far quartets, FR-1 for FA188 (OP-11, amendment item 4)."""
    return 1 if (dec or {}).get("FR1") is True else 0


def fr_reason(kind, failed=ABSENT, outcome=ABSENT):
    """The <reason> of 'fail (FR-1, <cell>, <reason>)' by decision.FR.kind (spec section 9)."""
    if kind == "check":
        return f"check {checks_str(failed)}"
    if kind == "end_rule":
        return f"end rule {S(outcome)}"
    return FR_REASON.get(kind) or S(kind)


def gate_fr_unapplied(fr_dir):
    """IX-15: gate FR written but not applied. W 50 run_gate writes fr/gates/FR.json (the scripts/49 CLI) before its
    gates_applied copy, and an N-FR4 or N-FR8 'not applied' Stop comes between the two. By name only (os.path.exists):
    no gate file is opened."""
    return os.path.exists(os.path.join(fr_dir, "gates", "FR.json")) and \
        not os.path.exists(os.path.join(fr_dir, "gates_applied", "gate_FR.gate.json"))


def stop_note_ok(path, text):
    """OP-19: a dated note that states the fr STOP is final; IX-6 (amendment item 12): the one file STOP_NOTE (which
    lies under S2/, not under s2b/)."""
    return path == STOP_NOTE and path.startswith(S2_REL + "/") and not path.startswith(f"{S2_REL}/s2b/") and \
        bool(STOP_PHRASE.search(text)) and bool(ISO_DATE.search(text))


def exc_line(stage, e):
    """S2B:603-604, [g2:375-378]: an exception is reported by stage and type, never by its message."""
    return f"FAILED: stage {stage}: {type(e).__name__}"


def calc_check(cd, check):
    """INT-CALC-LOAD / INT-CALC-EXIT: no module of check5_diag.CALC_ENGINES is loaded."""
    try:
        cd.assert_no_calculator()
    except AssertionError:
        raise EIntegrity(check, "sys.modules", "CALC_ENGINES") from None


def hinge_delta(v):
    """delta_Sr,m30 for block 4's calibrated tier: block 5's hinge quartet only, never Pb76 (spec section 13)."""
    return v["Pb136"]["delta"]


def fr1_recompute(cells):
    """S2B section 2 order over FR_ORDER (XC-FR1-DEC): status, end rule in END_ACCEPTED, validity_final.valid."""
    for lab in FR_ORDER:
        c = cells[lab]
        st = c["status"]
        if st is FILE_ABSENT or st == "pending":
            return None, lab, "pending"
        if st != "complete":
            return False, lab, st
        if c.get("end_rule.outcome") not in eg.END_ACCEPTED:
            return False, lab, "end_rule"
        v = c.get("validity_final.valid", ABSENT)
        if v is ABSENT:                                  # no validity_final (RF-4), as fr_eval [W 49:731-733]
            return False, lab, "check_not_evaluated"
        if v is not True:                                # a present validity_final whose valid is not True
            return False, lab, "check"
    return True, None, None


def reached_k0(c):
    """RF-4, RF-12 (fix round 1): True for an FR cell whose step-0 evaluation must exist (it reached k = 0): killed by
    the step-0 gate, or complete with n_config >= 1. False where it cannot exist: no record, not_run_gate,
    not_started_cap, or complete with n_config 0 (the SCF failed at k = 0, so its step-0 gate never ran; W
    50:4107-4111, 2945-2951). None: either (pending, missing)."""
    st, n = c.get("status"), c.get("n_config", ABSENT)
    if st == "killed_by_gate" or (st == "complete" and isinstance(n, int) and not isinstance(n, bool) and n >= 1):
        return True
    if st is FILE_ABSENT or st in ("not_run_gate", "not_started_cap") or (st == "complete" and n == 0):
        return False
    return None


def within_30_days(d_attempt2, d_note):
    """OP-21 (S2B:735): the item-7 amendment is committed within 30 days after the attempt-2 commit."""
    return datetime.timedelta(0) <= d_note - d_attempt2 <= datetime.timedelta(30)


def boltzmann_gap_meV(F_eV):
    """E's own per-leg aggregate (S2B section 2 of P section 9): F_min - k_BT ln sum exp(-(F_i - F_min)/k_BT), in meV
    relative to F_min (k_BT = 25.7 meV)."""
    x = [(v - min(F_eV)) * 1000.0 for v in F_eV]
    return -25.7 * math.log(math.fsum(math.exp(-v / 25.7) for v in x))


# ---------------------------------------------------------------- one run of E
class Refused(Exception):
    """Phase 0 refusal: exit 2, nothing written."""


class Run:
    def __init__(self, args, env):
        self.a, self.env, self.git = args, env, env.git
        self.mode = "hinge" if args.hinge else "evaluation"
        self.root = env.root
        self.L = er.ELayout(env.root, env.private_root)
        self.chk = eg.Checks()
        self.xcs, self.rows = [], []
        self.outs = collections.OrderedDict()
        self.stage, self.au, self.ex, self.own_ex = "phase 0", None, None, False
        self.attempt, self.attempt1_exit, self.attempt_path, self.csv_paths = None, None, None, ()
        self.route, self.fr, self.b4 = None, {}, env.block4 or _sibling("e_block4")
        self.item4, self.header, self.hinge_open, self.trigger = "L_ITEM4", None, False, None
        self.v, self.csv_rows, self.reads_summary, self.appendix = {}, [], [], []
        self.written, self.archive_fr, self.stop_note_sha, self.amend = [], None, None, None
        # the lines before the header, in the output order of spec section 9 (filled by phases 0a and 0b)
        self.pre_head, self.pre_env, self.pre_route, self.pre_commits = [], [], [], []

    @property
    def pre(self):
        return self.pre_head + self.pre_env + self.pre_route + self.pre_commits

    # ------------------------------------------------------------ entry
    def main(self):
        rc = None
        try:
            try:                                         # phase 0a: admissibility; every failure is a refusal
                self.phase0_start()                      # (S2B:515-518; spec 6.1, 6.2; fix round 1)
                self.phase0_admit()
            except (EError, Refused, EIntegrity) as e:
                return self.refuse(e)
            except Exception as e:                       # S2B:603-604: stage and type only
                return self.refuse(EError(exc_line(self.stage, e)))
            try:                                         # phase 0b: the integrity checks that may write
                self.phase0_integrity()
            except (EError, Refused) as e:
                return self.refuse(e)
            except EIntegrity as e:
                return self.fail(e.line())
            except Exception as e:                       # S2B:603-604: stage and type only
                return self.fail(exc_line(self.stage, e))
            try:
                rc = self.phase1()
            except EIntegrity as e:
                return self.fail(e.line())
            except Exception as e:
                return self.fail(exc_line(self.stage, e))
            return self.phase2(rc)
        finally:
            if self.au is not None:
                self.au.stop()
            if self.own_ex and self.ex is not None:
                m = self.ex.cleanup()                    # RF-21: reported, the exit code unchanged
                if m and self.env.echo:
                    print(f"cleanup: {m}", file=sys.stderr)

    def refuse(self, e):
        msg = f"E refused (exit 2; nothing written): {e}"
        if self.env.echo:
            print(msg, file=sys.stderr)
        self.result_text, self.rc = msg, 2
        return 2

    # ------------------------------------------------------------ phase 0 (spec 6.2)
    def phase0_start(self):
        a, env, g = self.a, self.env, self.git
        if sys.version_info < (3, 12) or not hasattr(tarfile, "data_filter"):
            raise EError("E needs Python >= 3.12 with tarfile.data_filter (spec section 1)")
        if a.rerun_cause is not None and a.amendment is None:
            raise EError("--rerun-cause needs --amendment (spec section 16)")
        if g.porcelain():                                                     # 1
            raise EError("the working tree is not clean (git status --porcelain --untracked-files=all)")
        self.head = g.head()                                                  # 2
        if not os.path.isdir(self.root):
            raise EError(f"root {self.root} is not a directory")
        self.root_rel = env.rel(self.root)
        self.au = eg.OpenAudit(self.root, private_root=env.private_root,
                               tmp=([env.ex.tmp] if env.ex is not None else [])).start()
        self.time = env.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.choose_attempt()                                                 # 5 (before the imports: a failure
        er.assert_no_c3(self.L, at="start")                                   # 6   report needs the attempt file)
        if env.private_root is not None and eg._under(os.path.realpath(env.private_root), os.path.realpath(self.root)):
            raise EError("the private root lies under the public root (spec section 3)")

    def tools(self):
        """Spec 6.2 item 3: the sha256 of E's tools (opened under OpenAudit: INT-SHA against HEAD)."""
        out = []
        for p in TOOLS:
            fp = os.path.join(self.env.repo, p)
            if not os.path.isfile(fp):
                raise EError(f"tool {p} is missing (spec section 1)")
            with open(fp, "rb") as fh:
                out.append((p, hashlib.sha256(fh.read()).hexdigest()))
        return out

    def phase0_admit(self):
        """Phase 0a (fix round 1): every condition under which E may not run at all, before any check that writes:
        the route (fr status and outcome, the stop note, block 4 past FR), the verify records, the hinge
        preconditions, the commits (RF-3, the amendment) and the rerun cause with both of its subprocess runs. Every
        failure here is a refusal (exit 2, nothing written; S2B:515-518, spec 6.1, 6.2). The leaves read are the
        status, outcome and commit leaves of fr/campaign.json only."""
        self.stage = "phase 0"
        title = (f"attempt {self.attempt} of the one evaluation" if self.mode == "evaluation" else
                 "hinge run" + (f", attempt {self.attempt}" if self.attempt > 1 else ""))
        self.pre_head.append(f"S2b E, {title} (S2B_PLAN.md §7); run at {self.time}; HEAD {self.head}; mode "
                             f"{self.mode}")
        self.pre_head.append("tools:")
        self.pre_head += [f"  {p} {h}" for p, h in self.tools()]
        self.route_admit()                                                    # 7 (spec 6.1)
        self.verify_records()                                                 # S2B:522; OP-18
        if self.mode == "hinge":
            self.hinge_preconditions()                                        # spec 14.3; RF-1
        self.commits_admit()                                                  # 8 (spec 7; RF-3)
        self.rerun_checks()                                                   # spec 16; RF-6, RF-9

    def phase0_integrity(self):
        """Phase 0b: the imports at 8bff03e (spec 2), INT-IMPORT and INT-GUARD, the route's integrity (RF-12,
        INT-ROUTE, INT-FR-SHA, INT-FR-DEC) and INT-COMMITS. A failure writes the failure report (exit 3)."""
        env = self.env
        self.stage = "phase 0"
        if env.ex is not None:                                                # 4: the imports at 8bff03e (spec 2)
            self.ex = env.ex
        else:
            self.ex = er.import_8bff03e(env.objects_repo, git=er.GitRunner(env.objects_repo))
            self.own_ex = True
            self.au.add_tmp(self.ex.tmp)
        self.pre_env.append("imported at 8bff03e:")
        self.pre_env += [f"  {p} {b}" for p, b in sorted(self.ex.blobs.items())]
        import numpy, scipy, ase
        self.pre_env.append(f"interpreter: Python {sys.version.split()[0]}, numpy {numpy.__version__}, scipy "
                            f"{scipy.__version__}, ase {ase.__version__}")
        self.pre_env.append(f"root: {self.root_rel}; private root: "
                            f"{os.path.realpath(env.private_root) if env.private_root else 'none'}")
        self.pre_env.append("no c3 entry in any root: ok")
        self.pre_env.append("")
        self.ctx_pre()
        self.route_fr()
        self.commits_integrity()

    def ctx_pre(self):
        """INT-IMPORT and INT-GUARD before any archive read (spec 6.2 phase 1 item 1)."""
        g49, c46 = self.ex.g49, self.ex.c46
        eg.assert_restated(g49, c46)
        er.assert_grammar(g49, FAR + HINGE + FR_ORDER)
        s49, s50 = self.git.show("HEAD", "scripts/49_s2_gates.py"), self.git.show("HEAD", "scripts/50_s2_campaign.py")
        if s49 is None or s50 is None:
            raise EIntegrity("INT-IMPORT", "HEAD", "scripts/49, scripts/50")
        eg.check_fr_constants(s49.decode(), s50.decode())                     # RF-17, OP-6
        er.assert_one_47(self.ex.q47)
        self.chk.passed["INT-IMPORT"] += 1
        eg.check_table(eg.TABLE)
        self.chk.passed["INT-GUARD"] += 1

    # ------------------------------------------------------------ attempts (spec 6.2 item 5, section 16; RF-6)
    def out_path(self, name):
        return os.path.join(self.root, OUT_DIR, name)

    def csv_for(self, suffix):
        d = os.path.join(self.root, CSV_DIR)
        return (os.path.join(d, f"fig_s2b_e_fk{suffix}.csv"), os.path.join(d, f"fig_s2b_e_fk{suffix}_meta.csv"))

    def read_out(self, name):
        """A committed E output, read as the HEAD blob (it must be tracked and clean)."""
        rel = f"{self.root_rel}/{OUT_DIR}/{name}"
        if not self.git.tracked(rel) or self.git.porcelain(rel):
            raise EError(f"{rel} is not committed unedited (S2B:525)")
        return self.git.show("HEAD", rel).decode()

    def choose_attempt(self):
        a = self.a
        files = EVAL_FILES if self.mode == "evaluation" else HINGE_FILES
        have = [os.path.exists(self.out_path(f)) for f in files]
        if self.mode == "evaluation":
            if a.hinge_cause or a.prereg or a.prereg_eval:
                raise EError("--hinge-cause, --prereg and --prereg-eval belong to --hinge")
            if have[2]:
                raise EError("E_output_attempt3.txt exists: a fourth attempt is always refused (OP-21)")
            if not have[0]:
                if a.rerun_cause or a.item7_amendment:
                    raise EError("attempt 1 takes no --rerun-cause or --item7-amendment")
                self.attempt = 1
            elif not have[1]:
                if not a.rerun_cause:
                    raise EError("E_output.txt exists: a rerun needs --rerun-cause CASE --amendment NOTE (S2B:521-524)")
                if a.item7_amendment:
                    raise EError("--item7-amendment applies to a third attempt only")
                self.attempt = 2
                t1 = self.read_out(files[0])
                self.attempt1_exit = exit_code_of(t1)
                if self.attempt1_exit not in (0, 1, 3):
                    raise EError("E_output.txt has no exit-code line")
                self.old_head = head_of(t1)
            else:
                t1, t2 = self.read_out(files[0]), self.read_out(files[1])
                if not (a.item7_amendment and a.rerun_cause):
                    raise EError("E_output.txt and E_output_attempt2.txt exist: a third attempt is refused except "
                                 "on the item-7 route (S2B:524, 735-736; OP-21)")
                if exit_code_of(t2) != 3 or "FALLBACK (S2B §7, item 7)" not in t2 or exit_code_of(t1) != 3:
                    raise EError("the item-7 route needs attempts 1 and 2 both failed before output, with the "
                                 "FALLBACK in attempt 2 (RF-6)")
                self.attempt, self.old_head = 3, head_of(t2)
                self.item7_check(self.a.item7_amendment)
        else:
            if a.item7_amendment:                        # --stop-note is allowed: the FR-STOP route (fix round 1)
                raise EError("--item7-amendment belongs to --run")
            if have[1]:
                raise EError("E_hinge_output_attempt2.txt exists: a third hinge run is refused (OP-22)")
            if not have[0]:
                if a.rerun_cause:
                    raise EError("the first hinge run takes no --rerun-cause")
                self.attempt = 1
            else:
                if not a.rerun_cause:
                    raise EError("E_hinge_output.txt exists: a rerun needs --rerun-cause CASE --amendment NOTE "
                                 "(spec 14.3, OP-22)")
                self.attempt, self.old_head = 2, head_of(self.read_out(files[0]))
        name = files[self.attempt - 1]
        self.attempt_path = self.out_path(name)
        self.csv_paths = self.csv_for(SUFFIX[(self.mode, self.attempt)])
        for p in (self.attempt_path,) + self.csv_paths:                       # RF-8: phase 0 asserts absence
            if os.path.exists(p):
                raise EError(f"{os.path.relpath(p, self.root)} exists: E never overwrites an output (S2B:521)")
        if self.attempt > 1 and not self.old_head:
            raise EError("the earlier attempt's line 1 names no HEAD")

    def note_ok(self, path, *, what):
        """A committed, clean note: tracked, unchanged in the tree; returns its HEAD text."""
        g = self.git
        if not isinstance(path, str) or path.startswith("/") or \
                any(s in ("", ".", "..") for s in path.split("/")):            # normalised only (fix round 1)
            raise EError(f"{what}: a normalised repository-relative path is required")
        if not g.tracked(path) or g.porcelain(path):
            raise EError(f"{what} {path} is not committed and clean")
        if g.kind("HEAD", path) != "blob":                                     # IX-6: a blob of HEAD, never a glob
            raise EError(f"{what} {path} is not a file of HEAD")
        b = g.show("HEAD", path)
        if b is None:
            raise EError(f"{what} {path} is not a file of HEAD")
        return b.decode(errors="replace")

    def amendment_ok(self, path, since, *, what="--amendment"):
        """Spec section 7, [48:1348-1368] re-implemented: committed and clean, outside scripts/, added or changed
        after `since`, carrying an ISO date on or after that commit's date."""
        text = self.note_ok(path, what=what)
        if path.startswith("scripts/"):
            raise EError(f"{what} {path} lies under scripts/")
        names = self.git.out("diff", "--name-only", "--diff-filter=AM", since, "HEAD", "--", path).split()
        if path not in names:
            raise EError(f"{what} {path} was not added or changed after {since[:12]}")
        d0 = self.git.cdate(since).date()
        dates = [datetime.date(int(y), int(m), int(d)) for y, m, d in ISO_DATE.findall(text)]
        if not any(x >= d0 for x in dates):
            raise EError(f"{what} {path} carries no ISO date on or after {d0}")
        return hashlib.sha256(text.encode()).hexdigest()

    def item7_check(self, note):
        """OP-21, RF-15: the item-7 amendment, within 30 days of the attempt-2 commit; only E's code changed."""
        g = self.git
        a2rel = f"{self.root_rel}/{OUT_DIR}/{EVAL_FILES[1]}"
        added = g.added(a2rel)
        if len(added) != 1:
            raise EError("E_output_attempt2.txt has no unique adding commit")
        c2, d2 = added[0][0], datetime.datetime.fromisoformat(added[0][1])
        text = self.note_ok(note, what="--item7-amendment")
        if note.startswith("scripts/"):
            raise EError("--item7-amendment lies under scripts/")
        last = g.out("log", "-1", "--format=%H %cI", "--", note).split()
        if not last or not g.strictly_after(last[0], c2) or \
                not within_30_days(d2, datetime.datetime.fromisoformat(last[1])):
            raise EError("--item7-amendment is not committed within 30 days after the attempt-2 commit (S2B:735)")
        changed = set(g.out("diff", "--name-only", c2, "HEAD").split())
        allowed = set(E_FILES) | {note}
        if not changed <= allowed:
            raise EError(f"the item-7 amendment may change only E's code (RF-15): {sorted(changed - allowed)}")
        self.item7 = (note, hashlib.sha256(text.encode()).hexdigest())

    def rerun_checks(self):
        """Spec section 16: CASE passes on the current code and fails on E's files at the earlier attempt's HEAD,
        each in a subprocess (python -B -I) with OpenAudit in self-test mode (RF-9). Fix round 1:
        - E's files must differ between the earlier attempt's HEAD and HEAD (a rerun needs a fix of E's code);
        - the old tree holds every tool and scripts/46-50 at the earlier attempt's HEAD, so that a case which builds a
          synthetic repository runs there as it does here;
        - the earlier code counts as failing only when the case itself fails (its status line: an AssertionError or
          an EIntegrity); a harness error (a missing file, an import error) is refused."""
        if self.attempt == 1:
            return
        case = self.a.rerun_cause
        if self.git.diff_quiet(self.old_head, "HEAD", list(E_FILES)):
            raise EError(f"E's files are unchanged since the earlier attempt ({self.old_head[:12]}): a rerun needs a "
                         f"fix of E's code (S2B:728-729, 736-737; spec 16)")
        st = _sibling("e_selftest")
        if case not in st.CASES:
            raise EError(f"--rerun-cause {case} is not a case of e_selftest.CASES")
        self.stage = "phase 0 (rerun cause)"
        new = self.run_case(self.env.code_dir, case)
        tmp = tempfile.mkdtemp(prefix="e_old_code_")
        try:
            paths = list(TOOLS) + list(SCRIPTS)
            have = [p for p in paths if self.git.exists(self.old_head, p)]
            miss = [p for p in SCRIPTS if p not in have]
            if miss:
                raise EError(f"the earlier attempt's HEAD {self.old_head[:12]} lacks {miss}: its code cannot be run")
            tarp = os.path.join(tmp, "old.tar")
            self.git("archive", "-o", tarp, self.old_head, "--", *have)
            with tarfile.open(tarp) as t:
                t.extractall(os.path.join(tmp, "tree"), filter="data")
            os.remove(tarp)
            dst = os.path.join(tmp, "tree", S2_REL, "s2b")
            os.makedirs(dst, exist_ok=True)
            shutil.copyfile(os.path.join(self.env.code_dir, "e_selftest.py"), os.path.join(dst, "e_selftest.py"))
            old = self.run_case(dst, case)
        finally:
            er.remove_tree(tmp)
        if new != (0, "ok"):
            raise EError(f"--rerun-cause {case} does not pass on the current code (exit {new[0]}, {new[1]})")
        if old[0] == 0 or old[1] == "ok":
            raise EError(f"--rerun-cause {case} passes on the code of the earlier attempt: not a fix (spec 16)")
        if old[1] not in RERUN_FAILS:
            raise EError(f"--rerun-cause {case} on the code of the earlier attempt ended with {old[1]} (exit "
                         f"{old[0]}), not with a failure of the case (an assertion or an integrity check): a harness "
                         f"error does not show that the earlier code was wrong (spec 16)")
        self.pre_commits.append(f"rerun cause: case {case}: passes on the current code; fails on the code at "
                                f"{self.old_head} (exit {old[0]}, {old[1]}); E's files changed since then")
        self.stage = "phase 0"

    def run_case(self, code_dir, case):
        """(exit code, status) of one case in a subprocess: status 'ok', the exception type of a failed case (from
        the case's status line '<id> [<group>] FAILED (<type>: ...'), or 'no status line'."""
        p = subprocess.run([self.env.python, "-B", "-I", os.path.join(code_dir, "e_selftest.py"), "--case", case,
                            "--no-mutants", "--repo", self.env.objects_repo], capture_output=True,
                           env={**os.environ, "TMPDIR": tempfile.gettempdir()})
        rx = re.compile(rf"{re.escape(case)} \[[A-Z]\] (?:(ok) |FAILED \((\w+)[:)])")
        got = [m for m in (rx.match(x) for x in p.stdout.decode(errors="replace").splitlines()) if m]
        if len(got) != 1:
            return p.returncode, "no status line"
        return p.returncode, got[0].group(1) or got[0].group(2)

    # ------------------------------------------------------------ the route (spec 6.1; RF-12)
    def load(self, c, rel, mode, kind):
        return eg.eg_load(self.L, c, rel, mode=mode, kind=kind, audit=self.au)

    def need(self, g, path, types, *, absent_ok=False):
        v = g.get(path)
        if v is ABSENT and absent_ok:
            return ABSENT
        if v is ABSENT or not isinstance(v, types) or (isinstance(v, bool) and bool not in
                                                       (types if isinstance(types, tuple) else (types,))):
            raise EIntegrity("INT-STRUCT", g.where(), path)
        return v

    def present(self, g, what):
        if g is FILE_ABSENT:
            raise EIntegrity("INT-STRUCT", what, "required file absent (RF-12)")
        return g

    def route_admit(self):
        """Spec 6.1, phase 0a: the route from fr/campaign.json's status and fr_outcome alone, the stop note of a final
        STOP (OP-19) and, past FR, block 4's tier_route; the fr-era commit history (RF-3). A second fr-era entry is
        the one fr/STEP0_FIX of a step-0 repeat: CAMPAIGN_COMMIT admits HEAD once and STEP0_FIX is the only other fr
        route (W 50:2577-2604, 2715-2723). Every failure is a refusal."""
        self.stage = "route"
        a, fr = self.a, self.fr
        cj = self.load("fr", "campaign.json", "fr", "campaign_fr")
        if cj is FILE_ABSENT:
            raise EError("fr has not run: none of S2B §7 'When E may run' holds")
        status = cj.get("status")
        if status == "running":
            raise EError("fr is running: none of S2B §7 'When E may run' holds")
        if status not in ("done", "stopped"):
            raise EError(f"fr status {S(status)!r}: E may not run")
        start, commit = cj.get("start_commit"), cj.get("commit")
        if status == "stopped" and start is None and commit is None:    # fix round 2: open for the analyst
            raise EError("fr stopped before its campaign commit was recorded (fr/campaign.json start_commit and commit "
                         "null; W 50 set_campaign): S2B_LAST and the RF-3 check (amendment item 8) are not defined on "
                         "this route, so E refuses it until a dated amendment rules on it")
        if status == "stopped" and gate_fr_unapplied(self.L.cdir("fr")):     # IX-15: before the note is read
            raise EError("fr stopped after gate FR was written but not applied (fr/gates/FR.json without "
                         "fr/gates_applied/gate_FR.gate.json; an N-FR4 or N-FR8 'not applied' Stop of W 50 run_gate): "
                         "a disagreement between the runner and the gate, resolved by a dated fix and a relaunch, "
                         "never by a stop note (IX-15)")
        for x, k in ((start, "start_commit"), (commit, "commit")):
            if not (isinstance(x, str) and re.fullmatch(r"[0-9a-f]{40}", x)):
                raise EError(f"fr/campaign.json {k} is not a 40-hex commit (spec 7)")
        hist = cj.get("commit_history[].to")
        hist = [] if hist is ABSENT else hist
        i0 = next((i for i, t in enumerate(hist) if t == start), None)   # RF-3: earlier entries are C1's and C2's
        era = list(hist[i0:]) if i0 is not None else []
        fr.update(cj=cj, status=status, start=start, commit=commit, era=era, repeat=len(era) >= 2)
        if status == "stopped":
            if not a.stop_note:
                raise EError("fr stopped: a final STOP needs --stop-note NOTE (OP-19)")
            if a.stop_note != STOP_NOTE:                 # IX-6 (amendment item 12): one fixed path, before git is asked
                raise EError(f"--stop-note {a.stop_note}: the stop note is the one file {STOP_NOTE} (IX-6)")
            text = self.note_ok(a.stop_note, what="--stop-note")
            if not stop_note_ok(a.stop_note, text):
                raise EError(f"--stop-note {a.stop_note} is not a dated note under S2/ stating that the fr STOP is "
                             f"final (OP-19)")
            self.stop_note_sha = hashlib.sha256(text.encode()).hexdigest()
            self.route = {"id": "FR-STOP", "fr_part": None, "blocks": (1, 2, 3), "reason": "final STOP in fr"}
            self.pre_route.append(f"route: FR-STOP (fr stopped; no fr/state_end.json; stop note {a.stop_note} sha256 "
                                  f"{self.stop_note_sha})")
            return
        if a.stop_note:                                  # IX-7: beside a done fr, as the figure and 6b refuse
            raise EError(f"--stop-note {a.stop_note} is refused: fr is done, there is no STOP (IX-7)")
        fo = cj.get("fr_outcome")
        if not isinstance(fo, str) or fo not in eg.FR_OUTCOMES:
            raise EError(f"fr/campaign.json fr_outcome {S(fo)!r} is not one of {list(eg.FR_OUTCOMES)} (spec 6.1)")
        fr["outcome"] = fo
        if fo == "pass":
            if not getattr(self.b4, "BLOCK4_IMPLEMENTED", False) is True:
                raise EError("FR passed: block 4 is a stub (BLOCK4_IMPLEMENTED = False); E waits for block 4 "
                             "(spec 6.1)")
            r4 = self.b4.tier_route(self)
            if r4.get("id") not in ("C3B-STOP", "C3B-NOTIER", "C4B-NOTRUN", "C4B-STOP", "C4B-ENDED"):
                raise EError("e_block4.tier_route returned no route of spec section 13")
            self.route = {"id": r4["id"], "fr_part": "pass", "blocks": (1, 2, 3, 4), "reason": None, "b4": r4}
        else:
            self.route = {"id": "FR-FAIL", "fr_part": None, "blocks": (1, 2, 3), "reason": "FR failed"}
        self.pre_route.append(f"route: {self.route['id']} (fr done; fr_outcome {fo})")

    def verify_records(self):
        """S2B:522, OP-18 (phase 0a): the committed, clean verify records of c2 and fr; their sha256 and last line."""
        for c in ("c2", "fr"):
            p = VERIFY_RECORD[c]
            if self.root_rel != S2_REL:
                p = p.replace(S2_REL, self.root_rel, 1)
            t = self.note_ok(p, what=f"verify record of {c}")
            last = [x for x in t.rstrip("\n").split("\n")][-1]
            self.pre_route.append(f"verify record {c}: {p} sha256 {hashlib.sha256(t.encode()).hexdigest()}; last "
                                  f"line: {last}")

    def route_fr(self):
        """Phase 0b (spec 6.1, 8; RF-12): the FR files of the route (state_fr, fr_gate, fr_marker, the records and
        the step-0 files), their absences and consistency (INT-STRUCT, INT-ROUTE, INT-FR-SHA, INT-FR-DEC), then the
        header (spec section 9)."""
        self.stage = "route"
        fr = self.fr
        cj, status = fr["cj"], fr["status"]
        st = self.load("fr", "state_end.json", "fr", "state_fr")
        frg = {f: self.load("fr", f, "fr", "fr_gate") for f in ("gates/FR.json", "gates_applied/gate_FR.gate.json")}
        frm = self.load("fr", "gates_applied/gate_FR.json", "fr", "fr_marker")
        recs = {}
        for lab in FR_ORDER:
            recs[lab] = self.load("fr", f"raw/{lab}.a2.json", "fr", "a2_fr")
        s0 = {}
        for at, sp, stem in (("@2", "s2_m30_VA188", eg.FR_S0_2), ("@4", "s2_m30_Cs188o0_vac", eg.FR_S0_4)):
            s0[at] = {"sp": sp, "a2": eg.FR_STEP0_PAIRS[sp],
                      "copy": self.load("fr", f"gates_applied/{stem}.gate.json", "fr", "fr_step0_gate"),
                      "marker": self.load("fr", f"gates_applied/{stem}.json", "fr", "fr_step0_marker")}
        s0_last = self.load("fr", "gates/fr_step0.json", "fr", "fr_step0_gate")
        # fix round 2 (R-1): the attempt-1 markers set aside for a repeat, by name only (os.listdir; nothing under
        # fr/step0_attempt1/ is opened, S2B:272-273). The archive publishes them whether or not the STEP0_FIX save
        # followed the move (W 50 fr_step0_repeat moves first; archive: discarded/step0_attempt1_*/gates* ->
        # step0_attempt1/<sub>/)
        aside = os.path.join(self.L.cdir("fr"), "step0_attempt1", "gates_applied")
        names = set(os.listdir(aside)) if os.path.isdir(aside) else set()
        fr["aside_named"] = {at: f"{stem}.json" in names for at, stem in (("@2", eg.FR_S0_2), ("@4", eg.FR_S0_4))}
        fr.update(st=st, frg=frg, frm=frm, recs=recs, s0=s0, s0_last=s0_last)
        fr["cells"] = {}
        for lab in FR_ORDER:
            g = recs[lab]
            if g is FILE_ABSENT:
                fr["cells"][lab] = {"status": FILE_ABSENT}
                continue
            fr["cells"][lab] = {p: g.get(p) for p in g.listed()}
            if not isinstance(fr["cells"][lab]["status"], str):
                raise EIntegrity("INT-STRUCT", g.where(), "status")
        # the decisions
        dec = {}
        for f, g in list(frg.items()) + [("gates_applied/gate_FR.json", frm)]:
            if g is not FILE_ABSENT:
                dec[f] = {k: g.get(f"decision.FR.{k}") for k in eg.FR_DECISION_KEYS}
        fr["dec_files"] = dec
        fr["dec"] = dec.get("gates/FR.json")
        # step-0 evaluations that ran (their marker exists)
        ran = [at for at in ("@2", "@4") if s0[at]["marker"] is not FILE_ABSENT]
        fr["s0_ran"] = ran
        self.route_absences(cj, st, frg, frm, status)
        self.rf12_step0()
        self.int_fr()
        self.route_of(cj, st, frg, frm, recs, dec, status)

    def route_absences(self, cj, st, frg, frm, status):
        """RF-12: the absences a route implies, checked before the files are compared: no fr/state_end.json on
        FR-STOP; no gate-FR file on the step-0-final route."""
        if status == "stopped" and st is not FILE_ABSENT:
            raise EIntegrity("INT-ROUTE", "fr/state_end.json", "present although fr stopped (RF-12)")
        if status == "done" and cj.get("fr_outcome") == eg.FR_OUTCOMES[3]:
            self.chk.require(all(g is FILE_ABSENT for g in list(frg.values()) + [frm]), "INT-ROUTE",
                             "fr/campaign.json", "fr_outcome step-0 final")

    def rf12_step0(self):
        """RF-12: the step-0 files each FR cell's status requires, and the absences it implies. Fix round 1 (R-1): a
        final STOP while the repeat of @4 is prepared (gates/fr_step0.json, the @4 trio and the D+V+ a2/ moved to
        discarded/, W 50 fr_step0_repeat) leaves the @2 trio and no gates/fr_step0.json; that absence is accepted on
        this route only (s0_set_aside). Fix round 2: the evidence of the move is the @4 attempt-1 marker's name under
        fr/step0_attempt1/gates_applied/, not the STEP0_FIX commit_history entry, which W's fr_step0_repeat writes
        only after the move (a start cut short between them leaves the move unrecorded)."""
        fr = self.fr
        s0, s0_last, ran, cells = fr["s0"], fr["s0_last"], fr["s0_ran"], fr["cells"]
        va = cells["s2r_m30_VA188"].get("status")
        for at in ("@2", "@4"):
            e = s0[at]
            rk = reached_k0(cells[e["a2"]])
            if (e["marker"] is FILE_ABSENT) != (e["copy"] is FILE_ABSENT):
                raise EIntegrity("INT-STRUCT", f"fr/gates_applied/{eg.applied_id('gate:fr_step0' + at)}", "copy and "
                                 "marker (RF-12)")
            if rk is True and e["marker"] is FILE_ABSENT:
                raise EIntegrity("INT-STRUCT", f"fr/gates_applied/{eg.applied_id('gate:fr_step0' + at)}.json",
                                 f"step-0 evaluation of {e['a2']} absent (RF-12)")
            if rk is False and e["marker"] is not FILE_ABSENT:
                raise EIntegrity("INT-STRUCT", f"fr/gates_applied/{eg.applied_id('gate:fr_step0' + at)}.json",
                                 f"step-0 file present although {e['a2']} never reached k = 0 (RF-12)")
        dv = cells[FR_QUARTET["DV"]]["status"]
        fr["s0_set_aside"] = (s0_last is FILE_ABSENT and ran == ["@2"] and fr["status"] == "stopped" and
                              fr["aside_named"]["@4"] is True and (dv is FILE_ABSENT or dv == "pending"))
        if ran and s0_last is FILE_ABSENT and not fr["s0_set_aside"]:
            raise EIntegrity("INT-STRUCT", "fr/gates/fr_step0.json", "required file absent (RF-12)")
        if not ran and s0_last is not FILE_ABSENT:
            raise EIntegrity("INT-STRUCT", "fr/gates/fr_step0.json", "present without a step-0 evaluation (RF-12)")
        if va is FILE_ABSENT or va in ("not_run_gate", "not_started_cap"):
            if ran:
                raise EIntegrity("INT-STRUCT", "fr/gates/fr_step0.json", "VA188 never reached k = 0 (RF-12)")

    def int_fr(self):
        """INT-FR-SHA and INT-FR-DEC (spec section 8). On the R-1 route (s0_set_aside) there is no gates/fr_step0.json
        to compare: only the @2 copy against its marker."""
        fr, au = self.fr, self.au
        frg, frm, st, dec, s0, s0_last, ran = (fr[k] for k in ("frg", "frm", "st", "dec_files", "s0", "s0_last",
                                                                "s0_ran"))
        if frg["gates/FR.json"] is not FILE_ABSENT or frm is not FILE_ABSENT:
            for f in ("gates/FR.json", "gates_applied/gate_FR.gate.json"):
                self.present(frg[f], f"fr/{f}")
            self.present(frm, "fr/gates_applied/gate_FR.json")
            self.chk.require(au.sha256_of(self.L.file("fr", "gates/FR.json")) == frm.get("gate_file_sha256"),
                             "INT-FR-SHA", "fr/gates/FR.json", "gate_file_sha256 of gates_applied/gate_FR.json")
            vals = list(dec.values())
            self.chk.require(all(d == vals[0] for d in vals), "INT-FR-DEC", "fr/gates/FR.json",
                             "decision.FR identical in FR.json, gate_FR.gate.json and gate_FR.json")
            if st is not FILE_ABSENT:
                sd = {k: st.get(f"FR.{k}") for k in eg.FR_DECISION_KEYS}
                self.chk.require(sd == vals[0], "INT-FR-DEC", "fr/state_end.json", "FR")
        if ran:
            last = s0[ran[-1]]
            if not fr["s0_set_aside"]:
                self.chk.require(au.sha256_of(self.L.file("fr", "gates/fr_step0.json")) ==
                                 last["marker"].get("gate_file_sha256"), "INT-FR-SHA", "fr/gates/fr_step0.json",
                                 f"gate_file_sha256 of the marker of fr_step0{ran[-1]}")
            keys = [p for p in eg.DEC_FR_STEP0]
            for at in ran:
                e = s0[at]
                dc, dm = ({k: e[x].get(k) for k in keys} for x in ("copy", "marker"))
                self.chk.require(dc == dm, "INT-FR-DEC", e["copy"].where(), "decision.fr_step0")
                e["dec"] = dc
            if not fr["s0_set_aside"]:
                self.chk.require({k: s0_last.get(k) for k in keys} == last["dec"], "INT-FR-DEC",
                                 "fr/gates/fr_step0.json", "decision.fr_step0")
            if st is not FILE_ABSENT:
                want = {k: last["dec"][f"decision.fr_step0.{k}"] for k in ("attempts", "outcome", "cell")}
                # integration (IX-2; W 50 preconditions, N-FR6): fr/STEP0_NO_ERROR after attempt 1's failure changes
                # only the state (fail_final, no_error_found True); the gate files keep the fail_pending_fix that
                # scripts/49 recorded at attempt 1. Accepted on the step-0-final route only
                fr["no_error"] = (want["outcome"] == "fail_pending_fix" and want["attempts"] == 1 and
                                  st.get("fr_step0.no_error_found") is True and fr.get("outcome") == eg.FR_OUTCOMES[3])
                if fr["no_error"]:
                    want["outcome"] = "fail_final"
                for k in ("attempts", "outcome", "cell"):
                    self.chk.require(st.get(f"fr_step0.{k}") == want[k], "INT-FR-DEC", "fr/state_end.json",
                                     f"fr_step0.{k}")

    def route_of(self, cj, st, frg, frm, recs, dec, status):
        """Phase 0b, spec 6.1: INT-ROUTE (the decisions against fr_outcome) and the header (spec section 9)."""
        fr = self.fr
        if status != "stopped":
            self.present(st, "fr/state_end.json")
            fo = fr["outcome"]
            for lab in FR_ORDER:
                self.present(recs[lab], f"fr/raw/{lab}.a2.json")
            d = fr["dec"]
            if fo == eg.FR_OUTCOMES[3]:                                       # step-0 final
                ok = frg["gates/FR.json"] is FILE_ABSENT and frg["gates_applied/gate_FR.gate.json"] is FILE_ABSENT \
                    and frm is FILE_ABSENT and st.get("fr_step0.outcome") == "fail_final"
                self.chk.require(ok, "INT-ROUTE", "fr/campaign.json", "fr_outcome step-0 final")
            else:
                self.chk.require(d is not None, "INT-ROUTE", "fr/gates/FR.json", "required (RF-12)")
                want = {"fail (FR-1)": {"outcome": "fail", "part": "FR-1", "FR1": False},
                        "fail (FR-2)": {"outcome": "fail", "part": "FR-2", "FR1": True, "FR2": False},
                        "pass": {"outcome": "pass", "FR1": True, "FR2": True, "part": None}}[fo]
                for f, dd in dec.items():
                    self.chk.require(all(dd[f"{k}"] == v for k, v in want.items()), "INT-ROUTE", f"fr/{f}",
                                     "decision.FR against fr_outcome")
                self.chk.require(all(st.get(f"FR.{k}") == v for k, v in want.items()), "INT-ROUTE",
                                 "fr/state_end.json", "FR against fr_outcome")
            self.pre_route.append(f"  fr_outcome {fo}: decision.FR and fr/state_end.json consistent (INT-ROUTE)")
        else:
            fr["stop_rec"] = self.stop_decision()
        # header (spec section 9)
        self.fr_part = self.header_fr_part()
        # IX-4 (amendment item 13): a final STOP in fr is 'FR fails' (S2B §1) whatever gate FR recorded before it, so
        # on FR-STOP FR is no valid far reference and item 4 is L_ITEM4
        stopped = fr["status"] == "stopped"
        self.k_valid = 0 if stopped else valid_far_refs(fr["dec"])            # OP-11
        self.header = (f"S2 K3: fail (fail_replan); checks_failed: s2r_m30_VB76, check 5 (C2_RESULT.md). S2b FR: "
                       f"{self.fr_part}. Valid far references: {self.k_valid} of 2.")
        self.item4 = "L_FRVALID" if not stopped and (fr["dec"] or {}).get("outcome") == "pass" else "L_ITEM4"

    def stop_decision(self):
        """IX-4 (amendment item 13): on a stopped fr, the FR outcome recorded before the STOP as an fr_outcome string,
        or None. Gate FR's decision comes from its files (INT-FR-DEC has tied them together); the step-0 final from a
        fail_final step-0 decision (attempt 2) or, after fr/STEP0_NO_ERROR (which changes the state only), from the
        fr_outcome that W's scripts/50 records in fr/campaign.json at every STOP of fr (begin_stop: the outcome its
        decisions fix, else null). That fr_outcome must be recorded and agree with the gate files (INT-ROUTE), so
        that E and the FR figure, which reads the same leaf, name one decision."""
        fr = self.fr
        fo = fr["cj"].get("fr_outcome")
        if not (fo is None or fo in eg.FR_OUTCOMES):                     # ABSENT included: W 50 always records it
            raise EIntegrity("INT-ROUTE", "fr/campaign.json", "fr_outcome at the STOP")
        d = fr["dec"]
        last = fr["s0"][fr["s0_ran"][-1]]["dec"] if fr["s0_ran"] else None
        lo, la = (None, None) if last is None else (last["decision.fr_step0.outcome"],
                                                    last["decision.fr_step0.attempts"])
        if d is not None:
            rec = "pass" if d["outcome"] == "pass" else f"fail ({S(d['part'])})"
            want = {"fail (FR-1)": {"outcome": "fail", "part": "FR-1", "FR1": False},
                    "fail (FR-2)": {"outcome": "fail", "part": "FR-2", "FR1": True, "FR2": False},
                    "pass": {"outcome": "pass", "FR1": True, "FR2": True, "part": None}}.get(rec)
            self.chk.require(want is not None and all(d[k] == v for k, v in want.items()), "INT-ROUTE",
                             "fr/gates/FR.json", "decision.FR at the STOP")
            self.chk.require(fo == rec, "INT-ROUTE", "fr/campaign.json", "fr_outcome at the STOP against decision.FR")
        elif lo == "fail_final":                                           # attempt 2 failed: the gate records it
            rec = eg.FR_OUTCOMES[3]
            self.chk.require(fo == rec, "INT-ROUTE", "fr/campaign.json",
                             "fr_outcome at the STOP against decision.fr_step0")
        elif fo == eg.FR_OUTCOMES[3]:                                     # fr/STEP0_NO_ERROR, then the STOP
            self.chk.require(lo == "fail_pending_fix" and la == 1, "INT-ROUTE", "fr/campaign.json",
                             "fr_outcome at the STOP against decision.fr_step0")
            rec = fo
            fr["no_error_stop"] = True
        else:
            self.chk.require(fo is None, "INT-ROUTE", "fr/campaign.json", "fr_outcome at the STOP without a decision")
            rec = None
        self.pre_route.append(f"  fr_outcome at the STOP {S(fo)}: " + ("no FR outcome recorded before the STOP" if
                                                                        rec is None else
                                                                        f"recorded before the STOP: {rec}"))
        return rec

    def header_fr_part(self):
        fr = self.fr
        if fr["status"] == "stopped":                 # fix round 2: the first FR cell not complete (absent, pending,
            reason = S(fr["cj"].get("stop_reason"))  # killed_by_gate, not_run_gate, ...)
            rec = fr.get("stop_rec")
            if rec is None:                           # ER2-13
                cell = next((lab for lab in FR_ORDER if fr["cells"][lab]["status"] is FILE_ABSENT or
                             fr["cells"][lab]["status"] != "complete"), "gate FR")
                return f"stopped at {cell} ({reason})"
            if rec == "pass":                         # IX-4: the decision recorded before the STOP, then the STOP
                return f"pass at gate FR; then a final STOP ({reason}); counted as FR fails (S2B §1)"
            return f"{self.decided_part(rec)}; then a final STOP ({reason})"
        return self.decided_part(fr["outcome"])

    def decided_part(self, fo):
        """The header's FR part of an FR outcome fo (an fr_outcome string), FR-1 with its cell and reason."""
        fr = self.fr
        if fo in ("pass", "fail (FR-2)", eg.FR_OUTCOMES[3]):
            return fo
        d = fr["dec"]
        cell, kind = d["cell"], d["kind"]
        c = fr["cells"].get(cell, {}) if isinstance(cell, str) else {}
        failed = c.get("validity_final.failed", ABSENT)
        if kind == "check" and not isinstance(failed, list):                  # fallback: the reason list
            cf = fr["frg"]["gates/FR.json"].get("result.checks_failed")
            m = [re.search(r"\[([0-9, ]+)\]", x) for x in (cf if isinstance(cf, list) else []) if
                 isinstance(x, str) and x.startswith(f"{cell}:")]
            failed = [int(v) for v in m[0].group(1).split(",")] if m and m[0] else ABSENT
        return f"fail (FR-1, {cell}, {fr_reason(kind, failed, c.get('end_rule.outcome', ABSENT))})"

    def frstop_pass(self, outcome):
        """IX-12 (amendment item 13): True on FR-STOP when gate FR recorded a pass (outcome: decision.FR.outcome), the
        route 'pass at gate FR; then a final STOP'. There every FR-quartet value E prints that carries no item-4 label
        (E_b^A2(FA188) in block 2, XC-FR2 and the item-7 fallback) carries L_FRSTOP; the A1 values keep L_ITEM4."""
        return (self.route or {}).get("id") == "FR-STOP" and outcome == "pass"

    # ------------------------------------------------------------ the commits (spec section 7; OP-20, RF-3)
    def commits_admit(self):
        """Spec section 7, phase 0a (OP-20, RF-3): E's files at fr start_commit, at every fr-era commit_history entry
        and at commit, and block 4 implemented at the c3b start commit (no amendment route); scripts/46-50 and E's
        tools unchanged from S2B_LAST to HEAD, or changed under a valid dated amendment (validated whenever it is
        named); the printed diffs. Every failure is a refusal."""
        self.stage = "commits"
        g, fr = self.git, self.fr
        start, commit = fr["start"], fr["commit"]
        fr_era = [start] + list(fr["era"]) + [commit]
        s2b_commits = [("fr start", start), ("fr", commit)]
        b4c = (self.route.get("b4") or {}).get("commits") or {}
        for k in ("c3b", "c4b"):
            if b4c.get(k):
                s2b_commits.append((k, b4c[k]))
        last = s2b_commits[-1][1]
        self.s2b_last = last
        e_rel = [p for p in E_FILES]
        for c in dict.fromkeys(fr_era + [last]):
            miss = [p for p in e_rel if not g.exists(c, p)]
            if miss:
                raise EError(f"E's files are missing at the S2b campaign commit {c[:12]}: {miss} (RF-3; no amendment "
                             f"route)")
        if self.route["id"] not in ("FR-FAIL", "FR-STOP"):
            c3s = b4c.get("c3b_start")
            blob = g.show(c3s, f"{S2_REL}/s2b/e_block4.py") if c3s else None
            if blob is None or not re.search(rb"^BLOCK4_IMPLEMENTED = True\b", blob, re.M):
                raise EError("e_block4.py with BLOCK4_IMPLEMENTED = True is not in the c3b start commit (RF-3)")
        paths = list(SCRIPTS) + list(TOOLS)
        quiet = g.diff_quiet(last, "HEAD", paths)
        lines = ["", "COMMITS (S2B:615-617; spec section 7)", f"  C2 campaign commit: {self.env.c2_commit}"]
        lines += [f"  S2b campaign commit ({k}): {c}" for k, c in s2b_commits]
        lines.append(f"  S2B_LAST (the last S2b campaign commit): {last}")
        st_ = g.out("diff", "--stat", self.env.c2_commit, last, "--", *SCRIPTS)
        dfull = g("diff", self.env.c2_commit, last, "--", *SCRIPTS)[1]
        lines.append(f"  git diff --stat C2 -> S2B_LAST -- scripts/46-50 (full diff sha256 "
                     f"{hashlib.sha256(dfull).hexdigest()}; Appendix A):")
        lines += ["    " + x for x in st_.rstrip("\n").split("\n")] if st_.strip() else ["    (no difference)"]
        for (k1, a1), (k2, a2) in zip(s2b_commits[:-1], s2b_commits[1:]):
            if a1 != a2:
                s = g.out("diff", "--stat", a1, a2, "--", *SCRIPTS, *TOOLS)
                lines.append(f"  git diff --stat {k1} -> {k2}:")
                lines += ["    " + x for x in s.rstrip("\n").split("\n")] if s.strip() else ["    (no difference)"]
        lines.append(f"  E's files at every fr campaign commit ({len(dict.fromkeys(fr_era))}): ok (RF-3)")
        if self.a.amendment:                                                  # validated whenever named
            self.amend = (self.a.amendment, self.amendment_ok(self.a.amendment, last))
        if quiet:
            lines.append("  scripts/46-50 and E's tools: S2B_LAST -> HEAD unchanged")
            if self.amend:
                lines.append(f"  amendment named: {self.amend[0]} (sha256 {self.amend[1]})")
        else:
            if not self.amend:
                raise EError("scripts/46-50 or E's files differ between S2B_LAST and HEAD without --amendment "
                             "(S2B:615-617)")
            s = g.out("diff", "--stat", last, "HEAD", "--", *paths)
            lines.append(f"  S2B_LAST -> HEAD changed under the amendment {self.amend[0]} (sha256 {self.amend[1]}):")
            lines += ["    " + x for x in s.rstrip("\n").split("\n")]
        if self.attempt == 3:
            lines.append(f"  item-7 amendment: {self.item7[0]} (sha256 {self.item7[1]})")
        self.pre_commits += lines
        self.appendix = (dfull.decode(errors="replace").rstrip("\n").split("\n") if dfull.strip() else
                         ["(no difference)"])

    def commits_integrity(self):
        """Spec section 7, phase 0b: INT-COMMITS (campaign_c2 commit = C2_COMMIT; state_fr campaign_commit.fr =
        fr/campaign.json commit)."""
        self.stage = "commits"
        c2 = self.load("c2", "campaign.json", "far", "campaign_c2")
        self.present(c2, "c2/campaign.json")
        self.chk.require(self.need(c2, "commit", str) == self.env.c2_commit, "INT-COMMITS", "c2/campaign.json",
                         "commit")
        if self.fr["st"] is not FILE_ABSENT:
            self.chk.require(self.fr["st"].get("campaign_commit.fr") == self.fr["commit"], "INT-COMMITS",
                             "fr/state_end.json", "campaign_commit.fr")
        self.chk.passed["INT-COMMITS"] += 1

    # ------------------------------------------------------------ the hinge run's preconditions (RF-1)
    def standing_output(self):
        """The evaluation output that stands (RF-6): the latest attempt with exit 0 or 1, or holding the FALLBACK."""
        have = [(f, self.read_out(f)) for f in EVAL_FILES if os.path.exists(self.out_path(f))]
        if not have:
            raise EError("no evaluation output exists: the hinge run follows E (spec 14.3)")
        for f, t in reversed(have):
            if exit_code_of(t) in (0, 1) or (exit_code_of(t) == 3 and "FALLBACK (S2B §7, item 7)" in t):
                return have, f, t
        raise EError("no evaluation output stands (spec 14.3, RF-6)")

    def prereg_ok(self, note, attempt_commit, *, raise_=True):
        """RF-1 conditions on a later pre-registration NOTE; returns (ok, why)."""
        g = self.git
        try:
            if NOTE_DENY.fullmatch(note) or re.search(r"(^|/)(E_(hinge_)?output|fig_s2b_e_fk)", note):
                raise EError(f"{note} is on the deny-list (RF-1)")
            text = self.note_ok(note, what="--prereg")
            add = g.added(note)
            if len(add) != 1:
                raise EError(f"{note} has no unique adding commit")
            c, d = add[0][0], datetime.datetime.fromisoformat(add[0][1])
            if not g.strictly_after(c, attempt_commit):
                raise EError(f"{note} was not added after the commit of the last E attempt file (RF-1)")
            if not d.astimezone(datetime.timezone.utc).date() < BACKSTOP:     # fix round 2: the UTC date (RF-1)
                raise EError(f"{note} was committed on or after {BACKSTOP} (RF-1)")
            if not any(STATUS_PLAN.search(x) for x in text.split("\n")[:40]):
                raise EError(f"{note} has no 'Status: PLAN' line in its first 40 lines (RF-1)")
            if "E_hinge_output.txt" not in text:
                raise EError(f"{note} does not name E_hinge_output.txt (RF-1)")
            return True, c
        except EError as e:
            if raise_:
                raise
            return False, str(e)

    def hinge_preconditions(self):
        """Spec 14.3, RF-1, phase 0a: the standing output (RF-6) left block 5 unopened; the cause (a later
        pre-registration and its evaluation record, or the backstop on the real UTC date); on the FR-STOP route the
        stop note re-validated at HEAD is the one the standing output names, unchanged (fix round 1)."""
        a, g = self.a, self.git
        have, name, text = self.standing_output()
        if NOT_OPENED not in text:
            raise EError(f"{name} opened block 5: the hinge block was read at E (spec 14.3)")
        latest = have[-1][0]
        add = g.added(f"{self.root_rel}/{OUT_DIR}/{latest}")
        if len(add) != 1:
            raise EError(f"{latest} has no unique adding commit")
        ac = add[0][0]
        if a.hinge_cause == "prereg":
            if not a.prereg or not a.prereg_eval:
                raise EError("--hinge-cause prereg needs --prereg NOTE and --prereg-eval REC (RF-1)")
            ok, nc = self.prereg_ok(a.prereg, ac)
            rec = self.note_ok(a.prereg_eval, what="--prereg-eval")
            ra = g.added(a.prereg_eval)
            if len(ra) != 1 or not g.strictly_after(ra[0][0], nc):
                raise EError("--prereg-eval was not added after the pre-registration's commit (RF-1)")
            if a.prereg not in rec:
                raise EError("--prereg-eval does not name the pre-registration (RF-1)")
            self.pre_route.append(f"hinge cause: prereg {a.prereg} (added {nc}); evaluation record {a.prereg_eval}")
        elif a.hinge_cause == "backstop":
            if a.prereg or a.prereg_eval:
                raise EError("--hinge-cause backstop takes no --prereg")
            today = self.env.now().date()
            if today < BACKSTOP:
                raise EError(f"the backstop is {BACKSTOP}; today is {today} (UTC) (S2B:719)")
            for p in g.added_since(ac):                 # fix round 2: renamed files too (--no-renames)
                if self.prereg_ok(p, ac, raise_=False)[0]:
                    raise EError(f"a later pre-registration ({p}) has replaced the backstop (RF-1)")
            self.pre_route.append(f"hinge cause: backstop {BACKSTOP} (UTC date {today})")
        else:
            raise EError("--hinge needs --hinge-cause prereg or backstop")
        if self.route["id"] == "FR-STOP":               # fix round 1 (M3); round 2: a missing route line is refused
            m = ROUTE_STOP_NOTE.search(text)
            if m is None:
                raise EError(f"{name} names no stop note on its FR-STOP route line: the hinge run cannot show it uses "
                             f"the same one (OP-19)")
            if (m.group(1), m.group(2)) != (a.stop_note, self.stop_note_sha):
                raise EError(f"--stop-note {a.stop_note} is not the stop note of {name} ({m.group(1)}, unchanged; "
                             f"OP-19)")
        self.pre_route.append(f"standing evaluation output: {name} (exit {exit_code_of(text)}; '{NOT_OPENED}')")

    # ------------------------------------------------------------ phase 1 (spec 6.2)
    def phase1(self):
        env, au = self.env, self.au
        self.stage = "prechecks"
        self.cd = er.load_cd()
        calc_check(self.cd, "INT-CALC-LOAD")
        self.chk.passed["INT-CALC-LOAD"] += 1
        self.ctx = er.ReadCtx(self.L, au, self.ex, checks=self.chk)
        self.c1 = eg.C1Access(self.L, self.ex.c46, self.ex.q47, au, self.ctx.reads, hinge=False)
        self.c1.load_census()
        self.chk.passed["INT-C1-CENSUS"] += 1
        self.stage = "C1 reads"
        au.set_block(3)
        self.T, self.ledger = er.build_c1_table(self.c1, self.ctx)            # block 3 data (block 2 uses its SPs)
        self.chk.passed["INT-SP"] += len(self.ctx.reads.labels["sp"])
        quiet = self.mode == "hinge"
        for n, fn in ((1, self.block1), (2, self.block2), (3, self.block3)):
            self.stage = f"block {n}"
            o = Out(self.item4, self.xcs)
            fn(o, quiet=quiet)
            self.outs[n] = o
        self.stage = "block 4"
        self.block4_and_5()
        if "before_exit_audit" in env.hooks:
            env.hooks["before_exit_audit"](self)
        self.stage = "exit audit"
        self.exit_audit()
        return 1 if any(ok is False for _, ok in self.xcs) else 0

    # ------------------------------------------------------------ per-relaxation items (S2B:638-642)
    def print_relax(self, o, block, r, *, number, c2const=None, tails=None, plateau=False, quartet=""):
        lab, lv = r["label"], r.get("leaves") or {}
        rid = f"B{block}.{lab}"
        o.line(f"  {number}. {lab} ({r['campaign']}): status {r['status']}; end rule {S(lv.get('end_rule.outcome'))}"
               f"; end {S(lv.get('end_rule.end', ABSENT))}")
        if not r.get("parsed"):
            o.row(block, rid + ".status", "status", f"not parsed (status {r['status']})")
            return
        if r.get("F0") is None:
            why = r.get("not_formed")
            for item in ("F(0)", "F(final)", "relaxation energy", "path work", "F(k) − F(final)", "ΔF_tail"):
                o.row(block, f"{rid}.{item}", "note", f"{item}: {L_NOTFORMED(why)}")
        else:
            o.row(block, rid + ".F0", "F", f"F(0) = {fe(r['F0'])} eV", values={"F0_eV": r["F0"]})
            o.row(block, rid + ".Ffin", "F", f"F(final) = {fe(r['Ffin'])} eV at k = {r['k_last']}",
                  values={"Ffin_eV": r["Ffin"], "k_last": r["k_last"]})
            o.row(block, rid + ".relax", "relax_energy",
                  f"relaxation energy F(final) − F(0) = {fm(r['relax_meV'])} meV",
                  values={"relax_meV": r["relax_meV"]})
        cnt = {k: lv.get(k, ABSENT) for k in C2_KEYS}
        o.row(block, rid + ".counts", "status", "n_config " + S(cnt["n_config"]) + ", converged_at_k " +
              S(cnt["converged_at_k"]) + ", k_last " + S(lv.get("k_last", ABSENT)) + ", restarts " +
              S(cnt["restarts"]) + ", reruns_from_zero " + S(cnt["reruns_from_zero"]))
        if c2const is not None:                                               # XC-C2R (spec 10.1)
            for k, want in zip(C2_KEYS, c2const):
                got = cnt[k]
                o.xc(block, "XC-C2R", got is not ABSENT and got == want and not isinstance(got, bool),
                     f"{lab} {k} {S(got)}; C2_RESULT.md §2: {want}")
        xp = r["xc"]["PARTS"]
        if xp["ok"] is None:
            o.xc(block, "XC-PARTS", None, f"{lab} parts {xp['n_parts']}, restarts {xp['restarts']}: restarts include "
                                          f"discarded attempts (reruns_from_zero > 0; INT-PARTS held)")
        else:
            o.xc(block, "XC-PARTS", xp["ok"], f"{lab} parts {xp['n_parts']} against restarts + 1 = "
                                              f"{xp['restarts'] + 1}")
        xe = r["xc"]["ENDRULE"]
        o.xc(block, "XC-ENDRULE", xe["ok"], f"{lab} end rule {xe['record']} against {xe['basis']}"
                                            + (f" {xe['recomputed']}" if xe["recomputed"] is not None else ""))
        if r.get("F0") is None:
            return
        pw = r.get("pw")
        if pw is None:
            o.row(block, rid + ".pw", "path_work",
                  f"path work: {L_NOTFORMED(r.get('pw_reason') or '< 2 configurations')}")
        else:
            o.row(block, rid + ".pw", "path_work",
                  f"path work: total W = {fm(pw['total_meV'])} meV; closure W − (F(final) − F(0)) = "
                  f"{fm(pw['closure_meV'])} meV (reported only); Σ|dr|² = {fa2(pw['sum_dr2_A2'])} Å²",
                  values={"total_meV": pw["total_meV"], "closure_meV": pw["closure_meV"],
                          "sum_dr2_A2": pw["sum_dr2_A2"]})
            o.line("    by shell (minimum-image distance from the k = 0 position to v or the site; lattice images "
                   "passed to scripts/48 path_work unchanged):")
            for sh in ("0-4", "4-6", "6-8", "8-1e+09"):
                o.row(block, f"{rid}.pw.{sh}", "path_work", f"{sh}: W = {fm(pw['shells_meV'][sh])} meV, Σ|dr|² = "
                      f"{fa2(pw['shells_dr2_A2'][sh])} Å²", values={"W_meV": pw["shells_meV"][sh],
                                                                    "dr2_A2": pw["shells_dr2_A2"][sh]}, indent="      ")
        xm = r["xc"]["MIC"]
        o.xc(block, "XC-MIC", xm["ok"], f"{lab} image-centre against minimum-image distances: max residual "
                                        f"{fr3(xm.get('max_residual_A', float('nan')))} Å "
                                        f"(tolerance {xm.get('tol_A', 0):g} Å)")
        o.line("    F(k) − F(final) (meV):")
        cur, kl = r["curve_meV"], r["k_last"]
        starts = {p["k_first"]: p["n"] for p in r["parts"] if p["n"] > 1 and p.get("n_config")}
        for k0 in range(0, kl + 1, 10):
            ks = list(range(k0, min(k0 + 10, kl + 1)))
            mark = "".join(f"  | restart part {starts[k]} at k = {k}" for k in ks if k in starts)
            o.row(block, f"{rid}.curve.{k0}", "curve",
                  f"k {ks[0]}-{ks[-1]}: " + " ".join(fm(cur[k]) for k in ks) + mark, values={k: cur[k] for k in ks},
                  indent="      ")
        if tails:
            for kt in tails:
                o.row(block, f"{rid}.tail.{kt}", "dF_tail", f"ΔF_tail {lab}: F({kt}) − F(final) = "
                      f"{fm(r['tail'][kt])} meV", values={"k": kt, "dF_meV": r["tail"][kt]})
        elif tails is not None and r.get("tail_reason"):
            o.row(block, f"{rid}.tail", "dF_tail", f"ΔF_tail {lab}: {L_NOTFORMED(r['tail_reason'])}")
        if plateau:
            if r.get("k_last") == er.K_CAP:
                o.row(block, rid + ".plateau", "note", f"plateau difference F(200) − F(180) = "
                      f"{fm(r['plateau_meV'])} meV (from the parse)", values={"plateau_meV": r["plateau_meV"]})
            else:
                o.row(block, rid + ".plateau", "note", "plateau difference: none (k_last < 200)")
        self.csv_add(block, r, number, quartet)

    def csv_add(self, block, r, number, quartet):
        """Figure source data (OP-24; spec section 17): one row per k."""
        part_of = {}
        for p in r["parts"]:
            if p.get("n_config"):
                for k in range(p["k_first"], p["k_last"] + 1):
                    part_of[k] = p["n"]
        starts = {p["k_first"] for p in r["parts"] if p["n"] > 1 and p.get("n_config")}
        kt = r["k_last"] - er.TAIL_BACK
        for k in sorted(r["curve_meV"]):
            self.csv_rows.append({"block": block, "campaign": r["campaign"], "order": number, "label": r["label"],
                                  "quartet": quartet, "role": role_of(r["label"]), "k": k, "part": part_of.get(k, ""),
                                  "dF_meV": repr(r["curve_meV"][k]), "k_last": r["k_last"],
                                  "restart_start": 1 if k in starts else 0, "tail_k": kt if kt >= 0 else ""})
        self.v.setdefault("end_rules", {})[r["label"]] = (r.get("leaves") or {}).get("end_rule.outcome")

    def require_complete(self, r, c):
        if not r.get("parsed") or r.get("F0") is None:
            raise EIntegrity("INT-STRUCT", f"{c}/raw/{r['label']}.a2.json", "status complete with configurations")

    # ------------------------------------------------------------ K3 (S2B:547-554)
    def read_k3(self, mode):
        out = {}
        for f in ("gates/K3.json", "gates_applied/gate_K3.gate.json"):
            g = self.present(self.load("c2", f, mode, "k3"), f"c2/{f}")
            if not g.is_none("result.value_meV"):
                raise EIntegrity("INT-K3-NULL", f"c2/{f}", "result.value_meV")
            self.chk.passed["INT-K3-NULL"] += 1
            out[f] = g
        mk = self.present(self.load("c2", "gates_applied/gate_K3.json", "far", "k3_marker"),
                          "c2/gates_applied/gate_K3.json")
        self.chk.require(self.au.sha256_of(self.L.file("c2", "gates/K3.json")) == mk.get("gate_file_sha256"),
                         "INT-K3-SHA", "c2/gates/K3.json", "gate_file_sha256 of gates_applied/gate_K3.json")
        decs = [g.get("decision.K3") for g in list(out.values()) + [mk]]
        self.chk.require(all(d == "fail_replan" for d in decs), "INT-K3-DEC", "c2/gates/K3.json", "decision.K3")
        cf = [g.get("result.checks_failed") for g in out.values()]
        self.chk.require(cf[0] == cf[1] == K3_CHECKS_FAILED, "INT-K3-DEC", "c2/gates/K3.json", "result.checks_failed")
        return out

    # ------------------------------------------------------------ block 1 (spec section 10)
    def block1(self, o, *, quiet=False):
        au = self.au
        au.set_block(1)
        o.line("BLOCK 1. Far block: C2 relaxations 5-8 (m30, Pb76)")
        o.line(self.header)
        k3 = self.read_k3("far")
        rel = {}
        o.line(" 1.1 Per relaxation")
        for i, lab in enumerate(FAR, 5):
            tks = [TAIL_K[lab]] + (list(VB76_EXTRA_K) if lab == "s2r_m30_VB76" else [])
            r = er.read_relaxation(self.ctx, "c2", lab, mode="far", kind="a2_far", tail_ks=tks, block=1)
            self.require_complete(r, "c2")
            self.chk.require(TAIL_K[lab] == r["k_last"] - er.TAIL_BACK, "INT-STRUCT", f"c2/raw/{lab}.a2.json",
                             "TAIL_K = k_last - 36")
            rel[lab] = r
            self.print_relax(o, 1, r, number=i, c2const=C2_RESULT[lab], quartet="Pb76")
        self.v["far"] = rel
        hc = {}
        for lab in HINGE:                                                     # relaxations 1-4: leaves only
            g = self.present(self.load("c2", f"raw/{lab}.a2.json", "far", "a2_hinge_counts"), f"c2/raw/{lab}.a2.json")
            hc[lab] = {p: g.get(p) for p in g.listed()}
        self.v["hinge_counts"] = hc
        o.line(" 1.2 ΔF_tail = F(k_last − 36) − F(final) (S2B:643-645)")
        for lab in FAR:
            r = rel[lab]
            for kt in [TAIL_K[lab]] + (list(VB76_EXTRA_K) if lab == "s2r_m30_VB76" else []):
                o.row(1, f"B1.{lab}.tail.{kt}", "dF_tail", f"{lab}: F({kt}) − F(final) = {fm(r['tail'][kt])} meV",
                      values={"k": kt, "dF_meV": r["tail"][kt]})
        o.line(" 1.3 The quartet (Sr at Pb76)")
        q = {role_of(lab): rel[lab] for lab in FAR}
        a1 = eb({k: r["F0"] for k, r in q.items()})
        a2 = eb({k: r["Ffin"] for k, r in q.items()})
        d = a2 - a1
        gN = er.read_json(self.L.gate("c1", "N"))
        nv = (((((gN.get("result") or {}).get("dopants") or {}).get("Sr") or {}).get("hosts") or {}).get("m30") or {}) \
            .get("per_site_meV", {}).get("76")
        o.row(1, "B1.EbA1", "Eb_A1", f"E_b^A1(Pb76) from k = 0 = {fm(a1)} meV; C1 (gate N; C1_RESULT.md §6): "
              f"−5.0 meV; difference E_b^A1 − (−5.0) = {full(a1 - (-5.0))} meV",
              values={"Eb_A1_meV": a1, "diff_minus5_meV": a1 - (-5.0)})
        if isinstance(nv, (int, float)) and not isinstance(nv, bool):
            o.row(1, "B1.EbA1.gateN", "Eb_A1", f"gate N unrounded c1/gates/N.json result.dopants.Sr.hosts.m30."
                  f"per_site_meV[\"76\"] = {full(nv)} meV; difference E_b^A1 − gate N = {full(a1 - nv)} meV",
                  values={"gateN_meV": nv, "diff_gateN_meV": a1 - nv})
        else:
            raise EIntegrity("INT-STRUCT", "c1/gates/N.json", "result.dopants.Sr.hosts.m30.per_site_meV.76")
        o.row(1, "B1.EbA2", "Eb_A2", f"E_b^A2(Pb76) = {fm(a2)} meV", values={"Eb_A2_meV": a2}, labels=("L_FAR",))
        o.row(1, "B1.delta", "delta", f"δ_far(Pb76) = E_b^A2 − E_b^A1 = {fm(d)} meV", values={"delta_meV": d},
              labels=("L_FAR",), has_a1=True)
        self.v.update(Pb76={"A1": a1, "A2": a2, "delta": d})
        o.line(" 1.4 Cross-checks")
        for f, g in k3.items():
            far = g.get("result.Eb_A2_meV.far")
            fs = fm(far) if isinstance(far, float) else S(far)
            o.xc(1, "XC-K3FAR", close(a2, far), f"E_b^A2(Pb76) {fm(a2)} meV against c2/{f} result.Eb_A2_meV.far "
                                                f"{fs} meV, {resid(a2, far)}")
        dsum = (q["DV"]["relax_meV"] - q["D"]["relax_meV"]) - (q["V"]["relax_meV"] - q["host"]["relax_meV"])
        o.xc(1, "XC-DSUM-FAR", close(d, dsum), f"δ_far(Pb76) {fm(d)} meV against the signed sum of the relaxation "
                                               f"energies {fm(dsum)} meV, {resid(d, dsum)}", has_a1=True,
             labels=("L_FAR",))                                         # ER2-2: as B1.delta
        bad = []
        for lab in HINGE + FAR:
            lv = hc[lab] if lab in hc else rel[lab]["leaves"]
            n = lv.get("n_config", ABSENT)
            if n is ABSENT or not isinstance(n, int) or n > er.K_CAP or lv.get("end_rule.outcome") != \
                    "accepted_converged":
                bad.append(lab)
        o.xc(1, "XC-PLATEAU", not bad, "plateau differences: none" if not bad else
             f"plateau differences: not none ({', '.join(bad)})")

    # ------------------------------------------------------------ block 2 (spec section 11)
    def block2(self, o, *, quiet=False):
        au, fr = self.au, self.fr
        au.set_block(2)
        o.line("BLOCK 2. FR block: m30 FA188, Cs (S2B §2)")
        o.line(self.header)
        cells = fr["cells"]
        o.line(" Status (both readings of check 5, S2B:267)")
        for lab in FR_ORDER:
            c = cells[lab]
            st = c["status"]
            if st is FILE_ABSENT:
                o.row(2, f"B2.{lab}.status", "status", f"{lab}: no record (not started)")
                continue
            txt = f"{lab}: status {st}"
            if st == "complete":
                txt += f"; end rule {S(c.get('end_rule.outcome'))}"
                if c.get("validity_final.valid", ABSENT) is ABSENT:
                    txt += "; final-geometry check not evaluated"
                else:
                    txt += (f"; validity_final valid {S(c['validity_final.valid'])} failed "
                            f"{S(c.get('validity_final.failed', ABSENT))} (check5_reading "
                            f"{S(c.get('validity_final.check5_reading', ABSENT))}; as written: valid "
                            f"{S(c.get('validity_final.valid_as_written', ABSENT))} failed "
                            f"{S(c.get('validity_final.failed_as_written', ABSENT))}; invariant_only "
                            f"{S(c.get('validity_final.invariant_only', ABSENT))})")
            o.row(2, f"B2.{lab}.status", "status", txt)
        self.v["fr_status"] = {lab: ("no record" if cells[lab]["status"] is FILE_ABSENT else S(cells[lab]["status"]))
                               for lab in FR_ORDER}                          # figure meta (spec 17 panel b)
        rel = {}
        if not quiet:
            o.line(" 2.1 Per relaxation")
            for i, lab in enumerate(FR_ORDER, 1):
                if cells[lab]["status"] != "complete":
                    continue
                r = er.read_relaxation(self.ctx, "fr", lab, mode="fr", kind="a2_fr", plateau=True, block=2)
                rel[lab] = r
                self.print_relax(o, 2, r, number=i, tails=([r["k_last"] - er.TAIL_BACK] if r.get("F0") is not None
                                                            and r["k_last"] >= er.TAIL_BACK else []),
                                 plateau=True, quartet="FA188")
        self.v["fr_rel"] = rel
        # 2.2 step 0 (amendment item 3; RF-5)
        o.line(" 2.2 Step 0 (S2B §2; amendment item 3)")
        aside = [at for at in ("@2", "@4") if fr["aside_named"][at]]
        if fr.get("repeat"):                             # fr/STEP0_FIX (S2B:271-274; fix round 1)
            o.row(2, "B2.step0.repeat", "note", f"step-0 repeat: fr/STEP0_FIX recorded (a second fr campaign commit "
                  f"in commit_history, {fr['era'][1]}); the attempt-1 files are set aside unread (S2B:271-274)")
        elif aside:                                      # fix round 2 (R-1): moved, the save not made
            o.row(2, "B2.step0.repeat", "note", f"step-0 repeat prepared, not recorded: the attempt-1 files of "
                  f"fr_step0{', fr_step0'.join(aside)} are set aside unread (named under fr/step0_attempt1/), and "
                  f"commit_history holds no fr/STEP0_FIX entry (a start cut short between the move and its save; W 50 "
                  f"fr_step0_repeat)")
        if not fr["s0_ran"]:
            o.row(2, "B2.step0", "note", "no fr step-0 evaluation in force (the attempt-1 evaluation is set aside for "
                  "its repeat)" if fr.get("repeat") or aside else
                  "no fr step-0 evaluation ran (V⁺_R(A188) never reached k = 0)")
        for at in fr["s0_ran"]:
            e = fr["s0"][at]
            sp, lab = e["sp"], e["a2"]
            dF = e["copy"].get(f"result.cells.{sp}.dF_meV")
            ps = e["copy"].get(f"result.cells.{sp}.passed")
            outc = e["dec"]["decision.fr_step0.outcome"]
            o.row(2, f"B2.step0.{sp}.gate", "note", f"fr_step0{at} {sp}: dF_meV = "
                  f"{fm(dF) if isinstance(dF, float) else S(dF)} meV, passed {S(ps)}, decision {S(outc)} -- "
                  f"{STEP0_GATE}", values={"dF_meV_gate": dF})
            dk = {k[len("decision.fr_step0."):]: S(v) for k, v in e["dec"].items()}
            a1 = [e["dec"][f"decision.fr_step0.attempt1.{k}"] for k in ("attempts", "outcome", "cell")]
            o.row(2, f"B2.step0.{sp}.decision", "note",       # the non-energy leaves (fix round 1; amendment 2)
                  f"fr_step0{at} decision: attempts {dk['attempts']}, repeat {dk['repeat']}, fix_note "
                  f"{dk['fix_note']}, no_error_found {dk['no_error_found']}, note {dk['note']}; " +
                  ("no repeat (no attempt-1 leaves)" if all(x is ABSENT for x in a1) else   # fix round 2 (wording)
                   f"attempt 1 (its files set aside unread): attempts {dk['attempt1.attempts']}, outcome "
                   f"{dk['attempt1.outcome']}, cell {dk['attempt1.cell']}"))
            st = cells[lab]["status"]
            if st == "killed_by_gate":
                o.row(2, f"B2.step0.{sp}", "note",
                      f"{lab}: cell killed by the step-0 gate; output set aside, not archived")
                continue
            if st != "complete" or quiet or lab not in rel or rel[lab].get("F0") is None:
                o.row(2, f"B2.step0.{sp}", "note", f"{lab}: status {S(st)}; no recompute")
                continue
            Fsp = self.c1.sp_full(sp, block=2)["F_eV"]
            F0 = rel[lab]["F0"]
            dd = (F0 - Fsp) * 1000.0
            o.row(2, f"B2.step0.{sp}.F", "F", f"F(SP {sp}) = {fe(Fsp)} eV; F(k = 0) of {lab} = {fe(F0)} eV",
                  values={"F_sp_eV": Fsp, "F_k0_eV": F0})
            o.row(2, f"B2.step0.{sp}.dF", "note", f"F(k = 0) − F(SP) = {fm(dd)} meV ({full(dd)})",
                  values={"dF_meV": dd})
            ok = isinstance(ps, bool) and (abs(dd) <= STEP0_MEV) == ps and (outc == "pass") == ps and close(dd, dF)
            o.xc(2, "XC-FRSTEP0", ok, f"{sp}: |ΔF| ≤ {STEP0_MEV} is {abs(dd) <= STEP0_MEV}; recorded passed "
                                      f"{S(ps)}, decision {S(outc)}; ΔF against the recorded dF_meV {resid(dd, dF)}")
        if fr.get("no_error"):                           # integration (IX-2): fr/STEP0_NO_ERROR (S2B:274-275)
            o.row(2, "B2.step0.no_error", "note", f"fr_step0{fr['s0_ran'][-1]}: final, no writer or input error found "
                  f"(fr/state_end.json fr_step0: outcome fail_final, no_error_found True; fr/STEP0_NO_ERROR, W 50 "
                  f"preconditions); the gate files keep attempt 1's decision fail_pending_fix")
        if fr.get("no_error_stop"):                      # IX-4: fr/STEP0_NO_ERROR, then a final STOP (no state_end)
            o.row(2, "B2.step0.no_error", "note", f"fr_step0{fr['s0_ran'][-1]}: final, no writer or input error found "
                  f"(fr/campaign.json fr_outcome at the STOP: {eg.FR_OUTCOMES[3]}, recorded by W 50 begin_stop; "
                  f"fr/STEP0_NO_ERROR, W 50 preconditions); the gate files keep attempt 1's decision fail_pending_fix")
        if fr.get("s0_set_aside"):                       # R-1: a final STOP while the repeat of @4 is prepared
            o.row(2, "B2.step0.s2_m30_Cs188o0_vac", "note", "fr_step0@4: set aside for its repeat (fr/gates/"
                  "fr_step0.json and the @4 trio moved aside, W 50:2725-2760); s2r_m30_Cs188o0_vac was not evaluated "
                  "again before the final STOP")
        # 2.3 quartet values
        o.line(" 2.3 Quartet values (FA188)")
        d = fr["dec"]
        incomplete = [lab for lab in FR_ORDER if cells[lab]["status"] != "complete" or
                      (lab in rel and rel[lab].get("F0") is None)]
        vals = None
        if quiet:
            o.row(2, "B2.quartet", "note", "not recomputed in the hinge run")
        elif incomplete:
            first = incomplete[0]                                             # OP-29: the not-run variant
            fst = cells[first]["status"]
            kind = "not started" if fst is FILE_ABSENT else ("no configuration" if fst == "complete" else S(fst))
            labels = (("L_FR1", L_FR1(kind, first, None)),)
            o.row(2, "B2.quartet", "note", L_NOTFORMED("quartet incomplete: " + ", ".join(
                f"{lab} " + ("not started" if cells[lab]["status"] is FILE_ABSENT else "no configuration" if
                             cells[lab]["status"] == "complete" else S(cells[lab]["status"]))
                for lab in incomplete)), labels=labels)
        else:
            q = {role_of(lab): rel[lab] for lab in FR_ORDER}
            a1 = eb({k: r["F0"] for k, r in q.items()})
            a2 = eb({k: r["Ffin"] for k, r in q.items()})
            dl = a2 - a1
            vals = {"A1": a1, "A2": a2, "delta": dl}
            labs = ()
            if d is not None and d.get("FR1") is False:
                cell, kind = d.get("cell"), d.get("kind")
                if kind == "check":
                    det = checks_str(cells.get(cell, {}).get("validity_final.failed", ABSENT))
                elif kind == "end_rule":
                    det = S(cells.get(cell, {}).get("end_rule.outcome", ABSENT))
                else:
                    det = None
                labs = (("L_FR1", L_FR1(kind, cell, det)),)
            elif d is not None and d.get("FR1") is True and d.get("FR2") is False:
                labs = ("L_FR2",)
            elif d is None and fr["status"] == "stopped":     # fix round 2: all four complete, no gate FR
                labs = ("L_FRNOTEVAL",)
            o.row(2, "B2.EbA1", "Eb_A1", f"E_b^A1(FA188) from k = 0 = {fm(a1)} meV", values={"Eb_A1_meV": a1},
                  labels=labs)
            o.row(2, "B2.EbA2", "Eb_A2", f"E_b^A2(FA188) = {fm(a2)} meV", values={"Eb_A2_meV": a2},
                  labels=labs + (("L_FRSTOP",) if self.frstop_pass((d or {}).get("outcome")) else ()))   # IX-12
            o.row(2, "B2.delta", "delta", f"δ_far(FA188) = E_b^A2 − E_b^A1 = {fm(dl)} meV", values={"delta_meV": dl},
                  labels=labs, has_a1=True)
        self.v["FA188"] = vals
        # 2.4 cross-checks
        o.line(" 2.4 Cross-checks")
        frg = fr["frg"]
        if d is None:
            o.xc(2, "XC-FR2", None, "gate FR not evaluated (" + ("step-0 final" if eg.FR_OUTCOMES[3] in
                                                                (fr.get("outcome"), fr.get("stop_rec")) else
                                                                "fr stopped") + ")")
            o.xc(2, "XC-FR1-DEC", None, "gate FR not evaluated")
        else:
            if quiet:                                    # the hinge run forms no FA188 value (fix round 1)
                for xid in ("XC-FR2", "XC-FR2-DEC", "XC-DSUM-FR"):
                    o.xc(2, xid, None, "not recomputed in the hinge run")
            elif d.get("FR2") is None:
                o.xc(2, "XC-FR2", None, "gate FR recorded no FR-2 values (FR-1 failed)")
                o.xc(2, "XC-FR2-DEC", None, "FR-2 not evaluated (FR-1 failed)")       # RF-22
            elif vals is None:
                o.xc(2, "XC-FR2", False, "gate FR recorded FR-2 values but the quartet is not formed")
            else:
                stop_a2 = ("L_FRSTOP",) if self.frstop_pass(d.get("outcome")) else ()       # IX-12
                for f, g in frg.items():
                    for k, mine in (("Eb_A1_meV", vals["A1"]), ("Eb_A2_meV", vals["A2"]),
                                    ("delta_far_meV", vals["delta"])):
                        rec = g.get(f"result.FR2.{k}")
                        o.xc(2, "XC-FR2", close(mine, rec), f"{k} {fm(mine)} meV against fr/{f} result.FR2.{k} "
                                                           f"{fm(rec) if isinstance(rec, float) else S(rec)} meV, "
                                                           f"{resid(mine, rec)}", has_a1=k != "Eb_A2_meV",
                             labels=stop_a2 if k == "Eb_A2_meV" else ())
                o.xc(2, "XC-FR2-DEC", fr2_pass(vals["delta"]) == d.get("FR2"),
                     f"fr2_pass(δ_far = {fm(vals['delta'])} meV ({full(vals['delta'])})) = {fr2_pass(vals['delta'])} "
                     f"against decision.FR.FR2 {S(d.get('FR2'))}", has_a1=True)
            fr1, cell, kind = fr1_recompute(fr["cells"])
            o.xc(2, "XC-FR1-DEC", (fr1, cell, kind) == (d.get("FR1"), d.get("cell"), d.get("kind")),
                 f"recomputed FR-1 {fr1}, first failure {cell} {kind}; decision.FR.FR1 {S(d.get('FR1'))}, cell "
                 f"{S(d.get('cell'))}, kind {S(d.get('kind'))}")
        if vals is not None:
            q = {role_of(lab): rel[lab] for lab in FR_ORDER}
            dsum = (q["DV"]["relax_meV"] - q["D"]["relax_meV"]) - (q["V"]["relax_meV"] - q["host"]["relax_meV"])
            o.xc(2, "XC-DSUM-FR", close(vals["delta"], dsum),
                 f"δ_far(FA188) {fm(vals['delta'])} meV against the signed sum {fm(dsum)} meV, "
                 f"{resid(vals['delta'], dsum)}", has_a1=True)
        # 2.5 invariant-only (OP-8)
        inv = frg["gates/FR.json"].get("result.invariant_only") if frg["gates/FR.json"] is not FILE_ABSENT else None
        self.v["invariant_only"] = inv if isinstance(inv, list) else []
        if frg["gates/FR.json"] is FILE_ABSENT:
            o.row(2, "B2.invariant_only", "note", "check 5 passed only under the identical-atom reading: not evaluated "
                                                 "(gate FR not evaluated)")
        else:
            o.row(2, "B2.invariant_only", "note", "check 5 passed only under the identical-atom reading: " +
                  (", ".join(inv) if isinstance(inv, list) and inv else "none"))

    # ------------------------------------------------------------ block 3 (spec section 12)
    def block3(self, o, *, quiet=False):
        au, T, m48 = self.au, self.T, self.ex.m48
        au.set_block(3)
        o.line("BLOCK 3. MACE and deferred-C1 block (Pb136 cells excluded; see block 5)")
        o.line(self.header)
        o.line(" 3.1 MACE records (155; class order, then work id)")
        n_leaves, per_ok = 0, True
        for e in self.ledger:
            o.row(3, f"B3.rec.{e['wid']}", "note", f"{e['wid']} {e['class']} valid {e['valid']} failed {e['failed']}")
            for p, val in e["mace"]:
                o.row(3, f"B3.mace.{e['wid']}.{p}", "E_mace", f"{p} E_mace_eV = {fe(val)} eV",
                      values={"E_mace_eV": val}, indent="    ")
            n_leaves += len(e["mace"])
            per_ok &= len(e["mace"]) == (4 if e["class"] == "host" else 1)
        o.xc(3, "XC-MACE-COUNT", n_leaves == eg.MACE_LEAVES_BLOCK3 and per_ok and len(self.ledger) == 155,
             f"{len(self.ledger)} records, {n_leaves} leaves (expected 155 and {eg.MACE_LEAVES_BLOCK3}: 4 per host "
             f"record, 1 per other record)")
        o.row(3, "B3.deferred", "note", "deferred to block 5 (Pb136): " + ", ".join(eg.PB136_WIDS))
        # 3.2 zero-shot MACE E_b
        o.line(" 3.2 Zero-shot MACE E_b")
        gN = er.read_json(self.L.gate("c1", "N"))
        noise = {}
        o.line("  noise pilot (40 quartets)")
        for p in eg.PILOTS:
            for Ls in "BAX":
                for f in eg.FAR4[p][Ls]:
                    for d in eg.TOKENS_OF[Ls]:
                        q = m48.quartet_a1(T, p, d, f)
                        em = m48._mace_eb(T["hosts"][p], q["labels"])
                        a1 = q["Eb_meV"]
                        noise[(p, d, f)] = a1
                        txt = (f"{p} {d}{f}: Eb_mace = {fm(em) if em is not None else L_NOTFORMED('MACE leg missing')} "
                               f"meV; Eb_A1 = " + (f"{fm(a1)} meV" if a1 is not None else
                                                   L_NOTFORMED("; ".join(q["reasons"]))) +
                               (f"; Eb_mace − Eb_A1 = {fm(em - a1)} meV" if em is not None and a1 is not None
                                else ""))
                        o.row(3, f"B3.noise.{p}.{d}{f}", "Eb_mace", txt, values={"Eb_mace_meV": em, "Eb_A1_meV": a1},
                              has_a1=True, indent="    ")
                        rec = ((((gN.get("result") or {}).get("dopants") or {}).get(d) or {}).get("hosts") or {}) \
                            .get(p, {}).get("per_site_meV", {}).get(str(f), ABSENT)
                        ok = (rec is None and a1 is None) or close(a1, rec)
                        rs_ = resid(a1, rec) if a1 is not None else "both none" if rec is None else "-"
                        o.xc(3, "XC-GATEN", ok, f"{p} {d}{f} Eb_A1 against c1/gates/N.json per_site_meV "
                                                f"{fm(rec) if isinstance(rec, float) else S(rec)}, {rs_}",
                             indent="      ", has_a1=True)
        self.v["noise"] = noise
        mp = m48._mace_pilot(T)
        cal = mp["calibration"]
        o.line("  start set (DFT column: no A1 DFT value in block 3; C4b k = 0 in block 4 where C4b ran)")
        for p in eg.PILOTS:
            for key, rr in (cal.get(p) or {}).items():
                if key in ("Sr136", "Ca136") and p == "m30":
                    raise EIntegrity("INT-PB136-REC", "block 3", f"calibration {key}")
                em = rr["Eb_mace_meV"]
                o.row(3, f"B3.start.{p}.{key}", "Eb_mace", f"{p} {key}: Eb_mace = "
                      f"{fm(em) if em is not None else L_NOTFORMED('MACE leg missing')} meV; DFT",
                      values={"Eb_mace_meV": em}, labels=("L_NOA1",), indent="    ")
        o.line("  pose pilot (m30)")
        for key in ("Cs128", "Cs188", "Cl138", "Cl175"):
            rr = (mp["pose_pilot"] or {}).get(key)
            if rr is None:
                raise EIntegrity("INT-STRUCT", "c1/pairs", f"pose pilot {key}")
            tok, j = key[:2], int(key[2:])
            dft = noise.get(("m30", tok, j)) if j in eg.FAR4["m30"][eg.SUBLATTICE[tok]] else None
            ct = rr["count_term_meV"]
            txt = (f"m30 {key}: Eb_mace_default = {fm(rr['Eb_mace_default_meV'])} meV; Eb_mace_aggregate = " +
                   (fm(rr["Eb_mace_aggregate_meV"]) + " meV" if rr["Eb_mace_aggregate_meV"] is not None else
                    L_NOTFORMED("no kept minimum")) + f"; N_D {rr['N_D']}, N_DV {rr['N_DV']}; count term " +
                   (fm(ct) + " meV" if ct is not None else "none"))
            if dft is not None:
                o.row(3, f"B3.pose.{key}", "Eb_mace", txt + f"; DFT Eb_A1 (noise pilot, o0) = {fm(dft)} meV",
                      values={"Eb_mace_default_meV": rr["Eb_mace_default_meV"],
                              "Eb_mace_aggregate_meV": rr["Eb_mace_aggregate_meV"], "Eb_A1_meV": dft},
                      has_a1=True, indent="    ")
            else:
                o.row(3, f"B3.pose.{key}", "Eb_mace", txt + "; DFT", values={"Eb_mace_default_meV":
                                                                            rr["Eb_mace_default_meV"],
                                                                            "Eb_mace_aggregate_meV":
                                                                            rr["Eb_mace_aggregate_meV"]},
                      labels=("L_NOA1",), indent="    ")
        # 3.3 the q = 0 link rows (P section 10; OP-28)
        o.line(" 3.3 q = 0 link rows (P §10; not at Pb136)")
        H = T["hosts"]["m30"]
        Fh = H["F"]
        census = set(self.c1.sp_stems)
        for lab, why in (("s2_m30_VX138", "Cl138 q = +1"), ("s2_m30_VA128", "Cs128, GA128 q = +1"),
                         ("s2_m30_GA128o0_novac", "GA128 q = 0")):   # fix round 2: before the rows are formed
            self.chk.require(lab not in census, "INT-C1-CENSUS", "c1/raw", f"{lab} ({why} not formable)")
        host = Fh["s2_m30_host"]
        for key, (Ls, j, d) in (("Sr76", ("B", 76, "Sr")), ("Cl138", ("X", 138, "Cl")), ("Cs128", ("A", 128, "Cs")),
                                ("GA128", ("A", 128, "GA"))):
            v0, dv0 = f"s2_m30_V{Ls}{j}_q0", f"s2_m30_{d}{j}o0_vac_q0"
            dl, v1, dv1 = f"s2_m30_{d}{j}o0_novac", f"s2_m30_V{Ls}{j}", f"s2_m30_{d}{j}o0_vac"
            e0 = e1 = None
            if dl in census and v0 in census and dv0 in census:
                e0 = eb({"DV": Fh[dv0], "D": Fh[dl], "V": Fh[v0], "host": host})
                o.row(3, f"B3.q0.{key}", "Eb_q0", f"m30 {key}: E_b(q = 0) = {fm(e0)} meV", values={"Eb_q0_meV": e0},
                      labels=("L_Q0",), indent="    ")
            else:
                o.row(3, f"B3.q0.{key}", "note", f"m30 {key}: E_b(q = 0): " + L["L_NOFORM_C1"], indent="    ")
            if dl in census and v1 in census and dv1 in census:
                e1 = eb({"DV": Fh[dv1], "D": Fh[dl], "V": Fh[v1], "host": host})
                o.row(3, f"B3.q1.{key}", "Eb_q1", f"m30 {key}: E_b(q = +1) = {fm(e1)} meV", values={"Eb_q1_meV": e1},
                      labels=("L_Q0",), indent="    ")
            else:
                o.row(3, f"B3.q1.{key}", "note", f"m30 {key}: E_b(q = +1): " + L["L_NOFORM_C1"], indent="    ")
            if e0 is not None and e1 is not None:
                o.row(3, f"B3.q01.{key}", "Eb_q1", f"m30 {key}: E_b(q = +1) − E_b(q = 0) = {fm(e1 - e0)} meV",
                      values={"diff_meV": e1 - e0}, labels=("L_Q0",), indent="    ")
        # 3.4 determinism (P section 5)
        o.line(" 3.4 Determinism (P §5)")
        wp1 = self.env.wp1_dir or os.path.join(self.ex.tmp, "results/objective2/dopant_shell/wp1_production")
        for fn in ("shell_m30.json", "shell_m05.json", "v2prod_structures.tar.gz"):
            if not os.path.isfile(os.path.join(wp1, fn)):
                raise EIntegrity("INT-STRUCT", f"wp1_production/{fn}", "absent")
        det = m48._determinism(T["hosts"], lambda c: self.L.cdir(c), wp1_dir=wp1)
        for p in eg.PILOTS:                                                   # RF-11: the members it read
            self.au.log_member(os.path.join(wp1, "v2prod_structures.tar.gz"), f"v2prod/{p}_host_relaxed.extxyz")
            self.au.log_member(self.L.structures("c1"), f"cells/s2_{p}_host/relaxed.extxyz")
        self.v["determinism"] = det
        for p in eg.PILOTS:
            r = det[p]
            okv = all(r.get(k) is not None for k in ("E_S2_mace_eV", "E_WP1_eV", "dE_meV", "max_dr_A"))
            shown = {k: (f(r[k]) if r.get(k) is not None else "none") for k, f in
                     (("E_S2_mace_eV", fe), ("E_WP1_eV", fe), ("dE_meV", fm), ("max_dr_A", fa))}
            o.row(3, f"B3.det.{p}", "determinism", f"{p}: E_S2_mace_eV = {shown['E_S2_mace_eV']} eV; E_WP1_eV = "
                  f"{shown['E_WP1_eV']} eV; dE = {shown['dE_meV']} meV; max_dr = {shown['max_dr_A']} Å",
                  values=dict(r), indent="    ")
            o.xc(3, "XC-DETERMINISM", okv, f"{p}: every determinism value formed", indent="    ")
        # 3.5 residual forces (amendment item 1; OP-1, OP-2)
        o.line(" 3.5 DFT residual forces of every A1 cell (eV/Å; Pb136 cells: deferred to block 5)")
        for lab in sorted(eg.BLOCK3_SP):
            h = re.match(r"s2_(m\d\d)_", lab).group(1)
            fo = T["hosts"][h]["forces"][lab]
            a_, fr_ = fo["all"], fo["free"]
            o.row(3, f"B3.forces.{lab}", "forces", f"{lab}: all rms {ff(a_['rms_eVA'])} max {ff(a_['max_eVA'])} n "
                  f"{a_['n']}; free rms {ff(fr_['rms_eVA'])} max {ff(fr_['max_eVA'])} n {fr_['n']}",
                  values={"all": a_, "free": {k: fr_[k] for k in ("rms_eVA", "max_eVA", "n")}}, indent="    ")
            ids, ns = fr_["indices"], fr_["norms_eVA"]
            for i0 in range(0, len(ids), 10):
                o.row(3, f"B3.forces.{lab}.{i0}", "forces", "free norms: " + " ".join(
                    f"{i}:{ff(n)}" for i, n in zip(ids[i0:i0 + 10], ns[i0:i0 + 10])), indent="      ")
        o.row(3, "B3.forces.pb136", "note", "Pb136 single points (" + ", ".join(eg.PB136_SP) + "): deferred to block 5")
        # 3.6 the invalid-cell table
        o.line(" 3.6 Invalid cells (campaign host wid dopant site leg failed)")
        n_c1 = 0
        for w in self.c1.wids:
            rb = self.c1.blind(w)
            val = rb.get("validity") or {}
            if val.get("valid") is not True:
                Ls, j = rb.get("sublattice"), rb.get("site")
                o.row(3, f"B3.inv.c1.{w}", "invalid", f"c1 {rb.get('member')} {w} {rb.get('token') or '—'} "
                      f"{(str(Ls) + str(j)) if Ls and j is not None else '—'} {rb.get('leg') or '—'} "
                      f"{val.get('failed')}", indent="    ")
                n_c1 += 1
        for n in sorted(os.listdir(self.L.cdir("c1", "pairs"))):
            m = re.fullmatch(r"(m\d\d)_(Sr|Ca|Cl|Cs|GA)(\d+)p(\d+)\.json", n)
            if m:
                r = er.read_json(os.path.join(self.L.cdir("c1", "pairs"), n))
                if r.get("status") == "rejected":
                    o.row(3, f"B3.inv.pair.{n}", "invalid", f"c1 {m.group(1)} pair {n[:-5]} pair rejected "
                          f"({(r.get('rejection') or {}).get('exception')})", indent="    ")
                    n_c1 += 1
        if not n_c1:
            o.row(3, "B3.inv.c1", "invalid", "c1: none", indent="    ")
        n_c2 = 0
        for lab in HINGE + FAR:
            lv = self.v["hinge_counts"][lab] if lab in HINGE else self.v["far"][lab]["leaves"]
            if lv.get("validity_final.valid", ABSENT) is False:
                c = er.a2_cell(lab)
                o.row(3, f"B3.inv.c2.{lab}", "invalid",
                      f"c2 {c['pilot']} {lab} {c['token'] or '—'} {c['L']}{c['site']} "
                      f"{c['leg'] if c['kind'] in ('D', 'DV') else '—'} {S(lv.get('validity_final.failed', ABSENT))}",
                      indent="    ")
                n_c2 += 1
        if not n_c2:
            o.row(3, "B3.inv.c2", "invalid", "c2: none", indent="    ")
        n_fr = 0
        for lab in FR_ORDER:
            cc = self.fr["cells"][lab]
            st = cc["status"]
            if st is FILE_ABSENT:
                continue
            vf = cc.get("validity_final.valid", ABSENT)
            if st != "complete" or cc.get("end_rule.outcome") not in eg.END_ACCEPTED or vf is not True:
                c = er.a2_cell(lab)                      # RF-4: an absent final-geometry check is invalid too
                why = "final-geometry check not evaluated" if st == "complete" and vf is ABSENT else \
                    f"failed {S(cc.get('validity_final.failed', ABSENT))}"
                o.row(3, f"B3.inv.fr.{lab}", "invalid",
                      f"fr {c['pilot']} {lab} {c['token'] or '—'} {c['L']}{c['site']} "
                      f"{c['leg'] if c['kind'] in ('D', 'DV') else '—'} status {st}; end rule "
                      f"{S(cc.get('end_rule.outcome', ABSENT))}; {why} "
                      f"(check5_reading {S(cc.get('validity_final.check5_reading', ABSENT))}; as written "
                      f"{S(cc.get('validity_final.failed_as_written', ABSENT))})", indent="    ")
                n_fr += 1
        if not n_fr:
            o.row(3, "B3.inv.fr", "invalid", "fr: none", indent="    ")
        # 3.7 C1 pilot items of P section 15. ER2-1: gate N's sigma_far and the pose gate's a_pose, delta_near and
        # delta_far are spreads or differences of A1 E_b, so their rows and cross-checks carry the item-4 label
        o.line(" 3.7 C1 pilot items (P §15)")
        dop = (gN.get("result") or {}).get("dopants") or {}
        for d in ("Sr", "Ca", "Cl", "Cs", "GA"):
            r = dop.get(d) or {}
            o.row(3, f"B3.gateN.{d}", "note", f"gate N {d}: sigma_far_meV {fmr(r.get('sigma_far_meV'))}, df "
                  f"{r.get('df')}, pass {r.get('pass')}", values={k: r.get(k) for k in ("sigma_far_meV", "df", "pass")},
                  indent="    ", has_a1=True)                       # fix round 2: 0.01 meV (S2B:633); ER2-1
            num, df = [], 0
            for p in eg.PILOTS:
                ok_ = [noise[(p, d, f)] for Ls in "BAX" if d in eg.TOKENS_OF[Ls] for f in eg.FAR4[p][Ls]
                       if noise.get((p, d, f)) is not None]
                if len(ok_) >= 2:
                    mu = math.fsum(ok_) / len(ok_)
                    num += [(x - mu) ** 2 for x in ok_]
                    df += len(ok_) - 1
            sig = math.sqrt(math.fsum(num) / df) if df > 0 else None
            rs = r.get("sigma_far_meV")
            ok = r.get("df") == df and ((sig is None and rs is None) or close(sig, rs)) and \
                r.get("pass") == (df >= 3 and sig is not None and sig <= 25.0)
            o.xc(3, "XC-GATEN-SIGMA", ok, f"gate N {d}: recomputed sigma_far {fmr(sig)}, df {df}; recorded "
                                          f"{fmr(rs)}, df {r.get('df')}, {resid(sig, rs)}", indent="      ",
                 has_a1=True)                                             # ER2-1
        gp = er.read_json(self.L.gate("c1", "pose"))
        for tok in ("Cs", "Cl"):
            r = (gp.get("result") or {}).get(tok) or {}
            txt = (f"pose {tok}: mode {r.get('mode')}, a_pose_meV {fmr(r.get('a_pose_meV'))}, delta_near_meV "
                   f"{fmr(r.get('delta_near_meV'))}, delta_far_meV {fmr(r.get('delta_far_meV'))}")   # fix round 2
            for side in ("near", "far"):
                s = r.get(side) or {}
                txt += (f"; {side} N_D {s.get('N_D')}, N_DV {s.get('N_DV')}, count_term_meV "
                        f"{fmr(s.get('count_term_meV'))}")
            o.row(3, f"B3.pose.gate.{tok}", "note", txt, indent="    ", has_a1=True,      # ER2-1
                  values={k: r.get(k) for k in ("a_pose_meV", "delta_near_meV", "delta_far_meV")})
            mine = self.pose_recompute(tok)
            ok = mine["mode"] == r.get("mode") and close(mine["a_pose_meV"], r.get("a_pose_meV"))
            for k in ("delta_near_meV", "delta_far_meV"):
                ok &= (mine[k] is None and r.get(k) is None) or close(mine[k], r.get(k))
            for side in ("near", "far"):
                s = r.get(side) or {}
                ok &= mine[side]["N_D"] == s.get("N_D") and mine[side]["N_DV"] == s.get("N_DV") and \
                    ((mine[side]["count_term_meV"] is None and s.get("count_term_meV") is None) or
                     close(mine[side]["count_term_meV"], s.get("count_term_meV")))
            o.xc(3, "XC-POSE", ok, f"pose {tok}: recomputed mode {mine['mode']}, a_pose {fmr(mine['a_pose_meV'])}, "
                                   f"delta_near {fmr(mine['delta_near_meV'])}, delta_far {fmr(mine['delta_far_meV'])}",
                 indent="      ", has_a1=True)                            # ER2-1
        gt = er.read_json(self.L.gate("c1", "throughput"))
        rt = gt.get("result") or {}
        o.row(3, "B3.throughput", "note", f"throughput: rate_config_per_node_h {rt.get('rate_config_per_node_h')}, "
              f"choice {rt.get('choice')}", indent="    ")

    def pose_recompute(self, tok):
        """XC-POSE (spec 12.7): Delta_pose from the kept minima's single points in E's own code (P section 9)."""
        near, far = eg.POSE_SITES[tok]
        H = self.T["hosts"]["m30"]
        out = {}
        for side, j in (("near", near), ("far", far)):
            st, why = {}, False
            for leg in eg.LEGS:
                r = er.read_json(self.L.distinct("m30", tok, j, leg))
                kept = r.get("map") or {}
                st[leg] = {o: H["F"].get(f"s2_m30_{tok}{j}{o}_{leg}") for o in sorted(kept)}
                p0 = f"s2_m30_{tok}{j}p0_{leg}"
                v = (self.c1.blind(p0).get("validity") or {}).get("valid") is True if p0 in self.c1.wids else False
                if not (v and kept.get("o0") == "p0") or any(x is None for x in st[leg].values()):
                    why = True
            nD, nDV = len(st["novac"]), len(st["vac"])
            rec = {"N_D": nD, "N_DV": nDV, "count_term_meV": 25.7 * math.log(nD / nDV) if nD and nDV else None,
                   "delta": None}
            if not why:
                gap = {leg: (st[leg]["o0"] - (min(st[leg].values()) + boltzmann_gap_meV(list(st[leg].values())) /
                                              1000.0)) * 1000.0 for leg in eg.LEGS}
                rec["delta"] = gap["vac"] - gap["novac"]
            out[side] = rec
        dn, dfa = out["near"]["delta"], out["far"]["delta"]                 # per site, as P section 9
        if dn is None or dfa is None or not (abs(dn) <= 10.0 and abs(dfa) <= 10.0):
            mode, ap = "multi", 0.0
        else:
            mode, ap = "default", max(abs(dn), abs(dfa), abs(dn - dfa))
        return {"mode": mode, "a_pose_meV": ap, "delta_near_meV": dn, "delta_far_meV": dfa,
                "near": out["near"], "far": out["far"]}

    # ------------------------------------------------------------ blocks 4 and 5 (spec sections 13, 14)
    def block4_and_5(self):
        rid = self.route["id"]
        b4 = self.b4
        o4 = Out(self.item4, self.xcs)
        fr_info = {"decision": self.fr.get("dec"), "FA188": self.v.get("FA188"),
                   "invariant_only": self.v.get("invariant_only"), "header": self.header}
        res = tbl = None
        if self.mode == "evaluation" and rid not in ("FR-FAIL", "FR-STOP"):
            self.au.set_block(4)
            tbl = b4.build_tier_table(self, self.c1, fr_info)
            res = b4.evaluate_tier(tbl, fr_info)
        self.stage = "block 5"
        if self.mode == "hinge":
            trig = {"held": None, "df_delta": None, "reason": "deferred hinge run"}
        else:
            trig = hinge_trigger(rid, b4, self)
        self.trigger = trig
        o5 = Out(self.item4, self.xcs)
        if self.mode == "hinge" or trig["held"]:
            self.block5(o5, trig)
            if res is not None:
                self.stage = "block 4"
                res = b4.evaluate_tier(tbl, fr_info, hinge=hinge_delta(self.v))
        else:
            n = trig["df_delta"]
            o5.line(f"{NOT_OPENED}. df_δ counted from validity leaves (Sr's C2 hinge quartet counted valid): "
                    f"{n if n is not None else L_NOTFORMED(trig['reason'])}; trigger df_δ ≥ 3: not held.")
            o5.line("Deferred, unread: relaxations 1-4 (s2r_m30_VB136, s2r_m30_hostB136, s2r_m30_Sr136o0_novac, "
                    "s2r_m30_Sr136o0_vac); E_b^A1(Pb136), E_b^A2(Pb136), δ_Sr,m30; F of s2_m30_VB136 and "
                    "s2_m30_Sr136o0_vac; the Pb136 q = 0 rows; the WP2c comparison at Pb136; E_mace_eV of the five "
                    "Pb136 records; the zero-shot MACE E_b of Sr and Ca at Pb136; the DFT residual forces of the "
                    "Pb136 single points (amendment item 1). Read by E_hinge_output.txt at the "
                    "first of: the evaluation of a later pre-registration that names it as data, in rules committed "
                    "before 2027-06-30; 2027-06-30.")
        if self.mode == "evaluation":
            if res is None:
                o4.line(f"BLOCK 4. Tier block: not printed ({self.route['reason']})")
            else:
                self.stage = "block 4"
                o4.line("BLOCK 4. Tier block (S2B §7 item 4; e_block4.py)")
                o4.line(self.header)
                clause = L_A1TIER_CLAUSE if self.v.get("invariant_only") else ""
                labels = {"L_A1TIER": L["L_A1TIER"].format(clause=clause)}
                for r in b4.rows(res, labels):
                    o4.rows.append(r)
                    o4.lines.append("  " + r.text + ("  -- " + "; ".join(labels.get(x, L.get(x, x)) for x in r.labels)
                                                       if r.labels else ""))
            self.outs[4] = o4
        self.outs[5] = o5

    def block5(self, o, trig):
        au, c1 = self.au, self.c1
        au.open_hinge(); c1.open_hinge(); au.set_block(5)
        self.hinge_open = True
        o.line("BLOCK 5. Hinge block: relaxations 1-4 (m30, Pb136) and the Pb136 C1 items")
        o.line(self.header)
        if self.mode == "hinge":
            o.line("  deferred hinge run (S2B:714-719): block 5 in hinge mode")
        else:
            o.line(f"  df_δ counted from validity leaves (Sr's C2 hinge quartet counted valid): {trig['df_delta']}; "
                   f"trigger df_δ ≥ 3: held. trigger held: block 5 opened")
        k3 = self.read_k3("hinge")
        rel = {}
        o.line(" 5.1 Per relaxation")
        for i, lab in enumerate(HINGE, 1):
            r = er.read_relaxation(self.ctx, "c2", lab, mode="hinge", kind="a2_hinge", tail_ks=[TAIL_K[lab]], block=5)
            self.require_complete(r, "c2")
            self.chk.require(TAIL_K[lab] == r["k_last"] - er.TAIL_BACK, "INT-STRUCT", f"c2/raw/{lab}.a2.json",
                             "TAIL_K = k_last - 36")
            rel[lab] = r
            self.print_relax(o, 5, r, number=i, c2const=C2_RESULT[lab], tails=[TAIL_K[lab]], quartet="Pb136")
        q = {role_of(lab): rel[lab] for lab in HINGE}
        a1 = eb({k: r["F0"] for k, r in q.items()})
        a2 = eb({k: r["Ffin"] for k, r in q.items()})
        d = a2 - a1
        self.v["Pb136"] = {"A1": a1, "A2": a2, "delta": d}
        o.line(" 5.2 The quartet and gate values")
        o.row(5, "B5.EbA1", "Eb_A1", f"E_b^A1(Pb136) from k = 0 = {fm(a1)} meV", values={"Eb_A1_meV": a1})
        o.row(5, "B5.EbA2", "Eb_A2", f"E_b^A2(Pb136) = {fm(a2)} meV", values={"Eb_A2_meV": a2})
        o.row(5, "B5.delta", "delta", f"δ_Sr,m30 = E_b^A2 − E_b^A1 = {fm(d)} meV", values={"delta_meV": d},
              has_a1=True)
        s0 = {f: self.load("c2", f, "hinge", "step0_c2") for f in
              ("gates/step0.json", f"gates_applied/{eg.C2_S0_1}.gate.json", f"gates_applied/{eg.C2_S0_4}.gate.json")}
        for f, g in s0.items():
            self.present(g, f"c2/{f}")
        for sp, lab, f in (("s2_m30_VB136", "s2r_m30_VB136", f"gates_applied/{eg.C2_S0_1}.gate.json"),
                           ("s2_m30_Sr136o0_vac", "s2r_m30_Sr136o0_vac", f"gates_applied/{eg.C2_S0_4}.gate.json")):
            Fsp = c1.sp_full(sp, block=5)["F_eV"]
            F0 = rel[lab]["F0"]
            dd = (F0 - Fsp) * 1000.0
            dF, ps = s0[f].get(f"result.cells.{sp}.dF_meV"), s0[f].get(f"result.cells.{sp}.passed")
            outc = s0[f].get("decision.step0.outcome")
            dFs = fm(dF) if isinstance(dF, float) else S(dF)
            o.row(5, f"B5.step0.{sp}.gate", "note", f"c2/{f} {sp}: dF_meV = {dFs} meV, passed {S(ps)}, "
                  f"decision.step0.outcome {S(outc)} -- {STEP0_GATE}")
            o.row(5, f"B5.step0.{sp}", "F", f"F(SP {sp}) = {fe(Fsp)} eV; F(k = 0) of {lab} = {fe(F0)} eV; "
                  f"F(k = 0) − F(SP) = {fm(dd)} meV ({full(dd)})", values={"F_sp_eV": Fsp, "dF_meV": dd})
            ok = isinstance(ps, bool) and (abs(dd) <= STEP0_MEV) == ps and (outc == "pass") == ps and close(dd, dF)
            o.xc(5, "XC-STEP0-C2", ok, f"{sp}: |ΔF| ≤ {STEP0_MEV} is {abs(dd) <= STEP0_MEV}; recorded passed "
                                       f"{S(ps)}, decision.step0.outcome {S(outc)}; {resid(dd, dF)}")
        if "Pb76" not in self.v:
            raise EIntegrity("INT-STRUCT", "block 1", "E_b^A2(Pb76)")
        hd = a2 - self.v["Pb76"]["A2"]
        o.row(5, "B5.hingediff", "Eb_A2", f"E_b^A2(Pb136) − E_b^A2(Pb76) = {fm(hd)} meV", values={"diff_meV": hd},
              labels=("L_HINGE_DIFF",))
        T, rows5 = er.extend_c1_table_hinge(self.T, self.ledger, c1, rel)
        H = T["hosts"]["m30"]
        Fh = H["F"]
        o.line(" 5.3 Pb136 comparisons and MACE")
        e0 = eb({"DV": Fh["s2_m30_Sr136o0_vac_q0"], "D": rel["s2r_m30_Sr136o0_novac"]["F0"], "V": Fh["s2_m30_VB136_q0"],
                 "host": Fh["s2_m30_host"]})
        e1 = eb({"DV": Fh["s2_m30_Sr136o0_vac"], "D": rel["s2r_m30_Sr136o0_novac"]["F0"], "V": Fh["s2_m30_VB136"],
                 "host": Fh["s2_m30_host"]})
        o.row(5, "B5.q0.Sr136", "Eb_q0", f"m30 Sr136: E_b(q = 0) = {fm(e0)} meV (D from k = 0 of "
              f"s2r_m30_Sr136o0_novac)", values={"Eb_q0_meV": e0}, labels=("L_Q0",))
        o.row(5, "B5.q1.Sr136", "Eb_q1", f"m30 Sr136: E_b(q = +1) = {fm(e1)} meV; E_b(q = +1) − E_b(q = 0) = "
              f"{fm(e1 - e0)} meV", values={"Eb_q1_meV": e1}, labels=("L_Q0",))
        o.row(5, "B5.q0.Ca136", "note", "m30 Ca136: E_b(q = 0): " + L["L_CA_Q0"])
        wpf = os.path.join(self.ex.tmp, "results/objective2/dopant_shell/wp2c/wp2cde_dft.json")
        if not os.path.isfile(wpf):
            raise EIntegrity("INT-STRUCT", "wp2c/wp2cde_dft.json", "absent")
        wp = (self.ex.m48._wp2c_values() or {}).get("m30_Sr136")
        wps = "none" if not isinstance(wp, dict) else ", ".join(f"{k} {fmr(wp.get(k))}" for k in
                                                                ("Eb_dft_meV", "Eb_dft_farref_meV"))   # fix round 2
        o.row(5, "B5.wp2c", "note", f"WP2c m30 Sr136: {wps}; beside E_b^A1(Pb136) {fm(a1)} meV and E_b^A2(Pb136) "
              f"{fm(a2)} meV", labels=("L_WP2C",), has_a1=True,
              values=dict(wp) if isinstance(wp, dict) else {})
        n = 0
        for e in rows5:
            o.row(5, f"B5.rec.{e['wid']}", "note", f"{e['wid']} pb136 valid {e['valid']} failed {e['failed']}")
            for p, val in e["mace"]:
                o.row(5, f"B5.mace.{e['wid']}.{p}", "E_mace", f"{p} E_mace_eV = {fe(val)} eV",
                      values={"E_mace_eV": val}, indent="    ")
                n += 1
        o.xc(5, "XC-MACE-COUNT", n == 5 and len(rows5) == 5, f"{len(rows5)} Pb136 records, {n} leaves (expected 5)")
        cal = self.ex.m48._mace_pilot(T)["calibration"].get("m30") or {}
        sr, ca = cal.get("Sr136") or {}, cal.get("Ca136") or {}
        em = sr.get("Eb_mace_meV")
        o.row(5, "B5.mace.Sr136", "Eb_mace", f"m30 Sr136: Eb_mace = {fm(em) if em is not None else 'none'} meV; beside "
              f"E_b^A1(Pb136) = {fm(a1)} meV", values={"Eb_mace_meV": em, "Eb_A1_meV": a1}, has_a1=True)
        o.xc(5, "XC-MACEPILOT-A1", close(sr.get("Eb_A1_dft_meV"), a1),
             f"_mace_pilot Eb_A1_dft_meV against E_b^A1(Pb136), {resid(sr.get('Eb_A1_dft_meV'), a1)}", has_a1=True)
        emc = ca.get("Eb_mace_meV")
        o.row(5, "B5.mace.Ca136", "Eb_mace", f"m30 Ca136: Eb_mace = {fm(emc) if emc is not None else 'none'} meV",
              values={"Eb_mace_meV": emc}, labels=("L_CA_MACE",))
        o.line(" 5.4 DFT residual forces of the Pb136 single points (amendment item 1)")
        for lab in eg.PB136_SP:
            fo = H["forces"][lab]
            a_, fr_ = fo["all"], fo["free"]
            o.row(5, f"B5.forces.{lab}", "forces", f"{lab}: all rms {ff(a_['rms_eVA'])} max {ff(a_['max_eVA'])} n "
                  f"{a_['n']}; free rms {ff(fr_['rms_eVA'])} max {ff(fr_['max_eVA'])} n {fr_['n']}")
            for i0 in range(0, len(fr_["indices"]), 10):
                o.row(5, f"B5.forces.{lab}.{i0}", "forces", "free norms: " + " ".join(
                    f"{i}:{ff(x)}" for i, x in zip(fr_["indices"][i0:i0 + 10], fr_["norms_eVA"][i0:i0 + 10])),
                    indent="      ")
        o.line(" 5.5 Cross-checks")
        for f, g in k3.items():
            hv = g.get("result.Eb_A2_meV.hinge")
            o.xc(5, "XC-K3HINGE", close(a2, hv), f"E_b^A2(Pb136) {fm(a2)} meV against c2/{f} result.Eb_A2_meV.hinge "
                                                f"{fm(hv) if isinstance(hv, float) else S(hv)} meV, {resid(a2, hv)}")
        dsum = (q["DV"]["relax_meV"] - q["D"]["relax_meV"]) - (q["V"]["relax_meV"] - q["host"]["relax_meV"])
        o.xc(5, "XC-DSUM-HINGE", close(d, dsum), f"δ_Sr,m30 {fm(d)} meV against the signed sum {fm(dsum)} meV, "
                                                 f"{resid(d, dsum)}", has_a1=True)

    # ------------------------------------------------------------ the exit audit (spec 6.2 phase 1 item 8)
    def exit_audit(self):
        au, c1 = self.au, self.c1
        er.assert_no_c3(self.L, at="exit")
        self.chk.passed["INT-ROOT"] += 1
        calc_check(self.cd, "INT-CALC-EXIT")
        self.chk.passed["INT-CALC-EXIT"] += 1
        c1.assert_closed("exit")
        self.chk.passed["INT-PB136-REC"] += 1
        self.chk.passed["INT-PB136-RAW"] += 1
        if not self.hinge_open:
            bad = au.hinge_closed()
            if bad:
                raise EIntegrity("INT-HINGE-CLOSED", bad[0][0], bad[0][1])
            self.chk.passed["INT-HINGE-CLOSED"] += 1
        a2_ok = set(FAR) | set(self.v.get("fr_rel") or {}) | (set(HINGE) if self.hinge_open else set())
        sp_ok = set(eg.BLOCK3_SP) | (set(eg.PB136_SP) if self.hinge_open else set())
        self.ctx.reads.check_labels(a2_ok, sp_ok)
        self.chk.passed["INT-READS"] += 1
        er.assert_one_47(self.ex.q47)
        self.chk.passed["INT-IMPORT"] += 1
        au.stop()                                                             # the re-reads below are unhooked
        bad = au.stable()
        if bad:
            raise EIntegrity("INT-SHA-STABLE", bad[0], "sha256 changed since first open")
        self.chk.passed["INT-SHA-STABLE"] += len(au.log)
        self.int_sha()

    def int_sha(self):
        """RF-11, OP-17: every logged file against its one reference class."""
        g, au = self.git, self.au
        trees, used = {}, set()

        def tree(c, prefix):
            if (c, prefix) not in trees:
                trees[(c, prefix)] = g.ls_tree(c, prefix)
            return trees[(c, prefix)]
        for rp, cl in au.classify().items():
            e = au.log[rp]
            if cl is None:
                raise EIntegrity("INT-SHA", e["rel"], "no reference class (RF-11)")
            kind, key = cl
            if kind == "exempt":
                continue
            blob, sha = git_blob_of_file(rp)
            if sha != e["sha256"]:
                raise EIntegrity("INT-SHA-STABLE", e["rel"], "sha256")
            if kind == "archive":
                c = self.archive_commit(key)
                want = tree(c, f"{self.root_rel}/{key}").get(f"{self.root_rel}/{e['rel']}")
                used.add(key)
            elif kind == "head":
                want = tree("HEAD", f"{self.root_rel}/{e['rel']}").get(f"{self.root_rel}/{e['rel']}")
            elif kind == "8bff03e":
                want = self.ex.blobs.get(e["rel"])
            elif kind == "manifest":
                man = self.b4.manifest(self, key)
                if man.get(e["rel"]) != e["sha256"]:
                    raise EIntegrity("INT-SHA", e["rel"], f"{key}/MANIFEST.sha256")
                self.chk.passed["INT-SHA"] += 1
                continue
            else:
                raise EIntegrity("INT-SHA", e["rel"], f"class {kind}")
            if want is None or want != blob:
                raise EIntegrity("INT-SHA", e["rel"], f"git blob of the {kind} reference")
            self.chk.passed["INT-SHA"] += 1
        for c in sorted(used):
            if not g.diff_quiet(self.archive_commit(c), "HEAD", [f"{self.root_rel}/{c}"]):
                raise EIntegrity("INT-SHA", f"{c}/", "archive changed since its archive commit")

    def archive_commit(self, c):
        if c in self.env.archive_commit:
            return self.env.archive_commit[c]
        if c == "fr":
            if self.archive_fr is None:
                add = self.git.added(f"{self.root_rel}/fr/campaign.json")
                if len(add) != 1:
                    raise EIntegrity("INT-SHA", "fr/campaign.json", "no unique archive commit")
                self.archive_fr = add[0][0]
            return self.archive_fr
        raise EIntegrity("INT-SHA", f"{c}/", "no archive commit")

    # ------------------------------------------------------------ assembly and phase 2 (spec 6.2, section 9; RF-8)
    def assemble(self, rc):
        lines = list(self.pre)
        lines += ["", self.header, "", "INTEGRITY"]
        for i in eg.INT_IDS:
            n = self.chk.passed.get(i, 0)
            lines.append(f"  {i} ok ({n})" if n else f"  {i}: not applicable on this route")
        order = (1, 2, 3, 4, 5) if self.mode == "evaluation" else (5,)
        for b in order:
            if b in self.outs:
                lines.append("")
                lines += self.outs[b].lines
                self.rows += self.outs[b].rows
        if self.mode == "hinge":
            for b in (1, 2, 3):
                self.rows += self.outs[b].rows
            # fix round 2: every failed cross-check of blocks 1-3 counts in the summary and the exit code, so it is
            # printed with its values and residual (S2B:739-740: nothing suppressed); the passing rows are not
            bad = [r for b in (1, 2, 3) for r in self.outs[b].rows if r.kind == "xcheck" and "L_XFAIL" in r.labels]
            lines += ["", "CROSS-CHECKS OF BLOCKS 1-3 (recomputed in memory for the header, the Pb76 value and the C1 "
                          "table): every failed row, printed in full (S2B:739-740)"]
            lines += [r.line for r in bad] if bad else ["  none failed"]
        lines += ["", "COVERAGE (P §10, §15; S2B:711-712)"]
        lines += ["  " + x for x in self.coverage()]
        lines += ["", "CROSS-CHECKS"]
        cnt = collections.OrderedDict()
        for xid, ok in self.xcs:
            c = cnt.setdefault(xid, [0, 0, 0])
            c[0 if ok is True else 1 if ok is False else 2] += 1
        for xid, (a, b, c) in cnt.items():
            lines.append(f"  {xid}: {a} ok, {b} " + ("cross-check failed" if b else "failed") + f", {c} not evaluated")
        lines += ["", "READS (scripts/47 counters, by key)"]
        tot = self.ctx.reads.totals if getattr(self, "ctx", None) else {}
        lines.append("  " + ", ".join(f"{k} {tot[k]}" for k in sorted(tot)))
        lines.append(f"  A2 labels read: {', '.join(sorted(self.ctx.reads.labels['a2']))}")
        lines.append(f"  SP labels read: {len(self.ctx.reads.labels['sp'])}")
        lines += ["", "APPENDIX A. git diff C2 -> S2B_LAST -- scripts/46-50"] + ["  " + x for x in self.appendix]
        lines += ["", "END", f"E exit code: {rc}"]
        return "\n".join(lines) + "\n"

    def coverage(self):
        """Spec 12.8: every item of P section 10 and P section 15 (P:788-820) once, with its block and row or
        reason."""
        fr_fail = self.route["id"] in ("FR-FAIL", "FR-STOP")
        b5 = "block 5" if self.hinge_open else "deferred to block 5"
        noc3 = "not formed (FR failed: no C3b)" if fr_fail else "block 4"
        noc4 = L["L_C4BNOTRUN"] if fr_fail else "block 4"
        items = (("P10 q = 0 Sr76", "block 3, B3.q0.Sr76"), ("P10 q = 0 Cl138", "block 3, B3.q0.Cl138"),
                 ("P10 q = 0 Cs128", "block 3, B3.q0.Cs128"), ("P10 q = 0 GA128", "block 3, B3.q0.GA128"),
                 ("P10 q = 0 Sr136", b5 + (", B5.q0.Sr136" if self.hinge_open else "")),
                 ("P10 q = 0 Ca136", b5 + (", B5.q0.Ca136" if self.hinge_open else "")),
                 ("P15 per-site e_h(j), E_d(j), G_d, raw E_b, far-site values", noc3),
                 ("P15 shared-region sensitivity", noc4),
                 ("P15 invalid cells (C1, C2, FR)", "block 3, B3.inv"),
                 ("P15 invalid cells (C3b, C4b)", noc3),
                 ("P15 plateau-excluded intervals", noc4),
                 ("P15 zero-shot MACE E_b, pilot cells", "block 3, B3.noise, B3.start, B3.pose"),
                 ("P15 zero-shot MACE E_b, production quartets", noc3),
                 ("P15 zero-shot MACE E_b, Pb136", b5 + (", B5.mace" if self.hinge_open else "")),
                 ("P15 DFT residual forces, A1 cells outside Pb136", "block 3, B3.forces"),
                 ("P15 DFT residual forces, Pb136", b5 + (", B5.forces" if self.hinge_open else "")),
                 ("P15 DFT residual forces, C3b", noc3),
                 ("P15 per A2 cell, C2 relaxations 5-8", "block 1, B1"),
                 ("P15 per A2 cell, FR", "block 2, B2"),
                 ("P15 per A2 cell, C2 relaxations 1-4", b5 + (", B5" if self.hinge_open else "")),
                 ("P15 per A2 cell, C4b", noc4),
                 ("P15 WP2c at Pb136 (m30, Sr)", b5 + (", B5.wp2c" if self.hinge_open else "")),
                 ("P15 WP2c at FA128 (m30, GA)", noc4), ("P15 WP2c at Pb124 (m05, Sr)", noc4),
                 ("P15 D3(BJ)", "withdrawn (D3BJ_AMENDMENT.md; sensitivity study after E)"),
                 ("P15 required hosts", noc3), ("P15 pose-pilot spreads", "block 3, B3.pose.gate"),
                 ("P15 noise-pilot per-site values", "block 3, B3.noise"),
                 ("P15 determinism (P §5)", "block 3, B3.det"), ("P15 throughput row", "block 3, B3.throughput"))
        self.coverage_items = items
        return [f"{a}: {b}" for a, b in items]

    def failure_lines(self, what):
        lines = list(self.pre) + ["", what]
        if self.mode == "evaluation" and self.attempt == 2 and self.attempt1_exit == 3:
            lines += [""] + self.fallback()
        lines += ["", "END", "E exit code: 3"]
        return "\n".join(lines) + "\n"

    def fallback(self):
        """S2B:730-734 (item 7; spec section 16): the gate-recorded values by leaf name through the guard. ER2-3: each
        also carries the labels blocks 1-2 attach to the same value (L_FAR on .far; L_FR2 on the FR-2 values when
        gate FR records the FR-2 failure), after L_FALLBACK."""
        out = ["FALLBACK (S2B §7, item 7): E failed twice."]
        lab = L["L_FALLBACK"]
        hinge_done = False
        au = eg.OpenAudit.current()
        own = None
        try:
            if au is None:
                own = au = eg.OpenAudit(self.root, private_root=self.env.private_root).start()
            for f in ("gates/K3.json", "gates_applied/gate_K3.gate.json"):
                g = eg.eg_load(self.L, "c2", f, mode="far", kind="k3", audit=au)
                v = g.get("result.Eb_A2_meV.far") if g is not FILE_ABSENT else ABSENT
                out.append(f"  c2/{f} result.Eb_A2_meV.far = {fm(v) if isinstance(v, float) else S(v)} meV -- {lab}; "
                           f"{L['L_FAR']}")                             # ER2-3: as B1.EbA2
            g = eg.eg_load(self.L, "fr", "gates/FR.json", mode="fr", kind="fr_gate", audit=au)
            if g is FILE_ABSENT:
                out.append("  fr/gates/FR.json: none recorded (gate FR not evaluated)")
            elif g.get("decision.FR.FR2") is None:
                out.append(f"  fr/gates/FR.json result.FR2: none recorded (FR-1 failed) -- {lab}")
            else:                                        # RF-25: the A1 value and the difference carry item 4
                # IX-4: on FR-STOP a pass recorded before the STOP is 'FR fails' (S2B §1): item 4 is L_ITEM4
                i4 = L["L_FRVALID" if g.get("decision.FR.outcome") == "pass" and
                       (self.route or {}).get("id") != "FR-STOP" else "L_ITEM4"]
                # ER2-3: the FR-2 failure as gate FR records it (scripts/49: outcome 'fail', part 'FR-2'), or as block
                # 2 reads it (FR1 True, FR2 False): L_FR2 on all three values, as on B2.EbA1, B2.EbA2 and B2.delta
                fr2 = (g.get("decision.FR.outcome") == "fail" and g.get("decision.FR.part") == "FR-2") or \
                    (g.get("decision.FR.FR1") is True and g.get("decision.FR.FR2") is False)
                # IX-12: on FR-STOP after a gate FR pass the value without the item-4 label carries L_FRSTOP
                stop_a2 = f"; {L['L_FRSTOP']}" if self.frstop_pass(g.get("decision.FR.outcome")) else ""
                for k in ("Eb_A1_meV", "Eb_A2_meV", "delta_far_meV"):
                    v = g.get(f"result.FR2.{k}")
                    out.append(f"  fr/gates/FR.json result.FR2.{k} = {fm(v) if isinstance(v, float) else S(v)} meV -- "
                               f"{lab}" + (f"; {i4}" if k != "Eb_A2_meV" else stop_a2) +
                               (f"; {L['L_FR2']}" if fr2 else ""))
            rid = (self.route or {}).get("id")
            if rid == "C4B-ENDED":
                trig = hinge_trigger(rid, self.b4, self)
                if trig["held"]:
                    au.open_hinge()
                    g = eg.eg_load(self.L, "c2", "gates/K3.json", mode="hinge", kind="k3", audit=au)
                    v = g.get("result.Eb_A2_meV.hinge")
                    out.append(f"  c2/gates/K3.json result.Eb_A2_meV.hinge = "
                               f"{fm(v) if isinstance(v, float) else S(v)} meV -- {lab}")
                    hinge_done = True
        except Exception as e:
            out.append(f"  fallback stopped: {type(e).__name__}")
        finally:
            if own is not None:
                own.stop()
        out.append(f"  every other part-c value, and the tier: {L['L_NOTREAD']}")
        if not hinge_done:
            out.append(f"{NOT_OPENED} (the trigger was not held or could not be evaluated)")
        return out

    def fail(self, what):
        """A failure before output (exit 3): the failure report (and, on attempt 2 after attempt 1 failed, the
        item-7 fallback); no CSV."""
        text = self.failure_lines(what)
        if self.au is not None:
            self.au.stop()
        try:
            self.write_excl(self.attempt_path, text)
        except FileExistsError:
            return self.refuse(EError("the attempt file appeared during the run (O_EXCL)"))
        except OSError as e:                             # fix round 2 (RF-8): ENOSPC, EIO, ...; the partial removed
            return self.refuse(EError(f"the attempt file could not be written ({type(e).__name__}); its partial "
                                      f"file removed, nothing written (RF-8)"))
        if self.env.echo:
            sys.stdout.write(text)
        self.result_text, self.rc = text, 3
        return 3

    def write_excl(self, path, text):
        """The attempt file with O_EXCL (RF-8). Fix round 2: a failed write removes the partial file it created and
        re-raises (the 'write' hook plants such a failure in the self-test, D9)."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        try:
            data, off = text.encode(), 0
            if "write" in self.env.hooks:
                self.env.hooks["write"](fd, path)
            while off < len(data):
                off += os.write(fd, data[off:])
            os.fsync(fd)
        except BaseException:
            os.close(fd)
            os.remove(path)
            raise
        os.close(fd)
        self.written.append(path)

    def csv_texts(self, text):
        cols = ("block", "campaign", "order", "label", "quartet", "role", "k", "part", "dF_meV", "k_last",
                "restart_start", "tail_k")
        b = io.StringIO()
        w = csv.DictWriter(b, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        drawn = set()
        for r in self.csv_rows:
            if self.mode == "hinge" and r["block"] != 5:
                continue
            w.writerow(r)
            drawn.add(r["label"])
        m = io.StringIO()
        mw = csv.writer(m, lineterminator="\n")
        mw.writerow(("key", "value"))
        for k, v in (("header", self.header), ("e_output", os.path.basename(self.attempt_path)), ("e_head", self.head),
                     ("attempt", self.attempt), ("mode", self.mode)):
            mw.writerow((k, v))
        for lab, o in sorted((self.v.get("end_rules") or {}).items()):
            if lab in drawn:                           # only the relaxations of this CSV (the hinge run recomputes
                mw.writerow((f"end_rule.{lab}", S(o)))  # block 1 in memory; its labels are not in the hinge CSV)
        if self.mode == "evaluation":                  # panel b lists the FR cells without a curve (spec 17)
            for lab in FR_ORDER:
                mw.writerow((f"status.{lab}", (self.v.get("fr_status") or {}).get(lab, "absent")))
        return b.getvalue(), m.getvalue()

    def phase2(self, rc):
        self.stage = "assembly"
        try:
            text = self.assemble(rc)
            csvs = self.csv_texts(text)
        except Exception as e:
            return self.fail(exc_line("assembly", e))
        if "before_write" in self.env.hooks:
            self.env.hooks["before_write"](self)
        linked = []
        try:
            for path, body in zip(self.csv_paths, csvs):                      # RF-8: CSVs first, by link
                os.makedirs(os.path.dirname(path), exist_ok=True)
                fd, tmp = tempfile.mkstemp(prefix=".e_tmp_", dir=os.path.dirname(path))
                try:
                    os.write(fd, body.encode()); os.fsync(fd)
                finally:
                    os.close(fd)
                try:
                    if "link" in self.env.hooks:
                        self.env.hooks["link"](tmp, path)
                    else:
                        os.link(tmp, path)
                    linked.append(path)
                finally:
                    os.remove(tmp)
        except OSError as e:
            for p in linked:
                os.remove(p)
            return self.fail(f"FAILED: stage phase 2 (figure source data): {type(e).__name__}")
        try:
            self.write_excl(self.attempt_path, text)
        except FileExistsError:
            for p in linked:
                os.remove(p)
            return self.refuse(EError("the attempt file appeared during the run (O_EXCL): nothing written"))
        except OSError as e:                             # fix round 2 (RF-8): the CSVs removed, the failure report
            for p in linked:                             # written if it can be (else a refusal, nothing written)
                os.remove(p)
            return self.fail(f"FAILED: stage phase 2 (attempt file): {type(e).__name__}")
        self.written += linked
        if self.env.echo:
            sys.stdout.write(text)
        self.result_text, self.rc = text, rc
        return rc


# ---------------------------------------------------------------- command line (spec section 1)
def parser():
    ap = argparse.ArgumentParser(description="E, the one evaluation of S2b (S2B_PLAN.md section 7)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test", action="store_true")
    g.add_argument("--run", action="store_true")
    g.add_argument("--hinge", action="store_true")
    ap.add_argument("--root", default=S2_REL)
    ap.add_argument("--private-root", default=None)
    ap.add_argument("--stop-note", default=None)
    ap.add_argument("--rerun-cause", default=None)
    ap.add_argument("--amendment", default=None)
    ap.add_argument("--item7-amendment", default=None)
    ap.add_argument("--hinge-cause", choices=("prereg", "backstop"), default=None)
    ap.add_argument("--prereg", default=None)
    ap.add_argument("--prereg-eval", default=None)
    return ap


def execute(argv, env=None):
    """One run of E; returns the Run (rc, result_text, rows, written). env: None in run mode (this checkout)."""
    a = parser().parse_args(argv)
    if a.self_test:
        raise EError("execute() runs --run or --hinge; --self-test goes through main()")
    if env is None:
        root = a.root if os.path.isabs(a.root) else os.path.join(REPO, a.root)
        pr = None if a.private_root is None else (a.private_root if os.path.isabs(a.private_root) else
                                                  os.path.join(REPO, a.private_root))
        env = Env(repo=REPO, root=root, private_root=pr)
    r = Run(a, env)
    r.rc = r.main()
    return r


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--self-test" in argv:
        if len(argv) != 1:
            print("--self-test takes no other argument", file=sys.stderr)
            return 2
        return _sibling("e_selftest").run()
    return execute(argv).rc


if __name__ == "__main__":
    sys.exit(_sibling("e_eval").main())

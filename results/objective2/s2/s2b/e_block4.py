#!/usr/bin/env python
"""Block 4 of E, the one evaluation of S2b: the tier block (results/objective2/s2/S2B_PLAN.md section 7, "Blocks",
item 4; E_IMPLEMENTATION_SPEC section 13; amendment 2026-11-16a). It is committed, with its self-tests (e_selftest.py
group T), in the c3b campaign commit, before any c3b value exists (S2B:532-533, 960-961).

What it does. From the private c3b archive it forms the A1 tier of P section 14: per production host and dopant the
quartets E_b,h(j) (P:140), the valid quartets and hosts (P:678-682, check 5 read invariantly, S2B:330-332), the
far-referenced values e_h(j), Y_h and Delta_h (P:143-146, 766), per dopant Ybar_d, s_Y,d, I^A1_d, U_d, the class of
rule V with the A1-tier controls (P:725-730, 739-781), the heterogeneity flag (P:750-756), the ranking over the 6
pairs of the 4 dopants (P:782-785; S2B:576), the required hosts, the zero-shot MACE E_b and the residual forces (P
section 15), the check-5 reading counts (S2B:331) and the far-bias sensitivity (S2B:685-687). The statistics come from
the scripts/48 and scripts/49 functions at 8bff03e that S2B:564-568 names; the composition is restated here from
scripts/48 _evaluate [48:640-747] for the dopants (Sr, Cl, Cs, GA), without Ca (S2B:575; amendment 2026-11-16a B-6).

C4b is not run in S2b (amendment 2026-11-16a, D-0). That decision is held in ONE place, the constants C4B_RUN,
C4B_ORIGIN and C4B_ITEM below: every C4b item of S2B section 7 is printed with C4B_ITEM, a c4b tree is refused, the
calibrated tier is not formed and the hinge block stays blind.

Routes admitted at this commit (spec section 13 ids): C4B-NOTRUN (C3b done, an A1 tier computable: n_d >= 2 for at
least one of Cl, Cs, GA), C3B-NOTIER (C3b done, no A1 tier computable: the P section 15 items, no interval, class or
ranking) and C3B-STOP (a final STOP in c3b, shown by the committed stop note; printed as C3B-NOTIER).

Interface (called by e_eval.py only on routes past FR):
  tier_route(run)                    -> {"id", "c3b", "c4b", "commits", "verify", ...}; admission only (EGuarded
                                         leaves and committed notes; before E's imports)
  c4b_df_delta_validity(run)         -> refused: C4b is not run
  build_tier_table(run, c1, fr)      -> an s2-evaltable-1-shaped production table of the c3b hosts
  evaluate_tier(table, fr, *, hinge=None) -> the A1 tier (hinge must be None: no calibrated tier)
  rows(result, labels)               -> the rows of block 4
  manifest(run, c)                   -> {private-root-relative path: sha256} of the c3b archive (INT-SHA, RF-11)

Blinding. Energies of c3b are read here only, in block 4, through e_guard.C3bAccess and the ReadsAudit.

    (imported by e_eval.py; self-tests: e_selftest.py group T)
"""
import hashlib, importlib.util, itertools, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _sibling(name):
    """A helper module of this directory, one object per process (RF-19; e_guard._load_shared)."""
    key = f"_s2b_{name}"
    m = sys.modules.get(key)
    if m is None:
        p = os.path.join(HERE, f"{name}.py")
        s = importlib.util.spec_from_file_location(key, p)
        m = importlib.util.module_from_spec(s)
        sys.modules[key] = m
        try:
            s.loader.exec_module(m)
        except BaseException:
            del sys.modules[key]
            raise
    return m


eg = _sibling("e_guard")
EError, EIntegrity, Blinded, ABSENT, FILE_ABSENT = eg.EError, eg.EIntegrity, eg.Blinded, eg.ABSENT, eg.FILE_ABSENT

BLOCK4_IMPLEMENTED = True
DOPANTS = ("Sr", "Cl", "Cs", "GA")                   # spec 13: no Ca in any pool or ranking
DECISIVE = ("Cl", "Cs", "GA")
ROUTES = ("C3B-STOP", "C3B-NOTIER", "C4B-NOTRUN", "C4B-STOP", "C4B-ENDED")

# ---------------------------------------------------------------- D-0 (amendment 2026-11-16a): the one place
C4B_RUN = False                                      # C4b is not run in S2b, by decision
C4B_ORIGIN = "decision (S2B amendment 2026-11-16a)"  # the runner's s2b_projection.c4b_origin
C4B_ITEM = "C4b not run (decision, amendment 2026-11-16a)"   # printed wherever S2B section 7 calls for a C4b item
ROUTES_ADMITTED = ("C3B-STOP", "C3B-NOTIER", "C4B-NOTRUN")   # no route with a C4b campaign at this commit
C4B_NAME = re.compile(r"c4b([._-].*)?", re.I)        # every form of a c4b tree: c4b, c4b.tar.gz, C4B_old ... (as the
#                                                      c3 lock of spec section 3); refused under both roots and in c3b

# ---------------------------------------------------------------- the plan's literals
S2_REL = "results/objective2/s2"
C3B_NOTE = f"{S2_REL}/C3B_NOTE.md"                   # the committed c3b note (its fixed manifest line below)
C3B_STOP_NOTE = f"{S2_REL}/C3B_STOP_NOTE.md"         # the one stop note of a final STOP in c3b (B-3)
VERIFY_C3B = f"{S2_REL}/c3b_verify/verify_c3b.txt"   # S2B:522; B-14
MANIFEST_NAME = "MANIFEST.sha256"
MANIFEST_LINE = re.compile(r"^c3b/MANIFEST\.sha256 sha256: ([0-9a-f]{64})$", re.M)
STOP_PHRASE = re.compile(r"the c3b STOP is final")
ISO_DATE = re.compile(r"\b(20\d\d)-(\d\d)-(\d\d)\b")
HEX40 = re.compile(r"[0-9a-f]{40}")
N_HOSTS = 8                                           # S2B:324 (the C1 n rule)
PROD8 = ("m06", "m02", "m16", "m12", "m32", "m26", "m22", "m23")          # P:214, draw order
SUBLATTICE = {"Sr": "B", "Cl": "X", "Cs": "A", "GA": "A"}
LEGS = ("novac", "vac")
FIRST = {"B": (124, 136), "A": (28, 92, 128), "X": (49, 53, 90, 102, 125, 126, 137, 138)}     # P:259-266
FAR = {                                               # (f1, f2), f1 the farthest: P:283-290 (B-5)
    "m06": {"B": (76, 172), "A": (200, 164), "X": (175, 222)},
    "m02": {"B": (76, 172), "A": (188, 152), "X": (175, 186)},
    "m16": {"B": (76, 172), "A": (164, 188), "X": (175, 222)},
    "m12": {"B": (76, 172), "A": (68, 200), "X": (175, 222)},
    "m32": {"B": (76, 172), "A": (200, 188), "X": (175, 222)},
    "m26": {"B": (76, 172), "A": (68, 164), "X": (175, 222)},
    "m22": {"B": (76, 172), "A": (16, 4), "X": (175, 186)},
    "m23": {"B": (172, 76), "A": (200, 4), "X": (175, 186)},
}
VALID_HOST_MIN = {"B": 2, "A": 2, "X": 6}             # P:680-682
LABEL_GATE_N = "inconclusive below the DFT noise floor"                   # scripts/48 LABEL_GATE_N
LABEL_DOPANT_SPECIFIC = "first shell not stable under the S2 protocol"    # scripts/48 LABEL_DOPANT_SPECIFIC
TOL_MEV = 1e-6

# the fixed strings of block 4 (amendment 2026-11-16a lists them verbatim); L_A1TIER comes from e_eval.py
LABELS = {
    "L_DOPANT_Sr": "B far pair (Pb76, Pb172) untested at A2 (Pb76 invalid)",                   # S2B:165
    "L_DOPANT_Cl": "X far pair (I175, I186) untested at A2",                                   # S2B:166
    "L_DOPANT_GA": "A f₁ (FA188) tested with Cs only; f₂ (FA164) untested",                    # S2B:167
    "L_DOPANT_Cs": "A f₂ (FA164) untested",                                                    # S2B:168
    "L_SENS": "sensitive to the far bias at FA188 (one quartet, Cs, A site; reported only)",   # S2B:686-687
    "L_NOTIER": "no A1 tier computable; reported only; no class",                              # B-1
    "L_C3BSTOP": "no A1 tier (final STOP in c3b; S2B section 1); reported only; no class",     # B-3
    "L_C3B_INV": "check 5 passed only under the identical-atom reading at a C3b cell of this value (S2B section 3)",
    "L_C4B": C4B_ITEM,
}
TITLES = (" 4.0 Route, archive and counts", " 4.1 Invalid cells and the two readings of check 5 (C3b)",
          " 4.2 Per host: raw E_b, far-site values, e_h(j), Y_h, Δ_h and the zero-shot MACE E_b (meV)",
          " 4.3 Per dopant: Ē_d(j), G_d, the A1 tier (P §14) and its controls",
          " 4.4 Ranking at the A1 tier (reported only; P:782-785)",
          " 4.5 Far-bias sensitivity (reported only; S2B:685-687)",
          " 4.6 DFT residual forces of the C3b A1 cells (eV/Å)", " 4.7 C4b items (S2B §7 item 4)",
          " 4.8 Cross-checks")
C4B_ITEMS = ("per-relaxation items of every C4b relaxation", "invalid cells of C4b", "C4b δ",
             "WP2c comparison at FA128 (m30, GA)", "WP2c comparison at Pb124 (m05, Sr)",
             "q = 0 link rows completed by the C4b k = 0 F (GA at FA128; the q = +1 comparators at FA128 and I138)",
             "start-set A1 E_b from the C4b k = 0 F beside the zero-shot MACE E_b",
             "calibrated tier and validated classes", "far-bias sensitivity at the calibrated tier",
             "shared-region sensitivity (P:792-796)", "plateau-excluded intervals", "ranking at the calibrated tier")


def cells_of(h):
    """The 68 cells of one production host (S2B:328-329): (work id, kind, single-point label, L, site, dopant, leg)."""
    yield (f"s2_{h}_host", "host", f"s2_{h}_host", None, None, None, None)
    for L in "BAX":
        for j in FIRST[L] + FAR[h][L]:
            yield (f"s2_{h}_V{L}{j}", "V", f"s2_{h}_V{L}{j}", L, j, None, "vac")
    for d in DOPANTS:
        L = SUBLATTICE[d]
        for j in FIRST[L] + FAR[h][L]:
            for leg in LEGS:
                yield (f"s2_{h}_{d}{j}p0_{leg}", "D" if leg == "novac" else "DV", f"s2_{h}_{d}{j}o0_{leg}", L, j, d,
                       leg)


PAIR_NAME = re.compile(r"(m\d\d)_(Sr|Cl|Cs|GA)(0|[1-9]\d*)(?:p0\.json|_(?:novac|vac)\.distinct\.json)")   # default pose
REGION_NAME = re.compile(r"(m\d\d)_([BAX])(0|[1-9]\d*)\.json")
ALL_CELLS = {h: tuple(cells_of(h)) for h in PROD8}
ALL_WIDS = frozenset(c[0] for h in PROD8 for c in ALL_CELLS[h])
ALL_LABELS = frozenset(c[2] for h in PROD8 for c in ALL_CELLS[h])
assert all(len(v) == 68 for v in ALL_CELLS.values()) and len(ALL_WIDS) == len(ALL_LABELS) == 544
assert all(len(set(FIRST[L]) | set(FAR[h][L])) == len(FIRST[L]) + 2 for h in PROD8 for L in "BAX")


class Row:
    """One printed item of block 4, in the shape of e_eval.Row (block, id, kind, values, label ids, text)."""
    __slots__ = ("block", "id", "kind", "values", "labels", "text", "has_a1", "line")

    def __init__(self, rid, kind, text, values=None, labels=(), has_a1=False):
        self.block, self.id, self.kind, self.text = 4, rid, kind, text
        self.values, self.labels, self.has_a1, self.line = dict(values or {}), tuple(labels), bool(has_a1), None


def fm(x):
    return "%.2f" % x                                     # meV (S2B:633; B-17)


def f6(x):
    return "%.6f" % x                                     # t, nu, eV, eV/A


def _rel(run, path):
    """A repository path under S2_REL, moved to the run's root (as e_eval verify_records does)."""
    rr = getattr(run, "root_rel", S2_REL)
    return path if rr == S2_REL else path.replace(S2_REL, rr, 1)


# ---------------------------------------------------------------- admission (spec 6.1, 13; amendment 2026-11-16a)
def tier_route(run):
    """The route past FR, from committed notes and the EGuarded leaves of c3b/campaign.json and c3b/state_end.json
    alone (admission runs before E's imports; every failure is a refusal, exit 2, nothing written)."""
    a, env = run.a, run.env
    if env.private_root is None:
        raise EError("FR passed: the private c3b archive needs --private-root (spec section 1)")
    for base, name, notes in ((run.root, "the public root", True), (env.private_root, "the private root", False)):
        for n in _c4b_entries(base, notes_ok=notes):
            raise EError(f"{name} holds the entry {n}: {C4B_ITEM}; no c4b tree of any form is admitted at this commit")
    cj = run.load("c3b", "campaign.json", "tier", "campaign_c3b")
    if cj is FILE_ABSENT:
        raise EError("FR passed and c3b has not run: none of S2B §7 'When E may run' holds")
    status = cj.get("status")
    if status == "running":
        raise EError("c3b is running: none of S2B §7 'When E may run' holds")
    if status not in ("done", "stopped"):
        raise EError("c3b/campaign.json status is neither done nor stopped: E may not run")
    start, commit = cj.get("start_commit"), cj.get("commit")
    for x, k in ((start, "start_commit"), (commit, "commit")):
        if not (isinstance(x, str) and HEX40.fullmatch(x)):
            raise EError(f"c3b/campaign.json {k} is not a 40-hex commit (spec 7)")
    out = {"c3b": {"status": status, "commit": commit, "start_commit": start, "computable": None, "n_d": None},
           "c4b": {"run": C4B_RUN, "origin": C4B_ORIGIN}, "commits": {"c3b_start": start, "c3b": commit},
           "stop_note": None}
    st = run.load("c3b", "state_end.json", "tier", "state_c3b")
    if st is FILE_ABSENT:                                 # B-12: required when c3b is done. A STOP of the runner
        if status != "stopped":                           # publishes no state file (scripts/50), so a stopped c3b
            #                                               may lack it; a state file that exists is checked below
            raise EError("c3b/state_end.json is absent: E needs the s2b_projection.c4b_run (false) and c4b_origin "
                         "recorded by the c3b campaign when c3b is done (amendment 2026-11-16a, B-12)")
    elif st.get("s2b_projection.c4b_run") is not C4B_RUN or st.get("s2b_projection.c4b_origin") != C4B_ORIGIN:
        raise EError(f"c3b/state_end.json s2b_projection.c4b_run is not false with c4b_origin "
                     f"'{C4B_ORIGIN}': only '{C4B_ITEM}' is admitted at this commit")
    if status == "stopped":
        note = _rel(run, C3B_STOP_NOTE)
        if a.stop_note != note:
            raise EError(f"c3b stopped: a final STOP needs --stop-note {note} (amendment 2026-11-16a, B-3)")
        text = run.note_ok(a.stop_note, what="--stop-note")
        if not (STOP_PHRASE.search(text) and ISO_DATE.search(text)):
            raise EError(f"--stop-note {a.stop_note} is not a dated note stating that the c3b STOP is final (B-3)")
        sr = cj.get("stop_reason")
        out.update(id="C3B-STOP", stop_note=(a.stop_note, hashlib.sha256(text.encode()).hexdigest()))
        out["c3b"]["stop_reason"] = sr if isinstance(sr, str) else None
    else:
        if a.stop_note:
            raise EError(f"--stop-note {a.stop_note} is refused: c3b is done, there is no STOP")
        if st.get("campaigns.c3b") != "done" or st.get("campaign_commit.c3b") != commit:
            raise EError("c3b/state_end.json campaigns.c3b or campaign_commit.c3b disagrees with c3b/campaign.json")
        comp = st.get("c3b_tier.computable")
        nd = {d: st.get(f"c3b_tier.n_d.{d}") for d in DOPANTS}
        if not isinstance(comp, bool) or any(isinstance(v, bool) or not isinstance(v, int) for v in nd.values()):
            raise EError("c3b/state_end.json c3b_tier.computable or c3b_tier.n_d is absent or of the wrong type")
        out["c3b"].update(computable=comp, n_d=nd)
        out["id"] = "C4B-NOTRUN" if comp else "C3B-NOTIER"
    if out["id"] not in ROUTES_ADMITTED:
        raise EError(f"route {out['id']} is not admitted at this commit (amendment 2026-11-16a)")
    vp, np_ = _rel(run, VERIFY_C3B), _rel(run, C3B_NOTE)
    vt = run.note_ok(vp, what="verify record of c3b")     # S2B:522: committed and clean
    nt = run.note_ok(np_, what="the c3b note")
    got = MANIFEST_LINE.findall(nt)
    if len(got) != 1:
        raise EError(f"{np_} does not hold exactly one line 'c3b/{MANIFEST_NAME} sha256: <64 hex>' (B-13)")
    out["manifest_sha256"] = got[0]
    out["verify"] = {"c3b": (vp, hashlib.sha256(vt.encode()).hexdigest())}
    try:                                                  # names and hashes only, no energy: a defect is a refusal
        man = _manifest_read(run, "c3b", got[0])          # here (exit 2, nothing written), never an attempt spent
        out["n_manifest"] = _manifest_complete(run, "c3b", man)       # in block 4 (review M2)
        _census(run)
    except _Names as e:
        raise EError(f"the c3b archive is refused at admission: {e.where}: {e.what}") from None
    run.pre_route.append(f"c3b: status {status}; start commit {start}; commit {commit}")
    run.pre_route.append(f"verify record c3b: {vp} sha256 {out['verify']['c3b'][1]}; last line: "
                         f"{vt.rstrip(chr(10)).split(chr(10))[-1]}")
    run.pre_route.append(f"c3b note: {np_} sha256 {hashlib.sha256(nt.encode()).hexdigest()}; c3b/{MANIFEST_NAME} "
                         f"sha256 {got[0]}")
    if out["stop_note"]:
        run.pre_route.append(f"c3b stop note: {out['stop_note'][0]} sha256 {out['stop_note'][1]}")
    run.pre_route.append(f"C4b: {C4B_ITEM}")
    return out


def c4b_df_delta_validity(run):
    raise EError(f"{C4B_ITEM}: no df_δ is counted at this commit")


# ---------------------------------------------------------------- the private-archive manifest (RF-11; B-13)
def manifest(run, c):
    """{private-root-relative path: sha256} of a private archive: <private_root>/<c>/MANIFEST.sha256, lines
    '<sha256>  <path relative to the campaign directory>', sorted, every file of the campaign but the manifest; its
    own sha256 is the one on the fixed line of the committed c3b note (INT-SHA)."""
    cache = run.__dict__.setdefault("_b4_manifest", {})
    if c in cache:
        return cache[c]
    if c != "c3b":
        raise EIntegrity("INT-SHA", f"{c}/", "no private archive of this campaign is admitted")
    try:
        cache[c] = _manifest_read(run, c, ((run.route or {}).get("b4") or {}).get("manifest_sha256"))
    except _Names as e:
        raise EIntegrity(e.check, e.where, e.what) from None
    return cache[c]


class _Names(Exception):
    """A defect of the private archive found from names and hashes alone. At admission (tier_route) it is a refusal:
    exit 2, nothing written, no attempt spent. Found again in block 4 (the archive changed during the run) it is the
    integrity failure `check` (review M2)."""

    def __init__(self, check, where, what):
        super().__init__(f"{check} {where}: {what}")
        self.check, self.where, self.what = check, where, what


def _c4b_entries(base, *, notes_ok):
    """The entries of a directory whose name is a form of a c4b tree (C4B_NAME; review M5). notes_ok: under the
    public root a regular file ending in .md or .txt is a note, not a tree."""
    out = []
    for n in sorted(os.listdir(base)) if os.path.isdir(base) else []:
        p = os.path.join(base, n)
        note = notes_ok and n.lower().endswith((".md", ".txt")) and os.path.isfile(p) and not os.path.islink(p)
        if C4B_NAME.fullmatch(n) and not note:
            out.append(n)
    return out


def _manifest_read(run, c, want):
    """Parse <private_root>/<c>/MANIFEST.sha256 against the sha256 `want` of the committed c3b note: lines
    '<sha256>  <path>', paths relative to the campaign directory, sorted bytewise by path (each path once), no path
    segment that is a form of a c4b tree. -> {private-root-relative path: sha256}, the manifest itself included."""
    rel = f"{c}/{MANIFEST_NAME}"
    path = run.L.cdir(c, MANIFEST_NAME)
    if not os.path.isfile(path):
        raise _Names("INT-SHA", rel, "absent")
    with open(path, "rb") as fh:
        data = fh.read()
    if want is None or hashlib.sha256(data).hexdigest() != want:
        raise _Names("INT-SHA", rel, "sha256 against the line of the committed c3b note")
    out, prev = {}, None
    try:
        lines = data.decode("utf-8").split("\n")
    except UnicodeDecodeError:
        raise _Names("INT-SHA", rel, "encoding") from None
    if lines and lines[-1] == "":
        lines.pop()
    for ln in lines:
        m = re.fullmatch(r"([0-9a-f]{64})  (\S(?:.*\S)?)", ln)
        p = m.group(2) if m else None
        if p is None or p.startswith("/") or any(s in ("", ".", "..") for s in p.split("/")) or p == MANIFEST_NAME:
            raise _Names("INT-SHA", rel, "line format or path")
        if prev is not None and p.encode("utf-8") <= prev.encode("utf-8"):
            raise _Names("INT-SHA", rel, "order: the lines are sorted bytewise by path, each path once")
        if any(C4B_NAME.fullmatch(s) for s in p.split("/")):
            raise _Names("INT-SHA", f"{c}/{p}", f"a c4b entry in the c3b archive: {C4B_ITEM}")
        out[f"{c}/{p}"], prev = m.group(1), p
    out[rel] = want
    return out


def _manifest_complete(run, c, man):
    """Every file of the campaign directory is in the manifest, every entry exists, and no directory is a form of a
    c4b tree (names only). -> the number of manifest entries."""
    base = run.L.cdir(c)
    on_disk = set()
    for dp, dns, fns in os.walk(base):
        for dn in sorted(dns):
            if C4B_NAME.fullmatch(dn):
                raise _Names("INT-SHA", f"{c}/" + os.path.relpath(os.path.join(dp, dn), base).replace(os.sep, "/"),
                             f"a c4b entry in the c3b archive: {C4B_ITEM}")
        for fn in fns:
            on_disk.add(f"{c}/" + os.path.relpath(os.path.join(dp, fn), base).replace(os.sep, "/"))
    for p in sorted(on_disk ^ set(man)):
        raise _Names("INT-SHA", p, f"{c}/{MANIFEST_NAME}: " + ("not listed" if p in on_disk else "listed, absent"))
    return len(man)


# ---------------------------------------------------------------- the production table (spec 13; S2B:330-332)
def _assert_restated(ex):
    """INT-IMPORT: the literals of this module against the 8bff03e objects (labels, work ids, site rules, strings)."""
    g49, m48 = ex.g49, ex.m48
    pins = (("VALID_HOST_MIN", dict(g49.RULES["VALID_HOST_MIN"]), VALID_HOST_MIN),
            ("FIRST_SHELL_SIZE", dict(g49.RULES["FIRST_SHELL_SIZE"]), {L: len(v) for L, v in FIRST.items()}),
            ("SUBLATTICE", {d: g49.SUBLATTICE[d] for d in DOPANTS}, SUBLATTICE), ("LEGS", tuple(g49.LEGS), LEGS),
            ("PROD8", tuple(m48.PROD8), PROD8), ("N_BASE", g49.RULES["N_BASE"], N_HOSTS),
            ("SITES.first", {L: tuple(m48.SITES[L]["first"]) for L in "BAX"}, FIRST),
            ("LABEL_GATE_N", m48.LABEL_GATE_N, LABEL_GATE_N),
            ("LABEL_DOPANT_SPECIFIC", m48.LABEL_DOPANT_SPECIFIC, LABEL_DOPANT_SPECIFIC),
            ("Q_RANK", g49.RULES["Q_RANK"], 0.9975), ("Q_STAR", g49.RULES["Q_STAR"], 0.99375))
    for name, obj, lit in pins:
        if obj != lit:
            raise EIntegrity("INT-IMPORT", "8bff03e", f"block 4 {name}")
    for h in PROD8:
        for wid, kind, lab, L, j, d, leg in ALL_CELLS[h]:
            if kind == "host":
                ref = (g49.wid_host(h), g49.lab_host(h))
            elif kind == "V":
                ref = (g49.wid_v(h, L, j), g49.lab_v(h, L, j))
            else:
                ref = (g49.wid_dop(h, d, j, leg, 0), g49.lab_dop(h, d, j, leg, 0))
            if ref != (wid, lab):
                raise EIntegrity("INT-IMPORT", "8bff03e", f"block 4 label {lab}")
    return True


def _int_list(x):
    return isinstance(x, list) and all(isinstance(v, int) and not isinstance(v, bool) for v in x)


def _validity(val, kind, where):
    """The validity leaves of a c3b cell record (amendment 2026-11-16a, interface): valid and failed under the
    invariant reading of check 5; for V+, D and D+V+ also check5_reading, valid_as_written, failed_as_written and
    invariant_only, checked for consistency (INT-STRUCT). check5: 'as written' (passes as written), 'invariant only'
    (passes only under the invariant reading), 'failed' (fails under both), None (host), 'not evaluated'."""
    out = {"valid": None, "failed": None, "valid_as_written": None, "failed_as_written": None,
           "check5": None if kind == "host" else "not evaluated"}
    if not isinstance(val, dict) or val.get("valid") is None:
        return out
    valid, failed = val.get("valid"), val.get("failed")
    if not isinstance(valid, bool) or not _int_list(failed) or valid != (not failed):
        raise EIntegrity("INT-STRUCT", where, "validity.valid, validity.failed")
    out.update(valid=valid, failed=list(failed))
    if kind == "host":
        return out
    vw, fw, io = val.get("valid_as_written"), val.get("failed_as_written"), val.get("invariant_only")
    if val.get("check5_reading") != "invariant" or not isinstance(vw, bool) or not _int_list(fw) or \
            not isinstance(io, bool):
        raise EIntegrity("INT-STRUCT", where, "validity.check5_reading, valid_as_written, failed_as_written, "
                                              "invariant_only")
    if vw != (not fw) or io != (valid and not vw) or not set(failed) <= set(fw) or (set(fw) - set(failed)) - {5}:
        raise EIntegrity("INT-STRUCT", where, "the two readings of check 5 are inconsistent")
    out.update(valid_as_written=vw, failed_as_written=list(fw),
               check5="failed" if 5 in failed else "invariant only" if 5 in fw else "as written")
    return out


def _mace_leaf_count(x):
    if isinstance(x, dict):
        return sum(1 if k == "E_mace_eV" else _mace_leaf_count(v) for k, v in x.items())
    if isinstance(x, list):
        return sum(_mace_leaf_count(v) for v in x)
    return 0


def _read_json(path):
    with open(path, "rb") as fh:
        return json.loads(fh.read())


def _c1_gates(run):
    """The public C1 gates that rule V uses: gate N (pass), G1 and the pose gate (mode, a_pose) [48:1137-1144]."""
    gN, gp, g1 = (_read_json(run.L.gate("c1", n)) for n in ("N", "pose", "G1"))
    pose = {t: {"mode": r.get("mode"), "a_pose_meV": r.get("a_pose_meV")}
            for t, r in ((gp.get("result") or {}).items()) if isinstance(r, dict)}
    for t in ("Cs", "Cl"):                               # S2B:326: production at the default poses (the pose rule)
        a = (pose.get(t) or {}).get("a_pose_meV")
        if (pose.get(t) or {}).get("mode") != "default" or isinstance(a, bool) or not isinstance(a, (int, float)):
            raise EIntegrity("INT-STRUCT", "c1/gates/pose.json", f"result.{t}.mode, a_pose_meV")
    return {"G1": (g1.get("decision") or {}).get("G1") or {},
            "N": {d: {"pass": (v or {}).get("pass")} for d, v in (((gN.get("result") or {}).get("dopants")) or
                                                                 {}).items()},
            "pose": pose}


def _state(run, gates):
    """The c3b state leaves of a finished campaign beside the plan's literals and the C1 gates (not called on a
    final STOP, whose state file may be absent or hold the D-0 leaves only). INT-STRUCT: n, the production list, G1 and the pose
    modes are what the literals assume."""
    st = run.load("c3b", "state_end.json", "tier", "state_c3b")
    where = "c3b/state_end.json"
    if st is FILE_ABSENT:
        raise EIntegrity("INT-STRUCT", where, "required file absent (RF-12)")
    if st.get("n") != N_HOSTS or isinstance(st.get("n"), bool):
        raise EIntegrity("INT-STRUCT", where, "n")
    if st.get("stage0.production_n8") != list(PROD8):
        raise EIntegrity("INT-STRUCT", where, "stage0.production_n8")
    if st.get("G1.Ca") is not False or st.get("G1.Cl") is not True:
        raise EIntegrity("INT-STRUCT", where, "G1.Ca, G1.Cl")
    if st.get("pose.Cs") != "default" or st.get("pose.Cl") != "default":
        raise EIntegrity("INT-STRUCT", where, "pose.Cs, pose.Cl")
    gn = {d: st.get(f"gateN.{d}") for d in DOPANTS}
    return {"gateN": gn, "agrees": all(isinstance(gn[d], bool) and gn[d] is (gates["N"].get(d) or {}).get("pass")
                                       for d in DOPANTS) and run.ex.g49.g1_pass(gates["G1"], "Cl") is True}


def _census(run):
    """Every name under c3b/records, c3b/raw, c3b/pairs and c3b/regions belongs to the production graph (names
    only; scripts/46 [46:1640-1646] names the pair and region files)."""
    def names(sub):
        d = run.L.cdir("c3b", sub)
        return sorted(os.listdir(d)) if os.path.isdir(d) else []
    for n in names("records"):
        if not n.endswith(".json") or n[:-5] not in ALL_WIDS:
            raise _Names("INT-STRUCT", f"c3b/records/{n}", "not a cell of the production graph")
    for n in names("raw"):
        if n.split(".")[0] not in ALL_LABELS:
            raise _Names("INT-STRUCT", f"c3b/raw/{n}", "not a single point of the production graph")
    for n in names("pairs"):
        m = PAIR_NAME.fullmatch(n)
        if not m or m.group(1) not in PROD8 or \
                int(m.group(3)) not in FIRST[SUBLATTICE[m.group(2)]] + FAR[m.group(1)][SUBLATTICE[m.group(2)]]:
            raise _Names("INT-STRUCT", f"c3b/pairs/{n}", "not a pair file of the production graph")
    for n in names("regions"):
        m = REGION_NAME.fullmatch(n)
        if not m or m.group(1) not in PROD8 or int(m.group(3)) not in FIRST[m.group(2)] + FAR[m.group(1)][m.group(2)]:
            raise _Names("INT-STRUCT", f"c3b/regions/{n}", "not a region file of the production graph")
    return True


def build_tier_table(run, c1, fr):
    """The s2-evaltable-1-shaped table of the eight production hosts from the private c3b archive (spec 13): the
    records (validity under the invariant reading, both readings kept; MACE energies), the single points (F,
    forces), the rejected pairs, and the public C1 gates. Every file is opened under OpenAudit in block 4 and is in
    the manifest (INT-SHA). A cell without a result is left out, so its quartet is invalid (B-15)."""
    ex = run.ex
    _assert_restated(ex)
    run.chk.passed["INT-IMPORT"] += 1
    r4 = (run.route or {}).get("b4") or {}
    man = manifest(run, "c3b")
    try:                                                 # passed at admission; again here: the archive during the run
        n_man = _manifest_complete(run, "c3b", man)
        _census(run)
    except _Names as e:
        raise EIntegrity(e.check, e.where, e.what) from None
    gates = _c1_gates(run)
    state = None if r4.get("id") == "C3B-STOP" else _state(run, gates)
    acc = eg.C3bAccess(run.L, ex.c46, ex.q47, run.au, run.ctx.reads, wids=ALL_WIDS, labels=ALL_LABELS)
    run.__dict__["_b4_access"] = acc                     # e_eval's exit audit calls acc.assert_closed() (review m2)
    hosts, cells, n_leaves, n_expect = {}, {}, 0, 0
    for h in PROD8:
        H = {"host_valid": False, "F": {}, "cell_valid": {}, "failed_checks": {}, "pair_rejected": {},
             "pose": {"Cs": {"mode": "default", "start_failed": {}}, "Cl": {"mode": "default", "start_failed": {}}},
             "E_mace": {}, "forces": {}}
        for wid, kind, lab, L, j, d, leg in ALL_CELLS[h]:
            where = f"c3b/records/{wid}.json"
            info = {"host": h, "kind": kind, "label": lab, "L": L, "site": j, "dopant": d, "leg": leg,
                    "record": False, "valid": None, "failed": None, "valid_as_written": None,
                    "failed_as_written": None, "check5": None if kind == "host" else "not evaluated"}
            rec, free = acc.record(wid, blind=False, block=4), None
            if rec is not FILE_ABSENT:
                if not isinstance(rec, dict) or rec.get("work_id") != wid or rec.get("member") != h or \
                        rec.get("cell_kind") != kind or rec.get("labels") != [lab]:
                    raise EIntegrity("INT-STRUCT", where, "work_id, member, cell_kind, labels")
                v = _validity(rec.get("validity"), kind, where)
                e = (rec.get("relax") or {}).get("E_mace_eV")
                if e is not None and (isinstance(e, bool) or not isinstance(e, (int, float))):
                    raise EIntegrity("INT-STRUCT", where, "relax.E_mace_eV")
                info.update(record=True, **v)
                H["cell_valid"][lab], H["failed_checks"][lab], H["E_mace"][lab] = v["valid"] is True, v["failed"], e
                if kind == "host":
                    H["host_valid"] = v["valid"] is True
                free = rec.get("free")
                n_leaves += _mace_leaf_count(rec)
                n_expect += 4 if kind == "host" else 1
            # a single point without its record is not read: no validity, no free region for the forces (review m1)
            sp = acc.sp(lab, free=free, block=4, read=rec is not FILE_ABSENT)
            info.update(sp=sp["status"], missing_reason=sp["missing_reason"])
            H["F"][lab] = sp["F_eV"]
            if sp["forces"] is not None:
                H["forces"][lab] = sp["forces"]
            cells[wid] = info
        pdir = run.L.cdir("c3b", "pairs")
        for d in DOPANTS:
            for j in FIRST[SUBLATTICE[d]] + FAR[h][SUBLATTICE[d]]:
                p = os.path.join(pdir, f"{h}_{d}{j}p0.json")
                if os.path.exists(p) and _read_json(p).get("status") == "rejected":
                    H["pair_rejected"].setdefault(f"{d}{j}", []).append("p0")
        hosts[h] = H
    acc.assert_closed()                                  # INT-READS: every c3b record and raw file in block 4 only
    run.chk.passed["INT-STRUCT"] += len(cells)
    return {"schema": "s2-evaltable-1", "n": N_HOSTS, "production": list(PROD8), "dopants": list(DOPANTS),
            "sites": {h: {L: {"first": list(FIRST[L]), "far": list(FAR[h][L])} for L in "BAX"} for h in PROD8},
            "hosts": hosts, "a2": {}, "a2_sites": {p: dict(eg.CAL[p]) for p in eg.PILOTS}, "gates": gates,
            "sp_labels": sorted(ALL_LABELS),
            "b4": {"ex": ex, "route": r4, "cells": cells, "state": state, "n_mace_leaves": n_leaves,
                   "n_mace_expected": n_expect, "n_manifest": n_man}}


# ---------------------------------------------------------------- rule V at the A1 tier (P section 14; B-6)
def _a_pose(table, d):
    """a_pose,d (P section 9; scripts/48 a_pose_of): Cs and Cl from the pose gate at the default mode; else 0."""
    if d not in ("Cs", "Cl"):
        return 0.0
    g = ((table.get("gates") or {}).get("pose") or {}).get(d) or {}
    return float(g["a_pose_meV"]) if g.get("mode") == "default" else 0.0


def _no_class_reasons(ex, table, d, ds):
    """scripts/48 _no_class_reasons [48:566-577] without the multi-pose cut (default poses, S2B:326)."""
    g = table.get("gates") or {}
    why = []
    if (((g.get("N") or {}).get(d)) or {}).get("pass") is not True:
        why.append(f"gate N failed: {LABEL_GATE_N}")
    if not ex.g49.g1_pass(g.get("G1") or {}, d):
        why.append("G1 failed for the element (C3)")
    if ds["applies"]:
        why.append(f"dopant-specific failure rule: {LABEL_DOPANT_SPECIFIC}")
    return why


def _compose(ex, table, hv, extra=0.0):
    """The A1 tier of every dopant with its controls and displayed class, as scripts/48 _evaluate [48:640-747]
    composes it (notes I-C7, I-C9, I-17, I-18, I-20), for DOPANTS. extra: a far-bias allowance added to every
    half-width before the classes and the Sr control are formed (S2B:685-687; B-8); 0 for the tier itself."""
    m48, g49 = ex.m48, ex.g49
    n, out = int(table["n"]), {}
    for d in DOPANTS:
        L = SUBLATTICE[d]
        ap = _a_pose(table, d)
        vh = [h for h in table["production"] if hv[d][h]["valid"]]
        Y = {h: hv[d][h]["Y_h_meV"] for h in vh}
        sites = {}
        for h in vh:
            for j, e in hv[d][h]["e_meV"].items():
                sites.setdefault(j, []).append(e)
        for j in table["sites"][table["production"][0]][L]["first"]:
            sites.setdefault(int(j), [])
        het = m48.heterogeneity(sites, 0.0)
        ds = m48.dopant_specific(table, d)               # a2 is empty here: C3b A1 cells only (B-7)
        a1 = m48.tier_a1(list(Y.values()), ap)
        if a1["available"]:
            if extra:
                half = a1["half_width_meV"] + extra
                a1 = {**a1, "half_width_meV": half, "interval_meV": [a1["Ybar_meV"] - half, a1["Ybar_meV"] + half],
                      "U_meV": abs(a1["Ybar_meV"]) + half, "far_bias_added_meV": extra}
            a1["class_rule_v"] = m48.classify(*a1["interval_meV"], list(Y.values()), het["G_meV"])
        out[d] = {"sublattice": L, "a1": a1, "hosts": vh, "Y": Y, "sites": sites, "het": het, "ds": ds,
                  "no_class_reasons": _no_class_reasons(ex, table, d, ds), "flag": bool(het["flag"]),
                  "C2": m48.c2_noise(table, d, hv[d]), "C3": g49.g1_pass((table.get("gates") or {}).get("G1") or {}, d),
                  "C4": {"pass": len(vh) >= n - 1, "n_d": len(vh), "n": n}, "a_pose_meV": ap,
                  "required_hosts": m48.required_hosts(a1.get("s_Y_meV"))}
    sr = out["Sr"]
    sr_a1 = (sr["a1"].get("class_rule_v") == "repels" and not sr["flag"] and not sr["no_class_reasons"]
             and sr["C2"]["pass"] and sr["C3"] and sr["C4"]["pass"])                          # I-C7
    for d in DOPANTS:
        r = out[d]
        fails = [x for x, ok in (("Sr does not repel at the A1 tier", sr_a1), ("C2", r["C2"]["pass"]),
                                 ("C3", r["C3"]), ("C4", r["C4"]["pass"])) if not ok]
        if not r["a1"]["available"]:
            cls = f"no class ({r['a1']['reason']})"
        elif r["no_class_reasons"]:
            cls = "no class (" + "; ".join(r["no_class_reasons"]) + ")"
        elif r["flag"]:
            cls = "no class (heterogeneous shell)"
        elif fails:
            cls = "no class (A1-tier control failed: " + "; ".join(fails) + ")"
        else:
            cls = r["a1"]["class_rule_v"]
        r["class"], r["Sr_repels_A1"] = cls, sr_a1
    return out


def _ranking(ex, table, hv):
    """P:782-785 at the A1 tier: host-paired D_h = Y_h,d - Y_h,d' over the hosts valid for both, with
    t_{n'-1}(1 - 0.05/20) intervals (the 10-pair Bonferroni, S2B:576), over the 6 pairs of the 4 dopants."""
    g49 = ex.g49
    q, out = g49.RULES["Q_RANK"], {}
    for d1, d2 in itertools.combinations(DOPANTS, 2):
        hs = [h for h in table["production"] if hv[d1][h]["valid"] and hv[d2][h]["valid"]]
        D = [hv[d1][h]["Y_h_meV"] - hv[d2][h]["Y_h_meV"] for h in hs]
        r = {"hosts": hs, "n": len(D), "mean_meV": math.fsum(D) / len(D) if D else None, "sd_meV": None,
             "interval_meV": None}
        if len(D) >= 2:
            m = r["mean_meV"]
            r["sd_meV"] = math.sqrt(math.fsum((x - m) ** 2 for x in D) / (len(D) - 1))
            hw = g49.t_ppf(q, len(D) - 1) * r["sd_meV"] / math.sqrt(len(D))
            r["half_width_meV"], r["interval_meV"] = hw, [m - hw, m + hw]
        out[f"{d1}-{d2}"] = r
    return out


def evaluate_tier(table, fr, *, hinge=None):
    """The A1 tier (P:725-730) of the table. hinge must be None: C4b is not run, so no calibrated tier is formed
    (C4B_ITEM). INT-ROUTE: the n_d and the 'computable' flag recorded by the c3b campaign equal E's recompute."""
    if hinge is not None:
        raise EError(f"{C4B_ITEM}: no calibrated tier is formed")
    b4 = table.get("b4") or {}
    ex = b4["ex"]
    hv = {d: ex.m48.host_values(table, d) for d in DOPANTS}
    per = _compose(ex, table, hv)
    n_d = {d: per[d]["a1"]["n_d"] for d in DOPANTS}
    computable = any(per[d]["a1"]["available"] for d in DECISIVE)        # B-2: n_d >= 2 for one of Cl, Cs, GA
    route = b4.get("route") or {}
    rec = route.get("c3b") or {}
    if rec.get("n_d") is not None:
        for d in DOPANTS:
            if rec["n_d"].get(d) != n_d[d]:
                raise EIntegrity("INT-ROUTE", "c3b/state_end.json", f"c3b_tier.n_d.{d}")
        if rec.get("computable") is not computable:
            raise EIntegrity("INT-ROUTE", "c3b/state_end.json", "c3b_tier.computable")
    rid = route.get("id")
    tier = computable and rid in (None, "C4B-NOTRUN")
    sens = None
    if tier:
        d188 = (fr or {}).get("FA188")                  # block 2: self.v["FA188"] = {"A1", "A2", "delta"} (e_eval)
        dl = d188.get("delta") if isinstance(d188, dict) else None
        if dl is None and rid is None:
            sens = {"formed": False}                      # a table evaluated alone (no route, no block 2)
        elif isinstance(dl, bool) or not isinstance(dl, (int, float)) or not math.isfinite(dl):
            # on a tier route FR has passed, so block 2 formed the value: its absence is a key mismatch between
            # the blocks, never a silent "not formed" (B-8; review M6)
            raise EIntegrity("INT-STRUCT", "block 2 FA188", "delta: δ_far(FA188) absent, boolean or not finite")
        else:
            extra = abs(float(d188["delta"]))
            per2 = _compose(ex, table, hv, extra)
            sens = {"formed": True, "delta_far_meV": float(d188["delta"]), "extra_meV": extra,
                    "per_dopant": {d: {"a1": per2[d]["a1"], "class": per2[d]["class"],
                                       "changed": per2[d]["class"] != per[d]["class"]} for d in DOPANTS}}
    return {"route": rid, "tier": tier, "computable": computable, "n_d": n_d, "per_dopant": per, "hv": hv,
            "ranking": _ranking(ex, table, hv) if tier else None, "sens": sens, "table": table, "fr": fr}


# ---------------------------------------------------------------- the rows of block 4 (S2B:676-695; spec 13)
ROUTE_TEXT = {
    "C4B-NOTRUN": "C3b done; an A1 tier is computable (n_d ≥ 2 for at least one of Cl, Cs, GA)",
    "C3B-NOTIER": "C3b done; no A1 tier is computable (n_d < 2 for each of Cl, Cs, GA): the P §15 items are "
                  "printed, with no interval, class or ranking",
    "C3B-STOP": "final STOP in c3b; no A1 tier: the P §15 items of the archived cells are printed, with no interval, "
                "class or ranking",
}
SITE_ROLE = ("first shell", "far f₁", "far f₂")


def _m(x):
    return f"{fm(x)} meV" if isinstance(x, (int, float)) and not isinstance(x, bool) else "not formed"


def rows(result, labels):
    """The rows of block 4 in the order of TITLES. Every A1 class and value carries the label ids L_A1TIER and
    L_DOPANT_<d> (S2B:158-168); on a route without a tier, L_NOTIER or L_C3BSTOP instead. e_eval.py adds the far-site
    label (S2B:631) to the rows with has_a1 and resolves the ids through LABELS."""
    R = []
    table, per, hv, tier, rid = result["table"], result["per_dopant"], result["hv"], result["tier"], result["route"]
    b4 = table.get("b4") or {}
    cells, route, ex = b4.get("cells") or {}, b4.get("route") or {}, b4["ex"]
    notier = ("L_C3BSTOP",) if rid == "C3B-STOP" else ("L_NOTIER",)

    def add(rid_, kind, text, values=None, labs=(), has_a1=False):
        R.append(Row(rid_, kind, text, values, labs, has_a1))

    def tl(*ds):
        return (("L_A1TIER",) + tuple(f"L_DOPANT_{d}" for d in ds)) if tier else notier

    def xc(xid, ok, text, values=None):
        add(xid, "xcheck", f"{xid}: {text}" + (": ok" if ok is True else ""), {**(values or {}), "ok": ok},
            ("L_XFAIL",) if ok is False else ())

    inv_cells = {w for w, c in cells.items() if c.get("check5") == "invariant only"}

    def q_inv(h, d, j):
        L = SUBLATTICE[d]
        return any(w in inv_cells for w in (f"s2_{h}_V{L}{j}", f"s2_{h}_{d}{j}p0_novac", f"s2_{h}_{d}{j}p0_vac"))

    def y_inv(h, d):
        r = hv[d][h]
        return any(q_inv(h, d, j) for j in list(r["far"]) + [j for j in r["first"] if r["first"][j]["valid"]])

    def d_inv(*ds):
        return any(y_inv(h, d) for d in ds for h in per[d]["hosts"])

    def il(cond):
        return ("L_C3B_INV",) if cond else ()

    # 4.0
    add("B4.title.0", "note", TITLES[0])
    c3 = route.get("c3b") or {}
    add("B4.route", "status", f"route {rid}: " + ROUTE_TEXT.get(rid, "no recorded route (a table evaluated alone)") +
        (f" (stop reason: {c3.get('stop_reason')})" if rid == "C3B-STOP" else ""), {"route": rid, "tier": tier})
    add("B4.c4b", "status", f"C4b: {C4B_ITEM}; no calibrated tier is formed and the hinge block stays blind",
        {"c4b_run": C4B_RUN}, ("L_C4B",))
    rec_nd = c3.get("n_d")
    add("B4.nd", "status", "valid hosts n_d (P:680-682, check 5 read invariantly): " +
        ", ".join(f"{d} {result['n_d'][d]}" for d in DOPANTS) + f"; A1 tier computable: {result['computable']}" +
        ("; equal to c3b/state_end.json c3b_tier (INT-ROUTE)" if rec_nd is not None else
         "; no c3b_tier recorded on this route"), {"n_d": dict(result["n_d"]), "computable": result["computable"]})
    n_rec = sum(1 for c in cells.values() if c["record"])
    n_sp = sum(1 for c in cells.values() if c.get("sp") == "complete")
    add("B4.counts", "status", f"cells of the production graph: {len(cells)}; records {n_rec}; single points complete "
        f"{n_sp}; files listed in c3b/{MANIFEST_NAME}: {b4.get('n_manifest')}",
        {"cells": len(cells), "records": n_rec, "sp_complete": n_sp})
    # 4.1
    add("B4.title.1", "note", TITLES[1])
    n_inv = 0
    for h in table["production"]:
        for wid, c in ((w, cells[w]) for w, *_ in ALL_CELLS.get(h, ()) if w in cells):
            why = []
            if not c["record"]:
                why.append("no record")
            elif c["valid"] is not True:
                why.append("failed " + (str(c["failed"]) if c["failed"] is not None else "not evaluated") +
                           (f" (as written {c['failed_as_written']})" if c["failed_as_written"] is not None else ""))
            if c.get("sp") != "complete":
                why.append(f"single point {c.get('sp')}" + (f" ({c['missing_reason']})" if c.get("missing_reason")
                                                             else ""))
            elif not c["record"]:
                why.append("single point complete, not read")
            if why:
                n_inv += 1
                site = f"{c['L']}{c['site']}" if c["L"] else "—"
                add(f"B4.inv.{wid}", "invalid", f"c3b {h} {wid} {c['dopant'] or '—'} {site} {c['leg'] or '—'}: " +
                    "; ".join(why), {"valid": c["valid"], "failed": c["failed"], "sp": c.get("sp")})
        for tj, st in sorted((table["hosts"][h].get("pair_rejected") or {}).items()):
            if not st:
                continue
            poses = ["p0"] if st is True else sorted(st)     # a bare True means p0 (scripts/48 _p0_rejected)
            n_inv += 1
            add(f"B4.inv.pair.{h}.{tj}", "invalid", f"c3b {h} {tj}: pair rejected ({', '.join(poses)})",
                {"poses": poses})
    if not n_inv:
        add("B4.inv.none", "invalid", "c3b: none")
    add("B4.inv.fr", "note", "FR: block 3, B3.inv")
    add("B4.inv.c4b", "note", f"C4b: {C4B_ITEM}", labs=("L_C4B",))
    c5 = {k: sorted(w for w, c in cells.items() if c["kind"] != "host" and c.get("check5") == k)
          for k in ("as written", "invariant only", "failed", "not evaluated")}
    add("B4.check5", "status", "check 5 of the V⁺, D and D+V⁺ cells, both readings (S2B:330-332): passed as written "
        f"{len(c5['as written'])}; passed only under the identical-atom reading {len(c5['invariant only'])}; failed "
        f"under both {len(c5['failed'])}; not evaluated or no record {len(c5['not evaluated'])}",
        {k: len(v) for k, v in c5.items()})
    add("B4.check5.cells", "status", "cells whose check 5 passes only under the identical-atom reading: " +
        (", ".join(c5["invariant only"]) or "none"), {"cells": c5["invariant only"]})
    aq = sorted(f"{h} {d}{j}" for d in DOPANTS for h in table["production"]
                for j in list(hv[d][h]["first"]) + list(hv[d][h]["far"]) if q_inv(h, d, j))
    ay = sorted(f"{h} {d}" for d in DOPANTS for h in per[d]["hosts"] if y_inv(h, d))
    add("B4.check5.flagged", "status", f"quartets flagged: {', '.join(aq) or 'none'}; host values Y_h flagged: "
        f"{', '.join(ay) or 'none'}", {"quartets": aq, "hosts": ay})
    # 4.2
    add("B4.title.2", "note", TITLES[2])
    for h in table["production"]:
        H = table["hosts"][h]
        for d in DOPANTS:
            L, r = SUBLATTICE[d], hv[d][h]
            for k, (j, q) in enumerate([(j, r["first"][j]) for j in r["first"]] +
                                       [(f, r["far"][f]) for f in r["far"]]):
                role = SITE_ROLE[0] if j in r["first"] else SITE_ROLE[1 + list(r["far"]).index(j)]
                e = r["e_meV"].get(j)
                txt = f"{h} {d} {L}{j} ({role}): E_b^A1 = {_m(q['Eb_meV'])}"
                if not q["valid"]:
                    txt += " (quartet not valid: " + "; ".join(q["reasons"]) + ")"
                if j in r["first"]:
                    txt += f"; e_h(j) = {_m(e)}"
                add(f"B4.Eb.{h}.{d}{j}", "Eb_A1", txt, {"Eb_meV": q["Eb_meV"], "e_meV": e, "valid": q["valid"]},
                    tl(d) + il(q_inv(h, d, j)), True)
                em = ex.m48._mace_eb(H, q["labels"])
                dm = em - q["Eb_meV"] if em is not None and q["Eb_meV"] is not None else None
                add(f"B4.mace.{h}.{d}{j}", "Eb_mace", f"{h} {d} {L}{j}: zero-shot MACE E_b = {_m(em)}; MACE − DFT A1 = "
                    f"{_m(dm)}", {"Eb_mace_meV": em, "diff_meV": dm},
                    ("L_MACE",) + ((tl(d) + il(q_inv(h, d, j))) if dm is not None else ()), dm is not None)
            if r["valid"]:
                txt = (f"{h} {d}: far mean = {_m(r['far_mean_meV'])}; Δ_h = {_m(r['Delta_h_meV'])}; Y_h = "
                       f"{_m(r['Y_h_meV'])}; valid first-shell quartets {r['n_valid_first']} of {len(r['first'])}")
            else:
                txt = (f"{h} {d}: not a valid host (far pair valid: {r['far_valid']}; valid first-shell quartets "
                       f"{r['n_valid_first']} of {len(r['first'])}, {VALID_HOST_MIN[L]} needed); far mean = "
                       f"{_m(r['far_mean_meV'])}; Δ_h = {_m(r['Delta_h_meV'])}; Y_h not formed")
            add(f"B4.Y.{h}.{d}", "Y", txt, {"Y_h_meV": r["Y_h_meV"], "Delta_h_meV": r["Delta_h_meV"],
                                            "far_mean_meV": r["far_mean_meV"], "valid": r["valid"]},
                tl(d) + il(r["valid"] and y_inv(h, d)), True)
    # 4.3
    add("B4.title.3", "note", TITLES[3])
    for d in DOPANTS:
        p, a1, het = per[d], per[d]["a1"], per[d]["het"]
        dl = tl(d) + il(d_inv(d))
        # without a tier only the P section 15 items are printed: Ē_d(j) and G_d, but no per-site interval and no
        # heterogeneity flag (P:750-756 belong to rule V; ruling B-1; review M3)
        for j in sorted(het["n_j"], key=int):
            iv = het["intervals"].get(j) if tier else None
            add(f"B4.site.{d}.{j}", "Y", f"{d} site {j}: Ē_d(j) = {_m(het['Ebar_meV'].get(j))} over n_j = "
                f"{het['n_j'][j]} hosts" + (f"; t(0.975) interval [{fm(iv[0])}, {fm(iv[1])}] meV" if iv else ""),
                {"Ebar_meV": het["Ebar_meV"].get(j), "n_j": het["n_j"][j], **({"interval_meV": iv} if tier else {})},
                dl, True)
        add(f"B4.G.{d}", "Y", f"{d}: k = {het['k']} sites; G_d = {_m(het['G_meV'])}; mean_j Ē_d(j) = "
            f"{_m(het['mean_meV'])}" + (f"; heterogeneity flag: {het['flag']}" if tier else ""),
            {"G_meV": het["G_meV"], "mean_meV": het["mean_meV"], "k": het["k"],
             **({"flag": het["flag"]} if tier else {})}, dl, True)
        rh = p["required_hosts"]
        if not tier:
            add(f"B4.tier.{d}", "tier", f"{d}: n_d = {a1['n_d']}; no interval and no class on this route",
                {"n_d": a1["n_d"]}, dl)
        elif not a1["available"]:
            add(f"B4.tier.{d}", "tier", f"{d}: A1 tier not formed ({a1['reason']})", {"n_d": a1["n_d"]}, dl)
            add(f"B4.class.{d}", "class", f"{d}: A1-tier class: {p['class']}", {"class": p["class"]}, dl)
        else:
            lo, hi = a1["interval_meV"]
            add(f"B4.tier.{d}", "tier", f"{d}: n_d = {a1['n_d']}; Ȳ_d = {fm(a1['Ybar_meV'])} meV; s_Y,d = "
                f"{fm(a1['s_Y_meV'])} meV; t_(n_d−1)(q*) = {f6(a1['t'])}; a_pose,d = {fm(a1['a_pose_meV'])} meV; "
                f"I^A1_d = [{fm(lo)}, {fm(hi)}] meV; U_d = {fm(a1['U_meV'])} meV",
                {k: a1[k] for k in ("n_d", "Ybar_meV", "s_Y_meV", "t", "a_pose_meV", "interval_meV", "U_meV")}, dl,
                True)
            c2, c4, ds = p["C2"], p["C4"], p["ds"]
            add(f"B4.controls.{d}", "tier", f"{d}: controls: Sr repels at the A1 tier {p['Sr_repels_A1']}; C2 "
                f"{c2['pass']} (gate N {c2['gate_N']}; SD(Δ_h)/√2 = {_m(c2['sd_over_sqrt2_meV'])}; mean(Δ_h) = "
                f"{_m(c2['mean_meV'])}); C3 {p['C3']}; C4 {c4['pass']} (n_d {c4['n_d']} of n {c4['n']}); no "
                f"heterogeneity flag {not p['flag']}; dopant-specific rule applies {ds['applies']} (failed cells "
                f"{ds['n_failed_cells']} of {ds['n_cells']}; sites over n/4: {sorted(ds['site_trip']) or 'none'})",
                {"Sr_repels_A1": p["Sr_repels_A1"], "C2": c2["pass"], "C3": p["C3"], "C4": c4["pass"],
                 "flag": p["flag"], "dopant_specific": ds["applies"]}, dl, True)
            add(f"B4.class.{d}", "class", f"{d}: A1-tier class: {p['class']}; rule V on I^A1_d, the Y_h,d and G_d: "
                f"{a1['class_rule_v']}", {"class": p["class"], "rule_v": a1["class_rule_v"]}, dl)
        add(f"B4.required.{d}", "tier", f"{d}: required hosts for t·s_Y,d/√n < k_BT: {rh['k_BT']}; < k_BT/2: "
            f"{rh['k_BT/2']}" if rh["k_BT"] is not None or rh["k_BT/2"] is not None or a1.get("s_Y_meV") is not None
            else f"{d}: required hosts: not formed (s_Y,d not formed)", {"required": rh}, dl)
    # 4.4
    add("B4.title.4", "note", TITLES[4])
    if result["ranking"] is None:
        add("B4.rank", "note", "not formed (no A1 tier on this route)", labs=notier)
    else:
        for key, r in result["ranking"].items():
            d1, d2 = key.split("-")
            iv = r["interval_meV"]
            add(f"B4.rank.{key}", "tier", f"{d1} − {d2}: n′ = {r['n']}; mean D_h = {_m(r['mean_meV'])}" +
                (f"; SD = {fm(r['sd_meV'])} meV; t_(n′−1)(0.9975) interval [{fm(iv[0])}, {fm(iv[1])}] meV" if iv else
                 "; interval not formed (n′ < 2)"), {"n": r["n"], "mean_meV": r["mean_meV"], "interval_meV": iv},
                tl(d1, d2) + il(d_inv(d1, d2)), r["mean_meV"] is not None)
    # 4.5
    add("B4.title.5", "note", TITLES[5])
    s = result["sens"]
    if s is None:
        add("B4.sens", "note", "not formed (no A1 tier on this route)", labs=notier)
    elif not s["formed"]:
        add("B4.sens", "note", "not formed (δ_far(FA188) not formed)")
    else:
        add("B4.sens.delta", "delta", f"δ_far(FA188) = {fm(s['delta_far_meV'])} meV; |δ_far(FA188)| is added to every "
            "A1 half-width and rule V is formed again, the Sr control included", {"delta_meV": s["delta_far_meV"]},
            has_a1=True)
        for d in DOPANTS:
            x, base = s["per_dopant"][d], per[d]
            if not x["a1"]["available"]:
                add(f"B4.sens.{d}", "tier", f"{d}: not formed ({x['a1']['reason']})", labs=tl(d))
                continue
            lo, hi = x["a1"]["interval_meV"]
            add(f"B4.sens.{d}", "class", f"{d}: I^A1_d with |δ_far(FA188)| added = [{fm(lo)}, {fm(hi)}] meV; U_d = "
                f"{fm(x['a1']['U_meV'])} meV; class {x['class']}" +
                (f" (without the far bias: {base['class']})" if x["changed"] else " (unchanged)"),
                {"interval_meV": [lo, hi], "U_meV": x["a1"]["U_meV"], "class": x["class"], "changed": x["changed"]},
                tl(d) + il(d_inv(d)) + (("L_SENS",) if x["changed"] else ()), True)
    # 4.6
    add("B4.title.6", "note", TITLES[6])
    n_f = 0
    for h in table["production"]:
        F = table["hosts"][h].get("forces") or {}
        for lab in [c[2] for c in ALL_CELLS.get(h, ())] or sorted(F):
            fo = F.get(lab)
            if fo is None:
                continue
            n_f += 1
            a_, fr_ = fo["all"], fo.get("free")
            if fr_ is None:                               # no free region was given (not reached through this module)
                add(f"B4.forces.{lab}", "forces", f"{lab}: all rms {f6(a_['rms_eVA'])} max {f6(a_['max_eVA'])} n "
                    f"{a_['n']}; free: not formed", {"all": a_, "free": None})
                continue
            add(f"B4.forces.{lab}", "forces", f"{lab}: all rms {f6(a_['rms_eVA'])} max {f6(a_['max_eVA'])} n {a_['n']}; "
                f"free rms {f6(fr_['rms_eVA'])} max {f6(fr_['max_eVA'])} n {fr_['n']}",
                {"all": a_, "free": {k: fr_[k] for k in ("rms_eVA", "max_eVA", "n")}})
            ids, ns = fr_["indices"], fr_["norms_eVA"]
            for i0 in range(0, len(ids), 10):
                add(f"B4.forces.{lab}.{i0}", "forces", "  free norms: " + " ".join(
                    f"{i}:{f6(n)}" for i, n in zip(ids[i0:i0 + 10], ns[i0:i0 + 10])))
    if not n_f:
        add("B4.forces.none", "note", "not formed (no complete single point)")
    # 4.7
    add("B4.title.7", "note", TITLES[7])
    for i, item in enumerate(C4B_ITEMS):
        add(f"B4.c4b.{i}", "note", f"{item}: {C4B_ITEM}", labs=("L_C4B",))
    # 4.8
    add("B4.title.8", "note", TITLES[8])
    if "n_mace_leaves" in b4:
        xc("XC-C3B-MACE-COUNT", b4["n_mace_leaves"] == b4["n_mace_expected"], f"E_mace_eV leaves in the c3b records "
           f"{b4['n_mace_leaves']}; expected {b4['n_mace_expected']} (4 per host record, 1 per other record)")
    st = b4.get("state")
    if st is None:
        xc("XC-C3B-STATE", None, "not evaluated (final STOP in c3b, or a table evaluated alone)")
    else:
        xc("XC-C3B-STATE", st["agrees"], "c3b/state_end.json gateN and G1 against c1/gates/N.json and G1.json")
    worst = 0.0
    for d in DOPANTS:
        for h in per[d]["hosts"]:
            r = hv[d][h]
            js = [j for j in r["first"] if r["first"][j]["valid"]]
            y2 = math.fsum(r["first"][j]["Eb_meV"] for j in js) / len(js) - \
                math.fsum(q["Eb_meV"] for q in r["far"].values()) / len(r["far"])
            worst = max(worst, abs(y2 - r["Y_h_meV"]))
    xc("XC-C3B-YSUM", worst <= TOL_MEV, f"Y_h = mean_j E_b,h(j) − mean_f E_b,h(f) (P:145-146) on every valid host: "
       f"max |Δ| = {'%.3e' % worst} meV (tolerance {'%.0e' % TOL_MEV})", {"max_residual_meV": worst})
    return R

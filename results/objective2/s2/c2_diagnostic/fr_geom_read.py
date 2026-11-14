#!/usr/bin/env python
"""The FR geometry read (S2B_PLAN.md section 6b): items 1-5 of amendment 2026-11-11a part d over the fr archive.

It generalises the part-d driver (part_d_read.py) from the eight C2 records to the S2b far-site reference FR, Cs at
m30 FA188 (S2B section 2), and runs the tools of check5_diag.py (D5, R46, G) on the archived fr final geometries and
raw A2 outputs. Both part-d files are imported unchanged (S2B 6b: "generalised ... without changing the part-d files").
It prints the five items and nothing else:
  1  Integrity, for every complete FR record, in FR order: validity_final.valid, failed, parent, parent_final and the
     two readings of check 5 (valid_as_written, failed_as_written, invariant_only, check5_reading); the files that the
     record names, present in the archive (its final geometry in structures.tar.gz, its validity file in fr/raw, the
     geometry hashes in the validity record); the sha256 of each final geometry and validity file against the record;
     the geometry hashes of the validity record (start, final, parent final, relaxed host) against the files loaded
     here; G's configurations against n_config and the final k, with k = 0 ... n_config - 1 (D-C2-11); each final
     geometry against G's last configuration (1e-6 A); the cell; the check-5 reading of record and validity record
     (invariant, S2B section 2, X4) and the validity leaves of the record against the validity record. The early stop
     of FR is printed with this item, and every cell after it must have no record or a not_run_gate one (S2B 2). A
     mismatch, an absent file among them, is printed and ends the read (S2B 6b).
  2  Agreement on check 5, for every FR pair whose check 5 was evaluated, passing or failing, up to the early stop: the
     record against D5 under the deciding (invariant) reading, and R46 against D5 as written (S2B 6b); the record's
     as-written leaf against D5 as written is printed too. A pass that needs the invariant reading is flagged (S2B 2).
     Then the gated objects: D5's (inorganic child indices, FA child carbons) against R46's gated lists, and D5's
     counts against the record's (validity.checks.5.gated n_inorganic, n_fa), because scripts/46 finds FA molecules by
     a38.molecule and D5 by the 1.6 A C-N cut, and 6b checks the two on the real FR pairs (FR implementation spec,
     section 11, risks).
  3  The per-object table (D5 rows) of every such pair: kind, child and host index, relaxed-host distance from the
     step's defect (0.01 A), |dr| (0.001 A), FA rotation with and without the nitrogen exchange (0.1 deg), pass or fail
     as written and under the invariant reading; for a pair on which the readings disagree, also the R46 lists.
  4  Which cell moved: for each object failing under D5 as written (a set that holds every object failing under the
     invariant reading) or under R46, |dr| and FA rotation of the child final and of the parent final against the
     reference, and between the two cells' k = 0 geometries, with D5's verdict under both readings. The reference is
     the S2-relaxed host for the V+ and D children, and the A1 V+_R(A188) geometry (C1 cells/s2_m30_VA188/relaxed)
     for the D+V+ child (S2B 6b).
  5  Trajectory, for every such pair: the gated inorganic atom of largest |dr|, the gated FA of largest rotation under
     the invariant reading and, if it is another FA, the gated FA of largest rotation as written (all D5), at every
     configuration of both cells read by G, against the item-4 reference.

FR pairs, in FR order (S2B 2, "Order and early stop"; P section 11 partners): V+_R(A188) against host_R(A188),
Cs D(A188) against host_R(A188), Cs D+V+(A188) against V+_R(A188).

Fixed before the read (this file, before any fr datum exists):
- The early stop is found from record leaves only (status, end_rule.outcome, validity_final.valid): walking FR order,
  the first cell that has no record or is pending, ended with another status than complete, has an end rule outside
  END_ACCEPTED, has no validity_final, or is not valid. It is cross-checked against scripts/49 fr_progress (final=True
  when every cell has ended): the same first failure (cell and kind), the same next cell, a waiting check at a
  check_not_evaluated stop, or no stop when FR passed; a disagreement, a refusal of fr_progress (GateRefused) included,
  is an item-1 mismatch.
- A cell starts only after the cell before it passes, and cells not started are recorded as not_run_gate (S2B 2;
  scripts/50 N-FR1): every cell after the stop (fr_progress cells_not_run) has no record or a not_run_gate record.
  Another status there is the named failing item-1 check "no record or not_run_gate after the early stop" of that
  cell; a complete one still gets every other item-1 check (6b: every complete record).
- A pair is read in items 2-5 if its child lies at or before the stop cell in FR order (the stop cell's own pair is
  read), its record is complete and its validity record holds check 5. Items 2-5 never read a later cell.
- A complete record without validity_final is printed "no validity_final (the section 11 check was not evaluated)"
  and is not a mismatch; one without a final geometry is printed "complete without a final geometry". A file that a
  complete record names and the archive lacks (the final geometry, the validity file, the validity record's geometry
  hashes) is a named failing check of item 1, printed MISMATCH, never a failure before output (S2B 6b).
- Readings: deciding = D5 passed_exchanged against validity.checks.5.passed of the record (S2B 2: D5's reading at
  966aa75); as written = D5 passed against R46 and against validity.checks.5.passed_as_written. A pair's readings
  disagree (READINGS DISAGREE) if any of these differ, or if the gated objects of D5 and R46 or the gated counts of D5
  and the record differ (printed "equal" or "DIFFER", with the indices that one side alone gates).
- Item-4 reference, in the parent's numbering: host_R and the S2-relaxed host share the host numbering; the A1 V+_R
  geometry has the V numbering of the D+V+ child's parent.
- Index maps (P section 4): child -> host and child -> parent from D5's maps_section4; for D and D+V+ through
  old_to_new of c1/pairs/m30_Cs188p0.json (novac: host FA188, atoms 188-195, deleted, host 196-232 -> 188-224, Cs
  appended at 225; vac: V 187-194 deleted, V 195-231 -> 187-223, Cs at 224). The m30 host's own Cs (host 232) is an
  ordinary mapped atom (D 224, D+V+ 223); the dopant Cs has no parent image and stays outside check 5, as in D5 and
  check_partner. For every pair the maps must equal those of scripts/46 cell_maps, and for every object printed in
  items 4-5 they must give D5's own row indices, with equal elements in child and parent (the dopant member exempt).
- An FA skeleton is its carbon and the two nitrogens within 1.6 A in the parent final (as D5); the cell of every
  configuration is the final geometry's (fixed-cell relaxation); ties in item 5 go to the first D5 row (child order
  for inorganic atoms, parent-carbon order for FA).
- Precision and tolerance as part d: 0.01 / 0.001 A, 0.1 deg; integrity 1e-6 A.
- When (S2B 6b: "Once, after CAMPAIGN_DONE or FR's final stop and after verify, before C3b and before E"; S2B 2 and
  the FR operations note: the validity leaves are read only after CAMPAIGN_DONE or the final STOP and after verify).
  A running campaign and a stopped one leave the same record leaves, so --read refuses (exit 3, nothing written)
  unless: the leaf status of fr/campaign.json, read by name through GuardedS2b, is 'done' (scripts/50 finish, at
  CAMPAIGN_DONE) with no stop note, or 'stopped' (scripts/50 begin_stop) with --stop-note NOTE naming the stop note
  that makes the STOP final; the fr verify record fr_verify/verify_fr.txt (FR operations note; amendment 2026-11-12a
  item 10) exists and is committed unedited at HEAD; the fr archive is committed unedited at HEAD (git status
  --porcelain of fr/ empty); and neither the c3b archive (c3b/) nor s2b/E_output.txt exists, in the working tree or at
  HEAD. The header prints the status (with the stop note's path and sha256 at a final STOP) and the verify record's
  sha256. Integration review 2 (IX-1: E's definition of a final STOP): a stopped fr whose campaign.json leaves
  start_commit and commit, read by name through GuardedS2b, are both null (a STOP before the node recorded the fr
  campaign commit; scripts/50 set_campaign) is refused before the stop note is read, as E refuses it until a dated
  amendment rules on it (amendment 2026-11-12a item 11; e_eval.Run.route_admit, pinned by the self-test). IX-15: a
  stopped fr whose fr/gates/FR.json exists without its copy fr/gates_applied/gate_FR.gate.json (gate FR written but not
  applied: an N-FR4 or N-FR8 'not applied' Stop of scripts/50 run_gate) is refused too, before the stop note is read;
  the test is by name only (os.path.exists: no gate file is opened), and it is E's (e_eval.gate_fr_unapplied and its
  condition in Run.route_admit, pinned by the self-test). Such a STOP is resolved by a dated fix and a relaunch, never
  by a stop note.
- Final STOP (integration ruling IX-1; amendment 2026-11-12a item 12): one definition for the 6b read, the FR figure and
  E. A STOP of fr is final only through a stop note, and the read applies E's tests (s2b/e_eval.py stop_note_ok and
  Run.note_ok, OP-19; pinned by the self-test): NOTE is a normalised repository-relative path; the note is a file
  committed and clean (at HEAD, git status --porcelain empty); its text, read from HEAD and never from the tree, states
  "the fr STOP is final" (any case) and carries an ISO date (20YY-MM-DD); it is the one file
  results/objective2/s2/FR_STOP_NOTE.md (IX-6; amendment item 12 as amended: any other path is refused before git is
  asked about it), and its HEAD object is a blob (git cat-file -t). The sha256 recorded is that of the text at HEAD,
  as E's. A path the read may not open (a gate file, C1's
  blinded files, C2, a raw output or record) is refused before it is read. 'stopped' without a valid stop note, and
  a stop note on 'done', are refused.
- Runs (part d, 'When'; S2B 7, failure and rerun rules, which "G2 and the FR geometry read follow"): --read computes
  every item in memory and writes c2_diagnostic/fr_geom_read_output.txt itself, by exclusive create, in one piece,
  with its exit code on the last line, then prints it. The one rerun writes fr_geom_read_output_attempt2.txt, and only
  once attempt 1's output is committed unedited at HEAD; a third attempt is refused. An output counts as existing in
  the working tree or at HEAD. Exit codes: 0 items 1-5; 1 item 1 with its mismatch; 2 a failure before output (header,
  stage and exception type only, written as well); 3 a refusal, with nothing written.
- Committed code (part d, 'When'): git status --porcelain must be empty for c2_diagnostic/, s2b/,
  figures/fig_s2_c2_a2.py, scripts/ and every module file under the repository loaded in this process (those loaded
  by path included, which sys.modules does not hold). A module first loaded during the read is checked after it; an
  uncommitted one is a failure before output.
- The c2 mode (part_d_read's read through these code paths) is a self-test path: it is refused outside a synthetic
  root in the temporary directory. In every mode a file under the read root's c2/ (a temporary c2 root excepted) or
  under any results/objective2/s2/c2/ or results/objective2/s2/c1/{raw,records,gates,gates_applied}/ is refused
  before it is opened.

Information state. Written on 2026-11-12, knowing every part-d output, G2 (c2_diagnostic/g2_output.txt, commit
4d27d2d) and the public C1 files; no fr datum exists (FR has not run). Every fr case of the self-test is synthetic,
built from the public C1 geometries; nothing in it bears on an FR result. Revised on 2026-11-12, before any read, after
review rounds 1 and 2, at integration (IX-1: --stop-note NOTE replaces the bare --final-stop) and at integration
review 1 (IX-6: the one stop note path and the blob test; IX-9: the --without-wp2e wording) (no fr datum seen).

Blinding (S2B sections 0, 1 and 6b; OPS2 D-C2-10 to D-C2-12; amendment part d). fr A2 and validity records are read
through GuardedS2b of s2b/guard.py, not through fig_s2_c2_a2.Guarded: S2B section 1 extends WITHHELD for fr records by
the exact name of every energy field the S2b code writes, and GuardedS2b is that extension (a subclass of the D-C2-12
Guarded with WITHHELD_S2B; its children stay guarded). C1 records go through the blinded loader of scripts/46, the C1
structures through part_d_read's loaders, and raw fr outputs only through G, on <campaign>/raw/<label>.p<n>.out.gz,
under the force-only reader conditions of D-C2-11: k from parse_relax(read='counts'), positions by scripts/47's own
rule, the scripts/47 READS counters unchanged (no energy or force read), no calculator loaded (asserted). While the read
runs, an audit hook refuses before opening any gate file (gates/, gates_applied/, step0_attempt1/, *.gate.json,
*.inputs.json), any file under c1/raw, c1/records, c1/gates, c1/gates_applied or c2/ (as above), and any raw output or
record outside the campaign's raw directory. Structures are read from the tar files in memory; the only file written
is the output (S2B 6b: "published unedited"). G is admitted for this purpose only (S2B 6b, X10).

    python fr_geom_read.py --self-test   # synthetic archives from the public C1 cells; no fr or C2 file is read
    python fr_geom_read.py --self-test --without-wp2e
                                         # every case but real G on the public WP2e output (not the full self-test;
                                         # the dated commit needs the full one). It still runs part_d_read's
                                         # self-tests and the C2, A-site and FR route cases, which read the real C1
                                         # structure archive (c1/structures.tar.gz) through part_d_read's loader, so
                                         # only the analyst runs it (INTEGRATION_DECISIONS IX-9); an agent runs only
                                         # the cases that need no C1 archive
    python fr_geom_read.py --read [--stop-note NOTE]
                                         # the one FR geometry read (S2B 6b): after CAMPAIGN_DONE (campaign status
                                         # 'done') or, with --stop-note NOTE (repository-relative, the same note E and
                                         # the FR figure are given), FR's final STOP ('stopped'), and after verify;
                                         # writes c2_diagnostic/fr_geom_read_output.txt (the one rerun: _attempt2.txt)
                                         # and prints it; a refusal exits 3 and writes nothing

Self-test: part_d_read's own cases, then twenty-two cases, each but real G run on the code above and again on
deliberately broken variants of it, which it must fail (several are the code before the reviews of 2026-11-12): the C2
synthetic read of part_d_read through these code paths (output equal line for line to part_d_read.read); the A-site
map of m30_Cs188p0 by hand; the FR routes (all four complete; early stop at V+_R, at Cs D, at Cs D+V+; a stop on Cs D's
end rule after its check; two gated FA of Cs D, one turned 25 deg, one exchanged) on synthetic fr archives built from
the public C1 cells through old_to_new, with host_R's final apart from the S2-relaxed host; the states without a final
geometry, without validity_final and with a check still waiting; the early stop of every kind at every position
against scripts/49 fr_progress; an invariant-only pass at FA188, with the printed words of items 1 and 3; item 2's
deciding, as-written, count and list comparisons and objects that only R46 fails, just past each R46 bound; every
item-1 check failing alone, absent files, records after the early stop, and seven fr_progress disagreements (a
refusal among them); the fr graph against the gate code's grammar; refusals of gate files and blinded paths (each rule
alone), of the c2 mode outside the temporary directory, of withheld leaves and of a loaded calculator module; G's
guards on placeholder fr raw parts; real G on synthetic fr raw parts cut from the public WP2e output (no broken
variant; skipped by --without-wp2e); the --read discipline (the 6b 'When' rule, output files, attempts, exit codes,
header, uncommitted code) on a stand-in git and S2; the stop note's phrase and rules against s2b/e_eval.py, E's own
code compiled from its source, on a throwaway git repository in the temporary directory (IX-1); and the final STOP
only through a stop note (IX-1: every refusal, the header, the command line) on the stand-in git and S2.
"""
import argparse, ast, contextlib, gc, gzip, hashlib, importlib.util, io, json, os, re, shutil, subprocess, sys
import tarfile, tempfile, types

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
S2 = os.path.normpath(os.path.join(HERE, ".."))
REPO = os.path.normpath(os.path.join(S2, "..", "..", ".."))
S2_REL = os.path.join("results", "objective2", "s2")
OUT_NAME, OUT2_NAME = "fr_geom_read_output.txt", "fr_geom_read_output_attempt2.txt"    # S2B 7: the run, the rerun
OUT = os.path.join(HERE, OUT_NAME)
REFUSED = 3                                                                       # exit code of a refusal
P = "s2r_m30_"
FR = {"host": P + "hostA188", "V": P + "VA188", "D": P + "Cs188o0_novac", "DV": P + "Cs188o0_vac"}    # S2B 2; 49
FR_ORDER = [FR[r] for r in ("host", "V", "D", "DV")]
FR_PAIRS = [(FR["V"], FR["host"]), (FR["D"], FR["host"]), (FR["DV"], FR["V"])]     # FR order; P section 11 partners
FR_A1 = {FR["host"]: "s2_m30_host", FR["V"]: "s2_m30_VA188", FR["D"]: "s2_m30_Cs188p0_novac",
         FR["DV"]: "s2_m30_Cs188p0_vac"}                                         # A1 starts (scripts/49 a1_start_of)
VI = 127                                                                          # P section 4: the vacancy iodide
READ_KEYS = ("F", "TS", "forces", "fermi", "mag", "ase")
TOL_G_A = 1e-6                                                                    # part d, item 1
V_LEAVES = ("valid", "failed", "valid_as_written", "failed_as_written", "invariant_only")
GATE_DIRS = ("gates", "gates_applied", "step0_attempt1")
GATE_SUFFIXES = (".gate.json", ".inputs.json")
RAW_SUFFIXES = (".a2.json", ".validity_final.json")
RAW_RE = r"\.out(\.try\d+)?(\.gz)?$"                                             # a raw output: .out, .out.tryN, .gz
BLIND_C1 = ("raw", "records", "gates", "gates_applied")
VAL = ".validity_final.json"
VERIFY = os.path.join("fr_verify", "verify_fr.txt")          # the fr verify record (amendment 2026-11-12a item 10)
NOT_YET = ("c3b", os.path.join("s2b", "E_output.txt"))                         # S2B 6b: before C3b and before E
NOTE_ROOT = "results/objective2/s2"                      # IX-1: where a stop note lies (E's S2_REL; pinned to e_eval)
STOP_PHRASE = re.compile(r"the fr STOP is final", re.I)  # IX-1: what it states (E's STOP_PHRASE, OP-19, ER2-11)
ISO_DATE = re.compile(r"\b(20\d\d)-(\d\d)-(\d\d)\b")     # IX-1: its date (E's ISO_DATE)
NOTE_NAME = "FR_STOP_NOTE.md"                            # IX-6: the one stop note, S2/NOTE_NAME (E's STOP_NOTE)
CK = {"after_stop": "no record or not_run_gate after the early stop (S2B 2)",   # item-1 checks, in printing order
      "final": "final geometry present (structures.tar.gz)",
      "vfile": "validity file present (fr/raw)",
      "final_sha": "final file sha256 = record",
      "vfile_sha": "validity file sha256 = record",
      "label": "validity label and parent = record",
      "gs": "validity record holds geometry_sha256",
      "v_final": "validity final geometry = loaded",
      "v_start": "validity start = A1 start",
      "v_host": "validity relaxed host = C1 host",
      "v_parent": "validity parent final = loaded",
      "g_n": "G configurations = record n_config",
      "g_last": "G last k = record final k",
      "g_final": "final = G last configuration (1e-6 A)",
      "cell": "final cell = A1 start cell",
      "g_range": "G k = 0 ... n_config - 1 (D-C2-11)",
      "reading": "check-5 reading invariant (record, validity record)",
      "leaves": "validity leaves = record (valid, failed, both readings)"}


class Refused(PermissionError):
    pass


class Uncommitted(Exception):
    pass


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_TOOLS = {}


def tools():
    """part_d_read with its tools (check5_diag; the C2 figure module with scripts/46, 47, 49) and the S2b guard,
    loaded once per process."""
    if not _TOOLS:
        pdr = _load("part_d_read", os.path.join(HERE, "part_d_read.py"))
        cd, fig, q47, c46 = pdr.tools()
        g49 = fig.modules()[0]
        gd = _load("s2b_guard", os.path.join(S2, "s2b", "guard.py"))
        assert dict(g49.FR_QUARTET) == FR and list(g49.FR_ORDER) == FR_ORDER, "the FR labels differ from scripts/49"
        assert all(g49.a1_start_of(lab) == a1 for lab, a1 in FR_A1.items()) and cd.VI == VI
        _TOOLS.update(pdr=pdr, cd=cd, fig=fig, q47=q47, c46=c46, g49=g49, gd=gd)
    t = _TOOLS
    return t["pdr"], t["cd"], t["fig"], t["q47"], t["c46"], t["g49"], t["gd"]


# ---- discipline: paths, guard, calculator ----------------------------------------------------------------------------

_CTX = {"on": False}
_HOOK = []


def _temporary(path):
    """A synthetic root of the self-test: in the temporary directory and outside any results/objective2/s2."""
    rp, t = os.path.realpath(path), os.path.realpath(tempfile.gettempdir())
    return rp.startswith(t + os.sep) and (os.sep + S2_REL + os.sep) not in rp + os.sep


def _refuse_path(path, ctx):
    """Why the read may not open path, or None (S2B sections 0, 1 and 6b; the not-read list)."""
    rp = os.path.realpath(path)
    parts = rp.split(os.sep)
    b = parts[-1]
    if b.endswith(GATE_SUFFIXES) or any(d in parts[:-1] for d in GATE_DIRS):
        return "a gate file"
    root, c = ctx.get("root"), ctx.get("campaign")
    rr = None if root is None else os.path.realpath(root)
    tmp_root = rr is not None and _temporary(rr)
    s2s = [os.path.realpath(s) for s in ctx.get("s2_roots", (S2,))]
    for s2 in s2s + ([] if rr is None else [rr]):
        if any(rp.startswith(os.path.join(s2, "c1", d) + os.sep) for d in BLIND_C1):
            return "a blinded C1 file"
    if any(os.sep + os.path.join(S2_REL, "c1", d) + os.sep in rp for d in BLIND_C1):   # any checkout's C1
        return "a blinded C1 file"
    for s2 in s2s:
        if rp.startswith(os.path.join(s2, "c2") + os.sep):
            return "a C2 file"
    if rr is not None and (c == "fr" or not tmp_root) and rp.startswith(os.path.join(rr, "c2") + os.sep):
        return "a C2 file"
    if os.sep + os.path.join(S2_REL, "c2") + os.sep in rp:                            # any checkout's C2
        return "a C2 file"
    raw_like = b.endswith(RAW_SUFFIXES) or re.search(RAW_RE, b)
    if rr is not None and raw_like:
        raw = os.path.join(rr, c, "raw")
        if os.path.dirname(rp) != raw or not any(b.startswith(lab + ".") for lab in ctx.get("labels", ())):
            return "a raw output or record outside the campaign's raw directory"
    return None


def _audit(event, args):
    if event != "open" or not _CTX.get("on") or not args or not isinstance(args[0], (str, bytes, os.PathLike)):
        return
    p = os.fsdecode(args[0])
    why = _refuse_path(p, _CTX)
    if why:
        raise Refused(f"refused before opening: {why} ({os.path.basename(p)}; S2B section 6b)")


@contextlib.contextmanager
def _reading(root, campaign, labels, s2_roots=()):
    """The audit context of one read (paths only; a file never reaches the read unless it passes _refuse_path)."""
    if not _HOOK:
        sys.addaudithook(_audit)
        _HOOK.append(True)
    prev = dict(_CTX)
    _CTX.clear()
    _CTX.update(on=True, root=root, campaign=campaign, labels=tuple(labels), s2_roots=(S2,) + tuple(s2_roots))
    try:
        yield
    finally:
        _CTX.clear()
        _CTX.update(prev)


def _no_calculator(*atoms):
    """No calculator module loaded and no structure with a calculator (check5_diag; amendment part d)."""
    _TOOLS["cd"].assert_no_calculator(*atoms)


def fr_guard(gd, fig):
    """The guard of fr A2 and validity records: GuardedS2b (S2B section 1, WITHHELD extended for fr records)."""
    return gd.guarded_s2b


def stop_on_mismatch(ok_all):
    """A mismatch in item 1 ends the read (S2B 6b; part d, item 1)."""
    return not ok_all


def _archive_class(pdr):
    class CampaignArchive(pdr.Archive):
        """part_d_read.Archive for one campaign: <c>/structures.tar.gz and <c>/graph.json, and the <c>/raw records
        through the campaign's guard; the C1 side (blinded loader, C1 structures, smoke mapping) unchanged."""

        def __init__(self, root, cd, fig, c46, *, campaign, labels, pairs, guard):
            super().__init__(root, cd, fig, c46, c2=False)
            self.c, self.guard = campaign, guard
            self.t2 = tarfile.open(os.path.join(root, campaign, "structures.tar.gz"))
            jobs = json.load(open(os.path.join(root, campaign, "graph.json")))["jobs"]
            self.job = {j["label"]: j for j in jobs if j.get("kind") == "a2v"}
            assert sorted(self.job) == sorted(labels), f"the {campaign} graph does not hold the a2v jobs of its cells"
            par = dict(pairs)
            for lab in labels:
                assert self.job[lab].get("parent") == par.get(lab), f"{lab}: the graph's partner differs from the pairs"

        def _open(self, path):
            why = _refuse_path(path, _CTX)
            if why:
                raise Refused(f"refused: {why} ({os.path.basename(path)})")
            return self.guard(path)

        def a2(self, label):
            return self._open(os.path.join(self.root, self.c, "raw", f"{label}.a2.json"))

        def validity_path(self, label):
            return os.path.join(self.root, self.c, "raw", f"{label}.validity_final.json")

        def validity(self, label):
            return self._open(self.validity_path(label))

        def has_final(self, label):
            """The final geometry of label is a member of structures.tar.gz (nothing is read)."""
            try:
                self.t2.getmember(f"a2/{label}/{label}.final.extxyz")
                return True
            except KeyError:
                return False

        def raw_bytes(self, path):
            """The bytes of a validity file, for its sha256 only."""
            why = _refuse_path(path, _CTX)
            if why:
                raise Refused(f"refused: {why} ({os.path.basename(path)})")
            with open(path, "rb") as fh:
                return fh.read()

        def close(self):
            for t in (self.t1, self.t2):
                if t is not None:
                    t.close()
    return CampaignArchive


def graph_mismatch(g49, lab, j):
    """None, or which part of the a2v job j of the fr cell lab differs from the gate code's own label grammar
    (scripts/49 a2_cell, a1_start_of): 'graph job' (member, kind, sublattice, site, token, A1 start) or 'graph leg'."""
    c = g49.a2_cell(lab)
    if (j["member"], j["cell_kind"], j["L"], int(j["j"]), j.get("token"), j["a1"]) != \
            (c["pilot"], c["kind"], c["L"], c["site"], c["token"], g49.a1_start_of(lab)):
        return "graph job"
    if j.get("leg") != (c["leg"] if c["kind"] in ("D", "DV") else None):
        return "graph leg"
    return None


def archive(root, campaign, labels, pairs, guard):
    pdr, cd, fig, q47, c46, g49, gd = tools()
    A = _archive_class(pdr)(root, cd, fig, c46, campaign=campaign, labels=labels, pairs=pairs, guard=guard)
    if campaign == "fr":                         # the graph's jobs against the gate code's own label grammar
        for lab in labels:
            why = graph_mismatch(g49, lab, A.job[lab])
            if why:
                A.close()
                raise AssertionError(f"{lab}: {why}")
    return A


# ---- G: positions of raw fr outputs (D-C2-11 conditions) -------------------------------------------------------------

def g_part_ok(A, lab, path):
    """A raw part of this campaign's relaxation lab: <root>/<c>/raw/<lab>.p<n>.out.gz."""
    rp = os.path.realpath(path)
    return os.path.dirname(rp) == os.path.realpath(os.path.join(A.root, A.c, "raw")) and \
        re.fullmatch(re.escape(lab) + r"\.p[1-9]\d*\.out\.gz", os.path.basename(rp)) is not None


def reads_changed(q47, before):
    """The scripts/47 READS counters that moved (D-C2-11: none may)."""
    return [k for k in READ_KEYS if q47.READS.get(k, 0) != before[k]]


def g_read(q47, A, lab, g_reader, ranks):
    """G (check5_diag.g_positions) on the raw parts of one relaxation, admitted only for this campaign's raw outputs."""
    parts = A.L.a2_parts(A.c, lab)
    bad = [os.path.basename(p) for p in parts if not g_part_ok(A, lab, p)]
    if bad:
        raise Refused(f"{lab}: G reads only {A.c}/raw/{lab}.p<n>.out.gz (S2B 6b), not {bad}")
    before = {k: q47.READS.get(k, 0) for k in READ_KEYS}
    pr, pos = g_reader(q47, parts, mapping=A.mapping, ranks=ranks, label=lab)
    moved = reads_changed(q47, before)
    if moved:
        raise Refused(f"{lab}: G read a value other than positions ({moved}; D-C2-11)")
    _no_calculator()
    return pr, pos


# ---- early stop, maps, readings, references --------------------------------------------------------------------------

def end_accepted(g49, outcome):
    """An end rule that accepts a cell (P section 11; scripts/49 RULES END_ACCEPTED)."""
    return outcome in g49.RULES["END_ACCEPTED"]


def progress_agrees(p, stop):
    """scripts/49 fr_progress against the record walk: the same first failure (cell and kind), the same next cell, a
    waiting check (passed None) at a check_not_evaluated stop, or no stop when FR passed. p None (fr_progress refused,
    GateRefused) is a disagreement."""
    if p is None:
        return False
    if p["first_failure"] is not None:
        return stop is not None and (p["first_failure"]["cell"], p["first_failure"]["kind"]) == stop[1:]
    if p["next"] is not None:
        return stop is not None and stop[1:] == (p["next"], "not ended")
    if p["passed"] is None:                                    # a check still waiting, a later cell not ended
        return stop is not None and stop[2] == "check_not_evaluated"
    return stop is None


def fr_stop(g49, pdr, recs):
    """(stop, agree): stop = (index, cell, kind) of the first cell in FR order that has not ended, ended without
    acceptance, has no final-geometry check or fails it, or None (S2B 2); agree = scripts/49 fr_progress agrees."""
    rows = []
    for lab in FR_ORDER:
        r = recs.get(lab)
        vf = None if r is None else r.get("validity_final")
        er = None if r is None else r.get("end_rule")
        rows.append({"label": lab, "status": None if r is None else r.get("status"),
                     "end_rule": None if er is None else er.get("outcome"),
                     "check": None if vf is None else "done", "valid": None if vf is None else vf.get("valid") is True})
    stop = None
    for i, w in enumerate(rows):
        st = w["status"]
        kind = ("not ended" if st in (None, "pending") else st if st != "complete" else
                "end_rule" if not end_accepted(g49, w["end_rule"]) else
                "check_not_evaluated" if w["valid"] is None else "check" if w["valid"] is not True else None)
        if kind:
            stop = (i, w["label"], kind)
            break
    try:
        p = g49.fr_progress(rows, final=all(w["status"] not in (None, "pending") for w in rows))
    except g49.GateRefused:                      # an unknown status, a cell not ended at the end: a disagreement
        p = None
    return stop, progress_agrees(p, stop)


def started_after_stop(recs, stop):
    """{label: status} of every cell after the stop (fr_progress cells_not_run) that has a record other than
    not_run_gate: a cell starts only after the cell before it passes, and cells not started are recorded as not_run_gate
    (S2B 2; scripts/50 N-FR1). Any such cell is an item-1 mismatch."""
    later = [] if stop is None else FR_ORDER[stop[0] + 1:]
    return {lab: recs[lab].get("status") for lab in later
            if recs.get(lab) is not None and recs[lab].get("status") != "not_run_gate"}


def pairs_up_to(stop, pairs):
    """The FR pairs whose child lies at or before the stop cell in FR order (S2B 6b, 'up to the early stop')."""
    lim = len(FR_ORDER) if stop is None else stop[0] + 1
    return [(ch, pa) for ch, pa in pairs if FR_ORDER.index(ch) < lim]


def pairs_read(pdr, stop, pairs, VR, final):
    """The FR pairs of items 2-5: up to the early stop, the child complete with a validity record that holds check 5,
    the parent with a final geometry (S2B 6b, 'every FR pair whose check 5 was evaluated, passing or failing')."""
    return [(ch, pa) for ch, pa in pairs_up_to(stop, pairs)
            if ch in VR and pa in final and pdr.leaf(VR[ch], "validity", "checks", "5", "passed") is not None]


def index_maps(cd, kind, n_host, leg):
    """(child -> host, child -> parent) of P section 4, from D5 (old_to_new of the pair leg for D and D+V+)."""
    return cd.maps_section4(kind, n_host, leg)


def object_indices(cd, pdr, o, child, parent, c2p, c2h, members):
    """(child indices, parent indices) of an object, checked against the D5 row (host, child, parent) and by element
    (dopant members exempt)."""
    ic, ip = pdr.obj_indices(cd, o, parent, c2p)
    assert c2h.get(o["child"]) == o["host"] and c2p.get(o["child"]) == o["parent"], \
        f"object {o['kind']} child {o['child']}: the leg maps differ from the D5 row"
    cs, ps = child.get_chemical_symbols(), parent.get_chemical_symbols()
    assert all(cs[a] == ps[b] or a in members for a, b in zip(ic, ip)), f"object child {o['child']}: element mismatch"
    return ic, ip


def item1_presence(A, lab, vf):
    """S2B 6b item 1: the files a complete fr record names are in the archive (its final geometry in
    structures.tar.gz; with validity_final, its validity file in fr/raw). An absent one is a printed mismatch."""
    ch = {CK["final"]: A.has_final(lab)}
    if vf is not None:
        ch[CK["vfile"]] = os.path.isfile(A.validity_path(lab))
    return ch


def _parent_final(pdr, A, final, par):
    """The parent's final geometry, as loaded in item 1 or from structures.tar.gz; None if it is absent."""
    if par is None:
        return None
    if par in final:
        return final[par]
    return pdr.atoms_from_bytes(A.final_bytes(par)) if A.has_final(par) else None


def item2_compare(rec_inv, rec_aw, d5, r46):
    """S2B 6b item 2: the record against D5 under the deciding (invariant) reading; R46 and the record's as-written
    leaf against D5 as written."""
    d5_inv, d5_aw = bool(d5["passed_exchanged"]), bool(d5["passed"])
    return {"d5_inv": d5_inv, "d5_aw": d5_aw, "invariant_only": d5_inv and not d5_aw,
            "disagree": bool(rec_inv) != d5_inv or bool(r46["passed"]) != d5_aw or bool(rec_aw) != d5_aw}


def gated_compare(d5, r46, rec_n):
    """Item 2, the gated objects (FR implementation spec, section 11: scripts/46 finds FA by a38.molecule, D5 by the
    1.6 A C-N cut): D5's gated inorganic child indices and FA child carbons against R46's gated lists, and D5's counts
    against the record's (n_inorganic, n_fa) of validity.checks.5.gated."""
    g = [r for r in d5["rows"] if r["gated"]]
    d = ({r["child"] for r in g if r["kind"] == "inorganic"}, {r["child"] for r in g if r["kind"] == "FA"})
    L = r46["lists"]["gated"]
    s = ({r["index"] for r in L["inorganic"]}, {r["carbon"] for r in L["fa"]})
    n = (len(d[0]), len(d[1]))
    return {"n_d5": n, "n_record": tuple(rec_n), "r46_equal": d == s, "record_equal": tuple(rec_n) == n,
            "d5_only": tuple(sorted(a - b) for a, b in zip(d, s)),
            "r46_only": tuple(sorted(b - a) for a, b in zip(d, s))}


def label_ok(vr, vf, lab, par):
    """Item 1: the validity record's label and parent label against the cell, the record's validity_final.parent and
    the graph's partner."""
    return vr.get("label") == lab and vr.get("parent_label") == vf.get("parent") == par


def reading_ok(rec_reading, vr_reading):
    """Item 1: check 5 read invariantly by the record and by the validity record (S2B section 2, X4)."""
    return rec_reading == "invariant" == vr_reading


def fr_leaf_words(vf):
    """Item 1's validity leaves of an fr record, both readings of check 5 (printed in this order)."""
    return (f"valid {vf.get('valid')}; failed {vf.get('failed')}; valid as written {vf.get('valid_as_written')}; failed "
            f"as written {vf.get('failed_as_written')}; invariant only {vf.get('invariant_only')}; check-5 reading "
            f"{vf.get('check5_reading')}; parent {vf.get('parent')}; parent_final {vf.get('parent_final')}")


def item2_fr_line(ch, pa, recp, rec_aw, cmp, r46, dis):
    """Item 2 of an fr pair: the deciding (invariant) reading, then the as-written one (record, D5, R46)."""
    w = lambda b: "pass" if b else "FAIL"
    return (f"  {ch} against {pa}: invariant reading (deciding): record {w(recp)}, D5 {w(cmp['d5_inv'])}; as written: "
            f"record {w(rec_aw)}, D5 {w(cmp['d5_aw'])}, R46 {w(r46['passed'])}"
            + ("; pass only under the invariant reading (flagged, S2B section 2)" if cmp["invariant_only"] else "")
            + ("; READINGS DISAGREE" if dis else ""))


def item3_row(r):
    """One D5 row of item 3: kind, child, host, d_host_A, |dr|, rotations, as written, invariant reading."""
    k = r["element"] if r["kind"] == "inorganic" else "FA"
    rot = "" if r["kind"] == "inorganic" else f"{r['rot_deg']:.1f}  {r['rot_exchanged_deg']:.1f}"
    return (f"    {k}  {r['child']}  {r['host']}  {r['d_host_A']:.2f}  {r['dr_A']:.3f}  {rot or '-  -'}  "
            f"{'pass' if r['pass'] else 'FAIL'}  {'pass' if r['pass_exchanged'] else 'FAIL'}")


def gated_line(c):
    (ni, nf), (ri, rf) = c["n_d5"], c["n_record"]
    lists = "equal" if c["r46_equal"] else (
        f"DIFFER (D5 only: inorganic {list(c['d5_only'][0])}, FA {list(c['d5_only'][1])}; R46 only: inorganic "
        f"{list(c['r46_only'][0])}, FA {list(c['r46_only'][1])})")
    return (f"    gated objects: D5 {ni} inorganic, {nf} FA; R46 lists {lists}; record (validity.checks.5.gated) {ri} "
            f"inorganic, {rf} FA, " + ("equal" if c["record_equal"] else "DIFFER"))


def failing_objects(d5, r46, c2p, c2h, symbols):
    """Item 4's objects (part d; S2B 6b): every gated object failing under D5 as written (a set that holds every object
    failing under the invariant reading), and every object that R46 gates and fails as written and D5 does not."""
    c46 = _TOOLS["c46"]
    dr_max, rot_max = c46.PARTNER_DR_A, c46.PARTNER_ROT_DEG          # R46 passes a row iff below both (scripts/46)
    failing = {r["child"]: r for r in d5["rows"] if r["gated"] and not r["pass"]}
    L = r46["lists"]["gated"]
    for r in L["inorganic"]:
        if r["dr_A"] >= dr_max and r["index"] not in failing:
            failing[r["index"]] = {"kind": "inorganic", "child": r["index"], "parent": c2p[r["index"]],
                                   "host": c2h[r["index"]], "element": symbols[r["index"]]}
    for r in L["fa"]:
        if (r["dr_carbon_A"] >= dr_max or r["rot_deg"] >= rot_max) and r["carbon"] not in failing:
            failing[r["carbon"]] = {"kind": "FA", "child": r["carbon"], "parent": c2p[r["carbon"]],
                                    "host": c2h[r["carbon"]]}
    return failing


def item4_reference(A, x, inp_pa, final_pa):
    """S2B 6b item 4: the S2-relaxed host for the V+ and D children, the A1 V+_R geometry for the D+V+ child."""
    if x["kind"] in ("V", "D"):
        return x["host"], "S2-relaxed MACE host"
    return A.c1_cell(inp_pa["a1"], "relaxed"), f"A1 {inp_pa['a1']} geometry"


def item5_objects(gated, fr):
    """part d item 5 (C2: D5 as written); for fr also the FA of largest rotation under the invariant reading."""
    ino = max((r for r in gated if r["kind"] == "inorganic"), key=lambda r: r["dr_A"], default=None)
    fa = [r for r in gated if r["kind"] == "FA"]
    fa_w = max(fa, key=lambda r: r["rot_deg"], default=None)
    if not fr:
        return [(None, o) for o in (ino, fa_w) if o is not None]
    fa_i = max(fa, key=lambda r: min(r["rot_deg"], r["rot_exchanged_deg"]), default=None)
    objs = [("largest |dr|", ino), ("largest rotation, invariant reading", fa_i)]
    if fa_w is not fa_i:
        objs.append(("largest rotation as written", fa_w))
    return [(role, o) for role, o in objs if o is not None]


# ---- the read --------------------------------------------------------------------------------------------------------

def read(root=S2, out=print, *, campaign="fr", g_reader=None, s2_roots=()):
    """The read; returns (ok, summary). campaign 'fr' is the read of S2B 6b; 'c2' runs part_d_read's read through these
    code paths, on a synthetic root in the temporary directory only (the self-test). g_reader replaces G only in the
    synthetic self-test."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    if campaign not in ("fr", "c2"):
        raise ValueError(f"campaign {campaign!r}")
    if campaign == "c2" and not _temporary(root):
        raise Refused("the c2 mode runs on a synthetic archive in the temporary directory only; no C2 archive is read "
                      "here (S2B 6b)")
    fr = campaign == "fr"
    labels, pairs = (list(FR_ORDER), list(FR_PAIRS)) if fr else (list(pdr.LABELS), list(pdr.PAIRS))
    guard = fr_guard(gd, fig) if fr else fig.guarded
    g_reader = g_reader or cd.g_positions
    summary = {"stop": None, "item1": {}, "mismatch": {}, "pairs": [], "item2": {}, "gated": {}, "item3": [],
               "item4": {}, "item5_lines": 0, "item5_objects": {}}
    with _reading(root, campaign, labels, s2_roots):
        _no_calculator()
        reads0 = {k: q47.READS.get(k, 0) for k in READ_KEYS}
        A = archive(root, campaign, labels, pairs, guard)
        try:
            ok = _items(A, out, summary, fr, labels, pairs, g_reader)
        finally:
            A.close()
        assert not reads_changed(q47, reads0), "a value other than positions was read"
        _no_calculator()
    return ok, summary


def _items(A, out, summary, fr, labels, pairs, g_reader):
    pdr, cd, fig, q47, c46, g49, gd = tools()
    leaf, w = pdr.leaf, (lambda b: "pass" if b else "FAIL")
    recs = {lab: A.a2(lab) for lab in labels}
    if fr:
        stop, agree = fr_stop(g49, pdr, recs)
        summary["stop"] = stop and stop[1:]
        after = started_after_stop(recs, stop)
        item1 = [lab for lab in labels if recs[lab] is not None and (recs[lab].get("status") == "complete" or
                                                                     lab in after)]
        out("ITEM 1. Integrity (every complete FR record, in FR order)")
        out("  FR order and early stop (record leaves): " +
            ("no early stop; all four cells complete and valid" if stop is None else
             f"first failure {stop[1]} ({stop[2]}); items 2-5 not read beyond it: {FR_ORDER[stop[0] + 1:]}") +
            f"; scripts/49 fr_progress {'agrees' if agree else 'DISAGREES'}")
    else:
        stop, agree, item1, after = None, True, labels, {}
        out("ITEM 1. Integrity")
    final, G, inp, VR = {}, {}, {}, {}
    ok_all = agree
    for lab in item1:
        r = recs[lab]
        if fr and r.get("status") != "complete":     # a cell after the stop that started (S2B 2): nothing to check
            out(f"  {lab}: status {r.get('status')} after the early stop; 0/1 integrity checks equal; MISMATCH: "
                f"{CK['after_stop']}")
            summary["item1"][lab] = (0, 1)
            summary["mismatch"][lab] = [CK["after_stop"]]
            ok_all = False
            continue
        vf, fg = r.get("validity_final"), r.get("final_geometry")
        if fr and fg is None:
            out(f"  {lab}: complete without a final geometry" + (
                f"; 0/1 integrity checks equal; MISMATCH: {CK['after_stop']}" if lab in after else
                " (nothing to check)"))
            if lab in after:
                summary["item1"][lab] = (0, 1)
                summary["mismatch"][lab] = [CK["after_stop"]]
                ok_all = False
            continue
        inp[lab] = A.inputs(lab)
        par = inp[lab]["parent"]
        checks = ({CK["after_stop"]: False} if lab in after else {}) if fr else {}
        checks.update(item1_presence(A, lab, vf) if fr else {})
        if checks.get(CK["final"], True):          # else nothing more of this record can be checked
            fb = A.final_bytes(lab)
            final[lab] = pdr.atoms_from_bytes(fb)
            checks[CK["final_sha"]] = pdr.sha256_bytes(fb) == fg.get("sha256")
            if vf is not None and checks.get(CK["vfile"], True):
                vb = A.raw_bytes(A.validity_path(lab))
                vr = VR[lab] = A.validity(lab)
                gs = vr.get("geometry_sha256")
                checks[CK["vfile_sha"]] = pdr.sha256_bytes(vb) == vf.get("sha256")
                checks[CK["label"]] = label_ok(vr, vf, lab, par)
                if fr:
                    checks[CK["gs"]] = gs is not None
                if gs is not None or not fr:       # c2: as part_d_read
                    par_at = _parent_final(pdr, A, final, par)
                    checks.update({
                        CK["v_final"]: gs.get("final") == c46.sha256_atoms(final[lab]),
                        CK["v_start"]: gs.get("start") == c46.sha256_atoms(inp[lab]["start"]),
                        CK["v_host"]: gs.get("host_relaxed") == c46.sha256_atoms(inp[lab]["host"]),
                        CK["v_parent"]: gs.get("parent_final") == (None if par_at is None
                                                                   else c46.sha256_atoms(par_at))})
            rk = leaf(r, "layout", "ranks")
            pr, pos = g_read(q47, A, lab, g_reader, rk)
            G[lab] = pos
            kl = max(pos)
            checks[CK["g_n"]] = len(pos) == r.get("n_config")
            checks[CK["g_last"]] = kl == fg.get("k")
            checks[CK["g_final"]] = pdr.check_integrity_positions(pos[kl], final[lab])
            checks[CK["cell"]] = np.allclose(final[lab].cell.array, inp[lab]["start"].cell.array, rtol=0, atol=1e-9)
            if fr:
                checks[CK["g_range"]] = sorted(pos) == list(range(int(r.get("n_config") or 0)))
                if lab in VR:
                    checks[CK["reading"]] = reading_ok(vf.get("check5_reading"),
                                                       leaf(VR[lab], "validity", "check5_reading"))
                    checks[CK["leaves"]] = all(vf.get(k) == leaf(VR[lab], "validity", k) for k in V_LEAVES)
        bad = [k for k, v in checks.items() if not v]
        tail = f"{len(checks) - len(bad)}/{len(checks)} integrity checks equal" + ("" if not bad else
                                                                                    "; MISMATCH: " + "; ".join(bad))
        if not fr:
            out(f"  {lab}: valid {vf.get('valid')}; failed {vf.get('failed')}; parent {vf.get('parent')}; "
                f"parent_final {vf.get('parent_final')}; " + tail)
        elif vf is None:
            out(f"  {lab}: no validity_final (the section 11 check was not evaluated); parent {par}; " + tail)
        else:
            out(f"  {lab}: {fr_leaf_words(vf)}; " + tail)
        summary["item1"][lab] = (len(checks) - len(bad), len(checks))
        if bad:
            summary["mismatch"][lab] = bad
        ok_all = ok_all and not bad
    if stop_on_mismatch(ok_all):
        out("Integrity mismatch: the read ends here (S2B_PLAN.md section 6b; part d, item 1)." if fr else
            "Integrity mismatch: the diagnostic ends here (part d, item 1).")
        return False

    pairs_ = pairs_read(pdr, stop, pairs, VR, final) if fr else pairs
    summary["pairs"] = list(pairs_)
    out("ITEM 2. Agreement on check 5 (" + ("deciding reading: invariant under the nitrogen exchange, S2B section 2; "
                                            if fr else "") + "record / D5 / R46)")
    if fr and not pairs_:
        out("  no FR pair whose check 5 was evaluated")
    res, disagree = {}, []
    for ch, pa in pairs_:
        x = inp[ch]
        d5 = cd.d5_check(x["kind"], final[ch], final[pa], x["host"], x["region"], x["leg"])
        r46, cp = cd.r46_for(c46, x["kind"], final[ch], final[pa], x["host"], x["region"], x["leg"])
        assert r46["passed"] == cp["passed"] and r46["gated"] == cp["gated"], f"{ch}: R46 differs from check_partner"
        vr = VR[ch]
        recp = leaf(vr, "validity", "checks", "5", "passed")
        res[ch] = (d5, r46)
        if fr:
            rec_aw = leaf(vr, "validity", "checks", "5", "passed_as_written")
            rec_n = tuple(leaf(vr, "validity", "checks", "5", "gated", k) for k in ("n_inorganic", "n_fa"))
            cmp, gcp = item2_compare(recp, rec_aw, d5, r46), gated_compare(d5, r46, rec_n)
            dis = cmp["disagree"] or not (gcp["r46_equal"] and gcp["record_equal"])
            summary["item2"][ch] = (bool(recp), cmp["d5_inv"], bool(rec_aw), cmp["d5_aw"], bool(r46["passed"]))
            summary["gated"][ch] = gcp
            if dis:
                disagree.append(ch)
            out(item2_fr_line(ch, pa, recp, rec_aw, cmp, r46, dis))
            out(gated_line(gcp))
            continue
        three = (bool(recp), bool(d5["passed"]), bool(r46["passed"]))
        summary["item2"][ch] = three + (bool(d5["passed_exchanged"]),)
        if len(set(three)) > 1:
            disagree.append(ch)
        out(f"  {ch} against {pa}: record {w(three[0])}; D5 {w(three[1])}; R46 {w(three[2])}; "
            f"D5 permutation-invariant reading {w(d5['passed_exchanged'])}"
            + ("; READINGS DISAGREE" if len(set(three)) > 1 else ""))

    out("ITEM 3. Per-object table (gated objects; D5)")
    for ch, pa in pairs_:
        if not fr and (ch, pa) not in pdr.FAR and ch not in disagree:
            continue
        d5, r46 = res[ch]
        rows = [r for r in d5["rows"] if r["gated"]]
        summary["item3"].append(ch)
        out(f"  {ch} against {pa}: {len(rows)} gated objects "
            f"({sum(r['kind'] == 'inorganic' for r in rows)} inorganic, {sum(r['kind'] == 'FA' for r in rows)} FA)")
        out("    kind  child  host  d_host_A  dr_A  rot_deg  rot_exchanged_deg  check5_as_written  permutation_invariant")
        for r in sorted(rows, key=lambda r: (r["kind"], r["host"])):
            out(item3_row(r))
        if ch in disagree:
            L = r46["lists"]["gated"]
            out("    R46 gated inorganic (index, d_host_A, dr_A): " +
                "; ".join(f"{r['index']} {r['d_host_A']:.2f} {r['dr_A']:.3f}" for r in L["inorganic"]))
            out("    R46 gated FA (carbon, d_host_A, dr_carbon_A, rot_deg): " +
                "; ".join(f"{r['carbon']} {r['d_host_A']:.2f} {r['dr_carbon_A']:.3f} {r['rot_deg']:.1f}"
                          for r in L["fa"]))

    out("ITEM 4. Which cell moved (failing objects)")
    refs = {}
    for ch, pa in pairs_:
        d5, r46 = res[ch]
        x = inp[ch]
        c2h, c2p = index_maps(cd, x["kind"], len(x["host"]), x["leg"])
        assert (c2h, c2p) == c46.cell_maps(x["kind"], built=x["leg"], n_host=len(x["host"])), \
            f"{ch}: the leg maps of D5 and scripts/46 differ"
        members = set() if x["leg"] is None else {int(m) for m in x["leg"]["members"]}
        ref, rname = item4_reference(A, x, inp[pa], final[pa])
        assert ref.get_chemical_symbols() == final[pa].get_chemical_symbols(), f"{ch}: reference numbering"
        refs[ch] = (ref, c2p, c2h, members)
        failing = failing_objects(d5, r46, c2p, c2h, final[ch].get_chemical_symbols())
        if not failing:
            continue
        out(f"  {ch} against {pa}: {len(failing)} failing object(s); reference {rname}")
        cell = final[ch].cell.array
        k0c, k0p = G[ch][0][1], G[pa][0][1]
        for c in sorted(failing):
            o = failing[c]
            ic, ip = object_indices(cd, pdr, o, final[ch], final[pa], c2p, c2h, members)
            name = (o["element"] if o["kind"] == "inorganic" else "FA") + f" child {o['child']} host {o['host']}"
            m3 = (pdr.measure(cd, final[ch].positions, ref.positions, ic, ip, cell),
                  pdr.measure(cd, final[pa].positions, ref.positions, ip, ip, cell),
                  pdr.measure(cd, k0c, k0p, ic, ip, cell))
            summary["item4"].setdefault(ch, []).append((o["child"], o["host"]) + tuple(m[0] for m in m3))
            verdict = "" if not fr else ("; D5: not failing (R46 only)" if "pass" not in o else
                                         f"; D5: {w(o['pass'])} as written, {w(o['pass_exchanged'])} invariantly")
            out(f"    {name}: child final vs reference {pdr.fmt(*m3[0])}; parent final vs reference {pdr.fmt(*m3[1])}; "
                f"child k = 0 vs parent k = 0 {pdr.fmt(*m3[2])}" + verdict)

    out("ITEM 5. Trajectory (" + ("FR pairs read" if fr else "far pairs") + "; against the item-4 reference)")
    for ch, pa in (pairs_ if fr else pdr.FAR):
        d5, _ = res[ch]
        ref, c2p, c2h, members = refs[ch]
        cell = final[ch].cell.array
        for role, o in item5_objects([r for r in d5["rows"] if r["gated"]], fr):
            ic, ip = object_indices(cd, pdr, o, final[ch], final[pa], c2p, c2h, members)
            summary["item5_objects"].setdefault(ch, []).append((role, o["kind"], o["host"]))
            name = (o["element"] if o["kind"] == "inorganic" else "FA") + f" child {o['child']} host {o['host']}" + \
                ("" if role is None else f" ({role})")
            for cellname, lab, ii in (("child", ch, ic), ("parent", pa, ip)):
                out(f"  {ch} against {pa}; {name}; {cellname} {lab}; k, |dr| A" +
                    ("" if len(ii) == 1 else ", rot deg, rot exchanged deg"))
                for k in sorted(G[lab]):
                    dr, rot, rotx = pdr.measure(cd, G[lab][k][1], ref.positions, ii, ip, cell)
                    out(f"    {k} {dr:.3f}" + ("" if rot is None else f" {rot:.1f} {rotx:.1f}"))
                    summary["item5_lines"] += 1
    out("END: items 1-5 printed for the FR pairs read; no energy, force or gate value read; no gate file opened; no "
        "calculator loaded" if fr else
        "END: items 1-5 printed; no energy, force or gate value read; no calculator loaded")
    return True


# ---- the final STOP: the stop note (IX-1) ----------------------------------------------------------------------------

def _git_cli(repo):
    """git -C repo for the read: stdout decoded as UTF-8 with replacement and without newline translation, which is the
    text e_eval.Run.note_ok reads from HEAD, so that a stop note's text and sha256 are E's (IX-1)."""
    def git(*a):
        r = subprocess.run(["git", "-C", repo, *a], capture_output=True)
        return types.SimpleNamespace(returncode=r.returncode, stdout=r.stdout.decode(errors="replace"))
    return git


def note_path_ok(path, s2_rel=NOTE_ROOT):
    """IX-6 (amendment 2026-11-12a item 12): the one stop note is S2/FR_STOP_NOTE.md (E's STOP_NOTE), which lies under
    S2/ and not under s2b/; s2_rel is S2 relative to the repository."""
    return path == f"{s2_rel}/{NOTE_NAME}" and path.startswith(s2_rel + "/") and not path.startswith(f"{s2_rel}/s2b/")


def stop_note_ok(path, text, s2_rel=NOTE_ROOT):
    """IX-1, E's test of a stop note (e_eval.stop_note_ok, OP-19; pinned by the self-test): the one note of
    note_path_ok (IX-6), dated, stating that the fr STOP is final. path is the note's repository-relative path and text
    its text at HEAD; s2_rel is S2 relative to the repository (NOTE_ROOT in the read)."""
    return note_path_ok(path, s2_rel) and bool(STOP_PHRASE.search(text)) and bool(ISO_DATE.search(text))


def note_text(git, repo, s2, note):
    """IX-1, E's committed-and-clean test (e_eval.Run.note_ok): the text at HEAD of the note at the normalised
    repository-relative path note, a file in the tree that is at HEAD and unchanged (git status --porcelain empty). The
    text is read from HEAD (git show), never from the tree, and only once git cat-file -t names a blob (IX-6: a glob,
    a pathspec or a directory is never read as a note). A path the read may not open (_refuse_path: a gate file, C1's
    blinded files, C2, a raw output or record), and any path but the one stop note (note_path_ok, IX-6), is refused
    before git is asked about it. Raises Refused."""
    if not isinstance(note, str) or note.startswith("/") or any(s in ("", ".", "..") for s in note.split("/")):
        raise Refused(f"--stop-note {note!r}: a normalised repository-relative path is required (IX-1)")
    p = os.path.join(repo, *note.split("/"))
    why = _refuse_path(p, {"root": s2, "campaign": "fr", "labels": (), "s2_roots": (S2, s2)})
    if why:
        raise Refused(f"--stop-note {note}: refused before it is read: {why} (S2B_PLAN.md section 6b)")
    s2_rel = os.path.relpath(os.path.realpath(s2), os.path.realpath(repo)).replace(os.sep, "/")
    if not note_path_ok(note, s2_rel):                    # IX-6: one fixed path, before git is asked about it
        raise Refused(f"--stop-note {note}: the stop note is the one file {s2_rel}/{NOTE_NAME} (IX-6)")
    st, k = git("status", "--porcelain", "--", p), git("cat-file", "-t", "HEAD:" + note)
    r = git("show", "HEAD:" + note) if k.returncode == 0 and k.stdout.strip() == "blob" else k   # IX-6: a blob
    if not os.path.isfile(p) or st.returncode != 0 or st.stdout.strip() or k.stdout.strip() != "blob" or \
            r.returncode != 0:
        raise Refused(f"--stop-note {note} is not committed and clean (a file at HEAD, unchanged in the tree; IX-1)")
    return r.stdout


def before_campaign_commit(start, commit):
    """Integration review 2 (IX-1; amendment 2026-11-12a item 11): fr/campaign.json's start_commit and commit both null,
    a STOP before the node recorded the fr campaign commit, which E refuses (e_eval.Run.route_admit; pinned by the
    self-test against E's source)."""
    return start is None and commit is None


def gate_fr_unapplied(fr):
    """Integration review 2 (IX-15): gate FR written but not applied (scripts/50 run_gate writes fr/gates/FR.json before
    its gates_applied copy, and an N-FR4 or N-FR8 'not applied' Stop comes between the two). By name only
    (os.path.exists): no gate file is opened. E's e_eval.gate_fr_unapplied (pinned by the self-test)."""
    return os.path.exists(os.path.join(fr, "gates", "FR.json")) and \
        not os.path.exists(os.path.join(fr, "gates_applied", "gate_FR.gate.json"))


def final_stop(git, repo, s2, status, note):
    """None at CAMPAIGN_DONE (status 'done', no stop note); (note, sha256 of its text at HEAD) at FR's final STOP
    (status 'stopped' and a valid stop note: note_text, then stop_note_ok with S2 relative to repo). A STOP is final
    only through its stop note, and a stop note on 'done' is refused (IX-1: one definition of a final STOP for the 6b
    read, the FR figure and E; amendment 2026-11-12a item 12). The sha256 is E's (of the text, UTF-8). Raises
    Refused."""
    if status != ("stopped" if note is not None else "done"):
        raise Refused(f"fr/campaign.json status {status!r}" + ("" if note is None else " with --stop-note") +
                      ": the read runs after CAMPAIGN_DONE (status 'done', no stop note) or after FR's final STOP "
                      "(status 'stopped', with --stop-note NOTE, the stop note that makes it final: IX-1) (S2B_PLAN.md "
                      "section 6b)")
    if note is None:
        return None
    text = note_text(git, repo, s2, note)
    s2_rel = os.path.relpath(os.path.realpath(s2), os.path.realpath(repo)).replace(os.sep, "/")
    if not stop_note_ok(note, text, s2_rel):
        raise Refused(f"--stop-note {note} is not a dated note under {s2_rel}/ (not under s2b/) stating that the fr "
                      f"STOP is final (IX-1; E's OP-19)")
    return note, hashlib.sha256(text.encode()).hexdigest()


# ---- self-test: synthetic archives -----------------------------------------------------------------------------------

class _Undetected(Exception):
    pass


@contextlib.contextmanager
def _mutant(name, bad):
    g = globals()
    old = g[name]
    g[name] = bad
    try:
        yield
    finally:
        g[name] = old


def _stub_g(starts, finals, n_cfg, parts=None):
    """G replaced: n_cfg configurations interpolated from the A1 start to the final (G itself: check5_diag and t_g)."""
    def g(q47_, paths, *, mapping, ranks, label):
        if parts is not None:
            assert [os.path.realpath(p) for p in paths] == parts[label], f"{label}: G was given other parts"
        s0, f1 = starts[label], finals[label]
        pos = {k: (f1.get_chemical_symbols(), s0.positions + (f1.positions - s0.positions) * k / (n_cfg - 1))
               for k in range(n_cfg)}
        pos[n_cfg - 1] = (f1.get_chemical_symbols(), f1.positions.copy())
        return {"n_config": n_cfg}, pos
    return g


def _write_archive(tmp, campaign, jobs, fin, *, reading=None, n_cfg=5, plant=None):
    """<tmp>/<campaign> in the archive layout of scripts/50 archive: graph.json; structures.tar.gz with the finals; for
    each cell with a final, its validity record (scripts/46 validity_a2 at the given check-5 reading) and A2 record,
    and for fr a placeholder raw part; for fr cells without a final, a not_run_gate record. Returns (finals, starts,
    parts)."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    if not os.path.lexists(os.path.join(tmp, "c1")):
        os.symlink(os.path.join(S2, "c1"), os.path.join(tmp, "c1"))
    cdir = os.path.join(tmp, campaign)
    raw = os.path.join(cdir, "raw")
    os.makedirs(raw)
    json.dump({"jobs": jobs}, open(os.path.join(cdir, "graph.json"), "w"))
    fdir = os.path.join(tmp, f"finals_{campaign}")
    fp = lambda lab: os.path.join(fdir, "a2", lab, f"{lab}.final.extxyz")
    fin = {lab: c46.write_cell(fp(lab), at) for lab, at in fin.items() if at is not None}
    with tarfile.open(os.path.join(cdir, "structures.tar.gz"), "w:gz") as tf:
        for lab in fin:
            tf.add(fp(lab), arcname=f"a2/{lab}/{lab}.final.extxyz")
    labels = [j["label"] for j in jobs]
    A = archive(tmp, campaign, labels, [(j["label"], j["parent"]) for j in jobs if j["parent"]], fig.guarded)
    starts, parts = {}, {}
    for j in jobs:
        lab, par = j["label"], j["parent"]
        if lab not in fin:
            c46.dump_public({"schema": "s2-a2-1", "label": lab, "campaign": campaign, "status": "not_run_gate",
                             "status_reason": "FR early stop (S2B section 2)", "parts": []},
                            os.path.join(raw, f"{lab}.a2.json"))
            continue
        inp = A.inputs(lab)
        starts[lab] = inp["start"]
        kw = {} if reading is None else {"check5_reading": reading}
        val = c46.validity_a2(inp["kind"], start=inp["start"], final=fin[lab], region=inp["region"],
                              host_relaxed=inp["host"], parent_final=par and fin[par], built=inp["leg"], **kw)
        vrec = {"label": lab, "kind": inp["kind"], "parent_label": par, "validity": val,
                "geometry_sha256": {"start": c46.sha256_atoms(inp["start"]), "final": c46.sha256_atoms(fin[lab]),
                                    "parent_final": par and c46.sha256_atoms(fin[par]),
                                    "host_relaxed": c46.sha256_atoms(inp["host"])}}
        vp = c46.dump_public(vrec, A.validity_path(lab))
        vfl = {"valid": val["valid"], "failed": val["failed"], "file": os.path.basename(vp),
               "sha256": pdr.sha256_bytes(open(vp, "rb").read()), "parent": par, "parent_final": par is not None}
        if reading == "invariant":
            vfl.update({k: val[k] for k in ("check5_reading",) + V_LEAVES[2:]})
        rec = {"label": lab, "campaign": campaign, "status": "complete", "n_config": n_cfg,
               "layout": {"name": "64", "ranks": 64, "copies": 1},
               "end_rule": {"outcome": "accepted_converged", "dF_200_180_meV": None},
               "final_geometry": {"file": os.path.basename(fp(lab)), "k": n_cfg - 1,
                                  "sha256": pdr.sha256_bytes(open(fp(lab), "rb").read())}, "validity_final": vfl}
        if plant and lab in plant:
            rec.update(plant[lab])
        c46.dump_public(rec, os.path.join(raw, f"{lab}.a2.json"))
        if campaign == "fr":
            pp = os.path.join(raw, f"{lab}.p1.out.gz")
            with gzip.open(pp, "wt") as fh:
                fh.write("synthetic placeholder; G is stubbed\n")
            parts[lab] = [os.path.realpath(pp)]
    A.close()
    return fin, starts, parts


def _c2_archive(tmp):
    """part_d_read.self_test_read's synthetic C2 archive, built the same way: every 'final' is the A1 relaxed geometry
    of its A1 cell; one gated far atom of VB76 (about the vacancy) and one (about the site) moved by 0.35 A."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    jobs = [{"id": f"a2v:{P}{lab}", "kind": "a2v", "label": P + lab, "parent": par and P + par, "member": "m30",
             "cell_kind": kind, "L": "B", "j": j, "token": tok, "leg": leg, "a1": a1}
            for lab, a1, kind, par, j, tok, leg in (
                ("VB136", "s2_m30_VB136", "V", "hostB136", 136, None, None),
                ("hostB136", "s2_m30_host", "host", None, 136, None, None),
                ("Sr136o0_novac", "s2_m30_Sr136p0_novac", "D", "hostB136", 136, "Sr", "novac"),
                ("Sr136o0_vac", "s2_m30_Sr136p0_vac", "DV", "VB136", 136, "Sr", "vac"),
                ("hostB76", "s2_m30_host", "host", None, 76, None, None),
                ("VB76", "s2_m30_VB76", "V", "hostB76", 76, None, None),
                ("Sr76o0_novac", "s2_m30_Sr76p0_novac", "D", "hostB76", 76, "Sr", "novac"),
                ("Sr76o0_vac", "s2_m30_Sr76p0_vac", "DV", "VB76", 76, "Sr", "vac"))]
    A1 = pdr.Archive(S2, cd, fig, c46, c2=False)
    fin = {x["label"]: A1.c1_cell(x["a1"], "relaxed") for x in jobs}
    V, H, DV = P + "VB76", P + "hostB76", P + "Sr76o0_vac"
    reg = c46.check_region_record(c46.load_record(A1.L.region("c1", "m30", "B", 76)))
    host = A1.c1_cell("s2_m30_host", "relaxed")
    legv = c46.load_record(A1.L.pair("c1", "m30", "Sr", 76, 0))["legs"]["vac"]
    gmax = lambda rows: max((r for r in rows if r["gated"] and r["kind"] == "inorganic"), key=lambda r: r["d_host_A"])
    mA = gmax(cd.d5_check("V", fin[V], fin[H], host, reg)["rows"])
    mB = gmax(cd.d5_check("DV", fin[DV], fin[V], host, reg, legv)["rows"])
    assert mA["child"] != mB["parent"], "the two moved atoms coincide"
    at = fin[V].copy(); at.calc = None
    at.positions[mA["child"]] += np.array([0.35, 0.0, 0.0])
    at.positions[mB["parent"]] += np.array([0.0, 0.35, 0.0])
    fin[V] = at
    A1.t1.close()
    fin, starts, _ = _write_archive(tmp, "c2", jobs, fin)
    return fin, starts, mA, mB


def _fr_jobs():
    pdr, cd, fig, q47, c46, g49, gd = tools()
    jobs, par = [], {FR["V"]: FR["host"], FR["D"]: FR["host"], FR["DV"]: FR["V"]}     # P section 11, written out
    for lab in FR_ORDER:
        c = g49.a2_cell(lab)
        jobs.append({"id": f"a2v:{lab}", "kind": "a2v", "label": lab, "parent": par.get(lab), "member": c["pilot"],
                     "cell_kind": c["kind"], "L": c["L"], "j": c["site"], "token": c["token"],
                     "leg": c["leg"] if c["kind"] in ("D", "DV") else None, "a1": FR_A1[lab]})
    assert [(j["cell_kind"], j["L"], j["j"], j["leg"]) for j in jobs] == \
        [("host", "A", 188, None), ("V", "A", 188, None), ("D", "A", 188, "novac"), ("DV", "A", 188, "vac")]
    return jobs


def _substitute(parent, leg, start):
    """A child built from its parent by a pair leg (P section 4): parent atom h goes to old_to_new[h], the deleted FA
    drops out, and the dopant member keeps its C1 A1 start position; without a leg, the V+ cell (I127 removed)."""
    if leg is None:
        ch = parent.copy(); del ch[VI]; ch.calc = None
        return ch
    ch = start.copy(); ch.calc = None
    for h, c in leg["old_to_new"].items():
        assert ch.numbers[int(c)] == parent.numbers[int(h)], "the leg maps an atom onto another element"
        ch.positions[int(c)] = parent.positions[int(h)]
    return ch


def _fr_inputs():
    """The public C1 inputs of FR (S2B 2): host, region m30_A188, pair m30_Cs188p0 and the A1 cells."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    A1 = pdr.Archive(S2, cd, fig, c46, c2=False)
    x = {"host": A1.c1_cell("s2_m30_host", "relaxed"), "Vrel": A1.c1_cell("s2_m30_VA188", "relaxed"),
         "Dstart": A1.c1_cell("s2_m30_Cs188p0_novac", "start"), "DVstart": A1.c1_cell("s2_m30_Cs188p0_vac", "start"),
         "region": c46.check_region_record(c46.load_record(A1.L.region("c1", "m30", "A", 188))),
         "pair": c46.load_record(A1.L.pair("c1", "m30", "Cs", 188, 0))}
    A1.t1.close()
    return x


def _mic(cd, v, cell):
    return float(np.linalg.norm(cd.mic(v, cell)[0]))


def _fa_groups(cd, at, c):
    """(nitrogens, {nitrogen: its two hydrogens}, the carbon's hydrogens) of the FA whose carbon is c in at."""
    s, cell = np.array(at.get_chemical_symbols()), at.cell.array
    near = lambda i, el, d: [int(j) for j in np.flatnonzero(s == el)
                             if _mic(cd, at.positions[j] - at.positions[i], cell) < d]
    ns = near(c, "N", 1.6)
    assert s[c] == "C" and len(ns) == 2, f"FA skeleton of carbon {c}"
    hn = {n: near(n, "H", 1.25) for n in ns}
    assert all(len(h) == 2 for h in hn.values()), f"FA amino groups of carbon {c}"
    return ns, hn, near(c, "H", 1.25)


def _exchange_fa(cd, at, c):
    """The two amino groups of an FA exchanged in place: the same configuration under other labels."""
    ns, hn, _ = _fa_groups(cd, at, c)
    ga, gb = [ns[0]] + hn[ns[0]], [ns[1]] + hn[ns[1]]
    pa, pb = at.positions[ga].copy(), at.positions[gb].copy()
    at.positions[ga], at.positions[gb] = pb, pa


def _rotate_fa(cd, at, c, deg, axis=(0.3, 0.5, 0.81)):
    """An FA turned rigidly about its carbon by deg (Rodrigues)."""
    ns, hn, hc = _fa_groups(cd, at, c)
    idx = ns + [h for n in ns for h in hn[n]] + hc
    k = np.asarray(axis, float) / np.linalg.norm(axis)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    t = np.radians(deg)
    R = np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * (K @ K)
    at.positions[idx] = at.positions[c] + cd.mic(at.positions[idx] - at.positions[c], at.cell.array) @ R.T


SHIFT_R = np.array([0.0, 0.1, 0.0])           # host_R's final against the S2-relaxed host, at the atoms the routes move


def _fr_route(tmp, route, n_cfg=5):
    """A synthetic fr archive for one route of S2B 2. host_R's final is the S2-relaxed host with the atoms that routes
    'V' and 'D' move shifted by SHIFT_R, so that item 4's reference (the S2-relaxed host) is not host_R's final; V+_R
    = host_R without I127; D and D+V+ from their parents through the pair legs (old_to_new), Cs at its A1 start
    position; so every check-5 displacement is exactly zero. Routes: 'pass'; 'V' (the gated inorganic atom of highest
    host index of V+_R moved 0.35 A, beyond the deleted FA; D and D+V+ not run); 'D' (the same in Cs D; D+V+ not run);
    'DV' (in Cs D+V+); 'inv' (FA188's two amino groups exchanged in V+_R); 'fa2' (in Cs D: the gated FA farthest from
    the site turned 25 deg about its carbon, the next one exchanged, the nearest gated inorganic atom moved 0.1 A;
    D+V+ not run)."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    x = _fr_inputs()
    host, reg, pair = x["host"], x["region"], x["pair"]
    lv, ld = pair["legs"]["vac"], pair["legs"]["novac"]
    rows_of = lambda kind, ch, par, leg: cd.d5_check(kind, ch, par, host, reg, leg)["rows"]
    top = lambda rows: max((r for r in rows if r["gated"] and r["kind"] == "inorganic"), key=lambda r: r["host"])
    shifted = sorted({top(rows_of("V", _substitute(host, None, None), host, None))["host"],
                      top(rows_of("D", _substitute(host, ld, x["Dstart"]), host, ld))["host"]})
    hostR = host.copy(); hostR.calc = None
    hostR.positions[shifted] += SHIFT_R
    V = _substitute(hostR, None, None)
    D = _substitute(hostR, ld, x["Dstart"])
    DV = _substitute(V, lv, x["DVstart"])
    fin = {FR["host"]: hostR, FR["V"]: V, FR["D"]: D, FR["DV"]: DV}
    cell, u = host.cell.array, np.array([0.35, 0.0, 0.0])
    info = {"route": route, "S2host": host, "shifted": shifted}
    if route in ("V", "D", "DV"):
        kind, ch, par, leg = {"V": ("V", V, hostR, None), "D": ("D", D, hostR, ld), "DV": ("DV", DV, V, lv)}[route]
        rows = rows_of(kind, ch, par, leg)
        assert all(r["dr_A"] < 1e-9 for r in rows), f"{route}: the synthetic pair is not at zero displacement"
        o = top(rows)
        ch.positions[o["child"]] += u
        info.update(host=o["host"], child=o["child"], parent=o["parent"])
        if route == "V":
            fin[FR["D"]] = fin[FR["DV"]] = None
        if route == "D":
            fin[FR["DV"]] = None
        if route == "DV":
            info["Vrel"] = x["Vrel"]
    if route == "inv":
        assert host.get_chemical_symbols()[188] == "C", "FA188's carbon"
        _exchange_fa(cd, V, 188 - 1)                                  # FA188's carbon in the V numbering
        info.update(host=188, child=187)
    if route == "fa2":
        rows = rows_of("D", D, hostR, ld)
        assert all(r["dr_A"] < 1e-9 for r in rows), "fa2: the synthetic pair is not at zero displacement"
        fa = sorted((r for r in rows if r["gated"] and r["kind"] == "FA"), key=lambda r: -r["d_host_A"])
        ino = min((r for r in rows if r["gated"] and r["kind"] == "inorganic"), key=lambda r: r["d_host_A"])
        assert len(fa) >= 2 and all(r["child"] < 188 for r in fa[:2]) and ino["host"] not in shifted
        _rotate_fa(cd, D, fa[0]["child"], 25.0)
        _exchange_fa(cd, D, fa[1]["child"])
        D.positions[ino["child"]] += np.array([0.1, 0.0, 0.0])
        fin[FR["DV"]] = None
        info.update(rot=fa[0], exc=fa[1], ino=ino)
    plant = {FR["V"]: {"end_rule": {"outcome": "accepted_converged", "dF_200_180_meV": -1.234},
                       "s2b_canary": {"delta_far_meV": 1.5, "Eb_A1_meV": -2.5, "F_k0_eV": -3.5, "ok": 1}}}
    fin, starts, parts = _write_archive(tmp, "fr", _fr_jobs(), fin, reading="invariant", n_cfg=n_cfg, plant=plant)
    return fin, starts, parts, info


_ROUTES = {}


def _route(name):
    """A route archive, built once in the self-test's temporary directory and read many times."""
    if name not in _ROUTES:
        d = tempfile.mkdtemp(prefix=f"frgeom_{name}_", dir=_ROUTES["_tmp"])
        fin, starts, parts, info = _fr_route(d, name)
        info["starts"] = starts
        info["stub_any_parts"] = _stub_g(starts, fin, 5)              # for copies of the archive
        _ROUTES[name] = (d, _stub_g(starts, fin, 5, parts), fin, info)
    return _ROUTES[name]


def _read(name, **kw):
    d, g, fin, info = _route(name)
    lines = []
    ok, sm = read(d, out=lines.append, campaign="fr", g_reader=g, **kw)
    return ok, sm, lines, fin, info


def _copy(name):
    """A copy of a route archive, to be edited (the route itself is read many times); (root, finals, info)."""
    d, g, fin, info = _route(name)
    root = os.path.join(tempfile.mkdtemp(prefix="frgeom_cp_", dir=_ROUTES["_tmp"]), "a")
    shutil.copytree(d, root, symlinks=True)
    return root, fin, info


def _read_root(root, g):
    """read() on a synthetic root; a raise is a failed case (S2B 6b: a mismatch is printed, and the read ends)."""
    lines = []
    try:
        ok, sm = read(root, out=lines.append, campaign="fr", g_reader=g)
    except Exception as e:
        raise AssertionError(f"the read raised {type(e).__name__} ({str(e)[:50]})")
    return ok, sm, lines


def _raw(root, lab, suffix=".a2.json"):
    return os.path.join(root, "fr", "raw", lab + suffix)


def _edit_json(path, fn):
    with open(path) as fh:
        d = json.load(fh)
    fn(d)
    with open(path, "w") as fh:
        json.dump(d, fh, indent=1)


def _setter(*keys, value):
    def f(d):
        for k in keys[:-1]:
            d = d[k]
        d[keys[-1]] = value
    return f


def _edit_validity(root, lab, fn):
    """A validity file edited, its new sha256 carried into the record (so only the target check differs)."""
    vp = _raw(root, lab, VAL)
    _edit_json(vp, fn)
    with open(vp, "rb") as fh:
        sha = hashlib.sha256(fh.read()).hexdigest()
    _edit_json(_raw(root, lab), _setter("validity_final", "sha256", value=sha))


def _retar(root, drop=(), replace=None):
    """structures.tar.gz of a copied fr archive rewritten without the members in drop, with replace {member: bytes}."""
    p = os.path.join(root, "fr", "structures.tar.gz")
    with tarfile.open(p) as tf:
        mem = [(m.name, tf.extractfile(m).read()) for m in tf.getmembers() if m.isfile()]
    with tarfile.open(p, "w:gz") as tf:
        for name, b in mem:
            if name in drop:
                continue
            b = (replace or {}).get(name, b)
            ti = tarfile.TarInfo(name)
            ti.size = len(b)
            tf.addfile(ti, io.BytesIO(b))


def _member(lab):
    return f"a2/{lab}/{lab}.final.extxyz"


def _new_cell(root, lab):
    """The final geometry of lab rewritten with a cell 0.1 % larger and the same positions (record sha256 updated)."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    with tarfile.open(os.path.join(root, "fr", "structures.tar.gz")) as tf:
        b = tf.extractfile(_member(lab)).read()
    at = pdr.atoms_from_bytes(b)
    x = at.copy()
    x.set_cell(at.cell.array * 1.001, scale_atoms=False)
    q = os.path.join(os.path.dirname(root), "cell.extxyz")
    c46.write_cell(q, x)
    with open(q, "rb") as fh:
        nb = fh.read()
    assert np.array_equal(pdr.atoms_from_bytes(nb).positions, at.positions), "the rewritten final moved"
    _retar(root, replace={_member(lab): nb})
    _edit_json(_raw(root, lab), _setter("final_geometry", "sha256", value=pdr.sha256_bytes(nb)))


def _g_edit(g0, lab, fn):
    """The stub G with the configurations of one relaxation edited."""
    def g(q47_, parts, *, mapping, ranks, label):
        pr, pos = g0(q47_, parts, mapping=mapping, ranks=ranks, label=label)
        return pr, (fn(pos) if label == lab else pos)
    return g


def _rm(root, lab, *suffixes):
    for s in suffixes:
        if os.path.exists(_raw(root, lab, s)):
            os.remove(_raw(root, lab, s))


def _no_check(root, lab):
    """A complete record without validity_final (the section 11 check not evaluated), its validity file removed."""
    _edit_json(_raw(root, lab), lambda r: r.pop("validity_final"))
    _rm(root, lab, VAL)


def _pending_v(root):
    """V+_R pending (no final geometry, no validity_final), Cs D and D+V+ without records: FR not ended at V+_R."""
    _edit_json(_raw(root, FR["V"]), lambda r: (r.__setitem__("status", "pending"), r.pop("validity_final"),
                                                r.pop("final_geometry")))
    _rm(root, FR["V"], VAL)
    for lab in (FR["D"], FR["DV"]):
        _rm(root, lab, ".a2.json", VAL)


def _lines_per_pair(sm, n_cfg=5):
    return {ch: 2 * n_cfg * len(objs) for ch, objs in sm["item5_objects"].items()}


def _item2(lines):
    i = next(i for i, l in enumerate(lines) if l.startswith("ITEM 2"))
    j = next(i for i, l in enumerate(lines) if l.startswith("ITEM 3"))
    return lines[i + 1:j]


def _traj(lines, ch, pa, role, which):
    """{k: printed values} of one item-5 block: the object of this role, in the child or the parent cell."""
    hd = next(i for i, l in enumerate(lines) if l.startswith(f"  {ch} against {pa}; ") and f"({role}); {which} " in l)
    got = {}
    for l in lines[hd + 1:]:
        if not l.startswith("    "):
            break
        v = l.split()
        got[int(v[0])] = tuple(map(float, v[1:]))
    return got


def _kabsch_deg(P, Q):
    """Angle of the best proper rotation of the centred set P onto the centred set Q, by SVD (D5 uses quaternions)."""
    P, Q = np.asarray(P, float) - np.mean(P, axis=0), np.asarray(Q, float) - np.mean(Q, axis=0)
    U, _, Vt = np.linalg.svd(P.T @ Q)
    R = Vt.T @ np.diag([1.0, 1.0, np.sign(np.linalg.det(Vt.T @ U.T))]) @ U.T
    return float(np.degrees(np.arccos(np.clip((np.trace(R) - 1.0) / 2.0, -1.0, 1.0))))


def _check_common(ok, sm, lines, item1, pairs, stop, n1=None, flagged=False):
    assert ok, "the read did not end"
    assert sm["stop"] == stop, f"early stop {sm['stop']}, expected {stop}"
    n1 = n1 or {lab: 17 for lab in item1}
    assert list(sm["item1"]) == item1 and all(sm["item1"][l] == (n1[l],) * 2 for l in item1), sm["item1"]
    assert sm["pairs"] == pairs and list(sm["item2"]) == [c for c, _ in pairs], (sm["pairs"], list(sm["item2"]))
    assert sm["item3"] == [c for c, _ in pairs] and list(sm["item5_objects"]) == [c for c, _ in pairs]
    assert sm["item5_lines"] == sum(_lines_per_pair(sm).values()), "item 5 lines"
    assert not any(l.endswith("READINGS DISAGREE") or "DIFFER" in l for l in lines) and lines[-1].startswith("END"), \
        "printed items"
    assert flagged or not any("pass only under the invariant reading" in l for l in _item2(lines)), \
        "an ordinary pass flagged as invariant-only"
    assert "scripts/49 fr_progress agrees" in lines[1], lines[1]
    for lab in FR_ORDER:
        assert any(l.startswith(f"  {lab}: ") for l in lines) == (lab in item1), f"{lab}: item 1"


# ---- self-test: cases ----------------------------------------------------------------------------------------------

def t_c2():
    """The C2 synthetic read of part_d_read.self_test_read through the generalised code paths: the output equals
    part_d_read.read's line for line, item 2 fails exactly VB76 and Sr76o0_vac, item 4 finds the child moved and the
    parent moved, and a changed validity file ends the read."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    tmp = tempfile.mkdtemp(prefix="frgeom_c2_", dir=_ROUTES["_tmp"])
    try:
        fin, starts, mA, mB = _c2_archive(tmp)
        g = _stub_g(starts, fin, 5)
        mine, ref = [], []
        ok, sm = read(tmp, out=mine.append, campaign="c2", g_reader=g)
        ok_ref, _ = pdr.read(tmp, out=ref.append, g_reader=g)
        assert ok and ok_ref and mine == ref, "the generalised C2 read differs from part_d_read.read"
        V, DV = P + "VB76", P + "Sr76o0_vac"
        for ch, four in sm["item2"].items():
            want = ch not in {V, DV}
            assert four == (want,) * 4, f"item 2 for {ch}"
        it4 = sm["item4"]
        assert set(it4) == {V, DV}, "item 4 pairs"
        a = [t for t in it4[V] if t[1] == mA["host"]]
        assert len(a) == 1 and a[0][2] > 0.25 and a[0][3] < 1e-9, "item 4: the child moved (VB76 against hostB76)"
        b = [t for t in it4[DV] if t[1] == mB["host"]]
        assert len(b) == 1 and abs(b[0][3] - 0.35) < 1e-6 and b[0][2] < 0.25, "item 4: the parent moved"
        vb = os.path.join(tmp, "c2", "raw", f"{P}VB136.validity_final.json")
        txt = open(vb).read(); open(vb, "w").write(txt.replace('"label"', '"label" ', 1))
        mine2, ref2 = [], []
        ok2, _ = read(tmp, out=mine2.append, campaign="c2", g_reader=g)
        ok2r, _ = pdr.read(tmp, out=ref2.append, g_reader=g)
        assert not ok2 and not ok2r and mine2 == ref2 and not any(l.startswith("ITEM 2") for l in mine2), \
            "a changed validity file must end the C2 read"
        return f"C2: {len(mine)} lines equal to part_d_read.read; item 2, 4, 5 ({sm['item5_lines']} lines) as there"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t_asite_map():
    """The A-site substitution of m30_Cs188p0 (FA188: 8 atoms deleted, Cs appended) written out by hand, against the
    maps the read uses (D5) and scripts/46, element by element on the public C1 cells, and the synthetic FA188 cells
    built from old_to_new against the C1 A1 starts."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    x = _fr_inputs()
    host, pair, reg = x["host"], x["pair"], x["region"]
    ld, lv = pair["legs"]["novac"], pair["legs"]["vac"]
    hs = host.get_chemical_symbols()
    assert ld["deleted"] == list(range(188, 196)) and sorted(hs[i] for i in ld["deleted"]) == \
        sorted(["C", "N", "N"] + ["H"] * 5), "novac: the deleted FA188"
    assert lv["deleted"] == list(range(187, 195)) and ld["members"] == ld["added"] == [225] and \
        lv["members"] == lv["added"] == [224], "legs"
    d_of = lambda h: h if h < 188 else h - 8                      # host -> D (h not in 188-195)
    v_of = lambda h: h if h < VI else h - 1                       # host -> V (h != 127)
    dv_of = lambda jv: jv if jv < 187 else jv - 8                 # V -> D+V (jv not in 187-194)
    want = {"D": ({d_of(h): h for h in range(233) if not 188 <= h <= 195},) * 2}
    dv_p = {dv_of(jv): jv for jv in range(232) if not 187 <= jv <= 194}
    want["DV"] = ({c: (jv if jv < VI else jv + 1) for c, jv in dv_p.items()}, dv_p)
    n = 0
    for kind, leg in (("D", ld), ("DV", lv)):
        got = index_maps(cd, kind, len(host), leg)
        assert got == want[kind], f"{kind}: the read's index maps differ from the hand-written A-site map"
        assert got == c46.cell_maps(kind, built=leg, n_host=len(host)), f"{kind}: scripts/46 maps differ"
        assert cd.free_section4(kind, reg["free"], leg) == c46.free_in_cell(reg, kind, built=leg), f"{kind}: free sets"
        n += len(got[0])
    assert want["D"][0][224] == 232 and want["DV"][0][223] == 232 and want["DV"][1][223] == 231
    assert want["DV"][0][127] == 128 and 225 not in want["D"][0] and 224 not in want["DV"][0]
    # the synthetic FA188 cells: built here from old_to_new alone, against the C1 starts (numbers and positions)
    V = host.copy(); del V[VI]
    for kind, par, leg, st in (("D", host, ld, x["Dstart"]), ("DV", V, lv, x["DVstart"])):
        o = {int(h): int(c) for h, c in leg["old_to_new"].items()}
        nums = np.zeros(len(o) + len(leg["added"]), int); pos = np.zeros((len(nums), 3))
        for h, c in o.items():
            nums[c], pos[c] = par.numbers[h], par.positions[h]
        for m in leg["added"]:
            nums[m], pos[m] = st.numbers[m], st.positions[m]
        assert np.array_equal(nums, st.numbers) and st.get_chemical_symbols()[leg["added"][0]] == "Cs", kind
        if kind == "D":                                            # the D start is the relaxed host plus Cs
            assert np.abs(pos - st.positions).max() == 0.0, "D: positions of the mapped atoms"
        syn = _substitute(par, leg, st)
        assert np.array_equal(syn.numbers, nums) and np.abs(syn.positions - pos).max() == 0.0, f"{kind}: _substitute"
        c2h, c2p = want[kind]
        ss, ps = st.get_chemical_symbols(), par.get_chemical_symbols()
        assert all(ss[c] == ps[p] for c, p in c2p.items()), f"{kind}: elements under the map"
    return f"A-site map: {n} mapped indices of D and D+V+ equal to the hand-written map, D5 and scripts/46; FA188 cells"


def _item4_against_host(cd, sm, fin, info, ch, pa):
    """Item 4 of a V+ or D child against independent recomputations: the reference is the S2-relaxed host, which
    host_R's final leaves by SHIFT_R at the moved atom (S2B 6b); k = 0 is the two A1 starts."""
    S, st = info["S2host"], info["starts"]
    c, h = info["child"], info["host"]
    cell = fin[ch].cell.array
    (t,) = sm["item4"][ch]
    want = (_mic(cd, fin[ch].positions[c] - S.positions[h], cell),
            _mic(cd, fin[pa].positions[h] - S.positions[h], cell),
            _mic(cd, st[ch].positions[c] - st[pa].positions[h], cell))
    assert abs(want[1] - np.linalg.norm(SHIFT_R)) < 1e-6 and h in info["shifted"], "host_R's final at the moved atom"
    assert t[:2] == (c, h) and all(abs(a - b) < 1e-9 for a, b in zip(t[2:], want)), (t, want)
    return t, S, st, c, h, cell


def t_r1():
    ok, sm, lines, fin, info = _read("pass")
    _check_common(ok, sm, lines, FR_ORDER, FR_PAIRS, None)
    assert all(v == (True,) * 5 for v in sm["item2"].values()) and sm["item4"] == {}, (sm["item2"], sm["item4"])
    assert {ch: [o[1] for o in objs] for ch, objs in sm["item5_objects"].items()} == \
        {FR["V"]: ["inorganic", "FA"], FR["D"]: ["inorganic", "FA"], FR["DV"]: ["inorganic", "FA"]}
    assert sm["item5_objects"][FR["V"]][1][2] == 188, "the gated FA of the V+-host pair is FA188"
    assert all(g["r46_equal"] and g["record_equal"] for g in sm["gated"].values()), "gated objects"
    return f"all four complete: 3 pairs pass every reading, none flagged; gated objects and counts equal; no failing " \
           f"object; {sm['item5_lines']} item-5 lines"


def t_r2():
    pdr, cd, fig, q47, c46, g49, gd = tools()
    ok, sm, lines, fin, info = _read("V")
    V, H = FR["V"], FR["host"]
    _check_common(ok, sm, lines, FR_ORDER[:2], FR_PAIRS[:1], (V, "check"))
    assert sm["item2"][V] == (False,) * 5, sm["item2"]
    t, S, st, c, h, cell = _item4_against_host(cd, sm, fin, info, V, H)
    assert t[:2] == (h - 1, h) and abs(t[2] - np.hypot(0.35, 0.1)) < 1e-6, t
    k2 = lambda lab, i: st[lab].positions[i] + (fin[lab].positions[i] - st[lab].positions[i]) * 2 / 4   # stub G
    tc, tp = _traj(lines, V, H, "largest |dr|", "child"), _traj(lines, V, H, "largest |dr|", "parent")
    assert abs(tc[2][0] - _mic(cd, k2(V, c) - S.positions[h], cell)) < 6e-4, tc
    assert abs(tp[2][0] - _mic(cd, k2(H, h) - S.positions[h], cell)) < 6e-4, tp
    assert abs(tc[4][0] - t[2]) < 6e-4 and abs(tp[4][0] - t[3]) < 6e-4, (tc, tp)
    return f"stop at V+_R (check): host {h} -> V {c}: child {t[2]:.3f}, parent {t[3]:.3f} A from the S2-relaxed " \
           f"host; k = 0 and trajectory recomputed"


def t_r3():
    pdr, cd, fig, q47, c46, g49, gd = tools()
    ok, sm, lines, fin, info = _read("D")
    _check_common(ok, sm, lines, FR_ORDER[:3], FR_PAIRS[:2], (FR["D"], "check"))
    assert sm["item2"][FR["V"]] == (True,) * 5 and sm["item2"][FR["D"]] == (False,) * 5, sm["item2"]
    assert info["host"] > 195, "the moved atom does not lie beyond the deleted FA"
    t, S, st, c, h, cell = _item4_against_host(cd, sm, fin, info, FR["D"], FR["host"])
    assert t[:2] == (h - 8, h) and abs(t[2] - np.hypot(0.35, 0.1)) < 1e-6, t
    return f"stop at Cs D (check): host {h} -> D {c} (FA188 deleted); child moved, host_R {t[3]:.3f} A from the " \
           f"reference; k = 0 recomputed"


def t_r4():
    pdr, cd, fig, q47, c46, g49, gd = tools()
    ok, sm, lines, fin, info = _read("DV")
    _check_common(ok, sm, lines, FR_ORDER, FR_PAIRS, (FR["DV"], "check"))
    assert all(sm["item2"][FR[r]] == (True,) * 5 for r in ("V", "D")) and sm["item2"][FR["DV"]] == (False,) * 5
    h = info["host"]
    jv = h - 1
    assert jv > 194, "the moved atom does not lie beyond the deleted FA"
    (t,) = sm["item4"][FR["DV"]]
    cell, Vf, Vr = fin[FR["V"]].cell.array, fin[FR["V"]].positions, info["Vrel"].positions
    want_p = _mic(cd, Vf[jv] - Vr[jv], cell)
    want_c = _mic(cd, fin[FR["DV"]].positions[jv - 8] - Vr[jv], cell)
    assert want_p > 1e-3, "the A1 V+_R reference does not differ from the V+_R final at the moved atom"
    assert t[:2] == (jv - 8, h) and abs(t[2] - want_c) < 1e-9 and abs(t[3] - want_p) < 1e-9, (t, want_c, want_p)
    assert any("reference A1 s2_m30_VA188 geometry" in l for l in lines)
    return f"stop at Cs D+V+ (check): host {h} -> V {jv} -> D+V+ {jv - 8}; reference the A1 V+_R geometry"


def t_r5():
    """FA188's amino groups exchanged in V+_R: valid only under the invariant reading, flagged in item 2; the printed
    words of items 1, 2 and 3 (the output is the published result, S2B 6b), not the summary alone."""
    ok, sm, lines, fin, info = _read("inv")
    V, H = FR["V"], FR["host"]
    _check_common(ok, sm, lines, FR_ORDER, FR_PAIRS, None, flagged=True)
    assert sm["item2"][V] == (True, True, False, False, False), sm["item2"][V]
    assert sm["item2"][FR["D"]] == sm["item2"][FR["DV"]] == (True,) * 5
    vline = next(l for l in lines if l.startswith(f"  {V} against"))
    assert vline.startswith(f"  {V} against {H}: invariant reading (deciding): record pass, D5 pass; as written: "
                            f"record FAIL, D5 FAIL, R46 FAIL; pass only under the invariant reading (flagged"), vline
    assert sum("pass only under the invariant reading" in l for l in _item2(lines)) == 1, "flagged elsewhere"
    l1 = next(l for l in lines if l.startswith(f"  {V}: "))
    assert l1.startswith(f"  {V}: valid True; failed []; valid as written False; failed as written [5]; invariant "
                         f"only True; check-5 reading invariant; parent {H}; parent_final True; "), l1
    i3 = next(i for i, l in enumerate(lines) if l.startswith("ITEM 3"))
    row = next(l for l in lines[i3:] if l.startswith("    FA  187  188  "))
    assert row.endswith("  FAIL  pass"), row                       # as written FAIL, invariant reading pass
    (t,) = sm["item4"][V]
    assert t[:2] == (187, 188) and t[2] < 1e-9 and t[3] < 1e-9, t
    fa = next(l for l in lines if l.startswith("    FA child 187 host 188: child final"))
    rot, rotx = map(float, re.search(r"rot ([\d.]+) deg \(exchanged ([\d.]+)\)", fa).groups())
    assert rot > 90 and rotx < 0.05 and "FAIL as written, pass invariantly" in fa, fa
    return "FA188 amino groups exchanged in V+_R: valid only invariantly, flagged; readings agree"


def t_fa2():
    """Two gated FA of Cs D: one turned 25 deg (fails under both readings), one exchanged (fails only as written). Item
    5 prints three objects (largest |dr|; largest rotation under the invariant reading, the turned FA; largest
    rotation as written, the exchanged FA); item 4's k = 0 column and an item-5 trajectory line against independent
    recomputations (SVD angle)."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    ok, sm, lines, fin, info = _read("fa2")
    D, H = FR["D"], FR["host"]
    _check_common(ok, sm, lines, FR_ORDER[:3], FR_PAIRS[:2], (D, "check"))
    assert sm["item2"][D] == (False,) * 5 and sm["item2"][FR["V"]] == (True,) * 5, sm["item2"]
    rot, exc, ino = info["rot"], info["exc"], info["ino"]
    assert sm["item5_objects"][D] == [("largest |dr|", "inorganic", ino["host"]),
                                      ("largest rotation, invariant reading", "FA", rot["host"]),
                                      ("largest rotation as written", "FA", exc["host"])], sm["item5_objects"][D]
    heads = {l.split("; ")[1] for l in lines if l.startswith(f"  {D} against {H}; ")}
    assert len(heads) == 3, heads
    S, st = info["S2host"], info["starts"]
    cell = fin[D].cell.array
    it4 = {t[0]: t for t in sm["item4"][D]}
    assert set(it4) == {rot["child"], exc["child"]}, it4
    for o in (rot, exc):
        t = it4[o["child"]]
        k0 = _mic(cd, st[D].positions[o["child"]] - st[H].positions[o["host"]], cell)
        assert t[2] < 1e-9 and t[3] < 1e-9 and abs(t[4] - k0) < 1e-9 and k0 > 1e-4, (t, k0)
    verdict = lambda o: next(l for l in lines
                             if l.startswith(f"    FA child {o['child']} host {o['host']}: child final"))
    assert verdict(rot).endswith("D5: FAIL as written, FAIL invariantly") and \
        verdict(exc).endswith("D5: FAIL as written, pass invariantly")
    ns = _fa_groups(cd, fin[H], rot["host"])[0]                    # parent (host_R) numbering; D = host below 188
    sk = [rot["host"]] + ns
    rel = lambda x: np.vstack([np.zeros(3), cd.mic(x[sk[1:]] - x[sk[0]], cell)])
    tr = _traj(lines, D, H, "largest rotation, invariant reading", "child")
    for k in (2, 4):
        xk = st[D].positions + (fin[D].positions - st[D].positions) * k / 4                # stub G
        want = (_mic(cd, xk[sk[0]] - S.positions[sk[0]], cell), _kabsch_deg(rel(S.positions), rel(xk)),
                _kabsch_deg(rel(S.positions), rel(xk)[[0, 2, 1]]))
        assert all(abs(a - b) < tol for a, b, tol in zip(tr[k], want, (6e-4, 0.06, 0.06))), (k, tr[k], want)
    assert abs(tr[4][1] - 25.0) < 0.06, tr[4]
    return f"Cs D: FA {rot['host']} turned 25 deg, FA {exc['host']} exchanged: three item-5 objects; k = 0 and the " \
           f"trajectory (k = 2: {tr[2][1]:.1f} deg) recomputed"


def t_states():
    """Read states reached through the early stop only, on copies of the 'pass' archive: Cs D+V+ complete without
    validity_final; Cs D+V+ complete without a final geometry; V+_R pending with Cs D and D+V+ unrecorded; host_R
    complete without validity_final and the later cells unrecorded (fr_progress: a check still waiting; a later record
    would contradict S2B 2, a case of t_mismatch), or not_run_gate (FR ended there)."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    H, V, D, DV = FR_ORDER
    no_vf = "no validity_final (the section 11 check was not evaluated)"
    states = [("P1", lambda r: _no_check(r, DV), (DV, "check_not_evaluated"), FR_PAIRS[:2],
               {H: 17, V: 17, D: 17, DV: 7}, f"  {DV}: {no_vf}"),
              ("P2", lambda r: (_no_check(r, DV), _edit_json(_raw(r, DV), _setter("final_geometry", value=None))),
               (DV, "check_not_evaluated"), FR_PAIRS[:2], {H: 17, V: 17, D: 17},
               f"  {DV}: complete without a final geometry (nothing to check)"),
              ("P3", _pending_v, (V, "not ended"), [], {H: 17}, "  no FR pair whose check 5 was evaluated"),
              ("P4", lambda r: (_pending_v(r), _rm(r, V, ".a2.json"), _no_check(r, H)), (H, "check_not_evaluated"),
               [], {H: 7}, f"  {H}: {no_vf}"),
              ("P5", lambda r: (_no_check(r, H), _not_run(r, V, D, DV)), (H, "check_not_evaluated"), [], {H: 7},
               f"  {H}: {no_vf}")]
    for name, edit, stop, pairs, n1, wording in states:
        root, fin, info = _copy("pass")
        edit(root)
        ok, sm, lines = _read_root(root, info["stub_any_parts"])
        assert ok and lines[-1].startswith("END") and "scripts/49 fr_progress agrees" in lines[1], (name, lines[:2])
        assert sm["stop"] == stop and sm["pairs"] == pairs, (name, sm["stop"], sm["pairs"])
        assert sm["item1"] == {l: (n, n) for l, n in n1.items()}, (name, sm["item1"])
        assert any(l.startswith(wording) for l in lines), (name, wording)
        assert list(sm["item2"]) == [c for c, _ in pairs] and not sm["mismatch"], name
    return "D+V+ without validity_final, D+V+ without a final geometry, V+_R pending, host_R's check waiting or not " \
           "evaluated at the end: stops, pairs, item-1 counts and wording as fixed"


def t_stop():
    """The early stop at every position and of every kind (record leaves, through GuardedS2b), against scripts/49
    fr_progress, and the pairs read up to it; a check still waiting while a later cell has not ended; accepted_plateau
    accepts a cell."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    ok_rec = {"status": "complete", "end_rule": {"outcome": "accepted_converged", "dF_200_180_meV": None},
              "validity_final": {"valid": True}}
    kinds = {"end_rule": dict(ok_rec, end_rule={"outcome": "unconverged_cap"}),
             "check": dict(ok_rec, validity_final={"valid": False}),
             "check_not_evaluated": {k: v for k, v in ok_rec.items() if k != "validity_final"},
             "missing": {"status": "missing"}, "not_started_cap": {"status": "not_started_cap"},
             "killed_by_gate": {"status": "killed_by_gate"}, "not ended": {"status": "pending"}, "no record": None}
    wrap = lambda d, lab: None if d is None else gd.GuardedS2b(json.loads(json.dumps(d)), lab)
    n = 0
    for i, lab in enumerate(FR_ORDER):
        for kind, rec in kinds.items():
            recs = {l: wrap(ok_rec if j < i else rec if j == i else {"status": "not_run_gate"}, l)
                    for j, l in enumerate(FR_ORDER)}
            stop, agree = fr_stop(g49, pdr, recs)
            assert stop == (i, lab, "not ended" if kind == "no record" else kind) and agree, (lab, kind, stop, agree)
            assert [c for c, _ in pairs_up_to(stop, FR_PAIRS)] == [c for c, _ in FR_PAIRS if FR_ORDER.index(c) <= i]
            n += 1
    m = 0
    for i, lab in enumerate(FR_ORDER[:-1]):            # fr_progress (final=False): the check waits, passed None
        for later in ({"status": "pending"}, None):
            recs = {l: wrap(ok_rec if j < i else kinds["check_not_evaluated"] if j == i else later if j == i + 1
                            else {"status": "not_run_gate"}, l) for j, l in enumerate(FR_ORDER)}
            stop, agree = fr_stop(g49, pdr, recs)
            assert stop == (i, lab, "check_not_evaluated") and agree, ("waiting check", lab, later, stop, agree)
            m += 1
    plateau = {l: wrap(dict(ok_rec, end_rule={"outcome": "accepted_plateau"}), l) for l in FR_ORDER}
    assert fr_stop(g49, pdr, plateau) == (None, True), "accepted_plateau must accept a cell"
    assert pairs_up_to(None, FR_PAIRS) == FR_PAIRS
    return f"{n} stops (8 kinds at 4 positions) and {m} waiting checks agree with scripts/49 fr_progress; pairs up " \
           f"to the stop; plateau accepted"


def t_endrule():
    """FR stopped by the end rule of Cs D (unconverged_cap) after its check was evaluated: the D-host pair is still
    read (its check 5 was evaluated), the D+V+ cell is not."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    root, fin, info = _copy("pass")
    raw = os.path.join(root, "fr", "raw")
    _edit_json(_raw(root, FR["D"]), _setter("end_rule", "outcome", value="unconverged_cap"))
    json.dump({"schema": "s2-a2-1", "label": FR["DV"], "campaign": "fr", "status": "not_run_gate", "parts": []},
              open(os.path.join(raw, f"{FR['DV']}.a2.json"), "w"))
    ok, sm, lines = _read_root(root, info["stub_any_parts"])
    _check_common(ok, sm, lines, FR_ORDER[:3], FR_PAIRS[:2], (FR["D"], "end_rule"))
    assert all(v == (True,) * 5 for v in sm["item2"].values())
    return "stop at Cs D (end_rule) with its check evaluated: V+-host and D-host read, D+V+ not"


def _r46_edit(orig, kind, edit):
    """R46 of one pair kind with its gated lists edited by edit(lists, r46); R46's verdict and check_partner's (whose
    summaries are left equal) then fail if any gated row reaches a bound of scripts/46 (PARTNER_DR_A, PARTNER_ROT_DEG),
    as check_partner's own rule."""
    c46 = _TOOLS["c46"]
    dr_max, rot_max = c46.PARTNER_DR_A, c46.PARTNER_ROT_DEG

    def f(c46_, k, child, parent, host, region, leg=None):
        r46, cp = orig(c46_, k, child, parent, host, region, leg)
        if k == kind:
            L = r46["lists"]["gated"]
            edit(L, r46)
            if any(r["dr_A"] >= dr_max for r in L["inorganic"]) or \
                    any(r["dr_carbon_A"] >= dr_max or r["rot_deg"] >= rot_max for r in L["fa"]):
                r46["passed"] = cp["passed"] = False
        return r46, cp
    return f


def _add_inorganic(dr, min_index=0):
    """An extra gated inorganic row (an atom D5 does not gate: R46's first reported row from min_index on) at |dr|."""
    def e(L, r46):
        row = next(r for r in r46["lists"]["within_6A_reported"]["inorganic"] if r["index"] >= min_index)
        L["inorganic"].append(dict(row, dr_A=dr))
    return e


def _set_fa(**fields):
    """R46's first gated FA row with fields replaced (|dr| of its carbon, rotation)."""
    def e(L, r46):
        L["fa"][0] = dict(L["fa"][0], **fields)
    return e


def _add_fa(carbon):
    """An extra gated FA row, passing, for a carbon that neither R46 nor D5 gates."""
    def e(L, r46):
        L["fa"].append(dict(L["fa"][0], carbon=carbon))
    return e


def _read_r46(kind, edit):
    """read() of the 'pass' route with R46 of one pair kind edited (scaffolding; a raise is a failed case)."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    d, gr, fin, info = _route("pass")
    orig, lines = cd.r46_for, []
    try:
        cd.r46_for = _r46_edit(orig, kind, edit)
        ok, sm = read(d, out=lines.append, campaign="fr", g_reader=gr)
    except Exception as e:
        raise AssertionError(f"the read raised {type(e).__name__} ({str(e)[:50]})")
    finally:
        cd.r46_for = orig
    return ok, sm, lines


def _disagree_on(ok, sm, lines, ch):
    it2 = _item2(lines)
    assert ok and lines[-1].startswith("END") and not sm["mismatch"], "the read did not end, or item 1 saw it"
    assert [l.split(" against ")[0].strip() for l in it2 if l.endswith("READINGS DISAGREE")] == [ch], it2
    assert [l for l in lines if l.startswith("    R46 gated inorganic")] and \
        not any("pass only under the invariant reading" in l for l in it2), "R46 lists or flag"


def t_item2():
    """Item 2 beyond the verdicts, on the 'pass' archive, each a disagreement on that pair only with the R46 lists in
    item 3. The record against D5 under the deciding reading (validity.checks.5.passed flipped in V+_R's validity file)
    and as written (passed_as_written flipped); the record's gated counts against D5's (n_inorganic, then n_fa, raised
    in Cs D's); R46's gated lists against D5's (an extra passing inorganic row; an extra passing FA row of a carbon that
    neither gates); objects only R46 fails, just past and at R46's bounds (scripts/46 PARTNER_DR_A, PARTNER_ROT_DEG):
    an inorganic row at the bound and one at 0.01 A past it numbered after the deleted FA (its element and host index
    printed), an FA carbon 0.01 A past it with the rotation unchanged, an FA turned 1 deg past it; each gives the item-4
    line 'D5: not failing (R46 only)' and the item-2 words 'as written: record pass, D5 pass, R46 FAIL'."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    V, D, H = FR["V"], FR["D"], FR["host"]
    c5 = lambda d: d["validity"]["checks"]["5"]
    flip = lambda k: lambda d: c5(d).__setitem__(k, not c5(d)[k])
    bump = lambda k: lambda d: c5(d)["gated"].__setitem__(k, c5(d)["gated"][k] + 1)
    n = 0
    for lab, edit, want, up in ((V, flip("passed"), (False, True, True, True, True), None),
                                (V, flip("passed_as_written"), (True, True, False, True, True), None),
                                (D, bump("n_inorganic"), (True,) * 5, (1, 0)), (D, bump("n_fa"), (True,) * 5, (0, 1))):
        root, fin, info = _copy("pass")
        _edit_validity(root, lab, edit)
        ok, sm, lines = _read_root(root, info["stub_any_parts"])
        _disagree_on(ok, sm, lines, lab)
        g = sm["gated"][lab]
        assert sm["item2"][lab] == want and g["r46_equal"] and sm["item4"] == {}, (sm["item2"][lab], g)
        if up is None:
            assert g["record_equal"], g
        else:
            assert not g["record_equal"] and g["n_record"] == (g["n_d5"][0] + up[0], g["n_d5"][1] + up[1]), g
            assert any(l.startswith("    gated objects:") and l.endswith(", DIFFER") for l in lines)
        n += 1
    d, gr, fin, info = _route("pass")
    x = _fr_inputs()
    r46_0 = cd.r46_for(c46, "D", fin[D], fin[H], x["host"], x["region"], x["pair"]["legs"]["novac"])[0]
    gated_c = {r["carbon"] for r in r46_0["lists"]["gated"]["fa"]}
    fa0 = r46_0["lists"]["gated"]["fa"][0]["carbon"]                   # the FA row edited below
    c_new = next(i for i, e in enumerate(fin[D].get_chemical_symbols()) if e == "C" and i not in gated_c)
    dr_b, rot_b = c46.PARTNER_DR_A, c46.PARTNER_ROT_DEG
    syms, hs = fin[D].get_chemical_symbols(), x["host"].get_chemical_symbols()
    cases = [("passing inorganic", _add_inorganic(0.0), "ino", False),          # (what, edit, object, R46 fails it)
             ("passing FA", _add_fa(c_new), "fa", False),
             ("inorganic at the bound", _add_inorganic(dr_b), "ino", True),
             ("inorganic past the bound, after the deleted FA", _add_inorganic(dr_b + 0.01, min_index=188), "ino",
              True),
             ("FA carbon past the bound", _set_fa(dr_carbon_A=dr_b + 0.01), "fa0", True),
             ("FA rotation past the bound", _set_fa(rot_deg=rot_b + 1.0), "fa0", True)]
    after = 0
    for what, edit, obj, fails in cases:
        ok, sm, lines = _read_r46("D", edit)
        _disagree_on(ok, sm, lines, D)
        g = sm["gated"][D]
        assert g["record_equal"] and g["d5_only"] == ([], []), (what, g)
        if obj == "ino":
            assert not g["r46_equal"] and len(g["r46_only"][0]) == 1 and not g["r46_only"][1], (what, g)
            assert any("R46 lists DIFFER (D5 only: inorganic [], FA []; R46 only: inorganic [" in l for l in lines), what
        elif obj == "fa":
            assert not g["r46_equal"] and g["r46_only"] == ([], [c_new]), (what, g)
            assert any(f"R46 only: inorganic [], FA [{c_new}])" in l for l in lines), what
        else:
            assert g["r46_equal"], (what, g)
        if not fails:
            assert sm["item2"][D] == (True,) * 5 and sm["item4"] == {}, (what, sm["item2"][D], sm["item4"])
            n += 1
            continue
        assert sm["item2"][D] == (True, True, True, True, False) and list(sm["item4"]) == [D], (what, sm["item4"])
        l2 = next(l for l in _item2(lines) if l.startswith(f"  {D} against"))
        assert "as written: record pass, D5 pass, R46 FAIL; READINGS DISAGREE" in l2, (what, l2)
        (t,) = sm["item4"][D]
        line = next(l for l in lines if l.startswith("    ") and f" child {t[0]} host {t[1]}: child final" in l)
        assert line.endswith("; D5: not failing (R46 only)"), (what, line)
        c = g["r46_only"][0][0] if obj == "ino" else fa0
        h = c if c < 188 else c + 8                                     # D numbering: FA188 (8 atoms) deleted
        assert t[:2] == (c, h), (what, t, c, h)
        el = "FA" if obj == "fa0" else syms[c]
        assert el == "FA" or el == hs[h], (what, el, hs[h])
        assert line.startswith(f"    {el} child {c} host {h}: "), (what, line[:50])
        after += c >= 188
        n += 1
    assert after == 1, "no R46-only object numbered after the deleted FA"
    return f"{n} item-2 comparisons, each a disagreement on its pair only: record against D5 under both readings, " \
           f"gated counts (n_inorganic, n_fa), gated lists (inorganic, FA), R46-only failures at and just past " \
           f"R46's bounds ({dr_b} A, {rot_b} deg; inorganic, FA carbon, FA rotation) with element and host index"


def _invalid(root, lab, failed=(4,)):
    """lab's final geometry failing its section 11 check (both readings), in its validity record and in the record's
    validity_final leaves alike (so that item 1's own checks still agree)."""
    leaves = {"valid": False, "failed": list(failed), "valid_as_written": False, "failed_as_written": list(failed)}
    _edit_validity(root, lab, lambda d: d["validity"].update(leaves))
    _edit_json(_raw(root, lab), lambda r: r["validity_final"].update(leaves))


def _not_run(root, *labs):
    """The records of labs replaced by not_run_gate records (scripts/50 a2_phase), their validity files removed."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    for lab in labs:
        _rm(root, lab, ".a2.json", VAL)
        c46.dump_public({"schema": "s2-a2-1", "label": lab, "campaign": "fr", "status": "not_run_gate",
                         "status_reason": "FR early stop (S2B section 2)", "parts": []}, _raw(root, lab))


def t_mismatch():
    """Every item-1 check failing alone ends the read before item 2, and the MISMATCH line names exactly it (on copies
    of an fr archive, each edited so that only the target check differs): seven scripts/49 fr_progress disagreements
    (another cell, another kind, another next cell, passed against a stop, a waiting check against none and against a
    failed check, a refusal of fr_progress for an unknown status); absent files (validity file, final geometry, geometry
    hashes); the validity file and final sha256; the validity record's label and parent label, and the record's
    validity_final.parent; the four geometry hashes; n_config, G's numbering, the final k, G's last configuration
    (2e-6 A); the cell; the check-5 reading of record or validity record, and of both as written; the five validity
    leaves; records after the early stop at host_R (three complete records; among not_run_gate records, a missing
    one, and a complete one without a final geometry)."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    H, V, D, DV = FR_ORDER
    ff = lambda cell, kind: {"first_failure": {"cell": cell, "kind": kind, "end_rule": None}, "next": None,
                             "cells_not_run": [], "passed": False}
    nf = lambda nxt, passed: {"first_failure": None, "next": nxt, "cells_not_run": [], "passed": passed}
    rec = lambda lab, *keys, value: lambda root, info: _edit_json(_raw(root, lab), _setter(*keys, value=value))
    val = lambda lab, *keys, value: lambda root, info: _edit_validity(root, lab, _setter(*keys, value=value))
    gst = lambda lab, fn: lambda root, info: _g_edit(info["stub_any_parts"], lab, fn)

    def vfile_text(root, info):
        p = _raw(root, H, VAL)
        txt = open(p).read(); open(p, "w").write(txt.replace('"label"', '"label" ', 1))

    def shift_last(pos):
        k, out = max(pos), dict(pos)
        out[k] = (pos[k][0], pos[k][1] + np.array([2e-6, 0.0, 0.0]))
        return out
    progress = [("fr_progress: another cell", "pass", None, ff(H, "check")),
                ("fr_progress: another kind", "V", None, ff(V, "end_rule")),
                ("fr_progress: another next cell", "pass", lambda root, info: _pending_v(root), nf(D, None)),
                ("fr_progress: passed against a stop", "V", None, nf(None, True)),
                ("fr_progress: a waiting check against no stop", "pass", None, nf(None, None)),
                ("fr_progress: a waiting check against a failed check", "V", None, nf(None, None)),
                ("fr_progress: refused (GateRefused, an unknown status)", "pass",
                 rec(DV, "status", value="weird_status"), None)]

    def both_as_written(root, info):
        rec(V, "validity_final", "check5_reading", value="as_written")(root, info)
        val(V, "validity", "check5_reading", value="as_written")(root, info)

    def complete_after(root, info):
        _invalid(root, H)

    def missing_after(root, info):
        _invalid(root, H)
        _edit_json(_raw(root, V), _setter("status", value="missing"))
        _not_run(root, D, DV)

    def no_final_after(root, info):
        _invalid(root, H)
        _no_check(root, V)
        _edit_json(_raw(root, V), _setter("final_geometry", value=None))
        _not_run(root, D, DV)
    named = [("validity file absent", lambda root, info: _rm(root, V, VAL), {V: ["vfile"]}),
             ("final geometry absent", lambda root, info: _retar(root, drop=[_member(DV)]), {DV: ["final"]}),
             ("geometry hashes absent", lambda root, info: _edit_validity(root, V, lambda d: d.pop("geometry_sha256")),
              {V: ["gs"]}),
             ("validity file changed", vfile_text, {H: ["vfile_sha"]}),
             ("final sha256", rec(V, "final_geometry", "sha256", value="0" * 64), {V: ["final_sha"]}),
             ("validity label", val(V, "label", value=FR["D"]), {V: ["label"]}),
             ("validity parent label", val(V, "parent_label", value=FR["D"]), {V: ["label"]}),
             ("record validity_final.parent", rec(V, "validity_final", "parent", value=FR["D"]), {V: ["label"]}),
             ("validity final hash", val(V, "geometry_sha256", "final", value="0" * 64), {V: ["v_final"]}),
             ("validity start hash", val(V, "geometry_sha256", "start", value="0" * 64), {V: ["v_start"]}),
             ("validity host hash", val(V, "geometry_sha256", "host_relaxed", value="0" * 64), {V: ["v_host"]}),
             ("validity parent-final hash", val(V, "geometry_sha256", "parent_final", value="0" * 64),
              {V: ["v_parent"]}),
             ("n_config", rec(V, "n_config", value=6), {V: ["g_n", "g_range"]}),
             ("G numbering", gst(V, lambda pos: {(-1 if k == 0 else k): x for k, x in pos.items()}), {V: ["g_range"]}),
             ("final k", rec(V, "final_geometry", "k", value=3), {V: ["g_last"]}),
             ("G last configuration", gst(H, shift_last), {H: ["g_final"]}),
             ("final cell", lambda root, info: _new_cell(root, DV), {DV: ["cell"]}),
             ("check-5 reading, record", rec(V, "validity_final", "check5_reading", value="as_written"),
              {V: ["reading"]}),
             ("check-5 reading, validity record", val(V, "validity", "check5_reading", value="as_written"),
              {V: ["reading"]}),
             ("check-5 reading, both as written", both_as_written, {V: ["reading"]}),
             ("complete records after the stop", complete_after,
              {V: ["after_stop"], D: ["after_stop"], DV: ["after_stop"]}),
             ("a missing record after the stop", missing_after, {V: ["after_stop"]}),
             ("a record without a final geometry after the stop", no_final_after, {V: ["after_stop"]})] + \
        [("validity leaf valid", val(V, "validity", "valid", value=False), {V: ["leaves"]})] + \
        [(f"validity leaf {k}", rec(V, "validity_final", k, value=v), {V: ["leaves"]})
         for k, v in (("failed", [5]), ("valid_as_written", False), ("failed_as_written", [5]),
                      ("invariant_only", True))]
    # (valid is edited in the validity record: the record's own leaf would move the stop, and the complete records
    # after it would fail their own check, S2B 2)
    n = 0
    for what, route, edit, fake in progress:
        orig = g49.fr_progress
        root, fin, info = _copy(route)
        if edit:
            edit(root, info)
        try:
            if fake is not None:
                g49.fr_progress = lambda rows, final=False, f=fake: json.loads(json.dumps(f))     # scaffolding
            ok, sm, lines = _read_root(root, info["stub_any_parts"])
        finally:
            g49.fr_progress = orig
        assert not ok and "scripts/49 fr_progress DISAGREES" in lines[1] and not sm["mismatch"], (what, lines[:2])
        assert lines[-1].startswith("Integrity mismatch: the read ends here") and not sm["item2"], (what, lines[-1:])
        assert not any(l.startswith("ITEM 2") for l in lines), f"{what}: the read went on"
        n += 1
    for what, edit, want in named:
        root, fin, info = _copy("pass")
        g = edit(root, info) or info["stub_any_parts"]
        ok, sm, lines = _read_root(root, g)
        want = {lab: [CK[k] for k in ks] for lab, ks in want.items()}
        assert not ok and lines[-1].startswith("Integrity mismatch: the read ends here"), (what, lines[-1:])
        assert not any(l.startswith("ITEM 2") for l in lines) and not sm["item2"], f"{what}: the read went on"
        assert {l: sorted(b) for l, b in sm["mismatch"].items()} == {l: sorted(b) for l, b in want.items()}, \
            (what, sm["mismatch"])
        for lab, b in want.items():
            line = next(l for l in lines if l.startswith(f"  {lab}: "))
            assert line.endswith("; MISMATCH: " + "; ".join(x for x in CK.values() if x in b)), (what, line[-90:])
        if "after the stop" in what:
            assert sm["stop"] == (H, "check") and "scripts/49 fr_progress agrees" in lines[1], (what, lines[1])
            assert f"first failure {H} (check); items 2-5 not read beyond it: {[V, D, DV]};" in lines[1], lines[1]
            later = {V: (17, 18), D: (17, 18), DV: (17, 18)} if what.startswith("complete") else {V: (0, 1)}
            assert sm["item1"] == dict({H: (17, 17)}, **later), (what, sm["item1"])
        n += 1
    return f"{n} item-1 mismatches end the read: {len(progress)} fr_progress disagreements, {len(named)} checks each " \
           f"failing alone and named (3 absent files and 3 records after the stop among them)"


def t_gate():
    """Gate files and blinded paths are refused before they are opened, through the record loader and through any
    open() while the read runs, each refusal rule with a file that it alone catches (synthetic files in a copy of an fr
    archive and in a stand-in S2 root); the c2 mode is refused outside the temporary directory, and any
    results/objective2/s2/c2/ path whatever the root (paths only)."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    tmp = tempfile.mkdtemp(prefix="frgeom_gate_", dir=_ROUTES["_tmp"])
    C2F, C1F, GATE = "a C2 file", "a blinded C1 file", "a gate file"
    RAW = "a raw output or record outside the campaign's raw directory"
    try:
        root, fin, info = _copy("pass")
        fake = os.path.join(tmp, "fakeS2")
        files = [("gate", os.path.join(root, "fr", "gates", "FR.json"), GATE),
                 ("applied gate", os.path.join(root, "fr", "gates_applied", "gate_FR.gate.json"), GATE),
                 ("gate inputs", os.path.join(root, "fr", "gate_fr_step0_2.inputs.json"), GATE),
                 ("*.gate.json alone", os.path.join(root, "fr", "x.gate.json"), GATE),
                 ("step-0 attempt 1", os.path.join(root, "fr", "step0_attempt1", "gates", "fr_step0.json"), GATE),
                 ("step0_attempt1/ alone", os.path.join(root, "fr", "step0_attempt1", "x.json"), GATE),
                 ("C1 record", os.path.join(fake, "c1", "records", "s2_m30_host.json"), C1F),
                 ("C1 raw output", os.path.join(fake, "c1", "raw", "s2_m30_VA188.out.gz"), C1F),
                 ("C1 raw input alone", os.path.join(fake, "c1", "raw", "s2_m30_VA188.in.gz"), C1F),
                 ("C2 record in S2", os.path.join(fake, "c2", "raw", f"{P}VB76.a2.json"), C2F),
                 ("C2 graph in S2 alone", os.path.join(fake, "c2", "graph.json"), C2F),
                 ("C2 structures in S2 alone", os.path.join(fake, "c2", "structures.tar.gz"), C2F),
                 ("C2 record in the root", os.path.join(root, "c2", "raw", f"{P}VB76.a2.json"), C2F),
                 ("C2 graph in the root alone", os.path.join(root, "c2", "graph.json"), C2F),
                 ("C2 structures in the root alone", os.path.join(root, "c2", "structures.tar.gz"), C2F),
                 ("record outside fr/raw", os.path.join(root, "fr", f"{FR['V']}.a2.json"), RAW),
                 ("validity record outside fr/raw alone", os.path.join(root, "fr", f"{FR['V']}{VAL}"), RAW),
                 ("raw of another label", os.path.join(root, "fr", "raw", f"{P}VB76.p1.out.gz"), RAW),
                 ("plain .out outside fr/raw", os.path.join(root, "fr", f"{FR['V']}.p1.out"), RAW),
                 (".out.tryN.gz outside fr/raw", os.path.join(root, "fr", f"{FR['V']}.out.try1.gz"), RAW),
                 (".out.tryN outside fr/raw", os.path.join(root, "fr", f"{FR['V']}.out.try2"), RAW)]
        for _, p, _ in files:                                      # synthetic files only
            os.makedirs(os.path.dirname(p), exist_ok=True)
            json.dump({"decision": {"FR": {"outcome": "pass"}}, "synthetic": True}, open(p, "w"))
        n = 0
        with _reading(root, "fr", FR_ORDER, s2_roots=(fake,)):
            A = archive(root, "fr", FR_ORDER, FR_PAIRS, fr_guard(gd, fig))
            try:
                for name, p, why in files:
                    for fn in (lambda: A._open(p), lambda: open(p).read()):
                        try:
                            fn()
                            raise AssertionError(f"{name}: not refused")
                        except Refused as e:
                            assert why in str(e), f"{name}: refused as {str(e)[:60]}, not as {why}"
                            n += 1
                assert A.a2(FR["V"]).get("status") == "complete", "a record of the campaign must be readable"
            finally:
                A.close()
        # the c2 mode and C2 paths outside the temporary directory: paths only, nothing exists there or is opened
        other = os.path.join(os.sep, "nonexistent_fr_geom_probe", "another_checkout", S2_REL)
        assert not os.path.exists(os.path.join(os.sep, "nonexistent_fr_geom_probe")), "the probe root exists"
        cctx = {"root": other, "campaign": "c2", "labels": tuple(pdr.LABELS), "s2_roots": (S2,)}
        fctx = {"root": root, "campaign": "fr", "labels": tuple(FR_ORDER), "s2_roots": (S2,)}
        probes = [(cctx, os.path.join(other, "c2", "raw", f"{P}VB76.a2.json"), C2F),
                  (cctx, os.path.join(other, "c2", "raw", f"{P}VB76.p1.out.gz"), C2F),
                  (cctx, os.path.join(other, "c2", "structures.tar.gz"), C2F),
                  (fctx, os.path.join(other, "c2", "graph.json"), C2F),
                  (cctx, os.path.join(other, "c1", "raw", "s2_m30_VA188.in.gz"), C1F),
                  (fctx, os.path.join(other, "c1", "raw", "s2_m30_VA188.in.gz"), C1F),       # any checkout's C1 alone
                  (dict(fctx, root=os.path.join(tmp, "rootX")),                            # the root's own c1 alone
                   os.path.join(tmp, "rootX", "c1", "raw", "s2_m30_VA188.in.gz"), C1F)]
        for ctx, p, why in probes:
            assert _refuse_path(p, ctx) == why, f"{os.path.basename(p)} ({ctx['campaign']}, root {ctx['root']}): not " \
                                                f"refused as {why}"
            n += 1
        tctx = dict(cctx, root=tmp)
        assert _refuse_path(os.path.join(tmp, "c2", "raw", f"{P}VB76.a2.json"), tctx) is None, "a temporary c2 root"
        assert not _temporary(os.path.join(tempfile.gettempdir(), "x", S2_REL)), "an S2 in the temporary directory"
        try:
            read(other, out=lambda s: None, campaign="c2")
            raise AssertionError("the c2 mode outside the temporary directory was not refused")
        except Refused:
            n += 1
        except AssertionError:
            raise
        except Exception as e:
            raise AssertionError(f"the c2 mode outside the temporary directory raised {type(e).__name__}")
        return f"{n} refusals before opening: {len(files)} files (each rule alone among them) through the loader and " \
               f"open(); C2 and C1 paths of another checkout; the c2 mode outside the temporary directory"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t_leaf():
    """A withheld field of an fr A2 record raises through the read's guard: dF_200_180_meV and the S2b energy names."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    d, g, fin, info = _route("pass")
    n = 0
    with _reading(d, "fr", FR_ORDER):
        A = archive(d, "fr", FR_ORDER, FR_PAIRS, fr_guard(gd, fig))
        try:
            r = A.a2(FR["V"])
            assert isinstance(r, gd.GuardedS2b), "the fr records are not read through GuardedS2b"
            for path in (("end_rule", "dF_200_180_meV"), ("s2b_canary", "delta_far_meV"), ("s2b_canary", "Eb_A1_meV"),
                         ("s2b_canary", "F_k0_eV")):
                try:
                    pdr.leaf(r, *path)
                    raise AssertionError(f"{'.'.join(path)} was read")
                except (gd.Blinded, fig.Blinded):
                    n += 1
            for f in (lambda: r.get("s2b_canary").open(), lambda: r.get("end_rule").open(), lambda: str(r),
                      lambda: list(r)):
                try:
                    f()
                    raise AssertionError("a guarded subtree was handed out")
                except (gd.Blinded, fig.Blinded):
                    n += 1
            assert pdr.leaf(r, "s2b_canary", "ok") == 1 and pdr.leaf(r, "end_rule", "outcome") == "accepted_converged"
        finally:
            A.close()
    ok, sm, lines, _, _ = _read("pass")
    assert ok and not any(any(v in l for v in ("-1.234", "-2.5", "-3.5")) or "1.5" in l.split() for l in lines), \
        "a planted value reached the output"
    return f"{n} withheld reads refused (dF_200_180_meV, delta_far_meV, Eb_A1_meV, F_k0_eV, parents, str, iteration)"


def t_calc():
    """A loaded calculator module is refused before the archive is opened (D5 would refuse it only later, after
    item 1 had been printed)."""
    d, g, fin, info = _route("pass")
    lines = []
    sys.modules["mace"] = types.ModuleType("mace")
    try:
        read(d, out=lines.append, campaign="fr", g_reader=g)
        raise AssertionError("a loaded calculator module was not refused")
    except AssertionError as e:
        if "calculator module is loaded" not in str(e) or lines:
            raise AssertionError(f"not refused before the read ({len(lines)} lines printed): {str(e)[:40]}")
    finally:
        del sys.modules["mace"]
    ok, sm, lines, _, _ = _read("pass")
    assert ok
    return "a loaded calculator module ends the read before any file is opened or line printed"


def t_graph():
    """The fr graph's a2v jobs against the gate code's own label grammar (scripts/49 a2_cell, a1_start_of): on copies of
    the 'pass' archive, Cs D with the vac leg, Cs D with the A1 start of D+V+, and V+_R at another site are each refused
    by the graph check in its own words, before any record is read."""
    root0, fin, info = _copy("pass")
    edits = [("graph leg", FR["D"], "leg", "vac"), ("graph job", FR["D"], "a1", FR_A1[FR["DV"]]),
             ("graph job", FR["V"], "j", 187)]
    n = 0
    for why, lab, key, value in edits:
        root = os.path.join(os.path.dirname(root0), f"g{n}")
        shutil.copytree(root0, root, symlinks=True)
        p = os.path.join(root, "fr", "graph.json")
        g = json.load(open(p))
        for j in g["jobs"]:
            if j["label"] == lab:
                j[key] = value
        json.dump(g, open(p, "w"))
        lines = []
        try:
            read(root, out=lines.append, campaign="fr", g_reader=info["stub_any_parts"])
        except AssertionError as e:
            if str(e) != f"{lab}: {why}":
                raise AssertionError(f"{lab} {key}: refused as {str(e)[:60]!r}, not by the graph check ({why})")
        except Exception as e:
            raise AssertionError(f"{lab} {key}: {type(e).__name__} ({str(e)[:50]}), not the graph check ({why})")
        else:
            raise AssertionError(f"{lab} {key}: the read went on")
        assert not lines, f"{lab} {key}: printed before the graph check"
        n += 1
    return f"{n} graph jobs off the gate code's grammar refused by the graph check (a leg, an A1 start, a site)"


def _g_parts(tmp, lab, n=1):
    """n placeholder raw parts of lab in <tmp>/fr/raw (never parsed: G's guards are tested with stub readers)."""
    raw = os.path.join(tmp, "fr", "raw")
    os.makedirs(raw, exist_ok=True)
    out = []
    for i in range(n):
        out.append(os.path.join(raw, f"{lab}.p{i + 1}.out.gz"))
        with gzip.open(out[-1], "wt") as fh:
            fh.write("synthetic placeholder; never parsed\n")
    return out


def t_g_guards():
    """G's guards without the WP2e output (placeholder fr raw parts in the temporary directory, stub readers): G is
    given <c>/raw/<label>.p<n>.out.gz of this campaign and label (the reader is called with them), and a part of the
    root's c2/, a plain .out and another label's part are refused before the reader is called; a reader that moves a
    scripts/47 READS counter is refused (D-C2-11)."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    tmp = tempfile.mkdtemp(prefix="frgeom_gg_", dir=_ROUTES["_tmp"])
    try:
        lab = FR["V"]
        good = _g_parts(tmp, lab, 2)
        A = types.SimpleNamespace(root=tmp, c="fr", L=c46.Layout(kind="archive", root=tmp), mapping={})
        n, called = 0, []
        with _reading(tmp, "fr", FR_ORDER):
            stub = lambda q47_, parts, **kw: (called.append([os.path.realpath(p) for p in parts]) or
                                              ({"n_config": 1}, {0: ("synthetic", None)}))
            try:
                pr, pos = g_read(q47, A, lab, stub, 64)
            except Refused as e:
                raise AssertionError(f"G refused this campaign's own parts ({str(e)[:60]})")
            assert called == [[os.path.realpath(p) for p in good]] and list(pos) == [0], "G was not given its parts"
            called.clear()
            for bad in (os.path.join(tmp, "c2", "raw", f"{lab}.p1.out.gz"), os.path.join(tmp, "fr", "raw", f"{lab}.p1.out"),
                        os.path.join(tmp, "fr", "raw", f"{FR['host']}.p1.out.gz")):
                B = types.SimpleNamespace(root=tmp, c="fr", mapping={},
                                          L=types.SimpleNamespace(a2_parts=lambda c, l, b=bad: [b]))
                try:
                    g_read(q47, B, lab, stub, 64)
                    raise AssertionError(f"G given {os.path.basename(bad)} was not refused")
                except Refused:
                    n += 1
            assert not called, "a refused part reached the reader"

            def energy_reader(q47_, parts, **kw):
                q47_.READS["F"] = q47_.READS.get("F", 0) + 1          # stands for an energy read; nothing is parsed
                return {}, {0: None}
            try:
                g_read(q47, A, lab, energy_reader, 64)
                raise AssertionError("a reader that moved READS['F'] was not refused")
            except Refused:
                n += 1
            finally:
                q47.READS["F"] -= 1
        return f"G given this campaign's 2 parts; {n} refusals (3 parts elsewhere, 1 READS move), no WP2e output read"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t_g_real():
    """Real G on synthetic restarted fr raw parts cut from the public WP2e output (opens the public *.out.gz; skipped
    by --without-wp2e): through g_read, every configuration, positions only, READS unchanged."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    tmp = tempfile.mkdtemp(prefix="frgeom_g_", dir=_ROUTES["_tmp"])
    try:
        lab = FR["V"]
        raw = os.path.join(tmp, "fr", "raw"); os.makedirs(raw)
        wp = fig._WP2e(q47)
        for i, t in enumerate(wp.parts(lab, "conv", 60, (40,))):
            with gzip.open(os.path.join(raw, f"{lab}.p{i + 1}.out.gz"), "wt") as fh:
                fh.write(t)
        mapping = json.load(open(os.path.join(S2, "c1", "smoke.json")))["mapping"]
        A = types.SimpleNamespace(root=tmp, c="fr", L=c46.Layout(kind="archive", root=tmp), mapping=mapping)
        with _reading(tmp, "fr", FR_ORDER):
            pr, pos = g_read(q47, A, lab, cd.g_positions, 64)
            assert sorted(pos) == list(range(61)) and pos[0][1].shape == (234, 3) and 40 in pos, "G on fr raw parts"
        return "real G on 2 synthetic fr raw parts (61 configurations), through the guards"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


class _Git:
    """A stand-in for git in main_read's cases; no repository is touched. HEAD holds the paths given to at_head
    (relative to base; a directory is at HEAD if a file under it is) and the text each file had then (git show HEAD:);
    dirty holds changed files anywhere; under base, a file that exists and is not at HEAD is untracked and one at HEAD
    that does not exist is deleted, every such file under a directory given to status included. A file rewritten after
    at_head and not in dirty stands for an edit that git status does not show (assume-unchanged)."""

    def __init__(self, base, dirty=()):
        self.base, self.head, self.dirty = os.path.realpath(base), set(), {os.path.realpath(f) for f in dirty}
        self.blob, self.shown = {}, []

    def at_head(self, *paths):
        for p in paths:
            rel = os.path.relpath(os.path.realpath(p), self.base)
            self.head.add(rel)
            if os.path.isfile(p):
                with open(p, "rb") as fh:
                    self.blob[rel] = fh.read().decode(errors="replace")

    def __call__(self, *a):
        res = lambda rc=0, out="": types.SimpleNamespace(returncode=rc, stdout=out)
        under = lambda f, d: f == d or f.startswith(d + os.sep)
        if a == ("rev-parse", "HEAD"):
            return res(out="0" * 40 + "\n")
        if a[:2] == ("cat-file", "-e"):
            rel = os.path.normpath(a[2].split(":", 1)[1])
            return res(0 if any(under(h, rel) for h in self.head) else 128)
        if a[:2] == ("cat-file", "-t"):                   # IX-6: a file at HEAD is a blob, a directory a tree
            rel = os.path.normpath(a[2].split(":", 1)[1])
            return res(0, "blob\n") if rel in self.blob else res(0, "tree\n") if any(
                under(h, rel) for h in self.head) else res(128)
        if len(a) == 2 and a[0] == "show" and a[1].startswith("HEAD:"):
            rel = os.path.normpath(a[1].split(":", 1)[1])
            self.shown.append(rel)
            return res(0, self.blob[rel]) if rel in self.blob else res(128)
        if a[:3] == ("status", "--porcelain", "--") and len(a) > 3:
            ps = [os.path.realpath(p) for p in a[3:]]
            rows = [f" M {f}" for f in sorted(self.dirty) if any(under(f, p) for p in ps)]
            for p in ps:
                if not p.startswith(self.base + os.sep):
                    continue
                rel = os.path.relpath(p, self.base)
                files = [os.path.join(d, f) for d, _, fs in os.walk(p) for f in fs] if os.path.isdir(p) else [p]
                rows += [f"?? {os.path.relpath(f, self.base)}" for f in files
                         if os.path.isfile(f) and os.path.relpath(f, self.base) not in self.head]
                rows += [f" D {h}" for h in sorted(self.head)
                         if under(h, rel) and not os.path.lexists(os.path.join(self.base, h))]
            return res(out="\n".join(rows))
        raise AssertionError(f"git {' '.join(a[:3])}: not expected")


def _read_rig(tmp, state):
    """main_read on a stand-in git and S2 under tmp, the reader stubbed (no fr or C2 file exists or is read), for t_main
    and t_stop_note: run(name, ...) -> (exit code, {output file: lines}, last refusal line, git, here), on a committed,
    verified archive at CAMPAIGN_DONE unless told otherwise; refused(name, why, ...) asserts exit 3, why in the refusal
    and nothing written."""

    def reader(kind):
        def f(root, out):
            assert root.startswith(tmp), "a real S2 given to the stub reader"
            out("ITEM 1. Integrity (every complete FR record, in FR order)")
            if kind == "fail":
                out("ITEM 2. Agreement on check 5")
                raise RuntimeError("synthetic failure")
            state["read"] = kind == "late"
            out("Integrity mismatch: the read ends here (synthetic)." if kind == "mismatch" else "END: synthetic")
            return kind != "mismatch", {}
        return f

    def run(name, kind="ok", dirty=(), fr=True, git=None, status="done", note=None, verify="head", edit=None,
            commits=("e" * 40, "e" * 40)):
        base = os.path.realpath(os.path.join(tmp, name))
        here, s2 = os.path.join(base, "c2_diagnostic"), os.path.join(base, "s2")
        os.makedirs(here, exist_ok=True)
        git = git or _Git(base, dirty)
        if fr:                                    # a committed, verified archive at CAMPAIGN_DONE unless told otherwise
            os.makedirs(os.path.join(s2, "fr"), exist_ok=True)
            cj = os.path.join(s2, "fr", "campaign.json")
            if status is not None:
                with open(cj, "w") as fh:            # commits: start_commit and commit ("absent": no leaves)
                    json.dump({"schema": "s2-campaign-1", "campaign": "fr", "status": status,
                               **({} if commits == "absent" else dict(zip(("start_commit", "commit"), commits)))}, fh)
                git.at_head(cj)
            vp = os.path.join(s2, VERIFY)
            if verify != "absent":
                os.makedirs(os.path.dirname(vp), exist_ok=True)
                with open(vp, "w") as fh:
                    fh.write("synthetic verify record\n")
                if verify != "untracked":
                    git.at_head(vp)
                if verify == "edited":
                    git.dirty.add(os.path.realpath(vp))
            if edit:
                edit(s2, git)
        echo, err = [], []
        try:
            code = main_read(git, repo=base, s2=s2, here=here, reader=reader(kind), echo=echo.append, err=err.append,
                             stop_note=note)
        except Exception as e:
            raise AssertionError(f"{name}: main_read raised {type(e).__name__} ({str(e)[:40]})")
        got = {}
        for f in (OUT_NAME, OUT2_NAME):
            if os.path.exists(os.path.join(here, f)):
                with open(os.path.join(here, f)) as fh:
                    got[f] = fh.read().splitlines()
        state["echo"] = echo
        return code, got, (err or [""])[-1], git, here

    def refused(name, why, **kw):
        code, got, err, _, _ = run(name, **kw)
        assert code == 3 and why in err and not got, (name, code, err, list(got))
        return 1
    return run, refused


def t_main():
    """The --read discipline (part d, 'When'; S2B 6b, 'When'; S2B 7), on a stand-in git and S2 in the temporary
    directory, the reader stubbed (no fr or C2 file exists or is read): the tool writes its output with the exit code on
    the last line and a header holding HEAD, the campaign status, the verify record's sha256 and the four tool hashes;
    the one rerun writes the attempt-2 file, only after attempt 1 is committed unedited. Refused with exit 3 and nothing
    written: a third attempt (attempt 2 in the tree, at HEAD, or at HEAD and deleted); attempt 1 uncommitted or deleted;
    uncommitted code (a tool file, a module loaded through scripts/46, and files the read does not load: g2_square.py,
    scripts/50, s2b/fr_inputs.py); a missing fr archive; every breach of 6b's 'When' outside a STOP (no
    fr/campaign.json, status 'running', the verify record absent, untracked or edited, an untracked or an edited file in
    fr/, a c3b archive, s2b/E_output.txt in the tree or at HEAD only; a STOP and its stop note are t_stop_note's). An
    uncommitted module first loaded during the read is a failure before output; exits 0, 1 and 2 in their documented
    shapes."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    tmp = os.path.realpath(tempfile.mkdtemp(prefix="frgeom_main_", dir=_ROUTES["_tmp"]))
    late = os.path.realpath(os.path.join(S2, "synthetic_module_loaded_late.py"))    # a path only; no such file
    state = {}
    run, refused = _read_rig(tmp, state)
    sha = lambda p, n=64: hashlib.sha256(open(p, "rb").read()).hexdigest()[:n]
    code, got, err, git, here = run("a")
    t1 = got.get(OUT_NAME, [""])
    assert code == 0 and list(got) == [OUT_NAME] and state["echo"] == ["\n".join(t1)], (code, list(got), err)
    m = re.fullmatch(r"FR geometry read \(S2B_PLAN\.md section 6b\), attempt 1, at 0{40}; fr/campaign\.json status "
                     r"'done' \(CAMPAIGN_DONE\); verify record fr_verify/verify_fr\.txt sha256 ([0-9a-f]{64}); tools "
                     r"sha256 fr_geom_read ([0-9a-f]{12}), part_d_read ([0-9a-f]{12}), check5_diag ([0-9a-f]{12}), "
                     r"s2b/guard ([0-9a-f]{12})", t1[0])
    assert m and m.groups() == (sha(os.path.join(os.path.dirname(here), "s2", VERIFY)), sha(os.path.abspath(__file__), 12),
                                sha(os.path.join(HERE, "part_d_read.py"), 12), sha(os.path.join(HERE, "check5_diag.py"), 12),
                                sha(os.path.join(S2, "s2b", "guard.py"), 12)), t1[0]
    assert t1[1:] == ["ITEM 1. Integrity (every complete FR record, in FR order)", "END: synthetic", "exit 0"], t1
    code, got2, err, _, _ = run("a", git=git)                       # attempt 1 not yet committed
    assert code == 3 and "committed unedited" in err and got2 == got, (code, err)
    git.at_head(os.path.join(here, OUT_NAME))
    code, got3, err, _, _ = run("a", kind="fail", git=git)          # the one rerun, failing before output
    t2 = got3.get(OUT2_NAME, [""])
    assert code == 2 and got3[OUT_NAME] == t1 and ", attempt 2 (attempt 1: fr_geom_read_output.txt sha256 " in t2[0] \
        and "last line 'exit 0'" in t2[0], (code, t2)
    assert t2[1:] == ["FR geometry read failed before output: RuntimeError at ITEM 2", "exit 2"], t2
    n = 0
    code, got4, err, _, _ = run("a", git=git)                       # attempt 2 written, not yet committed
    assert code == 3 and "third attempt" in err and got4 == got3, (code, err)
    git.at_head(os.path.join(here, OUT2_NAME))
    code, got4, err, _, _ = run("a", git=git)                       # attempt 2 committed
    assert code == 3 and "third attempt" in err and got4 == got3, (code, err)
    os.remove(os.path.join(here, OUT2_NAME))                        # attempt 2 committed, then deleted in the tree
    code, got4, err, _, _ = run("a", git=git)
    assert code == 3 and "third attempt" in err and got4 == {OUT_NAME: t1}, (code, err, list(got4))
    n += 3
    code, got, err, git, here = run("b", kind="mismatch")
    assert code == 1 and got[OUT_NAME][-2:] == ["Integrity mismatch: the read ends here (synthetic).", "exit 1"], got
    git.at_head(os.path.join(here, OUT_NAME))
    os.remove(os.path.join(here, OUT_NAME))                         # committed, then deleted in the tree
    code, got, err, _, _ = run("b", git=git)
    assert code == 3 and "committed unedited" in err and not got, (code, err)
    n += 1
    m38 = os.path.realpath(os.path.join(REPO, "scripts", "38_wp2e_displacement.py"))
    assert m38 in code_files(), "scripts/38 is not among the loaded module files"
    unloaded = [os.path.join(HERE, "g2_square.py"), os.path.join(REPO, "scripts", "50_s2_campaign.py"),
                os.path.join(S2, "s2b", "fr_inputs.py")]
    assert not set(map(os.path.realpath, unloaded)) & set(code_files()), "a file the read does not load is loaded"
    for i, f in enumerate([os.path.join(HERE, "fr_geom_read.py"), m38] + unloaded):
        n += refused(f"c{i}", "not committed", dirty=[f])
    n += refused("e", "no fr archive", fr=False)
    when = [("w1", dict(status=None), "status None"), ("w2", dict(status="running"), "status 'running'"),
            ("w5", dict(verify="absent"), "verify record"), ("w6", dict(verify="untracked"), "verify record"),
            ("w7", dict(verify="edited"), "verify record"),
            ("w8", dict(edit=lambda s2, g: open(os.path.join(s2, "fr", "graph.json"), "w").write("{}")),
             "fr archive is not committed"),
            ("w9", dict(edit=lambda s2, g: g.dirty.add(os.path.realpath(os.path.join(s2, "fr", "campaign.json")))),
             "fr archive is not committed"),
            ("w10", dict(edit=lambda s2, g: os.makedirs(os.path.join(s2, "c3b"))), "c3b exists"),
            ("w11", dict(edit=lambda s2, g: (os.makedirs(os.path.join(s2, "s2b")),
                                             open(os.path.join(s2, "s2b", "E_output.txt"), "w").write("exit 0\n"))),
             "E_output.txt exists"),
            ("w12", dict(edit=lambda s2, g: g.at_head(os.path.join(s2, "s2b", "E_output.txt"))), "E_output.txt exists")]
    for name, kw, why in when:
        n += refused(name, why, **kw)
    base_files = code_files
    with _mutant("code_files", lambda: base_files() + ([late] if state.get("read") else [])):   # scaffolding
        code, got, err, _, _ = run("f", kind="late", dirty=[late])
    assert code == 2 and got[OUT_NAME][1:] == ["FR geometry read failed before output: Uncommitted after the items",
                                               "exit 2"], got
    return f"outputs written with the exit code last, header checked; the rerun as attempt 2 after attempt 1 is " \
           f"committed; {n} refusals (exit 3, nothing written; {len(when)} of 6b's 'When'); a late uncommitted " \
           f"module (exit 2); exits 0, 1, 2"


def _e_precommit_rule():
    """Integration review 2: E's refusal of a STOP before the fr campaign commit (amendment 2026-11-12a item 11), from
    the source of s2b/e_eval.py alone (ast; e_eval is not imported): the compiled condition of the If in Run.route_admit
    whose body raises the refusal naming that route, and the assignment of the two leaves it tests."""
    path = os.path.join(S2, "s2b", "e_eval.py")
    with open(path) as fh:
        tree = ast.parse(fh.read(), path)
    fn = [n for c in tree.body if isinstance(c, ast.ClassDef) and c.name == "Run" for n in c.body
          if isinstance(n, ast.FunctionDef) and n.name == "route_admit"]
    assert len(fn) == 1, "s2b/e_eval.py: Run.route_admit not found"
    ifs = [n for n in ast.walk(fn[0]) if isinstance(n, ast.If) and any(
        isinstance(b, ast.Raise) and "before its campaign commit was recorded" in ast.unparse(b) for b in n.body)]
    leaves = [[(x.id, ast.unparse(v)) for x, v in zip(n.targets[0].elts, n.value.elts)] for n in ast.walk(fn[0])
              if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Tuple) and isinstance(n.value, ast.Tuple)
              and [ast.unparse(x) for x in n.targets[0].elts] == ["start", "commit"]]
    assert len(ifs) == 1 and len(leaves) == 1, ("s2b/e_eval.py: the pre-commit refusal", len(ifs), leaves)
    return compile(ast.Expression(ifs[0].test), path, "eval"), leaves[0]


def _e_unapplied_rule():
    """Integration review 2 (IX-15): E's refusal of gate FR written but not applied, from the source of s2b/e_eval.py
    alone (ast; e_eval is not imported): its module-level function gate_fr_unapplied, compiled, and the compiled
    condition of the If in Run.route_admit whose body raises that refusal."""
    path = os.path.join(S2, "s2b", "e_eval.py")
    with open(path) as fh:
        tree = ast.parse(fh.read(), path)
    fd = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "gate_fr_unapplied"]
    fn = [n for c in tree.body if isinstance(c, ast.ClassDef) and c.name == "Run" for n in c.body
          if isinstance(n, ast.FunctionDef) and n.name == "route_admit"]
    ifs = [n for f in fn for n in ast.walk(f) if isinstance(n, ast.If) and any(
        isinstance(b, ast.Raise) and "written but not applied" in ast.unparse(b) for b in n.body)]
    assert len(fd) == 1 and len(fn) == 1 and len(ifs) == 1, ("s2b/e_eval.py: the IX-15 refusal", len(fd), len(ifs))
    ns = {"os": os}
    exec(compile(ast.Module(body=fd, type_ignores=[]), path, "exec"), ns)
    return ns["gate_fr_unapplied"], compile(ast.Expression(ifs[0].test), path, "eval")


def _e_note_rules():
    """E's stop-note rules compiled from the source of s2b/e_eval.py alone (ast: e_eval is not imported, so no module
    of E enters this process): S2_REL, STOP_PHRASE, ISO_DATE, STOP_NOTE (IX-6), stop_note_ok, Git and Run.note_ok."""
    path = os.path.join(S2, "s2b", "e_eval.py")
    with open(path) as fh:
        tree = ast.parse(fh.read(), path)
    names = {"S2_REL", "STOP_PHRASE", "ISO_DATE", "STOP_NOTE"}
    body = [n for n in tree.body if isinstance(n, ast.Assign) and {getattr(t, "id", None) for t in n.targets} & names]
    body += [n for n in tree.body
             if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in ("stop_note_ok", "Git")]
    body += [n for c in tree.body if isinstance(c, ast.ClassDef) and c.name == "Run"
             for n in c.body if isinstance(n, ast.FunctionDef) and n.name == "note_ok"]
    ns = {"re": re, "subprocess": subprocess, "EError": type("EError", (Exception,), {})}
    exec(compile(ast.Module(body=body, type_ignores=[]), path, "exec"), ns)
    missing = sorted((names | {"stop_note_ok", "Git", "note_ok"}) - set(ns))
    assert not missing, f"s2b/e_eval.py: {missing} not found"
    return types.SimpleNamespace(**ns)


@contextlib.contextmanager
def _git_env():
    """git for a throwaway repository of the self-test: no system or global configuration, a fixed identity, no
    automatic gc or maintenance (as e_selftest's GIT_ENV); os.environ is restored on exit."""
    env = {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_AUTHOR_NAME": "fr-selftest",
           "GIT_AUTHOR_EMAIL": "fr-selftest@invalid", "GIT_COMMITTER_NAME": "fr-selftest",
           "GIT_COMMITTER_EMAIL": "fr-selftest@invalid", "GIT_CONFIG_COUNT": "3", "GIT_CONFIG_KEY_0": "gc.auto",
           "GIT_CONFIG_VALUE_0": "0", "GIT_CONFIG_KEY_1": "maintenance.auto", "GIT_CONFIG_VALUE_1": "false",
           "GIT_CONFIG_KEY_2": "gc.autoDetach", "GIT_CONFIG_VALUE_2": "false"}
    old = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def t_note_rules():
    """IX-1, IX-6: the stop note's phrase and rules pinned against s2b/e_eval.py, E's own code (_e_note_rules). The
    phrase, the date, the place and the one path equal E's (pattern and flags; NOTE_ROOT = E's S2_REL = S2 relative to
    the repository; NOTE_ROOT/NOTE_NAME = E's STOP_NOTE); stop_note_ok equals E's on 20 paths and texts; and, on
    throwaway git repositories in the temporary directory (one for each state of the one note, which has one path),
    final_stop through _git_cli (the read's own git) gives E's verdict (Run.note_ok and stop_note_ok through E's Git) on
    22 notes: at the one path, valid (LF, CRLF, a byte outside UTF-8); untracked, ignored, staged, edited; an edit that
    git status does not show, either way; absent; undated; lacking the phrase; a directory whose tree listing holds the
    phrase and a date (not a blob); and, beside a valid note at the one path, other paths each holding the phrase on one
    line with a date (S2B_PLAN.md, FR_OPERATIONS.md, a second note, under s2b/, outside S2/), a glob and a pathspec of
    the note, and a path not normalised. The five accepted (the three valid, the one valid at HEAD whose tree edit git
    status does not show, and the one beside the other paths) carry E's sha256, that of the text at HEAD."""
    e = _e_note_rules()
    assert (STOP_PHRASE.pattern, STOP_PHRASE.flags, ISO_DATE.pattern, ISO_DATE.flags, NOTE_ROOT,
            f"{NOTE_ROOT}/{NOTE_NAME}") == (e.STOP_PHRASE.pattern, e.STOP_PHRASE.flags, e.ISO_DATE.pattern,
                                            e.ISO_DATE.flags, e.S2_REL, e.STOP_NOTE), \
        "the phrase, the date, the place or the path of a stop note differs from s2b/e_eval.py"
    assert os.path.relpath(S2, REPO).replace(os.sep, "/") == e.S2_REL, "the read's S2 is not E's"
    R, ok = NOTE_ROOT, "2026-11-21: the fr STOP is final."
    N = f"{R}/{NOTE_NAME}"
    pairs = [(N, ok, True), (N, "2026-11-21: the fr stop is final.", True),
             (N, "THE FR STOP IS FINAL (2026-11-21)", True), (f"{R}/FR_STOP.md", ok, False),
             (f"{R}/notes/{NOTE_NAME}", ok, False), (f"{R}/s2bx/{NOTE_NAME}", ok, False),
             (f"{R}/s2b/{NOTE_NAME}", ok, False), (f"results/objective2/{NOTE_NAME}", ok, False),
             (f"results/objective2/s2x/{NOTE_NAME}", ok, False), (f"s2/{NOTE_NAME}", ok, False),
             (f"{R}/S2B_PLAN.md", ok, False), (f"{R}/FR_STOP_NO*.md", ok, False), (N, "the fr STOP is final.", False),
             (N, "2026-11-21: the fr STOP is not final.", False), (N, "2026-11-21: the fr  STOP is final.", False),
             (N, "12026-11-21: the fr STOP is final.", False), (N, "2026-11-210: the fr STOP is final.", False),
             (N, "1999-11-21: the fr STOP is final.", False), (N, "2026/11/21: the fr STOP is final.", False),
             (N + "/x.md", ok, False)]
    for p, t, want in pairs:
        assert stop_note_ok(p, t) == bool(e.stop_note_ok(p, t)) == want, f"stop_note_ok({p!r}, {t!r}): not E's"
    tmp = os.path.realpath(tempfile.mkdtemp(prefix="frgeom_git_", dir=_ROUTES["_tmp"]))
    good = b"# FR stop note (synthetic)\n\n2026-11-21: the fr STOP is final; no relaunch.\n"
    other = b"2026-11-22: the fr STOP is final (in the tree only).\n"
    bad = b"2026-11-21: fr stopped; no relaunch.\n"
    dated = b"# a synthetic note\n\n2026-11-21: the fr STOP is final.\n"
    # repository -> ({S2-relative path: bytes} committed, {path: bytes} written after the commit, staged paths,
    # assume-unchanged paths, the notes judged)
    repos = {"lf": ({NOTE_NAME: good}, {}, (), (), [N]),
             "crlf": ({NOTE_NAME: good.replace(b"\n", b"\r\n")}, {}, (), (), [N]),
             "bytes": ({NOTE_NAME: good + b"\xff\n"}, {}, (), (), [N]),
             "undated": ({NOTE_NAME: b"the fr STOP is final.\n"}, {}, (), (), [N]),
             "nophrase": ({NOTE_NAME: bad}, {}, (), (), [N]),
             "untracked": ({}, {NOTE_NAME: good}, (), (), [N]),
             "ignored": ({".gitignore": NOTE_NAME.encode() + b"\n"}, {NOTE_NAME: good}, (), (), [N]),
             "staged": ({}, {NOTE_NAME: good}, (NOTE_NAME,), (), [N]),
             "edited": ({NOTE_NAME: good}, {NOTE_NAME: good + b"edited in the tree\n"}, (), (), [N]),
             "hidden_bad": ({NOTE_NAME: bad}, {NOTE_NAME: good}, (), (NOTE_NAME,), [N]),
             "hidden_good": ({NOTE_NAME: good}, {NOTE_NAME: other}, (), (NOTE_NAME,), [N]),
             "absent": ({}, {}, (), (), [N]),
             "tree": ({f"{NOTE_NAME}/2026-11-21 the fr STOP is final.md": b"a file in a directory\n"}, {}, (), (), [N]),
             "others": ({NOTE_NAME: good, "S2B_PLAN.md": dated, "FR_OPERATIONS.md": dated, "FR_STOP_NOTE_2.md": dated,
                         f"s2b/{NOTE_NAME}": dated, f"../{NOTE_NAME}": dated}, {}, (), (),
                        [N, f"{R}/S2B_PLAN.md", f"{R}/FR_OPERATIONS.md", f"{R}/FR_STOP_NOTE_2.md",
                         f"{R}/s2b/{NOTE_NAME}", f"results/objective2/{NOTE_NAME}", f"{R}/FR_STOP_NO*.md",
                         f":(literal){N}", f"{R}/./{NOTE_NAME}"])}
    want = {("lf", N): good, ("crlf", N): good.replace(b"\n", b"\r\n"), ("bytes", N): good + b"\xef\xbf\xbd\n",
            ("hidden_good", N): good, ("others", N): good}
    want = {k: hashlib.sha256(v).hexdigest() for k, v in want.items()}             # E's: of the text at HEAD, UTF-8
    got = {}
    with _git_env():
        for name, (committed, after, staged, hidden, notes) in repos.items():
            base = os.path.join(tmp, name)
            s2 = os.path.join(base, *R.split("/"))
            sh = lambda *a: subprocess.run(["git", "-C", base, *a], capture_output=True, check=True)

            def write(rel, b):
                q = os.path.normpath(os.path.join(s2, rel))
                os.makedirs(os.path.dirname(q), exist_ok=True)
                with open(q, "wb") as fh:
                    fh.write(b)
            os.makedirs(s2)
            sh("init", "-q")
            for k, b in {"README.md": b"synthetic\n", **committed}.items():
                write(k, b)
            sh("add", "-A")
            sh("commit", "-q", "-m", "synthetic stop notes")
            for k in hidden:
                sh("update-index", "--assume-unchanged", "--", f"{R}/{k}")
            for k, b in after.items():
                write(k, b)
            for k in staged:
                sh("add", "--", f"{R}/{k}")
            eg = types.SimpleNamespace(git=e.Git(base))
            for note in notes:
                try:
                    text = e.note_ok(eg, note, what="--stop-note")
                    ew = hashlib.sha256(text.encode()).hexdigest() if e.stop_note_ok(note, text) else None
                except e.EError:
                    ew = None
                try:
                    rw = final_stop(_git_cli(base), base, s2, "stopped", note)[1]
                except Refused:
                    rw = None
                except Exception as x:
                    raise AssertionError(f"{name} {note}: {type(x).__name__} in final_stop (E: "
                                         f"{'accepted' if ew else 'refused'})")
                assert rw == ew, f"{name} {note}: the read's verdict {rw} is not E's {ew}"
                got[(name, note)] = rw
    assert {k: v for k, v in got.items() if v} == want, f"accepted {sorted(k for k, v in got.items() if v)}"
    return f"phrase, date, place and path as E's; stop_note_ok as E's on {len(pairs)} paths and texts; on " \
           f"{len(repos)} throwaway git repositories {len(got)} notes judged as E judges them, {len(want)} accepted " \
           f"with E's sha256 (LF, CRLF, a byte outside UTF-8, an edit git status does not show, the one note beside " \
           f"other dated notes)"


def t_stop_note():
    """IX-1, IX-6 on the stand-in git and S2 of t_main (_read_rig): a STOP of fr ('stopped') is read only with
    --stop-note naming the one stop note S2/FR_STOP_NOTE.md, committed and clean, a blob at HEAD whose text is dated and
    states that the fr STOP is final, and the header records the note's path and the sha256 of that text (an edit that
    git status does not show changes neither). Refused with exit 3 and nothing written: 'stopped' with no note; a valid
    note on 'done'; at the one path, a note lacking the phrase, undated, absent, untracked, edited, valid only in the
    tree, or a directory; any other path, each a dated note stating the phrase (under s2b/, outside S2/, S2B_PLAN.md,
    FR_OPERATIONS.md, a second note) or a glob of the note with the note present; a path not normalised; a C2 path
    named as the note (refused before git is asked about it). The command line passes --stop-note to main_read and no
    longer takes --final-stop, as the usage line says; main_read's own git is _git_cli. Integration review 2: a STOP
    before the fr campaign commit (start_commit and commit null, or neither leaf written) is refused with a valid note,
    and before the note is read (no note file at all, git never asked to show it); the rule is E's
    (_e_precommit_rule: the condition of e_eval.Run.route_admit, evaluated on a table). IX-15: a stopped fr with
    fr/gates/FR.json and no gates_applied/gate_FR.gate.json (gate FR written but not applied) is refused with a valid
    note and with no note file (before the note is read); with the copy beside it, and on a done fr, it is read; the
    rule is E's (_e_unapplied_rule: e_eval.gate_fr_unapplied and its condition in Run.route_admit, compiled from E's
    source and evaluated on every layout of the two files for each status)."""
    tools()
    tmp = os.path.realpath(tempfile.mkdtemp(prefix="frgeom_stop_", dir=_ROUTES["_tmp"]))
    run, refused = _read_rig(tmp, {})
    good = "# FR stop note (synthetic)\n\n2026-11-21: the fr STOP is final; no relaunch.\n"
    N, n = f"s2/{NOTE_NAME}", 0

    def note(rel, text=good, head=True, dirty=False, tree=None):
        """An edit of the rig: the note at rel (relative to the stand-in repository), at HEAD unless told otherwise;
        dirty: changed in the tree; tree: the tree's text after HEAD's, hidden from git status."""
        def edit(s2, git):
            p = os.path.join(os.path.dirname(s2), *rel.split("/"))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as fh:
                fh.write(text)
            if head:
                git.at_head(p)
            if dirty:
                git.dirty.add(os.path.realpath(p))
            if tree is not None:
                with open(p, "w") as fh:
                    fh.write(tree)
        return edit
    stopped = lambda rel=N, **kw: dict(status="stopped", note=rel, edit=note(rel, **kw))
    both = lambda rel: (lambda s2, git: (note(N)(s2, git), note(rel)(s2, git)))     # the one note and another
    one = "the stop note is the one file s2/FR_STOP_NOTE.md (IX-6)"
    cases = [("n1", dict(status="stopped"), "status 'stopped': the read runs"),
             ("n2", dict(note=N, edit=note(N)), "status 'done' with --stop-note"),
             ("n3", stopped(text="2026-11-21: fr stopped; no relaunch.\n"), "is not a dated note under s2/"),
             ("n4", stopped(text="the fr STOP is final; no relaunch.\n"), "is not a dated note under s2/"),
             ("n5", stopped(f"s2/s2b/{NOTE_NAME}"), one),
             ("n6", stopped(NOTE_NAME), one),
             ("n7", dict(stopped(), note=f"s2/./{NOTE_NAME}"), "a normalised repository-relative path is required"),
             ("n8", dict(status="stopped", note=N), "is not committed and clean"),
             ("n9", stopped(head=False), "is not committed and clean"),
             ("n10", stopped(dirty=True), "is not committed and clean"),
             ("n11", stopped(text="2026-11-21: fr stopped.\n", tree=good), "is not a dated note under s2/"),
             ("n13", dict(status="stopped", note=N, edit=note(f"{N}/2026-11-21 the fr STOP is final.md")),
              "is not committed and clean")]                                     # a directory at the one path
    for i, rel in enumerate(("s2/S2B_PLAN.md", "s2/FR_OPERATIONS.md", "s2/FR_STOP_NOTE_2.md", "s2/FR_STOP_NO*.md")):
        cases.append((f"n{14 + i}", dict(status="stopped", note=rel, edit=both(rel if "*" not in rel else N)), one))
    for name, kw, why in cases:
        n += refused(name, why, **kw)
    code, got, err, git, _ = run("n12", **stopped("s2/c2/FR_STOP.md"))
    assert code == 3 and "refused before it is read: a C2 file" in err and not got and not git.shown, (code, err)
    n += 1
    pre = "fr stopped before its campaign commit was recorded"            # integration review 2 (amendment item 11)
    for name, kw in (("p1", dict(stopped(), commits=(None, None))), ("p2", dict(stopped(), commits="absent")),
                     ("p3", dict(status="stopped", note=N, commits=(None, None)))):     # p3: no note file at all
        code, got, err, git, _ = run(name, **kw)
        assert code == 3 and pre in err and not got and not git.shown, (name, code, err)
        n += 1
    code, got, err, git, _ = run("p4", **dict(stopped(), commits=("e" * 40, None)))   # one commit recorded: read
    assert code == 0 and got[OUT_NAME][-1] == "exit 0", (code, err)
    e_test, e_leaves = _e_precommit_rule()
    assert e_leaves == [("start", "cj.get('start_commit')"), ("commit", "cj.get('commit')")], e_leaves
    for st_ in ("stopped", "done", "running", None):
        for a in (None, "e" * 40):
            for b in (None, "e" * 40):
                assert bool(eval(e_test, {}, {"status": st_, "start": a, "commit": b})) == \
                    (st_ == "stopped" and before_campaign_commit(a, b)), ("not E's pre-commit rule", st_, a, b)
    un = "fr stopped after gate FR was written but not applied"           # IX-15

    def gate(*rels):                            # files under fr/, committed (never opened by the read)
        def edit(s2, git):
            for rel in rels:
                p = os.path.join(s2, "fr", *rel.split("/"))
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w") as fh:
                    fh.write("{}")
                if git is not None:
                    git.at_head(p)
        return edit
    with_note = lambda *rels: (lambda s2, git: (note(N)(s2, git), gate(*rels)(s2, git)))
    for name, kw in (("u1", dict(status="stopped", note=N, edit=with_note("gates/FR.json", "gates_applied/"
                                                                          "gate_FR.inputs.json"))),
                     ("u2", dict(status="stopped", note=N, edit=gate("gates/FR.json")))):     # u2: no note file
        code, got, err, git, _ = run(name, **kw)
        assert code == 3 and un in err and not got and not git.shown, (name, code, err)
        n += 1
    for name, kw in (("u3", dict(status="stopped", note=N, edit=with_note("gates/FR.json", "gates_applied/"
                                                                          "gate_FR.gate.json"))),
                     ("u4", dict(edit=gate("gates/FR.json")))):          # applied beside it; a done fr: read
        code, got, err, git, _ = run(name, **kw)
        assert code == 0 and got[OUT_NAME][-1] == "exit 0", (name, code, err)
    e_fn, e_test = _e_unapplied_rule()
    lay = os.path.join(tmp, "ix15")
    for i, files in enumerate(((), ("gates/FR.json",), ("gates_applied/gate_FR.gate.json",),
                               ("gates/FR.json", "gates_applied/gate_FR.gate.json"),
                               ("gates/FR.json", "gates_applied/gate_FR.json", "gates_applied/gate_FR.inputs.json"))):
        fr = os.path.join(lay, str(i), "fr")
        os.makedirs(fr)
        gate(*files)(os.path.dirname(fr), None)
        for st_ in ("stopped", "done", "running", None):
            me = st_ == "stopped" and gate_fr_unapplied(fr)
            e_self = type("Run", (), {"L": type("L", (), {"cdir": staticmethod(lambda c, d=fr: d)})})()
            assert bool(eval(e_test, {}, {"status": st_, "self": e_self, "gate_fr_unapplied": e_fn})) == me and \
                e_fn(fr) == gate_fr_unapplied(fr), ("not E's IX-15 rule", files, st_)
    sha = hashlib.sha256(good.encode()).hexdigest()
    for name, kw in (("v1", {}), ("v2", dict(tree="2026-11-22: the fr STOP is final (in the tree only).\n"))):
        code, got, err, git, here = run(name, **stopped(**kw))
        h = got.get(OUT_NAME, [""])
        assert code == 0 and h[-1] == "exit 0" and re.fullmatch(
            r"FR geometry read \(S2B_PLAN\.md section 6b\), attempt 1, at 0{40}; fr/campaign\.json status 'stopped' "
            r"\(final STOP: stop note s2/FR_STOP_NOTE\.md sha256 " + sha + r"\); verify record "
            r"fr_verify/verify_fr\.txt "
            r"sha256 [0-9a-f]{64}; tools sha256 fr_geom_read [0-9a-f]{12}, part_d_read [0-9a-f]{12}, check5_diag "
            r"[0-9a-f]{12}, s2b/guard [0-9a-f]{12}", h[0]), (name, code, err, h[0])
    made, errs = [], []                         # main_read's own git: _git_cli (attempt 1 of v2 is not yet committed)
    with _mutant("_git_cli", lambda repo: made.append(repo) or git):                      # scaffolding
        code = main_read(repo=os.path.dirname(here), s2=os.path.join(os.path.dirname(here), "s2"), here=here,
                         reader=lambda root, out: (True, {}), echo=[].append, err=errs.append, stop_note=N)
    assert code == 3 and made == [os.path.dirname(here)] and "committed unedited" in errs[-1], (code, made, errs)
    seen = []

    def cli(*argv):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            try:
                return main(list(argv))
            except SystemExit as x:
                return f"SystemExit {x.code}"
    with _mutant("main_read", lambda **kw: seen.append(kw) or 0):                       # scaffolding
        got = [cli("--read", "--stop-note", f"{NOTE_ROOT}/{NOTE_NAME}"), cli("--read"), cli("--read", "--final-stop")]
    assert got == [0, 0, "SystemExit 2"] and seen == [{"stop_note": f"{NOTE_ROOT}/{NOTE_NAME}"}, {"stop_note": None}], \
        (got, seen)
    assert "\n    python fr_geom_read.py --read [--stop-note NOTE]\n" in __doc__ and "--final-stop]" not in __doc__, \
        "the usage line is not the parser's"
    return f"{n} refusals (exit 3, nothing written: 'stopped' without a note, a note on 'done', 15 notes failing one " \
           f"of E's tests or the one path, a C2 path before git, a STOP before the campaign commit (3), gate FR " \
           f"written but not applied (2)); E's rules for the last two pinned; a final STOP read with the note's path " \
           f"and sha256 of its text at HEAD (twice: one tree edit hidden from git status), also with gate FR applied; " \
           f"--stop-note to main_read through the command line, --final-stop refused; main_read's git is _git_cli"


def _bad_maps(cd, kind, n_host, leg):                    # broken: old_to_new ignored (the deleted FA and the shift)
    if kind in ("D", "DV"):
        m = {c: c for c in range(len(leg["old_to_new"]))}
        return (m, m) if kind == "D" else ({c: (c if c < VI else c + 1) for c in m}, m)
    return cd.maps_section4(kind, n_host, leg)


def _attempt_at_head_only(git, repo, here):              # broken: the code before review (refused only at HEAD)
    p = os.path.join(here, OUT_NAME)
    if git("cat-file", "-e", "HEAD:" + os.path.relpath(p, repo)).returncode == 0:
        raise Refused("the output is published at HEAD")
    return 1, p


def _tracked_before_fix():                               # broken: the code before review (named files only)
    return [HERE, os.path.join(S2, "s2b"), os.path.join(S2, "figures", "fig_s2_c2_a2.py")] + \
        [os.path.join(REPO, "scripts", f) for f in ("46_s2_cells.py", "47_s2_qe.py", "49_s2_gates.py")]


def _tracked_without_here():                             # broken: c2_diagnostic/ dropped from the fixed list
    fixed = [os.path.join(S2, "s2b"), os.path.join(S2, "figures", "fig_s2_c2_a2.py"), os.path.join(REPO, "scripts")]
    return fixed + [f for f in code_files() if not any(f == p or f.startswith(p + os.sep) for p in fixed)]


def _attempt2_tree_only(git, repo, here):                # broken: an attempt-2 output at HEAD but deleted not counted
    p1, p2 = os.path.join(here, OUT_NAME), os.path.join(here, OUT2_NAME)
    at_head = lambda p: git("cat-file", "-e", "HEAD:" + os.path.relpath(p, repo)).returncode == 0
    if os.path.exists(p2):
        raise Refused(f"{OUT2_NAME} exists: a third attempt is refused")
    if not (os.path.exists(p1) or at_head(p1)):
        return 1, p1
    st = git("status", "--porcelain", "--", p1)
    if not (os.path.exists(p1) and at_head(p1)) or st.returncode != 0 or st.stdout.strip():
        raise Refused(f"{OUT_NAME} is not committed unedited at HEAD")
    return 2, p2


def _failing_variant(dr_max=0.25, rot_max=20.0, carbon=True, element_at_parent=False):
    """A broken failing_objects (round-2 review: bounds other than R46's, the carbon criterion dropped, the element
    read at the parent index)."""
    def f(d5, r46, c2p, c2h, symbols):
        failing = {r["child"]: r for r in d5["rows"] if r["gated"] and not r["pass"]}
        L = r46["lists"]["gated"]
        for r in L["inorganic"]:
            if r["dr_A"] >= dr_max and r["index"] not in failing:
                i = r["index"]
                failing[i] = {"kind": "inorganic", "child": i, "parent": c2p[i], "host": c2h[i],
                              "element": symbols[c2p[i] if element_at_parent else i]}
        for r in L["fa"]:
            if ((carbon and r["dr_carbon_A"] >= dr_max) or r["rot_deg"] >= rot_max) and r["carbon"] not in failing:
                failing[r["carbon"]] = {"kind": "FA", "child": r["carbon"], "parent": c2p[r["carbon"]],
                                        "host": c2h[r["carbon"]]}
        return failing
    return f


def _header_without_tools(attempt, prev, head, status, final, vsha):   # broken: the tool hashes dropped
    return (f"FR geometry read (S2B_PLAN.md section 6b), attempt {attempt}{prev}, at {head}; fr/campaign.json status "
            f"{status!r}" + (" (CAMPAIGN_DONE)" if final is None else
                             f" (final STOP: stop note {final[0]} sha256 {final[1]})") +
            f"; verify record {VERIFY} sha256 {vsha}")


def _header_before_ix1(attempt, prev, head, status, final, vsha):   # broken: the header before IX-1 (no stop note)
    sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()[:12]
    return (f"FR geometry read (S2B_PLAN.md section 6b), attempt {attempt}{prev}, at {head}; fr/campaign.json status "
            f"{status!r}" + (" (--final-stop: FR's final stop)" if final else " (CAMPAIGN_DONE)") +
            f"; verify record {VERIFY} sha256 {vsha}; tools sha256 fr_geom_read {sha(os.path.abspath(__file__))}, "
            f"part_d_read {sha(os.path.join(HERE, 'part_d_read.py'))}, check5_diag "
            f"{sha(os.path.join(HERE, 'check5_diag.py'))}, s2b/guard {sha(os.path.join(S2, 's2b', 'guard.py'))}")


def _main_final_stop(argv=None):                         # broken: the command line before IX-1 (a bare --final-stop)
    ap = argparse.ArgumentParser(description="The FR geometry read (S2B_PLAN.md section 6b)")
    for flag in ("--self-test", "--without-wp2e", "--read", "--final-stop"):
        ap.add_argument(flag, action="store_true")
    a = ap.parse_args(argv)
    return main_read(stop_note="--final-stop" if a.final_stop else None) if a.read else 0


def _final_stop_bare(git, repo, s2, status, note):        # broken: the code before IX-1 (a STOP final on the
    if status != ("stopped" if note is not None else "done"):    # operator's word: the note named, never tested)
        raise Refused(f"fr/campaign.json status {status!r}" + ("" if note is None else " with --stop-note") +
                      ": the read runs after CAMPAIGN_DONE (status 'done', no stop note) or after FR's final STOP "
                      "(status 'stopped', with --stop-note NOTE, the stop note that makes it final: IX-1) (S2B_PLAN.md "
                      "section 6b)")
    return None if note is None else (note, "0" * 64)


def _note_ok_variant(place=True, s2b=False, phrase=True, date=True, fixed=True):
    """A broken stop_note_ok (IX-1, IX-6): the place under S2/ not tested, s2b/ admitted, the phrase or the date not
    tested, or any path under S2/ admitted (the rule before IX-6)."""
    def f(path, text, s2_rel=NOTE_ROOT):
        return (not fixed or path == f"{s2_rel}/{NOTE_NAME}") and (not place or path.startswith(s2_rel + "/")) and \
            (s2b or not path.startswith(f"{s2_rel}/s2b/")) and \
            (not phrase or bool(STOP_PHRASE.search(text))) and (not date or bool(ISO_DATE.search(text)))
    return f


def _note_path_before_ix6(path, s2_rel=NOTE_ROOT):        # broken: the place rule of IX-1, any path under S2/
    return path.startswith(s2_rel + "/") and not path.startswith(f"{s2_rel}/s2b/")


def _note_text_variant(normalised=True, guarded=True, clean=True, at_head=True, blob=True):
    """A broken note_text (IX-1, IX-6): the path not required normalised, the refusal of blinded paths dropped, the
    clean test dropped, the text read from the tree, or git show without the blob test."""
    def f(git, repo, s2, note):
        if normalised and (not isinstance(note, str) or note.startswith("/") or
                           any(s in ("", ".", "..") for s in note.split("/"))):
            raise Refused(f"--stop-note {note!r}: a normalised repository-relative path is required (IX-1)")
        p = os.path.join(repo, *note.split("/"))
        why = guarded and _refuse_path(p, {"root": s2, "campaign": "fr", "labels": (), "s2_roots": (S2, s2)})
        if why:
            raise Refused(f"--stop-note {note}: refused before it is read: {why} (S2B_PLAN.md section 6b)")
        if not note_path_ok(note, os.path.relpath(os.path.realpath(s2), os.path.realpath(repo)).replace(os.sep, "/")):
            raise Refused(f"--stop-note {note}: the stop note is the one file (IX-6)")
        k = git("cat-file", "-t", "HEAD:" + note)
        st, r = git("status", "--porcelain", "--", p), git("show", "HEAD:" + note)
        if not os.path.isfile(p) or (clean and (st.returncode != 0 or st.stdout.strip())) or r.returncode != 0 or \
                (blob and k.stdout.strip() != "blob"):
            raise Refused(f"--stop-note {note} is not committed and clean (a file at HEAD, unchanged in the tree; "
                          f"IX-1)")
        if at_head:
            return r.stdout
        with open(p, "rb") as fh:
            return fh.read().decode(errors="replace")
    return f


def _leaf_words_valid_twice(vf):                         # broken: 'valid as written' printing validity_final.valid
    return (f"valid {vf.get('valid')}; failed {vf.get('failed')}; valid as written {vf.get('valid')}; failed as "
            f"written {vf.get('failed_as_written')}; invariant only {vf.get('invariant_only')}; check-5 reading "
            f"{vf.get('check5_reading')}; parent {vf.get('parent')}; parent_final {vf.get('parent_final')}")


def _failing_d5_only(d5, r46, c2p, c2h, symbols):        # broken: R46-only failures dropped
    return {r["child"]: r for r in d5["rows"] if r["gated"] and not r["pass"]}


def _waiting(p):
    return p is not None and p["first_failure"] is None and p["next"] is None and p["passed"] is None


def _passed_none_disagrees(p, stop, f=progress_agrees):  # broken: a waiting check read as a disagreement
    return False if _waiting(p) else f(p, stop)


def _waiting_agrees_any(p, stop, f=progress_agrees):     # broken: a waiting check agreeing with a stop of any kind
    return stop is not None if _waiting(p) else f(p, stop)


def _refusal_agrees(p, stop, f=progress_agrees):         # broken: a refusal of fr_progress read as agreement
    return True if p is None else f(p, stop)


def _item5_fa_as_written(gated, fr, f=item5_objects):    # broken: the invariant FA chosen by the as-written rotation
    objs = f([dict(r, rot_exchanged_deg=r["rot_deg"]) if r["kind"] == "FA" else r for r in gated], fr)
    return objs


CASES = [
    ("C2 cases of part_d_read through the generalised code paths", t_c2,
     [("item4_reference", lambda A, x, ip, fp: (fp, "parent final")), ("stop_on_mismatch", lambda ok: False)]),
    ("A-site substitution map of m30_Cs188p0", t_asite_map, [("index_maps", _bad_maps)]),
    ("FR route: all four complete", t_r1,
     [("FR_PAIRS", [FR_PAIRS[0], FR_PAIRS[1], (FR["DV"], FR["host"])]),
      ("item2_compare", lambda ri, ra, d5, r46, f=item2_compare: dict(f(ri, ra, d5, r46),
                                                                      invariant_only=bool(d5["passed_exchanged"]))),
      ("started_after_stop", lambda recs, stop: {FR["DV"]: "complete"})]),     # broken: a false item-1 mismatch
    ("FR route: early stop after V+_R fails check 5", t_r2,
     [("pairs_up_to", lambda s, p: [x for x in p if s is None or FR_ORDER.index(x[0]) < s[0]]),
      ("item4_reference", lambda A, x, ip, fp: (fp, "parent final")),
      ("started_after_stop", lambda recs, stop: {} if stop is None else       # broken: not_run_gate counted started
       {l: recs[l].get("status") for l in FR_ORDER[stop[0] + 1:] if recs.get(l) is not None})]),
    ("FR route: early stop after Cs D fails check 5", t_r3,
     [("index_maps", _bad_maps), ("pairs_up_to", lambda s, p: list(p)[:1]),
      ("item4_reference", lambda A, x, ip, fp: (fp, "parent final"))]),
    ("FR route: Cs D+V+ fails check 5", t_r4, [("item4_reference", lambda A, x, ip, fp: (x["host"], "host")),
                                                ("item4_reference", lambda A, x, ip, fp: (fp, "parent final"))]),
    ("FR route: two gated FA of Cs D, one turned, one exchanged", t_fa2,
     [("item5_objects", _item5_fa_as_written),
      ("item5_objects", lambda gated, fr, f=item5_objects: f(gated, fr)[:2])]),
    ("FR route: stop on Cs D's end rule, check evaluated", t_endrule,
     [("pairs_up_to", lambda s, p: [x for x in p if s is None or FR_ORDER.index(x[0]) < s[0]])]),
    ("read states through the early stop only", t_states,
     [("pairs_read", lambda pdr, s, p, VR, f: [(c, a) for c, a in pairs_up_to(s, p) if a in f]),
      ("progress_agrees", _passed_none_disagrees)]),
    ("early stop of every kind at every position", t_stop,
     [("end_accepted", lambda g, o: o == "accepted_converged"),
      ("pairs_up_to", lambda s, p: [x for x in p if s is None or FR_ORDER.index(x[0]) < s[0]]),
      ("progress_agrees", _passed_none_disagrees)]),
    ("invariant-only pass at FA188, printed words", t_r5,
     [("item2_compare", lambda ri, ra, d5, r46, f=item2_compare: f(
         ri, ra, dict(d5, passed_exchanged=d5["passed"]), r46)),           # broken: the record against D5 as written
      ("fr_leaf_words", _leaf_words_valid_twice),
      ("item3_row", lambda r, f=item3_row: f(dict(r, **{"pass": r["pass_exchanged"], "pass_exchanged": r["pass"]}))),
      ("item2_fr_line", lambda ch, pa, rp, ra, cmp, r46, dis, f=item2_fr_line: f(
          ch, pa, rp, ra, dict(cmp, d5_inv=cmp["d5_aw"], d5_aw=cmp["d5_inv"]), r46, dis))]),
    ("item 2: both readings, gated counts and lists, R46-only failures at R46's bounds", t_item2,
     [("item2_compare", lambda ri, ra, d5, r46, f=item2_compare: f(ri, bool(d5["passed"]), d5, r46)),
      ("item2_compare", lambda ri, ra, d5, r46, f=item2_compare: dict(      # broken: the deciding reading dropped
          f(ri, ra, d5, r46), disagree=bool(r46["passed"]) != bool(d5["passed"]) or bool(ra) != bool(d5["passed"]))),
      ("gated_compare", lambda d5, r46, rn, f=gated_compare: dict(f(d5, r46, rn), r46_equal=True, record_equal=True)),
      ("gated_compare", lambda d5, r46, rn, f=gated_compare: (lambda g: dict(  # broken: n_fa compared alone
          g, record_equal=g["n_record"][1] == g["n_d5"][1]))(f(d5, r46, rn))),
      ("gated_compare", lambda d5, r46, rn, f=gated_compare: (lambda g: dict(  # broken: inorganic lists compared alone
          g, r46_equal=not g["d5_only"][0] and not g["r46_only"][0]))(f(d5, r46, rn))),
      ("failing_objects", _failing_d5_only), ("failing_objects", _failing_variant(carbon=False)),
      ("failing_objects", _failing_variant(dr_max=0.30)), ("failing_objects", _failing_variant(rot_max=25.0)),
      ("failing_objects", _failing_variant(dr_max=0.2500001)),
      ("failing_objects", _failing_variant(element_at_parent=True)),
      ("item2_fr_line", lambda ch, pa, rp, ra, cmp, r46, dis, f=item2_fr_line: f(
          ch, pa, rp, ra, cmp, dict(r46, passed=cmp["d5_aw"]), dis))]),     # broken: the R46 word showing D5's
    ("item-1 mismatch ends the read", t_mismatch,
     [("progress_agrees", lambda p, s: True), ("stop_on_mismatch", lambda ok: False),
      ("item1_presence", lambda A, lab, vf: {}), ("progress_agrees", _waiting_agrees_any),
      ("progress_agrees", _refusal_agrees), ("started_after_stop", lambda recs, stop: {}),
      ("label_ok", lambda vr, vf, lab, par: vr.get("label") == lab and vr.get("parent_label") == par),
      ("reading_ok", lambda a, b: a == b)]),
    ("fr graph against the gate code's grammar", t_graph,
     [("graph_mismatch", lambda g49, lab, j: None),
      ("graph_mismatch", lambda g49, lab, j, f=graph_mismatch: None if f(g49, lab, j) == "graph leg" else
       f(g49, lab, j))]),
    ("refusal: gate file and blinded paths", t_gate,
     [("_refuse_path", lambda p, c: None), ("GATE_DIRS", ("gates", "gates_applied")),
      ("BLIND_C1", ("records", "gates", "gates_applied")), ("GATE_SUFFIXES", (".inputs.json",)),
      ("RAW_SUFFIXES", (".a2.json",)), ("_temporary", lambda p: True), ("RAW_RE", r"\.out\.gz$"),
      ("RAW_RE", r"\.out(\.gz)?$")]),
    ("refusal: blinded leaf", t_leaf, [("fr_guard", lambda gd, fig: fig.guarded)]),
    ("refusal: calculator module loaded", t_calc, [("_no_calculator", lambda *a: None)]),
    ("G guards: raw fr outputs only, positions only (placeholder parts)", t_g_guards,
     [("g_part_ok", lambda A, l, p: True), ("reads_changed", lambda q, b: []), ("g_part_ok", lambda A, l, p: False)]),
    ("G: real G on fr raw parts cut from the public WP2e output", t_g_real, []),
    ("--read: 6b 'When', outputs, attempts, exit codes, header, uncommitted code", t_main,
     [("output_attempt", _attempt_at_head_only), ("output_attempt", _attempt2_tree_only),
      ("tracked_paths", _tracked_before_fix), ("tracked_paths", lambda: code_files()),
      ("tracked_paths", _tracked_without_here), ("REFUSED", 1),
      ("when_ok", lambda git, repo, s2, note=None: ("done", "0" * 64, None)),   # broken: the code before review
      ("read_header", _header_without_tools)]),                                  # (fr/ only)
    ("stop note: E's phrase and rules (s2b/e_eval.py), on throwaway git repositories (IX-1, IX-6)", t_note_rules,
     [("STOP_PHRASE", re.compile(r"the fr STOP is final")), ("ISO_DATE", re.compile(r"(20\d\d)-(\d\d)-(\d\d)")),
      ("stop_note_ok", _note_ok_variant(s2b=True, fixed=False)), ("stop_note_ok", _note_ok_variant(fixed=False)),
      ("stop_note_ok", _note_ok_variant(place=False, fixed=False)), ("note_path_ok", _note_path_before_ix6),
      ("NOTE_NAME", "FR_STOP.md"),
      ("_git_cli", lambda repo: lambda *a: subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True)),
      ("note_text", _note_text_variant(at_head=False)), ("note_text", _note_text_variant(clean=False))]),
    ("--read: a final STOP only through a stop note (IX-1)", t_stop_note,
     [("final_stop", _final_stop_bare),
      ("final_stop", lambda git, repo, s2, status, note, f=final_stop:          # broken: 'stopped' without a note
       None if note is None and status == "stopped" else f(git, repo, s2, status, note)),
      ("final_stop", lambda git, repo, s2, status, note, f=final_stop:          # broken: a stop note on 'done'
       f(git, repo, s2, "stopped" if note is not None else status, note)),
      ("stop_note_ok", _note_ok_variant(phrase=False)), ("stop_note_ok", _note_ok_variant(date=False)),
      ("note_path_ok", _note_path_before_ix6),
      ("note_text", _note_text_variant(normalised=False)), ("note_text", _note_text_variant(clean=False)),
      ("note_text", _note_text_variant(at_head=False)), ("note_text", _note_text_variant(guarded=False)),
      ("read_header", _header_before_ix1), ("main", _main_final_stop),
      ("__doc__", __doc__.replace("--read [--stop-note NOTE]", "--read [--final-stop]")),
      ("before_campaign_commit", lambda start, commit: False),                # broken: the rule of review 2 removed
      ("before_campaign_commit", lambda start, commit: start is None),       # broken: one leaf only
      ("gate_fr_unapplied", lambda fr: False),                               # broken: IX-15 removed
      ("gate_fr_unapplied", lambda fr: os.path.exists(os.path.join(fr, "gates_applied", "gate_FR.inputs.json")) and
       not os.path.exists(os.path.join(fr, "gates_applied", "gate_FR.json")))]),   # broken: the marker, not the copy
]


def self_test(wp2e=True):
    """The cases above, each on the code and on its broken variants. wp2e False (--without-wp2e) skips real G on the
    public WP2e output only: that run is not the full self-test, which the dated commit needs, and it still reads the
    real C1 structure archive through part_d_read's loader (IX-9)."""
    pdr, cd, fig, q47, c46, g49, gd = tools()
    pdr.self_test()                                       # part_d_read's own cases, unchanged
    pdr.self_test_read()
    _ROUTES.clear()
    _ROUTES["_tmp"] = tempfile.mkdtemp(prefix="frgeom_")
    run = [c for c in CASES if wp2e or c[1] is not t_g_real]
    try:
        for name, fn, mutants in run:
            msg = fn()
            caught = []
            for target, bad in mutants:
                with _mutant(target, bad):
                    try:
                        fn()
                    except AssertionError as e:
                        caught.append(f"{target}: {str(e)[:60]}")
                        continue
                raise _Undetected(f"{name}: passes on the broken variant {target}")
            print(f"  {name}: {msg}; fails on {len(caught)} broken variant(s) [{' | '.join(caught)}]")
        _no_calculator()
        assert not _CTX.get("on") and not any(q47.READS.get(k, 0) for k in ("F", "forces")), "a value was read"
    finally:
        shutil.rmtree(_ROUTES.pop("_tmp"), ignore_errors=True)
        _ROUTES.clear()
    nb = sum(len(m) for _, _, m in run)
    if wp2e:
        print(f"FR geometry read self-test passed: {len(run)} cases, each but real G also failing on its deliberately "
              f"broken variants ({nb} in all); synthetic archives from the public C1 cells; no fr or C2 file read")
    else:
        print(f"FR geometry read self-test passed WITHOUT the WP2e case (--without-wp2e; not the full self-test): "
              f"{len(run)} of {len(CASES)} cases, each also failing on its deliberately broken variants ({nb} in all); "
              f"real G on the public WP2e output not run; no fr or C2 file read")


# ---- the one read ----------------------------------------------------------------------------------------------------

def code_files():
    """Every module file under the repository loaded in this process, those loaded by path included (gc)."""
    r = os.path.realpath(REPO) + os.sep
    mods = [m for m in gc.get_objects() if isinstance(m, types.ModuleType)] + list(sys.modules.values())
    fs = {os.path.realpath(m.__file__) for m in mods if isinstance(getattr(m, "__file__", None), str)}
    return sorted(f for f in fs if f.startswith(r))


def tracked_paths():
    """The code the read runs on, which must be committed (part d, 'When'): c2_diagnostic/, s2b/, the C2 figure
    module, scripts/ and every module file under the repository loaded in this process."""
    fixed = [HERE, os.path.join(S2, "s2b"), os.path.join(S2, "figures", "fig_s2_c2_a2.py"),
             os.path.join(REPO, "scripts")]
    under = lambda f: any(f == p or f.startswith(p + os.sep) for p in map(os.path.realpath, fixed))
    return fixed + [f for f in code_files() if not under(f)]


def output_attempt(git, repo, here):
    """(attempt, path) of this run (S2B 7, which G2 and the FR geometry read follow): attempt 1 writes OUT_NAME; the
    one rerun writes OUT2_NAME, only once attempt 1's output is committed unedited at HEAD; a third attempt is refused.
    An output counts as existing in the working tree or at HEAD. Raises Refused."""
    p1, p2 = os.path.join(here, OUT_NAME), os.path.join(here, OUT2_NAME)
    at_head = lambda p: git("cat-file", "-e", "HEAD:" + os.path.relpath(p, repo)).returncode == 0
    if os.path.exists(p2) or at_head(p2):
        raise Refused(f"{OUT2_NAME} exists: the read has run twice, and a third attempt is refused (S2B_PLAN.md "
                      f"section 7)")
    if not (os.path.exists(p1) or at_head(p1)):
        return 1, p1
    st = git("status", "--porcelain", "--", p1)
    if not (os.path.exists(p1) and at_head(p1)) or st.returncode != 0 or st.stdout.strip():
        raise Refused(f"{OUT_NAME} is not committed unedited at HEAD: attempt 1's output is committed before the one "
                      f"rerun (S2B_PLAN.md section 7)")
    return 2, p2


def when_ok(git, repo, s2, note=None):
    """(status, verify sha256, final STOP) if the read may run now (S2B 6b, 'When': once, after CAMPAIGN_DONE or FR's
    final stop and after verify, before C3b and before E; S2B 2 and the FR operations note: validity leaves only after
    CAMPAIGN_DONE or the final STOP and after verify). Raises Refused otherwise. fr/campaign.json is read for its leaves
    status, start_commit and commit alone, by name, through GuardedS2b: 'done' is written by scripts/50 finish at
    CAMPAIGN_DONE, 'stopped' by begin_stop at a STOP, which is final only through the stop note named by --stop-note
    (final_stop, IX-1: None at CAMPAIGN_DONE, else the note's path and sha256). Before the note is read, a stopped fr
    is refused when both commits are null (integration review 2; amendment item 11) or when gate FR was written but not
    applied (IX-15; gate_fr_unapplied, by name only), as E refuses both."""
    pdr, gd = _TOOLS["pdr"], _TOOLS["gd"]
    at_head = lambda p: git("cat-file", "-e", "HEAD:" + os.path.relpath(p, repo)).returncode == 0
    clean = lambda p: (lambda st: st.returncode == 0 and not st.stdout.strip())(git("status", "--porcelain", "--", p))
    fr = os.path.join(s2, "fr")
    try:
        g = gd.guarded_s2b(os.path.join(fr, "campaign.json"))       # None if absent
        status = None if g is None else pdr.leaf(g, "status")
        commits = (None, None) if g is None else (pdr.leaf(g, "start_commit"), pdr.leaf(g, "commit"))
    except (OSError, ValueError, AttributeError):                   # unreadable, not JSON, not an object
        status, commits = None, (None, None)
    if status == "stopped" and before_campaign_commit(*commits):  # integration review 2: before the note is read
        raise Refused("fr stopped before its campaign commit was recorded (fr/campaign.json start_commit and commit "
                      "null): not read until a dated amendment rules on this route, as E refuses it (amendment "
                      "2026-11-12a item 11; S2B_PLAN.md section 6b)")
    if status == "stopped" and gate_fr_unapplied(fr):              # IX-15: by name only, before the note is read
        raise Refused("fr stopped after gate FR was written but not applied (fr/gates/FR.json without "
                      "fr/gates_applied/gate_FR.gate.json): not read; the route is resolved by a dated fix and a "
                      "relaunch, never by a stop note, as E refuses it (IX-15; S2B_PLAN.md section 6b)")
    final = final_stop(git, repo, s2, status, note)
    vp = os.path.join(s2, VERIFY)
    if not (os.path.isfile(vp) and at_head(vp) and clean(vp)):
        raise Refused(f"the fr verify record {VERIFY} is not committed unedited at HEAD: the read runs after verify "
                      f"(S2B_PLAN.md section 6b; amendment 2026-11-12a item 10)")
    if not (at_head(fr) and clean(fr)):
        raise Refused("the fr archive is not committed unedited at HEAD: the read runs on the committed, verified "
                      "archive (S2B_PLAN.md section 6b)")
    for rel in NOT_YET:
        q = os.path.join(s2, rel)
        if os.path.lexists(q) or at_head(q):
            raise Refused(f"{rel} exists: the read runs before C3b and before E (S2B_PLAN.md section 6b)")
    with open(vp, "rb") as fh:
        return status, hashlib.sha256(fh.read()).hexdigest(), final


def read_header(attempt, prev, head, status, final, vsha):
    """Line 1 of the output: attempt, HEAD, the campaign status (at a final STOP with the stop note's path and sha256,
    IX-1) and the verify record (S2B 6b, 'When'), and the sha256 of the four tool files."""
    sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()[:12]
    return (f"FR geometry read (S2B_PLAN.md section 6b), attempt {attempt}{prev}, at {head}; fr/campaign.json status "
            f"{status!r}" + (" (CAMPAIGN_DONE)" if final is None else
                             f" (final STOP: stop note {final[0]} sha256 {final[1]})") +
            f"; verify record {VERIFY} sha256 {vsha}; tools sha256 fr_geom_read {sha(os.path.abspath(__file__))}, "
            f"part_d_read {sha(os.path.join(HERE, 'part_d_read.py'))}, check5_diag "
            f"{sha(os.path.join(HERE, 'check5_diag.py'))}, s2b/guard {sha(os.path.join(S2, 's2b', 'guard.py'))}")


def main_read(git=None, *, repo=REPO, s2=S2, here=HERE, reader=None, echo=print, err=None, stop_note=None):
    """The one read (S2B 6b; part d, 'When'; S2B 7, failure and rerun rules). It refuses, with exit 3 and nothing
    written, a third attempt, a rerun before attempt 1's output is committed unedited, uncommitted code, a missing fr
    archive and a read outside 6b's 'When' (when_ok; at a STOP, stop_note names the stop note that makes it final,
    IX-1). It computes every item in memory and writes the whole output in one piece to the attempt's file, by exclusive
    create, with its exit code on the last line, then prints it: exit 0 (items 1-5), 1 (item 1 with its mismatch) or 2
    (a failure before output: the stage and the exception type only)."""
    git = git or _git_cli(repo)
    err = err or (lambda s: print(s, file=sys.stderr))
    reader = reader or (lambda root, out: read(root, out=out, campaign="fr"))

    def refused(msg):
        err("refused: " + msg)
        return REFUSED
    tools()
    try:
        attempt, path = output_attempt(git, repo, here)
    except Refused as e:
        return refused(str(e))
    paths = tracked_paths()
    st = git("status", "--porcelain", "--", *paths)
    if st.returncode != 0 or st.stdout.strip():
        return refused("the FR geometry read code is not committed (S2B_PLAN.md section 6b; part d, 'When')")
    if not os.path.isdir(os.path.join(s2, "fr")):
        return refused("there is no fr archive (S2B 6b: after CAMPAIGN_DONE or FR's final stop, and verify)")
    try:
        status, vsha, final = when_ok(git, repo, s2, stop_note)
    except Refused as e:
        return refused(str(e))
    head = git("rev-parse", "HEAD").stdout.strip()
    sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()[:12]
    prev = ""
    if attempt == 2:
        p1 = os.path.join(here, OUT_NAME)
        last = (open(p1).read().splitlines() or [""])[-1]
        prev = f" (attempt 1: {OUT_NAME} sha256 {sha(p1)}, last line '{last}')"
    hdr = read_header(attempt, prev, head, status, final, vsha)
    checked = [os.path.realpath(p) for p in paths]
    lines = []
    try:
        ok, _ = reader(s2, lines.append)
        q47 = _TOOLS["q47"]
        assert all(q47.READS.get(k, 0) == 0 for k in READ_KEYS), "a scripts/47 READS counter is not zero at exit"
        late = [f for f in code_files() if not any(f == p or f.startswith(p + os.sep) for p in checked)]
        if late:
            st = git("status", "--porcelain", "--", *late)
            if st.returncode != 0 or st.stdout.strip():
                raise Uncommitted("a module first loaded during the read is not committed")
        body, code = lines, (0 if ok else 1)
    except Exception as e:                       # the stage and the exception type only (S2B section 7 rules)
        stage = "after the items" if lines and lines[-1].startswith("END") else \
            "at " + next((l.split(".")[0] for l in reversed(lines) if l.startswith("ITEM")), "before item 1")
        body, code = [f"FR geometry read failed before output: {type(e).__name__} {stage}"], 2
    text = "\n".join([hdr] + body + [f"exit {code}"]) + "\n"
    with open(path, "x") as fh:
        fh.write(text)
    echo(text.rstrip("\n"))
    return code


def main(argv=None):
    """The command line (IX-1: --stop-note NOTE, a repository-relative path, replaces the bare --final-stop)."""
    ap = argparse.ArgumentParser(description="The FR geometry read (S2B_PLAN.md section 6b)")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--without-wp2e", action="store_true",
                    help="with --self-test: every case but real G on the public WP2e output (not the full self-test)")
    ap.add_argument("--read", action="store_true")
    ap.add_argument("--stop-note", metavar="NOTE",
                    help="with --read, after FR's final STOP (fr/campaign.json status 'stopped'): the committed stop "
                         "note that makes it final (repository-relative; IX-1, as E and the FR figure); in the header")
    a = ap.parse_args(argv)
    if a.self_test:
        self_test(wp2e=not a.without_wp2e)
    elif a.read:
        return main_read(stop_note=a.stop_note)
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
"""Figure S2b-FR: the four relaxations of the far-site reference FR (Cs at m30 FA188) and the fr gates, as fixed by
section 4 ('The figure') of the fr operations note, which adapts C2_OPERATIONS.md D-C2-11 and D-C2-12.

The figure is committed with its self-test before any fr record is read on the laptop; it was developed only on
synthetic archives made from the public WP2e output. Its claim is stated in the FR note, after fr has ended and its
archive has been verified (operations note sections 2 and 4).

  a  Force criterion of each FR relaxation of the attempt in force (host_R, V+_R, Cs D, Cs D+V+ at A188, in the run
     order FR_ORDER): the largest Cartesian force component on the free atoms against configuration k, on a log axis.
  b  The state of the gates fr_step0@2, fr_step0@4 and FR. No step-0 value and no FR-2 value is read or shown.
  c  Cost: configurations and minutes per configuration of each relaxation, and the fr node-hours against the
     S2B_PLAN.md section 8 range. There is no projection strip (fr computes none).

Blinding (S2B_PLAN.md sections 0, 1; operations note sections 2 and 4). The script reads no fr energy at all: no F(k)
of a relaxation, no step-0 dF, no F of a C1 reference single point, no E_b, no delta_far, no plateau difference. The
A2 outputs are read with scripts/47 in count mode (no value) and by their force rows (the D-C2-11 reader of
fig_s2_c2_a2.py, used unchanged); the '!' lines are never parsed, and the build asserts that scripts/47 read no value
other than forces. Every fr JSON file the build opens is read through s2b/guard.py: the A2 records, campaign.json,
state_end.json, completeness.json, HARD_CAP.json and ledger.json through GuardedS2b (a field by its name; a withheld
field raises; never iterated or printed), the gate files, their gates_applied copies and the applied-gate markers
through GateLeaves (decision.* and the three reason lists only); the self-test fails if any fr JSON file is opened
outside the guard. Read with json.load, outside fr/: c1/smoke.json (the restart mapping), the region file and
c2/ledger.json (C2's public ledger: boot ids, campaigns and hours, no energy). The C1 start records are read with the
blinded loader of scripts/46. After a step-0 repeat the attempt-1 files under fr/step0_attempt1/ are never opened or
listed (only the existence of the folder is checked); the repeat is shown from decision leaves only. No source-data
column holds an energy (asserted). The self-test enforces this at run time with an audit hook: an fr JSON file opened
outside s2b/guard.py, a part output (fr/raw/*.out.gz) opened outside force_curve of fig_s2_c2_a2.py, or an attempt-1
path opened or listed, fails the test. Every energy line of the synthetic part outputs and every withheld field of the
synthetic JSON files holds a canary, which the scan of the source data and the SVG finds when it is printed with at
least 3 significant digits; a static audit of this file's build, plot and QA code refuses the guard's private dict,
any other reader and an open() of any file but those named above.

Caption points (D-C2-11 adapted). pw.x ends a relaxation when the change in F between consecutive configurations is
below 1e-5 Ry and every free force component is below forc_conv_thr; panel a draws only the second criterion, and
QE's own flag, not the curve, decides the end rule. k counts configurations (one SCF cycle each, across restarts),
which is what the cap k <= 200 bounds; it is not the BFGS step count. Every point is one deterministic DFT result:
there are no replicates, so no interval is drawn. A value outside an axis is an edge arrow with its value; in panel a
every outside point has an arrow, and the value is printed at the extreme of each excursion and at an end outside the
axis. The node-hour axis of panel c extends to hold the largest bar, so no bar is cut. Status wording follows
D-C2-10; a relaxation pending at a final STOP is 'stopped at k = k_last' or 'stopped before k = 0'. After
fr/STEP0_NO_ERROR the gate file keeps fail_pending_fix and the A2 stop state holds fail_final; the figure shows
'fail (fail_final: no error found)', and gate FR 'fail (step-0 final; gate not evaluated)'. After a final STOP gate FR
is 'not reached (after a final STOP)', drawn as a failure: a final STOP in fr is an FR failure (S2B section 1, route
table). After a final STOP FR's detail names the stop note. A pass of FR-1 that needs the invariant (identical-atom)
reading of check 5 is flagged in FR's detail (S2B section 2). FR's state agrees with fr_outcome in campaign.json
(asserted).

When --build runs. Only after CAMPAIGN_DONE or the final STOP of fr and after verify (operations note sections 2 and
4): the FR-1 re-derivation reads the validity leaves of the fr records (validity_final, both readings of check 5). The
build asserts that the verify record fr_verify/verify_fr.txt exists (operations note D-C2-6); it does not open it.
A STOP of fr is final only through its stop note (the analyst's rulings FIG_DECISIONS_R3 FG-2 and
INTEGRATION_DECISIONS IX-1; E's OP-19 and E_DECISIONS_R2 ER2-11): --stop-note NOTE names a committed, clean, dated
note under results/objective2/s2/ (not under s2b/) that states 'the fr STOP is final'. The build applies E's tests:
e_eval.stop_note_ok (the phrase, an ISO date, the location) and the committed-and-clean test of e_eval.Run.note_ok (a
normalised repository-relative path, tracked and unchanged in the tree, its text read from HEAD); the self-test pins
both against e_eval.py. On a stopped fr every build without a valid stop note refuses. This includes a STOP at a step-0
fail_pending_fix where neither fr/STEP0_FIX nor fr/STEP0_NO_ERROR was applied (D-C2-2, D-C2-3), which is not final
without its note. With a valid stop note the STOP is drawn as final, at such a fail_pending_fix too, and the source data
(fig_s2b_fr_b_stop.csv) records the note's path and the sha256 of its HEAD text, as E prints them. A stop note beside a
done fr is refused, as in the section 6b read.

Integration review 1 (INTEGRATION_DECISIONS IX-4 to IX-6; amendment 2026-11-12a items 12 and 13). The stop note is
the one file results/objective2/s2/FR_STOP_NOTE.md (E's STOP_NOTE), and its HEAD object must be a blob (git cat-file
-t), so that a glob, a pathspec or a directory is never read as a note. A final STOP after a recorded FR outcome is
'FR fails' (S2B section 1): FR's state names the decision gate FR or the step-0 final recorded before the STOP, in E's
header words ('fail (FR-1, <cell>, <E's reason>)', 'fail (FR-2)', 'fail (step-0 final; gate not evaluated)', 'pass at
gate FR'), then 'then a final STOP (<stop reason>)', a pass adding 'counted as FR fails (S2B section 1)', and it is
drawn as a failure; campaign.json must hold the fr_outcome scripts/50 begin_stop records at every STOP (the outcome
the decisions fix, else null), equal to that decision (fr/STEP0_NO_ERROR, which changes only the state, is taken from
it as well as from the log line). On a stopped fr, step0_attempt1/ without a STEP0_FIX entry (the move made, the save
not) is accepted under exactly E's s0_set_aside conjuncts and drawn 'repeat prepared, not recorded'. The self-test
pins both against E's own route code on the same synthetic archives.

Integration review 2. The figure follows E (IX-1, IX-5) on three more points. (1) The repeat of fr_step0@2 prepared
and not recorded (the move made, the STEP0_FIX save not) is accepted on a stopped fr where E accepts it: no
gates/fr_step0.json, neither step-0 gate applied, the @2 attempt-1 marker present by name, V+_R without a record or
pending (set_aside_2); its row reads 'repeat prepared, not recorded', where E prints its B2.step0.repeat row. (2) A
stopped fr whose campaign.json start_commit and commit are both null (a STOP before the node recorded the fr campaign
commit) is refused before the stop note is read, as E's route_admit refuses it (amendment 2026-11-12a item 11); so is
(IX-15) a stopped fr whose gates/FR.json exists without gates_applied/gate_FR.gate.json (gate FR written but not
applied: an N-FR4 or N-FR8 'not applied' Stop of scripts/50 run_gate, resolved by a dated fix and a relaunch, never by
a stop note), tested by name only, as e_eval.gate_fr_unapplied does. (3) IX-16: E_REASON and e_reason are pinned
against E's FR_REASON and fr_reason, compiled from the source of e_eval.py with ast, and the runner's 'FR step-0
repeat prepared' log line, from which the rerun cell is parsed, against the source text of scripts/50
fr_step0_repeat. The self-test runs E's route_admit, rf12_step0, stop_decision and header code on every stopped
synthetic archive, and E's route_admit on the archives the figure refuses before the stop note is read.

Integration review 3 (IX-11 at both cells). The pin of the 'repeat prepared, not recorded' rows takes E's set-aside
rule from E's source with ast (_e_aside_src): the attempt-1 markers E names in Run.route_fr, tested by existence
only, and the list and tests of Run.block2 that print E's step-0 repeat row, in place of a restatement of them.

Decisions taken where the note allows more [I].
- Free atoms: besides the count (64 for host_R, the A1 start record's n_free otherwise; nat - n_fixed), the build
  asserts that the free index set equals the start source's free list.
- Gate states are re-derived from decision.fr_step0 and decision.FR (markers and their gate copies), the A2 stop state
  (state_end.json: fr_step0, fr_stop, FR), gates/, completeness.json, campaign.json (status, fr_outcome,
  commit_history) and the A2 records (scripts/49 fr_eval on their status, end rule and validity leaves). Without
  state_end.json (a final STOP) a STEP0_NO_ERROR is taken from the runner's log line, as D-C2-12 does for C2.
- A step-0 repeat is known from the commit_history entry via fr/STEP0_FIX, which must agree with the presence of
  fr/step0_attempt1/ (IX-5: on a stopped fr the @4 repeat prepared and not recorded is accepted without it, under E's
  s0_set_aside, the @4 attempt-1 marker checked by name only); the rerun cell from decision.fr_step0.attempt1 (else
  the runner's 'repeat prepared' log line), which must be a step-0 cell (V or D+V).
- A complete record has one part output per part (restarts = parts - 1 unless it was rerun from k = 0), and a record
  with a configuration has part outputs; otherwise the build fails rather than draw a legend entry without its line.
- fr node-hours: the fr ledger is compared with c2/ledger.json by boot id. The boot that ended C2 is the C2-ledger row
  marked current (a ledger written off the node marks none: then the last boot of C2 by boot time). Its increase is
  the tail of S2B section 8 (never negative), or, when fr ran on it, the part counted as fr. A change of any other
  boot of the C2 ledger (a re-timed earlier boot) is listed apart, as are manual rows new since C2, boots of neither
  campaign and rows the ledger could not time. The S2B section 8 band is 6-29 node-h when Cs D(A188) never started
  (FR stopped at host_R or after the V+-host pair), else 22-58; with a step-0 repeat a lighter band extends it to 72
  (S2B section 8: 'repeat: up to 72' for the four, and 'on FR failure 6-58 (with a repeat, up to 72)' after an early
  stop), and the cells that ran are named.
- min_per_config is drawn only for a relaxation with a configuration: scripts/50 divides the wall time by
  max(1, n_config), so for n_config = 0 it is the wall time of the failed start, not a rate (kept in the source data).
- Presentation: the cell key sits above panel a and the threshold (0.00078 Ry/bohr = 0.02005 eV/A, from the
  scripts/47 constants) is labelled in the glyph key below it, so that no text lies in the data area; curves are cut
  at the axis limits in code (clip_log), so no path leaves the plot area; arrows are polygon markers, and a value at a
  right-edge arrow sits left of it with a gap fixed in points; a marker at n_config = 0 sits 3 pt right of the
  spine of c1, not on it. Cells are labelled host, V, D and D+V, as in D-C2-12.
  Panel b's height follows from its wrapped text, wrapped so that no line of a text that wraps holds a single word
  (FG-4); the figure is 183 mm wide.

Layout QA: the panel-alignment gate (all panels; and the panel labels of the a-b column, require_panel_labels: the
three strips of c share one label), the PDF text audit (>= 5 pt) and the rendered collision audit come from the
external nature-figure toolkit (~/.claude/skills/nature-figure/scripts), with the tolerances (ALIGN_KW: 1.5 pt,
strict) and the 5 pt floor as module constants. The collision report holds the PDF's file name only, so that no local
path enters the public repository. The self-test requires all three, shows each failing on a bad figure (a 4 pt
text, two overlapping texts, c3 moved 5 pt off its row), checks every output text file against the hygiene rules of
scripts/46, and checks the drawn marks against the source data: threshold, k = 200, curves and their axis crossings,
glyphs, restart ticks, edge arrows (edge, direction, values), key colours and line styles, the gate rows in order (no
line of a wrapped text with a single word), and in panel c each marker, text, bar, band and title on the row of its
label. The stop notes are tested on a synthetic git repository. The self-test writes nothing into figures/: it compares
the paths there that this script can write (its figure files, its source data, --keep copies and bytecode) before and
after, and not the other figures' files, which another script or person may change meanwhile.

    python fig_s2b_fr.py --build [--stop-note NOTE]   # (re)extract source data from the fr archive, with the build
                                                      # asserts; NOTE: the stop note of a final STOP of fr
    python fig_s2b_fr.py               # plot from source_data/fig_s2b_fr_*.csv
    python fig_s2b_fr.py --self-test   # synthetic archives made from the public WP2e output; no fr file is read
"""
import argparse, ast, copy, csv, gzip, hashlib, importlib.util, json, math, os, re, shutil, subprocess, sys, tempfile
import textwrap

sys.dont_write_bytecode = True        # the modules loaded below write no __pycache__ into the repository or the toolkit
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
S2 = os.path.normpath(os.path.join(HERE, ".."))                          # results/objective2/s2, the archive root
SCRIPTS = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", "scripts"))
SRC = os.path.join(HERE, "source_data")
OUT = os.path.join(HERE, "fig_s2b_fr")
QA_DIR = os.path.expanduser("~/.claude/skills/nature-figure/scripts")

FR_LABELS = ("s2r_m30_hostA188", "s2r_m30_VA188", "s2r_m30_Cs188o0_novac", "s2r_m30_Cs188o0_vac")   # S2B section 2
FR_ROLES = ("host", "V", "D", "DV")
GATES = (("fr_step0@2", "gate:fr_step0@2"), ("fr_step0@4", "gate:fr_step0@4"), ("FR", "gate:FR"))   # graph order
STEP0_AT = {"fr_step0@2": ("s2_m30_VA188", "s2r_m30_VA188"),
            "fr_step0@4": ("s2_m30_Cs188o0_vac", "s2r_m30_Cs188o0_vac")}                       # (C1 SP, FR cell)
STEP0_CELLS = tuple(c for _, c in STEP0_AT.values())                     # the cells a step-0 repeat can rerun
VERIFY = ("fr_verify", "verify_fr.txt")                                  # operations note D-C2-6 (existence only)
S2_REL = "results/objective2/s2"                                         # the archive root in the repository
REPO = os.path.normpath(os.path.join(S2, "..", "..", ".."))             # the repository (git -C REPO), as e_eval.py
# the stop note of a final STOP of fr (FG-2, IX-1): E's rule (e_eval.py, OP-19), pinned against it in the self-test
STOP_PHRASE = re.compile(r"the fr STOP is final", re.I)
ISO_DATE = re.compile(r"\b(20\d\d)-(\d\d)-(\d\d)\b")
STOP_NOTE = f"{S2_REL}/FR_STOP_NOTE.md"          # IX-6 (amendment item 12): the one stop note; E's STOP_NOTE (pinned)
# E's reason words for the first FR-1 failure (e_eval.FR_REASON, fr_reason), named after a final STOP (IX-4; pinned)
E_REASON = {"missing": "missing", "not_started_cap": "hard-cap refusal", "killed_by_gate": "killed by a gate",
            "not_run_gate": "not run (gate)", "check_not_evaluated": "no final-geometry check"}
REGION, HOST_N_FREE = "m30_A188", 64                                     # c1/regions/m30_A188.json (S2B section 2)
TERMINAL = ("complete", "missing", "killed_by_gate", "not_run_gate", "not_started_cap")
NOT_STARTED = ("not_run_gate", "not_started_cap", "no record")
JOB_STATUS = {"complete": "done", "missing": "missing", "killed_by_gate": "killed_by_gate", "not_run_gate": "not_run",
              "not_started_cap": "not_started_cap"}                     # scripts/50 a2_status
# scripts/50 constants (checked against its source text in modules(); scripts/50 is not executed)
FR_DECISION_KEYS = ("outcome", "FR1", "FR2", "part", "cell", "kind")
FR_STEP0_KEYS = ("attempts", "outcome", "repeat", "fix_note", "cell", "attempt1", "no_error_found", "note")
FR_OUTCOMES = ("pass", "fail (FR-1)", "fail (FR-2)", "fail (step-0 final; gate not evaluated)")
GATE_LEAVES = ("result.checks_failed", "result.end_rule_failed", "result.cells_not_run")
CAP_CONFIGS, RATE_BAND, CAP_H = 201, (4.19, 4.65), 520.0                 # operations note section 4, Cost
PLAN_FR_H, PLAN_FR_EARLY_H, PLAN_FR_REPEAT_H = (22, 58), (6, 29), 72     # S2B_PLAN.md section 8
# the runner's two STEP0_NO_ERROR log lines (scripts/50; pinned against its source text in pins())
NOERR_LOG = ("fr/STEP0_NO_ERROR: FR step-0 fail_final (no error found)", "FR step-0 fail_final since an earlier start")
# the head of the runner's 'repeat prepared' log line (scripts/50 fr_step0_repeat): its first literal, the name of the
# value that follows (the cell) and the literal after it; fr_gates parses the rerun cell from it (pinned in pins())
REPEAT_LOG = ("FR step-0 repeat prepared: ", "cell", ": ")
# layout QA of the nature-figure toolkit, used by plot() and qa() alike (QA contract: 1.5 pt, strict; 5 pt glyphs)
ALIGN_KW = {"tolerance_pt": 1.5, "gutter_tolerance_pt": 1.5, "strict": True}
MIN_TEXT_PT = 5.0
COLUMNS = {    # every source-data column; none holds an energy (asserted by energy_column)
    "fig_s2b_fr_a_force.csv": ["order", "label", "k", "part", "fmax_free_Ry_bohr", "fmax_free_eV_A"],
    "fig_s2b_fr_a_relaxations.csv": ["order", "label", "role", "status", "line", "outcome", "end", "n_config",
                                     "k_last", "converged_at_k", "restarts", "reruns_from_zero", "interruptions",
                                     "ranks", "wall_h", "min_per_config", "n_free", "n_fixed", "part_starts",
                                     "step0_rerun", "status_text"],
    "fig_s2b_fr_b_gates.csv": ["gate", "state", "detail", "attempt", "cell", "kind", "stops_fr"],
    "fig_s2b_fr_b_stop.csv": ["key", "value"],
    "fig_s2b_fr_c_cost.csv": ["key", "value"],
    "fig_s2b_fr_constants.csv": ["key", "value"]}
ENERGY_TOKENS = {"F", "dF", "E", "dE", "Eb", "delta", "energy", "plateau", "K3", "SP"}
ENERGY_UNITS = {"eV", "meV", "Ry", "Ha", "kJ", "kcal"}

# every named build assert, one key per need() site (checked in the self-test, which shows each site failing on a
# broken archive or a code mutant)
KEYS = ("pins: scripts/49", "pins: scripts/47", "pins: scripts/50", "pins: guard",
        "campaign", "campaign: no campaign commit", "gates/: FR not applied", "stop note: none", "stop note: fr done",
        "stop note: path", "stop note: fixed path", "stop note: git",
        "stop note: committed and clean", "stop note: HEAD", "stop note: text", "state_end", "verify",
        "record", "A1 start", "rank count", "did not start", "part files: none", "part files: count",
        "part files: names", "host region", "free-atom count: host region", "free-atom set: host region",
        "MACE energy", "free-atom count: start record", "free-atom set: start record", "fixed-atom count",
        "k values differ from n_config", "without configurations", "converged_at_k", "converged above forc_conv_thr",
        "cap", "k_last", "pending k",
        "marker: no gate copy", "marker: decisions differ",
        "repeat: STEP0_FIX and step0_attempt1", "repeat: rerun cell", "repeat: attempt-1 leaves",
        "step-0 order", "step-0 cell", "step-0 outcome", "attempt: count", "attempt: attempt-1 leaves",
        "step-0 state: repeat_pending", "step-0 state: no applied gate", "step-0 state: STEP0_NO_ERROR",
        "step-0 state: differs",
        "FR after a failed step-0", "FR decision: keys", "FR-1: gate code refused", "FR-1 differs from the A2 records",
        "reason lists", "FR decision: combination", "FR-2", "fr_stop", "FR state", "FR not applied", "fr_outcome",
        "gates/: FR.json", "gates/: fr_step0.json", "completeness: file", "completeness: gate jobs",
        "completeness: relaxation jobs",
        "ledger: C2 end boot", "ledger: duplicate boot", "ledger split: not the C2 end boot",
        "ledger split: fewer hours", "ledger: C2 boot tail negative",
        "READS: before the build", "energy column: header", "READS: after the build", "columns",
        "energy column: key/value")
_MODS = {}


def need(ok, key, *detail):
    """A named build assert (KEYS)."""
    if key not in KEYS:
        raise ValueError(f"unknown build-assert key {key!r}")
    if not ok:
        raise AssertionError(f"[{key}] " + "; ".join(str(x) for x in detail))


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


_TREE50 = []


def _tree_50():
    """scripts/50 parsed once (its source text; scripts/50 is not run)."""
    if not _TREE50:
        _TREE50.append(ast.parse(open(os.path.join(SCRIPTS, "50_s2_campaign.py")).read()))
    return _TREE50[0]


def _constants_50():
    """The fr constants of scripts/50, read from its source text with ast.literal_eval, and the string constants of
    its code (where the runner's log lines are)."""
    tree = _tree_50()
    want = ("FR_ORDER", "FR_STEP0_AT", "FR_DECISION_KEYS", "FR_STEP0_KEYS", "FR_OUTCOMES")
    out = {t.id: ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
           for t in n.targets if isinstance(t, ast.Name) and t.id in want}
    strings = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    out["NOERR_LOG"] = tuple(s for s in NOERR_LOG if any(s in x for x in strings))   # the lines scripts/50 logs
    out["REPEAT_LOG"] = _repeat_log_50(tree)
    return out


def _repeat_log_50(tree):
    """Integration review 2: the head of each 'FR step-0 repeat prepared' line that scripts/50 fr_step0_repeat logs
    (the f-string of its self.log call): (its first literal, the name of the formatted value after it, the first
    len(REPEAT_LOG[2]) characters of the literal after that). fr_gates takes the rerun cell from that line."""
    heads = []
    for fn in ast.walk(tree):
        if not (isinstance(fn, ast.FunctionDef) and fn.name == "fr_step0_repeat"):
            continue
        for c in ast.walk(fn):
            if not (isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "log" and c.args
                    and isinstance(c.args[0], ast.JoinedStr)):
                continue
            v = c.args[0].values
            if not (v and isinstance(v[0], ast.Constant) and str(v[0].value).startswith(REPEAT_LOG[0].split(":")[0])):
                continue
            x = v[1].value if len(v) > 1 and isinstance(v[1], ast.FormattedValue) else None
            heads.append((v[0].value, x.id if isinstance(x, ast.Name) else None,
                          v[2].value[:len(REPEAT_LOG[2])] if len(v) > 2 and isinstance(v[2], ast.Constant) else None))
    return tuple(heads)


def modules():
    """scripts/49 (and the scripts/46, 47 objects it loads, so that READS is the reader's counter), the S2b guard
    (s2b/guard.py) and, through it, the unchanged D-C2-12 figure module whose force-only reader is used."""
    if not _MODS:
        sys.path.insert(0, SCRIPTS)
        g = _load("g49_fig_s2b_fr", os.path.join(SCRIPTS, "49_s2_gates.py"))
        gd = _load("s2b_guard_fig_s2b_fr", os.path.join(S2, "s2b", "guard.py"))
        _MODS.update(g49=g, q47=g.dep("q47"), c46=g.dep("c46"), guard=gd, c2fig=gd.fig)
        pins(_MODS)
    return _MODS


def pins(M):
    """The constants this figure relies on equal those of scripts/47, 49, 50 and the guard (checked at load and at
    every build)."""
    g, q, gd = M["g49"], M["q47"], M["guard"]
    need(g.FR_ORDER == FR_LABELS and tuple(g.FR_QUARTET[r] for r in FR_ROLES) == FR_LABELS and
         dict(g.FR_STEP0_PAIRS) == dict(STEP0_AT.values()) and g.RULES["FR2_MAX_MEV"] == 50.0 and
         g.RULES["HARD_CAP_H"] == CAP_H, "pins: scripts/49", "the FR constants or rules of scripts/49 differ")
    need((q.FORC_CONV_THR, q.K_CAP) == (7.8e-4, 200) and abs(q.FORC_CONV_THR * q.RY_EV / q.BOHR_A - 0.02005) < 5e-6,
         "pins: scripts/47", "forc_conv_thr, K_CAP or the unit constants of scripts/47 differ")
    need(_constants_50() == {"FR_ORDER": FR_LABELS, "FR_STEP0_AT": {gid: STEP0_AT[n][1] for n, gid in GATES[:2]},
                             "FR_DECISION_KEYS": FR_DECISION_KEYS, "FR_STEP0_KEYS": FR_STEP0_KEYS,
                             "FR_OUTCOMES": FR_OUTCOMES, "NOERR_LOG": NOERR_LOG, "REPEAT_LOG": (REPEAT_LOG,)},
         "pins: scripts/50", "the fr constants, the STEP0_NO_ERROR log lines or the 'repeat prepared' log line differ "
                             "from scripts/50")
    need(tuple(gd.GATE_LEAVES) == GATE_LEAVES and set(g.FR_ENERGY_FIELDS) <= gd.WITHHELD_S2B, "pins: guard",
         "the allow-list or the withheld fields of the guard differ")


def energy_column(name):
    """True for a column or key name that would hold an energy (fr energy fields, F/E/Eb/delta/value tokens, or an
    energy unit as the last token; forces end in _bohr or _A)."""
    t = str(name).split("_")
    return name in modules()["guard"].WITHHELD_S2B or bool(ENERGY_TOKENS & set(t)) or t[-1] in ENERGY_UNITS


# ---------------------------------------------------------------- relaxations (panel a, D-C2-11 a)
STATUS = {"missing": "missing", "killed_by_gate": "killed by a gate", "not_run_gate": "not run (gate)",
          "not_started_cap": "not started (cap)", "no record": "not started (no record)", "complete": "complete"}


def status_text(row):
    """The D-C2-10 wording of a relaxation's status (a record pending at a final STOP is 'stopped at k = k_last')."""
    st = row["status"]
    if st == "complete":
        return "complete" if row["outcome"] != "unconverged_early" else \
            f"early end, {row['end']}" + ("" if row["k_last"] != "" else ", no configuration")
    if st in STATUS:
        return STATUS[st]
    return f"stopped at k = {row['k_last']}" if row["k_last"] != "" else "stopped before k = 0"


def free_source(arch, M, lab, free):
    """The free atoms of the start source the runner used (scripts/50 a2_launch): c1/regions/m30_A188.json for
    host_R (64, S2B section 2), else the A1 start record, read with the blinded loader of scripts/46."""
    g49, c46 = M["g49"], M["c46"]
    if g49.a2_cell(lab)["kind"] == "host":
        reg = json.load(open(os.path.join(arch, "c1", "regions", f"{REGION}.json")))
        need(int(reg["n_free"]) == HOST_N_FREE == len(reg["free"]), "host region", lab, reg["n_free"])
        need(len(free) == HOST_N_FREE, "free-atom count: host region", lab, len(free), HOST_N_FREE)
        need(free == sorted(int(i) for i in reg["free"]), "free-atom set: host region", lab)
        return None
    rec = c46.load_record(os.path.join(arch, "c1", "records", f"{g49.a1_start_of(lab)}.json"))
    need("E_mace_eV" not in json.dumps(rec), "MACE energy", lab, "the blinded loader left a MACE energy")
    need(len(free) == int(rec["n_free"]) == len(rec["free"]), "free-atom count: start record", lab, len(free),
         rec["n_free"])
    need(free == sorted(int(i) for i in rec["free"]), "free-atom set: start record", lab)
    return int(rec["n_fixed"])


def relaxations(arch, M, rerun):
    g49, q47, c46, gd, c2 = M["g49"], M["q47"], M["c46"], M["guard"], M["c2fig"]
    fr = os.path.join(arch, "fr")
    lay = c46.Layout(kind="archive", root=arch)
    mapping = json.load(open(os.path.join(arch, "c1", "smoke.json")))["mapping"]
    hc = gd.guarded_s2b(os.path.join(fr, "HARD_CAP.json"))                # the runner's hard-cap refusal, if any
    capped = hc.get("job") if hc is not None else None
    rows, pts, recs, cap_seen = [], [], {}, False
    for order, lab in enumerate(FR_LABELS, 1):
        rec = gd.guarded_s2b(os.path.join(fr, "raw", f"{lab}.a2.json"))
        recs[lab] = rec
        st = rec.get("status") if rec is not None else "no record"
        cap_seen = cap_seen or st == "not_started_cap" or capped == f"a2:{lab}"
        if rec is None and cap_seen:
            st = "not_started_cap"                    # later jobs refused by the cap get no record (scripts/50)
        row = {k: "" for k in COLUMNS["fig_s2b_fr_a_relaxations.csv"]}
        row.update(order=order, label=lab, role=FR_ROLES[order - 1], status=st, line="none",
                   step0_rerun=lab == rerun)
        outs = lay.a2_parts("fr", lab)
        ranks = None
        if rec is not None:
            need(rec.get("label") == lab and rec.get("campaign") == "fr", "record", lab, "label or campaign")
            a1 = rec.get("a1_cell")
            need(a1 is not None and a1.get("work_id") == g49.a1_start_of(lab), "A1 start", lab)
            ranks = rec.get("layout").get("ranks") if rec.get("layout") is not None else None
            need(ranks in (None, 64), "rank count", lab, ranks)              # the C1 throughput layout
            row.update(restarts=rec.get("restarts"), reruns_from_zero=rec.get("reruns_from_zero"),
                       interruptions=len(rec.get("interruptions") or []), ranks="" if ranks is None else ranks)
        need(st not in NOT_STARTED or not outs, "did not start", lab, st, len(outs))
        live = rec is not None and (st == "complete" or st not in TERMINAL)     # complete, or pending at a final STOP
        # a record with a configuration has part outputs (else the legend would show it without its line)
        need(outs or not live or (int(rec.get("n_config") or 0) < 1 and not rec.get("k0_seen")), "part files: none",
             lab, st, "a record with a configuration has no part outputs")
        er = rec.get("end_rule") if rec is not None else None
        if st == "complete":
            parts, rs, rz = rec.get("parts") or [], rec.get("restarts"), rec.get("reruns_from_zero")
            need(len(outs) == len(parts) and isinstance(rs, int) and isinstance(rz, int) and rs >= len(outs) - 1 and
                 (rz > 0 or rs == len(outs) - 1), "part files: count", lab,
                 f"{len(outs)} part outputs, {len(parts)} parts, restarts {rs}, reruns from k = 0 {rz}")
            row.update(outcome=er.get("outcome"), end=er.get("end") or "", n_config=int(rec.get("n_config")),
                       k_last=rec.get("k_last") if rec.get("k_last") is not None else "",
                       converged_at_k=rec.get("converged_at_k") if rec.get("converged_at_k") is not None else "",
                       wall_h=repr(float(rec.get("wall_h"))), min_per_config=repr(float(rec.get("min_per_config"))))
        if not live or not outs:
            row["status_text"] = status_text(row)
            rows.append(row); continue
        names = [os.path.basename(p) for p in outs]
        need(names == [f"{lab}.p{n}.out.gz" for n in range(1, len(outs) + 1)], "part files: names", lab, names)
        nat, free = c2.free_atoms(q47, [os.path.join(fr, "raw", f"{lab}.p{n}.in.gz") for n in range(1, len(outs) + 1)])
        nfix = free_source(arch, M, lab, free)
        need(nfix is None or nat - len(free) == nfix, "fixed-atom count", lab, nat, nfix)
        rel, cur, starts = c2.force_curve(q47, lab, outs, mapping, ranks, nat, free)
        ks = [k for k, _, _ in cur]
        if st == "complete":
            need(ks == list(range(int(rec.get("n_config")))), "k values differ from n_config", lab)
            oc = er.get("outcome")
            need(ks or oc == "unconverged_early", "without configurations", lab, oc)
            if oc == "accepted_converged":
                need(rec.get("converged_at_k") == rel["converged_at_k"] == ks[-1], "converged_at_k", lab)
                need(cur[-1][1] <= q47.FORC_CONV_THR, "converged above forc_conv_thr", lab, cur[-1][1])
            elif oc in ("accepted_plateau", "unconverged_cap"):
                need(ks[-1] == q47.K_CAP, "cap", lab, ks[-1])
            elif oc == "unconverged_early":
                need((ks[-1] if ks else None) == rec.get("k_last") and not rel["qe_converged"], "k_last", lab)
            row["line"] = "complete"
        else:                                         # pending at a final STOP: its n_config lags until a part ends
            n = int(rec.get("n_config") or 0)
            need(ks[:n] == list(range(n)), "pending k", lab, n, len(ks))
            row.update(line="stopped" if ks else "none", k_last=ks[-1] if ks else "")
        row.update(n_free=len(free), n_fixed=nat - len(free), part_starts=" ".join(map(str, starts)))
        row["status_text"] = status_text(row)
        rows.append(row)
        pts += [{"order": order, "label": lab, "k": k, "part": p, "fmax_free_Ry_bohr": repr(f),
                 "fmax_free_eV_A": repr(f * q47.RY_EV / q47.BOHR_A)} for k, f, p in cur]
    return rows, pts, recs


# ---------------------------------------------------------------- gates (panel b)
ROLE = {"host": "host", "V": "V", "D": "D", "DV": "D+V"}       # region cells host_R, V+_R, D, D+V+ (S2B section 2)
KIND = {"end_rule": "end rule", "check": "check", "check_not_evaluated": "check not evaluated", "missing": "missing",
        "not_started_cap": "not started (cap)", "killed_by_gate": "killed by a gate", "not_run_gate": "not run (gate)"}


def role(lab):
    return ROLE[FR_ROLES[FR_LABELS.index(lab)]] if lab in FR_LABELS else str(lab)


def short(text):
    """A reason-list entry with each FR label replaced by its cell name (host, V, D, D+V); scripts/49's 'end rule None'
    (a relaxation without an end rule) is shown as 'no end rule'."""
    for lab in FR_LABELS:
        text = re.sub(re.escape(lab) + r"(?![A-Za-z0-9_])", role(lab), text)
    return text.replace("end rule None", "no end rule")


def applied(gd, gdir, gid, key):
    """The applied-gate marker and the gate copy the runner kept beside it (scripts/50 run_gate), read through
    GateLeaves (decision.* and the reason lists only), or None."""
    m = os.path.join(gdir, re.sub(r"[^A-Za-z0-9_.-]", "_", gid) + ".json")
    if not os.path.exists(m):
        return None
    mk, g = gd.gate_leaves(m), gd.gate_leaves(m[:-5] + ".gate.json")
    need(g is not None, "marker: no gate copy", gid, "no gate copy beside the marker")
    d1, d2 = mk.get(f"decision.{key}"), g.get(f"decision.{key}")
    need(isinstance(d1, dict) and d1 == d2, "marker: decisions differ", gid,
         "the marker and its gate copy hold different decisions")
    return {"gate": g, "dec": d1, "path": m}


def _log_lines(fr):
    if not os.path.exists(os.path.join(fr, "logs", "campaign.log")):
        return []
    return open(os.path.join(fr, "logs", "campaign.log")).read().splitlines()


def fr_gates(arch, M, recs, camp, st, sn=None):
    """Each fr gate in the state of the D-C2-10 file mapping, re-derived from decision leaves, the A2 stop state,
    gates_applied/ markers, campaign.json and the A2 records (operations note section 4). sn: the stop note of a final
    STOP (stop_note(); a2_stop_state requires it when fr is stopped), named in FR's detail."""
    g49, gd = M["g49"], M["guard"]
    fr = os.path.join(arch, "fr")
    gdir = os.path.join(fr, "gates_applied")
    done = camp.get("status") == "done"
    fixes = [h for h in (camp.get("commit_history") or []) if h.get("via") == "fr/STEP0_FIX"]
    prepared = bool(fixes)
    a1dir = os.path.isdir(os.path.join(fr, "step0_attempt1"))          # its existence only; never opened
    # IX-5: scripts/50 fr_step0_repeat moves the attempt-1 files before the save that records STEP0_FIX, so a STOP
    # between the two leaves step0_attempt1/ without the entry; on a stopped fr this is accepted under exactly the
    # conjuncts of E's s0_set_aside at @4 (e_eval.Run.rf12_step0), and at @2 where E accepts it with no step-0
    # evaluation in force (integration review 2; both pinned on the same archives)
    unrec_at = None if prepared or not a1dir or done else "fr_step0@4" if set_aside_4(fr, gdir, recs) else \
        "fr_step0@2" if set_aside_2(fr, gdir, recs) else None
    unrec = unrec_at is not None
    need(len(fixes) <= 1 and a1dir == (prepared or unrec), "repeat: STEP0_FIX and step0_attempt1",
         f"STEP0_FIX entries {len(fixes)}", f"step0_attempt1 present {a1dir}")
    log = _log_lines(fr)
    sdec = st.get("fr_step0").open() if st is not None and st.get("fr_step0") is not None else None
    ents = {name: applied(gd, gdir, gid, "fr_step0") for name, gid in GATES[:2]}
    a1s = [e["dec"]["attempt1"] for e in ents.values() if e is not None and e["dec"].get("attempt1")] + \
        ([sdec["attempt1"]] if sdec and sdec.get("attempt1") else [])
    rerun = a1s[0].get("cell") if a1s else None
    if prepared and rerun is None:                    # the repeat was prepared, no attempt-2 decision exists yet
        ln = [x for x in log if REPEAT_LOG[0] in x]
        rerun = ln[-1].split(REPEAT_LOG[0], 1)[1].split(REPEAT_LOG[2], 1)[0] if ln else None
    need(rerun is None or rerun in STEP0_CELLS, "repeat: rerun cell", f"{rerun!r} is not a step-0 cell")
    need(all(a == a1s[0] for a in a1s) and (rerun is None or prepared), "repeat: attempt-1 leaves",
         "attempt-1 leaves disagree, or a rerun cell without STEP0_FIX")
    out, stopped_by, last = [], None, None
    for name, gid in GATES[:2]:
        sp, cell = STEP0_AT[name]
        e = ents[name]
        if e is None:
            r = recs.get(cell)
            state = "not reached"
            if stopped_by is None and r is not None and r.get("status") in ("complete", "missing", "killed_by_gate") \
                    and not r.get("k0_seen") and int(r.get("n_config") or 0) < 1:
                state = "skipped (no k = 0)"
            detail = (f"attempt 2 after STEP0_FIX not evaluated (attempt 1 at {role(rerun)}: fail_pending_fix; its "
                      f"files are not opened)") if rerun == cell else ""
            if unrec_at == name:                        # IX-5: as E prints it (B2.step0.repeat)
                detail = (f"repeat prepared, not recorded (attempt 1 at {role(cell)}: fail_pending_fix; its files set "
                          f"aside unread; no STEP0_FIX entry)")
            out.append({"gate": name, "state": state, "detail": detail, "attempt": "", "cell": cell, "kind": "",
                        "stops_fr": False})
            continue
        d = e["dec"]
        need(stopped_by is None, "step-0 order", name, f"applied after the failed {stopped_by}")
        need(d.get("cell") == cell and set(d) <= set(FR_STEP0_KEYS), "step-0 cell", name, d.get("cell"))
        oc, att = d.get("outcome"), d.get("attempts")
        need(oc in ("pass", "fail_pending_fix", "fail_final"), "step-0 outcome", name, oc)
        want = 2 if prepared and rerun is not None and FR_LABELS.index(cell) >= FR_LABELS.index(rerun) else 1
        need(att == want and d.get("repeat") is (att == 2) and (oc != "fail_final" or att == 2), "attempt: count", name,
             f"attempts {att}, expected {want}; repeat {d.get('repeat')}; outcome {oc}")
        a1 = d.get("attempt1") or {}
        need(att == 1 or (a1.get("attempts") == 1 and a1.get("outcome") == "fail_pending_fix" and a1.get("cell") ==
                          rerun), "attempt: attempt-1 leaves", name, "attempt-1 leaves")
        state = {"pass": "pass", "fail_pending_fix": "fail (fail_pending_fix)", "fail_final": "fail (fail_final)"}[oc]
        detail = f"attempt {att}" + (f", after STEP0_FIX (attempt 1 at {role(rerun)}: {a1['outcome']}; its files "
                                     f"are not opened)" if att == 2 else "")
        if oc != "pass" and stopped_by is None:
            stopped_by = name
        last = (len(out), name, d)
        out.append({"gate": name, "state": state, "detail": detail, "attempt": att, "cell": cell, "kind": "",
                    "stops_fr": oc != "pass"})
    # the step-0 outcome in force: the A2 stop state (done), else the runner's STEP0_NO_ERROR log line
    no_err = False
    if st is not None:
        if sdec is not None and sdec.get("outcome") == "repeat_pending":
            need(prepared and sdec.get("cell") == rerun and (last is None or FR_LABELS.index(last[2]["cell"]) <
                                                              FR_LABELS.index(rerun)), "step-0 state: repeat_pending",
                 "repeat_pending without its STEP0_FIX, at another cell, or after a later applied step-0 gate")
        elif last is None:
            need(sdec is None, "step-0 state: no applied gate", "a step-0 state without an applied step-0 gate")
        else:
            d = last[2]
            if d["outcome"] == "fail_pending_fix" and (sdec or {}).get("outcome") == "fail_final":
                rest = {k: v for k, v in sdec.items() if k not in ("outcome", "no_error_found", "note")}
                need(sdec.get("no_error_found") is True and d["attempts"] == 1 and
                     rest == {k: v for k, v in d.items() if k != "outcome"}, "step-0 state: STEP0_NO_ERROR",
                     "the fail_final state does not follow the last decision by STEP0_NO_ERROR")
                no_err = True
            else:
                need(sdec == d, "step-0 state: differs", "the state differs from the last applied step-0 decision")
    elif last is not None and last[2]["outcome"] == "fail_pending_fix":
        # the runner's log line, or the fr_outcome scripts/50 begin_stop records at a STOP (IX-4: E reads that leaf;
        # the two must agree, checked with fr_outcome below)
        no_err = any(any(s in x for s in NOERR_LOG) for x in log) or (
            camp.get("fr_outcome") == FR_OUTCOMES[3] and last[2]["attempts"] == 1)
        # D-C2-2, D-C2-3: a step-0 STOP is resolved by fr/STEP0_FIX or fr/STEP0_NO_ERROR (dated analyst decisions);
        # after STEP0_FIX the failed attempt-1 marker is under step0_attempt1/, so a fail_pending_fix still in force
        # means that no route was taken. Such a STOP is final only through its stop note (FG-2, IX-1), which
        # a2_stop_state has required; it is drawn as final, and the step-0 row says that no route was taken
        if not no_err:
            out[last[0]]["detail"] += "; neither fr/STEP0_FIX nor fr/STEP0_NO_ERROR before the final STOP"
    if no_err:
        i = last[0]
        out[i].update(state="fail (fail_final: no error found)",
                      detail=out[i]["detail"] + "; STEP0_NO_ERROR: step-0 final (S2B section 2)")
    s0_final = no_err or any(r["state"] == "fail (fail_final)" for r in out)
    # gate FR
    e = applied(gd, gdir, "gate:FR", "FR")
    row = {"gate": "FR", "state": "", "detail": "", "attempt": "", "cell": "", "kind": "", "stops_fr": True}
    if e is not None:
        d = e["dec"]
        need(not s0_final and stopped_by is None, "FR after a failed step-0", "gate FR applied after a failed step-0")
        need(sorted(d) == sorted(FR_DECISION_KEYS), "FR decision: keys", sorted(d))
        t = {}
        for lab in FR_LABELS:
            r = recs.get(lab)
            vf = r.get("validity_final") if r is not None else None
            t[lab] = {"status": r.get("status") if r is not None else None,
                      "end_rule": (r.get("end_rule").get("outcome") if r is not None and r.get("end_rule") is not None
                                   else None), "validity_final": vf.open() if vf is not None else None,
                      "a1_valid": True}                   # a1_invalid_reported is not read (not on the allow-list)
        try:
            res, refused = g49.fr_eval(t), None
        except g49.GateRefused as x:
            res, refused = None, short(str(x))
        need(res is not None, "FR-1: gate code refused", refused)
        ff = res["first_failure"] or {}
        need(d["FR1"] is res["FR1"] and (d["cell"], d["kind"]) == (ff.get("cell"), ff.get("kind")),
             "FR-1 differs from the A2 records", f"decision {d['cell']}, {d['kind']}; records {ff}")
        need([e["gate"].get(p) for p in GATE_LEAVES] == [res["checks_failed"], res["end_rule_failed"],
                                                          res["cells_not_run"]], "reason lists", "gate FR")
        combo = (d["outcome"], d["part"], d["FR2"])
        need(combo in ((("pass", None, True), ("fail", "FR-2", False)) if d["FR1"] else (("fail", "FR-1", None),)),
             "FR decision: combination", combo)
        if d["FR2"] is not None:                   # FR-2 needs the fr_step0 pass at D+V+ (scripts/49)
            e4 = ents["fr_step0@4"]
            need(e4 is not None and e4["dec"]["outcome"] == "pass" and (sdec is None or (sdec.get("outcome"), sdec.get(
                "cell")) == ("pass", FR_LABELS[3])), "FR-2", "FR-2 evaluated without the step-0 pass at D+V")
        if st is not None:
            fs = st.get("fr_stop").open() if st.get("fr_stop") is not None else None
            need((d["FR1"] is True and not fs) or
                 (bool(fs) and (fs.get("at"), fs.get("kind")) == (d["cell"], d["kind"])), "fr_stop",
                 f"fr_stop {None if not fs else (fs.get('at'), fs.get('kind'))}")
            need(st.get("FR") is not None and st.get("FR").open() == d, "FR state", "state FR differs from gate FR")
        # S2B section 2: a pass of check 5 that needs the invariant (identical-atom) reading is flagged; the cells are
        # those of the re-derivation from the records' validity_final leaves (invariant_only)
        inv = [role(x) for x in res["invariant_only"]]
        flag = [f"check 5 passed only under the identical-atom reading at {', '.join(inv)}"] if inv else []
        if combo[0] == "pass":
            row.update(state="pass", detail="; ".join(["FR-1 and FR-2 passed (|δ_far| ≤ 50 meV)"] + flag))
            fo = FR_OUTCOMES[0]
        elif combo[1] == "FR-2":
            row.update(state="fail (FR-2)", detail="; ".join(["FR-1 passed; FR-2 failed (|δ_far| > 50 meV)"] + flag))
            fo = FR_OUTCOMES[2]
        else:
            why = [short(x) for x in res["checks_failed"] + res["end_rule_failed"]]
            nr = [role(x) for x in res["cells_not_run"]]
            row.update(state=f"fail (FR-1): {role(d['cell'])}, {KIND.get(d['kind'], d['kind'])}", cell=d["cell"],
                       kind=d["kind"], detail="; ".join(why + ([f"not run: {', '.join(nr)}"] if nr else []) + flag))
            fo = FR_OUTCOMES[1]
    elif s0_final:
        row.update(state="fail (step-0 final; gate not evaluated)", detail="FR is not evaluated after a final step-0 "
                                                                            "failure (S2B section 2)")
        fo = FR_OUTCOMES[3]
    else:
        need(not done, "FR not applied", "fr is done, gate FR has no applied-gate file and step-0 is not final")
        row.update(state="not reached (after a final STOP)",
                   detail="a final STOP in fr: FR fails (S2B section 1, route table)")
        fo = None
    if sn is not None:                                # the note that makes the STOP final (FG-2, IX-1)
        row["detail"] += f"; the STOP is final by the stop note {sn['path']}"
        if fo is not None:                            # IX-4: the decision recorded before the STOP, then the STOP
            why = str(camp.get("stop_reason"))
            dec = {FR_OUTCOMES[0]: "pass at gate FR", FR_OUTCOMES[2]: FR_OUTCOMES[2], FR_OUTCOMES[3]: FR_OUTCOMES[3]}
            part = dec.get(fo) or f"fail (FR-1, {role(row['cell'])}, {e_reason(row['kind'], recs.get(row['cell']))})"
            row["state"] = f"{part}; then a final STOP ({why})" + ("; counted as FR fails (S2B section 1)" if fo ==
                                                                   FR_OUTCOMES[0] else "")
    out.append(row)
    # at CAMPAIGN_DONE the outcome of the decisions; at a STOP the one scripts/50 begin_stop records (IX-4: the
    # outcome the decisions fix, else null; recorded at every STOP)
    need((camp.get("fr_outcome") == fo) and (done or camp.has("fr_outcome")), "fr_outcome",
         f"campaign.json {camp.get('fr_outcome')!r}, decisions {fo!r}")
    if done:                                          # the latest gate outputs and the completeness record
        gf, g0 = gd.gate_leaves(os.path.join(fr, "gates", "FR.json")), gd.gate_leaves(os.path.join(fr, "gates",
                                                                                                    "fr_step0.json"))
        need((gf is None) == (e is None) and (gf is None or (gf.get("decision.FR") == e["dec"] and [
            gf.get(p) for p in GATE_LEAVES] == [e["gate"].get(p) for p in GATE_LEAVES])), "gates/: FR.json",
             "gates/FR.json differs from the applied copy (decision or reason lists)")
        need((g0 is None and (last is None or prepared)) or (g0 is not None and last is not None and
                                                              g0.get("decision.fr_step0") == last[2]),
             "gates/: fr_step0.json", "gates/fr_step0.json differs from the last applied step-0 decision")
        comp = gd.guarded_s2b(os.path.join(fr, "completeness.json"))
        need(comp is not None and comp.get("jobs") is not None, "completeness: file",
             "no completeness.json at CAMPAIGN_DONE")
        jobs = comp.get("jobs")
        for name, gid in GATES:
            has = os.path.exists(os.path.join(gdir, re.sub(r"[^A-Za-z0-9_.-]", "_", gid) + ".json"))
            need((jobs.get(gid) == "done") == has, "completeness: gate jobs", gid, jobs.get(gid))
        for lab in FR_LABELS:
            r = recs.get(lab)
            need(r is not None and jobs.get("a2:" + lab) == JOB_STATUS.get(r.get("status")),
                 "completeness: relaxation jobs", lab)
    return out, rerun, prepared


def e_reason(kind, rec):
    """e_eval.fr_reason on a record: the reason E's header names for the first FR-1 failure of kind at the cell of
    record rec ('check <failed>', 'end rule <outcome>', or E's word for the kind)."""
    if kind == "check":
        vf = rec.get("validity_final") if rec is not None else None
        failed = vf.get("failed") if vf is not None else None
        return "check " + (", ".join(str(x) for x in failed) if isinstance(failed, list) else "absent")
    if kind == "end_rule":
        er = rec.get("end_rule") if rec is not None else None
        return f"end rule {er.get('outcome') if er is not None else 'absent'}"
    return E_REASON.get(kind) or str(kind)


def set_aside_4(fr, gdir, recs):
    """IX-5, E's s0_set_aside (e_eval.Run.rf12_step0): the repeat of fr_step0@4 prepared but not recorded. No
    gates/fr_step0.json; of the step-0 gates only @2 applied; the @4 attempt-1 marker present under
    step0_attempt1/gates_applied/ (its existence only: never opened or listed); D+V without a record or pending."""
    mk = lambda gid: re.sub(r"[^A-Za-z0-9_.-]", "_", gid) + ".json"
    dv = recs.get(FR_LABELS[3])
    return (not os.path.exists(os.path.join(fr, "gates", "fr_step0.json")) and
            os.path.exists(os.path.join(gdir, mk(GATES[0][1]))) and
            not os.path.exists(os.path.join(gdir, mk(GATES[1][1])))
            and os.path.exists(os.path.join(fr, "step0_attempt1", "gates_applied", mk(GATES[1][1]))) and
            (dv is None or dv.get("status") == "pending"))


def set_aside_2(fr, gdir, recs):
    """Integration review 2 (IX-5 at @2, IX-11; the figure follows E): the repeat of fr_step0@2 prepared but not
    recorded, which E accepts with no step-0 evaluation in force (e_eval.Run.rf12_step0: neither marker, no
    gates/fr_step0.json, V+_R absent or pending; B2.step0.repeat names the set-aside @2 files). No gates/fr_step0.json;
    neither step-0 gate applied; the @2 attempt-1 marker present under step0_attempt1/gates_applied/ (its existence
    only: never opened or listed); V+_R without a record or pending."""
    mk = lambda gid: re.sub(r"[^A-Za-z0-9_.-]", "_", gid) + ".json"
    v = recs.get(FR_LABELS[1])
    return (not os.path.exists(os.path.join(fr, "gates", "fr_step0.json")) and
            not any(os.path.exists(os.path.join(gdir, mk(gid))) for _, gid in GATES[:2]) and
            os.path.exists(os.path.join(fr, "step0_attempt1", "gates_applied", mk(GATES[0][1]))) and
            (v is None or v.get("status") == "pending"))


def gate_fr_unapplied(fr):
    """IX-15, e_eval.gate_fr_unapplied: gate FR written but not applied (scripts/50 run_gate writes gates/FR.json before
    its gates_applied copy; an N-FR4 or N-FR8 'not applied' Stop comes between the two). By name only
    (os.path.exists): no gate file is opened. Pinned against E on the same archives."""
    return os.path.exists(os.path.join(fr, "gates", "FR.json")) and \
        not os.path.exists(os.path.join(fr, "gates_applied", "gate_FR.gate.json"))


def stop_note_ok(path, text):
    """e_eval.stop_note_ok (OP-19; IX-6): the one file STOP_NOTE (under S2/, not under s2b/), dated, stating that the
    fr STOP is final."""
    return path == STOP_NOTE and path.startswith(S2_REL + "/") and not path.startswith(f"{S2_REL}/s2b/") and \
        bool(STOP_PHRASE.search(text)) and bool(ISO_DATE.search(text))


def _git(repo, *args, ok=(0,)):
    """git -C repo args -> (exit code, stdout bytes), as e_eval.Git; an exit code outside ok fails the build."""
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True)
    need(r.returncode in ok, "stop note: git", f"git {args[0]} failed (exit {r.returncode})")
    return r.returncode, r.stdout


def stop_note(repo, path):
    """The stop note of a final STOP of fr (FG-2, IX-1), by E's tests: the committed-and-clean test of
    e_eval.Run.note_ok (a normalised repository-relative path; tracked and unchanged in the tree; its text read from
    HEAD), then e_eval.stop_note_ok on that text. Returns its path and the sha256 of its HEAD text, as E prints them on
    its FR-STOP route line."""
    need(isinstance(path, str) and not path.startswith("/") and not any(s in ("", ".", "..") for s in path.split("/")),
         "stop note: path", f"--stop-note {path!r}: a normalised repository-relative path is required")
    need(path == STOP_NOTE, "stop note: fixed path", f"--stop-note {path}: the stop note is the one file {STOP_NOTE} "
                                                     "(IX-6)")
    tracked = _git(repo, "ls-files", "--error-unmatch", "--", path, ok=(0, 1))[0] == 0
    need(tracked and not _git(repo, "status", "--porcelain", "--untracked-files=all", "--", path)[1],
         "stop note: committed and clean", f"--stop-note {path} is not committed and clean")
    rk, kind = _git(repo, "cat-file", "-t", f"HEAD:{path}", ok=(0, 128))   # IX-6: a blob of HEAD, as E requires
    rc, b = _git(repo, "show", f"HEAD:{path}", ok=(0, 128)) if rk == 0 and kind.strip() == b"blob" else (128, b"")
    need(rc == 0, "stop note: HEAD", f"--stop-note {path} is not a file of HEAD")
    text = b.decode(errors="replace")
    need(stop_note_ok(path, text), "stop note: text", f"--stop-note {path} is not a dated note under {S2_REL}/ (not "
                                                      "under s2b/) stating that the fr STOP is final (OP-19)")
    return {"path": path, "sha256": hashlib.sha256(text.encode()).hexdigest()}


def a2_stop_state(arch, M, note=None, repo=REPO):
    """campaign.json and the A2 stop state (state_end.json, written only at CAMPAIGN_DONE), both guarded; on a STOP,
    the stop note that makes it final (stop_note(); FG-2, IX-1); the verify record must exist (its existence only is
    checked). Returns (campaign, A2 stop state, stop note or None)."""
    gd = M["guard"]
    fr = os.path.join(arch, "fr")
    camp = gd.guarded_s2b(os.path.join(fr, "campaign.json"))
    need(camp is not None and camp.get("status") in ("done", "stopped"), "campaign",
         "the figure is built after CAMPAIGN_DONE or the final STOP of fr")
    # FG-2, IX-1: a STOP of fr is final only through its stop note, so a stopped fr without a valid one is refused
    # (a step-0 fail_pending_fix with no route taken among them); a stop note beside a done fr is refused
    sn = None
    if camp.get("status") == "stopped":
        # integration review 2 (IX-1: E's definition): a STOP before the node recorded the fr campaign commit (W 50
        # set_campaign: start_commit and commit null) is not evaluated; E refuses it until a dated amendment rules on
        # it (amendment 2026-11-12a item 11; e_eval.Run.route_admit), and so does the figure, before the note is read
        need(camp.get("start_commit") is not None or camp.get("commit") is not None, "campaign: no campaign commit",
             "fr stopped before its campaign commit was recorded (campaign.json start_commit and commit null): not "
             "evaluated until a dated amendment rules on it (amendment 2026-11-12a item 11), as E refuses it")
        # IX-15: gate FR written but not applied shows a disagreement between the runner and the gate, a defect
        # resolved by a dated fix and a relaunch, never by a stop note; refused before the note is read, as E does
        need(not gate_fr_unapplied(fr), "gates/: FR not applied", "fr stopped after gate FR was written but not "
             "applied (gates/FR.json without gates_applied/gate_FR.gate.json): resolved by a dated fix and a relaunch, "
             "never by a stop note (IX-15), as E refuses it")
        need(note is not None, "stop note: none", "fr stopped: a STOP is final only through its stop note; --stop-note "
                                                  "NOTE is required (FG-2, IX-1)")
        sn = stop_note(repo, note)
    else:
        need(note is None, "stop note: fr done", "--stop-note is refused: fr is done, there is no STOP")
    st = gd.guarded_s2b(os.path.join(fr, "state_end.json"))
    need((st is not None) == (camp.get("status") == "done"), "state_end", "state_end.json exists iff fr is done")
    need(os.path.isfile(os.path.join(arch, *VERIFY)), "verify",
         "the validity leaves are read only after verify: " + "/".join(VERIFY) + " is not in the archive")
    return camp, st, sn


# ---------------------------------------------------------------- cost (panel c)
def cost(arch, M, rows, repeat):
    """fr node-hours (operations note section 4): the boots of the last fr ledger whose campaigns include fr. The
    fr ledger is compared with C2's by boot id. The boot that ended C2 is the C2-ledger row marked current, or, if the
    C2 ledger marks none (written off the node), the last boot of C2 by boot time. Its increase since the C2 ledger is
    the tail of S2B section 8 (never negative), listed apart; if fr ran on that boot, the increase counts as fr (split
    at the C2 snapshot). Any change of another boot of the C2 ledger is a re-timed earlier boot, listed apart, as are
    manual rows new since the C2 ledger, boots of neither campaign and rows the ledger could not time."""
    led = M["guard"].guarded_s2b(os.path.join(arch, "fr", "ledger.json"))
    c2l = json.load(open(os.path.join(arch, "c2", "ledger.json")))       # C2's public ledger: no energy field
    c2b = [b for b in c2l["boots"] if b.get("boot_id") and not b.get("manual")]
    c2h = {b["boot_id"]: float(b["hours"]) for b in c2b if b.get("hours") is not None}
    end = [b["boot_id"] for b in c2b if b.get("current") is True]
    if not end:
        c2t = sorted((b for b in c2b if "c2" in (b.get("campaigns") or [])), key=lambda b: b.get("btime") or 0)
        end = [c2t[-1]["boot_id"]] if c2t else []
    need(len(end) == 1 and end[0] in c2h, "ledger: C2 end boot", f"{len(end)} candidate(s) for the boot that ended C2")
    c2man = {(b.get("btime"), b.get("end_used")) for b in c2l["boots"] if b.get("manual")}
    boots = led.get("boots")
    ids = [b.get("boot_id") for b in boots if b.get("manual") is not True and b.get("boot_id")]
    need(len(ids) == len(set(ids)), "ledger: duplicate boot", "a boot id appears twice in the fr ledger")
    frh, nfr, split, tail, man_n, man_h, other, prob, ret_n, ret_h = 0.0, 0, 0, 0.0, 0, 0.0, 0.0, 0, 0, 0.0
    for b in boots:
        if b.get("hours") is None:
            prob += 1; continue
        h = float(b.get("hours"))
        if b.get("manual") is True:
            if (b.get("btime"), b.get("end_used")) not in c2man:
                man_n += 1; man_h += h
            continue
        bid = b.get("boot_id")
        if "fr" in (b.get("campaigns") or []):
            if bid in c2h:
                need(bid == end[0], "ledger split: not the C2 end boot", "an fr boot of the C2 ledger did not end C2")
                need(h - c2h[bid] >= -1e-9, "ledger split: fewer hours", "an fr boot has fewer hours than in the C2 "
                                                                          "ledger")
                split += 1
                h -= c2h[bid]
            nfr += 1; frh += h
        elif bid == end[0]:
            tail = h - c2h[bid]
            need(tail >= -1e-9, "ledger: C2 boot tail negative",
                 "the boot that ended C2 has fewer hours than in the C2 ledger")
        elif bid in c2h:
            if abs(h - c2h[bid]) > 1e-9:
                ret_n += 1; ret_h += h - c2h[bid]
        else:
            other += h
    early = next(r for r in rows if r["role"] == "D")["status"] in NOT_STARTED
    plan = PLAN_FR_EARLY_H if early else PLAN_FR_H
    ran = [ROLE[r["role"]] for r in rows if r["status"] not in NOT_STARTED]
    walls = sum(float(r["wall_h"]) for r in rows if r["wall_h"] != "")
    return [{"key": k, "value": v} for k, v in (
        ("fr_node_h", repr(frh)), ("fr_boots", nfr), ("fr_boot_split_at_c2_ledger", split == 1),
        ("c2_tail_h", repr(tail)), ("retimed_boots", ret_n), ("retimed_boots_h", repr(ret_h)),
        ("manual_rows_new", man_n), ("manual_rows_new_h", repr(man_h)),
        ("other_boots_h", repr(other)), ("problem_rows", prob), ("ledger_complete", led.get("complete") is True),
        ("ledger_problems", len(led.get("problems") or [])), ("H_spent_h", repr(float(led.get("H_spent_h")))),
        ("H_spent_c2_ledger_h", repr(float(c2l["H_spent_h"]))), ("ledger_now_utc", led.get("now_utc")),
        ("wall_h_sum", repr(walls)), ("uncovered_h", repr(frh - walls)), ("early_stop", early),
        ("cells_run", " ".join(ran)), ("plan_fr_node_h", f"{plan[0]}-{plan[1]}"), ("step0_repeat", repeat),
        ("plan_repeat_max_h", PLAN_FR_REPEAT_H), ("cap_h", repr(CAP_H)))]


# ---------------------------------------------------------------- build
def build(arch=S2, src=SRC, note=None, repo=REPO):
    """The source data from the fr archive at arch, with the build asserts; note: the stop note of a final STOP of fr
    (a repository-relative path in repo), required when fr is stopped and refused when it is done."""
    M = modules()
    q47 = M["q47"]
    pins(M)
    need(not any(v for k, v in q47.READS.items()), "READS: before the build", "a value was read before the build")
    for fn, cols in COLUMNS.items():
        need(not [c for c in cols if energy_column(c)], "energy column: header", fn,
             [c for c in cols if energy_column(c)])
    camp, st, sn = a2_stop_state(arch, M, note, repo)
    # the cell rerun after STEP0_FIX is known from the decision leaves; relaxations() only marks it
    recs0 = {lab: M["guard"].guarded_s2b(os.path.join(arch, "fr", "raw", f"{lab}.a2.json")) for lab in FR_LABELS}
    gt, rerun, repeat = fr_gates(arch, M, recs0, camp, st, sn)
    rows, pts, recs = relaxations(arch, M, rerun)
    cs = cost(arch, M, rows, repeat)
    const = [{"key": "forc_conv_thr_Ry_bohr", "value": repr(q47.FORC_CONV_THR)},
             {"key": "forc_conv_thr_eV_A", "value": repr(q47.FORC_CONV_THR * q47.RY_EV / q47.BOHR_A)},
             {"key": "k_cap", "value": q47.K_CAP}]
    stop = [{"key": "fr_status", "value": camp.get("status")},           # FG-2: the stop note of a final STOP
            {"key": "stop_note", "value": sn["path"] if sn else ""},
            {"key": "stop_note_sha256", "value": sn["sha256"] if sn else ""}]
    need(q47.READS["F"] == 0 and q47.READS["ase"] == 0 and set(k for k, v in q47.READS.items() if v) <= {"forces"},
         "READS: after the build", "scripts/47 read a value other than forces", dict(q47.READS))
    os.makedirs(src, exist_ok=True)
    for fn, data in (("fig_s2b_fr_a_force.csv", pts), ("fig_s2b_fr_a_relaxations.csv", rows),
                     ("fig_s2b_fr_b_gates.csv", gt), ("fig_s2b_fr_b_stop.csv", stop),
                     ("fig_s2b_fr_c_cost.csv", cs), ("fig_s2b_fr_constants.csv", const)):
        need(all(list(r) == COLUMNS[fn] for r in data), "columns", fn)
        if COLUMNS[fn] == ["key", "value"]:
            need(not [r["key"] for r in data if energy_column(r["key"])], "energy column: key/value", fn,
                 [r["key"] for r in data if energy_column(r["key"])])
        with open(os.path.join(src, fn), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLUMNS[fn]); w.writeheader(); w.writerows(data)
    print("source data written:", len(pts), "force points,", sum(r["line"] != "none" for r in rows), "lines,",
          "gates:", "; ".join(f"{r['gate']} {r['state']}" for r in gt) +
          (f"; final STOP by the stop note {sn['path']} (sha256 {sn['sha256']})" if sn else ""))
    return {"rows": rows, "gates": gt, "cost": cs, "points": pts, "stop": stop}


# ---------------------------------------------------------------- plot
ROLE_COL = {"host": "#2f6db5", "V": "#d08a2e", "D": "#2a9d8f", "DV": "#a4508b"}   # colour: the cell role
LS = {"host": "-", "V": (0, (4, 1.6)), "D": (0, (1, 1.3)), "DV": (0, (5, 1.4, 1, 1.4))}
GL = {"accepted_converged": ("o", 15), "accepted_plateau": ("^", 17), "unconverged_cap": ("X", 18),
      "unconverged_early": ("s", 13)}                                   # end glyph and its area (pt^2)
GATE_NAME = {"fr_step0@2": "Step-0 at 2 (V, k = 0)", "fr_step0@4": "Step-0 at 4 (D+V, k = 0)",
             "FR": "Gate FR (FR-1, FR-2)"}
ARROW_MS = 6.0                 # edge-arrow marker size (pt); a value sits ARROW_MS / 2 + 1.5 pt left of a right arrow
NO_CONFIG = "no config."       # panel c, minutes per configuration of a relaxation with n_config = 0
ZERO_DX = 3.0                  # panel c: a marker at x = 0 (n_config = 0) sits this many points right of the spine
FIG_WIDTH_MM = 183.0           # double column


def wrap(text, width):
    """text in the fewest lines of at most width characters, balanced (the narrowest width that needs no more lines,
    never narrower than its longest word), and narrowed further while a line of a text that wraps would hold a single
    word (FG-4: no lone word, such as the 'D' of FR's detail in the pass scenario, on a line of panel b)."""
    longest = max(map(len, text.split()), default=1)
    n, w = len(textwrap.wrap(text, width)), width
    while w > longest and len(textwrap.wrap(text, w - 1)) == n:
        w -= 1
    for v in range(w, longest - 1, -1):
        ws = textwrap.wrap(text, v)
        if len(ws) < 2 or all(len(x.split()) > 1 for x in ws):
            return ws
    return textwrap.wrap(text, width)


def clip_log(k, f, lo, hi):
    """The polyline (k, f) cut at the log-axis limits: the crossing of each segment with lo or hi is inserted (in
    log10 f, where the drawn segment is straight) and the points outside become gaps. The drawing equals the clipped
    line, but no path leaves the plot area (the PDF collision audit does not see clip paths)."""
    L, U = math.log10(lo), math.log10(hi)
    lf, k = np.log10(np.asarray(f, float)), np.asarray(k, float)
    X, Y = [k[0]], [lf[0]]
    for i in range(1, len(k)):
        a, b = lf[i - 1], lf[i]
        for t, B in sorted(((B - a) / (b - a), B) for B in (L, U) if (a - B) * (b - B) < 0):
            X.append(k[i - 1] + t * (k[i] - k[i - 1])); Y.append(B)
        X.append(k[i]); Y.append(b)
    X, Y = np.array(X), np.array(Y)
    Y[(Y < L - 1e-12) | (Y > U + 1e-12)] = np.nan
    return X, 10.0 ** Y


def plot(src=SRC, out=OUT, formats=("pdf", "svg", "png", "tiff"), audit=True, probe=None, skew_pt=0.0):
    """The figure from the source data. audit: True runs the panel-alignment gate when the nature-figure toolkit can
    be imported, 'required' fails when it cannot, False skips it. probe(fig, axes) is called after the final draw
    and the alignment gate, before the figure is saved and closed (the self-test checks the drawn marks with it).
    skew_pt (self-test only, a negative control of the alignment gate): c3 is moved down by this many points."""
    import matplotlib as mpl
    mpl.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    sys.path.insert(0, QA_DIR)
    try:      # layout QA from the nature-figure toolkit; required by the self-test
        from audit_panel_alignment import require_matplotlib_panel_alignment
    except ImportError:
        if audit == "required":
            raise
        require_matplotlib_panel_alignment = None
        if audit:
            print("note: panel-alignment audit unavailable; figure rendered without it")
    mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                         "svg.fonttype": "none", "pdf.fonttype": 42, "font.size": 7, "axes.spines.right": False,
                         "axes.spines.top": False, "axes.linewidth": 0.8,
                         "legend.frameon": False, "xtick.major.width": 0.8, "ytick.major.width": 0.8,
                         "xtick.labelsize": 6, "ytick.labelsize": 6, "axes.labelsize": 6.5,
                         "svg.hashsalt": "fig_s2b_fr"})               # fixed SVG ids: reproducible output
    rd = lambda fn: list(csv.DictReader(open(os.path.join(src, fn))))
    R, P, G = rd("fig_s2b_fr_a_relaxations.csv"), rd("fig_s2b_fr_a_force.csv"), rd("fig_s2b_fr_b_gates.csv")
    C = {r["key"]: r["value"] for r in rd("fig_s2b_fr_c_cost.csv")}
    K = {r["key"]: r["value"] for r in rd("fig_s2b_fr_constants.csv")}            # scripts/47 values, via --build
    NEU, FAIL, INK, BAND, BAND2 = "#9aa3ad", "#c4553a", "#3a3a3a", "#e6e9ed", "#f2f3f5"
    THR = float(K["forc_conv_thr_eV_A"])                                    # forc_conv_thr in eV/A (scripts/47)
    YLO, YHI = 1e-3, 10.0
    name = lambda r: f"{r['order']}  {ROLE[r['role']]}"
    up = [(-0.12, -1), (0.12, -1), (0.12, 0.15), (0.5, 0.15), (0, 1), (-0.5, 0.15), (-0.12, 0.15), (-0.12, -1)]
    ARROW = {w: mpl.path.Path([f(x, y) for x, y in up], closed=True) for w, f in (    # filled arrow markers (no
        ("top", lambda x, y: (x, y)), ("bottom", lambda x, y: (x, -y)), ("right", lambda x, y: (y, x)))}  # end glyph)

    def edge(ax, x, y, where, txt, col, gid):                             # a value outside the axis: arrow + value
        if where == "right":            # the value ends ARROW_MS / 2 + 1.5 pt left of the arrow's centre (in points)
            ax.plot([0.985], [y], marker=ARROW["right"], ms=ARROW_MS, color=col, transform=ax.get_yaxis_transform(),
                    clip_on=False, ls="none", gid=f"arrow:{gid}")
            ax.annotate(txt, (0.985, y), xycoords=ax.get_yaxis_transform(), xytext=(-(ARROW_MS / 2 + 1.5), 0),
                        textcoords="offset points", ha="right", va="center", fontsize=6, color=col,
                        annotation_clip=False, gid=f"arrowval:{gid}")
        else:
            yy = 0.975 if where == "top" else 0.025
            ax.plot([x], [yy], marker=ARROW[where], ms=ARROW_MS, color=col, transform=ax.get_xaxis_transform(),
                    clip_on=False, ls="none", gid=f"arrow:{gid}")
            if txt:                                    # left of the arrow near k = 200, so it stays on the canvas
                right = x > 170
                ax.text(x - 3 if right else x + 3, yy if where == "top" else 0.07, txt, ha="right" if right else "left",
                        transform=ax.get_xaxis_transform(), va="center", fontsize=6, color=col, gid=f"arrowval:{gid}")

    # panel b's rows are wrapped first: its height follows from its text (6 pt lines), so nothing overlaps
    brows = []
    for r in G:
        ws = wrap(r["state"], 33)
        wd = wrap(r["detail"], 100) if r["detail"] else []
        brows.append((r, ws, wd, max(len(ws), len(wd), 1)))
    LINE, MM = 6 * 1.2 / 72 * 25.4, 1 / 25.4                               # a 6 pt text line in mm; mm in inches
    b_mm = 3.6 + sum(n * LINE + 0.8 for *_, n in brows)
    rep, early = C["step0_repeat"] == "True", C["early_stop"] == "True"
    cells = C["cells_run"].split()
    c3_lines = 1 + (early or len(cells) < 4) + rep                         # the lines of c3's x label
    rows_mm = [13.0, 56.0, 19.5, b_mm, 9.5, 24.0]          # above a | a | a's axis and key | b | c titles | c
    top_mm, bot_mm, W = 1.5, 11.0 + (2.8 if c3_lines > 2 else 0.0), FIG_WIDTH_MM
    H = top_mm + sum(rows_mm) + bot_mm
    fig = plt.figure(figsize=(W * MM, H * MM))                             # 183 mm wide; height from panel b
    gs = fig.add_gridspec(6, 4, height_ratios=rows_mm, left=14.0 / W, right=1 - 3.0 / W, bottom=bot_mm / H,
                          top=1 - top_mm / H, hspace=0.0, wspace=0.55)
    a = fig.add_subplot(gs[1, :]); b = fig.add_subplot(gs[3, :])
    c1 = fig.add_subplot(gs[5, 0]); c2 = fig.add_subplot(gs[5, 1], sharey=c1); c3 = fig.add_subplot(gs[5, 2:])
    y_mm = lambda d: 1 - d / H                          # figure y of a point d mm below the top edge

    # (a) largest free-atom force component against k; QE's own flag, not this curve, decides the end rule
    hl, ll = [], []
    for r in R:
        o, rl = int(r["order"]), r["role"]
        lab = name(r) + ("  (rerun after the step-0 fix)" if r["step0_rerun"] == "True" else "")
        if r["status_text"] != "complete":                                 # D-C2-10 wording, made by --build
            lab += f": {r['status_text']}"
        q = [(int(p["k"]), float(p["fmax_free_eV_A"])) for p in P if int(p["order"]) == o]
        col = ROLE_COL[rl]
        if r["line"] == "none" or not q:
            hl.append(Line2D([], [], color="none")); ll.append(lab)
            continue
        k, f = np.array([x for x, _ in q]), np.array([y for _, y in q])
        a.plot(*clip_log(k, f, YLO, YHI), color=col, ls=LS[rl], lw=0.9, zorder=3, gid=f"curve:{o}")
        for s in (int(x) for x in r["part_starts"].split()):              # restart part boundaries
            a.plot([s], [min(max(f[list(k).index(s)], YLO), YHI)], marker="|", ms=6, mew=1.0, color=col, zorder=4,
                   clip_on=False, ls="none", gid=f"tick:{o}:{s}")
        fe = min(max(f[-1], YLO), YHI)                                   # an end outside the axis sits on its edge
        if r["line"] == "complete" and r["outcome"] in GL:
            mk, sz = GL[r["outcome"]]
            a.plot([k[-1]], [fe], marker=mk, ms=math.sqrt(sz), color=col, mec="white", mew=0.4, ls="none", zorder=5,
                   clip_on=False, gid=f"end:{o}")
        elif r["line"] == "stopped":                                     # open end: the record is still pending
            a.plot([k[-1]], [fe], marker="o", ms=math.sqrt(15), mfc="white", mec=col, mew=0.9, ls="none", zorder=5,
                   clip_on=False, gid=f"end:{o}")
        for sel, where in ((f > YHI, "top"), (f < YLO, "bottom")):       # every outside point gets an edge arrow;
            idx = np.flatnonzero(sel)                                      # the value of each excursion's extreme
            for run in np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1) if idx.size else []:   # and of an outside
                i = run[np.argmax(f[run])] if where == "top" else run[np.argmin(f[run])]          # end is printed
                for j in run:
                    edge(a, k[j], None, where, f"{f[j]:.3g} eV/Å" if j == i or j == len(f) - 1 else "", col,
                         f"a:{o}:{k[j]}")
        hl.append(Line2D([], [], color=col, ls=LS[rl], lw=0.9)); ll.append(lab)
    a.axhline(THR, color=INK, lw=0.6, ls=(0, (3, 2)), zorder=2, gid="thr")
    a.axvline(200, color=NEU, lw=0.6, ls=":", zorder=1, gid="k200")
    a.set_yscale("log"); a.set_ylim(YLO, YHI); a.set_xlim(-2, 202)
    a.yaxis.set_major_locator(mpl.ticker.FixedLocator([1e-3, 1e-2, 1e-1, 1, 10]))
    a.yaxis.set_major_formatter(mpl.ticker.FixedFormatter(["0.001", "0.01", "0.1", "1", "10"]))
    a.yaxis.set_minor_formatter(mpl.ticker.NullFormatter())
    a.set_xlabel("Configuration k (ionic SCF cycle, counted across restarts); dotted: k = 200 (cap)", labelpad=2)
    a.set_ylabel("Largest free-atom force component (eV/Å)")
    pa = a.get_position()
    fig.text(pa.x0, y_mm(top_mm), "FR relaxations of the attempt in force, Cs at m30 FA188: force criterion against "
                                  "k (energies not shown)", fontsize=7, va="top", ha="left")
    leg = a.legend(hl, ll, loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2, fontsize=6, handlelength=2.6,
                   columnspacing=2.0, borderaxespad=0.8, borderpad=0.0, title="Relaxation in run order; colour and "
                   "line: cell (V: iodide vacancy, q = +1; D: Cs on FA188)", title_fontsize=6)
    leg._legend_box.align = "left"                # the key sits above the plot area, which stays free for the data
    gh = [Line2D([], [], marker=GL[o][0], ms=math.sqrt(GL[o][1]), color=INK, mec="white", mew=0.4, ls="none")
          for o in GL] + \
        [Line2D([], [], marker="o", ms=math.sqrt(15), mfc="white", mec=INK, mew=0.9, ls="none"),
         Line2D([], [], marker="|", ms=6, mew=1.0, color=INK, ls="none"),
         Line2D([], [], marker=ARROW["top"], ms=ARROW_MS, color=INK, ls="none"),
         Line2D([], [], color=INK, lw=0.6, ls=(0, (3, 2)))]
    gkey = fig.legend(gh, ["accepted: converged", "accepted: plateau", "unconverged: cap", "unconverged: early end",
                          "stopped (pending)", "restart", "off-axis value",
                          f"forc_conv_thr {float(K['forc_conv_thr_Ry_bohr']):g} Ry/bohr = {THR:.4g} eV/Å"],
                     loc="upper left", ncol=4, fontsize=6,
                     bbox_to_anchor=(pa.x0, y_mm(top_mm + sum(rows_mm[:2]) + 10.5)), handletextpad=0.4,
                     columnspacing=1.6, borderaxespad=0.0, borderpad=0.0, handlelength=2.2)

    # (b) the gate strip: each fr gate in its state; no step-0 or FR-2 value exists in the source data. A final STOP
    # in fr is an FR failure (S2B section 1, route table), so FR 'not reached (after a final STOP)' is drawn as one
    b.set_axis_off(); b.set_xlim(0, 1); b.set_ylim(0, 1)
    put = lambda x, dy, s, **kw: b.annotate(s, (x, 1), xycoords="axes fraction", xytext=(0, -dy / 25.4 * 72),
                                            textcoords="offset points", va="top", ha="left", fontsize=6,
                                            linespacing=1.2, annotation_clip=False, **kw)
    put(0, 0, "fr gates in their state (attempt in force); no step-0 value and no FR-2 value is read or shown",
        color=INK).set_fontsize(7)
    dy = 3.6                                                                 # mm below the top of panel b
    for r, ws, wd, n in brows:
        s = r["state"]
        bad = s.startswith("fail") or (r["gate"] == "FR" and (s.startswith("not reached (after a final STOP)") or
                                                              "; then a final STOP (" in s))     # IX-4: FR fails
        col = FAIL if bad else INK if s.startswith("pass") else NEU
        put(0, dy, GATE_NAME[r["gate"]], color=INK, gid=f"b:{r['gate']}:name")
        put(0.17, dy, "\n".join(ws), color=col, gid=f"b:{r['gate']}:state")
        if wd:
            put(0.375, dy, "\n".join(wd), color=INK, gid=f"b:{r['gate']}:detail")
        dy += n * LINE + 0.8

    # (c) cost: configurations, minutes per configuration, and fr node-hours (S2B_PLAN.md section 8)
    ys = {int(r["order"]): 4 - int(r["order"]) for r in R}
    note = lambda axx, y, t, gid: axx.annotate(t, (0, y), xycoords=("axes fraction", "data"), xytext=(2, 0),
                                               textcoords="offset points", va="center", ha="left", fontsize=6,
                                               color=NEU, gid=gid)
    for axx, key, lim, tag in ((c1, "n_config", (0, 210), "c1"), (c2, "min_per_config", (0, 10), "c2")):
        if key == "n_config":
            axx.axvline(CAP_CONFIGS, color=INK, lw=0.6, ls=(0, (3, 2)), gid="cap201")
        else:
            axx.axvspan(*RATE_BAND, color=BAND, zorder=0, lw=0, gid="rateband")
        for r in R:
            o = int(r["order"])
            y = ys[o]
            if r["n_config"] == "":                     # no record of configurations: the status (D-C2-10 wording)
                if key == "n_config":
                    note(axx, y, r["status_text"], f"{tag}text:{o}")
                continue
            if key == "min_per_config" and int(r["n_config"]) < 1:     # wall time / max(1, 0): not a rate
                note(axx, y, NO_CONFIG, f"{tag}text:{o}")
                continue
            v, col = float(r[key]), ROLE_COL[r["role"]]
            mk, sz = GL.get(r["outcome"], ("o", 15))
            if v > lim[1]:
                edge(axx, None, y, "right", f"{v:.3g}", col, f"{tag}:{o}")
            else:                                   # a marker at x = 0 sits ZERO_DX pt right of the spine, not on it
                tr = mpl.transforms.offset_copy(axx.transData, fig=fig, x=ZERO_DX, units="points") if v == 0 else \
                    axx.transData
                axx.plot([v], [y], marker=mk, ms=math.sqrt(sz), color=col, mec="white", mew=0.4, ls="none", zorder=3,
                         clip_on=False, transform=tr, gid=f"{tag}:{o}")
        axx.set_xlim(*lim)
    c1.set_ylim(-0.6, 3.6)
    c1.set_yticks([ys[int(r["order"])] for r in R], [name(r) for r in R])
    plt.setp(c2.get_yticklabels(), visible=False)
    ranks = sorted({r["ranks"] for r in R if r["ranks"] != ""})
    c1.set_xlabel("Configurations per relaxation\ndashed: cap 201")
    c2.set_xlabel("Wall minutes" + (f", {', '.join(ranks)} MPI ranks" if ranks else "") +
                  "\nband: C2 range 4.19–4.65")
    c1.set_title("Configurations", fontsize=7, pad=4); c2.set_title("Minutes per configuration", fontsize=7, pad=4)
    plan = [int(x) for x in C["plan_fr_node_h"].split("-")]
    nb = int(C["fr_boots"])
    bars = (("fr", 2, f"fr ({nb} boot{'s' if nb != 1 else ''})", float(C["fr_node_h"]), INK),
            ("manual", 1, "manual rows", float(C["manual_rows_new_h"]), NEU),
            ("tail", 0, "C2 boot tail", float(C["c2_tail_h"]), NEU))
    # S2B section 8: up to 72 with a step-0 repeat, for the four and on FR failure alike (the lighter band)
    rep_hi = int(C["plan_repeat_max_h"]) if rep else None
    XMAX = max(80.0, 10.0 * math.ceil(1.12 * max([v for *_, v, _ in bars] + [plan[1], rep_hi or 0]) / 10.0))
    c3.fill_betweenx([1.62, 2.38], *plan, color=BAND, lw=0, zorder=0, gid="planband")
    if rep_hi:
        c3.fill_betweenx([1.62, 2.38], plan[1], rep_hi, color=BAND2, lw=0, zorder=0, gid="repeatband")
    for bk, yy, _, v, col in bars:                     # the axis holds every bar; the value sits 2 pt right of it
        c3.barh([yy], [max(v, 0.0)], height=0.5, color=col, zorder=2).patches[0].set_gid(f"bar:{bk}")
        c3.annotate(f"{v:.1f}", (max(v, 0.0), yy), xytext=(2, 0), textcoords="offset points", va="center",
                    ha="left", fontsize=6, color=col, gid=f"barval:{bk}")
    c3.set_xlim(0, XMAX); c3.set_ylim(-0.6, 2.95)                       # room above the band for the ledger flag
    c3.set_yticks([x[1] for x in bars], [x[2] for x in bars])
    xl3 = [f"Node-hours; band: plan {plan[0]}–{plan[1]}" + (", early stop" if early else " for the four") +
           " (S2B section 8)"]
    if early or len(cells) < 4:
        xl3.append(f"FR ran {', '.join(cells) or 'no cell'}")
    if rep:
        xl3.append(f"lighter band: up to {rep_hi}" + (" on FR failure" if early else "") + " with a step-0 repeat")
    assert len(xl3) == c3_lines
    c3.set_xlabel("\n".join(xl3))
    c3.set_title(f"fr node-hours (S2 so far {float(C['H_spent_h']):.1f} of {float(C['cap_h']):.0f})", fontsize=7,
                 pad=4, loc="left")
    if C["ledger_complete"] != "True":
        c3.text(1, 0.99, f"ledger incomplete: {C['ledger_problems']} problem(s), {C['problem_rows']} boot(s) "
                         "untimed", transform=c3.transAxes, ha="right", va="top", fontsize=6, color=FAIL,
                gid="ledger_incomplete")
    ret = f"{float(C['retimed_boots_h']):+.1f}".replace("-", "−")              # a minus sign, not a hyphen
    c3.text(1, -0.6, f"ledger {C['ledger_now_utc']}" + (f"; re-timed earlier boots {ret} node-h" if int(
        C["retimed_boots"]) else ""),
            transform=mpl.transforms.blended_transform_factory(c3.transAxes, c3.transData), ha="right", va="bottom",
            fontsize=6, color=NEU, gid="ledger_note")

    xl = a.get_position().x0 - 12.0 / W                                    # panel letters 12 mm left of the axes
    for lab, d, axx in (("a", top_mm, a), ("b", top_mm + sum(rows_mm[:3]), b)):   # axes texts: the alignment gate
        axx.text(xl, y_mm(d), lab, fontsize=8, fontweight="bold", va="top", ha="left",    # finds them
                 transform=fig.transFigure, gid=f"label:{lab}")
    fig.text(xl, y_mm(top_mm + sum(rows_mm[:4]) + 1.5), "c", fontsize=8, fontweight="bold", va="top", ha="left",
             gid="label:c")
    if skew_pt:                                       # self-test only: c3 off its row (the alignment gate must fail)
        p3 = c3.get_position()
        c3.set_position([p3.x0, p3.y0 - skew_pt / 72.0 / (H * MM), p3.width, p3.height])
    try:
        fig.canvas.draw()
        if audit and require_matplotlib_panel_alignment is not None:
            require_matplotlib_panel_alignment(fig, json_out=out + ".alignment.json",
                                               overlay_svg=out + ".alignment.svg", axes=[a, b, c1, c2, c3],
                                               panel_ids=["a", "b", "c1", "c2", "c3"], row_groups=[["c1", "c2", "c3"]],
                                               column_groups=[["a", "b"]], **ALIGN_KW)
            # the panel labels (QA contract): the a-b column; the three strips of c share one label (checked in the
            # self-test), so the row c1-c3 cannot carry require_panel_labels
            require_matplotlib_panel_alignment(fig, json_out=out + ".labels.alignment.json", axes=[a, b],
                                               panel_ids=["a", "b"], column_groups=[["a", "b"]],
                                               require_panel_labels=True, **ALIGN_KW)
        if probe is not None:
            probe(fig, {"a": a, "b": b, "c1": c1, "c2": c2, "c3": c3, "legend": leg, "key": gkey})
        if "pdf" in formats:
            fig.savefig(out + ".pdf", metadata={"CreationDate": None})       # no render date: reproducible outputs
        if "svg" in formats:
            fig.savefig(out + ".svg", metadata={"Date": None})
        if "png" in formats:
            fig.savefig(out + ".png", dpi=600)
        if "tiff" in formats:
            fig.savefig(out + ".tiff", dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    finally:
        plt.close(fig)
    print("written", out + ".{" + ",".join(formats) + "}")


def qa(out, required=False):
    """PDF text >= MIN_TEXT_PT (5 pt) and the rendered collision audit of the nature-figure toolkit on out.pdf; the
    collision report is written beside it with the PDF's file name only (the report is committed with the figure, and
    the public repository holds no local path). Returns (minimum text size, collision verdict, fail count, warn
    count)."""
    sys.path.insert(0, QA_DIR)
    try:
        import audit_pdf_text, audit_figure_collisions
        from pathlib import Path
    except ImportError as x:
        if required:
            raise
        print(f"note: PDF QA unavailable ({x})")
        return None
    t = audit_pdf_text.audit_pdf(open(out + ".pdf", "rb").read(), minimum_pt=MIN_TEXT_PT)
    c = audit_figure_collisions.audit_pdf(Path(out + ".pdf"))
    c = {**c, "pdf": os.path.basename(c["pdf"])}                         # no local path in the committed report
    with open(out + ".collision-audit.json", "w") as fh:
        json.dump(c, fh, indent=1)
    assert t["auditable"] and t["below_minimum_count"] == 0, \
        f"PDF text below {MIN_TEXT_PT:g} pt: {t['below_minimum'][:3]}"
    assert c["auditable"] and c["summary"]["fail"] == 0, \
        "collision audit: " + "; ".join(f"{f['kind']} {f['text']!r}" for f in c["findings"] if f["severity"] == "FAIL")
    return t["minimum_found_pt"], c["verdict"], c["summary"]["fail"], c["summary"]["warn"]


# ---------------------------------------------------------------- self-test (synthetic archives; no fr file is read)
# Every energy line of the synthetic part outputs (the '!' and SCF total energies, the internal energy and its terms,
# the BFGS energies old/new and the final energy) holds the one value E_PART_RY Ry, and the Fermi line E_FERMI_EV eV:
# the public WP2e energies never reach an fr-shaped archive, and a figure that read an energy line would write a
# canary (in Ry, eV, meV or Ha) that the scan below finds.
E_PART_RY, E_FERMI_EV = 4321.98765432, 7.43219
CANARY = {"dF_200_180_meV": 9876.54321, "Eb_A2_meV": 7654.321, "Eb_A1_meV": 6543.21, "delta_far_meV": 1111.111,
          "dF_meV": 2345.678, "E_mace_eV": 6182.37, "F_eV": 8765.4321,
          "E_part_Ry": E_PART_RY, "E_part_eV": E_PART_RY * 13.605693122994, "E_part_Ha": E_PART_RY / 2.0,
          "E_fermi_eV": E_FERMI_EV}
CANARY_SCALES = (1.0, 1e-3, 1e3, 1e-6, 1 / 13.6057, 1 / 27.2114, 1e-3 / 13.6057, 1e-3 / 27.2114)   # meV, eV, Ry, Ha
E_LINE = re.compile(r"^(?P<h>!?\s*(?:total energy|internal energy E=F\+TS|one-electron contribution|hartree "
                    r"contribution|xc contribution|ewald contribution|smearing contrib\. \(-TS\)|Final energy|energy"
                    r"\s+new|energy\s+old)\s+=\s+)(?P<v>-?\d+\.\d+)(?P<t>\s+Ry)", re.M)
E_ERROR = re.compile(r"^(?P<h>\s*Energy error\s+=\s+)(?P<v>\S+)(?P<t>\s+Ry)", re.M)
E_FERMI = re.compile(r"^(?P<h>\s*the Fermi energy is\s+)(?P<v>-?\d+\.\d+)(?P<t>\s+ev)", re.M)
_OPENED, _LISTED, _UNGUARDED, _UNREAD = [], [], [], []   # attempt-1 paths opened or listed, fr JSON opened outside
#                                                          the guard, part outputs opened outside the force reader
_ARMED = [False]
_GUARD = [None, None, None, None]   # the fr folder being built, guard.py, fig_s2_c2_a2.py, scripts/47 (real paths)


def _blind_part(txt):
    """A synthetic part output with every energy value replaced by the canary (QE's formats; the markers, counters and
    force rows that the count-mode reader and the force reader use are untouched)."""
    txt = E_LINE.sub(lambda m: m["h"] + f"-{E_PART_RY:.{len(m['v'].split('.')[1])}f}" + m["t"], txt)
    txt = E_ERROR.sub(lambda m: m["h"] + "0.0E+00" + m["t"], txt)
    return E_FERMI.sub(lambda m: m["h"] + f"{E_FERMI_EV:.4f}" + m["t"], txt)


def _part_energies(txt):
    """Every value in Ry, eV or Ha on a line of a part output that names an energy or an energy term (the input
    cutoffs and thresholds of the header excepted), and every '!' line value: the self-test's check, wider than the
    substitution, that _blind_part left no WP2e energy."""
    num = r"(-?\d+\.\d+(?:[EeDd][+-]?\d+)?)\s*(?:Ry|ev|eV|Ha)\b"
    vals = set()
    for ln in txt.splitlines():
        if re.search(r"(?i)energy|contribution|contrib\.|enthalpy", ln) and \
                not re.search(r"(?i)cutoff|criteria|thresh", ln):
            vals |= set(re.findall(num, ln))
        if ln.lstrip().startswith("!"):
            vals |= set(re.findall(r"=\s*(-?[\d.]+)", ln))
    return vals


def _audit_hook(event, args):
    """While armed: an attempt-1 path under step0_attempt1/ must not be opened or listed; every fr JSON file of the
    archive being built must be opened from s2b/guard.py (guarded_s2b or gate_leaves) on the call stack; and an fr
    part output (fr/raw/*.out.gz) only by the force-only reader, force_curve of fig_s2_c2_a2.py (with parse_relax of
    scripts/47 in count mode inside it), on the call stack."""
    if not _ARMED[0] or event not in ("open", "os.listdir", "os.scandir") or not args or \
            not isinstance(args[0], (str, bytes, os.PathLike)):
        return
    p = os.fsdecode(args[0])
    if "step0_attempt1" in p:
        (_OPENED if event == "open" else _LISTED).append(p)
        raise PermissionError(f"canary: an attempt-1 path was {'opened' if event == 'open' else 'listed'}: "
                              f"{os.path.basename(p)}")
    if event != "open" or not _GUARD[0]:
        return
    is_json, is_out = p.endswith(".json"), p.endswith((".out", ".out.gz"))
    if not (is_json or is_out) or not os.path.realpath(p).startswith(_GUARD[0] + os.sep):
        return
    ok = (("guarded_s2b", _GUARD[1]), ("gate_leaves", _GUARD[1])) if is_json else \
        (("force_curve", _GUARD[2]), ("parse_relax", _GUARD[3]))
    f = sys._getframe(1)
    while f is not None:
        if (f.f_code.co_name, os.path.realpath(f.f_code.co_filename)) in ok:
            return
        f = f.f_back
    rel = os.path.relpath(os.path.realpath(p), _GUARD[0])
    if is_json:
        _UNGUARDED.append(p)
        raise PermissionError(f"guard bypass: fr/{rel} was opened outside s2b/guard.py")
    _UNREAD.append(p)
    raise PermissionError(f"blinding: the part output fr/{rel} was opened outside the force-only reader")


class _Armed:
    """Arms the audit hook for one build (and plot) of the archive at root."""

    def __init__(self, root):
        self.fr = os.path.realpath(os.path.join(root, "fr"))

    def __enter__(self):
        _GUARD[0], _ARMED[0] = self.fr, True

    def __exit__(self, *exc):
        _GUARD[0], _ARMED[0] = None, False


def _canary_hits(text):
    """Numbers in text equal to a canary in meV, eV, Ry or Ha (CANARY_SCALES) to the precision printed: decimals with
    at least 3 significant digits (to half a unit of the last digit), integers with at least 4 digits (to 0.5)."""
    hits = []
    for s in re.findall(r"\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", text):
        mant = re.split(r"[eE]", s)[0]
        digits, dec = mant.replace(".", "").lstrip("0"), "." in mant or "e" in s.lower()
        x = float(s)
        if not digits or x == 0.0 or len(digits) < (3 if dec else 4):
            continue
        tol = 0.5 * 10.0 ** (math.floor(math.log10(x)) - len(digits) + 1) if dec else 0.5
        hits += [s for c in CANARY.values() for sc in CANARY_SCALES if abs(x - c * sc) <= tol * (1 + 1e-9)]
    return hits


def _wj(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)


def _edit(path, fn):
    d = json.load(open(path)); fn(d); _wj(d, path)


def _input(wp, free):
    """The WP2e input with '0 0 0' on every atom outside the free set (the scripts/47 writer's convention)."""
    lines, fs = wp.inp.split("\n"), set(free)
    h = next(i for i, ln in enumerate(lines) if ln.startswith("ATOMIC_POSITIONS"))
    pos = [ln.rstrip() + ("" if i in fs else "    0   0   0") for i, ln in enumerate(lines[h + 1:h + 235])]
    return "\n".join(lines[:h + 1] + pos + lines[h + 235:])


def _free_sets(region):
    f = sorted(int(i) for i in region["free"])
    return {"host": f, "V": f[:-1], "D": f[:57], "DV": f[:56]}       # synthetic start-record free lists


RATE_SYN = {"host": 4.25, "V": 4.4, "D": 4.55, "DV": 4.7}          # synthetic minutes per configuration, per cell


def _spec_nc(spec):
    """n_config of a synthetic relaxation, from its specification (kind, n, splits, status, outcome)."""
    kind, n = spec[0], spec[1]
    return {"conv": n + 1 if n is not None else 0, "fakeconv": (n or 0) + 1, "cap": 201, "early": (n or 0) + 1,
            "stopped": (n or 0) + 1}.get(kind, 0)


def _s0dec(cell, oc, att, a1=None):
    d = {"attempts": att, "outcome": oc, "repeat": att == 2, "cell": cell,
         "fix_note": "2026-11-21 results/objective2/s2/FR_STEP0_FIX.md" if att == 2 else None}
    if a1:
        d["attempt1"] = dict(a1)
    return d


def _gatefile(gate, res, dec, att):
    return {"schema": "s2-gate-1", "gate": gate, "campaign": "fr", "commit": "e" * 40, "attempt": att,
            "opened": [], "inputs_digest": "4" * 64, "result": res, "decision": dec, "written": "2026-11-21T00:00:00Z",
            "state_in": {"commit": "8" * 40, "K3": "fail_replan"}, "inputs_in": {}, "c1_in": None,
            "F_sp_eV": CANARY["F_eV"]}                       # a withheld canary beside the allowed leaves


def _put_gate(fr, sub, gid, gf, inputs, att):
    base = os.path.join(fr, sub, re.sub(r"[^A-Za-z0-9_.-]", "_", gid))
    _wj(gf, base + ".gate.json"); _wj(inputs, base + ".inputs.json")
    _wj({"schema": "s2-gate-applied-1", "id": gid, "gate": gf["gate"], "rc": 0, "attempt": att,
         "decision": gf["decision"], "gate_file_sha256": "5" * 64, "applied": "2026-11-21T00:00:00Z",
         "F_k0_eV": CANARY["F_eV"]}, base + ".json")


def _ledgers(scen):
    """The C2 ledger (b2 ended C2 and is marked current unless the scenario drops the marks) and the fr ledger (the
    C2 boots, b2 with its tail of 0.75 h, two fr boots and a new manual row), each editable by the scenario."""
    c2b = [{"boot_id": "b1", "btime": 1.0e9, "hours": 40.0, "campaigns": ["c1"], "current": False},
           {"boot_id": "b2", "btime": 1.1e9, "hours": 51.0, "campaigns": ["c2"], "current": True},
           {"btime": 1.2e9, "end_used": 1.2e9 + 3312.0, "hours": 0.92, "manual": True}]
    if scen.get("c2_current", True) is False:
        for b in c2b:
            b.pop("current", None)
    frb = [dict(c2b[0], current=False), dict(c2b[1], hours=51.75, current=False), dict(c2b[2]),
           {"boot_id": "f1", "btime": 1.3e9, "hours": 18.5, "campaigns": ["fr"], "current": False},
           {"boot_id": "f2", "btime": 1.31e9, "hours": 12.25, "campaigns": ["fr"], "current": False},
           {"btime": 1.32e9, "end_used": 1.32e9 + 1800.0, "hours": 0.5, "manual": True}] + \
        [dict(b) for b in scen.get("extra_boots", [])]
    for fn in scen.get("c2_ledger", ()):
        fn(c2b)
    for fn in scen.get("fr_ledger", ()):
        fn(frb)
    return c2b, frb


# the synthetic git repositories of the stop notes (FG-2; IX-6: the one path STOP_NOTE, so each variant of the note
# has a repository of its own): name -> {path: (bytes, how the file is left: committed; committed, then edited in the
# tree; staged only; untracked)}
NOTE_OK = STOP_NOTE
_GOOD = b"2026-11-21: the fr STOP is final (a synthetic stop note).\n"
_DATED = b"# a synthetic note\n\n2026-11-21: the fr STOP is final.\n"
STOP_REPOS = {"ok": {NOTE_OK: (_GOOD, "committed")},
              "crlf": {NOTE_OK: (_GOOD.replace(b"\n", b"\r\n"), "committed")},
              "bytes": {NOTE_OK: (_GOOD + b"\xff\n", "committed")},           # a byte outside UTF-8 (E: replaced)
              "nophrase": {NOTE_OK: (b"2026-11-21: fr stopped; the route is still open.\n", "committed")},
              "nodate": {NOTE_OK: (b"The fr STOP is final.\n", "committed")},
              "edited": {NOTE_OK: (_GOOD, "edited")}, "staged": {NOTE_OK: (_GOOD, "staged")},
              "untracked": {NOTE_OK: (_GOOD, "untracked")}, "absent": {},
              "tree": {f"{NOTE_OK}/2026-11-21 the fr STOP is final.md": (b"a file in a directory named as the note\n",
                                                                          "committed")},
              "others": {NOTE_OK: (_GOOD, "committed"), f"{S2_REL}/S2B_PLAN.md": (_DATED, "committed"),
                         f"{S2_REL}/FR_OPERATIONS.md": (_DATED, "committed"),
                         f"{S2_REL}/FR_STOP_NOTE_2.md": (_DATED, "committed"),
                         f"{S2_REL}/s2b/FR_STOP_NOTE.md": (_DATED, "committed"), "FR_STOP_NOTE.md": (_DATED,
                                                                                                    "committed")}}
# each stop note given to the build: (repository, path, the need() key that refuses it; None: accepted); the self-test
# checks these verdicts, and the sha256 of each accepted note, against e_eval.py's own tests on the same repository
STOP_CASES = (("ok", NOTE_OK, None), ("crlf", NOTE_OK, None), ("bytes", NOTE_OK, None),
              ("nophrase", NOTE_OK, "stop note: text"), ("nodate", NOTE_OK, "stop note: text"),
              ("edited", NOTE_OK, "stop note: committed and clean"),
              ("staged", NOTE_OK, "stop note: committed and clean"),
              ("untracked", NOTE_OK, "stop note: committed and clean"),
              ("absent", NOTE_OK, "stop note: committed and clean"),
              ("tree", NOTE_OK, "stop note: HEAD"),                       # a tree of HEAD: git cat-file -t is 'tree'
              ("others", NOTE_OK, None),
              ("others", f"{S2_REL}/S2B_PLAN.md", "stop note: fixed path"),
              ("others", f"{S2_REL}/FR_OPERATIONS.md", "stop note: fixed path"),
              ("others", f"{S2_REL}/FR_STOP_NOTE_2.md", "stop note: fixed path"),
              ("others", f"{S2_REL}/s2b/FR_STOP_NOTE.md", "stop note: fixed path"),
              ("others", "FR_STOP_NOTE.md", "stop note: fixed path"),
              ("others", f"{S2_REL}/FR_STOP_NO*.md", "stop note: fixed path"),      # a glob (git show: the commit)
              ("others", ":(literal)" + NOTE_OK, "stop note: fixed path"),           # a pathspec
              ("others", "./" + NOTE_OK, "stop note: path"), ("others", "/" + NOTE_OK, "stop note: path"),
              ("others", NOTE_OK.replace("/s2/", "/s2//"), "stop note: path"),
              ("others", NOTE_OK.replace("/s2/", "/s2/../s2/"), "stop note: path"))


def _stop_repos(d):
    """The synthetic git repositories of STOP_REPOS under d, each file left as its entry says, and beside them a
    folder whose .git names no repository (git fails there). Returns ({name: path}, that folder). Git writes them
    without the global and system configuration."""
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    env.update({f"GIT_{w}_{x}": "selftest" for w in ("AUTHOR", "COMMITTER") for x in ("NAME", "EMAIL")})
    repos = {}
    for name, files in STOP_REPOS.items():
        r = repos[name] = os.path.join(d, name)
        git = lambda *a: subprocess.run(["git", "-C", r, *a], env=env, check=True, capture_output=True)

        def put(rel, b):
            os.makedirs(os.path.dirname(os.path.join(r, rel)), exist_ok=True)
            with open(os.path.join(r, rel), "wb") as fh:
                fh.write(b)
        os.makedirs(r)
        git("init", "-q")
        git("config", "core.fsmonitor", "false")
        put("README", b"synthetic\n")
        git("add", "--", "README")
        for rel, (b, how) in files.items():
            if how in ("committed", "edited"):
                put(rel, b)
                git("add", "--", rel)
        git("commit", "-q", "--no-verify", "-m", "synthetic stop notes")
        for rel, (b, how) in files.items():
            if how != "committed":
                put(rel, b + (b"edited in the tree\n" if how == "edited" else b""))
            if how == "staged":
                git("add", "--", rel)
    nogit = os.path.join(d, "nogit")
    os.makedirs(nogit)
    with open(os.path.join(nogit, ".git"), "w") as fh:
        fh.write("gitdir: no-repository\n")
    return repos, nogit


def _e_eval():
    """e_eval.py of this tree, loaded under a private name; its setting of sys.pycache_prefix (which guards E's own
    runs) is undone for this process, which writes no bytecode."""
    prefix = sys.pycache_prefix
    try:
        return _load("e_eval_fig_s2b_fr", os.path.join(S2, "s2b", "e_eval.py"))
    finally:
        sys.pycache_prefix = prefix


def _note_verdicts(ee, repos):
    """For each note of STOP_CASES: (repository, path, the need() key the figure refuses it with, the figure's sha256,
    E's sha256), None for a refusal; E's verdict is e_eval.Run.note_ok, then e_eval.stop_note_ok, on the same
    repository (an EError is a refusal)."""
    import types
    out = []
    for rn, p, _ in STOP_CASES:
        try:
            fk, fs = None, stop_note(repos[rn], p)["sha256"]
        except AssertionError as e:
            fk, fs = re.match(r"\[(.+?)\]", str(e))[1], None
        try:
            t = ee.Run.note_ok(types.SimpleNamespace(git=ee.Git(repos[rn])), p, what="--stop-note")
            es = hashlib.sha256(t.encode()).hexdigest() if ee.stop_note_ok(p, t) else None
        except ee.EError:
            es = None
        out.append((rn, p, fk, fs, es))
    return out


def _pin_e_eval(ee, repos):
    """FG-2, IX-6: the figure's stop-note rule is E's. STOP_NOTE, STOP_PHRASE, ISO_DATE and S2_REL equal those of
    e_eval.py; stop_note_ok gives E's answer on a table of paths and texts; and on the notes of the synthetic
    repositories the figure refuses (with the key STOP_CASES names) or accepts (with E's sha256, that of the HEAD text
    as UTF-8 with replacement: an LF, a CRLF and a non-UTF-8 note) exactly where E does."""
    assert (S2_REL, STOP_NOTE, STOP_PHRASE.pattern, STOP_PHRASE.flags, ISO_DATE.pattern, ISO_DATE.flags) == \
        (ee.S2_REL, ee.STOP_NOTE, ee.STOP_PHRASE.pattern, ee.STOP_PHRASE.flags, ee.ISO_DATE.pattern,
         ee.ISO_DATE.flags), "pin: the stop-note constants differ from e_eval.py"
    paths = (NOTE_OK, f"{S2_REL}/sub/FR_STOP.md", f"{S2_REL}/s2b/FR_STOP.md", f"{S2_REL}/s2bx/FR_STOP.md",
             f"{S2_REL}x/FR_STOP.md", "FR_STOP.md", f"{S2_REL}/S2B_PLAN.md", f"{S2_REL}/FR_STOP_NO*.md")
    texts = ("2026-11-21: the fr STOP is final", "the fr STOP is final", "2026-11-21: The FR stop is final.",
             "1999-11-21: the fr STOP is final", "2026-11-21x: the fr STOP is final",
             "2026-11-21: the fr  STOP is final", "2026-11-21", "")
    for p in paths:
        for t in texts:
            assert stop_note_ok(p, t) == ee.stop_note_ok(p, t), ("pin: stop_note_ok differs from e_eval.py", p, t)
    v = _note_verdicts(ee, repos)
    assert [(rn, p, fk) for rn, p, fk, _, _ in v] == list(STOP_CASES) and all(fs == es for _, _, _, fs, es in v), \
        ("pin: the stop-note verdicts differ from e_eval.py (Run.note_ok, stop_note_ok)", v)


def _e_reason_src(src=None):
    """IX-16: E's reason words and reason code from the source of s2b/e_eval.py (src: that text), loaded with ast:
    FR_REASON (ast.literal_eval) and the functions fr_reason, checks_str and S compiled into one namespace, with ABSENT
    and FILE_ABSENT as fresh sentinels."""
    path = os.path.join(S2, "s2b", "e_eval.py")
    if src is None:
        with open(path) as fh:
            src = fh.read()
    tree = ast.parse(src, path)
    asg = [n for n in tree.body if isinstance(n, ast.Assign) and [getattr(x, "id", None) for x in n.targets] ==
           ["FR_REASON"]]
    fns = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("fr_reason", "checks_str", "S")]
    assert len(asg) == 1 and sorted(f.name for f in fns) == ["S", "checks_str", "fr_reason"], \
        "s2b/e_eval.py: FR_REASON, fr_reason, checks_str or S not found"
    ns = {"ABSENT": object(), "FILE_ABSENT": object(), "FR_REASON": ast.literal_eval(asg[0].value)}
    exec(compile(ast.Module(body=fns, type_ignores=[]), path, "exec"), ns)
    return ns


def _pin_e_reason(ns, M):
    """IX-4, IX-16: the reason FR's state names after a final STOP is E's, pinned against E's source (ns:
    _e_reason_src). E_REASON is E's FR_REASON (its kinds with a fixed word), and e_reason gives E's fr_reason text on
    the leaves of a record: a check with one and with two failed checks and with none recorded, an end rule and none
    recorded, every fixed word, and a kind without one."""
    assert E_REASON == {k: v for k, v in ns["FR_REASON"].items() if v is not None}, \
        ("pin: E_REASON differs from e_eval.FR_REASON", E_REASON)
    gs, A = M["guard"].GuardedS2b, ns["ABSENT"]
    rows = [("check", {"validity_final": {"failed": [5]}}, [5], A), ("check", {"validity_final": {"failed": [4, 5]}},
                                                                      [4, 5], A),
            ("check", {"validity_final": {}}, A, A), ("check", None, A, A),
            ("end_rule", {"end_rule": {"outcome": "unconverged_early"}}, A, "unconverged_early"),
            ("end_rule", {}, A, A), ("other_kind", {}, A, A)] + [(k, {}, A, A) for k in sorted(E_REASON)]
    for kind, d, failed, outcome in rows:
        rec = None if d is None else gs(d, "t")
        assert e_reason(kind, rec) == ns["fr_reason"](kind, failed, outcome), \
            ("pin: e_reason differs from e_eval.fr_reason", kind, d, e_reason(kind, rec))


def _e_admit(ee, cj, fr):
    """Integration review 2: E's route_admit (phase 0a) on the leaves cj of fr/campaign.json and the archive's fr
    folder fr (IX-15: its gate files by name), a stopped fr's stop note taken as valid (the note rules are pinned
    apart, _pin_e_eval). Returns E's fr dict (start, commit, era, repeat); an E refusal raises e_eval.EError."""
    import types

    class Run:
        route_admit = ee.Run.route_admit
    r = Run()
    r.L = types.SimpleNamespace(cdir=lambda c: fr if c == "fr" else None)
    r.a = types.SimpleNamespace(stop_note=STOP_NOTE if cj.get("status") == "stopped" else None)
    r.fr, r.pre_route, r.b4 = {}, [], None
    r.load = lambda *a: cj
    r.note_ok = lambda path, what=None: "2026-11-21: the fr STOP is final (synthetic)"
    r.route_admit()
    return r.fr


def _e_cj(ee, camp):
    """The leaves of fr/campaign.json that E's route code reads (amendment item 2), as E's guard gives them: ABSENT
    for a missing leaf; commit_history[].to as a list."""
    class Leaves(dict):
        def get(self, k, default=None):
            return dict.get(self, k, ee.ABSENT)
    cj = Leaves({k: camp.get(k) for k in ("status", "fr_outcome", "stop_reason", "start_commit", "commit")
                 if camp.has(k)})
    if camp.has("commit_history"):
        cj["commit_history[].to"] = [h.get("to") for h in camp.get("commit_history")]
    return cj


class _ByName:
    """The names under one folder as E's route_fr tests them ('<name> in names'), each by its existence only: the
    folder is never listed or opened (step0_attempt1/, operations note D-C2-2)."""

    def __init__(self, d):
        self.d = d

    def __contains__(self, name):
        return os.path.exists(os.path.join(self.d, name))


def _e_aside_src(src=None):
    """Integration review 3 (IX-11 at both cells): E's set-aside rule from the source of s2b/e_eval.py (src: that
    text), loaded with ast and compiled: in Run.route_fr the value assigned to fr["aside_named"] (the attempt-1 markers
    by name); in Run.block2 the list 'aside' and the tests of the if/elif that print the step-0 repeat row (a repeat
    recorded by fr/STEP0_FIX, else 'prepared, not recorded' for the gates in 'aside')."""
    path = os.path.join(S2, "s2b", "e_eval.py")
    if src is None:
        with open(path) as fh:
            src = fh.read()
    run = [n for n in ast.parse(src, path).body if isinstance(n, ast.ClassDef) and n.name == "Run"]
    fn = {n.name: n for n in (run[0].body if len(run) == 1 else []) if isinstance(n, ast.FunctionDef)}
    named = [n for n in ast.walk(fn["route_fr"]) if isinstance(n, ast.Assign) and len(n.targets) == 1 and
             isinstance(n.targets[0], ast.Subscript) and isinstance(n.targets[0].slice, ast.Constant) and
             n.targets[0].slice.value == "aside_named"] if "route_fr" in fn else []
    aside = [n for n in ast.walk(fn["block2"]) if isinstance(n, ast.Assign) and [getattr(t, "id", None) for t in
                                                                               n.targets] == ["aside"]] \
        if "block2" in fn else []
    rows = [n for n in ast.walk(fn["block2"]) if isinstance(n, ast.If) and len(n.orelse) == 1 and
            isinstance(n.orelse[0], ast.If) and any(isinstance(c, ast.Constant) and c.value == "B2.step0.repeat"
                                                    for c in ast.walk(n))] if "block2" in fn else []
    assert len(named) == 1 and len(aside) == 1 and len(rows) == 1, \
        "s2b/e_eval.py: Run.route_fr's aside_named or Run.block2's step-0 repeat rows not found"
    ex = lambda node: compile(ast.Expression(node), path, "eval")
    return {"named": ex(named[0].value), "aside": ex(aside[0].value), "recorded": ex(rows[0].test),
            "unrecorded": ex(rows[0].orelse[0].test)}


def _e_route(ee, root, M):
    """IX-4, IX-5: E's own route code (e_eval.Run.rf12_step0, stop_decision, header_fr_part and decided_part) on the
    leaves of this synthetic archive, read through the guard by the names E lists (amendment item 2; an absent leaf is
    E's ABSENT, an absent file its FILE_ABSENT, the set-aside marker by its name only). Returns E's header FR part,
    E's s0_set_aside and the gates of E's 'prepared, not recorded' row (integration review 3: E's set-aside rule from
    E's source, _e_aside_src)."""
    gd, A, FA, rule = M["guard"], ee.ABSENT, ee.FILE_ABSENT, _e_aside_src()
    fr = os.path.join(root, "fr")
    stem = lambda gid: re.sub(r"[^A-Za-z0-9_.-]", "_", gid)

    class Leaves(dict):                               # E's listed leaves: ABSENT for a missing one
        def get(self, k, default=None):
            return dict.get(self, k, A)
    camp = gd.guarded_s2b(os.path.join(fr, "campaign.json"))
    cj = _e_cj(ee, camp)
    adm = _e_admit(ee, cj, fr)                        # integration review 2: E admits the route (no refusal)
    cells = {}
    for lab in FR_LABELS:
        r = gd.guarded_s2b(os.path.join(fr, "raw", f"{lab}.a2.json"))
        if r is None:
            cells[lab] = {"status": FA}
            continue
        vf, er_ = r.get("validity_final"), r.get("end_rule")
        cells[lab] = Leaves({"status": r.get("status"),
                             **({"n_config": r.get("n_config")} if r.has("n_config") else {}),
                             **({"validity_final.failed": vf.get("failed")} if vf is not None else {}),
                             **({"end_rule.outcome": er_.get("outcome")} if er_ is not None else {})})
    s0 = {}
    for name, gid in GATES[:2]:
        at, mk = name[-2:], os.path.join(fr, "gates_applied", stem(gid) + ".json")
        m = gd.gate_leaves(mk) if os.path.exists(mk) else None
        c = gd.gate_leaves(mk[:-5] + ".gate.json") if os.path.exists(mk[:-5] + ".gate.json") else None
        s0[at] = {"a2": STEP0_AT[name][1], "marker": FA if m is None else m, "copy": FA if c is None else c}
        if m is not None:
            d = m.get("decision.fr_step0")
            s0[at]["dec"] = {"decision.fr_step0.outcome": d.get("outcome"), "decision.fr_step0.attempts":
                             d.get("attempts")}
    gp = os.path.join(fr, "gates", "FR.json")
    gfr = gd.gate_leaves(gp) if os.path.exists(gp) else None
    dec = gfr.get("decision.FR") if gfr is not None else None
    v = {"cj": cj, "status": camp.get("status"), "cells": cells, "s0": s0, "s0_ran": [a for a in ("@2", "@4") if
                                                                                      s0[a]["marker"] is not FA],
         "s0_last": FA if not os.path.exists(os.path.join(fr, "gates", "fr_step0.json")) else "present",
         "aside_named": eval(rule["named"], {"eg": ee.eg, "names": _ByName(os.path.join(fr, "step0_attempt1",
                                                                                         "gates_applied"))}),
         "dec": dict(dec) if isinstance(dec, dict) else None, "frg": {"gates/FR.json": FA if gfr is None else gfr},
         "outcome": camp.get("fr_outcome"), "repeat": adm["repeat"]}

    class Run:                                        # E's methods, on these leaves
        rf12_step0, stop_decision, header_fr_part, decided_part = (ee.Run.rf12_step0, ee.Run.stop_decision,
                                                                   ee.Run.header_fr_part, ee.Run.decided_part)
    r = Run()
    r.fr, r.chk, r.pre_route = v, ee.eg.Checks(), []
    r.rf12_step0()
    if v["status"] == "stopped":
        v["stop_rec"] = r.stop_decision()
    # E's block-2 rows (e_eval.Run block 2, 2.2), by E's own rule: a repeat recorded by fr/STEP0_FIX, else 'prepared,
    # not recorded' for each step-0 gate whose attempt-1 marker is named under step0_attempt1/
    aside = eval(rule["aside"], {"fr": v})
    unrec = [] if eval(rule["recorded"], {"fr": v}) else aside if eval(rule["unrecorded"], {"aside": aside}) else []
    return r.header_fr_part(), v["s0_set_aside"], unrec


def _pin_e_route(ee, root, M, gates, nm):
    """IX-4 and IX-5, the figure against E on the same stopped archive: with a decision recorded before the STOP, FR's
    state is E's header FR part, each FR label written as its cell name and 'S2B §1' as 'S2B section 1' (the same
    decision, cell, reason and STOP); without one, E names the first FR cell not complete and the figure draws 'not
    reached (after a final STOP)'; the step-0 row at @4 reads 'repeat prepared, not recorded' exactly where E's
    s0_set_aside holds; and (integration review 2) each step-0 row reads so exactly where E prints its 'step-0 repeat
    prepared, not recorded' row for that gate (at @2 too; integration review 3: by E's rule, compiled from E's source).
    E's route_admit admits every such archive."""
    part, aside, unrec = _e_route(ee, root, M)
    st, d4 = gates[2]["state"], gates[1]["detail"]
    if "; then a final STOP (" in st:
        assert st == short(part).replace("(S2B §1)", "(S2B section 1)"), (nm, "pin: FR against E's header", st, part)
    else:
        assert part.startswith("stopped at ") and st == "not reached (after a final STOP)", (nm, "pin: FR", st, part)
    assert aside == d4.startswith("repeat prepared, not recorded"), (nm, "pin: E's s0_set_aside", aside, d4)
    for (name, _), g in zip(GATES[:2], gates[:2]):
        assert (name[-2:] in unrec) == g["detail"].startswith("repeat prepared, not recorded"), \
            (nm, "pin: E's 'prepared, not recorded' rows", name, unrec, g["detail"])
    return part


def _synthetic(root, scen, wp, M):
    """One synthetic archive in the scripts/50 archive layout: c1 (smoke mapping, the real region file, start
    records), c2/ledger.json, the verify record, and fr (parts, records, gate files and markers, the A2 stop state,
    campaign.json, completeness, ledger, log, the hard-cap refusal and the attempt-1 canary when the scenario has them).
    Every guarded fr JSON file holds a withheld canary field beside the fields the build reads."""
    g49, q47 = M["g49"], M["q47"]
    c1, fr = os.path.join(root, "c1"), os.path.join(root, "fr")
    raw = os.path.join(fr, "raw")
    _wj({"mapping": json.load(open(os.path.join(S2, "c1", "smoke.json")))["mapping"]}, os.path.join(c1, "smoke.json"))
    region = json.load(open(os.path.join(S2, "c1", "regions", f"{REGION}.json")))     # public; geometry only
    _wj(region, os.path.join(c1, "regions", f"{REGION}.json"))
    fsets = _free_sets(region)
    for lab, rl in zip(FR_LABELS, FR_ROLES):
        if rl != "host":
            fs = fsets[rl]
            _wj({"work_id": g49.a1_start_of(lab), "n_free": len(fs), "n_fixed": 234 - len(fs), "free": fs,
                 "relax": {"E_mace_eV": CANARY["E_mace_eV"]}},
                os.path.join(c1, "records", f"{g49.a1_start_of(lab)}.json"))
    os.makedirs(os.path.join(root, VERIFY[0]), exist_ok=True)
    open(os.path.join(root, *VERIFY), "w").write("synthetic verify record (equal or differ lines only)\n")
    done = scen.get("status", "done") == "done"
    rerun = scen.get("rerun")                          # (cell, gate) whose step-0 failed at attempt 1, or None
    t, recs = {}, {}
    for order, (lab, rl) in enumerate(zip(FR_LABELS, FR_ROLES), 1):
        spec = scen["relax"].get(lab)
        if spec is None:
            continue
        kind, n, splits, status, outcome = spec
        rec = {"schema": "s2-a2-1", "label": lab, "campaign": "fr", "order": order,
               "a1_cell": {"work_id": g49.a1_start_of(lab)}, "layout": None, "parts": [], "restarts": 0,
               "reruns_from_zero": 0, "interruptions": [], "status": status, "F_final_eV": CANARY["F_eV"]}
        if status == "not_run_gate":
            rec["status_reason"] = "FR early stop (S2B section 2)"
        k_last = None
        if kind is not None:
            rec.update(layout={"name": "64", "ranks": 64, "copies": 1})
        if kind == "inonly":                                     # a prepared part that never ran, or one killed
            with gzip.open(os.path.join(raw, f"{lab}.p1.in.gz"), "wt", compresslevel=1) as fh:
                fh.write(_input(wp, fsets[rl]))
            rec["parts"] = [{"n": 1}]
            if status == "killed_by_gate":
                rec["k0_seen"] = True
        elif kind is not None:
            os.makedirs(raw, exist_ok=True)
            for j, txt in enumerate(wp.parts(lab, kind, n, splits), 1):
                with gzip.open(os.path.join(raw, f"{lab}.p{j}.out.gz"), "wt", compresslevel=1) as fh:
                    fh.write(_blind_part(txt))                   # no WP2e energy: the part-energy canary
                with gzip.open(os.path.join(raw, f"{lab}.p{j}.in.gz"), "wt", compresslevel=1) as fh:
                    fh.write(_input(wp, fsets[rl]))
            rec.update(parts=[{"n": j} for j in range(1, len(splits) + 2)], restarts=len(splits))
            k_last = {"cap": q47.K_CAP, "scf0": None, "dead": splits[-1] - 1 if splits else None}.get(kind, n)
        nc = 0 if k_last is None else k_last + 1
        if nc or lab in scen.get("k0_seen", ()):
            rec["k0_seen"] = True
        if status == "complete":
            wall = max(nc, 1) * RATE_SYN[rl] * 60.0                     # scripts/50: min_per_config = wall / max(1, n)
            conv = kind in ("conv", "fakeconv")
            rec.update(n_config=nc, k_last=k_last, converged_at_k=n if conv else None, qe_converged=conv,
                       wall_h=wall / 3600.0, min_per_config=wall / 60.0 / max(1, nc),
                       end_rule={"outcome": outcome, "dF_200_180_meV": CANARY["dF_200_180_meV"],
                                 "end": {"early": "bfgs_failed", "scf0": "scf_failed"}.get(kind), "stop": False,
                                 "reason": None})
            if k_last is not None and lab not in scen.get("no_validity", ()):
                v = scen.get("valid", {}).get(lab, {})
                inv = bool(v.get("invariant_only"))
                failed = list(v.get("failed", []))
                rec["final_geometry"] = {"file": f"{lab}.final.extxyz", "k": k_last, "sha256": "1" * 64}
                rec["validity_final"] = {"valid": not failed, "failed": failed, "file": f"{lab}.validity_final.json",
                                         "sha256": "2" * 64, "parent": None, "parent_final": True,
                                         "check5_reading": "invariant", "valid_as_written": not failed and not inv,
                                         "failed_as_written": failed or ([5] if inv else []), "invariant_only": inv}
        for fn in scen.get("rec_edit", {}).get(lab, ()):                # a record shape the runner writes otherwise
            fn(rec)
        _wj(rec, os.path.join(raw, f"{lab}.a2.json"))
        recs[lab] = rec
        vf = rec.get("validity_final")
        vkeys = ("valid", "failed", "check5_reading", "valid_as_written", "failed_as_written", "invariant_only")
        t[lab] = {"status": status, "end_rule": (rec.get("end_rule") or {}).get("outcome"), "a1_valid": True,
                  "validity_final": None if vf is None else {k: vf[k] for k in vkeys}}
    # step-0 gates, in the graph order; attempt-1 files of a repeat go under step0_attempt1/ (the canary)
    a1 = None
    if rerun:
        a1 = {"attempts": 1, "outcome": "fail_pending_fix", "cell": rerun[0]}
        sp = {c: s for s, c in STEP0_AT.values()}[rerun[0]]
        gf = _gatefile("fr_step0", {"cells": {sp: {"dF_meV": CANARY["dF_meV"], "passed": False, "reason": None}},
                                    "attempt": 1, "fix_note": None, "outcome": "fail_pending_fix",
                                    "tolerance_meV": 0.5},
                       {"fr_step0": _s0dec(rerun[0], "fail_pending_fix", 1)}, 1)
        a1d = os.path.join(fr, "step0_attempt1")
        _put_gate(a1d, "gates_applied", dict(GATES)[rerun[1]], gf, {"cells": [sp], "attempt": 1}, 1)
        _wj(gf, os.path.join(a1d, "gates", "fr_step0.json"))
        for dp, _, fns in os.walk(a1d):
            for f in fns:
                os.chmod(os.path.join(dp, f), 0)           # a second canary layer: these files cannot be read
    prev, last = {}, None
    for name, gid in GATES[:2]:
        sp, cell = STEP0_AT[name]
        if name not in scen.get("s0", {}):
            continue
        oc = scen["s0"][name]
        att = 2 if rerun and FR_LABELS.index(cell) >= FR_LABELS.index(rerun[0]) else 1
        dec = {**prev, **_s0dec(cell, oc, att, a1 if att == 2 else None)}
        ok = oc == "pass"
        gf = _gatefile("fr_step0", {"cells": {sp: {"dF_meV": CANARY["dF_meV"], "passed": ok, "reason": None}},
                                    "attempt": att, "fix_note": dec["fix_note"], "outcome": oc, "tolerance_meV": 0.5},
                       {"fr_step0": dec}, att)
        _put_gate(fr, "gates_applied", gid, gf, {"cells": [sp], "attempt": att}, att)
        _wj(gf, os.path.join(fr, "gates", "fr_step0.json"))
        prev, last = dec, dec
    rows = [{"label": lab, "status": t.get(lab, {}).get("status"), "end_rule": t.get(lab, {}).get("end_rule"),
             "check": "done" if t.get(lab, {}).get("validity_final") else      # a2v_status: nothing to check
             "skipped" if t.get(lab, {}).get("status") in TERMINAL else None,
             "valid": None if not t.get(lab, {}).get("validity_final") else t[lab]["validity_final"]["valid"]}
            for lab in FR_LABELS]
    ff = g49.fr_progress(rows)["first_failure"] if all(r["status"] for r in rows) or not done else None
    noerr = scen.get("no_error", False)
    s0_final = noerr or (last is not None and last["outcome"] == "fail_final")
    fr_dec = None
    if (done or scen.get("gate_fr")) and not s0_final:     # gate_fr: applied before a STOP (IX-4; scripts/50 N-F20)
        res = g49.fr_eval(t)
        fr2 = scen.get("fr2", True) if res["FR1"] else None
        res["FR2"] = None if fr2 is None else {"Eb_A1_meV": CANARY["Eb_A1_meV"], "Eb_A2_meV": CANARY["Eb_A2_meV"],
                                               "delta_far_meV": CANARY["delta_far_meV"], "bound_meV": 50.0,
                                               "passed": fr2}
        f1 = res["first_failure"]
        ok = res["FR1"] and fr2 is True
        fr_dec = {"outcome": "pass" if ok else "fail", "FR1": res["FR1"], "FR2": fr2,
                  "part": None if ok else ("FR-1" if not res["FR1"] else "FR-2"),
                  "cell": f1["cell"] if f1 else None, "kind": f1["kind"] if f1 else None}
        gf = _gatefile("FR", res, {"FR": fr_dec}, 1)
        _put_gate(fr, "gates_applied", "gate:FR", gf, {}, 1)
        _wj(gf, os.path.join(fr, "gates", "FR.json"))
    recorded = rerun and scen.get("recorded", True)   # IX-5: False, the move made and the STEP0_FIX save not
    hist = [{"from": "8" * 40, "to": "e" * 40, "via": "fr/CAMPAIGN_COMMIT"}] + \
        ([{"from": "e" * 40, "to": "f" * 40, "via": "fr/STEP0_FIX"}] if recorded else [])
    camp = {"schema": "s2-campaign-1", "campaign": "fr", "status": "done" if done else "stopped", "commit": "e" * 40,
            "start_commit": "e" * 40, "commit_history": hist, "phases": {}, "Eb_A1_meV": CANARY["Eb_A1_meV"]}
    if not done:                                      # scripts/50 begin_stop: the reason, and the fr_outcome the
        fo_stop = FR_OUTCOMES[3] if s0_final else None if fr_dec is None else FR_OUTCOMES[0] if \
            fr_dec["outcome"] == "pass" else f"fail ({fr_dec['part']})"            # decisions fix, else null (IX-4)
        camp.update(stop_reason=scen.get("stop_reason", "operator final STOP (synthetic)"),
                    fr_outcome=scen.get("fr_outcome_stop", fo_stop))
    log = [f"[2026-11-21T00:00:00Z] FR step-0 repeat prepared: {rerun[0]}: 5 of its 5 attempt-1 paths moved to "
           f"discarded/step0_attempt1_1763683200; {rerun[0]} reruns from k = 0 (attempt 2)"] if recorded else []
    nl = scen.get("noerr_log", "first") if noerr else None             # which STEP0_NO_ERROR line the log holds
    if nl == "first":
        log.append("[2026-11-21T02:00:00Z] fr/STEP0_NO_ERROR: FR step-0 fail_final (no error found); FR ends as 'fail "
                   "(step-0 final; gate not evaluated)' (S2B section 2, X6)")
    if nl == "leftover":                                # the route applied at a start cut short before its log line
        log.append("[2026-11-21T03:00:00Z] fr/STEP0_NO_ERROR: the applied route's leftover renamed .used, no state "
                   "change (N-FR6); FR step-0 fail_final since an earlier start")
    if done:
        camp["fr_outcome"] = FR_OUTCOMES[3] if s0_final else FR_OUTCOMES[0] if fr_dec["outcome"] == "pass" else \
            f"fail ({fr_dec['part']})"
        s0 = dict(last) if last else None
        if rerun and (last is None or last["cell"] != rerun[0] and FR_LABELS.index(last["cell"]) <
                      FR_LABELS.index(rerun[0])):
            s0 = {**(last or {}), "outcome": "repeat_pending", "repeat": True, "cell": rerun[0], "attempt1": a1,
                  "fix_note": "2026-11-21 results/objective2/s2/FR_STEP0_FIX.md", "attempts": 1}
        if noerr:
            s0.update(outcome="fail_final", no_error_found=True, note="2026-11-21: no writer or input error found")
        state = {"commit": "8" * 40, "campaign_commit": {"fr": "e" * 40}, "campaigns": {"c1": "done", "c2": "done",
                                                                                     "c3": "not_run", "fr": "done"},
                 "delta_far_meV": CANARY["delta_far_meV"]}
        if s0:
            state["fr_step0"] = s0
        if ff:
            state["fr_stop"] = {"at": ff["cell"], "kind": ff["kind"], "time": "2026-11-21T01:00:00Z"}
        if fr_dec:
            state["FR"] = fr_dec
        _wj(state, os.path.join(fr, "state_end.json"))
        jobs = {gid: "done" if os.path.exists(os.path.join(fr, "gates_applied", re.sub(r"[^A-Za-z0-9_.-]", "_", gid)
                                                           + ".json")) else "skipped" for _, gid in GATES}
        jobs.update({"a2:" + lab: JOB_STATUS[r["status"]] for lab, r in recs.items()})
        _wj({"schema": "s2-completeness-1", "campaign": "fr", "jobs": jobs, "by_category": {},
             "Eb_A2_meV": CANARY["Eb_A2_meV"]}, os.path.join(fr, "completeness.json"))
    _wj(camp, os.path.join(fr, "campaign.json"))
    os.makedirs(os.path.join(fr, "logs"), exist_ok=True)
    open(os.path.join(fr, "logs", "campaign.log"), "w").write("".join(x + "\n" for x in log))
    if "hard_cap" in scen:
        _wj({"schema": "s2-hardcap-1", "job": scen["hard_cap"], "dF_meV": CANARY["dF_meV"]},
            os.path.join(fr, "HARD_CAP.json"))
    c2b, frb = _ledgers(scen)
    _wj({"schema": "s2-ledger-1", "boots": c2b, "H_spent_h": sum(b["hours"] or 0.0 for b in c2b), "complete": True,
         "problems": [], "now_utc": "2026-11-12T00:00:00Z"}, os.path.join(root, "c2", "ledger.json"))
    probs = ["boot x: no btime or no heartbeat" for b in frb if b.get("hours") is None]
    _wj({"schema": "s2-ledger-1", "boots": frb, "H_spent_h": sum(b["hours"] or 0.0 for b in frb),
         "complete": not probs, "problems": probs, "now_utc": "2026-11-21T06:00:00Z",
         "value_meV": CANARY["delta_far_meV"]}, os.path.join(fr, "ledger.json"))
    for fn in scen.get("mutate", ()):
        fn(root)


def _scenarios(M):
    """The synthetic archives: relaxations, step-0 and FR decisions, and the expected (state, detail) of each gate,
    with the early-stop band (6-29) where Cs D(A188) never started."""
    H, V, D, DV = FR_LABELS
    conv = lambda n, sp=(): ("conv", n, list(sp), "complete", "accepted_converged")
    NR, KILL, CAPREF = (None, None, [], "not_run_gate", None), ("inonly", None, [], "killed_by_gate", None), \
        (None, None, [], "not_started_cap", None)
    plat, capu = ("cap", None, [], "complete", "accepted_plateau"), ("cap", None, [], "complete", "unconverged_cap")
    nr = ("not reached", "")
    a1 = ("pass", "attempt 1")
    rep = lambda c: f"attempt 2, after STEP0_FIX (attempt 1 at {c}: fail_pending_fix; its files are not opened)"
    prep = "attempt 2 after STEP0_FIX not evaluated (attempt 1 at V: fail_pending_fix; its files are not opened)"
    fin = f"; the STOP is final by the stop note {NOTE_OK}"             # every stopped scenario names NOTE_OK (FG-2)
    stop = ("not reached (after a final STOP)", "a final STOP in fr: FR fails (S2B section 1, route table)" + fin)
    s0f = ("fail (step-0 final; gate not evaluated)",
           "FR is not evaluated after a final step-0 failure (S2B section 2)")
    then = "; then a final STOP (operator final STOP (synthetic))"      # IX-4: the decision recorded, then the STOP
    s0f_stop = (s0f[0] + then, s0f[1] + fin)
    pend = ("fail (fail_pending_fix)", "attempt 1; neither fr/STEP0_FIX nor fr/STEP0_NO_ERROR before the final STOP")
    frp = "FR-1 and FR-2 passed (|δ_far| ≤ 50 meV)"
    inv = lambda cells: f"check 5 passed only under the identical-atom reading at {cells}"
    small = {H: conv(12, [6]), V: conv(10), D: conv(8), DV: conv(9)}
    b0 = {"boot_id": "b0", "btime": 1.05e9, "hours": 10.0, "campaigns": ["c2"]}   # an earlier C2 boot
    return {
        "pass": {"relax": {H: conv(70, [30]), V: conv(60), D: plat, DV: conv(90, [50])},
                 "valid": {V: {"invariant_only": True}, D: {"invariant_only": True}},
                 "s0": {"fr_step0@2": "pass", "fr_step0@4": "pass"},
                 "expect": {"fr_step0@2": a1, "fr_step0@4": a1, "FR": ("pass", frp + "; " + inv("V, D"))}},
        # V+_R rerun from k = 0 after a node loss (scripts/50 a2_rerun: reruns_from_zero + 1, parts reset, restarts
        # kept, one interruption), then one restart; the C2 ledger has two C2 boots and marks none current: the later
        # one ended C2 and carries the tail
        "rerun_k0": {"relax": {H: conv(50), V: conv(40, [20]), D: conv(45), DV: conv(55)},
                     "rec_edit": {V: [lambda rec: rec.update(reruns_from_zero=1, restarts=2, interruptions=[{
                         "k": 12, "time": "2026-11-21T00:30:00Z", "boot": "f1", "cause": "node-loss", "part": 1}])]},
                     "fields": {V: {"restarts": 2, "reruns_from_zero": 1, "interruptions": 1}},
                     "s0": {"fr_step0@2": "pass", "fr_step0@4": "pass"}, "c2_current": False,
                     "c2_ledger": [lambda c2b: c2b.append(dict(b0))], "extra_boots": [b0],
                     "cost": {**DEFAULT_COST, "H_spent_h": 133.92, "H_spent_c2_ledger_h": 101.92},
                     "expect": {"fr_step0@2": a1, "fr_step0@4": a1, "FR": ("pass", frp)}},
        "fr1_host_cap": {"relax": {H: capu, V: NR, D: NR, DV: NR}, "early": True,
                         "expect": {"fr_step0@2": nr, "fr_step0@4": nr, "FR": (
                             "fail (FR-1): host, end rule",
                             "host: end rule unconverged_cap (status complete); not run: V, D, D+V")}},
        "fr1_check5": {"relax": {H: conv(50), V: conv(40), D: NR, DV: NR},
                       "valid": {H: {"invariant_only": True}, V: {"failed": [5]}},
                       "s0": {"fr_step0@2": "pass"}, "early": True,
                       "expect": {"fr_step0@2": a1, "fr_step0@4": nr, "FR": (
                           "fail (FR-1): V, check", "V: final geometry fails check(s) [5]; not run: D, D+V; " + inv(
                               "host"))}},
        "fr1_early_D": {"relax": {H: conv(50), V: conv(40), D: ("early", 80, [], "complete", "unconverged_early"),
                                  DV: NR}, "s0": {"fr_step0@2": "pass"},
                        "expect": {"fr_step0@2": a1, "fr_step0@4": nr, "FR": (
                            "fail (FR-1): D, end rule",
                            "D: end rule unconverged_early (status complete); not run: D+V")}},
        "fr2_fail": {"relax": {H: conv(50), V: conv(40), D: conv(45), DV: conv(55)}, "fr2": False,
                     "valid": {H: {"invariant_only": True}},
                     "s0": {"fr_step0@2": "pass", "fr_step0@4": "pass"}, "c2_current": False,
                     "expect": {"fr_step0@2": a1, "fr_step0@4": a1, "FR": (
                         "fail (FR-2)", "FR-1 passed; FR-2 failed (|δ_far| > 50 meV); " + inv("host"))}},
        "s0_2_final": {"relax": {H: conv(50), V: KILL, D: NR, DV: NR}, "rerun": (V, "fr_step0@2"),
                       "s0": {"fr_step0@2": "fail_final"}, "early": True,
                       "expect": {"fr_step0@2": ("fail (fail_final)", rep("V")), "fr_step0@4": nr, "FR": s0f}},
        "s0_4_noerror": {"relax": {H: conv(50), V: conv(40), D: conv(45), DV: KILL}, "no_error": True,
                         "s0": {"fr_step0@2": "pass", "fr_step0@4": "fail_pending_fix"},
                         "expect": {"fr_step0@2": a1, "fr_step0@4": (
                             "fail (fail_final: no error found)",
                             "attempt 1; STEP0_NO_ERROR: step-0 final (S2B section 2)"), "FR": s0f}},
        "s0_4_noerror_at_stop": {"relax": {H: conv(50), V: conv(40), D: conv(45), DV: KILL}, "no_error": True,
                                 "status": "stopped", "s0": {"fr_step0@2": "pass", "fr_step0@4": "fail_pending_fix"},
                                 "expect": {"fr_step0@2": a1, "fr_step0@4": (
                                     "fail (fail_final: no error found)",
                                     "attempt 1; STEP0_NO_ERROR: step-0 final (S2B section 2)"), "FR": s0f_stop}},
        # the same at a STOP, where the log holds only the leftover line of a later start (scripts/50, N-FR6)
        "s0_4_noerror_leftover_stop": {"relax": {H: conv(50), V: conv(40), D: conv(45), DV: KILL}, "no_error": True,
                                       "noerr_log": "leftover", "status": "stopped",
                                       "s0": {"fr_step0@2": "pass", "fr_step0@4": "fail_pending_fix"},
                                       "expect": {"fr_step0@2": a1, "fr_step0@4": (
                                           "fail (fail_final: no error found)",
                                           "attempt 1; STEP0_NO_ERROR: step-0 final (S2B section 2)"),
                                           "FR": s0f_stop}},
        # IX-4: the same with no STEP0_NO_ERROR line in the log: the fr_outcome begin_stop recorded names it, as E reads
        "s0_4_noerror_nolog_stop": {"relax": {H: conv(50), V: conv(40), D: conv(45), DV: KILL}, "no_error": True,
                                    "noerr_log": "none", "status": "stopped",
                                    "s0": {"fr_step0@2": "pass", "fr_step0@4": "fail_pending_fix"},
                                    "expect": {"fr_step0@2": a1, "fr_step0@4": (
                                        "fail (fail_final: no error found)",
                                        "attempt 1; STEP0_NO_ERROR: step-0 final (S2B section 2)"), "FR": s0f_stop}},
        # a final STOP at a step-0 fail_pending_fix with no route taken: final only through its stop note (FG-2,
        # IX-1), and drawn so (at fr_step0@2 the runner gave the later cells no record)
        "s0_2_pending_final_stop": {"relax": {H: conv(50), V: KILL}, "status": "stopped",
                                    "s0": {"fr_step0@2": "fail_pending_fix"}, "early": True,
                                    "expect": {"fr_step0@2": pend, "fr_step0@4": nr, "FR": stop}},
        "s0_4_pending_final_stop": {"relax": {H: conv(50), V: conv(40), D: conv(45), DV: KILL}, "status": "stopped",
                                    "s0": {"fr_step0@2": "pass", "fr_step0@4": "fail_pending_fix"},
                                    "expect": {"fr_step0@2": a1, "fr_step0@4": pend, "FR": stop}},
        # IX-4: a final STOP after gate FR recorded its decision (a STOP held until gate FR, scripts/50 N-F20): FR-1
        # failed on D's end rule; FR-2 failed; FR passed (counted as FR fails, S2B section 1)
        "stop_after_fr1": {"relax": {H: conv(50), V: conv(40), D: ("early", 80, [], "complete", "unconverged_early"),
                                     DV: NR}, "s0": {"fr_step0@2": "pass"}, "status": "stopped", "gate_fr": True,
                           "stop_reason": "held STOP: D ended unconverged_early (synthetic)",
                           "expect": {"fr_step0@2": a1, "fr_step0@4": nr, "FR": (
                               "fail (FR-1, D, end rule unconverged_early); then a final STOP (held STOP: D ended "
                               "unconverged_early (synthetic))",
                               "D: end rule unconverged_early (status complete); not run: D+V" + fin)}},
        "stop_after_fr2": {"relax": {H: conv(50), V: conv(40), D: conv(45), DV: conv(55)}, "fr2": False,
                           "s0": {"fr_step0@2": "pass", "fr_step0@4": "pass"}, "status": "stopped", "gate_fr": True,
                           "expect": {"fr_step0@2": a1, "fr_step0@4": a1, "FR": (
                               "fail (FR-2)" + then, "FR-1 passed; FR-2 failed (|δ_far| > 50 meV)" + fin)}},
        # integration review 2 (IX-4): FR-1 kinds other than the end rule, gate FR recorded, then a final STOP: two
        # failed checks at V (E's joined reason), a cell killed by a gate, a hard-cap refusal
        "stop_after_fr1_check45": {"relax": {H: conv(50), V: conv(40), D: NR, DV: NR}, "valid": {V: {"failed": [4, 5]}},
                                   "s0": {"fr_step0@2": "pass"}, "status": "stopped", "gate_fr": True, "early": True,
                                   "stop_reason": "operator final STOP after gate FR (synthetic)",
                                   "expect": {"fr_step0@2": a1, "fr_step0@4": nr, "FR": (
                                       "fail (FR-1, V, check 4, 5); then a final STOP (operator final STOP after gate "
                                       "FR (synthetic))", "V: final geometry fails check(s) [4, 5]; not run: D, D+V" +
                                       fin)}},
        "stop_after_fr1_killed": {"relax": {H: conv(50), V: conv(40), D: KILL, DV: NR}, "s0": {"fr_step0@2": "pass"},
                                  "status": "stopped", "gate_fr": True,
                                  "stop_reason": "operator final STOP after gate FR (synthetic)",
                                  "expect": {"fr_step0@2": a1, "fr_step0@4": nr, "FR": (
                                      "fail (FR-1, D, killed by a gate); then a final STOP (operator final STOP after "
                                      "gate FR (synthetic))", "D: no end rule (status killed_by_gate); not run: D+V" +
                                      fin)}},
        "stop_after_fr1_cap": {"relax": {H: conv(50), V: conv(40), D: CAPREF, DV: NR}, "hard_cap": "a2:" + D,
                               "s0": {"fr_step0@2": "pass"}, "status": "stopped", "gate_fr": True, "early": True,
                               "stop_reason": "operator final STOP after gate FR (synthetic)",
                               "expect": {"fr_step0@2": a1, "fr_step0@4": nr, "FR": (
                                   "fail (FR-1, D, hard-cap refusal); then a final STOP (operator final STOP after "
                                   "gate FR (synthetic))", "D: no end rule (status not_started_cap); not run: D+V" +
                                   fin)}},
        "stop_after_pass": {"relax": {H: conv(50), V: conv(40), D: conv(45), DV: conv(55)},
                            "s0": {"fr_step0@2": "pass", "fr_step0@4": "pass"}, "status": "stopped", "gate_fr": True,
                            "expect": {"fr_step0@2": a1, "fr_step0@4": a1, "FR": (
                                "pass at gate FR" + then + "; counted as FR fails (S2B section 1)", frp + fin)}},
        # IX-5: the @4 repeat prepared and not recorded (the move made, the STEP0_FIX save not; scripts/50
        # fr_step0_repeat), then a final STOP: as E's s0_set_aside
        "repeat_unrecorded_stop": {"relax": {H: conv(50), V: conv(40), D: conv(45)}, "rerun": (DV, "fr_step0@4"),
                                   "recorded": False, "s0": {"fr_step0@2": "pass"}, "status": "stopped",
                                   "mutate": [lambda r: os.remove(os.path.join(r, "fr", "gates", "fr_step0.json"))],
                                   "expect": {"fr_step0@2": a1, "fr_step0@4": (
                                       "not reached", "repeat prepared, not recorded (attempt 1 at D+V: "
                                       "fail_pending_fix; its files set aside unread; no STEP0_FIX entry)"),
                                       "FR": stop}},
        # integration review 2 (IX-5 at @2): the repeat of fr_step0@2 prepared and not recorded, then a final STOP: E
        # accepts it with no step-0 evaluation in force, and the figure follows
        "repeat_unrecorded_stop_2": {"relax": {H: conv(50)}, "rerun": (V, "fr_step0@2"), "recorded": False,
                                     "status": "stopped", "early": True,
                                     "expect": {"fr_step0@2": (
                                         "not reached", "repeat prepared, not recorded (attempt 1 at V: "
                                         "fail_pending_fix; its files set aside unread; no STEP0_FIX entry)"),
                                         "fr_step0@4": nr, "FR": stop}},
        "repeat_pass": {"relax": {H: conv(50), V: conv(40, [20]), D: conv(45), DV: conv(55)},
                        "rerun": (V, "fr_step0@2"), "s0": {"fr_step0@2": "pass", "fr_step0@4": "pass"},
                        "expect": {"fr_step0@2": ("pass", rep("V")), "fr_step0@4": ("pass", rep("V")),
                                   "FR": ("pass", frp)}},
        "repeat_V_then_DV_final": {"relax": {H: conv(50), V: conv(40, [20]), D: conv(45), DV: KILL},
                                   "rerun": (V, "fr_step0@2"), "s0": {"fr_step0@2": "pass", "fr_step0@4": "fail_final"},
                                   "expect": {"fr_step0@2": ("pass", rep("V")),
                                              "fr_step0@4": ("fail (fail_final)", rep("V")), "FR": s0f}},
        # integration review 2: the same, then a final STOP (the step-0 final the gate records at attempt 2)
        "repeat_V_then_DV_final_stop": {"relax": {H: conv(50), V: conv(40, [20]), D: conv(45), DV: KILL},
                                        "rerun": (V, "fr_step0@2"), "status": "stopped",
                                        "s0": {"fr_step0@2": "pass", "fr_step0@4": "fail_final"},
                                        "stop_reason": "operator final STOP after the step-0 repeat failed (synthetic)",
                                        "expect": {"fr_step0@2": ("pass", rep("V")),
                                                   "fr_step0@4": ("fail (fail_final)", rep("V")),
                                                   "FR": (s0f[0] + "; then a final STOP (operator final STOP after the "
                                                                   "step-0 repeat failed (synthetic))", s0f[1] + fin)}},
        "noerror_at_V": {"relax": {H: conv(50), V: KILL, D: NR, DV: NR}, "no_error": True,
                         "s0": {"fr_step0@2": "fail_pending_fix"}, "early": True,
                         "expect": {"fr_step0@2": ("fail (fail_final: no error found)",
                                                   "attempt 1; STEP0_NO_ERROR: step-0 final (S2B section 2)"),
                                    "fr_step0@4": nr, "FR": s0f}},
        "host_missing": {"relax": {H: (None, None, [], "missing", None), V: NR, D: NR, DV: NR}, "early": True,
                         "expect": {"fr_step0@2": nr, "fr_step0@4": nr, "FR": (
                             "fail (FR-1): host, missing", "host: no end rule (status missing); not run: V, D, D+V")}},
        "repeat_at_4_pass": {"relax": {H: conv(50), V: conv(40), D: conv(45), DV: conv(55, [25])},
                             "rerun": (DV, "fr_step0@4"), "s0": {"fr_step0@2": "pass", "fr_step0@4": "pass"},
                             "expect": {"fr_step0@2": a1, "fr_step0@4": ("pass", rep("D+V")), "FR": ("pass", frp)}},
        "repeat_prepared_stop": {"relax": {H: conv(50), V: ("inonly", None, [], "pending", None)},
                                 "rerun": (V, "fr_step0@2"), "status": "stopped", "early": True,
                                 "expect": {"fr_step0@2": ("not reached", prep), "fr_step0@4": nr, "FR": stop}},
        "final_stop": {"relax": {H: conv(50), V: conv(40), D: conv(45), DV: ("stopped", 85, [30], "pending", None)},
                       "status": "stopped", "s0": {"fr_step0@2": "pass", "fr_step0@4": "pass"},
                       "expect": {"fr_step0@2": a1, "fr_step0@4": a1, "FR": stop}},
        "stop_before_k0": {"relax": {H: conv(50), V: conv(40), D: ("inonly", None, [], "pending", None)},
                           "status": "stopped", "s0": {"fr_step0@2": "pass"},
                           "expect": {"fr_step0@2": a1, "fr_step0@4": nr, "FR": stop}},
        "v_scf0": {"relax": {H: conv(50), V: ("scf0", None, [], "complete", "unconverged_early"), D: NR, DV: NR},
                   "early": True,
                   "expect": {"fr_step0@2": ("skipped (no k = 0)", ""), "fr_step0@4": nr, "FR": (
                       "fail (FR-1): V, end rule",
                       "V: end rule unconverged_early (status complete); not run: D, D+V")}},
        "missing_V": {"relax": {H: conv(50), V: ("inonly", None, [], "missing", None), D: NR, DV: NR}, "early": True,
                      "expect": {"fr_step0@2": ("skipped (no k = 0)", ""), "fr_step0@4": nr, "FR": (
                          "fail (FR-1): V, missing", "V: no end rule (status missing); not run: D, D+V")}},
        "missing_after_k0_stop": {"relax": {H: conv(50), V: ("inonly", None, [], "missing", None)},
                                  "k0_seen": [V], "status": "stopped", "early": True,      # k = 0 seen, no gate yet
                                  "expect": {"fr_step0@2": nr, "fr_step0@4": nr, "FR": stop}},
        "fr1_check_not_evaluated": {"relax": {H: conv(50), V: conv(40), D: NR, DV: NR}, "no_validity": [V],
                                    "s0": {"fr_step0@2": "pass"}, "early": True,
                                    "expect": {"fr_step0@2": a1, "fr_step0@4": nr, "FR": (
                                        "fail (FR-1): V, check not evaluated",
                                        "V: no final-geometry check; not run: D, D+V")}},
        "fr1_killed": {"relax": {H: conv(50), V: conv(40), D: KILL, DV: NR}, "s0": {"fr_step0@2": "pass"},
                       "expect": {"fr_step0@2": a1, "fr_step0@4": nr, "FR": (
                           "fail (FR-1): D, killed by a gate",
                           "D: no end rule (status killed_by_gate); not run: D+V")}},
        "hard_cap": {"relax": {H: conv(50), V: conv(40), D: CAPREF, DV: NR}, "hard_cap": "a2:" + D,
                     "s0": {"fr_step0@2": "pass"}, "early": True,
                     "expect": {"fr_step0@2": a1, "fr_step0@4": nr, "FR": (
                         "fail (FR-1): D, not started (cap)",
                         "D: no end rule (status not_started_cap); not run: D+V")}},
        # a final STOP after the hard-cap refusal of D, before the runner gave D+V its not_run_gate record (scripts/50
        # N-FR5): D keeps its not_started_cap record, D+V has none
        "cap_stop": {"relax": {H: conv(50), V: conv(40), D: CAPREF}, "hard_cap": "a2:" + D, "status": "stopped",
                     "s0": {"fr_step0@2": "pass"}, "early": True,
                     "expect": {"fr_step0@2": a1, "fr_step0@4": nr, "FR": stop}},
        # a relaxation killed by a gate before k = 0 (D-C2-9: its step-0 gate is skipped; not reachable in fr, where a
        # gate kills only the running cell after its k = 0, but the rule is the runner's)
        "killed_no_k0": {"relax": {H: conv(50), V: KILL, D: NR, DV: NR}, "early": True,
                         "rec_edit": {V: [lambda rec: rec.pop("k0_seen", None)]},
                         "expect": {"fr_step0@2": ("skipped (no k = 0)", ""), "fr_step0@4": nr, "FR": (
                             "fail (FR-1): V, killed by a gate",
                             "V: no end rule (status killed_by_gate); not run: D, D+V")}},
        "repeat_no_k0": {"relax": {H: conv(50), V: ("scf0", None, [], "complete", "unconverged_early"), D: NR, DV: NR},
                         "rerun": (V, "fr_step0@2"), "early": True,
                         "expect": {"fr_step0@2": ("skipped (no k = 0)", prep), "fr_step0@4": nr, "FR": (
                             "fail (FR-1): V, end rule",
                             "V: end rule unconverged_early (status complete); not run: D, D+V")}},
        # the ledger split: b2 (which ended C2) ran fr after the C2 snapshot, b1 was re-timed (journal rotated), one
        # boot is untimed and one belongs to neither campaign; the C2 ledger marks no current boot (written off the
        # node)
        "ledger_mix": {"relax": small, "s0": {"fr_step0@2": "pass", "fr_step0@4": "pass"}, "c2_current": False,
                       "fr_ledger": [lambda frb: frb[0].update(hours=37.0),
                                     lambda frb: frb[1].update(hours=53.0, campaigns=["c2", "fr"])],
                       "extra_boots": [{"boot_id": "u1", "btime": 1.33e9, "hours": None, "campaigns": ["fr"]},
                                       {"boot_id": "x1", "btime": 1.34e9, "hours": 2.5, "campaigns": ["c3"]}],
                       "cost": {"fr_node_h": 32.75, "fr_boots": 3, "fr_boot_split_at_c2_ledger": True,
                                "c2_tail_h": 0.0, "retimed_boots": 1, "retimed_boots_h": -3.0, "manual_rows_new": 1,
                                "manual_rows_new_h": 0.5, "other_boots_h": 2.5, "problem_rows": 1,
                                "ledger_complete": False, "H_spent_h": 124.67, "ledger_problems": 1,
                                "H_spent_c2_ledger_h": 91.92},
                       "expect": {"fr_step0@2": a1, "fr_step0@4": a1, "FR": ("pass", frp)}},
    }


DEFAULT_COST = {"fr_node_h": 30.75, "fr_boots": 2, "fr_boot_split_at_c2_ledger": False, "c2_tail_h": 0.75,
                "retimed_boots": 0, "retimed_boots_h": 0.0, "manual_rows_new": 1, "manual_rows_new_h": 0.5,
                "other_boots_h": 0.0, "problem_rows": 0, "ledger_complete": True, "H_spent_h": 123.92,
                "ledger_problems": 0, "H_spent_c2_ledger_h": 91.92}


def _mutants(M):
    """Broken archives and code mutants, each with the build-assert key (one need() site) it must fail on ("~text": a
    plain assert of the reused C2 reader, matched by its message; "withheld: ...": the guard must raise); "label": the
    relaxation the message must name."""
    H, V, D, DV = FR_LABELS
    ok = lambda n, sp=(): ("conv", n, list(sp), "complete", "accepted_converged")
    NR = (None, None, [], "not_run_gate", None)
    small = {H: ok(12, [6]), V: ok(10), D: ok(8), DV: ok(9)}
    base = {"relax": small, "s0": {"fr_step0@2": "pass", "fr_step0@4": "pass"}}
    chk5 = {"relax": {H: small[H], V: small[V], D: NR, DV: NR}, "valid": {V: {"failed": [5]}},
            "s0": {"fr_step0@2": "pass"}}
    fr_, raw = lambda r, *p: os.path.join(r, "fr", *p), lambda r, lab: os.path.join(r, "fr", "raw", f"{lab}.a2.json")
    rec = lambda lab, fn: (lambda r: _edit(raw(r, lab), fn))
    ga = lambda gid, suf=".json": (lambda r: fr_(r, "gates_applied", re.sub(r"[^A-Za-z0-9_.-]", "_", gid) + suf))
    s1 = lambda r: os.path.join(r, "c1", "records", f"{M['g49'].a1_start_of(D)}.json")

    def both(gid, fn):                                   # a marker and its gate copy edited alike
        return lambda r: (_edit(ga(gid)(r), fn), _edit(ga(gid, ".gate.json")(r), fn))

    def rm_gate(gid):
        def f(r):
            for s in (".json", ".gate.json", ".inputs.json"):
                os.remove(ga(gid, s)(r))
        return f

    def comp(fn):
        return lambda r: _edit(fr_(r, "completeness.json"), fn)

    def state(fn):
        return lambda r: _edit(fr_(r, "state_end.json"), fn)

    def set_d(path, val):
        def f(d):
            x = d
            for k in path[:-1]:
                x = x[k]
            x[path[-1]] = val
        return f

    region63 = lambda r: _edit(os.path.join(r, "c1", "regions", f"{REGION}.json"), set_d(["n_free"], 63))
    extra_free = lambda d: d.update(free=d["free"] + [233], n_free=d["n_free"] + 1)
    swap_free = lambda d: d.update(free=sorted(d["free"][:-1] + [233]))
    early = {**base, "relax": {**small, D: ("early", 8, [], "complete", "unconverged_early"), DV: NR},
             "s0": {"fr_step0@2": "pass"}}
    stop = {**base, "status": "stopped", "relax": {**small, DV: ("stopped", 9, [4], "pending", None)}}
    s2final = {"relax": {H: small[H], V: ("inonly", None, [], "killed_by_gate", None), D: NR, DV: NR},
               "rerun": (V, "fr_step0@2"), "s0": {"fr_step0@2": "fail_final"}}
    repeat = {"relax": {**small, V: ok(10, [5])}, "rerun": (V, "fr_step0@2"),
              "s0": {"fr_step0@2": "pass", "fr_step0@4": "pass"}}
    no_k0 = {"relax": {H: small[H], V: ("scf0", None, [], "complete", "unconverged_early"), D: NR, DV: NR}}
    prepared = {"relax": {H: small[H], V: ("inonly", None, [], "pending", None)}, "rerun": (V, "fr_step0@2"),
                "status": "stopped"}
    noerr = {"relax": {**small, DV: ("inonly", None, [], "killed_by_gate", None)}, "no_error": True,
             "s0": {"fr_step0@2": "pass", "fr_step0@4": "fail_pending_fix"}}
    reg_free = sorted(int(i) for i in json.load(open(os.path.join(S2, "c1", "regions", f"{REGION}.json")))["free"])

    def fr_after_final(r):          # a gate FR (consistent with the records) applied after a final step-0 failure
        g49 = M["g49"]
        t = {lab: {"status": json.load(open(raw(r, lab)))["status"], "end_rule": None, "validity_final": None,
                   "a1_valid": True} for lab in FR_LABELS}
        t[H].update(end_rule="accepted_converged", validity_final=json.load(open(raw(r, H)))["validity_final"])
        res = g49.fr_eval(t)
        dec = {"outcome": "fail", "FR1": False, "FR2": None, "part": "FR-1", "cell": res["first_failure"]["cell"],
               "kind": res["first_failure"]["kind"]}
        _put_gate(fr_(r), "gates_applied", "gate:FR", _gatefile("FR", res, {"FR": dec}, 1), {}, 1)

    def no_a1dir(r):
        shutil.rmtree(fr_(r, "step0_attempt1"))

    rm_s0last = lambda r: os.remove(fr_(r, "gates", "fr_step0.json"))
    # IX-5: the @4 repeat prepared, not recorded, at a STOP (accepted); each conjunct of E's s0_set_aside broken alone
    unrec = {"relax": {H: small[H], V: small[V], D: small[D]}, "rerun": (DV, "fr_step0@4"), "recorded": False,
             "s0": {"fr_step0@2": "pass"}, "status": "stopped", "mutate": [rm_s0last]}
    # integration review 2: the @2 repeat prepared, not recorded, at a STOP (accepted; set_aside_2), each conjunct
    # broken alone
    unrec2 = {"relax": {H: small[H]}, "rerun": (V, "fr_step0@2"), "recorded": False, "status": "stopped"}
    s0_file = lambda r: _wj(_gatefile("fr_step0", {}, {"fr_step0": _s0dec(V, "fail_pending_fix", 1)}, 1),
                            fr_(r, "gates", "fr_step0.json"))
    s0_mark = lambda r: _put_gate(fr_(r), "gates_applied", "gate:fr_step0@2", _gatefile(
        "fr_step0", {}, {"fr_step0": _s0dec(V, "fail_pending_fix", 1)}, 1), {}, 1)

    def a1dir_only(r):
        os.makedirs(fr_(r, "step0_attempt1", "gates"))

    def fr2_no_s4(r):               # gate FR-2 decided while fr_step0@4 has no applied-gate file
        rm_gate("gate:fr_step0@4")(r)
        d2 = json.load(open(ga("gate:fr_step0@2")(r)))["decision"]["fr_step0"]
        _edit(fr_(r, "state_end.json"), lambda d: d.update(fr_step0=d2))
        _edit(fr_(r, "gates", "fr_step0.json"), lambda d: d.update(decision={"fr_step0": d2}))
        _edit(fr_(r, "completeness.json"), lambda d: d["jobs"].update({"gate:fr_step0@4": "skipped"}))

    def fr_missing(r):
        rm_gate("gate:FR")(r)
        os.remove(fr_(r, "gates", "FR.json"))
        _edit(fr_(r, "state_end.json"), lambda d: d.pop("FR"))
        _edit(fr_(r, "completeness.json"), lambda d: d["jobs"].update({"gate:FR": "skipped"}))

    def nr_output(r):
        shutil.copy(os.path.join(fr_(r, "raw"), f"{V}.p1.out.gz"), os.path.join(fr_(r, "raw"), f"{D}.p1.out.gz"))

    def part_gap(r):                  # host_R parts p1, p3: a part missing in the sequence
        for x in ("out", "in"):
            os.rename(os.path.join(fr_(r, "raw"), f"{H}.p2.{x}.gz"), os.path.join(fr_(r, "raw"), f"{H}.p3.{x}.gz"))

    def no_outputs(lab):              # a complete record whose part outputs are absent
        def f(r):
            for n in (1, 2, 3):
                p = os.path.join(fr_(r, "raw"), f"{lab}.p{n}.out.gz")
                if os.path.exists(p):
                    os.remove(p)
        return f

    def host_inputs(edit):            # every host_R part input edited alike (the free set stays equal across parts)
        def f(r):
            for n in (1, 2):
                p = os.path.join(fr_(r, "raw"), f"{H}.p{n}.in.gz")
                lines = gzip.open(p, "rt").read().split("\n")
                h = next(i for i, ln in enumerate(lines) if ln.startswith("ATOMIC_POSITIONS"))
                edit(lines, h + 1)
                with gzip.open(p, "wt") as fh:
                    fh.write("\n".join(lines))
        return f

    def fix_region_atom(lines, h):    # one region atom gets if_pos 0 0 0: 63 free atoms
        lines[h + reg_free[0]] += "    0   0   0"

    def swap_region_atom(lines, h):   # one region atom fixed and one atom outside the region freed: 64, another set
        fix_region_atom(lines, h)
        j = next(i for i in range(234) if i not in set(reg_free))
        lines[h + j] = re.sub(r"\s+0\s+0\s+0\s*$", "", lines[h + j])

    def part_free(r):                 # the part-2 input of host_R fixes one more atom than part 1
        p = os.path.join(fr_(r, "raw"), f"{H}.p2.in.gz")
        lines = gzip.open(p, "rt").read().split("\n")
        h = next(i for i, ln in enumerate(lines) if ln.startswith("ATOMIC_POSITIONS"))
        i = next(i for i in range(h + 1, len(lines)) if len(lines[i].split()) == 4)
        lines[i] += "    0   0   0"
        with gzip.open(p, "wt") as fh:
            fh.write("\n".join(lines))

    def log_cell(lab):                # the 'repeat prepared' log line names another cell
        def f(r):
            p = fr_(r, "logs", "campaign.log")
            text = open(p).read()
            assert V in text
            open(p, "w").write(text.replace(V, lab))
        return f

    def all_s0(fn):                   # every copy of the step-0 decision in force edited alike
        def f(r):
            for gid in ("gate:fr_step0@2", "gate:fr_step0@4"):
                both(gid, lambda d: fn(d["decision"]["fr_step0"]))(r)
            _edit(fr_(r, "gates", "fr_step0.json"), lambda d: fn(d["decision"]["fr_step0"]))
            _edit(fr_(r, "state_end.json"), lambda d: fn(d["fr_step0"]))
        return f

    def patch(obj, name, value):      # a code mutant, undone after the build
        def apply(M_):
            old = obj[name] if isinstance(obj, dict) else getattr(obj, name)
            (obj.__setitem__ if isinstance(obj, dict) else lambda k, v: setattr(obj, k, v))(name, value)
            return lambda: (obj.__setitem__ if isinstance(obj, dict) else lambda k, v: setattr(obj, k, v))(name, old)
        return apply

    q47, c2f, c46, gd, G = M["q47"], M["c2fig"], M["c46"], M["guard"], globals()
    fc0, cost0, c50 = c2f.force_curve, cost, _constants_50

    def fc_reads(key):                # a reader that also reads another value (an energy, ase, positions)
        def fc(*a, **kw):
            out = fc0(*a, **kw)
            q47.READS[key] += 1
            return out
        return fc

    def cost_energy(*a, **kw):        # a cost table with an energy key
        return cost0(*a, **kw) + [{"key": "Eb_meV", "value": "0"}]

    def fc_bang(q47_, label, outs, *a, **kw):   # the force reader, then the '!' line of the last part read directly
        out = fc0(q47_, label, outs, *a, **kw)
        with gzip.open(outs[-1], "rt") as fh:
            re.findall(r"^!\s+total energy\s+=\s+(-?\d+\.\d+)\s+Ry", fh.read(), re.M)
        return out

    def guarded_s2b(path):            # a reader with the guard's name, outside s2b/guard.py (no withheld check)
        return gd.GuardedS2b(json.load(open(path)), os.path.basename(path)) if os.path.exists(path) else None

    def ledger_c2(fn):
        return lambda sc: {**sc, "c2_ledger": [fn]}

    return [
        # pins (each source of a constant)
        ("pins: scripts/49", {**base, "patch": patch(M["g49"].RULES, "FR2_MAX_MEV", 40.0)}),
        ("pins: scripts/49", {**base, "patch": patch(M["g49"].RULES, "HARD_CAP_H", 500.0)}),
        ("pins: scripts/49", {**base, "patch": patch(M["g49"], "FR_ORDER", FR_LABELS[::-1])}),
        ("pins: scripts/49", {**base, "patch": patch(M["g49"], "FR_QUARTET", {**M["g49"].FR_QUARTET, "D": DV,
                                                                              "DV": D})}),
        ("pins: scripts/49", {**base, "patch": patch(M["g49"], "FR_STEP0_PAIRS", {})}),
        ("pins: scripts/47", {**base, "patch": patch(q47, "K_CAP", 199)}),
        ("pins: scripts/47", {**base, "patch": patch(q47, "BOHR_A", 0.5)}),
        ("pins: scripts/50", {**base, "patch": patch(G, "_constants_50",
                                                     lambda: {**c50(), "FR_ORDER": FR_LABELS[::-1]})}),
        ("pins: scripts/50", {**base, "patch": patch(G, "NOERR_LOG", ("fr/STEP0_NO_ERROR: a line scripts/50 never "
                                                                      "logs", NOERR_LOG[1]))}),
        ("pins: scripts/50", {**base, "patch": patch(G, "REPEAT_LOG", ("FR step-0 repeat prepared: cell ", "cell",
                                                                       "; "))}),     # integration review 2
        ("pins: guard", {**base, "patch": patch(gd, "GATE_LEAVES", GATE_LEAVES[::-1])}),
        ("pins: guard", {**base, "patch": patch(gd, "WITHHELD_S2B", frozenset(gd.WITHHELD_S2B) - {"dF_meV"})}),
        # campaign, A2 stop state, verify
        ("campaign", {**base, "mutate": [lambda r: _edit(fr_(r, "campaign.json"), set_d(["status"], "running"))]}),
        ("campaign", {**base, "mutate": [lambda r: os.remove(fr_(r, "campaign.json"))]}),
        # integration review 2: a STOP before the fr campaign commit was recorded (amendment item 11; E refuses it)
        ("campaign: no campaign commit", {**stop, "mutate": [lambda r: _edit(
            fr_(r, "campaign.json"), lambda d: d.update(start_commit=None, commit=None))]}),
        ("campaign: no campaign commit", {**stop, "stop_note": None, "mutate": [lambda r: _edit(  # before the note
            fr_(r, "campaign.json"), lambda d: (d.pop("start_commit"), d.update(commit=None)))]}),
        # IX-15: gate FR written but not applied (an N-FR4 or N-FR8 Stop: no copy, no marker, fr_outcome null), after
        # a pass and after an FR-1 failure, with the stop note and before it is read
        ("gates/: FR not applied", {**base, "status": "stopped", "gate_fr": True, "fr_outcome_stop": None,
                                    "mutate": [lambda r: (os.remove(ga("gate:FR", ".gate.json")(r)),
                                                          os.remove(ga("gate:FR")(r)))]}),
        ("gates/: FR not applied", {**chk5, "status": "stopped", "gate_fr": True, "fr_outcome_stop": None,
                                    "stop_note": None, "mutate": [lambda r: (os.remove(ga("gate:FR", ".gate.json")(r)),
                                                                             os.remove(ga("gate:FR")(r)))]}),
        ("state_end", {**base, "mutate": [lambda r: os.remove(fr_(r, "state_end.json"))]}),
        ("verify", {**base, "mutate": [lambda r: os.remove(os.path.join(r, *VERIFY))]}),
        # relaxations
        ("record", {**base, "mutate": [rec(V, set_d(["campaign"], "c2"))]}),
        ("record", {**base, "mutate": [rec(V, set_d(["label"], H))]}),
        ("A1 start", {**base, "mutate": [rec(D, set_d(["a1_cell", "work_id"], "s2_m30_Cs188p0_vac"))]}),
        ("A1 start", {**base, "mutate": [rec(D, lambda d: d.pop("a1_cell"))]}),
        ("rank count", {**base, "mutate": [rec(H, set_d(["layout", "ranks"], 48))]}),
        ("did not start", {**chk5, "mutate": [nr_output]}),
        ("part files: none", {**base, "mutate": [no_outputs(H)], "label": H}),
        ("part files: none", {**stop, "mutate": [no_outputs(DV)], "label": DV}),
        ("part files: none", {**base, "mutate": [no_outputs(H), rec(H, lambda d: d.pop("k0_seen"))], "label": H}),
        ("part files: count", {**base, "mutate": [rec(H, set_d(["restarts"], 0))], "label": H}),
        ("part files: count", {**base, "mutate": [rec(V, lambda d: d["parts"].append({"n": 2}))], "label": V}),
        ("part files: count", {**base, "mutate": [rec(H, set_d(["restarts"], "1"))], "label": H}),
        ("part files: count", {**base, "mutate": [rec(H, set_d(["reruns_from_zero"], None))], "label": H}),
        ("part files: count", {**base, "mutate": [rec(H, lambda d: d.update(restarts=0, reruns_from_zero=1))],
                               "label": H}),                                  # fewer restarts than parts - 1
        ("part files: count", {**base, "mutate": [rec(H, set_d(["restarts"], 2))], "label": H}),   # not rerun
        ("part files: names", {**base, "mutate": [part_gap]}),
        ("host region", {**base, "mutate": [region63]}),
        ("free-atom count: host region", {**base, "mutate": [host_inputs(fix_region_atom)], "label": H}),
        ("free-atom set: host region", {**base, "mutate": [host_inputs(swap_region_atom)], "label": H}),
        ("MACE energy", {**base, "patch": patch(c46, "load_record", lambda path, blind=True: json.load(open(path)))}),
        ("free-atom count: start record", {**base, "mutate": [lambda r: _edit(s1(r), extra_free)], "label": D}),
        ("free-atom set: start record", {**base, "mutate": [lambda r: _edit(s1(r), swap_free)], "label": D}),
        ("fixed-atom count", {**base, "mutate": [lambda r: _edit(s1(r), lambda d: d.update(n_fixed=d["n_fixed"] +
                                                                                             1))]}),
        ("k values differ from n_config", {**base, "mutate": [rec(H, lambda d: d.update(n_config=d["n_config"] + 1))]}),
        ("without configurations", {**base, "relax": {**small, V: ("scf0", None, [], "complete", "accepted_plateau")}}),
        ("converged_at_k", {**base, "mutate": [rec(V, lambda d: d.update(converged_at_k=d["converged_at_k"] - 1))]}),
        ("converged above forc_conv_thr", {**base, "relax": {**small, D: ("fakeconv", 8, [], "complete",
                                                                          "accepted_converged")}}),
        ("cap", {**base, "mutate": [rec(D, set_d(["end_rule", "outcome"], "accepted_plateau"))]}),
        ("cap", {**base, "relax": {**small, D: ("stopped", 150, [], "complete", "unconverged_cap")}, "label": D}),
        ("k_last", {**early, "mutate": [rec(D, lambda d: d.update(k_last=d["k_last"] - 1))]}),
        ("k_last", {**stop, "mutate": [rec(D, set_d(["end_rule", "outcome"], "unconverged_early"))]}),   # QE converged
        ("pending k", {**stop, "mutate": [rec(DV, set_d(["n_config"], 30))]}),
        # applied-gate markers and the step-0 repeat
        ("marker: no gate copy", {**base, "mutate": [lambda r: os.remove(ga("gate:fr_step0@2", ".gate.json")(r))]}),
        ("marker: decisions differ", {**base, "mutate": [lambda r: _edit(ga("gate:fr_step0@2")(r), set_d(
            ["decision", "fr_step0", "outcome"], "fail_pending_fix"))]}),
        ("marker: decisions differ", {**base, "mutate": [both("gate:fr_step0@2", lambda d: d["decision"].pop(
            "fr_step0"))]}),
        ("repeat: STEP0_FIX and step0_attempt1", {**s2final, "mutate": [no_a1dir]}),
        ("repeat: STEP0_FIX and step0_attempt1", {**base, "mutate": [a1dir_only]}),
        ("repeat: STEP0_FIX and step0_attempt1", {**s2final, "mutate": [lambda r: _edit(  # a second STEP0_FIX
            fr_(r, "campaign.json"), lambda d: d["commit_history"].append({"from": "f" * 40, "to": "a" * 40,
                                                                           "via": "fr/STEP0_FIX"}))]}),
        ("repeat: STEP0_FIX and step0_attempt1", {**unrec, "mutate": []}),          # gates/fr_step0.json present
        ("repeat: STEP0_FIX and step0_attempt1", {**unrec, "relax": {**unrec["relax"], DV: (    # @4 applied, D+V
            "inonly", None, [], "pending", None)}, "s0": base["s0"]}),                         # pending (review 2)
        ("repeat: STEP0_FIX and step0_attempt1", {**unrec, "mutate": [rm_s0last, rm_gate("gate:fr_step0@2")]}),  # @2
        # not applied (integration review 2); the @2 route (set_aside_2), each conjunct broken alone:
        ("repeat: STEP0_FIX and step0_attempt1", {**unrec2, "mutate": [s0_file]}),       # gates/fr_step0.json present
        ("repeat: STEP0_FIX and step0_attempt1", {**unrec2, "mutate": [s0_mark]}),       # the @2 marker and copy
        ("repeat: STEP0_FIX and step0_attempt1", {**unrec2, "relax": {H: small[H], V: small[V]}}),   # V complete
        ("repeat: STEP0_FIX and step0_attempt1", {**unrec2, "mutate": [lambda r: os.remove(fr_(
            r, "step0_attempt1", "gates_applied", "gate_fr_step0_2.json"))]}),       # the @2 attempt-1 marker absent
        ("repeat: STEP0_FIX and step0_attempt1", {**unrec, "relax": {**unrec["relax"], DV: ok(9)}}),   # D+V complete
        ("repeat: STEP0_FIX and step0_attempt1", {**unrec, "mutate": [rm_s0last, lambda r: os.remove(fr_(
            r, "step0_attempt1", "gates_applied", "gate_fr_step0_4.json"))]}),       # the @4 attempt-1 marker absent
        ("repeat: rerun cell", {**prepared, "mutate": [log_cell(D)]}),
        ("repeat: attempt-1 leaves", {**repeat, "mutate": [state(set_d(["fr_step0", "attempt1", "outcome"],
                                                                       "fail_final"))]}),
        ("repeat: attempt-1 leaves", {**base, "mutate": [all_s0(lambda d: d.update(attempt1={
            "attempts": 1, "outcome": "fail_pending_fix", "cell": V}))]}),             # a rerun cell without STEP0_FIX
        ("step-0 order", {**base, "mutate": [both("gate:fr_step0@2", set_d(["decision", "fr_step0", "outcome"],
                                                                        "fail_pending_fix"))]}),
        ("step-0 cell", {**base, "mutate": [both("gate:fr_step0@2", set_d(["decision", "fr_step0", "cell"], DV))]}),
        ("step-0 cell", {**base, "mutate": [both("gate:fr_step0@2", set_d(["decision", "fr_step0", "extra"], 1))]}),
        ("step-0 outcome", {**base, "mutate": [both("gate:fr_step0@2", set_d(["decision", "fr_step0", "outcome"],
                                                                          "repeat_pending"))]}),
        ("attempt: count", {**base, "mutate": [both("gate:fr_step0@4", set_d(["decision", "fr_step0", "attempts"],
                                                                          2))]}),
        ("attempt: count", {**base, "mutate": [both("gate:fr_step0@4", lambda d: d["decision"]["fr_step0"].update(
            attempts=2, repeat=True))]}),
        ("attempt: count", {**base, "mutate": [both("gate:fr_step0@2", set_d(["decision", "fr_step0", "repeat"],
                                                                          True))]}),
        ("attempt: count", {**base, "mutate": [both("gate:fr_step0@2", set_d(["decision", "fr_step0", "outcome"],
                                                                          "fail_final"))]}),
        ("attempt: attempt-1 leaves", {**repeat, "mutate": [all_s0(lambda d: d["attempt1"].update(
            outcome="fail_final"))]}),
        ("attempt: attempt-1 leaves", {**repeat, "mutate": [all_s0(lambda d: d["attempt1"].update(attempts=2))]}),
        ("step-0 state: repeat_pending", {**no_k0, "rerun": (V, "fr_step0@2"),
                                          "mutate": [state(set_d(["fr_step0", "cell"], DV))]}),
        ("step-0 state: repeat_pending", {**repeat, "mutate": [state(lambda d: d["fr_step0"].update(
            outcome="repeat_pending", cell=V, attempts=1))]}),               # after the later gate at D+V
        ("step-0 state: no applied gate", {**no_k0, "mutate": [state(set_d(["fr_step0"], {
            "attempts": 1, "outcome": "pass", "repeat": False, "fix_note": None, "cell": V}))]}),
        ("step-0 state: STEP0_NO_ERROR", {**noerr, "mutate": [state(set_d(["fr_step0", "attempts"], 2))]}),
        ("step-0 state: STEP0_NO_ERROR", {**noerr, "mutate": [state(set_d(["fr_step0", "no_error_found"], False))]}),
        ("step-0 state: STEP0_NO_ERROR", {**noerr, "relax": {**repeat["relax"], DV: noerr["relax"][DV]},
                                          "rerun": (V, "fr_step0@2")}),      # STEP0_NO_ERROR after attempt 2
        ("step-0 state: differs", {**base, "mutate": [state(set_d(["fr_step0", "outcome"], "fail_final"))]}),
        # a STOP of fr is final only through its stop note (FG-2, IX-1): a stopped fr without one is refused, a STOP at
        # a step-0 fail_pending_fix with neither route applied among them (D-C2-2, D-C2-3; fix round 2's 'step-0 route
        # pending' refusal); a stop note E refuses (STOP_CASES), a repository git cannot read, or a note beside a
        # done fr is refused too
        ("stop note: none", {**stop, "stop_note": None}),
        ("stop note: none", {"relax": {H: small[H], V: ("inonly", None, [], "killed_by_gate", None), D: NR, DV: NR},
                             "status": "stopped", "s0": {"fr_step0@2": "fail_pending_fix"}, "stop_note": None}),
        ("stop note: none", {**noerr, "status": "stopped", "noerr_log": "none", "stop_note": None}),
        ("stop note: none", {**prepared, "stop_note": None}),
        *[(key, {**stop, "stop_note": p, "stop_repo": rn}) for rn, p, key in STOP_CASES if key],
        ("stop note: git", {**stop, "nogit": True}),
        ("stop note: fr done", {**base, "stop_note": NOTE_OK}),
        # gate FR
        ("FR after a failed step-0", {**s2final, "mutate": [fr_after_final]}),
        ("FR after a failed step-0", {"relax": s2final["relax"], "s0": {"fr_step0@2": "fail_pending_fix"}}),
        ("FR decision: keys", {**base, "mutate": [both("gate:FR", set_d(["decision", "FR", "extra"], 1))]}),
        ("FR-1: gate code refused", {**chk5, "mutate": [rec(H, set_d(["validity_final", "check5_reading"],
                                                                      "as_written"))]}),
        ("FR-1 differs from the A2 records", {**chk5, "mutate": [both("gate:FR", set_d(["decision", "FR", "kind"],
                                                                                      "end_rule"))]}),
        ("FR-1 differs from the A2 records", {**chk5, "mutate": [both("gate:FR", set_d(["decision", "FR", "FR1"],
                                                                                      True))]}),
        ("reason lists", {**chk5, "mutate": [lambda r: _edit(ga("gate:FR", ".gate.json")(r), set_d(
            ["result", "cells_not_run"], [DV]))]}),
        ("FR decision: combination", {**base, "mutate": [both("gate:FR", set_d(["decision", "FR", "FR2"], None))]}),
        ("FR-2", {**base, "fr2": False, "mutate": [fr2_no_s4]}),
        ("fr_stop", {**chk5, "mutate": [state(set_d(["fr_stop", "at"], H))]}),
        ("fr_stop", {**chk5, "mutate": [state(set_d(["fr_stop", "kind"], "end_rule"))]}),
        ("fr_stop", {**base, "mutate": [state(set_d(["fr_stop"], {"at": H, "kind": "check", "time": "x"}))]}),
        ("fr_stop", {**chk5, "mutate": [state(lambda d: d.pop("fr_stop"))]}),
        ("FR state", {**base, "mutate": [state(set_d(["FR", "outcome"], "fail"))]}),
        ("FR state", {**base, "mutate": [state(lambda d: d.pop("FR"))]}),
        ("FR not applied", {**base, "mutate": [fr_missing]}),
        ("fr_outcome", {**chk5, "mutate": [lambda r: _edit(fr_(r, "campaign.json"), set_d(["fr_outcome"], "pass"))]}),
        # IX-4: at a STOP, the fr_outcome begin_stop records: absent, or other than the decisions fix
        ("fr_outcome", {**stop, "mutate": [lambda r: _edit(fr_(r, "campaign.json"), lambda d: d.pop("fr_outcome"))]}),
        ("fr_outcome", {**stop, "fr_outcome_stop": FR_OUTCOMES[0]}),
        ("fr_outcome", {**stop, "relax": small, "gate_fr": True, "fr_outcome_stop": None}),
        ("fr_outcome", {**noerr, "status": "stopped", "fr_outcome_stop": None}),  # the log's STEP0_NO_ERROR, null
        # integration review 2: fr_outcome step-0 final at a STOP whose last step-0 decision is fail_pending_fix at
        # attempt 2 (after a repeat; STEP0_NO_ERROR follows attempt 1 only): not the no-error route
        ("fr_outcome", {"relax": {**repeat["relax"], DV: ("inonly", None, [], "killed_by_gate", None)},
                        "rerun": (V, "fr_step0@2"), "s0": {"fr_step0@2": "pass", "fr_step0@4": "fail_pending_fix"},
                        "status": "stopped", "fr_outcome_stop": FR_OUTCOMES[3]}),
        ("gates/: FR.json", {**base, "mutate": [lambda r: _edit(fr_(r, "gates", "FR.json"), set_d(
            ["decision", "FR", "kind"], "check"))]}),
        ("gates/: FR.json", {**chk5, "mutate": [lambda r: _edit(fr_(r, "gates", "FR.json"), set_d(
            ["result", "cells_not_run"], [DV]))]}),
        ("gates/: fr_step0.json", {**base, "mutate": [lambda r: _edit(fr_(r, "gates", "fr_step0.json"), set_d(
            ["decision", "fr_step0", "attempts"], 2))]}),
        ("gates/: FR.json", {**base, "mutate": [lambda r: os.remove(fr_(r, "gates", "FR.json"))]}),
        ("gates/: fr_step0.json", {**base, "mutate": [lambda r: os.remove(fr_(r, "gates", "fr_step0.json"))]}),
        ("gates/: fr_step0.json", {**no_k0, "rerun": (V, "fr_step0@2"), "mutate": [lambda r: _wj(_gatefile(
            "fr_step0", {}, {"fr_step0": _s0dec(V, "fail_pending_fix", 1)}, 1), fr_(r, "gates", "fr_step0.json"))]}),
        ("completeness: file", {**base, "mutate": [comp(lambda d: d.pop("jobs"))]}),
        ("completeness: file", {**base, "mutate": [lambda r: os.remove(fr_(r, "completeness.json"))]}),
        ("completeness: gate jobs", {**base, "mutate": [comp(lambda d: d["jobs"].update({"gate:fr_step0@4":
                                                                                         "skipped"}))]}),
        ("completeness: relaxation jobs", {**base, "mutate": [comp(lambda d: d["jobs"].update({"a2:" + V:
                                                                                               "missing"}))]}),
        # the ledgers
        ("ledger: C2 end boot", ledger_c2(lambda c2b: c2b[0].update(current=True))(base)),
        ("ledger: C2 end boot", ledger_c2(lambda c2b: c2b[1].update(hours=None))(base)),
        ("ledger: duplicate boot", {**base, "extra_boots": [{"boot_id": "f1", "btime": 1.3e9, "hours": 18.5,
                                                             "campaigns": ["fr"]}]}),
        ("ledger split: not the C2 end boot", {**base, "fr_ledger": [lambda frb: frb[0].update(
            campaigns=["c1", "fr"])]}),
        ("ledger split: fewer hours", {**base, "fr_ledger": [lambda frb: frb[1].update(hours=50.0,
                                                                                        campaigns=["c2", "fr"])]}),
        ("ledger: C2 boot tail negative", {**base, "fr_ledger": [lambda frb: frb[1].update(hours=50.0)]}),
        # READS, columns, energy columns
        ("READS: before the build", {**base, "pre": lambda M_: q47.READS.update(F=1)}),
        ("READS: after the build", {**base, "patch": patch(c2f, "force_curve", fc_reads("ase"))}),
        ("READS: after the build", {**base, "patch": patch(c2f, "force_curve", fc_reads("F"))}),
        ("READS: after the build", {**base, "patch": patch(c2f, "force_curve", fc_reads("positions"))}),
        ("energy column: header", {**base, "columns": ("fig_s2b_fr_a_relaxations.csv", "F_final_eV")}),
        ("energy column: key/value", {**base, "patch": patch(G, "cost", cost_energy)}),
        ("columns", {**base, "columns": ("fig_s2b_fr_b_gates.csv", "extra")}),
        # the reused C2 reader, and the guard
        ("~the free-atom set differs between parts", {**base, "mutate": [part_free]}),
        ("withheld: decision", {**base, "mutate": [both("gate:fr_step0@4", set_d(["decision", "fr_step0", "dF_meV"],
                                                                              CANARY["dF_meV"]))]}),
        ("withheld: record", {**chk5, "mutate": [rec(V, set_d(["validity_final", "F_final_eV"], CANARY["dF_meV"]))]}),
        # the audit hook: a part output opened beside the force reader, and an fr JSON file read by a function of the
        # guard's name outside s2b/guard.py
        ("hook: the part output", {**base, "patch": patch(c2f, "force_curve", fc_bang)}),
        ("hook: guard bypass", {**base, "patch": patch(gd, "guarded_s2b", guarded_s2b)}),
    ]


def _expected_forces(wp, q47, kind, n, free):
    """Independently of the figure's reader: for each k, the largest |F| component (Ry/bohr) over the free atoms and
    over all atoms of the WP2e configuration that _WP2e.parts() writes at k (conv: k < n from the WP2e run and k = n
    its converged last configuration; cap: k <= 200; early, stopped: k <= n; scf0: none). Forces only."""
    src = [] if kind == "scf0" else list(range(n)) + [282] if kind == "conv" else list(range(201)) if kind == "cap" \
        else list(range(n + 1))                                       # scf0: no configuration
    out = []
    for k, j in enumerate(src):
        F = np.abs(q47._read_forces(wp.txt, *wp.cfg[j]["forces"]))
        out.append((k, float(F[free].max()), float(F.max())))
    return out


def _span(p, axis):
    """The extent (data) along axis 0 (x) or 1 (y) of a span or band patch, or of the first path of a collection."""
    if hasattr(p, "get_patch_transform"):
        v = p.get_patch_transform().transform(p.get_path().vertices)
    else:
        v = p.get_paths()[0].vertices
    return float(v[:, axis].min()), float(v[:, axis].max())


def _xspan(p):
    return _span(p, 0)


def _tip(marker):
    """The direction an arrow marker points to: the side ('top', 'bottom', 'right', 'left') of its single tip vertex."""
    v = {(round(float(x), 6), round(float(y), 6)) for x, y in marker.vertices}
    got = [w for w, t in (("top", (0.0, 1.0)), ("bottom", (0.0, -1.0)), ("right", (1.0, 0.0)), ("left", (-1.0, 0.0)))
           if t in v]
    return got[0] if len(got) == 1 else tuple(got)


def _dash(line):
    """A line's dash pattern as (offset, tuple of floats or None)."""
    off, seq = line._unscaled_dash_pattern
    return float(off), None if seq is None else tuple(float(x) for x in seq)


def _probe(src, nm, early):
    """A probe for plot(): every drawn mark against the source data, with the constants the spec fixes written out
    (threshold 0.02005 eV/A, k = 200, axes, glyphs, cap 201, band 4.19-4.65, plan 22-58 or 6-29, up to 72): the
    curves (no point that is not a source point or an axis crossing; every crossing drawn), the restart ticks on the
    curve, the edge arrows (edge, direction, the value at each excursion's extreme), the keys (labels, colours, line
    styles), the gate rows in order, and in panel c every mark on the row of its relaxation's (or bar's) label."""
    import matplotlib as mpl
    rd = lambda fn: list(csv.DictReader(open(os.path.join(src, fn))))
    R, P, G = rd("fig_s2b_fr_a_relaxations.csv"), rd("fig_s2b_fr_a_force.csv"), rd("fig_s2b_fr_b_gates.csv")
    C = {r["key"]: r["value"] for r in rd("fig_s2b_fr_c_cost.csv")}
    glyph = {"accepted_converged": "o", "accepted_plateau": "^", "unconverged_cap": "X", "unconverged_early": "s"}
    dash = {"host": (0.0, None), "V": (0.0, (4.0, 1.6)), "D": (0.0, (1.0, 1.3)), "DV": (0.0, (5.0, 1.4, 1.0, 1.4))}
    cell = {"host": "host", "V": "V", "D": "D", "DV": "D+V"}
    col = {"host": "#2f6db5", "V": "#d08a2e", "D": "#2a9d8f", "DV": "#a4508b"}
    ink, fail, neu = "#3a3a3a", "#c4553a", "#9aa3ad"
    names = {"fr_step0@2": "Step-0 at 2 (V, k = 0)", "fr_step0@4": "Step-0 at 4 (D+V, k = 0)",
             "FR": "Gate FR (FR-1, FR-2)"}
    same = mpl.colors.same_color
    flat = lambda s: re.sub(r"\s+", "", s)
    near = lambda x, y: math.isclose(x, y, rel_tol=1e-9, abs_tol=1e-12)
    on_lim = lambda y: near(y, 1e-3) or near(y, 10.0)

    def probe(fig, ax):
        rnd = fig.canvas.get_renderer()
        pt = fig.dpi / 72.0
        arts = lambda axx, pre: [x for x in axx.get_children() if isinstance(x.get_gid(), str) and
                                 (x.get_gid() == pre or pre.endswith(":") and x.get_gid().startswith(pre))]

        def one(axx, gid):
            xs = arts(axx, gid)
            assert len(xs) == 1, (nm, gid, len(xs))
            return xs[0]
        a, b, c1, c2, c3 = (ax[k] for k in ("a", "b", "c1", "c2", "c3"))
        # panel a: frame, threshold (ink, dashed 3-2), k = 200
        thr = one(a, "thr")
        assert np.allclose(thr.get_ydata(), 0.02005, atol=5e-6) and same(thr.get_color(), ink) and \
            _dash(thr) == (0.0, (3.0, 2.0)), (nm, "threshold")
        assert list(one(a, "k200").get_xdata()) == [200, 200], (nm, "k = 200")
        assert a.get_yscale() == "log" and np.allclose(a.get_ylim(), (1e-3, 10.0)) and \
            np.allclose(a.get_xlim(), (-2, 202)), (nm, "axes of panel a")
        assert "BFGS" not in a.get_xlabel() and a.get_xlabel().startswith("Configuration k (ionic SCF cycle"), nm
        want_leg, handles = [], ax["legend"].legend_handles
        assert len(handles) == len(R), (nm, "relaxation key")
        for r, h in zip(R, handles):
            o, rl = int(r["order"]), r["role"]
            want_leg.append(f"{o}  {cell[rl]}" + ("  (rerun after the step-0 fix)" if r["step0_rerun"] == "True"
                                                  else "") + ("" if r["status_text"] == "complete" else
                                                              f": {r['status_text']}"))
            pts = [(int(p["k"]), float(p["fmax_free_eV_A"])) for p in P if int(p["order"]) == o]
            if r["line"] == "none" or not pts:          # no configuration: a legend entry without a line
                assert (r["line"] == "none") == (not pts) or r["n_config"] == "0", (nm, o, "line without points")
                assert not arts(a, f"curve:{o}") and not arts(a, f"end:{o}") and \
                    not arts(a, f"tick:{o}:") and not arts(a, f"arrow:a:{o}:"), (nm, o, "a line without data")
                assert h.get_color() == "none", (nm, o, "key handle of a relaxation without a line")
                continue
            # the key handle: the cell's colour and line style
            assert same(h.get_color(), col[rl]) and _dash(h) == dash[rl], (nm, o, "key handle")
            cv = one(a, f"curve:{o}")
            assert same(cv.get_color(), col[rl]) and _dash(cv) == dash[rl], (nm, o, "style")
            fk = dict(pts)
            X, Y = np.asarray(cv.get_xdata(), float), np.asarray(cv.get_ydata(), float)
            drawn = [(float(x), float(y)) for x, y in zip(X, Y) if np.isfinite(y)]
            for k, f in pts:                            # every source point inside the axis is drawn, none outside
                hit = [y for x, y in drawn if x == float(k)]
                if 1e-3 <= f <= 10.0:
                    assert hit and near(hit[0], f), (nm, o, k, "curve value")
                else:
                    assert not [y for y in hit if not on_lim(y)], (nm, o, k, "an off-axis point drawn inside")
            for x, y in drawn:                          # nothing else: a source point or a crossing of an axis limit
                assert (x == int(x) and int(x) in fk and near(fk[int(x)], y)) or on_lim(y), \
                    (nm, o, x, y, "a drawn point that is neither a source point nor an axis crossing")
            for (k0, f0), (k1, f1) in zip(pts, pts[1:]):    # every segment that crosses a limit reaches it
                for lim in (1e-3, 10.0):
                    if (f0 - lim) * (f1 - lim) < 0:
                        assert [x for x, y in drawn if k0 < x < k1 and near(y, lim)], (nm, o, k0, k1, lim, "crossing")
            e = one(a, f"end:{o}")
            lk, lf = pts[-1]
            assert e.get_xdata()[0] == lk and math.isclose(e.get_ydata()[0], min(max(lf, 1e-3), 10.0)), (nm, o, "end")
            if r["line"] == "complete":
                assert e.get_marker() == glyph[r["outcome"]] and same(e.get_markerfacecolor(), col[rl]), (nm, o)
            else:
                assert r["line"] == "stopped" and e.get_marker() == "o" and \
                    same(e.get_markerfacecolor(), "white") and same(e.get_markeredgecolor(), col[rl]), (nm, o)
            ticks = arts(a, f"tick:{o}:")              # restart ticks: at each part start, on the curve
            assert sorted(x.get_xdata()[0] for x in ticks) == sorted(int(x) for x in r["part_starts"].split()) and \
                all(x.get_marker() == "|" for x in ticks), (nm, o, "restart ticks")
            for x in ticks:
                s = int(x.get_xdata()[0])
                assert near(float(x.get_ydata()[0]), min(max(fk[s], 1e-3), 10.0)), (nm, o, s, "restart tick height")
            # edge arrows: one per off-axis point, at its edge and pointing out of the axis; the value at each
            # excursion's extreme and at an outside end, on the arrow's side
            off = [(i, k, f) for i, (k, f) in enumerate(pts) if f > 10.0 or f < 1e-3]
            want_vals = []
            for side in (1, -1):
                idx = [i for i, k, f in off if (f > 10.0) == (side == 1)]
                runs = [[i] for i in idx[:1]]
                for i in idx[1:]:
                    (runs[-1].append(i) if i == runs[-1][-1] + 1 else runs.append([i]))
                for run in runs:
                    ext = max(run, key=lambda i: side * pts[i][1])
                    want_vals += [f"{pts[i][1]:.3g} eV/Å" for i in run if i == ext or i == len(pts) - 1]
            arr = arts(a, f"arrow:a:{o}:")
            assert sorted(x.get_xdata()[0] for x in arr) == sorted(k for _, k, _ in off), (nm, o, "edge arrows")
            for x in arr:
                top = fk[int(x.get_xdata()[0])] > 10.0
                assert x.get_ydata()[0] == (0.975 if top else 0.025) and \
                    _tip(x.get_marker()) == ("top" if top else "bottom"), (nm, o, x.get_gid(), "edge and direction")
            vals = arts(a, f"arrowval:a:{o}:")
            assert sorted(t.get_text() for t in vals) == sorted(want_vals), (nm, o, "values")
            for t in vals:
                top = fk[int(t.get_gid().rsplit(":", 1)[1])] > 10.0
                assert t.get_position()[1] == (0.975 if top else 0.07), (nm, o, t.get_gid(), "value side")
        assert [t.get_text() for t in ax["legend"].get_texts()] == want_leg, (nm, "legend")
        assert [t.get_text() for t in ax["key"].get_texts()] == [
            "accepted: converged", "accepted: plateau", "unconverged: cap", "unconverged: early end",
            "stopped (pending)", "restart", "off-axis value", "forc_conv_thr 0.00078 Ry/bohr = 0.02005 eV/Å"], nm
        kh = ax["key"].legend_handles
        assert [h.get_marker() for h in kh[:6]] == ["o", "^", "X", "s", "o", "|"] and \
            _tip(kh[6].get_marker()) == "top" and same(kh[7].get_color(), ink) and _dash(kh[7]) == (0.0, (3.0, 2.0)), nm
        # panel b: every gate with its name, state (colour) and detail on one row, the rows in the graph order
        tops = []
        for g in G:
            nmt = one(b, f"b:{g['gate']}:name")
            assert nmt.get_text() == names[g["gate"]], (nm, g["gate"])
            y1 = nmt.get_window_extent(rnd).y1
            tops.append((g["gate"], y1))
            s = one(b, f"b:{g['gate']}:state")
            bad = g["state"].startswith("fail") or (g["gate"] == "FR" and (g["state"].startswith(
                "not reached (after a final STOP)") or "; then a final STOP (" in g["state"]))
            assert flat(s.get_text()) == flat(g["state"]) and same(s.get_color(), fail if bad else ink if
                                                                    g["state"].startswith("pass") else neu), \
                (nm, g["gate"], "state")
            dts = arts(b, f"b:{g['gate']}:detail")
            assert [flat(x.get_text()) for x in dts] == ([flat(g["detail"])] if g["detail"] else []), (nm, g["gate"])
            assert all(abs(x.get_window_extent(rnd).y1 - y1) <= 0.5 * pt for x in [s] + dts), (nm, g["gate"], "row")
            for x in [s] + dts:                         # FG-4: no line of a wrapped text holds a single word
                ln = x.get_text().split("\n")
                assert len(ln) < 2 or all(len(w.split()) > 1 for w in ln), (nm, g["gate"], "a lone word", ln)
        assert [x[0] for x in tops] == ["fr_step0@2", "fr_step0@4", "FR"] and tops[0][1] > tops[1][1] > tops[2][1], \
            (nm, "gate rows: order")
        # panel c: cap 201, band 4.19-4.65, the S2B section 8 plan (and up to 72 after a repeat), markers and texts,
        # each on the row whose label names its relaxation
        assert list(one(c1, "cap201").get_xdata()) == [201, 201], nm
        assert c1.get_title() == "Configurations" and c2.get_title() == "Minutes per configuration" and \
            c2.get_xlabel() == "Wall minutes" + (", 64 MPI ranks" if any(r["ranks"] for r in R) else "") + \
            "\nband: C2 range 4.19–4.65", (nm, c2.get_title(), c2.get_xlabel())
        assert np.allclose(_xspan(one(c2, "rateband")), (4.19, 4.65)), nm
        lab_at = {round(float(t.get_position()[1]), 6): t.get_text() for t in c1.get_yticklabels()}
        row_of = lambda y: lab_at.get(round(float(y), 6))
        for r in R:
            o, cl = int(r["order"]), col[r["role"]]
            want_row = f"{o}  {cell[r['role']]}"
            if r["n_config"] == "":
                t = one(c1, f"c1text:{o}")
                assert t.get_text() == r["status_text"] and row_of(t.xy[1]) == want_row and \
                    not arts(c1, f"c1:{o}") and not arts(c2, f"c2:{o}") and not arts(c2, f"c2text:{o}"), \
                    (nm, o, "c without n_config")
                continue
            for axx, tag, v, hi in ((c1, "c1", float(r["n_config"]), 210.0), (c2, "c2", float(r["min_per_config"]),
                                                                              10.0)):
                if tag == "c2" and int(r["n_config"]) < 1:
                    t = one(c2, f"c2text:{o}")
                    assert t.get_text() == "no config." and row_of(t.xy[1]) == want_row and \
                        not arts(c2, f"c2:{o}") and not arts(c2, f"arrow:c2:{o}"), \
                        (nm, o, "minutes per configuration without a configuration")
                    continue
                if v > hi:
                    m, t = one(axx, f"arrow:{tag}:{o}"), one(axx, f"arrowval:{tag}:{o}")
                    cx = axx.get_yaxis_transform().transform((0.985, 0))[0]
                    assert t.get_text() == f"{v:.3g}" and same(t.get_color(), cl) and \
                        t.get_window_extent(rnd).x1 <= cx - (3.0 + 1.0) * pt, (nm, o, tag, "right-edge value")
                    assert row_of(m.get_ydata()[0]) == want_row and row_of(t.xy[1]) == want_row and \
                        _tip(m.get_marker()) == "right", (nm, o, tag, "right-edge arrow row")
                else:
                    m = one(axx, f"{tag}:{o}")
                    assert m.get_xdata()[0] == v and m.get_marker() == glyph.get(r["outcome"], "o") and \
                        same(m.get_markerfacecolor(), cl) and row_of(m.get_ydata()[0]) == want_row, (nm, o, tag)
                    if v == 0:                          # off the spine by ZERO_DX (3 pt), not on it
                        dx = m.get_transform().transform((0, 0))[0] - axx.transData.transform((0, 0))[0]
                        assert 2.0 * pt <= dx <= 4.0 * pt, (nm, o, tag, "marker at x = 0 on the spine", dx / pt)
        # c3: every bar whole on its axis, on the row of its label, with its value right of it and inside the axis
        xmax = c3.get_xlim()[1]
        lab3 = {round(float(t.get_position()[1]), 6): t.get_text() for t in c3.get_yticklabels()}
        nb = int(C["fr_boots"])
        want3 = {"fr": f"fr ({nb} boot{'s' if nb != 1 else ''})", "manual": "manual rows", "tail": "C2 boot tail"}
        yc = {}
        for bk, key in (("fr", "fr_node_h"), ("manual", "manual_rows_new_h"), ("tail", "c2_tail_h")):
            v = float(C[key])
            bar, t = one(c3, f"bar:{bk}"), one(c3, f"barval:{bk}")
            yc[bk] = bar.get_y() + bar.get_height() / 2.0
            ext, bb, axb = t.get_window_extent(rnd), bar.get_window_extent(rnd), c3.get_window_extent(rnd)
            assert math.isclose(bar.get_width(), max(v, 0.0)) and v <= xmax and t.get_text() == f"{v:.1f}" and \
                ext.x0 >= bb.x1 + 1.0 * pt and ext.x1 <= axb.x1, (nm, bk, "node-hour bar")
            assert lab3.get(round(yc[bk], 6)) == want3[bk] and near(t.xy[1], yc[bk]), (nm, bk, "bar row and label")
        plan = (6, 29) if early else (22, 58)
        assert C["plan_fr_node_h"] == f"{plan[0]}-{plan[1]}" and (C["early_stop"] == "True") == early, (nm, "plan")
        fr_rows = (yc["fr"] - 0.38, yc["fr"] + 0.38)    # the plan bands lie on the fr bar's row
        pb = one(c3, "planband")
        assert np.allclose(_xspan(pb), plan) and np.allclose(_span(pb, 1), fr_rows), (nm, "plan band")
        rep = C["step0_repeat"] == "True"
        assert len(arts(c3, "repeatband")) == (1 if rep else 0), (nm, "repeat band")
        if rep:
            rb = one(c3, "repeatband")
            assert np.allclose(_xspan(rb), (plan[1], 72)) and np.allclose(_span(rb, 1), fr_rows), (nm, "repeat band")
        assert c3.get_title(loc="left") == f"fr node-hours (S2 so far {float(C['H_spent_h']):.1f} of 520)", \
            (nm, c3.get_title(loc="left"))
        flag, note = arts(c3, "ledger_incomplete"), one(c3, "ledger_note").get_text()
        assert [x.get_text() for x in flag] == ([] if C["ledger_complete"] == "True" else [
            f"ledger incomplete: {C['ledger_problems']} problem(s), {C['problem_rows']} boot(s) untimed"]), (nm, flag)
        assert ("re-timed earlier boots" in note) == (C["retimed_boots"] != "0") and (
            C["retimed_boots"] == "0" or note.endswith(f"{float(C['retimed_boots_h']):+.1f}".replace("-", "−") +
                                                       " node-h")), (nm, note)
        xl = c3.get_xlabel().split("\n")
        assert xl[0] == f"Node-hours; band: plan {plan[0]}–{plan[1]}" + (
            ", early stop" if early else " for the four") + " (S2B section 8)", (nm, xl)
        assert (C["cells_run"] == "host V D D+V" and not early) or ("FR ran " + (", ".join(C["cells_run"].split()) or
                                                                                 "no cell")) in xl, (nm, xl)
        assert [x for x in xl if x.startswith("lighter band")] == ([
            "lighter band: up to 72" + (" on FR failure" if early else "") + " with a step-0 repeat"] if rep else []), \
            (nm, xl)
        # panel letters: c sits under a and b
        la = [x for x in a.texts if x.get_gid() == "label:a"]
        lc = [x for x in fig.texts if x.get_gid() == "label:c"]
        assert len(la) == len(lc) == 1 and la[0].get_position()[0] == lc[0].get_position()[0], (nm, "panel letters")
    return probe


def _text_fills(pdf, text):
    """For each occurrence of text in the PDF (collision-audit geometry): the areas (pt^2) of the filled regions whose
    box contains it."""
    sys.path.insert(0, QA_DIR)
    import audit_figure_collisions as A
    from pathlib import Path
    out = []
    for page in A.extract_pdf_geometry(Path(pdf)):
        for t in page.texts:
            if t.text.strip() == text:
                out.append([A.rect_area(r.bbox) for r in page.fills if A.rect_contains(r.bbox, t.bbox, tolerance=0.25)])
    return out


def _alignment(out):
    """The alignment verdicts the plot wrote: both must be PASS with comparisons and no finding."""
    v = []
    for suf in (".alignment.json", ".labels.alignment.json"):
        j = json.load(open(out + suf))
        s = j["summary"]
        assert j["verdict"] == "PASS" and s["comparisons"] >= 1 and s["fail"] == 0 and s["warn"] == 0, \
            (out, suf, j["verdict"], s)
        v.append(f"{j['verdict']} ({s['comparisons']} comparisons)")
    return v


SELFTEST_MARK = "\n# ---------------------------------------------------------------- self-test"
# the first argument of every open() in the build, plot and QA code (_build_code_audit): scripts/50's source text,
# c1/regions/m30_A188.json, c1/smoke.json, fr/logs/campaign.log, c2/ledger.json, the source data (written by the
# build, read by the plot), the PDF and its collision report
OPEN_ALLOWED = sorted(['os.path.join(SCRIPTS, "50_s2_campaign.py")', 'os.path.join(fr, "logs", "campaign.log")',
                       'os.path.join(arch, "c1", "regions", f"{REGION}.json")',
                       'os.path.join(arch, "c1", "smoke.json")', 'os.path.join(arch, "c2", "ledger.json")',
                       'os.path.join(src, fn)', 'os.path.join(src, fn)', 'out + ".pdf"',
                       'out + ".collision-audit.json"'])
LOCAL_PATH = re.compile(r"(?<![\w.])/(?:Users|private|var|tmp|home|Volumes)/")


def _build_code_audit(extra=""):
    """The build, plot and QA code (everything above the self-test section, plus extra), read as an AST. Refused:
    access to a guarded object's private dict (_d), __dict__ or __getattribute__; vars(), getattr(), eval(), exec(),
    globals() or __import__; any other file reader (read_text, read_bytes, json.loads, an .open() with arguments such
    as gzip.open). open() is allowed only on the paths of OPEN_ALLOWED. Every fr JSON file goes through s2b/guard.py
    and every part output through the C2 force reader (the audit hook checks both at run time). A static complement
    of the canary scan, which finds a withheld value only when it is printed with at least 3 significant digits.
    Returns (refused constructs, sorted open() arguments)."""
    text = open(os.path.abspath(__file__)).read()
    head = text[:text.index(SELFTEST_MARK)] + extra
    bad, opens = [], []
    for n in ast.walk(ast.parse(head)):
        if isinstance(n, ast.Attribute) and n.attr in ("_d", "__dict__", "__getattribute__", "read_text", "read_bytes",
                                                      "loads", "f_locals", "f_globals"):
            bad.append(f"line {n.lineno}: .{n.attr}")
        if isinstance(n, ast.Name) and n.id in ("vars", "getattr", "eval", "exec", "globals", "__import__"):
            bad.append(f"line {n.lineno}: {n.id}")
        if isinstance(n, ast.Call) and (isinstance(n.func, ast.Name) and n.func.id == "open" or
                                        isinstance(n.func, ast.Attribute) and n.func.attr == "open" and n.args):
            opens.append(ast.get_source_segment(head, n.args[0]) if n.args else "")
    return bad, sorted(opens)


def _text_outputs(out, src):
    """The text files plot() and qa() write (with the hygiene kind of scripts/46: SVG may name its XML namespace URL)
    and the source data."""
    files = [(out + s, "code") for s in (".svg", ".alignment.svg")] + \
        [(out + s, "json") for s in (".alignment.json", ".labels.alignment.json", ".collision-audit.json")]
    return files + [(os.path.join(src, f), "json") for f in COLUMNS]


def _hygiene(c46, out, src, roots):
    """No output text file holds a local path (the temporary folder, or any /Users, /private, /var, /tmp, /home or
    /Volumes path) or breaks a hygiene rule of scripts/46: these files are committed to the public repository."""
    for p, kind in _text_outputs(out, src):
        t = open(p).read()
        bad = c46.hygiene_violations(t, kind=kind) + [r for r in roots if r in t] + LOCAL_PATH.findall(t)
        assert not bad, (os.path.basename(p), "hygiene", bad[:3])


def _own(rel):
    """True for a path under figures/ that this script can write: its figure files and QA reports (fig_s2b_fr.*, not
    the script itself), its source data (source_data/fig_s2b_fr_*), a folder of its own temporary files, --keep copies
    (selftest_*), the QA controls (qa_*) and bytecode (__pycache__/). Other figures' files are not its own: another
    script or person may change them while the self-test runs."""
    parts = rel.split(os.sep)
    return "__pycache__" in parts or parts[-1].startswith(("selftest_", "qa_")) or \
        (any(x.startswith("fig_s2b_fr") for x in parts) and rel != "fig_s2b_fr.py")


def _snapshot(d):
    """Every file under d that this script can write (_own), with its size and modification time: the self-test writes
    nothing into the repository."""
    out = {}
    for dp, _, fs in os.walk(d):
        for f in fs:
            rel = os.path.relpath(os.path.join(dp, f), d)
            if _own(rel):
                s = os.stat(os.path.join(dp, f))
                out[rel] = (s.st_size, s.st_mtime_ns)
    return out


def _qa_controls(tmp, src):
    """Negative controls of the layout QA, with the constants plot() and qa() use: a 4 pt text fails qa() (the 5 pt
    floor), two overlapping texts fail qa() (the collision audit), and plot() with c3 moved 5 pt off its row fails the
    panel-alignment gate (ALIGN_KW)."""
    import matplotlib as mpl
    mpl.use("Agg")
    import matplotlib.pyplot as plt
    sys.path.insert(0, QA_DIR)
    from audit_panel_alignment import PanelAlignmentError
    got = []
    for nm, texts in (("small_text", [(0.2, 0.5, "a label at 4 pt", 4.0)]),
                      ("overlap", [(0.2, 0.5, "an overlapping label", 7.0), (0.22, 0.52, "a second label", 7.0)])):
        size_in = (2.0, 1.0)                        # a small test canvas (not the figure)
        fig = plt.figure(figsize=size_in)
        for x, y, s, fs in texts:
            fig.text(x, y, s, fontsize=fs)
        p = os.path.join(tmp, f"qa_{nm}")
        fig.savefig(p + ".pdf")
        plt.close(fig)
        try:
            qa(p, required=True)
        except AssertionError as e:
            got.append(str(e))
            continue
        raise AssertionError(f"qa() passed the {nm} control")
    assert got[0].startswith("PDF text below 5 pt") and got[1].startswith("collision audit: text-text"), got
    try:
        plot(src, os.path.join(tmp, "qa_skew"), formats=("pdf",), audit="required", skew_pt=5.0)
    except PanelAlignmentError as e:
        got.append(str(e).split("\n")[0])
    else:
        raise AssertionError("the panel-alignment gate passed c3 moved 5 pt off its row")
    return got


def self_test(keep=None):
    M = modules()
    g49, q47, gd, c2, c46 = M["g49"], M["q47"], M["guard"], M["c2fig"], M["c46"]
    Blinded = gd.Blinded
    _GUARD[1:] = [os.path.realpath(x.__file__) for x in (gd, c2, q47)]
    sys.addaudithook(_audit_hook)
    before = _snapshot(HERE)
    wp = c2._WP2e(q47)
    scen = _scenarios(M)
    region = json.load(open(os.path.join(S2, "c1", "regions", f"{REGION}.json")))
    fsets = _free_sets(region)
    # the build, plot and QA code: no guarded private dict, no other reader, open() only of the allowed files; and
    # the audit refuses such code (a negative control)
    bad, opens = _build_code_audit()
    assert not bad and opens == OPEN_ALLOWED, ("build-code audit", bad, opens)
    bad, opens = _build_code_audit("\nx = rec._d.get('F_final_eV')\ny = getattr(rec, '_d')\nz = gzip.open(outs[-1])\n")
    assert len(bad) == 2 and "outs[-1]" in opens, ("build-code audit: negative control", bad, opens)
    # the canary scan finds values in meV, eV, Ry or Ha (a leak in other units), and nothing in the figure's numbers
    assert _canary_hits("δ 9.8765 eV") and _canary_hits("0.7259 Ry") and _canary_hits("7654 meV") and \
        _canary_hits("1.111e+00") and not _canary_hits("k = 200; 4.19-4.65 min; 0.02005 eV/Å; 30.8 of 520; 2026-11-21")
    assert math.isclose(CANARY["E_part_eV"], E_PART_RY * q47.RY_EV, rel_tol=1e-9)
    # the energy-column test: each branch alone (a withheld name, every energy token, every energy unit) and
    # forces, counts and look-alike names
    saved_w = gd.WITHHELD_S2B
    try:
        gd.WITHHELD_S2B = saved_w | {"held_x"}
        assert energy_column("held_x") and energy_column("dF_k0") and energy_column("relax_change_meV") and \
            energy_column("F_final_eV")
        for t in ("F", "dF", "E", "dE", "Eb", "delta", "energy", "plateau", "K3", "SP"):
            assert energy_column(f"x_{t}") and energy_column(f"{t}_x_y"), ("energy token", t)
        for u in ("eV", "meV", "Ry", "Ha", "kJ", "kcal"):
            assert energy_column(f"x_{u}"), ("energy unit", u)
        assert not any(energy_column(c) for c in ("fmax_free_eV_A", "fmax_free_Ry_bohr", "n_free", "wall_h",
                                                  "min_per_config", "x_Fe", "x_eVs", "meV_x", "Ry_bohr", "k_cap",
                                                  "held_y", "uncovered_h")), "energy column: a false positive"
    finally:
        gd.WITHHELD_S2B = saved_w
    tmp = tempfile.mkdtemp(prefix="fig_s2b_fr_selftest_")
    roots = sorted({tmp, os.path.realpath(tmp)})
    qa_rows, hit, n_parts = [], {}, 0
    cell = {"host": "host", "V": "V", "D": "D", "DV": "D+V"}
    kind_of = {"end rule": "end_rule", "check": "check", "check not evaluated": "check_not_evaluated",
               "missing": "missing", "not started (cap)": "not_started_cap", "killed by a gate": "killed_by_gate",
               **{v: k for k, v in E_REASON.items()}}       # IX-4: E's reason words after a final STOP
    G = globals()
    note_of = lambda sc: sc["stop_note"] if "stop_note" in sc else NOTE_OK if sc.get("status") == "stopped" else None
    e_parts = {}
    try:
        # the snapshot of figures/ holds the paths this script can write, not another figure's files (which another
        # script or person may change while the self-test runs) nor this script
        sd = os.path.join(tmp, "snapshot")
        own = sorted(os.path.join(*p) for p in (("fig_s2b_fr.pdf",), ("fig_s2b_fr.alignment.json",),
                                                 ("source_data", "fig_s2b_fr_b_gates.csv"), ("__pycache__", "m.pyc"),
                                                 ("selftest_pass.png",), ("qa_skew.pdf",)))
        for rel in own + [os.path.join(*p) for p in (("fig_s2b_fr.py",), ("fig_s2b_e_fk.py",), ("fig_s2_c2_a2.py",),
                                                     ("source_data", "fig_s2b_e_fk_a.csv"))]:
            os.makedirs(os.path.dirname(os.path.join(sd, rel)), exist_ok=True)
            with open(os.path.join(sd, rel), "w") as fh:
                fh.write("x")
        assert sorted(_snapshot(sd)) == own, ("snapshot: the paths compared", sorted(_snapshot(sd)))
        # FG-2: the stop notes, on a synthetic git repository; the figure's rule is E's (pinned against e_eval.py),
        # and the pin fails when the figure's phrase, date rule, location rule or committed-and-clean test differs
        repos, nogit = _stop_repos(os.path.join(tmp, "stop_repos"))
        ee = _e_eval()
        _pin_e_eval(ee, repos)
        git0 = _git
        for name, value in (("STOP_PHRASE", re.compile(STOP_PHRASE.pattern)),
                            ("STOP_NOTE", f"{S2_REL}/FR_STOP_NOTE_2.md"),
                            ("ISO_DATE", re.compile(r"\b(\d\d\d\d)-(\d\d)-(\d\d)\b")),
                            ("stop_note_ok", lambda p, t: p.startswith(S2_REL + "/") and bool(STOP_PHRASE.search(t))
                             and bool(ISO_DATE.search(t))),
                            ("_git", lambda repo, *a, ok=(0,): (0, b"") if a[0] == "status" else
                             git0(repo, *a, ok=ok))):
            saved = G[name]
            G[name] = value
            try:
                _pin_e_eval(ee, repos)
            except AssertionError:
                continue
            finally:
                G[name] = saved
            raise AssertionError(f"the pin against e_eval.py passed with {name} changed")
        # integration review 2 (IX-4, IX-16): E's reason words and reason code, from E's source (ast); the pin fails
        # when the figure's copy or its join differs, and when E's source differs (its words, its join)
        ens = _e_reason_src()
        _pin_e_reason(ens, M)
        er0 = e_reason
        for name, value in (("E_REASON", {**E_REASON, "killed_by_gate": "killed by gate"}),
                            ("E_REASON", {k: v for k, v in E_REASON.items() if k != "missing"}),
                            ("e_reason", lambda kind, rec: "check 4; 5" if kind == "check" else er0(kind, rec))):
            saved = G[name]
            G[name] = value
            try:
                _pin_e_reason(ens, M)
            except AssertionError:
                continue
            finally:
                G[name] = saved
            raise AssertionError(f"the pin against e_eval.py passed with {name} changed")
        with open(os.path.join(S2, "s2b", "e_eval.py")) as fh:
            esrc = fh.read()
        for old, new in (('"killed by a gate"', '"killed by gate"'), ('"hard-cap refusal"', '"cap refusal"'),
                         ('return ", ".join(str(x) for x in failed)', 'return "; ".join(str(x) for x in failed)'),
                         ('return f"check {checks_str(failed)}"', 'return f"checks {checks_str(failed)}"')):
            assert esrc.count(old) == 1, ("E's source", old)
            try:
                _pin_e_reason(_e_reason_src(esrc.replace(old, new)), M)
            except AssertionError:
                continue
            raise AssertionError(f"the pin against e_eval.py passed with E's {old} changed")
        sha_ok = hashlib.sha256(_GOOD).hexdigest()
        assert stop_note(repos["ok"], NOTE_OK) == {"path": NOTE_OK, "sha256": sha_ok}, "stop note: its sha256"
        b_ = STOP_REPOS["bytes"][NOTE_OK][0]              # a byte outside UTF-8: E's sha256, of the replaced text
        assert stop_note(repos["bytes"], NOTE_OK)["sha256"] == hashlib.sha256(
            b_.decode(errors="replace").encode()).hexdigest() != hashlib.sha256(b_).hexdigest(), "stop note: non-UTF-8"
        for nm, sc in scen.items():
            root, src = os.path.join(tmp, nm, "s2"), os.path.join(tmp, nm, "source_data")
            _synthetic(root, sc, wp, M)
            q47.READS.clear()
            out = os.path.join(tmp, nm, "fig")
            with _Armed(root):
                res = build(root, src, note_of(sc), repos[sc.get("stop_repo", "ok")])
                plot(src, out, formats=("pdf", "svg", "png") if keep else ("pdf", "svg"), audit="required",
                     probe=_probe(src, nm, sc.get("early", False)))
            # FG-2: the source data records the stop note of a final STOP, its path and the sha256 of its text
            want = {"fr_status": sc.get("status", "done"), "stop_note": "", "stop_note_sha256": ""}
            if sc.get("status") == "stopped":
                want.update(stop_note=NOTE_OK, stop_note_sha256=sha_ok)
            got_s = {r["key"]: r["value"] for r in csv.DictReader(open(os.path.join(src, "fig_s2b_fr_b_stop.csv")))}
            assert {r["key"]: r["value"] for r in res["stop"]} == got_s == want, (nm, "stop note in the source data",
                                                                                  got_s)
            assert not _OPENED and not _LISTED and not _UNGUARDED and not _UNREAD, \
                (nm, _OPENED, _LISTED, _UNGUARDED, _UNREAD)
            got = {r["gate"]: (r["state"], r["detail"]) for r in res["gates"]}
            assert got == sc["expect"], (nm, got, sc["expect"])
            assert [r["stops_fr"] for r in res["gates"]] == \
                [r["state"].startswith("fail") for r in res["gates"][:2]] + [True], (nm, "stops_fr")
            # the cell and kind columns of the gate rows: the step-0 cell; FR's first failure (label, raw kind)
            g0 = res["gates"]
            assert [(x["cell"], x["kind"]) for x in g0[:2]] == [(STEP0_AT[n][1], "") for n, _ in GATES[:2]], \
                (nm, "step-0 cell column")
            ff = re.fullmatch(r"fail \(FR-1\): (host|V|D|D\+V), (.+)", g0[2]["state"]) or \
                re.match(r"fail \(FR-1, (host|V|D|D\+V), (.+?)\); then a final STOP \(", g0[2]["state"])   # IX-4
            kw_ = (lambda w: kind_of.get(w) or kind_of["check" if w.startswith("check ") else " ".join(w.split()[:2])])
            assert (g0[2]["cell"], g0[2]["kind"]) == ((FR_LABELS[list(cell.values()).index(ff[1])], kw_(ff[2]))
                                                      if ff else ("", "")), (nm, "FR cell and kind columns")
            if sc.get("status") == "stopped":           # IX-4, IX-5: pinned against E's route code on this archive
                e_parts[nm] = _pin_e_route(ee, root, M, g0, nm)
            rows = {r["label"]: r for r in res["rows"]}
            txt = lambda i: rows[FR_LABELS[i]]["status_text"]
            cst = {r["key"]: r["value"] for r in res["cost"]}
            want_cost = sc.get("cost", DEFAULT_COST)
            for k, v in want_cost.items():
                assert (math.isclose(float(cst[k]), v, abs_tol=1e-9) if isinstance(v, float) else cst[k] == v), \
                    (nm, k, cst[k], v)
            ranks = {r["ranks"] for r in res["rows"] if r["line"] != "none"}
            assert ranks <= {64}, (nm, ranks)
            walls, ran = 0.0, []
            for lab, rl in zip(FR_LABELS, FR_ROLES):      # the reported fields against the synthetic specification
                spec, r = sc["relax"].get(lab), rows[lab]
                if spec is None:
                    continue
                if spec[3] not in ("not_run_gate", "not_started_cap"):
                    ran.append(cell[rl])
                fx = {"restarts": len(spec[2]), "reruns_from_zero": 0, "interruptions": 0,
                      **sc.get("fields", {}).get(lab, {})}
                assert (r["restarts"], r["reruns_from_zero"], r["interruptions"]) == \
                    (fx["restarts"], fx["reruns_from_zero"], fx["interruptions"]), (nm, lab, "restarts, reruns", r)
                if spec[3] == "complete":                 # the record's wall time and minutes per configuration
                    nc = _spec_nc(spec)
                    wh = max(nc, 1) * RATE_SYN[rl] / 60.0
                    walls += wh
                    assert r["n_config"] == nc and math.isclose(float(r["min_per_config"]), RATE_SYN[rl],
                                                                rel_tol=1e-12) and \
                        math.isclose(float(r["wall_h"]), wh, rel_tol=1e-12), (nm, lab, "n_config, wall time, rate", r)
                if r["line"] == "none":
                    continue
                assert r["n_free"] == len(fsets[rl]) and r["n_fixed"] == 234 - len(fsets[rl]) and \
                    r["part_starts"] == " ".join(map(str, spec[2])), (nm, lab, r)
                if spec[0] == "conv":
                    assert r["converged_at_k"] == spec[1] == r["k_last"] and r["n_config"] == spec[1] + 1, (nm, lab)
            assert math.isclose(float(cst["wall_h_sum"]), walls, rel_tol=1e-12, abs_tol=1e-12) and \
                math.isclose(float(cst["uncovered_h"]), want_cost["fr_node_h"] - walls, abs_tol=1e-9) and \
                cst["cells_run"] == " ".join(ran), (nm, "wall hours, uncovered hours, cells run")
            # panel a values, independently of the reader: k, the free-atom maximum, the unit conversion
            pts = res["points"]
            for order, (lab, rl) in enumerate(zip(FR_LABELS, FR_ROLES), 1):
                spec, r = sc["relax"].get(lab), rows[lab]
                if spec is None or r["line"] == "none":
                    assert not [p for p in pts if p["order"] == order], (nm, lab)
                    continue
                want = _expected_forces(wp, q47, spec[0], spec[1], fsets[rl])
                got_p = [p for p in pts if p["order"] == order]
                assert [p["k"] for p in got_p] == [k for k, _, _ in want] and (
                    r["line"] != "complete" or len(got_p) == r["n_config"]), (nm, lab, "k values")
                for p, (k, ff_, fa) in zip(got_p, want):
                    assert float(p["fmax_free_Ry_bohr"]) == ff_ and math.isclose(
                        float(p["fmax_free_eV_A"]), ff_ * 25.711033738162943, rel_tol=1e-12), (nm, lab, k)
            # the part outputs hold no WP2e energy: every energy line holds the canary, which the scan finds in Ry,
            # eV, meV and Ha (values are counted, never printed)
            if nm in ("pass", "fr1_early_D", "v_scf0", "final_stop"):
                allowed = {f"-{E_PART_RY:.8f}", f"-{E_PART_RY:.10f}", "0.0E+00", f"{E_FERMI_EV:.4f}"}
                raw = os.path.join(root, "fr", "raw")
                for f in sorted(os.listdir(raw)):
                    if not f.endswith(".out.gz"):
                        continue
                    t_ = gzip.open(os.path.join(raw, f), "rt").read()
                    n_bad = len(_part_energies(t_) - allowed)
                    assert n_bad == 0, (nm, f, f"{n_bad} energy value(s) of the WP2e run left in a part output")
                    bang = re.findall(r"^!\s+total energy\s+=\s+(-?\d+\.\d+)\s+Ry", t_, re.M)
                    if bang:
                        e = float(bang[-1])
                        ev = e * q47.RY_EV
                        assert all(_canary_hits(s) for s in (repr(e), f"{ev:.6g}", f"{ev * 1e3:.7g}", f"{e / 2:.6g}",
                                                              f"{ev:.3g}")), (nm, f, "the canary scan")
                    n_parts += 1
            if nm == "pass":
                assert any(fa != ff_ for lab, rl in zip(FR_LABELS, FR_ROLES) for _, ff_, fa in _expected_forces(
                    wp, q47, sc["relax"][lab][0], sc["relax"][lab][1], fsets[rl])), "free and all-atom maxima agree"
                k_ = {r["key"]: r["value"] for r in csv.DictReader(open(os.path.join(src,
                                                                                     "fig_s2b_fr_constants.csv")))}
                assert float(k_["forc_conv_thr_Ry_bohr"]) == 7.8e-4 and abs(float(k_["forc_conv_thr_eV_A"]) - 0.02005) \
                    < 5e-6 and k_["k_cap"] == "200", k_
                assert [txt(i) for i in range(4)] == ["complete"] * 4 and rows[FR_LABELS[0]]["part_starts"] == "30"
            if nm == "fr1_host_cap":
                assert [txt(i) for i in range(4)] == ["complete"] + ["not run (gate)"] * 3
            if nm == "fr1_early_D":
                assert txt(2) == "early end, bfgs_failed" and rows[FR_LABELS[2]]["line"] == "complete"
                assert cst["cells_run"] == "host V D"
            if nm in ("s0_2_final", "repeat_pass", "repeat_no_k0", "repeat_prepared_stop"):
                assert rows[FR_LABELS[1]]["step0_rerun"] is True and cst["step0_repeat"] is True
                assert sum(r["step0_rerun"] for r in res["rows"]) == 1
            if nm == "repeat_at_4_pass":
                assert rows[FR_LABELS[3]]["step0_rerun"] is True and sum(r["step0_rerun"] for r in res["rows"]) == 1
                assert [r["attempt"] for r in res["gates"][:2]] == [1, 2] and cst["step0_repeat"] is True
            if nm == "s0_2_final":
                assert txt(1) == "killed by a gate"
            if nm == "repeat_pass":
                assert [r["attempt"] for r in res["gates"][:2]] == [2, 2] and rows[FR_LABELS[1]]["part_starts"] == "20"
            if nm == "final_stop":
                assert txt(3) == "stopped at k = 85" and rows[FR_LABELS[3]]["line"] == "stopped"
            if nm == "stop_before_k0":
                assert txt(2) == "stopped before k = 0" and txt(3) == "not started (no record)"
            if nm == "repeat_prepared_stop":
                assert txt(1) == "stopped before k = 0" and txt(2) == txt(3) == "not started (no record)"
            if nm in ("v_scf0", "repeat_no_k0"):
                assert txt(1) == "early end, scf_failed, no configuration" and rows[FR_LABELS[1]]["n_config"] == 0
            if nm == "missing_V":
                assert txt(1) == "missing" and rows[FR_LABELS[1]]["line"] == "none"
            if nm in ("fr1_killed", "killed_no_k0"):
                assert txt(2 if nm == "fr1_killed" else 1) == "killed by a gate"
            if nm == "hard_cap":
                assert txt(2) == "not started (cap)" and txt(3) == "not run (gate)"
            if nm == "cap_stop":                          # D+V has no record after the cap refusal of D
                assert txt(2) == txt(3) == "not started (cap)" and cst["cells_run"] == "host V", (nm, txt(2), txt(3))
            if nm == "rerun_k0":
                assert rows[FR_LABELS[1]]["part_starts"] == "20"
            al = _alignment(out)
            m = qa(out, required=True)
            assert m[3] == 0, (nm, "collision warnings", m)
            cj = json.load(open(out + ".collision-audit.json"))      # the report qa() wrote, path-free
            assert cj["pdf"] == "fig.pdf" and (cj["verdict"], cj["summary"]["fail"], cj["summary"]["warn"]) == m[1:], \
                (nm, "collision report", cj["pdf"], m)
            _hygiene(c46, out, src, roots)
            qa_rows.append((nm, al, *m))
            if keep:
                os.makedirs(keep, exist_ok=True)
                for ext in ("pdf", "svg", "png", "alignment.json", "labels.alignment.json", "collision-audit.json"):
                    shutil.copy(f"{out}.{ext}", os.path.join(keep, f"selftest_{nm}.{ext}"))
            svg = re.sub(r'(?:id="[^"]*"|#[A-Za-z][\w-]*)', "", open(out + ".svg").read())   # SVG ids are hashes
            blob = "".join(open(os.path.join(src, f)).read() for f in COLUMNS) + svg
            near = _canary_hits(blob)
            assert not near, f"{nm}: a withheld canary value reached the source data or the figure ({len(near)})"
            assert not re.search("|".join(sorted(gd.WITHHELD_S2B)), blob), f"{nm}: a withheld field name in the output"
        assert n_parts >= 10, ("part outputs checked for the energy canary", n_parts)
        # integration review 2: the stopped archives the figure refuses before the stop note is read, and E's
        # route_admit refuses each: a STOP before the fr campaign commit (start_commit and commit null, as W 50
        # set_campaign writes them before s2b_accept; amendment 2026-11-12a item 11) and (IX-15) gate FR written but
        # not applied (the gates_applied copy and marker never written, fr_outcome null: an N-FR4 or N-FR8 Stop);
        # the stopped archives above E admitted
        cj_edit = lambda fn: (lambda r: _edit(os.path.join(r, "fr", "campaign.json"), fn))

        def unapplied(r):
            for s in (".gate.json", ".json"):
                os.remove(os.path.join(r, "fr", "gates_applied", "gate_FR" + s))
            _edit(os.path.join(r, "fr", "campaign.json"), lambda d: d.update(fr_outcome=None))
        pre_c = ("campaign: no campaign commit", ("before its campaign commit was recorded", "not a 40-hex commit"))
        pre_u = ("gates/: FR not applied", ("written but not applied",))
        for nm, base_, edit, (key, e_why) in (
                ("precommit_null", "final_stop", cj_edit(lambda d: d.update(start_commit=None, commit=None)), pre_c),
                ("precommit_absent", "final_stop", cj_edit(lambda d: (d.pop("start_commit"), d.update(commit=None))),
                 pre_c),
                ("unapplied_fr1", "stop_after_fr1", unapplied, pre_u),
                ("unapplied_pass", "stop_after_pass", unapplied, pre_u)):
            root = os.path.join(tmp, nm, "s2")
            _synthetic(root, {**scen[base_], "mutate": scen[base_].get("mutate", []) + [edit]}, wp, M)
            with _Armed(root):
                _expect_fail(lambda: (q47.READS.clear(), build(root, os.path.join(tmp, nm, "src"), NOTE_OK,
                                                                repos["ok"])), nm, key, Blinded)
                try:
                    _e_admit(ee, _e_cj(ee, gd.guarded_s2b(os.path.join(root, "fr", "campaign.json"))),
                             os.path.join(root, "fr"))
                    raise AssertionError(f"{nm}: E's route_admit admitted an archive the figure refuses")
                except ee.EError as x:
                    assert any(w in str(x) for w in e_why), (nm, str(x))
            q47.READS.clear()
        assert len(e_parts) >= 19, ("stopped archives pinned against E", len(e_parts))
        # the attempt-1 canary works: opening or listing one of its paths under the armed hook fails
        a1d = os.path.join(tmp, "repeat_pass", "s2", "fr", "step0_attempt1")
        cf = next(os.path.join(dp, f) for dp, _, fs in os.walk(a1d) for f in fs)
        for fn in (lambda: open(cf).close(), lambda: os.listdir(a1d)):
            _ARMED[0] = True
            try:
                fn(); raise AssertionError("the attempt-1 canary did not fire")
            except PermissionError:
                pass
            finally:
                _ARMED[0] = False
        assert _OPENED == [cf] and _LISTED == [a1d], (_OPENED, _LISTED)
        _OPENED.clear(); _LISTED.clear()
        # the guard hook works: an fr JSON file opened outside s2b/guard.py fails; and the part-output hook: a part
        # output opened outside the force reader fails
        with _Armed(os.path.join(tmp, "pass", "s2")):
            try:
                json.load(open(os.path.join(tmp, "pass", "s2", "fr", "campaign.json")))
                raise AssertionError("the guard hook did not fire")
            except PermissionError:
                pass
            assert gd.guarded_s2b(os.path.join(tmp, "pass", "s2", "fr", "campaign.json")).get("status") == "done"
            try:
                gzip.open(os.path.join(tmp, "pass", "s2", "fr", "raw", f"{FR_LABELS[1]}.p1.out.gz"), "rt").read(1)
                raise AssertionError("the part-output hook did not fire")
            except PermissionError:
                pass
        assert len(_UNGUARDED) == 1 and len(_UNREAD) == 1, (_UNGUARDED, _UNREAD)
        _UNGUARDED.clear(); _UNREAD.clear()
        # edge arrows: off-axis forces in panel a (excursions above and below with distinct values, an end above the
        # axis): the value at each excursion's extreme and at the end
        src = os.path.join(tmp, "pass", "source_data")
        rows = list(csv.DictReader(open(os.path.join(src, "fig_s2b_fr_a_force.csv"))))
        for r in rows:
            if r["order"] == "3" and int(r["k"]) in (0, 1, 2, 200):
                r["fmax_free_eV_A"] = {0: "25.0", 1: "70.0", 2: "40.0", 200: "40.0"}[int(r["k"])]
            if r["order"] == "1" and int(r["k"]) in (68, 69):
                r["fmax_free_eV_A"] = {68: "0.0005", 69: "0.0002"}[int(r["k"])]
        with open(os.path.join(src, "fig_s2b_fr_a_force.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLUMNS["fig_s2b_fr_a_force.csv"]); w.writeheader(); w.writerows(rows)
        # overruns in panel c: minutes per configuration above 10 (an edge arrow) and fr node-hours above 80
        for fn, edit in (("fig_s2b_fr_a_relaxations.csv", lambda r: r.update(min_per_config="12.5") if r["role"] ==
                          "V" else None), ("fig_s2b_fr_c_cost.csv", lambda r: r.update(value="95.25") if r["key"] ==
                                           "fr_node_h" else None)):
            rr = list(csv.DictReader(open(os.path.join(src, fn))))
            for r in rr:
                edit(r)
            with open(os.path.join(src, fn), "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=COLUMNS[fn]); w.writeheader(); w.writerows(rr)
        out = os.path.join(tmp, "pass", "edge")
        seen = {}

        def edge_probe(fig, ax):
            _probe(src, "edge", False)(fig, ax)
            seen.update(xmax=ax["c3"].get_xlim()[1], up=len([x for x in ax["a"].get_children() if str(
                x.get_gid()).startswith("arrow:a:")]), vals=sorted(x.get_text() for x in ax["a"].texts if str(
                    x.get_gid()).startswith("arrowval:a:")), c2=[x.get_text() for x in ax["c2"].texts if str(
                        x.get_gid()).startswith("arrowval:c2:")])
        plot(src, out, formats=("pdf", "svg", "png") if keep else ("pdf", "svg"), audit="required", probe=edge_probe)
        assert seen["xmax"] >= 95.25 * 1.12 and seen["up"] == 6 and seen["c2"] == ["12.5"] and \
            seen["vals"] == ["0.0002 eV/Å", "40 eV/Å", "70 eV/Å"], seen
        m = qa(out, required=True)
        assert m[3] == 0, ("edge", m)
        _hygiene(c46, out, src, roots)
        # in the exported PDF, the two overrun values lie in no fill but their axes' background (not inside a bar)
        lay = {p["id"]: p["bbox_pt"] for p in json.load(open(out + ".alignment.json"))["layout"]["panels"]}
        area = lambda bb: (bb[2] - bb[0]) * (bb[3] - bb[1])
        for txt_, pid in (("95.2", "c3"), ("12.5", "c2")):
            fills = _text_fills(out + ".pdf", txt_)
            assert fills and all(x >= 0.99 * area(lay[pid]) for fs in fills for x in fs), (txt_, fills, area(lay[pid]))
        qa_rows.append(("edge_arrows_and_overruns", _alignment(out), *m))
        if keep:
            for ext in ("pdf", "svg", "png", "alignment.json", "labels.alignment.json", "collision-audit.json"):
                shutil.copy(f"{out}.{ext}", os.path.join(keep, f"selftest_edge_arrows.{ext}"))
        # the layout QA fails on bad figures: a 4 pt text, overlapping texts, a panel off its row
        controls = _qa_controls(tmp, os.path.join(tmp, "pass", "source_data"))
        # broken archives and code mutants: each fails at its named need() site (or the guard or the hook raises)
        muts = _mutants(M)
        for key, sc in muts:
            root = os.path.join(tmp, "neg", "s2")
            shutil.rmtree(os.path.join(tmp, "neg"), ignore_errors=True)
            _synthetic(root, sc, wp, M)
            saved = copy.deepcopy(COLUMNS)
            if "columns" in sc:
                COLUMNS[sc["columns"][0]] = COLUMNS[sc["columns"][0]] + [sc["columns"][1]]
            undo = sc["patch"](M) if "patch" in sc else None
            try:
                with _Armed(root):
                    _expect_fail(lambda: (q47.READS.clear(), sc.get("pre", lambda M_: None)(M),
                                          build(root, os.path.join(tmp, "neg", "src"), note_of(sc),
                                                nogit if sc.get("nogit") else repos[sc.get("stop_repo", "ok")])),
                                 key, key, Blinded,
                                 sc.get("label"))
            finally:
                COLUMNS.clear(); COLUMNS.update(saved)
                if undo:
                    undo()
                q47.READS.clear()
            if key.startswith("hook:"):                   # the hook recorded what it refused
                assert _UNREAD or _UNGUARDED, key
                _UNREAD.clear(); _UNGUARDED.clear()
            assert not _OPENED and not _LISTED and not _UNGUARDED and not _UNREAD, \
                (key, _OPENED, _LISTED, _UNGUARDED, _UNREAD)
            hit[key] = hit.get(key, 0) + 1
        assert {"hook: the part output", "hook: guard bypass"} <= set(hit), "the hook mutants did not run"
        # one key per need() site, every key used, and every site shown failing
        tree = ast.parse(open(os.path.abspath(__file__)).read())
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "need"]
        sites = [n.args[1].value for n in calls if len(n.args) > 1 and isinstance(n.args[1], ast.Constant)]
        assert len(sites) == len(calls), "a need() call without a literal key"
        dup = sorted({k for k in sites if sites.count(k) > 1})
        assert not dup, f"build-assert keys used at more than one need() site: {dup}"
        assert set(sites) == set(KEYS) and len(KEYS) == len(set(KEYS)), \
            f"need() keys and KEYS differ: {sorted(set(sites) ^ set(KEYS))}"
        missing = set(KEYS) - set(hit)
        assert not missing, f"need() sites without a failing mutant: {sorted(missing)}"
        # the guard: withheld fields raise; the gate allow-list refuses result and bookkeeping fields
        g = gd.GuardedS2b({"end_rule": {"outcome": "x", "dF_200_180_meV": 1.0}, "validity_final": {"F_k0_eV": 1.0}},
                          "t")
        gl = gd.GateLeaves({"decision": {"fr_step0": {"outcome": "pass"}}, "result": {"cells": {}}, "attempt": 1}, "t")
        for bad_ in (lambda: g.get("end_rule").get("dF_200_180_meV"), lambda: str(g.get("end_rule")),
                     lambda: g.get("validity_final").open(), lambda: gl.get("result.cells"), lambda: gl.get("attempt")):
            try:
                bad_()
            except Blinded:
                continue
            raise AssertionError("the guard let a withheld read through")
        assert q47.READS["F"] == 0 and not _OPENED and not _LISTED
    finally:
        _ARMED[0], _GUARD[0] = False, None
        for dp, _, fs in os.walk(tmp):
            for f in fs:
                try:
                    os.chmod(os.path.join(dp, f), 0o600)
                except OSError:
                    pass
        shutil.rmtree(tmp, ignore_errors=True)
    assert _snapshot(HERE) == before, "the self-test wrote into the repository (figures/)"
    for nm, al, mn, verdict, nf, nw in qa_rows:
        print(f"  QA {nm}: alignment {al[0]}, labels {al[1]}; PDF text min {mn:g} pt; collision audit {verdict} "
              f"({nf} fail, {nw} warn)")
    print("  QA negative controls: " + "; ".join(c[:70] for c in controls))
    print(f"self-test passed: {len(scen)} synthetic archives (figures rendered and their marks checked against the "
          f"source data; alignment, PDF text and collision audits run; output files hygiene-checked), the panel-a "
          f"values recomputed, {n_parts} part outputs holding only the energy canary, the build-code audit, the "
          f"attempt-1, guard and part-output canaries, edge arrows and overruns, the QA negative controls, the "
          f"stop-note rule pinned against e_eval.py on {len(STOP_CASES)} synthetic notes in {len(STOP_REPOS)} "
          f"repositories (and failing when changed), the FR state and the step-0 set-aside of {len(e_parts)} stopped "
          f"archives pinned against E's route code (IX-4, IX-5, IX-11), E's route_admit refusing the 4 archives the "
          f"figure refuses before the stop note (IX-14, IX-15), E's reason words and code compiled from its source "
          f"(IX-16; failing when either side changes), "
          f"and {len(muts)} broken archives or code mutants failing at all {len(KEYS)} need() sites, the guard and the "
          f"audit hook")


def _expect_fail(fn, why, key, Blinded, label=None):
    """key: a need() key (the assert starts with '[key]'), '~text' (a plain assert of the reused C2 reader, matched by
    its message), 'withheld: ...' (the guard raises Blinded) or 'hook: text' (the audit hook raises PermissionError
    with text in its message); label: the relaxation the message must name."""
    try:
        fn()
    except Blinded as e:
        assert key.startswith("withheld"), f"{why}: the guard raised where a build assert was expected: {e}"
        return
    except PermissionError as e:
        assert key.startswith("hook:") and key[5:].strip() in str(e), \
            f"{why}: the audit hook raised where it was not expected: {e}"
        return
    except AssertionError as e:
        ok = not key.startswith(("withheld", "hook:")) and (
            key[1:] in str(e) if key.startswith("~") else str(e).startswith(f"[{key}]"))
        assert ok, f"{why}: the build failed for another reason: {e}"
        assert label is None or label in str(e), f"{why}: the failure does not name {label}: {e}"
        return
    raise AssertionError(f"the build accepted a bad archive ({why})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true"); ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--keep", default=None, help="self-test: copy the synthetic figures into this folder")
    ap.add_argument("--stop-note", default=None, help="--build after a final STOP of fr: its stop note, a normalised "
                    "repository-relative path (FG-2, IX-1)")
    a = ap.parse_args()
    if a.stop_note is not None and not a.build:
        ap.error("--stop-note belongs to --build")
    if a.self_test:
        self_test(a.keep); sys.exit(0)
    if a.build:
        build(note=a.stop_note)
    plot()
    qa(OUT)

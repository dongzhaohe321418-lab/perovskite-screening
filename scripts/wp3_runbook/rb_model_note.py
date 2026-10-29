#!/usr/bin/env python
"""WP3 runbook step 5b: draft of the dated model note (PLAN amendment m item 2, 'Model selection and stopping',
'Reporting', 'Interruptions', 'Record and model hash'; WP3_RUNBOOK.md 5b), from the training run directory and the
node work files copied next to it. The note is committed ON ITS OWN, before any test-host prediction; node_step7.sh
reads its four machine-readable lines (model_sha256, scripts_commit, run, note_status), which only a complete note
(exit 0) carries: a DRAFT has them prefixed 'draft-', so it cannot release step 7.

    python scripts/wp3_runbook/rb_model_note.py --run <MAC_STAGE>/run --node-files <MAC_STAGE> \
        --dataset results/objective2/dopant_shell/wp3/dataset \
        --out results/objective2/dopant_shell/wp3/MODEL_NOTE_<YYYY-MM-DD>.md [--m21-offset compute --threads 8]
    python scripts/wp3_runbook/rb_model_note.py --self-test

Run it from the repository root (git gives the commit of scripts 39, 40 and 41). Inputs:
  --run         <RUN> as copied from the node: wp3.model, logs/wp3_run-123.log, results/wp3_run-123_train.txt and,
                if copied, checkpoints/ (only the file names are read).
  --node-files  (default: the parent of --run) the node work files: train_command.txt, timing.txt, step34.log,
                restarts.txt and item1p_rerun.list (absent = none; checked against step34.log), versions.txt
                ('mace X', 'torch Y', 'e3nn Z' lines, from the node environment), techfail.txt or logs/techfail.txt
                (rb_techfail.py's output; library warnings before or after its own lines are ignored).
                After the item-2 retry also train_command_retry.txt and, after a technical failure of a finished run,
                logs/techfail_<failed run>.txt, or, after a deterministic abnormal end, run<j>.end and run<k>.end
                (node_step34's verdicts on the two abnormal ends; runbook 5a, WP3_RUNBOOK appendix A.5), and
                retry_causes_differ.txt if the retry itself ended abnormally more than once.
  --dataset     the scripts/33 dataset: only dataset_meta.json (basis, valid_hosts, start_check_reference) and, for
                --m21-offset compute, valid.xyz are opened.
What it records: <SHA>; the commit of scripts 39/40/41 (HEAD, which must hold them unchanged, clean, and equal to
the commit node_step34 trained at); the exact command and <T>; mace, torch and e3nn versions and the seed; every
restart and item-1' re-run with cause and time; the selected epoch with its m21 loss, RMSE_E_per_atom and RMSE_F;
the Initial values; the m21 host-wide energy offset.

Selected epoch (mace-torch 0.3.16 source, mace/tools/train.py, checkpoint.py, cli/run_train.py): after each epoch
the EMA model is evaluated on the validation set (m21) and logged to results/<name>_run-<seed>_train.txt as a JSON
line {"mode": "eval", "epoch": e, "head": "Default", "loss", "rmse_e_per_atom" (eV/atom), "rmse_f" (eV/A), ...}; the
Initial record has "epoch": null. A checkpoint checkpoints/<name>_run-<seed>_epoch-<e>.pt is saved only when the loss
is not >= the lowest so far (strict improvement; the Initial record does not set it), and --keep_checkpoints keeps
all. After the last epoch run_train loads the highest-epoch checkpoint (log: 'Loaded Stage one model from epoch <e>
for evaluation') and writes <work_dir>/wp3.model from it. This tool requires the three to agree: the log's epoch, the
highest checkpoint (if copied; the set must equal the improving epochs) and the epoch of the lowest loss by the
same strict rule.

m21 host-wide energy offset (amendment m does not define it; reading used here, to be stated in the WP3 result):
the mean over the 31 m21 validation frames of E_model - REF_energy (meV per cell; per atom beside it), the part of
the m21 energy error shared by every frame of the host, which cancels in every within-host dE_a and far-referenced
E_b (item 1c, item 5). RMSE_E_per_atom mixes it with the frame-to-frame scatter, so the RMSE with the offset removed
is given beside it. Initial: minus scripts/33 start_check_reference.mean_residual_meV (zero-shot MACE-MP-0 with
E0s.json, which is the Initial model). Selected model: needs a model evaluation, done only with --m21-offset compute:
MACE single points (float64, cpu, head Default, sha256 checked) on the frames of valid.xyz, after checking that they
are exactly the m21 frames. Without it the note is a DRAFT (exit 2).

Test-host data: never read. The tool opens no test.xyz or train.xyz, no QE output and no WP3b/MD file; it refuses
a valid.xyz holding any frame not of m21, a dataset_meta.json whose valid hosts are not [m21], a training log that
holds a test-set error table, a results file with another head, and any input path into a test archive.
Exit: 0 note written (complete); 2 note written as DRAFT (something to add or explain before commit; never commit
it; stdout says 'DRAFT -> <out>'); 1 refused, with the reason on stderr and nothing written (also: the Initial record
fails the start check, i.e. a void run; an unknown dataset basis; this tool's own errors: no --run or --out, an --out
not named MODEL_NOTE_<--date>.md, an --out that exists without --force). argparse's own usage errors (an unknown
option, a bad value) exit 2 with a 'usage:' message and write nothing. --force overwrites an existing --out (an
uncommitted note or DRAFT of the same date); a committed note is never rewritten: a new one gets a new date.
Item-2 retry (runbook 5a; item 2 'Technical failure', 'The one retry'): the selected run is the one retry when, before
it started, either (i) step34.log reports one earlier finished run and node_step34 stopped on its technical failure
('STOP: technical failure'), its 5a record kept as techfail_<run>.txt, or (ii) node_step34 stopped at a deterministic
abnormal end ('STOP: run<k>: second abnormal end': the same cause twice in succession, item 2 'Deterministic causes')
and run<k> was not discarded afterwards (a 'run<k> discarded unread' line, the PREV_CAUSE path for causes that differ,
means no retry); the two causes are run<k>.end (the second) and the restarts.txt line that node_step34's STOP line
quotes as 'earlier: ...' (the first; run<j>.end beside it if copied), never a later abnormal end of the retry itself.
Only one retry exists: (i) and (ii) together, or two such STOPs, are refused. The selected run's command is then
train_command_retry.txt, which must equal train_command.txt with '--lr 0.005' -> '--lr 0.0025' and nothing else, and
its training log must show 'Learning rate: 0.0025, weight decay: 5e-07'. Restarts of the retry itself (item-2
'Interruptions' apply to it, WP3_RUNBOOK appendix A.5) are the '4c: run<x> discarded unread <tag>' lines between the STOP
and the selected run's start: each tagged [node loss], [abnormal end] or [start check FAIL]. The same cause twice in
succession is a technical failure of the retry and there is no second retry, so every [abnormal end] of the retry
after its first is refused unless retry_causes_differ.txt states, as 'run<a> run<b>: <why>', that its cause differs
from the previous one (the note quotes it). The selected run must have trained with <T> threads (its '4c: training
started' line).
"""
import argparse, hashlib, json, math, os, re, shutil, subprocess, sys, tempfile, time

NAME, SEED_DEFAULT = "wp3", 123
SCRIPTS = ("scripts/39_wp3_evaluate.py", "scripts/40_wp3b.py", "scripts/41_wp3_md.py")
HELPERS = ("scripts/22_paired_pilot.py", "scripts/29_dopant_shell_scan.py", "scripts/30_qe_singlepoint.py",
           "scripts/32_dft_validation_analysis.py", "scripts/35_finetune_frames.py", "scripts/37_dft_eb_analysis.py",
           "scripts/38_wp2e_displacement.py", "scripts/checks.py")
FOUNDATION = "01bfe22100139f424713cf921144e5509cbe353d67aa9fa1be9c6e1e0ed35845"
MACE_VERSION = "0.3.16"
VALID_HOST, N_VALID = "m21", 31
TEST_HOSTS = ("m30", "m32", "m04", "m10", "m14", "m18", "m27")
START_CHECK = {"RMSE_F_meV_A": (79.819, 0.01), "RMSE_E_per_atom_meV": {"Eprime": (0.3334, 0.001), "raw": (0.3499, 0.001)}}
FORBIDDEN_OPTS = ("--test_file", "--test_dir", "--valid_fraction", "--pt_train_file", "--force_mh_ft_lr",
                  "--restart_latest", "--save_all_checkpoints")
FORBIDDEN_PREFIXES = ("--swa", "--lora", "--freeze")    # every option of these families (0.3.16: --swa_lr, --lora_rank,
                                                         # --lora_alpha, --freeze, ...): item 2 uses no SWA, LoRA or freezing
TECHFAIL_PASS = "no technical failure (items checked here)"
RMSE_TOL = 0.001              # meV/atom: single-point RMSE_E_per_atom vs the selected epoch's record (same model, frames)
_CALC_FACTORY = None          # self-test hook: a stub calculator instead of MACE (no model evaluation)


class Refused(Exception):
    pass


def refuse(msg):
    raise Refused(msg)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def guard(path, what):
    """No input may lead into test-host data."""
    p = os.path.abspath(path)
    parts = p.split(os.sep)
    bad = {"test.xyz", "test_extra", "wp3b", "wp3md", "wp3_eval.json", "wp3b_result.json", "wp3md_result.json"}
    if bad & set(parts) or any(x.startswith("wp3b_") or x.startswith("wp3md_") for x in parts):
        refuse(f"{what} {path}: a path into test-host data (test.xyz, item-1' archive, WP3b/MD, wp3_eval) is never read")
    return p


def read(path):
    with open(path, errors="replace") as fh:
        return fh.read()


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if p.returncode != 0:
        refuse(f"git {' '.join(args)} failed in {repo}: {p.stderr.strip()[:200]}")
    return p.stdout.strip()


def finite(x):
    return isinstance(x, (int, float)) and math.isfinite(x)


# ---------------------------------------------------------------- run directory
def results(path, tag):
    recs = []
    for i, ln in enumerate(read(path).splitlines(), 1):
        if not ln.strip():
            continue
        try:
            r = json.loads(ln)
        except ValueError as e:
            refuse(f"{path} line {i}: not JSON ({e})")
        recs.append(r)
    for r in recs:
        if not finite(r.get("loss")):
            refuse(f"{path}: non-finite loss (mode {r.get('mode')}, epoch {r.get('epoch')}): a technical failure "
                   "(item 2, 5a); no model note")
    ev = [r for r in recs if r.get("mode") == "eval"]
    heads = {r.get("head") for r in ev}
    if heads != {"Default"}:
        refuse(f"{path}: eval records of heads {sorted(map(str, heads))}; only the m21 validation head 'Default' is read")
    if {r.get("mode") for r in recs} - {"eval", "opt"}:
        refuse(f"{path}: records of modes {sorted({r.get('mode') for r in recs} - {'eval', 'opt'})}")
    init = [r for r in ev if r.get("epoch") is None]
    if len(init) != 1 or ev[0] is not init[0]:
        refuse(f"{path}: {len(init)} Initial (epoch null) records, or not the first eval record")
    eps = [r for r in ev if r.get("epoch") is not None]
    if [r["epoch"] for r in eps] != list(range(len(eps))):
        refuse(f"{path}: eval epochs are not 0, 1, 2, ... in order")
    for r in ev:
        for k in ("rmse_e_per_atom", "rmse_f"):
            if not finite(r.get(k)):
                refuse(f"{path}: eval epoch {r.get('epoch')} has no finite {k}")
    lowest, sel, improved = math.inf, None, []
    for r in eps:                                  # mace/tools/train.py: 'if valid_loss >= lowest_loss' = no checkpoint
        if not r["loss"] >= lowest:
            lowest, sel = r["loss"], r
            improved.append(r["epoch"])
    if sel is None:
        refuse(f"{path}: no epoch evaluated")
    return init[0], sel, improved, eps


def training_log(path):
    t = read(path)
    if "Error-table on TEST" in t:
        refuse(f"{path} holds a test-set error table: a run given a test set is outside item 2, and its values are "
               "never read")
    v = re.findall(r"MACE version: (\S+)", t)
    loaded = re.findall(r"Loaded Stage one model from epoch (\S+) for evaluation", t)
    if "Stage two" in t or "Stage Two" in t:
        refuse(f"{path}: a stage-two (SWA) model; item 2 uses none")
    if len(set(v)) != 1:
        refuse(f"{path}: MACE version lines {v}")
    if len(loaded) != 1 or not loaded[0].isdigit():
        refuse(f"{path}: 'Loaded Stage one model from epoch <e>' lines {loaded}: wp3.model's epoch is unknown")
    fm = re.findall(r"Using foundation model (\S+) as initial checkpoint", t)
    row = re.findall(r"\|\s*valid_Default\s*\|\s*([-\d.]+)\s*\|\s*([-\d.]+)\s*\|", t)
    lrs = sorted(set(re.findall(r"Learning rate: (\S+), weight decay: (\S+)", t)))
    return {"mace_version": v[0], "loaded_epoch": int(loaded[0]), "foundation": fm[-1] if fm else None,
            "valid_row": row[-1] if row else None, "lr_lines": lrs}


def checkpoints(d, tag):
    if not os.path.isdir(d):
        return None
    eps = []
    for f in os.listdir(d):
        if f.endswith("_swa.pt"):
            refuse(f"{d}/{f}: an SWA checkpoint; item 2 uses no SWA")
        m = re.fullmatch(re.escape(tag) + r"_epoch-(\d+)\.pt", f)
        if m:
            eps.append(int(m.group(1)))
    return sorted(eps)


# ---------------------------------------------------------------- node work files
def retry_command(nf, cmd):
    """train_command_retry.txt: the item-2 command with --lr 0.0025 instead of --lr 0.005 and nothing else."""
    rp = os.path.join(nf, "train_command_retry.txt")
    if not os.path.exists(rp):
        refuse("train_command_retry.txt (the retry's exact command) is missing")
    rc = read(rp).strip()
    if cmd.count("--lr 0.005 ") != 1 or rc != cmd.replace("--lr 0.005 ", "--lr 0.0025 "):
        refuse("train_command_retry.txt must equal train_command.txt with '--lr 0.005' replaced by '--lr 0.0025' and "
               "nothing else changed (item 2, the one retry)")
    return rc


def dae_stops(s34, run_path):
    """node_step34's 'STOP: run<k>: second abnormal end' lines before the selected run started, for runs that were not
    discarded afterwards (a 'run<k> discarded unread' line after the STOP is the PREV_CAUSE path: the causes differed,
    a restart, no retry). Returns {run<k>: (line index in step34.log, the STOP line)}."""
    d = {}
    for i, ln in enumerate(s34.splitlines()):
        if "4c: training started" in ln and ln.split()[-1] == run_path:
            break
        m = re.search(r"\] STOP: (run\d+): second abnormal end", ln)
        if m:
            d[m.group(1)] = (i, ln.strip())
        m = re.search(r"\] 4c: (run\d+) discarded unread ", ln)
        if m:
            d.pop(m.group(1), None)
    return d


RETRY_TAGS = ("[node loss]", "[abnormal end]", "[start check FAIL]")


def retry_restarts(nf, s34, i0, run_path):
    """The discarded runs of the one retry: the '4c: run<x> discarded unread <tag>' lines after node_step34's STOP line
    (index i0) and before the selected run started. Item-2 'Interruptions' apply to the retry (WP3_RUNBOOK appendix A.5):
    each is [node loss], [abnormal end] or [start check FAIL]; the same cause twice in succession is a technical failure
    of the retry, with no second retry. node_step34 stops at every second [abnormal end]; for the retry, run by hand,
    each [abnormal end] after the first needs the operator's statement in retry_causes_differ.txt, one line
    'run<a> run<b>: <why the causes differ>' per pair of successive [abnormal end] discards."""
    L = s34.splitlines()
    end = next(i for i, ln in enumerate(L) if "4c: training started" in ln and ln.split()[-1] == run_path)
    disc = []
    for ln in L[i0 + 1:end]:
        m = re.search(r"\] 4c: (run\d+) discarded unread (\[[^\]]*\])", ln)
        if m:
            disc.append((m.group(1), m.group(2), ln.strip()))
    bad = [d for d in disc if d[1] not in RETRY_TAGS]
    if bad:
        refuse(f"the retry run {bad[0][0]} was discarded as {bad[0][1]}: a retry run is discarded only as [node loss], "
               "[abnormal end] or [start check FAIL] (WP3_RUNBOOK appendix A.5)")
    ae = [d[0] for d in disc if d[1] == "[abnormal end]"]
    pairs = list(zip(ae, ae[1:]))
    said, p = {}, os.path.join(nf, "retry_causes_differ.txt")
    if os.path.exists(p):
        for ln in read(p).splitlines():
            if ln.strip():
                m = re.fullmatch(r"(run\d+) (run\d+): (\S.*)", ln.strip())
                if not m:
                    refuse(f"retry_causes_differ.txt: {ln.strip()[:80]!r} is not 'run<a> run<b>: <why the causes differ>'")
                said[(m.group(1), m.group(2))] = m.group(3)
    miss = [x for x in pairs if x not in said]
    if miss:
        refuse(f"the one retry ended abnormally twice in succession ({miss[0][0]}, then {miss[0][1]}): the same cause twice "
               "is a technical failure of the retry, and there is no second retry (criterion 6 'not met (no fine-tuned "
               "model)'); if the two causes differ, the operator states why in retry_causes_differ.txt as "
               f"'{miss[0][0]} {miss[0][1]}: <why>' (WP3_RUNBOOK appendix A.5)")
    extra = [x for x in said if x not in pairs]
    if extra:
        refuse(f"retry_causes_differ.txt names {extra[0][0]} {extra[0][1]}, which are not two successive [abnormal end] "
               "discards of the retry")
    return {"discards": [d[2] for d in disc], "differ": [(a, b, said[(a, b)]) for a, b in pairs]}


def retry_dae(nf, s34, k, stop, run_path, cmd, restarts):
    """The item-2 retry after a deterministic abnormal end (runbook 5a, 4e): node_step34 stopped at the second
    [abnormal end] in succession, the operator judged the two causes the same (a technical failure) and ran the one
    retry by hand. The causes: run<k>.end (node_step34's verdict on the second) and the restarts.txt line that the
    STOP line quotes as 'earlier: <line>' (the first; run<j>.end beside it if copied). A later [abnormal end] of the
    retry itself is never taken for the first of the pair."""
    i0, stop_line = stop
    ef = next((p for p in (os.path.join(nf, f"{k}.end"), os.path.join(nf, "logs", f"{k}.end")) if os.path.exists(p)), None)
    end = read(ef).strip() if ef else ""
    if not end.startswith("[abnormal end]"):
        refuse(f"{k}.end (node_step34's verdict on the second abnormal end, copied from <NODE_WORK>) is missing or is not "
               "an '[abnormal end]': the deterministic cause of the item-2 retry cannot be named")
    first = [x for x in restarts if "[abnormal end]" in x and f"; earlier: {x}). The same cause twice" in stop_line]
    if not first:
        refuse(f"node_step34's 'STOP: {k}: second abnormal end' line quotes no [abnormal end] line of restarts.txt as its "
               "'earlier:' cause: the first of the two deterministic ends cannot be named")
    j = first[-1].split()[1] if len(first[-1].split()) > 1 else "?"
    jf = os.path.join(nf, f"{j}.end")
    return {"kind": "dae", "failed_run": k, "stop_line": stop_line, "end_file": os.path.basename(ef), "end": end,
            "earlier": first[-1], "earlier_run": j, "earlier_end": read(jf).strip() if os.path.exists(jf) else None,
            "cmd": retry_command(nf, cmd), **retry_restarts(nf, s34, i0, run_path)}


def techfail_verdict(path, run_path):
    """rb_techfail.py's verdict on <run_path>/wp3.model in a 5a file: 'pass', 'fail' or None (no verdict), with
    rb_techfail's own lines. node_step34 writes the file with 2>&1, and in the node's mace environment library warnings
    (stderr) and mace's own import notice stand before rb_techfail's lines; warnings may also follow them. Only its
    own lines count: exactly one '<N> m21 frames evaluated with <run_path>/wp3.model', then on the next line its pass
    line ('pass', if no line of the file is a 'non-finite ...' line) or its first 'non-finite ...' line ('fail', if no
    line is the pass line). node_step7.sh (tf_verdict) reads the file the same way: lines end at '\\n' only (a '\\r' stays
    part of its line, as in awk)."""
    with open(path, errors="replace", newline="") as fh:     # no newline translation: a '\r' is not a line end
        L = fh.read().split("\n")
    if L and L[-1] == "":
        L.pop()
    head = re.compile(r"[0-9]+ m21 frames evaluated with " + re.escape(run_path) + r"/wp3\.model")
    at = [i for i, x in enumerate(L) if head.fullmatch(x)]
    if len(at) != 1:
        return None, []
    i = at[0]
    nxt = L[i + 1] if i + 1 < len(L) else ""
    any_nf, any_pass = any(x.startswith("non-finite") for x in L), TECHFAIL_PASS in L
    if nxt == TECHFAIL_PASS and not any_nf:
        return "pass", L[i:i + 2]
    if nxt.startswith("non-finite") and not any_pass:
        k = i + 1
        while k < len(L) and L[k].startswith("non-finite"):
            k += 1
        return "fail", L[i:k]
    return None, L[i:i + 1]


def retry_of(nf, s34, other, run_path, cmd):
    """The item-2 retry (runbook 5a): the earlier finished run `other` failed the technical-failure check, node_step34
    stopped on it before `run_path` started, its 5a record is kept, and the retry's command differs only in --lr."""
    seen_fin = seen_stop = ok = False
    stop_line, i0 = "", None
    for i, ln in enumerate(s34.splitlines()):
        if f"4: training finished in {other};" in ln:
            seen_fin = True
        elif seen_fin and not ok and "] STOP: technical failure" in ln:
            seen_stop, stop_line, i0 = True, ln, i
        elif "4c: training started" in ln and ln.split()[-1] == run_path and seen_stop:
            ok = True
    if not ok:
        refuse(f"step34.log reports the finished run {other} besides {run_path}, but no 'STOP: technical failure' after it "
               "and before the selected run started: only the item-2 retry may follow a finished run")
    tf = next((p for p in (os.path.join(nf, "logs", f"techfail_{os.path.basename(other)}.txt"),
                           os.path.join(nf, f"techfail_{os.path.basename(other)}.txt")) if os.path.exists(p)), None)
    verdict, lines = techfail_verdict(tf, other) if tf else (None, [])
    if verdict != "fail":
        refuse(f"techfail_{os.path.basename(other)}.txt (the 5a record of the failed run {other}: rb_techfail.py's 'with "
               f"{other}/wp3.model' line, then its 'non-finite' lines) is missing or does not show the failure")
    return {"kind": "techfail", "failed_run": other, "stop_line": stop_line.strip(), "techfail_file": tf,
            "techfail": lines[:6], "cmd": retry_command(nf, cmd), **retry_restarts(nf, s34, i0, run_path)}


def node_files(nf, run_model_sha):
    s34 = read(os.path.join(nf, "step34.log"))
    fin = sorted(set(re.findall(r"\] 4: training finished in ([^;]+); wp3\.model sha256 ([0-9a-f]{64});", s34)))
    sel = [f for f in fin if f[1] == run_model_sha]
    if len(sel) != 1 or len({f[1] for f in fin if f[0] == sel[0][0]}) != 1:
        refuse(f"step34.log: {len(sel)} 'training finished in' lines with the --run copy's sha256 {run_model_sha} "
               f"(all: {[(os.path.basename(r), s[:12]) for r, s in fin]}); exactly one selected run is expected")
    run_path, sha_log = sel[0]
    others = sorted({f[0] for f in fin} - {run_path})
    if len(others) > 1:
        refuse(f"step34.log reports the finished runs {others} besides {run_path}: at most one (the item-2 retry's failed "
               "run) is allowed")
    train_commit, t_start = None, None
    for ln in s34.splitlines():
        m = re.search(r"\] start; repo (\S+)", ln)
        if m:
            train_commit = m.group(1)
        if "4c: training started" in ln and ln.split()[-1] == run_path:
            t_start = train_commit
    if not t_start:
        refuse(f"step34.log: no 'start; repo' line before the training of {run_path}")
    rows = []
    for ln in read(os.path.join(nf, "timing.txt")).split("\n"):
        if ln.strip():
            a, b = ln.split()
            rows.append((int(a), int(b)))
    if [r[0] for r in rows] != [8, 16, 32]:
        refuse(f"timing.txt holds {rows}, not exactly the 8, 16 and 32 thread runs")
    T = sorted(rows, key=lambda r: (r[1], r[0]))[0][0]              # fastest; equal wall times: fewer threads
    tlog = re.findall(r"4b: timing .*-> T=(\d+)", s34)
    if tlog and int(tlog[-1]) != T:
        refuse(f"timing.txt gives T={T}, step34.log chose T={tlog[-1]}")
    t_sel = [re.search(r", threads (\d+), run ", ln) for ln in s34.splitlines()
             if "4c: training started" in ln and ln.split()[-1] == run_path]
    if not t_sel or not t_sel[0] or int(t_sel[0].group(1)) != T:
        refuse(f"the '4c: training started' line of {run_path} does not show threads {T} (timing.txt's <T>; item 2: "
               "nothing else changed)")
    cmd = read(os.path.join(nf, "train_command.txt")).strip()
    if cmd.count("\n") or "--work_dir <run>" not in cmd:
        refuse("train_command.txt must hold the one item-2 command line ending in '--work_dir <run>'")
    bad = [o for o in FORBIDDEN_OPTS if re.search(r"(^|\s)" + re.escape(o) + r"(\s|=|$)", cmd)]
    bad += re.findall(r"(?:^|\s)((?:" + "|".join(map(re.escape, FORBIDDEN_PREFIXES)) + r")\w*)(?=\s|=|$)", cmd)
    if bad:
        refuse(f"train_command.txt uses {bad}, which item 2 excludes")
    restarts = []
    if os.path.exists(os.path.join(nf, "restarts.txt")):
        restarts = [x for x in read(os.path.join(nf, "restarts.txt")).splitlines() if x.strip()]
    dae = dae_stops(s34, run_path)
    if others and dae:
        refuse(f"step34.log shows both a finished run besides {run_path} ({others}) and a deterministic abnormal end "
               f"({sorted(dae)}) before it: item 2 allows one retry only")
    if len(dae) > 1:
        refuse(f"step34.log has 'second abnormal end' STOPs for {sorted(dae)} before {run_path} (none discarded after "
               "it): item 2 allows one retry only")
    retry = (retry_of(nf, s34, others[0], run_path, cmd) if others else
             retry_dae(nf, s34, *next(iter(dae.items())), run_path, cmd, restarts) if dae else None)
    if retry:
        cmd = retry["cmd"]
    seed = re.findall(r"--seed (\d+)", cmd)
    lr = re.findall(r"--lr (\S+)", cmd)
    n_disc = len(re.findall(r"\] 4c: run\d+ discarded unread ", s34))
    if n_disc != len(restarts):
        refuse(f"restarts.txt has {len(restarts)} line(s), step34.log logs {n_disc} discarded run(s)")
    if any(x.split()[1:2] == [os.path.basename(run_path)] for x in restarts):
        refuse(f"the selected {run_path} is listed as discarded in restarts.txt")
    item1p = []
    if os.path.exists(os.path.join(nf, "item1p_rerun.list")):
        item1p = [x for x in read(os.path.join(nf, "item1p_rerun.list")).splitlines() if x.strip()]
    n1p = re.findall(r"item-1' re-runs and resubmissions: (\d+)", s34)
    if n1p and int(n1p[-1]) != len(item1p):
        refuse(f"item1p_rerun.list has {len(item1p)} line(s), step34.log reports {n1p[-1]}")
    vers = {}
    vp = os.path.join(nf, "versions.txt")
    if os.path.exists(vp):
        for ln in read(vp).splitlines():
            if len(ln.split()) == 2:
                vers[ln.split()[0]] = ln.split()[1]
    tf = next((p for p in (os.path.join(nf, "techfail.txt"), os.path.join(nf, "logs", "techfail.txt")) if os.path.exists(p)), None)
    techfail = None
    if tf:
        verdict, lines = techfail_verdict(tf, run_path)
        techfail = {"file": tf, "pass": verdict == "pass", "lines": lines[:6]}
    return {"run_path": run_path, "train_commit": t_start, "T": T, "timing": rows, "cmd": cmd, "seed": seed,
            "lr": lr, "restarts": restarts, "item1p": item1p, "versions": vers, "techfail": techfail, "retry": retry,
            "s34_5a": TECHFAIL_PASS in s34.split(f"training finished in {run_path};", 1)[1]}


# ---------------------------------------------------------------- m21 offset (optional model evaluation)
def m21_frames(ds):
    from ase.io import read as aread
    frames = aread(os.path.join(ds, "valid.xyz"), ":")
    hosts = sorted({str(a.info.get("host")) for a in frames})
    labs = [str(a.info.get("label", "")) for a in frames]
    if hosts != [VALID_HOST] or not all(x.startswith(VALID_HOST + "_") for x in labs):
        refuse(f"valid.xyz holds frames of hosts {hosts} (labels {sorted({x.split('_')[0] for x in labs})}): only the "
               f"{VALID_HOST} frames are ever evaluated; nothing evaluated")
    if any(x.split("_")[0] in TEST_HOSTS for x in labs):
        refuse("valid.xyz holds a test-host label; nothing evaluated")
    if len(frames) != N_VALID:
        refuse(f"valid.xyz holds {len(frames)} frames, not the {N_VALID} m21 frames; nothing evaluated")
    return frames


def m21_offset(ds, model, sha, threads):
    frames = m21_frames(ds)                       # checked before any model is loaded
    if _CALC_FACTORY is not None:
        calc, how = _CALC_FACTORY(), "SELF-TEST STUB calculator (no model evaluation)"
    else:
        if sha256(model) != sha:
            refuse(f"{model}: sha256 changed")
        import torch
        torch.set_num_threads(threads)
        from mace.calculators import MACECalculator
        calc = MACECalculator(model_paths=[model], device="cpu", default_dtype="float64", head="Default")
        if calc.head != "Default" or not all(p.dtype == torch.float64 for m in calc.models for p in m.parameters()):
            refuse("the model has no head 'Default' or is not float64")
        how = f"MACECalculator(device='cpu', default_dtype='float64', head='Default'), {threads} threads"
    d, n = [], []
    for a in frames:
        b = a.copy(); b.calc = calc
        e = float(b.get_potential_energy())
        if not math.isfinite(e):
            refuse(f"{a.info['label']}: non-finite model energy (a technical failure, 5a)")
        d.append(e - float(a.info["REF_energy"])); n.append(len(a))
    k = len(d)
    pa = [x / y for x, y in zip(d, n)]
    mpa = sum(pa) / k
    return {"how": how, "n": k, "offset_meV_per_cell": 1000 * sum(d) / k, "offset_meV_per_atom": 1000 * mpa,
            "rmse_e_per_atom_meV": 1000 * math.sqrt(sum(x * x for x in pa) / k),
            "rmse_e_per_atom_offset_removed_meV": 1000 * math.sqrt(sum((x - mpa) ** 2 for x in pa) / k),
            "sd_meV_per_cell": 1000 * math.sqrt(sum((x - sum(d) / k) ** 2 for x in d) / k)}


# ---------------------------------------------------------------- note
def build(a):
    run = guard(a.run, "--run")
    nf = guard(a.node_files or os.path.dirname(run.rstrip("/")), "--node-files")
    ds = guard(a.dataset, "--dataset")
    if not os.path.isdir(ds):
        refuse(f"--dataset {a.dataset} is not the scripts/33 dataset directory")
    repo = os.path.abspath(a.repo)
    model = os.path.join(run, "wp3.model")
    sha = sha256(model)
    if sha == FOUNDATION:
        refuse("wp3.model is the zero-shot foundation file")
    tag = f"{NAME}_run-{SEED_DEFAULT}"
    init, sel, improved, eps = results(os.path.join(run, "results", f"{tag}_train.txt"), tag)
    lg = training_log(os.path.join(run, "logs", f"{tag}.log"))
    ck = checkpoints(os.path.join(run, "checkpoints"), tag)
    if lg["loaded_epoch"] != sel["epoch"]:
        refuse(f"the log loaded epoch {lg['loaded_epoch']}, the lowest m21 loss (strict rule) is epoch {sel['epoch']}")
    if ck is not None and (ck != improved or ck[-1] != lg["loaded_epoch"]):
        refuse(f"checkpoints {ck} are not the improving epochs {improved} ending at the loaded epoch {lg['loaded_epoch']}")
    if lg["mace_version"] != MACE_VERSION:
        refuse(f"the training log shows MACE version {lg['mace_version']}, not {MACE_VERSION}")
    n = node_files(nf, sha)
    want_lr = ("0.0025" if n["retry"] else "0.005", "5e-07")
    if (n["retry"] and want_lr not in lg["lr_lines"]) or any(x != want_lr for x in lg["lr_lines"]):
        refuse(f"the training log's 'Learning rate: <lr>, weight decay: <wd>' lines {lg['lr_lines']} are not "
               f"{want_lr}" + (" (item 2: the retry's log must show 'Learning rate: 0.0025, weight decay: 5e-07')"
                               if n["retry"] else ""))
    if n["seed"] != [str(SEED_DEFAULT)]:
        refuse(f"the command's --seed is {n['seed']}, not the item-2 seed {SEED_DEFAULT} (results tag {tag})")
    meta = json.load(open(os.path.join(ds, "dataset_meta.json")))
    if meta.get("valid_hosts") != [VALID_HOST]:
        refuse(f"dataset_meta.json valid_hosts {meta.get('valid_hosts')}, not ['{VALID_HOST}']")
    basis, scr = meta.get("basis"), meta.get("start_check_reference") or {}
    sc_f, sc_e = START_CHECK["RMSE_F_meV_A"], START_CHECK["RMSE_E_per_atom_meV"].get(basis)
    if sc_e is None:
        refuse(f"dataset_meta.json basis {basis!r} is not one of {sorted(START_CHECK['RMSE_E_per_atom_meV'])}: the start "
               "check (item 2) cannot be applied")
    i_e, i_f = 1000 * init["rmse_e_per_atom"], 1000 * init["rmse_f"]
    if not (abs(i_f - sc_f[0]) <= sc_f[1] and abs(i_e - sc_e[0]) <= sc_e[1]):
        refuse(f"the Initial record fails the start check (item 2, basis {basis}): RMSE_F {i_f:.3f} vs {sc_f[0]} +/- "
               f"{sc_f[1]} meV/A, RMSE_E_per_atom {i_e:.4f} vs {sc_e[0]} +/- {sc_e[1]} meV/atom. The run is void, its "
               "outputs are not used and it is never evaluated on a test host: no model note")
    # git: HEAD holds scripts 39/40/41 (and the helpers 40/41 load) clean, and as they were at training
    head = git(repo, "rev-parse", "HEAD")
    dirty = git(repo, "status", "--porcelain", "--", *SCRIPTS, *HELPERS)
    if dirty:
        refuse(f"uncommitted changes to scripts 39/40/41 or their helpers:\n{dirty}")
    tc = git(repo, "rev-parse", "--verify", n["train_commit"] + "^{commit}")
    if subprocess.run(["git", "-C", repo, "diff", "--quiet", tc, head, "--", *SCRIPTS, *HELPERS]).returncode != 0:
        refuse(f"scripts 39/40/41 or their helpers changed between the training commit {tc[:12]} and HEAD {head[:12]}")
    files = {f: {"sha256": sha256(os.path.join(repo, f)), "last_commit": git(repo, "log", "-1", "--format=%H", "--", f)}
             for f in SCRIPTS}
    vers = dict(n["versions"])
    if a.versions_from_env:
        import mace, torch, e3nn
        vers = {"mace": mace.__version__, "torch": torch.__version__, "e3nn": e3nn.__version__,
                "source": f"interpreter {sys.executable}"}
    if vers.get("mace") and vers["mace"] != lg["mace_version"]:
        refuse(f"versions give mace {vers['mace']}, the training log {lg['mace_version']}")
    off = m21_offset(ds, model, sha, a.threads) if a.m21_offset == "compute" else None
    draft = []
    if off is None:
        draft.append("m21 host-wide energy offset of the selected model not computed (run with --m21-offset compute)")
    if not all(vers.get(k) for k in ("mace", "torch", "e3nn")):
        draft.append("torch / e3nn versions missing (versions.txt from the node environment, or --versions-from-env there)")
    if not (n["techfail"] and n["techfail"]["pass"]) and not n["s34_5a"]:
        draft.append("no passed technical-failure check (5a) found for this run")
    if off and abs(off["rmse_e_per_atom_meV"] - 1000 * sel["rmse_e_per_atom"]) > RMSE_TOL:
        draft.append(f"the single-point RMSE_E_per_atom differs from the selected epoch's record by "
                     f"{off['rmse_e_per_atom_meV'] - 1000 * sel['rmse_e_per_atom']:+.5f} meV/atom (wrong model or frames?)")
    return render(a, sha, run, n, init, sel, improved, eps, lg, ck, basis, scr, head, tc, files, vers, off, draft), draft


def fmt(x, d=4):
    return "n/a" if x is None else f"{x:.{d}f}"


def render(a, sha, run, n, init, sel, improved, eps, lg, ck, basis, scr, head, tc, files, vers, off, draft):
    rn = os.path.basename(n["run_path"])
    cmd = f"OMP_NUM_THREADS={n['T']} " + n["cmd"].replace("--work_dir <run>", f"--work_dir {n['run_path']}")
    sc_f, sc_e = START_CHECK["RMSE_F_meV_A"], START_CHECK["RMSE_E_per_atom_meV"][basis]   # basis checked in build()
    i_e, i_f = 1000 * init["rmse_e_per_atom"], 1000 * init["rmse_f"]
    s_e, s_f = 1000 * sel["rmse_e_per_atom"], 1000 * sel["rmse_f"]
    i_off = -scr["mean_residual_meV"] if finite(scr.get("mean_residual_meV")) else None
    L = []
    if draft:
        L += ["> **DRAFT: not ready to commit.** Missing: " + "; ".join(draft) + ".", ""]
    L += [f"# WP3 model note, {a.date}", "",
          "PLAN amendment m item 2 ('Record and model hash', 'Reporting'); WP3_RUNBOOK.md 5b. Committed on its own, "
          "before any test-host prediction (criterion 6, WP3b or MD). Generated by "
          f"`scripts/wp3_runbook/rb_model_note.py` (sha256 {sha256(os.path.abspath(__file__))[:16]}...).", "",
          *(["Machine-readable (node_step7.sh reads these four lines; do not edit them):", "", "```text",
             f"model_sha256: {sha}", f"scripts_commit: {head}", f"run: {rn}", "note_status: complete", "```", ""]
            if not draft else
            ["Machine-readable lines: none in a DRAFT (node_step7.sh refuses this file). For reference only:", "",
             "```text", f"draft-model_sha256: {sha}", f"draft-scripts_commit: {head}", f"draft-run: {rn}", "```", ""]),
          "## Model", "",
          f"- `wp3.model` of `{n['run_path']}` (the run that `step34.log` reports as 'training finished in'): "
          f"sha256 `{sha}` ({os.path.getsize(os.path.join(run, 'wp3.model'))} bytes).",
          f"- Foundation model: `{lg['foundation']}` (sha256 checked by node_step34: {FOUNDATION}).", "",
          "## Scripts", "",
          f"- Commit of scripts 39, 40 and 41: `{head}` (HEAD when this note was generated; clean). The training ran at "
          f"`{tc}`; scripts 39/40/41 and the helpers 40/41 load are identical there.",
          *[f"  - `{f}`: sha256 `{v['sha256']}`, last changed in `{v['last_commit']}`" for f, v in files.items()], "",
          "## Command, threads, versions, seed", "",
          f"- Exact command (as node_step34 ran it in `{rn}`):", "", "```text", cmd, "```", "",
          f"- <T> = {n['T']} threads: timing run (2 epochs) " + ", ".join(f"{t} threads {s} s" for t, s in n["timing"])
          + "; fastest, equal wall times to fewer threads.",
          f"- Versions: mace {vers.get('mace', 'n/a')} (training log: 'MACE version: {lg['mace_version']}'), torch "
          f"{vers.get('torch', 'n/a')}, e3nn {vers.get('e3nn', 'n/a')}" + (f" ({vers['source']})" if vers.get("source") else
                                                                          " (versions.txt from the node environment)") + ".",
          f"- Seed: {n['seed'][0]} (`--seed`; results tag `{NAME}_run-{SEED_DEFAULT}`); learning rate {n['lr'][0] if n['lr'] else 'n/a'}.",
          "", "## Restarts (item 2 'Interruptions'; restarts.txt)", ""]
    L += [f"- `{x}`" for x in n["restarts"]] or ["- none"]
    L += ["", "## Item-1' re-runs and resubmissions (item1p_rerun.list)", ""]
    L += [f"- `{x}`" for x in n["item1p"]] or ["- none"]
    rt = n["retry"]
    L += ["", "## Technical failure and the one retry (item 2)", ""]
    if rt and rt["kind"] == "techfail":
        L += [f"- `{rt['failed_run']}` failed the technical-failure check (5a): " + " / ".join(rt["techfail"][1:4])
              + f" (`{os.path.basename(rt['techfail_file'])}`; step34.log: `{rt['stop_line'][:200]}`)."]
    elif rt:
        L += [f"- Deterministic abnormal end (item 2 'Interruptions', 'Deterministic causes'; a technical failure): the "
              f"identical command ended abnormally twice in succession, `{rt['earlier_run']}` and then "
              f"`{rt['failed_run']}`, with the same cause. node_step34 stopped (step34.log: `{rt['stop_line'][:240]}`).",
              f"  - first ({rt['earlier_run']}, restarts.txt): `{rt['earlier'][:240]}`"
              + (f"; `{rt['earlier_run']}.end`: `{rt['earlier_end'][:200]}`" if rt["earlier_end"] else ""),
              f"  - second (`{rt['end_file']}`): `{rt['end'][:240]}`",
              "  - The operator judged the two causes the same, so the run counts as a technical failure and was "
              "retried once by hand (WP3_RUNBOOK appendix A.5); had they differed, node_step34 would have been relaunched "
              "with PREV_CAUSE (a restart, not the retry)."]
    if rt:
        L += [f"- `{n['run_path']}` is the one retry: the identical command with `--lr 0.0025` instead of `--lr 0.005` "
              "(train_command_retry.txt; the training log shows 'Learning rate: 0.0025, weight decay: 5e-07'). A second "
              "failure would leave criterion 6 'not met (no fine-tuned model)'; there is no second retry."]
        if rt["discards"]:
            L += ["- Runs of the retry discarded unread before it (item 2 'Interruptions'; step34.log, by hand, "
                  "WP3_RUNBOOK appendix A.5):"] + [f"  - `{x[:260]}`" for x in rt["discards"]]
        L += [f"  - `{a_}` and `{b_}` both ended abnormally; the operator stated that their causes differ "
              f"(retry_causes_differ.txt): {why}" for a_, b_, why in rt["differ"]]
    else:
        L += ["- none (no technical failure before the selected run: it is not a retry)"]
    L += ["", "## Selected epoch and Initial values (m21, item 2 'Model selection' and 'Reporting')", "",
          f"`wp3.model` is the epoch-{sel['epoch']} checkpoint: the log says 'Loaded Stage one model from epoch "
          f"{lg['loaded_epoch']} for evaluation'; it is the highest-epoch checkpoint"
          + (f" (checkpoints {ck})" if ck is not None else " (checkpoint files not in the copy; checked from the log and "
             "the results file)") + f", and the epoch of the lowest m21 validation loss among the {len(eps)} epochs "
          f"(strict improvement, as mace-torch 0.3.16 saves them; improving epochs {improved}).", "",
          "| | epoch | m21 loss | RMSE_E_per_atom (meV/atom) | RMSE_F (meV/A) | host-wide offset, model - REF (meV/cell) |",
          "|---|---|---|---|---|---|",
          f"| Initial (before any optimiser step) | null | {init['loss']:.6g} | {i_e:.4f} | {i_f:.3f} | {fmt(i_off, 2)} |",
          f"| Selected | {sel['epoch']} | {sel['loss']:.6g} | {s_e:.4f} | {s_f:.3f} | "
          f"{fmt(off['offset_meV_per_cell'], 2) if off else 'not computed'} |", ""]
    L += [f"- Start check (item 2, basis {basis}): RMSE_F {i_f:.3f} vs {sc_f[0]} +/- {sc_f[1]}; RMSE_E_per_atom "
          f"{i_e:.4f} vs {sc_e[0]} +/- {sc_e[1]}: PASS (a FAIL is refused: a void run gets no note). scripts/33 "
          f"reference: {fmt(scr.get('RMSE_E_per_atom_meV'), 6)} meV/atom, {fmt(scr.get('RMSE_F_meV_A'), 5)} meV/A."]
    if lg["valid_row"]:
        L += [f"- Final error table of the training log, valid_Default (rounded by mace): RMSE E {lg['valid_row'][0]} "
              f"meV/atom, RMSE F {lg['valid_row'][1]} meV/A."]
    if sel["loss"] > init["loss"]:
        L += ["- The selected model's m21 loss is above the Initial loss: reported as such and still evaluated (item 2)."]
    L += ["", "## m21 host-wide energy offset", "",
          "Reading (amendment m names it in item 2 'Reporting' without defining it): the mean over the 31 m21 frames of "
          "E_model - REF_energy, the part of the m21 energy error shared by every frame of the host; it cancels in every "
          "within-host dE_a and far-referenced E_b (items 1c and 5). RMSE_E_per_atom mixes it with the frame-to-frame "
          "scatter, so the RMSE with the offset removed is given beside it. m21 only; no test host.", "",
          f"- Initial: {fmt(i_off, 3)} meV/cell = minus scripts/33 `start_check_reference.mean_residual_meV` "
          f"({fmt(scr.get('mean_residual_meV'), 3)}, REF - model; zero-shot MACE-MP-0 with E0s.json, the Initial model)."]
    if off:
        L += [f"- Selected model: {off['offset_meV_per_cell']:.3f} meV/cell ({off['offset_meV_per_atom']:.5f} meV/atom; "
              f"SD over frames {off['sd_meV_per_cell']:.3f} meV/cell), from {off['n']} single points ({off['how']}) on "
              "valid.xyz.",
              f"- RMSE_E_per_atom from these single points {off['rmse_e_per_atom_meV']:.5f} meV/atom (results file: "
              f"{s_e:.5f}); with the offset removed {off['rmse_e_per_atom_offset_removed_meV']:.5f} meV/atom."]
        if abs(off["rmse_e_per_atom_meV"] - s_e) > RMSE_TOL:
            L += [f"- **Check:** the single-point RMSE_E_per_atom differs from the selected epoch's record by "
                  f"{off['rmse_e_per_atom_meV'] - s_e:+.5f} meV/atom (expected about 0: same model, same 31 frames). "
                  "Find out why before committing (this makes the note a DRAFT)."]
    else:
        L += ["- Selected model: NOT COMPUTED (needs `--m21-offset compute`: MACE single points on the 31 m21 frames)."]
    tf = n["techfail"]
    L += ["", "## Technical-failure check (5a)", "",
          (f"- `{os.path.basename(tf['file'])}`: " + (" / ".join(tf["lines"][:4]) if tf["lines"] else
                                                       f"no rb_techfail.py verdict on {n['run_path']}/wp3.model")
           + ("" if tf["pass"] else " (NOT a pass)"))
          if tf else ("- step34.log records the 5a pass after the training line." if n["s34_5a"] else "- not found"),
          "", "## Archived with the model (runbook 5b)", "",
          "The command, logs, results file, versions, seed, thread count, restarts and selected epoch: the run directory "
          f"(`{rn}`, copied to `<MAC_STAGE>/run`) with train_command.txt, timing.txt, restarts.txt, item1p_rerun.list and "
          "step34.log (after the item-2 retry also train_command_retry.txt, the failed run's techfail_<run>.txt or "
          "run<j>.end / run<k>.end, and retry_causes_differ.txt if written). Whether `wp3.model` itself is committed is "
          "decided separately; its sha256 identifies it.", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run")
    ap.add_argument("--node-files", default=None)
    ap.add_argument("--dataset", default="results/objective2/dopant_shell/wp3/dataset")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--out")
    ap.add_argument("--date", default=time.strftime("%Y-%m-%d", time.gmtime()))
    ap.add_argument("--m21-offset", choices=("skip", "compute"), default="skip")
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--versions-from-env", action="store_true", help="take mace/torch/e3nn versions from this interpreter "
                    "(only in the training environment on the node)")
    ap.add_argument("--force", action="store_true", help="overwrite an existing --out (an uncommitted note or DRAFT of "
                    "the same date; a committed note is never rewritten: write a new one under a new date)")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)                        # argparse's own usage errors (unknown option, bad value): exit 2
    if a.self_test:
        return self_test()

    def own_error(msg):                            # this tool's own errors: exit 1, with the reason; nothing written
        print(f"REFUSED: {msg}; nothing written", file=sys.stderr)
        return 1
    if not (a.run and a.out):
        return own_error("--run and --out are required")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.date) or os.path.basename(a.out) != f"MODEL_NOTE_{a.date}.md":
        return own_error(f"--out must be named MODEL_NOTE_{a.date}.md for --date {a.date} (node_step7.sh looks for "
                         "MODEL_NOTE_<YYYY-MM-DD>.md)")
    if os.path.exists(a.out) and not a.force:
        return own_error(f"{a.out} exists: to replace an uncommitted note or DRAFT of this date, run again with --force; "
                         "a committed note is never rewritten (write a new note under a new date, WP3_RUNBOOK appendix "
                         "A.3)")
    try:
        text, draft = build(a)
    except Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out + ".tmp", "w") as fh:
        fh.write(text)
    os.replace(a.out + ".tmp", a.out)
    print(f"{'DRAFT' if draft else 'note'} -> {a.out}" + (f" (missing: {'; '.join(draft)})" if draft else ""))
    return 2 if draft else 0


# ---------------------------------------------------------------- self-test (synthetic files only; no MACE)
def self_test():
    import numpy as np
    from ase import Atoms
    from ase.io import write as awrite
    global _CALC_FACTORY
    root = tempfile.mkdtemp(prefix="rb_model_note_selftest_")
    repo, stage, ds = (os.path.join(root, x) for x in ("repo", "stage", "ds"))
    run = os.path.join(stage, "run")
    G = ["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t"]
    os.makedirs(os.path.join(repo, "scripts"))
    subprocess.run(["git", "init", "-q", repo], check=True)
    for f in SCRIPTS + HELPERS:
        open(os.path.join(repo, f), "w").write(f"# {f}\n")
    subprocess.run(G + ["add", "-A"], check=True); subprocess.run(G + ["commit", "-qm", "scripts"], check=True)
    head = git(repo, "rev-parse", "HEAD"); short = head[:7]
    for d in ("logs", "results", "checkpoints"):
        os.makedirs(os.path.join(run, d))
    open(os.path.join(run, "wp3.model"), "wb").write(os.urandom(4096))
    sha = sha256(os.path.join(run, "wp3.model"))
    losses = [5.0, 4.0, 4.5, 3.0, 3.5, 3.2, 3.1, 2.0, 2.5, 2.0]          # epoch 7 lowest; epoch 9 ties it (no checkpoint)
    rec = [{"loss": 9.0, "rmse_e_per_atom": 0.0003334, "rmse_f": 0.079819, "mode": "eval", "epoch": None, "head": "Default"}]
    for e, l in enumerate(losses):
        rec += [{"loss": l * 2, "mode": "opt", "epoch": e},
                {"loss": l, "rmse_e_per_atom": 1e-4 * (1 + e), "rmse_f": 0.05 + 0.001 * e, "mode": "eval", "epoch": e, "head": "Default"}]
    res = os.path.join(run, "results", "wp3_run-123_train.txt")
    open(res, "w").write("\n".join(json.dumps(r) for r in rec) + "\n")
    for e in (0, 1, 3, 7):
        open(os.path.join(run, "checkpoints", f"wp3_run-123_epoch-{e}.pt"), "w").write("x")
    logp = os.path.join(run, "logs", "wp3_run-123.log")
    open(logp, "w").write("2026-11-01 10:00:00.000 INFO: MACE version: 0.3.16\n"
                          "2026-11-01 10:00:00.500 INFO: Learning rate: 0.005, weight decay: 5e-07\n"
                          "2026-11-01 10:00:01.000 INFO: Using foundation model /home/ericdft/.cache/mace/20231203mace128L1_epoch199model as initial checkpoint.\n"
                          "2026-11-02 10:00:00.000 INFO: Loaded Stage one model from epoch 7 for evaluation\n"
                          "| valid_Default |         0.8      |        57.0     |        40.00     |\n")
    rp = "/data/work/wp3/run2"
    open(os.path.join(stage, "step34.log"), "w").write(
        f"[2026-10-31T09:00:00Z] start; repo {short}\n[2026-10-31T09:10:00Z] item-1' re-runs and resubmissions: 1 (item1p_rerun.list); every QE input final\n"
        "[2026-10-31T10:00:00Z] 4b: timing (threads, s for 2 epochs): 8 1500;16 1000;32 1000; -> T=16\n"
        "[2026-10-31T10:01:00Z] 4c: training started, pid 11, threads 16, run /data/work/wp3/run1\n"
        f"[2026-10-31T12:00:00Z] start; repo {short}\n"
        "[2026-10-31T12:00:01Z] 4c: run1 discarded unread [node loss] the node booted at 2026-10-31T11:58:00Z; the identical command runs in /data/work/wp3/run2\n"
        f"[2026-10-31T12:00:02Z] 4c: training started, pid 12, threads 16, run {rp}\n"
        f"[2026-11-02T10:00:00Z] 4: training finished in {rp}; wp3.model sha256 {sha}; restarts: 1 (restarts.txt)\n"
        f"[2026-11-02T10:05:00Z] 5a: {TECHFAIL_PASS}\n[2026-11-02T10:05:01Z] done\n")
    open(os.path.join(stage, "timing.txt"), "w").write("8 1500\n16 1000\n32 1000\n")
    open(os.path.join(stage, "train_command.txt"), "w").write(
        "/data/miniforge3/envs/mace/bin/mace_run_train --name wp3 --seed 123 --device cpu --lr 0.005 --keep_checkpoints "
        "--max_num_epochs 100 --work_dir <run>\n")
    open(os.path.join(stage, "restarts.txt"), "w").write("2026-10-31T12:00:01Z run1 discarded unread [node loss] the node booted at 2026-10-31T11:58:00Z\n")
    open(os.path.join(stage, "item1p_rerun.list"), "w").write("2026-10-31T09:05:00Z m14_Sr_img3 re-run (unconverged output -> out.try1)\n")
    open(os.path.join(stage, "versions.txt"), "w").write("mace 0.3.16\ntorch 2.5.1\ne3nn 0.4.4\nase 3.24.0\n")
    os.makedirs(os.path.join(stage, "logs"))
    open(os.path.join(stage, "logs", "techfail.txt"), "w").write(f"31 m21 frames evaluated with {rp}/wp3.model\n{TECHFAIL_PASS}\n")
    os.makedirs(ds)
    json.dump({"basis": "Eprime", "valid_hosts": ["m21"], "test_hosts": list(TEST_HOSTS),
               "start_check_reference": {"n_valid": 31, "RMSE_E_per_atom_meV": 0.33342, "RMSE_F_meV_A": 79.819,
                                         "mean_residual_meV": -49.27}}, open(os.path.join(ds, "dataset_meta.json"), "w"))
    frames = []
    for i in range(31):
        at = Atoms("H2", positions=[[0, 0, 0], [0, 0, 0.74 + 0.001 * i]], cell=[10, 10, 10], pbc=True)
        at.info.update({"host": "m21", "label": f"m21_undoped_img{i}", "REF_energy": -1.0 - 0.01 * i})
        frames.append(at)
    awrite(os.path.join(ds, "valid.xyz"), frames, format="extxyz")
    open(os.path.join(ds, "test.xyz"), "w").write("THIS FILE MUST NEVER BE OPENED\n")
    calls = []

    stub_shift = [0.0008]                          # eV per atom: the selected epoch's rmse_e_per_atom (epoch 7: 0.8 meV/atom)

    class Stub:                                    # E = REF + shift * natoms (2 atoms: offset exactly +1.6 meV/cell)
        def get_potential_energy(self, atoms=None, force_consistent=False):
            calls.append(1)
            return float(atoms.info["REF_energy"]) + stub_shift[0] * len(atoms)
    _CALC_FACTORY = Stub
    real_open = open
    opened = []
    n_cases = [0]

    def run_case(name, expect_rc, mutate=None, extra=(), expect_text=(), reason=None):
        n_cases[0] += 1
        work = tempfile.mkdtemp(prefix=f"case_{name}_", dir=root)
        st2, ds2, repo2 = (os.path.join(work, x) for x in ("stage", "ds", "repo"))
        shutil.copytree(stage, st2); shutil.copytree(ds, ds2); shutil.copytree(repo, repo2)
        if mutate:
            mutate(st2, ds2, repo2)
        out = os.path.join(work, "MODEL_NOTE_2026-11-02.md")
        del calls[:]
        import builtins
        def spy(f, *x, **k):
            opened.append(str(f)); return real_open(f, *x, **k)
        import io
        err, olderr = io.StringIO(), sys.stderr
        builtins.open = spy; sys.stderr = err
        try:
            rc = main(["--run", os.path.join(st2, "run"), "--node-files", st2, "--dataset", ds2, "--repo", repo2,
                       "--out", out, "--date", "2026-11-02", *extra])
        finally:
            builtins.open = real_open; sys.stderr = olderr
        assert rc == expect_rc, (name, rc, expect_rc, err.getvalue())
        assert reason is None or reason in err.getvalue(), (name, "refused for another reason:", err.getvalue())
        assert not any(os.path.basename(f) == "test.xyz" for f in opened), (name, "test.xyz was opened")
        txt = real_open(out).read() if os.path.exists(out) else ""
        for t in expect_text:
            assert t in txt, (name, t)
        print(f"  {name}: rc {rc} as expected" + (f", stub single points {len(calls)}" if calls else "")
              + (f" ({err.getvalue().strip()[:110]})" if rc == 1 else ""))
        return txt

    print(f"self-test in {root}")
    txt = run_case("happy", 0, extra=("--m21-offset", "compute"),
                   expect_text=(f"model_sha256: {sha}", f"scripts_commit: {head}", "run: run2", "epoch-7 checkpoint",
                                "OMP_NUM_THREADS=16 ", f"--work_dir {rp}", "| Selected | 7 |", "1.600 meV/cell",
                                "| 49.27 |", "torch 2.5.1", "e3nn 0.4.4", "[node loss]", "m14_Sr_img3", "PASS",
                                "note_status: complete", "- none (no technical failure before the selected run: it is not a retry)"))
    assert len(calls) == 31 and "DRAFT" not in txt and "**Check:**" not in txt
    machine = lambda x: [ln for ln in x.splitlines() if re.match(r"(model_sha256|scripts_commit|run|note_status): ", ln)]
    assert len(machine(txt)) == 4, machine(txt)
    txt = run_case("no-offset-draft", 2, expect_text=("DRAFT", "NOT COMPUTED", "draft-model_sha256:"))
    assert not machine(txt), ("a DRAFT carries machine-readable lines", machine(txt))
    stub_shift[0] = 0.005
    txt = run_case("rmse-mismatch-draft", 2, extra=("--m21-offset", "compute"), expect_text=("DRAFT", "**Check:**", "+4.20000"))
    assert not machine(txt), ("a DRAFT carries machine-readable lines", machine(txt))
    stub_shift[0] = 0.0008
    def scfail(st, d, r):
        pth = os.path.join(st, "run", "results", "wp3_run-123_train.txt"); x = real_open(pth).read()
        real_open(pth, "w").write(x.replace('"rmse_f": 0.079819', '"rmse_f": 0.09', 1))
    run_case("start-check-fail", 1, scfail, reason="fails the start check")
    def basis(st, d, r):
        pth = os.path.join(d, "dataset_meta.json"); m = json.load(real_open(pth)); m["basis"] = "E_prime"
        json.dump(m, real_open(pth, "w"))
    run_case("unknown-basis", 1, basis, reason="basis 'E_prime'")
    for opt in ("--freeze 3", "--lora_rank 4", "--swa_lr 0.001"):
        def forb(st, d, r, opt=opt):
            pth = os.path.join(st, "train_command.txt"); x = real_open(pth).read()
            real_open(pth, "w").write(x.replace(" --work_dir", f" {opt} --work_dir"))
        run_case("forbidden " + opt.split()[0], 1, forb, reason="which item 2 excludes")
    other = "f" * 64
    def retry(st, d, r, stop=True, lr="0.0025", ae2=False, differ=False):
        r1, sp = "/data/work/wp3/run1", ("/data/work/wp3/run4" if ae2 else rp)
        k = "exit 1 after the start check, 2026-11-01T{}:00:00Z: RuntimeError: kernel failure"
        mid = (f"[2026-11-01T11:00:01Z] 4c: training started, pid 13, threads 16, run /data/work/wp3/run2\n"
               f"[2026-11-01T13:00:01Z] 4c: run2 discarded unread [abnormal end] {k.format(13)}; the identical command runs in /data/work/wp3/run3\n"
               f"[2026-11-01T13:00:02Z] start; repo {short} (5a retry, by hand)\n"
               f"[2026-11-01T13:00:03Z] 4c: training started, pid 14, threads 16, run /data/work/wp3/run3\n"
               f"[2026-11-01T15:00:01Z] 4c: run3 discarded unread [abnormal end] {k.format(15)}; the identical command runs in /data/work/wp3/run4\n"
               f"[2026-11-01T15:00:02Z] start; repo {short} (5a retry, by hand)\n") if ae2 else ""
        real_open(os.path.join(st, "step34.log"), "w").write(
            f"[2026-10-31T09:00:00Z] start; repo {short}\n[2026-10-31T09:10:00Z] item-1' re-runs and resubmissions: 1 (item1p_rerun.list); every QE input final\n"
            "[2026-10-31T10:00:00Z] 4b: timing (threads, s for 2 epochs): 8 1500;16 1000;32 1000; -> T=16\n"
            f"[2026-10-31T10:01:00Z] 4c: training started, pid 11, threads 16, run {r1}\n"
            f"[2026-11-01T10:00:00Z] 4: training finished in {r1}; wp3.model sha256 {other}; restarts: 0 (restarts.txt)\n"
            + ("[2026-11-01T10:05:00Z] STOP: technical failure: non-finite energy or forces on m21_band_3\n" if stop else "")
            + f"[2026-11-01T11:00:00Z] start; repo {short} (5a retry, by hand)\n" + mid
            + f"[2026-11-01T15:00:03Z] 4c: training started, pid 15, threads 16, run {sp}\n"
            f"[2026-11-02T10:00:00Z] 4: training finished in {sp}; wp3.model sha256 {sha}; restarts: {2 if ae2 else 0} (restarts.txt)\n"
            f"[2026-11-02T10:05:00Z] 5a: {TECHFAIL_PASS}\n")
        os.remove(os.path.join(st, "restarts.txt"))
        if ae2:
            real_open(os.path.join(st, "restarts.txt"), "w").write(
                f"2026-11-01T13:00:01Z run2 discarded unread [abnormal end] {k.format(13)}\n"
                f"2026-11-01T15:00:01Z run3 discarded unread [abnormal end] {k.format(15)}\n")
            real_open(os.path.join(st, "logs", "techfail.txt"), "w").write(f"31 m21 frames evaluated with {sp}/wp3.model\n{TECHFAIL_PASS}\n")
        if differ:
            real_open(os.path.join(st, "retry_causes_differ.txt"), "w").write(
                "run2 run3: run2 hit a node-side I/O error in the data loader, run3 a kernel failure (checked by two reviewers)\n")
        real_open(os.path.join(st, "logs", "techfail_run1.txt"), "w").write(
            f"31 m21 frames evaluated with {r1}/wp3.model\nnon-finite energy or forces on m21_band_3\n")
        c = real_open(os.path.join(st, "train_command.txt")).read()
        real_open(os.path.join(st, "train_command_retry.txt"), "w").write(c.replace("--lr 0.005 ", "--lr 0.0025 "))
        lp = os.path.join(st, "run", "logs", "wp3_run-123.log"); x = real_open(lp).read()
        real_open(lp, "w").write(x.replace("Learning rate: 0.005,", f"Learning rate: {lr},"))
    txt = run_case("retry", 0, retry, extra=("--m21-offset", "compute"),
                   expect_text=("note_status: complete", "is the one retry", "--lr 0.0025", "learning rate 0.0025",
                                "non-finite energy or forces on m21_band_3"))
    run_case("retry-without-stop-line", 1, lambda st, d, r: retry(st, d, r, stop=False), reason="only the item-2 retry")
    run_case("retry-log-lr-0.005", 1, lambda st, d, r: retry(st, d, r, lr="0.005"), reason="Learning rate")
    # the retry after a DETERMINISTIC abnormal end (node_step34 'STOP: run<k>: second abnormal end'; final-check issue 3)
    def dae(st, d, r, lr="0.0025", ends=True, cmdfile=True, prev_cause=False, reclaim=False, techfail_too=False,
            two=False, own_ae=False, own_ae2=False, differ=False, unquoted=False, badtag=False, threads=16):
        W = "/data/work/wp3"; sel = f"{W}/run5" if own_ae2 else f"{W}/run4" if (reclaim or own_ae or badtag) else f"{W}/run3"
        k1 = "exit 137 after the start check, 2026-10-31T11:00:00Z: Killed"; k2 = "exit 137 after the start check, 2026-10-31T12:00:00Z: Killed"
        L = [f"[2026-10-31T09:00:00Z] start; repo {short}",
             "[2026-10-31T09:10:00Z] item-1' re-runs and resubmissions: 1 (item1p_rerun.list); every QE input final",
             "[2026-10-31T10:00:00Z] 4b: timing (threads, s for 2 epochs): 8 1500;16 1000;32 1000; -> T=16"]
        if techfail_too:
            L += [f"[2026-10-31T10:00:30Z] 4c: training started, pid 10, threads 16, run {W}/run0",
                  f"[2026-10-31T10:00:40Z] 4: training finished in {W}/run0; wp3.model sha256 {other}; restarts: 0 (restarts.txt)",
                  "[2026-10-31T10:00:50Z] STOP: technical failure: non-finite energy or forces on m21_band_3",
                  f"[2026-10-31T10:00:55Z] start; repo {short} (5a retry, by hand)"]
            real_open(os.path.join(st, "logs", "techfail_run0.txt"), "w").write(
                f"31 m21 frames evaluated with {W}/run0/wp3.model\nnon-finite energy or forces on m21_band_3\n")
        L += [f"[2026-10-31T10:01:00Z] 4c: training started, pid 11, threads 16, run {W}/run1",
              f"[2026-10-31T11:00:00Z] 4c: run1 [abnormal end] {k1}",
              f"[2026-10-31T11:00:01Z] 4c: run1 discarded unread [abnormal end] {k1}; the identical command runs in {W}/run2",
              f"[2026-10-31T11:00:02Z] 4c: training started, pid 12, threads 16, run {W}/run2",
              f"[2026-10-31T12:00:00Z] 4c: run2 [abnormal end] {k2}",
              (f"[2026-10-31T12:00:01Z] STOP: run2: second abnormal end ([abnormal end] {k2}; earlier: 2026-10-31T11:00:01Z run1 "
               f"discarded unread [abnormal end] {k1}). The same cause twice in succession is a technical failure (item 2); "
               "if the causes differ, relaunch with PREV_CAUSE='<cause>'") if not unquoted else
              f"[2026-10-31T12:00:01Z] STOP: run2: second abnormal end ([abnormal end] {k2})"]
        rs = [f"2026-10-31T11:00:01Z run1 discarded unread [abnormal end] {k1}"]
        if prev_cause:                             # the operator judged the causes different: a restart, not the retry
            L += [f"[2026-10-31T13:00:00Z] start; repo {short}",
                  f"[2026-10-31T13:00:01Z] 4c: run2 discarded unread [operator] OOM in the data loader, not run1's cause "
                  f"2026-10-31T12:30:00Z; driver: [abnormal end] {k2}; the identical command runs in {W}/run3"]
            rs += [f"2026-10-31T13:00:01Z run2 discarded unread [operator] OOM in the data loader, not run1's cause"]
        else:
            L += [f"[2026-10-31T13:00:00Z] start; repo {short} (5a retry with --lr 0.0025, run by hand)"]
        if two:
            L += ["[2026-10-31T13:00:01Z] STOP: run9: second abnormal end ([abnormal end] exit 1; earlier: x)"]
        L += [f"[2026-10-31T13:00:02Z] 4c: training started, pid 13, threads {threads if sel.endswith('run3') else 16}, run {W}/run3"]
        k3 = "exit 1 after the start check, 2026-10-31T15:00:00Z: RuntimeError: kernel failure"
        k4 = "exit 1 after the start check, 2026-10-31T17:00:00Z: RuntimeError: kernel failure"
        if own_ae or own_ae2 or badtag:            # the retry itself ended abnormally (A.5: discarded unread, rerun)
            tag = "[operator] by hand" if badtag else "[abnormal end]"
            L += [f"[2026-10-31T15:00:01Z] 4c: run3 discarded unread {tag} {k3}; the identical command runs in {W}/run4",
                  f"[2026-10-31T15:00:02Z] start; repo {short} (5a retry with --lr 0.0025, run by hand)",
                  f"[2026-10-31T15:00:03Z] 4c: training started, pid 14, threads {threads if sel.endswith('run4') else 16}, run {W}/run4"]
            rs += [f"2026-10-31T15:00:01Z run3 discarded unread {tag} {k3}"]
        if own_ae2:
            L += [f"[2026-10-31T17:00:01Z] 4c: run4 discarded unread [abnormal end] {k4}; the identical command runs in {W}/run5",
                  f"[2026-10-31T17:00:02Z] start; repo {short} (5a retry with --lr 0.0025, run by hand)",
                  f"[2026-10-31T17:00:03Z] 4c: training started, pid 15, threads {threads}, run {W}/run5"]
            rs += [f"2026-10-31T17:00:01Z run4 discarded unread [abnormal end] {k4}"]
        if differ:
            real_open(os.path.join(st, "retry_causes_differ.txt"), "w").write(
                "run3 run4: run3 failed in the data loader, run4 in the optimiser step (checked by two reviewers)\n")
        if reclaim:                                # the retry itself cut by a reclaim: item-2 Interruptions, by hand
            L += [f"[2026-10-31T20:00:00Z] 4c: run3 discarded unread [node loss] the node booted at 2026-10-31T19:58:00Z, "
                  f"after run3 started at 2026-10-31T13:00:02Z; last results write 2026-10-31T19:50:00Z; the identical "
                  f"command runs in {W}/run4",
                  f"[2026-10-31T20:00:01Z] start; repo {short} (5a retry with --lr 0.0025, run by hand)",
                  f"[2026-10-31T20:00:02Z] 4c: training started, pid 14, threads 16, run {W}/run4"]
            rs += ["2026-10-31T20:00:00Z run3 discarded unread [node loss] the node booted at 2026-10-31T19:58:00Z, after "
                   "run3 started at 2026-10-31T13:00:02Z"]
        L += [f"[2026-11-02T10:00:00Z] 4: training finished in {sel}; wp3.model sha256 {sha}; restarts: {len(rs)} (restarts.txt)",
              f"[2026-11-02T10:05:00Z] 5a: {TECHFAIL_PASS}"]
        real_open(os.path.join(st, "step34.log"), "w").write("\n".join(L) + "\n")
        real_open(os.path.join(st, "restarts.txt"), "w").write("\n".join(rs) + "\n")
        real_open(os.path.join(st, "logs", "techfail.txt"), "w").write(f"31 m21 frames evaluated with {sel}/wp3.model\n{TECHFAIL_PASS}\n")
        if ends:
            real_open(os.path.join(st, "run1.end"), "w").write(f"[abnormal end] {k1}\n")
            real_open(os.path.join(st, "run2.end"), "w").write(f"[abnormal end] {k2}\n")
        c = real_open(os.path.join(st, "train_command.txt")).read()
        if cmdfile and not prev_cause:
            real_open(os.path.join(st, "train_command_retry.txt"), "w").write(c.replace("--lr 0.005 ", "--lr 0.0025 "))
        lp = os.path.join(st, "run", "logs", "wp3_run-123.log"); x = real_open(lp).read()
        real_open(lp, "w").write(x.replace("Learning rate: 0.005,", f"Learning rate: {lr},"))
    run_case("dae-retry", 0, dae, extra=("--m21-offset", "compute"),
             expect_text=("note_status: complete", "run: run3", "Deterministic abnormal end", "`run1` and then `run2`",
                          "run2.end", f"exit 137 after the start check, 2026-10-31T12:00:00Z", "STOP: run2: second abnormal end",
                          "is the one retry", "--lr 0.0025", "learning rate 0.0025", "there is no second retry"))
    run_case("dae-retry-cut-by-a-reclaim", 0, lambda st, d, r: dae(st, d, r, reclaim=True), extra=("--m21-offset", "compute"),
             expect_text=("run: run4", "[node loss]", "is the one retry", "Deterministic abnormal end"))
    run_case("dae-causes-differ-prev-cause", 0, lambda st, d, r: dae(st, d, r, lr="0.005", prev_cause=True),
             extra=("--m21-offset", "compute"),
             expect_text=("run: run3", "it is not a retry", "learning rate 0.005", "[operator] OOM in the data loader"))
    run_case("dae-without-retry-command", 1, lambda st, d, r: dae(st, d, r, cmdfile=False), reason="train_command_retry.txt")
    run_case("dae-without-end-file", 1, lambda st, d, r: dae(st, d, r, ends=False), reason="run2.end")
    run_case("dae-log-lr-0.005", 1, lambda st, d, r: dae(st, d, r, lr="0.005"), reason="Learning rate")
    run_case("dae-and-techfail-retry", 1, lambda st, d, r: dae(st, d, r, techfail_too=True), reason="one retry only")
    run_case("dae-two-stops", 1, lambda st, d, r: dae(st, d, r, two=True), reason="one retry only")
    # round-2 review (E-1/E2E-1, E2E-2, E-4): the first of the deterministic pair is the line node_step34's STOP quotes;
    # abnormal ends of the retry itself; <T>
    txt = run_case("dae-retry-with-own-abnormal-restart", 0, lambda st, d, r: dae(st, d, r, own_ae=True),
                   extra=("--m21-offset", "compute"),
                   expect_text=("run: run4", "`run1` and then `run2`", "first (run1, restarts.txt)", "Runs of the retry discarded",
                                "run3 discarded unread [abnormal end]"))
    assert "`run3` and then" not in txt and "first (run3" not in txt, "the retry's own abnormal end was named as the first of the pair"
    run_case("dae-retry-two-abnormal-ends", 1, lambda st, d, r: dae(st, d, r, own_ae2=True),
             reason="ended abnormally twice in succession (run3, then run4)")
    run_case("dae-retry-two-abnormal-ends-causes-differ", 0, lambda st, d, r: dae(st, d, r, own_ae2=True, differ=True),
             extra=("--m21-offset", "compute"),
             expect_text=("run: run5", "`run1` and then `run2`", "operator stated that their causes differ",
                          "run3 failed in the data loader"))
    run_case("dae-causes-differ-file-without-pair", 1, lambda st, d, r: dae(st, d, r, own_ae=True, differ=True),
             reason="which are not two successive")
    run_case("dae-stop-line-quotes-no-restart", 1, lambda st, d, r: dae(st, d, r, unquoted=True), reason="quotes no [abnormal end]")
    run_case("dae-retry-discard-bad-tag", 1, lambda st, d, r: dae(st, d, r, badtag=True), reason="discarded as [operator]")
    run_case("dae-retry-threads-not-T", 1, lambda st, d, r: dae(st, d, r, threads=32), reason="does not show threads 16")
    run_case("retry-two-abnormal-ends", 1, lambda st, d, r: retry(st, d, r, ae2=True),
             reason="ended abnormally twice in succession (run2, then run3)")
    run_case("retry-two-abnormal-ends-causes-differ", 0, lambda st, d, r: retry(st, d, r, ae2=True, differ=True),
             extra=("--m21-offset", "compute"), expect_text=("run: run4", "is the one retry", "causes differ"))
    def dirty(st, d, r): real_open(os.path.join(r, "scripts", "40_wp3b.py"), "a").write("# edit\n")
    run_case("uncommitted-script", 1, dirty, reason="uncommitted changes")
    def m30(st, d, r):
        from ase.io import read as aread
        fr = aread(os.path.join(d, "valid.xyz"), ":"); fr[5].info["host"] = "m30"; fr[5].info["label"] = "m30_GA_img0"
        awrite(os.path.join(d, "valid.xyz"), fr, format="extxyz")
    run_case("test-host-frame", 1, m30, extra=("--m21-offset", "compute"), reason="only the m21 frames")
    assert not calls, "a model evaluation ran although valid.xyz held a test-host frame"
    def testtable(st, d, r): real_open(os.path.join(st, "run", "logs", "wp3_run-123.log"), "a").write("INFO: Error-table on TEST:\n| test |\n")
    run_case("test-table-in-log", 1, testtable, reason="test-set error table")
    def nan(st, d, r):
        p = os.path.join(st, "run", "results", "wp3_run-123_train.txt")
        real_open(p, "a").write('{"loss": NaN, "mode": "eval", "epoch": 10, "head": "Default"}\n')
    run_case("nan-loss", 1, nan, reason="non-finite loss")
    def ckpt(st, d, r): os.remove(os.path.join(st, "run", "checkpoints", "wp3_run-123_epoch-7.pt"))
    run_case("checkpoint-mismatch", 1, ckpt, reason="not the improving epochs")
    def logep(st, d, r):
        p = os.path.join(st, "run", "logs", "wp3_run-123.log")
        t = real_open(p).read(); real_open(p, "w").write(t.replace("from epoch 7 ", "from epoch 9 "))
    run_case("log-epoch-mismatch", 1, logep, reason="the log loaded epoch 9")
    def shalog(st, d, r): real_open(os.path.join(st, "run", "wp3.model"), "ab").write(b"x")
    run_case("model-sha-mismatch", 1, shalog, reason="with the --run copy's sha256")
    def restart(st, d, r): os.remove(os.path.join(st, "restarts.txt"))
    run_case("restarts-missing", 1, restart, reason="restarts.txt has 0")
    def changed(st, d, r):
        real_open(os.path.join(r, "scripts", "41_wp3_md.py"), "a").write("# changed after training\n")
        subprocess.run(["git", "-C", r, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "edit"], check=True)
    run_case("script-changed-after-training", 1, changed, reason="changed between the training commit")
    def vh(st, d, r):
        p = os.path.join(d, "dataset_meta.json"); m = json.load(real_open(p)); m["valid_hosts"] = ["m21", "m30"]
        json.dump(m, real_open(p, "w"))
    run_case("valid-hosts", 1, vh, reason="valid_hosts")
    # merge review (R4): node_step34 writes the 5a file with 2>&1; in the node's mace environment library warnings
    # (stderr) and mace's import notice come before rb_techfail's own lines, and a warning may follow them (synthetic
    # lines below). Only rb_techfail's lines decide.
    tf_pre = ("/data/miniforge3/envs/mace/lib/python3.12/site-packages/e3nn/o3/_wigner.py:10: UserWarning: a library "
              "warning before the output (self-test)\n  _Jd, _W3j_flat, _W3j_indices = torch.load(...)\n"
              "/data/miniforge3/envs/mace/lib/python3.12/site-packages/torch/jit/_check.py:178: FutureWarning: another "
              "library warning (self-test)\n  warnings.warn(\n"
              "cuequivariance or cuequivariance_torch is not available. Cuequivariance acceleration will be disabled.\n")
    tf_post = "Exception ignored in: <function _TemporaryFileCloser.__del__ at 0x7f00>\nOSError: a warning after the output (self-test)\n"
    def tf_noisy(st, d, r):                        # node_step34 then logs 'tail -1' of the file as its 5a line
        real_open(os.path.join(st, "logs", "techfail.txt"), "w").write(
            f"{tf_pre}31 m21 frames evaluated with {rp}/wp3.model\n{TECHFAIL_PASS}\n{tf_post}")
        p = os.path.join(st, "step34.log"); x = real_open(p).read()
        real_open(p, "w").write(x.replace(f"5a: {TECHFAIL_PASS}", "5a: " + tf_post.splitlines()[-1]))
    txt = run_case("techfail-warnings", 0, tf_noisy, extra=("--m21-offset", "compute"),
                   expect_text=("note_status: complete", f"`techfail.txt`: 31 m21 frames evaluated with {rp}/wp3.model / "
                                f"{TECHFAIL_PASS}"))
    assert "(NOT a pass)" not in txt, "a passed 5a with warning lines was shown as not a pass"
    def retry_noisy(st, d, r):
        retry(st, d, r)
        real_open(os.path.join(st, "logs", "techfail_run1.txt"), "w").write(
            f"{tf_pre}31 m21 frames evaluated with /data/work/wp3/run1/wp3.model\nnon-finite energy or forces on m21_band_3\n{tf_post}")
        real_open(os.path.join(st, "logs", "techfail.txt"), "w").write(
            f"{tf_pre}31 m21 frames evaluated with {rp}/wp3.model\n{TECHFAIL_PASS}\n{tf_post}")
    run_case("retry-techfail-warnings", 0, retry_noisy, extra=("--m21-offset", "compute"),
             expect_text=("note_status: complete", "is the one retry", "non-finite energy or forces on m21_band_3"))
    def retry_tf_pass(st, d, r):
        retry(st, d, r)
        real_open(os.path.join(st, "logs", "techfail_run1.txt"), "w").write(
            f"{tf_pre}31 m21 frames evaluated with /data/work/wp3/run1/wp3.model\n{TECHFAIL_PASS}\n{tf_post}")
    run_case("retry-techfail-record-without-failure", 1, retry_tf_pass, reason="does not show the failure")
    def tf_noverdict(st, d, r):                    # a checker error: no rb_techfail verdict, and no 5a line logged
        real_open(os.path.join(st, "logs", "techfail.txt"), "w").write(
            tf_pre + "Traceback (most recent call last):\n  File \"scripts/wp3_runbook/rb_techfail.py\", line 22, in "
            "<module>\nImportError: a checker error (self-test)\n")
        p = os.path.join(st, "step34.log"); x = real_open(p).read()
        real_open(p, "w").write(x.replace(f"[2026-11-02T10:05:00Z] 5a: {TECHFAIL_PASS}\n", ""))
    txt = run_case("techfail-no-verdict-draft", 2, tf_noverdict, extra=("--m21-offset", "compute"),
                   expect_text=("DRAFT", "no passed technical-failure check (5a) found", "(NOT a pass)",
                                "draft-model_sha256:"))
    assert not machine(txt), ("a DRAFT carries machine-readable lines", machine(txt))
    def nover(st, d, r): os.remove(os.path.join(st, "versions.txt"))
    txt = run_case("versions-missing-draft", 2, nover, extra=("--m21-offset", "compute"),
                   expect_text=("DRAFT", "torch / e3nn versions missing"))
    assert not machine(txt), ("a DRAFT carries machine-readable lines", machine(txt))
    # the tool's own errors exit 1 and write nothing; --force overwrites an existing --out
    def preexist(st, d, r): real_open(os.path.join(os.path.dirname(st), "MODEL_NOTE_2026-11-02.md"), "w").write("an earlier DRAFT (self-test)\n")
    run_case("out-exists", 1, preexist, expect_text=("an earlier DRAFT (self-test)",), reason="exists")
    run_case("out-exists-force", 0, preexist, extra=("--force", "--m21-offset", "compute"), expect_text=("note_status: complete",))
    import io
    for name, argv, why in (
            ("out-name-wrong", ["--run", run, "--node-files", stage, "--dataset", ds, "--repo", repo,
                                "--out", os.path.join(root, "y", "MODEL_NOTE_2026-11-03.md"), "--date", "2026-11-02"],
             "must be named MODEL_NOTE_2026-11-02.md"),
            ("run-missing", ["--out", os.path.join(root, "y", "MODEL_NOTE_2026-11-02.md"), "--date", "2026-11-02"],
             "--run and --out are required")):
        n_cases[0] += 1
        err, olderr = io.StringIO(), sys.stderr
        sys.stderr = err
        try:
            rc = main(argv)
        finally:
            sys.stderr = olderr
        assert rc == 1 and why in err.getvalue() and not os.path.exists(os.path.join(root, "y")), (name, rc, err.getvalue())
        print(f"  {name}: rc 1 as expected ({err.getvalue().strip()[:110]})")
    n_cases[0] += 1
    rc = main(["--run", run, "--node-files", stage, "--dataset", os.path.join(ds, "test.xyz"), "--repo", repo,
               "--out", os.path.join(root, "x", "MODEL_NOTE_2026-11-02.md"), "--date", "2026-11-02"])
    assert rc == 1 and not os.path.exists(os.path.join(root, "x")), "a test.xyz path was accepted"
    print("  test.xyz-path: rc 1 as expected")
    print(f"SELF-TEST PASS ({n_cases[0]} cases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

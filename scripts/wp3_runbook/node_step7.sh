#!/bin/bash
# WP3 step 7 driver: WP3_RUNBOOK.md 7a-7d on the node (PLAN amendment m item 4 (d) WP3b and (e) MD stability,
# item 7 step 7). Installed as /data/work/wp3_step7.sh; runs as ericdft in the clean checkout /data/work/ps_wp3 at
# the step-6 commit <C6> (the commit that adds results/objective2/dopant_shell/wp3/wp3_eval.json, scripts/39's output;
# a descendant of the model-note commit <CNOTE>, the commit that adds the note; <CNOTE>'s parent is the note's
# scripts_commit, which is the runbook's <CN>). Start it with
#     setsid nohup bash /data/work/wp3_step7.sh > /data/work/wp3/driver7.out 2>&1 < /dev/null &
# or let /data/work/wp3_relaunch.sh do it. Log /data/work/wp3/step7.log; markers STEP7_DONE and STEP7_STOPPED;
# every rerun, re-issue, final end, operator acceptance and QE resubmission is listed in /data/work/wp3/step7_reruns.list.
#
# Order of work (PLAN amendment m item 7: 5 note, 6 scripts/39 once, 7 WP3b and (e)), enforced here: the note commit
# <CNOTE>, then step 6 on the Mac, then <C6> with wp3_eval.json, then this driver.
# Preconditions (each a STOP before anything runs): this file equals HEAD:scripts/wp3_runbook/node_step7.sh (the
# installed driver is the committed one; the installed wp3_relaunch.sh is compared with the committed one, a WARN);
# the system and kernel journal are readable through 'sudo -n journalctl' and the journal lists at least two boots
# (the classifier's only source of shutdown and OOM evidence); STEP34_DONE; NOTE_COMMITTED holding the full commit
# <CNOTE>; STEP6_DONE holding exactly one line, the full commit <C6>; checkout HEAD = <C6> and clean; <CNOTE> is the
# model note committed on its own (one parent, one added MODEL_NOTE_<date>.md); the note is COMPLETE (rb_model_note.py
# exit 0: no DRAFT banner, no '**Check:**' line, the selected model's m21 offset computed, 'note_status: complete') and
# its machine-readable lines name model_sha256 <SHA>, scripts_commit <CS> and run run<n>; <CNOTE> is a strict ancestor
# of <C6>; between them only paths under results/ changed (and scripts/39_wp3_evaluate.py: a step-6 fix, logged as a
# WARN; every other changed path besides wp3_eval.json is named in a WARN too), not the note, not any MODEL_NOTE, not
# PLAN.md (the pre-registration), not
# scripts 40/41, a helper they load, node_step7.sh, node_relaunch.sh or the repository data step 7 reads (each of these
# present at <C6>); <C6> itself adds wp3_eval.json and is the only commit after <CNOTE> that touches it (scripts/39
# once), a scripts/39 full-mode result made after the note commit (its git head between <CNOTE> and <C6>, a commit at
# which only results/ and scripts/39 differ from <CNOTE>) by the scripts/39 committed at <C6>, whose
# arms.finetuned.sha256 is <SHA>; <CS> is an ancestor of <CNOTE> and scripts 39, 40, 41 and every helper 40/41 load
# are present and byte-identical at <CS>, at the commit node_step34 trained at, and at <CNOTE>; step34.log has a
# 'training finished in .../run<n>; wp3.model sha256
# <SHA>' line, its wp3.model has sha256 <SHA>, and logs/techfail.txt passes for it; if run<n> is the one item-2 retry
# (runbook 5a), it follows either the technical failure of one other finished run ('STOP: technical failure' after it,
# and its own logs/techfail_<run>.txt with the failure) or a deterministic abnormal end ('STOP: run<k>: second abnormal
# end', run<k> not discarded afterwards, run<k>.end kept, the STOP line quoting the first end as 'earlier: <restarts.txt
# line>'), its command is train_command_retry.txt (= the command with --lr 0.0025), its log shows lr 0.0025, its own
# discarded runs are [node loss], [abnormal end] or [start check FAIL], and each [abnormal end] of it after the first
# has the operator's 'run<a> run<b>: <why>' in retry_causes_differ.txt (the same cause twice is a technical failure of
# the retry: no second retry); run<n> trained with timing.txt's <T> threads; <SHA> is not the zero-shot foundation
# file; mace 0.3.16; the cached
# foundation file (zeroshot) has its PLAN hash; the six band files exist; /data/jobs/wp3b holds nothing but the
# 12 WP3b labels; no QE (pw.x, neb.x, pp.x, qe_queue.sh), training or scripts/35/40/41 process outside this driver is
# alive. At the first start (before 7a was ever launched) the WP3b and MD work directories and /data/jobs/wp3b must
# be empty: an output made before step 7 (by hand, before the note commit?) is never adopted (item 2 'Reporting');
# <C6> is recorded then (step7/commit) and every later start must run at the same commit.
#
# Order and schedule (why): 7a region, then zeroshot (each must exit 0). Then ONE pool of MACE work under a 64-thread
# budget: the 12 relaxations (scripts/40, one --cells invocation each, its default 6 threads; the 6 unconstrained
# first, as they free all 234 atoms) and the 12 MD runs (scripts/41, --threads 8). Then the QE chain wp3b (12 single
# points, 64 ranks), started only when every relaxation has its record (or has no attempt left) and no other QE
# process runs. The chain may never run beside MACE work, and no MD run needs a relaxation, so all MACE work goes
# before the chain: wall time = MACE makespan + QE time. MD runs fill the threads that the tail of the relaxations
# leaves idle; MD after the chain would add its whole length (two 8-wide waves of 5 ps) to the wall time. The first
# scripts/40 invocation runs alone until it has written wp2e_minimum.json (single writer); nothing else starts
# meanwhile. Once the poller has recorded a spot termination notice in this boot, nothing new is started (neither a
# MACE job nor the chain) for NOTICE_HOLD s: a launch then is certain to be cut and would spend an attempt.
#
# Resumable after a hard stop at any point. Every launch is recorded (and synced) before its process starts; every
# end is classified from evidence and the classification is kept (fsynced) per script attempt; markers and list lines
# are written after sync. A complete output is adopted only if a node_step7 launch started the attempt that made it
# (its pid) and the record (and every attempt, and wp2e_minimum.json) was made at <C6> with no uncommitted change;
# it is re-verified (record, model sha, step cap, region, QE input, structure, trajectory sha) and a damaged one
# STOPs (never treated as complete). Reruns use the scripts' own --rerun-cause, with the identical command otherwise,
# at most what the scripts allow (3 attempts):
#   spot-reclaim  the attempt started in an earlier boot and that boot has a recorded spot termination notice
#                 (the background poller records the metadata endpoint's notice to step7/spot, fsynced);
#   node-loss     the attempt started in an earlier boot without a notice, the poller was alive in that boot (its last
#                 heartbeat at most 5 min before and at most 30 min after the end of that boot's system journal) and
#                 the system journal of that boot shows no system-level shutdown (systemd[1], systemd-shutdown[1],
#                 systemd-logind in the identifier field; a user manager's 'Reached target shutdown.target' at an ssh
#                 logout is not one);
#   oom           the kernel OOM killer killed the process (a kernel line for its pid, at or after its launch), or an
#                 MD traceback holds a memory error.
# Every journal read goes through 'sudo -n journalctl' ($JCTL; ericdft is not in adm/systemd-journal), as short-unix
# lines: only time-stamped lines are entries (continuation lines of a multi-line message are not). A failed or empty
# read, a boot without a time-stamped or systemd[1] entry, or a journal that does not cover the end of the boot (it
# ends over 30 min before the poller's last heartbeat or the launch) is no evidence: that attempt STOPs (not kept, so
# the next start classifies it again), never node-loss. So does an exit 137 younger than 5 min without an OOM line.
# Anything else STOPs for a human: a clean shutdown, a SIGTERM the driver never sends, a SIGKILL without OOM evidence,
# no exit status without a reboot, no poller evidence, an unreadable journal, a relaxation log with a traceback and an
# exit status other than 137 or none, unless it exited 1 and the log ends with the exception line. A QE chain cut by
# a reboot whose journal cannot be read STOPs before anything is listed (an operator's step7/cause.chain.C<n> resolves
# it); one whose boot journal is read but does not show a hard stop (a clean shutdown, no or a stale poller heartbeat,
# a stale or contradicted spot notice) is listed 'cause undetermined' with a WARN.
# A relaxation or MD run that ended with a Python exception has no rerun (an MD MemoryError: oom, as scripts/41
# allows); the first such end STOPs so a systematic failure cannot use up the other runs. A relaxation that died of a
# Python MemoryError STOPs for a human (runbook vs item 4). A launch the script refused is never re-issued
# automatically. A job running for more than 3 times its expected length STOPs for a human (nothing new starts; the
# driver never kills it). A human resolves a STOP for one label with the file the STOP line names,
# /data/work/wp3/step7/cause.<label>.att<n> (n = the script's attempt count), holding
# '<spot-reclaim|node-loss|oom|wall-time|final|retry|accept> <note>' (which words apply is said in the STOP line),
# then relaunches. A cause file that matches no current STOP is moved aside (.unused.<time>) and logged.
# KEEP_ALIVE: not used. No phase is idle: 7a and the pool run MACE (1-min load >= 6), the chain runs pw.x, and the
# driver moves between phases at once. After STEP7_DONE or a STOP the node is idle and the cost guard may stop it.
# (The operator keeps /data/KEEP_ALIVE while the node waits for step 6, and removes it once this driver has started;
# the driver warns while it exists.)
# Never edit this file in place while it runs: install a new copy as <file>.new, check its sha256, then mv it.
set -euo pipefail
{   # the whole body is parsed before any of it runs
# ---- paths and constants (the laptop e2e harness rewrites only the paths in this block)
R=/data/work/ps_wp3; PY=/data/miniforge3/envs/mace/bin/python; SPY=/usr/bin/python3
W=/data/work/wp3; J=/data/jobs; KA=/data/KEEP_ALIVE; CHAIN=/data/setup/chain.sh; QLOCK=/tmp/qe_queue_wp3b.lock
FM=/home/ericdft/.cache/mace/20231203mace128L1_epoch199model; BOOTF=/proc/sys/kernel/random/boot_id
JCTL="sudo -n journalctl"   # the ONE way the journal is read (cls.py); ericdft may run it, and is not in adm/systemd-journal
SPOT_URL=http://100.100.100.200/latest/meta-data/instance/spot/termination-time
FOUNDATION=01bfe22100139f424713cf921144e5509cbe353d67aa9fa1be9c6e1e0ed35845
S=$W/step7; B=$W/wp3b; RW=$W/wp3b/relax; MW=$W/wp3md; QE=$J/wp3b; LIST=$W/step7_reruns.list; LOG=$W/step7.log
BUDGET=64; T_RELAX=6; T_MD=8; TICK=5; NOTICE_HOLD=1800
WALL_RELAX=36000; WALL_MD=15000   # 3 x expected: FIRE 10 000 steps x ~1.2 s/call at 6 threads; 5000 MD steps x ~1.0 s/call at 8
HOSTS="m30 m32"; SYSTEMS="undoped GA Sr"
FROZEN="scripts/39_wp3_evaluate.py scripts/40_wp3b.py scripts/41_wp3_md.py scripts/22_paired_pilot.py scripts/29_dopant_shell_scan.py
 scripts/30_qe_singlepoint.py scripts/32_dft_validation_analysis.py scripts/35_finetune_frames.py scripts/37_dft_eb_analysis.py
 scripts/38_wp2e_displacement.py scripts/checks.py"
# every file step 7 executes or imports (scripts/40, 41, the helpers they load, the two drivers) and the repository
# data scripts/40 reads (region: pool and vac-ref; zeroshot and relax: WP2b image 0, WP2e relaxation): identical at
# <CNOTE> and <C6>, so step 7 at <C6> runs exactly what the note commit holds
STEP7_CODE="scripts/40_wp3b.py scripts/41_wp3_md.py scripts/22_paired_pilot.py scripts/29_dopant_shell_scan.py
 scripts/30_qe_singlepoint.py scripts/32_dft_validation_analysis.py scripts/35_finetune_frames.py scripts/37_dft_eb_analysis.py
 scripts/38_wp2e_displacement.py scripts/checks.py scripts/wp3_runbook/node_step7.sh scripts/wp3_runbook/node_relaunch.sh"
STEP7_DATA="results/fa_host results/objective2/dopant_shell/wp2b results/objective2/dopant_shell/wp2e"
DRV_REL=scripts/wp3_runbook/node_step7.sh; RL_REL=scripts/wp3_runbook/node_relaunch.sh; RLA=/data/work/wp3_relaunch.sh
S39=scripts/39_wp3_evaluate.py
EVAL=results/objective2/dopant_shell/wp3/wp3_eval.json
NOTE_RE='^results/objective2/dopant_shell/wp3/MODEL_NOTE_[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$'
RELAX_JOBS=""; for u in u ""; do for h in $HOSTS; do for s in $SYSTEMS; do RELAX_JOBS="$RELAX_JOBS wp3b${u}_${h}_${s}_img0"; done; done; done
MD_JOBS=""; for T in 450 300; do for h in $HOSTS; do for s in $SYSTEMS; do MD_JOBS="$MD_JOBS wp3md_${h}_${s}_md${T}"; done; done; done
ALL="$RELAX_JOBS $MD_JOBS"
mkdir -p $S
log(){ echo "[$(date -u +%FT%TZ)] $*" >> $LOG; }
# one instance only; the lock (fd 8) is inherited by every child (scripts/40, scripts/41, the QE chain, the poller),
# so a relaunch is refused while anything an earlier instance started is alive. A reboot releases it.
exec 8>>$W/step7.lock
flock -n 8 || { log "launch refused: another node_step7, or a process it started, holds step7.lock"; exit 0; }
[ -e $W/STEP7_DONE ] && { log "launch: STEP7_DONE exists, nothing to do"; exit 0; }
rm -f $W/STEP7_STOPPED
case $0 in /*) SELF=$0;; *) SELF=$PWD/$0;; esac   # this file, absolute (before the cd): pre() hashes it
cd $R

RUNNING=""      # entries <label>:<launch>:<threads>:<wrapper pid>
POLLER=""; STOPR=""; TERMREQ=0; TERMLOGGED=0; FINAL_STOP=0; GATE=closed; PUBTRIED=""; WPID=""; SYNC_RC=""; HOLD=0; HOLDLOG=0
CL_STATE=""; CL_N=0; CL_CAUSE=""; CL_EVID=""; CL_NEW=0; CL_FKIND=""; CL_DETAIL=""; CL_PROV=""; CL_UNUSED=""; CL_TRANSIENT=""; QEP=""
V_STATE=""; V_DETAIL=""; V_SUMMARY=""
SHA=""; CNOTE=""; HC=""; CS=""; RUN=""; BOOT=""
gv(){ local n=$1; printf '%s' "${!n-}"; }
sv(){ printf -v "$1" '%s' "$2"; }
stamp(){ date -u +%FT%TZ; }
add_stop(){   # a reason to stop: nothing new starts; STEP7_STOPPED (holding the reasons) at once, so a relaunch is
  STOPR="${STOPR:+$STOPR | }$*"; log "STOP pending: $*"   # refused (and names them) even if a reclaim cuts the wait short
  echo "$(stamp) STOP pending: $*" >> $W/STEP7_STOPPED; sync
}
alive_children(){ local e n=0; for e in $RUNNING; do kill -0 "${e##*:}" 2>/dev/null && n=$((n+1)); done; NALIVE=$n; }
wait_children(){ local t=0; NALIVE=0; alive_children
  while [ "$NALIVE" -gt 0 ]; do
    [ $((t % 600)) = 0 ] && log "waiting for $NALIVE running child(ren) before exiting: $RUNNING"
    sleep 10; t=$((t+10)); alive_children
  done
  local e; for e in $RUNNING; do wait "${e##*:}" 2>/dev/null || true; done; }
kill_poller(){ if [ -n "$POLLER" ]; then kill "$POLLER" 2>/dev/null || true; wait "$POLLER" 2>/dev/null || true; POLLER=""; fi; }
finish_stop(){ trap - ERR; wait_children; kill_poller; FINAL_STOP=1; log "STOP: $STOPR; STEP7_DONE not written"
  echo "$(stamp) STOP: $STOPR" >> $W/STEP7_STOPPED; sync; exit 1; }
stop(){ add_stop "$*"; finish_stop; }
on_err(){ trap - ERR; local c=${BASH_COMMAND%%$'\n'*}; stop "unexpected error (exit $1) at line $2: ${c:0:160}"; }
on_exit(){ local rc=$?; trap - ERR
  if [ $rc != 0 ] && [ $FINAL_STOP = 0 ]; then
    log "STOP: unexpected exit $rc (last command: ${BASH_COMMAND:0:160}); STEP7_DONE not written"
    { echo "$(stamp) STOP: unexpected exit $rc" >> $W/STEP7_STOPPED || touch $W/STEP7_STOPPED; } 2>/dev/null || true; sync
    wait_children
  fi
  kill_poller; }
trap 'on_err $? $LINENO' ERR
trap on_exit EXIT
trap 'TERMREQ=1' TERM HUP INT
chk_term(){ [ $TERMREQ = 0 ] || stop "terminated by a signal (TERM/HUP/INT)"; }

# ---- helpers, written afresh at every start from this file (so they always match the running driver)
mkdir -p $S/bin $S/jobs $S/spot $S/chain $S/sync $B $RW $MW
cat > $S/bin/cls.py.tmp <<'PYEOF'
# node_step7 classifier (stdlib only): the state of one relaxation or MD run from the script's own files, the
# driver's launch records and the boot/OOM evidence. Prints shell assignments CL_*. Writes one fsynced
# att<n>.cause per script attempt the first time it classifies that attempt; later calls reuse it. Operator files are
# per attempt: <op>.att<n> (the STOP line names it); one that matches no current STOP is moved aside (.unused.<time>).
import argparse, glob, json, os, re, shlex, subprocess, sys, time
CAUSES = ("spot-reclaim", "node-loss", "oom", "wall-time")                 # scripts/40 RERUN_CAUSES = scripts/41 CAUSES
MEM = ("MemoryError", "out of memory", "can't allocate memory", "Cannot allocate memory")   # scripts/41 MEMORY_ERRORS
MAX_ATT = 3                                                                # first run + at most two reruns (both scripts)
TB = "Traceback (most recent call last)"
# Journal lines are read as '-o short-unix': '<epoch>.<usec> <host> <ident>[<pid>]: <message>'. The continuation lines
# of a multi-line message are indented and carry no time stamp: only TS lines are entries.
TS = re.compile(r"^(\d{9,}\.\d{6})\s")
HEAD = r"^\d+(?:\.\d+)?\s+\S+\s+"                 # time stamp and host: what follows is the identifier field
SYS1 = re.compile(HEAD + r"systemd\[1\]: ")
# A clean shutdown: SYSTEM-level evidence only, in the identifier field of an entry (a message that quotes such text,
# e.g. sudo's COMMAND=..., is not one). systemd[1] (PID 1, the system manager) reaching a shutdown target or
# 'Shutting down.', systemd-shutdown[1], or systemd-logind announcing it. A user manager (systemd[<pid> != 1]) reaches
# its own 'shutdown.target - Shutdown.' at every last-session logout, and journald logs 'Journal stopped' at a restart
# too: neither is evidence. Both message forms of systemd[1] ('<unit>.target - <description>.' since systemd 249, the
# description alone before) are accepted.
CLEAN = re.compile(HEAD + r"(?:systemd\[1\]: (?:Reached target (?:(?:shutdown|poweroff|reboot|halt|kexec|final)\.target\b"
                   r"|(?:System Power Off|Power-Off|System Reboot|Reboot|System Halt|Halt|System Shutdown|Shutdown|"
                   r"Late Shutdown Services)\.)|Shutting down\.\s*$)"
                   r"|systemd-shutdown\[1\]: "
                   r"|systemd-logind\[\d+\]: (?:System is (?:powering down|rebooting|halting)|Power key pressed))")
GAP = 1800        # s: a boot's journal ending this long before the poller's last heartbeat (or the launch) does not cover
                  # the end of that boot (the node logs cron/sysstat every <= 10 min; journald syncs every 5 min)
OOM_LAG = 300     # s: an exit 137 younger than this without a kernel OOM line is re-read at the next start (journal lag)
UNUSED = []

def emit(**kw):
    if UNUSED:
        kw["UNUSED"] = " ".join(UNUSED)
    for k, v in kw.items():
        print(f"CL_{k}={shlex.quote(' '.join(str(v).split()))}")
    sys.exit(0)

def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def fsync_dir(d):
    fd = os.open(d, os.O_RDONLY); os.fsync(fd); os.close(fd)

def dump(obj, path):
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=1); fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp, path)
    fsync_dir(os.path.dirname(os.path.abspath(path)))

def move(src, dst):                                # an operator file, renamed once used (or unused); the rename is fsynced
    os.replace(src, dst)
    fsync_dir(os.path.dirname(os.path.abspath(dst)))

def kv(path):
    d = {}
    with open(path) as fh:
        for ln in fh:
            if "=" in ln:
                k, v = ln.rstrip("\n").split("=", 1); d[k] = v
    return d

def last_line(t):
    t = [x for x in (t or "").strip().splitlines() if x.strip()]
    return t[-1][:200] if t else ""

def exc_lines(t, truncated=False):
    """The exception line(s) of the LAST traceback in t: the unindented lines after its last 'Traceback' header.
    Quoted source lines (indented) never count, so a memory error is the raised exception's, not a word in the code."""
    t = t or ""
    if truncated:                                  # a tail cut at a fixed length starts mid-line
        t = t.split("\n", 1)[1] if "\n" in t else ""
    if TB not in t:
        return []
    return [x for x in t.rsplit(TB, 1)[1].splitlines()[1:] if x.strip() and x[0] not in " \t"]

def memory_error(t, truncated=False):
    return any(m in x for x in exc_lines(t, truncated) for m in MEM)

def jctl(a, extra):
    """The ONE journal reader: a.jctl is 'sudo -n journalctl' (the driver's $JCTL). Returns (lines, None, warning), or
    (None, why, '') if sudo or journalctl failed or printed nothing: with system access every boot has entries, so an
    empty answer is a failed read, never 'no evidence of a shutdown or OOM kill'. The warning is journalctl's stderr
    on success (e.g. a truncated file it skipped): it goes into the evidence."""
    try:
        p = subprocess.run(shlex.split(a.jctl) + extra, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           universal_newlines=True, timeout=180)
    except Exception as e:
        return None, f"{a.jctl} could not run ({type(e).__name__}: {e})", ""
    if p.returncode != 0:
        return None, f"'{a.jctl} {' '.join(extra)}' exited {p.returncode}: {' '.join(p.stderr.split())[:160] or 'no message'}", ""
    if not p.stdout.strip():
        return None, f"'{a.jctl} {' '.join(extra)}' printed nothing", ""
    return p.stdout.splitlines(), None, " ".join(p.stderr.split())[:160]

def utc(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))

def jw(w):
    return f" (journalctl warned: {w})" if w else ""

def jcheck(jcmd):
    """pre(): the system journal (at least one systemd[1] line) and the kernel journal (at least one line) of this
    boot are readable through jcmd, and the journal is persistent (it lists at least two boots). Without them a hard
    stop could not be told from a clean shutdown or an OOM kill."""
    a = argparse.Namespace(jctl=jcmd)
    s, e1, _ = jctl(a, ["-b", "0", "-q", "--no-pager", "-o", "short-unix", "_PID=1", "-n", "20"])
    k, e2, _ = jctl(a, ["-k", "-b", "0", "-q", "--no-pager", "-o", "short-unix", "-n", "20"])
    b, e3, _ = jctl(a, ["--list-boots", "--no-pager"])
    s1 = [x for x in (s or []) if SYS1.search(x)]
    nb = [x for x in (b or []) if re.match(r"\s*-?\d+\s+[0-9a-f]{32}\s", x)]
    if s1 and k and len(nb) >= 2:
        emit(STATE="ok", DETAIL=f"system journal ({len(s1)} systemd[1] line(s)) and kernel journal ({len(k)} line(s)) of "
                                f"this boot readable through '{jcmd}'; {len(nb)} boots listed (persistent journal)")
    sm = "ok" if s1 else "no systemd[1] line" + (f" ({e1})" if e1 else "")
    km = "ok" if k else f"no line ({e2})"
    bm = f"{len(nb)} listed" + (f" ({e3})" if e3 else "") + ("" if len(nb) >= 2 else ", at least 2 needed: the journal is "
                                                             "not persistent, so the end of a boot cut by a reclaim could "
                                                             "never be read")
    emit(STATE="stop", DETAIL=(f"the journal is not readable through '{jcmd}': system journal of this boot: {sm}; "
                               f"kernel journal: {km}; boots: {bm}. The classifier "
                               "needs both (clean-shutdown and OOM evidence) and the journals of earlier boots. ericdft "
                               "reads them only through 'sudo -n journalctl' ('sudo -n true' must succeed); fix that, then "
                               "relaunch"))

def nodash(b):
    return b.replace("-", "")

def boot_cause(a, boot, since=None):
    """(kind, cause, evidence, transient) for an attempt whose process vanished with the boot it started in (since:
    the epoch of its launch in that boot). The end of that boot is the last entry of its system journal. A journal
    that cannot be read (sudo or journalctl error, a boot no longer in the journal, an empty answer, no time-stamped
    entry, no systemd[1] entry) or that does not cover the end of the boot gives no evidence at all: a STOP, marked
    transient (not kept), so the next start classifies the attempt again; never node-loss or spot-reclaim from missing
    evidence."""
    notice, hbf = os.path.join(a.spot, f"notice.{boot}"), os.path.join(a.spot, f"heartbeat.{boot}")
    jl, err, warn = jctl(a, ["-b", nodash(boot), "-q", "--no-pager", "-o", "short-unix", "-n", "200"])
    st = [float(m.group(1)) for m in (TS.match(x) for x in (jl or [])) if m]
    if jl and not st:
        err = f"none of its last {len(jl)} lines is a time-stamped entry ({last_line(jl[-1])[:80]})"
    if not err:                                    # the system part of that boot is there (not only user-1000 files)
        p1, e1, _ = jctl(a, ["-b", nodash(boot), "-q", "--no-pager", "-o", "short-unix", "_PID=1", "-n", "1"])
        if e1 or not any(SYS1.search(x) for x in p1):
            err = f"it holds no systemd[1] entry ({e1 or 'none in the answer'}): the system journal of that boot is missing"
    if err:
        return "stop", None, (f"the system journal of boot {boot[:8]} could not be read ({err}): no evidence of how that "
                              "boot ended (hard stop, clean shutdown, OOM); not classified, not kept: fix the journal access "
                              "and relaunch, or decide by hand"), True
    end = st[-1]                                   # the last entry (continuation lines carry no time stamp)
    if since is not None and end < since - GAP:
        return "stop", None, (f"the system journal of boot {boot[:8]} ends at {utc(end)}, {since - end:.0f} s before the "
                              f"launch at {utc(since)}{jw(warn)}: it does not cover the end of that boot; not classified, "
                              "not kept: decide by hand"), True
    clean = [x for x in jl if CLEAN.search(x)]
    if os.path.exists(notice):
        t = open(notice).read().split()
        nt = float(t[1]) if len(t) > 1 else None
        if clean:
            return "stop", None, (f"boot {boot[:8]} has a spot notice ({' '.join(t)}) but its system journal ends with a "
                                  f"clean shutdown ({clean[-1][:100]}): contradictory evidence"), False
        if nt is not None and end - nt > 3600:
            return "stop", None, (f"the spot notice of boot {boot[:8]} ({' '.join(t)}) is {end - nt:.0f} s older than the "
                                  "end of that boot's journal: not the notice of this stop?"), False
        return "rerun", "spot-reclaim", (f"spot termination notice recorded in boot {boot[:8]} at {t[0] if t else '?'} "
                                         f"(termination-time {' '.join(t[2:]) or '?'}); the node booted again (boot "
                                         f"{a.boot[:8]}); that boot's system journal: no system-level shutdown"
                                         f"{jw(warn)}"), False
    if clean:
        return "stop", None, (f"boot {boot[:8]} ended with a clean shutdown ({clean[-1][:100]}) and no spot notice was "
                              "recorded: not a hard stop; cause unknown (operator or idle stop?)"), False
    if not os.path.exists(hbf):
        return "stop", None, f"no spot-poller heartbeat in boot {boot[:8]}: a reclaim notice could have been missed", False
    hb = open(hbf).read().split()
    hbt = float(hb[0])
    if end - hbt > 300:
        return "stop", None, (f"the spot poller's last good poll in boot {boot[:8]} was {end - hbt:.0f} s before "
                              "the end of that boot's system journal: a reclaim notice could have been missed"), False
    if hbt - end > GAP:                            # the journal stopped early: a later clean shutdown would be unseen
        return "stop", None, (f"the system journal of boot {boot[:8]} ends at {utc(end)}, {hbt - end:.0f} s before the "
                              f"spot poller's last good poll ({utc(hbt)}){jw(warn)}: it does not cover the end of that "
                              "boot (journald stopped early, a full root filesystem?), so a clean shutdown after that "
                              "point could not be seen; not classified, not kept: decide by hand"), True
    return "rerun", "node-loss", (f"the node booted again (boot {a.boot[:8]}) after the attempt started in boot {boot[:8]}; "
                                  f"no spot termination notice was recorded (poller alive, last good poll "
                                  f"{hb[1] if len(hb) > 1 else hb[0]}); that boot's system journal (sudo) ends at "
                                  f"{utc(end)} with no system-level shutdown{jw(warn)}"), False

def oom(a, pid, boot, since=None):
    """(OOM-kill line or None, why, transient): transient if the kernel journal could not be read. Only a line at or
    after the launch (since, less 60 s) counts: an earlier holder of the same pid in that boot is not this process."""
    if not pid:
        return None, "no pid recorded", False
    jl, err, warn = jctl(a, ["-k", "-b", nodash(boot), "-q", "--no-pager", "-o", "short-unix"])
    if err:
        return None, f"the kernel journal of boot {boot[:8]} could not be read: {err}", True
    pat = re.compile(rf"(Killed process {pid}\b|[ ,]pid={pid}[, ])")
    hits = []
    for x in jl:
        m = TS.match(x)
        if m and (since is None or float(m.group(1)) >= since - 60) and pat.search(x) and \
                ("oom" in x.lower() or "out of memory" in x.lower()):
            hits.append(x)
    return (hits[-1] if hits else None), ("" if hits else f"no kernel OOM-kill line for pid {pid} in the kernel journal of "
                                                          f"boot {boot[:8]} after its launch{jw(warn)}"), False

def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None

def launches_of(jobdir):
    out = []
    os.makedirs(jobdir, exist_ok=True)
    for f in sorted(os.listdir(jobdir)):
        m = re.fullmatch(r"L(\d+)\.launch", f)
        if not m:
            continue
        L = kv(os.path.join(jobdir, f)); L["seq"] = int(m.group(1))
        p = os.path.join(jobdir, f"L{L['seq']}")
        if os.path.exists(p + ".pid"):
            L["pid"] = open(p + ".pid").read().strip()
        if os.path.exists(p + ".rc"):
            L["rc_mtime"] = os.path.getmtime(p + ".rc")
            try:
                L["rc"] = int(open(p + ".rc").read().split()[0])
            except (ValueError, IndexError):
                L["rc"] = None
        if os.path.exists(p + ".log"):
            with open(p + ".log", errors="replace") as fh:
                L["logtail"] = fh.read()[-20000:]
        out.append(L)
    out.sort(key=lambda x: x["seq"])
    return out

def run_launch(launches, n):
    """The launch that made attempt n: the last run-mode launch expecting n (unique: a launch that left no attempt
    is followed by a re-issue with the same expect, a recorded attempt by a launch expecting n+1)."""
    c = [x for x in launches if x.get("mode") == "run" and str(x.get("expect")) == str(n)]
    return c[-1] if c else None

def read_op(p):
    w = open(p).read().split(None, 1)
    return (w[0] if w else ""), (w[1].strip() if len(w) > 1 else "")

def tidy(a, keep=None):
    """Move aside every operator file of this label except `keep` (the one that would resolve its current STOP)."""
    pat = re.compile(re.escape(os.path.basename(a.op)) + r"(\.att\d+)?")
    for f in sorted(glob.glob(glob.escape(a.op) + "*")):
        if f != keep and pat.fullmatch(os.path.basename(f)):
            dst = f"{f}.unused.{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
            move(f, dst); UNUSED.append(os.path.basename(dst))

def hint(op, allowed):
    return f" [to resolve: write '<{'|'.join(allowed)}> <note>' to {op}, then relaunch]"

def derive(a, n, att, launches, kind):
    started = att.get("started") or att.get("started_utc")
    pid = att.get("pid")
    L = run_launch(launches, n)
    base = {"attempt": n, "attempt_started": started, "decided_utc": now()}
    if L is None:
        return {**base, "kind": "stop", "cause": None,
                "evidence": f"attempt {n} (started {started}, pid {pid}) has no node_step7 launch record (run by hand?): decide by hand"}
    if L.get("pid") and pid is not None and str(pid) != L["pid"]:
        return {**base, "kind": "stop", "cause": None,
                "evidence": (f"attempt {n} (started {started}) has pid {pid}, but node_step7 launch L{L['seq']} (attempt {n}) "
                             f"started pid {L['pid']}: the attempt was made by another process (by hand?): decide by hand")}
    base.update({"launch": f"L{L['seq']}", "launch_boot": L["boot"], "pid": L.get("pid")})
    r = lambda kd, cause, ev, **x: {**base, "kind": kd, "cause": cause, "evidence": ev, **x}
    rc, logt = L.get("rc"), L.get("logtail", "")
    pidnote = "" if L.get("pid") else f" (launch L{L['seq']}'s pid file was lost; matched by attempt number)"
    tbnote = ""
    if kind == "md":
        st, det = att.get("status"), att.get("detail") or ""
        if st == "exception":
            ex = " / ".join(exc_lines(det, len(det) >= 3990))[:200] or last_line(det)
            if memory_error(det, len(det) >= 3990):
                return r("rerun", "oom", f"attempt {n} ended with a Python exception that is a memory error "
                                          f"(scripts/41 attempts: {ex})")
            if any(m in det for m in MEM):
                return r("stop", None, f"attempt {n} ended with a Python exception ({ex}); a memory error appears in its "
                                       "traceback but is not the exception that ended it: decide by hand",
                         allow_op=["oom", "final"])
            return r("final", None, f"attempt {n} ended with a Python exception ({ex}); runbook 7d: an MD run "
                                    "that ended with an exception has no rerun (only oom with a memory error)",
                     final_kind="exception")
        if st == "complete":
            return r("stop", None, f"attempt {n} has status 'complete' but its record is missing (scripts/41 never reruns it)",
                     allow_op=["final"])
        if st == "terminated":
            return r("stop", None, f"attempt {n} was ended by SIGTERM/SIGINT (status 'terminated'), which node_step7 never "
                                   "sends: cause unknown")
        if st != "started":
            return r("stop", None, f"attempt {n} has the unknown status {st!r}")
    elif TB in logt:
        xl = exc_lines(logt)
        nb = [x for x in logt.splitlines() if x.strip()]
        ex = " / ".join(xl)[:200] or last_line(logt)
        if rc == 1 and xl and nb and nb[-1] == xl[0]:   # exit 1 and the log ENDS with the exception line: uncaught
            # (a multi-line message, or any output after the traceback, is not this: a human decides)
            if memory_error(logt) or any(m in logt.rsplit(TB, 1)[1] for m in MEM):
                return r("stop", None, f"attempt {n} ended with a Python exception ({ex}) that is or involves a memory error. "
                                       "The runbook gives a relaxation that ended with an exception no rerun; item 4 reruns "
                                       "one stopped by OOM. Decide by hand", allow_op=["oom", "final"])
            return r("final", None, f"attempt {n} ended with a Python exception ({ex}); runbook 7d: a relaxation "
                                    "that ended with an exception has no rerun", final_kind="exception")
        if rc not in (None, 137):
            return r("stop", None, f"attempt {n} ended with exit {rc}; its log holds a Python traceback ({ex}) that is not "
                                   "the end of an exit-1 log: not a clear exception end; decide by hand")
        tbnote = f"; its log also holds an earlier traceback ({ex}), which did not end the process"
    if rc is not None:
        if rc in (137, -9):
            hit, why, tr = oom(a, L.get("pid"), L["boot"], num(L.get("epoch")))
            if hit:
                return r("rerun", "oom", f"attempt {n} was killed by the kernel OOM killer ({hit.strip()[:160]}){tbnote}")
            if tr:                                 # no evidence either way: not kept, classified again at the next start
                return r("stop", None, f"attempt {n} was killed by SIGKILL (exit {rc}) and {why}: whether the OOM killer "
                                       f"did it is unknown; not kept: fix the journal access and relaunch, or decide by "
                                       f"hand{tbnote}", transient=True)
            age = time.time() - L["rc_mtime"] if L.get("rc_mtime") else None
            if age is not None and age < OOM_LAG:  # journald may not have stored the kernel line yet: read it again later
                return r("stop", None, f"attempt {n} was killed by SIGKILL (exit {rc}) {age:.0f} s ago, and so far {why}: "
                                       "not kept, read again at the next start (a kill by systemd-oomd or earlyoom, "
                                       f"logged outside the kernel journal, also ends here){tbnote}", transient=True)
            return r("stop", None, f"attempt {n} was killed by SIGKILL (exit {rc}) without OOM evidence ({why}): cause "
                                   f"unknown (a kill by systemd-oomd or earlyoom is logged outside the kernel journal){tbnote}")
        return r("stop", None, f"attempt {n} ended with exit {rc}, no record and no Python traceback (last log line: "
                               f"{last_line(logt) or 'none'}): cause unknown")
    if L["boot"] == a.boot:
        return r("stop", None, f"attempt {n} has no exit status and the node did not reboot after it started (were it "
                               f"and the driver killed?): cause unknown{tbnote}")
    kd, cause, ev, tr = boot_cause(a, L["boot"], num(L.get("epoch")))
    return r(kd, cause, f"attempt {n}: " + ev + pidnote + tbnote, **({"transient": True} if tr else {}))

def complete_check(a, rec, attp, launches):
    """A complete output is adopted only if the node_step7 launch that made its attempt is on record (item 2: no
    test-host prediction outside the committed-note order); verify.py then checks the commit it was made at."""
    try:
        r = json.load(open(rec))
        if a.kind == "relax":
            al = r.get("attempts") or []
            att = al[-1] if al else {}
            n = att.get("attempt")
        else:
            al = json.load(open(attp)).get("attempts", []) if os.path.exists(attp) else []
            n = r.get("attempt")
            att = al[n - 1] if isinstance(n, int) and 1 <= n <= len(al) else {}
    except Exception as e:
        tidy(a)
        return dict(STATE="stop", DETAIL=f"{rec} or its attempt log unreadable ({type(e).__name__}): decide by hand")
    if not isinstance(n, int) or not att:
        tidy(a)
        return dict(STATE="stop", DETAIL=f"{rec}: no attempt entry for the record's attempt {n}: decide by hand")
    pid = att.get("pid")
    acc = os.path.join(a.jobdir, f"accepted.att{n}")
    if os.path.exists(acc):
        tidy(a)
        return dict(STATE="complete", N=n, PROV=f"accepted by the operator: {json.load(open(acc)).get('note')}")
    L = run_launch(launches, n)
    why = None
    if L is None:
        why = f"its attempt {n} (pid {pid}, started {att.get('started') or att.get('started_utc')}) has no node_step7 launch record"
    elif L.get("pid") and str(pid) != L["pid"]:
        why = f"its attempt {n} has pid {pid}, but node_step7 launch L{L['seq']} (attempt {n}) started pid {L['pid']}"
    if why is None:
        tidy(a)
        return dict(STATE="complete", N=n, PROV=f"launch L{L['seq']}" + ("" if L.get("pid") else " (pid file lost; matched by attempt number)"))
    op = f"{a.op}.att{n}"
    if os.path.exists(op):
        oc, note = read_op(op)
        if oc != "accept":
            tidy(a, keep=op)
            return dict(STATE="stop", N=n, DETAIL=f"operator file {op}: '{oc}' is not 'accept'; driver: a complete output "
                                                    f"that no node_step7 launch made: {why}")
        dump({"attempt": n, "pid": pid, "note": note, "accepted_utc": now(), "why": why}, acc)
        move(op, op + ".used"); tidy(a)
        return dict(STATE="complete", N=n, NEW=1, PROV=f"accepted by the operator: {note}",
                    DETAIL=f"{why}; operator ({os.path.basename(op)}): accept: {note}")
    tidy(a, keep=op)
    return dict(STATE="stop", N=n, DETAIL=(f"{os.path.basename(rec)} is a complete output that no node_step7 launch made: "
                f"{why} (made by hand?). Item 2: no test-host prediction may predate the committed note; the driver never "
                f"adopts an output it did not start. Move every file of {a.label} aside (work and queue directories) and "
                f"record why, or, if it was made at the step-7 checkout commit (STEP6_DONE) by the identical command (the "
                f"verifier checks the commit), write 'accept <note>' to {op}; then relaunch"))

def main():
    if sys.argv[1:2] == ["--jcheck"]:                # pre(): journal access through the same reader
        jcheck(sys.argv[2])
    ap = argparse.ArgumentParser()
    for k in ("label", "kind", "work", "jobdir", "boot", "spot", "op", "jctl"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--live", default="")
    ap.add_argument("--bootcause", default="")
    ap.add_argument("--since", default="")
    a = ap.parse_args()
    if a.bootcause:                                  # the cause of a QE chain cut short by a reboot (listed only)
        kd, cause, ev, tr = boot_cause(a, a.bootcause, num(a.since))
        emit(STATE=kd, CAUSE=cause or "", EVID=ev, TRANSIENT=1 if tr else 0)
    rec, attp = os.path.join(a.work, a.label + ".json"), os.path.join(a.work, a.label + ".attempts.json")
    launches = launches_of(a.jobdir)
    if os.path.exists(rec):
        emit(**complete_check(a, rec, attp, launches))
    try:
        atts = json.load(open(attp)) if os.path.exists(attp) else ([] if a.kind == "relax" else {"attempts": []})
        atts = atts if a.kind == "relax" else atts["attempts"]
    except Exception as e:
        emit(STATE="stop", DETAIL=f"{attp} unreadable ({type(e).__name__}): decide by hand")
    n = len(atts)
    op = f"{a.op}.att{n}"
    runs = [x for x in launches if x.get("mode") == "run"]
    last = runs[-1] if runs else None
    if last and str(last.get("expect")) == str(n + 1):   # launched, yet the script recorded no attempt for it
        seq = last["seq"]
        if "rc" not in last:                       # cut short (no exit status: a hard stop) before the script logged it
            tidy(a)
            emit(STATE="reissue", N=n, CAUSE=last.get("cause", ""), EVID=last.get("evid", ""),
                 DETAIL=f"launch L{seq} left no attempt {n + 1} in the script's log (cut short before the script logged it); re-issued")
        why = (f"launch L{seq} ended (exit {last.get('rc')}) before the script recorded attempt {n + 1}: refused or crashed "
               f"early: {last_line(last.get('logtail'))}")
        allowed = ["retry", "final"] + (list(CAUSES) if n else [])
        pf = os.path.join(a.jobdir, f"L{seq}.operator")
        if os.path.exists(pf):                     # the operator's decision on this refusal, already taken: it stands
            d = json.load(open(pf)); ev = d.get("evidence", "")
            tidy(a)
            if d.get("choice") == "final":
                emit(STATE="final", N=n, NEW=0, FKIND="operator", DETAIL=ev)
            if d.get("choice") == "retry":         # (a hard stop came before its launch was recorded)
                emit(STATE="reissue", N=n, NEW=0, CAUSE=last.get("cause", ""), EVID=last.get("evid", ""), DETAIL=ev)
            emit(STATE="rerun", N=n, NEW=0, CAUSE=d.get("choice"), EVID=ev)
        if a.live != f"L{seq}" and os.path.exists(op):
            oc, note = read_op(op)
            if oc not in allowed:
                tidy(a, keep=op)
                emit(STATE="stop", N=n, DETAIL=f"operator file {op}: '{oc}' is not one of {allowed}; driver: {why}")
            ev = f"operator ({os.path.basename(op)}, {now()}): {oc}: {note or 'no note'}; driver: {why}"
            dump({"attempt": n, "refused_launch": f"L{seq}", "choice": oc, "note": note, "decided_utc": now(),
                  "evidence": ev}, pf)
            move(op, f"{op}.used.L{seq}"); tidy(a)
            if oc == "final":
                emit(STATE="final", N=n, NEW=1, FKIND="operator", DETAIL=ev)
            if oc == "retry":
                emit(STATE="reissue", N=n, NEW=1, CAUSE=last.get("cause", ""), EVID=last.get("evid", ""), DETAIL=ev)
            emit(STATE="rerun", N=n, NEW=1, CAUSE=oc, EVID=ev)
        tidy(a, keep=op)
        emit(STATE="refused", N=n, DETAIL=why + ". A refused launch is never re-issued automatically" + hint(op, allowed))
    if n == 0:
        tidy(a)
        emit(STATE="first", N=0)
    cf = os.path.join(a.jobdir, f"att{n}.cause")
    new = 0
    if os.path.exists(cf):
        c = json.load(open(cf))
    else:
        c = derive(a, n, atts[-1], launches, a.kind); new = 1
        if not c.get("transient"):                 # a STOP for want of a readable journal is not kept: no evidence yet
            dump(c, cf)
    allowed = c.get("allow_op") or list(CAUSES) + ["final"]
    if c["kind"] == "stop" and os.path.exists(op):
        oc, note = read_op(op)
        if oc not in allowed:
            tidy(a, keep=op)
            emit(STATE="stop", N=n, DETAIL=f"operator file {op}: '{oc}' is not one of {allowed}; driver: {c['evidence']}")
        c = {**{k: v for k, v in c.items() if k != "transient"}, "kind": "final" if oc == "final" else "rerun",
             "cause": None if oc == "final" else oc, "final_kind": "operator" if oc == "final" else None, "operator": True,
             "evidence": f"operator ({os.path.basename(op)}, {now()}): {note or 'no note'}; driver: {c['evidence']}"}
        dump(c, cf); move(op, f"{op}.used"); new = 1
    tidy(a, keep=op if c["kind"] == "stop" else None)
    if c["kind"] == "rerun":
        if n >= MAX_ATT:
            emit(STATE="final", N=n, NEW=new, FKIND="exhausted",
                 DETAIL=f"attempt {n} also stopped ({c['cause']}: {c['evidence']}); {MAX_ATT} attempts used (1 run + 2 "
                        "reruns): no further rerun; this run cannot be evaluated")
        emit(STATE="rerun", N=n, NEW=new, CAUSE=c["cause"], EVID=c["evidence"])
    if c["kind"] == "final":
        emit(STATE="final", N=n, NEW=new, FKIND=c.get("final_kind") or "", DETAIL=c["evidence"])
    emit(STATE="stop", N=n, NEW=new, DETAIL=c["evidence"] + hint(op, allowed))

main()
PYEOF
cat > $S/bin/verify.py.tmp <<'PYEOF'
# node_step7 verifier (mace-env python, ase): a complete output is re-checked before it counts as complete.
# Prints V_STATE (ok | republish | bad), V_DETAIL, V_SUMMARY. <hc> is the step-7 checkout commit <C6> (STEP6_DONE, a
# descendant of the note commit): every record, every attempt and wp2e_minimum.json must have been made there with no
# uncommitted change (item 2: after the committed note; item 7: after step 6).
import hashlib, json, os, re, shlex, sys
import numpy as np

def emit(state, detail="", summary=""):
    for k, v in (("STATE", state), ("DETAIL", detail), ("SUMMARY", summary)):
        print(f"V_{k}={shlex.quote(' '.join(str(v).split()))}")
    sys.exit(0)

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def norm_sha(p):        # scripts/40 input_norm_sha256: no pseudo_dir line, blank runs collapsed
    with open(p, errors="replace") as fh:
        keep = [re.sub(r"\s+", " ", ln.strip()) for ln in fh.read().splitlines() if not re.match(r"\s*pseudo_dir\s*=", ln)]
    return hashlib.sha256("\n".join(x for x in keep if x).encode()).hexdigest()

def load(p):
    try:
        with open(p) as fh:
            return json.load(fh)
    except Exception as e:
        emit("bad", f"{p} unreadable ({type(e).__name__}: {e})")

def git_bad(g, hc, what):
    """scripts/40 code_state()['git'] / scripts/41 git_state(): made at the step-7 commit <C6>, nothing uncommitted."""
    if not isinstance(g, dict):
        return [f"{what}: no git state (made outside the checkout?)"]
    b = []
    if g.get("head") != hc:
        b.append(f"{what}: made at commit {str(g.get('head'))[:12]}, not the step-7 commit {hc[:12]} (STEP6_DONE)")
    if g.get("uncommitted"):
        b.append(f"{what}: uncommitted changes {g.get('uncommitted')[:3]}")
    if g.get("script_equals_head") is False:
        b.append(f"{what}: the script differs from HEAD")
    return b

mode = sys.argv[1]
if mode == "wp2e":
    p, want, hc = sys.argv[2:5]
    x = load(p)
    miss = [k for k in ("E_model_img0_eV", "E_model_dftmin_eV", "dE_dftmin_minus_img0_meV", "frms_eVA") if k not in x]
    g = git_bad(x.get("git"), hc, "wp2e_minimum.json")
    if (x.get("model") or {}).get("sha256") != want or miss or g:
        emit("bad", f"{p}: model {(x.get('model') or {}).get('sha256')} (want {want}), missing {miss}; {'; '.join(g)}")
    emit("ok", "", f"dE {x['dE_dftmin_minus_img0_meV']:+.1f} meV, force {x['frms_eVA']:.3f} eV/A")
if mode in ("relax", "qein"):
    lab, rw, qe, want, region, hc = sys.argv[2:8]
    rec = load(f"{rw}/{lab}.json")
    f = rec.get("files") or {}
    q, m = f"{qe}/{lab}/{lab}.in", f"{qe}/{lab}/{lab}.meta.json"
    if mode == "qein":
        if not os.path.isfile(q) or norm_sha(q) != f.get("qe_input_norm_sha256"):
            emit("bad", f"{q} missing or not the recorded input (normalised sha256)")
        emit("ok")
    bad = []
    if rec.get("label") != lab or rec.get("constrained") != (not lab.startswith("wp3bu_")):
        bad.append(f"label/constraint {rec.get('label')}/{rec.get('constrained')}")
    if (rec.get("model") or {}).get("sha256") != want:
        bad.append(f"model sha256 {(rec.get('model') or {}).get('sha256')}")
    p = rec.get("protocol") or {}
    if p.get("steps_cap") != 10000 or p.get("plan_protocol") is not True:
        bad.append(f"step cap {p.get('steps_cap')} (smoke test)")
    if rec.get("region_id") != load(region).get("region_id"):
        bad.append("region_id differs from the region file")
    if os.path.abspath(f.get("qe_input", "")) != os.path.abspath(q):
        bad.append(f"qe_input {f.get('qe_input')}")
    bad += git_bad(rec.get("git"), hc, "record")
    al = rec.get("attempts") or []
    if not al:
        bad.append("no attempt entries")
    for e in al:
        bad += git_bad(e.get("git"), hc, f"attempt {e.get('attempt')}")
    if bad:
        emit("bad", "record: " + "; ".join(bad))
    stage = f"{rw}/{lab}.qe/{lab}.in"
    if not os.path.isfile(stage) or sha(stage) != f.get("qe_input_sha256"):
        emit("bad", f"staged QE input {stage} missing or not the recorded one")
    from ase.io import read
    try:
        st, inp = read(f"{rw}/{lab}.extxyz"), read(stage, format="espresso-in")
    except Exception as e:
        emit("bad", f"relaxed structure or staged input unreadable ({type(e).__name__}: {e})")
    if (st.get_chemical_symbols() != inp.get_chemical_symbols() or np.abs(st.positions - inp.positions).max() > 1e-6
            or np.abs(st.cell.array - inp.cell.array).max() > 1e-6):
        emit("bad", "relaxed structure differs from the staged QE input (1e-6 A, as scripts/40 analyse)")
    summ = (f"{rec.get('steps')} steps, fmax {rec.get('fmax_eVA')}, converged {rec.get('converged')}, "
            f"fails {rec.get('fail_reasons') or 'none'}")
    if not os.path.isfile(q) or not os.path.isfile(m):
        emit("republish", "the queue copy of the QE input (or its meta) is missing", summ)
    if norm_sha(q) != f.get("qe_input_norm_sha256"):
        emit("bad", f"{q} is not the recorded input (normalised sha256)", summ)
    emit("ok", "", summ)
if mode == "md":
    lab, mw, want, hc = sys.argv[2:6]
    rec = load(f"{mw}/{lab}.json")
    h, s, T = re.fullmatch(r"wp3md_(m\d+)_(undoped|GA|Sr)_md(\d+)", lab).groups()
    p = rec.get("protocol") or {}
    bad = []
    if (rec.get("label"), rec.get("host"), rec.get("system"), rec.get("T_K")) != (lab, h, s, int(T)):
        bad.append("label")
    if rec.get("model_sha256") != want:
        bad.append(f"model sha256 {rec.get('model_sha256')}")
    if rec.get("protocol_ok") is not True or (p.get("steps"), p.get("report_every")) != (5000, 100):
        bad.append("non-protocol steps/report_every (smoke test)")
    if rec.get("threads") != 8:
        bad.append(f"threads {rec.get('threads')}")
    tp = os.path.join(mw, rec.get("trajectory") or "-")
    if not os.path.isfile(tp) or sha(tp) != rec.get("trajectory_sha256"):
        bad.append("trajectory missing or changed")
    att = load(f"{mw}/{lab}.attempts.json").get("attempts", [])
    if rec.get("attempt") != len(att):
        bad.append(f"attempt {rec.get('attempt')} != {len(att)} attempts logged")
    bad += git_bad(rec.get("git"), hc, "record")
    for e in att:
        bad += git_bad(e.get("git"), hc, f"attempt {e.get('n')}")
    if bad:
        emit("bad", "; ".join(bad))
    emit("ok", "", "pass" if rec.get("ok") else f"FAIL at {rec.get('first_failure_fs')} fs: {(rec.get('reasons') or [''])[0]}")
emit("bad", f"unknown mode {mode}")
PYEOF
cat > $S/bin/poller.py.tmp <<'PYEOF'
# node_step7 spot poller: polls the instance metadata every 5 s; a termination notice (HTTP 200) is written at once,
# fsynced, to notice.<boot>; a heartbeat with the time of the last good poll (200 or 404) goes to heartbeat.<boot>
# every 60 s. Exits when its parent (the driver) is gone.
import os, sys, time, urllib.error, urllib.request
_, tag, url, d, boot, ppid = sys.argv
ppid = int(ppid)
os.makedirs(d, exist_ok=True)
notice, hbf = os.path.join(d, f"notice.{boot}"), os.path.join(d, f"heartbeat.{boot}")
op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
utc = lambda t: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))

def write(p, text):
    with open(p + ".tmp", "w") as fh:
        fh.write(text); fh.flush(); os.fsync(fh.fileno())
    os.replace(p + ".tmp", p)
    fd = os.open(d, os.O_RDONLY); os.fsync(fd); os.close(fd)

last_hb = last_err = 0.0; ok = err = 0
print(f"{utc(time.time())} poller start, boot {boot}", flush=True)
while os.getppid() == ppid:
    t = time.time()
    try:
        try:
            with op.open(url, timeout=3) as r:
                code, body = r.status, r.read(300).decode("ascii", "replace").strip()
        except urllib.error.HTTPError as e:
            code, body = e.code, ""
        except Exception as e:
            code, body = None, f"{type(e).__name__}: {e}"
        if code in (200, 404):
            ok += 1
            if code == 200 and not os.path.exists(notice):
                write(notice, f"{utc(t)} {t:.0f} {' '.join(body.split())[:200]}\n")
                print(f"{utc(t)} spot termination notice: {body[:200]}", flush=True)
            if t - last_hb >= 60:
                write(hbf, f"{t:.0f} {utc(t)} ok={ok} err={err}\n"); last_hb = t
        else:
            err += 1
            if t - last_err >= 600:
                print(f"{utc(t)} metadata poll failed ({code}): {body[:200]}", flush=True); last_err = t
    except Exception as e:                         # e.g. a full disk: keep polling; the heartbeat goes stale meanwhile
        print(f"{utc(t)} poller error {type(e).__name__}: {e}", flush=True)
    time.sleep(5)
PYEOF
for f in cls verify poller; do mv -f $S/bin/$f.py.tmp $S/bin/$f.py; done

# ---- preconditions (fail-closed)
# rb_techfail.py's verdict on <run>/wp3.model in a 5a file: pass, fail or none. node_step34 writes the file with 2>&1,
# so library warnings (and mace's own import notice) stand before rb_techfail's lines, and may follow them. Only its own
# lines count: exactly one '<N> m21 frames evaluated with <run>/wp3.model', then on the next line its pass line (pass,
# if no line of the file is a 'non-finite ...' line) or a 'non-finite ...' line (fail, if no line is the pass line).
# rb_model_note.py (techfail_verdict) reads the file the same way.
tf_verdict(){ awk -v r="$2/wp3.model" -v p="no technical failure (items checked here)" '
    nx { v = ($0 == p) ? "pass" : (($0 ~ /^non-finite/) ? "fail" : "none"); nx = 0 }
    $0 == p { np++ }
    /^non-finite/ { nf++ }
    /^[0-9]+ m21 frames evaluated with / && substr($0, index($0, " evaluated with ") + 16) == r { n++; nx = 1; v = "none" }
    END { if (n != 1 || (v == "pass" && nf > 0) || (v == "fail" && np > 0)) v = "none"; print v }' "$1" 2>/dev/null || echo none; }
pre(){
  local x n y z o others dae e1 rt="" rk="" rf="" re tc ev DRVSHA DRVHEAD e_script e_mode e_sha e_si e_cache e_head e_unc e_ssha
  # the installed driver must be the committed one (logged at once; compared once the checkout is known to be <C6>)
  DRVSHA=$( { sha256sum "$SELF" 2>/dev/null || true; } | cut -c1-64)
  DRVHEAD=$( { git show "HEAD:$DRV_REL" 2>/dev/null || true; } | sha256sum | cut -c1-64)
  log "installed driver: sha256sum $SELF = $DRVSHA; git show HEAD:$DRV_REL | sha256sum = $DRVHEAD"
  # the journal: system (systemd[1]) and kernel entries readable through the one reader ($JCTL), or nothing can be
  # classified after a hard stop
  CL_STATE=""; CL_DETAIL=""; eval "$(cls --jcheck "$JCTL")"
  [ "$CL_STATE" = ok ] || stop "$CL_DETAIL"
  log "journal: $CL_DETAIL"
  [ -e $W/STEP34_DONE ] || stop "STEP34_DONE missing: steps 3-5a have not finished"
  [ -s $W/NOTE_COMMITTED ] || stop "NOTE_COMMITTED missing: commit the model note on its own (runbook 5b), then write its full commit to $W/NOTE_COMMITTED (WP3_RUNBOOK appendix A.4)"
  CNOTE=$(tr -d ' \t\r\n' < $W/NOTE_COMMITTED)
  [[ $CNOTE =~ ^[0-9a-f]{40}$ ]] || stop "NOTE_COMMITTED does not hold one full 40-hex commit"
  # step 6 before step 7 (PLAN amendment m item 7): STEP6_DONE names the commit <C6> that adds scripts/39's output
  [ -e $W/STEP6_DONE ] || stop "STEP6_DONE missing: step 6 (scripts/39, once, on the Mac) comes before step 7 (PLAN amendment m item 7). Commit its $EVAL, update the node checkout to that commit <C6>, then write <C6> (one line, the full commit) to $W/STEP6_DONE (WP3_RUNBOOK appendix A.4)"
  { [ "$(grep -c '' $W/STEP6_DONE)" = 1 ] && HC=$(cat $W/STEP6_DONE) && [[ $HC =~ ^[0-9a-f]{40}$ ]]; } \
    || stop "STEP6_DONE must hold exactly one line, the full 40-hex commit <C6> (it holds: $(head -c 130 $W/STEP6_DONE | tr '\n' '|'))"
  x=$(git rev-parse HEAD) || stop "git rev-parse HEAD failed in $R"
  [ "$x" = "$HC" ] || stop "checkout HEAD $x is not STEP6_DONE's commit $HC: update /data/work/ps_wp3 to <C6> first (WP3_RUNBOOK appendix A.4)"
  x=$(git status --porcelain --untracked-files=normal) || stop "git status failed"
  [ -z "$x" ] || stop "checkout not clean: $(echo $x | cut -c1-200) (node_step34's archive copies? move them out as WP3_RUNBOOK appendix A.4 says)"
  [ -n "$DRVSHA" ] && [ "$DRVSHA" = "$DRVHEAD" ] || stop "the installed driver $SELF (sha256 ${DRVSHA:-unreadable}) is not the committed $DRV_REL at $HC (sha256 $DRVHEAD): install the committed file (as <file>.new, check its sha256, mv), then relaunch"
  # the installed relaunch script (it starts step 7 after a reclaim; node_step7 checks its own preconditions): logged
  x=$( { sha256sum $RLA 2>/dev/null || true; } | cut -c1-64); y=$( { git show "HEAD:$RL_REL" 2>/dev/null || true; } | sha256sum | cut -c1-64)
  log "installed relaunch script: sha256sum $RLA = ${x:-missing}; git show HEAD:$RL_REL | sha256sum = $y"
  if [ "$x" != "$y" ]; then log "WARN: the installed $RLA is missing or is not the committed $RL_REL: install the committed file (WP3_RUNBOOK appendix B, Install)"; fi
  x=$(git rev-list --parents -n 1 $CNOTE 2>/dev/null) || stop "the note commit $CNOTE is not in the checkout"
  n=$(echo $x | wc -w)
  [ "$n" -eq 2 ] || stop "the note commit $CNOTE must have exactly one parent (it has $((n-1)))"
  x=$(git diff-tree --no-commit-id --name-status -r $CNOTE)
  NOTE=${x#$'A\t'}
  { [ "$(printf '%s\n' "$x" | wc -l)" -eq 1 ] && [ "${x:0:2}" = $'A\t' ] && [[ $NOTE =~ $NOTE_RE ]]; } \
    || stop "the note commit $CNOTE is not the model note committed on its own (it changes: $(echo $x | cut -c1-200))"
  x=$(git show "$CNOTE:$NOTE") || stop "cannot read $NOTE at $CNOTE"
  # a complete note only (runbook 5b: it records the selected model's m21 offset, the versions and 5a before any
  # test-host prediction); rb_model_note.py writes 'note_status: complete' and the machine-readable lines only then
  if grep -qE '^> \*\*DRAFT|NOT COMPUTED|\*\*Check:\*\*' <<< "$x"; then     # (here-strings: no SIGPIPE under pipefail)
    stop "$NOTE at $CNOTE is not complete (a DRAFT banner, 'NOT COMPUTED' or a '**Check:**' line): only a note for which rb_model_note.py exited 0 may be committed (runbook 5b). A committed note is never changed: write a NEW note under a new date (a new MODEL_NOTE_<YYYY-MM-DD>.md, rb_model_note.py exit 0), add it in a commit of its own, write that commit to NOTE_COMMITTED, and list the committed DRAFT as a deviation in the WP3 result (WP3_RUNBOOK appendix A.3)"
  fi
  [ "$(grep -cxF 'note_status: complete' <<< "$x" || true)" = 1 ] \
    || stop "$NOTE has no single 'note_status: complete' line: not a complete rb_model_note.py note (exit 0)"
  grep -qE '^- Selected model: [-+]?[0-9]+\.[0-9]+ meV/cell' <<< "$x" \
    || stop "$NOTE does not record the selected model's m21 host-wide energy offset (runbook 5b; rb_model_note.py --m21-offset compute)"
  SHA=$(printf '%s\n' "$x" | { grep -E '^model_sha256: [0-9a-f]{64}$' || true; } | cut -c15- | sort -u)
  CS=$(printf '%s\n' "$x" | { grep -E '^scripts_commit: [0-9a-f]{40}$' || true; } | cut -c17- | sort -u)
  NRUN=$(printf '%s\n' "$x" | { grep -E '^run: run[0-9]+$' || true; } | cut -c6- | sort -u)
  { [ ${#SHA} = 64 ] && [ ${#CS} = 40 ] && [ -n "$NRUN" ] && [[ ! $NRUN =~ [[:space:]] ]]; } \
    || stop "$NOTE must hold exactly one 'model_sha256: <64 hex>', one 'scripts_commit: <40 hex>' and one 'run: run<n>' line (rb_model_note.py writes them)"
  [ "$SHA" != $FOUNDATION ] || stop "the note names the zero-shot foundation file: (d) and (e) need the fine-tuned model"
  git cat-file -e "$CS^{commit}" 2>/dev/null || stop "scripts_commit $CS of the note is not in the checkout"
  git merge-base --is-ancestor $CS $CNOTE || stop "scripts_commit $CS is not an ancestor of the note commit $CNOTE"
  for x in $FROZEN; do git cat-file -e "$CNOTE:$x" 2>/dev/null || stop "$x is not in the note commit $CNOTE (the identity checks below would pass for a file absent everywhere)"; done
  git diff --quiet $CS $CNOTE -- $FROZEN || stop "scripts 39/40/41 or a helper they load differ between the note's scripts_commit $CS and $CNOTE"
  # <C6> after <CNOTE>: only results (and a scripts/39 step-6 fix) between them; step 7 runs what the note commit holds
  [ "$CNOTE" != "$HC" ] || stop "STEP6_DONE holds the note commit itself: <C6> is the LATER commit that adds $EVAL (step 6 runs after the note is committed, PLAN item 7)"
  git merge-base --is-ancestor $CNOTE $HC || stop "the note commit $CNOTE is not an ancestor of STEP6_DONE's commit $HC: step 6 and step 7 come after the committed note (PLAN item 7)"
  x=$(git diff --no-renames --name-only $CNOTE $HC)   # both sides of a rename: a file moved into results/ from elsewhere counts
  y=$(printf '%s\n' "$x" | { grep -v '^results/' || true; } | { grep -vxF $S39 || true; })
  [ -z "$y" ] || stop "between the note commit $CNOTE and $HC, files outside results/ changed ($(echo $y | cut -c1-200)): only step-6 results and a scripts/39 fix may come between them"
  if grep -qxF $S39 <<< "$x"; then
    log "WARN: $S39 changed between the note commit and $HC (commits $(git log --format=%h $CNOTE..$HC -- $S39 | tr '\n' ' ')): a step-6 fix (runbook step 6, exit 4/5/6, then step 6 repeated); list these commits and the diff in the WP3 result"
  fi
  if grep -qxF results/objective2/dopant_shell/PLAN.md <<< "$x"; then
    stop "PLAN.md changed between the note commit $CNOTE and $HC: the pre-registration does not change between the committed note and step 7; a human decides"
  fi
  y=$( { grep -vxF "$EVAL" || true; } <<< "$x")
  if [ -n "$y" ]; then log "WARN: besides $EVAL, these paths changed between the note commit and $HC: $(echo $y | cut -c1-600); list them in the WP3 result"; fi
  y=$( { grep -E 'MODEL_NOTE_' || true; } <<< "$x")
  [ -z "$y" ] || stop "a model note changed between the note commit $CNOTE and $HC ($(echo $y | cut -c1-200)): the note is committed once, on its own, before step 6"
  for x in $STEP7_CODE $STEP7_DATA; do git cat-file -e "$HC:$x" 2>/dev/null || stop "$x is not in $HC (the identity check below would pass for a path absent at both commits)"; done
  git diff --quiet $CNOTE $HC -- $STEP7_CODE $STEP7_DATA \
    || stop "files step 7 executes, imports or reads differ between the note commit $CNOTE and $HC: $(git diff --name-only $CNOTE $HC -- $STEP7_CODE $STEP7_DATA | tr '\n' ' ' | cut -c1-200)"
  if git cat-file -e "$CNOTE:$EVAL" 2>/dev/null; then stop "$EVAL exists already at the note commit $CNOTE: step 6 output from before the note"; fi
  x=$(git diff-tree --no-commit-id --name-status -r $HC)
  grep -qxF $'A\t'"$EVAL" <<< "$x" || stop "STEP6_DONE's commit $HC does not add $EVAL: <C6> must be the commit that adds scripts/39's step-6 output"
  # scripts/39 once (item 7.6): <C6> is the only commit after the note that adds or changes wp3_eval.json (an add,
  # delete and re-add would hide a second evaluation from the end-tree checks)
  x=$(git log --full-history --format=%H $CNOTE..$HC -- $EVAL)
  [ "$x" = "$HC" ] || stop "$EVAL was added or changed by more than one commit after the note commit ($(echo $x | cut -c1-130)): step 6 (scripts/39) runs once (PLAN item 7.6), and <C6> is the one commit that adds its output"
  ev=$( { git show "$HC:$EVAL" 2>/dev/null || true; } | $SPY -c '
import json, sys
try:
    e = json.load(sys.stdin); ft = (e.get("arms") or {}).get("finetuned") or {}; g = e.get("git") or {}
    v = [e.get("script"), e.get("mode"), ft.get("sha256"), "stand-in" if e.get("stand_in") else "-",
         "cache" if e.get("cache") is not None else "-", g.get("head"), len(g.get("uncommitted") or []), e.get("script_sha256")]
    print(" ".join(str(x) if x not in (None, "") and " " not in str(x) else "none" for x in v))
except Exception as x:
    print("unreadable", type(x).__name__)' || true)
  read -r e_script e_mode e_sha e_si e_cache e_head e_unc e_ssha <<< "$ev" || true
  [ "${e_script:-} ${e_mode:-}" = "scripts/39_wp3_evaluate.py full" ] || stop "$EVAL at $HC is not a scripts/39 full-mode result ($(echo $ev | cut -c1-120))"
  [[ ${e_sha:-} =~ ^[0-9a-f]{64}$ ]] || stop "$EVAL at $HC records no fine-tuned model sha256 (arms.finetuned.sha256, as scripts/39 writes it): cannot check that step 6 evaluated the note's model"
  [ "$e_sha" = "$SHA" ] || stop "$EVAL at $HC evaluated the model with sha256 $e_sha (arms.finetuned.sha256), the note names $SHA"
  [ "$e_si $e_cache" = "- -" ] || stop "$EVAL at $HC is a stand-in or --cache run of scripts/39, not step 6"
  { [[ $e_head =~ ^[0-9a-f]{40}$ ]] && git merge-base --is-ancestor $CNOTE $e_head 2>/dev/null && git merge-base --is-ancestor $e_head $HC 2>/dev/null; } \
    || stop "$EVAL at $HC was made at commit $e_head, not at or after the note commit $CNOTE and before $HC: scripts/39 runs after the note is committed (PLAN item 2 'Record and model hash', item 7)"
  # the code scripts/39 ran with: at its commit only results/ and scripts/39 itself may differ from the note commit
  # (so scripts/32 and 37, which it imports, are the note commit's; scripts/39 is checked by its sha256 below)
  y=$(git diff --no-renames --name-only $CNOTE $e_head | { grep -v '^results/' || true; } | { grep -vxF $S39 || true; })
  [ -z "$y" ] || stop "$EVAL at $HC was made at commit $e_head, where files outside results/ differ from the note commit ($(echo $y | cut -c1-200)): step 6 runs at <CNOTE> or at a later commit that changes only results/ and scripts/39"
  [ "$e_unc" = 0 ] || stop "$EVAL at $HC was made with uncommitted scripts 39/32/37"
  [ "$e_ssha" = "$(git show "$HC:$S39" | sha256sum | cut -c1-64)" ] || stop "$EVAL at $HC was written by a scripts/39 (sha256 $e_ssha) other than the one committed at $HC"
  log "pre: step 6 done: $HC adds $EVAL (scripts/39 run at ${e_head:0:12}, after the note commit ${CNOTE:0:12}; it evaluated the note's model)"
  # the selected run: the note's run<n> with its own 'training finished in' line. It may be the one item-2 retry
  # (runbook 5a; by hand, logged as WP3_RUNBOOK appendix A.5 says) after either (i) the technical failure of one other
  # finished run (node_step34's 'STOP: technical failure' after it, before run<n> started, and its 5a record kept as
  # logs/techfail_<run>.txt) or (ii) a deterministic abnormal end (node_step34's 'STOP: run<k>: second abnormal end'
  # before run<n> started, run<k> not discarded afterwards, i.e. not the PREV_CAUSE path, and run<k>.end kept)
  x=$({ grep -E '\] 4: training finished in [^;]+; wp3\.model sha256 [0-9a-f]{64};' $W/step34.log || true; })
  RUN=$(printf '%s\n' "$x" | sed -nE 's/.*training finished in ([^;]+);.*/\1/p' | sort -u | awk -v r="$NRUN" '{k=split($0, p, "/"); if (p[k] == r) print}')
  { [ -n "$RUN" ] && [ "$(printf '%s\n' "$RUN" | wc -l)" -eq 1 ]; } || stop "step34.log must report exactly one 'training finished in' line for the note's $NRUN (found: $(echo $RUN))"
  y=$(printf '%s\n' "$x" | grep -F "training finished in $RUN;" | sed -E 's/.*wp3\.model sha256 ([0-9a-f]{64});.*/\1/' | sort -u)
  [ "$y" = "$SHA" ] || stop "step34.log reports wp3.model sha256 $(echo $y) for $RUN, the note names $SHA"
  others=$(printf '%s\n' "$x" | sed -nE 's/.*training finished in ([^;]+);.*/\1/p' | sort -u | { grep -vxF "$RUN" || true; })
  dae=$(awk -v r="$RUN" 'index($0, "4c: training started") && $NF == r {s=1}
      !s && /\] STOP: run[0-9]+: second abnormal end/ {k=$0; sub(/.*\] STOP: /, "", k); sub(/:.*/, "", k); d[k]=1}
      !s && /\] 4c: run[0-9]+ discarded unread / {k=$0; sub(/.*\] 4c: /, "", k); sub(/ .*/, "", k); delete d[k]}
      END {for (k in d) print k}' $W/step34.log | sort)
  if [ -n "$others" ] && [ -n "$dae" ]; then stop "step34.log shows both a finished run besides $RUN ($(echo $others)) and a deterministic abnormal end ($(echo $dae)) before it: item 2 allows one retry only"; fi
  if [ -n "$others" ]; then
    [ "$(printf '%s\n' "$others" | wc -l)" -eq 1 ] || stop "step34.log reports the finished training runs $(echo $others) besides $RUN: at most one (the item-2 retry's failed run) is allowed"
    o=$others; y=$W/logs/techfail_$(basename $o).txt
    awk -v o="$o" -v r="$RUN" 'index($0, "4: training finished in " o ";") {f=1} f && /\] STOP: technical failure/ {t=1}
        index($0, "4c: training started") && $NF == r && t {ok=1} END{exit !ok}' $W/step34.log \
      || stop "step34.log reports the finished run $o besides $RUN, but no 'STOP: technical failure' after it and before $RUN started: only the item-2 retry may follow a finished run"
    { [ -s $y ] && [ "$(tf_verdict $y $o)" = fail ]; } \
      || stop "$y must keep the 5a record of the failed run $o (rb_techfail.py's 'with $o/wp3.model' line, then its 'non-finite' lines): runbook 5a, the one retry"
    rt="the technical failure of $o"; rk=techfail; rf=$o
    log "pre: $RUN is the item-2 retry after the technical failure of $o ($(grep -m1 '^non-finite' $y | cut -c1-120))"
  fi
  if [ -n "$dae" ]; then
    [ "$(printf '%s\n' "$dae" | wc -l)" -eq 1 ] || stop "step34.log has a 'second abnormal end' STOP for $(echo $dae) before $RUN: item 2 allows one retry only"
    y=$W/$dae.end
    { [ -s $y ] && grep -q '^\[abnormal end\]' $y; } \
      || stop "$y (node_step34's verdict on the second abnormal end of $dae) is missing or not an '[abnormal end]': it names the deterministic cause of the item-2 retry (WP3_RUNBOOK appendix A.5)"
    rt="the deterministic abnormal end of $dae"; rk=dae; rf=$dae
  fi
  if [ -n "$rt" ]; then   # the retry's own command and log (item 2: --lr 0.0025, nothing else changed)
    tc=$W/train_command_retry.txt
    { [ "$(grep -c -- '--lr 0\.005 ' $W/train_command.txt)" = 1 ] && [ -s $tc ] && [ "$(cat $tc)" = "$(sed 's/--lr 0\.005 /--lr 0.0025 /' $W/train_command.txt)" ]; } \
      || stop "$RUN is the item-2 retry after $rt, but $tc is missing or is not train_command.txt with '--lr 0.005' replaced by '--lr 0.0025' and nothing else changed"
    { grep -q 'Learning rate: 0\.0025, weight decay: 5e-07' $RUN/logs/wp3_run-123.log && ! grep -q 'Learning rate: 0\.005,' $RUN/logs/wp3_run-123.log; } 2>/dev/null \
      || stop "$RUN is the item-2 retry after $rt, but its training log does not show 'Learning rate: 0.0025, weight decay: 5e-07' (and no other learning rate)"
    # the earlier end of a deterministic pair is the one node_step34's STOP line quotes ('earlier: <restarts line>'),
    # not a later abnormal end of the retry itself; and the retry's own discarded runs: item-2 Interruptions apply
    # (A.5): the same cause twice in succession is a technical failure of the retry (no second retry), so every
    # [abnormal end] of the retry after its first needs the operator's statement that the causes differ
    x=$($SPY -c '
import os, re, sys
s34, run, kind, failed, rs, rcd = sys.argv[1:7]
L = open(s34).read().splitlines()
def out(*v):
    print("\t".join(" ".join(str(x).split()) for x in v)); sys.exit(0)
st = [i for i, x in enumerate(L) if "4c: training started" in x and x.split()[-1] == run]
if not st:
    out("stop", "no \"4c: training started\" line for " + run)
end = st[0]
if kind == "dae":
    pat = re.compile(r"\] STOP: " + re.escape(failed) + r": second abnormal end")
    idx = [i for i in range(end) if pat.search(L[i])]
else:
    fin = [i for i in range(end) if ("4: training finished in " + failed + ";") in L[i]]
    idx = [i for i in range(fin[0], end) if "] STOP: technical failure" in L[i]] if fin else []
if not idx:
    out("stop", "no node_step34 STOP line for " + failed + " before " + run + " started")
i0 = idx[-1]
e1 = "-"
if kind == "dae":
    R = [x for x in open(rs).read().splitlines() if x.strip()] if os.path.exists(rs) else []
    q = [x for x in R if "[abnormal end]" in x and ("; earlier: " + x + "). The same cause twice") in L[i0]]
    if not q:
        out("stop", "node_step34\x27s \"STOP: " + failed + ": second abnormal end\" line quotes no [abnormal end] line of "
            "restarts.txt as its \"earlier:\" cause (the first of the two deterministic ends)")
    e1 = q[-1]
disc = []
for x in L[i0 + 1:end]:
    m = re.search(r"\] 4c: (run\d+) discarded unread (\[[^\]]*\])", x)
    if m:
        disc.append((m.group(1), m.group(2)))
bad = [d for d in disc if d[1] not in ("[node loss]", "[abnormal end]", "[start check FAIL]")]
if bad:
    out("stop", "the retry run %s was discarded as %s: a retry run is discarded only as [node loss], [abnormal end] or "
        "[start check FAIL] (WP3_RUNBOOK appendix A.5)" % bad[0])
ae = [d[0] for d in disc if d[1] == "[abnormal end]"]
pairs = list(zip(ae, ae[1:]))
said = {}
if os.path.exists(rcd):
    for x in open(rcd).read().splitlines():
        if x.strip():
            m = re.fullmatch(r"(run\d+) (run\d+): (\S.*)", x.strip())
            if not m:
                out("stop", "retry_causes_differ.txt: \"%s\" is not \"run<a> run<b>: <why the causes differ>\"" % x.strip()[:80])
            said[(m.group(1), m.group(2))] = m.group(3)
miss = [p for p in pairs if p not in said]
if miss:
    out("stop", "the one retry ended abnormally twice in succession (%s, then %s): the same cause twice is a technical "
        "failure of the retry, and there is no second retry (criterion 6 not met, no fine-tuned model); if the two "
        "causes differ, the operator states why in retry_causes_differ.txt as \"%s %s: <why>\" (WP3_RUNBOOK appendix A.5)" % (miss[0] + miss[0]))
extra = [p for p in said if p not in pairs]
if extra:
    out("stop", "retry_causes_differ.txt names %s %s, which are not two successive [abnormal end] discards of the retry" % extra[0])
out("ok", e1, "%d discarded run(s) of the retry%s%s" % (len(disc), (": " + ", ".join("%s %s" % d for d in disc)) if disc else "",
    ("; causes stated to differ: " + "; ".join("%s/%s: %s" % (a, b, said[(a, b)]) for a, b in pairs)) if pairs else ""))
' "$W/step34.log" "$RUN" "$rk" "$rf" "$W/restarts.txt" "$W/retry_causes_differ.txt" 2>&1 || true)
    IFS=$'\t' read -r y e1 z <<< "$x" || true
    [ "$y" = ok ] || stop "$RUN is the item-2 retry after $rt: ${e1:-$(echo $x | cut -c1-200)}"
    if [ $rk = dae ]; then log "pre: $RUN is the item-2 retry after the deterministic abnormal end of $dae ($(cut -c1-110 $W/$dae.end); earlier: $(echo "$e1" | cut -c1-110)); $z"
    else log "pre: the retry $RUN: $z"; fi
  fi
  # <T> (item 2: nothing else changed): the selected run trained with timing.txt's fastest thread count
  x=$(awk -v r="$RUN" 'index($0, "4c: training started") && $NF == r {print; exit}' $W/step34.log)
  y=$( { sort -k2,2n -k1,1n $W/timing.txt 2>/dev/null || true; } | awk 'NR==1{print $1}')
  re=', threads ([0-9]+), run '
  { [ "$(cut -d' ' -f1 $W/timing.txt 2>/dev/null | tr '\n' ' ')" = "8 16 32 " ] && [[ $x =~ $re ]] && [ "${BASH_REMATCH[1]}" = "$y" ]; } \
    || stop "$RUN did not train with <T> threads: its '4c: training started' line ($(echo $x | cut -c23-140)) against timing.txt's fastest thread count ${y:-none} (item 2: nothing else changed; for the retry, WP3_RUNBOOK appendix A.5)"
  # the commit node_step34 trained at: the last 'start; repo' line before the training of the selected run
  x=$(awk -v run="$RUN" '/\] start; repo /{h=$4} index($0, "4c: training started") && $NF == run {t=h} END{print t}' $W/step34.log)
  [ -n "$x" ] || stop "no 'start; repo' line before the training of $RUN in step34.log"
  x=$(git rev-parse --verify --quiet "$x^{commit}") || stop "the training commit of step34.log is not in the checkout"
  git diff --quiet $x $CNOTE -- $FROZEN || stop "scripts 39/40/41 or a helper changed after training (node_step34 trained at $x): item 4 requires the scripts committed before training"
  [ "$(sha256sum $RUN/wp3.model | cut -c1-64)" = "$SHA" ] || stop "sha256 of $RUN/wp3.model is not the note's $SHA"
  [ "$(tf_verdict $W/logs/techfail.txt $RUN)" = pass ] \
    || stop "$W/logs/techfail.txt does not show a passed technical-failure check (5a) of $RUN/wp3.model"
  x=$($PY -c 'import mace, torch, e3nn, ase; print(mace.__version__)' 2>/dev/null) || stop "the mace environment does not import"
  [ "$x" = 0.3.16 ] || stop "mace $x, not 0.3.16"
  [ "$(sha256sum $FM 2>/dev/null | cut -c1-64)" = $FOUNDATION ] || stop "$FM missing or not the PLAN foundation file (zeroshot loads it as mace_mp medium)"
  [ -x $SPY ] || stop "$SPY missing"
  for h in $HOSTS; do for s in $SYSTEMS; do [ -s ../bands/band_${s}_${h}.extxyz ] || stop "../bands/band_${s}_${h}.extxyz missing"; done; done
  if [ -d $QE ]; then
    for x in $(ls -A $QE); do case " $RELAX_JOBS queue.log " in *" $x "*) ;; *) stop "$QE holds '$x', which is not one of the 12 WP3b labels: the queue would run it";; esac; done
  fi
  x=$(pgrep -f 'scripts/35_finetune_frames\.py|/data/miniforge3/envs/mace/bin/mace_run_train|40_wp3b\.py|41_wp3_md\.py' || true)
  [ -z "$x" ] || stop "processes outside this driver are alive ($(echo $x)): MACE work must not exceed 64 threads"
  if foreign_qe; then stop "a QE process is running ($QEP): step 7 starts only when no QE runs, as no MACE work may run beside QE (runbook 7d; 64-thread budget)"; fi
  if [ -e $KA ]; then log "WARN: $KA exists (kept while the node waited for step 6?). Step 7 neither needs nor creates it: remove it now, or the idle stop never comes after STEP7_DONE or a STOP"; fi
  return 0
}
foreign_qe(){ QEP=$( { pgrep -x pw.x; pgrep -x neb.x; pgrep -x pp.x; pgrep -f 'qe_queue\.sh'; } 2>/dev/null | tr '\n' ' ' || true)
  [ -n "${QEP// /}" ]; }   # QE processes not started by this driver (called only while the driver's own chain does not run)

# ---- children: each runs under a wrapper subshell that records its pid and, at its end, its exit status (synced)
spawn(){ local pf=$1 t=$2; shift 2
  ( trap - ERR EXIT TERM HUP INT; set +e
    if [ "$t" = - ]; then "$@" > "$pf.log" 2>&1 < /dev/null &
    else env OMP_NUM_THREADS=$t MKL_NUM_THREADS=$t OPENBLAS_NUM_THREADS=1 "$@" > "$pf.log" 2>&1 < /dev/null & fi
    p=$!; echo $p > "$pf.pid.tmp"; mv -f "$pf.pid.tmp" "$pf.pid"
    wait $p; rc=$?
    echo "$rc $(date -u +%FT%TZ)" > "$pf.rc.tmp"; mv -f "$pf.rc.tmp" "$pf.rc"; sync
  ) &
  WPID=$!; }
run_sync(){ local pf=$1 t=$2 w; shift 2; rm -f $pf.rc $pf.pid
  spawn $pf $t "$@"; w=$WPID; RUNNING="$RUNNING sync:$(basename $pf):0:$w"
  until [ -e $pf.rc ] || ! kill -0 $w 2>/dev/null; do
    if [ $TERMREQ = 1 ] && [ $TERMLOGGED = 0 ]; then
      log "signal received: waiting for $(basename $pf) to end, then STOP (SIGKILL the driver to leave it running unwatched)"; TERMLOGGED=1
    fi
    sleep 2; poller_watch
  done
  wait $w 2>/dev/null || true; RUNNING=${RUNNING% sync:*}
  SYNC_RC=$(cut -d' ' -f1 $pf.rc 2>/dev/null || echo none); return 0; }

# ---- helper calls: stdout is shell assignments (eval), stderr goes to a file, a failure gives a safe default
cls(){ local out
  if out=$($SPY $S/bin/cls.py "$@" 2>$S/cls.err); then printf '%s\n' "$out"
  else printf 'CL_STATE=stop CL_DETAIL=%q\n' "classifier error: $(tail -c 300 $S/cls.err 2>/dev/null | tr '\n' ' ')"; fi; return 0; }
vfy(){ local out
  if out=$($PY $S/bin/verify.py "$@" 2>$S/verify.err); then printf '%s\n' "$out"
  else printf 'V_STATE=bad V_DETAIL=%q\n' "verifier error: $(tail -c 300 $S/verify.err 2>/dev/null | tr '\n' ' ')"; fi; return 0; }

# ---- job bookkeeping
kind_of(){ case $1 in wp3md_*) echo md;; *) echo relax;; esac; }
threads_of(){ case $1 in wp3md_*) echo $T_MD;; *) echo $T_RELAX;; esac; }
build_cmd(){ local lab=$1 cause=$2 note=$3 x cell h s T
  case $lab in
    wp3md_*) x=${lab#wp3md_}; h=${x%%_*}; x=${x#*_}; s=${x%_md*}; T=${x##*_md}
      CMD=("$PY" scripts/41_wp3_md.py run --model $RUN/wp3.model --model-sha256 $SHA --host $h --system $s --T $T --work $MW --threads $T_MD)
      if [ -n "$cause" ]; then CMD+=(--rerun-cause "$cause" --rerun-note "$note"); fi;;
    *) x=${lab#wp3b}; x=${x#u}; cell=${x#_}; cell=${cell%_img0}
      CMD=("$PY" scripts/40_wp3b.py relax --region $B/wp3b_region.json --model $RUN/wp3.model --model-sha256 $SHA --work $RW --qe $QE)
      case $lab in wp3bu_*) CMD+=(--unconstrained);; esac
      if [ -n "$cause" ]; then CMD+=(--rerun-cause "$cause" --rerun-note "$note"); fi
      CMD+=(--cells $cell);;
  esac; return 0; }
listline(){ echo "$(stamp) $*" >> $LIST; }      # callers sync before writing the marker that stops a re-listing
verify_job(){ local lab=$1
  V_STATE=bad; V_DETAIL=""; V_SUMMARY=""
  case $lab in
    wp3md_*) eval "$(vfy md $lab $MW $SHA $HC)";;
    *) eval "$(vfy relax $lab $RW $QE $SHA $B/wp3b_region.json $HC)";;
  esac; return 0; }
evaluate(){   # evaluate <label> [<launch id just ended>]: the job's state from the files; sets ST_/CA_/EV_/RI_/RD_/N_<label>
  local lab=$1 live=${2:-} kind wd
  kind=$(kind_of $lab); wd=$RW; if [ $kind = md ]; then wd=$MW; fi
  CL_STATE=""; CL_N=0; CL_CAUSE=""; CL_EVID=""; CL_NEW=0; CL_FKIND=""; CL_DETAIL=""; CL_PROV=""; CL_UNUSED=""
  eval "$(cls --label $lab --kind $kind --work $wd --jobdir $S/jobs/$lab --boot $BOOT --spot $S/spot --op $S/cause.$lab --jctl "$JCTL" --live "$live")"
  if [ -n "$CL_UNUSED" ]; then log "$lab: operator cause file(s) matching no current STOP of this label, moved aside unused: $CL_UNUSED"; fi
  sv N_$lab "$CL_N"; sv RI_$lab ""; sv CA_$lab ""; sv EV_$lab ""; sv RD_$lab ""
  case $CL_STATE in
    complete) verify_job $lab
      case $V_STATE in
        ok) sv ST_$lab done
          if [[ $CL_PROV == accepted* ]] && [ ! -e $S/jobs/$lab/accepted.listed ]; then
            listline "ACCEPTED $lab attempt $CL_N: a complete output that no node_step7 launch made, verified (made at the step-7 commit $HC) and $CL_PROV"
            sync; touch $S/jobs/$lab/accepted.listed; log "$lab: complete output accepted by the operator (${CL_DETAIL:-$CL_PROV})"; fi
          if [ -n "$live" ]; then log "$lab: complete ($V_SUMMARY; $CL_PROV)"; fi;;
        republish) if [ "$(gv PUB_$lab)" = 1 ]; then sv ST_$lab stop; add_stop "$lab: the QE input is still not in $QE after a re-invocation of scripts/40"
                   else sv ST_$lab pub; log "$lab: record complete, $V_DETAIL: scripts/40 is re-invoked (identical command) to complete the copy"; fi;;
        *) sv ST_$lab stop; add_stop "$lab: its complete output fails verification ($V_DETAIL); a damaged output is never treated as complete: decide by hand";;
      esac;;
    first) sv ST_$lab run;;
    rerun|reissue) sv ST_$lab run; sv CA_$lab "$CL_CAUSE"; sv EV_$lab "$CL_EVID"; sv RI_$lab $CL_STATE; sv RD_$lab "$CL_DETAIL"
      if [ "$CL_NEW" = 1 ] && [ $CL_STATE = rerun ]; then log "$lab: attempt $CL_N classified: rerun with --rerun-cause $CL_CAUSE ($CL_EVID)"; fi
      if [ $CL_STATE = reissue ]; then log "$lab: $CL_DETAIL"; fi;;
    final) sv ST_$lab final
      if [ ! -e $S/jobs/$lab/final.listed ]; then listline "FINAL $lab: $CL_DETAIL"; sync; touch $S/jobs/$lab/final.listed; log "$lab: FINAL, no further attempt: $CL_DETAIL"; fi
      if [ "$CL_NEW" = 1 ] && [ "$CL_FKIND" = exception ]; then
        add_stop "$lab ended with a Python exception (no rerun; listed as final): a human checks that the cause is not systematic before the other runs go on"; fi;;
    stop|refused) sv ST_$lab stop; add_stop "$lab: $CL_DETAIL";;
    *) sv ST_$lab stop; add_stop "$lab: the classifier gave no state";;
  esac; return 0; }
launch(){ local lab=$1 jd=$S/jobs/$1 th mode=run expect cause note s=1 ri
  th=$(threads_of $lab); cause=$(gv CA_$lab); ri=$(gv RI_$lab); expect=$(( $(gv N_$lab) + 1 ))
  if [ "$(gv ST_$lab)" = pub ]; then mode=publish; expect=$(gv N_$lab); cause=""; sv PUB_$lab 1; fi
  note=""; if [ -n "$cause" ]; then note="node_step7 $(stamp): $(gv EV_$lab | cut -c1-400)"; fi
  build_cmd $lab "$cause" "$note"
  mkdir -p $jd; while [ -e $jd/L$s.launch ]; do s=$((s+1)); done
  { echo "mode=$mode"; echo "expect=$expect"; echo "boot=$BOOT"; echo "epoch=$(date +%s)"; echo "utc=$(stamp)"; echo "cause=$cause"
    echo "threads=$th"; echo "evid=$(gv EV_$lab | tr '\n' ' ')"; printf 'cmd='; printf '%q ' "${CMD[@]}"; echo; } > $jd/L$s.launch.tmp
  mv -f $jd/L$s.launch.tmp $jd/L$s.launch
  if [ "$ri" = reissue ]; then listline "REISSUE $lab launch L$s (attempt $expect${cause:+, --rerun-cause $cause}): $(gv RD_$lab); identical command, no attempt consumed"
  elif [ -n "$cause" ]; then listline "RERUN $lab attempt $expect of at most 3, --rerun-cause $cause: $(gv EV_$lab)"; fi
  sync                                    # the launch record (and list line) are on disk before the process exists
  spawn $jd/L$s $th "${CMD[@]}"
  RUNNING="$RUNNING $lab:L$s:$th:$WPID"; sv ST_$lab running
  log "$lab: launch L$s ($mode, attempt $expect${cause:+, --rerun-cause $cause}, $th threads, wrapper $WPID)"; return 0; }
used_threads(){ local e x; USED=0; for e in $RUNNING; do x=${e#*:}; x=${x#*:}; USED=$((USED + ${x%%:*})); done; return 0; }
relax_running(){ case " $RUNNING" in *" wp3b"*) return 0;; esac; return 1; }
reap(){ local e keep="" lab ls w
  for e in $RUNNING; do lab=${e%%:*}; ls=${e#*:}; ls=${ls%%:*}; w=${e##*:}
    if [ -e $S/jobs/$lab/$ls.rc ] || ! kill -0 $w 2>/dev/null; then
      wait $w 2>/dev/null || true; sync
      log "$lab: $ls ended (exit $(cut -d' ' -f1 $S/jobs/$lab/$ls.rc 2>/dev/null || echo 'not recorded'))"
      evaluate $lab $ls
    else keep="$keep $e"; fi
  done
  RUNNING=$keep; return 0; }
gate_check(){ local lab
  if [ $GATE = open ]; then return 0; fi
  if [ -e $RW/wp2e_minimum.json ]; then
    V_STATE=bad; eval "$(vfy wp2e $RW/wp2e_minimum.json $SHA $HC)"
    if [ "$V_STATE" = ok ]; then sync; touch $S/wp2e.ok; GATE=open; log "wp2e_minimum.json written and checked ($V_SUMMARY): parallel invocations may start"
    else add_stop "wp2e_minimum.json fails its check ($V_DETAIL): decide by hand"; fi
    return 0
  fi
  if relax_running; then return 0; fi
  for lab in $RELAX_JOBS; do case $(gv ST_$lab) in run|pub) return 0;; esac; done
  for lab in $RELAX_JOBS; do
    if [ "$(gv ST_$lab)" = done ]; then
      if [ -n "$PUBTRIED" ]; then add_stop "wp2e_minimum.json still missing after a re-invocation of scripts/40"; return 0; fi
      PUBTRIED=1; sv ST_$lab pub; log "wp2e_minimum.json missing: scripts/40 is re-invoked for the complete cell $lab (it writes the file and relaxes nothing)"; return 0
    fi
  done
  log "WARN: no relaxation record and no wp2e_minimum.json: the WP2e-minimum quantities will be reported missing"; GATE=open; return 0; }
schedule(){ local lab th
  used_threads
  for lab in $ALL; do
    case $(gv ST_$lab) in run|pub) ;; *) continue;; esac
    th=$(threads_of $lab); if [ $((USED + th)) -gt $BUDGET ]; then continue; fi
    if [ $GATE != open ]; then            # single writer of wp2e_minimum.json: one scripts/40 process, nothing else
      case $lab in wp3md_*) continue;; esac
      if relax_running; then continue; fi
    fi
    hold_check; if [ $HOLD = 1 ]; then break; fi      # a notice recorded during this pass: launch nothing more
    launch $lab; USED=$((USED + th))
  done; return 0; }
counts(){ local lab c="" st k; for st in done final run pub running stop; do k=0
    for lab in $ALL; do if [ "$(gv ST_$lab)" = $st ]; then k=$((k+1)); fi; done
    if [ $k != 0 ]; then c="$c $st=$k"; fi; done; echo "${c# }"; }
hold_check(){ local f=$S/spot/notice.$BOOT nt   # a spot notice in this boot: nothing new starts for NOTICE_HOLD s (HOLD=1)
  HOLD=0; [ -e $f ] || return 0
  nt=$(cut -d' ' -f2 $f 2>/dev/null || true); [[ $nt =~ ^[0-9]+$ ]] || nt=$(date -r $f +%s)
  if [ $(( $(date +%s) - nt )) -lt $NOTICE_HOLD ]; then HOLD=1
    if [ $HOLDLOG = 0 ]; then HOLDLOG=1; log "spot termination notice recorded ($(cut -c1-120 $f)): nothing new is started for ${NOTICE_HOLD} s (a launch now would be cut and spend an attempt); running children continue"; fi
  elif [ $HOLDLOG != 2 ]; then HOLDLOG=2; log "WARN: the spot notice of this boot ($(cut -c1-80 $f)) is over ${NOTICE_HOLD} s old and the node still runs: launches resume"; fi
  return 0; }
wall_check(){ local e lab ls jd ep lim n p   # a job past 3 x its expected length: WARN and STOP for a human (never killed)
  for e in $RUNNING; do lab=${e%%:*}; ls=${e#*:}; ls=${ls%%:*}; jd=$S/jobs/$lab
    case $lab in sync) continue;; esac
    [ ! -e $jd/$ls.wallwarn ] || continue
    ep=$(sed -n 's/^epoch=//p' $jd/$ls.launch 2>/dev/null || true); n=$(sed -n 's/^expect=//p' $jd/$ls.launch 2>/dev/null || true)
    lim=$WALL_RELAX; case $lab in wp3md_*) lim=$WALL_MD;; esac
    if [[ $ep =~ ^[0-9]+$ ]] && [ $(( $(date +%s) - ep )) -gt $lim ]; then
      p=$(cat $jd/$ls.pid 2>/dev/null || echo '?'); touch $jd/$ls.wallwarn
      log "WARN: $lab ($ls, pid $p) has run for more than $lim s, 3 times its expected length"
      add_stop "$lab ($ls, pid $p) has run for more than $lim s (3 x its expected length): hung? The driver never kills it. If it is hung, kill pid $p, write 'wall-time <note>' to $S/cause.$lab.att$n and relaunch; if it is not, wait for it to end, then relaunch"
    fi
  done; return 0; }
verify_wp2e(){   # wp2e_minimum.json again (made at the step-7 commit <C6>, by the selected model); never re-created behind the gate
  if [ -e $RW/wp2e_minimum.json ]; then
    V_STATE=bad; eval "$(vfy wp2e $RW/wp2e_minimum.json $SHA $HC)"
    [ "$V_STATE" = ok ] || add_stop "wp2e_minimum.json fails its check ($V_DETAIL): decide by hand"
  elif [ -e $S/wp2e.ok ]; then add_stop "$RW/wp2e_minimum.json is missing although it was written and checked earlier ($S/wp2e.ok): moved or removed by hand? decide by hand (it is never re-created behind the open gate)"; fi
  return 0; }
wait_clear(){ local l=0   # 7c: before the chain, no spot-notice hold and no QE process outside this driver
  while :; do
    hold_check; if [ $HOLD = 0 ] && ! foreign_qe; then return 0; fi
    if [ $HOLD = 0 ] && [ $l = 0 ]; then l=1; log "7c: a QE process outside this driver is running ($QEP): the chain waits until none is left"; fi
    sleep 10; poller_watch; chk_term
  done; }

# ================================================================== run
BOOT=$(tr -d ' \n' < $BOOTF)
log "start; boot ${BOOT:0:8}; repo $(git rev-parse --short HEAD)"
pre
log "preconditions PASS: note commit $CNOTE ($NOTE), step-6 commit $HC (checkout; adds wp3_eval.json), model $RUN/wp3.model sha256 $SHA, scripts_commit $CS"
start_poller(){ $SPY $S/bin/poller.py step7-spot-poller "$SPOT_URL" $S/spot "$BOOT" $$ >> $S/spot/poller.log 2>&1 < /dev/null &
  POLLER=$!; return 0; }
poller_watch(){ if [ -n "$POLLER" ] && ! kill -0 $POLLER 2>/dev/null; then
    wait $POLLER 2>/dev/null || true; log "WARN: the spot poller (pid $POLLER) had ended: restarted"; start_poller; fi; return 0; }
start_poller
chk_term

# first start (7a never launched): nothing of step 7 may exist yet. An output made before step 7, by hand and perhaps
# before the note commit, is never adopted (item 2 'Reporting': no test-host prediction before the committed note)
if [ ! -e $S/7a.started ] && [ -z "$(ls -A $S/sync 2>/dev/null)" ]; then
  x=$( { ls -A $RW; ls -A $MW; ls -A $B | grep -vx relax; ls -A $S/jobs; if [ -d $QE ]; then ls -A $QE | grep -vx queue.log; fi; } 2>/dev/null | head -8 | tr '\n' ' ' || true)
  [ -z "$x" ] || stop "first start of step 7, yet step-7 outputs exist ($x): made before step 7 (by hand, perhaps before the note commit). Item 2: no test-host prediction may predate the committed note, and the driver never adopts an output it did not start. Move $B, $MW and the label directories in $QE aside, record why for the WP3 result, then relaunch"
  echo $HC > $S/commit.tmp; mv -f $S/commit.tmp $S/commit   # every later start runs at this commit
  sync; touch $S/7a.started; sync
fi
x=$(cat $S/commit 2>/dev/null || true)
[ "$x" = "$HC" ] || stop "step 7 started at the commit '${x:-none recorded}' ($S/commit), this start is at $HC: the outputs of one step 7 come from one commit; restore the checkout and STEP6_DONE, or decide by hand"

# 7a: region, then zeroshot (zero-shot MACE-MP-0 on the m30 test cells: only now, after the note commit)
if [ ! -e $S/7a_region.done ]; then
  run_sync $S/sync/region - "$PY" scripts/40_wp3b.py region --out $B/wp3b_region.json
  [ "$SYNC_RC" = 0 ] || stop "7a region exited $SYNC_RC (must exit 0: 6.0 A, 81/83/81): $(tail -2 $S/sync/region.log | tr '\n' ' ' | cut -c1-300)"
  sync; touch $S/7a_region.done; log "7a: $(tail -1 $S/sync/region.log | cut -c1-240)"
fi
chk_term
if [ ! -e $S/7a_zeroshot.done ]; then
  if foreign_qe; then stop "a QE process is running ($QEP): 7a zeroshot (MACE-MP-0, 4 threads) never runs beside QE (runbook 7d)"; fi
  run_sync $S/sync/zeroshot 4 "$PY" scripts/40_wp3b.py zeroshot --region $B/wp3b_region.json --out $B/wp3b_zeroshot.json
  [ "$SYNC_RC" = 0 ] || stop "7a zeroshot exited $SYNC_RC (must exit 0: every comparator value reproduced): $(tail -3 $S/sync/zeroshot.log | tr '\n' ' ' | cut -c1-300)"
  sync; touch $S/7a_zeroshot.done; log "7a: $(tail -1 $S/sync/zeroshot.log | cut -c1-240)"
fi
chk_term

# 7b + 7d: the MACE pool (relaxations first, unconstrained first; MD fills the rest of the 64 threads)
if [ ! -e $S/pool.done ]; then
  if [ -e $S/wp2e.ok ]; then GATE=open; verify_wp2e; fi
  for lab in $ALL; do evaluate $lab; done
  log "pool: $(counts)"
  [ -z "$STOPR" ] || finish_stop
  last_sync=$(date +%s); last_status=$last_sync
  while :; do
    reap; poller_watch
    if [ $TERMREQ = 1 ] && [ $TERMLOGGED = 0 ]; then TERMLOGGED=1; add_stop "terminated by a signal (TERM/HUP/INT); the running children were waited for (SIGKILL the driver to leave them unwatched)"; fi
    if [ -z "$STOPR" ] && foreign_qe; then add_stop "a QE process outside this driver is running ($QEP): MACE work never runs beside the 64-rank QE chain (runbook 7d)"; fi
    [ -n "$STOPR" ] || gate_check
    hold_check
    if [ -z "$STOPR" ] && [ $HOLD = 0 ]; then schedule; fi
    if [ -z "$RUNNING" ]; then
      if [ -n "$STOPR" ]; then break; fi
      x=""; for lab in $ALL; do case $(gv ST_$lab) in run|pub) x="$x $lab";; esac; done
      if [ -z "$x" ]; then break; fi
      if [ $HOLD = 0 ]; then add_stop "scheduler made no progress with runnable jobs:$x"; break; fi
    fi
    now=$(date +%s)
    [ $((now - last_sync)) -lt 60 ] || { sync; last_sync=$now; wall_check; }
    [ $((now - last_status)) -lt 600 ] || { log "pool status: $(counts); running:$(for e in $RUNNING; do printf ' %s' ${e%%:*}; done)"; last_status=$now; }
    sleep $TICK
  done
  [ -z "$STOPR" ] || finish_stop
  for lab in $ALL; do evaluate $lab; done            # every complete output verified again before the marker
  verify_wp2e
  [ -z "$STOPR" ] || finish_stop
  for lab in $ALL; do case $(gv ST_$lab) in done|final) ;; *) stop "pool ended with $lab in state $(gv ST_$lab)";; esac; done
  sync; touch $S/pool.done; log "pool done: $(counts)"
fi
chk_term

# 7c: the QE chain, after every relaxation has its record (or no attempt left); never beside MACE work
if [ ! -e $S/7c.done ]; then
  DONE_RELAX=""; FINAL_RELAX=""
  for lab in $RELAX_JOBS; do if [ -e $RW/$lab.json ]; then DONE_RELAX="$DONE_RELAX $lab"; else FINAL_RELAX="$FINAL_RELAX $lab"; fi; done
  NIN=$(echo $DONE_RELAX | wc -w | tr -d ' ')
  if [ -n "$FINAL_RELAX" ]; then log "7c: no record (final) for:$FINAL_RELAX; the chain runs the other $NIN"; fi
  mkdir -p $QE
  for x in $(ls -A $QE); do case " $DONE_RELAX queue.log " in *" $x "*) ;; *) stop "$QE holds '$x', which has no relaxation record";; esac; done
  for lab in $DONE_RELAX; do
    V_STATE=bad; eval "$(vfy qein $lab $RW $QE $SHA $B/wp3b_region.json $HC)"
    [ "$V_STATE" = ok ] || stop "$lab: $V_DETAIL (damaged after a hard stop? restore it from $RW/$lab.qe/ by hand)"
  done
  x=$(pgrep -f 'scripts/35_finetune_frames\.py|/data/miniforge3/envs/mace/bin/mace_run_train|40_wp3b\.py|41_wp3_md\.py' || true)
  [ -z "$x" ] || stop "MACE processes alive ($(echo $x)): the QE chain never runs beside MACE work"
  s=1; while [ -e $S/chain/C$s.launch ]; do s=$((s+1)); done
  if [ $s -gt 1 ] && [ ! -e $S/chain/C$((s-1)).rc ] && [ ! -e $S/chain/C$((s-1)).listed ]; then
    c=C$((s-1)); pb=$(sed -n 's/^boot=//p' $S/chain/$c.launch); ce=$(sed -n 's/^epoch=//p' $S/chain/$c.launch); of=$S/cause.chain.$c
    if [ "$pb" != "$BOOT" ]; then
      CL_STATE=""; CL_CAUSE=""; CL_EVID=""; CL_DETAIL=""; CL_TRANSIENT=""
      eval "$(cls --label chain --kind relax --work $S --jobdir $S/chain --boot $BOOT --spot $S/spot --op $S/none --jctl "$JCTL" --bootcause $pb --since "$ce")"
      if [ "$CL_STATE" = rerun ]; then why="cause $CL_CAUSE: $CL_EVID"
      elif [ "$CL_STATE" = stop ] && [ "${CL_TRANSIENT:-}" = 0 ]; then   # evidence read, but it does not show a hard stop
        why="cause undetermined: $CL_EVID"
        log "WARN: 7c: the chain launch $c was cut by the end of boot ${pb:0:8}; the evidence does not show a hard stop ($CL_EVID): listed as cause undetermined; a cut-short job uses its one item-1d resubmission; state it in the WP3 result"
      elif [ -s $of ]; then why="cause given by the operator ($(basename $of)): $(head -c 300 $of | tr '\n' ' '); driver: $CL_EVID$CL_DETAIL"
      else   # no evidence (the journal could not be read): never listed from missing evidence; classified at the next start
        stop "7c: the earlier chain launch $c (boot ${pb:0:8}) was cut short and its cause cannot be determined: $CL_EVID$CL_DETAIL. Nothing is listed or started: fix the journal access and relaunch, or write the cause to $of and relaunch"
      fi
    else why="cause undetermined: the chain process ended without an exit status and without a reboot"; fi
    cutj=""                                                        # evidence of a cut job: an output without JOB DONE
    for f in $(ls $QE/*/*.out 2>/dev/null || true); do           # written after that launch (the queue renames it next)
      if ! grep -qs "JOB DONE" $f && [ ! -e ${f%.out}.gaveup ] && [ "$(date -r $f +%s)" -ge "${ce:-0}" ]; then cutj="$cutj $(basename $f .out)"; fi
    done
    if [ -n "$cutj" ]; then
      listline "QE-INTERRUPTED chain launch $c (boot ${pb:0:8}), job(s)$cutj: $why; the queue resubmits the cut-short job once (item 1d)"
      sync; log "7c: the earlier chain launch $c was cut short during$cutj ($why)"
    else log "7c: the earlier chain launch $c was cut short, but no wp3b job was (no output without JOB DONE written after that launch; $why): nothing to list"; fi
    sync; touch $S/chain/$c.listed
    if [ -e $of ]; then mv -f $of $of.used; log "7c: operator file $(basename $of) used"; fi
  fi
  wait_clear
  { echo "boot=$BOOT"; echo "epoch=$(date +%s)"; echo "utc=$(stamp)"; echo "inputs=$DONE_RELAX"; } > $S/chain/C$s.launch; sync
  log "7c: chain wp3b launch C$s for $NIN inputs (first waiting out any queue started outside chain.sh)"
  flock $QLOCK true
  run_sync $S/chain/C$s - "$CHAIN" wp3b
  if [ "$SYNC_RC" != 0 ]; then log "7c: chain.sh exited $SYNC_RC"; fi
  chk_term
  for lab in $DONE_RELAX; do
    grep -qs "JOB DONE" $QE/$lab/$lab.out || [ -e $QE/$lab/$lab.gaveup ] \
      || stop "7c: $lab has neither a JOB DONE output nor a .gaveup after the chain (queue.log: $(tail -1 $QE/queue.log 2>/dev/null))"
  done
  nd=0; ng=0
  for lab in $DONE_RELAX; do
    if grep -qs "JOB DONE" $QE/$lab/$lab.out; then nd=$((nd+1)); fi
    for f in $(ls $QE/$lab/$lab.out.try* 2>/dev/null || true); do
      if [ ! -e $S/chain/listed.$(basename $f) ]; then
        listline "QE-RESUBMISSION $lab: $(basename $f) (mtime $(date -u -r $f +%FT%TZ)): an output without JOB DONE, renamed by qe_queue.sh, which resubmits the identical input once (item 1d)"
        sync; touch $S/chain/listed.$(basename $f)
      fi
    done
    if [ -e $QE/$lab/$lab.gaveup ]; then ng=$((ng+1))
      if [ ! -e $S/chain/listed.$lab.gaveup ]; then listline "QE-GAVEUP $lab: no complete output after the resubmission (item 1d)"; sync; touch $S/chain/listed.$lab.gaveup; fi
    fi
  done
  sync; touch $S/7c.done
  log "7c: chain done; $nd of $NIN with JOB DONE, $ng given up"
fi

# done: every complete output verified once more
for lab in $ALL; do evaluate $lab; done
verify_wp2e
[ -z "$STOPR" ] || finish_stop
x=""; for lab in $ALL; do case $(gv ST_$lab) in final) x="$x $lab";; done) ;; *) stop "$lab is in state $(gv ST_$lab) at the end";; esac; done
nl=0; if [ -e $LIST ]; then nl=$(wc -l < $LIST | tr -d ' '); fi
sync; touch $W/STEP7_DONE; sync
log "done: $(counts)${x:+ (final without a complete output:$x)}; $nl line(s) in $LIST. Next: runbook 7e on the Mac (--model-sha256 $SHA; scripts/41 analyse --commit $CS, the note's scripts_commit = <CN>; outputs made at the step-6 commit $HC), then step 8"
kill_poller
exit 0; }

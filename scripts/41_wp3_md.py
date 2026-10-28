#!/usr/bin/env python
"""WP3 adoption check (e): MD stability of the selected model (PLAN amendment 2026-10-28m item 4 (e);
interrupted runs as in item 4 (d), "Interrupted jobs"). Committed before training (item 7, step 1), run
whenever a fine-tuned model exists (step 7). Writes no QE input; labels wp3md_<host>_<system>_md<T> match no
scripts/33 pattern. The label scheme, and so the 12 seeds crc32(label), is fixed by this committed script.

Runs (12): image 0 of band_{undoped,GA,Sr}_{m30,m32}.extxyz (the WP3b cells; full cell, no constraint)
at 300 K and 450 K, one run per invocation. 5 ps fixed-cell Langevin MD, 1 fs steps, friction 0.01 fs^-1,
Maxwell-Boltzmann start (+ Stationary) and rng = default_rng(crc32(label)), set up as in scripts/35
(seed_of and sane imported; ASE Langevin defaults otherwise). Model: MACECalculator(<wp3.model>, cpu,
float64, head Default), its sha256 checked against --model-sha256 (the committed model note, item 2)
before anything runs.

Pass of a run: every frame at 100 fs intervals (t = 0, 100, ..., 5000 fs: 51 frames) passes both
  * scripts/35 sane(): composition, organic (C/N/H) bonding pattern, no contact below 0.65 A, model
    max force below 15 eV/A;
  * the inorganic checks (minimum image), which sane() does not test:
      1. no I-I distance below 3.0 A (I2 2.67 A, I3- about 2.9 A);
      2. Sr cells: the Sr atom is nearer its own start position than the start position of any Pb;
      3. GA cells: the GA carbon is nearer its own start position than the start position of any
         other C or any Cs.
The first failing frame fixes the verdict; the run still continues to 5 ps, so that the reported values
cover the whole run. Between the 100 fs frames only the finiteness of the model forces is tested: non-finite
forces make the positions of every later frame non-finite (Langevin), so the next 100 fs frame could not
pass sane() (no contact > 0.65 A); the integration stops there and the step is recorded as the failing frame. An
exception after the first failure ends the integration but not the (failed) record. A vacancy hop is not
a failure. Reported, not gating: per run the minimum I-I, Pb-I and Sr-I distances and the largest
displacement of Sr and of the GA carbon from the start, over the frames at 100 fs intervals (unrounded).

Interrupted runs: frames go to <label>.extxyz.part, renamed on completion; <label>.json is written last
and marks a complete run. Every attempt (with the git state of scripts/41 and 35) is kept in
<label>.attempts.json. A rerun (identical script, scripts/35, model, seed, start and threads; at most two)
needs --rerun-cause, one of the four causes of item 4 (d): spot reclaim, node loss, OOM or wall time. An
attempt that ended in a Python exception admits only 'oom', and only with a memory error in its traceback.
The partial outputs of the earlier attempt are moved unread to <work>/discarded/, which nothing reads or
analyses. A run with no complete output after that cannot be evaluated.

    python scripts/41_wp3_md.py run --model <run>/wp3.model --model-sha256 <hex> --host m30 \
        --system GA --T 300 --work <dir> [--bands ../bands] [--threads 8] [--rerun-cause spot-reclaim]
    python scripts/41_wp3_md.py analyse --work <dir> [<dir> ...] --model-sha256 <hex> [--commit <rev>] --out <file>.json

analyse: "pass" is false if any run fails, else null if any run cannot be evaluated (the item-4
Outcomes treat both as a fail), else true; scripts/39 --md-json reads "pass" and "model_sha256". A record
counts only if it matches its label, seed, start structure, model, protocol, trajectory, the rerun rules,
and the scripts/41 and 35 committed at --commit (the commit of the model note, item 2; default HEAD). If
scripts/41 or 35 is not committed there, "pass" is null. The shortest I-I distance in the 106 band and
binding training DFT frames (90 band + 16 m05 WP2c QE inputs) is 4.0346 A (m06_GA_img4); amendment m
quotes 4.04 A. The WP3 frames of item 1a are not included in that value.
"""
import argparse, datetime, fcntl, hashlib, json, os, shutil, signal, socket, subprocess, sys, time, traceback
import importlib.util
import numpy as np
from ase import units
from ase.io import read, write
from ase.geometry import get_distances
from ase.calculators.singlepoint import SinglePointCalculator

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
_s = importlib.util.spec_from_file_location("a35", os.path.join(HERE, "35_finetune_frames.py"))
a35 = importlib.util.module_from_spec(_s); _s.loader.exec_module(a35)

HOSTS, SYSTEMS, TEMPS = ("m30", "m32"), ("undoped", "GA", "Sr"), (300, 450)
STEPS, EVERY, DT_FS, FRICTION = 5000, 100, 1.0, 0.01   # 5 ps; frames every 100 fs; fs; 1/fs (scripts/35)
FMAX_BOUND, CONTACT, II_MIN = 15.0, 0.65, 3.0           # scripts/35 bounds; I-I bonding cut (A)
MAX_RERUNS = 2
CAUSES = ("spot-reclaim", "node-loss", "oom", "wall-time")   # item 4 (d), as scripts/40
MEMORY_ERRORS = ("MemoryError", "out of memory", "can't allocate memory", "Cannot allocate memory")
FOUNDATION_SHA256 = "01bfe22100139f424713cf921144e5509cbe353d67aa9fa1be9c6e1e0ed35845"   # zero-shot medium
PROTOCOL_CONST = {"dt_fs": DT_FS, "friction_per_fs": FRICTION, "fmax_bound_eVA": FMAX_BOUND, "contact_A": CONTACT,
                  "II_min_A": II_MIN}
REL41, REL35 = "scripts/41_wp3_md.py", "scripts/35_finetune_frames.py"
TRAINING_II = {"value_A": 4.0346, "where": "m06_GA_img4, I52-I136", "plan_quotes_A": 4.04,
               "frames": "106 band and binding training DFT frames (90 WP2b band frames of m05 m06 m08 m12 m15 m20, "
                         "images 0 2 3 4 6; 16 m05 WP2c QE inputs); the WP3 frames of item 1a are not included"}


def label_of(host, sysn, T):
    return f"wp3md_{host}_{sysn}_md{T}"     # matches no scripts/33 pattern; seed = crc32(label)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def git(*args):
    """stdout (bytes) of git in the repository root, or None (no git, no repository, or an error)."""
    try:
        p = subprocess.run(["git", "-C", ROOT, *args], capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return p.stdout if p.returncode == 0 else None


def git_state():
    """HEAD and the uncommitted state of scripts/41 and 35 (as scripts/39 git_state); None without git."""
    head, st = git("rev-parse", "HEAD"), git("status", "--porcelain", "--", REL41, REL35)
    return None if head is None or st is None else {"head": head.decode().strip(), "uncommitted": st.decode().splitlines()}


def committed_sha256(rev):
    """sha256 of scripts/41 and 35 as committed at rev, or None if either is not in that commit."""
    c = git("rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}")
    blobs = [git("show", f"{rev}:./{p}") for p in (REL41, REL35)]
    if c is None or None in blobs:
        return None
    return {"commit": c.decode().strip(), "script_sha256": hashlib.sha256(blobs[0]).hexdigest(),
            "scripts35_sha256": hashlib.sha256(blobs[1]).hexdigest()}


def cause_fits(prev, cause):
    """Can attempt `prev` have been stopped by `cause` (item 4 (d))? 'started' (process gone without a record:
    SIGKILL, power or node loss) and 'terminated' (SIGTERM/SIGINT) fit all four causes; 'exception' (a Python
    traceback) fits only 'oom', with a memory error in the traceback; 'complete' fits none."""
    st = prev.get("status")
    if st in ("started", "terminated"):
        return cause in CAUSES
    return st == "exception" and cause == "oom" and any(m in (prev.get("detail") or "") for m in MEMORY_ERRORS)


def dopant_index(at, sysn):
    """Sr atom of a Sr cell; GA carbon of a GA cell (3 N < 1.6 A, no H < 1.25 A, the sane() rule)."""
    s = np.array(at.get_chemical_symbols())
    if sysn == "Sr":
        sr = np.flatnonzero(s == "Sr")
        if len(sr) != 1:
            raise ValueError(f"{len(sr)} Sr atoms")
        return int(sr[0])
    if sysn == "GA":
        d = at.get_all_distances(mic=True)
        N, H = np.flatnonzero(s == "N"), np.flatnonzero(s == "H")
        ga = [int(c) for c in np.flatnonzero(s == "C") if (d[c][N] < 1.6).sum() == 3 and (d[c][H] < 1.25).sum() == 0]
        if len(ga) != 1:
            raise ValueError(f"{len(ga)} GA carbons")
        return ga[0]
    return None


def inorganic(at, start, sysn, k):
    """Checks 1-3 of item 4 (e), minimum image, against the start frame; k = dopant_index(start).
    Comparisons are written so that a NaN distance fails."""
    s = np.array(start.get_chemical_symbols()); cell, pbc = start.cell, start.pbc
    if at.get_chemical_symbols() != list(s):
        raise ValueError("atom order or composition changed")
    I, Pb = np.flatnonzero(s == "I"), np.flatnonzero(s == "Pb")
    dist = lambda P, Q: get_distances(P, Q, cell=cell, pbc=pbc)[1]
    dII = dist(at.positions[I], at.positions[I]); np.fill_diagonal(dII, 99.0)
    r, why = {"min_II_A": float(dII.min()), "min_PbI_A": float(dist(at.positions[Pb], at.positions[I]).min())}, []
    if not r["min_II_A"] >= II_MIN:
        i, j = np.unravel_index(np.argmin(dII), dII.shape)
        why.append(f"I-I {r['min_II_A']:.3f} A < {II_MIN} A (I{I[i]}-I{I[j]})")
    if sysn == "Sr":
        r["min_SrI_A"] = float(dist(at.positions[[k]], at.positions[I]).min())
    if k is not None:              # site checks 2 and 3: own start site against the alternative start sites
        alt = Pb if sysn == "Sr" else np.r_[np.setdiff1d(np.flatnonzero(s == "C"), [k]), np.flatnonzero(s == "Cs")]
        own = float(dist(at.positions[[k]], start.positions[[k]])[0, 0])
        dalt = dist(at.positions[[k]], start.positions[alt])[0]
        j = int(alt[np.argmin(dalt)])
        r.update({"disp_dopant_A": own, "d_nearest_other_site_A": float(dalt.min()), "nearest_other_site": f"{s[j]}{j}"})
        if not own < dalt.min():
            why.append(f"{'Sr' if sysn == 'Sr' else 'GA carbon'} {k} is nearer the start of {s[j]}{j} "
                       f"({dalt.min():.3f} A) than its own start ({own:.3f} A)")
    return not why, r, why


def check_frame(at, start, sysn, calc, k):
    """scripts/35 sane() and the inorganic checks; returns (ok, values, reasons). The verdict is sane()'s; its
    reasons are taken from the unrounded contact and force (sane() returns them rounded; forces are cached)."""
    ok_s, chk = a35.sane(at, start, sysn, calc, FMAX_BOUND)
    ok_i, inorg, why = inorganic(at, start, sysn, k)
    if not ok_s:
        d = at.get_all_distances(mic=True); np.fill_diagonal(d, 99.0)
        dmin, fm = float(d.min()), float(np.linalg.norm(calc.get_forces(at), axis=1).max())
        r = [] if chk["topology_ok"] else ["composition or organic bonding pattern changed"]
        r += [] if dmin > CONTACT else [f"contact {dmin:.4f} A <= {CONTACT} A"]
        r += [] if fm < FMAX_BOUND else [f"model max force {fm:.4f} eV/A >= {FMAX_BOUND} eV/A"]
        why = [f"sane(): {x}" for x in (r or ["failed"])] + why
    return ok_s and ok_i, {**chk, **inorg}, why


def step_check(at, start, sysn, calc, k, n, every):
    """MD step n (forces and energy already cached by the integrator). On the frame grid (n % every == 0)
    the full check; off it only the finiteness of the model forces. None = nothing to record."""
    finite = bool(np.isfinite(at.get_forces()).all())
    on_grid = n % every == 0
    if finite and not on_grid:
        return None
    ok, vals, why = check_frame(at, start, sysn, calc, k)
    if not finite:
        ok, why = False, [f"non-finite model forces at step {n}" + ("" if on_grid else " (between frames)") +
                          ": every later frame has non-finite positions and cannot pass sane(); integration stopped"] + why
    return {"t_fs": n * DT_FS, "on_grid": on_grid, "ok": ok, "forces_finite": finite, **vals,
            "E_pot_eV": float(at.get_potential_energy()), "T_inst_K": round(float(at.get_temperature()), 1), "reasons": why}


def md(a, label, src, msha, part):
    import torch, ase, mace
    torch.set_num_threads(a.threads)
    from mace.calculators import MACECalculator
    from ase.md.langevin import Langevin
    from ase.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary
    calc = MACECalculator(model_paths=[a.model], device="cpu", default_dtype="float64", head="Default")
    if calc.head != "Default":       # 0.3.16 only warns and falls back to the last head
        raise RuntimeError(f"head {calc.head} (available {calc.available_heads})")
    if not all(p.dtype == torch.float64 for m in calc.models for p in m.parameters()):
        raise RuntimeError("model is not float64")
    base = read(src, index=0)
    base = base.copy(); base.calc = None; base.set_tags([0] * len(base))      # as scripts/35
    if not a35.sane(base, base, a.system, calc, 1e9)[1]["topology_ok"]:
        raise RuntimeError(f"{src}@0 fails the topology check")
    k = dopant_index(base, a.system)
    rng = np.random.default_rng(a35.seed_of(label))                           # scripts/35 MD set-up
    at = base.copy(); at.calc = calc
    MaxwellBoltzmannDistribution(at, temperature_K=a.T, rng=rng); Stationary(at)
    dyn = Langevin(at, DT_FS * units.fs, temperature_K=a.T, friction=FRICTION / units.fs, rng=rng)
    frames, fail, stop, done, t0 = [], None, None, 0, time.time()
    try:
        for _ in dyn.irun(a.steps):       # yields after each step, with the forces at the new positions cached
            n = int(dyn.nsteps)
            fr = step_check(at, base, a.system, calc, k, n, a.report_every)
            done = n
            if fr is None:
                continue
            frames.append(fr)
            if not fr["ok"] and fail is None:
                fail = fr                 # the verdict is fixed here; the run continues
            print(json.dumps({x: round(v, 4) if isinstance(v, float) else v for x, v in fr.items() if x != "nearest_other_site"}),
                  flush=True)
            snap = at.copy()
            snap.calc = SinglePointCalculator(snap, energy=fr["E_pot_eV"], forces=at.get_forces())
            snap.info.update({"label": label, "t_fs": fr["t_fs"], "frame_ok": fr["ok"]})
            write(part, snap, format="extxyz", append=True)
            if not fr["forces_finite"]:
                stop = f"non-finite model forces at step {n}"
                break
    except Exception:
        if fail is None:
            raise
        stop = "exception after the first failure (verdict already fixed): " + traceback.format_exc()[-2000:]
    grid = [f for f in frames if f["on_grid"]]
    col = lambda key, f: float(f(fr_[key] for fr_ in grid)) if grid and key in grid[0] else None
    rep = {"min_II_A": col("min_II_A", min), "min_PbI_A": col("min_PbI_A", min), "min_SrI_A": col("min_SrI_A", min),
           "max_disp_Sr_A": col("disp_dopant_A", max) if a.system == "Sr" else None,
           "max_disp_GA_C_A": col("disp_dopant_A", max) if a.system == "GA" else None,
           "sampled_every_fs": a.report_every * DT_FS, "window_fs": [0.0, (done // a.report_every) * a.report_every * DT_FS]}
    return {"label": label, "host": a.host, "system": a.system, "T_K": a.T, "seed": a35.seed_of(label),
            "source": f"{os.path.basename(src)}@0", "source_sha256": sha256(src), "natoms": len(base),
            "dopant_index": k, "model": os.path.abspath(a.model), "model_sha256": msha,
            "model_is_foundation_medium": msha == FOUNDATION_SHA256,
            "protocol": {"steps": a.steps, "report_every": a.report_every, **PROTOCOL_CONST,
                         "ensemble": "ASE Langevin, fixed cell, no constraint, ASE defaults otherwise (as scripts/35)",
                         "start": "MaxwellBoltzmannDistribution + Stationary, rng = default_rng(crc32(label))",
                         "calculator": "MACECalculator cpu float64 head Default",
                         "after_first_failure": "continues to the last step; stops only at non-finite model forces"},
            "protocol_ok": a.steps == STEPS and a.report_every == EVERY,
            "versions": {"mace": mace.__version__, "ase": ase.__version__, "torch": torch.__version__,
                         "numpy": np.__version__, "python": sys.version.split()[0]},
            "threads": a.threads, "script_sha256": sha256(os.path.abspath(__file__)), "scripts35_sha256": sha256(a35.__file__),
            "git": git_state(), "completed_steps": done, "n_frames_checked": len(frames),
            "n_failing_frames": sum(not f["ok"] for f in frames), "ok": fail is None,
            "first_failure_fs": fail["t_fs"] if fail else None, "reasons": fail["reasons"] if fail else [],
            "stopped": stop, "reported_not_gating": rep, "wall_s": round(time.time() - t0, 1), "frames": frames}


def run(a):
    a.host = f"m{int(a.host.lstrip('m')):02d}"
    if a.host not in HOSTS:
        raise SystemExit(f"--host must be one of {HOSTS}")
    if a.steps < 1 or a.report_every < 1:
        raise SystemExit("--steps and --report-every must be positive")
    label = label_of(a.host, a.system, a.T)
    P = lambda ext: os.path.join(a.work, label + ext)
    partial = lambda: [P(e) for e in (".extxyz.part", ".extxyz", ".json.tmp") if os.path.exists(P(e))]
    msha = sha256(a.model)
    if msha != a.model_sha256.lower():
        raise SystemExit(f"{a.model}: sha256 {msha} != --model-sha256 {a.model_sha256}")
    os.makedirs(a.work, exist_ok=True)
    lock = open(P(".lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)     # released by the kernel when this process ends
    except OSError:
        raise SystemExit(f"{label}: another process is running it ({P('.lock')})")
    if os.path.exists(P(".json")):
        raise SystemExit(f"{label}: complete output {P('.json')} exists; a run is never repeated")
    src = os.path.join(a.bands, f"band_{a.system}_{a.host}.extxyz")
    ident = {"script_sha256": sha256(os.path.abspath(__file__)), "scripts35_sha256": sha256(a35.__file__),
             "model_sha256": msha, "seed": a35.seed_of(label), "source_sha256": sha256(src),
             "steps": a.steps, "report_every": a.report_every, "threads": a.threads}
    log = json.load(open(P(".attempts.json"))) if os.path.exists(P(".attempts.json")) else {"label": label, "attempts": []}
    prev, discarded = log["attempts"], None
    if any(p.get("status") == "complete" for p in prev):
        raise SystemExit(f"{label}: an earlier attempt completed but {P('.json')} is missing; not re-run")
    if prev:
        if len(prev) > MAX_RERUNS:
            raise SystemExit(f"{label}: {len(prev)} attempts without complete output (1 run + {MAX_RERUNS} reruns); "
                             "(e) cannot be evaluated for this run")
        if a.rerun_cause is None:
            raise SystemExit(f"{label}: {len(prev)} earlier attempt(s) left no complete output (last status "
                             f"'{prev[-1].get('status')}'); a rerun needs --rerun-cause ({', '.join(CAUSES)})")
        if not cause_fits(prev[-1], a.rerun_cause):
            raise SystemExit(f"{label}: attempt {len(prev)} ended with status '{prev[-1].get('status')}', which cause "
                             f"'{a.rerun_cause}' cannot explain (item 4 (d) reruns only spot reclaim, node loss, OOM or wall time; "
                             "an exception admits only oom, with a memory error); no rerun: (e) cannot be evaluated for this run")
        diff = [x for x in ident if prev[0]["identity"].get(x) != ident[x]]
        if diff:
            raise SystemExit(f"{label}: a rerun uses the identical script, model, seed, start and settings; differs: {diff}")
        if partial():                                         # partial outputs, moved aside unread (never read)
            discarded = os.path.join(a.work, "discarded", f"{label}.attempt{len(prev)}")
            os.makedirs(discarded, exist_ok=True)
            for p in partial():
                shutil.move(p, os.path.join(discarded, os.path.basename(p)))
    elif a.rerun_cause:
        raise SystemExit(f"{label}: --rerun-cause given but there is no earlier attempt")
    elif partial():
        raise SystemExit(f"{label}: outputs exist without an attempt record: {partial()}; remove them by hand")
    if (a.steps, a.report_every) != (STEPS, EVERY):
        print(f"WARNING: --steps {a.steps} / --report-every {a.report_every} != {STEPS} / {EVERY}: smoke test, "
              "not the PLAN protocol; analyse will not evaluate it", flush=True)
    gs = git_state()
    if gs is None or gs["uncommitted"]:
        print(f"WARNING: scripts/41 or 35 is not committed here (git: {gs}); analyse counts a run only if both "
              "equal the committed scripts (item 2, item 7)", flush=True)
    att = {"n": len(prev) + 1, "started_utc": now(), "rerun_cause": a.rerun_cause, "rerun_note": a.rerun_note,
           "discarded_to": discarded, "hostname": socket.gethostname(), "pid": os.getpid(), "argv": sys.argv,
           "threads": a.threads, "git": gs, "identity": ident, "status": "started"}
    prev.append(att); a35.dump_atomic(log, P(".attempts.json"))
    signal.signal(signal.SIGTERM, lambda n, f: sys.exit(f"terminated by signal {n}"))
    try:
        rec = md(a, label, src, msha, P(".extxyz.part"))
        rec["attempt"] = att["n"]
        rec["reruns"] = [{x: p.get(x) for x in ("n", "started_utc", "rerun_cause", "rerun_note")} for p in prev[1:]]
        rec["earlier_attempts"] = [{x: p.get(x) for x in ("n", "started_utc", "status", "ended_utc", "detail")} for p in prev[:-1]]
        os.replace(P(".extxyz.part"), P(".extxyz"))
        rec["trajectory"] = os.path.basename(P(".extxyz")); rec["trajectory_sha256"] = sha256(P(".extxyz"))
        rec["finished_utc"] = now()
        a35.dump_atomic(rec, P(".json"))                      # completion marker, written last
    except BaseException as e:
        att.update(status="terminated" if isinstance(e, (SystemExit, KeyboardInterrupt)) else "exception",
                   ended_utc=now(), detail=traceback.format_exc()[-4000:])
        a35.dump_atomic(log, P(".attempts.json"))
        raise
    att.update(status="complete", ended_utc=now()); a35.dump_atomic(log, P(".attempts.json"))
    print(f"{label}: {'pass' if rec['ok'] else 'FAIL'}; {rec['n_frames_checked']} frames, {rec['completed_steps']} steps"
          + ("" if rec["protocol_ok"] else "; NON-PROTOCOL settings (test run)") + f"; {rec['reasons']}"
          + (f"; stopped: {rec['stopped'][:200]}" if rec["stopped"] else ""))


def script_reference(commit):
    """The scripts/41 and 35 a record must have been made with: those committed at --commit (default HEAD).
    Without such a commit the working files are used and 'committed' is False (pass is then null)."""
    work = {"script_sha256": sha256(os.path.abspath(__file__)), "scripts35_sha256": sha256(a35.__file__)}
    ref = committed_sha256(commit or "HEAD")
    if ref is None and commit:
        raise SystemExit(f"--commit {commit}: not a commit of this repository, or scripts/41 or 35 is not in it")
    out = {"requested": commit or "HEAD", "committed": ref is not None, **(ref or {"commit": None, **work}),
           "analysing_files": work, "git": git_state()}
    out["analysing_files_equal_reference"] = all(work[x] == out[x] for x in work)
    return out


def check_frames(rec, grid):
    """The frame list agrees with the verdict, the first failure, the completed steps and the 100 fs grid."""
    fr, cs = rec.get("frames") or [], rec.get("completed_steps")
    on = [f.get("t_fs") for f in fr if f.get("on_grid")]
    off = [f for f in fr if not f.get("on_grid")]
    first = next((f.get("t_fs") for f in fr if not f.get("ok")), None)
    return (bool(fr) and len(fr) == rec.get("n_frames_checked") and isinstance(cs, int) and 0 <= cs <= STEPS
            and on == grid[:cs // EVERY + 1] and rec.get("ok") is (first is None) and rec.get("first_failure_fs") == first
            and (rec.get("stopped") is not None or cs == STEPS)
            and (not off or (len(off) == 1 and fr[-1] is off[0] and off[0].get("forces_finite") is False
                             and off[0].get("t_fs") == cs * DT_FS))
            and (rec.get("ok") is not True or (cs == STEPS and rec.get("stopped") is None and not off)))


def analyse(a):
    def find(name):
        hits = [os.path.join(d, name) for d in a.work if os.path.exists(os.path.join(d, name))]
        if len(hits) > 1:
            raise SystemExit(f"{name} found in several --work dirs: {hits}")
        return hits[0] if hits else None
    want = a.model_sha256.lower()
    ref = script_reference(a.commit)
    grid = [i * EVERY * DT_FS for i in range(STEPS // EVERY + 1)]
    src_sha = {}
    for host in HOSTS:
        for sysn in SYSTEMS:
            p = os.path.join(a.bands, f"band_{sysn}_{host}.extxyz")
            if not os.path.isfile(p):
                raise SystemExit(f"{p}: start structure not found (--bands); the records cannot be verified")
            src_sha[host, sysn] = sha256(p)
    rows, reasons, scripts = [], [], set()
    for host in HOSTS:
        for sysn in SYSTEMS:
            for T in TEMPS:
                label = label_of(host, sysn, T)
                rp, ap_ = find(label + ".json"), find(label + ".attempts.json")
                att = json.load(open(ap_))["attempts"] if ap_ else []
                row = {"label": label, "host": host, "system": sysn, "T_K": T, "status": "cannot be evaluated", "pass": None,
                       "attempts": len(att), "reruns": [{x: p.get(x) for x in ("n", "started_utc", "rerun_cause", "rerun_note")} for p in att[1:]],
                       "earlier_attempt_status": [p.get("status") for p in att[:-1]], "reasons": []}
                bad = [f"rerun {p.get('n')} cause '{p.get('rerun_cause')}' is not one of {CAUSES} (item 4 (d))"
                       for p in att[1:] if p.get("rerun_cause") not in CAUSES]
                bad += [f"rerun {p.get('n')} cause '{p.get('rerun_cause')}' cannot have stopped attempt {q.get('n')} "
                        f"(status '{q.get('status')}')" for q, p in zip(att, att[1:])
                        if p.get("rerun_cause") in CAUSES and not cause_fits(q, p.get("rerun_cause"))]
                bad += [f"{len(att)} attempts (more than {MAX_RERUNS} reruns)"] if len(att) > 1 + MAX_RERUNS else []
                if rp is None:
                    bad.append("no complete output" + (f" after {len(att)} attempt(s), last status '{att[-1].get('status')}'"
                                                       if att else " (never started)"))
                else:
                    rec = json.load(open(rp)); tp = os.path.join(os.path.dirname(rp), rec.get("trajectory", ""))
                    prot = rec.get("protocol", {})
                    chk = [((rec.get("label"), rec.get("host"), rec.get("system"), rec.get("T_K")) == (label, host, sysn, T),
                            "record does not match its label"),
                           (rec.get("seed") == a35.seed_of(label), f"seed {rec.get('seed')} != crc32(label)"),
                           (rec.get("source_sha256") == src_sha[host, sysn], "start structure differs from --bands image 0"),
                           (rec.get("model_sha256") == want, f"model sha256 {rec.get('model_sha256')} != --model-sha256"),
                           ((rec.get("script_sha256"), rec.get("scripts35_sha256")) == (ref["script_sha256"], ref["scripts35_sha256"]),
                            f"made with a scripts/41 or 35 other than the reference ({ref['requested']}, commit {ref['commit']})"),
                           (rec.get("protocol_ok") is True and (prot.get("steps"), prot.get("report_every")) == (STEPS, EVERY),
                            f"non-protocol settings {prot.get('steps')} steps / every {prot.get('report_every')} (test run)"),
                           (all(prot.get(x) == v for x, v in PROTOCOL_CONST.items()), "protocol constants differ from this script"),
                           (os.path.isfile(tp) and sha256(tp) == rec.get("trajectory_sha256"), "trajectory missing or changed"),
                           (ap_ is not None and rec.get("attempt") == len(att), "attempt log missing or inconsistent with the record"),
                           (check_frames(rec, grid), "frame list inconsistent with the verdict, first failure, steps or 100 fs grid")]
                    bad += [why for good, why in chk if not good]
                    scripts.add(rec.get("script_sha256"))
                    row.update({"n_frames_checked": rec.get("n_frames_checked"), "n_failing_frames": rec.get("n_failing_frames"),
                                "completed_steps": rec.get("completed_steps"), "first_failure_fs": rec.get("first_failure_fs"),
                                "stopped": rec.get("stopped"), **rec.get("reported_not_gating", {}),
                                "record": os.path.abspath(rp), "trajectory_sha256": rec.get("trajectory_sha256")})
                    if not bad:
                        row["status"], row["pass"] = ("pass", True) if rec["ok"] else ("fail", False)
                        row["reasons"] += [f"t = {rec['first_failure_fs']:g} fs: {x}" for x in rec["reasons"]]
                row["reasons"] += bad
                rows.append(row)
                if row["status"] != "pass":
                    reasons.append(f"{label}: {row['status']}: " + "; ".join(row["reasons"]))
    n = {s: sum(r["status"] == s for r in rows) for s in ("pass", "fail", "cannot be evaluated")}
    if not ref["analysing_files_equal_reference"]:
        reasons.append(f"analysed with a scripts/41 or 35 that differs from the reference {ref['requested']} (git: {ref['git']})")
    if want == FOUNDATION_SHA256:      # (e) is for the selected fine-tuned model; zero-shot is a stand-in only
        ok, verdict = None, "not evaluated: --model-sha256 is the zero-shot MACE-MP-0 medium file (stand-in)"
        reasons.insert(0, verdict)
    elif not ref["committed"]:
        ok, verdict = None, f"cannot be evaluated: scripts/41 or 35 is not committed at {ref['requested']} (item 2, item 7)"
        reasons.insert(0, verdict)
    else:
        ok = False if n["fail"] else (None if n["cannot be evaluated"] else True)
        verdict = {False: "fail", None: "cannot be evaluated", True: "pass"}[ok]
    ev = [r for r in rows if r["status"] in ("pass", "fail")]          # reported values of evaluated runs only
    ext = lambda key, f: (lambda v: f(v) if v else None)([r[key] for r in ev if r.get(key) is not None])
    out = {"check": "WP3 adoption (e): MD stability", "plan": "PLAN amendment 2026-10-28m item 4 (e)",
           "model_sha256": want, "pass": ok, "verdict": verdict, "n_runs_expected": len(rows), "n_pass": n["pass"],
           "n_fail": n["fail"], "n_cannot_be_evaluated": n["cannot be evaluated"], "reasons": reasons,
           "rule": "pass only if all 12 runs pass; false if any run fails; null if none fails and any cannot be evaluated",
           "params": {"steps": STEPS, "report_every_fs": EVERY, "frames_per_run": STEPS // EVERY + 1, **PROTOCOL_CONST,
                      "max_reruns": MAX_RERUNS, "rerun_causes": list(CAUSES)},
           "reported_not_gating": {"over": f"the {len(ev)} evaluated runs (pass or fail), frames every {EVERY} fs",
                                   "min_II_A": ext("min_II_A", min), "min_PbI_A": ext("min_PbI_A", min),
                                   "min_SrI_A": ext("min_SrI_A", min), "max_disp_Sr_A": ext("max_disp_Sr_A", max),
                                   "max_disp_GA_C_A": ext("max_disp_GA_C_A", max),
                                   "shortest_II_in_106_band_binding_training_DFT_frames": TRAINING_II},
           "script_reference": ref, "script_sha256_of_records": sorted(s for s in scripts if s), "runs": rows}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    a35.dump_atomic(out, a.out)
    for r in rows:
        print(f"{r['label']:24s} {r['status']:20s} attempts {r['attempts']}  minII {r.get('min_II_A')}  {'; '.join(r['reasons'])}")
    print(f"(e) {verdict}: {n}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="one MD run")
    r.add_argument("--model", required=True, help="model file (the selected wp3.model)")
    r.add_argument("--model-sha256", required=True)
    r.add_argument("--host", required=True, help="m30 or m32")
    r.add_argument("--system", choices=SYSTEMS, required=True)
    r.add_argument("--T", type=int, choices=TEMPS, required=True)
    r.add_argument("--bands", default="../bands", help="dir with band_<system>_<host>.extxyz")
    r.add_argument("--work", required=True)
    r.add_argument("--threads", type=int, default=8, help="part of the rerun identity")
    r.add_argument("--rerun-cause", choices=CAUSES, default=None,
                   help="cause of the stop of an interrupted attempt; reruns it from the start (at most twice)")
    r.add_argument("--rerun-note", default=None, help="free text kept with the rerun (e.g. when the node was lost)")
    r.add_argument("--steps", type=int, default=STEPS, help="SMOKE TESTS ONLY: other values mark the run as a test")
    r.add_argument("--report-every", type=int, default=EVERY, help="SMOKE TESTS ONLY, as --steps")
    s = sub.add_parser("analyse", help="collect the 12 runs")
    s.add_argument("--work", nargs="+", required=True)
    s.add_argument("--model-sha256", required=True)
    s.add_argument("--commit", default=None,
                   help="commit of scripts/41 recorded in the model note (item 2); default HEAD")
    s.add_argument("--bands", default="../bands", help="dir with the start structures (their sha256 is checked)")
    s.add_argument("--out", required=True, help="result JSON (read by scripts/39 --md-json)")
    a = ap.parse_args()
    run(a) if a.cmd == "run" else analyse(a)


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""S2 campaigns C1-C4: the job graph of each campaign, the resumable node runner, the node-hour ledger and the
laptop archive (results/objective2/s2/S2_PLAN.md sections 7-13, 16 and 17 items 2 and 5; the Stage-0 interface
specification, sections 9, 11 and 12). Cells and their records are made by scripts/46, QE inputs and parsers by
scripts/47, and every gate, cut and budget decision by scripts/49. This script decides nothing: it schedules jobs,
keeps the evidence of every attempt and applies the decisions the gate outputs record.

  graph     The jobs of one campaign with their dependencies, labels, work ids and counts, built from the site
            sets of scripts/46 (geometry only) and the S2 state (Stage-0 lists, gate decisions, cuts). The counts
            are asserted against the plan (assert_counts). C1 (sections 7-11, 16): 2 host relaxations, 30 V+_R,
            80 noise-pilot and 20 start-set dopant relaxations, the pose-pilot extra starts (<= 32 relaxations);
            5 G1, 2 spin, 106 noise-pilot, 2 step-0, <= 40 pose-pilot and 10 q = 0 single points; 3 pw.x smoke
            tests (one with two parts, a fourth at the chosen A2 layout if it is not 48 ranks) and 4 throughput
            runs. C2: the 10 A2 relaxations of section 11 in their fixed order. C3 (section 12): per production
            host 1 + 75 frozen relaxations and 76 single points (multi-pose tokens: every sampled start, one
            single point per kept minimum, <= 100 more). C4: the 26 A2 relaxations of section 11. Each is reduced
            by G1 (section 7; I-31) and by the cuts of section 16. Every A2 relaxation has a geometry-only job for
            the section 11 final-geometry checks (scripts/46 validate-a2; I-F1); K3 waits for them.
  run       The node runner, started by ehpc/node/s2_campaign.sh. One runner at a time (fcntl.flock on
            /data/work/s2/s2.lock, inherited by every child). Resumable from files: the graph and every job's
            state are recomputed from records, outputs and markers at each start, and every launch is recorded
            (fsynced) before its process starts. Phases run in order (checks -> smoke tests -> throughput row ->
            MACE -> single points -> gates in C1; checks -> A2 in C2; checks -> projection -> MACE -> single
            points in C3; checks -> projection -> A2 in C4); MACE never runs beside pw.x (N-7).
            Keep-alive (section 16): /data/KEEP_ALIVE is present for the whole campaign and removed at its end or
            at a STOP (N-12). Spot notice (section 13): a child poller records the metadata endpoint's notice
            (spot/notice.<boot>, fsynced); the runner then creates <prefix>.EXIT in the outdir of every running A2
            part and starts nothing new for 1800 s (N-11). MACE (sections 5, 13): at most 10 concurrent
            relaxations at 6 threads (scripts/46 relax --job); an attempt without a record that started in an
            earlier boot is an interruption, rerun from the start with the identical job at most twice, its
            partial outputs moved to discarded/ unread; an attempt that ended with an exception is a STOP (N-9).
            Single points (sections 12, 13): staged by scripts/47, published at most two ahead (I-D2) into
            /data/jobs/s2c<k>/<label>/ and run by the committed queue rules (chain.sh -> qe_queue.sh: one
            resubmission, then .gaveup); completeness from scripts/47 sp_status (a JOB DONE output with an
            unconverged SCF is missing and never resubmitted). A2 relaxations (sections 11, 13): the committed
            ehpc/node/s2_run_qe.sh under the global chain lock (N-6; two copies on the two halves of the cores, N-F30),
            in the fixed order with one or two copies; the exit file stops a part once
            configuration k = 200 has completed; after a soft exit with usable restart data the next part is the
            part-1 input with only restart_mode='restart' and the reduced nstep of the smoke-test mapping, else the
            relaxation is rerun from k = 0 with the identical input at most twice; every interruption is logged.
            Gates (sections 7-11, 16): scripts/49 at their evaluation points; a gate that stops A2 kills a running
            partner (its output discarded unread). Hard cap (section 16): no pw.x or MACE job starts if H_spent plus
            its expected duration (scripts/49) would exceed 520 node-h; a refused job and every pw.x and MACE job
            after it is "not started (hard cap)"; gates, the section 11 checks and the other jobs without
            node-hours are never refused and run whenever their inputs are complete (N-F14).
  ledger    Node-hours (section 16): the wall time of every boot that carries a runner heartbeat (or is listed by
            the operator in ledger/manual.json), from its btime (/proc/stat) to max(last heartbeat + 60 s, the
            last entry of its journal); the current boot ends now. Incomplete evidence stops new job starts (I-23).
  archive   Laptop (interface spec 5.5): gzips the raw QE files of one pulled campaign, copies records, tars the
            structures, scrubs the log, refuses a duplicated label or a record whose sha256 does not match its file,
            and checks every written JSON and log for public-repository hygiene.

Blinding (section 17): the runner reads QE outputs only in the status, counts and end-rule modes of scripts/47, and
the final positions of A2 relaxations in final_geom mode for the section 11 checks (no energy); every such read is
listed in <campaign>/runner_reads.jsonl, and it never forms an E_b, Y_h or delta; MACE records are read with
load_record(blind=True). Gates read through the allow-lists of scripts/49.

    python scripts/50_s2_campaign.py --self-test [--work DIR]
    python scripts/50_s2_campaign.py graph --campaign c1 [--state F]
    python scripts/50_s2_campaign.py run --campaign c1 [--root /data]       (node; through ehpc/node/s2_campaign.sh)
    python scripts/50_s2_campaign.py status [--root /data]
    python scripts/50_s2_campaign.py ledger [--root /data]
    python scripts/50_s2_campaign.py archive --stage DIR --campaign c1 --out results/objective2/s2/c1
"""
import argparse, copy, fcntl, glob, gzip, hashlib, importlib.util, io, itertools, json, os, re, shutil, signal
import subprocess, sys, tarfile, tempfile, threading, time, traceback, types
from collections import Counter, OrderedDict

import numpy as np
from ase.geometry import find_mic
from ase.io import read, write

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


b42 = _load("b42", "42_s2_builders.py")            # build_paired, list_sites, sampled_names, POOL, VAC_REF (no model)
pp, s29 = b42.pp, b42.s29                          # scripts/22, scripts/29 (one module object each)
a38 = _load("a38", "38_wp2e_displacement.py")      # molecule (by bonding), used by the mock region only

# Interface spec 1.2: a dependency that does not exist yet is replaced by a small in-file stub of the interface;
# the self-test prints MOCKED <module> so a run with every file present can be told apart.
MOCKED = []


def _load_or_mock(name, fn, mock):
    if os.path.exists(os.path.join(HERE, fn)):
        return _load(name, fn)
    MOCKED.append(fn)
    return mock()


# ---------------------------------------------------------------- stubs of scripts/46, 47 and 49 (only if absent)
def _hyg_patterns():
    # the forbidden fragments are assembled, so this file does not match its own scan
    return [("local path", re.compile("/" + "Users/|/" + "private/|/" + "home/")),
            ("temporary path", re.compile(r"(?<![\w.])/" + r"tmp/")),
            ("work-area word", re.compile("scr" + "atch|v" + "env", re.I)),
            ("IPv4 address", re.compile(r"\b\d{1,3}(\.\d{1,3}){3}\b")),
            ("e-mail address", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")),
            ("instance or disk id", re.compile(r"\b(?:i|d)-[0-9a-z]{10,}\b")),
            ("currency", re.compile("[" + "".join(map(chr, (0xA5, 0x20AC, 0xA3, 0x5143))) + "]|\\b(?:US" + "D|CN" + "Y|RM"
                                    + "B)\\b|\\$\\s?\\d"))]


def _mock46():
    """Stub of scripts/46 (interface spec section 6): constants, labels, Layout, records, hygiene, and the
    geometry calls scripts/50 and 51 make. Geometry is delegated to scripts/42 exactly as the spec says 46 does."""
    m = types.SimpleNamespace()
    m.S2Error = type("S2Error", (RuntimeError,), {})
    m.VI = 127
    m.TOKENS = ("Sr", "Ca", "Cl", "Cs", "GA")
    m.SUBLATTICE = {"Sr": "B", "Ca": "B", "Cl": "X", "Cs": "A", "GA": "A"}
    m.CONTROL, m.DECISIVE, m.MULTI_START, m.PILOTS = "Sr", ("Ca", "Cl", "Cs", "GA"), ("Cs", "Cl"), ("m30", "m05")
    m.FIRST_SHELL = {"B": (124, 136), "A": (28, 92, 128), "X": (49, 53, 90, 102, 125, 126, 137, 138)}
    m.CAL_SITES = {"m30": {"B": 136, "A": 128, "X": 138}, "m05": {"B": 124, "A": 28, "X": 49}}
    m.POSE_SITES = {"Cs": (128, 188), "Cl": (138, 175)}
    m.THREADS, m.MAX_CONCURRENT_MACE = 6, 10
    m.FOUNDATION_SHA256 = "01bfe22100139f424713cf921144e5509cbe353d67aa9fa1be9c6e1e0ed35845"
    m.FOUNDATION_FILE = "20231203mace128L1_epoch199model"
    m.PBCL_RECORD = "results/objective2/s2/stage0/pbcl_source.json"
    IDX = r"(?:0|[1-9]\d*)"
    BODY = (r"(?P<host>m\d\d)_(?:(?P<hostcell>host)(?:(?P<hL>[BAX])(?P<hj>" + IDX + r"))?|V(?P<vL>[BAX])(?P<vj>" + IDX
            + r")|(?P<tok>Sr|Ca|Cl|Cs|GA)(?P<j>" + IDX + r")o(?P<k>" + IDX + r")_(?P<leg>novac|vac))")
    m.LABEL_RE = re.compile(r"(?P<prefix>s2spin|s2g1|s2r|s2)_" + BODY + r"(?P<q0>_q0)?(?:_e(?P<ecut>50|60))?")
    m.WORK_RE = re.compile(r"s2_(?P<host>m\d\d|ref233)_(?:host|V[BAX]" + IDX + r"|(?:Sr|Ca|Cl|Cs|GA)" + IDX + r"p"
                           + IDX + r"_(?:novac|vac))")
    m.REF_RE = re.compile(r"(?P<prefix>s2tp|s2smoke)_ref232_(?P<name>[a-z0-9]+)")

    def check_label(label, sites=None):
        if m.REF_RE.fullmatch(label):
            return
        g = m.LABEL_RE.fullmatch(label)
        if not g:
            raise m.S2Error(f"label {label!r} does not match the S2 grammar")
        d = g.groupdict()
        cellv = d["vL"] is not None or d["leg"] == "vac"
        if d["q0"] and not cellv:
            raise m.S2Error(f"{label}: _q0 only on a vacancy cell")
        if d["prefix"] == "s2r" and (d["q0"] or d["ecut"] or (d["hostcell"] and not d["hL"]) or (d["k"] not in (None, "0"))):
            raise m.S2Error(f"{label}: s2r_ needs a site on host cells, the default pose, no _q0 or _e")
        if d["prefix"] in ("s2g1", "s2spin") and d["host"] != "m30":
            raise m.S2Error(f"{label}: {d['prefix']}_ on m30 only")
        if d["prefix"] == "s2" and (d["ecut"] or d["hL"]):
            raise m.S2Error(f"{label}: s2_ host cells carry no site and no _e")
        if d["tok"] and int(d["k"]) >= 1 and d["tok"] not in m.MULTI_START:
            raise m.S2Error(f"{label}: o<k> with k >= 1 only for {m.MULTI_START}")
    m.check_label = check_label

    class Layout:
        """Node: everything under <root>/work/s2/<campaign>, single points under <root>/jobs/s2<campaign>.
        Archive: results/objective2/s2/<campaign> with records/ and raw/ (interface spec 5.1, 5.2)."""
        def __init__(self, kind="node", root="/data"):
            self.kind, self.root = kind, root
            self.base = os.path.join(root, "work", "s2") if kind == "node" else root
        def campaign_dir(self, c): return os.path.join(self.base, c)
        def cell_dir(self, c, wid): return os.path.join(self.campaign_dir(c), "cells", wid)
        def record(self, c, wid):
            if self.kind == "archive":
                return os.path.join(self.campaign_dir(c), "records", f"{wid}.json")
            return os.path.join(self.cell_dir(c, wid), "record.json")
        def region(self, c, member, L, j): return os.path.join(self.campaign_dir(c), "regions", f"{member}_{L}{j}.json")
        def pair(self, c, h, T, j, n): return os.path.join(self.campaign_dir(c), "pairs", f"{h}_{T}{j}p{n}.json")
        def sp_dir(self, c, label):
            if self.kind == "archive":
                return os.path.join(self.campaign_dir(c), "raw")
            return os.path.join(self.root, "jobs", f"s2{c}", label)
        def sp_out(self, c, label): return os.path.join(self.sp_dir(c, label), f"{label}.out")
        def sp_meta(self, c, label): return os.path.join(self.sp_dir(c, label), f"{label}.meta.json")
        def a2_dir(self, c, label): return os.path.join(self.campaign_dir(c), "a2", label)
        def a2_parts(self, c, label):
            return sorted(glob.glob(os.path.join(self.a2_dir(c, label), f"{label}.p*.out")),
                          key=lambda p: int(re.search(r"\.p(\d+)\.out$", p).group(1)))
        def gate(self, c, name): return os.path.join(self.campaign_dir(c), "gates", f"{name}.json")
        def distinct(self, c, h, T, j, leg): return os.path.join(self.campaign_dir(c), "pairs", f"{h}_{T}{j}_{leg}.distinct.json")
        def state(self): return os.path.join(self.base, "state.json")
        def ledger_dir(self): return os.path.join(self.base, "ledger")
        def spot_dir(self): return os.path.join(self.base, "spot")
    m.Layout = Layout

    def load_record(path, *, blind=True):
        rec = json.load(open(path))
        if blind:
            def strip(o):
                if isinstance(o, dict):
                    return {k: strip(v) for k, v in o.items() if k != "E_mace_eV"}
                if isinstance(o, list):
                    return [strip(v) for v in o]
                return o
            rec = strip(rec)
        return rec
    m.load_record = load_record

    def hygiene_violations(text):
        return [f"{nm}: {g.group(0)!r}" for nm, rx in _hyg_patterns() for g in [rx.search(text)] if g]
    m.hygiene_violations = hygiene_violations

    def dump_public(obj, path):
        txt = json.dumps(obj, indent=1)
        bad = hygiene_violations(txt)
        if bad:
            raise m.S2Error(f"refused to write {os.path.basename(path)}: {bad}")
        write_json(obj, path)
    m.dump_public = dump_public
    m.sha256_atoms = lambda at: hashlib.sha256(at.positions.tobytes() + at.numbers.tobytes()).hexdigest()

    def foundation_path():
        base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
        return os.path.join(base, "mace", m.FOUNDATION_FILE)
    m.foundation_path = foundation_path

    def foundation_check(path=None):
        p = path or foundation_path()
        sha = sha256_file(p) if os.path.exists(p) else None
        return {"schema": "s2-mace-1", "file": m.FOUNDATION_FILE, "sha256": sha, "passed": sha == m.FOUNDATION_SHA256}
    m.foundation_check = foundation_check

    # ---- geometry (scripts/42 underneath, as interface spec section 6 describes)
    class Ctx(types.SimpleNamespace):
        pass

    def host_context(member, *, pool=b42.POOL, vac_ref=b42.VAC_REF):
        host = read(os.path.join(ROOT, pool, f"{member}.extxyz"))
        vac, vpos, vi, mig = b42.vacancy_context(host, os.path.join(ROOT, pool), os.path.join(ROOT, vac_ref))
        if vi != m.VI:
            raise m.S2Error(f"{member}: vacancy iodide {vi}, not {m.VI}")
        return Ctx(member=member, host=host, vac=vac, vpos=vpos, vi=vi, mig_vac=mig, mig_host=mig + (1 if mig >= vi else 0))
    m.host_context = host_context

    def ref_context():
        host = read(os.path.join(ROOT, "results/fa_host/fa19cs1_pb20i60_233.extxyz"))
        vac, vpos, vi, mig = b42.vacancy_context(host, os.path.join(ROOT, b42.POOL), os.path.join(ROOT, b42.VAC_REF))
        return Ctx(member="ref233", host=host, vac=vac, vpos=vpos, vi=vi, mig_vac=mig, mig_host=mig + (1 if mig >= vi else 0))
    m.ref_context = ref_context

    def rank_sites(ctx, L):
        tok = {"B": "Sr", "A": "GA", "X": "Cl"}[L]
        s = b42.list_sites(ctx.host, tok, vi=ctx.vi, vpos=ctx.vpos)
        return sorted(s, key=lambda t: (round(t[1], 6), t[0]))
    m.rank_sites = rank_sites

    def site_sets(ctx):
        out = {}
        for L in "BAX":
            r = rank_sites(ctx, L)
            first = [j for j, d in r if d < {"B": 5.0, "A": 6.0}[L]] if L != "X" else [j for j, _ in r[:8]]
            out[L] = {"ranked": r, "first": first, "far": [r[-1][0], r[-2][0]], "far4": [r[-1][0], r[-2][0], r[-3][0], r[-4][0]]}
            out[L]["production"] = out[L]["first"] + out[L]["far"]
            if sorted(first) != sorted(m.FIRST_SHELL[L]) and ctx.member != "ref233":
                raise m.S2Error(f"{ctx.member} {L}: first shell {sorted(first)} differs from {m.FIRST_SHELL[L]}")
        out["mig_host"] = ctx.mig_host
        return out
    m.site_sets = site_sets

    def region_id(member, site, free):
        return hashlib.sha256(json.dumps({"free": sorted(int(x) for x in free), "member": member, "site": int(site)},
                                         sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    m.region_id = region_id

    def build_region(host_relaxed, member, site, *, vi=m.VI):
        cell, sym = host_relaxed.cell.array, np.array(host_relaxed.get_chemical_symbols())
        cv, cs = host_relaxed.positions[vi], host_relaxed.positions[site]
        d = np.minimum(find_mic(host_relaxed.positions - cv, cell, pbc=True)[1],
                       find_mic(host_relaxed.positions - cs, cell, pbc=True)[1])
        free = {int(i) for i in range(len(host_relaxed)) if sym[i] in ("Pb", "I", "Cs") and d[i] < 6.0}
        for c in np.flatnonzero(sym == "C"):
            if d[c] < 6.0:
                free |= set(a38.molecule(host_relaxed, int(c), sym, cell)[0])
        free = sorted(free)
        L = {"Pb": "B", "C": "A", "I": "X"}[sym[site]]
        return {"schema": "s2-region-1", "member": member, "site": int(site), "sublattice": L, "radius_A": 6.0,
                "free": free, "n_free": len(free), "region_id": region_id(member, site, free)}
    m.build_region = build_region
    m.to_vac_map = lambda vi=m.VI: (lambda j: int(j) if int(j) < vi else int(j) - 1)

    def free_in_cell(region, cell_kind, *, built=None, vi=m.VI):
        tv, f = m.to_vac_map(vi), [int(x) for x in region["free"]]
        if cell_kind == "host":
            return sorted(f)
        img = [tv(j) for j in f if j != vi]
        if cell_kind == "V":
            return sorted(img)
        base = f if cell_kind == "D" else img
        out = {built.old_to_new[j] for j in base if j in built.old_to_new} | {int(x) for x in built.members}
        return sorted(out)
    m.free_in_cell = free_in_cell

    def make_vacancy(host_relaxed, ctx):
        ref = s29.ref_vacancy_position(os.path.join(ROOT, b42.POOL), os.path.join(ROOT, b42.VAC_REF))
        vac, vpos, mig = pp.build_pair(host_relaxed, ref, None, None)
        if not np.array_equal(np.delete(host_relaxed.positions, m.VI, axis=0), vac.positions):
            raise m.S2Error("the deleted atom is not I127")
        return vac, int(mig)
    m.make_vacancy = make_vacancy

    def build_pair(host_rel, vac_rel, ctx, token, site, pose, *, partners):
        mig = "allow" if m.SUBLATTICE[token] == "X" else "forbid"
        return b42.build_paired(host_rel, vac_rel, m.VI, token, site, pose, vpos=ctx.vpos, mig=mig, partners=partners)
    m.build_pair = build_pair

    def build_host_leg(host_rel, ctx, token, site):
        if m.SUBLATTICE[token] == "X":
            return b42.build(host_rel, token, site, "inherit", vpos=ctx.vpos, mig="allow", mig_index=ctx.mig_host)
        return b42.build(host_rel, token, site, "inherit", vpos=ctx.vpos)
    m.build_host_leg = build_host_leg

    def pbcl_value(path=None, *, allow_provisional):
        p = path or os.path.join(ROOT, m.PBCL_RECORD)
        if not os.path.exists(p):
            raise m.S2Error("no Pb-Cl source record: no shifted Cl start is built")
        r = json.load(open(p))
        if r["decision"] == "confirmed_2.837":
            return {"d": 2.837, "tag": "[S] verified", "override": None}
        if r["decision"] == "use_source_value":
            return {"d": float(r["value_used_A"]), "tag": "[S] verified", "override": {"Cl:d_PbCl": float(r["value_used_A"])}}
        if not allow_provisional:
            raise b42.Refused("provisional Pb-Cl 2.837 A needs allow_provisional")
        return {"d": 2.837, "tag": "[M] starting point", "override": None}
    m.pbcl_value = pbcl_value

    def pose_starts(host_rel, ctx, token, site, *, pbcl=None):
        names = b42.sampled_names(token)
        if token == "Cs":
            got = b42.resolve_poses(host_rel, "Cs", site, label=f"{ctx.member}_Cs{site}", vpos=ctx.vpos)
        elif token == "Cl":
            if pbcl is None:
                got = [b42.build(host_rel, "Cl", site, "centred", vpos=ctx.vpos, mig="allow", mig_index=ctx.mig_host).pose]
            else:
                got = b42.resolve_poses(host_rel, "Cl", site, label=f"{ctx.member}_Cl{site}", vpos=ctx.vpos, mig="allow",
                                        mig_index=ctx.mig_host)
        else:
            got = [b42.build(host_rel, token, site, "inherit", vpos=ctx.vpos).pose]
        out = []
        for p in got:
            nm = p.get("name")
            out.append({"start": f"p{names.index(nm) if nm in names else 0}", "pose": p, "name": nm,
                        "tag": (pbcl or {}).get("tag") if token == "Cl" and str(nm).startswith("shift") else None})
        return out
    m.pose_starts = pose_starts
    return m


def _mock47():
    """Stub of scripts/47 (interface spec section 7): the writer (ASE espresso-in with the section-6 settings),
    electron counts, and status/counts parsers of the pw.x text markers. No energy is captured by any of them,
    except end_rule mode at the cap (F(180), F(200)), as the spec allows."""
    m = types.SimpleNamespace()
    m.S2Error = RuntimeError
    m.K_CAP, m.PLATEAU_FROM, m.PLATEAU_MEV = 200, 180, 3.0
    m.RANKS_SP, m.RANKS_A2_DEFAULT = 64, 48
    m.PSEUDO_DIR = "/data/pseudo"
    m.N_EL_HOST, m.N_EL_VAC_NEUTRAL = 1070, 1063
    m.DVAL = {"Sr": -4, "Ca": -4, "Cl": 0, "Cs": -10, "GA": 6}
    PSEUDO = {"Pb": "Pb.pbe-dn-rrkjus_psl.1.0.0.UPF", "I": "I.pbe-n-rrkjus_psl.1.0.0.UPF",
              "Cs": "Cs.pbe-spn-rrkjus_psl.1.0.0.UPF", "C": "C.pbe-n-rrkjus_psl.1.0.0.UPF",
              "N": "N.pbe-n-rrkjus_psl.1.0.0.UPF", "H": "H.pbe-rrkjus_psl.1.0.0.UPF",
              "Sr": "Sr.pbe-spn-rrkjus_psl.1.0.0.UPF", "Cl": "Cl.pbe-n-rrkjus_psl.1.0.0.UPF",
              "Ca": "Ca.pbe-spn-rrkjus_psl.1.0.0.UPF"}

    def n_x(at):
        s = at.get_chemical_symbols(); return s.count("I") + s.count("Cl")

    def charge_for(at, label):
        nx = n_x(at)
        if nx == 60:
            if label.endswith("_q0"):
                raise b42.Refused("_q0 on a vacancy-free cell")
            return 0
        if nx == 59:
            return 0 if label.endswith("_q0") else 1
        raise b42.Refused(f"{nx} X-site units")
    m.charge_for = charge_for

    def electrons(at, label):
        z = sum(b42.VALENCE[s] for s in at.get_chemical_symbols()); q = charge_for(at, label)
        n = z - q
        if n % 2 and not label.endswith("_q0"):
            raise b42.Refused(f"{label}: odd electron count {n}")
        return {"z_sum": z, "tot_charge": q, "n_el": n, "even": n % 2 == 0}
    m.electrons = electrons

    def settings_for(label, kind):
        g1 = label.startswith("s2g1_") and label.endswith("_e60")
        return {"calculation": "relax" if kind == "relax" else "scf", "ecutwfc": 60.0 if g1 else 50.0,
                "ecutrho": 480.0 if g1 else 400.0, "degauss": 0.005, "nspin": 2 if label.startswith("s2spin_") else 1,
                "conv_thr": 1e-8, "mixing_beta": 0.3, "electron_maxstep": 200, "disk_io": "low" if kind == "relax" else "none"}
    m.settings_for = settings_for

    def write_input(atoms, label, outdir, *, kind="sp", free=None, nstep=None, restart_mode=None,
                    dopant_index=None, ranks=None, campaign=None, cell=None):
        from ase.constraints import FixAtoms
        from ase.io.espresso import write_espresso_in
        os.makedirs(outdir, exist_ok=True)
        at = atoms.copy(); at.set_tags([0] * len(at)); at.set_constraint()
        st, el = settings_for(label, kind), electrons(at, label)
        idata = {"control": {"calculation": st["calculation"], "prefix": label, "pseudo_dir": m.PSEUDO_DIR,
                             "outdir": "./tmp", "tprnfor": True, "tstress": False, "disk_io": st["disk_io"],
                             "verbosity": "low"},
                 "system": {"ecutwfc": st["ecutwfc"], "ecutrho": st["ecutrho"], "occupations": "smearing",
                            "smearing": "gaussian", "degauss": 0.005, "nspin": st["nspin"], "nosym": True,
                            "tot_charge": float(el["tot_charge"])},
                 "electrons": {"conv_thr": 1e-8, "mixing_beta": 0.3, "electron_maxstep": 200}}
        if kind == "relax":
            if free is None or nstep is None:
                raise b42.Refused("a relax input needs free and nstep")
            idata["control"].update({"forc_conv_thr": 7.8e-4, "etot_conv_thr": 1e-5, "nstep": int(nstep)})
            idata["ions"] = {"ion_dynamics": "bfgs"}
            fixed = sorted(set(range(len(at))) - {int(i) for i in free})
            at.set_constraint(FixAtoms(indices=fixed))
        if st["nspin"] == 2:
            mm = [0.1] * len(at)
            if dopant_index is not None:
                mm[dopant_index] = 1.0 / b42.VALENCE[at[dopant_index].symbol]
            at.set_initial_magnetic_moments(mm)
        path = os.path.join(outdir, f"{label}.in")
        with open(path, "w") as fh:
            write_espresso_in(fh, at, input_data=idata, pseudopotentials={s: PSEUDO[s] for s in sorted(set(at.get_chemical_symbols()))},
                              kpts=(1, 1, 1), koffset=(1, 1, 1))
        meta = {"schema": "s2-qejob-1", "label": label, "kind": kind, "settings": st, "electrons": el,
                "input_sha256": sha256_file(path), "ranks_expected": ranks, "mock": True}
        write_json(meta, os.path.join(outdir, f"{label}.meta.json"))
        return meta
    m.write_input = write_input

    def restart_input(src_in, dst_in, nstep_new):
        t = open(src_in).read()
        t2 = re.sub(r"restart_mode\s*=\s*'[a-z_]+'", "restart_mode    = 'restart'", t)
        t2 = re.sub(r"nstep\s*=\s*\d+", f"nstep           = {int(nstep_new)}", t2)
        diff = [(a, b) for a, b in zip(t.splitlines(), t2.splitlines()) if a != b]
        assert len(diff) == 2 and all(("restart_mode" in a or "nstep" in a) for a, _ in diff), diff
        with open(dst_in, "w") as fh:
            fh.write(t2)
        return {"src": os.path.basename(src_in), "dst": os.path.basename(dst_in), "nstep": int(nstep_new)}
    m.restart_input = restart_input

    ENDS = (("bfgs converged", "converged"), ("maximum number of steps has been reached", "nstep"),
            ("bfgs failed", "bfgs_failed"), ("convergence NOT achieved", "scf_failed"),
            ("Program stopped by user request", "exit_stop"))

    def _part(text):
        cyc = [int(x) for x in re.findall(r"number of scf cycles\s*=\s*(\d+)", text)]
        nconf = len(re.findall(r"^!", text, re.M))
        end = next((cls for mk, cls in ENDS if mk in text), None)
        if end is None:
            end = "killed" if "JOB DONE" not in text else "unknown"
        mk = next((mk for mk, cls in ENDS if mk in text), None)
        wall = re.findall(r"PWSCF\s*:.*?([\d.]+)s WALL", text)
        return {"n_config": nconf, "counters_first": {"scf_cycles": cyc[0]} if cyc else None,
                "counters_last": {"scf_cycles": cyc[-1]} if cyc else None, "end": end, "end_marker": mk,
                "job_done": "JOB DONE" in text, "wall_s": float(wall[-1]) if wall else None,
                "k_first": cyc[0] - 1 if cyc else None, "k_last": cyc[-1] - 1 if cyc else None}

    def parse_counts(path):
        return _part(open(path, errors="replace").read())
    m.parse_counts = parse_counts

    def parse_relax(parts, *, read="full", k_cap=200, mapping=None):
        ps = [_part(open(p, errors="replace").read()) for p in parts]
        n = 0; k_last = -1
        for p in ps:
            if p["k_first"] is not None and n and p["k_first"] != k_last + 1:
                return {"usable": False, "parts": ps, "n_config": n, "k_last": k_last, "end": "unusable"}
            n += p["n_config"]; k_last = p["k_last"] if p["k_last"] is not None else k_last
        n = min(n, k_cap + 1); k_last = min(k_last, k_cap)
        out = {"usable": True, "parts": ps, "n_config": n, "k_last": k_last, "end": ps[-1]["end"] if ps else None,
               "converged_at_k": k_last if ps and ps[-1]["end"] == "converged" else None}
        if read == "end_rule" and k_last >= k_cap:
            F = []
            for p in parts:
                F += [float(x) for x in re.findall(r"^!\s+total energy\s+=\s+(-?[\d.]+) Ry", open(p).read(), re.M)]
            out["F_180_eV"], out["F_200_eV"] = F[180] * 13.605693122994, F[200] * 13.605693122994
        return out
    m.parse_relax = parse_relax

    def end_rule(rel):
        if rel.get("end") == "converged" and rel["k_last"] <= 200:
            return {"outcome": "accepted_converged", "dF_200_180_meV": None}
        if rel["k_last"] >= 200:
            dF = (rel["F_200_eV"] - rel["F_180_eV"]) * 1000 if "F_200_eV" in rel else None
            ok = dF is not None and abs(dF) <= 3.0
            return {"outcome": "accepted_plateau" if ok else "unconverged_cap", "dF_200_180_meV": dF}
        if rel.get("end") in ("bfgs_failed", "scf_failed", "nstep"):
            return {"outcome": "unconverged_early", "dF_200_180_meV": None}
        return {"outcome": "incomplete", "dF_200_180_meV": None}
    m.end_rule = end_rule

    def sp_status(job_dir, label, *, meta=None):
        out = os.path.join(job_dir, f"{label}.out")
        tries = sorted(glob.glob(os.path.join(job_dir, f"{label}.out.try*")))
        if os.path.exists(os.path.join(job_dir, f"{label}.gaveup")):
            return {"status": "missing", "missing_reason": "no JOB DONE after one resubmission", "attempts": len(tries)}
        if os.path.exists(out):
            t = open(out, errors="replace").read()
            if "JOB DONE" in t:
                ok = "convergence has been achieved" in t and "convergence NOT achieved" not in t and len(re.findall(r"^!", t, re.M)) == 1
                w = re.findall(r"PWSCF\s*:.*?([\d.]+)s WALL", t)
                return {"status": "complete" if ok else "missing",
                        "missing_reason": None if ok else "SCF not converged (JOB DONE)", "attempts": len(tries) + 1,
                        "wall_s": float(w[-1]) if w else None}
            return {"status": "running", "missing_reason": None, "attempts": len(tries) + 1}
        return {"status": "pending", "missing_reason": None, "attempts": len(tries)}
    m.sp_status = sp_status

    def upf_check(pseudo_dir, *, reference=None):
        return {"schema": "s2-upf-1", "passed": False, "reason": "stub of scripts/47: no UPF check implemented"}
    m.upf_check = upf_check
    return m


def _mock49():
    """Stub of scripts/49 (interface spec section 8): the decision constants the runner needs and the job-start rule."""
    m = types.SimpleNamespace()
    m.RULES = {"HARD_CAP_H": 520.0, "K_BT_MEV": 25.7,
               "UNIT_COST_H": {"sp": 6.74 / 60, "a2": 20.6, "a2_config": 6.15 / 60, "mace": 2 / 60, "host": 3.3, "smoke": 1.0,
                               "throughput": 1.5, "sp_g1": 1.31 * 6.74 / 60, "sp_spin": 2 * 6.74 / 60}}

    def expected_hours(kind, measured):
        meas = [float(x) for x in (measured or []) if x is not None]
        return sum(meas) / len(meas) if meas else m.RULES["UNIT_COST_H"][kind]
    m.expected_hours = expected_hours
    m.job_start_allowed = lambda H, e: float(H) + float(e) <= m.RULES["HARD_CAP_H"]
    return m


# ---------------------------------------------------------------- small helpers (used by the stubs too)
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def fsync_dir(d):
    try:
        fd = os.open(d, os.O_RDONLY); os.fsync(fd); os.close(fd)
    except OSError:
        pass


def write_json(obj, path):
    """Atomic JSON write (temporary file, fsync, rename, directory fsync): a kill never leaves half a record."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = f"{path}.tmp{os.getpid()}"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=1); fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp, path)
    fsync_dir(os.path.dirname(os.path.abspath(path)))


def write_text(text, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = f"{path}.tmp{os.getpid()}"
    with open(tmp, "w") as fh:
        fh.write(text); fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp, path)
    fsync_dir(os.path.dirname(os.path.abspath(path)))


def read_json(path, default=None):
    try:
        with open(path) as fh:
            return json.load(fh)
    except FileNotFoundError:
        return default


def append_jsonl(path, obj):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps(obj, sort_keys=True) + "\n"); fh.flush(); os.fsync(fh.fileno())


def utc(t=None):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() if t is None else t))


def parse_cpulist(s):
    """A Linux CPU list ('0-31,40,42-43') as a set of ints (N-F30)."""
    out = set()
    for part in str(s).strip().split(","):
        part = part.strip()
        if not part:
            continue
        a, _, b = part.partition("-")
        out.update(range(int(a), int(b or a) + 1))
    return out


def pair_check(a, b, overlap_min=None):
    """N-F30 (round-4 R4-C1-1 and missed item): two 32-rank copies count as the section 16 layout 'two concurrent
    32-rank copies' only if each recorded a core set, the two sets are disjoint, the CPUs their pw.x ranks were allowed
    (when recorded) are disjoint and inside their sets, and their walls overlap for >= overlap_min of the shorter one.
    a, b: {"cpuset", "affinity", "interval": [start, end]}. Returns {"valid", "reasons", "overlap"}."""
    why, ov = [], None
    overlap_min = PAIR_OVERLAP_MIN if overlap_min is None else overlap_min
    sa, sb = (parse_cpulist(x["cpuset"]) if x.get("cpuset") else None for x in (a, b))
    if not sa or not sb:
        why.append("a copy without a recorded core set")
    elif sa & sb:
        why.append("the two core sets overlap")
    fa, fb = (parse_cpulist(x["affinity"]) if x.get("affinity") else None for x in (a, b))
    if fa is not None and fb is not None and fa & fb:
        why.append("the pw.x ranks of the two copies shared CPUs")
    for f_, s_ in ((fa, sa), (fb, sb)):
        if f_ is not None and s_ and not f_ <= s_:
            why.append("pw.x ranks outside their core set")
    ia, ib = a.get("interval"), b.get("interval")
    if not (ia and ib and all(v is not None for v in (*ia, *ib))):
        why.append("a copy without a recorded interval")
    else:
        short = min(ia[1] - ia[0], ib[1] - ib[0])
        ov = min(ia[1], ib[1]) - max(ia[0], ib[0])
        if short <= 0 or ov < overlap_min * short:
            why.append(f"the walls overlap {ov:.0f} s, < {overlap_min:.0%} of the shorter wall {short:.0f} s")
    return {"valid": not why, "reasons": why, "overlap_s": ov}


def cpulist(cpus):
    """The compact Linux CPU list of an iterable of ints (N-F30)."""
    xs, out = sorted(set(int(c) for c in cpus)), []
    i = 0
    while i < len(xs):
        k = i
        while k + 1 < len(xs) and xs[k + 1] == xs[k] + 1:
            k += 1
        out.append(f"{xs[i]}-{xs[k]}" if k > i else f"{xs[i]}")
        i = k + 1
    return ",".join(out)


c46 = _load_or_mock("c46", "46_s2_cells.py", _mock46)
q47 = _load_or_mock("q47", "47_s2_qe.py", _mock47)
g49 = _load_or_mock("g49", "49_s2_gates.py", _mock49)
S2Error = c46.S2Error


# ---------------------------------------------------------------- constants (interface spec 2.4)
NODE_ROOT = "/data"
CHECKOUT = "/data/work/ps_s2"
WORK = "/data/work/s2"
JOBS = "/data/jobs"
KEEP_ALIVE = "/data/KEEP_ALIVE"                              # dopant_shell/WP3_RUNBOOK.md step 4
RUN_QE, QUEUE, CHAIN = "/usr/local/bin/run_qe.sh", "/data/setup/qe_queue.sh", "/data/setup/chain.sh"
QE_PROFILE = "/etc/profile.d/qe.sh"                           # sourced by run_qe.sh and s2_run_qe.sh (node only)
S2_RUN_QE = "ehpc/node/s2_run_qe.sh"                          # the committed launcher of every pw.x run outside the
                                                              # queue, used from the checkout (round 4, N-F30)
TP_PAIR = ("s2tp_ref232_np32a", "s2tp_ref232_np32b")          # the throughput row's two concurrent copies (section 16)
PAIR_OVERLAP_MIN = (getattr(g49, "RULES", None) or {}).get("TP_PAIR_OVERLAP", 0.9)   # >= 90% of the shorter wall (I-C13)
CHAIN_LOCK = "/" + "tmp/qe_chain.global.lock"                 # as ehpc/node/chain.sh (assembled: no literal temporary
                                                              # path in a repository file; never serialised)
PY_NODE = "/data/miniforge3/envs/mace/bin/python"
SPOT_URL_FILE = "/data/setup/s2_spot_url"                    # node-local, never in the repository (X-5)
SPOT_HELPER = "scripts/wp3_runbook/node_step7.sh"            # the committed helper whose SPOT_URL line is read (X-5)
MACE_RERUNS, A2_RERUNS_FROM_ZERO, PW_RERUNS = 2, 2, 2        # section 13: at most twice; smoke/throughput runs alike (N-D10)
HEARTBEAT_S, SPOT_POLL_S, NOTICE_HOLD_S, TICK_S, COUNTS_EVERY_S = 60, 5, 1800, 5, 30
# Section 16 node-hours when a past boot's journal cannot be read (I-F8): after the last heartbeat the node may stay up
# until the idle self-stop of WP3_RUNBOOK.md step 4 (60 idle minutes); 15 minutes are added for the cron interval and
# the stop itself, so the assumed end is never earlier than the real one (an over-count is conservative for the cap)
IDLE_STOP_S, IDLE_MARGIN_S = 3600.0, 900.0
# N-F13 (round-2 S2): a hung child is a STOP for a human: no line written to a pw.x output for 2 h, or a MACE attempt
# running beyond 3 h (host relaxation: 12 h); generous against the section 16 unit costs (17-27 min, 1.7 h)
STALL_OUT_S, MACE_WALL_S = 7200.0, {"host": 12 * 3600.0, "frozen": 3 * 3600.0}
# N-F18 (round-3 R3-C1-7, D-S0-8): the spot endpoint must answer (200 or 404) within SPOT_FIRST_S of the poller's start
# before any job runs, and a last good poll older than SPOT_STALE_S is a STOP (a notice that cannot arrive)
SPOT_FIRST_S, SPOT_STALE_S = 120.0, 300.0
CAMPAIGNS = ("c1", "c2", "c3", "c4")
K_TOTAL = 201                                               # configurations k = 0 ... 200 (section 11)
SP_AHEAD = 2                                                # single points published ahead of completion (I-D2)
ADMISSIBILITY_RECORD = "results/objective2/s2/stage0/admissibility.json"
PBCL_RECORD = "results/objective2/s2/stage0/pbcl_source.json"
PHASES = {"c1": ("check", "smoke", "tp", "smoke2", "mace", "qe", "gate"),
          "c2": ("check", "a2"),
          "c3": ("check", "pre", "mace", "qe", "gate"),
          "c4": ("check", "pre", "a2", "gate"),
          "t": ("check", "smoke", "tp", "smoke2", "mace", "qe", "a2", "gate")}       # the self-test graph (run as c1)
TERMINAL = {"done", "missing", "skipped", "rejected", "not_started_cap", "not_run", "killed_by_gate"}
TERMINAL_A2 = {"complete", "missing", "killed_by_gate", "not_run_gate", "not_started_cap"}   # A2 record statuses
CAP_KINDS = frozenset({"mace", "sp", "pw", "a2"})          # the jobs that consume node-hours, the only ones capped (N-F14)
TOKENS_OF = {"B": ("Sr", "Ca"), "A": ("Cs", "GA"), "X": ("Cl",)}
PILOT_FAR_X_B = {"Cl": 175, "Ca": 76}                         # section 7: the farthest m30 I and Pb (spin rows)
G1_SITES = (("Cl", "X", 138), ("Ca", "B", 136))                # section 7: Cl at I138, Ca at Pb136 on m30
Q0_ROWS = ("s2_m30_VB136_q0", "s2_m30_Sr136o0_vac_q0", "s2_m30_Ca136o0_vac_q0", "s2_m30_VB76_q0",
           "s2_m30_Sr76o0_vac_q0", "s2_m30_VX138_q0", "s2_m30_Cl138o0_vac_q0", "s2_m30_VA128_q0",
           "s2_m30_Cs128o0_vac_q0", "s2_m30_GA128o0_vac_q0")                      # section 10 (10 rows)
C2_ORDER = ("s2r_m30_VB136", "s2r_m30_hostB136", "s2r_m30_Sr136o0_novac", "s2r_m30_Sr136o0_vac",
            "s2r_m30_hostB76", "s2r_m30_VB76", "s2r_m30_Sr76o0_novac", "s2r_m30_Sr76o0_vac",
            "s2r_m30_Ca136o0_novac", "s2r_m30_Ca136o0_vac")                       # section 11 (fixed)
SP_LABELS_FIXED = {"G1": ("s2g1_m30_host_e60", "s2g1_m30_Cl138o0_novac_e60", "s2g1_m30_Cl138o0_novac_e50",
                          "s2g1_m30_Ca136o0_novac_e60", "s2g1_m30_Ca136o0_novac_e50"),
                   "spin": ("s2spin_m30_Cl175o0_vac", "s2spin_m30_Ca76o0_vac"),
                   "step0": ("s2_m30_VB136", "s2_m30_Sr136o0_vac")}

# Interpretations (I), implementation notes (N) and conflicts (X) implemented here; the ids of the interface spec,
# and the D-numbered ones added by this module. Printed by --self-test, recorded in campaign.json.
NOTES = {
    "X-3": "A2 needs c1/smoke.json with an affine nstep mapping of slope 1 and a restart that reproduces the "
           "uninterrupted count; otherwise restart_possible is false and every A2 interruption uses the rerun rule",
    "X-4": "smoke tests at 48 ranks first, then the throughput row; if another A2 layout is chosen, the exit/restart "
           "smoke test is repeated at it (s2smoke_ref232_rst<layout>) before C2",
    "X-5": "spot URL from the node-local /data/setup/s2_spot_url, else the SPOT_URL line of the committed "
           "scripts/wp3_runbook/node_step7.sh; it must start with http:// and end with /termination-time",
    "I-10": "revised after review F5 and by D-S0-2 as revised on 2026-11-04 (STAGE0 section 9): every planned A2 "
            "relaxation runs, whatever the validity of its A1 start cell (the plan skips none); A1 validity enters no "
            "gate, class or decision (a delta is valid by the section 11 rule alone, scripts/48); it is reported by K2 "
            "and K3 (scripts/49) and beside each delta, with a reported-only A1-start sensitivity row (scripts/48)",
    "I-F1": "section 11 final-geometry checks (review F1): when a relaxation completes, the positions of its last "
            "configuration (scripts/47 read final_geom, no energy) are written as <label>.final.extxyz; once it and "
            "its partner (host_R for V+_R and D, V+_R for D+V) have ended, scripts/46 validate-a2 runs checks 2-5 "
            "(host_R: 4) and validity_final {valid, failed} is written into the A2 record; K3 waits for these checks; "
            "a partner without a final geometry (missing, not run, killed, or complete without a configuration) and "
            "a relaxation completed without a configuration (k_last None, e.g. an SCF failure at k = 0): the check is "
            "not evaluated (skipped, no validity_final), the quartet is invalid through the missing cell (round-2 "
            "R2V-1, R2V-2)",
    "I-F6": "section 16 hard cap (review F6): the measured walls of every completed job of S2 so far are loaded from "
            "the files at each runner start (A2 records, MACE records, single-point outputs in status mode, smoke and "
            "throughput records), so expected durations survive a relaunch and carry across campaigns",
    "I-F7": "section 16 'jobs already running finish' (review F7): the restart part of an A2 relaxation that had started "
            "is checked against the cap with the expected time of the configurations still allowed (201 - completed) "
            "x the measured wall per configuration (else 6.15 min); a rerun from k = 0 counts as a whole relaxation",
    "I-F8": "section 16 node-hours (review F8): a past boot whose journal cannot be read ends at its last heartbeat "
            "+ 60 s + 60 min (the idle self-stop) + 15 min, unless ledger/manual.json gives its stop time by boot id",
    "N-F6": "N-6 implemented (review-2 F6): pw.x outside the queue starts only while the runner holds the global chain "
            "lock (passed to the child, released when none runs) and no pw.x it did not start is alive",
    "N-F7": "section 13 restart (review-2 F7): a restart nstep below 1 (possible when c0 >= 1) is written as 1; the exit "
            "file at k = 200 and the parser's cut at k = 200 keep the cap",
    "N-F8": "section 16 'jobs already running finish' (round-2 R2V-3): the section 11 checks (geometry only, seconds) "
            "complete a relaxation that was allowed to start; they run whatever the hard cap, so a cap refusal while a "
            "copy runs never leaves a completed relaxation without its validity_final (generalised by N-F14)",
    "N-F14": "section 16 hard cap (analyst decision 2026-11-04, round-2 open item N-C7): only jobs that consume "
             "node-hours are refused by the cap and swept to not_started_cap: pw.x (single points, smoke and "
             "throughput runs, A2 parts) and MACE (CAP_KINDS); gates (G1, N, n rule, pose rule, throughput, step-0, "
             "K2, projection, K3, c3_complete, c4_end), the section 11 check jobs and the other jobs that cost no "
             "node-hours (scripts/46 geometry builds, the G1 cells, the smoke and throughput records, the UPF and "
             "foundation checks) are never swept and are evaluated whenever their inputs are complete (any end of "
             "their dependencies); separability is evaluated by scripts/48 at the one evaluation",
    "N-F10": "section 13 (round-2 M1): SIGTERM (a reboot or a stop of the node) is an interruption, not a STOP: "
             "nothing new starts, it is logged in interruptions.jsonl, KEEP_ALIVE is removed, the runner waits for its "
             "children and exits with the campaign still 'running' and no CAMPAIGN_STOPPED, so s2_relaunch.sh "
             "relaunches it after the boot; an operator's STOP for a human is SIGINT",
    "N-F11": "section 17 item 2 (round-2 S4): on the node the runner refuses to start unless it is the scripts/50 of "
             "the recorded checkout /data/work/ps_s2, so the commit check covers the code that runs",
    "N-F12": "section 5 (round-2 S3, a reading): the cells and single points of a host whose S2 relaxation is invalid "
             "still run as planned (the runner reads no validity); scripts/48 applies 'missing for every dopant' "
             "through host_valid, so their values are reported only",
    "N-F13": "section 13 'wall time' (round-2 S2): a pw.x output (A2 part, smoke or throughput run, single point) not "
             "written for 2 h while its process lives, or a MACE attempt running beyond 3 h (host relaxation 12 h), "
             "is a STOP for a human (nothing is killed); the operator ends the process and resolves with RESOLVE",
    "N-F9": "section 16 projection (round-2 F3): the runner passes only the projection point and H_spent; scripts/49 "
            "derives tau_SP and the C1 MACE timings from the blinded C1 records (I-C7b: mean frozen-relaxation wall / "
            "10 concurrent, the longest C1 host wall); no campaign phase wall (which would hold the host wave and any "
            "stopped time between boots) enters the projection",
    "I-21": "expected durations from scripts/49 expected_hours(kind, measured walls of completed jobs of the kind)",
    "I-23": "a counted boot without btime or heartbeat evidence makes the ledger incomplete: no job starts (STOP)",
    "I-28": "see X-4",
    "I-31": "cells whose every dopant was removed (G1 failure, cuts) are not run, region cells included",
    "I-48": "a part that ends by nstep before k = 200 is unconverged early and STOPs the campaign (mapping wrong)",
    "N-5": "single points are published one input at a time (meta first, then <label>.in.part renamed to .in)",
    "N-6": "A2 relaxations, smoke tests and the throughput row run through the committed ehpc/node/s2_run_qe.sh (the "
           "node's run_qe.sh with an optional core set, round 4, N-F30) under the global chain lock",
    "N-7": "MACE work never runs beside pw.x: phases are strictly ordered within a campaign",
    "N-9": "a MACE attempt that ended with a Python exception (or a refusal) is a STOP for a human, not an interruption",
    "N-10": "the hard-cap check of a single point uses twice its expected duration (one automatic resubmission)",
    "N-11": "after a spot notice nothing new starts for 1800 s; running children continue; held() reads the notice "
            "itself, so a notice written while one scheduler pass runs its synchronous jobs holds every later launch of "
            "that pass (round-4 missed item)",
    "N-12": "KEEP_ALIVE is removed at the end of a campaign, at every STOP (first, before any write: round-2 F1), at a "
            "shutdown signal, whenever the runner exits, and by the spot poller when the runner died without "
            "CAMPAIGN_DONE (SIGKILL, OOM; the poller removes only the file that runner wrote)",
    "I-D1": "section 11 step-0: evaluated as soon as configuration k = 0 of the relaxation is complete; a failure "
            "stops A2 at once: the checked relaxation and any running partner are stopped by their exit files and "
            "marked killed_by_gate (outputs not read), nothing further starts; fail_pending_fix is a STOP for a "
            "human, resumed either with c2/STEP0_FIX ('<new commit> <dated note>'), after which C2 restarts at "
            "relaxation 1 for the one repeat (state 'repeat_pending', both cells checked as attempt 2; the attempt-1 "
            "A2 files and gate files moved to discarded/step0_attempt1_<t>/; the gate files are archived, the "
            "attempt-1 A2 records and outputs stay on the node, round-2 R2V-4), or with c2/STEP0_NO_ERROR (no error "
            "found: fail_final, A2 stops, A1 tier only)",
    "I-D2": "section 16 hard cap with queued single points: at most two published single points are incomplete at a "
            "time, and a publication is allowed iff H_spent + 2 x expected (each outstanding and the new one) <= 520, "
            "which is never below the check at the job's actual start",
    "I-D3": "section 16 two-copy layout: a gate on a finished relaxation does not delay the start of the next one in "
            "order; a stopping decision stops every running A2 part (exit file) and marks it killed_by_gate",
    "I-D4": "sections 9, 12: the default-pose single point (o0) of a pose or multi-pose site is run for the default "
            "cell whatever its validity; o<k>=1.. come from the distinct-minima map of scripts/46; a slot without "
            "a kept minimum is skipped",
    "I-D5": "section 13 A2: restart data are usable iff the part's output carries the soft-exit marker recorded by "
            "the smoke test and every file of smoke.mapping.restart_files exists for the prefix; otherwise rerun "
            "from k = 0 with the identical part-1 input, earlier parts and tmp/ moved to discarded/ unread",
    "I-D6": "section 11 end classes: a part that ends by nstep or by the cap exit file at k = 200 is at the cap "
            "(end rule applies); converged, BFGS or SCF failure and a pw.x error banner (scripts/47 pw_error: "
            "unconverged early, STOP for a human after the gates on ended relaxations, N-F20) end the relaxation; an end without JOB DONE is an interruption only "
            "if the part started in an earlier boot, was asked to exit (spot, gate), or its pw.x was OOM-killed; any "
            "other end without JOB DONE in this boot (a QE error on a rank whose output is not written, a crash) is "
            "a STOP for a human with RESOLVE 'unconverged', 'rerun' or 'missing' (round-2 F2, R2-QE-1), never an "
            "automatic rerun",
    "I-D7": "section 13 causes: an attempt that started in an earlier boot without an end is an interruption, "
            "cause spot-notice if that boot has a recorded notice, oom if its kernel journal has an OOM kill of the "
            "command's own pid (MACE: <rc>.pid written by the wrapper) or of a pw.x rank after the part's start (A2), "
            "else node-loss; every cause is rerun alike (round-2 F4)",
    "I-D8": "section 16 smoke tests: on the 232-atom reference cell at q = +1 with the Pb136-like frozen region of "
            "the throughput row; n1 (nstep 1) and n3 (nstep 3) fix c0 and the slope; rst stops part 1 by the exit "
            "file after k = 0 and restarts it; nstep_first = 201 - c0; nstep after a restart = 201 - completed - c0, "
            "valid only if the restart test reproduces the n3 count",
    "N-D1": "gate decisions are applied by updating the state fields named in the gate output's decision; the runner "
            "computes no decision",
    "N-D2": "before every gate the ledger snapshot is written to ledger/snapshot.json and <campaign>/ledger.json "
            "(scripts/49 may not load this script)",
    "N-D3": "geometry jobs of scripts/46 (region, build-vac, build-pair, distinct) run synchronously in the runner; "
            "they cost no node-hours, so the hard cap never refuses them (N-F14), and the spot hold does not apply "
            "to them",
    "N-D4": "a STOP removes KEEP_ALIVE, writes CAMPAIGN_STOPPED and starts nothing more; the runner waits for its "
            "running children (poller and heartbeat kept) and then exits; every step of a STOP is guarded, so a full "
            "or read-only /data or a hygiene refusal never keeps the runner from draining (round-2 F1, M2), and the "
            "stop reason in campaign.json is redacted to pass the hygiene rules (the raw text stays in campaign.log)",
    "N-D5": "a STOP for one job is resolved by the operator with <job dir>/RESOLVE holding 'rerun <note>' or "
            "'missing <note>' (an A2 relaxation also 'unconverged <note>': section 11, not rerun); it is logged in "
            "interruptions.jsonl",
    "N-D6": "during a spot hold no single point is published; one already published may still be started by the queue",
    "N-D7": "every read of a QE output by the runner is logged with its mode in <campaign>/runner_reads.jsonl "
            "(status, counts and end_rule only)",
    "N-D8": "superseded by I-F1 (review F1): the runner reads the final positions of each A2 relaxation (final_geom "
            "mode, no energy) for the section 11 checks; it reads no other position",
    "N-D9": "C3 G1 failure of Ca removes 8 relaxations and 8 single points per host (the interface spec says 16; the "
            "plan's section 12 counts give Ca 8 cells per host); Cl removes 20 dopant and 10 V+ relaxations and 30 "
            "single points",
    "N-D10": "smoke-test and throughput runs cut by an interruption are rerun at most twice (the plan gives no rule); "
             "one that ends with QE's error banner (scripts/47 pw_error) is not an interruption: missing at once, "
             "not rerun (round-3 R3-C1-5, as I-D6 for A2)",
    "N-F15": "sections 8, 17 (round-3 R3-C1-1): the n-rule gate is 'nrule' (gate:nrule, gates/nrule.json); with 'n' "
             "beside 'N' the gate outputs and gates_applied markers were one file on a case-insensitive volume (the "
             "laptop's APFS: pull, archive, verify, the one evaluation); no two job ids, gate names, marker names, "
             "labels or work ids of C1-C4 fold to the same lower-case string (asserted), and archive() refuses source "
             "names that differ only in case, a gate file whose 'gate' field differs from its name and a marker whose "
             "'id' differs from its file name",
    "N-F16": "section 16 smoke tests (round-3 R3-C1-2, D-S0-8): the throughput row and A2 need the smoke mapping c0 "
             "from n1 and n3; without it the campaign STOPs naming the smoke tests (never an unexpected error); a "
             "pw.x reference run (smoke, smoke2, throughput) is resolved by <run dir>/RESOLVE 'rerun <dated note>' "
             "(its parts, outputs and tmp/ and the record built on them, smoke.json, smoke2.json or throughput.json "
             "with the throughput gate markers, moved to discarded/resolved_<t>/, logged in interruptions.jsonl) or "
             "'missing <note>'; RESOLVE is read only once no part of the run lives, never into a running run (round-4 "
             "R4-C1-4)",
    "N-F17": "D-S0-8 (round-3 R3-C1-3): a C1 STOP that needs a code fix resumes at the fixed commit with "
             "c1/NODE_FIX ('<new commit> <dated note>'), accepted only while C1 is stopped (CAMPAIGN_STOPPED present, "
             "C1 not done) and when its commit is the checkout HEAD; the change goes to state commit_history and "
             "NODE_FIX is renamed NODE_FIX.used.<t>; a NODE_FIX in another campaign or with C1 not stopped is refused; "
             "campaign.json keeps the campaign's start_commit beside the commit in force and the commit_history, and "
             "scripts/48 reports the history with the diff of scripts/46-50 of each step (round-4 R4-C1-6)",
    "N-F18": "sections 13, 16 and D-S0-8 (round-3 R3-C1-7): the spot-endpoint check is a reachability check: no job "
             "of a campaign runs until the poller has had a good poll (200 or 404, spot/heartbeat.<boot> newer than "
             "the poller's start); none within 120 s, or a last good poll older than 5 min while the campaign runs, "
             "is a STOP (a termination notice could not arrive); the heartbeat is written at every good poll, so its "
             "age is the age of the last good poll (round-4 R4-C1-1); a poller restarted after it ended gets its own "
             "120 s for its first good poll (the dead poller's heartbeat is not judged), and none is restarted once a "
             "shutdown or a STOP began (round-4 R4-C1-2); that grace is renewed only when the dead poller had a good "
             "poll of its own, so pollers that end before answering keep the first one's start and STOP 120 s after "
             "it (round-5 R5-1); the third such renewal within 300 s is a STOP, so pollers that each answer once "
             "and end cannot hold the scheduler (round-6 R6-C1-2)",
    "N-F19": "section 16 / X-4 (round-3 missed item): the smoke test at the chosen layout folds its verdict into "
             "smoke.json (at_layout, restart_possible false if it fails) before smoke2.json is written, and rec:smoke2 "
             "is done only when smoke.json carries at_layout for its label; C2 requires at_layout whenever the A2 "
             "layout is not 48 ranks",
    "N-F20": "sections 11, 16 (round-3 R3-1): an A2 end whose end rule asks for a STOP (pw_error, nstep before k = 200, "
             "other_end) is recorded and the STOP is held until no gate, section 11 check or other job without "
             "node-hours of the active phase is ready, so step-0, K2, the projection and K3 apply to the ended cell "
             "first; no node-hour job starts meanwhile; a gate decision that stops A2 puts the 'gate' exit file on "
             "every running A2 part at once (I-D3), and the drain records a part that ends after it as killed_by_gate "
             "(outputs moved aside unread)",
    "N-F21": "section 13 / N-F10 (round-3 R3-3 and missed item): a shutdown (SIGTERM) that kills a synchronous child "
             "(a scripts/49 gate, a scripts/46 geometry job or validate-a2) leaves that job pending (no marker, no "
             "STOP); a child found ended while the shutdown flag is set is not classified (A2 part, MACE attempt, "
             "reference pw.x run), so the relaunch judges it as an interruption of an earlier boot; a real STOP "
             "followed by SIGTERM still exits as stopped (return 3)",
    "N-F22": "sections 11, 16 (round-3 R3C-1): a section 11 check ends the scheduler tick like a gate, so the "
             "statuses are rebuilt and K3 is applied before the next A2 relaxation can start (at 48 ranks relaxation 9 "
             "never starts before K3)",
    "N-F23": "section 13 causes (round-3 R3-8): the runner records the process tree of every running A2 part "
             "(descendants of its wrapper, node /proc) in its launch record and in a2_pids.json (kept across reruns); "
             "an OOM kill in this boot is the part's interruption only for one of its own pids; without a recorded "
             "tree the pw.x task test of I-D7 applies, excluding every pid recorded for another A2 part (the other "
             "copy) in this boot; revised in round 4 (N-F34): 'a recorded tree' is one that holds pw.x ranks",
    "N-F24": "section 3 (round-3 R3-C1-4): the production list needs a recorded n of 8 or 10 (the n rule), else "
             "S2Error; C3 requires the C1 gates_applied marker of gate:nrule",
    "N-F25": "section 16 keep-alive (round-3 R3-C1-9): s2_relaunch.sh, when it refuses, removes a /data/KEEP_ALIVE "
             "older than the current boot (left by a runner killed with its node), so the idle self-stop applies; a "
             "refusal of s2_campaign.sh itself inside a relaunch is such a refusal, and without /data/work/s2 (before "
             "the first start) the relaunch refuses and s2_status.sh says 'not started' (round-4 R4-C1-3, R4-C1-8)",
    "N-F30": "section 16 throughput row and the 2x32 layout (round-4 R4-C1-1, error, and the node lens' missed items): "
             "every pw.x run outside the queue goes through the committed ehpc/node/s2_run_qe.sh (the node's run_qe.sh "
             "with an optional core set, used from the checkout); two concurrent 32-rank copies (np32a/np32b and every "
             "A2 part at 2x32) each run on one half of the physical cores (lscpu), 'taskset -c <half> mpirun --bind-to "
             "none', the recipe confirmed on the node (two separate 'mpirun --bind-to core' both bind from core 0); a "
             "part takes the half no running copy uses; every other run is bound as run_qe.sh binds; the core set, the "
             "CPUs the pw.x ranks were allowed (node /proc) and the interval are recorded; the two throughput copies "
             "always start together (a copy that completed without the other is moved aside, its measurement not "
             "used, discarded/paired_<t>, not one of its reruns; one whose partner is missing is skipped), and the "
             "2x32 rate is "
             "computed only for two copies on disjoint cores whose walls overlap for >= 90% of the shorter one "
             "(scripts/49 I-C13)",
    "N-F31": "section 16, D-S0-8 (round-4 R4-C1-2): check:nodescripts (no node-hours) records the sha256 of the node "
             "scripts behind every pw.x run (run_qe.sh, the QE profile, qe_queue.sh, chain.sh, s2_run_qe.sh) in "
             "c1/nodescripts_check.json and STOPs unless the queue, the chain and the launcher equal the checkout's "
             "ehpc/node copies byte for byte; C2-C4 STOP on any hash that differs from the C1 record; a commit change "
             "(c1/NODE_FIX, c2/STEP0_FIX) moves that campaign's check records to discarded/commit_<t>/, so the UPF, "
             "node-script and model checks run again, first, at the new commit (round-5 R5-2); until the UPF check "
             "has passed again, md5_extra is the newest passed moved C1 record, and a re-check with other Cl/Ca MD5 "
             "is a STOP (round-6 R6-C1-1, N-B9)",
    "N-F32": "STAGE0 section 8 item 1, D-S0-8 (round-4 R4-C1-3): a git failure in the checkout (no repository, a copy "
             "without .git, git's ownership refusal) is a STOP in the runner and a refusal in s2_campaign.sh; HEAD must "
             "be 40 hex digits, never an empty commit read as clean",
    "N-F33": "section 13, N-D10 (round-4 R4-C1-4): RESOLVE 'rerun' of a smoke or throughput run moves the attempts "
             "before it (discarded/p<n>_*) aside with the resolution, so the rerun has the two reruns of N-D10; an "
             "operator's MACE rerun after a STOP for a human (an exception, N-9) is marked counts false and is not one "
             "of the two reruns section 13 allows after a reclaim, node loss, OOM or wall time",
    "N-F34": "section 13 causes (round-4 R4-C1-5, R4-C24-2): a running pw.x part (A2, smoke, throughput) records its "
             "process tree with the pw.x ranks among it at every tick until all its ranks are in it, then every 30 s; "
             "an OOM kill is the part's only for one of its own recorded pids once pw.x ranks are recorded, else the "
             "pw.x task test after its start applies, excluding the pids recorded for another part in that boot",
    "N-F35": "section 5, STAGE0 section 8 item 3 (round-4 R4-C1-6): check:mace checks the foundation file's sha256 and "
             "then runs scripts/46 load_mace in a child process (the runner never imports mace): version, float64, "
             "cpu, the resolved file, Z coverage and torch threads before the first MACE job, no structure evaluated; "
             "a failure STOPs before the smoke tests and costs no MACE attempt; the record names the exception also "
             "when the child qualifies it ('c46.S2Error', round-5 M-1)",
    "N-F36": "sections 11, 16 (round-4 R4-C24-1): the STOP an A2 end rule asks for is durable: the A2 record carries "
             "end_rule.stop_raised false until CAMPAIGN_STOPPED holds the reason; every runner start re-holds such a "
             "STOP before any launch; every STOP's reason includes the held ones, which are then marked raised (an "
             "operator's relaunch after that STOP does not raise them again)",
    "N-F37": "section 16 'killed and its output discarded unread' (round-4 R4-C24-3 and the C2-C4 lens' missed item): a "
             "stopping gate's exit request replaces an earlier 'cap' or 'spot' one of a running part (the prior reason "
             "kept), so the part is killed_by_gate whatever its end; a relaxation waiting for its restart part when a "
             "gate stops A2 is killed_by_gate with its outputs and restart data moved aside unread",
    "N-F38": "section 16, X-3, D-S0-6, D-S0-8 (round-4 R4-C1-5): smoke tests n1 and n3 that both end with JOB DONE but "
             "do not differ by two configurations (no affine nstep mapping of slope 1) STOP C1 before the exit/restart "
             "test and the throughput row, naming the smoke tests and the NODE_FIX / RESOLVE path, so they can be "
             "repeated while C1 is open",
    "I-D9": "section 16 hard cap (round-3 R3C-7; a reading, confirmed by the analyst as D-S0-10): 'No job "
            "starts if H_spent plus the job's expected duration would exceed 520 h ... Whatever is then "
            "incomplete is missing' is read as: after the "
            "first refusal in a campaign no further pw.x or MACE job of that campaign starts (each is "
            "not_started_cap); the refusal is persisted in HARD_CAP.json and read back at every runner start, so a "
            "relaunch gives the same decision; jobs without node-hours are never swept (N-F14)",
    "N-D11": "a campaign whose preconditions are refused by recorded decisions (e.g. K3 a1_only for C4) is recorded "
             "as not_run without booting work; missing evidence for a precondition is a STOP",
}


# ---------------------------------------------------------------- node paths
class Node:
    """Node paths derived from root ('/data' on the node; <sysroot>/data in the self-test, where the /tmp and
    /usr/local/bin paths move under <sysroot> as well)."""

    def __init__(self, root=NODE_ROOT):
        self.root = os.path.abspath(root)
        sysroot = "" if self.root == NODE_ROOT else os.path.dirname(self.root)
        j = os.path.join
        self.work, self.jobs, self.keep_alive = j(self.root, "work", "s2"), j(self.root, "jobs"), j(self.root, "KEEP_ALIVE")
        self.setup, self.pseudo = j(self.root, "setup"), j(self.root, "pseudo")
        self.checkout = j(self.root, "work", "ps_s2") if sysroot == "" else ROOT
        self.queue, self.chain = j(self.setup, "qe_queue.sh"), j(self.setup, "chain.sh")
        self.run_qe, self.chain_lock = sysroot + RUN_QE, sysroot + CHAIN_LOCK
        self.qe_profile = sysroot + QE_PROFILE
        # N-F30: the committed launcher in the checkout on the node; in the self-test a copy with its node paths
        # rewritten under <sysroot> (as qe_queue.sh and chain.sh, _node_scripts)
        self.s2_run_qe = j(self.checkout, S2_RUN_QE) if sysroot == "" else sysroot + "/usr/local/bin/s2_run_qe.sh"
        self.lock, self.state = j(self.work, "s2.lock"), j(self.work, "state.json")
        self.ledger, self.spot = j(self.work, "ledger"), j(self.work, "spot")
        self.spot_url_file = j(self.setup, "s2_spot_url")

    def c(self, campaign):
        return os.path.join(self.work, campaign)


# ---------------------------------------------------------------- labels (grammar owned by scripts/46)
def wid_of(h, kind, L=None, j=None, T=None, n=None, leg=None):
    if kind == "host":
        w = f"s2_{h}_host"
    elif kind == "V":
        w = f"s2_{h}_V{L}{j}"
    else:
        w = f"s2_{h}_{T}{j}p{n}_{leg}"
    if not c46.WORK_RE.fullmatch(w):
        raise S2Error(f"work id {w!r} does not match scripts/46 WORK_RE")
    return w


def label_of(prefix, h, kind, L=None, j=None, T=None, k=None, leg=None, q0=False, ecut=None, check=True):
    body = ("host" + (f"{L}{j}" if L is not None else "")) if kind == "host" else (
        f"V{L}{j}" if kind == "V" else f"{T}{j}o{k}_{leg}")
    lab = f"{prefix}_{h}_{body}" + ("_q0" if q0 else "") + (f"_e{ecut}" if ecut else "")
    if check:
        c46.check_label(lab)
    return lab


def a1_of_a2(label):
    """s2r_ label -> (member, kind, L, j, token, leg, A1 work id); host_R starts from the S2-relaxed host."""
    g = c46.LABEL_RE.fullmatch(label)
    if not g or g.group("prefix") != "s2r":
        raise S2Error(f"{label} is not an A2 label")
    h = g.group("host")
    if g.group("hostcell"):
        L, j = g.group("hL"), int(g.group("hj"))
        return {"member": h, "cell_kind": "host", "L": L, "j": j, "token": None, "leg": None, "a1": wid_of(h, "host")}
    if g.group("vL"):
        L, j = g.group("vL"), int(g.group("vj"))
        return {"member": h, "cell_kind": "V", "L": L, "j": j, "token": None, "leg": None, "a1": wid_of(h, "V", L, j)}
    T, j, leg = g.group("tok"), int(g.group("j")), g.group("leg")
    return {"member": h, "cell_kind": "D" if leg == "novac" else "DV", "L": c46.SUBLATTICE[T], "j": j, "token": T,
            "leg": leg, "a1": wid_of(h, "D", T=T, j=j, n=0, leg=leg)}


def a2_parent(label):
    """Section 11 partner of an A2 cell for the final-geometry partner check: host_R for V+_R and D, V+_R for D+V,
    none for host_R."""
    a = a1_of_a2(label)
    h, L, j = a["member"], a["L"], a["j"]
    if a["cell_kind"] == "host":
        return None
    if a["cell_kind"] in ("V", "D"):
        return label_of("s2r", h, "host", L=L, j=j)
    return label_of("s2r", h, "V", L=L, j=j)


def cut_ids(state):
    """The section 16 cuts applied so far (scripts/49 cut_ids: the spec 4.9 records or bare numbers; review F2)."""
    f = getattr(g49, "cut_ids", None)
    if f is not None:
        return f(state)
    out = set()
    for c in (state or {}).get("cuts") or []:
        v = c.get("cut") if isinstance(c, dict) else c
        if v is not None:
            out.add(int(v))
    return out


# ---------------------------------------------------------------- site sets (geometry only, cached)
_SITE_CACHE = {}


def site_sets(member):
    if member not in _SITE_CACHE:
        _SITE_CACHE[member] = c46.site_sets(c46.host_context(member))
    return _SITE_CACHE[member]


def first_sites(S, L):
    return sorted(int(x) for x in S[L]["first"])


def far_sites(S, L):
    return [int(x) for x in S[L]["far"]]


def production_sites(S, L):
    """Section 4: the first shell then the far pair (f1, f2); the publication order of C3 (interface spec 9.2)."""
    return first_sites(S, L) + far_sites(S, L)


# ---------------------------------------------------------------- graph
class Graph:
    """Jobs keyed by id, in insertion order (= scheduling and publication order). A job added twice (a cell that
    serves two designs, e.g. the default start at a pose site) keeps its first definition; the second role is noted."""

    def __init__(self, campaign, phases):
        self.campaign, self.phases, self.jobs = campaign, tuple(phases), OrderedDict()
        self.order = itertools.count()

    def add(self, jid, kind, phase, deps=(), **kw):
        if phase not in self.phases:
            raise S2Error(f"phase {phase} not in campaign {self.campaign}")
        if jid in self.jobs:
            self.jobs[jid].setdefault("also", []).append(kw.get("cat"))
            return self.jobs[jid]
        j = {"id": jid, "kind": kind, "phase": phase, "deps": list(deps), "seq": next(self.order), **kw}
        self.jobs[jid] = j
        return j

    def counts(self):
        return dict(Counter(j.get("cat") for j in self.jobs.values() if j.get("cat")))

    def to_json(self):
        return {"schema": "s2-graph-1", "campaign": self.campaign, "phases": list(self.phases),
                "counts": self.counts(), "jobs": list(self.jobs.values())}


def _starts(T, multi):
    return list(range(len(b42.sampled_names(T)))) if multi else [0]


def _mace_site(G, c, h, L, j, tokens, *, role, cat_dopant, starts, prov):
    host = "mace:" + wid_of(h, "host")
    rid = f"region:{h}_{L}{j}"
    G.add(rid, "g46", "mace", [host], action="region", member=h, L=L, site=j, role=role)
    v = wid_of(h, "V", L, j)
    G.add(f"vstart:{v}", "g46", "mace", [rid], action="build-vac", member=h, work_id=v, L=L, site=j, role=role)
    G.add("mace:" + v, "mace", "mace", [rid, f"vstart:{v}"], action="relax", member=h, work_id=v, cell_kind="V", L=L,
          site=j, region=rid, parents={"host": wid_of(h, "host")}, role=role, cat="mace_V", xkind="mace")
    for T in tokens:
        for n in starts(T, j):
            pid = f"pair:{h}_{T}{j}p{n}"
            G.add(pid, "g46", "mace", [host, "mace:" + v], action="build-pair", member=h, token=T, site=j, L=L, start=f"p{n}",
                  legs={lg: wid_of(h, "D", T=T, j=j, n=n, leg=lg) for lg in ("novac", "vac")},
                  pose=b42.sampled_names(T)[n], parents={"host": wid_of(h, "host"), "vac": v}, partners="relaxed",
                  allow_provisional=bool(prov and T == "Cl" and n > 0), role=role)
            for leg in ("novac", "vac"):
                w = wid_of(h, "D", T=T, j=j, n=n, leg=leg)
                G.add("mace:" + w, "mace", "mace", [pid, rid], action="relax", member=h, work_id=w,
                      cell_kind="D" if leg == "novac" else "DV",
                      token=T, site=j, L=L, leg=leg, start=f"p{n}", region=rid, pair=pid,
                      parents={"host": wid_of(h, "host")} if leg == "novac" else {"vac": v}, role=role,
                      cat=cat_dopant if n == 0 else "mace_pose_extra", xkind="mace")


def _distinct(G, h, T, j, starts, role):
    for leg in ("novac", "vac"):
        wids = [wid_of(h, "D", T=T, j=j, n=n, leg=leg) for n in starts]
        G.add(f"distinct:{h}_{T}{j}_{leg}", "g46", "mace", ["mace:" + w for w in wids], action="distinct", member=h, token=T, site=j, leg=leg,
              starts=[f"p{n}" for n in starts], work_ids=wids, role=role)


def _sp(G, label, cell, cat, *, deps=None, src="cell", **kw):
    return G.add("sp:" + label, "sp", "qe", deps if deps is not None else ["mace:" + cell], label=label, cell=cell,
                 src=src, cat=cat, **kw)


def _pose_sps(G, h, T, j, nstarts, *, near, cat):
    """Section 9 / I-D4: o0 of the default cell (near sites only; far defaults are noise-pilot single points) and
    one slot per possible kept non-default minimum."""
    for leg in ("novac", "vac"):
        if near:
            _sp(G, label_of("s2", h, "D", T=T, j=j, k=0, leg=leg), wid_of(h, "D", T=T, j=j, n=0, leg=leg), cat)
        for k in range(1, nstarts):
            _sp(G, label_of("s2", h, "D", T=T, j=j, k=k, leg=leg), None, cat, deps=[f"distinct:{h}_{T}{j}_{leg}"],
                src="distinct", slot={"distinct": f"distinct:{h}_{T}{j}_{leg}", "k": k, "member": h, "token": T,
                                      "site": j, "leg": leg})


def _ref_block(G, state):
    """Section 16: pw.x smoke tests (n1, n3, rst p1 + p2 at 48 ranks) and the throughput row (5 configurations
    at 48, 64 and two concurrent 32-rank copies) on the 232-atom reference cell; the rst repeat at another layout."""
    common = {"cell": "ref232", "region": "ref_Pb136"}
    G.add("pw:s2smoke_ref232_n1", "pw", "smoke", [], label="s2smoke_ref232_n1", part=1, nstep=1, ranks=48,
          cat="pw_smoke", **common)
    G.add("pw:s2smoke_ref232_n3", "pw", "smoke", ["pw:s2smoke_ref232_n1"], label="s2smoke_ref232_n3", part=1,
          nstep=3, ranks=48, cat="pw_smoke", **common)
    G.add("pw:s2smoke_ref232_rst.p1", "pw", "smoke", ["pw:s2smoke_ref232_n3"], label="s2smoke_ref232_rst", part=1,
          nstep=3, ranks=48, exit_after=1, cat="pw_smoke", **common)
    G.add("pw:s2smoke_ref232_rst.p2", "pw", "smoke", ["pw:s2smoke_ref232_rst.p1"], label="s2smoke_ref232_rst",
          part=2, restart_of=1, ranks=48, cat="pw_smoke", **common)
    G.add("rec:smoke", "record", "smoke", ["pw:s2smoke_ref232_n1", "pw:s2smoke_ref232_n3", "pw:s2smoke_ref232_rst.p1",
                                            "pw:s2smoke_ref232_rst.p2"], what="smoke")
    G.add("pw:s2tp_ref232_np48", "pw", "tp", [], label="s2tp_ref232_np48", part=1, n_config=5, ranks=48, cat="pw_tp", **common)
    G.add("pw:s2tp_ref232_np64", "pw", "tp", ["pw:s2tp_ref232_np48"], label="s2tp_ref232_np64", part=1, n_config=5,
          ranks=64, cat="pw_tp", **common)
    for x in ("a", "b"):
        G.add(f"pw:s2tp_ref232_np32{x}", "pw", "tp", ["pw:s2tp_ref232_np64"], label=f"s2tp_ref232_np32{x}", part=1,
              n_config=5, ranks=32, cat="pw_tp", **common)
    G.add("rec:tp", "record", "tp", ["pw:s2tp_ref232_np48", "pw:s2tp_ref232_np64", "pw:s2tp_ref232_np32a",
                                      "pw:s2tp_ref232_np32b"], what="tp")
    G.add("gate:throughput", "gate", "tp", ["rec:tp"], gate="throughput", cat="gate")
    lay = state.get("a2_layout")
    if lay not in (None, "48"):
        lab = f"s2smoke_ref232_rst{lay}"
        r = 32 if lay == "2x32" else int(lay)
        G.add(f"pw:{lab}.p1", "pw", "smoke2", [], label=lab, part=1, nstep=3, ranks=r, exit_after=1, cat="pw_smoke2", **common)
        G.add(f"pw:{lab}.p2", "pw", "smoke2", [f"pw:{lab}.p1"], label=lab, part=2, restart_of=1, ranks=r,
              cat="pw_smoke2", **common)
        G.add("rec:smoke2", "record", "smoke2", [f"pw:{lab}.p1", f"pw:{lab}.p2"], what="smoke2", label=lab)


def m05_cal(state):
    cal = (state.get("stage0") or {}).get("m05_cal") or c46.CAL_SITES["m05"]
    return {L: int(cal[L]) for L in "BAX"}


def cal_sites(member, state):
    return {L: int(c46.CAL_SITES["m30"][L]) for L in "BAX"} if member == "m30" else m05_cal(state)


def pbcl_provisional(state):
    p = (state.get("stage0") or {}).get("pbcl") or {}
    return p.get("decision") == "provisional_2.837"


def graph_c1(state, sites=site_sets):
    G = Graph("c1", PHASES["c1"])
    G.add("check:upf", "check", "check", what="upf")
    G.add("check:nodescripts", "check", "check", what="nodescripts")             # N-F31 (round 4)
    G.add("check:mace", "check", "check", what="mace")
    _ref_block(G, state)
    prov = pbcl_provisional(state)
    pose = {T: set(c46.POSE_SITES[T]) for T in c46.MULTI_START}
    for p in c46.PILOTS:
        S, cal = sites(p), cal_sites(p, state)
        G.add("mace:" + wid_of(p, "host"), "mace", "mace", [], action="relax-host", member=p, work_id=wid_of(p, "host"),
              cell_kind="host", role="pilot",
              cat="mace_host", xkind="host")
        for L in "BAX":
            far4 = [int(x) for x in S[L]["far4"]]
            for f in far4:
                _mace_site(G, "c1", p, L, f, TOKENS_OF[L], role="noise", cat_dopant="mace_dopant_noise",
                           starts=lambda T, j: [0], prov=prov)
            _mace_site(G, "c1", p, L, cal[L], TOKENS_OF[L], role="cal", cat_dopant="mace_dopant_startset",
                       starts=lambda T, j: [0], prov=prov)
    # pose pilot (section 9, m30): every sampled start at the four pose sites; defaults are reused cells
    for T in c46.MULTI_START:
        for j in c46.POSE_SITES[T]:
            L = c46.SUBLATTICE[T]
            _mace_site(G, "c1", "m30", L, j, (T,), role="pose", cat_dopant="mace_dopant_noise",
                       starts=lambda TT, jj: _starts(TT, True), prov=prov)
            _distinct(G, "m30", T, j, _starts(T, True), "pose")
    G.add("g1:m30", "g1", "mace", ["mace:" + wid_of("m30", "host")], member="m30", cells=[list(x) for x in G1_SITES])
    # single points, in publication order (interface spec 9.2): G1, spin, noise, step-0, pose, q = 0
    _sp(G, SP_LABELS_FIXED["G1"][0], wid_of("m30", "host"), "sp_g1", sp_kind="sp_g1")
    for T, L, j in G1_SITES:
        for e in (60, 50):
            _sp(G, label_of("s2g1", "m30", "D", T=T, j=j, k=0, leg="novac", ecut=e), None, "sp_g1", deps=["g1:m30"],
                src="g1", g1=f"{T}{j}", sp_kind="sp_g1" if e == 60 else "sp")
    S30 = sites("m30")
    if far_sites(S30, "X")[0] != PILOT_FAR_X_B["Cl"] or far_sites(S30, "B")[0] != PILOT_FAR_X_B["Ca"]:
        raise S2Error("the farthest m30 X/B sites differ from section 7 (I175, Pb76)")
    for T, L in (("Cl", "X"), ("Ca", "B")):
        f = far_sites(S30, L)[0]
        _sp(G, label_of("s2spin", "m30", "D", T=T, j=f, k=0, leg="vac"), wid_of("m30", "D", T=T, j=f, n=0, leg="vac"),
            "sp_spin", sp_kind="sp_spin", dopant=T)
    for p in c46.PILOTS:
        S = sites(p)
        _sp(G, label_of("s2", p, "host"), wid_of(p, "host"), "sp_noise")
        for L in "BAX":
            for f in S[L]["far4"]:
                _sp(G, label_of("s2", p, "V", L=L, j=int(f)), wid_of(p, "V", L, int(f)), "sp_noise")
        for L in "BAX":
            for T in TOKENS_OF[L]:
                for f in S[L]["far4"]:
                    for leg in ("novac", "vac"):
                        _sp(G, label_of("s2", p, "D", T=T, j=int(f), k=0, leg=leg),
                            wid_of(p, "D", T=T, j=int(f), n=0, leg=leg), "sp_noise")
    _sp(G, SP_LABELS_FIXED["step0"][0], wid_of("m30", "V", "B", 136), "sp_step0")
    _sp(G, SP_LABELS_FIXED["step0"][1], wid_of("m30", "D", T="Sr", j=136, n=0, leg="vac"), "sp_step0")
    for T in c46.MULTI_START:
        jn, jf = c46.POSE_SITES[T]
        for j, near in ((jn, True), (jf, False)):
            _pose_sps(G, "m30", T, j, len(b42.sampled_names(T)), near=near, cat="sp_pose")
    for lab in Q0_ROWS:
        g = c46.LABEL_RE.fullmatch(lab)
        if g.group("vL"):
            cell = wid_of("m30", "V", g.group("vL"), int(g.group("vj")))
        else:
            cell = wid_of("m30", "D", T=g.group("tok"), j=int(g.group("j")), n=0, leg="vac")
        c46.check_label(lab)
        _sp(G, lab, cell, "sp_q0")
    for gt in ("G1", "N", "nrule", "pose"):                              # 'nrule', not 'n' (N-F15)
        G.add(f"gate:{gt}", "gate", "gate", [], gate=gt, cat="gate")
    return G


def _a2_jobs(G, labels, *, cat="a2"):
    for i, lab in enumerate(labels, 1):
        c46.check_label(lab)
        G.add("a2:" + lab, "a2", "a2", [], label=lab, order=i, cat=cat, **a1_of_a2(lab))
    # section 11 final-geometry checks (I-F1): one geometry-only job per relaxation, after the relaxation and its
    # partner (host_R for V+_R and D, V+_R for D+V) have ended
    for i, lab in enumerate(labels, 1):
        par = a2_parent(lab)
        par = par if par in labels else None
        G.add("a2v:" + lab, "a2v", "a2", ["a2:" + lab] + (["a2:" + par] if par else []), label=lab, parent=par,
              order=i, cat="a2_validate", **a1_of_a2(lab))


def c2_labels(state):
    g1 = state.get("G1") or {}
    return [l for l in C2_ORDER if not ("Ca136" in l and g1.get("Ca") is False)]


def graph_c2(state, sites=site_sets):
    G = Graph("c2", PHASES["c2"])
    G.add("check:upf", "check", "check", what="upf")
    G.add("check:nodescripts", "check", "check", what="nodescripts")             # N-F31 (round 4)
    labs = c2_labels(state)
    _a2_jobs(G, labs)
    # in-line gates (section 11): step-0 at k = 0 of relaxations 1 and 4, K2 at the end of 1, projection after 1-4,
    # K3 after 1-8; each applies at once (I-D3)
    G.add("gate:step0@1", "gate", "a2", ["k0:s2r_m30_VB136"], gate="step0", cat="gate", at="s2r_m30_VB136")
    G.add("gate:K2", "gate", "a2", ["a2:s2r_m30_VB136"], gate="K2", cat="gate")
    G.add("gate:step0@4", "gate", "a2", ["k0:s2r_m30_Sr136o0_vac"], gate="step0", cat="gate", at="s2r_m30_Sr136o0_vac")
    G.add("gate:projection@after4", "gate", "a2", ["a2:" + x for x in labs[:4]], gate="projection", point="after4", cat="gate")
    G.add("gate:K3", "gate", "a2", ["a2v:" + x for x in labs[:8]], gate="K3", cat="gate")   # after the checks (I-F1)
    return G


def c4_labels(state):
    cuts = cut_ids(state)
    g1 = state.get("G1") or {}
    m5 = m05_cal(state)
    regions = [("m30", "X", 138, ("Cl",)), ("m30", "A", 128, ("Cs", "GA")), ("m05", "B", m5["B"], ("Sr", "Ca")),
               ("m05", "X", m5["X"], ("Cl",)), ("m05", "A", m5["A"], ("Cs", "GA"))]
    out = []
    for h, L, j, toks in regions:
        keep = [T for T in toks if g1.get(T) is not False]                              # section 7, I-31
        cga, ccs = {"m05": (1, 2), "m30": (3, 4)}.get(h, (None, None))
        if L == "A" and cga in cuts:
            keep = [T for T in keep if T != "GA"]                                       # cut 1 (m05) / 3 (m30): GA
        if L == "A" and ccs in cuts:
            keep = []                                                                   # cut 2 / 4: Cs and the region
        if not keep:
            continue
        out += [label_of("s2r", h, "host", L=L, j=j), label_of("s2r", h, "V", L=L, j=j)]
        for T in toks:
            if T in keep:
                out += [label_of("s2r", h, "D", T=T, j=j, k=0, leg=leg) for leg in ("novac", "vac")]
    return out


def graph_c4(state, sites=site_sets):
    G = Graph("c4", PHASES["c4"])
    G.add("check:upf", "check", "check", what="upf")
    G.add("check:nodescripts", "check", "check", what="nodescripts")             # N-F31 (round 4)
    G.add("gate:projection@c4", "gate", "pre", [], gate="projection", point="c4", cat="gate")
    if 8 not in cut_ids(state):
        _a2_jobs(G, c4_labels(state))
    G.add("gate:c4_end", "gate", "gate", [], gate="c4_end", cat="gate")
    return G


def production_hosts(state):
    s0 = state.get("stage0") or {}
    if state.get("n") not in (8, 10):
        raise S2Error(f"no recorded n (8 or 10) from the n rule: n = {state.get('n')!r} (section 3, N-F24)")
    n = int(state["n"])
    if 5 in cut_ids(state):
        n = 8
    lst = s0.get(f"production_n{n}")
    if not lst or len(lst) != n:
        raise S2Error(f"no Stage-0 production list for n = {n}")
    return list(lst)


def c3_multi(state, T):
    cuts = cut_ids(state)
    return (state.get("pose") or {}).get(T) == "multi" and not (T == "Cs" and 6 in cuts) and not (T == "Cl" and 7 in cuts)


def graph_c3(state, sites=site_sets):
    G = Graph("c3", PHASES["c3"])
    G.add("check:upf", "check", "check", what="upf")
    G.add("check:nodescripts", "check", "check", what="nodescripts")             # N-F31 (round 4)
    G.add("check:mace", "check", "check", what="mace")
    G.add("gate:projection@c3", "gate", "pre", [], gate="projection", point="c3", cat="gate")
    g1 = state.get("G1") or {}
    hosts = production_hosts(state)
    toks_of = {L: tuple(T for T in TOKENS_OF[L] if g1.get(T) is not False) for L in "BAX"}
    multi = {T: c3_multi(state, T) for T in c46.MULTI_START}
    for h in hosts:
        S = sites(h)
        G.add("mace:" + wid_of(h, "host"), "mace", "mace", [], action="relax-host", member=h, work_id=wid_of(h, "host"),
              cell_kind="host",
              role="production", cat="mace_host", xkind="host")
        for L in "BAX":
            if not toks_of[L]:
                continue                                                               # I-31: no V+ for no dopant
            for j in production_sites(S, L):
                _mace_site(G, "c3", h, L, j, toks_of[L], role="production", cat_dopant="mace_dopant",
                           starts=lambda T, jj: _starts(T, multi.get(T, False)), prov=pbcl_provisional(state))
                for T in toks_of[L]:
                    if multi.get(T):
                        _distinct(G, h, T, j, _starts(T, True), "production")
    for h in hosts:
        S = sites(h)
        _sp(G, label_of("s2", h, "host"), wid_of(h, "host"), "sp")
        for L in "BAX":
            if toks_of[L]:
                for j in production_sites(S, L):
                    _sp(G, label_of("s2", h, "V", L=L, j=j), wid_of(h, "V", L, j), "sp")
        for L in "BAX":
            for T in toks_of[L]:
                for j in production_sites(S, L):
                    for leg in ("novac", "vac"):
                        _sp(G, label_of("s2", h, "D", T=T, j=j, k=0, leg=leg), wid_of(h, "D", T=T, j=j, n=0, leg=leg), "sp")
                    if multi.get(T):
                        for leg in ("novac", "vac"):
                            for k in range(1, len(b42.sampled_names(T))):
                                _sp(G, label_of("s2", h, "D", T=T, j=j, k=k, leg=leg), None, "sp_pose_extra",
                                    deps=[f"distinct:{h}_{T}{j}_{leg}"], src="distinct",
                                    slot={"distinct": f"distinct:{h}_{T}{j}_{leg}", "k": k, "member": h, "token": T,
                                          "site": j, "leg": leg})
    G.add("gate:c3_complete", "gate", "gate", [], gate="c3_complete", cat="gate")
    return G


GRAPHS = {"c1": graph_c1, "c2": graph_c2, "c3": graph_c3, "c4": graph_c4}


def graph(campaign, state, *, sites=site_sets):
    """The job graph of a campaign (interface spec 9.1), as a dict; geometry only."""
    return GRAPHS[campaign](state, sites).to_json()


# ---------------------------------------------------------------- counts (asserted against the plan)
def expected_counts(campaign, state):
    """The plan's counts (interface spec section 11), each adjustment listed; independent of the graph builders."""
    g1 = state.get("G1") or {}
    cuts = cut_ids(state)
    adj = []
    if campaign == "c1":
        e = {"mace_host": 2, "mace_V": 30, "mace_dopant_noise": 80, "mace_dopant_startset": 20,
             "mace_pose_extra": 2 * (2 * 6) + 2 * (2 * 2),           # Cs 6 displaced, Cl 2 shifted; 2 sites, 2 legs
             "sp_g1": 5, "sp_spin": 2, "sp_noise": 2 * (1 + 12 + 40), "sp_step0": 2,
             "sp_pose": 4 + 2 * 2 * 6 + 2 * 2 * 2, "sp_q0": 10, "pw_smoke": 4, "pw_tp": 4, "gate": 5}
        if state.get("a2_layout") not in (None, "48"):
            e["pw_smoke2"] = 2; adj.append("rst repeated at the chosen A2 layout (X-4)")
        assert e["sp_pose"] <= 40 and e["mace_pose_extra"] <= 32
        return e, adj
    if campaign == "c2":
        n = 10 - (2 if g1.get("Ca") is False else 0)
        if n < 10:
            adj.append("Ca failed G1: Ca136 D, D+V not run")
        return {"a2": n, "a2_validate": n, "gate": 5}, adj
    if campaign == "c4":
        if 8 in cuts:
            return {"gate": 2}, ["cut 8: C4 not run"]
        n = 26
        for c, k, why in ((1, 2, "GA m05"), (2, 4, "Cs and A region m05"), (3, 2, "GA m30"), (4, 4, "Cs and A region m30")):
            if c in cuts:
                n -= k; adj.append(f"cut {c}: {why}")
        if g1.get("Cl") is False:
            n -= 8; adj.append("Cl failed G1: m30 and m05 X regions")
        if g1.get("Ca") is False:
            n -= 2; adj.append("Ca failed G1: Ca124 D, D+V")
        return {"a2": n, "a2_validate": n, "gate": 2}, adj
    hosts = production_hosts(state)
    nh = len(hosts)
    per = {"mace_host": 1, "mace_V": 19, "mace_dopant": 56, "sp": 76}
    if g1.get("Ca") is False:
        per["mace_dopant"] -= 8; per["sp"] -= 8; adj.append("Ca failed G1: -8 relaxations, -8 single points per host (N-D9)")
    if g1.get("Cl") is False:
        per["mace_dopant"] -= 20; per["mace_V"] -= 10; per["sp"] -= 30
        adj.append("Cl failed G1: -20 dopant and -10 V+ relaxations, -30 single points per host")
    extra_m = extra_s = 0
    if c3_multi(state, "Cs"):
        extra_m += 5 * 2 * 6; extra_s += 5 * 2 * 6; adj.append("Cs multi-pose: 6 more starts per A site and leg")
    if c3_multi(state, "Cl") and g1.get("Cl") is not False:
        extra_m += 10 * 2 * 2; extra_s += 10 * 2 * 2; adj.append("Cl multi-pose: 2 more starts per X site and leg")
    assert extra_s <= 100
    e = {k: v * nh for k, v in per.items()}
    if extra_m:
        e["mace_pose_extra"], e["sp_pose_extra"] = extra_m * nh, extra_s * nh
    e["gate"] = 2
    return e, adj


def assert_counts(g, state):
    """S2Error on any difference between the graph's counts and the plan's (interface spec 9.1)."""
    exp, adj = expected_counts(g["campaign"], state)
    got = {k: v for k, v in g["counts"].items()}
    if got != exp:
        raise S2Error(f"{g['campaign']} counts differ from the plan: graph {got}, plan {exp} (adjustments {adj})")
    return exp, adj


def synthetic_state(**over):
    """A state with the plan's lists (section 3; Stage-0 record absent) and every gate passed: for graph checks."""
    s = {"schema": "s2-state-1", "commit": None,
         "stage0": {"production_n8": ["m06", "m02", "m16", "m12", "m32", "m26", "m22", "m23"],
                    "reserves_n8": ["m33", "m13"],
                    "production_n10": ["m06", "m02", "m16", "m12", "m32", "m26", "m22", "m23", "m33", "m13"],
                    "reserves_n10": ["m17", "m03"], "m05_cal": {"B": 124, "A": 28, "X": 49},
                    "pbcl": {"decision": "confirmed_2.837"}, "source": "plan section 3 (synthetic)"},
         "a2_layout": "48", "G1": {"Cl": True, "Ca": True}, "gateN": {t: True for t in c46.TOKENS}, "sr_stop": False,
         "n": 8, "pose": {"Cs": "default", "Cl": "default"}, "step0": {"attempts": 1, "outcome": "pass"},
         "K2": "pass", "K3": "pass", "cuts": [], "campaigns": {}}
    s.update(over)
    return s


# ---------------------------------------------------------------- spot URL (X-5)
def spot_url(checkout=CHECKOUT, root=NODE_ROOT):
    """The metadata endpoint of the spot notice, read at run time: the node-local file /data/setup/s2_spot_url if
    present, else the SPOT_URL= line of the committed node_step7.sh in the checkout. No address is written here."""
    f = Node(root).spot_url_file
    if os.path.exists(f):
        url = open(f).read().strip().splitlines()[0].strip()
    else:
        g = re.search(r"^SPOT_URL=(\S+)\s*$", open(os.path.join(checkout, SPOT_HELPER)).read(), re.M)
        if not g:
            raise S2Error(f"no SPOT_URL line in {SPOT_HELPER}")
        url = g.group(1)
    if not (url.startswith("http://") and url.endswith("/termination-time")):
        raise S2Error("the spot URL must start with http:// and end with /termination-time: no spot watch, no start")
    return url


def poller_main(url, d, boot, ppid, poll, keep_alive=None, done=None):
    """Spot poller (child of the runner): polls the metadata endpoint every `poll` s; a termination notice (HTTP 200)
    is written at once, fsynced, to notice.<boot>; a heartbeat with the time of the last good poll (200 or 404)
    goes to heartbeat.<boot> at every good poll (round-4 R4-C1-1: with a 60-s cadence the file lagged the last good
    poll by up to a minute, so an outage of 4-5 min looked like one of 5 min, N-F18). Exits when its parent is gone (as
    node_step7's poller). If the runner died
    without ending its campaign (SIGKILL, OOM: no CAMPAIGN_DONE), the poller removes the KEEP_ALIVE the runner wrote
    before it started (not a newer one), so the idle self-stop applies once the orphaned jobs end (round-2 F1)."""
    import urllib.error, urllib.request
    os.makedirs(d, exist_ok=True)
    notice, hbf = os.path.join(d, f"notice.{boot}"), os.path.join(d, f"heartbeat.{boot}")
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    last_err = 0.0; ok = err = 0
    print(f"{utc()} poller start, boot {boot[:8]}", flush=True)
    t_start = time.time()
    while os.getppid() == ppid:
        t = time.time()
        try:
            try:
                with op.open(url, timeout=3) as r:
                    code, body = r.status, r.read(300).decode("ascii", "replace").strip()
            except urllib.error.HTTPError as e:
                code, body = e.code, ""
            except Exception as e:                                          # noqa: BLE001
                code, body = None, f"{type(e).__name__}"
            if code in (200, 404):
                ok += 1
                if code == 200 and not os.path.exists(notice):
                    write_text(f"{utc(t)} {t:.0f} {' '.join(body.split())[:120]}\n", notice)
                    print(f"{utc(t)} spot termination notice", flush=True)
                write_text(f"{t:.0f} {utc(t)} ok={ok} err={err}\n", hbf)        # every good poll (R4-C1-1)
            else:
                err += 1
                if t - last_err >= 600:
                    print(f"{utc(t)} metadata poll failed ({code}): {body[:80]}", flush=True); last_err = t
        except Exception as e:                                              # noqa: BLE001 (a full disk: keep polling)
            print(f"{utc(t)} poller error {type(e).__name__}", flush=True)
        time.sleep(poll)
    try:
        if keep_alive and done and not os.path.exists(done) and os.path.exists(keep_alive) and \
                os.path.getmtime(keep_alive) <= t_start + 1.0:
            os.remove(keep_alive)
            print(f"{utc()} the runner ended without CAMPAIGN_DONE: KEEP_ALIVE removed (round-2 F1)", flush=True)
    except OSError as e:
        print(f"{utc()} KEEP_ALIVE not removed ({type(e).__name__})", flush=True)
    return 0


# ---------------------------------------------------------------- backends
# the child wrapper: runs the command with its output in a log, then records its exit status and time (synced),
# so an end is classified from evidence after a runner restart. The command runs as 'sh -c ... exec', which writes
# its own pid (the pid the command keeps after exec) to <rc>.pid first: the process an OOM kill would name, not the
# wrapper's (round-2 F4)
WRAP = ('log=${1}; rcf=${2}; shift 2; '
        'S2_RCF="$rcf" sh -c \'echo $$ > "$S2_RCF.pid.tmp" && mv -f "$S2_RCF.pid.tmp" "$S2_RCF.pid"; exec "$@"\' '
        's2child "$@" > "$log" 2>&1 < /dev/null; '
        'rc=$?; echo "$rc $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$rcf.tmp" && mv -f "$rcf.tmp" "$rcf"; sync; exit $rc')


def child_pid(rcf):
    """The pid the wrapped command ran under (<rc>.pid written by WRAP), or None."""
    try:
        return int(open(rcf + ".pid").read().split()[0])
    except (OSError, ValueError, IndexError):
        return None


class NodeBackend:
    """Everything the runner does to the outside world on the node: process spawning, boot and journal evidence,
    git state, scripts/46 and 49 invocations, the UPF and foundation checks."""
    tick, heartbeat_s, notice_hold_s, counts_every_s, poll_s = TICK_S, HEARTBEAT_S, NOTICE_HOLD_S, COUNTS_EVERY_S, SPOT_POLL_S
    stall_out_s, mace_wall_s = STALL_OUT_S, MACE_WALL_S
    spot_first_s, spot_stale_s = SPOT_FIRST_S, SPOT_STALE_S
    calc = "mace"
    mock = False

    def __init__(self, root=NODE_ROOT):
        self.node = Node(root)
        self.python = sys.executable

    def boot_id(self):
        return open("/proc/sys/kernel/random/boot_id").read().strip()

    def btime(self):
        for x in open("/proc/stat"):
            if x.startswith("btime"):
                return float(x.split()[1])
        return None

    def _jctl(self, args):
        try:
            p = subprocess.run(["sudo", "-n", "journalctl"] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True, timeout=180)
        except Exception:                                                   # noqa: BLE001
            return None
        return p.stdout.splitlines() if p.returncode == 0 and p.stdout.strip() else None

    def journal_end(self, boot):
        """Epoch of the last entry of that boot's journal, or None if it cannot be read."""
        lines = self._jctl(["-b", boot.replace("-", ""), "-n", "1", "-q", "--no-pager", "-o", "short-unix"])
        for x in reversed(lines or []):
            g = re.match(r"(\d+\.\d+)\s", x)
            if g:
                return float(g.group(1))
        return None

    def oom(self, boot, pid, task=None, since=None, pids=None, exclude=None):
        """True iff that boot's kernel journal has an OOM kill of pid (the wrapped command's own pid, F4), of one of
        pids (the recorded process tree of an A2 part, N-F23), or of a process named task (the pw.x ranks of an A2
        part) dated at or after since whose pid is not in exclude (the other copy's tree); None if the journal cannot
        be read. Kernel lines: 'Out of memory: Killed process <pid> (<comm>) ...', 'oom-kill:...,task=<comm>,pid=<pid>,'."""
        lines = self._jctl(["-k", "-b", boot.replace("-", ""), "-q", "--no-pager", "-o", "short-unix"])
        if lines is None or (pid is None and task is None and not pids):
            return None
        pids, exclude = {int(x) for x in (pids or ())}, {int(x) for x in (exclude or ())}
        for x in lines:
            m = re.match(r"\s*(\d+(?:\.\d+)?)\s", x)
            if since is not None and m and float(m.group(1)) < float(since):
                continue
            v = re.search(r"Killed process (\d+)\b|oom-kill:.*\bpid=(\d+)\b", x)
            victim = int(v.group(1) or v.group(2)) if v else None
            if pid is not None and victim == int(pid):
                return True
            if pids and victim in pids:
                return True
            if task is not None and victim not in exclude and \
                    re.search(rf"(oom-kill:.*\btask={re.escape(task)}(,|\s|$)|Killed process \d+ "
                              rf"\({re.escape(task)}\))", x):
                return True
        return False

    def proc_tree(self, pid):
        """{pid: command name} of the process tree rooted at pid (node /proc; N-F23, N-F34); {} if it cannot be read."""
        try:
            par, comm = {}, {}
            for e in os.listdir("/proc"):
                if e.isdigit():
                    try:
                        s = open(f"/proc/{e}/stat").read()
                        par[int(e)] = int(s.rsplit(")", 1)[1].split()[1])
                        comm[int(e)] = s[s.index("(") + 1:s.rindex(")")]
                    except (OSError, ValueError, IndexError):
                        pass
        except OSError:
            return {}
        out, todo = set(), [int(pid)]
        while todo:
            p = todo.pop()
            if p in out:
                continue
            out.add(p)
            todo += [c for c, pp in par.items() if pp == p]
        return {p: comm.get(p, "?") for p in out} if len(out) > 1 or int(pid) in par else {}

    def descendants(self, pid):
        """The pids of the process tree rooted at pid (node /proc; N-F23); an empty set if it cannot be read."""
        return set(self.proc_tree(pid))

    def cpus_allowed(self, pid):
        """The CPUs a process may run on (/proc/<pid>/status Cpus_allowed_list), or None (N-F30)."""
        try:
            for x in open(f"/proc/{int(pid)}/status"):
                if x.startswith("Cpus_allowed_list:"):
                    return parse_cpulist(x.split(":", 1)[1])
        except (OSError, ValueError):
            return None
        return None

    def core_sets(self):
        """N-F30: two disjoint CPU lists, the first and the second half of the physical cores (lscpu -p=CPU,CORE), for
        two concurrent 32-rank copies; a STOP if lscpu cannot be read (two copies cannot then be confined)."""
        try:
            r = subprocess.run(["lscpu", "-p=CPU,CORE"], capture_output=True, text=True, timeout=60)
            pairs = [tuple(int(v) for v in x.split(",")[:2]) for x in r.stdout.splitlines()
                     if x.strip() and not x.startswith("#")]
        except (OSError, subprocess.SubprocessError, ValueError) as e:
            raise Stop(f"lscpu failed ({type(e).__name__}): two concurrent copies cannot be given disjoint cores (N-F30)")
        cores = sorted({c for _, c in pairs})
        if r.returncode != 0 or len(cores) < 2:
            raise Stop(f"lscpu gave {len(cores)} physical cores (exit {r.returncode}): no two disjoint core sets (N-F30)")
        h = len(cores) // 2
        return [cpulist(sorted(cpu for cpu, c in pairs if c in set(cores[:h]))),
                cpulist(sorted(cpu for cpu, c in pairs if c in set(cores[h:2 * h])))]

    def git_state(self):
        """N-F32 (round-4 R4-C1-3, D-S0-8): HEAD and cleanliness of the checkout; any git failure (no repository, a
        copy without .git, git's ownership refusal, no git) is a STOP, never an empty commit read as clean."""
        co = self.node.checkout
        try:
            h = subprocess.run(["git", "-C", co, "rev-parse", "--verify", "HEAD"], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, universal_newlines=True, timeout=120)
            s = subprocess.run(["git", "-C", co, "status", "--porcelain"], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, universal_newlines=True, timeout=600)
        except (OSError, subprocess.SubprocessError) as e:
            raise Stop(f"git failed in the checkout ({type(e).__name__}): nothing started (STAGE0 section 8 item 1, N-F32)")
        head = h.stdout.strip()
        if h.returncode != 0 or s.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", head):
            raise Stop(f"git failed in the checkout (rev-parse exit {h.returncode}, status exit {s.returncode}, HEAD "
                       f"{head[:12]!r}): nothing started; the checkout must be a clean git checkout of the S2 commit "
                       f"(STAGE0 section 8 item 1, N-F32)")
        return {"head": head, "clean": s.stdout.strip() == ""}

    def spawn(self, cmd, *, cwd, log, rc, env=None, pass_fds=()):
        e = dict(os.environ); e.update(env or {})
        return subprocess.Popen(["bash", "-c", WRAP, "s2wrap", log, rc] + [str(x) for x in cmd], cwd=cwd, env=e,
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                pass_fds=tuple(pass_fds))

    def run46(self, action, jobfile, log):
        with open(log, "a") as fh:
            return subprocess.run([self.python, os.path.join(HERE, "46_s2_cells.py"), action, "--job", jobfile],
                                  cwd=self.node.checkout, stdout=fh, stderr=subprocess.STDOUT, timeout=7200).returncode

    def cmd46(self, action, jobfile):
        return [self.python, os.path.join(HERE, "46_s2_cells.py"), action, "--job", jobfile]

    def gate(self, gate, campaign, log, inputs, attempt):
        with open(log, "a") as fh:
            return subprocess.run([self.python, os.path.join(HERE, "49_s2_gates.py"), "run", "--gate", gate,
                                   "--root", self.node.root, "--campaign", campaign, "--inputs", inputs,
                                   "--attempt", str(attempt)], cwd=self.node.checkout,
                                  stdout=fh, stderr=subprocess.STDOUT, timeout=7200).returncode

    def upf_check(self, campaign, reference):
        return q47.upf_check(self.node.pseudo, reference=reference)

    def foundation_check(self):
        """Section 5 / STAGE0 section 8 item 3 (round-4 R4-C1-6, N-F35): the foundation file's sha256 (scripts/46
        foundation_check), then scripts/46 load_mace in a child process (the runner never imports mace): mace-torch
        0.3.16, float64 parameters on cpu, the resolved file, Z coverage and torch threads are asserted before the first
        MACE job; no structure is passed to the calculator and nothing is evaluated. A failure is a STOP before the
        smoke tests and costs no MACE attempt."""
        rec = c46.foundation_check()
        if not rec.get("passed"):
            return rec
        rec["load"] = self.mace_load()
        rec["passed"] = bool(rec["load"].get("ok"))
        return rec

    MACE_LOAD_CODE = ("import importlib.util, json, sys\n"
                      "s = importlib.util.spec_from_file_location('c46', sys.argv[1])\n"
                      "m = importlib.util.module_from_spec(s); s.loader.exec_module(m)\n"
                      "calc, info = m.load_mace(int(sys.argv[2]))\n"
                      "print('S2-MACE-LOAD ' + json.dumps(info, sort_keys=True, default=str), flush=True)\n")

    def mace_load(self, log=None):
        """N-F35: scripts/46 load_mace(THREADS) in a child process; its output goes to a log (it may name paths), the
        record keeps the exit status, the exception name and the path-free info dict of load_mace."""
        env = dict(os.environ, OMP_NUM_THREADS=str(c46.THREADS), MKL_NUM_THREADS=str(c46.THREADS), OPENBLAS_NUM_THREADS="1")
        try:
            p = subprocess.run([self.python, "-c", self.MACE_LOAD_CODE, os.path.join(HERE, "46_s2_cells.py"),
                                str(c46.THREADS)], cwd=self.node.checkout, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True, timeout=1800, env=env)
        except (OSError, subprocess.SubprocessError) as e:
            return {"ok": False, "exit": None, "error": type(e).__name__}
        if log:
            try:
                write_text(p.stdout + p.stderr, log)
            except OSError:
                pass
        info = None
        for x in p.stdout.splitlines():
            if x.startswith("S2-MACE-LOAD "):
                try:
                    info = json.loads(x[len("S2-MACE-LOAD "):])
                except ValueError:
                    info = None
        err = None
        if p.returncode != 0:
            g = re.findall(r"^(?:\w+\.)*(\w+(?:Error|Exception))\b", p.stderr, re.M)    # 'c46.S2Error' too (R5 M-1)
            err = g[-1] if g else "exit without a traceback"
        keep = ("dtype", "device", "threads", "atomic_numbers_covered", "z_required_ok", "versions", "sha256", "file")
        return {"ok": p.returncode == 0 and info is not None, "exit": p.returncode, "error": err,
                "info": {k: info.get(k) for k in keep} if info else None}

    def nodescripts(self):
        """N-F31: the node-only scripts every pw.x run depends on, by name: the single-point queue and chain (they must
        equal the checkout's ehpc/node copies), run_qe.sh and the QE profile (recorded in C1, compared in C2-C4), and
        the committed launcher s2_run_qe.sh used from the checkout."""
        n = self.node
        return {"run_qe.sh": n.run_qe, "qe.sh": n.qe_profile, "qe_queue.sh": n.queue, "chain.sh": n.chain,
                "s2_run_qe.sh": n.s2_run_qe}

    def node_script_expected(self, name):
        """The bytes a node copy of a committed script must have (the self-test rewrites its paths, _node_scripts)."""
        return open(os.path.join(self.node.checkout, "ehpc", "node", name), "rb").read()

    def nodescripts_check(self, campaign, reference):
        """N-F31 (round-4 R4-C1-2): sha256 of every script of nodescripts(); the queue, the chain and the launcher must
        equal the checkout's ehpc/node copies byte for byte; in C2-C4 every hash must equal the C1 record. Names only,
        no path, are recorded."""
        files, problems = {}, []
        for name, path in self.nodescripts().items():
            try:
                raw = open(path, "rb").read()
            except OSError as e:
                files[name] = None; problems.append(f"{name} unreadable ({type(e).__name__})"); continue
            files[name] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
            if name in ("qe_queue.sh", "chain.sh", "s2_run_qe.sh"):
                try:
                    exp = self.node_script_expected(name)
                except OSError:
                    exp = None
                files[name]["equal_to_checkout"] = raw == exp
                if raw != exp:
                    problems.append(f"{name} differs from the checkout's ehpc/node/{name}")
        if reference is not None:
            ref = reference.get("files") or {}
            for name, v in files.items():
                if v is None or (ref.get(name) or {}).get("sha256") != v["sha256"]:
                    problems.append(f"{name} changed since the C1 record")
        return {"schema": "s2-nodescripts-1", "campaign": campaign, "files": files,
                "compared_with_c1": reference is not None, "problems": problems, "passed": not problems}

    def spot_url(self):
        return spot_url(self.node.checkout, self.node.root)

    def graph(self, campaign, state):
        return graph(campaign, state)

    def foreign_pw(self, own):
        """True iff a pw.x process is alive that does not descend from one of the runner's own children (N-6)."""
        try:
            r = subprocess.run(["pgrep", "-x", "pw.x"], capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError) as e:
            raise Stop(f"cannot list pw.x processes ({type(e).__name__}): nothing outside the queue starts (N-6)")
        if r.returncode not in (0, 1):
            raise Stop(f"pgrep failed (exit {r.returncode}): nothing outside the queue starts (N-6)")
        for pid in (int(x) for x in r.stdout.split()):
            p, ok = pid, False
            for _ in range(64):                                     # walk up the parents
                if p in own:
                    ok = True; break
                try:
                    p = int(open(f"/proc/{p}/stat").read().rsplit(")", 1)[1].split()[1])
                except (OSError, ValueError, IndexError):
                    break
                if p <= 1:
                    break
            if not ok:
                return True
        return False

    def alive(self, pid):
        try:
            os.kill(int(pid), 0)
        except (OSError, TypeError, ValueError):
            return False
        try:                                                               # a zombie is not alive
            st = open(f"/proc/{int(pid)}/stat").read().split(")")[-1].split()[0]
            return st != "Z"
        except OSError:
            return True

    def sleep(self, s):
        time.sleep(s)


class Stop(Exception):
    """A fail-closed stop for a human: nothing new starts, CAMPAIGN_STOPPED holds the reason (N-D4)."""


def public_text(text, limit=600):
    """A copy of text that passes the JSON hygiene rules of scripts/46: every match of a rule (local or temporary
    path, address, host name, id, currency, dollar sign) replaced by '<redacted>'. Used for the stop reason in
    campaign.json, so that a reason quoting a path never makes the STOP itself fail (round-2 M2); the raw text stays
    in campaign.log and CAMPAIGN_STOPPED on the node."""
    s = str(text)[:limit]
    pats = [rx for _, rx in list(getattr(c46, "_HYGIENE", None) or []) + list(getattr(c46, "_HYGIENE_JSON", None) or [])] \
        or [rx for _, rx in _hyg_patterns()]
    for _ in range(3):
        for rx in pats:
            s = rx.sub("<redacted>", s)
        s = s.replace("$", "<redacted>")
        try:
            if not c46.hygiene_violations(s):
                return s
        except Exception:                                                   # noqa: BLE001
            break
    return "<the reason broke the hygiene rules: see campaign.log>"


def _warn(msg):
    """Last-resort report on stderr (driver.out) when a log or record write fails during a stop or an exit."""
    try:
        sys.stderr.write(f"[{utc()}] WARN: {msg}\n"); sys.stderr.flush()
    except Exception:                                                       # noqa: BLE001
        pass


# ---------------------------------------------------------------- ledger (section 16; interface spec 9.3)
def ledger(root=NODE_ROOT, now=None, backend=None):
    be = backend or NodeBackend(root)
    d = Node(root).ledger
    now = time.time() if now is None else now
    try:
        cur = be.boot_id()
    except OSError:                                   # not on the node (laptop status of a pulled tree): no current boot
        cur = None
    boots, problems = {}, []
    for f in glob.glob(os.path.join(d, "boot.*.json")):
        r = read_json(f) or {}
        if r.get("boot_id"):
            boots[r["boot_id"]] = dict(r)
    for f in glob.glob(os.path.join(d, "heartbeat.*")):
        b = os.path.basename(f).split(".", 1)[1]
        try:
            boots.setdefault(b, {"boot_id": b})["last_heartbeat"] = float(open(f).read().split()[0])
        except (ValueError, IndexError):
            problems.append(f"unreadable heartbeat of boot {b[:8]}")
    rows = []
    manual = read_json(os.path.join(d, "manual.json"), []) or []
    # an operator entry with the boot id of a counted boot gives that boot's stop time (the console's record); any
    # other entry is a boot of its own (interface spec 9.3)
    override = {e.get("boot_id"): e for e in manual if isinstance(e, dict) and e.get("boot_id") in boots
                and e.get("end") is not None}
    for b, r in sorted(boots.items(), key=lambda kv: kv[1].get("btime") or 0):
        bt, hb = r.get("btime"), r.get("last_heartbeat")
        if bt is None or (hb is None and b != cur):
            problems.append(f"boot {b[:8]}: no btime or no heartbeat")
            rows.append({**r, "hours": None}); continue
        je = None if b == cur else be.journal_end(b)
        assumed = None
        if b == cur:
            end = now
        elif b in override:
            try:
                end = max(hb + 60.0, float(override[b]["end"])); assumed = "operator stop time (manual.json)"
            except (TypeError, ValueError):
                problems.append(f"boot {b[:8]}: manual end unreadable"); rows.append({**r, "hours": None}); continue
        elif je is not None:
            end = max(hb + 60.0, je)
        else:
            end = hb + 60.0 + IDLE_STOP_S + IDLE_MARGIN_S          # I-F8 (review F8): the idle self-stop bound
            assumed = "journal unreadable: last heartbeat + 60 s + 60 min idle self-stop + 15 min"
        rows.append({"boot_id": b, "btime": bt, "btime_utc": utc(bt), "first_heartbeat": r.get("first_heartbeat"),
                     "last_heartbeat": hb, "journal_end": je, "end_used": end, "end_used_utc": utc(end),
                     "end_assumed": assumed, "hours": (end - bt) / 3600.0, "campaigns": r.get("campaigns", []),
                     "current": b == cur})
    for e in manual:
        if isinstance(e, dict) and e.get("boot_id") in override:
            continue
        try:
            bt, en = float(e["btime"]), float(e["end"])
            rows.append({"boot_id": e.get("boot_id"), "btime": bt, "end_used": en, "hours": (en - bt) / 3600.0,
                         "manual": True, "note": e.get("note")})
        except (KeyError, TypeError, ValueError):
            problems.append(f"manual entry without btime and end: {str(e)[:60]}")
    H = sum(r["hours"] for r in rows if r.get("hours") is not None)
    return {"schema": "s2-ledger-1", "boots": rows, "H_spent_h": H, "complete": not problems, "problems": problems,
            "now_utc": utc(now)}


def h_spent(root=NODE_ROOT, now=None, backend=None):
    return ledger(root, now, backend)["H_spent_h"]


# ---------------------------------------------------------------- the runner
def _is_terminal(st):
    return st in TERMINAL


class Runner:
    """One campaign on the node (interface spec 9.2). Every decision about a job is recomputed from its files."""

    def __init__(self, campaign, root=NODE_ROOT, backend=None):
        self.c = campaign
        self.be = backend or NodeBackend(root)
        self.node = self.be.node
        self.L = c46.Layout(kind="node", root=self.node.root)
        self.cdir = self.L.campaign_dir(campaign)
        self.procs, self.walls, self.k0, self.last_counts, self.cache = {}, {}, {}, {}, {}
        self.stopping, self.term, self.capped, self.hold_until, self.notice_done = False, False, None, 0.0, False
        self.shutdown, self.ka_written, self.t_start = False, False, time.time()
        self.state, self.G, self.gkey, self.lockfd, self.poller, self.last_hb, self.reads_seen = None, None, None, None, None, 0.0, set()
        self.chainfd, self.chain_wait_logged = None, False
        # round 3: STOPs held until the free jobs of the phase have run (N-F20); whether CAMPAIGN_STOPPED was written
        # (N-F21); the poller's start (N-F18); a relaunch after a STOP (N-F17)
        self.pending_stop, self.stop_written, self.poller_t0, self.was_stopped = [], False, None, False
        self.held_labels, self.slots_cache = {}, None                       # round 4: N-F36 (held STOP -> A2 label); N-F30
        self.resolve_wait, self.tree_full = set(), set()                    # round 4: log-once keys; N-F34
        self.poller_renewals = []                                           # round 6: R6-C1-2 (N-F18)

    # ---- logging and records
    def log(self, msg):
        line = f"[{utc()}] {msg}"
        os.makedirs(self.cdir, exist_ok=True)
        with open(os.path.join(self.cdir, "campaign.log"), "a") as fh:
            fh.write(line + "\n")
        print(line, flush=True)

    def read_out(self, what_, label_, mode_, fn_, *a, **kw):
        """Every QE-output read of the runner goes through here and is listed (N-D7, blinding of section 17). The
        parser's own keywords (label, md5_extra, n_el, ...) pass through kw."""
        if mode_ not in ("status", "counts", "end_rule", "final_geom"):
            raise S2Error(f"the runner may not read {label_} in mode {mode_}")
        if mode_ == "final_geom" and not str(label_).startswith("s2r_"):
            raise S2Error(f"final_geom is read only for A2 relaxations (section 11 checks), not {label_}")
        key = (what_, label_, mode_)
        if key not in self.reads_seen:
            self.reads_seen.add(key)
            append_jsonl(os.path.join(self.cdir, "runner_reads.jsonl"), {"t": utc(), "what": what_, "label": label_,
                                                                         "mode": mode_})
        if "47_s2_qe.py" not in MOCKED and fn_ in (q47.sp_status, q47.parse_relax, q47.parse_counts):
            kw.setdefault("md5_extra", self.md5_extra())                      # N-B9 (round-2 R2-QE-3)
        return fn_(*a, **kw)

    def md5_extra(self):
        """The C1-recorded MD5 of the Cl and Ca files (scripts/47 upf_md5_extra), once the C1 UPF check has passed;
        None before (the S1 identities are checked from the start). N-B9, round-2 R2-QE-3."""
        if getattr(self, "_md5x", None) is None:
            rec = read_json(os.path.join(self.node.c("c1"), "upf_check.json"))
            if not (rec and rec.get("passed")):     # round-6 R6-C1-1: after a commit change, until check:upf passes
                old = sorted(glob.glob(os.path.join(self.node.c("c1"), "discarded", "commit_*", "upf_check.json")))
                rec = next((r for r in map(read_json, reversed(old)) if r and r.get("passed")), rec)
            if rec and rec.get("passed"):
                try:
                    self._md5x = q47.upf_md5_extra(rec)
                except (KeyError, TypeError, S2Error) as e:
                    raise Stop(f"the C1 UPF record has no MD5 for Cl and Ca ({type(e).__name__}; N-B9)")
        return getattr(self, "_md5x", None)

    def meta_nel(self, d, label):
        """The electron count of a pw.x input from its meta record (scripts/47 write_input), or None."""
        m = read_json(os.path.join(d, f"{label}.meta.json")) or {}
        return (m.get("electrons") or {}).get("n_el")

    def save_state(self):
        write_json(self.state, self.node.state)

    def set_campaign(self, status, **kw):
        p = os.path.join(self.cdir, "campaign.json")
        r = read_json(p) or {"schema": "s2-campaign-1", "campaign": self.c, "started": utc(), "boots": []}
        for k, v in (("schema", "s2-campaign-1"), ("campaign", self.c), ("started", utc()), ("boots", [])):
            r.setdefault(k, v)                                              # a file mark_phase wrote first
        if self.boot not in r["boots"]:
            r["boots"].append(self.boot)
        r.update({"status": status, "updated": utc(), "commit": self.state.get("commit") if self.state else None,
                  "phases": r.get("phases", {}),
                  "mocked": list(MOCKED), "notes": sorted(NOTES), **kw})
        if self.state is not None:
            # round-4 R4-C1-6: the commit this campaign started at, and every later commit change (NODE_FIX, STEP0_FIX)
            if r.get("start_commit") is None:
                r["start_commit"] = r.get("commit")
            r["commit_history"] = list(self.state.get("commit_history") or [])
        c46.dump_public(r, p)
        if self.state is not None:
            self.state.setdefault("campaigns", {})[self.c] = status
            self.save_state()

    # ---- lock, keep-alive, poller, heartbeat
    def take_lock(self):
        os.makedirs(self.node.work, exist_ok=True)
        fd = os.environ.get("S2_LOCK_FD")
        if fd is not None:                                    # ehpc/node/s2_campaign.sh took it on fd 8
            self.lockfd = int(fd)
        else:
            self.lockfd = os.open(self.node.lock, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            fcntl.flock(self.lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise SystemExit(f"another S2 runner, or a process it started, holds {os.path.basename(self.node.lock)}")
        os.set_inheritable(self.lockfd, True)

    def chain_lock_ok(self):
        """N-6 (review-2 F6): pw.x runs outside the queue (smoke tests, throughput row, A2 parts) only while this runner
        holds the global chain lock of ehpc/node/chain.sh, so no queue runs beside them, and only when no pw.x that
        this runner did not start is alive. The lock is passed to every such child, and released when none runs."""
        if self.chainfd is None:
            fd = os.open(self.node.chain_lock, os.O_WRONLY | os.O_CREAT, 0o644)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                os.close(fd)
                if not self.chain_wait_logged:
                    self.log("the global chain lock is held (a QE queue runs): pw.x outside the queue waits (N-6)")
                    self.chain_wait_logged = True
                return False
            self.chainfd = fd
            os.set_inheritable(fd, True)
            self.chain_wait_logged = False
        own = {h["p"].pid for h in self.procs.values() if h["kind"] in ("pw", "a2") and h["p"].poll() is None}
        if self.be.foreign_pw(own):
            if not self.chain_wait_logged:
                self.log("a pw.x not started by this runner is alive: pw.x outside the queue waits (N-6)")
                self.chain_wait_logged = True
            return False
        return True

    def chain_lock_release(self):
        if self.chainfd is not None and not any(h["kind"] in ("pw", "a2") and h["p"].poll() is None
                                                for h in self.procs.values()):
            try:
                fcntl.flock(self.chainfd, fcntl.LOCK_UN)
            finally:
                os.close(self.chainfd)
                self.chainfd = None

    def start_poller(self):
        url = self.be.spot_url()
        if self.poller_t0 is None:
            self.poller_t0 = time.time()
        os.makedirs(self.node.spot, exist_ok=True)
        lf = open(os.path.join(self.node.spot, "poller.log"), "a")
        self.poller = subprocess.Popen([self.be.python, os.path.abspath(__file__), "poller", "--url", url, "--dir",
                                        self.node.spot, "--boot", self.boot, "--ppid", str(os.getpid()), "--poll",
                                        str(self.be.poll_s), "--keep-alive", self.node.keep_alive, "--done",
                                        os.path.join(self.cdir, "CAMPAIGN_DONE"), "--tag", "s2-spot-poller"],
                                       stdout=lf, stderr=lf,
                                       stdin=subprocess.DEVNULL)

    def spot_hb_time(self):
        """Time of the poller's last good poll (spot/heartbeat.<boot>), or None."""
        try:
            return float(open(os.path.join(self.node.spot, f"heartbeat.{self.boot}")).read().split()[0])
        except (OSError, ValueError, IndexError):
            return None

    def spot_check(self):
        """N-F18 (round-3 R3-C1-7, D-S0-8): True once the poller has had a good poll (200 or 404) since this runner
        started it; a STOP when there is none within spot_first_s of its start, or when the last good poll is older
        than spot_stale_s. Without a poller (the scheduler's unit tests) there is nothing to check."""
        if self.poller_t0 is None:
            return True
        t, now = self.spot_hb_time(), time.time()
        if t is None or t < self.poller_t0 - 1.0:
            if now - self.poller_t0 > self.be.spot_first_s:
                raise Stop(f"spot endpoint not reachable: no good poll (200 or 404) of the metadata endpoint within "
                           f"{self.be.spot_first_s:.0f} s of the poller's start; nothing has run (D-S0-8, N-F18): see "
                           f"spot/poller.log")
            return False
        if now - t > self.be.spot_stale_s:
            raise Stop(f"spot endpoint not reachable: the last good poll of the metadata endpoint was {now - t:.0f} s "
                       f"ago (> {self.be.spot_stale_s:.0f} s), so a termination notice could not arrive (N-F18)")
        return True

    def heartbeat(self, force=False):
        t = time.time()
        if force or t - self.last_hb >= self.be.heartbeat_s:
            write_text(f"{t:.0f} {utc(t)}\n", os.path.join(self.node.ledger, f"heartbeat.{self.boot}"))
            self.last_hb = t

    def boot_record(self):
        p = os.path.join(self.node.ledger, f"boot.{self.boot}.json")
        r = read_json(p)
        if r is None:
            bt = self.be.btime()
            r = {"boot_id": self.boot, "btime": bt, "btime_utc": utc(bt) if bt else None, "first_heartbeat": time.time(),
                 "campaigns": []}
        if self.c not in r["campaigns"]:
            r["campaigns"].append(self.c)
        write_json(r, p)

    def h_spent(self):
        led = ledger(self.node.root, None, self.be)
        if not led["complete"]:
            raise Stop(f"the node-hour ledger is incomplete ({'; '.join(led['problems'])}): no job starts (I-23)")
        return led["H_spent_h"]

    def snapshot_ledger(self):
        led = ledger(self.node.root, None, self.be)
        write_json(led, os.path.join(self.node.ledger, "snapshot.json"))
        c46.dump_public(led, os.path.join(self.cdir, "ledger.json"))
        return led

    def housekeeping(self):
        self.heartbeat()
        if self.poller is not None and self.poller.poll() is not None and not (self.shutdown or self.stopping or self.term):
            # round-4 R4-C1-2: the new poller's first good poll is awaited, with spot_first_s of grace from the restart;
            # the dead poller's heartbeat is not judged by the staleness rule; no restart once a shutdown or STOP began.
            # Round-5 R5-1: the grace is renewed only if the dead poller had a good poll of its own, so pollers that
            # never answer keep the first one's start and spot_check STOPs spot_first_s after it
            t_hb = self.spot_hb_time()
            if self.poller_t0 is None or (t_hb is not None and t_hb >= self.poller_t0 - 1.0):
                # round-6 R6-C1-2: pollers that each answer once and end would renew the grace at every restart, so
                # nothing would start and nothing STOP; the third renewal within spot_stale_s is a STOP (no restart)
                now = time.time()
                self.poller_renewals = [x for x in self.poller_renewals if now - x <= self.be.spot_stale_s] + [now]
                if len(self.poller_renewals) >= 3:
                    raise Stop(f"the spot poller keeps ending after a good poll (3 times within "
                               f"{self.be.spot_stale_s:.0f} s; N-F18): see spot/poller.log")
                self.poller_t0 = None
            self.log("WARN: the spot poller had ended: restarted; its first good poll is awaited (N-F18)"); self.start_poller()
        self.note_notice()
        if self.shutdown and not self.stopping:
            self.begin_shutdown()
        if self.term and not self.stopping:
            self.begin_stop("SIGINT received: stopped by the operator")
        if not self.stopping:
            self.spot_check()                                               # N-F18: a STOP if the endpoint is gone

    def note_notice(self):
        """N-11: once spot/notice.<boot> exists, nothing new starts for notice_hold_s and every running A2 part gets the
        'spot' exit file. Called by housekeeping and by held(), so a notice written while one schedule() pass runs its
        synchronous jobs holds every later launch of that pass (round-4 missed item)."""
        if self.notice_done or getattr(self, "boot", None) is None:
            return
        nf = os.path.join(self.node.spot, f"notice.{self.boot}")
        if not os.path.exists(nf):
            return
        self.notice_done = True
        try:
            nt = float(open(nf).read().split()[1])
        except (OSError, IndexError, ValueError):
            nt = time.time()
        self.hold_until = nt + self.be.notice_hold_s
        self.log(f"spot termination notice recorded: nothing new starts for {self.be.notice_hold_s:.0f} s (N-11); "
                 f"exit files for every running A2 part")
        for lab, h in list(self.procs.items()):
            if h["kind"] == "a2" and h["p"].poll() is None:
                self.request_exit(lab, h["dir"], "spot")

    def held(self):
        self.note_notice()                                                  # round-4 missed item: within a pass too
        return time.time() < self.hold_until

    # ---- STOP (N-D4) and the end
    def _guard(self, fn, *a, **kw):
        """Run one step of a stop or an exit; an exception (a full or read-only /data, a hygiene refusal) is reported
        on stderr and does not keep the next step from running (round-2 F1, M2)."""
        try:
            return fn(*a, **kw)
        except Exception as e:                                              # noqa: BLE001
            _warn(f"{getattr(fn, '__name__', 'a step')} failed during a stop or exit: {type(e).__name__}: {e}")
            return None

    def drop_keep_alive(self):
        """Section 16 / N-12: remove /data/KEEP_ALIVE (an unlink needs no free space)."""
        try:
            os.remove(self.node.keep_alive)
        except FileNotFoundError:
            pass
        except OSError as e:
            _warn(f"KEEP_ALIVE not removed: {type(e).__name__}: {e}")

    def begin_stop(self, reason):
        """N-D4: KEEP_ALIVE first, then the log line, CAMPAIGN_STOPPED and campaign.json, each guarded, so that drain()
        is always reached (round-2 F1); the reason in campaign.json passes the hygiene rules (round-2 M2)."""
        if self.stopping:
            return
        self.stopping = self.stop_written = True
        self.drop_keep_alive()
        # N-F36 (round-4 R4-C24-1): every STOP held by the A2 end rule and not yet raised is part of this STOP's reason
        held = [w for w in self.pending_stop if w not in reason]
        if held:
            reason = "; ".join([reason] + held)
        self._guard(self.log, f"STOP: {reason}")
        sf = os.path.join(self.cdir, "CAMPAIGN_STOPPED")
        self._guard(write_text, f"{utc()} {reason}\n", sf)
        if self.state is not None:
            self._guard(self.set_campaign, "stopped", stop_reason=public_text(reason))
        if os.path.exists(sf):
            for why in list(self.pending_stop):
                self._guard(self.mark_stop_raised, why)

    def mark_stop_raised(self, why):
        """N-F36: the A2 record whose end rule asked for this STOP records it as raised (CAMPAIGN_STOPPED holds it), so
        an operator's relaunch after that STOP does not raise it again."""
        lab = self.held_labels.get(why)
        if not lab:
            return
        r = read_json(self.a2_path(lab))
        if r and (r.get("end_rule") or {}).get("stop") and not r["end_rule"].get("stop_raised"):
            r["end_rule"]["stop_raised"] = True
            write_json(r, self.a2_path(lab))

    def begin_shutdown(self):
        """N-F10 (round-2 M1): SIGTERM is what the system sends at a reboot or a stop of the node (section 13: a spot
        reclaim or a node loss is an interruption, not a fail). Nothing new starts, the interruption is logged,
        KEEP_ALIVE is removed (if the node stays up, the idle self-stop applies), and the campaign stays 'running'
        without CAMPAIGN_STOPPED, so s2_relaunch.sh relaunches it after the boot; jobs cut by the shutdown are
        interruptions of an earlier boot at the relaunch. A STOP for a human is asked for with SIGINT."""
        self.stopping = True
        self.drop_keep_alive()
        self._guard(self.log, "shutdown signal (SIGTERM): an interruption, not a STOP (N-F10); nothing new starts; the "
                              "campaign stays 'running' for s2_relaunch.sh")
        self._guard(append_jsonl, os.path.join(self.cdir, "interruptions.jsonl"),
                    {"label": None, "kind": "runner", "time": utc(), "boot": getattr(self, "boot", None),
                     "cause": "shutdown signal (SIGTERM)"})

    def running_any(self):
        alive = [k for k, h in self.procs.items() if h["p"].poll() is None]
        for k in [k for k, h in self.procs.items() if h["p"].poll() is not None]:
            del self.procs[k]
        self.chain_lock_release()                                  # once no pw.x of this runner runs (N-6)
        return bool(alive)

    def finish(self):
        st = self.statuses()
        self.mark_phase(None)
        comp = {"schema": "s2-completeness-1", "campaign": self.c, "by_category": {}, "jobs": {}}
        for jid, j in self.G["jobs_by_id"].items():
            comp["jobs"][jid] = st[jid]
            if j.get("cat"):
                comp["by_category"].setdefault(j["cat"], Counter())[st[jid]] += 1
        comp["by_category"] = {k: dict(v) for k, v in comp["by_category"].items()}
        c46.dump_public(comp, os.path.join(self.cdir, "completeness.json"))
        self.snapshot_ledger()
        self.set_campaign("done", completeness=comp["by_category"])
        c46.dump_public(self.state, os.path.join(self.cdir, "state_end.json"))
        write_text(f"{utc()}\n", os.path.join(self.cdir, "CAMPAIGN_DONE"))
        if os.path.exists(self.node.keep_alive):
            os.remove(self.node.keep_alive)
        self.log(f"end: {dict(Counter(st.values()))}; CAMPAIGN_DONE; KEEP_ALIVE removed")

    # ---- state, commit, preconditions
    def load_state(self):
        s = read_json(self.node.state)
        if s is None:
            if self.c != "c1" and not self.be.mock:
                raise Stop(f"no state.json: {self.c} cannot start before C1")
            s = {"schema": "s2-state-1", "commit": None, "campaigns": {}, "cuts": []}
        return s

    def load_walls(self):
        """I-21 / review F6: the measured walls of every completed job of S2 so far, from the files of every campaign
        (A2 records, MACE records, single-point outputs in status mode, smoke and throughput records), so that the
        expected durations of the hard cap survive a relaunch and carry from C1 to C3 and from C2 to C4."""
        W = {}
        for c in CAMPAIGNS:
            cd = self.L.campaign_dir(c)
            for f in glob.glob(os.path.join(cd, "a2", "*", "*.a2.json")):
                r = read_json(f) or {}
                if r.get("status") == "complete" and r.get("wall_h") is not None:
                    W.setdefault("a2", {})[r["label"]] = float(r["wall_h"])
                    if r.get("n_config"):
                        W.setdefault("a2_config", {})[r["label"]] = float(r["wall_h"]) / int(r["n_config"])
            for f in glob.glob(os.path.join(cd, "cells", "*", "record.json")):
                try:
                    rec = c46.load_record(f, blind=True)
                except (OSError, ValueError):
                    continue
                w = (rec.get("relax") or {}).get("wall_s")
                if w:
                    W.setdefault("host" if rec.get("cell_kind") == "host" else "mace", {})[rec.get("work_id")] = float(w) / 3600.0
            for sub, kind in (("smoke", "smoke"), ("tp", "throughput")):
                for f in glob.glob(os.path.join(cd, sub, "*", "*.done.json")):
                    r = read_json(f) or {}
                    if r.get("ok") and r.get("wall_s"):
                        W.setdefault(kind, {})[os.path.basename(f)] = float(r["wall_s"]) / 3600.0
        for c in ("c1", "c3"):
            for d in glob.glob(os.path.join(self.node.jobs, f"s2{c}", "*")):
                lab = os.path.basename(d)
                if not os.path.exists(os.path.join(d, f"{lab}.in")) or not os.path.exists(os.path.join(d, f"{lab}.out")):
                    continue
                try:
                    r = self.read_out("sp_status", lab, "status", q47.sp_status, d, lab,
                                      meta=read_json(os.path.join(d, f"{lab}.meta.json")))
                except Exception as e:                                      # noqa: BLE001 (a timing only)
                    self.log(f"WARN: wall of {lab} not read ({type(e).__name__})"); continue
                if r.get("status") == "complete" and r.get("wall_s"):
                    kind = "sp_g1" if (lab.startswith("s2g1_") and lab.endswith("_e60")) else \
                        "sp_spin" if lab.startswith("s2spin_") else "sp"
                    W.setdefault(kind, {})[f"{c}:{lab}"] = float(r["wall_s"]) / 3600.0
        self.walls = W
        self.log("measured walls loaded: " + ", ".join(f"{k} {len(v)}" for k, v in sorted(W.items())) if W else
                 "measured walls loaded: none yet (unit costs of section 16 apply, I-21)")

    def check_commit(self):
        gs = self.be.git_state()
        if not gs["clean"]:
            raise Stop("the checkout is not clean")
        if self.state.get("commit") is None:
            self.state["commit"] = gs["head"]; self.save_state()
            self.log(f"S2 campaign commit recorded: {gs['head'][:12]}")
        elif gs["head"] != self.state["commit"]:
            fix = os.path.join(self.node.c("c2"), "STEP0_FIX")
            fx = open(fix).read().split() if os.path.exists(fix) else []
            if (self.c == "c2" and (self.state.get("step0") or {}).get("outcome") == "fail_pending_fix" and fx
                    and fx[0] == gs["head"]):
                self.state.setdefault("commit_history", []).append({"from": self.state["commit"], "to": gs["head"],
                                                                     "note": " ".join(fx[1:]), "time": utc()})
                self.state["commit"] = gs["head"]; self.save_state()
                self.discard_checks("c2")
                self.log(f"commit change for the step-0 repeat accepted (I-D1): {gs['head'][:12]}")
                self.step0_repeat(" ".join(fx[1:]))
            elif self.node_fix(gs["head"]):
                pass
            else:
                raise Stop(f"checkout HEAD {gs['head'][:12]} is not the recorded S2 commit {self.state['commit'][:12]}")

    def node_fix(self, head):
        """N-F17 (round-3 R3-C1-3, D-S0-8): a C1 STOP fixed by a dated, committed change resumes at the new commit
        with c1/NODE_FIX holding '<new commit> <dated note>'. Accepted only for C1, while C1 is stopped (a relaunch
        after CAMPAIGN_STOPPED, C1 not done) and when its commit is the checkout HEAD; recorded in commit_history.
        False when there is no NODE_FIX; a NODE_FIX that does not qualify is a STOP naming the reason."""
        nf = os.path.join(self.node.c("c1"), "NODE_FIX")
        if not os.path.exists(nf):
            return False
        fx = open(nf).read().split()
        stopped = self.was_stopped or os.path.exists(os.path.join(self.node.c("c1"), "CAMPAIGN_STOPPED"))
        why = None
        if self.c != "c1":
            why = f"c1/NODE_FIX applies only to C1, not {self.c}"
        elif (self.state.get("campaigns") or {}).get("c1") == "done":
            why = "C1 is done"
        elif not stopped:
            why = "C1 is not stopped (NODE_FIX resumes only a stopped C1)"
        elif len(fx) < 2 or fx[0] != head:
            why = f"c1/NODE_FIX must hold '<commit> <dated note>' with the commit {head[:12]} of the checkout"
        if why:
            raise Stop(f"c1/NODE_FIX refused: {why} (N-F17)")
        note = " ".join(fx[1:])
        self.state.setdefault("commit_history", []).append({"from": self.state["commit"], "to": head, "note": note,
                                                             "time": utc(), "via": "c1/NODE_FIX"})
        self.state["commit"] = head; self.save_state()
        os.replace(nf, nf + f".used.{int(time.time())}")
        self.discard_checks("c1")
        self.log(f"commit change after a C1 STOP accepted (N-F17, D-S0-8): {head[:12]}; note: {note[:200]}")
        return True

    def discard_checks(self, c):
        """Round-5 R5-2 (N-F31): at a commit change (NODE_FIX, STEP0_FIX) the campaign's check records go to
        <c>/discarded/commit_<t>/, so the UPF, node-script and model checks run again, first, at the new commit."""
        dst = os.path.join(self.node.c(c), "discarded", f"commit_{int(time.time())}")
        for w in ("upf", "nodescripts", "mace"):
            src = os.path.join(self.node.c(c), f"{w}_check.json")
            if os.path.exists(src):
                os.makedirs(dst, exist_ok=True); os.replace(src, os.path.join(dst, os.path.basename(src)))

    def step0_repeat(self, note):
        """I-D1: after a fix, C2 restarts at relaxation 1 for the one repeat (section 11). Everything A2 made before,
        and the gate files and markers of that attempt (step-0, K2, projection, K3), are moved aside unread into
        discarded/step0_attempt1_<t>/ (archived), so every in-A2 gate is evaluated again; the state records
        'repeat_pending' with the fix note, which is not an A2 stop (review-2 F3)."""
        dst = os.path.join(self.cdir, "discarded", f"step0_attempt1_{int(time.time())}")
        os.makedirs(dst, exist_ok=True)
        for sub in ("a2", "gates", "gates_applied"):
            d = os.path.join(self.cdir, sub)
            if os.path.isdir(d):
                shutil.move(d, os.path.join(dst, sub))
        prev = self.state.get("step0") or {}
        self.state["step0"] = {"attempts": int(prev.get("attempts") or 1), "outcome": "repeat_pending", "repeat": True,
                               "fix_note": note, "attempt1": {k: prev.get(k) for k in ("attempts", "outcome")}}
        for k in ("K2", "K3", "a2_stopped"):
            self.state.pop(k, None)
        self.save_state()
        self.log(f"step-0 repeat prepared: attempt-1 files in {os.path.relpath(dst, self.cdir)}; C2 restarts at "
                 f"relaxation 1 (attempt 2)")

    def preconditions(self):
        """Interface spec 9.2 item 1 and section 11: the preceding campaign and its gates permit this one. A refusal by
        recorded decisions is 'not_run' (N-D11); missing evidence is a STOP."""
        s = self.state
        camp = s.get("campaigns") or {}
        if self.c == "c1" and "stage0" not in s:
            adm = read_json(os.path.join(self.node.checkout, ADMISSIBILITY_RECORD))
            pb = read_json(os.path.join(self.node.checkout, PBCL_RECORD))
            if adm is None or pb is None:
                raise Stop("Stage-0 records (admissibility.json, pbcl_source.json) are missing in the checkout")
            if adm.get("status") != "ok":
                raise Stop(f"the Stage-0 admissibility record has status {adm.get('status')!r}")
            pr = adm["production"]
            cal = adm.get("m05_chosen") or {L: adm["m05_calibration"][L].get("chosen") for L in "BAX"}
            s["stage0"] = {"production_n8": pr["n8"], "reserves_n8": pr["reserves_n8"], "production_n10": pr["n10"],
                           "reserves_n10": pr["reserves_n10"], "m05_cal": {L: int(cal[L]) for L in "BAX"},
                           "pbcl": {k: pb.get(k) for k in ("decision", "value_used_A", "tag_for_shifted_starts",
                                                           "allow_provisional_required")}}
            self.save_state()
        if self.c == "c2":
            if camp.get("c1") != "done":
                raise Stop("C1 is not done")
            s0 = s.get("step0") or {}
            ne = os.path.join(self.cdir, "STEP0_NO_ERROR")
            if s0.get("outcome") == "fail_pending_fix" and os.path.exists(ne):
                # section 11: no writer or input error was found after a failed step-0 check: A2 stops and S2
                # reports the A1 tier only; the operator's dated note is recorded (I-D1)
                s["step0"] = {**s0, "outcome": "fail_final", "no_error_found": True,
                              "note": open(ne).read().strip()[:300]}
                self.save_state()
                self.log("STEP0_NO_ERROR: step-0 fail_final (no error found); A2 stops (section 11)")
            if s.get("sr_stop") or (s.get("gateN") or {}).get("Sr") is not True:
                return "Sr failed gate N (section 8): the protocol stops before A2 and is re-planned"
            sm = read_json(os.path.join(self.node.c("c1"), "smoke.json"))
            if not sm or not (sm.get("mapping") or {}).get("affine_slope_1") or s.get("a2_layout") is None:
                raise Stop("no usable smoke-test mapping or A2 layout from C1 (X-3, X-4)")
            if s["a2_layout"] != "48" and (sm.get("at_layout") or {}).get("label") != f"s2smoke_ref232_rst{s['a2_layout']}":
                raise Stop(f"the exit/restart smoke test at the A2 layout {s['a2_layout']} is not in c1/smoke.json "
                           f"(at_layout; X-4, N-F19)")
        if self.c == "c3":
            if camp.get("c2") not in ("done",):
                if s.get("sr_stop") or (s.get("gateN") or {}).get("Sr") is not True:
                    return "Sr failed gate N: production does not run (section 8)"
                raise Stop("C2 is not done")
            if s.get("K3") == "fail_replan":
                return "K3 failed: A2 and production stop; S2 is re-planned (section 11)"
            if s.get("n") not in (8, 10) or not os.path.exists(os.path.join(self.node.c("c1"), "gates_applied",
                                                                             "gate_nrule.json")):
                raise Stop(f"the C1 n rule (gate:nrule) is not applied (n = {s.get('n')!r}): production needs it "
                           f"(section 3, N-F24)")
        if self.c == "c4":
            if camp.get("c3") != "done":
                raise Stop("C3 is not done")
            why = []
            if s.get("K2") != "pass":
                why.append(f"K2 {s.get('K2')}")
            if (s.get("step0") or {}).get("outcome") != "pass":
                why.append(f"step-0 {(s.get('step0') or {}).get('outcome')}")
            if s.get("K3") != "pass":
                why.append(f"K3 {s.get('K3')}")
            if (s.get("gateN") or {}).get("Sr") is not True:
                why.append("Sr gate N")
            if 8 in cut_ids(s):
                why.append("cut 8")
            if why:
                return "C4 is not run: " + ", ".join(why)
        return None

    # ---- graph and statuses
    def graph_now(self):
        key = hashlib.sha256(json.dumps({k: v for k, v in self.state.items() if k != "campaigns"},
                                        sort_keys=True, default=str).encode()).hexdigest()
        if key != self.gkey:
            g = self.be.graph(self.c, self.state)
            if self.c in GRAPHS and not self.be.mock:
                assert_counts(g, self.state)
            g["jobs_by_id"] = OrderedDict((j["id"], j) for j in g["jobs"])
            c46.dump_public({k: v for k, v in g.items() if k != "jobs_by_id"}, os.path.join(self.cdir, "graph.json"))
            self.G, self.gkey = g, key
            self.cache = {k: v for k, v in self.cache.items() if _is_terminal(v)}
        return self.G

    def statuses(self):
        st = {}
        for jid, j in self.G["jobs_by_id"].items():
            if jid in self.cache:
                st[jid] = self.cache[jid]; continue
            s = self.status(j, st)
            if self.capped and s == "pending" and j["kind"] in CAP_KINDS:
                # only jobs that consume node-hours (pw.x, MACE) are refused by the cap; gates, the section 11 checks
                # (the geometry-only completion of a relaxation allowed to run, R2V-3, N-F8) and every other job
                # without node-hours run whenever their inputs are complete (N-F14, analyst decision 2026-11-04)
                s = "not_started_cap"
            st[jid] = s
            if _is_terminal(s):
                self.cache[jid] = s
        return st

    def deps_state(self, j, st):
        """'ok' when every dependency is done, 'blocked' when one ended otherwise, 'wait' while one is open. A gate, a
        record (smoke, throughput) and a distinct-minima job need their dependencies only ended (any end: they
        report what exists), and 'k0:<label>' needs configuration k = 0 of that relaxation."""
        any_end = j["kind"] in ("gate", "record") or (j["kind"] == "g46" and j.get("action") == "distinct")
        out = "ok"
        for d in j["deps"]:
            if j["kind"] == "a2v" and d != "a2:" + j["label"]:
                s = st.get(d)                                        # the section 11 partner: any end (I-F1)
                if s is None or _is_terminal(s):
                    continue
                out = "wait"; continue
            if d.startswith("k0:"):
                lab = d[3:]
                if self.k0.get(lab) or self.a2_k0_from_files(lab):
                    continue
                s = st.get("a2:" + lab)
                if s is not None and _is_terminal(s):
                    if j["kind"] == "gate":
                        return "blocked"
                    continue
                out = "wait"; continue
            s = st.get(d)
            if s is None:
                return "blocked"                                     # a job of another campaign: never here
            if s == "done":
                continue
            if _is_terminal(s):
                if any_end:
                    continue
                return "blocked"
            out = "wait"
        return out

    def status(self, j, st):
        kind = j["kind"]
        if kind == "check":
            r = read_json(os.path.join(self.cdir, f"{j['what']}_check.json"))
            return "done" if r and r.get("passed") else "pending"
        if kind == "record":
            if os.path.exists(self.record_path(j)) and (j["what"] != "smoke2" or self.smoke2_folded(j)):
                return "done"
            return "pending" if self.deps_state(j, st) != "blocked" else "skipped"
        if kind == "gate":
            if os.path.exists(self.gate_marker(j)):
                return "done"
            if j["phase"] == "a2" and self.a2_stopped():
                return "skipped"                                            # no in-A2 gate after A2 has stopped
            ds = self.deps_state(j, st)
            return "skipped" if ds == "blocked" else "pending"
        ds = self.deps_state(j, st)
        if kind == "g46":
            r = self.g46_done(j)
            if r:
                return r
            return "skipped" if ds == "blocked" else "pending"
        if kind == "g1":
            if os.path.exists(os.path.join(self.cdir, "g1", "done.json")):
                return "done"
            return "skipped" if ds == "blocked" else "pending"
        if kind == "mace":
            return self.mace_status(j, ds)
        if kind == "sp":
            return self.sp_state(j, ds)
        if kind == "pw":
            return self.pw_status(j, ds)
        if kind == "a2":
            return self.a2_status(j)
        if kind == "a2v":
            return self.a2v_status(j, st)
        raise S2Error(f"unknown job kind {kind}")

    # ---- scheduling
    def free_ready(self, st):
        """N-F20: a job of the active phase that costs no node-hours (gate, section 11 check, record, check, scripts/46
        geometry job, G1 cells) is pending with its dependencies satisfied."""
        active = self.active_phase(st)
        return any(st[jid] == "pending" and j["kind"] not in CAP_KINDS and self.deps_state(j, st) == "ok"
                   for jid, j in self.G["jobs_by_id"].items() if j["phase"] == active)

    def active_phase(self, st):
        G = self.G
        return next((ph for ph in G["phases"] if any(not _is_terminal(st[jid]) for jid, j in G["jobs_by_id"].items()
                                                     if j["phase"] == ph)), None)

    def schedule(self, st):
        if not self.spot_check():
            return                                                         # no job before a good poll (N-F18)
        G = self.G
        active = next((ph for ph in G["phases"] if any(not _is_terminal(st[jid]) for jid, j in G["jobs_by_id"].items()
                                                       if j["phase"] == ph)), None)
        if active is None:
            return
        if active != getattr(self, "phase_now", None):
            self.mark_phase(active)
        jobs = [j for j in G["jobs_by_id"].values() if j["phase"] == active]
        n46 = 0
        for j in jobs:
            if self.stopping or self.shutdown:
                return
            s = st[j["id"]]
            if s != "pending" or self.deps_state(j, st) != "ok":
                continue
            k = j["kind"]
            if self.pending_stop and k in CAP_KINDS:
                continue                                                   # a STOP is held: nothing costly starts (N-F20)
            if k == "check":
                self.run_check(j)
            elif k == "record":
                self.run_record(j)
            elif k == "gate":
                self.run_gate(j)
                return                                                     # the state may have changed: rebuild
            elif k == "g46" and n46 < 25:
                n46 += 1; self.run_g46(j)
            elif k == "g1":
                self.run_g1(j)
            elif k == "mace":
                if sum(1 for h in self.procs.values() if h["kind"] == "mace" and h["p"].poll() is None) < c46.MAX_CONCURRENT_MACE:
                    self.launch_mace(j)
            elif k == "pw":
                self.launch_pw(j)
            elif k == "a2v":
                self.run_a2v(j)
                return                                                     # as a gate: K3 before the next start (N-F22)
        if active == "qe":
            self.sp_phase(jobs, st)
        if active == "a2":
            self.a2_phase(jobs, st)

    def mark_phase(self, active):
        """Phase start and end times in campaign.json (reported only; no phase wall enters the projection, N-F9)."""
        p = os.path.join(self.cdir, "campaign.json")
        r = read_json(p) or {}
        ph = r.setdefault("phases", {})
        t = time.time()
        prev = getattr(self, "phase_now", None)
        if prev and prev in ph and not ph[prev].get("end"):
            ph[prev]["end"] = t
        if active:
            ph.setdefault(active, {}).setdefault("start", t)
        c46.dump_public(r, p)
        self.phase_now = active

    # ---- checks, records, gates
    def run_check(self, j):
        if j["what"] == "upf":
            ref = read_json(os.path.join(self.node.c("c1"), "upf_check.json")) if self.c != "c1" else None
            r = self.be.upf_check(self.c, ref)
        elif j["what"] == "nodescripts":
            # N-F31 (round-4 R4-C1-2): the node-only scripts behind every pw.x run, recorded in C1, compared after
            ref = read_json(os.path.join(self.node.c("c1"), "nodescripts_check.json")) if self.c != "c1" else None
            if self.c != "c1" and not (ref or {}).get("passed"):
                raise Stop("no passed c1/nodescripts_check.json to compare the node scripts with (N-F31)")
            r = self.be.nodescripts_check(self.c, ref)
        else:
            r = self.be.foundation_check()
        c46.dump_public(r, os.path.join(self.cdir, f"{j['what']}_check.json"))
        if (j["what"] == "upf" and self.c == "c1" and r.get("passed") and getattr(self, "_md5x", None) is not None
                and q47.upf_md5_extra(r) != self._md5x):              # round-6 R6-C1-1: after a NODE_FIX
            raise Stop("the C1 UPF check at the new commit gives other Cl/Ca MD5 than the record the existing outputs "
                       "were read with (N-B9)")
        self.log(f"check {j['what']}: {'passed' if r.get('passed') else 'FAILED'}"
                 + (f" ({'; '.join(r.get('problems') or [])[:300]})" if r.get("problems") else ""))
        if not r.get("passed"):
            raise Stop(f"the {j['what']} check failed: the campaign stops (sections 5, 6, 16; N-F31, N-F35)"
                       + (f": {'; '.join(r.get('problems') or [])[:300]}" if r.get("problems") else ""))

    def gate_marker(self, j):
        """The runner's record that a graph gate job was applied (outside gates/, which holds only scripts/49 files)."""
        return os.path.join(self.cdir, "gates_applied", re.sub(r"[^A-Za-z0-9_.-]", "_", j["id"]) + ".json")

    def gate_inputs(self, j):
        """The non-energy inputs scripts/49 takes on its command line (its --inputs file) and the attempt."""
        g, inp, att = j["gate"], {}, 1
        if g == "projection":
            # N-F9 (round-2 F3): tau_SP and the C1 MACE timings are derived by scripts/49 from the blinded C1 records
            # (I-C7b), never from a campaign phase wall
            inp = {"point": j["point"], "H_spent_h": self.h_spent()}
        elif g == "step0":
            sp = {"s2r_m30_VB136": "s2_m30_VB136", "s2r_m30_Sr136o0_vac": "s2_m30_Sr136o0_vac"}[j["at"]]
            st = self.state.get("step0") or {}
            att = 2 if (st.get("repeat") or st.get("outcome") == "repeat_pending") else 1
            fx = os.path.join(self.cdir, "STEP0_FIX")
            note = (" ".join(open(fx).read().split()[1:]) if os.path.exists(fx) else None) or st.get("fix_note")
            inp = {"cells": [sp], "attempt": att, "fix_note": note if att == 2 else None}
        elif g == "c3_complete":
            inp = {"c1": {"c3_labels": [x["label"] for x in self.G["jobs_by_id"].values() if x["kind"] == "sp"]}}
        return inp, att

    def run_gate(self, j):
        self.snapshot_ledger()
        self.save_state()
        log = os.path.join(self.cdir, "gates_applied", "gates.log")
        os.makedirs(os.path.dirname(log), exist_ok=True)
        inp, att = self.gate_inputs(j)
        ip = os.path.join(self.cdir, "gates_applied", re.sub(r"[^A-Za-z0-9_.-]", "_", j["id"]) + ".inputs.json")
        c46.dump_public(inp, ip)
        rc = self.be.gate(j["gate"], self.c, log, ip, att)
        gp = self.L.gate(self.c, j["gate"])
        out = read_json(gp)
        if self.shutdown and (rc != 0 or out is None):
            self.log(f"gate {j['id']}: interrupted by the shutdown (exit {rc}; N-F21): no marker, evaluated again at "
                     f"the relaunch")
            return
        if rc != 0 or out is None:
            raise Stop(f"gate {j['gate']} did not complete (exit {rc}): see gates_applied/gates.log")
        dec = out.get("decision") or {}
        self.state.update(copy.deepcopy(dec))                               # N-D1
        self.save_state()
        c46.dump_public(out, self.gate_marker(j)[:-5] + ".gate.json")      # every evaluation kept (step-0 twice)
        c46.dump_public({"schema": "s2-gate-applied-1", "id": j["id"], "gate": j["gate"], "rc": rc, "attempt": att,
                         "decision": dec, "gate_file_sha256": sha256_file(gp), "applied": utc()}, self.gate_marker(j))
        self.log(f"gate {j['id']}: decision {json.dumps(dec, sort_keys=True)[:300]}")
        if j["gate"] == "step0" and (self.state.get("step0") or {}).get("outcome") == "fail_pending_fix":
            self.a2_stop_all("step-0 check failed")
            raise Stop("step-0 check failed: find the writer or input error, commit the fix with a dated note, write "
                       "c2/STEP0_FIX ('<commit> <note path>') and relaunch; the check is repeated once (section 11)")
        if j["phase"] == "a2" and self.a2_stopped():
            self.a2_stop_all(f"gate {j['id']}")                            # at once, every running part (I-D3, N-F20)

    def record_path(self, j):
        return os.path.join(self.cdir, {"smoke": "smoke.json", "smoke2": "smoke2.json", "tp": "throughput.json"}[j["what"]])

    def run_record(self, j):
        if j["what"] == "smoke":
            rec = self.smoke_record()
            c46.dump_public(rec, self.record_path(j))
        elif j["what"] == "smoke2":
            # N-F19: the verdict at the layout goes into smoke.json first, then smoke2.json (rec:smoke2 is done only
            # with both), so a node loss between the writes cannot leave A2 the 48-rank restart verdict
            rec = self.smoke_record(label=j["label"], base=read_json(os.path.join(self.cdir, "smoke.json")))
            sm = read_json(os.path.join(self.cdir, "smoke.json"))
            sm["at_layout"] = {"layout": self.state.get("a2_layout"), "label": j["label"],
                               "exit_file_works": rec["exit_file_works"], "restart_possible": rec["restart_possible"],
                               "restart_files": rec["mapping"].get("restart_files")}
            if not rec["restart_possible"]:
                sm["restart_possible"] = False
            sm["mapping"]["restart_files"] = rec["mapping"].get("restart_files") or sm["mapping"].get("restart_files")
            c46.dump_public(sm, os.path.join(self.cdir, "smoke.json"))
            c46.dump_public(rec, self.record_path(j))
        else:
            rec = self.tp_record()
            c46.dump_public(rec, self.record_path(j))
        self.log(f"record {j['what']} written")

    def smoke2_folded(self, j):
        """N-F19: smoke.json carries the verdict of the smoke test at the chosen layout (at_layout for its label)."""
        sm = read_json(os.path.join(self.node.c("c1"), "smoke.json")) or {}
        return (sm.get("at_layout") or {}).get("label") == j.get("label")

    # ---- scripts/46 geometry jobs (N-D3)
    def job46(self, j, **extra):
        d = {"campaign": self.c, "root": self.node.root, "member": j.get("member"), "calc": self.be.calc,
             "threads": c46.THREADS, "role": j.get("role")}
        if j.get("member") == "m05":
            d["m05_cal"] = m05_cal(self.state)
        for k in ("work_id", "kind", "token", "site", "leg", "start", "pose", "parents", "partners", "allow_provisional",
                  "starts", "work_ids", "L", "legs"):
            if j.get(k) is not None:
                d[k] = j[k]
        if j.get("region"):
            g = re.match(r"region:(m\d\d|ref233)_([BAX])(\d+)$", j["region"])
            d["region"] = self.L.region(self.c, g.group(1), g.group(2), int(g.group(3)))
        if j.get("cell_kind"):
            d["kind"] = j["cell_kind"]
        d.update(extra)
        return d

    def g46_done(self, j):
        a = j["action"]
        if a == "region":
            return "done" if os.path.exists(self.L.region(self.c, j["member"], j["L"], j["site"])) else None
        if a == "build-vac":
            return "done" if os.path.exists(os.path.join(self.L.cell_dir(self.c, j["work_id"]), "vac_start.json")) else None
        if a == "build-pair":
            r = read_json(self.L.pair(self.c, j["member"], j["token"], j["site"], int(j["start"][1:])))
            if r is None:
                return None
            return "done" if r.get("status") == "built" else "rejected"
        if a == "distinct":
            return "done" if os.path.exists(self.distinct_path(j)) else None
        raise S2Error(f"unknown scripts/46 action {a}")

    def distinct_path(self, j):
        """scripts/46 Layout.distinct: pairs/<h>_<T><j>_<leg>.distinct.json."""
        return self.L.distinct(self.c, j["member"], j["token"], j["site"], j["leg"])

    def run_g46(self, j):
        a = j["action"]
        extra = {"action": a}
        if a == "build-vac":
            extra["work_id"] = j["work_id"]; extra["kind"] = "V"
        if a == "distinct":
            extra["out"] = self.distinct_path(j)
            # the relaxed starts of the leg (a rejected pair or a missing relaxation has no cell; section 9)
            ok = [(s, w) for s, w in zip(j["starts"], j["work_ids"]) if os.path.exists(self.L.record(self.c, w))]
            extra["starts"], extra["work_ids"] = [s for s, _ in ok], [w for _, w in ok]
            if not ok:
                c46.dump_public({"schema": "s2-distinct-1", "member": j["member"], "token": j["token"], "site": j["site"],
                                 "leg": j["leg"], "starts": [], "kept": [], "map": {}, "work_ids": {},
                                 "status": "no relaxed start"}, extra["out"])
                return
        jf = os.path.join(self.cdir, "jobs46", j["id"].replace(":", "_") + ".json")
        write_json(self.job46(j, **extra), jf)
        rc = self.be.run46(a, jf, os.path.join(self.cdir, "jobs46", "jobs46.log"))
        if self.shutdown and (rc != 0 or self.g46_done(j) is None):
            self.log(f"scripts/46 {a} {j['id']}: interrupted by the shutdown (exit {rc}; N-F21): pending")
            return
        if rc == 3:
            raise Stop(f"scripts/46 {a} refused {j['id']} (fail-closed): see jobs46/jobs46.log")
        if rc != 0 or self.g46_done(j) is None:
            raise Stop(f"scripts/46 {a} for {j['id']} ended with exit {rc} without its output (N-9)")

    def run_g1(self, j):
        """Section 7: the unrelaxed host-leg builder outputs of Cl at I138 and Ca at Pb136 on the S2-relaxed m30 host
        (geometry only, in the runner; no relaxation, no V+)."""
        host = read(self.relaxed_path(wid_of("m30", "host")))
        ctx = c46.host_context("m30")
        rec = {"schema": "s2-g1cells-1", "cells": {}, "builder": {"BUILDER_VERSION": b42.BUILDER_VERSION, "GEOM_SHA": b42.GEOM_SHA}}
        for T, L, jj in j["cells"]:
            b = c46.build_host_leg(host, ctx, T, int(jj))
            p = os.path.join(self.cdir, "g1", f"{T}{jj}.extxyz")
            os.makedirs(os.path.dirname(p), exist_ok=True)
            write(p, b.atoms, format="extxyz")
            rec["cells"][f"{T}{jj}"] = {"file": f"g1/{T}{jj}.extxyz", "sha256": sha256_file(p), "centre": int(b.centre)}
        c46.dump_public(rec, os.path.join(self.cdir, "g1", "done.json"))
        self.log("G1 cells built (Cl138, Ca136 host legs)")

    # ---- MACE relaxations (sections 5, 13)
    def relaxed_path(self, wid, campaign=None):
        c = campaign or self.c
        rec = c46.load_record(self.L.record(c, wid), blind=True)
        rel = (rec.get("files") or {}).get("relaxed") or f"cells/{wid}/relaxed.extxyz"
        return os.path.join(self.L.campaign_dir(c), rel)

    def attempts_path(self, wid):
        return os.path.join(self.L.cell_dir(self.c, wid), "attempts.json")

    def mace_status(self, j, ds):
        wid = j["work_id"]
        d = self.L.cell_dir(self.c, wid)
        if os.path.exists(self.L.record(self.c, wid)):
            if wid not in self.walls.get(j["xkind"], {}):
                try:
                    w = (c46.load_record(self.L.record(self.c, wid), blind=True).get("relax") or {}).get("wall_s")
                    if w:
                        self.walls.setdefault(j["xkind"], {})[wid] = float(w) / 3600.0
                except (OSError, ValueError):
                    pass
            return "done"
        if os.path.exists(os.path.join(d, "MISSING")):
            return "missing"
        att = read_json(self.attempts_path(wid), [])
        if not att:
            return "skipped" if ds == "blocked" else "pending"
        a = att[-1]
        if a.get("ended"):
            return "missing" if self.mace_counted(att) > MACE_RERUNS else "pending"
        h = self.procs.get(wid)
        if h is not None and h["p"].poll() is None:
            self.mace_watch(j, a)
            return "running"
        rcf = os.path.join(d, f"attempt{a['n']}.rc")
        rc = int(open(rcf).read().split()[0]) if os.path.exists(rcf) else None
        if a["boot"] == self.boot and rc is None and h is None and self.be.alive(a.get("pid")):
            self.mace_watch(j, a)
            return "running"                                                # started by an earlier runner, still alive
        if self.shutdown:
            return "running"                                                # judged at the relaunch (N-F21)
        res = self.resolution(d)
        if res is not None:
            return self.mace_resolve(wid, att, res)
        if rc == 0:
            raise Stop(f"{wid}: scripts/46 exited 0 without a record")
        cpid = a.get("child_pid") or child_pid(rcf)                         # the python process itself (F4)
        if a["boot"] == self.boot:
            if rc == 137 and self.be.oom(self.boot, cpid):
                return self.mace_interrupted(wid, att, "oom")
            raise Stop(f"{wid}: attempt {a['n']} ended with exit {rc} in this boot (an exception or refusal, N-9): see "
                       f"cells/{wid}/attempt{a['n']}.log; resolve with cells/{wid}/RESOLVE (N-D5)")
        if rc not in (None, 137):
            raise Stop(f"{wid}: attempt {a['n']} ended with exit {rc} before the reboot (N-9); resolve with RESOLVE")
        return self.mace_interrupted(wid, att, self.cause_of(a["boot"], cpid))

    def mace_watch(self, j, a):
        """N-F13: a MACE attempt running beyond its wall limit is a STOP for a human (nothing is killed)."""
        lim = self.be.mace_wall_s["host" if j.get("xkind") == "host" else "frozen"]
        t0 = a.get("started_epoch")
        if t0 is not None and time.time() - float(t0) > lim:
            raise Stop(f"{j['work_id']}: attempt {a['n']} has run {(time.time() - float(t0)) / 3600.0:.1f} h, beyond "
                       f"{lim / 3600.0:.0f} h (a hung relaxation, N-F13): end it, then resolve with RESOLVE")

    def out_watch(self, what, out):
        """N-F13: a pw.x output not written for stall_out_s while its process lives is a STOP for a human. The clock
        starts no earlier than this runner (an output of an earlier boot is not stale while the node was stopped)."""
        if not os.path.exists(out):
            return
        idle = time.time() - max(os.path.getmtime(out), self.t_start)
        if idle > self.be.stall_out_s:
            raise Stop(f"{what}: {os.path.basename(out)} not written for {idle / 3600.0:.1f} h while its pw.x lives "
                       f"(a hung run, N-F13): end it, then resolve")

    def cause_of(self, boot, pid, task=None, since=None, pids=None, exclude=None):
        if boot != self.boot and os.path.exists(os.path.join(self.node.spot, f"notice.{boot}")):
            return "spot-notice"
        if self.be.oom(boot, pid, task=task, since=since, pids=pids, exclude=exclude):
            return "oom"
        return "node-loss" if boot != self.boot else "unknown"

    def resolution(self, d):
        f = os.path.join(d, "RESOLVE")
        if not os.path.exists(f):
            return None
        w = open(f).read().strip().split(None, 1)
        os.replace(f, f + f".used.{int(time.time())}")
        return (w[0], w[1] if len(w) > 1 else "") if w and w[0] in ("rerun", "missing", "unconverged") else \
            ("invalid", " ".join(w))

    def mace_resolve(self, wid, att, res):
        word, note = res
        append_jsonl(os.path.join(self.cdir, "interruptions.jsonl"), {"label": wid, "time": utc(), "boot": self.boot,
                                                                       "cause": f"operator {word}: {note}"[:200]})
        if word == "missing":
            write_text(f"{utc()} {note}\n", os.path.join(self.L.cell_dir(self.c, wid), "MISSING"))
            return "missing"
        if word == "rerun":
            # N-F33 (round-4 R4-C1-4): the operator's rerun after a STOP for a human and a committed fix (an exception,
            # N-9) is not one of the two reruns that section 13 allows after a reclaim, node loss, OOM or wall time
            return self.mace_interrupted(wid, att, f"operator: {note}"[:120], counts=False)
        raise Stop(f"{wid}: RESOLVE must hold 'rerun <note>' or 'missing <note>'")

    @staticmethod
    def mace_counted(att):
        """N-F33: the ended attempts that count against MACE_RERUNS (every interruption; not an operator's rerun)."""
        return sum(1 for a in att if a.get("ended") and a.get("counts", True))

    def mace_interrupted(self, wid, att, cause, counts=True):
        d = self.L.cell_dir(self.c, wid)
        a = att[-1]
        dst = os.path.join(d, "discarded", f"att{a['n']}")
        os.makedirs(dst, exist_ok=True)
        # the relaxation's inputs (builder outputs, the job) and the attempt list stay; everything else the attempt
        # wrote (FIRE log, partial structures, logs) is moved aside unread (section 13)
        keep = {"job.json", "start.extxyz", "vac_start.json", "attempts.json", "discarded"}
        for f in os.listdir(d):
            if f not in keep and not f.startswith("RESOLVE"):
                shutil.move(os.path.join(d, f), os.path.join(dst, f))
        a.update({"ended": utc(), "cause": cause, "counts": bool(counts)})
        write_json(att, self.attempts_path(wid))
        append_jsonl(os.path.join(self.cdir, "interruptions.jsonl"),
                     {"label": wid, "kind": "mace", "attempt": a["n"], "time": utc(), "boot": a["boot"], "cause": cause,
                      "counts": bool(counts)})
        left = self.mace_counted(att) <= MACE_RERUNS
        self.log(f"{wid}: attempt {a['n']} interrupted ({cause}); " + ("rerun from the start" if left else "no rerun left: missing"))
        return "pending" if left else "missing"

    def launch_mace(self, j):
        wid = j["work_id"]
        if self.held() or not self.cap_ok(j, j.get("xkind", "mace")):
            return
        d = self.L.cell_dir(self.c, wid)
        os.makedirs(d, exist_ok=True)
        jf = os.path.join(d, "job.json")
        job = self.job46(j, action=j["action"], work_id=wid)
        old = read_json(jf)
        if old is not None and old != job:
            raise Stop(f"{wid}: the job differs from its earlier attempts (a rerun must be identical, section 13)")
        if old is None:
            write_json(job, jf)
        att = read_json(self.attempts_path(wid), [])
        n = len(att) + 1
        att.append({"n": n, "boot": self.boot, "started": utc(), "started_epoch": time.time(), "pid": None})
        write_json(att, self.attempts_path(wid))                            # recorded before the process exists
        env = {"OMP_NUM_THREADS": str(c46.THREADS), "MKL_NUM_THREADS": str(c46.THREADS), "OPENBLAS_NUM_THREADS": "1"}
        p = self.be.spawn(self.be.cmd46(j["action"], jf), cwd=self.node.checkout, log=os.path.join(d, f"attempt{n}.log"),
                          rc=os.path.join(d, f"attempt{n}.rc"), env=env, pass_fds=(self.lockfd,))
        att[-1]["pid"] = p.pid
        write_json(att, self.attempts_path(wid))
        self.procs[wid] = {"p": p, "kind": "mace", "dir": d}
        self.log(f"MACE {j['action']} {wid} attempt {n} started (pid {p.pid})")

    # ---- the hard cap (section 16)
    def measured(self, kind):
        """Measured walls (h) of completed jobs of a kind in S2 so far, every campaign (I-21; loaded from the files at
        each start by load_walls, review F6)."""
        return list((self.walls.get(kind) or {}).values())

    def cap_ok(self, j, kind, factor=1.0, extra_h=0.0, expected_h=None):
        if self.capped:
            return False
        H = self.h_spent()
        e = g49.expected_hours(kind, self.measured(kind)) if expected_h is None else float(expected_h)
        if g49.job_start_allowed(H + extra_h, factor * e):
            return True
        self.capped = {"job": j["id"], "kind": kind, "H_spent_h": H, "outstanding_h": extra_h, "expected_h": factor * e,
                       "time": utc()}
        c46.dump_public({"schema": "s2-hardcap-1", **self.capped}, os.path.join(self.cdir, "HARD_CAP.json"))
        self.log(f"hard cap: {j['id']} not started (H_spent {H:.2f} + {extra_h:.2f} + {factor * e:.2f} > "
                 f"{g49.RULES['HARD_CAP_H']} node-h); every pw.x and MACE job of {self.c} not yet started is 'not "
                 f"started (hard cap)', also after a relaunch (I-D9); gates and geometry-only jobs still run (N-F14)")
        return False

    def load_cap(self):
        """I-D9 (round-3 R3C-7): a hard-cap refusal recorded in HARD_CAP.json persists across runner starts."""
        hc = read_json(os.path.join(self.cdir, "HARD_CAP.json"))
        if hc:
            self.capped = {k: hc.get(k) for k in ("job", "kind", "H_spent_h", "outstanding_h", "expected_h", "time")}
            self.log(f"hard cap: the refusal of {hc.get('job')} ({hc.get('time')}) persists: no pw.x or MACE job of "
                     f"{self.c} starts (I-D9)")

    # ---- single points (sections 6, 12, 13)
    def stage_dir(self, label):
        return os.path.join(self.cdir, "qe_stage", label)

    def sp_cell(self, j):
        """(work id or None, atoms file) behind a single point, or None if it cannot exist (skipped)."""
        if j["src"] == "g1":
            g = read_json(os.path.join(self.cdir, "g1", "done.json"))
            return None, os.path.join(self.cdir, g["cells"][j["g1"]]["file"])
        wid = j["cell"]
        if j["src"] == "distinct":
            s = j["slot"]
            r = read_json(self.distinct_path({"member": s["member"], "token": s["token"], "site": s["site"],
                                              "leg": s["leg"]})) or {}
            p = (r.get("map") or {}).get(f"o{s['k']}")
            if p is None:
                return None                                                 # no kept minimum in this slot (I-D4)
            wid = (r.get("work_ids") or {}).get(f"o{s['k']}") or wid_of(s["member"], "D", T=s["token"], j=s["site"],
                                                                       n=int(str(p).lstrip("p")), leg=s["leg"])
        if not os.path.exists(self.L.record(self.c, wid)):
            return None
        return wid, self.relaxed_path(wid)

    def sp_state(self, j, ds):
        lab = j["label"]
        jd = self.L.sp_dir(self.c, lab)
        if os.path.exists(os.path.join(jd, f"{lab}.in")):
            meta = read_json(os.path.join(jd, f"{lab}.meta.json"))
            r = self.read_out("sp_status", lab, "status", q47.sp_status, jd, lab, meta=meta)
            s = r.get("status")
            if s == "complete":
                if r.get("wall_s"):
                    self.walls.setdefault(j.get("sp_kind", "sp"), {})[f"{self.c}:{lab}"] = float(r["wall_s"]) / 3600.0
                return "done"
            if s == "missing":
                if r.get("gaveup_pending") and not os.path.exists(os.path.join(jd, f"{lab}.gaveup")):
                    # the node stopped between the queue's mv and touch: the runner writes .gaveup, so the queue
                    # never starts a third attempt (section 12; round-2 R2-QE-2)
                    write_text(f"{utc()} written by the S2 runner (the queue stopped before its touch)\n",
                               os.path.join(jd, f"{lab}.gaveup"))
                    fsync_dir(jd)
                self.log(f"{lab}: missing ({r.get('missing_reason')})")
                return "missing"
            if self.chain_alive():
                self.out_watch(lab, os.path.join(jd, f"{lab}.out"))           # N-F13
            return "running"
        if ds == "blocked":
            return "skipped"
        if ds == "wait":
            return "pending"
        if j["src"] == "distinct" and self.sp_cell(j) is None:
            return "skipped"                                                # no kept minimum in this slot (I-D4)
        if j["src"] == "cell" and self.sp_cell(j) is None:
            return "skipped"
        return "pending"

    def stage_sp(self, j):
        lab = j["label"]
        sd = self.stage_dir(lab)
        if os.path.exists(os.path.join(sd, "stage.json")):
            return
        wid, f = self.sp_cell(j)
        at = read(f)
        di = None
        if j.get("sp_kind") == "sp_spin":
            idx = [i for i, s in enumerate(at.get_chemical_symbols()) if s == j["dopant"]]
            if len(idx) != 1:
                raise Stop(f"{lab}: {len(idx)} atoms of {j['dopant']} in the cell")
            di = idx[0]
        q47.write_input(at, lab, sd, kind="sp", dopant_index=di, ranks=q47.RANKS_SP, campaign=self.c,
                        cell={"work_id": wid, "atoms_sha256": sha256_file(f)})
        c46.dump_public({"label": lab, "cell": wid, "atoms_sha256": sha256_file(f), "staged": utc()},
                        os.path.join(sd, "stage.json"))

    def publish_sp(self, lab):
        """N-5: meta first, then the input under a name no queue glob matches, renamed (fsynced)."""
        sd, jd = self.stage_dir(lab), self.L.sp_dir(self.c, lab)
        os.makedirs(jd, exist_ok=True)
        shutil.copyfile(os.path.join(sd, f"{lab}.meta.json"), os.path.join(jd, f"{lab}.meta.json"))
        part = os.path.join(jd, f"{lab}.in.part")
        shutil.copyfile(os.path.join(sd, f"{lab}.in"), part)
        with open(part, "rb+") as fh:
            os.fsync(fh.fileno())
        os.replace(part, os.path.join(jd, f"{lab}.in"))
        fsync_dir(jd)
        write_json({"published": utc(), "boot": self.boot}, os.path.join(sd, "published.json"))
        self.log(f"single point {lab} published")

    def chain_alive(self):
        h = self.procs.get("chain")
        if h is not None and h["p"].poll() is None:
            return True
        r = read_json(os.path.join(self.cdir, "chain.pid.json"))
        return bool(r and r.get("boot") == self.boot and self.be.alive(r.get("pid")) and h is None)

    def sp_phase(self, jobs, st):
        sps = [j for j in jobs if j["kind"] == "sp"]
        outstanding = [j for j in sps if st[j["id"]] == "running"]
        if outstanding and not self.chain_alive() and not self.held() and not self.stopping:
            n = len(glob.glob(os.path.join(self.cdir, "chain.*.log"))) + 1
            p = self.be.spawn([self.node.chain, f"s2{self.c}"], cwd=self.node.checkout,
                              log=os.path.join(self.cdir, f"chain.{n}.log"), rc=os.path.join(self.cdir, f"chain.{n}.rc"),
                              pass_fds=(self.lockfd,))
            self.procs["chain"] = {"p": p, "kind": "chain", "dir": self.cdir}
            write_json({"pid": p.pid, "boot": self.boot, "started": utc()}, os.path.join(self.cdir, "chain.pid.json"))
            self.log(f"chain.sh s2{self.c} started ({len(outstanding)} outstanding)")
        if self.held() or self.stopping or self.capped or self.pending_stop:
            return
        nout = len(outstanding)
        for j in sps:
            if nout >= SP_AHEAD:
                break
            if st[j["id"]] != "pending" or self.deps_state(j, st) != "ok":
                continue
            kind = j.get("sp_kind", "sp")
            extra = sum(2 * g49.expected_hours(o.get("sp_kind", "sp"), self.measured(o.get("sp_kind", "sp")))
                        for o in outstanding)
            if not self.cap_ok(j, kind, factor=2.0, extra_h=extra):          # N-10, I-D2
                return
            self.stage_sp(j)
            self.publish_sp(j["label"])
            outstanding.append(j); nout += 1
            st[j["id"]] = "running"

    # ---- pw.x runs: smoke tests, throughput row, A2 parts (sections 11, 13, 16)
    def pw_dir(self, j):
        return os.path.join(self.cdir, "smoke" if j["phase"].startswith("smoke") else "tp", j["label"])

    def part_files(self, d, label, n):
        b = os.path.join(d, f"{label}.p{n}")
        return {"in": b + ".in", "out": b + ".out", "launch": b + ".launch.json", "rc": b + ".rc", "log": b + ".runlog",
                "done": b + ".done.json"}

    def ref_cells(self):
        """The 232-atom reference vacancy cell (q = +1) and the Pb136-like frozen region of section 16."""
        if getattr(self, "_ref", None) is None:
            ctx = c46.ref_context()
            reg = c46.build_region(ctx.host, "ref233", 136)
            vac = read(os.path.join(ROOT, b42.VAC_REF))
            self._ref = (vac, c46.free_in_cell(reg, "V"))
        return self._ref

    def smoke_rec(self):
        return read_json(os.path.join(self.node.c("c1"), "smoke.json")) or {}

    def smoke_map(self):
        return self.smoke_rec().get("mapping") or {}

    def pw_resolve(self, j, d):
        """N-F16 (round-3 R3-C1-2): RESOLVE for a pw.x reference run (smoke, smoke2, throughput), after a STOP and a
        dated, committed fix. 'rerun <note>': every part, output and tmp/ of the run and the records built on it
        (smoke.json and smoke2.json for a smoke test, smoke2.json and smoke.json for the test at the layout,
        throughput.json and the throughput gate's markers for a throughput run) go to discarded/resolved_<t>/ unread,
        so the run and its records are made again; 'missing <note>': the part is missing."""
        word, note = self.resolution(d)
        lab = j["label"]
        append_jsonl(os.path.join(self.cdir, "interruptions.jsonl"), {"label": lab, "kind": "pw", "time": utc(),
                                                                       "boot": self.boot,
                                                                       "cause": f"operator {word}: {note}"[:200]})
        if word == "missing":
            f = self.part_files(d, lab, j["part"])
            write_json({"label": lab, "part": j["part"], "ok": False, "status": "missing",
                        "reason": f"operator: {note}"[:200], "energies_read": False}, f["done"])
            return "missing"
        if word != "rerun":
            raise Stop(f"{lab}: RESOLVE must hold 'rerun <note>' or 'missing <note>' (N-F16)")
        t = int(time.time())
        dst = os.path.join(d, "discarded", f"resolved_{t}")
        os.makedirs(dst, exist_ok=True)
        for x in os.listdir(d):
            if x != "discarded" and not x.startswith("RESOLVE"):
                shutil.move(os.path.join(d, x), os.path.join(dst, x))
        # N-F33 (round-4 R4-C1-4): the attempts before the resolution go aside with it, so the rerun has the two
        # reruns after an interruption that N-D10 gives (the count reads discarded/p<n>_* only)
        for x in os.listdir(os.path.join(d, "discarded")):
            if not x.startswith("resolved_"):
                shutil.move(os.path.join(d, "discarded", x), os.path.join(dst, x))
        recs = {"smoke": ("smoke.json", "smoke2.json"), "smoke2": ("smoke2.json", "smoke.json"),
                "tp": ("throughput.json", "gates_applied/gate_throughput.json", "gates_applied/gate_throughput.gate.json",
                       "gates_applied/gate_throughput.inputs.json")}[j["phase"]]
        for x in recs:
            p = os.path.join(self.cdir, x)
            if os.path.exists(p):
                shutil.move(p, os.path.join(dst, os.path.basename(x)))
        for k in [k for k, v in self.cache.items()]:
            del self.cache[k]                                              # the records changed: recompute every status
        self.log(f"{lab}: RESOLVE rerun ({note[:120]}): its parts and {', '.join(recs)} moved to "
                 f"{os.path.relpath(dst, self.cdir)} (N-F16)")
        return "pending"

    def pw_live(self, d, label):
        """True while a part of this pw.x reference run is alive: a handle of this runner, or a launch of this boot
        without an exit status whose pid lives (round-4 R4-C1-4)."""
        if any(h["kind"] == "pw" and h["dir"] == d and h["p"].poll() is None for h in self.procs.values()):
            return True
        for lf in glob.glob(os.path.join(d, f"{label}.p*.launch.json")):
            L = read_json(lf) or {}
            if not os.path.exists(lf[:-len(".launch.json")] + ".rc") and L.get("boot") == self.boot and \
                    self.be.alive(L.get("pid")):
                return True
        return False

    def pw_status(self, j, ds):
        d = self.pw_dir(j)
        f = self.part_files(d, j["label"], j["part"])
        if os.path.exists(os.path.join(d, "RESOLVE")):
            # round-4 R4-C1-4: a RESOLVE is read only once no part of the run lives (it is written after a STOP); a run
            # that is alive keeps 'running', its files stay where they are and RESOLVE waits for its end
            if not self.pw_live(d, j["label"]):
                return self.pw_resolve(j, d)
            if d not in self.resolve_wait:
                self.resolve_wait.add(d)
                self.log(f"{j['label']}: RESOLVE waits for the running part to end (R4-C1-4)")
        if os.path.exists(f["done"]):
            r = read_json(f["done"])
            return "done" if r.get("ok") else r.get("status", "missing")
        if ds == "blocked":
            return "skipped"
        if not os.path.exists(f["launch"]):
            return "pending"
        h = self.procs.get(j["id"])
        L = read_json(f["launch"])
        rc_exists = os.path.exists(f["rc"])
        if (h is not None and h["p"].poll() is None) or (h is None and not rc_exists and L["boot"] == self.boot
                                                          and self.be.alive(L.get("pid"))):
            self.out_watch(j["label"], f["out"])                            # N-F13
            self.watch_tree(j["id"], f["launch"], j["label"], int(j["ranks"]))      # N-F34
            if j.get("exit_after") and not os.path.exists(os.path.join(d, "exit_request.json")) and os.path.exists(f["out"]):
                r = self.read_out("parse_counts", j["label"], "counts", q47.parse_counts, f["out"], ranks=j["ranks"])
                if (r.get("n_config") or 0) >= j["exit_after"]:
                    self.request_exit(j["label"], d, "smoke")
            return "running"
        if self.shutdown:
            return "running"                                                # judged at the relaunch (N-F21)
        # ended (or cut by a reboot)
        if not os.path.exists(f["out"]):
            r = {}
        elif j.get("restart_of"):
            r = self.restart_counts(d, j)
        else:
            r = self.read_out("parse_counts", j["label"], "counts", q47.parse_counts, f["out"], ranks=j["ranks"])
        t0 = L.get("started_epoch"); t1 = os.path.getmtime(f["rc"]) if rc_exists else None
        rec = {"label": j["label"], "part": j["part"], "ranks": j["ranks"], "counts": r,
               "wall_s": (t1 - t0) if (t0 and t1) else None, "energies_read": False,
               # N-F30: the core set asked for, the CPUs its pw.x ranks were allowed (node /proc) and the interval, so
               # that the 2x32 rate is computed only for two copies that ran together on disjoint cores
               "cpuset": L.get("cpuset"), "affinity": L.get("affinity"), "interval": [t0, t1] if (t0 and t1) else None}
        if r.get("job_done"):
            if j.get("exit_after"):
                tmp = os.path.join(d, "tmp")
                rec["restart_files"] = sorted(os.path.relpath(os.path.join(a, b), tmp).replace(j["label"], "{prefix}")
                                              for a, _, bs in os.walk(tmp) for b in bs if not b.endswith(".EXIT")) \
                    if os.path.isdir(tmp) else []
            rec["ok"] = True
            write_json(rec, f["done"])
            return "done"
        if r.get("end") == "pw_error":
            # QE's error banner: a final end, not an interruption; not rerun (N-D10, as I-D6 for A2; round-3 R3-C1-5)
            rec.update({"ok": False, "status": "missing", "reason": f"pw.x error routine {r.get('end_marker')}"})
            write_json(rec, f["done"])
            self.log(f"{j['label']}.p{j['part']}: pw.x error ({r.get('end_marker')}): missing, not rerun (N-D10)")
            return "missing"
        n = len(glob.glob(os.path.join(d, "discarded", f"p{j['part']}_*"))) + 1
        dst = os.path.join(d, "discarded", f"p{j['part']}_{n}")
        os.makedirs(dst, exist_ok=True)
        cause = self.cause_of(L["boot"], child_pid(f["rc"]) or L.get("pid"), since=t0,
                              **self.oom_args(L, j["label"], L["boot"]))           # N-F34 (round-4 R4-C1-5)
        for k in ("out", "launch", "rc", "log"):
            if os.path.exists(f[k]):
                shutil.move(f[k], dst)
        if os.path.exists(f["rc"] + ".pid"):
            shutil.move(f["rc"] + ".pid", dst)
        if os.path.isdir(os.path.join(d, "tmp")) and j["part"] == 1:
            shutil.move(os.path.join(d, "tmp"), os.path.join(dst, "tmp"))
        append_jsonl(os.path.join(self.cdir, "interruptions.jsonl"),
                     {"label": f"{j['label']}.p{j['part']}", "kind": "pw", "time": utc(), "boot": L["boot"],
                      "cause": cause})
        if n > PW_RERUNS:
            rec.update({"ok": False, "status": "missing"})
            write_json(rec, f["done"])
            return "missing"
        return "pending"

    def restart_counts(self, d, j):
        """Counts of a restart part (the smoke test's part 2): parsed with part 1, since its counters continue part 1's;
        first as continuing, then as repeating the last configuration (the two readings the mapping can take)."""
        outs = [self.part_files(d, j["label"], n)["out"] for n in (j["restart_of"], j["part"])]
        for rep in (False, True):
            rel = self.read_out("parse_relax", j["label"], "counts", q47.parse_relax, outs, read="counts",
                                k_cap=q47.K_CAP, mapping={"restart_continues_counters": True, "restart_repeats_last": rep},
                                ranks=j["ranks"], **self.a2_checks(d, j["label"]))
            if rel.get("usable") and len(rel.get("parts") or []) == 2:
                p2 = rel["parts"][1]
                return {**{k: p2.get(k) for k in ("n_config", "k_first", "k_last", "end", "end_marker", "job_done",
                                                    "exit_marker_seen", "wall_s", "counters_first", "counters_last")},
                        "usable": True, "repeats_last": rep}
        return {"usable": False, "job_done": None, "reason": "the restart part does not continue part 1 either way"}

    def smoke_pair_check(self, before):
        """Round-4 R4-C1-5 (X-3, D-S0-6, D-S0-8): the smoke tests n1 and n3 must both have JOB DONE and differ by two
        configurations (an affine nstep mapping of slope 1) before the exit/restart test and the throughput row run;
        otherwise a STOP naming the smoke tests, while C1 can still be resumed (NODE_FIX, RESOLVE)."""
        rd = lambda lab: read_json(self.part_files(os.path.join(self.cdir, "smoke", lab), lab, 1)["done"]) or {}  # noqa: E731
        n1, n3 = (rd(x).get("counts") or {} for x in ("s2smoke_ref232_n1", "s2smoke_ref232_n3"))
        fix = ("after a dated, committed fix if one is needed (c1/NODE_FIX, N-F17) write smoke/<run>/RESOLVE 'rerun "
               "<dated note>' for each run to repeat and relaunch (N-F16)")
        if not (n1.get("job_done") and n3.get("job_done")):
            raise Stop(f"pw.x smoke tests n1/n3 incomplete: no nstep mapping (section 16, D-S0-8) before {before}: see "
                       f"smoke/ and smoke.json; {fix}")
        if int(n3.get("n_config") or 0) - int(n1.get("n_config") or 0) != 2:
            raise Stop(f"pw.x smoke tests n1/n3 not affine with slope 1 (n1 {n1.get('n_config')}, n3 {n3.get('n_config')} "
                       f"configurations; X-3, D-S0-6) before {before}: see smoke/; {fix}")

    def pw_prepare(self, j):
        """The input of one pw.x reference part, written once (False when the part is recorded skipped instead)."""
        d = self.pw_dir(j)
        os.makedirs(d, exist_ok=True)
        f = self.part_files(d, j["label"], j["part"])
        if j["phase"] == "smoke" and j.get("exit_after") and j["part"] == 1:
            self.smoke_pair_check("the exit/restart test")                  # R4-C1-5
        if os.path.exists(f["in"]):
            return True
        if j.get("restart_of"):
            p1 = self.part_files(d, j["label"], j["restart_of"])
            d1 = read_json(p1["done"]) or {}
            n3 = read_json(self.part_files(os.path.join(self.cdir, "smoke", "s2smoke_ref232_n3"),
                                           "s2smoke_ref232_n3", 1)["done"]) or {}
            n1 = read_json(self.part_files(os.path.join(self.cdir, "smoke", "s2smoke_ref232_n1"),
                                           "s2smoke_ref232_n1", 1)["done"]) or {}
            if (d1.get("counts") or {}).get("end") != "exit_stop":
                write_json({"ok": False, "status": "skipped", "reason": "part 1 did not stop by the exit file"}, f["done"])
                return False
            c0 = n1["counts"]["n_config"] - 1
            nst = n3["counts"]["n_config"] - d1["counts"]["n_config"] - c0
            q47.restart_input(p1["in"], f["in"], max(1, nst))
            return True
        vac, free = self.ref_cells()
        nstep = j.get("nstep")
        if nstep is None:
            sm = read_json(os.path.join(self.cdir, "smoke.json")) or {}
            mp = sm.get("mapping") or {}
            if mp.get("c0") is None:
                raise Stop("pw.x smoke tests n1/n3 incomplete: no nstep mapping (section 16, D-S0-8): see "
                           "smoke/ and smoke.json; after a dated, committed fix (c1/NODE_FIX, N-F17) write "
                           "smoke/<run>/RESOLVE 'rerun <dated note>' for each failed run and relaunch (N-F16)")
            if not mp.get("affine_slope_1"):
                raise Stop("the smoke-test mapping in smoke.json is not affine with slope 1 (X-3, D-S0-6; R4-C1-5): see "
                           "smoke/ and smoke.json; write smoke/<run>/RESOLVE 'rerun <dated note>' for each run to repeat "
                           "(after a dated, committed fix if one is needed, c1/NODE_FIX) and relaunch (N-F16)")
            nstep = max(1, j["n_config"] - int(mp["c0"]))
        q47.write_input(vac, j["label"], d, kind="relax", free=free, nstep=nstep, ranks=j["ranks"], campaign=self.c,
                        cell={"work_id": None, "reference": "ref232", "region": "Pb136-like"})
        os.replace(os.path.join(d, f"{j['label']}.in"), f["in"])
        return True

    def launch_pw(self, j):
        h = self.procs.get(j["id"])
        if h is not None and h["p"].poll() is None:
            return                                                          # started with its pair in this pass (N-F30)
        if self.held() or not self.chain_lock_ok() or \
                not self.cap_ok(j, "smoke" if j["phase"].startswith("smoke") else "throughput"):
            return
        if j["label"] in TP_PAIR:
            return self.launch_tp_pair(j)
        if self.pw_prepare(j):
            self._spawn_part(j["id"], self.pw_dir(j), j["label"], j["part"], j["ranks"], "pw")

    def launch_tp_pair(self, j):
        """N-F30 (round-4 missed item): the two 32-rank copies of the throughput row always start together, each on its
        own half of the cores. A copy left alone after an interruption of the other waits while the other lives; a
        copy that completed without the other beside it is moved aside, its measurement not used (discarded/
        paired_<t>, not one of its reruns), and both run again; with the other copy missing no pair can be measured and
        this one is skipped."""
        other = TP_PAIR[1 - TP_PAIR.index(j["label"])]
        jo = self.G["jobs_by_id"]["pw:" + other]
        do = self.pw_dir(jo)
        fo = self.part_files(do, other, 1)
        if self.pw_live(do, other):
            if ("pair", j["id"]) not in self.resolve_wait:
                self.resolve_wait.add(("pair", j["id"]))
                self.log(f"{j['label']}: waits for {other} to end, so that the two copies run together (N-F30)")
            return
        ro = read_json(fo["done"]) if os.path.exists(fo["done"]) else None
        if ro is not None and not ro.get("ok"):
            f = self.part_files(self.pw_dir(j), j["label"], 1)
            os.makedirs(self.pw_dir(j), exist_ok=True)
            write_json({"label": j["label"], "part": 1, "ok": False, "status": "skipped", "energies_read": False,
                        "reason": f"{other} is {ro.get('status', 'missing')}: no concurrent pair (section 16, N-F30)"},
                       f["done"])
            self.log(f"{j['label']}: skipped ({other} {ro.get('status', 'missing')}; N-F30)")
            return
        if ro is not None:
            dst = os.path.join(do, "discarded", f"paired_{int(time.time())}")
            os.makedirs(dst, exist_ok=True)
            for k in ("out", "launch", "rc", "log", "done"):
                if os.path.exists(fo[k]):
                    shutil.move(fo[k], dst)
            if os.path.exists(fo["rc"] + ".pid"):
                shutil.move(fo["rc"] + ".pid", dst)
            if os.path.isdir(os.path.join(do, "tmp")):
                shutil.move(os.path.join(do, "tmp"), os.path.join(dst, "tmp"))
            self.cache.pop(jo["id"], None)
            self.log(f"{other}: completed without {j['label']} beside it: moved aside, its measurement not used "
                     f"({os.path.relpath(dst, self.cdir)}); both copies run again together (N-F30)")
        elif os.path.exists(fo["launch"]):
            return                                                          # its end is judged by pw_status first
        if not self.cap_ok(jo, "throughput"):
            return
        for jj in (j, jo):
            if self.pw_prepare(jj):
                self._spawn_part(jj["id"], self.pw_dir(jj), jj["label"], jj["part"], jj["ranks"], "pw",
                                 cpuset=self.free_core_set())

    def free_core_set(self):
        """N-F30: (slot, CPU list) of a half of the cores that no running pw.x copy of this runner uses. A runner
        never inherits running copies from another (the S2 lock), so its own handles are the whole truth."""
        if self.slots_cache is None:
            self.slots_cache = self.be.core_sets()
        busy = {h.get("slot") for h in self.procs.values() if h["kind"] in ("pw", "a2") and h["p"].poll() is None}
        for i, cs in enumerate(self.slots_cache):
            if i not in busy:
                return i, cs
        raise Stop("no free core set for another concurrent pw.x copy (N-F30)")

    def _spawn_part(self, key, d, label, n, ranks, kind, cpuset=None):
        """Every pw.x part outside the queue runs through the committed launcher ehpc/node/s2_run_qe.sh (N-F30): with
        cpuset (slot, CPU list) the copy is confined to those cores (two concurrent copies), else bound as run_qe.sh."""
        f = self.part_files(d, label, n)
        ex = os.path.join(d, "tmp", f"{label}.EXIT")
        if os.path.exists(ex):
            os.remove(ex)                                                   # a restart must not stop at once
        if os.path.exists(os.path.join(d, "exit_request.json")):
            os.replace(os.path.join(d, "exit_request.json"), os.path.join(d, f"exit_request.p{n - 1}.json"))
        slot, cs = cpuset if cpuset else (None, None)
        write_json({"boot": self.boot, "started": utc(), "started_epoch": time.time(), "ranks": ranks, "pid": None,
                    "cpuset": cs, "slot": slot}, f["launch"])
        if self.chainfd is None:
            raise Stop(f"{label}: pw.x outside the queue without the global chain lock (N-6)")
        p = self.be.spawn([self.node.s2_run_qe, os.path.basename(f["in"]), str(ranks), "pw.x"], cwd=d, log=f["log"],
                          rc=f["rc"], env={"CPUSET": cs or ""}, pass_fds=(self.lockfd, self.chainfd))
        L = read_json(f["launch"]); L["pid"] = p.pid; write_json(L, f["launch"])
        self.procs[key] = {"p": p, "kind": kind, "dir": d, "slot": slot}
        self.log(f"pw.x {label}.p{n} started at {ranks} ranks (pid {p.pid})" + (f" on cores {cs}" if cs else ""))

    def request_exit(self, label, d, reason):
        """Sections 13, 16: the reason is recorded (fsynced) before <prefix>.EXIT is created in the outdir. A gate's
        request replaces an earlier 'cap' or 'spot' one (round-4 missed item, N-F37): a running partner that a stopping
        gate stops is killed and its output discarded unread, whatever exit it was already asked for."""
        rq = os.path.join(d, "exit_request.json")
        if os.path.exists(rq):
            old = read_json(rq) or {}
            if reason != "gate" or old.get("reason") == "gate":
                return
            write_json({"reason": "gate", "prior": old.get("reason"), "time": utc()}, rq)
        else:
            write_json({"reason": reason, "time": utc()}, rq)
        os.makedirs(os.path.join(d, "tmp"), exist_ok=True)
        ex = os.path.join(d, "tmp", f"{label}.EXIT")
        if not os.path.exists(ex):
            write_text(f"{reason}\n", ex)
        self.log(f"{label}: exit file created ({reason})")

    # ---- process trees and OOM evidence (N-F23, N-F34)
    def watch_tree(self, key, launch_file, lab, ranks):
        """N-F34 (round-4 R4-C24-2, R4-C1-5): the running part's process tree is recorded at every tick until its
        pw.x ranks are all in it, then every counts_every_s."""
        if key in self.tree_full and time.time() - self.last_counts.get(("tree", key), 0) < self.be.counts_every_s:
            return
        self.last_counts[("tree", key)] = time.time()
        if self.record_tree(lab, launch_file) >= ranks:
            self.tree_full.add(key)

    def record_tree(self, lab, launch_file):
        """N-F23, N-F34: the pids of a running part's process tree (descendants of its wrapper, node /proc), the pw.x
        ranks among them and the CPUs those ranks may use, added to its launch record and to a2_pids.json. Returns the
        number of pw.x ranks recorded."""
        L = read_json(launch_file)
        if not L or not L.get("pid"):
            return 0
        tree = self.be.proc_tree(L["pid"])
        pw = {p for p, c in tree.items() if c == "pw.x"}
        if tree and (not set(tree) <= set(L.get("pids") or []) or not pw <= set(L.get("pw_pids") or [])):
            L["pids"] = sorted(set(L.get("pids") or []) | set(tree))
            L["pw_pids"] = sorted(set(L.get("pw_pids") or []) | pw)
            aff = set()
            for p in pw:
                aff |= self.be.cpus_allowed(p) or set()
            if aff:
                L["affinity"] = cpulist(aff | parse_cpulist(L.get("affinity") or ""))
            write_json(L, launch_file)
            self.a2_note_pids(lab, tree)
        return len(L.get("pw_pids") or [])

    def oom_args(self, L, lab, boot):
        """N-F23 as revised in round 4 (R4-C24-2): with pw.x ranks in the recorded tree, an OOM kill is the part's only
        for one of its own recorded pids; without them (no tree, or only the wrapper, run_qe.sh and mpirun recorded) the
        pw.x task test applies after the part's start, excluding every pid recorded for another part in that boot."""
        if L.get("pw_pids"):
            return {"pids": set(L.get("pids") or [])}
        return {"task": "pw.x", "exclude": self.a2_other_pids(lab, boot)}

    def smoke_record(self, label="s2smoke_ref232_rst", base=None):
        sd = os.path.join(self.cdir, "smoke")
        rd = lambda lab, n: read_json(self.part_files(os.path.join(sd, lab), lab, n)["done"]) or {}
        n1, n3 = rd("s2smoke_ref232_n1", 1), rd("s2smoke_ref232_n3", 1)
        p1, p2 = rd(label, 1), rd(label, 2)
        C = lambda r: r.get("counts") or {}
        ok13 = bool(C(n1).get("job_done") and C(n3).get("job_done"))
        c0 = C(n1).get("n_config", 0) - 1 if ok13 else None
        slope = ok13 and (C(n3)["n_config"] - C(n1)["n_config"]) == 2
        exit_ok = C(p1).get("end") == "exit_stop"
        rf = p1.get("restart_files") or []
        kl1 = (C(p1).get("counters_last") or {}).get("scf_cycles")
        kf2 = (C(p2).get("counters_first") or {}).get("scf_cycles")
        cont = kl1 is not None and kf2 == kl1 + 1
        rep = kl1 is not None and kf2 == kl1
        new2 = C(p2).get("n_config", 0) - (1 if rep else 0)
        total = C(p1).get("n_config", 0) + new2
        reproduces = ok13 and total == C(n3).get("n_config")
        nst2 = (C(n3).get("n_config", 0) - C(p1).get("n_config", 0) - c0) if ok13 else None
        possible = bool(exit_ok and rf and (cont or rep) and reproduces and C(p2).get("job_done"))
        return {"schema": "s2-smoke-1", "layout": {"ranks": p1.get("ranks")}, "label": label,
                "runs": {"n1": {"nstep": 1, "n_config": C(n1).get("n_config"), "end_marker": C(n1).get("end_marker"),
                                "counters_last": C(n1).get("counters_last"), "wall_s": n1.get("wall_s")},
                         "n3": {"nstep": 3, "n_config": C(n3).get("n_config"), "end_marker": C(n3).get("end_marker"),
                                "counters_last": C(n3).get("counters_last"), "wall_s": n3.get("wall_s")},
                         "rst": {"p1": {"nstep": 3, "exit_file": f"tmp/{label}.EXIT", "n_config": C(p1).get("n_config"),
                                        "stopped_by_exit": exit_ok, "exit_marker": C(p1).get("end_marker"),
                                        "restart_files": rf, "counters_last": C(p1).get("counters_last")},
                                 "p2": {"restart_mode": "restart", "nstep": nst2, "n_config": C(p2).get("n_config"),
                                        "counters_first": C(p2).get("counters_first"), "job_done": C(p2).get("job_done")}}},
                "mapping": {"c0": c0, "affine_slope_1": bool(slope), "nstep_first": (K_TOTAL - c0) if slope else None,
                            "restart_continues_counters": cont, "restart_repeats_last": rep,
                            "restart_offset_d": (new2 - (nst2 + c0)) if (ok13 and p2) else None,
                            "nstep_after_restart": "201 - completed - c0", "restart_files": rf,
                            "exit_marker": C(p1).get("end_marker")},
                "exit_file_works": exit_ok, "restart_possible": possible, "energies_read": False}

    def tp_record(self):
        td = os.path.join(self.cdir, "tp")
        runs = {}
        for x in ("np48", "np64", "np32a", "np32b"):
            lab = f"s2tp_ref232_{x}"
            r = read_json(self.part_files(os.path.join(td, lab), lab, 1)["done"]) or {}
            runs[x] = {"n_config": (r.get("counts") or {}).get("n_config"), "wall_s": r.get("wall_s"), "ok": bool(r.get("ok")),
                       "cpuset": r.get("cpuset"), "affinity": r.get("affinity"), "interval": r.get("interval")}
        rate = {}
        for k, x in (("48", "np48"), ("64", "np64")):
            rate[k] = runs[x]["n_config"] / (runs[x]["wall_s"] / 3600.0) if runs[x]["ok"] and runs[x]["wall_s"] else None
        a, b = runs["np32a"], runs["np32b"]
        pair = pair_check(a, b)
        rate["2x32"] = ((a["n_config"] + b["n_config"]) / (max(a["wall_s"], b["wall_s"]) / 3600.0)
                        if a["ok"] and b["ok"] and a["wall_s"] and b["wall_s"] and pair["valid"] else None)
        return {"schema": "s2-throughput-1", "runs": runs, "rate_config_per_node_h": rate, "pair": pair,
                "rule": ">= 1.15 x rate(48), else 48 (the choice is the throughput gate's, scripts/49); the 2x32 rate "
                        "only for two copies that ran together on disjoint cores (N-F30)", "energies_read": False}

    # ---- A2 relaxations (sections 11, 13; I-D1 ... I-D6)
    def a2_checks(self, d, label):
        """N-B9 (round-2 R2-QE-3): the electron count of the part-1 input and the label, checked by scripts/47 in every
        part's header (part n must name <label>.p<n>.in)."""
        if "47_s2_qe.py" in MOCKED:
            return {}
        return {"n_el": self.meta_nel(d, label), "label": label}

    def a2_path(self, label):
        return os.path.join(self.L.a2_dir(self.c, label), f"{label}.a2.json")

    def a2_rec(self, j):
        r = read_json(self.a2_path(j["label"]))
        if r is None:
            r = {"schema": "s2-a2-1", "label": j["label"], "campaign": self.c, "order": j["order"],
                 "a1_cell": {"work_id": j["a1"]}, "layout": None, "parts": [], "reruns_from_zero": 0, "restarts": 0,
                 "interruptions": [], "status": "pending"}
        return r

    def a2_stopped(self):
        """K2 fail, a pending or final step-0 failure, K3 fail_replan or a1_only, or a recorded stop. 'repeat_pending'
        (after STEP0_FIX) is not a stop: C2 runs again from relaxation 1 for the one repeat (I-D1, review-2 F3)."""
        s = self.state
        return (s.get("K2") == "fail" or (s.get("step0") or {}).get("outcome") in ("fail_pending_fix", "fail_final")
                or s.get("K3") in ("fail_replan", "a1_only") or bool(s.get("a2_stopped")))

    def a2_k0_from_files(self, label):
        if self.c not in ("c1", "c2"):
            return False
        r = read_json(self.a2_path(label))
        return bool(r and (r.get("k0_seen") or r.get("n_config", 0) >= 1))

    def a2_status(self, j):
        r = read_json(self.a2_path(j["label"]))
        if r is None:
            return "pending"
        st = r.get("status")
        m = {"complete": "done", "missing": "missing", "killed_by_gate": "killed_by_gate",
             "not_run_gate": "not_run", "not_started_cap": "not_started_cap"}
        if st == "complete":
            self.hold_from_record(r)                                        # N-F36: a STOP not yet raised
        if st in m:
            return m[st]
        h = self.procs.get(j["label"])
        if h is not None and h["p"].poll() is None:
            return "running"
        if not r["parts"]:
            return "pending"
        p = r["parts"][-1]
        d = self.L.a2_dir(self.c, j["label"])
        f = self.part_files(d, j["label"], p["n"])
        if not os.path.exists(f["launch"]):
            return "pending"                                                 # prepared part, not launched
        L = read_json(f["launch"])
        if h is None and not os.path.exists(f["rc"]) and L["boot"] == self.boot and self.be.alive(L.get("pid")):
            return "running"                                                 # launched by an earlier runner
        if self.shutdown:
            return "running"                                                 # judged at the relaunch (N-F21)
        return self.a2_ended(j, r, p, L)

    def a2_outputs(self, label, r):
        d = self.L.a2_dir(self.c, label)
        return [self.part_files(d, label, p["n"])["out"] for p in r["parts"] if os.path.exists(self.part_files(d, label, p["n"])["out"])]

    def a2_monitor(self, j):
        """While a part runs: configuration counts only; the exit file once k = 200 has completed (section 13)."""
        lab = j["label"]
        r = read_json(self.a2_path(lab))
        if r and r.get("parts"):                                            # N-F23, N-F34: every tick until complete
            self.watch_tree(j["id"], self.part_files(self.L.a2_dir(self.c, lab), lab, r["parts"][-1]["n"])["launch"], lab,
                            int((r.get("layout") or {}).get("ranks") or 1))
        t = time.time()
        if t - self.last_counts.get(lab, 0) < self.be.counts_every_s:
            return
        self.last_counts[lab] = t
        outs = self.a2_outputs(lab, r)
        if not outs:
            return
        self.out_watch(lab, self.part_files(self.L.a2_dir(self.c, lab), lab, r["parts"][-1]["n"])["out"])   # N-F13
        rel = self.read_out("parse_relax", lab, "counts", q47.parse_relax, outs, read="counts", k_cap=q47.K_CAP,
                            mapping=self.smoke_map(), ranks=(r.get("layout") or {}).get("ranks"),
                            **self.a2_checks(self.L.a2_dir(self.c, lab), lab))
        n = int(rel.get("n_config") or 0)
        if n >= 1 and not r.get("k0_seen"):
            r["k0_seen"] = True; write_json(r, self.a2_path(lab))
        self.k0[lab] = n >= 1
        if n >= K_TOTAL:
            self.request_exit(lab, self.L.a2_dir(self.c, lab), "cap")

    def a2_record_pids(self, lab, r):
        """N-F23: the pids of a running part's process tree (with its pw.x ranks, N-F34), added to its launch record."""
        if not r or not r.get("parts"):
            return 0
        return self.record_tree(lab, self.part_files(self.L.a2_dir(self.c, lab), lab, r["parts"][-1]["n"])["launch"])

    def a2_note_pids(self, lab, pids):
        """N-F23: the campaign's map label -> boot -> recorded pids (a2_pids.json; it survives a rerun's moves)."""
        p = os.path.join(self.cdir, "a2_pids.json")
        m = read_json(p, {}) or {}
        cur = set((m.get(lab) or {}).get(self.boot) or [])
        if not {int(x) for x in pids} <= cur:
            m.setdefault(lab, {})[self.boot] = sorted(cur | {int(x) for x in pids})
            write_json(m, p)

    def a2_other_pids(self, lab, boot=None):
        """N-F23: the pids recorded in that boot (default this one) for every other part (the other copy's tree)."""
        m = read_json(os.path.join(self.cdir, "a2_pids.json"), {}) or {}
        return {int(x) for k, v in m.items() if k != lab for x in (v.get(boot or self.boot) or [])}

    def a2_ended(self, j, r, p, L):
        lab = j["label"]
        d = self.L.a2_dir(self.c, lab)
        outs = self.a2_outputs(lab, r)
        req = read_json(os.path.join(d, "exit_request.json"))
        if req and req["reason"] == "gate":
            return self.a2_discard(j, r, "killed_by_gate", "stopped by a gate decision (output not read, section 16)")
        rel = self.read_out("parse_relax", lab, "status", q47.parse_relax, outs, read="status", k_cap=q47.K_CAP,
                            mapping=self.smoke_map(), ranks=(r.get("layout") or {}).get("ranks"),
                            **self.a2_checks(d, lab)) if outs else \
            {"usable": True, "parts": [], "n_config": 0, "k_last": -1}
        end = (rel.get("parts") or [{}])[-1].get("end") if rel.get("parts") else None
        k_last = int(rel.get("k_last") if rel.get("k_last") is not None else -1)
        p.update({"ended": utc(), "end": end, "k_last": k_last,
                  "wall_s": (os.path.getmtime(self.part_files(d, lab, p["n"])["rc"]) - L["started_epoch"])
                  if os.path.exists(self.part_files(d, lab, p["n"])["rc"]) else None})
        r["n_config"], r["k_last"] = int(rel.get("n_config") or 0), k_last
        if rel.get("usable") is False:
            return self.a2_rerun(j, r, "parts unusable (counters do not continue)", L)
        if k_last >= K_TOTAL - 1 or end in ("cap", "converged", "bfgs_failed", "scf_failed", "nstep", "other_end",
                                            "pw_error"):
            return self.a2_finalise(j, r, outs)                             # I-D6; early nstep / pw.x error STOP
        res = self.resolution(d)
        if res is not None:
            return self.a2_resolve(j, r, L, res, outs, end)
        since = L.get("started_epoch")
        if L["boot"] == self.boot and not req:
            # I-D6 (round-2 F2, R2-QE-1): an end without JOB DONE in this boot with no exit request is neither a spot
            # reclaim nor a node loss; only an OOM kill of the part's pw.x is an interruption (section 13). Anything
            # else (a QE error on a rank whose output is not written, a crash) may be an 'other end without QE
            # convergence' (section 11: not rerun): a human decides; nothing is rerun automatically
            hit = self.be.oom(self.boot, None, since=since, **self.oom_args(L, lab, self.boot))   # N-F23 (round 4)
            if not hit:
                rcf = self.part_files(d, lab, p["n"])["rc"]
                rcv = open(rcf).read().split()[0] if os.path.exists(rcf) else None
                crash = " (a CRASH file exists)" if os.path.exists(os.path.join(d, "CRASH")) else ""
                raise Stop(f"{lab}: part {p['n']} ended in this boot without JOB DONE, without an exit request and "
                           f"without an OOM kill (exit {rcv}{crash}); section 11 'any other end without QE convergence "
                           f"... is not rerun': resolve with a2/{lab}/RESOLVE holding 'unconverged <note>', 'rerun "
                           f"<note>' (an infrastructure cause) or 'missing <note>' (N-D5)")
            cause = "oom"
        else:
            cause = "spot-notice" if (req and req["reason"] == "spot") else \
                self.cause_of(L["boot"], None, since=since, **self.oom_args(L, lab, L["boot"]))
        r["interruptions"].append({"k": k_last, "time": utc(), "boot": L["boot"], "cause": cause, "part": p["n"]})
        append_jsonl(os.path.join(self.cdir, "interruptions.jsonl"),
                     {"label": lab, "kind": "a2", "k": k_last, "time": utc(), "boot": L["boot"], "cause": cause})
        if end == "exit_stop" and self.restart_usable(d, lab):
            sm = self.smoke_map()
            nst = K_TOTAL - (k_last + 1) - int(sm.get("c0") or 0)
            if nst < 1:
                # with c0 >= 1 a restart late in the run would get nstep 0: nstep 1 is written instead, and the exit
                # file at k = 200 and the parser's cut at k = 200 keep the cap (section 13; review-2 F7, N-F7)
                self.log(f"{lab}: restart nstep {nst} raised to 1 (k = 200 is still enforced by the exit file)")
                nst = 1
            src = self.part_files(d, lab, 1)["in"]
            dst = self.part_files(d, lab, p["n"] + 1)["in"]
            q47.restart_input(src, dst, nst)
            r["parts"].append({"n": p["n"] + 1, "input": os.path.basename(dst), "restart_mode": "restart", "nstep": nst})
            r["restarts"] += 1
            write_json(r, self.a2_path(lab))
            self.log(f"{lab}: interrupted at k = {k_last} ({cause}); restart part {p['n'] + 1} with nstep {nst}")
            return "pending"
        return self.a2_rerun(j, r, f"no usable restart data ({cause})", L)

    def restart_usable(self, d, label):
        """I-D5: the smoke test showed a restart is possible, and every restart file exists for this prefix."""
        sm = self.smoke_rec()
        if not sm.get("restart_possible"):
            return False
        files = (sm.get("mapping") or {}).get("restart_files") or []
        return bool(files) and all(os.path.exists(os.path.join(d, "tmp", f.replace("{prefix}", label))) for f in files)

    def a2_discard(self, j, r, status, why):
        d = self.L.a2_dir(self.c, j["label"])
        dst = os.path.join(d, "discarded", status)
        os.makedirs(dst, exist_ok=True)
        for f in os.listdir(d):
            if f.endswith((".out", ".runlog")) or f == "tmp":
                shutil.move(os.path.join(d, f), os.path.join(dst, f))
        r.update({"status": status, "status_reason": why})
        write_json(r, self.a2_path(j["label"]))
        self.log(f"{j['label']}: {status} ({why})")
        return {"killed_by_gate": "killed_by_gate", "missing": "missing"}[status]

    def a2_rerun(self, j, r, why, L):
        lab = j["label"]
        d = self.L.a2_dir(self.c, lab)
        r["reruns_from_zero"] += 1
        if r["reruns_from_zero"] > A2_RERUNS_FROM_ZERO:
            return self.a2_discard(j, r, "missing", f"{why}; no rerun from k = 0 left (section 13)")
        dst = os.path.join(d, "discarded", f"r{r['reruns_from_zero']}")
        os.makedirs(dst, exist_ok=True)
        p1 = os.path.basename(self.part_files(d, lab, 1)["in"])
        for f in os.listdir(d):
            if f in (p1, os.path.basename(self.a2_path(lab)), f"{lab}.meta.json", "discarded"):
                continue
            shutil.move(os.path.join(d, f), os.path.join(dst, f))           # unread
        r["parts"] = [{"n": 1, "input": p1, "restart_mode": None, "nstep": r.get("nstep_first")}]
        r.pop("k0_seen", None); r["n_config"] = 0
        write_json(r, self.a2_path(lab))
        self.log(f"{lab}: {why}: rerun from k = 0 ({r['reruns_from_zero']} of {A2_RERUNS_FROM_ZERO})")
        return "pending"

    def a2_resolve(self, j, r, L, res, outs, end):
        """N-D5 for A2 (round-2 F2): the operator's RESOLVE after a STOP on an unexplained end in this boot:
        'unconverged <note>' (section 11: an end without QE convergence, not rerun), 'rerun <note>' (an infrastructure
        cause: a rerun from k = 0 with the identical input, counted against the two of section 13) or 'missing'."""
        word, note = res
        lab = j["label"]
        append_jsonl(os.path.join(self.cdir, "interruptions.jsonl"), {"label": lab, "kind": "a2", "time": utc(),
                                                                       "boot": self.boot, "cause": f"operator {word}: {note}"[:200]})
        if word == "unconverged":
            return self.a2_finalise(j, r, outs, override={
                "outcome": "unconverged_early", "end": f"{end or 'killed'} (operator)", "stop": False,
                "reason": f"operator: {note} (section 11: an end without QE convergence, not rerun)"[:300]})
        if word == "rerun":
            r["interruptions"].append({"k": r.get("k_last"), "time": utc(), "boot": L["boot"],
                                       "cause": f"operator: {note}"[:120], "part": r["parts"][-1]["n"]})
            return self.a2_rerun(j, r, f"operator rerun ({note[:80]})", L)
        if word == "missing":
            return self.a2_discard(j, r, "missing", f"operator: {note}"[:200])
        raise Stop(f"{lab}: RESOLVE must hold 'unconverged <note>', 'rerun <note>' or 'missing <note>'")

    def a2_finalise(self, j, r, outs, override=None):
        lab = j["label"]
        rel = self.read_out("parse_relax", lab, "end_rule", q47.parse_relax, outs, read="end_rule", k_cap=q47.K_CAP,
                            mapping=self.smoke_map(), ranks=(r.get("layout") or {}).get("ranks"),
                            **self.a2_checks(self.L.a2_dir(self.c, lab), lab))
        er = q47.end_rule(rel) if override is None else override
        walls = [p.get("wall_s") or 0.0 for p in r["parts"]]
        r.update({"status": "complete", "n_config": int(rel.get("n_config") or 0), "k_last": rel.get("k_last"),
                  "qe_converged": er["outcome"] == "accepted_converged", "converged_at_k": rel.get("converged_at_k"),
                  "end_rule": {"outcome": er["outcome"], "dF_200_180_meV": er.get("dF_200_180_meV"),
                               "end": er.get("end"), "stop": bool(er.get("stop")), "reason": er.get("reason"),
                               **({"stop_raised": False} if er.get("stop") else {})},       # N-F36
                  "wall_h": sum(walls) / 3600.0,
                  "min_per_config": (sum(walls) / 60.0 / max(1, int(rel.get("n_config") or 1)))})
        if rel.get("usable") is not False and rel.get("k_last") is not None:
            r["final_geometry"] = self.a2_write_final(j, r, outs)      # section 11 checks (I-F1); positions only
        write_json(r, self.a2_path(lab))
        self.walls.setdefault("a2", {})[lab] = r["wall_h"]
        if r["n_config"]:
            self.walls.setdefault("a2_config", {})[lab] = r["wall_h"] / r["n_config"]       # wall h per configuration
        self.log(f"{lab}: complete, {r['n_config']} configurations, end rule {er['outcome']}")
        if er.get("stop"):
            # N-F20 (round-3 R3-1): the STOP is held until the gates on ended relaxations have applied (a gate that
            # stops A2 puts the exit file on a running partner at once); nothing costly starts meanwhile. N-F36 (round
            # 4): the record says stop_raised false until CAMPAIGN_STOPPED holds it, so a shutdown or another STOP in
            # the hold cannot lose it
            self.hold_from_record(r)
        return "done"

    def held_reason(self, r):
        er = r.get("end_rule") or {}
        return f"{r['label']}: {er.get('reason') or 'the end rule stops the campaign'} (I-48)"

    def hold_from_record(self, r):
        """N-F20, N-F36: a complete A2 record whose end rule asked for a STOP not yet raised holds that STOP."""
        er = r.get("end_rule") or {}
        if not (er.get("stop") and er.get("stop_raised") is False):
            return
        why = self.held_reason(r)
        self.held_labels[why] = r["label"]
        if why not in self.pending_stop:
            self.pending_stop.append(why)
            self.log(f"STOP held (N-F20): {why}; the gates and checks ready now run first")

    def a2_start_atoms(self, j):
        """The A2 start: the S2-relaxed host for host_R, else the A1 relaxed cell (section 11); the reference vacancy
        cell for the self-test's reference rows."""
        if j.get("ref"):
            return self.ref_cells()[0]
        c1 = "c1"
        return read(self.relaxed_path(wid_of(j["member"], "host") if j["cell_kind"] == "host" else j["a1"], c1))

    def a2_write_final(self, j, r, outs):
        """Positions of the last configuration (scripts/47 read='final_geom': no energy is read) on the A2 start as
        template, written as <label>.final.extxyz beside the parts (geometry only, no calculator results)."""
        lab = j["label"]
        rel = self.read_out("parse_relax", lab, "final_geom", q47.parse_relax, outs, read="final_geom",
                            k_cap=q47.K_CAP, mapping=self.smoke_map(), ranks=(r.get("layout") or {}).get("ranks"),
                            **self.a2_checks(self.L.a2_dir(self.c, lab), lab))
        k = rel.get("k_last")
        pos = (rel.get("positions_A") or {}).get(k)
        if pos is None:
            raise Stop(f"{lab}: no final positions at k = {k}")
        tpl = self.a2_start_atoms(j)
        sym = rel.get("symbols")
        if sym is not None and list(sym) != list(tpl.get_chemical_symbols()):
            raise Stop(f"{lab}: the final configuration's atoms differ from the A2 start")
        f = os.path.join(self.L.a2_dir(self.c, lab), f"{lab}.final.extxyz")
        c46.write_cell(f, c46.atoms_with_positions(tpl, pos))
        return {"file": os.path.basename(f), "k": int(k), "sha256": sha256_file(f)}

    # ---- section 11 final-geometry checks (I-F1; geometry only, scripts/46 validate-a2)
    def a2v_out(self, label):
        return os.path.join(self.L.a2_dir(self.c, label), f"{label}.validity_final.json")

    def a2v_status(self, j, st):
        """done once validity_final is recorded; skipped (no validity_final: the check is not evaluated) if the
        relaxation ended without a complete output, or completed without a configuration to check (k_last None, e.g.
        an SCF failure at k = 0: the end rule already makes the cell unconverged; round-2 R2V-2), or if its section 11
        partner has ended without a final geometry (missing, not run, killed, or complete without one: check 5
        cannot be evaluated and the quartet is invalid through the missing partner; round-2 R2V-1); otherwise
        pending (deps_state lets it run once the relaxation is done and its partner has ended)."""
        r = read_json(self.a2_path(j["label"])) or {}
        if r.get("validity_final") is not None and os.path.exists(self.a2v_out(j["label"])):
            return "done"
        own = st.get("a2:" + j["label"])
        if own is None or (_is_terminal(own) and own != "done"):
            return "skipped"
        if own == "done" and not r.get("final_geometry"):
            return "skipped"                                                # nothing to check (R2V-2)
        par = j.get("parent")
        if par:
            ps = st.get("a2:" + par)
            if ps is not None and _is_terminal(ps):
                pr = read_json(self.a2_path(par)) or {}
                if pr.get("status") != "complete" or not pr.get("final_geometry"):
                    return "skipped"                                        # partner without a geometry (R2V-1)
        return "pending"

    def a2v_files(self, j):
        lab = j["label"]
        if j.get("ref"):
            d = os.path.join(self.cdir, "a2v_ref")
            hf, rf = os.path.join(d, "host233.extxyz"), os.path.join(d, "region_ref233_B136.json")
            if not os.path.exists(rf):
                host = c46.write_cell(hf, c46.ref_context().host)
                c46.dump_public(c46.build_region(host, "ref233", 136), rf)
            sf = os.path.join(d, "vac232.extxyz")
            if not os.path.exists(sf):
                c46.write_cell(sf, self.ref_cells()[0])
            return {"start": sf, "host_relaxed": hf, "region": rf, "pair": None, "parent_final": hf,
                    "final": os.path.join(self.L.a2_dir(self.c, lab), f"{lab}.final.extxyz")}
        c1, h, L_, jj = "c1", j["member"], j["L"], j["j"]
        a1 = wid_of(h, "host") if j["cell_kind"] == "host" else j["a1"]
        par = None
        if j.get("parent"):
            pr = read_json(self.a2_path(j["parent"])) or {}
            pf = os.path.join(self.L.a2_dir(self.c, j["parent"]), f"{j['parent']}.final.extxyz")
            if pr.get("status") == "complete" and pr.get("final_geometry") and os.path.exists(pf) and \
                    sha256_file(pf) == pr["final_geometry"]["sha256"]:
                par = pf
        return {"start": self.L.cell_file(c1, a1, "start"), "host_relaxed": self.L.cell_file(c1, wid_of(h, "host"), "relaxed"),
                "region": self.L.region(c1, h, L_, jj),
                "pair": self.L.pair(c1, h, j["token"], jj, 0) if j.get("token") else None, "parent_final": par,
                "final": os.path.join(self.L.a2_dir(self.c, lab), f"{lab}.final.extxyz")}

    def run_a2v(self, j):
        lab = j["label"]
        r = read_json(self.a2_path(lab)) or {}
        files = self.a2v_files(j)
        fg = r.get("final_geometry") or {}
        if not fg:
            return                                                          # nothing to check (a2v_status: skipped)
        if not os.path.exists(files["final"]) or sha256_file(files["final"]) != fg.get("sha256"):
            raise Stop(f"{lab}: the recorded final geometry is missing or does not match its sha256 (section 11)")
        if j.get("parent") and not files.get("parent_final"):
            raise Stop(f"{lab}: the partner {j['parent']} is complete but its final geometry is missing or does not "
                       f"match its sha256 (section 11)")
        job = {"action": "validate-a2", "campaign": self.c, "root": self.node.root, "member": j.get("member"),
               "label": lab, "kind": j["cell_kind"], "site": j["j"], "token": j.get("token"), "leg": j.get("leg"),
               "parent_label": j.get("parent"), "files": files, "out": self.a2v_out(lab)}
        jf = os.path.join(self.cdir, "jobs46", f"a2v_{lab}.json")
        write_json(job, jf)
        rc = self.be.run46("validate-a2", jf, os.path.join(self.cdir, "jobs46", "jobs46.log"))
        out = read_json(self.a2v_out(lab))
        if self.shutdown and (rc != 0 or out is None):
            self.log(f"validate-a2 {lab}: interrupted by the shutdown (exit {rc}; N-F21): pending")
            return
        if rc != 0 or out is None:
            raise Stop(f"scripts/46 validate-a2 for {lab} ended with exit {rc} without its output (N-9)")
        v = out["validity"]
        r["validity_final"] = {"valid": bool(v["valid"]), "failed": list(v["failed"]),
                               "file": os.path.basename(self.a2v_out(lab)), "sha256": sha256_file(self.a2v_out(lab)),
                               "parent": j.get("parent"), "parent_final": bool(files.get("parent_final"))}
        write_json(r, self.a2_path(lab))
        self.log(f"{lab}: section 11 final-geometry checks {'passed' if v['valid'] else 'FAILED ' + str(v['failed'])}")

    def a2_stop_all(self, why):
        for lab, h in list(self.procs.items()):
            if h["kind"] == "a2" and h["p"].poll() is None:
                self.request_exit(lab, h["dir"], "gate")
        self.log(f"A2 stopped ({why}): running parts stopped by their exit files")

    def a2_phase(self, jobs, st):
        a2 = sorted([j for j in jobs if j["kind"] == "a2"], key=lambda x: x["order"])
        for j in a2:
            if st[j["id"]] == "running":
                self.a2_monitor(j)
        if self.a2_stopped():
            for j in a2:
                if st[j["id"]] == "running":
                    # a 'cap' or 'spot' request is replaced by the gate's (round-4 missed item, N-F37)
                    self.request_exit(j["label"], self.L.a2_dir(self.c, j["label"]), "gate")
                elif st[j["id"]] == "pending":
                    r = self.a2_rec(j)
                    if r["parts"]:
                        # a relaxation between parts (a spot restart prepared) is killed: its outputs and restart data
                        # go aside unread like those of a running partner (section 16; round-4 R4-C24-3, N-F37)
                        self.a2_discard(j, r, "killed_by_gate", "A2 stopped by a gate decision (output not read, "
                                                                "section 16)")
                    else:
                        r["status"] = "not_run_gate"
                        r["status_reason"] = "A2 stopped by a gate decision"
                        write_json(r, self.a2_path(j["label"]))
            return
        if self.held() or self.stopping or self.pending_stop:
            return
        lay = self.state.get("a2_layout") or "48"
        copies, ranks = (2, 32) if lay == "2x32" else (1, int(lay))
        busy = sum(1 for j in a2 if st[j["id"]] == "running")
        for j in a2:
            s = st[j["id"]]
            if s != "pending":
                continue
            r = self.a2_rec(j)
            if busy >= copies:
                return
            # every planned relaxation runs whatever the validity of its A1 start (I-10 as revised, review F5); the
            # restart part of a started relaxation is checked against the cap with the expected time of the
            # configurations still allowed (I-F7), a fresh start with the expected time of a whole relaxation
            started = any(p.get("started") for p in r["parts"])
            exp = None
            if started:
                left = max(1, K_TOTAL - int(r.get("n_config") or 0))
                exp = left * g49.expected_hours("a2_config", list(self.walls.get("a2_config", {}).values()))
            if not self.chain_lock_ok():
                return                                                       # a queue or a foreign pw.x runs (N-6)
            if not self.cap_ok(j, "a2", expected_h=exp):
                r["status"] = "not_started_cap"
                write_json(r, self.a2_path(j["label"]))
                return
            self.a2_launch(j, r, ranks, lay)
            busy += 1; st[j["id"]] = "running"

    def a2_launch(self, j, r, ranks, lay):
        lab = j["label"]
        d = self.L.a2_dir(self.c, lab)
        os.makedirs(d, exist_ok=True)
        if not r["parts"]:
            sm = self.smoke_map()
            nst = sm.get("nstep_first")
            if not sm.get("affine_slope_1") or not nst:
                raise Stop(f"{lab}: no verified nstep mapping from the smoke tests (X-3)")
            if j.get("ref"):
                vac, free = self.ref_cells()
                at = vac
            else:
                c1 = "c1"
                if j["cell_kind"] == "host":
                    at = read(self.relaxed_path(j["a1"], c1))
                    free = read_json(self.L.region(c1, j["member"], j["L"], j["j"]))["free"]
                else:
                    at = read(self.relaxed_path(j["a1"], c1))
                    free = c46.load_record(self.L.record(c1, j["a1"]), blind=True)["free"]
            q47.write_input(at, lab, d, kind="relax", free=free, nstep=nst, ranks=ranks, campaign=self.c,
                            cell={"work_id": j.get("a1"), "free_from": "region" if j["cell_kind"] == "host" else "A1 record"})
            os.replace(os.path.join(d, f"{lab}.in"), self.part_files(d, lab, 1)["in"])
            r.update({"layout": {"name": lay, "ranks": ranks, "copies": 2 if lay == "2x32" else 1}, "nstep_first": nst,
                      "parts": [{"n": 1, "input": f"{lab}.p1.in", "restart_mode": None, "nstep": nst}]})
            write_json(r, self.a2_path(lab))
        n = r["parts"][-1]["n"]
        # N-F30: at 2x32 every part gets the half of the cores no running copy uses (a relaxation that replaces a
        # finished copy takes its half); a single copy is bound as run_qe.sh binds
        self._spawn_part(lab, d, lab, n, ranks, "a2", cpuset=self.free_core_set() if lay == "2x32" else None)
        r["parts"][-1]["started"] = utc()
        write_json(r, self.a2_path(lab))

    # ---- the main loop
    def run(self):
        os.makedirs(self.cdir, exist_ok=True)
        self.take_lock()
        self.boot = self.be.boot_id()
        signal.signal(signal.SIGTERM, lambda *_: setattr(self, "shutdown", True))      # N-F10: an interruption
        signal.signal(signal.SIGINT, lambda *_: setattr(self, "term", True))           # the operator's STOP
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
        self.log(f"start {self.c}; boot {self.boot[:8]}; pid {os.getpid()}; mocked {MOCKED or 'none'}")
        if os.path.exists(os.path.join(self.cdir, "CAMPAIGN_DONE")):
            self.log("CAMPAIGN_DONE exists: nothing to do"); return 0
        if not self.be.mock and os.path.realpath(HERE) != os.path.realpath(os.path.join(self.node.checkout, "scripts")):
            # N-F11 (round-2 S4): the code that runs is the code of the recorded checkout
            self.log(f"refused: this runner is not the one of the S2 checkout {self.node.checkout}")
            return 2
        if os.path.exists(os.path.join(self.cdir, "CAMPAIGN_STOPPED")):
            self.log(f"relaunch after a STOP: {open(os.path.join(self.cdir, 'CAMPAIGN_STOPPED')).read().strip()[:200]}")
            os.replace(os.path.join(self.cdir, "CAMPAIGN_STOPPED"),
                       os.path.join(self.cdir, f"CAMPAIGN_STOPPED.{int(time.time())}"))
            self.was_stopped = True
        rc = 0
        try:
            self.state = self.load_state()
            self.check_commit()
            why = self.preconditions()
            if why:
                self.set_campaign("not_run", reason=why)
                self.log(f"{self.c} not run: {why} (N-D11)")
                return 0
            self.load_walls()
            self.load_cap()
            write_text(f"{utc()} S2 {self.c}\n", self.node.keep_alive)       # section 16 keep-alive
            self.ka_written = True
            self.boot_record(); self.heartbeat(force=True)
            self.start_poller()
            self.set_campaign("running")
            rc = self.loop()
        except Stop as e:
            self._guard(self.begin_stop, str(e)); rc = self._guard(self.drain) or 3
        except BaseException as e:                                          # noqa: BLE001 (a Python exception is a STOP)
            self._guard(self.log, "unexpected error:\n" + traceback.format_exc())
            self._guard(self.begin_stop, f"unexpected error {type(e).__name__}: {e}"); self._guard(self.drain); rc = 1
        finally:
            if self.poller is not None and self.poller.poll() is None:
                self._guard(self.poller.terminate)
                self._guard(self.poller.wait, 10)
            if self.ka_written:
                # the runner never exits while its campaign goes on: whatever ended it, KEEP_ALIVE goes (round-2 F1)
                self.drop_keep_alive()
        if "mace" in sys.modules:
            self._guard(self.log, "FAIL: 'mace' was imported by the runner"); rc = rc or 1
        return rc

    def drain(self):
        """N-D4: after a STOP nothing starts; wait for the running children, keeping the heartbeat and the poller."""
        while True:
            ended = [(k, h) for k, h in self.procs.items() if h["kind"] == "a2" and h["p"].poll() is not None]
            for lab, h in ended:
                self._guard(self.settle_gate_kill, lab, h["dir"])
            if not self.running_any():
                break
            try:
                self.heartbeat()
                for lab, h in list(self.procs.items()):
                    if h["kind"] == "a2" and h["p"].poll() is None and self.notice_done:
                        self.request_exit(lab, h["dir"], "spot")
            except Exception:                                               # noqa: BLE001
                pass
            self.be.sleep(self.be.tick)
            if os.path.exists(os.path.join(self.node.spot, f"notice.{self.boot}")):
                self.notice_done = True
        if self.stop_written:
            self._guard(self.log, "STOP: no child running; runner exits (stopped)")
            return 3
        if self.shutdown and not self.term:
            self._guard(self.log, "shutdown: no child running; runner exits (campaign still 'running', N-F10)")
            return 4
        self._guard(self.log, "STOP: no child running; runner exits")
        return 3

    def settle_gate_kill(self, lab, d):
        """N-F20: an A2 part that ended after a gate's exit request (during a drain) is recorded killed_by_gate, its
        outputs moved aside unread (section 16), as a2_ended does at the next look."""
        req = read_json(os.path.join(d, "exit_request.json"))
        r = read_json(self.a2_path(lab))
        if req and req.get("reason") == "gate" and r and r.get("status") not in TERMINAL_A2:
            self.a2_discard({"label": lab}, r, "killed_by_gate", "stopped by a gate decision (output not read, section 16)")

    def loop(self):
        while True:
            try:
                self.housekeeping()
                if self.stopping:
                    return self.drain()
                self.graph_now()
                st = self.statuses()
                if self.shutdown:
                    self.be.sleep(self.be.tick)
                    continue                                               # the shutdown begins at housekeeping (N-F21)
                done = all(_is_terminal(s) for s in st.values())
                if self.pending_stop and (done or not self.free_ready(st)):
                    if self.c in ("c2", "c4") and self.a2_stopped():
                        self.a2_stop_all("a gate decision before the held STOP")
                    raise Stop("; ".join(self.pending_stop))               # N-F20: after the free jobs
                if done:
                    if not self.running_any():
                        self.finish(); return 0
                else:
                    self.schedule(st)
                self.running_any()
            except Stop as e:
                self.begin_stop(str(e))
                return self.drain()
            self.be.sleep(self.be.tick)


# ---------------------------------------------------------------- archive (laptop; interface spec 5.5)
def _gz(src, dst):
    with open(src, "rb") as fi, open(dst + ".tmp", "wb") as fo:
        with gzip.GzipFile(filename="", mode="wb", fileobj=fo, mtime=0) as gz:
            shutil.copyfileobj(fi, gz)
    os.replace(dst + ".tmp", dst)


def casefold_dupes(names):
    """Names that fold to the same lower-case string (N-F15): [[name, name, ...], ...]."""
    by = {}
    for x in names:
        by.setdefault(str(x).lower(), []).append(str(x))
    return [sorted(v) for v in by.values() if len(set(v)) > 1]


def _archive_casefold(cw, jobs):
    """N-F15: refuse a pulled campaign holding two source names that differ only in case (on a case-sensitive stage),
    and the trace such a pair leaves on a case-insensitive one: a gate file whose 'gate' field is not its name, a
    gates_applied marker whose 'id' is not its file name."""
    for d in [cw, jobs] + [os.path.join(r_, x) for top in (cw, jobs) if os.path.isdir(top)
                           for r_, ds, _ in os.walk(top) for x in ds]:
        if os.path.isdir(d):
            bad = casefold_dupes(os.listdir(d))
            if bad:
                raise S2Error(f"{os.path.relpath(d, os.path.dirname(cw))}: names that differ only in case {bad} "
                              f"(N-F15): the archive refuses them")
    for f in sorted(glob.glob(os.path.join(cw, "gates", "*.json"))):
        g = (read_json(f) or {}).get("gate")
        if g is not None and g != os.path.basename(f)[:-5]:
            raise S2Error(f"gates/{os.path.basename(f)} holds the output of gate {g!r} (a case-fold collision, N-F15)")
    for f in sorted(glob.glob(os.path.join(cw, "gates_applied", "*.json"))):
        b = os.path.basename(f)
        if b.endswith((".gate.json", ".inputs.json")):
            continue
        i = (read_json(f) or {}).get("id")
        if i is not None and re.sub(r"[^A-Za-z0-9_.-]", "_", i) + ".json" != b:
            raise S2Error(f"gates_applied/{b} is the marker of {i!r} (a case-fold collision, N-F15)")


def archive(stage, campaign, out):
    """One pulled campaign (<stage>/work = /data/work/s2, <stage>/jobs/s2<c> = /data/jobs/s2<c>) into the
    repository layout of interface spec 5.2. Refuses a duplicated label, a record whose sha256 does not match its
    file, names that differ only in case (N-F15), and any written JSON or log that fails the hygiene check."""
    cw, jobs = os.path.join(stage, "work", campaign), os.path.join(stage, "jobs", f"s2{campaign}")
    if not os.path.isdir(cw):
        raise S2Error(f"no pulled campaign directory for {campaign}")
    _archive_casefold(cw, jobs)
    if os.path.isdir(out) and os.listdir(out):
        raise S2Error("the archive directory exists and is not empty")
    os.makedirs(out, exist_ok=True)
    n = Counter()

    def pub(obj, rel):
        c46.dump_public(obj, os.path.join(out, rel)); n["json"] += 1

    for f in ("campaign.json", "graph.json", "upf_check.json", "mace_check.json", "nodescripts_check.json", "smoke.json",
              "smoke2.json", "throughput.json", "completeness.json", "state_end.json", "ledger.json", "HARD_CAP.json"):
        if os.path.exists(os.path.join(cw, f)):
            pub(read_json(os.path.join(cw, f)), f)
    for f, rel in (("interruptions.jsonl", "interruptions.json"), ("runner_reads.jsonl", "runner_reads.json")):
        p = os.path.join(cw, f)
        pub([json.loads(x) for x in open(p)] if os.path.exists(p) else [], rel)
    for sub in ("gates", "gates_applied", "regions", "pairs", "g1"):
        for f in sorted(glob.glob(os.path.join(cw, sub, "*.json"))):
            pub(read_json(f), os.path.join(sub, os.path.basename(f)))
    structs = []
    for rp in sorted(glob.glob(os.path.join(cw, "cells", "*", "record.json"))):
        rec = read_json(rp)
        wid = os.path.basename(os.path.dirname(rp))
        for k, rel in (rec.get("files") or {}).items():
            fp = os.path.join(cw, rel)
            if not os.path.exists(fp) or sha256_file(fp) != (rec.get("sha256") or {}).get(k):
                raise S2Error(f"{wid}: the {k} file does not match the sha256 of its record")
            structs.append(rel)
        pub(rec, os.path.join("records", f"{wid}.json"))
    structs += sorted(os.path.relpath(f, cw) for f in glob.glob(os.path.join(cw, "g1", "*.extxyz")))
    for d in sorted(glob.glob(os.path.join(cw, "a2", "*"))):                # A2 final geometries (section 11 checks)
        lab = os.path.basename(d)
        f = os.path.join(d, f"{lab}.final.extxyz")
        if os.path.exists(f):
            fg = (read_json(os.path.join(d, f"{lab}.a2.json")) or {}).get("final_geometry") or {}
            if sha256_file(f) != fg.get("sha256"):
                raise S2Error(f"{lab}: the final geometry does not match the sha256 of its A2 record")
            structs.append(os.path.relpath(f, cw))
    for f in sorted(glob.glob(os.path.join(cw, "discarded", "step0_attempt1_*", "gates*", "*.json"))):
        sub = os.path.basename(os.path.dirname(f))                          # the attempt-1 gate files (I-D1)
        pub(read_json(f), os.path.join("step0_attempt1", sub, os.path.basename(f)))
    with open(os.path.join(out, "structures.tar.gz.tmp"), "wb") as fo:
        with gzip.GzipFile(filename="", mode="wb", fileobj=fo, mtime=0) as gz:
            with tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tf:
                for rel in sorted(set(structs)):
                    ti = tf.gettarinfo(os.path.join(cw, rel), arcname=rel)
                    ti.mtime, ti.uid, ti.gid, ti.uname, ti.gname = 0, 0, 0, "", ""
                    with open(os.path.join(cw, rel), "rb") as fh:
                        tf.addfile(ti, fh)
    os.replace(os.path.join(out, "structures.tar.gz.tmp"), os.path.join(out, "structures.tar.gz"))
    raw = os.path.join(out, "raw")
    os.makedirs(raw, exist_ok=True)
    seen = set()

    def once(lab):
        if lab in seen:
            raise S2Error(f"label {lab} occurs twice in the pulled campaign")
        seen.add(lab)

    for d in sorted(glob.glob(os.path.join(jobs, "*"))):
        if not os.path.isdir(d):
            continue
        lab = os.path.basename(d); once(lab)
        for f in sorted(os.listdir(d)):
            src = os.path.join(d, f)
            if not os.path.isfile(src) or not f.startswith(lab + "."):
                continue
            if f.endswith(".meta.json"):
                pub(read_json(src), os.path.join("raw", f))
            elif f.endswith(".gaveup"):
                shutil.copyfile(src, os.path.join(raw, f)); n["marker"] += 1
            elif re.fullmatch(re.escape(lab) + r"\.(in|out|out\.try\d+)", f):
                _gz(src, os.path.join(raw, f + ".gz")); n["raw"] += 1
    for d in sorted(glob.glob(os.path.join(cw, "a2", "*"))):
        lab = os.path.basename(d); once(lab)
        for f in sorted(os.listdir(d)):
            src = os.path.join(d, f)
            if f in (f"{lab}.a2.json", f"{lab}.validity_final.json"):
                pub(read_json(src), os.path.join("raw", f))
            elif re.fullmatch(re.escape(lab) + r"\.p\d+\.(in|out)", f):
                _gz(src, os.path.join(raw, f + ".gz")); n["raw"] += 1
    if os.path.exists(os.path.join(cw, "campaign.log")):
        lines = []
        for x in open(os.path.join(cw, "campaign.log")):
            lines.append("[line removed: hygiene]\n" if c46.hygiene_violations(x) else x)
        write_text("".join(lines), os.path.join(out, "logs", "campaign.log"))
        if c46.hygiene_violations("".join(lines)):
            raise S2Error("the scrubbed log still fails the hygiene check")
    return {"campaign": campaign, "counts": dict(n), "labels": len(seen), "structures": len(set(structs))}


# ---------------------------------------------------------------- status (never an energy)
def cmd_status(root):
    node, L = Node(root), c46.Layout(kind="node", root=root)
    s = read_json(node.state) or {}
    print("state:", json.dumps({k: s.get(k) for k in ("commit", "a2_layout", "G1", "gateN", "sr_stop", "n", "pose",
                                                        "step0", "K2", "K3", "cuts", "campaigns")}, sort_keys=True))
    for c in CAMPAIGNS:
        cd = L.campaign_dir(c)
        if not os.path.isdir(cd):
            continue
        cj = read_json(os.path.join(cd, "campaign.json")) or {}
        recs = len(glob.glob(os.path.join(cd, "cells", "*", "record.json")))
        sp = Counter()
        for d in glob.glob(os.path.join(node.jobs, f"s2{c}", "*")):
            lab = os.path.basename(d)
            if os.path.exists(os.path.join(d, f"{lab}.in")):
                sp[q47.sp_status(d, lab, meta=read_json(os.path.join(d, f"{lab}.meta.json"))).get("status")] += 1
        a2 = Counter((read_json(f) or {}).get("status") for f in glob.glob(os.path.join(cd, "a2", "*", "*.a2.json")))
        print(f"{c}: {cj.get('status')}; MACE records {recs}; single points {dict(sp)}; A2 {dict(a2)}"
              + ("; CAMPAIGN_STOPPED" if os.path.exists(os.path.join(cd, "CAMPAIGN_STOPPED")) else ""))
        lg = os.path.join(cd, "campaign.log")
        if os.path.exists(lg):
            for x in open(lg).read().splitlines()[-8:]:
                print("   ", x[:200])
    led = ledger(root)
    print(f"node-hours: H_spent {led['H_spent_h']:.2f} h; complete {led['complete']} {led['problems'] or ''}")
    return 0


# ---------------------------------------------------------------- self-test stubs: scripts/46 jobs, pw.x, backend
UPF_MD5 = {"Pb": "1cf8f5e18580e6a90a35f98a53d336de", "I": "21b6b539e0050b62c62ace6be4e6e5e0",
           "C": "1fdd950c42eb37d8afe3dd2f8d12311e", "H": "3f4114867bd07edc7f1424d066fc1888",
           "N": "ada94e3ed05223de5319d0572dc76806", "Cs": "ce91a30752c48add39cf6ac6342f9330",
           "Sr": "062293b6b65f9744728f4999ca8ab72f"}


def _mock_cfg(sysroot):
    return read_json(os.path.join(sysroot, "mock", "config.json"), {}) or {}


def mock46_main(action, jobfile):
    """The scripts/46 CLI contract for the self-test when scripts/46 is absent: reference/synthetic cells only
    (N-1), a 'relaxation' that returns its start (a harmonic well centred on it), records as interface spec 4.3."""
    job = read_json(jobfile)
    if action == "hang":                                     # the self-test's interrupted MACE job (case g)
        d = c46.Layout(kind="node", root=job["root"]).cell_dir(job["campaign"], job["work_id"])
        write_text("FIRE partial log (a partial output)\n", os.path.join(d, "fire.log"))
        time.sleep(3600)
        return 1
    if job["member"] not in ("ref233", "synthetic"):
        print("refused: the stub evaluates only reference or synthetic cells (N-1)"); return 3
    root = job["root"]; c = job["campaign"]
    L = c46.Layout(kind="node", root=root)
    cdir = L.campaign_dir(c)
    sysroot = os.path.dirname(root)
    cfg = _mock_cfg(sysroot)
    boot = open(os.path.join(sysroot, "mock", "boot_id")).read().strip()
    ctx = c46.ref_context()

    def relaxed(wid):
        return read(os.path.join(L.cell_dir(c, wid), "relaxed.extxyz"))

    if action in ("relax-host", "relax"):
        wid = job["work_id"]; d = L.cell_dir(c, wid)
        start = ctx.host.copy() if action == "relax-host" else read(os.path.join(d, "start.extxyz"))
        if action == "relax-host":
            write(os.path.join(d, "start.extxyz"), start, format="extxyz")
        write(os.path.join(d, "relaxed.extxyz"), start, format="extxyz")
        free = None
        if job.get("region"):
            reg = read_json(job["region"])
            if job["kind"] in ("D", "DV"):
                pr = read_json(L.pair(c, job["member"], job["token"], job["site"], int(job["start"][1:])))
                leg = pr["legs"][job["leg"]]
                built = types.SimpleNamespace(old_to_new={int(k): v for k, v in leg["old_to_new"].items()}, members=leg["members"])
                free = c46.free_in_cell(reg, job["kind"], built=built)
            else:
                free = c46.free_in_cell(reg, job["kind"])
        rec = {"schema": "s2-cell-1", "work_id": wid, "member": job["member"], "role": "reference", "cell_kind": job["kind"],
               "leg": job.get("leg"), "site": job.get("site"), "token": job.get("token"), "start": job.get("start"),
               "region_id": reg["region_id"] if job.get("region") else None, "free": free,
               "builder": {"BUILDER_VERSION": b42.BUILDER_VERSION, "GEOM_SHA": b42.GEOM_SHA, "partners": "relaxed"},
               "model": {"mock": "harmonic"},
               "relax": {"optimizer": "mock", "steps": 0, "converged": True, "wall_s": 0.2, "E_mace_eV": -1.0},
               "validity": {"checks": {}, "valid": True, "failed": []},
               "files": {"start": f"cells/{wid}/start.extxyz", "relaxed": f"cells/{wid}/relaxed.extxyz"},
               "sha256": {"start": sha256_file(os.path.join(d, "start.extxyz")),
                          "relaxed": sha256_file(os.path.join(d, "relaxed.extxyz"))}, "written": utc()}
        time.sleep(0.2)
        write_json(rec, L.record(c, wid))
        return 0
    if action == "region":
        reg = c46.build_region(relaxed(wid_of(job["member"], "host")), job["member"], job["site"])
        write_json(reg, L.region(c, job["member"], job["L"], job["site"])); return 0
    if action == "build-vac":
        vac, _ = c46.make_vacancy(relaxed(wid_of(job["member"], "host")), ctx)
        d = L.cell_dir(c, job["work_id"]); os.makedirs(d, exist_ok=True)
        write(os.path.join(d, "start.extxyz"), vac, format="extxyz")
        write_json({"work_id": job["work_id"]}, os.path.join(d, "vac_start.json")); return 0
    if action == "build-pair":
        h = relaxed(job["parents"]["host"]); v = relaxed(job["parents"]["vac"])
        bh, bv = c46.build_pair(h, v, ctx, job["token"], job["site"], job["pose"], partners="relaxed")
        legs = {}
        for leg, b in (("novac", bh), ("vac", bv)):
            w = wid_of(job["member"], "D", T=job["token"], j=job["site"], n=int(job["start"][1:]), leg=leg)
            d = L.cell_dir(c, w); os.makedirs(d, exist_ok=True)
            write(os.path.join(d, "start.extxyz"), b.atoms, format="extxyz")
            legs[leg] = {"work_id": w, "centre": b.centre, "members": list(b.members), "old_to_new": {str(k): v for k, v in b.old_to_new.items()}}
        write_json({"schema": "s2-pair-1", "member": job["member"], "token": job["token"], "site": job["site"],
                    "start": job["start"], "status": "built", "legs": legs},
                   L.pair(c, job["member"], job["token"], job["site"], int(job["start"][1:])))
        return 0
    if action == "distinct":
        ok = [(s, w) for s, w in zip(job["starts"], job["work_ids"]) if os.path.exists(L.record(c, w))]
        write_json({"kept": [s for s, _ in ok], "map": {f"o{i}": s for i, (s, _) in enumerate(ok)},
                    "work_ids": {f"o{i}": w for i, (_, w) in enumerate(ok)}}, job["out"]); return 0
    print(f"unknown action {action}"); return 1


def mockpw_main(inp, ranks, sysroot):
    """A pw.x stand-in for the self-test: writes the text markers of a pw.x 7.5 output (no physics). Scenarios
    (mock/pw_scenarios.json, by label): sp_ok, sp_nojd (no JOB DONE), sp_scf (JOB DONE, SCF not converged); relax with
    converge_at, delay, die_at (an end without JOB DONE; with die_oom the kernel's OOM kill is recorded), pw_error_at
    (QE's error banner, CRASH, exit 1); an exit file in the outdir stops it with the soft-exit marker and restart
    files; restart_mode='restart' continues the counters."""
    t = open(inp).read()
    g = lambda k, dflt=None: (re.search(rf"\b{k}\s*=\s*'?([^'\s,]+)'?", t) or [None, dflt])[1]
    calc, prefix, nstep, mode = g("calculation"), g("prefix"), int(g("nstep", "1")), g("restart_mode", "fresh")
    lab = re.sub(r"\.p\d+$", "", os.path.basename(inp)[:-3])
    sc = (read_json(os.path.join(sysroot, "mock", "pw_scenarios.json"), {}) or {}).get(lab, {})
    pos = t.split("ATOMIC_POSITIONS", 1)[1].splitlines()[1:]
    pos = [x for x in pos if x.strip() and len(x.split()) >= 4 and x.split()[0].isalpha()][:int(g("nat", "0"))]
    syms = [x.split()[0] for x in pos]
    pos0 = list(pos)

    def moved(k):
        """Positions printed for configuration k: the input's, with sc['shift'] = [atom, dx] applied from k = 1 on."""
        if not sc.get("shift") or k < 1:
            return pos0
        a_, dx = int(sc["shift"][0]), float(sc["shift"][1])
        out_ = list(pos0)
        t_ = out_[a_].split()
        t_[1] = f"{float(t_[1]) + dx:.10f}"
        out_[a_] = "  ".join(t_)
        return out_
    q = float(g("tot_charge", "0"))
    nel = sum(b42.VALENCE[s] for s in syms) - q
    out = sys.stdout

    def w(s=""):
        out.write(s + "\n"); out.flush()

    w("\n     Program PWSCF v.7.5 starts on  3Nov2026 at 12: 0: 0 \n")
    w(f"     Number of MPI processes:              {int(ranks or 64)}")
    upf = getattr(q47, "PSEUDO_S2", None) or {}
    for i, s in enumerate(sorted(set(syms)), 1):
        w(f"     PseudoPot. # {i} for {s:2s} read from file:\n     /data/pseudo/{upf.get(s, s + '.UPF')}\n"
          f"     MD5 check sum: {UPF_MD5.get(s, '0' * 32)}")
    w(f"     number of atoms/cell      =          {len(syms)}")
    w(f"     number of electrons       =      {nel:.2f}")

    def config(k, F):
        w(f"\n!    total energy              =   {F:.8f} Ry")
        w("     smearing contrib. (-TS)   =      -0.00490943 Ry")
        w("\n     convergence has been achieved in  10 iterations\n")
        w("     Forces acting on atoms (cartesian axes, Ry/au):\n")
        for i, s in enumerate(syms):
            w(f"     atom {i + 1:4d} type  1   force =     0.00000000    0.00000000    0.00000000")
        w("\n     Total force =     0.000000     Total SCF correction =     0.000000")

    def end(code=0):
        w("\n     PWSCF        :      1.00s CPU          2.00s WALL\n")
        w("=------------------------------------------------------------------------------=\n   JOB DONE.\n"
          "=------------------------------------------------------------------------------=")
        sys.exit(code)

    if calc == "scf":
        m = sc.get("mode", "sp_ok")
        if m == "sp_nojd":
            w("     total energy              =   -5883.2 Ry (partial)"); sys.exit(1)
        if m == "sp_scf":
            w("\n     convergence NOT achieved after 200 iterations: stopping"); end()
        config(0, -5883.30000000); end()
    tmp = os.path.join(os.path.dirname(os.path.abspath(inp)), "tmp")
    os.makedirs(tmp, exist_ok=True)
    stf = os.path.join(tmp, f"{prefix}.mockstate.json")
    k = 0
    if mode == "restart":
        st = read_json(stf)
        if st is None:
            w("     Error: no restart data"); sys.exit(1)
        k = st["k_next"]
    for i in range(nstep):
        if sc.get("die_at") is not None and k == sc["die_at"]:
            if sc.get("die_oom"):                                # the kernel's OOM kill of a pw.x rank (round-2 F4)
                append_jsonl(os.path.join(sysroot, "mock", "oom_events.jsonl"),
                             {"boot": open(os.path.join(sysroot, "mock", "boot_id")).read().strip(), "t": time.time(),
                              "task": "pw.x", "pid": os.getpid()})
            w("     (killed)"); sys.exit(137)
        if sc.get("pw_error_at") is not None and k == sc["pw_error_at"]:        # QE errore: banner, MPI abort
            w("\n " + "%" * 78 + "\n     Error in routine c_bands (1):\n     too many bands are not converged\n "
              + "%" * 78 + "\n\n     stopping ...")
            write_text("errore\n", os.path.join(os.path.dirname(os.path.abspath(inp)), "CRASH"))
            sys.exit(1)
        config(k, -5883.0 - 0.0005 * k)
        if sc.get("converge_at") is not None and k == sc["converge_at"]:      # as pw.x: no counters, final block
            w(f"\n     bfgs converged in {k + 1} scf cycles and {k} bfgs steps\n\n     End of BFGS Geometry Optimization\n"
              "\nBegin final coordinates\n\nATOMIC_POSITIONS (angstrom)")
            for x in pos:
                w(x)
            w("End final coordinates")
            end()
        w(f"\n     number of scf cycles    =   {k + 1}\n     number of bfgs steps    =   {k}\n")
        w("ATOMIC_POSITIONS (angstrom)")
        for x in moved(k + 1):
            w(x)
        td = sc.get("tail_delay")                                 # [k_from, s]: slow last configurations, so the
        time.sleep(float(td[1]) if td and k >= int(td[0]) else float(sc.get("delay", 0.02)))   # cap exit file lands
        k += 1
        if os.path.exists(os.path.join(tmp, f"{prefix}.EXIT")):
            os.makedirs(os.path.join(tmp, f"{prefix}.save"), exist_ok=True)
            write_text("<xml/>\n", os.path.join(tmp, f"{prefix}.save", "data-file-schema.xml"))
            write_text("bfgs\n", os.path.join(tmp, f"{prefix}.bfgs"))
            write_json({"k_next": k}, stf)
            w("\n     Program stopped by user request")
            end()
    w("\n     The maximum number of steps has been reached.\n\n     End of BFGS Geometry Optimization")
    write_json({"k_next": k}, stf)
    end()


class MockBackend(NodeBackend):
    """The self-test backend: boot ids and btime from <sysroot>/mock, no journal, scripted gates and checks, the
    scripts/46 contract through the real scripts/46 (calc mock-harmonic, reference cells) or the stub above."""
    tick, heartbeat_s, notice_hold_s, counts_every_s, poll_s = 0.05, 0.3, 2.0, 0.03, 0.1
    calc = "mock-harmonic"
    mock = True

    def __init__(self, root):
        super().__init__(root)
        self.sys = os.path.dirname(os.path.abspath(root))
        self.cfg = _mock_cfg(self.sys)

    def boot_id(self):
        return open(os.path.join(self.sys, "mock", "boot_id")).read().strip()

    def btime(self):
        return float(open(os.path.join(self.sys, "mock", f"btime.{self.boot_id()}")).read())

    def journal_end(self, boot):
        return None

    def _jctl(self, args):
        """The kernel journal of a mock boot: OOM kills recorded by the mock pw.x (mock/oom_events.jsonl, scenario
        die_oom) or by a test, in the kernel's two line formats; NodeBackend.oom parses them (round-2 F4)."""
        if "-k" not in args:
            return None
        boot = args[args.index("-b") + 1]
        out = []
        p = os.path.join(self.sys, "mock", "oom_events.jsonl")
        for x in (open(p).read().splitlines() if os.path.exists(p) else []):
            e = json.loads(x)
            if e.get("boot", "").replace("-", "") != boot:
                continue
            out += [f"{e['t']:.6f} mock kernel: oom-kill:constraint=CONSTRAINT_NONE,nodemask=(null),cpuset=/,"
                    f"mems_allowed=0,global_oom,task={e['task']},pid={e['pid']},uid=1000",
                    f"{e['t']:.6f} mock kernel: Out of memory: Killed process {e['pid']} ({e['task']}) total-vm:1kB"]
        return out

    def foreign_pw(self, own):
        return False

    def proc_tree(self, pid):
        return {}                                          # no /proc on the laptop: the task test of I-D7 applies

    def cpus_allowed(self, pid):
        return None

    def core_sets(self):
        return list(self.cfg.get("core_sets") or ["0-31", "32-63"])

    def node_script_expected(self, name):
        return _node_script_text(name, self.sys).encode()

    def git_state(self):
        return {"head": _mock_cfg(self.sys).get("git_head") or "0" * 40, "clean": True}

    def cmd46(self, action, jobfile):
        hang = self.cfg.get("mace_hang") or {}
        if action == "relax" and hang.get("wid") == (read_json(jobfile) or {}).get("work_id") and \
                hang.get("boot") == self.boot_id():
            return [self.python, os.path.abspath(__file__), "_mock46", "hang", "--job", jobfile]   # case (g)
        if "46_s2_cells.py" not in MOCKED:
            return [self.python, os.path.join(HERE, "46_s2_cells.py"), action, "--job", jobfile]
        return [self.python, os.path.abspath(__file__), "_mock46", action, "--job", jobfile]

    def run46(self, action, jobfile, log):
        with open(log, "a") as fh:
            return subprocess.run(self.cmd46(action, jobfile), cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT,
                                  timeout=600).returncode

    def gate(self, gate, campaign, log, inputs, attempt):
        dec = (self.cfg.get("gates") or {}).get(gate, {})
        L = c46.Layout(kind="node", root=self.node.root)
        write_json({"schema": "s2-gate-1", "gate": gate, "campaign": campaign, "result": {"scripted": True},
                    "decision": dec, "written": utc()}, L.gate(campaign, gate))
        return 0

    def upf_check(self, campaign, reference):
        return {"schema": "s2-upf-1", "passed": True, "scripted": True,
                "files": {el: {"md5": "0" * 32} for el in ("Cl", "Ca")}}

    def foundation_check(self):
        return {"schema": "s2-mace-1", "passed": True, "scripted": True}

    def graph(self, campaign, state):
        return graph_ref(state).to_json()


def graph_ref(state):
    """The reduced self-test campaign (run as c1 by the mock backend) on the reference cells (interface spec 9.6): checks, smoke tests,
    throughput row, a host relaxation and two sites of the reference cell, single points with scripted queue
    outcomes, three A2 relaxations (spot notice and restart; the k = 200 cap; no restart data) and one gate."""
    G = Graph("c1", PHASES["t"])
    G.add("check:upf", "check", "check", what="upf")
    G.add("check:nodescripts", "check", "check", what="nodescripts")             # N-F31 (round 4)
    G.add("check:mace", "check", "check", what="mace")
    _ref_block(G, state)
    G.add("mace:" + wid_of("ref233", "host"), "mace", "mace", [], action="relax-host", member="ref233",
          work_id=wid_of("ref233", "host"), cell_kind="host",
          role="reference", cat="mace_host", xkind="host")
    _mace_site(G, "c1", "ref233", "B", 136, ("Sr",), role="reference", cat_dopant="mace_dopant", starts=lambda T, j: [0], prov=False)
    _mace_site(G, "c1", "ref233", "B", 76, (), role="reference", cat_dopant="mace_dopant", starts=lambda T, j: [0], prov=False)
    # label names only (the grammar needs a pool host): every cell behind them is a reference cell (N-1)
    for lab, cell in (("s2_m30_VB136", wid_of("ref233", "V", "B", 136)),
                      ("s2_m30_Sr136o0_vac", wid_of("ref233", "D", T="Sr", j=136, n=0, leg="vac")),
                      ("s2_m30_Sr136o0_novac", wid_of("ref233", "D", T="Sr", j=136, n=0, leg="novac")),
                      ("s2_m30_VB76", wid_of("ref233", "V", "B", 76))):
        c46.check_label(lab)
        _sp(G, lab, cell, "sp")
    for i, lab in enumerate(("s2r_m30_VB136", "s2r_m30_VB76", "s2r_m30_VX138"), 1):
        c46.check_label(lab)
        G.add("a2:" + lab, "a2", "a2", [], label=lab, order=i, ref=True, member="ref233", cell_kind="V", L="B", j=136,
              token=None,
              a1=None, cat="a2")
        # section 11 checks on the reference rows: the 232 cell as start, the 233 cell as the partner (I-F1)
        G.add("a2v:" + lab, "a2v", "a2", ["a2:" + lab], label=lab, parent=None, order=i, ref=True, member="ref233",
              cell_kind="V", L="B", j=136, token=None, leg=None, a1=None, cat="a2_validate")
    G.add("gate:N", "gate", "gate", [], gate="N", cat="gate")
    return G


# ---------------------------------------------------------------- self-test (interface spec 9.6)
FLOCK_SHIM = '''import fcntl, os, subprocess, sys
a = sys.argv[1:]
nb = bool(a) and a[0] == "-n"
a = a[1:] if nb else a
fl = fcntl.LOCK_EX | (fcntl.LOCK_NB if nb else 0)
if a[0].isdigit() and len(a) == 1:
    try:
        fcntl.flock(int(a[0]), fl)
    except OSError:
        sys.exit(1)
    sys.exit(0)
fd = os.open(a[0], os.O_RDWR | os.O_CREAT, 0o644)
try:
    fcntl.flock(fd, fl)
except OSError:
    sys.exit(1)
sys.exit(subprocess.call(a[1:]))
'''


def _node_script_text(name, sysroot):
    """A committed ehpc/node script with only its node paths rewritten under <sysroot> (the self-test's node copy)."""
    R = os.path.join(sysroot, "data")
    tq = "/" + "tmp/qe_queue_"
    rep = [(RUN_QE, sysroot + RUN_QE), (QUEUE, R + "/setup/qe_queue.sh"), ("/data/jobs", R + "/jobs"), (tq, sysroot + tq),
           (CHAIN_LOCK, sysroot + CHAIN_LOCK), (QE_PROFILE, sysroot + QE_PROFILE)]
    t = open(os.path.join(ROOT, "ehpc", "node", name)).read()
    for a, b in rep:
        t = t.replace(a, b)
    return t


def _node_scripts(sysroot):
    """The committed ehpc/node/qe_queue.sh, chain.sh and s2_run_qe.sh with only their paths rewritten (as the WP3 laptop
    harness), a mock run_qe.sh for the queue, a mock QE profile, mpirun, taskset and lscpu for s2_run_qe.sh (mpirun
    records its arguments and core set in mock/mpirun_calls.log and runs the mock pw.x), and a Python flock shim on PATH
    (macOS has no flock)."""
    R = os.path.join(sysroot, "data")
    for f, dst in (("qe_queue.sh", os.path.join(R, "setup", "qe_queue.sh")), ("chain.sh", os.path.join(R, "setup", "chain.sh")),
                   ("s2_run_qe.sh", sysroot + "/usr/local/bin/s2_run_qe.sh")):
        write_text(_node_script_text(f, sysroot), dst); os.chmod(dst, 0o755)
    py, me = sys.executable, os.path.abspath(__file__)
    rq = (f'#!/bin/bash\ninp=${{1}}; np=${{2:-64}}\ncd "$(dirname "$inp")" || exit 1\nb=$(basename "$inp" .in)\n'
          f'"{py}" "{me}" _mockpw --input "$b.in" --ranks "$np" --sys "{sysroot}" > "$b.out" 2> "$b.err"\n')
    p = os.path.join(sysroot, "usr", "local", "bin", "run_qe.sh"); write_text(rq, p); os.chmod(p, 0o755)
    write_text(f"export QE_ENV={sysroot}/qe ESPRESSO_PSEUDO={getattr(q47, 'PSEUDO_DIR', '/data/pseudo')}\n",
               sysroot + QE_PROFILE)
    mp = (f'#!/bin/bash\necho "$(date +%s) cpuset=${{S2_MOCK_TASKSET:-none}} mpirun $*" >> "{sysroot}/mock/mpirun_calls.log"\n'
          'np=""\nwhile [ "$#" -gt 0 ]; do case "${1}" in -np) np=${2}; shift 2;; --bind-to) shift 2;; '
          '--use-hwthread-cpus) shift;; *) break;; esac; done\n'
          f'shift\nexec "{py}" "{me}" _mockpw --input "${{2}}" --ranks "$np" --sys "{sysroot}"\n')
    p = os.path.join(sysroot, "qe", "bin", "mpirun"); write_text(mp, p); os.chmod(p, 0o755)
    ts = '#!/bin/bash\n[ "${1}" = "-c" ] || exit 2\nexport S2_MOCK_TASKSET="${2}"\nshift 2\nexec "$@"\n'
    p = os.path.join(sysroot, "bin", "taskset"); write_text(ts, p); os.chmod(p, 0o755)
    lc = ('#!/bin/bash\ncase "${1}" in -p=CPU,CORE) echo "# CPU,Core"; for i in $(seq 0 63); do echo "$i,$i"; done;; '
          '*) echo "# Core"; seq 0 63;; esac\n')
    p = os.path.join(sysroot, "bin", "lscpu"); write_text(lc, p); os.chmod(p, 0o755)
    write_text(FLOCK_SHIM, os.path.join(sysroot, "bin", "flock.py"))
    p = os.path.join(sysroot, "bin", "flock"); write_text(f'#!/bin/bash\nexec "{py}" "{sysroot}/bin/flock.py" "$@"\n', p)
    os.chmod(p, 0o755)
    os.makedirs(os.path.join(sysroot, "tmp"), exist_ok=True)


class _Spot:
    """A local metadata endpoint: 404 until fire(), then 200 with a termination time."""

    def __init__(self):
        import http.server
        me = self
        me.on = False

        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                code = 200 if me.on else 404
                self.send_response(code); self.end_headers()
                if code == 200:
                    self.wfile.write(b"2026-11-03T12:00:00Z")

            def log_message(self, *a):
                pass
        self.srv = http.server.HTTPServer(("localhost", 0), H)
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def fire(self):
        self.on = True


def self_test(work=None):
    t0 = time.time()
    results = []

    def case(name, fn):
        t = time.time()
        try:
            msg = fn()
            results.append((name, True)); print(f"PASS {name}: {msg}  [{time.time() - t:.1f} s]", flush=True)
        except Exception as e:                                              # noqa: BLE001 (report every failure)
            results.append((name, False)); print(f"FAIL {name}: {type(e).__name__}: {e}  [{time.time() - t:.1f} s]", flush=True)
            traceback.print_exc(limit=6)

    for m in MOCKED:
        print(f"MOCKED {m}")
    print("NOTES: " + ", ".join(sorted(NOTES)))
    base = tempfile.mkdtemp(prefix="s2camp_", dir=work)
    if " " in base:
        raise SystemExit("the self-test directory may not contain spaces (the queue script splits on them)")
    sysroot = os.path.join(base, "sys")
    R = os.path.join(sysroot, "data")
    for d in ("data/work/s2", "data/jobs", "data/setup", "data/pseudo", "mock", "bin"):
        os.makedirs(os.path.join(sysroot, d), exist_ok=True)
    _node_scripts(sysroot)
    spot = _Spot()
    write_text(f"http://localhost:{spot.port}/latest/meta-data/instance/spot/termination-time\n",
               os.path.join(R, "setup", "s2_spot_url"))
    bootA, bootB = "a" * 8 + "-boot-a", "b" * 8 + "-boot-b"
    write_text(bootA, os.path.join(sysroot, "mock", "boot_id"))
    write_text(f"{time.time() - 60:.0f}", os.path.join(sysroot, "mock", f"btime.{bootA}"))
    write_json({"gates": {"throughput": {"a2_layout": "48"}, "N": {"n": 8, "gateN": {t: True for t in c46.TOKENS}}},
                "mace_hang": {"wid": "s2_ref233_VB76", "boot": bootA}}, os.path.join(sysroot, "mock", "config.json"))
    # a free inorganic atom of the reference V cell beyond the 6.0 A gate from v (I138 at 6.51 A in the Pb136-like
    # region): the s2r_m30_VB76 row moves it by 0.30 A from
    # configuration 1 on, so its section 11 partner check (check 5) must fail (I-F1)
    ctx0 = c46.ref_context()
    reg0 = c46.build_region(ctx0.host, "ref233", 136)
    c2h0, _ = c46.cell_maps("V", n_host=len(ctx0.host))
    dv0 = np.linalg.norm(find_mic(ctx0.host.positions - np.array(reg0["centres"]["v"]), ctx0.host.cell.array)[0], axis=1)
    sym0 = ctx0.vac.get_chemical_symbols()
    shift_atom = [i for i in c46.free_in_cell(reg0, "V") if sym0[i] in ("Pb", "I", "Cs") and dv0[c2h0[i]] > c46.PARTNER_CUT_A + 0.25][0]
    write_json({"s2_m30_Sr136o0_vac": {"mode": "sp_nojd"}, "s2_m30_Sr136o0_novac": {"mode": "sp_scf"},
                "s2smoke_ref232_rst": {"delay": 0.4}, "s2r_m30_VB136": {"delay": 0.15, "converge_at": 8},
                "s2r_m30_VB76": {"delay": 0.002, "tail_delay": [198, 0.4], "shift": [shift_atom, 0.30]},
                "s2r_m30_VX138": {"die_at": 2, "die_oom": True, "delay": 0.02}},
               os.path.join(sysroot, "mock", "pw_scenarios.json"))
    write_json(synthetic_state(a2_layout=None, commit=None), os.path.join(R, "work", "s2", "state.json"))
    env = dict(os.environ, PATH=os.path.join(sysroot, "bin") + os.pathsep + os.environ.get("PATH", ""))
    env.pop("S2_LOCK_FD", None)
    L = c46.Layout(kind="node", root=R)
    cdir = L.campaign_dir("c1")
    me = os.path.abspath(__file__)
    procs = {}

    def start_runner(tag):
        lf = open(os.path.join(base, f"runner_{tag}.log"), "w")
        procs[tag] = subprocess.Popen([sys.executable, me, "run", "--campaign", "c1", "--root", R, "--mock"], env=env,
                                      stdout=lf, stderr=subprocess.STDOUT, start_new_session=True)
        return procs[tag]

    def wait_for(pred, timeout, what):
        t = time.time()
        while time.time() - t < timeout:
            if pred():
                return True
            time.sleep(0.05)
        raise AssertionError(f"timed out after {timeout} s waiting for {what}")

    ka = os.path.join(R, "KEEP_ALIVE")
    seen = {}
    S2 = {"m30": site_sets("m30"), "m05": site_sets("m05")}

    def run_campaign():
        p = start_runner("A")
        wait_for(lambda: os.path.exists(os.path.join(L.cell_dir("c1", "s2_ref233_VB76"), "fire.log")), 120,
                 "the MACE job s2_ref233_VB76 to start (boot A)")
        seen["ka_running"] = os.path.exists(ka)
        wait_for(lambda: os.path.exists(L.record("c1", "s2_ref233_Sr136p0_vac")), 120, "the boot-A MACE jobs")
        seen["sha_A"] = {w: sha256_file(L.record("c1", w)) for w in ("s2_ref233_host", "s2_ref233_VB136")}
        os.killpg(p.pid, signal.SIGKILL); p.wait()                            # a node loss: every process dies
        write_text(bootB, os.path.join(sysroot, "mock", "boot_id"))           # the next boot
        write_text(f"{time.time():.0f}", os.path.join(sysroot, "mock", f"btime.{bootB}"))
        seen["ka_after_loss"] = os.path.exists(ka)
        p = start_runner("B")
        wait_for(lambda: os.path.exists(os.path.join(L.a2_dir("c1", "s2r_m30_VB136"), "s2r_m30_VB136.p1.out"))
                 and "number of scf cycles    =   4" in open(os.path.join(L.a2_dir("c1", "s2r_m30_VB136"),
                                                                          "s2r_m30_VB136.p1.out")).read(),
                 240, "the spot-test A2 relaxation to reach k = 3")
        seen["ka_b"] = os.path.exists(ka)
        spot.fire(); seen["notice_t"] = time.time()
        wait_for(lambda: p.poll() is not None, 300, "the runner to end")
        seen["rc"] = p.returncode
        return seen

    def c_campaign():
        run_campaign()
        log = open(os.path.join(base, "runner_B.log")).read()
        assert seen["rc"] == 0, f"runner exit {seen['rc']}: {log[-1500:]}"
        assert os.path.exists(os.path.join(cdir, "CAMPAIGN_DONE")), "no CAMPAIGN_DONE"
        return f"two boots, runner exit 0, CAMPAIGN_DONE; logs in the test directory"

    case("simulated campaign (mock MACE, mock pw.x, the committed queue scripts)", c_campaign)

    def c_a():
        st = q47.sp_status(L.sp_dir("c1", "s2_m30_VB136"), "s2_m30_VB136")
        assert st["status"] == "complete", st
        return "complete single point (JOB DONE, converged)"

    def c_b():
        d = L.sp_dir("c1", "s2_m30_Sr136o0_vac")
        assert os.path.exists(os.path.join(d, "s2_m30_Sr136o0_vac.gaveup"))
        tr = sorted(os.path.basename(x) for x in glob.glob(os.path.join(d, "*.out.try*")))
        assert tr == ["s2_m30_Sr136o0_vac.out.try1", "s2_m30_Sr136o0_vac.out.try2"], tr
        assert q47.sp_status(d, "s2_m30_Sr136o0_vac")["status"] == "missing"
        return "no JOB DONE: resubmitted once by the queue (.out.try1, .try2), .gaveup, missing"

    def c_c():
        d = L.sp_dir("c1", "s2_m30_Sr136o0_novac")
        assert not glob.glob(os.path.join(d, "*.try*")), "resubmitted"
        assert q47.sp_status(d, "s2_m30_Sr136o0_novac")["status"] == "missing"
        return "JOB DONE with an unconverged SCF: missing, never resubmitted (D3)"

    def c_d():
        lab = "s2r_m30_VB136"; d = L.a2_dir("c1", lab)
        r = read_json(os.path.join(d, f"{lab}.a2.json"))
        assert r["status"] == "complete" and r["restarts"] == 1 and len(r["parts"]) == 2, r
        import difflib
        a = open(os.path.join(d, f"{lab}.p1.in")).read().splitlines()
        b = open(os.path.join(d, f"{lab}.p2.in")).read().splitlines()
        diff = [x for x in difflib.unified_diff(a, b, lineterm="", n=0) if x[:1] in "+-" and x[:3] not in ("+++", "---")]
        keys = sorted({x[1:].split("=")[0].strip() for x in diff})
        assert keys == ["nstep", "restart_mode"] and len(diff) == 3, diff
        o1 = open(os.path.join(d, f"{lab}.p1.out")).read(); o2 = open(os.path.join(d, f"{lab}.p2.out")).read()
        k1 = [int(x) for x in re.findall(r"number of scf cycles\s*=\s*(\d+)", o1)]
        k2 = [int(x) for x in re.findall(r"number of scf cycles\s*=\s*(\d+)", o2)]
        assert k2[0] == k1[-1] + 1 and r["end_rule"]["outcome"] == "accepted_converged", (k1, k2, r["end_rule"])
        vf = r.get("validity_final") or {}
        assert vf.get("valid") is True and vf.get("failed") == [] and os.path.exists(os.path.join(d, f"{lab}.final.extxyz")), r
        it = [json.loads(x) for x in open(os.path.join(cdir, "interruptions.jsonl"))]
        sp = [x for x in it if x["label"] == lab]
        assert len(sp) == 1 and sp[0]["cause"] == "spot-notice", sp
        nxt = read_json(os.path.join(L.a2_dir("c1", "s2r_m30_VB76"), "s2r_m30_VB76.p1.launch.json"))
        nt = float(open(os.path.join(R, "work", "s2", "spot", f"notice.{bootB}")).read().split()[1])
        assert nxt["started_epoch"] >= nt + MockBackend.notice_hold_s - 0.01, (nxt["started_epoch"], nt)
        return (f"spot notice at k = {sp[0]['k']}: exit file, part 2 differs from part 1 only in restart_mode and nstep "
                f"({'; '.join(x.strip() for x in diff)}), counters continue ({k1[-1]} -> {k2[0]}), interruption "
                f"logged, no launch during the {MockBackend.notice_hold_s} s hold")

    def c_e():
        lab = "s2r_m30_VB76"; d = L.a2_dir("c1", lab)
        r = read_json(os.path.join(d, f"{lab}.a2.json"))
        assert read_json(os.path.join(d, "exit_request.json"))["reason"] == "cap"
        assert r["n_config"] == 201 and r["k_last"] == 200, r
        assert r["end_rule"]["outcome"] == "unconverged_cap", r["end_rule"]
        raw = len(re.findall(r"^!", open(os.path.join(d, f"{lab}.p1.out")).read(), re.M))
        vf = r.get("validity_final") or {}
        assert vf.get("valid") is False and vf.get("failed") == [5] and r["final_geometry"]["k"] == 200, r
        vrec = read_json(os.path.join(d, f"{lab}.validity_final.json"))
        dr = vrec["validity"]["checks"]["5"]["gated"]["max_dr_inorganic_A"]
        assert abs(dr - 0.30) < 1e-6, dr
        return (f"exit file at k = 200 ({raw} configurations printed, 201 read), end rule {r['end_rule']['outcome']}; "
                f"section 11 checks on the k = 200 geometry: a far atom moved {dr:.2f} A fails check 5 (I-F1)")

    def c_f():
        lab = "s2r_m30_VX138"; d = L.a2_dir("c1", lab)
        r = read_json(os.path.join(d, f"{lab}.a2.json"))
        assert r["status"] == "missing" and r["reruns_from_zero"] == 3, r
        assert all(os.path.isdir(os.path.join(d, "discarded", f"r{k}")) for k in (1, 2))
        assert [x["cause"] for x in r["interruptions"]] == ["oom"] * 3, r["interruptions"]      # round-2 F2, F4
        assert "validity_final" not in r and not os.path.exists(os.path.join(d, f"{lab}.validity_final.json"))
        comp = read_json(os.path.join(cdir, "completeness.json"))
        assert comp["jobs"]["a2v:" + lab] == "skipped" and comp["jobs"]["a2v:s2r_m30_VB136"] == "done", comp["jobs"]
        return ("an OOM kill of the pw.x of a part without restart data (this boot): rerun from k = 0 twice, then "
                "missing; partial outputs in discarded/; its section 11 check skipped (no final geometry)")

    def c_g():
        d = L.cell_dir("c1", "s2_ref233_VB76")
        att = read_json(os.path.join(d, "attempts.json"))
        assert len(att) == 2 and att[0]["cause"] == "node-loss" and att[0]["boot"] == bootA and att[1]["boot"] == bootB, att
        assert os.path.exists(os.path.join(d, "discarded", "att1", "fire.log")) and os.path.exists(L.record("c1", "s2_ref233_VB76"))
        return "attempt without a record in an earlier boot: node-loss, rerun once, partial output moved aside unread"

    def c_h():
        assert seen["ka_running"] and seen["ka_b"] and not os.path.exists(ka), seen
        return "KEEP_ALIVE present while the campaign runs (both boots), removed at its end"

    def c_j():
        now = {w: sha256_file(L.record("c1", w)) for w in seen["sha_A"]}
        assert now == seen["sha_A"], "a record made in boot A changed"
        att = read_json(os.path.join(L.cell_dir("c1", "s2_ref233_host"), "attempts.json"))
        assert len(att) == 1
        return "resumed in a new boot: the boot-A records unchanged, completed jobs not rerun"

    def c_l():
        rd = [json.loads(x) for x in open(os.path.join(cdir, "runner_reads.jsonl"))]
        modes = Counter((x["what"], x["mode"]) for x in rd)
        assert set(x["mode"] for x in rd) <= {"status", "counts", "end_rule", "final_geom"}
        assert all(x["label"].startswith("s2r_") for x in rd if x["mode"] in ("end_rule", "final_geom"))
        assert ("parse_relax", "final_geom") in modes
        return (f"the runner read QE outputs only in status, counts and end_rule modes, and A2 final positions in "
                f"final_geom mode: {dict(modes)}")

    for nm, fn in (("(a) complete single point", c_a), ("(b) no JOB DONE", c_b), ("(c) unconverged SCF", c_c),
                   ("(d) spot notice and restart", c_d), ("(e) stop at k = 200", c_e),
                   ("(f) OOM kill without restart data", c_f), ("(g) MACE interruption", c_g), ("(h) keep-alive", c_h),
                   ("(j) resume", c_j), ("(l) runner reads", c_l)):
        case(nm, fn)

    def c_a2stop():
        R3 = os.path.join(base, "a2stop", "data")
        os.makedirs(os.path.join(R3, "work", "s2", "ledger"), exist_ok=True)
        os.makedirs(os.path.join(base, "a2stop", "mock"), exist_ok=True)
        write_text("s-boot", os.path.join(base, "a2stop", "mock", "boot_id"))
        write_text(f"{time.time():.0f}", os.path.join(base, "a2stop", "mock", "btime.s-boot"))
        write_json({}, os.path.join(base, "a2stop", "mock", "config.json"))
        L3 = c46.Layout(kind="node", root=R3)
        rec = lambda w, ok: write_json({"work_id": w, "validity": {"valid": ok}, "free": [0]}, L3.record("c1", w))
        for w, ok in (("s2_m30_host", True), ("s2_m30_VB136", True), ("s2_m30_Sr136p0_novac", False),
                      ("s2_m30_Sr136p0_vac", True), ("s2_m30_Ca136p0_novac", True), ("s2_m30_Ca136p0_vac", True)):
            rec(w, ok)
        st = synthetic_state()
        st.pop("K2"); st.pop("K3"); st["step0"] = {}
        rn = Runner("c2", R3, MockBackend(R3)); rn.boot = "s-boot"; rn.state = st
        rn.be.graph = lambda c, s: graph("c2", s, sites=lambda m: S2[m])
        rn.graph_now()
        jb = rn.G["jobs_by_id"]
        assert not hasattr(rn, "a2_a1_check")                     # I-10 revised: no A2 relaxation is skipped
        assert jb["gate:K3"]["deps"] == ["a2v:" + x for x in C2_ORDER[:8]]
        assert jb["a2v:s2r_m30_VB136"]["deps"] == ["a2:s2r_m30_VB136", "a2:s2r_m30_hostB136"]
        assert jb["a2v:s2r_m30_Sr136o0_vac"]["parent"] == "s2r_m30_VB136" and jb["a2v:s2r_m30_hostB136"]["parent"] is None
        st0 = rn.statuses()
        assert st0["a2:s2r_m30_Sr136o0_novac"] == "pending" and st0["a2v:s2r_m30_VB136"] == "pending"
        rn.state["K2"] = "fail"
        rn.cache = {}
        stt = rn.statuses()
        assert stt["gate:K3"] == "skipped" and stt["gate:projection@after4"] == "skipped", stt
        rn.a2_phase([j for j in jb.values() if j["phase"] == "a2"], stt)
        got = Counter(read_json(rn.a2_path(j["label"]))["status"] for j in jb.values() if j["kind"] == "a2")
        assert got == {"not_run_gate": 10}, got
        rn.cache = {}
        stv = rn.statuses()
        assert all(stv["a2v:" + x] == "skipped" for x in C2_ORDER), stv
        return ("every A2 relaxation is scheduled whatever its A1 validity (I-10 revised); each has its section 11 check "
                "job after itself and its partner, and K3 waits for the eight checks; after K2 'fail' every unstarted "
                "A2 relaxation is not_run, its check skipped, and the in-A2 gates are skipped")
    case("(m) A2 stopped by a gate; section 11 check jobs (I-10 revised, I-F1)", c_a2stop)

    def c_step0():
        """Review-2 F3: fail -> STEP0_FIX -> repeat (attempt 2 at both cells, with the note) through the hand-off between
        this runner and the scripts/49 CLI inputs; and STEP0_NO_ERROR -> fail_final."""
        R4 = os.path.join(base, "step0", "data")
        for dd in ("work/s2/ledger", "work/s2/c2/gates", "work/s2/c2/gates_applied", "work/s2/c2/a2/s2r_m30_VB136"):
            os.makedirs(os.path.join(R4, dd), exist_ok=True)
        write_json({"mapping": {"affine_slope_1": True, "nstep_first": 201}},
                   os.path.join(R4, "work", "s2", "c1", "smoke.json"))
        os.makedirs(os.path.join(base, "step0", "mock"), exist_ok=True)
        write_text("z-boot", os.path.join(base, "step0", "mock", "boot_id"))
        write_text(f"{time.time():.0f}", os.path.join(base, "step0", "mock", "btime.z-boot"))
        write_json({}, os.path.join(base, "step0", "mock", "config.json"))
        rn = Runner("c2", R4, MockBackend(R4)); rn.boot = "z-boot"
        rn.state = synthetic_state(commit="1" * 40, step0={"attempts": 1, "outcome": "fail_pending_fix",
                                                          "repeat": False, "fix_note": None})
        rn.state.update({"campaigns": {"c1": "done"}}); rn.state.pop("K3")
        write_json({"decision": {}}, os.path.join(rn.cdir, "gates_applied", "gate_step0_1.json"))
        write_json({}, os.path.join(rn.cdir, "a2", "s2r_m30_VB136", "s2r_m30_VB136.a2.json"))
        assert rn.a2_stopped()
        write_text("0" * 40 + " results/objective2/s2/STEP0_FIX_2026-11-20.md\n", os.path.join(rn.cdir, "STEP0_FIX"))
        rn.check_commit()                                                   # the mock HEAD is "0" * 40
        s0 = rn.state["step0"]
        assert s0["outcome"] == "repeat_pending" and s0["repeat"] and s0["fix_note"].endswith("2026-11-20.md"), s0
        assert not rn.a2_stopped() and rn.state["commit"] == "0" * 40 and "K2" not in rn.state
        assert not os.path.exists(os.path.join(rn.cdir, "gates_applied", "gate_step0_1.json"))
        assert glob.glob(os.path.join(rn.cdir, "discarded", "step0_attempt1_*", "gates_applied", "gate_step0_1.json"))
        assert not os.path.isdir(os.path.join(rn.cdir, "a2"))
        lay = c46.Layout(kind="node", root=R4)
        att = []
        for at, sp in (("s2r_m30_VB136", "s2_m30_VB136"), ("s2r_m30_Sr136o0_vac", "s2_m30_Sr136o0_vac")):
            inp, a_ = rn.gate_inputs({"gate": "step0", "at": at})
            assert a_ == 2 and inp["attempt"] == 2 and inp["fix_note"] and inp["cells"] == [sp], inp
            inp2, _ = g49.derive_inputs("step0", lay, rn.state, dict(inp))    # the scripts/49 CLI accepts them
            assert inp2["attempt"] == 2 and inp2["fix_note"] == inp["fix_note"]
            att.append(inp2["attempt"])
            # the decision scripts/49 writes for a passing check (merged fields), applied as run_gate does (N-D1)
            dec = {"step0": {**rn.state["step0"], "attempts": 2, "outcome": "pass", "repeat": True,
                             "fix_note": inp2["fix_note"]}}
            rn.state.update(copy.deepcopy(dec))
        assert rn.state["step0"]["outcome"] == "pass" and not rn.a2_stopped()
        # no error found: fail_final, A2 stops (section 11)
        rn.state["step0"] = {"attempts": 1, "outcome": "fail_pending_fix"}
        write_text("2026-11-20 no writer or input error found\n", os.path.join(rn.cdir, "STEP0_NO_ERROR"))
        assert rn.preconditions() is None and rn.state["step0"]["outcome"] == "fail_final" and rn.a2_stopped()
        return ("fail -> STEP0_FIX: repeat_pending with the note, attempt-1 A2 and gate files moved aside, A2 not "
                f"stopped; both cells attempt {att} with the note, accepted by scripts/49 derive_inputs; "
                "STEP0_NO_ERROR -> fail_final, A2 stops")
    case("(n) step-0 repeat after a fix (review-2 F3)", c_step0)

    def c_k3_records():
        """Review F1 across modules: scripts/49 gather_k3 and k3_eval on the A2 records this runner wrote (the reference
        rows stand in for the eight K3 cells; no energy of an S2 cell exists)."""
        recs = {lab: read_json(os.path.join(L.a2_dir("c1", lab), f"{lab}.a2.json")) for lab in ("s2r_m30_VB136", "s2r_m30_VB76")}

        class _Rd:
            def __init__(self, which):
                self.which = which

            def json_file(self, key):
                return copy.deepcopy(recs[self.which[key[3:]]])

            def relax(self, lab, mode):
                assert mode == "final"
                return {"F_eV": {10: -80000.0 + (0.2 if lab == g49.K3_QUARTETS["hinge"]["DV"] else 0.0)}, "k_last": 10}

            def record(self, wid):
                return {"validity": {"valid": True, "failed": []}}
        labs = [x for q in g49.K3_QUARTETS.values() for x in q.values()]
        good = g49.k3_eval(g49.gather_k3(_Rd({x: "s2r_m30_VB136" for x in labs})))
        bad = g49.k3_eval(g49.gather_k3(_Rd({x: ("s2r_m30_VB76" if x == "s2r_m30_hostB76" else "s2r_m30_VB136") for x in labs})))
        assert good["K3"] == "pass" and abs(good["value_meV"] - 200.0) < 1e-6, good
        assert bad["K3"] == "fail_replan" and any("s2r_m30_hostB76" in x for x in bad["checks_failed"]), bad
        return ("scripts/49 K3 on runner-written A2 records: valid checks and +200 meV -> pass; one record with "
                "validity_final failed [5] -> fail_replan")
    case("(o) K3 reads the runner's section 11 checks (review F1)", c_k3_records)

    def c_units():
        """Review F6, F7, F8 and review-2 F6, F7 (unit level, temporary root)."""
        R5 = os.path.join(base, "units", "data")
        for dd in ("work/s2/ledger", "work/s2/c2/a2/s2r_m30_VB136"):
            os.makedirs(os.path.join(R5, dd), exist_ok=True)
        os.makedirs(os.path.join(base, "units", "mock"), exist_ok=True)
        write_text("u-boot", os.path.join(base, "units", "mock", "boot_id"))
        write_text(f"{time.time():.0f}", os.path.join(base, "units", "mock", "btime.u-boot"))
        write_json({}, os.path.join(base, "units", "mock", "config.json"))
        write_json({"label": "s2r_m30_VB136", "status": "complete", "wall_h": 9.0, "n_config": 100},
                   os.path.join(R5, "work", "s2", "c2", "a2", "s2r_m30_VB136", "s2r_m30_VB136.a2.json"))
        rn = Runner("c4", R5, MockBackend(R5)); rn.boot = "u-boot"; rn.state = synthetic_state()
        os.makedirs(rn.cdir, exist_ok=True)
        rn.load_walls()                                                    # F6: C2 walls reach C4
        assert rn.measured("a2") == [9.0] and abs(rn.measured("a2_config")[0] - 0.09) < 1e-12
        led = os.path.join(R5, "work", "s2", "ledger")
        now = time.time()
        write_json({"boot_id": "old-boot", "btime": now - 505 * 3600.0 - 7200.0, "campaigns": ["c2"]},
                   os.path.join(led, "boot.old-boot.json"))
        write_text(f"{now - 7200.0:.0f} x\n", os.path.join(led, "heartbeat.old-boot"))
        write_json({"boot_id": "u-boot", "btime": now, "campaigns": ["c4"]}, os.path.join(led, "boot.u-boot.json"))
        rn.heartbeat(force=True)
        lg = ledger(R5, now, rn.be)                                         # F8: journal unreadable -> idle bound
        old = [r for r in lg["boots"] if r["boot_id"] == "old-boot"][0]
        assert old["end_assumed"] and abs(old["hours"] - (505 * 3600.0 + 60 + IDLE_STOP_S + IDLE_MARGIN_S) / 3600.0) < 1e-3   # heartbeat to 1 s
        H = lg["H_spent_h"]
        assert rn.cap_ok({"id": "a2:x"}, "a2") == g49.job_start_allowed(H, 9.0)           # measured mean, not 20.6 h
        assert g49.job_start_allowed(H, 9.0) and not g49.job_start_allowed(H, 20.6), H
        rn.capped = None
        assert rn.cap_ok({"id": "a2:y"}, "a2", expected_h=51 * 0.09)                      # F7: remaining configurations
        write_json([{"boot_id": "old-boot", "end": now - 7000.0, "note": "console stop time"}], os.path.join(led, "manual.json"))
        old2 = [r for r in ledger(R5, now, rn.be)["boots"] if r["boot_id"] == "old-boot"][0]
        assert old2["end_assumed"].startswith("operator") and abs(old2["end_used"] - (now - 7000.0)) < 1e-6
        # review-2 F6: the chain lock
        os.makedirs(os.path.dirname(rn.node.chain_lock), exist_ok=True)
        fd = os.open(rn.node.chain_lock, os.O_WRONLY | os.O_CREAT, 0o644)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)                     # a queue holds it
        held = rn.chain_lock_ok()
        fcntl.flock(fd, fcntl.LOCK_UN); os.close(fd)
        free_ = rn.chain_lock_ok()
        rn.chain_lock_release()
        assert held is False and free_ is True and rn.chainfd is None
        rn.be.foreign_pw = lambda own: True
        assert rn.chain_lock_ok() is False
        rn.chain_lock_release()
        return (f"C2 wall reaches C4 (expected 9.0 h, not 20.6 h: start allowed at H_spent {H:.2f}); a restart part "
                "checked with its remaining configurations; an unreadable journal ends a boot at the idle-stop bound, "
                "an operator stop time overrides it; pw.x outside the queue waits while the chain lock is held or a "
                "foreign pw.x runs")
    case("(p) hard-cap walls, restart cap, ledger bound, chain lock (reviews F6-F8, review-2 F6)", c_units)

    def c_smoke():
        sm = read_json(os.path.join(cdir, "smoke.json"))
        m = sm["mapping"]
        assert m["c0"] == 0 and m["affine_slope_1"] and m["nstep_first"] == 201 and sm["restart_possible"], sm
        assert m["restart_files"] == ["{prefix}.bfgs", "{prefix}.mockstate.json", "{prefix}.save/data-file-schema.xml"], m
        tp = read_json(os.path.join(cdir, "throughput.json"))
        assert all(tp["runs"][x]["n_config"] == 5 for x in tp["runs"]), tp
        return f"smoke mapping c0 0, nstep_first 201, restart reproduces n3; throughput runs 5 configurations each"
    case("smoke and throughput records", c_smoke)

    def c_cap():
        sys2 = os.path.join(base, "cap"); R2 = os.path.join(sys2, "data")
        for dd in ("data/work/s2/ledger", "mock"):
            os.makedirs(os.path.join(sys2, dd), exist_ok=True)
        write_text("cap-boot", os.path.join(sys2, "mock", "boot_id"))
        write_text(f"{time.time():.0f}", os.path.join(sys2, "mock", "btime.cap-boot"))
        write_json({}, os.path.join(sys2, "mock", "config.json"))
        out = []
        for H, exp in ((519.99, {"sp": False, "mace": False, "a2": False}), (500.0, {"sp": True, "mace": True, "a2": False})):
            write_json([{"boot_id": "old", "btime": 0.0, "end": H * 3600.0, "note": "synthetic"}],
                       os.path.join(R2, "work", "s2", "ledger", "manual.json"))
            for k, want in exp.items():
                rn = Runner("c1", R2, MockBackend(R2)); rn.boot = "cap-boot"; rn.state = synthetic_state()
                os.makedirs(rn.cdir, exist_ok=True)
                rn.heartbeat(force=True)
                write_json({"boot_id": "cap-boot", "btime": time.time(), "campaigns": ["c1"]},
                           os.path.join(R2, "work", "s2", "ledger", "boot.cap-boot.json"))
                f = 2.0 if k == "sp" else 1.0
                got = rn.cap_ok({"id": f"x_{k}"}, k, factor=f)
                assert got == want, (H, k, got)
                out.append(f"{H}:{k}={'start' if got else 'refused'}")
        rn.G = {"jobs_by_id": OrderedDict([
            ("j1", {"id": "j1", "kind": "check", "what": "zz", "deps": [], "phase": "check"}),
            ("j2", {"id": "j2", "kind": "pw", "phase": "smoke", "label": "s2smoke_ref232_n1", "part": 1, "deps": []}),
            ("j3", {"id": "j3", "kind": "gate", "gate": "N", "phase": "gate", "deps": []}),
            ("j4", {"id": "j4", "kind": "g1", "phase": "qe", "deps": []})])}
        rn.capped = {"job": "x"}
        st_ = rn.statuses()
        assert st_ == {"j1": "pending", "j2": "not_started_cap", "j3": "pending", "j4": "pending"}, st_     # N-F14
        write_json([{"boot_id": "old", "note": "no times"}], os.path.join(R2, "work", "s2", "ledger", "manual.json"))
        try:
            rn.h_spent(); raise AssertionError("an incomplete ledger was accepted")
        except Stop:
            pass
        return "; ".join(out) + ("; after a refusal an unstarted pw.x job is not_started_cap, a check, a gate and a "
                                 "geometry job stay pending (N-F14); an incomplete ledger STOPs (I-23)")
    case("(i) hard cap and ledger", c_cap)

    def c_counts():
        S = S2
        got = []
        for nm, camp, st in (("C1", "c1", synthetic_state(a2_layout=None)),
                             ("C1 layout 64", "c1", synthetic_state(a2_layout="64")),
                             ("C1 provisional Pb-Cl", "c1", synthetic_state(stage0={**synthetic_state()["stage0"],
                                                                                   "pbcl": {"decision": "provisional_2.837"}})),
                             ("C2", "c2", synthetic_state()), ("C2 Ca G1 fail", "c2", synthetic_state(G1={"Cl": True, "Ca": False})),
                             ("C4", "c4", synthetic_state()),
                             ("C4 cuts 1-4", "c4", synthetic_state(cuts=[{"cut": k} for k in (1, 2, 3, 4)])),
                             ("C4 cut 1, Cl G1 fail", "c4", synthetic_state(cuts=[{"cut": 1}], G1={"Cl": False, "Ca": True})),
                             ("C4 cut 8", "c4", synthetic_state(cuts=[{"cut": k} for k in range(1, 9)]))):
            g = graph(camp, st, sites=lambda m: S[m])
            exp, adj = assert_counts(g, st)
            labs = [j["label"] for j in g["jobs"] if j["kind"] in ("sp", "a2")]
            assert len(labs) == len(set(labs))
            for lab in labs:
                c46.check_label(lab)
            got.append(f"{nm} {sum(v for k, v in exp.items() if k.startswith(('mace', 'sp', 'a2')))}")
        g1 = graph("c1", synthetic_state(a2_layout=None), sites=lambda m: S[m])
        pr = [j for j in g1["jobs"] if j["kind"] == "g46" and j["action"] == "build-pair" and j.get("allow_provisional")]
        assert not pr
        g1p = graph("c1", synthetic_state(stage0={**synthetic_state()["stage0"], "pbcl": {"decision": "provisional_2.837"}}),
                    sites=lambda m: S[m])
        assert sum(1 for j in g1p["jobs"] if j.get("allow_provisional")) == 4
        assert [j["label"] for j in graph("c2", synthetic_state(), sites=lambda m: S[m])["jobs"] if j["kind"] == "a2"] == list(C2_ORDER)
        sp1 = [j["label"] for j in g1["jobs"] if j["kind"] == "sp"]
        assert sp1[:5] == list(SP_LABELS_FIXED["G1"]) and sp1[5:7] == list(SP_LABELS_FIXED["spin"])
        assert [x for x in sp1 if x.endswith("_q0")] == list(Q0_ROWS)
        try:
            bad = graph("c1", synthetic_state(a2_layout=None), sites=lambda m: S[m])
            bad["counts"]["sp_noise"] -= 1
            assert_counts(bad, synthetic_state(a2_layout=None)); raise AssertionError("a wrong count passed")
        except S2Error:
            pass
        return "counts equal the plan: " + "; ".join(got) + "; labels valid and unique; C2 order fixed; a wrong count refused"
    case("(k) C1-C4 graph counts (geometry only, unrelaxed m30/m05)", c_counts)

    def c_c3():
        S = {m: site_sets(m) for m in ["m06", "m02", "m16", "m12", "m32", "m26", "m22", "m23", "m33", "m13"]}
        got = []
        for nm, st in (("n = 8", synthetic_state()), ("n = 10", synthetic_state(n=10)),
                       ("n = 10, cut 5", synthetic_state(n=10, cuts=[{"cut": 5}])),
                       ("Cs multi-pose, Cl G1 fail", synthetic_state(pose={"Cs": "multi", "Cl": "multi"}, G1={"Cl": False, "Ca": True})),
                       ("Ca G1 fail", synthetic_state(G1={"Cl": True, "Ca": False})),
                       ("Cl multi-pose, cut 6", synthetic_state(pose={"Cs": "multi", "Cl": "multi"}, cuts=[{"cut": 6}]))):
            g = graph("c3", st, sites=lambda m: S[m])
            exp, _ = assert_counts(g, st)
            got.append(f"{nm}: {exp.get('mace_host', 0) + exp.get('mace_V', 0) + exp.get('mace_dopant', 0) + exp.get('mace_pose_extra', 0)}"
                       f" relaxations, {exp.get('sp', 0) + exp.get('sp_pose_extra', 0)} single points")
        return "; ".join(got)
    case("(k) C3 graph counts (Stage-0 hosts, geometry only)", c_c3)

    def c_archive():
        stage = os.path.join(base, "pull")
        os.makedirs(os.path.join(stage, "jobs"), exist_ok=True)
        shutil.copytree(os.path.join(R, "work", "s2"), os.path.join(stage, "work"), ignore=shutil.ignore_patterns("smoke", "tp", "tmp"))
        shutil.copytree(os.path.join(R, "jobs", "s2c1"), os.path.join(stage, "jobs", "s2c1"))
        out = os.path.join(base, "archive", "c1")
        r = archive(stage, "c1", out)
        assert os.path.exists(os.path.join(out, "raw", "s2_m30_VB136.out.gz"))
        assert os.path.exists(os.path.join(out, "raw", "s2r_m30_VB136.p2.out.gz"))
        assert os.path.exists(os.path.join(out, "records", "s2_ref233_host.json"))
        assert (read_json(os.path.join(out, "nodescripts_check.json")) or {}).get("passed")      # round 4 (N-F31)
        for f in glob.glob(os.path.join(out, "**", "*.json"), recursive=True) + [os.path.join(out, "logs", "campaign.log")]:
            assert not c46.hygiene_violations(open(f).read()), f
        try:
            archive(stage, "c1", out); raise AssertionError("a second archive into a full directory passed")
        except S2Error:
            pass
        rp = os.path.join(stage, "work", "c1", "cells", "s2_ref233_host", "record.json")
        rec = read_json(rp); rec["sha256"]["relaxed"] = "0" * 64; write_json(rec, rp)
        try:
            archive(stage, "c1", os.path.join(base, "archive2", "c1")); raise AssertionError("a mismatching sha256 passed")
        except S2Error as e:
            pass
        return f"archived {r['labels']} labels, {r['counts']}; hygiene clean; a full directory and a sha256 mismatch refused"
    case("archive", c_archive)

    def c_spot():
        u = spot_url(ROOT, os.path.join(base, "nowhere", "data"))
        assert u.startswith("http://") and u.endswith("/termination-time")
        write_text("https://example/termination-time\n", os.path.join(base, "bad", "data", "setup", "s2_spot_url"))
        try:
            spot_url(ROOT, os.path.join(base, "bad", "data")); raise AssertionError("a bad URL passed")
        except S2Error:
            pass
        return "spot URL read from the committed node_step7.sh (not printed) and validated; a bad URL refused (X-5)"
    case("spot URL", c_spot)

    def c_hyg():
        files = [os.path.abspath(__file__)] + [os.path.join(ROOT, "ehpc", "node", f) for f in
                                               ("s2_campaign.sh", "s2_relaunch.sh", "s2_status.sh", "s2_run_qe.sh")]
        f51 = os.path.join(HERE, "51_s2_preflight.py")
        files += [f51] if os.path.exists(f51) else []
        bad = {}
        for f in files:
            if not os.path.exists(f):
                raise AssertionError(f"{os.path.basename(f)} missing")
            try:                                                      # scripts/46's scanner, code mode
                v = c46.hygiene_violations(open(f).read(), kind="code")
            except TypeError:
                v = _hyg_scan(open(f).read())
            if v:
                bad[os.path.basename(f)] = v
        assert not bad, bad
        for f in files[1:5]:
            r = subprocess.run(["bash", "-n", f], stderr=subprocess.PIPE, universal_newlines=True)
            assert r.returncode == 0, (f, r.stderr)
        for t in ("/Us" + "ers/x", "10.0.0." + "1", "a@b." + "com", "i-" + "abcdef0123456", "/t" + "mp/x", "US" + "D 3"):
            assert _hyg_scan(t), t
        assert not _hyg_scan("/data/work/s2 /usr/local/bin/run_qe.sh /data/pseudo")
        return (f"{len(files)} new files clean under the scripts/46 scanner (code mode: '$' only next to a digit); "
                f"wrappers pass bash -n; the stub scanner catches each pattern")
    case("hygiene", c_hyg)

    # ---------------------------------------------------------------- round-2 cases (unit level, temporary roots)
    def mini(tag, boot="m-boot", cfg=None):
        sysd = os.path.join(base, tag); Rm = os.path.join(sysd, "data")
        for dd in ("data/work/s2/ledger", "data/jobs", "data/setup", "data/pseudo", "mock", "bin"):
            os.makedirs(os.path.join(sysd, dd), exist_ok=True)
        write_text(boot, os.path.join(sysd, "mock", "boot_id"))
        write_text(f"{time.time() - 60:.0f}", os.path.join(sysd, "mock", f"btime.{boot}"))
        write_json(cfg or {}, os.path.join(sysd, "mock", "config.json"))
        write_json({"boot_id": boot, "btime": time.time() - 60, "campaigns": []},
                   os.path.join(Rm, "work", "s2", "ledger", f"boot.{boot}.json"))
        return sysd, Rm

    def c2_runner(Rm, boot="m-boot", **st_over):
        rn = Runner("c2", Rm, MockBackend(Rm)); rn.boot = boot
        st = synthetic_state(**st_over); st.pop("K2", None); st.pop("K3", None); st["step0"] = {}
        st["campaigns"] = {"c1": "done"}
        rn.state = st
        rn.be.graph = lambda c, s: graph("c2", s, sites=lambda m: S2[m])
        rn.graph_now()
        return rn

    def put_part(rn, lab, text, *, boot, rc=None, started=None, nel=None):
        """One launched part of an A2 relaxation, ended (dead pid), with its output text."""
        d = rn.L.a2_dir(rn.c, lab); os.makedirs(d, exist_ok=True)
        f = rn.part_files(d, lab, 1)
        write_text("&CONTROL\n/\n", f["in"])
        write_text(text, f["out"])
        t0 = started or time.time() - 600
        write_json({"boot": boot, "started": utc(t0), "started_epoch": t0, "ranks": 48, "pid": 2 ** 22 + 7}, f["launch"])
        if rc is not None:
            write_text(f"{rc} {utc()}\n", f["rc"])
        r = rn.a2_rec(rn.G["jobs_by_id"]["a2:" + lab])
        r.update({"layout": {"name": "48", "ranks": 48, "copies": 1}, "nstep_first": 201,
                  "parts": [{"n": 1, "input": os.path.basename(f["in"]), "restart_mode": None, "nstep": 201,
                             "started": utc(t0)}]})
        write_json(r, rn.a2_path(lab))
        if nel is not None:
            write_json({"electrons": {"n_el": nel}}, os.path.join(d, f"{lab}.meta.json"))
        return d

    def put_nrule(Rm):
        """The C1 marker of gate:nrule that C3 requires (N-F24)."""
        p = os.path.join(Node(Rm).c("c1"), "gates_applied", "gate_nrule.json")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        write_json({"id": "gate:nrule", "gate": "nrule", "decision": {"n": 8}}, p)

    def put_rec(rn, lab, **kw):
        d = rn.L.a2_dir(rn.c, lab); os.makedirs(d, exist_ok=True)
        r = rn.a2_rec(rn.G["jobs_by_id"]["a2:" + lab]); r.update(kw)
        write_json(r, rn.a2_path(lab))

    class _Rd:
        """A scripts/49 Reader stand-in on runner-written A2 records (no energy of an S2 cell exists)."""
        def __init__(self, rn):
            self.rn = rn

        def json_file(self, key):
            return read_json(self.rn.a2_path(key[3:]))

        def relax(self, lab, mode):
            return {"F_eV": {10: -80000.0}, "k_last": 10}

        def record(self, wid):
            return {"validity": {"valid": True, "failed": []}}

    def c_noconf():
        """Round-2 R2V-1 and R2V-2: an SCF failure at k = 0 completes a relaxation without a configuration; its check
        and the checks of children whose partner has no final geometry are skipped (never a check-5 failure); K2
        fails, C2 ends with CAMPAIGN_DONE without a STOP, C3 may start; host_R(136) without a geometry gives K3
        a1_only."""
        sysd, Rm = mini("noconf", cfg={"gates": {"K2": {"K2": "fail"}}})
        rn = c2_runner(Rm)
        os.makedirs(rn.cdir, exist_ok=True)
        c46.dump_public({"schema": "s2-upf-1", "passed": True}, os.path.join(rn.cdir, "upf_check.json"))
        c46.dump_public({"schema": "s2-nodescripts-1", "passed": True}, os.path.join(rn.cdir, "nodescripts_check.json"))
        lab = "s2r_m30_VB136"
        put_part(rn, lab, q47.synthetic_pw_output(n_config=0, end="scf_failed", ranks=48, label=f"{lab}.p1"),
                 boot="m-boot", rc=0)
        assert rn.a2_status(rn.G["jobs_by_id"]["a2:" + lab]) == "done"
        r = read_json(rn.a2_path(lab))
        assert r["end_rule"]["outcome"] == "unconverged_early" and r["end_rule"]["end"] == "scf_failed" and \
            "final_geometry" not in r, r
        st = rn.statuses()
        assert st["a2v:" + lab] == "skipped", st["a2v:" + lab]                      # R2V-2: no Stop, no [5]
        assert g49.k2_eval(r["end_rule"])["K2"] == "fail"
        rc = rn.loop()                                                              # mock K2 gate: fail
        comp = read_json(os.path.join(rn.cdir, "completeness.json"))
        assert rc == 0 and os.path.exists(os.path.join(rn.cdir, "CAMPAIGN_DONE")) and rn.state["K2"] == "fail"
        assert all(v in ("skipped",) for k, v in comp["jobs"].items() if k.startswith("a2v:")), comp["jobs"]
        assert not os.path.exists(os.path.join(rn.cdir, "CAMPAIGN_STOPPED"))
        for x in C2_ORDER:
            assert "validity_final" not in (read_json(rn.a2_path(x)) or {}), x       # nothing recorded as failing
        rn3 = Runner("c3", Rm, MockBackend(Rm)); rn3.boot = "m-boot"; rn3.state = rn.state
        put_nrule(Rm)
        assert rn3.preconditions() is None                                          # C3 runs (A1 tier)
        # host_R(136) without a configuration, V+_R(136) and Sr D(136) complete with final geometries
        sysd2, R2 = mini("noconf2")
        rn = c2_runner(R2)
        hl = "s2r_m30_hostB136"
        put_part(rn, hl, q47.synthetic_pw_output(n_config=0, end="scf_failed", ranks=48, label=f"{hl}.p1"),
                 boot="m-boot", rc=0)
        fg = {"file": "x.final.extxyz", "k": 40, "sha256": "0" * 64}
        for x in ("s2r_m30_VB136", "s2r_m30_Sr136o0_novac"):
            put_rec(rn, x, status="complete", end_rule={"outcome": "accepted_converged"}, final_geometry=fg)
        st = rn.statuses()
        assert st["a2:" + hl] == "done" and st["a2v:s2r_m30_VB136"] == "skipped" and \
            st["a2v:s2r_m30_Sr136o0_novac"] == "skipped", st
        k3 = g49.k3_eval(g49.gather_k3(_Rd(rn)))
        assert k3["K3"] == "a1_only" and not k3["checks_failed"], k3
        # host_R(136) missing (no rerun left); after a K2 fail, host_R(136) not run
        for tag, status in (("noconf3", "missing"), ("noconf4", "not_run_gate")):
            _, R3 = mini(tag)
            rn = c2_runner(R3)
            put_rec(rn, hl, status=status)
            put_rec(rn, "s2r_m30_VB136", status="complete", end_rule={"outcome": "accepted_converged"},
                    final_geometry=fg)
            st = rn.statuses()
            assert st["a2v:s2r_m30_VB136"] == "skipped", (tag, st["a2v:s2r_m30_VB136"])
        return ("SCF failure at k = 0: complete, unconverged_early, no final geometry, its check skipped; K2 fail; C2 "
                "CAMPAIGN_DONE without a STOP, no check recorded; C3 precondition passes; host_R(136) without a "
                "geometry, missing or not run: the children's checks are skipped, K3 a1_only")
    case("(q) section 11 checks without a configuration or a partner (round-2 R2V-1, R2V-2)", c_noconf)

    def c_cap_check():
        """Round-2 R2V-3: two-copy layout; the cap refuses the next relaxation while one copy runs; once the running
        copy completes, its section 11 check still runs and validity_final is written before CAMPAIGN_DONE."""
        sysd, Rm = mini("capchk")
        rn = Runner("c2", Rm, MockBackend(Rm)); rn.boot = "m-boot"
        rn.state = synthetic_state(a2_layout="2x32")
        G = Graph("c2", PHASES["c2"])
        G.add("check:upf", "check", "check", what="upf")
        labs = ("s2r_m30_VB136", "s2r_m30_VB76", "s2r_m30_VX138")
        for i, lab in enumerate(labs, 1):
            G.add("a2:" + lab, "a2", "a2", [], label=lab, order=i, ref=True, member="ref233", cell_kind="V", L="B",
                  j=136, token=None, a1=None, cat="a2")
        for i, lab in enumerate(labs, 1):
            G.add("a2v:" + lab, "a2v", "a2", ["a2:" + lab], label=lab, parent=None, order=i, ref=True,
                  member="ref233", cell_kind="V", L="B", j=136, token=None, leg=None, a1=None, cat="a2_validate")
        rn.be.graph = lambda c, s: G.to_json()
        rn.graph_now()
        os.makedirs(rn.cdir, exist_ok=True)
        c46.dump_public({"schema": "s2-upf-1", "passed": True}, os.path.join(rn.cdir, "upf_check.json"))
        c46.dump_public({"schema": "s2-nodescripts-1", "passed": True}, os.path.join(rn.cdir, "nodescripts_check.json"))
        os.makedirs(os.path.dirname(rn.node.chain_lock), exist_ok=True)
        vac = rn.ref_cells()[0]

        def complete(lab):
            d = rn.L.a2_dir("c2", lab); os.makedirs(d, exist_ok=True)
            f = os.path.join(d, f"{lab}.final.extxyz")
            c46.write_cell(f, vac)
            put_rec(rn, lab, status="complete", end_rule={"outcome": "accepted_converged"},
                    final_geometry={"file": os.path.basename(f), "k": 9, "sha256": sha256_file(f)})
        complete(labs[0]); rn.run_a2v(rn.G["jobs_by_id"]["a2v:" + labs[0]])
        put_rec(rn, labs[1], status="pending", parts=[{"n": 1, "started": utc()}])

        class _Live:
            rc, pid = None, 2 ** 22 + 11

            def poll(self):
                return self.rc
        live = _Live()
        rn.procs[labs[1]] = {"p": live, "kind": "a2", "dir": rn.L.a2_dir("c2", labs[1])}
        rn.h_spent = lambda: 505.0                                         # 505 + 20.6 > 520: the cap refuses
        st = rn.statuses()
        assert st["a2:" + labs[1]] == "running" and st["a2:" + labs[2]] == "pending", st
        rn.a2_phase([j for j in rn.G["jobs_by_id"].values() if j["phase"] == "a2"], st)
        assert rn.capped and rn.capped["job"] == "a2:" + labs[2], rn.capped
        st = rn.statuses()
        assert st["a2v:" + labs[1]] == "pending" and st["a2:" + labs[2]] == "not_started_cap", st     # R2V-3
        complete(labs[1]); live.rc = 0                                       # the running copy completes
        st = rn.statuses()
        assert st["a2:" + labs[1]] == "done" and st["a2v:" + labs[1]] == "pending", st
        rn.schedule(st)                                                      # its check runs (geometry only)
        r = read_json(rn.a2_path(labs[1]))
        assert (r.get("validity_final") or {}).get("valid") is True, r
        st = rn.statuses()
        assert all(_is_terminal(s) for s in st.values()), st
        rn.finish()
        comp = read_json(os.path.join(rn.cdir, "completeness.json"))
        assert comp["jobs"]["a2v:" + labs[1]] == "done" and comp["jobs"]["a2:" + labs[2]] == "not_started_cap"
        return ("cap refused while a copy ran: its check stayed pending, ran after the copy completed, "
                "validity_final written and 'done' in completeness.json before CAMPAIGN_DONE")
    case("(r) section 11 check after a hard-cap refusal, two copies (round-2 R2V-3)", c_cap_check)

    def c_cap_gates():
        """Analyst decision 2026-11-04 (round-2 open item N-C7): a hard-cap refusal sweeps only the jobs that consume
        node-hours; the gates (here K3 after relaxation 5 is refused, its checks skipped) are still evaluated on what
        exists, their decisions applied, and C2 ends with CAMPAIGN_DONE without a STOP."""
        sysd, Rm = mini("capgate", cfg={"gates": {"K2": {"K2": "pass"}, "step0": {"step0": {"outcome": "pass"}},
                                                    "K3": {"K3": "a1_only"}}})
        rn = c2_runner(Rm, a2_layout="48")
        os.makedirs(rn.cdir, exist_ok=True)
        c46.dump_public({"schema": "s2-upf-1", "passed": True}, os.path.join(rn.cdir, "upf_check.json"))
        c46.dump_public({"schema": "s2-nodescripts-1", "passed": True}, os.path.join(rn.cdir, "nodescripts_check.json"))
        os.makedirs(os.path.dirname(rn.node.chain_lock), exist_ok=True)
        fg = {"file": "x.final.extxyz", "k": 40, "sha256": "0" * 64}
        for lab in C2_ORDER[:4]:                                            # relaxations 1-4 and their checks done
            put_rec(rn, lab, status="complete", end_rule={"outcome": "accepted_converged"}, final_geometry=fg,
                    n_config=41, k0_seen=True, validity_final={"valid": True, "failed": []})
            c46.dump_public({"validity": {"valid": True, "failed": []}}, rn.a2v_out(lab))
        rn.h_spent = lambda: 515.0                                          # 515 + 20.6 > 520: relaxation 5 refused
        rc = rn.loop()
        J = read_json(os.path.join(rn.cdir, "completeness.json"))["jobs"]
        assert rc == 0 and os.path.exists(os.path.join(rn.cdir, "CAMPAIGN_DONE")), rc
        assert not os.path.exists(os.path.join(rn.cdir, "CAMPAIGN_STOPPED"))
        assert read_json(os.path.join(rn.cdir, "HARD_CAP.json"))["job"] == "a2:" + C2_ORDER[4]
        assert all(J["a2:" + x] == "not_started_cap" for x in C2_ORDER[4:]), J
        assert all(J["a2v:" + x] == ("done" if i < 4 else "skipped") for i, x in enumerate(C2_ORDER)), J
        gates = {k: v for k, v in J.items() if k.startswith("gate:")}
        assert gates and all(v == "done" for v in gates.values()), gates           # none swept by the cap (N-F14)
        assert rn.state["K3"] == "a1_only" and os.path.exists(rn.gate_marker({"id": "gate:K3"})), rn.state.get("K3")
        k3 = g49.k3_eval(g49.gather_k3(_Rd(rn)))                                    # what scripts/49 gives on these records
        assert k3["K3"] == "a1_only" and not k3["checks_failed"], k3
        rn3 = Runner("c3", Rm, MockBackend(Rm)); rn3.boot = "m-boot"; rn3.state = rn.state
        put_nrule(Rm)
        rn4 = Runner("c4", Rm, MockBackend(Rm)); rn4.boot = "m-boot"; rn4.state = {**rn.state, "campaigns": {"c3": "done"}}
        assert rn3.preconditions() is None and "K3 a1_only" in (rn4.preconditions() or ""), rn4.preconditions()
        return (f"relaxation 5 refused at H_spent 515 h: relaxations 5-10 not_started_cap, checks 5-8 skipped, all "
                f"{len(gates)} gates evaluated (K3 a1_only applied, as scripts/49 gives), CAMPAIGN_DONE, C3 runs, C4 not")
    case("(y) gates after a hard-cap refusal (analyst decision 2026-11-04, N-F14)", c_cap_gates)

    def c_a2_ends():
        """Round-2 F2 / R2-QE-1 / F4: a pw.x error banner is final (unconverged early, STOP, never rerun); an end
        without JOB DONE in this boot without an exit request or an OOM kill is a STOP with RESOLVE; an OOM kill of a
        pw.x rank and a node loss are interruptions (rerun from k = 0)."""
        sysd, Rm = mini("a2ends")
        rn = c2_runner(Rm)
        J = lambda x: rn.G["jobs_by_id"]["a2:" + x]
        lab = "s2r_m30_VB136"
        d = put_part(rn, lab, q47.synthetic_pw_output(n_config=0, end="pw_error", ranks=48, label=f"{lab}.p1"),
                     boot="m-boot", rc=1)
        assert rn.a2_status(J(lab)) == "done" and len(rn.pending_stop) == 1 and \
            "pw.x error routine c_bands" in rn.pending_stop[0], rn.pending_stop        # STOP held (N-F20)
        rn.pending_stop = []                                                         # the loop's part: case (z5)
        r = read_json(rn.a2_path(lab))
        assert r["status"] == "complete" and r["end_rule"]["outcome"] == "unconverged_early" and \
            r["end_rule"]["end"] == "pw_error" and r["reruns_from_zero"] == 0, r
        assert not os.path.isdir(os.path.join(d, "discarded", "r1")) and rn.a2_status(J(lab)) == "done"
        assert g49.k2_eval(r["end_rule"])["K2"] == "fail"
        # an end without JOB DONE in this boot, no exit request, no OOM (a CRASH file): STOP, nothing rerun
        h = "s2r_m30_hostB136"
        dh = put_part(rn, h, q47.synthetic_pw_output(n_config=0, end="killed", ranks=48, label=f"{h}.p1"),
                      boot="m-boot", rc=1)
        write_text("errore on rank 3\n", os.path.join(dh, "CRASH"))
        for _ in range(2):                                                  # every relaunch: the same STOP
            try:
                rn.a2_status(J(h)); raise AssertionError("an unexplained end in this boot was not a STOP")
            except Stop as e:
                assert "RESOLVE" in str(e) and "CRASH" in str(e), e
        assert read_json(rn.a2_path(h))["reruns_from_zero"] == 0
        write_text("unconverged 2026-11-20 QE error confirmed, no node fault\n", os.path.join(dh, "RESOLVE"))
        assert rn.a2_status(J(h)) == "done"
        r = read_json(rn.a2_path(h))
        assert r["end_rule"]["outcome"] == "unconverged_early" and r["end_rule"]["end"].endswith("(operator)"), r
        s = "s2r_m30_Sr136o0_novac"
        ds = put_part(rn, s, q47.synthetic_pw_output(n_config=0, end="killed", ranks=48, label=f"{s}.p1"),
                      boot="m-boot", rc=1)
        write_text("rerun 2026-11-20 the node lost an MPI rank\n", os.path.join(ds, "RESOLVE"))
        assert rn.a2_status(J(s)) == "pending" and read_json(rn.a2_path(s))["reruns_from_zero"] == 1
        assert os.path.isdir(os.path.join(ds, "discarded", "r1"))
        # an OOM kill of a pw.x rank in this boot, and a part of an earlier boot (node loss): interruptions
        o = "s2r_m30_hostB76"
        t0 = time.time() - 300
        put_part(rn, o, q47.synthetic_pw_output(n_config=0, end="killed", ranks=48, label=f"{o}.p1"), boot="m-boot",
                 rc=137, started=t0)
        append_jsonl(os.path.join(sysd, "mock", "oom_events.jsonl"), {"boot": "m-boot", "t": t0 + 60, "task": "pw.x",
                                                                      "pid": 4242})
        assert rn.a2_status(J(o)) == "pending" and read_json(rn.a2_path(o))["interruptions"][-1]["cause"] == "oom"
        v = "s2r_m30_VB76"
        put_part(rn, v, q47.synthetic_pw_output(n_config=0, end="killed", ranks=48, label=f"{v}.p1"), boot="old-boot")
        assert rn.a2_status(J(v)) == "pending"
        r = read_json(rn.a2_path(v))
        assert r["reruns_from_zero"] == 1 and r["interruptions"][-1]["cause"] == "node-loss", r
        return ("pw.x error banner: complete unconverged_early (pw_error), STOP held (N-F20), no rerun, K2 fail; unexplained end in "
                "this boot (CRASH, exit 1): STOP at every look, then RESOLVE unconverged -> unconverged_early, RESOLVE "
                "rerun -> rerun 1; OOM kill of a pw.x rank -> 'oom', a part of an earlier boot -> 'node-loss', both rerun")
    case("(s) A2 ends: pw.x error, unexplained end, RESOLVE, OOM, node loss (round-2 F2, R2-QE-1)", c_a2_ends)

    def c_stop_paths():
        """Round-2 F1, M2, M1: a full /data in the loop, a stop reason that names a temporary path, and a SIGTERM;
        the runner always drains, never leaves KEEP_ALIVE, and a SIGTERM leaves a relaunchable campaign."""
        import builtins, errno
        old_h = {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)}
        out = []
        try:
            for tag in ("enospc", "hygpath", "sigterm"):
                sysd, Rm = mini(tag, boot=f"{tag}-boot")
                write_text("http://localhost:9/latest/meta-data/instance/spot/termination-time\n",
                           os.path.join(Rm, "setup", "s2_spot_url"))
                write_json(synthetic_state(a2_layout=None, commit=None), os.path.join(Rm, "work", "s2", "state.json"))
                rn = Runner("c1", Rm, MockBackend(Rm))
                seen = {"drain": 0, "ka": None}
                od = rn.drain
                rn.drain = lambda: (seen.__setitem__("drain", seen["drain"] + 1), od())[1]
                real_open, full = builtins.open, {"on": False}

                def fake_open(f, mode="r", *a, **k):
                    if full["on"] and any(c in mode for c in "wax+"):
                        raise OSError(errno.ENOSPC, "No space left on device", str(f))
                    return real_open(f, mode, *a, **k)

                def gnow():
                    seen["ka"] = os.path.exists(rn.node.keep_alive)
                    if tag == "enospc":
                        full["on"] = True
                        raise OSError(errno.ENOSPC, "No space left on device", "a job record")
                    raise PermissionError(13, "Permission denied", CHAIN_LOCK)
                oh = rn.housekeeping

                def hk():                                                 # systemd's SIGTERM at a reboot
                    if tag == "sigterm" and not seen.get("sent"):
                        seen["sent"], seen["ka"] = True, os.path.exists(rn.node.keep_alive)
                        os.kill(os.getpid(), signal.SIGTERM); time.sleep(0.05)
                    return oh()
                rn.graph_now, rn.housekeeping = gnow, hk
                builtins.open = fake_open
                try:
                    rc = rn.run()
                finally:
                    builtins.open = real_open
                    full["on"] = False
                if rn.lockfd is not None:
                    os.close(rn.lockfd)
                cj = read_json(os.path.join(rn.cdir, "campaign.json")) or {}
                stopped = os.path.exists(os.path.join(rn.cdir, "CAMPAIGN_STOPPED"))
                assert seen["ka"] is True and not os.path.exists(rn.node.keep_alive), (tag, seen)
                if tag == "sigterm":
                    it = [json.loads(x) for x in open(os.path.join(rn.cdir, "interruptions.jsonl"))]
                    assert rc == 4 and not stopped and cj.get("status") == "running", (rc, stopped, cj.get("status"))
                    assert it[-1]["cause"].startswith("shutdown signal"), it
                    # the relaunch decision of the committed s2_relaunch.sh (paths rewritten; this test's own process
                    # and shell stand in for the processes it must exclude; the start replaced by an echo)
                    t = open(os.path.join(ROOT, "ehpc", "node", "s2_relaunch.sh")).read()
                    for a_, b_ in (("W=/data/work/s2; R=/data/work/ps_s2", f"W={Rm}/work/s2; R={Rm}"),
                                   ('bash "$R/ehpc/node/s2_campaign.sh" "$c"', 'echo "WOULD RELAUNCH $c"; exit 0')):
                        assert a_ in t, a_
                        t = t.replace(a_, b_)
                    t = re.sub(r"pgrep -f '[^']*'", "echo $$ $PPID", t)
                    write_text(t, os.path.join(sysd, "relaunch.sh"))
                    _node_scripts(sysd)                                       # the flock shim on PATH
                    pr = subprocess.run(["bash", os.path.join(sysd, "relaunch.sh")], capture_output=True, text=True,
                                        env=dict(os.environ, PATH=os.path.join(sysd, "bin") + os.pathsep +
                                                 os.environ.get("PATH", "")))
                    assert pr.returncode == 0 and "WOULD RELAUNCH c1" in pr.stdout, (pr.returncode, pr.stdout, pr.stderr)
                    out.append("SIGTERM: interruption logged, status running, no CAMPAIGN_STOPPED, KEEP_ALIVE "
                               "removed, the relaunch decision relaunches c1 (own shell and parent excluded)")
                else:
                    assert rc == 1 and seen["drain"] == 1 and (stopped or tag == "enospc"), (tag, rc, seen, stopped)
                    if tag == "hygpath":
                        assert cj.get("status") == "stopped" and not c46.hygiene_violations(json.dumps(cj)), cj
                        assert "<redacted>" in cj.get("stop_reason", ""), cj.get("stop_reason")
                    out.append(f"{tag}: run() returned {rc}, drained, KEEP_ALIVE removed")
        finally:
            for s, hdl in old_h.items():
                signal.signal(s, hdl)
        return "; ".join(out)
    case("(t) STOP and exit paths: full disk, hygiene-flagged reason, SIGTERM (round-2 F1, M2, M1)", c_stop_paths)

    def c_projection_inputs():
        """Round-2 F3: the projection's C1 MACE timings come from the C1 records through scripts/49 (I-C7b), not from a
        phase wall that holds the host wave and 10 h of stopped node."""
        sysd, Rm = mini("proj")
        L6 = c46.Layout(kind="node", root=Rm)
        recs = [(wid_of("m30", "host"), "host", 1.7), (wid_of("m05", "host"), "host", 1.6)]
        recs += [(wid_of("m30", "D", T="Cs", j=128, n=k, leg=leg), "D", 22.0 / 60.0) for k in range(81)
                 for leg in ("novac", "vac")]
        for w, kind, hrs in recs:
            assert g49.label_campaign(w) == "c1"
            write_json({"work_id": w, "cell_kind": kind, "relax": {"wall_s": hrs * 3600.0},
                        "validity": {"valid": True, "failed": []}}, L6.record("c1", w))
        t0 = time.time() - 17 * 3600.0                                       # 3 h MACE, 10 h stopped, 4 h MACE
        write_json({"phases": {"mace": {"start": t0, "end": t0 + 17 * 3600.0}}},
                   os.path.join(L6.campaign_dir("c1"), "campaign.json"))
        rn = Runner("c2", Rm, MockBackend(Rm)); rn.boot = "m-boot"; rn.state = synthetic_state()
        inp, _ = rn.gate_inputs({"gate": "projection", "point": "after4"})
        assert set(inp) == {"point", "H_spent_h"}, inp
        inp2, _ = g49.derive_inputs("projection", L6, rn.state, dict(inp))
        assert abs(inp2["mace_h_per_relax"] - 2.2 / 60.0) < 1e-12 and abs(inp2["host_wave_h"] - 1.7) < 1e-12, inp2
        return (f"projection inputs {sorted(inp)}; scripts/49 derives {inp2['mace_h_per_relax'] * 60:.2f} min per "
                f"frozen relaxation and a {inp2['host_wave_h']:.2f} h host wave (a 17 h phase wall ignored)")
    case("(u) projection inputs from the C1 records (round-2 F3)", c_projection_inputs)

    def c_oom_pid():
        """Round-2 F4: the wrapper records the command's own pid; an OOM kill of it (kernel lines naming that pid)
        in this boot is a section 13 interruption of the MACE attempt (rerun), not a STOP."""
        sysd, Rm = mini("oom", boot="o-boot")
        nb = NodeBackend(Rm)
        d0 = os.path.join(sysd, "spawn"); os.makedirs(d0)
        pf = os.path.join(d0, "own.pid")
        p = nb.spawn([sys.executable, "-c", f"import os; open({pf!r}, 'w').write(str(os.getpid()))"], cwd=d0,
                     log=os.path.join(d0, "x.log"), rc=os.path.join(d0, "x.rc"))
        p.wait()
        own = int(open(pf).read())
        assert child_pid(os.path.join(d0, "x.rc")) == own and own != p.pid, (own, p.pid)
        rn = Runner("c1", Rm, MockBackend(Rm)); rn.boot = "o-boot"; rn.state = synthetic_state()
        wid = wid_of("ref233", "V", "B", 136)
        d = rn.L.cell_dir("c1", wid); os.makedirs(d, exist_ok=True)
        write_json([{"n": 1, "boot": "o-boot", "started": utc(), "started_epoch": time.time() - 60, "pid": 2 ** 22 + 9}],
                   rn.attempts_path(wid))
        write_text(f"137 {utc()}\n", os.path.join(d, "attempt1.rc"))
        write_text("31337\n", os.path.join(d, "attempt1.rc.pid"))
        append_jsonl(os.path.join(sysd, "mock", "oom_events.jsonl"), {"boot": "o-boot", "t": time.time() - 30,
                                                                      "task": "python", "pid": 31337})
        s = rn.mace_status({"work_id": wid, "xkind": "mace"}, "ok")
        att = read_json(rn.attempts_path(wid))
        assert s == "pending" and att[-1]["cause"] == "oom", (s, att)
        assert rn.be.oom("o-boot", 2 ** 22 + 9) is False                    # the wrapper's pid is not the victim
        return (f"wrapper pid {p.pid}, command pid {own} recorded in <rc>.pid; an OOM kill of the command in this boot "
                f"-> interruption 'oom', rerun (not a STOP)")
    case("(v) OOM evidence by the command's own pid (round-2 F4)", c_oom_pid)

    def c_queue_nb9():
        """Round-2 R2-QE-2: .out.try1 + .out.try2 without .gaveup (the node stopped between the queue's mv and touch)
        is missing, the runner writes .gaveup and the committed queue starts no third attempt. R2-QE-3: a wrong
        electron count, a wrong Cl MD5 or another input name in an A2 part STOPs."""
        sysd, Rm = mini("queue")
        _node_scripts(sysd)
        rn = Runner("c1", Rm, MockBackend(Rm)); rn.boot = "m-boot"; rn.state = synthetic_state()
        os.makedirs(rn.cdir, exist_ok=True)
        lab = "s2_m30_Sr136o0_vac"
        jd = rn.L.sp_dir("c1", lab); os.makedirs(jd, exist_ok=True)
        write_text("&CONTROL\n  calculation = 'scf'\n/\n", os.path.join(jd, f"{lab}.in"))
        write_json({"input_norm_sha256": q47.input_norm_sha256(os.path.join(jd, f"{lab}.in")), "ranks_expected": 64,
                    "electrons": {"n_el": 2.0}}, os.path.join(jd, f"{lab}.meta.json"))
        for k in (1, 2):
            write_text(q47.synthetic_pw_output(n_config=1, calculation="scf", end="killed", ranks=64, label=lab),
                       os.path.join(jd, f"{lab}.out.try{k}"))
        j = {"label": lab, "src": "cell", "cell": wid_of("ref233", "V", "B", 136), "sp_kind": "sp"}
        assert rn.sp_state(j, "ok") == "missing" and os.path.exists(os.path.join(jd, f"{lab}.gaveup"))
        env = dict(os.environ, PATH=os.path.join(sysd, "bin") + os.pathsep + os.environ.get("PATH", ""))
        q = subprocess.run(["bash", os.path.join(Rm, "setup", "qe_queue.sh"), "s2c1"], capture_output=True, text=True,
                           env=env, timeout=120)
        assert "all done" in q.stdout and not os.path.exists(os.path.join(jd, f"{lab}.out")), (q.stdout, q.stderr)
        # N-B9 at every A2 read: electrons, the C1 MD5 of Cl, the input name
        _, R7 = mini("nb9")
        rn = c2_runner(R7)
        c46.dump_public({"schema": "s2-upf-1", "passed": True, "files": {"Cl": {"md5": "f" * 32}, "Ca": {"md5": "e" * 32}}},
                        os.path.join(rn.node.c("c1"), "upf_check.json"))
        bad = []
        for x, kw, nel in (("s2r_m30_VB136", {}, 3.0), ("s2r_m30_hostB136", {"symbols": ["Cl", "H"]}, None),
                           ("s2r_m30_VB76", {"label": "another.p1"}, None)):
            text = q47.synthetic_pw_output(n_config=2, end="killed", ranks=48, **{"label": f"{x}.p1", **kw})
            put_part(rn, x, text, boot="m-boot", rc=1, nel=nel)
            try:
                rn.a2_status(rn.G["jobs_by_id"]["a2:" + x]); raise AssertionError(f"{x} accepted")
            except (S2Error, getattr(q47, "S2Error", S2Error)) as e:      # a refusal: the runner STOPs (N-9)
                bad.append(str(e).split(": ", 1)[-1][:60])
        return ("try1 + try2 without .gaveup: missing, .gaveup written by the runner, the queue skips it (no third "
                f"attempt); N-B9 refusals: {bad}")
    case("(w) queue state between mv and touch; N-B9 at every A2 read (round-2 R2-QE-2, R2-QE-3)", c_queue_nb9)

    def c_watchdog():
        """Round-2 S2: a hung MACE attempt and a pw.x output not written for longer than the limit STOP."""
        sysd, Rm = mini("watch")
        rn = Runner("c1", Rm, MockBackend(Rm)); rn.boot = "m-boot"; rn.state = synthetic_state()
        wid = wid_of("ref233", "V", "B", 136)
        d = rn.L.cell_dir("c1", wid); os.makedirs(d, exist_ok=True)
        write_json([{"n": 1, "boot": "m-boot", "started": utc(), "started_epoch": time.time() - 4 * 3600, "pid": 1}],
                   rn.attempts_path(wid))

        class _Live:
            pid = 2 ** 22 + 13

            def poll(self):
                return None
        rn.procs[wid] = {"p": _Live(), "kind": "mace", "dir": d}
        msgs = []
        try:
            rn.mace_status({"work_id": wid, "xkind": "mace"}, "ok"); raise AssertionError("a 4 h MACE attempt ran on")
        except Stop as e:
            msgs.append(str(e)[:50])
        rn2 = c2_runner(mini("watch2")[1])
        lab = "s2r_m30_VB136"
        dd = put_part(rn2, lab, q47.synthetic_pw_output(n_config=1, end="killed", ranks=48, label=f"{lab}.p1"),
                      boot="m-boot")
        out = rn2.part_files(dd, lab, 1)["out"]
        os.utime(out, (time.time() - 3 * 3600, time.time() - 3 * 3600))
        rn2.procs[lab] = {"p": _Live(), "kind": "a2", "dir": dd}
        rn2.t_start = time.time()                                   # a relaunch: an old output is not stale yet
        rn2.a2_monitor(rn2.G["jobs_by_id"]["a2:" + lab])
        rn2.t_start, rn2.last_counts = time.time() - 3 * 3600, {}   # a runner that has watched it for 3 h
        try:
            rn2.a2_monitor(rn2.G["jobs_by_id"]["a2:" + lab]); raise AssertionError("a stalled pw.x output ran on")
        except Stop as e:
            msgs.append(str(e)[:50])
        return f"STOP for a human: {msgs}"
    case("(x) hung child watchdog (round-2 S2, N-F13)", c_watchdog)

    # ---------------------------------------------------------------- round-3 cases
    def r3_relaunch(sysd, Rm, btime=None, campaign_sh=False):
        """The relaunch decision of the committed s2_relaunch.sh with its paths rewritten (as case t); with campaign_sh
        it starts the s2_campaign.sh of <Rm>/work/ps_s2 (a path-rewritten copy the case puts there, round 4)."""
        t = open(os.path.join(ROOT, "ehpc", "node", "s2_relaunch.sh")).read()
        reps = [("W=/data/work/s2; R=/data/work/ps_s2", f"W={Rm}/work/s2; R={Rm}" + ("/work/ps_s2" if campaign_sh else ""))]
        if not campaign_sh:
            reps.append(('bash "$R/ehpc/node/s2_campaign.sh" "$c"', 'echo "WOULD RELAUNCH $c"; exit 0'))
        for a_, b_ in reps:
            assert a_ in t, a_
            t = t.replace(a_, b_)
        t = re.sub(r"pgrep -f '[^']*'", "echo $$ $PPID", t)
        if btime is not None:
            write_text(f"cpu 0\nbtime {int(btime)}\n", os.path.join(sysd, "procstat"))
            t = t.replace("/proc/stat", os.path.join(sysd, "procstat"))
            if sys.platform == "darwin":
                t = t.replace("stat -c %Y", "stat -f %m")
        write_text(t, os.path.join(sysd, "relaunch.sh"))
        _node_scripts(sysd)
        pr = subprocess.run(["bash", os.path.join(sysd, "relaunch.sh")], capture_output=True, text=True,
                            env=dict(os.environ, PATH=os.path.join(sysd, "bin") + os.pathsep + os.environ.get("PATH", "")))
        return pr.returncode, pr.stdout + pr.stderr

    def r3_signals():
        return {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)}

    def r3_restore(old):
        for s, hdl in old.items():
            signal.signal(s, hdl)

    def r3_standin(exit_file, life=20.0):
        """A pw.x stand-in that honours the exit file (ends within 0.05 s of it) or ends after life seconds."""
        return subprocess.Popen(["bash", "-c", f'for i in $(seq {int(life / 0.05)}); do [ -e "${{1}}" ] && exit 0; '
                                               f'sleep 0.05; done; exit 0', "standin", exit_file])

    def r3_part(rn, lab, text, *, pid, rc=None, ranks=32, lay="2x32", t0=None, pids=None):
        d = rn.L.a2_dir(rn.c, lab); os.makedirs(d, exist_ok=True)
        f = rn.part_files(d, lab, 1)
        write_text("&CONTROL\n/\n", f["in"]); write_text(text, f["out"])
        t0 = t0 or time.time() - 3600
        Lj = {"boot": rn.boot, "started": utc(t0), "started_epoch": t0, "ranks": ranks, "pid": pid}
        if pids is not None:
            Lj["pids"] = sorted(pids)
            rn.a2_note_pids(lab, pids)
        write_json(Lj, f["launch"])
        if rc is not None:
            write_text(f"{rc} {utc()}\n", f["rc"])
        r = rn.a2_rec(rn.G["jobs_by_id"]["a2:" + lab])
        r.update({"layout": {"name": lay, "ranks": ranks, "copies": 2 if lay == "2x32" else 1}, "nstep_first": 201,
                  "parts": [{"n": 1, "input": os.path.basename(f["in"]), "restart_mode": None, "nstep": 201,
                             "started": utc(t0)}]})
        write_json(r, rn.a2_path(lab))
        return d

    def r3_c2(tag, cfg, **over):
        sysd, Rm = mini(tag, cfg=cfg)
        rn = c2_runner(Rm, **over)
        os.makedirs(rn.cdir, exist_ok=True)
        c46.dump_public({"schema": "s2-upf-1", "passed": True}, os.path.join(rn.cdir, "upf_check.json"))
        c46.dump_public({"schema": "s2-nodescripts-1", "passed": True}, os.path.join(rn.cdir, "nodescripts_check.json"))
        os.makedirs(os.path.dirname(rn.node.chain_lock), exist_ok=True)
        rn.h_spent = lambda: 100.0

        def refuse(*a, **k):
            raise RuntimeError("spawn refused in this case")
        rn.be.spawn = refuse
        fast = {"n": 0}

        def sl(s):
            fast["n"] += 1
            if fast["n"] > 2000:
                raise SystemExit("too many ticks")
            time.sleep(min(s, 0.05))
        rn.be.sleep = sl
        return sysd, Rm, rn

    def r3_done(rn, lab, *, valid=True):
        """A complete A2 relaxation with its section 11 check recorded."""
        put_rec(rn, lab, status="complete", end_rule={"outcome": "accepted_converged"}, n_config=41, k0_seen=True,
                final_geometry={"file": f"{lab}.final.extxyz", "k": 40, "sha256": "0" * 64},
                validity_final={"valid": valid, "failed": [] if valid else [5]})
        c46.dump_public({"validity": {"valid": valid, "failed": [] if valid else [5]}}, rn.a2v_out(lab))

    def r3_markers(rn, ids):
        for gid in ids:
            p = rn.gate_marker({"id": gid}); os.makedirs(os.path.dirname(p), exist_ok=True)
            write_json({"id": gid, "decision": {}}, p)

    def c_casefold():
        """Round-3 R3-C1-1 (N-F15): the gate names N and n folded to one file on the laptop's case-insensitive volume;
        now no two job ids, gate names, marker names, labels or work ids of C1-C4 fold together, and archive() refuses
        a stage with such names or with the trace they leave on a case-insensitive volume."""
        rn = Runner("c1", R, MockBackend(R))
        sts = [("c1", synthetic_state(a2_layout=None)), ("c1", synthetic_state(a2_layout="2x32")),
               ("c1", synthetic_state(a2_layout="64")), ("c2", synthetic_state()), ("c3", synthetic_state()),
               ("c3", synthetic_state(n=10, pose={"Cs": "multi", "Cl": "multi"})), ("c4", synthetic_state())]
        cats = 0
        for c, st in sts:
            g = graph(c, st, sites=lambda m: S2.get(m) or site_sets(m))
            J = g["jobs"]
            names = {"job ids": [j["id"] for j in J], "gate names": [j["gate"] for j in J if j["kind"] == "gate"],
                     "gate files": [os.path.basename(rn.L.gate(c, j["gate"])) for j in J if j["kind"] == "gate"],
                     "markers": [os.path.basename(rn.gate_marker(j))[:-5] + s for j in J if j["kind"] == "gate"
                                 for s in (".json", ".gate.json", ".inputs.json")],
                     "labels": [j["label"] for j in J if j.get("label")],
                     "work ids": [w for j in J for w in ([j.get("work_id")] + list(j.get("work_ids") or []) +
                                                         list((j.get("legs") or {}).values())) if w]}
            for k, v in names.items():
                assert not casefold_dupes(v), (c, k, casefold_dupes(v))
                cats += 1
        assert "nrule" in [j.get("gate") for j in graph("c1", sts[0][1], sites=lambda m: S2[m])["jobs"]]
        assert casefold_dupes(["gate:N", "gate:n", "gate:G1"]) == [["gate:N", "gate:n"]]
        assert casefold_dupes(list(getattr(g49, "GATE_NAMES", ()))) == []
        # what a case-insensitive volume does with the two old names (reported, not asserted: the volume decides)
        d = os.path.join(base, "casefold", "probe"); os.makedirs(d, exist_ok=True)
        write_text("1", os.path.join(d, "N.json")); write_text("2", os.path.join(d, "n.json"))
        folds = len(os.listdir(d)) == 1
        # archive: the trace of a collision on a case-insensitive stage, and a clean stage
        refusals = []
        for tag, files in (("gatefile", {"gates/N.json": {"gate": "n", "decision": {"n": 10}}}),
                           ("marker", {"gates_applied/gate_N.json": {"id": "gate:n", "gate": "nrule"}})):
            st_ = os.path.join(base, "casefold", tag)
            for rel, obj in files.items():
                write_json(obj, os.path.join(st_, "work", "c1", rel))
            try:
                archive(st_, "c1", os.path.join(base, "casefold", tag + "_out")); raise AssertionError(f"{tag} accepted")
            except S2Error as e:
                assert "N-F15" in str(e), e
                refusals.append(tag)
        ok = os.path.join(base, "casefold", "clean")
        for nm in ("G1", "N", "nrule", "pose"):
            write_json({"gate": nm, "decision": {}}, os.path.join(ok, "work", "c1", "gates", f"{nm}.json"))
            write_json({"id": f"gate:{nm}", "gate": nm}, os.path.join(ok, "work", "c1", "gates_applied", f"gate_{nm}.json"))
        out = os.path.join(base, "casefold", "clean_out")
        archive(ok, "c1", out)
        assert sorted(os.listdir(os.path.join(out, "gates"))) == ["G1.json", "N.json", "nrule.json", "pose.json"]
        return (f"{cats} name categories of {len(sts)} graphs unique after lower-casing (gate:nrule); this volume "
                f"{'folds' if folds else 'keeps'} N.json/n.json; archive refuses {refusals}, keeps the 4 C1 gate files")
    case("(z1) case-fold uniqueness of gate names, markers, labels and work ids (round-3 R3-C1-1)", c_casefold)

    def c_smoke_stop():
        """Round-3 R3-C1-2, R3-C1-3, R3-C1-5 (N-F16, N-F17, N-D10): the smoke test n1 ends with QE's error banner: one
        attempt (no rerun, no interruption), missing; the throughput row STOPs naming the smoke tests (no unexpected
        error); a new checkout HEAD without c1/NODE_FIX is refused; with NODE_FIX and RESOLVE 'rerun' the relaunch
        reruns n1, n3 and the restart test, writes smoke.json with c0, runs the throughput row and reaches MACE."""
        sysd = os.path.join(base, "smk"); Rx = os.path.join(sysd, "data")
        for dd in ("data/work/s2", "data/jobs", "data/setup", "data/pseudo", "mock", "bin"):
            os.makedirs(os.path.join(sysd, dd), exist_ok=True)
        _node_scripts(sysd)
        sp2 = _Spot()
        write_text(f"http://localhost:{sp2.port}/latest/meta-data/instance/spot/termination-time\n",
                   os.path.join(Rx, "setup", "s2_spot_url"))
        bt = "s" * 8 + "-boot-s"
        write_text(bt, os.path.join(sysd, "mock", "boot_id"))
        write_text(f"{time.time() - 60:.0f}", os.path.join(sysd, "mock", f"btime.{bt}"))
        cfg = {"gates": {"throughput": {"a2_layout": "48"}, "N": {"n": 8, "gateN": {t: True for t in c46.TOKENS}}}}
        write_json(cfg, os.path.join(sysd, "mock", "config.json"))
        write_json({"s2smoke_ref232_n1": {"pw_error_at": 0}}, os.path.join(sysd, "mock", "pw_scenarios.json"))
        write_json(synthetic_state(a2_layout=None, commit=None), os.path.join(Rx, "work", "s2", "state.json"))
        envx = dict(os.environ, PATH=os.path.join(sysd, "bin") + os.pathsep + os.environ.get("PATH", ""))
        envx.pop("S2_LOCK_FD", None)
        cd = c46.Layout(kind="node", root=Rx).campaign_dir("c1")

        def go(tag, until=None):
            lf = open(os.path.join(base, f"runner_smk_{tag}.log"), "w")
            p = subprocess.Popen([sys.executable, me, "run", "--campaign", "c1", "--root", Rx, "--mock"], env=envx,
                                 stdout=lf, stderr=subprocess.STDOUT, start_new_session=True)
            procs[f"smk_{tag}"] = p
            t = time.time()
            while p.poll() is None and time.time() - t < 150:
                if until is not None and until():
                    os.killpg(p.pid, signal.SIGKILL); p.wait(); return None
                time.sleep(0.1)
            assert p.poll() is not None, f"run {tag} did not end"
            return p.returncode
        rc1 = go("1")
        cj = read_json(os.path.join(cd, "campaign.json")) or {}
        n1d = os.path.join(cd, "smoke", "s2smoke_ref232_n1")
        d1 = read_json(os.path.join(n1d, "s2smoke_ref232_n1.p1.done.json")) or {}
        intr = [json.loads(x) for x in open(os.path.join(cd, "interruptions.jsonl"))] \
            if os.path.exists(os.path.join(cd, "interruptions.jsonl")) else []
        assert rc1 == 3 and "smoke tests n1/n3 incomplete" in (cj.get("stop_reason") or ""), (rc1, cj.get("stop_reason"))
        assert d1.get("status") == "missing" and "pw.x error" in (d1.get("reason") or ""), d1
        assert not os.path.isdir(os.path.join(n1d, "discarded")), "n1 was rerun"           # one attempt (N-D10)
        assert not any(str(x.get("label", "")).startswith("s2smoke_ref232_n1") for x in intr), intr
        assert (read_json(os.path.join(cd, "smoke.json")) or {}).get("mapping", {}).get("c0") is None
        assert not glob.glob(os.path.join(cd, "tp", "*", "*.launch.json")), "a throughput run started"
        cfg["git_head"] = "1" * 40
        write_json(cfg, os.path.join(sysd, "mock", "config.json"))                  # the fix is committed
        rc2 = go("2")
        cj = read_json(os.path.join(cd, "campaign.json")) or {}
        assert rc2 == 3 and "is not the recorded S2 commit" in (cj.get("stop_reason") or ""), (rc2, cj.get("stop_reason"))
        write_text("1" * 40 + " 2026-11-04 smoke-test input error fixed (self-test)\n", os.path.join(cd, "NODE_FIX"))
        write_text("rerun 2026-11-04 after the committed fix (self-test)\n", os.path.join(n1d, "RESOLVE"))
        write_json({"s2smoke_ref232_rst": {"delay": 0.4}}, os.path.join(sysd, "mock", "pw_scenarios.json"))
        reached = lambda: "mace" in ((read_json(os.path.join(cd, "campaign.json")) or {}).get("phases") or {})  # noqa: E731
        rc3 = go("3", until=reached)
        st = read_json(os.path.join(Rx, "work", "s2", "state.json"))
        sm = read_json(os.path.join(cd, "smoke.json")) or {}
        assert rc3 is None and reached(), (rc3, open(os.path.join(base, "runner_smk_3.log")).read()[-800:])
        assert st["commit"] == "1" * 40 and st["commit_history"][-1]["via"] == "c1/NODE_FIX", st.get("commit_history")
        cj3 = read_json(os.path.join(cd, "campaign.json")) or {}
        assert cj3.get("start_commit") == "0" * 40 and cj3.get("commit") == "1" * 40 and \
            len(cj3.get("commit_history") or []) == 1, {k: cj3.get(k) for k in ("start_commit", "commit", "commit_history")}
        assert glob.glob(os.path.join(cd, "NODE_FIX.used.*")) and not os.path.exists(os.path.join(cd, "NODE_FIX"))
        assert all(glob.glob(os.path.join(cd, "discarded", "commit_*", f"{w}_check.json")) and   # round-5 R5-2
                   os.path.exists(os.path.join(cd, f"{w}_check.json")) for w in ("upf", "nodescripts", "mace"))
        assert isinstance(sm["mapping"]["c0"], int) and sm["mapping"]["affine_slope_1"], sm.get("mapping")
        assert os.path.exists(os.path.join(cd, "throughput.json")) and glob.glob(os.path.join(n1d, "discarded",
                                                                                              "resolved_*"))
        # NODE_FIX refused outside a stopped C1
        _, Ry = mini("nodefix", cfg={"git_head": "2" * 40})
        msgs = []
        for c, stopped in (("c1", False), ("c3", True)):
            rn = Runner(c, Ry, MockBackend(Ry)); rn.boot = "m-boot"; rn.was_stopped = stopped
            rn.state = synthetic_state(commit="1" * 40, campaigns={"c1": "running"})
            write_text("2" * 40 + " 2026-11-04 note\n", os.path.join(rn.node.c("c1"), "NODE_FIX"))
            try:
                rn.check_commit(); raise AssertionError(f"NODE_FIX accepted in {c}")
            except Stop as e:
                assert "NODE_FIX refused" in str(e), e
                msgs.append(str(e).split(": ", 1)[1][:40])
        return (f"n1 pw.x error: one attempt, missing, no interruption; throughput STOP names the smoke tests; new HEAD "
                f"refused; NODE_FIX + RESOLVE rerun: commit_history (also in campaign.json beside start_commit, round-4 R4-C1-6), c0 {sm['mapping']['c0']}, throughput row, MACE "
                f"phase reached; NODE_FIX refused: {msgs}")
    case("(z2) smoke-test failure: STOP, NODE_FIX and RESOLVE (round-3 R3-C1-2, -3, -5)", c_smoke_stop)

    def c_spot_reach():
        """Round-3 R3-C1-7 (N-F18): an unreachable spot endpoint STOPs before any job (the checks and smoke n1 not
        run); a last good poll older than the limit STOPs; a fresh one passes."""
        old = r3_signals()
        try:
            sysd, Rm = mini("spotdown", boot="sd-boot")
            write_text("http://localhost:9/latest/meta-data/instance/spot/termination-time\n",
                       os.path.join(Rm, "setup", "s2_spot_url"))
            write_json(synthetic_state(a2_layout=None, commit=None), os.path.join(Rm, "work", "s2", "state.json"))
            rn = Runner("c1", Rm, MockBackend(Rm)); rn.be.spot_first_s = 1.0
            rc = rn.run()
            if rn.lockfd is not None:
                os.close(rn.lockfd)
        finally:
            r3_restore(old)
        cj = read_json(os.path.join(rn.cdir, "campaign.json")) or {}
        assert rc == 3 and "spot endpoint not reachable" in (cj.get("stop_reason") or ""), (rc, cj.get("stop_reason"))
        assert not os.path.exists(os.path.join(rn.cdir, "upf_check.json")) and \
            not os.path.exists(os.path.join(rn.cdir, "mace_check.json")) and not os.path.isdir(os.path.join(rn.cdir, "smoke"))
        rn2 = Runner("c1", Rm, MockBackend(Rm)); rn2.boot = "sd-boot"
        rn2.poller_t0 = time.time() - 400
        hb = os.path.join(rn2.node.spot, "heartbeat.sd-boot")
        write_text(f"{time.time() - 350:.0f} x ok=1 err=0\n", hb)
        try:
            rn2.spot_check(); raise AssertionError("a stale endpoint passed")
        except Stop as e:
            assert "last good poll" in str(e), e
        write_text(f"{time.time():.0f} x ok=9 err=0\n", hb)
        assert rn2.spot_check() is True
        return "unreachable URL: STOP before check:upf, check:mace and smoke n1; a 350 s old good poll STOPs; a fresh one passes"
    case("(z3) spot endpoint reachability (round-3 R3-C1-7)", c_spot_reach)

    def c_smoke2_fold():
        """Round-3 missed item (N-F19): smoke2.json without its fold into smoke.json (a node loss between the writes)
        leaves rec:smoke2 pending; run_record folds first; C2 requires at_layout at a layout other than 48."""
        sysd, Rm = mini("smk2")
        rn = Runner("c1", Rm, MockBackend(Rm)); rn.boot = "m-boot"; rn.state = {"a2_layout": "2x32"}
        os.makedirs(rn.cdir, exist_ok=True)
        write_json({"schema": "s2-smoke-1", "mapping": {"c0": 1, "affine_slope_1": True, "nstep_first": 200,
                                                         "restart_files": ["{prefix}.save/x"]}, "restart_possible": True},
                   os.path.join(rn.cdir, "smoke.json"))
        lab = "s2smoke_ref232_rst2x32"
        write_json({"schema": "s2-smoke-1", "label": lab, "restart_possible": False}, os.path.join(rn.cdir, "smoke2.json"))
        j = {"id": "rec:smoke2", "kind": "record", "what": "smoke2", "label": lab, "deps": [], "phase": "smoke2"}
        assert rn.status(j, {}) == "pending"                                     # was 'done' (the window)
        rn.run_record(j)
        sm = read_json(os.path.join(rn.cdir, "smoke.json"))
        assert sm["at_layout"]["label"] == lab and sm["restart_possible"] is False and rn.status(j, {}) == "done", sm
        rc2 = Runner("c2", Rm, MockBackend(Rm)); rc2.boot = "m-boot"
        rc2.state = synthetic_state(a2_layout="2x32", campaigns={"c1": "done"}); rc2.state["step0"] = {}
        sm.pop("at_layout"); write_json(sm, os.path.join(rn.cdir, "smoke.json"))
        try:
            rc2.preconditions(); raise AssertionError("C2 started without the test at its layout")
        except Stop as e:
            assert "at_layout" in str(e), e
        return "smoke2.json alone: rec:smoke2 pending; the fold gives at_layout and restart_possible false; C2 STOPs without at_layout"
    case("(z4) smoke test at the A2 layout: fold before smoke2.json (round-3 missed item)", c_smoke2_fold)

    def c_twocopy_stop():
        """Round-3 R3-1 (N-F20): at the 2x32 layout a STOP-asking end of the K2 cell or of a K3 cell is held until the
        gate has applied, so the running partner gets the 'gate' exit file at once and is killed_by_gate (outputs
        moved aside unread) instead of running on through the drain; the bfgs_failed control ends without a STOP."""
        out = []
        for tag, end, rc_want in (("a", "pw_error", 3), ("c", "bfgs_failed", 0)):
            sysd, Rm, rn = r3_c2("tc_" + tag, {"gates": {"K2": {"K2": "fail"}}}, a2_layout="2x32")
            A, B = "s2r_m30_VB136", "s2r_m30_hostB136"
            r3_part(rn, A, q47.synthetic_pw_output(n_config=0, end=end, ranks=32, label=f"{A}.p1"), pid=2 ** 22 + 7,
                    rc=1 if end == "pw_error" else 0)
            dB = rn.L.a2_dir(rn.c, B)
            sb = r3_standin(os.path.join(dB, "tmp", f"{B}.EXIT"))
            r3_part(rn, B, q47.synthetic_pw_output(n_config=12, end="killed", ranks=32, label=f"{B}.p1"), pid=sb.pid)
            rn.procs[B] = {"p": sb, "kind": "a2", "dir": dB}
            t = time.time(); rc = rn.loop(); dt = time.time() - t
            sb.wait(timeout=30)
            rb = read_json(rn.a2_path(B))
            req = read_json(os.path.join(dB, "exit_request.json")) or {}
            stopped = os.path.exists(os.path.join(rn.cdir, "CAMPAIGN_STOPPED"))
            assert rc == rc_want and rn.state.get("K2") == "fail" and req.get("reason") == "gate", (tag, rc, rn.state.get("K2"), req)
            assert rb["status"] == "killed_by_gate" and os.path.isdir(os.path.join(dB, "discarded", "killed_by_gate")) \
                and not os.path.exists(rn.part_files(dB, B, 1)["out"]), rb
            assert dt < 8.0, f"the drain waited {dt:.1f} s for the partner"
            assert stopped == (end == "pw_error"), stopped
            out.append(f"{tag} {end}: rc {rc} in {dt:.1f} s, K2 fail, host_R exit 'gate', killed_by_gate")
        # (b) Sr D+V(76) ends with QE's error banner while Ca D(136) runs: K3 a1_only first, Ca D(136) killed
        sysd, Rm, rn = r3_c2("tc_b", {"gates": {"K3": {"K3": "a1_only"}}}, a2_layout="2x32")
        rn.state.update({"K2": "pass", "step0": {"attempts": 1, "outcome": "pass"}})
        r3_markers(rn, ("gate:step0@1", "gate:K2", "gate:step0@4", "gate:projection@after4"))
        for lab in C2_ORDER[:7]:
            r3_done(rn, lab)
        P, Q = C2_ORDER[7], C2_ORDER[8]
        r3_part(rn, P, q47.synthetic_pw_output(n_config=0, end="pw_error", ranks=32, label=f"{P}.p1"), pid=2 ** 22 + 8, rc=1)
        dQ = rn.L.a2_dir(rn.c, Q)
        sq = r3_standin(os.path.join(dQ, "tmp", f"{Q}.EXIT"))
        r3_part(rn, Q, q47.synthetic_pw_output(n_config=5, end="killed", ranks=32, label=f"{Q}.p1"), pid=sq.pid)
        rn.procs[Q] = {"p": sq, "kind": "a2", "dir": dQ}
        t = time.time(); rc = rn.loop(); dt = time.time() - t
        sq.wait(timeout=30)
        rq = read_json(rn.a2_path(Q))
        assert rc == 3 and rn.state.get("K3") == "a1_only" and rq["status"] == "killed_by_gate" and dt < 8.0, \
            (rc, rn.state.get("K3"), rq.get("status"), dt)
        assert (read_json(os.path.join(dQ, "exit_request.json")) or {}).get("reason") == "gate"
        out.append(f"b: Sr D+V(76) pw_error, K3 a1_only applied, Ca D(136) killed_by_gate, rc {rc} in {dt:.1f} s")
        return "; ".join(out)
    case("(z5) a held STOP lets K2/K3 kill the running copy (round-3 R3-1)", c_twocopy_stop)

    def c_sigterm_sync():
        """Round-3 R3-3 (N-F21): a shutdown SIGTERM that kills a synchronous child (the K3 gate, validate-a2, a
        scripts/46 geometry job) is an interruption: rc 4, no CAMPAIGN_STOPPED, the job still pending, and the relaunch
        decision relaunches; a real STOP followed by SIGTERM exits as stopped (rc 3)."""
        old = r3_signals()
        out = []
        try:
            for what in ("gate", "a2v"):
                sysd, Rm, rn = r3_c2("st_" + what, {}, a2_layout="48")
                signal.signal(signal.SIGTERM, lambda *_: setattr(rn, "shutdown", True))
                rn.state.update({"K2": "pass", "step0": {"attempts": 1, "outcome": "pass"}})
                r3_markers(rn, ("gate:step0@1", "gate:K2", "gate:step0@4", "gate:projection@after4"))
                for lab in C2_ORDER[:7]:
                    r3_done(rn, lab)
                last = C2_ORDER[7]
                if what == "gate":
                    r3_done(rn, last)
                else:
                    ff = os.path.join(rn.L.a2_dir(rn.c, last), f"{last}.final.extxyz"); write_text("synthetic\n", ff)
                    put_rec(rn, last, status="complete", end_rule={"outcome": "accepted_converged"}, n_config=41,
                            final_geometry={"file": os.path.basename(ff), "k": 40, "sha256": sha256_file(ff)})
                    rn.a2v_files = lambda j, ff=ff: {"final": ff, "parent_final": "x"}

                def killed(*a, **k):
                    os.kill(os.getpid(), signal.SIGTERM); time.sleep(0.05)
                    return -15                                              # the child died with the same shutdown
                if what == "gate":
                    rn.be.gate = killed
                else:
                    rn.be.run46 = killed
                rn.set_campaign("running")
                rc = rn.loop()
                cj = read_json(os.path.join(rn.cdir, "campaign.json")) or {}
                pend = not os.path.exists(rn.gate_marker({"id": "gate:K3"})) if what == "gate" else \
                    "validity_final" not in (read_json(rn.a2_path(last)) or {})
                assert rc == 4 and not os.path.exists(os.path.join(rn.cdir, "CAMPAIGN_STOPPED")) and \
                    cj.get("status") == "running" and pend, (what, rc, cj.get("status"), pend)
                rr, so = r3_relaunch(sysd, Rm)
                assert rr == 0 and "WOULD RELAUNCH c2" in so, (rr, so)
                out.append(f"{what}: rc 4, running, pending, relaunched")
            # a scripts/46 geometry job killed by the shutdown: pending, no STOP
            sysd, Rm = mini("st_g46")
            rn = Runner("c1", Rm, MockBackend(Rm)); rn.boot = "m-boot"; rn.state = synthetic_state()
            os.makedirs(os.path.join(rn.cdir, "jobs46"), exist_ok=True)
            rn.shutdown = True
            rn.be.run46 = lambda *a, **k: -15
            rn.run_g46({"id": "region:ref233_B136", "kind": "g46", "action": "region", "member": "ref233", "L": "B",
                        "site": 136})
            out.append("g46: no STOP")
            # a real STOP, then SIGTERM: stopped, rc 3
            rn.begin_stop("a real STOP (self-test)"); rn.shutdown = True
            assert rn.drain() == 3 and "(stopped)" in open(os.path.join(rn.cdir, "campaign.log")).read().splitlines()[-1]
            out.append("STOP then SIGTERM: rc 3, logged stopped")
        finally:
            r3_restore(old)
        return "; ".join(out)
    case("(z6) SIGTERM while a synchronous child runs (round-3 R3-3)", c_sigterm_sync)

    def c_sigterm_async():
        """Round-3 missed item (N-F21): the shutdown SIGTERM reaches the runner inside statuses() and kills a running
        A2 part and a MACE attempt without rc files; neither is classified in this boot (rc 4, no STOP); after the
        reboot the A2 part is an interruption (rerun) and the MACE attempt 'node-loss'."""
        old = r3_signals()
        out = []
        try:
            sysd, Rm, rn = r3_c2("as_a2", {"gates": {"K2": {"K2": "pass"}}}, a2_layout="48")
            signal.signal(signal.SIGTERM, lambda *_: setattr(rn, "shutdown", True))
            lab = C2_ORDER[0]
            sl = subprocess.Popen(["sleep", "60"])
            r3_part(rn, lab, q47.synthetic_pw_output(n_config=12, end="killed", ranks=48, label=f"{lab}.p1"),
                    pid=sl.pid, ranks=48, lay="48")
            rn.procs[lab] = {"p": sl, "kind": "a2", "dir": rn.L.a2_dir(rn.c, lab)}
            orig, fired = rn.status, {"n": 0}

            def status(j, st):
                if not fired["n"]:
                    fired["n"] = 1
                    os.kill(os.getpid(), signal.SIGTERM); sl.terminate(); sl.wait()
                return orig(j, st)
            rn.status = status
            rn.set_campaign("running")
            rc = rn.loop()
            cj = read_json(os.path.join(rn.cdir, "campaign.json")) or {}
            assert rc == 4 and not os.path.exists(os.path.join(rn.cdir, "CAMPAIGN_STOPPED")) and cj.get("status") == "running", \
                (rc, cj.get("status"))
            rn2 = c2_runner(Rm, boot="n-boot", a2_layout="48")
            write_text("n-boot", os.path.join(sysd, "mock", "boot_id"))
            assert rn2.a2_status(rn2.G["jobs_by_id"]["a2:" + lab]) == "pending"
            r = read_json(rn2.a2_path(lab))
            assert r["reruns_from_zero"] == 1 and r["interruptions"][-1]["cause"] == "node-loss", r
            out.append("A2: rc 4, no STOP; next boot: node-loss, rerun")
            sysd, Rm = mini("as_mace")
            rm = Runner("c1", Rm, MockBackend(Rm)); rm.boot = "m-boot"; rm.state = synthetic_state()
            signal.signal(signal.SIGTERM, lambda *_: setattr(rm, "shutdown", True))
            rm.graph_now(); os.makedirs(rm.cdir, exist_ok=True)
            wid = wid_of("ref233", "host")
            d = rm.L.cell_dir("c1", wid); os.makedirs(d, exist_ok=True)
            sm_ = subprocess.Popen(["sleep", "60"])
            write_json([{"n": 1, "boot": "m-boot", "started": utc(), "started_epoch": time.time() - 60, "pid": sm_.pid}],
                       rm.attempts_path(wid))
            rm.procs[wid] = {"p": sm_, "kind": "mace", "dir": d}
            orig2, fired2 = rm.status, {"n": 0}

            def status2(j, st):
                if not fired2["n"]:
                    fired2["n"] = 1
                    os.kill(os.getpid(), signal.SIGTERM); sm_.terminate(); sm_.wait()
                return orig2(j, st)
            rm.status = status2
            rm.be.sleep = lambda s: time.sleep(min(s, 0.05))
            rc = rm.loop()
            assert rc == 4 and not os.path.exists(os.path.join(rm.cdir, "CAMPAIGN_STOPPED")), rc
            rm2 = Runner("c1", Rm, MockBackend(Rm)); rm2.boot = "n-boot"; rm2.state = synthetic_state()
            assert rm2.mace_status({"work_id": wid, "xkind": "host"}, "ok") == "pending"
            att = read_json(rm2.attempts_path(wid))
            assert att[-1]["cause"] == "node-loss", att
            out.append("MACE: rc 4, no STOP; next boot: interrupted (node-loss)")
        finally:
            r3_restore(old)
        return "; ".join(out)
    case("(z7) SIGTERM inside statuses (round-3 missed item)", c_sigterm_async)

    def c_k3_race():
        """Round-3 R3C-1 (N-F22): at 48 ranks relaxation 9 never starts before K3: a section 11 check ends the tick, K3
        is applied in the next, and only then may Ca D(136) start (K3 pass) or be not_run_gate (fail_replan)."""
        out = []
        for dec in ("fail_replan", "pass"):
            sysd, Rm, rn = r3_c2("k3r_" + dec, {"gates": {"K3": {"K3": dec}}}, a2_layout="48")
            rn.state.update({"K2": "pass", "step0": {"attempts": 1, "outcome": "pass"}})
            r3_markers(rn, ("gate:step0@1", "gate:K2", "gate:step0@4", "gate:projection@after4"))
            for lab in C2_ORDER[:7]:
                r3_done(rn, lab)
            last = C2_ORDER[7]
            ff = os.path.join(rn.L.a2_dir(rn.c, last), f"{last}.final.extxyz"); write_text("synthetic\n", ff)
            put_rec(rn, last, status="complete", end_rule={"outcome": "accepted_converged"}, n_config=41, k0_seen=True,
                    final_geometry={"file": os.path.basename(ff), "k": 40, "sha256": sha256_file(ff)})

            def run46(action, jf, log):
                c46.dump_public({"validity": {"valid": True, "failed": []}}, read_json(jf)["out"]); return 0
            rn.be.run46 = run46
            rn.a2v_files = lambda j: {"final": os.path.join(rn.L.a2_dir(rn.c, j["label"]), j["label"] + ".final.extxyz"),
                                      "parent_final": "x" if j.get("parent") else None}
            ev = []

            def a2_launch(j, r, ranks, lay, rn=rn, ev=ev):
                ev.append((j["label"], rn.state.get("K3")))
                r["parts"] = [{"n": 1, "started": utc()}]; write_json(r, rn.a2_path(j["label"]))
            rn.a2_launch = a2_launch
            for _ in range(5):
                rn.schedule(rn.statuses())
                if ev:
                    break
            if dec == "fail_replan":
                assert not ev, ev
                stx = [read_json(rn.a2_path(x))["status"] for x in C2_ORDER[8:]]
                assert stx == ["not_run_gate", "not_run_gate"], stx
            else:
                assert ev == [(C2_ORDER[8], "pass")], ev
            out.append(f"K3 {dec}: " + (f"launched with K3 {ev[0][1]}" if ev else "relaxations 9-10 not_run_gate, none launched"))
        return "; ".join(out)
    case("(z8) K3 before relaxation 9 at 48 ranks (round-3 R3C-1)", c_k3_race)

    def c_oom_tree():
        """Round-3 R3-8 (N-F23): with two copies, an OOM kill of copy A's rank is A's interruption only; copy B's
        unexplained end in the same boot STOPs, with or without a recorded tree of its own."""
        sysd, Rm, rn = r3_c2("oomtree", {}, a2_layout="2x32")
        t0 = time.time() - 600
        A, B = "s2r_m30_VB136", "s2r_m30_hostB136"
        r3_part(rn, A, q47.synthetic_pw_output(n_config=3, end="killed", ranks=32, label=f"{A}.p1"), pid=4000, rc=137,
                t0=t0, pids={4000, 4242, 4243})
        r3_part(rn, B, q47.synthetic_pw_output(n_config=3, end="killed", ranks=32, label=f"{B}.p1"), pid=5000, rc=1,
                t0=t0, pids={5000, 5555})
        append_jsonl(os.path.join(sysd, "mock", "oom_events.jsonl"), {"boot": "m-boot", "t": t0 + 60, "task": "pw.x",
                                                                      "pid": 4242})
        J = lambda x: rn.G["jobs_by_id"]["a2:" + x]                          # noqa: E731
        assert rn.a2_status(J(A)) == "pending" and read_json(rn.a2_path(A))["interruptions"][-1]["cause"] == "oom"
        msgs = []
        for with_tree in (True, False):
            if not with_tree:
                f = rn.part_files(rn.L.a2_dir(rn.c, B), B, 1)["launch"]
                Lb = read_json(f); Lb.pop("pids"); write_json(Lb, f)
            try:
                rn.a2_status(J(B)); raise AssertionError("copy B was rerun on copy A's OOM kill")
            except Stop as e:
                assert "without an OOM kill" in str(e), e
                msgs.append("tree" if with_tree else "no tree")
        rn.be.proc_tree = lambda pid: {int(pid): "bash", int(pid) + 1: "pw.x"}
        rn.be.descendants = lambda pid: {int(pid), int(pid) + 1}          # the same tree for the round-3 code
        lab = C2_ORDER[2]
        r3_part(rn, lab, "", pid=6000, t0=time.time())
        rn.a2_record_pids(lab, read_json(rn.a2_path(lab)))
        assert read_json(rn.part_files(rn.L.a2_dir(rn.c, lab), lab, 1)["launch"])["pids"] == [6000, 6001]
        return f"OOM of A's rank 4242: A rerun ('oom'); B STOPs ({', '.join(msgs)}); a running part's tree recorded"
    case("(z9) OOM evidence by the part's process tree (round-3 R3-8)", c_oom_tree)

    def c_cap_persist():
        """Round-3 R3C-7 (I-D9): after the first refusal no pw.x or MACE job of the campaign starts, also after a
        relaunch (HARD_CAP.json read back), although the plan's per-job test alone would allow a 2-min MACE job."""
        sysd, Rm = mini("cappers")
        rn = Runner("c1", Rm, MockBackend(Rm)); rn.boot = "m-boot"; rn.state = synthetic_state()
        os.makedirs(rn.cdir, exist_ok=True)
        rn.h_spent = lambda: 519.8
        e_mace = g49.expected_hours("mace", [])
        assert rn.cap_ok({"id": "sp:x"}, "sp", factor=2.0) is False
        assert rn.cap_ok({"id": "mace:y"}, "mace") is False and g49.job_start_allowed(519.8, e_mace)
        rn2 = Runner("c1", Rm, MockBackend(Rm)); rn2.boot = "m-boot"; rn2.state = synthetic_state()
        rn2.h_spent = lambda: 519.8
        rn2.load_cap()
        assert rn2.capped and rn2.capped["job"] == "sp:x" and rn2.cap_ok({"id": "mace:y"}, "mace") is False
        return (f"519.8 h: single point refused; a {e_mace * 60:.1f}-min MACE job refused as well (I-D9), and again "
                f"after a relaunch (HARD_CAP.json read back)")
    case("(z10) hard-cap refusal persists across a relaunch (round-3 R3C-7, I-D9)", c_cap_persist)

    def c_preconditions():
        """Round-3 R3C-10 / R3-C1-4: the campaign preconditions against the plan's stop rules (section 8 Sr gate N;
        section 11 step-0, K2, K3; section 16 cut 8); C3 needs the C1 n rule; the production list needs n."""
        sysd, Rm = mini("precond")
        write_json({"mapping": {"affine_slope_1": True, "nstep_first": 201}}, os.path.join(Node(Rm).c("c1"), "smoke.json"))

        def pre(c, **over):
            rn = Runner(c, Rm, MockBackend(Rm)); rn.boot = "m-boot"; rn.state = synthetic_state(**over)
            try:
                return rn.preconditions()
            except Stop as e:
                return f"STOP: {e}"
        rows = [("c2", dict(campaigns={"c1": "done"}), None),
                ("c2", dict(campaigns={"c1": "done"}, gateN={"Sr": False}, sr_stop=True), "refused"),
                ("c3", dict(campaigns={"c1": "done", "c2": "not_run"}, gateN={"Sr": False}, sr_stop=True), "refused"),
                ("c3", dict(campaigns={"c1": "done", "c2": "done"}, K2="fail"), None),
                ("c3", dict(campaigns={"c1": "done", "c2": "done"}, step0={"outcome": "fail_final"}), None),
                ("c3", dict(campaigns={"c1": "done", "c2": "done"}, K3="a1_only"), None),
                ("c3", dict(campaigns={"c1": "done", "c2": "done"}, K3="fail_replan"), "refused"),
                ("c4", dict(campaigns={"c3": "done"}, K3="a1_only"), "refused"),
                ("c4", dict(campaigns={"c3": "done"}, K2="fail"), "refused"),
                ("c4", dict(campaigns={"c3": "done"}, cuts=[{"cut": 8, "at": "after4", "P_before_h": 600,
                                                             "P_after_h": 500}]), "refused"),
                ("c4", dict(campaigns={"c3": "done"}), None)]
        got = pre("c3", campaigns={"c1": "done", "c2": "done"})
        assert str(got).startswith("STOP") and "gate:nrule" in got, got              # no n-rule marker yet
        put_nrule(Rm)
        assert str(pre("c3", campaigns={"c1": "done", "c2": "done"}, n=None)).startswith("STOP")
        for c, over, want in rows:
            got = pre(c, **over)
            ok = (got is None) if want is None else (got is not None and not str(got).startswith("STOP"))
            assert ok, (c, over, got)
        try:
            production_hosts(synthetic_state(n=None)); raise AssertionError("production list without n")
        except S2Error:
            pass
        assert len(production_hosts(synthetic_state(n=10))) == 10
        return (f"{len(rows)} precondition rows as the plan; C3 without the gate:nrule marker or without n STOPs; the "
                f"production list needs n (8 or 10)")
    case("(z11) campaign preconditions and the n rule (round-3 R3C-10, R3-C1-4)", c_preconditions)

    def c_misc_r3():
        """Round-3 R3-7 (the dead A1-start status removed) and R3-C1-9 (N-F25: s2_relaunch.sh removes a KEEP_ALIVE
        older than this boot when it refuses, and keeps one written in this boot)."""
        tok = "skipped_a1" + "_invalid"
        assert tok not in open(__file__).read() and tok not in open(os.path.join(HERE, "49_s2_gates.py")).read()
        out = []
        for age, kept in ((-3600, False), (+30, True)):
            sysd, Rm = mini(f"ka{'new' if kept else 'old'}")
            cdx = os.path.join(Rm, "work", "s2", "c2"); os.makedirs(cdx, exist_ok=True)
            write_text("stopped for the test\n", os.path.join(cdx, "CAMPAIGN_STOPPED"))
            ka_ = os.path.join(Rm, "KEEP_ALIVE"); write_text("S2 c2\n", ka_)
            bt_ = time.time() - 600
            os.utime(ka_, (bt_ + age, bt_ + age))
            rr, so = r3_relaunch(sysd, Rm, btime=bt_)
            assert rr == 1 and os.path.exists(ka_) == kept, (age, rr, so, os.path.exists(ka_))
            out.append("kept" if kept else "removed")
        return f"no '{tok[:10]}...' status left in scripts/49 and 50; refusing relaunch: an old KEEP_ALIVE {out[0]}, a new one {out[1]}"
    case("(z12) dead status removed; stale KEEP_ALIVE at a refused relaunch (round-3 R3-7, R3-C1-9)", c_misc_r3)

    # ---------------------------------------------------------------- round-4 cases (2026-11-04, after e257cdf)
    class _Fake:
        """A child-process stand-in: alive until ended (poll None), its pid a number nothing uses."""
        def __init__(self, pid=2 ** 22 + 101, alive=True):
            self.pid, self.rc = pid, (None if alive else 0)

        def poll(self):
            return self.rc

    def c_spot_heartbeat():
        """Round-4 R4-C1-1 and R4-C1-2 (N-F18): (a) the committed poller_main and spot_check on a fake clock with the
        real limits (120 s, 300 s, polls every 5 s): an outage that starts 55 s after the old 60-s heartbeat write and
        lasts 250 s gives no STOP; one of 305 s STOPs, with a stated age within one poll of the true time since the
        last good poll; (b) an ended poller with a 310-s old heartbeat is restarted with its own first-poll grace: no
        STOP with a healthy endpoint, nothing scheduled before its first good poll, a STOP 120 s (here 1 s) after the
        restart with an unreachable one, and no restart once a shutdown began; (c) round-5 R5-1: after one good poll of
        the first poller, restarted pollers that never answer keep the first restart's start and STOP spot_first_s
        after it, nothing run before; (d) round-6 R6-C1-2: pollers that each answer once and end STOP at the third
        renewal of the grace, nothing run."""
        import urllib.error, urllib.request
        g = globals()
        real = g["time"]

        class _End(BaseException):
            pass

        T0 = 1.8e9
        sysd, Rm = mini("spothb", boot="hb-boot")

        def run(t_out, outage):
            d = os.path.join(sysd, "spot", f"{t_out:.0f}_{outage}"); os.makedirs(d, exist_ok=True)
            rn = Runner("c1", Rm, MockBackend(Rm)); rn.boot = "hb-boot"; rn.node.spot = d; rn.poller_t0 = T0
            clk, ev = {"now": T0}, {"stop": None, "last_good": None}

            class FT:
                def __getattr__(self, k):
                    return getattr(real, k)

                def time(self):
                    return clk["now"]

                def sleep(self, dt):
                    clk["now"] += dt
                    if ev["stop"] is None and clk["now"] > t_out:
                        try:
                            rn.spot_check()
                        except Stop as e:
                            ev["stop"] = (clk["now"] - ev["last_good"], int(re.search(r"was (\d+) s ago", str(e)).group(1)))
                    if clk["now"] > t_out + outage + 120:
                        raise _End()

            class Op:
                def open(self, url, timeout=3):
                    if t_out <= clk["now"] < t_out + outage:
                        raise urllib.error.HTTPError(url, 503, "x", {}, None)
                    ev["last_good"] = clk["now"]
                    raise urllib.error.HTTPError(url, 404, "x", {}, None)
            ob = urllib.request.build_opener
            g["time"] = FT(); urllib.request.build_opener = lambda *a, **k: Op()
            try:
                poller_main("http://x/termination-time", d, "hb-boot", os.getppid(), SPOT_POLL_S)
            except _End:
                pass
            finally:
                g["time"] = real; urllib.request.build_opener = ob
            return ev["stop"]
        short = run(T0 + 175, 250)                    # 55 s after the old code's heartbeat write at T0 + 120
        assert short is None, f"a 250-s outage STOPped: {short}"
        long_ = run(T0 + 175, 305)
        assert long_ is not None and abs(long_[1] - long_[0]) <= SPOT_POLL_S, long_
        # (b) the poller restart
        old = r3_signals()
        try:
            sp = _Spot()
            out = []
            for tag, url in (("ok", f"http://localhost:{sp.port}/latest/meta-data/instance/spot/termination-time"),
                             ("down", "http://localhost:9/latest/meta-data/instance/spot/termination-time")):
                write_text(url + "\n", os.path.join(Rm, "setup", "s2_spot_url"))
                rn = Runner("c1", Rm, MockBackend(Rm)); rn.boot = "hb-boot"; os.makedirs(rn.cdir, exist_ok=True)
                rn.be.spot_first_s = 1.0 if tag == "down" else 120.0
                rn.poller_t0 = time.time() - 400
                write_text(f"{time.time() - 310:.0f} x ok=1 err=0\n", os.path.join(rn.node.spot, "heartbeat.hb-boot"))
                rn.poller = _Fake(alive=False)
                rn.housekeeping()                                            # no STOP (was: 'the last good poll ... 310 s')
                assert rn.poller.poll() is None and rn.poller_t0 > time.time() - 5, "the poller was not restarted"
                if tag == "ok":
                    wait_for(lambda: rn.spot_check() is True, 20, "the restarted poller's first good poll")
                    out.append("healthy endpoint: no STOP, the new poller's first good poll accepted")
                else:
                    launched = []
                    rn.launch_pw = lambda j: launched.append(j)
                    rn.G = {"phases": ["smoke"], "jobs_by_id": {}}
                    rn.schedule({})
                    assert rn.spot_check() is False and not launched
                    time.sleep(1.2)
                    try:
                        rn.housekeeping(); raise AssertionError("no STOP after the restart's grace")
                    except Stop as e:
                        assert "within 1 s of the poller's start" in str(e), e
                    out.append("unreachable endpoint: nothing scheduled, STOP after the grace from the restart")
                rn.poller.terminate(); rn.poller.wait(10)
            # (c) round-5 R5-1: after one good poll every restarted poller ends at once (its interpreter /usr/bin/false);
            # the first restart comes once the last good poll is 1.8 s old (a heartbeat within 1 s of a poller's start
            # counts as its own): the grace is not renewed at each restart, a STOP spot_first_s after it, nothing run
            write_text(f"http://localhost:{sp.port}/latest/meta-data/instance/spot/termination-time\n",
                       os.path.join(Rm, "setup", "s2_spot_url"))
            rn = Runner("c1", Rm, MockBackend(Rm)); rn.boot = "hb-boot"; os.makedirs(rn.cdir, exist_ok=True)
            rn.be.spot_first_s, rn.be.spot_stale_s = 1.0, 2.0
            rn.start_poller()
            wait_for(lambda: rn.spot_check() is True, 20, "the poller's first good poll")
            rn.poller.terminate(); rn.poller.wait(10); rn.be.python = "/usr/bin/false"; time.sleep(1.8)
            ran, stop, t1 = [], None, time.time()
            rn.run_check = lambda j: ran.append(j["id"])
            rn.G = {"phases": ["check"], "jobs_by_id": {"j": {"id": "j", "kind": "check", "what": "zz", "deps": [],
                                                              "phase": "check"}}}
            while time.time() - t1 < 6.0:
                try:
                    rn.housekeeping(); rn.schedule({"j": "pending"})
                except Stop as e:
                    stop = (time.time() - t1, str(e)); break
                time.sleep(rn.be.tick)
            assert stop and "within 1 s of the poller's start" in stop[1] and stop[0] < 2.5 and not ran, (stop, ran)
            out.append(f"after one good poll, restarts that never answer: STOP after {stop[0]:.1f} s, nothing run")
            # (d) round-6 R6-C1-2: every poller answers once and ends (a stand-in whose one good poll, 0.1 s after its
            # start, is seen as it ends), real limits (120 s, 300 s): the third renewal is a STOP, nothing run
            rn = Runner("c1", Rm, MockBackend(Rm)); rn.boot = "hb-boot"; os.makedirs(rn.cdir, exist_ok=True)

            class _Once(_Fake):
                def poll(self):
                    write_text(f"{rn.poller_t0 + 0.1:.3f} x ok=1 err=0\n", os.path.join(rn.node.spot, "heartbeat.hb-boot"))
                    return 0
            rn.start_poller = lambda: (setattr(rn, "poller_t0", rn.poller_t0 or time.time()), setattr(rn, "poller", _Once()))
            rn.start_poller()
            ran, stop, t1 = [], None, time.time()
            rn.run_check = lambda j: ran.append(j["id"])
            rn.G = {"phases": ["check"], "jobs_by_id": {"j": {"id": "j", "kind": "check", "what": "zz", "deps": [],
                                                              "phase": "check"}}}
            while time.time() - t1 < 8.0:
                time.sleep(1.5)
                try:
                    rn.housekeeping(); rn.schedule({"j": "pending"})
                except Stop as e:
                    stop = (time.time() - t1, str(e)); break
            assert stop and "keeps ending after a good poll" in stop[1] and not ran, (stop, ran)
            out.append(f"pollers answering once and ending: STOP at the third renewal ({stop[0]:.1f} s), nothing run")
            rn = Runner("c1", Rm, MockBackend(Rm)); rn.boot = "hb-boot"; rn.poller_t0 = time.time()
            rn.poller = _Fake(alive=False); rn.shutdown = True
            rn.housekeeping()
            assert isinstance(rn.poller, _Fake), "a poller restarted during a shutdown"
        finally:
            r3_restore(old)
        return (f"fake clock: a 250-s outage 55 s after the old heartbeat write gives no STOP; 305 s STOPs, stated age "
                f"{long_[1]} s vs {long_[0]:.0f} s since the last good poll; " + "; ".join(out) + "; no restart in a shutdown")
    case("(z13) spot heartbeat at every good poll; poller restart grace (round-4 R4-C1-1, R4-C1-2; round-5 R5-1; "
         "round-6 R6-C1-2)", c_spot_heartbeat)

    def c_notice_in_pass():
        """Round-4 missed item (N-11): a spot notice written while one schedule() pass runs a synchronous scripts/46 job
        holds the MACE launch later in the same pass (the real C1 graph; the g46 job and the launch are stand-ins)."""
        sysd, Rm = mini("noticepass", boot="np-boot")
        rn = Runner("c1", Rm, MockBackend(Rm)); rn.boot = "np-boot"; rn.state = synthetic_state()
        rn.be.graph = lambda c, s: graph("c1", s, sites=lambda m: S2[m])
        rn.graph_now(); os.makedirs(rn.cdir, exist_ok=True)
        ph = [j for j in rn.G["jobs_by_id"].values() if j["phase"] == "mace"]
        ig = next(i for i, j in enumerate(ph) if j["kind"] == "g46")
        jg = ph[ig]
        jm = next(j for j in ph[ig + 1:] if j["kind"] == "mace" and jg["id"] not in j["deps"]
                  and not any(d.startswith("k0:") for d in j["deps"]))
        st = {jid: "done" for jid in rn.G["jobs_by_id"]}
        st[jg["id"]] = st[jm["id"]] = "pending"
        nf = os.path.join(rn.node.spot, f"notice.{rn.boot}")
        seen = []

        def g46(j):
            t = time.time(); write_text(f"{utc(t)} {t:.0f} 2026-11-04T12:00:00Z\n", nf)   # the poller, meanwhile
        rn.run_g46 = g46
        rn.launch_mace = lambda j: seen.append(rn.held())
        rn.schedule(st)
        assert seen == [True], seen
        return f"notice written during {jg['id']}: held() true at the launch of {jm['id']} in the same pass"
    case("(z14) a spot notice inside one schedule pass holds its later launches (round-4 missed item)", c_notice_in_pass)

    def c_resolve_live():
        """Round-4 R4-C1-4: a RESOLVE written into a live throughput run is not read: 'running', no file moved, RESOLVE
        kept; once the run has ended the next status consumes it ('pending', parts in discarded/resolved_<t>)."""
        sysd, Rm = mini("reslive", boot="rl-boot")
        rn = Runner("c1", Rm, MockBackend(Rm)); rn.boot = "rl-boot"; rn.state = synthetic_state()
        rn.be.graph = lambda c, s: graph("c1", s, sites=lambda m: S2[m]); rn.graph_now()
        j = rn.G["jobs_by_id"]["pw:s2tp_ref232_np48"]
        d = rn.pw_dir(j); os.makedirs(d, exist_ok=True)
        f = rn.part_files(d, j["label"], 1)
        sl = subprocess.Popen(["sleep", "60"])
        write_text("&CONTROL\n/\n", f["in"]); write_text("partial\n", f["out"])
        write_json({"boot": "rl-boot", "started_epoch": time.time() - 30, "ranks": 48, "pid": sl.pid}, f["launch"])
        write_text("rerun 2026-11-04 self-test\n", os.path.join(d, "RESOLVE"))
        s1 = rn.pw_status(j, "ok")
        kept = all(os.path.exists(f[k]) for k in ("in", "out", "launch")) and os.path.exists(os.path.join(d, "RESOLVE"))
        sl.terminate(); sl.wait(); write_text(f"143 {utc()}\n", f["rc"])
        s2 = rn.pw_status(j, "ok")
        assert s1 == "running" and kept, (s1, kept)
        assert s2 == "pending" and glob.glob(os.path.join(d, "discarded", "resolved_*")) and not os.path.exists(f["out"]), s2
        return "live run: 'running', files and RESOLVE kept; ended: RESOLVE consumed, 'pending'"
    case("(z15) RESOLVE waits for a live pw.x reference run (round-4 R4-C1-4)", c_resolve_live)

    def c_smoke_slope():
        """Round-4 R4-C1-5 (X-3, D-S0-6, D-S0-8): n1 and n3 both end with JOB DONE but n3 - n1 is 1 configuration (n3
        converges at k = 1): a STOP naming the smoke tests before the exit/restart test and any throughput run, C1 not
        done; RESOLVE 'rerun' of n3 (scenario removed) and a relaunch give an affine mapping of slope 1, nstep_first
        201 - c0, and the throughput row."""
        sysd = os.path.join(base, "slope"); Rx = os.path.join(sysd, "data")
        for dd in ("data/work/s2", "data/jobs", "data/setup", "data/pseudo", "mock", "bin"):
            os.makedirs(os.path.join(sysd, dd), exist_ok=True)
        _node_scripts(sysd)
        sp3 = _Spot()
        write_text(f"http://localhost:{sp3.port}/latest/meta-data/instance/spot/termination-time\n",
                   os.path.join(Rx, "setup", "s2_spot_url"))
        bt = "p" * 8 + "-boot-p"
        write_text(bt, os.path.join(sysd, "mock", "boot_id"))
        write_text(f"{time.time() - 60:.0f}", os.path.join(sysd, "mock", f"btime.{bt}"))
        write_json({"gates": {"throughput": {"a2_layout": "48"}, "N": {"n": 8, "gateN": {t: True for t in c46.TOKENS}}}},
                   os.path.join(sysd, "mock", "config.json"))
        write_json({"s2smoke_ref232_n3": {"converge_at": 1}}, os.path.join(sysd, "mock", "pw_scenarios.json"))
        write_json(synthetic_state(a2_layout=None, commit=None), os.path.join(Rx, "work", "s2", "state.json"))
        envx = dict(os.environ, PATH=os.path.join(sysd, "bin") + os.pathsep + os.environ.get("PATH", ""))
        envx.pop("S2_LOCK_FD", None)
        cd = c46.Layout(kind="node", root=Rx).campaign_dir("c1")

        def go(tag, until=None):
            lf = open(os.path.join(base, f"runner_slope_{tag}.log"), "w")
            p = subprocess.Popen([sys.executable, me, "run", "--campaign", "c1", "--root", Rx, "--mock"], env=envx,
                                 stdout=lf, stderr=subprocess.STDOUT, start_new_session=True)
            procs[f"slope_{tag}"] = p
            t = time.time()
            while p.poll() is None and time.time() - t < 150:
                if until is not None and until():
                    os.killpg(p.pid, signal.SIGKILL); p.wait(); return None
                time.sleep(0.1)
            assert p.poll() is not None, f"run {tag} did not end"
            return p.returncode
        rc1 = go("1")
        cj = read_json(os.path.join(cd, "campaign.json")) or {}
        assert rc1 == 3 and "not affine with slope 1" in (cj.get("stop_reason") or ""), (rc1, cj.get("stop_reason"))
        assert not glob.glob(os.path.join(cd, "tp", "*", "*.launch.json")), "a throughput run started"
        assert not glob.glob(os.path.join(cd, "smoke", "s2smoke_ref232_rst", "*.launch.json")), "the restart test started"
        assert not os.path.exists(os.path.join(cd, "CAMPAIGN_DONE"))
        write_json({}, os.path.join(sysd, "mock", "pw_scenarios.json"))
        write_text("rerun 2026-11-04 n3 repeated (self-test)\n", os.path.join(cd, "smoke", "s2smoke_ref232_n3", "RESOLVE"))
        reached = lambda: os.path.exists(os.path.join(cd, "throughput.json"))   # noqa: E731
        rc2 = go("2", until=reached)
        sm = (read_json(os.path.join(cd, "smoke.json")) or {}).get("mapping") or {}
        assert rc2 is None and reached(), (rc2, open(os.path.join(base, "runner_slope_2.log")).read()[-800:])
        assert sm.get("affine_slope_1") and sm.get("nstep_first") == K_TOTAL - sm["c0"], sm
        return (f"n1 1 and n3 2 configurations: STOP before the restart test and the throughput row ('not affine with "
                f"slope 1'); RESOLVE rerun of n3: c0 {sm['c0']}, nstep_first {sm['nstep_first']}, throughput row run")
    case("(z16) smoke tests not affine with slope 1: STOP inside C1 (round-4 R4-C1-5)", c_smoke_slope)

    def c_core_sets():
        """Round-4 R4-C1-1 (error) and the missed items of the node lens (N-F30): (a) in the simulated campaign every
        pw.x outside the queue ran through the committed s2_run_qe.sh: np32a and np32b on the two halves of the cores
        ('taskset -c 0-31' / '32-63', --bind-to none), every other run (smoke tests, 48 and 64 ranks, A2 at 48) bound as
        run_qe.sh binds, and the 2x32 rate computed for the pair; (b) a copy rerun alone after the other completed: the
        completed one is moved aside unread and both start together on disjoint cores; a copy whose partner runs waits;
        a partner missing: skipped; (c) tp_record gives no 2x32 rate for a solo rerun, a missing or shared core set or
        shared CPUs; (d) at 2x32 a new part takes the half no running copy uses."""
        calls = [x for x in open(os.path.join(sysroot, "mock", "mpirun_calls.log")).read().splitlines() if x.strip()]
        np32 = [x for x in calls if "-np 32 " in x]
        others = [x for x in calls if "-np 32 " not in x]
        assert sorted(x.split()[1] for x in np32) == ["cpuset=0-31", "cpuset=32-63"] and \
            all("--bind-to none" in x for x in np32), np32
        assert others and all("cpuset=none" in x and "--bind-to core" in x for x in others), others[:3]
        tp = read_json(os.path.join(cdir, "throughput.json"))
        assert tp["pair"]["valid"] and tp["rate_config_per_node_h"]["2x32"], tp.get("pair")
        # (b) the pair rule
        sysd, Rm = mini("pair", boot="pr-boot")
        os.makedirs(os.path.join(sysd, "tmp"), exist_ok=True)
        rn = Runner("c1", Rm, MockBackend(Rm)); rn.boot = "pr-boot"; rn.state = synthetic_state()
        rn.be.graph = lambda c, s: graph("c1", s, sites=lambda m: S2[m]); rn.graph_now()
        os.makedirs(rn.cdir, exist_ok=True)
        write_json({"mapping": {"c0": 0, "affine_slope_1": True, "nstep_first": 201}}, os.path.join(rn.cdir, "smoke.json"))
        rn.h_spent = lambda: 10.0
        spawned = []

        def spawn(cmd, *, cwd, log, rc, env=None, pass_fds=()):
            spawned.append((os.path.basename(cwd), (env or {}).get("CPUSET"), os.path.basename(cmd[0])))
            return _Fake(pid=2 ** 22 + 200 + len(spawned))
        rn.be.spawn = spawn
        J = lambda x: rn.G["jobs_by_id"]["pw:" + x]                          # noqa: E731
        A, B = TP_PAIR
        dA = rn.pw_dir(J(A)); os.makedirs(dA, exist_ok=True)
        fA = rn.part_files(dA, A, 1)
        write_text("&CONTROL\n/\n", fA["in"]); write_text("x\n", fA["out"])
        write_json({"label": A, "part": 1, "ok": True, "counts": {"n_config": 5, "job_done": True}, "wall_s": 3000.0,
                    "cpuset": "0-31", "interval": [100.0, 3100.0]}, fA["done"])
        os.makedirs(os.path.join(rn.pw_dir(J(B)), "discarded", "p1_1"), exist_ok=True)   # B's first attempt was cut
        rn.launch_pw(J(B))
        assert sorted((x[0], x[1]) for x in spawned) == [(A, "32-63"), (B, "0-31")] and \
            all(x[2] == "s2_run_qe.sh" for x in spawned), spawned
        assert not os.path.exists(fA["done"]) and glob.glob(os.path.join(dA, "discarded", "paired_*", f"{A}.p1.done.json"))
        LA = read_json(rn.part_files(dA, A, 1)["launch"])
        assert LA["cpuset"] == "32-63" and LA["slot"] == 1, LA
        rn.launch_pw(J(A))                                                   # started with its pair: nothing more
        assert len(spawned) == 2, spawned
        rn.procs = {"pw:" + B: {"p": _Fake(), "kind": "pw", "dir": rn.pw_dir(J(B)), "slot": 0}}
        os.remove(rn.part_files(dA, A, 1)["launch"])
        rn.launch_pw(J(A))
        assert len(spawned) == 2, "a copy started while the other ran alone"
        rn.procs = {}
        fB = rn.part_files(rn.pw_dir(J(B)), B, 1)
        write_json({"label": B, "part": 1, "ok": False, "status": "missing"}, fB["done"])
        rn.launch_pw(J(A))
        assert (read_json(fA["done"]) or {}).get("status") == "skipped" and len(spawned) == 2
        # (c) the 2x32 rate needs a concurrent pair on disjoint cores
        T0 = 1.8e9
        base_runs = {"np48": (None, T0, T0 + 4.0 * 3600), "np64": (None, T0 + 4.1 * 3600, T0 + 7.1 * 3600),
                     "np32a": ("0-31", T0 + 7.2 * 3600, T0 + 12.2 * 3600), "np32b": ("32-63", T0 + 7.2 * 3600 + 5, T0 + 11.8 * 3600)}
        rows = {"concurrent": {}, "solo rerun": {"np32b": ("32-63", T0 + 12.3 * 3600, T0 + 16.9 * 3600)},
                "no core set": {"np32b": (None, T0 + 7.2 * 3600 + 5, T0 + 11.8 * 3600)},
                "shared core set": {"np32b": ("0-31", T0 + 7.2 * 3600 + 5, T0 + 11.8 * 3600)},
                "shared CPUs": {"np32b": ("32-63", T0 + 7.2 * 3600 + 5, T0 + 11.8 * 3600, "0-31")}}
        got = {}
        for name, over in rows.items():
            sysd, Rt = mini("tprate_" + name.replace(" ", "_"))
            rt = Runner("c1", Rt, MockBackend(Rt)); rt.boot = "m-boot"
            for k, v in {**base_runs, **over}.items():
                lab = f"s2tp_ref232_{k}"; d = os.path.join(rt.cdir, "tp", lab); os.makedirs(d, exist_ok=True)
                write_json({"label": lab, "part": 1, "ok": True, "counts": {"n_config": 5, "job_done": True},
                            "wall_s": v[2] - v[1], "cpuset": v[0], "interval": [v[1], v[2]],
                            "affinity": v[3] if len(v) > 3 else None}, rt.part_files(d, lab, 1)["done"])
            got[name] = rt.tp_record()["rate_config_per_node_h"]["2x32"]
        assert got["concurrent"] and all(got[k] is None for k in rows if k != "concurrent"), got
        # (d) slots at 2x32
        rn.procs = {"a2:x": {"p": _Fake(), "kind": "a2", "dir": "", "slot": 0}}
        assert rn.free_core_set() == (1, "32-63")
        rn.procs["a2:y"] = {"p": _Fake(), "kind": "a2", "dir": "", "slot": 1}
        try:
            rn.free_core_set(); raise AssertionError("a third copy got a core set")
        except Stop:
            pass
        rn.procs = {"a2:y": {"p": _Fake(), "kind": "a2", "dir": "", "slot": 1}}
        assert rn.free_core_set() == (0, "0-31")
        # A2 at 2x32 through a2_launch: the third relaxation takes the half the ended second copy used
        sysd, Ra = mini("a2slots", boot="as-boot")
        os.makedirs(os.path.join(sysd, "tmp"), exist_ok=True)
        ra = Runner("c1", Ra, MockBackend(Ra)); ra.boot = "as-boot"; ra.state = synthetic_state(a2_layout="2x32")
        ra.graph_now(); os.makedirs(ra.cdir, exist_ok=True)
        write_json({"mapping": {"c0": 0, "affine_slope_1": True, "nstep_first": 201}}, os.path.join(ra.cdir, "smoke.json"))
        got, fakes = [], {}

        def spawn2(cmd, *, cwd, log, rc, env=None, pass_fds=()):
            got.append((os.path.basename(cwd), (env or {}).get("CPUSET")))
            fakes[os.path.basename(cwd)] = _Fake(pid=2 ** 22 + 300 + len(got))
            return fakes[os.path.basename(cwd)]
        ra.be.spawn = spawn2
        assert ra.chain_lock_ok()
        a2rows = [ra.G["jobs_by_id"]["a2:" + x] for x in ("s2r_m30_VB136", "s2r_m30_VB76", "s2r_m30_VX138")]
        ra.a2_launch(a2rows[0], ra.a2_rec(a2rows[0]), 32, "2x32")
        ra.a2_launch(a2rows[1], ra.a2_rec(a2rows[1]), 32, "2x32")
        fakes["s2r_m30_VB76"].rc = 0                                       # the copy on 32-63 ends
        ra.a2_launch(a2rows[2], ra.a2_rec(a2rows[2]), 32, "2x32")
        assert [x[1] for x in got] == ["0-31", "32-63", "32-63"], got
        return (f"campaign: np32a/np32b on cores 0-31 and 32-63 (--bind-to none), {len(others)} other pw.x runs bound "
                f"as run_qe.sh; 2x32 rate computed; a solo rerun: the completed copy moved aside and both started "
                f"together; partner running: waits; partner missing: skipped; 2x32 rate None for "
                f"{[k for k in rows if k != 'concurrent']}; at 2x32 a new part takes the free half (A2: 0-31, 32-63, "
                f"then 32-63 after the second copy ended)")
    case("(z17) two concurrent copies on disjoint cores, run together (round-4 R4-C1-1 node, missed items)", c_core_sets)

    def c_nodescripts():
        """Round-4 R4-C1-2 (N-F31): the node-only scripts are hashed in C1 and the queue, the chain and the launcher must
        equal the checkout's copies: a queue differing by one byte STOPs C1 in its check phase (nothing else runs);
        equal copies give five hashes; C2 with a changed run_qe.sh STOPs."""
        old = r3_signals()
        try:
            sysd, Rm = mini("nodescr", boot="ns-boot")
            _node_scripts(sysd)
            sp4 = _Spot()
            write_text(f"http://localhost:{sp4.port}/latest/meta-data/instance/spot/termination-time\n",
                       os.path.join(Rm, "setup", "s2_spot_url"))
            write_json(synthetic_state(a2_layout=None, commit=None), os.path.join(Rm, "work", "s2", "state.json"))
            q = os.path.join(Rm, "setup", "qe_queue.sh")
            good = open(q).read()
            write_text(good.replace("retried once", "retried twice", 1), q)
            rn = Runner("c1", Rm, MockBackend(Rm))
            ticks = {"n": 0}

            def sl(s):                                     # the STOP comes in the check phase; never run a campaign here
                ticks["n"] += 1
                if ticks["n"] > 600:
                    raise RuntimeError("no STOP in the check phase")
                time.sleep(min(s, 0.05))
            rn.be.sleep = sl
            rc = rn.run()
            if rn.lockfd is not None:
                os.close(rn.lockfd)
        finally:
            r3_restore(old)
        cj = read_json(os.path.join(rn.cdir, "campaign.json")) or {}
        assert rc == 3 and "qe_queue.sh differs" in (cj.get("stop_reason") or ""), (rc, cj.get("stop_reason"))
        assert not os.path.isdir(os.path.join(rn.cdir, "smoke")), "a pw.x run started"
        write_text(good, q)
        be = MockBackend(Rm)
        rec = be.nodescripts_check("c1", None)
        assert rec["passed"] and len(rec["files"]) == 5 and all(v and v.get("sha256") for v in rec["files"].values()), rec
        rq = os.path.join(sysd, "usr", "local", "bin", "run_qe.sh")
        write_text(open(rq).read() + "# changed\n", rq)
        r2 = be.nodescripts_check("c2", rec)
        assert not r2["passed"] and any("run_qe.sh changed" in x for x in r2["problems"]), r2
        rn2 = Runner("c2", Rm, be); rn2.boot = "ns-boot"; rn2.state = synthetic_state()
        c46.dump_public(rec, os.path.join(rn2.node.c("c1"), "nodescripts_check.json"))
        try:
            rn2.run_check({"what": "nodescripts"}); raise AssertionError("C2 accepted a changed run_qe.sh")
        except Stop as e:
            assert "run_qe.sh changed since the C1 record" in str(e), e
        return ("a one-byte change of qe_queue.sh: STOP in the check phase, no pw.x; equal copies: 5 hashes recorded; C2 "
                "with a changed run_qe.sh: STOP")
    case("(z18) node scripts hashed in C1 and compared (round-4 R4-C1-2)", c_nodescripts)

    def c_git_state():
        """Round-4 R4-C1-3 (N-F32): git failing in the checkout is a STOP, never an empty commit read as clean; a git
        checkout gives a 40-hex HEAD and its cleanliness; s2_campaign.sh refuses a directory where git fails."""
        sysd, Rm = mini("gitst")
        be = NodeBackend(Rm)
        nog = os.path.join(sysd, "notgit"); os.makedirs(nog, exist_ok=True)
        be.node.checkout = nog
        try:
            be.git_state(); raise AssertionError("git_state passed on a directory without .git")
        except Stop as e:
            assert "git failed in the checkout" in str(e), e
        rp = os.path.join(sysd, "repo"); os.makedirs(rp, exist_ok=True)
        ge = dict(os.environ, GIT_AUTHOR_NAME="s2", GIT_AUTHOR_EMAIL="s2-selftest", GIT_COMMITTER_NAME="s2",
                  GIT_COMMITTER_EMAIL="s2-selftest", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
        for cmd in (["init", "-q"], ["add", "-A"], ["commit", "-q", "--allow-empty", "-m", "s2 self-test"]):
            subprocess.run(["git", "-C", rp] + cmd, check=True, env=ge, capture_output=True)
        be.node.checkout = rp
        g1 = be.git_state()
        write_text("x\n", os.path.join(rp, "stray.txt"))
        g2 = be.git_state()
        assert re.fullmatch(r"[0-9a-f]{40}", g1["head"]) and g1["clean"] and not g2["clean"], (g1, g2)
        camp = open(os.path.join(ROOT, "ehpc", "node", "s2_campaign.sh")).read()
        W = os.path.join(Rm, "work", "s2")
        a_ = "R=/data/work/ps_s2; PY=/data/miniforge3/envs/mace/bin/python; W=/data/work/s2"
        assert a_ in camp
        camp = camp.replace(a_, f"R={nog}; PY=/usr/bin/false; W={W}").replace("setsid nohup", "nohup")
        write_text(camp, os.path.join(sysd, "camp.sh"))
        _node_scripts(sysd)
        pr = subprocess.run(["bash", os.path.join(sysd, "camp.sh"), "c1"], capture_output=True, text=True,
                            env=dict(os.environ, PATH=os.path.join(sysd, "bin") + os.pathsep + os.environ.get("PATH", "")))
        assert pr.returncode == 1 and "git failed" in pr.stderr and not os.path.exists(os.path.join(W, "c1", "driver.out")), \
            (pr.returncode, pr.stderr[-300:])
        return "no .git: STOP; a git checkout: 40-hex HEAD, clean, then dirty; s2_campaign.sh in a non-repository: exit 1, nothing started"
    case("(z19) git failures are a STOP (round-4 R4-C1-3 node)", c_git_state)

    def c_resolve_budget():
        """Round-4 R4-C1-4 (N-F33): after RESOLVE 'rerun' a smoke or throughput run has the two reruns of N-D10 again
        (the attempts before go aside with the resolution), and an operator's MACE rerun after an exception does not
        count against the two reruns of section 13."""
        sysd, Rm = mini("resbud", boot="rb-boot")
        rn = Runner("c1", Rm, MockBackend(Rm)); rn.boot = "rb-boot"; rn.state = synthetic_state()
        rn.be.graph = lambda c, s: graph("c1", s, sites=lambda m: S2[m]); rn.graph_now()
        j = rn.G["jobs_by_id"]["pw:s2tp_ref232_np48"]
        d = rn.pw_dir(j); os.makedirs(d, exist_ok=True)
        f = rn.part_files(d, j["label"], 1)

        def cut():                                                         # a launch of an earlier boot, no output
            write_json({"boot": "old-boot", "started_epoch": time.time() - 600, "ranks": 48, "pid": 2 ** 22 + 9}, f["launch"])
            return rn.pw_status(j, "ok")
        s1 = [cut() for _ in range(3)]
        write_text("rerun 2026-11-04 after a fix (self-test)\n", os.path.join(d, "RESOLVE"))
        s2 = rn.pw_status(j, "ok")
        s3 = [cut() for _ in range(3)]
        assert s1 == ["pending", "pending", "missing"] and s2 == "pending" and s3 == ["pending", "pending", "missing"], (s1, s2, s3)
        wid = wid_of("ref233", "host")
        dm = rn.L.cell_dir("c1", wid); os.makedirs(dm, exist_ok=True)
        jm = {"work_id": wid, "xkind": "host"}
        write_json([{"n": 1, "boot": "rb-boot", "started": utc(), "started_epoch": time.time() - 60, "pid": None}],
                   rn.attempts_path(wid))
        write_text(f"1 {utc()}\n", os.path.join(dm, "attempt1.rc"))
        try:
            rn.mace_status(jm, "ok"); raise AssertionError("an exception attempt was not a STOP")
        except Stop:
            pass
        write_text("rerun 2026-11-04 after the committed fix (self-test)\n", os.path.join(dm, "RESOLVE"))
        m = [rn.mace_status(jm, "ok")]
        for n in (2, 3, 4):
            att = read_json(rn.attempts_path(wid))
            att.append({"n": n, "boot": "old-boot", "started": utc(), "started_epoch": time.time() - 60, "pid": None})
            write_json(att, rn.attempts_path(wid))
            m.append(rn.mace_status(jm, "ok"))
        assert m == ["pending", "pending", "pending", "missing"], m
        return f"pw: {s1}, RESOLVE rerun -> {s2}, then {s3}; MACE: exception STOP, RESOLVE rerun, then {m[1:]}"
    case("(z20) RESOLVE 'rerun' gives the reruns back (round-4 R4-C1-4)", c_resolve_budget)

    def c_pw_oom_tree():
        """Round-4 R4-C1-5 and R4-C24-2 (N-F34): a smoke or throughput run records its process tree with its pw.x ranks
        and their CPUs; an OOM kill of one of its pw.x ranks after its start is cause 'oom'; one of a pid in the other
        copy's tree, or one dated before its start, is not ('unknown')."""
        sysd, Rm = mini("pwoom", boot="po-boot")
        rn = Runner("c1", Rm, MockBackend(Rm)); rn.boot = "po-boot"; rn.state = synthetic_state()
        rn.be.graph = lambda c, s: graph("c1", s, sites=lambda m: S2[m]); rn.graph_now()
        J = lambda x: rn.G["jobs_by_id"]["pw:" + x]                          # noqa: E731
        A, B = TP_PAIR
        rn.be.proc_tree = lambda pid: {int(pid): "bash", int(pid) + 1: "mpirun", int(pid) + 7: "pw.x"}
        rn.be.cpus_allowed = lambda pid: set(range(32, 64)) if int(pid) == 31007 else set(range(32))
        rn.a2_note_pids(A, {32000, 32001, 32007})
        causes = []
        for tag, victim, dt in (("own rank", 31007, 20), ("other copy's rank", 32007, 20), ("before its start", 31007, -30)):
            d = rn.pw_dir(J(B)); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
            f = rn.part_files(d, B, 1)
            t0 = time.time() - 300
            write_json({"boot": "po-boot", "started_epoch": t0, "ranks": 32, "pid": 31000, "cpuset": "32-63"}, f["launch"])
            if tag == "own rank":
                rn.record_tree(B, f["launch"])
                L = read_json(f["launch"])
                assert L["pw_pids"] == [31007] and L["affinity"] == "32-63", L
            write_text(f"137 {utc()}\n", f["rc"])
            p = os.path.join(sysd, "mock", "oom_events.jsonl")
            write_text(json.dumps({"boot": "po-boot", "t": t0 + dt, "task": "pw.x", "pid": victim}) + "\n", p)
            assert rn.pw_status(J(B), "ok") == "pending"
            causes.append([json.loads(x) for x in open(os.path.join(rn.cdir, "interruptions.jsonl"))][-1]["cause"])
        assert causes == ["oom", "unknown", "unknown"], causes
        return f"own pw.x rank after the start: {causes[0]}; the other copy's rank: {causes[1]}; before the start: {causes[2]}"
    case("(z21) OOM evidence for smoke and throughput runs by their process tree (round-4 R4-C1-5)", c_pw_oom_tree)

    def c_mace_load():
        """Round-4 R4-C1-6 (N-F35): check:mace loads the model in a child process after the hash check (the runner
        never imports mace): on this laptop with an empty cache the hash check fails before any child runs; a child
        that reports the load gives a passed record with its info; one that raises gives a failed record and a STOP in
        the check phase, before any MACE attempt."""
        sysd, Rm = mini("maceload")
        cache = os.path.join(sysd, "cache"); os.makedirs(cache, exist_ok=True)
        old = os.environ.get("XDG_CACHE_HOME")
        os.environ["XDG_CACHE_HOME"] = cache
        try:
            r0 = NodeBackend(Rm).foundation_check()
        finally:
            if old is None:
                os.environ.pop("XDG_CACHE_HOME", None)
            else:
                os.environ["XDG_CACHE_HOME"] = old
        assert r0["passed"] is False and "load" not in r0, r0
        be = NodeBackend(Rm)
        good = os.path.join(sysd, "py_good"); bad = os.path.join(sysd, "py_bad")
        write_text('#!/bin/bash\necho \'S2-MACE-LOAD {"dtype": "float64", "device": "cpu", "threads": 6, '
                   '"z_required_ok": true, "versions": {"mace": "0.3.16"}}\'\n', good)
        write_text('#!/bin/bash\necho "Traceback (most recent call last):" >&2\necho "c46.S2Error: mace 0.3.17, the '
                   'plan\'s 0.3.16" >&2\nexit 1\n', bad)              # qualified, as the real child prints it (R5 M-1)
        os.chmod(good, 0o755); os.chmod(bad, 0o755)
        be.python = good; r1 = be.mace_load()
        be.python = bad; r2 = be.mace_load()
        assert r1["ok"] and r1["info"]["dtype"] == "float64" and not r2["ok"] and r2["error"] == "S2Error", (r1, r2)
        rn = Runner("c1", Rm, MockBackend(Rm)); rn.boot = "m-boot"; rn.state = synthetic_state()
        os.makedirs(rn.cdir, exist_ok=True)
        rn.be.foundation_check = lambda: {"schema": "s2-mace-1", "passed": False, "load": r2}
        try:
            rn.run_check({"what": "mace"}); raise AssertionError("a failed MACE load passed")
        except Stop as e:
            assert "mace check failed" in str(e), e
        assert not glob.glob(os.path.join(rn.cdir, "cells", "*", "attempts.json"))
        return "empty cache: the hash check fails first (no child); a reported load passes; an S2Error STOPs in the check phase"
    case("(z22) check:mace loads the model before the first MACE job (round-4 R4-C1-6; round-5 M-1)", c_mace_load)

    def c_wrappers_r4():
        """Round-4 R4-C1-8, R4-C1-3 (C1 lens) and R4-C1-9: before the first start s2_status.sh says 'not started' and
        s2_relaunch.sh refuses with 'no S2 work tree'; a relaunch whose s2_campaign.sh refuses (a checkout that is not
        clean) removes a KEEP_ALIVE older than the boot; a ledger entry of the operator without a boot id counts."""
        sysd = os.path.join(base, "wrap4"); Rm = os.path.join(sysd, "data")
        os.makedirs(os.path.join(sysd, "bin"), exist_ok=True); os.makedirs(os.path.join(sysd, "mock"), exist_ok=True)
        _node_scripts(sysd)
        envw = dict(os.environ, PATH=os.path.join(sysd, "bin") + os.pathsep + os.environ.get("PATH", ""))
        stt = open(os.path.join(ROOT, "ehpc", "node", "s2_status.sh")).read()
        stt = stt.replace("cd /data/work/ps_s2", f'cd "{ROOT}"').replace("/data/work/s2", os.path.join(Rm, "work", "s2")) \
            .replace("/data/KEEP_ALIVE", os.path.join(Rm, "KEEP_ALIVE"))
        stt = re.sub(r"^exec .*$", "exit 0", stt, flags=re.M)
        write_text(stt, os.path.join(sysd, "status.sh"))
        ps = subprocess.run(["bash", os.path.join(sysd, "status.sh")], capture_output=True, text=True, env=envw)
        assert ps.returncode == 0 and "runner: not started" in ps.stdout, (ps.returncode, ps.stdout, ps.stderr)
        rr, so = r3_relaunch(sysd, Rm)
        assert rr == 1 and "no S2 work tree" in so, (rr, so)
        # a refusal of s2_campaign.sh itself (the checkout is not clean): the stale KEEP_ALIVE goes
        W = os.path.join(Rm, "work", "s2"); co = os.path.join(Rm, "work", "ps_s2")
        os.makedirs(os.path.join(W, "c1"), exist_ok=True); os.makedirs(os.path.join(co, "ehpc", "node"), exist_ok=True)
        camp = open(os.path.join(ROOT, "ehpc", "node", "s2_campaign.sh")).read()
        camp = camp.replace("R=/data/work/ps_s2; PY=/data/miniforge3/envs/mace/bin/python; W=/data/work/s2",
                            f"R={co}; PY=/usr/bin/false; W={W}").replace("setsid nohup", "nohup")
        write_text(camp, os.path.join(co, "ehpc", "node", "s2_campaign.sh"))
        ge = dict(os.environ, GIT_AUTHOR_NAME="s2", GIT_AUTHOR_EMAIL="s2-selftest", GIT_COMMITTER_NAME="s2",
                  GIT_COMMITTER_EMAIL="s2-selftest", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
        for cmd in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "s2 self-test"]):
            subprocess.run(["git", "-C", co] + cmd, check=True, env=ge, capture_output=True)
        write_text("x\n", os.path.join(co, "stray.txt"))
        write_json({"status": "running"}, os.path.join(W, "c1", "campaign.json"))
        ka_ = os.path.join(Rm, "KEEP_ALIVE"); write_text("S2 c1\n", ka_)
        bt_ = time.time() - 600
        os.utime(ka_, (bt_ - 3600, bt_ - 3600))
        rr2, so2 = r3_relaunch(sysd, Rm, btime=bt_, campaign_sh=True)
        assert rr2 == 1 and "is not clean" in so2 and not os.path.exists(ka_), (rr2, so2, os.path.exists(ka_))
        led = os.path.join(W, "ledger"); os.makedirs(led, exist_ok=True)
        write_json([{"btime": 1.80e9, "end": 1.80e9 + 5400.0, "note": "deploy-only boot (self-test)"}],
                   os.path.join(led, "manual.json"))
        lg = ledger(Rm, now=1.81e9, backend=MockBackend(Rm))
        assert lg["complete"] and abs(lg["H_spent_h"] - 1.5) < 1e-9, lg
        return ("before the first start: status 'not started', relaunch refuses (no work tree); s2_campaign.sh refusing "
                "inside a relaunch: exit 1, stale KEEP_ALIVE removed; a manual ledger entry without a boot id: 1.5 h, complete")
    case("(z23) wrappers before the first start and on a refused start; manual ledger entries (round-4 R4-C1-8, -3, -9)",
         c_wrappers_r4)

    def c_held_durable():
        """Round-4 R4-C24-1 (N-F36): the STOP an A2 end rule asks for survives the hold: (i) relaxation 3 ends with QE's
        error banner and SIGTERM arrives while its validate-a2 runs: rc 4, no CAMPAIGN_STOPPED; the relaunch in a new
        boot STOPs with that reason before any A2 launch; (ii) validate-a2 exits 1 in the hold: CAMPAIGN_STOPPED holds
        both reasons; (iii) after (ii) the operator's relaunch does not raise it again and launches relaxation 4; (iv) the
        nstep-before-200 end (I-48) as (i)."""
        LAB = C2_ORDER[2]
        ok46 = lambda a, jf, log: (c46.dump_public({"validity": {"valid": True, "failed": []}}, read_json(jf)["out"]), 0)[1]  # noqa: E731

        def setup(tag, end):
            sysd, Rm, rn = r3_c2(tag, {}, a2_layout="48")
            rn.state.update({"K2": "pass", "step0": {"attempts": 1, "outcome": "pass"}})
            r3_markers(rn, ("gate:step0@1", "gate:K2"))
            for lab in C2_ORDER[:2]:
                r3_done(rn, lab)
            n = 41 if end == "pw_error" else 121
            r3_part(rn, LAB, q47.synthetic_pw_output(n_config=n, end=end, ranks=48, label=f"{LAB}.p1"), pid=2 ** 22 + 9,
                    rc=1 if end == "pw_error" else 0, ranks=48, lay="48")

            def final(j, r_, outs, rn=rn):
                ff = os.path.join(rn.L.a2_dir(rn.c, j["label"]), j["label"] + ".final.extxyz"); write_text("synthetic\n", ff)
                return {"file": os.path.basename(ff), "k": int(r_.get("k_last") or 0), "sha256": sha256_file(ff)}
            rn.a2_write_final = final
            rn.a2v_files = lambda j: {"final": os.path.join(rn.L.a2_dir(rn.c, j["label"]), j["label"] + ".final.extxyz"),
                                      "parent_final": "x"}
            return sysd, Rm, rn

        def relaunch(sysd, Rm, rn, boot):
            sf = os.path.join(rn.cdir, "CAMPAIGN_STOPPED")
            if os.path.exists(sf):
                os.replace(sf, sf + ".prev")                              # what run() does at a relaunch after a STOP
            write_text(boot, os.path.join(sysd, "mock", "boot_id"))
            write_text(f"{time.time() - 60:.0f}", os.path.join(sysd, "mock", f"btime.{boot}"))
            rn2 = c2_runner(Rm, boot=boot); rn2.state = rn.state; rn2.graph_now()
            rn2.h_spent = lambda: 100.0; rn2.a2v_files = rn.a2v_files; rn2.be.run46 = ok46
            rn2.be.sleep = lambda s: time.sleep(0.01)
            ev = []

            def launch(j, r, ranks, lay):
                ev.append(j["label"]); raise SystemExit("a2_launch")
            rn2.a2_launch = launch
            try:
                rc2 = rn2.loop()
            except SystemExit:
                rc2 = "launched"
            txt = open(os.path.join(rn2.cdir, "CAMPAIGN_STOPPED")).read() if os.path.exists(os.path.join(rn2.cdir, "CAMPAIGN_STOPPED")) else ""
            return rc2, ev, txt
        out = []
        for tag, end in (("i", "pw_error"), ("iv", "nstep")):
            sysd, Rm, rn = setup("hd_" + tag, end)

            def term(a, jf, log, rn=rn):
                rn.shutdown = True; return -15
            rn.be.run46 = term
            rn.set_campaign("running")
            rc = rn.loop()
            r = read_json(rn.a2_path(LAB))
            assert rc == 4 and not os.path.exists(os.path.join(rn.cdir, "CAMPAIGN_STOPPED")) and \
                r["end_rule"]["stop"] and r["end_rule"].get("stop_raised") is False, (tag, rc, r.get("end_rule"))
            rc2, ev, txt = relaunch(sysd, Rm, rn, f"n-boot-{tag}")
            assert rc2 == 3 and not ev and LAB in txt, (tag, rc2, ev, txt[:200])
            assert read_json(rn.a2_path(LAB))["end_rule"]["stop_raised"] is True
            out.append(f"({tag}) {end}: SIGTERM in the hold rc 4; relaunch STOPs with it, no launch")
        sysd, Rm, rn = setup("hd_ii", "pw_error")
        rn.be.run46 = lambda a, jf, log: 1
        rn.set_campaign("running")
        rc = rn.loop()
        txt = open(os.path.join(rn.cdir, "CAMPAIGN_STOPPED")).read()
        assert rc == 3 and "validate-a2" in txt and "pw.x error routine" in txt, (rc, txt[:300])
        rc3, ev3, _ = relaunch(sysd, Rm, rn, "n-boot-iii")
        assert rc3 == "launched" and ev3 == [C2_ORDER[3]], (rc3, ev3)
        out.append("(ii) a second STOP in the hold: CAMPAIGN_STOPPED holds both; (iii) the operator's relaunch launches "
                   "relaxation 4")
        return "; ".join(out)
    case("(z24) a held STOP survives a shutdown or a second STOP in the hold (round-4 R4-C24-1)", c_held_durable)

    def c_tree_partial():
        """Round-4 R4-C24-2 (N-F34): the tree is recorded at every tick until it holds the part's pw.x ranks; a first
        record of only the wrapper, run_qe.sh and mpirun is not a pw.x tree, so an OOM kill of a rank not yet recorded
        is the part's interruption ('oom', rerun), not a STOP for a human."""
        sysd, Rm, rn = r3_c2("treepart", {}, a2_layout="48")
        lab = C2_ORDER[0]
        t0 = time.time() - 60
        r3_part(rn, lab, q47.synthetic_pw_output(n_config=1, end="killed", ranks=48, label=f"{lab}.p1"), pid=7000,
                ranks=48, lay="48", t0=t0)
        early = {7000: "bash", 7001: "s2_run_qe.sh", 7002: "mpirun"}
        rn.be.proc_tree = lambda pid: dict(early)
        rn.be.descendants = lambda pid: set(early)                       # the same tree for the round-3 code
        rn.a2_record_pids(lab, read_json(rn.a2_path(lab)))
        write_text(f"137 {utc()}\n", rn.part_files(rn.L.a2_dir(rn.c, lab), lab, 1)["rc"])
        append_jsonl(os.path.join(sysd, "mock", "oom_events.jsonl"), {"boot": "m-boot", "t": t0 + 20, "task": "pw.x",
                                                                      "pid": 7010})
        s = rn.a2_status(rn.G["jobs_by_id"]["a2:" + lab])
        r = read_json(rn.a2_path(lab))
        assert s == "pending" and r["interruptions"][-1]["cause"] == "oom" and r["reruns_from_zero"] == 1, (s, r)
        full = {**early, **{7010 + i: "pw.x" for i in range(48)}}
        sysd2, Rm2, rn2 = r3_c2("treefull", {}, a2_layout="48")
        r3_part(rn2, lab, "", pid=7000, ranks=48, lay="48", t0=time.time())
        rn2.be.proc_tree = lambda pid: dict(early)
        jj = rn2.G["jobs_by_id"]["a2:" + lab]
        lf = rn2.part_files(rn2.L.a2_dir(rn2.c, lab), lab, 1)["launch"]
        rn2.watch_tree(jj["id"], lf, lab, 48)
        rn2.be.proc_tree = lambda pid: dict(full)
        rn2.watch_tree(jj["id"], lf, lab, 48)                             # the next tick, not 30 s later
        L = read_json(lf)
        assert len(L["pw_pids"]) == 48 and jj["id"] in rn2.tree_full, (len(L.get("pw_pids") or []), rn2.tree_full)
        return "first record without pw.x: an OOM of rank 7010 -> 'oom', rerun; the tree refreshed at the next tick holds 48 ranks"
    case("(z25) OOM of a rank before the tree holds the pw.x ranks (round-4 R4-C24-2)", c_tree_partial)

    def c_killed_between_parts():
        """Round-4 R4-C24-3 (N-F37): at 2x32 a relaxation waiting for its restart part when K3 = fail_replan stops A2 is
        killed_by_gate with its part-1 output and restart data moved aside unread (archive() then copies no output)."""
        sysd, Rm, rn = r3_c2("killparts", {}, a2_layout="2x32")
        for lab in C2_ORDER[:8]:
            r3_done(rn, lab)
        lab = C2_ORDER[8]
        d = r3_part(rn, lab, q47.synthetic_pw_output(n_config=60, end="exit", ranks=32, label=f"{lab}.p1"),
                    pid=2 ** 22 + 31, rc=0, ranks=32, lay="2x32")
        os.makedirs(os.path.join(d, "tmp", f"{lab}.save"), exist_ok=True)
        write_text("restart\n", os.path.join(d, "tmp", f"{lab}.save", "data-file-schema.xml"))
        r = read_json(rn.a2_path(lab))
        r["parts"].append({"n": 2, "input": f"{lab}.p2.in", "restart_mode": "restart", "nstep": 141})
        write_text("&CONTROL\n/\n", rn.part_files(d, lab, 2)["in"])
        write_json(r, rn.a2_path(lab))
        rn.state["K3"] = "fail_replan"
        jobs = [j for j in rn.G["jobs_by_id"].values() if j["phase"] == "a2"]
        st = rn.statuses()
        assert st["a2:" + lab] == "pending", st["a2:" + lab]
        rn.a2_phase(jobs, st)
        r = read_json(rn.a2_path(lab))
        kd = os.path.join(d, "discarded", "killed_by_gate")
        assert r["status"] == "killed_by_gate" and os.path.exists(os.path.join(kd, f"{lab}.p1.out")) and \
            os.path.isdir(os.path.join(kd, "tmp")) and not os.path.exists(rn.part_files(d, lab, 1)["out"]), r.get("status")
        return "relaxation 9 between parts: killed_by_gate, p1.out and tmp/ in discarded/killed_by_gate (none left for the archive)"
    case("(z26) a relaxation between parts when a gate stops A2 (round-4 R4-C24-3)", c_killed_between_parts)

    def c_gate_over_exit():
        """Round-4 missed item of the C2-C4 lens (N-F37): a stopping gate replaces an earlier 'cap' or 'spot' exit request
        of a running partner, so the partner is killed_by_gate after the drain (outputs moved aside unread), with no
        restart part and no interruption logged."""
        out = []
        lab = C2_ORDER[1]
        for prior, end in (("cap", "exit"), ("spot", "exit")):
            sysd, Rm, rn = r3_c2("gx_" + prior, {}, a2_layout="2x32")
            d = r3_part(rn, lab, q47.synthetic_pw_output(n_config=150, end="killed", ranks=32, label=f"{lab}.p1"),
                        pid=2 ** 22 + 77, ranks=32, lay="2x32")
            rn.request_exit(lab, d, prior)
            p = _Fake(pid=2 ** 22 + 77); rn.procs[lab] = {"p": p, "kind": "a2", "dir": d}
            rn.state["K2"] = "fail"
            rn.a2_stop_all("gate gate:K2")
            req = read_json(os.path.join(d, "exit_request.json"))
            f = rn.part_files(d, lab, 1)
            write_text(q47.synthetic_pw_output(n_config=201 if prior == "cap" else 151, end=end, ranks=32,
                                               label=f"{lab}.p1"), f["out"])
            write_text(f"0 {utc()}\n", f["rc"]); p.rc = 0
            rn.settle_gate_kill(lab, d)
            r = read_json(rn.a2_path(lab))
            intr = os.path.join(rn.cdir, "interruptions.jsonl")
            assert req["reason"] == "gate" and req.get("prior") == prior and r["status"] == "killed_by_gate" and \
                os.path.exists(os.path.join(d, "discarded", "killed_by_gate", f"{lab}.p1.out")) and \
                len(r["parts"]) == 1 and not os.path.exists(intr), (prior, req, r.get("status"))
            out.append(f"prior '{prior}': gate request (prior kept), killed_by_gate, no restart part, no interruption")
        return "; ".join(out)
    case("(z27) a gate's exit replaces a 'cap' or 'spot' request (round-4 missed item)", c_gate_over_exit)

    # ---------------------------------------------------------------- round-5 cases (2026-11-04, after bfaf321)
    def c_nodefix_checks():
        """Round-5 R5-2 (N-F31): a NODE_FIX whose commit changes the committed launcher moves the C1 check records
        aside, so check:nodescripts is pending again and its new record carries the new sha256; C2 then passes. A
        NODE_FIX whose commit changes qe_queue.sh while the node copy stays old STOPs C1 in its check phase. A C2
        STEP0_FIX moves C2's check records alike. Round-6 R6-C1-1 (N-B9): until check:upf passes again, the outputs
        are read with the Cl/Ca MD5 of the moved record, and a re-check giving other MD5 is a STOP."""
        sysd, Rm = mini("nodefix5", boot="nf-boot")
        _node_scripts(sysd)
        J = {"id": "check:nodescripts", "kind": "check", "what": "nodescripts", "phase": "check", "deps": []}
        rn = Runner("c1", Rm, MockBackend(Rm)); rn.boot = "nf-boot"
        rn.state = synthetic_state(commit="0" * 40, campaigns={"c1": "running"}); os.makedirs(rn.cdir, exist_ok=True)
        rn.run_check(J)
        sha0 = read_json(os.path.join(rn.cdir, "nodescripts_check.json"))["files"]["s2_run_qe.sh"]["sha256"]
        assert rn.status(J, {}) == "done"
        md5o = {"Cl": "a" * 32, "Ca": "b" * 32}                      # round-6 R6-C1-1: a passed C1 UPF record
        write_json({"schema": "s2-upf-1", "passed": True, "files": {e: {"md5": v} for e, v in md5o.items()}},
                   os.path.join(rn.cdir, "upf_check.json"))
        exp, new = rn.be.node_script_expected, {}
        rn.be.node_script_expected = lambda name: new[name].encode() if name in new else exp(name)
        for head, name in (("1" * 40, "s2_run_qe.sh"), ("2" * 40, "qe_queue.sh")):
            new[name] = exp(name).decode().replace("#!/bin/bash\n", "#!/bin/bash\n# 2026-11-05 dated fix (self-test)\n", 1)
            if name == "s2_run_qe.sh":                       # the launcher is the checkout's own file on the node
                write_text(new[name], rn.node.s2_run_qe)
            write_json({"git_head": head}, os.path.join(sysd, "mock", "config.json"))
            write_text("x\n", os.path.join(rn.cdir, "CAMPAIGN_STOPPED"))
            write_text(f"{head} 2026-11-05 node-script fix (self-test)\n", os.path.join(rn.cdir, "NODE_FIX"))
            rn.check_commit()
            assert rn.state["commit"] == head and rn.status(J, {}) == "pending", (rn.state["commit"], rn.status(J, {}))
            assert glob.glob(os.path.join(rn.cdir, "discarded", "commit_*", "nodescripts_check.json"))
            if name == "s2_run_qe.sh":
                rn.run_check(J)
                sha1 = read_json(os.path.join(rn.cdir, "nodescripts_check.json"))["files"][name]["sha256"]
                assert sha1 != sha0 and sha1 == hashlib.sha256(new[name].encode()).hexdigest(), (sha0, sha1)
                rn2 = Runner("c2", Rm, rn.be); rn2.boot = "nf-boot"; rn2.state = synthetic_state()
                os.makedirs(rn2.cdir, exist_ok=True)
                rn2.run_check(J)                                 # no STOP: the C1 record is that of the new commit
                rx = Runner("c1", Rm, rn.be); rx.boot = "nf-boot"    # round-6 R6-C1-1: the relaunch's first reads
                assert rx.md5_extra() == md5o, rx.md5_extra()          # use the moved record until check:upf passes
                try:
                    rx.run_check(dict(J, id="check:upf", what="upf")); raise AssertionError("other Cl/Ca MD5 accepted")
                except Stop as e:
                    assert "N-B9" in str(e), e
            else:
                try:
                    rn.run_check(J); raise AssertionError("C1 ran a queue that differs from the new commit's")
                except Stop as e:
                    assert "qe_queue.sh differs from the checkout's" in str(e), e
            os.remove(os.path.join(rn.cdir, "CAMPAIGN_STOPPED"))
        rn3 = Runner("c2", Rm, rn.be); rn3.boot = "nf-boot"          # the C2 step-0 fix moves C2's records alike
        rn3.state = synthetic_state(commit="2" * 40, step0={"attempts": 1, "outcome": "fail_pending_fix"})
        write_json({"git_head": "3" * 40}, os.path.join(sysd, "mock", "config.json"))
        write_text("3" * 40 + " 2026-11-05 step-0 writer fix (self-test)\n", os.path.join(rn3.cdir, "STEP0_FIX"))
        rn3.check_commit()
        assert rn3.status(J, {}) == "pending" and glob.glob(os.path.join(rn3.cdir, "discarded", "commit_*",
                                                                         "nodescripts_check.json")), rn3.status(J, {})
        assert PHASES["c1"][0] == PHASES["c2"][0] == "check"     # the checks run again before any further job
        return ("NODE_FIX changing s2_run_qe.sh: check records moved aside, check pending, new sha256 recorded, C2 "
                "passes; NODE_FIX changing the committed qe_queue.sh with the node copy old: STOP in the check phase; "
                "a C2 STEP0_FIX moves C2's check records alike; until check:upf passes the moved record's Cl/Ca MD5 "
                "are used, a re-check with other MD5 STOPs")
    case("(z28) a NODE_FIX re-runs the C1 checks at the new commit (round-5 R5-2; round-6 R6-C1-1)", c_nodefix_checks)

    for p in procs.values():                                   # nothing of the simulated campaign is left running
        if p.poll() is None:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except OSError:
                pass
    ok = "mace" not in sys.modules
    print(f"{'PASS' if ok else 'FAIL'} no-model: 'mace' {'not ' if ok else ''}in sys.modules; test files in {base}")
    results.append(("no-model", ok))
    nf = sum(not x for _, x in results)
    print(f"SELF-TEST {'PASS' if not nf else 'FAIL'} ({len(results)} cases, {nf} failed, {time.time() - t0:.0f} s)")
    return 1 if nf else 0


def _hyg_scan(text):
    """Hygiene of a script file: the patterns of scripts/46 (or its stub), with '$' counted only before a digit
    preceded by a space or at a line start (a shell or format '$' is not a currency)."""
    out = []
    for nm, rx in _hyg_patterns():
        if nm == "currency":
            rx = re.compile("[" + "".join(map(chr, (0xA5, 0x20AC, 0xA3, 0x5143))) + "]|\\b(?:US" + "D|CN" + "Y|RM"
                            + "B)\\b|(?:^|\\s)\\$\\s?\\d+(?:[.,]\\d+)?(?:\\s|$)", re.M)
        g = rx.search(text)
        if g:
            out.append(f"{nm}: {g.group(0)!r}")
    return out


# ---------------------------------------------------------------- CLI
def cmd_graph(campaign, state_file):
    st = read_json(state_file) if state_file else synthetic_state(a2_layout=None if campaign == "c1" else "48")
    g = graph(campaign, st)
    exp, adj = assert_counts(g, st)
    print(json.dumps({"campaign": campaign, "counts": g["counts"], "plan": exp, "adjustments": adj,
                      "jobs": len(g["jobs"]), "state": "file" if state_file else "synthetic (plan lists, all gates passed)"},
                     indent=1))
    assert "mace" not in sys.modules
    print("no-model: 'mace' not in sys.modules")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="S2 campaigns C1-C4 (results/objective2/s2/S2_PLAN.md sections 7-13, 16, 17)")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--work", default=None, help="self-test: parent of its temporary directory")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("graph"); p.add_argument("--campaign", required=True, choices=CAMPAIGNS); p.add_argument("--state")
    p = sub.add_parser("run"); p.add_argument("--campaign", required=True, choices=CAMPAIGNS)
    p.add_argument("--root", default=NODE_ROOT); p.add_argument("--mock", action="store_true", help=argparse.SUPPRESS)
    p = sub.add_parser("status"); p.add_argument("--root", default=NODE_ROOT)
    p = sub.add_parser("ledger"); p.add_argument("--root", default=NODE_ROOT)
    p = sub.add_parser("archive"); p.add_argument("--stage", required=True); p.add_argument("--campaign", required=True, choices=CAMPAIGNS)
    p.add_argument("--out", required=True)
    p = sub.add_parser("poller")
    for k in ("--url", "--dir", "--boot", "--ppid", "--poll", "--tag", "--keep-alive", "--done"):
        p.add_argument(k, required=k not in ("--tag", "--keep-alive", "--done"))
    p = sub.add_parser("_mock46"); p.add_argument("action"); p.add_argument("--job", required=True)
    p = sub.add_parser("_mockpw"); p.add_argument("--input", required=True); p.add_argument("--ranks", default="64")
    p.add_argument("--sys", required=True)
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test(a.work)
    if a.cmd == "graph":
        return cmd_graph(a.campaign, a.state)
    if a.cmd == "run":
        be = MockBackend(a.root) if a.mock else NodeBackend(a.root)
        if not a.mock and os.path.abspath(a.root) != NODE_ROOT:
            ap.error("the node runner runs only with --root /data")
        return Runner(a.campaign, a.root, be).run()
    if a.cmd == "status":
        return cmd_status(a.root)
    if a.cmd == "ledger":
        print(json.dumps(ledger(a.root), indent=1)); return 0
    if a.cmd == "archive":
        print(json.dumps(archive(a.stage, a.campaign, a.out), indent=1))
        assert "mace" not in sys.modules
        return 0
    if a.cmd == "poller":
        return poller_main(a.url, a.dir, a.boot, int(a.ppid), float(a.poll), a.keep_alive, a.done)
    if a.cmd == "_mock46":
        return mock46_main(a.action, a.job)
    if a.cmd == "_mockpw":
        return mockpw_main(a.input, a.ranks, a.sys)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
"""Input identity and the dry run of the S2b production campaign c3b (results/objective2/s2/S2B_PLAN.md section 9
step 3; C3B_OPERATIONS.md section 5, check 2). Pattern of fr_inputs.py.

dryrun    Production side. On the unrelaxed pool member given by --member (default m06, the first host of the draw
          order), with the committed builders of the checkout given by --repo and partners="unrelaxed" (as the
          pre-flight of S2_PLAN.md section 17 item 4): the region of each of the 19 production sites (scripts/46
          build_region), the default-pose pair of every c3b dopant at its sites (scripts/46 pair_record; Sr, Cl, Cs,
          GA; no Ca), and the single-point input of every cell (host, V+, D, D+V: 68 when every pair is built) as
          scripts/50 stage_sp writes it: the cell written by scripts/46 write_cell, read back, and passed to
          scripts/47 write_input (kind sp, ranks RANKS_SP). The outputs are not used for any calculation.
write-c1  C1 side. From the C1 source, rebuild every region of c1/regions and every pair of c1/pairs with the
          committed builders of --repo (scripts/46 job_region and job_build_pair, on a temporary copy of the C1 host
          and V+ files and records) and compare each with the C1 record as canonical JSON without 'written'. Then
          write the single-point input of every default-pose cell (hosts, V+, and the legs of every built p0 pair)
          from the C1 relaxed cell.
compare   Two outputs of the same mode, made at two commits (a checkout of 8bff03e and the c3b campaign commit):
          every region and pair record has the same canonical sha256, every .in is byte-identical, and a .meta.json
          may differ only in campaign, written and time.

Sources of write-c1 (--source):
  archive  ANALYST ONLY. The public C1 archive (--c1 results/objective2/s2/c1): the structures are members of
           c1/structures.tar.gz read in memory, the records are loaded blind (scripts/46 load_record). No other
           agent runs this source on the real C1 archive (S2B_PLAN.md sections 0 and 7).
  node     the node's C1 tree (--root /data).

--out is refused, before anything is read or written, if its real path lies under --c1, under
<repo>/results/objective2/s2/{c1,c2,c3,fr,c3b,c4b} (of --repo and of this checkout), under /data/work/s2 or, for the
node source, under <root>/work/s2 of --root (also casefolded and by file identity).

No energy is read: records are loaded blind and asserted free of E_mace_eV; no QE output is opened; no calculator is
loaded. scripts/47 is not changed by the c3b commit; the comparison shows it.

The self-test has two stages. Stage 1 needs no structure file: the refusals, the name grammar and compare on
synthetic outputs. Stage 2 uses the public reference cells only (ref233; labels naming m30 or m06 on its cells, as the
scripts/50 self-test does) and fails when they are absent. --self-test runs both; --self-test-light runs stage 1 alone
and says so.

    python results/objective2/s2/s2b/c3b_inputs.py dryrun --repo REPO --member m06 --out DIR
    python results/objective2/s2/s2b/c3b_inputs.py write-c1 --repo REPO --source node --root /data --state STATE --out DIR
    python results/objective2/s2/s2b/c3b_inputs.py write-c1 --repo REPO --source archive --c1 C1 --state STATE --out DIR
                                                                                                    (analyst only)
    python results/objective2/s2/s2b/c3b_inputs.py compare DIR_A DIR_B
    python results/objective2/s2/s2b/c3b_inputs.py --self-test [--repo-a REPO_A] [--repo-b REPO_B]
"""
import argparse, contextlib, hashlib, importlib.util, io, json, os, re, shutil, subprocess, sys, tarfile, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
NODE_WORK = "/data/work/s2"
ARCHIVE_TREES = ("c1", "c2", "c3", "fr", "c3b", "c4b")              # results/objective2/s2/<c>: never an --out
C3B_DOPANTS = ("Sr", "Cl", "Cs", "GA")                              # S2B_PLAN.md section 3: no Ca (G1)
META_FREE = ("campaign", "written", "time")                         # the only meta fields that may differ
RECORD = "c3b_inputs.json"
REGION_RE = re.compile(r"(m\d\d|ref233)_([BAX])(\d+)\.json")
PAIR_RE = re.compile(r"(m\d\d|ref233)_(Sr|Ca|Cl|Cs|GA)(\d+)p(\d+)\.json")


def load_repo(repo):
    """scripts/46 and scripts/47 of a checkout (each loads its own helpers from its own scripts/)."""
    sd = os.path.join(repo, "scripts")
    sys.path.insert(0, sd)
    out = {}
    for name, fn in (("c46", "46_s2_cells.py"), ("q47", "47_s2_qe.py")):
        s = importlib.util.spec_from_file_location(name, os.path.join(sd, fn))
        m = importlib.util.module_from_spec(s); s.loader.exec_module(m); out[name] = m
    return out["c46"], out["q47"]


def canon(obj):
    return json.dumps({k: v for k, v in obj.items() if k != "written"}, sort_keys=True, separators=(",", ":"))


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _under(rp, rd):
    """True iff the real path rp is the tree rd or lies under it: as strings, also casefolded, and by identity (rp or
    one of its existing ancestors being the existing tree rd)."""
    for a, b in ((rp, rd), (rp.casefold(), rd.casefold())):
        if a == b or a.startswith(b.rstrip(os.sep) + os.sep):
            return True
    if not os.path.exists(rd):
        return False
    x = rp
    while True:
        if os.path.exists(x) and os.path.samefile(x, rd):
            return True
        up = os.path.dirname(x)
        if up == x:
            return False
        x = up


def out_refusal(out, repo, c1=None, root=None):
    """The reason an --out is refused (its real path under --c1, an archive tree of --repo or of this checkout, the
    node's work tree /data/work/s2 or, for the node source, the work tree <root>/work/s2 of --root), or None."""
    rp = os.path.realpath(out)
    trees = [(NODE_WORK, NODE_WORK)] + ([(c1, "--c1")] if c1 else [])
    if root:
        trees.append((os.path.join(root, "work", "s2"), f"the work tree of --root {root}"))
    for r in sorted({os.path.realpath(repo), os.path.realpath(REPO)}):
        trees += [(os.path.join(r, "results", "objective2", "s2", c), f"results/objective2/s2/{c} of a checkout")
                  for c in ARCHIVE_TREES]
    for d, what in trees:
        if _under(rp, os.path.realpath(d)):
            return f"--out lies under {what}"
    return None


def _begin(a, mode, c1=None, root=None):
    out = os.path.abspath(a.out)
    why = out_refusal(out, a.repo, c1, root)                         # before anything is read or written
    if why:
        raise SystemExit(f"refused: {why} (C3B_OPERATIONS.md section 5; S2B_PLAN.md sections 0 and 9)")
    if os.path.isdir(out) and os.listdir(out):
        raise SystemExit("--out exists and is not empty")
    c46, q47 = load_repo(a.repo)
    os.makedirs(out, exist_ok=True)
    rec = {"schema": "s2b-c3b-inputs-1", "mode": mode,
           "repo_scripts_sha256": {f: sha256(os.path.join(a.repo, "scripts", f)) for f in
                                   ("42_s2_builders.py", "46_s2_cells.py", "47_s2_qe.py")},
           "regions": {}, "pairs": {}, "inputs": {}}
    return out, c46, q47, rec


def _sp_input(c46, q47, out, rec, at, label, wid, atoms_sha, campaign):
    """One single-point input as scripts/50 stage_sp writes it (kind sp, no dopant index, RANKS_SP)."""
    d = os.path.join(out, label)
    q47.write_input(at, label, d, kind="sp", dopant_index=None, ranks=q47.RANKS_SP, campaign=campaign,
                    cell={"work_id": wid, "atoms_sha256": atoms_sha})
    rec["inputs"][label] = {"work_id": wid, "in_sha256": sha256(os.path.join(d, f"{label}.in")),
                            "meta_sha256": sha256(os.path.join(d, f"{label}.meta.json"))}


def _labels(c46, lm, kind, **kw):
    return c46.make_label("s2", lm, kind, **kw)


def dryrun(a):
    """The production-side dry run on one unrelaxed member (no calculator, no relaxed structure, no energy)."""
    out, c46, q47, rec = _begin(a, "dryrun")
    from ase.io import read
    m, lm = a.member, a.label_member or a.member
    cx = c46.host_context(m)
    S = c46.site_sets(cx)
    hwid = c46.make_work_id(m, "host")
    rec.update({"member": m, "label_member": lm, "partners": "unrelaxed", "dopants": list(C3B_DOPANTS)})
    tmp = tempfile.mkdtemp(prefix="c3b_inputs_")
    try:
        def staged(atoms, name):
            """As stage_sp: the file scripts/46 write_cell writes, read back; (atoms, sha256 of the file)."""
            f = os.path.join(tmp, f"{name}.extxyz")
            c46.write_cell(f, atoms)
            return read(f), sha256(f)
        at, sh = staged(cx.host, hwid)
        _sp_input(c46, q47, out, rec, at, _labels(c46, lm, "host"), hwid, sh, "c3b")
        n_sites = 0
        for L in "BAX":
            toks = [T for T in c46.TOKENS_OF[L] if T in C3B_DOPANTS]
            if not toks:
                continue
            for j in sorted(int(x) for x in S[L]["first"]) + [int(x) for x in S[L]["far"]]:     # scripts/50 order
                n_sites += 1
                reg = c46.build_region(cx.host, m, j, roles=c46.site_roles(m, L, j, S, None), host_work_id=hwid)
                rec["regions"][f"{m}_{L}{j}"] = {"region_id": reg.get("region_id"), "n_free": len(reg.get("free") or []),
                                                 "sha256": sha256_text(canon(reg))}
                vwid = c46.make_work_id(m, "V", L=L, j=j)
                at, sh = staged(cx.vac, vwid)
                _sp_input(c46, q47, out, rec, at, _labels(c46, lm, "V", L=L, j=j), vwid, sh, "c3b")
                for T in toks:
                    pr, bh, bv = c46.pair_record(cx.host, cx.vac, cx, T, j, "p0", partners="unrelaxed",
                                                 parents={"novac": hwid, "vac": vwid})
                    rec["pairs"][f"{m}_{T}{j}p0"] = {"status": pr.get("status"), "sha256": sha256_text(canon(pr))}
                    if pr.get("status") != "built":
                        continue
                    for kind, b in (("D", bh), ("DV", bv)):
                        wid = c46.make_work_id(m, kind, token=T, j=j, n=0)
                        at, sh = staged(b.atoms, wid)
                        _sp_input(c46, q47, out, rec, at, _labels(c46, lm, kind, token=T, j=j, k=0), wid, sh, "c3b")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    assert "mace" not in sys.modules
    built = sum(1 for p in rec["pairs"].values() if p["status"] == "built")
    rec["counts"] = {"sites": n_sites, "regions": len(rec["regions"]), "pairs": len(rec["pairs"]), "pairs_built": built,
                     "inputs": len(rec["inputs"])}
    json.dump(rec, open(os.path.join(out, RECORD), "w"), indent=1)
    print(f"dryrun {m}: {n_sites} sites, {len(rec['regions'])} regions, {len(rec['pairs'])} pairs ({built} built), "
          f"{len(rec['inputs'])} single-point inputs")
    return 0 if built == len(rec["pairs"]) and len(rec["inputs"]) == 1 + n_sites + 2 * built else 1


class Source:
    """The C1 source: structure files by their record path, records (blind), region and pair records."""

    def __init__(self, c46, kind, *, c1=None, root=None):
        self.c46, self.kind = c46, kind
        if kind == "archive":
            self.dir = c1
            self.tar = tarfile.open(os.path.join(c1, "structures.tar.gz"))
        elif kind == "node":
            self.L = c46.Layout(kind="node", root=root)
            self.dir = self.L.campaign_dir("c1")
        else:
            raise SystemExit(f"unknown source {kind!r}")

    def record_path(self, wid):
        return os.path.join(self.dir, "records", f"{wid}.json") if self.kind == "archive" else self.L.record("c1", wid)

    def has(self, wid):
        return os.path.exists(self.record_path(wid))

    def record(self, wid):
        rec = self.c46.load_record(self.record_path(wid), blind=True)
        assert "E_mace_eV" not in json.dumps(rec), "MACE energy in a blinded record read"
        return rec

    def relaxed_bytes(self, wid):
        """The bytes of the relaxed structure named by the record (as scripts/50 relaxed_path)."""
        rel = (self.record(wid).get("files") or {}).get("relaxed") or f"cells/{wid}/relaxed.extxyz"
        if self.kind == "archive":
            return self.tar.extractfile(rel).read()
        return open(os.path.join(self.dir, rel), "rb").read()

    def names(self, sub, pattern):
        d = os.path.join(self.dir, sub)
        return sorted(f for f in (os.listdir(d) if os.path.isdir(d) else []) if pattern.fullmatch(f))

    def json(self, rel):
        return json.load(open(os.path.join(self.dir, rel)))


def write_c1(a):
    """The C1-side identity: every C1 region and pair rebuilt at --repo, and the default-pose single-point inputs."""
    out, c46, q47, rec = _begin(a, "c1", a.c1 if a.source == "archive" else None, a.root if a.source == "node" else None)
    from ase.io import read
    state = json.load(open(a.state)) if a.state else {}
    st0 = state.get("stage0") or {}
    cal = st0.get("m05_cal") or c46.CAL_SITES["m05"]
    m05_cal = {L: int(cal[L]) for L in "BAX"}                        # as scripts/50 m05_cal
    prov = (st0.get("pbcl") or {}).get("decision") == "provisional_2.837"   # as scripts/50 pbcl_provisional
    src = Source(c46, a.source, c1=a.c1, root=a.root)
    regions = [REGION_RE.fullmatch(f).groups() for f in src.names("regions", REGION_RE)]
    pairs = [PAIR_RE.fullmatch(f).groups() for f in src.names("pairs", PAIR_RE)]
    rec.update({"source": a.source, "state_given": bool(a.state), "m05_cal": m05_cal, "pbcl_provisional": prov,
                "label_member": a.label_member})
    lab_m = lambda m: a.label_member or m                            # noqa: E731
    tmp = tempfile.mkdtemp(prefix="c3b_inputs_")
    try:
        Lt = c46.Layout(kind="node", root=tmp)

        def put(wid):
            os.makedirs(Lt.cell_dir("c1", wid), exist_ok=True)
            with open(Lt.cell_file("c1", wid, "relaxed"), "wb") as fh:
                fh.write(src.relaxed_bytes(wid))
            json.dump(src.record(wid), open(Lt.record("c1", wid), "w"))

        def sp(wid, label):
            b = src.relaxed_bytes(wid)
            at = read(io.StringIO(b.decode()), format="extxyz")
            _sp_input(c46, q47, out, rec, at, label, wid, hashlib.sha256(b).hexdigest(), "c1")

        for m in sorted({r[0] for r in regions} | {p[0] for p in pairs}):
            hw = c46.make_work_id(m, "host")
            put(hw)
            sp(hw, _labels(c46, lab_m(m), "host"))
        for m, L, j in regions:
            j = int(j)
            name = f"{m}_{L}{j}"
            job = {"action": "region", "root": tmp, "campaign": "c1", "member": m, "site": j}
            if m == "m05":
                job["m05_cal"] = m05_cal
            try:
                eq = canon(c46.job_region(job)) == canon(src.json(os.path.join("regions", f"{name}.json")))
                err = None
            except Exception as e:                                   # noqa: BLE001 (reported as a difference)
                eq, err = False, f"{type(e).__name__}: {str(e)[:200]}"
            rec["regions"][name] = {"equal_c1": eq, "error": err,
                                    "sha256": sha256(os.path.join(src.dir, "regions", f"{name}.json"))}
            vw = c46.make_work_id(m, "V", L=L, j=j)
            if src.has(vw):
                put(vw)
                sp(vw, _labels(c46, lab_m(m), "V", L=L, j=j))
        for m, T, j, n in pairs:
            j, n = int(j), int(n)
            name = f"{m}_{T}{j}p{n}"
            pr_c1 = src.json(os.path.join("pairs", f"{name}.json"))
            job = {"action": "build-pair", "root": tmp, "campaign": "c1", "member": m, "site": j, "token": T,
                   "start": f"p{n}", "partners": pr_c1.get("partners", "relaxed"),
                   "allow_provisional": bool(prov and T == "Cl" and n > 0)}
            try:
                eq, err = canon(c46.job_build_pair(job)) == canon(pr_c1), None
            except Exception as e:                                   # noqa: BLE001 (reported as a difference)
                eq, err = False, f"{type(e).__name__}: {str(e)[:200]}"
            rec["pairs"][name] = {"equal_c1": eq, "error": err, "status": pr_c1.get("status"),
                                  "sha256": sha256(os.path.join(src.dir, "pairs", f"{name}.json"))}
            if n == 0 and pr_c1.get("status") == "built":
                for kind in ("D", "DV"):
                    w = c46.make_work_id(m, kind, token=T, j=j, n=0)
                    if src.has(w):
                        sp(w, _labels(c46, lab_m(m), kind, token=T, j=j, k=0))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    assert "mace" not in sys.modules
    bad = [k for sub in ("regions", "pairs") for k, v in rec[sub].items() if not v["equal_c1"]]
    rec["counts"] = {"regions": len(rec["regions"]), "pairs": len(rec["pairs"]), "inputs": len(rec["inputs"]),
                     "not_equal_c1": len(bad)}
    json.dump(rec, open(os.path.join(out, RECORD), "w"), indent=1)
    for k in bad:
        print(f"DIFFERS {k}" + (f" ({(rec['regions'].get(k) or rec['pairs'].get(k))['error']})"
                                if (rec["regions"].get(k) or rec["pairs"].get(k))["error"] else ""))
    print(f"write-c1: {len(rec['regions'])} regions and {len(rec['pairs'])} pairs rebuilt, {len(bad)} differ from c1; "
          f"{len(rec['inputs'])} single-point inputs")
    return 1 if bad or not rec["regions"] else 0


def meta_diff(ma, mb):
    return sorted(k for k in set(ma) | set(mb) if k not in META_FREE and ma.get(k) != mb.get(k))


def compare(da, db, verbose=False):
    """0 iff the two outputs have the same mode, the same region and pair records (canonical sha256; in mode c1 each
    also equal to c1 on both sides), byte-identical inputs and meta records equal outside campaign, written and time.
    Prints the differences and one summary line (every file with verbose)."""
    ra, rb = (json.load(open(os.path.join(d, RECORD))) for d in (da, db))
    bad = 0

    def line(ok, text):
        nonlocal bad
        bad += not ok
        if verbose or not ok:
            print(f"{'OK  ' if ok else 'DIFF'} {text}")
    line(ra.get("mode") == rb.get("mode"), f"mode {ra.get('mode')} / {rb.get('mode')}")
    for sub in ("regions", "pairs"):
        line(bool(ra[sub]) and bool(rb[sub]), f"{sub}: {len(ra[sub])} / {len(rb[sub])} (none is a difference)")
        for k in sorted(set(ra[sub]) | set(rb[sub])):
            xa, xb = ra[sub].get(k), rb[sub].get(k)
            ok = xa is not None and xb is not None and xa["sha256"] == xb["sha256"] and xa.get("status") == xb.get("status")
            if ok and ra.get("mode") == "c1":
                ok = xa.get("equal_c1") is True and xb.get("equal_c1") is True
            line(ok, f"{sub[:-1]} {k}")
    labs = sorted(set(ra["inputs"]) | set(rb["inputs"]))
    line(bool(labs), f"inputs: {len(ra['inputs'])} / {len(rb['inputs'])} (none is a difference)")
    line(set(ra["inputs"]) == set(rb["inputs"]), "input labels (the two records name other labels)")
    for lab in labs:
        pa, pb = (os.path.join(d, lab, f"{lab}.in") for d in (da, db))
        line(os.path.exists(pa) and os.path.exists(pb) and open(pa, "rb").read() == open(pb, "rb").read(), f"{lab}.in")
        qa, qb = (os.path.join(d, lab, f"{lab}.meta.json") for d in (da, db))
        if os.path.exists(qa) and os.path.exists(qb):
            keys = meta_diff(json.load(open(qa)), json.load(open(qb)))
            line(not keys, f"{lab}.meta.json" + (f" ({', '.join(keys)})" if keys else ""))
        else:
            line(False, f"{lab}.meta.json (missing)")
    print(f"compare ({ra.get('mode')}): {len(ra['regions'])} regions, {len(ra['pairs'])} pairs, {len(labs)} inputs; "
          f"{bad} differ")
    return 1 if bad else 0


# ---------------------------------------------------------------- self-test
def _quiet(fn, *args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*args)
    return rc, buf.getvalue()


def _synthetic(d, mode="dryrun", campaign="c3b"):
    """A synthetic output (stage 1): two regions, two pairs, three inputs; no structure."""
    rec = {"schema": "s2b-c3b-inputs-1", "mode": mode, "regions": {}, "pairs": {}, "inputs": {}}
    for k in ("m06_B1", "m06_A2"):
        rec["regions"][k] = {"sha256": sha256_text(k), "equal_c1": True}
    for k in ("m06_Sr1p0", "m06_Cs2p0"):
        rec["pairs"][k] = {"sha256": sha256_text(k), "status": "built", "equal_c1": True}
    for lab in ("s2_m06_host", "s2_m06_VB1", "s2_m06_Sr1o0_vac"):
        os.makedirs(os.path.join(d, lab))
        open(os.path.join(d, lab, f"{lab}.in"), "w").write(f"&control\n prefix = '{lab}'\n/\n")
        json.dump({"label": lab, "campaign": campaign, "time": campaign, "electrons": {"n_el": 1}},
                  open(os.path.join(d, lab, f"{lab}.meta.json"), "w"))
        rec["inputs"][lab] = {"work_id": lab}
    json.dump(rec, open(os.path.join(d, RECORD), "w"))
    return rec


def stage1(base):
    """No structure file: the name grammar, the refusals and compare on synthetic outputs."""
    assert REGION_RE.fullmatch("m30_A188.json").groups() == ("m30", "A", "188")
    assert PAIR_RE.fullmatch("m05_Cl49p3.json").groups() == ("m05", "Cl", "49", "3")
    assert not REGION_RE.fullmatch("m30_A188.json.bak") and not PAIR_RE.fullmatch("m30_Cs188.json")
    assert ARCHIVE_TREES == ("c1", "c2", "c3", "fr", "c3b", "c4b") and NODE_WORK == "/data/work/s2"
    assert C3B_DOPANTS == ("Sr", "Cl", "Cs", "GA") and META_FREE == ("campaign", "written", "time")
    # compare
    da, db = (os.path.join(base, x) for x in ("syn_a", "syn_b"))
    _synthetic(da); _synthetic(db, campaign="c3")
    rc, so = _quiet(compare, da, db)
    assert rc == 0 and "0 differ" in so, so                          # campaign and time alone may differ
    n_cmp = 0

    def broken(edit, word):
        nonlocal n_cmp
        dx = os.path.join(base, f"syn_x{n_cmp}")
        _synthetic(dx)
        edit(dx)
        for pair in ((da, dx), (dx, da)):
            rc_, so_ = _quiet(compare, *pair)
            assert rc_ == 1 and word in so_, (word, so_)
        n_cmp += 1

    def rec_edit(fn):
        def edit(dx):
            r = json.load(open(os.path.join(dx, RECORD))); fn(r); json.dump(r, open(os.path.join(dx, RECORD), "w"))
        return edit
    lab = "s2_m06_VB1"
    broken(lambda dx: open(os.path.join(dx, lab, f"{lab}.in"), "a").write(" "), f"DIFF {lab}.in")
    broken(lambda dx: os.remove(os.path.join(dx, lab, f"{lab}.in")), f"DIFF {lab}.in")
    broken(lambda dx: json.dump({"label": lab, "campaign": "c3b", "electrons": {"n_el": 2}},
                                open(os.path.join(dx, lab, f"{lab}.meta.json"), "w")), "electrons")
    broken(lambda dx: os.remove(os.path.join(dx, lab, f"{lab}.meta.json")), "missing")
    broken(rec_edit(lambda r: r["regions"]["m06_B1"].update(sha256="0")), "DIFF region m06_B1")
    broken(rec_edit(lambda r: r["regions"].pop("m06_A2")), "DIFF region m06_A2")
    broken(rec_edit(lambda r: r["pairs"]["m06_Sr1p0"].update(sha256="0")), "DIFF pair m06_Sr1p0")
    broken(rec_edit(lambda r: r["pairs"]["m06_Cs2p0"].update(status="rejected")), "DIFF pair m06_Cs2p0")
    broken(rec_edit(lambda r: r["inputs"].pop("s2_m06_host")), "DIFF input labels")
    broken(rec_edit(lambda r: r.update(mode="c1")), "DIFF mode")
    # mode c1: a record not equal to c1 on either side is a difference, although both sides agree
    dc, dd = (os.path.join(base, x) for x in ("syn_c1a", "syn_c1b"))
    _synthetic(dc, "c1"); _synthetic(dd, "c1")
    assert _quiet(compare, dc, dd)[0] == 0
    for d in (dc, dd):
        r = json.load(open(os.path.join(d, RECORD))); r["pairs"]["m06_Sr1p0"]["equal_c1"] = False
        json.dump(r, open(os.path.join(d, RECORD), "w"))
    rc, so = _quiet(compare, dc, dd)
    assert rc == 1 and "DIFF pair m06_Sr1p0" in so, so
    # an empty output is a difference, never a pass
    de = os.path.join(base, "syn_empty"); os.makedirs(de)
    json.dump({"mode": "dryrun", "regions": {}, "pairs": {}, "inputs": {}}, open(os.path.join(de, RECORD), "w"))
    assert _quiet(compare, de, de)[0] == 1
    # refusals of --out, by the rule and by the command line (nothing is made)
    fake = os.path.join(base, "fakerepo")
    for c in ARCHIVE_TREES:
        os.makedirs(os.path.join(fake, "results", "objective2", "s2", c))
    os.symlink(os.path.join(fake, "results", "objective2", "s2", "c3b"), os.path.join(base, "link_c3b"))
    n_ref = 0
    for c in ARCHIVE_TREES:
        for o in (os.path.join(fake, "results", "objective2", "s2", c, "x"),
                  os.path.join(fake, "results", "objective2", "s2", c.upper(), "x"),
                  os.path.join(REPO, "results", "objective2", "s2", c, "x")):
            assert out_refusal(o, fake) == f"--out lies under results/objective2/s2/{c} of a checkout", (o, c)
            n_ref += 1
    assert out_refusal(os.path.join(base, "link_c3b", "x"), fake) is not None
    assert out_refusal("/data/work/s2/c3b/d", fake) == "--out lies under /data/work/s2"
    root = os.path.join(base, "node")
    assert out_refusal(os.path.join(root, "work", "s2", "c3b"), fake, root=root) and \
        out_refusal(os.path.join(root, "work", "s2", "c3b"), fake) is None
    c1 = os.path.join(base, "arch", "c1"); os.makedirs(c1)
    assert out_refusal(os.path.join(c1, "x"), fake, c1) == "--out lies under --c1"
    assert out_refusal(os.path.join(base, "out_ok"), fake) is None
    me = os.path.abspath(__file__)
    n_cli = 0
    for args in (["dryrun", "--repo", fake, "--out", os.path.join(fake, "results", "objective2", "s2", "c3b", "x")],
                 ["dryrun", "--repo", fake, "--out", os.path.join(base, "link_c3b", "x")],
                 ["write-c1", "--repo", fake, "--source", "node", "--root", root, "--out",
                  os.path.join(root, "work", "s2", "c1", "x")],
                 ["write-c1", "--repo", fake, "--source", "archive", "--c1", c1, "--out", os.path.join(c1, "x")]):
        o = args[args.index("--out") + 1]
        p = subprocess.run([sys.executable, "-B", me] + args, capture_output=True, text=True)
        assert p.returncode != 0 and "refused: --out lies under" in p.stderr and not os.path.exists(o), (args, p.stderr)
        n_cli += 1
    assert "mace" not in sys.modules
    return (f"stage 1: name grammar; compare passes on a campaign-only difference and reports {n_cmp} single "
            f"differences on either side (an input byte, a missing input, a meta field, a missing meta, a region or "
            f"pair sha256, a missing region, a pair status, a missing input record, the mode), a record not equal to "
            f"c1 and an empty output; {n_ref} --out refusals by the rule (the six trees as literals, a case variant, "
            f"this checkout), a link, the node work tree, the --root work tree, --c1; {n_cli} refusals by the command "
            f"line with nothing made")


def stage2(base, repo_a, repo_b):
    """The reference cells (ref233): a C1-like tree by the scripts/46 mock pipeline; write-c1 and dryrun at two
    checkouts, compared; an edited C1 region and an edited C1 pair are reported."""
    c46, _ = load_repo(REPO)
    if not os.path.exists(os.path.join(REPO, c46.REF_HOST)):
        raise SystemExit(f"stage 2 needs the public reference cell {c46.REF_HOST}: absent; the self-test FAILS")
    root = os.path.join(base, "node")
    b = {"campaign": "c1", "root": root, "member": "ref233", "calc": "mock-harmonic", "threads": 1}
    c46.run_job(dict(b, action="relax-host", work_id="s2_ref233_host"))
    c46.run_job(dict(b, action="region", site=128))
    c46.run_job(dict(b, action="build-vac", site=128))
    c46.run_job(dict(b, action="relax", work_id="s2_ref233_VA128"))
    pr = c46.run_job(dict(b, action="build-pair", token="Cs", site=128, start="p0", partners="relaxed"))
    assert pr["status"] == "built", pr.get("rejection")
    for lg in ("novac", "vac"):
        c46.run_job(dict(b, action="relax", work_id=pr["legs"][lg]["work_id"]))
    me = os.path.abspath(__file__)

    def run(*args):
        p = subprocess.run([sys.executable, "-B", me] + list(args), capture_output=True, text=True)
        return p.returncode, p.stdout, p.stderr
    # C1 side at the two checkouts
    outs = []
    for tag, repo in (("A", repo_a), ("B", repo_b)):
        o = os.path.join(base, f"c1_{tag}")
        rc, so, se = run("write-c1", "--repo", repo, "--source", "node", "--root", root, "--label-member", "m30",
                         "--out", o)
        assert rc == 0, so + se
        outs.append(o)
    r = json.load(open(os.path.join(outs[1], RECORD)))
    assert r["counts"] == {"regions": 1, "pairs": 1, "inputs": 4, "not_equal_c1": 0}, r["counts"]
    assert sorted(r["inputs"]) == sorted(["s2_m30_host", "s2_m30_VA128", "s2_m30_Cs128o0_novac",
                                          "s2_m30_Cs128o0_vac"]), sorted(r["inputs"])
    assert compare(*outs) == 0, "the C1-side inputs differ between the two checkouts"
    # an edited C1 region (one free index) and an edited C1 pair (one field): exit 1, DIFFERS, compare fails
    L0 = c46.Layout(kind="node", root=root)

    def free_edited(r_):
        fr_ = [int(i) for i in r_["free"]]
        r_["free"] = sorted(fr_[:-1] + [min(set(range(max(fr_) + 2)) - set(fr_))])

    def pair_edited(r_):
        r_["region_id"] = f"{r_.get('region_id')}-edited"
    n_edit = 0
    for tag, path_of, edit, name in (("region", lambda L_: L_.region("c1", "ref233", "A", 128), free_edited, "ref233_A128"),
                                     ("pair", lambda L_: L_.pair("c1", "ref233", "Cs", 128, 0), pair_edited,
                                      "ref233_Cs128p0")):
        rt = os.path.join(base, f"node_{tag}_edited")
        shutil.copytree(root, rt, symlinks=True)
        pe = path_of(c46.Layout(kind="node", root=rt))
        assert pe != path_of(L0)
        rx = json.load(open(pe)); edit(rx); json.dump(rx, open(pe, "w"), indent=1)
        ox = os.path.join(base, f"c1_{tag}_edited")
        rc, so, se = run("write-c1", "--repo", REPO, "--source", "node", "--root", rt, "--label-member", "m30", "--out", ox)
        rr = json.load(open(os.path.join(ox, RECORD)))
        assert rc == 1 and f"DIFFERS {name}" in so and rr["counts"]["not_equal_c1"] >= 1, (tag, rc, so, se)
        for pair in ((ox, outs[0]), (outs[0], ox)):
            rc_, so_ = _quiet(compare, *pair)
            assert rc_ == 1 and f"DIFF {tag} {name}" in so_, (tag, so_)
        n_edit += 1
    # production side: the dry run on the unrelaxed reference cell at the two checkouts
    dry = []
    for tag, repo in (("A", repo_a), ("B", repo_b)):
        o = os.path.join(base, f"dry_{tag}")
        rc, so, se = run("dryrun", "--repo", repo, "--member", "ref233", "--label-member", "m06", "--out", o)
        assert rc in (0, 1) and os.path.exists(os.path.join(o, RECORD)), so + se   # 1: a pair rejected on this cell
        dry.append(o)
    d = json.load(open(os.path.join(dry[1], RECORD)))["counts"]
    assert d["sites"] == d["regions"] == 19 and d["pairs"] == 24, d
    assert d["inputs"] == 1 + 19 + 2 * d["pairs_built"] and d["pairs_built"] >= 1, d
    assert compare(*dry) == 0, "the dry-run records or inputs differ between the two checkouts"
    assert _quiet(compare, dry[0], outs[0])[0] == 1                  # two modes never compare equal
    assert "mace" not in sys.modules
    return (f"stage 2: on ref233 the C1 region, pair and 4 default-pose single-point inputs rebuilt and written at "
            f"{os.path.basename(repo_a)} and {os.path.basename(repo_b)} are identical; {n_edit} edited C1 records (a "
            f"region free index, a pair field) give exit 1, DIFFERS and a failing compare on either side; the dry "
            f"run gives 19 regions, 24 pairs ({d['pairs_built']} built) and {d['inputs']} inputs, identical at the "
            f"two checkouts")


def self_test(repo_a, repo_b, light=False):
    base = tempfile.mkdtemp(prefix="c3b_inputs_selftest_")
    try:
        print(stage1(base))
        if light:
            print("c3b_inputs self-test LIGHT: stage 1 only; stage 2 (the reference cells) was NOT run")
            return 0
        print(stage2(base, repo_a, repo_b))
        print("c3b_inputs self-test passed (stages 1 and 2)")
        return 0
    finally:
        shutil.rmtree(base, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description="c3b input identity and dry run (S2B_PLAN.md section 9 step 3). The "
                                             "archive source opens the C1 structure archive and records: analyst only.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--self-test-light", action="store_true", help="stage 1 only (no structure file); says so")
    ap.add_argument("--repo-a", default=REPO, help="self-test: the first checkout (e.g. one at 8bff03e)")
    ap.add_argument("--repo-b", default=REPO, help="self-test: the second checkout (the c3b commit)")
    sub = ap.add_subparsers(dest="cmd")
    d = sub.add_parser("dryrun", description="The production-side dry run on one unrelaxed member.")
    d.add_argument("--repo", default=REPO); d.add_argument("--out", required=True)
    d.add_argument("--member", default="m06")
    d.add_argument("--label-member", default=None, help="the member named in the labels (the self-test: m06 on ref233)")
    w = sub.add_parser("write-c1", description="Rebuild every C1 region and pair and write the default-pose single-"
                                               "point inputs. --source archive: analyst only.")
    w.add_argument("--repo", default=REPO); w.add_argument("--out", required=True)
    w.add_argument("--source", required=True, choices=["archive", "node"],
                   help="node: the node's C1 tree; archive: the public C1 archive, ANALYST ONLY (it opens "
                        "c1/structures.tar.gz and c1/records, blinded to every other agent)")
    w.add_argument("--c1", default=os.path.join(REPO, "results", "objective2", "s2", "c1"))
    w.add_argument("--root", default="/data")
    w.add_argument("--state", default=None, help="state.json or c1/state_end.json: the m05 calibration sites and the "
                                                 "Pb-Cl decision of Stage 0 (the defaults of scripts/46 without it)")
    w.add_argument("--label-member", default=None, help="the member named in the labels (the self-test: m30 on ref233)")
    c = sub.add_parser("compare"); c.add_argument("a"); c.add_argument("b"); c.add_argument("--verbose", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test or a.self_test_light:
        return self_test(os.path.abspath(a.repo_a), os.path.abspath(a.repo_b), light=a.self_test_light and not a.self_test)
    if a.cmd in ("dryrun", "write-c1"):
        a.repo = os.path.abspath(a.repo)
        return dryrun(a) if a.cmd == "dryrun" else write_c1(a)
    if a.cmd == "compare":
        return compare(a.a, a.b, a.verbose)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
"""Input identity and the dry run of the S2b far-site reference FR (results/objective2/s2/S2B_PLAN.md section 9 step 3;
D4 of the fr operations note).

write    From the C1 source, rebuild the region m30_A188 and the pair m30_Cs188p0 with the committed builders of the
         checkout given by --repo (scripts/46 job_region and job_build_pair, on a temporary copy of the C1 host, V+ and
         record files) and compare them with c1/regions and c1/pairs as canonical JSON without 'written'. Then write
         the four part-1 inputs of FR exactly as scripts/50 a2_launch does: scripts/47 write_input on the C1 relaxed A1
         cell (host_R: the S2-relaxed host with the free atoms of the region record; the others: the free list of the
         A1 record), nstep = nstep_first of c1/smoke.json, the ranks of the A2 layout, campaign fr; <label>.in renamed
         <label>.p1.in. Written to --out, with fr_inputs.json (sha256 of every file, the two comparisons).
compare  Two write outputs, made at two commits (a checkout of 8bff03e and the S2b campaign commit): every .p1.in must
         be byte-identical; a .meta.json may differ only in campaign and time.

Sources (--source):
  archive  ANALYST ONLY. The public C1 archive (--c1 results/objective2/s2/c1): the structure files are members of
           c1/structures.tar.gz read in memory, the records are loaded blind (scripts/46 load_record). Under the S2b
           blinding rules (S2B_PLAN.md sections 0 and 7) the C1 structure archive and records are opened only by the
           analyst; no other agent runs this source on the real C1 archive. The self-test exercises it on a synthetic
           archive (scripts/50 archive of a C1-like tree on the public reference cells) in a temporary directory.
  node     the node's C1 tree (--root /data: /data/work/s2/c1); on the node this is D4.

Ranks: with --state (the node's state.json) they are those of its a2_layout (one copy; 2x32 or none is refused) and a
--ranks that differs is refused; without it, --ranks (default 48).
--out is refused, before anything is read or written, if its real path lies under --c1, under
<repo>/results/objective2/s2/{c1,c2,c3,fr} (of --repo and of this checkout), under /data/work/s2 or, for the node
source, under <root>/work/s2 of --root; the comparison is also casefolded and by file identity (a case-variant or
otherwise aliased spelling of a protected tree is refused).

No energy is read: records are loaded blind and asserted free of E_mace_eV; no QE output is opened; no calculator is
loaded. The self-test uses the public reference cells only (a C1-like tree made by the scripts/46 mock pipeline on
ref233, the FR labels naming its cells, as the scripts/50 self-test does), and compares the inputs with those
scripts/50 Runner.a2_launch writes for the same FR jobs (the pw.x launch stubbed).

    python results/objective2/s2/s2b/fr_inputs.py write --repo REPO --source node --root /data --state STATE --out DIR
    python results/objective2/s2/s2b/fr_inputs.py write --repo REPO --source archive --c1 C1 --out DIR   (analyst only)
    python results/objective2/s2/s2b/fr_inputs.py compare DIR_A DIR_B
    python results/objective2/s2/s2b/fr_inputs.py --self-test [--repo-a REPO_A] [--repo-b REPO_B]
"""
import argparse, contextlib, hashlib, importlib.util, io, json, os, shutil, subprocess, sys, tarfile, tempfile
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
NODE_WORK = "/data/work/s2"
ARCHIVE_TREES = ("c1", "c2", "c3", "fr")                            # results/objective2/s2/<c>: never an --out
# S2B_PLAN.md section 2: (A2 label, the A1 start, cell kind) of host_R(A188), V+_R(A188), Cs D(A188), Cs D+V+(A188)
FR_LABELS = ("s2r_m30_hostA188", "s2r_m30_VA188", "s2r_m30_Cs188o0_novac", "s2r_m30_Cs188o0_vac")
META_FREE = ("campaign", "written", "time")                         # the only meta fields that may differ


def fr_cells(member, site, token):
    """[(label, A1 work id, kind)]: the FR labels on the cells of member, site and token (m30, 188, Cs for FR)."""
    w = [f"s2_{member}_host", f"s2_{member}_VA{site}", f"s2_{member}_{token}{site}p0_novac",
         f"s2_{member}_{token}{site}p0_vac"]
    return list(zip(FR_LABELS, w, ("host", "V", "D", "DV")))


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


def _under(rp, rd):
    """True iff the real path rp is the tree rd or lies under it: as strings, also casefolded (on a case-insensitive
    volume realpath keeps the typed case: '.../s2/C1' is '.../s2/c1'), and by identity, rp or one of its existing
    ancestors being the existing tree rd (os.path.samefile; a volume that folds case or Unicode normalisation)."""
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
        trees += [(os.path.join(r, "results", "objective2", "s2", c), f"results/objective2/s2/{c} of {r}")
                  for c in ARCHIVE_TREES]
    for d, what in trees:
        if _under(rp, os.path.realpath(d)):
            return f"--out lies under {what}"
    return None


def ranks_of(state, ranks):
    """(ranks, origin): the ranks of the state's a2_layout when a state file is given (a --ranks that differs is
    refused; 2x32 or no layout is refused: FR runs one copy), else --ranks (default 48)."""
    if state is None:
        return (48 if ranks is None else int(ranks)), "--ranks" if ranks is not None else "default"
    lay = (json.load(open(state)) or {}).get("a2_layout")
    if not isinstance(lay, str) or not lay.isdigit():
        raise SystemExit(f"the state's a2_layout is {lay!r}: FR runs one copy at the A2 ranks (not 2x32 or none)")
    if ranks is not None and int(ranks) != int(lay):
        raise SystemExit(f"--ranks {ranks} differs from the state's a2_layout {lay}: refused")
    return int(lay), "state a2_layout"


class Source:
    """The C1 source: structure files by their record path, records (blind), region, pair and smoke records."""

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

    def record(self, wid):
        p = os.path.join(self.dir, "records", f"{wid}.json") if self.kind == "archive" else self.L.record("c1", wid)
        rec = self.c46.load_record(p, blind=True)
        assert "E_mace_eV" not in json.dumps(rec), "MACE energy in a blinded record read"
        return rec

    def relaxed_bytes(self, wid):
        """The bytes of the relaxed structure named by the record (as scripts/50 relaxed_path)."""
        rel = (self.record(wid).get("files") or {}).get("relaxed") or f"cells/{wid}/relaxed.extxyz"
        if self.kind == "archive":
            return self.tar.extractfile(rel).read()
        return open(os.path.join(self.dir, rel), "rb").read()

    def json(self, rel):
        return json.load(open(os.path.join(self.dir, rel)))


def write(a):
    out = os.path.abspath(a.out)
    why = out_refusal(out, a.repo, a.c1, a.root if a.source == "node" else None)   # before anything is read or written
    if why:
        raise SystemExit(f"refused: {why} (D4; S2B_PLAN.md sections 0 and 9)")
    ranks, ranks_from = ranks_of(a.state, a.ranks)
    if os.path.isdir(out) and os.listdir(out):
        raise SystemExit("--out exists and is not empty")
    c46, q47 = load_repo(a.repo)
    from ase.io import read
    os.makedirs(out, exist_ok=True)
    src = Source(c46, a.source, c1=a.c1, root=a.root)
    m, j, T = a.member, int(a.site), a.token
    Ls = c46.SUBLATTICE[T]
    cells = fr_cells(m, j, T)
    hw, vw = cells[0][1], cells[1][1]
    rec = {"schema": "s2b-fr-inputs-1", "repo_scripts_sha256": {f: sha256(os.path.join(a.repo, "scripts", f)) for f in
                                                                 ("42_s2_builders.py", "46_s2_cells.py", "47_s2_qe.py")},
           "source": a.source, "member": m, "site": j, "token": T, "ranks": ranks, "ranks_from": ranks_from,
           "inputs": {}}
    tmp = tempfile.mkdtemp(prefix="fr_inputs_")
    try:
        # the builders on a temporary C1 tree holding the host and V+ files the jobs read (scripts/46 Layout, node)
        Lt = c46.Layout(kind="node", root=tmp)
        for w in (hw, vw):
            os.makedirs(Lt.cell_dir("c1", w), exist_ok=True)
            with open(Lt.cell_file("c1", w, "relaxed"), "wb") as fh:
                fh.write(src.relaxed_bytes(w))
            json.dump(src.record(w), open(Lt.record("c1", w), "w"))
        reg = c46.job_region({"action": "region", "root": tmp, "campaign": "c1", "member": m, "site": j})
        reg_c1 = src.json(os.path.join("regions", f"{m}_{Ls}{j}.json"))
        pr = c46.job_build_pair({"action": "build-pair", "root": tmp, "campaign": "c1", "member": m, "site": j, "token": T,
                                 "start": "p0", "partners": "relaxed"})
        pr_c1 = src.json(os.path.join("pairs", f"{m}_{T}{j}p0.json"))
        rec["region_equal"], rec["pair_equal"] = canon(reg) == canon(reg_c1), canon(pr) == canon(pr_c1)
        print(f"region {m}_{Ls}{j}: {'equal' if rec['region_equal'] else 'DIFFERS'} to c1/regions; pair {m}_{T}{j}p0: "
              f"{'equal' if rec['pair_equal'] else 'DIFFERS'} to c1/pairs")
        # the four part-1 inputs as scripts/50 a2_launch writes them
        sm = src.json("smoke.json").get("mapping") or {}
        nst = sm.get("nstep_first")
        if not sm.get("affine_slope_1") or not nst:
            raise SystemExit("no verified nstep mapping in c1/smoke.json (X-3)")
        for lab, a1, kind in cells:
            at = read(io.StringIO(src.relaxed_bytes(a1).decode()), format="extxyz")
            free = reg_c1["free"] if kind == "host" else src.record(a1)["free"]
            d = os.path.join(out, lab)
            q47.write_input(at, lab, d, kind="relax", free=free, nstep=nst, ranks=ranks, campaign="fr",
                            cell={"work_id": a1, "free_from": "region" if kind == "host" else "A1 record"})
            os.replace(os.path.join(d, f"{lab}.in"), os.path.join(d, f"{lab}.p1.in"))
            rec["inputs"][lab] = {"a1": a1, "in_sha256": sha256(os.path.join(d, f"{lab}.p1.in")),
                                  "meta_sha256": sha256(os.path.join(d, f"{lab}.meta.json"))}
            print(f"{lab}: {lab}.p1.in sha256 {rec['inputs'][lab]['in_sha256']}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    assert "mace" not in sys.modules
    json.dump(rec, open(os.path.join(out, "fr_inputs.json"), "w"), indent=1)
    return 0 if rec["region_equal"] and rec["pair_equal"] else 1


def compare(da, db):
    """0 iff both outputs rebuilt the C1 region and pair, every .p1.in is byte-identical and every .meta.json equal
    outside campaign and time; prints one line per file."""
    ra, rb = (json.load(open(os.path.join(d, "fr_inputs.json"))) for d in (da, db))
    bad = 0
    for nm, r in (("A", ra), ("B", rb)):
        ok = r.get("region_equal") is True and r.get("pair_equal") is True
        print(f"{'OK  ' if ok else 'DIFF'} {nm}: region and pair rebuilt equal to c1")
        bad += not ok
    labs = sorted(set(ra["inputs"]) | set(rb["inputs"]))
    if labs != sorted(FR_LABELS):
        print(f"DIFF labels {labs}"); bad += 1
    for lab in labs:
        pa, pb = (os.path.join(d, lab, f"{lab}.p1.in") for d in (da, db))
        same = os.path.exists(pa) and os.path.exists(pb) and open(pa, "rb").read() == open(pb, "rb").read()
        print(f"{'OK  ' if same else 'DIFF'} {lab}.p1.in"); bad += not same
        ma, mb = (json.load(open(os.path.join(d, lab, f"{lab}.meta.json"))) for d in (da, db))
        keys = meta_diff(ma, mb)
        print(f"{'OK  ' if not keys else 'DIFF'} {lab}.meta.json" + (f" ({', '.join(keys)})" if keys else "")
              + ("" if ma.get("campaign") == mb.get("campaign") else " (campaign differs: allowed)"))
        bad += bool(keys)
    print(f"compare: {len(labs)} FR inputs, {bad} differ")
    return 1 if bad else 0


def meta_diff(ma, mb):
    return sorted(k for k in set(ma) | set(mb) if k not in META_FREE and ma.get(k) != mb.get(k))


def _load50():
    s = importlib.util.spec_from_file_location("s50", os.path.join(REPO, "scripts", "50_s2_campaign.py"))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def self_test(repo_a, repo_b):
    """A C1-like tree on the public reference cells (ref233: host, region A128, V+_R(A128), the Cs128 p0 pair and its
    legs, by the scripts/46 mock pipeline of this checkout), written at two checkouts from the node source with the
    ranks of a state file (48; once with a 64-rank layout), and once from the archive source (a synthetic archive:
    scripts/50 archive of that tree), and compared; the inputs equal those scripts/50 Runner.a2_launch writes for the
    same FR jobs; a C1 region with one free index edited, and a C1 pair with one field edited, make write exit 1 with
    DIFFERS and the inequality in fr_inputs.json, and compare against a good output fail on the A-side identity line;
    other ranks, a changed input byte and a changed meta field other than campaign are reported; an --out under an
    archive tree (the trees c1, c2, c3 and fr and /data/work/s2 as literals; also through a link or a case variant),
    --c1 (also through a spelling the volume folds), the node work tree or the --root work tree, a --ranks other than
    the state's and a 2x32 layout are refused before anything is written."""
    c46, _ = load_repo(REPO)
    base = tempfile.mkdtemp(prefix="fr_inputs_selftest_")
    try:
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
        L = c46.Layout(kind="node", root=root)
        json.dump({"mapping": {"affine_slope_1": True, "nstep_first": 201}}, open(os.path.join(L.campaign_dir("c1"),
                                                                                                "smoke.json"), "w"))
        stf = os.path.join(base, "state.json")
        json.dump({"schema": "s2-state-1", "a2_layout": "48"}, open(stf, "w"))
        me = os.path.abspath(__file__)

        def run(*args):
            p = subprocess.run([sys.executable, me, "write", "--member", "ref233", "--site", "128"] + list(args),
                               capture_output=True, text=True)
            return p.returncode, p.stdout, p.stderr
        outs = []
        for tag, repo in (("A", repo_a), ("B", repo_b)):
            o = os.path.join(base, f"out_{tag}")
            rc, so, se = run("--repo", repo, "--source", "node", "--root", root, "--state", stf, "--out", o)
            print(f"write at {tag}: exit {rc}; " + "; ".join(so.strip().splitlines()[:1]))
            assert rc == 0, so + se
            outs.append(o)
        assert compare(*outs) == 0, "the inputs differ between the two checkouts"
        r = json.load(open(os.path.join(outs[1], "fr_inputs.json")))
        assert r["ranks"] == 48 and r["ranks_from"] == "state a2_layout", r
        # a state whose one-copy layout is not the default: its ranks reach fr_inputs.json and every meta record
        st64 = os.path.join(base, "state_64.json")
        json.dump({"schema": "s2-state-1", "a2_layout": "64"}, open(st64, "w"))
        o64 = os.path.join(base, "out_64")
        rc, so, se = run("--repo", REPO, "--source", "node", "--root", root, "--state", st64, "--out", o64)
        assert rc == 0, so + se
        r64 = json.load(open(os.path.join(o64, "fr_inputs.json")))
        assert r64["ranks"] == 64 and r64["ranks_from"] == "state a2_layout", r64
        assert all(json.load(open(os.path.join(o64, lab, f"{lab}.meta.json")))["ranks_expected"] == 64
                   for lab in FR_LABELS)
        assert ranks_of(st64, None) == ranks_of(st64, "64") == (64, "state a2_layout")
        # the archive source (analyst only) on a synthetic archive: scripts/50 archive of the C1-like tree
        s50 = _load50()
        stage = os.path.join(base, "stage"); os.makedirs(stage)
        os.symlink(os.path.join(root, "work", "s2"), os.path.join(stage, "work"))
        arch = os.path.join(base, "archive", "c1")
        ar = s50.archive(stage, "c1", arch)
        assert ar["structures"] > 0 and os.path.exists(os.path.join(arch, "structures.tar.gz")), ar
        oa = os.path.join(base, "out_archive")
        rc, so, se = run("--repo", REPO, "--source", "archive", "--c1", arch, "--state", stf, "--out", oa)
        assert rc == 0, so + se
        assert compare(outs[1], oa) == 0, "the archive source gives other inputs than the node source"
        assert json.load(open(os.path.join(oa, "fr_inputs.json")))["source"] == "archive"
        # the inputs scripts/50 Runner.a2_launch writes for the same FR jobs (pw.x launch stubbed)
        rn = s50.Runner("fr", root, s50.NodeBackend(root))
        rn._spawn_part = lambda *a_, **k_: None
        n_launch = 0
        for i, (lab, a1, kind) in enumerate(fr_cells("ref233", 128, "Cs")):
            j = {"id": "a2:" + lab, "label": lab, "a1": a1, "member": "ref233", "L": "A", "j": 128, "cell_kind": kind,
                 "order": i + 1, "ref": False}
            rn.a2_launch(j, rn.a2_rec(j), 48, "48")
            d = rn.L.a2_dir("fr", lab)
            assert open(os.path.join(d, f"{lab}.p1.in"), "rb").read() == \
                open(os.path.join(outs[1], lab, f"{lab}.p1.in"), "rb").read(), f"{lab}: a2_launch writes another input"
            assert not meta_diff(json.load(open(os.path.join(d, f"{lab}.meta.json"))),
                                 json.load(open(os.path.join(outs[1], lab, f"{lab}.meta.json")))), lab
            n_launch += 1
        # D4's identity can fail (S2B_PLAN.md section 9 step 3): on copies of the node tree, one free index of the C1
        # region of the FR host, and separately one field of the C1 pair, edited: write exits 1 printing DIFFERS,
        # fr_inputs.json records the inequality, and compare against a good output fails on the A-side identity line;
        # a rank count other than the good output's is named by compare (ranks_expected is no free meta field)
        def free_edited(r_):
            fr_ = [int(i) for i in r_["free"]]
            r_["free"] = sorted(fr_[:-1] + [min(set(range(max(fr_) + 2)) - set(fr_))])

        def pair_edited(r_):
            r_["region_id"] = f"{r_.get('region_id')}-edited"
        n_ident_fail = 0
        for tag, path_of, edit, key, line in (
                ("region", lambda L_: L_.region("c1", "ref233", "A", 128), free_edited, "region_equal",
                 "region ref233_A128: DIFFERS"),
                ("pair", lambda L_: L_.pair("c1", "ref233", "Cs", 128, 0), pair_edited, "pair_equal",
                 "pair ref233_Cs128p0: DIFFERS")):
            rt = os.path.join(base, f"node_{tag}_edited")
            shutil.copytree(root, rt, symlinks=True)
            pe = path_of(c46.Layout(kind="node", root=rt))
            rx = json.load(open(pe)); edit(rx); json.dump(rx, open(pe, "w"), indent=1)
            ox = os.path.join(base, f"out_{tag}_edited")
            rc, so, se = run("--repo", REPO, "--source", "node", "--root", rt, "--state", stf, "--out", ox)
            rr = json.load(open(os.path.join(ox, "fr_inputs.json")))
            other = "pair_equal" if key == "region_equal" else "region_equal"
            assert rc == 1 and line in so and rr[key] is False and rr[other] is True and len(rr["inputs"]) == 4, \
                (tag, rc, so, se)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                cr = compare(ox, outs[0])
            assert cr == 1 and "DIFF A: region and pair rebuilt equal to c1" in buf.getvalue(), (tag, buf.getvalue())
            buf = io.StringIO()                         # FR_IMPL_DECISIONS_R5 R5-6 (N4_09): the B side as well
            with contextlib.redirect_stdout(buf):
                cr = compare(outs[0], ox)
            assert cr == 1 and "DIFF B: region and pair rebuilt equal to c1" in buf.getvalue(), (tag, buf.getvalue())
            n_ident_fail += 1
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cr = compare(outs[0], o64)
        assert cr == 1 and "ranks_expected" in buf.getvalue(), buf.getvalue()
        # the comparison reports a changed meta field and a changed input byte
        lab = FR_LABELS[2]
        mp = os.path.join(outs[1], lab, f"{lab}.meta.json")
        mt = json.load(open(mp)); mt["campaign"] = "c4"; json.dump(mt, open(mp, "w"))
        assert compare(*outs) == 0, "a meta file differing in campaign only was reported"
        mt["electrons"] = {"n_el": -1}; json.dump(mt, open(mp, "w"))
        assert compare(*outs) == 1, "a changed meta field was not reported"
        mt["electrons"] = json.load(open(os.path.join(outs[0], lab, f"{lab}.meta.json")))["electrons"]
        json.dump(mt, open(mp, "w"))
        ip = os.path.join(outs[1], FR_LABELS[0], f"{FR_LABELS[0]}.p1.in")
        t = open(ip).read(); open(ip, "w").write(t.replace("nstep", "nstep ", 1))
        assert compare(*outs) == 1, "a changed input byte was not reported"
        for d in (outs[0],):
            r = json.load(open(os.path.join(d, "fr_inputs.json")))
            assert r["region_equal"] and r["pair_equal"] and len(r["inputs"]) == 4, r
        # refusals before anything is written: --out under an archive tree (also through a link, a dangling link to one
        # not made yet, or a case variant), --c1, the node work tree and the --root work tree; a --ranks other than the
        # state's; a 2x32 layout
        trees = ("c1", "c2", "c3", "fr")                # the literals of F9 (a changed constant is not followed)
        assert ARCHIVE_TREES == trees and NODE_WORK == "/data/work/s2", (ARCHIVE_TREES, NODE_WORK)
        fake = os.path.join(base, "fakerepo")
        for c in trees:
            os.makedirs(os.path.join(fake, "results", "objective2", "s2", c))
        os.symlink(os.path.join(fake, "results", "objective2", "s2", "fr"), os.path.join(base, "link_fr"))
        fake2 = os.path.join(base, "fakerepo2")                         # results/objective2/s2 without its trees
        os.makedirs(os.path.join(fake2, "results", "objective2", "s2"))
        os.symlink(os.path.join(fake2, "results", "objective2", "s2", "fr"), os.path.join(base, "link_fr_dangling"))
        st2 = os.path.join(base, "state_2x32.json"); json.dump({"a2_layout": "2x32"}, open(st2, "w"))
        rows = [(["--repo", fake, "--source", "node", "--root", root, "--out",
                  os.path.join(fake, "results", "objective2", "s2", c, "x")], "results/objective2/s2/" + c)
                for c in trees]
        rows += [(["--repo", fake, "--source", "node", "--root", root, "--out",
                   os.path.join(fake, "results/objective2/s2/c3/x")], "results/objective2/s2/c3")]    # a literal path
        rows += [(["--repo", fake, "--source", "node", "--root", root, "--out", os.path.join(base, "link_fr", "x")],
                  "results/objective2/s2/fr"),
                 (["--repo", fake2, "--source", "node", "--root", root, "--out",
                   os.path.join(base, "link_fr_dangling", "x")], "results/objective2/s2/fr"),
                 (["--repo", fake, "--source", "node", "--root", root, "--out",
                   os.path.join(fake, "results", "objective2", "s2", "C1", "x")], "results/objective2/s2/c1"),
                 (["--repo", fake, "--source", "node", "--root", root, "--out",
                   os.path.join(fake, "results", "objective2", "s2", "Fr", "x")], "results/objective2/s2/fr"),
                 (["--repo", fake, "--source", "node", "--root", root, "--out", os.path.join(root, "work", "s2", "fr", "d4")],
                  "the work tree of --root"),
                 (["--repo", REPO, "--source", "archive", "--c1", arch, "--out", os.path.join(arch, "x")], "--c1"),
                 (["--repo", REPO, "--source", "node", "--root", root, "--state", stf, "--ranks", "64", "--out",
                   os.path.join(base, "o_r")], "differs from the state"),
                 (["--repo", REPO, "--source", "node", "--root", root, "--state", st2, "--out", os.path.join(base, "o_l")],
                  "2x32")]
        for args, word in rows:
            o = args[args.index("--out") + 1]
            rc, so, se = run(*args)
            assert rc != 0 and word in se and not os.path.exists(o), (args, rc, se)
        assert not os.path.lexists(os.path.join(fake2, "results", "objective2", "s2", "fr"))     # nothing made
        for c in trees:                                  # this checkout's archive trees: the rule alone (nothing made)
            assert out_refusal(os.path.join(REPO, "results", "objective2", "s2", c, "x"), fake) is not None, c
            assert out_refusal(os.path.join(REPO, "results", "objective2", "s2", c.upper(), "x"), fake) is not None, c
        # the node work tree by its literal path, by the rule alone (a write under it is never tried here)
        assert out_refusal("/data/work/s2/fr/d4", fake) == "--out lies under /data/work/s2" and \
            out_refusal("/data/work/s2", fake) and out_refusal(os.path.join(base, "out_ok"), fake) is None
        assert out_refusal(os.path.join(root, "work", "s2", "fr"), fake, root=root) and \
            out_refusal(os.path.join(root, "work", "s2", "fr"), fake) is None        # --root counts for the node source
        # identity: a spelling that neither realpath nor casefold equates (Unicode normalisation), on a volume that
        # folds it to the same directory (APFS), is refused as --c1; on a volume that does not, it is another directory
        nfc, nfd = "c" + "af\u00e9", unicodedata.normalize("NFD", "c" + "af\u00e9")
        os.makedirs(os.path.join(base, nfc, "c1"))
        alias = os.path.join(base, nfd, "c1", "x")
        n_ident = 0
        if os.path.isdir(os.path.dirname(alias)):
            assert out_refusal(alias, fake, os.path.join(base, nfc, "c1")) == "--out lies under --c1", alias
            n_ident = 1
        else:
            assert out_refusal(alias, fake, os.path.join(base, nfc, "c1")) is None
        assert ranks_of(None, None) == (48, "default") and ranks_of(stf, "48") == (48, "state a2_layout")
        assert "mace" not in sys.modules
        print(f"fr_inputs self-test passed: the region, pair and four part-1 inputs rebuilt and written at {repo_a} "
              f"and {repo_b} are identical, and so are those from the archive source on a synthetic archive "
              f"({ar['structures']} structures); {n_launch} inputs equal scripts/50 Runner.a2_launch's; ranks from the "
              f"state's a2_layout (48, and 64 in fr_inputs.json and every meta record); {n_ident_fail} edited C1 "
              f"records (a region free index, a pair field) give exit 1, DIFFERS and a failing A-side identity line; "
              f"other ranks are named (ranks_expected); a campaign-only meta difference is allowed, a meta field "
              f"and an input byte are reported; the refused trees pinned as literals; {len(rows)} refusals (an --out "
              f"under an archive tree, a link to one, a case variant of one, the --root work tree or --c1; another "
              f"--ranks; 2x32) with nothing written; identity refusals of an aliased spelling: {n_ident}")
        return 0
    finally:
        shutil.rmtree(base, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description="FR input identity and dry run (S2B_PLAN.md section 9 step 3; D4). The "
                                             "archive source opens the C1 structure archive and records: analyst only.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--repo-a", default=REPO, help="self-test: the first checkout (e.g. one at 8bff03e)")
    ap.add_argument("--repo-b", default=REPO, help="self-test: the second checkout (the S2b commit)")
    sub = ap.add_subparsers(dest="cmd")
    w = sub.add_parser("write", description="Rebuild the FR region and pair and write the four part-1 inputs. --source "
                                            "archive opens the C1 structure archive and records: analyst only.")
    w.add_argument("--repo", default=REPO)
    w.add_argument("--source", required=True, choices=["archive", "node"],
                   help="node: the node's C1 tree (D4); archive: the public C1 archive, ANALYST ONLY (it opens "
                        "c1/structures.tar.gz and c1/records, blinded to every other agent)")
    w.add_argument("--c1", default=os.path.join(REPO, "results", "objective2", "s2", "c1"))
    w.add_argument("--root", default="/data"); w.add_argument("--out", required=True)
    w.add_argument("--member", default="m30"); w.add_argument("--site", default="188"); w.add_argument("--token", default="Cs")
    w.add_argument("--state", default=None, help="the node's state.json: the ranks are those of its a2_layout")
    w.add_argument("--ranks", default=None, help="the A2 ranks (one copy); refused if it differs from --state's a2_layout; "
                                                  "default 48 without --state")
    c = sub.add_parser("compare"); c.add_argument("a"); c.add_argument("b")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test(os.path.abspath(a.repo_a), os.path.abspath(a.repo_b))
    if a.cmd == "write":
        a.repo = os.path.abspath(a.repo)
        return write(a)
    if a.cmd == "compare":
        return compare(a.a, a.b)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

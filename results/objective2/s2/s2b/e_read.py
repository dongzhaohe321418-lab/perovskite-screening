#!/usr/bin/env python
"""The readers of E, the one evaluation of S2b (results/objective2/s2/S2B_PLAN.md section 7, "Raw outputs",
"Imports", "MACE records" and "Integrity checks", with amendment 2026-11-12a and E_DECISIONS_R1;
E_IMPLEMENTATION_SPEC sections 2, 3 and 5).

  import_8bff03e  scripts/46-50 and the four data files of scripts/48 from a git archive of 8bff03e in a read-only
                  temporary tree; m48, g49 = m48.g49, q47 = g49.dep('q47') and c46 = g49.dep('c46'), with the
                  blob, directory, ROOT and single-READS assertions (INT-IMPORT; RF-17, RF-19, RF-21).
  ELayout         the archive paths of the campaigns c1, c2, fr (root) and c3b, c4b (private root) and the c3 lock
                  (RF-2). No c3 path and no *.inputs.json path can be built.
  ReadsAudit      the scripts/47 READS counters before and after every parse_relax and parse_sp call, and between
                  calls (S2B:612-614; INT-READS).
  read_relaxation one A2 relaxation: the listed record leaves through EGuarded, then parse_relax(read='full') of a
                  complete one with the integrity checks INT-PARTS ... INT-CELL, the cross-checks XC-ENDRULE,
                  XC-PARTS and XC-MIC, and the derived values (F, curves, restarts, Delta F_tail, path work by shell
                  with lattice-image centres). OP-14, RF-4, RF-13, RF-14, RF-20, RF-23; amendment items 5, 6.
  sp_full         a C1 single point through C1Access (e_guard.py): sp_status, then parse_sp(read='full') with the
                  free set of its base record. There is no force-only reader (OP-1).
  build_c1_table  the s2-evaltable-1-shaped pilot host tables of block 3 (and the Pb136 additions of block 5) and the
                  MACE ledger: every E_mace_eV leaf at any depth of the 155 (and 5) records; kept minima mapped
                  through distinct.json work_ids (RF-18); E_mace[label] = relax.E_mace_eV (RF-24).
  member_bytes    one member of a structures tar, read in memory and logged (never extractall).

Blinding. Every C2, fr, c3b and c4b record and gate file is read through e_guard.EGuarded by listed leaf; C1 MACE
records only through C1Access (blocks 3-5; Pb136 in block 5 of a hinge read); every open is logged and refused by
e_guard.OpenAudit. This module never decides which block runs; it reads what the caller asks and asserts the READS
deltas. No energy is printed here. No calculator is loaded (ase.io only; every Atoms built has calc None).

    (imported by e_eval.py and e_selftest.py; self-tests: e_selftest.py group B)
"""
import collections, gc, hashlib, importlib.util, io, json, os, re, shutil, stat, subprocess, sys, tarfile, tempfile
import types

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
S2 = os.path.normpath(os.path.join(HERE, ".."))
REPO = os.path.normpath(os.path.join(S2, "..", "..", ".."))


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

PIN_8BFF03E = "8bff03ede8b9d0f380b6ef373b239e7deb87817f"          # S2B:564 (the C2 campaign commit)
IMPORT_DATA = ("results/objective2/dopant_shell/wp2c/wp2cde_dft.json",
               "results/objective2/dopant_shell/wp1_production/shell_m30.json",
               "results/objective2/dopant_shell/wp1_production/shell_m05.json",
               "results/objective2/dopant_shell/wp1_production/v2prod_structures.tar.gz")   # spec section 2
BLOB_PINS = {"scripts/48_s2_analysis.py": "4cbd82f5", "scripts/49_s2_gates.py": "e074d8a2",
             "scripts/46_s2_cells.py": "92fbaab6", "scripts/47_s2_qe.py": "84c8e8ee",
             "scripts/50_s2_campaign.py": "8c04d65f"}              # map 1 section A
K_CAP = 200                                                        # S2B:537
FINALPOS_TOL_A, CELL_TOL_A, MIC_TOL_A = 1e-6, 1e-9, 1e-9           # S2B:609; spec 5.1 items 4 and 6
TAIL_BACK = 36                                                     # Delta F_tail at k_last - 36 (S2B:643; OP-13)
IMAGE_RANGE = range(-2, 3)                                         # lattice images n in {-2..2}^3 (OP-15)
SP_DELTA = {"F": 1, "TS": 1, "forces": 1, "fermi": 1, "mag_total": 1, "mag_abs": 1}   # spec 5.2


# ---------------------------------------------------------------- the 8bff03e import (spec section 2)
class GitRunner:
    """git -C <repo> <args>; returns stdout bytes (injectable: the self-test replaces it)."""

    def __init__(self, repo):
        self.repo = repo

    def __call__(self, *args, stdin=None):
        r = subprocess.run(["git", "-C", self.repo, *args], input=stdin, capture_output=True)
        if r.returncode != 0:
            raise EError(f"git {args[0]} failed (exit {r.returncode})")
        return r.stdout


class Extraction:
    """The 8bff03e modules and their read-only temporary tree."""

    def __init__(self, tmp, m48, g49, q47, c46, blobs):
        self.tmp, self.m48, self.g49, self.q47, self.c46, self.blobs = tmp, m48, g49, q47, c46, blobs

    def cleanup(self):
        """RF-21: restore u+w on the directories, then remove; a failure is returned, never raised."""
        return remove_tree(self.tmp)


def remove_tree(d):
    """RF-21: u+w restored on the directories, then removed; a failure is returned, never raised. Fix round 2: the
    OpenAudit hook is paused for the removal. shutil.rmtree opens each child by its bare name with dir_fd, which the
    'open' audit event does not carry, so the hook would resolve a child 'c2' or 'fr' against the working directory
    (a false refusal when E or the self-test runs from a checkout's S2 directory). rmtree reads no file's bytes."""
    prev = getattr(eg._TL, "busy", False)
    eg._TL.busy = True
    try:
        if os.path.isdir(d):
            for dp, dns, fns in os.walk(d):
                os.chmod(dp, stat.S_IMODE(os.stat(dp).st_mode) | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRUSR)
            shutil.rmtree(d)
        return None
    except OSError as e:
        return f"{d}: not removed ({type(e).__name__})"
    finally:
        eg._TL.busy = prev


def git_blob_id(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def modules_47():
    """RF-17: the loaded module objects whose __file__ ends with 47_s2_qe.py (gc scan)."""
    return [o for o in gc.get_objects() if isinstance(o, types.ModuleType) and
            str(getattr(o, "__file__", None) or "").endswith("47_s2_qe.py")]


def _load_file(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def import_8bff03e(repo, *, git=None, prefix="e_8bff03e_", tmp_parent=None):
    """Spec section 2 with RF-17, RF-19, RF-21. Every failed assertion is INT-IMPORT; the tree is removed on a
    failure. The caller removes it with Extraction.cleanup() after the final audit."""
    if not (sys.version_info >= (3, 12) and hasattr(tarfile, "data_filter")):
        raise EIntegrity("INT-IMPORT", "python", "version >= 3.12 with tarfile.data_filter")
    git = git or GitRunner(repo)
    tmp = tempfile.mkdtemp(prefix=prefix, dir=tmp_parent)
    try:
        tarp = os.path.join(tmp, "x.tar")
        git("archive", "-o", tarp, PIN_8BFF03E, "scripts", *IMPORT_DATA)
        with tarfile.open(tarp) as t:
            t.extractall(tmp, filter="data")
        os.remove(tarp)
        listing = git("ls-tree", "-r", PIN_8BFF03E, "--", "scripts", *IMPORT_DATA).decode()
        blobs = {}
        for line in listing.splitlines():
            meta, path = line.split("\t", 1)
            mode, typ, sha = meta.split()
            if typ == "blob":
                blobs[path] = sha
        got = git("cat-file", "--batch", stdin="".join(f"{s}\n" for s in blobs.values()).encode())
        content, pos = {}, 0
        for path, sha in blobs.items():                    # '<sha> blob <size>\n<content>\n', in order
            nl = got.index(b"\n", pos)
            h, typ, size = got[pos:nl].decode().split()
            if h != sha or typ != "blob":
                raise EIntegrity("INT-IMPORT", path, "git cat-file")
            content[path] = got[nl + 1:nl + 1 + int(size)]
            pos = nl + 1 + int(size) + 1
        on_disk = set()
        for dp, dns, fns in os.walk(tmp):
            for fn in fns:
                on_disk.add(os.path.relpath(os.path.join(dp, fn), tmp).replace(os.sep, "/"))
        if on_disk != set(blobs) or not set(IMPORT_DATA) <= set(blobs):
            raise EIntegrity("INT-IMPORT", "8bff03e", "extracted file set")
        for path in sorted(blobs):
            with open(os.path.join(tmp, path), "rb") as fh:
                b = fh.read()
            if hashlib.sha256(b).digest() != hashlib.sha256(content[path]).digest() or git_blob_id(b) != blobs[path]:
                raise EIntegrity("INT-IMPORT", path, "sha256 against git cat-file blob 8bff03e")
        for path, pin in BLOB_PINS.items():
            if not blobs.get(path, "").startswith(pin):
                raise EIntegrity("INT-IMPORT", path, "pinned blob")
        for dp, dns, fns in os.walk(tmp, topdown=False):        # chmod -R a-w
            for fn in fns:
                p = os.path.join(dp, fn)
                os.chmod(p, stat.S_IMODE(os.stat(p).st_mode) & ~0o222)
            os.chmod(dp, stat.S_IMODE(os.stat(dp).st_mode) & ~0o222)
        if modules_47():                                       # RF-17: no 47 instance before the import
            raise EIntegrity("INT-IMPORT", "scripts/47_s2_qe.py", "one READS counter")
        m48 = _load_file("e_a48_8bff03e", os.path.join(tmp, "scripts", "48_s2_analysis.py"))
        g49 = m48.g49
        q47, c46 = g49.dep("q47"), g49.dep("c46")
        sd = os.path.join(tmp, "scripts")
        for name, m in (("g49", g49), ("q47", q47), ("c46", c46), ("m48", m48)):
            if os.path.dirname(os.path.abspath(m.__file__)) != sd:
                raise EIntegrity("INT-IMPORT", name, "__file__ outside the extraction")
        if os.path.abspath(m48.ROOT) != os.path.abspath(tmp):
            raise EIntegrity("INT-IMPORT", "m48", "ROOT")
        m47 = modules_47()
        if len(m47) != 1 or m47[0] is not q47 or g49.dep("q47") is not q47:
            raise EIntegrity("INT-IMPORT", "scripts/47_s2_qe.py", "one READS counter")
        return Extraction(tmp, m48, g49, q47, c46, blobs)
    except BaseException:
        remove_tree(tmp)
        raise


def assert_one_47(q47):
    """RF-17 at any later point: exactly one loaded 47 module object, and it is q47."""
    m = modules_47()
    if len(m) != 1 or m[0] is not q47:
        raise EIntegrity("INT-IMPORT", "scripts/47_s2_qe.py", "one READS counter")
    return True


def load_cd():
    """S2/c2_diagnostic/check5_diag.py, unchanged (CALC_ENGINES, assert_no_calculator, mic)."""
    return eg._load_shared("_s2b_e_check5_diag", os.path.join(S2, "c2_diagnostic", "check5_diag.py"))


# ---------------------------------------------------------------- ELayout and the c3 lock (spec section 3; RF-2)
class ELayout:
    """Archive paths of E. root holds c1, c2 and fr; private_root holds c3b and c4b only (spec section 3)."""

    def __init__(self, root, private_root=None):
        self.root = os.path.abspath(root)
        self.private_root = os.path.abspath(private_root) if private_root else None

    def cdir(self, c, *sub):
        if c not in eg.CAMPAIGNS:
            raise EError(f"campaign {c!r} is not one of {eg.CAMPAIGNS} (no c3 path is built; S2B:569)")
        if c in eg.PRIVATE_CAMPAIGNS and self.private_root is None:
            raise EError(f"{c} needs --private-root (spec section 1)")
        base = self.root if c in eg.PUBLIC_CAMPAIGNS else self.private_root
        for s in sub:
            if not isinstance(s, str) or s in ("", ".", "..") or "/" in s or os.sep in s:
                raise EError(f"path segment {s!r}")
        return os.path.join(base, c, *sub)

    def file(self, c, relpath):
        segs = relpath.split("/")
        if relpath.startswith("/") or any(s in ("", ".", "..") for s in segs):
            raise EError(f"relative path {relpath!r}")
        if relpath.endswith(".inputs.json"):
            raise Blinded(f"{c}/{relpath}: inputs files are never opened (S2B:545)")
        return self.cdir(c, *segs)

    def record(self, c, wid):
        if c not in ("c1", "c3b"):
            raise EError(f"{c} has no records/ directory")
        return self.cdir(c, "records", f"{wid}.json")

    def raw(self, c, name):
        return self.file(c, f"raw/{name}")

    def a2_record(self, c, lab):
        return self.raw(c, f"{lab}.a2.json")

    def a2_parts(self, c, lab):
        """The part outputs <lab>.p<n>.out.gz in order; the numbers must be exactly 1..N (INT-PARTS)."""
        d = self.cdir(c, "raw")
        rx = re.compile(re.escape(lab) + r"\.p([1-9]\d*)\.out\.gz")
        got = sorted((int(m.group(1)), f) for f in (os.listdir(d) if os.path.isdir(d) else [])
                     for m in [rx.fullmatch(f)] if m)
        if [n for n, _ in got] != list(range(1, len(got) + 1)) or not got:
            raise EIntegrity("INT-PARTS", f"{c}/raw/{lab}.p<n>.out.gz", "part numbers 1..N")
        return [os.path.join(d, f) for _, f in got]

    def structures(self, c):
        return self.cdir(c, "structures.tar.gz")

    def region(self, member, L, j):
        return self.cdir("c1", "regions", f"{member}_{L}{int(j)}.json")

    def pair(self, member, T, j, n):
        return self.cdir("c1", "pairs", f"{member}_{T}{int(j)}p{int(n)}.json")

    def distinct(self, member, T, j, leg):
        return self.cdir("c1", "pairs", f"{member}_{T}{int(j)}_{leg}.distinct.json")

    def gate(self, c, name):
        return self.cdir(c, "gates", f"{name}.json")

    def applied(self, c, gid, suffix):
        if suffix not in (".json", ".gate.json"):
            raise EError(f"applied-gate suffix {suffix!r} (no .inputs.json path; S2B:545)")
        return self.cdir(c, "gates_applied", eg.applied_id(gid) + suffix)

    def campaign(self, c):
        return self.cdir(c, "campaign.json")

    def state_end(self, c):
        return self.cdir(c, "state_end.json")

    def smoke(self):
        return self.cdir("c1", "smoke.json")

    def upf_check(self):
        return self.cdir("c1", "upf_check.json")

    def throughput(self):
        return self.cdir("c1", "throughput.json")

    def roots(self):
        return [r for r in (self.root, self.private_root) if r]

    def c3_entries(self):
        """The refused entries of every root (RF-2)."""
        return {r: c3_entries(r) for r in self.roots() if c3_entries(r)}


def c3_entries(d):
    """RF-2: an entry named (any case) c3, c3.tar, c3.tar.gz, c3.tgz or c3_notrun, or a directory or a symlink (a
    dangling one included) whose name matches c3([._-].*)?. A regular file such as C3_OPERATIONS.md is allowed."""
    bad = []
    for n in sorted(os.listdir(d)):
        p = os.path.join(d, n)
        if n.lower() in eg.C3_NAMES or (eg.C3_DIR_RE.fullmatch(n) and (os.path.islink(p) or os.path.isdir(p))):
            bad.append(n)
    return bad


def assert_no_c3(L, *, at="start"):
    """Before any read (exit 2: EError) and at exit (INT-ROOT)."""
    bad = L.c3_entries()
    if bad:
        if at == "start":
            raise EError(f"a root holds a c3 entry: {bad} (S2B:569; RF-2)")
        r = sorted(bad)[0]
        raise EIntegrity("INT-ROOT", bad[r][0], "c3 entry")             # the entry name, not the root's path
    return True


# ---------------------------------------------------------------- READS (spec 5.2; S2B:612-614)
class ReadsAudit:
    """READS of the one scripts/47 object, recorded around every parse call and checked between calls."""

    def __init__(self, q47, mapping):
        self.q = q47
        if mapping is None or mapping.get("restart_repeats_last", None) is not False:
            raise EIntegrity("INT-READS", "c1/smoke.json", "mapping.restart_repeats_last")   # the deltas need False
        self.after = collections.Counter(q47.READS)
        self.labels = {"a2": {}, "sp": {}}               # label -> block of the read
        self.totals = collections.Counter()

    def _between(self, where):
        if collections.Counter(self.q.READS) != self.after:
            raise EIntegrity("INT-READS", where, "READS changed between calls")

    def _change(self, before, after):
        return {k: after.get(k, 0) - before.get(k, 0) for k in set(before) | set(after)}

    def _check(self, where, d, want):
        for k in set(d) | set(want):
            if d.get(k, 0) != want.get(k, 0):
                raise EIntegrity("INT-READS", where, f"READS[{k}]")
        for k, v in d.items():
            if v:
                self.totals[k] += v

    def parse_relax(self, lab, parts, *, block=None, **kw):
        q = self.q
        self._between(lab)
        before = collections.Counter(q.READS)
        try:
            rel = q.parse_relax(parts, **kw)
        except (q.S2Error, q.Refused) as e:                  # RF-20: stage and exception type only
            self.after = collections.Counter(q.READS)
            raise EIntegrity("INT-PARSE", lab, f"stage parse_relax {type(e).__name__}") from None
        self.after = collections.Counter(q.READS)
        want = {}
        if rel.get("usable") is True and kw.get("read") == "full":
            n = int(rel["n_config"])
            want = {"ase": sum(1 for p in rel["parts"] if (p.get("n_config") or 0) > 0), "F": n, "forces": n,
                    "positions": n}
        self._check(lab, self._change(before, self.after), {k: v for k, v in want.items() if v})
        self.labels["a2"][lab] = block
        return rel

    def parse_sp(self, label, path, *, free, block=None):
        q = self.q
        self._between(label)
        before = collections.Counter(q.READS)
        try:
            r = q.parse_sp(path, read="full", free=free)
        except (q.S2Error, q.Refused) as e:
            self.after = collections.Counter(q.READS)
            raise EIntegrity("INT-SP", label, f"stage parse_sp {type(e).__name__}") from None
        self.after = collections.Counter(q.READS)
        self._check(label, self._change(before, self.after), SP_DELTA)
        self.labels["sp"][label] = block
        return r

    def check_labels(self, a2_allowed, sp_allowed):
        """At exit: every A2 and SP label whose F was read belongs to the blocks run (spec 5.2)."""
        self._between("exit")
        for lab in self.labels["a2"]:
            if lab not in a2_allowed:
                raise EIntegrity("INT-READS", lab, "A2 label outside the blocks run")
        for lab in self.labels["sp"]:
            if lab not in sp_allowed:
                raise EIntegrity("INT-READS", lab, "SP label outside the blocks run")
        return True


# ---------------------------------------------------------------- labels (restated grammar; OP-26, amendment 7)
A2_RE = re.compile(r"s2r_(?P<h>m\d\d)_(?:host(?P<hL>[BAX])(?P<hj>\d+)|V(?P<vL>[BAX])(?P<vj>\d+)"
                   r"|(?P<tok>Sr|Ca|Cl|Cs|GA)(?P<j>\d+)o0_(?P<leg>novac|vac))")    # scripts/49 _A2_RE


def a2_cell(lab):
    m = A2_RE.fullmatch(lab)
    if not m:
        raise EError(f"not an A2 label: {lab}")
    g = m.groupdict()
    if g["hL"]:
        return {"pilot": g["h"], "L": g["hL"], "site": int(g["hj"]), "kind": "host", "token": None, "leg": None}
    if g["vL"]:
        return {"pilot": g["h"], "L": g["vL"], "site": int(g["vj"]), "kind": "V", "token": None, "leg": "vac"}
    tok = g["tok"]
    return {"pilot": g["h"], "L": eg.SUBLATTICE[tok], "site": int(g["j"]), "kind": "D" if g["leg"] == "novac" else "DV",
            "token": tok, "leg": g["leg"]}


def a1_start(lab):
    """The A1 start work id of an A2 label (scripts/49 a1_start_of; S2B section 11)."""
    c = a2_cell(lab)
    if c["kind"] == "host":
        return f"s2_{c['pilot']}_host"
    if c["kind"] == "V":
        return f"s2_{c['pilot']}_V{c['L']}{c['site']}"
    return f"s2_{c['pilot']}_{c['token']}{c['site']}p0_{c['leg']}"


def assert_grammar(g49, labels):
    """INT-IMPORT: the restated A2 grammar equals scripts/49 at 8bff03e on every label E reads."""
    for lab in labels:
        ref = g49.a2_cell(lab)
        if a2_cell(lab) != ref or a1_start(lab) != g49.a1_start_of(lab):
            raise EIntegrity("INT-IMPORT", "8bff03e", f"a2_cell {lab}")
    return True


# ---------------------------------------------------------------- files, tar members, geometry
def read_json(path):
    """A plain public JSON file (C1 regions, pairs, smoke, upf_check, gates), opened under OpenAudit."""
    with open(path, "rb") as fh:
        return json.loads(fh.read())


def member_bytes(audit, tar_path, name, *, check="INT-STRUCT"):
    """Spec 5.5: tarfile.open(...).extractfile(getmember(name)).read(), logged as (tar, member); no extractall."""
    with tarfile.open(tar_path) as t:
        audit.log_member(tar_path, name)
        try:
            m = t.getmember(name)
        except KeyError:
            raise EIntegrity(check, f"{os.path.basename(tar_path)}:{name}", "member absent") from None
        return t.extractfile(m).read()


def atoms_from_bytes(b):
    """An extxyz member as Atoms with no calculator and no constraint (as part_d_read.atoms_from_bytes)."""
    from ase.io import read
    at = read(io.StringIO(b.decode()), format="extxyz")
    at.calc = None                                         # INT-CALC: every Atoms E builds has calc None
    at.set_constraint()
    return at


def image_centres(centres, cell):
    """OP-15: c + n.A for every centre c and n in {-2..2}^3 (A: the rows of the cell)."""
    A = np.asarray(cell, float)
    out = []
    for c in centres:
        c = np.asarray(c, float)
        for n0 in IMAGE_RANGE:
            for n1 in IMAGE_RANGE:
                for n2 in IMAGE_RANGE:
                    out.append((c + n0 * A[0] + n1 * A[1] + n2 * A[2]).tolist())
    return out


def mic_residual(cd, X0, centres, images, cell):
    """XC-MIC: max over atoms of |min over image centres |x - c'| - min_c |cd.mic(x - c, cell)||, in A."""
    X0 = np.asarray(X0, float)
    d_img = np.min(np.linalg.norm(X0[:, None, :] - np.asarray(images, float)[None, :, :], axis=2), axis=1)
    d_mic = np.min(np.stack([np.linalg.norm(cd.mic(X0 - np.asarray(c, float), cell), axis=1) for c in centres]),
                   axis=0)
    return float(np.abs(d_img - d_mic).max())


# ---------------------------------------------------------------- context
class ReadCtx:
    """What the readers need: L (ELayout), audit (OpenAudit), the 8bff03e extraction, checks, cd (check5_diag),
    mapping (c1/smoke.json) and md5_extra (c1/upf_check.json), and the ReadsAudit."""

    def __init__(self, L, audit, ex, *, checks=None):
        self.L, self.audit, self.ex = L, audit, ex
        self.q47, self.c46, self.m48, self.g49 = ex.q47, ex.c46, ex.m48, ex.g49
        self.checks = checks or eg.Checks()
        self.cd = load_cd()
        self.mapping = read_json(L.smoke())["mapping"]
        try:
            self.md5_extra = self.q47.upf_md5_extra(read_json(L.upf_check()))
        except self.q47.S2Error:
            raise EIntegrity("INT-STRUCT", "c1/upf_check.json", "passed") from None
        self.reads = ReadsAudit(self.q47, self.mapping)


def region_centres(ctx, lab):
    """[v, site] of c1/regions/<pilot>_<L><site>.json for an A2 label (spec 5.1 item 6)."""
    c = a2_cell(lab)
    r = read_json(ctx.L.region(c["pilot"], c["L"], c["site"]))
    cen = r.get("centres") or {}
    if not all(isinstance(cen.get(k), list) and len(cen[k]) == 3 for k in ("v", "site")):
        raise EIntegrity("INT-STRUCT", f"c1/regions/{c['pilot']}_{c['L']}{c['site']}.json", "centres")
    return [cen["v"], cen["site"]]


# ---------------------------------------------------------------- read_relaxation (spec 5.1)
def read_relaxation(ctx, c, lab, *, mode, kind, tail_ks=None, plateau=False, block=None):
    """One A2 relaxation of campaign c (spec 5.1 with OP-14, RF-4, RF-13, RF-14, RF-20, RF-23). Integrity failures
    raise EIntegrity; cross-checks are returned in 'xc' and never raise. tail_ks: the Delta F_tail ks (default
    k_last - 36, 'not formed (k_last < 36)' below it); plateau: also return F(200) - F(180) from the parse when
    k_last = 200 (block 2, S2B section 7 FR block)."""
    L, chk, q = ctx.L, ctx.checks, ctx.q47
    where = f"{c}/raw/{lab}.a2.json"
    g = eg.eg_load(L, c, f"raw/{lab}.a2.json", mode=mode, kind=kind, audit=ctx.audit)
    out = {"label": lab, "campaign": c, "mode": mode, "kind": kind, "parsed": False}
    if g is FILE_ABSENT:
        out.update(record=FILE_ABSENT, status=FILE_ABSENT)
        return out
    lv = {p: g.get(p) for p in g.listed()}
    out["leaves"] = lv
    st = lv.get("status", ABSENT)
    if st is ABSENT or not isinstance(st, str):
        raise EIntegrity("INT-STRUCT", where, "status")
    out["status"] = st
    if st != "complete":                                   # N-F40, [48:1113-1115]: no part is opened
        return out
    for k in ("n_config", "restarts", "reruns_from_zero", "end_rule.outcome", "layout.ranks"):
        if lv.get(k, ABSENT) is ABSENT or (k != "end_rule.outcome" and not isinstance(lv[k], int)):
            raise EIntegrity("INT-STRUCT", where, k)
    parts = L.a2_parts(c, lab)                             # INT-PARTS
    chk.passed["INT-PARTS"] += 1
    rel = ctx.reads.parse_relax(lab, parts, read="full", k_cap=K_CAP, mapping=ctx.mapping, ranks=lv["layout.ranks"],
                                md5_extra=ctx.md5_extra, label=lab, block=block)   # OP-31: no n_el
    chk.require(rel.get("usable") is True and rel.get("ks") == list(range(rel.get("n_config") or 0)), "INT-PARSE",
                where, "usable, ks")
    chk.require(rel["n_config"] == lv["n_config"], "INT-NCFG", where, "n_config")
    outcome, kl_rec, conv_rec = lv["end_rule.outcome"], lv.get("k_last", ABSENT), lv.get("converged_at_k", ABSENT)
    kl = rel["k_last"]
    if outcome == "accepted_converged":                    # OP-14
        ok = kl is not None and kl == rel["converged_at_k"] == conv_rec == kl_rec
    elif outcome in ("accepted_plateau", "unconverged_cap"):
        ok = kl == K_CAP == kl_rec and rel["cap_reached"] is True
    elif outcome == "unconverged_early":
        ok = kl_rec is not ABSENT and kl == kl_rec
    else:
        ok = False
    chk.require(ok, "INT-KLAST", where, f"k_last ({outcome})")
    # XC-ENDRULE (RF-13): an operator-resolved end is compared with the override, not recomputed
    end_leaf = lv.get("end_rule.end", ABSENT)
    if isinstance(end_leaf, str) and end_leaf.endswith("(operator)"):
        xer = {"ok": outcome == "unconverged_early" and kl == kl_rec, "basis": "operator override",
               "recomputed": None, "record": outcome}
    else:
        try:
            er = q.end_rule(rel)
        except (q.S2Error, q.Refused) as e:
            raise EIntegrity("INT-PARSE", where, f"stage end_rule {type(e).__name__}") from None
        xer = {"ok": er["outcome"] == outcome, "basis": "scripts/47 end_rule", "recomputed": er["outcome"],
               "record": outcome}
        del er                                             # holds dF_200_180_meV at the cap; never kept
    # XC-PARTS (RF-23)
    if lv["reruns_from_zero"] == 0:
        xp = {"ok": len(parts) == lv["restarts"] + 1, "n_parts": len(parts), "restarts": lv["restarts"]}
    else:
        xp = {"ok": None, "n_parts": len(parts), "restarts": lv["restarts"],
              "note": "restarts include discarded attempts"}
    parts_summary = [{"n": p["n"], "n_config": p["n_config"], "k_first": p.get("k_first"), "k_last": p.get("k_last"),
                      "end": p.get("end")} for p in rel["parts"]]
    out.update(parsed=True, n_config=rel["n_config"], k_last=kl, converged_at_k=rel["converged_at_k"],
               cap_reached=rel["cap_reached"], n_parts=len(parts), parts=parts_summary,
               restart_k=[p["k_first"] for p in rel["parts"][1:] if p["n_config"]],
               xc={"ENDRULE": xer, "PARTS": xp})
    if rel["n_config"] == 0 or kl is None:                 # RF-4: no configuration, no final-geometry check
        why = f"no configuration; end rule {outcome}"
        out.update(F={}, F0=None, Ffin=None, relax_meV=None, curve_meV={}, tail={}, tail_reason=why, pw=None,
                   pw_reason=why, not_formed=why)
        out["xc"]["MIC"] = {"ok": None, "note": why}
        del rel
        return out
    chk.require(lv.get("final_geometry.k", ABSENT) == kl, "INT-FINALK", where, "final_geometry.k")
    mname = f"a2/{lab}/{lab}.final.extxyz"
    b = member_bytes(ctx.audit, L.structures(c), mname, check="INT-FINALSHA")
    chk.require(hashlib.sha256(b).hexdigest() == lv.get("final_geometry.sha256", ABSENT), "INT-FINALSHA",
                f"{c}/structures.tar.gz:{mname}", "final_geometry.sha256")
    fin = atoms_from_bytes(b)
    Xk = np.asarray(rel["positions_A"][kl], float)
    chk.require(list(rel["symbols"]) == fin.get_chemical_symbols() and Xk.shape == fin.positions.shape and
                float(np.abs(Xk - fin.positions).max()) <= FINALPOS_TOL_A, "INT-FINALPOS",
                f"{c}/structures.tar.gz:{mname}", "positions at k_last")
    a1 = a1_start(lab)
    st_at = atoms_from_bytes(member_bytes(ctx.audit, L.structures("c1"), f"cells/{a1}/start.extxyz", check="INT-CELL"))
    chk.require(float(np.abs(fin.cell.array - st_at.cell.array).max()) <= CELL_TOL_A, "INT-CELL",
                f"{c}/structures.tar.gz:{mname}", f"cell against c1 cells/{a1}/start.extxyz")
    # derived values (spec 5.1 item 6)
    F = {int(k): float(v) for k, v in rel["F_eV"].items()}
    F0, Ffin = F[0], F[kl]
    if tail_ks is None:
        kt = kl - TAIL_BACK
        tail_ks, tail_reason = ([kt], None) if kt >= 0 else ([], f"k_last < {TAIL_BACK}")   # RF-14
    else:
        tail_reason = None
    for kt in tail_ks:
        if kt not in F:
            raise EIntegrity("INT-STRUCT", where, f"Delta F_tail k = {kt}")
    cell = fin.cell.array.copy()
    centres = region_centres(ctx, lab)
    images = image_centres(centres, cell)
    pw = ctx.m48.path_work(rel, images)                    # scripts/48 unchanged; images as centres (OP-15)
    X0 = np.asarray(rel["positions_A"][0], float)
    res = mic_residual(ctx.cd, X0, centres, images, cell)
    out.update(F=F, F0=F0, Ffin=Ffin, relax_meV=(Ffin - F0) * 1000.0,
               curve_meV={k: (F[k] - Ffin) * 1000.0 for k in sorted(F)},
               tail={kt: (F[kt] - Ffin) * 1000.0 for kt in tail_ks}, tail_reason=tail_reason,
               pw=pw, pw_reason=None if pw is not None else "< 2 configurations", centres=centres, cell=cell,
               pos0=X0.copy(), posfin=Xk.copy(), symbols=list(rel["symbols"]))
    out["xc"]["MIC"] = {"ok": res <= MIC_TOL_A, "max_residual_A": res, "tol_A": MIC_TOL_A}
    if plateau and kl == K_CAP and (K_CAP - 20) in F:      # F(200) - F(180) from the parse, never from the record
        out["plateau_meV"] = (F[K_CAP] - F[K_CAP - 20]) * 1000.0
    del rel                                                # one relaxation at a time (spec 5.1 item 7)
    return out


# ---------------------------------------------------------------- C1: census, single points, table (spec 5.3, 5.4)
def sp_full(c1, label, *, block):
    """A C1 single point (spec 5.3): C1Access.sp_full (access, cache, sp_status, parse through the ReadsAudit)."""
    return c1.sp_full(label, block=block)


def census(c1):
    """{class: [wid, ...]} of the loaded census, each list sorted (block 3.1 order: host, V, noise, startset,
    pose_start; then pb136)."""
    out = {k: [] for k in eg.CLASSES}
    for w in c1.wids:
        out[eg.classify_wid(w)].append(w)
    return {k: sorted(v) for k, v in out.items()}


def mace_leaves(rec, pre=""):
    """Every (json path, value) of an E_mace_eV key at any depth, lists included ('a.b[2].E_mace_eV')."""
    out = []
    if isinstance(rec, dict):
        for k, v in rec.items():
            p = f"{pre}.{k}" if pre else k
            if k == "E_mace_eV":
                out.append((p, v))
            else:
                out += mace_leaves(v, p)
    elif isinstance(rec, list):
        for i, v in enumerate(rec):
            out += mace_leaves(v, f"{pre}[{i}]")
    return out


_PAIR_RE = re.compile(r"(m\d\d)_(Sr|Ca|Cl|Cs|GA)(\d+)p(\d+)\.json")
_DISTINCT_RE = re.compile(r"(m\d\d)_(Cs|Cl)(\d+)_(novac|vac)\.distinct\.json")


def _empty_host():
    return {"host_valid": False, "F": {}, "cell_valid": {}, "failed_checks": {}, "pair_rejected": {},
            "pose": {"Cs": {"mode": "default", "start_failed": {}}, "Cl": {"mode": "default", "start_failed": {}}},
            "E_mace": {}, "forces": {}}


def build_c1_table(c1, ctx):
    """Block 3 (spec 5.4 with RF-18, RF-24): the pilot host tables H[p] in the s2-evaltable-1 host shape, without any
    Pb136 label, and the MACE ledger of the 155 block-3 records. Returns (T, ledger); ledger: one row per record in
    class order then wid, {wid, class, valid, failed, mace: [(json path, value)]}."""
    H = {p: _empty_host() for p in eg.PILOTS}
    ledger, full = [], {}
    cls = c1.classes()
    for k in eg.BLOCK3_CLASSES:
        for w in sorted(x for x in c1.wids if cls[x] == k):
            rb = c1.blind(w)
            rf = c1.record(w, blind=False, block=3)
            full[w] = rf
            val = rb.get("validity") or {}
            ledger.append({"wid": w, "class": k, "valid": val.get("valid") is True, "failed": list(val.get("failed")
                                                                                                    or []),
                           "mace": mace_leaves(rf)})
            p = rb.get("member")
            if p not in H:
                raise EIntegrity("INT-STRUCT", f"c1/records/{w}.json", "member")
            if rb.get("cell_kind") == "host":
                H[p]["host_valid"] = val.get("valid") is True
            for lab in rb.get("labels") or []:
                H[p]["cell_valid"][lab] = val.get("valid") is True
                H[p]["failed_checks"][lab] = val.get("failed")
                H[p]["E_mace"][lab] = (rf.get("relax") or {}).get("E_mace_eV")        # RF-24: relax, not a stage
    pdir = ctx.L.cdir("c1", "pairs")
    for n in sorted(os.listdir(pdir)):
        m, md = _PAIR_RE.fullmatch(n), _DISTINCT_RE.fullmatch(n)
        if md:                                              # kept minima (RF-18; [48:1037-1062])
            r = read_json(os.path.join(pdir, n))
            h, tok, site, leg = md.group(1), md.group(2), int(md.group(3)), md.group(4)
            if h not in H or (r.get("member"), r.get("token"), int(r.get("site")), r.get("leg")) != (h, tok, site, leg):
                raise EIntegrity("INT-STRUCT", f"c1/pairs/{n}", "member, token, site, leg")
            for o, wid in sorted((r.get("work_ids") or {}).items()):
                lab = (r.get("labels") or {}).get(o) or eg.lab_dop(h, tok, site, leg, int(o[1:]))
                if wid not in full:
                    if wid in eg.PB136_WIDS:
                        continue
                    raise EIntegrity("INT-STRUCT", f"c1/pairs/{n}", f"work_ids.{o}")
                val = c1.blind(wid).get("validity") or {}
                H[h]["cell_valid"][lab] = val.get("valid") is True
                H[h]["failed_checks"][lab] = val.get("failed")
                H[h]["E_mace"][lab] = (full[wid].get("relax") or {}).get("E_mace_eV")
            if h == "m30":
                H[h].setdefault("pose_pilot", {}).setdefault(tok, {}).setdefault(str(site), {})[leg] = \
                    sorted(r.get("map") or {}, key=lambda o: int(o[1:]))
        elif m:
            h = m.group(1)
            r = read_json(os.path.join(pdir, n))
            if h in H and r.get("status") == "rejected":
                H[h]["pair_rejected"].setdefault(f"{r['token']}{r['site']}", []).append(r.get("start", "p0"))
    for lab in sorted(eg.BLOCK3_SP):
        r = c1.sp_full(lab, block=3)
        h = re.match(r"s2_(m\d\d)_", lab).group(1)
        H[h]["F"][lab] = r["F_eV"]
        H[h]["forces"][lab] = r["forces"]
    T = {"schema": "s2-evaltable-1", "hosts": H, "a2": {},
         "a2_sites": {"m30": {"A": eg.CAL["m30"]["A"], "X": eg.CAL["m30"]["X"]},
                      "m05": {L: eg.CAL["m05"][L] for L in "BAX"}},    # no m30 B: _mace_pilot skips B136
         "sites": {p: {"far4": {L: list(eg.FAR4[p][L]) for L in "BAX"}} for p in eg.PILOTS}}
    assert_no_pb136(T, "block 3")
    return T, ledger


def pb136_keys(T):
    bad = set(eg.PB136_LABELS) | set(eg.PB136_SP)
    out = []
    for p, Hp in T["hosts"].items():
        for f in ("F", "E_mace", "cell_valid", "failed_checks", "forces"):
            out += [f"{p}.{f}.{k}" for k in Hp.get(f, {}) if k in bad]
    if "B" in T.get("a2_sites", {}).get("m30", {}) or T.get("a2", {}).get("m30"):
        out.append("a2_sites.m30.B or a2.m30")
    return out


def assert_no_pb136(T, where):
    """INT-PB136-REC: no Pb136 label (DFT, MACE or validity) in a table outside block 5."""
    bad = pb136_keys(T)
    if bad:
        raise EIntegrity("INT-PB136-REC", where, bad[0])
    return True


def extend_c1_table_hinge(T, ledger, c1, a2_hinge):
    """Block 5 of a hinge read (spec 5.4 'In hinge mode'): the five Pb136 records (MACE ledger and H['m30']), the
    Pb136 single points, a2_sites['m30']['B'] = 136 and T['a2']['m30'] from the hinge relaxations (read_relaxation
    results of the four HINGE labels). C1Access and OpenAudit must be in hinge mode, block 5."""
    if not c1.hinge or c1.audit.block != 5 or not c1.audit.hinge:
        raise Blinded("the Pb136 additions are made only in block 5 of a hinge read (S2B:561-563)")
    H = T["hosts"]["m30"]
    rows = []
    for w in sorted(eg.PB136_WIDS):
        rb, rf = c1.blind(w), c1.record(w, blind=False, block=5)
        val = rb.get("validity") or {}
        rows.append({"wid": w, "class": "pb136", "valid": val.get("valid") is True,
                     "failed": list(val.get("failed") or []), "mace": mace_leaves(rf)})
        for lab in rb.get("labels") or []:
            H["cell_valid"][lab] = val.get("valid") is True
            H["failed_checks"][lab] = val.get("failed")
            H["E_mace"][lab] = (rf.get("relax") or {}).get("E_mace_eV")
    for lab in sorted(eg.PB136_SP):
        r = c1.sp_full(lab, block=5)
        H["F"][lab] = r["F_eV"]
        H["forces"][lab] = r["forces"]
    T["a2_sites"]["m30"]["B"] = eg.CAL["m30"]["B"]
    a2 = {}
    for lab in eg.HINGE:
        r = a2_hinge[lab]
        lv = r.get("leaves") or {}
        vf = lv.get("validity_final.valid", ABSENT)
        a2[lab] = {"F0_eV": r.get("F0"), "Ffin_eV": r.get("Ffin"), "status": r.get("status"),
                   "end_rule": lv.get("end_rule.outcome"), "n_config": r.get("n_config"), "k_last": r.get("k_last"),
                   "valid_final": None if vf is ABSENT else vf is True,
                   "failed_checks": None if vf is ABSENT else lv.get("validity_final.failed")}
    T["a2"]["m30"] = a2
    return T, rows

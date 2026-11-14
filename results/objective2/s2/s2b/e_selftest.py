#!/usr/bin/env python
"""Self-tests of E, the one evaluation of S2b (S2B_PLAN.md section 7 "Self-tests"; E_IMPLEMENTATION_SPEC section 18
with E_DECISIONS_R1 RF-9, RF-18): the synthetic archive builder and the CASES registry.

  build       a synthetic archive in a temporary directory, in the shapes that scripts/46, 47, 49 and 50 write:
              c1 (160 records with unique MACE canaries, 129 single points, regions, pairs with one two-minimum
              distinct file, smoke mapping, upf_check, the gates N, pose, G1 and throughput, structures, a WP1
              directory), c2 (the eight relaxations with the C2_RESULT.md section 2 counts, relaxation 7 in three
              parts, finals, K3 and step-0 gate files with one cell per step-0 file (RF-5), the trios, canaries) and fr
              (per scenario: records, parts, finals, FR and fr_step0 gate files, markers, campaign.json,
              state_end.json). Raw outputs are q47.synthetic_pw_output text post-processed per atom: distinct force
              rows and positions, F planted as decimal strings of at most 8 places (RF-18), distinct mixed-sign
              relaxation energies and E_b by role. The planted strings are returned in the manifest, from which an
              independent recomputation starts with fractions.Fraction.
  CASES       id -> Case(fn, mutants). Each case passes on this code and fails on each of its mutants (a deliberately
              broken variant, applied by monkeypatching for the duration of one run; the comment of each mutant
              names what it breaks). Group A: the guard and access (e_guard.py; A4b and A10 at run level); group B:
              the readers (e_read.py); group C: the blocks and routes of e_eval.py on synthetic archives (every row
              of S2B sections 1 and 11 that can occur before C3b, the independent recomputation, the counts, labels,
              the FR-2 boundary, cross-check failures (C8, C8b), the hinge trigger through a test double of block
              4, and the figure: C11 runs the build asserts of figures/fig_s2b_e_fk.py on E's own source data, C11b
              the figure's self-test); group D: the run discipline (dirty tree, attempts and reruns with old-code
              runs in a subprocess, the c3 lock, the commits check, the routes' preconditions, every integrity check
              planted, the item-7 fallback, the deferred hinge run, the two-phase write, the absences of RF-12, the
              verify record (D11), RF-3 at the c3b start commit (D12), the hinge run after a FALLBACK (D13)); group
              T: the block-4 stub. Fix round 1 adds: C1o-C1q (the step-0 repeat, S2B:271-274, and R-1), C1r (RF-4
              at a step-0 cell), C1s (no final-geometry check), C1t (the STOP header's branches), C6b and C8c
              (cross-check failures planted), D14 (admissibility before integrity), D15 (the hinge run after a
              final STOP, after FR-2 failed, and its rerun), D16 (a stale .pyc under the root) and D17 (the item-7
              fallback's variants). Fix round 2 (review round 2's test-strength findings) adds: A13 (remove_tree
              from a refused working directory), C8d (FR-2, step-0 decision, signed-sum and MIC cross-checks made
              to fail), D18 (a failed block 1-3 cross-check printed in the hinge run), D19 (a STOP before the fr
              campaign commit), the C1q variants of the set-aside rule (one conjunct at a time, the @2 repeat, the
              move not recorded), the step-0 STOPs pending a fix (C1t), a planted case for each surviving mutant
              (D2, D4, D6-D10, D13-D15, A2, A5, A7, A9, A12, B2, B7, C1j, C1l, C4, C6, C6b, C7, the figure's
              self-test), and hashed MACE canaries (every MACE E_b depends on its four records; RF-18). The
              integration round adds: the item-4 label on the C1 gate statistics of A1 E_b (C4, C5b; ER2-1), L_FAR
              without L_FRVALID on an FR-pass route (C4, C5b; ER2-2), the fallback's labels (D17; ER2-3), and the
              fr/STEP0_NO_ERROR route as W's scripts/50 writes it (C1h, C1m; IX-2). Integration review 1 adds: the
              one stop note results/objective2/s2/FR_STOP_NOTE.md and its blob test (C1j, D14, D15; IX-6), a final
              STOP after a recorded FR outcome (C1v; IX-4), a stop note on a done fr refused (D20; IX-7), the labels
              of a failed XC-DSUM-FAR on both kinds of route (C8d; ER2-2) and the conjuncts of the IX-2
              acceptance (D10). Integration review 2 adds: L_FRSTOP on 'pass at gate FR; then a final STOP' (C1v,
              D17; IX-12), a stopped fr with gate FR written but not applied refused (D21; IX-15), and the review's
              test-strength rows: the attempt-2 fail_final then a STOP and its INT-ROUTE plants (C1v), the item-7
              fallback on FR-STOP after a pass (D17).
  synth_repo  for groups C, D and T: a throwaway git repository in the temporary directory holding the synthetic
              archive at results/objective2/s2, committed as the campaigns would be (scripts, archives, E's files at
              the fr campaign commit, the fr archive); e_run runs E in-process on it with an injected environment
              (e_eval.Env: git, roots, the shared 8bff03e extraction, a clock) and removes its outputs afterwards.

Blinding. No case names or opens a real archive file: at the start of a run every real archive path of this checkout,
of the main checkout and of its worktrees, and of the repository named by --repo and every worktree git lists for it
(an old-code run in a temporary tree, spec 16), is refused for the rest of the process (e_guard.selftest_block, RF-9),
and every input is synthetic. The 8bff03e modules come from git objects (e_read.import_8bff03e), not archive files;
scripts/48 _wp2c_values is replaced by a synthetic stand-in, so that no real WP2c E_b is read (fix round 1).

    python -B -I results/objective2/s2/s2b/e_eval.py --self-test       # every case, with its mutants
    python -B -I results/objective2/s2/s2b/e_selftest.py --case A1 C1a # some cases
    python -B -I results/objective2/s2/s2b/e_selftest.py --case B3 --no-mutants --repo REPO   # E's rerun check
    python -B -I results/objective2/s2/s2b/e_selftest.py --list
"""
import argparse, collections, contextlib, copy, datetime, errno, gzip, hashlib, importlib.util, io, json, math, os
import pathlib
import pickle
import re, shutil, stat, subprocess, sys, tarfile, tempfile, time
from decimal import Decimal
from fractions import Fraction

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
S2 = os.path.normpath(os.path.join(HERE, ".."))
REPO = os.path.normpath(os.path.join(S2, "..", "..", ".."))


def _sibling(name):
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
er = _sibling("e_read")
OBJECTS = {"repo": REPO}                          # the repository whose git objects hold 8bff03e (--repo; RF-9)
Blinded, EIntegrity, EError, ABSENT, FILE_ABSENT = eg.Blinded, eg.EIntegrity, eg.EError, eg.ABSENT, eg.FILE_ABSENT

# ---------------------------------------------------------------- registry
Case = collections.namedtuple("Case", "id group fn mutants doc")
CASES = collections.OrderedDict()


def case(cid, group, *, mutants=()):
    """Register a case; mutants: ((name, factory), ...), factory(fx) -> a context manager that breaks the code."""
    def deco(fn):
        if cid in CASES:
            raise ValueError(f"case {cid} registered twice")
        CASES[cid] = Case(cid, group, fn, tuple(mutants), " ".join((fn.__doc__ or "").split()))
        return fn
    return deco


@contextlib.contextmanager
def patched(obj, attr, value):
    """Monkeypatch obj.attr for the duration of a mutant run (a class attribute, a module function or a dict key)."""
    if isinstance(obj, dict):
        had, old = attr in obj, obj.get(attr)
        obj[attr] = value
        try:
            yield
        finally:
            if had:
                obj[attr] = old
            else:
                del obj[attr]
        return
    old = getattr(obj, attr)
    setattr(obj, attr, value)
    try:
        yield
    finally:
        setattr(obj, attr, old)


class MutantNotApplied(Exception):
    """A source mutant whose text no longer occurs exactly once; run() counts it as a failure, never as caught."""


def src_patched(cls, name, old, new):
    """Integration review 3: a source mutant of the method cls.name of e_eval.py, as patched() applies it. Its source
    (inspect) with the one occurrence of old replaced by new, compiled in e_eval's namespace."""
    import inspect
    import textwrap
    src = textwrap.dedent(inspect.getsource(getattr(cls, name)))
    if src.count(old) != 1:
        raise MutantNotApplied(f"src_patched: {name}: {src.count(old)} occurrences of {old!r}")
    ns = {}
    exec(compile(src.replace(old, new), f"<mutant of {name}>", "exec"), ee().__dict__, ns)
    return patched(cls, name, ns[name])


def raises(exc, fn, *a, check=None, **kw):
    """fn(*a, **kw) must raise exc (and, with check, the exception must satisfy it); returns the exception."""
    try:
        fn(*a, **kw)
    except exc as e:
        if check is not None and not check(e):
            raise AssertionError(f"{fn}: raised {type(e).__name__} without the expected content: {e}")
        return e
    raise AssertionError(f"{getattr(fn, '__name__', fn)} did not raise {exc.__name__}")


def int_fail(check_id, fn, *a, **kw):
    """fn must raise EIntegrity with this check id."""
    return raises(EIntegrity, fn, *a, check=lambda e: e.check == check_id, **kw)


# ---------------------------------------------------------------- fixture
class Fixture:
    """Shared state of one run: the 8bff03e extraction (once), a temporary directory (RF-21 removal), cached trees."""

    def __init__(self, keep=None):
        self.tmp = tempfile.mkdtemp(prefix="e_selftest_")
        self.keep = keep
        self._ex, self._trees, self._n = None, {}, 0

    @property
    def ex(self):
        if self._ex is None:
            self._ex = er.import_8bff03e(OBJECTS["repo"], tmp_parent=self.tmp)
            self._ex.m48._wp2c_values = _wp2c_stub     # no self-test reads the real WP2c E_b (fix round 1; RF-9)
        return self._ex

    def workdir(self, name):
        self._n += 1
        d = os.path.join(self.tmp, f"{self._n:03d}_{name}")
        os.makedirs(d)
        return d

    def tree(self, name="base", **scenario):
        """A full synthetic archive, built once per name and treated as read-only by the cases."""
        if name not in self._trees:
            root = os.path.join(self.workdir(f"tree_{name}"), "s2")
            self._trees[name] = (root, build(root, self.ex, scenario or None))
        return self._trees[name]

    def close(self):
        msgs = []
        if self._ex is not None:
            m = self._ex.cleanup()
            if m:
                msgs.append(m)
        if self.keep:
            shutil.copytree(self.tmp, self.keep, dirs_exist_ok=True)
        m = er.remove_tree(self.tmp)
        if m:
            msgs.append(m)
        return msgs


@contextlib.contextmanager
def session(fx, root, *, private_root=None, hinge=False, block=None):
    """ELayout, a started OpenAudit and a ReadCtx on a synthetic root; the audit is stopped afterwards."""
    L = er.ELayout(root, private_root)
    audit = eg.OpenAudit(root, private_root=private_root, tmp=[fx.ex.tmp]).start()
    try:
        if hinge:
            audit.open_hinge()
        audit.set_block(block)
        ctx = er.ReadCtx(L, audit, fx.ex)
        yield L, audit, ctx
    finally:
        audit.stop()


WP2C_STUB = {"m30_Sr136": {"Eb_dft_meV": 4242.4242, "Eb_dft_farref_meV": 4343.4343}, "m30_GA128": None,
             "m05_Sr124": None}                     # synthetic values in the shape of scripts/48 _wp2c_values


def _wp2c_stub():
    """The self-test's stand-in for scripts/48 _wp2c_values (fix round 1): block 5 prints these synthetic values and
    the extracted wp2cde_dft.json is never opened by an E run of the self-test (C6 asserts it)."""
    return copy.deepcopy(WP2C_STUB)


def real_archive_roots(repo):
    """RF-9 (fix round 1): the S2 roots of a repository and of every worktree git lists for it, by name only (no
    archive file is opened). e_selftest.run refuses them for the whole process, so that an old-code run in a
    temporary tree (spec 16) refuses the real archive of the repository named by --repo, not only its own tree."""
    out = [os.path.join(repo, "results", "objective2", "s2")]
    try:
        r = subprocess.run(["git", "-C", repo, "worktree", "list", "--porcelain"], capture_output=True,
                           env={**os.environ, **GIT_ENV})
    except OSError:
        r = None
    if r is not None and r.returncode == 0:
        out += [os.path.join(x[len("worktree "):], "results", "objective2", "s2")
                for x in r.stdout.decode(errors="replace").splitlines() if x.startswith("worktree ")]
    seen, res = set(), []
    for x in out:
        rp = os.path.realpath(x)
        if rp not in seen:
            seen.add(rp); res.append(rp)
    return res


# ---------------------------------------------------------------- synthetic archive: constants
ALAT_BOHR = 40.0                                  # cubic synthetic cell (21.17 A), as printed by the pw.x text
SYM_SP = ("Pb", "I", "Cs")                        # single points: nat 3 (spec section 18)
SYM_A2 = ("Pb", "I", "I", "Cs", "C", "N")         # relaxations and every structure member: nat 6
RY = Fraction(13605693122994, 10 ** 12)           # scripts/32 RY (eV), as a Fraction for the independent code
BOHR = Fraction(529177210903, 10 ** 12)           # scripts/32 BOHR (A)
Q8 = Decimal("0.00000001")
MAPPING = {"c0": 0, "affine_slope_1": True, "nstep_first": 201, "restart_continues_counters": True,
           "restart_repeats_last": False, "restart_offset_d": 0, "nstep_after_restart": "201 - completed - c0",
           "restart_files": ["synthetic"], "exit_marker": "Program stopped by user request"}   # c1/smoke.json keys
C2_CONST = {"s2r_m30_VB136": (79, 0, 1), "s2r_m30_hostB136": (83, 0, 0), "s2r_m30_Sr136o0_novac": (81, 0, 0),
            "s2r_m30_Sr136o0_vac": (75, 0, 0), "s2r_m30_hostB76": (165, 0, 0), "s2r_m30_VB76": (193, 0, 0),
            "s2r_m30_Sr76o0_novac": (142, 2, 0), "s2r_m30_Sr76o0_vac": (136, 0, 0)}  # n_config, restarts, reruns
POSE_STARTS = {("Cs", 128): (1, 2, 3, 4, 5, 6), ("Cs", 188): (1, 2, 4, 5), ("Cl", 138): (1, 2), ("Cl", 175): (1, 2)}
REJECTED = (("Cs", 188, 3), ("Cs", 188, 6))       # c1/pairs m30_Cs188p3, p6 (C1_RESULT section 1)
TWO_MINIMA = ("Cs", 188, "novac")                 # RF-18: one distinct file with o0 and o1
CANARY = {"dF_200_180_meV": 9876.54321, "value_meV": 1111.111, "hinge_target_meV": 7654.321}   # spec section 18
PB136_MACE = -13613.613613                        # Pb136 E_mace_eV canaries: -13613.613613 - i (spec section 18)


def hnum(s, n):
    return int(hashlib.sha256(s.encode()).hexdigest()[:12], 16) % n


def d8(x):
    return Decimal(x).quantize(Q8)


def census_wids():
    """The 160 C1 work ids of the archive listing (restated from the constants of e_guard and POSE_STARTS)."""
    out = []
    for p in eg.PILOTS:
        out.append(f"s2_{p}_host")
        for L in "BAX":
            for j in sorted(set(eg.FAR4[p][L]) | {eg.CAL[p][L]}):
                out.append(f"s2_{p}_V{L}{j}")
                for t in eg.TOKENS_OF[L]:
                    for leg in eg.LEGS:
                        out.append(f"s2_{p}_{t}{j}p0_{leg}")
    for (t, j), ns in POSE_STARTS.items():
        for n in ns:
            for leg in eg.LEGS:
                out.append(f"s2_m30_{t}{j}p{n}_{leg}")
    out = sorted(set(out))
    m05_g = {f"s2_m05_{t}{j}p0_{leg}" for t in ("Sr", "Ca") for j in (eg.CAL["m05"]["B"],) for leg in eg.LEGS}
    assert m05_g <= set(out)
    return out


def sp_labels():
    return sorted(set().union(*eg.SP_SETS.values()))


def sp_F(label):
    """The planted F of a single point (Ry, 8 places): a pilot base plus a label offset within +-0.01 Ry."""
    base = Decimal("-12345.12345678") if "_m30_" in label else Decimal("-12346.87654321")
    return str(d8(base + (hnum(label, 2000001) - 1000000) * Q8))


def sp_forces(label, nat=3):
    """Distinct mixed-sign force rows (Ry/bohr, 8 places) of a single point."""
    return [[str(d8(Decimal(hnum(f"{label}|f{i}{c}", 2000001) - 1000000) * Decimal("0.00000005")))
             for c in range(3)] for i in range(nat)]


def a1_sp_label(lab):
    c = er.a2_cell(lab)
    if c["kind"] == "host":
        return f"s2_{c['pilot']}_host"
    if c["kind"] == "V":
        return f"s2_{c['pilot']}_V{c['L']}{c['site']}"
    return lab.replace("s2r_", "s2_", 1)


ROLE_SIGN = {"host": -1, "V": -1, "D": 1, "DV": -1}     # mixed-sign relaxation energies (RF-18)


def a2_F(lab, n_config, *, d0=None, drop=None, plateau_Ry=None):
    """F(k) strings (Ry, 8 places) of one relaxation: F(0) = F(SP of its A1 start) + d0 (|d0| <= 3e-5 Ry, about
    0.41 meV: step 0 passes), then a smooth approach to F(0) + drop (sign by role). plateau_Ry: F(200) - F(180) set to
    this value (a relaxation that reaches the cap)."""
    kind = er.a2_cell(lab)["kind"]
    d0 = Decimal(hnum(lab + "|d0", 6001) - 3000) * Q8 if d0 is None else d8(d0)
    drop = ROLE_SIGN[kind] * Decimal(hnum(lab + "|drop", 400000) + 20000) * Q8 if drop is None else d8(drop)
    F0 = Decimal(sp_F(a1_sp_label(lab))) + d0
    K = n_config - 1
    if K <= 0:
        return [str(d8(F0))] if n_config == 1 else []
    r = Decimal("0.97")
    den = 1 - r ** K
    F = [d8(F0 + drop * (1 - r ** k) / den) for k in range(K)] + [d8(F0 + drop)]
    if plateau_Ry is not None and K >= 200:
        base = F[180]
        for k in range(181, 201):
            F[k] = d8(base + Decimal(plateau_Ry) * (k - 180) / 20)
        F[200] = d8(base + Decimal(plateau_Ry))
    return [str(x) for x in F]


def positions_fn(lab, nat=6):
    """Per-atom distinct positions (A) along the path; atom i drifts along its own direction."""
    rng = np.random.default_rng(hnum(lab + "|pos", 2 ** 31))
    base = rng.uniform(2.0, 19.0, size=(nat, 3))
    dirs = rng.normal(size=(nat, 3))
    amp = rng.uniform(0.01, 0.2, size=nat)

    def pos(k):
        return base + (amp * (1 - 0.95 ** k))[:, None] * dirs
    return pos


def forces_fn(lab, nat=6):
    """Per-atom distinct mixed-sign forces (Ry/bohr) decaying with k."""
    rng = np.random.default_rng(hnum(lab + "|frc", 2 ** 31))
    f0 = rng.uniform(-0.02, 0.02, size=(nat, 3))

    def frc(k):
        return f0 * (0.93 ** k) + 1e-4 * (np.arange(nat)[:, None] + 1) * (-1) ** k
    return frc


_TAU = re.compile(r"^\s+\d+\s+\S+\s+tau\(\s*\d+\)\s*=\s*\(")
_FROW = re.compile(r"^\s+atom\s+\d+\s+type\s+\d+\s+force\s+=")
_AXIS = re.compile(r"^\s+a\((\d)\) = \(")


def pw_text(q47, *, input_name, k0, n_config, end, F, pos, frc, symbols, ranks=64, calculation="relax", header=True,
            cell=None):
    """q47.synthetic_pw_output, post-processed (RF-18): alat and crystal axes of the synthetic cell, header positions,
    every ATOMIC_POSITIONS block and every force row per atom and configuration. Returns (text, printed): printed
    holds the strings of F, positions and forces of every configuration as the parsers read them."""
    nat = len(symbols)
    t = q47.synthetic_pw_output(n_config=n_config, calculation=calculation, end=end, k0=k0, header=header, nat=nat,
                                F_Ry=[float(s) for s in F] if F else None, label=input_name, ranks=ranks,
                                symbols=list(symbols))
    bA = ALAT_BOHR * q47.QE_UNITS["Bohr"]
    cell = np.eye(3) * bA if cell is None else np.asarray(cell, float)
    out, lines, nb, fin, tau, i = [], t.split("\n"), 0, False, 0, 0
    printed = {"F": {k0 + j: F[j] for j in range(len(F))}, "pos": {}, "frc": {}, "header_k": k0 if header else None}
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("     lattice parameter (alat)"):
            ln = f"     lattice parameter (alat)  =  {ALAT_BOHR:11.4f}  a.u."
        elif "celldm(1)=" in ln:
            ln = re.sub(r"celldm\(1\)=\s*\S+", f"celldm(1)=  {ALAT_BOHR:.6f}", ln)
        elif _AXIS.match(ln):
            j = int(_AXIS.match(ln).group(1)) - 1
            a = cell[j] / bA
            ln = f"               a({j + 1}) = ( {a[0]:10.6f} {a[1]:10.6f} {a[2]:10.6f} )  "
        elif _TAU.match(ln):
            X = pos(k0)
            s = [f"{X[tau][c] / bA:12.7f}" for c in range(3)]
            ln = f"     {tau + 1:5d}           {symbols[tau]:2s}  tau({tau + 1:4d}) = ({s[0]}{s[1]}{s[2]}  )"
            printed["pos"].setdefault(k0, []).append(("alat", s))
            tau += 1
        elif ln.startswith("!"):
            nb += 1
        elif ln.startswith("Begin final coordinates"):
            fin = True
        elif ln.startswith("End final coordinates"):
            fin = False
        elif ln.startswith("ATOMIC_POSITIONS"):
            k = k0 + nb - 1 if fin else k0 + nb
            X = pos(k)
            out.append(ln)
            rows = []
            for a in range(nat):
                s = [f"{X[a][c]:20.10f}" for c in range(3)]
                out.append(f"{symbols[a]:2s} {s[0]}{s[1]}{s[2]}")
                rows.append(("A", s))
            if not fin:
                printed["pos"][k] = rows
            i += 1 + nat
            continue
        elif _FROW.match(ln):
            k = k0 + nb - 1
            Fo = frc(k)
            a = int(ln.split()[1]) - 1
            s = [f"{Fo[a][c]:14.8f}" for c in range(3)]
            ln = f"     atom {a + 1:4d} type  1   force = {s[0]}{s[1]}{s[2]}"
            printed["frc"].setdefault(k, []).append(s)
        out.append(ln)
        i += 1
    return "\n".join(out), printed


def printed_positions(q47, printed, k):
    """The positions (A, float) the parsers read for configuration k, from the printed strings."""
    rows = printed["pos"][k]
    alat = float(f"{ALAT_BOHR:.6f}") * q47.QE_UNITS["Bohr"]
    return np.array([[float(v) * alat if kind == "alat" else float(v) for v in s] for kind, s in rows])


def write_gz(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt") as fh:
        fh.write(text)


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(json.dumps(obj, indent=1))
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def extxyz_bytes(c46, symbols, positions, cell, workdir):
    """A structure member as scripts/46 write_cell writes it (no calculator, positions to 1e-8 A)."""
    from ase import Atoms
    p = os.path.join(workdir, f"m{hnum(repr((symbols, np.asarray(positions).tolist())), 10 ** 9)}.extxyz")
    c46.write_cell(p, Atoms(symbols=list(symbols), positions=np.asarray(positions, float), cell=cell, pbc=True))
    with open(p, "rb") as fh:
        b = fh.read()
    os.remove(p)
    return b


def write_tar(path, members):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with tarfile.open(path, "w:gz", format=tarfile.PAX_FORMAT) as t:
        for name in sorted(members):
            b = members[name]
            ti = tarfile.TarInfo(name)
            ti.size, ti.mtime = len(b), 0
            t.addfile(ti, io.BytesIO(b))


def cell_matrix(q47):
    return np.eye(3) * (ALAT_BOHR * q47.QE_UNITS["Bohr"])


# ---------------------------------------------------------------- synthetic archive: relaxations
def write_relaxation(root, ex, c, lab, *, n_config, outcome="accepted_converged", end=None, parts=None, d0=None,
                     drop=None, plateau_Ry=None, restarts=None, reruns_from_zero=0, valid=True, failed=None,
                     check=True, fr=False, invariant_only=False, operator=False, input_label=None, cell=None,
                     members=None, workdir=None, extra=None):
    """One complete A2 relaxation: part outputs (and inputs), the s2-a2-1 record with canaries and an unlisted sibling
    at every depth, the final member (added to members). Returns the planted values."""
    q47, c46 = ex.q47, ex.c46
    raw = os.path.join(root, c, "raw")
    os.makedirs(raw, exist_ok=True)
    F = a2_F(lab, n_config, d0=d0, drop=drop, plateau_Ry=plateau_Ry)
    pos, frc = positions_fn(lab), forces_fn(lab)
    if end is None:
        end = {"accepted_converged": "converged", "accepted_plateau": "exit", "unconverged_cap": "exit",
               "unconverged_early": "bfgs_failed"}[outcome]
    parts = parts or [(0, n_config, end)]
    printed = {"F": {}, "pos": {}, "frc": {}, "header_ks": []}
    for n, (k0, nk, pend) in enumerate(parts, 1):
        txt, pr = pw_text(q47, input_name=f"{input_label or lab}.p{n}", k0=k0, n_config=nk, end=pend,
                          F=F[k0:k0 + nk], pos=pos, frc=frc, symbols=SYM_A2, cell=cell)
        write_gz(os.path.join(raw, f"{lab}.p{n}.out.gz"), txt)
        write_gz(os.path.join(raw, f"{lab}.p{n}.in.gz"), f"&control\n  calculation = 'relax'\n/\n! {lab}.p{n}\n")
        for key in ("F", "pos", "frc"):
            printed[key].update(pr[key])
        printed["header_ks"].append(k0)
    kl = n_config - 1 if n_config else None
    rec = {"schema": "s2-a2-1", "label": lab, "campaign": c, "order": 0, "a1_cell": {"work_id": er.a1_start(lab)},
           "layout": {"name": "np64", "ranks": 64, "copies": 1, "zz_unlisted": 1},
           "parts": [{"n": n, "input": f"{lab}.p{n}.in", "restart_mode": None if n == 1 else "restart", "nstep": 201,
                      "ended": "2026-11-20T00:00:00Z", "end": pend, "k_last": k0 + nk - 1 if nk else None,
                      "wall_s": 100.0} for n, (k0, nk, pend) in enumerate(parts, 1)],
           "reruns_from_zero": reruns_from_zero, "restarts": len(parts) - 1 if restarts is None else restarts,
           "interruptions": [], "status": "complete", "n_config": n_config, "k_last": kl,
           "qe_converged": outcome == "accepted_converged",
           "converged_at_k": kl if outcome == "accepted_converged" else None,
           "end_rule": {"outcome": outcome, "dF_200_180_meV": CANARY["dF_200_180_meV"],
                        "end": (f"{end} (operator)" if operator else end) if outcome == "unconverged_early" else
                        {"exit": "cap", "converged": "converged"}.get(end, end),
                        "stop": False, "reason": None, "zz_unlisted": 2},
           "wall_h": 1.5, "min_per_config": 0.7, "k0_seen": True, "nstep_first": 201, "zz_unlisted": 3,
           "value_meV": CANARY["value_meV"], "Eb_A2_meV": CANARY["value_meV"]}
    out = {"label": lab, "F": F, "printed": printed, "n_config": n_config, "k_last": kl, "pos": pos, "frc": frc}
    if kl is not None:
        Xk = printed_positions(q47, printed, kl) if kl in printed["pos"] else None
        if Xk is None:
            raise AssertionError(f"{lab}: no printed positions at k_last")
        b = extxyz_bytes(c46, SYM_A2, Xk, cell_matrix(q47) if cell is None else cell, workdir or raw)
        members[f"a2/{lab}/{lab}.final.extxyz"] = b
        rec["final_geometry"] = {"file": f"{lab}.final.extxyz", "k": kl, "sha256": hashlib.sha256(b).hexdigest(),
                                 "zz_unlisted": 4}
        out["final_bytes"] = b
        if check:
            vf = {"valid": bool(valid), "failed": list(failed or ([] if valid else [5])),
                  "file": f"{lab}.validity_final.json", "sha256": "2" * 64, "parent": None, "parent_final": True,
                  "zz_unlisted": 5}
            if fr:
                vf.update(check5_reading="invariant", valid_as_written=bool(valid) and not invariant_only,
                          failed_as_written=list(vf["failed"]) + ([5] if invariant_only else []),
                          invariant_only=bool(invariant_only))
            rec["validity_final"] = vf
            dump(os.path.join(raw, f"{lab}.validity_final.json"), {"schema": "s2-a2validity-1", "label": lab,
                                                                    "validity": {"valid": vf["valid"]},
                                                                    "F_final_eV": -1.0})   # never opened
    rec.update(extra or {})
    out["record_sha256"] = dump(os.path.join(raw, f"{lab}.a2.json"), rec)
    out["record"] = rec
    return out


def write_stub(root, c, lab, status, reason=None, parts=None):
    """An A2 record of a cell that did not complete (no part is archived)."""
    rec = {"schema": "s2-a2-1", "label": lab, "campaign": c, "status": status, "status_reason": reason,
           "parts": parts or [], "restarts": 0, "reruns_from_zero": 0, "layout": {"name": "np64", "ranks": 64,
                                                                                 "copies": 1}}
    dump(os.path.join(root, c, "raw", f"{lab}.a2.json"), rec)
    return rec


def gate_file(gate, campaign, result, decision, *, attempt=1):
    """The s2-gate-1 shape with the CLI's state_in/inputs_in/c1_in/inputs_opened canaries (scripts/49)."""
    return {"schema": "s2-gate-1", "gate": gate, "campaign": campaign, "commit": "8" * 40, "attempt": attempt,
            "opened": [{"label": "x", "file": "work/s2/x", "sha256": "3" * 64, "mode": "k0"}],
            "inputs_digest": "4" * 64, "result": result, "decision": decision, "written": "2026-11-20T00:00:00Z",
            "state_in": {"K3": "fail_replan", "Eb_A2_meV": 5555.5}, "inputs_in": {"F_k0_eV": -4444.4},
            "c1_in": None, "inputs_opened": [{"dF_meV": 3333.3}]}


def write_applied(root, c, gid, gate, gfile_obj, gates_name=None, *, inputs=None):
    """gates/<name>.json (if gates_name), gates_applied/<id>.gate.json, the marker <id>.json and <id>.inputs.json."""
    stem = eg.applied_id(gid)
    ga = os.path.join(root, c, "gates_applied")
    sha = None
    if gates_name:
        sha = dump(os.path.join(root, c, "gates", f"{gates_name}.json"), gfile_obj)
    copy_sha = dump(os.path.join(ga, f"{stem}.gate.json"), gfile_obj)
    marker = {"schema": "s2-gate-applied-1", "id": gid, "gate": gate, "rc": 0, "attempt": gfile_obj.get("attempt", 1),
              "decision": gfile_obj["decision"], "gate_file_sha256": sha or copy_sha,
              "applied": "2026-11-20T00:00:00Z"}
    dump(os.path.join(ga, f"{stem}.json"), marker)
    dump(os.path.join(ga, f"{stem}.inputs.json"), inputs if inputs is not None else {"canary_dF_meV": 2222.2})
    return marker


def eb_float(Fdv, Fd, Fv, Fh):
    """E_b (meV) from Ry strings with the parsers' float arithmetic (eV = float(s) x RY), as scripts/49 eb_meV."""
    r = float(RY)
    return ((float(Fdv) * r - float(Fd) * r) - (float(Fv) * r - float(Fh) * r)) * 1000.0


def eb_fraction(Fdv, Fd, Fv, Fh):
    """The independent E_b (meV) from the planted strings (Fraction; RF-18)."""
    return ((Fraction(Fdv) - Fraction(Fd)) - (Fraction(Fv) - Fraction(Fh))) * RY * 1000


# ---------------------------------------------------------------- synthetic archive: c1
def build_c1(root, ex, man, workdir):
    q47, c46, g49 = ex.q47, ex.c46, ex.g49
    c1 = os.path.join(root, "c1")
    wids = census_wids()
    assert len(wids) == 160
    cls = {w: eg.classify_wid(w) for w in wids}
    mace, i_pb = {}, 0
    members = {}
    cell = cell_matrix(q47)
    for i, w in enumerate(wids):
        p = eg.WORK_RE.fullmatch(w).groupdict()
        member = p["host"]
        if p["hostcell"]:
            kind, labels, L, j, tok, leg, start = "host", [f"s2_{member}_host"], None, None, None, None, None
        elif p["vL"]:
            kind, L, j, tok, leg, start = "V", p["vL"], int(p["vj"]), None, "vac", None
            labels = [f"s2_{member}_V{L}{j}"]
        else:
            tok, j, n, leg = p["tok"], int(p["j"]), int(p["n"]), p["leg"]
            kind, L, start = ("D" if leg == "novac" else "DV"), eg.SUBLATTICE[tok], f"p{n}"
            labels = [f"s2_{member}_{tok}{j}o0_{leg}"] if n == 0 else []
        # fix round 2 (RF-18): a hashed micro-eV offset per work id, so that every MACE E_b depends on all four
        # records and the Sr/Ca and Cs/GA quartets of one site differ (before, every D/D+V pair differed by 1 meV)
        if cls[w] == "pb136":
            e = round(PB136_MACE - i_pb - hnum(w + "|mace", 500) * 1e-6, 6)
            i_pb += 1
        else:
            e = round(-1000.0 - 0.001 * i - 0.000123 - hnum(w + "|mace", 800) * 1e-6, 6)
        relax = {"optimizer": "FIRE", "steps": 50 + i, "converged": True, "E_mace_eV": e, "fmax_final_free_eVA": 0.01}
        leaves = [("relax.E_mace_eV", e)]
        if kind == "host":
            relax["stages"] = []
            for s in range(3):
                es = round(e - 0.5 - 0.111 * (s + 1), 6)                     # RF-24: distinct stage canaries
                relax["stages"].append({"fmax_target": 0.02 / (s + 1), "steps": 10, "converged": True,
                                        "E_mace_eV": es})
                leaves.append((f"relax.stages[{s}].E_mace_eV", es))
        mace[w] = leaves
        free = [0, 2] if i % 3 else [1, 2]
        valid = w != "s2_m30_Cs128p4_vac"                                    # one invalid pose start, check 3
        vdict = {"checks": {str(c): {"passed": valid or c != 3} for c in range(1, 6)}, "valid": valid,
                 "failed": [] if valid else [3]}
        if w == "s2_m30_Cs128p5_novac":                  # fix round 2: a pose start whose checks were not evaluated
            vdict = {"checks": {}, "valid": None, "failed": None}            # (valid None: listed in table 3.6)
        rec = {"schema": "s2-cell-1", "work_id": w, "labels": labels, "campaign": "c1", "member": member,
               "role": "pilot", "cell_kind": kind, "leg": leg, "site": j, "site_cell": j, "sublattice": L,
               "site_roles": [], "token": tok, "start": start, "pose_id": None, "is_default_pose": start in (None,
                                                                                                             "p0"),
               "k_min": None, "region_id": "r" * 8, "free": free, "n_free": len(free), "n_fixed": 3 - len(free),
               "parent": None, "pair": None, "builder": {}, "model": {"name": "mace"}, "relax": relax,
               "validity": vdict,
               "files": {}, "sha256": {}, "geometry_sha256": {}, "attempts": [], "code": {}, "written": "t"}
        dump(os.path.join(c1, "records", f"{w}.json"), rec)
        X = positions_fn(w)(0)
        members[f"cells/{w}/start.extxyz"] = extxyz_bytes(c46, SYM_A2, X, cell, workdir)
        members[f"cells/{w}/relaxed.extxyz"] = extxyz_bytes(c46, SYM_A2, X + 0.01, cell, workdir)
    man["c1_mace"] = mace
    man["c1_classes"] = cls
    # single points (129): planted F and force rows, nat 3
    man["sp_F"], man["sp_forces"], man["sp_free"] = {}, {}, {}
    label_wid = {}
    for w in wids:
        with open(os.path.join(c1, "records", f"{w}.json")) as fh:
            for lab in json.load(fh)["labels"]:
                label_wid[lab] = w
    for lab in sp_labels():
        F = sp_F(lab)
        frows = sp_forces(lab)
        X = positions_fn(lab, 3)
        txt, _ = pw_text(q47, input_name=lab, k0=0, n_config=1, end="done", F=[F], pos=X,
                         frc=lambda k, fr=frows: np.array([[float(v) for v in r] for r in fr]), symbols=SYM_SP,
                         calculation="scf")
        write_gz(os.path.join(c1, "raw", f"{lab}.out.gz"), txt)
        write_gz(os.path.join(c1, "raw", f"{lab}.in.gz"), f"&control\n  calculation = 'scf'\n/\n! {lab}\n")
        man["sp_F"][lab], man["sp_forces"][lab] = F, frows
        base = lab[:-3] if lab.endswith("_q0") else lab
        if base in label_wid:
            with open(os.path.join(c1, "records", f"{label_wid[base]}.json")) as fh:
                man["sp_free"][lab] = json.load(fh)["free"]
    # regions (the A2 sites; a centre near a cell face, as the m30 Pb76 site at z = 0.037 A)
    for (L, j) in (("B", 76), ("A", 188), ("B", 136)):
        dump(os.path.join(c1, "regions", f"m30_{L}{j}.json"),
             {"schema": "s2-region-1", "member": "m30", "site": j, "sublattice": L,
              "centres": {"v": [6.71811919, 13.57856311, 9.685798], "site": [6.63524065, 6.60189266, 0.03674373]},
              "free": [0, 1, 2, 3], "n_free": 4, "region_id": "r" * 8})
    # pairs: built pairs, two rejected pairs, eight distinct files (one with o0 and o1, RF-18)
    for t, j in (("Sr", 76), ("Cs", 188), ("Cl", 175)):
        dump(os.path.join(c1, "pairs", f"m30_{t}{j}p0.json"), {"schema": "s2-pair-1", "member": "m30", "token": t,
                                                               "site": j, "start": "p0", "status": "built"})
    for t, j, n in REJECTED:
        dump(os.path.join(c1, "pairs", f"m30_{t}{j}p{n}.json"),
             {"schema": "s2-pair-1", "member": "m30", "token": t, "site": j, "start": f"p{n}", "status": "rejected",
              "rejection": {"exception": "Inadmissible", "leg": "host"}})
    man["distinct"] = {}
    for (t, j) in POSE_STARTS:
        for leg in eg.LEGS:
            mp = {"o0": "p0"}
            if (t, j, leg) == TWO_MINIMA:
                mp = {"o0": "p0", "o1": "p1"}
            kind = "D" if leg == "novac" else "DV"
            dump(os.path.join(c1, "pairs", f"m30_{t}{j}_{leg}.distinct.json"),
                 {"schema": "s2-distinct-1", "member": "m30", "token": t, "site": j, "leg": leg, "kind": kind,
                  "map": mp, "labels": {o: f"s2_m30_{t}{j}{o}_{leg}" for o in mp},
                  "work_ids": {o: f"s2_m30_{t}{j}{pn}_{leg}" for o, pn in mp.items()}})
            man["distinct"][(t, j, leg)] = mp
    dump(os.path.join(c1, "smoke.json"), {"schema": "s2-smoke-1", "mapping": MAPPING, "energies_read": False})
    upf = {"schema": "s2-upf-1", "passed": True, "reference_sha256_from": None,
           "files": {el: {"file": q47.PSEUDO_S2[el], "md5": q47.UPF_MD5_S1.get(el, "0" * 32), "passed": True}
                     for el in sorted(q47.PSEUDO_S2)}}
    dump(os.path.join(c1, "upf_check.json"), upf)
    # gates: N from the planted noise quartets (scripts/49 gate_n_eval), pose, G1, throughput
    t = {}
    for p in eg.PILOTS:
        for L in "BAX":
            for f in eg.FAR4[p][L]:
                for d in eg.TOKENS_OF[L]:
                    t.setdefault(p, {}).setdefault(d, {})[f] = eb_float(
                        sp_F(f"s2_{p}_{d}{f}o0_vac"), sp_F(f"s2_{p}_{d}{f}o0_novac"), sp_F(f"s2_{p}_V{L}{f}"),
                        sp_F(f"s2_{p}_host"))
    gN = g49.gate_n_eval(t)
    man["gate_N"] = gN
    dump(os.path.join(c1, "gates", "N.json"), gate_file("N", "c1", gN, {"N": {d: v["pass"] for d, v in
                                                                          gN["dopants"].items()}}))
    # the pose gate as scripts/49 pose_eval gives it for the planted single points of the kept minima (a kept
    # minimum without a single point, as o1 of TWO_MINIMA, makes the rule 'not met': multi, a_pose 0)
    sps, pose_t = set(sp_labels()), {}
    for tok, (near, far) in eg.POSE_SITES.items():
        pose_t[tok] = {}
        for role, j in (("near", near), ("far", far)):
            st_ = {"default_valid": {}}
            for leg in eg.LEGS:
                mp = man["distinct"][(tok, j, leg)]
                labs = {o: f"s2_m30_{tok}{j}{o}_{leg}" for o in mp}
                st_[leg] = {o: float(sp_F(lab)) * float(RY) if lab in sps else None for o, lab in sorted(labs.items())}
                st_["default_valid"][leg] = f"s2_m30_{tok}{j}p0_{leg}" != "s2_m30_Cs128p4_vac" and mp.get("o0") == "p0"
            pose_t[tok][role] = st_
    pose = g49.pose_eval(pose_t)
    man["pose"] = pose
    dump(os.path.join(c1, "gates", "pose.json"), gate_file("pose", "c1", pose, {"pose": {k: "default" for k in pose}}))
    dump(os.path.join(c1, "gates", "G1.json"), gate_file("G1", "c1", {}, {"G1": {"Cl": {"pass": True},
                                                                               "Ca": {"pass": False}}}))
    dump(os.path.join(c1, "gates", "throughput.json"),
         gate_file("throughput", "c1", {"rate_config_per_node_h": {"48": 10.0, "64": 12.5, "2x32": None},
                                        "choice": "64"}, {"throughput": "64"}))
    dump(os.path.join(c1, "throughput.json"), {"schema": "s2-throughput-1", "runs": {}, "energies_read": False})
    write_tar(os.path.join(c1, "structures.tar.gz"), members)
    # WP1 directory for scripts/48 _determinism (outside the archive root)
    wp1 = os.path.join(os.path.dirname(root), "wp1")
    wm = {}
    for p in eg.PILOTS:
        dump(os.path.join(wp1, f"shell_{p}.json"), {"E_host": {"E_eV": -999.5 - (p == "m05")}})
        wm[f"v2prod/{p}_host_relaxed.extxyz"] = extxyz_bytes(c46, SYM_A2, positions_fn(f"s2_{p}_host")(0) + 0.02,
                                                             cell, workdir)
    write_tar(os.path.join(wp1, "v2prod_structures.tar.gz"), wm)
    man["wp1_dir"] = wp1
    return members


# ---------------------------------------------------------------- synthetic archive: c2
def build_c2(root, ex, man, workdir, sc):
    c2 = os.path.join(root, "c2")
    members, rel = {}, {}
    for lab, (n, rs, rz) in C2_CONST.items():
        parts = [(0, 1, "killed"), (1, 1, "killed"), (2, n - 2, "converged")] if lab == "s2r_m30_Sr76o0_novac" else None
        drop = None
        if lab == "s2r_m30_Sr136o0_vac":                     # E_b^A2(Pb136) about the hinge canary 7654.321 meV
            r = {k: rel[k] for k in ("s2r_m30_VB136", "s2r_m30_hostB136", "s2r_m30_Sr136o0_novac")}
            F0dv = Decimal(sp_F(a1_sp_label(lab))) + Decimal(hnum(lab + "|d0", 6001) - 3000) * Q8
            want = (Decimal(CANARY["hinge_target_meV"]) / 1000 / Decimal(str(float(RY))) +
                    Decimal(r["s2r_m30_Sr136o0_novac"]["F"][-1]) +
                    (Decimal(r["s2r_m30_VB136"]["F"][-1]) - Decimal(r["s2r_m30_hostB136"]["F"][-1])))
            drop = want - F0dv
        rel[lab] = write_relaxation(root, ex, "c2", lab, n_config=n, parts=parts, restarts=rs, reruns_from_zero=rz,
                                    valid=lab != "s2r_m30_VB76", members=members, workdir=workdir, drop=drop)
    write_tar(os.path.join(c2, "structures.tar.gz"), members)
    fin = {lab: r["F"][-1] for lab, r in rel.items()}
    k0 = {lab: r["F"][0] for lab, r in rel.items()}
    far = eb_float(fin["s2r_m30_Sr76o0_vac"], fin["s2r_m30_Sr76o0_novac"], fin["s2r_m30_VB76"], fin["s2r_m30_hostB76"])
    hinge = eb_float(fin["s2r_m30_Sr136o0_vac"], fin["s2r_m30_Sr136o0_novac"], fin["s2r_m30_VB136"],
                     fin["s2r_m30_hostB136"])
    vm = sc.get("k3_value_meV")
    k3 = gate_file("K3", "c2", {"Eb_A2_meV": {"hinge": hinge + sc.get("k3_hinge_offset", 0.0),
                                               "far": far + sc.get("k3_far_offset", 0.0)},
                                "checks_failed": ["s2r_m30_VB76: final geometry fails check(s) [5]"],
                                "end_rule_failed": [], "value_meV": vm, "a1_invalid_reported": [],
                                "K3": "fail_replan"}, {"K3": "fail_replan"})
    write_applied(root, "c2", "gate:K3", "K3", k3, "K3", inputs={"canary": 1111.111})
    man["k3"] = {"far": far, "hinge": hinge}
    # step 0 at 1 (VB136) and at 4 (Sr136o0_vac): one cell per evaluation (RF-5)
    for gid, (sp, a2) in (("gate:step0@1", ("s2_m30_VB136", "s2r_m30_VB136")),
                          ("gate:step0@4", ("s2_m30_Sr136o0_vac", "s2r_m30_Sr136o0_vac"))):
        dF = (float(k0[a2]) * float(RY) - float(sp_F(sp)) * float(RY)) * 1000.0
        res = {"cells": {sp: {"dF_meV": dF, "passed": abs(dF) <= 0.5, "reason": None}}, "attempt": 1,
               "fix_note": None, "outcome": "pass", "tolerance_meV": 0.5}
        g = gate_file("step0", "c2", res, {"step0": {"attempts": 1, "outcome": "pass", "repeat": False,
                                                     "fix_note": None}})
        write_applied(root, "c2", gid, "step0", g, "step0")
        man.setdefault("c2_step0", {})[sp] = dF
    for gid, name in (("gate:K2", "K2"), ("gate:projection@after4", "projection")):
        write_applied(root, "c2", gid, name, gate_file(name, "c2", {"canary_meV": 1.5}, {name: "pass"}), name)
    dump(os.path.join(c2, "campaign.json"), {"schema": "s2-campaign-1", "campaign": "c2", "status": "done",
                                             "commit": sc.get("c2_commit", "8bff03ede8b9d0f380b6ef373b239e7deb87817f"),
                                             "phases": {}, "notes": []})
    dump(os.path.join(c2, "state_end.json"), {"commit": "8" * 40, "K3": "fail_replan"})
    for f in ("graph.json", "ledger.json", "completeness.json", "runner_reads.json"):
        dump(os.path.join(c2, f), {"canary_meV": 1.0})
    man["c2"] = rel
    return members


# ---------------------------------------------------------------- synthetic archive: fr (per scenario)
FR_N = {"host": 61, "V": 73, "D": 52, "DV": 67}


FIX_NOTE = "2026-11-21 results/objective2/s2/FR_STEP0_FIX_NOTE.md"   # the fr/STEP0_FIX note of a repeat (synthetic)
ATTEMPT1_CANARY = 6666.6666                         # the set-aside attempt-1 step-0 dF (never opened, never printed)


def build_fr(root, ex, man, workdir, sc):
    """fr per scenario: sc['fr'] = {"cells": {role: spec}, "delta_meV": target, "step0_fail": None | role,
    "status": None (derived) | 'stopped' | 'running', "stop_reason": str, "repeat": None | {"role": 'V' | 'DV',
    "after": 'pass' | 'fail_final' | 'stopped'}}. A cell spec: status, outcome, end, n_config, valid, failed,
    check, invariant_only, parts, restarts, reruns_from_zero, operator, d0, plateau_Ry.
    A repeat (fix round 1; S2B:271-274; W 50:2725-2760): the role's attempt-1 step-0 evaluation failed
    (fail_pending_fix) and was set aside under fr/step0_attempt1/ (canaries); after fr/STEP0_FIX (a second fr
    commit, added by synth_repo) the cell reruns and is evaluated as attempt 2 ('pass' or 'fail_final'), or a final
    STOP comes before it reruns ('stopped': its record, gates/fr_step0.json and its trio are absent). Fix round 2:
    'stopped' also for role V (a STOP during the @2 repeat: no step-0 evaluation in force); repeat 'recorded': False
    (the files moved, the STEP0_FIX save not made: no second commit_history entry; W 50 fr_step0_repeat); a cell
    spec 'step0': True on a pending cell (its step-0 evaluation ran and passed, the cell still running at the STOP);
    'step0_pending': role (that cell's step-0 evaluation failed at attempt 1, fail_pending_fix, the cell
    killed_by_gate and the later cells not_run_gate; the STOP that follows is final). Integration (IX-2): 'step0_fail'
    is that failure made final by fr/STEP0_NO_ERROR, as W 50 applies it: the gate files keep fail_pending_fix and only
    fr/state_end.json reads fail_final with no_error_found and the note. Integration review 1 (IX-4): 'gate_fr': True
    on a stopped fr writes gate FR as on a done one (a STOP held until gate FR was applied, W 50 N-F20); a stopped
    campaign.json holds the fr_outcome W 50 begin_stop records (the outcome the decisions fix, else null), or the
    scenario's 'fr_outcome_stop'."""
    s = dict(sc.get("fr") or {})
    s.setdefault("delta_meV", "-23.456")                  # default: FR-2 passes, delta_far(FA188) < 0
    cells = {r: dict((s.get("cells") or {}).get(r) or {}) for r in ("host", "V", "D", "DV")}
    fr = os.path.join(root, "fr")
    os.makedirs(os.path.join(fr, "raw"), exist_ok=True)
    members, rel, recs = {}, {}, {}
    ff, kill, pend = None, s.get("step0_fail") or s.get("step0_pending"), s.get("step0_pending")
    rep = s.get("repeat")
    if rep and rep["after"] == "fail_final":
        kill = rep["role"]
    if rep and rep["after"] == "stopped":
        cells[rep["role"]]["status"] = "absent"            # its a2/ moved aside; no record is archived
    s0_cells = {r: sp for sp, lab in eg.FR_STEP0_PAIRS.items() for r, l in eg.FR_QUARTET.items() if l == lab}
    stopped = s.get("status") in ("stopped", "running")
    s0_runs, fr_step0 = [], None
    for role in ("host", "V", "D", "DV"):
        lab = eg.FR_QUARTET[role]
        cs = cells[role]
        if ff is not None:                                 # after the first failure, a STOP or an unstarted cell
            st = cs.get("status", "absent" if ff["kind"] in ("pending", "absent") else "not_run_gate")
            reason = f"FR early stop at {ff['cell']} ({ff['kind']}; S2B section 2)" if ff["kind"] != "step0" else \
                f"FR step-0 {ff['outcome']}"
            if st != "absent":
                recs[lab] = write_stub(root, "fr", lab, st, reason)
            continue
        st = cs.get("status", "complete")
        if st == "absent":                                 # never started (no record), at a STOP
            ff = {"cell": lab, "kind": "absent"}
            continue
        if role in s0_cells and kill == role:              # killed by the step-0 gate: output set aside, unarchived
            o0 = "fail_pending_fix" if pend == role else "fail_final"
            recs[lab] = write_stub(root, "fr", lab, "killed_by_gate", f"step-0 {o0}",
                                   parts=[{"n": 1, "end": "killed"}])
            sp = s0_cells[role]
            dF = 0.731 if role == "V" else -0.902
            s0_runs.append((role, sp, dF, False))
            ff = {"cell": lab, "kind": "step0", "outcome": o0}
            fr_step0 = o0
            continue
        if st != "complete":
            recs[lab] = write_stub(root, "fr", lab, st, cs.get("reason"))
            if st == "pending" and cs.get("step0") and role in s0_cells:     # fix round 2: k = 0 done, step 0 passed
                s0_runs.append((role, s0_cells[role], 0.123, True))
            if st == "pending":
                ff = {"cell": lab, "kind": "pending"}
            else:
                ff = {"cell": lab, "kind": st}
            continue
        n = cs.get("n_config", FR_N[role])
        outcome = cs.get("outcome", "accepted_converged")
        drop = cs.get("drop")
        if role == "DV" and s.get("delta_meV") is not None and drop is None:
            o = {r: rel[eg.FR_QUARTET[r]] for r in ("host", "V", "D")}
            dr = lambda r: Decimal(o[r]["F"][-1]) - Decimal(o[r]["F"][0])
            drop = Decimal(s["delta_meV"]) / 1000 / Decimal(str(float(RY))) + dr("D") + dr("V") - dr("host")
        r_ = write_relaxation(root, ex, "fr", lab, n_config=n, outcome=outcome, end=cs.get("end"),
                              parts=cs.get("parts"), d0=cs.get("d0"), drop=drop, plateau_Ry=cs.get("plateau_Ry"),
                              restarts=cs.get("restarts"), reruns_from_zero=cs.get("reruns_from_zero", 0),
                              valid=cs.get("valid", True), failed=cs.get("failed"), check=cs.get("check", True),
                              fr=True, invariant_only=cs.get("invariant_only", False), operator=cs.get("operator",
                                                                                                        False),
                              members=members, workdir=workdir)
        rel[lab] = r_
        recs[lab] = r_["record"]
        if role in s0_cells and n:
            sp = s0_cells[role]
            dF = (float(r_["F"][0]) * float(RY) - float(sp_F(sp)) * float(RY)) * 1000.0
            s0_runs.append((role, sp, dF, abs(dF) <= 0.5))
        if outcome not in eg.END_ACCEPTED:
            ff = {"cell": lab, "kind": "end_rule"}
        elif not cs.get("check", True):
            ff = {"cell": lab, "kind": "check_not_evaluated"}
        elif not cs.get("valid", True):
            ff = {"cell": lab, "kind": "check"}
    write_tar(os.path.join(fr, "structures.tar.gz"), members)
    # fr_step0 evaluations (one cell each; RF-5): @2 is VA188, @4 is Cs188o0_vac; a repeat as scripts/49-50 write it
    decision0, last_sha, attempt = {}, None, 1          # the evaluations before the repeated one: attempt 1
    rep_role = rep["role"] if rep else None
    pre = [x for x in s0_runs if rep_role == "DV" and x[0] == "V"]
    for role, sp, dF, ok in s0_runs:
        gid = "gate:fr_step0@2" if role == "V" else "gate:fr_step0@4"
        if role == rep_role:
            _set_aside_attempt1(root, gid, sp, eg.FR_STEP0_PAIRS[sp], dict(decision0))
            decision0 = {**decision0, "attempts": 1, "outcome": "repeat_pending", "repeat": True,
                         "fix_note": FIX_NOTE, "attempt1": {"attempts": 1, "outcome": "fail_pending_fix",
                                                            "cell": eg.FR_STEP0_PAIRS[sp]}}
            attempt = 2
        outcome0 = "pass" if ok else ("fail_pending_fix" if pend == role else "fail_final")
        # integration (IX-2): a final failure at attempt 1 is fr/STEP0_NO_ERROR as W 50 applies it (preconditions,
        # N-FR6): scripts/49 records fail_pending_fix (the runner passes no no_error_found), and only the state, hence
        # fr/state_end.json, reads fail_final with no_error_found and the note
        no_error = outcome0 == "fail_final" and attempt == 1
        gate0 = "fail_pending_fix" if no_error else outcome0
        prev = dict(decision0)
        decision0 = {**prev, "attempts": attempt, "outcome": gate0, "repeat": attempt == 2,
                     "fix_note": prev.get("fix_note") if attempt == 2 else None, "cell": eg.FR_STEP0_PAIRS[sp]}
        res = {"cells": {sp: {"dF_meV": dF, "passed": ok, "reason": None}}, "attempt": attempt,
               "fix_note": decision0["fix_note"], "outcome": gate0, "tolerance_meV": 0.5}
        g = gate_file("fr_step0", "fr", res, {"fr_step0": decision0}, attempt=attempt)
        write_applied(root, "fr", gid, "fr_step0", g, "fr_step0")
        if no_error:
            decision0 = {**decision0, "outcome": "fail_final", "no_error_found": True,
                         "note": "2026-11-20 no error found"}
        man.setdefault("fr_step0", {})[sp] = {"dF_meV": dF, "passed": ok, "gid": gid}
        if not ok:
            fr_step0 = outcome0
            break
    if rep and rep["after"] == "stopped":                 # the STOP before the repeated cell reruns (R-1)
        assert rep_role == "V" or (rep_role == "DV" and pre), "a STOP during the repeat of @2 or @4"
        sp = s0_cells[rep_role]
        _set_aside_attempt1(root, "gate:fr_step0@2" if rep_role == "V" else "gate:fr_step0@4", sp,
                            eg.FR_STEP0_PAIRS[sp], dict(decision0))
        p0 = os.path.join(fr, "gates", "fr_step0.json")
        if os.path.exists(p0):
            os.remove(p0)                                  # the repeated gate's attempt-1 file: moved aside
        decision0 = {**decision0, "attempts": 1, "outcome": "repeat_pending", "repeat": True, "fix_note": FIX_NOTE,
                     "attempt1": {"attempts": 1, "outcome": "fail_pending_fix", "cell": eg.FR_STEP0_PAIRS[sp]}}
    # gate FR (not evaluated after a final step-0 failure, nor before FR ended)
    dec = None
    if fr_step0 not in ("fail_final", "fail_pending_fix") and (not stopped or s.get("gate_fr")):
        FR1 = ff is None
        FR2 = None
        if FR1:
            k0 = {r: rel[eg.FR_QUARTET[r]]["F"][0] for r in ("host", "V", "D", "DV")}
            fi = {r: rel[eg.FR_QUARTET[r]]["F"][-1] for r in ("host", "V", "D", "DV")}
            a1 = eb_float(k0["DV"], k0["D"], k0["V"], k0["host"])
            a2 = eb_float(fi["DV"], fi["D"], fi["V"], fi["host"])
            FR2 = {"Eb_A1_meV": a1, "Eb_A2_meV": a2, "delta_far_meV": a2 - a1, "bound_meV": 50.0,
                   "passed": abs(a2 - a1) <= 50.0}
            man["fr2"] = FR2
        fr2 = None if FR2 is None else FR2["passed"]
        ok = FR1 and fr2 is True
        dec = {"FR": {"outcome": "pass" if ok else "fail", "FR1": FR1, "FR2": fr2,
                      "part": None if ok else ("FR-1" if not FR1 else "FR-2"),
                      "cell": ff["cell"] if ff else None, "kind": ff["kind"] if ff else None}}
        res = {"cells": {}, "first_failure": ff, "end_rule_failed": [], "checks_failed": [],
               "cells_not_run": [l for l in eg.FR_ORDER if recs.get(l, {}).get("status") == "not_run_gate"],
               "invariant_only": [eg.FR_QUARTET[r] for r in cells if cells[r].get("invariant_only")],
               "a1_invalid_reported": [], "FR1": FR1, "FR2": FR2}
        if ff and ff["kind"] == "check":
            res["checks_failed"] = [f"{ff['cell']}: final geometry fails check(s) "
                                    f"{recs[ff['cell']]['validity_final']['failed']}"]
        elif ff:
            res["end_rule_failed"] = [f"{ff['cell']}: end rule"]
        write_applied(root, "fr", "gate:FR", "FR", gate_file("FR", "fr", res, dec), "FR")
    status = s.get("status") or "done"
    fo = None
    if status == "done":
        fo = eg.FR_OUTCOMES[3] if fr_step0 == "fail_final" else ("pass" if dec["FR"]["outcome"] == "pass" else
                                                                 f"fail ({dec['FR']['part']})")
    cj = {"schema": "s2-campaign-1", "campaign": "fr", "status": status, "commit": "e" * 40, "start_commit": "e" * 40,
          "commit_history": [{"from": "8" * 40, "to": "e" * 40, "note": "fr/CAMPAIGN_COMMIT", "time": "t",
                              "via": "fr/CAMPAIGN_COMMIT", "campaign": "fr"}], "phases": {}, "notes": []}
    if fo is not None:
        cj["fr_outcome"] = s.get("fr_outcome", fo)
    if status == "stopped":
        cj["stop_reason"] = s.get("stop_reason", "operator STOP (synthetic)")
        fos = (eg.FR_OUTCOMES[3] if fr_step0 == "fail_final" else None) if dec is None else \
            ("pass" if dec["FR"]["outcome"] == "pass" else f"fail ({dec['FR']['part']})")
        cj["fr_outcome"] = s.get("fr_outcome_stop", fos)          # IX-4: as W 50 begin_stop records it
    dump(os.path.join(fr, "campaign.json"), cj)
    if status == "done":
        st = {"commit": "8" * 40, "campaigns": {"c1": "done", "c2": "done", "fr": "done"},
              "campaign_commit": {"fr": "e" * 40}, "K3": "fail_replan", "Eb_A2_meV": 5555.5}
        if decision0:
            st["fr_step0"] = decision0
        if dec:
            st["FR"] = dec["FR"]
        if ff and ff["kind"] not in ("step0", "pending", "absent"):
            st["fr_stop"] = {"at": ff["cell"], "kind": ff["kind"], "time": "t"}
        dump(os.path.join(fr, "state_end.json"), st)
    man["fr"] = {"rel": rel, "recs": recs, "first_failure": ff, "decision": dec, "fr_step0": decision0,
                 "fr_outcome": fo, "status": status, "repeat": rep}
    return members


def _set_aside_attempt1(root, gid, sp, a2, prev):
    """The attempt-1 files of a repeated step-0 evaluation, as the archive holds them (fr/step0_attempt1/gates,
    gates_applied; W 50:4787-4788), with a canary dF: E never opens them (OpenAudit refuses step0_attempt1/)."""
    d0 = {**prev, "attempts": 1, "outcome": "fail_pending_fix", "repeat": False, "fix_note": None, "cell": a2}
    g = gate_file("fr_step0", "fr", {"cells": {sp: {"dF_meV": ATTEMPT1_CANARY, "passed": False, "reason": None}},
                                     "attempt": 1, "fix_note": None, "outcome": "fail_pending_fix",
                                     "tolerance_meV": 0.5}, {"fr_step0": d0})
    base = os.path.join(root, "fr", "step0_attempt1")
    write_applied(base, "", gid, "fr_step0", g, "fr_step0", inputs={"canary_dF_meV": ATTEMPT1_CANARY})


def build(root, ex, scenario=None):
    """The synthetic archive under root (c1, c2, fr; spec section 18). Returns the manifest of planted values."""
    sc = dict(scenario or {})
    os.makedirs(root, exist_ok=True)
    workdir = os.path.join(os.path.dirname(root), "workdir")
    os.makedirs(workdir, exist_ok=True)
    man = {"root": root, "scenario": sc}
    with open(os.path.join(root, "C3_OPERATIONS.md"), "w") as fh:          # RF-2: a regular file is allowed
        fh.write("# synthetic note\n")
    if sc.get("c1", True):
        build_c1(root, ex, man, workdir)
    if sc.get("c2", True):
        build_c2(root, ex, man, workdir, sc)
    if sc.get("fr", True) is not False:
        build_fr(root, ex, man, workdir, sc)
    return man


def build_min(root, ex, *, regions=(("B", 76), ("A", 188), ("B", 136)), cell=None, centres=None, starts=()):
    """A minimal c1 for one relaxation: smoke, upf_check, regions and the A1 start members of the given A2 labels."""
    q47, c46 = ex.q47, ex.c46
    workdir = os.path.join(os.path.dirname(root), "workdir")
    os.makedirs(workdir, exist_ok=True)
    c1 = os.path.join(root, "c1")
    dump(os.path.join(c1, "smoke.json"), {"schema": "s2-smoke-1", "mapping": MAPPING})
    dump(os.path.join(c1, "upf_check.json"),
         {"schema": "s2-upf-1", "passed": True,
          "files": {el: {"md5": q47.UPF_MD5_S1.get(el, "0" * 32)} for el in sorted(q47.PSEUDO_S2)}})
    for (L, j) in regions:
        dump(os.path.join(c1, "regions", f"m30_{L}{j}.json"),
             {"centres": centres or {"v": [6.71811919, 13.57856311, 9.685798],
                                     "site": [6.63524065, 6.60189266, 0.03674373]}})
    cellm = cell_matrix(q47) if cell is None else cell
    write_tar(os.path.join(c1, "structures.tar.gz"),
              {f"cells/{er.a1_start(lab)}/start.extxyz": extxyz_bytes(c46, SYM_A2, positions_fn(lab)(0), cellm,
                                                                      workdir) for lab in starts})
    return workdir


# ---------------------------------------------------------------- group A: the guard (spec 18 A; e_guard.py)
# The expected allow-lists, restated from S2B section 7 with amendment item 2 (not from e_guard), so that a change of
# TABLE is caught here: {(mode, kind): (files, get, get_by_file, is_none)}.
_RB = ("n_config", "converged_at_k", "k_last", "final_geometry.k", "final_geometry.sha256", "restarts",
       "reruns_from_zero", "status", "end_rule.outcome", "layout.ranks", "validity_final.valid",
       "validity_final.failed", "end_rule.end")
_DFR = tuple("decision.FR." + k for k in ("outcome", "FR1", "FR2", "part", "cell", "kind"))
_DS0 = tuple("decision.fr_step0." + k for k in ("attempts", "outcome", "repeat", "fix_note", "cell", "no_error_found",
                                                "note")) + \
    tuple("decision.fr_step0.attempt1." + k for k in ("attempts", "outcome", "cell"))
_H = ("s2r_m30_VB136", "s2r_m30_hostB136", "s2r_m30_Sr136o0_novac", "s2r_m30_Sr136o0_vac")
_F = ("s2r_m30_hostB76", "s2r_m30_VB76", "s2r_m30_Sr76o0_novac", "s2r_m30_Sr76o0_vac")
_FR = ("s2r_m30_hostA188", "s2r_m30_VA188", "s2r_m30_Cs188o0_novac", "s2r_m30_Cs188o0_vac")
EXPECTED = {
    ("far", "k3"): (("c2/gates/K3.json", "c2/gates_applied/gate_K3.gate.json"),
                    ("decision.K3", "result.checks_failed", "result.Eb_A2_meV.far"), {}, ("result.value_meV",)),
    ("far", "k3_marker"): (("c2/gates_applied/gate_K3.json",), ("decision.K3", "gate_file_sha256"), {}, ()),
    ("far", "a2_far"): (tuple(f"c2/raw/{x}.a2.json" for x in _F), _RB, {}, ()),
    ("far", "a2_hinge_counts"): (tuple(f"c2/raw/{x}.a2.json" for x in _H),
                                 ("n_config", "end_rule.outcome", "layout.ranks", "validity_final.valid",
                                  "validity_final.failed", "end_rule.end"), {}, ()),
    ("far", "campaign_c2"): (("c2/campaign.json",), ("commit", "status"), {}, ()),
    ("fr", "a2_fr"): (tuple(f"fr/raw/{x}.a2.json" for x in _FR),
                      _RB + ("validity_final.check5_reading", "validity_final.valid_as_written",
                             "validity_final.failed_as_written", "validity_final.invariant_only"), {}, ()),
    ("fr", "fr_gate"): (("fr/gates/FR.json", "fr/gates_applied/gate_FR.gate.json"),
                        _DFR + ("result.checks_failed", "result.end_rule_failed", "result.cells_not_run",
                                "result.FR2.Eb_A1_meV", "result.FR2.Eb_A2_meV", "result.FR2.delta_far_meV",
                                "result.invariant_only"), {}, ()),
    ("fr", "fr_marker"): (("fr/gates_applied/gate_FR.json",), _DFR + ("gate_file_sha256",), {}, ()),
    ("fr", "fr_step0_gate"): (("fr/gates/fr_step0.json", "fr/gates_applied/gate_fr_step0_2.gate.json",
                               "fr/gates_applied/gate_fr_step0_4.gate.json"), _DS0,
                              {"fr/gates_applied/gate_fr_step0_2.gate.json":
                               ("result.cells.s2_m30_VA188.dF_meV", "result.cells.s2_m30_VA188.passed"),
                               "fr/gates_applied/gate_fr_step0_4.gate.json":
                               ("result.cells.s2_m30_Cs188o0_vac.dF_meV", "result.cells.s2_m30_Cs188o0_vac.passed"),
                               "fr/gates/fr_step0.json":
                               ("result.cells.s2_m30_Cs188o0_vac.dF_meV", "result.cells.s2_m30_Cs188o0_vac.passed")},
                              ()),
    ("fr", "fr_step0_marker"): (("fr/gates_applied/gate_fr_step0_2.json", "fr/gates_applied/gate_fr_step0_4.json"),
                                _DS0 + ("gate_file_sha256",), {}, ()),
    ("fr", "campaign_fr"): (("fr/campaign.json",), ("status", "commit", "start_commit", "fr_outcome", "stop_reason",
                                                    "commit_history[].to"), {}, ()),
    ("fr", "state_fr"): (("fr/state_end.json",), ("commit", "campaigns.fr", "campaign_commit.fr", "fr_step0.attempts",
                                                  "fr_step0.outcome", "fr_step0.cell",
                                                  "fr_step0.no_error_found") +              # integration (IX-2)
                         tuple("FR." + k for k in ("outcome", "FR1", "FR2", "part", "cell", "kind")) +
                         ("fr_stop.at", "fr_stop.kind"), {}, ()),
    ("hinge", "k3"): (("c2/gates/K3.json", "c2/gates_applied/gate_K3.gate.json"),
                      ("decision.K3", "result.checks_failed", "result.Eb_A2_meV.far", "result.Eb_A2_meV.hinge"), {},
                      ("result.value_meV",)),
    ("hinge", "a2_hinge"): (tuple(f"c2/raw/{x}.a2.json" for x in _H), _RB, {}, ()),
    ("hinge", "step0_c2"): (("c2/gates/step0.json", "c2/gates_applied/gate_step0_1.gate.json",
                             "c2/gates_applied/gate_step0_4.gate.json"), ("decision.step0.outcome",),
                            {"c2/gates_applied/gate_step0_1.gate.json":
                             ("result.cells.s2_m30_VB136.dF_meV", "result.cells.s2_m30_VB136.passed"),
                             "c2/gates_applied/gate_step0_4.gate.json":
                             ("result.cells.s2_m30_Sr136o0_vac.dF_meV", "result.cells.s2_m30_Sr136o0_vac.passed"),
                             "c2/gates/step0.json":
                             ("result.cells.s2_m30_Sr136o0_vac.dF_meV", "result.cells.s2_m30_Sr136o0_vac.passed")}, ()),
}
FIG_WITHHELD = frozenset({"dF_200_180_meV", "value_meV", "Eb_A2_meV"})                     # figures/fig_s2_c2_a2.py
S2B_ENERGY = ("Eb_A1_meV", "Eb_A2_meV", "delta_far_meV", "dF_meV", "F_sp_eV", "F_k0_eV", "F_final_eV")


def _sample(path):
    last = path.split(".")[-1]
    return {"status": "complete", "n_config": 165, "converged_at_k": 164, "k_last": 164, "k": 164,
            "sha256": "1" * 64, "restarts": 0, "reruns_from_zero": 0, "outcome": "fail", "end": "converged",
            "ranks": 64, "valid": False, "failed": [5], "check5_reading": "invariant", "valid_as_written": False,
            "failed_as_written": [5], "invariant_only": ["s2r_m30_VA188"] if path.startswith("result") else True,
            "K3": "fail_replan", "checks_failed": ["s2r_m30_VB76: final geometry fails check(s) [5]"],
            "far": 6543.21, "hinge": 7654.321, "gate_file_sha256": "5" * 64, "FR1": False, "FR2": None,
            "part": "FR-1", "cell": "s2r_m30_VA188", "kind": "check", "end_rule_failed": [],
            "cells_not_run": ["s2r_m30_Cs188o0_novac"], "Eb_A1_meV": -12.5, "Eb_A2_meV": -30.25,
            "delta_far_meV": -17.75, "dF_meV": 0.123, "passed": True, "attempts": 1, "repeat": False,
            "fix_note": None, "no_error_found": True, "note": "n", "commit": "e" * 40, "start_commit": "e" * 40,
            "fr_outcome": "fail (FR-1)", "stop_reason": "r", "fr": "done", "at": "s2r_m30_VA188",
            "value_meV": None}.get(last, f"v:{path}")


def _set(d, path, value):
    segs = path.split(".")
    for s in segs[:-1]:
        d = d.setdefault(s, {})
    d[segs[-1]] = value


def synth_file(mode, kind, rel):
    """A synthetic JSON holding every listed leaf of one file, the WITHHELD and S2b energy names as canaries at
    several depths and inside list elements, and unlisted siblings beside every listed parent."""
    files, get, byf, isn = EXPECTED[(mode, kind)]
    d = {}
    listed = list(get) + list(byf.get(rel, ()))
    for p in listed:
        if "[]" in p:
            continue
        _set(d, p, _sample(p))
    for p in isn:
        _set(d, p, None)
    if any("[]" in p for p in listed):
        d["commit_history"] = [{"from": "8" * 40, "to": "e" * 40, "note": "x", "dF_meV": 9.5},
                               {"from": "e" * 40, "to": "f" * 40, "note": "y", "F_k0_eV": 9.6}]
    names = sorted(FIG_WITHHELD | set(S2B_ENERGY))

    def plant(node, depth):
        if not isinstance(node, dict):
            return
        for k in list(node):
            plant(node[k], depth + 1)
        for n in names:
            node.setdefault(n, 100.0 + depth)
        node["zz_unlisted"] = depth
        node["zz_unlisted_obj"] = {"x": 1, **{n: 200.0 + depth for n in names}}
        node["zz_canary_list"] = [{n: 300.0 + depth for n in names}, "s"]
    plant(d, 0)
    for k in ("state_in", "inputs_in", "c1_in", "inputs_opened", "opened", "inputs_digest"):
        d[k] = {"decision": {"K3": "x"}, "dF_meV": 1.0} if k != "inputs_opened" else [{"dF_meV": 1.0}]
    return d, set(listed), set(isn)


def dotted(x, pre=""):
    out = []
    if isinstance(x, dict):
        for k, v in x.items():
            p = f"{pre}.{k}" if pre else k
            out.append(p)
            out += dotted(v, p)
    return out


def _value_at(d, path):
    if "[]" in path:
        a, b = path.split("[].")
        return [e[b] for e in d[a]]
    for s in path.split("."):
        d = d[s]
    return d


@case("A1", "A", mutants=(
        # an extra leaf on a list (TABLE drift): the pinned EXPECTED lists catch it
        ("table_extra_leaf", lambda fx: patched(eg.TABLE["far"]["a2_far"], "get",
                                                eg.TABLE["far"]["a2_far"]["get"] + ("end_rule.reason",))),
        # get() without the allow-list test: unlisted siblings and canaries become readable
        ("get_no_allow_list", lambda fx: patched(eg, "leaves", lambda mode, kind, rel, which="get": _AnyPath())),
        # a step-0 leaf of the @2 copy granted to every file of the kind (RF-5)
        ("step0_leaf_all_files", lambda fx: patched(eg.TABLE["fr"]["fr_step0_gate"], "get",
                                                    eg.TABLE["fr"]["fr_step0_gate"]["get"] +
                                                    ("result.cells.s2_m30_VA188.dF_meV",)))))
def case_a1(fx):
    """Every (mode, kind, file) of TABLE: get(p) succeeds iff p is a listed leaf, on a file holding every listed leaf,
    every fig.WITHHELD and S2b energy name as canaries at several depths and in list elements, and unlisted siblings;
    the set of paths read equals the list (closed both ways); TABLE equals the plan's lists (EXPECTED)."""
    got = {(m, k): (t["files"], tuple(t.get("get", ())), {f: tuple(v) for f, v in t.get("get_by_file", {}).items()},
                    tuple(t.get("is_none", ()))) for m, ks in eg.TABLE.items() for k, t in ks.items()}
    norm = lambda e: (tuple(e[0]), frozenset(e[1]), {f: frozenset(v) for f, v in e[2].items()}, frozenset(e[3]))
    assert {k: norm(v) for k, v in got.items()} == {k: norm(v) for k, v in EXPECTED.items()}, \
        sorted(set(got) ^ set(EXPECTED)) or [k for k in got if norm(got[k]) != norm(EXPECTED.get(k, ((), (), {}, ())))]
    assert eg.WITHHELD == FIG_WITHHELD and set(S2B_ENERGY) | FIG_WITHHELD == eg.WITHHELD_S2B
    n_read = n_refused = 0
    for (mode, kind), (files, get, byf, isn) in EXPECTED.items():
        for rel in files:
            d, listed, isn_set = synth_file(mode, kind, rel)
            g = eg.EGuarded(copy.deepcopy(d), rel, mode=mode, kind=kind)
            paths = set(dotted(d)) | listed | isn_set | {"", "x", "decision", "result", "result.FR2", "zz_unlisted"}
            read = set()
            for p in sorted(paths):
                try:
                    v = g.get(p)
                except Blinded:
                    n_refused += 1
                    continue
                read.add(p)
                n_read += 1
                want = _value_at(d, p)
                assert v == want and (not isinstance(v, list) or v is not want), (rel, p)
            assert read == listed, (mode, kind, rel, sorted(read ^ listed))
            for p in sorted(paths):
                if p in isn_set:
                    assert g.is_none(p) is True
                else:
                    raises(Blinded, g.is_none, p)
    assert n_read > 150 and n_refused > 3000, (n_read, n_refused)


class _AnyPath(frozenset):
    def __contains__(self, x):
        return True


@case("A2", "A", mutants=(
        # deepcopy no longer refused (the fig.Guarded default would copy the raw dict out)
        ("deepcopy_allowed", lambda fx: patched(eg.EGuarded, "__deepcopy__",
                                                lambda self, memo: eg.EGuarded({}, "x", mode="far", kind="k3"))),
        # a parent (dict) handed out by get
        ("parent_allowed", lambda fx: patched(eg, "_leaf", lambda x, rel, path: x)),
        # ABSENT printable
        ("absent_printable", lambda fx: patched(type(eg.ABSENT), "__repr__", lambda self: "ABSENT"))))
def case_a2(fx):
    """Parents, has, open, _wrap, repr, str, ==, in, iteration, len, keys, items, values, copy.copy, copy.deepcopy and
    pickle.dumps all raise Blinded; ABSENT and FILE_ABSENT cannot be printed, formatted or tested for truth; a listed
    leaf holding a list of floats is INT-STRUCT (fix round 1)."""
    d = {"decision": {"K3": "fail_replan"}, "result": {"checks_failed": ["a"], "Eb_A2_meV": {"far": 1.0},
                                                       "value_meV": None}}
    g = eg.EGuarded(d, "c2/gates/K3.json", mode="far", kind="k3")
    tests = [lambda: g.has("decision"), lambda: g.open(), lambda: g._wrap({}, "x"), lambda: repr(g), lambda: str(g),
             lambda: g == g, lambda: "decision" in g, lambda: list(g), lambda: iter(g), lambda: len(g),
             lambda: g.keys(), lambda: g.items(), lambda: g.values(), lambda: copy.copy(g), lambda: copy.deepcopy(g),
             lambda: pickle.dumps(g), lambda: f"{g}", lambda: hash(g) and None]
    n = 0
    for t in tests:
        try:
            t()
        except (Blinded, TypeError) as e:
            assert isinstance(e, Blinded) or "unhashable" in str(e), t
            n += 1
            continue
        raise AssertionError("a guarded object was copied, printed, compared or iterated")
    assert n == len(tests)
    g2 = eg.EGuarded({"decision": {"K3": "x"}, "result": {"checks_failed": [{"a": 1}], "Eb_A2_meV": {"far": {"x": 1}}}},
                     "c2/gates/K3.json", mode="far", kind="k3")
    raises(Blinded, g2.get, "result.checks_failed")             # a list holding a dict is a parent
    raises(Blinded, g2.get, "result.Eb_A2_meV.far")             # a dict is a parent
    g3 = eg.EGuarded({"decision": {"K3": "x"}, "result": {"checks_failed": [1.5, 2.5]}}, "c2/gates/K3.json",
                     mode="far", kind="k3")
    int_fail("INT-STRUCT", g3.get, "result.checks_failed")      # fix round 1: a list of floats is no listed leaf
    g4 = eg.EGuarded({"commit_history": [{"to": ["a"]}]}, "fr/campaign.json", mode="fr", kind="campaign_fr")
    int_fail("INT-STRUCT", g4.get, "commit_history[].to")       # fix round 2 (G07): a list in a projected list
    for s in (eg.ABSENT, eg.FILE_ABSENT):
        for t in (repr, str, bool, lambda x: f"{x}", lambda x: pickle.dumps(x), len, list, float, int):
            raises(Blinded, t, s)
        assert copy.deepcopy(s) is s and copy.copy(s) is s
    assert g.get("decision.K3") == "fail_replan"


@case("A3", "A", mutants=(
        # eg_load without the file-list test: any path of a known kind would load
        ("no_file_list", lambda fx: patched(eg.TABLE["far"]["k3"], "files", _AnyTuple())),
        # eg_load without the hinge-mode test
        ("hinge_without_allowance", lambda fx: patched(eg, "eg_load", _eg_load_force_hinge))))
def case_a3(fx):
    """eg_load refuses *.inputs.json, a file outside the kind's list, a kind of another mode, the hinge kinds in far
    mode, hinge mode before the hinge allowance, and FR kinds in a C2 call; an absent listed file is FILE_ABSENT."""
    root = os.path.join(fx.workdir("a3"), "s2")
    for rel in ("c2/gates/K3.json", "c2/gates_applied/gate_K3.inputs.json", "c2/gates/K3x.json",
                "c2/raw/s2r_m30_VB136.a2.json", "fr/gates/FR.json"):
        dump(os.path.join(root, rel), {"decision": {"K3": "x"}, "n_config": 1, "end_rule": {"outcome": "x"}})
    L = er.ELayout(root)
    with eg.OpenAudit(root) as audit:
        load = lambda c, r, m, k: eg.eg_load(L, c, r, mode=m, kind=k, audit=audit)
        assert isinstance(load("c2", "gates/K3.json", "far", "k3"), eg.EGuarded)
        raises(Blinded, load, "c2", "gates_applied/gate_K3.inputs.json", "far", "k3")
        raises(Blinded, load, "c2", "gates/K3x.json", "far", "k3")        # not on the list (the hook allows it)
        raises(Blinded, load, "c2", "gates/K3.json", "far", "fr_gate")          # an FR kind in a C2 call
        raises(Blinded, load, "c2", "gates/K3.json", "fr", "fr_gate")
        raises(Blinded, load, "c2", "raw/s2r_m30_VB136.a2.json", "far", "a2_hinge")
        raises(Blinded, load, "c2", "raw/s2r_m30_VB136.a2.json", "far", "a2_far")
        raises(Blinded, load, "c2", "raw/s2r_m30_VB136.a2.json", "hinge", "a2_hinge")   # before open_hinge
        g = load("c2", "raw/s2r_m30_VB136.a2.json", "far", "a2_hinge_counts")
        assert g.get("n_config") == 1
        raises(Blinded, g.get, "status")
        assert load("fr", "gates/fr_step0.json", "fr", "fr_step0_gate") is eg.FILE_ABSENT
        raises(Blinded, load, "c3", "gates/K3.json", "far", "k3")
        audit.open_hinge()
        assert load("c2", "raw/s2r_m30_VB136.a2.json", "hinge", "a2_hinge").get("n_config") == 1
    raises(EError, eg.eg_load, L, "c2", "gates/K3.json", mode="far", kind="k3")    # outside OpenAudit


class _AnyTuple(tuple):
    def __contains__(self, x):
        return True


_orig_eg_load = eg.eg_load


def _eg_load_force_hinge(L, c, relpath, *, mode, kind, audit=None):
    a = audit or eg.OpenAudit.current()
    old, a.hinge = a.hinge, True
    try:
        return _orig_eg_load(L, c, relpath, mode=mode, kind=kind, audit=a)
    finally:
        a.hinge = old


@case("A4", "A", mutants=(
        # is_none granted on every path
        ("is_none_anywhere", lambda fx: patched(eg, "leaves", _leaves_isnone_everywhere)),
        # is_none answering 'is ABSENT' as None (an absent value_meV would pass INT-K3-NULL)
        ("absent_is_none", lambda fx: patched(eg.EGuarded, "is_none", _is_none_absent_true))))
def case_a4(fx):
    """is_none works only for result.value_meV of k3, returns a bool and never the value (1111.111 appears in no
    message); an absent value_meV is INT-STRUCT. (The run-level part, 'a run with value_meV = 1111.111 exits 3 with
    INT-K3-NULL and 1111.111 is absent from the output', is engineer B's: it needs e_eval.)"""
    for v, want in ((None, True), (1111.111, False)):
        d = {"decision": {"K3": "fail_replan"}, "result": {"value_meV": v, "checks_failed": [], "x_meV": v}}
        for mode in ("far", "hinge"):
            g = eg.EGuarded(d, "c2/gates/K3.json", mode=mode, kind="k3")
            assert g.is_none("result.value_meV") is want
            raises(Blinded, g.get, "result.value_meV")
            for p in ("result.x_meV", "decision.K3", "result.checks_failed", "result", "value_meV"):
                e = raises(Blinded, g.is_none, p)
                assert "1111.111" not in str(e)
    g = eg.EGuarded({"decision": {"K3": "x"}, "result": {}}, "c2/gates/K3.json", mode="far", kind="k3")
    int_fail("INT-STRUCT", g.is_none, "result.value_meV")
    g = eg.EGuarded({"n_config": None}, "c2/raw/s2r_m30_VB76.a2.json", mode="far", kind="a2_far")
    raises(Blinded, g.is_none, "n_config")


def _leaves_isnone_everywhere(mode, kind, rel, which="get"):
    return _AnyPath() if which == "is_none" else frozenset(eg.TABLE[mode][kind].get("get", ()))


def _is_none_absent_true(self, path):
    try:
        return eg.EGuarded.__dict__["get"](self, path) is None
    except Exception:
        return True


def _planted_tables():
    """One violation of each rule R1-R6, each on a copy of TABLE."""
    def mod(fn):
        t = copy.deepcopy(eg.TABLE)
        fn(t)
        return t
    add = lambda m, k, p, which="get": (lambda t: t[m][k].__setitem__(which, tuple(t[m][k].get(which, ())) + (p,)))
    return {
        "R1 state_in": mod(add("far", "k3", "state_in.K3")),
        "R1 inputs_in": mod(add("fr", "fr_gate", "inputs_in.cells")),
        "R1 opened": mod(add("fr", "fr_gate", "opened.sha256")),
        "R2 plateau": mod(add("far", "a2_far", "end_rule.dF_200_180_meV")),
        "R3 value_meV in get": mod(add("far", "k3", "result.value_meV")),
        "R3 Eb_A2_meV last": mod(add("far", "k3", "result.Eb_A2_meV")),
        "R3 F_k0_eV": mod(add("fr", "a2_fr", "inputs.F_k0_eV")),
        "R3 value_meV is_none elsewhere": mod(add("far", "a2_far", "value_meV", "is_none")),
        "R4 hinge in far": mod(add("far", "k3", "result.Eb_A2_meV.hinge")),
        "R4 far in fr": mod(lambda t: t["fr"].__setitem__("k3", {"files": ("c2/gates/K3.json",),
                                                                 "get": ("result.Eb_A2_meV.far",)})),
        "R4 FR2 outside fr": mod(add("far", "k3", "result.FR2.delta_far_meV")),
        "R4 fr step-0 dF in hinge": mod(add("hinge", "step0_c2", "result.cells.s2_m30_VA188.dF_meV")),
        "R4 C2 step-0 dF in fr": mod(add("fr", "fr_step0_gate", "result.cells.s2_m30_VB136.dF_meV")),
        "R4 C2 step-0 dF in far": mod(lambda t: t["far"].__setitem__(
            "s0", {"files": ("c2/gates/step0.json",), "get": ("result.cells.s2_m30_VB136.dF_meV",)})),
        "R5 Eb_A2_meV parent": mod(add("far", "a2_far", "x.Eb_A2_meV.far")),
        "R6 glob": mod(lambda t: t["far"]["a2_far"].__setitem__("files", ("c2/raw/*.a2.json",))),
        "R6 inputs file": mod(lambda t: t["far"]["k3"].__setitem__("files", ("c2/gates_applied/gate_K3.inputs.json",))),
        "R6 validity record": mod(lambda t: t["far"]["a2_far"].__setitem__(
            "files", ("c2/raw/s2r_m30_VB76.validity_final.json",))),
        "R6 c3 campaign": mod(lambda t: t["far"]["k3"].__setitem__("files", ("c3/gates/K3.json",))),
        # fix round 2 (G05, G06): planted beside the listed files, so that no other R6 test fires first
        "R6 attempt1": mod(lambda t: t["fr"]["fr_step0_gate"].__setitem__(
            "files", t["fr"]["fr_step0_gate"]["files"] + ("fr/step0_attempt1/gates/fr_step0.json",))),
        "R6 discarded": mod(lambda t: t["fr"]["fr_step0_gate"].__setitem__(
            "files", t["fr"]["fr_step0_gate"]["files"] + ("fr/discarded/step0_attempt1_1/gates/fr_step0.json",))),
        "R3 value_meV parent": mod(add("far", "k3", "result.value_meV.x")),
        "R6 wildcard path": mod(add("fr", "fr_gate", "decision.*")),
    }


A5_EXACT = {"R6 attempt1": "R6 fr/step0_attempt1/gates/fr_step0.json",
            "R6 discarded": "R6 fr/discarded/step0_attempt1_1/gates/fr_step0.json",
            "R3 value_meV parent": "R3 result.value_meV.x"}     # fix round 2: the rule itself, not a neighbour


@case("A5", "A", mutants=(
        # check_table without the R4 test
        ("no_R4", lambda fx: patched(eg, "check_table", _check_table_without("R4"))),
        # check_table without the R1 test
        ("no_R1", lambda fx: patched(eg, "check_table", _check_table_without("R1")))))
def case_a5(fx):
    """R1-R6 hold on TABLE; each planted violation (a copy of TABLE) raises INT-GUARD naming its rule; the module
    calls check_table(TABLE) at import (module-level statement)."""
    assert eg.check_table(eg.TABLE) is True
    for name, t in _planted_tables().items():
        e = int_fail("INT-GUARD", eg.check_table, t)
        assert e.key.startswith(name.split()[0]) and e.key == A5_EXACT.get(name, e.key), (name, e.key)
    with open(os.path.join(HERE, "e_guard.py")) as fh:
        tree = __import__("ast").parse(fh.read())
    calls = [n for n in tree.body if isinstance(n, __import__("ast").Expr) and
             getattr(getattr(n.value, "func", None), "id", None) == "check_table"]
    assert len(calls) == 1 and calls[0].value.args[0].id == "TABLE"


def _check_table_without(rule):
    real = eg.check_table

    def f(table):
        try:
            return real(table)
        except EIntegrity as e:
            if e.key.startswith(rule):
                return True
            raise
    return f


@case("A6", "A", mutants=(
        # .hinge planted on the far list
        ("hinge_in_far", lambda fx: patched(eg.TABLE["far"]["k3"], "get",
                                            eg.TABLE["far"]["k3"]["get"] + ("result.Eb_A2_meV.hinge",))),
        # FR-2 values on a far kind
        ("fr2_in_far", lambda fx: patched(eg.TABLE["far"]["k3"], "get",
                                          eg.TABLE["far"]["k3"]["get"] + ("result.FR2.Eb_A2_meV",)))))
def case_a6(fx):
    """.far reads in far and hinge modes; .hinge raises in far mode and reads in hinge mode; result.FR2.* raises
    outside fr mode; the C2 step-0 dF reads only in hinge mode and the fr step-0 dF only in fr mode (RF-7)."""
    d = {"decision": {"K3": "fail_replan"}, "result": {"Eb_A2_meV": {"far": -1.5, "hinge": 7654.321},
                                                       "FR2": {"Eb_A2_meV": 2.5, "Eb_A1_meV": 1.0},
                                                       "checks_failed": [], "value_meV": None}}
    for mode in ("far", "hinge"):
        assert eg.EGuarded(d, "c2/gates/K3.json", mode=mode, kind="k3").get("result.Eb_A2_meV.far") == -1.5
    raises(Blinded, eg.EGuarded(d, "c2/gates/K3.json", mode="far", kind="k3").get, "result.Eb_A2_meV.hinge")
    assert eg.EGuarded(d, "c2/gates/K3.json", mode="hinge", kind="k3").get("result.Eb_A2_meV.hinge") == 7654.321
    for mode in ("far", "hinge"):
        for p in ("result.FR2.Eb_A2_meV", "result.FR2.Eb_A1_meV"):
            raises(Blinded, eg.EGuarded(d, "c2/gates/K3.json", mode=mode, kind="k3").get, p)
    assert eg.EGuarded(d, "fr/gates/FR.json", mode="fr", kind="fr_gate").get("result.FR2.Eb_A2_meV") == 2.5
    s0 = {"decision": {"step0": {"outcome": "pass"}}, "result": {"cells": {"s2_m30_VB136": {"dF_meV": 0.1,
                                                                                            "passed": True}}}}
    rel1 = "c2/gates_applied/gate_step0_1.gate.json"
    assert eg.EGuarded(s0, rel1, mode="hinge", kind="step0_c2").get("result.cells.s2_m30_VB136.dF_meV") == 0.1
    for mode, kind in (("far", "k3"), ("fr", "fr_step0_gate")):
        raises(Blinded, eg.EGuarded(s0, rel1, mode=mode, kind=kind).get, "result.cells.s2_m30_VB136.dF_meV")
    raises(Blinded, eg.EGuarded(s0, "c2/gates/step0.json", mode="hinge", kind="step0_c2").get,
           "result.cells.s2_m30_VB136.dF_meV")                    # the @4 copy holds only Sr136o0_vac (RF-5)


@case("A7", "A", mutants=(
        # record() without the Pb136 test
        ("pb136_record_open", lambda fx: patched(eg, "PB136_WIDS", ())),
        # sp_full allowing the Pb136 single points in block 3
        ("pb136_sp_block3", lambda fx: patched(eg, "BLOCK3_SP", eg.BLOCK3_SP | frozenset(eg.PB136_SP))),
        # sp_full allowing G1 and spin outputs
        ("never_sp_allowed", lambda fx: patched(eg, "NEVER_SP", ()))))
def case_a7(fx):
    """C1Access: record(blind=False) raises in blocks 1 and 2 and for each Pb136 wid outside block 5 of a hinge read;
    sp_full raises for the Pb136, G1 and spin labels outside their allowance; there is no force-only reader (OP-1).
    Fix round 1: a Pb136 output logged with the hinge allowance but in block 3 is INT-PB136-RAW at exit; a blind
    record holding E_mace_eV is refused at load (INT-STRUCT)."""
    root, man = fx.tree()
    with session(fx, root) as (L, audit, ctx):
        c1 = eg.C1Access(L, fx.ex.c46, fx.ex.q47, audit, ctx.reads).load_census()
        w = "s2_m30_VB76"
        for blk in (1, 2, None):
            raises(Blinded, c1.record, w, blind=False, block=blk)
        assert "E_mace_eV" in json.dumps(c1.record(w, blind=False, block=3))
        assert "E_mace_eV" not in json.dumps(c1.record(w, blind=True, block=1))
        for pw in eg.PB136_WIDS:
            for blk in (3, 4, 5):
                raises(Blinded, c1.record, pw, blind=False, block=blk)
            assert "E_mace_eV" not in json.dumps(c1.record(pw, blind=True, block=3))
        for lab in eg.PB136_SP:
            for blk in (1, 2, 3, 4, 5):
                raises(Blinded, c1.sp_full, lab, block=blk)
        for lab in eg.NEVER_SP:
            for blk in (1, 3, 5):
                raises(Blinded, c1.sp_full, lab, block=blk)
        assert c1.sp_full("s2_m30_VB76", block=3)["F_eV"] is not None
        raises(Blinded, open, os.path.join(root, "c1", "raw", "s2_m30_VB136.out.gz"))   # the hook, any reader
        raises(Blinded, open, os.path.join(root, "c1", "raw", "s2g1_m30_host_e60.out.gz"))
        audit.open_hinge(); audit.set_block(5)                    # the hook allows: C1Access alone must refuse
        own = lambda e: "OpenAudit" not in str(e)
        for blk in (1, 3, 4):
            raises(Blinded, c1.sp_full, "s2_m30_VB136", block=blk, check=own)
            raises(Blinded, c1.record, "s2_m30_Sr136p0_vac", blind=False, block=blk, check=own)
        raises(Blinded, c1.sp_full, "s2_m30_VB136", block=5, check=own)        # C1Access not in hinge mode
        raises(Blinded, c1.record, "s2_m30_VB136", blind=False, block=5, check=own)
        raises(Blinded, open, os.path.join(root, "c1", "raw", "s2spin_m30_Cl175o0_vac.out.gz"))
        c1.open_hinge()
        for pw in eg.PB136_WIDS:                                  # fix round 2 (G08): hinge open, blocks 3 and 4
            for blk in (3, 4):
                raises(Blinded, c1.record, pw, blind=False, block=blk, check=own)
        assert "E_mace_eV" in json.dumps(c1.record("s2_m30_VB136", blind=False, block=5))
        assert c1.sp_full("s2_m30_VB136", block=5)["F_eV"] is not None
        raises(Blinded, c1.sp_full, "s2spin_m30_Ca76o0_vac", block=5)
        assert not hasattr(c1, "sp_forces") and not hasattr(eg, "PB136_FORCES_IN_BLOCK3")
        assert c1.assert_closed("exit")
    with session(fx, root) as (L, audit, ctx):                    # the exit audit of an illegal blind=False load
        c1 = eg.C1Access(L, fx.ex.c46, fx.ex.q47, audit, ctx.reads).load_census()
        c1.log.append(("s2_m30_VB136", False, 3))
        int_fail("INT-PB136-REC", c1.assert_closed, "exit")
    with session(fx, root) as (L, audit, ctx):                    # fix round 1: a Pb136 output opened with the
        c1 = eg.C1Access(L, fx.ex.c46, fx.ex.q47, audit, ctx.reads).load_census()   # hinge allowance, in block 3
        audit.log["/planted/c1/raw/s2_m30_VB136.out.gz"] = {"rel": "c1/raw/s2_m30_VB136.out.gz", "base": "root",
                                                           "sha256": "0" * 64, "block": 3, "hinge": True, "n": 1,
                                                           "via": None}
        int_fail("INT-PB136-RAW", c1.assert_closed, "exit")
    orig = fx.ex.c46.load_record

    def leaky(path, blind=True):                                  # a blind record holding E_mace_eV
        rec = orig(path, blind=blind)
        return dict(rec, relax={"E_mace_eV": -1.0}) if blind and path.endswith("s2_m30_VB76.json") else rec
    with session(fx, root) as (L, audit, ctx), patched(fx.ex.c46, "load_record", leaky):
        int_fail("INT-STRUCT", eg.C1Access(L, fx.ex.c46, fx.ex.q47, audit, ctx.reads).load_census)


@case("A8", "A", mutants=(
        # the MACE walk misses list elements (the host stage leaves)
        ("mace_walk_no_lists", lambda fx: patched(er, "mace_leaves", _mace_leaves_no_lists)),
        # the table builder keeps the Pb136 records in block 3
        ("pb136_in_block3", lambda fx: patched(eg, "BLOCK3_CLASSES", eg.BLOCK3_CLASSES + ("pb136",)))))
def case_a8(fx):
    """MACE canary: the block-3 ledger holds every planted non-Pb136 E_mace_eV exactly (161 leaves of 155 records) and
    no Pb136 canary; c46.load_record (blind) returns no E_mace_eV at any depth; g49.Reader(..., evaluation=False)
    .record passes its no-MACE assertion; fig.guarded(c2 record).get('end_rule').get('dF_200_180_meV') raises. (The
    printing of the ledger with L_MACE is engineer B's block 3.)"""
    root, man = fx.tree()
    ex = fx.ex
    with session(fx, root) as (L, audit, ctx):
        c1 = eg.C1Access(L, ex.c46, ex.q47, audit, ctx.reads).load_census()
        T, ledger = er.build_c1_table(c1, ctx)
    want = {(w, p, v) for w, lv in man["c1_mace"].items() if man["c1_classes"][w] != "pb136" for p, v in lv}
    got = {(r["wid"], p, v) for r in ledger for p, v in r["mace"]}
    assert got == want and len(got) == eg.MACE_LEAVES_BLOCK3 and len(ledger) == 155, (len(got), len(ledger))
    order = [r["class"] for r in ledger]
    assert order == sorted(order, key=eg.BLOCK3_CLASSES.index)
    assert not any(str(PB136_MACE)[:10] in repr(r) for r in ledger)
    for w in ("s2_m30_host", "s2_m30_Cs188p1_novac", "s2_m30_VB136"):
        assert "E_mace_eV" not in json.dumps(ex.c46.load_record(os.path.join(root, "c1", "records", f"{w}.json")))
    lay = ex.c46.Layout(kind="archive", root=root)
    r = ex.g49.Reader(lay, "c1", {"records": {"s2_m30_host"}}, evaluation=False).record("s2_m30_host")
    assert r["work_id"] == "s2_m30_host" and "E_mace_eV" not in json.dumps(r)
    gfig = eg.fig.guarded(os.path.join(root, "c2", "raw", "s2r_m30_VB76.a2.json"))
    raises(Blinded, lambda: gfig.get("end_rule").get("dF_200_180_meV"))


def _mace_leaves_no_lists(rec, pre=""):
    out = []
    if isinstance(rec, dict):
        for k, v in rec.items():
            p = f"{pre}.{k}" if pre else k
            out += [(p, v)] if k == "E_mace_eV" else _mace_leaves_no_lists(v, p)
    return out


A9_SOURCE_EDIT = []        # (old, new) edits of the e_selftest.py copied for A9's run outside .claude/worktrees
A9_OUTSIDE = "E_SELFTEST_A9_OUTSIDE"                     # set in that run: it does not start another


def _a9_outside(fx):
    """Fix round 2 (ST01): A9 once more, in a subprocess (python -B -I), from a copy of E's files outside
    .claude/worktrees, with --repo naming the repository whose worktrees git lists. That is where an old-code run of
    spec 16 executes: there e_guard.real_s2_dirs() covers only the copy, so the main checkout and every worktree are
    refused only through real_archive_roots(--repo), which A9's own parse of 'git worktree list' then checks."""
    s2 = os.path.join(fx.workdir("a9_outside"), "tree", "results", "objective2", "s2")
    for rel in ("s2b/e_guard.py", "s2b/e_read.py", "s2b/e_eval.py", "s2b/e_block4.py", "s2b/e_selftest.py",
                "figures/fig_s2_c2_a2.py"):
        with open(os.path.join(S2, rel)) as fh:
            t = fh.read()
        if rel == "s2b/e_selftest.py":
            for old, new in A9_SOURCE_EDIT:
                assert t.count(old) == 1, old
                t = t.replace(old, new)
        write_text(os.path.join(s2, rel), t)
    p = subprocess.run([sys.executable, "-B", "-I", os.path.join(s2, "s2b", "e_selftest.py"), "--case", "A9",
                        "--no-mutants", "--repo", OBJECTS["repo"]], capture_output=True,
                       env={**os.environ, "TMPDIR": tempfile.gettempdir(), A9_OUTSIDE: "1"})
    out = p.stdout.decode(errors="replace")
    assert p.returncode == 0 and re.search(r"^A9 \[A\] ok ", out, re.M), out[-1500:]


@case("A9", "A", mutants=(
        # the self-test refusals not applied to the mirror: the open reaches the (unreadable) file
        ("no_selftest_block", lambda fx: patched(eg, "selftest_block", lambda dirs, private_root=None: [])),
        # fix round 2 (ST01): real_archive_roots without the worktree listing (seen only outside .claude/worktrees)
        ("worktrees_unlisted", lambda fx: patched(sys.modules[__name__].__dict__, "A9_SOURCE_EDIT", [
            ("    if r is not None and r.returncode == 0:\n        out += [os.path.join(",
             "    if False:\n        out += [os.path.join(")]))))
def case_a9(fx):
    """Self-test refusals (RF-9, RF-10): on a synthetic tree mirroring the S2 layout, open, io.open, os.open,
    pathlib, gzip.open and tarfile.open of c2/gates/K3.json, c1/raw, c1/records, c1/gates, c1/structures.tar.gz and
    fr paths raise Blinded before the OS open (sentinel: the files are mode 000, so a reached open would raise
    PermissionError); the real archive paths of this checkout are in the refusal list (checked without opening).
    Fix round 1 (RF-9): the expected roots are also built independently of e_guard, from REPO and 'git worktree
    list' (names only), and every one is refused, the main checkout's included."""
    mirror = os.path.join(fx.workdir("a9"), "results", "objective2", "s2")
    rels = ("c2/gates/K3.json", "c1/raw/s2_m30_VB76.out.gz", "c1/records/s2_m30_host.json", "c1/gates/N.json",
            "c1/structures.tar.gz", "fr/raw/s2r_m30_VA188.a2.json", "c2/raw/s2r_m30_VB76.p1.out.gz")
    for r in rels:
        p = os.path.join(mirror, r)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(b"{}")
        os.chmod(p, 0)
    added = eg.selftest_block([mirror])
    try:
        n = 0
        for r in rels:
            p = os.path.join(mirror, r)
            for opener in (lambda q: open(q), lambda q: io.open(q, "rb"), lambda q: os.close(os.open(q, os.O_RDONLY)),
                           lambda q: pathlib.Path(q).read_bytes(), lambda q: gzip.open(q).read(),
                           lambda q: tarfile.open(q), lambda q: io.open_code(q)):
                try:
                    opener(p)
                except Blinded:
                    n += 1
                    continue
                except PermissionError:
                    raise AssertionError(f"{r}: the open reached the file (sentinel)") from None
                raise AssertionError(f"{r}: opened")
        assert n == 7 * len(rels)
        assert not eg.selftest_blocked(os.path.join(mirror, "C3_OPERATIONS.md"))
    finally:
        eg.selftest_unblock(added)
        for r in rels:
            os.chmod(os.path.join(mirror, r), 0o600)
    for s2 in eg.real_s2_dirs():
        for r in ("c2/gates/K3.json", "c1/raw/x.out.gz", "c1/records/x.json", "fr/x", "c1/structures.tar.gz"):
            assert eg.selftest_blocked(os.path.join(s2, r)), (s2, r)
        assert not eg.selftest_blocked(os.path.join(s2, "c1", "smoke.json"))
    # fix round 1: the expected set built independently of e_guard, from REPO and 'git worktree list' (names only;
    # nothing is opened): every S2 root of the repository and of its worktrees is refused, the main checkout's
    # included, and real_s2_dirs() covers each existing one under the main checkout
    exp = real_archive_roots(REPO)
    mine = {os.path.realpath(x) for x in eg.real_s2_dirs()}
    main = os.path.realpath(REPO.split(os.sep + os.path.join(".claude", "worktrees") + os.sep)[0])
    for s2 in exp:
        for r in ("c2/gates/K3.json", "c1/raw/x.out.gz", "c1/records/x.json", "fr/x", "c1/structures.tar.gz"):
            assert eg.selftest_blocked(os.path.join(s2, r)), (s2, r)
        top = os.path.dirname(os.path.dirname(os.path.dirname(s2)))
        if os.path.isdir(top) and (top == main or top.startswith(os.path.join(main, ".claude", "worktrees") + os.sep)):
            assert s2 in mine, s2
    assert os.path.realpath(os.path.join(main, "results", "objective2", "s2")) in mine
    # fix round 2 (ST01): the expected roots parsed here from 'git -C <--repo> worktree list --porcelain' (names
    # only), not through real_archive_roots: the main worktree (git lists it first) and every other one is refused
    r = subprocess.run(["git", "-C", OBJECTS["repo"], "worktree", "list", "--porcelain"], capture_output=True,
                       env={**os.environ, **GIT_ENV})
    wts = [x[len("worktree "):] for x in r.stdout.decode(errors="replace").splitlines() if x.startswith("worktree ")]
    assert r.returncode == 0 and wts, "git worktree list"
    for w in wts:
        s2 = os.path.join(w, "results", "objective2", "s2")
        for rr in ("c2/gates/K3.json", "c1/raw/x.out.gz", "fr/x", "c1/structures.tar.gz"):
            assert eg.selftest_blocked(os.path.join(s2, rr)), (s2, rr)
    if not os.environ.get(A9_OUTSIDE):
        _a9_outside(fx)


@case("A11", "A", mutants=(
        # an E file (other than e_guard.py) that reaches into a guarded object's data
        ("planted_private_access", lambda fx: patched(sys.modules[__name__].__dict__, "E_SOURCE_EXTRA",
                                                      [("planted.py", "x = g" + "._" + "d\n")])),
        # an E file that puts its directory on sys.path (RF-19; engineer C)
        ("planted_sys_path", lambda fx: patched(sys.modules[__name__].__dict__, "E_SOURCE_EXTRA",
                                                [("planted.py", "import sys\nsys.path" + ".insert(0, 'x')\n")])),
        # integration: an E file with a work-area word (the public-repository rules of scripts/46)
        ("planted_work_area_word", lambda fx: patched(sys.modules[__name__].__dict__, "E_SOURCE_EXTRA",
                                                      [("planted.py", "d = 'scr" + "atch'\n")])),))
def case_a11(fx):
    """No E source file other than e_guard.py contains the private data attribute of a guarded object (the
    literal dot-underscore-d), none calls the C2 figure's module loader or the check5_diag loaders of scripts/46
    and of the figure (spec 4.1, section 2), and none changes sys.path (RF-19: helpers by spec_from_file_location).
    Integration: every E source passes the public-repository rules of scripts/46 hygiene_violations (kind 'code'),
    as the hygiene scan of the S2b campaign commit requires (the round-2 self-test named its temporary directories
    with a work-area word)."""
    files = [os.path.join(HERE, n) for n in sorted(os.listdir(HERE)) if re.fullmatch(r"e_\w+\.py", n)]
    fig_e = os.path.join(S2, "figures", "fig_s2b_e_fk.py")
    if os.path.exists(fig_e):
        files.append(fig_e)
    srcs = []
    for p in files:
        with open(p) as fh:
            srcs.append((os.path.basename(p), fh.read()))
    srcs += E_SOURCE_EXTRA
    priv = re.compile(r"\._" + r"d\b")                      # the attribute itself, not e.g. m48._determinism
    calls = ("fig" + ".modules(", ".load_" + "c46(", ".load_" + "fig(")
    for name, src in srcs:
        if name != "e_guard.py":
            assert not priv.search(src), f"{name} reads a guarded object's data"
        for c_ in calls:
            assert c_ not in src, f"{name} calls {c_}"
        assert not re.search(r"\bsys\.path\.(insert|append|extend)\(|\bsys\.path\s*(\+?=)", src), \
            f"{name} changes sys.path (RF-19)"
        bad = fx.ex.c46.hygiene_violations(src, kind="code")              # integration: the rule names only
        assert not bad, f"{name} breaks the public-repository rules of scripts/46: {[b.split(':')[0] for b in bad]}"
    assert {"e_guard.py", "e_read.py", "e_selftest.py"} <= {n for n, _ in srcs}


E_SOURCE_EXTRA = []


@case("A12", "A", mutants=(
        # the files E never opens (graph, ledger, HARD_CAP, ...) no longer refused
        ("never_files_open", lambda fx: patched(eg, "NEVER_FILES", ())),
        # the hinge outputs no longer refused outside hinge mode
        ("hinge_raw_open", lambda fx: patched(eg, "HINGE", ())),
        # the Pb136 C1 outputs no longer refused outside block 5
        ("pb136_raw_open", lambda fx: patched(eg, "PB136_SP", ())),
        # the campaign/root binding lost (a c3b under the public root, c1 under the private root)
        ("no_root_binding", lambda fx: patched(eg, "PUBLIC_CAMPAIGNS", eg.CAMPAIGNS))))
def case_a12(fx):
    """OpenAudit run-mode refusals (spec 4.2, 4.5; S2B:545, 561-562, 610; OP-2; RF-2): inputs files, validity
    records, the files E never opens, step0_attempt1/ and discarded/, the C2 K2 and projection files, the C2 step-0
    files and the hinge outputs outside hinge mode (a hinge .a2.json only through a2_hinge_counts), the Pb136 C1
    outputs outside block 5 of a hinge read, every G1 and spin output, c3 entries and a campaign under the wrong
    root (names in any case, fix round 1); the allowed files read."""
    base = fx.workdir("a12")
    a = eg.OpenAudit(os.path.join(base, "s2"), private_root=os.path.join(base, "priv"))
    refused = ("c2/gates_applied/gate_K3.inputs.json", "c2/raw/s2r_m30_VB76.validity_final.json", "c2/graph.json",
               "c1/ledger.json", "fr/HARD_CAP.json", "fr/completeness.json", "c2/runner_reads.json",
               "c2/logs/campaign.log", "fr/step0_attempt1/gates/fr_step0.json", "fr/discarded/a2/x.out.gz",
               "fr/discarded/step0_attempt1_17/gates/fr_step0.json", "c2/gates/K2.json", "c2/gates/projection.json",
               "c2/gates_applied/gate_K2.json", "c2/gates_applied/gate_projection_after4.gate.json",
               "c2/gates/step0.json", "c2/gates_applied/gate_step0_1.gate.json", "c2/gates_applied/gate_step0_4.json",
               "c2/raw/s2r_m30_VB136.p1.out.gz", "c2/raw/s2r_m30_Sr136o0_vac.a2.json",
               "c2/raw/s2r_m30_hostB136.p1.in.gz", "c1/raw/s2_m30_VB136.out.gz", "c1/raw/s2_m30_Ca136o0_vac_q0.in.gz",
               "c1/raw/s2_m30_Sr136o0_vac.meta.json",
               "c1/raw/s2g1_m30_host_e60.out.gz", "c1/raw/s2spin_m30_Ca76o0_vac.out.gz", "c3/x.json", "c3.tar.gz",
               "c3b/raw/x.a2.json")
    allowed = ("c2/gates/K3.json", "c2/gates_applied/gate_K3.json", "c2/raw/s2r_m30_VB76.a2.json",
               "c2/raw/s2r_m30_VB76.p1.out.gz", "c2/structures.tar.gz", "c1/raw/s2_m30_VB76.out.gz",
               "c1/raw/s2_m30_VB76_q0.out.gz", "c1/records/s2_m30_VB136.json", "c1/gates/N.json", "fr/gates/FR.json",
               "fr/campaign.json", "C3_OPERATIONS.md", "c2_verify/verify_c2.txt", "s2b/E_output.txt")
    for r in refused + ("C3.TAR.GZ", "C3.TGZ", "C3_NOTRUN") + \
            ("c2/gates_applied/gate_K3.inputs.json.gz", "fr/x.inputs.txt", "c3.tar"):   # fix round 2 (G03, G01)
        assert a.refusal(r), r
    for r in allowed:
        assert a.refusal(r) is None, r
    with a.via("a2_hinge_counts"):
        assert a.refusal("c2/raw/s2r_m30_Sr136o0_vac.a2.json") is None
        assert a.refusal("c2/raw/s2r_m30_Sr136o0_vac.p1.out.gz")
    a.set_block(5)
    assert a.refusal("c1/raw/s2_m30_VB136.out.gz")                 # block 5 without the hinge allowance
    a.open_hinge()
    for r in ("c2/raw/s2r_m30_VB136.p1.out.gz", "c2/gates/step0.json", "c2/gates_applied/gate_step0_1.gate.json",
              "c1/raw/s2_m30_VB136.out.gz"):
        assert a.refusal(r) is None, r
    for r in ("c1/raw/s2g1_m30_Ca136o0_novac_e50.out.gz", "c2/gates/K2.json", "c2/gates_applied/gate_K3.inputs.json"):
        assert a.refusal(r), r
    a.set_block(3)
    assert a.refusal("c1/raw/s2_m30_VB136.out.gz")                 # hinge allowance, block 3
    assert a.refusal("c3b/raw/x.a2.json", base="private") is None and a.refusal("c1/smoke.json", base="private")


def _remove_tree_hooked(d):
    """remove_tree as before fix round 2: the OpenAudit hook active during shutil.rmtree."""
    try:
        if os.path.isdir(d):
            for dp, dns, fns in os.walk(d):
                os.chmod(dp, stat.S_IMODE(os.stat(dp).st_mode) | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRUSR)
            shutil.rmtree(d)
        return None
    except OSError as e:
        return f"{d}: not removed ({type(e).__name__})"


@case("A13", "A", mutants=(
        # the hook not paused for the removal (the code before fix round 2)
        ("hook_during_rmtree", lambda fx: patched(er, "remove_tree", _remove_tree_hooked)),))
def case_a13(fx):
    """Fix round 2: er.remove_tree, run with the working directory at an S2 root the self-test refuses (a synthetic
    mirror), removes a temporary tree holding children named c2, fr and c1/raw. shutil.rmtree opens each child by
    its bare name with dir_fd, which the 'open' audit event does not carry; the hook, paused for the removal, would
    otherwise resolve 'c2' against the working directory and refuse it (a false refusal; the tree left behind). A
    direct relative open of the mirror's archive path from there is still refused."""
    base = fx.workdir("a13")
    mirror = os.path.join(base, "mirror", "results", "objective2", "s2")
    for rel in ("c2/gates/K3.json", "fr/campaign.json", "c1/raw/x.out.gz"):
        write_text(os.path.join(mirror, rel), "{}\n")
    victim = os.path.join(base, "victim")
    for rel in ("c2/gates/K3.json", "fr/raw/y.a2.json", "c1/raw/z.out.gz", "notes.txt"):
        write_text(os.path.join(victim, rel), "x\n")
    added = eg.selftest_block([mirror])
    cwd = os.getcwd()
    try:
        os.chdir(mirror)
        m = er.remove_tree(victim)
        raises(Blinded, open, os.path.join("c2", "gates", "K3.json"))
    finally:
        os.chdir(cwd)
        eg.selftest_unblock(added)
    assert m is None and not os.path.exists(victim), m


# ---------------------------------------------------------------- group B: the readers (spec 18 B; e_read.py)
def one_relaxation(fx, name, c, lab, **kw):
    """A tree with one complete relaxation of campaign c and the minimal c1 it needs."""
    root = os.path.join(fx.workdir(name), "s2")
    workdir = build_min(root, fx.ex, starts=(lab,), **{k: kw.pop(k) for k in ("cell", "centres") if k in kw})
    members = {}
    r = write_relaxation(root, fx.ex, c, lab, members=members, workdir=workdir, fr=(c == "fr"), **kw)
    write_tar(os.path.join(root, c, "structures.tar.gz"), members)
    return root, r


def mode_kind(c, lab):
    if c == "fr":
        return "fr", "a2_fr"
    return ("far", "a2_far") if lab in eg.FAR else ("hinge", "a2_hinge")


def read_one(fx, root, c, lab, *, hinge=False, **kw):
    mode, kind = mode_kind(c, lab)
    with session(fx, root, hinge=hinge or mode == "hinge", block=5 if mode == "hinge" else 1) as (L, audit, ctx):
        r = er.read_relaxation(ctx, c, lab, mode=mode, kind=kind, **kw)
        return r, dict(ctx.checks.passed), ctx.reads


@case("B1", "B", mutants=(
        # no between-call test: a planted _read_F goes unseen
        ("no_between_check", lambda fx: patched(er.ReadsAudit, "_between", lambda self, where: None)),
        # the expected ase delta fixed at 1 (the three-part relaxation then fails)
        ("ase_delta_one", lambda fx: patched(er.ReadsAudit, "_check", _check_ase_one))))
def case_b1(fx):
    """READS: ase +1 for one part and +3 for a three-part relaxation (restarts at k = 1 and 2); F, forces and
    positions +n; every other key 0. A _read_F call planted between two reads gives INT-READS."""
    q = fx.ex.q47
    root, r1 = one_relaxation(fx, "b1a", "c2", "s2r_m30_VB76", n_config=9)
    root3 = os.path.join(os.path.dirname(root), "s2b")
    workdir = build_min(root3, fx.ex, starts=("s2r_m30_Sr76o0_novac",))
    mem = {}
    write_relaxation(root3, fx.ex, "c2", "s2r_m30_Sr76o0_novac", n_config=12, members=mem, workdir=workdir,
                     parts=[(0, 1, "killed"), (1, 1, "killed"), (2, 10, "converged")], restarts=2)
    write_tar(os.path.join(root3, "c2", "structures.tar.gz"), mem)
    for rt, lab, n, nparts in ((root, "s2r_m30_VB76", 9, 1), (root3, "s2r_m30_Sr76o0_novac", 12, 3)):
        before = collections.Counter(q.READS)
        res, passed, reads = read_one(fx, rt, "c2", lab)
        d = {k: q.READS[k] - before.get(k, 0) for k in set(q.READS) | set(before)}
        assert {k: v for k, v in d.items() if v} == {"ase": nparts, "F": n, "forces": n, "positions": n}, d
        assert res["n_parts"] == nparts and res["restart_k"] == ([] if nparts == 1 else [1, 2])
        assert dict(reads.totals) == {"ase": nparts, "F": n, "forces": n, "positions": n}
    with session(fx, root) as (L, audit, ctx):
        er.read_relaxation(ctx, "c2", "s2r_m30_VB76", mode="far", kind="a2_far")
        q._read_F("!    total energy              =   -1.00000000 Ry", 0)          # planted value read
        int_fail("INT-READS", er.read_relaxation, ctx, "c2", "s2r_m30_VB76", mode="far", kind="a2_far")
        ctx.cd.assert_no_calculator()                         # full reads load none of CALC_ENGINES (INT-CALC)


def _check_ase_one(self, where, d, want):
    want = dict(want)
    if "ase" in want:
        want["ase"] = 1
    return _orig_check(self, where, d, want)


_orig_check = er.ReadsAudit._check


@case("B2", "B", mutants=(
        # INT-KLAST without the converged_at_k comparison
        ("klast_no_conv", lambda fx: patched(er, "read_relaxation", _rr_patch_record_conv)),
        # INT-KLAST without the cap_reached test
        ("cap_read_as_199", lambda fx: patched(er, "K_CAP", 199))))
def case_b2(fx):
    """INT-KLAST (OP-14) for accepted_converged, accepted_plateau (k_last 200, cap), unconverged_cap and
    unconverged_early (bfgs_failed): a consistent record passes; each inconsistent leaf fails."""
    cases = (("accepted_converged", 21, {}), ("accepted_plateau", 201, {"plateau_Ry": "-0.00000735"}),
             ("unconverged_cap", 201, {"plateau_Ry": "0.00036750"}), ("unconverged_early", 30, {}))
    for outcome, n, kw in cases:
        root, r = one_relaxation(fx, f"b2_{outcome}", "fr", "s2r_m30_VA188", n_config=n, outcome=outcome, **kw)
        res, passed, _ = read_one(fx, root, "fr", "s2r_m30_VA188", plateau=True)
        assert res["parsed"] and res["k_last"] == n - 1 and passed.get("INT-KLAST") == 1
        assert res["xc"]["ENDRULE"]["ok"] is True, (outcome, res["xc"]["ENDRULE"])
        if n == 201:
            assert abs(res["plateau_meV"] - float(Fraction(kw["plateau_Ry"]) * RY * 1000)) < 1e-6
        path = os.path.join(root, "fr", "raw", "s2r_m30_VA188.a2.json")
        with open(path) as fh:
            rec0 = json.load(fh)
        bad = [("k_last", n - 2)]
        if outcome == "accepted_converged":
            bad.append(("converged_at_k", n - 2))
        for key, val in bad:
            rec = copy.deepcopy(rec0)
            rec[key] = val
            dump(path, rec)
            int_fail("INT-KLAST", read_one, fx, root, "fr", "s2r_m30_VA188")
        dump(path, rec0)
        if outcome != "unconverged_early":                       # the outcome leaf against the parse
            rec = copy.deepcopy(rec0)
            rec["end_rule"]["outcome"] = "unconverged_early" if outcome != "accepted_plateau" else "accepted_converged"
            dump(path, rec)
            try:
                res2, _, _ = read_one(fx, root, "fr", "s2r_m30_VA188")
                assert res2["xc"]["ENDRULE"]["ok"] is False
            except EIntegrity as e:
                assert e.check == "INT-KLAST"
            dump(path, rec0)
        if n == 201:                                              # fix round 2 (R02): k_last 200 without the cap
            orig = fx.ex.q47.parse_relax
            with patched(fx.ex.q47, "parse_relax", lambda *a, **kw: dict(orig(*a, **kw), cap_reached=False)):
                int_fail("INT-KLAST", read_one, fx, root, "fr", "s2r_m30_VA188")


def _rr_patch_record_conv(ctx, c, lab, **kw):
    """read_relaxation on a copy of the record whose converged_at_k equals k_last (the comparison is lost)."""
    path = ctx.L.a2_record(c, lab)
    with open(path) as fh:
        rec = json.load(fh)
    if rec.get("converged_at_k") is not None and rec.get("k_last") is not None:
        rec["converged_at_k"] = rec["k_last"]
        audit = ctx.audit
        audit.stop()
        dump(path, rec)
        audit.start()
    return _orig_read_relaxation(ctx, c, lab, **kw)


_orig_read_relaxation = er.read_relaxation


@case("B3", "B", mutants=(
        # INT-FINALPOS at 1e-5 A: a 2e-6 A move passes
        ("finalpos_loose", lambda fx: patched(er, "FINALPOS_TOL_A", 1e-5)),
        # INT-CELL at 1 A
        ("cell_loose", lambda fx: patched(er, "CELL_TOL_A", 1.0))))
def case_b3(fx):
    """A final member moved by 2e-6 A on one atom gives INT-FINALPOS; 0.9e-6 A passes; a sha mismatch gives
    INT-FINALSHA; a cell mismatch gives INT-CELL."""
    root, r = one_relaxation(fx, "b3", "fr", "s2r_m30_VA188", n_config=7)
    ex = fx.ex
    fin = er.atoms_from_bytes(r["final_bytes"])
    rec_path = os.path.join(root, "fr", "raw", "s2r_m30_VA188.a2.json")
    with open(rec_path) as fh:
        rec0 = json.load(fh)
    workdir = os.path.join(os.path.dirname(root), "workdir")

    def plant(dx=0.0, cell=None, sha=None):
        X = fin.positions.copy()
        X[3, 1] += dx
        b = extxyz_bytes(ex.c46, fin.get_chemical_symbols(), X, fin.cell.array if cell is None else cell, workdir)
        write_tar(os.path.join(root, "fr", "structures.tar.gz"), {"a2/s2r_m30_VA188/s2r_m30_VA188.final.extxyz": b})
        rec = copy.deepcopy(rec0)
        rec["final_geometry"]["sha256"] = sha or hashlib.sha256(b).hexdigest()
        dump(rec_path, rec)
    plant(0.9e-6)
    res, passed, _ = read_one(fx, root, "fr", "s2r_m30_VA188")
    assert passed["INT-FINALPOS"] == 1 and passed["INT-CELL"] == 1 and passed["INT-FINALSHA"] == 1
    plant(2e-6)
    int_fail("INT-FINALPOS", read_one, fx, root, "fr", "s2r_m30_VA188")
    plant(0.0, sha="0" * 64)
    int_fail("INT-FINALSHA", read_one, fx, root, "fr", "s2r_m30_VA188")
    plant(0.0, cell=fin.cell.array * (1 + 1e-6))
    int_fail("INT-CELL", read_one, fx, root, "fr", "s2r_m30_VA188")
    plant(0.0)
    rec = copy.deepcopy(rec0)
    rec["final_geometry"]["k"] = 5
    dump(rec_path, rec)
    int_fail("INT-FINALK", read_one, fx, root, "fr", "s2r_m30_VA188")


@case("B4", "B", mutants=(
        # sp_full with the label's own record for a _q0 row (the base-record rule lost)
        ("q0_own_record", lambda fx: patched(eg.C1Access, "base_free", _base_free_no_strip)),
        # the SP delta without the magnetisation keys
        ("sp_delta_short", lambda fx: patched(er, "SP_DELTA", {"F": 1, "TS": 1, "forces": 1, "fermi": 1})),
        # no cache: READS rises twice for one label
        ("no_cache", lambda fx: patched(eg.C1Access, "sp_full", _sp_full_nocache))))
def case_b4(fx):
    """sp_full (OP-1: no force-only reader): READS rises by exactly F, TS, forces, fermi, mag_total and mag_abs 1
    each, once per label (cached); the free set of a _q0 row is its base record's; F and the force summaries equal an
    independent computation from the planted strings (F to 1e-9 eV, forces to 1e-12 eV/A); a parse_sp that raises
    READS['ase'] is INT-READS (fix round 1)."""
    root, man = fx.tree()
    ex = fx.ex
    q = ex.q47
    with session(fx, root) as (L, audit, ctx):
        c1 = eg.C1Access(L, ex.c46, q, audit, ctx.reads).load_census()
        for lab in ("s2_m30_VB76", "s2_m30_Sr76o0_vac_q0", "s2_m05_GA164o0_novac", "s2_m30_host"):
            b = collections.Counter(q.READS)
            r = c1.sp_full(lab, block=3)
            d = {k: q.READS[k] - b.get(k, 0) for k in set(q.READS) | set(b)}
            assert {k: v for k, v in d.items() if v} == er.SP_DELTA, (lab, d)
            b2 = collections.Counter(q.READS)
            assert c1.sp_full(lab, block=3) is r and collections.Counter(q.READS) == b2
            assert abs(r["F_eV"] - float(Fraction(man["sp_F"][lab]) * RY)) < 1e-9
            free = man["sp_free"][lab]
            n = [math.sqrt(math.fsum(float(Fraction(v) * RY / BOHR) ** 2 for v in row))
                 for row in man["sp_forces"][lab]]
            fr_, al = r["forces"]["free"], r["forces"]["all"]
            assert fr_["indices"] == sorted(free) and al["n"] == 3 and fr_["n"] == len(free)
            assert max(abs(a - b_) for a, b_ in zip(fr_["norms_eVA"], [n[i] for i in sorted(free)])) < 1e-12
            assert abs(al["max_eVA"] - max(n)) < 1e-12 and abs(fr_["max_eVA"] - max(n[i] for i in free)) < 1e-12
            assert abs(al["rms_eVA"] - math.sqrt(math.fsum(x * x for x in n) / 3)) < 1e-12
        assert man["sp_free"]["s2_m30_Sr76o0_vac_q0"] == man["sp_free"]["s2_m30_Sr76o0_vac"]
        assert ctx.reads.check_labels(set(), set(eg.BLOCK3_SP))
        int_fail("INT-READS", ctx.reads.check_labels, set(), {"s2_m30_VB76"})
        orig = q.parse_sp

        def bumped(*a, **kw):                                     # fix round 1: a full parse_sp that also reads
            out = orig(*a, **kw)                                  # with ase (sp_status's own status read is left
            if kw.get("read") == "full":                          # alone, so that only the check after the full
                q.READS["ase"] += 1                               # parse can see it)
            return out
        with patched(q, "parse_sp", bumped):
            e = int_fail("INT-READS", c1.sp_full, "s2_m30_VA188", block=3)
        assert e.where == "s2_m30_VA188" and e.key == "READS[ase]", e.line()


def _base_free_no_strip(self, label):
    w = self.label_wid.get(label)
    if w is None:
        raise EIntegrity("INT-SP", f"c1/raw/{label}", "no cell record for the label")
    return self.blind(w).get("free")


def _sp_full_nocache(self, label, *, block):
    self._sp.pop(label, None) if hasattr(self, "_sp") else None
    return _orig_sp_full(self, label, block=block)


_orig_sp_full = eg.C1Access.sp_full


@case("B5", "B", mutants=(
        # image centres reduced to the plain centres (n = 0)
        ("no_images", lambda fx: patched(er, "IMAGE_RANGE", range(0, 1))),
        # XC-MIC against plain distances
        ("mic_plain", lambda fx: patched(er, "mic_residual", _mic_plain))))
def case_b5(fx):
    """Path work by shell (OP-15): an atom 0.5 A from the far side of a cell face from the centre is in shell
    8-1e+09 with plain centres and in 0-4 with image centres; XC-MIC holds; the closure and the total equal an
    independent trapezoid sum from the planted strings (Fraction) to 1e-9 meV."""
    ex, q = fx.ex, fx.ex.q47
    lab = "s2r_m30_hostA188"
    Lc = ALAT_BOHR * q.QE_UNITS["Bohr"]
    centre = [0.30, 10.0, 10.0]
    root = os.path.join(fx.workdir("b5"), "s2")
    workdir = build_min(root, ex, starts=(lab,), regions=(("A", 188),), centres={"v": [10.0, 10.0, 10.0],
                                                                                  "site": centre})
    rng = np.random.default_rng(5)
    near = np.array([[10.0, 10.0, 10.0]] * 6) + rng.uniform(-2.0, 2.0, (6, 3))   # within 4 A of v: same shells
    dirs = rng.normal(size=(6, 3))

    def pos(k):
        X = near + 0.002 * k * dirs
        X[0] = [Lc - 0.20 + 1e-4 * k, 10.0 + 0.001 * k, 10.0]       # 0.5 A from the site through the x face
        return X
    members = {}
    n = 9
    F = a2_F(lab, n)
    frc = forces_fn(lab)
    txt, pr = pw_text(q, input_name=f"{lab}.p1", k0=0, n_config=n, end="converged", F=F, pos=pos, frc=frc,
                      symbols=SYM_A2)
    write_gz(os.path.join(root, "fr", "raw", f"{lab}.p1.out.gz"), txt)
    Xk = printed_positions(q, pr, n - 1)
    b = extxyz_bytes(ex.c46, SYM_A2, Xk, cell_matrix(q), workdir)
    members[f"a2/{lab}/{lab}.final.extxyz"] = b
    write_tar(os.path.join(root, "fr", "structures.tar.gz"), members)
    rec = {"status": "complete", "n_config": n, "k_last": n - 1, "converged_at_k": n - 1, "restarts": 0,
           "reruns_from_zero": 0, "layout": {"ranks": 64}, "end_rule": {"outcome": "accepted_converged",
                                                                        "end": "converged"},
           "final_geometry": {"k": n - 1, "sha256": hashlib.sha256(b).hexdigest()},
           "validity_final": {"valid": True, "failed": [], "check5_reading": "invariant"}}
    dump(os.path.join(root, "fr", "raw", f"{lab}.a2.json"), rec)
    res, passed, _ = read_one(fx, root, "fr", lab)
    assert res["xc"]["MIC"]["ok"] is True, res["xc"]["MIC"]
    shells = res["pw"]["shells_dr2_A2"]
    # independent: per-atom work and dr^2 by shell from the printed strings
    alat_f = Fraction(float(f"{ALAT_BOHR:.6f}") * q.QE_UNITS["Bohr"])      # the parsers' alat (a float product)
    Xs = {k: [[Fraction(v) * alat_f if kind_ == "alat" else Fraction(v) for v in s] for kind_, s in pr["pos"][k]]
          for k in range(n)}
    Fo = {k: [[Fraction(v) * RY / BOHR for v in s] for s in pr["frc"][k]] for k in range(n)}
    W = [Fraction(0)] * 6
    for k in range(n - 1):
        for i in range(6):
            W[i] -= sum((Fo[k][i][c] + Fo[k + 1][i][c]) / 2 * (Xs[k + 1][i][c] - Xs[k][i][c]) for c in range(3))
    Fe = [Fraction(s) * RY for s in F]
    dF_float = float(F[-1]) * float(RY) - float(F[0]) * float(RY)          # F(final) - F(0) as the parse forms it
    tot = sum(W) * 1000
    clos = float(sum(W)) * 1000 - dF_float * 1000
    assert abs(res["pw"]["total_meV"] - float(tot)) < 1e-9 and abs(res["pw"]["closure_meV"] - clos) < 1e-9, \
        (res["pw"]["total_meV"] - float(tot), res["pw"]["closure_meV"] - clos)
    assert abs(float(sum(W) - (Fe[-1] - Fe[0])) * 1000 - res["pw"]["closure_meV"]) < 1e-6     # exact F, 1e-6 meV
    plain = ex.m48.path_work({"positions_A": {k: np.array([[float(v) for v in r] for r in Xs[k]]) for k in range(n)},
                              "forces_eVA": {k: np.array([[float(v) for v in r] for r in Fo[k]]) for k in range(n)},
                              "F_eV": {k: float(Fe[k]) for k in range(n)}}, res["centres"])
    dr2_0 = float(sum((Xs[n - 1][0][c] - Xs[0][0][c]) ** 2 for c in range(3)))
    assert abs(plain["shells_dr2_A2"]["8-1e+09"] - shells["8-1e+09"] - dr2_0) < 1e-12, (plain, shells)
    assert abs(shells["0-4"] - plain["shells_dr2_A2"]["0-4"] - dr2_0) < 1e-12
    assert abs(res["pw"]["shells_meV"]["0-4"] - plain["shells_meV"]["0-4"] - float(W[0] * 1000)) < 1e-9


def _mic_plain(cd, X0, centres, images, cell):
    X0 = np.asarray(X0, float)
    d_img = np.min(np.linalg.norm(X0[:, None, :] - np.asarray(images, float)[None, :, :], axis=2), axis=1)
    d_pl = np.min(np.linalg.norm(X0[:, None, :] - np.asarray(centres, float)[None, :, :], axis=2), axis=1)
    return float(np.abs(d_img - d_pl).max())


@case("B6", "B", mutants=(
        # a2_parts without the 1..N test
        ("parts_gap_allowed", lambda fx: patched(er.ELayout, "a2_parts", _a2_parts_nogap)),
        # parse_relax errors not caught (RF-20): the S2Error escapes
        ("no_rf20_catch", lambda fx: patched(er.ReadsAudit, "parse_relax", _parse_relax_nocatch))))
def case_b6(fx):
    """A missing part number (p1, p3) gives INT-PARTS. A part labelled with another relaxation's input name raises in
    parse_relax [47:1025-1027] and is reported as INT-PARSE by stage and exception type only (RF-20)."""
    root, r = one_relaxation(fx, "b6", "c2", "s2r_m30_Sr76o0_novac", n_config=6,
                             parts=[(0, 1, "killed"), (1, 1, "killed"), (2, 4, "converged")])
    raw = os.path.join(root, "c2", "raw")
    os.rename(os.path.join(raw, "s2r_m30_Sr76o0_novac.p2.out.gz"), os.path.join(raw, "x.gz"))
    int_fail("INT-PARTS", read_one, fx, root, "c2", "s2r_m30_Sr76o0_novac")
    root2, r2 = one_relaxation(fx, "b6b", "c2", "s2r_m30_VB76", n_config=6, input_label="s2r_m30_hostB76")
    e = int_fail("INT-PARSE", read_one, fx, root2, "c2", "s2r_m30_VB76")
    assert e.key == "stage parse_relax S2Error" and "hostB76" not in e.line(), e.line()


def _a2_parts_nogap(self, c, lab):
    d = self.cdir(c, "raw")
    rx = re.compile(re.escape(lab) + r"\.p([1-9]\d*)\.out\.gz")
    return [os.path.join(d, f) for _, f in sorted((int(m.group(1)), f) for f in os.listdir(d) for m in [rx.fullmatch(f)]
                                                 if m)]


def _parse_relax_nocatch(self, lab, parts, *, block=None, **kw):
    return self.q.parse_relax(parts, **kw)


@case("B7", "B", mutants=(
        # the old c3 lock (any entry matching c3([._-].*)?): C3_OPERATIONS.md is refused
        ("old_c3_rule", lambda fx: patched(er, "c3_entries", lambda d: [n for n in os.listdir(d)
                                                                         if eg.C3_DIR_RE.fullmatch(n)])),
        # OpenAudit without the c3 segment rule
        ("no_c3_segment", lambda fx: patched(eg, "C3_DIR_RE", re.compile(r"(?!)")))))
def case_b7(fx):
    """ELayout and the c3 lock (RF-2): C3_OPERATIONS.md and c3b/ are allowed; c3/, C3/, c3_x/, a dangling c3 symlink
    and c3.tar.gz are refused (exit 2 at the start, INT-ROOT at exit), and so are dangling symlinks named C3-old and
    c3_y, which only the symlink rule refuses, while a regular file c3_x.txt is allowed (fix round 1); OpenAudit
    refuses a c3 directory segment and allows the note; no c3 path and no .inputs.json path can be built."""
    base = fx.workdir("b7")
    ok_root = os.path.join(base, "ok")
    os.makedirs(os.path.join(ok_root, "c3b"))
    os.makedirs(os.path.join(ok_root, "c1"))
    with open(os.path.join(ok_root, "C3_OPERATIONS.md"), "w") as fh:
        fh.write("note\n")
    with open(os.path.join(ok_root, "c3b_notes.txt"), "w") as fh:
        fh.write("x\n")
    with open(os.path.join(ok_root, "c3_x.txt"), "w") as fh:     # fix round 1: a regular file is allowed
        fh.write("x\n")
    L = er.ELayout(ok_root)
    assert er.assert_no_c3(L) and er.assert_no_c3(L, at="exit")
    for i, (bad, mk) in enumerate((("c3", "dir"), ("C3", "dir"), ("c3_x", "dir"), ("c3", "dangling"),
                                   ("c3.tar.gz", "file"), ("c3_notrun", "file"), ("C3.TGZ", "file"),
                                   ("c3.tar", "file"),                                    # fix round 2 (G01)
                                   ("C3-old", "dangling"), ("c3_y", "dangling"))):   # by the symlink rule alone
        r = os.path.join(base, f"bad{i}")                       # case-insensitive volumes: no name from 'bad
        shutil.copytree(ok_root, r)
        p = os.path.join(r, bad)
        if mk == "dir":
            os.makedirs(p)
        elif mk == "dangling":
            os.symlink(os.path.join(r, "nowhere"), p)
        else:
            with open(p, "w") as fh:
                fh.write("x")
        Lb = er.ELayout(r)
        raises(EError, er.assert_no_c3, Lb)
        int_fail("INT-ROOT", er.assert_no_c3, Lb, at="exit")
    priv = os.path.join(base, "priv")
    os.makedirs(os.path.join(priv, "c3"))
    raises(EError, er.assert_no_c3, er.ELayout(ok_root, priv))
    for c in ("c3", "C3", "c4", "s2", ""):
        raises(EError, L.cdir, c)
    raises(EError, L.applied, "c2", "gate:K3", ".inputs.json")
    raises(Blinded, L.file, "c2", "gates_applied/gate_K3.inputs.json")
    raises(EError, L.file, "c2", "../c3/x.json")
    raises(EError, L.cdir, "c3b")                                     # no private root given
    assert L.applied("fr", "gate:fr_step0@2", ".gate.json").endswith("fr/gates_applied/gate_fr_step0_2.gate.json")
    a = eg.OpenAudit(ok_root)
    assert a.refusal("c3/x.json") and a.refusal("C3_x/y.json") and a.refusal("c3.tar.gz") and \
        a.refusal("c1/c3/y.json")
    assert a.refusal("C3_OPERATIONS.md") is None and a.refusal("c3b_notes.txt") is None
    with a:
        with open(os.path.join(ok_root, "C3_OPERATIONS.md")) as fh:
            fh.read()
    assert any(e["rel"] == "C3_OPERATIONS.md" for e in a.log.values())


@case("B8", "B", mutants=(
        # E_mace of a host from its last stage (RF-24)
        ("host_mace_stage", lambda fx: patched(er, "build_c1_table", _table_stage_mace)),
        # kept minima not mapped through work_ids (RF-18)
        ("no_work_ids", lambda fx: patched(er, "_DISTINCT_RE", re.compile(r"(?!)"))),
        # Pb136 labels left in H
        ("pb136_label_added", lambda fx: patched(er, "build_c1_table", _table_with_pb136)),
        # the census without the class counts
        ("census_no_counts", lambda fx: patched(eg, "CLASS_COUNTS", {**eg.CLASS_COUNTS, "pose_start": 29}))))
def case_b8(fx):
    """The C1 census and table builder (spec 5.4, RF-18, RF-24): classes 2/29/80/16/28 + 5; H holds no Pb136 label
    outside hinge mode; E_mace[host label] is relax.E_mace_eV, not a stage canary; the kept minimum o1 of the
    two-minimum distinct file takes the E_mace, validity and checks of the record its work_ids names; pose_pilot,
    pair_rejected and the a2_sites; a planted 161st record s2_m30_Sr136p1_novac gives INT-C1-CENSUS; block 5 adds the
    five Pb136 records and single points."""
    root, man = fx.tree()
    ex = fx.ex
    with session(fx, root) as (L, audit, ctx):
        c1 = eg.C1Access(L, ex.c46, ex.q47, audit, ctx.reads).load_census()
        cen = er.census(c1)
        assert {k: len(v) for k, v in cen.items()} == eg.CLASS_COUNTS and cen["pb136"] == sorted(eg.PB136_WIDS)
        T, ledger = er.build_c1_table(c1, ctx)
        H = T["hosts"]["m30"]
        for p in eg.PILOTS:
            assert T["hosts"][p]["E_mace"][f"s2_{p}_host"] == man["c1_mace"][f"s2_{p}_host"][0][1]
            assert T["hosts"][p]["host_valid"] is True
        lab1 = "s2_m30_Cs188o1_novac"
        assert H["E_mace"][lab1] == man["c1_mace"]["s2_m30_Cs188p1_novac"][0][1] and H["cell_valid"][lab1] is True
        assert H["pose_pilot"]["Cs"]["188"] == {"novac": ["o0", "o1"], "vac": ["o0"]}
        assert sorted(H["pose_pilot"]) == ["Cl", "Cs"] and "pose_pilot" not in T["hosts"]["m05"]
        assert H["pair_rejected"] == {"Cs188": ["p3", "p6"]}
        assert H["cell_valid"]["s2_m30_Cs128o0_vac"] is True and "s2_m30_Cs128o4_vac" not in H["cell_valid"]
        assert not er.pb136_keys(T) and "B" not in T["a2_sites"]["m30"] and T["a2"] == {}
        assert set(H["F"]) | set(T["hosts"]["m05"]["F"]) == set(eg.BLOCK3_SP)
        s = ex.m48._mace_pilot(T)
        assert not any(k.endswith("136") for k in s["calibration"].get("m30", {}))
        agg = s["pose_pilot"]["Cs188"]
        assert agg["N_D"] == 2 and agg["N_DV"] == 1 and agg["Eb_mace_aggregate_meV"] is not None
        c1.open_hinge(); audit.open_hinge(); audit.set_block(5)
        a2h = {lab: {"F0": -1.0, "Ffin": -1.1, "status": "complete", "n_config": 3, "k_last": 2,
                     "leaves": {"validity_final.valid": True, "validity_final.failed": [],
                                "end_rule.outcome": "accepted_converged"}} for lab in eg.HINGE}
        T2, rows = er.extend_c1_table_hinge(T, ledger, c1, a2h)
        assert {r["wid"] for r in rows} == set(eg.PB136_WIDS) and len([1 for r in rows for _ in r["mace"]]) == 5
        want = {v for w in eg.PB136_WIDS for _, v in man["c1_mace"][w]}      # fix round 2: hashed canaries
        assert {v for r in rows for _, v in r["mace"]} == want and len(want) == 5
        assert set(eg.PB136_SP) <= set(T2["hosts"]["m30"]["F"]) and T2["a2_sites"]["m30"]["B"] == 136
        assert set(T2["a2"]["m30"]) == set(eg.HINGE)
        assert c1.assert_closed("exit")
    extra = os.path.join(fx.workdir("b8"), "s2")
    shutil.copytree(root, extra, symlinks=True)
    shutil.copy(os.path.join(extra, "c1", "records", "s2_m30_Sr136p0_novac.json"),
                os.path.join(extra, "c1", "records", "s2_m30_Sr136p1_novac.json"))
    with session(fx, extra) as (L, audit, ctx):
        int_fail("INT-C1-CENSUS", eg.C1Access(L, ex.c46, ex.q47, audit, ctx.reads).load_census)


def _table_stage_mace(c1, ctx):
    T, ledger = _orig_build_c1_table(c1, ctx)
    for p in eg.PILOTS:
        rf = c1.record(f"s2_{p}_host", blind=False, block=3)
        T["hosts"][p]["E_mace"][f"s2_{p}_host"] = rf["relax"]["stages"][-1]["E_mace_eV"]
    return T, ledger


_orig_build_c1_table = er.build_c1_table


def _table_with_pb136(c1, ctx):
    T, ledger = _orig_build_c1_table(c1, ctx)
    T["hosts"]["m30"]["cell_valid"]["s2_m30_Sr136o0_vac"] = True
    return T, ledger


@case("B9", "B", mutants=(
        # an absent listed file raises instead of FILE_ABSENT
        ("absent_raises", lambda fx: patched(eg, "eg_load", _eg_load_raises)),
        # a missing segment returns None instead of ABSENT
        ("absent_is_none_value", lambda fx: patched(eg, "ABSENT", None))))
def case_b9(fx):
    """RF-12 (guard part): eg_load of an absent listed file returns FILE_ABSENT; a missing leaf is ABSENT, distinct
    from a null leaf; an absent record gives read_relaxation {record: FILE_ABSENT, parsed: False}; a record that did
    not complete opens no part; ABSENT inside a list projection (commit history) is INT-STRUCT."""
    root = os.path.join(fx.workdir("b9"), "s2")
    build_min(root, fx.ex, starts=())
    dump(os.path.join(root, "fr", "raw", "s2r_m30_VA188.a2.json"), {"status": "not_run_gate", "parts": []})
    write_gz(os.path.join(root, "fr", "raw", "s2r_m30_VA188.p1.out.gz"), "planted part, never opened\n")
    dump(os.path.join(root, "fr", "campaign.json"), {"status": "stopped", "commit": None,
                                                     "commit_history": [{"from": "a"}]})
    with session(fx, root) as (L, audit, ctx):
        assert eg.eg_load(L, "fr", "state_end.json", mode="fr", kind="state_fr", audit=audit) is FILE_ABSENT
        g = eg.eg_load(L, "fr", "campaign.json", mode="fr", kind="campaign_fr", audit=audit)
        assert g.get("status") == "stopped" and g.get("commit") is None and g.get("fr_outcome") is ABSENT
        int_fail("INT-STRUCT", g.get, "commit_history[].to")
        r = er.read_relaxation(ctx, "fr", "s2r_m30_hostA188", mode="fr", kind="a2_fr")
        assert r["record"] is FILE_ABSENT and r["parsed"] is False
        r = er.read_relaxation(ctx, "fr", "s2r_m30_VA188", mode="fr", kind="a2_fr")
        assert r["status"] == "not_run_gate" and r["parsed"] is False and r["leaves"]["n_config"] is ABSENT
        assert not any(e["rel"].endswith(".out.gz") for e in audit.log.values())


@case("B10", "B", mutants=(
        # the zero-configuration branch removed (RF-4): the missing final geometry becomes INT-FINALK
        ("no_zero_branch", lambda fx: patched(er, "read_relaxation", _rr_no_zero)),
        # XC-PARTS checked although the relaxation was rerun from zero (RF-23)
        ("parts_after_rerun", lambda fx: patched(er, "read_relaxation", _rr_parts_always)),
        # the operator override recomputed (RF-13)
        ("operator_recomputed", lambda fx: patched(er, "read_relaxation", _rr_no_operator))))
def case_b10(fx):
    """RF-4, RF-13, RF-14, RF-23: an SCF failure at k = 0 is complete with n_config 0 and is read without the
    final-geometry checks ({parsed: True, n_config: 0}, every F item 'not formed'); k_last = 20 gives no Delta F_tail
    ('k_last < 36'); n_config 1 gives no path work ('< 2 configurations'); an operator end is compared with its
    override; XC-PARTS is not checked after a rerun from zero."""
    root = os.path.join(fx.workdir("b10"), "s2")
    lab = "s2r_m30_Cs188o0_novac"
    workdir = build_min(root, fx.ex, starts=(lab, "s2r_m30_VA188", "s2r_m30_hostA188"))
    q = fx.ex.q47
    txt, _ = pw_text(q, input_name=f"{lab}.p1", k0=0, n_config=0, end="scf_failed", F=[], pos=positions_fn(lab),
                     frc=forces_fn(lab), symbols=SYM_A2)
    write_gz(os.path.join(root, "fr", "raw", f"{lab}.p1.out.gz"), txt)
    dump(os.path.join(root, "fr", "raw", f"{lab}.a2.json"),
         {"status": "complete", "n_config": 0, "k_last": None, "converged_at_k": None, "restarts": 0,
          "reruns_from_zero": 0, "layout": {"ranks": 64}, "end_rule": {"outcome": "unconverged_early",
                                                                       "end": "scf_failed"}})
    members = {}
    write_relaxation(root, fx.ex, "fr", "s2r_m30_VA188", n_config=21, outcome="unconverged_early", fr=True,
                     members=members, workdir=workdir, operator=True, reruns_from_zero=1)
    write_relaxation(root, fx.ex, "fr", "s2r_m30_hostA188", n_config=1, fr=True, members=members, workdir=workdir)
    write_tar(os.path.join(root, "fr", "structures.tar.gz"), members)
    r, passed, _ = read_one(fx, root, "fr", lab)
    assert r["parsed"] is True and r["n_config"] == 0 and r["k_last"] is None and r["F"] == {}
    assert r["not_formed"] == "no configuration; end rule unconverged_early" and "INT-FINALK" not in passed
    assert r["xc"]["ENDRULE"]["ok"] is True and r["xc"]["PARTS"]["ok"] is True
    r, passed, _ = read_one(fx, root, "fr", "s2r_m30_VA188")
    assert r["k_last"] == 20 and r["tail"] == {} and r["tail_reason"] == "k_last < 36"
    assert r["xc"]["ENDRULE"] == {"ok": True, "basis": "operator override", "recomputed": None,
                                  "record": "unconverged_early"}
    assert r["xc"]["PARTS"]["ok"] is None and r["xc"]["PARTS"]["note"] == "restarts include discarded attempts"
    r, passed, _ = read_one(fx, root, "fr", "s2r_m30_hostA188")
    assert r["k_last"] == 0 and r["pw"] is None and r["pw_reason"] == "< 2 configurations" and r["relax_meV"] == 0.0


def _eg_load_raises(*a, **kw):
    r = _orig_eg_load(*a, **kw)
    if r is FILE_ABSENT:
        raise FileNotFoundError("absent listed file")
    return r


def _rr_no_zero(ctx, c, lab, **kw):
    g = eg.eg_load(ctx.L, c, f"raw/{lab}.a2.json", mode=kw["mode"], kind=kw["kind"], audit=ctx.audit)
    if g is not FILE_ABSENT and g.get("n_config") == 0:
        ctx.checks.require(g.get("final_geometry.k") is not eg.ABSENT, "INT-FINALK", lab, "final_geometry.k")
    return _orig_read_relaxation(ctx, c, lab, **kw)


def _rr_parts_always(ctx, c, lab, **kw):
    r = _orig_read_relaxation(ctx, c, lab, **kw)
    if r.get("parsed") and r["xc"]["PARTS"]["ok"] is None:
        r["xc"]["PARTS"] = {"ok": r["n_parts"] == r["leaves"]["restarts"] + 1}
    return r


def _rr_no_operator(ctx, c, lab, **kw):
    r = _orig_read_relaxation(ctx, c, lab, **kw)
    if r.get("parsed") and r["xc"]["ENDRULE"]["basis"] == "operator override":
        r["xc"]["ENDRULE"] = {"ok": False, "basis": "scripts/47 end_rule", "recomputed": "incomplete",
                              "record": r["xc"]["ENDRULE"]["record"]}
    return r


@case("B11", "B", mutants=(
        # INT-SHA-STABLE comparing a file with itself (the first-open sha not kept)
        ("stable_self", lambda fx: patched(eg.OpenAudit, "stable", lambda self: [])),
        # the tar-member log dropped
        ("no_member_log", lambda fx: patched(eg.OpenAudit, "log_member", lambda self, t, n: None))))
def case_b11(fx):
    """OpenAudit: every open under the root is logged once with its sha256 at first open (open, os.open, pathlib);
    a file changed after its first open is reported by stable() (INT-SHA-STABLE); member_bytes logs (tar, member);
    a hinge member of c2/structures.tar.gz and a hinge output are refused outside hinge mode; writes under the root
    are refused; classify() gives every logged file one RF-11 class."""
    root = os.path.join(fx.workdir("b11"), "s2")
    for rel in ("c1/smoke.json", "c2/gates/K3.json", "c2_verify/verify_c2.txt", "s2b/E_output.txt"):
        dump(os.path.join(root, rel), {"x": 1})
    write_tar(os.path.join(root, "c2", "structures.tar.gz"), {"a2/s2r_m30_VB76/s2r_m30_VB76.final.extxyz": b"x",
                                                              "a2/s2r_m30_VB136/s2r_m30_VB136.final.extxyz": b"y"})
    dump(os.path.join(root, "c2", "raw", "s2r_m30_VB136.a2.json"), {"n_config": 3})
    a = eg.OpenAudit(root, tmp=[fx.ex.tmp])
    with a:
        for rel in ("c1/smoke.json", "c2/gates/K3.json", "c2_verify/verify_c2.txt", "s2b/E_output.txt"):
            with open(os.path.join(root, rel)) as fh:
                fh.read()
        os.close(os.open(os.path.join(root, "c1", "smoke.json"), os.O_RDONLY))
        pathlib.Path(os.path.join(root, "c1", "smoke.json")).read_text()
        assert er.member_bytes(a, os.path.join(root, "c2", "structures.tar.gz"),
                               "a2/s2r_m30_VB76/s2r_m30_VB76.final.extxyz") == b"x"
        raises(Blinded, er.member_bytes, a, os.path.join(root, "c2", "structures.tar.gz"),
               "a2/s2r_m30_VB136/s2r_m30_VB136.final.extxyz")
        raises(Blinded, open, os.path.join(root, "c2", "raw", "s2r_m30_VB136.a2.json"))
        raises(Blinded, open, os.path.join(root, "c2", "new.json"), "w")
        with open(os.path.join(fx.ex.tmp, "scripts", "48_s2_analysis.py"), "rb") as fh:
            fh.read(10)
    e = a.log[os.path.realpath(os.path.join(root, "c1", "smoke.json"))]
    assert e["n"] == 3 and e["sha256"] == hashlib.sha256(open(os.path.join(root, "c1", "smoke.json"), "rb").read()) \
        .hexdigest()
    assert ("c2/structures.tar.gz", "a2/s2r_m30_VB76/s2r_m30_VB76.final.extxyz", None, False) in a.members
    assert a.stable() == []
    dump(os.path.join(root, "c2", "gates", "K3.json"), {"x": 2})
    assert a.stable() == ["c2/gates/K3.json"]
    cl = {e_["rel"]: a.classify()[rp] for rp, e_ in a.log.items()}
    assert cl["c1/smoke.json"] == ("archive", "c1") and cl["c2_verify/verify_c2.txt"] == ("head",
                                                                                         "c2_verify/verify_c2.txt")
    assert cl["s2b/E_output.txt"][0] == "exempt" and cl["scripts/48_s2_analysis.py"][0] == "8bff03e"
    assert a.hinge_closed() == []


@case("B12", "B", mutants=(
        # the single-READS check not applied (a second 47 instance unseen)
        ("one_47_unchecked", lambda fx: patched(er, "modules_47", lambda: [fx.ex.q47])),
        # the restated FAR4 table changed (INT-IMPORT must catch it)
        ("far4_drift", lambda fx: patched(eg, "FAR4", {**eg.FAR4, "m05": {**eg.FAR4["m05"], "B": (76, 172, 24, 148)}})),
        # FR_ORDER drift against scripts/49
        ("fr_order_drift", lambda fx: patched(eg, "FR_ORDER", tuple(reversed(eg.FR_ORDER))))))
def case_b12(fx):
    """The 8bff03e import (spec section 2, RF-17, RF-21): every blob checked, the dirname and ROOT assertions, exactly
    one 47 module (gc scan) and a second instance detected; the restated constants and A2 grammar against 8bff03e;
    the FR literals against this checkout's scripts/49 and 50 (ast, never executed) and a drifted copy refused; the
    tree is removable after chmod a-w."""
    ex = fx.ex
    assert len(ex.blobs) > 50 and all(p in ex.blobs for p in er.IMPORT_DATA) and \
        all(ex.blobs[p].startswith(v) for p, v in er.BLOB_PINS.items())
    assert os.path.dirname(ex.q47.__file__) == os.path.join(ex.tmp, "scripts") and ex.m48.ROOT == ex.tmp
    assert not os.access(os.path.join(ex.tmp, "scripts"), os.W_OK)
    assert er.assert_one_47(ex.q47)
    extra = er._load_file("e_extra_47", os.path.join(ex.tmp, "scripts", "47_s2_qe.py"))
    try:
        int_fail("INT-IMPORT", er.assert_one_47, ex.q47)
    finally:
        del extra
        import gc
        gc.collect()
    assert er.assert_one_47(ex.q47)
    assert eg.assert_restated(ex.g49, ex.c46)
    assert er.assert_grammar(ex.g49, eg.FAR + eg.HINGE + eg.FR_ORDER + tuple(ex.g49.A2_ORDER["c4"]))
    with open(os.path.join(REPO, "scripts", "49_s2_gates.py")) as fh:
        s49 = fh.read()
    with open(os.path.join(REPO, "scripts", "50_s2_campaign.py")) as fh:
        s50 = fh.read()
    assert eg.check_fr_constants(s49, s50)
    bad = s49.replace('"D": "s2r_m30_Cs188o0_novac", "DV"', '"D": "s2r_m30_Cs188o0_vac", "DV"', 1)
    assert bad != s49
    int_fail("INT-IMPORT", eg.check_fr_constants, bad, s50)
    bad50 = s50.replace('"cell", "kind")      # decision.FR', '"cell", "kind", "x")      # decision.FR', 1)
    assert bad50 != s50
    int_fail("INT-IMPORT", eg.check_fr_constants, s49, bad50)
    t = tempfile.mkdtemp(prefix="e_ro_", dir=fx.tmp)
    os.makedirs(os.path.join(t, "a", "b"))
    with open(os.path.join(t, "a", "b", "f"), "w") as fh:
        fh.write("x")
    for dp in (os.path.join(t, "a", "b"), os.path.join(t, "a"), t):
        os.chmod(dp, 0o555)
    assert er.remove_tree(t) is None and not os.path.exists(t)


# ---------------------------------------------------------------- E runs on a throwaway git repository (groups C, D, T)
def ee():
    """e_eval.py, loaded under its shared key (RF-19)."""
    return _sibling("e_eval")


GIT_ENV = {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_AUTHOR_NAME": "e-selftest",
           "GIT_AUTHOR_EMAIL": "e-selftest@invalid", "GIT_COMMITTER_NAME": "e-selftest",
           "GIT_COMMITTER_EMAIL": "e-selftest@invalid",
           # fix round 2: no detached auto gc or maintenance after a commit in a throwaway repository (git 2.55 ran
           # one that was still writing packs while a subprocess's fixture was removed: FileNotFoundError, left over)
           "GIT_CONFIG_COUNT": "3", "GIT_CONFIG_KEY_0": "gc.auto", "GIT_CONFIG_VALUE_0": "0",
           "GIT_CONFIG_KEY_1": "maintenance.auto", "GIT_CONFIG_VALUE_1": "false",
           "GIT_CONFIG_KEY_2": "gc.autoDetach", "GIT_CONFIG_VALUE_2": "false"}


def git(repo, *args, date=None):
    """git in a throwaway repository of the self-test (never in this checkout)."""
    env = {**os.environ, **GIT_ENV}
    if date:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = date
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, env=env)
    if r.returncode != 0:
        raise AssertionError(f"git {args[0]}: {r.stderr.decode()[:300]}")
    return r.stdout.decode()


def commit(repo, msg, *paths, date=None):
    git(repo, "add", "-A", "--", *(paths or (".",)))
    git(repo, "commit", "-q", "--allow-empty", "-m", msg, date=date)
    return git(repo, "rev-parse", "HEAD").strip()


def e_sources():
    """repository path -> source path of every E file and tool (this checkout; a placeholder for a missing figure
    script, which engineer C supplies)."""
    out = {}
    for rel in ee().TOOLS:
        src = os.path.join(REPO, rel)
        out[rel] = src if os.path.exists(src) else None
    for rel in ee().SCRIPTS:
        out[rel] = os.path.join(REPO, rel)
    return out


SR = collections.namedtuple("SR", "repo root man commits")


def synth_repo(fx, name, scenario=None, *, e_text=None, dates=None, post=None, extra=None):
    """A throwaway git repository holding the synthetic archive at results/objective2/s2, committed as the
    campaigns would be: (0) scripts/46-50 = the C2 campaign commit; (1) the c1 and c2 archives and the c2 verify
    record = their archive commit; (2) E's files and tools = the fr campaign commit F (fr/campaign.json start_commit
    and commit, commit_history -> F); (3) the fr archive and its verify record. e_text: {repo path: text} replacing
    E's files at F; dates: {step: git date}; extra: {repo path: text} committed with E's files at F (fix round 2)."""
    dates = dates or {}
    d = fx.workdir(f"repo_{name}")
    repo = os.path.join(d, "repo")
    root = os.path.join(repo, "results", "objective2", "s2")
    man = build(root, fx.ex, scenario)
    if post is not None:                                  # a planted change of the archive, before its commits
        post(root, man)
    git(repo, "init", "-q")
    with open(os.path.join(repo, ".git", "info", "exclude"), "w") as fh:
        fh.write("results/objective2/workdir/\nresults/objective2/wp1/\n")
    src = e_sources()
    for rel in ee().SCRIPTS:
        os.makedirs(os.path.dirname(os.path.join(repo, rel)), exist_ok=True)
        shutil.copyfile(src[rel], os.path.join(repo, rel))
    c2c = commit(repo, "C2 campaign commit (synthetic)", "scripts", date=dates.get(0))
    cp = os.path.join(root, "c2", "campaign.json")
    if os.path.exists(cp) and not (scenario or {}).get("c2_commit"):
        with open(cp) as fh:
            cj = json.load(fh)
        cj["commit"] = c2c
        dump(cp, cj)
    dump(os.path.join(root, "c2_verify", "verify_c2.txt"), {"verify": "c2", "result": "ok"})
    with open(os.path.join(root, "c2_verify", "verify_c2.txt"), "a") as fh:
        fh.write("\nverify c2: ok\n")
    arch = commit(repo, "c1 and c2 archives (synthetic)", "results/objective2/s2/c1", "results/objective2/s2/c2",
                  "results/objective2/s2/c2_verify", "results/objective2/s2/C3_OPERATIONS.md", date=dates.get(1))
    for rel in ee().TOOLS:
        dst = os.path.join(repo, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if e_text and rel in e_text:
            with open(dst, "w") as fh:
                fh.write(e_text[rel])
        elif src[rel] is None:
            with open(dst, "w") as fh:
                fh.write('"""placeholder of the E figure script (engineer C)."""\n')
        else:
            shutil.copyfile(src[rel], dst)
    for rel, text in (extra or {}).items():
        write_text(os.path.join(repo, rel), text)
    F = commit(repo, "E code (synthetic fr campaign commit)", "results/objective2/s2/s2b",
               "results/objective2/s2/figures", "results/objective2/s2/c2_diagnostic", *(extra or {}),
               date=dates.get(2))
    last = F
    hist = [{"from": "7" * 40, "to": c2c, "note": "c2/CAMPAIGN_COMMIT", "time": "t", "via": "c2/CAMPAIGN_COMMIT",
             "campaign": "c2"}, {"from": c2c, "to": F, "note": "fr/CAMPAIGN_COMMIT", "time": "t",
                                 "via": "fr/CAMPAIGN_COMMIT", "campaign": "fr"}]
    rep = (man.get("fr") or {}).get("repeat")
    if rep and rep.get("recorded", True):                 # fr/STEP0_FIX: the one other fr route (W 50:2577-2604)
        write_text(os.path.join(repo, FIX_NOTE.split()[1]), f"# FR step-0 fix (synthetic)\n\n{FIX_NOTE.split()[0]}: "
                   f"the fix of the step-0 failure; the failed cell is repeated once (S2B:271-274).\n")
        last = commit(repo, "fr step-0 fix (synthetic STEP0_FIX commit)", FIX_NOTE.split()[1], date=dates.get(2))
        hist.append({"from": F, "to": last, "note": FIX_NOTE, "time": "t", "via": "fr/STEP0_FIX", "campaign": "fr"})
    fj = os.path.join(root, "fr", "campaign.json")
    if os.path.exists(fj):
        with open(fj) as fh:
            cj = json.load(fh)
        cj["start_commit"], cj["commit"] = F, last
        cj["commit_history"] = hist
        dump(fj, cj)
        sj = os.path.join(root, "fr", "state_end.json")
        if os.path.exists(sj):
            with open(sj) as fh:
                st = json.load(fh)
            st["campaign_commit"] = {"fr": last}
            dump(sj, st)
        os.makedirs(os.path.join(root, "fr_verify"), exist_ok=True)
        with open(os.path.join(root, "fr_verify", "verify_fr.txt"), "w") as fh:
            fh.write("verify fr (synthetic)\nverify fr: ok\n")
    frc = commit(repo, "fr archive (synthetic)", date=dates.get(3))
    return SR(repo, root, man, {"c2": c2c, "arch": arch, "F": F, "fr": frc, "last": last})


def e_env(fx, sr, **kw):
    """The self-test environment of one E run on a throwaway repository (spec section 18: injected git, clock)."""
    base = dict(repo=sr.repo, root=sr.root, ex=fx.ex, wp1_dir=sr.man["wp1_dir"], selftest=True,
                c2_commit=sr.commits["c2"], archive_commit={"c1": sr.commits["arch"], "c2": sr.commits["arch"]},
                objects_repo=OBJECTS["repo"], echo=False)
    base.update(kw)
    return ee().Env(**base)


def e_run(fx, sr, argv=("--run",), *, keep=False, **kw):
    """One in-process run of E; returns the Run with .rc, .result_text, .rows, .files ({rel: text} written). The
    written files are removed afterwards (the throwaway tree is clean again) unless keep."""
    r = ee().execute(list(argv), env=e_env(fx, sr, **kw))
    for k in ("T", "ledger", "ctx_T"):                    # memory: the C1 table is not inspected by the cases
        if hasattr(r, k):
            setattr(r, k, None)
    r.files = {}
    for p in r.written:
        with open(p) as fh:
            r.files[os.path.relpath(p, sr.root)] = fh.read()
        if not keep:
            os.remove(p)
    if eg.OpenAudit.current() is not None:
        raise AssertionError("an OpenAudit is still active after the run")
    return r


def cached(fx, key, make):
    """A value cached on the fixture for the base runs of a scenario (never during a mutant run)."""
    if getattr(fx, "mutant", None):
        return make()
    c = fx.__dict__.setdefault("_cache", {})
    if key not in c:
        c[key] = make()
    return c[key]


# ---------------------------------------------------------------- group C: blocks and routes (spec 18 C; S2B §§1, 11)
SCEN = {                                                 # S2B section 11 rows that can occur before C3b
    "C1a": {"fr": {"cells": {"V": {"valid": False, "failed": [5]}}}},                       # V+-host check 5
    # fix round 2: C1b, C1c and C1n carry validity_final {valid True, failed []}, as scripts/50 a2v_status writes it
    # for a complete relaxation with a final geometry (I-F1): only the end-rule clause lists them in table 3.6
    "C1b": {"fr": {"cells": {"V": {"outcome": "unconverged_cap", "n_config": 201, "plateau_Ry": "0.0005"}}}},
    "C1c": {"fr": {"cells": {"host": {"outcome": "accepted_plateau", "n_config": 201, "plateau_Ry": "0.00001"},
                             "D": {"outcome": "unconverged_early"}}}},                        # plateau host; bfgs
    "C1d": {"fr": {"cells": {"host": {"status": "missing"}}}},
    "C1e": {"fr": {"cells": {"DV": {"status": "not_started_cap"}}}},                         # hard-cap refusal
    "C1f": {"fr": {"cells": {"DV": {"valid": False, "failed": [5]}}}},                       # equal-charge pair
    "C1g": {"fr": {"cells": {"D": {"valid": False, "failed": [3]}}}},
    "C1h": {"fr": {"step0_fail": "V"}},                                                      # killed at @2 (RF-5)
    "C1i": {"fr": {"delta_meV": "50.001"}},                                                  # FR-2 fails
    "C1i_neg": {"fr": {"delta_meV": "-50.001"}},
    "C1j": {"fr": {"status": "stopped", "stop_reason": "operator final STOP (synthetic)",
                   "cells": {"D": {"status": "absent"}}}},                                   # final STOP in fr
    "C1k": {"fr": {"cells": {"D": {"n_config": 0, "outcome": "unconverged_early", "end": "scf_failed",
                                   "check": False}}}},                                       # RF-4: SCF fails at k = 0
    "C1l": {"fr": {"cells": {"host": {"n_config": 21},                                       # RF-4: k_last 20; fix
                             "V": {"valid": False, "failed": [5], "n_config": 37}}}},        # round 2: k_last 36
    "C1m": {"fr": {"step0_fail": "DV"}},                                                     # killed at @4 (RF-5)
    "C1n": {"fr": {"cells": {"DV": {"outcome": "unconverged_early"}}}},                       # OP-29 end-rule variant
    # fix round 1: RF-4 at the step-0 cells; no final-geometry check; STOP headers; the step-0 repeat (S2B:271-274)
    "C1k_V": {"fr": {"cells": {"V": {"n_config": 0, "outcome": "unconverged_early", "end": "scf_failed",
                                     "check": False}}}},
    "C1k_DV": {"fr": {"cells": {"DV": {"n_config": 0, "outcome": "unconverged_early", "end": "scf_failed",
                                       "check": False}}}},
    "C1s_V": {"fr": {"cells": {"V": {"check": False}}}},                                      # no validity_final
    "C1s_DV": {"fr": {"cells": {"DV": {"check": False}}}},                                    # the quartet complete
    "C1t_pending": {"fr": {"status": "stopped", "stop_reason": "operator final STOP (synthetic)",
                           "cells": {"D": {"status": "pending"}}}},
    "C1t_gate": {"fr": {"status": "stopped", "stop_reason": "operator final STOP (synthetic)"}},   # before gate FR
    "C1o": {"fr": {"repeat": {"role": "V", "after": "pass"}, "cells": {"DV": {"valid": False, "failed": [5]}}}},
    "C1p": {"fr": {"repeat": {"role": "DV", "after": "fail_final"}}},
    "C1q": {"fr": {"repeat": {"role": "DV", "after": "stopped"}, "status": "stopped",
                   "stop_reason": "operator final STOP during the step-0 repeat (synthetic)"}},
    "C1q_norepeat": {"fr": {"status": "stopped", "stop_reason": "operator final STOP (synthetic)",
                            "cells": {"DV": {"status": "absent"}}}},
    # fix round 2 (R-1): the set-aside rule, one conjunct at a time, and the two repeat routes not built before
    "C1q_unrec": {"fr": {"repeat": {"role": "DV", "after": "stopped", "recorded": False}, "status": "stopped",
                         "stop_reason": "operator final STOP during the step-0 repeat (synthetic)"}},
    "C1q_vstop": {"fr": {"repeat": {"role": "V", "after": "stopped"}, "status": "stopped",
                         "stop_reason": "operator final STOP during the step-0 repeat at VA188 (synthetic)"}},
    # integration review 3 (IX-11 at @2): the @2 move made, the STEP0_FIX save not
    "C1q_vunrec": {"fr": {"repeat": {"role": "V", "after": "stopped", "recorded": False}, "status": "stopped",
                          "stop_reason": "operator final STOP during the step-0 repeat at VA188 (synthetic)"}},
    "C1q_dvpend": {"fr": {"repeat": {"role": "V", "after": "pass"}, "status": "stopped",
                          "stop_reason": "operator final STOP (synthetic)",
                          "cells": {"DV": {"status": "pending", "step0": True}}}},             # @4 ran
    "C1q_dvnotrun": {"fr": {"repeat": {"role": "V", "after": "pass"}, "status": "stopped",
                            "stop_reason": "operator final STOP (synthetic)",
                            "cells": {"D": {"outcome": "unconverged_early", "check": False}}}},  # D+V+ not_run_gate
    "C1q_pend": {"fr": {"repeat": {"role": "V", "after": "pass"}, "status": "stopped",
                        "stop_reason": "operator final STOP (synthetic)", "cells": {"DV": {"status": "pending"}}}},
    # fix round 2: a final STOP after a step-0 failure pending its fix (fail_pending_fix), at @2 and at @4
    "C1u_2": {"fr": {"step0_pending": "V", "status": "stopped",
                     "stop_reason": "operator final STOP after the step-0 failure at VA188 (synthetic)"}},
    "C1u_4": {"fr": {"step0_pending": "DV", "status": "stopped",
                     "stop_reason": "operator final STOP after the step-0 failure at Cs188o0_vac (synthetic)"}},
    # integration review 1 (IX-4): a final STOP after a recorded FR outcome (a STOP held until gate FR was applied,
    # W 50 N-F20; or fr/STEP0_NO_ERROR, then a STOP before CAMPAIGN_DONE)
    "C1v_fr1": {"fr": {"cells": {"D": {"outcome": "unconverged_early"}}, "status": "stopped", "gate_fr": True,
                       "stop_reason": "held STOP: s2r_m30_Cs188o0_novac ended unconverged_early (synthetic)"}},
    "C1v_fr2": {"fr": {"delta_meV": "50.001", "status": "stopped", "gate_fr": True,
                       "stop_reason": "operator final STOP after gate FR (synthetic)"}},
    "C1v_pass": {"fr": {"status": "stopped", "gate_fr": True,
                        "stop_reason": "operator final STOP after gate FR (synthetic)"}},
    "C1v_noerr": {"fr": {"step0_fail": "DV", "status": "stopped",
                         "stop_reason": "operator final STOP after fr/STEP0_NO_ERROR (synthetic)"}},
    # integration review 2: the other source of the step-0 final, a failed repeat (gate fr_step0 records fail_final
    # at attempt 2; W 50 begin_stop then records fr_outcome step-0 final), then a final STOP
    "C1v_s0final": {"fr": {"repeat": {"role": "DV", "after": "fail_final"}, "status": "stopped",
                           "stop_reason": "operator final STOP after the step-0 repeat failed (synthetic)"}},
    "pass": {},                                                                              # FR passes
    "pass_50": {"fr": {"delta_meV": "49.9999"}},                                             # |delta| = 50.000
    "inv": {"fr": {"cells": {"V": {"invariant_only": True}}}},                               # invariant-only pass
    "A4": {"fr": {"cells": {"V": {"valid": False, "failed": [5]}}}, "k3_value_meV": 1111.111},   # a non-null value
}
HDR = ("S2 K3: fail (fail_replan); checks_failed: s2r_m30_VB76, check 5 (C2_RESULT.md). S2b FR: {}. Valid far "
       "references: {} of 2.")
LABELS = {          # spec section 9 (S2B:623-631, 645, 649, 659-660, 667-675, 702-708, 731), restated
    "L_ITEM4": "S2 K3 failed (far quartet invalid); A1 not validated against A2 at the far site",
    "L_FRVALID": "far-site reference: FR, m30 FA188, valid",
    "L_MACE": "zero-shot MACE, not re-admitted",
    "L_FAR": "far quartet invalid (check 5, VB76); reported only; not valid",
    "L_TAIL": "path energy of the whole region over the window; not attributable to the failing objects; bounds no "
              "E_b error; reported only",
    "L_FR2": "FR-2 failed (|δ_far(FA188)| > 50 meV in one quartet; bias and site scatter not separable); "
             "reported only",
    "L_FRNOTEVAL": "gate FR not evaluated (final STOP in fr); reported only; not valid",          # fix round 2
    "L_FRSTOP": "gate FR passed, then a final STOP in fr (S2B section 1); reported only; not valid",   # IX-12
    "L_NOFORM_C1": "not formable from C1 single points (no A2 cell)",
    "L_NOA1": "no A1 DFT value",
    "L_HINGE_DIFF": "not a K3 decision; K3 failed on validity",
    "L_CA_Q0": "not formable: no F of Ca D(136)",
    "L_CA_MACE": "no DFT A1 E_b (Ca failed G1)",
    "L_FALLBACK": "recorded by gate code; not cross-checked (E failed twice)",
    "L_NOTREAD": "not read: E failed",
    "L_XFAIL": "cross-check failed",
    "L_Q0": "q = 0 link row (§10), reported only",
    "L_WP2C": "WP2c: whole-cell WP1 MACE geometry, q = 0, one far site (different protocol)",
    "L_NOA2": "no S2 A2 cell",
    "L_C4BNOTRUN": "C4b not run",
    "L_A1TIER": "fixed-geometry DFT; relaxation bias not bounded. Far-site A2 reference valid at pilot host m30, FA188 "
                "only (Cs, A f₁, 11.25 Å; S2b FR){clause}. Invalid at m30 Pb76 (Sr, B f₁, 11.81 Å; C2, check 5). "
                "Valid far references: 1 of 2. No production-host far site is tested at A2. S2 K3: fail_replan; its "
                "value test (P:644-646) was not reached, and no A2 test of the first shell gates this tier.",
}
B4_TRUE = None


def block4_true_text():
    """e_block4.py with BLOCK4_IMPLEMENTED = True, committed in a throwaway repository for the test double routes
    (RF-3: block 4 with its implementation at the c3b start commit)."""
    with open(os.path.join(HERE, "e_block4.py")) as fh:
        t = fh.read()
    assert "\nBLOCK4_IMPLEMENTED = False\n" in t
    return t.replace("\nBLOCK4_IMPLEMENTED = False\n", "\nBLOCK4_IMPLEMENTED = True\n", 1)


def repo_of(fx, name, scenario=None, **kw):
    """A cached throwaway repository of a named scenario; the cases treat it as read-only (E's outputs removed)."""
    c = fx.__dict__.setdefault("_repos", {})
    if name not in c:
        if name in ("pass", "pass_50", "inv"):
            kw.setdefault("e_text", {f"{ee().S2_REL}/s2b/e_block4.py": block4_true_text()})
        c[name] = synth_repo(fx, name, SCEN.get(name, scenario), **kw)
        if name not in ("C1f", "C1i"):
            slim(c[name].man)
    return c[name]


def slim(man):
    """Drop the printed strings and position functions of a cached manifest (C2 alone needs them)."""
    for rels in (man.get("c2") or {}, (man.get("fr") or {}).get("rel") or {}):
        for v in rels.values():
            for k in ("printed", "pos", "frc", "final_bytes", "record"):
                v.pop(k, None)


def run_of(fx, name, argv=("--run",), **kw):
    """The cached base run of a scenario (a fresh run during a mutant)."""
    sr = repo_of(fx, name)
    return cached(fx, ("run", name, tuple(argv)), lambda: e_run(fx, sr, argv, **kw)), sr


class B4Double:
    """A test double of e_block4 (spec 18 C6, C7, C9): BLOCK4_IMPLEMENTED True; a fixed route and df_delta; records
    the hinge value passed to evaluate_tier."""
    BLOCK4_IMPLEMENTED = True

    def __init__(self, route_id, df_delta, F):
        self.route_id, self.df, self.F, self.calls, self.labels = route_id, df_delta, F, [], None

    def tier_route(self, run):
        return {"id": self.route_id, "commits": {"c3b_start": self.F, "c3b": self.F, "c4b": self.F}}

    def c4b_df_delta_validity(self, run):
        return {"df_delta": self.df, "m_d": {}, "units": [], "function": "test double", "blob": "0" * 40}

    def build_tier_table(self, run, c1, fr):
        return {"schema": "test double"}

    def evaluate_tier(self, table, fr, *, hinge=None):
        self.calls.append(hinge)
        return {"hinge": hinge, "fr": fr}

    def rows(self, result, labels):
        self.labels = labels
        return [ee().Row(4, "B4.double", "note", "A1 tier (test double)", {}, ["L_A1TIER"], False)]

    def manifest(self, run, c):
        raise AssertionError("no private archive in the test double")


def hinge_canaries(sr):
    """Strings that appear only if a hinge or Pb136 value was printed: the K3 hinge value, F(0) and F(final) of
    relaxations 1-4, the Pb136 MACE canaries and the Pb136 single-point F."""
    man, r = sr.man, float(RY)
    out = ["%.2f" % man["k3"]["hinge"]]
    for lab in eg.HINGE:
        F = man["c2"][lab]["F"]
        out += ["%.6f" % (float(F[0]) * r), "%.6f" % (float(F[-1]) * r)]
    for w in eg.PB136_WIDS:
        out += ["%.6f" % v for _, v in man["c1_mace"][w]]
    out += ["%.6f" % (float(sp_F(lab)) * r) for lab in eg.PB136_SP]
    return out


def assert_closed_paths(r):
    """No hinge output, hinge member, Pb136 C1 output or Pb136 MACE record was opened (S2B:561-562, 610)."""
    for e in r.au.log.values():
        segs = e["rel"].split("/")
        if segs[:2] == ["c2", "raw"] and segs[2].split(".")[0] in eg.HINGE:
            assert segs[2].endswith(".a2.json") and e["via"] == "a2_hinge_counts", e["rel"]
        if segs[:2] == ["c1", "raw"]:
            assert segs[2].split(".")[0] not in eg.PB136_SP + eg.NEVER_SP, e["rel"]
    for rel, name, blk, hg in r.au.members:
        assert not any(name.startswith(f"a2/{lab}/") for lab in eg.HINGE), name
    for w, blind, blk in r.c1.log:
        assert w not in eg.PB136_WIDS or blind, w


def rows_by(r, pre):
    return [x for x in r.rows if x.id.startswith(pre)]


def row(r, rid):
    got = [x for x in r.rows if x.id == rid]
    assert len(got) == 1, (rid, len(got))
    return got[0]


def assert_fr_fail(r, sr, part, k, *, block4="BLOCK 4. Tier block: not printed (FR failed)"):
    """The common asserts of every FR-fail scenario (spec 18 C, first paragraph)."""
    t = r.result_text
    assert r.rc == 0, (r.rc, t[-1500:])
    hdr = HDR.format(part, k)
    lines = t.split("\n")
    assert lines.count(hdr) == 4, (hdr, [x for x in lines if x.startswith("S2 K3")][:2])   # top and blocks 1-3
    for b in ("BLOCK 1. Far block", "BLOCK 2. FR block", "BLOCK 3. MACE"):
        i = next(i for i, x in enumerate(lines) if x.startswith(b))
        assert lines[i + 1] == hdr, b
    assert block4 in lines and sum(x.startswith("BLOCK 5. Hinge block: not opened.") for x in lines) == 1
    item4 = ee().L["L_ITEM4"]
    a1rows = [x for x in r.rows if x.kind in ("Eb_A1", "Eb_q0", "Eb_q1") or x.has_a1]
    assert a1rows and all("L_ITEM4" in x.labels and "L_FRVALID" not in x.labels for x in a1rows)
    assert t.count(item4) >= len(a1rows)
    assert "class" not in ee().Row.__slots__ and not any(c in t for c in ("repels", "binds", "no first-shell"))
    for s in hinge_canaries(sr):
        assert s not in t, f"hinge or Pb136 value {s} printed"
    assert_closed_paths(r)
    fr_ok = {lab for lab in eg.FR_ORDER if sr.man["fr"]["recs"].get(lab, {}).get("status") == "complete"}
    assert set(r.ctx.reads.labels["a2"]) <= set(eg.FAR) | fr_ok
    assert set(r.ctx.reads.labels["sp"]) <= eg.BLOCK3_SP
    assert r.files and all(v.rstrip("\n").split("\n")[-1] == f"E exit code: {r.rc}" for k_, v in r.files.items()
                           if k_.endswith(".txt"))


def patch_attr(obj, attr, value):
    return patched(obj, attr, value)


@case("C1a", "C", mutants=(
        # the header reason of FR-1 lost
        ("fr_reason_lost", lambda fx: patched(ee(), "fr_reason", lambda kind, failed=None, outcome=None: "kind")),
        # the item-4 label not attached to the q = 0 rows
        ("q0_item4_lost", lambda fx: patched(ee().Out, "row", _wrap_no_q0(ee().Out.row)))))
def case_c1a(fx):
    """FR stops at the V+-host check 5 (D and DV not_run_gate): header 'fail (FR-1, s2r_m30_VA188, check 5)' and
    '0 of 2'; the FA188 values 'not formed (quartet incomplete: ...)' with the not-run variant of L_FR1; the
    common FR-fail asserts (blocks, header in every block, item-4 label, no class, no hinge or Pb136 value or path,
    READS labels within the blocks run)."""
    r, sr = run_of(fx, "C1a")
    assert_fr_fail(r, sr, "fail (FR-1, s2r_m30_VA188, check 5)", 0)
    for rid in ("B3.q0.Sr76", "B3.q0.Cl138", "B3.q0.Cs128", "B3.q1.Sr76", "B1.EbA1", "B2.step0.s2_m30_VA188.dF"):
        x = row(r, rid)
        assert ("L_ITEM4" in x.labels) == (rid != "B2.step0.s2_m30_VA188.dF"), rid
    q = row(r, "B2.quartet")
    assert q.text.startswith("not formed (quartet incomplete: s2r_m30_Cs188o0_novac not_run_gate") and \
        "L_FR1" in q.labels
    assert "FR quartet incomplete (s2r_m30_Cs188o0_novac not_run_gate); reported only; not valid" in r.result_text


def _wrap_no_q0(orig):
    def f(self, block, rid, kind, text, **kw):
        return orig(self, block, rid, "note" if kind == "Eb_q0" else kind, text, **kw)
    return f


@case("C1b", "C", mutants=(
        # the plateau difference not printed from the parse
        ("no_plateau_line", lambda fx: patched(ee().Run, "print_relax", _wrap_no_plateau(ee().Run.print_relax))),))
def case_c1b(fx):
    """V+ unconverged_cap (plateau failed): 'end rule unconverged_cap' in the header; 'plateau difference F(200) -
    F(180)' printed from the parse; the record's dF_200_180_meV canary is never printed."""
    r, sr = run_of(fx, "C1b")
    assert_fr_fail(r, sr, "fail (FR-1, s2r_m30_VA188, end rule unconverged_cap)", 0)
    p = row(r, "B2.s2r_m30_VA188.plateau")
    F = sr.man["fr"]["rel"]["s2r_m30_VA188"]["F"]
    want = (Fraction(F[200]) - Fraction(F[180])) * RY * 1000
    assert abs(p.values["plateau_meV"] - float(want)) <= 1e-6 and "from the parse" in p.text
    assert "9876.54" not in r.result_text and "9876.5" not in r.result_text
    _assert_endrule_listed(r, "s2r_m30_VA188", "unconverged_cap")


def _assert_endrule_listed(r, lab, outcome):
    """Fix round 2 (M43): a cell whose final-geometry check passed (validity_final valid True, as scripts/50 writes
    it) but whose end rule is not accepted is listed in table 3.6 by the end-rule clause alone; block 2 prints its
    validity leaves."""
    x = row(r, f"B3.inv.fr.{lab}")
    assert f"end rule {outcome}; failed []" in x.text, x.text
    assert "validity_final valid True failed []" in row(r, f"B2.{lab}.status").text


def _wrap_no_plateau(orig):
    def f(self, o, block, r, **kw):
        kw["plateau"] = False
        return orig(self, o, block, r, **kw)
    return f


@case("C1c", "C", mutants=(
        # a plateau-accepted host counted as an FR-1 failure by E's recompute
        ("plateau_rejected", lambda fx: patched(eg, "END_ACCEPTED", ("accepted_converged",))),))
def case_c1c(fx):
    """host_R accepted_plateau (it continues), then Cs D unconverged_early (bfgs_failed): 'end rule
    unconverged_early'; the host's plateau difference is printed; XC-FR1-DEC holds."""
    r, sr = run_of(fx, "C1c")
    assert_fr_fail(r, sr, "fail (FR-1, s2r_m30_Cs188o0_novac, end rule unconverged_early)", 0)
    assert "plateau difference F(200) − F(180)" in row(r, "B2.s2r_m30_hostA188.plateau").text
    assert row(r, "XC-FR1-DEC").text.endswith(": ok")
    _assert_endrule_listed(r, "s2r_m30_Cs188o0_novac", "unconverged_early")


@case("C1d", "C", mutants=(
        ("missing_reason", lambda fx: patched(ee(), "FR_REASON", {**ee().FR_REASON, "missing": "absent"})),))
def case_c1d(fx):
    """host_R missing: 'fail (FR-1, s2r_m30_hostA188, missing)'; no part of any FR cell is opened; no fr step-0 file
    exists or is read (RF-12: V+ never reached k = 0)."""
    r, sr = run_of(fx, "C1d")
    assert_fr_fail(r, sr, "fail (FR-1, s2r_m30_hostA188, missing)", 0)
    assert not [e["rel"] for e in r.au.log.values() if e["rel"].startswith("fr/raw/") and ".out" in e["rel"]]
    assert "no fr step-0 evaluation ran" in row(r, "B2.step0").text


@case("C1e", "C", mutants=(
        ("cap_reason", lambda fx: patched(ee(), "FR_REASON", {**ee().FR_REASON, "not_started_cap": "cap"})),))
def case_c1e(fx):
    """Cs D+V+ hard-cap refusal (not_started_cap): 'fail (FR-1, s2r_m30_Cs188o0_vac, hard-cap refusal)'; step 0 at
    @2 only."""
    r, sr = run_of(fx, "C1e")
    assert_fr_fail(r, sr, "fail (FR-1, s2r_m30_Cs188o0_vac, hard-cap refusal)", 0)
    assert rows_by(r, "B2.step0.s2_m30_VA188") and not rows_by(r, "B2.step0.s2_m30_Cs188o0_vac")


@case("C1f", "C", mutants=(
        # the check variant of L_FR1 replaced by the not-run variant
        ("fr1_label_variant", lambda fx: patched(ee(), "L_FR1", lambda kind, cell, detail:
                                                 f"FR quartet incomplete ({cell} {kind}); reported only; not valid")),))
def case_c1f(fx):
    """The equal-charge pair fails (D+V+ against V+, check 5; the quartet is complete): L_FR1 '(check 5,
    s2r_m30_Cs188o0_vac)' on all three FA188 values; XC-FR2 reads 'gate FR recorded no FR-2 values (FR-1 failed)'
    and XC-FR2-DEC 'FR-2 not evaluated (FR-1 failed)' (RF-22); exit 0."""
    r, sr = run_of(fx, "C1f")
    assert_fr_fail(r, sr, "fail (FR-1, s2r_m30_Cs188o0_vac, check 5)", 0)
    lab = "FR quartet invalid (check 5, s2r_m30_Cs188o0_vac); reported only; not valid"
    for rid in ("B2.EbA1", "B2.EbA2", "B2.delta"):
        assert "L_FR1" in row(r, rid).labels
    assert r.result_text.count(lab) == 3
    assert "XC-FR2: gate FR recorded no FR-2 values (FR-1 failed)" in r.result_text
    assert "XC-FR2-DEC: FR-2 not evaluated (FR-1 failed)" in r.result_text


@case("C1n", "C", mutants=(
        # the end-rule variant of L_FR1 replaced by the check variant
        ("fr1_endrule_variant", lambda fx: patched(ee(), "L_FR1", lambda kind, cell, detail:
                                                   f"FR quartet invalid (check {detail}, {cell}); reported only; "
                                                   f"not valid")),))
def case_c1n(fx):
    """OP-29, the end-rule variant of L_FR1 (engineer C): Cs D+V+ unconverged_early (bfgs_failed) with the quartet
    complete: header 'fail (FR-1, s2r_m30_Cs188o0_vac, end rule unconverged_early)'; 'FR quartet invalid (end rule
    unconverged_early, s2r_m30_Cs188o0_vac); reported only; not valid' on all three FA188 values; exit 0."""
    r, sr = run_of(fx, "C1n")
    assert_fr_fail(r, sr, "fail (FR-1, s2r_m30_Cs188o0_vac, end rule unconverged_early)", 0)
    lab = "FR quartet invalid (end rule unconverged_early, s2r_m30_Cs188o0_vac); reported only; not valid"
    for rid in ("B2.EbA1", "B2.EbA2", "B2.delta"):
        assert "L_FR1" in row(r, rid).labels
    assert r.result_text.count(lab) == 3
    _assert_endrule_listed(r, "s2r_m30_Cs188o0_vac", "unconverged_early")


@case("C1g", "C", mutants=(
        ("check_list_lost", lambda fx: patched(ee(), "checks_str", lambda failed: "?")),))
def case_c1g(fx):
    """Check 3 fails at Cs D: 'fail (FR-1, s2r_m30_Cs188o0_novac, check 3)'."""
    r, sr = run_of(fx, "C1g")
    assert_fr_fail(r, sr, "fail (FR-1, s2r_m30_Cs188o0_novac, check 3)", 0)


@case("C1h", "C", mutants=(
        ("gate_label_lost", lambda fx: patched(ee(), "STEP0_GATE", "recorded")),))
def case_c1h(fx):
    """Step-0 final at @2 (VA188 killed_by_gate, no raw part; RF-5): header 'fail (step-0 final; gate not
    evaluated)'; block 2.2 prints the gate-recorded dF_meV and passed of gate_fr_step0_2 'recorded by gate code'
    and 'cell killed by the step-0 gate; output set aside, not archived'; no FR.json is read. Integration (IX-2):
    the failure is made final by fr/STEP0_NO_ERROR as W 50 applies it (the gate files keep 'fail_pending_fix',
    fr/state_end.json reads 'fail_final' with no_error_found): exit 0 (no INT-FR-DEC) and the B2.step0.no_error row."""
    r, sr = run_of(fx, "C1h")
    assert_fr_fail(r, sr, "fail (step-0 final; gate not evaluated)", 0)
    g = row(r, "B2.step0.s2_m30_VA188.gate")
    assert "recorded by gate code" in r.result_text and "passed False" in g.text and \
        abs(g.values["dF_meV_gate"] - 0.731) < 1e-12
    assert "decision fail_pending_fix" in g.text and "no_error_found absent" in \
        row(r, "B2.step0.s2_m30_VA188.decision").text
    assert row(r, "B2.step0.no_error").text == (
        "fr_step0@2: final, no writer or input error found (fr/state_end.json fr_step0: outcome fail_final, "
        "no_error_found True; fr/STEP0_NO_ERROR, W 50 preconditions); the gate files keep attempt 1's decision "
        "fail_pending_fix")
    assert row(r, "B2.step0.s2_m30_VA188").text.endswith("cell killed by the step-0 gate; output set aside, "
                                                         "not archived")
    assert not any(e["rel"].startswith("fr/gates/FR") for e in r.au.log.values())


@case("C1i", "C", mutants=(
        # k counts FR as a whole instead of the valid far quartets (OP-11)
        ("k_counts_fr", lambda fx: patched(ee(), "valid_far_refs", lambda dec: 1 if (dec or {}).get("outcome") ==
                                           "pass" else 0)),
        ("fr2_label_lost", lambda fx: patched(ee(), "L", {**ee().L, "L_FR2": "FR-2 failed"}))))
def case_c1i(fx):
    """FR-1 passes and FR-2 fails (delta = +50.001 meV): header 'fail (FR-2)' and '1 of 2'; L_FR2 on the FA188
    values; XC-FR2 and XC-FR2-DEC ok. The same at -50.001 meV."""
    r, sr = run_of(fx, "C1i")
    assert_fr_fail(r, sr, "fail (FR-2)", 1)
    for rid in ("B2.EbA1", "B2.EbA2", "B2.delta"):
        assert "L_FR2" in row(r, rid).labels
    assert r.result_text.count(LABELS["L_FR2"]) == 3
    assert all(x.text.endswith(": ok") for x in r.rows if x.id in ("XC-FR2", "XC-FR2-DEC"))
    d = row(r, "B2.delta").values["delta_meV"]
    assert 50.0005 < d < 50.0015, d
    pinned = [row(r, "B2.EbA1"), row(r, "B2.delta"), row(r, "XC-FR2-DEC"), row(r, "XC-DSUM-FR")] + \
        [x for x in r.rows if x.id == "XC-FR2" and x.text.startswith(("XC-FR2: Eb_A1_meV", "XC-FR2: delta_far_meV"))]
    assert len(pinned) == 8 and all("L_ITEM4" in x.labels and _labelled(r, x, "L_ITEM4") for x in pinned)
    assert not any("L_ITEM4" in x.labels for x in r.rows if x.id == "XC-FR2" and "Eb_A2_meV" in x.text[:20])
    assert repr(d) in row(r, "XC-FR2-DEC").text               # the full-precision delta beside the 0.01 meV one
    r2, sr2 = run_of(fx, "C1i_neg")
    assert_fr_fail(r2, sr2, "fail (FR-2)", 1)
    assert -50.0015 < row(r2, "B2.delta").values["delta_meV"] < -50.0005


def stop_repo(fx, name="C1j", scenario=None, post=None):
    sr = repo_of(fx, name, scenario, post=post)
    note = f"{ee().S2_REL}/FR_STOP_NOTE.md"
    if not os.path.exists(os.path.join(sr.repo, note)):
        with open(os.path.join(sr.repo, note), "w") as fh:
            fh.write("# FR stop note (synthetic)\n\n2026-11-21: the fr STOP is final; no relaunch.\n")
        commit(sr.repo, "stop note")
    return sr, note


@case("C1j", "C", mutants=(
        ("stop_without_note", lambda fx: patched(ee(), "stop_note_ok", lambda path, text: True)),
        # IX-6 reverted: any path admitted again (the place under S2/, not under s2b/, as before integration review 1)
        ("stop_note_any_path", lambda fx: patched(ee(), "STOP_NOTE", _AnyPath())),))
def case_c1j(fx):
    """A final STOP in fr: without --stop-note exit 2 (nothing written); with a note that does not state the STOP
    is final, exit 2; with the note, header 'stopped at s2r_m30_Cs188o0_novac (operator final STOP (synthetic))'
    and 'BLOCK 4. Tier block: not printed (final STOP in fr)'. Integration review 1 (IX-6, amendment item 12): the
    stop note is the one file results/objective2/s2/FR_STOP_NOTE.md. Refused (exit 2, nothing written): every other
    path, each holding the phrase on one line with an ISO date (S2B_PLAN.md, FR_OPERATIONS.md, a second note, a note
    under s2b/), C3_OPERATIONS.md, and the glob paths FR_STOP_NO*.md and FR_STOP_NOTE.* with the fixed file present
    (whose 'text' was the HEAD commit, which holds the note); at the fixed path, the note undated, without the phrase,
    edited in the tree (the clean-tree test), and a directory of that name whose tree listing holds the phrase and a
    date (git cat-file -t is not 'blob')."""
    sr, nt = stop_repo(fx)
    assert nt == f"{S2R}/FR_STOP_NOTE.md"
    r0 = e_run(fx, sr, ["--run"])
    assert r0.rc == 2 and not r0.written
    valid = "# FR stop note (synthetic)\n\n2026-11-21: the fr STOP is final; no relaunch.\n"
    one = "the stop note is the one file results/objective2/s2/FR_STOP_NOTE.md (IX-6)"
    for rel in (f"{S2R}/FR_STOP_NO*.md", f"{S2R}/FR_STOP_NOTE.*", f"{S2R}/C3_OPERATIONS.md"):
        rb = e_run(fx, sr, ["--run", "--stop-note", rel])
        assert rb.rc == 2 and not rb.written and one in rb.result_text, (rel, rb.result_text[-300:])
    # fix round 2 (M12, M13) and IX-6: dated final notes at other paths are refused by the path rule
    for rel in (f"{S2R}/S2B_PLAN.md", f"{S2R}/FR_OPERATIONS.md", f"{S2R}/FR_STOP_NOTE_2.md", f"{S2R}/s2b/STOP.md"):
        note(sr, rel, "# a synthetic note\n\n2026-11-21: the fr STOP is final.\n")
        rb = e_run(fx, sr, ["--run", "--stop-note", rel])
        assert rb.rc == 2 and not rb.written and one in rb.result_text, (rel, rb.result_text[-300:])
    for text in ("# FR stop note (synthetic)\n\nthe fr STOP is final.\n",
                 "# FR stop note (synthetic)\n\n2026-11-21: fr stopped; the route is still open.\n"):
        note(sr, nt, text)
        rb = e_run(fx, sr, ["--run", "--stop-note", nt])
        assert rb.rc == 2 and not rb.written and "stating that the fr STOP is final (OP-19)" in rb.result_text, \
            (text, rb.result_text[-300:])
    note(sr, nt, valid)
    write_text(os.path.join(sr.repo, nt), valid + "edited in the tree\n")
    try:                                                  # E's clean-tree test refuses first (phase 0a)
        rb = e_run(fx, sr, ["--run", "--stop-note", nt])
    finally:
        write_text(os.path.join(sr.repo, nt), valid)
    assert rb.rc == 2 and not rb.written and "not clean" in rb.result_text, rb.result_text[-300:]
    st = repo_of(fx, "C1j_tree", SCEN["C1j"])             # IX-6: a tree at the fixed path, never a note
    note(st, f"{nt}/2026-11-21 the fr STOP is final.md", "a file inside a directory named as the note\n")
    rb = e_run(fx, st, ["--run", "--stop-note", nt])
    assert rb.rc == 2 and not rb.written and "is not a file of HEAD" in rb.result_text, rb.result_text[-300:]
    r = cached(fx, ("run", "C1j", "note"), lambda: e_run(fx, sr, ["--run", "--stop-note", nt]))
    assert_fr_fail(r, sr, "stopped at s2r_m30_Cs188o0_novac (operator final STOP (synthetic))", 0,
                   block4="BLOCK 4. Tier block: not printed (final STOP in fr)")


class _AnyPath(str):
    """A STOP_NOTE that every path equals (the IX-6 path rule removed, for the mutant of C1j)."""

    def __new__(cls):
        return super().__new__(cls, f"{S2R}/FR_STOP_NOTE.md")

    def __eq__(self, other):
        return isinstance(other, str)

    def __ne__(self, other):
        return not isinstance(other, str)

    __hash__ = str.__hash__


def _no_stop_decision(self):
    return None


@case("C1v", "C", mutants=(
        # IX-4 reverted: the decision recorded before the STOP not read (the header of ER2-13 alone)
        ("stop_decision_unread", lambda fx: patched(ee().Run, "stop_decision", _no_stop_decision)),
        # IX-12 reverted: L_FRSTOP dropped (E_b^A2(FA188) after 'pass at gate FR; then a final STOP' unlabelled)
        ("frstop_label_dropped", lambda fx: patched(ee().Run, "frstop_pass", lambda self, outcome: False)),
        # IX-12 widened: L_FRSTOP on every gate FR pass, the done FR-pass route too
        ("frstop_any_route", lambda fx: patched(ee().Run, "frstop_pass", lambda self, outcome: outcome == "pass"))))
def case_c1v(fx):
    """IX-4 (amendment item 13): a final STOP after a recorded FR outcome is 'FR fails' (S2B §1). On each route the
    header names the recorded decision in the done routes' words, then 'then a final STOP (<stop reason>)', and a
    recorded pass adds 'counted as FR fails (S2B §1)'; 'Valid far references: 0 of 2'; item 4 is L_ITEM4 on every A1
    row and L_FRVALID is printed nowhere. Routes: FR-1 failed on Cs D's end rule (the STOP W 50 held until gate FR,
    N-F20); FR-2 failed; FR passed; fr/STEP0_NO_ERROR at @4, then a STOP (no fr/state_end.json: the fr_outcome W 50
    begin_stop records in fr/campaign.json; B2.step0.no_error names it); integration review 2: the step-0 repeat at @4
    failed at attempt 2 (gate fr_step0 fail_final), then a STOP (Run.stop_decision, branch fail_final). INT-ROUTE (exit
    3): an fr_outcome at the STOP that disagrees with gate FR; a step-0 final with no failed step-0 decision behind it;
    an outcome with no decision at all; no fr_outcome recorded at the STOP (W 50 begin_stop always records it, null
    included); integration review 2: fr_outcome null after the attempt-2 fail_final; the STEP0_NO_ERROR route with the
    @4 decision at attempts 2 (fail_pending_fix is attempt 1's outcome only); a gate FR 'pass' with FR2 False in all
    three gate-FR files (no decision gate FR writes). IX-12: on the recorded pass, E_b^A2(FA188) and the two XC-FR2 rows
    of result.FR2.Eb_A2_meV, the FR-quartet values without the item-4 label, carry L_FRSTOP on their printed lines
    (three times in the text), the A1 rows L_ITEM4 and never L_FRSTOP; L_FRSTOP is printed on no other STOP route and
    not on the done FR-pass route (C6's run, C4B-ENDED)."""
    b4 = "BLOCK 4. Tier block: not printed (final STOP in fr)"
    for name, part in (("C1v_fr1", "fail (FR-1, s2r_m30_Cs188o0_novac, end rule unconverged_early); then a final STOP "
                                   "(held STOP: s2r_m30_Cs188o0_novac ended unconverged_early (synthetic))"),
                       ("C1v_fr2", "fail (FR-2); then a final STOP (operator final STOP after gate FR (synthetic))"),
                       ("C1v_pass", "pass at gate FR; then a final STOP (operator final STOP after gate FR "
                                    "(synthetic)); counted as FR fails (S2B §1)"),
                       ("C1v_noerr", "fail (step-0 final; gate not evaluated); then a final STOP (operator final STOP "
                                     "after fr/STEP0_NO_ERROR (synthetic))"),
                       ("C1v_s0final", "fail (step-0 final; gate not evaluated); then a final STOP (operator final "
                                       "STOP after the step-0 repeat failed (synthetic))")):
        sr, nt = stop_repo(fx, name, SCEN[name])
        r = cached(fx, ("run", name, "note"), lambda: e_run(fx, sr, ["--run", "--stop-note", nt]))
        assert_fr_fail(r, sr, part, 0, block4=b4)
        assert LABELS["L_FRVALID"] not in r.result_text and not any("L_FRVALID" in x.labels for x in r.rows), name
        if name == "C1v_fr2":
            assert all("L_FR2" in row(r, rid).labels for rid in ("B2.EbA1", "B2.EbA2", "B2.delta"))
        a2rows = [row(r, "B2.EbA2")] + [x for x in r.rows if x.id == "XC-FR2" and x.text.startswith(
            "XC-FR2: Eb_A2_meV")] if name == "C1v_pass" else []
        if name == "C1v_pass":                         # IX-12: L_FRSTOP where no item-4 label stands
            assert len(a2rows) == 3 and all("L_FRSTOP" in x.labels and _labelled(r, x, "L_FRSTOP") and "L_ITEM4" not
                                            in x.labels for x in a2rows), [x.line for x in a2rows]
            assert r.result_text.count(LABELS["L_FRSTOP"]) == 3, r.result_text.count(LABELS["L_FRSTOP"])
            assert not any("L_FRSTOP" in x.labels for x in r.rows if x.has_a1 or x.kind == "Eb_A1")
        else:
            assert LABELS["L_FRSTOP"] not in r.result_text and not any("L_FRSTOP" in x.labels for x in r.rows), name
        if name == "C1v_s0final":                      # the step-0 final from the gate, not from STEP0_NO_ERROR
            assert row(r, "XC-FR2").text == "XC-FR2: gate FR not evaluated (step-0 final)"
            assert not rows_by(r, "B2.step0.no_error") and "decision fail_final" in \
                row(r, "B2.step0.s2_m30_Cs188o0_vac.gate").text
        if name == "C1v_noerr":
            assert row(r, "B2.step0.no_error").text.startswith(
                "fr_step0@4: final, no writer or input error found (fr/campaign.json fr_outcome at the STOP: fail "
                "(step-0 final; gate not evaluated), recorded by W 50 begin_stop")
            assert row(r, "XC-FR2").text == "XC-FR2: gate FR not evaluated (step-0 final)"
    s4, fr3 = eg.FR_S0_4, ("gates/FR.json", "gates_applied/gate_FR.gate.json", "gates_applied/gate_FR.json")
    for name, sc, post, why in (
            ("C1v_bad_dec", {"fr": {**SCEN["C1v_pass"]["fr"], "fr_outcome_stop": "fail (FR-1)"}}, None,
             "INT-ROUTE fr/campaign.json fr_outcome at the STOP against decision.FR"),
            ("C1v_bad_s0", {"fr": {**SCEN["C1t_gate"]["fr"], "fr_outcome_stop": eg.FR_OUTCOMES[3]}}, None,
             "INT-ROUTE fr/campaign.json fr_outcome at the STOP against decision.fr_step0"),
            ("C1v_bad_none", {"fr": {**SCEN["C1t_gate"]["fr"], "fr_outcome_stop": "pass"}}, None,
             "INT-ROUTE fr/campaign.json fr_outcome at the STOP without a decision"),
            ("C1v_bad_absent", SCEN["C1v_noerr"], _post_json("fr/campaign.json", lambda d: d.pop("fr_outcome")),
             "INT-ROUTE fr/campaign.json fr_outcome at the STOP"),
            # integration review 2 (probes P3, P5, P6 of its mutation lens)
            ("C1v_bad_s0final", {"fr": {**SCEN["C1v_s0final"]["fr"], "fr_outcome_stop": None}}, None,
             "INT-ROUTE fr/campaign.json fr_outcome at the STOP against decision.fr_step0"),
            ("C1v_bad_noerr2", SCEN["C1v_noerr"], _post_decision(
                ("gates/fr_step0.json", f"gates_applied/{s4}.gate.json", f"gates_applied/{s4}.json"), "fr_step0",
                {"attempts": 2}),
             "INT-ROUTE fr/campaign.json fr_outcome at the STOP against decision.fr_step0"),
            ("C1v_bad_frdec", SCEN["C1v_pass"], _post_decision(fr3, "FR", {"FR2": False}),
             "INT-ROUTE fr/gates/FR.json decision.FR at the STOP")):
        sr, nt = stop_repo(fx, name, sc, post=post)
        r = e_run(fx, sr, ["--run", "--stop-note", nt])
        assert r.rc == 3 and f"INTEGRITY FAILED: {why}" in r.result_text, (name, r.rc, r.result_text[-300:])
    sp = repo_of(fx, "pass")                           # IX-12: the done FR-pass route (C6's run) has no L_FRSTOP
    r = cached(fx, ("run", "C6"), lambda: e_run(fx, sp, ["--run"], block4=B4Double("C4B-ENDED", 3, sp.commits["F"])))
    assert r.rc == 0 and LABELS["L_FRSTOP"] not in r.result_text and not row(r, "B2.EbA2").labels, \
        (r.rc, row(r, "B2.EbA2").line)


def _post_decision(files, key, changes):
    """Integration review 2: decision.<key> changed alike in a gate file and its gates_applied copy (files[0:2], under
    fr/) and in the marker files[2], whose gate_file_sha256 follows the gate file (so INT-FR-SHA and INT-FR-DEC hold
    and only the route rules can refuse); a stopped fr has no fr/state_end.json to edit."""
    def post(root, man):
        fr = os.path.join(root, "fr")
        with open(os.path.join(fr, files[0])) as fh:
            g = json.load(fh)
        g["decision"][key].update(changes)
        sha = dump(os.path.join(fr, files[0]), g)
        dump(os.path.join(fr, files[1]), g)
        with open(os.path.join(fr, files[2])) as fh:
            mk = json.load(fh)
        mk["decision"], mk["gate_file_sha256"] = g["decision"], sha
        dump(os.path.join(fr, files[2]), mk)
    return post


@case("C1k", "C", mutants=(
        # RF-4's no-configuration branch removed from read_relaxation
        ("no_zero_branch", lambda fx: patched(er, "read_relaxation", _rr_no_zero)),))
def case_c1k(fx):
    """RF-4: Cs D's SCF fails at k = 0 (a complete record with n_config 0 and k_last None): FR-1 fails with kind
    end_rule; every item that needs F prints 'not formed (no configuration; end rule unconverged_early)'; no
    final-geometry check is attempted."""
    r, sr = run_of(fx, "C1k")
    assert_fr_fail(r, sr, "fail (FR-1, s2r_m30_Cs188o0_novac, end rule unconverged_early)", 0)
    nf = [x for x in r.rows if x.id.startswith("B2.s2r_m30_Cs188o0_novac.") and "not formed (no configuration; "
          "end rule unconverged_early)" in x.text]
    assert len(nf) == 6, [x.text for x in nf]
    assert not [m for m in r.au.members if "s2r_m30_Cs188o0_novac" in m[1]]
    q = row(r, "B2.quartet").text                         # fix round 1: not 'complete' among the incomplete cells
    assert "s2r_m30_Cs188o0_novac no configuration, s2r_m30_Cs188o0_vac not_run_gate" in q, q


@case("C1l", "C", mutants=(
        ("tail_formed_below_36", lambda fx: patched(ee().Run, "print_relax", _wrap_tail_k0(ee().Run.print_relax))),))
def case_c1l(fx):
    """RF-4, RF-14: host_R with k_last = 20 prints 'ΔF_tail ...: not formed (k_last < 36)'; FR stops at V+ check 5.
    Fix round 2 (M44): V+_R with k_last = 36, the boundary, forms ΔF_tail = F(0) − F(final) with L_TAIL."""
    r, sr = run_of(fx, "C1l")
    assert_fr_fail(r, sr, "fail (FR-1, s2r_m30_VA188, check 5)", 0)
    t = row(r, "B2.s2r_m30_hostA188.tail")
    assert t.text.endswith("not formed (k_last < 36)") and "L_TAIL" in t.labels
    t0 = row(r, "B2.s2r_m30_VA188.tail.0")
    F = sr.man["fr"]["rel"]["s2r_m30_VA188"]["F"]
    assert len(F) == 37 and "L_TAIL" in t0.labels and "F(0) − F(final)" in t0.text and \
        abs(t0.values["dF_meV"] - float((Fraction(F[0]) - Fraction(F[36])) * RY * 1000)) <= 1e-6, t0.text
    assert not [x for x in r.rows if x.id == "B2.s2r_m30_VA188.tail"]          # no 'not formed' row beside it


def _wrap_tail_k0(orig):
    def f(self, o, block, r, **kw):
        if kw.get("tails") == []:
            kw["tails"] = [0]
        return orig(self, o, block, r, **kw)
    return f


@case("C1m", "C", mutants=(
        ("gate_label_lost", lambda fx: patched(ee(), "STEP0_GATE", "recorded")),))
def case_c1m(fx):
    """Step-0 final at @4 (Cs D+V+ killed_by_gate): both evaluations are printed from their own gate copies: @2 with
    E's recompute and XC-FRSTEP0, @4 'cell killed by the step-0 gate'. Integration (IX-2): @4 made final by
    fr/STEP0_NO_ERROR (its gate files 'fail_pending_fix', fr/state_end.json 'fail_final'); a planted
    no_error_found False in fr/state_end.json gives INT-FR-DEC (exit 3)."""
    r, sr = run_of(fx, "C1m")
    assert_fr_fail(r, sr, "fail (step-0 final; gate not evaluated)", 0)
    assert row(r, "XC-FRSTEP0").text.endswith(": ok")
    assert row(r, "B2.step0.s2_m30_Cs188o0_vac").text.endswith("cell killed by the step-0 gate; output set aside, "
                                                               "not archived")
    assert r.result_text.count("recorded by gate code") == 2
    assert "decision fail_pending_fix" in row(r, "B2.step0.s2_m30_Cs188o0_vac.gate").text and \
        row(r, "B2.step0.no_error").text.startswith("fr_step0@4: final, no writer or input error found")
    sn = repo_of(fx, "C1m_noerr", SCEN["C1m"], post=_post_json("fr/state_end.json", lambda d: d["fr_step0"].update(
        no_error_found=False)))
    rn = e_run(fx, sn, ["--run"])
    assert rn.rc == 3 and "INTEGRITY FAILED: INT-FR-DEC fr/state_end.json fr_step0.outcome" in rn.result_text, \
        (rn.rc, rn.result_text[-300:])


def _reached_k0_old(c):
    """The rule before fix round 1: a complete cell always needs its step-0 evaluation (RF-4 ignored)."""
    st = c.get("status")
    if st in ("complete", "killed_by_gate"):
        return True
    if st is FILE_ABSENT or st in ("not_run_gate", "not_started_cap"):
        return False
    return None


@case("C1r", "C", mutants=(
        ("k0_marker_required", lambda fx: patched(ee(), "reached_k0", _reached_k0_old)),))
def case_c1r(fx):
    """RF-4 at a step-0 cell (fix round 1): V+_R(A188), then Cs D+V+, complete with n_config 0 (SCF failed at k = 0)
    never ran their step-0 gate (W 50:4107-4111, 2945-2951): no INT-STRUCT; FR-1 fails with kind end_rule; for V+,
    block 2.2 prints 'no fr step-0 evaluation ran'; for D+V+, @2 is printed and @4 is absent, and the FA188 values
    are 'not formed' with 'no configuration' for the complete cell."""
    r, sr = run_of(fx, "C1k_V")
    assert_fr_fail(r, sr, "fail (FR-1, s2r_m30_VA188, end rule unconverged_early)", 0)
    assert "no fr step-0 evaluation ran" in row(r, "B2.step0").text
    r2, sr2 = run_of(fx, "C1k_DV")
    assert_fr_fail(r2, sr2, "fail (FR-1, s2r_m30_Cs188o0_vac, end rule unconverged_early)", 0)
    assert rows_by(r2, "B2.step0.s2_m30_VA188") and not rows_by(r2, "B2.step0.s2_m30_Cs188o0_vac")
    q = row(r2, "B2.quartet").text
    assert q.startswith("not formed (quartet incomplete: s2r_m30_Cs188o0_vac no configuration)"), q


def _L_FR1_old(kind, cell, detail):
    if kind == "check":
        return f"FR quartet invalid (check {detail}, {cell}); reported only; not valid"
    if kind == "end_rule":
        return f"FR quartet invalid (end rule {detail}, {cell}); reported only; not valid"
    return f"FR quartet incomplete ({cell} {kind}); reported only; not valid"


def _fr1_cne_as_check(orig):
    def f(cells):
        ok, cell, kind = orig(cells)
        return ok, cell, "check" if kind == "check_not_evaluated" else kind
    return f


@case("C1s", "C", mutants=(
        # an absent validity_final taken as kind 'check' by E's recompute (L1)
        ("cne_as_check", lambda fx: patched(ee(), "fr1_recompute", _fr1_cne_as_check(ee().fr1_recompute))),
        # the not-run variant of L_FR1 on a complete quartet (the code before fix round 1)
        ("cne_label_not_run", lambda fx: patched(ee(), "L_FR1", _L_FR1_old)),))
def case_c1s(fx):
    """No final-geometry check on a complete, accepted FR cell (RF-4; fix round 1): at V+_R(A188) the header reads
    'fail (FR-1, s2r_m30_VA188, no final-geometry check)' and XC-FR1-DEC holds; at Cs D+V+ (the quartet complete)
    the three FA188 values carry 'FR quartet invalid (no final-geometry check, s2r_m30_Cs188o0_vac); reported only;
    not valid' (not the not-run variant); the invalid-cell table 3.6 lists the cell 'final-geometry check not
    evaluated'."""
    ok = {"status": "complete", "end_rule.outcome": "accepted_converged", "validity_final.valid": True}
    for v, kind in ((ABSENT, "check_not_evaluated"), (None, "check"), (False, "check")):   # as fr_eval [W 49:731-733]
        c = dict(ok, **{"validity_final.valid": v})
        assert ee().fr1_recompute({**{lab: ok for lab in eg.FR_ORDER}, "s2r_m30_VA188": c}) == \
            (False, "s2r_m30_VA188", kind), (v, kind)
    r, sr = run_of(fx, "C1s_V")
    assert_fr_fail(r, sr, "fail (FR-1, s2r_m30_VA188, no final-geometry check)", 0)
    assert row(r, "XC-FR1-DEC").text.endswith(": ok")
    assert "final-geometry check not evaluated" in row(r, "B3.inv.fr.s2r_m30_VA188").text
    r2, sr2 = run_of(fx, "C1s_DV")
    assert_fr_fail(r2, sr2, "fail (FR-1, s2r_m30_Cs188o0_vac, no final-geometry check)", 0)
    lab = "FR quartet invalid (no final-geometry check, s2r_m30_Cs188o0_vac); reported only; not valid"
    assert r2.result_text.count(lab) == 3 and all("L_FR1" in row(r2, i).labels for i in ("B2.EbA1", "B2.EbA2",
                                                                                         "B2.delta"))
    assert "final-geometry check not evaluated" in row(r2, "B3.inv.fr.s2r_m30_Cs188o0_vac").text


@case("C1t", "C")
def case_c1t(fx):
    """The STOP header's branches (S2B:619-621; fix round 1): a final STOP with Cs D pending (D+V+ not started) reads
    'stopped at s2r_m30_Cs188o0_novac (...)' (the pending record, not the first absent one); a final STOP after all
    four FR cells completed, before gate FR, reads 'stopped at gate FR (...)'. Fix round 2: there the three FA188
    values carry L_FRNOTEVAL (gate FR not evaluated); a final STOP after a step-0 failure pending its fix
    (fail_pending_fix; the cell killed_by_gate, the later cells not_run_gate) names that cell, at @2 and at @4 (before:
    'gate FR' at @4, the not-run stubs being skipped)."""
    blk = "BLOCK 4. Tier block: not printed (final STOP in fr)"
    sr, nt = stop_repo(fx, "C1t_pending")
    r = e_run(fx, sr, ["--run", "--stop-note", nt])
    assert_fr_fail(r, sr, "stopped at s2r_m30_Cs188o0_novac (operator final STOP (synthetic))", 0, block4=blk)
    sr2, nt2 = stop_repo(fx, "C1t_gate")
    r2 = e_run(fx, sr2, ["--run", "--stop-note", nt2])
    assert_fr_fail(r2, sr2, "stopped at gate FR (operator final STOP (synthetic))", 0, block4=blk)
    assert "XC-FR2: gate FR not evaluated (fr stopped)" in r2.result_text and row(r2, "B2.delta")
    for rid in ("B2.EbA1", "B2.EbA2", "B2.delta"):          # fix round 2 (L_FRNOTEVAL; the wording needs a ruling)
        x = row(r2, rid)
        assert "L_FRNOTEVAL" in x.labels and _labelled(r2, x, "L_FRNOTEVAL"), (rid, x.line)
    assert r2.result_text.count(LABELS["L_FRNOTEVAL"]) == 3
    for name, cell, at in (("C1u_2", "s2r_m30_VA188", "VA188"), ("C1u_4", "s2r_m30_Cs188o0_vac", "Cs188o0_vac")):
        su, nu = stop_repo(fx, name)
        ru = e_run(fx, su, ["--run", "--stop-note", nu])
        assert_fr_fail(ru, su, f"stopped at {cell} (operator final STOP after the step-0 failure at {at} "
                               f"(synthetic))", 0, block4=blk)
        sp = "s2_m30_VA188" if at == "VA188" else "s2_m30_Cs188o0_vac"
        assert "decision fail_pending_fix" in row(ru, f"B2.step0.{sp}.gate").text
        assert row(ru, f"B2.step0.{sp}").text.endswith("cell killed by the step-0 gate; output set aside, not archived")


def _drop_rows(orig, suffix):
    def f(self, block, rid, kind, text, **kw):
        if rid.endswith(suffix):
            return None
        return orig(self, block, rid, kind, text, **kw)
    return f


def assert_set_aside_unread(r):
    """No file under step0_attempt1/ or discarded/ was opened, and the attempt-1 canary is not printed (S2B:272-273)."""
    assert not any(("step0_attempt1" in e["rel"] or "discarded" in e["rel"]) for e in r.au.log.values())
    assert ("%.2f" % ATTEMPT1_CANARY) not in r.result_text and "6666.6" not in r.result_text


@case("C1o", "C", mutants=(
        ("decision_leaves_unprinted", lambda fx: patched(ee().Out, "row", _drop_rows(ee().Out.row, ".decision"))),))
def case_c1o(fx):
    """A step-0 repeat that passes (S2B:271-274; fix round 1): V+_R(A188) failed @2 at attempt 1 (its files set aside
    under fr/step0_attempt1/), fr/STEP0_FIX (a second fr campaign commit), the repeat passes; @4 runs as attempt 2;
    FR-1 fails at the D+V+ check 5. The header; INT-FR-DEC on the attempt-2 decisions; block 2.2's decision leaves
    (attempts 2, repeat True, the fix note, attempt 1 fail_pending_fix at VA188) and the repeat line; E's files at
    both fr campaign commits (RF-3); nothing set aside is opened or printed."""
    r, sr = run_of(fx, "C1o")
    assert_fr_fail(r, sr, "fail (FR-1, s2r_m30_Cs188o0_vac, check 5)", 0)
    for sp in ("s2_m30_VA188", "s2_m30_Cs188o0_vac"):
        t = row(r, f"B2.step0.{sp}.decision").text
        assert "attempts 2, repeat True, fix_note " + FIX_NOTE in t and \
            "attempts 1, outcome fail_pending_fix, cell s2r_m30_VA188" in t, t
    assert all(x.text.endswith(": ok") for x in rows_by(r, "XC-FRSTEP0")) and len(rows_by(r, "XC-FRSTEP0")) == 2
    assert "step-0 repeat: fr/STEP0_FIX recorded" in row(r, "B2.step0.repeat").text
    assert "E's files at every fr campaign commit (2): ok (RF-3)" in r.result_text
    assert_set_aside_unread(r)


@case("C1p", "C")
def case_c1p(fx):
    """The repeat of @4 fails finally (fix round 1): Cs D+V+ killed_by_gate at attempt 2; header 'fail (step-0
    final; gate not evaluated)'; @2 printed as attempt 1 (repeat False, no attempt-1 leaves), @4 as attempt 2
    (fail_final; attempt 1 fail_pending_fix at Cs188o0_vac) with the killed-cell label; no FR.json; nothing set aside
    is opened or printed."""
    r, sr = run_of(fx, "C1p")
    assert_fr_fail(r, sr, "fail (step-0 final; gate not evaluated)", 0)
    t2 = row(r, "B2.step0.s2_m30_VA188.decision").text      # fix round 2: no attempt-1 clause without a repeat
    assert "attempts 1, repeat False" in t2 and t2.endswith("; no repeat (no attempt-1 leaves)") and \
        "set aside" not in t2, t2
    t4 = row(r, "B2.step0.s2_m30_Cs188o0_vac.decision").text
    assert "attempts 2, repeat True" in t4 and "outcome fail_pending_fix, cell s2r_m30_Cs188o0_vac" in t4, t4
    assert "decision fail_final" in row(r, "B2.step0.s2_m30_Cs188o0_vac.gate").text
    assert row(r, "B2.step0.s2_m30_Cs188o0_vac").text.endswith("cell killed by the step-0 gate; output set aside, "
                                                               "not archived")
    assert not any(e["rel"].startswith("fr/gates/FR") for e in r.au.log.values())
    assert_set_aside_unread(r)


def _rf12_no_aside(orig):
    def f(self):
        named = self.fr["aside_named"]
        self.fr["aside_named"] = {"@2": False, "@4": False}
        try:
            return orig(self)
        finally:
            self.fr["aside_named"] = named
    return f


def _post_aside4(root, man):
    """The @4 attempt-1 trio named under fr/step0_attempt1/gates_applied/, as after a repeat's move (fix round 2)."""
    _set_aside_attempt1(root, "gate:fr_step0@4", "s2_m30_Cs188o0_vac", "s2r_m30_Cs188o0_vac", {})


def _posts(*fns):
    def post(root, man):
        for f in fns:
            f(root, man)
    return post


@case("C1q", "C", mutants=(
        # R-1 not modelled: a missing gates/fr_step0.json is INT-STRUCT on every route (the set-aside names unseen)
        ("no_set_aside", lambda fx: patched(ee().Run, "rf12_step0", _rf12_no_aside(ee().Run.rf12_step0))),
        # integration review 3 (IX-11 at @2): block 2 lists the set-aside @4 files only
        ("aside_at4_only", lambda fx: src_patched(
            ee().Run, "block2", 'for at in ("@2", "@4") if fr["aside_named"][at]]',
            'for at in ("@4",) if fr["aside_named"][at]]')),
        # the @2 attempt-1 marker never seen by name
        ("aside_named_at4_only", lambda fx: src_patched(
            ee().Run, "route_fr", 'f"{stem}.json" in names for', 'f"{stem}.json" in names and at == "@4" for')),
        # B2.step0 'never reached k = 0' after a move that was not recorded
        ("in_force_repeat_only", lambda fx: src_patched(
            ee().Run, "block2", '"its repeat)" if fr.get("repeat") or aside else', '"its repeat)" if fr.get("repeat") '
            'else'))))
def case_c1q(fx):
    """R-1 (fix round 1): a final STOP while the repeat of @4 is prepared (fr/STEP0_FIX recorded; gates/fr_step0.json,
    the @4 trio and the D+V+ record set aside, W 50:2725-2760): exit 0; header 'stopped at s2r_m30_Cs188o0_vac
    (...)'; @2 printed from its own copy (INT-FR-DEC against its marker); the set-aside line for @4; nothing set aside
    is opened. The same files with no set-aside @4 trio (a missing file, no repeat) give INT-STRUCT (exit 3).
    Fix round 2, one conjunct of the set-aside rule at a time (each planted with every other conjunct true):
    (i) the same archive on a done route; (ii) D+V+ pending after @4 ran; (iii) D+V+ not_run_gate: each INT-STRUCT;
    (iv) a STOP after a passing @2 repeat with D+V+ pending and gates/fr_step0.json present: exit 0, INT-FR-SHA ok (1)
    and no set-aside row; (v) a STOP during the @2 repeat: 'no fr step-0 evaluation in force ...'; (vi) the move made
    but not recorded (no STEP0_FIX entry; W 50 fr_step0_repeat moves first): exit 0, the set-aside rows. Integration
    review 3 (IX-11 at @2): (vii) the @2 move made but not recorded: exit 0; B2.step0.repeat names the set-aside
    fr_step0@2 files and B2.step0 says no step-0 evaluation is in force, never that V+_R did not reach k = 0."""
    sr, nt = stop_repo(fx, "C1q")
    r = cached(fx, ("run", "C1q", "note"), lambda: e_run(fx, sr, ["--run", "--stop-note", nt]))
    blk = "BLOCK 4. Tier block: not printed (final STOP in fr)"
    assert_fr_fail(r, sr, "stopped at s2r_m30_Cs188o0_vac (operator final STOP during the step-0 repeat "
                   "(synthetic))", 0, block4=blk)
    assert "set aside for its repeat" in row(r, "B2.step0.s2_m30_Cs188o0_vac").text
    assert row(r, "B2.step0.s2_m30_VA188.gate") and row(r, "XC-FRSTEP0").text.endswith(": ok")
    assert "step-0 repeat: fr/STEP0_FIX recorded" in row(r, "B2.step0.repeat").text
    assert_set_aside_unread(r)
    rs = "INTEGRITY FAILED: INT-STRUCT fr/gates/fr_step0.json required file absent (RF-12)"
    sn, nn = stop_repo(fx, "C1q_norepeat", post=_post_rm("fr/gates/fr_step0.json"))
    rn = e_run(fx, sn, ["--run", "--stop-note", nn])
    assert rn.rc == 3 and rs in rn.result_text, rn.result_text[-300:]
    # (i) done (M01); (ii) @4 ran (M02); (iii) D+V+ not_run_gate (M03)
    rm = _post_rm("fr/gates/fr_step0.json")
    s1 = repo_of(fx, "C1q_done", SCEN["C1q"], post=_post_json(
        "fr/campaign.json", lambda d: d.update(status="done", fr_outcome="fail (FR-1)")))
    for name, srx, argv in (("done", s1, ["--run"]),
                            ("dvpend",) + _stop_argv(fx, "C1q_dvpend", _posts(rm, _post_aside4)),
                            ("dvnotrun",) + _stop_argv(fx, "C1q_dvnotrun", _posts(rm, _post_aside4))):
        rx = e_run(fx, srx, argv)
        assert rx.rc == 3 and rs in rx.result_text, (name, rx.result_text[-300:])
    # (iv) gates/fr_step0.json present (M04)
    s4, a4 = _stop_argv(fx, "C1q_pend", _post_aside4)
    r4 = e_run(fx, s4, a4)
    assert_fr_fail(r4, s4, "stopped at s2r_m30_Cs188o0_vac (operator final STOP (synthetic))", 0, block4=blk)
    assert "\n  INT-FR-SHA ok (1)\n" in r4.result_text and not rows_by(r4, "B2.step0.s2_m30_Cs188o0_vac")
    # (v) a STOP during the @2 repeat (M51)
    s5, a5 = _stop_argv(fx, "C1q_vstop")
    r5 = e_run(fx, s5, a5)
    assert_fr_fail(r5, s5, "stopped at s2r_m30_VA188 (operator final STOP during the step-0 repeat at VA188 "
                           "(synthetic))", 0, block4=blk)
    assert row(r5, "B2.step0").text.startswith("no fr step-0 evaluation in force (the attempt-1 evaluation is set "
                                               "aside for its repeat)")
    assert_set_aside_unread(r5)
    # (vi) moved, not recorded (finding R-1 of review round 2)
    s6, a6 = _stop_argv(fx, "C1q_unrec")
    r6 = e_run(fx, s6, a6)
    assert_fr_fail(r6, s6, "stopped at s2r_m30_Cs188o0_vac (operator final STOP during the step-0 repeat "
                           "(synthetic))", 0, block4=blk)
    assert "set aside for its repeat" in row(r6, "B2.step0.s2_m30_Cs188o0_vac").text
    assert row(r6, "B2.step0.repeat").text.startswith("step-0 repeat prepared, not recorded: the attempt-1 files of "
                                                      "fr_step0@4 are set aside unread")
    assert "E's files at every fr campaign commit (1): ok (RF-3)" in r6.result_text
    assert_set_aside_unread(r6)
    # (vii) the @2 move made, not recorded (integration review 3, IX-11 at @2)
    s7, a7 = _stop_argv(fx, "C1q_vunrec")
    r7 = e_run(fx, s7, a7)
    assert_fr_fail(r7, s7, "stopped at s2r_m30_VA188 (operator final STOP during the step-0 repeat at VA188 "
                           "(synthetic))", 0, block4=blk)
    t7 = row(r7, "B2.step0.repeat").text
    assert t7.startswith("step-0 repeat prepared, not recorded: the attempt-1 files of fr_step0@2 are set aside "
                         "unread"), t7
    assert row(r7, "B2.step0").text.startswith("no fr step-0 evaluation in force (the attempt-1 evaluation is set "
                                               "aside for its repeat)"), row(r7, "B2.step0").text
    assert not rows_by(r7, "B2.step0.s2_m30_VA188.gate") and \
        "E's files at every fr campaign commit (1): ok (RF-3)" in r7.result_text
    assert_set_aside_unread(r7)


def _stop_argv(fx, name, post=None):
    """(repository, argv) of a final-STOP scenario run with its stop note."""
    s, n = stop_repo(fx, name, post=post)
    return s, ["--run", "--stop-note", n]


# ---------------------------------------------------------------- C2: independent recomputation (RF-18)
def _ind_eV(s):
    return Fraction(s) * RY


def _ind_pos(q47, rows):
    alat = Fraction(float(f"{ALAT_BOHR:.6f}") * q47.QE_UNITS["Bohr"])
    return [[Fraction(v) * alat if kind == "alat" else Fraction(v) for v in s] for kind, s in rows]


def _ind_relax(q47, rr, tails, centres):
    """Independent per-relaxation values from the planted strings: F, relaxation energy, tails, path work."""
    F, pr = rr["F"], rr["printed"]
    kl = len(F) - 1
    F0, Ff = _ind_eV(F[0]), _ind_eV(F[kl])
    out = {"F0": F0, "Ffin": Ff, "relax": (Ff - F0) * 1000, "tail": {k: (_ind_eV(F[k]) - Ff) * 1000 for k in tails}}
    X = {k: _ind_pos(q47, pr["pos"][k]) for k in range(kl + 1)}
    conv = RY / BOHR
    Fo = {k: [[Fraction(v) * conv for v in row_] for row_ in pr["frc"][k]] for k in range(kl + 1)}
    nat = len(X[0])
    W = [Fraction(0)] * nat
    for k in range(kl):
        for i in range(nat):
            W[i] -= sum((Fo[k][i][c] + Fo[k + 1][i][c]) * (X[k + 1][i][c] - X[k][i][c]) for c in range(3)) / 2
    dr2 = [sum((X[kl][i][c] - X[0][i][c]) ** 2 for c in range(3)) for i in range(nat)]
    A = float(ALAT_BOHR * q47.QE_UNITS["Bohr"])
    d = []
    for i in range(nat):
        best = math.inf
        for cen in centres:
            for n0 in range(-2, 3):
                for n1 in range(-2, 3):
                    for n2 in range(-2, 3):
                        v = [float(X[0][i][c]) - (cen[c] + (n0, n1, n2)[c] * A) for c in range(3)]
                        best = min(best, math.sqrt(math.fsum(x * x for x in v)))
        d.append(best)
    sh = {}
    for lo, hi in ((0.0, 4.0), (4.0, 6.0), (6.0, 8.0), (8.0, 1e9)):
        idx = [i for i in range(nat) if lo <= d[i] < hi]
        sh[f"{lo:g}-{hi:g}"] = (sum((W[i] for i in idx), Fraction(0)) * 1000, sum((dr2[i] for i in idx), Fraction(0)))
    tot = sum(W, Fraction(0))
    out.update(pw_total=tot * 1000, pw_closure=(tot - (Ff - F0)) * 1000, dr2=sum(dr2, Fraction(0)), shells=sh)
    return out


def _ind_eb(F):
    return ((F["DV"] - F["D"]) - (F["V"] - F["host"])) * 1000


def _ind_leg(Es):
    """The per-leg Boltzmann aggregate with explicit loops and math.fsum (k_BT = 25.7 meV), in eV."""
    m = min(Es)
    s = math.fsum(math.exp(-((x - m) * 1000.0) / 25.7) for x in Es)
    return m - 25.7 * math.log(s) / 1000.0


def _fmt_ok(ind, text, f="%.2f"):
    """The printed string equals the formatted independent value (either rounding within 1e-6 of a boundary)."""
    x = float(ind)
    return any((f % y) in text for y in (x, x - 1e-6, x + 1e-6))


def independent_checks(fx, r, sr):
    """Spec 18 C2: every printed number of blocks 1-3 against the independent values (1e-6 meV, 1e-6 eV)."""
    q47, man, n = fx.ex.q47, sr.man, 0

    def near(a, b, tol=1e-6):
        assert a is not None and abs(float(a) - float(b)) <= tol, (a, float(b))
    cen = {}
    for (L_, j) in (("B", 76), ("A", 188)):
        with open(os.path.join(sr.root, "c1", "regions", f"m30_{L_}{j}.json")) as fh:
            c = json.load(fh)["centres"]
        cen[(L_, j)] = [c["v"], c["site"]]
    groups = [(1, "c2", man["c2"], eg.FAR, ("B", 76)), (2, "fr", man["fr"]["rel"], eg.FR_ORDER, ("A", 188))]
    quartets = {}
    for blk, c, rels, labs, site in groups:
        F0s, Ffs = {}, {}
        for lab in labs:
            if lab not in rels:
                continue
            rr = rels[lab]
            kl = len(rr["F"]) - 1
            tails = [ee().TAIL_K[lab]] + (list(ee().VB76_EXTRA_K) if lab == "s2r_m30_VB76" else []) if blk == 1 else \
                ([kl - 36] if kl >= 36 else [])
            ind = _ind_relax(q47, rr, tails, cen[site])
            pre = f"B{blk}.{lab}"
            for rid, key, val, f in ((".F0", "F0_eV", ind["F0"], "%.6f"), (".Ffin", "Ffin_eV", ind["Ffin"], "%.6f"),
                                     (".relax", "relax_meV", ind["relax"], "%.2f")):
                x = row(r, pre + rid)
                near(x.values[key], val)
                assert _fmt_ok(val, x.text, f), (pre + rid, x.text)
                n += 1
            for kt, v in ind["tail"].items():
                x = row(r, f"{pre}.tail.{kt}")
                near(x.values["dF_meV"], v)
                assert _fmt_ok(v, x.text)
                n += 1
            x = row(r, pre + ".pw")
            near(x.values["total_meV"], ind["pw_total"]); near(x.values["closure_meV"], ind["pw_closure"])
            near(x.values["sum_dr2_A2"], ind["dr2"], 1e-9)
            assert _fmt_ok(ind["pw_total"], x.text) and _fmt_ok(ind["dr2"], x.text, "%.6f")
            for sh, (w, d2) in ind["shells"].items():
                y = row(r, f"{pre}.pw.{sh}")
                near(y.values["W_meV"], w); near(y.values["dr2_A2"], d2, 1e-9)
                assert _fmt_ok(w, y.text)
                n += 2
            F0s[role_of_lab(lab)], Ffs[role_of_lab(lab)] = ind["F0"], ind["Ffin"]
        if len(F0s) == 4:
            a1, a2 = _ind_eb(F0s), _ind_eb(Ffs)
            quartets[blk] = (a1, a2, a2 - a1)
            for rid, key, v in (("EbA1", "Eb_A1_meV", a1), ("EbA2", "Eb_A2_meV", a2), ("delta", "delta_meV", a2 - a1)):
                x = row(r, f"B{blk}.{rid}")
                near(x.values[key], v)
                assert _fmt_ok(v, x.text), x.text
                n += 1
    # block 3: MACE E_b, DFT A1, q = 0, determinism
    E = {w: dict(lv)["relax.E_mace_eV"] for w, lv in man["c1_mace"].items()}

    def wid(lab):
        m = re.fullmatch(r"s2_(m\d\d)_([A-Za-z]+?)(\d+)o(\d+)_(novac|vac)", lab)
        if not m:
            return lab
        h, t, j, o, leg = m.groups()
        mp = man["distinct"].get((t, int(j), leg)) if h == "m30" else None
        p = mp[f"o{o}"] if mp else f"p{o}"
        return f"s2_{h}_{t}{j}{p}_{leg}"

    def mace_eb(labs):
        leg = {k: (Fraction(repr(E[wid(labs[k][0])])) if len(labs[k]) == 1 else
                   Fraction(repr(_ind_leg([E[wid(x)] for x in labs[k]])))) for k in ("D", "DV")}
        return _ind_eb({"DV": leg["DV"], "D": leg["D"], "V": Fraction(repr(E[labs["V"]])),
                        "host": Fraction(repr(E[labs["host"]]))})
    for p in eg.PILOTS:
        for L_ in "BAX":
            for f in eg.FAR4[p][L_]:
                for d in eg.TOKENS_OF[L_]:
                    labs = {"host": f"s2_{p}_host", "V": f"s2_{p}_V{L_}{f}", "D": [f"s2_{p}_{d}{f}o0_novac"],
                            "DV": [f"s2_{p}_{d}{f}o0_vac"]}
                    x = row(r, f"B3.noise.{p}.{d}{f}")
                    em = mace_eb(labs)
                    a1 = _ind_eb({k: _ind_eV(sp_F(v if isinstance(v, str) else v[0])) for k, v in labs.items()})
                    near(x.values["Eb_mace_meV"], em); near(x.values["Eb_A1_meV"], a1)
                    assert _fmt_ok(em, x.text) and _fmt_ok(a1, x.text)
                    n += 2
    for p, sites in (("m30", (("A", 128), ("X", 138))), ("m05", (("B", 124), ("A", 28), ("X", 49)))):
        for L_, j in sites:
            for d in eg.TOKENS_OF[L_]:
                labs = {"host": f"s2_{p}_host", "V": f"s2_{p}_V{L_}{j}", "D": [f"s2_{p}_{d}{j}o0_novac"],
                        "DV": [f"s2_{p}_{d}{j}o0_vac"]}
                x = row(r, f"B3.start.{p}.{d}{j}")
                near(x.values["Eb_mace_meV"], mace_eb(labs))
                n += 1
    for (t, j) in POSE_STARTS:
        L_ = eg.SUBLATTICE[t]
        kept = {leg: [f"s2_m30_{t}{j}{o}_{leg}" for o in sorted(man["distinct"][(t, j, leg)])] for leg in eg.LEGS}
        base = {"host": "s2_m30_host", "V": f"s2_m30_V{L_}{j}"}
        x = row(r, f"B3.pose.{t}{j}")
        near(x.values["Eb_mace_default_meV"], mace_eb({**base, "D": [f"s2_m30_{t}{j}o0_novac"],
                                                       "DV": [f"s2_m30_{t}{j}o0_vac"]}))
        near(x.values["Eb_mace_aggregate_meV"], mace_eb({**base, "D": kept["novac"], "DV": kept["vac"]}))
        assert _fmt_ok(x.values["Eb_mace_aggregate_meV"], x.text)
        n += 2
    for key, (L_, j, d) in (("Sr76", ("B", 76, "Sr")), ("Cl138", ("X", 138, "Cl")), ("Cs128", ("A", 128, "Cs"))):
        v = _ind_eb({"DV": _ind_eV(sp_F(f"s2_m30_{d}{j}o0_vac_q0")), "D": _ind_eV(sp_F(f"s2_m30_{d}{j}o0_novac")),
                     "V": _ind_eV(sp_F(f"s2_m30_V{L_}{j}_q0")), "host": _ind_eV(sp_F("s2_m30_host"))})
        x = row(r, f"B3.q0.{key}")
        near(x.values["Eb_q0_meV"], v)
        assert _fmt_ok(v, x.text)
        n += 1
        if key == "Sr76":                                # fix round 1: the q = +1 comparator and the difference
            v1 = _ind_eb({"DV": _ind_eV(sp_F(f"s2_m30_{d}{j}o0_vac")), "D": _ind_eV(sp_F(f"s2_m30_{d}{j}o0_novac")),
                          "V": _ind_eV(sp_F(f"s2_m30_V{L_}{j}")), "host": _ind_eV(sp_F("s2_m30_host"))})
            x1, x01 = row(r, f"B3.q1.{key}"), row(r, f"B3.q01.{key}")
            near(x1.values["Eb_q1_meV"], v1); near(x01.values["diff_meV"], v1 - v)
            assert _fmt_ok(v1, x1.text) and _fmt_ok(v1 - v, x01.text)
            n += 2
    # block 1.3 (OP-30): the two full-precision differences, recorded in the row and printed at repr
    a1 = quartets[1][0]
    with open(os.path.join(sr.root, "c1", "gates", "N.json")) as fh:
        gnv = json.load(fh)["result"]["dopants"]["Sr"]["hosts"]["m30"]["per_site_meV"]["76"]
    x, y = row(r, "B1.EbA1"), row(r, "B1.EbA1.gateN")
    near(x.values["diff_minus5_meV"], a1 + 5)
    near(y.values["gateN_meV"], Fraction(repr(gnv)), 0.0)
    near(y.values["diff_gateN_meV"], a1 - Fraction(repr(gnv)))
    assert f"E_b^A1 − (−5.0) = {x.values['diff_minus5_meV']!r} meV" in x.text
    assert f"E_b^A1 − gate N = {y.values['diff_gateN_meV']!r} meV" in y.text and f"= {gnv!r} meV;" in y.text
    n += 3
    # block 3.5: the residual-force summaries of every A1 cell from the planted force rows (eV/A = Ry/bohr x RY/BOHR)
    fx_re = re.compile(r"all rms (\S+) max (\S+) n (\d+); free rms (\S+) max (\S+) n (\d+)$")
    for lab in sorted(eg.BLOCK3_SP):
        nrm = [math.sqrt(math.fsum(float(Fraction(v) * RY / BOHR) ** 2 for v in row_)) for row_ in man["sp_forces"][lab]]
        free = sorted(man["sp_free"][lab])
        want = (math.sqrt(math.fsum(v * v for v in nrm) / len(nrm)), max(nrm), len(nrm),
                math.sqrt(math.fsum(nrm[i] ** 2 for i in free) / len(free)), max(nrm[i] for i in free), len(free))
        m = fx_re.search(row(r, f"B3.forces.{lab}").text)
        got = (float(m.group(1)), float(m.group(2)), int(m.group(3)), float(m.group(4)), float(m.group(5)),
               int(m.group(6)))
        assert all(abs(a - b) <= 5.1e-7 for a, b in zip(got, want)), (lab, got, want)
        n += 1
    for p in eg.PILOTS:
        x = row(r, f"B3.det.{p}")
        dE = (Fraction(repr(E[f"s2_{p}_host"])) - Fraction(repr(-999.5 - (p == "m05")))) * 1000
        near(x.values["dE_meV"], dE)
        near(x.values["max_dr_A"], math.sqrt(3) * 0.01, 1e-6)
        n += 2
    return n, quartets


def role_of_lab(lab):
    return er.a2_cell(lab)["kind"]


_SWAP = {"Sr": "Ca", "Ca": "Sr", "Cs": "GA", "GA": "Cs"}


def _quartet_dopant_swap(orig):
    """quartet_a1 with Sr <-> Ca and Cs <-> GA in its D and D+V labels (the labels only the MACE rows use)."""
    def f(table, h, d, j):
        q = orig(table, h, d, j)
        sw = lambda lab: re.sub(r"_(Sr|Ca|Cs|GA)(\d)", lambda m: f"_{_SWAP[m.group(1)]}{m.group(2)}", lab)
        q["labels"] = dict(q["labels"], D=[sw(x) for x in q["labels"]["D"]], DV=[sw(x) for x in q["labels"]["DV"]])
        return q
    return f


@case("C2", "C", mutants=(
        # E_b formed with D and V exchanged (RF-18: every role distinct, so every E_b changes)
        ("eb_roles_swapped", lambda fx: patched(ee(), "eb", lambda F: None if any(F.get(k) is None for k in
                                                ("host", "V", "D", "DV")) else
                                                ((F["D"] - F["DV"]) - (F["V"] - F["host"])) * 1000.0)),
        # meV printed at another precision
        ("precision", lambda fx: patched(ee(), "fm", lambda x: "%.3f" % x)),
        # the pose aggregate without the Boltzmann sum (the minimum only)
        ("no_boltzmann", lambda fx: patched(fx.ex.g49, "leg_free_energy", lambda F: min(float(v) for v in F))),
        # fix round 2 (RF-18): a dopant mix-up in the MACE quartets (Sr <-> Ca, Cs <-> GA in the D and D+V labels),
        # visible only because every planted MACE E_b now depends on all four records
        ("mace_dopant_swap", lambda fx: patched(fx.ex.m48, "quartet_a1", _quartet_dopant_swap(fx.ex.m48.quartet_a1)))))
def case_c2(fx):
    """Independent recomputation (C1f and C1i): every printed number of blocks 1-3 (F(0), F(final), relaxation
    energies, Delta F_tail, E_b^A1, E_b^A2, delta, path-work totals and shells with lattice-image centres, the
    zero-shot MACE E_b including the Boltzmann aggregate of the planted two-minimum pose leg, the q = 0 E_b and the
    determinism values) equals the value of an independent code that starts from the planted strings with
    fractions.Fraction, explicit loops and math.fsum, to 1e-6 meV (1e-6 eV for F), and each printed string equals
    the formatted independent value. Fix round 1: also the q = +1 row and the q = +1 - q = 0 difference at Sr76, the
    two full-precision differences of E_b^A1(Pb76) (to -5.0 and to gate N's unrounded value; OP-30) and every
    residual-force summary of block 3.5."""
    for name in ("C1f", "C1i"):
        r, sr = run_of(fx, name)
        assert r.rc == 0, r.result_text[-800:]
        n, q = independent_checks(fx, r, sr)
        assert n > 200 and 1 in q, n
        if name == "C1i":
            assert 2 in q and abs(float(q[2][2]) - 50.001) < 2e-4


# ---------------------------------------------------------------- C3-C11
def _c3_post(root, man):
    rec = os.path.join(root, "c1", "records", "s2_m30_Sr136p1_novac.json")
    with open(os.path.join(root, "c1", "records", "s2_m30_Sr136p0_novac.json")) as fh:
        d = json.load(fh)
    d["work_id"], d["start"] = "s2_m30_Sr136p1_novac", "p1"
    dump(rec, d)


@case("C3", "C", mutants=(
        # a Pb136 record counted as a pose start (the census then accepts the planted 161st record)
        ("census_open", lambda fx: multi(patched(eg, "classify_wid", _wrap_classify(eg.classify_wid)),
                                         patched(eg, "CLASS_COUNTS", {**eg.CLASS_COUNTS, "pose_start": 29}))),
        # the expected MACE leaf count changed (XC-MACE-COUNT must fail)
        ("leaf_count", lambda fx: patched(eg, "MACE_LEAVES_BLOCK3", 160))))
def case_c3(fx):
    """Counts (S2B:595-597): block 3 lists 155 records and 161 E_mace_eV leaves, each planted non-Pb136 canary
    printed with L_MACE (the MACE canary, S0:965), and block 3 defers the 5 Pb136 work ids: 160 in all, disjoint;
    without block 5 no Pb136 MACE canary and no Pb136 single-point F is in the text; a planted 161st record
    s2_m30_Sr136p1_novac gives INT-C1-CENSUS (exit 3)."""
    r, sr = run_of(fx, "C1f")
    assert r.rc == 0
    recs = [x for x in r.rows if x.id.startswith("B3.rec.")]
    leaves = [x for x in r.rows if x.id.startswith("B3.mace.")]
    assert len(recs) == 155 and len(leaves) == 161 and all("L_MACE" in x.labels for x in leaves)
    wids = {x.id[len("B3.rec."):] for x in recs}
    deferred = row(r, "B3.deferred").text.split(": ", 1)[1].split(", ")
    assert len(deferred) == 5 and set(deferred) == set(eg.PB136_WIDS) and not wids & set(deferred)
    assert wids | set(deferred) == set(census_wids())
    for w, lv in sr.man["c1_mace"].items():
        for p, v in lv:
            if w in eg.PB136_WIDS:
                assert ("%.6f" % v) not in r.result_text
            else:
                assert f"{p} E_mace_eV = {'%.6f' % v} eV  -- {ee().L['L_MACE']}" in r.result_text, (w, p)
    srp = repo_of(fx, "C3_planted", {"fr": SCEN["C1f"]["fr"]}, post=_c3_post)
    rp = e_run(fx, srp, ["--run"])
    assert rp.rc == 3 and "INTEGRITY FAILED: INT-C1-CENSUS" in rp.result_text, rp.result_text[-500:]


def _wrap_classify(orig):
    def f(wid):
        return "pose_start" if wid == "s2_m30_Sr136p1_novac" else orig(wid)
    return f
EXPECTED_COVERAGE = ("P10 q = 0 Sr76", "P10 q = 0 Cl138", "P10 q = 0 Cs128", "P10 q = 0 GA128", "P10 q = 0 Sr136",
                     "P10 q = 0 Ca136", "P15 per-site e_h(j), E_d(j), G_d, raw E_b, far-site values",
                     "P15 shared-region sensitivity", "P15 invalid cells (C1, C2, FR)", "P15 invalid cells (C3b, C4b)",
                     "P15 plateau-excluded intervals", "P15 zero-shot MACE E_b, pilot cells",
                     "P15 zero-shot MACE E_b, production quartets", "P15 zero-shot MACE E_b, Pb136",
                     "P15 DFT residual forces, A1 cells outside Pb136", "P15 DFT residual forces, Pb136",
                     "P15 DFT residual forces, C3b", "P15 per A2 cell, C2 relaxations 5-8", "P15 per A2 cell, FR",
                     "P15 per A2 cell, C2 relaxations 1-4", "P15 per A2 cell, C4b", "P15 WP2c at Pb136 (m30, Sr)",
                     "P15 WP2c at FA128 (m30, GA)", "P15 WP2c at Pb124 (m05, Sr)", "P15 D3(BJ)", "P15 required hosts",
                     "P15 pose-pilot spreads", "P15 noise-pilot per-site values", "P15 determinism (P §5)",
                     "P15 throughput row")             # P:542-547 and P:788-820, restated (not from e_eval)


def expected_coverage(b5_open, fr_fail=True):
    """The coverage table restated (P:542-547, P:788-820; spec 12.8): item -> reason, for an FR-fail or FR-STOP route,
    with block 5 opened (the deferred hinge run) or not (fix round 1: the reasons are pinned, not only the items)."""
    b5 = "block 5" if b5_open else "deferred to block 5"
    at = (lambda rid: f"{b5}, {rid}") if b5_open else (lambda rid: b5)
    noc3, noc4 = ("not formed (FR failed: no C3b)", "C4b not run") if fr_fail else ("block 4", "block 4")
    return {"P10 q = 0 Sr76": "block 3, B3.q0.Sr76", "P10 q = 0 Cl138": "block 3, B3.q0.Cl138",
            "P10 q = 0 Cs128": "block 3, B3.q0.Cs128", "P10 q = 0 GA128": "block 3, B3.q0.GA128",
            "P10 q = 0 Sr136": at("B5.q0.Sr136"), "P10 q = 0 Ca136": at("B5.q0.Ca136"),
            "P15 per-site e_h(j), E_d(j), G_d, raw E_b, far-site values": noc3,
            "P15 shared-region sensitivity": noc4, "P15 invalid cells (C1, C2, FR)": "block 3, B3.inv",
            "P15 invalid cells (C3b, C4b)": noc3, "P15 plateau-excluded intervals": noc4,
            "P15 zero-shot MACE E_b, pilot cells": "block 3, B3.noise, B3.start, B3.pose",
            "P15 zero-shot MACE E_b, production quartets": noc3, "P15 zero-shot MACE E_b, Pb136": at("B5.mace"),
            "P15 DFT residual forces, A1 cells outside Pb136": "block 3, B3.forces",
            "P15 DFT residual forces, Pb136": at("B5.forces"), "P15 DFT residual forces, C3b": noc3,
            "P15 per A2 cell, C2 relaxations 5-8": "block 1, B1", "P15 per A2 cell, FR": "block 2, B2",
            "P15 per A2 cell, C2 relaxations 1-4": at("B5"), "P15 per A2 cell, C4b": noc4,
            "P15 WP2c at Pb136 (m30, Sr)": at("B5.wp2c"), "P15 WP2c at FA128 (m30, GA)": noc4,
            "P15 WP2c at Pb124 (m05, Sr)": noc4,
            "P15 D3(BJ)": "withdrawn (D3BJ_AMENDMENT.md; sensitivity study after E)", "P15 required hosts": noc3,
            "P15 pose-pilot spreads": "block 3, B3.pose.gate", "P15 noise-pilot per-site values": "block 3, B3.noise",
            "P15 determinism (P §5)": "block 3, B3.det", "P15 throughput row": "block 3, B3.throughput"}


def coverage_lines(t):
    """{item: reason} of the COVERAGE section of an E output."""
    sec = t.split("COVERAGE (P §10, §15; S2B:711-712)\n", 1)[1].split("\n\n", 1)[0]
    out = {}
    for x in sec.split("\n"):
        if x.strip():
            k, v = x.strip().split(": ", 1)
            assert k not in out, k
            out[k] = v
    return out


def _labelled(r, x, lab):
    """The printed line of row x carries the text of label lab (S2B:623-629: beside the value, on its line)."""
    t = r.result_text
    k = t.index(x.text + "  -- ")
    return LABELS[lab] in t[k:t.index("\n", k)]


A1_ROW_IDS = ("B1.EbA1", "B1.EbA1.gateN", "B1.delta", "B3.pose.Cs188", "B3.pose.Cl175", "XC-DSUM-FAR")   # RF-25
# ER2-1: the C1 gate statistics of A1 E_b in block 3: gate N's sigma_far (5 rows, 5 cross-checks) and the pose gate's
# a_pose, delta_near and delta_far (2 rows, 2 cross-checks)
A1_GATE_ROW_PREFIXES = ("B3.gateN.", "XC-GATEN-SIGMA", "B3.pose.gate.", "XC-POSE")


def _wrap_no_rf25(orig):
    def f(self, block, rid, kind, text, **kw):
        kw["has_a1"] = False
        return orig(self, block, rid, kind, text, **kw)
    return f


def _wrap_no_rf25_gate(orig):
    def f(self, block, rid, kind, text, **kw):
        if rid.startswith(A1_GATE_ROW_PREFIXES):
            kw["has_a1"] = False
        return orig(self, block, rid, kind, text, **kw)
    return f


def _wrap_cov_twice(orig):
    def f(self):
        out = orig(self)
        return out + [out[0]]
    return f


def _wrap_drop_label(orig, lab):
    def f(self, block, rid, kind, text, **kw):
        kw["labels"] = tuple(x for x in kw.get("labels", ()) if x != lab)
        return orig(self, block, rid, kind, text, **kw)
    return f


@case("C4", "C", mutants=(
        # RF-25: the item-4 label not attached to the DFT column of MACE rows
        ("no_rf25", lambda fx: patched(ee().Out, "row", _wrap_no_rf25(ee().Out.row))),
        # a coverage item printed twice
        ("coverage_twice", lambda fx: patched(ee().Run, "coverage", _wrap_cov_twice(ee().Run.coverage))),
        # the q = +1 comparator formed from a q = 0 single point
        ("noform_lost", lambda fx: patched(ee(), "L", {**ee().L, "L_NOFORM_C1": "formable"})),
        # fix round 2: the q = 0 link label dropped from its rows (M40)
        ("q0_label_lost", lambda fx: patched(ee().Out, "row", _wrap_drop_label(ee().Out.row, "L_Q0"))),
        # ER2-1 reverted: the C1 gate statistics of A1 E_b without the item-4 label
        ("gate_stats_no_item4", lambda fx: patched(ee().Out, "row", _wrap_no_rf25_gate(ee().Out.row)))))
def case_c4(fx):
    """Labels (C1a; fix round 1: the coverage reasons, every A1-bearing row by id with L_ITEM4 on its printed line,
    and the invalid-cell table 3.6 as an exact set are pinned): L_NOFORM_C1 on both GA128 rows and on the q = +1
    rows of Cs128 and Cl138; L_NOA1 on every
    start-set row and on the Cs128 and Cl138 pose rows; L_ITEM4 on the noise-pilot rows and on the DFT column of the
    Cs188 and Cl175 pose rows (RF-25); 'not formed' (block 2.3); L_MACE on every MACE and determinism row; L_TAIL on
    every Delta F_tail row; L_FAR on E_b^A2(Pb76) and delta_far(Pb76); the coverage table holds every P section 10
    and 15 item exactly once. Integration: L_ITEM4 also on the C1 gate statistics of A1 E_b (gate N's sigma_far
    rows and XC-GATEN-SIGMA, the pose gate rows and XC-POSE; ER2-1, pinned); XC-DSUM-FAR carries L_FAR beside
    L_ITEM4, as delta_far(Pb76) does (ER2-2)."""
    r, sr = run_of(fx, "C1a")
    t, Lb = r.result_text, LABELS
    for k, v in LABELS.items():
        assert ee().L[k] == v, k
    for rid in ("B3.q0.GA128", "B3.q1.GA128", "B3.q1.Cs128", "B3.q1.Cl138"):
        assert row(r, rid).text.endswith(Lb["L_NOFORM_C1"]), rid
    st = rows_by(r, "B3.start.")
    assert len(st) == 8 and all("L_NOA1" in x.labels and "L_ITEM4" not in x.labels for x in st)
    for k in ("Cs128", "Cl138"):
        assert "L_NOA1" in row(r, f"B3.pose.{k}").labels
    for k in ("Cs188", "Cl175"):
        assert "L_ITEM4" in row(r, f"B3.pose.{k}").labels
    noise = rows_by(r, "B3.noise.")
    assert len(noise) == 40 and all({"L_ITEM4", "L_MACE"} <= set(x.labels) for x in noise)
    assert row(r, "B2.quartet").text.startswith("not formed (")
    assert all("L_MACE" in x.labels for x in r.rows if x.kind in ("E_mace", "Eb_mace", "determinism"))
    tails = [x for x in r.rows if x.kind == "dF_tail"]
    assert len(tails) >= 8 and all("L_TAIL" in x.labels for x in tails)
    assert all("L_FAR" in row(r, rid).labels for rid in ("B1.EbA2", "B1.delta"))
    # ER2-2: XC-DSUM-FAR carries L_FAR as B1.delta does; on an FR-fail route both keep L_ITEM4 beside it, on the line
    assert all({"L_ITEM4", "L_FAR"} <= set(row(r, rid).labels) and _labelled(r, row(r, rid), "L_FAR") and
               _labelled(r, row(r, rid), "L_ITEM4") for rid in ("B1.delta", "XC-DSUM-FAR"))
    cov =[x.split(": ", 1)[0] for x in t.split("COVERAGE (P §10, §15; S2B:711-712)\n", 1)[1].split("\n\n", 1)[0]
           .split("\n") if x.strip()]
    cov = [x.strip() for x in cov]
    assert sorted(cov) == sorted(EXPECTED_COVERAGE) and len(cov) == len(set(cov)), cov
    # fix round 1: the reasons pinned (L4), every A1-bearing row pinned by id with L_ITEM4 on its printed line
    # (RF-25, independently of Row.has_a1; E65), and the invalid-cell table 3.6 as an exact set (L7, L8)
    assert coverage_lines(t) == expected_coverage(False), coverage_lines(t)
    pinned = [row(r, i) for i in A1_ROW_IDS] + [x for x in r.rows if x.id.startswith("B3.noise.") or
                                                x.id == "XC-GATEN"] + \
        [x for x in r.rows if x.id.startswith(("B3.q0.", "B3.q1.", "B3.q01.")) and x.kind != "note"] + \
        [x for x in r.rows if x.id.startswith(A1_GATE_ROW_PREFIXES)]                     # ER2-1
    assert len(pinned) == 6 + 40 + 40 + 5 + 14, len(pinned)
    bad = [x.id for x in pinned if "L_ITEM4" not in x.labels or not _labelled(r, x, "L_ITEM4")]
    assert not bad, bad[:5]
    inv = {x.id: x.text for x in rows_by(r, "B3.inv.")}
    assert set(inv) == {"B3.inv.c1.s2_m30_Cs128p4_vac", "B3.inv.c1.s2_m30_Cs128p5_novac",
                        "B3.inv.pair.m30_Cs188p3.json", "B3.inv.pair.m30_Cs188p6.json",
                        "B3.inv.c2.s2r_m30_VB76", "B3.inv.fr.s2r_m30_VA188", "B3.inv.fr.s2r_m30_Cs188o0_novac",
                        "B3.inv.fr.s2r_m30_Cs188o0_vac"}, sorted(inv)
    assert inv["B3.inv.c2.s2r_m30_VB76"] == "c2 m30 s2r_m30_VB76 — B76 — [5]"
    assert inv["B3.inv.c1.s2_m30_Cs128p4_vac"].endswith("[3]")
    assert inv["B3.inv.c1.s2_m30_Cs128p5_novac"].endswith(" None")      # fix round 2 (M42): valid None is listed
    assert inv["B3.inv.pair.m30_Cs188p3.json"].endswith("pair rejected (Inadmissible)")
    assert "status complete; end rule accepted_converged; failed [5]" in inv["B3.inv.fr.s2r_m30_VA188"]
    # fix round 2 (M40): L_Q0 on every q = 0, q = +1 and difference row of block 3, on its printed line
    q0 = [x for x in r.rows if x.id.startswith(("B3.q0.", "B3.q1.", "B3.q01.")) and x.kind in ("Eb_q0", "Eb_q1")]
    assert len(q0) == 5 and all("L_Q0" in x.labels and _labelled(r, x, "L_Q0") for x in q0), [x.id for x in q0]
    # fix round 2 (S2B:633): the recorded C1 gate values at 0.01 meV, no raw repr
    num = r"-?\d+\.\d\d meV|none"
    for d in ("Sr", "Ca", "Cl", "Cs", "GA"):
        x = row(r, f"B3.gateN.{d}")
        assert re.fullmatch(rf"gate N {d}: sigma_far_meV ({num}), df \S+, pass \S+", x.text), x.text
    for tok in ("Cs", "Cl"):
        x = row(r, f"B3.pose.gate.{tok}")
        side = rf"N_D \S+, N_DV \S+, count_term_meV ({num})"
        assert re.fullmatch(rf"pose {tok}: mode \S+, a_pose_meV ({num}), delta_near_meV ({num}), delta_far_meV "
                            rf"({num}); near {side}; far {side}", x.text), x.text
    for x in rows_by(r, "XC-POSE"):
        assert re.fullmatch(rf"XC-POSE: pose (Cs|Cl): recomputed mode \S+, a_pose ({num}), delta_near ({num}), "
                            rf"delta_far ({num}): ok", x.text), x.text
    for x in rows_by(r, "XC-GATEN-SIGMA"):
        res = r"(\|Δ\| = \S+ meV \(tolerance 1e-06 meV\)|\|Δ\| not formed)"
        assert re.fullmatch(rf"XC-GATEN-SIGMA: gate N \S+: recomputed sigma_far ({num}), df \d+; recorded ({num}), "
                            rf"df \S+, {res}: ok", x.text), x.text




@case("C5", "C", mutants=(
        ("strict_bound", lambda fx: patched(ee(), "fr2_pass", lambda d: d is not None and abs(d) < 50.0)),
        ("bound_moved", lambda fx: patched(ee(), "FR2_MAX_MEV", 50.0005))))
def case_c5(fx):
    """FR-2 boundary (S2B:589): fr2_pass(+-50.000) is True and fr2_pass(+-50.001) is False; a missing value fails."""
    f = ee().fr2_pass
    assert f(50.0) is True and f(-50.0) is True and f(50.001) is False and f(-50.001) is False and f(None) is False
    assert f(49.9999) is True and f(50.0000001) is False


def _wrap_frvalid_beside_far(orig):
    """ER2-2 reverted: a row carrying L_FAR also carries the route's item-4 label (the round-2 code)."""
    def f(self, block, rid, kind, text, **kw):
        labels = tuple(kw.get("labels", ()))
        if "L_FAR" in labels and (kw.get("has_a1") or kind in ("Eb_A1", "Eb_q0", "Eb_q1")):
            kw["labels"] = (self.item4,) + labels
        return orig(self, block, rid, kind, text, **kw)
    return f


def _rewrite_fr2_false(root, man):
    """Plant a decision.FR.FR2 = False that disagrees with |delta| <= 50 (and the outcome that follows from it)."""
    fr = os.path.join(root, "fr")
    dec = {"outcome": "fail", "FR1": True, "FR2": False, "part": "FR-2", "cell": None, "kind": None}
    p = os.path.join(fr, "gates", "FR.json")
    with open(p) as fh:
        g = json.load(fh)
    g["decision"]["FR"] = dec
    g["result"]["FR2"]["passed"] = False
    sha = dump(p, g)
    dump(os.path.join(fr, "gates_applied", "gate_FR.gate.json"), g)
    mp = os.path.join(fr, "gates_applied", "gate_FR.json")
    with open(mp) as fh:
        m = json.load(fh)
    m["decision"], m["gate_file_sha256"] = g["decision"], sha
    dump(mp, m)
    for name, key in (("campaign.json", None), ("state_end.json", "FR")):
        q = os.path.join(fr, name)
        with open(q) as fh:
            d = json.load(fh)
        if key:
            d[key] = dec
        else:
            d["fr_outcome"] = "fail (FR-2)"
        dump(q, d)


@case("C5b", "C", mutants=(
        ("strict_bound", lambda fx: patched(ee(), "fr2_pass", lambda d: d is not None and abs(d) < 49.99)),
        # ER2-2 reverted: L_FRVALID beside L_FAR on delta_far(Pb76) and its cross-check
        ("frvalid_beside_far", lambda fx: patched(ee().Out, "row", _wrap_frvalid_beside_far(ee().Out.row)))))
def case_c5b(fx):
    """FR-2 at |delta| = 50.000 meV (planted 49.9999) passes end to end (FR pass, a block-4 test double on the
    route C4B-NOTRUN): header 'pass' and '1 of 2', XC-FR2-DEC ok, L_FRVALID on the A1 values; with a planted
    decision.FR.FR2 = False that disagrees, the XC-FR2-DEC line reads 'cross-check failed' and E exits 1 with its
    output complete. Integration: on this FR-pass route delta_far(Pb76) and XC-DSUM-FAR carry L_FAR and not
    L_FRVALID, while E_b^A1(Pb76) keeps L_FRVALID (ER2-2); the C1 gate statistics of A1 E_b carry L_FRVALID
    (ER2-1)."""
    sr = repo_of(fx, "pass_50")
    dbl = B4Double("C4B-NOTRUN", None, sr.commits["F"])
    r = e_run(fx, sr, ["--run"], block4=dbl)
    assert r.rc == 0, r.result_text[-1200:]
    assert HDR.format("pass", 1) in r.result_text and row(r, "XC-FR2-DEC").text.endswith(": ok")
    assert "L_FRVALID" in row(r, "B2.EbA1").labels and "L_ITEM4" not in row(r, "B2.EbA1").labels
    for rid in ("B1.delta", "XC-DSUM-FAR"):                                                   # ER2-2
        x = row(r, rid)
        assert "L_FAR" in x.labels and _labelled(r, x, "L_FAR") and not \
            {"L_FRVALID", "L_ITEM4"} & set(x.labels) and LABELS["L_FRVALID"] not in x.line, (rid, x.labels)
    assert "L_FRVALID" in row(r, "B1.EbA1").labels and _labelled(r, row(r, "B1.EbA1"), "L_FRVALID")
    gate = [x for x in r.rows if x.id.startswith(A1_GATE_ROW_PREFIXES)]                     # ER2-1
    assert len(gate) == 14 and all("L_FRVALID" in x.labels and "L_ITEM4" not in x.labels for x in gate), \
        [(x.id, x.labels) for x in gate if "L_FRVALID" not in x.labels][:3]
    assert 49.9995 < row(r, "B2.delta").values["delta_meV"] <= 50.0 and "BLOCK 4. Tier block (" in r.result_text
    assert row(r, "B3.inv.fr").text == "fr: none" and not rows_by(r, "B3.inv.fr.")
    srp = repo_of(fx, "C5_planted", SCEN["pass_50"], post=_rewrite_fr2_false)
    rp = e_run(fx, srp, ["--run"])
    x = row(rp, "XC-FR2-DEC")
    assert rp.rc == 1 and "L_XFAIL" in x.labels and "cross-check failed" in rp.result_text.split(x.text, 1)[1][:40]
    assert rp.result_text.rstrip("\n").endswith("END\nE exit code: 1")


def _hinge_delta_pb76(v):
    return v["Pb76"]["delta"]


@case("C6", "C", mutants=(
        # delta_Sr,m30 taken from Pb76 (spec 13: never)
        ("delta_from_pb76", lambda fx: patched(ee(), "hinge_delta", _hinge_delta_pb76)),
        # the trigger needs df_delta > 3
        ("trigger_strict", lambda fx: patched(ee(), "hinge_trigger", _wrap_trigger(ee().hinge_trigger, 4)))))
def case_c6(fx):
    """Hinge opened (a test double of e_block4 with BLOCK4_IMPLEMENTED True, route C4B-ENDED, df_delta = 3):
    block 5 is printed; delta_Sr,m30 equals the independent hinge value and is passed to evaluate_tier, not the
    Pb76 delta; XC-K3HINGE ok; L_HINGE_DIFF, L_CA_Q0, L_CA_MACE and the WP2c row; the Pb136 canaries now print.
    Fix round 1: every block-5 value recomputed independently (check_block5), the WP2c row from the synthetic
    stand-in with the extracted wp2cde_dft.json never opened."""
    sr = repo_of(fx, "pass")
    dbl = B4Double("C4B-ENDED", 3, sr.commits["F"])
    r = cached(fx, ("run", "C6"), lambda: e_run(fx, sr, ["--run"], block4=dbl))
    assert r.rc == 0, r.result_text[-1500:]
    t = r.result_text
    assert "BLOCK 5. Hinge block: relaxations 1-4" in t and "trigger held: block 5 opened" in t
    F = {role_of_lab(lab): sr.man["c2"][lab]["F"] for lab in eg.HINGE}
    d = _ind_eb({k: _ind_eV(v[-1]) for k, v in F.items()}) - _ind_eb({k: _ind_eV(v[0]) for k, v in F.items()})
    dd = row(r, "B5.delta").values["delta_meV"]
    assert abs(dd - float(d)) <= 1e-6 and r.b4.calls[-1] == dd and r.b4.calls[-1] != row(r, "B1.delta").values[
        "delta_meV"]
    assert all(x.text.endswith(": ok") for x in r.rows if x.id == "XC-K3HINGE") and len(rows_by(r, "XC-K3HINGE")) == 2
    assert "L_HINGE_DIFF" in row(r, "B5.hingediff").labels and row(r, "B5.q0.Ca136").text.endswith(ee().L["L_CA_Q0"])
    assert "L_CA_MACE" in row(r, "B5.mace.Ca136").labels and "L_WP2C" in row(r, "B5.wp2c").labels
    man, ry = sr.man, float(RY)
    shown = [x for lab in eg.HINGE for x in ("%.6f" % (float(man["c2"][lab]["F"][0]) * ry),
                                             "%.6f" % (float(man["c2"][lab]["F"][-1]) * ry))]
    shown += ["%.6f" % v for w in eg.PB136_WIDS for _, v in man["c1_mace"][w]]
    shown += ["%.6f" % (float(sp_F(lab)) * ry) for lab in ("s2_m30_VB136", "s2_m30_Sr136o0_vac")]
    for s in shown:
        assert s in t, s
    check_block5(r, sr)


def check_block5(r, sr):
    """Fix round 1 (C6): the block-5 values recomputed from the planted strings with Fraction, as C2 does for blocks
    1-3: E_b^A1(Pb136), E_b^A2(Pb136), E_b^A2(Pb136) - E_b^A2(Pb76) (E5), the q = 0 and q = +1 rows at Sr136 with D
    from k = 0 of s2r_m30_Sr136o0_novac (E6), the step-0 F(k = 0) - F(SP); the WP2c row prints the synthetic
    stand-in and the extracted wp2cde_dft.json is never opened (RF-9)."""
    man = sr.man

    def near(a, b, tol=1e-6):
        assert a is not None and abs(float(a) - float(b)) <= tol, (a, float(b))
    Fh = {role_of_lab(lab): man["c2"][lab]["F"] for lab in eg.HINGE}
    Ff = {role_of_lab(lab): man["c2"][lab]["F"] for lab in eg.FAR}
    a1 = _ind_eb({k: _ind_eV(v[0]) for k, v in Fh.items()})
    a2 = _ind_eb({k: _ind_eV(v[-1]) for k, v in Fh.items()})
    a2_76 = _ind_eb({k: _ind_eV(v[-1]) for k, v in Ff.items()})
    for rid, key, v in (("B5.EbA1", "Eb_A1_meV", a1), ("B5.EbA2", "Eb_A2_meV", a2), ("B5.delta", "delta_meV", a2 - a1),
                        ("B5.hingediff", "diff_meV", a2 - a2_76)):
        x = row(r, rid)
        near(x.values[key], v)
        assert _fmt_ok(v, x.text), (rid, x.text)
    D0, host = _ind_eV(man["c2"]["s2r_m30_Sr136o0_novac"]["F"][0]), _ind_eV(sp_F("s2_m30_host"))
    e0 = _ind_eb({"DV": _ind_eV(sp_F("s2_m30_Sr136o0_vac_q0")), "D": D0, "V": _ind_eV(sp_F("s2_m30_VB136_q0")),
                  "host": host})
    e1 = _ind_eb({"DV": _ind_eV(sp_F("s2_m30_Sr136o0_vac")), "D": D0, "V": _ind_eV(sp_F("s2_m30_VB136")),
                  "host": host})
    near(row(r, "B5.q0.Sr136").values["Eb_q0_meV"], e0)
    near(row(r, "B5.q1.Sr136").values["Eb_q1_meV"], e1)
    assert _fmt_ok(e1 - e0, row(r, "B5.q1.Sr136").text)
    for sp, lab in eg.STEP0_PAIRS.items():
        dd = (_ind_eV(man["c2"][lab]["F"][0]) - _ind_eV(sp_F(sp))) * 1000
        near(row(r, f"B5.step0.{sp}").values["dF_meV"], dd)
    assert "WP2c m30 Sr136: Eb_dft_meV 4242.42 meV, Eb_dft_farref_meV 4343.43 meV; beside" in \
        row(r, "B5.wp2c").text                            # fix round 2: 0.01 meV (S2B:633), no dict repr
    assert all("L_Q0" in row(r, i).labels and _labelled(r, row(r, i), "L_Q0") for i in ("B5.q0.Sr136", "B5.q1.Sr136"))
    assert not any(e["rel"].endswith("wp2cde_dft.json") for e in r.au.log.values())
    assert all(r.item4 in row(r, i).labels for i in ("B5.EbA1", "B5.delta", "B5.wp2c", "B5.mace.Sr136",
                                                     "XC-DSUM-HINGE", "XC-MACEPILOT-A1"))


def _wrap_trigger(orig, threshold):
    def f(route_id, b4=None, ctx=None):
        r = orig(route_id, b4, ctx)
        if r["df_delta"] is not None:
            r["held"] = r["df_delta"] >= threshold
        return r
    return f


@case("C7", "C", mutants=(
        ("trigger_loose", lambda fx: patched(ee(), "hinge_trigger", _wrap_trigger(ee().hinge_trigger, 2))),))
def case_c7(fx):
    """The same test double with df_delta = 2: the count line reads 2 and 'not held'; no hinge path is opened. Fix
    round 2 (M52): on the route C4B-STOP the line reads 'not formed (C4b final STOP)'."""
    sr = repo_of(fx, "pass")
    r = e_run(fx, sr, ["--run"], block4=B4Double("C4B-ENDED", 2, sr.commits["F"]))
    assert r.rc == 0, r.result_text[-800:]
    assert ("BLOCK 5. Hinge block: not opened. df_δ counted from validity leaves (Sr's C2 hinge quartet counted "
            "valid): 2; trigger df_δ ≥ 3: not held.") in r.result_text
    assert_closed_paths(r)
    for s in hinge_canaries(sr):
        assert s not in r.result_text
    r2 = e_run(fx, sr, ["--run"], block4=B4Double("C4B-STOP", None, sr.commits["F"]))
    assert r2.rc == 0 and ("BLOCK 5. Hinge block: not opened. df_δ counted from validity leaves (Sr's C2 hinge "
                           "quartet counted valid): not formed (C4b final STOP); trigger df_δ ≥ 3: not held.") in \
        r2.result_text, r2.result_text[-800:]




@case("C8", "C", mutants=(
        ("tolerance_loose", lambda fx: patched(ee(), "TOL_MEV", 1e-5)),))
def case_c8(fx):
    """A cross-check failure (the K3 .far value off by 2e-6 meV): the 'cross-check failed' line with both values;
    exit 1; the output is complete and the figure source data is written; the CROSS-CHECKS summary counts (fix
    round 1)."""
    sr = repo_of(fx, "C8", {"fr": SCEN["C1a"]["fr"], "k3_far_offset": 2e-6})
    r = e_run(fx, sr, ["--run"])
    assert r.rc == 1 and r.result_text.rstrip("\n").endswith("END\nE exit code: 1")
    bad = [x for x in r.rows if x.id == "XC-K3FAR" and "L_XFAIL" in x.labels]
    assert len(bad) == 2 and all("2.000e-06" in x.text or "1.9" in x.text for x in bad)
    assert len(r.files) == 3 and "CROSS-CHECKS" in r.result_text
    assert "\n  XC-K3FAR: 0 ok, 2 cross-check failed, 0 not evaluated\n" in r.result_text
    assert "\n  XC-FR2-DEC: 0 ok, 0 failed, 1 not evaluated\n" in r.result_text


def _det_unformed(orig):
    def f(*a, **kw):
        d = {p: dict(v) for p, v in orig(*a, **kw).items()}
        d["m30"]["max_dr_A"] = None                          # one determinism value not formed
        return d
    return f


def _xc_never_fails(orig):
    def f(self, block, xid, ok, text, **kw):
        return orig(self, block, xid, True if ok is False else ok, text, **kw)
    return f


@case("C8b", "C", mutants=(
        # a failed cross-check printed as passed
        ("xc_never_fails", lambda fx: patched(ee().Out, "xc", _xc_never_fails(ee().Out.xc))),))
def case_c8b(fx):
    """Further cross-check failures planted in one run of C1f (engineer C; spec 15, S2B:739-740): XC-C2R (a
    C2_RESULT.md constant of hostB76 changed), XC-FRSTEP0 (the 0.5 meV bound moved below every |dF|), XC-DETERMINISM
    (one value not formed) and XC-MACE-COUNT (the expected leaf count changed) each print 'cross-check failed'; no
    other cross-check fails; exit 1; the output and the figure source data are complete."""
    sr = repo_of(fx, "C1f")
    c2r = dict(ee().C2_RESULT)
    c2r["s2r_m30_hostB76"] = (c2r["s2r_m30_hostB76"][0] + 1,) + c2r["s2r_m30_hostB76"][1:]
    with multi(patched(ee(), "C2_RESULT", c2r), patched(ee(), "STEP0_MEV", -1.0),
               patched(fx.ex.m48, "_determinism", _det_unformed(fx.ex.m48._determinism)),
               patched(eg, "MACE_LEAVES_BLOCK3", eg.MACE_LEAVES_BLOCK3 + 1)):
        r = e_run(fx, sr, ["--run"])
    assert r.rc == 1 and r.result_text.rstrip("\n").endswith("END\nE exit code: 1"), r.result_text[-600:]
    failed = {x.id for x in r.rows if x.kind == "xcheck" and "L_XFAIL" in x.labels}
    assert failed == {"XC-C2R", "XC-FRSTEP0", "XC-DETERMINISM", "XC-MACE-COUNT"}, failed
    assert len(r.files) == 3


def _post_c6b(root, man):
    """The C2 step-0 dF of VB136 off by 1e-5 meV in its own gate copy (XC-STEP0-C2). Fix round 2 (M37): the decision
    of the Sr136o0_vac copy 'fail_final' while its cell passed (the decision part of XC-STEP0-C2)."""
    _post_json("c2/gates_applied/gate_step0_1.gate.json",
               lambda d: d["result"]["cells"]["s2_m30_VB136"].update(
                   dF_meV=d["result"]["cells"]["s2_m30_VB136"]["dF_meV"] + 1e-5))(root, man)
    _post_json("c2/gates_applied/gate_step0_4.gate.json",
               lambda d: d["decision"]["step0"].update(outcome="fail_final"))(root, man)


def _rr_shift_relax(labs):
    """read_relaxation with the relaxation energy of the given labels 1e-3 meV off (the signed-sum identities)."""
    orig = er.read_relaxation

    def f(ctx, c, lab, **kw):
        out = orig(ctx, c, lab, **kw)
        if lab in labs and out.get("relax_meV") is not None:
            out["relax_meV"] += 1e-3
        return out
    return f


def _mace_pilot_a1_off(orig):
    def f(T):
        out = orig(T)
        sr = ((out.get("calibration") or {}).get("m30") or {}).get("Sr136")
        if sr is not None and sr.get("Eb_A1_dft_meV") is not None:
            sr["Eb_A1_dft_meV"] += 1e-3                           # XC-MACEPILOT-A1 (block 5 only)
        return out
    return f


def _extend_drop_row(orig):
    def f(T, ledger, c1, rel):
        T2, rows = orig(T, ledger, c1, rel)
        return T2, rows[:-1]                                       # one Pb136 record missing (XC-MACE-COUNT)
    return f


@case("C6b", "C")
def case_c6b(fx):
    """Block-5 cross-check failures planted (fix round 1; S2B:739-740): the K3 .hinge value off by 2e-6 meV in both K3
    files (XC-K3HINGE) and the C2 step-0 dF of VB136 off by 1e-5 meV (XC-STEP0-C2). Fix round 2: the Sr136o0_vac
    step-0 decision 'fail_final' with its cell passed (XC-STEP0-C2, the decision part), and white box the relaxation
    energy of hostB136 1e-3 meV off (XC-DSUM-HINGE), _mace_pilot's Eb_A1_dft_meV at Sr136 1e-3 meV off
    (XC-MACEPILOT-A1) and one Pb136 record dropped from the block-5 table (XC-MACE-COUNT): exactly those print
    'cross-check failed', exit 1, and the output is complete."""
    sr = repo_of(fx, "C6b", {"k3_hinge_offset": 2e-6}, post=_post_c6b,
                 e_text={f"{ee().S2_REL}/s2b/e_block4.py": block4_true_text()})
    with multi(patched(er, "read_relaxation", _rr_shift_relax(("s2r_m30_hostB136",))),
               patched(fx.ex.m48, "_mace_pilot", _mace_pilot_a1_off(fx.ex.m48._mace_pilot)),
               patched(er, "extend_c1_table_hinge", _extend_drop_row(er.extend_c1_table_hinge))):
        r = e_run(fx, sr, ["--run"], block4=B4Double("C4B-ENDED", 3, sr.commits["F"]))
    assert r.rc == 1 and r.result_text.rstrip("\n").endswith("END\nE exit code: 1"), r.result_text[-600:]
    failed = collections.Counter(x.id for x in r.rows if x.kind == "xcheck" and "L_XFAIL" in x.labels)
    assert failed == {"XC-K3HINGE": 2, "XC-STEP0-C2": 2, "XC-DSUM-HINGE": 1, "XC-MACEPILOT-A1": 1,
                      "XC-MACE-COUNT": 1}, failed
    assert "\n  XC-K3HINGE: 0 ok, 2 cross-check failed, 0 not evaluated\n" in r.result_text
    assert "\n  XC-MACE-COUNT: 1 ok, 1 cross-check failed, 0 not evaluated\n" in r.result_text


def _post_c8c(root, man):
    """One inconsistency per cross-check that no other case makes fail (fix round 1)."""
    def gate_n(d):
        res = d["result"]["dopants"]
        res["Cl"]["hosts"]["m05"]["per_site_meV"]["175"] += 2e-6                 # XC-GATEN (one row)
        res["Sr"]["sigma_far_meV"] += 1e-3                                         # XC-GATEN-SIGMA (Sr)
    _post_json("c1/gates/N.json", gate_n)(root, man)
    _post_json("c1/gates/pose.json", lambda d: d["result"]["Cs"].update(
        a_pose_meV=d["result"]["Cs"]["a_pose_meV"] + 1e-3))(root, man)             # XC-POSE (Cs)
    _post_json("c2/raw/s2r_m30_VB136.a2.json", lambda d: d["end_rule"].update(outcome="accepted_plateau"))(root, man)
    _post_json("fr/raw/s2r_m30_hostA188.a2.json", lambda d: d.update(restarts=1))(root, man)   # XC-PARTS
    _post_fr_dec(cell="s2r_m30_hostA188")(root, man)                               # XC-FR1-DEC
    _post_json("fr/gates_applied/gate_fr_step0_2.gate.json", lambda d: d["result"]["cells"]["s2_m30_VA188"].update(
        dF_meV=d["result"]["cells"]["s2_m30_VA188"]["dF_meV"] + 1e-5))(root, man)  # XC-FRSTEP0 (the recorded dF)


@case("C8c", "C")
def case_c8c(fx):
    """Further cross-check failures planted in one run of C1a (fix round 1; spec 15, S2B:739-740): gate N's per-site
    value off by 2e-6 meV (XC-GATEN), its sigma_far (XC-GATEN-SIGMA), the pose gate's a_pose (XC-POSE), a relaxation
    1-4 record with end rule accepted_plateau (XC-PLATEAU), restarts off by one (XC-PARTS), decision.FR.cell renamed
    consistently in every FR file (XC-FR1-DEC) and the recorded step-0 dF off by 1e-5 meV (XC-FRSTEP0): exactly that
    set fails, one row each, exit 1, the output complete."""
    sr = repo_of(fx, "C8c", {"fr": SCEN["C1a"]["fr"]}, post=_post_c8c)
    r = e_run(fx, sr, ["--run"])
    assert r.rc == 1 and r.result_text.rstrip("\n").endswith("END\nE exit code: 1"), r.result_text[-600:]
    failed = collections.Counter(x.id for x in r.rows if x.kind == "xcheck" and "L_XFAIL" in x.labels)
    assert failed == {"XC-GATEN": 1, "XC-GATEN-SIGMA": 1, "XC-POSE": 1, "XC-PLATEAU": 1, "XC-PARTS": 1,
                      "XC-FR1-DEC": 1, "XC-FRSTEP0": 1}, failed
    assert len(r.files) == 3


def _post_c8d(root, man):
    """Fix round 2: on C1i (FR-2 evaluated), result.FR2.Eb_A1_meV off by 2e-6 meV in FR.json and its copy (the
    marker's gate_file_sha256 follows), and the @2 step-0 decision 'fail_final' in its copy and marker while its cell
    passed (consistent, so that only XC-FRSTEP0's decision part can see it)."""
    fr = os.path.join(root, "fr")
    p = os.path.join(fr, "gates", "FR.json")
    with open(p) as fh:
        g = json.load(fh)
    g["result"]["FR2"]["Eb_A1_meV"] += 2e-6
    sha = dump(p, g)
    dump(os.path.join(fr, "gates_applied", "gate_FR.gate.json"), g)
    _post_json("fr/gates_applied/gate_FR.json", lambda d: d.update(gate_file_sha256=sha))(root, man)
    for f in (f"{eg.FR_S0_2}.gate.json", f"{eg.FR_S0_2}.json"):
        _post_json(f"fr/gates_applied/{f}", lambda d: d["decision"]["fr_step0"].update(outcome="fail_final"))(root, man)


def _xc_fail_labels_dropped(orig):
    """ER2-2 weakened (review E02): a failed cross-check carries L_XFAIL alone, not the labels of its value."""
    def f(self, block, xid, ok, text, **kw):
        if ok is False:
            kw["labels"] = ()
        return orig(self, block, xid, ok, text, **kw)
    return f


@case("C8d", "C", mutants=(
        ("xfail_drops_value_labels", lambda fx: patched(ee().Out, "xc", _xc_fail_labels_dropped(ee().Out.xc))),))
def case_c8d(fx):
    """Fix round 2 (M30-M32, M36, M38; S2B:739-740): on C1i, result.FR2.Eb_A1_meV off by 2e-6 meV in both FR files
    (XC-FR2, two rows), the @2 decision 'fail_final' while its cell passed (XC-FRSTEP0, the decision part), and white
    box the relaxation energies of hostB76 and hostA188 1e-3 meV off (XC-DSUM-FAR, XC-DSUM-FR) and the image-centre
    residual 1 A (XC-MIC, every relaxation read): exactly those print 'cross-check failed', exit 1, the output
    complete. Integration review 1 (ER2-2 on a failed XC-DSUM-FAR): on this FR-fail route the failed row keeps L_FAR
    beside L_ITEM4 on its line; on the FR-pass route (pass_50, C4B-NOTRUN double, hostB76 alone shifted) it keeps
    L_FAR and carries no L_FRVALID."""
    sr = repo_of(fx, "C8d", {"fr": SCEN["C1i"]["fr"]}, post=_post_c8d)
    with multi(patched(er, "read_relaxation", _rr_shift_relax(("s2r_m30_hostB76", "s2r_m30_hostA188"))),
               patched(er, "mic_residual", lambda *a, **kw: 1.0)):
        r = e_run(fx, sr, ["--run"])
    assert r.rc == 1 and r.result_text.rstrip("\n").endswith("END\nE exit code: 1"), r.result_text[-600:]
    failed = collections.Counter(x.id for x in r.rows if x.kind == "xcheck" and "L_XFAIL" in x.labels)
    assert failed == {"XC-FR2": 2, "XC-FRSTEP0": 1, "XC-DSUM-FAR": 1, "XC-DSUM-FR": 1, "XC-MIC": 8}, failed
    assert all("Eb_A1_meV" in x.text for x in r.rows if x.id == "XC-FR2" and "L_XFAIL" in x.labels)
    assert len(r.files) == 3
    x = row(r, "XC-DSUM-FAR")                                                                 # ER2-2, S2B:649
    assert {"L_XFAIL", "L_FAR", "L_ITEM4"} <= set(x.labels) and _labelled(r, x, "L_FAR"), x.labels
    sp = repo_of(fx, "pass_50")
    with patched(er, "read_relaxation", _rr_shift_relax(("s2r_m30_hostB76",))):
        rp = e_run(fx, sp, ["--run"], block4=B4Double("C4B-NOTRUN", None, sp.commits["F"]))
    x = row(rp, "XC-DSUM-FAR")
    assert rp.rc == 1 and "L_XFAIL" in x.labels and "L_FAR" in x.labels and _labelled(rp, x, "L_FAR") and \
        "L_FRVALID" not in x.labels and LABELS["L_FRVALID"] not in x.line, x.labels


@case("C9", "C", mutants=(
        ("clause_lost", lambda fx: patched(ee(), "L_A1TIER_CLAUSE", "")),))
def case_c9(fx):
    """Invariant-only pass (FR pass, result.invariant_only = [VA188], the block-4 test double on C4B-NOTRUN): block
    2.5 lists VA188; the labels the test double prints carry the bracketed clause."""
    sr = repo_of(fx, "inv")
    dbl = B4Double("C4B-NOTRUN", None, sr.commits["F"])
    r = e_run(fx, sr, ["--run"], block4=dbl)
    assert r.rc == 0, r.result_text[-800:]
    assert row(r, "B2.invariant_only").text.endswith(": s2r_m30_VA188")
    assert "; check 5 passed only under the identical-atom reading" in dbl.labels["L_A1TIER"]
    assert "(Cs, A f₁, 11.25 Å; S2b FR); check 5 passed only under the identical-atom reading. Invalid" in \
        r.result_text


@case("C10", "C", mutants=(
        ("message_printed", lambda fx: patched(ee(), "exc_line", lambda stage, e: f"FAILED: stage {stage}: {e}")),))
def case_c10(fx):
    """An exception inside block 3: the failure report holds only the stage name and the exception type (not its
    message, no block text); exit 3; no figure source data."""
    sr = repo_of(fx, "C1a")

    def boom(table):
        raise ValueError("planted 4242.4242 meV")
    with patched(fx.ex.m48, "_mace_pilot", boom):
        r = e_run(fx, sr, ["--run"])
    t = r.result_text
    assert r.rc == 3 and "FAILED: stage block 3: ValueError" in t and "BLOCK 1" not in t
    assert "planted" not in t and "4242.4242" not in t      # not "4242" alone: a hex digest may hold it
    assert list(r.files) == ["s2b/E_output.txt"] and t.rstrip("\n").endswith("E exit code: 3")


# ---------------------------------------------------------------- C11, C11b: the figure (spec 17; S2B:721-725)
def efig():
    """figures/fig_s2b_e_fk.py, loaded under its shared key (RF-19); it shares e_guard with E."""
    key = "_s2b_fig_s2b_e_fk"
    m = sys.modules.get(key)
    if m is None:
        s = importlib.util.spec_from_file_location(key, os.path.join(S2, "figures", "fig_s2b_e_fk.py"))
        m = importlib.util.module_from_spec(s)
        sys.modules[key] = m
        try:
            s.loader.exec_module(m)
        except BaseException:
            del sys.modules[key]
            raise
    return m


FIG_SCEN = ("C1a", "C1b", "C1c", "C1d", "C1e", "C1f", "C1g", "C1h", "C1i", "C1k", "C1l", "C1m",
            "C1n")                                                                         # the FR-fail routes


def fig_hinge_run(fx):
    """The deferred hinge run (backstop, injected clock) after a standing attempt 1 of scenario C1a (as D8)."""
    def make():
        sr = synth_repo(fx, "fig_hinge", SCEN["C1a"])
        assert e_run(fx, sr, ["--run"], keep=True).rc == 0
        commit(sr.repo, "E attempt 1 (unedited)")
        return e_run(fx, sr, ["--hinge", "--hinge-cause", "backstop"],
                     clock=lambda: datetime.datetime(2027, 7, 1, 12, tzinfo=datetime.timezone.utc))
    return cached(fx, ("run", "fig_hinge"), make)


def fig_c6_run(fx):
    sr = repo_of(fx, "pass")
    return cached(fx, ("run", "C6"), lambda: e_run(fx, sr, ["--run"], block4=B4Double("C4B-ENDED", 3, sr.commits["F"])))


def fig_inputs(r):
    """(suffix, CSV text, meta text, E output text) of a completed E run (spec 17: E's figure source data)."""
    suffix = "_hinge" if "s2b/E_hinge_output.txt" in r.files else ""
    name = "E_hinge_output.txt" if suffix else "E_output.txt"
    return (suffix, r.files[f"figures/source_data/fig_s2b_e_fk{suffix}.csv"],
            r.files[f"figures/source_data/fig_s2b_e_fk{suffix}_meta.csv"], r.files[f"s2b/{name}"])


def _csv_add_shifted(orig):
    def f(self, block, r, number, quartet):
        n = len(self.csv_rows)
        orig(self, block, r, number, quartet)
        if len(self.csv_rows) > n:                      # F(0) - F(final) written 0.01 meV off
            self.csv_rows[n]["dF_meV"] = repr(float(self.csv_rows[n]["dF_meV"]) + 0.01)
    return f


def _csv_texts_meta(orig, edit):
    def f(self, text):
        c, m = orig(self, text)
        return c, edit(m)
    return f


@case("C11", "C", mutants=(
        ("caption_no_header", lambda fx: patched(efig(), "caption", lambda meta: "Figure S2b-E.\n")),
        # E's figure source data disagrees with the values E printed
        ("csv_value_off", lambda fx: patched(ee().Run, "csv_add", _csv_add_shifted(ee().Run.csv_add))),
        # the meta of a hinge run lists block-1 end rules (the defect fixed by engineer C)
        ("meta_extra_end_rule", lambda fx: patched(ee().Run, "csv_texts", _csv_texts_meta(
            ee().Run.csv_texts, lambda m: m if "end_rule.s2r_m30_VB76," in m else
            m + "end_rule.s2r_m30_VB76,accepted_converged\n"))),
        # the FR status rows of panel b missing
        ("meta_no_status", lambda fx: patched(ee().Run, "csv_texts", _csv_texts_meta(
            ee().Run.csv_texts, lambda m: "".join(x for x in m.splitlines(True) if not x.startswith("status.")))))))
def case_c11(fx):
    """The figure on E's own source data (spec 17; S2B:619, 721-725): for the hinge run, every FR-fail scenario and
    the block-5 route (C6), the CSV columns are the figure's, every build assert of the figure passes on E's CSVs and
    E output (the values, ks, restart marks and Delta F_tail ks as printed; the header; the end rules; the FR status
    rows), the panels are blocks 1 and 2 (plus 5 for C6; 5 alone for the hinge run), and caption(meta) begins with the
    E output's header line; the FR cells without a curve are named in the caption. C1f and C6 are rendered (PDF, with
    the panel-alignment gate) and the caption file and PDF Subject hold the caption."""
    F = efig()
    assert F.COLS == ("block", "campaign", "order", "label", "quartet", "role", "k", "part", "dF_meV", "k_last",
                      "restart_start", "tail_k")
    assert {(m, str(a)): s for (m, a), s in ee().SUFFIX.items()} == F.SUFFIX
    assert set(F.E_OUTPUT.values()) == set(ee().EVAL_FILES + ee().HINGE_FILES)
    runs = [("hinge", fig_hinge_run(fx), [5])] + [(n, run_of(fx, n)[0], [1, 2]) for n in FIG_SCEN] + \
        [("C6", fig_c6_run(fx), [1, 2, 5])]
    for name, r, blocks in runs:
        assert r.rc in (0, 1), (name, r.rc, r.result_text[-400:])
        suffix, c, m, e = fig_inputs(r)
        assert tuple(c.split("\n", 1)[0].split(",")) == F.COLS, name
        rows, meta = F.parse_source(c, m)
        curves, pan = F.check(rows, meta, e, suffix)
        assert [b for _, b, _ in pan] == blocks, (name, pan)
        hdr = next(x for x in e.split("\n") if x.startswith("S2 K3: "))
        cap = F.caption(meta)
        assert meta["header"] == hdr and cap.startswith(hdr + "\n"), name
        drawn = {lab for _, b, labs in pan if b == 2 for lab in labs}
        for lab in eg.FR_ORDER if meta["mode"] == "evaluation" else ():
            assert (lab in drawn) == (f"{lab} (" not in cap), (name, lab)
    for name, r in (("C1f", run_of(fx, "C1f")[0]), ("C6", fig_c6_run(fx))):
        d = fx.workdir(f"fig_{name}")
        suffix, c, m, e = fig_inputs(r)
        write_text(os.path.join(d, "source_data", "fig_s2b_e_fk.csv"), c)
        write_text(os.path.join(d, "source_data", "fig_s2b_e_fk_meta.csv"), m)
        write_text(os.path.join(d, "E_output.txt"), e)
        out = os.path.join(d, "fig_s2b_e_fk")
        with contextlib.redirect_stdout(io.StringIO()):
            b = F.build(os.path.join(d, "source_data"), suffix, os.path.join(d, "E_output.txt"), out,
                        formats=("pdf",))
        with open(out + ".caption.txt") as fh:
            assert fh.read() == b["caption"] and b["caption"].startswith(b["meta"]["header"] + "\n")
        with open(out + ".pdf", "rb") as fh:
            assert fh.read(4) == b"%PDF"


@case("C11b", "C", mutants=(
        ("zero_unchecked", lambda fx: patched(efig(), "chk_zero_at_klast", lambda lab, c: None)),
        ("contiguity_unchecked", lambda fx: patched(efig(), "chk_contiguous", lambda lab, c: None)),
        ("tail_unchecked", lambda fx: patched(efig(), "chk_tail", lambda lab, c: None)),
        ("restarts_unchecked", lambda fx: patched(efig(), "chk_restarts", lambda lab, c: None)),
        ("e_output_unchecked", lambda fx: patched(efig(), "chk_e_output", lambda meta, curves, text: None)),
        ("caption_no_header", lambda fx: patched(efig(), "caption", lambda meta: "Figure S2b-E.\n"))))
def case_c11b(fx):
    """The figure script's own self-test (fig_s2b_e_fk.py --self-test, spec 17), in-process: on synthetic CSVs (three
    relaxations, one in three parts with negative values) the build succeeds, the caption begins with the header and
    is the PDF Subject, and each build assert refuses its planted violation (a non-zero value at k_last among them);
    the archive refusals are installed (RF-9)."""
    with contextlib.redirect_stdout(io.StringIO()):
        assert efig().self_test(render=not getattr(fx, "mutant", None)) == 0


@case("A4b", "A", mutants=(
        ("null_unchecked", lambda fx: patched(eg.EGuarded, "is_none", lambda self, path: True)),))
def case_a4b(fx):
    """A4, run level: a K3 value_meV = 1111.111 gives exit 3 with 'INTEGRITY FAILED: INT-K3-NULL', and 1111.111 is
    absent from the output (S2B:553-554)."""
    sr = repo_of(fx, "A4")
    r = e_run(fx, sr, ["--run"])
    assert r.rc == 3 and "INTEGRITY FAILED: INT-K3-NULL c2/gates/K3.json result.value_meV" in r.result_text
    assert "1111.1" not in r.result_text


@case("A10", "A", mutants=(
        ("calc_unchecked", lambda fx: patched(ee(), "calc_check", lambda cd, check: None)),))
def case_a10(fx):
    """With sys.modules['mace'] planted, the run exits 3 with INT-CALC-LOAD; the plant is removed afterwards."""
    sr = repo_of(fx, "C1a")
    import types
    sys.modules["mace"] = types.ModuleType("mace")
    try:
        r = e_run(fx, sr, ["--run"])
    finally:
        del sys.modules["mace"]
    assert r.rc == 3 and "INTEGRITY FAILED: INT-CALC-LOAD" in r.result_text and "mace" not in sys.modules


# ---------------------------------------------------------------- group D: discipline (spec 18 D; RF-1, -3, -6, -8)
def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)


def note(sr, rel, text, msg=None, date=None):
    """Commit a note (repository-relative path) in a throwaway repository; returns the commit."""
    write_text(os.path.join(sr.repo, rel), text)
    return commit(sr.repo, msg or f"note {rel}", rel, date=date)


@contextlib.contextmanager
def multi(*cms):
    with contextlib.ExitStack() as st:
        for c in cms:
            st.enter_context(c)
        yield


@case("D1", "D", mutants=(
        ("no_clean_check", lambda fx: patched(ee().Git, "porcelain", lambda self, *p: "")),))
def case_d1(fx):
    """A dirty tree (an untracked file) gives exit 2, and no file is written (S2B:521)."""
    sr = repo_of(fx, "C1a")
    p = os.path.join(sr.root, "untracked_note.txt")
    write_text(p, "x\n")
    try:
        r = e_run(fx, sr, ["--run"])
    finally:
        os.remove(p)
    assert r.rc == 2 and not r.written and not os.path.exists(os.path.join(sr.root, "s2b", "E_output.txt"))
    assert git(sr.repo, "config", "--get", "maintenance.auto").strip() == "false"     # fix round 2 (GIT_ENV)


S2R = "results/objective2/s2"
E_READ_REL = f"{S2R}/s2b/e_read.py"
E_EVAL_REL = f"{S2R}/s2b/e_eval.py"


def _variant(name, old, new):
    with open(os.path.join(HERE, name)) as fh:
        t = fh.read()
    assert t.count(old) == 1, (name, old)
    return t.replace(old, new)


def buggy_e_read():
    """The code of an earlier attempt for D2: the final-position tolerance 1e-3 A (B3 fails on it)."""
    return _variant("e_read.py", "FINALPOS_TOL_A, CELL_TOL_A, MIC_TOL_A = 1e-6, 1e-9, 1e-9",
                    "FINALPOS_TOL_A, CELL_TOL_A, MIC_TOL_A = 1e-3, 1e-9, 1e-9")


def buggy_e_eval():
    """The code of an earlier attempt for D7: the FR-2 bound 49 meV (C5 fails on it)."""
    return _variant("e_eval.py", "TOL_MEV, STEP0_MEV, FR2_MAX_MEV = 1e-6, 0.5, 50.0",
                    "TOL_MEV, STEP0_MEV, FR2_MAX_MEV = 1e-6, 0.5, 49.0")


E_SELFTEST_REL = f"{S2R}/s2b/e_selftest.py"


def selftest_without_b3():
    """The self-test of an earlier attempt for D2 (fix round 2, M27): case B3 not yet registered (it comes with the
    fix), so that the rerun cause can run on the earlier code only through the fixed self-test copied into the old
    tree (spec 16)."""
    return _variant("e_selftest.py", '@case("B3", ' + '"B", mutants=(', '@case("B3_before_fix", "B", mutants=(')


AMEND = f"{S2R}/E_AMENDMENT_1.md"


def amend_text(sr, days=0):
    """A dated amendment (spec 7): its ISO date is the S2B_LAST commit's date plus days, so that the cases hold on any
    day (fix round 1: the fixed date 2026-11-21 failed D2 and D4 from the day after it)."""
    d = datetime.datetime.fromisoformat(git(sr.repo, "show", "-s", "--format=%cI", sr.commits["last"]).strip()).date()
    return (f"# E amendment 1 (synthetic)\n\n{(d + datetime.timedelta(days=days)).isoformat()}: a fix of E's code; "
            f"no rule changes.\n")


def _diff_quiet_e_changed(orig):
    def f(self, a, b, paths):
        return False if list(paths) == list(ee().E_FILES) else orig(self, a, b, paths)
    return f


@case("D2", "D", mutants=(
        # the old-code run of the rerun cause not checked (a cause that passes on the old code accepted)
        ("old_code_unchecked", lambda fx: patched(ee().Run, "run_case", lambda self, code_dir, case: (
            (0, "ok") if code_dir == HERE else (1, "AssertionError")))),
        # fix round 1: a rerun with E's code unchanged since the earlier attempt accepted
        ("unchanged_code_accepted", lambda fx: patched(ee().Git, "diff_quiet", _diff_quiet_e_changed(ee().Git.diff_quiet))),
        # fix round 1: a harness error on the earlier code (no status line) taken as its failure
        ("harness_error_accepted", lambda fx: patched(ee(), "RERUN_FAILS", ee().RERUN_FAILS + ("no status line",)))))
def case_d2(fx):
    """Attempts (spec 16; RF-6, RF-9): E_output.txt present without --rerun-cause gives exit 2; with E's code
    unchanged since attempt 1 every cause is refused (fix round 1); after a fix, a cause that passes on the old code
    (A2) is refused, an unknown case too; a cause that fails on the old code and passes on the new (B3; both run in a
    subprocess python -B -I with the self-test refusals) writes E_output_attempt2.txt with the dated amendment
    recorded; both files present gives exit 2, also with --item7-amendment when attempt 2 has no FALLBACK; a fourth
    attempt is always refused. Fix round 1 (M1): a cause that builds a synthetic repository (D1) runs in the old tree
    as here (it holds scripts/46-50), so with E changed only by a comment it passes there and is refused (before, it
    'failed' there with FileNotFoundError and was accepted); a cause whose old-code run is a harness error (no status
    line: E's files absent at the earlier HEAD) is refused. Fix round 2 (M27): the earlier attempt's self-test lacks
    case B3, which the fix adds; the cause B3 is accepted only because the fixed self-test is run on the old tree."""
    sr = synth_repo(fx, "d2", SCEN["C1a"], e_text={E_READ_REL: buggy_e_read(), E_SELFTEST_REL: selftest_without_b3()})
    r1 = e_run(fx, sr, ["--run"], keep=True)
    assert r1.rc == 0, r1.result_text[-600:]
    commit(sr.repo, "E attempt 1 (unedited)")
    r = e_run(fx, sr, ["--run"])
    assert r.rc == 2 and not r.written
    write_text(os.path.join(sr.repo, AMEND), amend_text(sr))
    commit(sr.repo, "a dated amendment, E's code unchanged")
    r = e_run(fx, sr, ["--run", "--rerun-cause", "B3", "--amendment", AMEND])
    assert r.rc == 2 and not r.written and "unchanged since the earlier attempt" in r.result_text, r.result_text[-300:]
    shutil.copyfile(os.path.join(HERE, "e_read.py"), os.path.join(sr.repo, E_READ_REL))
    shutil.copyfile(os.path.join(HERE, "e_selftest.py"), os.path.join(sr.repo, E_SELFTEST_REL))   # with case B3
    commit(sr.repo, "E fix")
    for cause in ("A2", "NOPE"):
        r = e_run(fx, sr, ["--run", "--rerun-cause", cause, "--amendment", AMEND])
        assert r.rc == 2 and not r.written, (cause, r.rc)
    r2 = e_run(fx, sr, ["--run", "--rerun-cause", "B3", "--amendment", AMEND], keep=True)
    assert r2.rc == 0 and "s2b/E_output_attempt2.txt" in r2.files, r2.result_text[-800:]
    t = r2.result_text
    assert "attempt 2 of the one evaluation" in t and "rerun cause: case B3: passes on the current code" in t and \
        f"changed under the amendment {AMEND}" in t and "(exit 1, AssertionError)" in t
    assert "figures/source_data/fig_s2b_e_fk_attempt2.csv" in r2.files
    commit(sr.repo, "E attempt 2 (unedited)")
    for argv in (["--run"], ["--run", "--rerun-cause", "B3", "--amendment", AMEND, "--item7-amendment", AMEND]):
        r = e_run(fx, sr, argv)
        assert r.rc == 2 and not r.written, argv
    write_text(os.path.join(sr.root, "s2b", "E_output_attempt3.txt"), "planted\nE exit code: 0\n")
    commit(sr.repo, "a planted third attempt")
    r = e_run(fx, sr, ["--run", "--rerun-cause", "B3", "--amendment", AMEND, "--item7-amendment", AMEND])
    assert r.rc == 2 and "a fourth attempt is always refused" in r.result_text
    # M1: a case that builds a synthetic repository, with E changed by a comment only
    sn = synth_repo(fx, "d2_harness", SCEN["C1a"])
    assert e_run(fx, sn, ["--run"], keep=True).rc == 0
    commit(sn.repo, "E attempt 1 (unedited)")
    with open(os.path.join(sn.repo, S2R, "s2b", "e_block4.py"), "a") as fh:
        fh.write("\n# a comment (no fix)\n")
    write_text(os.path.join(sn.repo, AMEND), amend_text(sn))
    commit(sn.repo, "E changed by a comment, with a dated amendment")
    r = e_run(fx, sn, ["--run", "--rerun-cause", "D1", "--amendment", AMEND])
    assert r.rc == 2 and not r.written and "passes on the code of the earlier attempt" in r.result_text, \
        r.result_text[-300:]
    # M1: a harness error on the earlier code (attempt 1 planted at the C2 commit, where E's files are absent)
    sh = synth_repo(fx, "d2_harness_err", SCEN["C1a"])
    note(sh, f"{S2R}/s2b/E_output.txt", f"S2b E, attempt 1 of the one evaluation (S2B_PLAN.md §7); run at "
         f"2026-11-20T00:00:00Z; HEAD {sh.commits['c2']}; mode evaluation\n\nFAILED: stage block 3: RuntimeError\n\n"
         f"END\nE exit code: 3\n", msg="E attempt 1 (planted: failed before output)")
    note(sh, AMEND, amend_text(sh))
    r = e_run(fx, sh, ["--run", "--rerun-cause", "A5", "--amendment", AMEND])
    assert r.rc == 2 and not r.written and "not with a failure of the case" in r.result_text and \
        "FALLBACK" not in r.result_text, r.result_text[-300:]


@case("D3", "D", mutants=(
        ("no_exit_lock", lambda fx: patched(er, "assert_no_c3", _no_exit_c3(er.assert_no_c3))),))
def case_d3(fx):
    """The c3 lock (RF-2): roots holding c3/, C3/, c3_x/, c3.tar.gz, c3_notrun/ or a dangling c3, c3_x or C3-old
    symlink (fix round 1) give exit 2 before any archive read; c3b/ and C3_OPERATIONS.md are allowed; a private root holding c3/ is refused; a c3/
    planted between phase 1 and the exit audit gives INT-ROOT (exit 3)."""
    sr = repo_of(fx, "C1a")
    with open(os.path.join(sr.repo, ".git", "info", "exclude"), "a") as fh:
        fh.write("results/objective2/s2/c3\nresults/objective2/s2/c3.tar.gz\nresults/objective2/s2/c3_x\n"
                 "results/objective2/s2/C3-old\nresults/objective2/s2/c3.tar\n")
    for kind, name in (("dir", "c3"), ("dir", "C3"), ("dir", "c3_x"), ("file", "c3.tar.gz"), ("dir", "c3_notrun"),
                       ("link", "c3"), ("link", "c3_x"), ("link", "C3-old"),     # fix round 1: dangling c3_x, C3-old
                       ("file", "c3.tar")):                                      # fix round 2 (G01)
        p = os.path.join(sr.root, name)
        if kind == "dir":
            os.makedirs(p)
        elif kind == "file":
            write_text(p, "x")
        else:
            os.symlink(os.path.join(sr.root, "nowhere"), p)
        try:
            r = e_run(fx, sr, ["--run"])
        finally:
            (os.rmdir if kind == "dir" else os.remove)(p)
        assert r.rc == 2 and not r.written and "c3 entry" in r.result_text, (name, r.rc)
        assert not [e for e in r.au.log.values() if e["rel"].split("/")[0] in ("c1", "c2", "fr")], name
    priv = os.path.join(os.path.dirname(sr.repo), "private")
    os.makedirs(os.path.join(priv, "c3"), exist_ok=True)
    r = e_run(fx, sr, ["--run"], private_root=priv)
    assert r.rc == 2 and "c3 entry" in r.result_text
    os.makedirs(os.path.join(sr.root, "c3b"))
    try:
        def plant(run):
            os.makedirs(os.path.join(run.root, "c3"))
        r = e_run(fx, sr, ["--run"], hooks={"before_exit_audit": plant})
    finally:
        os.rmdir(os.path.join(sr.root, "c3b"))
        if os.path.isdir(os.path.join(sr.root, "c3")):
            os.rmdir(os.path.join(sr.root, "c3"))
    assert r.rc == 3 and "INTEGRITY FAILED: INT-ROOT c3 c3 entry" in r.result_text, r.result_text[-300:]


def _no_exit_c3(orig):
    def f(L, *, at="start"):
        return True if at == "exit" else orig(L, at=at)
    return f


@case("D4", "D", mutants=(
        ("diff_ignored", lambda fx: patched(ee().Git, "diff_quiet", lambda self, a, b, paths: True)),
        ("rf3_unchecked", lambda fx: patched(ee().Git, "exists", lambda self, c, path: True))))
def case_d4(fx):
    """The commits check (spec 7; RF-3), in a real throwaway git repository: scripts/49 changed between S2B_LAST
    and HEAD without an amendment gives exit 2; an amendment under scripts/, an undated one and one not changed
    after S2B_LAST are refused; a valid dated amendment lets the run go ahead and is recorded; E's files missing at
    the fr start_commit give exit 2 even with the amendment (no amendment route); campaign_c2 commit != C2_COMMIT
    gives INT-COMMITS (exit 3). Fix round 1: the amendment is dated from the S2B_LAST commit (one dated on that day
    is accepted, one dated the day before is refused), and a commit_history entry after start_commit without
    e_read.py gives exit 2 (RF-3). Fix round 2: an amendment dated on the S2B_LAST day but committed at S2B_LAST
    itself (not changed after it) is refused for that reason (M22; C3_OPERATIONS.md had no date and was refused for
    the date first); on a run where nothing changed, a named undated amendment is still refused (M25)."""
    AT_F = f"{S2R}/E_AMEND_AT_F.md"
    sr = synth_repo(fx, "d4", SCEN["C1a"], extra={AT_F: f"# E amendment (synthetic)\n\n"
                                                         f"{(datetime.date.today() + datetime.timedelta(1))}: "
                                                         f"committed with the fr campaign commit.\n"})
    p49 = os.path.join(sr.repo, "scripts", "49_s2_gates.py")
    with open(p49, "a") as fh:
        fh.write("\n# a planted change after the S2b campaign commit\n")
    commit(sr.repo, "scripts/49 changed")
    r = e_run(fx, sr, ["--run"])
    assert r.rc == 2 and "without --amendment" in r.result_text
    note(sr, "scripts/E_AMEND.md", amend_text(sr))
    note(sr, f"{S2R}/E_AMEND_UNDATED.md", "# an amendment without a date\n")
    note(sr, f"{S2R}/E_AMEND_EARLY.md", amend_text(sr, days=-1))      # dated the day before S2B_LAST
    for bad, why in (("scripts/E_AMEND.md", "lies under scripts/"),
                     (f"{S2R}/E_AMEND_UNDATED.md", "carries no ISO date"),
                     (f"{S2R}/E_AMEND_EARLY.md", "carries no ISO date"), (f"{S2R}/C3_OPERATIONS.md", ""),
                     (AT_F, "was not added or changed after")):
        r = e_run(fx, sr, ["--run", "--amendment", bad])
        assert r.rc == 2 and not r.written and why in r.result_text, (bad, r.result_text[-300:])
    note(sr, AMEND, amend_text(sr))                       # dated on the S2B_LAST date: 'on or after' holds
    r = e_run(fx, sr, ["--run", "--amendment", AMEND])
    assert r.rc == 0 and f"changed under the amendment {AMEND}" in r.result_text, r.result_text[-500:]
    fj = os.path.join(sr.root, "fr", "campaign.json")
    with open(fj) as fh:
        cj = json.load(fh)
    cj["start_commit"] = sr.commits["c2"]
    dump(fj, cj)
    commit(sr.repo, "fr start_commit without E's files")
    r = e_run(fx, sr, ["--run", "--amendment", AMEND])
    assert r.rc == 2 and "RF-3" in r.result_text
    sr2 = repo_of(fx, "d4_c2commit", {"fr": SCEN["C1a"]["fr"], "c2_commit": "9" * 40})
    r = e_run(fx, sr2, ["--run"])
    assert r.rc == 3 and "INTEGRITY FAILED: INT-COMMITS c2/campaign.json commit" in r.result_text
    note(sr2, f"{S2R}/E_AMEND_UNDATED.md", "# an amendment without a date\n")   # fix round 2 (M25): nothing
    r = e_run(fx, sr2, ["--run", "--amendment", f"{S2R}/E_AMEND_UNDATED.md"])  # changed, the note still checked
    assert r.rc == 2 and not r.written and "carries no ISO date" in r.result_text, r.result_text[-300:]
    # fix round 1 (RF-3): a commit_history entry after start_commit (a mid-campaign commit) without e_read.py;
    # start_commit and commit hold every E file
    sh = synth_repo(fx, "d4_hist", SCEN["C1a"])
    git(sh.repo, "rm", "-q", E_READ_REL)
    X = commit(sh.repo, "a mid-campaign commit without e_read.py (synthetic)")
    shutil.copyfile(os.path.join(HERE, "e_read.py"), os.path.join(sh.repo, E_READ_REL))
    Y = commit(sh.repo, "e_read.py back (synthetic)")
    fj, sj = os.path.join(sh.root, "fr", "campaign.json"), os.path.join(sh.root, "fr", "state_end.json")
    with open(fj) as fh:
        cj = json.load(fh)
    cj["commit_history"] += [{"from": sh.commits["F"], "to": X, "note": "n", "time": "t", "via": "fr/STEP0_FIX",
                              "campaign": "fr"}, {"from": X, "to": Y, "note": "n", "time": "t", "via": "x",
                                                  "campaign": "fr"}]
    cj["commit"] = Y
    dump(fj, cj)
    with open(sj) as fh:
        st = json.load(fh)
    st["campaign_commit"] = {"fr": Y}
    dump(sj, st)
    commit(sh.repo, "fr archive with the history (synthetic)")
    r = e_run(fx, sh, ["--run"])
    assert r.rc == 2 and not r.written and "RF-3" in r.result_text and X[:12] in r.result_text, r.result_text[-300:]


@case("D5", "D", mutants=(
        ("stub_bypassed", lambda fx: patched(_sibling("e_block4"), "BLOCK4_IMPLEMENTED", True)),))
def case_d5(fx):
    """Preconditions (S2B:515-518; spec 6.1): fr running is refused; stopped without a note is refused; FR pass
    with BLOCK4_IMPLEMENTED = False is refused (exit 2, nothing written); an fr_outcome inconsistent with
    decision.FR gives INT-ROUTE (exit 3)."""
    for name, sc, why in (("d5_running", {"fr": {"status": "running", "cells": {"D": {"status": "pending"}}}},
                           "fr is running"), ("C1j", None, "needs --stop-note"), ("pass", None, "block 4 is a stub")):
        r = e_run(fx, repo_of(fx, name, sc), ["--run"])
        assert r.rc == 2 and not r.written and why in r.result_text, (name, r.rc, r.result_text[-300:])
    r = e_run(fx, repo_of(fx, "d5_route", {"fr": {**SCEN["C1a"]["fr"], "fr_outcome": "fail (FR-2)"}}), ["--run"])
    assert r.rc == 3 and "INTEGRITY FAILED: INT-ROUTE" in r.result_text


def _post_json(rel, fn):
    def post(root, man):
        p = os.path.join(root, rel)
        with open(p) as fh:
            d = json.load(fh)
        fn(d)
        dump(p, d)
    return post


def _post_rm(rel):
    def post(root, man):
        os.remove(os.path.join(root, rel))
    return post


def _post_rename(a, b):
    def post(root, man):
        os.rename(os.path.join(root, a), os.path.join(root, b))
    return post


def _fake_log(rel, via=None):
    def hook(run):
        run.au.log["/nonexistent/" + rel] = {"rel": rel, "base": "root", "sha256": "0" * 64, "block": 3,
                                             "hinge": False, "n": 1, "via": via}
    return hook


def _fake_member(rel, name):
    def hook(run):                                        # a hinge member read outside hinge mode (planted log entry)
        run.au.members.append((rel, name, 3, False))
    return hook


def _touch(rel):
    def hook(run):                                        # a concurrent change, written outside E's audit
        run.au.stop()
        try:
            with open(os.path.join(run.root, rel), "a") as fh:
                fh.write(" ")
        finally:
            run.au.start()
    return hook


def _reads_plant(run):
    run.ex.q47.READS["F"] += 1


def _calc_plant(run):
    import types
    sys.modules["torch"] = types.ModuleType("torch")


D6_PLANTS = (   # (id, how, expected 'INTEGRITY FAILED: ...' prefix)
    ("INT-K3-NULL", ("repo", "A4", None), "INT-K3-NULL c2/gates/K3.json result.value_meV"),
    ("INT-K3-SHA", ("repo", "d6_k3sha", _post_json("c2/gates_applied/gate_K3.json",
                                                   lambda d: d.update(gate_file_sha256="0" * 64))),
     "INT-K3-SHA c2/gates/K3.json gate_file_sha256"),
    ("INT-FR-SHA", ("repo", "d6_frsha", _post_json("fr/gates_applied/gate_FR.json",
                                                   lambda d: d.update(gate_file_sha256="0" * 64))),
     "INT-FR-SHA fr/gates/FR.json gate_file_sha256"),
    ("INT-FR-DEC", ("repo", "d6_frdec", _post_json("fr/state_end.json", lambda d: d["FR"].update(cell="x"))),
     "INT-FR-DEC fr/state_end.json FR"),
    ("INT-STRUCT", ("repo", "d6_struct", _post_rm("fr/state_end.json")),
     "INT-STRUCT fr/state_end.json required file absent (RF-12)"),
    ("INT-FINALSHA", ("repo", "d6_finalsha", _post_json("c2/raw/s2r_m30_hostB76.a2.json",
                                                        lambda d: d["final_geometry"].update(sha256="f" * 64))),
     "INT-FINALSHA c2/structures.tar.gz:a2/s2r_m30_hostB76/s2r_m30_hostB76.final.extxyz final_geometry.sha256"),
    ("INT-NCFG", ("repo", "d6_ncfg", _post_json("fr/raw/s2r_m30_hostA188.a2.json", lambda d: d.update(n_config=60))),
     "INT-NCFG fr/raw/s2r_m30_hostA188.a2.json n_config"),
    ("INT-KLAST", ("repo", "d6_klast", _post_json("fr/raw/s2r_m30_hostA188.a2.json", lambda d: d.update(k_last=59))),
     "INT-KLAST fr/raw/s2r_m30_hostA188.a2.json k_last (accepted_converged)"),
    ("INT-FINALK", ("repo", "d6_finalk", _post_json("fr/raw/s2r_m30_hostA188.a2.json",
                                                    lambda d: d["final_geometry"].update(k=59))),
     "INT-FINALK fr/raw/s2r_m30_hostA188.a2.json final_geometry.k"),
    ("INT-PARTS", ("repo", "d6_parts", _post_rename("fr/raw/s2r_m30_hostA188.p1.out.gz",
                                                    "fr/raw/s2r_m30_hostA188.p2.out.gz")),
     "INT-PARTS fr/raw/s2r_m30_hostA188.p<n>.out.gz part numbers 1..N"),
    ("INT-FINALPOS", ("patch", er, "FINALPOS_TOL_A", -1.0), "INT-FINALPOS c2/structures.tar.gz:a2/s2r_m30_hostB76"),
    ("INT-CELL", ("patch", er, "CELL_TOL_A", -1.0), "INT-CELL c2/structures.tar.gz:a2/s2r_m30_hostB76"),
    ("INT-IMPORT", ("patch", eg, "FAR4", {**eg.FAR4, "m05": {**eg.FAR4["m05"], "B": (76, 172, 24, 148)}}),
     "INT-IMPORT 8bff03e FAR4_TABLE"),
    ("INT-READS", ("hook", _reads_plant), "INT-READS exit READS changed between calls"),
    ("INT-HINGE-CLOSED", ("hook", _fake_log("c2/raw/s2r_m30_VB136.p1.out.gz")),
     "INT-HINGE-CLOSED c2/raw/s2r_m30_VB136.p1.out.gz hinge output"),
    ("INT-PB136-RAW", ("hook", _fake_log("c1/raw/s2_m30_VB136.out.gz")),
     "INT-PB136-RAW c1/raw/s2_m30_VB136.out.gz opened outside block 5"),
    ("INT-PB136-REC", ("hook", lambda run: run.c1.log.append(("s2_m30_VB136", False, 3))),
     "INT-PB136-REC c1/records/s2_m30_VB136.json blind=False outside block 5"),
    ("INT-SHA-STABLE", ("hook", _touch("c1/regions/m30_A188.json")),
     "INT-SHA-STABLE c1/regions/m30_A188.json sha256 changed since first open"),
    ("INT-CALC-EXIT", ("hook", _calc_plant), "INT-CALC-EXIT sys.modules CALC_ENGINES"),
    ("INT-K3-DEC", ("repo", "d6_k3dec", _post_json("c2/gates_applied/gate_K3.gate.json",
                                                   lambda d: d["result"].update(checks_failed=["x"]))),
     "INT-K3-DEC c2/gates/K3.json result.checks_failed"),
    ("INT-K3-DEC", ("repo", "d6_k3mk", _post_json("c2/gates_applied/gate_K3.json",                 # fix round 1
                                                  lambda d: d["decision"].update(K3="pass"))),
     "INT-K3-DEC c2/gates/K3.json decision.K3"),
    ("INT-HINGE-CLOSED", ("hook", _fake_member("c2/structures.tar.gz", "a2/s2r_m30_VB136/s2r_m30_VB136.final.extxyz")),
     "INT-HINGE-CLOSED c2/structures.tar.gz:a2/s2r_m30_VB136/s2r_m30_VB136.final.extxyz hinge member"),
    ("INT-GUARD", ("patchx", lambda fx: patched(eg, "TABLE", _table_r2())), "INT-GUARD far/a2_far R2"),
    ("INT-PARSE", ("patchx", lambda fx: patched(fx.ex.q47, "parse_relax", _raise_s2error(fx.ex.q47))),
     "INT-PARSE s2r_m30_hostB76 stage parse_relax S2Error"),
    ("INT-SP", ("patchx", lambda fx: patched(fx.ex.q47, "sp_status", lambda d, lab, **kw: {"status": "missing"})),
     "INT-SP c1/raw/"),
    # fix round 2: the tripwires no case planted before (M53, M55, M54, M47, M48, G09)
    ("INT-K3-DEC", ("repo", "d6_k3both", lambda root, man: _post_k3_cf_both(root, man)),
     "INT-K3-DEC c2/gates/K3.json result.checks_failed"),
    ("INT-STRUCT", ("patchx", lambda fx: patched(ee(), "TAIL_K", {**ee().TAIL_K, "s2r_m30_hostB76": 127})),
     "INT-STRUCT c2/raw/s2r_m30_hostB76.a2.json TAIL_K = k_last - 36"),
    ("INT-C1-CENSUS", ("repox", "d6_census", lambda root, man: _post_census_vx138(root, man),
                       lambda fx: multi(patched(eg.SP_SETS, "q0", eg.SP_SETS["q0"] + ("s2_m30_VX138",)),
                                        patched(eg, "N_SP", eg.N_SP + 1))),
     "INT-C1-CENSUS c1/raw s2_m30_VX138 (Cl138 q = +1 not formable)"),
    ("INT-READS", ("hook", lambda run: run.ctx.reads.labels["sp"].__setitem__("s2_m30_VB136", 3)),
     "INT-READS s2_m30_VB136 SP label outside the blocks run"),
    ("INT-READS", ("hook", lambda run: run.ctx.reads.labels["a2"].__setitem__("s2r_m30_VB136", 1)),
     "INT-READS s2r_m30_VB136 A2 label outside the blocks run"),
    ("INT-HINGE-CLOSED", ("hook", lambda run: _fake_log("c2/raw/s2r_m30_VB136.a2.json", via="a2_far")(run)),
     "INT-HINGE-CLOSED c2/raw/s2r_m30_VB136.a2.json hinge output"),
)


def _post_k3_cf_both(root, man):
    """Both K3 files with the same checks_failed, other than C2_RESULT.md's (the marker's sha follows)."""
    p = os.path.join(root, "c2", "gates", "K3.json")
    with open(p) as fh:
        g = json.load(fh)
    g["result"]["checks_failed"] = ["x"]
    sha = dump(p, g)
    dump(os.path.join(root, "c2", "gates_applied", "gate_K3.gate.json"), g)
    _post_json("c2/gates_applied/gate_K3.json", lambda d: d.update(gate_file_sha256=sha))(root, man)


def _post_census_vx138(root, man):
    """A single-point output s2_m30_VX138 (the q = +1 V of Cl138, not formable from C1); with SP_SETS and N_SP patched
    to hold it, only the block-3 census rule can refuse it (M54; before the rule, the q = +1 row would form)."""
    raw = os.path.join(root, "c1", "raw")
    shutil.copyfile(os.path.join(raw, "s2_m30_VX138_q0.out.gz"), os.path.join(raw, "s2_m30_VX138.out.gz"))


def _table_r2():
    t = copy.deepcopy(eg.TABLE)
    t["far"]["a2_far"]["get"] = t["far"]["a2_far"]["get"] + ("end_rule.dF_200_180_meV",)
    return t


def _raise_s2error(q47):
    def f(*a, **kw):
        raise q47.S2Error("planted 1111.111 meV")
    return f
PLANTED_NUMBERS = ("1111.1", "9876.5", "7654.3", "5555.5", "4444.4", "3333.3", "2222.2", " meV", " eV")


@case("D6", "D", mutants=(
        # the failure line without its key path
        ("key_path_lost", lambda fx: patched(eg.EIntegrity, "line", lambda self: f"INTEGRITY FAILED: {self.check}")),))
def case_d6(fx):
    """Every integrity check planted in turn (in the archive, the code or the run) exits 3; the failure report holds
    'INTEGRITY FAILED: <id> <file or tar:member> <key path>' and none of the planted numbers, no meV or eV value
    (S2B:603-604); INT-SHA against the archive commit after a committed change of a c1 file. Fix round 1: the K3
    marker's decision.K3 (INT-K3-DEC), a hinge tar member read outside hinge mode (INT-HINGE-CLOSED) and a committed
    change of a c2 file E never opens (INT-SHA, 'archive changed')."""
    base = repo_of(fx, "C1a")
    for cid, how, want in D6_PLANTS:
        sr, kw, cm = base, {}, contextlib.nullcontext()
        if how[0] == "repo":
            sr = repo_of(fx, how[1], {"fr": SCEN["C1a"]["fr"]}, post=how[2]) if how[2] else repo_of(fx, how[1])
        elif how[0] == "repox":                                  # fix round 2: a planted archive and a patch
            sr, cm = repo_of(fx, how[1], {"fr": SCEN["C1a"]["fr"]}, post=how[2]), how[3](fx)
        elif how[0] == "patch":
            cm = patched(how[1], how[2], how[3])
        elif how[0] == "patchx":
            cm = how[1](fx)
        else:
            kw = {"hooks": {"before_exit_audit": how[1]}}
        try:
            with cm:
                r = e_run(fx, sr, ["--run"], **kw)
        finally:
            sys.modules.pop("torch", None)
            git(sr.repo, "checkout", "--", ".")
        t = r.result_text
        assert r.rc == 3 and f"INTEGRITY FAILED: {want}" in t, (cid, r.rc, t[-400:])
        assert not any(x in t for x in PLANTED_NUMBERS), cid
        assert list(r.files) == ["s2b/E_output.txt"] and t.rstrip("\n").endswith("END\nE exit code: 3"), cid
    sr = synth_repo(fx, "d6_sha", SCEN["C1a"])
    with open(os.path.join(sr.root, "c1", "regions", "m30_B76.json"), "a") as fh:
        fh.write("\n")
    commit(sr.repo, "a c1 file changed after its archive commit")
    r = e_run(fx, sr, ["--run"])
    assert r.rc == 3 and "INTEGRITY FAILED: INT-SHA c1/regions/m30_B76.json" in r.result_text, r.result_text[-300:]
    sr = synth_repo(fx, "d6_sha_unopened", SCEN["C1a"])   # fix round 1: a file E never opens, changed after its
    with open(os.path.join(sr.root, "c2", "ledger.json"), "a") as fh:     # archive commit (the final diff of INT-SHA)
        fh.write("\n")
    commit(sr.repo, "an unopened c2 file changed after its archive commit")
    r = e_run(fx, sr, ["--run"])
    assert r.rc == 3 and "INTEGRITY FAILED: INT-SHA c2/ archive changed since its archive commit" in r.result_text, \
        r.result_text[-300:]
    # fix round 2 (M24): fr/state_end.json campaign_commit.fr other than fr/campaign.json commit (planted after the
    # fr archive commit, which synth_repo writes)
    sc = synth_repo(fx, "d6_ccfr", SCEN["C1a"])
    _post_json("fr/state_end.json", lambda d: d["campaign_commit"].update(fr="0" * 40))(sc.root, sc.man)
    commit(sc.repo, "state_end campaign_commit.fr planted")
    r = e_run(fx, sc, ["--run"])
    assert r.rc == 3 and "INTEGRITY FAILED: INT-COMMITS fr/state_end.json campaign_commit.fr" in r.result_text, \
        r.result_text[-300:]
    # fix round 2 (M49): a file E lists and reads that has no blob at its archive commit (ignored, untracked)
    with open(os.path.join(base.repo, ".git", "info", "exclude"), "a") as fh:
        fh.write("results/objective2/s2/c1/pairs/m30_Cs188p9.json\n")
    p = os.path.join(base.root, "c1", "pairs", "m30_Cs188p9.json")
    dump(p, {"schema": "s2-pair-1", "member": "m30", "token": "Cs", "site": 188, "start": "p9", "status": "built"})
    try:
        r = e_run(fx, base, ["--run"])
    finally:
        os.remove(p)
    assert r.rc == 3 and "INTEGRITY FAILED: INT-SHA c1/pairs/m30_Cs188p9.json git blob of the archive reference" in \
        r.result_text, r.result_text[-300:]


def _fail_block3(self, o, *, quiet=False):
    raise RuntimeError("planted failure before output")


@case("D7", "D", mutants=(
        ("no_fallback", lambda fx: patched(ee().Run, "fallback", lambda self: [])),
        ("no_30_days", lambda fx: patched(ee(), "within_30_days", lambda a, b: True))))
def case_d7(fx):
    """The item-7 fallback and the third attempt (spec 16; RF-6, RF-15, OP-21): attempt 1 fails before output
    (exit 3); after a fix of E's code (the FR-2 bound; rerun cause C5, which fails on the earlier code) attempt 2,
    with a planted INT-FINALPOS, prints the FALLBACK block with both K3 .far leaves and the FR-2 leaves (here 'none
    recorded (FR-1 failed)'), each labelled, 'not read: E failed' and the 'BLOCK 5 ... not opened' line, no .hinge;
    after a second fix (the final-position tolerance; cause B3) an item-7 amendment committed 40 days later, or one
    that comes with a change of scripts/49 (RF-15), is refused; a valid one writes E_output_attempt3.txt; a fourth is
    refused. RF-6 negative: attempt 1 exit 0 and attempt 2 exit 3 give no FALLBACK, and attempt 3 is refused. (Fix
    round 1: each rerun follows a committed change of E's code, and the amendment is dated from S2B_LAST.)"""
    sr = synth_repo(fx, "d7", SCEN["C1a"], e_text={E_EVAL_REL: buggy_e_eval(), E_READ_REL: buggy_e_read()})
    with patched(ee().Run, "block3", _fail_block3):
        r1 = e_run(fx, sr, ["--run"], keep=True)
    assert r1.rc == 3 and "FAILED: stage block 3: RuntimeError" in r1.result_text and "FALLBACK" not in r1.result_text
    commit(sr.repo, "E attempt 1 (failed before output)")
    shutil.copyfile(os.path.join(HERE, "e_eval.py"), os.path.join(sr.repo, E_EVAL_REL))
    write_text(os.path.join(sr.repo, AMEND), amend_text(sr))
    commit(sr.repo, "E fix (the FR-2 bound) and its dated amendment")
    with patched(er, "FINALPOS_TOL_A", -1.0):
        r2 = e_run(fx, sr, ["--run", "--rerun-cause", "C5", "--amendment", AMEND], keep=True)
    t = r2.result_text
    assert r2.rc == 3 and "INTEGRITY FAILED: INT-FINALPOS" in t and "FALLBACK (S2B §7, item 7): E failed twice." in t, \
        t[-600:]
    lab = ee().L["L_FALLBACK"]
    for f in ("c2/gates/K3.json", "c2/gates_applied/gate_K3.gate.json"):
        far = "%.2f" % sr.man["k3"]["far"]
        assert f"  {f} result.Eb_A2_meV.far = {far} meV -- {lab}" in t, f
    assert f"fr/gates/FR.json result.FR2: none recorded (FR-1 failed) -- {lab}" in t and "not read: E failed" in t
    assert ".hinge" not in t and "BLOCK 5. Hinge block: not opened" in t
    a2 = commit(sr.repo, "E attempt 2 (failed before output)")
    I7 = f"{S2R}/E_ITEM7_AMENDMENT.md"
    i7 = "# item-7 amendment (synthetic)\n\n2026-11-25: E's code only.\n"
    late = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=40)) \
        .strftime("%Y-%m-%dT%H:%M:%S+00:00")
    argv = ["--run", "--rerun-cause", "B3", "--amendment", AMEND, "--item7-amendment", I7]

    def fix_e_read():
        shutil.copyfile(os.path.join(HERE, "e_read.py"), os.path.join(sr.repo, E_READ_REL))
        commit(sr.repo, "E fix (the final-position tolerance)")
    fix_e_read()
    note(sr, I7, i7, date=late)
    r = e_run(fx, sr, argv)
    assert r.rc == 2 and "30 days" in r.result_text, r.result_text[-300:]
    git(sr.repo, "reset", "-q", "--hard", a2)
    with open(os.path.join(sr.repo, "scripts", "49_s2_gates.py"), "a") as fh:
        fh.write("\n# planted\n")
    commit(sr.repo, "scripts/49 changed after attempt 2", "scripts")
    fix_e_read()
    note(sr, I7, i7)
    r = e_run(fx, sr, argv)
    assert r.rc == 2 and "RF-15" in r.result_text, r.result_text[-300:]
    git(sr.repo, "reset", "-q", "--hard", a2)
    fix_e_read()
    d_a2 = datetime.datetime.fromisoformat(git(sr.repo, "show", "-s", "--format=%cI", a2).strip())
    note(sr, I7, i7, date=(d_a2 + datetime.timedelta(days=30)).isoformat())   # fix round 2 (M26): day 30 holds
    r3 = e_run(fx, sr, argv, keep=True)
    assert r3.rc == 0 and "s2b/E_output_attempt3.txt" in r3.files and "item-7 amendment" in r3.result_text, \
        r3.result_text[-600:]
    commit(sr.repo, "E attempt 3")
    r = e_run(fx, sr, argv)
    assert r.rc == 2 and "fourth" in r.result_text
    # RF-6 negative
    sn = synth_repo(fx, "d7n", SCEN["C1a"], e_text={E_EVAL_REL: buggy_e_eval()})
    assert e_run(fx, sn, ["--run"], keep=True).rc == 0
    commit(sn.repo, "E attempt 1")
    shutil.copyfile(os.path.join(HERE, "e_eval.py"), os.path.join(sn.repo, E_EVAL_REL))
    write_text(os.path.join(sn.repo, AMEND), amend_text(sn))
    commit(sn.repo, "E fix (the FR-2 bound) and its dated amendment")
    with patched(er, "FINALPOS_TOL_A", -1.0):
        rn = e_run(fx, sn, ["--run", "--rerun-cause", "C5", "--amendment", AMEND], keep=True)
    assert rn.rc == 3 and "FALLBACK" not in rn.result_text and "INT-FINALPOS" in rn.result_text, rn.result_text[-400:]
    commit(sn.repo, "E attempt 2 (failed before output)")
    note(sn, I7, i7)
    r = e_run(fx, sn, argv)
    assert r.rc == 2 and "item-7 route needs attempts 1 and 2 both failed" in r.result_text


def _post_fr_files(root, man):
    """Plant a consistent trio of gate-FR files (FR.json, its copy and marker) that the route says cannot exist."""
    write_applied(root, "fr", "gate:FR", "FR", gate_file("FR", "fr", {}, {}), "FR")


def _post_step0_files(root, man):
    """Plant the fr step-0 files of an evaluation at @2 that cannot have run (V+ never started)."""
    g = gate_file("fr_step0", "fr", {"cells": {"s2_m30_VA188": {"dF_meV": 0.1, "passed": True}}},
                  {"fr_step0": {"attempts": 1, "outcome": "pass", "cell": "s2r_m30_VA188"}})
    write_applied(root, "fr", "gate:fr_step0@2", "fr_step0", g, "fr_step0")


def _post_fr_dec(**changes):
    """Plant decision.FR changes consistently in FR.json, its copy, its marker (with the new gate_file_sha256) and
    fr/state_end.json, so that only INT-ROUTE or the recomputation (XC-FR1-DEC) can see them (fix round 1)."""
    def post(root, man):
        fr = os.path.join(root, "fr")
        p = os.path.join(fr, "gates", "FR.json")
        with open(p) as fh:
            g = json.load(fh)
        g["decision"]["FR"].update(changes)
        sha = dump(p, g)
        dump(os.path.join(fr, "gates_applied", "gate_FR.gate.json"), g)
        mp = os.path.join(fr, "gates_applied", "gate_FR.json")
        with open(mp) as fh:
            m = json.load(fh)
        m["decision"], m["gate_file_sha256"] = g["decision"], sha
        dump(mp, m)
        q = os.path.join(fr, "state_end.json")
        with open(q) as fh:
            d = json.load(fh)
        d["FR"] = dict(g["decision"]["FR"])
        dump(q, d)
    return post


def _post_state_end(root, man):
    dump(os.path.join(root, "fr", "state_end.json"), {"commit": "8" * 40, "campaign_commit": {"fr": "e" * 40}})


def _post_s0_last_only(root, man):
    """Only fr/gates/fr_step0.json, with no applied step-0 evaluation (fix round 2, M11)."""
    g = gate_file("fr_step0", "fr", {"cells": {"s2_m30_VA188": {"dF_meV": 0.1, "passed": True}}},
                  {"fr_step0": {"attempts": 1, "outcome": "pass", "cell": "s2r_m30_VA188"}})
    dump(os.path.join(root, "fr", "gates", "fr_step0.json"), g)


def _post_s0_dec(at, **changes):
    """Fix round 2 (M10): decision.fr_step0 changes planted consistently in the @at copy, gates/fr_step0.json (this
    evaluation's), the marker (its gate_file_sha256 follows) and fr/state_end.json."""
    def post(root, man):
        fr = os.path.join(root, "fr")
        stem = eg.FR_S0_2 if at == "@2" else eg.FR_S0_4
        cp = os.path.join(fr, "gates_applied", f"{stem}.gate.json")
        with open(cp) as fh:
            g = json.load(fh)
        g["decision"]["fr_step0"].update(changes)
        dump(cp, g)
        sha = dump(os.path.join(fr, "gates", "fr_step0.json"), g)
        _post_json(f"fr/gates_applied/{stem}.json", lambda d: d.update(decision=g["decision"],
                                                                       gate_file_sha256=sha))(root, man)
        _post_json("fr/state_end.json", lambda d: d["fr_step0"].update(changes))(root, man)
    return post


@case("D10", "D", mutants=(
        ("no_step0_absence", lambda fx: patched(ee().Run, "rf12_step0", lambda self: None)),
        ("no_route_absences", lambda fx: patched(ee().Run, "route_absences", lambda self, *a: None))))
def case_d10(fx):
    """RF-12, the absences each route implies: an fr/gates/FR.json on the step-0-final route gives INT-ROUTE; fr
    step-0 files although V+_R(A188) never started give INT-STRUCT; an fr/state_end.json on the FR-STOP route gives
    INT-ROUTE (each exit 3). Fix round 1: fr/gates/fr_step0.json removed after @2 ran (a done route) gives
    INT-STRUCT; decision.FR.FR2 True under 'fail (FR-2)', consistent in every file, gives INT-ROUTE. Fix round 2
    (M05-M11), each planted alone with its own message: the @2 copy and marker of a killed VA188 removed (its
    evaluation absent); the @2 marker alone removed (copy and marker); gates/fr_step0.json alone planted (no
    evaluation); the @2 copy's decision changed (INT-FR-DEC against its marker); state_end fr_step0.attempts
    changed; on the step-0-final route the decision 'pass' consistent everywhere (INT-ROUTE). Integration review 1
    (the IX-2 acceptance of fr/STEP0_NO_ERROR, INT-FR-DEC): the gate files at attempts 2; no_error_found absent; the
    state's attempts or cell other than the gate files'; the same plant on a route other than step-0 final (C1a)."""
    a2 = "fr/gates_applied/gate_fr_step0_2"
    for name, sc, post, want, extra in (
            ("d10_m2both", SCEN["C1h"], _posts(_post_rm(f"{a2}.json"), _post_rm(f"{a2}.gate.json")),
             f"INT-STRUCT {a2}.json step-0 evaluation of s2r_m30_VA188 absent (RF-12)", []),           # M05, M07
            ("d10_m2only", SCEN["C1a"], _post_rm(f"{a2}.json"), f"INT-STRUCT {a2} copy and marker (RF-12)", []),
            ("d10_s0only", SCEN["C1d"], _post_s0_last_only,
             "INT-STRUCT fr/gates/fr_step0.json present without a step-0 evaluation (RF-12)", []),     # M11
            ("d10_s0copy", SCEN["C1a"], _post_json(f"{a2}.gate.json", lambda d: d["decision"]["fr_step0"].update(
                outcome="fail_final")), f"INT-FR-DEC {a2}.gate.json decision.fr_step0", []),          # M09
            ("d10_s0att", SCEN["C1a"], _post_json("fr/state_end.json", lambda d: d["fr_step0"].update(attempts=2)),
             "INT-FR-DEC fr/state_end.json fr_step0.attempts", []),                                     # M08
            ("d10_s0final", SCEN["C1h"], _post_s0_dec("@2", outcome="pass"),
             "INT-ROUTE fr/campaign.json fr_outcome step-0 final", []),                                 # M10
            ("d10_fr", SCEN["C1h"], _post_fr_files,
             "INT-ROUTE fr/campaign.json fr_outcome step-0 final", []),
            ("d10_s0", SCEN["C1d"], _post_step0_files, "INT-STRUCT fr/gates_applied/gate_fr_step0_2.json", []),
            ("d10_st", SCEN["C1j"], _post_state_end, "INT-ROUTE fr/state_end.json present although fr stopped", []),
            ("d10_s0last", SCEN["C1a"], _post_rm("fr/gates/fr_step0.json"),             # fix round 1 (R2)
             "INT-STRUCT fr/gates/fr_step0.json required file absent (RF-12)", []),
            ("d10_fr2", SCEN["C1i"], _post_fr_dec(FR2=True),                              # fix round 1 (R1)
             "INT-ROUTE fr/gates/FR.json decision.FR against fr_outcome", []),
            # integration review 1: the IX-2 acceptance of fr/STEP0_NO_ERROR holds only at attempt 1, with
            # no_error_found True, on the step-0-final route, and with the attempts and cell of the gate files
            ("d10_ne_att2", SCEN["C1h"], _post_s0_dec("@2", attempts=2),
             "INT-FR-DEC fr/state_end.json fr_step0.outcome", []),
            ("d10_ne_absent", SCEN["C1h"], _post_json("fr/state_end.json", lambda d: d["fr_step0"].pop(
                "no_error_found")), "INT-FR-DEC fr/state_end.json fr_step0.outcome", []),
            ("d10_ne_satt", SCEN["C1h"], _post_json("fr/state_end.json", lambda d: d["fr_step0"].update(attempts=2)),
             "INT-FR-DEC fr/state_end.json fr_step0.attempts", []),
            ("d10_ne_cell", SCEN["C1h"], _post_json("fr/state_end.json", lambda d: d["fr_step0"].update(
                cell="s2r_m30_Cs188o0_vac")), "INT-FR-DEC fr/state_end.json fr_step0.cell", []),
            ("d10_ne_route", SCEN["C1a"], _posts(_post_s0_dec("@2", outcome="fail_pending_fix"), _post_json(
                "fr/state_end.json", lambda d: d["fr_step0"].update(outcome="fail_final", no_error_found=True))),
             "INT-FR-DEC fr/state_end.json fr_step0.outcome", [])):
        sr = repo_of(fx, name, sc, post=post)
        if name == "d10_st":
            sr, nt = stop_repo(fx, name)
            extra = ["--stop-note", nt]
        r = e_run(fx, sr, ["--run"] + extra)
        assert r.rc == 3 and f"INTEGRITY FAILED: {want}" in r.result_text, (name, r.rc, r.result_text[-300:])


def _hinge_member_moved(orig):
    def f(audit, tar_path, name, *, check="INT-STRUCT"):
        b = orig(audit, tar_path, name, check=check)
        if any(name.startswith(f"a2/{lab}/") for lab in eg.HINGE):
            b = b.replace(b"\n", b"\n ", 1)
        return b
    return f


@case("D8", "D", mutants=(
        ("backstop_moved", lambda fx: patched(ee(), "BACKSTOP", datetime.date(2100, 1, 1))),))
def case_d8(fx):
    """The deferred hinge run (spec 14.3; RF-1): refused without an E output; the backstop before 2027-06-30
    (injected clock) is refused, after it accepted (no later pre-registration yet); an injected clock outside the
    self-test is refused; a prereg NOTE that is on the deny-list (S2B_PLAN.md, S2_PLAN.md, an operations, result or
    diagnostic note, an E output), committed on or after 2027-06-30 (also at 00:00 UTC that day, although its text is
    dated before), added before the attempt-1 commit, without a 'Status: PLAN' line ('Status: PLANNED' is not one),
    not naming E_hinge_output.txt, or given without REC, with a REC older than the NOTE or a REC that does not name
    it, is refused; once a later pre-registration is committed (before any hinge output exists) the backstop is
    refused because it was replaced; a planted hinge final-geometry mismatch exits 3; a valid NOTE and REC write
    E_hinge_output.txt (block 5 in hinge mode, XC-K3HINGE ok); afterwards a rerun without the attempt rule is refused;
    a standing output that opened block 5 refuses the hinge run. (Fix round 1: the RF-1 negatives H1-H7 and the
    backstop refusal checked before any hinge output exists.) Fix round 2: the backstop day 2027-06-30T00:00Z is
    accepted (M15); a later pre-registration added and then renamed replaces the backstop under its new name (the
    scan with --no-renames); a NOTE committed on 2027-06-29 at -05:00 (2027-06-30 in UTC) is refused; refused too
    are a NOTE in the attempt-1 commit itself (M16), a REC in its NOTE's commit (M17), a NOTE under s2b/ (M18) or
    with an E-output name (M19), and a NOTE added, deleted and added again (M21)."""
    utc = datetime.timezone.utc
    after, before = (lambda: datetime.datetime(2027, 7, 1, 12, tzinfo=utc)), \
        (lambda: datetime.datetime(2027, 1, 1, 12, tzinfo=utc))
    sr = synth_repo(fx, "d8", SCEN["C1a"])
    hb = ["--hinge", "--hinge-cause", "backstop"]
    assert e_run(fx, sr, hb, clock=after).rc == 2
    pre = "# A later pre-registration (synthetic)\n\n**Status: PLAN.** Written on 2027-01-10.\n\nIt names " \
          "results/objective2/s2/s2b/E_hinge_output.txt as data.\n"
    EARLY = f"{S2R}/EARLY_PREREG.md"
    note(sr, EARLY, pre)                                    # committed before the attempt-1 commit (H3)
    assert e_run(fx, sr, ["--run"], keep=True).rc == 0
    SAME = f"{S2R}/SAME_PREREG.md"                          # fix round 2 (M16): in the attempt-1 commit itself
    write_text(os.path.join(sr.repo, SAME), pre)
    commit(sr.repo, "E attempt 1 (unedited)")
    assert e_run(fx, sr, hb, clock=before).rc == 2
    r = e_run(fx, sr, hb, clock=after, selftest=False)
    assert r.rc == 2 and "injected clock" in r.result_text
    r = e_run(fx, sr, hb, clock=after)
    assert r.rc == 0 and "s2b/E_hinge_output.txt" in r.files and "hinge cause: backstop" in r.result_text, \
        r.result_text[-800:]
    r = e_run(fx, sr, hb, clock=lambda: datetime.datetime(2027, 6, 30, 0, 0, tzinfo=utc))   # fix round 2 (M15)
    assert r.rc == 0 and "hinge cause: backstop 2027-06-30 (UTC date 2027-06-30)" in r.result_text, \
        r.result_text[-300:]
    # fix round 2 (RF-1): a later pre-registration added and then renamed replaces the backstop under its new name
    OLDN, REN = f"{S2R}/OLDNAME_PREREG.md", f"{S2R}/RENAMED_PREREG.md"
    note(sr, OLDN, pre)
    git(sr.repo, "mv", OLDN, REN)
    commit(sr.repo, "the later pre-registration renamed")
    r = e_run(fx, sr, hb, clock=after)
    assert r.rc == 2 and not r.written and f"a later pre-registration ({REN}) has replaced the backstop" in \
        r.result_text, r.result_text[-300:]
    git(sr.repo, "rm", "-q", REN)
    commit(sr.repo, "the renamed pre-registration removed")
    NOTE, REC = f"{S2R}/NEXT_PREREG.md", f"{S2R}/NEXT_PREREG_EVAL.md"
    LATE, OLD, BOUND = f"{S2R}/LATE_PREREG.md", f"{S2R}/OLD_EVAL.md", f"{S2R}/BOUND_PREREG.md"
    NOSTATUS, PLANNED, NONAME = f"{S2R}/NOSTATUS_PREREG.md", f"{S2R}/PLANNED_PREREG.md", f"{S2R}/NONAME_PREREG.md"
    RECX = f"{S2R}/OTHER_EVAL.md"
    DENY = ("S2B_PLAN.md", "S2_PLAN.md", "X_OPERATIONS.md", "X_RESULT.md", "X_DIAGNOSTIC.md")
    for d in DENY:
        note(sr, f"{S2R}/{d}", pre)
    note(sr, OLD, f"Evaluation of {NOTE} under way (synthetic).\n")
    note(sr, NOSTATUS, pre.replace("**Status: PLAN.**", "**Status: DRAFT.**"))
    note(sr, PLANNED, pre.replace("**Status: PLAN.**", "**Status: PLANNED.**"))
    note(sr, NONAME, pre.replace("results/objective2/s2/s2b/E_hinge_output.txt", "the hinge block"))
    note(sr, NOTE, pre, date="2027-01-10T12:00:00+00:00")
    note(sr, BOUND, pre, date="2027-06-30T00:00:00+00:00")
    note(sr, LATE, pre, date="2027-07-01T12:00:00+00:00")
    TZN = f"{S2R}/TZ_PREREG.md"                              # fix round 2: 2027-06-30T01:00Z, committed at -05:00
    note(sr, TZN, pre, date="2027-06-29T20:00:00-05:00")
    every = " ".join([NOTE, LATE, BOUND, EARLY, NOSTATUS, PLANNED, NONAME, TZN, SAME] + [f"{S2R}/{d}" for d in DENY])
    note(sr, REC, f"2027-07-02: the evaluation of {every} is under way (synthetic).\n", date="2027-07-02T12:00:00+00:00")
    note(sr, RECX, "2027-07-03: an evaluation is under way (synthetic).\n", date="2027-07-03T12:00:00+00:00")
    r = e_run(fx, sr, hb, clock=after)                      # no hinge output exists yet (H5)
    assert r.rc == 2 and not r.written and f"a later pre-registration ({NOTE}) has replaced the backstop" in \
        r.result_text, r.result_text[-300:]
    # fix round 2 (M17-M19, M21): a REC committed with its NOTE; NOTEs under s2b/ and with an E-output name; a NOTE
    # added, deleted and added again (each otherwise valid, and named by REC2)
    NOTE2, REC_W = f"{S2R}/WITH_REC_PREREG.md", f"{S2R}/WITH_REC_EVAL.md"
    write_text(os.path.join(sr.repo, NOTE2), pre)
    write_text(os.path.join(sr.repo, REC_W), f"2027-07-04: the evaluation of {NOTE2} is under way (synthetic).\n")
    commit(sr.repo, "a pre-registration and its evaluation record in one commit", NOTE2, REC_W)
    S2BN, EON, READD = f"{S2R}/s2b/NEXT_PREREG.md", f"{S2R}/E_output_notes.md", f"{S2R}/READD_PREREG.md"
    for p in (S2BN, EON, READD):
        note(sr, p, pre)
    git(sr.repo, "rm", "-q", READD)
    commit(sr.repo, "READD removed")
    note(sr, READD, pre, msg="READD added again")
    REC2 = f"{S2R}/LATER_EVAL.md"
    note(sr, REC2, f"2027-07-05: the evaluation of {S2BN} {EON} {READD} is under way (synthetic).\n")
    hp = ["--hinge", "--hinge-cause", "prereg"]
    for argv, why in ([(hp + ["--prereg", f"{S2R}/{d}", "--prereg-eval", REC], "deny-list") for d in DENY] +
                      [(hp + ["--prereg", f"{S2R}/s2b/E_output.txt", "--prereg-eval", REC], "deny-list"),
                       (hp + ["--prereg", S2BN, "--prereg-eval", REC2], "deny-list"),                   # M18
                       (hp + ["--prereg", EON, "--prereg-eval", REC2], "deny-list"),                    # M19
                       (hp + ["--prereg", READD, "--prereg-eval", REC2], "no unique adding commit"),    # M21
                       (hp + ["--prereg", NOTE2, "--prereg-eval", REC_W], "not added after the pre-registration"),
                       (hp + ["--prereg", SAME, "--prereg-eval", REC], "not added after the commit of the last E"),
                       (hp + ["--prereg", TZN, "--prereg-eval", REC], "on or after 2027-06-30"),
                       (hp + ["--prereg", LATE, "--prereg-eval", REC], "on or after 2027-06-30"),
                       (hp + ["--prereg", BOUND, "--prereg-eval", REC], "on or after 2027-06-30"),
                       (hp + ["--prereg", EARLY, "--prereg-eval", REC], "not added after the commit of the last E"),
                       (hp + ["--prereg", NOSTATUS, "--prereg-eval", REC], "no 'Status: PLAN' line"),
                       (hp + ["--prereg", PLANNED, "--prereg-eval", REC], "no 'Status: PLAN' line"),
                       (hp + ["--prereg", NONAME, "--prereg-eval", REC], "does not name E_hinge_output.txt"),
                       (hp + ["--prereg", NOTE], "--prereg-eval REC"),
                       (hp + ["--prereg", NOTE, "--prereg-eval", OLD], "not added after"),
                       (hp + ["--prereg", NOTE, "--prereg-eval", RECX], "does not name the pre-registration")]):
        r = e_run(fx, sr, argv)
        assert r.rc == 2 and why in r.result_text and not r.written, (argv, r.result_text[-200:])
    good = hp + ["--prereg", NOTE, "--prereg-eval", REC]
    with patched(er, "member_bytes", _hinge_member_moved(er.member_bytes)):
        r = e_run(fx, sr, good)
    assert r.rc == 3 and "INTEGRITY FAILED: INT-FINALSHA c2/structures.tar.gz:a2/s2r_m30_VB136" in r.result_text
    r = e_run(fx, sr, good, keep=True)
    t = r.result_text
    assert r.rc == 0 and "mode hinge" in t and "BLOCK 5. Hinge block: relaxations 1-4" in t and "BLOCK 1." not in t, \
        t[-800:]
    assert all(x.text.endswith(": ok") for x in r.rows if x.id == "XC-K3HINGE") and \
        "figures/source_data/fig_s2b_e_fk_hinge.csv" in r.files
    assert coverage_lines(t) == expected_coverage(True), coverage_lines(t)
    assert "every failed row, printed in full (S2B:739-740)\n  none failed\n" in t      # fix round 2 (D18)
    commit(sr.repo, "E hinge output (unedited)")
    for argv in (hb, good):
        r = e_run(fx, sr, argv, clock=after)
        assert r.rc == 2 and "rerun needs --rerun-cause" in r.result_text, r.result_text[-300:]
    so = synth_repo(fx, "d8_opened", SCEN["pass"], e_text={f"{S2R}/s2b/e_block4.py": block4_true_text()})
    assert e_run(fx, so, ["--run"], keep=True, block4=B4Double("C4B-ENDED", 3, so.commits["F"])).rc == 0
    commit(so.repo, "E attempt 1 (block 5 opened)")
    r = e_run(fx, so, hb, clock=after, block4=B4Double("C4B-ENDED", 3, so.commits["F"]))
    assert r.rc == 2 and "opened block 5" in r.result_text, r.result_text[-300:]


@case("D9", "D", mutants=(
        ("no_excl", lambda fx: patched(ee().Run, "write_excl", _write_overwrite)),))
def case_d9(fx):
    """Outputs (RF-8): the last line of every written attempt file is 'E exit code: <n>'; an output created
    concurrently makes O_EXCL fail (exit 2) and the figure source data of the run is removed; a failed link of a
    CSV removes the partial files and writes the attempt file as a failure report (exit 3); an existing CSV of the
    attempt is refused in phase 0 (exit 2, nothing written; fix round 1)."""
    r, sr = run_of(fx, "C1a")
    assert r.files["s2b/E_output.txt"].rstrip("\n").split("\n")[-1] == "E exit code: 0" and len(r.files) == 3
    out = os.path.join(sr.root, "s2b", "E_output.txt")

    def concurrent(run):
        write_text(out, "a concurrent writer\n")
    try:
        r = e_run(fx, sr, ["--run"], hooks={"before_write": concurrent})
        assert r.rc == 2 and not r.written
        assert not os.listdir(os.path.join(sr.root, "figures", "source_data"))
    finally:
        if os.path.exists(out):
            os.remove(out)

    def link(tmp, path):
        if path.endswith("_meta.csv"):
            raise OSError("planted link failure")
        os.link(tmp, path)
    r = e_run(fx, sr, ["--run"], hooks={"link": link})
    assert r.rc == 3 and list(r.files) == ["s2b/E_output.txt"] and "FAILED: stage phase 2" in r.result_text
    sd = repo_of(fx, "d9_csv", SCEN["C1a"])                # fix round 1: an existing CSV of the attempt (RF-8)
    with open(os.path.join(sd.repo, ".git", "info", "exclude"), "a") as fh:
        fh.write("results/objective2/s2/figures/source_data/\n")
    p = os.path.join(sd.root, "figures", "source_data", "fig_s2b_e_fk.csv")
    write_text(p, "planted\n")
    try:
        rc = e_run(fx, sd, ["--run"])
    finally:
        os.remove(p)
    assert rc.rc == 2 and not rc.written and "fig_s2b_e_fk.csv exists" in rc.result_text, rc.result_text[-300:]
    assert r.files["s2b/E_output.txt"].rstrip("\n").endswith("E exit code: 3")
    assert not [n for n in os.listdir(os.path.join(sr.root, "figures", "source_data")) if n.startswith("fig_s2b_e")]
    # fix round 2 (RF-8): ENOSPC on the attempt file after part of it was written, once (the failure report is
    # written; no CSV stays) and always (a refusal: no attempt file, no CSV)
    out_dir = os.path.join(sr.root, "s2b")

    def enospc(fd, path):
        os.write(fd, b"partial ")
        raise OSError(errno.ENOSPC, "planted: no space left on device")
    calls = []

    def once(fd, path):
        calls.append(path)
        if len(calls) == 1:
            enospc(fd, path)
    for hook, want_rc in ((once, 3), (enospc, 2)):
        r = e_run(fx, sr, ["--run"], hooks={"write": hook})
        left = [n for n in os.listdir(os.path.join(sr.root, "figures", "source_data")) if n.startswith("fig_s2b_e")]
        assert r.rc == want_rc and not left, (want_rc, r.rc, left, r.result_text[-300:])
        if want_rc == 3:
            assert list(r.files) == ["s2b/E_output.txt"] and "FAILED: stage phase 2 (attempt file): OSError" in \
                r.result_text and r.files["s2b/E_output.txt"].rstrip("\n").endswith("E exit code: 3")
        else:
            assert not r.written and not os.path.exists(os.path.join(out_dir, "E_output.txt")) and \
                "could not be written (OSError)" in r.result_text, r.result_text[-300:]


def _write_overwrite(self, path, text):
    with open(path, "w") as fh:
        fh.write(text)
    self.written.append(path)


@case("D11", "D", mutants=(
        # the fr verify record taken to be the c2 one
        ("fr_verify_unchecked", lambda fx: patched(ee(), "VERIFY_RECORD", {
            "c2": ee().VERIFY_RECORD["c2"], "fr": ee().VERIFY_RECORD["c2"]})),))
def case_d11(fx):
    """The verified archive (S2B:522; OP-18, amendment item 10; engineer C): with the committed
    fr_verify/verify_fr.txt removed (a committed removal), the run is refused (exit 2, nothing written); when it is
    present, its path, sha256 and last line are printed (C1a)."""
    sr = synth_repo(fx, "d11", SCEN["C1a"])
    git(sr.repo, "rm", "-q", f"{S2R}/fr_verify/verify_fr.txt")
    commit(sr.repo, "fr verify record removed (synthetic)")
    r = e_run(fx, sr, ["--run"])
    assert r.rc == 2 and not r.written and "verify record of fr" in r.result_text, r.result_text[-300:]
    r0, _ = run_of(fx, "C1a")
    assert re.search(r"^verify record fr: results/objective2/s2/fr_verify/verify_fr\.txt sha256 [0-9a-f]{64}; last "
                     r"line: verify fr: ok$", r0.result_text, re.M), r0.result_text[:3000]


class _B4C3(B4Double):
    """The block-4 test double with a given c3b start commit (RF-3)."""

    def __init__(self, route_id, df_delta, F, c3b_start):
        super().__init__(route_id, df_delta, F)
        self.c3s = c3b_start

    def tier_route(self, run):
        d = super().tier_route(run)
        d["commits"]["c3b_start"] = self.c3s
        return d


def _show_b4_true(orig):
    def f(self, c, path):
        if path.endswith("s2b/e_block4.py"):
            return block4_true_text().encode()
        return orig(self, c, path)
    return f


@case("D12", "D", mutants=(
        ("rf3_c3b_unchecked", lambda fx: patched(ee().Git, "show", _show_b4_true(ee().Git.show))),))
def case_d12(fx):
    """RF-3, block-4 part (amendment item 8; engineer C): on a route past FR, e_block4.py with BLOCK4_IMPLEMENTED =
    True must be in the c3b start commit, with no amendment route: a c3b start commit holding the stub, or one
    without e_block4.py, gives exit 2 (nothing written); the same test double with the c3b start at the fr campaign
    commit (block 4 implemented there) runs (exit 0)."""
    sr = synth_repo(fx, "d12", SCEN["pass"], e_text={f"{S2R}/s2b/e_block4.py": block4_true_text()})
    p = os.path.join(sr.repo, S2R, "s2b", "e_block4.py")
    with open(p) as fh:
        t = fh.read()
    write_text(p, t.replace("\nBLOCK4_IMPLEMENTED = True\n", "\nBLOCK4_IMPLEMENTED = False\n", 1))
    stub = commit(sr.repo, "block 4 as the stub (synthetic c3b start)")
    write_text(p, t)
    commit(sr.repo, "block 4 implemented again")
    for c3s in (stub, sr.commits["c2"]):
        r = e_run(fx, sr, ["--run"], block4=_B4C3("C4B-NOTRUN", None, sr.commits["F"], c3s))
        assert r.rc == 2 and not r.written and "c3b start commit (RF-3)" in r.result_text, r.result_text[-300:]
    r = e_run(fx, sr, ["--run"], block4=_B4C3("C4B-NOTRUN", None, sr.commits["F"], sr.commits["F"]))
    assert r.rc == 0, r.result_text[-500:]


def _standing_without_fallback(self):
    have = [(f, self.read_out(f)) for f in ee().EVAL_FILES if os.path.exists(self.out_path(f))]
    for f, t in reversed(have):
        if ee().exit_code_of(t) in (0, 1):
            return have, f, t
    raise EError("no evaluation output stands (spec 14.3, RF-6)")


@case("D13", "D", mutants=(
        # only an output with exit 0 or 1 taken to stand
        ("fallback_not_standing", lambda fx: patched(ee().Run, "standing_output", _standing_without_fallback)),))
def case_d13(fx):
    """RF-1, last point (engineer C): the deferred hinge run is also allowed after a FALLBACK attempt (exit 3) whose
    output holds 'BLOCK 5. Hinge block: not opened' (backstop, injected clock after 2027-06-30); two attempts that
    failed before output without a FALLBACK leave no standing output, and the hinge run is refused (exit 2). The two
    attempt files are planted committed texts (the FALLBACK route itself is D7). Fix round 1: of two outputs with
    exit 0 the latest stands (RF-6)."""
    sr = synth_repo(fx, "d13", SCEN["C1a"])
    hb = ["--hinge", "--hinge-cause", "backstop"]
    after = lambda: datetime.datetime(2027, 7, 1, 12, tzinfo=datetime.timezone.utc)
    fail = "S2b E, attempt {} of the one evaluation (planted)\n\nFAILED: stage block 3: RuntimeError\n\nEND\n" \
           "E exit code: 3\n"
    note(sr, f"{S2R}/s2b/E_output.txt", fail.format(1), msg="E attempt 1 (planted: failed before output)")
    note(sr, f"{S2R}/s2b/E_output_attempt2.txt", fail.format(2), msg="E attempt 2 (planted: no FALLBACK)")
    r = e_run(fx, sr, hb, clock=after)
    assert r.rc == 2 and not r.written and "no evaluation output stands" in r.result_text, r.result_text[-300:]
    fb = fail.format(2).replace("\nEND\n", "\nFALLBACK (S2B §7, item 7): E failed twice.\n  every other part-c value, "
                                "and the tier: not read: E failed\nBLOCK 5. Hinge block: not opened (trigger not "
                                "evaluated)\n\nEND\n")
    note(sr, f"{S2R}/s2b/E_output_attempt2.txt", fb, msg="E attempt 2 (planted: with the FALLBACK)")
    r = e_run(fx, sr, hb, clock=after)
    assert r.rc == 0 and "standing evaluation output: E_output_attempt2.txt (exit 3;" in r.result_text and \
        "s2b/E_hinge_output.txt" in r.files, r.result_text[-600:]
    s2 = synth_repo(fx, "d13b", SCEN["C1a"])                # fix round 1: two outputs (exit 0, then exit 0 after a
    ok = ("S2b E, attempt {} of the one evaluation (planted)\n\n" + ee().NOT_OPENED +   # code error, RF-6):
          ". df_δ ...: not held.\n\nEND\nE exit code: 0\n")                            # the latest stands
    note(s2, f"{S2R}/s2b/E_output.txt", ok.format(1), msg="E attempt 1 (planted)")
    note(s2, f"{S2R}/s2b/E_output_attempt2.txt", ok.format(2), msg="E attempt 2 (planted)")
    r = e_run(fx, s2, hb, clock=after)
    assert r.rc == 0 and "standing evaluation output: E_output_attempt2.txt (exit 0;" in r.result_text, \
        r.result_text[-600:]
    # fix round 2 (M20): attempt 1 (exit 0) stands, attempt 2 failed before output (no FALLBACK); a NOTE committed
    # between the two is not after 'the last E attempt file' (attempt 2), so it is refused
    s3 = synth_repo(fx, "d13c", SCEN["C1a"])
    NOTE, REC = f"{S2R}/NEXT_PREREG.md", f"{S2R}/NEXT_PREREG_EVAL.md"
    note(s3, f"{S2R}/s2b/E_output.txt", ok.format(1), msg="E attempt 1 (planted: exit 0)")
    note(s3, NOTE, "# A later pre-registration (synthetic)\n\n**Status: PLAN.** Written on 2027-01-10.\n\nIt names "
                   "results/objective2/s2/s2b/E_hinge_output.txt as data.\n")
    note(s3, f"{S2R}/s2b/E_output_attempt2.txt", fail.format(2), msg="E attempt 2 (planted: exit 3, no FALLBACK)")
    note(s3, REC, f"The evaluation of {NOTE} is under way (synthetic).\n")
    r = e_run(fx, s3, ["--hinge", "--hinge-cause", "prereg", "--prereg", NOTE, "--prereg-eval", REC])
    assert r.rc == 2 and not r.written and "not added after the commit of the last E attempt file" in r.result_text, \
        r.result_text[-300:]


@case("D14", "D")
def case_d14(fx):
    """Admissibility before integrity (fix round 1; S2B:515-518, spec 6.1, 6.2): every refusal comes before any check
    that writes. (a) A final STOP with fr/gates/fr_step0.json removed and no --stop-note: exit 2, nothing written
    (before: INT-STRUCT, exit 3). (b) A --stop-note path with a '.' segment, an empty segment or a trailing '/': exit
    2 (before: AttributeError, exit 3). (c) Attempt 2 after an attempt 1 that failed before output, with an unknown
    --rerun-cause or an --amendment that does not exist: exit 2, nothing written, no FALLBACK (before: exit 3 with
    the item-7 FALLBACK). Fix round 2, each beside an integrity failure of phase 0b (fr/gates/fr_step0.json missing):
    (d) the fr verify record removed in a commit (M28); (e) after a committed attempt 1, the hinge run on the backstop
    with a clock before 2027-06-30 (M29): exit 2, nothing written (the single hinge attempt is not used up)."""
    sr = repo_of(fx, "d14_s0", SCEN["C1j"], post=_post_rm("fr/gates/fr_step0.json"))
    r = e_run(fx, sr, ["--run"])
    assert r.rc == 2 and not r.written and "needs --stop-note" in r.result_text, r.result_text[-300:]
    sr, nt = stop_repo(fx)
    for bad in (f"{S2R}/./FR_STOP_NOTE.md", f"{S2R}//FR_STOP_NOTE.md", f"{S2R}/FR_STOP_NOTE.md/"):
        r = e_run(fx, sr, ["--run", "--stop-note", bad])                 # IX-6: refused by the one fixed path
        assert r.rc == 2 and not r.written and "the stop note is the one file" in r.result_text, \
            (bad, r.result_text[-300:])
    s7 = synth_repo(fx, "d14_a2", SCEN["C1a"], e_text={E_READ_REL: buggy_e_read()})
    with patched(ee().Run, "block3", _fail_block3):
        assert e_run(fx, s7, ["--run"], keep=True).rc == 3
    commit(s7.repo, "E attempt 1 (failed before output)")
    shutil.copyfile(os.path.join(HERE, "e_read.py"), os.path.join(s7.repo, E_READ_REL))
    write_text(os.path.join(s7.repo, AMEND), amend_text(s7))
    commit(s7.repo, "E fix and its dated amendment")
    for argv, why in ((["--run", "--rerun-cause", "NOT_A_CASE", "--amendment", AMEND], "not a case"),
                      (["--run", "--rerun-cause", "B3", "--amendment", f"{S2R}/ABSENT.md"], "not committed and clean")):
        r = e_run(fx, s7, argv)
        assert r.rc == 2 and not r.written and why in r.result_text and "FALLBACK" not in r.result_text, \
            (argv, r.result_text[-300:])
    # fix round 2 (M28, M29): with fr/gates/fr_step0.json missing (an INT-STRUCT of phase 0b), (d) a removed verify
    # record and (e) a hinge run on the backstop before 2027-06-30 are still refusals (exit 2, nothing written)
    sv = synth_repo(fx, "d14_verify", SCEN["C1a"], post=_post_rm("fr/gates/fr_step0.json"))
    git(sv.repo, "rm", "-q", f"{S2R}/fr_verify/verify_fr.txt")
    commit(sv.repo, "fr verify record removed (synthetic)")
    r = e_run(fx, sv, ["--run"])
    assert r.rc == 2 and not r.written and "verify record of fr" in r.result_text, r.result_text[-300:]
    sb = synth_repo(fx, "d14_hinge", SCEN["C1a"])
    assert e_run(fx, sb, ["--run"], keep=True).rc == 0
    commit(sb.repo, "E attempt 1 (unedited)")
    git(sb.repo, "rm", "-q", f"{S2R}/fr/gates/fr_step0.json")
    commit(sb.repo, "fr/gates/fr_step0.json removed (synthetic)")
    r = e_run(fx, sb, ["--hinge", "--hinge-cause", "backstop"],
              clock=lambda: datetime.datetime(2027, 1, 1, 12, tzinfo=datetime.timezone.utc))
    assert r.rc == 2 and not r.written and "the backstop is 2027-06-30" in r.result_text, r.result_text[-300:]


@case("D15", "D", mutants=(
        # the standing output's stop note not compared (another valid note accepted)
        ("stop_note_unchecked", lambda fx: patched(ee(), "ROUTE_STOP_NOTE", re.compile(r"(?!)"))),))
def case_d15(fx):
    """The deferred hinge run on the routes the earlier code missed (fix round 1; S2B:153, 714-719; spec 14.3,
    OP-22): (a) after a final STOP in fr: without --stop-note, or with a valid note other than the one the standing
    output names, it is refused; with that note (re-validated at HEAD) it writes E_hinge_output.txt (exit 0) and the
    block-5 values equal the independent ones; (b) after FR-2 failed (C1i): exit 0 and no 'cross-check failed' (XC-FR2,
    XC-FR2-DEC and XC-DSUM-FR are not recomputed in the hinge run); (c) a hinge rerun after a fix of E's code with a
    cause that fails on the earlier code writes E_hinge_output_attempt2.txt, and a third is refused. Fix round 2: on
    (a), the stop note edited in place after E's output is refused (its sha256, M14), and a standing output whose
    FR-STOP route line names no stop note is refused. Integration review 1 (IX-6): a valid note at another path is
    refused by the one fixed path."""
    after = lambda: datetime.datetime(2027, 7, 1, 12, tzinfo=datetime.timezone.utc)
    hb = ["--hinge", "--hinge-cause", "backstop"]
    sj = synth_repo(fx, "d15_stop", SCEN["C1j"])
    nt, other = f"{S2R}/FR_STOP_NOTE.md", f"{S2R}/FR_STOP_NOTE_2.md"
    for p in (nt, other):
        note(sj, p, "# FR stop note (synthetic)\n\n2026-11-21: the fr STOP is final; no relaunch.\n")
    assert e_run(fx, sj, ["--run", "--stop-note", nt], keep=True).rc == 0
    commit(sj.repo, "E attempt 1 (unedited)")
    r = e_run(fx, sj, hb, clock=after)
    assert r.rc == 2 and not r.written and "needs --stop-note" in r.result_text, r.result_text[-300:]
    r = e_run(fx, sj, hb + ["--stop-note", other], clock=after)        # IX-6: a second note is no stop note
    assert r.rc == 2 and not r.written and "the stop note is the one file" in r.result_text, r.result_text[-300:]
    r = e_run(fx, sj, hb + ["--stop-note", nt], clock=after)
    assert r.rc == 0 and "s2b/E_hinge_output.txt" in r.files and "S2b FR: stopped at s2r_m30_Cs188o0_novac" in \
        r.result_text, r.result_text[-600:]
    check_block5(r, sj)
    # fix round 2 (M14): the same note edited in place after E's output (still final and dated): another sha256
    with open(os.path.join(sj.repo, nt)) as fh:
        t0 = fh.read()
    note(sj, nt, t0 + "\n2026-11-30: a line added after E's output (synthetic).\n")
    r = e_run(fx, sj, hb + ["--stop-note", nt], clock=after)
    assert r.rc == 2 and not r.written and "is not the stop note of E_output.txt" in r.result_text, \
        r.result_text[-300:]
    note(sj, nt, t0)                                      # the same bytes again, the same sha256
    # fix round 2: a standing output whose FR-STOP route line names no stop note is refused (it failed open before)
    with open(os.path.join(sj.root, "s2b", "E_output.txt")) as fh:
        eo = fh.read()
    eo2 = re.sub(r"; stop note .* sha256 [0-9a-f]{64}\)", ")", eo, count=1)
    assert eo2 != eo
    note(sj, f"{S2R}/s2b/E_output.txt", eo2, msg="the standing output's route line without its stop note (planted)")
    r = e_run(fx, sj, hb + ["--stop-note", nt], clock=after)
    assert r.rc == 2 and not r.written and "names no stop note on its FR-STOP route line" in r.result_text, \
        r.result_text[-300:]
    si = synth_repo(fx, "d15_fr2", SCEN["C1i"])
    assert e_run(fx, si, ["--run"], keep=True).rc == 0
    commit(si.repo, "E attempt 1 (unedited)")
    r = e_run(fx, si, hb, clock=after)
    assert r.rc == 0 and "cross-check failed" not in r.result_text and \
        not any("L_XFAIL" in x.labels for x in r.rows), r.result_text[-1500:]
    for xid in ("XC-FR2", "XC-FR2-DEC", "XC-DSUM-FR"):
        assert f"\n  {xid}: 0 ok, 0 failed, 1 not evaluated\n" in r.result_text, xid
    sh = synth_repo(fx, "d15_rerun", SCEN["C1a"], e_text={E_READ_REL: buggy_e_read()})
    assert e_run(fx, sh, ["--run"], keep=True).rc == 0
    commit(sh.repo, "E attempt 1 (unedited)")
    assert e_run(fx, sh, hb, clock=after, keep=True).rc == 0
    commit(sh.repo, "E hinge output (unedited)")
    shutil.copyfile(os.path.join(HERE, "e_read.py"), os.path.join(sh.repo, E_READ_REL))
    write_text(os.path.join(sh.repo, AMEND), amend_text(sh))
    commit(sh.repo, "E fix and its dated amendment")
    rr = hb + ["--rerun-cause", "B3", "--amendment", AMEND]
    r = e_run(fx, sh, rr, clock=after, keep=True)
    assert r.rc == 0 and "s2b/E_hinge_output_attempt2.txt" in r.files and "hinge run, attempt 2" in r.result_text \
        and "figures/source_data/fig_s2b_e_fk_hinge_attempt2.csv" in r.files, r.result_text[-600:]
    commit(sh.repo, "E hinge output, attempt 2 (unedited)")
    r = e_run(fx, sh, rr, clock=after)
    assert r.rc == 2 and not r.written and "a third hinge run is refused" in r.result_text


@case("D16", "D", mutants=(
        # bytecode looked up in __pycache__ under the root again (the code before fix round 1)
        ("pycache_read", lambda fx: patched(sys, "pycache_prefix", None)),))
def case_d16(fx):
    """A stale __pycache__/check5_diag.cpython-*.pyc under the root (ignored by git, so the clean-tree check cannot see
    it) is never read (fix round 1): E loads c2_diagnostic/check5_diag.py from its tracked source (sys.pycache_prefix
    lies outside every root) and exits 0; before, OpenAudit logged the .pyc with no HEAD blob (INT-SHA, exit 3)."""
    import py_compile
    sr = synth_repo(fx, "d16", SCEN["C1a"])
    with open(os.path.join(sr.repo, ".git", "info", "exclude"), "a") as fh:
        fh.write("__pycache__/\n")
    src = os.path.join(sr.root, "c2_diagnostic", "check5_diag.py")
    pyc = os.path.join(os.path.dirname(src), "__pycache__", f"check5_diag.{sys.implementation.cache_tag}.pyc")
    py_compile.compile(src, cfile=pyc, doraise=True)
    key = "_s2b_e_check5_diag"
    saved = sys.modules.pop(key, None)
    try:
        with patched(er, "S2", sr.root):                  # load_cd from the root, as in a real run
            r = e_run(fx, sr, ["--run"])
    finally:
        sys.modules.pop(key, None)
        if saved is not None:
            sys.modules[key] = saved
        shutil.rmtree(os.path.dirname(pyc))
    assert r.rc == 0, r.result_text[-400:]
    assert not any("__pycache__" in e["rel"] for e in r.au.log.values())
    assert any(e["rel"] == "c2_diagnostic/check5_diag.py" for e in r.au.log.values())


def _force_fallback(run):
    """White box: the state of an attempt 2 whose attempt 1 failed before output, then a failure before output."""
    run.attempt, run.attempt1_exit = 2, 3
    raise RuntimeError("planted failure before output")


@case("D17", "D", mutants=(
        # the fallback never prints .hinge (A1)
        ("fallback_no_hinge", lambda fx: patched(ee().Run, "fallback", _fallback_without_route(ee().Run.fallback))),
        # integration review 3 (IX-12): the fallback's L_FRSTOP on every FR-STOP route, whatever gate FR recorded
        ("fallback_frstop_any_outcome", lambda fx: src_patched(
            ee().Run, "fallback", 'if self.frstop_pass(g.get("decision.FR.outcome")) else ""',
            'if (self.route or {}).get("id") == "FR-STOP" else ""'))))
def case_d17(fx):
    """The item-7 fallback's variants (spec 16; S2B:730-734; fix round 1), white box on the FR-pass route C4B-ENDED
    (the block-4 test double): with df_delta 3 the FALLBACK prints the three gate-recorded FR-2 leaves (the A1 value
    and delta_far also with the item-4 label, here L_FRVALID; RF-25) and the K3 .hinge leaf, and no 'not opened'
    line; with df_delta 2 it prints no .hinge and the 'BLOCK 5 ... not opened' line. Integration (ER2-3): the labels
    blocks 1-2 attach follow L_FALLBACK: L_FAR on .far from both K3 files; on the FR-2-fail route C1i, L_FR2 on all
    three FR-2 values (and L_ITEM4 on the A1 value and delta_far), on the FR-pass route none. Integration review 2
    (IX-4): on FR-STOP after a recorded gate FR pass (C1v_pass), the A1 value and delta_far carry L_ITEM4 and never
    L_FRVALID (the FR-STOP conjunct of Run.fallback), and (IX-12) E_b^A2 carries L_FRSTOP, which the done FR-pass
    route's fallback never prints. Integration review 3: on FR-STOP after a recorded FR-2 failure (C1v_fr2) the
    fallback's three FR-2 values carry L_FR2 and never L_FRSTOP (the outcome conjunct of IX-12)."""
    sr = repo_of(fx, "pass")
    lab, valid = LABELS["L_FALLBACK"], LABELS["L_FRVALID"]

    def lines(t, pre):
        return [x for x in t.split("\n") if x.startswith(pre)]
    for df, hinge in ((3, True), (2, False)):
        r = e_run(fx, sr, ["--run"], block4=B4Double("C4B-ENDED", df, sr.commits["F"]),
                  hooks={"before_exit_audit": _force_fallback})
        t = r.result_text
        assert r.rc == 3 and "FALLBACK (S2B §7, item 7): E failed twice." in t, t[-600:]
        for k in ("Eb_A1_meV", "Eb_A2_meV", "delta_far_meV"):
            ln = lines(t, f"  fr/gates/FR.json result.FR2.{k} = ")
            assert len(ln) == 1 and lab in ln[0] and ((valid in ln[0]) == (k != "Eb_A2_meV")), (k, ln)
            assert ln[0].split(" meV -- ", 1)[1].startswith(lab) and LABELS["L_FR2"] not in ln[0], ln   # ER2-3
            assert LABELS["L_FRSTOP"] not in ln[0], ln                                      # IX-12: FR-STOP only
        far = lines(t, "  c2/gates/K3.json result.Eb_A2_meV.far = ") + \
            lines(t, "  c2/gates_applied/gate_K3.gate.json result.Eb_A2_meV.far = ")
        assert len(far) == 2 and all(x.split(" meV -- ", 1)[1] == f"{lab}; {LABELS['L_FAR']}" for x in far), far
        assert ("result.Eb_A2_meV.hinge" in t) is hinge and ("BLOCK 5. Hinge block: not opened" in t) is not hinge, df
    r = e_run(fx, repo_of(fx, "C1i"), ["--run"], hooks={"before_exit_audit": _force_fallback})   # ER2-3, FR-2 fails
    t, i4 = r.result_text, LABELS["L_ITEM4"]
    assert r.rc == 3 and "FALLBACK (S2B §7, item 7): E failed twice." in t, t[-600:]
    for k in ("Eb_A1_meV", "Eb_A2_meV", "delta_far_meV"):
        ln = lines(t, f"  fr/gates/FR.json result.FR2.{k} = ")
        want = f"{lab}; {i4}; {LABELS['L_FR2']}" if k != "Eb_A2_meV" else f"{lab}; {LABELS['L_FR2']}"
        assert len(ln) == 1 and ln[0].split(" meV -- ", 1)[1] == want and valid not in ln[0], (k, ln)
    sv, nv = stop_repo(fx, "C1v_pass", SCEN["C1v_pass"])          # IX-4: a gate FR pass, then a final STOP
    r = e_run(fx, sv, ["--run", "--stop-note", nv], hooks={"before_exit_audit": _force_fallback})
    t = r.result_text
    assert r.rc == 3 and "FALLBACK (S2B §7, item 7): E failed twice." in t, t[-600:]
    for k in ("Eb_A1_meV", "Eb_A2_meV", "delta_far_meV"):           # IX-12: L_FRSTOP where no item-4 label stands
        ln = lines(t, f"  fr/gates/FR.json result.FR2.{k} = ")
        want = f"{lab}; {i4}" if k != "Eb_A2_meV" else f"{lab}; {LABELS['L_FRSTOP']}"
        assert len(ln) == 1 and ln[0].split(" meV -- ", 1)[1] == want and valid not in ln[0], (k, ln)
    sf, nf = stop_repo(fx, "C1v_fr2", SCEN["C1v_fr2"])            # IX-12: an FR-2 failure, then a final STOP
    r = e_run(fx, sf, ["--run", "--stop-note", nf], hooks={"before_exit_audit": _force_fallback})
    t = r.result_text
    assert r.rc == 3 and "FALLBACK (S2B §7, item 7): E failed twice." in t, t[-600:]
    for k in ("Eb_A1_meV", "Eb_A2_meV", "delta_far_meV"):
        ln = lines(t, f"  fr/gates/FR.json result.FR2.{k} = ")
        want = f"{lab}; {i4}; {LABELS['L_FR2']}" if k != "Eb_A2_meV" else f"{lab}; {LABELS['L_FR2']}"
        assert len(ln) == 1 and ln[0].split(" meV -- ", 1)[1] == want, (k, ln)
    assert LABELS["L_FRSTOP"] not in t


def _fallback_without_route(orig):
    def f(self):
        rt, self.route = self.route, dict(self.route or {}, id="FR-FAIL")
        try:
            return orig(self)
        finally:
            self.route = rt
    return f


def _hinge_section(t):
    return t.split("CROSS-CHECKS OF BLOCKS 1-3 (", 1)[1].split("\n\n", 1)[0].split("\n")[1:]


@case("D18", "D", mutants=(
        # the failed block 1-3 rows not printed in the hinge run (the code before fix round 2)
        ("hinge_xc_rows_dropped", lambda fx: patched(ee().Row, "__init__", _row_init_drop_xfail(ee().Row.__init__))),))
def case_d18(fx):
    """Fix round 2 (S2B:739-740): in the deferred hinge run, blocks 1-3 are recomputed in memory and their
    cross-checks count in the CROSS-CHECKS summary and the exit code, so every failed one is printed in full: with
    the K3 .far value off by 2e-6 meV, attempt 1 exits 1 and the hinge run exits 1 and prints both XC-K3FAR rows with
    'cross-check failed', their values and residual, as the standing output prints them; a clean hinge run prints
    'none failed' (D8)."""
    sr = synth_repo(fx, "d18", {"fr": SCEN["C1a"]["fr"], "k3_far_offset": 2e-6})
    r1 = e_run(fx, sr, ["--run"], keep=True)
    assert r1.rc == 1, r1.result_text[-400:]
    commit(sr.repo, "E attempt 1 (unedited)")
    r = e_run(fx, sr, ["--hinge", "--hinge-cause", "backstop"],
              clock=lambda: datetime.datetime(2027, 7, 1, 12, tzinfo=datetime.timezone.utc))
    t = r.result_text
    assert r.rc == 1 and t.rstrip("\n").endswith("E exit code: 1"), t[-600:]
    sec = _hinge_section(t)
    assert len(sec) == 2 and all(x.startswith("  XC-K3FAR: E_b^A2(Pb76) ") and "|Δ| = " in x and
                                 x.endswith(LABELS["L_XFAIL"]) for x in sec), sec
    assert all(x in r1.result_text for x in sec)                  # the rows of the standing output, unchanged
    assert "\n  XC-K3FAR: 0 ok, 2 cross-check failed, 0 not evaluated\n" in t


def _row_init_drop_xfail(orig):
    def f(self, *a, **kw):
        orig(self, *a, **kw)
        if self.kind == "xcheck" and self.block in (1, 2, 3):
            self.labels = tuple(x for x in self.labels if x != "L_XFAIL")
    return f


@case("D19", "D", mutants=(
        # the route without its own refusal (the 40-hex refusal of the commits stays)
        ("no_precommit_refusal", lambda fx: patched(ee().Run, "route_admit", _route_admit_no_precommit(
            ee().Run.route_admit))),))
def case_d19(fx):
    """Fix round 2 (open for the analyst): a final STOP before the fr campaign commit was recorded (the first fr
    start stopped by its commit check: fr/campaign.json status 'stopped' with commit and start_commit null, as W 50
    set_campaign writes them) is refused with its own reason (exit 2, nothing written): S2B_LAST and the RF-3 check are
    not defined there until a dated amendment rules on the route."""
    sr = synth_repo(fx, "d19", SCEN["C1j"])
    note(sr, f"{S2R}/FR_STOP_NOTE.md", "# FR stop note (synthetic)\n\n2026-11-21: the fr STOP is final.\n")
    _post_json("fr/campaign.json", lambda d: d.update(commit=None, start_commit=None, commit_history=[]))(
        sr.root, sr.man)
    commit(sr.repo, "fr stopped before its campaign commit (synthetic)")
    r = e_run(fx, sr, ["--run", "--stop-note", f"{S2R}/FR_STOP_NOTE.md"])
    assert r.rc == 2 and not r.written and "fr stopped before its campaign commit was recorded" in r.result_text, \
        r.result_text[-300:]


@case("D20", "D")
def case_d20(fx):
    """IX-7: a --stop-note on a done fr is refused (exit 2, nothing written), as the FR figure and the 6b read refuse
    it: on an FR-fail route (C1a) and on the step-0-final route (C1h), with the fixed stop note committed, clean and
    valid; and on the hinge run of C1a after its committed attempt 1."""
    for name in ("C1a", "C1h"):
        sr, nt = stop_repo(fx, f"d20_{name}", SCEN[name])
        r = e_run(fx, sr, ["--run", "--stop-note", nt])
        assert r.rc == 2 and not r.written and "is refused: fr is done, there is no STOP (IX-7)" in r.result_text, \
            (name, r.rc, r.result_text[-300:])
        assert e_run(fx, sr, ["--run"]).rc == 0                     # the same archive without the note runs
    sr, nt = stop_repo(fx, "d20_C1a")
    assert e_run(fx, sr, ["--run"], keep=True).rc == 0
    commit(sr.repo, "E attempt 1 (unedited)")
    r = e_run(fx, sr, ["--hinge", "--hinge-cause", "backstop", "--stop-note", nt],
              clock=lambda: datetime.datetime(2027, 7, 1, 12, tzinfo=datetime.timezone.utc))
    assert r.rc == 2 and not r.written and "fr is done, there is no STOP (IX-7)" in r.result_text, r.result_text[-300:]


def _post_unapplied(*rels):
    """IX-15: gate FR written but not applied, as W 50 run_gate leaves it at an N-FR4 or N-FR8 'not applied' Stop:
    fr/gates/FR.json and gates_applied/gate_FR.inputs.json kept, the gates_applied copy and marker (rels) never
    written, and fr_outcome null at the STOP (state FR was not set)."""
    def post(root, man):
        for rel in rels:
            os.remove(os.path.join(root, "fr", rel))
        _post_json("fr/campaign.json", lambda d: d.update(fr_outcome=None))(root, man)
    return post


@case("D21", "D", mutants=(
        # IX-15 reverted: gate FR written but not applied reaches INT-STRUCT (exit 3, the failure report written)
        ("unapplied_admitted", lambda fx: patched(ee(), "gate_fr_unapplied", lambda fr_dir: False)),))
def case_d21(fx):
    """Integration review 2 (IX-15): a stopped fr whose fr/gates/FR.json exists without its gates_applied copy (gate FR
    written but not applied; the N-FR4 or N-FR8 'not applied' Stops of W 50 run_gate) is refused (exit 2, nothing
    written), with the stop note valid and without any note (the refusal comes before the note is read), after an FR-1
    failure and after a pass recorded by the gate; the existence test is by name. The same archives with the copy and
    marker in place (C1v) run."""
    for name, base in (("d21_fr1", "C1v_fr1"), ("d21_pass", "C1v_pass")):
        sr, nt = stop_repo(fx, name, SCEN[base], post=_post_unapplied("gates_applied/gate_FR.gate.json",
                                                                      "gates_applied/gate_FR.json"))
        assert os.path.exists(os.path.join(sr.root, "fr", "gates", "FR.json")) and os.path.exists(
            os.path.join(sr.root, "fr", "gates_applied", "gate_FR.inputs.json"))
        for argv in (["--run", "--stop-note", nt], ["--run"]):
            r = e_run(fx, sr, argv)
            assert r.rc == 2 and not r.written and "fr stopped after gate FR was written but not applied" in \
                r.result_text and "(IX-15)" in r.result_text, (name, argv, r.rc, r.result_text[-300:])


def _route_admit_no_precommit(orig):
    def f(self):
        cj = self.load("fr", "campaign.json", "fr", "campaign_fr")
        if cj is not FILE_ABSENT and cj.get("status") == "stopped" and cj.get("commit") is None:
            raise EError("fr/campaign.json commit is not a 40-hex commit (spec 7)")
        return orig(self)
    return f


# ---------------------------------------------------------------- group T: the block-4 stub (spec 13, 18 T)
@case("T1", "T", mutants=(
        ("stub_returns", lambda fx: patched(_sibling("e_block4"), "rows", lambda result, labels: [])),
        ("flag_true", lambda fx: patched(_sibling("e_block4"), "BLOCK4_IMPLEMENTED", True))))
def case_t1(fx):
    """Block 4 at the FR commit is a stub: BLOCK4_IMPLEMENTED is False and every interface function raises
    NotImplementedError('block 4 is specified before C3b ...'); a run on an FR-pass route is refused (exit 2,
    nothing written); an FR-fail route never calls block 4. T1-T5 of spec 18 are written with block 4."""
    b4 = _sibling("e_block4")
    assert b4.BLOCK4_IMPLEMENTED is False
    for fn, args in ((b4.tier_route, (None,)), (b4.c4b_df_delta_validity, (None,)),
                     (b4.build_tier_table, (None, None, None)), (b4.evaluate_tier, (None, None)),
                     (b4.rows, (None, None)), (b4.manifest, (None, None))):
        raises(NotImplementedError, fn, *args, check=lambda e: "before C3b" in str(e))
    r = e_run(fx, repo_of(fx, "pass"), ["--run"])
    assert r.rc == 2 and not r.written and "block 4 is a stub" in r.result_text
    r, sr = run_of(fx, "C1a")
    assert "BLOCK 4. Tier block: not printed (FR failed)" in r.result_text


# ---------------------------------------------------------------- runner
def run(ids=None, *, mutants=True, out=print, keep=None):
    """Run the cases (and their mutants). Returns 0 if every case passed and every mutant was caught, else 1."""
    added = eg.selftest_block(eg.real_s2_dirs())         # RF-9: for the rest of the process (never removed here)
    added += eg.selftest_block(real_archive_roots(OBJECTS["repo"]))   # and those of --repo (old-code runs; RF-9)
    assert added or eg._STATE["blocked"]
    ids = list(ids or CASES)
    unknown = [i for i in ids if i not in CASES]
    if unknown:
        out(f"unknown case(s): {unknown}")
        return 1
    fx = Fixture(keep)
    bad = []
    try:
        for cid in ids:
            c = CASES[cid]
            t0 = time.time()
            try:
                c.fn(fx)
                st = "ok"
            except Exception as e:
                st = f"FAILED ({type(e).__name__}: {str(e)[:300]})"
                bad.append(cid)
            caught = []
            if mutants and st == "ok":
                for name, mk in c.mutants:
                    fx.mutant = f"{cid}/{name}"                  # cached base runs are not reused (cached())
                    try:
                        with mk(fx):
                            c.fn(fx)
                    except MutantNotApplied as e:
                        bad.append(f"{cid}/{name}")
                        caught.append(f"{name}: NOT APPLIED ({str(e)[:200]})")
                        continue
                    except Exception as e:
                        caught.append(f"{name}: {type(e).__name__}")
                        continue
                    finally:
                        fx.mutant = None
                        if eg.OpenAudit.current() is not None:
                            eg.OpenAudit.current().stop()
                    bad.append(f"{cid}/{name}")
                    caught.append(f"{name}: NOT CAUGHT")
            out(f"{cid} [{c.group}] {st} ({time.time() - t0:.1f} s); mutants {len(c.mutants)}: " +
                ("; ".join(caught) if caught else "-"))
    finally:
        for m in fx.close():
            out(f"cleanup: {m}")
        if eg.OpenAudit.current() is not None:
            eg.OpenAudit.current().stop()
    out(f"e_selftest: {len(ids) - len([b for b in bad if '/' not in b])} of {len(ids)} cases passed; "
        f"{sum(len(CASES[i].mutants) for i in ids)} mutants, "
        f"{len([b for b in bad if '/' in b])} not caught" + (f"; failed: {bad}" if bad else ""))
    return 0 if not bad else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Self-tests of E (groups A-D and T)")
    ap.add_argument("--case", nargs="*", default=None)
    ap.add_argument("--repo", default=None, help="the repository whose git objects hold 8bff03e (old-code reruns)")
    ap.add_argument("--no-mutants", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--keep", default=None, help="copy the temporary tree here (debugging)")
    a = ap.parse_args()
    if a.repo:
        OBJECTS["repo"] = os.path.abspath(a.repo)
    if a.list:
        for c in CASES.values():
            print(f"{c.id} [{c.group}] mutants {len(c.mutants)}: {c.doc}")
        sys.exit(0)
    sys.exit(run(a.case, mutants=not a.no_mutants, keep=a.keep))

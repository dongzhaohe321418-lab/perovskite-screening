#!/usr/bin/env python
"""S2 pw.x layer (results/objective2/s2/S2_PLAN.md sections 6, 7, 11-13 and 16; S2_BUILDERS_DESIGN.md section 11):
the S2 QE writer for single points and A2 relaxations, the X-unit charge rule and the valence-electron assertion, the
section-7 spin seed, the UPF identity check, the single-point and relaxation parsers with their read modes (the
blinding interface of section 17), the section-11 end rule and the step-0 equivalence check. Text and geometry only:
no calculator is created or evaluated here, and no CLI prints an energy of an S2 cell.

  writer    The scripts/30 fingerprint, unchanged (scripts/30 is not edited; its PSEUDO set plus the Cl and Ca files of
            PSEUDOPOTENTIALS_S2.md): plain PBE, 50/400 Ry (G1 rows _e60: 60/480 Ry), one k-point at supercell
            (1/2,1/2,1/2) (kpts (1,1,1), offset (1,1,1)), Gaussian smearing 0.005 Ry, nosym, conv_thr 1e-8 Ry,
            mixing_beta 0.3, electron_maxstep 200, tprnfor, no tstress, tot_charge always written. Single points:
            'scf', disk_io 'none'. A2 relaxations (s2r_, and the s2smoke_/s2tp_ rows of section 16): 'relax', BFGS,
            forc_conv_thr 7.8e-4 Ry/bohr, etot_conv_thr 1e-5 Ry, nstep from the caller (fixed by the C1 smoke tests,
            X-3), no restart_mode line (QE's default, a fresh start; X-B1), disk_io 'low', if_pos 0 0 0 on every atom
            outside R_j. A restart part is made only by restart_input: part 1 with the line restart_mode = 'restart'
            added and nstep changed, nothing else (section 13).
            Every written input is parsed back and checked line by line (namelists, species, k-points, cell,
            positions, if_pos flags, electron count) before it is renamed into place.
  charge    n_X = n(I) + n(Cl): 60 -> tot_charge 0; 59 -> +1, labels ending _q0 -> 0; anything else is refused, and
            the label must agree (vacancy label <-> 59). Valence electrons from z_valence: host 1070 and vacancy cells
            1063 before the charge, plus the dopant shift (Sr -4, Ca -4, Cl 0, Cs -10, GA +6); even except _q0 rows.
            The composition must equal the label's (host formula, minus I127 for a vacancy cell, plus the registry
            delta of the token); a ref232 row (s2tp_, s2smoke_) must be the stored 232-atom reference vacancy cell.
  spin      s2spin_ rows (section 7): nspin 2, starting_magnetization 0.1 for every species and 1/z_valence on the
            dopant (Cl 1/7, Ca 1/10), the dopant its own species; read back from the text, and rewritten explicitly
            if the ASE version wrote anything else.
  parsers   parse_sp: JOB DONE, "convergence has been achieved" with no "convergence NOT achieved" and exactly one
            "!" line; F, -TS and forces with scripts/32 parse_qe (last force block); E_F and the magnetisation with
            the scripts/37 regexes. parse_relax: every configuration k of the concatenated parts of one A2
            relaxation (k from QE's "number of scf cycles" counter, continuing across restarts), F(k), forces and
            positions (ASE espresso-out, as scripts/38, in the full read only); the text of the part that reaches
            k = k_cap is cut after the BFGS block of configuration k_cap, so nothing beyond it is read.
  modes     The read modes are the blinding interface. status and counts capture no value; k0 adds F(0); end_rule
            adds F(180) and F(200) only when configuration 200 exists; final_geom gives the positions of the last
            configuration (no energy regex runs); final adds its F; full reads everything. Every value read is
            counted in READS, and the self-test asserts per mode which counters move.
  end rule  section 11: QE convergence at k <= 200 accepted; at the cap accepted only if |F(200) - F(180)| <= 3 meV;
            a BFGS failure, an SCF failure or an nstep end before k = 200 is unconverged and never rerun; a soft exit
            or a killed part is incomplete (the runner restarts or reruns it, section 13).
  identity  The S1 UPFs carry no recorded sha256: their identity is the MD5 that every archived S1 output prints, one
            per element (I-25; s1_md5_table re-derives it); Cl and Ca are checked against the sha256 of
            PSEUDOPOTENTIALS_S2.md. Every output must print pw.x v.7.5 and the expected MPI rank count (I-26).
  mocks     synthetic_pw_output writes pw.x-like texts (no physics) for the self-tests here and the mock pw.x of
            scripts/50; they are read by the same parsers.

    python scripts/47_s2_qe.py --self-test [--work DIR]
    python scripts/47_s2_qe.py write --cell F.extxyz --label L --out DIR [--kind sp|relax] [--free F.json] [--nstep N]
        [--dopant-index I] [--ranks N]
    python scripts/47_s2_qe.py restart --input P1.in --out P2.in --nstep N
    python scripts/47_s2_qe.py status --dir JOBDIR --label L [--meta M.json]
    python scripts/47_s2_qe.py counts OUT [OUT ...]
    python scripts/47_s2_qe.py upf-check --pseudo-dir /data/pseudo --out F.json [--reference c1/upf_check.json]
"""
import argparse, collections, glob, gzip, hashlib, importlib.util, io, json, os, re, shutil, sys, tempfile, time
import traceback

import numpy as np
from ase.constraints import FixAtoms
from ase.data import atomic_masses, atomic_numbers
from ase.io import read as ase_read
from ase.io import espresso as ase_espresso
from ase.io.espresso import label_to_symbol, write_espresso_in

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


b42 = _load("b42", "42_s2_builders.py"); pp, s29 = b42.pp, b42.s29      # scripts/22, scripts/29 (one object each)
a30 = _load("a30", "30_qe_singlepoint.py")                              # PSEUDO, KMODES, write_input (fingerprint)
a37 = _load("a37", "37_dft_eb_analysis.py"); a32 = a37.a32              # scripts/37 loads scripts/32: one object


# ---------------------------------------------------------------- scripts/46 (labels, records, hygiene)
class _Stub46:
    """In-file stand-in for the scripts/46 names this module uses, used ONLY while scripts/46_s2_cells.py does not
    exist (interface spec section 1.2); the self-test then prints 'MOCKED c46'. Grammar as spec section 3.1."""
    IDX = r"(?:0|[1-9]\d*)"
    BODY = (r"(?P<host>m\d\d)_(?:"
            r"(?P<hostcell>host)(?:(?P<hL>[BAX])(?P<hj>" + IDX + r"))?"
            r"|V(?P<vL>[BAX])(?P<vj>" + IDX + r")"
            r"|(?P<tok>Sr|Ca|Cl|Cs|GA)(?P<j>" + IDX + r")o(?P<k>" + IDX + r")_(?P<leg>novac|vac))")
    LABEL_RE = re.compile(r"(?P<prefix>s2spin|s2g1|s2r|s2)_" + BODY + r"(?P<q0>_q0)?(?:_e(?P<ecut>50|60))?")
    WORK_RE = re.compile(r"s2_(?P<host>m\d\d|ref233)_(?:host|V[BAX]" + IDX +
                         r"|(?:Sr|Ca|Cl|Cs|GA)" + IDX + r"p" + IDX + r"_(?:novac|vac))")
    REF_RE = re.compile(r"(?P<prefix>s2tp|s2smoke)_ref232_(?P<name>[a-z0-9]+)")
    SUBLATTICE = {"Sr": "B", "Ca": "B", "Cl": "X", "Cs": "A", "GA": "A"}
    REF_NAMES = {"s2smoke": ("n1", "n3", "rst", "rst64", "rst2x32"), "s2tp": ("np48", "np64", "np32a", "np32b")}

    class S2Error(RuntimeError):
        """Fail-closed STOP (stand-in)."""

    # hygiene patterns of spec section 5.4, assembled so that this source file does not match them itself
    _HYG = [("local path", "/" + "Users/"), ("local path", "/" + "private/"), ("local path", "/" + "home/"),
            ("local path", r"(?<![\w.])/" + "tmp/"), ("work-area word", "scr" + "atch"), ("work-area word", "ve" + "nv"),
            ("IPv4 address", r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
            ("e-mail address", r"[\w.+-]+" + chr(64) + r"[\w-]+\.[\w.-]+"),
            ("instance or disk id", r"\b(?:i|d)-[0-9a-z]{10,}\b"),
            ("currency", "[" + "".join(map(chr, (0xA5, 0x24, 0x20AC, 0xA3, 0x5143))) + "]|\\b(?:"
             + "|".join(("U" "SD", "C" "NY", "R" "MB")) + ")\\b")]

    def __init__(self):
        self.S2Error = _Stub46.S2Error

    def check_label(self, label, sites=None):
        r = self.REF_RE.fullmatch(label)
        if r:
            if r["name"] not in self.REF_NAMES[r["prefix"]]:
                raise self.S2Error(f"{label}: unknown {r['prefix']} run name")
            return
        m = self.LABEL_RE.fullmatch(label)
        if not m:
            raise self.S2Error(f"{label!r} is not an S2 label")
        g = m.groupdict(); pre = g["prefix"]
        kind = "host" if g["hostcell"] else ("V" if g["vL"] else "dopant")
        vac = kind == "V" or g["leg"] == "vac"
        if g["q0"] and (pre != "s2" or not vac):
            raise self.S2Error(f"{label}: _q0 only on an s2_ V or _vac cell")
        if g["ecut"] and pre != "s2g1":
            raise self.S2Error(f"{label}: _e<cut> only on s2g1_ rows")
        if pre == "s2" and kind == "host" and g["hL"]:
            raise self.S2Error(f"{label}: s2_ host takes no site")
        if pre == "s2r" and kind == "host" and not g["hL"]:
            raise self.S2Error(f"{label}: s2r_ host needs its region site (I-7)")
        if pre == "s2r" and kind == "dopant" and g["k"] != "0":
            raise self.S2Error(f"{label}: A2 cells use the default pose only")
        if pre == "s2g1":
            ok = g["host"] == "m30" and ((kind == "host" and not g["hL"] and g["ecut"] == "60") or
                                         (g["tok"], g["j"], g["k"], g["leg"]) in (("Cl", "138", "0", "novac"),
                                                                                  ("Ca", "136", "0", "novac"))
                                         and g["ecut"] in ("50", "60"))
            if not ok:
                raise self.S2Error(f"{label}: not a G1 row")
        if pre == "s2spin" and not (g["host"] == "m30" and (g["tok"], g["j"], g["k"], g["leg"]) in
                                    (("Cl", "175", "0", "vac"), ("Ca", "76", "0", "vac"))):
            raise self.S2Error(f"{label}: not a spin row")
        if kind == "dopant" and g["k"] != "0" and g["tok"] not in ("Cs", "Cl"):
            raise self.S2Error(f"{label}: o<k> >= 1 only for multi-start tokens")

    @staticmethod
    def sha256_atoms(at):
        return hashlib.sha256(np.ascontiguousarray(at.positions).tobytes() +
                              np.ascontiguousarray(at.numbers).tobytes()).hexdigest()

    def hygiene_violations(self, text):
        return [f"{what}: {m.group(0)!r}" for what, rx in self._HYG for m in re.finditer(rx, text)]

    def dump_public(self, obj, path):
        bad = self.hygiene_violations(json.dumps(obj, indent=1))
        if bad:
            raise self.S2Error(f"refused to write {os.path.basename(path)}: {bad[:5]}")
        s29.dump_atomic(obj, path)


C46_NEEDS = ("LABEL_RE", "REF_RE", "S2Error", "check_label", "sha256_atoms", "dump_public", "hygiene_violations")


def _load46():
    """scripts/46 if it exists (its interface names must all be there: fail-closed), else the stub."""
    if os.path.exists(os.path.join(HERE, "46_s2_cells.py")):
        m = _load("c46", "46_s2_cells.py")
        missing = [n for n in C46_NEEDS if not hasattr(m, n)]
        if missing:
            raise ImportError(f"scripts/46_s2_cells.py lacks the interface names {missing}")
        return m, False
    return _Stub46(), True


c46, C46_MOCKED = _load46()
S2Error = c46.S2Error             # fail-closed STOP for a human
Refused = b42.Refused             # a request the writer refuses (wrong label, cell, count, flag)

# ---------------------------------------------------------------- constants (section 6; spec section 2.2)
PSEUDO_S1_PINNED = {"Pb": "Pb.pbe-dn-rrkjus_psl.1.0.0.UPF", "I": "I.pbe-n-rrkjus_psl.1.0.0.UPF",
                    "Cs": "Cs.pbe-spn-rrkjus_psl.1.0.0.UPF", "C": "C.pbe-n-rrkjus_psl.1.0.0.UPF",
                    "N": "N.pbe-n-rrkjus_psl.1.0.0.UPF", "H": "H.pbe-rrkjus_psl.1.0.0.UPF",
                    "Sr": "Sr.pbe-spn-rrkjus_psl.1.0.0.UPF"}          # literal copy of scripts/30 PSEUDO (asserted)
PSEUDO_S2 = {**a30.PSEUDO, "Cl": "Cl.pbe-n-rrkjus_psl.1.0.0.UPF", "Ca": "Ca.pbe-spn-rrkjus_psl.1.0.0.UPF"}
# PSEUDOPOTENTIALS_S2.md section 2 [R]; Cl and Ca are used, S and Rb only recorded
UPF_SHA256_S2 = {"Cl.pbe-n-rrkjus_psl.1.0.0.UPF": "6178e5e4ea26a81a2e8556f65f13c3ba282b75cc3df620746ac20d4a195b0513",
                 "S.pbe-n-rrkjus_psl.1.0.0.UPF": "90fb585e830674f2de7b4cbace28d5dd0c05ca1a919d1f92a59b54d6b95cbfc4",
                 "S.pbe-nl-rrkjus_psl.1.0.0.UPF": "4717a5314fa0fa53f6ee7542a50e7dfd44824a2f19f727c0f76f2205cae79deb",
                 "Ca.pbe-spn-rrkjus_psl.1.0.0.UPF": "60745cd19cb7c96ea734fe68ea89a54603d83eaaca19cb8b37deb3fc41fe9b43",
                 "Rb.pbe-spn-rrkjus_psl.1.0.0.UPF": "642852a379c2f212a7cd4205bd705cf2195b26f263ee2f14fe9a10dab824fa28"}
# I-25: the S1 files have no recorded sha256; their identity is the MD5 printed by every archived S1 output, one per
# element (pinned here from all 376 outputs under results/objective2/dopant_shell; the self-test re-derives it)
UPF_MD5_S1 = {"Pb": "1cf8f5e18580e6a90a35f98a53d336de", "I": "21b6b539e0050b62c62ace6be4e6e5e0",
              "C": "1fdd950c42eb37d8afe3dd2f8d12311e", "H": "3f4114867bd07edc7f1424d066fc1888",
              "N": "ada94e3ed05223de5319d0572dc76806", "Cs": "ce91a30752c48add39cf6ac6342f9330",
              "Sr": "062293b6b65f9744728f4999ca8ab72f"}
S1_ARCHIVE = "results/objective2/dopant_shell"
ZVAL = {e: b42.VALENCE[e] for e in ("Pb", "I", "C", "N", "H", "Cs", "Sr", "Cl", "Ca")}
ECUT, ECUT_G1 = (50.0, 400.0), (60.0, 480.0)          # Ry (sections 6, 7)
DEGAUSS, CONV_THR, MIXING_BETA, ELECTRON_MAXSTEP = 0.005, 1e-8, 0.3, 200
FORC_CONV_THR, ETOT_CONV_THR = 7.8e-4, 1e-5            # Ry/bohr, Ry (section 6; amendment b; the WP2e input)
KMODE = dict(a30.KMODES["R"])                          # kpts (1,1,1), koffset (1,1,1): the folded R point
KPTS_TEXT = "R (1,1,1) offset (1,1,1)"
PSEUDO_DIR, OUTDIR = "/data/pseudo", "./tmp"            # as scripts/30
N_EL_HOST, N_EL_VAC_NEUTRAL = 1070, 1063
DVAL = {"Sr": -4, "Ca": -4, "Cl": 0, "Cs": -10, "GA": 6}
NX_NOVAC, NX_VAC = 60, 59
BASE_COMPOSITION = {"Pb": 20, "I": 60, "C": 19, "N": 38, "H": 95, "Cs": 1}   # FA19Cs1Pb20I60, every pool member
SPIN_SEED = 0.1                                         # every species (S1 nspin-2 row)
SPIN_DOPANT = {"Cl": 1.0 / 7.0, "Ca": 1.0 / 10.0}       # 1/z_valence: about 1 muB on the dopant (section 7)
K_CAP, PLATEAU_FROM, PLATEAU_MEV = 200, 180, 3.0        # accept at the cap iff abs(F200 - F180) <= 3.0 meV
STEP0_TOL_MEV = 0.5                                     # pass iff abs(dF) <= 0.5 meV
RY_EV, BOHR_A = a32.RY, a32.BOHR                        # scripts/32 constants (13.605693122994 eV, 0.529177210903 A)
QE_UNITS = ase_espresso.units                           # the unit set ASE espresso-out uses (positions are compared
                                                        # with ASE bitwise; energies and forces use scripts/32 units)
QE_FRESH_START = "from_" + "scr" + "atch"               # QE's default restart_mode, spelled out only to recognise it
                                                        # (the hygiene scan flags the word, X-B1); never written
PW_VERSION = "7.5"                                      # required in every output (I-26)
RANKS_SP, RANKS_A2_DEFAULT = 64, 48                     # section 6
NSTEP_MAX = 1000                                        # sanity bound on the nstep the caller passes [N-B11]
EXIT_MARKERS = ("Program stopped by user request", "Maximum CPU time exceeded")   # QE soft exits [S]; the C1
                                                        # smoke test records the one pw.x 7.5 prints (mapping)
NSTEP_MARKER = "The maximum number of steps has been reached"
BFGS_FAIL_MARKERS = ("bfgs failed", "history already reset at previous step: stopping")   # [S], see N-B12
SCF_FAIL_MARKER = "convergence NOT achieved"
# QE's errore banner (error_handler.f90: a rule of '%', 'Error in routine <name> (<code>):', the message, a rule of
# '%', then 'stopping ...' and an MPI abort, so no JOB DONE): an end of pw.x without convergence (round-2 R2-QE-1)
ERROR_RX = re.compile(r"^ ?%{20,}[ \t]*\n[ \t]*Error in routine[ \t]+(\S+)[ \t]*\([ \t]*(-?\d+)[ \t]*\):[ \t]*\n[ \t]*(.*?)"
                      r"[ \t]*\n ?%{20,}", re.M)


def pw_error(text):
    """'<routine> (<code>): <message>' of the first QE error banner in text, or None. The message is reduced to word
    characters and simple punctuation, paths replaced, so that it can enter a public record."""
    m = ERROR_RX.search(text or "")
    if not m:
        return None
    msg = re.sub(r"/\S+", "<path>", m.group(3))
    msg = re.sub(r"[^\w .,:;()=+<>-]", "_", msg)
    msg = re.sub("scr" + "atch|v" + "env", "<w>", msg, flags=re.I)[:120]          # the hygiene word rule
    routine = re.sub(r"[^\w.]", "_", m.group(1))[:40]
    return f"{routine} ({int(m.group(2))}): {msg}"
REPEAT_POS_TOL_A, REPEAT_POS_TOL_HEADER_A, REPEAT_F_TOL_RY = 1e-6, 3e-6, 1e-6     # N-B7
READ_MODES = ("status", "counts", "k0", "end_rule", "final_geom", "final", "full")
KIND_OF_PREFIX = {"s2": "sp", "s2g1": "sp", "s2spin": "sp", "s2r": "relax", "s2smoke": "smoke", "s2tp": "tp"}
# reference-cell rows (section 16; spec 3.3): the four throughput runs; smoke runs at 48 ranks unless named
TP_RUNS = {"np48": 48, "np64": 64, "np32a": 32, "np32b": 32}
SMOKE_RANKS = {"rst64": 64, "rst2x32": 32}
REF_CELL_TOL_A = 1e-6                                   # N-B17: a ref232 row is the stored reference vacancy cell

NOTES = {
    "I-25": "section 6 UPF identity: S1 UPFs by the MD5 printed in every archived S1 output (one per element); Cl, Ca "
            "by the sha256 of PSEUDOPOTENTIALS_S2.md; z_valence against the registry; C2-C4 against the C1 sha256 record",
    "I-26": "section 6: every output must print pw.x v.7.5 and the expected MPI rank count, else S2Error (STOP)",
    "I-48": "section 11: a part that ends by nstep before k = 200 is unconverged early (not rerun) and STOPs "
            "(mapping wrong)",
    "X-3": "sections 11, 13, 16: nstep is a parameter of the writer and of restart_input; its values come from the C1 "
           "smoke-test mapping; the parser cuts at k = 200 whatever nstep was",
    "N-B1": "section 6 (silent): the composition must equal the label's (host formula, minus I127 if vacancy, plus the "
            "registry delta), in addition to the X-unit count and the electron count",
    "N-B2": "section 13 (silent): write_input writes only fresh starts (restart_mode None or QE's default value); a "
            "restart part is made only by restart_input, and only restart_mode and nstep may differ from part 1",
    "X-B1": "spec 5.4 vs QE: the hygiene word rule matches QE's default restart_mode value (the word 'from_' + "
            "'scr' + 'atch'); part 1 therefore writes no restart_mode line (QE default, a fresh start: the same "
            "calculation), restart_input adds the line restart_mode = 'restart' and changes nstep (section 13: "
            "differs only in restart_mode and nstep), and records give restart_mode null for a fresh start. The "
            "spec's a2 record field restart_mode = <that word> (spec 4.5) cannot pass dump_public either",
    "N-B4": "section 11 (silent on precedence): end class of a part: converged > cap > soft exit > nstep > pw.x error "
            "routine (QE's errore banner, round-2 R2-QE-1) > BFGS failure > SCF failure > other JOB DONE end > killed; "
            "a pw.x error end is unconverged early (section 11: 'any other end without QE convergence ... is not "
            "rerun') and STOPs for a human, who rules out an infrastructure cause; a JOB DONE end without a known "
            "marker is unconverged early and STOPs for a human (never rerun)",
    "N-B5": "sections 6, 11, 13: a configuration counts only with its '!' line and a complete force block (nat rows and "
            "'Total force'); a trailing incomplete configuration is not counted (the interrupted one is not completed)",
    "N-B6": "section 13: the part that reaches k = 200 is cut after configuration 200's BFGS block (before the "
            "ATOMIC_POSITIONS of configuration 201); nothing after the cut is processed, markers included",
    "N-B7": "spec 7.2 (repeat tolerance): QE prints header positions at 7 decimals in alat units, so a repeated "
            "restart configuration is compared at 1e-6 A between ATOMIC_POSITIONS blocks and at 3e-6 A when a copy "
            "comes from a header block (spec: 1e-6 A flat); F at 1e-6 Ry, only in the full read",
    "N-B8": "section 12: queue states qe_queue.sh does not leave (.gaveup beside .out, .gaveup without .out.try1 and "
            ".out.try2, .out.try2 beside .out without .gaveup, .out.try3, outputs without the input) STOP (S2Error); "
            "a snapshot taken while the queue moves files is read again (3 times, 0.5 s apart) first, and .out.try1 + "
            ".out.try2 without .out and .gaveup (the queue's state between its mv and touch) is missing once it "
            "persists, with gaveup_pending, so the runner writes .gaveup (round-2 R2-QE-2)",
    "N-B9": "section 6: the printed electron count must equal the input's, the printed MD5 of each S1 element must "
            "equal UPF_MD5_S1 (Cl, Ca: the C1-recorded MD5, md5_extra) and the output must name its input "
            "(<label>.in; A2 part n: <label>.p<n>.in), else STOP; the runner (scripts/50) passes md5_extra at every "
            "read, and the electron count and the label at every read of a single-point or A2 output (and of the "
            "smoke restart test), so each such output is checked once on the node (round-2 R2-QE-3); smoke and "
            "throughput outputs are of the reference cell; scripts/48 and 49 re-read outputs the runner has checked",
    "N-B10": "section 17 (blinding): read modes counted in READS; ASE espresso-out only in the full read; final_geom "
             "uses this module's ATOMIC_POSITIONS/header parser, equal to ASE at every WP2e configuration (self-test)",
    "N-B11": "sections 6, 16: s2_/s2g1_/s2spin_ are single points, s2r_/s2smoke_/s2tp_ relaxations; nstep must be "
             "an int in 1..1000; dopant_index only (and always) for s2spin_",
    "N-B16": "section 16 (spec 3.3): throughput rows only s2tp_ref232_{np48, np64, np32a, np32b}, each at its own "
             "rank count (np32a/b: 32, np64: 64, np48: 48); smoke rows any REF_RE name, at 48 ranks except rst64 "
             "(64) and rst2x32 (32) or an explicit count",
    "N-B17": "header and section 16: a ref232 row (s2tp_, s2smoke_) must be the stored reference vacancy cell "
             "(results/fa_host/fa19cspb20i59_232_vI.extxyz: numbers and cell equal, positions within 1e-6 A); a pool "
             "member's V cell has the same composition, so the composition check alone cannot keep S2 cells out",
    "N-B18": "section 15 residual forces (round-3 R3C-5): the full read of a single point gives, for the free atoms, "
             "the per-atom force norms (norms_eVA, in the order of their indices) beside RMS and max",
    "N-B12": "section 11: the BFGS-failure texts are the QE messages as known, not seen in a pw.x 7.5 output; an end "
             "with JOB DONE and no known marker is caught by N-B4",
    "N-B13": "section 13: k comes from 'number of scf cycles' (k = N - 1) or 'bfgs converged in N scf cycles'; a later "
             "part must continue at k_last + 1 (or repeat k_last if the smoke mapping says so, both copies equal), "
             "else the parts are unusable and the relaxation reruns from k = 0; parts after a final end STOP",
    "N-B14": "section 6 (silent): one label, one input: write_input refuses to replace an existing <label>.in whose "
             "normalised text differs (rewriting the identical input is allowed)",
    "N-B15": "section 6: ATOMIC_SPECIES carries ASE's default masses (as every S1 input), whatever masses the cell "
             "carries; masses do not enter scf or BFGS",
    "I-B1": "section 6: tot_charge is written explicitly in every input, also 0.0 (as scripts/30 writes it)",
    "I-B2": "section 7: 'the dopant atom is its own species' is met by requiring the dopant element to occur exactly "
            "once in the spin cell; refused otherwise",
    "I-B3": "section 6: the MD5 that pw.x prints is the md5 of the UPF file bytes (QE md5_from_file); upf_check uses "
            "hashlib md5 [I]; every output's printed MD5 is also checked by the runner (N-B9)",
    "I-B4": "section 11: a relaxation whose configuration 200 is complete is judged by the cap rule whatever ended "
            "the part (the driver's exit file at k = 200)",
}

READS = collections.Counter()      # every value read by a parser: F, TS, forces, positions, fermi, mag, ase


# ---------------------------------------------------------------- labels
def label_info(label):
    """Fields of an S2 QE label (grammar and semantic checks of scripts/46, plus the writer's own rules)."""
    m = c46.LABEL_RE.fullmatch(label)
    if m or c46.REF_RE.fullmatch(label):
        c46.check_label(label)
    if m:
        g = m.groupdict(); pre = g["prefix"]
        if g["hostcell"]:
            ck, L, j, tok = "host", g["hL"], g["hj"], None
        elif g["vL"]:
            ck, L, j, tok = "V", g["vL"], g["vj"], None
        else:
            tok = g["tok"]; ck = "D" if g["leg"] == "novac" else "DV"
            L, j = b42.REGISTRY[tok]["site"], g["j"]
        info = {"label": label, "prefix": pre, "kind": KIND_OF_PREFIX[pre], "host": g["host"], "cell_kind": ck,
                "sublattice": L, "site": int(j) if j is not None else None, "token": tok,
                "k": int(g["k"]) if g["k"] is not None else None, "leg": g["leg"],
                "vacancy": ck in ("V", "DV"), "q0": bool(g["q0"]), "ecut": int(g["ecut"]) if g["ecut"] else None,
                "ref": None}
    else:
        m = c46.REF_RE.fullmatch(label)
        if not m:
            raise Refused(f"{label!r} is neither an S2 cell label nor a reference-cell label")
        pre = m.group("prefix")
        if pre == "s2tp" and m.group("name") not in TP_RUNS:
            raise Refused(f"{label}: the throughput rows are {sorted(TP_RUNS)} (section 16; N-B16)")
        info = {"label": label, "prefix": pre, "kind": KIND_OF_PREFIX[pre], "host": "ref232", "cell_kind": "ref232",
                "sublattice": None, "site": None, "token": None, "k": None, "leg": None, "vacancy": True,
                "q0": False, "ecut": None, "ref": m.group("name")}
    # the writer's own rules (fail-closed even if a scripts/46 check were looser)
    if info["q0"] and (info["prefix"] != "s2" or not info["vacancy"]):
        raise Refused(f"{label}: _q0 only on an s2_ vacancy cell (section 10)")
    if (info["ecut"] is not None) != (info["prefix"] == "s2g1"):
        raise Refused(f"{label}: _e50/_e60 exactly on the s2g1_ rows (section 7)")
    if info["prefix"] == "s2g1" and (info["vacancy"] or info["host"] != "m30"):
        raise Refused(f"{label}: G1 cells are vacancy-free m30 cells (section 7)")
    if info["prefix"] == "s2spin" and not (info["cell_kind"] == "DV" and info["token"] in SPIN_DOPANT
                                           and info["host"] == "m30"):
        raise Refused(f"{label}: spin rows are m30 Cl or Ca D+V cells (section 7)")
    if info["prefix"] == "s2r" and (info["q0"] or (info["k"] not in (None, 0))):
        raise Refused(f"{label}: A2 cells are q = +1 default-pose cells (section 11)")
    return info


def charge_class(info):
    """tot_charge implied by the label: vacancy cells +1 (section 1), _q0 rows 0 (section 10), others 0."""
    return 1 if info["vacancy"] and not info["q0"] else 0


def expected_electrons(info):
    base = N_EL_VAC_NEUTRAL if info["vacancy"] else N_EL_HOST
    return base + (DVAL[info["token"]] if info["token"] else 0) - charge_class(info)


def expected_composition(info):
    comp = dict(BASE_COMPOSITION)
    if info["vacancy"]:
        comp["I"] -= 1
    if info["token"]:
        for e, d in b42.REGISTRY[info["token"]]["delta"].items():
            comp[e] = comp.get(e, 0) + d
    return {e: n for e, n in comp.items() if n}


# ---------------------------------------------------------------- writer: counts, charge, electrons
def composition(atoms):
    return dict(collections.Counter(atoms.get_chemical_symbols()))


def n_x(atoms):
    """X-site units n(I) + n(Cl) (section 6; never count('I') == 59)."""
    s = atoms.get_chemical_symbols()
    return s.count("I") + s.count("Cl")


def charge_for(atoms, label):
    """tot_charge from the X-unit count (section 6), refused unless the label agrees."""
    info = label_info(label)
    nx = n_x(atoms)
    if nx == NX_NOVAC:
        if info["q0"]:
            raise Refused(f"{label}: _q0 on a vacancy-free cell ({nx} X units)")
        q = 0
    elif nx == NX_VAC:
        q = 0 if info["q0"] else 1
    else:
        raise Refused(f"{label}: {nx} X units (60 or 59 required)")
    if info["vacancy"] != (nx == NX_VAC):
        raise Refused(f"{label}: the label says {'a vacancy' if info['vacancy'] else 'no vacancy'}, the cell has "
                      f"{nx} X units")
    if info["prefix"] == "s2g1" and nx != NX_NOVAC:
        raise Refused(f"{label}: s2g1_ cells are vacancy-free")
    if info["prefix"] == "s2spin" and nx != NX_VAC:
        raise Refused(f"{label}: s2spin_ cells are vacancy cells")
    if q != charge_class(info):
        raise Refused(f"{label}: charge {q} from the cell differs from the label's {charge_class(info)}")
    return q


def electrons(atoms, label):
    """Valence-electron bookkeeping (section 6): z_sum - tot_charge must equal the label's expectation; even unless
    _q0 (then odd). Refused otherwise."""
    info = label_info(label)
    unknown = sorted(set(atoms.get_chemical_symbols()) - set(ZVAL))
    if unknown:
        raise Refused(f"{label}: no z_valence for {unknown}")
    z = int(sum(ZVAL[s] for s in atoms.get_chemical_symbols()))
    q = charge_for(atoms, label)
    n_el, exp = z - q, expected_electrons(info)
    if n_el != exp:
        raise Refused(f"{label}: {n_el} valence electrons, expected {exp}")
    even = n_el % 2 == 0
    if even == info["q0"]:
        raise Refused(f"{label}: {n_el} electrons is {'even' if even else 'odd'}; only _q0 rows are odd")
    return {"z_sum": z, "tot_charge": q, "n_el": n_el, "expected": exp, "even": even}


def check_composition(atoms, label):
    """N-B1: the cell's composition equals the label's."""
    info = label_info(label)
    got, exp = composition(atoms), expected_composition(info)
    if got != exp:
        raise Refused(f"{label}: composition {got} differs from the label's {exp}")
    return got


def settings_for(label, kind):
    """The section-6 settings implied by the label (tot_charge from the label class; nstep, n_fixed and the spin seed
    are filled in by write_input)."""
    info = label_info(label)
    if kind not in ("sp", "relax"):
        raise Refused(f"kind must be 'sp' or 'relax', not {kind!r}")
    want = "sp" if info["kind"] == "sp" else "relax"
    if kind != want:
        raise Refused(f"{label}: a {info['prefix']}_ label is a {want} job, not {kind} (N-B11)")
    ec = ECUT_G1 if info["ecut"] == 60 else ECUT
    s = {"calculation": "scf" if kind == "sp" else "relax", "ecutwfc": ec[0], "ecutrho": ec[1], "kpts": KPTS_TEXT,
         "occupations": "smearing", "smearing": "gaussian", "degauss": DEGAUSS,
         "nspin": 2 if info["prefix"] == "s2spin" else 1, "tot_charge": charge_class(info), "nosym": True,
         "conv_thr": CONV_THR, "mixing_beta": MIXING_BETA, "electron_maxstep": ELECTRON_MAXSTEP,
         "tprnfor": True, "tstress": False, "disk_io": "none" if kind == "sp" else "low", "verbosity": "low",
         "outdir": OUTDIR, "pseudo_dir": PSEUDO_DIR, "relax": None, "starting_magnetization": None}
    if kind == "relax":
        s["relax"] = {"ion_dynamics": "bfgs", "forc_conv_thr": FORC_CONV_THR, "etot_conv_thr": ETOT_CONV_THR,
                      "nstep": None, "restart_mode": None, "n_fixed": None}      # None: QE default (X-B1)
    return s


def _input_data(prefix, s):
    """Namelists as scripts/30 write_input builds them, plus the S2 relax settings."""
    d = {"control": {"calculation": s["calculation"], "prefix": prefix, "pseudo_dir": s["pseudo_dir"],
                     "outdir": s["outdir"], "tprnfor": s["tprnfor"], "tstress": s["tstress"], "disk_io": s["disk_io"],
                     "verbosity": s["verbosity"]},
         "system": {"ecutwfc": float(s["ecutwfc"]), "ecutrho": float(s["ecutrho"]), "occupations": s["occupations"],
                    "smearing": s["smearing"], "degauss": float(s["degauss"]), "nspin": int(s["nspin"]),
                    "nosym": s["nosym"], "tot_charge": float(s["tot_charge"])},
         "electrons": {"conv_thr": float(s["conv_thr"]), "mixing_beta": float(s["mixing_beta"]),
                       "electron_maxstep": int(s["electron_maxstep"])}}
    if s["relax"]:
        r = s["relax"]
        d["control"].update({"forc_conv_thr": float(r["forc_conv_thr"]), "etot_conv_thr": float(r["etot_conv_thr"]),
                             "nstep": int(r["nstep"])})
        if r["restart_mode"] is not None:                 # never set by write_input (X-B1, N-B2)
            d["control"]["restart_mode"] = r["restart_mode"]
        d["ions"] = {"ion_dynamics": r["ion_dynamics"]}
    return d


def _render(atoms, prefix, s, *, free=None, magmoms=None):
    """pw.x input text for a copy of atoms (calc dropped, tags 0, constraints only from free, moments only if given)."""
    x = atoms.copy(); x.calc = None; x.set_constraint(); x.set_tags([0] * len(x)); x.set_masses()   # default masses
    x.set_initial_magnetic_moments(magmoms)
    if s["relax"]:
        fixed = sorted(set(range(len(x))) - set(free))
        if fixed:
            x.set_constraint(FixAtoms(indices=fixed))
    species = sorted(set(x.get_chemical_symbols()))
    unknown = [e for e in species if e not in PSEUDO_S2]
    if unknown:
        raise Refused(f"no S2 pseudopotential for {unknown}")
    buf = io.StringIO()
    write_espresso_in(buf, x, input_data=_input_data(prefix, s), pseudopotentials={e: PSEUDO_S2[e] for e in species},
                      **KMODE)
    return buf.getvalue()


# ---------------------------------------------------------------- writer: parse back and verify
def _nl_value(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] == "'":
        return v[1:-1]
    if v.lower() in (".true.", ".false."):
        return v.lower() == ".true."
    if re.fullmatch(r"[-+]?\d+", v):
        return int(v)
    return float(v.replace("d", "e").replace("D", "e"))


CARDS = ("ATOMIC_SPECIES", "K_POINTS", "CELL_PARAMETERS", "ATOMIC_POSITIONS")


def parse_input_text(text):
    """Namelists (dicts, keys lower case) and cards (header + rows of tokens) of a pw.x input."""
    nl, cards, cur = {}, {}, None
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if cur is not None:
            if s == "/":
                cur = None
            elif s:
                k, eq, v = s.partition("=")
                if not eq:
                    raise Refused(f"namelist &{cur.upper()}: line without '=': {s!r}")
                k = k.strip().lower()
                if k in nl[cur]:
                    raise Refused(f"namelist &{cur.upper()}: {k} given twice")
                nl[cur][k] = _nl_value(v)
        elif s.startswith("&"):
            cur = s[1:].strip().lower()
            if cur in nl:
                raise Refused(f"namelist &{cur.upper()} given twice")
            nl[cur] = {}
        elif s:
            head = s.split()[0]
            if head not in CARDS or head in cards:
                raise Refused(f"unexpected line in a pw.x input: {s!r}")
            rows = []; i += 1
            while i < len(lines) and lines[i].strip():
                rows.append(lines[i].split()); i += 1
            cards[head] = {"header": " ".join(s.split()), "rows": rows}
            continue
        i += 1
    if cur is not None:
        raise Refused(f"namelist &{cur.upper()} not closed")
    return {"namelists": nl, "cards": cards}


def _same(a, b):
    return type(a) is type(b) and a == b


def expected_namelists(prefix, s, nat, ntyp, mags=None):
    """Every namelist value the S2 writer must produce (nothing else may appear)."""
    d = _input_data(prefix, s)
    nl = {"control": dict(d["control"]), "system": dict(d["system"]), "electrons": dict(d["electrons"]),
          "ions": dict(d.get("ions", {})), "cell": {}, "fcp": {}, "rism": {}}
    nl["system"].update({"ntyp": int(ntyp), "nat": int(nat), "ibrav": 0})
    for i, v in enumerate(mags or [], 1):
        nl["system"][f"starting_magnetization({i})"] = float(v)
    return nl


def verify_input_text(text, label, prefix, s, atoms, *, free=None, mag_by_element=None, n_el=None):
    """Re-parse a written input and check it line by line against the settings, the cell and the electron count.
    Returns the list of checks done; raises Refused on the first difference."""
    p = parse_input_text(text)
    nl, cards = p["namelists"], p["cards"]
    if set(cards) != set(CARDS):
        raise Refused(f"{label}: cards {sorted(cards)}")
    species = cards["ATOMIC_SPECIES"]["rows"]
    if any(len(r) != 3 for r in species):
        raise Refused(f"{label}: ATOMIC_SPECIES rows {species}")
    sp_el = [label_to_symbol(r[0]) for r in species]
    mags = None
    if s["nspin"] == 2:
        mags = [mag_by_element[e] for e in sp_el]
    elif mag_by_element:
        raise Refused(f"{label}: a magnetisation for an nspin-1 input")
    exp = expected_namelists(prefix, s, len(atoms), len(species), mags)
    if set(nl) != set(exp):
        raise Refused(f"{label}: namelists {sorted(nl)} != {sorted(exp)}")
    for name, want in exp.items():
        got = nl[name]
        if set(got) != set(want):
            raise Refused(f"{label}: &{name.upper()} keys differ: extra {sorted(set(got) - set(want))}, "
                          f"missing {sorted(set(want) - set(got))}")
        bad = [(k, got[k], want[k]) for k in want if not _same(got[k], want[k])]
        if bad:
            raise Refused(f"{label}: &{name.upper()} values differ: {bad}")
    # species: one per element (the spin dopant is its own element), the S2 pseudopotential and the cell's mass
    if len(set(sp_el)) != len(sp_el) or set(sp_el) != set(atoms.get_chemical_symbols()):
        raise Refused(f"{label}: species {sp_el} for elements {sorted(set(atoms.get_chemical_symbols()))}")
    for (lab, m, pseudo), e in zip(species, sp_el):          # ASE default masses, as every S1 input
        if pseudo != PSEUDO_S2[e] or abs(float(m) - atomic_masses[atomic_numbers[e]]) > 1e-9:
            raise Refused(f"{label}: species line {lab} {m} {pseudo}")
    k = cards["K_POINTS"]
    if k["header"] != "K_POINTS automatic" or k["rows"] != [["1", "1", "1", "1", "1", "1"]]:
        raise Refused(f"{label}: K_POINTS {k}")
    c = cards["CELL_PARAMETERS"]
    if c["header"] != "CELL_PARAMETERS angstrom" or len(c["rows"]) != 3 or \
            np.abs(np.array(c["rows"], float) - atoms.cell.array).max() > 1e-12:
        raise Refused(f"{label}: CELL_PARAMETERS differ from the cell")
    a = cards["ATOMIC_POSITIONS"]
    if a["header"] != "ATOMIC_POSITIONS angstrom" or len(a["rows"]) != len(atoms):
        raise Refused(f"{label}: ATOMIC_POSITIONS header or row count")
    syms = [label_to_symbol(r[0]) for r in a["rows"]]
    if syms != atoms.get_chemical_symbols():
        raise Refused(f"{label}: species order of ATOMIC_POSITIONS differs from the cell")
    pos = np.array([r[1:4] for r in a["rows"]], float)
    if np.abs(pos - atoms.positions).max() > 1e-9:
        raise Refused(f"{label}: positions differ from the cell by {np.abs(pos - atoms.positions).max():.2e} A")
    fixed = set(range(len(atoms))) - set(free) if s["relax"] else set()
    for i, r in enumerate(a["rows"]):
        want = ["0", "0", "0"] if i in fixed else []
        if r[4:] != want:
            raise Refused(f"{label}: atom {i} if_pos {r[4:]} (expected {want or 'none'})")
    if s["nspin"] == 2:          # the label of each atom's species carries its intended moment
        lab_of = {r[0]: e for r, e in zip(species, sp_el)}
        if {r[0] for r in a["rows"]} - set(lab_of):
            raise Refused(f"{label}: an atom with an undeclared species label")
    z = sum(ZVAL[e] for e in syms)
    q = nl["system"]["tot_charge"]
    if n_el is not None and z - q != n_el:
        raise Refused(f"{label}: the written input carries {z - q} electrons, expected {n_el}")
    return ["namelists", "species", "k_points", "cell", "positions", "if_pos", "electrons"]


def _fix_magnetization(text, mags):
    """Rewrite the starting_magnetization lines of &SYSTEM explicitly (section 7: 'whatever the ASE version')."""
    out, in_sys, done = [], False, False
    for ln in text.splitlines(keepends=True):
        st = ln.strip()
        if st.upper() == "&SYSTEM":
            in_sys = True
        elif in_sys and st == "/":
            in_sys = False
        if in_sys and re.match(r"\s*starting_magnetization\(\d+\)\s*=", ln):
            continue
        out.append(ln)
        if in_sys and not done and re.match(r"\s*nspin\s*=", ln):
            out += [f"   {f'starting_magnetization({i})':16} = {float(v)!r}\n" for i, v in enumerate(mags, 1)]
            done = True
    if not done:
        raise Refused("no nspin line in &SYSTEM to anchor the starting_magnetization lines")
    return "".join(out)


def _norm_sha256_text(text):
    keep = [re.sub(r"\s+", " ", ln.strip()) for ln in text.splitlines() if not re.match(r"\s*pseudo_dir\s*=", ln)]
    return hashlib.sha256("\n".join(x for x in keep if x).encode()).hexdigest()


def input_norm_sha256(path):
    """sha256 of a pw.x input without its pseudo_dir line and with blank runs collapsed (as scripts/40: run_qe.sh
    rewrites pseudo_dir in place on the node)."""
    return _norm_sha256_text(a32.read_text(path))


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _script_sha256():
    return _sha256_file(os.path.abspath(__file__))


def _ranks_for(info, ranks):
    if info["prefix"] == "s2tp" or info["ref"] in SMOKE_RANKS:
        n = (TP_RUNS if info["prefix"] == "s2tp" else SMOKE_RANKS)[info["ref"]]
        if ranks is not None and ranks != n:
            raise Refused(f"{info['label']}: runs at {n} ranks, not {ranks} (N-B16)")
        return n
    if ranks is not None:
        return int(ranks)
    return RANKS_SP if info["kind"] == "sp" else RANKS_A2_DEFAULT


_REF232 = []


def check_reference_cell(atoms, label):
    """N-B17: a ref232 row is the stored 232-atom reference vacancy cell, nothing else."""
    if not _REF232:
        r = ase_read(os.path.join(ROOT, b42.VAC_REF)); r.calc = None
        _REF232.append(r)
    ref = _REF232[0]
    ok = (len(atoms) == len(ref) and np.array_equal(atoms.numbers, ref.numbers)
          and np.abs(atoms.cell.array - ref.cell.array).max() <= 1e-9
          and np.abs(atoms.positions - ref.positions).max() <= REF_CELL_TOL_A)
    if not ok:
        raise Refused(f"{label}: a ref232 row must be the stored reference vacancy cell (N-B17)")


def write_input(atoms, label, outdir, *, kind="sp", free=None, nstep=None, restart_mode=None,
                dopant_index=None, ranks=None, campaign=None, cell=None):
    """Write <outdir>/<label>.in and <label>.meta.json (s2-qejob-1) for one S2 QE job. Every check is fail-closed
    (Refused). restart_mode: None or QE's default value only (a fresh start; X-B1). Returns the meta record."""
    if restart_mode == QE_FRESH_START:
        restart_mode = None
    info = label_info(label)
    if b42.out_is_forbidden(outdir):
        raise Refused(f"S2 outputs are never written under {b42.FORBIDDEN_OUT} (section 5)")
    s = settings_for(label, kind)
    ranks_expected = _ranks_for(info, ranks)
    if info["cell_kind"] == "ref232":
        check_reference_cell(atoms, label)
    comp = check_composition(atoms, label)
    el = electrons(atoms, label)
    if el["tot_charge"] != s["tot_charge"]:
        raise Refused(f"{label}: charge bookkeeping differs")
    n = len(atoms)
    if s["relax"]:
        if restart_mode is not None:
            raise Refused(f"{label}: a restart part is made only by restart_input (N-B2)")
        if not isinstance(nstep, (int, np.integer)) or isinstance(nstep, bool) or not 1 <= int(nstep) <= NSTEP_MAX:
            raise Refused(f"{label}: a relaxation needs an int nstep in 1..{NSTEP_MAX} (X-3), not {nstep!r}")
        if free is None:
            raise Refused(f"{label}: a relaxation needs its free region (if_pos 0 0 0 outside R_j)")
        fr = [int(i) for i in free]
        if not fr or len(set(fr)) != len(fr) or min(fr) < 0 or max(fr) >= n:
            raise Refused(f"{label}: free indices must be unique and within 0..{n - 1}")
        free = sorted(fr)
        s["relax"].update({"nstep": int(nstep), "n_fixed": n - len(free)})
    elif free is not None or nstep is not None or restart_mode is not None:
        raise Refused(f"{label}: a single point takes no free region, nstep or restart_mode")
    magmoms, mag_el = None, None
    if s["nspin"] == 2:
        tok = info["token"]
        if dopant_index is None or not 0 <= int(dopant_index) < n or atoms[int(dopant_index)].symbol != tok:
            raise Refused(f"{label}: dopant_index must name the {tok} atom")
        if atoms.get_chemical_symbols().count(tok) != 1:
            raise Refused(f"{label}: the dopant element must occur once, so it is its own species (I-B2)")
        magmoms = [SPIN_SEED] * n
        magmoms[int(dopant_index)] = SPIN_DOPANT[tok]
        mag_el = {e: (SPIN_DOPANT[tok] if e == tok else SPIN_SEED) for e in set(atoms.get_chemical_symbols())}
        s["starting_magnetization"] = dict(sorted(mag_el.items()))
    elif dopant_index is not None:
        raise Refused(f"{label}: dopant_index applies only to s2spin_ rows")
    text = _render(atoms, label, s, free=free, magmoms=magmoms)
    rewritten = False
    if mag_el is not None:
        p = parse_input_text(text)
        sp_el = [label_to_symbol(r[0]) for r in p["cards"]["ATOMIC_SPECIES"]["rows"]]
        got = [p["namelists"]["system"].get(f"starting_magnetization({i})") for i in range(1, len(sp_el) + 1)]
        want = [mag_el[e] for e in sp_el]
        if got != want:                                   # an ASE that scales or drops the moments
            text = _fix_magnetization(text, want); rewritten = True
    verify_input_text(text, label, label, s, atoms, free=free, mag_by_element=mag_el, n_el=el["n_el"])
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"{label}.in")
    if os.path.exists(path) and input_norm_sha256(path) != _norm_sha256_text(text):
        raise Refused(f"{label}: {label}.in exists with other content; one label, one input (N-B14)")
    with open(path + ".part", "w") as fh:            # '.part' matches no qe_queue.sh glob
        fh.write(text); fh.flush(); os.fsync(fh.fileno())
    os.replace(path + ".part", path)
    x = atoms.copy(); x.calc = None
    meta = {"schema": "s2-qejob-1", "label": label, "kind": info["kind"], "campaign": campaign,
            "parsed_label": info, "cell": cell,
            "settings": {k: v for k, v in s.items() if k not in ("verbosity", "outdir", "pseudo_dir")},
            "composition": dict(sorted(comp.items())), "n_X": n_x(atoms), "vacancy": info["vacancy"],
            "electrons": el,
            "pseudopotentials": {e: {"file": PSEUDO_S2[e], "sha256_expected": UPF_SHA256_S2.get(PSEUDO_S2[e]),
                                     "md5_expected": UPF_MD5_S1.get(e)} for e in sorted(comp)},
            "starting_magnetization_rewritten": rewritten,
            "input_sha256": _sha256_file(path), "input_norm_sha256": input_norm_sha256(path),
            "geometry_sha256": c46.sha256_atoms(x), "ranks_expected": ranks_expected,
            "writer": {"script_sha256": _script_sha256(), "builder": b42.BUILDER_VERSION},
            "queue": None, "result": None}
    c46.dump_public(meta, os.path.join(outdir, f"{label}.meta.json"))
    return meta


def restart_input(src_in, dst_in, nstep_new):
    """Restart part of an A2 relaxation (section 13): the original part-1 input (a fresh start: no restart_mode line,
    X-B1) with the line restart_mode = 'restart' added after its calculation line and nstep = nstep_new; asserts
    that nothing else differs (text and namelists)."""
    if not isinstance(nstep_new, (int, np.integer)) or isinstance(nstep_new, bool) or \
            not 1 <= int(nstep_new) <= NSTEP_MAX:
        raise Refused(f"nstep must be an int in 1..{NSTEP_MAX}, not {nstep_new!r}")
    src = a32.read_text(src_in)
    p = parse_input_text(src)["namelists"]
    if p.get("control", {}).get("calculation") != "relax" or "restart_mode" in p["control"]:
        raise Refused("the source must be a part-1 relax input (a fresh start, no restart_mode line)")
    lines = src.splitlines(keepends=True)
    ca = [i for i, ln in enumerate(lines) if re.match(r"\s*calculation\s*=", ln)]
    ns = [i for i, ln in enumerate(lines) if re.match(r"\s*nstep\s*=", ln)]
    if len(ca) != 1 or len(ns) != 1:
        raise Refused("the source needs exactly one calculation and one nstep line")
    body = list(lines)
    body[ns[0]] = re.sub(r"=\s*\d+", f"= {int(nstep_new)}", lines[ns[0]], count=1)
    new = body[:ca[0] + 1] + [f"   {'restart_mode':16} = 'restart'\n"] + body[ca[0] + 1:]
    changed = [i for i, (x, y) in enumerate(zip(lines, body)) if x != y]
    if not set(changed) <= {ns[0]} or len(new) != len(lines) + 1:
        raise Refused(f"restart input differs from part 1 in lines {changed}")
    q = parse_input_text("".join(new))["namelists"]
    diff = sorted((nm, k) for nm in set(p) | set(q) for k in set(p.get(nm, {})) | set(q.get(nm, {}))
                  if not _same(p.get(nm, {}).get(k), q.get(nm, {}).get(k)))
    if not set(diff) <= {("control", "restart_mode"), ("control", "nstep")} or ("control", "restart_mode") not in diff:
        raise Refused(f"restart input differs in {diff}")
    with open(dst_in + ".part", "w") as fh:
        fh.write("".join(new)); fh.flush(); os.fsync(fh.fileno())
    os.replace(dst_in + ".part", dst_in)
    return {"src_sha256": hashlib.sha256(src.encode()).hexdigest(), "dst_sha256": _sha256_file(dst_in),
            "dst_norm_sha256": input_norm_sha256(dst_in), "added_line": ca[0] + 2,
            "changed_lines": [i + 1 for i in changed], "restart_mode": "restart", "nstep": int(nstep_new)}


# ---------------------------------------------------------------- output parsing: markers (capture no value)
RX = {
    "bang": re.compile(r"^!\s+total energy\s+=", re.M),                       # locates a '!' line only
    "force_row": re.compile(r"^\s*atom\s+\d+\s+type\s+\d+\s+force\s+=", re.M),  # counted, values not captured
    "scf_cycles": re.compile(r"number of scf cycles\s+=\s+(\d+)"),
    "bfgs_steps": re.compile(r"number of bfgs steps\s+=\s+(\d+)"),
    "bfgs_conv": re.compile(r"bfgs converged in\s+(\d+)\s+scf cycles and\s+(\d+)\s+bfgs steps"),
    "version": re.compile(r"Program PWSCF v\.(\S+) starts"),
    "mpi": re.compile(r"Number of MPI processes:\s+(\d+)"),
    "nat": re.compile(r"number of atoms/cell\s+=\s+(\d+)"),
    "nel": re.compile(r"number of electrons\s+=\s+([\d.]+)"),
    "input": re.compile(r"Reading input from\s+(\S+)"),
    "wall": re.compile(r"PWSCF\s+:\s+(.*?)CPU\s+(.*?)WALL"),
    "celldm": re.compile(r"celldm\(1\)=\s*(\S+)"),
    "md5": re.compile(r"PseudoPot\. #\s*\d+ for\s+(\S+)\s+read from file:\s*\n\s*(\S+)\s*\n\s*MD5 check sum:\s*(\S+)"),
    "tau": re.compile(r"\s*\d+\s*(\S+)\s*tau\(\s*\d+\)\s*=\s*\(\s*(\S+)\s+(\S+)\s+(\S+)\s*\)"),
}
# value regexes: every call is counted in READS (the blinding audit of the self-test)
ENERGY_RX = {
    "F": re.compile(r"!\s+total energy\s+=\s+([-\d.]+)\s+Ry"),
    "fermi": re.compile(r"the Fermi energy is\s+([-\d.]+)\s+ev"),                    # scripts/37
    "mag_total": re.compile(r"total magnetization\s+=\s+([-\d.]+)\s+Bohr"),          # scripts/37
    "mag_abs": re.compile(r"absolute magnetization\s+=\s+([-\d.]+)\s+Bohr"),
    "force_vals": re.compile(r"atom\s+\d+\s+type\s+\d+\s+force =\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)"),  # scripts/32
}


def _qe_seconds(s):
    """QE clock string ('1d 5h 1m', '24m44.08s', '7m 2.34s', '40.12s') in seconds."""
    m = re.fullmatch(r"\s*(?:(\d+)d)?\s*(?:(\d+)h)?\s*(?:(\d+)m)?\s*(?:([\d.]+)s)?\s*", s or "")
    if not m or not any(m.groups()):
        return None
    d, h, mi, se = (float(x) if x else 0.0 for x in m.groups())
    return ((d * 24 + h) * 60 + mi) * 60 + se


def _header(txt):
    """Header and status fields of one pw.x output (markers and counts, no energy)."""
    g = {k: RX[k].search(txt) for k in ("version", "mpi", "nat", "nel", "input", "celldm")}
    md5, files = {}, {}
    for el, path, cks in RX["md5"].findall(txt):
        if md5.get(el, cks) != cks:
            raise S2Error(f"two MD5 sums for {el} in one output")
        md5[el], files[el] = cks, os.path.basename(path)
    w = RX["wall"].findall(txt)
    return {"pw_version": g["version"].group(1) if g["version"] else None,
            "mpi_processes": int(g["mpi"].group(1)) if g["mpi"] else None,
            "nat": int(g["nat"].group(1)) if g["nat"] else None,
            "n_electrons_printed": float(g["nel"].group(1)) if g["nel"] else None,
            "input_name": g["input"].group(1) if g["input"] else None,
            "celldm1": g["celldm"].group(1) if g["celldm"] else None,
            "upf_md5": md5, "upf_files": files, "job_done": "JOB DONE" in txt,
            "wall_s": _qe_seconds(w[-1][1]) if w else None}


def _check_header(h, *, ranks=None, where="", md5_extra=None):
    """I-26 and N-B9: version, ranks and the printed UPF identities of one output; S2Error (STOP) on a mismatch."""
    if h["pw_version"] is not None and h["pw_version"] != PW_VERSION:
        raise S2Error(f"{where}: pw.x v.{h['pw_version']}, S2 requires v.{PW_VERSION} (I-26)")
    if ranks is not None and h["mpi_processes"] is not None and h["mpi_processes"] != int(ranks):
        raise S2Error(f"{where}: {h['mpi_processes']} MPI processes, expected {ranks} (I-26)")
    for el, cks in h["upf_md5"].items():
        if h["upf_files"].get(el) != PSEUDO_S2.get(el):
            raise S2Error(f"{where}: {el} read from {h['upf_files'].get(el)}, not {PSEUDO_S2.get(el)}")
        want = UPF_MD5_S1.get(el) or (md5_extra or {}).get(el)
        if want is not None and cks != want:
            raise S2Error(f"{where}: {el} MD5 {cks} != {want} (UPF identity, I-25)")


def _read_F(txt, pos):
    READS["F"] += 1
    m = ENERGY_RX["F"].match(txt, pos)
    if not m:
        raise S2Error("no '!' energy at a configuration start")
    return float(m.group(1))


def _read_forces(txt, f, t):
    READS["forces"] += 1
    rows = ENERGY_RX["force_vals"].findall(txt, f, t)
    return np.array(rows, float)                      # Ry/bohr


def _positions(txt, w0, b, hdr):
    """Positions (A) and symbols of the configuration whose '!' line is at b: the last ATOMIC_POSITIONS block or
    header 'positions (alat units)' block in [w0, b). Same arithmetic as ASE espresso-out."""
    READS["positions"] += 1
    nat = hdr["nat"]
    a, h = txt.rfind("ATOMIC_POSITIONS", w0, b), txt.rfind("positions (alat units)", w0, b)
    if a < 0 and h < 0:
        raise S2Error("no positions before a configuration")
    if a > h:
        lines = txt[a:b].splitlines()
        if "angstrom" not in lines[0].lower():
            raise S2Error(f"positions not in angstrom: {lines[0]!r}")
        rows = [ln.split() for ln in lines[1:1 + nat]]
        sym = [label_to_symbol(r[0]) for r in rows]
        pos = np.array([[float(x) for x in r[1:4]] for r in rows]) @ np.identity(3)
        return sym, pos, "atomic_positions"
    alat = float(hdr["celldm1"]) * QE_UNITS["Bohr"]
    rows = [RX["tau"].match(ln) for ln in txt[h:b].splitlines()[1:1 + nat]]
    if any(r is None for r in rows):
        raise S2Error("malformed header positions")
    sym = [label_to_symbol(r.group(1)) for r in rows]
    pos = np.array([[float(r.group(i)) * alat for i in (2, 3, 4)] for r in rows])
    return sym, pos, "header"


def _segment(txt, nat):
    """Complete configurations of one part (N-B5), with their offsets, counters and convergence flags (markers only).
    own_end: the end of the configuration's BFGS block (the next ATOMIC_POSITIONS outside the final-coordinates
    block, else the next '!' line, else the end of the text)."""
    bangs = [m.start() for m in RX["bang"].finditer(txt)]
    cfg, incomplete = [], []
    prev_end = 0
    for i, b in enumerate(bangs):
        nxt = bangs[i + 1] if i + 1 < len(bangs) else len(txt)
        f = txt.find("Forces acting on atoms", b, nxt)
        t = txt.find("Total force", f, nxt) if f >= 0 else -1
        rows = len(RX["force_row"].findall(txt, f, t)) if t >= 0 else -1
        if nat is None or t < 0 or rows != nat:
            incomplete.append(i); continue
        tend = txt.find("\n", t)
        tend = nxt if tend < 0 or tend > nxt else tend
        a = txt.find("ATOMIC_POSITIONS", tend, nxt)
        if a >= 0 and txt.find("Begin final coordinates", tend, a) < 0:
            own_end = a
        else:
            own_end = nxt
        c = RX["scf_cycles"].search(txt, tend, own_end); s = RX["bfgs_steps"].search(txt, tend, own_end)
        v = RX["bfgs_conv"].search(txt, tend, own_end)
        counter = int(c.group(1)) if c else (int(v.group(1)) if v else None)
        bsteps = int(s.group(1)) if s else (int(v.group(2)) if v else None)
        cfg.append({"bang": b, "forces": (f, t), "own_end": own_end, "window": (prev_end, b), "counter": counter,
                    "bfgs_steps": bsteps, "converged": v is not None})
        prev_end = own_end
    if incomplete and incomplete != list(range(len(bangs) - len(incomplete), len(bangs))):
        raise S2Error(f"an incomplete configuration before a complete one (positions {incomplete})")
    return cfg, len(incomplete)


def _end_class(scan, converged, cap, exit_markers):
    """N-B4: end class of one part from its (cut) text."""
    if converged:
        return "converged", "bfgs converged"
    if cap:
        return "cap", None
    for mk in exit_markers:
        if mk in scan:
            return "exit_stop", mk
    if NSTEP_MARKER in scan:
        return "nstep", NSTEP_MARKER
    pe = pw_error(scan)
    if pe is not None:
        return "pw_error", pe
    for mk in BFGS_FAIL_MARKERS:
        if mk in scan:
            return "bfgs_failed", mk
    if SCF_FAIL_MARKER in scan:
        return "scf_failed", SCF_FAIL_MARKER
    if "JOB DONE" in scan:
        return "other_end", "JOB DONE"
    return "killed", None


FINAL_ENDS = ("converged", "bfgs_failed", "scf_failed", "nstep", "other_end", "pw_error")


def parse_relax(parts, *, read="full", k_cap=K_CAP, mapping=None, ranks=None, md5_extra=None, n_el=None, label=None):
    """The configurations of one A2 relaxation from its part outputs, in order (section 6). read selects what is
    read (module docstring, 'modes'); mapping is the C1 smoke-test mapping (restart_continues_counters,
    restart_repeats_last, exit_marker); ranks the expected MPI rank count of every part; n_el the electron count of
    the input (meta electrons.n_el), md5_extra the C1-recorded MD5 of Cl and Ca, and label the relaxation's label
    (part n must name <label>.p<n>.in), each checked against every part's header when given (N-B9)."""
    if read not in READ_MODES:
        raise ValueError(f"read must be one of {READ_MODES}")
    if not parts:
        raise ValueError("no part")
    mp = dict(mapping or {})
    cont = mp.get("restart_continues_counters", True) is not False
    rep = bool(mp.get("restart_repeats_last", False))
    exit_markers = (mp["exit_marker"],) if mp.get("exit_marker") else EXIT_MARKERS
    out = {"read": read, "k_cap": k_cap, "usable": True, "unusable_reason": None, "parts": [], "ks": [],
           "repeats": [], "cap_reached": False, "qe_converged": False, "converged_at_k": None, "last_end": None}
    texts, hdrs, glob_cfg = [], [], []        # glob_cfg: (part index, cfg) of the unique configurations
    k_last, prev_end, stop = None, None, False

    def unusable(why):
        out["usable"], out["unusable_reason"] = False, why

    for p, path in enumerate(parts):
        if p > 0 and (stop or prev_end in FINAL_ENDS):    # the runner never continues a finished relaxation
            raise S2Error(f"part {p + 1} follows a part that ended '{prev_end}' (N-B13)")
        if p > 0 and k_last is None:
            unusable(f"part {p + 1} follows a part without a complete configuration"); break
        txt = a32.read_text(path)
        hdr = _header(txt)
        _check_header(hdr, ranks=ranks, where=f"part {p + 1}", md5_extra=md5_extra)
        if label is not None and hdr["input_name"] is not None and \
                os.path.basename(hdr["input_name"]) != f"{label}.p{p + 1}.in":
            raise S2Error(f"part {p + 1}: the output read {hdr['input_name']}, not {label}.p{p + 1}.in (N-B9)")
        if n_el is not None and hdr["n_electrons_printed"] is not None and \
                abs(hdr["n_electrons_printed"] - n_el) > 1e-6:
            raise S2Error(f"part {p + 1}: pw.x counted {hdr['n_electrons_printed']} electrons, the input {n_el} (N-B9)")
        cfg, n_inc = _segment(txt, hdr["nat"])
        if cfg and hdr["pw_version"] is None:
            raise S2Error(f"part {p + 1}: configurations without a pw.x header")
        cut, kept = None, []
        for i, c in enumerate(cfg):
            k = i if p == 0 else (k_last + i if rep else k_last + 1 + i)
            if c["counter"] is not None:
                if p == 0 or cont:                        # QE's counter continues across restarts (N-B13)
                    if c["counter"] - 1 != k:
                        unusable(f"part {p + 1}: QE counter gives k = {c['counter'] - 1}, order gives k = {k}")
                        break
                elif cfg[0]["counter"] is None or c["counter"] - cfg[0]["counter"] != i:
                    unusable(f"part {p + 1}: QE counters are not consecutive within the part")
                    break
            kept.append(dict(c, k=k))
            if k >= k_cap:                                # N-B6: nothing after configuration k_cap is processed
                cut = c["own_end"]; out["cap_reached"] = True; stop = True
                break
        if not out["usable"]:
            out["parts"].append({"n": p + 1, "n_config": len(cfg)}); break
        scan = txt[:cut] if cut is not None else txt
        conv = [c for c in kept if c["converged"]]
        end, marker = _end_class(scan, bool(conv), cut is not None, exit_markers)
        if conv:
            if conv[0] is not kept[-1]:
                raise S2Error(f"part {p + 1}: configurations after 'bfgs converged'")
            out["qe_converged"], out["converged_at_k"] = True, conv[0]["k"]
            stop = True
        first, last = (kept[0] if kept else None), (kept[-1] if kept else None)
        out["parts"].append({
            "n": p + 1, "n_config": len(kept), "k_first": first["k"] if first else None,
            "k_last": last["k"] if last else None, "end": end, "end_marker": marker, "job_done": "JOB DONE" in scan,
            "exit_marker_seen": any(mk in scan for mk in exit_markers), "incomplete_trailing": n_inc,
            "cut_at_cap": cut is not None, "pw_version": hdr["pw_version"], "mpi_processes": hdr["mpi_processes"],
            "nat": hdr["nat"], "wall_s": hdr["wall_s"] if cut is None else None,
            "counters_first": {"scf_cycles": first["counter"], "bfgs_steps": first["bfgs_steps"]} if first else None,
            "counters_last": {"scf_cycles": last["counter"], "bfgs_steps": last["bfgs_steps"]} if last else None})
        texts.append(scan); hdrs.append(hdr)
        pi = len(texts) - 1
        if p > 0 and rep and kept:
            if kept[0]["k"] != k_last:
                unusable(f"part {p + 1}: the repeated configuration is k = {kept[0]['k']}, not {k_last}")
                break
            rec = {"part": p + 1, "k": k_last, "verified_positions": None, "verified_F": None}
            if read not in ("status", "counts"):
                pj, cj = glob_cfg[-1]
                s1, x1, src1 = _positions(texts[pj], *cj["window"], hdrs[pj])
                s2, x2, src2 = _positions(scan, *kept[0]["window"], hdr)
                tol = REPEAT_POS_TOL_A if src1 == src2 == "atomic_positions" else REPEAT_POS_TOL_HEADER_A
                dx = float(np.abs(x1 - x2).max()) if s1 == s2 else float("inf")
                rec["verified_positions"] = dx <= tol; rec["max_dr_A"] = dx
                if read == "full":
                    dF = abs(_read_F(texts[pj], cj["bang"]) - _read_F(scan, kept[0]["bang"]))
                    rec["verified_F"] = dF <= REPEAT_F_TOL_RY
                if rec["verified_positions"] is False or rec["verified_F"] is False:
                    out["repeats"].append(rec)
                    unusable(f"part {p + 1}: the repeated configuration k = {k_last} differs from part {p}")
                    break
            out["repeats"].append(rec)
            kept = kept[1:]
        for c in kept:
            glob_cfg.append((pi, c))
        if kept:
            k_last = kept[-1]["k"]
        prev_end = end
        out["last_end"] = end
    out["ks"] = [c["k"] for _, c in glob_cfg]
    out["n_config"] = len(glob_cfg)
    out["k_first"] = out["ks"][0] if glob_cfg else None
    out["k_last"] = out["ks"][-1] if glob_cfg else None
    if out["usable"] and out["ks"] != list(range(len(out["ks"]))):
        unusable(f"configurations are not k = 0, 1, ...: {out['ks'][:5]}...")
    if not out["usable"] or read in ("status", "counts"):
        return out
    by_k = {c["k"]: (pi, c) for pi, c in glob_cfg}
    F_at = lambda k: _read_F(texts[by_k[k][0]], by_k[k][1]["bang"])
    if read == "k0" and 0 in by_k:
        out["F_Ry"] = {0: F_at(0)}
    elif read == "end_rule" and out["k_last"] is not None and out["k_last"] >= k_cap:
        out["F_Ry"] = {k_cap - (K_CAP - PLATEAU_FROM): F_at(k_cap - (K_CAP - PLATEAU_FROM)), k_cap: F_at(k_cap)}
    elif read in ("final_geom", "final") and glob_cfg:
        pi, c = glob_cfg[-1]
        sym, pos, _ = _positions(texts[pi], *c["window"], hdrs[pi])
        out.update({"symbols": sym, "positions_A": {c["k"]: pos}})
        if read == "final":
            out["F_Ry"] = {c["k"]: F_at(c["k"])}
    elif read == "full":
        _full(out, texts, hdrs, glob_cfg)
    if "F_Ry" in out:
        out["F_eV"] = {k: v * RY_EV for k, v in out["F_Ry"].items()}
    return out


def _full(out, texts, hdrs, glob_cfg):
    """Every F(k), force and position; positions from ASE espresso-out (as scripts/38), checked against the module's
    own parser and its F and forces against ASE's."""
    F, Fo, X = {}, {}, {}
    by_part = collections.defaultdict(list)
    for pi, c in glob_cfg:
        by_part[pi].append(c)
    sym0 = None
    for pi, cs in sorted(by_part.items()):
        txt, hdr = texts[pi], hdrs[pi]
        READS["ase"] += 1
        imgs = [a for a in ase_read(io.StringIO(txt[:cs[-1]["own_end"]]), index=":", format="espresso-out")
                if a.calc is not None and a.calc.results.get("energy") is not None]
        imgs = imgs[-len(cs):] if len(imgs) >= len(cs) else imgs   # a repeated configuration precedes the kept ones
        if len(imgs) != len(cs):
            raise S2Error(f"ASE finds {len(imgs)} configurations in a part, this parser {len(cs)}")
        for c, im in zip(cs, imgs):
            k = c["k"]
            F[k] = _read_F(txt, c["bang"])
            f = _read_forces(txt, *c["forces"])
            sym, pos, _ = _positions(txt, *c["window"], hdr)
            if abs(im.calc.results["energy"] / QE_UNITS["Ry"] - F[k]) > 1e-9:
                raise S2Error(f"k = {k}: ASE and this parser differ in F")
            if np.abs(im.get_forces() / (QE_UNITS["Ry"] / QE_UNITS["Bohr"]) - f).max() > 1e-9:
                raise S2Error(f"k = {k}: ASE and this parser differ in the forces")
            if im.get_chemical_symbols() != sym or np.abs(im.positions - pos).max() > 1e-10:
                raise S2Error(f"k = {k}: ASE and this parser differ in the positions")
            Fo[k] = f * RY_EV / BOHR_A
            X[k] = im.positions.copy()
            sym0 = sym0 or sym
    out.update({"F_Ry": F, "forces_eVA": Fo, "positions_A": X, "symbols": sym0})


def end_rule(rel):
    """Section 11 end rule on a parse_relax result (read end_rule, final or full)."""
    if rel.get("k_cap") != K_CAP:
        raise S2Error(f"the end rule is defined at k_cap = {K_CAP}, not {rel.get('k_cap')}")
    if not rel["usable"]:
        return {"outcome": "incomplete", "action": "rerun_from_zero", "reason": rel["unusable_reason"],
                "dF_200_180_meV": None, "stop": False}
    if rel["qe_converged"] and rel["converged_at_k"] is not None and rel["converged_at_k"] <= K_CAP:
        return {"outcome": "accepted_converged", "converged_at_k": rel["converged_at_k"], "dF_200_180_meV": None,
                "stop": False}
    if rel["k_last"] is not None and rel["k_last"] >= K_CAP:          # I-B4: the cap rule, whatever ended the part
        F = rel.get("F_eV") or {}
        if PLATEAU_FROM not in F or K_CAP not in F:
            raise S2Error("the cap rule needs F(180) and F(200): parse with read='end_rule', 'final' or 'full'")
        d = (F[K_CAP] - F[PLATEAU_FROM]) * 1000.0
        ok = abs(d) <= PLATEAU_MEV
        return {"outcome": "accepted_plateau" if ok else "unconverged_cap", "dF_200_180_meV": d, "stop": False}
    last = rel["last_end"]
    if last in ("bfgs_failed", "scf_failed", "nstep", "other_end", "pw_error"):
        mk = ((rel.get("parts") or [{}])[-1] or {}).get("end_marker")
        return {"outcome": "unconverged_early", "end": last, "k_last": rel["k_last"], "dF_200_180_meV": None,
                "stop": last in ("nstep", "other_end", "pw_error"),
                "reason": {"nstep": "nstep end before k = 200: the nstep mapping is wrong (I-48)",
                           "other_end": "JOB DONE without a known end marker (N-B4)",
                           "pw_error": f"pw.x error routine {mk} (section 11: unconverged, not rerun; a human rules "
                                       f"out an infrastructure cause, N-B4)"}.get(last)}
    return {"outcome": "incomplete", "action": "restart_or_rerun", "end": last, "k_last": rel["k_last"],
            "dF_200_180_meV": None, "stop": False}


def step0_equivalence(F_sp_eV, F_k0_eV):
    """Section 11 step-0 check: |F(k = 0) - F(single point)| <= 0.5 meV."""
    d = (float(F_k0_eV) - float(F_sp_eV)) * 1000.0
    return {"dF_meV": d, "passed": abs(d) <= STEP0_TOL_MEV, "tol_meV": STEP0_TOL_MEV}


def parse_counts(path, *, mapping=None, ranks=None, md5_extra=None):
    """Smoke-test and throughput outputs (section 16): counts, counters, end markers and wall times; no value."""
    before = dict(READS)
    r = parse_relax([path], read="counts", mapping=mapping, ranks=ranks, md5_extra=md5_extra)
    assert dict(READS) == before, "parse_counts captured a value"
    part = r["parts"][0] if r["parts"] else {}
    return {"n_config": r["n_config"], "usable": r["usable"], **{k: part.get(k) for k in
            ("k_first", "k_last", "end", "end_marker", "job_done", "exit_marker_seen", "wall_s", "pw_version",
             "mpi_processes", "counters_first", "counters_last", "incomplete_trailing")}}


# ---------------------------------------------------------------- single points
def parse_sp(path, *, read="full", free=None):
    """One single-point output (section 6). status: markers only; full: F (scripts/32 parse_qe), -TS, forces (last
    block), E_F (scripts/37), total and absolute magnetisation (last printed)."""
    if read not in ("status", "full"):
        raise ValueError("read must be 'status' or 'full'")
    txt = a32.read_text(path)
    h = _header(txt)
    nb = len(RX["bang"].findall(txt))
    conv = "convergence has been achieved" in txt and SCF_FAIL_MARKER not in txt and nb == 1
    out = {**h, "n_bang": nb, "scf_converged": conv}
    if read == "status":
        return out
    READS["F"] += 1; READS["TS"] += 1; READS["forces"] += 1
    q = a32.parse_qe(path)
    def last(rx):
        READS[rx] += 1
        v = ENERGY_RX[rx].findall(txt)
        return float(v[-1]) if v else None
    out.update({"F_eV": None, "F_Ry": None, "mTS_eV": None, "forces": None})
    if q is not None:
        out.update({"F_eV": q["F_eV"], "F_Ry": q["F_eV"] / RY_EV if q["F_eV"] is not None else None,
                    "mTS_eV": q["mTS_eV"]})
        if q["forces"] is not None:
            n = np.linalg.norm(q["forces"], axis=1)
            summ = lambda idx: {"rms_eVA": float(np.sqrt(np.mean(n[idx] ** 2))), "max_eVA": float(n[idx].max()),
                                "n": int(len(idx))}
            fr = np.asarray(sorted(free), int) if free is not None else None
            out["forces"] = {"all": summ(np.arange(len(n))),
                             "free": {**summ(fr), "indices": [int(i) for i in fr],                      # N-B18
                                      "norms_eVA": [float(x) for x in n[fr]]} if fr is not None else None}
            out["forces_eVA"] = q["forces"]
    out.update({"E_F_eV": last("fermi"), "M_total_muB": last("mag_total"), "M_abs_muB": last("mag_abs")})
    return out


def _found(base, suffix):
    have = [p for p in (base + suffix, base + suffix + ".gz") if os.path.exists(p)]
    if len(have) > 1:
        raise S2Error(f"both {os.path.basename(have[0])} and its .gz exist")
    return have[0] if have else None


class _QueueMoving(Exception):
    """A file snapshot of a single point taken while qe_queue.sh moved its files (round-2 R2-QE-2)."""


def sp_status(job_dir, label, *, meta=None, running=False, ranks=None, md5_extra=None, retries=3, retry_s=0.5):
    """Section 12 completeness of one single point from <label>.out, <label>.out.try<n>, <label>.gaveup (plain or
    .gz, node or archive layout): complete | missing (reason) | pending | running. Status read only.
    qe_queue.sh moves files while it runs (.out -> .out.try<n> after a failed attempt; after the second, touch
    .gaveup): a snapshot taken during a move (a file gone between two reads, or a state the queue passes through) is
    taken again, up to `retries` times retry_s apart, before the N-B8 rules apply. .out.try1 + .out.try2 without
    .out and .gaveup that persists (the node stopped between the queue's mv and touch) is missing with gaveup_pending
    True: the runner writes .gaveup, so the queue never starts a third attempt (round-2 R2-QE-2)."""
    base = os.path.join(job_dir, label)
    for i in range(int(retries) + 1):
        try:
            return _sp_status_once(base, label, meta=meta, running=running, ranks=ranks, md5_extra=md5_extra,
                                   last=i == int(retries))
        except (_QueueMoving, FileNotFoundError) as e:
            if i == int(retries):
                raise S2Error(f"{label}: the single point's files changed during {i + 1} reads "
                              f"({type(e).__name__}; N-B8)")
            time.sleep(retry_s)


def _sp_status_once(base, label, *, meta, running, ranks, md5_extra, last):
    def inconsistent(msg):                          # N-B8 only on the last snapshot; before it, read again
        raise S2Error(msg) if last else _QueueMoving(msg)
    inp, out = _found(base, ".in"), _found(base, ".out")
    gave = os.path.exists(base + ".gaveup")
    tries = {}
    for f in glob.glob(glob.escape(base) + ".out.try*"):
        m = re.fullmatch(re.escape(os.path.basename(base)) + r"\.out\.try(\d+)(\.gz)?", os.path.basename(f))
        if not m:
            raise S2Error(f"unexpected file {os.path.basename(f)}")
        if int(m.group(1)) in tries:
            raise S2Error(f"{label}: try{m.group(1)} twice")
        tries[int(m.group(1))] = f
    if out is not None and not os.path.exists(out):
        raise _QueueMoving(f"{label}: the output moved during the snapshot")
    if not gave and os.path.exists(base + ".gaveup"):
        raise _QueueMoving(f"{label}: .gaveup appeared during the snapshot")
    rk = ranks if ranks is not None else (meta or {}).get("ranks_expected", RANKS_SP)
    res = {"label": label, "status": None, "missing_reason": None, "attempts": [os.path.basename(tries[k])
           for k in sorted(tries)], "gaveup": gave, "job_done": None, "scf_converged": None}
    if (out or tries or gave) and inp is None:
        raise S2Error(f"{label}: outputs without the input (N-B8)")
    if meta is not None and inp is not None and input_norm_sha256(inp) != meta["input_norm_sha256"]:
        raise S2Error(f"{label}: the input is not the one of its meta record")
    for k, f in sorted(tries.items()):              # every attempt must be of the right program and layout
        _check_header(_header(a32.read_text(f)), ranks=rk, where=f"{label} try{k}", md5_extra=md5_extra)
    if gave:
        if out is not None or sorted(tries) != [1, 2]:
            inconsistent(f"{label}: .gaveup with .out {out is not None} and tries {sorted(tries)}: a state "
                         f"qe_queue.sh does not leave (N-B8)")
        res.update(status="missing", missing_reason="no JOB DONE after one resubmission")
        return res
    if sorted(tries) == [1, 2] and out is None:
        # the queue's state between 'mv .out .out.try2' and 'touch .gaveup': transient; if it persists the node
        # stopped between the two commands, and the second failure is final (section 12)
        if not last:
            raise _QueueMoving(f"{label}: tries [1, 2] without .gaveup")
        res.update(status="missing", missing_reason="no JOB DONE after one resubmission (.gaveup not written by the "
                                                    "queue)", gaveup_pending=True)
        return res
    if sorted(tries) not in ([], [1]):
        inconsistent(f"{label}: tries {sorted(tries)} without .gaveup (N-B8)")
    if out is None:
        res["status"] = "running" if running else "pending"
        return res
    st = parse_sp(out, read="status")
    _check_header(st, ranks=rk, where=label, md5_extra=md5_extra)
    res.update({k: st[k] for k in ("job_done", "scf_converged", "pw_version", "mpi_processes", "n_electrons_printed",
                                   "upf_md5", "wall_s", "n_bang")})
    if not st["job_done"]:
        res["status"] = "running" if running else "pending"      # the queue reruns it once (section 12)
        return res
    if st["input_name"] is not None and os.path.basename(st["input_name"]) != f"{label}.in":
        raise S2Error(f"{label}: the output read {st['input_name']} (N-B9)")
    if meta is not None and st["n_electrons_printed"] is not None and \
            abs(st["n_electrons_printed"] - meta["electrons"]["n_el"]) > 1e-6:
        raise S2Error(f"{label}: pw.x counted {st['n_electrons_printed']} electrons, the input "
                      f"{meta['electrons']['n_el']} (N-B9)")
    if st["scf_converged"]:
        res["status"] = "complete"
    else:
        res.update(status="missing", missing_reason="SCF not converged (JOB DONE)")   # D3: not rerun
    return res


# ---------------------------------------------------------------- UPF identity (I-25)
def _upf_zval(data):
    t = data[:20000].decode("utf-8", "replace")
    m = re.search(r'z_valence\s*=\s*"\s*([-+0-9.EeDd]+)\s*"', t) or re.search(r"^\s*([-+0-9.EeDd]+)\s+Z valence", t, re.M)
    return float(m.group(1).replace("D", "E").replace("d", "e")) if m else None


def upf_check(pseudo_dir, *, reference=None, reference_name=None, md5_s1=None, sha256_s2=None):
    """Before the first pw.x job of every campaign (section 6): sha256, md5 and z_valence of every UPF S2 uses;
    S1 files against UPF_MD5_S1, Cl and Ca against UPF_SHA256_S2, z_valence against ZVAL; with reference (the C1
    record) every sha256 must equal it. Returns s2-upf-1 (no path); passed False stops the campaign."""
    md5_s1 = UPF_MD5_S1 if md5_s1 is None else md5_s1
    sha256_s2 = UPF_SHA256_S2 if sha256_s2 is None else sha256_s2
    files, ok = {}, True
    for el, fn in sorted(PSEUDO_S2.items()):
        p = os.path.join(pseudo_dir, fn)
        r = {"file": fn, "sha256": None, "md5": None, "z_valence": None,
             "expected": {"z_valence": ZVAL[el]}, "passed": False, "reasons": []}
        if el in md5_s1:
            r["expected"]["md5"] = md5_s1[el]
        else:
            r["expected"]["sha256"] = sha256_s2.get(fn)
        if not os.path.isfile(p):
            r["reasons"].append("missing")
        else:
            data = open(p, "rb").read()
            r.update(sha256=hashlib.sha256(data).hexdigest(), md5=hashlib.md5(data).hexdigest(),
                     z_valence=_upf_zval(data))
            if "md5" in r["expected"] and r["md5"] != r["expected"]["md5"]:
                r["reasons"].append("md5 differs from the S1 outputs")
            if "sha256" in r["expected"] and r["sha256"] != r["expected"]["sha256"]:
                r["reasons"].append("sha256 differs from PSEUDOPOTENTIALS_S2.md")
            if r["z_valence"] is None or abs(r["z_valence"] - ZVAL[el]) > 1e-9:
                r["reasons"].append(f"z_valence {r['z_valence']} != {ZVAL[el]}")
            if reference is not None:
                ref = reference.get("files", {}).get(el, {}).get("sha256")
                r["expected"]["sha256_reference"] = ref
                if ref is None or ref != r["sha256"]:
                    r["reasons"].append("sha256 differs from the C1 record")
        r["passed"] = not r["reasons"]
        ok &= r["passed"]
        files[el] = r
    return {"schema": "s2-upf-1", "files": files, "reference_sha256_from": reference_name if reference else None,
            "passed": bool(ok)}


def upf_md5_extra(record):
    """{element: md5} of the S2 files (Cl, Ca) from a passed s2-upf-1 record: the md5_extra against which sp_status,
    parse_relax and parse_counts check an output's printed MD5 when the caller passes it (the runner passes it at every
    read, N-B9)."""
    if not record or not record.get("passed"):
        raise S2Error("the UPF check record did not pass")
    return {el: record["files"][el]["md5"] for el in ("Cl", "Ca")}


def s1_md5_table(archive_root=S1_ARCHIVE):
    """The MD5 that every archived S1 output prints, per element; S2Error unless one per element and the file is the
    scripts/30 one."""
    root = os.path.join(ROOT, archive_root) if not os.path.isabs(archive_root) else archive_root
    paths = sorted(set(glob.glob(os.path.join(root, "**", "*.out*"), recursive=True)))
    paths = [p for p in paths if re.search(r"\.out(\.try\d+)?(\.gz)?\Z", p)]
    tab, n = collections.defaultdict(collections.Counter), 0
    for p in paths:
        op = gzip.open if p.endswith(".gz") else open
        head = []
        with op(p, "rt", errors="replace") as fh:
            for i, ln in enumerate(fh):
                head.append(ln)
                if "Starting wfc" in ln or "Initial potential" in ln or i > 5000:
                    break
        n += 1
        for el, path, cks in RX["md5"].findall("".join(head)):
            if os.path.basename(path) != a30.PSEUDO.get(el):
                raise S2Error(f"S1 output read {os.path.basename(path)} for {el}")
            tab[el][cks] += 1
    multi = {el: dict(c) for el, c in tab.items() if len(c) != 1}
    if multi:
        raise S2Error(f"S1 outputs print more than one MD5 for {multi}")
    return {"n_outputs": n, "elements": {el: {"md5": next(iter(c)), "n_outputs": sum(c.values())}
                                         for el, c in sorted(tab.items())}}


def sha256_table_from_note(path="results/objective2/s2/PSEUDOPOTENTIALS_S2.md"):
    """file -> (element, sha256, z_valence) from the section-2 table of PSEUDOPOTENTIALS_S2.md."""
    t = open(os.path.join(ROOT, path)).read()
    rows = re.findall(r"^\|\s*`([^`]+\.UPF)`\s*\|\s*(\w+)\s*\|\s*`([0-9a-f]{64})`\s*\|[^|]*\|[^|]*\|\s*(\d+)\s*\|", t, re.M)
    return {f: (el, sha, int(z)) for f, el, sha, z in rows}


# ---------------------------------------------------------------- synthetic pw.x outputs (self-tests and mocks)
def synthetic_pw_output(*, n_config, calculation="relax", end="converged", k0=0, header=True, nat=2,
                        F_Ry=None, label="synthetic", version=PW_VERSION, ranks=48, symbols=None,
                        exit_marker=EXIT_MARKERS[0], counters=True, n_electrons=None):
    """A pw.x-like output text (format of pw.x 7.5 at verbosity 'low', reduced to what the parsers and ASE read) for
    mocks. Configurations k0 .. k0 + n_config - 1; F_Ry(k) a callable or a sequence. end: converged | nstep |
    bfgs_failed | scf_failed (the SCF of the next configuration fails) | exit | killed | pw_error (QE's errore banner
    in the next SCF, no JOB DONE) | done (scf). n_electrons: the
    printed count (default the z_valence sum, i.e. a neutral cell). No physics."""
    sym = symbols or ["H"] * nat
    nat = len(sym)
    Fk = (F_Ry if callable(F_Ry) else (lambda k, s=F_Ry: s[k - k0])) if F_Ry is not None else \
        (lambda k: -100.0 - 0.001 * (1 - np.exp(-k / 30.0)))
    alat = 10.0
    nel = n_electrons if n_electrons is not None else sum(ZVAL.get(s, 1) for s in sym)
    pos = lambda k: [[1.0 * i + 0.0001 * k, 0.5 * i, 0.25 * i] for i in range(nat)]
    L = []
    if header:
        L += [f"     Program PWSCF v.{version} starts on  3Nov2026 at 12: 0: 0 ", "",
              f"     Number of MPI processes:          {ranks:6d}", f"     Reading input from {label}.in", "",
              "     bravais-lattice index     =            0",
              f"     lattice parameter (alat)  =      {alat:.4f}  a.u.",
              f"     number of atoms/cell      =  {nat:11d}", f"     number of atomic types    =  {len(set(sym)):11d}",
              f"     number of electrons       =  {nel:11.2f}",
              "",
              f"     celldm(1)=  {alat:.6f}  celldm(2)=   0.000000  celldm(3)=   0.000000", "",
              "     crystal axes: (cart. coord. in units of alat)",
              "               a(1) = (   1.000000   0.000000   0.000000 )  ",
              "               a(2) = (   0.000000   1.000000   0.000000 )  ",
              "               a(3) = (   0.000000   0.000000   1.000000 )  ", ""]
        for i, e in enumerate(sorted(set(sym), key=sym.index), 1):
            L += [f"     PseudoPot. # {i} for {e:2s} read from file:", f"     {PSEUDO_DIR}/{PSEUDO_S2[e]}",
                  f"     MD5 check sum: {UPF_MD5_S1.get(e, '0' * 32)}", ""]
        b = alat * QE_UNITS["Bohr"]
        L += ["   Cartesian axes", "", "     site n.     atom                  positions (alat units)"]
        L += [f"     {i + 1:5d}           {e:2s}  tau({i + 1:4d}) = ({x / b:12.7f}{y / b:12.7f}{z / b:12.7f}  )"
              for i, (e, (x, y, z)) in enumerate(zip(sym, pos(k0)))]
        L += ["", "     Self-consistent Calculation", ""]

    def apos(k):
        return ["", "ATOMIC_POSITIONS (angstrom)"] + [f"{e:2s} {x:20.10f}{y:20.10f}{z:20.10f}"
                                                     for e, (x, y, z) in zip(sym, pos(k))] + [""]

    for i in range(n_config):
        k = k0 + i
        if i > 0 or not header:
            L += apos(k)
        F = Fk(k)
        L += [f"     total energy              = {F + 0.01:17.8f} Ry", "",
              f"     the Fermi energy is {3.0:10.4f} ev", "", f"!    total energy              = {F:17.8f} Ry",
              f"     smearing contrib. (-TS)   = {-1e-6:17.8f} Ry", "",
              "     convergence has been achieved in   9 iterations", ""]
        if calculation == "scf":
            L += ["     Forces acting on atoms (cartesian axes, Ry/au):", ""]
            L += [f"     atom {j + 1:4d} type  1   force = {0.001:14.8f}{0.0:14.8f}{0.0:14.8f}" for j in range(nat)]
            L += ["", f"     Total force = {0.001:12.6f}     Total SCF correction =     0.000001", ""]
            continue
        L += ["     Forces acting on atoms (cartesian axes, Ry/au):", ""]
        L += [f"     atom {j + 1:4d} type  1   force = {0.001 / (k + 1):14.8f}{0.0:14.8f}{0.0:14.8f}" for j in range(nat)]
        L += ["", f"     Total force = {0.001:12.6f}     Total SCF correction =     0.000001", ""]
        last = i == n_config - 1
        if last and end == "converged":
            L += [f"     bfgs converged in {k + 1:3d} scf cycles and {k:3d} bfgs steps",
                  "     (criteria: energy <  1.0E-05 Ry, force <  7.8E-04 Ry/Bohr)", "",
                  "     End of BFGS Geometry Optimization", "", f"     Final energy             = {F:17.10f} Ry",
                  "Begin final coordinates"] + apos(k) + ["End final coordinates", ""]
        else:
            L += ["     BFGS Geometry Optimization"] + ([f"     number of scf cycles    = {k + 1:3d}",
                                                        f"     number of bfgs steps    = {k:3d}"] if counters else []) + \
                 ["", f"     energy             new  = {F:17.10f} Ry", "",
                  "     new trust radius        =       0.0100000000 bohr", ""]
    if calculation == "relax":
        kl = k0 + n_config - 1
        if end == "nstep":
            L += [f"     {NSTEP_MARKER}.", "", "     End of BFGS Geometry Optimization", ""]
        elif end == "bfgs_failed":
            L += ["     Message from routine bfgs:", f"     {BFGS_FAIL_MARKERS[1]}", "",
                  f"     bfgs failed after {kl + 1:3d} scf cycles and {kl:3d} bfgs steps, convergence not achieved", ""]
        elif end == "scf_failed":
            L += apos(kl + 1) + [f"     total energy              = {-99.0:17.8f} Ry", "",
                                 "     convergence NOT achieved after 200 iterations: stopping", ""]
        elif end == "exit":
            L += [f"     {exit_marker}", ""]
        elif end == "killed":
            L += apos(kl + 1) + [f"     total energy              = {-99.0:17.8f} Ry"]
        elif end == "pw_error":                       # QE errore inside the next SCF: banner, MPI abort, no JOB DONE
            L += apos(kl + 1) + [f"     total energy              = {-99.0:17.8f} Ry", "",
                                 " " + "%" * 78, "     Error in routine c_bands (1):",
                                 "     too many bands are not converged", " " + "%" * 78, "", "     stopping ..."]
    elif end == "scf_failed":
        L = [ln for ln in L if not ln.startswith("!") and "convergence has been" not in ln]
        L += ["     convergence NOT achieved after 200 iterations: stopping", ""]
    if end not in ("killed", "pw_error"):
        L += ["     PWSCF        :      1m 2.00s CPU      1m 3.50s WALL", "",
              "=------------------------------------------------------------------------------=",
              "   JOB DONE.", "=------------------------------------------------------------------------------="]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- self-test
def _ref_pair():
    """The reference pair (233 host, 232 vacancy cell from pp.build_pair at I127), as scripts/42 builds partners."""
    h = ase_read(os.path.join(ROOT, "results/fa_host/fa19cs1_pb20i60_233.extxyz")); h.calc = None   # energy unread
    v232 = ase_read(os.path.join(ROOT, "results/fa_host/fa19cspb20i59_232_vI.extxyz")); v232.calc = None
    vac, vpos, vi, mig = b42.vacancy_context_from_ref(h, h.positions[127].copy())
    assert vi == 127 and np.array_equal(vac.positions, v232.positions) and np.array_equal(vac.numbers, v232.numbers)
    return h, vac, vpos


def _cells(h, vac, vpos):
    """Synthetic doped cells on the reference pair, every token, both legs (default poses)."""
    sites = {"Sr": 136, "Ca": 136, "Cl": 126, "Cs": 128, "GA": 128}
    out = {}
    for tok, j in sites.items():
        bh, bv = b42.build_paired(h, vac, 127, tok, j, "inherit", vpos=vpos,
                                  mig="allow" if b42.REGISTRY[tok]["site"] == "X" else "forbid")
        out[tok] = (bh, bv, j)
    return out


def _cmp_inputs(t1, t2, *, ignore=("pseudo_dir",)):
    """Differences between two pw.x inputs after whitespace normalisation: namelist keys and card lines."""
    p, q = parse_input_text(t1), parse_input_text(t2)
    diff = []
    for nm in sorted(set(p["namelists"]) | set(q["namelists"])):
        a, b = p["namelists"].get(nm, {}), q["namelists"].get(nm, {})
        for k in sorted(set(a) | set(b)):
            if k not in ignore and not _same(a.get(k), b.get(k)):
                diff.append((nm, k, a.get(k), b.get(k)))
    for cd in CARDS:
        a, b = p["cards"].get(cd), q["cards"].get(cd)
        if (a or {}).get("header") != (b or {}).get("header"):
            diff.append((cd, "header", (a or {}).get("header"), (b or {}).get("header")))
        ra, rb = (a or {}).get("rows", []), (b or {}).get("rows", [])
        if len(ra) != len(rb):
            diff.append((cd, "rows", len(ra), len(rb)))
        else:
            for i, (x, y) in enumerate(zip(ra, rb)):
                if x != y:
                    diff.append((cd, i, " ".join(x), " ".join(y)))
    return diff


def self_test(work=None):
    t0 = time.time()
    results = []
    own = work is None
    work = tempfile.mkdtemp(prefix="s2qe_selftest_") if own else os.path.abspath(work)
    os.makedirs(work, exist_ok=True)

    def case(name, fn):
        t = time.time()
        try:
            msg = fn()
            results.append((name, True))
            print(f"PASS {name}: {msg}  [{time.time() - t:.1f} s]", flush=True)
        except Exception as e:                                   # noqa: BLE001 (report every failure)
            results.append((name, False))
            print(f"FAIL {name}: {type(e).__name__}: {e}  [{time.time() - t:.1f} s]", flush=True)
            traceback.print_exc(limit=4)

    def refused(fn, *a, **kw):
        try:
            fn(*a, **kw)
        except (Refused, S2Error, ValueError) as e:
            return str(e)
        raise AssertionError(f"not refused: {fn.__name__}{a[1:2]}")

    print(f"47_s2_qe self-test: builder {b42.BUILDER_VERSION}, GEOM_SHA {b42.GEOM_SHA[:12]}, numpy {np.__version__}")
    if C46_MOCKED:
        print("MOCKED c46 (scripts/46_s2_cells.py absent: the in-file stub of labels, records and hygiene is used)")
    h, vac, vpos = _ref_pair()
    cells = _cells(h, vac, vpos)
    wp2e_out = os.path.join(ROOT, S1_ARCHIVE, "wp2e/relax_m30_GA_img0.out.gz")
    st = {}

    def clean(at):
        x = at.copy(); x.calc = None; x.set_tags([0] * len(x)); return x

    # ---- 1 constants against literal copies of the plan text
    def c_constants():
        assert a30.PSEUDO == PSEUDO_S1_PINNED, "scripts/30 PSEUDO changed"
        assert PSEUDO_S2 == {**PSEUDO_S1_PINNED, "Cl": "Cl.pbe-n-rrkjus_psl.1.0.0.UPF",
                             "Ca": "Ca.pbe-spn-rrkjus_psl.1.0.0.UPF"}
        assert KMODE == {"kpts": (1, 1, 1), "koffset": (1, 1, 1)}
        assert (ECUT, ECUT_G1, DEGAUSS, CONV_THR, MIXING_BETA, ELECTRON_MAXSTEP) == \
            ((50.0, 400.0), (60.0, 480.0), 0.005, 1e-8, 0.3, 200)
        assert (FORC_CONV_THR, ETOT_CONV_THR, K_CAP, PLATEAU_FROM, PLATEAU_MEV, STEP0_TOL_MEV) == \
            (7.8e-4, 1e-5, 200, 180, 3.0, 0.5)
        assert ZVAL == {"Pb": 14, "I": 7, "C": 4, "N": 5, "H": 1, "Cs": 9, "Sr": 10, "Cl": 7, "Ca": 10}
        assert DVAL == {t: b42.REGISTRY[t]["dval"] for t in DVAL} == {"Sr": -4, "Ca": -4, "Cl": 0, "Cs": -10, "GA": 6}
        assert SPIN_DOPANT == {"Cl": 1 / ZVAL["Cl"], "Ca": 1 / ZVAL["Ca"]} and SPIN_SEED == 0.1
        assert RY_EV == 13.605693122994 and (RANKS_SP, RANKS_A2_DEFAULT, PW_VERSION) == (64, 48, "7.5")
        assert composition(h) == BASE_COMPOSITION and sum(ZVAL[s] for s in h.get_chemical_symbols()) == N_EL_HOST
        assert sum(ZVAL[s] for s in vac.get_chemical_symbols()) == N_EL_VAC_NEUTRAL
        assert (n_x(h), n_x(vac)) == (60, 59)
        return "fingerprint, z_valence, dopant shifts, caps and tolerances equal the plan; 233 cell 1070, 232 cell 1063"

    # ---- 2 inputs for the reference and synthetic doped cells; electron counts; refusals
    def c_inputs():
        d = os.path.join(work, "inputs"); os.makedirs(d, exist_ok=True)
        rows = []

        def w(at, lab, **kw):
            m = write_input(at, lab, d, **kw)
            rows.append((lab, m["electrons"]["n_el"]))
            return m

        free_ref = [i for i in range(len(vac)) if np.linalg.norm(vac.positions[i] - vpos) < 6.5]
        assert w(h, "s2_m30_host")["electrons"]["n_el"] == 1070
        assert w(vac, "s2_m30_VB136")["electrons"]["n_el"] == 1062
        m = w(vac, "s2_m30_VB136_q0"); assert m["electrons"]["n_el"] == 1063 and not m["electrons"]["even"]
        assert w(vac, "s2tp_ref232_np48", kind="relax", free=free_ref, nstep=5)["ranks_expected"] == 48
        assert w(vac, "s2tp_ref232_np32a", kind="relax", free=free_ref, nstep=5)["ranks_expected"] == 32
        assert w(vac, "s2smoke_ref232_n1", kind="relax", free=free_ref, nstep=1)["electrons"]["n_el"] == 1062
        assert w(h, "s2g1_m30_host_e60")["settings"]["ecutwfc"] == 60.0
        want = {"Sr": (1066, 1058), "Ca": (1066, 1058), "Cl": (1070, 1062), "Cs": (1060, 1052), "GA": (1076, 1068)}
        for tok, (bh, bv, j) in cells.items():
            L = b42.REGISTRY[tok]["site"]
            dn, dv = w(bh.atoms, f"s2_m30_{tok}{j}o0_novac"), w(bv.atoms, f"s2_m30_{tok}{j}o0_vac")
            assert (dn["electrons"]["n_el"], dv["electrons"]["n_el"]) == want[tok], (tok, dn["electrons"], dv["electrons"])
            q0 = w(bv.atoms, f"s2_m30_{tok}{j}o0_vac_q0")
            assert q0["electrons"]["n_el"] == want[tok][1] + 1 and not q0["electrons"]["even"]
            fr = [i for i in range(len(bv.atoms)) if np.linalg.norm(bv.atoms.positions[i] - vpos) < 6.0] + \
                 [x for x in bv.members if np.linalg.norm(bv.atoms.positions[x] - vpos) >= 6.0]
            r = w(bv.atoms, f"s2r_m30_{tok}{j}o0_vac", kind="relax", free=fr, nstep=201)
            assert r["settings"]["relax"]["n_fixed"] == len(bv.atoms) - len(set(fr)) and r["settings"]["disk_io"] == "low"
            assert r["ranks_expected"] == 48 and r["electrons"]["n_el"] == want[tok][1]
            txt = open(os.path.join(d, f"s2r_m30_{tok}{j}o0_vac.in")).read()
            assert txt.count(" 0 0 0") == r["settings"]["relax"]["n_fixed"]
            st[tok] = (bh, bv, j, L)
        w(cells["Cl"][0].atoms, "s2g1_m30_Cl138o0_novac_e50")
        assert w(cells["Ca"][0].atoms, "s2g1_m30_Ca136o0_novac_e60")["settings"]["ecutrho"] == 480.0
        # refusals
        x58 = vac.copy(); del x58[[i for i, s in enumerate(x58.get_chemical_symbols()) if s == "I"][0]]
        x61 = h.copy(); x61.append("I"); x61.positions[-1] = [0.5, 0.5, 0.5]
        noH = h.copy(); del noH[[i for i, s in enumerate(noH.get_chemical_symbols()) if s == "H"][0]]
        why = [refused(write_input, x58, "s2_m30_VB136", d), refused(write_input, x61, "s2_m30_host", d),
               refused(electrons, noH, "s2_m30_host"),
               refused(write_input, h, "s2_m30_Sr136o0_novac_q0", d),
               refused(write_input, vac, "s2g1_m30_Cl138o0_novac_e60", d),
               refused(write_input, cells["Cl"][1].atoms, "s2g1_m30_Cl138o0_novac_e60", d),
               refused(write_input, cells["Cl"][0].atoms, "s2spin_m30_Cl175o0_vac", d, dopant_index=126),
               refused(write_input, vac, "s2r_m30_VB136", d, kind="relax", nstep=201),
               refused(write_input, vac, "s2r_m30_VB136", d, kind="relax", free=free_ref),
               refused(write_input, vac, "s2r_m30_VB136", d, kind="relax", free=free_ref, nstep=201,
                       restart_mode="restart"),
               refused(write_input, vac, "s2r_m30_VB136", d, kind="sp"),
               refused(write_input, vac, "s2_m30_VB136", d, kind="relax", free=free_ref, nstep=3),
               refused(write_input, h, "s2_m30_VB136", d),
               refused(write_input, vac, "s2_m30_host", d),
               refused(write_input, cells["Sr"][0].atoms, "s2_m30_Ca136o0_novac", d),
               refused(write_input, vac, "s2_m30_VB136", os.path.join(ROOT, S1_ARCHIVE, "x")),
               refused(write_input, vac, "s2tp_ref232_np48", d, kind="relax", free=free_ref, nstep=5, ranks=64)]
        write_input(h, "s2_m30_host", d)                                       # identical rewrite: allowed
        moved = h.copy(); moved.positions[0] += 0.001
        why.append(refused(write_input, moved, "s2_m30_host", d))            # N-B14
        mv = vac.copy(); mv.positions[5] += 0.01
        why.append(refused(write_input, mv, "s2smoke_ref232_n3", d, kind="relax", free=free_ref, nstep=3))   # N-B17
        why.append(refused(write_input, cells["Sr"][1].atoms, "s2tp_ref232_np64", d, kind="relax", free=free_ref,
                           nstep=5))
        assert w(vac, "s2smoke_ref232_rst2x32", kind="relax", free=free_ref, nstep=3)["ranks_expected"] == 32
        assert not glob.glob(os.path.join(d, "*.part"))
        return (f"{len(rows)} inputs (host 1070; V 1062; V_q0 1063 odd; Sr/Ca 1066/1058, Cl 1070/1062, Cs 1060/1052, "
                f"GA 1076/1068; every _q0 row +1, odd); {len(why)} refusals (58 and 61 X units, odd count, _q0 "
                f"novac, s2g1 vacancy, s2spin vacancy-free, relax without free/nstep, restart via write_input, "
                f"kind/label, label/cell, token/composition, dopant_shell output, ranks, a second input under "
               f"one label, a ref232 row that is not the reference cell)")

    # ---- 3 fingerprint identity with scripts/30 (same ASE) and with archived S1 inputs
    def c_fingerprint():
        d = os.path.join(work, "fp"); os.makedirs(d, exist_ok=True)
        n_ident = 0
        for at, lab in [(h, "s2_m30_host"), (vac, "s2_m30_VB136"), (cells["Sr"][0].atoms, "s2_m30_Sr136o0_novac"),
                        (cells["Sr"][1].atoms, "s2_m30_Sr136o0_vac"), (cells["Cs"][1].atoms, "s2_m30_Cs128o0_vac"),
                        (cells["GA"][1].atoms, "s2_m30_GA128o0_vac"), (vac, "s2_m30_VB136_q0")]:
            q = 0 if lab.endswith("_q0") or n_x(at) == 60 else 1
            a30.write_input(clean(at), lab, os.path.join(d, "s30"), kmode="R", calc="scf", charge=q)
            write_input(at, lab, os.path.join(d, "s2"))
            t30, t2 = (open(os.path.join(d, x, f"{lab}.in")).read() for x in ("s30", "s2"))
            assert t30 == t2, f"{lab}: S2 single-point input differs from scripts/30's"
            n_ident += 1
        hm = h.copy(); hm.set_masses([1.0] * len(hm))                          # N-B15: default masses written
        write_input(hm, "s2_m30_host", os.path.join(d, "mass"))
        assert open(os.path.join(d, "mass", "s2_m30_host.in")).read() == \
            open(os.path.join(d, "s30", "s2_m30_host.in")).read()
        at = cells["GA"][1].atoms
        fr = sorted({i for i in range(len(at)) if np.linalg.norm(at.positions[i] - vpos) < 6.0} |
                    set(cells["GA"][1].members))
        a30.write_input(clean(at), "s2r_m30_GA128o0_vac", os.path.join(d, "s30"), kmode="R", calc="relax", charge=1)
        write_input(at, "s2r_m30_GA128o0_vac", os.path.join(d, "s2"), kind="relax", free=fr, nstep=201)
        diff = _cmp_inputs(*(open(os.path.join(d, x, "s2r_m30_GA128o0_vac.in")).read() for x in ("s30", "s2")))
        nl = sorted((a, b) for a, b, *_ in diff if a in ("control", "system", "electrons", "ions"))
        assert nl == [("control", "disk_io"), ("control", "nstep")], nl
        pos = [x for x in diff if x[0] == "ATOMIC_POSITIONS"]
        nfix = len(at) - len(set(fr))
        assert len(pos) == nfix and all(y == x + " 0 0 0" for _, _, x, y in pos) and \
            len(diff) == 2 + nfix, diff[:4]
        # archived S1 inputs: regenerated from their own geometry with the S2 writer (whitespace normalised,
        # pseudo_dir excluded); every difference must be one of the deliberate S2 differences listed here
        s1 = os.path.join(ROOT, S1_ARCHIVE)
        cases = [("wp2b/raw/m30_Sr/m30_Sr_img0.in.gz", "s2_m30_Sr136o0_vac_q0", "sp", None,
                  {("control", "prefix"), ("system", "tot_charge")}),
                 ("wp2d/raw/m30_GA152_vac_q1.in.gz", "s2_m30_GA152o0_vac", "sp", None, {("control", "prefix")}),
                 ("wp2e/relax_m30_GA_img0.in.gz", "s2r_m30_GA128o0_vac", "relax", 8.0,
                  {("control", "prefix"), ("system", "tot_charge"), ("control", "disk_io"), ("control", "nstep")})]
        listed = []
        for rel, lab, kind, rcut, allowed in cases:
            txt1 = a32.read_text(os.path.join(s1, rel))
            g = ase_read(io.StringIO(txt1), format="espresso-in")
            kw = {}
            if kind == "relax":
                kw = {"kind": "relax", "nstep": 201,
                      "free": [i for i in range(len(g)) if np.linalg.norm(g.positions[i] - g.positions[0]) < rcut]}
            write_input(g, lab, os.path.join(d, "s1cmp"), **kw)
            diff = _cmp_inputs(txt1, open(os.path.join(d, "s1cmp", f"{lab}.in")).read())
            nl = {(a, b) for a, b, *_ in diff if a not in CARDS}
            assert nl == allowed, (rel, sorted(nl ^ allowed), [x for x in diff if (x[0], x[1]) in nl ^ allowed][:3])
            cards = [x for x in diff if x[0] in CARDS]
            nfix = len(g) - len(kw.get("free", range(len(g))))
            assert len(cards) == nfix and all(x[0] == "ATOMIC_POSITIONS" and x[3] == x[2] + " 0 0 0" for x in cards)
            listed.append(f"{os.path.basename(rel)}: {sorted(b for _, b in nl)}" + (f" + if_pos on {nfix}" if nfix else ""))
        # the undoped nspin-2 S1 row: same settings path with the seed 0.1 on every species (no S2 label exists)
        rel = "wp2b/raw/zz_settings/set_m30u_img0_nspin2.in.gz"
        txt1 = a32.read_text(os.path.join(s1, rel)); g = ase_read(io.StringIO(txt1), format="espresso-in")
        s = settings_for("s2spin_m30_Cl175o0_vac", "sp"); s["tot_charge"] = 0
        mags = {e: SPIN_SEED for e in set(g.get_chemical_symbols())}
        t2 = _render(g, "set_m30u_img0_nspin2", s, magmoms=[SPIN_SEED] * len(g))
        verify_input_text(t2, rel, "set_m30u_img0_nspin2", s, g, mag_by_element=mags, n_el=1063)
        diff = _cmp_inputs(txt1, t2)
        assert diff == [], diff[:3]
        listed.append("set_m30u_img0_nspin2.in: identical")
        return f"{n_ident} single points byte-identical to scripts/30; relax differs only in disk_io, nstep " \
               f"and if_pos; S1 archive: " + "; ".join(listed)

    # ---- 4 spin seed
    def c_spin():
        d = os.path.join(work, "spin"); os.makedirs(d, exist_ok=True)
        msg = []
        for tok, lab in (("Cl", "s2spin_m30_Cl175o0_vac"), ("Ca", "s2spin_m30_Ca76o0_vac")):
            bv = cells[tok][1]
            m = write_input(bv.atoms, lab, d, dopant_index=bv.centre)
            p = parse_input_text(open(os.path.join(d, f"{lab}.in")).read())
            sp_el = [label_to_symbol(r[0]) for r in p["cards"]["ATOMIC_SPECIES"]["rows"]]
            got = {e: p["namelists"]["system"][f"starting_magnetization({i})"] for i, e in enumerate(sp_el, 1)}
            assert got[tok] == 1 / ZVAL[tok] and all(v == 0.1 for e, v in got.items() if e != tok), got
            assert p["namelists"]["system"]["nspin"] == 2 and p["namelists"]["system"]["tot_charge"] == 1.0
            assert m["electrons"]["n_el"] == {"Cl": 1062, "Ca": 1058}[tok] and not m["starting_magnetization_rewritten"]
            msg.append(f"{tok} {got[tok]:.6f}")
        # an ASE that scales the moments (e.g. by z_valence) is caught and rewritten explicitly
        bv = cells["Cl"][1]; s = settings_for("s2spin_m30_Cl175o0_vac", "sp")
        mm = [SPIN_SEED] * len(bv.atoms); mm[bv.centre] = SPIN_DOPANT["Cl"]
        t = _render(bv.atoms, "s2spin_m30_Cl175o0_vac", s, magmoms=mm)
        bad = re.sub(r"(starting_magnetization\(\d+\)\s*=\s*)(\S+)", lambda m: m.group(1) + repr(float(m.group(2)) / 7), t)
        mag = {e: (SPIN_DOPANT["Cl"] if e == "Cl" else SPIN_SEED) for e in set(bv.atoms.get_chemical_symbols())}
        refused(verify_input_text, bad, "x", "s2spin_m30_Cl175o0_vac", s, bv.atoms, mag_by_element=mag, n_el=1062)
        sp_el = [label_to_symbol(r[0]) for r in parse_input_text(bad)["cards"]["ATOMIC_SPECIES"]["rows"]]
        fixed = _fix_magnetization(bad, [mag[e] for e in sp_el])
        verify_input_text(fixed, "x", "s2spin_m30_Cl175o0_vac", s, bv.atoms, mag_by_element=mag, n_el=1062)
        refused(write_input, cells["Sr"][1].atoms, "s2_m30_Sr136o0_vac", d, dopant_index=136)
        return f"dopant 1/z_valence ({', '.join(msg)}), 0.1 on every other species, read back from the text; " \
               f"a scaled writer is refused by the check and repaired by the explicit rewrite"

    # ---- 5 WP2e relaxation: 283 configurations, values, CSV, the k = 200 cut
    def c_wp2e():
        READS.clear()
        r = parse_relax([wp2e_out], read="full", k_cap=10 ** 9, ranks=48)
        st["wp2e_full"] = r
        assert r["usable"] and r["n_config"] == 283 and r["ks"] == list(range(283))
        assert r["qe_converged"] and r["converged_at_k"] == 282 and r["last_end"] == "converged"
        F = r["F_eV"]
        d120, d200 = (F[120] - F[100]) * 1000, (F[200] - F[180]) * 1000
        assert abs(d120 - (-58.3)) < 0.05 and abs(d200 - (-16.3)) < 0.05, (d120, d200)
        import csv
        rows = list(csv.DictReader(open(os.path.join(ROOT, S1_ARCHIVE, "wp2e/wp2e_trajectory_m30_GA_img0.csv"))))
        assert [int(x["scf_cycle"]) for x in rows] == list(range(283))
        dev = max(abs((F[k] - F[0]) * 1000 - float(x["F_minus_F0_meV"])) for k, x in enumerate(rows))
        devf = max(abs(float(np.linalg.norm(r["forces_eVA"][k], axis=1).max()) - float(x["fmax_eVA"]))
                   for k, x in enumerate(rows))
        assert dev <= 0.001 and devf <= 5.1e-5, (dev, devf)
        assert READS["ase"] == 1 and READS["F"] == 283 and READS["positions"] == 283
        R = parse_relax([wp2e_out], read="full", ranks=48)            # the plan cap k = 200
        assert R["n_config"] == 201 and max(R["F_eV"]) == 200 and R["cap_reached"] and not R["qe_converged"]
        assert all(R["F_eV"][k] == F[k] for k in range(201)) and np.array_equal(R["positions_A"][200], r["positions_A"][200])
        e = end_rule(parse_relax([wp2e_out], read="end_rule", ranks=48, n_el=1069))
        refused(parse_relax, [wp2e_out], read="counts", ranks=48, n_el=1068)          # N-B9
        refused(parse_relax, [wp2e_out], read="counts", ranks=64)                     # I-26
        assert e["outcome"] == "unconverged_cap" and abs(e["dF_200_180_meV"] - d200) < 1e-9
        return (f"283 configurations k = 0..282, converged at k = 282; F(120) - F(100) = {d120:.3f} meV, "
                f"F(200) - F(180) = {d200:.3f} meV; CSV max |dev| {dev * 1000:.2f} ueV (F), {devf:.1e} eV/A (fmax); "
                f"ASE = this parser at every k; k_cap 200: 201 configurations, nothing beyond k = 200, "
                f"end rule unconverged_cap")

    # ---- 6 read modes are the blinding interface
    def c_modes():
        n = {}
        for mode in READ_MODES[:-1]:                       # full: case wp2e-relaxation
            READS.clear()
            r = parse_relax([wp2e_out], read=mode, ranks=48)
            n[mode] = dict(READS)
            vals = {k for k in ("F_Ry", "F_eV", "forces_eVA", "positions_A") if k in r}
            if mode in ("status", "counts"):
                assert not READS and not vals, (mode, dict(READS), vals)
            elif mode == "k0":
                assert dict(READS) == {"F": 1} and list(r["F_eV"]) == [0] and "positions_A" not in r
            elif mode == "end_rule":
                assert dict(READS) == {"F": 2} and sorted(r["F_eV"]) == [180, 200]
            elif mode == "final_geom":
                assert dict(READS) == {"positions": 1} and vals == {"positions_A"} and list(r["positions_A"]) == [200]
                assert np.array_equal(r["positions_A"][200], st["wp2e_full"]["positions_A"][200])
            elif mode == "final":
                assert dict(READS) == {"positions": 1, "F": 1} and list(r["F_eV"]) == [200]
        # end_rule below the cap reads no energy at all
        p = os.path.join(work, "short.out"); open(p, "w").write(synthetic_pw_output(n_config=40, end="exit"))
        READS.clear(); r = parse_relax([p], read="end_rule")
        assert not READS and "F_eV" not in r and end_rule(r)["outcome"] == "incomplete"
        # parse_sp status mode captures nothing; the value regexes are instrumented
        calls = []
        saved = dict(ENERGY_RX)
        class Spy:
            def __init__(self, k, rx): self.k, self.rx = k, rx
            def __getattr__(self, a):
                calls.append(self.k); return getattr(self.rx, a)
        try:
            for k in ENERGY_RX:
                ENERGY_RX[k] = Spy(k, saved[k])
            READS.clear()
            parse_sp(os.path.join(ROOT, S1_ARCHIVE, "wp2d/raw/m30_GA152_vac_q1.out.gz"), read="status")
            parse_relax([wp2e_out], read="status", ranks=48)
            parse_relax([wp2e_out], read="final_geom", ranks=48)
            parse_counts(p)
        finally:
            ENERGY_RX.update(saved)
        assert not calls and READS == collections.Counter({"positions": 1}), (calls, READS)
        return "status/counts capture no value; k0 F(0) only; end_rule F(180), F(200) only (none below the cap); " \
               "final_geom positions of k_last only; final adds F(k_last); no value regex runs in status reads"

    # ---- 7 end rule
    def c_end_rule():
        base = {"usable": True, "k_cap": 200, "qe_converged": False, "converged_at_k": None, "last_end": "cap",
                "k_last": 200, "n_config": 201}
        cases = {
            "conv150": dict(base, qe_converged=True, converged_at_k=150, k_last=150, last_end="converged"),
            "conv200": dict(base, qe_converged=True, converged_at_k=200, last_end="converged"),
            "plateau3.000": dict(base, F_eV={180: 0.0, 200: -0.003}),
            "plateau3.001": dict(base, F_eV={180: 0.0, 200: -0.003001}),
            "plateau+3.000": dict(base, F_eV={180: -80000.5, 200: -80000.5 + 0.0029999}),
        }
        want = {"conv150": "accepted_converged", "conv200": "accepted_converged", "plateau3.000": "accepted_plateau",
                "plateau3.001": "unconverged_cap", "plateau+3.000": "accepted_plateau"}
        got = {k: end_rule(v)["outcome"] for k, v in cases.items()}
        assert got == want, got
        # synthetic output texts
        txt = {"bfgs50": synthetic_pw_output(n_config=51, end="bfgs_failed"),
               "scf80": synthetic_pw_output(n_config=80, end="scf_failed"),
               "nstep120": synthetic_pw_output(n_config=121, end="nstep"),
               "killed": synthetic_pw_output(n_config=30, end="killed"),
               "exit": synthetic_pw_output(n_config=30, end="exit"),
               "conv150": synthetic_pw_output(n_config=151, end="converged"),
               "conv200": synthetic_pw_output(n_config=201, end="converged"),
               "beyond": synthetic_pw_output(n_config=205, end="killed", F_Ry=lambda k: -100.0 if k <= 200 else 999.0)}
        out = {}
        for k, t in txt.items():
            p = os.path.join(work, f"end_{k}.out"); open(p, "w").write(t)
            r = parse_relax([p], read="end_rule")
            out[k] = (end_rule(r)["outcome"], r["k_last"], r["last_end"], end_rule(r).get("stop"))
        assert out["bfgs50"] == ("unconverged_early", 50, "bfgs_failed", False), out["bfgs50"]
        assert out["scf80"] == ("unconverged_early", 79, "scf_failed", False), out["scf80"]
        assert out["nstep120"] == ("unconverged_early", 120, "nstep", True), out["nstep120"]
        assert out["killed"][0] == "incomplete" and out["exit"][0] == "incomplete" and out["exit"][2] == "exit_stop"
        assert out["conv150"][:2] == ("accepted_converged", 150) and out["conv200"][:2] == ("accepted_converged", 200)
        assert out["beyond"] == ("accepted_plateau", 200, "cap", False), out["beyond"]
        READS.clear()
        r = parse_relax([os.path.join(work, "end_beyond.out")], read="full")
        assert max(r["F_Ry"]) == 200 and 999.0 not in r["F_Ry"].values() and READS["F"] == 201
        other = os.path.join(work, "end_other.out")
        open(other, "w").write(synthetic_pw_output(n_config=20, end="exit").replace(EXIT_MARKERS[0], "something else"))
        e = end_rule(parse_relax([other], read="end_rule"))
        assert e["outcome"] == "unconverged_early" and e["stop"]
        # round-2 R2-QE-1: QE's error banner (errore: no JOB DONE) cut into the archived WP2e output inside the SCF of
        # configuration 120 is a final end, unconverged early with a STOP, never 'restart_or_rerun'
        E = a32.read_text(wp2e_out)
        bang = [m_.start() for m_ in re.finditer(r"^!", E, re.M)]
        a_ = E.find("ATOMIC_POSITIONS", bang[119]); cut = E.find("\n", E.find("iteration #", a_) + 200)
        assert a_ < cut < bang[120]
        banner = (f"\n {'%' * 78}\n     Error in routine c_bands (1):\n     too many bands are not converged\n "
                  f"{'%' * 78}\n\n     stopping ...\n")
        pe = os.path.join(work, "end_pw_error.out"); open(pe, "w").write(E[:cut] + banner)
        r = parse_relax([pe], read="end_rule", ranks=48)
        e = end_rule(r)
        assert (r["n_config"], r["k_last"], r["last_end"]) == (120, 119, "pw_error") and "JOB DONE" not in open(pe).read()
        assert e["outcome"] == "unconverged_early" and e["stop"] and "c_bands (1): too many bands" in e["reason"], e
        refused(parse_relax, [pe, pe], read="status", ranks=48)                       # nothing continues it (N-B13)
        # the same banner after configuration 200 is complete: the cap rule decides (I-B4 precedence)
        pc = os.path.join(work, "end_pw_error_cap.out")
        open(pc, "w").write(synthetic_pw_output(n_config=203, end="pw_error", F_Ry=lambda k: -100.0))
        r = parse_relax([pc], read="end_rule")
        assert r["last_end"] == "cap" and end_rule(r)["outcome"] == "accepted_plateau", (r["last_end"], end_rule(r))
        assert pw_error(synthetic_pw_output(n_config=3, end="pw_error")).startswith("c_bands (1): too many bands")
        # N-B9 (round-2 R2-QE-3): with a label, part n must name <label>.p<n>.in
        refused(parse_relax, [os.path.join(work, "end_bfgs50.out")], read="status", label="s2r_m30_VB136")
        return ("F-series: converged at 150 and 200 accepted; |dF| 3.000 accepted, 3.001 not; texts: BFGS failure at "
                "k = 50, SCF failure at k = 80, nstep at k = 120 unconverged early (nstep STOPs); killed and soft exit "
                "incomplete; a run past k = 200 is cut at 200 (F(201..) never read); unknown JOB DONE end STOPs; a "
                "pw.x error banner in the SCF of WP2e configuration 120 is pw_error, unconverged early and STOPs, "
                "after k = 200 the cap rule applies; another input name refused")

    # ---- 8 restart concatenation on the WP2e output
    def c_restart():
        txt = a32.read_text(wp2e_out)
        hdr = _header(txt)
        cfg, _ = _segment(txt, hdr["nat"])
        K = 120
        sc = txt.find("Self-consistent Calculation"); assert sc > 0
        head = txt[:txt.rfind("\n", 0, sc) + 1]                     # the header, cut at a line start
        tail = "\n     Program stopped by user request\n\n   JOB DONE.\n"
        d = os.path.join(work, "restart"); os.makedirs(d, exist_ok=True)
        P = lambda nm, t: (open(os.path.join(d, nm), "w").write(t), os.path.join(d, nm))[1]
        p1 = P("p1.out", txt[:cfg[K]["own_end"]] + tail)
        p2 = P("p2.out", head + txt[cfg[K]["own_end"]:])
        full = st["wp2e_full"]
        r = parse_relax([p1, p2], read="full", k_cap=10 ** 9, ranks=48)
        assert r["usable"] and r["ks"] == list(range(283)) and r["parts"][0]["end"] == "exit_stop"
        assert r["parts"][1]["k_first"] == K + 1 and r["converged_at_k"] == 282
        same = all(r["F_Ry"][k] == full["F_Ry"][k] and np.array_equal(r["forces_eVA"][k], full["forces_eVA"][k])
                   and np.array_equal(r["positions_A"][k], full["positions_A"][k]) for k in range(283))
        assert same, "the split relaxation differs from the unsplit one"
        rc = parse_relax([p1, p2], read="end_rule", ranks=48)
        assert rc["n_config"] == 201 and end_rule(rc)["outcome"] == "unconverged_cap"
        # repeated last configuration, allowed only by the mapping and only if equal
        p2r = P("p2r.out", head + txt[cfg[K - 1]["own_end"]:])
        rr = parse_relax([p1, p2r], read="full", k_cap=10 ** 9, ranks=48, mapping={"restart_repeats_last": True})
        assert rr["usable"] and rr["ks"] == list(range(283)) and rr["repeats"][0]["verified_F"] and \
            all(rr["F_Ry"][k] == full["F_Ry"][k] for k in range(283))
        assert not parse_relax([p1, p2r], read="final_geom", ranks=48)["usable"]          # repeat not in the mapping
        lines = (head + txt[cfg[K - 1]["own_end"]:]).splitlines(keepends=True)
        i0 = next(i for i, ln in enumerate(lines) if ln.startswith("ATOMIC_POSITIONS"))
        assert sum(len(x) for x in lines[:i0]) == len(head)                # the repeated block of k = K
        tok = lines[i0 + 5].split(); tok[1] = f"{float(tok[1]) + 0.01:.10f}"
        lines[i0 + 5] = " ".join(tok) + "\n"
        p2m = P("p2m.out", "".join(lines))
        rm = parse_relax([p1, p2m], read="final_geom", ranks=48, mapping={"restart_repeats_last": True})
        assert not rm["usable"] and "differs" in rm["unusable_reason"]
        p2l = P("p2l.out", head + txt[cfg[K + 2]["own_end"]:])                           # starts at K + 3
        rl = parse_relax([p1, p2l], read="counts", ranks=48)
        assert not rl["usable"] and end_rule(dict(rl, k_cap=200))["outcome"] == "incomplete"
        refused(parse_relax, [wp2e_out, p2], read="counts", ranks=48)                       # part after 'converged'
        return (f"split at k = {K} (soft exit, then header + rest): 283 configurations equal to the unsplit run "
                f"(F, forces, positions); a repeated k = {K} accepted only under the mapping and only if equal; "
                f"a moved repeat and a part starting at k = {K + 3} are unusable; a part after 'converged' STOPs")

    # ---- 9 restart input
    def c_restart_input():
        d = os.path.join(work, "inputs")
        src = os.path.join(d, "s2r_m30_Sr136o0_vac.in")
        dst = os.path.join(d, "s2r_m30_Sr136o0_vac.p2.in")
        r = restart_input(src, dst, 140)
        a, b = open(src).read().splitlines(), open(dst).read().splitlines()
        added = b.pop(r["added_line"] - 1)
        ch = [(x.strip(), y.strip()) for x, y in zip(a, b) if x != y]
        assert re.sub(r"\s+", " ", added.strip()) == "restart_mode = 'restart'" and len(a) == len(b) and r["nstep"] == 140
        assert len(ch) == 1 and re.sub(r"\s+", " ", ch[0][1]) == "nstep = 140" and ch[0][0].startswith("nstep"), ch
        assert not re.search(r"restart_mode", open(src).read())
        refused(restart_input, dst, dst + ".x", 10)                                         # not a part-1 input
        refused(restart_input, os.path.join(d, "s2_m30_host.in"), dst + ".y", 10)          # a single point
        refused(restart_input, src, dst + ".z", 0)
        m = write_input(vac, "s2r_m30_VB136", d, kind="relax", free=list(range(50)), nstep=201,
                        restart_mode=QE_FRESH_START)                                    # QE's default value = None
        assert m["settings"]["relax"]["restart_mode"] is None
        return "part 1 has no restart_mode line (QE default); part 2 adds restart_mode = 'restart' and changes " \
               "nstep, nothing else; refusals: a restart input as source, a single point, nstep 0"

    # ---- 10 single points: parse_sp vs scripts/32 and scripts/37; completeness states
    def c_sp():
        n = 0
        wp3 = sorted(f for f in os.listdir(os.path.join(ROOT, S1_ARCHIVE, "wp3/raw")) if f.endswith(".out.gz"))[0]
        for rel in ("wp2b/raw/m30_Sr/m30_Sr_img0.out.gz", "wp2d/raw/m30_GA152_vac_q1.out.gz",
                    "wp2b/raw/zz_settings/set_m30u_img0_nspin2.out.gz", "wp3/raw/" + wp3):
            p = os.path.join(ROOT, S1_ARCHIVE, rel)
            r, q, e = parse_sp(p), a32.parse_qe(p), a37.qe(p)
            assert r["F_eV"] == q["F_eV"] == e["F"] and r["mTS_eV"] == q["mTS_eV"] and r["E_F_eV"] == e["EF"]
            assert np.array_equal(r["forces_eVA"], q["forces"]) and abs(r["forces"]["all"]["max_eVA"] - e["fmax"]) < 1e-12
            fr = [0, 3, 7]                                                 # N-B18: the free atoms' per-atom norms
            rf = parse_sp(p, free=fr)["forces"]["free"]
            want = [float(np.linalg.norm(q["forces"][i])) for i in fr]
            assert rf["indices"] == fr and np.allclose(rf["norms_eVA"], want, rtol=0, atol=1e-12) and \
                abs(rf["max_eVA"] - max(want)) < 1e-12, rf
            assert r["M_total_muB"] == e["mag"] and r["scf_converged"] and r["job_done"] and r["n_bang"] == 1
            _check_header(r, where=rel)
            n += 1
        nsp = parse_sp(os.path.join(ROOT, S1_ARCHIVE, "wp2b/raw/zz_settings/set_m30u_img0_nspin2.out.gz"))
        assert nsp["M_abs_muB"] is not None
        d = os.path.join(work, "jobs", "s2_m30_host"); os.makedirs(d, exist_ok=True)
        b = os.path.join(d, "s2_m30_host")
        meta = write_input(h, "s2_m30_host", d, ranks=64)
        S = lambda **kw: sp_status(d, "s2_m30_host", meta=meta, **{"retry_s": 0.01, **kw})
        flow = [S()["status"]]
        open(b + ".out", "w").write(synthetic_pw_output(n_config=1, calculation="scf", end="killed", ranks=64,
                                                        label="s2_m30_host"))
        flow += [S()["status"], S(running=True)["status"]]
        os.replace(b + ".out", b + ".out.try1")                                     # the queue's first resubmission
        flow.append(S()["status"])
        open(b + ".out", "w").write(synthetic_pw_output(n_config=1, calculation="scf", end="killed", ranks=64,
                                                        label="s2_m30_host"))
        os.replace(b + ".out", b + ".out.try2"); open(b + ".gaveup", "w").close()
        r = S(); flow.append(r["status"])
        assert flow == ["pending", "pending", "running", "pending", "missing"] and \
            r["missing_reason"] == "no JOB DONE after one resubmission", flow
        for f in (b + ".out.try2", b + ".gaveup"):
            os.remove(f)
        sym = h.get_chemical_symbols()
        good = synthetic_pw_output(n_config=1, calculation="scf", end="done", ranks=64, label="s2_m30_host", symbols=sym,
                                   n_electrons=1070)
        open(b + ".out", "w").write(good)
        assert S()["status"] == "complete"
        bad = synthetic_pw_output(n_config=1, calculation="scf", end="scf_failed", ranks=64, label="s2_m30_host",
                                  symbols=sym)
        bad = re.sub(r"number of electrons\s+=\s+\S+", "number of electrons       =      1070.00", bad)
        open(b + ".out", "w").write(bad)
        r = S()
        assert r["status"] == "missing" and r["missing_reason"] == "SCF not converged (JOB DONE)" and "JOB DONE" in bad
        # the queue never resubmits it: qe_queue.sh skips any output that contains JOB DONE
        assert re.search(r'grep -q "JOB DONE" "\S+\.out"', open(os.path.join(ROOT, "ehpc/node/qe_queue.sh")).read())
        open(b + ".out", "w").write(good.replace("v.7.5", "v.7.2"))
        why = [refused(S)]
        open(b + ".out", "w").write(re.sub(r"Number of MPI processes:\s+64", "Number of MPI processes:  48", good))
        why.append(refused(S))
        open(b + ".out", "w").write(good.replace("1070.00", "1069.00"))
        why.append(refused(S))
        open(b + ".out", "w").write(good); open(b + ".gaveup", "w").close()
        why.append(refused(S)); os.remove(b + ".gaveup")
        open(b + ".out.try3", "w").close(); why.append(refused(S)); os.remove(b + ".out.try3")
        open(b + ".out", "w").write(good.replace(UPF_MD5_S1["H"], "f" * 32)); why.append(refused(S))
        # round-2 R2-QE-2: the queue's states while it moves files (qe_queue.sh: mv .out .out.try<n>; touch .gaveup)
        for f in glob.glob(b + ".out*") + glob.glob(b + ".gaveup"):
            os.remove(f)
        killed = synthetic_pw_output(n_config=1, calculation="scf", end="killed", ranks=64, label="s2_m30_host")
        open(b + ".out.try1", "w").write(killed); open(b + ".out.try2", "w").write(killed)
        r = S()                                               # between mv and touch, persisting: missing, gaveup due
        assert r["status"] == "missing" and r.get("gaveup_pending"), r
        real_glob = glob.glob

        def moving(n_try, touch):
            def g(pat, *a, **k):
                if os.path.exists(b + ".out"):
                    os.replace(b + ".out", b + f".out.try{n_try}")
                    if touch:
                        open(b + ".gaveup", "w").close()
                return real_glob(pat, *a, **k)
            return g
        os.remove(b + ".out.try2"); open(b + ".out", "w").write(killed)
        glob.glob = moving(2, True)                           # the second failure, after .out was found
        try:
            r2 = S()
        finally:
            glob.glob = real_glob
        assert r2["status"] == "missing" and not r2.get("gaveup_pending"), r2
        for f in (b + ".out.try1", b + ".out.try2", b + ".gaveup"):
            os.remove(f)
        open(b + ".out", "w").write(killed)
        glob.glob = moving(1, False)                          # the first failure, after .out was found
        try:
            r3 = S()
        finally:
            glob.glob = real_glob
        assert r3["status"] == "pending", r3
        return (f"{n} S1 outputs: parse_sp = scripts/32 parse_qe and scripts/37 qe (F, -TS, E_F, forces, M); "
                f"states pending -> running -> (try1) pending -> (try2 + gaveup) missing; JOB DONE converged "
                f"complete; JOB DONE with 'convergence NOT achieved' missing and never resubmitted; {len(why)} STOPs "
                f"(version, ranks, electrons, .gaveup beside .out, try3, MD5); queue moves: try1 + try2 without "
                f".gaveup missing (gaveup due), .out moved to try2 + touch during a read missing, .out moved to try1 "
                f"during a read pending (no STOP)")

    # ---- 11 UPF identity
    def c_upf():
        t = s1_md5_table()
        got = {el: v["md5"] for el, v in t["elements"].items()}
        assert got == UPF_MD5_S1 and t["n_outputs"] >= 376, (got, t["n_outputs"])
        note = sha256_table_from_note()
        assert {f: v[1] for f, v in note.items()} == UPF_SHA256_S2 and note["Cl.pbe-n-rrkjus_psl.1.0.0.UPF"][2] == 7 \
            and note["Ca.pbe-spn-rrkjus_psl.1.0.0.UPF"][2] == 10
        d = os.path.join(work, "pseudo"); os.makedirs(d, exist_ok=True)
        for el, fn in PSEUDO_S2.items():
            open(os.path.join(d, fn), "w").write(f'<UPF version="2.0.1">\n<PP_HEADER\n  element="{el}"\n'
                                                 f'  z_valence="{float(ZVAL[el]):.15E}"\n/>\n</UPF>\n')
        md5 = {el: hashlib.md5(open(os.path.join(d, fn), "rb").read()).hexdigest() for el, fn in PSEUDO_S2.items()
               if el in UPF_MD5_S1}
        sha = {PSEUDO_S2[e]: _sha256_file(os.path.join(d, PSEUDO_S2[e])) for e in ("Cl", "Ca")}
        ok = upf_check(d, md5_s1=md5, sha256_s2=sha)
        assert ok["passed"] and not c46.hygiene_violations(json.dumps(ok))
        assert not upf_check(d)["passed"]                         # fake files against the real identities
        ref = json.loads(json.dumps(ok))
        assert upf_check(d, reference=ref, reference_name="c1/upf_check.json", md5_s1=md5, sha256_s2=sha)["passed"]
        open(os.path.join(d, PSEUDO_S2["Ca"]), "a").write(" ")
        r = upf_check(d, reference=ref, md5_s1=md5, sha256_s2=sha)
        assert not r["passed"] and len(r["files"]["Ca"]["reasons"]) == 2
        p = os.path.join(d, PSEUDO_S2["Cl"]); open(p, "w").write(open(p).read().replace("7.0000", "6.0000"))
        assert "z_valence" in " ".join(upf_check(d, md5_s1=md5)["files"]["Cl"]["reasons"])
        assert upf_md5_extra(ok) == {e: ok["files"][e]["md5"] for e in ("Cl", "Ca")}
        refused(upf_md5_extra, r)
        os.remove(os.path.join(d, PSEUDO_S2["Pb"]))
        assert upf_check(d, md5_s1=md5, sha256_s2=sha)["files"]["Pb"]["reasons"] == ["missing"]
        return (f"{t['n_outputs']} S1 outputs print one MD5 per element = UPF_MD5_S1; UPF_SHA256_S2 = the table of "
                f"PSEUDOPOTENTIALS_S2.md (Cl 7, Ca 10); synthetic directory passes, then fails on a changed byte, "
                f"a C1-reference mismatch, a z_valence and a missing file")

    # ---- 12 step-0 equivalence
    def c_step0():
        assert step0_equivalence(0.0, 0.0005)["passed"] and not step0_equivalence(0.0, 0.0005001)["passed"]
        assert step0_equivalence(0.0, -0.0005)["passed"] and not step0_equivalence(0.0, -0.0005001)["passed"]
        assert step0_equivalence(-80000.123, -80000.123 + 0.0004)["passed"]
        assert not step0_equivalence(-80000.123, -80000.123 + 0.0006)["passed"]
        return "0.5000 meV passes, 0.5001 fails (both signs); 0.4 / 0.6 meV at F of -8e4 eV"

    # ---- 13 labels, hygiene of written records and of this file
    def c_hygiene():
        metas = glob.glob(os.path.join(work, "**", "*.meta.json"), recursive=True)
        bad = {os.path.basename(m): c46.hygiene_violations(open(m).read()) for m in metas}
        bad = {k: v for k, v in bad.items() if v}
        assert metas and not bad, bad
        src = open(os.path.abspath(__file__)).read()
        v = c46.hygiene_violations(src)
        assert not v, v[:5]
        for lab in ("s2r_m30_hostB136", "s2spin_m30_Ca76o0_vac", "s2g1_m30_host_e60", "s2smoke_ref232_rst64"):
            label_info(lab)
        why = [refused(label_info, x) for x in ("s2_m30_VB136_e60", "s2r_m30_Cs128o1_vac", "s2g1_m05_host_e60",
                                                "s2spin_m30_Sr76o0_vac", "s2_m30_Sr136o0_novac_q0", "relax_m30_GA_img0",
                                                "s2_m30_Sr0136o0_vac", "s2tp_ref232_np99")]
        return f"{len(metas)} meta records and this script carry no local path, address, id or currency; " \
               f"{len(why)} label refusals"

    # ---- 14 CLI round trip
    def c_cli():
        d = os.path.join(work, "cli"); os.makedirs(d, exist_ok=True)
        from ase.io import write as ase_write
        f = os.path.join(d, "cell.extxyz"); ase_write(f, vac, format="extxyz")
        fr = os.path.join(d, "free.json"); json.dump(list(range(40)), open(fr, "w"))
        assert main(["write", "--cell", f, "--label", "s2smoke_ref232_n3", "--out", d, "--kind", "relax",
                     "--free", fr, "--nstep", "3"]) == 0
        assert main(["restart", "--input", os.path.join(d, "s2smoke_ref232_n3.in"),
                     "--out", os.path.join(d, "s2smoke_ref232_n3.p2.in"), "--nstep", "2"]) == 0
        p = os.path.join(d, "c.out"); open(p, "w").write(synthetic_pw_output(n_config=4, end="exit"))
        assert main(["counts", p]) == 0
        assert main(["status", "--dir", d, "--label", "s2smoke_ref232_n3"]) == 0
        return "write, restart, counts and status subcommands run"

    case("constants", c_constants)
    case("inputs-electrons-refusals", c_inputs)
    case("fingerprint-scripts30-and-S1", c_fingerprint)
    case("spin-seed", c_spin)
    case("wp2e-relaxation", c_wp2e)
    case("read-modes-blinding", c_modes)
    case("end-rule", c_end_rule)
    case("restart-concatenation", c_restart)
    case("restart-input", c_restart_input)
    case("single-points-completeness", c_sp)
    case("upf-identity", c_upf)
    case("step0-equivalence", c_step0)
    case("labels-hygiene", c_hygiene)
    case("cli", c_cli)
    def c_no_model():
        assert "mace" not in sys.modules, "mace was imported"
        return "'mace' not in sys.modules"

    case("no-model", c_no_model)
    if own:
        shutil.rmtree(work, ignore_errors=True)
    print("NOTES:")
    for k, v in NOTES.items():
        print(f"  {k}: {v}")
    nf = sum(1 for _, ok in results if not ok)
    print(f"SELF-TEST {'PASS' if nf == 0 else 'FAIL'} ({len(results)} cases, {nf} failed, {time.time() - t0:.0f} s)"
          + ("  [MOCKED c46]" if C46_MOCKED else ""))
    return 0 if nf == 0 else 1


# ---------------------------------------------------------------- CLI
def _jsonable(x):
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, (np.integer, np.floating)):
        return x.item()
    return x


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--work", default=None, help="self-test working directory (default: a fresh temporary one)")
    sub = ap.add_subparsers(dest="cmd")
    w = sub.add_parser("write", help="write one S2 QE input and its meta record")
    w.add_argument("--cell", required=True, help="extxyz file of the cell (any stored energy is ignored)")
    w.add_argument("--label", required=True)
    w.add_argument("--out", required=True)
    w.add_argument("--kind", choices=["sp", "relax"], default="sp")
    w.add_argument("--free", default=None, help="JSON: a list of free indices, or a record with 'free'")
    w.add_argument("--nstep", type=int, default=None)
    w.add_argument("--dopant-index", type=int, default=None)
    w.add_argument("--ranks", type=int, default=None)
    w.add_argument("--campaign", default=None)
    r = sub.add_parser("restart", help="restart part of an A2 relaxation (section 13)")
    r.add_argument("--input", required=True); r.add_argument("--out", required=True)
    r.add_argument("--nstep", type=int, required=True)
    s = sub.add_parser("status", help="section-12 completeness of one single point (no energy)")
    s.add_argument("--dir", required=True); s.add_argument("--label", required=True)
    s.add_argument("--meta", default=None); s.add_argument("--running", action="store_true")
    c = sub.add_parser("counts", help="configuration counts, counters, markers, wall times (no energy)")
    c.add_argument("outs", nargs="+")
    u = sub.add_parser("upf-check", help="UPF identity before the first pw.x job of a campaign")
    u.add_argument("--pseudo-dir", required=True); u.add_argument("--out", required=True)
    u.add_argument("--reference", default=None, help="the C1 upf_check.json (C2-C4)")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test(a.work)
    try:
        if a.cmd == "write":
            at = ase_read(a.cell); at.calc = None
            free = None
            if a.free:
                fr = json.load(open(a.free))
                free = fr["free"] if isinstance(fr, dict) else fr
            m = write_input(at, a.label, a.out, kind=a.kind, free=free, nstep=a.nstep, dopant_index=a.dopant_index,
                            ranks=a.ranks, campaign=a.campaign)
            print(f"{a.label}: {m['kind']}, tot_charge {m['electrons']['tot_charge']}, {m['electrons']['n_el']} "
                  f"electrons, input {m['input_sha256'][:12]}")
        elif a.cmd == "restart":
            print(json.dumps(restart_input(a.input, a.out, a.nstep), indent=1))
        elif a.cmd == "status":
            meta = json.load(open(a.meta)) if a.meta else None
            print(json.dumps(_jsonable(sp_status(a.dir, a.label, meta=meta, running=a.running)), indent=1))
        elif a.cmd == "counts":
            for p in a.outs:
                print(json.dumps({os.path.basename(p): _jsonable(parse_counts(p))}, indent=1))
        elif a.cmd == "upf-check":
            ref = json.load(open(a.reference)) if a.reference else None
            rec = upf_check(a.pseudo_dir, reference=ref, reference_name=os.path.basename(a.reference) if ref else None)
            c46.dump_public(rec, a.out)
            print(f"UPF check passed: {rec['passed']}")
            if not rec["passed"]:
                return 3
        else:
            ap.print_help(); return 1
    except (Refused, S2Error) as e:
        print(f"REFUSED: {type(e).__name__}: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())

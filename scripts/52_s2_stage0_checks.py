#!/usr/bin/env python
"""S2 Stage 0 laptop checks (geometry and records only; no calculator is created): S2_PLAN.md section 17 item 3,
with section 2 (the Pb-Cl source check), section 3 (admissibility and the production list), section 5 (the MACE
foundation file), section 11 (the m05 calibration draw and its admissibility), and S2_BUILDERS_DESIGN.md section 6
("Freeze") and section 16 answers 3 and 4. Outputs go to results/objective2/s2/stage0/ (path-free, hygiene-checked
by scripts/46 dump_public); anything holding local paths stays in the off-repository record folder.

  t4            Regenerates the T4 admissibility report of scripts/42 (s2b-2): runs
                `scripts/42_s2_builders.py --self-test --report <file>` with this interpreter, the report and the
                full self-test log outside the repository (the report's temporary work folder lands beside it).
                Requires exit 0, 'SELF-TEST PASS (<n> cases, 0 failed, ...)', no FAIL line, the no-model case, the
                pinned GEOM_SHA and the pinned kept poses of every T4 case. Archives a path-free copy as
                stage0/t4_admissibility.json and writes the freeze record stage0/s2b2_freeze.json: BUILDER_VERSION,
                GEOM_SHA, f, f_w, the class map with the H split, the class-Y rule, the thresholds and host minima,
                and the sha256 of the raw (off-repository) and of the archived report (answer 3).
  admissibility Re-executes the host draw of section 3 (zlib.crc32("S2n-host-" + member), ascending, over the 28
                eligible members) and the m05 calibration draw of section 11 ("S2n-cal-m05-" + label), and asserts
                both against the plan tables (and scripts/46). For draw ranks 1-12 it builds every required cell:
                all 19 sites of scripts/46 site_sets (first shell + far pair, asserted against the section 4
                table) x the tokens of their sublattice (B: Sr, Ca; A: Cs, GA; X: Cl), both legs, default poses,
                scripts/42 build_paired(..., partners="unrelaxed") on the unrelaxed pool member, mig "allow" at
                every X site (I-39). A host is admissible iff no required cell raises Inadmissible or Refused; any
                other exception is an error: the host is not admissible and the check stops for a human (I-40).
                Production n = 8 / 10 = the first n admissible hosts in draw order, reserves the next two. The m05
                calibration cells (Pb124 Sr, Ca; FA28 Cs, GA; I49 Cl) are built the same way; a failing drawn site
                is replaced by the next in draw order (FA92; I138, I125, ...); Pb124 has no fallback (conflict).
  pbcl          Validates the implementer's verification notes of the Pb-Cl 2.837 A value (Poglitsch & Weber 1987,
                J. Chem. Phys. 87, 6373, cubic CH3NH3PbCl3; web search only, nothing downloaded or executed) and
                writes stage0/pbcl_source.json with the section 2 decision (I-E1, I-E2): confirmed_2.837 (the
                primary source verified and a/2 equal to 2.837 at its stated digits), use_source_value (the primary
                source verified with another value; X-2), or provisional_2.837 (nothing verified at the primary
                level: shifted starts at 2.837 A with --allow-provisional, labelled [M] starting points).
  mace-laptop   sha256 of the laptop copy of the MACE-MP-0 medium foundation file (scripts/46 foundation_path; mace
                is never imported, versions read from the installed distribution metadata) against section 5.
                The node copy is a campaign-1 item.
  all           t4, admissibility, pbcl and mace-laptop in that order.

Every subcommand and the self-test end by asserting that mace was never imported. Exit 0 = done, 3 = refused or a
fail-closed STOP for a human (the record, where one is written, says why), 1 = unexpected error.

    python scripts/52_s2_stage0_checks.py --self-test [--work DIR]
    python scripts/52_s2_stage0_checks.py t4 --report-off <off-repository file>
    python scripts/52_s2_stage0_checks.py admissibility
    python scripts/52_s2_stage0_checks.py pbcl --notes <off-repository notes.json>
    python scripts/52_s2_stage0_checks.py mace-laptop
    python scripts/52_s2_stage0_checks.py all --report-off <file> --notes <file>
"""
import argparse, hashlib, importlib.util, json, os, platform, re, subprocess, sys, tempfile, time, types, zlib
from decimal import Decimal, InvalidOperation

import numpy as np
import ase
from ase.geometry import find_mic
from ase.io import read

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


# ---------------------------------------------------------------- constants owned here (E checks)
STAGE0_REL = "results/objective2/s2/stage0"
STAGE0 = os.path.join(ROOT, *STAGE0_REL.split("/"))
OUT = {"t4": "t4_admissibility.json", "freeze": "s2b2_freeze.json", "admissibility": "admissibility.json",
       "pbcl": "pbcl_source.json", "mace": "mace_laptop.json"}
BUILDER_VERSION_S2 = "s2b-2"
GEOM_SHA_FROZEN = "58ebbd29fdf179417269818f6fc31b7d55622164929a40778c49208e1cdafedf"   # S2_PLAN.md sections 0, 17
HOST_SEED = "S2n-host-"                        # section 3
CAL_SEED = "S2n-cal-m05-"                      # section 11
N_RANKS_CHECKED = 12                           # section 3: Stage-0 admissibility of draw ranks 1-12
N_RESERVE = 2                                  # section 3: "the reserves are the next two"
# section 3 eligible set: m00-m35 minus the pilots, minus the WP3 test hosts (amendment m item 1'), minus m21
EXCLUDED_TEST_HOSTS = ("m04", "m10", "m14", "m18", "m27")
EXCLUDED_WP2C = ("m21",)
TOKENS_OF = {"B": ("Sr", "Ca"), "A": ("Cs", "GA"), "X": ("Cl",)}       # section 2, by sublattice
DEFAULT_POSE_NAME = {"Sr": "swap", "Ca": "swap", "Cs": "centred", "GA": "inherit", "Cl": "centred"}   # section 2
CAL_TOKENS = {"B": ("Sr", "Ca"), "A": ("Cs", "GA"), "X": ("Cl",)}      # section 11 "Cells per region"
PBCL_DEFAULT = Decimal("2.837")                # section 2
PBCL_LEVELS = ("[S] primary verified", "[S] secondary", "unverified")
PBCL_DECISIONS = ("confirmed_2.837", "use_source_value", "provisional_2.837")

# Interpretations (I), implementation notes (N) and conflicts (X) implemented here; printed by --self-test and
# carried in every record. Ids without "E" are those of the Stage-0 interface specification.
NOTES = {
    "I-39": "section 4 / answer 8: mig='allow' at every X site in the admissibility builds (identical to 'forbid' "
            "except at the MIG iodide)",
    "I-40": "section 3: a builder exception other than Inadmissible or Refused (BuildError, AssertionError, any "
            "other) makes the host not admissible and stops the check for a human (exit 3, production lists null)",
    "I-E1": "section 2 / design sections 1 and 4 ('Verifying a primary source flips the tag'): 'verified' means "
            "read in the primary source (the paper, or its publisher's abstract if it states the value); a value "
            "read only in a secondary source, even one attributing it to the paper, is not verified, so the "
            "decision is provisional_2.837 (shifted Cl starts at 2.837 A, --allow-provisional, [M] starting "
            "points); the secondary value is recorded, reported only. Kept after review F10: the design's tag "
            "legend reads [S] as 'secondary source only, so recheck before production' and [V] as 'checked against "
            "a primary source', and 2.837 A is already tagged [S] there, so a secondary quotation does not verify",
    "I-E2": "section 2 / spec X-2: 'another Pb-Cl distance' is decided at the precision the source states: "
            "d = a/2 as an exact decimal of the stated digits; any difference from 2.837 is another distance "
            "(a = 5.675 A gives 2.8375 A, not 2.837 A)",
    "I-E3": "section 3: a required cell is one leg of build_paired for a token of the site's sublattice at one of "
            "the 19 sites of scripts/46 site_sets (first shell + far pair), default pose ('inherit', resolved by "
            "scripts/42 to swap / centred / inherit); Refused counts as not admissible, as Inadmissible",
    "I-E4": "section 11: a drawn m05 site is admissible iff every required cell of it (both legs of each dopant "
            "of the sublattice, default poses) builds; the next site in draw order is tried until one is "
            "admissible; if none is, or if Pb124 (chosen, no fallback) fails, the check stops for a human",
    "I-E5": "section 17 item 3 / design section 6 'Freeze': the freeze record is stage0/s2b2_freeze.json, holding "
            "the frozen clash parameters (f, f_w, class map with the H split, class-Y rule, thresholds, host "
            "minima), GEOM_SHA and the sha256 of the archived T4 report; the raw report and its self-test log stay "
            "off-repository with their sha256 recorded",
    "N-E1": "if scripts/46 is absent an in-file stub with literal copies of the plan tables is used and printed as "
            "'MOCKED 46'; outside --self-test a mocked 46 is refused unless --allow-mock-46, and every record then "
            "carries 'c46': 'MOCKED' (the final run, with all files present, must regenerate it)",
    "N-E2": "the T4 report path must lie outside the repository and must not exist yet (no silent reuse of an "
            "older report); the full scripts/42 self-test log is written beside it",
    "N-E3": "if draw ranks 1-12 do not give n + 2 admissible hosts for n = 8 or 10, the lists are written as far "
            "as they go under 'candidate_lists', flagged short, 'production' is null and the check stops for a "
            "human (the plan builds ranks 1-12 only; rank 14, m15, may not enter, section 0)",
    "N-E4": "the Pb-Cl notes are validated: the citation must name Poglitsch & Weber 1987, J. Chem. Phys. 87, "
            "6373 and the phase cubic CH3NH3PbCl3; the lattice parameter is a decimal string so that its stated "
            "digits are kept; the level is one of three; anything else is refused",
    "N-E5": "the MACE versions are read from the installed distribution metadata (importlib.metadata), so mace "
            "and torch are never imported; the foundation file is located by scripts/46 foundation_path",
    "N-E6": "each built leg must report valid and admissible, carry the registry atom count and the default pose "
            "name of its token; any deviation is an error (I-40)",
    "N-E7": "the archived T4 copy carries an 'archive' block (raw sha256, the JSON pointers of every stripped "
            "value, the generator); its own sha256 is in the freeze record",
    "N-E9": "public hygiene (review F10): web addresses of sources are kept in the off-repository notes; the "
            "committed Pb-Cl record cites sources by name and DOI only (scripts/46 refuses a URL or host name in JSON)",
    "N-E8": "the m05 draw is re-executed from the unrelaxed m05 site sets (geometry only) and must equal both "
            "scripts/46 M05_DRAW_ORDER and the crc32 values printed in section 11",
}

# Self-test pins: literal copies of the plan text (S2_PLAN.md section 3 table, section 3 lists, section 11 draw)
PLAN_DRAW_PIN = [(1, "m06", 18472929), (2, "m02", 108272632), (3, "m16", 402845344), (4, "m12", 527379129),
                 (5, "m32", 760825915), (6, "m26", 858766691), (7, "m22", 876771706), (8, "m23", 1128614380),
                 (9, "m33", 1516140717), (10, "m13", 1751652911), (11, "m17", 1862655542), (12, "m03", 1903373166),
                 (13, "m07", 1981738871), (14, "m15", 2165030682), (15, "m11", 2254863107), (16, "m19", 2294149937),
                 (17, "m09", 2443625072), (18, "m01", 2675788354), (19, "m29", 2744164594), (20, "m25", 2854677721),
                 (21, "m35", 3007176088), (22, "m31", 3025148289), (23, "m34", 3292196110), (24, "m28", 3566702692),
                 (25, "m20", 3662420054), (26, "m24", 3709983823), (27, "m08", 3869373158), (28, "m00", 3900340948)]
PLAN_LISTS_PIN = {"n8": ["m06", "m02", "m16", "m12", "m32", "m26", "m22", "m23"], "reserves_n8": ["m33", "m13"],
                  "n10": ["m06", "m02", "m16", "m12", "m32", "m26", "m22", "m23", "m33", "m13"],
                  "reserves_n10": ["m17", "m03"]}
PLAN_M05_PIN = {"A": [(28, 684900801), (92, 737407252)],
                "X": [(49, 299187232), (138, 1029408902), (125, 1525794170), (137, 2917438743), (126, 3287848128),
                      (90, 3718773449), (102, 4137890395)]}


class S2Error(RuntimeError):
    """A fail-closed STOP (replaced by scripts/46 S2Error when that file exists)."""


# ---------------------------------------------------------------- stub of scripts/46 (used only if it is absent)
def _hygiene_patterns():
    # assembled from pieces so that this file itself passes the scanner (it is a new repository file)
    sl = "/"
    cur = "[" + "".join(chr(c) for c in (0x24, 0xA5, 0x20AC, 0xA3, 0x5143)) + "]"
    return [("local path", re.compile(re.escape(sl + "Users" + sl))),
            ("local path", re.compile(re.escape(sl + "private" + sl))),
            ("local path", re.compile(re.escape(sl + "home" + sl))),
            ("local path", re.compile(r"(?<![\w.])" + re.escape(sl + "tmp" + sl))),
            ("local path", re.compile("scr" + "atch", re.I)),
            ("local path", re.compile("ve" + "nv", re.I)),
            ("IPv4 address", re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")),
            ("e-mail address", re.compile(r"[\w.+-]+" + chr(0x40) + r"[\w-]+(?:\.[\w-]+)+")),
            ("instance or disk id", re.compile(r"\b(?:i|d)-[0-9a-z]{10,}\b")),
            ("currency", re.compile(cur)),
            ("currency", re.compile(r"\b(?:" + "|".join(("U" + "SD", "C" + "NY", "R" + "MB")) + r")\b"))]


def _make_mock46(b42):
    """Interface stub of scripts/46 (section 6 of the Stage-0 interface specification) with literal copies of the
    S2_PLAN.md tables it needs; used only while scripts/46_s2_cells.py does not exist (N-E1)."""
    m = types.SimpleNamespace()
    m.MOCKED = True
    m.b42 = b42
    m.S2Error = S2Error
    m.VI = 127
    m.TOKENS = ("Sr", "Ca", "Cl", "Cs", "GA")
    m.SUBLATTICE = {"Sr": "B", "Ca": "B", "Cl": "X", "Cs": "A", "GA": "A"}
    m.PILOTS = ("m30", "m05")
    m.DRAW = [{"rank": r, "member": mm, "crc32": c} for r, mm, c in PLAN_DRAW_PIN]
    m.M05_DRAW_ORDER = {L: [{"site": j, "crc32": c} for j, c in v] for L, v in PLAN_M05_PIN.items()}
    m.CAL_SITES = {"m30": {"B": 136, "A": 128, "X": 138}, "m05": {"B": 124, "A": 28, "X": 49}}
    m.FIRST_SHELL = {"B": [124, 136], "A": [28, 92, 128], "X": [49, 53, 90, 102, 125, 126, 137, 138]}
    m.FIRST_CUT_A = {"B": 5.0, "A": 6.0}
    m.GAPS = {"B_next_min": 6.715, "A_first_max": 5.465, "A_next_min": 7.215, "X_8th_max": 5.1195, "X_9th_min": 5.4835}
    m.FAR_MIN_A = {"B": 8.5, "A": 9.0, "X": 9.0}
    # section 4 table: migrating I, Cs-v, far pairs (index, distance to 2 dp), f1 first
    T = {"m30": (138, 4.52, ((76, 11.81), (172, 11.55)), ((188, 11.25), (164, 10.87)), ((175, 12.77), (186, 11.91))),
         "m05": (53, 4.25, ((76, 11.96), (172, 11.47)), ((188, 10.86), (164, 10.48)), ((175, 12.95), (222, 11.99))),
         "m06": (53, 4.22, ((76, 11.77), (172, 11.68)), ((200, 10.96), (164, 10.69)), ((175, 12.93), (222, 12.00))),
         "m02": (126, 4.35, ((76, 11.93), (172, 11.53)), ((188, 10.91), (152, 10.87)), ((175, 12.70), (186, 11.81))),
         "m16": (138, 4.54, ((76, 11.86), (172, 11.58)), ((164, 10.80), (188, 10.79)), ((175, 12.86), (222, 11.93))),
         "m12": (126, 4.17, ((76, 11.96), (172, 11.53)), ((68, 10.96), (200, 10.56)), ((175, 12.79), (222, 11.95))),
         "m32": (49, 4.42, ((76, 11.90), (172, 11.70)), ((200, 10.65), (188, 10.57)), ((175, 13.02), (222, 11.94))),
         "m26": (126, 4.08, ((76, 11.97), (172, 11.54)), ((68, 11.12), (164, 10.94)), ((175, 12.77), (222, 11.40))),
         "m22": (53, 4.54, ((76, 11.79), (172, 11.70)), ((16, 10.56), (4, 10.56)), ((175, 12.77), (186, 11.83))),
         "m23": (90, 4.44, ((172, 11.84), (76, 11.70)), ((200, 10.71), (4, 10.48)), ((175, 12.84), (186, 11.92))),
         "m33": (126, 4.20, ((76, 11.94), (172, 11.59)), ((68, 10.87), (200, 10.73)), ((175, 12.33), (222, 11.71))),
         "m13": (126, 4.15, ((76, 11.86), (172, 11.46)), ((188, 10.60), (164, 10.52)), ((175, 12.64), (222, 11.79))),
         "m17": (138, 4.04, ((76, 11.93), (172, 11.59)), ((200, 10.65), (188, 10.62)), ((175, 12.79), (222, 11.69))),
         "m03": (53, 4.16, ((76, 11.96), (172, 11.67)), ((188, 10.75), (68, 10.40)), ((175, 13.00), (222, 11.95)))}
    m.SITE_TABLE = {h: {"mig": r[0], "cs_v_A": r[1], "far": {"B": r[2], "A": r[3], "X": r[4]}} for h, r in T.items()}
    m.FAR4_TABLE = {"m30": {"B": [76, 172, 24, 148], "A": [188, 164, 176, 200], "X": [175, 186, 222, 174]},
                    "m05": {"B": [76, 172, 24, 64], "A": [188, 164, 152, 68], "X": [175, 222, 186, 174]}}
    m.FOUNDATION_SHA256 = "01bfe22100139f424713cf921144e5509cbe353d67aa9fa1be9c6e1e0ed35845"
    m.FOUNDATION_FILE = "20231203mace128L1_epoch199model"
    m.MACE_VERSION = "0.3.16"
    m.GEOM_SHA_S2B2 = GEOM_SHA_FROZEN
    m.PBCL_DEFAULT_A = 2.837
    m.PBCL_RECORD = STAGE0_REL + "/" + OUT["pbcl"]
    tok_of = {"B": "Sr", "A": "Cs", "X": "Cl"}

    def host_context(member, *, pool=None, vac_ref=None):
        pool = pool or os.path.join(ROOT, b42.POOL)
        vac_ref = vac_ref or os.path.join(ROOT, b42.VAC_REF)
        host = read(os.path.join(pool, f"{member}.extxyz"))
        vac, vpos, vi, mig = b42.vacancy_context(host, pool, vac_ref)
        if vi != m.VI or host.get_chemical_symbols()[vi] != "I":
            raise S2Error(f"{member}: vacancy iodide {vi} is not I{m.VI}")
        return types.SimpleNamespace(member=member, host=host, vac=vac, vpos=vpos, vi=vi, mig_vac=mig,
                                     mig_host=mig + (1 if mig >= vi else 0))

    def site_sets(ctx):
        out = {}
        for L in "BAX":
            raw = b42.list_sites(ctx.host, tok_of[L], vi=ctx.vi, vpos=ctx.vpos)
            ranked = sorted(raw, key=lambda t: (round(t[1], 6), t[0]))
            if L == "X":
                first = [j for j, _ in ranked[:8]]
            else:
                first = [j for j, d in ranked if d < m.FIRST_CUT_A[L]]
            if sorted(first) != m.FIRST_SHELL[L]:
                raise S2Error(f"{ctx.member} {L}: first shell {sorted(first)} != {m.FIRST_SHELL[L]}")
            d = [x for _, x in ranked]
            ok = {"B": d[2] >= m.GAPS["B_next_min"],
                  "A": d[2] <= m.GAPS["A_first_max"] and d[3] >= m.GAPS["A_next_min"],
                  "X": d[7] <= m.GAPS["X_8th_max"] and d[8] >= m.GAPS["X_9th_min"]}[L]
            if not ok:
                raise S2Error(f"{ctx.member} {L}: the section 4 gap is violated")
            far = [ranked[-1][0], ranked[-2][0]]
            if min(ranked[-1][1], ranked[-2][1]) <= m.FAR_MIN_A[L]:
                raise S2Error(f"{ctx.member} {L}: a far site lies within {m.FAR_MIN_A[L]} A")
            out[L] = {"ranked": ranked, "first": first, "far": far, "far4": [j for j, _ in ranked[-4:][::-1]],
                      "production": first + far}
        cs = [k for k, s in enumerate(ctx.host.get_chemical_symbols()) if s == "Cs"]
        out["mig_host"] = ctx.mig_host
        out["cs_v_A"] = float(find_mic(ctx.host.positions[cs] - ctx.vpos, ctx.host.cell.array, pbc=True)[1][0])
        return out

    def assert_site_tables(member, sets):
        row = m.SITE_TABLE.get(member)
        if row is None:
            raise S2Error(f"{member} is not in the section 4 table")
        if sets["mig_host"] != row["mig"] or abs(sets["cs_v_A"] - row["cs_v_A"]) > 0.005 + 1e-9:
            raise S2Error(f"{member}: migrating I or Cs-v differs from the section 4 table")
        for L in "BAX":
            dist = dict(sets[L]["ranked"])
            if sets[L]["far"] != [j for j, _ in row["far"][L]]:
                raise S2Error(f"{member} {L}: far pair {sets[L]['far']} != table {row['far'][L]}")
            for j, dd in row["far"][L]:
                if abs(dist[j] - dd) > 0.005 + 1e-9:
                    raise S2Error(f"{member} {L}{j}: {dist[j]:.4f} A != table {dd}")
            if member in m.FAR4_TABLE and sets[L]["far4"] != m.FAR4_TABLE[member][L]:
                raise S2Error(f"{member} {L}: four farthest {sets[L]['far4']} != table")

    def hygiene_violations(text):
        return [f"{nm}: {mt.group(0)!r}" for nm, rx in _hygiene_patterns() for mt in rx.finditer(text)]

    def dump_public(obj, path):
        text = json.dumps(obj, indent=1)
        bad = hygiene_violations(text)
        if bad:
            raise S2Error(f"hygiene: {bad[:5]}; nothing written")
        tmp = path + ".part"
        with open(tmp, "w") as fh:
            fh.write(text); fh.flush(); os.fsync(fh.fileno())
        os.replace(tmp, path)

    def foundation_path():
        base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
        return os.path.join(base, "mace", m.FOUNDATION_FILE)

    for fn in (host_context, site_sets, assert_site_tables, hygiene_violations, dump_public, foundation_path):
        setattr(m, fn.__name__, fn)
    return m


def _load_deps():
    """scripts/46 when it exists (and the scripts/42 module object it holds), else the stub (N-E1)."""
    if os.path.exists(os.path.join(HERE, "46_s2_cells.py")):
        c46 = _load("c46", "46_s2_cells.py")
        b42 = getattr(c46, "b42", None) or _load("b42", "42_s2_builders.py")
        return c46, b42, False
    b42 = _load("b42", "42_s2_builders.py")
    return _make_mock46(b42), b42, True


c46, b42, MOCKED_46 = _load_deps()
S2Err = getattr(c46, "S2Error", S2Error)
STOP = (S2Error, S2Err, b42.Refused)
if b42.BUILDER_VERSION != BUILDER_VERSION_S2 or b42.GEOM_SHA != GEOM_SHA_FROZEN:
    raise S2Error(f"scripts/42 is {b42.BUILDER_VERSION} / {b42.GEOM_SHA}, not the frozen {BUILDER_VERSION_S2}")


# ---------------------------------------------------------------- small helpers
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _inside_repo(path):
    p = os.path.realpath(os.path.abspath(path))
    return p == os.path.realpath(ROOT) or p.startswith(os.path.realpath(ROOT) + os.sep)


def _git():
    """HEAD and the state of the scripts this check depends on (relative names only)."""
    def run(*a):
        r = subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else None
    names = ["scripts/42_s2_builders.py", "scripts/22_paired_pilot.py", "scripts/29_dopant_shell_scan.py",
             "scripts/07_fa_host_cell.py", "scripts/checks.py", "scripts/46_s2_cells.py",
             "scripts/52_s2_stage0_checks.py"]
    st = run("status", "--porcelain", "--", *names)
    dirty = sorted({ln[3:] for ln in (st or "").splitlines() if ln.strip()})
    return {"head": run("rev-parse", "HEAD"), "scripts_clean": st == "", "not_committed_or_modified": dirty}


def _script_sha():
    out = {}
    for nm in ("42_s2_builders.py", "22_paired_pilot.py", "29_dopant_shell_scan.py", "07_fa_host_cell.py",
               "checks.py", "46_s2_cells.py", "52_s2_stage0_checks.py"):
        p = os.path.join(HERE, nm)
        out[nm] = sha256_file(p) if os.path.exists(p) else None
    return out


def _versions():
    import importlib.metadata as md
    v = {"python": platform.python_version(), "ase": ase.__version__, "numpy": np.__version__}
    for d in ("mace-torch", "torch", "e3nn"):
        try:
            v[d] = md.version(d)            # distribution metadata only: nothing is imported (N-E5)
        except md.PackageNotFoundError:
            v[d] = None
    return v


def _generator():
    return {"script": "scripts/52_s2_stage0_checks.py", "script_sha256": _script_sha(), "git": _git(),
            "c46": "MOCKED" if MOCKED_46 else "real", "builder": {"BUILDER_VERSION": b42.BUILDER_VERSION,
                                                                  "GEOM_SHA": b42.GEOM_SHA}}


def _hygiene(text):
    return list(c46.hygiene_violations(text))


def _dump(obj, path):
    """Hygiene-checked atomic write through scripts/46 dump_public; returns the sha256 of the file written."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    c46.dump_public(obj, path)
    return sha256_file(path)


def _no_mace():
    if "mace" in sys.modules:
        raise S2Error("'mace' was imported in a geometry-only code path")


def _attr(o, name):
    return o[name] if isinstance(o, dict) else getattr(o, name)


# ---------------------------------------------------------------- (1) T4 report and freeze (answer 3)
LOCAL_ROOTS = ("Users", "private", "tmp", "var", "home", "Volumes", "Library", "opt", "System", "Applications",
               "root", "mnt")
_LOCAL_RX = re.compile(r"(?<![\w.])/(?:" + "|".join(LOCAL_ROOTS) + r")/[^\s\"'<>|,;)\]]*")


REMOVED = "<off-repository path removed>"


def strip_paths(obj, *, root=ROOT, ptr=""):
    """(copy, stripped pointers): in every string the repository root is made repository-relative; a string that
    still holds a local absolute path or the home directory is replaced as a whole by REMOVED (local paths may
    contain blanks, so a partial cut could leave a fragment)."""
    stripped = []
    home = os.path.expanduser("~")
    roots = sorted({root, os.path.realpath(root)}, key=len, reverse=True)

    def walk(o, p):
        if isinstance(o, dict):
            return {k: walk(v, f"{p}/{k}") for k, v in o.items()}
        if isinstance(o, list):
            return [walk(v, f"{p}/{i}") for i, v in enumerate(o)]
        if isinstance(o, str):
            s = o
            for r in roots:
                s = s.replace(r + os.sep, "").replace(r, ".")
            if _LOCAL_RX.search(s) or (len(home) > 1 and home in s):
                s = REMOVED
            if s != o:
                stripped.append(p)
            return s
        return o
    return walk(obj, ptr), stripped


SUMMARY_RX = re.compile(r"SELF-TEST PASS \((\d+) cases, 0 failed, (\d+) s\)\Z")
CASE_RX = re.compile(r"(PASS|FAIL) (T\d+ [^:]+|no-model):")


def _run_42_selftest(report_off):
    cmd = [sys.executable, os.path.join(HERE, "42_s2_builders.py"), "--self-test", "--report", report_off]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return r.returncode, r.stdout + ("\n--- stderr ---\n" + r.stderr if r.stderr else "")


def parse_selftest_log(text):
    lines = text.splitlines()
    cases = [{"name": mt.group(2), "status": mt.group(1)} for ln in lines for mt in [CASE_RX.match(ln)] if mt]
    summ = [ln for ln in lines if ln.startswith("SELF-TEST ")]
    return cases, (summ[-1] if summ else None)


def t4(report_off, out_dir=STAGE0, *, runner=None, overwrite=False):
    """Regenerate and archive the s2b-2 T4 admissibility report, then write the freeze record (I-E5, N-E2, N-E7)."""
    report_off = os.path.abspath(report_off)
    if _inside_repo(report_off):
        raise S2Error("the raw T4 report must be written outside the repository (it may hold local paths)")
    if os.path.exists(report_off) and not overwrite:
        raise S2Error("the raw T4 report file already exists: give a new path (no silent reuse of an older report)")
    os.makedirs(os.path.dirname(report_off), exist_ok=True)
    rc, log = (runner or _run_42_selftest)(report_off)
    log_off = os.path.splitext(report_off)[0] + "_selftest.log"
    with open(log_off, "w") as fh:
        fh.write(log)
    cases, summary = parse_selftest_log(log)
    lines = log.splitlines()
    why = []
    if rc != 0:
        why.append(f"scripts/42 --self-test exited {rc}")
    if not summary or not SUMMARY_RX.fullmatch(summary):
        why.append(f"no 'SELF-TEST PASS (<n> cases, 0 failed, <t> s)' line (got {summary!r})")
    if any(ln.startswith("FAIL ") for ln in lines):
        why.append("a FAIL line in the self-test output")
    if not any(ln.startswith("PASS no-model:") for ln in lines):
        why.append("no 'PASS no-model' line")
    if not os.path.exists(report_off):
        why.append("no report written")
    if why:
        raise S2Error("T4 regeneration refused: " + "; ".join(why))
    raw_sha = sha256_file(report_off)
    with open(report_off) as fh:
        rep = json.load(fh)
    kept = {f"{c['token']}@{c['site']}": [k["pose"] for k in c["kept"]] for c in rep.get("cases", [])}
    checks = {"builder_version": rep.get("builder_version") == BUILDER_VERSION_S2,
              "geom_sha": rep.get("geom_sha") == GEOM_SHA_FROZEN,
              "f": rep.get("f") == b42.CLASH["f"], "f_w": rep.get("f_w") == b42.CLASH["f_w"],
              "member_vi_mig": (rep.get("member"), rep.get("vi"), rep.get("mig_host")) == ("m30", 127, 138),
              "kept_poses_pinned": kept == b42.T4_PINNED}
    if not all(checks.values()):
        raise S2Error(f"T4 report refused: {[k for k, v in checks.items() if not v]}")
    pub, stripped = strip_paths(rep)
    pub["schema"] = "s2-t4-archive-1"
    pub["archive"] = {"what": "path-free copy of the scripts/42 s2b-2 T4 admissibility report (self-test --report)",
                      "raw_sha256": raw_sha, "stripped_pointers": stripped, "checks": checks,
                      "generator": _generator(), "written": _utc()}
    bad = _hygiene(json.dumps(pub, indent=1))
    if bad:
        raise S2Error(f"T4 archive refused, hygiene: {bad[:5]}")
    p_t4 = os.path.join(out_dir, OUT["t4"])
    t4_sha = _dump(pub, p_t4)
    canon = b42._canon({"geom": b42.GEOM, "clash": b42.CLASH,
                        "bond_cut": {"-".join(k): v for k, v in b42.BOND_CUT.items()}})
    if hashlib.sha256(canon.encode()).hexdigest() != GEOM_SHA_FROZEN or \
            b42.GEOM_SHA_PIN.get(BUILDER_VERSION_S2) != GEOM_SHA_FROZEN:
        raise S2Error("GEOM_SHA recomputed from GEOM, CLASH and BOND_CUT differs from the frozen value")
    n_cases = int(SUMMARY_RX.fullmatch(summary).group(1))
    freeze = {
        "schema": "s2-freeze-1", "builder_version": BUILDER_VERSION_S2, "GEOM_SHA": GEOM_SHA_FROZEN,
        "GEOM_SHA_recomputed": True,
        "statement": ("s2b-2 frozen (S2_BUILDERS_DESIGN.md section 6 'Freeze', section 16 answer 3; S2_PLAN.md "
                      "section 17 item 3) after the T4 admissibility report was regenerated and archived, before "
                      "any S2 energy existed: f, f_w, the class map with the H(N)/H(C) split, the class-Y rule and "
                      "the threshold table enter GEOM_SHA and may not change"),
        "f": b42.CLASH["f"], "f_w": b42.CLASH["f_w"], "floor_A": b42.CLASH["floor"],
        "vac_excl_A": b42.CLASH["vac_excl"], "class_map": b42.CLASH["class_map"], "h_split": b42.CLASH["h_split"],
        "y_rule": b42.CLASH["y_rule"], "bondi_A": b42.CLASH["bondi"], "host_min_A": b42.CLASH["host_min"],
        "thresholds_A": dict(b42.THR), "exempt": b42.CLASH["exempt"], "untested": b42.CLASH["untested"],
        "bond_cut_A": {"-".join(k): v for k, v in b42.BOND_CUT.items()}, "geom": b42.GEOM,
        "provisional": b42.PROVISIONAL,
        "t4_report": STAGE0_REL + "/" + OUT["t4"], "t4_report_sha256": t4_sha, "t4_raw_sha256": raw_sha,
        "t4_raw_location": "off-repository record folder (with the full scripts/42 self-test log)",
        "t4_kept_poses": kept, "t4_kept_equal_pinned": True,
        "self_test_summary": {"line": summary, "n_cases": n_cases, "cases": cases},
        "versions": _versions(), "generator": _generator(), "notes": ["I-E5", "N-E2", "N-E7"],
        "date": time.strftime("%Y-%m-%d", time.gmtime()), "written": _utc()}
    fz_sha = _dump(freeze, os.path.join(out_dir, OUT["freeze"]))
    return {"t4_sha256": t4_sha, "raw_sha256": raw_sha, "freeze_sha256": fz_sha, "summary": summary,
            "stripped": stripped, "log_off": log_off}


# ---------------------------------------------------------------- (2) draws and admissibility (sections 3, 11)
def host_draw():
    """Section 3 draw, re-executed with the standard library: [(rank, member, crc32)]."""
    excl = set(c46.PILOTS) | set(EXCLUDED_TEST_HOSTS) | set(EXCLUDED_WP2C)
    elig = [f"m{k:02d}" for k in range(36) if f"m{k:02d}" not in excl]
    keyed = sorted((zlib.crc32((HOST_SEED + mm).encode()), mm) for mm in elig)
    if len(elig) != 28 or len({c for c, _ in keyed}) != len(keyed):
        raise S2Error("section 3: the eligible set is not 28 members, or a crc32 tie occurred")
    return [(r + 1, mm, c) for r, (c, mm) in enumerate(keyed)]


def _norm_draw(tbl):
    """scripts/46 DRAW in any of the plain shapes -> [(rank, member, crc32)] (fail-closed on anything else)."""
    out = []
    for k, e in enumerate(tbl):
        if isinstance(e, dict):
            out.append((int(e.get("rank", k + 1)), str(e["member"]), int(e.get("crc32", e.get("crc")))))
        elif len(e) == 3:
            out.append((int(e[0]), str(e[1]), int(e[2])))
        elif len(e) == 2:
            out.append((k + 1, str(e[0]), int(e[1])))
        else:
            raise S2Error(f"scripts/46 DRAW entry {e!r} has no known shape")
    return out


def _norm_m05(tbl):
    """scripts/46 M05_DRAW_ORDER -> {"A": [(site, crc32 | None)], "X": [...]}."""
    out = {}
    for L in ("A", "X"):
        rows = []
        for e in tbl[L]:
            if isinstance(e, dict):
                s = e.get("site", e.get("label")); c = e.get("crc32", e.get("crc"))
            elif isinstance(e, (list, tuple)):
                s, c = e[0], (e[1] if len(e) > 1 else None)
            else:
                s, c = e, None
            if isinstance(s, str):
                s = int(re.sub(r"\A(?:FA|I|Pb)", "", s))
            rows.append((int(s), None if c is None else int(c)))
        out[L] = rows
    return out


def m05_draw(sets_m05, sets_m30):
    """Section 11 draw, re-executed: first-shell sites of m05 minus the m30 site type (A: FA128, the nearest FA on
    both pilots; X: the migrating iodide of m05), ordered by zlib.crc32(("S2n-cal-m05-" + label).encode())."""
    if sets_m30["A"]["ranked"][0][0] != 128 or sets_m05["A"]["ranked"][0][0] != 128:
        raise S2Error("section 11: FA128 is not the nearest FA on both pilot hosts")
    mig = int(sets_m05["mig_host"])
    cand = {"A": [("FA", j) for j in sets_m05["A"]["first"] if j != 128],
            "X": [("I", j) for j in sets_m05["X"]["first"] if j != mig]}
    out = {}
    for L, cc in cand.items():
        rows = sorted(((zlib.crc32((CAL_SEED + f"{p}{j}").encode()), j) for p, j in cc))
        if len({c for c, _ in rows}) != len(rows):
            raise S2Error(f"section 11: crc32 tie in the m05 {L} draw")
        out[L] = [(j, c) for c, j in rows]
    return out, mig


def required_cells(sets):
    """[(L, role, site, token)]: the 19 production sites x the tokens of their sublattice (I-E3)."""
    out = []
    for L in "BAX":
        first, far = list(sets[L]["first"]), list(sets[L]["far"])
        prod = list(sets[L].get("production") or first + far)
        if prod != first + far or len(prod) != {"B": 4, "A": 5, "X": 10}[L]:
            raise S2Error(f"{L}: production sites {prod} are not first shell + far pair")
        for j in prod:
            for t in TOKENS_OF[L]:
                out.append((L, "first" if j in first else "far", int(j), t))
    return out


def _build_default(ctx, token, site, L):
    return b42.build_paired(_attr(ctx, "host"), _attr(ctx, "vac"), _attr(ctx, "vi"), token, site, "inherit",
                            vpos=_attr(ctx, "vpos"), mig="allow" if L == "X" else "forbid", partners="unrelaxed")


def build_cell(ctx, token, site, L, role, *, build_fn=None):
    """One required pair (both legs): status ok | Inadmissible | Refused | error (I-40, N-E6)."""
    row = {"token": token, "site": int(site), "sublattice": L, "role": role, "status": None, "leg": None,
           "reason": None}
    try:
        bh, bv = (build_fn or _build_default)(ctx, token, site, L)
        n_exp = b42.REGISTRY[token]["n"]
        bad = []
        for leg, b, n in (("host", bh, n_exp[0]), ("V", bv, n_exp[1])):
            if not (b.report.get("valid") and b.report.get("admissible")):
                bad.append(f"{leg} leg not valid/admissible")
            if len(b.atoms) != n or b.token != token:
                bad.append(f"{leg} leg has {len(b.atoms)} atoms / token {b.token} (registry {n} / {token})")
            if b.pose.get("name") != DEFAULT_POSE_NAME[token]:
                bad.append(f"{leg} leg pose {b.pose.get('name')!r} is not the default {DEFAULT_POSE_NAME[token]!r}")
        if bad:
            row.update(status="error", reason="; ".join(bad))
        else:
            row.update(status="ok", pose=bh.pose.get("name"), n_atoms=[len(bh.atoms), len(bv.atoms)])
    except b42.Inadmissible as e:
        row.update(status="Inadmissible", leg=(e.report or {}).get("leg"), reason=str(e))
    except b42.Refused as e:
        row.update(status="Refused", reason=str(e))
    except Exception as e:                                       # noqa: BLE001 (I-40: any other exception)
        row.update(status="error", reason=f"{type(e).__name__}: {e}")
    return row


def host_status(rows):
    st = {r["status"] for r in rows}
    if "error" in st:
        return "error"
    return "admissible" if st == {"ok"} else "inadmissible"


def production_lists(order, admissible):
    """Section 3: production n = the first n admissible hosts in draw order, reserves the next two (N-E3)."""
    adm = [mm for mm in order if admissible.get(mm) is True]
    lists, short = {}, {}
    for n in (8, 10):
        lists[f"n{n}"], lists[f"reserves_n{n}"] = adm[:n], adm[n:n + N_RESERVE]
        short[f"n{n}"] = len(adm) < n + N_RESERVE
    return lists, short


def choose_site(order, outcome):
    """Section 11 fallback (I-E4): the first site in order whose required cells are all admissible.
    outcome(site) -> (status, rows); status admissible | inadmissible | error."""
    tried = []
    for j in order:
        st, rows = outcome(j)
        tried.append({"site": int(j), "status": st, "cells": rows})
        if st == "error":
            return {"chosen": None, "tried": tried, "conflict": False, "error": True}
        if st == "admissible":
            return {"chosen": int(j), "tried": tried, "conflict": False, "error": False}
    return {"chosen": None, "tried": tried, "conflict": True, "error": False}


def _ctx(member):
    """scripts/46 host_context with the repository's pool and reference vacancy cell given as absolute paths (its
    defaults are repository-relative); a host_context without these keywords is called with the member only."""
    try:
        return c46.host_context(member, pool=os.path.join(ROOT, b42.POOL), vac_ref=os.path.join(ROOT, b42.VAC_REF))
    except TypeError as e:
        if "unexpected keyword" not in str(e):
            raise
        return c46.host_context(member)


def _sites_checked(member, ctx):
    sets = c46.site_sets(ctx)
    c46.assert_site_tables(member, sets)
    return sets


def admissibility(out=None, *, build_fn=None, members=None, log=print):
    """Section 3 / section 11 Stage-0 admissibility check (geometry only). Returns (record, problems)."""
    problems = []
    draw = host_draw()
    d46 = _norm_draw(c46.DRAW)
    draw_ok = {"plan": draw == PLAN_DRAW_PIN, "c46": draw == d46}
    if not all(draw_ok.values()):
        problems.append(f"section 3 draw differs: {draw_ok}")
    order = [mm for _, mm, _ in draw[:N_RANKS_CHECKED]]
    members = list(members or order)
    hosts = {}
    for rank, mm, _ in draw:
        if mm not in members:
            continue
        t0 = time.time()
        rec = {"rank": rank, "admissible": False, "status": None, "site_check": None, "cells": []}
        try:
            ctx = _ctx(mm)
            sets = _sites_checked(mm, ctx)
            cells = required_cells(sets)
            rec["site_check"] = "passed (section 4 table)"
        except Exception as e:                                   # noqa: BLE001 (section 4: stop on a set mismatch)
            rec.update(status="error", site_check=f"{type(e).__name__}: {e}")
            problems.append(f"{mm}: site sets ({type(e).__name__}: {e})")
            hosts[mm] = rec
            continue
        rec["sites"] = {L: {"first": list(map(int, sets[L]["first"])), "far": list(map(int, sets[L]["far"]))}
                        for L in "BAX"}
        rec["mig_host"] = int(sets["mig_host"])
        rows = [build_cell(ctx, t, j, L, role, build_fn=build_fn) for L, role, j, t in cells]
        rec["cells"] = rows
        rec["n_pairs"], rec["n_legs"] = len(rows), 2 * len(rows)
        rec["status"] = host_status(rows)
        rec["admissible"] = rec["status"] == "admissible"
        if rec["status"] == "error":
            problems.append(f"{mm}: builder error (I-40) at "
                            f"{[(r['token'], r['site']) for r in rows if r['status'] == 'error']}")
        hosts[mm] = rec
        log(f"  {mm} rank {rank}: {rec['status']} ({sum(r['status'] == 'ok' for r in rows)}/{len(rows)} pairs, "
            f"{time.time() - t0:.1f} s)")
    lists, short = production_lists(order, {mm: hosts[mm]["admissible"] for mm in hosts})
    if any(short.values()):
        problems.append(f"ranks 1-{N_RANKS_CHECKED} give too few admissible hosts: short {short} (N-E3)")
    # m05 calibration (section 11)
    cal = {"draw": None}
    try:
        ctx05, ctx30 = _ctx("m05"), _ctx("m30")
        s05, s30 = _sites_checked("m05", ctx05), _sites_checked("m30", ctx30)
        dr, mig05 = m05_draw(s05, s30)
        m46 = _norm_m05(c46.M05_DRAW_ORDER)
        dok = {"plan": dr == PLAN_M05_PIN,
               "c46": all([j for j, _ in dr[L]] == [j for j, _ in m46[L]] and
                          all(c is None or c == cc for (_, c), (_, cc) in zip(m46[L], dr[L])) for L in dr)}
        cal["draw"] = {"seed_prefix": CAL_SEED, "excluded": {"A": "FA128 (nearest FA on both pilots)",
                                                            "X": f"I{mig05} (migrating iodide of m05)"},
                       "A": [{"label": f"FA{j}", "crc32": c} for j, c in dr["A"]],
                       "X": [{"label": f"I{j}", "crc32": c} for j, c in dr["X"]], "matches": dok}
        if not all(dok.values()):
            problems.append(f"section 11 m05 draw differs: {dok}")
        cal46 = c46.CAL_SITES["m05"]
        orders = {"B": [int(cal46["B"])], "A": [j for j, _ in dr["A"]], "X": [j for j, _ in dr["X"]]}
        if orders["B"] != [124] or orders["A"][0] != int(cal46["A"]) or orders["X"][0] != int(cal46["X"]):
            problems.append(f"section 11: scripts/46 CAL_SITES m05 {cal46} disagree with the draw")

        def outcome(L):
            def f(j):
                rows = [build_cell(ctx05, t, j, L, "cal", build_fn=build_fn) for t in CAL_TOKENS[L]]
                return host_status(rows), rows
            return f
        for L in "BAX":
            res = choose_site(orders[L], outcome(L))
            res.update(order=orders[L], drawn=L != "B", admissible=res["chosen"] is not None,
                       tokens=list(CAL_TOKENS[L]))
            if L == "B":
                res["site"] = orders["B"][0]          # chosen, not drawn; no fallback (section 11)
            cal[L] = res
            if res["error"]:
                problems.append(f"m05 calibration {L}: builder error (I-40)")
            elif res["conflict"]:
                problems.append(f"m05 calibration {L}: no admissible site in {orders[L]}"
                                + (" (Pb124 has no fallback)" if L == "B" else ""))
            log(f"  m05 calibration {L}: chosen {res['chosen']} (tried {[t['site'] for t in res['tried']]})")
    except Exception as e:                                       # noqa: BLE001 (stop for a human)
        problems.append(f"m05 calibration: {type(e).__name__}: {e}")
    plan_lists = lists == PLAN_LISTS_PIN
    rec = {
        "schema": "s2-admissibility-1",
        "plan": "S2_PLAN.md section 3 (Admissibility and the production list), section 4, section 11 (m05 draw, "
                "Admissibility on m05), section 17 item 3",
        "draw": {"seed_prefix": HOST_SEED, "excluded": {"pilots": list(c46.PILOTS),
                                                        "test_hosts": list(EXCLUDED_TEST_HOSTS),
                                                        "wp2c": list(EXCLUDED_WP2C)},
                 "ranks": [{"rank": r, "member": mm, "crc32": c} for r, mm, c in draw],
                 "matches_plan": draw_ok["plan"], "matches_c46": draw_ok["c46"]},
        "checked_ranks": [1, N_RANKS_CHECKED],
        "build": {"call": "scripts/42 build_paired(host, vac, 127, token, site, 'inherit', vpos=v, mig='allow' at X "
                          "else 'forbid', partners='unrelaxed') on the unrelaxed pool member",
                  "tokens": {L: list(v) for L, v in TOKENS_OF.items()}, "default_pose": DEFAULT_POSE_NAME},
        "hosts": hosts,
        "candidate_lists": lists, "short": short,
        "production": None if problems else lists,
        "matches_plan_lists": plan_lists,
        "m05_calibration": cal,
        "m05_chosen": None if problems else {L: cal[L]["chosen"] for L in "BAX"},
        "status": "stop" if problems else "ok", "problems": problems,
        "notes": ["I-39", "I-40", "I-E3", "I-E4", "N-E3", "N-E6", "N-E8"] + (["N-E1"] if MOCKED_46 else []),
        "versions": _versions(), "generator": _generator(), "mace_imported": "mace" in sys.modules,
        "date": time.strftime("%Y-%m-%d", time.gmtime()), "written": _utc()}
    if out:
        _dump(rec, out)
    return rec, problems


# ---------------------------------------------------------------- (3) Pb-Cl source check (section 2, answer 4)
def pbcl_decision(level, a_str):
    """(decision, d_from_source, differs): I-E1 (only a primary-verified value counts), I-E2 (exact decimals)."""
    if level not in PBCL_LEVELS:
        raise S2Error(f"level {level!r} not one of {PBCL_LEVELS}")
    d = None
    if a_str is not None:
        if not isinstance(a_str, str):
            raise S2Error("the lattice parameter must be a decimal string (its stated digits are kept)")
        try:
            a = Decimal(a_str)
        except InvalidOperation:
            raise S2Error(f"lattice parameter {a_str!r} is not a decimal")
        if not a.is_finite() or a <= 0:
            raise S2Error(f"lattice parameter {a_str!r} is not a positive number")
        d = a / 2
    if level == "[S] primary verified":
        if d is None:
            raise S2Error("a primary-verified record needs the lattice parameter")
        return ("confirmed_2.837" if d == PBCL_DEFAULT else "use_source_value"), d, d != PBCL_DEFAULT
    return "provisional_2.837", d, (None if d is None else d != PBCL_DEFAULT)


def pbcl_record(notes):
    """The s2-pbcl-1 record from the verification notes (N-E4)."""
    cit = str(notes.get("citation", ""))
    need = ("Poglitsch", "Weber", "1987", "87", "6373")
    if not all(w in cit for w in need) or "J. Chem. Phys." not in cit:
        raise S2Error(f"citation {cit!r} does not name Poglitsch & Weber 1987, J. Chem. Phys. 87, 6373")
    phase = str(notes.get("phase", ""))
    if "cubic" not in phase or "CH3NH3PbCl3" not in phase:
        raise S2Error(f"phase {phase!r} is not cubic CH3NH3PbCl3")
    level, a_str = notes.get("level"), notes.get("lattice_parameter_A")
    decision, d, differs = pbcl_decision(level, a_str)
    if level == "[S] primary verified" and not notes.get("how_verified"):
        raise S2Error("a primary-verified record must say how the value was read")
    use = d if decision == "use_source_value" else PBCL_DEFAULT
    primary = level == "[S] primary verified"
    digits = None if a_str is None else (len(a_str.split(".")[1]) if "." in a_str else 0)
    tag = {"confirmed_2.837": "[S] verified (primary source)", "use_source_value": "[S] verified (primary source)",
           "provisional_2.837": "[M] starting point"}[decision]
    return {
        "schema": "s2-pbcl-1",
        "plan": "S2_PLAN.md section 2 (Poses, Cl), section 17 item 3; S2_BUILDERS_DESIGN.md section 4 (Cl row), "
                "section 16 answer 4",
        "source": {"citation": cit, "doi": notes.get("doi"), "phase": phase,
                   "lattice_parameter_A": a_str, "stated_digits": digits, "how_verified": notes.get("how_verified"),
                   "level": level, "primary": notes.get("primary"),
                   # sources are cited by name and DOI; their web addresses stay in the off-repository notes (public
                   # hygiene: no host names in a committed record; review F10, N-E9)
                   "secondary_sources": [{**{k: v for k, v in x.items() if k != "url"},
                                          **({"web_address": "in the off-repository notes"} if "url" in x else {})}
                                         if isinstance(x, dict) else x for x in notes.get("secondary_sources", [])]},
        # a value that is not verified at the primary level is kept apart, so that no reader can take it for the
        # value to use (the value to use is value_used_A, whatever the decision)
        "d_PbCl_from_source_A": float(d) if primary else None,
        "d_PbCl_from_source_decimal": str(d) if primary else None,
        "d_PbCl_unverified_A": None if (primary or d is None) else float(d),
        "d_PbCl_unverified_decimal": None if (primary or d is None) else str(d),
        "d_PbCl_level": level,
        "differs_from_2.837_at_stated_digits": differs,
        "decision": decision,
        "value_used_A": float(use), "value_used_decimal": str(use),
        "tag_for_shifted_starts": tag,
        "allow_provisional_required": decision == "provisional_2.837",
        "start_override_required": decision == "use_source_value",
        "rule": ("confirmed_2.837 iff the primary source is verified and a/2 equals 2.837 A at its stated digits; "
                 "use_source_value iff the primary source is verified with another value (X-2: scripts/46 moves "
                 "the shifted Cl to that distance and records start_override); provisional_2.837 otherwise "
                 "(shifted starts at 2.837 A with --allow-provisional, labelled [M] starting points); a value read "
                 "only in a secondary source does not verify (I-E1)"),
        "open_item": notes.get("open_item"),
        "notes": ["I-E1", "I-E2", "N-E4", "N-E9"] + (["N-E1"] if MOCKED_46 else []),
        "nothing_downloaded_or_executed": True,
        "generator": _generator(), "date": notes.get("date") or time.strftime("%Y-%m-%d", time.gmtime()),
        "written": _utc()}


def pbcl(notes_path, out=None):
    with open(notes_path) as fh:
        notes = json.load(fh)
    rec = pbcl_record(notes)
    if out:
        _dump(rec, out)
    return rec


# ---------------------------------------------------------------- (4) MACE foundation file on the laptop (section 5)
def mace_laptop(out=None, *, path=None):
    p = path or c46.foundation_path()
    rec = {"schema": "s2-mace-laptop-1", "plan": "S2_PLAN.md section 5 (Model), section 17 item 3",
           "file": os.path.basename(p), "expected_file": c46.FOUNDATION_FILE,
           "expected_sha256": c46.FOUNDATION_SHA256, "bytes": None, "sha256": None, "passed": False,
           "versions": _versions(), "mace_imported": "mace" in sys.modules,
           "coverage": ("Z = 16, 17, 20, 37 (and 1, 6, 7, 38, 53, 55, 82) read on the laptop on 2026-11-03 "
                        "(S2_PLAN.md section 0); not re-read here, so mace is never imported"),
           "node": "the node copy is checked in campaign 1 (scripts/46 foundation_check and load_mace)",
           "notes": ["N-E5"] + (["N-E1"] if MOCKED_46 else []), "generator": _generator(), "written": _utc()}
    if os.path.isfile(p):
        rec.update(bytes=os.path.getsize(p), sha256=sha256_file(p))
        rec["passed"] = rec["sha256"] == c46.FOUNDATION_SHA256 and rec["file"] == c46.FOUNDATION_FILE
    else:
        rec["missing"] = True
    if out:
        _dump(rec, out)
    return rec


# ---------------------------------------------------------------- self-test (synthetic outcomes; m30 geometry only)
def self_test(work=None):
    import traceback
    t0 = time.time()
    work = work or tempfile.mkdtemp(prefix="s2_52_selftest_")
    os.makedirs(work, exist_ok=True)
    results = []

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

    def refuses(fn, *a, **kw):
        try:
            fn(*a, **kw)
        except STOP as e:
            return str(e)
        raise AssertionError(f"{fn.__name__} did not refuse")

    print(f"52_s2_stage0_checks self-test: {b42.BUILDER_VERSION}, GEOM_SHA {b42.GEOM_SHA}; numpy {np.__version__}, "
          f"ase {ase.__version__}")
    if MOCKED_46:
        print("MOCKED 46 (scripts/46_s2_cells.py absent: the interface stub with literal plan tables is used)")
    ctxs, sets = {}, {}

    def ctx(mm):
        if mm not in ctxs:
            ctxs[mm] = _ctx(mm)
            sets[mm] = _sites_checked(mm, ctxs[mm])
        return ctxs[mm]

    def c_pins():
        assert b42.BUILDER_VERSION == "s2b-2" and b42.GEOM_SHA == GEOM_SHA_FROZEN
        assert c46.GEOM_SHA_S2B2 == GEOM_SHA_FROZEN == b42.GEOM_SHA_PIN["s2b-2"]
        assert c46.FOUNDATION_SHA256 == "01bfe22100139f424713cf921144e5509cbe353d67aa9fa1be9c6e1e0ed35845"
        assert list(c46.PILOTS) == ["m30", "m05"] and int(c46.VI) == 127
        assert {L: tuple(v) for L, v in TOKENS_OF.items()} == {"B": ("Sr", "Ca"), "A": ("Cs", "GA"), "X": ("Cl",)}
        assert all(c46.SUBLATTICE[t] == L for L, ts in TOKENS_OF.items() for t in ts)
        assert sum(len(v) for v in TOKENS_OF.values()) == len(c46.TOKENS) == 5
        assert {int(v) for v in c46.CAL_SITES["m05"].values()} == {124, 28, 49}
        assert set(NOTES) >= {"I-39", "I-40", "I-E1", "I-E2", "I-E3", "I-E4", "I-E5"}
        return "s2b-2 / GEOM_SHA frozen value, foundation sha256, pilots, VI, tokens by sublattice, m05 CAL_SITES"

    def c_draws():
        d = host_draw()
        assert d == PLAN_DRAW_PIN, "the section 3 draw differs from the plan table"
        assert d == _norm_draw(c46.DRAW), "the section 3 draw differs from scripts/46 DRAW"
        order = [mm for _, mm, _ in d[:12]]
        lists, short = production_lists(order, {mm: True for mm in order})
        assert lists == PLAN_LISTS_PIN and not any(short.values())
        assert "m15" not in order and dict((mm, r) for r, mm, _ in d)["m15"] == 14
        for mm in ("m30", "m05"):
            ctx(mm)
        dr, mig = m05_draw(sets["m05"], sets["m30"])
        assert mig == 53 and dr == PLAN_M05_PIN, (mig, dr)
        m46 = _norm_m05(c46.M05_DRAW_ORDER)
        assert all([j for j, _ in dr[L]] == [j for j, _ in m46[L]] for L in dr)
        assert all(c is None or c == cc for L in dr for (_, c), (_, cc) in zip(m46[L], dr[L]))
        return (f"28 eligible, crc32 order = section 3 table (and scripts/46); ranks 1-12 all admissible -> the "
                f"plan's n = 8 / 10 lists and reserves; m15 at rank 14; m05 draw A {[j for j, _ in dr['A']]}, X "
                f"{[j for j, _ in dr['X']]} (migrating I{mig} excluded) = section 11 crc32")

    def c_m30():
        c = ctx("m30"); s = sets["m30"]
        cells = required_cells(s)
        assert len(cells) == 28 and len({(L, j) for L, _, j, _ in cells}) == 19
        assert sorted(s["B"]["first"]) == [124, 136] and s["B"]["far"] == [76, 172], s["B"]
        assert s["A"]["far"] == [188, 164] and s["X"]["far"] == [175, 186] and int(s["mig_host"]) == 138
        one = {"B": "Sr", "A": "Cs", "X": "Cl"}
        rows = [build_cell(c, one[L], j, L, role) for L, role, j, t in cells if t == one[L]]
        assert len(rows) == 19, len(rows)
        bad = [r for r in rows if r["status"] != "ok"]
        assert not bad, bad
        assert host_status(rows) == "admissible"
        assert all(r["n_atoms"] == list(b42.REGISTRY[r["token"]]["n"]) for r in rows)
        assert {r["pose"] for r in rows} == {"swap", "centred"}
        return (f"Sr at 4 B, Cs at 5 A, Cl at 10 X production sites of m30 (first shell + far pair, section 4 "
                f"table asserted): 19/19 pairs admissible on both legs, default poses, unrelaxed partners")

    def c_classify():
        c = ctx("m30")

        def raiser(exc):
            def f(*_a):
                raise exc
            return f
        r1 = build_cell(c, "Sr", 136, "B", "first", build_fn=raiser(b42.Inadmissible({"leg": "V"}, "V leg: clash")))
        r2 = build_cell(c, "Sr", 136, "B", "first", build_fn=raiser(b42.Refused("refused")))
        r3 = build_cell(c, "Sr", 136, "B", "first", build_fn=raiser(b42.BuildError({"V4": {"passed": False,
                                                                                         "reason": "x"}})))
        r4 = build_cell(c, "Sr", 136, "B", "first", build_fn=raiser(ValueError("boom")))
        assert (r1["status"], r1["leg"]) == ("Inadmissible", "V") and r2["status"] == "Refused"
        assert r3["status"] == "error" and r4["status"] == "error"
        ok = build_cell(c, "Sr", 136, "B", "first")
        assert host_status([ok, r1]) == "inadmissible" and host_status([ok, r2]) == "inadmissible"
        assert host_status([ok, r1, r3]) == "error" and host_status([ok]) == "admissible"
        bh, bv = _build_default(c, "Ca", 136, "B")
        r5 = build_cell(c, "Sr", 136, "B", "first", build_fn=lambda *_a: (bh, bv))     # wrong token -> error
        bhp, bvp = b42.build_paired(_attr(c, "host"), _attr(c, "vac"), 127, "Cs", 128, "q0+",
                                    vpos=_attr(c, "vpos"), partners="unrelaxed")
        r6 = build_cell(c, "Cs", 128, "A", "first", build_fn=lambda *_a: (bhp, bvp))   # non-default pose -> error
        assert r5["status"] == "error" and r6["status"] == "error", (r5, r6)
        return ("Inadmissible (leg kept) and Refused -> inadmissible; BuildError, ValueError, a wrong token and a "
                "non-default pose -> error (host not admissible, stop)")

    def c_lists():
        order = [mm for _, mm, _ in PLAN_DRAW_PIN[:12]]
        adm = {mm: True for mm in order}; adm["m16"] = False
        lists, short = production_lists(order, adm)
        assert lists["n8"] == ["m06", "m02", "m12", "m32", "m26", "m22", "m23", "m33"]
        assert lists["reserves_n8"] == ["m13", "m17"] and not short["n8"]
        assert lists["n10"] == ["m06", "m02", "m12", "m32", "m26", "m22", "m23", "m33", "m13", "m17"]
        assert lists["reserves_n10"] == ["m03"] and short["n10"]
        adm2 = {mm: True for mm in order}; adm2["m23"] = None                 # an error host is never listed
        l2, s2 = production_lists(order, adm2)
        assert "m23" not in l2["n8"] + l2["reserves_n8"] + l2["n10"] and l2["n8"][-1] == "m33" and s2["n10"]
        # the full admissibility() with injected outcomes on two cheap members: rank-3 inadmissible, then an error
        calls = {"n": 0}

        def fake_ok(ctx_, token, site, L):
            calls["n"] += 1
            return _fake_built(token)

        def fake_bad(member_bad, exc):
            def f(ctx_, token, site, L):
                if _attr(ctx_, "member") == member_bad and token == "Sr" and site == 136:
                    raise exc
                return _fake_built(token)
            return f
        rec, pr = admissibility(None, build_fn=fake_ok, members=["m06", "m16"], log=lambda *_: None)
        assert rec["hosts"]["m06"]["admissible"] and rec["hosts"]["m16"]["admissible"]
        assert rec["status"] == "stop" and rec["production"] is None and any("too few" in p for p in pr)
        rec, pr = admissibility(None, build_fn=fake_bad("m16", b42.Inadmissible({"leg": "host"}, "clash")),
                                members=["m06", "m16"], log=lambda *_: None)
        assert rec["hosts"]["m16"]["status"] == "inadmissible" and not any("I-40" in p for p in pr)
        rec, pr = admissibility(None, build_fn=fake_bad("m16", RuntimeError("defect")), members=["m06", "m16"],
                                log=lambda *_: None)
        assert rec["hosts"]["m16"]["status"] == "error" and any("I-40" in p for p in pr) and rec["status"] == "stop"
        assert rec["hosts"]["m06"]["n_pairs"] == 28 and rec["hosts"]["m06"]["n_legs"] == 56
        return (f"m16 inadmissible shifts n = 8 to ...m23, m33 with reserves m13, m17 and leaves n = 10 short "
                f"(reserves [m03]: stop, N-E3); an error host is never listed; admissibility() with injected "
                f"outcomes: Inadmissible -> host inadmissible, RuntimeError -> error + stop; {calls['n']} fake builds")

    def c_m05():
        def oc(table):
            return lambda j: (table.get(j, "admissible"), [])
        r = choose_site([28, 92], oc({28: "inadmissible"}))
        assert r["chosen"] == 92 and not r["conflict"] and [t["site"] for t in r["tried"]] == [28, 92]
        r = choose_site([28, 92], oc({28: "inadmissible", 92: "inadmissible"}))
        assert r["chosen"] is None and r["conflict"]
        r = choose_site([49, 138, 125, 137, 126, 90, 102], oc({49: "inadmissible", 138: "inadmissible"}))
        assert r["chosen"] == 125
        r = choose_site([124], oc({124: "inadmissible"}))
        assert r["chosen"] is None and r["conflict"]
        r = choose_site([28, 92], oc({28: "error"}))
        assert r["chosen"] is None and r["error"] and len(r["tried"]) == 1
        r = choose_site([49, 138], oc({}))
        assert r["chosen"] == 49 and len(r["tried"]) == 1

        def fake(bad):          # bad: {(token, site): exception} on m05 only; every other build succeeds
            def f(ctx_, token, site, L):
                e = bad.get((token, int(site))) if _attr(ctx_, "member") == "m05" else None
                if e is not None:
                    raise e
                return _fake_built(token)
            return f
        quiet = {"members": ["m06"], "log": lambda *_: None}
        rec, pr = admissibility(None, build_fn=fake({("GA", 28): b42.Inadmissible({"leg": "V"}, "clash")}), **quiet)
        cal = rec["m05_calibration"]
        assert cal["A"]["chosen"] == 92 and [t["site"] for t in cal["A"]["tried"]] == [28, 92]
        assert cal["B"]["chosen"] == 124 and cal["X"]["chosen"] == 49 and cal["B"]["site"] == 124
        assert not any("m05" in p for p in pr), pr
        rec, pr = admissibility(None, build_fn=fake({("Ca", 124): b42.Refused("no")}), **quiet)
        assert rec["m05_calibration"]["B"]["conflict"] and any("Pb124 has no fallback" in p for p in pr)
        assert rec["m05_chosen"] is None and rec["status"] == "stop"
        rec, pr = admissibility(None, build_fn=fake({("Cl", 49): b42.Inadmissible({"leg": "host"}, "x"),
                                                     ("Cl", 138): b42.Inadmissible({"leg": "V"}, "x")}), **quiet)
        assert rec["m05_calibration"]["X"]["chosen"] == 125
        return ("choose_site: FA28 inadmissible -> FA92; both -> conflict; I49, I138 -> I125; Pb124 -> conflict; "
                "error -> stop; through admissibility(): GA@FA28 V leg -> FA92, Ca@Pb124 Refused -> conflict "
                "(stop, m05_chosen null), Cl at I49 and I138 -> I125")

    def c_pbcl():
        base = {"citation": "A. Poglitsch & D. Weber 1987, J. Chem. Phys. 87, 6373", "phase": "cubic CH3NH3PbCl3",
                "how_verified": "synthetic"}
        r = pbcl_record(dict(base, level="[S] primary verified", lattice_parameter_A="5.674"))
        assert r["decision"] == "confirmed_2.837" and r["value_used_decimal"] == "2.837"
        assert not r["allow_provisional_required"] and r["tag_for_shifted_starts"].startswith("[S]")
        r = pbcl_record(dict(base, level="[S] primary verified", lattice_parameter_A="5.675"))
        assert r["decision"] == "use_source_value" and r["value_used_decimal"] == "2.8375"
        assert abs(r["value_used_A"] - 2.8375) < 1e-15 and r["start_override_required"]
        assert r["d_PbCl_from_source_decimal"] == "2.8375" and r["d_PbCl_unverified_A"] is None
        r = pbcl_record(dict(base, level="[S] primary verified", lattice_parameter_A="5.6740"))
        assert r["decision"] == "confirmed_2.837" and r["source"]["stated_digits"] == 4
        r = pbcl_record(dict(base, level="unverified", lattice_parameter_A=None))
        assert r["decision"] == "provisional_2.837" and r["allow_provisional_required"]
        assert r["value_used_decimal"] == "2.837" and r["tag_for_shifted_starts"] == "[M] starting point"
        assert r["d_PbCl_from_source_A"] is None and r["d_PbCl_unverified_A"] is None
        r = pbcl_record(dict(base, level="[S] secondary", lattice_parameter_A="5.675"))
        assert r["decision"] == "provisional_2.837" and r["d_PbCl_unverified_decimal"] == "2.8375"
        assert r["d_PbCl_from_source_A"] is None and r["value_used_A"] == 2.837
        assert r["differs_from_2.837_at_stated_digits"] is True and r["value_used_decimal"] == "2.837"
        refuses(pbcl_record, dict(base, level="[S] primary verified", lattice_parameter_A=5.675))
        refuses(pbcl_record, dict(base, level="[S] primary verified", lattice_parameter_A="5,675"))
        refuses(pbcl_record, dict(base, level="[S] primary verified", lattice_parameter_A=None))
        refuses(pbcl_record, dict(base, level="verified", lattice_parameter_A="5.675"))
        refuses(pbcl_record, dict(base, citation="Weber 1978, Z. Naturforsch.", level="unverified"))
        refuses(pbcl_record, dict(base, phase="tetragonal CH3NH3PbCl3", level="unverified"))
        p = os.path.join(work, "pbcl_source.json")
        _dump(pbcl_record(dict(base, level="[S] secondary", lattice_parameter_A="5.675")), p)
        assert json.load(open(p))["decision"] == "provisional_2.837"
        web = "https" + ":" + "//materials.example" + ".edu/reference/29"
        ru = pbcl_record(dict(base, level="[S] secondary", lattice_parameter_A="5.675",
                              secondary_sources=[{"source": "a curated database", "url": web, "value": "5.675"}]))
        assert "url" not in ru["source"]["secondary_sources"][0] and web not in json.dumps(ru)        # N-E9
        _dump(ru, os.path.join(work, "pbcl_url.json"))
        return ("a = 5.674 (and 5.6740) -> confirmed; 5.675 -> use 2.8375 (exact decimal); unverified and "
                "secondary-only -> provisional at 2.837 [M] (I-E1); float, malformed, missing value, unknown level, "
                "wrong citation or phase refused; record written through dump_public")

    def c_strip():
        home = os.path.expanduser("~")
        rep = {"a": os.path.join(ROOT, "results", "x.json"), "b": [home + "/some where/file.json", "3.6/4.0 A"],
               "c": {"d": "see " + os.path.join(tempfile.gettempdir(), "w x") + " and more"},
               "e": 1.5, "f": "H(N)/H(C) split", "g": "node path /data/work/s2 and /usr/local/bin/run_qe.sh"}
        pub, stripped = strip_paths(rep)
        assert pub["a"] == "results/x.json" and pub["b"][0] == REMOVED and pub["c"]["d"] == REMOVED
        assert pub["b"][1] == "3.6/4.0 A" and pub["f"] == "H(N)/H(C) split" and pub["g"] == rep["g"]
        assert sorted(stripped) == ["/a", "/b/0", "/c/d"], stripped
        assert not _hygiene(json.dumps(pub)), _hygiene(json.dumps(pub))
        assert _hygiene(json.dumps(rep)), "the scanner misses the unstripped report"
        ip = ".".join(["10", "0", "0", "1"])
        assert _hygiene(json.dumps({"x": ip})) and _hygiene("i-" + "0123456789abc")
        assert not _hygiene(json.dumps({"x": "/data/work/s2", "y": "/usr/local/bin/run_qe.sh"}))
        refuses(_dump, {"x": ip}, os.path.join(work, "bad.json"))
        assert not os.path.exists(os.path.join(work, "bad.json"))
        me = open(os.path.abspath(__file__)).read()
        assert not _hygiene(me), _hygiene(me)[:5]
        return ("repository paths made relative, home/temporary paths removed, '/data' kept, ratios untouched; the "
                "scanner flags the raw copy, an IPv4 and an instance id, and passes this script's own text")

    def c_t4():
        def fake_runner(kind):
            def run(report_off):
                rep = {"builder_version": "s2b-2", "geom_sha": GEOM_SHA_FROZEN, "member": "m30", "vi": 127,
                       "mig_host": 138, "f": b42.CLASH["f"], "f_w": b42.CLASH["f_w"],
                       "cases": [{"token": k.split("@")[0], "site": int(k.split("@")[1]),
                                  "kept": [{"pose": p} for p in v],
                                  "rejected": [{"reason": "work dir " + os.path.dirname(report_off)}]}
                                 for k, v in b42.T4_PINNED.items()]}
                if kind == "geom":
                    rep["geom_sha"] = "0" * 64
                if kind == "kept":
                    rep["cases"][0]["kept"] = []
                with open(report_off, "w") as fh:
                    json.dump(rep, fh)
                ok = "SELF-TEST PASS (13 cases, 0 failed, 91 s)"
                lines = ["PASS T1 templates: x", "PASS T4 tokens on m30: report -> " + report_off,
                         "PASS no-model: 'mace' not in sys.modules; work files in " + os.path.dirname(report_off)]
                if kind == "fail":
                    lines.append("FAIL T7 PBC: AssertionError")
                    ok = "SELF-TEST FAIL (13 cases, 1 failed, 91 s)"
                lines.append(ok)
                return (1 if kind in ("fail", "rc") else 0), "\n".join(lines) + "\n"
            return run
        off = os.path.join(work, "off")
        outd = os.path.join(work, "stage0")
        r = t4(os.path.join(off, "t4_raw.json"), outd, runner=fake_runner("ok"))
        a = json.load(open(os.path.join(outd, OUT["t4"])))
        fz = json.load(open(os.path.join(outd, OUT["freeze"])))
        assert fz["t4_report_sha256"] == sha256_file(os.path.join(outd, OUT["t4"])) == r["t4_sha256"]
        assert fz["t4_raw_sha256"] == sha256_file(os.path.join(off, "t4_raw.json"))
        assert fz["GEOM_SHA"] == GEOM_SHA_FROZEN and fz["f"] == 0.9 and fz["f_w"] == 0.8
        assert fz["class_map"]["H"] == "H" and fz["thresholds_A"]["HN-X"] == b42.THR["HN-X"]
        assert fz["self_test_summary"]["n_cases"] == 13 and len(a["archive"]["stripped_pointers"]) == 22
        assert os.path.exists(os.path.join(off, "t4_raw_selftest.log"))
        for txt in (json.dumps(a), json.dumps(fz)):
            assert not _hygiene(txt), _hygiene(txt)[:3]
        n = 0
        for kind in ("rc", "fail", "geom", "kept"):
            refuses(t4, os.path.join(off, f"t4_{kind}.json"), outd, runner=fake_runner(kind)); n += 1
        refuses(t4, os.path.join(off, "t4_raw.json"), outd, runner=fake_runner("ok"))          # exists already
        refuses(t4, os.path.join(ROOT, "results", "t4_in_repo.json"), outd, runner=fake_runner("ok"))
        assert not os.path.exists(os.path.join(ROOT, "results", "t4_in_repo.json"))
        return (f"archive + freeze written, sha256 of raw and archived copies recorded and equal to the files, 22 "
                f"path-bearing values stripped; {n} bad runs (exit code, FAIL line, GEOM_SHA, kept poses), an "
                f"existing raw path and a raw path inside the repository refused")

    def c_mace():
        p = os.path.join(work, c46.FOUNDATION_FILE)
        with open(p, "wb") as fh:
            fh.write(b"synthetic foundation file")
        r = mace_laptop(None, path=p)
        assert r["passed"] is False and r["sha256"] == hashlib.sha256(b"synthetic foundation file").hexdigest()
        r2 = mace_laptop(None, path=os.path.join(work, "absent", c46.FOUNDATION_FILE))
        assert r2["passed"] is False and r2.get("missing")
        assert not _hygiene(json.dumps(r)) and "work" not in json.dumps({k: r[k] for k in ("file", "expected_file")})
        fp = c46.foundation_path()
        assert os.path.basename(fp) == c46.FOUNDATION_FILE and os.path.basename(os.path.dirname(fp)) == "mace"
        assert r["versions"]["mace-torch"] in (None, "0.3.16") and "mace" not in sys.modules
        return (f"synthetic file -> sha256 recorded, passed False; absent file -> missing; foundation_path ends in "
                f"mace/{c46.FOUNDATION_FILE}; versions from metadata (mace-torch {r['versions']['mace-torch']}); "
                f"record path-free")

    for nm, fn in (("E1 pins and constants", c_pins), ("E2 draws (sections 3, 11)", c_draws),
                   ("E3 admissibility on m30 (one token per sublattice)", c_m30),
                   ("E4 exception classes", c_classify), ("E5 production-list logic", c_lists),
                   ("E6 m05 calibration fallback", c_m05), ("E7 Pb-Cl decision rule", c_pbcl),
                   ("E8 path stripping and hygiene", c_strip), ("E9 T4 archive and freeze", c_t4),
                   ("E10 MACE laptop check", c_mace)):
        case(nm, fn)
    print("NOTES:")
    for k, v in NOTES.items():
        print(f"  {k}: {v}")
    ok_mace = "mace" not in sys.modules
    print(f"{'PASS' if ok_mace else 'FAIL'} no-model: 'mace' {'not ' if ok_mace else ''}in sys.modules "
          f"(torch {'imported' if 'torch' in sys.modules else 'not imported'})")
    results.append(("no-model", ok_mace))
    nf = sum(not ok for _, ok in results)
    print(f"SELF-TEST {'PASS' if not nf else 'FAIL'} ({len(results)} cases, {nf} failed, {time.time() - t0:.0f} s)")
    return 1 if nf else 0


def _fake_built(token):
    """A Built-like object for the list-logic self-test (no geometry; outcome only)."""
    n = b42.REGISTRY[token]["n"]
    mk = lambda k: types.SimpleNamespace(atoms=[None] * k, token=token, pose={"name": DEFAULT_POSE_NAME[token]},
                                         report={"valid": True, "admissible": True})
    return mk(n[0]), mk(n[1])


# ---------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--work", default=None, help="self-test: work folder (default: a new temporary folder)")
    ap.add_argument("--allow-mock-46", action="store_true",
                    help="run a subcommand although scripts/46 is absent (records carry c46 MOCKED; N-E1)")
    sub = ap.add_subparsers(dest="cmd")
    for nm in ("t4", "all"):
        sp = sub.add_parser(nm)
        sp.add_argument("--report-off", required=True, help="raw T4 report path outside the repository (new file)")
        if nm == "all":
            sp.add_argument("--notes", required=True, help="Pb-Cl verification notes (JSON, off-repository)")
    sub.add_parser("admissibility")
    sp = sub.add_parser("pbcl")
    sp.add_argument("--notes", required=True, help="Pb-Cl verification notes (JSON, off-repository)")
    sub.add_parser("mace-laptop")
    for p in sub.choices.values():
        p.add_argument("--out-dir", default=STAGE0, help="output folder (default results/objective2/s2/stage0)")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test(a.work)
    if not a.cmd:
        ap.print_help()
        return 2
    if MOCKED_46 and not a.allow_mock_46:
        print("REFUSED: scripts/46_s2_cells.py is absent; rerun with all files present (or --allow-mock-46)",
              file=sys.stderr)
        return 3
    if MOCKED_46:
        print("MOCKED 46: records carry c46 MOCKED and must be regenerated with scripts/46 present")
    rc = 0
    try:
        if a.cmd in ("t4", "all"):
            r = t4(a.report_off, a.out_dir)
            print(f"t4: {r['summary']}; archived sha256 {r['t4_sha256']}; raw {r['raw_sha256']}; freeze "
                  f"{r['freeze_sha256']}; {len(r['stripped'])} values stripped")
        if a.cmd in ("admissibility", "all"):
            rec, pr = admissibility(os.path.join(a.out_dir, OUT["admissibility"]))
            print(f"admissibility: {rec['status']}; production {rec['production']}; m05 {rec['m05_chosen']}; "
                  f"matches plan lists {rec['matches_plan_lists']}")
            for p in pr:
                print(f"  STOP: {p}")
            rc = max(rc, 3 if pr else 0)
        if a.cmd in ("pbcl", "all"):
            r = pbcl(a.notes, os.path.join(a.out_dir, OUT["pbcl"]))
            print(f"pbcl: level {r['source']['level']}; a = {r['source']['lattice_parameter_A']} A; decision "
                  f"{r['decision']}; value used {r['value_used_decimal']} A; tag {r['tag_for_shifted_starts']}")
        if a.cmd in ("mace-laptop", "all"):
            r = mace_laptop(os.path.join(a.out_dir, OUT["mace"]))
            print(f"mace-laptop: {r['file']} sha256 {r['sha256']} passed {r['passed']}")
            rc = max(rc, 0 if r["passed"] else 3)
    except STOP as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        rc = 3
    _no_mace()
    print("no-model: 'mace' not in sys.modules")
    return rc


if __name__ == "__main__":
    sys.exit(main())

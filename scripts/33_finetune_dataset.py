#!/usr/bin/env python
"""Build the MACE fine-tuning dataset from the DFT single points (PLAN WP3), split by HOST:
amendment 2026-10-28m items 1a-1e and the loss-weight record of item 2.

Every QE output (scripts/30, plain PBE, R point) is paired with the exact frame it was run on and
written to extxyz with info REF_energy (target, eV), REF_energy_raw (free energy F), REF_EF (E_F, eV),
label, host, system, image, config_type, split, mTS_eV, band_term_eV, c_D_eV, and arrays REF_forces
(eV/A). band_term_eV keeps its old name but is now F - REF_energy (the E' shift plus c_D of m 1c), not
the fitted class term of amendment h. Frames are split by host configuration, never by frame (images
of one band share almost all coordinates); a host not in --test-hosts or --valid-hosts is train.

Inclusion (m 1b). An output below --dft enters only if its label fully matches one of
    band  mNN_<undoped|GA|Sr>_img<k>                     frame band_<system>_mNN.extxyz @ k
    WP2c  mNN_host, mNN_vac, mNN_<Sr|GA><j>_<novac|vac>  frame <label>_relaxed.extxyz (v2prod)
    WP3   mNN_<undoped|GA|Sr|pristine>_<rat05f|rat10f|md300|md450>  frame <label>.extxyz (scripts/35)
and it has JOB DONE, a converged SCF and a force block. Skipped pattern outputs are listed with the
reason (gave up, no JOB DONE, SCF not converged, no force block). Any other label must be one of the
28 exclusions of m 1b or chk_*, else the script stops.

Archive and counts (m 1d, 1e). WP3 outputs sit in <dft>/wp3/raw/<label>.{in,out}.gz, the 50 item-1'
outputs (m 1') in <dft>/wp3/test_extra/raw/; queue markers <label>.gaveup (also read gzipped) and
<label>.out.tryN(.gz) are copied beside them and match no output glob. frames_report.json (scripts/35)
is read from the --frames dir that holds it; its records must be exactly the 96 labels of
scripts/35 --hosts 05 06 08 12 15 20 at md_steps 1500 and fmax_bound 15 (m 1d). The script stops if an
ok record has neither wp3/raw/<label>.out.gz nor wp3/raw/<label>.gaveup, if a WP3 output has no ok
record, if a pattern label has a .out.tryN but neither a final output nor a .gaveup (retry pending),
or unless it finds exactly: train 90 band + 16 binding (m05) + W WP3 (training hosts), valid 15 + 16
(m21), test 30 band (m30, m32) + 16 binding (m30) + the item-1' frames found (missing ones listed by
expected label), and no rattle or md frame outside train. W = ok records - dropped frames; no dataset
is written unless W >= 60 (m 1d).

Targets (m 1c). E_F is the last "the Fermi energy is" value (scripts/37 qe()). On the E' basis every
vacancy cell (59 I) gets REF_energy = F - (E_F - 3.3447 eV); on the raw basis F. c_D is then
subtracted from every Sr+V and GA+V frame (E': c_Sr -2.174, c_GA -18.851 meV; raw +55.826,
-2.451 meV). The basis follows only the q = +1 check (outputs chk_<frame label>_q1 anywhere below
--dft), with v = F(q=0) - E_F(q=0) - F(q=+1):
    (a) |[v(m15 Sr img3) - v(m15 Sr img0)] - [v(m15 undoped img3) - v(m15 undoped img0)]| < 10 meV
    (b) |v(m05 X md450) - v(m05 X img0)| < 10 meV, X = Sr and undoped (md300 if md450 was rejected)
One chk_* file starts the check. Each of its 16 jobs (8 chk_*, their 8 q = 0 frames) must then be final
under the queue protocol of m 1d, a JOB DONE output or a .gaveup marker, else the script stops (archive
incomplete; no basis is decided). A job abandoned under m 1d (.gaveup) or an unconverged SCF fails the
test it enters. If md450 and md300 of m05 X were both rejected, (b) fails for that X (script rule; m 1c
names only the md300 replacement). (a) passes: E'; the WP3 vacancy frames E' if (b) passes for both X,
else config_energy_weight = 0 (forces kept). (a) fails: raw basis throughout. There is no option that
picks a basis. Without any chk_* file the script stops; --no-chk-yet (testing only) then writes
dataset_meta.json with basis UNDECIDED and no dataset (and accepts an empty frames_report.json).

E0s (m 1c; amendment g item 6). Least squares of REF_energy - E(MACE-MP-0) over the 106 training
band_* and binding frames against (const, dI, dN, nSr), assigned to I, N, Pb and Sr (C, H, Cs 0).
Exact within the FA19Cs1Pb20I60(-I)(+GA)(+Sr) family, meaningless outside it. WP3 frames are trained
on but not fitted. E0s.json = foundation E0s + offsets, flat {Z: eV}.

Loss weights (m 2). L_F = zero-shot force MSE per component over all atoms of all n_train frames;
L_E = (1/n_train) sum_i e_i ((E_ref,i - E_i)/N_i)^2 with E0s.json, e_i = config_energy_weight;
w_E = 100 L_F / L_E to two significant figures. Written to dataset_meta.json with n_train, n_E,
mean N, the check record, the m21 start-check values and the m 1c diagnostics (training frames;
test frames are not evaluated with MACE here, and no item-1' value is analysed, m item 7). Residuals
are REF_energy - E(zero-shot, E0s.json); the m05 far-site errors are MACE - DFT (= -c_D).

Fail-closed rules of this script that amendment m does not state (none can select a basis) are listed
in SCRIPT_RULES and in dataset_meta.json: the check completeness above, the both-rejected rule, the
pending-retry stop, the 96-record report, charge neutrality of every dataset output (electron count =
sum of pseudopotential valences, so a 59-I cell is odd), the chk electron count (q = 0 minus 1) and
geometry (printed cell and positions of the two outputs, and the inputs where archived), frame = its
QE input <label>.in(.gz) within 1e-6 A, WP3 config_type = label kind, the wp3/raw and
wp3/test_extra/raw locations, and no dataset when W < 60.

    python scripts/33_finetune_dataset.py --dft results/objective2/dopant_shell \
        --frames ../bands <x>/v2prod results/objective2/dopant_shell/wp3/frames \
        --out results/objective2/dopant_shell/wp3/dataset \
        --test-hosts m30 m32 m04 m10 m14 m18 m27 --valid-hosts m21
"""
import argparse, glob, json, os, re
from collections import Counter, defaultdict
import importlib.util
import numpy as np
from ase.io import read, write

HERE = os.path.dirname(os.path.abspath(__file__))
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
a32 = _load("a32", "32_dft_validation_analysis.py")
a37 = _load("a37", "37_dft_eb_analysis.py")
Z = {"H": 1, "C": 6, "N": 7, "Sr": 38, "I": 53, "Cs": 55, "Pb": 82}
TRAIN_HOSTS = ("m05", "m06", "m08", "m12", "m15", "m20")          # amendment e item 1; m 1a
PATTERNS = {"band": re.compile(r"(m\d\d)_(undoped|GA|Sr)_img(\d)"),  # m 1b, matched in full
            "binding": re.compile(r"(m\d\d)_(host|vac|(?:Sr|GA)\d+_(?:novac|vac))"),
            "wp3": re.compile(r"(m\d\d)_(undoped|GA|Sr|pristine)_(rat05f|rat10f|md300|md450)")}
WP3_TYPE = {"rat05f": "rattle", "rat10f": "rattle", "md300": "md", "md450": "md"}   # scripts/35 config_type
EXCLUDED = (  # the 28 non-pattern outputs of the 2026-10-28 archive (m 1b)
    [f"atom_{e}" for e in ("C", "Cs", "H", "I", "N", "Pb", "Sr")] +
    [f"kconv_m30u_img{i}_{k}" for i in (0, 3) for k in ("R", "gamma", "mp222")] +
    ["set_m30u_img0_dg0025", "set_m30u_img0_nspin2", "set_m30u_img3_dg0025"] +
    [f"m30_{x}_q1" for x in ("GA128_vac", "GA152_vac", "Sr136_vac", "Sr64_vac", "Sr_img0", "Sr_img3",
                             "undoped_img0", "undoped_img3", "vac")] +
    ["part_m30_GA_img0_far_only", "part_m30_GA_img0_near_only", "relax_m30_GA_img0"])
ITEM1P = {"m10": "GA", "m18": "GA", "m04": "Sr", "m14": "Sr", "m27": "Sr"}       # m 1'
ITEM1P_LABELS = [f"{h}_{s}_img{k}" for h, d in ITEM1P.items() for s in ("undoped", d) for k in (0, 2, 3, 4, 6)]
assert len(set(EXCLUDED)) == 28 and len(set(ITEM1P_LABELS)) == 50
EF_REF = 3.3447                                    # eV, median E_F of the 30 training undoped band frames
C_D = {"Eprime": {"Sr": -2.174e-3, "GA": -18.851e-3}, "raw": {"Sr": 55.826e-3, "GA": -2.451e-3}}  # eV
CHK_TOL, V_M30, A_M30 = 10.0, -51.25, -3.32        # meV: tolerance; m30 WP2d mean v and paired value (reported)
CHK_A = ("m15_Sr_img3", "m15_Sr_img0", "m15_undoped_img3", "m15_undoped_img0")
WP3_MIN = 60                                       # amendment c item 7; m 1d
WP3_LABELS = [f"{h}_{s}_{k}" for h in TRAIN_HOSTS for s in ("undoped", "GA", "Sr", "pristine") for k in WP3_TYPE]
WP3_PARAMS = {"md_steps": 1500, "fmax_bound": 15.0}  # scripts/35 --hosts 05 06 08 12 15 20 at its defaults (m 1d)
assert len(set(WP3_LABELS)) == 96
W_F = 100.0
START_CHECK = {"RMSE_F_meV_A": 79.819, "RMSE_E_per_atom_meV": {"Eprime": 0.333420, "raw": 0.349936}}  # m 2
SCRIPT_RULES = [  # fail-closed rules not stated in amendment m; none selects a basis (written to dataset_meta.json)
    "q = +1 check: once a chk_* file exists, each of its 16 jobs (8 chk_*, 8 q = 0 frames) with neither a JOB DONE "
    "output nor a .gaveup marker stops the script; only .gaveup and an unconverged SCF fail a test",
    "q = +1 check: md450 and md300 of m05 X both rejected by scripts/35 -> test (b) fails for that X",
    "a pattern label with a .out.tryN file but neither a final output nor a .gaveup marker (retry pending) stops the script",
    "frames_report.json must hold exactly the 96 labels of m 1d, made with md_steps 1500 and fmax_bound 15",
    "every dataset output is charge-neutral: electron count = sum of the pseudopotential valences over its frame",
    "a chk_* output has its q = 0 frame's electron count minus 1, the same printed cell and positions, and the "
    "same QE input geometry where both inputs are archived",
    "every frame equals its archived QE input <label>.in(.gz): species, cell, positions within 1e-6 A",
    "a WP3 frame's config_type matches its label kind; WP3 files sit at wp3/raw, item-1' files at wp3/test_extra/raw",
    "W < 60 (m 1d) or --no-chk-yet: only dataset_meta.json is written, into an --out without dataset files"]


def label_of(f):
    return os.path.basename(f).removesuffix(".gz")[:-4]


def qe_outputs(root):
    """pw.x outputs below root, plain or gzipped (the archive); a label present twice is an error."""
    fs = sorted(glob.glob(os.path.join(root, "**", "*.out"), recursive=True) +
                glob.glob(os.path.join(root, "**", "*.out.gz"), recursive=True))
    labs = [label_of(f) for f in fs]
    dup = sorted({l for l in labs if labs.count(l) > 1})
    assert not dup, f"labels found twice: {dup[:5]}"
    return fs


def gaveups(root):
    """Queue markers <label>.gaveup below root (qe_queue.sh: second failure, no <label>.out left), also
    read gzipped (<label>.gaveup.gz; m 1e copies the queue files 'gzipped where they are text')."""
    fs = sorted(glob.glob(os.path.join(root, "**", "*.gaveup"), recursive=True) +
                glob.glob(os.path.join(root, "**", "*.gaveup.gz"), recursive=True))
    labs = [os.path.basename(f).removesuffix(".gz").removesuffix(".gaveup") for f in fs]
    dup = sorted({l for l in labs if labs.count(l) > 1})
    assert not dup, f".gaveup markers found twice: {dup[:5]}"
    return dict(zip(labs, fs))


def retries(root):
    """Failed attempts <label>.out.tryN(.gz) kept by qe_queue.sh (listed only; never parsed)."""
    r = defaultdict(list)
    for f in sorted(glob.glob(os.path.join(root, "**", "*.out.try*"), recursive=True)):
        r[os.path.basename(f).split(".out.try")[0]].append(os.path.relpath(f, root))
    return dict(r)


def kind_of(label):
    for k, p in PATTERNS.items():
        m = p.fullmatch(label)
        if m:
            return k, m
    return None, None


def find(frames_dirs, name):
    hits = [os.path.join(d, name) for d in frames_dirs if os.path.exists(os.path.join(d, name))]
    assert len(hits) <= 1, f"{name} found in several frame dirs: {hits}"
    return hits[0] if hits else None


def status(path):
    """(parse_qe record + E_F, None) for a usable output, else (None, the m 1e skip reason)."""
    q = a32.parse_qe(path)
    if q is None:
        return None, "no JOB DONE"
    if not q["converged"]:
        return None, "SCF not converged"
    if q["forces"] is None:
        return None, "no force block"
    q["EF"] = a37.qe(path)["EF"]                   # last "the Fermi energy is" (scripts/37 qe())
    assert q["F_eV"] is not None and q["EF"] is not None and q["mTS_eV"] is not None, path
    return q, None


def qe_header(path):
    """Electron count, pseudopotential valences, celldm(1) (bohr), crystal axes and the printed positions
    (alat units) of a pw.x output; stops if any of them cannot be read."""
    t = a32.read_text(path)
    ne = re.search(r"number of electrons\s+=\s+([-\d.]+)", t)
    al = re.search(r"celldm\(1\)=\s*([-\d.]+)", t)
    nat = re.search(r"number of atoms/cell\s+=\s+(\d+)", t)
    sp = re.search(r"atomic species\s+valence\s+mass\s+pseudopotential\n(.*?)\n\s*\n", t, re.S)
    ax = re.findall(r"^\s+a\([123]\) = \(\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\)", t, re.M)[:3]
    i = t.find("positions (alat units)")
    tau = re.findall(r"^\s+\d+\s+(\S+)\s+tau\(\s*\d+\)\s+=\s+\(\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\)",
                     t[i:], re.M) if i >= 0 else []
    if not (ne and al and nat and sp and len(ax) == 3 and len(tau) >= int(nat.group(1))):
        raise SystemExit(f"{path}: cannot read electrons, celldm(1), species, axes or positions from the pw.x header")
    tau = tau[:int(nat.group(1))]
    return {"nelec": float(ne.group(1)), "alat": float(al.group(1)), "axes": np.array(ax, float),
            "valence": {r.split()[0]: float(r.split()[1]) for r in sp.group(1).splitlines() if r.strip()},
            "species": [r[0] for r in tau], "tau": np.array([r[1:] for r in tau], float)}


def neutral(h, symbols, path):
    """Electron count of the neutral cell: sum of the pseudopotential valences (m 1c: 59 I -> odd)."""
    miss = sorted(set(symbols) - set(h["valence"]))
    if miss:
        raise SystemExit(f"{path}: no pseudopotential valence for {miss}")
    return float(sum(h["valence"][e] for e in symbols))


def input_of(out):
    p = out.removesuffix(".gz").removesuffix(".out") + ".in"
    return p + ".gz" if os.path.exists(p + ".gz") else (p if os.path.exists(p) else None)


def input_geometry(p):
    """(symbols, cell, positions) of a scripts/30 pw.x input (CELL_PARAMETERS / ATOMIC_POSITIONS angstrom)."""
    L = a32.read_text(p).splitlines()
    ic = next(i for i, l in enumerate(L) if l.startswith("CELL_PARAMETERS"))
    ip = next(i for i, l in enumerate(L) if l.startswith("ATOMIC_POSITIONS"))
    assert "angstrom" in L[ic] and "angstrom" in L[ip], p
    cell = np.array([l.split()[:3] for l in L[ic + 1:ic + 4]], float)
    rows = []
    for l in L[ip + 1:]:
        r = l.split()
        if len(r) < 4 or not r[0].isalpha():
            break
        rows.append(r)
    return [r[0] for r in rows], cell, np.array([r[1:4] for r in rows], float)


def check_input(at, out, lab):
    """Frame = archived QE input <label>.in(.gz): species order, cell and positions within 1e-6 A."""
    p = input_of(out)
    if p is None:
        raise SystemExit(f"{lab}: no archived QE input next to {out}")
    s, cell, pos = input_geometry(p)
    if not (s == at.get_chemical_symbols() and np.abs(cell - at.cell[:]).max() < 1e-6 and
            np.abs(pos - at.positions).max() < 1e-6):
        raise SystemExit(f"{lab}: frame differs from its QE input {p}")


def frame_of(kind, m, frames_dirs):
    lab, idx = m.group(0), -1
    if kind == "band":
        name, idx = f"band_{m.group(2)}_{m.group(1)}.extxyz", int(m.group(3))
    else:                                          # WP2c: scripts/29 relaxed structure; WP3: scripts/35 frame
        name = f"{lab}_relaxed.extxyz" if kind == "binding" else f"{lab}.extxyz"
    fx = find(frames_dirs, name)
    if fx is None:
        return None
    at = read(fx, index=idx); at = at.copy(); at.calc = None; at.set_tags([0] * len(at))
    return at


def collect(dft_dir, frames_dirs):
    """Atoms with REF data for band frames, WP2c binding frames and WP3 off-equilibrium frames.
    Returns (frames, unmatched, rec): unmatched = complete outputs whose frame file was not found;
    rec = skipped pattern outputs, non-matching outputs, retries and the label -> path indexes."""
    outs, marks = qe_outputs(dft_dir), gaveups(dft_dir)
    idx = {label_of(f): f for f in outs}
    both = sorted(set(idx) & set(marks))
    if both:
        raise SystemExit(f"labels with both an output and a .gaveup marker: {both}")
    rel = lambda f: os.path.relpath(f, dft_dir)
    nonmatch = sorted(({"label": l, "path": rel(f)} for l, f in list(idx.items()) + list(marks.items())
                       if kind_of(l)[0] is None), key=lambda r: r["label"])
    bad = [r["label"] for r in nonmatch if r["label"] not in EXCLUDED and not r["label"].startswith("chk_")]
    if bad:
        raise SystemExit(f"outputs whose label matches no pattern and is neither one of the 28 exclusions "
                         f"of amendment m 1b nor chk_*: {bad}")
    skipped = [{"label": l, "path": rel(f), "reason": "gave up"} for l, f in marks.items() if kind_of(l)[0]]
    frames, unmatched = [], []
    for kind in ("band", "binding", "wp3"):                    # order of the earlier script
        for f in outs:
            k, m = kind_of(label_of(f))
            if k != kind:
                continue
            lab = m.group(0)
            q, why = status(f)
            if q is None:
                skipped.append({"label": lab, "path": rel(f), "reason": why}); continue
            at = frame_of(kind, m, frames_dirs)
            if at is None:
                unmatched.append(lab); continue
            assert len(at) == len(q["forces"]), lab
            check_input(at, f, lab)
            h = qe_header(f); n0 = neutral(h, at.get_chemical_symbols(), f)
            if abs(h["nelec"] - n0) > 1e-6:                # e.g. a q = +1 output archived under a dataset label
                raise SystemExit(f"{lab}: {h['nelec']} electrons, the neutral cell has {n0} ({f})")
            if kind == "wp3":
                ctype = WP3_TYPE[m.group(3)]
                assert at.info.get("config_type", ctype) == ctype, f"{lab}: frame config_type {at.info['config_type']}"
            else:
                ctype = f"band_{m.group(2)}" if kind == "band" else "binding"
            at.info = {"REF_energy": q["F_eV"], "REF_energy_raw": q["F_eV"], "REF_EF": q["EF"],
                       "host": m.group(1), "system": m.group(2), "image": int(m.group(3)) if kind == "band" else -1,
                       "label": lab, "config_type": ctype, "mTS_eV": q["mTS_eV"]}
            at.arrays["REF_forces"] = q["forces"]
            frames.append(at)
    return frames, unmatched, {"skipped": sorted(skipped, key=lambda r: r["label"]), "nonmatching": nonmatch,
                               "retries": retries(dft_dir), "index": idx, "gaveup": marks}


def comp(at):
    """Composition coordinates on the FA19Cs1Pb20I60 baseline; refuses frames outside the family."""
    s = at.get_chemical_symbols(); n = {e: s.count(e) for e in Z}
    c = {"dI": n["I"] - 60, "dN": n["N"] - 38, "nSr": n["Sr"]}
    if not (len(s) == sum(n.values()) and c["dI"] in (0, -1) and c["dN"] in (0, 1) and c["nSr"] in (0, 1) and
            c["dN"] * c["nSr"] == 0 and n["Pb"] + n["Sr"] == 20 and n["C"] == 19 and n["Cs"] == 1 and
            n["H"] == 95 + c["dN"]):
        raise SystemExit(f"{at.info.get('label')}: composition {n} is outside the FA19Cs1Pb20I60(-I)(+GA)(+Sr) family")
    c["vac"] = c["dI"] == -1
    return c


def comp_coords(at):
    c = comp(at)
    return np.array([1.0, c["dI"], c["dN"], c["nSr"]])


def comp_class(at):
    c = comp(at)
    d = "Sr" if c["nSr"] else ("GA" if c["dN"] else "")
    return (d + "+V" if d else "V") if c["vac"] else (d or "host")


def read_report(frames_dirs, allow_empty=False):
    """scripts/35 frames_report.json from the --frames dir that holds it (m 1e: wp3/frames/). Its records
    must be exactly the 96 labels of m 1d, made at the scripts/35 defaults; an empty report is accepted
    only with allow_empty (--no-chk-yet, before any WP3 frame exists). Returns (path, records, complete)."""
    hits = [os.path.join(d, "frames_report.json") for d in frames_dirs
            if os.path.exists(os.path.join(d, "frames_report.json"))]
    if len(hits) != 1:
        raise SystemExit(f"need exactly one frames_report.json among --frames (amendment m 1e), found {hits}")
    rep = json.load(open(hits[0]))
    recs = rep.get("records") if isinstance(rep, dict) else None
    if not isinstance(recs, list):
        raise SystemExit(f"{hits[0]}: no records list")
    labs = [r["label"] for r in recs]
    dup = sorted({l for l in labs if labs.count(l) > 1})
    if dup:
        raise SystemExit(f"{hits[0]}: records found twice: {dup}")
    if not recs and allow_empty:
        return hits[0], {}, False
    err, par = [], rep.get("params") or {}
    if set(labs) != set(WP3_LABELS):
        err.append(f"{len(labs)} records; missing {sorted(set(WP3_LABELS) - set(labs))}, "
                   f"unexpected {sorted(set(labs) - set(WP3_LABELS))}")
    err += [f"params {k} = {par.get(k)!r}, expected {v!r}" for k, v in WP3_PARAMS.items() if par.get(k) != v]
    err += [f"{r['label']}: ok = {r.get('ok')!r} is not a boolean" for r in recs if not isinstance(r.get("ok"), bool)]
    if err:
        raise SystemExit(f"{hits[0]} is not the scripts/35 report of amendment m 1d:\n  " + "\n  ".join(err))
    return hits[0], {r["label"]: r for r in recs}, True


def check_wp3_archive(dft_dir, rec, records):
    """The stop conditions of m 1e and the WP3 / item-1' archive layout; returns the dropped ok frames."""
    raw, extra = os.path.join(dft_dir, "wp3", "raw"), os.path.join(dft_dir, "wp3", "test_extra", "raw")
    norm = lambda d: os.path.normpath(os.path.abspath(d))
    at_ = lambda f, d, l: norm(os.path.dirname(f)) == norm(d) and os.path.basename(f) in (
        l + ".out.gz", l + ".gaveup", l + ".gaveup.gz")
    ok = sorted(l for l, r in records.items() if r.get("ok") is True)
    err = []
    for l in ok:
        if not PATTERNS["wp3"].fullmatch(l):
            err.append(f"{l}: ok record whose label is not a WP3 label")
        elif not any(os.path.exists(os.path.join(raw, l + t)) for t in (".out.gz", ".gaveup", ".gaveup.gz")):
            err.append(f"{l}: ok record with neither wp3/raw/{l}.out.gz nor wp3/raw/{l}.gaveup")
    for l, f in list(rec["index"].items()) + list(rec["gaveup"].items()):
        k = kind_of(l)[0]
        if k == "wp3":
            if l not in ok:
                err.append(f"{l}: WP3 output or marker with no ok record in frames_report.json")
            if not at_(f, raw, l):
                err.append(f"{l}: not archived as wp3/raw/{l}.out.gz or .gaveup ({f})")
        if l in ITEM1P_LABELS and not at_(f, extra, l):
            err.append(f"{l}: item-1' output not archived as wp3/test_extra/raw/{l}.out.gz or .gaveup ({f})")
    for l in sorted(rec["retries"]):                # qe_queue.sh renamed a failed attempt; the retry has not ended
        if kind_of(l)[0] and l not in rec["index"] and l not in rec["gaveup"]:
            err.append(f"{l}: retry pending ({', '.join(rec['retries'][l])}) with neither a final output nor a .gaveup")
    if err:
        raise SystemExit("WP3 archive (amendment m 1e):\n  " + "\n  ".join(err))
    why = {r["label"]: r["reason"] for r in rec["skipped"]}
    return [{"label": l, "reason": why[l]} for l in ok if l in why]


def check_counts(sets, W, found1p):
    """The exact counts of m 1e; returns a list of violations."""
    grp = lambda at: ("band" if at.info["config_type"].startswith("band_") else
                      "binding" if at.info["config_type"] == "binding" else "wp3")
    got = {(k, g): [at for at in v if grp(at) == g] for k, v in sets.items() for g in ("band", "binding", "wp3")}
    want = {("train", "band"): 90, ("train", "binding"): 16, ("train", "wp3"): W, ("valid", "band"): 15,
            ("valid", "binding"): 16, ("valid", "wp3"): 0, ("test", "band"): 30 + len(found1p),
            ("test", "binding"): 16, ("test", "wp3"): 0}
    err = [f"{k} {g}: {len(got[k, g])} frames, expected {w}" for (k, g), w in want.items() if len(got[k, g]) != w]
    hs = lambda L: {at.info["host"] for at in L}
    if not hs(sets["train"]) <= set(TRAIN_HOSTS):
        err.append(f"train frames from non-training hosts {sorted(hs(sets['train']) - set(TRAIN_HOSTS))}")
    if got["train", "binding"] and hs(got["train", "binding"]) != {"m05"}:
        err.append(f"train binding hosts {sorted(hs(got['train', 'binding']))}, expected m05")
    if sets["valid"] and hs(sets["valid"]) != {"m21"}:
        err.append(f"valid hosts {sorted(hs(sets['valid']))}, expected m21")
    if got["test", "binding"] and hs(got["test", "binding"]) != {"m30"}:
        err.append(f"test binding hosts {sorted(hs(got['test', 'binding']))}, expected m30")
    nb = sum(at.info["host"] in ("m30", "m32") for at in got["test", "band"])
    n1 = sum(at.info["label"] in found1p for at in got["test", "band"])
    if nb != 30 or n1 != len(found1p):
        err.append(f"test band: {nb} m30/m32 frames (expected 30), {n1} item-1' frames (expected {len(found1p)})")
    return err


def chk_labels(rec):
    """chk_* labels with an output, a .gaveup marker or a .out.tryN file below --dft."""
    return sorted(l for l in set(rec["index"]) | set(rec["gaveup"]) | set(rec["retries"]) if l.startswith("chk_"))


def v_of(lab, idx, marks):
    """v = F(q=0) - E_F(q=0) - F(q=+1) in eV for one check frame (m 1c): (v, None, geometry record), or
    (None, failure, ...) for a job abandoned under m 1d (.gaveup) or an unconverged SCF. Both jobs are
    final (run_check); an output that is not this frame at q = +1 stops the script."""
    chk = f"chk_{lab}_q1"
    gave = [L for L in (lab, chk) if L in marks]
    if gave:
        return None, f"{gave[0]}: gave up", None
    # the q = +1 job must be this frame with one electron less (scripts/30 --charge 1); else the archive is wrong
    h0, h1 = qe_header(idx[lab]), qe_header(idx[chk])
    n0 = neutral(h0, h0["species"], idx[lab])
    if abs(h0["nelec"] - n0) > 1e-6 or abs(h1["nelec"] - (n0 - 1)) > 1e-6:
        raise SystemExit(f"{chk}: {h1['nelec']} electrons and {lab}: {h0['nelec']}; expected {n0 - 1} and the neutral {n0}")
    if not (h0["species"] == h1["species"] and abs(h0["alat"] - h1["alat"]) < 1e-6 and
            np.abs(h0["axes"] - h1["axes"]).max() < 1e-6 and np.abs(h0["tau"] - h1["tau"]).max() < 1e-6):
        raise SystemExit(f"{chk}: printed cell or positions differ from those of {lab} (not the same frame)")
    geo = {"outputs": True, "inputs": False}
    p0, p1 = input_of(idx[lab]), input_of(idx[chk])
    if p0 is not None and p1 is not None:          # the chk input, where archived, must be the same geometry
        g0, g1 = input_geometry(p0), input_geometry(p1)
        if not (g0[0] == g1[0] and np.abs(g0[1] - g1[1]).max() < 1e-6 and np.abs(g0[2] - g1[2]).max() < 1e-6):
            raise SystemExit(f"{chk}: QE input geometry differs from that of {lab}")
        geo["inputs"] = True
    q0, q1 = a37.qe(idx[lab]), a37.qe(idx[chk])
    for L, q in ((lab, q0), (chk, q1)):
        if not q["scf_converged"]:
            return None, f"{L}: SCF not converged", geo
    if q0["F"] is None or q0["EF"] is None or q1["F"] is None:
        raise SystemExit(f"{lab} / {chk}: converged output without a free energy or E_F")
    return q0["F"] - q0["EF"] - q1["F"], None, geo


def run_check(rec, records):
    """The q = +1 check before training (m 1c), once a chk_* file exists; records are the 96 of read_report."""
    idx, marks, tries = rec["index"], rec["gaveup"], rec["retries"]
    md, todo = {}, [(l, None) for l in CHK_A]
    for X in ("Sr", "undoped"):                    # md300 only where the md450 frame was rejected
        md[X] = next((l for l in (f"m05_{X}_md450", f"m05_{X}_md300") if records[l]["ok"] is True), None)
        todo += [(f"m05_{X}_img0", None), (md[X], None) if md[X] else
                 (f"m05_{X}_md450", "md450 and md300 both rejected by scripts/35 (script rule: (b) fails)")]
    # every job entering the check must be final under m 1d (a JOB DONE output or .gaveup); else stop, no basis
    err = []
    for l, bad in todo:
        for L in ([] if bad else [l, f"chk_{l}_q1"]):
            if L in marks:
                continue
            if L not in idx:
                err.append(f"{L}: neither an output nor a .gaveup marker" +
                           (f" (retry pending: {', '.join(tries[L])})" if L in tries else ""))
            elif "JOB DONE" not in a32.read_text(idx[L]):
                err.append(f"{L}: output without JOB DONE and no .gaveup marker (job unfinished)")
    if err:
        raise SystemExit("q = +1 check of amendment m 1c: archive incomplete, no basis decided:\n  " + "\n  ".join(err))
    v, frames = {}, []
    for l, bad in todo:
        x, why, geo = (None, f"{l}: {bad}", None) if bad else v_of(l, idx, marks)
        v[l] = x
        frames.append({"frame": l, "chk_label": f"chk_{l}_q1", "v_meV": None if x is None else x * 1000,
                       "minus_m30_mean_meV": None if x is None else x * 1000 - V_M30, "failure": why,
                       "geometry_checked": geo})
    fail = lambda ls: [f["failure"] for f in frames if f["frame"] in ls and f["failure"]]
    A = CHK_A
    fa = fail(A)
    va = None if fa else ((v[A[0]] - v[A[1]]) - (v[A[2]] - v[A[3]])) * 1000
    res = {"tolerance_meV": CHK_TOL, "m30_mean_v_meV": V_M30, "m30_paired_value_meV": A_M30, "v": frames,
           "a": {"value_meV": va, "pass": va is not None and abs(va) < CHK_TOL, "failures": fa,
                 "Sr_img3_minus_img0_meV": None if fa else (v[A[0]] - v[A[1]]) * 1000,
                 "undoped_img3_minus_img0_meV": None if fa else (v[A[2]] - v[A[3]]) * 1000}, "b": {}}
    for X in ("Sr", "undoped"):
        B = [md[X] or f"m05_{X}_md450", f"m05_{X}_img0"]
        fb = fail(B)
        vb = None if fb else (v[B[0]] - v[B[1]]) * 1000
        res["b"][X] = {"frame": B[0], "md_frame_rule": "md450" if md[X] and md[X].endswith("md450") else
                       ("md300 (md450 rejected)" if md[X] else "none (md450 and md300 rejected; script rule)"),
                       "value_meV": vb, "pass": vb is not None and abs(vb) < CHK_TOL, "failures": fb}
    res["b"]["pass_both"] = res["b"]["Sr"]["pass"] and res["b"]["undoped"]["pass"]
    res["b"]["used"] = res["a"]["pass"]            # (a) fails: raw basis throughout, (b) not used
    res["chk_labels_not_used"] = sorted(set(chk_labels(rec)) - {f["chk_label"] for f in frames})
    return res


def decide(chk):
    """Branch of m 1c, from the check outcome only: (basis, energy rule of the WP3 vacancy frames)."""
    if not chk["a"]["pass"]:
        return "raw", "raw"
    return "Eprime", "Eprime" if chk["b"]["pass_both"] else "weight0"


def set_targets(frames, basis, wp3_vac):
    """REF_energy of m 1c on every frame of every split; REF_energy_raw (F) and REF_EF stay."""
    for at in frames:
        c, F = comp(at), at.info["REF_energy_raw"]
        e = F - (at.info["REF_EF"] - EF_REF) if (basis == "Eprime" and c["vac"]) else F
        cd = (C_D[basis]["Sr"] * c["nSr"] + C_D[basis]["GA"] * c["dN"] + 0.0) if c["vac"] else 0.0   # + 0.0: no -0.0
        at.info.update({"REF_energy": e - cd, "band_term_eV": F - (e - cd), "c_D_eV": cd})
        if wp3_vac == "weight0" and c["vac"] and at.info["config_type"] in ("rattle", "md"):
            at.info["config_energy_weight"] = 0.0      # forces kept (m 1c, (a) passes and (b) fails)


def zero_shot(frames, threads):
    """Foundation E0s {Z: eV} and zero-shot MACE-MP-0 (medium, CPU, float64) (E, forces) per frame."""
    import torch, warnings; warnings.filterwarnings("ignore"); torch.set_num_threads(threads)
    from mace.calculators import mace_mp
    calc = mace_mp(model="medium", device="cpu", default_dtype="float64")
    model = calc.models[0]
    e0f = {int(z): float(e) for z, e in zip(model.atomic_numbers.numpy().ravel(),
                                            model.atomic_energies_fn.atomic_energies.detach().numpy().ravel())}
    res = []
    for at in frames:
        b = at.copy(); b.calc = calc
        res.append((float(b.get_potential_energy()), b.get_forces().copy()))
    return e0f, res


def stats(x):
    x = np.asarray(x, float)
    return {"n": int(x.size), "mean": float(x.mean()), "sd": float(x.std(ddof=1)) if x.size > 1 else None,
            "min": float(x.min()), "max": float(x.max())} if x.size else {"n": 0}


def dft_diagnostics(train):
    """DFT-only diagnostics of m 1c on the training frames (meV unless stated; SD with ddof 1)."""
    E = {at.info["label"]: at.info["REF_EF"] for at in train}
    band = [at for at in train if at.info["config_type"].startswith("band_")]
    und_of = lambda at: f"{at.info['host']}_undoped_img{at.info['image']}"
    dEF = {D: stats([(E[at.info["label"]] - E[und_of(at)]) * 1000 for at in band
                     if at.info["system"] == D and und_of(at) in E]) for D in ("Sr", "GA")}
    und = [at.info["REF_EF"] for at in band if at.info["system"] == "undoped"]
    wp3 = [at for at in train if at.info["config_type"] in ("rattle", "md")]
    spread = {s: stats([at.info["REF_EF"] for at in wp3 if at.info["system"] == s]) for s in ("undoped", "GA", "Sr", "pristine")}
    shift = defaultdict(list)
    for at in wp3:
        ref = f"{at.info['host']}_{at.info['system']}_img0"
        if ref in E:
            shift[f"{at.info['system']}_{at.info['label'].rsplit('_', 1)[1]}"].append((at.info["REF_EF"] - E[ref]) * 1000)
    return {"mean_dEF_per_dopant_meV": dEF,
            "EF_ref_check": {"fixed_eV": EF_REF, "median_train_undoped_band_eV": float(np.median(und)) if und else None,
                             "n": len(und)},
            "wp3_EF_spread": {"EF_eV_by_system": spread,
                              "EF_minus_band_img0_meV_by_system_kind": {k: stats(x) for k, x in sorted(shift.items())}}}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dft", required=True)
    ap.add_argument("--frames", nargs="+", required=True, help="dirs with band, WP2c and WP3 frames (+ frames_report.json)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--test-hosts", nargs="+", required=True)
    ap.add_argument("--valid-hosts", nargs="+", required=True)
    ap.add_argument("--allow-missing", action="store_true",
                    help="continue when converged outputs have no frame file (listed in dataset_meta.json)")
    ap.add_argument("--no-chk-yet", action="store_true",
                    help="TESTING ONLY, before any chk_* file exists: write dataset_meta.json with basis "
                         "UNDECIDED and no dataset or E0s (an empty frames_report.json is then accepted)")
    ap.add_argument("--threads", type=int, default=6)
    a = ap.parse_args(argv)
    norm = lambda x: f"m{int(str(x).lstrip('m')):02d}"          # '30' and 'm30' both -> 'm30'
    test, valid = {norm(x) for x in a.test_hosts}, {norm(x) for x in a.valid_hosts}
    assert not test & valid, f"hosts in both test and valid: {sorted(test & valid)}"
    rpath, records, complete = read_report(a.frames, allow_empty=a.no_chk_yet)
    frames, unmatched, rec = collect(a.dft, a.frames)
    dropped = check_wp3_archive(a.dft, rec, records)
    if unmatched and not a.allow_missing:
        raise SystemExit(f"{len(unmatched)} converged outputs have no frame file in --frames "
                         f"(e.g. {unmatched[:5]}); add the directory or pass --allow-missing")
    found = {f.info["host"] for f in frames}
    if not (test | valid) <= found:
        raise SystemExit(f"held-out hosts with no frames: {sorted((test | valid) - found)} "
                         "(an item-1' host with no converged frame is left out of --test-hosts)")
    split = lambda at: "test" if at.info["host"] in test else ("valid" if at.info["host"] in valid else "train")
    for at in frames:
        at.info["split"] = split(at)
    sets = {k: [f for f in frames if f.info["split"] == k] for k in ("train", "valid", "test")}
    n_ok = sum(r.get("ok") is True for r in records.values())
    W = n_ok - len(dropped)
    labs = {f.info["label"] for f in frames}
    found1p = [l for l in ITEM1P_LABELS if l in labs]
    why = {r["label"]: r["reason"] for r in rec["skipped"]}
    missing1p = [{"label": l, "reason": why.get(l, "no frame file" if l in unmatched else "no output")}
                 for l in ITEM1P_LABELS if l not in labs]
    err = check_counts(sets, W, set(found1p))
    if err:
        raise SystemExit("counts differ from amendment m 1e:\n  " + "\n  ".join(err))
    chk_present = chk_labels(rec)
    if not chk_present and not a.no_chk_yet:
        raise SystemExit("no chk_<frame label>_q1 output below --dft: the q = +1 check of amendment m 1c "
                         "decides the energy basis (--no-chk-yet only for testing)")
    if chk_present and a.no_chk_yet:
        raise SystemExit(f"chk_* files exist ({chk_present[:3]} ...): run without --no-chk-yet")
    chk = run_check(rec, records) if chk_present else None
    basis, wp3_vac = decide(chk) if chk is not None else ("UNDECIDED", "UNDECIDED")
    rejected = [{k: r.get(k) for k in ("label", "min_dist_A", "mace_fmax_eVA", "topology_ok")}
                for r in records.values() if r.get("ok") is not True]
    meta = {"amendment": "2026-10-28m", "basis": basis, "wp3_vacancy_energy": wp3_vac,
            "q1_check": chk,
            "n": {k: len(v) for k, v in sets.items()},
            "hosts": {k: sorted({f.info['host'] for f in v}) for k, v in sets.items()},
            "n_by_config_type": {k: dict(Counter(f.info["config_type"] for f in v)) for k, v in sets.items()},
            "n_by_host": {k: dict(Counter(f.info["host"] for f in v)) for k, v in sets.items()},
            "test_hosts": sorted(test), "valid_hosts": sorted(valid),
            "unmatched_outputs": unmatched, "skipped_outputs": rec["skipped"], "nonmatching_outputs": rec["nonmatching"],
            "resubmitted": rec["retries"],
            "wp3": {"frames_report": rpath, "records": len(records), "report_complete": complete, "ok": n_ok,
                    "rejected": rejected, "dropped": dropped, "W": W, "minimum": WP3_MIN, "minimum_met": W >= WP3_MIN},
            "item1p": {"expected": len(ITEM1P_LABELS), "found": found1p, "missing": missing1p},
            "E_F_ref_eV": EF_REF, "c_D_meV": {b: {k: x * 1000 for k, x in v.items()} for b, v in C_D.items()},
            "diagnostics": dft_diagnostics(sets["train"]),
            "note": "E0s valid only within the FA19Cs1Pb20I60(-I)(+GA)(+Sr) family.",
            "key_notes": {
                "band_term_eV": "extxyz info: F - REF_energy per frame, the E' shift E_F - E_F,ref (vacancy cells, "
                                "E' basis) plus c_D (Sr+V, GA+V); no longer the fitted class term of amendment h",
                "offset_fit.band_term_removed_meV": "the c_D constants subtracted on this basis (meV) and E_F,ref of "
                                                    "the E' shift (None on the raw basis)",
                "offset_fit.train_residual_rms_meV": "over the 106 band and binding fit frames",
                "residual": "REF_energy - E(zero-shot MACE-MP-0 with E0s.json), i.e. DFT target - MACE "
                            "(wp3_residual_*, residual_rms_*, start_check_reference.mean_residual_meV)",
                "m05_far_site_error_meV": "E_b(MACE) - E_b(DFT) at the m05 far site (model - DFT, as item 3) = -c_D"},
            "script_rules": SCRIPT_RULES}
    os.makedirs(a.out, exist_ok=True)
    dump = lambda: json.dump(meta, open(os.path.join(a.out, "dataset_meta.json"), "w"), indent=1)
    if basis == "UNDECIDED" or W < WP3_MIN:
        stale = [f for f in ("train.xyz", "valid.xyz", "test.xyz", "E0s.json") if os.path.exists(os.path.join(a.out, f))]
        if stale:
            raise SystemExit(f"--out already holds {stale}; use an empty directory")
        meta["status"] = ("UNDECIDED: no q = +1 check yet; no dataset written" if basis == "UNDECIDED" else
                          f"W = {W} < {WP3_MIN} WP3 frames: a further amendment is needed before training "
                          "(amendment m 1d); no dataset written")
        dump(); print(json.dumps(meta, indent=1))
        if basis == "UNDECIDED":
            return
        raise SystemExit(meta["status"])
    set_targets(frames, basis, wp3_vac)

    tr, va = sets["train"], sets["valid"]
    e0f, zs = zero_shot(tr + va, a.threads)
    Em = np.array([e for e, _ in zs])
    X = np.array([comp_coords(at) for at in tr + va])
    y = np.array([at.info["REF_energy"] for at in tr + va]) - Em
    fit = np.array([at.info["config_type"].startswith("band_") or at.info["config_type"] == "binding" for at in tr]
                   + [False] * len(va))
    coef, _, rank, _ = np.linalg.lstsq(X[fit], y[fit], rcond=None)
    # Rank 4 needs vacancy-free frames with and without each dopant (the m05 host and D_j cells)
    assert rank == X.shape[1] and fit.sum() == 106, f"offset fit rank {rank} on {fit.sum()} frames"
    # Per-element offsets o_e apply to EVERY atom of element e. With o_C = o_H = o_Cs = 0 and
    # n_I = 60+dI, n_N = 38+dN (GA also adds one H, whose offset is 0), n_Pb = 20-nSr, n_Sr = nSr:
    #   sum_e n_e o_e = (60+dI) o_I + (38+dN) o_N + (20-nSr) o_Pb + nSr o_Sr
    # matches c0 + c1 dI + c2 dN + c3 nSr exactly when
    o_I, o_N = coef[1], coef[2]
    o_Pb = (coef[0] - 60 * o_I - 38 * o_N) / 20.0
    o_Sr = coef[3] + o_Pb
    off = {"I": o_I, "N": o_N, "Pb": o_Pb, "Sr": o_Sr, "C": 0.0, "H": 0.0, "Cs": 0.0}
    for at in frames:   # exactness check of the per-element assignment on every frame
        assert abs(sum(off[e] for e in at.get_chemical_symbols()) - comp_coords(at) @ coef) < 1e-6
    e0 = {Z[e]: e0f[Z[e]] + off[e] for e in Z}
    resid = y - X @ coef                           # REF_energy - E(zero-shot with E0s.json), eV
    N = np.array([len(at) for at in tr + va], float)
    ntr = len(tr); rt, Nt = resid[:ntr], N[:ntr]
    w = np.array([at.info.get("config_energy_weight", 1.0) for at in tr])
    sq = np.array([float(((f - at.arrays["REF_forces"]) ** 2).sum()) for at, (_, f) in zip(tr + va, zs)])
    L_F = float(sq[:ntr].sum() / (3 * Nt.sum()))   # every training frame, force weight 1
    L_E = float(np.mean(w * (rt / Nt) ** 2))       # mean over all n_train graphs, zero-weight ones included
    w_E = 100.0 * L_F / L_E
    rv, Nv = resid[ntr:], N[ntr:]
    rmse_e = float(np.sqrt(np.mean((rv / Nv) ** 2)) * 1000)
    rmse_f = float(np.sqrt(sq[ntr:].sum() / (3 * Nv.sum())) * 1000)

    # diagnostics of m 1c (training frames only; no decision rests on them)
    lab = {at.info["label"]: i for i, at in enumerate(tr)}
    def eb_err(site, b):                           # E_b(MACE) - E_b(DFT) at an m05 far site, meV (= -c_D)
        def t(l):                                  # MACE - DFT target of one frame (no c_D)
            at = tr[lab[l]]
            ep = at.info["REF_EF"] - EF_REF if (b == "Eprime" and comp(at)["vac"]) else 0.0
            return Em[lab[l]] - (at.info["REF_energy_raw"] - ep)
        return float((t(f"m05_{site}_vac") - t(f"m05_{site}_novac") - t("m05_vac") + t("m05_host")) * 1000)
    need = [f"m05_{x}" for x in ("vac", "host", "Sr112_vac", "Sr112_novac", "GA4_vac", "GA4_novac")]
    far = ({s: {b: eb_err(s, b) for b in ("raw", "Eprime")} for s in ("Sr112", "GA4")}
           if all(l in lab for l in need) else None)
    far_ok = far is not None and all(abs(far[s][b] + C_D[b][d] * 1000) < 0.001
                                     for s, d in (("Sr112", "Sr"), ("GA4", "GA")) for b in C_D)
    yraw = np.array([at.info["REF_energy_raw"] for at in tr]) - Em[:ntr]
    X6 = np.array([list(comp_coords(at)) + [comp(at)["nSr"] * comp(at)["vac"], comp(at)["dN"] * comp(at)["vac"]] for at in tr])
    sat = {}
    for nm, m_ in (("band_binding_106", fit[:ntr]), ("all_train", np.ones(ntr, bool))):
        c6, _, r6, _ = np.linalg.lstsq(X6[m_], yraw[m_], rcond=None)
        sat[nm] = {"n": int(m_.sum()), "rank": int(r6), "coef_eV": c6.tolist(),
                   "Sr+V_meV": float(c6[4] * 1000), "GA+V_meV": float(c6[5] * 1000)}
    wp3 = [i for i, at in enumerate(tr) if at.info["config_type"] in ("rattle", "md")]
    wres, wres_s = defaultdict(list), defaultdict(list)
    for i in wp3:
        kind = tr[i].info["label"].rsplit("_", 1)[1]
        wres[f"{tr[i].info['host']}_{kind}"].append(rt[i] * 1000)
        wres_s[f"{tr[i].info['system']}_{kind}"].append(rt[i] * 1000)
    cls = lambda ii: {c: float(np.sqrt(np.mean([rt[i] ** 2 for i in ii if comp_class(tr[i]) == c])) * 1000)
                      for c in sorted({comp_class(tr[i]) for i in ii})}
    meta["diagnostics"].update({
        "saturated_6col_raw_F": sat,
        "m05_far_site_error_meV": None if far is None else {**far, "sign": "MACE - DFT",
                                                            "equal_to_minus_fixed_c_D_within_0.001": far_ok},
        "wp3_residual_meV_by_host_kind": {k: stats(x) for k, x in sorted(wres.items())},
        "wp3_residual_meV_by_system_kind": {k: stats(x) for k, x in sorted(wres_s.items())},
        "residual_rms_meV_per_class": {"band_binding_106": cls(np.flatnonzero(fit[:ntr])), "wp3": cls(wp3)}})
    if not far_ok:
        print("WARNING: the m05 far-site errors (MACE - DFT) differ from minus the fixed c_D constants", far)
    meta.update({
        "E0s": {str(k): v for k, v in e0.items()},
        "offset_fit": {"coords": ["const(FA19Cs1Pb20I60)", "dI", "dN(GA)", "nSr"], "frames": int(fit.sum()),
                       "band_term_removed_meV": {"Sr+vac": C_D[basis]["Sr"] * 1000, "GA+vac": C_D[basis]["GA"] * 1000,
                                                 "E_F_ref_eV": EF_REF if basis == "Eprime" else None},
                       "coef_eV": coef.tolist(), "rank": int(rank), "offsets_eV": {k: float(v) for k, v in off.items()},
                       "train_residual_rms_meV": float(np.sqrt(np.mean(resid[fit] ** 2)) * 1000)},
        "loss_weights": {"L_F_eVA2": L_F, "L_E_eVatom2": L_E, "n_train": ntr, "n_E": int((w > 0).sum()),
                         "N_mean": float(Nt.mean()), "w_F": W_F, "w_E": float(f"{w_E:.1e}"), "w_E_unrounded": w_E,
                         "energy_weight_zero": sorted(at.info["label"] for at in tr if "config_energy_weight" in at.info)},
        "start_check_reference": {"note": "zero-shot MACE-MP-0 with E0s.json on valid.xyz; compare with the "
                                          "pre-registered values of amendment m item 2 (reported only)",
                                  "n_valid": len(va), "RMSE_E_per_atom_meV": rmse_e, "RMSE_F_meV_A": rmse_f,
                                  "mean_residual_meV": float(np.mean(rv) * 1000),
                                  "pre_registered": {"RMSE_E_per_atom_meV": START_CHECK["RMSE_E_per_atom_meV"][basis],
                                                     "RMSE_F_meV_A": START_CHECK["RMSE_F_meV_A"]}}})
    for k, v in sets.items():
        write(os.path.join(a.out, f"{k}.xyz"), v, format="extxyz")
    json.dump({str(k): v for k, v in e0.items()}, open(os.path.join(a.out, "E0s.json"), "w"))
    dump()
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()

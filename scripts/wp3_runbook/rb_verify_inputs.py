# RUNBOOK step 2d: check the scripts/30 item-1' and chk_ inputs and the scripts/35 WP3 inputs BEFORE any DFT
# (run from the repo root; node_step34 runs it again before the 3a archive).
#   python rb_verify_inputs.py <jobs root> <scripts/35 frames dir>
# Every <jobs>/wp3x/<label>/<label>.in must be one of the 50 item-1' labels, every <jobs>/wp3chk/<label>/<label>.in
# one of the 8 chk_ labels of m 1c (md300 where md450 was rejected); each input's species, cell and positions equal
# the frame scripts/33 will pair it with (1e-6 A), tot_charge is 0 (item 1') or 1 (chk_), prefix = label,
# calculation 'scf', and positions carry no if_pos columns.
# WP3: the job dirs under <jobs>/wp3 are exactly the ok records of <frames>/frames_report.json; each frame and input
# is non-empty and the input equals its frame (1e-6 A); an input not yet run (no .out, .out.try* or .gaveup, and
# pseudo_dir still as scripts/30 wrote it: run_qe.sh rewrites it in place) has the input_sha256 of its fsynced
# <label>.meta.json. scripts/35 writes the frame and input without fsync, so a hard stop can leave either empty under
# an ok record; this catches it before its DFT, instead of it becoming a 1d 'gave up' drop.
import glob, hashlib, importlib.util, json, os, re, sys
import numpy as np
s = importlib.util.spec_from_file_location("a33", "scripts/33_finetune_dataset.py")
a33 = importlib.util.module_from_spec(s); s.loader.exec_module(a33)
JOBS, FR = sys.argv[1], sys.argv[2]
rec = {r["label"]: r["ok"] for r in json.load(open(os.path.join(FR, "frames_report.json")))["records"]}
md = {X: next((k for k in ("md450", "md300") if rec.get(f"m05_{X}_{k}") is True), None) for X in ("Sr", "undoped")}
want_chk = {f"chk_{l}_q1" for l in a33.CHK_A} | {f"chk_m05_{X}_img0_q1" for X in md} | \
           {f"chk_m05_{X}_{k}_q1" for X, k in md.items() if k}
bad = []
got = {"wp3x": set(), "wp3chk": set()}
for camp in ("wp3x", "wp3chk"):
    for p in sorted(glob.glob(os.path.join(JOBS, camp, "*", "*.in"))):
        lab = os.path.basename(p)[:-3]; got[camp].add(lab); chk = camp == "wp3chk"
        if os.path.basename(os.path.dirname(p)) != lab:
            bad.append(f"{p}: directory is not the label"); continue
        fl = lab[4:-3] if chk and lab.startswith("chk_") and lab.endswith("_q1") else lab
        k, m = a33.kind_of(fl)
        at = a33.frame_of(k, m, ["../bands", FR]) if k in ("band", "wp3") else None
        if at is None:
            bad.append(f"{lab}: no frame for {fl}"); continue
        sym, cell, pos = a33.input_geometry(p)
        t = open(p).read()
        q = re.search(r"tot_charge\s*=\s*([-\d.]+)", t)
        rows = t[t.index("ATOMIC_POSITIONS"):].splitlines()[1:len(at) + 1]
        checks = {"species": sym == at.get_chemical_symbols(),
                  "geometry": np.abs(cell - at.cell[:]).max() < 1e-6 and np.abs(pos - at.positions).max() < 1e-6,
                  "tot_charge": q is not None and float(q.group(1)) == (1.0 if chk else 0.0),
                  "prefix": re.search(rf"prefix\s*=\s*'{re.escape(lab)}'", t) is not None,
                  "scf": re.search(r"calculation\s*=\s*'scf'", t) is not None,
                  "4 columns": all(len(r.split()) == 4 for r in rows)}
        bad += [f"{lab}: {c} check failed" for c, ok in checks.items() if not ok]
if got["wp3x"] != set(a33.ITEM1P_LABELS):
    bad.append(f"item-1' labels: missing {sorted(set(a33.ITEM1P_LABELS) - got['wp3x'])}, extra {sorted(got['wp3x'] - set(a33.ITEM1P_LABELS))}")
if got["wp3chk"] != want_chk:
    bad.append(f"chk_ labels: missing {sorted(want_chk - got['wp3chk'])}, extra {sorted(got['wp3chk'] - want_chk)}")
okl = {l for l, v in rec.items() if v is True}
wd = os.path.join(JOBS, "wp3")
dirs = {x for x in os.listdir(wd) if os.path.isdir(os.path.join(wd, x))} if os.path.isdir(wd) else set()
if dirs != okl:
    bad.append(f"WP3 job dirs: missing {sorted(okl - dirs)}, without an ok record {sorted(dirs - okl)}")
size = lambda f: os.path.getsize(f) if os.path.exists(f) else "missing"
for lab in sorted(okl & dirs):
    b = os.path.join(wd, lab, lab); p = b + ".in"; fx = os.path.join(FR, f"{lab}.extxyz")
    try:
        if not (os.path.getsize(fx) > 0 and os.path.getsize(p) > 0):
            raise ValueError("empty file")
        at = a33.frame_of("wp3", a33.kind_of(lab)[1], [FR]); sym, cell, pos = a33.input_geometry(p)
        if sym != at.get_chemical_symbols() or np.abs(cell - at.cell[:]).max() >= 1e-6 or np.abs(pos - at.positions).max() >= 1e-6:
            bad.append(f"{lab}: WP3 input differs from its frame")
        ran = os.path.exists(b + ".out") or glob.glob(b + ".out.try*") or os.path.exists(b + ".gaveup")
        if not ran and re.search(r"pseudo_dir\s*=\s*'/data/pseudo'\s*$", open(p).read(), re.M):   # as scripts/30 wrote it
            if hashlib.sha256(open(p, "rb").read()).hexdigest() != json.load(open(b + ".meta.json"))["input_sha256"]:
                bad.append(f"{lab}: WP3 input (not yet run) differs from the input_sha256 of its meta.json")
    except Exception as e:
        bad.append(f"{lab}: WP3 frame or input unreadable ({type(e).__name__}: {e}; frame {size(fx)} B, input {size(p)} B)")
print(f"{len(got['wp3x'])} item-1', {len(got['wp3chk'])} chk_ and {len(okl & dirs)} WP3 inputs; m05 (b) frames {md}")
print("\n".join(bad) if bad else "ALL INPUT CHECKS PASS")
sys.exit(1 if bad else 0)

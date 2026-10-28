# RUNBOOK step 2d: check the scripts/30 item-1' and chk_ inputs BEFORE any DFT (run from the repo root).
#   python rb_verify_inputs.py <jobs root> <scripts/35 frames dir>
# Every <jobs>/wp3x/<label>/<label>.in must be one of the 50 item-1' labels, every <jobs>/wp3chk/<label>/<label>.in
# one of the 8 chk_ labels of m 1c (md300 where md450 was rejected); each input's species, cell and positions equal
# the frame scripts/33 will pair it with (1e-6 A), tot_charge is 0 (item 1') or 1 (chk_), prefix = label,
# calculation 'scf', and positions carry no if_pos columns.
import glob, importlib.util, json, os, re, sys
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
print(f"{len(got['wp3x'])} item-1' and {len(got['wp3chk'])} chk_ inputs; m05 (b) frames {md}")
print("\n".join(bad) if bad else "ALL INPUT CHECKS PASS")
sys.exit(1 if bad else 0)

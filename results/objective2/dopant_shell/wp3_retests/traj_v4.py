"""V4 read-out (V4V5_PRESPEC_2026-11-18.md; traj_v3.py with the run directory changed): far-referenced Sr hinge and flank E_b of m05, m21 and m30 at every kept
checkpoint of run_v4. Checkpoint weights are loaded into the saved model object (the checkpoint's 'model' entry).
DFT basis: REF_energy_raw. Output: v4_traj.json, v4_traj.csv."""
import glob, json, re, sys, csv
sys.argv = [sys.argv[0]]
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import torch
import eval_v1 as ev
from mace.calculators import MACECalculator
R = "run_v4"
sets = {"m30": ev.load("test.xyz"), "m21": ev.load("valid.xyz"), "m05": ev.load("train.xyz")}
need, Ed = {}, {}
for h, d in sets.items():
    st = ev.SEL[h]["sites"]
    js = [st[n]["site"] for n in ("Sr_hinge", "Sr_flank", "Sr_far")]
    labs = [f"{h}_host", f"{h}_vac"] + [f"{h}_Sr{j}_{t}" for j in js for t in ("vac", "novac")]
    assert all(l in d for l in labs), (h, [l for l in labs if l not in d])
    need[h] = {l: d[l] for l in labs}
    Ed[h] = {l: float(a.info["REF_energy_raw"]) for l, a in need[h].items()}
def read(Em, h):
    st = ev.SEL[h]["sites"]; far = st["Sr_far"]["site"]; out = {}
    for n in ("Sr_hinge", "Sr_flank"):
        j = st[n]["site"]
        out[n] = {"model_meV": ev.eb(Em, h, "Sr", j) - ev.eb(Em, h, "Sr", far),
                  "dft_meV": ev.eb(Ed[h], h, "Sr", j) - ev.eb(Ed[h], h, "Sr", far)}
    return out
model = torch.load(f"{R}/wp3v4.model", map_location="cpu", weights_only=False).double()
cks = sorted(glob.glob(f"{R}/checkpoints/wp3v4_run-123_epoch-*.pt"), key=lambda p: int(re.search(r"epoch-(\d+)", p).group(1)))
res = {}
def run(tag):
    calc = MACECalculator(models=[model], device="cpu", default_dtype="float64")
    r = {}
    for h in need:
        Em, _ = ev.predict(calc, need[h]); r[h] = read(Em, h)
    res[tag] = r
    print(tag, " ".join(f"{h}:{r[h]['Sr_hinge']['model_meV']:+.1f}/{r[h]['Sr_flank']['model_meV']:+.1f}" for h in r), flush=True)
run("selected")
for p in cks:
    ep = int(re.search(r"epoch-(\d+)", p).group(1))
    ck = torch.load(p, map_location="cpu", weights_only=False)
    model.load_state_dict(ck["model"]); run(f"epoch-{ep}")
json.dump(res, open("v4_traj.json", "w"), indent=1)
with open("v4_traj.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["checkpoint", "host", "site", "model_meV", "dft_meV"])
    for t, r in res.items():
        for h in r:
            for n, v in r[h].items():
                w.writerow([t, h, n, f"{v['model_meV']:.2f}", f"{v['dft_meV']:.2f}"])
print("DFT", {h: {n: round(v["dft_meV"], 1) for n, v in res["selected"][h].items()} for h in need})

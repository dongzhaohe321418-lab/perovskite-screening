# RUNBOOK step 5a: technical-failure check of amendment m item 2, from the training log, the results file and m21 ONLY.
#   python rb_techfail.py <run> <ds dir> [<n m21 frames, default all 31>]
# (1) a non-finite training or validation loss at any epoch (results file and log, not the exit status);
# (2) a non-finite energy or force of the selected <run>/wp3.model on any m21 frame (valid.xyz; float64, cpu, head
# Default). Deterministic abnormal ends (item 2 Interruptions) are judged from the restart list, not here.
import glob, json, math, re, sys
from ase.io import read
import numpy as np
run, ds = sys.argv[1], sys.argv[2]
nmax = int(sys.argv[3]) if len(sys.argv) > 3 else None
bad = []
for res in glob.glob(f"{run}/results/*_train.txt"):
    for l in open(res):
        if l.strip():
            r = json.loads(l.replace("NaN", "null").replace("Infinity", "null"))
            if r.get("loss") is None or not math.isfinite(r["loss"]):
                bad.append(f"non-finite loss in {res}: mode {r.get('mode')} epoch {r.get('epoch')}")
for lg in glob.glob(f"{run}/logs/*.log"):
    for l in open(lg):
        if re.search(r"loss=\s*(nan|inf|-inf)", l, re.I):
            bad.append(f"non-finite loss in {lg}: {l.strip()[:120]}")
from mace.calculators import MACECalculator
calc = MACECalculator(model_paths=[f"{run}/wp3.model"], device="cpu", default_dtype="float64", head="Default")
assert calc.head == "Default", calc.head
frames = read(f"{ds}/valid.xyz", ":")[:nmax]
assert {a.info["host"] for a in frames} == {"m21"}, "valid.xyz must hold m21 frames only"
for a in frames:
    b = a.copy(); b.calc = calc
    if not (np.isfinite(b.get_potential_energy()) and np.isfinite(b.get_forces()).all()):
        bad.append(f"non-finite energy or forces on {a.info['label']}")
print(f"{len(frames)} m21 frames evaluated with {run}/wp3.model")
print("\n".join(bad) if bad else "no technical failure (items checked here)")
sys.exit(1 if bad else 0)

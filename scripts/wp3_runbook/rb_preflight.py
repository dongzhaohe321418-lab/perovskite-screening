# RUNBOOK step 4b: the pre-flight checks of amendment m item 2 on the INFO log of the --dry_run.
#   python rb_preflight.py <preflight>/logs/wp3_run-123.log <ds dir> <foundation model path> <w_E> [<lr>]
import ast, json, re, sys
log, ds, fm, we = sys.argv[1:5]
lr = sys.argv[5] if len(sys.argv) > 5 else "0.005"           # 0.0025 for the one retry (item 2)
t = open(log).read()
E0 = {int(k): v for k, v in json.load(open(f"{ds}/E0s.json")).items()}
m = re.search(r"Atomic Energies used \(z: eV\) for head Default: (\{.*\})", t)
z = re.search(r"Using filtered elements: \[(.*)\]", t)
checks = {
    "MACE version: 0.3.16": "MACE version: 0.3.16" in t,
    f"Using foundation model {fm} as initial checkpoint.": f"Using foundation model {fm} as initial checkpoint." in t,
    "Using heads: ['Default']": "Using heads: ['Default']" in t,
    "filtered elements Z = 1 6 7 38 53 55 82":
        z is not None and sorted(int(x) for x in re.findall(r"\d+", z.group(1).replace("int64", ""))) == [1, 6, 7, 38, 53, 55, 82],
    "Atomic Energies used ... equal to E0s.json": m is not None and ast.literal_eval(m.group(1)) == E0,
    "Using weighted loss function for fine-tuning": "Using weighted loss function for fine-tuning" in t,
    "Using Exponential Moving Average with decay: 0.99": "Using Exponential Moving Average with decay: 0.99" in t,
    f"Learning rate: {lr}, weight decay: 5e-07": f"Learning rate: {lr}, weight decay: 5e-07" in t,
    f"WeightedEnergyForcesLoss(energy_weight={float(we):.3f}, forces_weight=100.000)":
        f"WeightedEnergyForcesLoss(energy_weight={float(we):.3f}, forces_weight=100.000)" in t,
    "no line with 'multiheads finetuning'": "multiheads finetuning" not in t.lower()}
for k, v in checks.items():
    print("PASS" if v else "FAIL", k)
sys.exit(0 if all(checks.values()) else 1)

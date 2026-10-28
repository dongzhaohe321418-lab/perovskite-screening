# RUNBOOK step 4d: start check of amendment m item 2 on the "Initial" validation record (epoch null) of the results file.
#   python rb_startcheck.py <run>/results/wp3_run-123_train.txt <basis: Eprime|raw>
import json, sys
res, basis = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(res) if l.strip()]
init = [r for r in rows if r.get("mode") == "eval" and r.get("epoch") is None and r.get("head") == "Default"]
if not init:
    sys.exit("no Initial record yet")
e, f = init[0]["rmse_e_per_atom"] * 1000, init[0]["rmse_f"] * 1000
want = {"Eprime": 0.3334, "raw": 0.3499}[basis]
ok_f, ok_e = abs(f - 79.819) <= 0.01, abs(e - want) <= 0.001
print(f"Initial m21: RMSE_F {f:.4f} meV/A (79.819 +/- 0.01: {'PASS' if ok_f else 'FAIL'}); "
      f"RMSE_E_per_atom {e:.5f} meV/atom ({want} +/- 0.001, basis {basis}: {'PASS' if ok_e else 'FAIL'})")
sys.exit(0 if ok_f and ok_e else 1)

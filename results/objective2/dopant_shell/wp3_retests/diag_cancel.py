"""D-V1b (post hoc, reported only): per-cell energy residuals r = E_model - E_DFT (raw F) on the m05 binding frames and
on the m30 test binding frames, and how they combine into E_b. E_b error = r(D+V) - r(D) - r(V) + r(host)."""
import json, sys
import numpy as np
import eval_v1 as ev
P = "<project>"
models = {"ZS": f"<wp3_retests>/foundation/20231203mace128L1_epoch199model",
          "WP3": f"{P}/perovskite-screening/results/objective2/dopant_shell/wp3/run2/wp3.model",
          "V1": f"<wp3_retests>/run_v1/wp3v1.model"}
sets = {"m05 (train)": {l: a for l, a in ev.load("train.xyz").items() if a.info.get("config_type") == "binding"},
        "m30 (test)": {l: a for l, a in ev.load("test.xyz").items() if a.info.get("config_type") == "binding"}}
out = {}
for name, path in models.items():
    calc = ev.calc_for(name, path); out[name] = {}
    for sn, fr in sets.items():
        Em, _ = ev.predict(calc, fr)
        r = {l: (Em[l] - float(a.info["REF_energy_raw"])) * 1000 for l, a in fr.items()}
        mean = float(np.mean(list(r.values()))); sd = float(np.std(list(r.values()), ddof=1))
        h = sn.split()[0]
        quart = {k: r[k] for k in (f"{h}_Sr136_vac", f"{h}_Sr136_novac", f"{h}_vac", f"{h}_host")}
        out[name][sn] = {"mean_meV": mean, "sd_meV": sd, "sr136_quartet_meV": quart,
                         "sr136_Eb_err_not_farref_meV": quart[f"{h}_Sr136_vac"] - quart[f"{h}_Sr136_novac"] - quart[f"{h}_vac"] + quart[f"{h}_host"]}
        print(f"{name:4s} {sn:12s} residual mean {mean:+9.1f}  SD over {len(r)} cells {sd:6.1f} meV | Sr136 quartet",
              " ".join(f"{v:+.1f}" for v in quart.values()), f"| E_b err (raw, not far-ref) {out[name][sn]['sr136_Eb_err_not_farref_meV']:+.1f}")
json.dump(out, open("diag_cancel.json", "w"), indent=1)

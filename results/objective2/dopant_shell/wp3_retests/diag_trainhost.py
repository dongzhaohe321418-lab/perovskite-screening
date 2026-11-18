"""D-V1a (post hoc, reported only): far-referenced E_b on the training host m05, raw F and E' (training labels)."""
import json, sys
sys.argv = [sys.argv[0]]
import eval_v1 as ev
P = "<project>"
models = {"ZS": f"<wp3_retests>/foundation/20231203mace128L1_epoch199model",
          "WP3": f"{P}/perovskite-screening/results/objective2/dopant_shell/wp3/run2/wp3.model",
          "V1": f"<wp3_retests>/run_v1/wp3v1.model", "V1b": f"<wp3_retests>/run_v1b/wp3v1b.model"}
tr = ev.load("train.xyz")
fr = {l: a for l, a in tr.items() if a.info.get("config_type") == "binding"}
Ed = {"raw": {l: float(a.info["REF_energy_raw"]) for l, a in fr.items()},
      "Eprime": {l: float(a.info["REF_energy"]) for l, a in fr.items()}}
out = {}
for name, path in models.items():
    Em, _ = ev.predict(ev.calc_for(name, path), fr)
    out[name] = {b: ev.sites(Em, Ed[b], "m05") for b in Ed}
json.dump(out, open("diag_trainhost_m05_v1b.json", "w"), indent=1)
for b in ("raw", "Eprime"):
    print("basis", b)
    for s in out["ZS"][b]:
        print("  ", s, "DFT %+.1f" % out["ZS"][b][s]["dft_meV"], " ".join("%s %+.1f" % (n, out[n][b][s]["model_meV"]) for n in models))

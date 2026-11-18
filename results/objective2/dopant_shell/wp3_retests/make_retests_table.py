#!/usr/bin/env python
"""Build wp3_retests_table.csv from the evaluator json files; values are copied, not recomputed or rounded.
Usage, from results/objective2/dopant_shell/wp3_retests/:  python -B make_retests_table.py . wp3_retests_table.csv"""
import csv, json, sys

src, out = sys.argv[1], sys.argv[2]
FILES = ("geval.json", "v1_eval.json", "v1b_eval.json", "v2_eval.json", "v3_eval.json")
J = {f: json.load(open(f"{src}/{f}")) for f in FILES}
SUMMARY = json.load(open(f"{src}/retests_summary.json"))
# model -> file the row is copied from; every other file holding the same model must hold identical values
ROWS = [("ZS", "v1_eval.json"), ("WP3", "v1_eval.json"), ("V1", "v1_eval.json"), ("V1b", "v1b_eval.json"),
        ("V2", "v2_eval.json"), ("V3", "v3_eval.json")]
KEYS = [("P3_force_rmse_46_frames_meV_per_A", "i_meVA"), ("P1_m30_Sr_Eb_rms_meV", "iii_m30_rms_Sr_meV"),
        ("m30_all_site_Eb_rms_meV", "iii_m30_rms_meV"), ("m30_GA_Eb_rms_meV", "iii_m30_rms_GA_meV"),
        ("m21_all_site_Eb_rms_meV", "iii_m21_rms_meV"), ("m21_Sr_Eb_rms_meV", "iii_m21_rms_Sr_meV"),
        ("m21_GA_Eb_rms_meV", "iii_m21_rms_GA_meV")]


def site(r, name):
    s = [v for v in r["iii_m30_sites"].values() if v["name"] == name]
    assert len(s) == 1, name
    return s[0]


def strip(r):                      # everything except the recorded model path
    return {k: v for k, v in r.items() if k != "model"}


with open(out, "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["model", "source_file"] + [k for k, _ in KEYS]
               + ["m30_Sr_hinge_Eb_model_meV", "m30_Sr_hinge_Eb_dft_meV", "m30_Sr_flank_Eb_model_meV",
                  "m30_Sr_flank_Eb_dft_meV"])
    for name, f in ROWS:
        r = J[f][name]
        for g, d in J.items():
            if g != f and name in d:
                assert strip(d[name]) == strip(r), (name, f, g)
        for k, v in SUMMARY[name].items():          # the side-by-side summary must hold the same values
            assert r[k] == v, (name, k)
        h, fl = site(r, "Sr_hinge"), site(r, "Sr_flank")
        w.writerow([name, f] + [repr(r[j]) for _, j in KEYS]
                   + [repr(h["model_meV"]), repr(h["dft_meV"]), repr(fl["model_meV"]), repr(fl["dft_meV"])])
        print(name, f, *(f"{r[j]:.2f}" for _, j in KEYS), f"{h['model_meV']:+.1f}", f"{h['dft_meV']:+.1f}",
              f"{fl['model_meV']:+.1f}", f"{fl['dft_meV']:+.1f}")

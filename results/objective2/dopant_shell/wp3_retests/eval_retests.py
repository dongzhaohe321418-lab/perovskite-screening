#!/usr/bin/env python
"""Relocatable evaluator for the WP3 fine-tuning re-tests (V1, V1b, V2, V3).

A copy of the local evaluator `eval_v1.py` (V1_PRESPEC_2026-11-15.md section 3, G-eval) in which the hard-coded
dataset location is replaced by command-line arguments. The computed quantities and the output format are unchanged.

Criterion-6 quantities of scripts/39 recomputed from the DFT labels stored in the WP3 dataset files (REF_energy_raw =
raw F, REF_forces), not from QE outputs:
  (i)   force RMSE over the 46 m30/m32 frames (5 images x 3 systems per host + the 16 m30 WP2c binding frames);
  (ii)  RMS of model - DFT paired dE_a over (m30, m32) x (GA, Sr), E_a = max_{i=2..4} E_i - E_0;
  (iii) far-referenced E_b error at the non-far sites of a host (scripts/37 eb order D+V, D, V, host), RMS all/Sr/GA.
Also reports the m21 (validation host) site errors.

Usage (from the repository root, for example):
  python -B eval_retests.py --dataset results/objective2/dopant_shell/wp3/dataset \
      --foundation FOUNDATION_FILE --out result.json ZS WP3=wp3.model V2=wp3v2.model

  --dataset DIR      directory holding test.xyz and valid.xyz (train.xyz is read only by load("train.xyz") callers)
  --foundation FILE  the MACE-MP-0 medium foundation file; it is the model of the name 'ZS'
  --selection FILE   wp2cde_selection.json (site and WP2c label selection). Default: DIR/wp2cde_selection.json if
                     that file exists, otherwise DIR/../../wp1_production/wp2cde_selection.json (repository layout)
  --out FILE         output json
  NAME=MODEL ...     models to evaluate. NAME 'ZS' loads the foundation file through mace_mp: write 'ZS' (uses
                     --foundation) or, as in eval_v1.py, 'ZS=FILE'. Every other NAME is loaded with MACECalculator
                     on the head "Default".

The "model" field of the output records each model path as typed; give relative paths if the json is to be public.
No path is built into this file. It trains nothing; it evaluates each model on 46 test and the m21 binding frames.
"""
import argparse, json, os, re, sys
import numpy as np
from ase.io import read

DS = None                                           # dataset directory, set by configure()
SEL = None                                          # content of wp2cde_selection.json, set by configure()
IMG = (0, 2, 3, 4, 6)                               # scripts/39 IMG
PAIRS = [("m30", "GA"), ("m30", "Sr"), ("m32", "GA"), ("m32", "Sr")]


def configure(dataset, selection=None):
    """Set the dataset directory and load the selection file (replaces the constants of eval_v1.py)."""
    global DS, SEL
    DS = dataset
    if selection is None:
        selection = os.path.join(dataset, "wp2cde_selection.json")
        if not os.path.isfile(selection):
            selection = os.path.join(dataset, os.pardir, os.pardir, "wp1_production", "wp2cde_selection.json")
    SEL = json.load(open(selection))
    return selection


def load(fn):
    out = {}
    for a in read(f"{DS}/{fn}", index=":"):
        out[a.info["label"]] = a
    return out


def calc_for(name, path):
    if name == "ZS":
        from mace.calculators import mace_mp
        return mace_mp(model=path, device="cpu", default_dtype="float64")
    from mace.calculators import MACECalculator
    c = MACECalculator(model_paths=[path], device="cpu", default_dtype="float64", head="Default")
    return c


def predict(calc, frames):
    E, F = {}, {}
    for l, a in frames.items():
        b = a.copy(); b.calc = calc
        E[l] = float(b.get_potential_energy()); F[l] = np.array(b.get_forces())
    return E, F


def rms(x):
    x = [v for v in x]; return float(np.sqrt(np.mean(np.square(x)))) if x else None


def Ea(E, h, s):
    l = {k: f"{h}_{s}_img{k}" for k in IMG}
    return max(E[l[i]] - E[l[0]] for i in (2, 3, 4)) * 1000


def eb(E, h, dop, j):
    return (E[f"{h}_{dop}{j}_vac"] - E[f"{h}_{dop}{j}_novac"] - E[f"{h}_vac"] + E[f"{h}_host"]) * 1000


def sites(Em, Ed, h):
    st = SEL[h]["sites"]; out = {}
    for dop in ("Sr", "GA"):
        far = st[f"{dop}_far"]["site"]
        fm, fd = eb(Em, h, dop, far), eb(Ed, h, dop, far)
        for n, v in st.items():
            if not n.startswith(dop + "_") or n == f"{dop}_far":
                continue
            j = v["site"]; m, d = eb(Em, h, dop, j) - fm, eb(Ed, h, dop, j) - fd
            out[f"{dop}{j}"] = {"name": n, "dopant": dop, "model_meV": m, "dft_meV": d, "error_meV": m - d,
                                "sign_agree": bool(np.sign(m) == np.sign(d))}
    return out


def parse_spec(spec, foundation):
    """NAME=MODEL -> (NAME, MODEL); a bare 'ZS' takes the --foundation file."""
    if "=" in spec:
        name, path = spec.split("=", 1)
        if name == "ZS" and foundation is not None and os.path.abspath(path) != os.path.abspath(foundation):
            sys.exit(f"ZS={path} differs from --foundation {foundation}: give one of them")
        return name, path
    if spec != "ZS":
        sys.exit(f"model argument '{spec}' is not NAME=MODEL (only 'ZS' may be given without a path)")
    if foundation is None:
        sys.exit("'ZS' needs --foundation FILE (or write ZS=FILE)")
    return spec, foundation


def main():
    ap = argparse.ArgumentParser(description="WP3 re-test evaluator (relocatable copy of eval_v1.py)")
    ap.add_argument("--dataset", required=True, help="directory holding test.xyz and valid.xyz")
    ap.add_argument("--foundation", default=None, help="foundation model file, used for the name 'ZS'")
    ap.add_argument("--selection", default=None, help="wp2cde_selection.json (default: see the module docstring)")
    ap.add_argument("--out", required=True); ap.add_argument("models", nargs="+", metavar="NAME=MODEL")
    a = ap.parse_args()
    specs = [parse_spec(s, a.foundation) for s in a.models]
    configure(a.dataset, a.selection)
    test, valid = load("test.xyz"), load("valid.xyz")
    f46 = [f"{h}_{s}_img{k}" for h in ("m30", "m32") for s in ("undoped", "GA", "Sr") for k in IMG] \
        + SEL["m30"]["wp2c_labels"]
    assert len(f46) == 46 and all(l in test for l in f46)
    m21 = [l for l, x in valid.items() if x.info.get("config_type") == "binding"]
    frames = {**{l: test[l] for l in f46}, **{l: valid[l] for l in m21}}
    Ed = {l: float(x.info["REF_energy_raw"]) for l, x in frames.items()}
    Fd = {l: np.array(x.arrays["REF_forces"]) for l, x in frames.items()}
    res = {}
    for name, path in specs:
        Em, Fm = predict(calc_for(name, path), frames)
        d = np.concatenate([(Fm[l] - Fd[l]).ravel() for l in f46])
        p = {f"{h}_{s}": (Ea(Em, h, s) - Ea(Em, h, "undoped")) - (Ea(Ed, h, s) - Ea(Ed, h, "undoped")) for h, s in PAIRS}
        s30, s21 = sites(Em, Ed, "m30"), sites(Em, Ed, "m21")
        r = {"model": path, "i_meVA": float(np.sqrt(np.mean(d ** 2))) * 1000, "ii_raw_rms_meV": rms(p.values()),
             "ii_raw_pairs_meV": p}
        for tag, s in (("m30", s30), ("m21", s21)):
            r[f"iii_{tag}_rms_meV"] = rms(x["error_meV"] for x in s.values())
            for dop in ("Sr", "GA"):
                r[f"iii_{tag}_rms_{dop}_meV"] = rms(x["error_meV"] for x in s.values() if x["dopant"] == dop)
            r[f"iii_{tag}_sites"] = s
        res[name] = r
        print(name, {k: round(v, 3) for k, v in r.items() if isinstance(v, float)}, flush=True)
    json.dump(res, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()

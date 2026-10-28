#!/usr/bin/env python
"""Compare zero-shot MACE-MP-0 with fixed-geometry DFT on the corpus NEB bands (PLAN WP2b/WP2e).

For every (host, system) band with DFT single points (scripts/30_qe_singlepoint.py), this
recomputes MACE on exactly the same frames and reports, at both levels:

  * E_a(path) = max over images {2,3,4} of E_i - E_0, only for complete bands {0,2,3,4,6}
    (pre-registered: script 32 as first committed, e1556a9; can be negative when image 0 is not a
    DFT minimum). Sensitivity: the corpus definition max over all sampled images - E_0 (>= 0).
    (forward barrier ALONG THE MACE PATH;
    at DFT level this is a fixed-path diagnostic, not a relaxed DFT barrier)
  * paired dE_a(dopant) = E_a(dopant) - E_a(undoped) in the same host
  * residual DFT force at the MACE minima (images 0 and 6): max and RMS per-atom norm
  * per-frame force RMSE MACE vs DFT, and the per-frame -TS smearing term

Energies are the free energy F ("!    total energy") consistently. Absolute MACE vs QE energies
are never compared (different pseudopotential references); only differences within one level.

    python scripts/32_dft_validation_analysis.py --dft <pulled dir> --bands <bands dir> --out <dir>
"""
import argparse, glob, gzip, json, os, re, csv
import numpy as np
from ase.io import read

RY = 13.605693122994  # eV
BOHR = 0.529177210903  # A


def read_text(path):
    """pw.x output as text; .gz (the archived raw outputs) is read transparently."""
    with (gzip.open(path, "rt", errors="replace") if path.endswith(".gz") else open(path, errors="replace")) as fh:
        return fh.read()


def parse_qe(path):
    txt = read_text(path)
    if "JOB DONE" not in txt:
        return None
    F = [float(x) for x in re.findall(r"^!\s+total energy\s+=\s+([-\d.]+)\s+Ry", txt, re.M)]
    TS = [float(x) for x in re.findall(r"smearing contrib\. \(-TS\)\s+=\s+([-\d.]+)\s+Ry", txt)]
    conv = "convergence has been achieved" in txt
    m = re.findall(r"Forces acting on atoms.*?\n\n(.*?)\n\n", txt, re.S)   # last block (relax outputs have many)
    forces = None
    if m:
        rows = re.findall(r"atom\s+\d+\s+type\s+\d+\s+force =\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)", m[-1])
        forces = np.array(rows, float) * RY / BOHR  # eV/A
    kp = re.search(r"number of k points=\s+(\d+)", txt)
    # sigma -> 0 estimate for Gaussian smearing: E0 = F + TS/2 = F - (-TS)/2 (review m1)
    E0 = (F[-1] - TS[-1] / 2.0) * RY if (F and TS) else None
    return {"F_eV": F[-1] * RY if F else None, "mTS_eV": TS[-1] * RY if TS else None, "E0_eV": E0,
            "converged": conv, "forces": forces, "nk": int(kp.group(1)) if kp else None}


REQUIRED_IMAGES = (0, 2, 3, 4, 6)        # PLAN amendment a; amendment g item 2: all must converge
WP2B_HOSTS = ["m05", "m06", "m08", "m12", "m15", "m20", "m21", "m30", "m32"]
BAND = 59.5                               # +/- equivalence band of the corpus TOST (meV)


def band_class(x):
    return int(x > BAND) - int(x < -BAND)   # -1 below, 0 inside, +1 above the band


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dft", required=True, help="dir with <label>.out files (any depth)")
    ap.add_argument("--bands", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--hosts", nargs="+", default=WP2B_HOSTS, help="pre-registered WP2b hosts")
    ap.add_argument("--threads", type=int, default=6)
    a = ap.parse_args()
    import torch; torch.set_num_threads(a.threads)
    from mace.calculators import mace_mp
    calc = mace_mp(model="medium", device="cpu", default_dtype="float64")

    outs = {}
    for f in glob.glob(os.path.join(a.dft, "**", "*.out"), recursive=True) + \
            glob.glob(os.path.join(a.dft, "**", "*.out.gz"), recursive=True):
        m = re.match(r"(m\d\d)_(undoped|GA|Sr)_img(\d)$", os.path.basename(f).removesuffix(".gz")[:-4])
        if m:
            outs[(m.group(1), m.group(2), int(m.group(3)))] = f
    bands, skipped = {}, []
    for (host, sysn, img), f in sorted(outs.items()):
        q = parse_qe(f)
        if q is None or not q["converged"] or q["forces"] is None:
            skipped.append(os.path.basename(f)); print(f"skip (not finished/converged): {f}"); continue
        frames = bands.setdefault((host, sysn), read(os.path.join(a.bands, f"band_{sysn}_{host}.extxyz"), ":"))
        at = frames[img].copy(); at.calc = calc
        Em = float(at.get_potential_energy()); Fm = at.get_forces()
        nrm = np.linalg.norm(q["forces"], axis=1)
        rec = {"host": host, "system": sysn, "image": img, "E_dft": q["F_eV"], "E0_dft": q["E0_eV"], "E_mace": Em,
               "mTS_meV": q["mTS_eV"] * 1000 if q["mTS_eV"] is not None else None, "nk": q["nk"],
               "force_rmse_eVA": float(np.sqrt(np.mean((Fm - q["forces"]) ** 2))),
               "dft_fmax_eVA": float(nrm.max()), "dft_frms_eVA": float(np.sqrt(np.mean(nrm ** 2)))}
        bands[(host, sysn, "rows")] = bands.get((host, sysn, "rows"), []) + [rec]

    per_band, frames_out, incomplete = [], [], []
    raw = {}                                  # unrounded E_a per band: differences never use rounded values
    for key, rows in [(k[:2], v) for k, v in bands.items() if len(k) == 3]:
        frames_out += rows
        imgs = {r["image"]: r for r in rows}
        missing = [i for i in REQUIRED_IMAGES if i not in imgs]
        if missing:                       # never compute E_a over a partial image set
            incomplete.append({"host": key[0], "system": key[1], "missing_images": missing}); continue
        inner = [2, 3, 4]                 # pre-registered definition (script 32 as first committed, e1556a9)
        rel = lambda k, i: imgs[i][k] - imgs[0][k]
        v = {"Ea_dft": max(rel("E_dft", i) for i in inner) * 1000,
             "Ea_mace": max(rel("E_mace", i) for i in inner) * 1000,
             "Ea_dft_E0": max(rel("E0_dft", i) for i in inner) * 1000,
             # sensitivity: the corpus definition (scripts/22: E.max() - E[0] over every image, so >= 0),
             # applied to the sampled images {0, 2, 3, 4, 6}
             "Ea_dft_corpusdef": max(rel("E_dft", i) for i in REQUIRED_IMAGES) * 1000,
             "Ea_mace_corpusdef": max(rel("E_mace", i) for i in REQUIRED_IMAGES) * 1000}
        raw[key] = v
        am = max(inner, key=lambda i: imgs[i]["E_dft"])
        # a DFT maximum at image 2 (4) that still rises from image 3 points to the unsampled image 1 (5):
        # the fixed-path DFT maximum is then not bracketed and E_a is a lower bound
        edge = am in (2, 4) and imgs[am]["E_dft"] > imgs[3]["E_dft"]
        per_band.append({"host": key[0], "system": key[1], "images": sorted(imgs),
                         "Ea_dft_meV": round(v["Ea_dft"], 3), "Ea_mace_meV": round(v["Ea_mace"], 3),
                         # sigma->0 estimate beside F (amendment c item 6 failed: dg 0.0025 moved E3-E0 by 4.9 meV)
                         "Ea_dft_E0_meV": round(v["Ea_dft_E0"], 3),
                         "Ea_dft_corpusdef_meV": round(v["Ea_dft_corpusdef"], 3),
                         "Ea_mace_corpusdef_meV": round(v["Ea_mace_corpusdef"], 3),
                         "argmax_dft": am, "argmax_mace": max(inner, key=lambda i: imgs[i]["E_mace"]),
                         "dft_max_unbracketed": bool(edge),
                         "minima_dft_fmax_eVA": [round(imgs[i]["dft_fmax_eVA"], 4) for i in (0, 6)],
                         "minima_dft_frms_eVA": [round(imgs[i]["dft_frms_eVA"], 4) for i in (0, 6)]})
    pairs, pb = [], {(b["host"], b["system"]): b for b in per_band}
    for (host, sysn), b in sorted(pb.items()):
        if sysn == "undoped" or (host, "undoped") not in pb:
            continue
        r, u = raw[(host, sysn)], raw[(host, "undoped")]
        dd, dm = r["Ea_dft"] - u["Ea_dft"], r["Ea_mace"] - u["Ea_mace"]
        dc, dmc = r["Ea_dft_corpusdef"] - u["Ea_dft_corpusdef"], r["Ea_mace_corpusdef"] - u["Ea_mace_corpusdef"]
        pairs.append({"host": host, "dopant": sysn, "dEa_dft_meV": round(dd, 3), "dEa_mace_meV": round(dm, 3),
                      "dEa_dft_E0_meV": round(r["Ea_dft_E0"] - u["Ea_dft_E0"], 3),
                      "error_meV": round(dm - dd, 3), "class_dft": band_class(dd), "class_mace": band_class(dm),
                      "dEa_dft_corpusdef_meV": round(dc, 3), "dEa_mace_corpusdef_meV": round(dmc, 3),
                      "error_corpusdef_meV": round(dmc - dc, 3),
                      "class_dft_corpusdef": band_class(dc), "class_mace_corpusdef": band_class(dmc),
                      "unbracketed": bool(b["dft_max_unbracketed"] or pb[(host, "undoped")]["dft_max_unbracketed"]),
                      "_dd": dd, "_dm": dm, "_dc": dc, "_dmc": dmc, "_d0": r["Ea_dft_E0"] - u["Ea_dft_E0"]})
    expected = [(h, d) for h in a.hosts for d in ("GA", "Sr")]
    have = {(p["host"], p["dopant"]) for p in pairs}
    err = np.array([p["_dm"] - p["_dd"] for p in pairs])
    rms = float(np.sqrt(np.mean(err ** 2))) if err.size else None
    flips = [{k: v for k, v in p.items() if not k.startswith("_")} for p in pairs if p["class_dft"] != p["class_mace"]]
    complete = all(e in have for e in expected)
    crit3 = {"n_pairs": len(pairs), "expected": len(expected),
             "missing_pairs": [f"{h}_{d}" for h, d in expected if (h, d) not in have],
             "rms_error_meV": rms, "mean_error_meV": float(err.mean()) if err.size else None,
             "rms_pass": bool(rms is not None and rms < 20.0), "flips": flips,
             "verdict": ("pass" if (rms < 20.0 and not flips) else "fail") if complete else "incomplete"}
    def gate(rows):
        ok = [r for r in rows if r["dft_frms_eVA"] < 0.05 and r["dft_fmax_eVA"] < 0.2]
        return {"n": len(rows), "n_pass": len(ok),
                "frms_range_eVA": [round(min(r["dft_frms_eVA"] for r in rows), 4), round(max(r["dft_frms_eVA"] for r in rows), 4)] if rows else None,
                "fmax_range_eVA": [round(min(r["dft_fmax_eVA"] for r in rows), 4), round(max(r["dft_fmax_eVA"] for r in rows), 4)] if rows else None}
    crit5 = {"gate": "RMS < 0.05 and max < 0.2 eV/A (PLAN criterion 5)",
             "minima_img0_img6": gate([r for r in frames_out if r["image"] in (0, 6)]),
             "saddle_img3": gate([r for r in frames_out if r["image"] == 3])}
    # criterion 3 consequence (PLAN): if RMS >= 20 meV the corpus equivalence result is re-stated at
    # DFT level from WP2b. Same test as the corpus (CORPUS108_RESULT.md): Student-t 95% CI of the
    # paired dE_a inside +/-59.5 meV, and TOST p; MACE on the same pairs alongside.
    from scipy import stats
    def eqv(x):
        x = np.asarray(x, float); n = x.size; m = float(x.mean()); s_ = float(x.std(ddof=1)); se = s_ / np.sqrt(n)
        h = float(stats.t.ppf(0.975, n - 1)) * se
        p_tost = max(float(stats.t.sf((m + BAND) / se, n - 1)), float(stats.t.cdf((m - BAND) / se, n - 1)))
        return {"n": n, "mean_meV": round(m, 2), "sd_meV": round(s_, 2), "ci95_meV": [round(m - h, 2), round(m + h, 2)],
                "ci_inside_band": bool(m - h > -BAND and m + h < BAND), "tost_p": round(p_tost, 4)}
    sel = lambda d, k: [p[k] for p in pairs if p["dopant"] == d]
    restate = {d: {"dft": eqv(sel(d, "_dd")), "dft_E0_sigma0": eqv(sel(d, "_d0")), "mace": eqv(sel(d, "_dm")),
                   "dft_corpusdef": eqv(sel(d, "_dc")), "mace_corpusdef": eqv(sel(d, "_dmc")),
                   "error_rms_meV": round(float(np.sqrt(np.mean((np.array(sel(d, "_dm")) - np.array(sel(d, "_dd"))) ** 2))), 2)}
               for d in ("GA", "Sr") if sum(p["dopant"] == d for p in pairs) > 2}
    ec = np.array([p["_dmc"] - p["_dc"] for p in pairs])
    crit3_corpusdef = {"note": "sensitivity only: E_a = max over all sampled images {0,2,3,4,6} - E_0 (scripts/22 definition)",
                       "rms_error_meV": float(np.sqrt(np.mean(ec ** 2))) if ec.size else None,
                       "mean_error_meV": float(ec.mean()) if ec.size else None,
                       "flips": [f"{p['host']}_{p['dopant']}" for p in pairs if p["class_dft_corpusdef"] != p["class_mace_corpusdef"]]}
    max_F_E0 = max((abs(p["_d0"] - p["_dd"]) for p in pairs), default=None)
    summary = {"n_frames": len(frames_out), "n_skipped_outputs": len(skipped), "n_complete_bands": len(per_band),
               "dft_level_restatement": restate, "criterion3_corpus_definition": crit3_corpusdef,
               "max_abs_dEa_E0_minus_F_meV": max_F_E0,
               "unbracketed_bands": [f"{b['host']}_{b['system']}" for b in per_band if b["dft_max_unbracketed"]],
               "incomplete_bands": incomplete, "criterion3": crit3, "criterion5": crit5,
               "force_rmse_median_eVA": float(np.median([r["force_rmse_eVA"] for r in frames_out])) if frames_out else None}
    os.makedirs(a.out, exist_ok=True)
    pairs = [{k: v for k, v in p.items() if not k.startswith("_")} for p in pairs]
    json.dump({"summary": summary, "skipped_outputs": skipped, "pairs": pairs, "bands": per_band, "frames": frames_out},
              open(os.path.join(a.out, "wp2b_validation.json"), "w"), indent=1)
    with open(os.path.join(a.out, "wp2b_frames.csv"), "w", newline="") as fh:
        if frames_out:
            w = csv.DictWriter(fh, fieldnames=list(frames_out[0].keys())); w.writeheader(); w.writerows(frames_out)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()

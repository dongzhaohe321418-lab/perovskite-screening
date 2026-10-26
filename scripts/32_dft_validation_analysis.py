#!/usr/bin/env python
"""Compare zero-shot MACE-MP-0 with fixed-geometry DFT on the corpus NEB bands (PLAN WP2b/WP2e).

For every (host, system) band with DFT single points (scripts/30_qe_singlepoint.py), this
recomputes MACE on exactly the same frames and reports, at both levels:

  * E_a(path) = max over images {2,3,4} of E_i - E_0, only for complete bands {0,2,3,4,6}
    (forward barrier ALONG THE MACE PATH;
    at DFT level this is a fixed-path diagnostic, not a relaxed DFT barrier)
  * paired dE_a(dopant) = E_a(dopant) - E_a(undoped) in the same host
  * residual DFT force at the MACE minima (images 0 and 6): max and RMS per-atom norm
  * per-frame force RMSE MACE vs DFT, and the per-frame -TS smearing term

Energies are the free energy F ("!    total energy") consistently. Absolute MACE vs QE energies
are never compared (different pseudopotential references); only differences within one level.

    python scripts/32_dft_validation_analysis.py --dft <pulled dir> --bands <bands dir> --out <dir>
"""
import argparse, glob, json, os, re, csv
import numpy as np
from ase.io import read

RY = 13.605693122994  # eV
BOHR = 0.529177210903  # A


def parse_qe(path):
    txt = open(path, errors="replace").read()
    if "JOB DONE" not in txt:
        return None
    F = [float(x) for x in re.findall(r"^!\s+total energy\s+=\s+([-\d.]+)\s+Ry", txt, re.M)]
    TS = [float(x) for x in re.findall(r"smearing contrib\. \(-TS\)\s+=\s+([-\d.]+)\s+Ry", txt)]
    conv = "convergence has been achieved" in txt
    m = re.search(r"Forces acting on atoms.*?\n\n(.*?)\n\n", txt, re.S)
    forces = None
    if m:
        rows = re.findall(r"atom\s+\d+\s+type\s+\d+\s+force =\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)", m.group(1))
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
    for f in glob.glob(os.path.join(a.dft, "**", "*.out"), recursive=True):
        m = re.match(r"(m\d\d)_(undoped|GA|Sr)_img(\d)$", os.path.basename(f)[:-4])
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
    for key, rows in [(k[:2], v) for k, v in bands.items() if len(k) == 3]:
        frames_out += rows
        imgs = {r["image"]: r for r in rows}
        missing = [i for i in REQUIRED_IMAGES if i not in imgs]
        if missing:                       # never compute E_a over a partial image set
            incomplete.append({"host": key[0], "system": key[1], "missing_images": missing}); continue
        e0d, e0m = imgs[0]["E_dft"], imgs[0]["E_mace"]
        inner = [2, 3, 4]
        per_band.append({"host": key[0], "system": key[1], "images": sorted(imgs),
                         "Ea_dft_meV": round(max(imgs[i]["E_dft"] - e0d for i in inner) * 1000, 2),
                         "Ea_mace_meV": round(max(imgs[i]["E_mace"] - e0m for i in inner) * 1000, 2),
                         # sigma->0 estimate beside F (amendment c item 6 failed: dg 0.0025 moved E3-E0 by 4.9 meV)
                         "Ea_dft_E0_meV": round(max(imgs[i]["E0_dft"] - imgs[0]["E0_dft"] for i in inner) * 1000, 2),
                         "argmax_dft": max(inner, key=lambda i: imgs[i]["E_dft"]),
                         "argmax_mace": max(inner, key=lambda i: imgs[i]["E_mace"]),
                         "minima_dft_fmax_eVA": [round(imgs[i]["dft_fmax_eVA"], 4) for i in (0, 6)],
                         "minima_dft_frms_eVA": [round(imgs[i]["dft_frms_eVA"], 4) for i in (0, 6)]})
    pairs, pb = [], {(b["host"], b["system"]): b for b in per_band}
    for (host, sysn), b in sorted(pb.items()):
        if sysn == "undoped" or (host, "undoped") not in pb:
            continue
        u = pb[(host, "undoped")]
        dd, dm = b["Ea_dft_meV"] - u["Ea_dft_meV"], b["Ea_mace_meV"] - u["Ea_mace_meV"]
        pairs.append({"host": host, "dopant": sysn, "dEa_dft_meV": round(dd, 2), "dEa_mace_meV": round(dm, 2),
                      "dEa_dft_E0_meV": round(b["Ea_dft_E0_meV"] - u["Ea_dft_E0_meV"], 2),
                      "error_meV": round(dm - dd, 2), "class_dft": band_class(dd), "class_mace": band_class(dm)})
    expected = [(h, d) for h in a.hosts for d in ("GA", "Sr")]
    have = {(p["host"], p["dopant"]) for p in pairs}
    err = np.array([p["error_meV"] for p in pairs])
    rms = float(np.sqrt(np.mean(err ** 2))) if err.size else None
    flips = [p for p in pairs if p["class_dft"] != p["class_mace"]]
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
    restate = {d: {"dft": eqv([p["dEa_dft_meV"] for p in pairs if p["dopant"] == d]),
                   "dft_E0_sigma0": eqv([p["dEa_dft_E0_meV"] for p in pairs if p["dopant"] == d]),
                   "mace": eqv([p["dEa_mace_meV"] for p in pairs if p["dopant"] == d]),
                   "error_rms_meV": round(float(np.sqrt(np.mean([p["error_meV"] ** 2 for p in pairs if p["dopant"] == d]))), 2)}
               for d in ("GA", "Sr") if sum(p["dopant"] == d for p in pairs) > 2}
    summary = {"n_frames": len(frames_out), "n_skipped_outputs": len(skipped), "n_complete_bands": len(per_band),
               "dft_level_restatement": restate,
               "incomplete_bands": incomplete, "criterion3": crit3, "criterion5": crit5,
               "force_rmse_median_eVA": float(np.median([r["force_rmse_eVA"] for r in frames_out])) if frames_out else None}
    os.makedirs(a.out, exist_ok=True)
    json.dump({"summary": summary, "skipped_outputs": skipped, "pairs": pairs, "bands": per_band, "frames": frames_out},
              open(os.path.join(a.out, "wp2b_validation.json"), "w"), indent=1)
    with open(os.path.join(a.out, "wp2b_frames.csv"), "w", newline="") as fh:
        if frames_out:
            w = csv.DictWriter(fh, fieldnames=list(frames_out[0].keys())); w.writeheader(); w.writerows(frames_out)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()

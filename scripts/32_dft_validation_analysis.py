#!/usr/bin/env python
"""Compare zero-shot MACE-MP-0 with fixed-geometry DFT on the corpus NEB bands (PLAN WP2b/WP2e).

For every (host, system) band with DFT single points (scripts/30_qe_singlepoint.py), this
recomputes MACE on exactly the same frames and reports, at both levels:

  * E_a(path) = max over the computed images of E_i - E_0  (forward barrier ALONG THE MACE PATH;
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dft", required=True, help="dir with <label>.out files (any depth)")
    ap.add_argument("--bands", required=True)
    ap.add_argument("--out", required=True)
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
    bands = {}
    for (host, sysn, img), f in sorted(outs.items()):
        q = parse_qe(f)
        if q is None or not q["converged"]:
            print(f"skip (not finished/converged): {f}"); continue
        frames = bands.setdefault((host, sysn), read(os.path.join(a.bands, f"band_{sysn}_{host}.extxyz"), ":"))
        at = frames[img].copy(); at.calc = calc
        Em = float(at.get_potential_energy()); Fm = at.get_forces()
        rmse = float(np.sqrt(np.mean((Fm - q["forces"]) ** 2))) if q["forces"] is not None else None
        rec = {"host": host, "system": sysn, "image": img, "E_dft": q["F_eV"], "E_mace": Em,
               "mTS_meV": q["mTS_eV"] * 1000 if q["mTS_eV"] is not None else None, "nk": q["nk"],
               "force_rmse_eVA": rmse,
               "dft_fmax_eVA": float(np.linalg.norm(q["forces"], axis=1).max()),
               "dft_frms_eVA": float(np.sqrt(np.mean(np.sum(q["forces"] ** 2, axis=1))))}
        bands[(host, sysn, "rows")] = bands.get((host, sysn, "rows"), []) + [rec]

    per_band, frames_out = [], []
    for key, rows in [(k[:2], v) for k, v in bands.items() if len(k) == 3]:
        frames_out += rows
        imgs = {r["image"]: r for r in rows}
        if 0 not in imgs or len(imgs) < 3:
            continue
        e0d, e0m = imgs[0]["E_dft"], imgs[0]["E_mace"]
        inner = [i for i in imgs if i not in (0, 6)]
        Ead = max(imgs[i]["E_dft"] - e0d for i in inner) * 1000
        Eam = max(imgs[i]["E_mace"] - e0m for i in inner) * 1000
        per_band.append({"host": key[0], "system": key[1], "images": sorted(imgs),
                         "Ea_dft_meV": round(Ead, 2), "Ea_mace_meV": round(Eam, 2),
                         "argmax_dft": max(inner, key=lambda i: imgs[i]["E_dft"]),
                         "argmax_mace": max(inner, key=lambda i: imgs[i]["E_mace"]),
                         "minima_dft_fmax_eVA": [round(imgs[i]["dft_fmax_eVA"], 4) for i in (0, 6) if i in imgs],
                         "minima_dft_frms_eVA": [round(imgs[i]["dft_frms_eVA"], 4) for i in (0, 6) if i in imgs]})
    pairs = []
    pb = {(b["host"], b["system"]): b for b in per_band}
    for (host, sysn), b in pb.items():
        if sysn == "undoped" or (host, "undoped") not in pb:
            continue
        u = pb[(host, "undoped")]
        dd, dm = b["Ea_dft_meV"] - u["Ea_dft_meV"], b["Ea_mace_meV"] - u["Ea_mace_meV"]
        pairs.append({"host": host, "dopant": sysn, "dEa_dft_meV": round(dd, 2), "dEa_mace_meV": round(dm, 2),
                      "error_meV": round(dm - dd, 2)})
    err = np.array([p["error_meV"] for p in pairs]) if pairs else np.array([])
    summary = {"n_frames": len(frames_out), "n_bands": len(per_band), "n_pairs": len(pairs),
               "dEa_error_rms_meV": float(np.sqrt(np.mean(err ** 2))) if err.size else None,
               "dEa_error_mean_meV": float(err.mean()) if err.size else None,
               "sign_or_band_flips": [p for p in pairs if (abs(p["dEa_dft_meV"]) > 59.5) != (abs(p["dEa_mace_meV"]) > 59.5)],
               "force_rmse_median_eVA": float(np.median([r["force_rmse_eVA"] for r in frames_out])) if frames_out else None}
    os.makedirs(a.out, exist_ok=True)
    json.dump({"summary": summary, "pairs": pairs, "bands": per_band, "frames": frames_out},
              open(os.path.join(a.out, "wp2b_validation.json"), "w"), indent=1)
    with open(os.path.join(a.out, "wp2b_frames.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(frames_out[0].keys())) if frames_out else None
        if w:
            w.writeheader(); w.writerows(frames_out)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()

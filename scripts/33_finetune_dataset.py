#!/usr/bin/env python
"""Build the MACE fine-tuning dataset from the DFT single points (PLAN WP3), split by HOST.

Every QE output (scripts/30, plain PBE, R-point) is paired with the exact frame it was run on
and written to extxyz with info['REF_energy'] (free energy F, eV) and arrays['REF_forces']
(eV/A). Frames are split by host configuration, never by frame, so the test set measures
transfer to unseen FA-orientation configurations: a frame-level split would leak (images of one
band share almost all coordinates).

Energy reference. QE pslibrary energies and MACE-MP-0 energies differ by large per-element
constants, and the foundation model's E0s are fitted constants (H -3.67 eV), not isolated-atom
energies. In this dataset composition varies only along three directions: -I (vacancy),
FA->GA (+N +H) and Pb->Sr, on top of one fixed FA19Cs1Pb20I60 baseline. So only four
combinations of per-element offsets are identifiable. They are fitted on the TRAINING frames
by least squares of (E_QE - E_MACE0) against those four composition coordinates, and assigned
to I, N, Sr and Pb (C, H, Cs offsets fixed to 0). Within this compositional family the
assignment is exact; outside it the offsets are meaningless and the model must not be used.
E0_new = E0_foundation + offset; the network then only learns interaction-energy residuals.

    python scripts/33_finetune_dataset.py --dft <dir> --frames <bands> <v2 dir> <wp3 frames> \
        --out <dir> --test-hosts m30 m32 --valid-hosts m21
"""
import argparse, glob, json, os, re
import numpy as np
from ase.io import read, write
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("a32", os.path.join(HERE, "32_dft_validation_analysis.py"))
a32 = importlib.util.module_from_spec(_s); _s.loader.exec_module(a32)
Z = {"H": 1, "C": 6, "N": 7, "Sr": 38, "I": 53, "Cs": 55, "Pb": 82}


def find(frames_dirs, name):
    hits = [os.path.join(d, name) for d in frames_dirs if os.path.exists(os.path.join(d, name))]
    assert len(hits) <= 1, f"{name} found in several frame dirs: {hits}"
    return hits[0] if hits else None


def collect(dft_dir, frames_dirs):
    """Atoms with REF data for band frames, WP2c binding frames and WP3 off-equilibrium frames."""
    out = []
    for f in sorted(glob.glob(os.path.join(dft_dir, "**", "*.out"), recursive=True)):
        lab = os.path.basename(f)[:-4]
        m = re.match(r"(m\d\d)_(undoped|GA|Sr)_img(\d)$", lab)
        if not m:
            continue
        q = a32.parse_qe(f)
        if q is None or not q["converged"] or q["forces"] is None:
            continue
        at = read(find(frames_dirs, f"band_{m.group(2)}_{m.group(1)}.extxyz"), index=int(m.group(3)))
        at = at.copy(); at.calc = None; at.set_tags([0] * len(at))
        assert len(at) == len(q["forces"]), lab
        at.info.update({"REF_energy": q["F_eV"], "host": m.group(1), "system": m.group(2),
                        "image": int(m.group(3)), "label": lab, "config_type": f"band_{m.group(2)}",
                        "mTS_eV": q["mTS_eV"]})
        at.arrays["REF_forces"] = q["forces"]
        out.append(at)
    # WP2c binding-energy frames: QE label = <host>_<kind>, frame = 29's relaxed extxyz (review M4)
    for f in sorted(glob.glob(os.path.join(dft_dir, "**", "*.out"), recursive=True)):
        lab = os.path.basename(f)[:-4]
        m = re.match(r"(m\d\d)_(host|vac|(?:Sr|GA)\d+_(?:novac|vac))$", lab)
        if not m:
            continue
        q = a32.parse_qe(f)
        if q is None or not q["converged"] or q["forces"] is None:
            continue
        fx = find(frames_dirs, f"{m.group(1)}_{m.group(2)}_relaxed.extxyz")
        if fx is None:
            continue
        at = read(fx); at = at.copy(); at.calc = None; at.set_tags([0] * len(at))
        assert len(at) == len(q["forces"]), lab
        at.info.update({"REF_energy": q["F_eV"], "host": m.group(1), "system": m.group(2), "image": -1,
                        "label": lab, "config_type": "binding", "mTS_eV": q["mTS_eV"]})
        at.arrays["REF_forces"] = q["forces"]
        out.append(at)
    # WP3 off-equilibrium frames (scripts/35): QE label = frame label = <host>_<system>_<kind>
    for f in sorted(glob.glob(os.path.join(dft_dir, "**", "*.out"), recursive=True)):
        lab = os.path.basename(f)[:-4]
        m = re.match(r"(m\d\d)_(undoped|GA|Sr|pristine)_(rat05f|rat10f|md300|md450)$", lab)
        if not m:
            continue
        q = a32.parse_qe(f)
        fx = find(frames_dirs, f"{lab}.extxyz")
        if q is None or not q["converged"] or q["forces"] is None or fx is None:
            continue
        at = read(fx); at = at.copy(); at.calc = None; at.set_tags([0] * len(at))
        assert len(at) == len(q["forces"]), lab
        ctype = at.info.get("config_type", "md" if m.group(3).startswith("md") else "rattle")
        at.info = {"REF_energy": q["F_eV"], "host": m.group(1), "system": m.group(2), "image": -1,
                   "label": lab, "config_type": ctype, "mTS_eV": q["mTS_eV"]}
        at.arrays["REF_forces"] = q["forces"]
        out.append(at)
    return out


def comp_coords(at):
    s = at.get_chemical_symbols()
    n = {e: s.count(e) for e in Z}
    # baseline FA19Cs1Pb20I60: I deficit (vacancy), GA count (extra N), Sr count
    return np.array([1.0, n["I"] - 60, n["N"] - 38, n["Sr"]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dft", required=True)
    ap.add_argument("--frames", nargs="+", required=True, help="dirs with band, WP2c and WP3 frames")
    ap.add_argument("--out", required=True)
    ap.add_argument("--test-hosts", nargs="+", required=True)
    ap.add_argument("--valid-hosts", nargs="+", required=True)
    a = ap.parse_args()
    frames = collect(a.dft, a.frames)
    split = lambda at: "test" if at.info["host"] in a.test_hosts else ("valid" if at.info["host"] in a.valid_hosts else "train")
    sets = {k: [f for f in frames if split(f) == k] for k in ("train", "valid", "test")}

    import torch, warnings; warnings.filterwarnings("ignore"); torch.set_num_threads(6)
    from mace.calculators import mace_mp
    calc = mace_mp(model="medium", device="cpu", default_dtype="float64")
    model = calc.models[0]
    e0f = {int(z): float(e) for z, e in zip(model.atomic_numbers.numpy().ravel(),
                                            model.atomic_energies_fn.atomic_energies.detach().numpy().ravel())}
    X, y = [], []
    for at in sets["train"]:
        b = at.copy(); b.calc = calc
        X.append(comp_coords(at)); y.append(at.info["REF_energy"] - b.get_potential_energy())
    X, y = np.array(X), np.array(y)
    coef, res, rank, _ = np.linalg.lstsq(X, y, rcond=None)
    # All band frames have dI = -1, so const and dI are collinear until vacancy-free frames
    # (host, D_j from WP2c) are in the training set; refuse an arbitrary split (review M3).
    assert rank == X.shape[1], f"offset fit rank {rank} < {X.shape[1]}: add dI=0 frames (host/D_j) to train"
    # Per-element offsets o_e apply to EVERY atom of element e. With o_C = o_H = o_Cs = 0 and
    # n_I = 60+dI, n_N = 38+dN (GA also adds one H, whose offset is 0), n_Pb = 20-nSr, n_Sr = nSr:
    #   sum_e n_e o_e = (60+dI) o_I + (38+dN) o_N + (20-nSr) o_Pb + nSr o_Sr
    # matches c0 + c1 dI + c2 dN + c3 nSr exactly when
    o_I, o_N = coef[1], coef[2]
    o_Pb = (coef[0] - 60 * o_I - 38 * o_N) / 20.0
    o_Sr = coef[3] + o_Pb
    off = {"I": o_I, "N": o_N, "Pb": o_Pb, "Sr": o_Sr, "C": 0.0, "H": 0.0, "Cs": 0.0}
    for at in frames:   # exactness check of the assignment on every frame
        s_ = at.get_chemical_symbols()
        assert abs(sum(off[e] for e in s_) - comp_coords(at) @ coef) < 1e-6
    e0 = {Z[e]: e0f[Z[e]] + off[e] for e in Z}
    resid = y - X @ coef
    os.makedirs(a.out, exist_ok=True)
    for k, v in sets.items():
        write(os.path.join(a.out, f"{k}.xyz"), v, format="extxyz")
    meta = {"n": {k: len(v) for k, v in sets.items()},
            "hosts": {k: sorted({f.info['host'] for f in v}) for k, v in sets.items()},
            "E0s": {str(k): v for k, v in e0.items()},
            "offset_fit": {"coords": ["const(FA19Cs1Pb20I60)", "dI", "dN(GA)", "nSr"],
                           "coef_eV": coef.tolist(), "rank": int(rank),
                           "train_residual_rms_meV": float(np.sqrt(np.mean(resid ** 2)) * 1000)},
            "note": "E0s valid only within the FA19Cs1Pb20I60(-I)(+GA)(+Sr) family."}
    json.dump(meta, open(os.path.join(a.out, "dataset_meta.json"), "w"), indent=1)
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()

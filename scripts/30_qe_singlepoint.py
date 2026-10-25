#!/usr/bin/env python
"""Write a fixed-geometry pw.x SCF single point for a MACE-relaxed FA-host frame.

Purpose: DFT validation and fine-tuning data for the MACE-MP-0 results of Objective 2.

Theory level -- deliberately PLAIN PBE (no D3), because MACE-MP-0 was trained on Materials
Project PBE(+U) data without dispersion; validating or fine-tuning it against PBE+D3 would
mix a dispersion term into what is meant to be a test of the potential itself. Dispersion is
geometry-only and can be added afterwards. This differs from the Objective-1 production
fingerprint (PBE+D3(BJ)); the two must not be compared directly (standing rule 1).

    ecutwfc 50 / ecutrho 400 Ry (pslibrary 1.0.0 US; max suggested 46 / 326 Ry), Gamma point,
    Gaussian smearing 0.005 Ry, nspin = 1, conv_thr 1e-8 Ry, forces printed (tprnfor).

nspin = 1 for the odd-electron neutral V_I cells follows the Objective-1 finding that the
neutral vacancy electron is delocalised (CBM-like) with no competing magnetic solution
(RESULTS_INDEX.md Q3). Charge-neutral cells only: MACE is charge-agnostic.

    python scripts/30_qe_singlepoint.py frame.extxyz[@index] --label m30_undoped_img0 --out jobs/dir
"""
import argparse, json, os, hashlib
from ase.io import read
from ase.io.espresso import write_espresso_in

PSEUDO = {"Pb": "Pb.pbe-dn-rrkjus_psl.1.0.0.UPF", "I": "I.pbe-n-rrkjus_psl.1.0.0.UPF",
          "Cs": "Cs.pbe-spn-rrkjus_psl.1.0.0.UPF", "C": "C.pbe-n-rrkjus_psl.1.0.0.UPF",
          "N": "N.pbe-n-rrkjus_psl.1.0.0.UPF", "H": "H.pbe-rrkjus_psl.1.0.0.UPF",
          "Sr": "Sr.pbe-spn-rrkjus_psl.1.0.0.UPF"}

FINGERPRINT = {"functional": "PBE (no D3)", "ecutwfc": 50.0, "ecutrho": 400.0, "kpts": "gamma",
               "smearing": "gaussian", "degauss": 0.005, "nspin": 1, "conv_thr": 1e-8,
               "pseudos": "pslibrary 1.0.0 US (Cs spn, Pb dn, Sr spn)"}


KMODES = {"gamma": dict(kpts=None),                         # Gamma trick; misses R in this cell
          "R": dict(kpts=(1, 1, 1), koffset=(1, 1, 1)),     # single k at supercell (1/2,1/2,1/2) = folded R
          "mp222": dict(kpts=(2, 2, 2), koffset=(0, 0, 0))} # Gamma-centred 2x2x2, contains Gamma and R


def write_input(atoms, label, outdir, kmode="gamma", calc="scf"):
    os.makedirs(outdir, exist_ok=True)
    input_data = {
        "control": {"calculation": calc, "prefix": label, "pseudo_dir": "/data/pseudo",
                    "outdir": "./tmp", "tprnfor": True, "tstress": False, "disk_io": "none",
                    "verbosity": "low"},
        "system": {"ecutwfc": 50.0, "ecutrho": 400.0, "occupations": "smearing",
                   "smearing": "gaussian", "degauss": 0.005, "nspin": 1, "nosym": True},
        "electrons": {"conv_thr": 1e-8, "mixing_beta": 0.3, "electron_maxstep": 200},
    }
    if calc == "relax":   # WP2e: fixed-cell DFT relaxation, same force target as the MACE corpus
        input_data["control"].update({"forc_conv_thr": 7.8e-4, "etot_conv_thr": 1e-5, "nstep": 300})
        input_data["ions"] = {"ion_dynamics": "bfgs"}
    species = sorted(set(atoms.get_chemical_symbols()))
    pp = {s: PSEUDO[s] for s in species}
    path = os.path.join(outdir, f"{label}.in")
    with open(path, "w") as fd:
        write_espresso_in(fd, atoms, input_data=input_data, pseudopotentials=pp, **KMODES[kmode])
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frame", help="extxyz file, optionally file@index")
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--calc", choices=["scf", "relax"], default="scf",
                    help="relax = fixed-cell BFGS to 0.02 eV/A (7.8e-4 Ry/bohr), PLAN WP2e")
    ap.add_argument("--kmode", choices=sorted(KMODES), default="gamma",
                    help="k-sampling; in the det-20 FA cell the primitive R point folds to (1/2,1/2,1/2), "
                         "not Gamma, so 'gamma' misses the band edges (2026-10-25 review DFT-1)")
    a = ap.parse_args()
    fn, _, idx = a.frame.partition("@")
    atoms = read(fn, index=int(idx) if idx else -1)
    atoms.set_tags([0] * len(atoms))
    path = write_input(atoms, a.label, a.out, a.kmode, a.calc)
    meta = {"label": a.label, "source": a.frame, "natoms": len(atoms),
            "formula": atoms.get_chemical_formula(), "fingerprint": {**FINGERPRINT, "kpts": a.kmode, "calculation": a.calc},
            "input_sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()}
    json.dump(meta, open(os.path.join(a.out, f"{a.label}.meta.json"), "w"), indent=1)
    print(path, meta["formula"], meta["input_sha256"][:12])


if __name__ == "__main__":
    main()

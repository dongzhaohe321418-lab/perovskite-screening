#!/usr/bin/env python
"""Isolated-atom reference energies (E0s) at the scripts/30 DFT fingerprint, for MACE fine-tuning.

Why: QE pslibrary-US total energies sit on a different absolute reference from the VASP-PAW
energies MACE-MP-0 was trained on, by a large per-element constant. Every FA-host frame has
nearly the same stoichiometry, so fitting per-element E0s from those frames is ill-conditioned
(2026-10-25 design review, DFT-3). Isolated-atom energies computed with the same pseudopotentials
and cutoffs give the per-element reference directly.

Each atom: cubic box (default 16 A), Gamma point, ecutwfc 50 / ecutrho 400 Ry, spin-polarised
with the free-atom ground-state moment fixed (tot_magnetization), small Gaussian smearing,
symmetry off so the open shell may break spherical symmetry. Scalar-relativistic, no SOC
(as in the pseudopotentials).

    python scripts/31_qe_atom_e0.py --out jobs/e0
"""
import argparse, os, json
from ase import Atoms
from ase.io.espresso import write_espresso_in
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("s30", os.path.join(HERE, "30_qe_singlepoint.py"))
s30 = importlib.util.module_from_spec(_s); _s.loader.exec_module(s30)

# free-atom ground-state number of unpaired electrons (Hund), scalar-relativistic
MOMENT = {"H": 1, "C": 2, "N": 3, "Cs": 1, "Sr": 0, "Pb": 2, "I": 1}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--box", type=float, default=16.0)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for el, mom in MOMENT.items():
        # off-centre and slightly non-cubic box so no accidental symmetry pins the open shell
        at = Atoms(el, positions=[[a.box / 2 + 0.11, a.box / 2 + 0.07, a.box / 2 + 0.03]],
                   cell=[a.box, a.box * 1.02, a.box * 1.04], pbc=True)
        # seed only (QE needs -1..1); the moment itself is fixed by tot_magnetization
        at.set_initial_magnetic_moments([0.5 if mom else 0.0])
        system = {"ecutwfc": 50.0, "ecutrho": 400.0, "occupations": "smearing", "smearing": "gaussian",
                  "degauss": 0.002, "nosym": True}
        if mom:
            system.update({"nspin": 2, "tot_magnetization": mom})
        else:
            system.update({"nspin": 1})
        inp = {"control": {"calculation": "scf", "prefix": f"atom_{el}", "pseudo_dir": "/data/pseudo",
                           "outdir": "./tmp", "disk_io": "none"},
               "system": system,
               "electrons": {"conv_thr": 1e-8, "mixing_beta": 0.2, "electron_maxstep": 400}}
        path = os.path.join(a.out, f"atom_{el}.in")
        with open(path, "w") as fd:
            write_espresso_in(fd, at, input_data=inp, pseudopotentials={el: s30.PSEUDO[el]}, kpts=None)
        json.dump({"element": el, "unpaired": mom, "box_A": [a.box, a.box * 1.02, a.box * 1.04],
                   "fingerprint": {**s30.FINGERPRINT, "kpts": "gamma (isolated atom)", "degauss": 0.002,
                                   "nspin": 2 if mom else 1}},
                  open(os.path.join(a.out, f"atom_{el}.meta.json"), "w"), indent=1)
        print(path)


if __name__ == "__main__":
    main()

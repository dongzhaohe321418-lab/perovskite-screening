#!/usr/bin/env python3
"""Generate a Quantum ESPRESSO neb.x input for the charged V_I migration path
(Stage 2.2 explore / Stage 2.3 full CI-NEB).

neb.x input format (distinct from pw.x; verified against QE INPUT_NEB v7.x):

  BEGIN
  BEGIN_PATH_INPUT
  &PATH
     string_method='neb', nstep_path, num_of_images (INCLUDES endpoints),
     CI_scheme, opt_scheme, path_thr, minimum_image=.true., first_last_opt=.false.
  /
  END_PATH_INPUT
  BEGIN_ENGINE_INPUT
  &CONTROL ... / &SYSTEM ... / &ELECTRONS ...
  ATOMIC_SPECIES
  BEGIN_POSITIONS
  FIRST_IMAGE / ATOMIC_POSITIONS ...
  LAST_IMAGE  / ATOMIC_POSITIONS ...
  END_POSITIONS
  K_POINTS ... / CELL_PARAMETERS ...
  END_ENGINE_INPUT
  END

Endpoints are the SEPARATELY-RELAXED q0/q1 initial & final (Stage 2.1). Identical
atom ordering + identical cell between endpoints is asserted. Theory level (D3, spin,
nosym, ecut/k/degauss) is passed in to match the locked production setting.

Usage:
  python 11_generate_neb_input.py --initial relax_q1_initial.xyz \
      --final relax_q1_final.xyz --charge 1 --nspin 1 --num-images 5 \
      --ci-scheme no-CI --path-thr 0.1 --out q1_explore.neb.in
"""
import argparse
from pathlib import Path
import numpy as np
from ase.io import read

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PSEUDO = "$HOME/pseudo"
# pslibrary 1.0.0 US scalar-rel PBE (same as scripts/05)
PSEUDO = {"Cs": ("Cs.pbe-spn-rrkjus_psl.1.0.0.UPF", 132.905),
          "Pb": ("Pb.pbe-dn-rrkjus_psl.1.0.0.UPF", 207.2),
          "I":  ("I.pbe-n-rrkjus_psl.1.0.0.UPF", 126.904)}


def _atomic_positions_block(atoms):
    s = "ATOMIC_POSITIONS angstrom\n"
    for sym, p in zip(atoms.get_chemical_symbols(), atoms.positions):
        s += f"  {sym:3s} {p[0]:18.12f} {p[1]:18.12f} {p[2]:18.12f}\n"
    return s


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--initial", required=True)
    p.add_argument("--final", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--charge", type=int, default=0)
    p.add_argument("--nspin", type=int, default=1)
    p.add_argument("--tot-magnetization", type=float, default=None)
    p.add_argument("--num-images", type=int, default=5, help="INCLUDES endpoints")
    p.add_argument("--ci-scheme", default="auto", choices=["no-CI", "auto", "manual"])
    p.add_argument("--path-thr", type=float, default=0.05, help="eV/A")
    p.add_argument("--nstep-path", type=int, default=100)
    p.add_argument("--ecutwfc", type=float, default=50.0)
    p.add_argument("--ecutrho", type=float, default=400.0)
    p.add_argument("--degauss", type=float, default=0.01)
    p.add_argument("--conv-thr", default="1e-6",
                   help="SCF threshold: 1e-6 explore / 1e-8 production (locked protocol)")
    p.add_argument("--kpoints", default="1,1,1")
    p.add_argument("--d3", action="store_true", default=True)
    p.add_argument("--no-d3", dest="d3", action="store_false")
    p.add_argument("--pseudo-dir", default=DEFAULT_PSEUDO)
    args = p.parse_args()

    ini = read(args.initial)
    fin = read(args.final)
    # hard requirements for a valid migration NEB
    assert ini.get_chemical_symbols() == fin.get_chemical_symbols(), \
        "endpoint atom ORDERING mismatch — NEB requires identical ordering"
    assert np.allclose(ini.cell.array, fin.cell.array, atol=1e-6), \
        "endpoint CELL mismatch — fixed-cell NEB requires identical cells"
    kp = tuple(int(x) for x in args.kpoints.split(","))

    species = []
    for s in ini.get_chemical_symbols():
        if s not in species:
            species.append(s)
    nat, ntyp = len(ini), len(species)

    L = []
    L.append("BEGIN")
    L.append("BEGIN_PATH_INPUT")
    L.append("&PATH")
    L.append("   string_method = 'neb'")
    L.append(f"   nstep_path = {args.nstep_path}")
    L.append("   opt_scheme = 'broyden'")
    L.append(f"   num_of_images = {args.num_images}")
    L.append(f"   CI_scheme = '{args.ci_scheme}'")
    L.append(f"   path_thr = {args.path_thr:.3f}")   # eV/A
    L.append("   ds = 1.0")
    L.append("   k_max = 0.3")
    L.append("   k_min = 0.2")
    L.append("   minimum_image = .true.")            # MIC path across PBC
    L.append("   first_last_opt = .false.")          # endpoints pre-relaxed in Stage 2.1
    L.append("/")
    L.append("END_PATH_INPUT")
    L.append("BEGIN_ENGINE_INPUT")
    L.append("&CONTROL")
    # neb.x drives ionic motion via its own PATH optimizer; the engine (pw.x) does a
    # single-point SCF-with-forces per image. Must be 'scf' — 'relax' makes pw.x expect
    # an &IONS namelist that the NEB engine block doesn't provide, and the parser then
    # misreads the trailing CELL_PARAMETERS rows as bad &ions lines (QE read_namelists err).
    L.append("   calculation = 'scf'")
    L.append("   prefix = 'neb'")
    L.append("   tprnfor = .true.")
    L.append("   tstress = .false.")
    L.append(f"   pseudo_dir = '{args.pseudo_dir}'")
    L.append("   outdir = './out'")
    L.append("/")
    L.append("&SYSTEM")
    L.append("   ibrav = 0")
    L.append(f"   nat = {nat}")
    L.append(f"   ntyp = {ntyp}")
    L.append(f"   ecutwfc = {args.ecutwfc}")
    L.append(f"   ecutrho = {args.ecutrho}")
    L.append("   occupations = 'smearing'")
    L.append("   smearing = 'gaussian'")
    L.append(f"   degauss = {args.degauss}")
    if args.charge:
        L.append(f"   tot_charge = {args.charge}")
    if args.d3:
        L.append("   vdw_corr = 'dft-d3'")
        L.append("   dftd3_version = 4")
    L.append("   nosym = .true.")
    L.append("   noinv = .true.")
    if args.nspin == 2:
        L.append("   nspin = 2")
        if args.tot_magnetization is not None:
            L.append(f"   tot_magnetization = {args.tot_magnetization}")
    L.append("/")
    L.append("&ELECTRONS")
    L.append(f"   conv_thr = {args.conv_thr}")
    L.append("   mixing_beta = 0.3")
    L.append("   electron_maxstep = 200")
    L.append("/")
    L.append("ATOMIC_SPECIES")
    for s in species:
        fname, mass = PSEUDO[s]
        L.append(f"  {s:3s} {mass:10.5f}  {fname}")
    L.append("BEGIN_POSITIONS")
    L.append("FIRST_IMAGE")
    L.append(_atomic_positions_block(ini).rstrip())
    L.append("LAST_IMAGE")
    L.append(_atomic_positions_block(fin).rstrip())
    L.append("END_POSITIONS")
    L.append("K_POINTS automatic")
    L.append(f"  {kp[0]} {kp[1]} {kp[2]} 0 0 0")
    L.append("CELL_PARAMETERS angstrom")
    for v in ini.cell.array:
        L.append(f"  {v[0]:18.12f} {v[1]:18.12f} {v[2]:18.12f}")
    L.append("END_ENGINE_INPUT")
    L.append("END")

    Path(args.out).write_text("\n".join(L) + "\n")
    print(f"[neb.x] wrote {args.out}: {nat} atoms, {ntyp} species, q=+{args.charge}, "
          f"nspin={args.nspin}, {args.num_images} images (incl. endpoints), "
          f"CI={args.ci_scheme}, path_thr={args.path_thr} eV/A, D3={args.d3}")


if __name__ == "__main__":
    main()

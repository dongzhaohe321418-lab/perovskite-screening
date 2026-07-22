#!/usr/bin/env python3
"""Step 0 of the tracer bullet: bulk CsPbI3 with zero-shot MACE.

Builds the ideal cubic (alpha) perovskite cell, then a symmetry-broken
sqrt2 x sqrt2 x 2 (20-atom) cell that is allowed to relax into the tilted
room-temperature gamma-like phase. Reports lattice parameters, the detected
space group, and the energy gain from octahedral tilting.

Output:
  structures/cubic_relaxed.extxyz
  structures/gamma_relaxed.extxyz   <- used by 01_vacancy_neb.py
  results/bulk.json
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
from ase import Atoms
from ase.build import make_supercell
from ase.filters import FrechetCellFilter
from ase.io import write
from ase.optimize import FIRE

ROOT = Path(__file__).resolve().parent.parent


def ideal_cubic(a0: float = 6.25) -> Atoms:
    """Ideal 5-atom alpha-CsPbI3 perovskite cell."""
    return Atoms(
        symbols=["Pb", "I", "I", "I", "Cs"],
        scaled_positions=[
            (0.0, 0.0, 0.0),
            (0.5, 0.0, 0.0),
            (0.0, 0.5, 0.0),
            (0.0, 0.0, 0.5),
            (0.5, 0.5, 0.5),
        ],
        cell=[a0, a0, a0],
        pbc=True,
    )


def vc_relax(atoms: Atoms, calc, fmax: float, steps: int, tag: str) -> Atoms:
    atoms.calc = calc
    opt = FIRE(FrechetCellFilter(atoms), logfile=str(ROOT / "results" / f"opt_{tag}.log"))
    opt.run(fmax=fmax, steps=steps)
    return atoms


def spacegroup(atoms: Atoms, symprec: float) -> str:
    import spglib

    cell = (atoms.get_cell().array, atoms.get_scaled_positions(), atoms.get_atomic_numbers())
    ds = spglib.get_symmetry_dataset(cell, symprec=symprec)
    if ds is None:
        return "unknown"
    # spglib >=2.5 returns a dataclass, earlier a dict
    num = getattr(ds, "number", None) or ds.get("number")
    intl = getattr(ds, "international", None) or ds.get("international")
    return f"{intl} (#{num})"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="medium", help="mace_mp checkpoint (medium, medium-mpa-0, ...)")
    p.add_argument("--device", default="cpu")
    p.add_argument("--fmax", type=float, default=0.02)
    args = p.parse_args()

    from mace.calculators import mace_mp

    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "structures").mkdir(exist_ok=True)

    t0 = time.time()
    calc = mace_mp(model=args.model, device=args.device, default_dtype="float32")

    # --- ideal cubic reference ---------------------------------------------
    cubic = ideal_cubic()
    cubic = vc_relax(cubic, calc, args.fmax, 200, "cubic")
    e_cubic = cubic.get_potential_energy() / len(cubic)
    a_cubic = cubic.cell.lengths().mean()
    write(ROOT / "structures" / "cubic_relaxed.extxyz", cubic)
    print(f"[cubic]  a = {a_cubic:.4f} A   E = {e_cubic:.4f} eV/atom")

    # --- symmetry-broken 20-atom cell -> tilted gamma-like phase -----------
    seed = make_supercell(ideal_cubic(a_cubic), [[1, 1, 0], [-1, 1, 0], [0, 0, 2]])
    rng = np.random.default_rng(42)
    seed.positions += rng.normal(scale=0.12, size=seed.positions.shape)
    seed.set_cell(seed.cell.array * np.array([[1.000], [1.005], [0.995]]), scale_atoms=True)

    gamma = vc_relax(seed, calc, args.fmax, 800, "gamma")
    e_gamma = gamma.get_potential_energy() / len(gamma)
    write(ROOT / "structures" / "gamma_relaxed.extxyz", gamma)

    la, lb, lc = gamma.cell.lengths()
    print(f"[gamma]  a,b,c = {la:.4f}, {lb:.4f}, {lc:.4f} A")
    print(f"[gamma]  E = {e_gamma:.4f} eV/atom   dE(tilt) = {1000*(e_gamma - e_cubic):.1f} meV/atom")
    for sp in (0.01, 0.1):
        print(f"[gamma]  space group (symprec={sp}): {spacegroup(gamma, sp)}")

    json.dump(
        {
            "model": args.model,
            "device": args.device,
            "cubic": {"a": a_cubic, "e_per_atom": e_cubic},
            "gamma": {
                "abc": [la, lb, lc],
                "e_per_atom": e_gamma,
                "tilt_gain_meV_per_atom": 1000 * (e_gamma - e_cubic),
                "spacegroup_loose": spacegroup(gamma, 0.1),
                "spacegroup_tight": spacegroup(gamma, 0.01),
            },
            "runtime_s": time.time() - t0,
        },
        open(ROOT / "results" / "bulk.json", "w"),
        indent=2,
    )
    print(f"done in {time.time() - t0:.0f} s -> results/bulk.json")


if __name__ == "__main__":
    main()

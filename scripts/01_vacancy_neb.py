#!/usr/bin/env python3
"""Step 1 of the tracer bullet: iodide-vacancy migration barrier via CI-NEB.

Takes the relaxed gamma-like cell from 00_relax_bulk.py, builds a 2x2x2
supercell (~160 atoms), removes one iodide to create V_I, and computes the
barrier for a neighbouring iodide (sharing the same Pb octahedron, i.e. an
octahedron-edge hop) to move into the vacancy.

NOTE: zero-shot MACE is charge-agnostic, so this is the quasi-neutral PES.
The number is a pipeline-validation milestone, not a production V_I+ barrier;
per-charge-state fine-tuning supplies those (see proposal Section 4.5).

Output:
  results/neb.json, results/barrier.png, structures/neb_path.extxyz
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
from ase.io import read, write
from ase.mep import NEB
from ase.optimize import FIRE

ROOT = Path(__file__).resolve().parent.parent


def pick_hop_pair(atoms):
    """Return indices (i_vac, i_hop) of two iodides on the same PbI6 octahedron.

    i_vac is the iodide removed to form the vacancy; i_hop migrates into it.
    Cis pair on one octahedron => I-I separation ~ a_pc/sqrt(2) ~ 4.5 A.
    """
    sym = np.array(atoms.get_chemical_symbols())
    pb_idx = np.flatnonzero(sym == "Pb")
    # Pb closest to the cell centre, to keep the defect away from any bias
    centre = atoms.cell.array.sum(axis=0) / 2
    pb = pb_idx[np.argmin(np.linalg.norm(atoms.positions[pb_idx] - centre, axis=1))]

    i_idx = np.flatnonzero(sym == "I")
    d_pb = atoms.get_distances(pb, i_idx, mic=True)
    octa = i_idx[d_pb < 3.8]  # the six coordinating iodides
    if len(octa) < 2:
        raise RuntimeError(f"only {len(octa)} iodides coordinate Pb{pb}")

    # choose the cis pair with I-I distance closest to the ideal edge length
    best, best_err = None, 1e9
    for a in range(len(octa)):
        for b in range(a + 1, len(octa)):
            d = atoms.get_distance(octa[a], octa[b], mic=True)
            if abs(d - 4.5) < best_err:
                best, best_err = (int(octa[a]), int(octa[b])), abs(d - 4.5)
    return best


def relax(atoms, calc, fmax, steps, tag):
    atoms.calc = calc
    FIRE(atoms, logfile=str(ROOT / "results" / f"opt_{tag}.log")).run(fmax=fmax, steps=steps)
    return atoms


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="medium")
    p.add_argument("--device", default="cpu")
    p.add_argument("--n-images", type=int, default=5, help="interior NEB images")
    p.add_argument("--fmax-endpoint", type=float, default=0.03)
    p.add_argument("--fmax-neb", type=float, default=0.05)
    args = p.parse_args()

    from mace.calculators import mace_mp

    t0 = time.time()
    make_calc = lambda: mace_mp(model=args.model, device=args.device, default_dtype="float32")
    calc = make_calc()

    bulk = read(ROOT / "structures" / "gamma_relaxed.extxyz")
    sc = bulk.repeat((2, 2, 2))
    print(f"supercell: {len(sc)} atoms, cell = {np.round(sc.cell.lengths(), 2)} A")

    i_vac, i_hop = pick_hop_pair(sc)
    hop_d = sc.get_distance(i_vac, i_hop, mic=True)
    print(f"vacancy at I{i_vac}, migrating I{i_hop}, hop distance {hop_d:.2f} A")

    # initial: vacancy at site 1 (remove i_vac). final: the i_hop iodide now
    # occupies site 1, vacancy at site 2. Same atom ordering in both images.
    initial = sc.copy()
    vac_pos = initial.positions[i_vac].copy()
    del initial[i_vac]
    final = sc.copy()
    final.positions[i_hop] = vac_pos
    del final[i_vac]

    print("relaxing endpoints ...")
    initial = relax(initial, calc, args.fmax_endpoint, 500, "neb_initial")
    final = relax(final, make_calc(), args.fmax_endpoint, 500, "neb_final")
    e_i, e_f = initial.get_potential_energy(), final.get_potential_energy()

    images = [initial] + [initial.copy() for _ in range(args.n_images)] + [final]
    for im in images[1:-1]:
        im.calc = make_calc()
    neb = NEB(images, climb=False, k=0.1)
    neb.interpolate(method="idpp", mic=True)

    print("NEB stage 1 (no climb) ...")
    FIRE(neb, logfile=str(ROOT / "results" / "opt_neb1.log")).run(fmax=2 * args.fmax_neb, steps=300)
    print("NEB stage 2 (climbing image) ...")
    neb.climb = True
    FIRE(neb, logfile=str(ROOT / "results" / "opt_neb2.log")).run(fmax=args.fmax_neb, steps=300)

    energies = np.array([im.get_potential_energy() for im in images])
    rel = energies - energies[0]
    ea_fwd = float(rel.max())
    ea_bwd = float((energies - energies[-1]).max())
    print(f"\nE_a(forward)  = {ea_fwd:.3f} eV")
    print(f"E_a(backward) = {ea_bwd:.3f} eV")
    print("literature (DFT, V_I in lead-iodide perovskites): ~0.1-0.6 eV; "
          "zero-shot MPtrj models bias low (softening)")

    write(ROOT / "structures" / "neb_path.extxyz", images)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x = np.arange(len(images))
    fig, ax = plt.subplots(figsize=(5.4, 3.6))
    ax.plot(x, rel, "o-", color="#1F3055")
    ax.set_xlabel("image")
    ax.set_ylabel("E - E$_0$ (eV)")
    ax.set_title(f"V$_I$ hop, zero-shot MACE ({args.model}): "
                 f"E$_a$ = {ea_fwd:.2f} eV")
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "barrier.png", dpi=200)

    json.dump(
        {
            "model": args.model,
            "device": args.device,
            "n_atoms": len(initial),
            "hop_distance_A": float(hop_d),
            "i_vac": i_vac,
            "i_hop": i_hop,
            "E_images_eV": energies.tolist(),
            "Ea_forward_eV": ea_fwd,
            "Ea_backward_eV": ea_bwd,
            "dE_endpoints_eV": float(e_f - e_i),
            "caveat": "zero-shot, charge-agnostic (quasi-neutral) PES; path-seeding quality only",
            "runtime_s": time.time() - t0,
        },
        open(ROOT / "results" / "neb.json", "w"),
        indent=2,
    )
    print(f"done in {(time.time() - t0)/60:.1f} min -> results/neb.json, results/barrier.png")


if __name__ == "__main__":
    main()

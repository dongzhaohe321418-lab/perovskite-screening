#!/usr/bin/env python3
"""Lane 2 / W2-3 — zero-shot FA baseline Ea distribution (EXPLORATORY / QUARANTINED).

For each FA orientation config from W2-2 (scripts/08), carve the SAME V_I
octahedron-edge hop and run a zero-shot MACE CI-NEB. Output the Ea distribution
(N, mean, std, range) — per EXECUTION_GUIDE this spread sizes the Stage 4/5
sampling budget and is "the single most important number in Lane 2".

Reuses the proven NEB machinery from scripts/04:
  * per-image MACE calculators (built once, ~3.4x faster than a shared calc);
  * endpoints carved with IDENTICAL atom ordering (assert-checked);
  * two-stage FIRE: non-climb (fmax 2x) then CI-NEB climb (fmax);
  * octahedron-edge hop chosen on the Pb nearest the cell centre.

MD is only an orientation sampler; these are zero-shot barriers, NOT validated
rotational/kinetic numbers. Fixed lattice (per user decision 2026-07-24): endpoints
relax positions only at the config's cell; cell held fixed so NEB endpoints share it.

Usage:
  python 09_fa_neb_distribution.py --configs fa_md/fa_orient_*.extxyz \
      --outdir fa_neb --device cuda
"""
import argparse, json, glob
from pathlib import Path
import numpy as np
from ase.io import read, write
from ase.mep import NEB
from ase.optimize import FIRE

N_IMAGES = 5
FMAX_EP = 0.03
FMAX_NEB = 0.05


def pick_hop_pair(atoms):
    """(i_vac, i_hop): two cis iodides (~4.5 A apart) on the Pb octahedron nearest
    the cell centre — an octahedron-edge hop. Same rule as scripts/04."""
    sym = np.array(atoms.get_chemical_symbols())
    pb_idx = np.flatnonzero(sym == "Pb")
    centre = atoms.cell.array.sum(axis=0) / 2
    pb = pb_idx[np.argmin(np.linalg.norm(atoms.positions[pb_idx] - centre, axis=1))]
    i_idx = np.flatnonzero(sym == "I")
    d_pb = atoms.get_distances(pb, i_idx, mic=True)
    octa = i_idx[d_pb < 3.8]
    if len(octa) < 2:
        raise RuntimeError(f"only {len(octa)} iodides coordinate Pb{pb}")
    best, best_err = None, 1e9
    for a in range(len(octa)):
        for b in range(a + 1, len(octa)):
            d = atoms.get_distance(int(octa[a]), int(octa[b]), mic=True)
            if abs(d - 4.5) < best_err:
                best, best_err = (int(octa[a]), int(octa[b])), abs(d - 4.5)
    return best


def make_endpoints(sc):
    """(initial, final) V_I edge-hop endpoints with identical atom ordering.
    initial = remove i_vac. final = move i_hop into the vacated site, remove i_vac."""
    i_vac, i_hop = pick_hop_pair(sc)
    hop_d = sc.get_distance(i_vac, i_hop, mic=True)
    initial = sc.copy()
    vac_pos = initial.positions[i_vac].copy()
    del initial[i_vac]
    final = sc.copy()
    final.positions[i_hop] = vac_pos
    del final[i_vac]
    assert initial.get_chemical_symbols() == final.get_chemical_symbols(), "ordering mismatch"
    assert np.allclose(initial.cell.array, final.cell.array), "cell mismatch"
    meta = {"i_vac": int(i_vac), "i_hop": int(i_hop), "hop_distance_A": float(hop_d),
            "n_atoms": len(initial)}
    return initial, final, meta


def build_calcs(n, model, device, dtype):
    from mace.calculators import mace_mp
    return [mace_mp(model=model, device=device, default_dtype=dtype, dispersion=False)
            for _ in range(n)]


def run_neb(initial, final, calcs, n_images=N_IMAGES, fmax_ep=FMAX_EP, fmax_neb=FMAX_NEB):
    initial.calc = calcs[0]
    c1 = FIRE(initial, logfile=None).run(fmax=fmax_ep, steps=800)
    final.calc = calcs[-1]
    c2 = FIRE(final, logfile=None).run(fmax=fmax_ep, steps=800)
    e_i = initial.get_potential_energy(); e_f = final.get_potential_energy()
    images = [initial] + [initial.copy() for _ in range(n_images)] + [final]
    for im, c in zip(images, calcs):
        im.calc = c
    neb = NEB(images, climb=False, k=0.1)
    neb.interpolate(method="idpp", mic=True)
    conv1 = FIRE(neb, logfile=None).run(fmax=2 * fmax_neb, steps=400)
    neb.climb = True
    conv2 = FIRE(neb, logfile=None).run(fmax=fmax_neb, steps=400)
    energies = [im.get_potential_energy() for im in images]
    e0 = energies[0]
    prof = [(e - e0) * 1000 for e in energies]  # meV vs initial
    saddle = int(np.argmax(energies))
    ea_fwd = (max(energies) - energies[0]) * 1000
    ea_bwd = (max(energies) - energies[-1]) * 1000
    return {"profile_meV": [round(x, 1) for x in prof], "saddle_image": saddle,
            "Ea_fwd_meV": round(ea_fwd, 1), "Ea_bwd_meV": round(ea_bwd, 1),
            "endpoints_converged": bool(c1 and c2), "neb_converged": bool(conv2),
            "dE_endpoint_meV": round((e_f - e_i) * 1000, 1)}, images


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--configs", nargs="+", required=True,
                   help="glob(s) for fa_orient_*.extxyz from W2-2")
    p.add_argument("--outdir", default="fa_neb")
    p.add_argument("--device", default="cuda")
    p.add_argument("--model", default="medium")
    p.add_argument("--dtype", default="float64")
    args = p.parse_args()
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)

    files = sorted({f for pat in args.configs for f in glob.glob(pat)})
    assert files, f"no configs matched {args.configs}"
    print(f"[neb] {len(files)} FA orientation configs")

    calcs = build_calcs(N_IMAGES + 2, args.model, args.device, args.dtype)
    results = []
    for k, f in enumerate(files):
        sc = read(f)
        initial, final, meta = make_endpoints(sc)
        res, images = run_neb(initial, final, calcs)
        rec = {"config": Path(f).name, "config_id": k, **meta, **res}
        results.append(rec)
        write(outdir / f"fa_neb_band_{k:02d}.extxyz", images)
        print(f"[neb] {Path(f).name}: Ea_fwd={res['Ea_fwd_meV']:.1f} meV "
              f"saddle=img{res['saddle_image']} conv={res['neb_converged']} "
              f"hop={meta['hop_distance_A']:.2f}A")

    eas = [r["Ea_fwd_meV"] for r in results if r["neb_converged"]]
    dist = {"n": len(eas), "mean_meV": round(float(np.mean(eas)), 1),
            "std_meV": round(float(np.std(eas)), 1),
            "min_meV": round(float(np.min(eas)), 1),
            "max_meV": round(float(np.max(eas)), 1),
            "range_meV": round(float(np.max(eas) - np.min(eas)), 1),
            "all_Ea_meV": eas}
    out = {"tag": "EXPLORATORY / QUARANTINED — Lane 2 W2-3",
           "note": "zero-shot MACE CI-NEB; fixed lattice; orientation sampled from W2-2 MD. "
                   "NOT a validated kinetic barrier.",
           "n_images": N_IMAGES, "fmax_neb": FMAX_NEB,
           "Ea_distribution": dist, "per_config": results}
    json.dump(out, open(outdir / "fa_neb_distribution.json", "w"), indent=2)
    print(f"\n[neb] Ea DISTRIBUTION (n={dist['n']}): mean {dist['mean_meV']} +/- "
          f"{dist['std_meV']} meV, range [{dist['min_meV']}, {dist['max_meV']}] "
          f"= {dist['range_meV']} meV spread")


if __name__ == "__main__":
    main()

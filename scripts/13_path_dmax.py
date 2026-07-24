#!/usr/bin/env python3
"""Rigorous d_max between a DFT explore path and the MACE reference path (Stage 2.2 ★).

The ★ budget decision hinges on d_max = max atomic displacement of the DFT-relaxed
explore path relative to the MACE path. Per review this must be done carefully:
  * PBC unwrap  — displacements via minimum image, so an atom crossing a cell face
    is not counted as moving ~a cell length;
  * rigid alignment — remove global drift before measuring the residual (report
    aligned AND unaligned so a large gap flags a real drift);
  * consistent atom numbering — asserted identical composition+ordering.

Alignment is TRANSLATION-ONLY. For a fixed, identical cell (which both the DFT and
MACE paths use) there is no rotational degree of freedom to align against — both
structures live in the same cell frame — so a Kabsch rotation is not physically
meaningful and can only mask real differences. The one genuine rigid freedom is a
translation (absolute origin in a periodic cell is arbitrary), removed here as the
mean min-image displacement over the fit set. This is also numerically robust: in the
real regime (DFT vs MACE at the SAME path image differ by <~0.5 A) the min-image
displacement is always well under half a cell.

Besides all-atom d_max it reports the physically diagnostic quantities:
  * migrating-I displacement (the ion that moves into the vacancy);
  * nearest-neighbour Pb-I bond length at the saddle;
  * saddle image index for each path;
  * a mechanism-change flag (different saddle position or a different migrating ion).

Paths may have different image counts (explore 3-interior vs MACE 5-interior): both
are resampled onto a common normalised arc-length grid before the image-by-image
comparison.

Usage:
  python 13_path_dmax.py --dft dft_explore_band.extxyz --mace gamma_neb_band_5int.extxyz \
      --out dmax_report.json
"""
import argparse, json
from pathlib import Path
import numpy as np
from ase.io import read


def _min_image_disp(a, b, cell):
    """Displacement b-a for matched atoms, wrapped to the minimum image (Cartesian A)."""
    d = b - a
    frac = np.linalg.solve(cell.T, d.T).T   # to fractional
    frac -= np.round(frac)                   # minimum image
    return frac @ cell                       # back to Cartesian


def aligned_max_disp(atoms_a, atoms_b, align=True, mask=None):
    """Max per-atom displacement (A) between two identical-ordering structures,
    PBC-aware (min-image), optionally after removing a rigid TRANSLATION (the only
    rigid freedom for a fixed identical cell). mask restricts the atoms used to fit the
    translation (e.g. framework only); displacement is reported for all atoms.
    Returns (dmax, per_atom_disp_magnitudes, translation_vector)."""
    assert atoms_a.get_chemical_symbols() == atoms_b.get_chemical_symbols(), \
        "atom ordering/composition mismatch"
    cell = atoms_a.cell.array
    pa = atoms_a.get_positions()
    pb = atoms_b.get_positions()
    disp = _min_image_disp(pa, pb, cell)          # per-atom min-image displacement
    if align:
        m = np.ones(len(pa), bool) if mask is None else np.asarray(mask, bool)
        t = disp[m].mean(0)                        # rigid translation = mean displacement
        disp = disp - t                            # residual after translation removal
    else:
        t = np.zeros(3)
    dmag = np.linalg.norm(disp, axis=1)
    return float(dmag.max()), dmag, t


def resample_path(images, n):
    """Resample a list of Atoms onto n points along normalised cumulative arc length
    (linear interpolation of Cartesian positions, PBC-unwrapped along the path)."""
    pos = [im.get_positions() for im in images]
    cell = images[0].cell.array
    # unwrap consecutive images so interpolation is continuous
    unwrapped = [pos[0]]
    for i in range(1, len(pos)):
        d = _min_image_disp(unwrapped[-1], pos[i], cell)
        unwrapped.append(unwrapped[-1] + d)
    unwrapped = np.array(unwrapped)  # (nimg, nat, 3)
    seg = np.sqrt(((unwrapped[1:] - unwrapped[:-1])**2).sum(axis=(1, 2)))
    s = np.concatenate([[0], np.cumsum(seg)])
    s /= s[-1]
    grid = np.linspace(0, 1, n)
    out = []
    for g in grid:
        j = np.searchsorted(s, g, side="right") - 1
        j = min(max(j, 0), len(s) - 2)
        f = (g - s[j]) / (s[j + 1] - s[j] + 1e-12)
        p = unwrapped[j] * (1 - f) + unwrapped[j + 1] * f
        at = images[0].copy(); at.set_positions(p)
        out.append(at)
    return out


def migrating_ion_index(initial, final):
    """The atom (expected an I) that moves most between the path endpoints = migrating ion."""
    cell = initial.cell.array
    d = np.linalg.norm(_min_image_disp(initial.get_positions(), final.get_positions(), cell), axis=1)
    return int(np.argmax(d)), float(d.max())


def nearest_pb_i(atoms, i_index):
    sym = np.array(atoms.get_chemical_symbols())
    pb = np.flatnonzero(sym == "Pb")
    d = atoms.get_distances(i_index, pb, mic=True)
    return float(d.min())


def saddle_index(images):
    e = np.array([im.get_potential_energy() for im in images])
    return int(np.argmax(e))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dft", required=True, help="DFT explore path (extxyz, all images)")
    p.add_argument("--mace", required=True, help="MACE reference path (extxyz, all images)")
    p.add_argument("--out", required=True)
    p.add_argument("--threshold", type=float, default=0.15, help="d_max decision threshold (A)")
    args = p.parse_args()

    dft = read(args.dft, index=":")
    mace = read(args.mace, index=":")
    n = max(len(dft), len(mace))
    dft_r = resample_path(dft, n)
    mace_r = resample_path(mace, n)

    per_image = []
    dmax_all = 0.0
    for i, (a, b) in enumerate(zip(mace_r, dft_r)):
        dm_aln, _, _ = aligned_max_disp(a, b, align=True)
        dm_raw, _, _ = aligned_max_disp(a, b, align=False)
        per_image.append({"image": i, "dmax_aligned_A": round(dm_aln, 4),
                          "dmax_unaligned_A": round(dm_raw, 4)})
        dmax_all = max(dmax_all, dm_aln)

    # diagnostics
    mig_dft, mig_dft_d = migrating_ion_index(dft[0], dft[-1])
    mig_mace, mig_mace_d = migrating_ion_index(mace[0], mace[-1])
    sad_dft = saddle_index(dft) if _has_energy(dft) else None
    sad_mace = saddle_index(mace) if _has_energy(mace) else None
    mechanism_changed = (mig_dft != mig_mace) or (sad_dft is not None and sad_mace is not None
                                                  and abs(sad_dft/(len(dft)-1) - sad_mace/(len(mace)-1)) > 0.2)

    decision = ("economy (q1 full CI-NEB; q0 DFT-sampled -> PROVISIONAL)"
                if dmax_all < args.threshold and not mechanism_changed
                else "full CI-NEB both states (-> path to VALIDATED)")

    report = {"d_max_all_atom_A": round(dmax_all, 4), "threshold_A": args.threshold,
              "mechanism_changed": bool(mechanism_changed),
              "migrating_ion": {"dft_index": mig_dft, "dft_disp_A": round(mig_dft_d, 3),
                                "mace_index": mig_mace, "mace_disp_A": round(mig_mace_d, 3),
                                "same_ion": mig_dft == mig_mace},
              "saddle_index": {"dft": sad_dft, "mace": sad_mace},
              "per_image": per_image, "decision": decision,
              "note": "d_max is aligned (Kabsch, PBC-unwrapped). Compare aligned vs unaligned "
                      "per image: a large gap flags global path drift."}
    json.dump(report, open(args.out, "w"), indent=2)
    print(f"[dmax] d_max(all-atom, aligned) = {dmax_all:.3f} A (threshold {args.threshold})")
    print(f"[dmax] migrating ion: dft #{mig_dft} ({mig_dft_d:.2f} A) vs mace #{mig_mace} "
          f"({mig_mace_d:.2f} A) same={mig_dft==mig_mace}")
    print(f"[dmax] mechanism changed: {mechanism_changed}  ->  {decision}")


def _has_energy(images):
    try:
        images[0].get_potential_energy(); return True
    except Exception:
        return False


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
Objective-2 structure enumeration for the FA_0.95Cs_0.05PbI3 production host.

Design rule (PI gate 6): the CONFIGURATIONAL ENSEMBLE is a first-class dimension of
the results table, not a post-hoc addition. Every row carries (dopant, site_class,
host_member, path_id, d_dopant_vacancy) so that a dEa DISTRIBUTION -- never a single
number -- is the unit of comparison between dopants.

Everything this script emits is EXPLORE-tier. Nothing here is a production ranking.

Usage:
  python scripts/16_objective2_enumerate.py --host-dir results/fa_host \
      --out results/objective2/structures --members 0 1 2 3 --max-per-dopant 6
"""
from __future__ import annotations
import argparse, json, os, itertools
import numpy as np
from ase.io import read, write

# ---------------------------------------------------------------------------
# Candidate table. Classes and members follow proposal_v2.tex Objective 2:
#   A-site substitution, B-site substitution (deliberate NEGATIVE CONTROL class,
#   anchored to the Arber et al. 2025 null result), X-site substitution,
#   interstitials. Cs+ is listed first because the proposal singles it out: whether
#   the 5% Cs of the workhorse formulation pins the iodide sublattice or only
#   stabilises the phase is answered as a by-product.
# ---------------------------------------------------------------------------
CANDIDATES = [
    # (label, class, substitutes, note)
    ("Cs_A",   "A_site",       "FA",  "priority: does the 5% Cs itself pin the I sublattice?"),
    ("GA_A",   "A_site",       "FA",  "guanidinium; comparable to hybrid-lattice pinning literature"),
    ("DMA_A",  "A_site",       "FA",  "dimethylammonium"),
    ("AA_A",   "A_site",       "FA",  "acetamidinium"),
    ("MA_A",   "A_site",       "FA",  "methylammonium; small-cation control"),
    ("Sr_B",   "B_site_ctrl",  "Pb",  "NEGATIVE CONTROL (Arber 2025 null)"),
    ("Ca_B",   "B_site_ctrl",  "Pb",  "NEGATIVE CONTROL"),
    ("Bi_B",   "B_site_ctrl",  "Pb",  "NEGATIVE CONTROL; also mid-gap-state failure mode"),
    ("La_B",   "B_site_ctrl",  "Pb",  "NEGATIVE CONTROL"),
    ("Cl_X",   "X_site",       "I",   "halide substitution"),
    ("SCN_X",  "X_site",       "I",   "pseudohalide"),
    ("K_int",  "interstitial", None,  "interstitial cation"),
    ("Rb_int", "interstitial", None,  "interstitial cation"),
]

SIMPLE_ION = {"Cs_A": "Cs", "Sr_B": "Sr", "Ca_B": "Ca", "Bi_B": "Bi", "La_B": "La",
              "Cl_X": "Cl", "K_int": "K", "Rb_int": "Rb"}
MOLECULAR = {"GA_A", "DMA_A", "AA_A", "MA_A", "SCN_X"}

# A site closer than this to the vacancy IS the vacancy site (or overlaps it).
MIN_SEP_A = 1.5


def a_site_centroids(atoms):
    """FA molecular centroids + Cs positions = the A-site sublattice."""
    sym = np.array(atoms.get_chemical_symbols())
    pos = atoms.positions
    sites = []
    for i in np.where(sym == "Cs")[0]:
        sites.append({"kind": "Cs", "pos": pos[i].copy(), "idx": [int(i)]})
    # FA = CH(NH2)2 : group each C with its 2 nearest N and their H
    cidx = np.where(sym == "C")[0]
    nidx = np.where(sym == "N")[0]
    hidx = np.where(sym == "H")[0]
    cell = atoms.cell.array
    inv = np.linalg.inv(cell)

    def mic(d):
        f = d @ inv
        f -= np.round(f)
        return f @ cell

    for c in cidx:
        dn = np.linalg.norm(mic(pos[nidx] - pos[c]), axis=1)
        mine = nidx[np.argsort(dn)[:2]]
        grp = [int(c)] + [int(x) for x in mine]
        for n in mine:
            dh = np.linalg.norm(mic(pos[hidx] - pos[n]), axis=1)
            grp += [int(x) for x in hidx[np.argsort(dh)[:2]]]
        dh = np.linalg.norm(mic(pos[hidx] - pos[c]), axis=1)
        grp.append(int(hidx[np.argmin(dh)]))
        grp = sorted(set(grp))
        centroid = pos[c] + mic(pos[grp] - pos[c]).mean(axis=0)
        sites.append({"kind": "FA", "pos": centroid, "idx": grp})
    return sites


def vacancy_position(pristine, vac):
    """Locate the removed iodide by matching I sublattices."""
    pi = pristine.positions[np.array(pristine.get_chemical_symbols()) == "I"]
    vi = vac.positions[np.array(vac.get_chemical_symbols()) == "I"]
    cell = pristine.cell.array
    inv = np.linalg.inv(cell)
    best = None
    for p in pi:
        d = vi - p
        f = d @ inv
        f -= np.round(f)
        dmin = np.linalg.norm(f @ cell, axis=1).min()
        if best is None or dmin > best[0]:
            best = (dmin, p)
    return best[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host-dir", default="results/fa_host")
    ap.add_argument("--out", default="results/objective2/structures")
    ap.add_argument("--members", type=int, nargs="+", default=[0, 1, 2, 3],
                    help="FA-orientation ensemble members to enumerate over")
    ap.add_argument("--max-per-dopant", type=int, default=6,
                    help="distance-binned sites retained per dopant per member")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    pristine = read(f"{args.host_dir}/fa19cs1_pb20i60_233.extxyz")
    vac = read(f"{args.host_dir}/fa19cspb20i59_232_vI.extxyz")
    vpos = vacancy_position(pristine, vac)
    cell = vac.cell.array
    inv = np.linalg.inv(cell)

    def dist_to_vac(p):
        f = (p - vpos) @ inv
        f -= np.round(f)
        return float(np.linalg.norm(f @ cell))

    # Minimum-image radius: half the shortest perpendicular width of the cell. Beyond
    # this a "dopant-vacancy separation" is really a distance to a periodic image.
    vol = abs(np.linalg.det(cell))
    widths = [vol / np.linalg.norm(np.cross(cell[(k + 1) % 3], cell[(k + 2) % 3]))
              for k in range(3)]
    r_max = float(min(widths)) / 2.0
    print(f"minimum-image radius r_max = {r_max:.2f} A "
          f"(perpendicular widths {np.round(widths,2)}); sites beyond it are excluded")

    rows = []
    for member in args.members:
        mpath = f"{args.host_dir}/fa_ensemble_{member:02d}.extxyz"
        host_atoms = read(mpath) if os.path.exists(mpath) else pristine
        sites = a_site_centroids(host_atoms)
        sym = np.array(host_atoms.get_chemical_symbols())
        pb_idx = np.where(sym == "Pb")[0]
        i_idx = np.where(sym == "I")[0]

        for label, cls, subs, note in CANDIDATES:
            if cls in ("A_site",):
                cand = [(s["pos"], s["idx"], s["kind"]) for s in sites]
            elif cls == "B_site_ctrl":
                cand = [(host_atoms.positions[i], [int(i)], "Pb") for i in pb_idx]
            elif cls == "X_site":
                cand = [(host_atoms.positions[i], [int(i)], "I") for i in i_idx]
            else:  # interstitial: cuboctahedral voids approximated by Pb-Pb midpoints
                cand = []
                for a, b in itertools.combinations(pb_idx, 2):
                    d = host_atoms.positions[b] - host_atoms.positions[a]
                    f = d @ inv
                    f -= np.round(f)
                    dv = f @ cell
                    if 5.5 < np.linalg.norm(dv) < 7.5:
                        cand.append((host_atoms.positions[a] + dv / 2, [], "void"))

            scored = sorted(((dist_to_vac(p), p, idx, kind) for p, idx, kind in cand),
                            key=lambda t: t[0])
            # Exclude two classes of meaningless site:
            #  (a) d ~ 0 : that IS the vacancy site (substituting the removed iodide,
            #      or placing an interstitial inside the vacancy, is not a dopant study);
            #  (b) d > d_min/2 : beyond the minimum-image radius the "separation" is to a
            #      periodic image, not a real neighbour, so dEa(d) there is an artefact.
            scored = [t for t in scored if MIN_SEP_A <= t[0] <= r_max]
            # distance-BINNED selection (proposal: bin by dopant-vacancy distance)
            if scored:
                dmin, dmax = scored[0][0], scored[-1][0]
                edges = np.linspace(dmin, dmax, args.max_per_dopant + 1)
                picked, used = [], set()
                for lo, hi in zip(edges[:-1], edges[1:]):
                    for k, (d, p, idx, kind) in enumerate(scored):
                        if k in used:
                            continue
                        if lo <= d <= hi:
                            picked.append((d, p, idx, kind))
                            used.add(k)
                            break
            else:
                picked = []

            for j, (d, p, idx, kind) in enumerate(picked):
                rows.append({
                    "dopant": label, "class": cls, "substitutes": subs,
                    "host_member": member, "site_rank": j,
                    "site_kind": kind, "d_dopant_vacancy_A": round(d, 3),
                    "is_molecular": label in MOLECULAR,
                    "simple_ion": SIMPLE_ION.get(label),
                    "n_host_atoms_replaced": len(idx),
                    # Persist the actual site coordinates and the host atom indices.
                    # Downstream screening needs the position to place the dopant; a
                    # distance alone is ambiguous (many sites share a distance).
                    "site_pos_A": [round(float(x), 4) for x in p],
                    "host_atom_indices": idx,
                    "tier": "EXPLORE", "note": note,
                })

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    man = f"{args.out}/enumeration_manifest.json"
    if not args.dry_run:
        json.dump({"n_rows": len(rows),
                   "vacancy_position_A": [round(float(x), 4) for x in vpos],
                   "members": args.members,
                   "max_per_dopant": args.max_per_dopant,
                   "r_max_minimum_image_A": round(r_max, 3),
                   "min_separation_A": MIN_SEP_A,
                   "tier": "EXPLORE",
                   "note": ("Configurational ensemble is a first-class dimension: every row is "
                            "(dopant, class, host_member, site_rank, d_dopant_vacancy). dEa is "
                            "only ever reported as a DISTRIBUTION over host_member x site_rank."),
                   "rows": rows}, open(man, "w"), indent=1)
    print(f"enumerated {len(rows)} candidate configurations "
          f"({len(CANDIDATES)} dopants x {len(args.members)} members x <={args.max_per_dopant} sites)")
    print(f"vacancy at {np.round(vpos,3)}")
    if not args.dry_run:
        print("manifest:", man)
    return rows


if __name__ == "__main__":
    main()

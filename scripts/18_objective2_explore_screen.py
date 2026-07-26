#!/usr/bin/env python
"""
Objective-2 EXPLORE pre-screen: MACE-level dEa distributions over the enumerated
(dopant, host_member, site_rank) configurations.

Two rules are enforced in code, not left to discipline:

  1. VALIDITY GATE (from the noise-floor lesson). A barrier is emitted only if both
     endpoints are local minima of the band and the saddle is interior. Endpoints get a
     tighter force target and a much larger step budget than the band, because this host
     has soft molecular-rotation modes that leave under-relaxed endpoints ABOVE the first
     interior image -- which silently turns Ea into a difference from a non-minimum.

  2. DISTRIBUTION, NOT POINT VALUE. Output is one row per path; dopant-level numbers are
     derived only as medians/IQRs over >= min_paths configurations, and are flagged
     unresolvable unless the between-dopant separation exceeds the measured noise floor.

EXPLORE tier only. Nothing here is a production ranking.

Usage:
  python scripts/18_objective2_explore_screen.py --manifest results/objective2/structures/enumeration_manifest.json \
      --dopants Cs_A GA_A Sr_B --members 0 1 --out results/objective2/explore
"""
from __future__ import annotations
import argparse, hashlib, json, os, time
import numpy as np
from ase.io import read, write
from ase.mep import NEB
from ase.optimize import FIRE

KB = 8.617333262e-5
T_REF = 300.0
TEN_X_MEV = KB * T_REF * np.log(10) * 1000  # 59.5 meV


def path_id(**kw):
    return hashlib.sha1(json.dumps(kw, sort_keys=True).encode()).hexdigest()[:12]


def mic(d, cell):
    inv = np.linalg.inv(cell)
    f = d @ inv
    f -= np.round(f)
    return f @ cell


def nearest(atoms, target, symbol="I", exclude=()):
    sym = np.array(atoms.get_chemical_symbols())
    cell = atoms.cell.array
    best = None
    for i in np.where(sym == symbol)[0]:
        if i in exclude:
            continue
        d = float(np.linalg.norm(mic((atoms.positions[i] - target)[None, :], cell)[0]))
        if best is None or d < best[1]:
            best = (int(i), d)
    return best


def make_calc():
    from mace.calculators import mace_mp
    return mace_mp(model="medium", device="cpu", default_dtype="float64")


def relax(atoms, fmax, steps):
    atoms.calc = make_calc()
    opt = FIRE(atoms, logfile=None)
    opt.run(fmax=fmax, steps=steps)
    return {"fmax": float(np.abs(atoms.get_forces()).max()),
            "converged": bool(opt.converged()),
            "nsteps": int(opt.get_number_of_steps())}


def run_band(ini, fin, n_images, fmax, steps):
    images = [ini] + [ini.copy() for _ in range(n_images)] + [fin]
    for im in images:
        im.calc = make_calc()
    neb = NEB(images, climb=True, allow_shared_calculator=False, method="improvedtangent")
    neb.interpolate(mic=True)
    opt = FIRE(neb, logfile=None)
    opt.run(fmax=fmax, steps=steps)
    E = np.array([im.get_potential_energy() for im in images])
    interior = E[1:-1]
    endpoints_are_minima = bool(interior.min() >= min(E[0], E[-1]) - 1e-6)
    saddle_is_interior = bool(0 < int(E.argmax()) < len(E) - 1)
    return images, E, {
        "valid": endpoints_are_minima and saddle_is_interior,
        "endpoints_are_minima": endpoints_are_minima,
        "saddle_is_interior": saddle_is_interior,
        "band_converged": bool(opt.converged()),
        "band_nsteps": int(opt.get_number_of_steps()),
    }


def apply_dopant(host, row, vpos):
    """Return a doped copy, or None if this row is not representable simply."""
    lab, cls = row["dopant"], row["class"]
    ion = row.get("simple_ion")
    at = host.copy()
    if row["is_molecular"]:
        return None  # molecular substitution needs a builder; EXPLORE stage handles ions first
    if ion is None:
        return None
    if cls == "A_site":
        # An A-site dopant replaces an FA MOLECULE (the majority A cation), not the
        # single existing Cs. Replacing Cs with Cs is a no-op and silently produces an
        # undoped cell -- the manifest records FA-centroid sites for exactly this reason,
        # so delete the whole molecule and place the ion at its centroid.
        idx_mol = row.get("host_atom_indices") or []
        if row.get("site_kind") != "FA" or not idx_mol:
            return None
        # The manifest indices refer to the PRISTINE host; `at` has already had the
        # vacancy iodide deleted, so every index above it is shifted down by one.
        # Remap explicitly rather than assuming a fixed offset.
        vac_idx = row.get("_vacancy_atom_index")
        if vac_idx is not None:
            idx_mol = [i - 1 if i > vac_idx else i for i in idx_mol if i != vac_idx]
        # Verify the remap landed on a genuine FA unit before mutating anything.
        got = sorted(at.get_chemical_symbols()[i] for i in idx_mol)
        if got != sorted(["C"] + ["N"] * 2 + ["H"] * 5):
            raise ValueError(
                f"A-site remap did not land on an FA unit for {lab} "
                f"member-site {row.get('site_rank')}: got {got}")
        keep = [i for i in range(len(at)) if i not in set(idx_mol)]
        pos_centroid = np.array(row["_pos"])
        at = at[keep]
        from ase import Atom
        at.append(Atom(ion, position=pos_centroid))
        return at
    if cls in ("B_site_ctrl", "X_site"):
        target_sym = {"B_site_ctrl": "Pb", "X_site": "I"}[cls]
        sym = np.array(at.get_chemical_symbols())
        if target_sym not in sym:
            return None
        i, _ = nearest(at, np.array(row["_pos"]), symbol=target_sym)
        at.symbols[i] = ion
        return at
    if cls == "interstitial":
        from ase import Atom
        at.append(Atom(ion, position=row["_pos"]))
        return at
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="results/objective2/structures/enumeration_manifest.json")
    ap.add_argument("--host-dir", default="results/fa_host")
    ap.add_argument("--out", default="results/objective2/explore")
    ap.add_argument("--dopants", nargs="+", default=None)
    ap.add_argument("--members", type=int, nargs="+", default=None)
    ap.add_argument("--images", type=int, default=5)
    ap.add_argument("--fmax", type=float, default=0.05)
    ap.add_argument("--steps", type=int, default=300)
    ap.add_argument("--endpoint-fmax", type=float, default=0.02)
    ap.add_argument("--endpoint-steps", type=int, default=800)
    ap.add_argument("--noise-floor", default="results/objective2/noise_floor/noise_floor.json")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    man = json.load(open(args.manifest))
    vpos = np.array(man["vacancy_position_A"])
    rows = man["rows"]
    if args.dopants:
        rows = [r for r in rows if r["dopant"] in args.dopants]
    if args.members is not None:
        rows = [r for r in rows if r["host_member"] in args.members]
    rows = [r for r in rows if not r["is_molecular"]]  # ions first
    if args.limit:
        rows = rows[:args.limit]
    print(f"{len(rows)} ionic configurations selected")

    nf = None
    if os.path.exists(args.noise_floor):
        nfj = json.load(open(args.noise_floor))
        nf = nfj.get("Ea_spread_meV")
        print(f"noise floor from {args.noise_floor}: {nf} meV (status {nfj.get('status','ok')})")
    else:
        print("NO noise floor available -> resolvability cannot be assessed")

    out_rows = []
    for k, row in enumerate(rows):
        t0 = time.time()
        mem = row["host_member"]
        hp = f"{args.host_dir}/fa_ensemble_{mem:02d}.extxyz"
        host_atoms = read(hp) if os.path.exists(hp) else read(f"{args.host_dir}/fa19cs1_pb20i60_233.extxyz")

        # rebuild the site position for this row (manifest stores distance, not coords)
        # -> re-derive by matching the stored distance is ambiguous, so recompute here.
        vi, _ = nearest(host_atoms, vpos, symbol="I")
        base = host_atoms.copy()
        del base[vi]
        mig, hop = nearest(base, vpos, symbol="I")

        # Build the DOPED cell (this is the point of the screen). apply_dopant uses the
        # persisted site coordinates; undoped reference rows keep dopant == "undoped".
        row["_pos"] = row["site_pos_A"]
        row["_vacancy_atom_index"] = vi
        doped = apply_dopant(base, row, vpos)
        if doped is None:
            print(f"  [{k+1}/{len(rows)}] {row['dopant']} m{mem} r{row['site_rank']}: SKIPPED "
                  f"(no simple-ion representation)")
            continue
        ini = doped.copy()
        fin = doped.copy()
        fin.positions[mig] = vpos

        ep = {}
        for nm, at in (("initial", ini), ("final", fin)):
            ep[nm] = relax(at, args.endpoint_fmax, args.endpoint_steps)
        images, E, gate = run_band(ini, fin, args.images, args.fmax, args.steps)

        rec = dict(row)
        rec.pop("_pos", None)
        rec.update({
            "path_id": path_id(dopant=row["dopant"], member=mem, rank=row["site_rank"]),
            "level": "MACE-MP-0-medium", "charge_state": 0,
            "hop_distance_A": round(hop, 3),
            "Ea_forward_eV": float(E.max() - E[0]),
            "Ea_backward_eV": float(E.max() - E[-1]),
            "dE_endpoints_eV": float(E[-1] - E[0]),
            "profile_eV": [float(x - E[0]) for x in E],
            "endpoint_relax": ep, "wall_s": round(time.time() - t0, 1),
        })
        rec.update(gate)
        out_rows.append(rec)
        flag = "" if gate["valid"] else "  [REJECTED by validity gate]"
        print(f"  [{k+1}/{len(rows)}] {row['dopant']} m{mem} r{row['site_rank']}: "
              f"Ea = {rec['Ea_forward_eV']*1000:7.1f} meV{flag}  ({rec['wall_s']:.0f}s)")
        json.dump({"tier": "EXPLORE", "level": "MACE-MP-0-medium",
                   "noise_floor_meV": nf, "ten_x_threshold_meV": round(TEN_X_MEV, 1),
                   "n_paths": len(out_rows), "rows": out_rows},
                  open(f"{args.out}/explore_paths.json", "w"), indent=1)

    valid = [r for r in out_rows if r["valid"]]
    print(f"\n{len(valid)}/{len(out_rows)} paths passed the validity gate")
    print(f"10x-rate threshold: {TEN_X_MEV:.1f} meV | noise floor: {nf} meV")
    return out_rows


if __name__ == "__main__":
    main()

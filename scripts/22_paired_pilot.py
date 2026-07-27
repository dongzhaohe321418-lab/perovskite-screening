#!/usr/bin/env python
"""Objective C: undoped / GA / Sr PAIRED pilot.

The paired design is the whole point. The undoped barrier varies by sigma = 73.3 meV across
FA orientations -- larger than the 59.5 meV effect we want to detect -- so an unpaired
comparison of mean(doped) vs mean(undoped) is hopeless at any affordable n. Pairing removes
the host-configuration term:

    dEa(member) = Ea(doped, member) - Ea(undoped, member)

Both legs of every pair share the same FA orientation, the same vacancy site, and the same
migrating ion, so the configurational contribution cancels to the extent the dopant does not
change it. The quantity that then sets the required sample size is s_dEa, the standard
deviation of the PAIRED DIFFERENCES -- not sigma. Reporting s_dEa and the updated n is a
required output of this pilot.

    python scripts/22_paired_pilot.py --members 0 1 2 ... --systems undoped GA Sr
"""
import argparse, json, os, sys, time
import numpy as np
from ase.io import read, write
from ase.optimize import FIRE
from ase.mep import NEB

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import check_endpoints, check_endpoint_consistency, check_composition, structure_hash

TEN_X_MEV = 59.5

# Dopants. GA+ (guanidinium, CN3H6+) substitutes an FA A-site; Sr2+ substitutes Pb.
# Both are named in the proposal; GA is the pipeline-validation anchor.
SYSTEMS = {
    "undoped": {"kind": "none"},
    "GA":      {"kind": "A_site_GA"},
    "Sr":      {"kind": "B_site", "ion": "Sr"},
}


def mic(dv, cell):
    inv = np.linalg.inv(cell)
    f = dv @ inv
    f -= np.round(f)
    return f @ cell


def fa_molecule(at, c_index):
    """The 8 atoms of the FA whose carbon is c_index, by rank (never by cutoff)."""
    sym = np.array(at.get_chemical_symbols())
    n_all = np.flatnonzero(sym == "N")
    h_all = np.flatnonzero(sym == "H")
    nn = n_all[np.argsort(at.get_distances(c_index, n_all, mic=True))[:2]]
    mol = [int(c_index)] + [int(x) for x in nn]
    mol.append(int(h_all[np.argsort(at.get_distances(int(c_index), h_all, mic=True))[0]]))
    for N in nn:
        mol += [int(x) for x in h_all[np.argsort(at.get_distances(int(N), h_all, mic=True))[:2]]]
    return sorted(set(mol))


def apply_system(host, spec, vpos):
    """Return (doped_atoms, expected_composition_delta) or (host.copy(), {}) for undoped."""
    at = host.copy()
    if spec["kind"] == "none":
        return at, {}

    sym = np.array(at.get_chemical_symbols())
    cell = at.cell.array

    if spec["kind"] == "B_site":
        pb = np.flatnonzero(sym == "Pb")
        d = np.linalg.norm(mic(at.positions[pb] - vpos, cell), axis=1)
        i = int(pb[int(np.argmin(d))])
        at.symbols[i] = spec["ion"]
        return at, {"Pb": -1, spec["ion"]: +1}

    if spec["kind"] == "A_site_GA":
        # GA+ = C(NH2)3+ : replace the nearest FA (CH(NH2)2) with guanidinium.
        # Net change vs FA: +1 N, +1 H, C unchanged. Built by adding an NH2 in the
        # molecular plane, opposite the FA's own C-H, then deleting that H.
        c_all = np.flatnonzero(sym == "C")
        d = np.linalg.norm(mic(at.positions[c_all] - vpos, cell), axis=1)
        c = int(c_all[int(np.argmin(d))])
        mol = fa_molecule(at, c)
        msym = [at.get_chemical_symbols()[i] for i in mol]
        assert sorted(msym) == sorted(["C", "N", "N", "H", "H", "H", "H", "H"]), \
            f"A-site target is not an FA unit: {msym}"

        cpos = at.positions[c]
        nvec = [at.get_distance(c, i, mic=True, vector=True)
                for i in mol if at.get_chemical_symbols()[i] == "N"]
        # the FA's own C-H: the H closest to C
        hs = [(np.linalg.norm(at.get_distance(c, i, mic=True, vector=True)), i)
              for i in mol if at.get_chemical_symbols()[i] == "H"]
        d_ch, i_ch = min(hs)
        vch = at.get_distance(c, int(i_ch), mic=True, vector=True)
        # new N goes where that H was, at C-N bond length, keeping the molecular plane
        n_new = cpos + vch / np.linalg.norm(vch) * 1.33
        # two H on the new N, in the plane defined by the two existing C-N vectors
        plane_n = np.cross(nvec[0], nvec[1])
        plane_n /= np.linalg.norm(plane_n)
        u = vch / np.linalg.norm(vch)
        w = np.cross(plane_n, u)
        h1 = n_new + (0.34 * u + 0.95 * w) * 1.01
        h2 = n_new + (0.34 * u - 0.95 * w) * 1.01
        del at[int(i_ch)]                      # remove the FA C-H hydrogen
        from ase import Atoms as _A
        at += _A("NHH", positions=[n_new, h1, h2])
        return at, {"N": +1, "H": +1}

    raise ValueError(spec["kind"])


def build_pair(host, vac_ref_pos, calc, args):
    """Make the V_I initial/final endpoints in this host and relax them."""
    at = host.copy()
    sym = np.array(at.get_chemical_symbols())
    cell = at.cell.array
    iod = np.flatnonzero(sym == "I")
    d = np.linalg.norm(mic(at.positions[iod] - vac_ref_pos, cell), axis=1)
    vi = int(iod[int(np.argmin(d))])
    vpos = at.positions[vi].copy()
    del at[vi]

    # Migrating ion: the iodide nearest the vacancy in the post-deletion cell.
    #
    # INCIDENT: this was returned as a bare integer index, captured BEFORE the dopant
    # substitution ran. The GA substitution deletes an FA hydrogen, which shifts every index
    # above it down by one, so `fin.positions[mig] = vpos` then moved the WRONG atom -- in 8
    # of 18 members (m00,01,05,06,08,13,16,17), i.e. every member whose deleted H sat below
    # the migrating iodide. All three "MLIP blow-ups" were in that set.
    #
    # Fix: tag the atom instead of indexing it. ASE tags survive deletion and insertion, so
    # `migrating_index(at)` resolves the correct atom no matter how the cell was edited.
    sym2 = np.array(at.get_chemical_symbols())
    iod2 = np.flatnonzero(sym2 == "I")
    d2 = np.linalg.norm(mic(at.positions[iod2] - vpos, cell), axis=1)
    mig = int(iod2[int(np.argmin(d2))])
    tags = np.zeros(len(at), int)
    tags[mig] = MIG_TAG
    at.set_tags(tags)
    return at, vpos, mig


MIG_TAG = 99  # stable marker for the migrating iodide; survives atom deletion/insertion


def migrating_index(at):
    """Index of the tagged migrating iodide in the CURRENT cell, whatever was edited."""
    hits = np.flatnonzero(np.asarray(at.get_tags()) == MIG_TAG)
    assert hits.size == 1, f"expected exactly 1 tagged migrating ion, found {hits.size}"
    i = int(hits[0])
    assert at.get_chemical_symbols()[i] == "I", \
        f"tagged migrating atom is {at.get_chemical_symbols()[i]}, not I"
    return i


def run_path(ini, fin, make_calc, args, label):
    """ASE requires a SEPARATE calculator object per NEB image -- a shared one raises
    'One or more NEB images share the same calculator'. `make_calc` is a factory, not a
    calculator, so each image gets its own instance (this is what scripts/17 did)."""
    ep = {}
    for nm, a in (("initial", ini), ("final", fin)):
        a.calc = make_calc()
        oe = FIRE(a, logfile=None)
        oe.run(fmax=args.endpoint_fmax, steps=args.endpoint_steps)
        ep[nm] = {"fmax": round(float(np.linalg.norm(a.get_forces(), axis=1).max()), 4),
                  "converged": bool(oe.converged()),
                  "nsteps": int(oe.get_number_of_steps())}
    images = [ini] + [ini.copy() for _ in range(args.images)] + [fin]
    for im in images:
        im.calc = make_calc()
    neb = NEB(images, climb=True, allow_shared_calculator=False,
              method="improvedtangent")
    neb.interpolate(mic=True)
    opt = FIRE(neb, logfile=None)
    opt.run(fmax=args.fmax, steps=args.steps)
    E = np.array([im.get_potential_energy() for im in images])
    neb_fmax = float(np.linalg.norm(neb.get_forces(), axis=1).max())
    ep["neb"] = {"fmax": round(neb_fmax, 4), "converged": bool(opt.converged()),
                 "nsteps": int(opt.get_number_of_steps())}
    ep["all_converged"] = bool(ep["initial"]["converged"] and ep["final"]["converged"]
                               and opt.converged()
                               and ep["initial"]["fmax"] <= args.endpoint_fmax
                               and ep["final"]["fmax"] <= args.endpoint_fmax
                               and neb_fmax <= args.fmax)
    gate_e = check_endpoints((E - E[0]).tolist(), label=label)
    gate_c = check_endpoint_consistency(images[0].positions, images[-1].positions,
                                        ini.cell.array, label=label)
    return images, E, gate_e, gate_c, bool(opt.converged()), int(opt.get_number_of_steps()), ep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", default="results/fa_host/pool_v2")
    ap.add_argument("--vac-ref", default="results/fa_host/pool_v2/fa19cspb20i59_232_vI.extxyz")
    ap.add_argument("--members", type=int, nargs="+", required=True)
    ap.add_argument("--systems", nargs="+", default=["undoped", "GA", "Sr"])
    ap.add_argument("--images", type=int, default=5)
    ap.add_argument("--fmax", type=float, default=0.05)
    ap.add_argument("--steps", type=int, default=300)
    ap.add_argument("--endpoint-fmax", type=float, default=0.02)
    ap.add_argument("--endpoint-steps", type=int, default=800)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--dtype", default="float64")
    ap.add_argument("--out", default="results/objective2/paired_pilot")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    from mace.calculators import mace_mp
    # factory, not a single instance: ASE needs one calculator object per NEB image
    def make_calc():
        return mace_mp(model="medium", device=args.device, default_dtype=args.dtype)
    calc = make_calc()

    vac_ref = read(args.vac_ref)
    pristine = read(f"{args.pool}/fa19cs1_pb20i60_233.extxyz")
    sym0 = np.array(pristine.get_chemical_symbols())
    i0 = np.flatnonzero(sym0 == "I")
    vac_ref_pos = pristine.positions[i0[0]].copy()
    # locate the reference vacancy by comparing pristine vs the reference V_I cell
    from collections import Counter
    dif = None
    for i in i0:
        dd = np.linalg.norm(mic(vac_ref.positions - pristine.positions[i], pristine.cell.array), axis=1)
        if dd.min() > 0.5:
            dif = i
            break
    if dif is not None:
        vac_ref_pos = pristine.positions[dif].copy()

    rows = []
    for mem in args.members:
        hp = f"{args.pool}/m{mem:02d}.extxyz"
        if not os.path.exists(hp):
            print(f"  member {mem}: MISSING {hp}")
            continue
        host = read(hp)
        for sysname in args.systems:
            t0 = time.time()
            spec = SYSTEMS[sysname]
            base_vac, vpos, mig = build_pair(host, vac_ref_pos, calc, args)
            doped, delta = apply_system(base_vac, spec, vpos)
            comp = (check_composition(base_vac, doped, delta, label=f"{sysname} m{mem}")
                    if delta else {"check": "composition", "passed": True, "label": "undoped"})
            if not comp["passed"]:
                rows.append({"member": mem, "system": sysname, "valid": False,
                             "reject": f"composition: {comp.get('reason')}", "wall_s": time.time()-t0})
                print(f"  m{mem:02d} {sysname:<8} REJECT composition: {comp.get('reason')}")
                sys.stdout.flush()
                continue

            # resolve the migrating iodide in the DOPED cell -- the GA substitution
            # deletes an H, so the pre-doping integer index is stale (see MIG_TAG note)
            mig_d = migrating_index(doped)
            ini = doped.copy()
            fin = doped.copy()
            fin.positions[mig_d] = vpos
            images, E, ge, gc, conv, nst, ep = run_path(ini, fin, make_calc, args, f"{sysname}_m{mem}")
            Ea = float((E.max() - E[0]) * 1000)
            valid = bool(ge["passed"] and gc["passed"])  # SHAPE gates only
            rows.append({
                "member": mem, "system": sysname, "Ea_meV": Ea,
                "valid": bool(valid and ep["all_converged"]),
                "valid_shape_only": valid,
                "converged_all": ep["all_converged"],
                "migrating_index_doped": int(mig_d), "band_converged": conv, "nsteps": nst,
                "gate_endpoints": ge, "gate_consistency": gc, "endpoint_relax": ep,
                "profile_meV": ((E - E[0]) * 1000).tolist(),
                "structure_hash": structure_hash(doped),
                "wall_s": round(time.time() - t0, 1),
            })
            write(f"{args.out}/band_{sysname}_m{mem:02d}.extxyz", images)
            valid_all = bool(valid and ep["all_converged"])
            flag = "ok " if valid_all else "REJ"
            why = ("" if valid_all else
                   f"  [{ge.get('reason') or gc.get('reason') or 'not converged'}]")
            print(f"  m{mem:02d} {sysname:<8} Ea={Ea:8.1f} meV  {flag} conv={conv} "
                  f"{time.time()-t0:5.0f}s{why}")
            sys.stdout.flush()
        json.dump({"rows": rows}, open(f"{args.out}/paired_raw.json", "w"), indent=1)

    json.dump({"tier": "EXPLORE",
               "level": f"MACE-MP-0 medium, {args.device.upper()}, {args.dtype}, CI-NEB improvedtangent",
               "design": "PAIRED: dEa(member) = Ea(doped,member) - Ea(undoped,member)",
               "rows": rows}, open(f"{args.out}/paired_raw.json", "w"), indent=1)
    print(f"\nwrote {args.out}/paired_raw.json  ({len(rows)} rows)")


if __name__ == "__main__":
    main()

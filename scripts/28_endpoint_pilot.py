#!/usr/bin/env python
"""A1a — endpoint-protocol pilot on the 6 one-away hosts (E0).

PURPOSE: protocol feasibility ONLY. These 6 hosts are a convenience sample (selected because
2 of 3 slots already passed the admission gate), so nothing here enters the main-effect
statistics. The pilot tests whether a new endpoint-construction protocol raises usable yield,
and it reports the OLD (free-relaxation) result alongside the NEW one for every path so the
two can be compared directly.

The new protocol (design v2, NEXT_EXPERIMENT_DESIGN.md):
  1. Build the initial endpoint with the non-migrating sublattice TEMPORARILY constrained
     (fix Pb/Cs/FA-C/FA-N, relax only the local iodide cage) so the starting endpoint is the
     intended vacancy configuration and does not fall into a competing basin during setup.
  2. RELEASE all constraints and re-relax freely. The REPORTED endpoint is always the free
     one. A constrained-only barrier is a conditional constrained barrier and must never mix
     with the free-relaxation distribution.
  3. Displacement-only return test; classify pure-hop / hop+FA / band-collapse.

Two groups (design v2):
  endpoint/protocol : m3-undoped, m4-GA, m10-Sr, m18-Sr  -> can the protocol raise yield?
  mechanism-diag    : m14-GA, m27-GA                      -> still a pure hop? (no forced recovery)

Usage:
  python scripts/28_endpoint_pilot.py --pool results/fa_host/pool_v3_harmonised \
      --vac-ref results/fa_host/pool_v2/fa19cspb20i59_232_vI.extxyz \
      --pristine results/fa_host/pool_v2/fa19cs1_pb20i60_233.extxyz \
      --out results/objective2/endpoint_pilot
"""
import argparse, json, os, sys, time
import numpy as np
from ase.io import read, write
from ase.optimize import FIRE
from ase.constraints import FixAtoms
from ase.mep import NEB

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import check_endpoints, check_endpoint_consistency, structure_hash

# reuse the exact substitution + pairing logic from the corpus pipeline so the ONLY thing
# that differs between old and new is the endpoint-relaxation step
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "pp22", os.path.join(os.path.dirname(os.path.abspath(__file__)), "22_paired_pilot.py"))
pp22 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(pp22)
mic, apply_system, build_pair, migrating_index, MIG_TAG = (
    pp22.mic, pp22.apply_system, pp22.build_pair, pp22.migrating_index, pp22.MIG_TAG)

RETURN_TOL_A = 0.15   # max per-atom displacement to count as "same configuration" (from script 24)

# The 6 one-away hosts and their missing slot + group, from the audited admission record.
E0 = [
    (3,  "undoped", "endpoint"),
    (4,  "GA",      "endpoint"),
    (10, "Sr",      "endpoint"),
    (18, "Sr",      "endpoint"),
    (14, "GA",      "mechanism"),
    (27, "GA",      "mechanism"),
]


def cage_mask(at, mig_i, cutoff=3.8):
    """Atoms to RELAX during constrained endpoint construction: the migrating iodide plus
    everything within `cutoff` Angstrom of it (the local iodide cage). Everything else —
    Pb/Cs/FA backbone farther out — is fixed. Returns the FixAtoms constraint (fix the rest)."""
    cell = at.cell.array
    d = np.linalg.norm(mic(at.positions - at.positions[mig_i], cell), axis=1)
    relax = d <= cutoff
    relax[mig_i] = True
    fixed = np.flatnonzero(~relax)
    return FixAtoms(indices=fixed.tolist()), int(relax.sum())


def relax_free(a, make_calc, fmax, steps):
    a.calc = make_calc()
    a.set_constraint()  # ensure no constraint
    oe = FIRE(a, logfile=None)
    oe.run(fmax=fmax, steps=steps)
    return {"fmax": round(float(np.linalg.norm(a.get_forces(), axis=1).max()), 4),
            "converged": bool(oe.converged()), "nsteps": int(oe.get_number_of_steps()),
            "E": float(a.get_potential_energy())}


def relax_constrained_then_free(a, make_calc, fmax, steps):
    """NEW protocol: constrain non-cage atoms, relax the cage to seat the vacancy, THEN
    release everything and relax freely. Returns the FREE endpoint + both stages' records."""
    mig_i = migrating_index(a)
    cons, n_relax = cage_mask(a, mig_i)
    a.calc = make_calc()
    a.set_constraint(cons)
    oc = FIRE(a, logfile=None)
    oc.run(fmax=fmax, steps=steps)
    con_rec = {"fmax_cage": round(float(np.linalg.norm(a.get_forces(), axis=1).max()), 4),
               "nsteps": int(oc.get_number_of_steps()), "n_relaxed": n_relax,
               "converged": bool(oc.converged())}
    # release and free-relax — this is the reported endpoint
    free_rec = relax_free(a, make_calc, fmax, steps)
    return free_rec, con_rec


def neb_barrier(ini, fin, make_calc, args, label):
    images = [ini] + [ini.copy() for _ in range(args.images)] + [fin]
    for im in images:
        im.calc = make_calc()
    neb = NEB(images, climb=True, allow_shared_calculator=False, method="improvedtangent")
    neb.interpolate(mic=True)
    opt = FIRE(neb, logfile=None)
    opt.run(fmax=args.fmax, steps=args.steps)
    E = np.array([im.get_potential_energy() for im in images])
    neb_fmax = float(np.linalg.norm(neb.get_forces(), axis=1).max())
    gate_e = check_endpoints((E - E[0]).tolist(), label=label)
    gate_c = check_endpoint_consistency(images[0].positions, images[-1].positions,
                                        ini.cell.array, label=label)
    Ea = float((E.max() - E[0]) * 1000.0)
    return images, E, Ea, neb_fmax, bool(opt.converged()), gate_e, gate_c


def one_host(host, sysname, vac_ref_pos, make_calc, args):
    """Run BOTH protocols on this (host, system) path and compare."""
    out = {"member_group": None}
    # build the pair (shared setup) — build_pair returns (doped_with_vacancy, vpos, mig)
    doped, _ = apply_system(host, pp22.SYSTEMS[sysname], vac_ref_pos)
    at, vpos, mig = build_pair(doped, vac_ref_pos, make_calc(), args)
    # initial = vacancy cell; final = migrating iodide moved into the vacancy site
    ini0 = at.copy(); fin0 = at.copy()
    fin0.positions[migrating_index(fin0)] = vpos

    res = {}
    for proto, relaxer in (("old_free", "free"), ("new_constrained", "cons")):
        ini = ini0.copy(); fin = fin0.copy()
        if relaxer == "free":
            ri = relax_free(ini, make_calc, args.endpoint_fmax, args.endpoint_steps)
            rf = relax_free(fin, make_calc, args.endpoint_fmax, args.endpoint_steps)
            con_i = con_f = None
        else:
            ri, con_i = relax_constrained_then_free(ini, make_calc, args.endpoint_fmax, args.endpoint_steps)
            rf, con_f = relax_constrained_then_free(fin, make_calc, args.endpoint_fmax, args.endpoint_steps)
        images, E, Ea, nfmax, nconv, ge, gc = neb_barrier(ini, fin, make_calc, args,
                                                          f"m{args._m}-{sysname}-{proto}")
        # basin check: did the freely-relaxed endpoints stay the intended single-vacancy config?
        gc_pass = bool(gc.get("passed", False)) if isinstance(gc, dict) else bool(gc)
        res[proto] = {
            "endpoint_initial": ri, "endpoint_final": rf,
            "constrain_initial": con_i, "constrain_final": con_f,
            "Ea_meV": round(Ea, 2), "neb_fmax": round(nfmax, 4), "neb_converged": nconv,
            "gate_endpoints": ge, "gate_consistency": gc,
            "admissible": bool(nconv and ri["converged"] and rf["converged"]
                               and ri["fmax"] <= args.endpoint_fmax and rf["fmax"] <= args.endpoint_fmax
                               and nfmax <= args.fmax
                               and (ge.get("passed", False) if isinstance(ge, dict) else ge)
                               and gc_pass),
            "largest_disp_A": gc.get("largest_disp_A") if isinstance(gc, dict) else None,
            "second_disp_A": gc.get("second_disp_A") if isinstance(gc, dict) else None,
        }
    # head-to-head: barrier shift, mechanism/basin preservation
    old, new = res["old_free"], res["new_constrained"]
    res["compare"] = {
        "dEa_new_minus_old_meV": round(new["Ea_meV"] - old["Ea_meV"], 2),
        "old_admissible": old["admissible"], "new_admissible": new["admissible"],
        "new_recovers": bool(new["admissible"] and not old["admissible"]),
        "both_basin_ok": bool((old["gate_consistency"].get("passed", False) if isinstance(old["gate_consistency"], dict) else False)
                              and (new["gate_consistency"].get("passed", False) if isinstance(new["gate_consistency"], dict) else False)),
    }
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", default="results/fa_host/pool_v3_harmonised")
    ap.add_argument("--vac-ref", default="results/fa_host/pool_v2/fa19cspb20i59_232_vI.extxyz")
    ap.add_argument("--pristine", default="results/fa_host/pool_v2/fa19cs1_pb20i60_233.extxyz")
    ap.add_argument("--images", type=int, default=5)
    ap.add_argument("--fmax", type=float, default=0.05)
    ap.add_argument("--steps", type=int, default=300)
    ap.add_argument("--endpoint-fmax", type=float, default=0.02)
    ap.add_argument("--endpoint-steps", type=int, default=800)
    ap.add_argument("--cage-cutoff", type=float, default=3.8)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--dtype", default="float64")
    ap.add_argument("--out", default="results/objective2/endpoint_pilot")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    from mace.calculators import mace_mp
    def make_calc():
        return mace_mp(model="medium", device=args.device, default_dtype=args.dtype)

    # vacancy reference position (same derivation as script 22)
    vac_ref = read(args.vac_ref)
    pristine = read(args.pristine)
    sym0 = np.array(pristine.get_chemical_symbols())
    i0 = np.flatnonzero(sym0 == "I")
    vac_ref_pos = pristine.positions[i0[0]].copy()
    for i in i0:
        dd = np.linalg.norm(mic(vac_ref.positions - pristine.positions[i], pristine.cell.array), axis=1)
        if dd.min() > 0.5:
            vac_ref_pos = pristine.positions[i].copy(); break

    results = []
    t0 = time.time()
    for m, sysname, group in E0:
        host = read(f"{args.pool}/m{m:02d}.extxyz")
        args._m = m
        rec = one_host(host, sysname, vac_ref_pos, make_calc, args)
        rec["member"] = m; rec["system"] = sysname; rec["group"] = group
        rec["host_sha256_16"] = structure_hash(host)[:16]
        results.append(rec)
        c = rec["compare"]
        print(f"m{m:02d}-{sysname} [{group}]: old_adm={c['old_admissible']} "
              f"new_adm={c['new_admissible']} recovers={c['new_recovers']} "
              f"dEa={c['dEa_new_minus_old_meV']:+.1f} meV")

    n_recover = sum(1 for r in results if r["compare"]["new_recovers"])
    endpoint_recover = sum(1 for r in results if r["group"] == "endpoint" and r["compare"]["new_recovers"])
    summary = {
        "protocol": "constrained-cage-then-free-release",
        "cage_cutoff_A": args.cage_cutoff, "endpoint_fmax": args.endpoint_fmax,
        "n_hosts": len(results), "n_recovered": n_recover,
        "endpoint_group_recovered": endpoint_recover, "endpoint_group_total": 4,
        "mechanism_group": [r["member"] for r in results if r["group"] == "mechanism"],
        "A1_gate": ("feasible (>=4/6)" if n_recover >= 4 else "insufficient (<4/6) — diagnose, no physical-exclusion claim"),
        "wall_s": round(time.time() - t0, 1),
        "NOTE": "protocol feasibility ONLY; these 6 do NOT enter main-effect statistics",
    }
    json.dump({"summary": summary, "results": results},
              open(f"{args.out}/endpoint_pilot.json", "w"), indent=1, default=float)
    print("\n" + json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()

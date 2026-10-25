#!/usr/bin/env python
"""Dopant-vacancy binding-energy map (MACE level): E_b as a function of dopant-vacancy distance.

Why this exists. The paired corpus (scripts/22_paired_pilot.py) placed each additive on the
single site nearest the vacancy. That answers "does ONE near-dopant hop change its barrier" but
not "does the dopant change iodide transport": in a solid, a dopant changes vacancy transport
mainly by binding (trapping) or repelling the vacancy, which a single nearest-site barrier
cannot show. This script maps the interaction over EVERY site of the dopant's sublattice.

For host member m, with the vacancy V fixed at the corpus site and the dopant D on site j:

    E_b(j) = E[D_j + V] - E[D_j] - E[V] + E[host]

All four are relaxed with the corpus protocol (MACE-MP-0 medium, float64, FIRE, fmax 0.02,
<= 800 steps, fixed cell). Subtracting E[D_j] removes the dopant's own site energy, which is
not constant in this orientationally disordered host, so E_b(j) isolates the D-V interaction.
E_b < 0: attraction (trapping). Sites far from V should give E_b ~ 0; their spread is the
noise floor of the method on this landscape and is reported, not assumed.

Integrity checks per relaxation: converged to fmax; the vacancy stays empty (no I within
1.2 A of the vacancy site); the dopant stays on its site (< 1.0 A displacement for Sr; the GA
carbon < 1.0 A).

    python scripts/29_dopant_shell_scan.py --member 30 --dopants Sr GA --out results/objective2/dopant_shell
"""
import argparse, json, os, sys, time, importlib.util
import numpy as np
from ase.io import read, write
from ase.optimize import FIRE
from ase.geometry import find_mic

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
_spec = importlib.util.spec_from_file_location("pp", os.path.join(HERE, "22_paired_pilot.py"))
pp = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(pp)

FMAX, STEPS = 0.02, 800


def ref_vacancy_position(pool_dir, vac_ref_path):
    """Same reference vacancy site as scripts/22_paired_pilot.py main()."""
    pristine = read(os.path.join(os.path.dirname(pool_dir.rstrip("/")), "fa19cs1_pb20i60_233.extxyz")) \
        if os.path.exists(os.path.join(os.path.dirname(pool_dir.rstrip("/")), "fa19cs1_pb20i60_233.extxyz")) \
        else read("results/fa_host/fa19cs1_pb20i60_233.extxyz")
    vac_ref = read(vac_ref_path)
    cell = pristine.cell.array
    for i in np.flatnonzero(np.array(pristine.get_chemical_symbols()) == "I"):
        if np.linalg.norm(pp.mic(vac_ref.positions - pristine.positions[i], cell), axis=1).min() > 0.5:
            return pristine.positions[i].copy()
    raise RuntimeError("reference vacancy not found")


def ga_at_carbon(at, c):
    """Turn the FA whose carbon is index c into GA (same construction as apply_system)."""
    at = at.copy()
    mol = pp.fa_molecule(at, c)
    msym = sorted(at.get_chemical_symbols()[i] for i in mol)
    assert msym == sorted(["C", "N", "N", "H", "H", "H", "H", "H"]), f"not an FA unit: {msym}"
    cpos = at.positions[c]
    nvec = [at.get_distance(c, i, mic=True, vector=True) for i in mol if at.get_chemical_symbols()[i] == "N"]
    hs = [(np.linalg.norm(at.get_distance(c, i, mic=True, vector=True)), i)
          for i in mol if at.get_chemical_symbols()[i] == "H"]
    _, i_ch = min(hs)
    vch = at.get_distance(c, int(i_ch), mic=True, vector=True)
    n_new = cpos + vch / np.linalg.norm(vch) * 1.33
    pn = np.cross(nvec[0], nvec[1]); pn /= np.linalg.norm(pn)
    u = vch / np.linalg.norm(vch); w = np.cross(pn, u)
    h1 = n_new + (0.34 * u + 0.95 * w) * 1.01
    h2 = n_new + (0.34 * u - 0.95 * w) * 1.01
    del at[int(i_ch)]
    c_new = c - 1 if int(i_ch) < c else c          # deleting an earlier H shifts the carbon index
    from ase import Atoms
    at += Atoms("NHH", positions=[n_new, h1, h2])
    assert at.get_chemical_symbols()[c_new] == "C"
    return at, c_new


def relax(at, calc, label, log):
    at = at.copy(); at.calc = calc
    opt = FIRE(at, logfile=None)
    t = time.time(); opt.run(fmax=FMAX, steps=STEPS)
    f = np.linalg.norm(at.get_forces(), axis=1).max()
    r = {"label": label, "E_eV": float(at.get_potential_energy()), "fmax": float(f),
         "steps": int(opt.get_number_of_steps()), "converged": bool(f <= FMAX + 1e-9),
         "wall_s": round(time.time() - t, 1)}
    log(f"    {label:<22} E={r['E_eV']:.5f}  fmax={f:.4f}  steps={r['steps']:>3}  {r['wall_s']:6.1f}s")
    return at, r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--member", type=int, required=True)
    ap.add_argument("--dopants", nargs="+", default=["Sr", "GA"])
    ap.add_argument("--pool", default="results/fa_host/pool_v3_harmonised")
    ap.add_argument("--vac-ref", default="results/fa_host/pool_v2/fa19cspb20i59_232_vI.extxyz")
    ap.add_argument("--sites", type=int, default=0, help="limit sites per dopant (0 = all; pilot use)")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--out", default="results/objective2/dopant_shell")
    args = ap.parse_args()

    import torch; torch.set_num_threads(args.threads)
    from mace.calculators import mace_mp
    calc = mace_mp(model="medium", device=args.device, default_dtype="float64")
    os.makedirs(args.out, exist_ok=True)
    outp = os.path.join(args.out, f"shell_m{args.member:02d}.json")
    logf = open(os.path.join(args.out, f"shell_m{args.member:02d}.log"), "a")
    def log(s): print(s); logf.write(s + "\n"); logf.flush()

    ref = ref_vacancy_position(args.pool, args.vac_ref)
    host = read(f"{args.pool}/m{args.member:02d}.extxyz")
    cell = host.cell.array
    sym = np.array(host.get_chemical_symbols())
    vac_struct, vpos, _ = pp.build_pair(host, ref, None, None)
    iod = np.flatnonzero(sym == "I")
    vi = int(iod[np.argmin(np.linalg.norm(pp.mic(host.positions[iod] - ref, cell), axis=1))])
    to_vac_index = lambda j: j if j < vi else j - 1   # index map host -> vacancy cell
    # True minimum image (ase.geometry.find_mic). pp.mic only rounds fractional coordinates,
    # which is not the minimum image in this skewed cell (angles 63/117/84 deg) -- review MIC-1.
    D = lambda p: float(find_mic(np.atleast_2d(p - vpos), cell, pbc=True)[1][0])

    res = {"member": args.member, "protocol": {"model": "MACE-MP-0 medium", "dtype": "float64",
           "optimizer": "FIRE", "fmax": FMAX, "steps": STEPS, "cell": "fixed"},
           "vacancy_host_index": vi, "vacancy_pos": vpos.tolist(), "rows": []}
    if os.path.exists(outp):
        old = json.load(open(outp))
        if old.get("protocol") != res["protocol"] or old.get("member") != res["member"] \
                or old.get("vacancy_host_index") != res["vacancy_host_index"]:
            raise SystemExit(f"{outp} was written with a different protocol/member/vacancy; "
                             "move it aside instead of mixing results (review: resume guard)")
        res = old
    done = {(r["dopant"], r["site_host_index"]) for r in res["rows"]}

    log(f"m{args.member:02d}: references")
    if "E_host" not in res:
        _, rh = relax(host, calc, "host", log)
        av0, rv = relax(vac_struct, calc, "vacancy", log)
        # the shared references enter EVERY E_b, so an unconverged or rearranged reference
        # would bias the whole map: refuse to continue (review: ungated references)
        if not (rh["converged"] and rv["converged"]):
            raise SystemExit(f"reference relaxation not converged: host {rh['fmax']:.4f}, vac {rv['fmax']:.4f}")
        s0 = np.array(av0.get_chemical_symbols()); i0 = np.flatnonzero(s0 == "I")
        gap0 = float(find_mic(av0.positions[i0] - vpos, cell, pbc=True)[1].min())
        if gap0 <= 1.2:
            raise SystemExit(f"vacancy reference relaxed shut (nearest I {gap0:.2f} A from the site)")
        rv["nearest_I_to_vacancy_site_A"] = round(gap0, 3)
        res["E_host"], res["E_vac"] = rh, rv
        json.dump(res, open(outp, "w"), indent=1)

    def vacancy_still_empty(at):
        s = np.array(at.get_chemical_symbols()); ii = np.flatnonzero(s == "I")
        return float(find_mic(at.positions[ii] - vpos, cell, pbc=True)[1].min())

    for dop in args.dopants:
        if dop == "Sr":
            sites = list(np.flatnonzero(sym == "Pb"))
        elif dop == "GA":
            sites = list(np.flatnonzero(sym == "C"))
        else:
            raise ValueError(dop)
        sites.sort(key=lambda j: D(host.positions[j]))
        if args.sites: sites = sites[: args.sites]
        for j in sites:
            j = int(j)
            if (dop, j) in done: continue
            dist = D(host.positions[j])
            log(f"m{args.member:02d} {dop} site {j} (d = {dist:.2f} A)")
            if dop == "Sr":
                d0 = host.copy(); d0.symbols[j] = "Sr"
                dv = vac_struct.copy(); dv.symbols[to_vac_index(j)] = "Sr"
                track0, trackv = j, to_vac_index(j)
            else:
                d0, track0 = ga_at_carbon(host, j)
                dv, trackv = ga_at_carbon(vac_struct, to_vac_index(j))
            a0, r0 = relax(d0, calc, f"{dop}@{j} no-vac", log)
            av, rv = relax(dv, calc, f"{dop}@{j} +vac", log)
            disp0 = float(find_mic(np.atleast_2d(a0.positions[track0] - d0.positions[track0]), cell, pbc=True)[1][0])
            dispv = float(find_mic(np.atleast_2d(av.positions[trackv] - dv.positions[trackv]), cell, pbc=True)[1][0])
            gap = vacancy_still_empty(av)
            Eb = (rv["E_eV"] - r0["E_eV"] - res["E_vac"]["E_eV"] + res["E_host"]["E_eV"]) * 1000
            ok = r0["converged"] and rv["converged"] and gap > 1.2 and disp0 < 1.0 and dispv < 1.0
            res["rows"].append({"dopant": dop, "site_host_index": j, "d_dopant_vacancy_A": round(dist, 3),
                                "Eb_meV": round(Eb, 2), "valid": bool(ok),
                                "nearest_I_to_vacancy_site_A": round(gap, 3),
                                "dopant_displacement_A": [round(disp0, 3), round(dispv, 3)],
                                "no_vac": r0, "with_vac": rv})
            log(f"    -> E_b = {Eb:+8.1f} meV   {'ok' if ok else 'INVALID'}")
            json.dump(res, open(outp, "w"), indent=1)
    log(f"m{args.member:02d}: done, {len(res['rows'])} rows -> {outp}")


if __name__ == "__main__":
    main()

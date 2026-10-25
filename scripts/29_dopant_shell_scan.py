#!/usr/bin/env python
"""Dopant-vacancy binding-energy map (MACE level): E_b as a function of dopant-vacancy distance.

Why this exists. The paired corpus (scripts/22_paired_pilot.py) placed each additive on the
single site nearest the vacancy. That answers "does ONE near-dopant hop change its barrier" but
not "does the dopant change iodide transport": in a solid, a dopant changes vacancy transport
mainly by binding (trapping) or repelling the vacancy. This script maps the interaction over
the sites of the dopant's sublattice.

For host member m, with the vacancy V fixed at the corpus site and the dopant D on site j:

    E_b(j) = E[D_j + V] - E[D_j] - E[V] + E[host]          (E_b < 0: attraction / trapping)

PROTOCOL v2 (2026-10-25, after the design review; v1 = commit 5d9a3ca, exploratory only):

* Warm start (review EB-BASIN). host and V are relaxed first; D_j is built on the RELAXED host
  and D_j+V on the RELAXED V. Far from the defects the doped cell then starts in its partner's
  basin, so FA reorientations elsewhere in the cell cannot enter E_b. v1 relaxed all four cells
  from the unrelaxed pool geometry, and any basin hop anywhere entered E_b at full size.
* Staged depth (review EB-DEPTH). Every relaxation is run through fmax stages (default 0.02,
  0.01, 0.005 eV/A; FIRE restarted per stage, <= --steps per stage) and the energy is recorded
  at each stage. E_b(stage) uses the doped cells at that stage and the fully relaxed references,
  so the depth convergence of E_b is measured, not assumed. On this soft FA landscape fmax 0.02
  is not energy-converged.
* Basin check. For D_j vs host and for D_j+V vs V: atoms more than --basin-rcut (6 A) from both
  the dopant and the vacancy site are matched between partners; the largest displacement and
  the largest FA-axis rotation (C -> midpoint of the two N) are recorded. A row is valid at a
  stage only if, at that stage, both pairs stay below 0.25 A and 20 deg, both cells converged,
  the vacancy site stays empty (no I within 1.2 A) and the dopant stays on its site (< 1.0 A).
  v2.1 (PLAN amendment j): these checks are made and stored for EVERY stage (row["by_stage"]),
  and the structures of every stage are saved; in v2 they were made on the final stage only,
  so a far-field basin hop in the deepest stage discarded the whole row.
* Distances are true minimum image (ase.geometry.find_mic); pp.mic is not minimum image beyond
  half the smallest perpendicular height (7.28 A) of this skewed cell (review MIC-1).

The 'far' reference set and the near-minus-far analysis are defined in the analysis step, not
here (PLAN amendment: Pb d > 8.5 A, C d > 9.0 A, from the geometric shell gaps).
References may use their own stage list (--ref-fmax-stages) or be reused from the pilot
(--ref-from); E_b(stage) always uses the fully relaxed references (PLAN amendment g item 4).

    python scripts/29_dopant_shell_scan.py --member 30 --dopants Sr GA --near 2 --far 3 \
        --out results/objective2/dopant_shell/v2
"""
import argparse, hashlib, json, os, shutil, sys, time, importlib.util
import numpy as np
from ase.io import read, write
from ase.optimize import FIRE
from ase.geometry import find_mic

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
_spec = importlib.util.spec_from_file_location("pp", os.path.join(HERE, "22_paired_pilot.py"))
pp = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(pp)

PROTOCOL_VERSION = "v2.1-stage-validity"   # v2 + every check per fmax stage (PLAN amendment j)


def dump_atomic(obj, path):
    """Write JSON via a temp file + rename, so a kill (spot node) never truncates the record."""
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=1); fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp, path)


def ref_vacancy_position(pool_dir, vac_ref_path):
    """Same reference vacancy site as scripts/22_paired_pilot.py main()."""
    cand = os.path.join(os.path.dirname(pool_dir.rstrip("/")), "fa19cs1_pb20i60_233.extxyz")
    pristine = read(cand if os.path.exists(cand) else "results/fa_host/fa19cs1_pb20i60_233.extxyz")
    vac_ref = read(vac_ref_path)
    cell = pristine.cell.array
    for i in np.flatnonzero(np.array(pristine.get_chemical_symbols()) == "I"):
        if find_mic(vac_ref.positions - pristine.positions[i], cell, pbc=True)[1].min() > 0.5:
            return pristine.positions[i].copy()
    raise RuntimeError("reference vacancy not found")


def ga_at_carbon(at, c):
    """Turn the FA whose carbon is index c into GA (same construction as apply_system).
    Returns (atoms, new carbon index, index of the deleted C-H hydrogen in the INPUT atoms)."""
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
    return at, c_new, int(i_ch)


def relax_staged(at, calc, label, log, stages, steps):
    """FIRE through the fmax stages; returns (final atoms, record, per-stage snapshots)."""
    from ase.calculators.singlepoint import SinglePointCalculator
    at = at.copy(); at.calc = calc
    rec = {"label": label, "stages": []}
    snaps = []
    t = time.time()
    for fm in stages:
        opt = FIRE(at, logfile=None)            # fresh FIRE per stage; velocities reset
        opt.run(fmax=fm, steps=steps)
        f = float(np.linalg.norm(at.get_forces(), axis=1).max())
        rec["stages"].append({"fmax_target": fm, "E_eV": float(at.get_potential_energy()), "fmax": f,
                              "steps": int(opt.get_number_of_steps()), "converged": bool(f <= fm + 1e-9)})
        snap = at.copy()                        # frozen results: the shared calculator moves on
        snap.calc = SinglePointCalculator(snap, energy=float(at.get_potential_energy()), forces=at.get_forces().copy())
        snaps.append(snap)
    # The MACE calculator is shared between structures: freeze THIS structure's results so a later
    # write() cannot attach another cell's forces (found in the v2 smoke test).
    e_fin, f_fin = float(at.get_potential_energy()), at.get_forces().copy()
    at.calc = SinglePointCalculator(at, energy=e_fin, forces=f_fin)
    rec.update({"E_eV": rec["stages"][-1]["E_eV"], "fmax": rec["stages"][-1]["fmax"],
                "converged": rec["stages"][-1]["converged"], "wall_s": round(time.time() - t, 1)})
    log(f"    {label:<22} " + "  ".join(f"[{s['fmax_target']}] E={s['E_eV']:.5f} n={s['steps']}" for s in rec["stages"])
        + f"  {rec['wall_s']:.0f}s")
    return at, rec, snaps


def basin_dev(partner, doped, keep, centres, cell, rcut):
    """Largest displacement and FA-axis rotation between relaxed partner and relaxed doped cell,
    over atoms farther than rcut from every centre. keep = partner indices that survive the
    build, in order; doped atom k' (k' < len(keep)) corresponds to partner atom keep[k']."""
    keep = np.asarray(keep)
    pa, pb = partner.positions[keep], doped.positions[: len(keep)]
    dmin = np.min([find_mic(pa - c, cell, pbc=True)[1] for c in centres], axis=0)
    far = dmin > rcut
    dr = find_mic(pb[far] - pa[far], cell, pbc=True)[1]
    inv = {int(k): i for i, k in enumerate(keep)}
    sym = partner.get_chemical_symbols()
    ang = [0.0]
    for c in [int(k) for k in keep[far] if sym[int(k)] == "C"]:
        mol = pp.fa_molecule(partner, c)
        ns = [i for i in mol if sym[i] == "N"]
        if len(ns) != 2 or any(i not in inv for i in ns):
            continue
        def axis(P, ic, i1, i2):
            v1 = find_mic(np.atleast_2d(P[i1] - P[ic]), cell, pbc=True)[0][0]
            v2 = find_mic(np.atleast_2d(P[i2] - P[ic]), cell, pbc=True)[0][0]
            a = 0.5 * (v1 + v2); return a / np.linalg.norm(a)
        aa = axis(partner.positions, c, ns[0], ns[1])
        bb = axis(doped.positions, inv[c], inv[ns[0]], inv[ns[1]])
        ang.append(float(np.degrees(np.arccos(np.clip(aa @ bb, -1, 1)))))
    return {"n_far": int(far.sum()), "max_dr_A": float(dr.max()) if dr.size else 0.0,
            "max_fa_rot_deg": float(max(ang))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--member", type=int, required=True)
    ap.add_argument("--dopants", nargs="+", default=["Sr", "GA"])
    ap.add_argument("--pool", default="results/fa_host/pool_v3_harmonised")
    ap.add_argument("--vac-ref", default="results/fa_host/pool_v2/fa19cspb20i59_232_vI.extxyz")
    ap.add_argument("--near", type=int, default=0, help="only the N nearest sites (with --far)")
    ap.add_argument("--far", type=int, default=0, help="only the M farthest sites (with --near)")
    ap.add_argument("--site-list", type=int, nargs="+", default=None, help="only these host site indices")
    ap.add_argument("--fmax-stages", type=float, nargs="+", default=[0.02, 0.01, 0.005],
                    help="stages for the doped cells D_j and D_j+V")
    ap.add_argument("--ref-fmax-stages", type=float, nargs="+", default=[0.02, 0.01, 0.005],
                    help="stages for the host and V references (PLAN amendments d4/g4/h: always to 0.005)")
    ap.add_argument("--ref-from", default=None,
                    help="reuse relaxed references (shell_mNN.json + *_relaxed.extxyz) from this output dir")
    ap.add_argument("--steps", type=int, default=3000, help="max FIRE steps per stage")
    ap.add_argument("--basin-rcut", type=float, default=6.0)
    ap.add_argument("--save-structures", action=argparse.BooleanOptionalAction, default=True)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--out", default="results/objective2/dopant_shell/v2")
    args = ap.parse_args()

    import torch; torch.set_num_threads(args.threads)
    from mace.calculators import mace_mp
    calc = mace_mp(model="medium", device=args.device, default_dtype="float64")
    os.makedirs(args.out, exist_ok=True)
    tag = f"m{args.member:02d}"
    outp = os.path.join(args.out, f"shell_{tag}.json")
    logf = open(os.path.join(args.out, f"shell_{tag}.log"), "a")
    def log(s): print(s, flush=True); logf.write(s + "\n"); logf.flush()

    ref = ref_vacancy_position(args.pool, args.vac_ref)
    host = read(f"{args.pool}/{tag}.extxyz")
    cell = host.cell.array
    sym = np.array(host.get_chemical_symbols())
    vac_struct, vpos, _ = pp.build_pair(host, ref, None, None)
    iod = np.flatnonzero(sym == "I")
    vi = int(iod[np.argmin(find_mic(host.positions[iod] - ref, cell, pbc=True)[1])])
    to_vac_index = lambda j: j if j < vi else j - 1   # index map host -> vacancy cell
    D = lambda p: float(find_mic(np.atleast_2d(p - vpos), cell, pbc=True)[1][0])

    stages = sorted(args.fmax_stages, reverse=True)
    ref_stages = sorted(args.ref_fmax_stages, reverse=True)
    if min(ref_stages) > 0.005 + 1e-12:
        raise SystemExit(f"references must reach fmax 0.005 (PLAN amendment d item 4); got {ref_stages}")
    protocol = {"version": PROTOCOL_VERSION, "model": "MACE-MP-0 medium", "dtype": "float64",
                "optimizer": "FIRE (restarted per stage)", "fmax_stages": stages,
                "steps_per_stage": args.steps, "cell": "fixed", "basin_rcut_A": args.basin_rcut,
                "warm_start": "D_j from relaxed host, D_j+V from relaxed V"}
    if ref_stages != stages:                    # key only when different: older outputs stay resumable
        protocol["ref_fmax_stages"] = ref_stages
    res = {"member": args.member,
           "protocol": protocol,
           "inputs": {"pool": os.path.abspath(args.pool), "vac_ref": os.path.abspath(args.vac_ref),
                      "host_sha256": hashlib.sha256(host.positions.tobytes() + host.numbers.tobytes()).hexdigest(),
                      "vpos": np.round(vpos, 4).tolist()},
           "vacancy_host_index": vi, "rows": []}
    if os.path.exists(outp):
        old = json.load(open(outp))
        for k in ("protocol", "inputs", "member", "vacancy_host_index"):
            if old.get(k) != res[k]:
                raise SystemExit(f"{outp}: '{k}' differs from this run; move it aside instead of mixing results")
        res = old
    done = {(r["dopant"], r["site_host_index"]) for r in res["rows"]}
    hpath, vpath = (os.path.join(args.out, f"{tag}_host_relaxed.extxyz"),
                    os.path.join(args.out, f"{tag}_vac_relaxed.extxyz"))

    if "E_host" not in res and args.ref_from:
        src = json.load(open(os.path.join(args.ref_from, f"shell_{tag}.json")))
        for k in ("inputs", "member", "vacancy_host_index"):
            if src.get(k) != res[k]:
                raise SystemExit(f"--ref-from: '{k}' differs from this run")
        for k in ("E_host", "E_vac"):
            got = [st["fmax_target"] for st in src[k]["stages"]]
            if got != ref_stages or not src[k]["converged"]:
                raise SystemExit(f"--ref-from: {k} stages {got} (converged {src[k]['converged']}) != {ref_stages}")
        for fn in (f"{tag}_host_relaxed.extxyz", f"{tag}_vac_relaxed.extxyz"):
            shutil.copy2(os.path.join(args.ref_from, fn), os.path.join(args.out, fn))
        res["E_host"], res["E_vac"] = src["E_host"], src["E_vac"]
        res["references_from"] = os.path.abspath(args.ref_from)
        log(f"{tag}: references reused from {args.ref_from} (stages {ref_stages})")
        dump_atomic(res, outp)
    if "E_host" not in res:
        log(f"{tag}: references ({PROTOCOL_VERSION}, stages {ref_stages})")
        ah, rh, _ = relax_staged(host, calc, "host", log, ref_stages, args.steps)
        av, rv, _ = relax_staged(vac_struct, calc, "vacancy", log, ref_stages, args.steps)
        if not (rh["converged"] and rv["converged"]):
            raise SystemExit(f"reference relaxation not converged: host {rh['fmax']:.4f}, vac {rv['fmax']:.4f}")
        gap0 = float(find_mic(av.positions[np.array(av.get_chemical_symbols()) == "I"] - vpos, cell, pbc=True)[1].min())
        if gap0 <= 1.2:
            raise SystemExit(f"vacancy reference relaxed shut (nearest I {gap0:.2f} A from the site)")
        rv["nearest_I_to_vacancy_site_A"] = round(gap0, 3)
        write(hpath, ah); write(vpath, av)
        res["E_host"], res["E_vac"] = rh, rv
        dump_atomic(res, outp)
    host_r, vac_r = read(hpath), read(vpath)          # warm-start partners (also on resume)

    def gap_of(at):
        s = np.array(at.get_chemical_symbols())
        return float(find_mic(at.positions[s == "I"] - vpos, cell, pbc=True)[1].min())

    for dop in args.dopants:
        sites = list(np.flatnonzero(sym == ("Pb" if dop == "Sr" else "C")))
        sites.sort(key=lambda j: D(host.positions[j]))
        if args.near or args.far:
            sites = sites[: args.near] + (sites[-args.far:] if args.far else [])
        if args.site_list is not None:
            sites = [j for j in sites if int(j) in set(args.site_list)]
        for j in sites:
            j = int(j)
            if (dop, j) in done:
                continue
            dist = D(host.positions[j])
            log(f"{tag} {dop} site {j} (d = {dist:.2f} A)")
            jv = to_vac_index(j)
            if dop == "Sr":
                d0 = host_r.copy(); d0.symbols[j] = "Sr"
                dv = vac_r.copy(); dv.symbols[jv] = "Sr"
                t0, tv, keep0, keepv = j, jv, range(len(host_r)), range(len(vac_r))
            else:
                d0, t0, ich0 = ga_at_carbon(host_r, j)
                dv, tv, ichv = ga_at_carbon(vac_r, jv)
                keep0 = [k for k in range(len(host_r)) if k != ich0]
                keepv = [k for k in range(len(vac_r)) if k != ichv]
            a0, r0, s0n = relax_staged(d0, calc, f"{dop}@{j} no-vac", log, stages, args.steps)
            av, rv, svn = relax_staged(dv, calc, f"{dop}@{j} +vac", log, stages, args.steps)
            if args.save_structures:
                write(os.path.join(args.out, f"{tag}_{dop}{j}_novac_relaxed.extxyz"), a0)
                write(os.path.join(args.out, f"{tag}_{dop}{j}_vac_relaxed.extxyz"), av)
                for fm, x0, xv in list(zip(stages, s0n, svn))[:-1]:     # earlier stages (amendment j)
                    write(os.path.join(args.out, f"{tag}_{dop}{j}_novac_fmax{fm}.extxyz"), x0)
                    write(os.path.join(args.out, f"{tag}_{dop}{j}_vac_fmax{fm}.extxyz"), xv)
            dpos = host_r.positions[j]
            Eh, Ev = res["E_host"]["E_eV"], res["E_vac"]["E_eV"]
            by_stage = {}
            for k, fm in enumerate(stages):     # every validity check at every stage (amendment j)
                x0, xv = s0n[k], svn[k]
                b0 = basin_dev(host_r, x0, keep0, [dpos, vpos], cell, args.basin_rcut)
                bv = basin_dev(vac_r, xv, keepv, [dpos, vpos], cell, args.basin_rcut)
                disp0 = float(find_mic(np.atleast_2d(x0.positions[t0] - d0.positions[t0]), cell, pbc=True)[1][0])
                dispv = float(find_mic(np.atleast_2d(xv.positions[tv] - dv.positions[tv]), cell, pbc=True)[1][0])
                gap = gap_of(xv)
                conv = r0["stages"][k]["converged"] and rv["stages"][k]["converged"]
                bok = all(b["max_dr_A"] < 0.25 and b["max_fa_rot_deg"] < 20.0 for b in (b0, bv))
                okk = conv and gap > 1.2 and disp0 < 1.0 and dispv < 1.0 and bok
                by_stage[str(fm)] = {"Eb_meV": round((rv["stages"][k]["E_eV"] - r0["stages"][k]["E_eV"] - Ev + Eh) * 1000, 2),
                                     "valid": bool(okk), "converged": bool(conv), "basin_ok": bool(bok),
                                     "basin_novac_vs_host": b0, "basin_vac_vs_V": bv,
                                     "nearest_I_to_vacancy_site_A": round(gap, 3),
                                     "dopant_displacement_A": [round(disp0, 3), round(dispv, 3)]}
            fin = by_stage[str(stages[-1])]
            res["rows"].append({"dopant": dop, "site_host_index": j, "d_dopant_vacancy_A": round(dist, 3),
                                "Eb_meV": fin["Eb_meV"], "Eb_by_stage_meV": {k: v["Eb_meV"] for k, v in by_stage.items()},
                                "valid": fin["valid"], "basin_ok": fin["basin_ok"],
                                "basin_novac_vs_host": fin["basin_novac_vs_host"], "basin_vac_vs_V": fin["basin_vac_vs_V"],
                                "nearest_I_to_vacancy_site_A": fin["nearest_I_to_vacancy_site_A"],
                                "dopant_displacement_A": fin["dopant_displacement_A"],
                                "by_stage": by_stage, "no_vac": r0, "with_vac": rv})
            log("    -> " + "  ".join(f"[{k}] E_b={v['Eb_meV']:+.1f} dr={v['basin_novac_vs_host']['max_dr_A']:.2f}/"
                                      f"{v['basin_vac_vs_V']['max_dr_A']:.2f} rot={v['basin_novac_vs_host']['max_fa_rot_deg']:.0f}/"
                                      f"{v['basin_vac_vs_V']['max_fa_rot_deg']:.0f} {'ok' if v['valid'] else 'INVALID'}"
                                      for k, v in by_stage.items()))
            dump_atomic(res, outp)
    log(f"{tag}: done, {len(res['rows'])} rows -> {outp}")


if __name__ == "__main__":
    main()

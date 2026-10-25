#!/usr/bin/env python
"""QE inputs for WP2c (DFT E_b), WP2d (charge state) and the WP2e E_b quartet, from the WP1 v2
MACE-relaxed structures (scripts/29 --save-structures). PLAN WP2c/2d, amendments c (items 4, 5)
and d (shells).

Site selection is geometric and fixed before any v2 E_b was read (PLAN amendment 2026-10-25f);
only VALID WP1 rows are used, and every choice is written to wp2cde_selection.json:

    Sr hinge  : of the two near-shell Pb, the one closer to the migrating iodide (the iodide
                nearest the vacancy site, as in scripts/22) -- it holds the hopping ion
    Sr flank  : the other near-shell Pb
    Sr/GA mid : valid mid-shell site whose distance is closest to the median mid-shell distance
    Sr/GA far : valid far-shell site whose distance is closest to the median far-shell distance
    GA near   : nearest valid FA site

WP2c (every host): host, V, and D_j / D_j+V for the seven sites; neutral; labels match
scripts/33 (<host>_host, <host>_vac, <host>_<dop><j>_novac|vac).
WP2d (--charged-host only): q = +1 single points of the vacancy cells V, Sr hinge, Sr far, GA near,
GA far, and of band images 0 and 3 of undoped and Sr (labels end in _q1, never used for training).
WP2e quartet (--charged-host): host, V, Sr-hinge D and D+V, fixed-cell DFT relaxation (_relax).

    python scripts/36_wp2cde_inputs.py --v2 /data/work/v2 --hosts 30 21 05 --charged-host 30 \
        --bands /data/work/bands --jobs /data/jobs
"""
import argparse, hashlib, json, os, sys, importlib.util
import numpy as np
from ase.io import read
from ase.geometry import find_mic

HERE = os.path.dirname(os.path.abspath(__file__))
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
a30 = _load("a30", "30_qe_singlepoint.py")
a29 = _load("a29", "29_dopant_shell_scan.py")
a34 = _load("a34", "34_dopant_shell_analysis.py")


def emit(atoms, label, jobs, campaign, source, calc="scf", charge=0):
    at = atoms.copy(); at.calc = None; at.set_tags([0] * len(at))
    d = os.path.join(jobs, campaign, label)
    path = a30.write_input(at, label, d, "R", calc, charge)
    json.dump({"label": label, "source": source, "natoms": len(at), "formula": at.get_chemical_formula(),
               "fingerprint": {**a30.FINGERPRINT, "calculation": calc, "tot_charge": charge},
               "input_sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()},
              open(os.path.join(d, f"{label}.meta.json"), "w"), indent=1)
    return path


def closest_to_median(cands, all_d):
    med = float(np.median(all_d))
    return min(cands, key=lambda r: (abs(r["d_dopant_vacancy_A"] - med), r["site_host_index"]))


def select(res, host, vpos, cell):
    rows = res["rows"]
    sym = np.array(host.get_chemical_symbols())
    # migrating iodide: nearest iodide to the vacancy site after deleting the vacancy iodide
    iod = [i for i in np.flatnonzero(sym == "I") if i != res["vacancy_host_index"]]
    dI = find_mic(host.positions[iod] - vpos, cell, pbc=True)[1]
    mig = int(iod[int(np.argmin(dI))])
    sel, notes = {}, []
    for dop in ("Sr", "GA"):
        R = [r for r in rows if r["dopant"] == dop]
        sh = {r["site_host_index"]: a34.shell(dop, r["d_dopant_vacancy_A"]) for r in R}
        V = [r for r in R if r["valid"]]
        if dop == "Sr":
            near = sorted([r for r in R if sh[r["site_host_index"]] == "near"], key=lambda r: r["site_host_index"])
            assert len(near) == 2, f"expected 2 near-shell Pb, got {len(near)}"
            dm = [float(find_mic(np.atleast_2d(host.positions[r["site_host_index"]] - host.positions[mig]),
                                 cell, pbc=True)[1][0]) for r in near]
            order = np.argsort(dm)
            notes.append(f"Sr near Pb {[r['site_host_index'] for r in near]}: Pb-I(mig {mig}) = "
                         f"{[round(x, 3) for x in dm]} A")
            if dm[order[1]] - dm[order[0]] < 0.5:
                notes.append("WARNING: hinge assignment ambiguous (Pb-I(mig) distances within 0.5 A)")
            for name, r in (("Sr_hinge", near[order[0]]), ("Sr_flank", near[order[1]])):
                if r["valid"]:
                    sel[name] = r
                else:
                    notes.append(f"{name} site {r['site_host_index']} invalid: not computed")
        else:
            nv = sorted([r for r in V if sh[r["site_host_index"]] == "near"], key=lambda r: r["d_dopant_vacancy_A"])
            if nv:
                sel["GA_near"] = nv[0]
        for s in ("mid", "far"):
            alld = [r["d_dopant_vacancy_A"] for r in R if sh[r["site_host_index"]] == s]
            cands = [r for r in V if sh[r["site_host_index"]] == s]
            if cands:
                sel[f"{dop}_{s}"] = closest_to_median(cands, alld)
            else:
                notes.append(f"{dop}_{s}: no valid site")
    return sel, mig, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v2", required=True, help="WP1 v2 output dir (shell_mNN.json + *_relaxed.extxyz)")
    ap.add_argument("--hosts", nargs="+", required=True)
    ap.add_argument("--charged-host", default="30")
    ap.add_argument("--bands", required=True)
    ap.add_argument("--pool", default="results/fa_host/pool_v3_harmonised")
    ap.add_argument("--jobs", required=True)
    a = ap.parse_args()
    out = {}
    for h in [f"m{int(x):02d}" for x in a.hosts]:
        res = json.load(open(os.path.join(a.v2, f"shell_{h}.json")))
        host = read(os.path.join(a.pool, f"{h}.extxyz")); cell = host.cell.array
        vpos = np.array(res["inputs"]["vpos"])
        sel, mig, notes = select(res, host, vpos, cell)
        f = lambda name: os.path.join(a.v2, name)
        jobs = {f"{h}_host": f(f"{h}_host_relaxed.extxyz"), f"{h}_vac": f(f"{h}_vac_relaxed.extxyz")}
        for r in sel.values():
            j, dop = r["site_host_index"], r["dopant"]
            for k in ("novac", "vac"):
                jobs[f"{h}_{dop}{j}_{k}"] = f(f"{h}_{dop}{j}_{k}_relaxed.extxyz")
        for lab, src in jobs.items():
            emit(read(src), lab, a.jobs, "wp2c", os.path.basename(src))
        rec = {"migrating_iodide_host_index": mig, "notes": notes,
               "sites": {k: {"site": r["site_host_index"], "d_A": r["d_dopant_vacancy_A"]} for k, r in sel.items()},
               "wp2c_labels": sorted(jobs)}
        if h == f"m{int(a.charged_host):02d}":
            q1 = {f"{h}_vac_q1": jobs[f"{h}_vac"]}
            for k in ("Sr_hinge", "Sr_far", "GA_near", "GA_far"):
                if k in sel:
                    r = sel[k]; q1[f"{h}_{r['dopant']}{r['site_host_index']}_vac_q1"] = \
                        jobs[f"{h}_{r['dopant']}{r['site_host_index']}_vac"]
            for lab, src in q1.items():
                emit(read(src), lab, a.jobs, "wp2d", os.path.basename(src), charge=1)
            for sysn in ("undoped", "Sr"):
                bf = os.path.join(a.bands, f"band_{sysn}_{h}.extxyz")
                for img in (0, 3):
                    lab = f"{h}_{sysn}_img{img}_q1"; q1[lab] = f"{bf}@{img}"
                    emit(read(bf, index=img), lab, a.jobs, "wp2d", f"{os.path.basename(bf)}@{img}", charge=1)
            rq = {}
            if "Sr_hinge" in sel:
                j = sel["Sr_hinge"]["site_host_index"]
                for base in (f"{h}_host", f"{h}_vac", f"{h}_Sr{j}_novac", f"{h}_Sr{j}_vac"):
                    rq[f"{base}_relax"] = jobs[base]
                    emit(read(jobs[base]), f"{base}_relax", a.jobs, "wp2e", os.path.basename(jobs[base]), calc="relax")
            rec.update({"wp2d_labels": sorted(q1), "wp2e_quartet_labels": sorted(rq)})
        out[h] = rec
        print(h, json.dumps(rec, indent=1))
    json.dump(out, open(os.path.join(a.v2, "wp2cde_selection.json"), "w"), indent=1)


if __name__ == "__main__":
    main()

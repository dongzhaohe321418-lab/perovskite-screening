#!/usr/bin/env python
"""DFT analysis of WP2c (E_b transfer), WP2d (charge state), WP2e (relaxation bias) and the WP2a
smearing/spin rows. PLAN criteria 4 and 5 with amendments c (items 4-6), g (items 1, 2) and h (item 2).

Energies are QE free energies F ("! total energy"), plain PBE, R point (scripts/30); E_F from
"the Fermi energy is". MACE E_b comes from the WP1 shell JSON of the same structures (scripts/29,
final stage = adopted depth, amendment h item 4).

WP2c, per host and dopant, for every selected site j (scripts/36, wp2cde_selection.json):
    E_b^DFT(j)  = F[D_j+V] - F[D_j] - F[V] + F[host]                      (q = 0)
    far-referenced: E_b(j) - E_b(far site), at the same level (criterion 4 as amended by g item 1)
    criterion 4: |far-ref MACE - far-ref DFT| < 25 meV at every non-far site, and the near-minus-far
                 sign agrees between MACE and DFT
    band-term residual (h item 2): [E_F(D_j+V) - E_F(V)] - [same at the far site]
WP2d (charged host): E_b(q=+1) = F[D_j+V]^+ - F[D_j] - F[V]^+ + F[host]; rule (c item 4 / g item 1):
    V_I0-specific if |far-ref E_b(+1) - far-ref E_b(0)| > 25 meV at any site, or the near-minus-far
    sign differs; and dE_a(+1) on images 0/3 = [F3 - F0]_Sr - [F3 - F0]_undoped vs the q = 0 value.
WP2e: E_relax = F(DFT-relaxed) - F(single point at the MACE geometry); the single-point bias of
    the paired dE_a is -(E_relax(dopant) - E_relax(undoped)) (endpoint image 0 only; c item 5); the
    relaxed E_b quartet gives E_b(relaxed) - E_b(single point).
Settings (c item 6): dE(img3 - img0) at degauss 0.0025 vs 0.005 must move < 3 meV; nspin 2 vs 1.

    python scripts/37_dft_eb_analysis.py --dft <QE outputs> --v2 <WP1 dir> --bands <band dir> --out <dir>
"""
import argparse, glob, json, os, re
import importlib.util
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("a32", os.path.join(HERE, "32_dft_validation_analysis.py"))
a32 = importlib.util.module_from_spec(_s); _s.loader.exec_module(a32)
RY = a32.RY
TOL4, TOL_Q, TOL_SMEAR = 25.0, 25.0, 3.0


def qe(path):
    """F (eV), E_F (eV), converged, relax info for one pw.x output; None if unfinished."""
    if path is None or not os.path.exists(path):
        return None
    t = open(path, errors="replace").read()
    if "JOB DONE" not in t:
        return None
    q = a32.parse_qe(path)
    ef = re.findall(r"the Fermi energy is\s+([-\d.]+)\s+ev", t)
    mag = re.findall(r"total magnetization\s+=\s+([-\d.]+)\s+Bohr", t)
    relax = "calculation" in t and "bfgs" in t.lower() and "Geometry Optimization" in t
    return {"F": q["F_eV"], "EF": float(ef[-1]) if ef else None, "scf_converged": q["converged"],
            "mag": float(mag[-1]) if mag else None,
            "bfgs_converged": ("bfgs converged" in t) if relax else None,
            "fmax": float(np.linalg.norm(q["forces"], axis=1).max()) if q["forces"] is not None else None}


def index_outputs(root):
    out = {}
    for f in glob.glob(os.path.join(root, "**", "*.out"), recursive=True):
        k = os.path.basename(f)[:-4]
        assert k not in out, f"label {k} found twice: {out[k]} and {f}"
        out[k] = f
    return out


def eb(F, dv, d, v, h):
    return (F[dv] - F[d] - F[v] + F[h]) * 1000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dft", required=True)
    ap.add_argument("--v2", required=True, help="WP1 dir: shell_mNN.json + wp2cde_selection.json")
    ap.add_argument("--bands", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--threads", type=int, default=4)
    a = ap.parse_args()
    O = index_outputs(a.dft)
    R = {k: qe(v) for k, v in O.items()}
    ok = lambda lab: R.get(lab) is not None and R[lab]["scf_converged"]
    sel = json.load(open(os.path.join(a.v2, "wp2cde_selection.json")))
    out = {"wp2c": {}, "wp2d": {}, "wp2e": {}, "settings": {}, "missing": []}

    # ---------------- WP2c and WP2d
    for h, rec in sel.items():
        shell = json.load(open(os.path.join(a.v2, f"shell_{h}.json")))
        Em = {(r["dopant"], r["site_host_index"]): r["Eb_meV"] for r in shell["rows"]}
        base = [f"{h}_host", f"{h}_vac"]
        for lab in base:
            if not ok(lab):
                out["missing"].append(lab)
        res_h = {}
        for dop in ("Sr", "GA"):
            sites = {k: v["site"] for k, v in rec["sites"].items() if k.startswith(dop + "_")}
            far = sites.get(f"{dop}_far")
            rows = {}
            for name, j in sites.items():
                labs = [f"{h}_{dop}{j}_vac", f"{h}_{dop}{j}_novac"] + base
                miss = [l for l in labs if not ok(l)]
                if miss:
                    out["missing"] += miss; continue
                F = {l: R[l]["F"] for l in labs}
                rows[name] = {"site": j, "d_A": rec["sites"][name]["d_A"],
                              "Eb_dft_meV": round(eb(F, *labs), 2), "Eb_mace_meV": Em[(dop, j)],
                              "dEF_meV": round((R[labs[0]]["EF"] - R[f"{h}_vac"]["EF"]) * 1000, 1)}
            if far is None or f"{dop}_far" not in rows:
                res_h[dop] = {"rows": rows, "note": "far site missing: far-referenced comparison impossible"}
                continue
            fr = rows[f"{dop}_far"]
            for name, r in rows.items():
                r["Eb_dft_farref_meV"] = round(r["Eb_dft_meV"] - fr["Eb_dft_meV"], 2)
                r["Eb_mace_farref_meV"] = round(r["Eb_mace_meV"] - fr["Eb_mace_meV"], 2)
                r["farref_error_meV"] = round(r["Eb_mace_farref_meV"] - r["Eb_dft_farref_meV"], 2)
                r["raw_error_meV"] = round(r["Eb_mace_meV"] - r["Eb_dft_meV"], 2)
                r["band_residual_meV"] = round(r["dEF_meV"] - fr["dEF_meV"], 1)
            tested = {n: r for n, r in rows.items() if n != f"{dop}_far"}
            near = [n for n in tested if n.endswith(("_hinge", "_flank", "_near"))]
            sgn = lambda x: int(np.sign(x))
            sign_agree = all(sgn(tested[n]["Eb_mace_farref_meV"]) == sgn(tested[n]["Eb_dft_farref_meV"]) for n in near)
            res_h[dop] = {"rows": rows, "far_site_raw_dft_meV": fr["Eb_dft_meV"], "far_site_raw_mace_meV": fr["Eb_mace_meV"],
                          "criterion4": {"max_abs_farref_error_meV": round(max(abs(r["farref_error_meV"]) for r in tested.values()), 2) if tested else None,
                                         "near_sign_agree": sign_agree,
                                         "pass": bool(tested) and all(abs(r["farref_error_meV"]) < TOL4 for r in tested.values()) and sign_agree}}
            # WP2d at this host
            if "wp2d_labels" in rec:
                q = {}
                for name, r in rows.items():
                    j = r["site"]
                    labs = [f"{h}_{dop}{j}_vac_q1", f"{h}_{dop}{j}_novac", f"{h}_vac_q1", f"{h}_host"]
                    if f"{h}_{dop}{j}_vac_q1" not in rec["wp2d_labels"]:
                        continue
                    miss = [l for l in labs if not ok(l)]
                    if miss:
                        out["missing"] += miss; continue
                    F = {l: R[l]["F"] for l in labs}
                    q[name] = {"site": j, "Eb_q1_meV": round(eb(F, *labs), 2), "Eb_q0_meV": r["Eb_dft_meV"]}
                if f"{dop}_far" in q:
                    fq = q[f"{dop}_far"]
                    for name, x in q.items():
                        x["farref_q1_meV"] = round(x["Eb_q1_meV"] - fq["Eb_q1_meV"], 2)
                        x["farref_q0_meV"] = round(x["Eb_q0_meV"] - fq["Eb_q0_meV"], 2)
                        x["farref_q1_minus_q0_meV"] = round(x["farref_q1_meV"] - x["farref_q0_meV"], 2)
                    tq = {n: x for n, x in q.items() if n != f"{dop}_far"}
                    flag = any(abs(x["farref_q1_minus_q0_meV"]) > TOL_Q or np.sign(x["farref_q1_meV"]) != np.sign(x["farref_q0_meV"])
                               for x in tq.values())
                    out["wp2d"].setdefault(h, {})[dop] = {"rows": q, "far_site_raw_q1_minus_q0_meV":
                                                          round(fq["Eb_q1_meV"] - fq["Eb_q0_meV"], 2),
                                                          "label": "V_I0-specific" if flag else "charge-state robust"}
                else:
                    out["wp2d"].setdefault(h, {})[dop] = {"rows": q, "note": "far site missing"}
        out["wp2c"][h] = res_h
        # dE_a at q = +1 on images 0/3 (charged host only)
        if "wp2d_labels" in rec:
            labs = [f"{h}_{s}_img{i}{sfx}" for s in ("undoped", "Sr") for i in (0, 3) for sfx in ("_q1", "")]
            if all(ok(l) for l in labs):
                d = lambda s, sfx: (R[f"{h}_{s}_img3{sfx}"]["F"] - R[f"{h}_{s}_img0{sfx}"]["F"]) * 1000
                import torch; torch.set_num_threads(a.threads)
                from ase.io import read
                from mace.calculators import mace_mp
                calc = mace_mp(model="medium", device="cpu", default_dtype="float64")
                def dm(s):
                    fr = read(os.path.join(a.bands, f"band_{s}_{h}.extxyz"), ":")
                    e = []
                    for i in (0, 3):
                        x = fr[i].copy(); x.calc = calc; e.append(x.get_potential_energy())
                    return (e[1] - e[0]) * 1000
                out["wp2d"].setdefault(h, {})["dEa_img03"] = {
                    "q1_meV": round(d("Sr", "_q1") - d("undoped", "_q1"), 2), "q0_meV": round(d("Sr", "") - d("undoped", ""), 2),
                    "mace_meV": round(dm("Sr") - dm("undoped"), 2),
                    "note": "E(img3) - E(img0) differences on the MACE path, not max over images"}
            else:
                out["missing"] += [l for l in labs if not ok(l)]

    # ---------------- WP2e
    for s in ("undoped", "GA", "Sr"):
        rl, sp = f"relax_m30_{s}_img0", f"m30_{s}_img0"
        if ok(rl) and ok(sp):
            out["wp2e"][s] = {"E_relax_meV": round((R[rl]["F"] - R[sp]["F"]) * 1000, 2),
                              "bfgs_converged": R[rl]["bfgs_converged"], "final_fmax_eVA": R[rl]["fmax"]}
        else:
            out["missing"] += [l for l in (rl, sp) if not ok(l)]
    e = out["wp2e"]
    if all(k in e for k in ("undoped", "GA", "Sr")):
        e["dEa_single_point_bias_meV"] = {d: round(-(e[d]["E_relax_meV"] - e["undoped"]["E_relax_meV"]), 2) for d in ("GA", "Sr")}
    for h, rec in sel.items():
        q = rec.get("wp2e_quartet_labels")
        if q and all(ok(l) for l in q) and all(ok(l.replace("_relax", "")) for l in q):
            hst = [l for l in q if l.endswith("_host_relax")][0]; vac = [l for l in q if l.endswith("_vac_relax") and "Sr" not in l][0]
            dv = [l for l in q if "Sr" in l and l.endswith("_vac_relax")][0]; dn = [l for l in q if "Sr" in l and l.endswith("_novac_relax")][0]
            Fr = {l: R[l]["F"] for l in q}; Fs = {l: R[l.replace("_relax", "")]["F"] for l in q}
            out["wp2e"]["Eb_quartet"] = {"host": h, "Eb_relaxed_meV": round(eb(Fr, dv, dn, vac, hst), 2),
                                         "Eb_single_point_meV": round(eb(Fs, dv, dn, vac, hst), 2),
                                         "bfgs_converged": {l: R[l]["bfgs_converged"] for l in q}}

    # ---------------- settings rows (c item 6)
    base0, base3 = "m30_undoped_img0", "m30_undoped_img3"
    if all(ok(l) for l in (base0, base3, "set_m30u_img0_dg0025", "set_m30u_img3_dg0025")):
        d5 = (R[base3]["F"] - R[base0]["F"]) * 1000
        d25 = (R["set_m30u_img3_dg0025"]["F"] - R["set_m30u_img0_dg0025"]["F"]) * 1000
        out["settings"]["degauss"] = {"dE_img3_minus_img0_dg0.005_meV": round(d5, 2), "dg0.0025_meV": round(d25, 2),
                                      "shift_meV": round(d25 - d5, 2), "pass": abs(d25 - d5) < TOL_SMEAR}
    if ok("set_m30u_img0_nspin2") and ok(base0):
        out["settings"]["nspin2"] = {"F_nspin2_minus_nspin1_meV": round((R["set_m30u_img0_nspin2"]["F"] - R[base0]["F"]) * 1000, 2),
                                     "total_magnetization_muB": R["set_m30u_img0_nspin2"]["mag"]}
    out["missing"] = sorted(set(out["missing"]))
    os.makedirs(a.out, exist_ok=True)
    json.dump(out, open(os.path.join(a.out, "wp2cde_dft.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()

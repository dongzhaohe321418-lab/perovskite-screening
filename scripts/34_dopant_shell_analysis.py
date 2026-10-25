#!/usr/bin/env python
"""Analysis of the WP1 binding-energy scans (scripts/29_dopant_shell_scan.py, protocol v2).

Definitions fixed in PLAN amendment 2026-10-25d BEFORE any v2 E_b value was read. Shells come
from the unrelaxed host geometry (row field d_dopant_vacancy_A, true minimum image), where the
three pilot hosts show wide natural gaps:

    Sr (Pb sites):  near d < 5.0 A (2 sites)   mid 5.0-8.5 A   far d > 8.5 A
    GA (FA sites):  near d < 6.0 A (3 sites)   mid 6.0-9.0 A   far d > 9.0 A

Modes
  depth : depth gate (amendment c, item 2). For every VALID row, |E_b(stage) - E_b(tightest)|;
          the loosest stage with every value <= 5 meV is adopted.
  map   : criteria 1 and 2 of PLAN.md.
          crit 1 (as written): valid rows with d > 8 A, pooled over hosts, per dopant:
                 |mean| < 15 meV and SD < 25 meV (SD with ddof = 1).
          crit 2: pooled near mean minus pooled far mean (far = amended set); "binds"/"repels"
                 only if |difference| > 2 x pooled far SD AND the per-host (near - far) sign
                 agrees in >= 2 of 3 hosts. Thermal relevance flagged at |difference| > 25.7 meV.
          Also reported (amendment c, item 3): E_b - median(far) per host, with the far SD.
Invalid rows are never used and are listed with their reasons.

    python scripts/34_dopant_shell_analysis.py --mode depth --inp /data/work/v2pilot --out <dir>
    python scripts/34_dopant_shell_analysis.py --mode map --inp <v2 dir> --out <dir>
"""
import argparse, csv, glob, json, os
import numpy as np

NEAR = {"Sr": 5.0, "GA": 6.0}
FAR = {"Sr": 8.5, "GA": 9.0}
CRIT1_D, CRIT1_MEAN, CRIT1_SD = 8.0, 15.0, 25.0
DEPTH_TOL = 5.0
KT298 = 25.7


def shell(dop, d):
    return "near" if d < NEAR[dop] else ("far" if d > FAR[dop] else "mid")


def reasons(r):
    out = []
    if not r["no_vac"]["converged"] or not r["with_vac"]["converged"]:
        out.append("not converged")
    if r["nearest_I_to_vacancy_site_A"] <= 1.2:
        out.append("vacancy refilled")
    if max(r["dopant_displacement_A"]) >= 1.0:
        out.append("dopant left site")
    if not r["basin_ok"]:
        b0, bv = r["basin_novac_vs_host"], r["basin_vac_vs_V"]
        out.append(f"basin (dr {b0['max_dr_A']:.2f}/{bv['max_dr_A']:.2f} A, rot "
                   f"{b0['max_fa_rot_deg']:.0f}/{bv['max_fa_rot_deg']:.0f} deg)")
    return out


def load(inp):
    rows, meta = [], {}
    for f in sorted(glob.glob(os.path.join(inp, "shell_m*.json"))):
        res = json.load(open(f))
        h = f"m{res['member']:02d}"
        meta[h] = {"protocol": res["protocol"], "E_host_fmax": res.get("E_host", {}).get("fmax"),
                   "E_vac_fmax": res.get("E_vac", {}).get("fmax")}
        for r in res["rows"]:
            rows.append({"host": h, "dopant": r["dopant"], "site": r["site_host_index"],
                         "d_A": r["d_dopant_vacancy_A"], "shell": shell(r["dopant"], r["d_dopant_vacancy_A"]),
                         "Eb_meV": r["Eb_meV"], "Eb_by_stage_meV": r["Eb_by_stage_meV"],
                         "valid": r["valid"], "invalid_reasons": reasons(r)})
    return rows, meta


def sd(x):
    return float(np.std(x, ddof=1)) if len(x) > 1 else float("nan")


def depth(rows):
    val = [r for r in rows if r["valid"]]
    stages = sorted({float(s) for r in val for s in r["Eb_by_stage_meV"]}, reverse=True)
    tight = min(stages)
    per = {}
    for s in stages:
        dev = [abs(r["Eb_by_stage_meV"][str(s)] - r["Eb_by_stage_meV"][str(tight)]) for r in val]
        per[str(s)] = {"max_abs_dev_meV": round(max(dev), 2) if dev else None, "n": len(dev),
                       "pass": bool(dev) and max(dev) <= DEPTH_TOL}
    adopted = max([s for s in stages if per[str(s)]["pass"]], default=None)
    return {"tolerance_meV": DEPTH_TOL, "stages": per, "adopted_fmax": adopted,
            "n_valid": len(val), "n_invalid": len(rows) - len(val)}


def map_(rows):
    out = {}
    for dop in sorted({r["dopant"] for r in rows}):
        v = [r for r in rows if r["dopant"] == dop and r["valid"]]
        hosts = sorted({r["host"] for r in v})
        c1 = np.array([r["Eb_meV"] for r in v if r["d_A"] > CRIT1_D])
        near = np.array([r["Eb_meV"] for r in v if r["shell"] == "near"])
        far = np.array([r["Eb_meV"] for r in v if r["shell"] == "far"])
        diff = float(near.mean() - far.mean()) if near.size and far.size else float("nan")
        per_host = {}
        for h in hosts:
            hn = [r["Eb_meV"] for r in v if r["host"] == h and r["shell"] == "near"]
            hf = [r["Eb_meV"] for r in v if r["host"] == h and r["shell"] == "far"]
            if hn and hf:
                per_host[h] = {"near_mean": round(float(np.mean(hn)), 2), "far_median": round(float(np.median(hf)), 2),
                               "far_mean": round(float(np.mean(hf)), 2), "far_sd": round(sd(hf), 2),
                               "near_minus_far": round(float(np.mean(hn) - np.mean(hf)), 2), "n_near": len(hn), "n_far": len(hf)}
        signs = [np.sign(p["near_minus_far"]) for p in per_host.values()]
        agree = int(sum(1 for s in signs if s == np.sign(diff))) if np.isfinite(diff) else 0
        sig = bool(np.isfinite(diff) and far.size > 1 and abs(diff) > 2 * sd(far) and agree >= 2)
        out[dop] = {
            "criterion1": {"n": int(c1.size), "mean_meV": round(float(c1.mean()), 2) if c1.size else None,
                           "sd_meV": round(sd(c1), 2) if c1.size > 1 else None,
                           "pass": bool(c1.size > 1 and abs(c1.mean()) < CRIT1_MEAN and sd(c1) < CRIT1_SD)},
            "criterion2": {"near_mean_meV": round(float(near.mean()), 2) if near.size else None, "n_near": int(near.size),
                           "far_mean_meV": round(float(far.mean()), 2) if far.size else None, "n_far": int(far.size),
                           "far_sd_meV": round(sd(far), 2) if far.size > 1 else None,
                           "near_minus_far_meV": round(diff, 2) if np.isfinite(diff) else None,
                           "hosts_sign_agree": f"{agree}/{len(per_host)}",
                           "verdict": ("binds" if diff < 0 else "repels") if sig else "no resolved interaction",
                           "thermally_relevant": bool(np.isfinite(diff) and abs(diff) > KT298)},
            "per_host": per_host}
    for r in rows:      # E_b relative to the host's far median (amendment c, item 3)
        ph = out[r["dopant"]]["per_host"].get(r["host"])
        r["Eb_rel_far_median_meV"] = round(r["Eb_meV"] - ph["far_median"], 2) if ph and r["valid"] else None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["depth", "map"], required=True)
    ap.add_argument("--inp", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows, meta = load(a.inp)
    assert rows, f"no rows under {a.inp}"
    res = {"mode": a.mode, "definitions": {"near_lt_A": NEAR, "far_gt_A": FAR, "crit1_d_gt_A": CRIT1_D},
           "hosts": meta, "invalid": [{k: r[k] for k in ("host", "dopant", "site", "d_A", "invalid_reasons")}
                                      for r in rows if not r["valid"]]}
    res["result"] = depth(rows) if a.mode == "depth" else map_(rows)
    os.makedirs(a.out, exist_ok=True)
    json.dump(res, open(os.path.join(a.out, f"wp1_{a.mode}.json"), "w"), indent=1)
    keys = ["host", "dopant", "site", "d_A", "shell", "Eb_meV", "Eb_rel_far_median_meV", "valid", "invalid_reasons"]
    stages = sorted({s for r in rows for s in r["Eb_by_stage_meV"]}, key=float, reverse=True)
    with open(os.path.join(a.out, f"wp1_{a.mode}_rows.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(keys + [f"Eb_fmax{s}" for s in stages])
        for r in sorted(rows, key=lambda r: (r["dopant"], r["host"], r["d_A"])):
            w.writerow([r.get(k) if k != "invalid_reasons" else "; ".join(r[k]) for k in keys]
                       + [r["Eb_by_stage_meV"].get(s) for s in stages])
    print(json.dumps(res["result"], indent=1))
    if res["invalid"]:
        print(f"{len(res['invalid'])} invalid rows:", *[f"  {i}" for i in res["invalid"]], sep="\n")


if __name__ == "__main__":
    main()

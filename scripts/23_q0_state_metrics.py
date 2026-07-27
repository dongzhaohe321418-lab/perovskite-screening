#!/usr/bin/env python
"""q=0 numerical-convergence ladder: extract defect-state metrics from one rung.

The defect state is NEVER identified by band index -- adding nbnd renumbers bands. It is
identified by, in order:
  1. fractional occupation (0.2 < occ < 0.8) in the pw output, else
  2. the band within E_F +- 0.6 eV whose Pb-p weight is maximal in projwfc.

Emitted per rung: defect-state energy, occupation, Pb-p weight, IPR, weights on the two
vacancy-flanking Pb (QE atoms 71 and 140), and the COSINE SIMILARITY of the per-atom weight
vector against a reference rung -- the state-identity criterion that replaces band number.

Usage: python 23_q0_state_metrics.py --pw q0.out --proj projwfc.out [--ref ref_weights.json]
"""
import argparse, json, re, sys
import numpy as np


def parse_pw(path):
    t = open(path, errors="ignore").read()
    seg = t.split("End of self-consistent calculation")[-1]
    ev_txt = seg.split("occupation numbers")[0].split("bands (ev):")[-1]
    occ_txt = seg.split("occupation numbers")[1].split("the Fermi energy is")[0]
    ev = [float(x) for x in re.findall(r"-?\d+\.\d{4}", ev_txt)]
    occ = [float(x) for x in re.findall(r"\d\.\d{4}", occ_txt)]
    assert len(ev) == len(occ), f"eigenvalue/occupation mismatch: {len(ev)} vs {len(occ)}"
    ef = float(re.search(r"the Fermi energy is\s+([-\d.]+)", seg).group(1))
    nit = t.count("iteration #")
    conv = "convergence has been achieved" in t
    etot = re.findall(r"^!\s+total energy\s+=\s+([-\d.]+)", t, re.M)
    return ev, occ, ef, nit, conv, (float(etot[-1]) if etot else None)


def parse_proj(path):
    t = open(path, errors="ignore").read()
    states = {}
    for m in re.finditer(r"state #\s*(\d+):\s*atom\s+(\d+)\s+\(([A-Za-z]+)\s*\).*?wfc\s+\d+\s*\(l=(\d+)", t):
        states[int(m.group(1))] = (int(m.group(2)), m.group(3).strip(), int(m.group(4)))
    bands = {}
    for b in re.split(r"==== e\(", t)[1:]:
        hm = re.match(r"\s*(\d+)\)\s*=\s*([-\d.]+)\s*eV", b)
        if not hm:
            continue
        pairs = [(int(s), float(w)) for w, s in
                 re.findall(r"([\d.]+)\*\[#\s*(\d+)\]", b.split("|psi|^2")[0])]
        bands[int(hm.group(1))] = (float(hm.group(2)), pairs)
    return states, bands


def metrics(states, pairs):
    agg, per_atom = {}, {}
    for st, wt in pairs:
        if st not in states:
            continue
        a, sp, l = states[st]
        agg[f"{sp}-{'spdf'[l]}"] = agg.get(f"{sp}-{'spdf'[l]}", 0.0) + wt
        per_atom[a] = per_atom.get(a, 0.0) + wt
    S = sum(agg.values()) or 1.0
    pa = np.array([per_atom.get(i, 0.0) for i in range(1, 160)])  # fixed 159-atom vector
    pan = pa / (pa.sum() or 1.0)
    return {"pb_p_frac": agg.get("Pb-p", 0.0) / S,
            "char": {k: round(v / S, 4) for k, v in sorted(agg.items(), key=lambda kv: -kv[1])[:4]},
            "ipr": float((pan ** 2).sum()),
            "eff_atoms": float(1.0 / (pan ** 2).sum()),
            "w_Pb140": float(pan[139]), "w_Pb71": float(pan[70]),
            "weights": pan.tolist()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pw", required=True)
    ap.add_argument("--proj", required=True)
    ap.add_argument("--ref", default=None, help="reference weights json for cosine match")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    ev, occ, ef, nit, conv, etot = parse_pw(a.pw)
    states, bands = parse_proj(a.proj)

    frac = [i + 1 for i in range(len(occ)) if 0.2 < occ[i] < 0.8]
    how = None
    if len(frac) == 1:
        band = frac[0]
        how = "fractional occupation"
    else:
        # fall back: max Pb-p weight within E_F +- 0.6 eV
        cand = [b for b, (E, _) in bands.items() if abs(E - ef) < 0.6]
        best, band = -1.0, None
        for b in cand:
            m = metrics(states, bands[b][1])
            if m["pb_p_frac"] > best:
                best, band = m["pb_p_frac"], b
        how = f"max Pb-p near E_F ({len(frac)} fractional bands)"
    E_state, pairs = bands[band]
    m = metrics(states, pairs)
    res = {"pw": a.pw, "n_bands": len(ev), "n_iter": nit, "converged": conv,
           "etot_Ry": etot, "E_F": ef, "band": band, "identified_by": how,
           "E_state": E_state, "occupation": occ[band - 1],
           **{k: v for k, v in m.items() if k != "weights"}}
    if a.ref:
        ref = np.array(json.load(open(a.ref))["weights"])
        w = np.array(m["weights"])
        res["cosine_vs_ref"] = float(w @ ref / (np.linalg.norm(w) * np.linalg.norm(ref)))
    out = a.out or a.pw.replace(".out", "_metrics.json")
    json.dump({**res, "weights": m["weights"]}, open(out, "w"), indent=1)
    for k, v in res.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()

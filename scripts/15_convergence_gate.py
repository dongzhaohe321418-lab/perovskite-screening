#!/usr/bin/env python3
"""Stage 2 parameter-convergence gate analysis.

For each perturbed setting (ecut 50->60, k Gamma->2x2x2, degauss 0.01->0.005) computes
the barrier E(img3)-E(img0) for q0 and q1, and compares to the base (50/Gamma/0.01)
barriers from the d3_baseline. If ANY variation shifts the barrier by more than the
tolerance (default 10 meV), the base setting is NOT converged for that parameter and
the production setting must be upgraded (with a cost report, since a k-point upgrade
multiplies every later SCF cost).

Base barriers (from Stage 1.5 d3_baseline, PBE+D3(BJ)): q0 179.1, q1 152.8 meV.

Usage:
  python 15_convergence_gate.py --indir <harvest> --base-q0 179.1 --base-q1 152.8 \
      --tol 10 --out convergence_gate.json
"""
import argparse, json, re
from pathlib import Path

RY_TO_MEV = 13605.693122994
RE_ETOT = re.compile(r"^!\s+total energy\s*=\s*(-?\d+\.\d+)\s*Ry", re.M)


def energy_ry(path):
    if path is None or not Path(path).exists():
        return None
    m = RE_ETOT.findall(Path(path).read_text())
    return float(m[-1]) if m else None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--indir", required=True)
    p.add_argument("--base-q0", type=float, default=179.1)
    p.add_argument("--base-q1", type=float, default=152.8)
    p.add_argument("--tol", type=float, default=10.0, help="meV barrier-shift tolerance")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    d = Path(args.indir)

    def find(name):
        hits = list(d.glob(f"{name}.out")) + list(d.glob(f"**/{name}.out"))
        return hits[0] if hits else None

    variants = ["ecut60", "k222", "dg005"]
    base = {"q0": args.base_q0, "q1": args.base_q1}
    results = {}
    max_shift = 0.0
    forced = []
    for v in variants:
        results[v] = {}
        for q in ("q0", "q1"):
            e0 = energy_ry(find(f"conv_{v}_img0_{q}"))
            e3 = energy_ry(find(f"conv_{v}_img3_{q}"))
            if e0 is None or e3 is None:
                results[v][q] = {"barrier_meV": None, "shift_vs_base_meV": None,
                                 "status": "MISSING"}
                continue
            bar = (e3 - e0) * RY_TO_MEV
            shift = bar - base[q]
            max_shift = max(max_shift, abs(shift))
            conv = abs(shift) <= args.tol
            if not conv:
                forced.append(f"{v}/{q} ({shift:+.1f} meV)")
            results[v][q] = {"barrier_meV": round(bar, 1),
                             "shift_vs_base_meV": round(shift, 1),
                             "status": "converged" if conv else "NOT CONVERGED"}

    all_conv = len(forced) == 0
    verdict = {
        "all_converged": all_conv,
        "max_abs_shift_meV": round(max_shift, 1),
        "tolerance_meV": args.tol,
        "forced_upgrades": forced,
        "recommendation": (
            "Base settings (ecutwfc 50, Gamma-only, degauss 0.01 Ry) are CONVERGED for the "
            "barrier at the {tol} meV tolerance -> proceed to endpoint relaxations at base."
            .format(tol=args.tol) if all_conv else
            "Base NOT converged for: " + ", ".join(forced) +
            ". UPGRADE the production setting and REPORT the cost impact to the user "
            "(a k-point upgrade multiplies every later SCF cost ~4-8x)."),
    }
    out = {"base_barriers_meV": base, "variant_barriers": results, "verdict": verdict}
    json.dump(out, open(args.out, "w"), indent=2)

    print(f"[conv] base barriers: q0 {base['q0']} / q1 {base['q1']} meV; tol {args.tol} meV\n")
    print(f"{'variant':>8} {'q0 bar':>8} {'q0 dshift':>10} {'q1 bar':>8} {'q1 dshift':>10}")
    for v in variants:
        r0, r1 = results[v]["q0"], results[v]["q1"]
        print(f"{v:>8} {str(r0['barrier_meV']):>8} {str(r0['shift_vs_base_meV']):>10} "
              f"{str(r1['barrier_meV']):>8} {str(r1['shift_vs_base_meV']):>10}")
    print(f"\n[conv] max |shift| = {max_shift:.1f} meV -> {'ALL CONVERGED' if all_conv else 'UPGRADE FORCED: ' + ', '.join(forced)}")
    print(f"[conv] {verdict['recommendation']}")


if __name__ == "__main__":
    main()

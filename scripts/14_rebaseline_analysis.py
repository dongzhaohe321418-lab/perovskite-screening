#!/usr/bin/env python3
"""Stage 1.5 re-baseline analysis: assemble the PBE+D3(BJ) baseline table and the
32-vs-64-rank launch-config verdict from the harvested job outputs.

Produces the three-way barrier comparison the review demands be kept SEPARATE
(never mixed in one conclusion row):
  1. bare-PBE          — the old Stage-1 numbers (q0 spin 152.9, q1 126.6 meV);
  2. simple-dftd3 est. — the post-hoc geometry-only additive estimate (+25.3 meV);
  3. true QE PBE+D3(BJ)— computed here (D3 energy+force correction inside QE).

For q=0 the D3 barrier is compared to the SPIN bare-PBE value (152.9 meV, nspin=2),
since the D3 baseline uses nspin=2 too — matching theory levels, per the review.

Rank verdict: wall time / core-hours / SCF iterations for img0_q0 at 32 vs 64 ranks
(both spanning 2 nodes). Recommends the launch config; a ~1:1 wall ratio means the
extra ranks don't help this Gamma-point 159-atom cell and 32 ranks is the efficient
choice (frees a node-equivalent of throughput).

Usage:
  python 14_rebaseline_analysis.py --indir <harvest_dir> --out rebaseline.json
"""
import argparse, json, re
from pathlib import Path

RY_TO_MEV = 13605.693122994
RE_ETOT = re.compile(r"^!\s+total energy\s*=\s*(-?\d+\.\d+)\s*Ry", re.M)
RE_CONV_ITER = re.compile(r"convergence has been achieved in\s+(\d+)\s+iterations")
RE_WALL = re.compile(r"PWSCF\s*:\s*(.+?)\s+CPU\s+(.+?)\s+WALL")
RE_TOTMAG = re.compile(r"total magnetization\s*=\s*(-?\d+\.\d+)\s*Bohr mag")

# reference values from earlier stages (bare-PBE + post-hoc simple-dftd3 estimate)
BARE_PBE = {"q0_nonspin_meV": 140.6, "q0_spin_meV": 152.9, "q1_meV": 126.6}
SIMPLE_DFTD3_EST = {"shift_meV": 25.3, "q0_from_nonspin_meV": 165.9, "q1_meV": 151.9}


def energy_ry(path):
    m = RE_ETOT.findall(Path(path).read_text())
    return float(m[-1]) if m else None


def scf_iters(path):
    m = RE_CONV_ITER.search(Path(path).read_text())
    return int(m.group(1)) if m else None


def wall_seconds(path):
    """Parse the PWSCF WALL time (e.g. '1h 5m' or '3905.2s') to seconds."""
    txt = Path(path).read_text()
    m = RE_WALL.search(txt)
    if not m:
        return None
    wall = m.group(2)
    sec = 0.0
    for val, unit in re.findall(r"(\d+\.?\d*)\s*([hms])", wall):
        sec += float(val) * {"h": 3600, "m": 60, "s": 1}[unit]
    return sec if sec > 0 else None


def barrier_meV(e_img0, e_img3):
    if e_img0 is None or e_img3 is None:
        return None
    return round((e_img3 - e_img0) * RY_TO_MEV, 1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--indir", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    d = Path(args.indir)

    def find(name):
        hits = list(d.glob(f"{name}.out")) + list(d.glob(f"**/{name}.out"))
        return hits[0] if hits else None

    # --- D3 baseline energies ---
    E = {}
    for tag in ["d3base_img0_q0", "d3base_img3_q0", "d3base_img0_q1", "d3base_img3_q1"]:
        # img0_q0 may only exist as the rank-gate variants
        f = find(tag) or find(tag + "_r64") or find(tag + "_r32")
        E[tag] = energy_ry(f) if f else None

    d3_q0 = barrier_meV(E["d3base_img0_q0"], E["d3base_img3_q0"])
    d3_q1 = barrier_meV(E["d3base_img0_q1"], E["d3base_img3_q1"])

    # --- rank gate ---
    r64, r32 = find("d3base_img0_q0_r64"), find("d3base_img0_q0_r32")
    rank = {}
    for label, f in [("64", r64), ("32", r32)]:
        if f:
            w = wall_seconds(f)
            nranks = int(label)
            rank[label] = {"wall_s": w, "wall_min": round(w/60, 1) if w else None,
                           "scf_iterations": scf_iters(f),
                           "core_hours": round(nranks * w / 3600, 2) if w else None,
                           "energy_Ry": energy_ry(f)}
    verdict = None
    if rank.get("32", {}).get("wall_s") and rank.get("64", {}).get("wall_s"):
        speedup = rank["32"]["wall_s"] / rank["64"]["wall_s"]  # >1 means 64 faster
        ch32, ch64 = rank["32"]["core_hours"], rank["64"]["core_hours"]
        # energies must match (same physics) — sanity
        de = None
        if rank["32"]["energy_Ry"] and rank["64"]["energy_Ry"]:
            de = round((rank["32"]["energy_Ry"] - rank["64"]["energy_Ry"]) * RY_TO_MEV, 3)
        if speedup < 1.3:
            rec = ("32 ranks (16/node x2): ~1:1 wall vs 64 but ~half the core-hours -> "
                   "64 ranks does NOT help this Gamma-point 159-atom cell; use 32.")
        else:
            rec = f"64 ranks: {speedup:.2f}x faster wall, worth the extra core-hours."
        verdict = {"wall_ratio_32_over_64": round(speedup, 2),
                   "core_hours_32": ch32, "core_hours_64": ch64,
                   "energy_diff_32_minus_64_meV": de, "recommendation": rec}

    out = {
        "theory_level": "PBE + D3(BJ) (vdw_corr=dft-d3, dftd3_version=4), US psl-1.0.0 scalar-rel, nosym",
        "d3_baseline_barriers_meV": {"q0_spin": d3_q0, "q1": d3_q1},
        "d3_baseline_energies_Ry": E,
        "three_way_comparison_meV": {
            "note": "SEPARATE theory levels — do not merge into one row. q0 compares within nspin=2.",
            "q0": {"bare_PBE_spin": BARE_PBE["q0_spin_meV"],
                   "simple_dftd3_estimate": SIMPLE_DFTD3_EST["q0_from_nonspin_meV"],
                   "true_QE_D3_spin": d3_q0},
            "q1": {"bare_PBE": BARE_PBE["q1_meV"],
                   "simple_dftd3_estimate": SIMPLE_DFTD3_EST["q1_meV"],
                   "true_QE_D3": d3_q1},
        },
        "rank_gate": rank, "rank_verdict": verdict,
    }
    json.dump(out, open(args.out, "w"), indent=2)
    print(f"[rebaseline] PBE+D3(BJ): q0(spin) barrier = {d3_q0} meV, q1 = {d3_q1} meV")
    print(f"[rebaseline] q0 three-way: bare-PBE(spin) {BARE_PBE['q0_spin_meV']} | "
          f"simple-dftd3-est {SIMPLE_DFTD3_EST['q0_from_nonspin_meV']} | true-QE-D3 {d3_q0}")
    print(f"[rebaseline] q1 three-way: bare-PBE {BARE_PBE['q1_meV']} | "
          f"simple-dftd3-est {SIMPLE_DFTD3_EST['q1_meV']} | true-QE-D3 {d3_q1}")
    if verdict:
        print(f"[rank] {verdict['recommendation']}")
        print(f"[rank] 32r: {rank['32']['wall_min']} min / {rank['32']['core_hours']} core-h; "
              f"64r: {rank['64']['wall_min']} min / {rank['64']['core_hours']} core-h; "
              f"E diff {verdict['energy_diff_32_minus_64_meV']} meV (should be ~0)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""WP3 (e), post hoc and reported only: which bond made a frame fail the scripts/35 sane() topology test, and
the C-H / N-H bond-length statistics of every run. Written after the (e) verdict (2026-11-03); it changes no
verdict, loads no model and reads no QE file.

Input: the archived scripts/41 work directory (results/objective2/dopant_shell/wp3/step7/wp3md_work.tar.gz):
per run the record <label>.json and the trajectory <label>.extxyz (51 frames, t = 0, 100, ..., 5000 fs).
Each trajectory is checked against the record's trajectory_sha256 before it is read.

Topology test: the organic part of scripts/35 sane(), restated with its cut-offs (C-N < 1.6 A; C-H, N-H and
H-(C or N) < 1.25 A; every C with (2 N, 1 H) or (3 N, 0 H), exactly one GA carbon in GA cells and none
otherwise; every N with 2 H; every H with exactly one C or N within 1.25 A; composition unchanged). Its
result must equal the recorded topology_ok of every frame, or the script stops. For each failing frame the
atoms that break the pattern are listed with their distances.

Bond statistics (frames t > 0 only; t = 0 is the relaxed band image): each H is assigned to its nearest
heavy atom among C and N; per run and per temperature the mean, sample SD (ddof 1), maximum and count at or
above 1.25 A of the C-H and N-H distances, with minimum-image distances.

Sampled temperature (frames t > 0): per temperature the mean of the recorded whole-cell T_inst_K and, from the
stored momenta and ASE's default masses, the kinetic temperature of each element, sum(p^2 / 2m) / (1.5 N kB).

    python scripts/43_wp3_md_bond_diagnostic.py [--tar <wp3md_work.tar.gz>] [--out <json>]
"""
import argparse, hashlib, io, json, os, tarfile
import numpy as np
from ase import units
from ase.io import read

CN_CUT, H_CUT = 1.6, 1.25           # scripts/35 sane()
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "results", "objective2", "dopant_shell", "wp3", "step7")


def topology(at, ref_symbols, sysn):
    """(ok, list of offending atoms) by the organic part of scripts/35 sane()."""
    d = at.get_all_distances(mic=True)
    np.fill_diagonal(d, 99.0)
    s = np.array(at.get_chemical_symbols())
    C, N, H = (np.flatnonzero(s == e) for e in ("C", "N", "H"))
    CNi = np.concatenate([C, N])
    I = np.flatnonzero(s == "I")
    bad = []
    cn = np.array([(d[c][N] < CN_CUT).sum() for c in C])
    ch = np.array([(d[c][H] < H_CUT).sum() for c in C])
    for c, a, b in zip(C, cn, ch):
        if not ((a == 2 and b == 1) or (a == 3 and b == 0)):
            bad.append({"atom": f"C{c}", "n_N_below_1.6": int(a), "n_H_below_1.25": int(b)})
    for n in N:
        k = int((d[n][H] < H_CUT).sum())
        if k != 2:
            bad.append({"atom": f"N{n}", "n_H_below_1.25": k,
                        "nearest_H_A": {f"H{h}": round(float(d[n][h]), 4) for h in H[np.argsort(d[n][H])[:3]]}})
    for h in H:
        k = int((d[h][CNi] < H_CUT).sum())
        if k != 1:
            nb = CNi[np.argsort(d[h][CNi])[:2]]
            bad.append({"atom": f"H{h}", "n_C_or_N_below_1.25": k,
                        "nearest_C_or_N_A": {f"{s[j]}{j}": round(float(d[h][j]), 4) for j in nb},
                        "nearest_I_A": round(float(d[h][I].min()), 4)})
    n_ga = int(((cn == 3) & (ch == 0)).sum())
    ok = (sorted(s) == sorted(ref_symbols) and not bad and n_ga == (1 if sysn == "GA" else 0))
    return ok, bad


def bonds(at):
    """C-H and N-H distances, each H assigned to its nearest C or N."""
    d = at.get_all_distances(mic=True)
    s = np.array(at.get_chemical_symbols())
    C, N, H = (np.flatnonzero(s == e) for e in ("C", "N", "H"))
    dC, dN = d[np.ix_(H, C)].min(1), d[np.ix_(H, N)].min(1)
    return dC[dC < dN], dN[dN <= dC]


def stats(x):
    x = np.asarray(x)
    return {"n": int(x.size), "mean_A": float(x.mean()), "sd_A": float(x.std(ddof=1)), "max_A": float(x.max()),
            "n_at_or_above_1.25": int((x >= H_CUT).sum())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tar", default=os.path.join(D, "wp3md_work.tar.gz"))
    ap.add_argument("--out", default=os.path.join(D, "md_bond_diagnostic.json"))
    a = ap.parse_args()
    tar_bytes = open(a.tar, "rb").read()
    files = {}
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:gz") as tf:
        for m in tf.getmembers():
            if m.isfile():
                files[os.path.basename(m.name)] = tf.extractfile(m).read()
    labels = sorted(f[:-5] for f in files if f.endswith(".json") and not f.endswith(".attempts.json"))
    assert len(labels) == 12, labels
    runs, pooled, kin, tinst = [], {}, {}, {}
    for lab in labels:
        rec = json.loads(files[lab + ".json"])
        traj = files[rec["trajectory"]]
        assert hashlib.sha256(traj).hexdigest() == rec["trajectory_sha256"], lab
        frames = read(io.StringIO(traj.decode()), index=":", format="extxyz")
        assert len(frames) == len(rec["frames"]) == rec["n_frames_checked"], lab
        ref = frames[0].get_chemical_symbols()
        failing, ch_all, nh_all = [], [], []
        for i, (at, fr) in enumerate(zip(frames, rec["frames"])):
            assert abs(at.info["t_fs"] - fr["t_fs"]) < 1e-9
            ok, bad = topology(at, ref, rec["system"])
            assert ok == fr["topology_ok"], (lab, fr["t_fs"], ok, fr["topology_ok"])
            if not ok:
                failing.append({"t_fs": fr["t_fs"], "offending": bad, "T_inst_K": fr.get("T_inst_K")})
            if i > 0:
                ch, nh = bonds(at)
                ch_all += list(ch); nh_all += list(nh)
                s = np.array(at.get_chemical_symbols())
                ke = (at.get_momenta() ** 2).sum(1) / (2 * at.get_masses())
                for e in set(s):
                    k = kin.setdefault(str(rec["T_K"]), {}).setdefault(str(e), [0.0, 0])
                    k[0] += float(ke[s == e].sum()); k[1] += int((s == e).sum())
                tinst.setdefault(str(rec["T_K"]), []).append(fr["T_inst_K"])
        start_ch, _ = bonds(frames[0])
        row = {"label": lab, "host": rec["host"], "system": rec["system"], "T_K": rec["T_K"], "ok": rec["ok"],
               "first_failure_fs": rec["first_failure_fs"], "n_failing_frames": rec["n_failing_frames"],
               "topology_failing_frames": failing, "start_CH_mean_A": float(np.mean(start_ch)),
               "CH": stats(ch_all), "NH": stats(nh_all)}
        assert len(failing) <= rec["n_failing_frames"]
        runs.append(row)
        p = pooled.setdefault(str(rec["T_K"]), {"CH": [], "NH": []})
        p["CH"] += ch_all; p["NH"] += nh_all
    out = {"script": "scripts/43_wp3_md_bond_diagnostic.py",
           "status": "post hoc, reported only; written after the (e) verdict; changes no verdict",
           "input": {"tar": os.path.relpath(a.tar, os.path.join(HERE, "..")),
                     "tar_sha256": hashlib.sha256(tar_bytes).hexdigest()},
           "cutoffs_A": {"C-N": CN_CUT, "C-H, N-H, H-(C or N)": H_CUT},
           "topology_reproduced_frames": sum(len(json.loads(files[l + ".json"])["frames"]) for l in labels),
           "frames_in_statistics": "t > 0 (50 per run); each H assigned to its nearest C or N",
           "pooled_by_T": {T: {k: stats(v) for k, v in p.items()} for T, p in sorted(pooled.items())},
           "sampled_temperature_K": {T: {"whole_cell_T_inst_mean": float(np.mean(tinst[T])),
                                         "whole_cell_T_inst_sd": float(np.std(tinst[T], ddof=1)), "n_frames": len(tinst[T]),
                                         "kinetic_by_element": {e: v[0] / (1.5 * v[1] * units.kB) for e, v in sorted(kin[T].items())},
                                         "atom_samples_by_element": {e: v[1] for e, v in sorted(kin[T].items())}}
                                     for T in sorted(kin)},
           "runs": runs}
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    for r in runs:
        print(f"{r['label']:26s} ok={r['ok']!s:5s} C-H mean {r['CH']['mean_A']:.4f} sd {r['CH']['sd_A']:.4f} "
              f"max {r['CH']['max_A']:.4f} (>=1.25: {r['CH']['n_at_or_above_1.25']}); N-H max {r['NH']['max_A']:.4f}; "
              f"failing {[f['t_fs'] for f in r['topology_failing_frames']]}")
    for T, p in out["pooled_by_T"].items():
        print(f"T = {T} K: C-H {p['CH']['mean_A']:.4f} +/- {p['CH']['sd_A']:.4f} (n {p['CH']['n']}, max {p['CH']['max_A']:.4f}); "
              f"N-H {p['NH']['mean_A']:.4f} +/- {p['NH']['sd_A']:.4f} (max {p['NH']['max_A']:.4f})")
    for T, v in out["sampled_temperature_K"].items():
        print(f"T = {T} K: whole-cell T_inst {v['whole_cell_T_inst_mean']:.1f} K; kinetic by element "
              + ", ".join(f"{e} {x:.1f}" for e, x in v["kinetic_by_element"].items()))
    print("topology test reproduced on", out["topology_reproduced_frames"], "frames ->", os.path.relpath(a.out))


if __name__ == "__main__":
    main()

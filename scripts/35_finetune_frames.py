#!/usr/bin/env python
"""Off-equilibrium frames for MACE fine-tuning (PLAN WP3; amendment 2026-10-25c item 7, e).

The WP2 DFT frames are all at or near MACE minima and saddles, so forces there are small and
the fit would see almost no curvature information. This adds, for each TRAINING host only:

    systems : band image 0 of {undoped, GA, Sr} (vacancy cells) + the pristine host (no vacancy;
              makes the per-element offset fit of scripts/33 full rank without WP2c frames)
    kinds   : rat05f / rat10f = Gaussian rattle of the inorganic framework only (Pb, I, Cs, Sr),
                                sigma 0.05 / 0.10 A per Cartesian component; FA/GA untouched
              md300 / md450   = last frame of a 300 K / 450 K Langevin MACE-MD run (fixed cell,
                                1 fs, friction 0.01 fs^-1, --md-steps steps from Maxwell-Boltzmann
                                velocities): thermal sampling of the intramolecular FA modes
    A uniform rattle of all atoms was tried first and rejected (amendment 2026-10-25e): at
    sigma 0.05-0.10 A it displaces H far beyond thermal amplitudes (MACE forces up to 84 eV/A,
    7 of 12 smoke-test frames failed the pre-set 15 eV/A bound).

Every random number comes from a seed derived from the label (crc32), so frames are
reproducible. Frames that fail sanity checks (min distance, MACE force bound, molecular topology
identical to the source frame) are not written and are reported. A resume refuses a frames
directory made with different settings.
Writes <frames>/<label>.extxyz and a QE single point <qe>/<host>_<system>_<kind>/<label>.in
(scripts/30 fingerprint).

    python scripts/35_finetune_frames.py --hosts 05 06 08 12 15 20 --bands <band dir> \
        --frames <dir> --qe /data/jobs/wp3 --threads 5
"""
import argparse, hashlib, json, os, sys, zlib, importlib.util
import numpy as np
from ase import units
from ase.io import read, write

HERE = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("a30", os.path.join(HERE, "30_qe_singlepoint.py"))
a30 = importlib.util.module_from_spec(_s); _s.loader.exec_module(a30)

KINDS = {"rat05f": ("rattle", 0.05), "rat10f": ("rattle", 0.10), "md300": ("md", 300.0), "md450": ("md", 450.0)}
FRAMEWORK = ("Pb", "I", "Cs", "Sr")


def seed_of(label):
    return zlib.crc32(label.encode())


def dump_atomic(obj, path):
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=1); fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp, path)


def sane(at, ref, sysn, calc, fmax_bound):
    """Frame must keep the molecular topology of its source frame: composition unchanged; every
    FA carbon with 2 N and 1 H, the one GA carbon (GA systems only) with 3 N and 0 H; every N with
    2 H; every H bonded to exactly one C or N; no contact below 0.65 A; MACE max force below bound."""
    d = at.get_all_distances(mic=True)
    np.fill_diagonal(d, 99.0)
    dmin = float(d.min())
    s = np.array(at.get_chemical_symbols())
    same_comp = sorted(s) == sorted(ref.get_chemical_symbols())
    C, N, H = (np.flatnonzero(s == e) for e in ("C", "N", "H"))
    cn = np.array([(d[c][N] < 1.6).sum() for c in C])
    ch = np.array([(d[c][H] < 1.25).sum() for c in C])
    nh = np.array([(d[n][H] < 1.25).sum() for n in N])
    hb = np.array([(d[h][np.concatenate([C, N])] < 1.25).sum() for h in H])
    n_ga = int(((cn == 3) & (ch == 0)).sum())
    fa_ok = bool(np.all(((cn == 2) & (ch == 1)) | ((cn == 3) & (ch == 0))))
    topo = same_comp and fa_ok and n_ga == (1 if sysn == "GA" else 0) and bool(np.all(nh == 2)) and bool(np.all(hb == 1))
    b = at.copy(); b.calc = calc
    fm = float(np.linalg.norm(b.get_forces(), axis=1).max())
    ok = topo and dmin > 0.65 and fm < fmax_bound
    return ok, {"min_dist_A": round(dmin, 3), "mace_fmax_eVA": round(fm, 3), "topology_ok": topo}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hosts", nargs="+", required=True, help="TRAINING hosts only (e.g. 05 06)")
    ap.add_argument("--bands", required=True, help="dir with band_<system>_mNN.extxyz")
    ap.add_argument("--pool", default="results/fa_host/pool_v3_harmonised")
    ap.add_argument("--frames", required=True)
    ap.add_argument("--qe", required=True)
    ap.add_argument("--md-steps", type=int, default=1500)
    ap.add_argument("--fmax-bound", type=float, default=15.0)
    ap.add_argument("--threads", type=int, default=5)
    a = ap.parse_args()
    import torch; torch.set_num_threads(a.threads)
    from mace.calculators import mace_mp
    from ase.md.langevin import Langevin
    from ase.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary
    calc = mace_mp(model="medium", device="cpu", default_dtype="float64")
    os.makedirs(a.frames, exist_ok=True)
    params = {"md_steps": a.md_steps, "fmax_bound": a.fmax_bound, "kinds": KINDS, "framework": list(FRAMEWORK),
              "md": "Langevin 1 fs, friction 0.01/fs, fixed cell, MACE-MP-0 medium float64"}
    rpath = os.path.join(a.frames, "frames_report.json")
    report = {"params": json.loads(json.dumps(params)), "records": []}
    if os.path.exists(rpath):                 # resume only into a directory made with the same settings
        old = json.load(open(rpath))
        if not isinstance(old, dict) or old.get("params") != report["params"]:
            raise SystemExit(f"{rpath}: made with different settings; use a new --frames directory")
        report = old
    seen = {r["label"] for r in report["records"]}
    for h in [f"m{int(x):02d}" for x in a.hosts]:
        src = {s: (os.path.join(a.bands, f"band_{s}_{h}.extxyz"), 0) for s in ("undoped", "GA", "Sr")}
        src["pristine"] = (os.path.join(a.pool, f"{h}.extxyz"), -1)
        for sysn, (fn, idx) in src.items():
            base = read(fn, index=idx)
            base = base.copy(); base.calc = None; base.set_tags([0] * len(base))
            assert sane(base, base, sysn, calc, 1e9)[1]["topology_ok"], f"source frame {fn}@{idx} fails the topology check"
            for kind, (mode, par) in KINDS.items():
                label = f"{h}_{sysn}_{kind}"
                if label in seen:
                    continue
                rng = np.random.default_rng(seed_of(label))
                at = base.copy()
                if mode == "rattle":
                    fw = np.isin(at.get_chemical_symbols(), FRAMEWORK)
                    at.positions[fw] += rng.normal(0.0, par, (int(fw.sum()), 3))
                else:
                    at.calc = calc
                    MaxwellBoltzmannDistribution(at, temperature_K=par, rng=rng); Stationary(at)
                    Langevin(at, 1.0 * units.fs, temperature_K=par, friction=0.01 / units.fs,
                             rng=rng).run(a.md_steps)
                    at = at.copy(); at.calc = None
                ok, chk = sane(at, base, sysn, calc, a.fmax_bound)
                rec = {"label": label, "host": h, "system": sysn, "kind": kind,
                       "sigma_A": par if mode == "rattle" else None, "T_K": par if mode == "md" else None,
                       "md_steps": a.md_steps if mode == "md" else 0, "seed": seed_of(label),
                       "source": f"{os.path.relpath(fn)}@{idx}", "ok": ok, **chk}
                print(rec, flush=True)
                if ok:                        # frame, QE input and meta first; the record last
                    at.info.update({k: v for k, v in rec.items() if k not in ("ok", "topology_ok")})
                    at.info["config_type"] = mode
                    write(os.path.join(a.frames, f"{label}.extxyz"), at)
                    qdir = os.path.join(a.qe, label)
                    path = a30.write_input(at, label, qdir)
                    dump_atomic({"label": label, "source_frame": f"{label}.extxyz", "natoms": len(at),
                                 "formula": at.get_chemical_formula(), "fingerprint": a30.FINGERPRINT,
                                 "input_sha256": hashlib.sha256(open(path, "rb").read()).hexdigest()},
                                os.path.join(qdir, f"{label}.meta.json"))
                report["records"].append(rec)
                dump_atomic(report, rpath)
    R = report["records"]
    print(f"{sum(r['ok'] for r in R)} written, {sum(not r['ok'] for r in R)} rejected")


if __name__ == "__main__":
    main()

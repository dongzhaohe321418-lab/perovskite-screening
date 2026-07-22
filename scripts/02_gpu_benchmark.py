#!/usr/bin/env python3
"""GPU benchmark campaign for the MLIP-NEB farm (v2 -- corrected).

Fixes over v1:
  * Stage 1 single-point timing defeated ASE force caching (v1 measured ~90us
    cache hits, flat across 160/540/1280 atoms). v2 perturbs positions
    (rattle) before every timed call so each is a real force evaluation with a
    fresh neighbour list -- representative of an MD/NEB step.
  * Stage 2 reconciles the 17.6s (tracer bullet, per-image calc) vs 47s (v1,
    shared calc) per-path discrepancy with a threads x calc-strategy matrix, so
    the throughput number rests on the true warm per-path cost.
  * Stage 3 runs a FIXED number of paths per worker (not a short wall-clock
    window that only fit ~1 path) and divides CPU threads across workers, the
    realistic farm config. Uses the fastest strategy found in stage 2.

Zero-shot MACE-MP-0 medium, float32 (same physics as the tracer bullet; this
measures compute, not new science). Public ASE + MACE API only.

Stages (guarded; JSON written after each so partials survive a crash):
  0  env / GPU / cueq
  1  single-point force scaling {2x2x2..5x5x5} x {cpu, cuda[, cueq]}  (cache-safe)
  2  warm per-path NEB cost: {shared@Tlo, shared@Thi, per-image@Thi} + E_a check
  3  process-parallel throughput: FIXED paths/worker, K in {1,8,12}, best strategy

Output: results/gpu/benchmark.json
"""
import json
import os
import time
import multiprocessing as mp
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
STRUCT = ROOT / "structures" / "gamma_relaxed.extxyz"
OUT = ROOT / "results" / "gpu" / "benchmark.json"

# --- knobs ---
SP_SIZES = [2, 3, 4, 5]      # 160 / 540 / 1280 / 2500 atoms
SP_WARMUP, SP_REPS = 2, 5
N_IMAGES = 5                 # interior NEB images (7 total), matches tracer bullet
NEB_TOTAL = N_IMAGES + 2
WARM_RUNS = 3                # stage 2: warm runs per config (plus 1 cold, dropped)
NCORES = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else (os.cpu_count() or 8)
T_LO = 16
T_HI = min(64, NCORES)
K_LIST = [1, 8, 12]          # stage 3 concurrency
PATHS_PER_WORKER = 3         # stage 3: fixed paths each worker completes


def _sync(device):
    if device == "cuda":
        import torch
        torch.cuda.synchronize()


def make_calc(device="cuda", cueq=False):
    from mace.calculators import mace_mp
    kw = dict(model="medium", device=device, default_dtype="float32")
    if cueq:
        try:
            return mace_mp(enable_cueq=True, **kw), True
        except TypeError:
            pass
    return mace_mp(**kw), False


def cueq_installed():
    try:
        import cuequivariance_torch  # noqa: F401
        return True
    except Exception:
        return False


def pick_hop_pair(atoms):
    sym = np.array(atoms.get_chemical_symbols())
    pb_idx = np.flatnonzero(sym == "Pb")
    centre = atoms.cell.array.sum(axis=0) / 2
    pb = pb_idx[np.argmin(np.linalg.norm(atoms.positions[pb_idx] - centre, axis=1))]
    i_idx = np.flatnonzero(sym == "I")
    d_pb = atoms.get_distances(pb, i_idx, mic=True)
    octa = i_idx[d_pb < 3.8]
    best, best_err = None, 1e9
    for a in range(len(octa)):
        for b in range(a + 1, len(octa)):
            d = atoms.get_distance(octa[a], octa[b], mic=True)
            if abs(d - 4.5) < best_err:
                best, best_err = (int(octa[a]), int(octa[b])), abs(d - 4.5)
    return best


def _build_endpoints(bulk):
    sc = bulk.repeat((2, 2, 2))
    i_vac, i_hop = pick_hop_pair(sc)
    initial = sc.copy()
    vac_pos = initial.positions[i_vac].copy()
    del initial[i_vac]
    final = sc.copy()
    final.positions[i_hop] = vac_pos
    del final[i_vac]
    return initial, final


def run_one_neb(bulk, calcs, shared, fmax_endpoint=0.03, fmax_neb=0.05):
    """One V_I hop CI-NEB. `calcs` is a single calc (shared=True) or a list of
    NEB_TOTAL calcs (shared=False). Calcs are RESET and reused (load-once)."""
    from ase.mep import NEB
    from ase.optimize import FIRE
    initial, final = _build_endpoints(bulk)

    if shared:
        c = calcs
        c.reset()
        initial.calc = c; FIRE(initial, logfile=None).run(fmax=fmax_endpoint, steps=500)
        c.reset()
        final.calc = c; FIRE(final, logfile=None).run(fmax=fmax_endpoint, steps=500)
        images = [initial] + [initial.copy() for _ in range(N_IMAGES)] + [final]
        for im in images:
            im.calc = c
        neb = NEB(images, climb=False, k=0.1, allow_shared_calculator=True)
    else:
        for cc in calcs:
            cc.reset()
        initial.calc = calcs[0]; FIRE(initial, logfile=None).run(fmax=fmax_endpoint, steps=500)
        final.calc = calcs[-1]; FIRE(final, logfile=None).run(fmax=fmax_endpoint, steps=500)
        images = [initial] + [initial.copy() for _ in range(N_IMAGES)] + [final]
        for im, cc in zip(images, calcs):
            im.calc = cc
        neb = NEB(images, climb=False, k=0.1)

    neb.interpolate(method="idpp", mic=True)
    FIRE(neb, logfile=None).run(fmax=2 * fmax_neb, steps=300)
    neb.climb = True
    FIRE(neb, logfile=None).run(fmax=fmax_neb, steps=300)
    energies = np.array([im.get_potential_energy() for im in images])
    return float((energies - energies[0]).max())


# ---------- stage 1: single-point force scaling (cache-safe) ----------
def stage1_single_point():
    from ase.io import read
    import torch
    torch.set_num_threads(T_HI)
    bulk = read(STRUCT)
    have_cueq = cueq_installed()
    rows = []
    for n in SP_SIZES:
        sc0 = bulk.repeat((n, n, n))
        natoms = len(sc0)
        entry = {"reps": n, "n_atoms": natoms}
        for device in ["cpu", "cuda"]:
            for cueq in ([False, True] if (device == "cuda" and have_cueq) else [False]):
                tag = device + ("+cueq" if cueq else "")
                try:
                    calc, applied = make_calc(device, cueq)
                    a = sc0.copy(); a.calc = calc
                    rng = np.random.default_rng(0)
                    # warmup (also perturbed, to pay graph-compile before timing)
                    for _ in range(SP_WARMUP):
                        a.rattle(stdev=0.005, seed=int(rng.integers(1 << 30)))
                        a.get_forces()
                    _sync(device)
                    ts = []
                    for _ in range(SP_REPS):
                        a.rattle(stdev=0.005, seed=int(rng.integers(1 << 30)))  # invalidate cache
                        t0 = time.perf_counter()
                        a.get_forces()                                          # real eval
                        _sync(device)
                        ts.append(time.perf_counter() - t0)
                    entry[tag] = {"mean_s": float(np.mean(ts)), "std_s": float(np.std(ts)),
                                  "cueq_applied": bool(applied)}
                    del calc, a
                    if device == "cuda":
                        torch.cuda.empty_cache()
                except Exception as e:
                    entry[tag] = {"error": repr(e)[:300]}
                    print(f"  [s1] {natoms} atoms {tag} FAILED: {e!r}", flush=True)
        if isinstance(entry.get("cpu"), dict) and "mean_s" in entry["cpu"] \
           and isinstance(entry.get("cuda"), dict) and "mean_s" in entry["cuda"]:
            entry["speedup_cpu_over_cuda"] = entry["cpu"]["mean_s"] / entry["cuda"]["mean_s"]
        rows.append(entry)
        sp = entry.get("speedup_cpu_over_cuda")
        msg = f"  [s1] {natoms:5d} atoms  cpu={entry.get('cpu',{}).get('mean_s',float('nan')):.4f}s  " \
              f"cuda={entry.get('cuda',{}).get('mean_s',float('nan')):.4f}s"
        if sp:
            msg += f"  speedup={sp:.1f}x"
        print(msg, flush=True)
    return {"cpu_threads": T_HI, "ncores": NCORES, "cueq_installed": have_cueq, "rows": rows}


# ---------- stage 2: warm per-path cost, threads x strategy ----------
def _measure_config(bulk, device, threads, shared):
    import torch
    torch.set_num_threads(threads)
    if shared:
        calcs, _ = make_calc(device, False)
    else:
        calcs = [make_calc(device, False)[0] for _ in range(NEB_TOTAL)]
    times, eas = [], []
    for i in range(1 + WARM_RUNS):          # 1 cold + WARM_RUNS warm
        t0 = time.perf_counter()
        ea = run_one_neb(bulk, calcs, shared)
        _sync(device)
        times.append(time.perf_counter() - t0); eas.append(ea)
    peak_gb = float(torch.cuda.max_memory_allocated() / 1e9) if device == "cuda" else 0.0
    warm = times[1:]
    return {"cold_s": times[0], "warm_mean_s": float(np.mean(warm)),
            "warm_std_s": float(np.std(warm)), "all_s": times, "Ea_eV": eas,
            "peak_gb": peak_gb, "Ea_ok": bool(all(0.20 <= e <= 0.32 for e in eas))}


def stage2_warm(device="cuda"):
    from ase.io import read
    bulk = read(STRUCT)
    configs = {
        f"shared@{T_LO}t":    dict(threads=T_LO, shared=True),
        f"shared@{T_HI}t":    dict(threads=T_HI, shared=True),
        f"per-image@{T_HI}t": dict(threads=T_HI, shared=False),
    }
    out = {}
    for name, cfg in configs.items():
        try:
            r = _measure_config(bulk, device, cfg["threads"], cfg["shared"])
            out[name] = r
            print(f"  [s2] {name:16s} warm={r['warm_mean_s']:.1f}s (cold {r['cold_s']:.1f}s) "
                  f"E_a={r['Ea_eV'][-1]:.3f} peak={r['peak_gb']:.2f}GB", flush=True)
        except Exception as e:
            out[name] = {"error": repr(e)[:300]}
            print(f"  [s2] {name} FAILED: {e!r}", flush=True)
    # pick fastest valid strategy (shared vs per-image) for stage 3
    best = min((k for k, v in out.items() if isinstance(v, dict) and "warm_mean_s" in v),
               key=lambda k: out[k]["warm_mean_s"], default=None)
    out["_best_strategy"] = {"shared": ("shared" in best) if best else True,
                             "name": best, "warm_mean_s": out[best]["warm_mean_s"] if best else None}
    return out


# ---------- stage 3: process-parallel throughput ----------
def throughput_worker(cfg):
    import torch
    from ase.io import read
    device = cfg["device"]
    torch.set_num_threads(cfg["threads_per_worker"])
    bulk = read(cfg["struct"])
    shared = cfg["shared"]
    if shared:
        calcs, _ = make_calc(device, False)
    else:
        calcs = [make_calc(device, False)[0] for _ in range(NEB_TOTAL)]
    run_one_neb(bulk, calcs, shared)        # 1 warmup path (not counted)
    _sync(device)
    t0 = time.perf_counter()
    for _ in range(cfg["paths"]):
        run_one_neb(bulk, calcs, shared)
        _sync(device)
    wall = time.perf_counter() - t0
    peak_gb = float(torch.cuda.max_memory_allocated() / 1e9) if device == "cuda" else 0.0
    return {"paths": cfg["paths"], "wall_s": wall, "peak_gb": peak_gb}


def stage3_throughput(shared, device="cuda"):
    ctx = mp.get_context("spawn")
    levels = []
    for K in K_LIST:
        tpw = max(1, NCORES // K)
        cfg = {"device": device, "struct": str(STRUCT), "shared": shared,
               "paths": PATHS_PER_WORKER, "threads_per_worker": tpw}
        try:
            with ctx.Pool(K) as pool:
                res = pool.map(throughput_worker, [cfg] * K)
            total = sum(r["paths"] for r in res)
            slowest = max(r["wall_s"] for r in res)          # conservative: gated by slowest worker
            pph = total / slowest * 3600.0
            peak = max(r["peak_gb"] for r in res)
            levels.append({"K": K, "threads_per_worker": tpw, "paths_completed": total,
                           "slowest_worker_s": slowest, "paths_per_hour": pph,
                           "per_path_s": slowest / PATHS_PER_WORKER, "peak_gb_per_worker": peak})
            print(f"  [s3] K={K:2d} tpw={tpw:3d}  {total:2d} paths  {pph:6.1f} paths/hr  "
                  f"per-path {slowest/PATHS_PER_WORKER:.1f}s  peak/wkr {peak:.2f}GB", flush=True)
        except Exception as e:
            levels.append({"K": K, "error": repr(e)[:300]})
            print(f"  [s3] K={K} FAILED (likely OOM): {e!r}", flush=True)
            break
    return {"paths_per_worker": PATHS_PER_WORKER, "shared_strategy": shared, "levels": levels}


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out = {}
    import torch
    out["env"] = {
        "mace": __import__("mace").__version__, "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "capability": list(torch.cuda.get_device_capability(0)) if torch.cuda.is_available() else None,
        "cueq_installed": cueq_installed(), "ncores": NCORES, "T_lo": T_LO, "T_hi": T_HI,
    }
    json.dump(out, open(OUT, "w"), indent=2)
    print(f"[s0] {out['env']}", flush=True)

    print("=== stage 1: single-point scaling ===", flush=True)
    try:
        out["single_point"] = stage1_single_point()
    except Exception as e:
        out["single_point"] = {"error": repr(e)[:500]}
        print(f"  [s1] STAGE FAILED: {e!r}", flush=True)
    json.dump(out, open(OUT, "w"), indent=2)

    print("=== stage 2: warm per-path (threads x strategy) ===", flush=True)
    try:
        out["warm_path"] = stage2_warm()
    except Exception as e:
        out["warm_path"] = {"error": repr(e)[:500]}
        print(f"  [s2] STAGE FAILED: {e!r}", flush=True)
    json.dump(out, open(OUT, "w"), indent=2)

    shared_best = out.get("warm_path", {}).get("_best_strategy", {}).get("shared", True)
    print(f"=== stage 3: throughput (shared={shared_best}) ===", flush=True)
    try:
        out["throughput"] = stage3_throughput(shared=shared_best)
    except Exception as e:
        out["throughput"] = {"error": repr(e)[:500]}
        print(f"  [s3] STAGE FAILED: {e!r}", flush=True)
    json.dump(out, open(OUT, "w"), indent=2)

    print(f"done -> {OUT}", flush=True)


if __name__ == "__main__":
    main()

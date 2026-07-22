# GPU benchmark — RTX 5090 MLIP-NEB farm (2026-07-22)

Node: AutoDL RTX 5090 (32 GB, Blackwell sm_120), 208-core host, driver 580.142.
Stack: mace-torch 0.3.16, torch 2.8.0+cu128. Model: zero-shot MACE-MP-0 medium,
float32 (same physics as the tracer bullet — this measures **compute**, not new
science). Script: `scripts/02_gpu_benchmark.py`. Raw data: `benchmark.json`.

This benchmark exists because the CPU-vs-GPU tracer-bullet re-run showed only a
**2× NEB speedup** — far below the 30–100× a GPU should give — and we needed to
know whether that was a real ceiling or a starved-GPU artifact before committing
the screening-farm budget. Answer: **artifact.** All three findings below.

> **Correction note.** The v1 benchmark had two measurement bugs (single-point
> timing hit ASE's force cache → fake ~90 µs flat numbers; a "load-once" shared
> calculator silently tripled per-path cost). Both are fixed in the script now
> in the repo; the numbers below are the corrected v2 run.

---

## Finding 1 — GPU force-eval speedup grows with system size (20× → 72×)

Single-point force evaluation, cache-safe (positions rattled 0.005 Å before each
timed call so every call is a real evaluation with a fresh neighbour list).

| supercell | atoms | CPU (16→64 thr) | CUDA | **speedup** |
|-----------|------:|----------------:|-----:|------------:|
| 2×2×2 | 160 | 0.635 s | 0.032 s | **19.6×** |
| 3×3×3 | 540 | 1.923 s | 0.042 s | **45.9×** |
| 4×4×4 | 1280 | 3.759 s | 0.062 s | **61.1×** |
| 5×5×5 | 2500 | 6.658 s | 0.092 s | **72.4×** |

The tracer-bullet 2× was entirely the 159-atom cell starving the GPU. At the
**4×4×4 pinning-radius size (1280 atoms) the speedup is 61×**, still climbing at
2500 atoms. This is the leading indicator for the campaigns that actually
motivated the GPU:
- **pinning-radius extraction** (≥4×4×4, single big cells) → ~60× per force call;
- **Phase-5 nanosecond MD** (large cell, millions of steps) → GPU-native;
- **active-learning fine-tuning** (training) → GPU-native.

## Finding 2 — Use a per-image calculator, NOT a shared one (3.4× per path)

Warm per-path cost of the tracer-bullet V_I hop CI-NEB (7 images), model loaded
once per worker and reused across paths:

| strategy | threads | warm/path | note |
|----------|--------:|----------:|------|
| shared calculator | 16 | 46.2 s | recompute forced each optimizer step |
| shared calculator | 64 | 46.2 s | thread count irrelevant — it's recompute, not CPU |
| **per-image calculator** | 64 | **13.7 s** | correct design; beats tracer bullet's 17.6 s |

`allow_shared_calculator=True` makes ASE recompute the whole band's forces on
every image's `get_potential_energy()` — a **3.4× pessimization**, not the
load-once win it looks like. Keep the original per-image-calculator NEB design.
E_a = 0.259 eV held across all 10 runs (regression check passed).

## Finding 3 — One card sustains ~1500 NEB paths/hour; farm is not budget-bound

Process-parallel throughput, K persistent workers sharing the one GPU, CPU cores
split across workers (208/K each), fixed 3 paths/worker after 1 warmup:

| K workers | cores/worker | per-path latency | **paths/hour** | VRAM/worker |
|----------:|-------------:|-----------------:|---------------:|------------:|
| 1  | 208 | 11.7 s | 308  | 0.44 GB |
| 8  | 26  | 21.0 s | 1369 | 0.44 GB |
| 12 | 17  | 28.6 s | **1509** | 0.44 GB |

Per-path latency rises with K (GPU time-slicing + fewer cores each) but aggregate
throughput keeps climbing to ~1500/hr; 8→12 is +10% (plateauing — **K≈8–12 is the
sweet spot**). VRAM is only **0.44 GB/worker** — the 32 GB card is nowhere near
memory-bound, so K is limited by host cores / GPU time-slicing, not memory.

### Campaign budget (this dissolves the 70-hour / ¥150 worry)

- Measured: 2000 tracer-class paths ÷ 1509 /hr ≈ **1.3 h** on one card.
- Conservative (fine-tuned model + tighter convergence, assume 5× the tracer
  path cost): **~6.6 h**.
- At ~¥2.2/hr that is **¥3–15** for the whole ranking campaign — the farm is
  compute-trivial. Throughput, not budget, is the design axis.

---

## Not yet working: cuEquivariance

cuEq installs and imports on the box, but mace-torch 0.3.16 + this cuEq version
throw `'SegmentedPolynomialNaive' object has no attribute 'buffer_num_segments'`
at calculator-build time — an API-version mismatch, **not** a missing Blackwell
wheel. Parked: the 60× single-point win already lands the case for the GPU. To
revisit, pin a matched mace/cueq pair (needs testing) and re-run stage 1 —
`cuda+cueq` will populate if it engages.

## How to reproduce

```bash
# on the AutoDL box, repo unpacked to /root/autodl-tmp/run/perovskite-screening
python scripts/02_gpu_benchmark.py   # writes results/gpu/benchmark.json, ~20 min
```
Stages are guarded and JSON is written after each, so a crash (e.g. OOM at high
K) still leaves partial results.

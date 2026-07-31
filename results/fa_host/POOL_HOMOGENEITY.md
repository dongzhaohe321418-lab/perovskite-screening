# Host-pool homogeneity — the v2/v3 offset is relaxation depth, not sampling

**10 new members were generated for the n = 10 expansion. They came out 277 meV below
pool_v2 with Mann–Whitney p = 0.001 — same sampler, same script. The cause is a parameter
I changed without noticing: pool_v2 was built at `fmax = 0.03`, and I passed `0.02`.**

## Diagnosis

| | pool_v2 (18) | pool_v3 (10) |
|---|---|---|
| relaxation target | **fmax = 0.03** | **fmax = 0.02** |
| achieved fmax (median) | 0.0242 | 0.0171 |
| FIRE steps (median) | 228 | 517 |
| energy mean | −1065.709 eV | −1065.986 eV |
| energy sd | 0.150 | 0.156 |

Separation 277 meV = 1.81 pooled sd; only 4 of 10 new members fall inside the v2 range.

**Direct test.** Three pool_v2 members were re-relaxed from their 0.03 state to 0.02:

    m00: −318.2 meV   (fmax 0.0296 → 0.0194, max atom move 0.663 Å, 403 steps)
    m05: −546.3 meV   (fmax 0.0290 → 0.0200, max atom move 0.840 Å, 545 steps)
    m11: −163.6 meV   (fmax 0.0295 → 0.0194, max atom move 0.256 Å, 141 steps)

The drops bracket the 277 meV offset. The two pools are the **same population at different
relaxation depths**, not different populations.

This is the same lesson as the earlier endpoint work in a new place: on this soft
octahedral-tilt-plus-FA-rotation landscape, `fmax = 0.03` and `fmax = 0.02` are not
cosmetically different — hundreds of meV and atomic motions up to 0.84 Å separate them.

## Does this contaminate the existing n = 7 statistics? No — checked, not assumed

`scripts/22_paired_pilot.py` re-relaxes **both endpoints** to `--endpoint-fmax` (default
0.02) before building each band, and all 54 rerun rows record an achieved endpoint
`fmax = 0.0200`. Barriers therefore never inherit the host member's own relaxation depth.
**The published GA/Sr numbers stand.**

## What it does affect

The host **pool** is inhomogeneous. Mixing 0.03-relaxed with 0.02-relaxed members would
reintroduce precisely the confound the pool-separation rule exists to prevent: "which host
member" would partly mean "which relaxation depth". That is a nuisance variable inside a
paired design built to remove nuisance variables.

**Fix applied** (job `28721f3e`): all 18 pool_v2 members re-relaxed to `fmax = 0.02`.

| | before | after |
|---|---|---|
| pool_v2 mean | −1065.709 eV | **−1065.972 eV** |
| separation from v3 | 276.8 meV | **14.2 meV** |
| Mann–Whitney p | **0.001** | **0.792** |

Per-member drop: mean −262.6 meV (range −599.1 to −88.6); median atom displacement 0.269 Å,
max 0.840 Å; all 18 converged. **Harmonisation resolves the split completely** — the two
sets are one population, and relaxation depth was the entire cause.

## Decision: one homogeneous 28-member pool, all paths re-run

A first draft of this note recommended the cheaper route — keep the 18-member 0.03 pool and
generate the 8 new members at 0.03 to match — on the assumption that harmonising would be
expensive. **That assumption was wrong and the recommendation is withdrawn:** harmonising 18
members took a single GPU job, and it worked.

The remaining cost is real and is stated rather than glossed. Harmonisation moved host
geometries by up to 0.84 Å, so the existing 54 bands were built on host structures that no
longer exist in the harmonised pool. Keeping them would leave the corpus mixing two host
geometry sets — the very confound the pool-separation rule exists to prevent. The full
corpus is therefore re-run: **28 hosts × 3 systems = 84 paths ≈ 3.2 GPU-h** (job
`7022c547`), supporting up to ~11 pairs per dopant instead of 7.

The existing n = 7 results are **preserved, not discarded**. They remain valid on their own
pool; they are superseded only as the baseline for the expansion.

## Prevention

The pool's relaxation target is now part of its identity, not an incidental CLI argument.
`pool_v3_harmonised/` carries `results/fa_host/pool_v3_harmonised/harmonise.json` (per-member before/after) and
`results/fa_host/pool_v3_harmonised/expansion.json` (generation record), and any future pool extension must state and match
`fmax` explicitly. On this soft octahedral-tilt-plus-FA-rotation landscape, 0.03 and 0.02
are not cosmetically different: they differ by hundreds of meV and by atomic motions
approaching 1 Å.

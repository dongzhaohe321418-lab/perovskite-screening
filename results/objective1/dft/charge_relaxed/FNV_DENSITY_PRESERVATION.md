# FNV charge-density preservation record

**The ~2 GB of converged charge densities that feed the FNV correction have been pulled off
perishable HPC scratch and copied to durable storage.** This file is the git-tracked pointer;
the binary densities themselves are deliberately NOT in git (2 GB of HDF5 would bloat the
history and they are regenerable in principle but only by re-running both NEB legs).

## Why this was done

`charge_correction_check.md` recorded these densities as the perishable input to the pending
FNV correction: they lived only in HPC scratch, which is reclaimable. On 2026-08-04 the scratch
copies were verified intact and preserved before any reclamation could lose them.

## What was preserved

10 converged charge densities (pp.x plot_num=11 input for FNV), 197 MB each:

- q=0 leg (job `374e51f1`): images 1–5
- q=+1 leg (job `98199034`): images 1–5

Each `neb.save` also carries its `data-file-schema.xml` (needed to interpret the grid), packaged
alongside.

## Where it is (NOT in git)

| item | location |
|---|---|
| tarball | `~/Desktop/perovskite-screening/fnv_densities_preserve/fnv_densities.tar.gz` (1.0 GB) |
| tarball sha256 | `0c3e7e3c86929e495755c320a0c66b40a5e7af9b6aceb45688016081a82a845a` |
| per-density hashes | `fnv_densities_preserve/FNV_DENSITY_MANIFEST.txt` (also committed below) |
| original (still on scratch as of 2026-08-04) | `/home/ericdft/scratch/.claude-science/jobs/{374e51f1,98199034}-…/run/out/neb_{1..5}/neb.save/charge-density.hdf5` |

## Integrity chain (verified end-to-end 2026-08-04)

1. Per-file sha256 taken on HPC at pack time → `FNV_DENSITY_MANIFEST.txt`.
2. Whole-tarball sha256 taken on HPC → `0c3e7e3c86929e495755c320a0c66b40a5e7af9b6aceb45688016081a82a845a`.
3. Transferred in 6 chunks (256 MB single-file transfer limit), reassembled locally.
4. Reassembled tarball sha256 **matches** the HPC value byte-for-byte.
5. Unpacked; **all 10** per-density sha256 match the manifest.

## What it does NOT change

Preserving the input does not compute the correction. FNV `ΔE_corr` remains **PENDING** — the
`pp.x` potential step and PI authorization are still required, per `charge_correction_check.md`.
The barriers remain unextracted; this only removes the perishability risk on the input.

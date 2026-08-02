# Production CI-NEB pair — BOTH LEGS CONVERGED (raw records committed)

**Status date: 2026-08-02. Barriers are NOT extracted in this record** — extraction is a
separate, gated analysis step (see below).

| leg | job | iterations | final per-image error (eV/Å) | exit | archive |
|---|---|---|---|---|---|
| q=0  | `374e51f1` | **36** | all ≤ 0.05 (see `q0_production/q0_neb.out.gz`) | JOB DONE, 0 | 38 snapshots, `q0_production/q0_neb_archive.tar.gz` |
| q=+1 | `98199034` | **37** | 0.0451 0.0261 0.0328 0.0462 0.0499 | JOB DONE, 0 | 39 snapshots, `q1_production/q1_neb_archive.tar.gz` |

Both legs ran the pair-locked production fingerprint (conv_thr=1e-8, degauss=0.005, path_thr=0.05,
CI auto, 5 images, Γ, PBE+D3(BJ)), differing only in `tot_charge`.

## Input custody
- q=0: remote run input sha256 `04acee190675ec82…` — byte-identical to the PI-approved hash.
- q=+1: committed repo input matches the PI-approved `9954e6b171c56551…` byte-exactly. The
  *run copy* on the cluster differs by exactly one line — the job preamble's documented
  `pseudo_dir` substitution (`$HOME/pseudo` → `/home/ericdft/pseudo`), verified by unified diff.
  This substitution is applied by `cmd.sh` at job start on every submission and does not touch
  any physical parameter.

## Raw records committed (hashes in each leg's SHA256/REMOTE_SHA256 file)
- `q0_production/`: `q0_neb.out.gz`, `q0_neb.path.final.gz`, `q0_neb.dat.gz`, `q0_neb.xyz.gz`,
  full append-only archive tarball, `q0_verify_last.json`, `q0_cmd.sh`.
- `q1_production/`: `q1_neb.out.gz`, `q1_neb.path.gz`, `q1_cineb.neb.in` (run copy), full
  archive tarball, `CONVERGENCE_SUMMARY_q1.json` (parsed from the archived raw itself).
- `q1/q1_initial_relaxed.extxyz`, `q1/q1_final_relaxed.extxyz`: the q=+1 endpoint structures
  (closes the F-003 'input source absent' gap).

## What is NOT in this record
No barrier value, no forward/reverse activation energy, no charge-state ordering, and no
comparison to the Tyagi ordering (ban stands). The raw outputs contain activation-energy lines;
they are deliberately not quoted. Extraction requires: (1) this evidence commit audited, and
(2) an explicit `check_action` ALLOW for the barrier-extraction/publication step.

# HARNESS_TRIAL result — workflow validation, NO scientific content

**Tag: HARNESS_TRIAL. Nothing in this file is a barrier, a mechanism statement, or a scientific
result. The trial exists solely to answer: can the harness archive a live q=0 band, and can
`neb.x` genuinely resume from that archive?**

## Outcome against the five approved pass criteria

| # | criterion | outcome |
|---|---|---|
| 1 | ≤2 NEB updates fresh + 1 restart evaluation, no CI | **MET** — phase 1: nstep_path=2 (2 updates, `JOB DONE`); restart: nstep_path=3=istep+1 (1 evaluation) |
| 2 | per-snapshot neb.path, per-image structures, hashes, energies | **MET** — both snapshots carry `neb.path` (sha256), 5-frame `images.extxyz` (sha256), 5 energies; state-ID field present in META (see gap below) |
| 3 | genuine restart from the archive, not mere re-reading | **MET as re-evaluation, NOT as position update** — QE resumed the iteration counter and spent 1h16m recomputing SCF from the archived state (bit-non-identical re-converged values); no Broyden move ran at this budget, so zero atoms moved. See decomposition below. |
| 4 | stop on any failure, raw outputs preserved | **MET** — demonstrated live: v1 halted in env setup (exit 1), v3 halted at the archive step (exit 4) with the raw traceback preserved; v4's asserts all passed |
| 5 | all products tagged, no barrier reported | **MET** — no activation-energy value from any trial output appears in any report or statistic |

## What the restart demonstrably did (criterion 3, stated precisely)

`neb.x` parsed `restart_mode='restart'`, **resumed at iteration 3** (not 1), and ran a full SCF
force evaluation on all three interior images (1h16m wall; ~25 min of self-consistency per
interior image, read from the tcpu stamps). The re-archived snapshot differs from the
pre-restart snapshot in exactly the fields a genuine re-evaluation updates:

- `istep`: 2 → 3
- image energies re-converged: per-image |ΔE| = 0, 1×10⁻⁸, 2×10⁻⁸, 4×10⁻⁸, 0 au
  (**max 4×10⁻⁸ au ≈ 1.1 µeV** — an earlier version of this file wrote "≤3×10⁻⁹ au", which
  was wrong by an order of magnitude; corrected against the printed snapshot values)
- **477 of 636 gradient rows updated**, |Δgrad| up to 2.7×10⁻⁴ au (median 4×10⁻⁶) against
  gradient magnitudes up to 4.3×10⁻² au — the ~10⁻⁵-relative wiggle of a re-converged SCF at
  identical positions
- **0 position rows changed**

**Recompute-vs-reread is the decisive discriminator, and it separates v4 from the v2 no-op:**
a file re-read gives bit-identical values — v2's post-"restart" `neb.path` had the *same*
sha256 and zero SCF time. v4 spent 1h16m of SCF and produced re-converged, non-bit-identical
energies and gradients. That — not the hash difference per se, and *not* the near-zero energy
movement (which an earlier audit cell mislabelled "evidence of genuine continuation"; energy
*stability* at fixed positions is evidence of nothing) — is what demonstrates the archived
snapshot is a live optimiser state QE genuinely resumes from.

Positions are unchanged because QE applies the Broyden move *after* the force evaluation, and
the `nstep_path` cap stops the run at the evaluation. So the trial proves: **the archived
snapshot is a genuine, resumable optimiser state — QE accepts it, continues the iteration
counter, and rebuilds the force state from it.** What the trial does NOT show (by design, at
the approved budget) is a post-restart position update; that would need one more update beyond
the approved cap and was not run.

An earlier in-job assert said "band hashes differ: restart genuinely continued" — true, but the
hash difference is istep+energies+gradients, **not positions**. Recorded here so the claim
cannot be read as larger than it is.

## Failure history of the trial itself (each stopped at its own step, per criterion 4)

| attempt | failed at | cause | fix |
|---|---|---|---|
| v1 | env setup, 0 s | `oneapi setvars.sh` exits non-zero under `set -e` | proven conda-qe preamble |
| v2 | post-phase-1 | `neb.x` exits `STOP 1` at the nstep_path cap (normal for capped runs); `-e` killed the script after the band was written | `|| true` + `JOB DONE` grep; **and** audit found its "restart" ran ZERO iterations (cumulative-nstep_path bug) |
| v3 | archive step, exit 4 | cluster python has no `ase` | stdlib-only extxyz writer (round-trip validated) |
| v4 | — | all asserts passed | — |

The v2 zero-iteration no-op is the trial's most important catch: a restart with
`nstep_path ≤ istep` parses, prints `JOB DONE`, and does nothing. The harness now reads `istep`
from the archive and **refuses** such a restart (`ValueError`), and the job asserts ≥1 iteration
ran. This is precisely the silent failure mode the trial existed to flush out.

## Declared gap (unchanged)

Per-snapshot state-ID cosine requires a `projwfc.x` projection on the band's wavefunctions;
the wavefunctions for images 2–4 remain on the cluster (`phase2/out/neb_*/neb.save/wfc1.hdf5`,
~4.2 GB each). The `identify_state()` function is validated; wiring it to a live projection is
follow-up work and is NOT claimed as done.

## Condition-5 verdict proposal

Archive ✓, per-image structures ✓, hashes ✓, genuine resume ✓ (scope above), stop-on-failure ✓,
tagging ✓. **Proposed: condition 5 PARTIAL → PASS with the position-update scope and the
state-ID wiring gap recorded.** The PI makes the call.

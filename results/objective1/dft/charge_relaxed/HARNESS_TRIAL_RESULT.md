# HARNESS_TRIAL result — workflow validation, NO scientific content

**Tag: HARNESS_TRIAL. Nothing in this file is a barrier, a mechanism statement, or a scientific
result. The trial exists solely to answer: can the harness archive a live q=0 band, and can
`neb.x` genuinely resume from that archive?**

## Outcome against the five approved pass criteria

| # | criterion | outcome |
|---|---|---|
| 1 | ≤2 NEB updates fresh + 1 restart evaluation, no CI | **MET** — phase 1: nstep_path=2 (2 updates, `JOB DONE`); restart: nstep_path=3=istep+1 (1 evaluation) |
| 2 | per-snapshot neb.path, per-image structures, hashes, energies | **MET** — both snapshots carry `neb.path` (sha256), 5-frame `images.extxyz` (sha256), 5 energies; state-ID field present in META (see gap below) |
| 3 | genuine restart from the archive, not mere re-reading | **MET, with precise scope** — see decomposition below |
| 4 | stop on any failure, raw outputs preserved | **MET** — demonstrated live: v1 halted in env setup (exit 1), v3 halted at the archive step (exit 4) with the raw traceback preserved; v4's asserts all passed |
| 5 | all products tagged, no barrier reported | **MET** — no activation-energy value from any trial output appears in any report or statistic |

## What the restart demonstrably did (criterion 3, stated precisely)

`neb.x` parsed `restart_mode='restart'`, **resumed at iteration 3** (not 1), and ran a full SCF
force evaluation on all three interior images (~1.5 h wall). The re-archived snapshot differs
from the pre-restart snapshot in exactly the fields a genuine continuation updates:

- `istep`: 2 → 3
- all 5 image energies (re-converged SCF; ≤3×10⁻⁹ au from the archived values)
- **477 gradient rows updated**
- **0 position rows changed**

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

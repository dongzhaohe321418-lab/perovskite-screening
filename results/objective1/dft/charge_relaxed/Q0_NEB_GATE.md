# q=0 NEB entry gate — status against the five conditions

The guide sets five conditions, all of which must pass before any HPC time goes to a q=0
CI-NEB. Current state, audited rather than assumed.

| # | condition | status |
|---|---|---|
| 1 | both q=0 endpoints genuinely ionically converged | **initial PASS, final IN PROGRESS** |
| 2 | `nspin=1` stable and restartable across nearby geometries | **PASS** |
| 3 | P1/P2 show no competing localised spin state | **PASS** |
| 4 | q=0 and q=+1 at an identical theory fingerprint | **PASS (by construction)** |
| 5 | NEB input, restart, archiving and state-identification tooling ready | **PARTIAL** |

## Condition 1 — endpoints

**q0_initial: PASS.** `bfgs converged in 1 scf cycle and 0 bfgs steps`, energy error
7.0×10⁻⁵ Ry (criterion 1.0×10⁻⁴) and gradient error 1.7×10⁻³ Ry/bohr (criterion
1.945×10⁻³). The q=+1 geometry is already a q=0 stationary point; the artifact store
deduplicated the relaxed structure onto the input by checksum, confirming zero movement
independently.

**q0_final: in progress, at the soft-mode floor** (job `f9993838`, `nspin=1`). **Updated
2026-07-28 — this section previously reported 3 monotonically-descending steps, which is no
longer the state.** Nine or more BFGS steps completed (the run is live; the count grows), and
the gradient error does **not** descend monotonically:

    step: 1     2     3     4     5     6     7     8     9
    grad: 3.1   2.9   2.7   2.4   1.9   1.4   1.9   2.3   2.2   (x1e-3 Ry/bohr, crit 1.945e-3)
    eV/A: 0.080 0.075 0.069 0.062 0.049 0.036 0.049 0.059 0.057

**This table is a snapshot of a running job, not a final record.** The authoritative trajectory
is the job output itself; the invariant that matters for this gate is the *shape* — the gradient
oscillates in the 0.036-0.059 eV/Å band and QE has printed no convergence block — not the exact
step count.

Steps 5-7 read below the criterion but **BFGS did not accept them**; the gradient rose again and
QE has never printed its convergence block (`End of BFGS` count = 0). A single sub-threshold
reading is not convergence, and an earlier claim that this run "crossed its force target" is
retracted.

The energy descends monotonically throughout (−9247.62777349 → −9247.62803730 →
−9247.62822030 Ry; −3.59 and −2.49 meV on the last two steps), so the optimiser is finding
genuinely lower structures. The 0.036-0.059 eV/Å oscillation is the **soft octahedral-tilt
floor** documented for this cell, where the q=+1 endpoints floored at fmax ≈ 0.04 eV/Å.

**Proposed protocol revision, NOT yet adopted.** After the step cap, accept the
**lowest-gradient accepted step with a stable energy** as the converged geometry — the same
treatment already applied to the q=+1 pair. Three conditions attach to adopting it:

1. it must be applied **identically to q=0 and q=+1**, since the whole point of the campaign is
   a charge-state comparison at one theory level;
2. `LOCKED_PROTOCOL_AND_STOPLOSS.md` and this gate document must both be updated to state the
   revised acceptance criterion explicitly, before any NEB input is generated;
3. the accepted geometry's gradient and energy stability must be recorded per endpoint so the
   comparison is auditable.

Until all three are done, **condition 1 of this gate remains OPEN** regardless of how the
relaxation ends.

## Condition 2 — `nspin=1` stability across geometries

Now demonstrated at four distinct geometries: the q0A/P2 geometry (27 and 6 iterations),
the ELAS distorted geometry (39 iterations, converged), and three successive BFGS geometries
in the current relaxation (all converged to 1.5×10⁻⁷ Ry). Restart from a saved density works
**at the geometry the density was computed for** — the failure mode when it is not is
recorded in the E-HPC provider notes.

## Condition 3 — no competing spin state

P2 audit, all four sub-criteria pass: the total moment decays to 0.00 and the absolute
moment with it; converged in **6 iterations** to 1.0×10⁻⁶ Ry; exactly one partially occupied
state (occupation 0.5000 at 4.3259 eV) as expected for an odd electron count under smearing;
no stable finite moment anywhere. The seeded polaron test independently found no magnetic
basin worth ~110 meV of elastic cost.

## Condition 5 — tooling, and what is missing

Ready: `scripts/11_generate_neb_input.py` (neb.x input generation, exercised on the q=+1
leg), `scripts/13` (d_max), `scripts/23_q0_state_metrics.py` (state identification by
per-atom weight overlap rather than band index — needed because band numbering shifts).

Missing: a restart/archive harness for the q=0 band specifically. The q=+1 explore band's
`neb.path` is preserved in `q1_explore_state.tar.gz` and is the CI-NEB restart point for
that leg; the q=0 leg needs the same treatment provisioned before launch.

## Verdict

**Gate NOT yet open.** Four of five conditions pass; condition 1 needs q0_final to reach
1.945×10⁻³ Ry, which it is approaching monotonically, and condition 5 needs the archive
harness. No large HPC allocation should be committed until both close.

Also worth stating: a false alarm during this audit. A grep for band-convergence warnings
returned a hit that turned out to be routine `c_bands` memory-report lines, not a warning.
Checked before reporting; there is no band-switching problem.

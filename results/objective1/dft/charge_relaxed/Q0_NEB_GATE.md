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

**q0_final: in progress and behaving correctly for the first time** (job `f9993838`,
`nspin=1`). Three BFGS steps completed, each with a fully converged SCF (1.5×10⁻⁷ Ry), and
the gradient error is descending monotonically toward the target:

    step 1:  energy error 9.7e-5 Ry   gradient error 3.1e-3 Ry/bohr
    step 2:  energy error 9.4e-5 Ry   gradient error 2.9e-3
    step 3:  energy error 1.0e-4 Ry   gradient error 2.7e-3    (target 1.945e-3)

Energies −9247.62700020 → −9247.62709463 → −9247.62719485 Ry, descending smoothly. Every
previous q0_final attempt used `nspin=2` and either diverged or plateaued at 1.4×10⁻³ Ry
without completing a single step.

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

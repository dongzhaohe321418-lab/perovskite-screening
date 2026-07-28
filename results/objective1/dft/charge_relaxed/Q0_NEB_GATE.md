# q=0 NEB entry gate — status against the five conditions

The guide sets five conditions, all of which must pass before any HPC time goes to a q=0
CI-NEB. Current state, audited rather than assumed.

| # | condition | status |
|---|---|---|
| 1 | both q=0 endpoints genuinely ionically converged | **PASS — both converged** (final: QE block, 10 BFGS steps, 2026-07-28) |
| 2 | `nspin=1` stable and restartable across nearby geometries | **PASS** |
| 3 | P1/P2 show no competing localised spin state | **PASS** |
| 4 | q=0 and q=+1 at an identical theory fingerprint | **PASS (by construction)** |
| 5 | NEB input, restart, archiving and state-identification tooling ready | **PARTIAL — 4 of 5 components validated** (`NEB_HARNESS.md`); the harness is not yet exercised on a live q=0 job |

## Condition 1 — endpoints

**q0_initial: PASS.** `bfgs converged in 1 scf cycle and 0 bfgs steps`, energy error
7.0×10⁻⁵ Ry (criterion 1.0×10⁻⁴) and gradient error 1.7×10⁻³ Ry/bohr (criterion
1.945×10⁻³). The q=+1 geometry is already a q=0 stationary point; the artifact store
deduplicated the relaxed structure onto the input by checksum, confirming zero movement
independently.

**q0_final: CONVERGED** (job `f9993838`, `nspin=1`, 2026-07-28). QE printed its own
convergence block — no protocol revision was needed:

    Energy error   = 9.8E-05 Ry     (criterion 1.0E-04)   PASS
    Gradient error = 1.6E-03 Ry/Bohr (criterion 1.9E-03)  PASS
    bfgs converged in 11 scf cycles and 10 bfgs steps

Full gradient trajectory (×10⁻³ Ry/bohr): 3.1 2.9 2.7 2.4 1.9 1.4 1.9 2.3 2.2 2.0 → **1.6
accepted**. The mid-run oscillation (1.4 rising to 2.3) was real — an earlier claim that the run
had "crossed its force target" at the transient 1.4 reading was retracted — but the optimiser
worked through the soft-mode floor and converged formally. The proposed
lowest-accepted-step protocol revision is therefore **withdrawn as unnecessary**; it was never
adopted.

Final energy **−9247.62842357 Ry**. Displacement from the q=+1 final geometry: max 0.047 Å,
mean 0.010 Å, no atom over 0.05 Å — unlike `q0_initial` (which converged in zero steps), this
endpoint did relax, but only slightly, consistent with the delocalised electron adding no
strong local force.

**The q=0 endpoint pair, both converged at identical theory level:**

| | E (Ry) | steps |
|---|---|---|
| q0_initial | −9247.62643363 | 0 |
| q0_final | −9247.62842357 | 10 |
| asymmetry | **−27.1 meV** (final below initial) | |

(q=+1 pair: +11.9 meV, final above initial. The two charge states prefer opposite ends of the
path — noted, not yet interpreted; it awaits the NEBs.)

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

**Built 2026-07-28:** `scripts/26_neb_harness.py` — append-only iteration archive, restart
verification, and state identification by per-atom weight cosine (never band index). Validated
by round-tripping the **real** q=+1 explore band written by `neb.x` itself (5 images × 159
atoms, 2 snapshots, hash-verified), not a synthetic fixture. Regression test [31] pins every
value. Detail in `NEB_HARNESS.md`.

**Still missing, and honestly circular:** the harness has not been exercised on a *live* q=0
job, and it cannot be until a q=0 NEB runs — which this gate exists to prevent. The proposed
resolution is to treat the **first** q=0 NEB as the harness's live trial: archiving enabled
from iteration 1, archive verified after the first few iterations, job stopped immediately if
the round-trip fails. That is a bounded commitment, not a full CI-NEB, and it closes the
circularity rather than declaring the component done by assertion.

## Verdict

**Gate: 4 of 5 conditions PASS. Condition 5 is PARTIAL — 4 of its 5 components are built and
validated; the harness has not been exercised on a live q=0 job.**

No CI-NEB submission. What *is* now defensible is a **bounded harness trial**: a short q=0 NEB
(explore tier, no CI, low iteration cap) run solely to exercise archiving and restart on a live
band, stopped as soon as the round-trip is verified or fails. That trial is not a scientific
result and its barrier must not be quoted. A full q=0 CI-NEB waits until this file records the
trial's outcome.

Also worth stating: a false alarm during this audit. A grep for band-convergence warnings
returned a hit that turned out to be routine `c_bands` memory-report lines, not a warning.
Checked before reporting; there is no band-switching problem.

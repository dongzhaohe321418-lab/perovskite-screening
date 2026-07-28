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

**The live trial RAN (2026-07-28, PI-approved, jobs e2273435 phase-1 + 0e4443ed restart) and
its result is in `HARNESS_TRIAL_RESULT.md`:** archive → verify → real `neb.x` restart
(resumed at iteration 3, 1h16m of SCF re-evaluation, re-converged non-bit-identical
energies/gradients) → re-archive, all succeeded. Restart is proven **as re-evaluation, not as
position update** (the budget cap stops before the Broyden move). The trial's ~0.98–1.29 eV
intermediate activation energies are **HARNESS_TRIAL output and remain unquotable**.

**PI verdict on the trial: harness validated; condition 5 stays PARTIAL** pending four closure
items: (1) at least one real `projwfc.x` → weights → cosine → JSON state-ID on the preserved
phase-2 wavefunctions (in progress); (2) production inputs regenerated at `degauss=0.005` with
an automated theory-fingerprint comparison against the q=+1 leg — the trial ran at the
generator default 0.01, fine for the harness, PROHIBITED for production; (3) the three
authority documents synchronised (this edit); (4) the regression suite green from a clean
clone.

## Verdict

**Gate: 4 of 5 conditions PASS. Condition 5 is PARTIAL — the live harness trial SUCCEEDED
(see above) and the PI has conditioned PARTIAL → PASS on four small closure items** (state-ID
closure on real wavefunctions; degauss=0.005 production inputs + fingerprint check; document
sync; clean-clone green suite).

No full q=0 CI-NEB submission until this file records condition 5 as PASS. The trial's
intermediate energies stay unquotable.

Also worth stating: a false alarm during this audit. A grep for band-convergence warnings
returned a hit that turned out to be routine `c_bands` memory-report lines, not a warning.
Checked before reporting; there is no band-switching problem.

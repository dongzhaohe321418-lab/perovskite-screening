# Charged-defect correction (FNV) — **PENDING**, with the input data located and inventoried

**Status: FNV ΔE_corr is NOT computed.** This document records (a) why the correction matters
for the q=+1 leg specifically, (b) exactly which committed/remote data the computation needs and
where it is, and (c) the gate decision that stops it here. It quantifies nothing and must not be
cited as a correction magnitude.

## Why this check exists

The q=+1 leg is a charged supercell under periodic boundary conditions, so its total energies
carry a spurious electrostatic self-interaction with the periodic images and the compensating
background. Freysoldt–Neugebauer–Van de Walle (FNV) is the standard correction. The q=0 leg is
neutral: its FNV correction is identically zero.

**The barrier is a difference, so most of the correction cancels — but not all of it.** Both the
initial-state and saddle-point images of the q=+1 path are the same +1 charge in the same cell,
so the leading monopole term (∝ q²α_M/2εL) is common to both and drops out of E_saddle − E_initial
exactly. What does *not* cancel is the part that depends on how the defect charge is
*distributed*: as the iodide vacancy's hole density delocalises or re-localises along the
migration path, both the model-charge width entering the FNV Gaussian and the
potential-alignment term change. The quantity that actually matters for this project is therefore

    Δ(ΔE_corr) = ΔE_corr(saddle) − ΔE_corr(initial)

not ΔE_corr itself. This is expected to be small relative to the leading term, but "expected
small" is not a measurement, and the whole point of the charge-state comparison is that the
q=+1 and q=0 barriers are being compared at one theory level — so any residual that survives
the difference is a systematic on exactly the quantity of interest.

## What the computation needs, and where it is

| ingredient | status | location |
|---|---|---|
| converged charge density, q=+1 images | **available** (197 MB per image, HDF5) | remote `jobs/98199034-…/run/out/neb_{1..5}/neb.save/charge-density.hdf5` |
| converged charge density, q=0 images | **available** (197 MB per image, HDF5) | remote `jobs/374e51f1-…/run/out/neb_{1..5}/neb.save/charge-density.hdf5` |
| total electrostatic potential grid | **NOT PRESENT** — needs `pp.x` with `plot_num=11` | would be generated from the densities above |
| cell + geometry | committed | `q{0,1}_production/` inputs and archived paths |
| dielectric constant ε | **not fixed** — see sensitivity note | literature range vs computed |
| pristine reference potential | derivable from the P1 pristine run | `q3_raw/` (P1 records committed) |

The `pp.x` step reads the existing densities, starts no new SCF, and alters no NEB state.

## Dielectric-choice sensitivity — why this cannot be a single number

FNV scales as 1/ε, so the correction inherits the full uncertainty of the dielectric constant,
and for a halide perovskite that choice is not obvious: the high-frequency (electronic) ε∞ and
the static ε₀ differ by a large factor because of the soft polar lattice, and which one is
appropriate depends on whether the lattice can screen on the timescale of the hop. **Any FNV
number reported for this system must therefore be reported as a range across that choice, with
the choice stated, not as a point value.** A single ΔE_corr with an unstated ε would be exactly
the kind of over-precise claim this project has retracted before.

## Why it stops here

`check_action(action="submit_production_job")` was consulted for the `pp.x` step on
2026-08-04 and returned **DENY**, with reasons `ACTIVE_BLOCKER_F-024`,
`NO_FINAL_AUDIT_FOR_COMMIT`, `POLICY_APPROVAL_REQUIRED`, `BUDGET_APPROVAL_REQUIRED`,
`PI_APPROVAL_REQUIRED`. The DENY is binding and was not retried. `ACTIVE_BLOCKER_F-024` is the
substantive one: F-024 is the finding that the regression suite's *success* receipts asserted
failure propositions, i.e. a truthfulness defect in the evidence layer. Until an audit cycle
confirms that fix on a descendant commit, nothing new should be derived from this evidence base
— including a correction that would later be applied to the barriers.

## What unblocks it

1. Audit confirmation of F-024 closure (fix `7a4f3b0e`; first queued snapshot containing it is
   `735e7f00`).
2. PI authorization covering the `pp.x` step.

Then: `pp.x` on images 1 and 3 of both legs → planar-averaged potential → FNV alignment against
the pristine reference → report Δ(ΔE_corr) as a range over ε∞…ε₀ with both endpoints stated.
The remote densities are the perishable input — they live in scratch, so if that space is
reclaimed this becomes a re-run of the NEB legs rather than a post-processing step.

> # SUPERSEDED — archived 2026-07-28
>
> Readiness audit that gated Objective 2's start; the gates it demanded are all met and recorded elsewhere.
>
> **Current authority: `results/objective2/CURRENT_STATUS.md`.** This file is retained verbatim below for provenance; do not cite it as current.

# Objective 2 readiness — audit of the proposed two-tier plan

**Verdict: the two-tier structure is adopted. One proposed gate does not survive contact
with the data, and a sixth gate is needed. Details below.**

## Agreed as proposed

- Preparation now / production later, with everything interim marked `EXPLORE`.
- Gates 1, 2, 3, 5 (stable physical q=0 state; identical final protocol including
  occupation scheme; both clean-baseline CI-NEBs converged; host and charge state fixed
  in advance and not switched mid-stream).
- The three-branch decision tree on the q0B outcome.
- Host-transfer validation before any FA-Cs conclusion — see the strengthening below.
- Strain anchor (d) may run in parallel but must precede any "chemical effect" claim.

## Gate 4 (GA⁺ ΔE_a anchor) — **cannot be used as a gate in its current state**

This is the one substantive disagreement. The existing GA anchor is not a converged
result, so requiring "the GA⁺ anchor is complete" would be satisfied by a number that
cannot bear the weight.

| quantity | value |
|---|---|
| ΔE_a(GA) at 2×2×2 | **70.3 meV** |
| ΔE_a(GA) at 3×3×3 | **334.8 meV** |
| finite-size ratio | **4.8×, not converged** |

Orientation dependence of the *same* additive at fixed composition:

| orientation | ΔE_a |
|---|---|
| xy-plane | 70.3 meV |
| xz-plane | 277.6 meV |
| tilted 60° | 182.3 meV |
| far control | −23.4 meV |

Spread = **207.2 meV, which is 2.9× the headline 70.3 meV effect.** The additive's
computed influence depends more on how it is oriented than on whether it is present.

For contrast, the strain anchor **is** finite-size converged (−41.5 meV at 2×2×2 vs
−40.8 meV at 3×3×3 per 1% tensile). Combining the two: a GA-induced local strain of only
**~1.7%** reproduces the entire 2×2×2 GA effect. So the current GA number cannot be
attributed to chemistry at all — strain alone accounts for it.

**Revised gate 4.** Before GA⁺ can serve as the pipeline-validation anchor it must be
re-established with: (i) finite-size convergence demonstrated, not assumed; (ii) an
orientation *ensemble* rather than a single configuration, reported as a distribution;
(iii) the strain contribution separated out, so the residual is the chemical effect.
Until then GA⁺ demonstrates only that the pipeline *runs*, not that it *correctly
describes an additive changing the barrier* — which is precisely what gate 4 was meant
to certify.

## Proposed additional gate 6 — additive effect vs configurational noise

The orientation spread above is not specific to GA. Any additive screening on this system
inherits it. A ranking is only meaningful if the between-additive differences exceed the
within-additive configurational spread.

**Gate 6:** for each additive, sample an orientation/position ensemble and report
ΔE_a as a distribution. Publish a ranking only where the separation between additives
exceeds the within-additive spread. A single-configuration ΔE_a per additive is an
`EXPLORE` result permanently, never a production ranking.

This also supplies the natural significance threshold, alongside the 59.5 meV
order-of-magnitude criterion already in ACCEPTANCE_GATE.md.

## Host-transfer validation — stronger than "recompute the baseline"

Agreed that the CsPbI₃/MAPbI₃ anchors are not an FA₀.₉₅Cs₀.₀₅PbI₃ baseline. Two additions:

1. The FA host is **already built** (`results/fa_host/`: `fa19cs1_pb20i60_233`,
   `fa19cspb20i59_232_vI`, plus an 8-member ensemble `fa_ensemble_00..07`) — the ensemble
   exists precisely because the FA orientations are not unique. Host transfer must
   therefore be validated **against the ensemble**, not a single member.
2. Host transfer must be re-validated for the **charge state** too. The q=0 spin
   localisation now under investigation sits on Pb dangling bonds; in a mixed-cation host
   the A-site environment around those Pb differs, so a q=0 solution found for CsPbI₃ does
   not transfer for free.

## Note on the existing dopant screen

`results/dopant_screen/` already holds a five-dopant MACE ranking (Sr/Ca/Ba/Bi@Pb, Br@I)
with ΔE_a from −131 to −37 meV. These are **substitutional dopants, not molecular
additives**, and they are MACE-level. They are useful as pipeline scaffolding and as a
sanity check on the new automation, but they are not Objective-2 results and their
ranking inherits the same configurational-noise question as gate 6.

## What starts now

Preparation only, all outputs labelled `EXPLORE`: candidate list and prioritisation;
structure generation across position / orientation / concentration; MACE path exploration
and configurational pre-screening; automation, directory layout, and results-table schema
designed so the orientation ensemble is a first-class dimension from the start rather
than retrofitted.

No DFT screening, and no ranking published, until gates 1-3, revised 4, 5, and 6 are met.

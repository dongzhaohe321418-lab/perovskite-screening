# Next-experiment design — executable protocols

Concrete designs for the ranked next steps, grounded in the confirmed corpus. Costs are priced
from the **measured 70 s/path** at MLIP level and the **measured 25% triple-yield** (9 of 36
attempted hosts became usable three-system pairs). Reads no Q2 barrier; MLIP-level throughout.

## The finding these designs respond to

Host configuration sets the barrier: host SD 57.3 meV vs dopant SD 4.6 meV (12.3×), residual
29.7 meV. Both additives are null with the 10× target excluded (GA CI [−25,+39], Sr [−42,+34]).
No structural predictor survives multiplicity correction. The open questions are therefore about
**resolution** (is there a sub-20 meV additive effect?), **generality** (does the null hold off
one concentration?), and **transferability** (is the 152 meV host spread physical or an MLIP
artifact?).

---

## E0 — Recover the 6 one-slot-away hosts (do this first; ~7 GPU-min)

**Why.** 6 hosts (members 3, 4, 10, 14, 18, 27) are admissible in two of three systems and fail
only one slot. Recovering that one path each lifts the paired n from 9 to 15 triples immediately
— a 67% increase in statistical power for the cost of 6 single paths.

**Protocol.** Re-run only the failing (member, system) path for each, with the endpoint fix in E1.
This is a pilot for E1's yield claim before committing to the large batch.

**Decision gate.** If ≥4 of 6 recover, the endpoint fix works → proceed to E1 at the improved
yield. If <4 recover, the failures are physical (that host genuinely has no comparable hop in
that system) → treat those hosts as structurally excluded, not a protocol problem.

---

## E1 — Corpus expansion to 20 meV resolution (the primary experiment)

**Objective.** Take the additive question from "no 10× effect" (excluded) to "no 20 meV effect"
(the scale that could still matter for device lifetime), or detect one.

**Target n.** GA: 47 paired triples; Sr: 72. (From the observed SDs 47.4 / 59.6 meV and a 20 meV
two-sided test at 80% power, computed by Monte-Carlo.)

**The design lever — fix the yield, not just add hosts.** The bottleneck is not force convergence.
Of the failed system-slots, **40 are `gate_reject`: after endpoint relaxation the two endpoints
describe *different* configurations** (an atom other than the migrating iodide moved >1 Å), so the
path is not a clean single-vacancy hop. Only 5 slots are force-capped. Adding raw hosts inherits
the same 25% triple-yield, so:

- at 25% yield: GA needs ~152 new hosts (456 paths, **8.9 GPU-h**); Sr ~252 (**14.7 GPU-h**)
- at 50% yield (endpoint protocol fixed): GA ~76 hosts (**4.4 GPU-h**); Sr ~126 (**7.3 GPU-h**)

**Endpoint protocol fix (what lifts the yield).** The `gate_reject` failures are endpoints
relaxing into a different local minimum. Two mitigations, testable in E0:
1. **Constrain the non-migrating sublattice** during endpoint relaxation (fix Pb/Cs/FA, relax
   only the local iodide cage), so the endpoint stays the intended vacancy configuration.
2. **Tighter endpoint fmax** (0.01 → 0.005 eV/Å) so a shallow competing minimum is not entered.

**Batch structure.** Draw new hosts from the same harmonised 36-member ensemble's generation
protocol (documented in `HOST_MANIFEST`), keep the strict pairing (same host across
undoped/GA/Sr), and hold the additive concentration fixed at the current level. Run in waves of
~30 hosts; re-run the admission gate after each wave and stop when GA and Sr each reach target n.

**Analysis (pre-specified, to avoid the multiplicity trap E2 addresses).** Paired t on ΔE_a vs
undoped, per additive, single test each, α=0.05. Report the CI against the 20 meV band. This is
the confirmatory arm — no predictor screening on this data.

---

## E2 — Pre-register the d_max hypothesis (free, rides on E1)

**Why separate from E1.** d_max reached raw p=0.05 in the screen but does **not** survive Holm
correction over the 6 tests, and the screen that generated it cannot also confirm it — that is
circular. It must be tested out-of-sample on data it did not help select.

**Pre-registration (fix before E1 runs).**
- Hypothesis: E_a increases with the migrating-iodide hop distance d_max (one-sided, slope > 0).
- Single test: Pearson r on the E1 *new* members only, α=0.05.
- Power: r≈0.28 needs n≈97 for 80% power single-test; E1 at n≈72 (Sr) plus the existing 49
  admissible reaches ~120, enough to settle it.
- No other predictor is tested on this arm. If a broader screen is wanted, it is a separate
  pre-registration at α/k.

**If confirmed:** the design lever moves from chemistry to geometry — the useful additive is one
that *widens the iodide channel*, not one that binds iodide. That reframes the whole screen.

---

## E3 — Concentration series (generality; ~2–4 GPU-h)

**Why.** The 12.3× host dominance is measured at **one** doping level. "No effect at this
concentration" is not "no effect." A dopant term that scales with concentration would still be
missed by a single-point design.

**Protocol.** Take the ~20 best-behaved triple hosts (the E0/E1 recovered set), run each at 2×
and 3× the current additive concentration (GA and Sr), paired against the same undoped host.
Decompose variance at each concentration.

**Readout.** If dopant SD stays near 4.6 meV as concentration triples, the additive route is
closed *on evidence across the concentration axis*, not by inference from one point. If it grows,
there is a concentration threshold worth mapping — the first positive result the screen could
produce.

---

## E4 — DFT re-anchor at the distribution extremes (transferability; ~1 day DFT)

**Why this is the highest-leverage single check.** Every number above is MACE-MP-0 level and not
transferable. If the 152 meV host spread is an MLIP artifact, the entire "host dominates"
conclusion is about the potential, not the material. Two DFT single-points bound this.

**Protocol.** Take the two extreme admissible hosts — the **48 meV minimum** and the **293 meV
maximum** — and recompute each barrier at the **production DFT level**: PBE+D3(BJ), degauss
**0.005 Ry** (the converged value; 0.01 shifts q0 by −15.8 meV and is *not* converged), Γ-only,
ecutwfc 50 / ecutrho 400 Ry.

**Caveat carried from the convergence gate.** ecutwfc 60 and k 2×2×2 both OOM'd at 132–159 GB on
the current cell. The re-anchor runs at the converged base (50/400, Γ, degauss 0.005); it does
not attempt the parameters that could not run, and the report must state that the plane-wave
cutoff and k-mesh convergence for *this* cell size remain untested against a memory ceiling.

**Readout.** Two numbers: DFT E_a at the MLIP min-host and max-host. If the DFT spread tracks the
MLIP spread (both ~150–250 meV wide), the host-dominance finding is physical. If DFT compresses
the spread, the MLIP is over-dispersing and the finding is a potential artifact — which would
change how E1–E3 should be read. **This is the one result that reframes everything else, and it
is the cheapest test of it: 2 calculations, not 49.**

---

## Recommended order and total cost

| step | question | cost | gates the next? |
|---|---|---|---|
| **E0** | is the endpoint fix real? | ~7 GPU-min | yes — sets E1 yield |
| **E1** | sub-20 meV additive effect? | 4–15 GPU-h | primary result |
| **E2** | does d_max predict E_a? | free (on E1) | reframes the lever |
| **E3** | does the null hold off one concentration? | 2–4 GPU-h | generality |
| **E4** | is the host spread physical? | ~1 day DFT | reframes E1–E3 |

**Do E0 and E4 first, in parallel.** E0 (7 GPU-min) de-risks E1's cost; E4 (1 day DFT, different
machine) tests whether E1 is even measuring the right thing. If E4 shows the MLIP over-disperses,
E1's target n should be recomputed against the DFT SD before committing the GPU-hours.

## What none of these do

None extract or depend on the gated Q2 charge-state barriers. All are MLIP-level except E4, whose
two DFT points are the neutral undoped host and carry no charge-state comparison. The Tyagi
ordering ban is untouched.

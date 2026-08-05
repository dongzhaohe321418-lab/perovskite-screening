# A1a — endpoint-protocol pilot result

**Job `1a86777c` on RTX 5090, MACE-MP-0 medium, 6 hosts × 2 protocols, 1124 s. Exit 0.**

**A1 gate: INSUFFICIENT (0/6 recovered).** Per the pinned design, this is *not* a
physical-exclusion claim — it means the constrained-cage-then-free-release protocol does not, by
itself, raise usable yield on this convenience set. But the per-path diagnosis is clean and
splits exactly along the two pre-registered groups, and the pilot delivered an unexpected
**early bridge signal** that de-risks E1 pooling.

## Head-to-head (old free relaxation vs new constrained-then-free)

| host | group | old Ea | new Ea | old adm | new adm | ΔEa new−old | diagnosis |
|---|---|---|---|---|---|---|---|
| m03-undoped | endpoint | +112.0 | +114.9 | ✗ | ✗ | +2.9 | basin OK; fails **endpoint-energy** gate (initial 21 meV above adjacent image) |
| m04-GA | endpoint | +16.3 | +24.6 | ✗ | ✗ | +8.3 | basin OK; fails endpoint-energy gate (initial 119 meV above adjacent image) |
| m10-Sr | endpoint | +88.7 | +92.4 | ✓ | ✓ | +3.6 | **both admissible** — original failure was transient (seed/convergence), not protocol |
| m18-Sr | endpoint | +186.9 | +184.2 | ✓ | ✓ | −2.6 | **both admissible** — transient |
| m14-GA | mechanism | +482.6 | +479.9 | ✗ | ✗ | −2.7 | **mechanism**: 3 atoms >1 Å, 2nd disp 1.12 Å — not a pure hop |
| m27-GA | mechanism | +236.9 | +239.2 | ✗ | ✗ | +2.3 | **mechanism**: 2nd disp 0.92 Å > 0.8 threshold — not a pure hop |

## What this means, group by group

- **Mechanism group (m14, m27): correctly not recovered.** Both fail basin consistency under
  *both* protocols because the true path is multi-atom, exactly as the design anticipated. These
  are structurally not pure hops; forcing "recovery" would be wrong. Recorded as mechanism, not
  protocol, failures.
- **Endpoint group, energy-gate subset (m03, m04): the constraint cannot fix them.** Their
  endpoints are the intended configuration (basin OK) but the initial image sits above its
  neighbour on the energy profile — a band/endpoint-energy problem the cage constraint does not
  touch. A different fix (more images, endpoint-energy-aware admission) would be needed, not this
  one.
- **Endpoint group, transient subset (m10, m18): already admissible on re-run.** Both pass under
  both protocols here, so their original single-slot failure was seed/convergence noise, not a
  systematic gap. These recover for free on any re-run.

## The early bridge signal (matters for E1 pooling)

The new protocol **barely moves the barrier** (|ΔEa| mean 3.7 meV, max 8.3 meV) and **does not
introduce a basin shift**: after the cage relaxation is released and the structure re-relaxes
freely, it converges to the *same* endpoint as plain free relaxation. This is the first evidence
that a constrained-construction protocol would **not** create a second, incompatible barrier
population — the exact risk A1b exists to rule out. A1b will confirm this on a proper
representative sample; the pilot already points the right way.

## Consequence for the plan

1. The constrained-cage protocol as specified is **not** the yield lever — dropped as the E1
   endpoint fix. E1's yield improvement, if any, must come from elsewhere (endpoint-energy-aware
   admission, or accepting the measured 25% triple-yield and pricing E1 accordingly).
2. Because the new protocol reproduces the free-relaxation endpoint, **the free-relaxation
   protocol the old 108-corpus already uses is retained** — which means the A1b bridge question
   simplifies: there may be no protocol change to bridge. A1b now tests whether *re-running* the
   free protocol reproduces the corpus barriers within tolerance (a reproducibility check), not
   whether two different protocols agree.
3. None of the 6 enters main-effect statistics (feasibility sample only).

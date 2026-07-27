# Rejected-path basin identification (P2 follow-up)

**All 35 rejected paths from the rerun classified by what actually moves between the
initial endpoint and the band's lowest configuration. Two physical classes emerge, and
neither is an unphysical collapse. Each needs a different fix, and neither is "more
relaxation budget".**

Method: for every rejected path, the displacement field between the initial endpoint and
the band's minimum-energy image (minimum-image convention), split by atom type; co-movers
counted above 0.8 Å. Endpoints are images 0 and 6 in a 7-image band — an earlier pass of
this analysis misclassified minima at image 6 as "interior", which is corrected here
(2 of the 35 were mislabelled; the class counts below are the corrected ones).

## Class A — FA reorientation accompanies the hop: 20 of 35

| | |
|---|---|
| interior minimum below initial endpoint | mean −280 meV, range [−563, −22] |
| FA co-movers >0.8 Å | 50 atoms across 20 paths, mean displacement 0.97 Å |
| by system | undoped 5, GA 8, Sr 7 |

The band discovers that rotating one or more FA molecules *during* the iodide hop reaches
configurations far below the initial endpoint. These are genuine states — the validity gate
is doing exactly its job by refusing to report their barrier as the pure iodide hop.

**This is the composite-mechanism branch. The fix is mechanistic, not numerical:**
treat "I hop at frozen FA orientation" and "I hop + FA reorientation" as *different
mechanisms* with separate barriers. Practically: re-relax each rejected path's endpoints
with the band's discovered FA orientation, and run that band as its own mechanism class.
A single Ea mixing both is meaningless.

## Class B — no co-mover above 0.8 Å: 9 of 35

Seven of nine are **strongly asymmetric wells**: the final endpoint sits 100–520 meV below
the initial one, with the profile descending after the saddle (`dip_after_barrier`). Two are
**shallow initial minima**: an adjacent configuration reachable by small *collective*
displacements (every atom under 0.8 Å) lies 84–100 meV below the converged endpoint
(`dip_before_barrier`).

Neither is a failure of the calculation. Both mean the endpoint chosen by
"nearest iodide to the vacancy, relaxed to fmax ≤ 0.02" is a *shallow* local minimum whose
basin bottom lies elsewhere — reachable not by one atom moving but by many small motions,
which is why force convergence does not catch it (forces at a shallow minimum are small
by definition).

**Fix: basin-bottom identification before the band** — a short MD quench or a perturbed
re-relaxation of each endpoint, accepting the endpoint only if it returns to itself.

## What this changes

1. The ~35% validity yield decomposes into: 19 valid + 20 composite-mechanism +
   9 shallow-endpoint + 6 other. The "yield" is not noise to push through with more
   sampling — half the rejections are a second mechanism worth studying in its own right.
2. **The screening statistic stays defined on the pure-hop class only.** Composite paths
   must not be averaged in, at any n.
3. GA shows the most class-A rejections (8), consistent with a larger A-site cation
   coupling more strongly to FA orientation — worth tracking, but at these counts not yet
   a claim.

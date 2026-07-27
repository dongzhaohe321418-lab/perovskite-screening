# Rejected-path basin identification — CORRECTED (v2)

> **This version supersedes v1 entirely.** A reviewer audit found that v1's
> "correction" fixed only the labels while carrying the uncorrected statistics: 25 of the
> 29 profile minima sat at image 6 — the **final endpoint** of a 7-image band — not 2 as
> v1 claimed, so v1's "interior minimum, mean −280 meV" was in fact mostly the final
> endpoint, its Class A "during the hop" interpretation rested on that mislabelling, and
> its Class B "shallow initial minimum reachable by many small motions" reading was
> contradicted by the recorded migrating-ion displacements (3.5–4 Å — one atom completing
> the hop, not many small motions). The analysis below was redone from scratch with the
> two questions kept separate.

Method: for each of the 35 rejected paths, two independent questions, each with its own
displacement field —

- **Q1 (asymmetric well):** does the *final endpoint* sit >50 meV below the initial one?
  Displacements measured initial→final.
- **Q2 (interior basin):** does the *lowest interior image* sit below **both** endpoints?
  Displacements measured initial→that image.

## Result: the dominant phenomenon is strongly asymmetric wells, not mid-path basins

| class | n / 35 | definition |
|---|---|---|
| **asymmetric well** | **27** | final endpoint below initial by >50 meV (mean -273, range [-563, -71] meV) |
| genuine interior basin | 3 | an interior image below *both* endpoints |
| both | 1 | (counted in each row above) |
| neither (other gate failures) | 6 | endpoint-consistency or magnitude rejections |

By system, asymmetric wells: undoped 9, GA 8, Sr 10 — evenly spread, a host property.

## What the asymmetric wells are

**18 of 27 have FA atoms displaced >0.8 Å in the final state.** The picture: the two
iodide sites connected by the hop are strongly inequivalent in a disordered FA host, and in
most cases the *arrival* site is additionally stabilised by an FA reorientation that the
final-endpoint relaxation finds. The initial endpoint is *not* shown to be shallow —
that was v1's unsupported claim. What the data show is a hop landing in a much deeper well.

These paths fail the endpoint gate because the descending profile puts an adjacent interior
image below the initial endpoint. The physics is a **strongly exothermic hop**, and the
forward barrier from the initial state is still a well-defined quantity — but for
18 of the 27, the *final* state mixes iodide transfer with FA reorientation, so the
reverse barrier and the well depth are composite-mechanism quantities.

**Fix:** for the pure-hop statistic, these need endpoints prepared in a *common* FA
orientation — re-relax the final endpoint with FA orientations constrained to the initial
member's, or accept the forward barrier only, with the asymmetry recorded. Averaging their
apparent barriers into the screening statistic without that separation mixes mechanisms.

## The genuine interior basins (3 of 35)

| path | interior min | image | co-movers (FA/framework) |
|---|---|---|---|
| m01 Sr | −121.3 meV | 5 | 1 / 0 |
| m04 GA | −22.4 meV | 5 | 1 / 0 |
| m09 undoped | −100.0 meV | 1 | 0 / 0 |

Two involve a single FA rotating mid-path (a true composite mechanism, the only cases the
v1 "Class A" story actually describes); m09's basin at image 1 with no co-mover >0.8 Å is
the one place a small-collective-displacement reading might apply — a single path, not a
class.

## Consequences (revised)

1. The rejection pool is dominated by **site-energy asymmetry** (27/35), not by mid-path
   FA-rotation mechanisms (3/35). v1 had this backwards.
2. The screening statistic can potentially recover many of the 27 asymmetric-well paths by
   reporting **forward barriers with endpoint-asymmetry recorded**, rather than discarding
   them — a protocol question for the user, since it changes what "E_a" means in the table.
3. The basin-bottom re-identification fix proposed in v1 addresses at most 1 path (m09) and
   is dropped as a priority.

# Evaluation of the proposed next step

**Verdict: adopted. Both statistical corrections are right and I have applied them. One
cost figure in the proposal inherits an error of mine and is now recomputed from measured
data. One addition to the DFT+U protocol is required, from a geometry check run for this
evaluation.**

---

## 1. Student-t intervals — CORRECT, and my figures were wrong

Verified independently; the proposal's numbers match mine to the decimal.

| system | n | mean ΔE_a | my CI (1.96·SE) | correct CI (t, df=n−1) | understated |
|---|---:|---:|---|---|---:|
| GA | 2 | +25.8 meV | [−91.8, +143.5] | **[−736.7, +788.4]** | 6.5× |
| Sr | 4 | −9.8 meV | [−46.4, +26.9] | **[−69.3, +49.8]** | 1.6× |

At df = 1 the critical value is 12.706, not 1.96. Using the normal approximation at n = 2
understated the GA interval by more than sixfold. The qualitative conclusion (neither dopant
resolvable) is unchanged and in fact strengthened, but the intervals as published were
indefensible. **Corrected in `PAIRED_PILOT.md`.**

The related point is equally right and I had not made it: **an sd estimated from n = 2
cannot set a sample size.** The 95% upper confidence bound on σ from a χ² distribution:

    GA: point sd 84.9 meV -> n>=9    but sigma could be up to 1353 meV -> n>=2070
    Sr: point sd 37.4 meV -> n>=2    but sigma could be up to  109 meV -> n>=14

The GA figure spans two orders of magnitude. Treating 84.9 meV as a planning number was
wrong; it is an early-warning signal, exactly as the proposal says.

## 2. Paired pass rate ≠ single-path pass rate — CORRECT in principle; measured here

The reasoning is right and I had conflated the two. But the proposal *assumes* independence
(0.33² ≈ 11%); I have the data to measure it:

| | single-path | observed paired | independence predicts |
|---|---|---|---|
| undoped | 6/18 = 0.333 | — | — |
| GA | 6/18 = 0.333 | **2/18 = 0.111** | 0.111 (ratio 1.00) |
| Sr | 6/18 = 0.333 | **4/18 = 0.222** | 0.111 (ratio 2.00) |

GA matches independence exactly. **Sr is twice the independent prediction** — its failures
cluster on the same members as the undoped leg's, so pairing salvages more than chance
would. Fisher's exact test on the 2×2 gives p = 0.107, so at n = 18 this is suggestive, not
established. The planning default should remain independence, with the possibility of
correlated failures noted as upside.

Host counts, from the *observed* paired rates with Jeffreys intervals on the rate itself:

| dopant | paired rate | hosts for 10 pairs | range across the rate CI |
|---|---|---:|---|
| GA | 0.111 [0.024-0.311] | **90** | 33-420 |
| Sr | 0.222 [0.080-0.446] | **45** | 23-125 |

The proposal's 90 and 45 are confirmed. My "~30 hosts" was wrong.

## 3. Where the proposal's cost figures need revising — downward

The proposal scales GPU hours from my "~8 GPU-h", but that figure was itself an
overestimate. Measured wall time in the pilot: **137 s per path** (mean and median over 54
paths, so no tail skew).

| dopant | hosts | legs | GPU-hours | proposal said |
|---|---:|---:|---:|---:|
| GA | 90 | 180 | **6.8 h** | ~24 h |
| Sr | 45 | 90 | **3.4 h** | ~12 h |

The proposal's factor-of-three inflation comes from propagating my bad estimate rather than
from its own reasoning — the host counts it derived are right.

One further saving it does not use: **the undoped leg is shared.** Screening k dopants on
one host set costs (k+1) legs per host, not 2k. The marginal cost of dopant number two onward
is half the first. This matters for the full screen, not for the pilot.

## 4. Required addition to the DFT+U protocol

The proposal's escalation order — projection first, then uniform DFT+U with a
non-arbitrary U, cDFT demoted to fallback, HSE06 excluded on cost — is right, and matches
what the cost ladder already established.

A geometry check run for this evaluation adds a constraint:

    Pb139-Pb70 separation across the vacancy: 6.71 A

The two Pb flanking the vacancy sit on **opposite sides, 6.7 Å apart**, with negligible
direct 6p overlap. So there are two nearly-degenerate, spatially separated, essentially
**decoupled** sites.

**A uniform U on all Pb penalises both identically.** It can localise the electron — which
is what U is for — without breaking the degeneracy between "on Pb139" and "on Pb70", leaving
the SCF free to keep trading between them: the original failure mode.

**Requirement: run U together with one of the spatial seeds already validated, not U
alone.** The seeds cost nothing (a species relabel with the identical pseudopotential) and
are already verified to leave the Hamiltonian unchanged. Without this, a U run that fails to
converge would be misread as "U does not work" when the actual cause is an unbroken
symmetry U cannot break by itself.

*Correction to my own reasoning:* I first framed this as a Pb-Pb dimer whose two-centre
character U would damage. The 6.71 Å separation rules that out — there is no bond to
protect. Separately, the 0.5000 occupation cited in `Q0_DIAGNOSTIC_RESULT.md` is an artefact
of the spin-free probe (an odd electron count forces half occupancy there) and is not
evidence about spatial localisation in either direction. The projection step remains the
only thing that settles it.

## 5. Points adopted without qualification

- **Salvage the existing 18 members before generating more.** Record the achieved endpoint
  `fmax`, re-relax the ones that fell short, and separate numerical non-convergence from
  MLIP failure from genuine path failure. This is already the open item from the last
  reviewer finding, and it is the right order: raising yield from 33% cuts the host
  requirement proportionally, so it is strictly cheaper than generating hosts.
- **Report single-path and paired pass rates separately.**
- **Reach 8-10 valid pairs for both dopants before interpreting the GA scatter.** If the
  scatter survives strict endpoint criteria it is worth treating as physics; if it collapses,
  it was path quality.
- **HPC restricted to the projection and a small DFT+U benchmark.** No production CI-NEB
  until q=0 converges formally with reliable forces.

## Execution order

1. Fix the statistics in `PAIRED_PILOT.md` — done.
2. HPC: `projwfc.x` on the converged q0C/q0D densities → Pb-6p vs I-5p weights, IPR, and
   **whether the state sits on one Pb or is split across both**.
3. GPU: re-run the 18 existing members with endpoint `fmax` recorded and a larger relaxation
   budget. Re-pair. Measure the new yield before committing to more hosts.
4. HPC: DFT+U benchmark **with a spatial seed**, U from linear response, on a few static
   q=0 and q=+1 points.
5. Only then: endpoint optimisation and CI-NEB for both charge states.

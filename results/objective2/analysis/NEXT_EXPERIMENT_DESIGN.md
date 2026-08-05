# Next-experiment design v2 — pinned stage target and path

**This is the frozen authority for the current stage.** It supersedes the v1 design after two
rounds of independent review that recomputed every cited number from the raw records. Costs are
priced from the **measured 70 s/path** (MLIP) and the **measured 25% triple-yield** (9 of 36
attempted hosts became usable three-system triples). Reads no Q2 production barrier; MLIP-level
throughout except E4's neutral-host DFT points.

## The finding these designs respond to — stated as a point estimate, not a constant

On the balanced 9-host subset admissible in all three systems, host configuration is the dominant
term in the migration barrier:

> **Within the domain** {MACE-MP-0, FA₀.₉₅Cs₀.₀₅PbI₃, ~5% single-substitution GA/Sr, bulk
> pure-hop, the 9 hosts admissible in all three systems}, the estimated host-configuration SD is
> **57.3 meV** and the dopant-identity SD is **4.6 meV**, a **point-estimate ratio of 12.3**.

This ratio is **not a material constant**. It rests on 9 complete triples; the denominator (4.6
meV) is near zero, so the ratio is unstable. Resampling over hosts gives a 95% interval of
**[1.7, 26.7]** with median **5.2**. "Host is the stronger term" is well supported; "exactly 12×"
is not. All numbers are MLIP-level, not DFT or experiment.

The open questions are **resolution** (is there a sub-20 meV additive effect?), **generality**
(does the null hold off one concentration?), and **transferability** (is the host spread physical
or an MLIP artifact?).

---

## E0 / A1a — Endpoint-protocol pilot on the 6 one-away hosts (RTX 5090, ~10–30 GPU-min)

**Purpose: protocol feasibility only. These 6 do NOT enter the main-effect statistics.** They are
a convenience sample (selected *because* 2 of 3 slots already passed), so using them to update any
GA/Sr mean or SD would bias the variance low. They test whether the new endpoint protocol works,
nothing more.

**The 6 are not one failure mode.** Split into two groups by their actual gate record:

| group | hosts (missing slot) | what E0 asks |
|---|---|---|
| endpoint/protocol | m3-undoped, m4-GA, m10-Sr, m18-Sr | can the new endpoint protocol raise usable yield? |
| mechanism-diagnostic | m14-GA (3 atoms >1 Å), m27-GA (2nd disp 0.841 Å > 0.8 threshold) | is this still a pure hop? — recovery is not required |

m3/m10/m18 fail on endpoint-vs-band energy; m4 also failed to converge; m14 is a multi-atom
rearrangement (possible FA reorientation); m27 passed endpoint energy but is a **mechanism
boundary** case, not an endpoint failure.

**Endpoint protocol (the fix under test).** The old 108-corpus used **free relaxation** (no
constraints), and the dominant failure is endpoints relaxing into a *different* configuration. The
new protocol:
1. Build the initial endpoint with the non-migrating sublattice **temporarily constrained** (fix
   Pb/Cs/FA, relax the local iodide cage) so the starting endpoint is the intended vacancy config.
2. **Release all constraints and re-relax freely** — the reported endpoint is always the free one.
   A constrained-only barrier is a *conditional constrained barrier* and must NOT mix with the
   free-relaxation distribution.
3. Displacement-only return test; classify pure-hop / hop+FA / band-collapse by the existing rules.

Endpoint fmax target is **0.02 eV/Å** (the value the corpus actually uses), NEB fmax 0.05.

**A1 gate (revised — no "physical exclusion" claim):**
- **≥4/6 recover** → the protocol shows feasibility on the convenience failure set; still must be
  validated by A1b and A3 before any E1 use.
- **<4/6 recover** → the protocol is insufficient to raise yield; **stop E1 submission,
  diagnose per-path, and do NOT conclude the failures are physical.** Low recovery could be band
  images, endpoint initial guess, constraint release, optimizer basin, FA reorientation, or a
  pure-hop threshold ill-suited to that structure — none provable as "physical" from this pilot.

The "9→15" figure is a **theoretical maximum** if all 6 recover legitimately, never an expected
result.

---

## A1b — New-vs-old protocol bridge (RTX 5090) — GATES whether E1 can pool the old corpus

**The single most important addition.** E1 will use the new endpoint protocol; the old 108-corpus
used free relaxation. Even with constraints released, the construction step can steer a structure
into a different basin. Adding new E1 data to the old n=11/12 could merge two protocols' barriers
into one statistical population.

**Protocol.** Take a representative set of **already-admissible** paths — undoped/GA/Sr each ≥2,
spanning low/mid/high barrier, including both strict and return-test-recovered — and re-run each
under the **new** protocol. Check, against a pre-registered tolerance:
1. Does the freely-relaxed endpoint return to the original basin?
2. Is the mechanism label preserved?
3. Is the barrier change below the pre-registered tolerance?
4. Is there a systematic shift in admission route?

**Pooling gate (this is the load-bearing decision):**
> **Only if A1b shows the two protocols agree within the pre-registered tolerance may the old
> n=11/12 count toward E1's total n.** Otherwise E1 is a **new-protocol-only confirmatory corpus,
> target n recomputed from 0**, and the 108-path result is retained only as a historical support
> set.

---

## A2a / A2b — DFT fixed-path diagnostic at the host extremes (E-HPC) — two-level submission

**This is a DFT fixed-path diagnostic, not a relaxed DFT barrier.** 14 SCF single-points on a
frozen MLIP path give a relative-energy profile along that path, not a relaxed barrier (that needs
full CI-NEB — see E4b).

**The extremes must match the 152 meV estimand.** v1 wrongly used m28-GA (48 meV) and m30-GA
(293 meV) — both GA paths, and m28 is not even one of the 9 triples. The 152 meV host range is a
**host-mean** range on the 9 triples: m15 (mean 81.6) to m30 (mean 233.4). The correct arm is
**same system, same charge**:
- **m15-undoped: 55.11 meV** (lowest of the two host means' undoped slot)
- **m30-undoped: 220.06 meV**
- same-arm MLIP contrast: **164.96 meV**

**A2a preflight (6 SCF).** Run m15 and m30 at **images 1, 4, 7** first. For each image store: total
energy, DFT forces, SCF convergence, electronic state/occupation, q0 CBM-like-state continuity,
structure + input hash, the relative-energy reference, and whether state-switching occurred. If
SCF, memory, electronic state, or forces look wrong, **stop and adjust** before the rest.

**A2b (remaining 8 SCF).** Only after A2a passes, complete both 7-image profiles (~1 day, not
guaranteed).

**DFT fingerprint — frozen in full, not just the electronic basics.** Beyond PBE+D3(BJ), degauss
0.005 Ry, Γ, 50/400 Ry: **tot_charge=0** (explicitly V_I⁰, a q=0 charge state — *not* "no charge
state"), electron count, nspin, conv_thr, smearing/occupation type, nosym/noinv, the
C/H/N/Cs/Pb/I pseudopotential filenames **and hashes**, cell + atom ordering + PBC, whether all
nuclei are fixed, and the restart/state-ID rule. **50/400 Ry and Γ are an operational setting
under a hardware ceiling** (ecutwfc 60 and k 2×2×2 both OOM'd at 132–159 GB on this cell), NOT a
convergence claim for the 232-atom FA cell.

**A2 gate (revised — no "DFT proves it" claim):**
- **fixed-path DFT keeps the ordering with significant contrast** → the two anchors support that
  the host contrast is not a pure MLIP energy-ordering artifact; worth proceeding to E4b.
- **contrast compresses/inverts, OR DFT forces are large** → cannot distinguish MLIP energy error
  from path mismatch (the MLIP path may be far from the DFT minimum-energy path); **stop
  large-scale E1 interpretation and do path/model calibration first.**

Readout wording is bounded: "the relative-energy profile and extreme ordering of DFT on two frozen
MLIP paths," never "host-dominance is proven physical by DFT."

---

## A3 — Blind-host protocol validation & variance estimate (RTX 5090, ~1.2 GPU-h)

**Freeze the protocol first; no rule changes after seeing results.** ~20 fresh blind-selected
hosts (not colliding with the old 36, same sampler, explicit MD/frame-independence rule), each run
fully across undoped/GA/Sr = 60 paths.

**Why 20, not "a few".** A workflow check alone needs ≥12; pricing E1 from yield needs ~20 to
estimate the triple-yield and the **blinded internal-pilot variance** that E1's sample size should
use — *not* A1's convenience sample.

**A3 pass criteria (pre-registered):** no index/composition errors; all paths complete; endpoint
force / return test / mechanism gate replayable; triple-yield meets a pre-set operational
threshold; **no systematic offset vs the A1b bridge.**

---

## E1 / B — Equivalence corpus to ±20 meV (RTX 5090, 4–15 GPU-h scenario budget)

**This is an equivalence question, not difference-detection.** A non-significant paired t-test
does NOT prove "no 20 meV effect." Pre-register:
- **TOST** with margin **±20 meV** (or require the 90%/95% CI to fall entirely within ±20 meV);
- alpha and power target, and which CI (90% vs the more conservative 95%);
- the nuisance-SD re-estimation algorithm (A3 blinded variance, or the original pre-registered
  value — **never** re-choose n after seeing ΔE_a direction);
- maximum host count; GA and Sr each reach target n separately;
- both strict-only and all-admitted sensitivity retained.

Sample size is computed by **real equivalence-power simulation** after A3, not the difference-power
plug-in that gave v1's n=47/72. A plug-in check (95% CI ⊂ ±20 meV at the current mean/SD) suggests
GA n≈52, Sr n≈58, but the simulation is authoritative.

**Wave stop rule:** stop only on reaching the pre-registered effective n / admission target —
**never** on the mid-run ΔE_a direction.

**What ±20 meV means.** At 300 K and equal prefactor, 20 meV is ≈**2.17× the single-hop rate**. It
is a **finer, potentially kinetically-meaningful pre-set precision scale**, NOT an
experimentally-validated device-lifetime threshold.

---

## E2 — Pre-registered d_max test (free, rides on E1)

d_max reached raw p=0.05 but does **not** survive Holm over the 6 valid tests, and the 49 paths
that generated it are the **discovery set** — they cannot re-enter the confirmatory test.
- **Primary confirmation: E1 new data only.** Old 49 = discovery; report discovery and replication
  separately, optional secondary meta-analysis.
- The three system-paths share a host → **host-level clustering**. Pre-register a mixed model
  `E_a ~ d_max + system + (1|host)`, or use only the undoped path per host, or cluster-bootstrap.
  Power on the number of **independent hosts**, not path rows.
- **Physical reading is bounded.** d_max is the migrating-iodide hop displacement, **not** channel
  width. Even if the positive correlation confirms, it says "longer local hop correlates with
  higher E_a" — it does **not** license "seek additives that widen the iodide channel" (widening a
  bottleneck often *lowers* the steric barrier).

---

## E3 — Concentration series (generality, RTX 5090, ~2–4 GPU-h+)

12.3× host dominance is measured at **one** doping level (GA 1/20 A-sites ≈ 5%, FA₁₈GA₁Cs₁; Sr
1/20 B-sites ≈ 5%, Pb₁₉Sr₁). 2× and 3× give 10% and 15%, where multi-additive **placement** becomes
a new variable (GA–GA distance, second-additive-to-vacancy distance, Sr–Sr adjacency, cooperative
H-bonding, strain-induced local phases).
- Hosts sampled randomly or stratified by low/mid/high barrier — **not** the best-behaved subset
  (that biases to easy-path structures).
- Each host gets ≥2–3 dopant placements, or placement as a random effect.
- Same undoped host as shared control; model concentration × additive + host/placement.
- n≈20 is **exploratory dose-response only** — not grounds to "close the additive route."

---

## E4b — Relaxed DFT CI-NEB at the extremes (E-HPC, multi-day) — only after A2 passes

Two full relaxed q0 CI-NEB legs at m15-undoped and m30-undoped, at the frozen DFT fingerprint.
Prior 159-atom production CI-NEB ran ~2.5 days each; the FA host is 233 atoms with C/N/H and
molecular reorientation, so budget **multi-day, not 1 day**. Even matching anchors only validates
two points, not the full distribution.

---

## Recommended order and gates

| stage | work | resource | into main stats? |
|---|---|---|---|
| Phase 0 | freeze design, TOST, bridge, DFT fingerprint, A3 n | local | no |
| **A1a** | 6 old-failure protocol pilot (2 groups) | RTX 5090, ~10–30 min | no |
| **A1b** | new-vs-old protocol bridge on admissible paths | RTX 5090 | no (gates pooling) |
| **A2a** | m15/m30 × images 1,4,7 = 6-SCF preflight | E-HPC | no |
| **A2b** | complete two 7-image fixed profiles (14 SCF) | E-HPC, ~1 day (not guaranteed) | DFT diagnostic |
| **A3** | ~20 blind hosts, yield + blinded variance | RTX 5090, ~1.2 GPU-h | internal pilot |
| **E1** | pre-registered ±20 meV TOST corpus | RTX 5090, 4–15 GPU-h | **yes** |
| E2 | new-data, host-clustered d_max test | on E1 | independent confirmatory |
| E4b | two relaxed q0 CI-NEB | E-HPC, multi-day | only if A2 passes |

**A1a + A2a run first, in parallel.** A1a de-risks E1's cost; A2a tests whether the MLIP path is
even the right object before spending DFT. **The biggest risk is not compute — it is merging
new-protocol data with the old 108-corpus without the A1b bridge, and over-reading two fixed-path
DFT profiles as a full DFT host distribution.**

## What none of these do

None extract or depend on the gated Q2 charge-state barriers. E4's DFT points are the neutral
undoped host (V_I⁰, a q=0 state carrying no q=0-vs-q=+1 comparison). The Tyagi ordering ban is
untouched.

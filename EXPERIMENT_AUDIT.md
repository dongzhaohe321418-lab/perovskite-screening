# EXPERIMENT AUDIT RECORD

**Compiled 2026-07-28 from committed records, not from memory. Every number below was read
back from a file in this repository; the file is named beside it so it can be checked
independently.**

Repository: `dongzhaohe321418-lab/perovskite-screening` (private, branch `main`)
Compute: `ssh:ehpc` (Aliyun E-HPC, Quantum ESPRESSO, 2 nodes x 32 ranks) and
`ssh:autodl` (RTX 5090, MACE-MP-0 medium, float64)

## How to read this document

Sections 1-3 are results. Section 4 is the retraction log — **every claim I published and
then withdrew, with the reason**. Section 5 lists what is *not* established. Section 6 is the
execution-failure log. Section 7 is the file inventory. An auditor short of time should read
**Section 4 and Section 5 first**: they say what to distrust.

Three labels are used throughout and mean specific things:

- **ESTABLISHED** — converged calculation, checked, reproducible from committed data.
- **BOUNDED** — the sign or an upper limit is secure; the point value is not resolved.
- **PROVISIONAL** — computed but failing at least one acceptance criterion; not citable.

---

# 1. Objective 1 — iodide vacancy migration, charge-state dependence

## 1.1 Theory fingerprints (the two are NOT comparable)

| | Stage-1 benchmark | Stage-2 production |
|---|---|---|
| functional | PBE | **PBE + D3(BJ)** (`dftd3_version = 4`) |
| smearing `degauss` | 0.01 Ry | **0.005 Ry** |
| `ecutwfc` / `ecutrho` | 50 / 400 Ry | 50 / 400 Ry |
| k-points | Γ | Γ (`nosym`, `noinv`) |
| cell | 159-atom (V_I), 160-atom pristine | same |

The D3 correction alone shifts the total energy by **2.722 Ry = 37.03 eV**. Any comparison
across these two fingerprints is invalid. The old fixed-path pair (141 meV for V_I⁰,
127 meV for V_I⁺) belongs to Stage 1 and **must never be quoted alongside Stage-2 numbers**.
Recorded in `THEORY_LEVEL_RECONCILIATION.md`.

## 1.2 q = +1 endpoints — ESTABLISHED

| quantity | value | source |
|---|---|---|
| initial endpoint | **−9247.94069589 Ry** | `q1/q1_initial_relaxed.extxyz` |
| final endpoint | **−9247.93981770 Ry** | `q1/q1_final_relaxed.extxyz` |
| endpoint asymmetry | **+11.9 meV** | computed |
| Pb flanking the vacancy | indices 139, 70 at 3.446 / 3.511 Å | computed |

Both closed-shell (1400 electrons), converged. A known limitation: the γ-CsPbI₃ V_I cell has
soft octahedral-tilt modes, so BFGS floors at fmax ≈ 0.04 eV/Å rather than reaching 0.02.
The accepted geometries are the lowest-fmax ionic steps, documented in
`LOCKED_PROTOCOL_AND_STOPLOSS.md`.

## 1.3 q = +1 explore NEB — PROVISIONAL (unconverged)

3 interior images, no climbing image, `path_thr = 0.1`. Barrier over 6 path iterations:

    1216 → 945 → 544 → 490 → 461 → 431 meV   (still descending, NOT converged)

**431 meV is a lower bound on nothing and an upper bound on nothing** — it is a snapshot of a
descending optimisation. It is recorded so the CI-NEB can restart from the preserved
`neb.path` (`q1_explore_state.tar.gz`), not as a barrier.

## 1.4 The ★ decision: full CI-NEB is required — ESTABLISHED

d_max between the DFT-relaxed q=+1 band and the MACE band, at matched arc-length reaction
coordinate with minimum-image convention:

| reference band | d_max | clears 0.4 Å threshold |
|---|---|---|
| `gamma_neb_band_5int.extxyz` | **0.462 Å** | yes |
| `gamma_neb_band_7int.extxyz` (finer) | **0.472 Å** | yes |

Robust to the reference-band choice, and both are **lower bounds** since the DFT band is not
converged. MACE geometries therefore cannot serve as a fixed-path proxy. Recorded in
`THEORY_LEVEL_RECONCILIATION.md` with explicit band provenance (an earlier version of that
note conflated two different MACE bands — see Section 4.1).

## 1.5 The q = 0 electronic state — ESTABLISHED, with the energy metric BOUNDED

The half-occupied state in the V_I⁰ cell is **CBM-like**. Evidence, all from
`P1_REFERENCE_AUDIT.md`:

| metric | pristine (160-atom, P1) | defective (159-atom, q0A) | verdict |
|---|---|---|---|
| Pb-p orbital weight | 91.4% | 90.8% | match |
| per-atom weight cosine | — | **0.9757** | match (controls: 0.788 vs CBM+1, 0.741 vs CBM+3) |
| effective atom count | 35.6 | 38.3 | match |
| energy, raw eigenvalue | 4.3188 eV | 4.3259 eV | **INVALID — no common zero** |
| energy, VBM-referenced | +1.5560 above VBM | +1.6319 above VBM | **+75.9 meV** |
| energy, semicore-aligned | 4.2738 (shifted −45 meV) | 4.3259 | **+52.1 meV** |
| gap to next conduction state | **311 meV** | 229 meV | nothing split off |

Cell and theory identical: volume 54529.4666 Å³ both, ecut 50/400, degauss 0.0050; the
7-electron difference is exactly the removed iodide's valence.

**The critical point for audit:** the 229 meV gap above the defect state looks like an
isolated donor level, but the *pristine* Γ-point CBM is already isolated by 311 meV. The
229 meV is the intrinsic supercell band-edge spacing, mildly perturbed — **no state has been
pulled out of the conduction band**. There is no in-gap level, which is why DFT+U has no
premise here.

## 1.6 No thermally significant polaron — BOUNDED

Three calculations, `Q0_POLARON_EXCLUDED.md`:

| run | geometry | spin | E (Ry) | status |
|---|---|---|---|---|
| deloc | undistorted (= q=+1 relaxed) | non-magnetic | −9247.62643363 | converged, **0 BFGS steps** |
| ELAS | +0.20 Å Pb cage contraction | non-magnetic | −9247.61815625 | converged, 39 iterations |
| POL | same +0.20 Å | seeded `starting_magnetization = 0.5` | −9247.61832 | **plateau, moment decaying** |

    elastic cost      E(ELAS) − E(deloc)  =  +112.6 meV      [both runs converged]
    total             E(POL)  − E(deloc)  =  +110.4 meV      [POL unconverged]
    localisation gain = elastic − total    =  a few meV — NOT RESOLVED

**What is secure:** POL sits ~110 meV *above* the delocalised state, and that gap is ~4× POL's
own SCF residual (~30 meV), so the **sign** is safe. The seeded state is not the ground state.
Lattice stiffness k = 112.6/0.20² = **2815 meV/Å²** from converged runs.

**What is bounded, not measured:** granting the *entire* residual as localisation gain, and
then twice it:

| assumed gain at 0.20 Å | g (meV/Å) | u_crit (Å) | well depth (meV) |
|---|---|---|---|
| 30 (full residual) | 150 | 0.053 | **2.0** |
| 60 (2×, deliberately extreme) | 299 | 0.106 | **8.0** |

Deepest possible well ~8 meV, under one-third of room-temperature kT (25.7 meV). **A weakly
bound few-meV state is NOT excluded.** Three qualitative signatures agree independently: the
seeded |m| decayed 1.25 → 0.80 → 0.58 rather than consolidating; the energy never descended
over 90 iterations; and from the undistorted geometry BFGS took zero steps with m = 0.00.

## 1.7 P2 — no competing magnetic state — ESTABLISHED

Unconstrained-spin run restarting from the converged q0A density: total moment 0.00 and
absolute moment 0.00 throughout, **converged in 6 iterations** to 1.0×10⁻⁶ Ry, exactly one
partially occupied state (occupation 0.5000 at 4.3259 eV) as expected for an odd electron
count under smearing. Every prior *forced*-moment attempt failed after 47-200 iterations, and
the forced-moment plateau sits **above** this non-magnetic solution.

## 1.8 q = 0 geometry relaxation — one endpoint ESTABLISHED, one IN PROGRESS

**q0_initial: converged in ZERO BFGS steps.**

    Energy error   = 7.0E-05 Ry   (criterion 1.0E-04)   PASS
    Gradient error = 1.7E-03 Ry/Bohr (criterion 1.945E-03) PASS
    bfgs converged in 1 scf cycle and 0 bfgs steps

The q=+1 geometry is already a q=0 stationary point. Independent confirmation: the artifact
store **deduplicated the relaxed structure onto the q=+1 input by checksum** — the geometry is
byte-identical.

**q0_final (`nspin=1`, job `f9993838`): IN PROGRESS.** 7 BFGS steps, 6 converged SCF cycles,
gradient error descending

    3.1E-03 → 2.9E-03 → 2.7E-03 → 2.4E-03 → 1.9E-03 → 1.4E-03 Ry/bohr   (criterion 1.945E-03)

It has crossed the criterion value but QE has **not** printed its convergence block, so this
is **NOT** a verified converged endpoint. Latest energy −9247.62777349 Ry.

## 1.9 q = 0 NEB entry gate — NOT OPEN

| # | condition | status |
|---|---|---|
| 1 | both endpoints ionically converged | initial PASS, **final in progress** |
| 2 | `nspin=1` stable/restartable across nearby geometries | PASS (4 distinct geometries) |
| 3 | no competing localised spin state | PASS (§1.7, §1.6) |
| 4 | q=0 and q=+1 at identical theory fingerprint | PASS by construction |
| 5 | NEB input, restart, archive, state-ID tooling ready | **PARTIAL — archive harness missing** |

**No large HPC allocation may be committed until 1 and 5 close.** `Q0_NEB_GATE.md`.

---

# 2. Objective 2 — additive screening on the FA-disordered host

## 2.1 Method and pre-registered thresholds

MACE-MP-0 medium, float64, RTX 5090. Paired design: each host member gives an undoped path and
a doped path, so the difference ΔE_a cancels the host's own configurational spread.

| threshold | value | meaning |
|---|---|---|
| significance scale | **±59.5 meV** | a 10× change in hop rate at room temperature |
| band convergence | fmax 0.05 eV/Å, 400 steps | NEB band |
| endpoint convergence | **fmax 0.02 eV/Å**, 800 steps | both endpoints, per path |
| max admissible barrier | 3 eV | above this the path is a structural failure |

**Barrier definition (locked).** Primary metric is the **forward** barrier from an initial
state verified as a local minimum. Endpoint asymmetry and a mechanism label are recorded
alongside. Forward and reverse barriers need not match in a disordered host, and a much lower
final state is a property of the material, not an error to symmetrise away.
`BARRIER_DEFINITION.md`.

**Mechanism classes are never pooled:** `pure_hop_asymmetric`, `hop_plus_FA_reorientation`,
`band_collapsed`, `endpoint_energy_unconverged`, `multi_basin_ambiguous`.

## 2.2 The 84-path corpus — integrity audit ran BEFORE any statistics

Job `13fabdfd`. 28 hosts × 3 systems = 84 paths. `paired_raw_84.json`.

| check | result |
|---|---|
| rows / unique member-system combos | **84 / 84**, no duplicates |
| all required fields present | yes |
| magnitude blow-ups (\|E\| > 3 eV) | **0** |
| bands not converged | **0** |
| endpoints at target (fmax ≤ 0.02, < 800 steps) | **79 of 84** |

The 5 failures — `m04-GA`, `m23-Sr`, `m23-undoped`, `m24-GA`, `m24-Sr` — are **excluded**, not
silently used.

## 2.3 Admission accounting

    strict-gate valid                                    30 / 84
    remaining rejections                                 49
      of which asymmetric wells                          30
      of which asymmetric wells WITH an interior saddle   27  -> return-tested
    return test verdict: verified metastable             21 / 27
      of which pure_hop_asymmetric (ADMITTED)             10
      of which hop_plus_FA_reorientation (separate)       11
    ------------------------------------------------------------
    pure-hop admissible total                            40 / 84 = 0.476

Return test protocol: perturb along the path direction, both signs, two amplitudes
(±0.02, ±0.05 Å), re-relax, require return to the initial basin. 108 perturbation relaxations,
all converged; median max displacement 0.034 Å. `return_test_84.json`.

## 2.4 Result — GA is EQUIVALENT to no effect; Sr is not yet decided

| | GA | Sr |
|---|---|---|
| paired n | **9** | **10** |
| members | [5, 6, 8, 10, 12, 15, 18, 20, 21] | [4, 5, 6, 8, 12, 14, 15, 20, 21, 27] |
| individual ΔE_a (meV) | [-11.4, -17.0, 4.5, 66.5, -38.0, 71.7, -30.1, 33.7, -14.3] | [-7.4, -30.2, 19.2, -14.7, 13.8, -139.8, 7.9, 129.3, -7.8, 11.8] |
| mean ΔE_a | **+7.3 meV** | **-1.8 meV** |
| paired sd | 40.6 meV | 65.2 meV |
| 95% CI (Student-t) | **[-23.9, +38.5]** | **[-48.4, +44.8]** |
| entire CI inside ±59.5 meV | **yes** | **yes** |
| TOST equivalence p | **0.0024** | 0.0104 |
| σ 95% upper bound (χ²) | 77.8 meV | 119.0 meV |
| n required by that bound | **7 → MET at 9** | 16 → **short by 6** |
| **status** | **EQUIVALENT** | **SUGGESTIVE-EQUIVALENT** |

Host forward barriers over the same admissible set: n = 13, mean **162.8 meV**,
sd **69.6 meV**. Pairing reduces the spread 69.6 → 40.6 (GA) and → 65.2 (Sr),
confirming the paired design works.

**Permitted claim (verbatim, and no stronger):** *under the current FA-host ensemble, the
pure-hop definition, and the MACE potential-energy surface, GA's barrier change is practically
equivalent to zero within ±59.5 meV.*

**Prohibited:** "GA has no effect on all FAPbI₃ migration"; any GA-vs-Sr ranking; presenting
MACE numbers as DFT or experimental barriers; treating Sr's equivalence as settled; pooling
`hop_plus_FA_reorientation` into the statistic.

## 2.5 Sr's variance is driven by two RESCUED configurations

`m14` gives −139.8 meV and `m20` gives +129.3 meV. **Both failed the strict endpoint gate**
(`Sr_m14` and `undoped_m20` have `gate_endpoints.passed = False`) and entered only via the
return-test rescue. They do have: converged bands, endpoints at fmax ≤ 0.02, interior saddles
at image 3, verified-metastable initial endpoints.

Admission route per pair, and the sensitivity it implies:

| | strict-only pairs | pairs with ≥1 rescued member | all pairs | strict-only |
|---|---|---|---|---|
| GA | 5 | 4 | n=9, mean +7.3, sd 40.6 | n=5, mean −17.9, **sd 16.7**, CI [−38.5, +2.8] |
| Sr | 6 | 4 | n=10, mean −1.8, sd 65.2 | n=6, mean −1.3, **sd 19.4**, CI [−21.6, +19.0] |

Both means stay well inside ±59.5 meV under either treatment and the strict-only subsets are
much tighter, so **the rescued paths inflate the spread and the all-pairs figures are the
conservative ones**. The outliers are **kept** — removing them would be selection on outcome.

## 2.6 A property of the sample-size criterion — declared, not exploited

The χ² requirement **falls as n rises even at constant variance**, because the upper bound on
σ tightens with degrees of freedom. Holding sd at exactly the observed 65.2 meV:

    n=10 → σ_hi 119.0 → n_req 16   (short)
    n=12 → σ_hi 110.7 → n_req 14   (short)
    n=13 → σ_hi 107.6 → n_req 13   (MET — self-clearing)
    n=20 → σ_hi  95.2 → n_req 10   (MET)

**Consequence for the audit:** Sr's criterion will likely read "met" at n = 13 with no new
evidence that its effect is small. The final Sr judgement must therefore rest on whether its
**95% CI lies entirely inside ±59.5 meV**, not on `n_req` clearing. GA is unaffected: it passes
on three independent grounds (n = 9 vs 7, CI well inside the band, TOST p = 0.0024).

## 2.7 Host pool ledger — 36 members

`HOST_MANIFEST.md` / `.json` is the single authority. Three counts appear in earlier prose and
mean different things:

    36 = total members in pool_v3_harmonised (m00-m35)
    28 = members that entered the 84-path corpus (m00-m27); 28 x 3 = 84
     8 = new expansion members (m28-m35), NOT yet in any corpus
    18 = members whose energy was readable from the file's attached calculator
         -- a FILE FORMAT fact, not a pool subset. Quoting it as "existing 18" caused
            the ambiguity this manifest exists to remove.

Integrity: **36 unique IDs**, no gaps, **zero duplicate structure hashes**, **uniform
fmax 0.02** across the whole pool, energy coverage **36/36** (18 from file calculators, 16 from
committed expansion records, 2 recomputed as MACE single points — m26/m27 verified at fmax
0.0193 and 0.0168).

**Homogeneity gate on the complete pool** (the earlier reported gate used only 18 of 28):

| | all 28 existing | all 8 new |
|---|---|---|
| mean E (eV) | −1065.9058 ± 0.1769 | −1066.0085 ± 0.1706 |
| offset | — | **−102.6 meV** |
| Welch t / p | — | **t = 1.49, p = 0.1632** |
| separation | — | **0.59σ** |

Verdict unchanged (poolable), but **weaker than first reported** (−36.6 meV, p = 0.6018, 0.24σ
on the partial set). Far from the 643 meV / 2.24σ / p < 1e-4 failure this gate exists to catch,
but 0.59σ is the number to cite.

## 2.8 Rejected-path basin identification

Of the rejections, the pool is dominated by **site-energy asymmetry in the disordered host**
(the final endpoint sits far below the initial), with only a handful of genuine mid-path
basins. `BASIN_IDENTIFICATION.md` (v2 — the v1 analysis was wrong; see Section 4.3).

---

# 3. Current execution state (as of compilation)

| track | state | evidence |
|---|---|---|
| HPC `q0_final` (`f9993838`) | **running**, 7 BFGS steps, gradient error 1.4E-03 vs criterion 1.945E-03, not yet converged per QE | job output read directly |
| GPU 24-path extension (`41ac4172`) | **COMPLETE**, exit 0, 24/24 bands, integrity-audited | §3.1 below |
| GPU return test on extension (`c535502d`) | **running**, 14 candidates | preflighted before submission |
| everything else | idle | `squeue` empty apart from the above |

## 3.1 Integrity audit of the 24 new rows — run before any statistics

| check | result |
|---|---|
| rows | **24** (expected 24) |
| unique member-system combos | **24 / 24**, no duplicates |
| members | 28-35 as intended |
| all required fields present | yes |
| max endpoint fmax (initial / final) | **0.0200 / 0.0200** (target 0.02) |
| endpoints NOT at target → excluded | **0** |
| magnitude blow-ups (\|E\| > 3 eV) | **0** |
| bands not converged | **0** |
| **overlap with the 84-path corpus** | **0** (must be 0 — verified) |
| strict-gate valid | **4 / 24** |

Of the 20 rejections, **14 are asymmetric wells with an interior saddle** (5 GA, 5 Sr,
4 undoped) and are being return-tested under the identical protocol used for the 84-path
corpus. If all pass, up to 5 new pairs per dopant become available (members 29-33), which
would take GA toward n ≈ 14 and Sr toward n ≈ 15.

**No statistics from the extension appear anywhere in this document.** Updated n / mean / CI /
TOST / variance-bound figures will be reported only after the return test completes and the
merged corpus is re-audited. The strict-valid rate of 4/24 versus 30/84 in the first corpus is
itself a difference worth explaining before the two are pooled — pooling is not automatic.

---

# 4. RETRACTION LOG — claims published then withdrawn

**This is the section to read first.** Each entry is a claim that appeared in a committed
report or a status message and was later found wrong. All corrections are pushed; each has a
regression test where a test is meaningful.

## 4.1 MACE reference band conflated (Objective 1)

**Claimed:** a single MACE barrier of 259 meV as the comparison reference for d_max.
**Actual:** three different bands exist — `regression_saddle_path` (259 meV, the anchor-(a)
reference) and `gamma_neb_band_5int` (253.3 meV, what d_max actually used).
**Impact:** none on the decision — d_max clears 0.4 Å against both (0.462 and 0.472 Å).
**Fix:** `THEORY_LEVEL_RECONCILIATION.md` now lists all bands with explicit provenance.

## 4.2 "Unphysical spin collapse" — my own diagnosis was wrong

**Claimed:** a collapse to zero magnetic moment must be unphysical because V_I⁰ has an odd
electron count (1401 valence electrons).
**Actual:** under smearing, fractional occupation of both spin channels is legitimate. P2
converged to m = 0 in 6 iterations; the forced-moment plateau sits *above* it.
**Impact:** substantial — I spent four attempts and roughly 7 hours of cluster time forcing a
moment the physics was telling me not to force. The convergence failure was self-inflicted
from the moment `tot_magnetization` was imposed.
**Fix:** retracted in `Q0_RESOLVED.md`; DFT+U demoted for lack of premise.

## 4.3 Basin identification v1 — statistics carried across a correction

**Claimed:** a two-class picture of rejected paths, with a specific class-B interpretation.
**Actual:** the "interior" minimum was in most cases the *final endpoint* of the band. The
reclassification then carried pre-correction statistics forward and **understated the
mislabelling by an order of magnitude**, and the class-B reading was contradicted by its own
recorded displacements.
**Fix:** redone from scratch with the two questions separated, each with its own displacement
field. The corrected picture **inverted** the original reading. `BASIN_IDENTIFICATION.md`
carries a superseding banner naming v1's specific errors.

## 4.4 Return-test perturbation scaled by atom count

**Claimed (implicitly, by running it):** a "small" ±0.02/0.05 Å perturbation.
**Actual:** the perturbation was scaled by a factor involving the atom count, making the
displacement a substantial fraction of the path segment — for several paths *larger* than it.
**Impact:** the first run was void. Caught by review before any statistics were read.
**Fix:** scaling corrected so the largest single-atom move equals the stated amplitude;
regression test pins the incident's real numbers.

## 4.5 "Dropping the energy tolerance changed nothing"

**Claimed:** removing the combined test's energy criterion left the outcome unchanged.
**Actual:** it left the set of *escaping relaxations* unchanged — but flipped most relaxation
verdicts and produced the headline classification.
**Fix:** retracted explicitly in both the report and the source header; regression test pins
both the impact figures and the narrow claim that does hold.

## 4.6 Pool population offset attributed to the sampler

**Claimed:** new pool members formed a distinct population (643 meV below, 2.24σ, p < 1e-4).
**Actual:** the two batches had been relaxed to **different force targets**. A direct test
re-relaxing existing members to the tighter target reproduced the offset exactly.
**Fix:** whole pool harmonised; relaxation depth made part of the pool's identity. Also
verified that existing barrier statistics were unaffected — the driver re-relaxes both
endpoints before building each band, and every row records the achieved target.

## 4.7 Two outliers described as passing every gate

**Claimed:** Sr's outliers `m14` and `m20` "pass every gate", used to argue no criterion
existed for removing them.
**Actual:** both **failed the strict endpoint gate** and entered via return-test rescue. A
distinction was available and my argument denied it.
**Fix:** per-pair admission-route table plus sensitivity analysis (§2.5), which *strengthened*
the conclusion. Regression test [16].

## 4.8 A retraction that reached one file but not the index

**Claimed:** §4.7 fixed.
**Actual:** fixed in `CORPUS84_RESULT.md` but **not** in `CURRENT_STATUS.md`, the self-declared
canonical index, written and pushed in the same window. My sweep and my new regression test
were both scoped to one file.
**Fix:** index corrected; regression test broadened from one file to a repo-wide scan of every
`results/**/*.md`.

## 4.9 Polaron constants quoted below their input's uncertainty

**Claimed:** g = 11.0 meV/Å, u_crit = 0.0039 Å, well depth 0.011 meV, and "the conclusion does
not depend on the amplitude chosen".
**Actual:** all derived from a 2.2 meV localisation gain whose own SCF residual was ~30 meV,
and which read 7.3 meV from one sampling window and 2.3 meV from another — a 5 meV swing, more
than twice the value.
**Fix:** constants retracted; replaced with bounds (§1.6). Claim weakened to "no *thermally
significant* polaron". Regression test [17].

## 4.10 The retracted claim survived in the abstract, in paraphrase

**Claimed:** §4.9 fixed.
**Actual:** the body carried the retraction while the **abstract** still said the conclusion
"does not depend on the amplitude chosen" — the same claim in different words. My verification
grepped literal strings only.
**Fix:** abstract rewritten; sweep changed from literal-string matching to a regex over all 30
result documents checking each hit for retraction context (9 candidates, 7 unrelated
legitimate uses, 2 real, both fixed). Regression test [18].

## 4.11 P1 energy agreement invalid — raw eigenvalues across cells

**Claimed:** the defect state matches the pristine CBM to **7 meV** (4.3259 vs 4.3188 eV), and
the title "the state IS the conduction band minimum".
**Actual:** absolute Kohn-Sham eigenvalues from two separate periodic calculations share **no
common zero** — the average electrostatic potential is set by each cell's own G = 0 convention,
which differs when the composition differs. Re-anchored: **+75.9 meV** VBM-referenced,
**+52.1 meV** semicore-aligned.
**Impact:** the identification survives (all references place the state at the band edge) but
at ~50-80 meV resolution, not 7 meV. Downstream conclusions unaffected — they rest on the
spatial overlap, not the eigenvalue.
**Fix:** `Q0_RESOLVED.md` retitled to "CBM-like" with a correction banner;
`P1_REFERENCE_AUDIT.md` documents all three alignments.

## 4.12 A false execution-status claim

**Claimed:** "24 new paths running."
**Actual:** the job had failed **five consecutive times** and nothing was computing. The claim
was false when made.
**Impact:** this is the most serious entry in the log — not because of the science, but because
a status claim that cannot be backed undermines every other claim in the record.
**Fix:** `CURRENT_STATUS.md` carries a per-track true-state table and the rule now adopted:
*a track is described as running only after its own preflight reports success and output
exists; job submission is not evidence of execution.*

## 4.13 Homogeneity gate run on a subset without saying so

**Claimed:** the +8 expansion passed the gate at −36.6 meV, p = 0.6018, 0.24σ.
**Actual:** that compared **18 of 28** existing members — those whose energies happened to be
readable from an attached calculator. On the complete pool: **−102.6 meV, p = 0.1632, 0.59σ**.
**Impact:** verdict unchanged (poolable) but the margin is ~3× smaller than reported.
**Fix:** energy coverage completed to 36/36; `HOST_MANIFEST.md` carries the full-pool gate.

## 4.14 My own guard misreported a failure, twice

**Instance 1:** a produced-nothing guard globbed `m*.extxyz` while the script writes
`fa_ensemble_*.extxyz`, so it reported failure on a run that had succeeded 8/8.
**Instance 2:** a flag guard ran `driver --help`, found no flags, and reported "--pool not
accepted" when the real cause was `ModuleNotFoundError` — `--help` had crashed.
**Fix:** the guard now checks `--help`'s exit code first and reports an import failure as such.
A false positive in the preflight tool itself was also found during validation (it flagged
`open(f"{args.out}/paired_raw.json","w")` as a missing *input*) and fixed.
**Note for audit:** a guard that lies is worse than no guard, which is why these are logged.

---

# 5. WHAT IS NOT ESTABLISHED

Read this alongside Section 4. Nothing in this list may be presented as a result.

## 5.1 The charge-state ordering — the project's headline question — is OPEN

**No claim of the form "V_I⁺ migrates faster/slower than V_I⁰" is supported.** Requirements
still unmet:

1. Both endpoints relaxed at identical theory level — **q0_final not yet converged**.
2. Both CI-NEBs run at identical theory level — **neither has been run**.
3. The q=+1 explore band is unconverged (431 meV still descending) and is not a barrier.

**The ban on claiming reproduction of the literature (Tyagi) barrier ordering stands, and has
stood unbroken for the whole campaign.** The old Stage-1 fixed-path pair (141 / 127 meV) is at
a different theory fingerprint and cannot be used to sustain an ordering.

## 5.2 Absolute barrier values

No converged DFT migration barrier exists for either charge state. The only converged
DFT-level quantities are endpoint energies and the electronic-structure results of §1.5-1.7.

## 5.3 A weakly bound polaron

Excluded only down to a bound of ~8 meV under the most generous reading of POL's residual
(§1.6). A few-meV bound state is compatible with the data. Converging POL to 10⁻⁶ Ry would
tighten this and is the obvious follow-up if the question becomes load-bearing.

Additionally: polaron binding is sensitive to self-interaction error, so a hybrid functional
could in principle bind what PBE does not. Testing that would change the theory level and
would require re-running **both** charge states identically.

Only one distortion mode was probed (symmetric contraction of the two flanking Pb). The
stiffness-to-coupling ratio (2815 meV/Å² against ≤300 meV/Å) makes other modes unlikely
candidates but they were not tested.

## 5.4 Sr's equivalence

`SUGGESTIVE-EQUIVALENT` only. Its TOST passes (p = 0.0104) and its CI is inside ±59.5 meV, but
n = 10 against a required 16, and §2.6 explains why that requirement is a weak gate. **Sr must
not be described as equivalent, nor ranked against GA.**

## 5.5 Transfer of MLIP results to DFT or experiment

Every Objective 2 number is on the MACE-MP-0 potential-energy surface. The GA equivalence
result is a statement about that surface, the FA-host ensemble used, and the pure-hop
definition — not about FAPbI₃ in general and not at DFT level.

## 5.6 The 24-path extension

Completed and integrity-audited (24/24 rows clean, zero exclusions, zero overlap with the
84-path corpus, 4 of 24 strict-valid, 14 return-test candidates identified). **No statistics
from it appear anywhere in this document** — the rescue pathway is still running, and updated
n / mean / CI / TOST / variance-bound figures will be reported only when it completes.

## 5.7 Noise floor

The recorded ensemble spread (~205 meV in the stored record) is **not** a noise floor and has
never been used as one. The ±59.5 meV significance scale is a physical threshold (10× hop
rate), independently defined.

---

# 6. EXECUTION-FAILURE LOG

Kept because a record of results without a record of process is not auditable.

| # | failure | cause | cost | fix |
|---|---|---|---|---|
| 1 | endpoint relax oscillating | soft octahedral-tilt modes floor BFGS at fmax ≈ 0.04 | several resubmits | accept lowest-fmax step; documented |
| 2 | q0 spin-SCF plateau ×4 | forced `tot_magnetization` on a genuinely non-magnetic state | ~7 h cluster | §4.2 |
| 3 | job died after science succeeded | job runner uses `errexit`; a non-matching `grep` aborted the script | 1 job | `set +e`; recorded in provider notes |
| 4 | `nspin=2` from `nspin=1` density diverged | works at the SAME geometry (6 iterations), catastrophic at a different one (accuracy 10⁶ Ry, \|m\| ~7000 μB) | hours | recorded in provider notes with the `"some spin components not found"` signature |
| 5 | pool population split | mismatched relaxation depth between batches | one full corpus re-run | §4.6; fmax is now part of pool identity |
| 6 | return-test perturbation void | scaled by atom count | 1 run | §4.4 |
| 7-11 | five consecutive failed submissions of one job | invented `--base`/`--seed`; missing required `--members`; unstaged `checks.py` crashing `--help`; unstaged `--vac-ref` default; unstaged pristine file read from inside `--pool` | minutes each (all failed fast) | `scripts/25_preflight.py`, validated against all five |
| 12 | my own guards misreported twice | wrong glob pattern; `--help` crash misread as a flag error | 1 false alarm each | §4.14 |

**Preflight tool.** `scripts/25_preflight.py` parses the driver source and checks: `--help`
exits 0 (a crash is an environment problem, never a flag one); every flag passed is accepted;
every required argument is present; every locally-imported module is staged; every path-valued
argparse default exists; and every filename read from *inside* a directory argument exists —
the class no flag-level check can see. It fails all five historical invocations and passes the
correct one.

**Regression suite.** `scripts/20_test_checks.py`, 22 numbered check groups, every one firing on
an actual historical incident from this project rather than on a hypothetical. All pass.

---

# 7. FILE INVENTORY

## 7.1 Authoritative documents

| question | document |
|---|---|
| governing plan | `NEXT_STEP_GUIDE.md` |
| Objective 2 index | `results/objective2/CURRENT_STATUS.md` |
| paired result (GA/Sr) | `results/objective2/paired_pilot/CORPUS84_RESULT.md` |
| host pool ledger | `results/fa_host/pool_v3_harmonised/HOST_MANIFEST.md` |
| barrier definition | `results/objective2/BARRIER_DEFINITION.md` |
| path rejection classes | `results/objective2/paired_pilot/BASIN_IDENTIFICATION.md` (v2) |
| endpoint metastability | `results/objective2/paired_pilot/RETURN_TEST_RESULT.md` |
| q=0 electronic state | `results/objective1/dft/charge_relaxed/Q0_RESOLVED.md` + `P1_REFERENCE_AUDIT.md` |
| polaron bound | `results/objective1/dft/charge_relaxed/Q0_POLARON_EXCLUDED.md` |
| q=0 relaxation state | `results/objective1/dft/charge_relaxed/Q0_RELAXATION_STATUS.md` |
| NEB entry gate | `results/objective1/dft/charge_relaxed/Q0_NEB_GATE.md` |
| theory fingerprints | `results/objective1/dft/charge_relaxed/THEORY_LEVEL_RECONCILIATION.md` |
| protocol + stop-loss | `results/objective1/dft/charge_relaxed/LOCKED_PROTOCOL_AND_STOPLOSS.md` |

## 7.2 Superseded — do NOT cite

- `paired_pilot/PAIRED_PILOT.md` — retracted first run (index bug).
- `paired_pilot/RERUN_RESULT.md`, `RETURN_TEST_RESULT.md` **statistics** — 18-host pool; their
  *method* stands, their n = 7 numbers are superseded by the 28-host corpus.
- `objective2/AUDIT_RESPONSE.md`, `noise_floor/NOISE_FLOOR_REPORT.md` — old 8-member pool.
- `charge_relaxed/CHARGE_STATE_ANCHOR.md` — marked PROVISIONAL; the q=0 leg it awaited has
  since been partly delivered, so read `Q0_RESOLVED.md` and `Q0_NEB_GATE.md` instead.
- `charge_relaxed/Q0_SPIN_SCF_UNRESOLVED.md` — the problem it describes was self-inflicted
  (§4.2); kept as the diagnostic record only.

## 7.3 Raw evidence committed

| file | contents |
|---|---|
| `corpus84/paired_raw_84.json` | all 84 rows: profiles, gate outcomes, endpoint fmax/steps, migrating index |
| `corpus84/return_test_84.json` | 27 candidates × 4 perturbations |
| `corpus84/corpus84_bands.tar.gz` | all 84 band trajectories (5.3 MB) |
| `corpus84/corpus84_stats.json` | the published statistics |
| `pool_v3_harmonised/HOST_MANIFEST.json` | 36 members: seed, source, hash, fmax, energy + provenance |
| `pool_v3_harmonised/expansion_plus8.json` | the +8 expansion record |
| `q1/q1_initial_relaxed.extxyz`, `q1_final_relaxed.extxyz` | relaxed q=+1 endpoints |
| `q0/q0_initial_relaxed.extxyz` | relaxed q=0 initial endpoint |
| `q1_explore_state.tar.gz` | preserved `neb.path` — the CI-NEB restart point |

## 7.4 Analysis code

`05` QE inputs · `06` QE parsing · `11` neb.x input · `12` relax frames · `13` d_max ·
`16` enumeration · `17` ensemble spread · `18` explore screen · `19` GPU regression ·
`20` regression suite (22 groups) · `21` pool expansion · `22` paired pilot ·
`23` q=0 state metrics (overlap-based, not band-index) · `24` return test · `25` preflight ·
`checks.py` shared gates.

## 7.5 Figures

`corpus84.png` (equivalence + power) · `q0_polaron_excluded.png` (bound) ·
`q0_resolved.png` (CBM identification) · `return_test.png` · `rerun_paired.png` ·
`q0_projection.png` · `q0_seed_comparison.png` · `q1_explore_neb.png` ·
`noise_floor.png` · `fixed_path_profile.png` · `ga_anchor_audit.png` · `q0_gap_state.png` ·
`fa_host_structures.png` (×2) · `paired_pilot.png`

---

# 8. STANDING RULES

Adopted during the campaign and in force:

1. Never compare barriers across different theory fingerprints.
2. Never use an unconverged force for a relaxation or path calculation.
3. Never rank additives from a single configuration or from exploratory-tier data.
4. Never merge host pools built by different samplers **or at different relaxation depths**.
5. Preserve raw results — corrections create a new canonical result or a marked superseding
   report; they never overwrite evidence.
6. Commit each self-contained correction with tests and a report before launching the next
   expensive calculation.
7. A track is described as running only after its own preflight reports success **and** output
   exists. Job submission is not evidence of execution.
8. Sample-size and pool-count claims are counted from `HOST_MANIFEST.json`, never from prose.
9. Every retraction is swept **repo-wide** and checked for paraphrases, not just literal
   strings.
10. The Tyagi-ordering claim stays closed until both legs are converged at identical theory
    level.

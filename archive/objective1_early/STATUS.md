> # SUPERSEDED — archived 2026-07-28
>
> Early status ledger; anchor-b section repeatedly amended, now fully superseded.
>
> **Current authority: `RESULTS_INDEX.md`.** This file is retained verbatim below for provenance; do not cite it as current.

# Objective 1 — single status table

> **⚠️ SUPERSEDED ESCALATION ADVICE (2026-07-27).** Any recommendation below to apply a
> Hubbard U is HISTORICAL and must not drive an HPC decision. The spin-free projection
> (`Q0_PROJECTION_RESULT.md`) shows the q=0 half-occupied state is **delocalised** —
> IPR 0.0261 ≈ 38 effective atoms of 159, with the two vacancy-flanking Pb carrying only
> 2.66% and 2.44% — so a U would *impose* a localisation the physics does not support and
> yield an artefact. The convergence ladder (`Q0_CONVERGENCE_LADDER.md`) further shows the
> result is robust to `nbnd` and the Davidson subspace. **The agreed next HPC step is a
> LARGER-SUPERCELL spin-free q=0 SCF + projection**, to decide whether the delocalisation
> is intrinsic or an artefact of periodic images in the 159-atom cell. Until the q=0 state
> and its forces are established: no U, no q=0 relaxation or NEB on q=0 forces, and the
> q=0/q=+1 DFT barrier comparison stays closed.

**This file is the single authoritative status source for Objective 1 (method
validation).** Where README / HANDOFF / DFT_BENCHMARK / anchors_summary disagree
about a completion state, this table wins. Last updated 2026-07-26.

**Host definition (used identically across all DFT / MACE / strain / charge-state
comparisons).** "γ-P1" denotes a **P1 tilted γ-like CsPbI₃ model** — a 2×2×2 (159-atom
with V_I) supercell obtained by MACE-MP-0 zero-shot relaxation from a perturbed start
under **no symmetry constraint**. It is a consistent computational host, **not** a
DFT- or experiment-validated Pnma γ-CsPbI₃ equilibrium phase; do not describe it as the
"real" γ phase. Every anchor below shares this exact host.

## Anchor (b) headline status — READ THIS FIRST

```
FIXED-GEOMETRY ELECTRONIC COMPARISON:        COMPLETE  (plain PBE — see theory-level warning)
RELAXED-CHARGE-STATE MIGRATION BARRIER:      PROVISIONAL — q=+1 partial, q=0 UNRESOLVED
★ CI-NEB DECISION:                           DECIDED — full CI-NEB REQUIRED (d_max = 0.462 Å)
```

**Theory-level warning (2026-07-26).** The fixed-geometry numbers below were computed with
**plain PBE, `degauss=0.01`**. Stage-2 relaxed work uses **PBE+D3(BJ), `degauss=0.005`** —
a **2.722 Ry = 37.03 eV** absolute-energy offset, verified from the QE inputs. The two sets
**must never be compared, combined, or tabulated together**, and the fixed-geometry pair
cannot substitute for a missing relaxed leg. See
`dft/charge_relaxed/THEORY_LEVEL_RECONCILIATION.md`.

The charged-supercell DFT machinery runs end-to-end and gives a converged,
self-consistent *fixed-geometry* number (V_I⁰ 141 meV vs V_I⁺ 127 meV on the same
MACE-relaxed neutral geometry, **plain PBE**). This is **not** Tyagi et al. (2025)'s
order-of-magnitude separation — that requires *relaxed* charged geometries.

**Stage-2 progress (2026-07-26).**

- **q = +1:** both endpoints relaxed and converged at PBE+D3(BJ). Explore NEB relaxed the
  barrier 1216 → 431 meV before being stopped deliberately; interior path forces 0.43–0.56
  eV/Å against a 0.10 threshold. **431 meV is an upper bound, not a result** — it may not be
  quoted as the barrier. The relaxed band is preserved as the CI-NEB restart
  (`q1_explore_state.tar.gz`).
- **q = 0:** **UNRESOLVED.** Stop-loss reached after three diagnosed attempts (~7 h).
  V_I⁰ has 1401 valence electrons (odd ⇒ one unpaired electron). `tot_magnetization=1.0`
  completely fixed the spin-collapse failure — the moment held at exactly 1.00 for 30
  iterations — but the SCF still random-walks at 4–7×10⁻³ Ry while *absolute* magnetisation
  wanders 1.5–2.6: the moment's magnitude is pinned while its spatial distribution keeps
  rearranging between the Pb 139 / Pb 70 dangling bonds. Multi-minimum spin localisation,
  not a mixing problem. Ranked fixes in `dft/charge_relaxed/Q0_SPIN_SCF_UNRESOLVED.md`.
- **d_max = 0.462 Å** (≥ 0.4 Å threshold, and a *lower* bound since the path was still
  relaxing): the MACE geometry is not an adequate proxy for the relaxed charged path, so
  **full CI-NEB is required**. The *mechanism* nonetheless agrees with MACE — single-ion
  octahedron-edge hop, framework mean deviation 0.044 Å.

**Consequence: no charge-state comparison is possible. Anchor (b) is PROVISIONAL and the
ban on claiming reproduction of the Tyagi ordering REMAINS IN FORCE.** Even once both legs
exist, comparing E_a alone is a barrier-level approximation — a *mobility* ordering also
requires the hop attempt-frequency prefactor, which is not computed here.

## Status table

| # | date | calc ID | host / phase / supercell | method / model / charge / spin | geometry state | result | status |
|---|---|---|---|---|---|---|---|
| a-zs | 2026-07-22 | `anchors.json:regression` | local CPU / γ-P1 / 2×2×2 (159 at) | MACE-MP-0 medium zero-shot, float64, charge-agnostic | MACE-relaxed CI-NEB | E_a = **0.259 eV** fwd / 0.230 eV bwd; saddle img3 | ✅ pipeline sanity (in 0.1–0.6 eV band) |
| a-dft | 2026-07-23 | `dft_benchmark.json:anchor_a` | ehpc Slurm `comp` / γ-P1 / 2×2×2 | QE 7.5 PBE, US psl-1.0.0, Γ, ecut 50/400, non-spin | fixed-path single-point (MACE geom) | DFT **140.6 meV** vs MACE 259.0 meV (**+118 meV model-level gap**); both saddle img3 | ✅ fixed-geometry complete |
| b-fix | 2026-07-23 | `dft_benchmark.json:anchor_b` | ehpc Slurm `comp` / γ-P1 / 2×2×2 | QE 7.5 PBE, q=0 (1401 e⁻) vs q=+1 (1400 e⁻), non-spin | fixed-path single-point (same neutral geom) | V_I⁰ **140.6** / V_I⁺ **126.6 meV** (ratio 0.90) | ⚠️ FIXED-GEOMETRY COMPLETE / RELAXED PENDING |
| b-spin | 2026-07-23 | job `b520e71a` (spin_scan; 2 nodes/64 ranks) | ehpc Slurm `comp` / γ-P1 / 2×2×2 | QE 7.5 PBE, q=0 nspin 1/2, tot_mag=1, localized-Pb | fixed-path single-point | V_I⁰ non-spin **140.6** → spin **152.9 meV** (+12.3, borderline); B≡C (no polaron); q+1 mag→0 unchanged | ✅ spin scan complete |
| b-prof | 2026-07-23 | job `673e904d` (all-images; 2 nodes) | ehpc Slurm `comp` / γ-P1 / 2×2×2 | QE 7.5 PBE, imgs 1/5/6 both q, non-spin | fixed-path single-point | full 7-image profile; **img3 is the saddle for both q** (not a hidden max) | ✅ Stage 1.3 profile complete |
| c-GA | 2026-07-22 | `anchors_summary.json:anchor_c` | local CPU / γ-P1 / 2×2×2 (168 at) | MACE-MP-0 zero-shot, GA⁺ for Cs, 3 orient × near/far | MACE-relaxed CI-NEB | near +70/+278/+182 meV (spread 207); far −23 meV | ✅ sign robust / magnitude NOT converged |
| d-strain | 2026-07-22 | `anchors_summary.json:anchor_d` | local CPU / γ-P1 / 2×2×2 | MACE-MP-0 zero-shot, biaxial + isotropic strain | MACE-relaxed CI-NEB per strain | biaxial dE_a/dε = **−2.25 eV/strain** (r=−0.98) | ✅ trend reproduced (biaxial); iso branch unresolved |
| fs | 2026-07-22 | `finite_size.json` | local CPU / γ-P1 / 3×3×3 (540 at) | MACE-MP-0 zero-shot vs 2×2×2 | MACE-relaxed CI-NEB | undoped 0.259→0.258 eV; strain −41=−41; GA +70→+335 | ✅ undoped+strain size-converged; GA not |

Legend: ✅ complete · ⚠️ partial (see limits) · 🔄 in progress.

## Per-calculation detail (limits / allowed claim / next step / actual cost)

### a-zs — undoped zero-shot MACE E_a
- **Limits:** zero-shot MACE-MP-0 sits 118 meV above the scalar-relativistic PBE reference at fixed geometry (a model-level difference, see a-dft — NOT a MACE error vs ground truth); charge-agnostic (quasi-neutral PES). NOT an Eames 2015 reproduction — Eames studied MAPbI₃ (~0.6 eV); 0.1–0.6 eV is the cross-literature band.
- **Allowed claim:** "the zero-shot pipeline gives an E_a in the literature band and reproduces the octahedron-edge mechanism; usable for path seeding and float32/64 regression, not for absolute barriers."
- **Caveat:** this is an **exploratory tracer** NEB — the original driver (`scripts/01`) did not record production-quality convergence metadata (FIRE convergence return, final max NEB force, image-count densification), so 0.259 eV is a stable tracer number, not a production-converged barrier. The Stage-1.3 fixed path (b-prof) is the production-metadata reference.
- **Next step:** superseded by fine-tuned models (Stage 3).
- **Actual cost:** ~20 s/path (local CPU), negligible.

### a-dft — undoped DFT-vs-MACE benchmark
- **Limits:** PBE is not ground truth (typically underestimates halide migration barriers; no SOC, GGA delocalization). Single-point on MACE geometry, not a DFT-NEB. Γ-only, one supercell size, non-spin.
- **Allowed claim:** "MACE-MP-0 gives a fixed-path barrier 118 meV higher than the selected scalar-relativistic PBE reference on identical structures — a model-level difference (different functional/dispersion/SOC/charge treatment), not a MACE error; MACE gets the mechanism and saddle location right."
- **Next step:** completed by the all-images fixed path (Stage 1.3) + spin/cutoff/k convergence (Stage 1.2).
- **Actual cost:** part of the 8-SCF matrix, ~33 min × 8 SCF on 32 cores ≈ 4.4 core-node-hours (~¥70).

### b-fix — charge-state fixed-geometry comparison
- **Limits:** **Fixed-geometry single-point only.** Removing one electron at fixed nuclei gives a 10% electronic-energy barrier change; this is NOT Tyagi's structural (relaxed) separation. Odd neutral electron count (1401) computed non-spin — the spin treatment is being checked in b-spin.
- **Allowed claim:** "at fixed geometry, V_I⁺ is ~14 meV (10%) lower than V_I⁰; the charged-supercell DFT link now runs end-to-end and is self-consistent." **Forbidden:** any claim of reproducing Tyagi's charge-state ordering.
- **Next step:** relaxed charged endpoints + charged NEB (Stage 2), after Stage 1 locks the theory level.
- **Actual cost:** shared with a-dft (8-SCF matrix).

### b-relax — Stage 2.1 relaxed-charge-state endpoints (IN PROGRESS, multi-day)
- **Phase 0 DONE + pushed:** theory level locked/validated — degauss upgraded 0.01→0.005
  (convergence gate found the q0 odd-electron barrier shifts 15.8 meV; not converged at
  0.01), in-QE D3(BJ) validated to 0.9 meV vs the geometry-only estimate, 32-rank ≡ 64-rank.
  New PBE+D3 fixed-path baseline: **q0 = 163.3 meV, q1 = 152.8 meV**. Honest caveat:
  ecut60 (159 GB) and 2×2×2-k exceed the 124 GB cluster, so cutoff/k convergence is
  **untested** (documented, user-approved). See `dft/CONVERGENCE_GATE.md`.
- **Stage 2.1 endpoint relaxation IN PROGRESS:** DFT-relaxing the 4 charge-state endpoints
  (q0/q1 × initial/final), fixed-cell `relax`, PBE+D3(BJ), degauss=0.005, q0 spin / q1
  closed-shell. This is the first genuine step past fixed-geometry — it relaxes the nuclei
  at the DFT level, which is what a validated anchor (b) requires.
- **Convergence finding (important):** the γ-CsPbI₃ V_I cell has **soft octahedral-tilt
  modes** — BFGS floors at fmax ≈ 0.04 eV/Å (energy-converged; the residual force is real,
  not SCF noise, confirmed by QE auto-tightening conv_thr to 1e-8). Fixes applied to the
  generator: local-TF mixing (charge-sloshing), mixing_beta=0.2, trust_radius_ini=0.1,
  bfgs_ndim=3, two-tier tolerance (explore fmax≤0.05 / production fmax≤0.02), nstep cap.
  Relaxed endpoints are taken as the lowest-fmax energy-converged ionic step.
- **Wall-clock reality:** ~30 min per spin-SCF on the 159-atom cell × ~15-20 ionic steps ×
  4 endpoints ≈ 25-30 h just for endpoints; the full VALIDATED both-state relaxed CI-NEB
  campaign is **60-80 h wall (multi-day)**, exactly the guide's "Stage 2 ≈ 4× Stage 1".
  Budget is NOT the limit (~¥400 / ¥1500 cap); wall-clock is.
- **Allowed claim (unchanged):** still **FORBIDDEN** to claim reproducing Tyagi's ordering —
  that gate stays closed until both charge states have a full DFT-relaxed CI-NEB (VALIDATED).
- **Priority:** q1 (non-spin, ~2× faster) endpoints → q1 explore NEB first, as one complete
  DFT-relaxed charged NEB, then q0. Pipeline (relax→harvest→neb.x→d_max) built + verified.

### b-spin — Stage 1.1 odd-electron spin scan (COMPLETE) + Stage 1.3 full profile (COMPLETE)
- **Reproduction gate PASSED (2026-07-23, job b520e71a, 2 nodes/64 ranks):** the
  regenerated inputs reproduce the archived benchmark to ~6 significant decimals —
  img0_q0_A = −9244.90895455 Ry (archived −9244.9089544; Δ ≈ 1.5×10⁻⁷ Ry), img3_q0_A =
  −9244.89861800 Ry (archived −9244.89861758; Δ ≈ 4.2×10⁻⁷ Ry) → **barrier 140.6 meV**
  (matches the archived 140.6 meV to <0.1 meV). Confirms the QE generator (`scripts/05`)
  and that the 64-rank run reproduces the 32-rank energy at this precision.
- **Spin result (8/8 SCFs):** spin RAISES the q=0 barrier by **+12.3 meV** (140.6 →
  **152.9 meV**, mag 1.0 μB) — in the 10–20 meV BORDERLINE band. Case B ≡ Case C
  (localized guess relaxes to same solution, Δ<0.01 meV) → **no distinct localized
  polaron at PBE**. q=+1 is closed-shell (mag→0), barrier unchanged at **126.6 meV**.
- **Full 7-image profile (Stage 1.3, job 673e904d):** all 7 images evaluated for both
  charge states; **image 3 is the saddle (highest point) for both** — the benchmark
  barrier was not missing a hidden maximum. See `dft/fixed_path/FIXED_PATH_BENCHMARK.md`.
- **Allowed claim:** "the fixed-path benchmark reproduces from the repo to <0.1 meV;
  image 3 is the fixed-path saddle; the q=0 barrier is spin-sensitive (141 non-spin /
  153 spin)." NOT allowed: "DFT found the true saddle" (fixed MACE path, not DFT-relaxed).
- **Production spin setting:** nspin=2 for q=0 (odd e⁻); nspin=1 acceptable for q=+1.
- **Actual cost (measured PWSCF wall):** spin scan 8 SCFs = 7.52 h wall; all-images
  6 SCFs = 2.49 h wall → **10.0 h wall × 2 nodes = 20 node-hours = 0.83 node-days**.
  At the ¥16.48/hr E-HPC 2-node allocation rate that is **~¥165**, within the ≤¥400
  Stage-1 cap. (Per-SCF: non-spin ~25 min, spin ~55–93 min.)

### d3 — D3(BJ) dispersion correction (Stage 1.2, COMPLETE)
- **Result:** D3(BJ) computed from geometry alone (charge-independent) raises the
  fixed-path barrier by **+25.3 meV**: PBE+D3 = **165.9 meV** (q=0) / **151.9 meV**
  (q=+1). File `dft/fixed_path/d3_check.json`.
- **Limits:** additive dispersion term on the fixed MACE path (not a self-consistent
  PBE+D3 relaxation). ~18% of the barrier — well above noise.
- **Allowed claim:** "D3 is a non-negligible (+25 meV) contribution; project-wide
  functional locked to **PBE+D3** for γ-CsPbI₃ and FA host (per EXECUTION_GUIDE 1.2)."
- **SOC:** deferred — pseudopotentials are scalar-relativistic (pslibrary US
  scalar-rel); full-relativistic SOC single-points require a separate PP set and are
  recorded here as **SOC DEFERRED** (reason: scalar-rel PP; SOC is a Stage-2+ refinement).

### c-GA — guanidinium A-site pinning
- **Limits:** magnitude NOT converged — configuration-dependent (207 meV spread across 3 orientations) AND size-dependent (+70 meV at 2×2×2 → +335 meV at 3×3×3). n=1 per orientation; H-bond-stiffening mechanism inferred from N–H···I contacts (2.4–2.7 Å), not proven. GA⁺ is a stoichiometric label (MACE charge-agnostic).
- **Allowed claim:** "GA⁺ pins the local V_I hop (sign robust: positive at the near site in all 3 orientations, ~0 at the far control, confirming a local effect)." **Forbidden:** any quantitative pinning strength.
- **Next step:** configurational + size averaging under fine-tuned models; DFT spot-check (Stage 5 pilot, GA⁺ is the positive control).
- **Actual cost:** local CPU, negligible.

### d-strain — strain–E_a correlation
- **Limits:** biaxial branch sign-correct and size-converged (−41 meV/1% at both 2×2×2 and 3×3×3) but NOT strictly monotonic (+3 meV uptick at +3%). Isotropic compressive branch scatters — numerically reproducible (bit-identical tight re-run) but mechanistically unresolved (path-switching / local minima / model artefact, not proven PES roughness).
- **Allowed claim:** "biaxial tensile strain lowers E_a, compressive raises it (dE_a/dε ≈ −2.25 eV/strain, r=−0.98), size-converged." **Forbidden:** treating the isotropic compressive scatter as physical.
- **Next step:** DFT 3-point (−1/0/+1% biaxial) check (Stage 4.4 / deferred).
- **Actual cost:** local CPU, negligible.

### fs — γ-phase finite-size check
- **Limits:** 3×3×3 (~540 atoms) vs 2×2×2; single hop path.
- **Allowed claim:** "undoped absolute E_a and the strain shift are size-converged at 2×2×2; the GA magnitude is NOT (needs the larger cell + averaging)."
- **Next step:** feeds the sampling-budget decision for Stages 4–5.
- **Actual cost:** local CPU, negligible.

## Standing claim bans (from EXECUTION_GUIDE Part 1)

Do not write, anywhere in the repo or proposal, until the gating work is done:
- "we reproduced Tyagi's charge-state mobility ordering" (needs relaxed charged NEB)
- "DFT benchmarked the true migration barrier" (PBE ≠ truth)
- "the true barrier lies between PBE and MACE" (unproven; retracted from DFT_BENCHMARK.md)
- "DFT found the true saddle" (needs all-image evaluation + DFT-NEB)


---

## 2026-07-27 — q=0 escalation ladder: both no-theory-change rungs closed

**Rung 1 (degauss 0.005 → 0.001 Ry): TESTED AND FAILED.** Plateaued at ~4.6×10⁻³ Ry then
oscillated; |m| drifted **up** to 2.68, further from the physical 1.00 than any
fixed-occupation run. At 0.0136 eV smearing against a 0.230 eV gap-state separation,
fractional occupation of both spin channels should be impossible — so **smearing width is
ruled out**. The obstacle is the near-degenerate manifold itself.

**Rung 2 (cg diagonalisation): NOT VIABLE ON COST**, stopped at 3 iterations before any
numerical verdict. 1155 s/iteration vs ~150 s for davidson — 8× slower. One CI-NEB ≈ 80
days, both charge states ≈ 160 days: the same wall-clock wall that already excluded HSE06.
Even if it converged it could not be used. This is a *different* verdict from rung 1's
tested-and-failed, and the hypothesis it tests remains untested and plausible.

**Spatial seeds.** q0C (Pb139) and q0D (Pb70) reach the same plateau and agree to
**0.04 meV**, closing the site-selection question. Energy agreement at the current precision
does **not** establish that the two seeds share a wavefunction — `projwfc.x`, spin density
and IPR are still outstanding, so spatial localisation is **unproven**. The 0.5000
occupation reported earlier is an artefact of the spin-free probe (an odd electron count
forces half occupancy there) and is not evidence either way.

**Position.** q=0 supports **static energies only**. Its forces are not trustworthy, so no
DFT migration barrier — and therefore no charge-state comparison — until a theory-level
change is made and **both** legs are rerun identically. Every remaining option (DFT+U, cDFT,
hybrid) changes the theory level. A uniform U on all Pb penalises the two Pb sites
identically and cannot by itself break the Pb139/Pb70 degeneracy (they sit 6.71 Å apart on
opposite sides of the vacancy), so any U benchmark must run **together with a spatial seed**.

The anchor stays **PROVISIONAL** and the ban on claiming the Tyagi ordering stays in force.

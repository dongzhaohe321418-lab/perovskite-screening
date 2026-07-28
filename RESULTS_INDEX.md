# RESULTS_INDEX — every scientific question, its current answer, and where the evidence is

**One row per question: current conclusion · scope · authoritative file · raw data · next step.**
Anything not listed here is historical. Restructured 2026-07-28.

---

## Q1. Do GA⁺ / Sr²⁺ additives change the V_I migration barrier? (Objective 2)

- **Current conclusion:** both GA and Sr are **practically equivalent to no effect** at the
  10×-rate threshold (±59.5 meV). GA: n=11, +6.8 meV, CI [−25.0, +38.6], TOST p=0.0021.
  Sr: n=12, −4.3 meV, CI [−42.2, +33.6], TOST p=0.0042. No GA-vs-Sr ranking.
- **Scope:** MACE-MP-0 level ONLY; 36-host disordered FA₁₉Cs₁ ensemble; pure asymmetric hops;
  equilibrium forward barriers. Not transferable to DFT, other compositions, or other mechanisms.
- **Authoritative:** `results/objective2/CURRENT_STATUS.md` →
  `results/objective2/paired_pilot/CORPUS108_RESULT.md`
- **Raw data:** `results/objective2/paired_pilot/corpus108/` (raw rows, return tests, admission
  lists, band archives, input manifest, HASHES.json)
- **Next:** nothing blocking; corpus can grow if a tighter CI is wanted.

## Q2. Are V_I⁰ and V_I⁺ migration barriers separable at DFT level? (Objective 1)

- **Current conclusion: OPEN.** No validated charge-state ordering exists. The historical
  claim of reproducing the literature (Tyagi) ordering remains **banned**. q=+1 explore band:
  barrier still descending at stop (431 meV, NOT converged, NOT quotable). q=0: both endpoints
  formally converged (asymmetry −27.1 meV); NEB not yet run.
- **Scope:** PBE+D3(BJ), degauss 0.005, Γ, 159-atom γ-like cell — one vacancy, one path.
- **Authoritative:** `results/objective1/dft/charge_relaxed/Q0_NEB_GATE.md` (gate, 4/5 pass)
  + `CHARGE_STATE_ANCHOR.md` (PROVISIONAL anchor)
- **Raw data:** `results/objective1/dft/charge_relaxed/q0/` (QE outputs .gz, inputs,
  CONVERGENCE_SUMMARY.json), `q1_explore_restart/q1_explore_state.tar.gz`
- **Next:** HARNESS_TRIAL **complete** (restart-as-re-evaluation proven; `results/objective1/dft/charge_relaxed/HARNESS_TRIAL_RESULT.md`); condition 5 stays PARTIAL pending the PI's four closure items (state-ID on real wavefunctions, degauss-0.005 production inputs + fingerprint check, doc sync, clean-clone green suite); then the full q=0 CI-NEB decision.

## Q3. Is V_I⁰ a polaron or a shallow donor?

- **Current conclusion:** **no thermally significant polaron** at PBE+D3(BJ); the state is
  CBM-like (per-atom cosine 0.976 vs pristine CBM; energy agreement ~50–80 meV once properly
  referenced — the earlier 7 meV claim is retracted). A weakly bound few-meV state is not
  excluded. Seeded distortion costs ~113 meV elastic vs ≤ a-few-meV spin gain.
- **Scope:** one distortion mode probed, 159-atom cell, PBE-level gap caveats apply.
- **Authoritative:** `results/objective1/dft/charge_relaxed/Q0_POLARON_EXCLUDED.md` +
  `Q0_RESOLVED.md` + `P1_REFERENCE_AUDIT.md`
- **Raw data:** `hpc/` job outputs referenced in each document; discriminator outputs P1/P2.
- **Next:** none — closed at this theory level.

## Q4. Is the host-pool / noise floor sound for screening? (methodology)

- **Current conclusion:** 36-member pool, ALL force targets measured ≤ 0.02 eV/Å, homogeneity
  gate −31.5 meV (p=0.64, 0.20σ). Noise floor: host-ensemble σ ≈ 84 meV → paired design and
  ±59.5 meV band. Two earlier gate versions were retracted (contaminated energy ledger).
- **Authoritative:** `results/fa_host/pool_v3_harmonised/HOST_MANIFEST.md` +
  `results/fa_host/POOL_HOMOGENEITY.md` + `results/objective2/noise_floor/NOISE_FLOOR_REPORT.md`
- **Raw data:** `results/fa_host/pool_v3_harmonised/*.extxyz` + HOST_MANIFEST.json
- **Next:** none; the manifest is the single ledger.

## Historical (retained, superseded, do not cite as current)

| area | where | why superseded |
|---|---|---|
| Original MACE tracer-bullet screen | `results/dopant_screen/`, `archive/objective1_early/REPORT_objective1.md`, `archive/objective1_early/STATUS.md` | fixed-path single-point method superseded by relaxed NEB + paired design |
| Early FA baseline | `results/fa_host/REPORT_fa_baseline.md` | pool superseded by pool_v3_harmonised |
| q=0 diagnostic chain (spin-SCF saga) | `archive/objective1_q0_diagnostics/` | resolved by Q0_RESOLVED.md — kept as the record of HOW it was resolved |
| Early plans/handoffs | `archive/` | superseded by NEXT_STEP_GUIDE.md |
| Literature survey | `literature_survey/` | background material, still valid as a survey |

## Independent sub-project

- **`xrd/`** — experimental XRD passivator screening. Separate evidence chain, separate
  README, no shared conclusions with Q1–Q4.

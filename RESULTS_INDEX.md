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
  barrier still descending at stop (431 meV, NOT converged, NOT quotable — historical explore
  record). q=0: both endpoints formally converged (asymmetry −27.1 meV). **Production CI-NEB:
  BOTH legs ran and converged** (q=0: 36 iterations, q=+1: 37; see
  `results/objective1/dft/charge_relaxed/PRODUCTION_NEB_STATUS.md`) — barriers not yet extracted.
- **Scope:** PBE+D3(BJ), degauss 0.005, Γ, 159-atom γ-like cell — one vacancy, one path.
- **Authoritative:** `results/objective1/dft/charge_relaxed/Q0_NEB_GATE.md` (gate: ALL FIVE conditions PASS)
  + `results/objective1/dft/charge_relaxed/PRODUCTION_NEB_STATUS.md` (current production state) + `results/objective1/dft/charge_relaxed/CHARGE_STATE_ANCHOR.md` (PROVISIONAL — pre-production historical snapshot, superseded banner inside; to be rewritten only after gated extraction)
- **Raw data:** `results/objective1/dft/charge_relaxed/q0/` (QE outputs .gz, inputs,
  CONVERGENCE_SUMMARY.json), `q1_explore_restart/q1_explore_state.tar.gz`
- **Next:** HARNESS_TRIAL **complete** (restart-as-re-evaluation proven; `results/objective1/dft/charge_relaxed/HARNESS_TRIAL_RESULT.md`); condition 5 is PASS (all four PI closure items met: state-ID recomputable from committed weights, production pair at conv_thr=1e-8/degauss=0.005 with machine-verified fingerprint identity, docs synced, clean-clone green). The full q=0+q=+1 production CI-NEB pair was PI-authorized, ran, and **both legs converged** (q=0: 36 iterations; q=+1: 37 iterations; raw records + archives committed under `results/objective1/dft/charge_relaxed/q{0,1}_production/` — see `results/objective1/dft/charge_relaxed/PRODUCTION_NEB_STATUS.md`). Barriers are NOT yet extracted; extraction/ordering awaits audit of the evidence commit and a `check_action` ALLOW.

## Q3. Is V_I⁰ a polaron or a shallow donor?

- **STATUS: CITABLE — demotion CLOSED (see
  `results/objective1/dft/charge_relaxed/Q3_CLOSURE_RECORD.md`).** The demotion's own lifting
  condition — an audit cycle closing the Q3 findings — was met by the controller's
  verified-closed records: F-006 in CYCLE-000005, F-012/F-013 in CYCLE-000006, with three later
  cycles (000010/000011/000016) independently re-running `q3_raw/derive_q3.py` and reproducing
  every quoted value. Q3 is restored as admissible Q0-gate evidence (condition 3), consistent
  with the gate's PASS.
  *(Historical: this row carried an UNVERIFIED / NOT CITABLE demotion from 2026-07-31 — audit
  CYCLE-000001 F-006 — which was correct until the controller's closures landed; the demotion
  text outlived its own closure condition, which audit CYCLE-000016 F-019 caught as a
  contradiction with the Q0 gate.)*
  *(Superseded wording, CYCLE-000005 F-013: this row previously said the raw inputs "are not
  committed" and "cannot be independently reproduced from committed records". That was true at
  CYCLE-000001 and is no longer true — it contradicted the Raw data row below and the authority
  banners, and is retracted here.)*
- **Conclusion:** "no thermally significant polaron" at
  PBE+D3(BJ); state described as CBM-like (per-atom cosine 0.9757 vs pristine CBM, against
  pristine-internal controls 0.788/0.741; alignment +75.8 meV VBM-referenced and +52.1 meV
  semicore-aligned under one declared convention — the earlier 7 meV raw-eigenvalue claim is
  retracted as invalid); a weakly bound few-meV state not excluded; seeded distortion 112.6 meV
  elastic vs ≤2.8 meV spin gain. Every figure here **is** recomputable from committed records
  via `results/objective1/dft/charge_relaxed/q3_raw/derive_q3.py`; it is not yet **independently
  verified closed**, which is why the row stays NOT CITABLE.
- **Scope:** one distortion mode probed, 159-atom cell, PBE-level gap caveats apply.
- **Authoritative documents (each carries the Q3 provenance banner; raw data committed):**
  `results/objective1/dft/charge_relaxed/Q0_POLARON_EXCLUDED.md` + `results/objective1/dft/charge_relaxed/Q0_RESOLVED.md` +
  `results/objective1/dft/charge_relaxed/P1_REFERENCE_AUDIT.md`
- **Raw data:** COMMITTED 2026-07-31 at `results/objective1/dft/charge_relaxed/q3_raw/` —
  P1/P2 outputs, projwfc outputs, ELAS/POL discriminator outputs and inputs, cluster-side
  SHA-256 chain of custody (`REMOTE_SHA256_UNCOMPRESSED.txt`), `results/objective1/dft/charge_relaxed/q3_raw/INPUT_MANIFEST.json`, and an
  executable `results/objective1/dft/charge_relaxed/q3_raw/derive_q3.py` that recomputes and asserts every quoted value (exit 0 at this
  commit).
- **Next:** independent closure of the remaining Q3 findings. CYCLE-000005 verified F-006,
  F-008 and F-011 closed and raised F-012 (alignment convention — fixed) and F-013 (this row's
  contradiction — fixed). **Status stays NOT CITABLE until an audit cycle closes those**; the
  demotion is lifted by the controller, not by this repository.

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

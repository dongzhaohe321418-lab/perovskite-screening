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
- **Mechanism (2026-08-04):** on the balanced 9-host subset admissible in all three systems,
  the **host configuration term exceeds the dopant term by 12.3×** (SD 57.3 vs 4.6 meV;
  residual 29.7 meV). Per-system means differ by 9.3 meV while hosts span 151.7 meV; the
  dopant factor is indistinguishable from zero (ANOVA p=0.955, Friedman p=0.895). So the null
  is *structural*: at these concentrations the additive perturbs the barrier far less than the
  host's own configurational disorder. Power at the 10× target is 0.96 (GA) / 0.88 (Sr), so
  the null is informative, not merely underpowered — but detecting a 20 meV effect would need
  n≈47 (GA) / 72 (Sr), roughly 4–6× more members. See
  `results/objective2/analysis/ANALYSIS_objective2.md`, with the final result and ranked
  next experiments in `results/objective2/analysis/FINAL_RESULT_AND_NEXT_STEPS.md`
  (P1: expand to n≈50/72 for 20 meV resolution, ~2 GPU-hours at the measured 70 s/path).
- **Next:** nothing blocking; corpus can grow if a tighter CI is wanted. A 20 meV-resolution
  question would need the 4–6× larger corpus quantified above. **Pinned next-stage design:
  `results/objective2/analysis/NEXT_EXPERIMENT_DESIGN.md` (v2 — A1a/A1b/A2a/A2b/A3/E1 with the
  equivalence and pooling gates).**

## Q2. Are V_I⁰ and V_I⁺ migration barriers separable at DFT level? (Objective 1)
- **Current conclusion: EXTRACTED (2026-08-05) — barriers are INDISTINGUISHABLE at this level.**
  V_I⁰ forward barrier **185.6 meV** (36 iters), V_I⁺¹ forward barrier **181.7 meV** (37 iters);
  difference **−3.9 meV**, far below the degauss-0.005 convergence noise (15.8 meV) and the
  residual-force uncertainty. **The Tyagi charge-state ordering is NOT reproduced** — the data do
  not support a charge-state barrier separation at this level (the prior ban is now empirically
  grounded). Bare PBE+D3 barriers; **FNV residual Δ(ΔE_corr) NOT yet applied** (pp.x needs remote
  densities, E-HPC unreachable) — the qualitative conclusion is robust to a small FNV residual,
  a precise difference is not final until FNV closes.
- **Scope:** PBE+D3(BJ), degauss 0.005, Γ, 159-atom γ-like cell — one vacancy, one path, one
  composition, one theory level. No SOC, no hybrid.
- **Authoritative:** `results/objective1/dft/charge_relaxed/CHARGE_STATE_ANCHOR.md` (EXTRACTED) +
  `barrier_extraction_record.json` (hash-locked record) +
  `results/objective1/dft/charge_relaxed/PRODUCTION_NEB_STATUS.md`. NEB convergence gate:
  `results/objective1/dft/charge_relaxed/Q0_NEB_GATE.md` (gate: ALL FIVE conditions PASS).
- **Raw data:** `results/objective1/dft/charge_relaxed/q{0,1}_production/` (committed neb.out.gz,
  neb.path, archives, SHA256 custody records)
- **Open sub-item:** FNV charged-defect residual for the q=+1 leg — see `charge_correction_check.md`
  (needs pp.x on the remote densities; unblocks when E-HPC is rebuilt).
- **Next:** compute the FNV residual once E-HPC is back to finalize the difference; otherwise the
  qualitative charge-state conclusion is complete.

## Q3. Is V_I⁰ a polaron or a shallow donor?

- **STATUS: CITABLE — demotion CLOSED (see
  `results/objective1/dft/charge_relaxed/Q3_CLOSURE_RECORD.md`).** The demotion's own lifting
  condition — an audit cycle closing the Q3 findings — was met by the controller's
  verified-closed records: F-006 in CYCLE-000005, F-012/F-013 in CYCLE-000006, with three later
  cycles (000010/000011/000016) independently re-running `results/objective1/dft/charge_relaxed/q3_raw/derive_q3.py` and reproducing
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
  via `results/objective1/dft/charge_relaxed/q3_raw/derive_q3.py`, and the closure condition IS
  met (see the STATUS row and `results/objective1/dft/charge_relaxed/Q3_CLOSURE_RECORD.md`).
  *(Historical: this sentence previously ended "…which is why the row stays NOT CITABLE" —
  written before the controller's closures; caught by audit CYCLE-000017 F-019 as a
  contradiction with the CITABLE status above.)*
- **Scope:** one distortion mode probed, 159-atom cell, PBE-level gap caveats apply.
- **Authoritative documents (each carries the Q3 provenance banner; raw data committed):**
  `results/objective1/dft/charge_relaxed/Q0_POLARON_EXCLUDED.md` + `results/objective1/dft/charge_relaxed/Q0_RESOLVED.md` +
  `results/objective1/dft/charge_relaxed/P1_REFERENCE_AUDIT.md`
- **Raw data:** COMMITTED 2026-07-31 at `results/objective1/dft/charge_relaxed/q3_raw/` —
  P1/P2 outputs, projwfc outputs, ELAS/POL discriminator outputs and inputs, cluster-side
  SHA-256 chain of custody (`REMOTE_SHA256_UNCOMPRESSED.txt`), `results/objective1/dft/charge_relaxed/q3_raw/INPUT_MANIFEST.json`, and an
  executable `results/objective1/dft/charge_relaxed/q3_raw/derive_q3.py` that recomputes and asserts every quoted value (exit 0 at this
  commit).
- **Next:** none open for Q3 — closure is complete. *(Historical: this row previously said
  "Status stays NOT CITABLE until an audit cycle closes those"; the closures landed —
  F-006 in CYCLE-000005, F-012/F-013 in CYCLE-000006, recorded in
  `results/objective1/dft/charge_relaxed/Q3_CLOSURE_RECORD.md` — and the stale sentence was
  caught by audit CYCLE-000017 F-019.)*

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

### QX (XRD sub-project). Do the P1–P5 passivators change the film? (Generations-0726 screen)

- **Current conclusion:** all six films (control + P1–P5) are the same pseudo-cubic perovskite
  phase; the apparent lattice/crystallite-size differences are instrumental artifacts (the ITO
  substrate line moves — built-in control). Composition dispositions: P5 shows ~10% PbI₂
  (≈3.8× control, VALID); P3 PbI₂ below detection; remaining films per the per-film
  VALID/PROVISIONAL/NOT COMPARABLE table. **No efficacy/stability claim** — XRD composition
  and artifact analysis only, one generation of films.
- **Scope:** six films on ITO, DX-27Mini, identical protocol (absolute-intensity comparison
  permitted); sample-height/displacement artifacts dominate peak-position differences.
- **Authoritative:** `xrd/PASSIVATOR_SCREEN.md` (English) / `xrd/PASSIVATOR_SCREEN_CN.md`
- **Raw data:** `xrd/data/` (.txt + .mdi, byte-verified pairs), `xrd/results/summary_metrics.csv`,
  analysis code `xrd/analysis/`
- **Next:** nothing open — single-generation screen, complete as measured.

# Objective 2 — CURRENT STATUS (canonical index)

**Updated 2026-07-28. This file names the authoritative result for each question;
anything it does not name is historical.**

## Headline — 108-path merged corpus

**Both additives are equivalent to no effect at the 10x rate scale by the confidence-interval
test.**

| | GA | Sr |
|---|---|---|
| paired n | 11 | 12 |
| mean ΔE_a | +6.8 meV | −4.3 meV |
| 95% CI | [−25.0, +38.6] | [−42.2, +33.6] |
| CI inside ±59.5 meV | yes, 35% margin | yes, **29% margin** |
| TOST p | 0.0021 | 0.0042 |
| χ² sample requirement | 8 → met at 11 | 12 → met at 12 |

**Sr's sample-size threshold cleared MOSTLY MECHANICALLY** (2 of the 4-point drop came from
sample size alone, 2 from the variance genuinely falling 65.2 → 59.6 meV), so the CI is what
carries its claim — as agreed. GA's margin is the larger of the two.

Sr's spread is driven partly by two configurations (`m14`, `m20`) that entered via the
**return-test rescue**, not the strict gate (`Sr_m14` and `undoped_m20` both have
`gate_endpoints.passed = False`). They are kept — removing them would be selection on outcome —
and a sensitivity analysis shows the strict-only subsets are tighter (GA sd 39.8, Sr **sd 21.3**
against 47.4 and 59.6 for all pairs), so the reported all-pairs figures are the conservative
ones. Full admission-route accounting in `paired_pilot/CORPUS108_RESULT.md` §6.

**No ranking. Both are indistinguishable from zero and from each other. MACE level only.**

| question | authoritative document |
|---|---|
| paired result (GA/Sr) | **`paired_pilot/CORPUS108_RESULT.md`** + `corpus108/` raw records |
| extension provenance | `results/objective2/paired_pilot/corpus108/paired_raw_24.json`, `results/objective2/paired_pilot/corpus108/integrity_audit_24.json`, `results/objective2/paired_pilot/corpus108/input_manifest_24.json`, `results/objective2/paired_pilot/corpus108/HASHES.json` |
| host pool | `../fa_host/pool_v3_harmonised/HOST_MANIFEST.md` (v2 — 36 members, all fmax measured ≤ 0.02000, gate −31.5 meV / p 0.6422 / 0.20σ) |
| why paths are rejected | `paired_pilot/BASIN_IDENTIFICATION.md` (v2) |
| endpoint metastability | `paired_pilot/RETURN_TEST_RESULT.md` (method) + `results/objective2/paired_pilot/corpus84/return_test_84.json` (27 candidates) + **`results/objective2/paired_pilot/corpus108/return_test_24.json`** (14 candidates, 14/14 metastable) |
| barrier definition + tiers | `BARRIER_DEFINITION.md` |
| GPU validity | `gpu_regression/GATE1_GPU_REGRESSION.md` |
| automated gates | `../../scripts/checks.py` + `scripts/20_test_checks.py` (51 check groups, all passing) |

**Superseded / historical (do not cite):** `paired_pilot/PAIRED_PILOT.md` (retracted first
run), `paired_pilot/RERUN_RESULT.md` and `results/objective2/paired_pilot/RETURN_TEST_RESULT.md` statistics (18-host pool —
their *method* stands, their n = 7 numbers are superseded by the 28-host corpus),
`paired_pilot/CORPUS84_RESULT.md` (superseded by the 108-path merge; its method and retractions stand), `AUDIT_RESPONSE.md`, `noise_floor/NOISE_FLOOR_REPORT.md` (old 8-member pool).

## Execution status — corrected 2026-07-28

**A status-reporting failure is recorded here because it matters more than the science it
concerned.** I reported "24 new paths running" while the job had failed five times in a row
and nothing was computing. The claim was false when made. Corrections:

| track | true state |
|---|---|
| HPC — P1 / P2 | **audited and closed.** P1 wording corrected to CBM-like (see `../objective1/dft/charge_relaxed/P1_REFERENCE_AUDIT.md`); P2 passes all four criteria. |
| HPC — `q0_final` | **CONVERGED FORMALLY** (2026-07-28, job `f9993838`): QE convergence block at 10 BFGS steps, energy error 9.8×10⁻⁵ Ry / gradient error 1.6×10⁻³ Ry/bohr, both within criteria. E = −9247.62842357 Ry. The earlier "crossed its force target" claim at a transient sub-threshold reading stays retracted; the run later converged genuinely. Both q=0 endpoints now exist at identical theory level (asymmetry −27.1 meV). |
| GPU — 8 new hosts | **built and through the homogeneity gate.** m28–m35, see `../fa_host/pool_v3_harmonised/HOST_MANIFEST.md`. |
| GPU — 24-path extension | **was NOT running when I claimed it was.** Five submissions failed on four distinct causes (invented flags; missing required `--members`; unstaged `scripts/checks.py` crashing `--help` so the guard misreported a flag problem; two unstaged input paths). The sixth submission (all inputs staged and inventoried) **completed: 24/24 bands, exit 0**, integrity-audited, return test complete (14/14 metastable), and **merged into the published 108-path result**. |

**Rule adopted:** a track is described as running only after its own preflight has reported
success and output exists. Job submission is not evidence of execution.

**q=0 NEB gate: ALL FIVE conditions PASS (2026-07-28)** — condition 5 closed via the live HARNESS_TRIAL plus the PI's four closure items (state-ID recomputable from committed weights; production pair at conv_thr=1e-8 with fingerprint identity; docs synced; clean-clone green). Production inputs for both legs are ready; **launch requires the PI's explicit go**. See `../objective1/dft/charge_relaxed/Q0_NEB_GATE.md`.

**Sr methodology note.** The χ² sample-size threshold falls as n rises even at constant
variance (n_req 16 at n=10 → 13 at n=13 → 10 at n=20, holding sd at 65.2 meV). The final Sr
judgement must therefore rest on whether its **95% CI lies entirely inside ±59.5 meV**, not on
`n_req` clearing itself. Retained in the methods description, not used as evidence.

**Standing prohibitions:** no ranking from EXPLORE-tier data; no mixing mechanism labels or
result tiers in one distribution; no cross-theory-fingerprint comparisons; pools of
different relaxation depth never merged.

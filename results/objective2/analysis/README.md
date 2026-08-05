# Objective-2 analysis (2026-08-04)

Descriptive analysis over the already-committed, independently-audited 108-path paired corpus.
Reads **no** Q2 production CI-NEB output; no barrier extracted or quoted.

## Read in this order

1. **`FINAL_RESULT_AND_NEXT_STEPS.md`** — the result, the mechanism, and ranked next experiments
   (P1–P5, priced from the measured 70 s/path). Start here.
1b. **`NEXT_EXPERIMENT_DESIGN.md`** — **PINNED stage authority (v2)**. Executable E0–E4
   protocols after two review rounds: point-estimate framing, A1b new-vs-old protocol bridge
   (gates whether the old corpus may be pooled), E1 as ±20 meV TOST equivalence, A2a/A2b
   fixed-path DFT diagnostic at m15/m30-undoped, A3 blind-host yield/variance.
2. **`ANALYSIS_objective2.md`** — full method: reproduction check against the audited record,
   power analysis, the balanced 9×3 variance decomposition.

## Figures

- `objective2_variance.png` — host-vs-dopant: paired trajectories, the 12.3× variance split,
  both CIs against the 10× target.
- `objective2_design.png` — the d_max hypothesis (does not survive multiplicity correction) and
  what each open question costs in paired members.

## Data

- `paired_effects.csv` — all 23 pairs, per-member, strict/recovered flag.
- `analysis_summary.csv` — the headline tables as data.
- `analysis_stats.json` — full statistics with provenance and the reproduction check.
- `predictors.json` — the predictor screen: 7 examined, 6 valid correlation tests (one is
  constant across all admissible paths), with Holm-corrected p-values.

## One-line result

Neither GA nor Sr suppresses migration (both CIs exclude the 10× target); the barrier is set by
host configuration, which dominates dopant identity by 12.3×. Values are MACE-MP-0 level, not DFT.

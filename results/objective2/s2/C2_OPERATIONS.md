# S2 campaign 2 (C2): operating decisions, recorded before C2 starts (2026-11-05)

C2 is the A2 calibration on the pilot host m30 (`S2_PLAN.md` §11). This note records the analyst's decisions on how C2 is operated. It was committed before the C2 runner started and before any C2 value existed. It changes no rule of `S2_PLAN.md` or `STAGE0.md`. Where the code leaves a choice to the operator, it fixes that choice in advance.

**Basis.**
- A C2 operator runbook was drafted from the code at the campaign commit and reviewed through three adversarial lenses (code correctness, safety and blinding, completeness). It is kept in the private record folder with its review record.
- Its 21 open items were decided by the analyst, who was delegated by the PI on 2026-11-03.

Labels: [I] marks the analyst's inference or arithmetic.

## 1. What C2 runs

- **Commit.** C2 runs at the S2 campaign commit `8bff03e`, as recorded in C1's state, with no redeployment.
  - The runner fixes one commit across campaigns (`scripts/50` `check_commit`).
  - In C2 a new HEAD is accepted only through `c2/STEP0_FIX`, after a failed step-0 check.
- **Relaxations.** There are 8 A2 relaxations, one at a time, at 64 ranks (C1 throughput gate). The order is fixed (`C2_ORDER`):
  - VB136, hostB136, Sr136 D, Sr136 D+V;
  - hostB76, VB76, Sr76 D, Sr76 D+V.
  - The Ca136 pair is not run: Ca failed G1 (`C1_RESULT.md` §3.1).
  - The graph has 23 jobs: 2 checks, 8 relaxations, 8 section-11 checks and 5 gates.
- **Gates (§11), applied by the node as they fall.**
  - step-0 at k = 0 of relaxations 1 and 4;
  - K2 at the end of relaxation 1;
  - the cost projection after relaxation 4;
  - K3 after the checks of relaxations 1-8.
- **Cost [I].**
  - At the C1-measured 64-rank rate (13.10 configurations per node-hour), 8 relaxations take about 40-86 node-h, with a median of about 54.
  - That is about 2-4 days of continuous running, with no allowance for interruptions.
  - The estimate is updated from relaxation 1's measured wall time.
  - The hard cap stays at 520 node-h, against 20.6 spent.

## 2. Decisions

- **D-C2-1 (no code change).** No recorded suggestion of `STAGE0.md` §7 is applied (`C1_RESULT.md` §5).
- **D-C2-2 (after a step-0 STOP).** After any step-0 STOP the operator never starts C2 plainly.
  - A plain start with neither a STEP0_FIX at a new HEAD nor STEP0_NO_ERROR would mark every pending relaxation not_run_gate and end C2. That would lose the one repeat that §11 allows [code trace].
  - The only routes are these two:
    - `c2/STEP0_FIX`, written as `<40-hex new commit> <YYYY-MM-DD of the dated note> <repository-relative note path>`, with the checkout at that commit;
    - `c2/STEP0_NO_ERROR`, with a dated note.
  - Each needs a dated analyst decision. The watcher never relaunches after a STOP.
- **D-C2-3 (STOPs that need a code or data fix).** Any such C2 STOP ends in "stop and re-plan" by a new amendment. No C2 analogue of `c1/NODE_FIX` is added, because the runner refuses a commit change.
- **D-C2-4 (operator notes).** Every operator note (STEP0_FIX, STEP0_NO_ERROR, RESOLVE, a manual ledger entry) is passed through the hygiene check of `scripts/46` on the laptop before it is written on the node. These notes enter public JSON.
- **D-C2-5 (what the operator reads).** The operator reads decisions, counts and timings only. The blinding rule of §17 is unchanged.
  - Of an A2 record only `end_rule.outcome` is read, never `dF_200_180_meV`.
  - Of the step-0 and K3 gate files only the decision is read, never `dF_meV`, `Eb_A2_meV` or `value_meV`.
- **D-C2-6 (verifying the archive: `scripts/49 verify --campaign c2`).** The comparison is read field by field (result, decision, inputs digest), printing only equal or differ.
  - Two differences are expected from the code, and are accepted if they are the only ones:
    - **step-0, inputs digest only.** The node read the A2 output while it was still being written; the archive holds the finished file. If the step-0 result itself differs, only its k = 0 fields are compared, and a difference there is a stop.
    - **The projection's rows.** The archive holds all complete A2 records, and the node held four. The node's decision is in force (N-D1).
  - Any difference in K2 or K3, or in a step-0 decision, is a stop for the analyst. No code is changed.
- **D-C2-7 (publication).** The C2 archive is committed to this public repository after C2, as C1's was. C2 is A2-I on the pilot host. The blinding of §17 covers production and A2-II (C4) cells, and it rests on not combining raw energies, which stay visible in output files by design.
- **D-C2-8 (disk).** Nothing under the C2 directory is deleted before C4 ends, because C4 reads the C2 wall times. If less than 50 GB is free on the node's data disk at a relaxation end, the operator stops for the analyst.
- **D-C2-9 (accepted as the code reads them).**
  - The step-0 repeat restarts C2 at relaxation 1 (I-D1).
  - The operator has no pause that keeps restart data: an operator stop is SIGINT followed by the drain.
  - step0@1 survives as its applied-gate record after step0@4 overwrites `gates/step0.json`.
  - A relaunch does not rerun the node checks. The operator repeats the read-only node-script and UPF comparisons before every relaunch.
  - A relaxation that ends with no configuration k = 0 skips its step-0 gate instead of failing it. If this happens it is reported.

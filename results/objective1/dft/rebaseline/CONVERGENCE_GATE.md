# Stage 2 parameter-convergence gate — γ-CsPbI₃ V_I, PBE+D3(BJ)

**Purpose.** Before committing multi-day endpoint-relaxation + NEB budget, test whether
the base electronic parameters (ecutwfc 50 / ecutrho 400 Ry, Γ-only, degauss 0.01 Ry)
are converged for the *barrier* E(img3)−E(img0). Any parameter shifting the barrier by
>10 meV is not converged and must be upgraded. Barriers are fixed-path single-points on
the frozen MACE band (img0, img3), q=0 (nspin=2, tot_mag=1) and q=+1 (nspin=1), all
PBE+D3(BJ), nosym.

## Result

| parameter change | q0 barrier | q0 shift | q1 barrier | q1 shift | verdict |
|---|---|---|---|---|---|
| base (50/400, Γ, degauss 0.01) | 179.1 meV | — | 152.8 meV | — | reference |
| **degauss 0.01 → 0.005 Ry** | **163.3 meV** | **−15.8** | 152.8 meV | −0.0 | **q0 NOT converged** |
| ecutwfc 50 → 60 Ry | — | — | — | — | **could not run (OOM)** |
| k-points Γ → 2×2×2 | — | — | — | — | **could not run (OOM)** |

## Findings

### 1. Smearing (degauss) — q0 NOT converged at 0.01 Ry → tightened to 0.005
Halving the Gaussian smearing width shifts the **q0 (spin-polarised, odd-electron)**
barrier by **−15.8 meV** (179.1 → 163.3), well past the 10 meV tolerance. The q1
(closed-shell) barrier is unaffected (−0.0 meV). This is the smearing sensitivity of the
odd-electron V_I⁰ mid-gap state anticipated in review: a 0.01 Ry (0.136 eV) Gaussian
width over-smears the defect level and perturbs the small barrier difference.

*(Interpretation superseded 2026-10-05: the repo has since found the q=0 state CBM-like, not a
mid-gap defect level — "There is no in-gap defect level at this geometry" at the q=+1 relaxed
geometry (`results/objective1/dft/charge_relaxed/Q0_RESOLVED.md`;
`results/objective1/dft/charge_relaxed/P1_REFERENCE_AUDIT.md`; `RESULTS_INDEX.md` Q3). These q0
runs also used the later-retracted forced moment (`nspin=2`, `tot_magnetization=1`; the
`conv_dg005_img{0,3}_q0.out.gz` outputs print `total magnetization = 1.00`). The −15.8 meV
shift stands as measured for that setup; the "mid-gap defect level" explanation does not.)*

**Decision (user-approved):** lock the production smearing at **degauss = 0.005 Ry** for
both charge states. The degauss=0.005 single-points computed here **are** the new
production baseline — no separate re-baseline run was needed.

**New production PBE+D3(BJ) baseline (degauss 0.005):** q0 = **163.3 meV**, q1 = **152.8 meV**.

*(Note 2026-10-05: these are fixed-path single-points on the frozen MACE band, with q0 under the
retracted forced-moment treatment. They are a settings baseline, not production barriers. The
production relaxed CI-NEB barriers at these settings are V_I⁰ 185.6 / V_I⁺¹ 181.7 meV (bare,
FNV residual pending; `results/objective1/dft/charge_relaxed/CHARGE_STATE_ANCHOR.md`). Fixed-path
numbers may not be used in a conclusion alongside Stage-2 results
(`results/objective1/dft/charge_relaxed/LOCKED_PROTOCOL_AND_STOPLOSS.md`).)*

*Caveat:* convergence is demonstrated 0.01→0.005 (q0 still moving); a further 0.005→0.0025
check would confirm the 0 K limit but was deprioritised to conserve budget. 0.005 Ry is a
standard defect-calculation width and the adopted production value.

### 2. Plane-wave cutoff & k-points — could not be tested (memory wall)
The 159-atom cell's estimated dynamical RAM is **132 GB at base (50/400)** and
**159 GB at ecut 60/480**; a 2×2×2 k-mesh adds ~4× the wavefunction memory. The E-HPC
`comp` partition has **2 nodes × 62 GB = 124 GB total**, so ecut60 and k222 are
**OOM-killed** (exit 137) — they cannot run as a single job on this hardware. The base
50/400 job fits (~132 GB estimate overcommits into 124 GB successfully); the higher
settings do not.

**Decision (user-approved):** proceed at the base **ecutwfc 50 / ecutrho 400 Ry, Γ-only**
production setting. These are literature-standard for a 159-atom halide-perovskite defect
supercell (a single Γ point is adequate for a ~2×2×2 supercell of this size). The
cutoff/k-point convergence is recorded here as a **known, hardware-limited caveat** — it
is an honest untested axis, not a validated convergence bound. If a higher-RAM node
becomes available, ecut60/k222 should be run to close this.

## Production settings locked for Stage 2.1+

```
calculation      relax (fixed cell) / scf
ecutwfc          50 Ry      ecutrho 400 Ry     [base; cutoff conv untested — memory]
K_POINTS         Γ (1×1×1)                     [base; k conv untested — memory]
degauss          0.005 Ry   smearing gaussian  [UPGRADED from 0.01 — q0 conv]
vdw_corr         dft-d3     dftd3_version 4     [D3-BJ energy+force correction]
nspin/charge     q0: nspin=2 tot_mag=1  |  q1: nspin=1 tot_charge=1
symmetry         nosym=.true. noinv=.true.
launch           2 nodes, mpirun -np 64 (32/node)  [memory-required; 64=32 ranks wall]
forc_conv_thr    7.8d-4 Ry/Bohr (0.020 eV/Å)
```

*(Superseded, noted 2026-10-05: the q0 line above is retracted — q0 production uses `nspin=1`
with no imposed moment. See the "Current protocol for q=0: `nspin=1`" banner of
`results/objective1/dft/charge_relaxed/LOCKED_PROTOCOL_AND_STOPLOSS.md` and
`results/objective1/dft/charge_relaxed/Q0_RESOLVED.md`; the production input
`ehpc/inputs_stage2/neb_q0_production/q0_cineb.neb.in` sets no `nspin`, i.e. the QE default
`nspin=1`. The q0 single-points in this gate were run with the retracted forced-moment
treatment.)*

Files: `conv_gate_outputs/conv_dg005_*.out.gz` (degauss=0.005 baseline, 4 SCFs),
`conv_ecut60_img0_q1_OOM.out.gz` (the 159 GB estimate + OOM evidence).

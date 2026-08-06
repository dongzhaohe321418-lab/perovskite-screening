# Charge-state migration-barrier anchor — EXTRACTED (2026-08-05)

**Status: barriers extracted from the converged production CI-NEB legs.** This supersedes the
earlier PROVISIONAL pre-production snapshot. Every value here traces by SHA256 to a committed raw
`neb.out.gz`; nothing was recomputed. Extraction record: `barrier_extraction_record.json`.

Authorization: the machine-enforced audit gate (science-audit-loop) was retired; the PI authorized
extraction directly on 2026-08-05. The scientific custody discipline the gate used to enforce was
kept in full — custody-hash verification before parsing, single theory level for both legs, and no
claim beyond what the numbers support.

## Result

| leg | charge | forward barrier | backward barrier | NEB iterations |
|---|---|---|---|---|
| V_I⁰  | q = 0  | **185.6 meV** | 210.2 meV | 36 (converged) |
| V_I⁺¹ | q = +1 | **181.7 meV** | 169.7 meV | 37 (converged, per-image force ≤ 0.050 eV/Å) |

**Charge-state difference (forward, q=+1 − q=0): −3.9 meV.**

Theory level (identical for both legs, differing only in cell charge): PBE+D3(BJ), degauss
0.005 Ry, Γ-only, 159-atom γ-like CsPbI₃ supercell, ecutwfc 50 / ecutrho 400 Ry. Forward barrier
= final converged `activation energy (->)` line of each raw output.

## What this means — read the bounds, not just the number

**1. The two barriers are indistinguishable at this precision.** The −3.9 meV difference is far
below the convergence noise of the calculation itself: the measured degauss 0.01 → 0.005 shift is
−15.8 meV (CONVERGENCE_GATE.md), and the q=+1 leg's final per-image forces span 0.026–0.050 eV/Å.
A 3.9 meV separation sits inside both. The honest statement is: **at bare PBE+D3 level, on this
single path, the neutral and +1 iodide-vacancy migration barriers are equal within numerical
uncertainty.**

**2. This does NOT reproduce the Tyagi charge-state ordering.** The project's original target was
the literature report of a sizeable neutral-vs-charged barrier separation. We do not observe it.
The prior ban on claiming Tyagi reproduction is now empirically grounded: the data do not support
a charge-state barrier separation at this level. This is a clean negative result, not a failure.

**3. FNV residual is NOT yet applied — one bound remains open.** These are bare barriers. The
q=+1 leg is a charged supercell; the part of the FNV correction that survives the saddle−initial
difference, Δ(ΔE_corr), is not computed (the `pp.x` potential step needs the remote 197 MB/image
densities, and E-HPC is currently unreachable). Physically Δ(ΔE_corr) is a small residual after
the leading monopole term cancels in the difference (charge_correction_check.md), so it is
unlikely to move −3.9 meV to the Tyagi scale — but "unlikely" is not "measured". **Until FNV is
computed, the difference is reported as −3.9 meV (bare), FNV residual pending.** The qualitative
conclusion (indistinguishable, no Tyagi ordering) is robust to a small FNV residual; a precise
difference is not final until FNV closes.

## Scope

One vacancy, one path, one composition (γ-like CsPbI₃), one theory level (PBE+D3, no SOC, no
hybrid). Not transferable to other mechanisms, the disordered FA ensemble of Objective 2, or
higher levels of theory. Forward/backward asymmetry (both legs) reflects the asymmetric hop
geometry, not an error.

## Provenance

- Raw q=0: `q0_production/q0_neb.out.gz` — decompressed SHA256 `1b040ee76ec790d3…` = REMOTE_SHA256 `run/neb.out`
- Raw q=+1: `q1_production/q1_neb.out.gz` — decompressed SHA256 `0529a57971d100e6…` = SHA256.txt `uncompressed:neb.out`
- Extraction: `scripts/27_extract_barriers.py` logic (custody-verify → parse final iteration), executed 2026-08-05
- Full record with all hashes and the iteration trace: `barrier_extraction_record.json`

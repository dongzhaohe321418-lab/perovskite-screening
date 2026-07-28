> # SUPERSEDED — archived 2026-07-28
>
> Mid-campaign progress note; wholly superseded.
>
> **Current authority: `results/objective2/CURRENT_STATUS.md`.** This file is retained verbatim below for provenance; do not cite it as current.

# Objective 2 EXPLORE start + q0 campaign — progress record

Written mid-campaign so the state survives. Two independent tracks are running.

## Track A — q=0 spin localisation (DFT, E-HPC)

| variant | setting | result |
|---|---|---|
| `q0A` | `nspin=1` probe | **CONVERGED**, 27 iters, monotone to 6.1×10⁻⁷ Ry |
| `q0B` | fixed occupations, no spatial seed | running, 47 iters, residual FLAT at 4.1-4.3×10⁻³ Ry |
| `q0C` | fixed occ + spin seed on Pb 139 | queued |
| `q0D` | fixed occ + spin seed on Pb 70 | queued |

**q0A settled the electronic question.** An isolated gap state exists at E_F = 4.326 eV,
1.632 eV above the valence edge and 0.230 eV below the conduction edge, with occupation
exactly 0.5000 — one unpaired electron sharing one spatial orbital across both spin
channels. The electron is *not* spilling into the conduction manifold, so the
fixed-occupation / Hubbard family is aimed at the right problem.

It also explains the smearing failure quantitatively: `degauss = 0.005 Ry = 0.068 eV`
against a 0.230 eV gap-state-to-CBM separation is wide enough to place fractional charge
in both spin channels of the defect level at negligible cost.

**q0B is a new outcome, not a repeat.** Against criterion 2: total moment pinned at 1.00
(pass); absolute magnetisation settled at 1.70 ± 0.01 by iteration 116, after early swings of
2.50-5.52 (pass — this is the first attempt where the spin density stopped wandering); but the SCF
residual is flat at ~4×10⁻³ Ry, about 4000× above `conv_thr` (fail). So the distribution
is now stationary while the SCF still cannot close — consistent with two nearly degenerate
localisation solutions the mixer keeps trading between.

Per criterion 1, localisation is still **not** established: an isolated gap state can be
spatially delocalised. `projwfc.x` site projection on Pb 139 / Pb 70 plus an IPR is
required. It did not run in the first campaign (`disk_io='low'` withheld the wavefunction
data, and the failing post-step took the job exit code with it *after* `q0A` had exited 0);
now fixed and non-fatal.

## Track B — Objective 2 EXPLORE preparation (MACE, local CPU)

Delivered, all `EXPLORE` tier:

- `scripts/16` — enumerates 156 configurations, 13 dopants × 4 host members,
  distance-binned. Candidate table taken from `proposal_v2.tex`, not invented.
- `scripts/17` — gate-6 noise floor: undoped barrier spread across all 8 FA-orientation
  members.
- `scripts/18` — MACE EXPLORE screen with the validity gate and distribution-only output.
- `results/objective2/SCHEMA.md` — results schema with the configurational ensemble as a
  primary-key column.

### Findings that changed the design

**Minimum-image radius is 7.28 Å, not 9.7 Å.** The det-20 host cell is triclinic, so
perpendicular widths (15.98 / 16.09 / 14.55 Å) govern, not edge lengths. The proposal
states the ΔE_a decay tail extends beyond ~7 Å, so this cell can supply the **ranking**
but cannot resolve the **pinning radius** — the tail begins where the cell stops being
trustworthy. Consistent with the proposal, which already routes radius extraction to
≥4×4×4 cells.

**The first noise-floor run was rejected, not reported.** All 8 bands hit the step cap
unconverged and two returned exactly 0.0 meV. Diagnosis: the first interior image sat
*below* the initial endpoint in every single member (mean −199 meV), so the endpoints were
not local minima and "Ea" was a difference from a non-minimum reference. Cause: endpoints
were relaxed at the band's own force target and step budget, and this host has soft
molecular-rotation modes — the same class of problem diagnosed for the CsPbI₃ host. Fixed
with a dedicated endpoint stage (tighter fmax, 800 steps) and a **validity gate** that
rejects a band unless both endpoints are local minima and the saddle is interior. The
rejected 162.7 meV spread must never be quoted as the noise floor.

**Two substitution bugs caught by a composition unit test before any screening ran.**
`Cs_A` was a no-op — the A-site branch replaced the atom nearest the site, so Cs → Cs
produced an *undoped* cell reported as doped. Since Cs⁺ is the proposal's priority
candidate, this would have silently produced a null result for the most important row.
An A-site dopant must replace an FA *molecule* (8 atoms, ion at the centroid). Second, an
index shift: manifest indices are computed on the 233-atom pristine host but applied after
the vacancy iodide is deleted, so everything above it was off by one — the symptom was
`Cs_A` deleting a Pb instead of a C. Both fixed; 22/22 substitutions now produce exactly
the expected composition deltas.

## Not yet established

- q=0 spatial localisation (criterion 1) — needs `projwfc.x`
- a defensible gate-6 noise floor — rerun in progress
- any ΔE_a for any dopant — the screen has not been run on real configurations yet

No ranking exists and none may be published until the six entry gates are met.


---

# Update — 2026-07-27

## Track A, q=0 spin localisation: both cheap rungs CLOSED

| variant | outcome |
|---|---|
| q0C (seed Pb139) | plateaued at 1.55e-3 Ry, 65 iters; energy stable to 0.7 meV |
| q0D (seed Pb70) | same plateau; **agrees with q0C to 0.04 meV** |
| rung 1, degauss 0.001 Ry | TESTED AND FAILED — \|m\| rose to 2.68; smearing width RULED OUT |
| rung 2, cg diagonalisation | NOT VIABLE ON COST — 8x slower/iter, ~160 days for both legs |

Site-selection ambiguity is closed. **But energy agreement at the current precision does
not prove the two seeds share a wavefunction** — `projwfc.x`, spin density and IPR are
still outstanding, so spatial localisation remains unproven. q=0 supports static energies
only; forces are not trustworthy and no CI-NEB may run.

## Track B, Objective 2: pool expanded, pilot run, GA arm retracted

- FA pool: 18/18 accepted (`results/fa_host/pool_v2/m00..m17`), carbon-pivot rotation.
- GPU Gate 1: passed exactly (309.9168 meV on both devices, 7.7x speedup).
- Paired pilot: 54 paths run. **The GA arm is retracted** — a migrating-iodide index bug
  invalidated 8 of 18 GA arms. See [`AUDIT_RESPONSE.md`](AUDIT_RESPONSE.md). Sr's numbers stand.
- Noise floor: the 73.3 meV figure is the OLD 8-member pool's. On the new pool the undoped
  scatter is **83.9 meV** (n=6), giving n >= 16 for an unpaired design rather than 13.

## Next

P0 code fixes are done (tag-based atom tracking, convergence required for validity, force
norms, 39 test assertions). Next is a full 54-path rerun on the same 18 members, then
`projwfc.x` plus a seeded DFT+U benchmark on HPC.

> # SUPERSEDED IN PART — READ THIS FIRST
>
> **The `nspin=2` mandate for q=0 in this document is WRONG and is retracted.** So is the
> reasoning behind it: this file states that 1401 valence electrons (odd) require a non-zero
> total magnetic moment. Under Fermi–Dirac/Gaussian smearing, fractional occupation of both
> spin channels is legitimate, so an odd electron count does **not** force m ≠ 0.
>
> What the calculations showed: the unconstrained-spin run **P2** converged to
> total m = 0.00 and absolute m = 0.00 in **6 iterations** to 1.0×10⁻⁶ Ry, while every
> *forced*-moment attempt logged below failed after 47–200 iterations — and the forced-moment
> plateau sits **above** the converged non-magnetic solution. The convergence failures this
> document treats as physics were self-inflicted from the point a moment was imposed.
>
> **Current protocol for q=0: `nspin=1`**, justified by P2 and by the polaron test
> (`Q0_POLARON_EXCLUDED.md`), not adopted as an approximation. It converges roughly 5× faster
> and is what the running `q0_final` relaxation uses.
>
> **What still stands in this document:** the theory fingerprint (PBE+D3(BJ), degauss 0.005,
> ecut 50/400, Γ), the stop-loss discipline, and — importantly — the **soft octahedral-tilt
> floor**: BFGS on this cell floors near fmax ≈ 0.04 eV/Å and the accepted geometry is the
> lowest-gradient accepted step. That behaviour is now being observed again in `q0_final`.
>
> See `Q0_RESOLVED.md`, `Q0_POLARON_EXCLUDED.md`, `Q0_NEB_GATE.md`.

# Stage 2 locked computational protocol and q=0 stop-loss

Agreed with the PI after the theory-level discrepancy was found. Binding for every
Stage-2 number. Deviating from any row invalidates the charge-state comparison.

## Locked protocol — identical for q=0 and q=+1

| parameter | locked value |
|---|---|
| functional | PBE |
| dispersion | **D3(BJ)** — `vdw_corr='dft-d3'`, `dftd3_version=4` |
| pseudopotentials | pslibrary 1.0.0 US, scalar-rel: Cs.pbe-spn (z=9), Pb.pbe-dn (z=14), I.pbe-n (z=7) |
| `ecutwfc` / `ecutrho` | 50 / 400 Ry |
| k-points | Gamma only (159-atom 2x2x2 supercell) |
| smearing | Gaussian, `degauss = 0.005` Ry |
| symmetry | `nosym=.true.`, `noinv=.true.` |
| supercell | identical cell for both charge states |
| SCF `conv_thr` | 1e-6 Ry (explore) / 1e-8 Ry (production) |
| NEB images | identical count for both charge states |
| NEB `path_thr` | **0.10 eV/A for both legs** |

Only two things may differ between the legs:

- `tot_charge`: 0 vs +1
- `nspin`: ~~**2 for q=0** (1401 valence electrons — odd, one unpaired electron)~~ **RETRACTED — see the banner above; q=0 uses `nspin=1`**,
  1 for q=+1 (1400 electrons — even, closed shell)

Nothing else changes. Electron counts verified against the Stage-1 record (1401 / 1400).

## Barriers are differences within one leg

E_a(q) = E(CI-NEB saddle, charge q) - E(initial image, charge q).

Absolute total energies are **never** compared across charge states (charged cells carry a
cell-dependent neutralising-background offset) nor across theory levels (the plain-PBE
Stage-1 benchmark sits 2.722 Ry = 37.03 eV away from PBE+D3 — see
THEORY_LEVEL_RECONCILIATION.md).

**The Stage-1 fixed-path numbers (V_I0 141 meV / V_I+ 127 meV, ratio 0.90) are marked
NOT COMPARABLE with any Stage-2 result and may not be used in a conclusion.**

## q=0 stop-loss (hard)

The V_I0 spin-SCF previously stalled: accuracy oscillating around 5e-3 Ry for 30+
iterations at `mixing_beta=0.2`, absolute magnetisation fluctuating near 2.2 — the odd
electron failing to settle into a localised state.

**Pilot before commitment.** Two single-point SCFs only — the initial endpoint and the
saddle (the hardest geometry) — never a full NEB on an unproven setting.

Pilot settings: `nspin=2`, `mixing_beta=0.1`, `mixing_mode='local-TF'`, `mixing_ndim=12`,
`starting_magnetization(Pb)=0.05` (seeds the odd electron on the Pb dangling bonds
flanking the vacancy — Pb 139 at 3.45 A and Pb 70 at 3.51 A).

**Pass requires all three:**

1. `convergence has been achieved` in **both** SCFs;
2. the last several `estimated scf accuracy` values **descend monotonically** — a single
   lucky convergence after oscillation does not count;
3. total/absolute magnetisation **stabilises** rather than fluctuating.

**Budget cap: at most 3 setting combinations or 4-6 h of cluster time.**

If the cap is reached without a pass: **stop**, spend no further budget, record the
outcome as `q=0 spin-SCF unresolved`, and fall back to delivering a PROVISIONAL anchor.

If it passes: run q=0 and q=+1 CI-NEB at the identical locked level.

## Final validation criteria

- Both legs reach the same force threshold (`< 0.10 eV/A`).
- Each barrier is taken as its own CI-NEB saddle relative to its own initial image.
- Only when **both** legs are complete may the charge-state ordering be discussed.
- **Caveat carried into any ordering claim:** comparing E_a alone is a barrier-level
  approximation. A mobility ordering in the sense of Tyagi et al. also depends on the
  hop attempt frequency (the transition-rate prefactor), which is not computed here.
  Any ordering statement must be scoped to activation energies, not mobilities.

## Attempt log

| attempt | settings | outcome |
|---|---|---|
| 1 | `mixing_beta=0.2`, default mixing | FAILED — charge sloshing: accuracy stuck ~5e-3 Ry over 57+ iterations, no descent |
| 2 | `mixing_beta=0.1`, local-TF, `mixing_ndim=12`, `starting_magnetization(Pb)=0.05` | FAILED — **spin-state collapse** (diagnosis below) |
| 3 | attempt 2 **+ `tot_magnetization=1.0`**, `starting_magnetization(Pb)=0.3` | running (job f4eac4bb) — final attempt under the cap |

### Attempt 2 diagnosis — spin-state collapse, not charge sloshing

Total magnetisation by SCF iteration:

```
0.87  0.84  -0.08  -0.31  -0.02  -0.05  -0.01  -0.01  -0.02  -0.02  -0.01
```

It began near the correct ~1 μB and **collapsed to zero by iteration 3**, then stayed
there. With 1401 valence electrons (odd) the total moment cannot be zero. Gaussian
smearing permits fractional occupation of both spin channels at E_F, so QE can hold a
spin-degenerate solution that the electron count forbids; the SCF then chases an
unphysical state and plateaus — the observed stall at ~6e-3 Ry
(`0.00697 → 0.00762 → 0.00749 → 0.00579`, non-monotone).

Mixing was **not** the limiting factor here: the descent from 3.8 to 7e-3 Ry was healthy,
and absolute magnetisation stayed non-zero (0.48–0.69) while the *total* went to zero —
the signature of up/down channels equalising rather than charge oscillating.

Attempt 3 therefore constrains the moment (`tot_magnetization = 1.0`, fixing
n_up − n_down = 1) rather than relying on a seed that can be washed out, and strengthens
the Pb seed 0.05 → 0.3. This is a distinct physical fix, not a re-roll of attempt 2.

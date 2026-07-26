# q = 0 (V_I⁰) spin-SCF: UNRESOLVED

**Status: stop-loss reached. Three diagnosed setting combinations, ~7 h cluster time.
The neutral-vacancy leg is not delivered. This document records what was established so
the next attempt starts from the diagnosis rather than from scratch.**

## Why this leg is hard — the physics

The neutral iodine vacancy V_I⁰ in the 159-atom γ-CsPbI₃ supercell carries
**1401 valence electrons** (Cs z=9 ×32, Pb z=14 ×32, I z=7 ×95). Odd ⇒ exactly one
unpaired electron, which must localise somewhere. The natural host is the pair of Pb
dangling bonds left by the missing iodide — here **Pb 139 (3.45 Å from the vacancy)** and
**Pb 70 (3.51 Å)**. Electron count verified against the Stage-1 record (1401 neutral /
1400 charged).

By contrast V_I⁺ has 1400 electrons — even, closed-shell, `nspin=1` — which is exactly
why the q=+1 leg converged without incident.

## Attempts

| # | settings | outcome |
|---|---|---|
| 1 | `mixing_beta=0.2`, default mixing, `nspin=2` | charge sloshing: accuracy stuck ~5×10⁻³ Ry over 57+ iterations |
| 2 | `mixing_beta=0.1`, `local-TF`, `mixing_ndim=12`, `starting_magnetization(Pb)=0.05` | **spin-state collapse** |
| 3 | attempt 2 + **`tot_magnetization=1.0`**, `starting_magnetization(Pb)=0.3` | moment held; **accuracy random-walk** |

### Attempt 2 — spin-state collapse (diagnosed and fixed)

Total magnetisation by iteration: `0.87 0.84 -0.08 -0.31 -0.02 -0.05 -0.01 …`

Started near the correct ~1 μB, **collapsed to zero by iteration 3**. A zero total moment
is forbidden for 1401 electrons; Gaussian smearing allows fractional occupation of both
spin channels at E_F, letting QE hold a spin-degenerate solution the electron count
excludes. Absolute magnetisation stayed non-zero (0.48–0.69) while the total went to zero
— the signature of the two channels equalising, not of charge oscillation. Mixing was not
the limiter: descent from 3.8 to 7×10⁻³ Ry was healthy.

### Attempt 3 — constraint holds, convergence still fails

`tot_magnetization = 1.0` fixed the collapse **completely**: total moment read exactly
`1.00` at every one of 30 iterations. The fix was correct and should be retained.

But the SCF still does not converge. Accuracy (Ry):

```
8.143 6.798 0.477 0.352 0.248 0.0130 0.00954 0.00654 0.00596 0.00616 0.00499 0.00394 0.00407 0.00420 0.00424 0.00428 0.00504 0.00491 0.00492 0.00486 0.00446 0.00470 0.00474 0.00696 0.00688 0.00555 0.00507 0.00460 0.00419
```

After iteration 11 it stops descending and **random-walks in the 4–7×10⁻³ Ry band for
twenty iterations** — never approaching `conv_thr = 1×10⁻⁶`. Absolute magnetisation
wanders in parallel:

```
9.12 8.51 1.79 1.77 1.64 1.30 1.37 1.66 1.89 1.95 1.87 1.51 1.88 1.99 2.01 2.04 2.24 2.25 2.27 2.26 2.09 2.17 2.17 2.59 2.57 2.41 2.26 2.12 2.02
```

Total moment is pinned, but its **spatial distribution keeps rearranging** — the unpaired
electron is hopping between near-degenerate localisation patterns (the two Pb dangling
bonds, and I p-states around the vacancy) from iteration to iteration. Each rearrangement
perturbs the potential enough to reset the accuracy. This is a **multi-minimum spin-
localisation problem**, not a mixing-parameter problem, which is why three successive
mixing/seed adjustments all hit the same wall.

## What to try next (in priority order)

The remaining fixes all target *where* the electron sits rather than how the density is
mixed:

1. **Symmetry-broken localisation via a Hubbard U on Pb 6p** (`lda_plus_u`, U ≈ 2–5 eV).
   Penalises fractional occupation and picks one localised state. Cheapest real fix.
2. **`occupations = 'fixed'` with explicit `nbnd`** and no smearing, or a much smaller
   `degauss` (≤0.001 Ry). Smearing is what permits the near-degenerate mixing; removing it
   forces a definite occupation. Costs more SCF iterations but removes the ambiguity.
3. **Start from the converged q=+1 density** (`startingpot='file'`) and add the electron —
   begins from a physically sensible potential instead of a superposition of atomic
   densities.
4. **Gamma-point spin-constrained DFT** (`constrained_magnetization='atomic'`) targeting
   the moment onto Pb 139/Pb 70 specifically, rather than the cell-wide total.

Option 3 is the cheapest to attempt and composes with the others; options 1 and 2 change
the theory level and would require **re-running the q=+1 leg identically** to preserve
comparability (see LOCKED_PROTOCOL_AND_STOPLOSS.md).

## Consequence

- **No charge-state comparison is possible.** The anchor stays **PROVISIONAL**.
- The Stage-1 fixed-path numbers (V_I⁰ 141 meV / V_I⁺ 127 meV) remain **NOT COMPARABLE**
  with Stage-2 results and must not be substituted for the missing q=0 leg.
- The **ban on claiming reproduction of the Tyagi et al. ordering stays in force.**

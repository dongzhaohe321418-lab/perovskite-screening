# Objective B — FA host pool expanded to 18 homogeneous members

**Result: 18 of 18 candidates accepted**, all with every Pb 6-fold coordinated, every FA
intact, and relaxation converged (161-381 FIRE steps). Stored as
`results/fa_host/pool_v2/ m00..m17 (range of 18 files)`, renumbered contiguously so member ids are stable
and gap-free.

| | mean E (eV) | sd | range |
|---|---|---|---|
| new pool (18) | -1065.709 | 0.150 | [-1065.906, -1065.421] |
| original 0-7 | -1065.066 | 0.378 | [-1065.533, -1064.325] |

## Two failed attempts, and what they cost to diagnose

**v1 accepted 0 of 14.** Energies came back at −1.2×10⁷ eV with forces of 4×10⁷ eV/Å —
physically impossible. Cause: unconditional FA rotation drove molecular hydrogen into the
inorganic framework, producing minimum separations of 0.30 Å (Pb-H) and 0.51 Å (I-C)
against 1.01 Å in the relaxed host. MACE has never seen such geometries and returned
nonsense that tore the molecules apart.

**v2 accepted 3 of 18**, after adding clash rejection. Energies were now physical, but the
three survivors sat **8.2 eV above** the existing pool, whose own spread is 0.35 eV — a
different population, not an extension of the existing one.

**Root cause, found by reading the generator that actually built members 0-7**
(`scripts/07_fa_host_cell.py`): it rotates each FA **about its own carbon** using
minimum-image vectors. I had rotated about the molecular centroid. The carbon sits in the
A-site cage and must stay there; a centroid pivot displaces it by up to twice the
C-to-centroid offset — and for a molecule wrapped across the periodic boundary, a naive mean
of raw coordinates lands nowhere near the molecule at all (measured 4.84 Å off for FA[0]).
Doing that to all 19 molecules simultaneously is the 8 eV.

**v3, with the carbon pivot restored:** unrelaxed post-rotation energy −1062 eV (+3.4 eV
from base), fmax ~1 eV/Å, maximum carbon displacement **0.000 Å**. Verified locally with
real MACE energies before resubmitting.

## Why the new pool is used alone rather than merged with members 0-7

The new members sit 643 meV lower with a tighter spread (0.150 vs 0.378 eV) — 2.24 pooled
sd apart, or 2.62 sd excluding the `as_built` outlier.

**The two ranges barely overlap.** Against the new range [−1065.906, −1065.421], only
**1 of the 7** non-outlier original members (−1065.533) falls inside; the other six sit
above −1065.421.

> An earlier version of this document claimed 7 of 7 overlap. That was a coding error — the
> test checked only `E_old >= E_new.min()` and omitted the upper bound, so every old member
> passed trivially. The corrected figure is 1/7, and it makes the separation *stronger*,
> not weaker.

The two samplers therefore produce measurably different distributions: clash rejection
avoids the strained corners of orientation space that the original sometimes landed in, so
it reaches better minima with less scatter. Whether that is "a better-sampled version of the
same population" or "a distinct population" is not settled by these data, and the decision
does not depend on which: **merging them would confound "host member" with "which sampler
produced it"** — a nuisance variable inside the very design meant to eliminate nuisance
variables. The paired pilot therefore runs on the 18 new members as one homogeneous set.

## Route and its limitation

Random FA orientation + relax, matching members 0-7. This is **not** MLIP-MD sampling: it
draws local minima, not the thermal orientation distribution. `scripts/08_fa_md_ensemble.py`
exists for the MD route and was used for the 96-atom parent; switching route now would make
new members non-comparable with any earlier work. The limitation is recorded in
`fa_pool_expansion.json` so it travels with the data.

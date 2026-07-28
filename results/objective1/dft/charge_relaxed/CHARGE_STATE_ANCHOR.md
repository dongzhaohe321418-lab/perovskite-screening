# CHARGE_STATE_ANCHOR — **PROVISIONAL**

**Anchor (b), the V_I⁺ / V_I⁰ charge-state separation, is NOT validated.**
One of the two required legs is missing. This document states exactly what is
established, what is not, and what may not be claimed.

---

## Verdict

| item | status |
|---|---|
| q = +1 (V_I⁺) relaxed endpoints | **done** — both converged, PBE+D3(BJ) |
| q = +1 relaxed migration path | **partial** — explore NEB relaxed to 431 meV, forces 0.43–0.56 eV/Å (threshold 0.10), stopped deliberately |
| q = 0 (V_I⁰) any relaxed quantity | **not delivered** — spin-SCF unresolved after 3 diagnosed attempts |
| charge-state comparison | **impossible** — requires both legs at one theory level |
| ★ CI-NEB decision | **decided: full CI-NEB required** (d_max = 0.462 Å ≥ 0.4 Å) |

**The ban on claiming reproduction of the Tyagi et al. (2025) ordering remains in force.**

---

## What was established

### 1. The MACE path is not an adequate proxy for the relaxed charged path

`d_max = 0.462 Å`, measured between the PBE+D3-relaxed q=+1 band and the MACE band at
matched arc-length reaction coordinate, minimum-image convention per atom. The deviation
peaks at the saddle and is carried almost entirely by the migrating iodide (atom 127);
framework atoms track MACE to a mean of 0.044 Å.

Two consequences, in opposite directions:

- The **mechanism agrees** — a single-ion octahedron-edge hop, one iodide moving 4.22 Å
  (DFT) against 4.32 Å (MACE), with the framework essentially spectating. MACE gets the
  physics of the hop right.
- The **geometry does not** — 0.462 Å exceeds the 0.4 Å threshold at which a fixed-path
  single-point calculation stops being trustworthy, so **full CI-NEB is required** and
  single-points on MACE geometries cannot stand in for it.

This value is a **lower bound**: the path was still relaxing when stopped, and further
relaxation can only increase the deviation.

### 2. Stage-1 and Stage-2 numbers are at different theory levels

The Stage-1 fixed-path benchmark used **plain PBE, `degauss=0.01`**; Stage 2 uses
**PBE+D3(BJ) (`dftd3_version=4`), `degauss=0.005`**. Measured on the identical initial
structure the absolute energies differ by **2.722 Ry = 37.03 eV** — the D3 dispersion sum
over the 159-atom cell. Verified from the QE input files and confirmed by the
`DFT-D3 Dispersion Correction` block present in the Stage-2 per-image output and absent
from the Stage-1 output.

**Therefore the Stage-1 charge-state result (V_I⁰ 141 meV, V_I⁺ 127 meV, ratio 0.90) may
not be compared with, combined with, or substituted into any Stage-2 result.** It also
cannot be used to fill the gap left by the missing q=0 leg. Detail:
THEORY_LEVEL_RECONCILIATION.md.

### 3. Why V_I⁰ resists convergence — diagnosed, not merely observed

V_I⁰ carries 1401 valence electrons (odd ⇒ one unpaired electron); V_I⁺ carries 1400
(even, closed-shell). The unpaired electron has several near-degenerate places to sit —
the Pb dangling bonds flanking the vacancy (Pb 139 at 3.45 Å, Pb 70 at 3.51 Å) and
neighbouring I p-states.

Constraining the **total** moment (`tot_magnetization=1.0`) fixed the spin-collapse failure
completely — the moment then read exactly 1.00 at all 30 iterations. But the SCF still
plateaued, random-walking in the 4–7×10⁻³ Ry band while the *absolute* magnetisation
wandered 1.5–2.6: the moment's magnitude is pinned while its **spatial distribution keeps
rearranging**. This is a multi-minimum spin-localisation problem, which is why three
successive mixing and seeding adjustments all struck the same wall. Diagnosis and the
ranked list of remaining fixes: ../../../../archive/objective1_q0_diagnostics/Q0_SPIN_SCF_UNRESOLVED.md (archived; resolved by Q0_RESOLVED.md).

---

## The q = +1 numbers, and how they may be used

| quantity | value |
|---|---|
| q1_initial total energy | −9247.94069589 Ry |
| q1_final total energy | −9247.93981770 Ry |
| endpoint asymmetry | +11.9 meV (near-degenerate hop, as expected) |
| explore-NEB barrier at stop | 431 meV, **still descending ~30 meV/iter** |
| interior path forces at stop | 0.43–0.56 eV/Å (threshold 0.10) |

**431 meV is an upper bound on the relaxed PBE+D3 V_I⁺ barrier, not a result.** It must
not be quoted as the barrier, compared against the MACE 253 meV, or placed beside the
Stage-1 127 meV. The relaxed band is preserved (`q1_explore_state.tar.gz`, containing
`neb.path`) and is the restart point for the CI-NEB.

---

## What must happen before this anchor becomes VALIDATED

1. Resolve the V_I⁰ spin-SCF (../../../../archive/objective1_q0_diagnostics/Q0_SPIN_SCF_UNRESOLVED.md (archived; resolved by Q0_RESOLVED.md), options ranked by cost).
2. Run **both** legs to CI-NEB at the identical locked level, `path_thr < 0.10 eV/Å`
   (LOCKED_PROTOCOL_AND_STOPLOSS.md).
3. Take each barrier as its own CI-NEB saddle relative to its own initial image; never
   compare absolute total energies across charge states or theory levels.

**Scope limit on any eventual ordering claim.** Even with both legs complete, comparing
activation energies alone is a barrier-level approximation. A mobility ordering in the
sense of Tyagi et al. also depends on the hop attempt frequency (the transition-rate
prefactor), which is not computed here. Any ordering statement must be scoped to
activation energies, not mobilities.

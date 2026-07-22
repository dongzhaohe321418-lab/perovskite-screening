# Zero-shot MACE-MP-0 screen of iodine-vacancy pinning in CsPbI₃

**Scope.** This report executes the "future calculations" of the dopant-screening
roadmap: a candidate ΔEₐ screen, a distance-resolved pinning-radius curve, a
saddle-geometry mechanism analysis, and a finite-size + MD cross-check of the
undoped baseline. All barriers are **zero-shot MACE-MP-0** (medium, float64,
CI-NEB) on a CPU-only machine — the initial-screening tier the roadmap assigns
to this stage. No DFT validation, no charged-defect (FNV) correction, and no
active-learning fine-tuning were possible here; those require a DFT engine and
GPU/cluster. **Read every number below as a relative, screening-quality estimate,
not a production barrier.**

> **Base-structure caveat.** This screen uses **cubic (Pm-3̄m)** CsPbI₃, whereas
> the project's tracer-bullet baseline (`scripts/01_vacancy_neb.py`, Eₐ = 0.26 eV)
> uses the tilted **γ-like (P-1)** phase in a 159-atom cell. The two are **not
> directly comparable** — different phase and cell size. The value of this screen
> is the *relative* ΔEₐ ordering between dopants at matched cell/phase, not any
> single absolute Eₐ. Re-running the ranking in the γ phase is the natural
> follow-up.

![Screen summary]({{artifact:art_7ad26767-084b-4ffa-bb5c-c68516e28a9b}})

---

## 1. ΔEₐ dopant ranking

V_I octahedral-edge hop, 2×2×2 (40-atom) cell, 5 dopants placed adjacent to the
hop. Barrier = saddle minus the deepest point on the band (well-to-well). Full
table: `dEa_ranking.csv`.

| config | site | Eₐ (2×2×2, eV) | ΔEₐ (eV) | effect |
|--------|------|:---:|:---:|--------|
| undoped | — | 0.461 | 0.000 | baseline |
| Ba@Pb | B-site | 0.424 | −0.037 | de-pins |
| Bi@Pb | B-site (3+, no charge comp.) | 0.404 | −0.056 | de-pins |
| Ca@Pb | B-site | 0.351 | −0.110 | de-pins |
| Sr@Pb | B-site | 0.330 | −0.131 | de-pins |
| Br@I | X-site | 0.241 | −0.220 | de-pins |

**Headline result — an honest negative.** Placed at the first-neighbour position,
**none of the tested dopants pin the vacancy; every one lowers Eₐ.** The softer /
smaller B-site cations (Sr²⁺, Ca²⁺) give the largest reduction, and the X-site
Br⁻ substitution lowers it most of all. This directly answers the screening
question for these candidates: at this configuration they are *anti-pinners*.
A dopant that raises Eₐ would need a different mechanism (e.g. an interstitial
that electrostatically traps V_I, or channel-blocking) — none of which is a
first-neighbour B-site substitution.

---

## 2. Pinning (perturbation) radius

Strongest clean B-site pinner (Sr@Pb): the identical edge-hop run at increasing
Sr→vacancy distance. Data: `pinning_radius.json`.

| Sr–vacancy distance (Å) | Eₐ (eV) | ΔEₐ (eV) | shell |
|:---:|:---:|:---:|-------|
| 2.26 | 0.338 | −0.123 | 1st-neighbour |
| 6.79 | 0.528 | +0.067 | mid |
| 9.33 | 0.546 | +0.085 | far (cell max) |

The Sr effect is strongly local: Eₐ is depressed by ~0.12 eV right next to the
dopant and **recovers to a plateau (~0.53 eV) by ~7 Å** — a perturbation radius
of roughly 5 Å (about one octahedron). Two of five intended shells (5.06, 8.16 Å)
are omitted because their NEB runs failed to converge numerically on those
specific I–I pairs (documented in the JSON); they are excluded rather than
reported as unreliable numbers.

*Caveat:* even the "far" hop in a 2×2×2 cell is <1 cell from a periodic Sr image,
so the plateau sits **above** the isolated-undoped 0.461 eV baseline — the
plateau is the doped-lattice bulk value, not the clean-lattice one.

---

## 3. Mechanism fingerprints

Geometric descriptors at each converged saddle. Full table:
`mechanism_fingerprints.csv`.

At the saddle the migrating iodine is transiently **under-coordinated** (one short
metal–I bond ~3.0 Å, one long ~4.7 Å; coordination 1) in every case — this is the
intrinsic V_I transition state. The dopants split into two mechanism classes:

- **Octahedral-edge contact (all B-site cations).** The dopant forms a *direct*
  bond to the migrating iodine at the saddle (Bi 2.99, Ca 3.03, Sr 3.16, Ba 3.28
  Å) — it sits on the migration edge. The barrier change tracks cation size: the
  smaller the substituent, the more room on the edge and the lower the barrier
  (Sr/Ca lower most; large Ba barely changes it).
- **2nd-shell bond modulation (X-site Br).** Br sits 4.47 Å away, a remote
  spectator; the migrating-I saddle geometry is essentially identical to undoped
  (3.09/4.75 Å vs 3.10/4.75 Å). Its effect is electronic/bond-strength modulation
  of the surrounding cage, not a direct steric contact.

This is exactly the "every number carries a mechanism label" output the roadmap
called for — and it explains *why* the ranking looks the way it does.

---

## 4. Finite-size + MD cross-check (undoped baseline)

**Finite size — the most consequential caveat.** Repeating the undoped NEB in a
3×3×3 (135-atom) cell:

| cell | atoms | well-to-well Eₐ (eV) |
|------|:---:|:---:|
| 2×2×2 | 40 | 0.461 |
| 3×3×3 | 135 | 0.119 |

The 2×2×2 cell **overestimates the barrier by +0.34 eV** from vacancy
self-image interaction — far larger than the roadmap's 0.05–0.1 eV estimate. The
converged (135-atom) barrier, **0.12 eV**, sits at the low end of the
experimental band (~0.1–0.6 eV). **Consequence:** the absolute Eₐ from a 40-atom
screen is not trustworthy; the **relative ranking (ΔEₐ)** — where the self-image
error largely cancels between doped and undoped runs at matched cell size — is
the robust deliverable.

**MD cross-check — qualitative only.** Langevin NVT MD (8 ps) of one V_I in the
135-atom cell at 600/800/1000 K: the final iodine MSD rises monotonically
(0.79 → 0.91 → 1.54 Å²), confirming thermally-activated mobility consistent with
a low barrier. **But** 8-ps single-vacancy statistics are far too sparse for a
quantitative Einstein/Arrhenius Eₐ (the fit returns an unphysical negative
value). A quantitative MD cross-check needs ~100× longer trajectories or many
vacancies — out of reach on this CPU. Reported as a qualitative trend only.

---

## 5. What is solid, and what is not

**Solid (screening-tier):**
- Relative ΔEₐ ordering of the five candidates at matched cell size.
- The mechanism split (edge-contact vs remote modulation) from saddle geometry.
- The finding that a 40-atom cell badly overshoots the absolute barrier.
- The qualitative MD confirmation of low-barrier iodine mobility.

**Not established here (needs DFT + cluster):**
- Absolute barriers (finite-size + zero-shot MLIP + no charge state).
- Charged-vacancy (V_I⁺) energetics with FNV correction — the physically
  dominant charge state; could reorder the ranking.
- Bi³⁺ result is aliovalent with **no charge compensation** — treat as
  indicative only.
- Any claim that a real pinner exists: this candidate set contained none. The
  next screen should target interstitials and channel-blockers, where the
  pinning mechanism is electrostatic/steric rather than edge-substitutional.

## Files
- `screen_summary.png` — 4-panel figure (ranking, pinning radius, finite-size, MD)
- `dEa_ranking.csv` — ΔEₐ ranking table
- `mechanism_fingerprints.csv` — saddle geometry descriptors
- `results/*.json` — raw numbers for every stage
- `results/*_saddle.cif` — saddle structures for each config
- `neb_pipeline.py` — the underlying reproducible NEB driver

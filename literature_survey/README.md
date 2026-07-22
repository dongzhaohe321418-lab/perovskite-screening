# Halide-Perovskite Stability — Panorama Literature Survey

A referee-grade panorama of halide-perovskite stability research, assembled by systematic
retrieval from the OpenAlex scholarly graph and arXiv (2020–2026 emphasis window, with
foundational work back to 2000) and one-step citation-graph expansion on the most-cited
paper in each theme.

**Corpus:** 146 unique papers · 73/146 (50%) published 2020–2026 ·
13 cross-cutting · all DOIs CrossRef-verified (0 retractions).

## Contents

| File | Description |
|------|-------------|
| [`perovskite_stability_review.md`](perovskite_stability_review.md) | Full ~16,000-word review with inline DOI citations and a 146-entry reference appendix |
| [`perovskite_stability_review.pdf`](perovskite_stability_review.pdf) | Concise 5-page presentation version with both diagrams |
| [`perovskite_stability_references.csv`](perovskite_stability_references.csv) | Master reference table (title, authors, year, venue, DOI, citations, theme tags) |
| [`figures/`](figures/) | Publication timeline and thematic-landscape figures |
| [`sections/`](sections/) | The seven per-theme review sections (source prose) |
| [`papers/`](papers/) | Per-theme paper lists as JSON (with per-paper findings) |

## The seven stability channels

1. **Phase & compositional stability** — black-phase survival, tolerance factor, A-site/halide mixing
2. **Environmental degradation** — moisture, oxygen, heat, UV, photo-oxidation
3. **Ion migration & point defects** — the mechanistic hub; iodide-vacancy transport, hysteresis, segregation
4. **Strain & lattice engineering** — residual strain as an intrinsic degradation lever
5. **Defect passivation, additives & doping** — the dominant practical stability toolkit
6. **Device operational stability & encapsulation** — ISOS protocols, operational vs. shelf lifetime
7. **Computational & ML methods** — DFT, MLIPs/foundation models, high-throughput screening

## Organising insight

Ion migration occupies a privileged causal position: a ~0.2 eV rise in the migration
activation energy suppresses the room-temperature migration rate ~1000×. Strain,
composition, and passivation strategies largely register their stability benefit *through*
migration, and migration is the one channel encapsulation cannot exclude. This motivates the
repository's core computational programme — a mechanism-resolved, MLIP-accelerated screen of
ion-migration-suppressing dopants in γ-CsPbI₃.

---
*Generated as part of the perovskite-screening project. Citation counts reflect OpenAlex at
time of retrieval and are age-biased (recent work has had less time to accrue citations).*

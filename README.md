# perovskite-screening

MLIP-accelerated screening of ion-migration suppressing dopants in halide
perovskites. Companion code to the research proposal *Rational Design of
Ion-Migration Suppressing Dopants in Halide Perovskites* (July 2026).

Current status: **tracer bullet** — the minimal end-to-end pipeline of the
months 1–2 milestone: undoped CsPbI₃, single iodide vacancy, zero-shot
MACE-MP CI-NEB.

## Setup (this machine)

This machine sits behind a TLS-intercepting proxy; Python HTTPS needs the
exported keychain bundle in `.certs/system.pem` (not committed).

```bash
uv venv --python python3.13
SSL_CERT_FILE=.certs/system.pem uv pip install --native-tls -r requirements.txt
```

## Run

```bash
export SSL_CERT_FILE=.certs/system.pem   # needed for the MACE checkpoint download
.venv/bin/python scripts/00_relax_bulk.py    # cubic + tilted gamma-like bulk
.venv/bin/python scripts/01_vacancy_neb.py   # V_I hop barrier, 2x2x2 supercell
```

Outputs land in `results/` (JSON + barrier.png + optimizer logs) and
`structures/` (extxyz).

## What the numbers mean — and what they don't

- `00_relax_bulk.py` relaxes the ideal cubic cell, then lets a
  symmetry-broken 20-atom cell fall into the tilted (gamma-like) phase, and
  reports the detected space group and the energy gained by tilting.
  Experimental γ-CsPbI₃ is orthorhombic *Pnma* with pseudo-cubic lattice
  parameter ≈ 6.25 Å.
- `01_vacancy_neb.py` computes the octahedron-edge V_I hop barrier with
  CI-NEB. **Zero-shot MACE is charge-agnostic**: this is a quasi-neutral
  PES, not the production V_I⁺ barrier, and MPtrj-trained checkpoints bias
  barriers low (softening). The number validates the pipeline (literature
  window 0.1–0.6 eV) and seeds paths; ranked ΔE_a values require the
  per-charge-state fine-tuned models of the proposal's Phase 3.

## Roadmap (mirrors the proposal)

- [x] Phase MVP: bulk + single V_I CI-NEB, zero-shot (this repo, tracer bullet)
- [ ] DFT anchors: convergence tests, FNV corrections, QE/VASP single points
- [ ] Objective 1 anchors: charge-state ordering (Tyagi 2025), GA⁺ ΔE_a, strain–E_a
- [ ] Phase 1–2 at scale: dopant enumeration, MLIP-NEB farm
- [ ] Phase 3: per-charge-state active-learning fine-tuning
- [ ] Phase 4: ΔE_a ranking, pinning radii in ≥4×4×4 cells
- [ ] Phase 5: top-5 MD (MSD–Arrhenius) + kMC cross-validation

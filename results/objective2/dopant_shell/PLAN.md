# Dopant–vacancy interaction and DFT validation of the MACE results — pre-registered plan

**Status: PLAN, written 2026-10-25 before any production result was read.** Criteria below are
fixed now so the analysis cannot be tuned after the fact. Changes after this date are appended
as dated amendments, never edited in place.

## Why

The 108-path corpus (`../paired_pilot/CORPUS108_RESULT.md`) put each additive on the single site
nearest the vacancy (`scripts/22_paired_pilot.py`). That answers "does one near-dopant hop change
its barrier", not "does the dopant change iodide transport". In a solid, a dopant changes vacancy
transport mainly by binding (trapping) or repelling the vacancy. Re-analysis on 2026-10-18 also
showed the nearest-site rule mixes two physically different Sr sites (the Pb that holds the
hopping iodide in 16/36 hosts, the far-side Pb in 20/36) and three different GA A-sites. All
corpus numbers are MACE-MP-0 (zero-shot), never validated against DFT for the doped FA host.

## Work packages

| WP | what | method | output |
|---|---|---|---|
| 1 | dopant–vacancy binding map E_b(r) | MACE, `scripts/29_dopant_shell_scan.py`: every Pb site (Sr) and every FA site (GA), vacancy fixed; E_b(j) = E[D_j+V] − E[D_j] − E[V] + E[host], all relaxed (FIRE, fmax 0.02, fixed cell) | `shell_mNN.json` per host |
| 2a | DFT electronic settings | PBE (no D3) single points on m30 undoped img0/img3: k-sampling Γ / R-point / 2×2×2; degauss 0.005 vs 0.0025; nspin 1 vs 2 | chosen production fingerprint |
| 2b | barrier transfer | DFT single points on the MACE bands (images 0, 2, 3, 4, 6) for the 9 balanced hosts × {undoped, GA, Sr} | DFT ΔE_a on MACE paths vs MACE ΔE_a |
| 2c | binding-energy transfer | DFT single points on WP1 MACE-relaxed structures, 3 hosts × {Sr near-hinge, Sr other flank, Sr mid, Sr far, GA near, GA mid, GA far} + host + V | DFT E_b vs MACE E_b |
| 2d | charge state | m30: vacancy cells of 2c at tot_charge = +1 (V_I⁺; even electron count) | E_b(q=+1) vs E_b(q=0) |
| 2e | geometry transfer | residual DFT force at every MACE minimum; DFT relaxation of 2 endpoints if the gate fails | single-point bias estimate |
| 3 | fine-tuned MACE | fine-tune MACE-MP-0 on WP2 frames (energies + forces) with isolated-atom E0s (`scripts/31_qe_atom_e0.py`); split by host | re-run WP2 quantities and the WP1 map on held-out hosts |

DFT fingerprint (WP2/3): pslibrary 1.0.0 US, ecutwfc 50 / ecutrho 400 Ry, Gaussian smearing,
nspin = 1 for the neutral odd-electron cells, plain PBE because MACE-MP-0 was trained on MP
PBE(+U) without dispersion. This is NOT the Objective-1 fingerprint (PBE+D3(BJ)); the two sets of
numbers are never compared (standing rule 1). The free energy F ("! total energy") is used
throughout; −TS is logged per frame.

**k-sampling note (design review DFT-1).** In the det-20 FA supercell the primitive R point,
where both band edges sit, folds to supercell (½,½,½), not Γ (supercell matrix M has det 20;
R → (−½, −½, ½) mod 1). Γ-only therefore misses the band edges and puts the vacancy's extra
electron in a folded conduction state. WP2a decides between the single R-point and 2×2×2.

## Pre-registered acceptance criteria

1. **WP1 noise floor.** E_b at sites with d > 8 Å must scatter about 0 with |mean| < 15 meV and
   SD < 25 meV per dopant (pooled over hosts). If not, relaxation noise (FA basin hopping)
   dominates and WP1 is reported as inconclusive below that floor.
2. **WP1 verdict.** A dopant "binds" or "repels" the vacancy only if the nearest-shell mean E_b
   differs from the far-site mean by more than 2× the far-site SD and the sign holds in ≥ 2 of 3
   hosts. Thermal relevance threshold: |E_b| > k_BT = 25.7 meV at 298 K.
3. **WP2b MACE validity for ΔE_a.** MACE is accepted for paired barrier differences if, over
   the 18 paired (host, dopant) comparisons, RMS(ΔE_a^MACE − ΔE_a^DFT) < 20 meV and no pair
   flips across the ±59.5 meV equivalence band. If RMS ≥ 20 meV the corpus equivalence result is
   re-stated at DFT level from WP2b and the MACE numbers are downgraded.
4. **WP2c MACE validity for E_b.** Accepted if |E_b^MACE − E_b^DFT| < 25 meV for every site
   tested and the near-vs-far sign agrees.
5. **WP2e geometry gate.** Residual DFT force at MACE minima: RMS < 0.05 eV/Å and max < 0.2 eV/Å;
   otherwise single-point energies are reported with the WP2e relaxation bias as an error bar.
6. **WP3 fine-tuning.** Reported as an improvement only if, on held-out hosts, force RMSE and
   ΔE_a / E_b errors versus DFT all decrease relative to zero-shot MACE.

## What will not be claimed

No absolute MACE-vs-QE energies (different pseudopotential references). No DFT barrier from the
fixed-path single points is a relaxed DFT barrier: the DFT maximum along a MACE path is an
upper-bound-type diagnostic, not the DFT saddle. No transfer to experiment.

## Long-term goal

This study is stage S1 of `../SCREENING_ROADMAP.md` (adopted 2026-10-25): a validated multi-dopant
screen. Its verdict decides whether later stages use zero-shot or fine-tuned MACE.

## Amendment 2026-10-25a (after WP2a; no WP1/WP2b result read)

*Date correction (2026-10-25): amendments a–c were first labelled 2026-10-26 by a clerical
error; all were written and committed on 2026-10-25 (git timestamps are authoritative). Content
unchanged.*

- Production k-sampling fixed to the single R point (½,½,½); see `WP2A_KPOINTS.md`.
- WP2b images reduced from 7 to {0, 2, 3, 4, 6} per band (the MACE saddle is image 3 on every
  admissible path; 2 and 4 bracket it): 135 single points.
- Criterion 5 fails on the first frame tested (m30 undoped img0: RMS 0.152, max 0.354 eV/Å);
  WP2e is therefore triggered regardless of the remaining frames.

## Amendment 2026-10-25b

- WP2e relaxes the m30 image-0 endpoint of all three systems (undoped, GA, Sr), not two, so the
  single-point bias can be compared within the pair for both dopants. Fixed cell, BFGS,
  forc_conv_thr 7.8e-4 Ry/bohr (0.02 eV/Å, the corpus target), R-point.
- Isolated-atom E0s computed (`e0_atoms/E0_isolated_atoms.json`), all converged at the Hund moment.

## Amendment 2026-10-25c — after the design review; written before any v2 result was read

The adversarial design review (34 agents; 15 of 16 issues confirmed by independent skeptics)
changes WP1 and adds decision rules. No v2 E_b value existed when this was written. The
exploratory v1 run (cold start, fmax 0.02; script 29 at commit 5d9a3ca) was in progress and
its log showed near-shell Sr values; the rules below are fixed from geometry and from the
review, not from those values, and v1 numbers are not reported as binding energies.

1. **WP1 protocol v2** (`scripts/29_dopant_shell_scan.py`): D_j relaxed from the relaxed host,
   D_j+V from the relaxed V (warm start); every relaxation run through fmax 0.02 → 0.01 → 0.005
   eV/Å with the energy recorded per stage; basin check on atoms > 6 Å from both defects
   (max displacement < 0.25 Å and max FA-axis rotation < 20° for both partner pairs).
2. **Depth gate.** Pilot: m30, m21, m05 × {Sr, GA} × (2 nearest + 3 farthest sites). Adopt the
   loosest fmax at which every pilot E_b is within 5 meV of its fmax-0.005 value.
3. **Far reference** (from the shell gaps of the true minimum-image distances): Pb sites with
   d > 8.5 Å and C sites with d > 9.0 Å (8–10 sites per member). These lie beyond the 7.28 Å
   minimum-image radius of this cell, so E_b(far) is a sum over periodic vacancy images, not an
   asymptotic zero; E_b is reported as E_b − median(far) with the far-set SD. No trapping range
   beyond ~7 Å is resolvable in this 233-atom cell.
4. **Charge-state rule (WP2d).** If |E_b(q=+1) − E_b(q=0)| > 25 meV at any tested site, or the
   near-minus-far sign differs between q = 0 and q = +1, the WP1 map is labelled V_I⁰-specific
   and not carried over to V_I⁺ transport. WP2d scope: Sr near-hinge and one far Sr site; GA
   nearest and one far GA site; one Sr band (img0, img3) at q = +1 for ΔE_a. Only the vacancy
   cells carry charge, so the compensating-background term cancels within each E_b and ΔE_a.
5. **WP2e error bar.** The single-point bias on ΔE_a is ΔE_relax(dopant) − ΔE_relax(undoped)
   within a host pair (it need not cancel: GA replaces an FA, where the residual force sits).
   One E_b quartet (m30, Sr near-hinge: host, V, D, D+V) is also DFT-relaxed. Criterion 5 is
   applied to every WP2b frame, not only to img0.
6. **Smearing/spin rows (WP2a).** At the R point: degauss 0.0025 Ry on m30 img0/img3, nspin = 2
   on img0. ΔE_a must move by < 3 meV, else degauss 0.0025 is adopted or the σ→0 estimate
   E₀ = F + TS/2 is reported beside F.
7. **Fine-tuning data (WP3).** Offset fit must be full rank (vacancy-free frames required);
   60–120 off-equilibrium frames (300 K MACE-MD snapshots, 0.05–0.1 Å rattles) added with
   config_type "rattle"; held-out hosts never contribute any frame.

## Amendment 2026-10-25d — WP1 analysis definitions; written before any v2 E_b value existed

At writing, the v2 depth pilot had produced no E_b row (all three hosts still relaxing their
references). The definitions are taken from the unrelaxed host geometry of the pilot hosts
(m30, m21, m05), whose minimum-image dopant–vacancy distances show wide natural gaps
(Pb: 3.17–3.28 | 6.90–7.69 | 9.13–11.96 Å; C: 4.15–5.11 | 7.38–8.49 | 9.67–11.25 Å).
Implemented in `scripts/34_dopant_shell_analysis.py`.

1. **Shells.** Sr (Pb sites): near d < 5.0 Å (2 sites), far d > 8.5 Å (10 sites). GA (FA sites):
   near d < 6.0 Å (3 sites; the fourth nearest A-site is the Cs), far d > 9.0 Å (8 sites).
   Everything between is "mid". d is the unrelaxed minimum-image distance to the vacancy site.
2. **Criterion 1** is evaluated exactly as written (valid rows with d > 8 Å, pooled over hosts,
   SD with ddof = 1). Because far E_b is a periodic-image sum (amendment c, item 3), a failure of
   the |mean| < 15 meV part with the SD part passing is reported as such, not reinterpreted.
3. **Criterion 2.** Pooled near mean minus pooled far mean (far as in item 1); a verdict
   ("binds"/"repels") requires |difference| > 2 × pooled far SD AND the same sign of the per-host
   near − far difference in ≥ 2 of 3 hosts. Thermal relevance flagged at |difference| > 25.7 meV.
4. **Production hosts** for WP1: m30, m21, m05 (the pilot hosts; also the WP2c hosts), all 20 Pb
   and 19 FA sites each, at the depth adopted by the gate (references always at fmax 0.005).
5. Invalid rows (convergence, vacancy refilled, dopant displaced, basin check) are excluded and
   listed with reasons; they are never replaced by re-runs with different settings unless that
   is recorded as a further amendment before the re-run results are read.

## Amendment 2026-10-25e — WP3 split and off-equilibrium frames; written before any fine-tuning

1. **Host split (fixed now).** test = {m30, m32}, valid = {m21}, train = {m05, m06, m08, m12,
   m15, m20}. m30 is held out because it carries the most DFT-only data (WP2c E_b, WP2d charge
   state, WP2e relaxations), so criterion 6 is tested on E_b and ΔE_a of an unseen host. m21's
   WP2c frames are validation only; m05's WP2c frames enter training.
2. **Off-equilibrium frames** (`scripts/35_finetune_frames.py`, training hosts only): per host,
   {band image 0 of undoped, GA, Sr; pristine host} × {framework-only rattle σ = 0.05 and
   0.10 Å on Pb/I/Cs/Sr; last frame of 1.5 ps 300 K and 450 K Langevin MACE-MD} = 96 frames.
   This replaces the "0.05–0.1 Å rattles" of amendment c item 7: in a smoke test (m05,
   2026-10-25) a uniform all-atom rattle displaced H far beyond thermal amplitudes (MACE forces
   up to 84 eV/Å; 7 of 12 frames failed the pre-set 15 eV/Å sanity bound), whereas the new set
   gave 16/16 frames within bounds (framework rattles 0.3–1.4 eV/Å, MD 2.9–4.6 eV/Å max force
   after 3 MD steps). The pristine-host frames also make the offset fit of `scripts/33` full rank
   without relying on WP2c.

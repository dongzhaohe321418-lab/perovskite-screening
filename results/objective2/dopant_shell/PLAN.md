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

## Amendment 2026-10-25f — WP2c/2d/2e site selection; geometric, before any v2 E_b

Implemented in `scripts/36_wp2cde_inputs.py`; only valid WP1 rows are used and every choice is
written to `wp2cde_selection.json`. Sr hinge = the near-shell Pb closer to the migrating iodide
(the iodide nearest the vacancy site, as in `scripts/22`); Sr flank = the other near-shell Pb;
mid and far = the valid site of that shell whose distance is closest to the shell's median
distance (ties: lower index); GA near = the nearest valid FA. A hinge/flank assignment with
Pb–I(mig) distances within 0.5 Å is flagged as ambiguous (m30, unrelaxed: 3.20 vs 7.12 Å).
WP2d additionally includes band images 0 and 3 of **undoped** m30 at q = +1 (ΔE_a needs both
members of the pair; amendment c item 4 named only the Sr band). Charged (_q1) and relaxed
(_relax) frames are excluded from fine-tuning by label.

## Amendment 2026-10-25g — after the code review; written before any WP2c/2d frame existed and before the WP1 pilot produced an E_b

A second adversarial review (84 agents: 39 candidate defects, each reproduced or refuted by two
skeptics with different lenses, plus a completeness critic) examined scripts 29–36 and
amendments a–f. No WP2c or WP2d input had been generated and no v2 E_b existed when this was
written. WP2b was 30/138 complete; its interim numbers motivate nothing below except item 2,
which is a completeness rule, not a change of threshold.

1. **Finite-cell band term in DFT E_b(q = 0) (critic, confirmed).** The extra electron of the
   neutral V_I sits in a delocalised CBM-like state (RESULTS_INDEX Q3). A substituent shifts
   that band in the whole 20-f.u. cell: at m05 image 0 the Fermi level moves by +57.8 meV with
   Sr on the near Pb and +16.5 meV with GA (image 3: +50.5 / +13.9 meV; semicore-aligned values
   agree within ~10 meV). To first order this term does not depend on the dopant–vacancy
   distance, vanishes in the dilute limit, is absent at q = +1, and cannot be represented by
   MACE. A site-independent offset of the same order also arises between the charged V⁺ and
   D+V⁺ cells (average-potential/background term; the sentence in amendment c item 4 that it
   "cancels within each E_b" holds only for ΔE_a, where composition is fixed). Therefore:
   - **Criterion 4 is evaluated on far-referenced values**, E_b(site) − E_b(far site of the same
     dopant, host, level and charge), for every WP2c site; the raw-E_b comparison is reported
     beside it, together with the far-site DFT E_b(q = 0) and E_b(q = +1) as the measured
     finite-cell term.
   - **The WP2d 25 meV rule** (amendment c item 4) is likewise applied to far-referenced
     E_b(q = +1) − E_b(q = 0); the near-minus-far sign test is unchanged.
   - For WP2b, the paired DFT ΔE_a of a neutral cell contains the change of this level between
     images 0 and 3 (m05 Sr: −7.3 meV relative to undoped); this is reported as a known
     neutral-cell contribution, and the q = +1 m30 bands of WP2d measure ΔE_a without it.
2. **WP2b completeness (criterion 3).** A band is used only if all five pre-registered images
   {0, 2, 3, 4, 6} converged; a pair only if both bands are complete. Criterion 3 is reported as
   "incomplete" unless all 18 pairs exist; a "flip" is any change of class among
   {< −59.5, inside, > +59.5 meV} between DFT and MACE (sign reversals across the band included).
   Criterion 5 is reported for every minimum frame (images 0 and 6) of every band, with the
   saddle frames (image 3) reported separately.
3. **WP1 analysis (script 34).** Only files named exactly `shell_mNN.json` are read; all hosts must
   share one protocol and their references must reach fmax ≤ 0.005; (host, dopant, site) must be
   unique. Map mode takes E_b at an explicit `--fmax` (the depth adopted by the gate), with
   validity judged at that stage. The depth gate is reported only when the pre-registered pilot
   set (m30, m21, m05 × Sr, GA × 2 nearest + 3 farthest) is complete. Far medians are computed for
   every host with ≥ 1 valid far row; criterion 2 pools near and far values only over hosts with
   valid rows in both shells (excluded hosts are listed). Criterion 1 reports the mean and SD
   parts separately; if it fails, the criterion-2 output carries "inconclusive below the noise
   floor" as PLAN criterion 1 requires.
4. **Production references.** Script 29 gains `--ref-fmax-stages` (references, default 0.02 0.01
   0.005) separate from `--fmax-stages` (doped cells) and `--ref-from` (reuse the pilot's relaxed
   references for the same host). This is how amendment d item 4 ("references always at fmax
   0.005") is executed if the gate adopts a looser depth.
5. **WP2c/2d selection (script 36).** "Closest to the median" is evaluated on distances rounded
   to 10⁻⁶ Å so that exact ties (every shell has an even number of sites) fall through to the
   lower index as amendment f states; floating-point noise had decided 2 of 12 selections.
6. **WP3 E0s.** The fine-tuning E0s are the foundation E0s plus the per-element offsets fitted by
   `scripts/33` (`dataset_meta.json`), so that the fine-tune starts from the zero-shot model that
   criterion 6 compares against. The isolated-atom E0s of `e0_atoms/` (and the WP3 row of the work
   package table) are diagnostic only; the note in `E0_isolated_atoms.json` is superseded.
7. **Corrections to earlier text.** Amendment d: the Cs is one of the four A-sites of the vacancy
   cage (nearest in m21 and m05, second nearest in m30), not "the fourth nearest". WP2A_KPOINTS:
   −TS does not cancel exactly in F(img3) − F(img0) (Δ(−TS) = −10.0 / −6.2 / −3.5 meV for
   Γ / R / 2×2×2); the R-point force deviation is 3.3 / 3.4 meV/Å for images 0 / 3.

## Amendment 2026-10-25h — disclosure correction to g, and follow-up of a second review; written before any WP2c/2d frame, any v2 E_b, or any fine-tuning existed

A second adversarial review (26 agents) checked commit 603693e and amendment g.

1. **Correction of amendment g's header (information state).** The header says the interim WP2b
   numbers "motivate nothing below except item 2". That is wrong for item 1: every band-term value
   it quotes was computed from the interim WP2b outputs (m05 Fermi levels), and when it was written
   the interim analysis already listed m05 Sr as a criterion-3 band crossing (DFT ΔE_a −61.02,
   MACE −30.15 meV; RMS 21.9 meV over 2 pairs), i.e. the quoted −7.3 meV neutral-cell
   contribution exceeds that pair's 1.5 meV margin. To remove any doubt: **criterion 3 is decided
   on the raw neutral-cell ΔE_a exactly as pre-registered; the band-term estimate is reported
   beside it and is never used to reclassify a pair or change the verdict.**
2. **The band term is not exactly site-independent.** Along the WP2b bands the Sr-induced Fermi
   shift changes by 7–10 meV as the vacancy moves (m05: +57.8 → +50.7 meV from image 0 to 6;
   m06: +55.2 → +45.6 meV; GA ≤ 3 meV). Far-referencing (amendment g item 1) removes the
   site-independent part only; criterion 4 keeps its far-referenced 25 meV rule, and for every
   WP2c site the residual is reported as [E_F(D+V) − E_F(V)] − [same at the far site] (q = 0
   outputs), together with the far-referenced q = +1 comparison at m30 (no extra electron). The
   single far site per dopant and host carries its own MACE-vs-DFT error into every far-referenced
   value of that host; this is stated with the result, not corrected.
3. **WP3 targets and criterion 6.** A local potential cannot represent this cell-wide term, so the
   offset fit of `scripts/33` gains two class coordinates, n_Sr·[vacancy] and n_GA·[vacancy]; their
   fitted values are subtracted from REF_energy of the frames that carry them (raw value kept as
   REF_energy_raw). The subtraction is a constant per frame class: forces and every energy
   difference within one band are unchanged. It requires vacancy-free doped frames of a training
   host (the m05 WP2c D_j cells) in the training set; otherwise the fit is rank-deficient and the
   script stops. Criterion 6 compares E_b errors far-referenced (as criterion 4) and ΔE_a errors
   raw (as criterion 3).
4. **Production path for WP1.** If the gate adopts 0.005, production continues in the pilot
   directory (same protocol; all 20 Pb and 19 FA sites). If it adopts a looser depth, production
   runs in a fresh directory with `--fmax-stages` = the adopted list and `--ref-from` the pilot
   (references stay at 0.005), so that the structures handed to WP2c (`scripts/36`) and the E_b of
   the map are from the same stage; `scripts/34` map mode refuses an `--fmax` that is not the run's
   last doped stage. `scripts/29` now defaults `--ref-fmax-stages` to 0.02 0.01 0.005 and refuses
   references looser than 0.005 (amendment g item 4 described this default; the first
   implementation used the doped list; corrected before any production use).
5. **Gate and selection details.** The depth gate uses exactly the pre-registered pilot rows
   (per host and dopant the 2 nearest and 3 farthest sites) and requires the 0.005 stage as its
   reference. GA near is the nearest valid FA whatever its shell, as amendment f states (a pick
   outside the near shell is noted). The WP3 frame generator also refuses to resume when any source
   frame changed (sha256).

## Amendment 2026-10-25i — m21 pilot references hit the FIRE step cap; m21 re-run with a larger cap

The m21 host reference reached the 3000-step cap in the fmax-0.005 stage (0.02 → 0.01: −416 meV
in 1316 steps; 0.01 → 0.005: a further −110 meV in 3000 steps, not converged). Script 29 would stop
with "reference relaxation not converged" after the vacancy reference. m21 was therefore stopped
during its vacancy reference (no m21 E_b existed) and restarted from scratch with
`--steps 10000`, everything else unchanged; the failed log is kept as `shell_m21_steps3000.log`.

The step cap does not change any converged relaxation (FIRE's trajectory does not depend on it),
and every row used must be converged at the evaluated stage, so hosts that differ only in
`steps_per_stage` are treated as one protocol by `scripts/34`; the cap per host is reported. Rows
of m30 and m05 that fail only by reaching the 3000-step cap remain invalid (they are not re-run
with a larger cap unless a further amendment says so before their re-run is read). The pilot
hosts are unchanged (m30, m21, m05).

## Amendment 2026-10-25j — validity at every fmax stage (protocol v2.1); pilot restarted in a new directory

**What was seen (the first pilot row, m30 Sr@136, the only E_b read so far).** E_b = 135.3 / 132.5
meV at fmax 0.02 / 0.01, but in the 0.005 stage the Sr no-vacancy cell ran 1740 FIRE steps and hopped
to another far-field basin (max displacement 0.86 Å, FA rotation 20°, −89 meV), so E_b(0.005) =
209.8 meV and v2 marked the whole row invalid, because v2 checked validity on the final stage only.
Separately, the m05 vacancy reference reached the 3000-step cap in the 0.005 stage (fmax 0.0085) and
m05 stopped; m21 had done the same (amendment i). Deep relaxation on this glassy FA landscape thus
both costs most of the time (Sr@136: 20 + 33 steps to 0.01, 1740 steps to 0.005) and invites the
far-field hops the basin check exists to catch. Applying the v2 gate to final-stage validity would
discard rows whose shallower stages are sound, and would make the gate's reference (0.005)
unavailable exactly where depth matters.

**Change (decided from this one row's validity pattern, before any other E_b).**
1. Protocol v2.1 (`scripts/29`): every check (convergence, basin, vacancy, dopant displacement) is
   made and stored for each stage (row `by_stage`), and the structures of every stage are saved.
   The relaxation itself is unchanged.
2. Depth gate (replaces amendment c item 2 as refined by d, g, h): per-stage validity. The
   reference stage is 0.005 if at least half of the 30 pilot rows are valid at 0.005, otherwise
   0.01 (then only 0.02 is tested). A candidate stage passes if every row valid at both it and the
   reference agrees within 5 meV; the loosest passing stage is adopted, else the reference stage.
   The fraction of rows invalid at each stage (basin hops) is reported as a result.
3. The pilot is restarted in `/data/work/v2pilot2` with protocol v2.1 and `--steps 10000` for all
   three hosts. m30 reuses its converged v2 references (`--ref-from`); m21 reuses the references of
   its amendment-i run once they finish; m05 starts from scratch. The v2 m30 Sr@136 row stays in
   `/data/work/v2pilot` as the record that motivated this amendment and is not used.
4. Recommendation for S2 onwards (not applied here): constrain atoms beyond the basin radius to the
   partner's positions in D_j and D_j+V, which removes far-field hops by construction.

## Amendment 2026-10-27k — WP2e relaxations held after the first one was seen to wander; WP1 gate disclosure

1. **What was seen.** The first WP2e relaxation (m30 GA image 0: fixed-cell BFGS from the MACE
   geometry, R point, nstep 300) had lowered F by 971 meV after 253 BFGS steps (~27 h at 48 ranks)
   and was still descending (~0.4 meV per step; total force 0.0037 Ry/bohr). A descent of ~1 eV is
   far larger than any defect-local relaxation; like the MACE references (0.2–0.6 eV between fmax
   0.02 and 0.005, `WP1_PILOT_RESULT.md`), it indicates that the DFT relaxation wanders over the FA
   orientational landscape. If so, ΔE_relax(dopant) − ΔE_relax(undoped) (amendment c item 5) is
   dominated by far-field wandering and is not interpretable as the single-point bias of ΔE_a.
2. **Decision (operational; no WP2e value other than this one trajectory has been read).** The six
   queued WP2e relaxations (undoped and Sr image 0; the m30 Sr-hinge E_b quartet) are held, not
   cancelled (inputs renamed `*.in.hold`). The GA relaxation runs to its 300-step limit; its
   displacement field (per-atom displacement and FA rotation versus distance from the defects) is
   then analysed. If the energy is carried by far-field atoms, WP2e is reported as uninformative in
   its pre-registered form, and a relaxation with atoms beyond the basin radius frozen to the MACE
   geometry is proposed as a new, explicitly post hoc design; the held relaxations are not run in
   the pre-registered form. If the energy is local, the held relaxations are resumed. Meanwhile cores
   0–47 go to WP2c/WP2d (criterion 4), which do not depend on WP2e.
3. **Consequence for criterion 5's error bar.** Until this is resolved, the WP2b DFT re-statement
   (`WP2B_RESULT.md` §3) stays provisional, as already stated there.
4. **WP1 gate disclosure.** Amendment j changed the depth-gate outcome: under the rule in force
   before j, fmax 0.005 would have been adopted (`WP1_PILOT_RESULT.md`, disclosure section).

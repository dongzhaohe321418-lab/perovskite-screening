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

## Amendment 2026-10-28l — two analysis defects found on the first WP2c run; the WP2e decision of amendment k; written after every WP2c, WP2d and WP2e (GA) value had been read

**Information state.** All 57 WP2c/WP2d single points (48 + 9), the WP2e GA relaxation and its two
partition single points had finished and had been read. Nothing below changes a pre-registered
threshold or decision rule. Items 1–2 are code defects found by inspecting the first output.
Item 3 carries out amendment k item 2 with an analysis that k did not name. Item 4 is a new,
explicitly post hoc design that has not been run.

1. **`scripts/37`, label order in the q = 0 E_b.** The vacancy and host references were passed
   to `eb()` in swapped order, so the q = 0 E_b came out as E_b + 2(F[V] − F[host]) (≈ +911 eV;
   obviously wrong). The error is the same constant for every site of a host, so the far-referenced
   values (criterion 4 and the WP2d rule) were unaffected. The raw E_b, the raw MACE − DFT error and
   the raw far-site values were wrong. The q = +1 E_b used the correct order. Fixed; `eb()` now
   refuses |E_b| > 2 eV. No number from the faulty run is used anywhere.
2. **`scripts/32`, force block.** `parse_qe` read the first force block of an output. For a
   relaxation that is the starting geometry: the GA relaxation's "final" fmax read 0.369 eV/Å
   instead of 0.017 eV/Å. Single points have one force block. Re-running `scripts/32` on the
   archived WP2b outputs after the fix reproduces `wp2b_validation.json` and `wp2b_frames.csv`
   (checked on 2026-10-28). Every value is identical except 12 MACE force RMSEs, which differ by
   ≤ 3 × 10⁻¹⁷ eV/Å (floating-point summation order). It now reads the last block, and both
   scripts read the gzipped archive directly.
3. **WP2e decision (amendment k item 2).**
   - **The partition single points are uninformative.** A cut by atom at 6 Å splits 6 FA
     molecules across the boundary (N–H distorted to 0.89–1.48 Å, C–H to 1.03–1.27 Å). Both
     partitions therefore cost +4.5 and +5.3 eV, with forces up to 9.5 eV/Å: they measure
     distorted bonds, not regions.
   - **Replacement analysis (post hoc).** The work done on each atom along the actual BFGS path,
     W_i = −Σ_k ½(F_i^k + F_i^(k+1))·Δr_i^k (`scripts/38`), has no boundary term. It sums to the
     relaxation energy within 1.2 meV of 977 meV.
   - **What it shows.** Atoms within 6 Å of either defect (organic atoms assigned by their
     molecule's C) are 50 of 234 and carry 19% of the energy (−189 meV). Atoms beyond 6 Å carry
     81% (−787 meV). Per atom this is −3.1 to −5.2 meV in every shell from 0 to beyond 10 Å, and
     the organic sublattice carries most of it. Mean displacement is 0.28–0.39 Å in every shell, and
     10 of the 12 FA that rotate by more than 10° lie beyond 6 Å.
   - **Decision, as amendment k specified.** The relaxation energy is spread over the cell in
     proportion to the number of atoms; it is not concentrated at the defects. WP2e is therefore
     reported as **uninformative in its pre-registered form**, and the six held relaxations are not
     run in that form. Criterion 5's error bar (amendment c item 5) does not exist. Every DFT
     single-point statement keeps its "fixed MACE geometry" qualification, and `WP2B_RESULT.md` §3
     stays provisional.
4. **Proposed post hoc design (WP2e′; not run).**
   - **Relaxation.** Fixed-cell DFT relaxation in which every atom beyond 6 Å of both defect
     centres (molecules assigned by their C) is fixed at its MACE position. The free region is
     identical in all cells of one comparison: the m30 image-0 endpoints of undoped, GA and Sr for
     the ΔE_a bias, and the four cells of the m30 Sr-hinge E_b quartet.
   - **Scheduling.** It ranks below the WP3 DFT single points, which decide criterion 6. Whether
     and when it runs will be recorded in a later amendment, before any of its outputs is read.

**Addendum to l, after the verification review (2026-10-28).** An independent review of commit
7f23c48 against the raw outputs changed no verdict. It found the following, now corrected:
- **Record.** The count of single points (59 → 57) and the partition bond ranges in item 3 above.
- **`scripts/37`, two further post-read changes not listed in items 1–2.** MACE E_b is now
  recomputed from the stored stage energies (asserted equal to `Eb_by_stage`), and rounding is
  applied only at output. No value moved by more than 0.1 meV.
- **`scripts/37`, post hoc diagnostics.** The WP2d diagnostics q0 − q1, ΔE_F(q = 0) and the
  band-term row were also added after the data had been read. They are labelled as post hoc in
  `WP2D_RESULT.md`.
- **`scripts/38`.** Organic molecules are now found by bonding. The FA routine of `scripts/22`
  had left one N and one H of the GA with their own distance; both lie in the 0–4 Å shell, so no
  shell or region total changed. The GA rotation is now given as a rigid-body (Kabsch) angle,
  12.3°, because it has no single C→N axis. The FA axis angles are unchanged.
- **`scripts/32`.** It now refuses a frame label found twice, as `scripts/37` does.
- **Documents.** Wording and last-digit corrections in `WP2C_RESULT.md`, `WP2D_RESULT.md`,
  `WP2E_RESULT.md`, the roadmap and both figures, and a dated note in `WP2B_RESULT.md` that the
  WP2e error bar will not exist.

## Amendment 2026-10-28m — WP3 fine-tuning and criterion 6, fixed before any WP3 DFT single point, any run of the item-2 protocol, or any fine-tuned prediction on a test host exists

**Information state.**
- **Read.** WP1 (pilot and production, including test host m30) and WP2a–2e, so every zero-shot
  error on m30 and m32 is known. Those errors are fixed below as the criterion-6 comparators
  (item 3). The item-1′ hosts have no DFT; only their zero-shot MACE values are known.
- **Exists, MACE only, no DFT.**
  - The m05 smoke-test frames of 2026-10-25 (amendment e item 2).
  - Zero-shot single points along the WP2e path, run during the review of this amendment.
  - Two short zero-shot MD runs of m30 GA image 0 (Langevin, 1.5 ps at 300 K and 450 K, float32,
    snapshots every 100 fs), run during the review in scratch space to check how the
    `scripts/35` MD frames sample the soft FA modes. m30 is a test host; these are MACE-only
    frames, enter no dataset, and no threshold below was set from them. A first set of four
    float64 runs (m30 GA and m05 undoped, 300 K and 450 K) was stopped before writing any frame.
  - A further zero-shot float64 MD run of training host m05 GA image 0 (Langevin, 300 K, 1 fs,
    friction 0.01 fs⁻¹, seed 12345, not a `scripts/35` label seed), stopped after its first report
    at 300 fs. That report was read: mean |Δr| 0.65 Å (inorganic 0.33 Å, organic 0.81 Å); 17 of
    the 19 molecules had rotated their axis by more than 10° from image 0 (median 22.8°, max
    73.1°); E_pot − E_0 = +9.98 eV at an instantaneous 333 K. It wrote no frame, enters no
    dataset, and no threshold below was set from it.
  - The zero-shot MACE ΔE_a of the five item-1′ pairs, known from the corpus
    (`paired_pilot/CORPUS108_RESULT.md`), and the zero-shot MACE E_a of their 10 bands, from the
    stored energies of `../bands` (item 5); their DFT values are not.
- **Exists: exploratory fine-tuning trials on training hosts and m21 only.** Three
  `mace_run_train` 0.3.16 trials of the E0 options were run during the review, on 2026-10-28
  (scratch `e0check/`).
  - **Common settings.** `--foundation_model medium` (by name) with
    `--multiheads_finetuning False`, float64, lr 0.01, weight decay 5e-7, the weighted loss at
    weights 1/100, no EMA, batch size 2, seed 1, `--max_num_epochs 1`.
  - **Data.** Train: the 30 WP2b band frames of m05 and m06, with REF_energy = raw QE F (no E′,
    no c_D). Valid: the 15 m21 band frames.
  - **(1) E0s = foundation E0s plus a 3-column offset fit on those 30 frames.** One epoch (15
    updates) ran and wrote a model. Its records were read:
    - m21 Initial: RMSE_E_per_atom 0.25 meV, RMSE_F 86.35 meV/Å;
    - m21 after epoch 0: 248.01 meV and 159.22 meV/Å;
    - final error table: train 247.3 meV / 154.0 meV/Å, valid 248.0 meV / 159.2 meV/Å.
  - **(2) E0s 'foundation'.** It logged its m21 Initial record (RMSE_E_per_atom 337 335.78 meV,
    RMSE_F 86.35 meV/Å) and four optimiser-step training losses. It was then stopped and wrote no
    model.
  - **(3) E0s = `dataset_meta.json`.** It stopped with a ValueError while loading the E0s, before
    any evaluation.
  - **Use.** No trial model is used anywhere in this amendment. None was evaluated on any frame of
    m30, m32 or an item-1′ host. The trials informed only the E0 rule of item 1c and the start
    check of item 2 (choice 8).
- **Does not exist.**
  - Any WP3 DFT single point, or any DFT for the item-1′ pairs.
  - Any run of the item-2 protocol (the item-1 dataset, the item-1c E0s and targets, the item-2
    w_E and command).
  - Any fine-tuning run that uses a frame of a test host, and any fine-tuned prediction on a test
    host (m30, m32 or an item-1′ host).
  - Apart from the trials above, the only `mace_run_train` runs are option tests and dry runs on
    synthetic few-atom frames (EMT copper, and toy cells of the study elements) without study
    labels.
- **Choices made here with knowledge of the zero-shot values or of test-host DFT.**
  1. RMS as the statistic of criterion 6(ii)–(iii), which criterion 6 does not specify (taken from
     criterion 3).
  2. The band-term-free energy E′ (item 1c). It was introduced after WP2d, and its evidence comes
     from test host m30. With it, criterion 6(ii) gains a second, conjunctive condition on E′
     (item 3). That condition leaves the raw condition of (ii) with the headroom stated in
     item 3(ii).
  3. The WP3b design (item 4), chosen after WP2e.
  4. The class constants c_Sr and c_GA, taken from the m05 far-site quartets.
  5. The q = +1 check of item 1c: its eight frames, its test on differences of v, and its 10 meV
     tolerance. They were chosen after the nine m30 WP2d values had been read (mean −51.25 meV,
     SD 2.33, range 7.98 meV; paired along-band value −3.32 meV). Its outcome selects the energy
     basis of training, of criterion 6(ii) and of adoption (b).
  6. The bases of the energy conditions: criterion 6(ii) on raw F and on E′, both required
     (item 3), and adoption (b) on E′ alone, DFT classes included. Both were chosen knowing the
     zero-shot 4-pair RMS (raw 23.647 meV, E′ 38.191 meV). They were also chosen knowing that a
     model equal to the E′ DFT values scores 20.45 meV on raw F over those pairs, so it would fail
     RMS < 20 meV on raw F.
  7. The extension of adoption (b) to the five item-1′ pairs. Their zero-shot ΔE_a are known
     (GA m10 +66.5, m18 −30.1; Sr m04 −7.4, m14 −139.8, m27 +11.8 meV; m10 and m14 lie outside
     ±59.5 meV), and their DFT is not. All five admissible pairs without DFT are taken, so none was
     selected.
  8. The single E0 option of item 1c and the start-check values of item 2. Both were set after the
     exploratory trials above (training hosts and m21 only).

  The acceptance thresholds are inherited:
  - criterion 6 and adoption (b)–(c): RMS < 20 meV, ±59.5 meV and 25 meV, from criteria 3–4;
  - (d): 0.05 / 0.2 eV/Å, from criterion 5.

  The failure bounds of (d) are taken from `scripts/29` (1.2 Å, 1.0 Å), and its topology check
  from `scripts/35`; (e) uses the `scripts/35` bounds (0.65 Å, 15 eV/Å). The WP3b relaxation
  settings (fmax 0.01 eV/Å, at most 10 000 steps) are those of protocol v2.1 (item 6). The 6.0 Å
  radius comes from amendment l item 4, and the 60-frame minimum from amendment c item 7.

  Chosen here:
  - the 10 meV tolerance of the item-1c check (choice 5);
  - the start-check tolerances of item 2 (±0.01 meV/Å on RMSE_F, ±0.001 meV/atom on
    RMSE_E_per_atom) and the reproduction-gate tolerances of item 3 (10⁻⁶ eV, 0.001 meV);
  - the 5 ps MD length of (e) and its inorganic check (I–I 3.0 Å; dopant site).
- **How the values here were computed.** On 2026-10-28, from the archived outputs, with
  mace-torch 0.3.16, MACE-MP-0 medium and float64 (`../venv`). The recomputed MACE energies equal
  `wp2b_validation.json` exactly. They equal the final-stage WP1 energies (top-level `E_eV`) of the
  16 m30 WP2c structures to within 3 × 10⁻¹⁰ eV (largest 2.2 × 10⁻¹⁰ eV, m30_GA128_vac). The
  residual comes from the `_relaxed` files storing positions to 10⁻⁸ Å and is the same at 1 and 4
  threads; the reproduction gate is 10⁻⁶ eV.
- **Split** (amendment e item 1). Train and validation are unchanged; the test set is extended by
  item 1′.

1. **Data.**
   - **1a. Split.**
     - **Train** (m05, m06, m08, m12, m15, m20):
       - the WP2b band frames (90);
       - the m05 WP2c frames (16), which are the only within-host E_b quartets and the source of
         c_Sr and c_GA;
       - the WP3 off-equilibrium frames of `scripts/35` (at most 96; item 1d).
     - **Validation** (m21): the band frames (15) and the WP2c frames (16).
     - **Test.** As in amendment e: the m30/m32 band frames (30) and the m30 WP2c frames (16). The
       item-1′ frames (50) are added.
   - **1′. Additional test pairs (fixed now; no DFT for them exists).**
     - **Pairs.** The five admissible corpus pairs that have no DFT (`paired_pilot/CORPUS108_RESULT.md`
       §4; `WP2B_RESULT.md` §3): GA m10 and m18; Sr m04, m14 and m27.
     - **Single points.** `scripts/30` at the WP2b settings, on images 0, 2, 3, 4 and 6 of the
       undoped and dopant bands in `../bands` (7-image bands, MACE saddle at image 3): 50 frames.
       - Each is run with `--label <host>_<system>_img<k>`, the band pattern of item 1b, where
         `<system>` is `undoped` or the pair's dopant (for example `m10_GA_img3`). `scripts/30`
         requires `--label` and has no default.
       - The inputs and outputs are archived as `wp3/test_extra/raw/<label>.{in,out}.gz`, below
         `--dft`, so `scripts/33` and `scripts/39` find them.
     - **Isolation.** These hosts are test only, and no other frame of them is used anywhere.
     - **Completeness** follows amendment g item 2.
       - A job that stops without JOB DONE is resubmitted with the identical input, as in item 1d.
         A job the queue gives up on (`<label>.gaveup`) is incomplete.
       - An SCF that does not converge is re-run once with identical settings.
       - If any of the 9 test pairs is then incomplete, adoption (b) is not met.
     - **No re-decision.** These pairs change neither the criterion-3 verdict nor `WP2B_RESULT.md`
       §3. Any DFT re-statement over 11 or 12 pairs is reported separately and labelled post hoc.
     - **Caution for re-runs of WP2b.** `scripts/32` pools every complete pair below `--dft`, so any
       WP2b re-run uses `--dft wp2b/raw` only.
   - **1b. Inclusion rule (replaces the label exclusion of amendment f).** An output enters the
     dataset only if two conditions hold: its label matches one of the three anchored patterns of
     `scripts/33`, and it converged with a force block. The patterns are:
     - band: `mNN_<undoped|GA|Sr>_img<k>`;
     - WP2c: `mNN_host`, `mNN_vac` and `mNN_<Sr|GA><j>_<novac|vac>`;
     - WP3: `mNN_<undoped|GA|Sr|pristine>_<rat05f|rat10f|md300|md450>`.

     On 2026-10-28 the archive held 211 outputs: 135 band, 48 WP2c and 28 excluded. The excluded
     ones are the 9 `*_q1`, `relax_m30_GA_img0`, 2 `part_*`, 3 `set_*`, 6 `kconv_*` and 7 `atom_*`.
     Of the outputs written later, only two groups carry a label that matches a pattern: the WP3
     frames (labels set by `scripts/35`, WP3 pattern) and the 50 item-1′ frames (band pattern).
     Every other later output gets a label that matches no pattern: `chk_*` (q = +1 checks),
     `wp3b_*` and `wp3bu_*` (WP3b), and WP2e′.
   - **1c. Targets (`scripts/33`; replaces the fitted band-term class coordinates of amendment h
     item 3).**
     - **Why.**
       - With six composition classes and six coordinates, the class fit is saturated. Each
         coefficient is a double difference of class-mean zero-shot errors, not the band term.
       - On the existing training frames it gives +19.5 meV (Sr+V) and −33.1 meV (GA+V). The mean
         dopant Fermi shift on the training bands is +47.0 meV (SD 9.7) and +15.8 meV (SD 2.6).
       - Nearly every D+V training frame is a band or WP3 frame, built with the dopant on the site
         nearest the vacancy. The coefficient therefore absorbs the near-shell binding error that
         criterion 6(iii) tests.
       - Once WP3 frames are included, it would also absorb about 0.94 × their mean
         off-equilibrium error.
       - A constant per class also leaves the along-band band term in the targets (m15 Sr:
         −40.8 meV from image 0 to image 3). A local model could learn that term only as a spurious
         Sr–I interaction.
     - **E′ for vacancy cells.**
       - **Rule.** Every frame with the vacancy (59 I, odd electron count), in every split, gets
         REF_energy = F − (E_F − E_F,ref).
         - E_F is the last "the Fermi energy is" value of that output, parsed as in
           `scripts/37 qe()`. `scripts/32 parse_qe` does not return E_F, so the changed
           `scripts/33 collect()` adds this parse for every frame and stores it as REF_EF.
         - E_F,ref = 3.3447 eV, the median E_F of the 30 training undoped band frames. It is a
           constant, absorbed by the offset fit.
       - **Other frames.** Vacancy-free frames keep F. Raw F is kept as REF_energy_raw, and E_F as
         REF_EF.
       - **Basis.** On the 9 m30 frames computed at both charges (WP2d),
         F(q = 0) − E_F(q = 0) − F(q = +1) is −51.25 meV (SD 2.33; range −56.42 to −48.44 meV). E′
         therefore follows the V_I⁺ energy frame by frame.
       - **Forces.** These stay the q = 0 forces. Their mismatch with −∇E′ is ∇E_F. Because E′
         follows F(q = +1) up to a constant (Basis), this is approximately the force difference
         f(q = 0) − f(q = +1), which WP2d gives on the 9 m30 frames:
         - component RMS 0.0065–0.0098 eV/Å, 7.5–11% of the zero-shot test-frame force RMSE of
           comparator (i) (0.086809 eV/Å);
         - per-atom maximum 0.052–0.079 eV/Å, in every frame on one of the two Pb that flank the
           vacancy (6.5 Å apart at image 0);
         - 0.006–0.036 eV/Å on the migrating iodide.
     - **Class constants (fixed now).**
       - **Definition.** c_D = E′_b(DFT) − E_b(MACE-MP-0) at the m05 far site (Sr112, GA4). This
         gives c_Sr = −2.174 meV and c_GA = −18.851 meV.
       - **Use.** c_D is subtracted from REF_energy of every Sr+V or GA+V frame, in every split.
       - **Purpose.** On E′ it removes the site-independent offset that a local model cannot
         carry. On the raw fallback it also removes the far site's own band term (see the
         raw-basis consequence below).
       - **Caveats.** Each is anchored on a single site. The same quantity at the m21 and m30 far
         sites is −15.727 and −32.184 meV for GA, and −5.896 and −12.708 meV for Sr. These differ
         from the m05 anchor by up to 13.3 meV (GA) and 10.5 meV (Sr). The MACE GA far-site SD of
         28 meV is the spread of E_b itself, which DFT shares at fixed geometry (raw MACE − DFT is
         +2.5 and −0.3 meV at the atypical m05 and m21 GA4 references), so it is not the error of
         c_D. Both constants cancel in every within-band ΔE_a and every far-referenced E_b.
     - **Per-element offsets.**
       - **Fit.** Least squares of REF_energy (after E′ and c_D) − E(MACE-MP-0) over the training
         frames of config_type `band_*` and `binding` only: 106 frames, rank 4 through the m05 host
         and D_j cells.
       - **Columns.** Four columns (const, dI, dN, nSr), assigned to I, N, Pb and Sr as now.
       - **WP3 frames** are trained on but stay out of the fit. They cover only the host, V, Sr+V
         and GA+V classes, so their mean error would shift the offsets.
       - **E0s.** The foundation E0s plus these offsets (amendment g item 6), written as a flat
         {Z: eV} map to `E0s.json`. No other E0 option is used ('foundation', 'average',
         'estimated', or the isolated-atom E0s of `e0_atoms/`).
     - **Check before training.** Eight single points at q = +1 (`scripts/30 --charge 1`, labels
       `chk_<frame label>_q1`):
       - m15 Sr and m15 undoped, images 0 and 3 (the training hinge-Sr band and its undoped band);
       - m05 Sr and m05 undoped, image 0 and md450 (md300 if the md450 frame was rejected).

       For each frame, v = F(q = 0) − E_F(q = 0) − F(q = +1). A host-wide constant in v cancels in
       every within-band ΔE_a and every far-referenced E_b, so only differences of v are tested:
       - **(a) Band test.** |[v(m15 Sr img3) − v(m15 Sr img0)] − [v(m15 undoped img3) −
         v(m15 undoped img0)]| < 10 meV. At m30 this paired value is −3.32 meV.
       - **(b) WP3 test.** |v(m05 X md450) − v(m05 X img0)| < 10 meV, for X = Sr and for
         X = undoped (md300 where it replaces md450).

       An unconverged SCF, or a job abandoned without JOB DONE (item 1d), fails the test it enters.
       The eight v values, their differences and their distance from the m30 mean (−51.25 meV) are
       written to `dataset_meta.json` before training. No decision rests on the distance from the
       m30 mean.
       - **(a) passes:** the E′ basis is used, for the band and binding frames at least.
         - If (b) passes for both X, E′ is used for the WP3 vacancy frames too.
         - Otherwise those frames carry `config_energy_weight = 0`, and their forces are kept.
       - **(a) fails: raw basis throughout** ((b) is then not used):
         - REF_energy = F;
         - c_Sr = +55.826 meV and c_GA = −2.451 meV (the m05 far quartet on raw F);
         - criterion 6(ii) and adoption (b) are evaluated on raw F only.
       - **Known consequence of the raw basis (disclosed now; not corrected).** On raw F a constant
         per class cannot remove the band term, which varies between sites and hosts.
         - The anchor site m05 Sr112 has ΔE_F = +58.0 meV. The other m05 Sr sites have +41.7
           (hinge), +45.4 (flank) and +44.0 meV (mid). The 30 training Sr band frames average
           +46.95 meV (SD 9.65).
         - Measured from the far anchor, the raw Sr+V targets therefore carry a band offset of
           −16.3 meV (m05 hinge), −12.6 meV (flank) and −14.0 meV (mid). The band and WP3 frames
           carry −11.0 meV on average, through c_Sr.
         - A local model can learn this only as a spurious near-shell Sr–V attraction. At the m30
           test sites the same residual is −0.4 (Sr136) and −2.6 meV (Sr124).
         - Under the fallback, a model that fits its targets is therefore expected to
           under-predict the far-referenced raw E_b at the m30 Sr hinge and flank by about
           8–16 meV. This expectation is printed with the (iii) and (c) results and with the
           item-5 power statement for (c), which assumes zero-mean errors. It changes no verdict.
         - On E′ it does not arise, because each frame's own ΔE_F is removed.
     - **Diagnostics in `dataset_meta.json`** (no decision rests on them):
       - the saturated six-column coefficients;
       - the mean ΔE_F per dopant;
       - the m05 far-site raw and E′ errors;
       - the mean and SD of the WP3-frame residuals per host and kind, which estimate the
         off-equilibrium offset;
       - the residual RMS per class;
       - the E_F spread of the WP3 frames.
   - **1d. WP3 frames and shortfall.**
     - **Generation.** `scripts/35 --hosts 05 06 08 12 15 20`, with the defaults (1500 MD steps,
       15 eV/Å bound).
     - **Rejected frames.** A frame rejected by the checks is not regenerated; its seed is fixed by
       its label.
     - **Failed jobs.** A QE job without JOB DONE is resubmitted once with the identical input
       (`ehpc/node/qe_queue.sh`, which renames the failed output `<label>.out.try1`). If the retry
       also ends without JOB DONE, the queue writes `<label>.gaveup` and leaves no `<label>.out`;
       that frame is dropped. A frame whose SCF does not converge is dropped.
     - **Listing.** Rejected and dropped frames are listed.
     - **Minimum.** Training proceeds if at least 60 WP3 frames remain (amendment c item 7).
       Otherwise a further amendment is written before any training.
   - **1e. Invocation and counts.**
     - **Archiving.** Before `scripts/33` runs:
       - the `scripts/35` frames and `frames_report.json` go to `wp3/frames/`;
       - the WP3 QE inputs and outputs go to `wp3/raw/<label>.{in,out}.gz`;
       - the queue's `<label>.out.tryN` files and `<label>.gaveup` markers are copied under the
         same names to `wp3/raw/` and `wp3/test_extra/raw/`, gzipped where they are text. Their
         names match no glob of `scripts/32`, `33` or `37`, so no label occurs twice;
       - `v2prod_structures.tar.gz` is extracted to a scratch directory `<x>`.
     - **Command.** It is run once, from the repository root, without `--allow-missing`. A host
       that is not listed defaults to train.

       `python scripts/33_finetune_dataset.py --dft results/objective2/dopant_shell --frames ../bands <x>/v2prod results/objective2/dopant_shell/wp3/frames --out results/objective2/dopant_shell/wp3/dataset --test-hosts m30 m32 m04 m10 m14 m18 m27 --valid-hosts m21`

       An item-1′ host with no converged frame is left out of `--test-hosts`.
     - **Expected counts.** `scripts/33` stops unless it finds exactly:
       - train: 90 band + 16 binding (m05) + W WP3 frames, all from the six training hosts. W is
         the number of records with ok = true in `wp3/frames/frames_report.json`, minus the
         dropped frames;
       - valid: 15 + 16 (m21);
       - test: 30 band (m30, m32) + 16 binding (m30), plus the item-1′ frames found (any missing
         frame is listed by its expected label `<host>_<system>_img<k>` and decides (b) as item 1′
         states);
       - no rattle or md frame outside train.

       `scripts/33` reads `frames_report.json`. It stops if a record with ok = true has neither
       `wp3/raw/<label>.out.gz` nor `wp3/raw/<label>.gaveup`, or if a WP3-pattern output has no
       record with ok = true. Every output that matches a pattern but is skipped is listed with its
       reason: gave up, no JOB DONE, SCF not converged, or no force block. The 50 item-1′ labels
       are enumerated in `scripts/33`. Every output whose label matches no pattern is also listed
       in `dataset_meta.json`. `scripts/33` stops if such a label is neither one of the 28
       exclusions named in item 1b nor a `chk_*` label.
2. **Training (fixed now; not tuned on any held-out host).**
   - **Version and starting model.**
     - **Version.** mace-torch 0.3.16, the version whose code was checked. The log must show
       "MACE version: 0.3.16". The torch and e3nn versions are recorded.
     - **Foundation model.** The file that `mace_mp(model="medium")` loads zero-shot:
       2023-12-03-mace-128-L1_epoch-199, cached as `20231203mace128L1_epoch199model`, sha256
       01bfe22100139f424713cf921144e5509cbe353d67aa9fa1be9c6e1e0ed35845. It is passed by path, and
       the node copy must have this hash.
     - **Naive single-head fine-tuning,** hence the path and `--multiheads_finetuning False`. In
       0.3.16, giving the name `medium` switches on multihead replay fine-tuning. That mode sets
       lr 1e-4, EMA decay 0.99999 and the Huber "universal" loss, and it downloads MPtrj replay
       data.
     - **Inherited settings.** r_max (6 Å), avg_num_neighbors and scale/shift come from the
       foundation model. The element table is that of the data (H, C, N, Sr, I, Cs, Pb), by the
       default element filtering.
   - **Loss weights (rule fixed now; value from training frames only).**
     - **Problem.** MACE's `weighted` loss uses ((E − E_ref)/N)² per frame and the force MSE per
       component. At weights 1/100, the energy term is 1/(1 + w_E) ≈ 1.5 × 10⁻⁷ of the starting
       loss on the 106 existing training frames with the item-1c targets (1.6 × 10⁻⁷ on raw F), in
       these 233-atom cells. The energy differences of criterion 6(ii)–(iii) would then enter
       neither the fit nor the selection.
     - **Rule.** w_F = 100 and w_E = w_F · L_F / L_E, to two significant figures.
       - L_F is the zero-shot force MSE per component over all atoms of all n_train training
         frames. Every training frame has force weight 1.
       - L_E = (1/n_train) · Σ_i e_i · ((E_ref,i − E_i)/N_i)², summed over all n_train training
         frames, with the E0s and targets of item 1c. Here e_i is the frame's
         config_energy_weight: 1, or 0 for the WP3 vacancy frames in the item-1c branch where (a)
         passes and (b) fails. Equivalently, L_E = (n_E/n_train) × the mean over the n_E frames
         with e_i = 1.
       - This is how mace-torch 0.3.16 averages the energy term. `weighted_mean_squared_error_energy`
         multiplies by `ref.energy_weight`, and `reduce_loss` takes the mean over every graph of a
         batch, zero-weight graphs included (`mace/modules/loss.py`, lines 23–43 and 58–68;
         `config_energy_weight` is read at `mace/data/utils.py` line 195). With all 96 WP3 frames
         written and the 72 vacancy frames at e_i = 0, n_E/n_train = 130/202.

       The two terms are therefore equal at the start of training, averaged over the training set,
       in every branch of item 1c.
     - **Recording.** `scripts/33` writes L_F, L_E, n_train, n_E, N̄ and w_E to `dataset_meta.json`
       before training. On the 106 existing training frames, all with e_i = 1,
       L_F = 8.36 × 10⁻³ (eV/Å)² and L_E = 1.25 × 10⁻⁷ (eV/atom)², so w_E ≈ 6.7 × 10⁶ on the E′
       basis. Under the raw-basis fallback of item 1c it would be 6.1 × 10⁶
       (L_E = 1.36 × 10⁻⁷ (eV/atom)²). These values are indicative; the value used is the one
       `scripts/33` writes after the q = +1 check.
     - **No stage two (SWA).** The retry does not change w_E.
   - **Command (fixed now).** Paths are absolute, and `<run>` is an empty directory.

     `mace_run_train --name wp3 --seed 123 --work_dir <run> --device cpu --default_dtype float64 --foundation_model <path>/20231203mace128L1_epoch199model --multiheads_finetuning False --train_file <ds>/train.xyz --valid_file <ds>/valid.xyz --E0s <ds>/E0s.json --energy_key REF_energy --forces_key REF_forces --loss weighted --energy_weight <w_E> --forces_weight 100 --optimizer adam --amsgrad --lr 0.005 --weight_decay 5e-7 --clip_grad 10 --scheduler ReduceLROnPlateau --lr_factor 0.8 --scheduler_patience 50 --ema --ema_decay 0.99 --batch_size 2 --valid_batch_size 2 --max_num_epochs 100 --patience 2048 --eval_interval 1 --keep_checkpoints`

     - **Not used:** `--test_file`, `--test_dir`, `--valid_fraction`, `--pt_train_file`,
       `--force_mh_ft_lr`, `--swa`, `--restart_latest`, `--save_all_checkpoints`, LoRA and
       freezing.
     - Every other option stays at its 0.3.16 default.
   - **Pre-flight (a configuration check, not a training run).** The command is run with
     `--dry_run` in a separate directory. Its INFO log must contain each of these:
     - "MACE version: 0.3.16"
     - "Using foundation model <path> as initial checkpoint."
     - "Using heads: ['Default']"
     - "Using filtered elements: …" listing Z = 1, 6, 7, 38, 53, 55, 82
     - "Atomic Energies used (z: eV) for head Default: …", equal to `E0s.json`
     - "Using weighted loss function for fine-tuning"
     - "Using Exponential Moving Average with decay: 0.99"
     - "Learning rate: 0.005, weight decay: 5e-07"
     - "WeightedEnergyForcesLoss(energy_weight=<w_E>, forces_weight=100.000)"

     It must contain no line with "multiheads finetuning". The `Configuration:` dump of the debug
     log is written before these overrides apply, so it is not used. If a check fails, the cause
     is recorded and corrected and the pre-flight is repeated; nothing is trained.
   - **Start check.** It uses the "Initial" validation record (results file, `"epoch": null`),
     which is made before any optimiser step.
     - RMSE_F must be 79.819 ± 0.01 meV/Å: the zero-shot value pooled over all components of the
       31 m21 frames, computed on 2026-10-28.
     - RMSE_E_per_atom must be 0.3334 ± 0.001 meV/atom, or 0.3499 ± 0.001 meV/atom under the
       raw-basis fallback of item 1c (unrounded 0.333420 and 0.349936 meV/atom).
       - These are the zero-shot values on the 31 m21 frames with the `E0s.json` offsets and the
         item-1c targets, computed on 2026-10-28.
       - They are fixed now. The offsets use only the 106 band and binding training frames, and
         c_D and E_F,ref are constants, so no WP3 frame changes them.
       - A wrong E0 option gives 0.442 eV/atom ('average'), 2.93 eV/atom (the isolated-atom E0s
         of `e0_atoms/`) or 337 eV/atom ('foundation').
       - Valid targets built without E′, without c_D, or from raw F give 0.3258, 0.3513 and
         0.3408 meV/atom.
       - 'estimated' cannot be told apart by this check; the pre-flight "Atomic Energies used" line
         catches it.

     If either fails, the run is stopped, its outputs are not used, and the cause is recorded and
     corrected. This does not use the retry.
   - **Corrections.** At the pre-flight and the start check, a correction may only bring the
     command, files or environment into agreement with this amendment. Any other change is a
     further amendment, written before training.
   - **Threads and cost.**
     - **Single process.** mace-torch 0.3.16 has no CPU data-parallel backend.
     - **Thread count.** It is fixed by a 2-epoch timing run at OMP_NUM_THREADS 8, 16 and 32, in a
       separate directory with `--max_num_epochs 2`. Only wall time is read, and the outputs are
       then deleted.
     - **Precision.** float64 is kept: float32 spacing at the −8 × 10⁴ eV totals is 7.8 meV.
     - **Expected time.** 8–15 min per epoch, so about 13–25 h for 100 epochs.
   - **Model selection and stopping.**
     - **No early stopping.** In a single-process 0.3.16 run, patience only writes to the log, and
       `--patience 2048` silences even that. All 100 epochs run.
     - **Checkpoints.** One (EMA weights) is written only when the m21 validation loss improves
       (same loss and weights as training), and `--keep_checkpoints` deletes none.
     - **The model.** `<run>/wp3.model`, which `mace_run_train` writes from the highest-epoch
       checkpoint. That checkpoint is the epoch with the lowest validation loss.
     - **Never the starting model.** The first epoch always counts as an improvement, because the
       Initial evaluation does not set the reference.
     - **Reporting.** Reported side by side: the selected epoch with its m21 loss,
       RMSE_E_per_atom and RMSE_F; the Initial values; and the m21 host-wide energy offset.
     - A model worse than Initial on m21 is reported as such and is still evaluated.
   - **Interruptions.**
     - **Why no restart.** `--restart_latest` is not used. In 0.3.16 it resumes from the last
       improved checkpoint, starts a new EMA and resets the best-loss record.
     - **Rule.** A run stopped by a spot reclaim, node loss, OOM or wall time is discarded unread.
       The identical command is run from scratch in a new, empty `<run>`.
     - **Other abnormal ends.** A run that ends before `<run>/wp3.model` is written for any other
       reason (a Python exception, a kill signal, a non-zero exit) is handled in the same way. It
       is discarded unread, its cause and traceback are listed, and the identical command is run
       from scratch in a new, empty `<run>`.
     - **Deterministic causes.** If the identical command ends with the same cause twice in
       succession (the same exception, or OOM or wall time again; never a spot reclaim or node
       loss), the cause is deterministic, and the run counts as a technical failure.
     - **Model written, then abnormal exit.** A run that exits abnormally after `wp3.model` is
       written is judged from the log, as below.
     - **Not the retry.** Such a restart may be repeated, and each one is listed with its cause and
       time.
     - **Keep-alive.** `/data/KEEP_ALIVE` stays present throughout, so the idle cron does not power
       the node off.
   - **Technical failure.** It is decided from the training log, the results file and m21 only,
     before any test-host prediction.
     - **What counts.** Only three things: a non-finite training or validation loss at any epoch;
       a non-finite energy or force of the selected model on any m21 frame; or a deterministic
       abnormal end (under Interruptions).
     - **Checked from the log, not the exit status.** In 0.3.16, `valid_loss >= lowest_loss` is
       False for NaN, so a NaN epoch is saved as the best and the run ends normally.
     - **Not a failure.** A finite but poor or rising loss.
     - **The one retry.** The cause is recorded, and the run is repeated once from MACE-MP-0 with
       `--lr 0.0025`, in a new empty `<run>`, with nothing else changed. Its log must show
       "Learning rate: 0.0025, weight decay: 5e-07".
     - **If the retry also fails** (in any of these three ways), criterion 6 is "not met (no
       fine-tuned model)".
     - **Never evaluated.** A failed run, or a void one (stopped at the pre-flight or the start
       check), is never evaluated on a test host.
   - **Record and model hash.**
     - **Archived with the model:** the command, logs, results file, versions, seed, thread count,
       restarts and selected epoch.
     - **Before any test-host prediction** (criterion 6, WP3b or MD), a dated note in `wp3/` is
       committed. It records the sha256 of `wp3.model` and the commit of `scripts/39`, `40` and
       `41`.
     - This amendment is not edited.
3. **Criterion 6, evaluated once on the test hosts** (as amended by h item 3, with one condition
   added here: (ii) on E′), against zero-shot MACE-MP-0 on the same frames.
   - **(i) Force RMSE.** Pooled per component over all atoms of the 46 frames of amendment e:
     sqrt(Σ|F_model − F_DFT|² / Σ 3N).
   - **(ii) Paired ΔE_a error.**
     - **Definition.** The RMS of model − DFT over the 4 m30/m32 pairs, with E_a as in criterion 3
       (`scripts/32`: the maximum over images 2–4 of E_i − E_0 on the fixed MACE path).
     - **Bases.** It is evaluated on raw F, as h item 3 requires, and also on E′.
     - **Why E′ is added.**
       - The training targets now exclude the band term.
       - In the hinge-Sr test pair m30 Sr, the band term is −39.7 meV, so a gain on raw F alone
         could come from learning the finite-cell term.
       - A model equal to the E′ DFT values scores 20.45 meV on raw F, only 3.2 meV below the
         zero-shot 23.647 meV.
     - **Headroom of the raw condition.** For a model trained on E′, the raw condition is the
       tighter one.
       - Let d = E′(DFT) − raw(DFT) ΔE_a = (−0.6, +39.7, +1.7, +9.7) meV for m30 GA, m30 Sr,
         m32 GA and m32 Sr, and let e be the model's E′ errors. Its raw errors are e + d.
       - Raw passes only if mean(e²) + 2·mean(e·d) < 140.8 meV². That is an RMS budget of
         11.9 meV for errors uncorrelated with d, against 38.2 meV on E′.
       - With the other three pairs exact, the m30 Sr E′ error must lie between −86.0 and
         +6.6 meV. Overshoot away from the band term is penalised, and undershoot towards it is
         not. For example, E′ errors of (0, +10, 0, 0) meV (E′ RMS 5.0 meV) give 25.3 meV on raw F
         and fail.
       - Raw stays decisive because h item 3 pre-registered it and roadmap update 2026-10-27,
         consequence 1, requires criterion 6. E′ is not made the sole basis, which would pick the
         easier comparator with the zero-shot values known. Item 5 gives the pass probabilities.
   - **(iii) Far-referenced E_b error.** Far-referenced as in criterion 4 (amendment g item 1), on
     raw F. The statistic is the RMS over the 5 non-far m30 sites; it is not a criterion-4 rule. The
     residual band term at these sites is at most 4.2 meV, so no E′ condition is added. The
     E′-based values are reported.
   - **Verdict.** "Improvement" only if (i), (ii) on both bases and (iii) are all strictly below
     the zero-shot values.
     - The E′ condition on (ii) is added by this amendment, after the zero-shot values were read.
       It makes criterion 6 stricter than h item 3, which compares ΔE_a on raw F only; it never
       makes the verdict looser.
     - The verdict under h item 3 alone ((i), (ii) on raw F, (iii)) is reported beside it, labelled
       "criterion 6 as amended by h".
     - Adoption (a) uses the verdict of this item.
     - Under the raw-basis fallback of item 1c, (ii) is evaluated on raw F only, and the two
       verdicts coincide.
   - **Zero-shot comparators (fixed now; meV unless stated):**
     - **(i)** 0.086809 eV/Å: 0.088867 on the 30 band frames and 0.082823 on the 16 WP2c frames.
     - **(ii), raw.** m30 GA −22.241, m30 Sr −29.782, m32 GA −16.394, m32 Sr +24.215; RMS 23.647.
       m32 GA changes class (0 → −1).
     - **(ii), E′.** −21.641, −69.482, −18.094, +14.515; RMS 38.191. m32 GA changes class.
     - **(iii).** Sr136 −6.403, Sr124 +14.084, Sr52 −3.838, GA128 −60.043, GA212 −13.306;
       RMS 28.412.
       - By dopant (reported, not gated): Sr 9.203, GA 43.487.
       - GA128 carries 89.3% of the sum of squares (reported, not gated).
       - The GA near-shell sign disagrees.
   - **Computation.** By `scripts/39_wp3_evaluate.py`, committed before training.
     - **Both arms in one invocation:** float64, CPU, one mace-torch installation.
       - Zero-shot: `mace_mp(model="medium", device="cpu", default_dtype="float64")`, the call of
         `scripts/32` and `scripts/37`. In 0.3.16 its defaults are float32 and device "" (CUDA
         when available).
       - Fine-tuned: `MACECalculator(model_paths=<wp3.model>, device="cpu", default_dtype="float64", head="Default")`,
         with its sha256 checked.
       - The script asserts float64 for both arms before any frame is evaluated.
     - **Single points only,** at the geometries DFT was run on:
       - the band images of `../bands`;
       - the `_relaxed` WP2c structures of `v2prod_structures.tar.gz`, with labels from
         `wp2cde_selection.json`.

       Cell and positions must equal the CELL_PARAMETERS and ATOMIC_POSITIONS of the archived QE
       input `<label>.in.gz` to within 10⁻⁶ Å. This check runs at step 1 on the 46 m30/m32 frames,
       and at step 6 on all 96 test frames. At step 6, the set of labels evaluated must also equal
       the set of labels in `test.xyz`. No relaxation or NEB enters criterion 6 or adoption
       (b)–(c).
     - **DFT values.** F and forces are read with `scripts/32 parse_qe` (last force block). E_F is
       the last "the Fermi energy is" value of the same output, parsed as in `scripts/37 qe()`
       (regex `the Fermi energy is\s+([-\d.]+)\s+ev`, last match). None of them is read from
       REF_energy.
     - **Code reused.** E_a, pairing and `band_class` as in `scripts/32`. The `eb()` order, the far
       sites (Pb64, FA152) and the near-sign rule as in `scripts/37`.
     - **Reproduction gate.** At every invocation the zero-shot arm runs first and must reproduce:
       - frame energies to within 10⁻⁶ eV:
         - the 30 m30/m32 band frames against `E_mace` in `wp2b/wp2b_validation.json`;
         - the 16 m30 WP2c frames against the final-stage energies in `shell_m30.json`, the stage
           at which each `_relaxed` structure was written: the top-level `E_eV` of `E_host` and
           `E_vac` (0.005 eV/Å stage), and the `doped_fmax_final` (0.01 eV/Å) stage of each row's
           `no_vac` and `with_vac`, as in `scripts/37 mace_eb`;
         - the 50 item-1′ band images against the `energy` field of
           `../bands/band_<system>_<host>.extxyz` (geometries from `../bands`; no QE output is
           parsed for this);
       - to within 0.001 meV (10⁻⁶ eV/Å for (i)): the (i) value and its band and WP2c parts, the 4
         raw and 4 E′ pair errors and their two RMS values, and the 5 site errors and their RMS;
       - exactly: the two class changes and the GA near-sign statement.

       The per-dopant RMS and the GA128 share are reported, not gated. No item-1′ QE output is
       parsed, and the fine-tuned model is not loaded, until this gate has passed. On a failure the
       script stops after printing only the gate diagnostics.
     - **Check at commit (step 1).** The script is run in a gate-only mode. `test.xyz` and the
       item-1′ outputs do not yet exist and are not read.
     - **Failure at step 6.** The cause is recorded. Any change to `scripts/39` is committed, and
       its diff is listed in the WP3 result. The step-1 check is repeated, and then step 6 is run
       again. Because no item-1′ or fine-tuned value has been read, this re-run is not a second
       evaluation and is not an outcome under item 4.
     - **Output.** Unrounded values go to `wp3/wp3_eval.json`.
     - **Raw E_b.** The fine-tuned raw E_b is never reported as an error, because its targets
       exclude the band term and c_D.
   - **Reported beside the verdict** (no decision rests on these):
     - (i) over all 96 test frames;
     - (ii) over all 9 test pairs, on both bases;
     - (iii) per dopant, on E′, and raw;
     - the absolute E_a error (model − DFT, E_a as in (ii), on raw F and on E′) of all 16 test
       bands (6 m30/m32, 10 item-1′), for both models;
     - every per-frame, per-pair and per-site error for both models, with the number of items that
       improve;
     - the model's m30 (img3 − img0)(Sr − undoped), against DFT at q = +1 (+40.2), on E′ (+36.8)
       and at q = 0 (−2.9);
     - the m21 and training-host quantities of item 5.
4. **Adoption for S2.** This is a new decision rule. It was written after all zero-shot results
   had been read, and it is fixed before any WP3 result exists.
   - **Status.**
     - It implements SCREENING_ROADMAP update 2026-10-28, consequence 1 (adoption also needs the
       thresholds of criteria 3–5).
     - It makes concrete update 2026-10-27, consequence 1 ("a fine-tuned potential that passes
       criteria 5 and 6"). Whole-cell criterion 5 is replaced by the free-region gate (d), whose
       design is post hoc (WP2e; amendment l item 4).
     - It refines PLAN "Long-term goal": S2 is decided by the outcome below, not by criterion 6
       alone.
     - Item 4 does not change criterion 6 beyond item 3. Criterion 6 (item 3, with the h-only
       verdict beside it) is reported whatever the outcome.
     - The rule is appended to the roadmap as a dated update.
   - **Disclosure.** Zero-shot MACE already fails:
     - (b) on the 4 pairs: raw RMS 23.6, E′ RMS 38.2, and the m32 GA crossing;
     - (c): m30 GA near −60.0 meV, with the sign disagreeing;
     - criterion 5, at every WP2b frame.

     On the atom sets of (d), its image-0 DFT residual RMS is about three times the threshold.
   - **Conditions.** The fine-tuned model replaces zero-shot MACE in S2 only if all of the
     following hold:
     - **(a)** Criterion 6 gives "improvement" (the verdict of item 3).
     - **(b)** Over all 9 test pairs (item 1′), on E′ (on raw F under the item-1c fallback):
       - RMS(model − DFT) < 20 meV; and
       - no pair changes class between model and DFT among {< −59.5, inside, > +59.5 meV}
         (amendment g item 2).

       Both parts take the DFT ΔE_a, and so the DFT class, from E′ (from raw F under the
       fallback). The DFT E_a is the maximum over images 2–4 of E′_i − E′_0 (`scripts/32`), and
       the class is `band_class` of that ΔE_a.
       The model ΔE_a is the model's own energy difference along the band, which is the same on
       either basis. (b) is therefore decided on band-term-corrected DFT; this is a new rule that
       departs on purpose from criterion 3. The raw-F DFT values and classes, and the m30/m32
       4-pair values, are reported beside it and decide nothing. (b) reclassifies no pair of
       criterion 3 or of `WP2B_RESULT.md` §3, which stay on raw F (amendment h item 1; item 1′,
       "No re-decision"). For example, m05 Sr is class −1 on raw F and 0 on E′. On the 4 m30/m32
       pairs (m30 GA, m30 Sr, m32 GA, m32 Sr) the DFT classes are the same on both bases
       (+1, 0, 0, 0).
     - **(c)** At the 5 non-far m30 sites, on raw F (criterion-4 thresholds):
       - every |far-referenced E_b(model) − E_b(DFT)| < 25 meV; and
       - the far-referenced E_b at the Sr hinge, Sr flank and GA near sites has the DFT sign.

       The result is labelled "one host (m30), 5 sites".
     - **(d)** WP3b passes (below).
     - **(e)** The MD stability check passes (below).
   - **WP3b.** By `scripts/40_wp3b.py`, committed before training, and run whenever a fine-tuned
     model exists.
     - **Cells.** Image 0 of `band_{undoped,GA,Sr}_{m30,m32}.extxyz`: 6 cells, fixed cell.
     - **Free region.** It is the same in the three cells of a host (amendment l item 4).
       - **Atoms.** Every atom within 6.0 Å (minimum image, start geometry) of any of three fixed
         points: the vacancy site (`scripts/29 ref_vacancy_position` via `build_pair`, as in
         `scripts/38`), the Sr atom of the Sr cell, and the GA carbon of the GA cell.
       - **Molecules.** Organic molecules are found by bonding (`scripts/38 molecule`) and are free
         or fixed whole, by the distance of their C.
       - **Identity check.** Each free inorganic atom and each free C is mapped to the nearest
         same-species atom of the undoped cell (Sr to Pb). If the three mapped sets differ, their
         union is freed in all three cells.
       - **On the WP2b frames** the sets are identical in both hosts: 81, 83 and 81 free atoms (25
         inorganic + 7 molecules).
     - **Constraint.** Every other atom is held at its start position (ASE FixAtoms).
     - **Relaxation.**
       - The selected model, float64, ASE FIRE with default parameters (as in `scripts/29`).
       - fmax 0.01 eV/Å over the free atoms, at most 10 000 steps.
       - Then one `scripts/30` single point at the WP2b settings, labelled
         `wp3b_<host>_<system>_img0`.
     - **Pass.** (d) passes only if every one of the 6 cells has a residual DFT force over its free
       atoms with RMS < 0.05 eV/Å and max < 0.2 eV/Å. Forces are per-atom norms, as in
       `scripts/32` (`dft_frms_eVA`, `dft_fmax_eVA`), not the component RMS of 3(i).
     - **Fail.** (d) fails if any of these happens:
       - a relaxation reaches the step cap;
       - an I lies within 1.2 Å of the vacancy site;
       - the Sr atom or GA carbon moves by 1.0 Å or more (the `scripts/29` checks);
       - the `scripts/35` (organic) topology check fails;
       - an SCF does not converge, meaning the output has JOB DONE but not "convergence has been
         achieved" (`scripts/32 parse_qe` returns converged = False).

       No cell is dropped or re-run with other settings.
     - **Interrupted jobs.**
       - A `wp3b_` or `wp3bu_` QE single point without JOB DONE (`parse_qe` returns None) follows
         item 1d: one resubmission with the identical input. A job the queue gives up on has no
         complete output.
       - A relaxation, or an (e) MD run, stopped by a spot reclaim, node loss, OOM or wall time is
         rerun from the start with the identical script, model and seed, at most twice. Partial
         outputs are discarded unread.
       - Neither is a fail. Each rerun is listed with its cause and time.
       - If a cell still has no complete output, (d) (or (e), for an MD run) cannot be evaluated,
         which the Outcomes treat as a fail. For a `wp3bu_` job, the value is reported as missing.
         Neither case is ever resolved by changing settings.
     - **Zero-shot comparator (not a decision rule).** The same atom sets at the WP2b image-0 frames
       give RMS / max (eV/Å):

       | host | undoped | GA | Sr |
       |---|---|---|---|
       | m30 | 0.153 / 0.332 | 0.142 / 0.270 | 0.160 / 0.337 |
       | m32 | 0.157 / 0.360 | 0.148 / 0.365 | 0.160 / 0.374 |

       All six fail. Freezing alone cannot pass, so a pass must come from the fine-tuned
       relaxation.
     - **Reported, not gating.**
       - Whole-cell values, and the free atoms within 1 Å of the 6 Å surface.
       - The relaxation energy at model and at DFT level (F(relaxed) − F(image 0)) per cell, and
         its dopant − undoped difference per host.
       - The same six relaxations without constraints (labels `wp3bu_<host>_<system>_img0`), each
         followed by a DFT single point. For each: the whole-cell residual force (criterion 5 as
         pre-registered), F(minimum) − F(image 0), and the basin measures of amendment c item 1
         beyond 6 Å.
       - At the WP2e DFT minimum of m30 GA (the last frame of `wp2e/relax_m30_GA_img0.out.gz`),
         with the selected model in float64:
         1. E_model(DFT minimum) − E_model(image 0 of `band_GA_m30.extxyz`), beside the DFT value
            F(minimum) − F(image 0) = −977.3 meV. Image 0 is the start of that DFT relaxation and
            a zero-shot-relaxed endpoint (MACE fmax 0.019 eV/Å).
         2. For the fine-tuned model only: E_model(DFT minimum) − E_model(final geometry of
            `wp3bu_m30_GA_img0`), the model's own unconstrained minimum from image 0. It has no
            separate zero-shot value; the nearest is (1).
         3. The whole-cell (all 234 atoms) RMS and max of the per-atom model force norm at the DFT
            minimum, as `scripts/32` `dft_frms_eVA` / `dft_fmax_eVA`, not the component RMS of
            3(i).

         Zero-shot: (1) +227.0 meV; (3) 0.115 / 0.260 eV/Å (component RMS 0.067 eV/Å). No
         relaxation is started from the DFT minimum.
     - **Scope.**
       - A pass validates fine-tuned forces at frozen-far-field minima of vacancy cells only (V and
         first-shell D+V). It validates neither the energies of those relaxations nor vacancy-free
         cells. It is not criterion 5.
       - An S2 protocol that relaxes whole cells (for example the host and V references of
         `scripts/29`) needs criterion 5 on all atoms of a fine-tuned full-cell minimum,
         pre-registered for that protocol. The `wp3bu_` values of WP3b do not meet this
         requirement.
       - `scripts/29 --freeze-beyond` cuts by atom; it is changed to this rule before any S2 use.
     - **Other rules.** WP3b outputs never enter any training set. WP3b is not WP2e′, which stays
       unscheduled.
   - **(e) MD stability.** By `scripts/41`, committed before training, and run whenever a
     fine-tuned model exists.
     - **Runs.** 5 ps of fixed-cell Langevin MD with the selected model: 1 fs steps, friction
       0.01 fs⁻¹, a Maxwell–Boltzmann start and a crc32 label seed, as in `scripts/35`. It runs at
       300 K and 450 K for each of the 6 WP3b cells: 12 runs.
     - **Pass.** Every frame at 100 fs intervals must pass both of these:
       - `scripts/35 sane()`: composition unchanged, the organic (C/N/H) bonding pattern of the
         start, no contact below 0.65 Å, and model max force below 15 eV/Å;
       - the inorganic checks of `scripts/41` (minimum image), which `sane()` does not test:
         1. no I–I distance below 3.0 Å. This flags I–I bonding: I₂ is 2.67 Å and I₃⁻ about
            2.9 Å. The shortest I–I in any training DFT frame is 4.04 Å.
         2. In Sr cells, the Sr atom is nearer its start position than the start position of any
            Pb.
         3. In GA cells, the GA carbon is nearer its start position than the start position of any
            other C or any Cs.

         Checks 2 and 3 test whether the dopant has left its site, not how far it rattles: the
         B–B and A–A spacings are at least 6.28 Å, against thermal amplitudes below 1 Å. The 1.0 Å
         cut of `scripts/29` is a relaxation test and is not used in MD.
     - **Reported, not gating.** For each run: the minimum I–I, Pb–I and Sr–I distances, and the
       largest displacements of Sr and of the GA carbon from their start positions.
     - **Interrupted runs** follow the "Interrupted jobs" rule of (d).
     - A vacancy hop is not a failure.
   - **Outcomes (exhaustive; fail-closed).**
     - **No improvement:** if there is no fine-tuned model (two technical failures, item 2), or if
       (a) fails or cannot be evaluated.
     - **Improved but not validated:** if (a) holds and any of (b)–(e) fails or cannot be
       evaluated.
     - **Validated:** if all of (a)–(e) hold.
       - S2 uses exactly the evaluated `wp3.model`, identified by the recorded sha256.
       - Any other model is new and unvalidated. That includes a model that is retrained,
         re-seeded, given other data or settings, or trained on any frame of a test or validation
         host.
     - **If not validated** (either of the first two outcomes):
       - S1 ends without a validated potential, and zero-shot MACE is not re-admitted.
       - S2 proceeds as in SCREENING_ROADMAP update 2026-10-28, consequence 1: DFT for the decisive
         quantities, or a coarser ranking metric.
     - **Test hosts used up.** The 7 test hosts are used up by this single evaluation, and m21 has
       served for model selection. No later model may be validated on them. A further fine-tune
       needs new held-out hosts, named in an amendment before their DFT exists.
     - (d) and (e) are run and reported whatever (a)–(c) give.
   - **Error budget if validated.** The S1 errors are single-point errors at fixed geometries:
     ΔE_a on the zero-shot 7-image NEB paths (maximum over images 2–4), and far-referenced E_b at
     the zero-shot whole-cell WP1 v2.1 minima. S2 quotes the RMS ΔE_a and E_b errors, each with
     the one-sided 95% upper confidence bound on the error SD σ under zero-mean normal errors with
     n degrees of freedom, RMS·sqrt(n/χ²_{0.05,n}):
     - ΔE_a: RMS × 1.645 (n = 9 pairs);
     - E_b: RMS × 2.089 (n = 5 sites).

     These bound σ, not individual errors: for n = 9, a new independent error lies within
     ±1.645·RMS only about 87% of the time. Both bounds are optimistic, because the errors are not
     independent (item 5). The four m30/m32 pairs share one undoped band per host, and the five
     sites share two far references (Pb64 for Sr, FA152 for GA). If the shared band or reference
     has the same error variance as each dopant band or site, the 95% factors are about 1.68 for
     the 9 pairs and 2.27 for the 5 sites (Monte Carlo). S2 quotes the independent-error factors
     above, with this caveat. The budget is quoted only as the single-point part of the error. It
     excludes any error from the model's own geometries or paths, which S1 does not measure.
   - **Scope of a validation.**
     - **Family.** FA19Cs1Pb20I60 cells with the iodide vacancy, GA on an FA site and/or Sr on a Pb
       site.
     - **Protocols.** A validation covers exactly what S1 tests:
       - **Energies.** Single points at fixed geometries of the kinds compared with DFT in
         criterion 6, (b) and (c): zero-shot NEB images and zero-shot WP1 whole-cell minima. The
         error budget above applies only to such single points.
       - **Geometries.** Frozen-far-field relaxations of the WP3b construction, for the forces on
         the free atoms of vacancy cells (V, and D+V with the dopant in the first shell; (d)). The
         energies of these relaxations are reported, not validated. Host and D_j cells, saddles
         and paths are not tested.
       - **MD.** Up to the length tested in (e), for stability only.
       - **Not validated.** E_b computed from fine-tuned relaxations (frozen-far-field or
         whole-cell), and barriers on the model's own NEB paths. No NEB with the model enters S1,
         and whole-cell relaxations are excluded (WP3b, Scope).
       - **Before S2 uses such a value.** Before S2 reports a barrier difference or an E_b from one
         of these protocols with an error budget, a DFT check of that protocol is pre-registered
         in an amendment, before its DFT exists. It runs on hosts that gave no WP3 training or
         validation frame:
         - for barriers, DFT single points at images 0, 2, 3, 4 and 6 of the model's own
           frozen-far-field CI-NEB bands, at the criterion-3 thresholds (RMS ΔE_a < 20 meV; no
           class change at ±59.5 meV);
         - for E_b, DFT single points on the relaxed quartet cells, at the criterion-4 thresholds.

         Until that check passes, such values are labelled "fine-tuned-MACE level" and carry no
         error budget.
       - **Relation to the roadmap.** This check is the DFT-level test of the frozen-far-field
         construction that roadmap update 2026-10-27, consequence 2, requires. WP3b covers only its
         forces, and WP2e′ stays unscheduled.
     - **Topology.** Every structure it relaxes in S2 must pass the `scripts/35` (organic) topology
       check.
     - **Elements.**
       - H, C, N, Sr, I, Cs and Pb only; it cannot evaluate Cl, S, Ca or Rb.
       - `--foundation_model_elements True` is not used: it would keep untested representations
         for other elements after every shared weight has moved.
       - DMA, acetamidinium and other cations made of these elements would run, but they are
         untested.
     - **New chemistries.** Each S2 chemistry needs its own DFT validation at the criterion-3/4
       thresholds, or its own fine-tune, pre-registered with held-out hosts. An S1 pass validates
       the WP3 recipe for GA and Sr, not this model for other dopants.
     - **Offsets.** The per-element offsets cancel in composition-balanced E_b and ΔE_a. Outside
       the family they make absolute energies meaningless.
     - **What the test spans.**
       - Shared by all hosts: one vacancy site and the near-shell sites (Pb124, Pb136, FA128).
       - Varying across hosts: the FA configuration, the hop direction and the mid- and far-shell
         sites.
       - Criterion 6 therefore tests transfer across these at one vacancy site. Binding maps and
         barriers keep DFT checks (see Protocols).
5. **Power and coverage.** This item qualifies how strong each statement is. It never changes a
   verdict of items 3–4.
   - **Correlation.**
     - The 4 m30/m32 pairs share one undoped band per host.
     - The 5 far-referenced sites share one far site per dopant (Sr: Pb64; GA: FA152).
     - Each of these tests therefore carries about 3 independent errors. The 9 pairs come from 7
       hosts.
   - **No significance test is attempted.** On 4 pairs the smallest one-sided sign-flip p is 1/16.
     On 5 sites it is 1/32, and only if all 5 improve.
   - **Chance pass.**
     - Force RMSE is almost certain to fall.
     - Suppose the energy errors were an independent redraw of the zero-shot ones. Each energy
       condition would then pass with p ≈ 0.5, and criterion 6 with a probability of up to about
       0.25 (less with the E′ condition).
     - Criterion 6 alone is therefore not the gate; (b)–(e) are.
   - **(ii) on raw F for a model trained on E′** (E′ basis only).
     - Under independent zero-mean normal E′ errors with SD 5/10/15/20 meV, (ii) on raw F passes
       with probability 0.87/0.62/0.46/0.35. (ii) on E′ passes with probability ≥ 0.99, and the
       RMS part of (b) with probability 1.00 (0.93) at SD 10 (15) meV.
     - At SD 10 meV, the raw pass probability is 0.28 if the m30 Sr error is positive and 0.95 if
       it is negative. Whether it fails is decided mainly by the sign of the m30 Sr residual.
     - If the model's errors are the zero-shot E′ errors scaled by α, raw passes for
       −0.10 < α < 1. If they keep 20–50% of the zero-shot E′ errors (plus SD 10 meV), it fails
       with probability 0.02–0.08.
     - A fail on raw F with a pass on E′ is reported as "no improvement on raw F; E′ improved",
       with these figures and the per-pair raw and E′ errors. It shows that the model does not
       reproduce the neutral-cell band term, not that it is worse on E′.
     - The outcome stays "No improvement" (fail-closed). It is never a reason to re-run, re-train
       or re-decide.
   - **Adoption (b).** Under independent zero-mean normal errors, a model with a true RMS of 30
     (25) meV meets the RMS part with probability 0.09 (0.24) on 9 pairs. The figures are 0.22
     (0.37) on 4 pairs and 0.02 (0.13) on the 18 pairs of criterion 3.
   - **Adoption (c).** A model with a true error SD of 15 meV fails "all 5 < 25 meV" with
     probability 0.40. This assumes zero-mean errors; under the raw-basis fallback, the expected
     Sr bias of item 1c is stated beside it.
   - **Coverage.** m30 and m32 lack two systematic zero-shot errors:
     1. the along-path barrier overestimate of low-barrier hosts. MACE − DFT absolute E_a is +59 to
        +117 meV in 14 of the 15 bands of m05, m06, m15, m20 and m21 (m15 Sr: −24.9), but within
        ±22.3 meV (RMS 16.0) in the six m30/m32 bands;
     2. the first-shell Sr E_b overestimate: +21.7 to +36.1 meV at m05 and m21, against −6.4 and
        +14.1 meV at m30, the only test host with E_b.

     Whether the five item-1′ hosts carry (1) is unknown until their DFT exists. Their zero-shot
     MACE E_a (images 2–4) are, in meV: m10 undoped 85.9, GA 152.4; m18 undoped 197.1, GA 166.9;
     m04 undoped 139.4, Sr 132.0; m14 undoped 240.1, Sr 100.4; m27 undoped 267.8, Sr 279.6. Seven
     lie within the 55–211 meV MACE range of the affected bands. m10 undoped and m14 Sr lie below
     112.0 meV, the lowest MACE value of an unaffected band (m32 GA).

     Criterion 6 and adoption (b) test the paired ΔE_a, in which a host-wide overestimate largely
     cancels. A pass therefore does not show that (1) or (2) is corrected on unseen hosts, and the
     report says so. If any item-1′ band shows a zero-shot absolute E_a error above +59 meV, the
     fine-tuned change in those bands is reported, labelled as the only unseen-host evidence on
     (1); it gates nothing. Criterion 6(iii) and (c) rest mainly on one GA site, whose far
     reference has a MACE-level SD of 28 meV and no DFT noise floor.
   - **Wording.**
     - A pass of criterion 6 is reported as "consistent with improvement on the held-out hosts; not
       statistically resolved".
     - A fail is reported as a fail. The sample size is stated beside it, but it is never a reason
       to adopt, to change a threshold or to re-run.
   - **Also reported for both models, labelled.**
     - m21 (validation): 3 absolute E_a errors, 2 paired ΔE_a errors and 5 far-referenced E_b
       errors. m21 selected the checkpoint, so it is not independent, and its GA and Sr DFT maxima
       are unbracketed.
     - The training hosts, labelled as fit quality.
6. **WP1 map with the fine-tuned model.** This is the map output of the WP3 row; amendment g item 6
   superseded only that row's E0s.
   - **When.** Only if the model is validated under item 4. Otherwise it is not run, and that is
     recorded as a deviation from the WP3 row, decided here.
   - **Status.** Reported only; it never changes a verdict.
     - Its relaxations relax whole cells (doped cells, host and V references) with no frozen
       region. That protocol lies outside the validated protocols of item 4: (d) validates
       frozen-far-field relaxations only, and (c) validates energies only at zero-shot geometries.
     - Every row, and every criterion-1/2 statement drawn from them, is therefore labelled
       "fine-tuned-MACE level; whole-cell relaxations, geometry not validated (item 4, Scope)".
     - The `wp3bu_` whole-cell residuals are quoted beside it. Whatever they give, they do not add
       whole-cell relaxations to the protocols of item 4: they cover only the six m30/m32 image-0
       vacancy cells, no D_j or host cell and no m21 cell.
   - **Hosts.** m30 and m21, all 20 Pb and 19 FA sites. m21 is labelled as the
     checkpoint-selection host.
   - **Protocol.** v2.1, as in WP1 production:
     - doped cells relaxed 0.02 → 0.01 eV/Å;
     - references relaxed afresh with the fine-tuned model to 0.005 eV/Å, with no `--ref-from` of
       zero-shot references;
     - `--steps 10000`.
   - **Code change.** `scripts/29` gains `--model` and writes the path and sha256 into `protocol`.
     `--ref-from` refuses a different model, so `scripts/34` refuses to pool zero-shot and
     fine-tuned hosts.
   - **Analysis.** `scripts/34 --mode map --fmax 0.01`. Criterion 2's sign rule becomes 2 of 2. The
     result is labelled as under Status and reported beside the zero-shot rows of the same hosts.
7. **Order of work.**
   1. Commit this amendment on its own. Then commit `scripts/33` (as changed above), `39`, `40`
      and `41`, before any step-2 job is submitted, and run `scripts/39` in gate-only mode
      (reproduction gate and QE-input position check on the 46 m30/m32 frames).
   2. Run `scripts/35`. Then the DFT: the WP3 frames, the 50 item-1′ frames and the 8 q = +1
      checks (about 150 single points, about 18 node-hours).
   3. Archive, then run `scripts/33`. Record the counts, the check outcome and w_E.
   4. Pre-flight, timing run, then training with the start check.
   5. Technical-failure check. Commit the model note with the sha256.
   6. Run `scripts/39` once (a re-run after a gate failure, item 3, is not a second evaluation).
   7. Run WP3b (12 single points) and (e).
   8. Write the WP3 result with every verdict, and add the roadmap update.

   The item-1′ outputs are archived but not analysed before step 6.

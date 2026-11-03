#!/usr/bin/env python
"""WP3 post hoc diagnostic D3: where the fine-tuned model books its change of S = E(i*) - E(0) along a densified band
path, in two gauges (work of the force change; MACE site energies), as WP3_DIAGNOSTICS_D3_PLAN.md (committed at
ddb352b before any interpolated-point single point existed). A pre-specified description; no verdict.

Status. Post hoc and reported only: nothing here changes a WP3 verdict, threshold or the outcome (amendment m item 4);
no model is validated or chosen. It does not answer D2's Q4 and does not run reason 7's named test (model - DFT
residual). Laptop single points only (MACE float64 on CPU, --threads 4): no MD, relaxation, training or QE.

Inputs (every path written to the JSON or the console log is repository-relative, '../bands/...' or '~/...'):
    plan         results/objective2/dopant_shell/WP3_DIAGNOSTICS_D3_PLAN.md (check 2).
    bands        ../bands/band_<system>_<host>.extxyz (--bands, the scripts/44 default): 7 images each with the stored
                 zero-shot energy, forces and per-atom 'energies'. Images 0-4: single points for both models;
                 image 6: geometry only (hopping I, hop midpoint); image 5: not used. sha256 of all 37 recorded.
    dataset      wp3/dataset/{train,valid,test}.xyz and dataset_meta.json, through scripts/44 Data (the archived QE
                 outputs under --dft and wp1_production/wp2cde_selection.json are read by it for its cross-check).
    D2           wp3/diagnostics/d2_path_attribution.json (--d2-json): the values of check 6, D2's versions and model
                 sha256 (check 1), the seen coarse D2b groups_meV (section 7 item 5, exclusion report).
    zero-shot    scripts/44 Models.zeroshot: mace_mp(model="medium", device="cpu", default_dtype="float64"); foundation
                 file sha256 = scripts/39 FOUNDATION_SHA256 (exit 3).
    fine-tuned   scripts/44 Models.finetuned: --model (wp3/run2/wp3.model), MACECalculator(float64, cpu, head
                 "Default"); sha256 = --model-sha256 (exit 3). Both arms float64/CPU asserted (scripts/39 Arm).
    Per-atom energies: the calculator property 'energies' (keeps the E0s), never 'node_energy'; asserted at every
    single point: 'energies' - 'node_energy' = the model's E0 of each atom (1e-9 eV; the E0s are non-zero, so the
    property used is not node_energy) and sum_i eps_i = E (1e-6 eV).

Paths (plan section 3). 37 bands (18 training, 3 m21, 16 test; scripts/44 bands37 order). Per segment k -> k+1 the
minimum-image displacement dr_k (ase find_mic, band cell); path points r_k + (j/8) dr_k, j = 0..8, with the stored
images as j = 0 and j = 8; the quadrature step of a segment at n intervals is dr_k / n. n = 4 and n = 2 use every 2nd
and 4th point (subsets), n = 1 the images only.
    P (primary)   0 -> 1 -> 2 [-> 3], to i*.        C (sensitivity)   chord 0 -> 2 [-> 3], to i*.
    i* = the D2 DFT argmax image (images 2-4 of raw F, recomputed from REF_energy_raw): 3 in 35 bands, 2 in m21_GA and
    m21_Sr (asserted). For these two, P and C are each extended 2 -> 3 (extension, reported apart, outside every
    criterion and summary). Single points per model and band: images 0-4 (5) + interior of P segments 0-1, 1-2, 2-3 (21)
    + interior of the chord 0-2 (7) = 33; 1221 per model, 2442 in all (check 9).

Quantities (plan sections 4-5), meV unless stated.
    D3a  W = -sum 1/2 (F_a + F_b) . (r_b - r_a) over successive points, per atom before summation, n = 8, 4, 2 (and 1);
         closure = W - [E(end) - E(start)] per segment and in total; per model and path.
    Every work quantity X (per-group and total works of each model, dW_g and its sum; per path, and per segment for the
         totals): X8, X4, X2, X1; e = |X8 - X4|/3 (asymptotic error estimate of X8, not a bound); Richardson
         X_R = X8 + (X8 - X4)/3 (its error not estimated); |X8 - X4| (the conservative error used in statements);
         ratio (X2 - X4)/(X4 - X8) (null when X4 = X8); closure4/closure8 (null when closure8 = 0).
    D3b  dW_g = -int dF_g . dr, dF = F_FT - F_ZS, for the five D2 groups (scripts/44 groups(): image 0, minimum image,
         distances to the hop midpoint r_I(0) + 1/2 mic(r_I(6) - r_I(0)); hop_I, inorganic_near/far, organic_near/far
         by whole molecules of scripts/38 molecule(); membership fixed along the path). Identity (1e-9 meV, n = 8,4,2,1):
         sum_g dW_g = W_FT - W_ZS, and (sum_g dW_g - dS) = closure_FT - closure_ZS, dS = segment change
         [E_FT(i*) - E_FT(0)] - [E_ZS(i*) - E_ZS(0)]. Comparators per group: dW_g, W_ZS,g, W_FT,g (X_R, e), the
         displacement share D_g = sum_{i in g} sum_steps |dr_i|^2 / sum_all, and dW_g/W_ZS,g where |W_ZS,g| >= 5 meV
         (Richardson values). Cancellation kappa = (|L| + |N|)/|L + N|, L = dW(hop_I) + dW(inorganic_near), N = the
         other three (Richardson; ill-conditioned where |dS| is small).
    D3c  d_eps_g = sum_{i in g} {[eps_FT(i*) - eps_FT(0)] - [eps_ZS(i*) - eps_ZS(0)]}; asserted sum_g d_eps_g = dS
         within 1e-6 eV.
    D3d  (reported, no rule) per model and P segment: cubic Hermite H(lambda) with E at both images and dE/dlambda =
         -F_k . dr_k, -F_k+1 . dr_k (eV); excess = max_j [E(lambda_j) - H(lambda_j)] over the 7 interior points; beside
         it the largest E(lambda_j) above the higher bracketing image. D3d.hermite holds the P segments to i* only; the
         chord 0-2 is beside it (hermite_chord_0_2_beside), the extension's 2-3 segment under extension_2_3
         (D3d_hermite_2_3). Geometry along P and C to i*: the largest per-atom
         displacement per segment; per interior point the shortest intramolecular distance (image-0 molecules) and the
         shortest pair distance, against the shortest at the path's images. The number of atoms whose distance to the
         hop midpoint crosses 6 A at any point of P between image 0 and i*.
    E_a link per band: E_a = max over images 2-4 of E_i - E_0 of the new image points (scripts/44 argmax; scripts/39 Ea is
         not called: it needs image 6); E_a(FT) - E_a(ZS) = dS + [E_FT(i*_FT) - E_FT(i*)] - [E_ZS(i*_ZS) - E_ZS(i*)]
         (asserted, 1e-9 meV).

Resolution (plan section 6), on P to i*; path C by the same criteria. A band is resolved if
    1  for both models at n = 8: |closure8| <= 2 meV, and closure4/closure8 in [2, 8] unless |closure8| < 0.5 meV;
    2  for every group: |dW_g,8 - dW_g,4| <= 3 meV, and (dW_g,2 - dW_g,4)/(dW_g,4 - dW_g,8) in [2, 8] unless
       |dW_g,4 - dW_g,8| < 0.3 meV.
    Every failed criterion is recorded per band. A band enters the path-dependence summary only if P and C both meet
    them. Unresolved bands keep their per-band values; no summary over them. Exclusion report: for excluded and
    resolved bands, by host and split: failed criteria, dS, the seen coarse D2b groups_meV.
Summaries (plan section 7), over the resolved bands only: overall, by split (training, m21, test) and by host (one row
    per host plus the mean of the host means of every mean statistic). Items 1-7 (dW_g; d_eps_g; comparators; path
    dependence P - C; seen coarse D2b values against C and P Richardson values; kappa; D3a closures), the gauge sign
    comparison (agreement or disagreement only when both |means| exceed max(2 meV, 2 x SE over bands), plus the mean
    |dW_g,8 - dW_g,4| for the work gauge; otherwise 'sign not resolved') and the per-band count of groups whose signs
    agree. Fewer than 10 resolved bands: labelled 'few resolved bands'. No verdict; shares of a signed sum are not used.

Checks (plan section 8; fail-closed unless marked; nothing is written on a failure). Order: 2, inputs, 1 (versions),
    3, 4, 6 (i*, groups), 8 (molecules, geometry only), 1 (model sha256), single points at images 0-4, 5, 6 (energies and
    works), then the interior points, 9, 7; check 10 is reported. No interpolated point is evaluated before checks 1-6
    and 8 have passed (an addition).
    1  model-file sha256 = D2's model_files and the scripts/39/44 constants; mace, torch, ase, numpy versions = D2's
       'versions' (exit 3).
    2  the plan file is committed, its last commit is ddb352b (the commit this script implements; recorded), and the
       working file is byte-identical to that commit's and to HEAD's version, with no local change (exit 4).
    3  band files: sha256 recorded; 7 frames; identical cell (1e-12 A) and species in every image; for every step
       0-1, 1-2, 2-3, 3-4 and the chord 0-2: minimum-image = raw displacement (1e-8 A per component), max per-atom
       |dr| < 2 A, r_start + dr = r_end (1e-8 A) (exit 5). The 0 -> 6 displacement is not bounded.
    4  images 0, 2, 3, 4, 6 equal the dataset frames: scripts/44 Data.need cross-check (positions and cell 1e-6 A,
       numbers identical; also DFT F, E_F, E' and forces of the dataset against the archived QE outputs) (exit 5).
    5  zero-shot at images 0-4: |E - stored energy| <= 1e-6 eV (scripts/39 TOL_FRAME_EV, Geometry.stored_energy);
       every per-atom energy = stored 'energies' within 1e-6 eV; largest force difference reported, not gated (exit 5).
    6  D2 reproduction (exit 6): per model, segments_beside dE_meV and W_meV of 0-2, 2-3, 3-4 (1e-3 meV); D2b
       groups_meV, segment_change_meV and direct_meV (1e-3 meV); groups hop_I_index and n_atoms; D2a i_star of dft
       (= i* from REF_energy_raw), zeroshot and finetuned. Addition: the new quadrature code at n = 1 on C reproduces
       scripts/44 path_work (1e-9 meV).
    7  identities: the work identity (1e-9 meV), sum_i eps_i = E at every point and sum_g d_eps_g = dS (1e-6 eV), the
       E_a link (1e-9 meV) (exit 7).
    8  molecules: scripts/38 molecule() of every image-0 C returns the same atoms at every image 0..i* and every
       interior point of P and C (and of the extension) (exit 7).
    9  single points: 33 per model and band, 2442 in all; no point evaluated twice (exit 7).
    10 reported, not gated: the eight scratch image-1 closures of WP3_DIAGNOSTICS.md section 4 (zero-shot, one interval
       per segment, 0 -> 2 and full path; m05_undoped, m12_undoped, m30_GA, m27_Sr) recomputed (P at n = 1).

Every departure, interpretation and addition is listed in the JSON (departures_from_plan, interpretations_of_plan,
additions_to_plan). The head mirrors d2_path_attribution.json: script sha256, plan commit, git state, versions, model
files, input files, band-file sha256. No bytecode is written (sys.dont_write_bytecode).

    python scripts/45_wp3_d3_dense_path.py
    defaults: --model results/objective2/dopant_shell/wp3/run2/wp3.model, --model-sha256 the wp3 model note's, --bands
    ../bands, --d2-json wp3/diagnostics/d2_path_attribution.json, --out-dir results/objective2/dopant_shell/wp3/diagnostics
    (d3_dense_path.json; the console output is appended to d3_console.log there at the end of a run with exit 0; a
    failed run writes neither file, its console output is on stdout only), --threads 4.
    Development only: --bands-only <host_system> ... runs a subset (33 single points per model and band), is refused
    for the default --out-dir and marks the JSON 'development_subset'; it is never the recorded run.
Exit status: 0 done; 2 command-line error; 3 a model file's sha256 or a package version differs (check 1); 4 the plan
check failed (check 2); 5 a data check failed (an input missing, band files, geometry vs dataset, stored zero-shot
values: checks 3-5); 6 a D2 reproduction failed (check 6); 7 an identity, the molecule partition, the single-point count
or another assertion failed, or an unexpected error (checks 7-9).
"""
import argparse, datetime, io, json, os, subprocess, sys, time
import importlib.util
sys.dont_write_bytecode = True      # no scripts/__pycache__ writes from the imports below
import numpy as np
from ase import Atoms
from ase.geometry import find_mic

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DS = os.path.join(ROOT, "results", "objective2", "dopant_shell")


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


a44 = _load("a44", "44_wp3_diagnostics.py")           # Data, Models, groups, path_work, attribution, argmax, rel, Tee, ...
a39, a38 = a44.a39, a44.a38                            # Geometry, Arm, sha256, git_state, write_json; molecule()

PLAN = "results/objective2/dopant_shell/WP3_DIAGNOSTICS_D3_PLAN.md"
PLAN_COMMIT = "ddb352b63513542df5082565dacfb494f0db5049"
SCRIPT = "scripts/45_wp3_d3_dense_path.py"
PER_ATOM = "energies"                                  # MACECalculator property with the E0s (not 'node_energy')
MODELS = ("zeroshot", "finetuned")
GROUPS, LOCAL = a44.GROUPS, a44.LOCAL
SEGS = {"0-1": (0, 1), "1-2": (1, 2), "2-3": (2, 3), "0-2": (0, 2)}       # the computed segments
CHECK_STEPS = ((0, 1), (1, 2), (2, 3), (3, 4), (0, 2))                      # check 3
NS = (8, 4, 2, 1)                                      # n = 8 dense; 4 and 2 subsets (plan); 1 = images only (beside)
PER_BAND, N_BANDS = 33, 37
N_TOTAL = 2 * PER_BAND * N_BANDS                       # 2442
I_STAR_2 = {"m21_GA", "m21_Sr"}                        # plan section 1: i* = 2 in these two bands
SPLIT_NAME = {"train": "training", "valid": "m21", "test": "test"}
TOL_ID, TOL_SITE, TOL_D2, TOL_MIC, TOL_CELL, TOL_E0 = 1e-9, 1e-6, 1e-3, 1e-8, 1e-12, 1e-9   # meV; eV; meV; A; A; eV
TOL_STORED = a39.TOL_FRAME_EV                          # 1e-6 eV (scripts/39)
MAX_STEP = 2.0                                         # A, check 3
CLOSURE_MAX, CLOSURE_EXEMPT, DW_MAX, DW_EXEMPT, RATIO_LO, RATIO_HI = 2.0, 0.5, 3.0, 0.3, 2.0, 8.0   # meV; criteria
W_ZS_MIN, E_COMP, KAPPA_HI, MARGIN_MIN, FEW = 5.0, 1.0, 2.0, 2.0, 10
R_CUT = a44.R_CUT                                      # 6 A
EXIT_SHA, EXIT_PLAN, EXIT_DATA, EXIT_REPRO, EXIT_ERROR = 3, 4, 5, 6, 7
# WP3_DIAGNOSTICS.md section 4 (581d020): zero-shot closures with image 1, one interval per segment (check 10)
SEEN_IMAGE1 = {"m05_undoped": {"0-2": -19.0, "full": -24.6}, "m12_undoped": {"0-2": -25.7, "full": -30.0},
               "m30_GA": {"0-2": -30.8, "full": -38.6}, "m27_Sr": {"0-2": -23.7, "full": -26.5}}
Stop, require, rel = a44.Stop, a44.require, a44.rel

DEPARTURES = []
INTERPRETATIONS = [
    "path points: interior point j of segment k is r_k + (j/8) dr_k with dr_k = find_mic(r_k+1 - r_k) in the band cell; "
    "j = 0 and j = 8 are the stored images; the quadrature step of a segment at n intervals is dr_k/n (the plan's "
    "'n equal steps of dr_k/n'), not the difference of rounded point positions",
    "check 3 'minimum-image displacement equals the raw displacement' and 'r_start + dr = r_end' are tested per Cartesian "
    "component within 1e-8 A (the plan's tolerance of the second); 'same cell' within 1e-12 A, species identical",
    "check 4 is the scripts/44 Data.need cross-check of images 0, 2, 3, 4 and 6 (the plan's parenthesis); it also compares "
    "the dataset's DFT energies and forces with the archived QE outputs",
    "check 5 covers images 0-4 (image 1 is not in the dataset; it is read from the band file); per-atom energies are "
    "compared with the band file's per-atom 'energies' array",
    "check 6 tolerance 1e-3 meV for every reproduced number (the plan states it for segments_beside); groups_meV, "
    "segment_change_meV and direct_meV are recomputed with scripts/44 path_work and attribution from the new image single "
    "points; i* from the dataset REF_energy_raw by scripts/44 argmax; D2a i_star is compared for dft, zeroshot and "
    "finetuned",
    "statements and summaries use the Richardson value X_R of every work quantity; the ratio dW_g/W_ZS,g, its 5 meV "
    "threshold (|W_ZS,g,R| >= 5 meV) and kappa use Richardson values",
    "a convergence ratio is null where its denominator is exactly zero; such a case falls under the criterion's exemption "
    "(|closure8| < 0.5 meV, |dW_g,4 - dW_g,8| < 0.3 meV); bounds are inclusive ([2, 8], <= 2 meV, <= 3 meV)",
    "D_g is summed over the n = 8 steps of P (each segment's steps are equal, so every n gives the same share)",
    "section 7 item 4 'the mean and the largest |dW_g(P) - dW_g(C)|': the mean of |d| and the largest |d| (Richardson); "
    "the signed mean is given beside; 'the mean of e(P) + e(C)' with e = |X8 - X4|/3 as defined, and beside it the mean "
    "of |X8 - X4|(P) + |X8 - X4|(C) (the conservative error of statements)",
    "section 7 item 5 is summarised over the P-resolved bands (C's own status not required; the number whose C fails is "
    "given); 'the median and the largest absolute value' = the median of the signed difference and the largest |.|",
    "section 7 item 7 is given per model (zero-shot, fine-tuned) for P and C, over the P-resolved bands",
    "'by host ... the mean of the host means': every statistic named mean* of the per-host summaries is averaged over the "
    "hosts with at least one resolved band (equal host weights); medians, ranges and counts are given per host only",
    "sign comparison: SE = sample SD (ddof 1)/sqrt(n) of the per-band values of the subset; work margin = max(2 meV, 2 SE) "
    "+ mean |dW_g,8 - dW_g,4|, site-energy margin = max(2 meV, 2 SE); 'exceed' is strict; with n < 2 the SE is undefined "
    "and the sign is 'not resolved'; given for every summary subset (overall, split, host); per band, a group's signs "
    "agree when sign(dW_g,R) = sign(d_eps_g)",
    "6 A crossings: an atom counts if at any point of P from image 0 to i* (images and interior points) its minimum-image "
    "distance to the fixed hop midpoint is on the other side of 6 A than at image 0",
    "shortest intramolecular bond = the shortest minimum-image distance between two atoms of the same image-0 molecule; "
    "reported per segment (minimum over its interior points) against the minimum over the path's images 0..i*",
    "Hermite excess and the excess above the higher bracketing image are in meV, over the 7 interior points j = 1..7",
    "splits: training = D2 'train', m21 = D2 'valid', test = D2 'test'; hosts are the 14 mNN of the 37 bands",
    "the extension 2 -> 3 of the two i* = 2 bands (extension_2_3) carries the D3a/D3b quantities of P_ext and C_ext, the "
    "numbers to which criteria 1-2 would apply (criteria_values_no_status: closure8, closure4/closure8, |dW8 - dW4|, e and "
    "the convergence ratio; no status, no 'meets' or 'failed' and no per-criterion pass/fail flag), d_eps_g and dS to "
    "image 3 (D3c_to_image3) and the Hermite excess of its 2-3 segment (D3d_hermite_2_3); it enters no criterion, no D3d "
    "block and no summary"]
ADDITIONS = [
    "development option --bands-only (a subset; refused for the default --out-dir; JSON marked development_subset); the "
    "recorded run uses all 37 bands",
    "order: no interpolated point is evaluated before checks 1-6 and 8 have passed on the images and geometries",
    "check 6 also reproduces D2a i_star of the two models, D2b segment_change_meV and direct_meV, and the group sizes; the new "
    "n = 1 quadrature on C is asserted to equal scripts/44 path_work (1e-9 meV)",
    "i* in {2, 3} and the i* = 2 bands = {m21_GA, m21_Sr} (plan section 1) are asserted (exit 6)",
    "the plan's last commit is asserted to be ddb352b, the commit this script implements (exit 4)",
    "'energies' assertion at every single point: energies - node_energy = the model's per-element E0 (1e-9 eV)",
    "n = 1 values (images only) are recorded beside n = 8, 4, 2 for every work quantity (P at n = 1 gives check 10; C at "
    "n = 1 is the coarse D2b)",
    "Hermite excess also for the chord 0-2 (D3d.hermite_chord_0_2_beside, beside D3d, not part of it) and for the 2-3 "
    "segment of the extension (extension_2_3.D3d_hermite_2_3); D3d.hermite holds the segments of P to i* only; D_g also "
    "along C; d_eps_g and dS to image 3 for the two extension bands",
    "molecule check also at the extension points; reported beside it at image 4",
    "the E_a link identity is asserted (1e-9 meV)",
    "the console log is appended to d3_console.log only after a run with exit 0; a failed run writes nothing to --out-dir "
    "(neither the JSON nor the console log), so the repository log holds only completed runs (section 9)",
    "summaries also give dS, the summed dW and SE beside the plan's statistics"]


# ---------------------------------------------------------------- helpers
def stats(xs):
    x = np.array([v for v in xs if v is not None], float)
    if not x.size:
        return {"n": 0}
    return {"n": int(x.size), "mean": float(x.mean()), "median": float(np.median(x)), "min": float(x.min()),
            "max": float(x.max()), "se": float(x.std(ddof=1) / np.sqrt(x.size)) if x.size > 1 else None}


def mean(xs):
    x = [v for v in xs if v is not None]
    return float(np.mean(x)) if x else None


def median(xs):
    x = [v for v in xs if v is not None]
    return float(np.median(x)) if x else None


def wq(v):
    """A work quantity at n = 8, 4, 2, 1: error estimate, Richardson value, convergence ratio."""
    d = v[8] - v[4]
    return {"n8": v[8], "n4": v[4], "n2": v[2], "n1": v[1], "abs_8_minus_4": abs(d), "e": abs(d) / 3,
            "richardson": v[8] + d / 3, "ratio_2_4_over_4_8": (v[2] - v[4]) / (v[4] - v[8]) if v[4] != v[8] else None}


def ratio_c(c):
    return c[4] / c[8] if c[8] != 0 else None


def in_range(r):
    return r is not None and RATIO_LO <= r <= RATIO_HI


def git(*args):
    r = subprocess.run(["git", "-C", ROOT, *args], capture_output=True)
    return r.returncode, r.stdout


class Tee(a44.Tee):
    """scripts/44 Tee (terminal and console log, local paths replaced by <repo> and ~), except that the log text is held in
    memory and appended to the console log only by commit(), after a run that ends with exit 0. A failed run therefore
    writes nothing to --out-dir; its console output is on stdout only."""
    def __init__(self, path):
        self.path, self.out, self.f = path, sys.stdout, io.StringIO()
        self.sub = [(x, y) for p, y in ((a44.ROOT, "<repo>"), (os.path.expanduser("~"), "~"))
                    for x in dict.fromkeys((os.path.abspath(p), os.path.realpath(p)))]

    def commit(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "a") as f:
            f.write(self.f.getvalue())


# ---------------------------------------------------------------- check 2: the plan
def plan_check():
    path = os.path.join(ROOT, PLAN)
    require(os.path.isfile(path), EXIT_PLAN, f"{PLAN}: no such file")
    rc, out = git("log", "-1", "--format=%H", "--", PLAN)
    commit = out.decode().strip()
    require(rc == 0 and len(commit) == 40, EXIT_PLAN, f"{PLAN} is not committed (git log rc {rc})")
    rc, head = git("rev-parse", "HEAD")
    rc2, st = git("status", "--porcelain", "--", PLAN)
    require(rc == 0 and rc2 == 0, EXIT_PLAN, "git rev-parse / status failed")
    work = open(path, "rb").read()
    rc3, at_commit = git("show", f"{commit}:{PLAN}")
    rc4, at_head = git("show", f"HEAD:{PLAN}")
    res = {"file": PLAN, "commit": commit, "head": head.decode().strip(), "sha256": a39.sha256(path),
           "status_porcelain": st.decode().strip(), "identical_to_commit": rc3 == 0 and work == at_commit,
           "identical_to_head": rc4 == 0 and work == at_head, "expected_commit": PLAN_COMMIT}
    require(not res["status_porcelain"], EXIT_PLAN, f"{PLAN} has local changes: {res['status_porcelain']}")
    require(res["identical_to_commit"] and res["identical_to_head"], EXIT_PLAN,
            f"{PLAN} differs from its commit {commit[:12]} or from HEAD")
    require(commit == PLAN_COMMIT, EXIT_PLAN, f"{PLAN} last committed at {commit[:12]}, not at {PLAN_COMMIT[:12]} (the "
            "commit this script implements)")
    res["pass"] = True
    return res


# ---------------------------------------------------------------- band geometry
class Band:
    """One band: images, segment displacements, path points, groups, molecules, hop midpoint."""
    def __init__(self, h, s, split, geo, bands_dir):
        self.h, self.s, self.split, self.key = h, s, split, f"{h}_{s}"
        self.file = os.path.join(bands_dir, f"band_{s}_{h}.extxyz")
        self.fr = geo.band_file(h, s)
        self.at0 = self.fr[0]
        self.cell = self.at0.cell.array
        self.sym = np.array(self.at0.get_chemical_symbols())
        self.N = len(self.at0)
        self.P = {i: np.array(f.positions, dtype=np.float64) for i, f in enumerate(self.fr)}
        self.lab = {i: f"{self.key}_img{i}" for i in range(len(self.fr))}

    def check3(self):
        """Plan check 3 (exit 5)."""
        fr = self.fr
        require(len(fr) == 7, EXIT_DATA, f"{self.key}: {len(fr)} frames, not 7")
        dc = max(float(np.abs(f.cell.array - self.cell).max()) for f in fr)
        same_sp = all(f.get_chemical_symbols() == list(self.sym) for f in fr)
        require(dc <= TOL_CELL and same_sp, EXIT_DATA, f"{self.key}: cell differs by {dc:.1e} A or species differ")
        steps = {}
        for a, b in CHECK_STEPS:
            raw = self.P[b] - self.P[a]
            mic = find_mic(raw, self.cell, pbc=True)[0]
            x = {"mic_minus_raw_A": float(np.abs(mic - raw).max()), "max_abs_dr_A": float(np.linalg.norm(mic, axis=1).max()),
                 "start_plus_dr_minus_end_A": float(np.abs(self.P[a] + mic - self.P[b]).max())}
            x["pass"] = x["mic_minus_raw_A"] <= TOL_MIC and x["max_abs_dr_A"] < MAX_STEP and x["start_plus_dr_minus_end_A"] <= TOL_MIC
            steps[f"{a}-{b}"] = x
        bad = [k for k, x in steps.items() if not x["pass"]]
        require(not bad, EXIT_DATA, f"{self.key}: check 3 fails at steps {bad}: {[steps[k] for k in bad]}")
        self.D = {k: find_mic(self.P[b] - self.P[a], self.cell, pbc=True)[0] for k, (a, b) in SEGS.items()}
        self.seglabs = {k: [self.lab[a]] + [f"{self.key}_{a}{b}_j{j}" for j in range(1, 8)] + [self.lab[b]]
                        for k, (a, b) in SEGS.items()}
        return {"n_frames": len(fr), "max_cell_diff_A": dc, "species_identical": same_sp, "steps": steps, "pass": True}

    def pos(self, k, j):
        a, b = SEGS[k]
        return self.P[a] if j == 0 else self.P[b] if j == 8 else self.P[a] + (j / 8) * self.D[k]

    def points(self):
        """label -> positions of the 33 single-point geometries (images 0-4, then the interior points)."""
        out = {self.lab[i]: self.P[i] for i in range(5)}
        for k in SEGS:
            for j in range(1, 8):
                out[self.seglabs[k][j]] = self.pos(k, j)
        return out

    def atoms(self, positions):
        return Atoms(numbers=self.at0.numbers, positions=positions, cell=self.at0.cell, pbc=self.at0.pbc)

    def setup_groups(self):
        self.g, self.ginfo = a44.groups(self.fr[0], self.fr[6])
        hop = self.ginfo["hop_I_index"]
        self.midp = self.P[0][hop] + 0.5 * find_mic(self.P[6][hop] - self.P[0][hop], self.cell, pbc=True)[0]
        self.d0 = find_mic(self.P[0] - self.midp, self.cell, pbc=True)[1]
        inorg = np.flatnonzero(~np.isin(self.sym, list(a44.ORGANIC)))
        assert set(self.g["inorganic_near"]) | {hop} == set(inorg[self.d0[inorg] < R_CUT]), f"{self.key}: midpoint recomputation"
        self.mols = {int(c): a38.molecule(self.at0, int(c), self.sym, self.cell)[0] for c in np.flatnonzero(self.sym == "C")}
        self.grp_of = np.empty(self.N, dtype=object)
        for gname, idx in self.g.items():
            self.grp_of[idx] = gname

    def paths(self, istar):
        P = ["0-1", "1-2"] + (["2-3"] if istar == 3 else [])
        C = ["0-2"] + (["2-3"] if istar == 3 else [])
        ext = {"P_ext": ["0-1", "1-2", "2-3"], "C_ext": ["0-2", "2-3"]} if istar == 2 else {}
        return {"P": P, "C": C}, ext

    def path_labels(self, segs):
        out = []
        for k in segs:
            out += self.seglabs[k] if not out else self.seglabs[k][1:]
        return out


def molecule_check(b, labels, pts):
    """Plan check 8: scripts/38 molecule() of every image-0 C returns the same atoms at every listed point (exit 7)."""
    bad = []
    for l in labels:
        at = b.atoms(pts[l])
        for c, mol in b.mols.items():
            m, _ = a38.molecule(at, c, b.sym, b.cell)          # asserts the (2 N, 8) / (3 N, 10) composition
            if m != mol:
                bad.append((l, c))
    require(not bad, EXIT_ERROR, f"{b.key}: molecule partition changes at {bad[:5]}")
    return len(labels)


def geom_metrics(b, positions):
    """(shortest intramolecular distance, shortest pair distance), minimum image, A."""
    d = b.atoms(positions).get_all_distances(mic=True)
    intra = min(float(d[np.ix_(m, m)][np.triu_indices(len(m), 1)].min()) for m in b.mols.values())
    np.fill_diagonal(d, np.inf)
    return intra, float(d.min())


# ---------------------------------------------------------------- single points
class Evaluator:
    """Single points of one model arm (scripts/39 Arm: float64/CPU asserted): energy, forces, per-atom 'energies'."""
    def __init__(self, arm):
        self.arm, self.calc = arm, arm.calc
        self.e0 = a44.atomic_energies(arm.calc.models[0])
        self.E, self.F, self.eps = {}, {}, {}
        self.n, self.max_e0_dev, self.max_sum_dev, self.min_abs_e0 = 0, 0.0, 0.0, float("inf")   # min |E0| of the atoms evaluated

    def __call__(self, label, atoms):
        require(label not in self.E, EXIT_ERROR, f"{self.arm.name}: {label} evaluated twice")
        at = atoms.copy(); at.set_constraint(); at.calc = self.calc
        E = float(at.get_potential_energy()); F = np.array(at.get_forces(), dtype=np.float64)
        r = self.calc.results
        require(PER_ATOM in r and "node_energy" in r, EXIT_ERROR, f"{self.arm.name}: calculator results lack "
                f"'{PER_ATOM}' or 'node_energy': {sorted(r)}")
        eps = np.array(r[PER_ATOM], dtype=np.float64)
        e0 = np.array([self.e0[int(z)] for z in at.numbers])
        dev = float(np.abs(eps - np.asarray(r["node_energy"], dtype=np.float64) - e0).max())
        sdev = abs(float(eps.sum()) - E)
        require(np.isfinite(E) and np.all(np.isfinite(F)) and np.all(np.isfinite(eps)), EXIT_ERROR,
                f"{self.arm.name} {label}: non-finite result")
        require(dev <= TOL_E0, EXIT_ERROR, f"{self.arm.name} {label}: '{PER_ATOM}' - 'node_energy' differs from the E0s by "
                f"{dev:.2e} eV (the property used must be '{PER_ATOM}', which keeps the E0s)")
        require(sdev <= TOL_SITE, EXIT_ERROR, f"{self.arm.name} {label}: sum of '{PER_ATOM}' differs from E by {sdev:.2e} eV")
        self.max_e0_dev, self.max_sum_dev = max(self.max_e0_dev, dev), max(self.max_sum_dev, sdev)
        self.min_abs_e0 = min(self.min_abs_e0, float(np.abs(e0).min()))
        self.E[label], self.F[label], self.eps[label] = E, F, eps
        self.n += 1
        return E


# ---------------------------------------------------------------- D3 quantities
def seg_work(F, b, k, n):
    """Per-atom work (meV) along segment k at n intervals (trapezoid; step dr_k/n)."""
    labs, s = b.seglabs[k], 8 // n
    idx = list(range(0, 9, s))
    step = b.D[k] / n
    w = np.zeros(b.N)
    for j0, j1 in zip(idx[:-1], idx[1:]):
        w -= 0.5 * np.einsum("ij,ij->i", F[labs[j0]] + F[labs[j1]], step)
    return w * 1000.0


def path_quantities(b, segs, ev, istar_end):
    """D3a and D3b of one path (list of segments) ending at image istar_end."""
    end = SEGS[segs[-1]][1]
    assert end == istar_end and SEGS[segs[0]][0] == 0, (b.key, segs, istar_end)
    sw = {m: {k: {n: seg_work(ev[m].F, b, k, n) for n in NS} for k in segs} for m in MODELS}
    pw = {m: {n: sum(sw[m][k][n] for k in segs) for n in NS} for m in MODELS}
    E = {m: ev[m].E for m in MODELS}
    dEseg = {m: {k: (E[m][b.lab[SEGS[k][1]]] - E[m][b.lab[SEGS[k][0]]]) * 1000 for k in segs} for m in MODELS}
    dE = {m: (E[m][b.lab[end]] - E[m][b.lab[0]]) * 1000 for m in MODELS}
    dS = dE["finetuned"] - dE["zeroshot"]
    d3a = {}
    for m in MODELS:
        segrec = {}
        for k in segs:
            c = {n: float(sw[m][k][n].sum()) - dEseg[m][k] for n in NS}
            segrec[k] = {"W": wq({n: float(sw[m][k][n].sum()) for n in NS}), "dE_meV": dEseg[m][k], "closure_meV": c,
                         "closure4_over_closure8": ratio_c(c)}
        c = {n: float(pw[m][n].sum()) - dE[m] for n in NS}
        d3a[m] = {"segments": segrec,
                  "total": {"W": wq({n: float(pw[m][n].sum()) for n in NS}), "dE_meV": dE[m], "closure_meV": c,
                            "closure4_over_closure8": ratio_c(c)},
                  "groups": {g: wq({n: float(pw[m][n][idx].sum()) for n in NS}) for g, idx in b.g.items()}}
    dw = {n: pw["finetuned"][n] - pw["zeroshot"][n] for n in NS}
    dW = {g: wq({n: float(dw[n][idx].sum()) for n in NS}) for g, idx in b.g.items()}
    dW["total"] = wq({n: float(dw[n].sum()) for n in NS})
    # identity (plan D3b): sum_g dW_g = W_FT - W_ZS; (sum - dS) = closure_FT - closure_ZS; 1e-9 meV at every n
    id1 = max(abs(sum(dW[g][f"n{n}"] for g in GROUPS) - (d3a["finetuned"]["total"]["W"][f"n{n}"] -
                                                         d3a["zeroshot"]["total"]["W"][f"n{n}"])) for n in NS)
    id2 = max(abs((sum(dW[g][f"n{n}"] for g in GROUPS) - dS) - (d3a["finetuned"]["total"]["closure_meV"][n] -
                                                                d3a["zeroshot"]["total"]["closure_meV"][n])) for n in NS)
    require(id1 <= TOL_ID and id2 <= TOL_ID, EXIT_ERROR, f"{b.key} {segs}: work identity fails ({id1:.2e}, {id2:.2e} meV)")
    # displacement share D_g over the n = 8 steps
    dsq = sum(8 * np.sum((b.D[k] / 8) ** 2, axis=1) for k in segs)
    Dg = {g: float(dsq[idx].sum() / dsq.sum()) for g, idx in b.g.items()}
    comp = {}
    for g in GROUPS:
        wz, wf, x = d3a["zeroshot"]["groups"][g], d3a["finetuned"]["groups"][g], dW[g]
        comp[g] = {"dW": {"richardson": x["richardson"], "e": x["e"]},
                   "W_ZS": {"richardson": wz["richardson"], "e": wz["e"]},
                   "W_FT": {"richardson": wf["richardson"], "e": wf["e"]}, "D": Dg[g],
                   "ratio_dW_over_W_ZS": x["richardson"] / wz["richardson"] if abs(wz["richardson"]) >= W_ZS_MIN else None}
    L = sum(dW[g]["richardson"] for g in LOCAL)
    Nn = sum(dW[g]["richardson"] for g in GROUPS if g not in LOCAL)
    kappa = {"L_meV": L, "N_meV": Nn, "kappa": (abs(L) + abs(Nn)) / abs(L + Nn) if L + Nn != 0 else None,
             "dS_meV": dS, "note": "ill-conditioned where |dS| is small"}
    d3b = {"dW": dW, "dS_meV": dS, "identity_max_abs_diff_meV": {"sum_vs_W_FT_minus_W_ZS": id1,
                                                                 "closure_of_sum_vs_closure_FT_minus_ZS": id2},
           "comparators": comp, "kappa": kappa}
    return {"segments": segs, "end_image": end, "D3a": d3a, "D3b": d3b}, pw


def criteria(q):
    """Plan section 6 criteria 1-2 on one path record."""
    failed, rows = [], {"1": {}, "2": {}}
    for m in MODELS:
        t = q["D3a"][m]["total"]
        c8, r = t["closure_meV"][8], t["closure4_over_closure8"]
        ok_c, ex = abs(c8) <= CLOSURE_MAX, abs(c8) < CLOSURE_EXEMPT
        ok_r = ex or in_range(r)
        rows["1"][m] = {"closure8_meV": c8, "closure4_over_closure8": r, "abs_closure8_le_2": ok_c,
                        "ratio_exempt_abs_closure8_lt_0p5": ex, "ratio_in_2_8_or_exempt": ok_r}
        if not ok_c:
            failed.append(f"1 {m}: |closure8| = {abs(c8):.2f} > 2 meV")
        if not ok_r:
            failed.append(f"1 {m}: closure4/closure8 = {a39.num(r, '.2f')} not in [2, 8]")
    for g in GROUPS:
        x = q["D3b"]["dW"][g]
        d, r = x["abs_8_minus_4"], x["ratio_2_4_over_4_8"]
        ok_e, ex = d <= DW_MAX, d < DW_EXEMPT
        ok_r = ex or in_range(r)
        rows["2"][g] = {"abs_8_minus_4_meV": d, "e_meV": x["e"], "ratio_2_4_over_4_8": r, "abs_8_minus_4_le_3": ok_e,
                        "ratio_exempt_lt_0p3": ex, "ratio_in_2_8_or_exempt": ok_r}
        if not ok_e:
            failed.append(f"2 {g}: |dW8 - dW4| = {d:.2f} > 3 meV")
        if not ok_r:
            failed.append(f"2 {g}: (dW2 - dW4)/(dW4 - dW8) = {a39.num(r, '.2f')} not in [2, 8]")
    return {"meets": not failed, "failed": failed, "values": rows}


def criteria_values(q):
    """The numbers to which criteria 1-2 apply, for the 2 -> 3 extension: no status, no 'meets', 'failed' or per-criterion
    pass/fail flag (the extension is outside every criterion, plan section 3)."""
    v = criteria(q)["values"]
    return {c: {w: {k: x for k, x in row.items() if not isinstance(x, bool)} for w, row in rows.items()} for c, rows in v.items()}


def hermite(ev, b, k):
    """D3d: excess of E over the cubic Hermite interpolant on segment k, and the excess over the higher image (meV)."""
    labs, out = b.seglabs[k], {}
    for m in MODELS:
        E, F = ev[m].E, ev[m].F
        Ea, Eb = E[labs[0]], E[labs[8]]
        m0, m1 = -float(np.sum(F[labs[0]] * b.D[k])), -float(np.sum(F[labs[8]] * b.D[k]))
        ex, ab = [], []
        for j in range(1, 8):
            t = j / 8
            H = (2 * t**3 - 3 * t**2 + 1) * Ea + (t**3 - 2 * t**2 + t) * m0 + (-2 * t**3 + 3 * t**2) * Eb + (t**3 - t**2) * m1
            ex.append((E[labs[j]] - H) * 1000); ab.append((E[labs[j]] - max(Ea, Eb)) * 1000)
        out[m] = {"hermite_excess_meV": max(ex), "j_at_hermite_excess": 1 + int(np.argmax(ex)),
                  "above_higher_image_meV": max(ab), "j_at_above_higher_image": 1 + int(np.argmax(ab)),
                  "dE_dlambda_start_eV": m0, "dE_dlambda_end_eV": m1}
    return out


def geometry_d3d(b, paths, pts, istar):
    """D3d geometry along P and C to i* (model-independent) and the 6 A crossings along P."""
    cache, out = {}, {}

    def gm(l):
        if l not in cache:
            cache[l] = geom_metrics(b, pts[l])
        return cache[l]
    for name, segs in paths.items():
        imgs = [0] + [SEGS[k][1] for k in segs]
        im = {i: dict(zip(("shortest_intramolecular_A", "shortest_pair_A"), gm(b.lab[i]))) for i in imgs}
        mi = min(x["shortest_intramolecular_A"] for x in im.values()); mp = min(x["shortest_pair_A"] for x in im.values())
        sg = {}
        for k in segs:
            nrm = np.linalg.norm(b.D[k], axis=1)
            vals = [gm(b.seglabs[k][j]) for j in range(1, 8)]
            ji, jp = int(np.argmin([v[0] for v in vals])), int(np.argmin([v[1] for v in vals]))
            sg[k] = {"max_atom_displacement_A": float(nrm.max()), "atom": int(nrm.argmax()), "symbol": str(b.sym[nrm.argmax()]),
                     "group": b.grp_of[nrm.argmax()],
                     "interior_shortest_intramolecular_A": vals[ji][0], "j_intramolecular": ji + 1,
                     "interior_shortest_pair_A": vals[jp][1], "j_pair": jp + 1,
                     "by_j_shortest_intramolecular_A": [v[0] for v in vals], "by_j_shortest_pair_A": [v[1] for v in vals],
                     "images_shortest_intramolecular_A": mi, "images_shortest_pair_A": mp,
                     "interior_minus_images_intramolecular_A": vals[ji][0] - mi, "interior_minus_images_pair_A": vals[jp][1] - mp}
        out[name] = {"images": im, "segments": sg}
    near0, cross = b.d0 < R_CUT, np.zeros(b.N, bool)
    for l in b.path_labels(paths["P"]):
        d = find_mic(pts[l] - b.midp, b.cell, pbc=True)[1]
        cross |= (d < R_CUT) != near0
    idx = np.flatnonzero(cross)
    out["crossings_6A_P"] = {"n_atoms": int(idx.size), "atoms": [{"index": int(i), "symbol": str(b.sym[i]), "group": b.grp_of[i],
                                                                  "d_image0_A": float(b.d0[i])} for i in idx]}
    return out


def site_energy(b, ev, end):
    d = {}
    for g, idx in b.g.items():
        d[g] = float(sum(((ev[m].eps[b.lab[end]][idx] - ev[m].eps[b.lab[0]][idx]).sum()) * (1 if m == "finetuned" else -1)
                         for m in MODELS) * 1000)
    dS = ((ev["finetuned"].E[b.lab[end]] - ev["finetuned"].E[b.lab[0]]) - (ev["zeroshot"].E[b.lab[end]] - ev["zeroshot"].E[b.lab[0]])) * 1000
    dev = abs(sum(d.values()) - dS)
    require(dev <= TOL_SITE * 1000, EXIT_ERROR, f"{b.key}: sum_g d_eps_g - dS = {dev:.2e} meV > 1e-6 eV")
    return {"d_eps_meV": d, "sum_meV": sum(d.values()), "dS_meV": dS, "sum_minus_dS_meV": sum(d.values()) - dS}


def ea_link(b, ev, istar):
    E = {m: {i: ev[m].E[b.lab[i]] for i in range(5)} for m in MODELS}
    out = {}
    for m in MODELS:
        L = {i: b.lab[i] for i in range(5)}
        i_m = a44.argmax(ev[m].E, L)
        out[m] = {"i_star_own": i_m, "Ea_meV": (E[m][i_m] - E[m][0]) * 1000}
    dS = ((E["finetuned"][istar] - E["finetuned"][0]) - (E["zeroshot"][istar] - E["zeroshot"][0])) * 1000
    tf = (E["finetuned"][out["finetuned"]["i_star_own"]] - E["finetuned"][istar]) * 1000
    tz = (E["zeroshot"][out["zeroshot"]["i_star_own"]] - E["zeroshot"][istar]) * 1000
    ch = out["finetuned"]["Ea_meV"] - out["zeroshot"]["Ea_meV"]
    dev = abs(ch - (dS + tf - tz))
    require(dev <= TOL_ID, EXIT_ERROR, f"{b.key}: E_a link identity fails by {dev:.2e} meV")
    return {**out, "Ea_change_meV": ch, "dS_meV": dS, "term_FT_own_minus_istar_meV": tf, "term_ZS_own_minus_istar_meV": tz,
            "identity_abs_diff_meV": dev, "argmax_differs": [m for m in MODELS if out[m]["i_star_own"] != istar]}


# ---------------------------------------------------------------- summaries
def subset_summary(R, n_res_all):
    """Plan section 7 items 1-7 and the sign comparison over the band records R (resolved bands)."""
    n = len(R)
    if not n:
        return {"n": 0}
    P = lambda r: r["paths"]["P"]
    out = {"n": n, "label": "few resolved bands" if n_res_all < FEW else None, "bands": [r["band"] for r in R]}
    out["item1_dW"] = {g: {**stats(P(r)["D3b"]["dW"][g]["richardson"] for r in R),
                           "mean_abs_8_minus_4": mean(P(r)["D3b"]["dW"][g]["abs_8_minus_4"] for r in R)}
                       for g in GROUPS + ("total",)}
    out["item1_dW"]["dS"] = stats(r["dS_meV"] for r in R)
    out["item2_d_eps"] = {g: stats(r["D3c"]["d_eps_meV"][g] for r in R) for g in GROUPS}
    it3 = {}
    for g in GROUPS:
        c = [P(r)["D3a"] for r in R]
        rat = [P(r)["D3b"]["comparators"][g]["ratio_dW_over_W_ZS"] for r in R]
        rs = stats(rat)
        it3[g] = {"W_ZS": {"mean": mean(x["zeroshot"]["groups"][g]["richardson"] for x in c),
                           "mean_abs_8_minus_4": mean(x["zeroshot"]["groups"][g]["abs_8_minus_4"] for x in c)},
                  "W_FT": {"mean": mean(x["finetuned"]["groups"][g]["richardson"] for x in c),
                           "mean_abs_8_minus_4": mean(x["finetuned"]["groups"][g]["abs_8_minus_4"] for x in c)},
                  "n_bands_e_W_ZS_or_W_FT_above_1meV": sum(x["zeroshot"]["groups"][g]["e"] > E_COMP or
                                                           x["finetuned"]["groups"][g]["e"] > E_COMP for x in c),
                  "median_D": median(P(r)["D3b"]["comparators"][g]["D"] for r in R),
                  "ratio_dW_over_W_ZS_where_abs_W_ZS_ge_5meV": {k: rs.get(k) for k in ("n", "median", "min", "max")}}
    out["item3_comparators"] = it3
    RC = [r for r in R if r["status_C"] == "resolved"]
    it4 = {"n_both_resolved": len(RC), "bands": [r["band"] for r in RC]}
    for g in GROUPS:
        if not RC:
            break
        d = [P(r)["D3b"]["dW"][g]["richardson"] - r["paths"]["C"]["D3b"]["dW"][g]["richardson"] for r in RC]
        it4[g] = {"mean_abs_diff_meV": mean(abs(x) for x in d), "max_abs_diff_meV": max(abs(x) for x in d),
                  "mean_signed_diff_meV": mean(d),
                  "mean_e_P_plus_e_C_meV": mean(P(r)["D3b"]["dW"][g]["e"] + r["paths"]["C"]["D3b"]["dW"][g]["e"] for r in RC),
                  "mean_abs_8_minus_4_P_plus_C_meV": mean(P(r)["D3b"]["dW"][g]["abs_8_minus_4"] +
                                                          r["paths"]["C"]["D3b"]["dW"][g]["abs_8_minus_4"] for r in RC)}
    out["item4_path_dependence"] = it4
    it5 = {"n": n, "n_C_not_resolved": sum(r["status_C"] != "resolved" for r in R)}
    for g in GROUPS:
        c = [r["paths"]["C"]["D3b"]["dW"][g]["richardson"] - r["D2b_groups_meV_seen"][g] for r in R]
        p = [P(r)["D3b"]["dW"][g]["richardson"] - r["D2b_groups_meV_seen"][g] for r in R]
        it5[g] = {"C_R_minus_D2b": {"median_meV": median(c), "max_abs_meV": max(abs(x) for x in c)},
                  "P_R_minus_D2b": {"median_meV": median(p), "max_abs_meV": max(abs(x) for x in p)}}
    out["item5_seen_coarse_vs_converged"] = it5
    k = [P(r)["D3b"]["kappa"]["kappa"] for r in R]
    out["item6_kappa"] = {"n_defined": sum(x is not None for x in k), "median": median(k),
                          "n_above_2": sum(x is not None and x > KAPPA_HI for x in k)}
    out["item7_D3a"] = {p: {m: {"median_abs_closure8_meV": median(abs(r["paths"][p]["D3a"][m]["total"]["closure_meV"][8]) for r in R),
                                "max_abs_closure8_meV": max(abs(r["paths"][p]["D3a"][m]["total"]["closure_meV"][8]) for r in R),
                                "median_closure4_over_closure8": median(r["paths"][p]["D3a"][m]["total"]["closure4_over_closure8"] for r in R)}
                            for m in MODELS} for p in ("P", "C")}
    sc = {}
    for g in GROUPS:
        w, e = out["item1_dW"][g], out["item2_d_eps"][g]
        if n < 2:
            sc[g] = {"statement": "sign not resolved", "why": "n < 2: standard error undefined", "mean_dW_meV": w["mean"],
                     "mean_d_eps_meV": e["mean"]}
            continue
        mw = max(MARGIN_MIN, 2 * w["se"]) + w["mean_abs_8_minus_4"]
        me = max(MARGIN_MIN, 2 * e["se"])
        ok = abs(w["mean"]) > mw and abs(e["mean"]) > me
        sc[g] = {"mean_dW_meV": w["mean"], "se_dW_meV": w["se"], "mean_abs_8_minus_4_meV": w["mean_abs_8_minus_4"],
                 "margin_dW_meV": mw, "mean_d_eps_meV": e["mean"], "se_d_eps_meV": e["se"], "margin_d_eps_meV": me,
                 "statement": ("agree" if np.sign(w["mean"]) == np.sign(e["mean"]) else "disagree") if ok else "sign not resolved"}
    out["sign_comparison"] = sc
    cnt = {r["band"]: sum(np.sign(P(r)["D3b"]["dW"][g]["richardson"]) == np.sign(r["D3c"]["d_eps_meV"][g]) for g in GROUPS)
           for r in R}
    cnt = {k: int(v) for k, v in cnt.items()}
    out["per_band_groups_sign_agree"] = {"counts": cnt, "histogram": {str(i): sum(v == i for v in cnt.values()) for i in range(6)}}
    return out


def mean_of_means(rows):
    """Mean over hosts of every statistic named mean* (rows: per-host summaries with n > 0)."""
    def rec(xs):
        out = {}
        keys = dict.fromkeys(k for x in xs if isinstance(x, dict) for k in x
                             if k not in ("sign_comparison", "per_band_groups_sign_agree"))
        for k in keys:
            vals = [x[k] for x in xs if isinstance(x, dict) and k in x]
            if k.startswith("mean") and all(isinstance(v, (int, float)) or v is None for v in vals):
                v = [y for y in vals if y is not None]
                if v:
                    out[k] = {"mean_of_host_means": float(np.mean(v)), "n_hosts": len(v)}
            elif any(isinstance(v, dict) for v in vals):
                r = rec([v for v in vals if isinstance(v, dict)])
                if r:
                    out[k] = r
        return out
    rows = [r for r in rows if r.get("n")]
    return {"n_hosts": len(rows), **rec(rows)} if rows else {"n_hosts": 0}


# ---------------------------------------------------------------- main computation
def d3(a, data, M, d2, checks):
    """The whole D3 plan; checks holds checks 1 (packages) and 2 (plan) of main() and is completed here."""
    bandsel = a.bands_only
    print("\n==== D3: dense-path attribution of the segment change (post hoc, descriptive)")
    B = [x for x in a44.bands37() if bandsel is None or f"{x[0]}_{x[1]}" in bandsel]
    if bandsel is not None:
        require(len(B) == len(set(bandsel)), 2, f"--bands-only: unknown bands {sorted(set(bandsel) - {f'{h}_{s}' for h, s, _ in B})}")
    # ---- check 3: band files
    bands, c3 = {}, {}
    for h, s, sp in B:
        b = Band(h, s, sp, data.geo, a.bands)
        c3[b.key] = b.check3()
        bands[b.key] = b
    band_sha = {k: {"file": rel(b.file), "sha256": a39.sha256(b.file)} for k, b in bands.items()}
    checks["3_band_files"] = {"pass": True, "n_bands": len(bands),
                              "max_mic_minus_raw_A": max(x["mic_minus_raw_A"] for c in c3.values() for x in c["steps"].values()),
                              "max_step_A": max(x["max_abs_dr_A"] for c in c3.values() for x in c["steps"].values()),
                              "max_start_plus_dr_minus_end_A": max(x["start_plus_dr_minus_end_A"] for c in c3.values()
                                                                   for x in c["steps"].values()),
                              "max_cell_diff_A": max(c["max_cell_diff_A"] for c in c3.values()),
                              "tol": {"mic_A": TOL_MIC, "step_A": MAX_STEP, "cell_A": TOL_CELL}}
    print(f"  check 3 (band files): {len(bands)} bands, 7 frames, same cell and species; steps 0-1..3-4 and 0-2: max "
          f"|mic - raw| {checks['3_band_files']['max_mic_minus_raw_A']:.1e} A, max |dr| {checks['3_band_files']['max_step_A']:.3f} "
          f"A (< 2), max |r + dr - r_end| {checks['3_band_files']['max_start_plus_dr_minus_end_A']:.1e} A  PASS")
    # ---- check 4: images 0, 2, 3, 4, 6 against the dataset (scripts/44 cross-check)
    labs5 = [l for h, s, _ in B for l in a39.band_labels(h, s)]
    xc = data.need(labs5)
    checks["4_image_geometry_vs_dataset"] = xc
    print(f"  check 4 (scripts/44 cross-check), {a44.fmt_check(xc)}  PASS")
    # ---- i*, groups and molecules (geometry only)
    istar, d2b = {}, {}
    rep_geo = []
    for k, b in bands.items():
        L = dict(zip(a39.IMG, a39.band_labels(b.h, b.s)))
        i = a44.argmax({l: data.ds[l].info["REF_energy_raw"] for l in L.values()}, L)
        istar[k] = i
        ref = d2["bands"][k]
        rep_geo.append({"band": k, "what": "i_star (REF_energy_raw) vs D2a.dft.i_star", "ok": i == ref["D2a"]["dft"]["i_star"]
                        and i == ref["D2b"]["i_star_dft"], "ours": i, "ref": ref["D2a"]["dft"]["i_star"]})
        b.setup_groups()
        rep_geo.append({"band": k, "what": "groups hop_I_index and n_atoms", "ok": b.ginfo["hop_I_index"] == ref["groups"]["hop_I_index"]
                        and b.ginfo["n_atoms"] == ref["groups"]["n_atoms"], "ours": b.ginfo["hop_I_index"], "ref": ref["groups"]["hop_I_index"]})
        d2b[k] = ref["D2b"]["groups_meV"]
    bad = [r for r in rep_geo if not r["ok"]]
    require(not bad, EXIT_REPRO, f"check 6 (i*, groups) fails: {bad[:5]}")
    require(set(istar.values()) <= {2, 3} and {k for k, v in istar.items() if v == 2} == (I_STAR_2 & set(bands)), EXIT_REPRO,
            f"i* = 2 bands {sorted(k for k, v in istar.items() if v == 2)} are not {sorted(I_STAR_2 & set(bands))}")
    print(f"  check 6 (part): i* from REF_energy_raw = D2's in {len(bands)} bands (i* = 2: "
          f"{sorted(k for k, v in istar.items() if v == 2)}); hop_I index and group sizes = D2's  PASS")
    pts, nmol, extra_mol = {}, 0, {}
    for k, b in bands.items():
        pts[k] = b.points()
        paths, ext = b.paths(istar[k])
        ml = list(dict.fromkeys(l for segs in list(paths.values()) + list(ext.values()) for l in b.path_labels(segs)))
        nmol += molecule_check(b, ml, pts[k])
        try:
            molecule_check(b, [b.lab[4]], pts[k]); extra_mol[k] = True
        except (Stop, AssertionError):                       # beside only, not gated
            extra_mol[k] = False
    checks["8_molecules"] = {"pass": True, "n_points_checked": nmol, "rule": "scripts/38 molecule() of every image-0 C returns "
                             "the same atoms at every image 0..i* and interior point of P and C (and of the extension)",
                             "image4_beside_unchanged": extra_mol}
    print(f"  check 8 (molecules): partition unchanged at {nmol} path points of P, C and the extensions  PASS "
          f"(beside, image 4 unchanged in {sum(extra_mol.values())} of {len(extra_mol)})")
    # ---- check 1 (models) and the image single points
    zs, ft = M.zeroshot(), M.finetuned()
    mf = d2["model_files"]
    require(zs.sha == mf["zeroshot"]["sha256"] == a39.FOUNDATION_SHA256 and ft.sha == mf["finetuned"]["sha256"] == a44.MODEL_SHA256,
            EXIT_SHA, f"model sha256 differ from D2's: zero-shot {zs.sha[:12]}, fine-tuned {ft.sha[:12]}")
    checks["1_models_and_packages"]["model_sha256"] = {"zeroshot": zs.sha, "finetuned": ft.sha, "equal_to_D2": True}
    print(f"  check 1 (models): sha256 zero-shot {zs.sha[:12]}, fine-tuned {ft.sha[:12]} = D2's model_files  PASS")
    ev = {"zeroshot": Evaluator(zs), "finetuned": Evaluator(ft)}
    t0 = time.time()
    for k, b in bands.items():
        for i in range(5):
            for m in MODELS:
                ev[m](b.lab[i], b.atoms(pts[k][b.lab[i]]))
    print(f"  single points at images 0-4: {sum(e.n for e in ev.values())} ({time.time() - t0:.0f} s)")
    # ---- check 5: stored zero-shot values
    w5 = {"energy_eV": 0.0, "per_atom_energies_eV": 0.0, "forces_eVA_reported": 0.0}
    fails = []
    for k, b in bands.items():
        for i in range(5):
            l, fr = b.lab[i], b.fr[i]
            dE = abs(ev["zeroshot"].E[l] - data.geo.stored_energy(l))
            de = float(np.abs(ev["zeroshot"].eps[l] - np.asarray(fr.calc.results["energies"])).max())
            dF = float(np.abs(ev["zeroshot"].F[l] - np.asarray(fr.calc.results["forces"])).max())
            w5 = {"energy_eV": max(w5["energy_eV"], dE), "per_atom_energies_eV": max(w5["per_atom_energies_eV"], de),
                  "forces_eVA_reported": max(w5["forces_eVA_reported"], dF)}
            if not (dE <= TOL_STORED and de <= TOL_STORED):
                fails.append(f"{l}: |dE| {dE:.2e}, max |d eps| {de:.2e} eV")
    checks["5_stored_zeroshot"] = {"n_frames": 5 * len(bands), "max_abs_diff": w5, "tol_eV": TOL_STORED, "failures": fails,
                                   "pass": not fails}
    require(not fails, EXIT_DATA, f"check 5 (stored zero-shot values) fails: {fails[:5]}")
    print(f"  check 5 (zero-shot vs stored, images 0-4): max |dE| {w5['energy_eV']:.1e} eV, max |d eps_i| "
          f"{w5['per_atom_energies_eV']:.1e} eV (tol 1e-6); max |dF| {w5['forces_eVA_reported']:.1e} eV/A (reported)  PASS")
    # ---- check 6: D2 reproduction from the image points
    rows = []
    for k, b in bands.items():
        ref = d2["bands"][k]
        L = {i: b.lab[i] for i in range(5)}
        Pimg = {i: b.P[i] for i in range(5)}
        for m in MODELS:
            E, F = ev[m].E, ev[m].F
            rows.append({"band": k, "what": f"D2a.{m}.i_star", "ok": a44.argmax(E, L) == ref["D2a"][m]["i_star"]})
            for x, y in ((0, 2), (2, 3), (3, 4)):
                sb = ref["D2a"][m]["segments_beside"][f"{x}-{y}"]
                W = float(a44.path_work(F, {0: Pimg[x], 2: Pimg[y]}, b.cell, {0: L[x], 2: L[y]}, 2).sum())
                dE = (E[L[y]] - E[L[x]]) * 1000
                for nm, ours, r_ in (("W_meV", W, sb["W_meV"]), ("dE_meV", dE, sb["dE_meV"])):
                    rows.append({"band": k, "what": f"D2a.{m}.segments_beside.{x}-{y}.{nm}", "diff": abs(ours - r_),
                                 "ok": abs(ours - r_) <= TOL_D2})
        i = istar[k]
        wz, wf = (a44.path_work(ev[m].F, Pimg, b.cell, L, i) for m in MODELS)
        ea = {m: (ev[m].E[L[a44.argmax(ev[m].E, L)]] - ev[m].E[L[0]]) * 1000 for m in MODELS}
        seg = lambda m: (ev[m].E[L[i]] - ev[m].E[L[0]]) * 1000
        att = a44.attribution(wf - wz, b.g, ea["finetuned"] - ea["zeroshot"], seg("finetuned") - seg("zeroshot"))
        for g in GROUPS:
            rows.append({"band": k, "what": f"D2b.groups_meV.{g}", "diff": abs(att["groups_meV"][g] - ref["D2b"]["groups_meV"][g]),
                         "ok": abs(att["groups_meV"][g] - ref["D2b"]["groups_meV"][g]) <= TOL_D2})
        for nm in ("segment_change_meV", "direct_meV"):
            rows.append({"band": k, "what": f"D2b.{nm}", "diff": abs(att[nm] - ref["D2b"][nm]), "ok": abs(att[nm] - ref["D2b"][nm]) <= TOL_D2})
        # the new quadrature on C at n = 1 against scripts/44 path_work (consistency of the new code)
        Csegs = b.paths(i)[0]["C"]
        for m, wref in (("zeroshot", wz), ("finetuned", wf)):
            wn = sum(seg_work(ev[m].F, b, kk, 1) for kk in Csegs)
            rows.append({"band": k, "what": f"new n=1 quadrature on C vs scripts/44 path_work ({m})",
                         "diff": float(np.abs(wn - wref).max()), "ok": float(np.abs(wn - wref).max()) <= TOL_ID, "tol": TOL_ID})
    rows += [{**r, "diff": None} for r in rep_geo]
    num = [r["diff"] for r in rows if r.get("diff") is not None and "tol" not in r]
    c6 = {"n_compared": len(rows), "max_abs_diff_meV": max(num) if num else None, "tol_meV": TOL_D2,
          "max_abs_diff_new_quadrature_vs_path_work_meV": max((r["diff"] for r in rows if "tol" in r), default=None),
          "failures": [r for r in rows if not r["ok"]], "pass": all(r["ok"] for r in rows)}
    checks["6_D2_reproduction"] = c6
    require(c6["pass"], EXIT_REPRO, f"check 6 (D2 reproduction) fails: {c6['failures'][:5]}")
    print(f"  check 6 (D2 reproduction): {len(rows)} items (segments_beside W and dE of 0-2, 2-3, 3-4 per model; D2b "
          f"groups_meV, segment_change_meV, direct_meV; i_star; hop_I and group sizes); max |diff| {c6['max_abs_diff_meV']:.1e} "
          f"meV (tol 1e-3); new n=1 quadrature vs scripts/44 path_work max |diff| "
          f"{c6['max_abs_diff_new_quadrature_vs_path_work_meV']:.1e} meV  PASS")
    # ---- interior points
    t0 = time.time()
    for n_done, (k, b) in enumerate(bands.items(), 1):
        for l, p in pts[k].items():
            if l in ev["zeroshot"].E:
                continue
            for m in MODELS:
                ev[m](l, b.atoms(p))
        if n_done % 5 == 0 or n_done == len(bands):
            el = time.time() - t0
            print(f"  interior points: {n_done}/{len(bands)} bands, {sum(e.n for e in ev.values())} single points so far "
                  f"({el:.0f} s, {el / n_done:.0f} s per band)")
    # ---- check 9: the count
    exp = 2 * PER_BAND * len(bands)
    cnt = {m: ev[m].n for m in MODELS}
    require(sum(cnt.values()) == exp and all(c == PER_BAND * len(bands) for c in cnt.values()) and
            (bandsel is not None or exp == N_TOTAL), EXIT_ERROR, f"single-point count {cnt} != {exp} (plan: 2442)")
    checks["9_single_points"] = {"per_model": cnt, "total": sum(cnt.values()), "expected": exp, "plan_total": N_TOTAL,
                                 "per_model_and_band": PER_BAND, "pass": True}
    print(f"  check 9 (single points): zero-shot {cnt['zeroshot']}, fine-tuned {cnt['finetuned']}, total {sum(cnt.values())} "
          f"(expected {exp}{'' if bandsel else ', the plan 2442'})  PASS")

    # ---- per-band quantities
    out = {}
    for k, b in bands.items():
        i = istar[k]
        paths, ext = b.paths(i)
        rec = {"band": k, "host": b.h, "system": b.s, "split": b.split, "split_name": SPLIT_NAME[b.split],
               "images": {"single_points": [0, 1, 2, 3, 4], "geometry_only": [6], "not_used": [5]},
               "i_star": i, "groups": b.ginfo, "band_file": band_sha[k], "check3": c3[k], "paths": {}}
        for p, segs in paths.items():
            q, _ = path_quantities(b, segs, ev, i)
            q["criteria"] = criteria(q)
            rec["paths"][p] = q
        rec["dS_meV"] = rec["paths"]["P"]["D3b"]["dS_meV"]
        rec["status"] = "resolved" if rec["paths"]["P"]["criteria"]["meets"] else "not resolved"
        rec["failed_criteria"] = rec["paths"]["P"]["criteria"]["failed"]
        rec["status_C"] = "resolved" if rec["paths"]["C"]["criteria"]["meets"] else "not resolved"
        rec["failed_criteria_C"] = rec["paths"]["C"]["criteria"]["failed"]
        rec["D3c"] = site_energy(b, ev, i)
        # D3d Hermite excess: the segments of P to i* only; the chord 0-2 beside it (an addition, not D3d); the 2-3 segment
        # of an i* = 2 band under extension_2_3 (plan section 3: the extension is reported separately)
        rec["D3d"] = {"hermite": {kk: hermite(ev, b, kk) for kk in paths["P"]},
                      "hermite_chord_0_2_beside": hermite(ev, b, "0-2"),
                      "geometry": geometry_d3d(b, paths, pts[k], i)}
        assert set(paths["P"]) | {"0-2"} | ({"2-3"} if ext else set()) == set(SEGS) and "0-2" not in paths["P"], (k, paths)
        if ext:
            rec["extension_2_3"] = {"note": "beside, no rule: the 2 -> 3 extension of an i* = 2 band; outside every criterion "
                                            "and summary", "paths": {}}
            for p, segs in ext.items():
                q, _ = path_quantities(b, segs, ev, 3)
                q["criteria_values_no_status"] = criteria_values(q)
                rec["extension_2_3"]["paths"][p] = q
            rec["extension_2_3"]["D3c_to_image3"] = site_energy(b, ev, 3)
            rec["extension_2_3"]["D3d_hermite_2_3"] = hermite(ev, b, "2-3")
        rec["Ea_link"] = ea_link(b, ev, i)
        rec["D2b_groups_meV_seen"] = d2b[k]
        P1 = rec["paths"]["P"]["D3a"]["zeroshot"]
        rec["P_n1_zeroshot_closures_meV"] = {"0-2": P1["segments"]["0-1"]["closure_meV"][1] + P1["segments"]["1-2"]["closure_meV"][1],
                                             "full": P1["total"]["closure_meV"][1]}
        out[k] = rec

    # ---- check 7 summary (asserted inside), check 10 (reported)
    checks["7_identities"] = {
        "pass": True,
        "work_identity_max_abs_diff_meV": max(max(q["D3b"]["identity_max_abs_diff_meV"].values()) for r in out.values()
                                              for q in list(r["paths"].values()) + list(r.get("extension_2_3", {}).get("paths", {}).values())),
        "site_energy_sum_vs_E_max_abs_diff_eV": max(e.max_sum_dev for e in ev.values()),
        "sum_d_eps_vs_dS_max_abs_diff_meV": max(abs(r["D3c"]["sum_minus_dS_meV"]) for r in out.values()),
        "Ea_link_max_abs_diff_meV": max(r["Ea_link"]["identity_abs_diff_meV"] for r in out.values()),
        "energies_minus_node_energy_vs_E0_max_abs_diff_eV": max(e.max_e0_dev for e in ev.values()),
        "min_abs_E0_of_evaluated_atoms_eV": {m: ev[m].min_abs_e0 for m in MODELS}, "per_atom_property": PER_ATOM,
        "note": "'energies' - 'node_energy' equals each atom's E0, which is non-zero for every atom evaluated, so the "
                "property used keeps the E0s and is not 'node_energy'",
        "tol": {"work_meV": TOL_ID, "site_eV": TOL_SITE, "E0_eV": TOL_E0}}
    c10 = {}
    for k, v in SEEN_IMAGE1.items():
        if k in out:
            ours = out[k]["P_n1_zeroshot_closures_meV"]
            c10[k] = {s_: {"recomputed_meV": ours[s_], "WP3_DIAGNOSTICS_md_meV": v[s_], "diff_meV": ours[s_] - v[s_]} for s_ in v}
    checks["10_image1_scratch_closures_reported"] = {"note": "reported, not gated: zero-shot, one interval per segment (P at n = 1); "
                                                             "the document values are rounded to 0.1 meV", "values": c10}
    print("  check 7 (identities): work {:.1e} meV, sum eps = E {:.1e} eV, sum d_eps = dS {:.1e} meV, E_a link {:.1e} meV; "
          "'energies' - 'node_energy' = E0 within {:.1e} eV  PASS".format(
              checks["7_identities"]["work_identity_max_abs_diff_meV"], checks["7_identities"]["site_energy_sum_vs_E_max_abs_diff_eV"],
              checks["7_identities"]["sum_d_eps_vs_dS_max_abs_diff_meV"], checks["7_identities"]["Ea_link_max_abs_diff_meV"],
              checks["7_identities"]["energies_minus_node_energy_vs_E0_max_abs_diff_eV"]))
    print("  check 10 (reported): image-1 closures (zero-shot, n = 1): " + "; ".join(
        f"{k} 0-2 {v['0-2']['recomputed_meV']:+.1f} (doc {v['0-2']['WP3_DIAGNOSTICS_md_meV']:+.1f}), full "
        f"{v['full']['recomputed_meV']:+.1f} (doc {v['full']['WP3_DIAGNOSTICS_md_meV']:+.1f})" for k, v in c10.items()))

    # ---- resolution, summaries, exclusion report
    res = [k for k in out if out[k]["status"] == "resolved"]
    nres = len(res)
    R = lambda keys: [out[k] for k in keys]
    hosts = list(dict.fromkeys(out[k]["host"] for k in out))
    summ = {"label": "few resolved bands" if nres < FEW else None, "n_bands": len(out), "n_resolved": nres,
            "n_resolved_with_C_not_resolved": sum(out[k]["status_C"] != "resolved" for k in res),
            "overall": subset_summary(R(res), nres),
            "by_split": {SPLIT_NAME[sp]: subset_summary(R([k for k in res if out[k]["split"] == sp]), nres)
                         for sp in ("train", "valid", "test")},
            "by_host": {h: subset_summary(R([k for k in res if out[k]["host"] == h]), nres) for h in hosts}}
    summ["by_host_mean_of_host_means"] = mean_of_means(list(summ["by_host"].values()))
    if not nres:
        summ["note"] = "no band is resolved: only the per-band values and the exclusion report are given (plan section 6)"
    ex = {"note": "a check on selection (plan section 6): for excluded and resolved bands, the failed criteria, dS and the "
                  "seen coarse D2b groups_meV (not a reading)", "by_split": {}, "by_host": {}}
    for k, r in out.items():
        row = {"band": k, "status": r["status"], "failed_criteria": r["failed_criteria"], "status_C": r["status_C"],
               "failed_criteria_C": r["failed_criteria_C"], "dS_meV": r["dS_meV"], "D2b_groups_meV_seen": r["D2b_groups_meV_seen"]}
        for key, val in (("by_split", r["split_name"]), ("by_host", r["host"])):
            d = ex[key].setdefault(val, {"n_resolved": 0, "n_excluded": 0, "resolved": [], "excluded": []})
            d["resolved" if r["status"] == "resolved" else "excluded"].append(row)
            d["n_resolved" if r["status"] == "resolved" else "n_excluded"] += 1
    ex["criterion_failure_counts"] = {}
    for r in out.values():
        for f in r["failed_criteria"]:
            key = f.split(":")[0]
            ex["criterion_failure_counts"][key] = ex["criterion_failure_counts"].get(key, 0) + 1

    # ---- print
    print("\n  band          split i* | P closure8 ZS    FT  (c4/c8)       | C closure8 ZS    FT   | max |dW8-dW4| P  C | "
          "status P / C | dS     | dW_R(P): hop_I in<6 in>6 org<6 org>6 | d_eps: hop_I in<6 in>6 org<6 org>6")
    for k, r in out.items():
        pa, ca = r["paths"]["P"], r["paths"]["C"]
        z, f = pa["D3a"]["zeroshot"]["total"], pa["D3a"]["finetuned"]["total"]
        cz, cf = ca["D3a"]["zeroshot"]["total"], ca["D3a"]["finetuned"]["total"]
        mp = max(pa["D3b"]["dW"][g]["abs_8_minus_4"] for g in GROUPS)
        mc = max(ca["D3b"]["dW"][g]["abs_8_minus_4"] for g in GROUPS)
        print(f"  {k:<13s} {r['split']:<5s} {r['i_star']}  | {z['closure_meV'][8]:+6.2f} {f['closure_meV'][8]:+6.2f} "
              f"({a39.num(z['closure4_over_closure8'], '.1f')}/{a39.num(f['closure4_over_closure8'], '.1f')}) | "
              f"{cz['closure_meV'][8]:+6.2f} {cf['closure_meV'][8]:+6.2f} | {mp:5.2f} {mc:5.2f} | "
              f"{'res' if r['status'] == 'resolved' else 'NOT'} / {'res' if r['status_C'] == 'resolved' else 'NOT'} | "
              f"{r['dS_meV']:+7.1f} | " + " ".join(f"{pa['D3b']['dW'][g]['richardson']:+6.1f}" for g in GROUPS) + " | " +
              " ".join(f"{r['D3c']['d_eps_meV'][g]:+6.1f}" for g in GROUPS))
        if r["failed_criteria"]:
            print(f"      P failed: {'; '.join(r['failed_criteria'])}")
    o = summ["overall"]
    print(f"\n  resolved: {nres} of {len(out)} bands{' (FEW RESOLVED BANDS)' if nres < FEW else ''}; resolved with C not "
          f"resolved: {summ['n_resolved_with_C_not_resolved']}; criterion failures (P): {ex['criterion_failure_counts']}")
    for sp, d in ex["by_split"].items():
        print(f"    {sp}: {d['n_resolved']} resolved, {d['n_excluded']} excluded")
    if o.get("n"):
        print("  item 1/2 (overall, meV): group: mean dW_R [median, range] (mean |dW8-dW4|) | mean d_eps [median, range]")
        for g in GROUPS:
            w, e = o["item1_dW"][g], o["item2_d_eps"][g]
            print(f"    {g:<15s} {w['mean']:+7.2f} [{w['median']:+7.2f}, {w['min']:+7.2f} .. {w['max']:+7.2f}] ({w['mean_abs_8_minus_4']:.2f}) | "
                  f"{e['mean']:+7.2f} [{e['median']:+7.2f}, {e['min']:+7.2f} .. {e['max']:+7.2f}]  sign: {o['sign_comparison'][g]['statement']}")
        print("  item 3 (overall): group: mean W_ZS,R, mean W_FT,R (meV); n e>1; median D_g; ratio dW/W_ZS (n, median, range)")
        for g in GROUPS:
            c = o["item3_comparators"][g]; rr = c["ratio_dW_over_W_ZS_where_abs_W_ZS_ge_5meV"]
            print(f"    {g:<15s} {c['W_ZS']['mean']:+8.2f} {c['W_FT']['mean']:+8.2f}; {c['n_bands_e_W_ZS_or_W_FT_above_1meV']}; "
                  f"{c['median_D']:.3f}; {rr['n']}" + (f", {rr['median']:+.2f} [{rr['min']:+.2f} .. {rr['max']:+.2f}]" if rr["n"] else ""))
        p4 = o["item4_path_dependence"]
        print(f"  item 4 (P vs C, {p4['n_both_resolved']} bands with both resolved): " + "; ".join(
            f"{g} mean |d| {p4[g]['mean_abs_diff_meV']:.2f} max {p4[g]['max_abs_diff_meV']:.2f} (mean e(P)+e(C) "
            f"{p4[g]['mean_e_P_plus_e_C_meV']:.2f})" for g in GROUPS if g in p4))
        p5 = o["item5_seen_coarse_vs_converged"]
        print("  item 5 (seen coarse D2b vs converged; median, max |.|, meV): " + "; ".join(
            f"{g} C {p5[g]['C_R_minus_D2b']['median_meV']:+.1f}/{p5[g]['C_R_minus_D2b']['max_abs_meV']:.1f}, P "
            f"{p5[g]['P_R_minus_D2b']['median_meV']:+.1f}/{p5[g]['P_R_minus_D2b']['max_abs_meV']:.1f}" for g in GROUPS))
        print(f"  item 6 (kappa): median {a39.num(o['item6_kappa']['median'], '.2f')}, n > 2: {o['item6_kappa']['n_above_2']} "
              f"of {o['item6_kappa']['n_defined']}")
        print("  item 7 (D3a): " + "; ".join(f"{p} {m} median |c8| {o['item7_D3a'][p][m]['median_abs_closure8_meV']:.2f}, max "
                                            f"{o['item7_D3a'][p][m]['max_abs_closure8_meV']:.2f}, median c4/c8 "
                                            f"{a39.num(o['item7_D3a'][p][m]['median_closure4_over_closure8'], '.2f')}"
                                            for p in ("P", "C") for m in MODELS))
        print(f"  per-band groups with agreeing signs: histogram {o['per_band_groups_sign_agree']['histogram']}")
        for sp, s_ in summ["by_split"].items():
            if s_.get("n"):
                print(f"  by split {sp} (n {s_['n']}): mean dW_R " + ", ".join(f"{g} {s_['item1_dW'][g]['mean']:+.1f}" for g in GROUPS) +
                      "; mean d_eps " + ", ".join(f"{g} {s_['item2_d_eps'][g]['mean']:+.1f}" for g in GROUPS))
        mh = summ["by_host_mean_of_host_means"]
        print(f"  mean of host means ({mh['n_hosts']} hosts): dW_R " + ", ".join(
            f"{g} {mh['item1_dW'][g]['mean']['mean_of_host_means']:+.1f}" for g in GROUPS) + "; d_eps " + ", ".join(
            f"{g} {mh['item2_d_eps'][g]['mean']['mean_of_host_means']:+.1f}" for g in GROUPS))
    return {"part": "D3", "plan": f"WP3_DIAGNOSTICS_D3_PLAN.md (commit {PLAN_COMMIT[:7]})",
            "status": "post hoc, reported only; a pre-specified description, no verdict",
            "definitions": {
                "paths": "P = 0 -> 1 -> 2 [-> 3] to i*; C = chord 0 -> 2 [-> 3] to i*; n = 8 points per segment (r_k + j/8 dr_k), "
                         "n = 4 and 2 subsets, n = 1 the images; extension 2 -> 3 for i* = 2 bands (beside)",
                "work": "W = -sum 1/2 (F_a + F_b) . (r_b - r_a), per atom before summation, meV; closure = W - [E(end) - E(start)]",
                "work_quantity": "n8, n4, n2, n1; e = |X8 - X4|/3; richardson = X8 + (X8 - X4)/3; abs_8_minus_4 (the conservative "
                                 "error of statements); ratio_2_4_over_4_8 = (X2 - X4)/(X4 - X8)",
                "dS": "[E_FT(i*) - E_FT(0)] - [E_ZS(i*) - E_ZS(0)] (the segment change, scripts/44 segment_change_meV)",
                "dW_g": "-int (F_FT - F_ZS)_g . dr along the path", "D_g": "sum_{i in g} sum_steps |dr_i|^2 / sum_all (n = 8)",
                "kappa": "(|L| + |N|)/|L + N|, L = dW(hop_I) + dW(inorganic_near), N = the other three (Richardson)",
                "d_eps_g": "site-energy gauge, calculator property 'energies' (keeps the E0s; they cancel)",
                "hermite": "cubic Hermite with E at both images and dE/dlambda = -F . dr_k; excess = max_j E(lambda_j) - H(lambda_j); "
                           "D3d.hermite = the segments of P to i* only; D3d.hermite_chord_0_2_beside = the chord 0-2 (beside, "
                           "not D3d); extension_2_3.D3d_hermite_2_3 = the extension's 2-3 segment (i* = 2 bands)",
                "extension_2_3": "i* = 2 bands only: P_ext and C_ext to image 3, beside, outside every criterion, D3d block and "
                                 "summary; criteria_values_no_status = the numbers criteria 1-2 would use, with no status or "
                                 "pass/fail flag",
                "resolved": "plan section 6 criteria 1-2 on P (status), on C (status_C)",
                "splits": SPLIT_NAME},
            "departures_from_plan": DEPARTURES, "interpretations_of_plan": INTERPRETATIONS, "additions_to_plan": ADDITIONS,
            "checks": checks, "bands": out, "summaries": summ, "exclusion_report": ex,
            "n_single_points": checks["9_single_points"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--model", default=os.path.join(DS, "wp3", "run2", "wp3.model"))
    ap.add_argument("--model-sha256", default=a44.MODEL_SHA256)
    ap.add_argument("--dataset", default=os.path.join(DS, "wp3", "dataset"))
    ap.add_argument("--dft", default=DS, help="root of the archived QE outputs (scripts/44 cross-check)")
    ap.add_argument("--v2", default=os.path.join(DS, "wp1_production"), help="wp2cde_selection.json, v2prod structures")
    ap.add_argument("--structures", default=None)
    ap.add_argument("--bands", default=os.path.join(os.path.dirname(ROOT), "bands"))
    ap.add_argument("--d2-json", default=os.path.join(DS, "wp3", "diagnostics", "d2_path_attribution.json"))
    ap.add_argument("--out-dir", default=os.path.join(DS, "wp3", "diagnostics"))
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--bands-only", nargs="+", default=None, help="development only: a subset of bands (<host>_<system>)")
    a = ap.parse_args(argv)
    a.model_sha256 = a.model_sha256.lower()
    if not os.path.isfile(a.model):
        ap.error(f"--model {a.model}: no such file")
    if a.bands_only and os.path.realpath(a.out_dir) == os.path.realpath(os.path.join(DS, "wp3", "diagnostics")):
        ap.error("--bands-only (development) may not write to the default --out-dir")
    log = os.path.join(a.out_dir, "d3_console.log")
    tee = sys.stdout = Tee(log)
    script_sha = a39.sha256(os.path.abspath(__file__))
    inputs = {f"dataset_{sp}": os.path.join(a.dataset, f"{sp}.xyz") for sp in ("train", "valid", "test")}
    inputs.update({"dataset_meta": os.path.join(a.dataset, "dataset_meta.json"),
                   "wp2cde_selection": os.path.join(a.v2, "wp2cde_selection.json"), "d2_json": a.d2_json,
                   "wp3_model": a.model, "plan": os.path.join(ROOT, PLAN)})
    tracked = [rel(p) for p in inputs.values() if a39.inside(p, ROOT)]
    gs = a39.git_state([SCRIPT, "scripts/44_wp3_diagnostics.py", "scripts/39_wp3_evaluate.py", "scripts/38_wp2e_displacement.py",
                        "scripts/37_dft_eb_analysis.py", "scripts/32_dft_validation_analysis.py"] + tracked)
    print(f"\n######## {SCRIPT}  {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%S} UTC"
          f"\n  git head {gs.get('head')}; uncommitted (scripts and inputs) {gs.get('uncommitted')}; script sha256 "
          f"{script_sha}; threads {a.threads}" + (f"\n  DEVELOPMENT SUBSET {a.bands_only}; out-dir {rel(a.out_dir)}" if a.bands_only else ""))
    try:
        # ---- check 2: the plan (before anything else)
        pc = plan_check()
        print(f"  check 2 (plan): {PLAN} committed at {pc['commit'][:12]} (sha256 {pc['sha256'][:12]}), identical to that "
              f"commit and to HEAD {pc['head'][:12]}  PASS")
        miss = [rel(p) for p in inputs.values() if not os.path.isfile(p)]
        require(not miss, EXIT_DATA, f"input files missing: {miss}")
        import mace, torch, ase
        d2 = json.load(open(a.d2_json))
        ver = {"mace": mace.__version__, "torch": torch.__version__, "ase": ase.__version__, "numpy": np.__version__}
        require(ver == d2["versions"], EXIT_SHA, f"package versions {ver} differ from D2's {d2['versions']}")
        print(f"  check 1 (packages): {ver} = D2's  PASS; model sha256 checked at load")
        hashed = {k: {"file": rel(p), "sha256": a39.sha256(p)} for k, p in inputs.items()}
        print("  inputs: " + "; ".join(f"{v['file']} {v['sha256'][:12]}" for v in hashed.values()))
        data, M = a44.Data(a), a44.Models(a)
        checks = {"1_models_and_packages": {"versions": ver, "versions_D2": d2["versions"], "pass": True},
                  "2_plan": pc}
        head = {"script": SCRIPT, "script_sha256": script_sha, "plan_file": pc, "git": gs, "versions": ver, "threads": a.threads,
                "float64_cpu": "asserted for both arms before their first frame (scripts/39 Arm)",
                "model_files": {"zeroshot": {"call": 'mace_mp(model="medium", device="cpu", default_dtype="float64")',
                                             "file": "~/.cache/mace/20231203mace128L1_epoch199model", "sha256": a39.FOUNDATION_SHA256},
                                "finetuned": {"file": rel(a.model), "sha256": a.model_sha256, "head": "Default"}},
                "input_files": {**hashed, "note": "sha256 at the start of the run; the git status of every input inside the "
                                                  "repository is in 'git'. The archived QE outputs are not hashed: they are "
                                                  "tied to the hashed dataset by the scripts/44 cross-check (check 4)"},
                "development_subset": a.bands_only}
        r = d3(a, data, M, d2, checks)
        r["band_files"] = {k: v["band_file"] for k, v in r["bands"].items()}
        assert not set(head) & set(r), f"head and result share keys {sorted(set(head) & set(r))}"
        os.makedirs(a.out_dir, exist_ok=True)
        f = os.path.join(a.out_dir, "d3_dense_path.json")
        a39.write_json({**head, **r}, f)
        print("written", rel(f), "and (appended)", rel(log))
    except Stop as e:
        print(f"STOP (exit {e.code}): {e}\n  nothing written (no JSON, no console log; this output is on stdout only)")
        sys.stdout.flush()
        return e.code
    except Exception as e:                      # a failed assertion or an unexpected error: fail-closed, on stdout only
        import traceback
        print(f"ERROR (exit {EXIT_ERROR}): {type(e).__name__}: {e}\n{traceback.format_exc()}  nothing written (no JSON, no "
              "console log; this output is on stdout only)")
        sys.stdout.flush()
        return EXIT_ERROR
    sys.stdout.flush()
    tee.commit()                                # the console log is appended only after a run with exit 0
    return 0


if __name__ == "__main__":
    sys.exit(main())

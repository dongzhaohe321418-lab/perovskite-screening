#!/usr/bin/env python
"""Criterion 6 and adoption (a)-(e) for the WP3 fine-tuned MACE (PLAN amendment 2026-10-28m, items 3-5).

Arms (item 3, Computation). Both in one invocation, float64, CPU, one mace-torch installation:
    zero-shot   mace_mp(model="medium", device="cpu", default_dtype="float64")      (the call of scripts/32, 37)
    fine-tuned  MACECalculator(model_paths=[<wp3.model>], device="cpu", default_dtype="float64", head="Default")
The fine-tuned file's sha256 must equal --model-sha256 (checked at start; hashing does not load the model),
and the calculator must report head 'Default' among its heads (0.3.16 otherwise falls back silently to the
last head). float64 assertion: item 3 states both 'asserts float64 for both arms before any frame is
evaluated' and 'the fine-tuned model is not loaded ... until this gate has passed'. Both cannot hold, because
the gate evaluates zero-shot frames. The gate-order rule is kept: each arm is asserted float64 (calculator
dtype and every parameter) and CPU when it is built, before its own first frame; the fine-tuned arm is built
after the gate, so no fine-tuned frame is evaluated before its assertion. The JSON records this
('float64_assertion') for the WP3 result.

Geometries (item 3). Single points only, at the geometries DFT was run on: the band images of ../bands and
the _relaxed WP2c structures of v2prod_structures.tar.gz (labels from wp2cde_selection.json). Cell (per
lattice vector) and positions (per-atom displacement norm) must equal CELL_PARAMETERS / ATOMIC_POSITIONS of
the archived <label>.in(.gz) within 1e-6 A: at step 1 (--gate-only) on the 46 m30/m32 frames; at step 6 on
all 96 test frames, whether or not the output is complete (a missing input fails for an m30/m32 frame or a
frame with a complete output, and is listed otherwise: that frame is incomplete). The label set of the frames
with complete DFT must equal the label set of test.xyz. Addition (stricter, never looser): each complete
output used must be one single point of that geometry: at most one '!' total energy, force block and
Fermi-energy line, and its header cell and positions (alat units, printed to 1e-6 / 1e-7 alat; at most
1.7e-5 A from the input on the archive) within 1e-4 A of the geometry. For the item-1' frames no other check
catches a relax or multi-SCF output, or another frame's output archived under the label.
DFT: F and forces by scripts/32 parse_qe (last force block), E_F as scripts/37 qe() (last 'the Fermi energy
is ... ev'); never from REF_energy. A frame is complete with JOB DONE, a total energy, a converged SCF, a force
block and E_F (amendment g item 2; item 1'); <label>.gaveup(.gz) marks a job the queue gave up on (item 1e).
E' = F - (E_F - 3.3447 eV) for the vacancy cells (59 I), F otherwise (item 1c); E_F,ref and c_D cancel in
every quantity below.

Reused code: scripts/32 parse_qe, read_text, REQUIRED_IMAGES, band_class (E_a = max over images 2-4 of
E_i - E_0 on the fixed path, complete bands only; pair = dopant minus undoped band of one host; scripts/32
has no E_a function, so its two lines are restated in Ea()); scripts/37 qe, index_outputs, eb() (order D+V,
D, V, host), TOL4, and its near-sign rule (sites ending _hinge/_flank/_near, int(np.sign) compared); far
sites from wp2cde_selection.json (m30: Pb64, FA152, asserted). DFT E_b uses scripts/37 eb() with its
|E_b| < 2 eV label-order assertion; the model arms use the same expression on the same labels without it
(eb_model), so a finite but poor model is evaluated, not stopped (item 2: a model worse than Initial 'is
still evaluated').
Non-finite model values (fail-closed): no non-finite energy or force drops out of a statistic. Ea() is NaN if
any of the five energies is non-finite (Python's max() would skip a NaN after the first image). A condition
resting on a non-finite value 'cannot be evaluated': it is not strictly below zero-shot, (b) or (c) is not
met, and the frames are listed. NaN is written to the JSON as null.

Reproduction gate (item 3), at every invocation, zero-shot arm first. 'At every invocation' includes step 1,
so the 50 item-1' images (MACE only; no QE file of theirs is read) are checked in --gate-only as well:
    frame energies within 1e-6 eV: 30 m30/m32 band frames vs E_mace of wp2b_validation.json; 16 m30 WP2c
    frames vs shell_m30.json (top-level E_eV of E_host and E_vac; the doped_fmax_final stage of each row's
    no_vac and with_vac, the stage selection of scripts/37 mace_eb); 50 item-1' images vs the energy field
    of ../bands/band_<system>_<host>.extxyz;
    comparators (GATE): (i) and its band / WP2c parts within 1e-6 eV/A; the 4 raw and 4 E' pair errors,
    their two RMS, the 5 site errors and their RMS within 0.001 meV;
    exactly: the class changes on both bases ({m32 GA: DFT 0 -> MACE -1}, no other) and the GA near-sign
    disagreement. Per-dopant RMS and the GA128 share are printed, not gated.
  Tolerance rule. PLAN states each comparator rounded to its last digit (0.001 meV; 1e-6 eV/A for (i)).
  The gate requires |unrounded recomputation - stated| <= one unit of that digit, the literal 'to within
  0.001 meV'. A faithful recomputation lies within half a unit of the stated value, so it passes with a
  margin of at least 0.0005 meV. A change of more than 0.0015 meV fails wherever the value sits; a change
  between 0.0005 and 0.0015 meV may pass, depending on where the unrounded value sits. Rounded equality
  (round(x, 3) == stated) is printed beside each line but not gated: m30 GA (raw -22.2405064, E' -21.6405064
  meV) lies 6.4e-6 meV from a half-way point, so float64 noise in the band-frame energies on another machine
  or thread count could flip its rounding. The tolerance is never widened by the half-unit
  (|x - stated| <= 0.0005 + 0.001 is not used).
  Order. No item-1' QE output or input is read, test.xyz is not read, and the fine-tuned model is not
  loaded, before the gate (and the 46-frame check) has passed. On a failure, including an error while
  reading or checking the reference data, only the gate diagnostics are printed, nothing is written, and the
  exit status is 4.

Criterion 6 (item 3; full mode, step 6), fine-tuned vs this invocation's unrounded zero-shot values:
    (i) sqrt(sum |F_model - F_DFT|^2 / sum 3N) over the 46 frames; (ii) RMS of model - DFT dE_a over the 4
    m30/m32 pairs, raw F and E' (the model dE_a is its own energy difference, the same on either basis);
    (iii) RMS of the far-referenced E_b error over the 5 non-far m30 sites, raw F (E' values reported).
    'Improvement' iff (i), (ii) raw, (ii) E' and (iii) are all strictly below zero-shot; the verdict on
    (i), (ii) raw, (iii) is reported beside it as 'criterion 6 as amended by h'. --basis must equal
    dataset_meta.json 'basis'; under the raw fallback (ii) is on raw F only and the verdicts coincide.
Adoption (item 4): (a) the verdict; (b) all 9 test pairs on E' (raw F under the fallback), DFT classes from
that basis: RMS < 20 meV and no class change at +/-59.5 meV; any incomplete pair -> 'not met: incomplete';
(c) the 5 non-far m30 sites on raw F: every |far-ref error| < 25 meV and the DFT sign at Sr hinge, Sr flank
and GA near ('one host (m30), 5 sites'); (d) WP3b, (e) MD from the JSON of scripts/40 (top-level item 'PLAN
amendment m item 4 (d), WP3b') and scripts/41 (top-level check 'WP3 adoption (e): MD stability'): 'pass'
true/false/null and 'model_sha256', which must equal the evaluated model's. A wrong identity key, pass null,
a missing or different model_sha256, or an unreadable file is 'cannot be evaluated' (a fail for the
Outcomes); the two paths may not be the same file. Outcome (fail-closed): 'No improvement' unless (a);
'Improved but not validated' if (a) and any of (b)-(e) fails or cannot be evaluated; 'Validated' if all hold.
At step 6, (d) and (e) do not exist yet (item 7: they run at step 7), so a full run without them ends
'pending' unless (a), (b) or (c) already decides. --outcome-only composes the final Outcome at step 8 from the
saved wp3_eval.json and the two results: it loads no model and reads no QE file, so it is not a second
evaluation.
Reported beside (no decision): (i) over all test frames; (ii) over all 9 pairs on both bases; (iii) per
dopant on raw and E'; the absolute E_a errors of the 16 test bands on both bases; every per-frame (force
RMSE), per-pair, per-band and per-site error of both models with the number that improve; the model's m30
(img3 - img0)(Sr - undoped) against DFT q = +1 / E' / q = 0 (+40.2 / +36.8 / -2.9 meV); the m21 and
training-host quantities of item 5 (labelled); the item-5 coverage, power and wording notes; the error
budget (quoted only if Validated); the raw-fallback Sr expectation of item 1c (printed with (iii) and (c)).
The item-5 coverage flag (an item-1' band whose zero-shot absolute E_a error exceeds +59 meV) uses raw F, the
basis of the item-5 '+59 to +117 meV' figures; the E' values are reported beside it.
The raw (not far-referenced) model E_b is never reported as an error. A reported-only computation (item 5,
q = +1) that raises is recorded as an error in its place and never aborts the run.

    step 1: python scripts/39_wp3_evaluate.py --gate-only
    step 6: python scripts/39_wp3_evaluate.py --model <run>/wp3.model --model-sha256 <hex> \
                --dataset results/objective2/dopant_shell/wp3/dataset --basis Eprime
    step 8: python scripts/39_wp3_evaluate.py --outcome-only results/objective2/dopant_shell/wp3/wp3_eval.json \
                --wp3b-json <scripts/40 analyse result> --md-json <scripts/41 analyse result>
    defaults: --dft results/objective2/dopant_shell, --v2 .../wp1_production, --bands ../bands,
    --out .../wp3/wp3_eval.json (full mode), .../wp3/wp3_outcome.json (--outcome-only); --gate-only writes
    JSON only with --out.
Commit state: the git state of scripts/39, 32 and 37 is recorded. If one is uncommitted, a run whose --out
lies inside results/objective2/dopant_shell is refused (items 3 and 7.1 require scripts/39 committed);
elsewhere a warning is printed.
Development tests only: --cache DIR stores and reuses single points, keyed by arm, the model's full sha256,
label and a hash of numbers, positions and cell. It is allowed only with --gate-only or a stand-in (a
fine-tuned file equal to the zero-shot foundation file), and refused with an --out inside
results/objective2/dopant_shell; such a run is not a valid step-1 or step-6 run (the gate must run the
zero-shot arm afresh). A stand-in is recorded as such and also refused with an --out inside that directory.
Exit status: 0 done; 2 command-line error or refusal; 3 model sha256 differs from --model-sha256 (nothing
evaluated); 4 reproduction gate or 46-frame check failed, or an error before or inside the gate; 5 a check
failed before anything was evaluated or written (step 6: test-frame positions or outputs, test.xyz label set,
--basis; --outcome-only: the saved result is unusable); 6 an unexpected error after the gate (the message
states whether the fine-tuned model was loaded and how many fine-tuned single points ran; nothing written).
"""
import argparse, glob, hashlib, io, json, os, re, subprocess, sys, tarfile
import importlib.util
import numpy as np
from ase.io import read

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DS = os.path.join(ROOT, "results", "objective2", "dopant_shell")
_s = importlib.util.spec_from_file_location("a37", os.path.join(HERE, "37_dft_eb_analysis.py"))
a37 = importlib.util.module_from_spec(_s); _s.loader.exec_module(a37)
a32 = a37.a32                                     # the scripts/32 module that scripts/37 loaded

EF_REF = 3.3447                                   # eV, item 1c (cancels in every dE_a and far-ref E_b)
FOUNDATION_SHA256 = "01bfe22100139f424713cf921144e5509cbe353d67aa9fa1be9c6e1e0ed35845"   # item 2
IMG = a32.REQUIRED_IMAGES                         # (0, 2, 3, 4, 6)
WP2B_PAIRS = [("m30", "GA"), ("m30", "Sr"), ("m32", "GA"), ("m32", "Sr")]
EXTRA_PAIRS = [("m10", "GA"), ("m18", "GA"), ("m04", "Sr"), ("m14", "Sr"), ("m27", "Sr")]   # item 1'
TEST_PAIRS = WP2B_PAIRS + EXTRA_PAIRS
EB_HOST, FAR_SITES = "m30", {"Sr": 64, "GA": 152}
VALID_HOSTS, TRAIN_HOSTS = ["m21"], ["m05", "m06", "m08", "m12", "m15", "m20"]
NEAR = ("_hinge", "_flank", "_near")              # scripts/37 near-sign rule
TOL_FRAME_EV, TOL_MEV, TOL_FORCE, TOL_POS = 1e-6, 1e-3, 1e-6, 1e-6   # eV; meV; eV/A; A
TOL_OUT = 1e-4                                    # A, output header vs geometry (identity check, not precision)
RMS_TOL = 20.0                                    # meV, criterion 3 / adoption (b)
EXIT_SHA, EXIT_GATE, EXIT_CHECK, EXIT_ERROR = 3, 4, 5, 6
IDENT = {"WP3b": ("item", "PLAN amendment m item 4 (d), WP3b"),          # scripts/40 analyse result
         "MD": ("check", "WP3 adoption (e): MD stability")}               # scripts/41 analyse result
CODE = ["scripts/39_wp3_evaluate.py", "scripts/32_dft_validation_analysis.py", "scripts/37_dft_eb_analysis.py"]
# zero-shot comparators of item 3 (meV; (i) in eV/A); keys: pair '<host>_<dopant>' or site '<dopant><index>'
GATE = {"i": 0.086809, "i_band": 0.088867, "i_wp2c": 0.082823,
        "ii_raw": {"m30_GA": -22.241, "m30_Sr": -29.782, "m32_GA": -16.394, "m32_Sr": 24.215}, "ii_raw_rms": 23.647,
        "ii_Eprime": {"m30_GA": -21.641, "m30_Sr": -69.482, "m32_GA": -18.094, "m32_Sr": 14.515}, "ii_Eprime_rms": 38.191,
        "iii": {"Sr136": -6.403, "Sr124": 14.084, "Sr52": -3.838, "GA128": -60.043, "GA212": -13.306}, "iii_rms": 28.412,
        "class_changes": {"raw": {"m32_GA": [0, -1]}, "Eprime": {"m32_GA": [0, -1]}},   # [DFT, MACE]
        "GA_near_sign_disagrees": True}
REPORTED_NOT_GATED = {"iii_rms_Sr": 9.203, "iii_rms_GA": 43.487, "GA128_share_of_sum_sq": 0.893}
DFT_IMG30 = {"q1": 40.2, "Eprime": 36.8, "q0": -2.9}   # m30 (img3 - img0)(Sr - undoped), DFT, meV (item 3)
SR_FALLBACK_NOTE = ("raw-basis fallback (item 1c): a model that fits its targets is expected to under-predict the "
                    "far-referenced raw E_b at the m30 Sr hinge and flank by about 8-16 meV; this changes no verdict")
FLOAT64_NOTE = ("item 3 asks for float64 to be asserted for both arms before any frame and for the fine-tuned model not "
                "to be loaded before the gate passed; both cannot hold. Kept: the gate order. Zero-shot is asserted "
                "before its first (gate) frame, the fine-tuned arm when it is built after the gate, before its first frame")
NOTES = {
    "wording_pass": "consistent with improvement on the held-out hosts; not statistically resolved",
    "raw_fail_Eprime_pass": (
        "no improvement on raw F; E' improved. Item 5: under independent zero-mean normal E' errors of SD 5/10/15/20 "
        "meV, (ii) on raw F passes with probability 0.87/0.62/0.46/0.35, (ii) on E' with probability >= 0.99, and "
        "the RMS part of (b) with probability 1.00 (0.93) at SD 10 (15) meV; at SD 10 meV the raw pass probability "
        "is 0.28 if the m30 Sr error is positive and 0.95 if it is negative, so the sign of the m30 Sr residual "
        "mainly decides it; for errors equal to the zero-shot E' errors scaled by alpha, raw passes for "
        "-0.10 < alpha < 1, and with 20-50% of the zero-shot E' errors kept (plus SD 10 meV) it fails with "
        "probability 0.02-0.08. It shows that the model does not reproduce the neutral-cell band term, not that "
        "it is worse on E'. Per-pair raw and E' errors: criterion6.values. The outcome stays 'No improvement' "
        "(fail-closed); never a reason to re-run, re-train or re-decide"),
    "power": ("item 5: the 4 pairs share one undoped band per host and the 5 sites one far site per dopant (about 3 "
              "independent errors each); no significance test (smallest one-sided sign-flip p: 1/16 on 4 pairs, 1/32 on "
              "5 sites); criterion 6 alone is not the gate, (b)-(e) are"),
    "power_b": ("item 5: under independent zero-mean normal errors, a model with a true RMS of 30 (25) meV meets the "
                "RMS part of (b) with probability 0.09 (0.24) on 9 pairs; 0.22 (0.37) on 4 pairs and 0.02 (0.13) on "
                "the 18 pairs of criterion 3"),
    "power_c": ("item 5: a model with a true error SD of 15 meV fails 'all 5 < 25 meV' with probability 0.40 "
                "(zero-mean errors)"),
    "coverage": ("item 5: criterion 6 and (b) test paired dE_a, in which a host-wide overestimate largely cancels; a pass "
                 "does not show that the low-barrier overestimate (1) or the first-shell Sr E_b overestimate (2) is "
                 "corrected on unseen hosts. (iii) and (c) rest mainly on one GA site whose far reference has a MACE-level "
                 "SD of 28 meV and no DFT noise floor"),
    "budget": ("item 4: quoted only if Validated; sigma upper bounds RMS*1.645 (n = 9 pairs) and RMS*2.089 (n = 5 sites) "
               "assume independent errors (about 1.68 and 2.27 with shared bands / references); single-point part only"),
    "raw_Eb": "the raw (not far-referenced) model E_b is never reported as an error (item 3)"}


def rms(x):
    x = np.asarray(list(x), float)
    return float(np.sqrt(np.mean(x ** 2))) if x.size else None


def finite(x):
    return x is not None and bool(np.all(np.isfinite(x)))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def band_labels(host, system):
    return [f"{host}_{system}_img{k}" for k in IMG]


def is_band(label):
    return re.match(r"(m\d\d)_(undoped|GA|Sr)_img(\d)$", label)


def inside(path, root):
    return os.path.realpath(path).startswith(os.path.realpath(root) + os.sep)


# ---------------------------------------------------------------- geometries and archived QE files
class Geometry:
    """Band images of ../bands and _relaxed WP2c structures of v2prod (tarball or extracted directory)."""
    def __init__(self, bands, structures):
        self.bands, self.structures, self._b, self._w, self._tar = bands, structures, {}, {}, None

    def band_file(self, host, system):
        k = (host, system)
        if k not in self._b:
            self._b[k] = read(os.path.join(self.bands, f"band_{system}_{host}.extxyz"), ":")
        return self._b[k]

    def get(self, label):
        m = is_band(label)
        if m:
            return self.band_file(m.group(1), m.group(2))[int(m.group(3))]
        if label not in self._w:
            name = f"{label}_relaxed.extxyz"
            if os.path.isdir(self.structures):
                self._w[label] = read(os.path.join(self.structures, name))
            else:
                if self._tar is None:
                    self._tar = tarfile.open(self.structures)
                self._w[label] = read(io.StringIO(self._tar.extractfile(f"v2prod/{name}").read().decode()), format="extxyz")
        return self._w[label]

    def stored_energy(self, label):
        at = self.get(label)
        return float(at.calc.results["energy"]) if at.calc is not None else float(at.info["energy"])


def index_inputs(root):
    out = {}
    for f in glob.glob(os.path.join(root, "**", "*.in"), recursive=True) + \
            glob.glob(os.path.join(root, "**", "*.in.gz"), recursive=True):
        k = os.path.basename(f).removesuffix(".gz")[:-3]
        assert k not in out, f"input {k} found twice: {out[k]} and {f}"
        out[k] = f
    return out


def qe_input_geometry(path):
    """Species, cell and positions (A) and the 'calculation' value of a scripts/30 pw.x input."""
    t = a32.read_text(path)
    m = re.search(r"^CELL_PARAMETERS\s*\{?\s*(\w+)\s*\}?\s*\n", t, re.M)
    assert m and m.group(1).lower() == "angstrom", f"{path}: CELL_PARAMETERS not in angstrom"
    cell = np.array([[float(x) for x in l.split()[:3]] for l in t[m.end():].splitlines()[:3]])
    m = re.search(r"^ATOMIC_POSITIONS\s*\{?\s*(\w+)\s*\}?\s*\n", t, re.M)
    assert m and m.group(1).lower() == "angstrom", f"{path}: ATOMIC_POSITIONS not in angstrom"
    rows = []
    for l in t[m.end():].splitlines():
        p = l.split()
        if len(p) < 4 or not re.match(r"[A-Z][a-z]?$", p[0]):
            break
        rows.append(p)
    c = re.search(r"calculation\s*=\s*['\"](\w+)['\"]", t)
    return [p[0] for p in rows], cell, np.array([[float(x) for x in p[1:4]] for p in rows]), (c.group(1) if c else "scf")


def out_geometry(text):
    """Species, cell and positions (A) printed in the header of a pw.x output (alat units; celldm(1) in bohr)."""
    alat = float(re.search(r"celldm\(1\)=\s*([-\d.]+)", text).group(1)) * a32.BOHR
    nat = int(re.search(r"number of atoms/cell\s+=\s+(\d+)", text).group(1))
    ax = re.search(r"crystal axes: \(cart\. coord\. in units of alat\)\s*\n((?:\s*a\(\d\) = \(.*\)\s*\n){3})", text).group(1)
    cell = np.array([[float(x) for x in re.search(r"=\s*\((.*)\)", l).group(1).split()] for l in ax.strip().splitlines()])
    rows = text[text.index("positions (alat units)"):].splitlines()[1:nat + 1]
    pos = np.array([[float(x) for x in re.search(r"=\s*\((.*)\)", l).group(1).split()] for l in rows])
    return [l.split()[1] for l in rows], cell * alat, pos * alat


def output_check(label, path, at):
    """(failures, (dcell, dpos)): a complete output must be one single point of this geometry."""
    t = a32.read_text(path)
    n = {"'!' total energy": len(re.findall(r"^!\s+total energy", t, re.M)),
         "force-block": t.count("Forces acting on atoms"), "Fermi-energy": len(re.findall(r"the Fermi energy is", t))}
    f = [f"{label}: output has {v} {k} lines (a single point has one)" for k, v in n.items() if v > 1]
    try:
        sym, cell, pos = out_geometry(t)
    except (AttributeError, ValueError, IndexError) as e:
        return f + [f"{label}: output header geometry not parseable ({type(e).__name__})"], None
    if sym != at.get_chemical_symbols():
        return f + [f"{label}: output species or count differ from the geometry"], None
    d = (float(np.linalg.norm(cell - at.cell.array, axis=1).max()), float(np.linalg.norm(pos - at.positions, axis=1).max()))
    if not max(d) <= TOL_OUT:
        f.append(f"{label}: output header |dcell| {d[0]:.2e}, |dpos| {d[1]:.2e} A (tol {TOL_OUT:.0e})")
    return f, d


def position_check(labels, geo, inputs, outputs=None, required=None, geom=lambda l: l):
    """Archived input of each frame vs its geometry (cell per vector, positions per atom, TOL_POS; 'scf'), and each
    complete output in `outputs` by output_check. A missing input fails for labels in `required` (default all)."""
    outputs, required = outputs or {}, set(labels) if required is None else set(required)
    w = {"dcell": 0.0, "dpos": 0.0, "out_dcell": 0.0, "out_dpos": 0.0}; fails, no_input, n_in = [], [], 0
    for l in labels:
        at = geo.get(geom(l))
        if l in outputs:
            f, d = output_check(l, outputs[l], at); fails += f
            if d:
                w["out_dcell"], w["out_dpos"] = max(w["out_dcell"], d[0]), max(w["out_dpos"], d[1])
        if l not in inputs:
            if l in required:
                fails.append(f"{l}: no archived input")
            else:
                no_input.append(l)
            continue
        sym, cell, pos, calc = qe_input_geometry(inputs[l]); n_in += 1
        if calc != "scf":
            fails.append(f"{l}: input calculation '{calc}', not 'scf'")
        if sym != at.get_chemical_symbols():
            fails.append(f"{l}: input species or count differ"); continue
        dc = float(np.linalg.norm(cell - at.cell.array, axis=1).max())
        dp = float(np.linalg.norm(pos - at.positions, axis=1).max())
        w["dcell"], w["dpos"] = max(w["dcell"], dc), max(w["dpos"], dp)
        if not (dc <= TOL_POS and dp <= TOL_POS):
            fails.append(f"{l}: |dcell| {dc:.2e}, |dpos| {dp:.2e} A")
    return {"n_frames": len(labels), "n_inputs_checked": n_in, "n_outputs_checked": sum(l in outputs for l in labels),
            "max_dcell_A": w["dcell"], "max_dpos_A": w["dpos"], "tol_A": TOL_POS,
            "output_max_dcell_A": w["out_dcell"], "output_max_dpos_A": w["out_dpos"], "output_tol_A": TOL_OUT,
            "no_input_incomplete_frames": no_input, "failures": fails, "pass": not fails}


def read_dft(label, outputs, root):
    """(record, reason): F, forces (scripts/32 parse_qe, last block) and E_F (scripts/37 qe) of one output."""
    if label not in outputs:
        gave = glob.glob(os.path.join(root, "**", f"{label}.gaveup*"), recursive=True)   # gzipped too (item 1e)
        return None, ("gave up" if gave else "no output")
    q = a32.parse_qe(outputs[label])
    if q is None:
        return None, "no JOB DONE"
    if q["F_eV"] is None:
        return None, "no total energy"
    if not q["converged"]:
        return None, "SCF not converged"
    if q["forces"] is None:
        return None, "no force block"
    e = a37.qe(outputs[label])
    assert e["F"] == q["F_eV"], label
    if e["EF"] is None:
        return None, "no Fermi energy"
    return {"F": q["F_eV"], "EF": e["EF"], "forces": q["forces"], "path": outputs[label]}, None


# ---------------------------------------------------------------- model arms
def assert_float64_cpu(calc, name):
    import torch
    assert calc.default_dtype == "float64", f"{name}: calculator dtype {calc.default_dtype}"
    for m in calc.models:
        dts = {p.dtype for p in m.parameters()}
        assert dts == {torch.float64}, f"{name}: parameter dtypes {dts}"
    assert str(calc.device) == "cpu", f"{name}: device {calc.device}"


class Arm:
    """One model; single points by label (cached in memory, and on disk only with --cache)."""
    def __init__(self, name, calc, model_file, cache):
        assert_float64_cpu(calc, name)                         # before this arm evaluates any frame
        self.name, self.calc, self.file, self.sha = name, calc, model_file, sha256(model_file)
        self.cache, self.n_eval, self.n_cached, self.E, self.F = cache, 0, 0, {}, {}

    def evaluate(self, atoms):
        at = atoms.copy(); at.set_constraint(); at.calc = self.calc
        return float(at.get_potential_energy()), np.array(at.get_forces(), dtype=np.float64)

    def __call__(self, label, atoms):
        if label in self.E:
            return self.E[label]
        h = hashlib.sha256(atoms.numbers.tobytes() + atoms.positions.tobytes() + atoms.cell.array.tobytes()).hexdigest()
        p = self.cache and os.path.join(self.cache, f"{self.name}_{self.sha}_{label}.npz")
        if p and os.path.exists(p):
            z = np.load(p)
            if str(z["g"]) == h:
                self.E[label], self.F[label] = float(z["E"]), np.array(z["F"]); self.n_cached += 1
                return self.E[label]
        E, F = self.evaluate(atoms)
        self.E[label], self.F[label] = E, F; self.n_eval += 1
        if p:
            np.savez(p, E=E, F=F, g=h)
        return E

    def bad(self, labels, what="E"):
        """Labels (of those evaluated) whose energy ('E') or forces ('F') are not finite."""
        d = self.E if what == "E" else self.F
        return sorted(l for l in labels if l in d and not finite(d[l]))

    def info(self):
        return {"model_file": os.path.abspath(self.file), "sha256": self.sha, "dtype": self.calc.default_dtype,
                "device": str(self.calc.device), "head": getattr(self.calc, "head", None),
                "available_heads": list(getattr(self.calc, "available_heads", [])),
                "n_single_points": self.n_eval, "n_from_cache": self.n_cached,
                "non_finite_frames": sorted(set(self.bad(self.E, "E")) | set(self.bad(self.F, "F")))}


# ---------------------------------------------------------------- quantities (one arm, one DFT basis)
def basis_energies(D, vac, basis):
    if basis == "raw":
        return {l: d["F"] for l, d in D.items()}
    return {l: d["F"] - (d["EF"] - EF_REF) if vac[l] else d["F"] for l, d in D.items()}


def Ea(E, host, system):
    """E_a (meV) as scripts/32: max over images 2-4 of E_i - E_0 on the fixed path; None unless complete; NaN
    if any of the five energies is not finite (fail-closed: a NaN image never drops out of the max)."""
    labs = dict(zip(IMG, band_labels(host, system)))
    if any(l not in E for l in labs.values()):
        return None
    if not all(finite(E[l]) for l in labs.values()):
        return float("nan")
    return max(E[labs[i]] - E[labs[0]] for i in (2, 3, 4)) * 1000


def pair(Em, Ed, host, dop):
    """Paired dE_a (scripts/32: dopant minus undoped band of one host); None if a band is incomplete."""
    dd, dm = [Ea(Ed, host, s) for s in (dop, "undoped")], [Ea(Em, host, s) for s in (dop, "undoped")]
    if None in dd or None in dm:
        return None
    dm, dd = dm[0] - dm[1], dd[0] - dd[1]
    return {"dEa_model_meV": dm, "dEa_dft_meV": dd, "error_meV": dm - dd,
            "class_model": a32.band_class(dm) if finite(dm) else None, "class_dft": a32.band_class(dd)}


def site_labels(host, dop, j):
    return [f"{host}_{dop}{j}_vac", f"{host}_{dop}{j}_novac", f"{host}_vac", f"{host}_host"]   # scripts/37 eb() order


def eb_model(E, dv, d, v, h):
    """scripts/37 eb() for a model arm, without its |E_b| < 2 eV assertion (the same labels pass it on DFT)."""
    return (E[dv] - E[d] - E[v] + E[h]) * 1000


def sgn(x):
    return int(np.sign(x)) if finite(x) else None


def sites(Em, Ed, host, sel):
    """Far-referenced E_b (criterion 4, amendment g item 1) at every non-far WP2c site of a host (scripts/37)."""
    rec, out = sel[host], {}
    for dop in ("Sr", "GA"):
        st = {k: v["site"] for k, v in rec["sites"].items() if k.startswith(dop + "_")}
        eb = {n: (eb_model(Em, *site_labels(host, dop, j)), a37.eb(Ed, *site_labels(host, dop, j))) for n, j in st.items()}
        fm, fd = eb[f"{dop}_far"]
        for n, j in st.items():
            if n == f"{dop}_far":
                continue
            m, d = eb[n][0] - fm, eb[n][1] - fd
            out[f"{dop}{j}"] = {"name": n, "dopant": dop, "Eb_model_farref_meV": m, "Eb_dft_farref_meV": d,
                                "Eb_dft_not_farref_meV": eb[n][1], "error_meV": m - d, "near": n.endswith(NEAR),
                                "sign_agree": None if sgn(m) is None else sgn(m) == sgn(d)}
    return out


def force_rmse(arm, D, labels):
    assert all(arm.F[l].shape == D[l]["forces"].shape for l in labels)
    d = [arm.F[l] - D[l]["forces"] for l in labels]
    return float(np.sqrt(sum(float(np.sum(x ** 2)) for x in d) / sum(x.size for x in d))) if d else None


def crit6_values(arm, D, Ed, sel, f46):
    """(i), (ii) raw and E', (iii) raw and E' for one arm (unrounded)."""
    Em = arm.E
    out = {"i_eVA": force_rmse(arm, D, f46), "i_band_eVA": force_rmse(arm, D, [l for l in f46 if is_band(l)]),
           "i_wp2c_eVA": force_rmse(arm, D, [l for l in f46 if not is_band(l)])}
    for b in ("raw", "Eprime"):
        p = {f"{h}_{d}": pair(Em, Ed[b], h, d) for h, d in WP2B_PAIRS}
        out[f"ii_{b}"] = p
        out[f"ii_{b}_rms_meV"] = rms(x["error_meV"] for x in p.values())
        s = sites(Em, Ed[b], EB_HOST, sel)
        out[f"iii_{b}"] = s
        out[f"iii_{b}_rms_meV"] = rms(x["error_meV"] for x in s.values())
        for dop in ("Sr", "GA"):
            out[f"iii_{b}_rms_{dop}_meV"] = rms(x["error_meV"] for x in s.values() if x["dopant"] == dop)
    ss = float(np.sum(np.array([x["error_meV"] for x in out["iii_raw"].values()]) ** 2))
    out["iii_raw_GA128_share"] = float(out["iii_raw"]["GA128"]["error_meV"] ** 2 / ss) if finite(ss) and ss > 0 else None
    return out


def num(x, spec=".3f"):
    return "n/a" if x is None else format(x, spec)


# ---------------------------------------------------------------- reproduction gate
def gate(zs, D, missing, vac, sel, shell, wp2b, f46, geo, item1p):
    fm = sel[EB_HOST]["doped_fmax_final"]
    W = {(f["host"], f["system"], f["image"]): f["E_mace"] for f in wp2b["frames"]}

    def shell_energy(label):          # the stage at which each _relaxed structure was written (scripts/37 mace_eb)
        if label in (f"{EB_HOST}_host", f"{EB_HOST}_vac"):
            return shell["E_host" if label.endswith("_host") else "E_vac"]["E_eV"]
        m = re.match(rf"{EB_HOST}_(Sr|GA)(\d+)_(novac|vac)$", label)
        r = [r for r in shell["rows"] if r["dopant"] == m.group(1) and r["site_host_index"] == int(m.group(2))]
        assert len(r) == 1, label
        st = [x for x in r[0]["with_vac" if m.group(3) == "vac" else "no_vac"]["stages"] if abs(x["fmax_target"] - fm) < 1e-12]
        assert len(st) == 1, label
        return st[0]["E_eV"]

    def frames(name, ref):
        d = {l: zs.E[l] - e for l, e in ref.items()}
        w = max(d, key=lambda l: abs(d[l]) if finite(d[l]) else np.inf)
        return {"group": name, "n": len(d), "max_abs_diff_eV": abs(d[w]), "worst": w, "tol_eV": TOL_FRAME_EV,
                "pass": all(abs(x) <= TOL_FRAME_EV for x in d.values())}

    fe = [frames("m30/m32 band frames vs E_mace of wp2b_validation.json",
                 {l: W[(m.group(1), m.group(2), int(m.group(3)))] for l in f46 for m in [is_band(l)] if m}),
          frames(f"m30 WP2c frames vs shell_m30.json (E_host/E_vac top level; doped stage fmax {fm})",
                 {l: shell_energy(l) for l in f46 if not is_band(l)}),
          frames("item-1' band images vs energy field of ../bands", {l: geo.stored_energy(l) for l in item1p})]
    res = {"frame_energies": fe, "dft_missing": missing, "comparators": [], "exact": [], "reported_not_gated": None}
    if missing:                                              # the comparators cannot be computed
        res["pass"] = False
        return res, None
    Ed = {b: basis_energies(D, vac, b) for b in ("raw", "Eprime")}
    v = crit6_values(zs, D, Ed, sel, f46)
    cmp = [("(i) pooled, 46 frames (eV/A)", v["i_eVA"], GATE["i"], TOL_FORCE),
           ("(i) 30 band frames (eV/A)", v["i_band_eVA"], GATE["i_band"], TOL_FORCE),
           ("(i) 16 WP2c frames (eV/A)", v["i_wp2c_eVA"], GATE["i_wp2c"], TOL_FORCE)]
    for b in ("raw", "Eprime"):
        cmp += [(f"(ii) {b} {k} (meV)", v[f"ii_{b}"][k]["error_meV"], s, TOL_MEV) for k, s in GATE[f"ii_{b}"].items()]
        cmp.append((f"(ii) {b} RMS (meV)", v[f"ii_{b}_rms_meV"], GATE[f"ii_{b}_rms"], TOL_MEV))
    cmp += [(f"(iii) {k} (meV)", v["iii_raw"][k]["error_meV"], s, TOL_MEV) for k, s in GATE["iii"].items()]
    cmp.append(("(iii) RMS (meV)", v["iii_raw_rms_meV"], GATE["iii_rms"], TOL_MEV))
    res["comparators"] = [{"name": n, "value": x, "stated": s, "diff": x - s, "tol": t, "pass": bool(abs(x - s) <= t),
                           "rounded_equal": finite(x) and round(x, 6 if t == TOL_FORCE else 3) == s} for n, x, s, t in cmp]
    for b in ("raw", "Eprime"):
        ch = {k: [p["class_dft"], p["class_model"]] for k, p in v[f"ii_{b}"].items() if p["class_dft"] != p["class_model"]}
        res["exact"].append({"name": f"(ii) {b} class changes [DFT, MACE]", "value": ch, "stated": GATE["class_changes"][b],
                             "pass": ch == GATE["class_changes"][b]})
    ga = [s for s in v["iii_raw"].values() if s["name"] == "GA_near"][0]
    dis = None if ga["sign_agree"] is None else not ga["sign_agree"]
    res["exact"].append({"name": "(iii) GA near-shell sign disagrees", "value": dis,
                         "stated": GATE["GA_near_sign_disagrees"], "pass": dis is GATE["GA_near_sign_disagrees"]})
    try:                              # scripts/37 mace_eb on the same rows (its own stage-consistency assertion)
        for r in shell["rows"]:
            if f"{EB_HOST}_{r['dopant']}{r['site_host_index']}_vac" in f46:
                a37.mace_eb(r, shell, fm)
        eb_ok = True
    except AssertionError as e:
        eb_ok = f"scripts/37 mace_eb assertion: {e}"
    res["reported_not_gated"] = {
        "iii_rms_Sr": v["iii_raw_rms_Sr_meV"], "iii_rms_GA": v["iii_raw_rms_GA_meV"],
        "GA128_share_of_sum_sq": v["iii_raw_GA128_share"],
        "Sr_near_sign_agree": {s["name"]: s["sign_agree"] for s in v["iii_raw"].values() if s["near"] and s["dopant"] == "Sr"},
        "shell_m30_Eb_by_stage_consistent": eb_ok, "stated": REPORTED_NOT_GATED}
    res["pass"] = all(x["pass"] for x in fe + res["comparators"] + res["exact"])
    return res, v


def print_gate(g, pos):
    P = lambda b: "PASS" if b else "FAIL"
    print("\n== QE input and output check (input cell and positions within %.0e A; complete outputs: one single "
          "point, header within %.0e A)" % (TOL_POS, TOL_OUT))
    for p in pos:
        print(f"  {p['n_frames']:3d} frames ({p['n_inputs_checked']} inputs, {p['n_outputs_checked']} outputs): max "
              f"|dcell| {p['max_dcell_A']:.2e} A, max |dpos| {p['max_dpos_A']:.2e} A; output header max |dcell| "
              f"{p['output_max_dcell_A']:.2e}, |dpos| {p['output_max_dpos_A']:.2e} A  {P(p['pass'])}")
        for f in p["failures"]:
            print("     ", f)
    print("== Reproduction gate (zero-shot arm, amendment m item 3)")
    for x in g["frame_energies"]:
        print(f"  {x['group']}: n {x['n']}, max |dE| {x['max_abs_diff_eV']:.2e} eV ({x['worst']})  {P(x['pass'])}")
    for l, why in g["dft_missing"].items():
        print(f"  gate frame {l}: {why}  FAIL")
    for x in g["comparators"]:
        print(f"  {x['name']:<34s} recomputed {x['value']:+.7f}  stated {x['stated']:+.6f}  diff {x['diff']:+.2e}"
              f"  tol {x['tol']:.0e}  rounded-equal {x['rounded_equal']}  {P(x['pass'])}")
    for x in g["exact"]:
        print(f"  {x['name']}: {x['value']} (stated {x['stated']})  {P(x['pass'])}")
    r = g["reported_not_gated"]
    if r:
        print(f"  reported, not gated: (iii) RMS Sr {num(r['iii_rms_Sr'])}, GA {num(r['iii_rms_GA'])} meV; GA128 share "
              f"{num(r['GA128_share_of_sum_sq'])} (stated 9.203, 43.487, 0.893); Sr near signs agree "
              f"{r['Sr_near_sign_agree']}; shell_m30 E_b by stage consistent: {r['shell_m30_Eb_by_stage_consistent']}")
    print("  GATE", P(g["pass"]))


# ---------------------------------------------------------------- full-mode helpers
def external(path, name, model_sha):
    """(d) or (e) from the scripts/40 or 41 result: identity key, 'pass' true/false/null, 'model_sha256'; fail-closed."""
    if path is None:
        return {"status": "not yet evaluated", "pass": None}
    try:
        j = json.load(open(path))
    except (OSError, ValueError) as e:
        return {"status": f"cannot be evaluated ({type(e).__name__}: {e})", "pass": False, "file": path}
    if not isinstance(j, dict):
        return {"status": f"cannot be evaluated: {name} file is not a JSON object", "pass": False, "file": path}
    key, want = IDENT[name]
    sha, p = j.get("model_sha256"), j.get("pass")
    base = {"file": os.path.abspath(path), "file_sha256": sha256(path), "identity": {key: j.get(key)},
            "model_sha256_in_file": sha, "verdict_in_file": j.get("verdict"), "reasons_in_file": j.get("reasons")}
    if j.get(key) != want:
        return {**base, "status": f"cannot be evaluated: not a {name} result ({key} {j.get(key)!r}, expected {want!r})",
                "pass": False}
    if not isinstance(sha, str) or sha.lower() != model_sha:
        return {**base, "status": f"cannot be evaluated: {name} JSON model_sha256 {sha} is not the evaluated model",
                "pass": False}
    if p is None:
        return {**base, "status": f"cannot be evaluated ({name}: {j.get('verdict')})", "pass": False}
    if not isinstance(p, bool):
        return {**base, "status": f"cannot be evaluated: {name} JSON 'pass' is {p!r}", "pass": False}
    return {**base, "status": "pass" if p else "fail", "pass": p}


def git_state(paths):
    try:
        r = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True)
        s = subprocess.run(["git", "-C", ROOT, "status", "--porcelain", "--"] + paths, capture_output=True, text=True)
    except OSError as e:
        return {"head": None, "uncommitted": None, "error": str(e)}
    if r.returncode or s.returncode:
        return {"head": None, "uncommitted": None, "error": (r.stderr + s.stderr).strip()}
    return {"head": r.stdout.strip(), "uncommitted": s.stdout.strip().splitlines()}


def jsonable(x):
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, (np.floating, np.integer, np.bool_)):
        x = x.item()
    if isinstance(x, float) and not np.isfinite(x):
        return None                                          # NaN / inf: JSON null (strict JSON)
    return x


def write_json(obj, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(jsonable(obj), fh, indent=1, allow_nan=False)


def band_errors(arms, Ed, host, system):
    """Absolute E_a error (model - DFT) of one band on both bases, every arm; None if the DFT band is incomplete."""
    out = {}
    for b in ("raw", "Eprime"):
        d = Ea(Ed[b], host, system)
        out[b] = None if d is None else {"Ea_dft_meV": d, **{f"abs_Ea_error_{a.name}_meV": Ea(a.E, host, system) - d
                                                             for a in arms}}
    return out


def host_report(arms, D, Ed, sel, host, label):
    """Item 5 quantities of one m21 / training host for both arms: absolute E_a, paired dE_a, far-ref E_b."""
    out = {"label": label, "bands": {}, "pairs": {}, "sites": {}}
    for s in ("undoped", "GA", "Sr"):
        out["bands"][f"{host}_{s}"] = band_errors(arms, Ed, host, s)
    for dop in ("GA", "Sr"):
        out["pairs"][f"{host}_{dop}"] = {b: {a.name: pair(a.E, Ed[b], host, dop) for a in arms} for b in ("raw", "Eprime")}
    if host in sel:
        need = {l for n, v in sel[host]["sites"].items() for l in site_labels(host, n.split("_")[0], v["site"])}
        if need <= set(D):
            for b in ("raw", "Eprime"):
                for a in arms:
                    for k, x in sites(a.E, Ed[b], host, sel).items():
                        out["sites"].setdefault(f"{host}_{k}", {}).setdefault(b, {})[a.name] = x
            out["sites_rms_meV"] = {b: {a.name: rms(v[b][a.name]["error_meV"] for v in out["sites"].values()) for a in arms}
                                    for b in ("raw", "Eprime")}
        else:
            out["sites"] = {"missing_dft": sorted(need - set(D))}
    return out


def guarded(f, *args, **kw):
    """A reported-only computation (item 5, q = +1) never aborts the run: an error is recorded in its place."""
    try:
        return f(*args, **kw)
    except Exception as e:
        err = f"error (reported-only item): {type(e).__name__}: {e}"
        return (None, err) if f is read_dft else {"error": err}


def outcome_of(st):
    """Item 4 Outcomes (exhaustive, fail-closed) from the condition states: True, False, or None (not yet evaluated)."""
    if st["a"] is not True:
        return "No improvement"
    if any(st[k] is False for k in "bcde"):
        return "Improved but not validated"
    if all(st[k] is True for k in "bcde"):
        return "Validated"
    return "pending: (d)/(e) not yet evaluated; compose with --outcome-only after step 7 ('Validated' only if both pass)"


def improved(rows):
    """Number of (finetuned, zeroshot) error pairs with |fine-tuned| < |zero-shot| (non-finite never improves)."""
    rows = [r for r in rows if None not in r]
    return {"n_improve": sum(bool(finite(f) and abs(f) < abs(z)) for f, z in rows), "n": len(rows),
            "n_nonfinite_finetuned": sum(not finite(f) for f, _ in rows)}


def max_abs(xs):
    xs = list(xs)
    return max(abs(x) for x in xs) if xs and all(finite(x) for x in xs) else None


def outcome_only(a, ap, script_sha, git):
    """Step 8: the item-4 Outcome from a saved full-mode result and the scripts/40 and 41 results (no model, no QE)."""
    try:
        ev = json.load(open(a.outcome_only))
    except (OSError, ValueError) as e:
        print(f"--outcome-only {a.outcome_only}: unreadable ({type(e).__name__}: {e}); nothing written")
        sys.exit(EXIT_CHECK)
    ad, cond = ev.get("adoption") or {}, (ev.get("outcome") or {}).get("conditions") or {}
    msha = ((ev.get("arms") or {}).get("finetuned") or {}).get("sha256")
    probs = [w for ok, w in (
        (ev.get("script") == "scripts/39_wp3_evaluate.py" and ev.get("mode") == "full", "not a scripts/39 full-mode result"),
        ((ev.get("gate") or {}).get("pass") is True, "its reproduction gate did not pass"),
        (isinstance(msha, str) and re.fullmatch(r"[0-9a-f]{64}", msha or "") is not None, "no fine-tuned model sha256"),
        (all(isinstance(cond.get(k), bool) and (ad.get(k) or {}).get("met") is cond.get(k) for k in "abc"),
         "conditions (a)-(c) missing or inconsistent")) if not ok]
    if probs:
        print(f"--outcome-only {a.outcome_only}: " + "; ".join(probs) + "; nothing written")
        sys.exit(EXIT_CHECK)
    dev = bool(ev.get("stand_in")) or ev.get("cache") is not None
    if dev and inside(a.out, DS):
        ap.error(f"{a.outcome_only} is a stand-in or --cache run: give an --out outside {DS}")
    d_, e_ = external(a.wp3b_json, "WP3b", msha), external(a.md_json, "MD", msha)
    st = {"a": cond["a"], "b": cond["b"], "c": cond["c"], "d": d_["pass"], "e": e_["pass"]}
    outcome = outcome_of(st)
    budget = dict((ev.get("reported") or {}).get("error_budget") or {}, quoted=outcome == "Validated")
    c6 = ev.get("criterion6") or {}
    res = {"script": "scripts/39_wp3_evaluate.py", "plan": "amendment 2026-10-28m item 4, Outcomes", "mode": "outcome-only",
           "note": "composes the item-4 Outcome from the saved step-6 result; loads no model and reads no QE file, so it "
                   "is not a second evaluation (item 7, step 6)",
           "script_sha256": script_sha, "git": git,
           "eval_json": {"path": os.path.abspath(a.outcome_only), "file_sha256": sha256(a.outcome_only),
                         "script_sha256": ev.get("script_sha256"), "script_sha256_equal": ev.get("script_sha256") == script_sha,
                         "model_sha256": msha, "stand_in": ev.get("stand_in"), "cache": ev.get("cache")},
           "criterion6": {k: c6.get(k) for k in ("verdict", "verdict_label", "verdict_h", "verdict_h_label", "wording")},
           "adoption": {"a": ad["a"], "b": {k: ad["b"].get(k) for k in ("met", "status", "rms_meV", "class_changes", "basis")},
                        "c": {k: ad["c"].get(k) for k in ("met", "status", "label", "max_abs_error_meV")}, "d": d_, "e": e_},
           "outcome": {"outcome": outcome, "conditions": st}, "error_budget": budget}
    if ev.get("script_sha256") != script_sha:
        print(f"WARNING: {a.outcome_only} was written by scripts/39 sha256 {ev.get('script_sha256')}, this is {script_sha}")
    if dev:
        print("WARNING: the saved result is a stand-in or --cache run: not a WP3 result")
    write_json(res, a.out)
    print(f"== Outcome (item 4), model {msha}")
    print(f"  (a) {cond['a']} [{c6.get('verdict')}]; (b) {ad['b'].get('status')}; (c) {ad['c'].get('status')}")
    print(f"  (d) {d_['status']}; (e) {e_['status']}")
    print(f"  OUTCOME: {outcome}" + ("; error budget quoted" if outcome == "Validated" else ""))
    print("written", a.out)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--gate-only", action="store_true", help="step 1: reproduction gate and 46-frame check only")
    ap.add_argument("--outcome-only", metavar="WP3_EVAL_JSON", help="step 8: the item-4 Outcome from a saved full-mode "
                    "result and --wp3b-json / --md-json; loads no model, reads no QE file")
    ap.add_argument("--dft", default=DS, help="root of the archived QE outputs and inputs (any depth)")
    ap.add_argument("--v2", default=os.path.join(DS, "wp1_production"), help="shell_m30.json, wp2cde_selection.json")
    ap.add_argument("--structures", default=None, help="v2prod_structures.tar.gz or its extracted v2prod dir (default: in --v2)")
    ap.add_argument("--wp2b-json", default=os.path.join(DS, "wp2b", "wp2b_validation.json"))
    ap.add_argument("--bands", default=os.path.join(os.path.dirname(ROOT), "bands"))
    ap.add_argument("--model", help="the selected <run>/wp3.model (full mode)")
    ap.add_argument("--model-sha256", help="sha256 recorded in the dated wp3/ model note (full mode)")
    ap.add_argument("--dataset", help="scripts/33 output dir with test.xyz and dataset_meta.json (full mode)")
    ap.add_argument("--basis", choices=["Eprime", "raw"], help="must equal 'basis' of dataset_meta.json (full mode)")
    ap.add_argument("--wp3b-json", help="scripts/40 analyse result (adoption d)")
    ap.add_argument("--md-json", help="scripts/41 analyse result (adoption e)")
    ap.add_argument("--item5-hosts", nargs="*", default=VALID_HOSTS + TRAIN_HOSTS, help="m21 and training hosts (item 5)")
    ap.add_argument("--out", default=None, help="result JSON (defaults: <results>/wp3/wp3_eval.json, wp3_outcome.json)")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--cache", default=None, help="development tests only (--gate-only or a stand-in): reuse single points")
    a = ap.parse_args(argv)
    script_sha = sha256(os.path.abspath(__file__))                 # the code that runs, hashed at start
    mode = "outcome-only" if a.outcome_only else "gate-only" if a.gate_only else "full"
    flag = lambda ks: ", ".join("--" + k.replace("_", "-") for k in ks)
    if mode == "outcome-only":
        given = [k for k in ("gate_only", "model", "model_sha256", "dataset", "basis", "cache") if getattr(a, k)]
        if given:
            ap.error("--outcome-only loads no model and reads no QE file or dataset; drop " + flag(given))
        miss = [k for k in ("wp3b_json", "md_json") if not getattr(a, k)]
        if miss:
            ap.error("--outcome-only needs " + flag(miss))
        a.out = a.out or os.path.join(DS, "wp3", "wp3_outcome.json")
    elif mode == "gate-only":
        given = [k for k in ("model", "model_sha256", "dataset", "basis", "wp3b_json", "md_json") if getattr(a, k)]
        if given:
            ap.error("--gate-only reads no model, dataset or adoption file; drop " + flag(given))
    else:
        miss = [k for k in ("model", "model_sha256", "dataset", "basis") if getattr(a, k) is None]
        if miss:
            ap.error("full mode needs " + flag(miss))
        if not os.path.isfile(a.model):
            ap.error(f"--model {a.model}: no such file")
        a.model_sha256 = a.model_sha256.lower()
        a.out = a.out or os.path.join(DS, "wp3", "wp3_eval.json")
    if a.wp3b_json and a.md_json and os.path.realpath(a.wp3b_json) == os.path.realpath(a.md_json):
        ap.error("--wp3b-json and --md-json are the same file")
    stand_in_arg = mode == "full" and a.model_sha256 == FOUNDATION_SHA256
    if a.cache and mode == "full" and not stand_in_arg:
        ap.error("--cache is for development tests: only with --gate-only or a stand-in (the foundation file's sha256)")
    if a.cache and a.out and inside(a.out, DS):
        ap.error("--cache is for development tests: give an --out outside " + DS)
    if stand_in_arg and inside(a.out, DS):
        ap.error("--model-sha256 is the zero-shot foundation file (a stand-in): give an --out outside " + DS)
    if not set(a.item5_hosts) <= set(VALID_HOSTS + TRAIN_HOSTS):
        ap.error(f"--item5-hosts must be among {VALID_HOSTS + TRAIN_HOSTS}")
    git = git_state(CODE)
    if git["uncommitted"]:
        if a.out and inside(a.out, DS):
            ap.error(f"uncommitted {git['uncommitted']}: items 3 and 7.1 require scripts/39 committed; commit it, or "
                     f"give an --out outside {DS}")
        print(f"WARNING: uncommitted code {git['uncommitted']}: not a valid step-1, step-6 or step-8 run")
    elif git["uncommitted"] is None:
        print(f"WARNING: git state unknown ({git.get('error')}); the commit of scripts/39 is not verified")
    if mode == "outcome-only":
        return outcome_only(a, ap, script_sha, git)
    if mode == "full" and sha256(a.model) != a.model_sha256:
        print(f"model sha256 {sha256(a.model)} != --model-sha256 {a.model_sha256}: nothing evaluated")
        sys.exit(EXIT_SHA)
    if a.cache:
        os.makedirs(a.cache, exist_ok=True)
        print(f"WARNING: --cache {a.cache}: stored single points are reused; not a valid step-1 or step-6 run")

    import warnings
    for msg in (r"`torch\.jit\.\w+` is deprecated", r"Environment variable TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD detected"):
        warnings.filterwarnings("ignore", message=msg)          # benign load-time warnings only (0.3.16, torch 2.x)
    # ---- step 1: 46-frame input/output check, their DFT, the zero-shot arm, the gate. Any error is a gate failure.
    try:
        import torch; torch.set_num_threads(a.threads)
        import mace, ase
        from mace.calculators import mace_mp, MACECalculator
        from mace.calculators.foundations_models import download_mace_mp_checkpoint
        structures = a.structures or os.path.join(a.v2, "v2prod_structures.tar.gz")
        sel = json.load(open(os.path.join(a.v2, "wp2cde_selection.json")))
        shell = json.load(open(os.path.join(a.v2, f"shell_{EB_HOST}.json")))
        wp2b = json.load(open(a.wp2b_json))
        assert {d: sel[EB_HOST]["sites"][f"{d}_far"]["site"] for d in FAR_SITES} == FAR_SITES, "m30 far sites"
        geo = Geometry(a.bands, structures)
        outputs, inputs = a37.index_outputs(a.dft), index_inputs(a.dft)     # file names only; parsed below as allowed
        f46 = [l for h in ("m30", "m32") for s in ("undoped", "GA", "Sr") for l in band_labels(h, s)] + sel[EB_HOST]["wp2c_labels"]
        assert len(f46) == 46 and len(set(f46)) == 46, "46 m30/m32 frames"
        item1p = [l for h, d in EXTRA_PAIRS for s in (d, "undoped") for l in band_labels(h, s)]
        assert len(item1p) == 50
        vac = {}                                                    # 59 I: the vacancy cells of E' (item 1c)
        D, missing = {}, {}
        for l in f46:
            r, why = read_dft(l, outputs, a.dft)
            if r is None:
                missing[l] = why
            else:
                D[l] = r
        pos46 = position_check(f46, geo, inputs, {l: D[l]["path"] for l in D})
        zs = Arm("zeroshot", mace_mp(model="medium", device="cpu", default_dtype="float64"),
                 download_mace_mp_checkpoint("medium"), a.cache)
        for l in f46 + item1p:
            at = geo.get(l); vac[l] = at.get_chemical_symbols().count("I") == 59
            zs(l, at)
        g, z46 = gate(zs, D, missing, vac, sel, shell, wp2b, f46, geo, item1p)
        print_gate(g, [pos46])
    except Exception as e:
        print(f"\n== Reproduction gate (zero-shot arm, amendment m item 3)\n  error before or inside the gate: "
              f"{type(e).__name__}: {e}\n  GATE FAIL (nothing written; no item-1' file read; fine-tuned model not loaded)")
        sys.exit(EXIT_GATE)
    if not (g["pass"] and pos46["pass"]):
        sys.exit(EXIT_GATE)
    f64 = {"zeroshot": "asserted (dtype of calculator and every parameter, CPU) before its first frame",
           "finetuned": None if mode == "gate-only" else "asserted when built after the gate, before its first frame",
           "note": FLOAT64_NOTE}
    res = {"script": "scripts/39_wp3_evaluate.py", "plan": "amendment 2026-10-28m items 3-5",
           "mode": mode, "versions": {"mace": mace.__version__, "torch": torch.__version__,
           "ase": ase.__version__, "numpy": np.__version__}, "threads": a.threads, "script_sha256": script_sha, "git": git,
           "cache": {"dir": os.path.abspath(a.cache), "note": "development test: not a valid step-1 or step-6 run"} if a.cache else None,
           "zeroshot_is_item2_foundation_file": zs.sha == FOUNDATION_SHA256, "float64_assertion": f64,
           "position_check": {"gate_46": pos46}, "gate": g}
    if zs.sha != FOUNDATION_SHA256:
        print(f"WARNING: zero-shot model file sha256 {zs.sha} differs from the item-2 foundation hash")
    if mace.__version__ != "0.3.16":
        print(f"WARNING: mace-torch {mace.__version__}; the comparators were computed with 0.3.16")
    if mode == "gate-only":
        res["arms"] = {"zeroshot": zs.info()}
        if a.out:
            write_json(res, a.out)
            print("written", a.out)
        return 0
    state = {"ft_loaded": False, "ft": None}
    try:
        return step6(a, res, state, zs, z46, D, vac, sel, geo, outputs, inputs, f46, item1p, MACECalculator)
    except Exception as e:
        ft = state["ft"]
        print(f"ERROR after the gate: {type(e).__name__}: {e}\n  fine-tuned model loaded: {state['ft_loaded']}; "
              f"fine-tuned single points evaluated: {ft.n_eval if ft else 0} (+{ft.n_cached if ft else 0} cached); "
              f"no value printed, nothing written")
        sys.exit(EXIT_ERROR)


def step6(a, res, state, zs, z46, D, vac, sel, geo, outputs, inputs, f46, item1p, MACECalculator):
    # ---- step 6, after the gate: item-1' DFT, test-frame inputs and outputs, test.xyz, basis; then the fine-tuned arm
    status = {}
    for l in item1p:
        r, status[l] = read_dft(l, outputs, a.dft)
        if r is not None:
            D[l] = r
    test_labels = [l for l in f46 + item1p if l in D]
    pos_test = position_check(f46 + item1p, geo, inputs, {l: D[l]["path"] for l in test_labels}, required=test_labels)
    tl = [t.info["label"] for t in read(os.path.join(a.dataset, "test.xyz"), ":")]
    meta = json.load(open(os.path.join(a.dataset, "dataset_meta.json")))
    checks = {"labels_test_xyz": len(tl), "labels_evaluated": len(test_labels),
              "label_sets_equal": sorted(tl) == sorted(test_labels) and len(set(tl)) == len(tl),
              "only_in_test_xyz": sorted(set(tl) - set(test_labels)), "only_evaluated": sorted(set(test_labels) - set(tl)),
              "item1p_incomplete": {l: status[l] for l in item1p if l not in D},
              "item1p_no_input": pos_test["no_input_incomplete_frames"],
              "basis_argument": a.basis, "basis_dataset_meta": meta.get("basis"),
              "basis_equal": meta.get("basis") == a.basis}
    res["position_check"]["test_frames"] = pos_test
    if not (checks["label_sets_equal"] and pos_test["pass"] and checks["basis_equal"]):
        print(json.dumps(jsonable({"position_check_test_frames": pos_test, "test_set": checks}), indent=1))
        print("step-6 check failed (test-frame inputs or outputs, test.xyz label set, or --basis vs dataset_meta.json): "
              "fine-tuned model not loaded, nothing written")
        sys.exit(EXIT_CHECK)
    state["ft_loaded"] = "load attempted"
    ft = state["ft"] = Arm("finetuned", MACECalculator(model_paths=[a.model], device="cpu", default_dtype="float64",
                                                       head="Default"), a.model, a.cache)
    state["ft_loaded"] = True
    if ft.sha != a.model_sha256:
        print(f"model sha256 {ft.sha} != --model-sha256 {a.model_sha256} at load: nothing evaluated")
        sys.exit(EXIT_SHA)
    assert ft.calc.head == "Default" and "Default" in ft.calc.available_heads, (ft.calc.head, ft.calc.available_heads)
    stand_in = ft.sha == FOUNDATION_SHA256
    if stand_in:
        print("WARNING: the fine-tuned model file is the zero-shot foundation file: a stand-in, not a WP3 result")
    for l in test_labels:
        ft(l, geo.get(l))
    arms = (zs, ft)
    # item 5 hosts (m21 validation, training hosts), both arms; reported only
    i5 = [l for h in a.item5_hosts for s in ("undoped", "GA", "Sr") for l in band_labels(h, s)] + \
         [l for h in a.item5_hosts if h in sel for l in sel[h]["wp2c_labels"]]
    i5_missing = {}
    for l in i5:
        r, why = guarded(read_dft, l, outputs, a.dft)
        if r is None:
            i5_missing[l] = why; continue
        D[l] = r
        try:
            at = geo.get(l); vac[l] = at.get_chemical_symbols().count("I") == 59
            zs(l, at); ft(l, at)
        except Exception as e:                                 # reported-only: never aborts the run
            for d in (D, vac, zs.E, zs.F, ft.E, ft.F):
                d.pop(l, None)
            i5_missing[l] = f"error (reported-only item): {type(e).__name__}: {e}"
    pos_i5 = guarded(position_check, [l for l in i5 if l in D], geo, inputs, {l: D[l]["path"] for l in i5 if l in D})
    q1 = {k: guarded(read_dft, k, outputs, a.dft)[0] for k in (f"m30_{s}_img{i}_q1" for s in ("Sr", "undoped") for i in (0, 3))}
    pos_q1 = guarded(position_check, [k for k, v in q1.items() if v], geo, inputs, {k: v["path"] for k, v in q1.items() if v},
                     geom=lambda l: l.removesuffix("_q1"))
    Ed = {b: basis_energies(D, vac, b) for b in ("raw", "Eprime")}

    # ---- criterion 6 (item 3); a condition resting on a non-finite model value cannot be evaluated (fail-closed)
    band46, wp2c16 = [l for l in f46 if is_band(l)], [l for l in f46 if not is_band(l)]
    V = {"zeroshot": z46, "finetuned": crit6_values(ft, D, Ed, sel, f46)}
    bases = ["raw", "Eprime"] if a.basis == "Eprime" else ["raw"]
    keys = {"i": ("i_eVA", ft.bad(f46, "F")), **{f"ii_{b}": (f"ii_{b}_rms_meV", ft.bad(band46)) for b in bases},
            "iii": ("iii_raw_rms_meV", ft.bad(wp2c16))}
    cond = {}
    for k, (v, bad) in keys.items():
        ok = finite(V["finetuned"][v]) and not bad
        cond[k] = {"finetuned": V["finetuned"][v], "zeroshot": V["zeroshot"][v], "evaluable": ok,
                   "nonfinite_frames": bad, "strictly_below": bool(ok and V["finetuned"][v] < V["zeroshot"][v])}
    not_eval = {k: c["nonfinite_frames"] for k, c in cond.items() if not c["evaluable"]}
    verdict = "Improvement" if all(c["strictly_below"] for c in cond.values()) else "No improvement"
    vh = "Improvement" if all(cond[k]["strictly_below"] for k in ("i", "ii_raw", "iii")) else "No improvement"
    words = NOTES["wording_pass"] if verdict == "Improvement" else \
        "fail (sample: 4 pairs, 5 sites, 46 frames; never a reason to adopt, to change a threshold or to re-run)"
    if not_eval:
        words += f"; cannot be evaluated (non-finite fine-tuned values): {not_eval}"
    if a.basis == "Eprime" and cond["ii_raw"]["evaluable"] and not cond["ii_raw"]["strictly_below"] \
            and cond["ii_Eprime"]["strictly_below"]:
        words += "; " + NOTES["raw_fail_Eprime_pass"]
    c6 = {"conditions": cond, "verdict": verdict, "verdict_label": "criterion 6 (amendment m item 3)",
          "verdict_h": vh, "verdict_h_label": "criterion 6 as amended by h", "wording": words,
          "cannot_be_evaluated": not_eval or None,
          "basis": a.basis, "ii_bases_in_verdict": bases, "values": V, "stated_zeroshot_comparators": GATE,
          "iii_Eprime_rms_meV_reported": {k: V[k]["iii_Eprime_rms_meV"] for k in V},
          "raw_fallback": ("(ii) on raw F only; the two verdicts coincide" if a.basis == "raw" else None),
          "raw_fallback_Sr_expectation": SR_FALLBACK_NOTE if a.basis == "raw" else None,
          "power_note": NOTES["power"]}

    # ---- adoption (item 4)
    bb = a.basis
    pb = {f"{h}_{d}": {x.name: pair(x.E, Ed[bb], h, d) for x in arms} for h, d in TEST_PAIRS}
    incomplete = [k for k, v in pb.items() if v["finetuned"] is None]
    nf_b = ft.bad([l for h, d in TEST_PAIRS for s in (d, "undoped") for l in band_labels(h, s)])
    if incomplete:
        b_ = {"met": False, "status": "not met: incomplete", "incomplete_pairs": incomplete,
              "incomplete_frames": checks["item1p_incomplete"]}
    elif nf_b or not all(finite(v["finetuned"]["error_meV"]) for v in pb.values()):
        b_ = {"met": False, "status": "not met: cannot be evaluated (non-finite fine-tuned energy)"}
    else:
        e = [v["finetuned"]["error_meV"] for v in pb.values()]
        flips = [k for k, v in pb.items() if v["finetuned"]["class_model"] != v["finetuned"]["class_dft"]]
        b_ = {"met": rms(e) < RMS_TOL and not flips, "rms_meV": rms(e), "rms_below_20meV": rms(e) < RMS_TOL,
              "class_changes": flips}
        b_["status"] = "met" if b_["met"] else "not met"
    b_.update({"basis": bb, "n_pairs": len(TEST_PAIRS), "nonfinite_frames": nf_b, "pairs": pb,
               "reported_raw_F_beside": {k: {x.name: pair(x.E, Ed["raw"], *k.split("_")) for x in arms} for k in pb},
               "reported_4pair_rms_meV": {x.name: rms(pb[f"{h}_{d}"][x.name]["error_meV"] for h, d in WP2B_PAIRS) for x in arms},
               "power_note": NOTES["power_b"]})
    s3, nf_c = V["finetuned"]["iii_raw"], ft.bad(wp2c16)
    c_ = {"all_below_25meV": all(finite(x["error_meV"]) and abs(x["error_meV"]) < a37.TOL4 for x in s3.values()),
          "near_signs_agree": {x["name"]: x["sign_agree"] for x in s3.values() if x["near"]},
          "errors_meV": {k: x["error_meV"] for k, x in s3.items()}, "nonfinite_frames": nf_c,
          "max_abs_error_meV": max_abs(x["error_meV"] for x in s3.values()), "label": "one host (m30), 5 sites",
          "power_note": NOTES["power_c"], "raw_fallback_Sr_expectation": SR_FALLBACK_NOTE if a.basis == "raw" else None}
    c_["met"] = not nf_c and c_["all_below_25meV"] and all(v is True for v in c_["near_signs_agree"].values())
    c_["status"] = "met" if c_["met"] else \
        "not met: cannot be evaluated (non-finite fine-tuned energy)" if nf_c else "not met"
    d_, e_ = external(a.wp3b_json, "WP3b", ft.sha), external(a.md_json, "MD", ft.sha)
    st = {"a": verdict == "Improvement", "b": b_["met"], "c": c_["met"], "d": d_["pass"], "e": e_["pass"]}
    outcome = outcome_of(st)

    # ---- reported beside the verdict (no decision rests on these)
    pf = {l: {x.name: float(np.sqrt(np.mean((x.F[l] - D[l]["forces"]) ** 2))) for x in arms} for l in test_labels}
    p9 = {b: {f"{h}_{d}": {x.name: pair(x.E, Ed[b], h, d) for x in arms} for h, d in TEST_PAIRS} for b in ("raw", "Eprime")}
    s5 = {b: {k: {x: V[x][f"iii_{b}"][k] for x in V} for k in GATE["iii"]} for b in ("raw", "Eprime")}
    tb = {f"{h}_{s}": band_errors(arms, Ed, h, s) for h, d in TEST_PAIRS for s in ("undoped", d)}   # 16 bands
    err = lambda v: None if v is None else v["error_meV"]
    n_imp = {"frames_force_rmse": improved((v["finetuned"], v["zeroshot"]) for v in pf.values())}
    for b in ("raw", "Eprime"):
        n_imp[f"pairs_{b}"] = improved((err(v["finetuned"]), err(v["zeroshot"])) for v in p9[b].values())
        n_imp[f"sites_{b}"] = improved((v["finetuned"]["error_meV"], v["zeroshot"]["error_meV"]) for v in s5[b].values())
        n_imp[f"bands_abs_Ea_{b}"] = improved((v[b]["abs_Ea_error_finetuned_meV"], v[b]["abs_Ea_error_zeroshot_meV"])
                                              for v in tb.values() if v[b])
    img30 = lambda E: ((E["m30_Sr_img3"] - E["m30_Sr_img0"]) - (E["m30_undoped_img3"] - E["m30_undoped_img0"])) * 1000
    dft30 = {"q1": img30({k[:-3]: v["F"] for k, v in q1.items()}) if all(q1.values()) else None,
             "Eprime": img30(Ed["Eprime"]), "q0": img30(Ed["raw"])}
    cover = {k: {"zeroshot_meV": v["raw"]["abs_Ea_error_zeroshot_meV"], "finetuned_meV": v["raw"]["abs_Ea_error_finetuned_meV"],
                 "change_meV": v["raw"]["abs_Ea_error_finetuned_meV"] - v["raw"]["abs_Ea_error_zeroshot_meV"],
                 "Eprime_beside": v["Eprime"] and {"zeroshot_meV": v["Eprime"]["abs_Ea_error_zeroshot_meV"],
                                                   "finetuned_meV": v["Eprime"]["abs_Ea_error_finetuned_meV"]}}
             for k, v in tb.items() if k[:3] in {h for h, _ in EXTRA_PAIRS} and v["raw"]
             and v["raw"]["abs_Ea_error_zeroshot_meV"] > 59.0}
    i5r = {h: guarded(host_report, arms, D, Ed, sel, h, "m21 (validation): selected the checkpoint, so not independent; its GA and "
                          "Sr DFT maxima are unbracketed" if h in VALID_HOSTS else "training host: fit quality")
           for h in a.item5_hosts}
    budget = {"dEa_rms_meV": b_.get("rms_meV"), "dEa_sigma_ub95_meV": b_["rms_meV"] * 1.645 if b_.get("rms_meV") is not None else None,
              "Eb_rms_meV": V["finetuned"]["iii_raw_rms_meV"], "Eb_sigma_ub95_meV": V["finetuned"]["iii_raw_rms_meV"] * 2.089,
              "quoted": outcome == "Validated", "note": NOTES["budget"]}
    rep = {"i_all_test_frames_eVA": {x.name: force_rmse(x, D, test_labels) for x in arms}, "n_test_frames": len(test_labels),
           "ii_all_9_pairs": {b: {**{f"rms_{x.name}_meV": rms(v[x.name]["error_meV"] for v in p9[b].values() if v[x.name])
                                     for x in arms}, "n_complete": sum(v["finetuned"] is not None for v in p9[b].values()),
                                  "pairs": p9[b], "incomplete": [k for k, v in p9[b].items() if v["finetuned"] is None]}
                              for b in ("raw", "Eprime")},
           "iii_per_dopant_meV": {b: {f"{x}_{d}": V[x][f"iii_{b}_rms_{d}_meV"] for x in V for d in ("Sr", "GA")}
                                  for b in ("raw", "Eprime")},
           "iii_raw_GA128_share": {x: V[x]["iii_raw_GA128_share"] for x in V},
           "abs_Ea_16_test_bands": tb, "per_frame_force_rmse_eVA": pf, "per_site": s5, "n_improve": n_imp,
           "m30_img3_minus_img0_Sr_minus_undoped_meV": {"dft": dft30, "dft_stated": DFT_IMG30,
                                                        **{x.name: img30(x.E) for x in arms}},
           "item5": i5r, "item5_position_check": pos_i5, "item5_missing_dft": i5_missing, "q1_position_check": pos_q1,
           "coverage_item1p_zeroshot_abs_Ea_error_above_59meV": {
               "label": "the only unseen-host evidence on the low-barrier overestimate (item 5, coverage 1); gates nothing",
               "basis": "raw F (the basis of the item-5 +59 to +117 meV figures); E' beside", "bands": cover},
           "coverage_note": NOTES["coverage"], "error_budget": budget, "raw_Eb_note": NOTES["raw_Eb"],
           "raw_fallback_Sr_expectation": SR_FALLBACK_NOTE if a.basis == "raw" else "not applicable (E' basis)"}
    res.update({"arms": {x.name: x.info() for x in arms}, "stand_in": stand_in and
                "the fine-tuned arm is the zero-shot foundation file (stand-in for testing); not a WP3 result",
                "test_set": checks, "basis": {"argument": a.basis, "dataset_meta": meta.get("basis"), "EF_ref_eV": EF_REF},
                "criterion6": c6, "adoption": {"a": {"met": st["a"], "verdict": verdict}, "b": b_, "c": c_, "d": d_, "e": e_},
                "outcome": {"outcome": outcome, "conditions": st}, "reported": rep})
    write_json(res, a.out)

    # ---- terminal summary
    f = lambda x: num(x)
    print("\n== Criterion 6 (fine-tuned vs zero-shot; test hosts m30, m32)" + ("  [STAND-IN MODEL]" if stand_in else ""))
    for k, c in cond.items():
        u = 1000 if k == "i" else 1
        print(f"  {k:<9s} fine-tuned {c['finetuned'] * u:9.3f}  zero-shot {c['zeroshot'] * u:9.3f}  "
              f"{'strictly below' if c['strictly_below'] else 'NOT below'}" + ("  (meV/A)" if k == "i" else "  (meV)") +
              ("" if c["evaluable"] else f"  CANNOT BE EVALUATED (non-finite: {c['nonfinite_frames']})"))
    print(f"  (iii) E' RMS (reported): fine-tuned {f(V['finetuned']['iii_Eprime_rms_meV'])}, "
          f"zero-shot {f(V['zeroshot']['iii_Eprime_rms_meV'])} meV")
    if a.basis == "raw":
        print("  " + SR_FALLBACK_NOTE)
    print(f"  verdict: {verdict}  [{c6['verdict_label']}];  {vh}  [{c6['verdict_h_label']}]")
    print(f"  wording: {words}")
    print(f"== Adoption: (a) {'met' if st['a'] else 'not met'}; (b) {b_['status']} ({bb}" +
          (f", RMS {f(b_.get('rms_meV'))} meV, class changes {b_.get('class_changes')})" if 'rms_meV' in b_
           else f", incomplete pairs {incomplete}, non-finite frames {nf_b})"))
    print(f"  (c) {c_['status']} [{c_['label']}]: max |error| {f(c_['max_abs_error_meV'])} meV, "
          f"near signs agree {c_['near_signs_agree']}")
    print(f"      {NOTES['power_c']}" + (f"; {SR_FALLBACK_NOTE}" if a.basis == "raw" else ""))
    print(f"  (d) {d_['status']}; (e) {e_['status']}")
    print(f"  OUTCOME: {outcome}")
    print(f"  m30 (img3-img0)(Sr-undoped): fine-tuned {f(img30(ft.E))}, zero-shot {f(img30(zs.E))}; DFT q=+1 {f(dft30['q1'])}, "
          f"E' {f(dft30['Eprime'])}, q=0 {f(dft30['q0'])} meV (stated +40.2, +36.8, -2.9)")
    print(f"  input/output check, {pos_test['n_frames']} test frames ({pos_test['n_inputs_checked']} inputs, "
          f"{pos_test['n_outputs_checked']} outputs): max |dcell| {pos_test['max_dcell_A']:.2e}, max |dpos| "
          f"{pos_test['max_dpos_A']:.2e} A; no input (incomplete) {len(pos_test['no_input_incomplete_frames'])}; "
          f"test.xyz label set equal: {checks['label_sets_equal']}")
    print(f"  single points: zero-shot {zs.n_eval} (+{zs.n_cached} cached), fine-tuned {ft.n_eval} (+{ft.n_cached} cached)")
    print("written", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

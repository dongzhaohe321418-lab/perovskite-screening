#!/usr/bin/env python
"""WP3 post hoc diagnostics D1 (checkpoint trajectory, reason 6) and D2 (attribution of the barrier change along
the band path, reason 7), as WP3_DIAGNOSTICS_PLAN.md (committed at d69fe75 before any D1 or D2 value existed).

Status. Post hoc and reported only: nothing here changes a WP3 verdict, threshold or the outcome (amendment m
item 4), and no model is validated, selected, saved or used further. Laptop single points only (MACE float64 on
CPU): no MD, no relaxation, no training, no QE.

Inputs (committed or archived files only; every path written to the JSON is repository-relative, '~/...' or
'<CKPT_DIR>/...'):
    DFT          F, forces (scripts/32 parse_qe, last force block) and E_F (scripts/37 qe) of the archived pw.x
                 outputs, read by scripts/39 read_dft (complete outputs only); E' by scripts/39 basis_energies.
    dataset      wp3/dataset/{train,valid,test}.xyz and dataset_meta.json. Cross-check (fail-closed, exit 5) for every
                 frame used: REF_energy_raw = F and REF_EF = E_F within 1e-6 eV; REF_forces = the QE forces within
                 1e-6 eV/A per component (the extxyz file rounds to 1e-8); REF_energy + c_D_eV = E' within 1e-6 eV,
                 with c_D_eV the dataset_meta constant of the cell's class (Sr+V, GA+V; 0 for every other cell);
                 numbers equal, and cell and positions within 1e-6 A of the scripts/39 geometry (band images of
                 ../bands; _relaxed WP2c structures of v2prod_structures.tar.gz). D1: the valid.xyz label set must be
                 the 31 m21 frames.
    zero-shot    mace_mp(model="medium", device="cpu", default_dtype="float64"), the scripts/39 call; the file
                 download_mace_mp_checkpoint("medium") must have the item-2 foundation sha256 (exit 3).
    fine-tuned   --model (wp3/run2/wp3.model) by MACECalculator(model_paths=[...], device="cpu", default_dtype="float64",
                 head="Default"), the scripts/39 call; its sha256 must equal --model-sha256 (exit 3).
    checkpoints  the 20 kept run2 checkpoints <CKPT_DIR>/wp3_run-123_epoch-<n>.pt (off-repository; --checkpoints).
                 The set in the directory must be exactly the plan's 20 epochs, and they must be exactly the epochs at
                 which the logged m21 eval loss improved on its running minimum from epoch 0 (exit 3).
    training log run2/results/wp3_run-123_train.txt (JSON lines; 'eval' records carry loss, rmse_e_per_atom, rmse_f,
                 epoch; epoch null is Initial).
    wp3_eval     wp3/wp3_eval.json (step 6), the comparator of the reproduction checks.
    Provenance: the JSON head records the sha256 of every input file above (dataset xyz x3, E0s.json, dataset_meta.json,
    the training log, wp2cde_selection.json, the WP2c structures, wp3_eval.json, wp3.model; 'input_files'), the model
    files ('model_files') and the git status of the scripts and of every input inside the repository ('git'). The
    archived QE outputs and the band geometries are tied to the hashed dataset by the cross-check. The head and a part's
    result must not share a key (asserted). No bytecode is written (sys.dont_write_bytecode).

Checkpoint loading. A run2 checkpoint is torch.save({'model', 'optimizer', 'lr_scheduler'}) of mace-torch 0.3.16
(tools/checkpoint.py CheckpointBuilder); it is read with torch.load(weights_only=True). mace tools/train.py saves
it inside ema.average_parameters(), so 'model' holds the EMA-averaged weights (EMA 0.99), the same weights its
per-epoch m21 eval used; the EMA shadow is not stored separately. run_train then loads the best checkpoint (epoch
82) into the model and torch.saves the whole module as wp3.model. Here each 'model' state_dict is loaded with
strict=True into a deep copy of the wp3.model module (ScaleShiftMACE, float64) whose floating state_dict tensors are
first set to NaN, after asserting that its key set, shapes and dtypes equal wp3.model's; the copy is wrapped by
MACECalculator(models=[...], device="cpu", default_dtype="float64", head="Default"), the calculator's module is
asserted to hold every checkpoint tensor bitwise (exit 4), and the arm is asserted float64/CPU (scripts/39 Arm)
before its first frame. A tensor the load missed is therefore NaN, not wp3.model's value, so check 1 also tests the
loading (at epoch 82, whose weights equal wp3.model's) and check 2 tests it at the 19 other checkpoints. Each
checkpoint's lr_scheduler.last_epoch must equal the epoch of its file name (identity; exit 4). Whether the
state_dict is bitwise equal to wp3.model's is recorded for every checkpoint.

D1 checks (plan; fail-closed, exit 4; no D1 value is computed or printed before both pass):
    (1) the epoch-82 checkpoint reproduces the energies and forces of wp3.model on all 31 m21 frames within 1e-6 eV
        and 1e-6 eV/A (max over frames and force components);
    (2) every checkpoint's m21 RMSE_E per atom, sqrt(mean(((E - REF_energy)/N)^2)), and RMSE_F, sqrt(mean over all
        components (F - REF_forces)^2), against valid.xyz, equal the values mace logged for that epoch within 0.5%
        (relative).
    Reported, not gated: the zero-shot arm against the logged Initial record (RMSE_F directly; RMSE_E per atom after
    replacing the foundation E0s by E0s.json, the only difference of the mace fine-tuning start model).
Reproduction (task rule; fail-closed, exit 6): the zero-shot and epoch-82 item-5 values of m21 and m05 (scripts/39
host_report: absolute E_a errors, paired dE_a and far-referenced E_b, both bases) must equal
wp3_eval.json reported.item5 within 1e-6 meV (classes, signs and booleans exactly). D2: the zero-shot and fine-tuned
absolute E_a errors and the DFT E_a of all 37 bands (scripts/39 band_errors) must equal reported.abs_Ea_16_test_bands
and reported.item5 within 1e-6 meV.

D1 quantities, per model (Initial = zero-shot, and the 20 checkpoints), with the scripts/39 functions Ea, pair, sites:
    absolute E_a errors of the m21 and m05 bands, raw F and E'; paired dE_a errors (GA, Sr), both bases;
    far-referenced E_b errors at the 5 non-far sites of m21 and m05, raw F; per host the RMS of the 5.
    Q1  a kept checkpoint whose 5 m21 |E_b error| are all < 25 meV and whose Sr hinge and Sr flank far-referenced E_b
        signs agree with DFT (scripts/39 sites sign_agree). If yes: reason 6 contributes; if no: the first-shell Sr
        collapse is a property of the training, not of the selection. Both first-shell sites must be found by name
        (asserted; no vacuous all()). Beside: the same condition on the two first-shell Sr sites alone, and a caveat
        when a site that is not first-shell Sr fails at every checkpoint (the rule then cannot discriminate, and the
        reading rests on the first-shell-only check).
    Q2  per host (m21, m05) and first-shell Sr site (hinge, flank), over the models in training order (Initial, then
        the 20 kept epochs): the first model at which |E_b error| > 25 meV (the literal reading; 'Initial' when the
        site is already above before training; the error and its sign there are given), the first at which the error
        is < -25 meV (the direction of the collapse), and the first from which every later model has |error| > 25 meV;
        the same for both sites together. The epochs between kept checkpoints are not evaluated, so each onset is
        located only to its bracket (previous model, onset]. The fall of the m21 force RMSE is described from the
        logged eval records: RMSE_F at each onset and the fraction of the Initial -> epoch-82 fall reached there, both
        also as a range over the logged epochs of the bracket, and the first epoch whose RMSE_F is at or below the
        midpoint of that fall.
    Q3  Spearman's rho (average ranks) between the logged m21 eval loss and the m21 E_b RMS (raw F) over the 20
        checkpoints; no test (20 non-independent checkpoints).

D2 (all 37 bands with images 0, 2, 3, 4 and 6: 18 training, 3 m21, 16 test), at the band geometries:
    path work  W(i*) = -sum_k 1/2 (F_k + F_k+1) . dr_k over the available images 0 -> ... -> i* (trapezoid rule),
               dr_k = minimum-image change of the positions between successive images (ase find_mic, the band cell);
               per atom before summation.
    D2a        for zero-shot, fine-tuned and DFT (raw F energies and the q = 0 forces), i* = each one's own argmax over
               images 2-4 (scripts/39 Ea); closure = W(i*) - [E(i*) - E(0)]. A band whose DFT closure exceeds 20 meV
               in magnitude is 'not resolved' in D2b and D2c: its values are kept in the JSON under that status and
               enter no resolved-band summary or Q4 count. Reported beside (no rule rests on it): the closure of each
               segment 0-2, 2-3 and 3-4 separately, which locates the discretisation error.
    D2b        attribution of the fine-tuning change with dF = F_finetuned - F_zeroshot and i* = the DFT argmax image;
               per group, the sum, each group's share of the sum, and the closure of the sum against the direct E_a
               change E_a(fine-tuned) - E_a(zero-shot) (each its own argmax, the WP3 quantity) and, beside it, against
               the change of E(i*) - E(0) on the DFT segment.
    D2c        the same with dF = F_finetuned - F_DFT (raw F), against E_a(fine-tuned) - E_a(DFT, raw F).
    groups     at image 0, minimum image, distances to the hop midpoint r_I(0) + 1/2 mic(r_I(6) - r_I(0)):
               hop_I (the I with the largest minimum-image displacement from image 0 to image 6); inorganic_near (every
               other atom that is not C, N or H, d < 6 A); inorganic_far (d >= 6 A); organic_near and organic_far
               (molecules by bonding, scripts/38 molecule(): C, its N within 1.6 A, the H within 1.25 A of either;
               assigned whole by the distance of their C, < 6 A or >= 6 A). The molecules must partition the C, N
               and H atoms, and the five groups all atoms.
    Q4         over the resolved bands, from D2b: 'mainly local' if hop_I + inorganic_near carry more than half the
               summed change (share > 0.5) in more than half the resolved bands; 'mainly far or organic' if the
               complementary groups (inorganic_far + organic_near + organic_far) do; otherwise 'mixed'. The same count
               for D2c is reported beside it. The attribution is path-dependent (amendment l item 3): it assigns each
               interaction to the atoms on which its force acts. With no resolved band Q4 'cannot be read' (a
               departure: the plan's literal 'otherwise mixed' is then vacuous; it is kept beside as
               plan_literal_reading). A summary of D2b and D2c over all 37 bands is written beside (an addition), not a
               Q4 reading and not evidence for one: its share counts are named not_a_reading_share_counts and carry the
               attribution closure scale.
    Every departure, interpretation and addition is listed in each JSON (departures_from_plan, interpretations_of_plan,
    additions_to_plan) for the write-up.

    python scripts/44_wp3_diagnostics.py d1  --checkpoints <CKPT_DIR>
    python scripts/44_wp3_diagnostics.py d2
    python scripts/44_wp3_diagnostics.py all --checkpoints <CKPT_DIR>
    defaults: --model results/objective2/dopant_shell/wp3/run2/wp3.model, --model-sha256 the wp3/ model note's,
    --out-dir results/objective2/dopant_shell/wp3/diagnostics (d1_checkpoints.json, d2_path_attribution.json; the
    console output is appended to diag_console.log there), --threads 4.
Exit status: 0 done; 2 command-line error; 3 a model file's sha256 or the checkpoint set differs; 4 a D1 check or a
checkpoint load check failed; 5 a data check failed (an input file missing, DFT archive vs dataset, geometry, label
sets); 6 a reproduction of wp3_eval.json failed; 7 a failed assertion (molecule or group partition, cell or species of
a band, head, the first-shell Sr sites of Q1 or Q2, a key shared by the JSON head and a result) or an unexpected
error. On a failure nothing is written for that part (the console log keeps the diagnostics).
"""
import argparse, copy, datetime, json, os, re, sys
import importlib.util
sys.dont_write_bytecode = True      # no scripts/__pycache__ writes from the imports below (the task writes only 44 and wp3/diagnostics)
import numpy as np
from ase.geometry import find_mic
from ase.io import read

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DS = os.path.join(ROOT, "results", "objective2", "dopant_shell")


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


a39 = _load("a39", "39_wp3_evaluate.py")              # Ea, pair, sites, band_errors, host_report, read_dft, Arm, ...
a38 = _load("a38", "38_wp2e_displacement.py")         # molecule() by bonding
a37, a32 = a39.a37, a39.a32

MODEL_SHA256 = "3f7bf6f5aaaadc72d3954b56dfe3b7bcf5878b0f1be0c115e56c8bcaec65d2ca"   # wp3/MODEL_NOTE_2026-11-03.md
EPOCHS = [0, 2, 3, 4, 6, 7, 8, 11, 15, 26, 27, 31, 33, 35, 56, 59, 77, 80, 81, 82]  # plan, D1 Models
SELECTED = 82
CKPT = "wp3_run-123_epoch-{}.pt"
SYSTEMS = ("undoped", "GA", "Sr")
D1_HOSTS = ("m21", "m05")
TOL_E, TOL_F, TOL_POS, TOL_REL, TOL_REPRO = 1e-6, 1e-6, 1e-6, 0.005, 1e-6   # eV; eV/A; A; relative; meV
EB_BOUND, CLOSURE_BOUND, R_CUT = 25.0, 20.0, 6.0                            # meV; meV; A
FIRST_SHELL_SR = ("Sr_hinge", "Sr_flank")                                   # the first-shell Sr sites of Q1 and Q2
GROUPS = ("hop_I", "inorganic_near", "inorganic_far", "organic_near", "organic_far")
LOCAL = ("hop_I", "inorganic_near")
ORGANIC = {"C", "N", "H"}
EXIT_SHA, EXIT_CHECK, EXIT_DATA, EXIT_REPRO, EXIT_ERROR = 3, 4, 5, 6, 7


class Stop(Exception):
    def __init__(self, code, msg):
        super().__init__(msg); self.code = code


def require(ok, code, msg):
    if not ok:
        raise Stop(code, msg)


class Tee:
    """stdout to the terminal and appended to the console log, with local paths replaced (the checkpoint directory by
    <CKPT_DIR>, the repository by <repo>, the home directory by ~): the log is a repository file."""
    def __init__(self, path, ckpt_dir=None):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.f, self.out = open(path, "a"), sys.stdout
        sub = [(ckpt_dir, "<CKPT_DIR>")] if ckpt_dir else []
        sub += [(ROOT, "<repo>"), (os.path.expanduser("~"), "~")]
        self.sub = [(x, y) for p, y in sub for x in dict.fromkeys((os.path.abspath(p), os.path.realpath(p)))]

    def write(self, s):
        for x, y in self.sub:
            s = s.replace(x, y)
        self.out.write(s); self.f.write(s); self.flush()

    def flush(self):
        self.out.flush(); self.f.flush()


def rel(path, ckpt_dir=None):
    """A path for the JSON: '<CKPT_DIR>/...' for checkpoints, repository-relative inside or beside it, '~/...' at home."""
    p = os.path.realpath(path)
    if ckpt_dir and p.startswith(os.path.realpath(ckpt_dir) + os.sep):
        return "<CKPT_DIR>/" + os.path.relpath(p, os.path.realpath(ckpt_dir))
    home = os.path.realpath(os.path.expanduser("~"))
    r = os.path.relpath(p, os.path.realpath(ROOT))
    if not r.startswith(".." + os.sep + ".."):
        return r
    return "~/" + os.path.relpath(p, home) if p.startswith(home + os.sep) else os.path.basename(p)


def input_files(a):
    """The numerical input files (name -> path) whose sha256 and git status the JSON records."""
    f = {f"dataset_{sp}": os.path.join(a.dataset, f"{sp}.xyz") for sp in ("train", "valid", "test")}
    f.update({"E0s": os.path.join(a.dataset, "E0s.json"), "dataset_meta": os.path.join(a.dataset, "dataset_meta.json"),
              "train_log": a.train_log, "wp2cde_selection": os.path.join(a.v2, "wp2cde_selection.json"),
              "wp2c_structures": a.structures or os.path.join(a.v2, "v2prod_structures.tar.gz"),
              "wp3_eval_json": a.eval_json, "wp3_model": a.model})
    return f


def rms(x):
    return a39.rms(x)


def ranks(x):
    """Average ranks (1-based), ties averaged."""
    x = np.asarray(x, float); o = np.argsort(x, kind="mergesort"); r = np.empty(len(x)); i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and x[o[j + 1]] == x[o[i]]:
            j += 1
        r[o[i:j + 1]] = (i + j) / 2 + 1; i = j + 1
    return r


def spearman(x, y):
    rx, ry = ranks(x), ranks(y)
    return float(np.corrcoef(rx, ry)[0, 1])


def compare(ours, ref, path="", out=None):
    """Leaf-by-leaf comparison: numbers within TOL_REPRO, everything else exactly. Returns the list of rows."""
    out = [] if out is None else out
    if isinstance(ref, dict):
        if not isinstance(ours, dict) or set(ours) != set(ref):
            out.append({"path": path, "ok": False, "why": f"keys differ: {sorted(set(ours or {}) ^ set(ref))}"})
            return out
        for k in ref:
            if k != "label":
                compare(ours[k], ref[k], f"{path}/{k}", out)
    elif isinstance(ref, bool) or ref is None or isinstance(ref, str) or isinstance(ours, bool):
        out.append({"path": path, "ok": ours == ref, "ours": ours, "ref": ref})
    elif isinstance(ref, int) and isinstance(ours, (int, np.integer)) and not isinstance(ref, bool):
        out.append({"path": path, "ok": int(ours) == ref, "ours": int(ours), "ref": ref})
    elif isinstance(ref, (int, float)):
        d = abs(float(ours) - float(ref)) if a39.finite(ours) else float("inf")
        out.append({"path": path, "ok": d <= TOL_REPRO, "diff": d})
    else:
        out.append({"path": path, "ok": False, "why": f"unexpected type {type(ref).__name__}"})
    return out


def summarise_compare(rows):
    num = [r for r in rows if "diff" in r]
    return {"n_leaves": len(rows), "n_numeric": len(num), "max_abs_diff_meV": max((r["diff"] for r in num), default=None),
            "tol_meV": TOL_REPRO, "failures": [r for r in rows if not r["ok"]], "pass": all(r["ok"] for r in rows)}


# ---------------------------------------------------------------- data
class Data:
    """DFT (archived QE outputs), the scripts/39 geometry, the dataset records and the WP2c selection."""
    def __init__(self, a):
        self.a = a
        self.sel = json.load(open(os.path.join(a.v2, "wp2cde_selection.json")))
        self.geo = a39.Geometry(a.bands, a.structures or os.path.join(a.v2, "v2prod_structures.tar.gz"))
        self.outputs = a37.index_outputs(a.dft)
        self.meta = json.load(open(os.path.join(a.dataset, "dataset_meta.json")))
        self.ds, self.split = {}, {}
        for sp in ("train", "valid", "test"):
            for at in read(os.path.join(a.dataset, f"{sp}.xyz"), ":"):
                l = at.info["label"]
                assert l not in self.ds, f"dataset label {l} twice"
                self.ds[l], self.split[l] = at, sp
        self.D, self.vac = {}, {}

    def need(self, labels):
        """Read DFT for the labels (complete outputs only), then cross-check against the dataset (fail-closed)."""
        new = [l for l in labels if l not in self.D]
        miss = {}
        for l in new:
            r, why = a39.read_dft(l, self.outputs, self.a.dft)
            if r is None:
                miss[l] = why
            else:
                self.D[l] = r
                self.vac[l] = self.geo.get(l).get_chemical_symbols().count("I") == 59
        require(not miss, EXIT_DATA, f"DFT incomplete or missing: {miss}")
        return self.cross_check(new)

    def cd(self, at, vac):
        """c_D (eV) of dataset_meta for the cell's class on its basis: Sr+V, GA+V; 0 otherwise."""
        if not vac:
            return 0.0
        s = at.get_chemical_symbols()
        c = self.meta["c_D_meV"][self.meta["basis"]]
        if "Sr" in s:
            return c["Sr"] / 1000
        return c["GA"] / 1000 if s.count("N") > 2 * s.count("C") else 0.0

    def cross_check(self, labels):
        w = {"F_eV": 0.0, "EF_eV": 0.0, "forces_eVA": 0.0, "Eprime_eV": 0.0, "cD_eV": 0.0, "pos_A": 0.0, "cell_A": 0.0}
        fails, bitwise = [], True
        Ep = a39.basis_energies({l: self.D[l] for l in labels}, self.vac, self.meta["basis"])
        for l in labels:
            if l not in self.ds:
                fails.append(f"{l}: not in the dataset"); continue
            at, g, d = self.ds[l], self.geo.get(l), self.D[l]
            if list(at.numbers) != list(g.numbers):
                fails.append(f"{l}: numbers differ"); continue
            cd = self.cd(g, self.vac[l])
            x = {"F_eV": abs(at.info["REF_energy_raw"] - d["F"]), "EF_eV": abs(at.info["REF_EF"] - d["EF"]),
                 "forces_eVA": float(np.abs(at.arrays["REF_forces"] - d["forces"]).max()),
                 "Eprime_eV": abs(at.info["REF_energy"] + at.info["c_D_eV"] - Ep[l]), "cD_eV": abs(at.info["c_D_eV"] - cd),
                 "pos_A": float(np.linalg.norm(at.positions - g.positions, axis=1).max()),
                 "cell_A": float(np.linalg.norm(at.cell.array - g.cell.array, axis=1).max())}
            bitwise &= bool(np.array_equal(at.positions, g.positions) and np.array_equal(at.cell.array, g.cell.array))
            for k, v in x.items():
                w[k] = max(w[k], v)
                tol = TOL_F if k == "forces_eVA" else TOL_POS if k.endswith("_A") else TOL_E
                if not v <= tol:
                    fails.append(f"{l}: {k} differs by {v:.2e}")
        res = {"n_frames": len(labels), "max_abs_diff": w, "positions_cell_bitwise_equal": bitwise,
               "tol": {"energy_eV": TOL_E, "forces_eVA": TOL_F, "geometry_A": TOL_POS}, "failures": fails,
               "pass": not fails}
        require(not fails, EXIT_DATA, f"dataset vs archived QE / geometry: {fails[:10]}")
        return res


def fmt_check(x):
    return (f"{x['n_frames']} frames: max |d| " + ", ".join(f"{k} {float(v):.1e}" for k, v in x["max_abs_diff"].items()) +
            f"; positions and cell bitwise equal: {x['positions_cell_bitwise_equal']}")


def d1_labels(sel, host):
    return [l for s in SYSTEMS for l in a39.band_labels(host, s)] + list(sel[host]["wp2c_labels"])


def bands37():
    """(host, system, split) of the 37 bands: 18 training, 3 m21, 16 test (scripts/39 order of the test bands)."""
    out = [(h, s, "train") for h in a39.TRAIN_HOSTS for s in SYSTEMS] + [(h, s, "valid") for h in a39.VALID_HOSTS for s in SYSTEMS]
    for h, d in a39.TEST_PAIRS:
        for s in ("undoped", d):
            if (h, s, "test") not in out:
                out.append((h, s, "test"))
    assert len(out) == 37 and len(set(out)) == 37
    return out


# ---------------------------------------------------------------- models
class Models:
    """Zero-shot, wp3.model and the checkpoint arms (scripts/39 Arm: float64/CPU asserted before the first frame)."""
    def __init__(self, a):
        import torch, warnings
        for msg in (r"`torch\.jit\.\w+` is deprecated", r"Environment variable TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD detected"):
            warnings.filterwarnings("ignore", message=msg)
        torch.set_num_threads(a.threads)
        self.torch, self.a, self._zs, self._ft, self._base = torch, a, None, None, None
        from mace.calculators import mace_mp, MACECalculator
        from mace.calculators.foundations_models import download_mace_mp_checkpoint
        self.mace_mp, self.MACECalculator, self.dl = mace_mp, MACECalculator, download_mace_mp_checkpoint

    def zeroshot(self):
        if self._zs is None:
            f = self.dl("medium")
            require(a39.sha256(f) == a39.FOUNDATION_SHA256, EXIT_SHA, f"zero-shot file sha256 {a39.sha256(f)} is not the "
                    "item-2 foundation file")
            self._zs = a39.Arm("zeroshot", self.mace_mp(model="medium", device="cpu", default_dtype="float64"), f, None)
        return self._zs

    def finetuned(self):
        if self._ft is None:
            require(a39.sha256(self.a.model) == self.a.model_sha256, EXIT_SHA,
                    f"{rel(self.a.model)} sha256 {a39.sha256(self.a.model)} != --model-sha256 {self.a.model_sha256}")
            c = self.MACECalculator(model_paths=[self.a.model], device="cpu", default_dtype="float64", head="Default")
            assert c.head == "Default" and "Default" in c.available_heads, (c.head, c.available_heads)
            self._ft = a39.Arm("finetuned", c, self.a.model, None)
        return self._ft

    def base(self):
        """The wp3.model module (architecture and buffers) into which checkpoint weights are loaded."""
        if self._base is None:
            self.finetuned()
            self._base = self.torch.load(self.a.model, map_location="cpu", weights_only=False)
        return self._base

    def checkpoint(self, epoch):
        """(Arm, record) of one kept checkpoint, loaded strict into a copy of the wp3.model module."""
        path = os.path.join(self.a.checkpoints, CKPT.format(epoch))
        ck = self.torch.load(path, map_location="cpu", weights_only=True)
        require(set(ck) == {"model", "optimizer", "lr_scheduler"}, EXIT_CHECK, f"{CKPT.format(epoch)}: keys {sorted(ck)}")
        sd, ref = ck["model"], self.base().state_dict()
        require(set(sd) == set(ref), EXIT_CHECK, f"{CKPT.format(epoch)}: state_dict keys differ from wp3.model: "
                f"{sorted(set(sd) ^ set(ref))[:5]}")
        bad = [k for k in sd if sd[k].shape != ref[k].shape or sd[k].dtype != ref[k].dtype]
        require(not bad, EXIT_CHECK, f"{CKPT.format(epoch)}: shape or dtype differs from wp3.model at {bad[:5]}")
        m = copy.deepcopy(self.base())
        with self.torch.no_grad():                  # NaN prefill: a tensor the load misses gives NaN, not wp3.model's value
            for t in m.state_dict().values():
                if t.is_floating_point():
                    t.fill_(float("nan"))
        m.load_state_dict(sd, strict=True)
        le = ck["lr_scheduler"].get("last_epoch")
        require(le == epoch, EXIT_CHECK, f"{CKPT.format(epoch)}: lr_scheduler.last_epoch {le} is not the epoch of the file")
        calc = self.MACECalculator(models=[m], device="cpu", default_dtype="float64", head="Default")
        assert calc.head == "Default", calc.head
        csd = calc.models[0].state_dict()
        bad = sorted(k for k in sd if k not in csd or not self.torch.equal(csd[k], sd[k]))
        require(set(csd) == set(sd) and not bad, EXIT_CHECK, f"{CKPT.format(epoch)}: the calculator's module does not hold "
                f"the checkpoint tensors at {bad[:5]} (keys differ: {sorted(set(csd) ^ set(sd))[:5]})")
        rec = {"epoch": epoch, "file": rel(path, self.a.checkpoints), "sha256": a39.sha256(path),
               "checkpoint_keys": sorted(ck), "n_state_dict_entries": len(sd),
               "load": "load_state_dict(strict=True) into a NaN-prefilled copy of the wp3.model module",
               "calculator_module_holds_checkpoint_tensors": True,
               "state_dict_bitwise_equal_to_wp3_model": all(self.torch.equal(sd[k], ref[k]) for k in sd),
               "max_abs_param_diff_from_wp3_model": max(float((sd[k].double() - ref[k].double()).abs().max())
                                                        for k in sd if sd[k].is_floating_point() and sd[k].numel()),
               "lr_scheduler_last_epoch": le, "lr_scheduler_best": ck["lr_scheduler"].get("best"),
               "lr_scheduler_num_bad_epochs": ck["lr_scheduler"].get("num_bad_epochs")}
        return a39.Arm(f"epoch{epoch}", calc, path, None), rec


def run(arm, data, labels):
    for l in labels:
        arm(l, data.geo.get(l))


def atomic_energies(model):
    """{Z: E0 (eV)} of a MACE module (atomic_energies_fn buffer; first row for a head-indexed table)."""
    e = model.atomic_energies_fn.atomic_energies.detach().cpu().numpy()
    e = e[0] if e.ndim == 2 else e
    return {int(z): float(x) for z, x in zip(model.atomic_numbers.cpu().numpy(), e)}


def m21_metrics(E, F, valid, shift=None):
    """RMSE_E per atom (eV/atom) and RMSE_F (eV/A) of one model on valid.xyz, as mace's eval metrics."""
    de, df = [], []
    for l, at in valid.items():
        e = E[l] + (sum(shift[int(z)] for z in at.numbers) if shift else 0.0)
        de.append((e - at.info["REF_energy"]) / len(at)); df.append((F[l] - at.arrays["REF_forces"]).ravel())
    return {"rmse_e_per_atom_eV": float(np.sqrt(np.mean(np.square(de)))), "rmse_f_eVA": float(np.sqrt(np.mean(np.square(np.concatenate(df)))))}


def read_log(path):
    ev = [r for r in (json.loads(x) for x in open(path) if x.strip()) if r.get("mode") == "eval"]
    by = {}
    for r in ev:
        k = "initial" if r["epoch"] is None else int(r["epoch"])
        assert k not in by, f"two eval records for epoch {k}"
        by[k] = {"loss": r["loss"], "rmse_e_per_atom_eV": r["rmse_e_per_atom"], "rmse_f_eVA": r["rmse_f"]}
    best, imp = float("inf"), []
    for e in sorted(k for k in by if k != "initial"):
        if by[e]["loss"] < best:
            best = by[e]["loss"]; imp.append(e)
    return by, imp


# ---------------------------------------------------------------- D1
def host_quantities(E, data, Ed, host):
    """D1 quantities of one model at one host (scripts/39 Ea, pair, sites)."""
    out = {"abs_Ea_error_meV": {}, "dEa_error_meV": {}, "Eb_farref_raw": {}}
    for s in SYSTEMS:
        out["abs_Ea_error_meV"][f"{host}_{s}"] = {b: a39.Ea(E, host, s) - a39.Ea(Ed[b], host, s) for b in ("raw", "Eprime")}
    for d in ("GA", "Sr"):
        out["dEa_error_meV"][f"{host}_{d}"] = {b: a39.pair(E, Ed[b], host, d)["error_meV"] for b in ("raw", "Eprime")}
    for k, x in a39.sites(E, Ed["raw"], host, data.sel).items():
        out["Eb_farref_raw"][k] = {"name": x["name"], "error_meV": x["error_meV"], "Eb_model_farref_meV": x["Eb_model_farref_meV"],
                                   "sign_agree": x["sign_agree"], "near": x["near"]}
    out["Eb_rms_raw_meV"] = rms(x["error_meV"] for x in out["Eb_farref_raw"].values())
    return out


def dft_reference(data, Ed, host):
    out = {"Ea_dft_meV": {f"{host}_{s}": {b: a39.Ea(Ed[b], host, s) for b in ("raw", "Eprime")} for s in SYSTEMS},
           "dEa_dft_meV": {f"{host}_{d}": {b: a39.pair(Ed[b], Ed[b], host, d)["dEa_dft_meV"] for b in ("raw", "Eprime")}
                           for d in ("GA", "Sr")},
           "Eb_dft_farref_raw_meV": {k: {"name": x["name"], "Eb_dft_farref_meV": x["Eb_dft_farref_meV"]}
                                     for k, x in a39.sites(Ed["raw"], Ed["raw"], host, data.sel).items()}}
    return out


def first(seq, cond):
    return next((e for e, x in seq if cond(x)), None)


def d1(a, data, M, ev_json):
    print("\n==== D1: checkpoint trajectory (reason 6)")
    log, improved = read_log(a.train_log)
    have = sorted(int(m.group(1)) for f in os.listdir(a.checkpoints) for m in [re.fullmatch(r"wp3_run-123_epoch-(\d+)\.pt", f)] if m)
    print(f"  checkpoints in <CKPT_DIR>: {have}")
    print(f"  epochs at which the logged m21 eval loss improved (running minimum from epoch 0): {improved}")
    require(have == EPOCHS, EXIT_SHA, f"checkpoint set {have} is not the plan's {EPOCHS}")
    require(improved == EPOCHS, EXIT_SHA, f"logged improving epochs {improved} are not the plan's {EPOCHS}")
    labels = {h: d1_labels(data.sel, h) for h in D1_HOSTS}
    valid = {l: at for l, at in data.ds.items() if data.split[l] == "valid"}
    require(sorted(valid) == sorted(labels["m21"]) and len(valid) == 31, EXIT_DATA,
            f"valid.xyz labels are not the 31 m21 frames: {sorted(set(valid) ^ set(labels['m21']))}")
    xcheck = data.need(labels["m21"] + labels["m05"])
    print(f"  dataset vs archived QE and geometry, {fmt_check(xcheck)}  PASS")

    # ---- phase A: m21 frames for every model, then the two plan checks (nothing else is computed before they pass)
    zs, ft = M.zeroshot(), M.finetuned()
    run(zs, data, labels["m21"]); run(ft, data, labels["m21"])
    arms, recs = {}, {}
    for e in EPOCHS:
        arm, rec = M.checkpoint(e)
        run(arm, data, labels["m21"])
        arms[e], recs[e] = arm, rec
        print(f"  epoch {e:2d}: {rec['file']} loaded (strict; last_epoch {rec['lr_scheduler_last_epoch']}; bitwise = "
              f"wp3.model {rec['state_dict_bitwise_equal_to_wp3_model']}); {arm.n_eval} m21 single points")
    e82 = arms[SELECTED]
    dE = max(abs(e82.E[l] - ft.E[l]) for l in labels["m21"])
    dF = max(float(np.abs(e82.F[l] - ft.F[l]).max()) for l in labels["m21"])
    chk1 = {"name": "epoch-82 checkpoint vs wp3.model, 31 m21 frames", "n_frames": len(labels["m21"]),
            "max_abs_dE_eV": dE, "max_abs_dF_eVA": dF, "tol_eV": TOL_E, "tol_eVA": TOL_F,
            "state_dict_bitwise_equal": recs[SELECTED]["state_dict_bitwise_equal_to_wp3_model"],
            "what_it_tests": "each arm is a copy of the wp3.model module whose floating tensors are set to NaN before "
                             "load_state_dict(strict=True), and the calculator's module is asserted to hold the checkpoint "
                             "tensors bitwise; so check 1 tests the loading and the evaluation path at epoch 82 (a missed "
                             "tensor would give NaN), and check 2 tests them at the 19 checkpoints whose weights differ from "
                             "wp3.model",
            "pass": dE <= TOL_E and dF <= TOL_F}
    print(f"  check 1: epoch 82 vs wp3.model on 31 m21 frames: max |dE| {dE:.2e} eV, max |dF| {dF:.2e} eV/A "
          f"(tol 1e-6)  {'PASS' if chk1['pass'] else 'FAIL'}")
    chk2 = {"name": "m21 RMSE_E per atom and RMSE_F vs the training log, every checkpoint", "tol_relative": TOL_REL, "rows": {}}
    for e in EPOCHS:
        r = m21_metrics(arms[e].E, arms[e].F, valid)
        rd = {k: abs(r[k] - log[e][k]) / abs(log[e][k]) for k in r}
        chk2["rows"][e] = {"recomputed": r, "logged": {k: log[e][k] for k in r}, "relative_diff": rd,
                           "pass": all(v <= TOL_REL for v in rd.values())}
        print(f"  check 2: epoch {e:2d}: RMSE_E/atom {r['rmse_e_per_atom_eV'] * 1000:.6f} (log "
              f"{log[e]['rmse_e_per_atom_eV'] * 1000:.6f}) meV, RMSE_F {r['rmse_f_eVA'] * 1000:.5f} (log "
              f"{log[e]['rmse_f_eVA'] * 1000:.5f}) meV/A; rel diff {rd['rmse_e_per_atom_eV']:.1e}, {rd['rmse_f_eVA']:.1e}  "
              f"{'PASS' if chk2['rows'][e]['pass'] else 'FAIL'}")
    chk2["max_relative_diff"] = max(max(v["relative_diff"].values()) for v in chk2["rows"].values())
    chk2["pass"] = all(v["pass"] for v in chk2["rows"].values())
    require(chk1["pass"] and chk2["pass"], EXIT_CHECK, "D1 check failed (plan: the script stops); no D1 value computed")
    print("  D1 checks PASS")
    # reported, not gated: zero-shot vs the logged Initial (the start model differs from mace_mp only by E0s.json)
    e0j = {int(k): float(v) for k, v in json.load(open(os.path.join(a.dataset, "E0s.json"))).items()}
    e0f, e0m = atomic_energies(zs.calc.models[0]), atomic_energies(M.base())
    shift = {z: e0j[z] - e0f[z] for z in e0j}
    zi = m21_metrics(zs.E, zs.F, valid, shift)
    initial = {"recomputed_E0s_json": zi, "logged": {k: log["initial"][k] for k in zi},
               "relative_diff": {k: abs(zi[k] - log["initial"][k]) / log["initial"][k] for k in zi},
               "wp3_model_E0s_equal_E0s_json": all(abs(e0m[z] - e0j[z]) < 1e-12 for z in e0j) and set(e0m) == set(e0j),
               "note": "reported, not gated: mace_mp zero-shot with its foundation E0s replaced by E0s.json (the only "
                       "difference of the mace fine-tuning start model); forces unchanged"}
    print(f"  reported: zero-shot (E0s.json) vs logged Initial: RMSE_E/atom rel diff "
          f"{initial['relative_diff']['rmse_e_per_atom_eV']:.1e}, RMSE_F rel diff {initial['relative_diff']['rmse_f_eVA']:.1e}; "
          f"wp3.model E0s = E0s.json: {initial['wp3_model_E0s_equal_E0s_json']}")

    # ---- phase B: m05 frames, then the reproduction of wp3_eval.json item 5 for zero-shot and epoch 82
    run(zs, data, labels["m05"])
    for e in EPOCHS:
        arm, _ = M.checkpoint(e)
        arm.E.update(arms[e].E); arm.F.update(arms[e].F)
        run(arm, data, labels["m05"])
        arms[e] = arm
    Ed = {b: a39.basis_energies(data.D, data.vac, b) for b in ("raw", "Eprime")}
    from types import SimpleNamespace as NS
    repro = {}
    for h in D1_HOSTS:
        ref = ev_json["reported"]["item5"][h]
        ours = a39.host_report([NS(name="zeroshot", E=zs.E), NS(name="finetuned", E=arms[SELECTED].E)], data.D, Ed,
                               data.sel, h, ref["label"])
        repro[h] = summarise_compare(compare(ours, ref))
        print(f"  reproduction of wp3_eval.json reported.item5.{h} (zero-shot, epoch 82): {repro[h]['n_numeric']} numbers, "
              f"max |diff| {repro[h]['max_abs_diff_meV']:.2e} meV; {repro[h]['n_leaves'] - repro[h]['n_numeric']} exact "
              f"leaves  {'PASS' if repro[h]['pass'] else 'FAIL'}")
    require(all(r["pass"] for r in repro.values()), EXIT_REPRO,
            f"reproduction failed: {[f for r in repro.values() for f in r['failures']][:10]}")

    # ---- quantities
    order = [("Initial", zs)] + [(e, arms[e]) for e in EPOCHS]
    Q = {}
    for k, arm in order:
        Q[k] = {h: host_quantities(arm.E, data, Ed, h) for h in D1_HOSTS}
    dft = {h: dft_reference(data, Ed, h) for h in D1_HOSTS}
    # Q1
    q1rows = {}
    for e in EPOCHS:
        s = Q[e]["m21"]["Eb_farref_raw"]
        assert len(s) == 5, (e, sorted(s))
        fs = [x for x in s.values() if x["name"] in FIRST_SHELL_SR]
        sg = {x["name"]: x["sign_agree"] for x in fs}
        assert len(fs) == 2 and set(sg) == set(FIRST_SHELL_SR), (e, sg)        # no vacuous all() over a missing site
        q1rows[e] = {"max_abs_error_meV": max(abs(x["error_meV"]) for x in s.values()),
                     "all_below_25meV": all(abs(x["error_meV"]) < EB_BOUND for x in s.values()),
                     "sites_at_or_above_25meV": [f"{k} ({x['name']})" for k, x in s.items() if not abs(x["error_meV"]) < EB_BOUND],
                     "Sr_hinge_flank_signs_agree": sg, "meets": all(abs(x["error_meV"]) < EB_BOUND for x in s.values())
                     and all(v is True for v in sg.values()),
                     "first_shell_Sr_only_meets": all(abs(x["error_meV"]) < EB_BOUND and x["sign_agree"] is True for x in fs)}
    q1_yes = [e for e, r in q1rows.items() if r["meets"]]
    q1_fs = [e for e, r in q1rows.items() if r["first_shell_Sr_only_meets"]]
    best = min(EPOCHS, key=lambda e: q1rows[e]["max_abs_error_meV"])
    s0 = Q["Initial"]["m21"]["Eb_farref_raw"]
    assert all(set(Q[e]["m21"]["Eb_farref_raw"]) == set(s0) for e in EPOCHS), "m21 site keys differ between models"
    lab = lambda k: f"{k} ({s0[k]['name']})"
    err = lambda e, k: Q[e]["m21"]["Eb_farref_raw"][k]["error_meV"]
    fail_init = [lab(k) for k in s0 if not abs(err("Initial", k)) < EB_BOUND]
    fail_all = [k for k in s0 if all(not abs(err(e, k)) < EB_BOUND for e in EPOCHS)]
    fixed = [k for k in fail_all if s0[k]["name"] not in FIRST_SHELL_SR]
    caveat = None
    if fixed:
        caveat = ("the plan rule cannot discriminate here: " + "; ".join(
            f"{lab(k)}, not a first-shell Sr site, has |error| >= 25 meV at every kept checkpoint ({min(err(e, k) for e in EPOCHS):+.1f} "
            f"to {max(err(e, k) for e in EPOCHS):+.1f} meV; Initial {err('Initial', k):+.1f})" for k in fixed) +
            ", so no checkpoint could meet the rule whatever happened at the first-shell Sr sites; the reading about the "
            "first-shell Sr collapse rests on the first-shell-only check beside it, which is met by " +
            ("no checkpoint" if not q1_fs else f"epochs {q1_fs}"))
    q1 = {"question": "a kept checkpoint whose 5 m21 |far-ref E_b error| (raw F) are all < 25 meV, with the Sr hinge and "
                      "flank signs right", "answer": "yes" if q1_yes else "no", "checkpoints_meeting": q1_yes,
          "reading": ("selecting on the whole-cell m21 loss passed over a checkpoint that was better on this quantity "
                      "(reason 6 contributes)") if q1_yes else
                     "the collapse of the first-shell Sr E_b is a property of the training, not of the selection",
          "caveat": caveat,
          "sites_failing_at_every_checkpoint": [lab(k) for k in fail_all],
          "sites_failing_at_every_checkpoint_not_first_shell_Sr": [lab(k) for k in fixed],
          "smallest_max_abs_error": {"epoch": best, "max_abs_error_meV": q1rows[best]["max_abs_error_meV"],
                                     "sites_at_or_above_25meV": q1rows[best]["sites_at_or_above_25meV"]},
          "initial_beside": {"max_abs_error_meV": max(abs(x["error_meV"]) for x in s0.values()),
                             "sites_at_or_above_25meV": fail_init},
          "beside_first_shell_Sr_only": {
              "note": "reported beside, not the Q1 rule: the same condition on the two first-shell Sr sites alone (|error| < "
                      "25 meV and the sign right at both), to show whether the answer rests on them",
              "checkpoints_meeting": q1_fs},
          "rows": q1rows}
    # Q2: the models in training order, Initial (the zero-shot start model, before epoch 0) first
    seqm = ["Initial"] + EPOCHS
    lg = lambda e: log["initial" if e == "Initial" else e]
    f0, f82 = log["initial"]["rmse_f_eVA"], log[SELECTED]["rmse_f_eVA"]
    allep = sorted(k for k in log if k != "initial")
    assert allep == list(range(len(allep))) and allep[0] == 0, f"logged eval epochs are not 0..n: {allep[:5]}..."
    mid = 0.5 * (f0 + f82)
    fall = lambda e: (f0 - lg(e)["rmse_f_eVA"]) / (f0 - f82)

    def onset(e):
        """An onset first seen at model e (Initial or a kept epoch), with its bracket: the epochs between kept
        checkpoints are not evaluated, so a crossing first seen at kept epoch e, and not at the previous model p, lies
        at a logged epoch in (p, e] (an earlier excursion at an epoch that was not kept is not excluded)."""
        if e is None:
            return None
        if e == "Initial":
            return {"model": "Initial", "previous_model": None, "logged_epochs_in_bracket": [], "exact": True,
                    "note": "already at Initial, before any training", "rmse_f_meV_A": f0 * 1000,
                    "rmse_f_fall_fraction": 0.0, "rmse_f_meV_A_range": [f0 * 1000] * 2, "rmse_f_fall_fraction_range": [0.0, 0.0]}
        p = seqm[seqm.index(e) - 1]
        br = [x for x in allep if (p == "Initial" or x > p) and x <= e]
        assert br and br[-1] == e, (e, p, br)
        return {"model": e, "previous_model": p, "logged_epochs_in_bracket": br, "exact": len(br) == 1,
                "rmse_f_meV_A": lg(e)["rmse_f_eVA"] * 1000, "rmse_f_fall_fraction": fall(e),
                "rmse_f_meV_A_range": [min(lg(x)["rmse_f_eVA"] for x in br) * 1000, max(lg(x)["rmse_f_eVA"] for x in br) * 1000],
                "rmse_f_fall_fraction_range": [min(fall(x) for x in br), max(fall(x) for x in br)]}

    q2 = {"definition": "per host and first-shell Sr site, over the models in training order (Initial, then the 20 kept "
                        "epochs): the first model with |far-ref E_b error| > 25 meV (literal; 'Initial' = already above "
                        "before any training); the first with error < -25 meV (collapse direction); the first from which "
                        "every later model has |error| > 25 meV. Each onset is located only to its bracket (previous "
                        "model, onset]: the epochs between kept checkpoints are not evaluated; the logged m21 RMSE_F and "
                        "the fraction of its Initial -> epoch-82 fall are given at the onset and as a range over the "
                        "logged epochs of the bracket",
          "rmse_f_fall": {"initial_meV_A": f0 * 1000, "epoch82_meV_A": f82 * 1000, "midpoint_meV_A": mid * 1000,
                          "first_epoch_at_or_below_midpoint": first(((e, log[e]["rmse_f_eVA"]) for e in allep), lambda x: x <= mid),
                          "first_epoch_below_initial": first(((e, log[e]["rmse_f_eVA"]) for e in allep), lambda x: x < f0),
                          "logged_rmse_f_meV_A_kept": {e: log[e]["rmse_f_eVA"] * 1000 for e in EPOCHS},
                          "logged_rmse_f_meV_A_all_epochs": {e: log[e]["rmse_f_eVA"] * 1000 for e in allep},
                          "fall_fraction_all_epochs": {e: fall(e) for e in allep}},
          "hosts": {}}
    for h in D1_HOSTS:
        s0h = Q["Initial"][h]["Eb_farref_raw"]
        key = {s0h[k]["name"]: k for k in s0h}
        assert len(key) == len(s0h) and set(FIRST_SHELL_SR) <= set(key), (h, sorted(key))
        E = lambda e, n: Q[e][h]["Eb_farref_raw"][key[n]]["error_meV"]
        rows = {}
        for nm in FIRST_SHELL_SR:
            seq = [(e, E(e, nm)) for e in seqm]
            lit = first(seq, lambda x: abs(x) > EB_BOUND)
            neg = first(seq, lambda x: x < -EB_BOUND)
            stay = next((seqm[i] for i in range(len(seqm)) if all(abs(x) > EB_BOUND for _, x in seq[i:])), None)
            rows[nm] = {"site": key[nm], "initial_error_meV": E("Initial", nm),
                        "abs_gt_25_at_initial": abs(E("Initial", nm)) > EB_BOUND,
                        "errors_meV": dict(seq), "first_epoch_abs_gt_25": lit, "error_there_meV": dict(seq).get(lit),
                        "first_epoch_below_minus_25": neg, "first_epoch_staying_abs_gt_25": stay,
                        "onsets": {"literal": onset(lit), "negative": onset(neg), "staying": onset(stay)}}
        both = first(((e, e) for e in seqm), lambda e: all(abs(E(e, n)) > EB_BOUND for n in FIRST_SHELL_SR))
        bneg = first(((e, e) for e in seqm), lambda e: all(E(e, n) < -EB_BOUND for n in FIRST_SHELL_SR))
        q2["hosts"][h] = {"sites": rows, "first_epoch_both_abs_gt_25": both, "first_epoch_both_below_minus_25": bneg,
                          "onsets_both": {"literal": onset(both), "negative": onset(bneg)}}
    # Q3
    loss = [log[e]["loss"] for e in EPOCHS]
    ebr = [Q[e]["m21"]["Eb_rms_raw_meV"] for e in EPOCHS]
    q3 = {"rho_loss_vs_m21_Eb_rms": spearman(loss, ebr), "n": len(EPOCHS), "method": "Spearman, average ranks; no test",
          "note": "the kept checkpoints are the epochs at which the m21 loss improved, so the loss ranks them in reverse "
                  "epoch order", "loss": dict(zip(EPOCHS, loss)), "m21_Eb_rms_raw_meV": dict(zip(EPOCHS, ebr))}
    try:
        from scipy.stats import spearmanr
        q3["scipy_check"] = float(spearmanr(loss, ebr)[0])
    except ImportError:
        q3["scipy_check"] = None

    # ---- print
    print("\n  m21 / m05 far-referenced E_b errors (raw F, meV), logged m21 loss, RMSE_E/atom (meV), RMSE_F (meV/A)")
    sk = {h: list(Q["Initial"][h]["Eb_farref_raw"]) for h in D1_HOSTS}
    print("  model     loss      RMSE_E  RMSE_F | m21 " + " ".join(f"{k:>7s}" for k in sk["m21"]) + "    RMS | m05 " +
          " ".join(f"{k:>7s}" for k in sk["m05"]) + "    RMS")
    for k, _ in order:
        lg = log["initial" if k == "Initial" else k]
        row = f"  {str(k):<8s} {lg['loss']:8.5f} {lg['rmse_e_per_atom_eV'] * 1000:7.4f} {lg['rmse_f_eVA'] * 1000:7.3f} |     "
        for h in D1_HOSTS:
            row += " ".join(f"{Q[k][h]['Eb_farref_raw'][s]['error_meV']:+7.1f}" for s in sk[h]) + f" {Q[k][h]['Eb_rms_raw_meV']:6.1f} |     "
        print(row.rstrip(" |"))
    print("\n  absolute E_a errors raw F (meV) | paired dE_a errors raw / E' (meV)")
    for k, _ in order:
        print(f"  {str(k):<8s} " + "  ".join(" ".join(f"{Q[k][h]['abs_Ea_error_meV'][f'{h}_{s}']['raw']:+6.1f}" for s in SYSTEMS)
                                       for h in D1_HOSTS) + " | " +
              "  ".join(" ".join(f"{Q[k][h]['dEa_error_meV'][f'{h}_{d}'][b]:+6.1f}" for d in ("GA", "Sr") for b in ("raw", "Eprime"))
                        for h in D1_HOSTS))
    print(f"\n  Q1: {q1['answer']}; checkpoints meeting: {q1_yes}; smallest max |m21 E_b error| {q1['smallest_max_abs_error']}; "
          f"sites >= 25 meV per checkpoint: " + "; ".join(f"{e}: {len(r['sites_at_or_above_25meV'])}" for e, r in q1rows.items()) +
          f"\n      beside (first-shell Sr only): checkpoints meeting {q1['beside_first_shell_Sr_only']['checkpoints_meeting']}"
          f"\n      caveat: {q1['caveat']}")

    def fmt_onset(o):
        if o is None:
            return "never"
        if o["model"] == "Initial":
            return "Initial (already)"
        f = o["rmse_f_fall_fraction_range"]
        if o["exact"]:
            return f"epoch {o['model']} (after {o['previous_model']}; RMSE_F fall fraction {f[0]:.2f})"
        return (f"an epoch in ({o['previous_model']}, {o['model']}] (kept epoch {o['model']}; RMSE_F fall fraction "
                f"{f[0]:.2f}-{f[1]:.2f})")
    for h in D1_HOSTS:
        r = q2["hosts"][h]
        print(f"  Q2 {h}: " + "; ".join(f"{n} (Initial {v['initial_error_meV']:+.1f}) first |err|>25 at {fmt_onset(v['onsets']['literal'])} "
                                        f"({a39.num(v['error_there_meV'], '+.1f')}), first < -25 at {fmt_onset(v['onsets']['negative'])}, "
                                        f"stays >25 from {fmt_onset(v['onsets']['staying'])}" for n, v in r["sites"].items()) +
              f"; both > 25 at {fmt_onset(r['onsets_both']['literal'])}, both < -25 at {fmt_onset(r['onsets_both']['negative'])}")
    print(f"  Q2 RMSE_F fall: Initial {f0 * 1000:.3f} -> epoch 82 {f82 * 1000:.3f} meV/A; first epoch at or below the "
          f"midpoint {mid * 1000:.3f}: {q2['rmse_f_fall']['first_epoch_at_or_below_midpoint']}; first below Initial: "
          f"{q2['rmse_f_fall']['first_epoch_below_initial']}")
    print(f"  Q3: Spearman rho(m21 loss, m21 E_b RMS) over 20 checkpoints = {q3['rho_loss_vs_m21_Eb_rms']:+.4f} "
          f"(scipy {a39.num(q3['scipy_check'], '+.4f')})")

    models = {}
    for k, arm in order:
        ent = {"model": "zero-shot (Initial)" if k == "Initial" else f"checkpoint epoch {k}",
               "logged_m21": log["initial" if k == "Initial" else k], "quantities": Q[k]}
        if k != "Initial":
            ent["checkpoint"] = recs[k]
            ent["recomputed_m21"] = chk2["rows"][k]["recomputed"]
        models[str(k)] = ent
    return {"part": "D1", "plan": "WP3_DIAGNOSTICS_PLAN.md D1 (commit d69fe75)",
            "status": "post hoc, reported only; no checkpoint is selected, saved as a model or used further",
            "departures_from_plan": D1_DEPARTURES, "interpretations_of_plan": D1_INTERPRETATIONS,
            "additions_to_plan": D1_ADDITIONS,
            "inputs": {"checkpoint_dir": "<CKPT_DIR>", "train_log": rel(a.train_log), "valid": rel(os.path.join(a.dataset, "valid.xyz")),
                       "frames": {h: labels[h] for h in D1_HOSTS}},
            "checkpoint_loading": {
                "file": "torch.save({'model', 'optimizer', 'lr_scheduler'}) by mace-torch 0.3.16 CheckpointBuilder; read with "
                        "torch.load(weights_only=True)",
                "ema": "mace tools/train.py saves each checkpoint inside ema.average_parameters(), so 'model' holds the EMA "
                       "weights (decay 0.99) that its per-epoch eval used; no separate EMA state is stored",
                "into": "a deep copy of the wp3.model module (ScaleShiftMACE, float64) whose floating state_dict tensors are "
                        "first set to NaN, load_state_dict(strict=True) after asserting equal key sets, shapes and dtypes; "
                        "MACECalculator(models=[...], float64, cpu, head Default), whose module is then asserted to hold "
                        "every checkpoint tensor bitwise (a tensor the load missed would be NaN, not wp3.model's value)",
                "identity": "lr_scheduler.last_epoch equals the epoch of the file name (asserted)",
                "wp3_model": "run_train loads the epoch-82 checkpoint into the model and saves the module as wp3.model; the "
                             "epoch-82 state_dict is bitwise equal to wp3.model's: "
                             f"{recs[SELECTED]['state_dict_bitwise_equal_to_wp3_model']}"},
            "data_cross_check": xcheck,
            "checks": {"1_epoch82_vs_wp3_model": chk1, "2_logged_rmse": chk2, "zeroshot_vs_logged_initial_reported": initial,
                       "reproduction_wp3_eval_item5": repro},
            "dft": dft, "models": models, "Q1": q1, "Q2": q2, "Q3": q3,
            "n_single_points": {"zeroshot": zs.n_eval, "wp3_model": ft.n_eval,
                                "checkpoints": len(EPOCHS) * (len(labels["m21"]) + len(labels["m05"]))}}


# ---------------------------------------------------------------- D2
def argmax(E, labs):
    return max((2, 3, 4), key=lambda i: E[labs[i]] - E[labs[0]])


def path_work(F, P, cell, labs, istar):
    """Per-atom work (meV) of the force field F (label -> forces) along images 0 -> ... -> istar of {0, 2, 3, 4}
    (trapezoid rule; dr minimum-image in the band cell). P: image -> positions; labs: image -> label."""
    path = [i for i in (0, 2, 3, 4) if i <= istar]
    w = np.zeros(len(P[0]))
    for i, j in zip(path[:-1], path[1:]):
        dr = find_mic(P[j] - P[i], cell, pbc=True)[0]
        w += -0.5 * np.einsum("ij,ij->i", F[labs[i]] + F[labs[j]], dr)
    return w * 1000


def groups(at0, at6):
    """The five atom groups of the plan (index arrays), the hopping I and the group sizes."""
    sym, cell = np.array(at0.get_chemical_symbols()), at0.cell.array
    I = np.flatnonzero(sym == "I")
    disp = find_mic(at6.positions[I] - at0.positions[I], cell, pbc=True)[1]
    o = np.argsort(disp)[::-1]
    hop = int(I[o[0]])
    midp = at0.positions[hop] + 0.5 * find_mic(at6.positions[hop] - at0.positions[hop], cell, pbc=True)[0]
    d = find_mic(at0.positions - midp, cell, pbc=True)[1]
    org = np.isin(sym, list(ORGANIC))
    dmol, seen, mols = d.copy(), np.zeros(len(sym), int), {}
    for c in np.flatnonzero(sym == "C"):
        mol, _ = a38.molecule(at0, int(c), sym, cell)
        mols[int(c)] = mol; seen[mol] += 1; dmol[mol] = d[c]
    assert np.all(seen[org] == 1) and np.all(seen[~org] == 0), "molecules do not partition the C, N and H atoms"
    g = {"hop_I": np.array([hop]), "inorganic_near": np.flatnonzero(~org & (d < R_CUT) & (np.arange(len(sym)) != hop)),
         "inorganic_far": np.flatnonzero(~org & (d >= R_CUT)), "organic_near": np.flatnonzero(org & (dmol < R_CUT)),
         "organic_far": np.flatnonzero(org & (dmol >= R_CUT))}
    allidx = np.sort(np.concatenate(list(g.values())))
    assert np.array_equal(allidx, np.arange(len(sym))), "the five groups do not partition the atoms"
    nm = {k: sum(1 for c in mols if (d[c] < R_CUT) == (k == "organic_near")) for k in ("organic_near", "organic_far")}
    info = {"hop_I_index": hop, "hop_I_displacement_A": float(disp[o[0]]), "second_largest_I_displacement_A": float(disp[o[1]]),
            "n_atoms": {k: int(len(v)) for k, v in g.items()}, "n_molecules": nm,
            "n_GA_molecules": sum(1 for m in mols.values() if len(m) == 10)}
    return g, info


def attribution(w, g, total_direct, segment):
    """Group sums (meV), shares of the summed attribution, closures; the local share for Q4."""
    s = {k: float(w[v].sum()) for k, v in g.items()}
    tot = float(sum(s.values()))
    sh = {k: (x / tot if tot != 0 else None) for k, x in s.items()}
    loc = None if tot == 0 else sum(s[k] for k in LOCAL) / tot
    return {"groups_meV": s, "sum_meV": tot, "shares": sh, "local_share": loc,
            "far_or_organic_share": None if loc is None else 1 - loc,
            "side_above_half": None if loc is None else "local" if loc > 0.5 else "far_or_organic" if loc < 0.5 else "half",
            "direct_meV": total_direct, "segment_change_meV": segment,
            "closure_vs_direct_meV": tot - total_direct, "closure_vs_segment_meV": tot - segment}


NOT_A_READING = ("reported beside, not a Q4 reading and not to be cited as evidence for one: these bands include those whose "
                 "DFT closure exceeds 20 meV, which the plan reports as 'not resolved' in D2b and D2c")

# For the write-up (plan, Reporting: it lists every departure). No rule of the plan rests on an addition.
D1_DEPARTURES = []
D1_INTERPRETATIONS = [
    "Q2 'at which epoch ... first exceed 25 meV': the models are scanned in training order with Initial (the zero-shot "
    "start model) first, so a site already above 25 meV before any training is answered 'Initial', not kept epoch 0",
    "Q2 onsets are located only to a bracket (previous kept model, onset]: the epochs between kept checkpoints are not "
    "evaluated; the RMSE_F fall fraction is given at the onset and as a range over the logged epochs of the bracket",
    "Q1 'signs right' = scripts/39 sites() sign_agree of the far-referenced E_b (model sign = DFT sign); the first-shell Sr "
    "sites are the WP2c sites named Sr_hinge and Sr_flank"]
D1_ADDITIONS = [
    "Q1: the same condition on the two first-shell Sr sites alone (beside_first_shell_Sr_only) and a computed caveat when a "
    "site that is not first-shell Sr fails at every checkpoint (the plan rule then cannot discriminate)",
    "Q2: besides the literal |error| > 25 meV onset, the first model with error < -25 meV (the collapse direction), the "
    "first from which every later model stays above 25 meV, and the onsets for both sites together",
    "zero-shot vs the logged Initial record (reported, not gated); reproduction of wp3_eval.json item 5 (task rule, exit 6); "
    "dataset vs archived QE cross-check (exit 5); checkpoint identity and set checks (exit 3, 4); checkpoint loading into "
    "a NaN-prefilled copy with the calculator's module asserted to hold the checkpoint tensors (exit 4)"]
D2_DEPARTURES = [
    "Q4 with no resolved band is reported as 'cannot be read', not as the plan's literal 'mixed' (with n = 0 neither count "
    "can exceed n/2, so the literal 'otherwise' branch is vacuous); the literal result is kept beside as "
    "plan_literal_reading"]
D2_INTERPRETATIONS = [
    "resolved = |DFT closure| <= 20 meV; Q4 shares are of the summed attribution (the five groups add to 1)",
    "groups at image 0 and minimum image: distances to the hop midpoint r_I(0) + 1/2 mic(r_I(6) - r_I(0)); inorganic = not "
    "C, N or H; molecules by scripts/38 molecule(), assigned whole by the distance of their C"]
D2_ADDITIONS = [
    "a summary of D2b and D2c over all 37 bands (all_37_bands_beside): not a Q4 reading and not evidence for one; its share "
    "counts are named not_a_reading_share_counts and carry the attribution closure scale",
    "per-segment closures (0-2, 2-3, 3-4) beside D2a; the D2b closure also against the change of E(i*) - E(0) on the DFT "
    "segment; the D2c counts and per-split counts beside Q4",
    "reproduction of the 37 band E_a values of wp3_eval.json (task rule, exit 6); dataset vs archived QE cross-check (exit 5)"]


def q4_reading(rows):
    """The Q4 rule over the given (resolved) bands. With no band the plan's rule is vacuous: neither count can exceed
    n/2 = 0, so its literal 'otherwise' branch gives 'mixed'; the reading is then 'cannot be read' (a departure, listed),
    and the literal result is kept beside it."""
    n = len(rows)
    nl = sum(r["side_above_half"] == "local" for r in rows)
    nf = sum(r["side_above_half"] == "far_or_organic" for r in rows)
    lit = "mainly local" if nl > n / 2 else "mainly far or organic" if nf > n / 2 else "mixed"
    return {"n_resolved": n, "n_local_share_above_half": nl, "n_far_or_organic_share_above_half": nf,
            "reading": "cannot be read: no resolved band" if n == 0 else lit,
            "plan_literal_reading": f"{lit} (vacuous: 0 resolved bands)" if n == 0 else lit}


def part_summary(rr, reading=True):
    """Descriptive summary of D2b or D2c over a set of bands. With reading=False (the all-band block beside) the share
    counts carry no Q4 verdict and are named so."""
    q = q4_reading(rr)
    ck = "reading_counts" if reading else "not_a_reading_share_counts"
    counts = q if reading else {"n_bands": q["n_resolved"], "n_local_share_above_half": q["n_local_share_above_half"],
                                "n_far_or_organic_share_above_half": q["n_far_or_organic_share_above_half"]}
    if not rr:
        return {"n": 0, ck: counts}
    if not reading:
        nr = sum(r["status"] != "resolved" for r in rr)
        counts["n_not_resolved"] = nr
        counts["closure_vs_direct_rms_meV"] = rms(r["closure_vs_direct_meV"] for r in rr)
        counts["closure_vs_direct_max_abs_meV"] = max(abs(r["closure_vs_direct_meV"]) for r in rr)
        counts["mean_abs_direct_meV"] = float(np.mean([abs(r["direct_meV"]) for r in rr]))
        counts["note"] = (f"not a Q4 reading and not evidence for one: {nr} of these {len(rr)} bands are not resolved (the "
                          f"plan lets them enter no reading), and the summed attribution closes on the direct E_a change "
                          f"only to RMS {counts['closure_vs_direct_rms_meV']:.1f} meV (max |.| "
                          f"{counts['closure_vs_direct_max_abs_meV']:.1f}) against a mean |direct change| of "
                          f"{counts['mean_abs_direct_meV']:.1f} meV")
    tot = sum(r["sum_meV"] for r in rr)
    return {"n": len(rr),
            "mean_group_meV": {g: float(np.mean([r["groups_meV"][g] for r in rr])) for g in GROUPS},
            "mean_sum_meV": float(np.mean([r["sum_meV"] for r in rr])),
            "mean_direct_meV": float(np.mean([r["direct_meV"] for r in rr])),
            "share_of_band_summed_change": {g: sum(r["groups_meV"][g] for r in rr) / tot for g in GROUPS},
            "local_share_median": float(np.median([r["local_share"] for r in rr])),
            "max_abs_closure_vs_direct_meV": max(abs(r["closure_vs_direct_meV"]) for r in rr),
            "rms_closure_vs_direct_meV": rms(r["closure_vs_direct_meV"] for r in rr),
            "max_abs_closure_vs_segment_meV": max(abs(r["closure_vs_segment_meV"]) for r in rr),
            "rms_closure_vs_segment_meV": rms(r["closure_vs_segment_meV"] for r in rr),
            "n_sum_negative": sum(r["sum_meV"] < 0 for r in rr), "n_direct_negative": sum(r["direct_meV"] < 0 for r in rr),
            ck: counts}


def d2(a, data, M, ev_json):
    print("\n==== D2: attribution of the barrier change along the band path (reason 7)")
    B = bands37()
    labs = [l for h, s, _ in B for l in a39.band_labels(h, s)]
    xcheck = data.need(labs)
    print(f"  dataset vs archived QE and geometry, {fmt_check(xcheck)}  PASS")
    zs, ft = M.zeroshot(), M.finetuned()
    n0 = (zs.n_eval, ft.n_eval)
    run(zs, data, labs); run(ft, data, labs)
    print(f"  single points: zero-shot {zs.n_eval - n0[0]}, fine-tuned {ft.n_eval - n0[1]} (others reused in memory)")
    Ed = {b: a39.basis_energies(data.D, data.vac, b) for b in ("raw", "Eprime")}
    # reproduction of the E_a values in wp3_eval.json
    rows = []
    rep = ev_json["reported"]
    for h, s, sp in B:
        ref = rep["abs_Ea_16_test_bands"][f"{h}_{s}"] if sp == "test" else rep["item5"][h]["bands"][f"{h}_{s}"]
        compare(a39.band_errors((zs, ft), Ed, h, s), ref, f"{h}_{s}", rows)
    repro = summarise_compare(rows)
    print(f"  reproduction of the 37 band E_a values of wp3_eval.json: {repro['n_numeric']} numbers, max |diff| "
          f"{repro['max_abs_diff_meV']:.2e} meV  {'PASS' if repro['pass'] else 'FAIL'}")
    require(repro["pass"], EXIT_REPRO, f"reproduction failed: {repro['failures'][:10]}")

    EF = {l: data.D[l]["F"] for l in labs}
    FF = {l: data.D[l]["forces"] for l in labs}
    lev = {"dft": (EF, FF), "zeroshot": (zs.E, zs.F), "finetuned": (ft.E, ft.F)}
    out = {}
    for h, s, sp in B:
        L = dict(zip(a39.IMG, a39.band_labels(h, s)))
        ats = {i: data.geo.get(L[i]) for i in a39.IMG}
        cell = ats[0].cell.array
        assert all(np.allclose(ats[i].cell.array, cell, atol=1e-12) for i in a39.IMG), f"{h}_{s}: cell differs between images"
        assert all(ats[i].get_chemical_symbols() == ats[0].get_chemical_symbols() for i in a39.IMG), f"{h}_{s}: species differ"
        P = {i: ats[i].positions for i in a39.IMG}
        g, ginfo = groups(ats[0], ats[6])
        rec = {"split": sp, "groups": ginfo, "D2a": {}}
        istar = {}
        for name, (E, F) in lev.items():
            i = argmax(E, L); istar[name] = i
            w = path_work(F, P, cell, L, i)
            dE = (E[L[i]] - E[L[0]]) * 1000
            ea = a39.Ea(E, h, s)
            assert abs(ea - dE) < 1e-9, (h, s, name)
            sg = {}
            for x, y in ((0, 2), (2, 3), (3, 4)):
                wx = float(path_work(F, {0: P[x], 2: P[y]}, cell, {0: L[x], 2: L[y]}, 2).sum())
                sg[f"{x}-{y}"] = {"W_meV": wx, "dE_meV": (E[L[y]] - E[L[x]]) * 1000, "closure_meV": wx - (E[L[y]] - E[L[x]]) * 1000}
            rec["D2a"][name] = {"i_star": i, "Ea_meV": ea, "W_meV": float(w.sum()), "closure_meV": float(w.sum()) - dE,
                                "segments_beside": sg}
        cl = rec["D2a"]["dft"]["closure_meV"]
        rec["resolved"] = abs(cl) <= CLOSURE_BOUND
        rec["status"] = "resolved" if rec["resolved"] else "not resolved"
        i = istar["dft"]
        seg = lambda E: (E[L[i]] - E[L[0]]) * 1000
        w_ft, w_zs, w_d = (path_work(F, P, cell, L, i) for F in (ft.F, zs.F, FF))
        b = attribution(w_ft - w_zs, g, rec["D2a"]["finetuned"]["Ea_meV"] - rec["D2a"]["zeroshot"]["Ea_meV"], seg(ft.E) - seg(zs.E))
        c = attribution(w_ft - w_d, g, rec["D2a"]["finetuned"]["Ea_meV"] - rec["D2a"]["dft"]["Ea_meV"], seg(ft.E) - seg(EF))
        rec["D2b"] = {"status": rec["status"], "i_star_dft": i, "dF": "F_finetuned - F_zeroshot", **b}
        rec["D2c"] = {"status": rec["status"], "i_star_dft": i, "dF": "F_finetuned - F_DFT (raw F)", **c}
        out[f"{h}_{s}"] = rec

    res = [k for k, r in out.items() if r["resolved"]]
    bysplit = lambda sp: [k for k in res if out[k]["split"] == sp]
    summ = {"D2a": {}, "D2b": {}, "D2c": {}}
    for name in lev:
        cl = [out[k]["D2a"][name]["closure_meV"] for k in out]
        summ["D2a"][name] = {"max_abs_closure_meV": max(abs(x) for x in cl), "rms_closure_meV": rms(cl),
                             "n_abs_closure_above_20meV": sum(abs(x) > CLOSURE_BOUND for x in cl)}
    summ["D2a"]["n_bands"], summ["D2a"]["n_resolved"] = len(out), len(res)
    summ["D2a"]["not_resolved"] = {k: out[k]["D2a"]["dft"]["closure_meV"] for k in out if not out[k]["resolved"]}
    summ["D2a"]["argmax_differs_from_dft"] = {n: [k for k in out if out[k]["D2a"][n]["i_star"] != out[k]["D2a"]["dft"]["i_star"]]
                                              for n in ("zeroshot", "finetuned")}
    for part in ("D2b", "D2c"):
        summ[part] = {"resolved": part_summary([out[k][part] for k in res]),
                      "by_split": {sp: q4_reading([out[k][part] for k in bysplit(sp)]) for sp in ("train", "valid", "test")},
                      "all_37_bands_beside": {"note": NOT_A_READING, **part_summary([out[k][part] for k in out], reading=False)}}
        summ[part]["reading_counts"] = summ[part]["resolved"]["reading_counts"]
    q4 = {"question": "is the systematic E_a lowering carried mainly by the hopping I and its first shell, or by the far "
                      "field and the organic sublattice?",
          "rule": "D2b over the resolved bands: 'mainly local' if hop_I + inorganic_near carry > 1/2 of the summed change in "
                  "more than half the resolved bands; 'mainly far or organic' if inorganic_far + organic_near + organic_far "
                  "do; otherwise 'mixed'",
          **summ["D2b"]["reading_counts"], "D2c_beside": summ["D2c"]["reading_counts"],
          "dft_closure_range_meV": [min(out[k]["D2a"]["dft"]["closure_meV"] for k in out),
                                    max(out[k]["D2a"]["dft"]["closure_meV"] for k in out)],
          "dft_segment_closure_rms_meV_beside": {sk: rms(out[k]["D2a"]["dft"]["segments_beside"][sk]["closure_meV"] for k in out)
                                                 for sk in ("0-2", "2-3", "3-4")}}

    # ---- print
    print("\n  band          split  i*(D/Z/F)  closure DFT   ZS    FT  | D2b sum  hop_I  in<6  in>6  org<6 org>6 local | "
          "D2c sum  hop_I  in<6  in>6  org<6 org>6 local")
    for k, r in out.items():
        a_ = r["D2a"]
        row = (f"  {k:<13s} {r['split']:<5s}  {a_['dft']['i_star']}/{a_['zeroshot']['i_star']}/{a_['finetuned']['i_star']}     "
               f"{a_['dft']['closure_meV']:+6.1f} {a_['zeroshot']['closure_meV']:+6.1f} {a_['finetuned']['closure_meV']:+6.1f} |")
        for part in ("D2b", "D2c"):
            x = r[part]
            row += (f" {x['sum_meV']:+7.1f} " + " ".join(f"{x['groups_meV'][gname]:+6.1f}" for gname in GROUPS) +
                    f" {a39.num(x['local_share'], '+.2f')} |")
        print(row + ("" if r["resolved"] else "  NOT RESOLVED"))
    print(f"\n  D2a: {len(res)} of {len(out)} bands resolved (|DFT closure| <= 20 meV); max |closure| DFT "
          f"{summ['D2a']['dft']['max_abs_closure_meV']:.1f}, zero-shot {summ['D2a']['zeroshot']['max_abs_closure_meV']:.1f}, "
          f"fine-tuned {summ['D2a']['finetuned']['max_abs_closure_meV']:.1f} meV")
    for nm in lev:
        sg = {sk: [out[k]["D2a"][nm]["segments_beside"][sk]["closure_meV"] for k in out] for sk in ("0-2", "2-3", "3-4")}
        print(f"  D2a beside, per-segment closure RMS over 37 bands ({nm}): " +
              ", ".join(f"{sk} {rms(v):.1f} meV (max |.| {max(abs(x) for x in v):.1f})" for sk, v in sg.items()))
    for part in ("D2b", "D2c"):
        for tag, s_ in (("resolved", summ[part]["resolved"]), ("all 37, beside, NOT A READING", summ[part]["all_37_bands_beside"])):
            if not s_["n"]:
                print(f"  {part} [{tag}]: no band"); continue
            line = (f"  {part} [{tag}]: n {s_['n']}; mean per group (meV) " +
                    ", ".join(f"{gname} {v:+.1f}" for gname, v in s_["mean_group_meV"].items()) +
                    f"; mean sum {s_['mean_sum_meV']:+.1f}, mean direct {s_['mean_direct_meV']:+.1f}; share of the "
                    "band-summed change: " + ", ".join(f"{gname} {v:+.2f}" for gname, v in s_["share_of_band_summed_change"].items()) +
                    f"; closure vs direct RMS {s_['rms_closure_vs_direct_meV']:.1f} (max |.| "
                    f"{s_['max_abs_closure_vs_direct_meV']:.1f}), vs segment RMS {s_['rms_closure_vs_segment_meV']:.1f} meV")
            if "reading_counts" in s_:
                line += (f"; local share > 1/2 in {s_['reading_counts']['n_local_share_above_half']}, far or organic in "
                         f"{s_['reading_counts']['n_far_or_organic_share_above_half']}")
            print(line)
    print(f"  Q4: {q4['reading']} (local in {q4['n_local_share_above_half']}, far or organic in "
          f"{q4['n_far_or_organic_share_above_half']} of {q4['n_resolved']} resolved bands; the plan's literal rule: "
          f"{q4['plan_literal_reading']}); D2c beside: {q4['D2c_beside']['reading']}")
    return {"part": "D2", "plan": "WP3_DIAGNOSTICS_PLAN.md D2 (commit d69fe75)", "status": "post hoc, reported only",
            "definitions": {"work": "W(i*) = -sum_k 1/2 (F_k + F_k+1) . dr_k over images 0 -> ... -> i* of {0, 2, 3, 4}; dr_k "
                                    "minimum-image (ase find_mic, band cell); per atom, meV",
                            "closure": "W(i*) - [E(i*) - E(0)], i* each level's own argmax over images 2-4 (DFT: raw F)",
                            "resolved": "|DFT closure| <= 20 meV",
                            "D2b": "dF = F_finetuned - F_zeroshot on the DFT-argmax segment; closure vs the direct E_a change "
                                   "(own argmax each) and vs the change of E(i*) - E(0) on that segment",
                            "D2c": "dF = F_finetuned - F_DFT (raw F), same segment; direct = E_a(FT) - E_a(DFT raw)",
                            "groups": "image 0, minimum image, distances to the hop midpoint; hop_I = the I with the largest "
                                      "image-0 -> image-6 displacement; molecules by scripts/38 molecule(), assigned whole "
                                      "by their C; near = d < 6 A, far = d >= 6 A",
                            "shares": "group sum / sum over the five groups (they add to 1; a group can exceed 1 or be "
                                      "negative when groups carry opposite signs)",
                            "side_above_half": "per band, which side carries more than half the summed attribution "
                                               "(local = hop_I + inorganic_near); counted for Q4 only over resolved bands",
                            "segments_beside": "W and closure of the single segments 0-2, 2-3, 3-4 (reported, no rule)"},
            "departures_from_plan": D2_DEPARTURES, "interpretations_of_plan": D2_INTERPRETATIONS,
            "additions_to_plan": D2_ADDITIONS,
            "data_cross_check": xcheck, "reproduction_wp3_eval_Ea": repro, "bands": out, "summary": summ, "Q4": q4,
            "n_single_points_this_part": {"zeroshot": zs.n_eval - n0[0], "finetuned": ft.n_eval - n0[1]}}


def main(argv=None):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--model", default=os.path.join(DS, "wp3", "run2", "wp3.model"))
    common.add_argument("--model-sha256", default=MODEL_SHA256)
    common.add_argument("--dataset", default=os.path.join(DS, "wp3", "dataset"))
    common.add_argument("--eval-json", default=os.path.join(DS, "wp3", "wp3_eval.json"))
    common.add_argument("--train-log", default=os.path.join(DS, "wp3", "run2", "results", "wp3_run-123_train.txt"))
    common.add_argument("--dft", default=DS, help="root of the archived QE outputs (any depth)")
    common.add_argument("--v2", default=os.path.join(DS, "wp1_production"), help="wp2cde_selection.json, v2prod structures")
    common.add_argument("--structures", default=None)
    common.add_argument("--bands", default=os.path.join(os.path.dirname(ROOT), "bands"))
    common.add_argument("--out-dir", default=os.path.join(DS, "wp3", "diagnostics"))
    common.add_argument("--threads", type=int, default=4)
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="part", required=True)
    for p, h in (("d1", "D1 only"), ("d2", "D2 only"), ("all", "D1 then D2")):
        sp = sub.add_parser(p, parents=[common], help=h)
        if p != "d2":
            sp.add_argument("--checkpoints", required=True, help="directory of the kept run2 checkpoints (<CKPT_DIR>)")
    a = ap.parse_args(argv)
    a.model_sha256 = a.model_sha256.lower()
    if not os.path.isfile(a.model):
        ap.error(f"--model {a.model}: no such file")
    if getattr(a, "checkpoints", None) and not os.path.isdir(a.checkpoints):
        ap.error("--checkpoints: no such directory")
    log = os.path.join(a.out_dir, "diag_console.log")
    sys.stdout = Tee(log, getattr(a, "checkpoints", None))
    inputs = input_files(a)
    tracked = [rel(p) for p in inputs.values() if a39.inside(p, ROOT)]
    git = a39.git_state(["scripts/44_wp3_diagnostics.py", "scripts/39_wp3_evaluate.py", "scripts/38_wp2e_displacement.py",
                         "scripts/37_dft_eb_analysis.py", "scripts/32_dft_validation_analysis.py"] + tracked)
    script_sha = a39.sha256(os.path.abspath(__file__))
    print(f"\n######## scripts/44_wp3_diagnostics.py {a.part}  {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%S} UTC"
          f"\n  git head {git.get('head')}; uncommitted (scripts and inputs) {git.get('uncommitted')}; script sha256 "
          f"{script_sha}; threads {a.threads}")
    try:
        import mace, torch, ase
        miss = [rel(p) for p in inputs.values() if not os.path.exists(p)]
        require(not miss, EXIT_DATA, f"input files missing: {miss}")
        hashed = {k: {"file": rel(p), "sha256": a39.sha256(p) if os.path.isfile(p) else None,
                      **({} if os.path.isfile(p) else {"note": "a directory, not hashed"})} for k, p in inputs.items()}
        print("  inputs: " + "; ".join(f"{v['file']} {(v['sha256'] or 'not hashed')[:12]}" for v in hashed.values()))
        print(f"  models: zero-shot ~/.cache/mace/20231203mace128L1_epoch199model (sha256 {a39.FOUNDATION_SHA256[:12]}, "
              f"checked at load); fine-tuned {rel(a.model)} (sha256 {a.model_sha256[:12]}, checked at load)")
        ev_json = json.load(open(a.eval_json))
        data, M = Data(a), Models(a)
        head = {"script": "scripts/44_wp3_diagnostics.py", "script_sha256": script_sha, "git": git,
                "versions": {"mace": mace.__version__, "torch": torch.__version__, "ase": ase.__version__, "numpy": np.__version__},
                "threads": a.threads, "float64_cpu": "asserted for every arm before its first frame (scripts/39 Arm)",
                "model_files": {"zeroshot": {"call": 'mace_mp(model="medium", device="cpu", default_dtype="float64")',
                                             "file": "~/.cache/mace/20231203mace128L1_epoch199model", "sha256": a39.FOUNDATION_SHA256},
                                "finetuned": {"file": rel(a.model), "sha256": a.model_sha256, "head": "Default"}},
                "wp3_eval_json": {"file": rel(a.eval_json), "sha256": a39.sha256(a.eval_json)},
                "input_files": {**hashed, "note": "sha256 at the start of the run; the git status of every input inside the "
                                                  "repository is in 'git'. The archived QE outputs and the band geometries "
                                                  "(../bands) are not hashed: they are tied to the hashed dataset by the "
                                                  "fail-closed cross-check (data_cross_check)"}}
        os.makedirs(a.out_dir, exist_ok=True)
        for part, fn, name in ((d1, "d1_checkpoints.json", "d1"), (d2, "d2_path_attribution.json", "d2")):
            if a.part not in (name, "all"):
                continue
            r = part(a, data, M, ev_json)
            assert not set(head) & set(r), f"head and {name} result share keys {sorted(set(head) & set(r))}"
            f = os.path.join(a.out_dir, fn)
            a39.write_json({**head, **r}, f)
            print("written", rel(f))
    except Stop as e:
        print(f"STOP (exit {e.code}): {e}\n  nothing written for this part")
        sys.stdout.flush()
        return e.code
    except Exception as e:                      # a failed assertion or an unexpected error: fail-closed, logged
        print(f"ERROR (exit {EXIT_ERROR}): {type(e).__name__}: {e}\n  nothing written for this part")
        sys.stdout.flush()
        return EXIT_ERROR
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())

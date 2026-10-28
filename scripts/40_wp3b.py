#!/usr/bin/env python
"""WP3b: frozen-far-field relaxations of the six m30/m32 image-0 vacancy cells with the selected
model, judged by the DFT residual force on the free atoms (PLAN amendment m item 4, adoption (d)).

Committed before training (amendment m item 7, step 1) and run whenever a fine-tuned model exists
(step 7). WP3b outputs never enter a training set: wp3b_/wp3bu_ labels match no scripts/33 pattern
(item 1b). WP3b is not WP2e', which stays unscheduled.

  region    The free region, the same in the three cells of a host (item 4 'Free region'; amendment
            l item 4). Fixed points at image 0 of band_{undoped,GA,Sr}_<host>.extxyz: the vacancy
            site (scripts/29 ref_vacancy_position via build_pair, as scripts/38), the Sr atom of the
            Sr cell and the GA carbon of the GA cell. Free: every inorganic atom within 6.0 A
            (minimum image, start geometry) of any fixed point, and every organic molecule
            (scripts/38 molecule, by bonding) whose C is; molecules are free or fixed whole.
            Identity check: free inorganic atoms and free C are mapped to the nearest same-species
            atom of the undoped cell (Sr -> Pb); if the three mapped sets differ, their union is
            freed in all three cells. The WP2b frames give 81 / 83 / 81 free atoms (25 inorganic +
            7 molecules) in both hosts; the command exits non-zero if they do not. Item 4 does not
            define 'the free atoms within 1 A of the 6 A surface'; two labelled sets are written:
            'surface' (|d - 6| < 1 A in the distance the region is cut by, organic atoms at their
            molecule's C distance) and 'surface_own' (each atom's own distance). The region is
            identified by 'region_id', the sha256 of the content that fixes it (radius, band-file
            sha256, fixed points, free and surface lists), not of the file, which also holds paths.
  relax     Per cell, the model file (sha256 checked against --model-sha256) as a float64 CPU
            MACECalculator, head Default (refused otherwise); ASE FixAtoms on every non-free atom
            (item 4 'Constraint'); ASE FIRE with default parameters (as scripts/29), fmax 0.01 eV/A
            over the free atoms, at most 10 000 steps. Reading (recorded as protocol.reading): one
            FIRE run whose cap bounds the whole relaxation, because item 4 names one fmax and 'at
            most 10 000 steps'. m (Information state) ascribes these values to protocol v2.1, whose
            doped WP1 cells are relaxed in two restarted FIRE stages (0.02 then 0.01, <= 10 000 steps
            each); that staged scheme is not used. Fail checks (item 4 'Fail'): the step cap, i.e.
            FIRE stops at the cap without max per-atom |F| < 0.01 (ASE's strict test; converging on
            the last allowed step is not a fail); an I within 1.2 A of the vacancy site; the Sr atom
            or GA carbon moved >= 1.0 A (scripts/29); the scripts/35 organic topology check (sane()
            topology_ok). --unconstrained: the same relaxation with no FixAtoms and fmax over all
            atoms (labels wp3bu_; reported, not gating). Basin measures: 'basin_beyond_6A' =
            scripts/29 basin_dev vs image 0 over atoms > 6 A (own distance) from the three fixed
            points, the amendment-c item-1 measure item 4 asks of wp3bu_; 'basin_nonfree' = the same
            measures over exactly the non-free atoms (molecules by their C; zero by construction in
            wp3b_). Before any relaxation, the two model single points of the WP2e-minimum
            quantities (1) and (3) (image 0 of band_GA_m30 and the last frame of
            wp2e/relax_m30_GA_img0.out.gz) go to <work>/wp2e_minimum.json, so they exist whatever the
            relaxations give. Each relaxation writes the relaxed structure, the record, and the
            scripts/30 single point at the WP2b settings (scripts/30 defaults: scf, R point, q = 0,
            degauss 0.005, nspin 1; label wp3b_<host>_<system>_img0 or wp3bu_...).
            Interrupted jobs (item 4): outputs are written under temporary names and renamed when
            complete; the QE input is staged in <work>/<label>.qe and the record <label>.json is
            written next, so an attempt without a record is partial. Only then is the input copied to
            <qe>/<label>/ (under a .part name that no qe_queue.sh glob matches, then renamed), so the
            queue never sees the input of an incomplete attempt; a re-invocation completes the copy.
            A rerun needs --rerun-cause (spot-reclaim, node-loss, oom, wall-time), must be identical
            (sha256 of this script and of the numbered scripts it loads, model sha256, step cap,
            region_id), moves the partial outputs aside unread (<work>/discarded/) and is allowed at
            most twice per cell; every attempt is listed with its cause and time. A complete record
            made with anything else is refused, not skipped. A per-cell lock refuses a second
            process on the same cell. Each record carries the git state of these scripts.
  analyse   (d) from the six wp3b_ outputs (scripts/32 parse_qe: None = no JOB DONE, converged
            False = SCF not converged, a Fail): per-atom-norm residual RMS and max over the free
            atoms, as scripts/32 dft_frms_eVA / dft_fmax_eVA. pass = true iff all six cells have
            RMS < 0.05 and max < 0.2 eV/A and no Fail condition; false on any fail; null ('cannot be
            evaluated', a fail for the Outcomes and for scripts/39) otherwise. 'No complete output'
            (item 4) is read as: no QE output, no JOB DONE, a queue give-up, or one of these
            implementation checks failing (each fail-closed, none in item 4's text): no relaxation
            record, or a record of another label/constraint, region_id, model (--model-sha256) or
            step cap (a smoke test); no force block; the output geometry (1e-4 A) or the archived
            input beside it (1e-6 A, and the input text up to the pseudo_dir line, which run_qe.sh
            rewrites on the node) is not the relaxed structure's; a queue state qe_queue.sh cannot
            leave (a .gaveup beside an output, or a second resubmission); wp3b_ records made with
            different versions of the scripts. Reported, not gating, and only from usable records:
            whole-cell values; both surface sets; relaxation energies F(relaxed) - F(image 0) at
            model and DFT level (DFT image 0 = the WP2b single point) and their dopant - undoped
            difference per host; for wp3bu_ the whole-cell residual (criterion 5 as pre-registered),
            F(min) - F(image 0) and both basin measures, a missing wp3bu_ value reported as missing;
            the three WP2e-minimum quantities; the zero-shot comparator on the same atom sets; every
            relaxation rerun and QE resubmission with its cause and time; the code state of the
            records. Writes the result JSON read by scripts/39 (top-level 'pass', 'model_sha256';
            'cells' = the per-cell table, 'reasons').
  zeroshot  The zero-shot comparator of item 4 (not a decision rule): the free-atom residuals at the
            WP2b image-0 frames (DFT outputs only), the DFT F(WP2e minimum) - F(image 0) = -977.3 meV,
            and with zero-shot MACE-MP-0 (mace_mp medium, float64, cpu; 2 single points) the
            WP2e-minimum values +227.0 meV and 0.115 / 0.260 eV/A (component RMS 0.067). Exits
            non-zero unless every value is reproduced at the precision PLAN states.

From the repository root:
    python scripts/40_wp3b.py region --out <dir>/wp3b_region.json
    python scripts/40_wp3b.py zeroshot --region <dir>/wp3b_region.json --out <dir>/wp3b_zeroshot.json
    python scripts/40_wp3b.py relax --region <dir>/wp3b_region.json --model <run>/wp3.model \
        --model-sha256 <hex> --work <dir>/relax --qe /data/jobs/wp3b [--unconstrained] [--cells m30_GA ...]
    python scripts/40_wp3b.py analyse --region <dir>/wp3b_region.json --work <dir>/relax \
        --dft <dir with the wp3b_/wp3bu_ outputs> --model-sha256 <hex> --out <dir>/wp3b_result.json
"""
import argparse, fcntl, glob, hashlib, io, json, os, re, shutil, socket, subprocess, time, importlib.util
import numpy as np
from ase.io import read, write
from ase.geometry import find_mic

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
a29 = _load("a29", "29_dopant_shell_scan.py"); pp = a29.pp
a30 = _load("a30", "30_qe_singlepoint.py")
a32 = _load("a32", "32_dft_validation_analysis.py")
a35 = _load("a35", "35_finetune_frames.py")
a37 = _load("a37", "37_dft_eb_analysis.py")
a38 = _load("a38", "38_wp2e_displacement.py")
HELPERS = {"22": pp, "29": a29, "30": a30, "32": a32, "35": a35, "37": a37, "38": a38}

HOSTS, SYSTEMS = ("m30", "m32"), ("undoped", "GA", "Sr")
RADIUS, FMAX, STEPS = 6.0, 0.01, 10000           # amendment l item 4; m item 4 'Relaxation'
GAP_MIN, DOPANT_MAX = 1.2, 1.0                    # scripts/29 vacancy and dopant checks
RMS_MAX, MAX_MAX = 0.05, 0.2                      # criterion 5 thresholds, applied to the free atoms
BASIN_DR, BASIN_ROT = 0.25, 20.0                  # amendment c item 1 bounds (reported only)
EXPECTED = {"undoped": (81, 25, 7), "GA": (83, 25, 7), "Sr": (81, 25, 7)}   # free, inorganic, molecules
ZERO_SHOT = {("m30", "undoped"): (0.153, 0.332), ("m30", "GA"): (0.142, 0.270), ("m30", "Sr"): (0.160, 0.337),
             ("m32", "undoped"): (0.157, 0.360), ("m32", "GA"): (0.148, 0.365), ("m32", "Sr"): (0.160, 0.374)}
ZERO_SHOT_WP2E = {"dE_dftmin_minus_img0_meV": (227.0, 1), "frms_eVA": (0.115, 3), "fmax_eVA": (0.260, 3),
                  "component_rms_eVA": (0.067, 3)}   # value, decimals stated in item 4
DFT_WP2E_MEV = -977.3                              # F(WP2e minimum) - F(image 0), item 4 / WP2E_RESULT.md
FOUNDATION_SHA256 = "01bfe22100139f424713cf921144e5509cbe353d67aa9fa1be9c6e1e0ed35845"   # m item 2
RERUN_CAUSES = ("spot-reclaim", "node-loss", "oom", "wall-time")
MAX_ATTEMPTS = 3                                   # the first run and at most two reruns
WP2B_RAW = "results/objective2/dopant_shell/wp2b/raw"
WP2E_RELAX = "results/objective2/dopant_shell/wp2e/relax_m30_GA_img0.out.gz"
WP2E_FILE = "wp2e_minimum.json"
PROTOCOL_READING = ("one FIRE run to fmax 0.01 eV/A, the 10 000-step cap bounding the whole relaxation: item 4 names "
                    "one fmax and 'at most 10 000 steps'. m (Information state) ascribes these values to protocol v2.1, "
                    "whose doped WP1 cells are relaxed in two restarted FIRE stages (0.02 then 0.01, <= 10 000 steps "
                    "each); that staged scheme is not used here (an interpretation of item 4, to be stated in the WP3 result)")
STEP_CAP_RULE = ("fail if FIRE stops at the cap without max per-atom |F| < 0.01 eV/A over the gated atoms (ASE's strict "
                 "test); converging on the last allowed step is not a fail")
SCOPE_WP3BU = ("item 4 Scope: a WP3b pass is not criterion 5; an S2 protocol that relaxes whole cells needs criterion 5 on "
               "all atoms of a fine-tuned full-cell minimum, pre-registered for that protocol. The wp3bu_ values of WP3b "
               "do not meet this requirement")


def label(h, s, unconstrained=False):
    return f"wp3b{'u' if unconstrained else ''}_{h}_{s}_img0"


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def input_norm_sha256(path):
    """sha256 of a pw.x input (.gz read transparently) without its pseudo_dir line and with blank runs collapsed:
    run_qe.sh rewrites pseudo_dir in place on the node (every archived wp2b-wp2e input shows it), so raw bytes differ."""
    keep = [re.sub(r"\s+", " ", ln.strip()) for ln in a32.read_text(path).splitlines()
            if not re.match(r"\s*pseudo_dir\s*=", ln)]
    return hashlib.sha256("\n".join(x for x in keep if x).encode()).hexdigest()


def git(*args):
    """stdout (bytes) of git in the repository root, or None (as scripts/41)."""
    try:
        p = subprocess.run(["git", "-C", ROOT, *args], capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return p.stdout if p.returncode == 0 else None


def code_state():
    """sha256 of this script and of the numbered scripts it loads, and their git state (as scripts/39 git_state)."""
    files = {"40": os.path.abspath(__file__), **{k: os.path.abspath(m.__file__) for k, m in HELPERS.items()}}
    rel = [os.path.relpath(f, ROOT) for f in files.values()]
    head, st, blob = git("rev-parse", "HEAD"), git("status", "--porcelain", "--", *rel), git("show", f"HEAD:./{rel[0]}")
    sha = {k: sha256_file(f) for k, f in files.items()}
    return {"script_sha256": sha.pop("40"), "helpers_sha256": sha,
            "git": None if head is None or st is None else
            {"head": head.decode().strip(), "uncommitted": st.decode().splitlines(),
             "script_equals_head": blob is not None and hashlib.sha256(blob).hexdigest() == sha256_file(files["40"])}}


def dist(at, p):
    """Minimum-image distance of every atom of at to the point p (ase find_mic, as scripts/29)."""
    return find_mic(at.positions - p, at.cell.array, pbc=True)[1]


def norms(F, idx=None):
    """RMS and max of the per-atom force norm (scripts/32 dft_frms_eVA / dft_fmax_eVA) over idx."""
    n = np.linalg.norm(F, axis=1)
    n = n if idx is None else n[np.asarray(idx, int)]
    return {"rms_eVA": float(np.sqrt(np.mean(n ** 2))), "max_eVA": float(n.max()), "n": int(n.size)}


def band_path(bands, h, s):
    return os.path.join(bands, f"band_{s}_{h}.extxyz")


def start_cell(bands, h, s):
    at = read(band_path(bands, h, s), index=0)
    at.calc = None
    return at


def dopant_index(at, system, vpos):
    """The Sr atom, or the GA carbon (the C with 3 N within 1.6 A); position as scripts/38 centres."""
    s = np.array(at.get_chemical_symbols())
    if system == "Sr":
        hits = list(np.flatnonzero(s == "Sr"))
    else:
        N = np.flatnonzero(s == "N")
        hits = [c for c in np.flatnonzero(s == "C") if (dist(at, at.positions[c])[N] < 1.6).sum() == 3]
    assert len(hits) == 1, f"{system}: {len(hits)} dopant atoms"
    assert np.allclose(at.positions[hits[0]], a38.centres(at, system, vpos)["dopant"])
    return int(hits[0])


def region_id(reg):
    """sha256 of the content that fixes the free region; paths and diagnostics are left out, so a region rebuilt
    identically elsewhere (another checkout, a symlink, the node) has the same identity."""
    core = {"radius_A": reg["radius_A"], "band_sha256": reg["band_sha256"],
            "hosts": {h: {"vacancy": [round(x, 6) for x in r["fixed_points"]["vacancy"]], "sr_index": r["sr_index"],
                          "ga_carbon_index": r["ga_carbon_index"],
                          "cells": {s: {k: c[k] for k in ("natoms", "free", "surface", "surface_own")}
                                    for s, c in r["cells"].items()}}
                      for h, r in reg["hosts"].items()}}
    return hashlib.sha256(json.dumps(core, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_region(path, bands):
    reg = json.load(open(path))
    if abs(reg["radius_A"] - RADIUS) > 1e-12 or not reg.get("matches_plan"):
        raise SystemExit(f"{path}: radius {reg['radius_A']} A, matches_plan {reg.get('matches_plan')}; "
                         f"WP3b uses the PLAN free region ({RADIUS} A, 81/83/81)")
    try:
        rid = region_id(reg)
    except KeyError as e:
        raise SystemExit(f"{path}: no {e} (written by an earlier scripts/40); rebuild it with 'region'")
    if reg.get("region_id") != rid:
        raise SystemExit(f"{path}: region_id {reg.get('region_id')} != recomputed {rid} (file edited?)")
    for k, v in reg["band_sha256"].items():
        h, s = k.split("_")
        if sha256_file(band_path(bands, h, s)) != v:
            raise SystemExit(f"{path}: {band_path(bands, h, s)} changed since the region was built")
    return reg, rid


# ---------------------------------------------------------------- region
def build_region(h, cells, vpos, radius):
    isr, iga = dopant_index(cells["Sr"], "Sr", vpos), dopant_index(cells["GA"], "GA", vpos)
    pts = {"vacancy": np.asarray(vpos, float), "Sr": cells["Sr"].positions[isr].copy(),
           "GA_C": cells["GA"].positions[iga].copy()}
    U = cells["undoped"]; usym = np.array(U.get_chemical_symbols())

    def to_undoped(at, i):          # nearest same-species atom of the undoped cell (Sr -> Pb)
        sp = at.get_chemical_symbols()[i]; sp = "Pb" if sp == "Sr" else sp
        cand = np.flatnonzero(usym == sp); d = dist(U, at.positions[i])[cand]
        return (sp, int(cand[np.argmin(d)])), float(d.min())

    per, mapped = {}, {}
    for s, at in cells.items():
        sym = np.array(at.get_chemical_symbols())
        d = np.min([dist(at, p) for p in pts.values()], axis=0)
        org = np.isin(sym, ["C", "N", "H"])
        mols = {int(c): a38.molecule(at, int(c), sym, at.cell.array)[0] for c in np.flatnonzero(sym == "C")}
        assert sorted(i for m in mols.values() for i in m) == [int(i) for i in np.flatnonzero(org)], \
            f"{h} {s}: organic atoms not assigned to exactly one molecule"
        dmol = d.copy()                                # organic atoms take their molecule's C distance
        for c, m in mols.items():
            dmol[m] = d[c]
        inorg = [int(i) for i in np.flatnonzero(~org & (d < radius))]
        cs = [c for c in mols if d[c] < radius]
        mp = [to_undoped(at, i) for i in inorg + cs]
        mapped[s] = {k for k, _ in mp}
        per[s] = {"at": at, "sym": sym, "mols": mols, "d": d, "dmol": dmol, "inorg": inorg, "cs": cs,
                  "map_max_A": max(x for _, x in mp)}
    identical = mapped["undoped"] == mapped["GA"] == mapped["Sr"]
    union = sorted(set().union(*mapped.values()))
    out = {}
    for s, p in per.items():
        at, inorg, cs = p["at"], p["inorg"], p["cs"]
        if not identical:           # free the union in all three cells: map each undoped atom back
            inorg, cs = set(inorg), set(cs)
            for sp, j in union:
                ok = np.flatnonzero(np.isin(p["sym"], ["Pb", "Sr"] if sp == "Pb" else [sp]))
                k = int(ok[np.argmin(dist(at, U.positions[j])[ok])])
                assert to_undoped(at, k)[0] == (sp, j), f"{h} {s}: identity map not one-to-one at {sp}{j}"
                (cs if sp == "C" else inorg).add(k)
            inorg, cs = sorted(inorg), sorted(cs)
        free = sorted(inorg + [i for c in cs for i in p["mols"][c]])
        surf = [i for i in free if abs(p["dmol"][i] - radius) < 1.0]     # within 1 A of the surface (cut distance)
        surf_own = [i for i in free if abs(p["d"][i] - radius) < 1.0]    # the same in each atom's own distance
        isym = p["sym"][inorg]
        ext = lambda f, v: round(float(f(v)), 4) if len(v) else None
        out_inorg = np.flatnonzero(~np.isin(p["sym"], ["C", "N", "H"]) & ~np.isin(np.arange(len(at)), inorg))
        out[s] = {"natoms": len(at), "n_free": len(free), "n_inorganic": len(inorg), "n_molecules": len(cs),
                  "inorganic_species": {str(e): int((isym == e).sum()) for e in sorted(set(isym))},
                  "molecule_carbons": cs, "free": free, "surface": surf, "n_surface": len(surf),
                  "surface_own": surf_own, "n_surface_own": len(surf_own),
                  "identity_map_max_A": round(p["map_max_A"], 6),
                  "margin_A": {"inorganic_inside_max": ext(max, p["d"][inorg]), "inorganic_outside_min": ext(min, p["d"][out_inorg]),
                               "C_inside_max": ext(max, p["d"][cs]),
                               "C_outside_min": ext(min, p["d"][[c for c in p["mols"] if c not in cs]])},
                  "d_assigned_A": [round(float(x), 4) for x in p["dmol"]]}
    dvac = lambda k: float(find_mic(np.atleast_2d(pts[k] - pts["vacancy"]), U.cell.array, pbc=True)[1][0])
    return {"fixed_points": {k: [float(x) for x in v] for k, v in pts.items()},
            "sr_index": isr, "ga_carbon_index": iga,
            "fixed_point_distances_A": {"vacancy-Sr": dvac("Sr"), "vacancy-GA_C": dvac("GA_C")},
            "mapped_identical": bool(identical), "union_applied": not identical,
            "mapped_undoped_atoms": [list(x) for x in union], "cells": out}


def cmd_region(a):
    ref = a29.ref_vacancy_position(a.pool, a.vac_ref)
    res = {"plan": "amendment m item 4 (WP3b free region; amendment l item 4)", "radius_A": a.radius,
           "bands": os.path.abspath(a.bands), "pool": os.path.abspath(a.pool), "vac_ref": os.path.abspath(a.vac_ref),
           "band_sha256": {f"{h}_{s}": sha256_file(band_path(a.bands, h, s)) for h in HOSTS for s in SYSTEMS},
           "surface_definition": {
               "surface": "free atoms with |d - radius| < 1 A, d = distance to the nearest fixed point, organic atoms "
                          "at their molecule's C distance (the distance the region is cut by)",
               "surface_own": "free atoms with |d - radius| < 1 A in each atom's own distance",
               "about": "item 4 does not define 'the free atoms within 1 A of the 6 A surface'; both are reported"},
           "hosts": {}}
    good = abs(a.radius - RADIUS) < 1e-12
    for h in HOSTS:
        _, vpos, _ = pp.build_pair(read(os.path.join(a.pool, f"{h}.extxyz")), ref, None, None)
        cells = {s: start_cell(a.bands, h, s) for s in SYSTEMS}
        r = build_region(h, cells, vpos, a.radius)
        res["hosts"][h] = r
        good &= r["mapped_identical"]
        for s in SYSTEMS:
            c = r["cells"][s]
            got = (c["n_free"], c["n_inorganic"], c["n_molecules"])
            good &= got == EXPECTED[s]
            print(f"{h} {s:<8} free {got[0]:3d} (inorganic {got[1]} {c['inorganic_species']}, molecules {got[2]})"
                  f"  surface {c['n_surface']} (own distance {c['n_surface_own']})  identity-map max "
                  f"{c['identity_map_max_A']:.3f} A  margins {c['margin_A']}")
        print(f"{h}: mapped sets identical: {r['mapped_identical']}; d(vac-Sr) {r['fixed_point_distances_A']['vacancy-Sr']:.3f}"
              f" A, d(vac-GA C) {r['fixed_point_distances_A']['vacancy-GA_C']:.3f} A")
    res["matches_plan"] = bool(good)
    res["region_id"] = region_id(res)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    a29.dump_atomic(res, a.out)
    print(f"-> {a.out}; region_id {res['region_id']}; matches PLAN (6.0 A, 81/83/81, 25 inorganic + 7 molecules, "
          f"identical sets): {good}")
    if not good:
        raise SystemExit(1)


# ---------------------------------------------------------------- model and WP2e minimum
def load_model(path, sha, threads):
    got = sha256_file(path)
    if got != sha.lower():
        raise SystemExit(f"{path}: sha256 {got} != --model-sha256 {sha}")
    import torch, ase, mace
    torch.set_num_threads(threads)
    from mace.calculators import MACECalculator
    calc = MACECalculator(model_paths=[path], device="cpu", default_dtype="float64", head="Default")
    if calc.head != "Default":           # 0.3.16 falls back to the last head with only a warning (scripts/29)
        raise SystemExit(f"{path}: no head 'Default' (heads {calc.available_heads})")
    assert all(p.dtype == torch.float64 for m in calc.models for p in m.parameters()), "model is not float64"
    info = {"path": os.path.abspath(path), "sha256": got, "zero_shot_foundation": got == FOUNDATION_SHA256,
            "calculator": "MACECalculator(device='cpu', default_dtype='float64', head='Default')", "head": calc.head,
            "mace_version": mace.__version__, "torch_version": torch.__version__, "ase_version": ase.__version__,
            "threads": threads}
    return calc, info


def model_point(calc, at):
    x = at.copy(); x.set_constraint(); x.calc = calc
    return float(x.get_potential_energy()), x.get_forces().copy()


def wp2e_minimum(path, img0):
    """Last frame of the WP2e DFT relaxation of m30 GA image 0 (fixed cell; the cell of image 0 is
    used once the printed cell agrees with it)."""
    tr = read(io.StringIO(a32.read_text(path)), index=-1, format="espresso-out")
    assert tr.get_chemical_symbols() == img0.get_chemical_symbols(), "WP2e minimum: species differ from image 0"
    assert np.abs(tr.cell.array - img0.cell.array).max() < 1e-4, "WP2e minimum: cell differs from image 0"
    x = img0.copy(); x.calc = None; x.positions = tr.positions
    return x


def wp2e_values(E_img0, E_min, F_min):
    """Item 4 'Reported, not gating', WP2e minimum: (1) and (3); (2) needs the wp3bu_ final energy."""
    w = norms(F_min)
    return {"E_model_dftmin_eV": E_min, "dE_dftmin_minus_img0_meV": (E_min - E_img0) * 1000,
            "frms_eVA": w["rms_eVA"], "fmax_eVA": w["max_eVA"],
            "component_rms_eVA": float(np.sqrt(np.mean(F_min ** 2)))}


def write_wp2e(a, calc, model, path):
    """WP2e-minimum quantities (1) and (3): two single points of the selected model at fixed geometries, written
    before any relaxation so that they do not depend on one."""
    img0 = start_cell(a.bands, "m30", "GA")
    E0, _ = model_point(calc, img0)
    Em, Fm = model_point(calc, wp2e_minimum(a.wp2e, img0))
    rec = {"item": "m item 4 'Reported, not gating', WP2e minimum (1) and (3), selected model in float64",
           "source": os.path.abspath(a.wp2e), "source_sha256": sha256_file(a.wp2e),
           "image0": os.path.abspath(band_path(a.bands, "m30", "GA")) + "@0", "model": model,
           "E_model_img0_eV": E0, **wp2e_values(E0, Em, Fm), **code_state(), "written": now()}
    a29.dump_atomic(rec, path)
    print(f"WP2e minimum: dE {rec['dE_dftmin_minus_img0_meV']:+.1f} meV, force {rec['frms_eVA']:.3f} / "
          f"{rec['fmax_eVA']:.3f} eV/A (component RMS {rec['component_rms_eVA']:.3f}) -> {path}", flush=True)


# ---------------------------------------------------------------- relax
def out_paths(work, qe, lab):
    return {"record": os.path.join(work, f"{lab}.json"), "attempts": os.path.join(work, f"{lab}.attempts.json"),
            "structure": os.path.join(work, f"{lab}.extxyz"), "log": os.path.join(work, f"{lab}.fire.log"),
            "stage": os.path.join(work, f"{lab}.qe"),       # QE input staged here, outside every queue glob
            "lock": os.path.join(work, f"{lab}.lock"), "qe": os.path.join(qe, lab) if qe else None}


def partial_outputs(P):
    return [p for k in ("structure", "log", "stage") for p in (P[k], P[k] + ".tmp", P[k] + ".partial")
            if os.path.exists(p)]


def rec_ident(rec):
    return {"script_sha256": rec.get("script_sha256"), "helpers_sha256": rec.get("helpers_sha256"),
            "model_sha256": rec.get("model", {}).get("sha256"), "steps_cap": rec.get("protocol", {}).get("steps_cap"),
            "region_id": rec.get("region_id")}


def publish_qe(P, lab, rec):
    """Copy the staged QE input into <qe>/<label>/ once the record exists: meta first, the .in last, each under a
    .part name (matched by no qe_queue.sh glob) and renamed. Idempotent; an input already there must be the recorded one."""
    os.makedirs(P["qe"], exist_ok=True)
    for fn in (f"{lab}.meta.json", f"{lab}.in"):
        dst, src = os.path.join(P["qe"], fn), os.path.join(P["stage"], fn)
        if not os.path.exists(dst):
            if not os.path.exists(src):
                raise SystemExit(f"{lab}: neither {dst} nor the staged {src} exists")
            shutil.copyfile(src, dst + ".part"); os.replace(dst + ".part", dst)
    q = os.path.join(P["qe"], f"{lab}.in")
    if input_norm_sha256(q) != rec["files"]["qe_input_norm_sha256"]:
        raise SystemExit(f"{lab}: {q} is not the input of the record {P['record']}")


def relax_cell(a, calc, model, reg, rid, h, s, P, attempts, code):
    from ase.constraints import FixAtoms
    from ase.optimize import FIRE
    from ase.calculators.singlepoint import SinglePointCalculator
    lab = label(h, s, a.unconstrained)
    R = reg["hosts"][h]; free = np.array(R["cells"][s]["free"], int)
    vpos = np.array(R["fixed_points"]["vacancy"]); centres = [np.array(v) for v in R["fixed_points"].values()]
    start = start_cell(a.bands, h, s); n = len(start); cell = start.cell.array
    assert n == R["cells"][s]["natoms"], f"{lab}: {n} atoms, region has {R['cells'][s]['natoms']}"
    fixed = np.setdiff1d(np.arange(n), free)
    at = start.copy()
    if not a.unconstrained:
        at.set_constraint(FixAtoms(indices=fixed))
    at.calc = calc
    t0 = time.time()
    E0 = float(at.get_potential_energy()); F0 = at.get_forces(apply_constraint=False).copy()
    with FIRE(at, logfile=P["log"] + ".partial") as opt:  # default parameters, as scripts/29
        converged = bool(opt.run(fmax=FMAX, steps=a.steps))
        nsteps = int(opt.get_number_of_steps())
    E1 = float(at.get_potential_energy()); F1 = at.get_forces(apply_constraint=False).copy()
    gate = np.arange(n) if a.unconstrained else free
    fmax = float(np.linalg.norm(F1[gate], axis=1).max())
    assert abs(fmax - float(np.linalg.norm(at.get_forces(), axis=1).max())) < 1e-12, "FIRE criterion != gated atoms"
    assert converged == (fmax < FMAX) and (converged or nsteps == a.steps), (converged, fmax, nsteps)
    held = float(np.abs(at.positions[fixed] - start.positions[fixed]).max()) if fixed.size else 0.0
    if not a.unconstrained:
        assert held == 0.0, f"{lab}: a fixed atom moved by {held} A"
    dr = find_mic(at.positions - start.positions, cell, pbc=True)[1]
    sym = np.array(at.get_chemical_symbols())
    gap = float(dist(at, vpos)[sym == "I"].min())
    disp = float(dr[R["sr_index" if s == "Sr" else "ga_carbon_index"]]) if s != "undoped" else None
    snap = at.copy(); snap.set_constraint()
    snap.calc = SinglePointCalculator(snap, energy=E1, forces=F1)
    _, chk = a35.sane(snap, start, s, snap.calc, 1e9)       # organic topology (scripts/35); force bound not used
    basin = a29.basin_dev(start, snap, range(n), centres, cell, RADIUS)      # own distance (amendment c item 1)
    # the same measures over exactly the non-free atoms (rcut -1 keeps every atom passed; molecules whole by C)
    bnf = a29.basin_dev(start, snap[fixed], fixed, [vpos], cell, -1.0) if fixed.size else None
    fails = []
    if not converged:
        fails.append(f"step cap: fmax {fmax:.4f} eV/A after {nsteps} steps")
    if gap <= GAP_MIN:
        fails.append(f"an I lies {gap:.3f} A from the vacancy site")
    if disp is not None and disp >= DOPANT_MAX:
        fails.append(f"{'Sr atom' if s == 'Sr' else 'GA carbon'} moved {disp:.3f} A")
    if not chk["topology_ok"]:
        fails.append("scripts/35 organic topology check failed")
    within = lambda b: None if b is None else bool(b["max_dr_A"] < BASIN_DR and b["max_fa_rot_deg"] < BASIN_ROT)
    rec = {"label": lab, "host": h, "system": s, "constrained": not a.unconstrained,
           "protocol": {"optimizer": "ASE FIRE, default parameters (as scripts/29)", "fmax_eVA": FMAX,
                        "fmax_over": "all atoms" if a.unconstrained else "free atoms", "steps_cap": a.steps,
                        "plan_protocol": a.steps == STEPS, "cell": "fixed", "reading": PROTOCOL_READING,
                        "step_cap_rule": STEP_CAP_RULE,
                        "constraint": None if a.unconstrained else "ASE FixAtoms on every non-free atom"},
           "model": model, "region_id": rid, "region_file_sha256": sha256_file(a.region), **code,
           "n_free": int(free.size), "n_fixed": 0 if a.unconstrained else int(fixed.size),
           "E_img0_eV": E0, "E_relaxed_eV": E1, "dE_relax_model_meV": (E1 - E0) * 1000,
           "img0_force_free": norms(F0, free), "img0_force_all": norms(F0),
           "steps": nsteps, "fmax_eVA": fmax, "converged": converged,
           "final_force_free": norms(F1, free), "final_force_all": norms(F1),
           "max_dr_free_A": float(dr[free].max()), "max_dr_all_A": float(dr.max()),
           "max_dr_nonfree_A": float(dr[fixed].max()) if fixed.size else 0.0,
           "nearest_I_to_vacancy_site_A": gap, "dopant_displacement_A": disp, "topology": chk,
           "basin_beyond_6A": {**basin, "within_amendment_c_bounds": within(basin),
                               "about": "amendment c item 1 measure: scripts/29 basin_dev vs image 0 over atoms > 6 A "
                                        "(own distance) from all three fixed points"},
           "basin_nonfree": None if bnf is None else
                            {**bnf, "within_amendment_c_bounds": within(bnf),
                             "about": "the same measures over exactly the non-free atoms (molecules assigned by their C)"},
           "fail_reasons": fails}
    # outputs: temporary names first, renamed when complete; the record after the staged input; the queue copy last
    snap.info.update({"label": lab, "model_sha256": model["sha256"]})
    write(P["structure"] + ".tmp", snap, format="extxyz"); os.replace(P["structure"] + ".tmp", P["structure"])
    x = snap.copy(); x.calc = None; x.set_tags([0] * n)
    stmp = P["stage"] + ".tmp"
    shutil.rmtree(stmp, ignore_errors=True)
    path = a30.write_input(x, lab, stmp)          # scripts/30 defaults = the WP2b settings
    meta = {"label": lab, "source": os.path.abspath(P["structure"]), "natoms": n, "formula": x.get_chemical_formula(),
            "fingerprint": {**a30.FINGERPRINT, "calculation": "scf", "tot_charge": 0},
            "input_sha256": sha256_file(path), "input_norm_sha256": input_norm_sha256(path), "model_sha256": model["sha256"]}
    json.dump(meta, open(os.path.join(stmp, f"{lab}.meta.json"), "w"), indent=1)
    os.replace(stmp, P["stage"])
    os.replace(P["log"] + ".partial", P["log"])
    attempts[-1]["finished"] = now()
    a29.dump_atomic(attempts, P["attempts"])
    rec.update({"attempts": attempts, "wall_s": round(time.time() - t0, 1),
                "files": {"structure": os.path.abspath(P["structure"]),
                          "qe_stage": os.path.abspath(os.path.join(P["stage"], f"{lab}.in")),
                          "qe_input": os.path.abspath(os.path.join(P["qe"], f"{lab}.in")),
                          "qe_input_sha256": meta["input_sha256"], "qe_input_norm_sha256": meta["input_norm_sha256"]}})
    a29.dump_atomic(rec, P["record"])
    publish_qe(P, lab, rec)
    print(f"{lab}: {nsteps} steps, fmax {fmax:.4f} eV/A, dE_model {rec['dE_relax_model_meV']:+.1f} meV, "
          f"gap {gap:.2f} A, dopant {disp if disp is None else round(disp, 3)} A, topology {chk['topology_ok']}, "
          f"fails {fails or 'none'}, {rec['wall_s']:.0f} s", flush=True)


def cmd_relax(a):
    reg, rid = load_region(a.region, a.bands)
    cells = [tuple(c.split("_")) for c in dict.fromkeys(a.cells)]
    for c in cells:
        if len(c) != 2 or c[0] not in HOSTS or c[1] not in SYSTEMS:
            raise SystemExit(f"--cells: '{'_'.join(c)}' is not one of {[f'{h}_{s}' for h in HOSTS for s in SYSTEMS]}")
    if os.path.abspath(a.work) == os.path.abspath(a.qe):  # the staged <work>/<label>.qe/<label>.in would match $D/*/*.in
        raise SystemExit("--work must not be the --qe (queue campaign) directory")
    os.makedirs(a.work, exist_ok=True); os.makedirs(a.qe, exist_ok=True)
    code = code_state()
    ident = {"script_sha256": code["script_sha256"], "helpers_sha256": code["helpers_sha256"],
             "model_sha256": a.model_sha256.lower(), "steps_cap": a.steps, "region_id": rid}   # identical rerun (item 4)
    if code["git"] is None or code["git"]["uncommitted"] or not code["git"]["script_equals_head"]:
        print(f"WARNING: scripts/40 or its helpers are not committed here (git: {code['git']}); item 2 and item 7 "
              "require the committed script before any test-host prediction", flush=True)
    wfile = os.path.join(a.work, WP2E_FILE)
    todo, done, refuse, locks = [], [], [], []
    if os.path.exists(wfile) and json.load(open(wfile))["model"]["sha256"] != ident["model_sha256"]:
        refuse.append(f"{wfile} is of another model; use another --work")
    for h, s in cells:                            # decide every cell before any model is loaded
        lab = label(h, s, a.unconstrained); P = out_paths(a.work, a.qe, lab)
        lk = open(P["lock"], "a")
        try:
            fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB); locks.append(lk)
        except BlockingIOError:
            refuse.append(f"{lab}: another process holds {P['lock']}"); continue
        if os.path.exists(P["record"]):           # complete: only with the identical script, model, cap and region
            rec = json.load(open(P["record"])); ri = rec_ident(rec)
            diff = sorted(k for k in ident if ri[k] != ident[k])
            if diff:
                refuse.append(f"{lab}: a complete record made with another {diff} exists ({P['record']}); it is not "
                              f"redone or overwritten: use another --work, or move it aside by hand")
            elif os.path.abspath(P["qe"]) != os.path.dirname(rec["files"]["qe_input"]):
                refuse.append(f"{lab}: its QE input belongs in {os.path.dirname(rec['files']['qe_input'])}; give that --qe")
            else:
                done.append((lab, P, rec))
            continue
        att = json.load(open(P["attempts"])) if os.path.exists(P["attempts"]) else []
        if os.path.exists(P["qe"]):
            refuse.append(f"{lab}: {P['qe']} exists without a record in {a.work}")
        elif len(att) >= MAX_ATTEMPTS:
            refuse.append(f"{lab}: {len(att)} attempts without a complete output; no further rerun is allowed "
                          f"(item 4 'Interrupted jobs': (d) cannot be evaluated for this cell)")
        elif att and a.rerun_cause is None:
            refuse.append(f"{lab}: attempt {len(att)} (started {att[-1].get('started')}) left no record; it was "
                          f"interrupted. Give --rerun-cause ({', '.join(RERUN_CAUSES)}) to rerun it from the start")
        elif att and any(e.get(k) != v for e in att for k, v in ident.items()):
            refuse.append(f"{lab}: a rerun must use the identical scripts, model, step cap and region; differs in "
                          f"{sorted({k for e in att for k, v in ident.items() if e.get(k) != v})}")
        elif not att and partial_outputs(P):
            refuse.append(f"{lab}: outputs exist without an attempt log: {partial_outputs(P)}")
        todo.append((h, s, lab, P, att))
    if a.rerun_cause and not any(t[4] for t in todo):
        refuse.append("--rerun-cause given, but no listed cell has an interrupted attempt")
    if refuse:
        raise SystemExit("\n".join(refuse))
    for lab, P, rec in done:
        publish_qe(P, lab, rec)
        print(f"{lab}: complete ({P['record']}), skipped; QE input {rec['files']['qe_input']}")
    if not todo and os.path.exists(wfile):
        return
    if a.steps != STEPS:
        print(f"WARNING: --steps {a.steps} != {STEPS}: smoke test, not the PLAN protocol; analyse will not evaluate it")
    calc, model = load_model(a.model, a.model_sha256, a.threads)
    if model["zero_shot_foundation"]:
        print("NOTE: the model is the zero-shot MACE-MP-0 foundation file (a stand-in, not a WP3b result)")
    if not os.path.exists(wfile):
        write_wp2e(a, calc, model, wfile)
    for h, s, lab, P, att in todo:
        entry = {"attempt": len(att) + 1, "started": now(), "host": socket.gethostname(), "pid": os.getpid(), **ident,
                 "git": code["git"]}
        if att:                                   # rerun from the start; partial outputs moved aside unread
            d = os.path.join(a.work, "discarded", f"{lab}.attempt{len(att)}")
            os.makedirs(d, exist_ok=True)
            for p in partial_outputs(P):
                shutil.move(p, os.path.join(d, os.path.basename(p)))
            entry.update({"previous_attempt_stopped_by": a.rerun_cause, "note": a.rerun_note, "discarded_to": d})
        att = att + [entry]
        a29.dump_atomic(att, P["attempts"])
        relax_cell(a, calc, model, reg, rid, h, s, P, att, code)


# ---------------------------------------------------------------- analyse
def qe_geometry_dev(path, struct, rec):
    """Deviations between a QE output (and its archived input beside it, if any) and the relaxed structure."""
    o = read(io.StringIO(a32.read_text(path)), index=-1, format="espresso-out")
    assert o.get_chemical_symbols() == struct.get_chemical_symbols(), f"{path}: species differ from the relaxed structure"
    dev = {"output_A": float(find_mic(o.positions - struct.positions, struct.cell.array, pbc=True)[1].max()),
           "output_cell_A": float(np.abs(o.cell.array - struct.cell.array).max())}
    base = path.removesuffix(".gz").removesuffix(".out")
    for inp in (base + ".in", base + ".in.gz"):
        if os.path.exists(inp):
            i = read(io.StringIO(a32.read_text(inp)), format="espresso-in")
            dev.update({"input": inp, "input_A": float(max(np.abs(i.positions - struct.positions).max(),
                                                           np.abs(i.cell.array - struct.cell.array).max())),
                        "input_text_matches_relax": input_norm_sha256(inp) == rec["files"]["qe_input_norm_sha256"]})
    bad = (dev["output_A"] > 1e-4 or dev["output_cell_A"] > 1e-4 or dev.get("input_A", 0.0) > 1e-6
           or dev.get("input_text_matches_relax") is False)
    return dev, bad


def mtime(p):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(os.path.getmtime(p)))


def eval_cell(a, reg, rid, h, s, unc, O, q0):
    """One row of the per-cell table. wp3b_: status 'pass', 'fail' or 'cannot be evaluated';
    wp3bu_ (reported, not gating): 'complete' or 'missing'. Values come only from a usable record (and,
    for DFT values, a complete output of its relaxed structure)."""
    lab = label(h, s, unc); P = out_paths(a.work, None, lab)
    rc = reg["hosts"][h]["cells"][s]
    row = {"label": lab, "fails": [], "cannot": [], "notes": [], "qe_reruns": []}
    rec = json.load(open(P["record"])) if os.path.exists(P["record"]) else None
    att = json.load(open(P["attempts"])) if os.path.exists(P["attempts"]) else []
    row["attempts"] = rec["attempts"] if rec else att
    usable = False
    if rec is None:
        row["cannot"].append(f"no complete relaxation ({len(att)} attempt(s) without a record)" if att else "relaxation not run")
    else:
        bad = []
        if rec["label"] != lab or rec["constrained"] == unc:
            bad.append(f"record {rec['label']} (constrained {rec['constrained']}) is not {lab}")
        if rec.get("region_id") != rid:
            bad.append("relaxed with another free region (region_id)")
        if not rec["protocol"]["plan_protocol"]:
            bad.append(f"step cap {rec['protocol']['steps_cap']} != {STEPS} (smoke test, not the PLAN protocol)")
        if rec["model"]["sha256"] != a.model_sha256.lower():
            bad.append(f"relaxed with model {rec['model']['sha256']}, not --model-sha256")
        usable = not bad; row["cannot"] += bad
        if usable:                                # model-level values, from the relaxation record
            row["fails"] += rec["fail_reasons"]
            row.update({k: rec[k] for k in ("steps", "converged", "fmax_eVA", "nearest_I_to_vacancy_site_A",
                                             "dopant_displacement_A", "E_img0_eV", "E_relaxed_eV", "dE_relax_model_meV",
                                             "max_dr_nonfree_A", "basin_nonfree")})
            if unc:
                row["basin_beyond_6A"] = rec["basin_beyond_6A"]
            row.update({"topology_ok": rec["topology"]["topology_ok"], "model_sha256": rec["model"]["sha256"],
                        "code": {k: rec.get(k) for k in ("script_sha256", "helpers_sha256", "git")}})
        else:
            row["rejected_record"] = {"why": bad, "model_sha256": rec["model"]["sha256"],
                                      "steps_cap": rec["protocol"]["steps_cap"], "about": "no value of it is used"}
    f = O.get(lab)
    gave = sorted(glob.glob(os.path.join(a.dft, "**", f"{lab}.gaveup*"), recursive=True))
    tries = sorted(glob.glob(os.path.join(a.dft, "**", f"{lab}.out.try*"), recursive=True))
    for t in tries:                               # qe_queue.sh renames an output without JOB DONE to .out.tryN
        row["qe_reruns"].append({"label": lab, "kind": "QE resubmission", "file": t, "time": mtime(t),
                                 "time_source": "file mtime (the queue records no time)",
                                 "cause": "QE output without JOB DONE (renamed by qe_queue.sh)"})
    if gave:
        row["notes"].append(f"queue gave up: {[os.path.basename(x) for x in gave]} ({mtime(gave[0])})")
    q = a32.parse_qe(f) if f else None
    row["qe_output"] = f
    out_ok = False
    if f is not None and gave:
        row["cannot"].append("the queue gave up on this input, yet an output exists (a state qe_queue.sh cannot leave)")
    elif f is not None and len(tries) > 1:
        row["cannot"].append(f"{len(tries)} resubmissions before this output; item 1d allows one")
    elif f is None:
        row["cannot"].append("no QE output" + (" (queue gave up)" if gave else ""))
    elif q is None:
        row["cannot"].append("QE output without JOB DONE")
    elif not q["converged"]:
        (row["fails"] if usable else row["notes"]).append("SCF not converged (JOB DONE without 'convergence has been achieved')")
    elif q["forces"] is None:
        row["cannot"].append("QE output has no force block")
    elif usable:
        dev, gbad = qe_geometry_dev(f, read(P["structure"]), rec)
        row["qe_geometry_check"] = dev
        if gbad:
            row["cannot"].append(f"QE output/input is not the relaxed structure: {dev}")
        else:
            out_ok = True
            if "input" not in dev:
                row["notes"].append("no QE input beside the output; geometry checked on the output only")
    else:
        row["notes"].append("QE output present; not used (no usable relaxation record)")
    if out_ok:                                    # DFT values of the relaxed structure
        Fd = q["forces"]
        row.update({"free": norms(Fd, rc["free"]), "whole_cell": norms(Fd), "surface_1A": norms(Fd, rc["surface"]),
                    "surface_1A_own_distance": norms(Fd, rc["surface_own"]),
                    "F_dft_eV": q["F_eV"], "dE_relax_dft_meV": (q["F_eV"] - q0["F_eV"]) * 1000})
        row["free_pass"] = bool(row["free"]["rms_eVA"] < RMS_MAX and row["free"]["max_eVA"] < MAX_MAX)
        wc = bool(row["whole_cell"]["rms_eVA"] < RMS_MAX and row["whole_cell"]["max_eVA"] < MAX_MAX)
        if unc:
            row["criterion5_whole_cell_pass"] = wc        # 'criterion 5 as pre-registered' (item 4); Scope in notes
        else:
            row["whole_cell_below_thresholds"] = wc       # reported only; a WP3b cell is not criterion 5 (Scope)
            if not row["free_pass"]:
                row["fails"].append(f"free-atom residual RMS {row['free']['rms_eVA']:.4f} / max {row['free']['max_eVA']:.4f}"
                                    f" eV/A (needs < {RMS_MAX} / < {MAX_MAX})")
    if unc:                                       # reported, not gating; a missing value is reported as missing
        row["flags"] = row.pop("fails")
        row["status"] = "complete" if usable and out_ok else "missing"
        if row["status"] == "missing":
            row["missing_because"] = row["cannot"] or ["QE output not usable"]
    else:                                         # without a usable record nothing is a WP3b result
        row["status"] = ("cannot be evaluated" if not usable else "fail" if row["fails"]
                         else "cannot be evaluated" if row["cannot"] else "pass")
    row["zero_shot_img0"] = {"free": norms(q0["forces"], rc["free"]), "whole_cell": norms(q0["forces"]),
                             "surface_1A": norms(q0["forces"], rc["surface"]),
                             "surface_1A_own_distance": norms(q0["forces"], rc["surface_own"])}   # comparator
    return row, (rec if usable else None)


def wp2b_img0(wp2b):
    """F and forces of the six WP2b image-0 single points (image 0 of the DFT relaxation energies)."""
    R, q0 = a37.index_outputs(wp2b), {}
    for h in HOSTS:
        for s in SYSTEMS:
            q = a32.parse_qe(R[f"{h}_{s}_img0"]) if f"{h}_{s}_img0" in R else None
            if q is None or not q["converged"] or q["forces"] is None:
                raise SystemExit(f"{h}_{s}_img0: WP2b image-0 output missing or incomplete below {wp2b}")
            q0[(h, s)] = q
    return q0


def dft_wp2e(path, q0):
    q = a32.parse_qe(path)
    if q is None or not q["converged"]:
        raise SystemExit(f"{path}: WP2e relaxation output incomplete")
    return (q["F_eV"] - q0[("m30", "GA")]["F_eV"]) * 1000


def cmd_analyse(a):
    reg, rid = load_region(a.region, a.bands)
    O = a37.index_outputs(a.dft)
    q0 = wp2b_img0(a.wp2b)
    model_sha = a.model_sha256.lower()            # usable records are of this model only (eval_cell)
    cells, unc, recs = {}, {}, {}
    for h in HOSTS:
        for s in SYSTEMS:
            for flag, table in ((False, cells), (True, unc)):
                row, rec = eval_cell(a, reg, rid, h, s, flag, O, q0[(h, s)])
                table[row["label"]] = row; recs[row["label"]] = rec
    fails = [f"{k}: {x}" for k, r in cells.items() if r["status"] == "fail" for x in r["fails"]]
    cannot = [f"{k}: {x}" for k, r in cells.items() if r["status"] == "cannot be evaluated" for x in r["cannot"]]
    code = code_state()
    vers = {k: (r["script_sha256"], json.dumps(r.get("helpers_sha256"), sort_keys=True))
            for k, r in recs.items() if r is not None and k.startswith("wp3b_")}
    if len(set(vers.values())) > 1:               # one committed script relaxes all six cells (item 4, item 7)
        cannot.append(f"wp3b_ records made with different versions of scripts/40 or its helpers: "
                      f"{ {k: v[0][:12] for k, v in vers.items()} }")
    p = False if fails else (None if cannot else True)
    notes = [f"relaxation: {PROTOCOL_READING}", f"step cap: {STEP_CAP_RULE}", SCOPE_WP3BU,
             "surface: " + reg["surface_definition"]["about"]]
    if model_sha == FOUNDATION_SHA256:
        notes.append("the model is the zero-shot MACE-MP-0 foundation file: a stand-in, not a WP3b result")
    rcode = {k: recs[k] and {"script_sha256": recs[k]["script_sha256"], "git": recs[k].get("git")} for k in recs}
    if any(r and (r["script_sha256"] != code["script_sha256"] or not (r["git"] or {}).get("script_equals_head")
                  or (r["git"] or {}).get("uncommitted")) for r in rcode.values()):
        notes.append("some records were made with a scripts/40 that differs from the analysing one, or with uncommitted "
                     "scripts (item 2: the model note records the commit of scripts/40); see 'code'")
    hosts = {}
    for h in HOSTS:
        hosts[h] = {"about": "relaxation energy F(relaxed) - F(image 0), dopant - undoped (reported, not gating; None "
                             "unless both rows carry the value)"}
        for name, T, u in (("wp3b", cells, False), ("wp3bu", unc, True)):
            g = lambda s, k: T[label(h, s, u)].get(k)
            hosts[h][name] = {lvl: {d: (g(d, k) - g("undoped", k)) if g(d, k) is not None and g("undoped", k) is not None else None
                                    for d in ("GA", "Sr")}
                              for lvl, k in (("model_meV", "dE_relax_model_meV"), ("dft_meV", "dE_relax_dft_meV"))}
    # WP2e minimum (item 4 'Reported, not gating'); (1) and (3) from <work>/wp2e_minimum.json, (2) also needs wp3bu_
    w = {"dft_F_min_minus_img0_meV": dft_wp2e(a.wp2e, q0), "dft_plan_value_meV": DFT_WP2E_MEV, "missing": []}
    wfile = os.path.join(a.work, WP2E_FILE)
    x = json.load(open(wfile)) if os.path.exists(wfile) else None
    if x is None:
        w["missing"].append(f"(1), (3): no {wfile} (written by 'relax' before any relaxation)")
    elif x["model"]["sha256"] != model_sha:
        w["missing"].append(f"(1), (3): {wfile} is of model {x['model']['sha256']}, not --model-sha256"); x = None
    if x is not None:
        w.update({k: x[k] for k in ("E_model_img0_eV", "E_model_dftmin_eV", "dE_dftmin_minus_img0_meV", "frms_eVA",
                                    "fmax_eVA", "component_rms_eVA")})
        for k in (label("m30", "GA"), label("m30", "GA", True)):
            if recs[k] and abs(recs[k]["E_img0_eV"] - x["E_model_img0_eV"]) > 1e-6:
                notes.append(f"{k}: E_img0 {recs[k]['E_img0_eV']} != {WP2E_FILE} E_model_img0 {x['E_model_img0_eV']}")
    ru = recs[label("m30", "GA", True)]
    w["dE_dftmin_minus_wp3bu_final_meV"] = (x["E_model_dftmin_eV"] - ru["E_relaxed_eV"]) * 1000 if x and ru else None
    if w["dE_dftmin_minus_wp3bu_final_meV"] is None:
        w["missing"].append("(2): needs a usable wp3bu_m30_GA_img0 record and the (1) single point")
    w["about"] = ("(1) E_model(DFT min) - E_model(image 0) beside DFT -977.3 meV; (2) E_model(DFT min) - E_model(final "
                  "wp3bu_m30_GA_img0), fine-tuned model only (no zero-shot value; with the foundation file it is a stand-in); "
                  "(3) whole-cell per-atom-norm RMS / max of the model force at the DFT min (component RMS beside)")
    if a.zeroshot:
        w["zero_shot"] = json.load(open(a.zeroshot)).get("wp2e_minimum")
    zs = {k: {"free": r["zero_shot_img0"]["free"], "plan_rms_max_eVA": ZERO_SHOT[tuple(k.split("_")[1:3])],
              "reproduced": [round(r["zero_shot_img0"]["free"][x_], 3) for x_ in ("rms_eVA", "max_eVA")]
                            == list(ZERO_SHOT[tuple(k.split("_")[1:3])])}
          for k, r in cells.items()}
    reruns = [{"label": k, "kind": "relaxation rerun", "time": e.get("started"), "cause": e.get("previous_attempt_stopped_by"),
               **e} for k, r in {**cells, **unc}.items() for e in r["attempts"] if e.get("attempt", 1) > 1]
    reruns += [e for r in {**cells, **unc}.values() for e in r["qe_reruns"]]
    res = {"item": "PLAN amendment m item 4 (d), WP3b", "pass": p,
           "verdict": "pass" if p else ("fail" if p is False else "cannot be evaluated"),
           "reasons": fails + cannot, "notes": notes,
           "thresholds": {"free_rms_eVA": RMS_MAX, "free_max_eVA": MAX_MAX, "fmax_relax_eVA": FMAX, "steps": STEPS,
                          "vacancy_I_A": GAP_MIN, "dopant_move_A": DOPANT_MAX},
           "model_sha256": model_sha, "script_sha256": code["script_sha256"],
           "code": {"analysing": code, "records": rcode},
           "region": {"path": os.path.abspath(a.region), "region_id": rid, "file_sha256": sha256_file(a.region),
                      "n_free": {f"{h}_{s}": reg["hosts"][h]["cells"][s]["n_free"] for h in HOSTS for s in SYSTEMS},
                      "surface_definition": reg["surface_definition"]},
           "inputs": {"dft": os.path.abspath(a.dft), "wp2b": os.path.abspath(a.wp2b), "wp2e": os.path.abspath(a.wp2e),
                      "work": os.path.abspath(a.work)},
           "cells": cells, "hosts": hosts, "unconstrained": unc, "wp2e_minimum": w,
           "zero_shot_comparator": zs, "reruns": reruns}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    a29.dump_atomic(res, a.out)
    for k, r in cells.items():
        fr = r.get("free"); z = r["zero_shot_img0"]["free"]
        print(f"{k:<24} {r['status']:<20} free " + (f"{fr['rms_eVA']:.3f}/{fr['max_eVA']:.3f}" if fr else "   -/-   ")
              + f"  (zero-shot img0 {z['rms_eVA']:.3f}/{z['max_eVA']:.3f})")
    for k, r in unc.items():
        wc = r.get("whole_cell")
        print(f"{k:<24} {r['status']:<20} whole cell " + (f"{wc['rms_eVA']:.3f}/{wc['max_eVA']:.3f}" if wc else "-"))
    print(f"(d) WP3b: {res['verdict']}" + (f"; {len(res['reasons'])} reason(s)" if res["reasons"] else "") + f" -> {a.out}")
    for n_ in notes[4:]:
        print("NOTE:", n_)


# ---------------------------------------------------------------- zeroshot
def cmd_zeroshot(a):
    reg, _ = load_region(a.region, a.bands)
    q0 = wp2b_img0(a.wp2b)
    table, bad = {}, []
    for h in HOSTS:
        for s in SYSTEMS:
            q, rc, exp = q0[(h, s)], reg["hosts"][h]["cells"][s], ZERO_SHOT[(h, s)]
            fr = norms(q["forces"], rc["free"])
            ok = round(fr["rms_eVA"], 3) == exp[0] and round(fr["max_eVA"], 3) == exp[1]
            table[f"{h}_{s}"] = {"free": fr, "whole_cell": norms(q["forces"]), "surface_1A": norms(q["forces"], rc["surface"]),
                                 "surface_1A_own_distance": norms(q["forces"], rc["surface_own"]),
                                 "plan_rms_max_eVA": exp, "reproduced": ok}
            bad += [] if ok else [f"{h}_{s}: {fr['rms_eVA']:.4f}/{fr['max_eVA']:.4f} != {exp}"]
            print(f"{h} {s:<8} free {fr['rms_eVA']:.3f} / {fr['max_eVA']:.3f} eV/A (PLAN {exp[0]:.3f} / {exp[1]:.3f})"
                  f" {'ok' if ok else 'DIFFERS'}")
    d = dft_wp2e(a.wp2e, q0)
    bad += [] if round(d, 1) == DFT_WP2E_MEV else [f"DFT F(WP2e min) - F(image 0) {d:.2f} != {DFT_WP2E_MEV}"]
    print(f"DFT F(WP2e minimum) - F(image 0): {d:+.2f} meV (PLAN {DFT_WP2E_MEV:+.1f})")
    res = {"item": "PLAN amendment m item 4, zero-shot comparator (not a decision rule)", "image0_free_atoms": table,
           "dft_F_wp2emin_minus_img0_meV": d}
    if not a.no_mace:
        import torch
        torch.set_num_threads(a.threads)
        from mace.calculators import mace_mp
        calc = mace_mp(model="medium", device="cpu", default_dtype="float64")      # as scripts/32 and 37
        assert all(p.dtype == torch.float64 for m in calc.models for p in m.parameters())
        img0 = start_cell(a.bands, "m30", "GA")
        E0, _ = model_point(calc, img0)
        Em, Fm = model_point(calc, wp2e_minimum(a.wp2e, img0))
        w = {"source": os.path.abspath(a.wp2e), "E_model_img0_eV": E0, **wp2e_values(E0, Em, Fm)}
        w["reproduced"] = {k: round(w[k], dd) == v for k, (v, dd) in ZERO_SHOT_WP2E.items()}
        bad += [f"WP2e {k}: {w[k]:.4f} != {ZERO_SHOT_WP2E[k][0]}" for k, ok in w["reproduced"].items() if not ok]
        res["wp2e_minimum"] = w
        print(f"WP2e minimum (zero-shot): dE {w['dE_dftmin_minus_img0_meV']:+.1f} meV (PLAN +227.0), "
              f"force {w['frms_eVA']:.3f} / {w['fmax_eVA']:.3f} eV/A (PLAN 0.115 / 0.260), "
              f"component RMS {w['component_rms_eVA']:.3f} (PLAN 0.067)")
    res["reproduced"] = not bad; res["differences"] = bad
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    a29.dump_atomic(res, a.out)
    print(f"reproduced: {not bad} -> {a.out}")
    if bad:
        raise SystemExit("\n".join(bad))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    def common(p):
        p.add_argument("--bands", default="../bands", help="dir with band_<system>_mNN.extxyz")
        return p
    r = common(sub.add_parser("region", help="build the free region of the 6 cells"))
    r.add_argument("--pool", default="results/fa_host/pool_v3_harmonised")
    r.add_argument("--vac-ref", default="results/fa_host/pool_v2/fa19cspb20i59_232_vI.extxyz")
    r.add_argument("--radius", type=float, default=RADIUS, help=f"PLAN: {RADIUS} A; other values for tests only")
    r.add_argument("--out", required=True, help="region JSON")
    x = common(sub.add_parser("relax", help="frozen-far-field (or --unconstrained) FIRE relaxation + QE inputs"))
    x.add_argument("--region", required=True)
    x.add_argument("--model", required=True, help="model file (the selected wp3.model)")
    x.add_argument("--model-sha256", required=True, help="the sha256 of the committed model note (item 2)")
    x.add_argument("--cells", nargs="+", default=[f"{h}_{s}" for h in HOSTS for s in SYSTEMS])
    x.add_argument("--unconstrained", action="store_true", help="no FixAtoms: labels wp3bu_<host>_<system>_img0")
    x.add_argument("--work", required=True, help="relaxed structures, records, attempt logs, wp2e_minimum.json")
    x.add_argument("--qe", required=True, help="QE inputs go to <qe>/<label>/<label>.in (after the record is written)")
    x.add_argument("--steps", type=int, default=STEPS, help=f"FIRE step cap (PLAN: {STEPS}; smaller = smoke test)")
    x.add_argument("--wp2e", default=WP2E_RELAX, help="WP2e DFT relaxation output (m30 GA)")
    x.add_argument("--rerun-cause", choices=RERUN_CAUSES, default=None,
                   help="cause of the stop of an interrupted attempt; reruns it from the start (at most twice)")
    x.add_argument("--rerun-note", default=None, help="free text kept with the rerun (e.g. when the node was lost)")
    x.add_argument("--threads", type=int, default=6)
    y = common(sub.add_parser("analyse", help="(d) from the wp3b_ / wp3bu_ QE outputs"))
    y.add_argument("--region", required=True)
    y.add_argument("--work", required=True, help="the relax --work (wp3b_ and wp3bu_ records, wp2e_minimum.json)")
    y.add_argument("--dft", required=True, help="dir with the wp3b_/wp3bu_ <label>.out(.gz), any depth")
    y.add_argument("--wp2b", default=WP2B_RAW, help="dir with the WP2b image-0 outputs <host>_<system>_img0.out(.gz)")
    y.add_argument("--wp2e", default=WP2E_RELAX, help="WP2e DFT relaxation output (m30 GA)")
    y.add_argument("--model-sha256", required=True, help="the committed model sha256; every record must be of this "
                   "model, and it is written as top-level 'model_sha256' (scripts/39 refuses any other)")
    y.add_argument("--zeroshot", default=None, help="zeroshot JSON, reported beside the WP2e-minimum values")
    y.add_argument("--out", required=True, help="result JSON (read by scripts/39 --wp3b-json)")
    z = common(sub.add_parser("zeroshot", help="reproduce the zero-shot comparator of item 4"))
    z.add_argument("--region", required=True)
    z.add_argument("--wp2b", default=WP2B_RAW)
    z.add_argument("--wp2e", default=WP2E_RELAX)
    z.add_argument("--no-mace", action="store_true", help="DFT values only")
    z.add_argument("--threads", type=int, default=4)
    z.add_argument("--out", required=True)
    a = ap.parse_args()
    {"region": cmd_region, "relax": cmd_relax, "analyse": cmd_analyse, "zeroshot": cmd_zeroshot}[a.cmd](a)


if __name__ == "__main__":
    main()

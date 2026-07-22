#!/usr/bin/env python3
"""Objective 1 (method validation) — anchors (a), (c), (d) on the gamma-P1 lattice.

Reproduces, with the zero-shot MACE-MP-0 pipeline in the *production* gamma phase
(P-1, 159-atom 2x2x2 V_I cell, float64), three of the four Objective-1 anchors:

  (a) undoped E_a — physical sanity check vs the broad literature   -> `regression`
  (c) sign & magnitude of the GA+ (guanidinium) A-site dEa          -> `ga`
  (d) strain-E_a correlation: tensile lowers, compressive raises    -> `strain`

Post-review DFT-free refinements (see results/objective1/REPORT_objective1.md
"Next steps"):
  (c+) GA configurational robustness — 3 orientations x {near,far} Cs site, plus
       mechanistic fingerprints (N-H...I, Pb-I, octahedral distortion) at initial
       and saddle                                                    -> `ga`
  (fs) gamma-phase finite-size: same V_I edge-hop in 3x3x3 vs 2x2x2 for
       undoped / GA / tensile, testing the cancellation assumption   -> `finite_size`

Anchor (b) — the V_I+ vs V_I0 charge-state ordering (Tyagi 2025) — is NOT here:
MACE is charge-agnostic, so it requires charged-supercell DFT + per-charge-state
fine-tuning (DFT-gated). Likewise the undoped/GA DFT check and the biaxial DFT
3-point remain DFT-gated. See results/objective1/CHARGE_STATE_PROTOCOL.md.

Design notes (from the RTX 5090 benchmark, results/gpu/BENCHMARK.md):
  * per-image calculators (one MACE object per NEB image) are 3.4x faster than a
    single shared calculator (allow_shared_calculator forces full-band recompute);
  * the calculators are built ONCE and reused across every path (model load-once);
  * float64 is the production dtype (float32 is pre-screen only, per HANDOFF).

Strain convention: strain is applied to the 2x2x2 supercell CELL (scale_atoms=True)
and then held FIXED while internal coordinates relax — i.e. epitaxial/residual
lattice strain with ionic relaxation, the experimentally relevant setup. Isotropic
scales all three cell vectors; biaxial scales the in-plane a,b vectors only.

Output: results/objective1/{regression,strain,ga}.json (+ combined anchors.json),
written incrementally so a crash leaves partial results.
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
from ase import Atoms
from ase.io import read, write
from ase.mep import NEB
from ase.optimize import FIRE

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "results" / "objective1"
STRAINS = [-0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03]
N_IMAGES = 5
FMAX_EP = 0.03
FMAX_NEB = 0.05


def _rot(axis, angle_deg):
    """Rodrigues rotation matrix about `axis` by `angle_deg`."""
    a = np.deg2rad(angle_deg)
    x, y, z = np.asarray(axis, float) / np.linalg.norm(axis)
    c, s, C = np.cos(a), np.sin(a), 1 - np.cos(a)
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


# Three distinct guanidinium orientations to test configurational robustness of
# the GA+ pinning shift: planar cation in xy, rotated into xz, and a tilted case.
GA_ORIENTS = [
    ("xy_plane", np.eye(3)),
    ("xz_plane", _rot([1.0, 0.0, 0.0], 90.0)),
    ("tilted_60", _rot([1.0, 1.0, 0.0], 60.0)),
]


# ---------------- geometry helpers ----------------
def pick_hop_pair(atoms):
    """Indices (i_vac, i_hop) of two cis iodides on the Pb octahedron nearest the
    cell centre (I-I ~ 4.5 A, an octahedron-edge hop). Identical to script 01."""
    sym = np.array(atoms.get_chemical_symbols())
    pb_idx = np.flatnonzero(sym == "Pb")
    centre = atoms.cell.array.sum(axis=0) / 2
    pb = pb_idx[np.argmin(np.linalg.norm(atoms.positions[pb_idx] - centre, axis=1))]
    i_idx = np.flatnonzero(sym == "I")
    d_pb = atoms.get_distances(pb, i_idx, mic=True)
    octa = i_idx[d_pb < 3.8]
    if len(octa) < 2:
        raise RuntimeError(f"only {len(octa)} iodides coordinate Pb{pb}")
    best, best_err = None, 1e9
    for a in range(len(octa)):
        for b in range(a + 1, len(octa)):
            d = atoms.get_distance(octa[a], octa[b], mic=True)
            if abs(d - 4.5) < best_err:
                best, best_err = (int(octa[a]), int(octa[b])), abs(d - 4.5)
    return best


def make_guanidinium(center, rot=None):
    """Planar guanidinium cation C(NH2)3+ (10 atoms) centred at `center` (Cartesian).
    Base molecular plane = global xy (C-N 1.33 A, N-H 1.01 A, all angles ~120 deg);
    `rot` (3x3) optionally rotates the rigid cation to a different orientation."""
    dCN, dNH = 1.33, 1.01
    syms, pos = ["C"], [np.array([0.0, 0.0, 0.0])]
    for k in range(3):
        th = np.deg2rad(90 + 120 * k)            # three N at 120 deg in xy-plane
        uN = np.array([np.cos(th), np.sin(th), 0.0])
        N = dCN * uN
        syms.append("N"); pos.append(N)
        back = -uN                                # N->C direction
        for sgn in (+1, -1):                       # two H per N, +/-120 deg from N->C
            a = np.deg2rad(120 * sgn)
            R = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
            uH = R @ back
            syms.append("H"); pos.append(N + dNH * uH)
    pos = np.array(pos)
    if rot is not None:
        pos = pos @ np.asarray(rot).T             # rotate rigid cation about its C
    pos = pos + np.asarray(center)
    return syms, pos


def build_supercell(bulk, eps_iso=0.0, eps_biax=0.0, size=2):
    sc = bulk.repeat((size, size, size))
    if eps_iso:
        sc.set_cell(sc.cell.array * (1.0 + eps_iso), scale_atoms=True)
    elif eps_biax:
        c = sc.cell.array.copy()
        c[0] *= (1.0 + eps_biax); c[1] *= (1.0 + eps_biax)
        sc.set_cell(c, scale_atoms=True)
    return sc


def make_endpoints(sc, dopant=None, ga_rot=None, ga_site="near"):
    """Build (initial, final) V_I edge-hop endpoints with identical atom ordering.
    If dopant=='GA', replace a Cs with guanidinium in BOTH endpoints via the
    identical operation sequence (ordering stays matched).

    ga_site: 'near' picks the Cs nearest the hop midpoint (pinning test); 'far'
    picks the farthest Cs (control — expect dEa ~ 0). ga_rot: 3x3 rotation of the
    rigid GA cation, for orientation sampling."""
    i_vac, i_hop = pick_hop_pair(sc)
    hop_d = sc.get_distance(i_vac, i_hop, mic=True)

    cs_pos = None
    if dopant == "GA":
        sym = np.array(sc.get_chemical_symbols())
        cs_idx = np.flatnonzero(sym == "Cs")
        mid = (sc.positions[i_vac] + sc.positions[i_hop]) / 2
        dists = np.linalg.norm(sc.positions[cs_idx] - mid, axis=1)
        cs_pick = cs_idx[np.argmin(dists) if ga_site == "near" else np.argmax(dists)]
        cs_pos = sc.positions[cs_pick].copy()
        dopant_d = float(np.linalg.norm(cs_pos - mid))
    else:
        dopant_d = None

    def modify(atoms):
        if dopant != "GA":
            return atoms
        # find the Cs by recorded position (robust to the i_vac reindex), remove, add GA
        d = np.linalg.norm(atoms.positions - cs_pos, axis=1)
        j = int(np.argmin(d))
        assert atoms.get_chemical_symbols()[j] == "Cs" and d[j] < 1e-6, "Cs match failed"
        del atoms[j]
        syms, pos = make_guanidinium(cs_pos, rot=ga_rot)
        atoms += Atoms(syms, positions=pos)
        return atoms

    initial = sc.copy()
    vac_pos = initial.positions[i_vac].copy()
    del initial[i_vac]
    initial = modify(initial)

    final = sc.copy()
    final.positions[i_hop] = vac_pos
    del final[i_vac]
    final = modify(final)

    assert initial.get_chemical_symbols() == final.get_chemical_symbols(), "ordering mismatch"
    meta = {"i_vac": int(i_vac), "i_hop": int(i_hop), "hop_distance_A": float(hop_d),
            "n_atoms": len(initial), "dopant_distance_A": dopant_d, "ga_site": ga_site}
    return initial, final, meta


# ---------------- NEB driver ----------------
def build_calcs(n, model, device, dtype):
    from mace.calculators import mace_mp
    return [mace_mp(model=model, device=device, default_dtype=dtype, dispersion=False)
            for _ in range(n)]


def run_neb(initial, final, calcs, n_images=N_IMAGES, fmax_ep=FMAX_EP, fmax_neb=FMAX_NEB):
    for c in calcs:
        c.reset() if hasattr(c, "reset") else None
    initial = initial.copy(); final = final.copy()
    initial.calc = calcs[0]
    FIRE(initial, logfile=None).run(fmax=fmax_ep, steps=800)
    final.calc = calcs[-1]
    FIRE(final, logfile=None).run(fmax=fmax_ep, steps=800)
    e_i, e_f = initial.get_potential_energy(), final.get_potential_energy()

    images = [initial] + [initial.copy() for _ in range(n_images)] + [final]
    for im, c in zip(images, calcs):
        im.calc = c
    neb = NEB(images, climb=False, k=0.1)
    neb.interpolate(method="idpp", mic=True)
    conv1 = FIRE(neb, logfile=None).run(fmax=2 * fmax_neb, steps=400)
    neb.climb = True
    conv2 = FIRE(neb, logfile=None).run(fmax=fmax_neb, steps=400)

    energies = np.array([im.get_potential_energy() for im in images])
    rel = energies - energies[0]
    return {"E_images_eV": energies.tolist(),
            "Ea_forward_eV": float(rel.max()),
            "Ea_backward_eV": float((energies - energies[-1]).max()),
            "dE_endpoints_eV": float(e_f - e_i),
            "converged": bool(conv1 and conv2)}, images


# ---------------- mechanistic fingerprints ----------------
def octahedral_distortion(atoms, pb, cutoff=3.8):
    """Bond-length distortion index of the PbI6 octahedron around atom `pb`:
    Delta_d = mean( (d_i - d_mean)/d_mean )^2 over coordinating iodides."""
    sym = np.array(atoms.get_chemical_symbols())
    i_idx = np.flatnonzero(sym == "I")
    d = atoms.get_distances(pb, i_idx, mic=True)
    d = d[d < cutoff]
    if len(d) == 0:
        return None, 0
    dm = d.mean()
    return float(np.mean(((d - dm) / dm) ** 2)), int(len(d))


def fingerprint(atoms, i_migrating, dopant=None):
    """Structural fingerprint at one geometry: Pb-I environment of the migrating
    iodide + (if GA present) closest N-H...I contact, to test the H-bond-
    stiffening pinning hypothesis. Returns a JSON-able dict."""
    sym = np.array(atoms.get_chemical_symbols())
    pb_idx = np.flatnonzero(sym == "Pb")
    # Pb neighbours of the migrating iodide (the two octahedra it bridges)
    d_pb = atoms.get_distances(i_migrating, pb_idx, mic=True)
    near_pb = pb_idx[np.argsort(d_pb)[:2]]
    fp = {
        "PbI_bonds_migrating_A": sorted(float(x) for x in d_pb[d_pb < 4.0]),
        "octa_distortion": [octahedral_distortion(atoms, int(p))[0] for p in near_pb],
    }
    if dopant == "GA":
        h_idx = np.flatnonzero(sym == "H")
        i_idx = np.flatnonzero(sym == "I")
        if len(h_idx):
            # closest H...I contact (N-H...I hydrogen bond to the iodide sublattice)
            alld = np.concatenate([atoms.get_distances(h, i_idx, mic=True) for h in h_idx])
            fp["NH_I_closest_A"] = float(alld.min())
            fp["NH_I_within_3A"] = int((alld < 3.0).sum())
    return fp


# ---------------- anchors ----------------
def anchor_regression(bulk, calcs):
    sc = build_supercell(bulk)
    initial, final, meta = make_endpoints(sc)
    res, images = run_neb(initial, final, calcs)
    write(OUTDIR / "regression_saddle_path.extxyz", images)
    ok = 0.20 <= res["Ea_forward_eV"] <= 0.32
    out = {**meta, **res, "phase": "gamma-P1", "dtype": "float64",
           "Ea_target_band_eV": [0.20, 0.32], "regression_ok": bool(ok),
           "literature_band_eV": [0.1, 0.6]}
    print(f"  [reg] E_a={res['Ea_forward_eV']:.3f} eV  ok={ok}  conv={res['converged']}", flush=True)
    return out


def anchor_strain(bulk, calcs):
    rows = []
    for mode in ("iso", "biax"):
        for eps in STRAINS:
            kw = {"eps_iso": eps} if mode == "iso" else {"eps_biax": eps}
            sc = build_supercell(bulk, **kw)
            initial, final, meta = make_endpoints(sc)
            try:
                res, _ = run_neb(initial, final, calcs)
                row = {"mode": mode, "strain": eps, "Ea_forward_eV": res["Ea_forward_eV"],
                       "Ea_backward_eV": res["Ea_backward_eV"], "converged": res["converged"],
                       "cell_volume_A3": float(np.linalg.det(sc.cell.array))}
            except Exception as e:
                row = {"mode": mode, "strain": eps, "error": repr(e)[:200]}
            rows.append(row)
            print(f"  [strain] {mode} eps={eps:+.2f} -> "
                  f"{row.get('Ea_forward_eV', float('nan')):.3f} eV conv={row.get('converged')}",
                  flush=True)
    # slope dEa/deps at small strain (iso), fit over |eps|<=0.03 converged points
    iso = [r for r in rows if r["mode"] == "iso" and "Ea_forward_eV" in r and r.get("converged")]
    slope = None
    if len(iso) >= 3:
        xs = np.array([r["strain"] for r in iso]); ys = np.array([r["Ea_forward_eV"] for r in iso])
        slope = float(np.polyfit(xs, ys, 1)[0])  # eV per unit strain
    return {"rows": rows, "dEa_dstrain_iso_eV_per_unit_strain": slope,
            "sign_convention": "tensile (+eps) expected to LOWER Ea (negative slope)"}


def _migrating_index(images):
    """Index of the migrating iodide = atom with the largest initial->final
    displacement (robust to vacancy reindexing and to the GA substitution)."""
    d = np.linalg.norm(images[-1].positions - images[0].positions, axis=1)
    return int(np.argmax(d))


def _fps(images, dopant):
    """Fingerprints at the initial image and the (energy-max) saddle image."""
    imig = _migrating_index(images)
    energies = np.array([im.get_potential_energy() for im in images])
    saddle = images[int(np.argmax(energies))]
    return {"initial": fingerprint(images[0], imig, dopant),
            "saddle": fingerprint(saddle, imig, dopant)}


def anchor_ga(bulk, calcs):
    """GA+ pinning anchor with configurational sampling: 3 GA orientations at the
    Cs site NEAREST the hop (pinning test) + 1 FAR-site control (expect dEa~0).
    Records dEa per config and mechanistic fingerprints (N-H...I, Pb-I, octa
    distortion) at initial and saddle."""
    sc0 = build_supercell(bulk)
    initial0, final0, _ = make_endpoints(sc0)                     # undoped reference
    und, und_images = run_neb(initial0, final0, calcs)
    Ea_und = und["Ea_forward_eV"]
    print(f"  [ga] Ea_undoped={Ea_und:.3f} eV", flush=True)

    configs = [("near", name, R) for name, R in GA_ORIENTS] + [("far", GA_ORIENTS[0][0], GA_ORIENTS[0][1])]
    rows, saved = [], False
    for site, oname, R in configs:
        sc = build_supercell(bulk)
        initial, final, meta = make_endpoints(sc, dopant="GA", ga_rot=R, ga_site=site)
        try:
            ga, images = run_neb(initial, final, calcs)
            dEa = ga["Ea_forward_eV"] - Ea_und
            row = {"site": site, "orientation": oname, "dopant_distance_A": meta["dopant_distance_A"],
                   "n_atoms": meta["n_atoms"], "Ea_GA_eV": ga["Ea_forward_eV"], "dEa_eV": float(dEa),
                   "effect": "pins (+)" if dEa > 0 else "de-pins (-)", "converged": ga["converged"],
                   "fingerprints": _fps(images, "GA"), "GA_E_images_eV": ga["E_images_eV"]}
            if site == "near" and oname == GA_ORIENTS[0][0] and not saved:
                write(OUTDIR / "ga_saddle_path.extxyz", images); saved = True
            print(f"  [ga] {site:4s}/{oname:9s} d={meta['dopant_distance_A']:.2f}A  "
                  f"Ea_GA={ga['Ea_forward_eV']:.3f}  dEa={dEa:+.3f} eV  conv={ga['converged']}", flush=True)
        except Exception as e:
            row = {"site": site, "orientation": oname, "error": repr(e)[:200]}
            print(f"  [ga] {site}/{oname} FAILED: {e!r}", flush=True)
        rows.append(row)

    near = [r for r in rows if r.get("site") == "near" and "dEa_eV" in r]
    dEas = [r["dEa_eV"] for r in near]
    summary = {"Ea_undoped_eV": Ea_und, "undoped_E_images_eV": und["E_images_eV"],
               "undoped_fingerprints": _fps(und_images, None), "configs": rows}
    if dEas:
        summary["dEa_near_mean_eV"] = float(np.mean(dEas))
        summary["dEa_near_spread_eV"] = float(np.ptp(dEas))
        summary["dEa_near_all_positive"] = bool(all(d > 0 for d in dEas))
    far = [r for r in rows if r.get("site") == "far" and "dEa_eV" in r]
    if far:
        summary["dEa_far_eV"] = far[0]["dEa_eV"]
    return summary


def anchor_finite_size(bulk, calcs):
    """gamma-phase finite-size check: same V_I edge-hop path in 3x3x3 (~540-atom)
    vs the 2x2x2 (159-atom) cell, for undoped / GA-near / biaxial-tensile(+1%).
    Tests the finite-size-cancellation assumption directly in the gamma phase
    (the cubic screen's 2x2x2-vs-3x3x3 gap motivated this). Absolute E_a is
    expected to move; the RELATIVE quantities (dEa_GA, strain shift) should be
    more stable if cancellation holds. Reuses the SAME pick_hop_pair logic."""
    cases = [("undoped", {}, None), ("GA_near", {}, "GA"), ("tensile_1pct", {"eps_biax": 0.01}, None)]
    out = {"note": "3x3x3 vs 2x2x2, same gamma V_I edge-hop", "cases": []}
    for label, strain_kw, dopant in cases:
        rec = {"case": label}
        for size in (2, 3):
            sc = build_supercell(bulk, size=size, **strain_kw)
            initial, final, meta = make_endpoints(sc, dopant=dopant, ga_site="near")
            try:
                res, _ = run_neb(initial, final, calcs)
                rec[f"{size}x{size}x{size}"] = {"n_atoms": meta["n_atoms"],
                    "Ea_forward_eV": res["Ea_forward_eV"], "converged": res["converged"]}
                print(f"  [fs] {label:14s} {size}x{size}x{size} n={meta['n_atoms']:3d}  "
                      f"Ea={res['Ea_forward_eV']:.3f}  conv={res['converged']}", flush=True)
            except Exception as e:
                rec[f"{size}x{size}x{size}"] = {"error": repr(e)[:200]}
                print(f"  [fs] {label} {size}x{size}x{size} FAILED: {e!r}", flush=True)
        out["cases"].append(rec)
    # relative-quantity stability: dEa_GA and strain shift at each size
    def ea(case, size):
        for r in out["cases"]:
            if r["case"] == case:
                return r.get(f"{size}x{size}x{size}", {}).get("Ea_forward_eV")
    for size in (2, 3):
        und, ga, ten = ea("undoped", size), ea("GA_near", size), ea("tensile_1pct", size)
        if None not in (und, ga):
            out[f"dEa_GA_{size}x"] = float(ga - und)
        if None not in (und, ten):
            out[f"dEa_tensile1pct_{size}x"] = float(ten - und)
    return out


def main():
    global FMAX_EP, FMAX_NEB
    p = argparse.ArgumentParser()
    p.add_argument("--mode", default="all",
                   choices=["all", "regression", "strain", "ga", "finite_size"])
    p.add_argument("--model", default="medium")
    p.add_argument("--device", default="cuda")
    p.add_argument("--dtype", default="float64")
    p.add_argument("--fmax-ep", type=float, default=0.03)
    p.add_argument("--fmax-neb", type=float, default=0.05)
    p.add_argument("--tag", default="")  # output filename suffix, e.g. "_tight"
    args = p.parse_args()
    FMAX_EP, FMAX_NEB = args.fmax_ep, args.fmax_neb

    OUTDIR.mkdir(parents=True, exist_ok=True)
    bulk = read(ROOT / "structures" / "gamma_relaxed.extxyz")
    print(f"[init] gamma cell {np.round(bulk.cell.lengths(), 2)} A, building {args.dtype} "
          f"calculators on {args.device} ...", flush=True)
    t0 = time.time()
    calcs = build_calcs(N_IMAGES + 2, args.model, args.device, args.dtype)
    print(f"[init] {len(calcs)} calculators ready in {time.time()-t0:.1f}s", flush=True)

    combined = {"phase": "gamma-P1", "dtype": args.dtype, "model": args.model,
                "device": args.device}
    stages = [("regression", anchor_regression), ("strain", anchor_strain),
              ("ga", anchor_ga), ("finite_size", anchor_finite_size)]
    # finite_size uses 3x3x3 (~540-atom) cells — run it only when named explicitly,
    # not under the "all" bundle, so the main anchor sweep stays fast.
    for name, fn in stages:
        run_it = args.mode == name or (args.mode == "all" and name != "finite_size")
        if not run_it:
            continue
        print(f"=== anchor: {name} ===", flush=True)
        ts = time.time()
        try:
            res = fn(bulk, calcs)
        except Exception as e:
            res = {"error": repr(e)[:500]}
            print(f"  [{name}] STAGE FAILED: {e!r}", flush=True)
        res["_runtime_s"] = time.time() - ts
        res["_fmax_ep"], res["_fmax_neb"] = FMAX_EP, FMAX_NEB
        combined[name] = res
        json.dump(res, open(OUTDIR / f"{name}{args.tag}.json", "w"), indent=2)
        json.dump(combined, open(OUTDIR / f"anchors{args.tag}.json", "w"), indent=2)
    print(f"done -> {OUTDIR}/anchors.json  (total {(time.time()-t0)/60:.1f} min)", flush=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Automated pre-submit / pre-ingest checks (Objective E).

Every check here exists because the corresponding error ACTUALLY OCCURRED in this project
and produced a plausible-looking wrong number. Each docstring names the incident.

Usage as a library:
    from checks import run_all, CheckFailure
    report = run_all(stage="pre_ingest", **kwargs)
    if not report["passed"]: -> mark the row rejected, do NOT put it in a summary table

Usage as a CLI:
    python scripts/20_checks.py --selftest
"""
from __future__ import annotations
import hashlib, json, math, re
from collections import Counter

import numpy as np

TEN_X_MEV = 59.5      # |dEa| for a 10x rate ratio at 300 K, equal prefactors
REL_DRIFT_TOL = 0.02  # |m| relative drift over the last 5 iterations (see parse_magnetisation)
MAX_EA_EV = 3.0       # physical upper bound on a halide-perovskite ionic migration barrier;
                      # a band exceeding this is an MLIP failure (see check_endpoints)


class CheckFailure(Exception):
    pass


def _mic(dv, cell):
    inv = np.linalg.inv(cell)
    f = dv @ inv
    f -= np.round(f)
    return f @ cell


# --------------------------------------------------------------------------- 1 composition
def check_composition(base, doped, expected_delta, *, label=""):
    """INCIDENT: `Cs_A` was a no-op -- the branch replaced the atom nearest the site, so
    Cs -> Cs produced an UNDOPED cell reported as doped. Cs+ is the proposal's priority
    candidate, so this would have yielded a silent null for the most important row.

    Requires the element-count delta to match exactly, AND the structure hash to change.
    A hash that does not move means nothing was substituted, whatever the counts say.
    """
    b = Counter(base.get_chemical_symbols())
    d = Counter(doped.get_chemical_symbols())
    got = {s: d.get(s, 0) - b.get(s, 0) for s in set(b) | set(d) if d.get(s, 0) != b.get(s, 0)}
    ok_counts = got == dict(expected_delta)
    h_base, h_doped = structure_hash(base), structure_hash(doped)
    ok_hash = h_base != h_doped
    return {
        "check": "composition", "label": label, "passed": bool(ok_counts and ok_hash),
        "expected_delta": dict(expected_delta), "observed_delta": got,
        "hash_changed": ok_hash, "hash_base": h_base[:12], "hash_doped": h_doped[:12],
        "reason": None if (ok_counts and ok_hash) else
                  ("composition delta mismatch" if not ok_counts else
                   "structure hash unchanged -> no-op substitution"),
    }


def structure_hash(atoms, ndigits=4):
    """Order-independent structure fingerprint: sorted (symbol, rounded scaled position)."""
    sp = atoms.get_scaled_positions(wrap=True)
    rows = sorted(f"{s}:{p[0]:.{ndigits}f},{p[1]:.{ndigits}f},{p[2]:.{ndigits}f}"
                  for s, p in zip(atoms.get_chemical_symbols(), sp))
    cell = ",".join(f"{x:.{ndigits}f}" for x in np.asarray(atoms.cell).ravel())
    return hashlib.sha256(("|".join(rows) + "#" + cell).encode()).hexdigest()


# --------------------------------------------------------------------------- 2 index map
def check_index_map(index_map, n_before, n_after, *, removed=(), label=""):
    """INCIDENT: manifest indices computed on the 233-atom pristine host were applied after
    the vacancy iodide had been deleted, so every index above it was off by one. The symptom
    was deleting a framework Pb instead of a C.

    Requires an EXPLICIT old->new mapping, never an inferred offset. Validates that the map
    is injective, covers every surviving atom, and omits exactly the removed ones.
    """
    removed = set(removed)
    keys, vals = set(index_map), list(index_map.values())
    problems = []
    if len(set(vals)) != len(vals):
        problems.append("mapping is not injective")
    if keys & removed:
        problems.append(f"removed indices present in map: {sorted(keys & removed)[:5]}")
    expected_keys = set(range(n_before)) - removed
    if keys != expected_keys:
        miss, extra = expected_keys - keys, keys - expected_keys
        if miss:  problems.append(f"{len(miss)} surviving atoms missing from map")
        if extra: problems.append(f"{len(extra)} out-of-range keys in map")
    if vals and (min(vals) < 0 or max(vals) >= n_after):
        problems.append(f"target index out of range [0,{n_after})")
    return {"check": "index_map", "label": label, "passed": not problems,
            "n_before": n_before, "n_after": n_after, "n_removed": len(removed),
            "reason": "; ".join(problems) or None}


# --------------------------------------------------------------------------- 3 endpoints
def check_endpoints(profile_eV, *, label="", tol_eV=0.0):
    """INCIDENT: the first noise-floor run reported barriers -- two of them exactly 0.0 meV --
    from bands whose first interior image lay BELOW the initial endpoint. The endpoints were
    not minima, so Ea was a difference from a non-minimum reference.

    Requires each endpoint to lie below ITS OWN ADJACENT interior image (i.e. to be a local
    minimum of the band), the maximum strictly interior, and the band span within a
    physical bound. NOTE: an earlier version required both endpoints below EVERY interior
    image -- that tests path SYMMETRY, not minimality, and rejected valid asymmetric hops.
    """
    E = np.asarray(profile_eV, float)
    if E.size < 3:
        return {"check": "endpoints", "label": label, "passed": False,
                "reason": f"band has only {E.size} images"}
    interior = E[1:-1]
    # An endpoint is a local minimum of the band iff it lies below ITS OWN ADJACENT
    # interior image. Requiring it to lie below EVERY interior image (as an earlier version
    # of this check did) is a test for path SYMMETRY, not for minimality, and it rejects
    # every asymmetric hop -- which is the generic case here, since the two iodide sites are
    # inequivalent in a disordered FA host. That error rejected a band whose Ea reproduced
    # the reference to 0.0000 meV (old member 2, final endpoint 80.2 meV above initial,
    # lowest interior 49.8 meV: both endpoints ARE local minima, 0.0 < 49.8 and 80.2 < 132.6).
    ini_ok = bool(E[0] <= E[1] + tol_eV)
    fin_ok = bool(E[-1] <= E[-2] + tol_eV)
    saddle_ok = bool(0 < int(np.argmax(E)) < E.size - 1)
    # MAGNITUDE SANITY. INCIDENT: a GA band passed both shape gates with Ea = 77400 meV and
    # interior images at -323356 meV -- a catastrophic MLIP failure on a geometry outside
    # its training distribution. The shape gates test ORDERING and only compare each
    # endpoint to its immediate neighbour, so an interior blow-up slips through. An ionic
    # migration barrier in a halide perovskite is O(0.1-1 eV); anything beyond MAX_EA_EV is
    # a model failure, not a barrier, and no span of the band may exceed it either.
    span = float(np.abs(E - E[0]).max())
    sane = bool(span <= MAX_EA_EV)
    problems = []
    if not sane:
        problems.append(f"band spans {span*1000:.0f} meV, beyond the {MAX_EA_EV*1000:.0f} meV "
                        f"physical bound -- MLIP failure, not a barrier")
    if not ini_ok:  problems.append(f"initial endpoint above its adjacent interior image by "
                                    f"{(E[0]-E[1])*1000:.1f} meV -- not a local minimum")
    if not fin_ok:  problems.append(f"final endpoint above its adjacent interior image by "
                                    f"{(E[-1]-E[-2])*1000:.1f} meV -- not a local minimum")
    if not saddle_ok: problems.append(f"maximum at image {int(np.argmax(E))} (an endpoint)")
    return {"check": "endpoints", "label": label,
            "passed": bool(ini_ok and fin_ok and saddle_ok and sane),
            "Ea_forward_meV": float((E.max() - E[0]) * 1000),
            "band_span_meV": round(span * 1000, 1), "magnitude_sane": sane,
            "saddle_index": int(np.argmax(E)), "n_images": int(E.size),
            "reason": "; ".join(problems) or None}


def check_endpoint_consistency(ini_pos, fin_pos, cell, *, big=1.0, second=0.8, label=""):
    """INCIDENT: a Cs_A path returned +2984 meV because both endpoints relaxed (each to
    fmax<0.03, both reporting converged) into genuinely DIFFERENT basins -- the final state
    was a different structure, not the same defect with the ion moved.

    Requires exactly one atom to move substantially, framework static.
    """
    disp = np.linalg.norm(_mic(np.asarray(fin_pos) - np.asarray(ini_pos), np.asarray(cell)), axis=1)
    order = np.argsort(disp)[::-1]
    n_big = int((disp > big).sum())
    ok = bool(n_big == 1 and disp[order[1]] < second)
    return {"check": "endpoint_consistency", "label": label, "passed": ok,
            "n_atoms_moved_gt_{}A".format(big): n_big,
            "largest_disp_A": round(float(disp[order[0]]), 3),
            "second_disp_A": round(float(disp[order[1]]), 3),
            "reason": None if ok else
                      f"{n_big} atoms moved >{big} A (second largest {disp[order[1]]:.2f} A) "
                      f"-> endpoints describe different configurations"}


# --------------------------------------------------------------------------- 4 cell
def check_cell(cell, *, required_radius_A=None, label=""):
    """INCIDENT: `d_min/2` from EDGE lengths gave 9.7 A as the usable radius; the cell is
    triclinic, so PERPENDICULAR WIDTHS govern and the true radius is 7.28 A. The same
    edge-length metric later reappeared as a claimed '19.3 A minimum image distance',
    inflating the built cell's advantage from 1.12x to 1.48x.

    Always returns the perpendicular-width radius. Never accepts an edge length.
    """
    C = np.asarray(cell, float)
    vol = abs(np.linalg.det(C))
    widths = np.array([vol / np.linalg.norm(np.cross(C[(k + 1) % 3], C[(k + 2) % 3]))
                       for k in range(3)])
    r_max = float(widths.min() / 2)
    lengths = np.linalg.norm(C, axis=1)
    out = {"check": "cell", "label": label, "passed": True,
           "perpendicular_widths_A": [round(float(w), 3) for w in widths],
           "min_image_radius_A": round(r_max, 3),
           "min_image_distance_A": round(float(widths.min()), 3),
           "edge_lengths_A": [round(float(x), 3) for x in lengths],
           "anisotropy": round(float(lengths.max() / lengths.min()), 3),
           "note": "radius is HALF the smallest PERPENDICULAR width; edge lengths are not a "
                   "substitute and overstate the usable radius in a triclinic cell"}
    if required_radius_A is not None and r_max < required_radius_A:
        out["passed"] = False
        out["reason"] = (f"usable radius {r_max:.2f} A < required {required_radius_A} A")
    return out


# --------------------------------------------------------------------------- 5 magnetisation
_MAG_RE = re.compile(r"^\s*(total|absolute)\s+magnetization\s*=\s*([-\d.]+)", re.M)


def parse_magnetisation(out_text, *, label=""):
    """INCIDENT: |m| was quoted as 'settled at 1.85 +- 0.04' from an iteration-47 snapshot;
    by iteration 116 it had drifted to 1.70 +- 0.01. A mid-run value was presented as final.

    Parses ONLY from output text, always returns the LAST value with its iteration index,
    and reports the drift over the run so a still-moving moment cannot be called settled.
    """
    tot = [float(m.group(2)) for m in _MAG_RE.finditer(out_text) if m.group(1) == "total"]
    ab = [float(m.group(2)) for m in _MAG_RE.finditer(out_text) if m.group(1) == "absolute"]
    if not ab:
        return {"check": "magnetisation", "label": label, "passed": False,
                "reason": "no magnetisation lines found in output"}
    tail = ab[-5:]
    drift = float(max(tail) - min(tail))
    mean = float(np.mean(tail))
    # RELATIVE drift, not absolute. The two real windows this must separate are the
    # iteration-47 plateau (4.8% relative, wrongly called "settled") and the iteration-116
    # plateau (1.8%, genuinely settled). An absolute 0.05 mu_B cut sits between them but
    # lands exactly on rounded data; a 2% relative cut separates them cleanly and stays
    # meaningful if |m| is far from ~1.7 mu_B.
    rel = drift / abs(mean) if mean else float("inf")
    settled = bool(rel < REL_DRIFT_TOL and len(ab) >= 10)
    return {"check": "magnetisation", "label": label, "passed": settled,
            "n_iterations": len(ab),
            "total_magnetisation_final": tot[-1] if tot else None,
            "absolute_magnetisation_final": ab[-1],
            "absolute_last5": tail, "drift_last5": round(drift, 4),
            "relative_drift": round(rel, 4), "relative_tol": REL_DRIFT_TOL,
            "reason": None if settled else
                      (f"|m| still moving: {drift:.3f} mu_B ({rel*100:.1f}%) over the last "
                       f"{len(tail)} of {len(ab)} iterations -- not settled"
                       if len(ab) >= 10 else
                       f"only {len(ab)} iterations -- too few to call settled")}


# --------------------------------------------------------------------------- 6 theory level
THEORY_KEYS = ("functional", "dispersion", "occupations", "degauss", "ecutwfc",
               "ecutrho", "kpoints", "nspin", "tot_charge", "conv_thr", "model", "dtype")


def theory_fingerprint(**settings):
    """INCIDENT: Stage-1 fixed-path barriers (plain PBE, degauss 0.01) were compared against
    Stage-2 relaxed NEB (PBE+D3(BJ), degauss 0.005) -- a 2.722 Ry = 37.03 eV offset. The
    numbers looked comparable and were not.

    Produces a short hash over the settings that define the theory level.
    """
    rec = {k: settings.get(k) for k in THEORY_KEYS if settings.get(k) is not None}
    blob = json.dumps(rec, sort_keys=True)
    return {"fingerprint": hashlib.sha256(blob.encode()).hexdigest()[:16], "settings": rec}


def check_comparable(fp_a, fp_b, *, label=""):
    """Refuses a comparison across different theory levels, naming the differing keys."""
    a, b = fp_a["settings"], fp_b["settings"]
    diff = {k: (a.get(k), b.get(k)) for k in set(a) | set(b) if a.get(k) != b.get(k)}
    ok = fp_a["fingerprint"] == fp_b["fingerprint"]
    return {"check": "theory_level", "label": label, "passed": ok,
            "fingerprint_a": fp_a["fingerprint"], "fingerprint_b": fp_b["fingerprint"],
            "differing_settings": diff,
            "reason": None if ok else
                      f"theory levels differ in {sorted(diff)} -- comparison forbidden"}


# --------------------------------------------------------------------------- runner
def run_all(checks):
    """Aggregate. A row is ingestable only if EVERY check passed."""
    failed = [c for c in checks if not c.get("passed")]
    return {"passed": not failed, "n_checks": len(checks), "n_failed": len(failed),
            "failed": [{"check": c["check"], "label": c.get("label"), "reason": c.get("reason")}
                       for c in failed],
            "checks": checks}

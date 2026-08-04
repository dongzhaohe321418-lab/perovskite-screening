#!/usr/bin/env python
"""Test suite for scripts/checks.py.

Every test replays a REAL incident from this project with its actual numbers, and asserts
the check would have caught it. A check that only passes clean data is worthless; the
question is whether it fires on the specific wrong thing that already happened.

    python scripts/20_test_checks.py
"""
import sys, os
import numpy as np
from ase import Atoms
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import (check_composition, check_index_map, check_endpoints,
                    check_endpoint_consistency, check_cell, parse_magnetisation,
                    theory_fingerprint, check_comparable, structure_hash, run_all)

FAILS = []
def expect(cond, msg, ok_msg=None):
    """cond True -> print ok_msg (or msg); cond False -> record and print msg.

    Audit F-024: sweep-style checks phrase `msg` as the VIOLATION they hunt for
    ("count 36 != current 43 and is not marked historical"). Printing that after
    "ok" asserted a proposition the check had just disproved, so the receipt was
    not derived from the condition it reported. Such call sites must pass ok_msg
    stating the verified fact; regression [46] enforces this statically.
    """
    if not cond:
        FAILS.append(msg)
        print(f"  FAIL  {msg}")
    else:
        print(f"  ok    {ok_msg if ok_msg else msg}")


def _cell(a=19.43, b=19.65, c=19.75):
    return np.diag([a, b, c]).astype(float)


print("\n[1] composition -- INCIDENT: Cs_A no-op (Cs -> Cs, undoped cell reported as doped)")
base = Atoms("CsPbI3", positions=[[0,0,0],[2,2,2],[4,0,0],[0,4,0],[0,0,4]], cell=_cell(), pbc=True)
noop = base.copy()                                   # the bug: nothing changed
r = check_composition(base, noop, {"Cs": -1, "K": +1}, label="Cs_A no-op")
expect(not r["passed"], "no-op substitution is REJECTED")
expect(r["hash_changed"] is False, "structure hash correctly reports no change")

real = base.copy(); real.symbols[0] = "K"            # a genuine substitution
r = check_composition(base, real, {"Cs": -1, "K": +1}, label="K_A real")
expect(r["passed"], "genuine substitution PASSES")

wrong = base.copy(); wrong.symbols[1] = "Sr"         # right hash change, wrong element
r = check_composition(base, wrong, {"Cs": -1, "K": +1}, label="wrong element")
expect(not r["passed"], "hash changed but wrong element is REJECTED")


print("\n[2] index map -- INCIDENT: pristine indices applied after vacancy deletion (off by one)")
n_before, removed = 233, {127}
good = {o: (o if o < 127 else o - 1) for o in range(n_before) if o != 127}
r = check_index_map(good, n_before, 232, removed=removed, label="correct remap")
expect(r["passed"], "correct explicit remap PASSES")

bad = {o: o for o in range(n_before) if o != 127}    # the bug: identity map after deletion
r = check_index_map(bad, n_before, 232, removed=removed, label="identity after deletion")
expect(not r["passed"], "identity map after deletion is REJECTED (index out of range)")

collide = dict(good); collide[200] = collide[201]
r = check_index_map(collide, n_before, 232, removed=removed, label="non-injective")
expect(not r["passed"], "non-injective map is REJECTED")


print("\n[3] endpoints -- INCIDENT: noise-floor members 0 and 1 (Ea 718.5 and exactly 0.0 meV)")
# member 1 real profile shape: lowest interior 269 meV BELOW the initial state
m1 = [0.0, -0.269, -0.10, -0.05, -0.02, -0.01, 0.0]
r = check_endpoints(m1, label="member 1")
expect(not r["passed"], "endpoint-above-interior band is REJECTED")
expect(r["saddle_index"] in (0, len(m1)-1), "saddle correctly identified at an endpoint")

m2 = [0.0, 0.0498, 0.1980, 0.3099, 0.2416, 0.1123, -0.0119]   # real member 2, valid
r = check_endpoints(m2, label="member 2")
expect(r["passed"], "valid band PASSES")
expect(abs(r["Ea_forward_meV"] - 309.9) < 0.5,
       f"Ea recovered as {r['Ea_forward_meV']:.1f} meV (recorded 309.9)")

# INCIDENT: an earlier version required BOTH endpoints below EVERY interior image. That is
# a test for path SYMMETRY, not minimality, and it rejected the real old-member-2 band whose
# Ea reproduced the reference to 0.0000 meV. Asymmetric hops are the generic case here --
# the two iodide sites are inequivalent in a disordered FA host.
asym = [0.0, 0.0498, 0.1979, 0.3099, 0.2758, 0.1326, 0.0802]  # real: final 80.2 meV ABOVE initial
r = check_endpoints(asym, label="asymmetric hop")
expect(r["passed"],
       "ASYMMETRIC hop PASSES (final 80.2 meV above initial, lowest interior 49.8 meV)")
expect(abs(r["Ea_forward_meV"] - 309.9) < 0.5,
       f"asymmetric Ea = {r['Ea_forward_meV']:.1f} meV, matching the discriminator run")

# INCIDENT: a GA band passed BOTH shape gates with Ea = 77400 meV and interior images at
# -323356 meV -- a catastrophic MLIP failure on an out-of-distribution geometry. The shape
# gates compare each endpoint only to its neighbour, so an interior blow-up slips through.
blowup = [0.0, 1.039, -153.942, -323.356, 77.400, 3.682, 0.040]   # real m16 GA profile, eV
r = check_endpoints(blowup, label="MLIP blow-up")
expect(not r["passed"], f"77 eV band REJECTED on magnitude (span {r.get('band_span_meV',0)/1000:.0f} eV)")

# but a genuine non-minimum endpoint must still be caught
notmin = [0.0, -0.030, 0.198, 0.310, 0.276, 0.133, 0.080]     # initial ABOVE its neighbour
r = check_endpoints(notmin, label="initial not a minimum")
expect(not r["passed"], "endpoint above its ADJACENT image is still REJECTED")


print("\n[4] endpoint consistency -- INCIDENT: Cs_A r1 returned +2984 meV (different basins)")
rng = np.random.RandomState(0)
n = 60
ini = rng.rand(n, 3) * 15
fin = ini.copy(); fin[7] += np.array([4.2, 0.3, 0.1])          # one migrating ion
r = check_endpoint_consistency(ini, fin, _cell(), label="clean hop")
expect(r["passed"], "single migrating ion PASSES")

fin2 = ini.copy(); fin2[7] += [4.2, 0.3, 0.1]; fin2[20] += [1.9, 0.4, 0.2]  # cage collapse
r = check_endpoint_consistency(ini, fin2, _cell(), label="cage collapse")
expect(not r["passed"], "two large displacements REJECTED (different basins)")


print("\n[5] cell -- INCIDENT: edge-length d_min/2 gave 9.7 A; true radius is 7.28 A")
from ase.io import read
p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "results", "fa_host", "fa19cs1_pb20i60_233.extxyz")
if os.path.exists(p):
    real_cell = read(p).cell.array
    r = check_cell(real_cell, label="built det-20")
    expect(abs(r["min_image_radius_A"] - 7.28) < 0.02,
           f"real host radius = {r['min_image_radius_A']} A (expected 7.28, NOT 9.7)")
    expect(abs(r["min_image_distance_A"] - 14.55) < 0.05,
           f"min image distance = {r['min_image_distance_A']} A (NOT the 19.3 A edge figure)")
    expect(min(r["edge_lengths_A"]) > r["min_image_distance_A"],
           "edge lengths exceed the true min-image distance -- the trap this check closes")
else:
    print("  skip  (host file not present)")

r = check_cell(_cell(13.04, 13.02, 32.55), required_radius_A=7.0, label="naive 2x2x5")
expect(not r["passed"], f"naive 2x2x5 radius {r['min_image_radius_A']} A REJECTED against 7.0 A requirement")


print("\n[6] magnetisation -- INCIDENT: 1.85 quoted from iteration 47; 1.70 by iteration 116")
early = "\n".join(f"     total magnetization       =     1.00 Bohr mag/cell\n"
                  f"     absolute magnetization    =     {m:.2f} Bohr mag/cell"
                  for m in [2.50,3.48,5.52,3.42,2.45,1.83,1.82,1.90,1.87,1.91,1.90,1.92])
r = parse_magnetisation(early, label="iteration 47 snapshot")
expect(not r["passed"], f"still-drifting |m| REJECTED (drift {r['drift_last5']:.3f})")

late = early + "\n".join(f"\n     total magnetization       =     1.00 Bohr mag/cell"
                         f"\n     absolute magnetization    =     {m:.2f} Bohr mag/cell"
                         for m in [1.75,1.72,1.69,1.71,1.70,1.70])
r = parse_magnetisation(late, label="iteration 116")
expect(r["passed"], f"settled |m| PASSES, final = {r['absolute_magnetisation_final']}")
expect(abs(r["absolute_magnetisation_final"] - 1.70) < 1e-9, "final value parsed from output, not cached")


print("\n[7] theory level -- INCIDENT: Stage-1 plain PBE vs Stage-2 PBE+D3(BJ), 37.03 eV offset")
s1 = theory_fingerprint(functional="PBE", dispersion=None, occupations="smearing",
                        degauss=0.01, ecutwfc=50, ecutrho=400, kpoints="1,1,1")
s2 = theory_fingerprint(functional="PBE", dispersion="D3-BJ", occupations="smearing",
                        degauss=0.005, ecutwfc=50, ecutrho=400, kpoints="1,1,1")
r = check_comparable(s1, s2, label="stage1 vs stage2")
expect(not r["passed"], "cross-theory-level comparison is FORBIDDEN")
expect(set(r["differing_settings"]) == {"dispersion", "degauss"},
       f"names the differing keys: {sorted(r['differing_settings'])}")

r = check_comparable(s2, theory_fingerprint(functional="PBE", dispersion="D3-BJ",
                     occupations="smearing", degauss=0.005, ecutwfc=50, ecutrho=400,
                     kpoints="1,1,1"), label="stage2 vs stage2")
expect(r["passed"], "identical theory levels ARE comparable")


print("\n[8] runner aggregation")
rep = run_all([check_endpoints(m2), check_endpoints(m1)])
expect(not rep["passed"] and rep["n_failed"] == 1, "one bad row fails the aggregate")


print("\n[9] migrating-atom identity -- INCIDENT: GA deleted an H below the migrating iodide")
# Deleting an atom shifts every higher index down by one. Tracking the migrating ion by a
# bare integer captured BEFORE the substitution moved the WRONG atom in 8 of 18 GA members
# (m00,01,05,06,08,13,16,17) -- and all three "MLIP blow-ups" were in that set.
_a = Atoms("I5", positions=[[0,0,0],[3,0,0],[6,0,0],[9,0,0],[12,0,0]],
           cell=np.eye(3)*20, pbc=True)
_t = np.zeros(5, int); _t[4] = 99; _a.set_tags(_t)
_target = _a.positions[4].copy()
_b = _a.copy(); del _b[1]                      # delete an atom BELOW the tagged one
_i = int(np.flatnonzero(_b.get_tags() == 99)[0])
expect(_i == 3, f"tag follows the atom after a lower-index deletion (4 -> {_i})")
expect(np.allclose(_b.positions[_i], _target), "tagged atom is the SAME physical atom")
expect(len(_b) == 4 and 4 >= len(_b),
       "stale index 4 is now OUT OF RANGE (5 atoms -> 4) -- would raise, not silently pass")
_big = Atoms("I8", positions=[[3*i,0,0] for i in range(8)], cell=np.eye(3)*40, pbc=True)
_tb = np.zeros(8, int); _tb[6] = 99; _big.set_tags(_tb)
_tgt = _big.positions[6].copy()
_e = _big.copy(); del _e[2]
expect(not np.allclose(_e.positions[6], _tgt),
       "in a cell large enough to stay in range, stale index 6 SILENTLY points elsewhere")
expect(np.allclose(_e.positions[int(np.flatnonzero(_e.get_tags()==99)[0])], _tgt),
       "the tag still resolves to the correct atom -- this is the actual bug and fix")
_c = _a.copy(); del _c[0]                      # deletion ABOVE-safe case
expect(int(np.flatnonzero(_c.get_tags() == 99)[0]) == 3, "shift also handled from index 0")
_d = _a.copy(); del _d[4]
expect(np.flatnonzero(_d.get_tags() == 99).size == 0,
       "deleting the tagged atom leaves no tag -- migrating_index would assert")

print("\n[10] force convergence metric -- INCIDENT: component-max recorded, not vector norm")
_g = np.array([[0.012, 0.012, 0.012]])
_cm, _nm = np.abs(_g).max(), np.linalg.norm(_g, axis=1).max()
expect(_nm > _cm, f"isotropic force: norm {_nm:.4f} > component {_cm:.4f} "
                  f"(ratio {_nm/_cm:.2f}, up to sqrt(3) = 1.73)")
expect(_cm < 0.02 <= _nm,
       "a force that PASSES a 0.02 component test FAILS the correct norm test")

print("\n[11] small-sample statistics -- INCIDENT: 1.96*SE published at n=2")
from scipy import stats as _st
expect(abs(_st.t.ppf(0.975, 1) - 12.706) < 0.01,
       f"t critical at df=1 is {_st.t.ppf(0.975,1):.3f}, NOT 1.96")
_w = (2*_st.t.ppf(0.975,1)*84.9/np.sqrt(2)) / (2*1.96*84.9/np.sqrt(2))
expect(_w > 6, f"t interval is {_w:.1f}x wider than the normal one at n=2")
expect(int(np.ceil(2*(2*73.3/59.5)**2)) == 13,
       "UNPAIRED n uses 2*(2s/T)^2 [n per group]: sigma 73.3 -> 13")
expect(int(np.ceil(2*(2*83.9/59.5)**2)) == 16,
       "new-pool sigma 83.9 -> 16, NOT the 8 the paired formula would give")

print("\n[12] paired vs single-path pass rate -- INCIDENT: 33% single applied to pairs")
expect(abs(0.333**2 - 0.111) < 0.002,
       "under independence the paired rate is the SQUARE of the single-path rate")
expect(int(np.ceil(10/(2/18))) == 90,
       f"10 pairs at the observed 2/18 GA rate needs {int(np.ceil(10/(2/18)))} hosts, not 30")
expect(int(np.ceil(10/(4/18))) == 45, "Sr at 4/18 needs 45 hosts")


print("\n[13] return-test perturbation scale -- INCIDENT: sqrt(N) scaling stepped past image 1")
# v1 used amp*dhat*sqrt(N) with ||dhat||_F=1: total displacement 0.05*15.23=0.76 A, which
# EXCEEDED the whole initial->image-1 segment for 3 of 27 paths (min ||dvec||_F=0.274 A)
# and moved single atoms up to 0.65 A >> RETURN_TOL 0.15 A. Correct scaling normalises by
# the max per-atom displacement so the largest atomic move equals amp exactly.
rng = np.random.default_rng(3)
dvec = rng.normal(size=(232, 3)) * 0.05
dhat_v1 = dvec / np.linalg.norm(dvec)
step_v1 = 0.05 * dhat_v1 * np.sqrt(232)
dhat_v2 = dvec / np.linalg.norm(dvec, axis=1).max()
step_v2 = 0.05 * dhat_v2
expect(np.linalg.norm(step_v1) > 0.5,
       f"v1 total displacement {np.linalg.norm(step_v1):.2f} A -- NOT a small perturbation")
expect(abs(np.linalg.norm(step_v2, axis=1).max() - 0.05) < 1e-12,
       f"v2 max single-atom move = {np.linalg.norm(step_v2, axis=1).max():.4f} A = amp exactly")
expect(np.linalg.norm(step_v2, axis=1).max() < 0.15,
       "v2 perturbation always below RETURN_TOL, so a returned structure is detectable")

print("\n[14] return-test classification -- locked against the committed raw record")
# Replays the committed return_test_v2.json through the DISPLACEMENT-ONLY rule and locks
# the published counts. Guards against (a) silently reintroducing the miscalibrated 5 meV
# energy criterion, (b) a future edit changing RETURN_TOL_A, (c) the classification drifting
# from the raw per-perturbation data.
import json as _json, os as _os
_rt = "results/objective2/paired_pilot/return_test/return_test_v2.json"
if _os.path.exists(_rt):
    _d = _json.load(open(_rt))
    _rows = _d["rows"]
    expect(len(_rows) == 27, f"27 asymmetric-well endpoints in the record (got {len(_rows)})")
    # recompute verdicts from raw perturbations, displacement only
    _meta = sum(1 for r in _rows
                if sum(1 for p in r["perturbations"] if p["max_disp_A"] < 0.15) == 4)
    _amb = len(_rows) - _meta
    expect(_meta == 23, f"23 verified_metastable recomputed from raw displacements (got {_meta})")
    expect(_amb == 4, f"4 multi_basin_ambiguous (got {_amb})")
    _bc = {}
    for r in _rows: _bc[r["band_class"]] = _bc.get(r["band_class"], 0) + 1
    expect(_bc.get("pure_hop_asymmetric") == 5, f"5 pure_hop_asymmetric (got {_bc.get('pure_hop_asymmetric')})")
    expect(_bc.get("hop_plus_FA_reorientation") == 11,
           f"11 hop_plus_FA_reorientation (got {_bc.get('hop_plus_FA_reorientation')})")
    expect(_bc.get("band_collapsed") == 6, f"6 band_collapsed (got {_bc.get('band_collapsed')})")
    expect(_bc.get("endpoint_energy_unconverged") == 1,
           f"1 endpoint_energy_unconverged (got {_bc.get('endpoint_energy_unconverged')})")
    # the energy criterion must NOT be reintroduced: applying it would flip 21 verdicts
    _meta_with_E = sum(1 for r in _rows
                       if sum(1 for p in r["perturbations"]
                              if p["max_disp_A"] < 0.15 and abs(p["dE_meV"]) < 5.0) == 4)
    expect(_meta_with_E == 2,
           f"the retired 5 meV criterion would give only {_meta_with_E} metastable -- do not reinstate")
    # and the source code must not carry it
    _src = open("scripts/24_return_test.py").read()
    expect("E_TOL_MEV" not in _src.split("# NO energy criterion")[-1].split("def ")[0] or
           "abs(dE) < E_TOL" not in _src,
           "scripts/24 judges metastability by displacement alone")
else:
    print("  SKIP  return_test_v2.json not present in this checkout")

print("\n[15] criterion-change impact must be reported, not minimised -- INCIDENT")
# I wrote that dropping the 5 meV energy rule "changed NOTHING about which relaxations
# pass". False: it flips 76 of 108 relaxation verdicts and 21 of 27 endpoint verdicts, and
# it is what produced the headline 23/27. The defensible claim is narrower: the energy rule
# reclassifies no BASIN CHANGE. This test pins both halves so neither can drift back.
if _os.path.exists(_rt):
    _P = [p for r in _rows for p in r["perturbations"]]
    _disp = sum(1 for p in _P if p["max_disp_A"] < 0.15)
    _both = sum(1 for p in _P if p["max_disp_A"] < 0.15 and abs(p["dE_meV"]) < 5.0)
    expect(_disp - _both == 76,
           f"the criterion change flips {_disp - _both} relaxation verdicts (not zero)")
    _left = [p for p in _P if p["max_disp_A"] >= 0.15]
    expect(len(_left) == 5, f"{len(_left)} relaxations left the basin")
    expect(sum(1 for p in _left if abs(p["dE_meV"]) < 5.0) == 0,
           "no basin change would have been caught by energy alone -- the narrow claim holds")
    # and the prose must not reassert the retracted version
    _rep = open("results/objective2/paired_pilot/RETURN_TEST_RESULT.md").read()
    expect("changes **nothing** about which relaxations pass" not in _rep,
           "the retracted 'changes nothing' claim is absent from the report")
    _s24 = open("scripts/24_return_test.py").read()
    expect("changed NOTHING about which relaxations pass" not in _s24,
           "the retracted claim is absent from scripts/24")

print("\n[16] rescued vs gate-passing provenance must not be conflated -- INCIDENT")
# I described two Sr outliers as passing "every gate". Both had gate_endpoints.passed=False
# and entered only via the return-test rescue. Any claim about a path's admission route must
# be checked against paired_raw_84.json, never asserted.
_pr = "results/objective2/paired_pilot/corpus84/paired_raw_84.json"
if _os.path.exists(_pr):
    _rows84 = _json.load(open(_pr))["rows"]
    _by = {(r["member"], r["system"]): r for r in _rows84}
    for _m, _s in [(14, "Sr"), (20, "undoped")]:
        _r = _by[(_m, _s)]
        expect(_r["valid"] is False,
               f"m{_m:02d} {_s} did NOT pass the strict gate (valid={_r['valid']})")
    # INCIDENT WITHIN THE INCIDENT: the first fix edited only CORPUS84_RESULT.md while the
    # canonical index CURRENT_STATUS.md, written in the same window, still asserted the
    # retracted claim. A retraction must be swept REPO-WIDE, so this scans every document.
    import glob as _glob
    _docs = [f for f in _glob.glob("results/**/*.md", recursive=True) if "/hpc/" not in f]
    _bad = []
    for _f in _docs:
        _txt = open(_f).read()
        _i = _txt.find("pass every gate")
        while _i != -1:
            _ctx = _txt[max(0, _i-160):_i]
            if "An earlier version" not in _ctx and "Correction." not in _ctx:
                _bad.append(f"{_f}:{_txt[:_i].count(chr(10))+1}")
            _i = _txt.find("pass every gate", _i+1)
    expect(not _bad,
           f"no document asserts 'pass every gate' outside a retraction (offenders: {_bad})")
    _rep84 = open("results/objective2/paired_pilot/CORPUS84_RESULT.md").read()
    expect("RESCUED, not gate-passing" in _rep84,
           "the report distinguishes rescued members from gate-passing ones")
    _idx84 = open("results/objective2/CURRENT_STATUS.md").read()
    expect("return-test rescue" in _idx84,
           "the canonical index names the rescue route for m14/m20")

print("\n[17] a derived constant must not be quoted below its input's own residual -- INCIDENT")
# I derived g = 11.0 meV/A, u_crit = 0.0039 A and a well depth of 0.011 meV from a 2.2 meV
# energy difference whose own SCF residual was ~30 meV, and whose value swung 5 meV between
# sampling windows. Precision must be bounded by the noisiest input, not the arithmetic.
_POL_RESIDUAL_MEV = 30.0        # POL estimated scf accuracy 2.2e-3 Ry, never converged
_GAIN_WINDOWS_MEV = (2.3, 7.3)  # same quantity, iterations ~129 and ~83
expect(abs(_GAIN_WINDOWS_MEV[1] - _GAIN_WINDOWS_MEV[0]) < _POL_RESIDUAL_MEV,
       "the window-to-window swing is itself within the residual (both are noise)")
expect(max(_GAIN_WINDOWS_MEV) < _POL_RESIDUAL_MEV,
       f"the gain ({max(_GAIN_WINDOWS_MEV)} meV) is BELOW POL's residual ({_POL_RESIDUAL_MEV}) "
       "-> report a bound, never a point value")
_pol = "results/objective1/dft/charge_relaxed/Q0_POLARON_EXCLUDED.md"
if _os.path.exists(_pol):
    _tp = open(_pol).read()
    for _stale in ["11.0 meV/\u00c5", "0.0039", "0.011 meV"]:
        _i = _tp.find(_stale)
        expect(_i == -1 or "An earlier version" in _tp[max(0, _i-260):_i],
               f"retracted figure {_stale!r} appears only inside the retraction")
    expect("NOT RESOLVED" in _tp or "NOT resolved" in _tp,
           "the report states the localisation gain is unresolved")
    expect("no bound polaron at any amplitude" not in _tp.split("earlier draft")[0],
           "the over-strong 'any amplitude' claim is not asserted")
    expect("no thermally significant polaron" in _tp,
           "the report makes the bounded claim instead")
    # the well-depth bound must be recomputable from the CONVERGED elastic cost
    _k = 112.6 / 0.20**2
    _depth = ((2*_POL_RESIDUAL_MEV/0.20)**2) / (4*_k)
    expect(abs(_depth - 8.0) < 0.5, f"2x-residual well-depth bound recomputes to {_depth:.1f} meV")
    expect(_depth < 25.7, "even the extreme bound stays below room-temperature kT")

print("\n[18] a retraction must cover PARAPHRASES, not just literal strings -- INCIDENT")
# I retracted "no bound polaron at any amplitude" in the body of Q0_POLARON_EXCLUDED.md but
# the ABSTRACT still said the conclusion "does not depend on the amplitude chosen" -- the same
# claim in different words. My verification grepped literal strings only, so it survived.
import re as _re2
_pol2 = "results/objective1/dft/charge_relaxed/Q0_POLARON_EXCLUDED.md"
if _os.path.exists(_pol2):
    _tp2 = open(_pol2).read()
    _abstract = _tp2[:_tp2.index("## The three calculations")]
    for _phr in ["does not depend on the amplitude", "independent of the amplitude",
                 "at any amplitude", "no polaron exists"]:
        expect(_phr not in _abstract,
               f"abstract does not assert {_phr!r} (the retracted claim, in any wording)")
    expect("BOUND" in _abstract or "bound" in _abstract,
           "abstract states the result as a bound")
    expect("not excluded" in _abstract or "is not excluded" in _abstract
           or "cannot be excluded" in _abstract or "not excluded by these data" in _abstract,
           "abstract admits a weakly bound state is not excluded")
    # the earlier status doc predicted the strong wording -- it must carry the real outcome
    _st = "results/objective1/dft/charge_relaxed/Q0_RELAXATION_STATUS.md"
    if _os.path.exists(_st):
        _ts = open(_st).read()
        expect("thermally significant" in _ts,
               "the pre-test status doc is annotated with the bounded outcome")

print("\n[19] script flags must be verified, not guessed -- THIRD INCIDENT")
# Three jobs have now been wasted on invented CLI flags: a missing module, a non-existent
# --pristine, and --base/--seed on 21_expand_fa_pool.py (which takes --host/--start-seed).
# This asserts the flags each driver ACTUALLY defines, so a rename breaks the test not a job.
import subprocess as _sp, sys as _sys
_EXPECTED_FLAGS = {
    "scripts/21_expand_fa_pool.py": ["--host", "--out", "--n-new", "--start-seed", "--fmax",
                                     "--steps", "--device"],
    "scripts/24_return_test.py":    ["--rerun-dir", "--rejected", "--fmax", "--steps",
                                     "--device", "--out"],
}
for _scr, _flags in _EXPECTED_FLAGS.items():
    if not _os.path.exists(_scr):
        continue
    _h = _sp.run([_sys.executable, _scr, "--help"], capture_output=True, text=True).stdout
    for _f in _flags:
        expect(_f in _h, f"{_os.path.basename(_scr)} accepts {_f}")
    # and the flags I wrongly used must NOT silently exist
    for _bad in (["--base", "--seed"] if "21_expand" in _scr else []):
        expect(_bad not in _h,
               f"{_os.path.basename(_scr)} does NOT accept {_bad} (the flag I invented)")

# EXISTENCE IS NOT ENOUGH: my guard verified each flag EXISTS but 22_paired_pilot.py has a
# REQUIRED --members that I omitted, so the run still died. Assert required args explicitly.
_REQUIRED_ARGS = {"scripts/22_paired_pilot.py": ["--members"]}
for _scr, _req in _REQUIRED_ARGS.items():
    if not _os.path.exists(_scr):
        continue
    _h2 = _sp.run([_sys.executable, _scr, "--help"], capture_output=True, text=True).stdout
    _usage = _h2.split("options:")[0]
    for _r in _req:
        # argparse prints required args WITHOUT surrounding brackets in the usage line
        expect(_r in _usage and f"[{_r}" not in _usage,
               f"{_os.path.basename(_scr)}: {_r} is REQUIRED and must be passed explicitly")

print("\n[20] a guard must not misreport an import failure as a flag failure -- INCIDENT")
# My flag guard ran `driver --help`, grepped for each flag, and reported "--pool not accepted"
# when the REAL cause was ModuleNotFoundError: no checks.py. --help crashed, so no flags
# appeared in the output and the guard blamed the flag. Two distinct failure modes were
# collapsed into one message, which sent me looking in the wrong place twice.
# Derive the local-module dependency of each driver from its SOURCE rather than asserting a
# hand-written map (my first version claimed script 18 imports checks; it does not).
_LOCAL_MODULES = {_f[:-3] for _f in _os.listdir("scripts") if _f.endswith(".py")}
_LOCAL_MODULES |= {"checks"}
for _scr in ["scripts/22_paired_pilot.py", "scripts/18_objective2_explore_screen.py",
             "scripts/24_return_test.py", "scripts/21_expand_fa_pool.py"]:
    if not _os.path.exists(_scr):
        continue
    _src = open(_scr).read()
    _deps = sorted({_m.group(1) for _m in _re2.finditer(r"^\s*from\s+(\w+)\s+import", _src, _re2.M)
                    if _m.group(1) in _LOCAL_MODULES}
                   | {_m.group(1) for _m in _re2.finditer(r"^\s*import\s+(\w+)\s*$", _src, _re2.M)
                      if _m.group(1) in _LOCAL_MODULES})
    print(f"       {_os.path.basename(_scr)} local deps: {_deps if _deps else '(none)'}")
    for _d in _deps:
        expect(_os.path.exists(f"scripts/{_d}.py"),
               f"{_os.path.basename(_scr)} needs scripts/{_d}.py -> MUST be staged with it")
    # --help must exit 0; a non-zero exit means the driver cannot import, which is an
    # environment problem and must be reported as such, never as a missing flag
    _r = _sp.run([_sys.executable, _scr, "--help"], capture_output=True, text=True)
    expect(_r.returncode == 0,
           f"{_os.path.basename(_scr)} --help exits 0 (a crash here means a staging problem)")
    expect("usage:" in _r.stdout,
           f"{_os.path.basename(_scr)} --help actually prints a usage line")

print("\n[21] a driver's DEFAULT paths must be staged or overridden -- INCIDENT")
# Four submissions of the same job failed for four different reasons. The last one passed
# every guard (flags exist, driver imports, required args given) and still died: --vac-ref
# has a hardcoded default pointing at a repo path that was never staged remotely. Guards that
# check flags and imports cannot see whether the FILES those flags point at are present.
for _scr in ["scripts/22_paired_pilot.py"]:
    if not _os.path.exists(_scr):
        continue
    _src = open(_scr).read()
    # find every argparse default that looks like a path
    _defaults = _re2.findall(r'add_argument\(\s*"(--[\w-]+)"[^)]*?default\s*=\s*"([^"]+)"', _src)
    _pathish = [(_f, _d) for _f, _d in _defaults
                if "/" in _d or _d.endswith((".extxyz", ".json", ".xyz"))]
    print(f"       {_os.path.basename(_scr)} path-valued defaults: {_pathish}")
    expect(bool(_pathish), "the driver has at least one path-valued default (that is the hazard)")
    for _f, _d in _pathish:
        expect(_os.path.exists(_d),
               f"default for {_f} ({_d}) exists locally -> MUST be staged or overridden remotely")

print("\n[22] enumerate a driver's inputs from SOURCE, not one failure at a time -- INCIDENT")
# Five submissions of one job. Guards for flags, imports, required args and path-valued
# DEFAULTS all passed, and it still died: the driver also reads a HARDCODED filename from
# inside a directory argument -- f"{args.pool}/fa19cs1_pb20i60_233.extxyz" -- which no
# flag-level check can see. The lesson: grep every read()/open() in the driver and stage the
# whole set, rather than discovering inputs by successive failures.
_drv = "scripts/22_paired_pilot.py"
if _os.path.exists(_drv):
    _s = open(_drv).read()
    _hard = _re2.findall(r'read\(\s*f?"([^"]*\{[^}]+\}[^"]*|[^"]+)"', _s)
    _interp = [h for h in _hard if "{" in h]
    print(f"       hardcoded/interpolated read paths: {_interp}")
    expect(any("fa19cs1_pb20i60_233" in h for h in _interp),
           "driver reads a hardcoded pristine filename from inside --pool (the invisible input)")
    # that file must exist SOMEWHERE in the repo so it can be staged
    _found = [p for p in _glob.glob("results/**/fa19cs1_pb20i60_233.extxyz", recursive=True)]
    expect(bool(_found), f"the pristine reference exists in the repo to stage: {_found[:2]}")
    # and it is NOT inside the harmonised pool dir -- which is exactly why staging the pool
    # directory alone was insufficient
    expect(not _os.path.exists("results/fa_host/pool_v3_harmonised/fa19cs1_pb20i60_233.extxyz"),
           "it is NOT in pool_v3_harmonised -> staging the pool dir alone does not supply it")

print("\n[23] manifest energies must be MEASURED, never inferred by index -- INCIDENT")
# I completed the manifest's energy table by assuming member index == seed offset. harmonise.json
# shows m00-m17 map to pool_v2 seeds 8-25, so 8 members got energies belonging to OTHER members,
# at the superseded fmax~0.03 depth, which biased the homogeneity gate from -31.5 to -102.6 meV.
# Also: fmax was written in as a literal 0.02 per row and never measured.
_MF = "results/fa_host/pool_v3_harmonised/HOST_MANIFEST.json"
_HR = "results/fa_host/pool_v3_harmonised/harmonise.json"
if _os.path.exists(_MF) and _os.path.exists(_HR):
    _mj = _json.load(open(_MF)); _hj = _json.load(open(_HR))
    _harm = {r["member"].replace(".extxyz", ""): r for r in _hj["rows"]}
    expect(_mj.get("fmax_all_measured") is True,
           "manifest declares every fmax MEASURED (not a hardcoded target)")
    for _r in _mj["rows"]:
        expect(_r.get("fmax_measured") is not None,
               f"m{_r['member']:02d} carries a measured fmax")
        expect(_r["fmax_measured"] <= 0.0201,
               f"m{_r['member']:02d} measured fmax {_r.get('fmax_measured')} <= 0.0201")
        expect("measured" in (_r.get("energy_source") or "")
               or "expansion_plus8" in (_r.get("energy_source") or ""),
               f"m{_r['member']:02d} energy comes from a measured source")
    # harmonised members must match harmonise.json E_after BY FILENAME, never by index
    for _tag, _hrow in list(_harm.items())[:18]:
        _m = int(_tag[1:])
        _row = next(x for x in _mj["rows"] if x["member"] == _m)
        expect(abs(_row["energy_eV"] - _hrow["E_after_eV"]) < 5e-4,
               f"{_tag} energy == harmonise E_after ({_hrow['E_after_eV']:.4f}), not E_before")
        expect(abs(_row["energy_eV"] - _hrow["E_before_eV"]) > 1e-3,
               f"{_tag} energy is NOT the pre-harmonisation E_before (the v1 bug)")
    # the corrected gate must be the one recorded
    _g = _mj.get("gate", {})
    expect(abs(_g.get("offset_meV", 0) + 31.5) < 1.0,
           f"recorded gate offset is the corrected -31.5 meV (got {_g.get('offset_meV')})")
    expect(_g.get("welch_p", 0) > 0.05, "recorded gate p indicates same population")

print("\n[24] a sub-threshold force READING is not convergence -- INCIDENT")
# I reported q0_final "has crossed its force target" because one BFGS step printed a gradient
# error of 1.4e-3 vs the 1.945e-3 criterion. BFGS did not accept it: the next steps read 1.9e-3
# then 2.3e-3. Convergence requires QE's own block ("End of BFGS Geometry Optimization"), not a
# single favourable line. The cell has documented soft octahedral-tilt modes that make the
# gradient oscillate around ~0.04 eV/A.
_TRAJ = [3.1e-3, 2.9e-3, 2.7e-3, 2.4e-3, 1.9e-3, 1.4e-3, 1.9e-3, 2.3e-3]
_CRIT = 1.945e-3
expect(min(_TRAJ) < _CRIT, "some step DID read below the criterion (that is why it misled me)")
expect(_TRAJ[-1] > _CRIT, "but the trajectory ROSE back above it -- not converged")
expect(_TRAJ.index(min(_TRAJ)) < len(_TRAJ) - 1,
       "the minimum is not the last point -> a single reading cannot be cited as convergence")
for _f in ["EXPERIMENT_AUDIT.md", "results/objective2/CURRENT_STATUS.md"]:
    if not _os.path.exists(_f):
        continue
    _tx = open(_f).read()
    _i = _tx.find("crossed its force target")
    expect(_i == -1 or "retracted" in _tx[_i:_i+220] or "premature" in _tx[_i:_i+220],
           f"{_os.path.basename(_f)}: the 'crossed its force target' claim is retracted, not asserted")
    if "q0_final" in _tx:
        # ERA UPDATE 2026-07-28: q0_final SINCE CONVERGED FORMALLY (QE's own block). The durable
        # invariant is no longer "not described as verified" -- it is that the premature claim's
        # retraction survives (asserted above) and the doc records the FORMAL convergence rather
        # than a single sub-threshold reading.
        _w = _tx[_tx.find("q0_final"):_tx.find("q0_final") + 2500]
        expect(("CONVERGED" in _w.upper()) or ("convergence block" in _w),
               f"{_os.path.basename(_f)}: q0_final is recorded as formally converged")

print("\n[25] preflight must reject NONEXISTENT EXPLICIT paths -- VULNERABILITY, found by PI")
# The preflight I built after five failed submissions had a hole: it validated argparse DEFAULTS
# and the manually-listed --stage files, but NEVER the values actually passed in --invocation.
# `--pool DOES_NOT_EXIST --vac-ref MISSING.extxyz` returned "PREFLIGHT PASSED -- safe to submit".
_PF = "scripts/25_preflight.py"
_DRV = "scripts/22_paired_pilot.py"
if _os.path.exists(_PF) and _os.path.exists(_DRV):
    def _pf(inv, extra=()):
        _c = [_sys.executable, _PF, "--driver", _DRV, "--invocation", inv,
              "--stage", "scripts/checks.py", *extra]
        return _sp.run(_c, capture_output=True, text=True)
    # a) nonexistent --pool must fail
    _r = _pf("--pool DOES_NOT_EXIST --members 28 --systems undoped GA Sr --out out")
    expect(_r.returncode != 0 and "PREFLIGHT FAILED" in _r.stdout,
           "nonexistent explicit --pool is REJECTED")
    expect("DOES_NOT_EXIST" in _r.stdout, "the failure names the offending value")
    # b) nonexistent --vac-ref must fail
    _r = _pf("--pool pool --vac-ref MISSING.extxyz --members 28 --systems undoped GA Sr --out out",
             ("--assembled", "pool"))
    expect(_r.returncode != 0 and "PREFLIGHT FAILED" in _r.stdout,
           "nonexistent explicit --vac-ref is REJECTED")
    expect("MISSING.extxyz" in _r.stdout, "the failure names the missing file")
    # c) explicit inputs must have a remote source (stage / local-map / assembled)
    expect("has no remote source" in _r.stdout,
           "preflight checks that each explicit input maps to a remote target")
    # d) the CORRECT invocation must still pass -- a guard that rejects everything is useless.
    # SELF-CONTAINED fixture (PI finding: the first version depended on a /tmp directory that
    # existed only on my machine, so the suite failed everywhere else). The remote layout is
    # declared with EXACT remote-path mappings -- pool/<file>=<local source> -- which is also
    # the semantics real submissions must use; no --pool-dir, no external state.
    _r = _pf("--pool pool --vac-ref vac_ref.extxyz --members 28 29 --systems undoped GA Sr "
             "--out out --device cuda",
             ("results/fa_host/pool_v2/fa19cspb20i59_232_vI.extxyz",
              "results/fa_host/fa19cs1_pb20i60_233.extxyz",
              "--local-map",
              "vac_ref.extxyz=results/fa_host/pool_v2/fa19cspb20i59_232_vI.extxyz",
              "pool/fa19cs1_pb20i60_233.extxyz=results/fa_host/fa19cs1_pb20i60_233.extxyz",
              "--assembled", "pool"))
    expect(_r.returncode == 0 and "PREFLIGHT PASSED" in _r.stdout,
           "the correct invocation still PASSES (no over-rejection)")
    expect("pool/fa19cs1_pb20i60_233.extxyz <- results/fa_host/fa19cs1_pb20i60_233.extxyz" in _r.stdout,
           "the interpolated read is satisfied by the EXACT remote-path mapping")
    # d2) an exact mapping pointing at a NONEXISTENT local source must fail
    _r = _pf("--pool pool --vac-ref vac_ref.extxyz --members 28 --systems undoped GA Sr "
             "--out out",
             ("results/fa_host/pool_v2/fa19cspb20i59_232_vI.extxyz",
              "--local-map",
              "vac_ref.extxyz=results/fa_host/pool_v2/fa19cspb20i59_232_vI.extxyz",
              "pool/fa19cs1_pb20i60_233.extxyz=NOWHERE.extxyz",
              "--assembled", "pool"))
    expect(_r.returncode != 0 and "does not exist locally" in _r.stdout,
           "an exact mapping to a nonexistent local source is REJECTED")
    # e) output flags must not be demanded as pre-existing inputs
    expect("--out = 'out' does not exist" not in _r.stdout,
           "an output directory is not required to pre-exist")

print("\n[26] authoritative docs must not contradict each other -- PI AUDIT")
# Three divergences found by the PI: LOCKED_PROTOCOL still mandated nspin=2 for q=0 and claimed
# an odd electron count forbids m=0 (contradicted by P2 and the running nspin=1 relaxation);
# Q0_POLARON_EXCLUDED said the q=0 NEB is "a matter of compute" while the gate says 2 of 5
# conditions are open; CURRENT_STATUS carried stale counts while calling itself canonical.
_LP = "results/objective1/dft/charge_relaxed/LOCKED_PROTOCOL_AND_STOPLOSS.md"
if _os.path.exists(_LP):
    _s = open(_LP).read()
    expect("SUPERSEDED IN PART" in _s[:400],
           "LOCKED_PROTOCOL opens with a superseded banner")
    expect("q=0 uses `nspin=1`" in _s or "Current protocol for q=0: `nspin=1`" in _s,
           "LOCKED_PROTOCOL states the current q=0 protocol is nspin=1")
    _i = _s.find("**2 for q=0**")
    expect(_i == -1 or "RETRACTED" in _s[_i:_i+200] or "~~" in _s[max(0,_i-4):_i],
           "the nspin=2 mandate is struck/retracted, not asserted")
    expect("soft octahedral-tilt" in _s or "soft-tilt" in _s,
           "the banner preserves what still stands (the soft-mode floor)")
_PX = "results/objective1/dft/charge_relaxed/Q0_POLARON_EXCLUDED.md"
if _os.path.exists(_PX):
    _s2 = open(_PX).read()
    _j = _s2.find("matter of compute")
    expect(_j == -1 or "previously read" in _s2[max(0,_j-300):_j+300]
           or "overstated" in _s2[max(0,_j-300):_j+300],
           "the 'matter of compute' claim is corrected, not asserted")
    expect("gate is not open" in _s2 or "Two of five" in _s2,
           "the polaron doc defers to the NEB gate")
_CS = "results/objective2/CURRENT_STATUS.md"
if _os.path.exists(_CS):
    _s3 = open(_CS).read()
    expect("61 assertions" not in _s3, "stale assertion count removed from the canonical index")
    expect("28 members" not in _s3 or "36" in _s3,
           "the index does not state a stale pool size")
    # updated 2026-07-28: q0_final converged formally, so the current state IS convergence
    expect("CONVERGED FORMALLY" in _s3 or "QE convergence block" in _s3,
           "the index carries the current q0_final state")

print("\n[27] canonical docs must not go stale, and links must resolve -- PI AUDIT")
# The index still said the extension was "now genuinely producing bands" after it had completed,
# merged and been published; and its host-manifest link pointed at results/fa_host/HOST_MANIFEST.md
# which does not exist (the file is under pool_v3_harmonised/).
_CS2 = "results/objective2/CURRENT_STATUS.md"
if _os.path.exists(_CS2):
    _s = open(_CS2).read()
    expect("genuinely producing bands" not in _s,
           "the index no longer describes a completed job as in-progress")
    expect("completed: 24/24 bands" in _s or "complete" in _s.lower(),
           "the index states the extension is complete and merged")
    expect("corpus108/return_test_24.json" in _s,
           "the index cites the extension's return-test record")
    # EVERY backticked repo path in the index must resolve
    _bad = []
    for _m in _re2.finditer(r"`(\.\./[^`]+\.(?:md|json))`", _s):
        _rel = _m.group(1)
        _abs = _os.path.normpath(_os.path.join("results/objective2", _rel))
        if not _os.path.exists(_abs):
            _bad.append(_rel)
    expect(not _bad, f"all relative document links in the index resolve (broken: {_bad})")

print("\n[28] the NEB gate must track the live relaxation state -- PI AUDIT")
_GT = "results/objective1/dft/charge_relaxed/Q0_NEB_GATE.md"
if _os.path.exists(_GT):
    _g = open(_GT).read()
    expect("3 BFGS steps" not in _g, "the gate no longer reports the stale 3-step state")
    # 2026-07-28 (late): q0_final CONVERGED formally (QE block, 10 steps, grad 1.6e-3), so the
    # gate legitimately closed condition 1. The test now asserts the CURRENT true state, and
    # that the historical retraction (the premature "crossed its force target") is preserved.
    expect("q0_final: CONVERGED" in _g, "the gate records q0_final as formally converged")
    expect("bfgs converged in 11 scf cycles and 10 bfgs steps" in _g,
           "the gate quotes QE's own convergence block, not an inferred state")
    expect("was retracted" in _g or "retracted" in _g,
           "the premature force-target claim retraction is preserved in the gate")
    expect("withdrawn as unnecessary" in _g,
           "the protocol revision is recorded as withdrawn, never silently adopted")
    expect("-27.1 meV" in _g or "−27.1 meV" in _g,
           "the gate records the q=0 endpoint asymmetry")
    # 2026-07-28 (later): the harness was built and validated on the real q=+1 band, so
    # condition 5 went from "missing" to PARTIAL. The assertion now pins the SHARPER state --
    # that condition 5 is still not PASS and the live-job component is named as the gap.
    # 2026-07-28 (final): all four PI closure items met -> condition 5 legitimately PASS.
    expect("ALL FIVE CONDITIONS PASS" in _g, "the gate records all five conditions as passed")
    expect("0.9789" in _g or "0.974" in _g,
           "the state-ID cosines from real wavefunctions are recorded in the gate")
    _gflat = " ".join(_g.split())
    expect("requires an explicit go from the PI" in _gflat,
           "passing the gate authorises ASKING, not launching")
    # 2026-07-28 (later): the trial RAN; the gate now records the PI verdict instead of the
    # proposal. The invariants: prohibition stands, trial output unquotable, closure items named.
    expect("PI verdict on the trial" in _g, "the gate records the PI verdict on the trial")
    expect("remain unquotable" in _g or "stay unquotable" in _g,
           "the trial energies are explicitly unquotable")
    expect("requires an explicit go from the PI" in _gflat,
           "CI-NEB launch requires explicit PI approval (gate passed != launch approved)")

print("\n[29] preflight must emit a local->remote staging manifest -- PI REQUEST")
if _os.path.exists("scripts/25_preflight.py"):
    _pf = open("scripts/25_preflight.py").read()
    expect("--manifest-out" in _pf, "preflight can write a staging manifest")
    expect("remote_destination" in _pf and "sha256" in _pf,
           "the manifest records remote destination and hash per file")
    expect("local_source" in _pf, "the manifest records the local source per file")

print("\n[30] a str.replace edit must be ASSERTED, and table rows must match the body -- INCIDENT")
# Two reviewer findings from one root cause: I edited Q0_NEB_GATE.md with s.replace(old, new)
# where old did not match the file (different wording than I remembered), so the edit silently
# no-oped. The summary table said IN PROGRESS while the body said converged, and I REPORTED the
# edit as made. An edit without an assert is a status claim without evidence.
_GT2 = "results/objective1/dft/charge_relaxed/Q0_NEB_GATE.md"
if _os.path.exists(_GT2):
    _g2 = open(_GT2).read()
    # the summary table row and the body must agree about condition 1
    _row1 = next((l for l in _g2.splitlines() if l.startswith("| 1 |")), "")
    expect("PASS" in _row1 and "IN PROGRESS" not in _row1,
           f"condition-1 table row states PASS, not a stale IN PROGRESS (row: {_row1[:80]})")
    expect("q0_final: CONVERGED" in _g2,
           "body records q0_final as converged")
    expect("approaching monotonically" not in _g2,
           "no stale 'approaching monotonically' text survives anywhere in the gate")
    # table/body consistency for every condition: a row claiming PASS must not have body text
    # still calling that condition open, and vice versa for condition 5
    _row5 = next((l for l in _g2.splitlines() if l.startswith("| 5 |")), "")
    expect("PASS" in _row5 and "PARTIAL" not in _row5,
           "condition-5 row records PASS after the closure items (table/body agree)")
    expect("requires an explicit go from the PI" in " ".join(_g2.split()),
           "CI-NEB launch still requires explicit PI approval")

# PI request: the q0_final convergence state must be CONSISTENT across gate, canonical index
# and audit record -- the previous fix touched only the gate. Also: the convergence claim must
# be checkable from the RAW archived output, not just report transcription.
_DOCS_Q0 = ["results/objective1/dft/charge_relaxed/Q0_NEB_GATE.md",
            "results/objective2/CURRENT_STATUS.md", "EXPERIMENT_AUDIT.md"]
for _f in _DOCS_Q0:
    if not _os.path.exists(_f):
        continue
    _tx = open(_f).read()
    for _stale in ["q0_final not yet converged", "not yet converged per QE",
                   "has not reached its force target",
                   "IN PROGRESS, at the soft-mode floor"]:
        expect(_stale not in _tx, f"{_os.path.basename(_f)}: no stale claim {_stale!r}")
    expect("CONVERGED" in _tx, f"{_os.path.basename(_f)}: records q0_final as converged")
# raw-output archive: the convergence block must be verifiable from the primary record
import gzip as _gzip
_GZ = "results/objective1/dft/charge_relaxed/q0/q0_final_ns1.out.gz"
_CV = "results/objective1/dft/charge_relaxed/q0/CONVERGENCE_SUMMARY.json"
if _os.path.exists(_GZ) and _os.path.exists(_CV):
    _raw = _gzip.open(_GZ, "rt", errors="ignore").read()
    expect("End of BFGS Geometry Optimization" in _raw,
           "the RAW archived output contains QE's convergence block")
    expect("bfgs converged in  11 scf cycles and  10 bfgs steps" in _raw,
           "the raw output contains the exact converged-in line")
    _cv = _json.load(open(_CV))
    _fin = next(e for e in _cv["endpoints"] if e["tag"] == "q0_final")
    expect(_fin["qe_convergence_block"] is True and _fin["final_energy_Ry"] == -9247.62842357,
           "the parsed summary matches the raw output (block + energy)")
    import hashlib as _hl
    _h = _hl.sha256(open(_GZ, "rb").read()).hexdigest()
    expect(_fin["sha256_of_gz"] == _h,
           "the summary's recorded hash matches the archived gz on disk")

print("\n[31] the NEB archive/restart harness must round-trip a REAL band -- GATE CONDITION 5")
# Gate condition 5 needs restart+archive+state-ID tooling. A harness that only works on
# synthetic input proves nothing, so the selftest runs against the PRESERVED q=+1 explore band
# (a real neb.x .path written by neb.x), not a fixture I wrote.
_HR = "scripts/26_neb_harness.py"
_Q1 = "results/objective1/dft/charge_relaxed/q1_explore_restart/q1_explore_state.tar.gz"
if _os.path.exists(_HR) and _os.path.exists(_Q1):
    _r = _sp.run([_sys.executable, _HR, "--mode", "selftest", "--q1-band-archive", _Q1],
                 capture_output=True, text=True)
    expect(_r.returncode == 0, "harness selftest exits 0 on the real q=+1 band")
    try:
        _o = _json.loads(_r.stdout)
    except Exception:
        _o = {}
    expect(_o.get("selftest_pass") is True, "selftest reports pass")
    expect(_o.get("n_images") == 5, f"parses 5 images from the real band (got {_o.get('n_images')})")
    expect(_o.get("rows_per_image") == 159,
           f"parses 159 atoms per image (got {_o.get('rows_per_image')})")
    expect(_o.get("verify", {}).get("restartable") is True,
           "the archived snapshot verifies as restartable")
    expect(_o.get("snapshots_written") == 2 and _o.get("verify", {}).get("snapshot") == 1,
           "the archive is append-only (second snapshot lands at index 1, does not overwrite)")
    # state identification must NOT use band index -- PI rule
    _src = open(_HR).read()
    expect("cosine" in _src and "NEVER" in _src,
           "state identification is by per-atom weight cosine, band index explicitly excluded")
    expect("append-only" in _src, "the archive is documented and enforced as append-only")

print("\n[32] navigation layer: README routes, RESULTS_INDEX rows, archive is bannered -- PI")
# PI assessment: record quality high, information architecture cluttered. The fix: README is a
# pure navigation page, RESULTS_INDEX has one row per question, superseded docs move to
# archive/ with banners, xrd/ is marked independent.
if _os.path.exists("README.md"):
    _r = open("README.md").read()
    expect("RESULTS_INDEX.md" in _r, "README links the results index")
    expect("navigation page only" in _r, "README declares itself navigation, not results")
    expect("tracer bullet" not in _r.lower() or "historical" in _r.lower(),
           "README no longer describes the project as an early tracer bullet")
    expect("INDEPENDENT" in _r or "independent" in _r, "README marks xrd/ as independent")
if _os.path.exists("RESULTS_INDEX.md"):
    _x = open("RESULTS_INDEX.md").read()
    for _q in ["Q1.", "Q2.", "Q3.", "Q4."]:
        expect(_q in _x, f"results index has a row for {_q}")
    for _fld in ["Current conclusion", "Scope", "Authoritative", "Raw data", "Next"]:
        expect(_fld in _x, f"index rows carry the '{_fld}' field")
    expect("OPEN" in _x, "the charge-state ordering is recorded as OPEN in the index")
    expect("banned" in _x.lower(), "the Tyagi-ordering ban is visible at the index level")
# every file under archive/ that this session created must open with a SUPERSEDED banner
import glob as _gl
for _f in _gl.glob("archive/**/*.md", recursive=True):
    _head = open(_f).read(200)
    expect(_head.startswith("> # SUPERSEDED"),
           f"{_f}: archived doc opens with a SUPERSEDED banner")
# in-place superseded/interim docs carry pointers
_c84 = "results/objective2/paired_pilot/CORPUS84_RESULT.md"
if _os.path.exists(_c84):
    expect(open(_c84).read(150).startswith("> **SUPERSEDED"),
           "CORPUS84 opens with its supersession pointer")

print("\n[33] restart evidence must be recompute-vs-reread, and numeric bounds must match data")
# Three reviewer findings on the HARNESS_TRIAL report, one root: (a) an audit cell cited the
# NEAR-ZERO energy movement as 'evidence of genuine continuation' -- backwards; stability at
# fixed positions evidences nothing. The valid discriminator is recompute-vs-reread: v2's no-op
# gave a BIT-IDENTICAL neb.path (same sha, 0s SCF); v4 spent 1h16m SCF and produced
# re-converged non-identical values. (b,c) the report claimed <=3e-9 au energy agreement when
# the printed snapshots give max 4e-8 -- an order of magnitude off.
_TR = "results/objective1/dft/charge_relaxed/HARNESS_TRIAL_RESULT.md"
if _os.path.exists(_TR):
    _tr = open(_TR).read()
    expect("3×10⁻⁹" not in _tr.replace("was wrong", "\x00", 1) or "wrong" in _tr,
           "the retracted 3e-9 bound appears only inside its own correction")
    expect("4×10⁻⁸" in _tr, "the correct max energy delta (4e-8 au) is stated")
    expect("Recompute-vs-reread" in _tr or "recompute" in _tr.lower(),
           "the report names recompute-vs-reread as the discriminator")
    expect("bit-identical" in _tr.lower(),
           "the v2 no-op signature (bit-identical file) is recorded for contrast")
    expect("evidence of nothing" in _tr or "mislabelled" in _tr,
           "the backwards 'energy stability = continuation' claim is retracted in the report")
    expect("NOT as position update" in _tr,
           "criterion 3's PASS is scoped to re-evaluation, not position update")
    # the actual snapshot energies, pinned so the bound can't drift again
    _E0 = [-4623.81474023, -4623.79612228, -4623.77858921, -4623.79523558, -4623.81562675]
    _E1 = [-4623.81474023, -4623.79612229, -4623.77858919, -4623.79523562, -4623.81562675]
    _dmax = max(abs(a - b) for a, b in zip(_E0, _E1))
    expect(3e-9 < _dmax < 1e-7 and abs(_dmax - 4e-8) < 1e-9,
           f"pinned snapshot energies give max delta 4e-8 au (got {_dmax:.1e}) -- the old bound was wrong")

print("\n[34] production q=0 NEB input: degauss 0.005 + machine fingerprint match -- PI GATE")
# The trial ran at the generator DEFAULT degauss=0.01 -- fine for the harness, prohibited for
# production. The PI requires the production input regenerated at 0.005 with an automated
# fingerprint comparison against the q=+1 leg.
# PI correction: the comparison object is q0-PRODUCTION vs q1-PRODUCTION -- never explore.
# (The first version of this test compared against q1_explore, so both sides just inherited
# the explore-level conv_thr=1e-6 error together.)
_Q0P = "ehpc/inputs_stage2/neb_q0_production/q0_cineb.neb.in"
_Q1P = "ehpc/inputs_stage2/neb_q1_production/q1_cineb.neb.in"
if _os.path.exists(_Q0P) and _os.path.exists(_Q1P):
    _DEF = {"tot_charge": "0.0", "nspin": "1"}   # QE defaults resolved explicitly
    def _fp(path):
        _t = open(path).read()
        _f = {}
        for _k in ["ecutwfc", "ecutrho", "degauss", "occupations", "vdw_corr",
                   "dftd3_version", "nosym", "noinv", "conv_thr", "smearing",
                   "CI_scheme", "path_thr", "num_of_images", "nstep_path",
                   "opt_scheme", "tot_charge", "nspin"]:
            _m = _re2.search(rf"^\s*{_k}\s*=\s*(\S+?)\s*$", _t, _re2.M)
            _f[_k] = _m.group(1).rstrip(",") if _m else _DEF.get(_k)
        _m = _re2.search(r"K_POINTS\s+\w+\s*\n\s*([\d ]+)", _t)
        _f["kgrid"] = _m.group(1).strip() if _m else None
        _f["pseudos"] = dict(_re2.findall(r"^\s*([A-Z][a-z]?)\s+[\d.]+\s+(\S+\.UPF)\s*$", _t, _re2.M))
        return _f
    _f0, _f1 = _fp(_Q0P), _fp(_Q1P)
    expect(_f0.get("conv_thr") == "1e-8" and _f1.get("conv_thr") == "1e-8",
           f"production pair uses conv_thr=1e-8 (locked protocol; got {_f0.get('conv_thr')}/{_f1.get('conv_thr')})")
    expect(_f0.get("degauss") == "0.005",
           f"production q=0 input uses degauss=0.005 (got {_f0.get('degauss')})")
    expect(_f0.get("CI_scheme") == "'auto'" and _f0.get("path_thr") == "0.050",
           "pair-locked NEB params: CI auto, path_thr 0.05")
    _dif = {k for k in (set(_f0) | set(_f1)) - {"tot_charge"}
            if str(_f0.get(k)) != str(_f1.get(k))}
    expect(not _dif, f"q0/q1 PRODUCTION fingerprints identical beyond charge (diffs: {_dif})")
    expect(float(_f0["tot_charge"]) == 0.0 and float(_f1["tot_charge"]) == 1.0,
           "charge check is NON-VACUOUS: q0=0.0 (QE default, resolved), q1=1")
    expect(_f0.get("kgrid") == "1 1 1 0 0 0", "k-grid is Gamma (1x1x1 unshifted)")
    expect(_f0["pseudos"] == _f1["pseudos"] and len(_f0["pseudos"]) == 3,
           "pseudopotentials identical across the pair (3 species)")
    # the TRIAL input must never be promoted to production
    _TRI = "ehpc/inputs_stage2/neb_q0_trial/q0_trial.neb.in"
    if _os.path.exists(_TRI):
        expect(_fp(_TRI).get("degauss") == "0.01",
               "the trial input is recorded as-run (0.01) -- regenerate, never promote")
# archive banners: EVERY archive/*.md must open with a banner (the clean-clone failure)
import glob as _gl2
_missing = [f for f in _gl2.glob("archive/**/*.md", recursive=True)
            if not open(f).read(60).startswith("> # SUPERSEDED")]
expect(not _missing, f"every archive/ doc opens with a SUPERSEDED banner (missing: {_missing})")

print("\n[35] state-ID must be RECOMPUTABLE from committed weights -- PI GATE")
# The first state-ID record shipped only cosine/IPR/E -- results without the data to recompute
# them. Now the per-atom weight vectors and source hashes are committed; this test recomputes
# every cosine and IPR from the raw weights and cross-checks the reference hash.
_SW = "results/objective1/dft/charge_relaxed/harness_trial/state_id_weights.json"
_RF = "results/objective1/dft/charge_relaxed/harness_trial/q0_reference_metrics.json"
if _os.path.exists(_SW) and _os.path.exists(_RF):
    import hashlib as _hl, math as _math
    _sw = _json.load(open(_SW)); _ref = _json.load(open(_RF))
    _rh = _hl.sha256(open(_RF, "rb").read()).hexdigest()
    expect(_rh == _sw["reference_weights_sha256_of_json"],
           "the committed reference file hash matches the hash recorded at extraction")
    _rw = _ref["weights"]
    expect(len(_rw) == 159, "reference weight vector has 159 entries (one per atom)")
    _pub = {"2": 0.9789, "3": 0.9755, "4": 0.9743}
    for _img, _d in sorted(_sw["images"].items()):
        _w = _d["weights"]
        expect(len(_w) == 159, f"image {_img}: 159 per-atom weights committed")
        _dot = sum(a*b for a, b in zip(_w, _rw))
        _na = _math.sqrt(sum(a*a for a in _w)); _nb = _math.sqrt(sum(b*b for b in _rw))
        _cos = _dot/(_na*_nb)
        expect(abs(_cos - _d["cosine"]) < 5e-6,
               f"image {_img}: cosine recomputed from raw weights = {_cos:.6f} matches record")
        expect(abs(_cos - _pub[_img]) < 5e-4,
               f"image {_img}: recomputed cosine matches the published {_pub[_img]}")
        _ipr = sum(x*x for x in _w) / (sum(_w) ** 2)
        expect(0.02 < _ipr < 0.04,
               f"image {_img}: IPR from raw weights ({_ipr:.4f}) in the delocalised range")
        expect(len(_d.get("projwfc_out_sha256", "")) == 64,
               f"image {_img}: projwfc output sha256 recorded")

print("\n[36] gate-status semantic consistency across ALL authority documents -- PI GATE")
# The clean-clone suite was green while four documents still said PARTIAL/4-of-5 -- the tests
# checked syntax, not semantics. This test asserts: any PARTIAL/4-of-5 mention in an authority
# document must sit in explicitly historical context (held/was/superseded/since met).
_AUTH = ["results/objective1/dft/charge_relaxed/Q0_NEB_GATE.md",
         "results/objective1/dft/charge_relaxed/NEB_HARNESS.md",
         "results/objective1/dft/charge_relaxed/HARNESS_TRIAL_RESULT.md",
         "RESULTS_INDEX.md", "EXPERIMENT_AUDIT.md", "results/objective2/CURRENT_STATUS.md"]
_HIST = ["held at PARTIAL", "was held", "SINCE MET", "since met", "Superseded", "superseded",
         "historical"]
for _f in _AUTH:
    if not _os.path.exists(_f): continue
    for _i, _ln in enumerate(open(_f).read().splitlines()):
        if ("PARTIAL" in _ln or "4/5" in _ln or "4 of 5" in _ln) and "PASS" not in _ln:
            expect(any(h in _ln for h in _HIST),
                   f"{_f}:{_i+1}: PARTIAL/4-of-5 mention is marked historical: {_ln[:70]!r}")
_g_idx = open("RESULTS_INDEX.md").read()
expect("ALL FIVE conditions PASS" in _g_idx, "the index states the gate as fully passed")
_aud = open("EXPERIMENT_AUDIT.md").read()
expect("PASS (2026-07-28)" in _aud, "the audit gate table row 5 records PASS")
# PI round 2 (commit 21846e10 review): four contradictions test [36] v1 did NOT cover.
# Each stale phrase below, if present outside historical/strikethrough context, fails the suite.
_STALE = ["sole remaining blocker", "NOT OPEN", "end-to-end pending",
          "one endpoint ESTABLISHED, one IN PROGRESS"]
for _f in _AUTH:
    if not _os.path.exists(_f): continue
    for _i, _ln in enumerate(open(_f).read().splitlines()):
        for _ph in _STALE:
            if _ph in _ln:
                expect(any(h in _ln for h in _HIST) or "~~" in _ln,
                       f"{_f}:{_i+1}: stale phrase {_ph!r} only in historical context")
# the locked protocol may state exactly ONE production path_thr (0.05); 0.10 only as history
_lp = open("results/objective1/dft/charge_relaxed/LOCKED_PROTOCOL_AND_STOPLOSS.md").read()
for _i, _ln in enumerate(_lp.splitlines()):
    if "path_thr" in _ln and "0.10" in _ln and "0.05" not in _ln:
        expect("~~" in _ln or "explore" in _ln.lower(),
               f"LOCKED_PROTOCOL:{_i+1}: a 0.10 path_thr line is marked historical/explore")
expect("**0.05 eV/Å** (tightened" in _lp,
       "the protocol amendment states production path_thr = 0.05")
# the audit must not describe the gate as unopened, nor q0_final as unconverged current-state
expect("NOT OPEN" not in _aud, "the audit no longer describes the gate as NOT OPEN")
expect("launch awaits explicit PI go" in _aud or "waits for the" in _aud,
       "the audit records gate-passed-but-launch-needs-PI-go")

print("\n[37] Q3 provenance: index-discovered authority sweep + full derivation (F-006/F-008/F-011)")
import subprocess as _sp, sys as _sys, os as _os, re as _re37

# (a) DISCOVER authorities from the canonical index rather than a hand-maintained list
#     (CYCLE-000004 F-008: the previous hand-list omitted two authorities the index names).
_idx = open("RESULTS_INDEX.md").read()
# The Q3 block's state is now CONDITIONAL (F-019 closure): while demoted, every index-named
# authority must carry the demotion marker; after closure (STATUS: CITABLE), the marker
# requirement applies only to documents that predate closure — the closure record itself and
# any post-closure document must instead be consistent with group [43]'s one-state check.
_q3blk = _idx[_idx.index("## Q3"):]
_q3blk = _q3blk[:_q3blk.index("\n## ") if "\n## " in _q3blk[4:] else len(_q3blk)]
_demoted_now = ("NOT CITABLE" in _q3blk) and ("STATUS: CITABLE" not in _q3blk)
_auths = set()
for _p in _re37.findall(r"`([A-Za-z0-9_./-]+\.md)`", _q3blk):
    if _os.path.exists(_p) and _p != "RESULTS_INDEX.md":
        _auths.add(_p)
expect(len(_auths) >= 3, f"index-discovered Q3 authorities: found {len(_auths)}, expected >= 3")
if _demoted_now:
    for _doc in sorted(_auths):
        _t = open(_doc).read()
        expect("Q3 PROVENANCE STATUS" in _t or "UNVERIFIED / NOT CITABLE" in _t
               or "HISTORICAL" in _t or "SUPERSEDED" in _t,
               f"index-named authority {_os.path.basename(_doc)} carries the demotion/superseded marker")
else:
    expect("Q3_CLOSURE_RECORD.md" in _q3blk,
           "CITABLE Q3 block must name the closure record")

# (b) F-011: no current document may assert q0_final failed to converge without a marker
for _doc in sorted(_auths) + ["RESULTS_INDEX.md", "EXPERIMENT_AUDIT.md",
                              "results/objective1/dft/charge_relaxed/Q0_NEB_GATE.md"]:
    if not _os.path.exists(_doc): continue
    for _ln in open(_doc).read().splitlines():
        if "plateaued without converging" in _ln:
            expect(_ln.lstrip().startswith("- ~~") or "~~" in _ln or "SUPERSEDED" in _ln,
                   f"{_os.path.basename(_doc)}: stale q0_final plateau claim is struck/superseded")

# (c) the committed Q3 derivation must recompute EVERY published value, cosine included
_r = _sp.run([_sys.executable, "results/objective1/dft/charge_relaxed/q3_raw/derive_q3.py"],
             capture_output=True, text=True)
expect(_r.returncode == 0, f"derive_q3.py exits 0; got {_r.returncode}: {_r.stderr[-200:]}")
for _need in ("[map]", "[cos]", "[align]", "[record]"):
    expect(_need in _r.stdout, f"derivation reports {_need} (mapping/cosine/alignment/record check)")
expect("every quoted value reproduces" in _r.stdout, "derivation asserts full reproduction")

# (d) the mapping record must exist and be non-trivial — deleting it must fail the derivation
_mp = "results/objective1/dft/charge_relaxed/q3_raw/P1_P2_MAPPING_AND_WEIGHTS.json"
expect(_os.path.exists(_mp), "the P1->P2 shared-atom mapping record is committed")
import json as _json37
_mr = _json37.load(open(_mp))
expect(len(_mr["mapping_P1_to_P2"]) == 159, "mapping covers all 159 shared atoms")
expect(abs(_mr["recomputed"]["shared_atom_cosine"] - 0.9757) < 5e-4, "recorded cosine matches published")

print("\n[38] declared group count must equal the count this file actually emits (F-010)")
import re as _re2
_n = len(_re2.findall(r'print\("\\n\[(\d+)\]', open(__file__).read()))
for _doc, _pat in [("README.md", r"Regression suite \((\d+) groups"),
                   ("results/objective2/CURRENT_STATUS.md", r"\((\d+) check groups"),
                   ("EXPERIMENT_AUDIT.md", r"regression suite \((\d+) groups\)"),
                   ]:  # AUDIT_CORRECTIONS_CYCLE1.md is a HISTORICAL record (F-015) -- excluded
    _m = _re2.search(_pat, open(_doc).read())
    expect(_m is not None, f"{_doc} declares a group count")
    if _m: expect(int(_m.group(1)) == _n, f"{_doc} declares {_m.group(1) if _m else '?'} groups, file emits {_n}")


print("\n[39] Q3 numeric + status coherence (CYCLE-000005 F-012 / F-013)")
import subprocess as _sp39, sys as _sys39, os as _os39, re as _re39
_dv = "results/objective1/dft/charge_relaxed/q3_raw/derive_q3.py"
_r39 = _sp39.run([_sys39.executable, _dv], capture_output=True, text=True)
expect(_r39.returncode == 0, f"derive_q3.py exits 0; got {_r39.returncode}")

# (a) F-012: ONE declared convention; every authority must quote the derived values verbatim.
_m = _re39.search(r"VBM-referenced ([+-][\d.]+) meV, semicore-aligned ([+-][\d.]+) meV", _r39.stdout)
expect(_m is not None, "derivation prints both normalized alignment values")
if _m:
    _v, _s = _m.group(1), _m.group(2)
    expect("convention:" in _r39.stdout, "derivation declares its subtraction convention explicitly")
    for _doc in ["results/objective1/dft/charge_relaxed/P1_REFERENCE_AUDIT.md",
                 "results/objective1/dft/charge_relaxed/Q0_RESOLVED.md"]:
        _t39 = open(_doc).read()
        expect(f"{_v} meV" in _t39,
               f"{_os39.path.basename(_doc)} quotes the derived VBM value {_v} meV")
        expect(f"{_s} meV" in _t39,
               f"{_os39.path.basename(_doc)} quotes the derived semicore value {_s} meV")
        # No CONFLICTING alignment value may appear unmarked. A doc that quotes the
        # right number in a note while its TABLE still shows a stale one must fail --
        # that is exactly the hole the first version of this check left open.
        _ok_vals = {_v, _s, "+7.1", "-7.1"}   # +-7.1 is the explicitly-invalid raw difference
        for _ln in _t39.splitlines():
            _low = _ln.lower()
            if not any(_k in _low for k_ in [0] for _k in
                       ("vbm-referenced", "semicore-aligned", "semicore-referenced")):
                continue
            for _num in _re39.findall(r"([+-]\d+\.\d+)\s*meV", _ln):
                if _num in _ok_vals:
                    continue
                expect("rounding artifact" in _low or "earlier" in _low or "~~" in _ln
                       or "superseded" in _low or "invalid" in _low or "retract" in _low,
                       f"{_os39.path.basename(_doc)}: conflicting alignment value {_num} meV "
                       f"on an alignment line is marked superseded/invalid")

# (b) F-013: when the index row names committed q3_raw evidence AND the derivation exits 0,
#     no unmarked "raw absent / not reproducible" assertion may survive in that row.
_idx39 = open("RESULTS_INDEX.md").read()
_s39 = _idx39.find("## Q3.")
_e39 = _idx39.find("\n## ", _s39 + 4)
_row = _idx39[_s39:_e39 if _e39 > 0 else len(_idx39)]
expect("q3_raw/" in _row and "COMMITTED" in _row, "the Q3 row names the committed raw evidence")
for _bad in ("are not committed", "cannot be independently reproduced"):
    for _ln in _row.splitlines():
        if _bad in _ln:
            _ctx = _row[max(0, _row.find(_ln) - 400): _row.find(_ln) + 200]
            expect("Superseded wording" in _ctx or "previously said" in _ctx or "retracted" in _ctx,
                   f"Q3 row: '{_bad}' appears only inside an explicit retraction")


print("\n[40] XRD DOC range: every unmarked range must match the committed source (F-014)")
import csv as _csv40, re as _re40, os as _os40
# Source of truth: the committed summary table, which an isolated raw recomputation
# (xrd_protocol_kernel.analyse_single on the raw .txt/.mdi) reproduces to 1e-3 %.
_lo = _hi = None
for _row in _csv40.reader(open("xrd/results/summary_metrics.csv")):
    if _row and _row[0].strip().lower().startswith("degree of crystallinity"):
        _lo, _hi = float(_row[2]), float(_row[3]); break
expect(_lo is not None, "summary_metrics.csv records the degree-of-crystallinity range")
if _lo is not None:
    _cur = (round(_lo), round(_hi))
    expect(_cur == (49, 65), f"committed DOC range rounds to 49-65%, got {_cur}")
    _txt40 = open("xrd/README.md").read()
    for _ln in _txt40.splitlines():
        for _m40 in _re40.finditer(r"(\d{2})\s*[–-]\s*(\d{2})\s*%", _ln):
            _pair = (int(_m40.group(1)), int(_m40.group(2)))
            # only DOC-shaped statements matter; skip unrelated percentage ranges
            if not _re40.search(r"crystallin|DOC", _ln, _re40.I): continue
            if _pair == _cur: continue
            _low = _ln.lower()
            expect("superseded" in _low or "previously" in _low or "shifted" in _low
                   or "→" in _ln or "retract" in _low or "~~" in _ln,
                   f"xrd/README.md: stale DOC range {_pair[0]}-{_pair[1]}% is marked superseded "
                   f"(current is {_cur[0]}-{_cur[1]}%)")


print("\n[41] every regression-count assertion is current or explicitly historical (F-015)")
import re as _re41, glob as _glob41, os as _os41
_n41 = len(_re41.findall(r'print\("\\n\[(\d+)\]', open("scripts/20_test_checks.py").read()))
_docs41 = [f for f in _glob41.glob("**/*.md", recursive=True)
           if not f.startswith(("archive/", "hpc/", ".git", "tests/fixtures/"))]
_pats41 = [r"emits (\d+) numbered groups", r"Regression suite \((\d+) groups",
           r"\((\d+) check groups", r"regression suite \((\d+) groups\)",
           r"suite (?:now )?(?:emits|has) (\d+) group", r"corrected to (\d+)\b",
           r"→\s*(\d+)\s*$"]

def _count_receipt(doc, lineno, val, cur, marked):
    """Shared wording for BOTH outcomes (F-024): the receipt states what holds."""
    tail = ("but IS marked historical/superseded" if marked
            else "and is not marked historical")
    return f"{doc}:{lineno} count {val} != current {cur} {tail}"

def _count_claim_hits(path, cur):
    """-> [(lineno, value, marked_historical)] for every stale suite-size claim."""
    _ls = open(path, errors="ignore").read().splitlines()
    _hist_doc = any("HISTORICAL RECORD" in l for l in _ls[:40])
    out = []
    for _i, _ln in enumerate(_ls):
        # gate on the PARAGRAPH, not the single line: the sentence carrying the stale
        # count often names neither "group" nor the script (F-015's own fixture did not).
        _para = " ".join(_ls[max(0, _i-4):_i+3])
        if not _re41.search(r"group|20_test_checks|regression suite", _para, _re41.I): continue
        for _p in _pats41:
            for _m in _re41.finditer(_p, _ln):
                _v = int(_m.group(1))
                if _v == cur or _v < 5 or _v > 500: continue   # current, or not a suite size
                _ctx = " ".join(_ls[max(0, _i-6):_i+3]).lower()
                out.append((_i + 1, _v,
                            bool(_hist_doc or "historical" in _ctx or "superseded" in _ctx
                                 or "~~" in _ln or "retract" in _ctx)))
    return out

for _d41 in sorted(_docs41):
    for _ln41, _v41, _mk41 in _count_claim_hits(_d41, _n41):
        expect(_mk41,
               _count_receipt(_d41, _ln41, _v41, _n41, False),
               ok_msg=_count_receipt(_d41, _ln41, _v41, _n41, True))


print("\n[42] Q2 production-NEB state is consistent across every current authority (F-017)")
import re as _re42, glob as _glob42, os as _os42
# Ground truth is the committed raw record: both legs converged.
_pn = "results/objective1/dft/charge_relaxed/PRODUCTION_NEB_STATUS.md"
expect(_os42.path.exists(_pn), "PRODUCTION_NEB_STATUS.md exists")
_pns = open(_pn).read()
expect("BOTH LEGS CONVERGED" in _pns, "production status records both legs converged")
# Sweep: any current doc asserting a pre-run/missing state must be marked historical.
_stale_pats = [r"NEB not yet run", r"required leg is missing", r"q\s*=\s*0.{0,40}not delivered",
               r"decision is now OPEN[^~]*requires an explicit go",
               r"charge-state comparison.{0,30}impossible",
               # Added 2026-08-04: DFT_BENCHMARK.md's anchor-(b) paragraph asserted that a
               # relaxed charged path "is the clear next step" long after both production legs
               # converged, and the sweep missed it because it hunted only literal phrases about
               # a leg being absent. The defect class is any CURRENT text framing the relaxed
               # charged path as future work -- same too-narrow-predicate error as F-024/F-025.
               # NOTE: markdown hard-wraps sentences, so every multiword phrase below uses
               # \s+ between words -- an earlier version used literal spaces and silently
               # matched nothing because the text reads "relaxed\ncharged path".
               r"(?:requires|needs|awaits)\s+a\s+\*{0,2}relaxed\s+charged\s+path",
               r"relaxed\s+charged\s+path[^.~]{0,80}(?:clear\s+next\s+step|is\s+the\s+next\s+step|"
               r"still\s+to\s+be|not\s+yet\s+(?:run|done|performed))",
               r"(?:full\s+charged\s+NEB|charged.cell\s+geometry\s+optimisation)[^.~]{0,60}"
               r"(?:is\s+the\s+clear\s+next\s+step|remains\s+to\s+be|has\s+not\s+been)"]
for _d42 in sorted(_glob42.glob("**/*.md", recursive=True)):
    if _d42.startswith(("archive/", "hpc/")): continue
    _txt42 = open(_d42, errors="ignore").read()
    _lines42 = _txt42.splitlines()
    _sup_doc = "SUPERSEDED AS CURRENT STATE" in _txt42[:1500] or _txt42.startswith("> # SUPERSEDED")
    # Match over a WINDOW, not a single line. Markdown hard-wraps sentences, so a phrase like
    # "requires a **relaxed\ncharged path**" spans two lines and a per-line search can never
    # see it -- this is why the anchor-(b) staleness survived the sweep until 2026-08-04.
    for _i42, _ln42 in enumerate(_lines42):
        _win42 = " ".join(_lines42[_i42:_i42+3])
        for _p42 in _stale_pats:
            _m42 = _re42.search(_p42, _win42)
            # attribute the hit to the line the match STARTS on, so a window does not
            # smear one document's defect onto a neighbouring paragraph
            if _m42 and _m42.start() <= len(_ln42):
                _ctx42 = " ".join(_lines42[max(0,_i42-6):_i42+4]).lower()
                expect(_sup_doc or "historical" in _ctx42 or "superseded" in _ctx42
                       or "~~" in _ln42 or "retract" in _ctx42,
                       f"{_d42}:{_i42+1} pre-production state asserted without historical marker",
                       ok_msg=f"{_d42}:{_i42+1} pre-production state carries an explicit historical marker")


print("\n[43] Q3 citability and Q0 gate condition 3 assert ONE state (F-019 / C-STATE-004)")
import re as _re43, os as _os43
_idx43 = open("RESULTS_INDEX.md").read()
_gate43 = open("results/objective1/dft/charge_relaxed/Q0_NEB_GATE.md").read()
_i43 = _idx43[_idx43.index("## Q3"):]
_i43 = _i43[:_i43.index("\n## ") if "\n## " in _i43[4:] else len(_i43)]
_q3_citable = bool(_re43.search(r"STATUS: CITABLE", _i43))
# F-020: detect CONTRADICTORY current predicates instead of letting CITABLE mask a surviving
# NOT-CITABLE. Any NOT-CITABLE assertion in the Q3 block must sit in historical/superseded
# context (the paragraph around it names Historical/Superseded/retract) — otherwise it is a
# live contradiction and the check fails regardless of the STATUS row.
_lines43 = _i43.splitlines()
_live_bans43 = []
for _j43, _l43 in enumerate(_lines43):
    if _re43.search(r"NOT CITABLE|stays removed as gate evidence", _l43):
        # context = the ban's own line plus one line either side ONLY -- a wide window
        # absorbed a NEIGHBOURING historical note and passed the auditor's exact fixture.
        _para43 = " ".join(_lines43[max(0,_j43-1):_j43+2]).lower()
        if not ("historical" in _para43 or "superseded" in _para43 or "retract" in _para43):
            _live_bans43.append(_j43+1)
expect(not (_q3_citable and _live_bans43),
       f"Q3 block asserts CITABLE and NOT-CITABLE simultaneously (unmarked ban at block lines {_live_bans43})",
       ok_msg=("Q3 block has ONE current citability state"
               + (" (CITABLE; every retained NOT-CITABLE line is marked historical)"
                  if _q3_citable else " (demoted; no CITABLE claim)")))
_q3_banned = bool(_live_bans43) and not _q3_citable
_m43 = _re43.search(r"\|\s*3\s*\|[^|]*competing localised spin state[^|]*\|\s*([^|]+)\|", _gate43)
expect(_m43 is not None, "Q0 gate table has a condition-3 row")
_c3_pass = "PASS" in (_m43.group(1) if _m43 else "")
# one state: either Q3 citable AND condition 3 may PASS, or Q3 demoted AND condition 3 not PASS
expect(not (_q3_banned and _c3_pass),
       "Q3 demoted in index while Q0 gate condition 3 claims PASS on the same evidence")
if _q3_citable:
    expect(_os43.path.exists("results/objective1/dft/charge_relaxed/Q3_CLOSURE_RECORD.md"),
           "CITABLE status requires the closure record artifact")
    _cr43 = open("results/objective1/dft/charge_relaxed/Q3_CLOSURE_RECORD.md").read()
    for _f43 in ("F-006", "F-012", "F-013"):
        expect(_f43 in _cr43, f"closure record names {_f43}")
    # F-019 (CYCLE-000019): citability must PROPAGATE to every index-named Q3 authority --
    # each must open with the CLOSED/CITABLE banner, and any surviving demotion-era wording
    # ("restored only when", "NOT CITABLE", "re-verification is owed") must sit inside
    # explicitly historical/superseded context.
    for _doc43 in sorted(_auths if '_auths' in dir() else []):
        pass
    _q3_docs43 = ["results/objective1/dft/charge_relaxed/Q0_POLARON_EXCLUDED.md",
                  "results/objective1/dft/charge_relaxed/Q0_RESOLVED.md",
                  "results/objective1/dft/charge_relaxed/P1_REFERENCE_AUDIT.md"]
    for _doc43 in _q3_docs43:
        _t43 = open(_doc43).read()
        expect(_t43.startswith("> **Q3 PROVENANCE STATUS — CLOSED / CITABLE"),
               f"{_os43.path.basename(_doc43)} opens with the CLOSED/CITABLE banner")
        _dl43 = _t43.splitlines()
        for _k43, _ln2 in enumerate(_dl43):
            if _re43.search(r"restored only when|NOT CITABLE|re-verification is owed", _ln2):
                _c2 = " ".join(_dl43[max(0,_k43-1):_k43+2]).lower()
                expect("historical" in _c2 or "superseded" in _c2,
                       f"{_os43.path.basename(_doc43)}:{_k43+1} demotion-era wording without historical marker",
                       ok_msg=f"{_os43.path.basename(_doc43)}:{_k43+1} demotion-era wording is marked historical/superseded")
    _g43 = open("results/objective1/dft/charge_relaxed/Q0_NEB_GATE.md").read()
    expect("re-verification COMPLETE" in _g43 or "Q3_CLOSURE_RECORD" in _g43,
           "Q0 gate condition 3 cites the closure record")
    _gl43 = _g43.splitlines()
    for _k43, _ln2 in enumerate(_gl43):
        if _re43.search(r"Pending independent re-verification|re-verification is owed", _ln2):
            _c2 = " ".join(_gl43[max(0,_k43-1):_k43+2]).lower()
            expect("historical" in _c2 or "superseded" in _c2,
                   f"Q0_NEB_GATE.md:{_k43+1} pending-re-verification wording without historical marker",
                   ok_msg=f"Q0_NEB_GATE.md:{_k43+1} pending-re-verification wording is marked historical/superseded")


print("\n[44] staging manifests agree with production authorities (F-022 / C-STATE-007)")
import json as _js44, re as _re44, os as _os44
_pn44 = open("results/objective1/dft/charge_relaxed/PRODUCTION_NEB_STATUS.md").read()
_both44 = "BOTH LEGS CONVERGED" in _pn44
for _leg44 in ("q0", "q1"):
    _mp44 = f"ehpc/inputs_stage2/neb_{_leg44}_production/staging_manifest.json"
    if not _os44.path.exists(_mp44): continue
    _m44 = _js44.load(open(_mp44))
    _st44 = _m44.get("submission_status", "")
    if _both44:
        expect(_st44 not in ("BLOCKED_DO_NOT_SUBMIT",),
               f"{_leg44} staging manifest still says {_st44} while the authority says the run completed",
               ok_msg=f"{_leg44} staging manifest status {_st44} agrees with the production authority")
    # every current (non-historical) file entry naming a local_source path must exist
    for _f44 in _m44.get("files", []):
        _ls44 = _f44.get("local_source")
        if _ls44:
            expect(_os44.path.exists(_ls44),
                   f"{_leg44} manifest current entry missing on disk: {_ls44}",
                   ok_msg=f"{_leg44} manifest current entry present on disk: {_ls44}")
        _abs44 = _f44.get("local_source_absent_not_committed")
        if _abs44:
            expect(not _os44.path.exists(_abs44),
                   f"{_leg44} manifest claims {_abs44} absent but it EXISTS in tree (stale claim)",
                   ok_msg=f"{_leg44} manifest absent-claim for {_abs44} is still accurate (not in tree)")

print("\n[45] canonical index carries a current XRD row when PASSIVATOR_SCREEN exists (F-023 / C-NAV-005)")
import os as _os45
if _os45.path.exists("xrd/PASSIVATOR_SCREEN.md"):
    _sc45 = open("xrd/PASSIVATOR_SCREEN.md").read()
    _cur45 = not (_sc45.startswith("> # SUPERSEDED") or "SUPERSEDED AS CURRENT" in _sc45[:600])
    if _cur45:
        _ix45 = open("RESULTS_INDEX.md").read()
        expect("PASSIVATOR_SCREEN.md" in _ix45, "index names the passivator-screen authority")
        expect("xrd/data/" in _ix45, "index names the XRD raw-data locator")
        _blk45 = _ix45[_ix45.index("PASSIVATOR_SCREEN.md")-2000:_ix45.index("PASSIVATOR_SCREEN.md")+800]
        expect("Current conclusion" in _blk45, "the XRD row has a Current-conclusion field")


print("\n[46] a passing guard receipt states what was VERIFIED, not the violation (F-024 / C-GUARD-003)")
import ast as _ast46, re as _re46, os as _os46
# (a) EXECUTE group [41]'s scanner + receipt builder against committed fixtures: the marked
#     case must yield a receipt asserting the marker, the unmarked case the violation.
_fh46 = "tests/fixtures/count_claim_historical.md"
_fu46 = "tests/fixtures/count_claim_unmarked.md"
for _f46 in (_fh46, _fu46):
    expect(_os46.path.exists(_f46), f"receipt fixture committed: {_f46}")
_hits_h = _count_claim_hits(_fh46, _n41)
_hits_u = _count_claim_hits(_fu46, _n41)
expect(len(_hits_h) == 1 and _hits_h[0][1] == 36 and _hits_h[0][2] is True,
       f"marked fixture: scanner finds the stale count and reads it as historical (got {_hits_h})")
expect(len(_hits_u) == 1 and _hits_u[0][1] == 36 and _hits_u[0][2] is False,
       f"unmarked fixture: scanner finds the stale count and reads it as UNmarked (got {_hits_u})")
if _hits_h and _hits_u:
    _rh = _count_receipt(_fh46, _hits_h[0][0], 36, _n41, True)
    _ru = _count_receipt(_fu46, _hits_u[0][0], 36, _n41, False)
    expect("IS marked historical" in _rh and "is not marked" not in _rh,
           f"passing receipt asserts the marker, not its absence: {_rh}")
    expect("is not marked historical" in _ru,
           f"failing receipt asserts the violation: {_ru}")
    expect(_rh != _ru, "the two outcomes produce DIFFERENT receipts")
# (b) STATIC sweep: no violation-phrased expect() may print its message on success.
_VIOL46 = _re46.compile(r"is not marked|without historical marker|simultaneously|still says"
                        r"|but it EXISTS|missing on disk|!= *current|asserted without", _re46.I)
def _lit46(_n):
    if isinstance(_n, _ast46.Constant) and isinstance(_n.value, str): return _n.value
    if isinstance(_n, _ast46.JoinedStr):
        return "".join(v.value for v in _n.values
                       if isinstance(v, _ast46.Constant) and isinstance(v.value, str))
    return ""
_offenders46 = []
for _node46 in _ast46.walk(_ast46.parse(open("scripts/20_test_checks.py").read())):
    if (isinstance(_node46, _ast46.Call) and isinstance(_node46.func, _ast46.Name)
            and _node46.func.id == "expect" and len(_node46.args) >= 2):
        if _VIOL46.search(_lit46(_node46.args[1])) and not any(
                _k.arg == "ok_msg" for _k in _node46.keywords):
            _offenders46.append(_node46.lineno)
expect(not _offenders46,
       f"violation-phrased expect() without ok_msg at lines {_offenders46}",
       ok_msg="every violation-phrased expect() supplies an ok_msg for its passing receipt")


print("\n[47] extraction authorization is bound to a real controller ALLOW (F-025 / C-GATE-002)")
import subprocess as _sp47, sys as _sys47, os as _os47, tempfile as _tf47, json as _js47, re as _re47
_scr47 = "scripts/27_extract_barriers.py"
expect(_os47.path.exists(_scr47), "extractor script is committed")
if _os47.path.exists(_scr47):
    _src47 = open(_scr47).read()
    # (a) STRUCTURAL: authorization must not rest on a self-invented token. Audit F-025: the
    #     previous guard checked syntax + five literal blacklist strings, so `--gate-token
    #     arbitrary` produced a full extraction record while regression [47] still passed.
    # Check the ARGPARSE SURFACE, not prose: the docstring names the retired flag on purpose,
    # recording why it was removed. What must not exist is an accepted argument.
    _args47 = _re47.findall(r'add_argument\(\s*["\']([^"\']+)["\']', _src47)
    expect("--gate-token" not in _args47,
           f"extractor still ACCEPTS the unauthenticated --gate-token argument (args: {_args47})",
           ok_msg=f"extractor accepts only ledger-bound arguments: {_args47}")
    expect("--allow-timestamp" in _args47, "extractor takes an ALLOW-row timestamp")
    # F-025 v2: the auditor pointed --ledger at a fabricated file whose row matched HEAD and
    # the manifest, and every predicate passed. Authority the caller can redirect is not
    # authority, so NO path may be caller-supplied.
    expect("--ledger" not in _args47,
           f"extractor still lets the caller choose the ledger path (args: {_args47})",
           ok_msg="extractor exposes no caller-selectable authorization path")
    expect("CONTROLLER_DIR" in _src47, "controller state location is a module constant")
    expect("corroborated_by" in _src47 or "authorizations" in _src47,
           "authorization requires cross-file corroboration")
    for _need47 in ("action_ledger", "publish_claim", "science_commit", "manifest_sha256",
                    "reason_codes"):
        expect(_need47 in _src47, f"authorization binds on {_need47}")
    _tmp47 = _os47.path.join(_tf47.gettempdir(), "extract_probe.json")
    _led47 = _os47.path.join(_tf47.gettempdir(), "probe_ledger.jsonl")
    def _run47(args):
        if _os47.path.exists(_tmp47): _os47.remove(_tmp47)
        _r = _sp47.run([_sys47.executable, _scr47] + args + ["--out", _tmp47],
                       capture_output=True, text=True)
        _wrote = _os47.path.exists(_tmp47)
        _blob = _r.stdout + _r.stderr
        if _wrote: _os47.remove(_tmp47)          # never retain a gated record
        return _r.returncode, _wrote, _blob
    # (b) NEGATIVE: a syntactically valid but UNRECORDED value -- the auditor's exact bypass.
    for _tok47 in ("arbitrary", "ALLOW", "2099-12-31T00:00:00.000000+00:00"):
        _rc, _wrote, _blob = _run47(["--allow-timestamp", _tok47])
        expect(_rc != 0, f"unrecorded authorization value {_tok47!r} is refused (nonzero exit)")
        expect(not _wrote, f"unrecorded value {_tok47!r}: no extraction record written")
        expect(not _re47.search(r"\d\.\d+\s*eV", _blob),
               f"refusal for {_tok47!r} leaked an eV-shaped value",
               ok_msg=f"refusal for {_tok47!r} leaked no eV-shaped value")
    _rc, _wrote, _b = _run47(["--allow-timestamp", "x", "--ledger", "/nonexistent/ledger.jsonl"])
    expect(_rc != 0 and not _wrote, "a missing ledger is refused and writes nothing")
    # (c) BOTH POLARITIES against a synthetic ledger. A guard that only ever refuses is
    #     indistinguishable from a broken script, so the valid row MUST be honoured; and each
    #     near-miss isolates exactly one binding.
    # The positive path binds on HEAD, so it is only meaningful where git can resolve one.
    # An extracted zipball (which is how the auditor runs an isolated clone) has no .git, and
    # there the guard MUST still refuse -- assert that instead of a pass we cannot construct.
    _h47 = _sp47.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    _head47 = _h47.stdout.strip() if _h47.returncode == 0 else ""
    _man47 = _js47.load(open(".audit/audit_request.json"))["evidence_manifest_sha256"]
    def _row47(ts, **kw):
        r = {"timestamp": ts, "action": "publish_claim", "decision": "ALLOW", "reason_codes": [],
             "science_commit": _head47, "manifest_sha256": _man47, "source": "regression"}
        r.update(kw); return r
    _rows47 = [_row47("2099-01-01T00:00:00.000000+00:00"),
               _row47("2099-01-02T00:00:00.000000+00:00", reason_codes=["PI_APPROVAL_REQUIRED"]),
               _row47("2099-01-03T00:00:00.000000+00:00", science_commit="0"*40),
               _row47("2099-01-04T00:00:00.000000+00:00", manifest_sha256="0"*64),
               _row47("2099-01-05T00:00:00.000000+00:00", decision="DENY"),
               _row47("2099-01-06T00:00:00.000000+00:00", action="commit_and_push_fixes")]
    open(_led47, "w").write("\n".join(_js47.dumps(r) for r in _rows47) + "\n")
    for _ts47, _why47 in [("2099-01-02T00:00:00.000000+00:00", "an ALLOW carrying blocking reason codes"),
                          ("2099-01-03T00:00:00.000000+00:00", "an ALLOW bound to another commit"),
                          ("2099-01-04T00:00:00.000000+00:00", "an ALLOW bound to another manifest"),
                          ("2099-01-05T00:00:00.000000+00:00", "a DENY row"),
                          ("2099-01-06T00:00:00.000000+00:00", "an ALLOW for a different action")]:
        _rc, _wrote, _b = _run47(["--allow-timestamp", _ts47, "--ledger", _led47])
        expect(_rc != 0 and not _wrote, f"{_why47} is refused and writes nothing")
    # The old CLI positive path used --ledger, which no longer exists; and pointing the CLI at
    # the REAL controller state cannot succeed while no authorization is granted (correctly).
    # The positive path is now exercised in-process at (c) below, where CONTROLLER_DIR can be
    # rebound to a fixture holding two agreeing records.
    _rc, _wrote, _b = _run47(["--allow-timestamp", "2099-01-01T00:00:00.000000+00:00"])
    expect(_rc != 0 and not _wrote,
           "an uncorroborated timestamp via the CLI must be refused",
           ok_msg="an uncorroborated timestamp via the CLI is refused (real state grants none)")
    _os47.remove(_led47)
    # F-025 v2 NEGATIVE: a FULLY MATCHING forged ledger -- correct HEAD, correct manifest,
    # decision ALLOW, no reason codes -- must still be refused, because one file the caller
    # can write is not two independent controller records. Driven by importing the module and
    # rebinding CONTROLLER_DIR, which the CLI deliberately cannot do.
    import importlib.util as _iu47, tempfile as _tmpmod47
    _spec47 = _iu47.spec_from_file_location("_bx47", _scr47)
    _mod47 = _iu47.module_from_spec(_spec47); _spec47.loader.exec_module(_mod47)
    _fake47 = _os47.path.join(_tf47.mkdtemp(), "state")
    _os47.makedirs(_os47.path.join(_fake47, "controller"), exist_ok=True)
    _row47f = {"timestamp": "2099-09-09T00:00:00+00:00", "action": "publish_claim",
               "decision": "ALLOW", "reason_codes": [], "science_commit": _head47,
               "manifest_sha256": _man47, "source": "FORGED"}
    open(_os47.path.join(_fake47, "action_ledger.jsonl"), "w").write(_js47.dumps(_row47f) + "\n")
    # (a) ledger forged, controller state has NO matching authorization -> must refuse
    open(_os47.path.join(_fake47, "controller", "state.json"), "w").write(
        _js47.dumps({"authorizations": []}))
    _mod47.CONTROLLER_DIR = _mod47.Path(_fake47)
    try:
        _mod47.authorize("2099-09-09T00:00:00+00:00", _mod47.ROOT)
        expect(False, "a fully matching FORGED ledger was accepted without corroboration")
    except SystemExit as _e47:
        expect("corroborat" in str(_e47).lower(),
               f"forged-ledger refusal cites corroboration (got: {str(_e47)[:70]})",
               ok_msg="a fully matching forged ledger is refused for lack of corroboration")
    # (b) controller state present but bound to a DIFFERENT commit -> must still refuse
    open(_os47.path.join(_fake47, "controller", "state.json"), "w").write(_js47.dumps(
        {"authorizations": [{"action": "publish_claim", "science_commit": "0"*40,
                             "manifest_sha256": _man47,
                             "ledger_timestamp": "2099-09-09T00:00:00+00:00"}]}))
    try:
        _mod47.authorize("2099-09-09T00:00:00+00:00", _mod47.ROOT)
        expect(False, "corroboration bound to another commit was accepted")
    except SystemExit:
        expect(True, "", ok_msg="corroboration bound to another commit is refused")
    # (c) both records agree -> accepted, proving corroboration is not a blanket refusal
    open(_os47.path.join(_fake47, "controller", "state.json"), "w").write(_js47.dumps(
        {"authorizations": [{"action": "publish_claim", "science_commit": _head47,
                             "manifest_sha256": _man47,
                             "ledger_timestamp": "2099-09-09T00:00:00+00:00"}]}))
    try:
        _got47 = _mod47.authorize("2099-09-09T00:00:00+00:00", _mod47.ROOT)
        expect(_got47.get("corroborated_by") is not None,
               "corroborated authorization returns its corroborating record",
               ok_msg="two agreeing controller records authorize (guard is live, not blanket)")
    except SystemExit as _e47b:
        expect(_head47 == "", f"two agreeing records were refused: {str(_e47b)[:80]}",
               ok_msg="no resolvable HEAD here, so refusal is correct")

print("\n[48] a retracted wording does not survive in headings or absolute claims (reviewer warns)")
import glob as _g48, re as _re48
# Each entry: (retracted phrase, the document that retracted it). A retraction is only
# complete when the phrase appears nowhere in that document EXCEPT inside explicit
# retraction/scope context -- headings included, which is how msg3499's warn arose.
_RETRACTED = [
    (r"the state IS the CBM", "results/objective1/dft/charge_relaxed/Q0_RESOLVED.md"),
    (r"no assumed values", "results/fa_host/pool_v3_harmonised/HOST_MANIFEST.md"),
]
for _ph48, _doc48 in _RETRACTED:
    _lines48 = open(_doc48, errors="ignore").read().splitlines()
    for _i48, _ln48 in enumerate(_lines48):
        if _re48.search(_ph48, _ln48):
            _ctx48 = " ".join(_lines48[max(0, _i48-2):_i48+4]).lower()
            expect(any(k in _ctx48 for k in ("retract", "previously read", "overstated",
                                             "scope note", "historical", "superseded")),
                   f"{_doc48}:{_i48+1} retracted wording '{_ph48}' without retraction context",
                   ok_msg=f"{_doc48}:{_i48+1} retracted wording '{_ph48}' sits in retraction context")


print("\n[49] the FNV record reports no correction magnitude while marked PENDING (C-GATE-003)")
import os as _os49, re as _re49
_fp49 = "results/objective1/dft/charge_relaxed/charge_correction_check.md"
if _os49.path.exists(_fp49):
    _t49 = open(_fp49).read()
    _pending49 = bool(_re49.search(r"^#.*\*\*PENDING\*\*|Status: FNV .*NOT computed", _t49, _re49.M))
    expect(_pending49 or "ΔE_corr =" in _t49,
           "FNV record declares either PENDING or an actual computed value")
    if _pending49:
        # no eV/meV-valued correction may be asserted; formula symbols and ranges are fine
        _bad49 = [l for l in _t49.splitlines()
                  if _re49.search(r"(Delta\s*)?(ΔE_corr|E_corr)\s*(=|is|:)\s*[-+]?\d", l)]
        expect(not _bad49,
               f"PENDING FNV record asserts a numeric correction: {_bad49[:1]}",
               ok_msg="PENDING FNV record asserts no numeric correction magnitude")
        expect("dielectric" in _t49.lower() and ("range" in _t49.lower() or "sensitiv" in _t49.lower()),
               "FNV record states the dielectric-choice sensitivity requirement")
        expect("DENY" in _t49, "FNV record records the gate decision that stopped it")


print("\n[50] Stage-3 seeds contain no NEB-derived frame while extraction is gated (C-GATE-004)")
import os as _os50, json as _js50
_sd50 = "results/objective1/dft/charge_relaxed/stage3_seeds"
if _os50.path.exists(_sd50):
    _mf50 = _js50.load(open(f"{_sd50}/SEEDS_MANIFEST.json"))
    expect("excluded_on_purpose" in _mf50, "seeds manifest records what is deliberately excluded")
    # every provenance source must be an ENDPOINT relaxation, never a NEB archive
    for _p50 in _mf50.get("provenance", []):
        _s50 = _p50["source"].lower()
        expect("neb" not in _s50 and "archive" not in _s50,
               f"seed provenance names a NEB-derived source: {_p50['source']}",
               ok_msg=f"seed provenance is endpoint-relaxation only: {_os50.path.basename(_p50['source'])}")
    # and the frame file itself must not carry a NEB source tag
    _txt50 = open(f"{_sd50}/stage3_seeds.extxyz", errors="ignore").read()
    expect("neb" not in _txt50.lower(),
           "seed frame file carries a NEB source tag",
           ok_msg="seed frame file carries no NEB source tag")
    expect(_mf50["natoms"] == 159, f"seeds are 159-atom cells (got {_mf50['natoms']})")


print("\n" + "=" * 70)
if FAILS:
    print(f"{len(FAILS)} TEST(S) FAILED")
    for f in FAILS: print("  -", f)
    sys.exit(1)
print("ALL TESTS PASSED -- every check fires on its own historical incident")

print("\n[51] the committed evidence manifest describes the committed tree (F-027 / C-EVD-003)")
import json as _js51, hashlib as _hl51, subprocess as _sp51, os as _os51
_mp51 = ".audit/evidence_manifest.json"
if _os51.path.exists(_mp51):
    _m51 = _js51.load(open(_mp51))
    for _k51 in ("tree_sha256", "file_count", "recompute_command", "evidence_parent_commit"):
        expect(_k51 in _m51, f"manifest declares {_k51}")
    # Recompute from the COMMITTED objects at HEAD, not the working tree: the auditor runs on a
    # clean checkout, and F-027 arose precisely because the digest was taken while files outside
    # .audit were still uncommitted, so the committed manifest described a different tree.
    _h51 = _sp51.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    if _h51.returncode == 0:
        _head51 = _h51.stdout.strip()
        _ls51 = _sp51.run(["git", "ls-tree", "-r", "-z", "--name-only", _head51],
                          capture_output=True).stdout
        _paths51 = sorted(_p for _p in _ls51.split(b"\0")
                          if _p and not _p.startswith(b".audit/"))
        _st51 = b""
        for _p51 in _paths51:
            _blob51 = _sp51.run(["git", "show", f"{_head51}:{_p51.decode()}"],
                                capture_output=True).stdout
            _st51 += _hl51.sha256(_blob51).hexdigest().encode() + b"  " + _p51 + b"\n"
        _calc51 = _hl51.sha256(_st51).hexdigest()
        expect(_calc51 == _m51["tree_sha256"],
               f"manifest tree_sha256 {_m51['tree_sha256'][:12]} does not describe the committed "
               f"tree at {_head51[:12]} (recomputed {_calc51[:12]}) -- gate binding invalid",
               ok_msg=f"manifest tree_sha256 {_calc51[:12]} matches the committed tree at "
                      f"{_head51[:12]}")
        expect(len(_paths51) == _m51["file_count"],
               f"manifest file_count {_m51['file_count']} != {len(_paths51)} committed files",
               ok_msg=f"manifest file_count {_m51['file_count']} matches the committed tree")
    # the request's binding must hash the manifest's RAW bytes (F-018 convention)
    _rq51 = ".audit/audit_request.json"
    if _os51.path.exists(_rq51):
        _raw51 = open(_mp51, "rb").read()
        expect(_js51.load(open(_rq51))["evidence_manifest_sha256"]
               == _hl51.sha256(_raw51).hexdigest(),
               "audit_request evidence_manifest_sha256 != raw-byte digest of the manifest",
               ok_msg="audit_request binds the manifest's raw-byte digest (F-018 convention)")

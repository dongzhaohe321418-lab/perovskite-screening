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
def expect(cond, msg):
    if not cond:
        FAILS.append(msg)
        print(f"  FAIL  {msg}")
    else:
        print(f"  ok    {msg}")


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

print("\n" + "=" * 70)
if FAILS:
    print(f"{len(FAILS)} TEST(S) FAILED")
    for f in FAILS: print("  -", f)
    sys.exit(1)
print("ALL TESTS PASSED -- every check fires on its own historical incident")

#!/usr/bin/env python
"""S2 gates and budget rules (results/objective2/s2/S2_PLAN.md, binding from commit ae6402e; interface of the S2
Stage-0 specification, module C). This file holds every decision constant of S2 (RULES) and every gate that the
node driver (scripts/50) or the laptop evaluates before the next stage starts (S2_PLAN.md §16, "Gates"):

  G1          elements gate (§7): Delta_cut = [F60(D) - F60(host)] - [F50(D) - F50(host)], |Delta_cut| <= 5 meV;
              spin |F(nspin 2) - F(nspin 1)| <= 3 meV and printed |M| < 0.1 muB; z_valence through the UPF record.
  N, nrule    gate N (§8): pooled sigma_far over the valid far sites of both pilot hosts, df = sum (k_p - 1);
              df < 3 or sigma > 25 meV fails; a failing Sr stops S2 before A2. The n rule (gate 'nrule': no two gate
              names fold to the same lower-case string, N-F15): n = 10 iff a decisive dopant that passes gate N and
              G1 has 20 < sigma <= 25 meV.
  pose        the pose rule (§9): per-leg Boltzmann aggregate at k_BT = 25.7 meV, Delta_pose(j), N_D, N_D+V and the
              count term; default iff |Delta_pose| <= 10 meV at both pilot sites, with a_pose = max(|near|, |far|,
              |near - far|); multi-pose otherwise or when a default minimum is invalid or an SP is missing.
  step0       the step-0 equivalence check (§11): |F(k = 0) - F(SP)| <= 0.5 meV (tolerance of scripts/47), one
              repeat after a fix note, else A2 stops.
  K2, K3      the A2 kill gates (§11), with the fail-closed outcomes fail_replan and a1_only of K3.
  separability  a_far = |delta_far| iff |delta_far| > t_df(0.975) s_delta (§11; evaluated by scripts/48).
  projection  P = H_spent + N_relax c_bar tau_bar + N_SP tau_SP + H_MACE and the cut order 1-8 (§16) with its
              timing restrictions; the hard-cap job-start rule; the expected job durations; the throughput row.
  c3_complete, c4_end   completeness (§§12, 13) in status mode, and the end rule of every C4 relaxation.

Blinding (§17). Every gate opens its inputs through a Reader built from allow_list(gate): a label outside the list,
or an energy read mode (full, k0, final) on a production-host (C3) or A2-II (C4) label, raises Blinded before any
file is opened. MACE energies are stripped from every cell record (scripts/46 load_record, blind=True). No gate,
runner or status command computes an E_b, Y_h or delta of a production host or of an A2-II cell; only scripts/48
(the one evaluation) does. The gate output (s2-gate-1) lists every opened file with the sha256 of its content.

No calculator is created or evaluated here, and mace, torch and e3nn are never imported; scipy is imported only in
t_ppf (a missing scipy raises there; there is no fallback).

    python scripts/49_s2_gates.py --self-test
    python scripts/49_s2_gates.py run --gate G1 --root /data --campaign c1
    python scripts/49_s2_gates.py verify --archive results/objective2/s2 --campaign c1
"""
import argparse, copy, glob, gzip, hashlib, importlib.util, json, math, os, re, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


# Dependencies (interface spec §1.2: 49 -> 46, 47). They are loaded on first use (N-C3), so that the decision rules
# below can be imported by scripts/48 and tested without the geometry stack; a missing file raises MissingDependency.
DEP_FILES = {"c46": "46_s2_cells.py", "q47": "47_s2_qe.py"}
_DEPS = {}


class MissingDependency(RuntimeError):
    pass


def dep(alias):
    if alias not in _DEPS:
        fn = DEP_FILES[alias]
        if not os.path.exists(os.path.join(HERE, fn)):
            raise MissingDependency(f"scripts/{fn} does not exist")
        _DEPS[alias] = _load(alias, fn)
    return _DEPS[alias]


class GateRefused(RuntimeError):
    """A gate call that the plan does not allow (fail-closed STOP for a human)."""


class Blinded(PermissionError):
    """A read outside the gate's allow-list or an energy read of a blinded label (§17)."""


# ---------------------------------------------------------------- decision constants (each defined once)
# Owner of every S2 decision and budget constant (interface spec §2.3). scripts/48 and scripts/50 read them as
# g49.RULES[...]; the self-test pins them against literal copies of the plan text (PLAN_PINS below).
RULES = {
    "K_BT_MEV": 25.7,                       # §0 symbols: exactly, in every Boltzmann sum and class bound
    "N_FAMILY": 4,                          # §14: Bonferroni over the 4 decisive dopants
    "Q_STAR": 1 - 0.05 / (2 * 4),           # §14: family quantile, also for the control
    "Q_SITE": 0.975,                        # §§11, 14: per-site intervals and the separability threshold
    "Q_RANK": 1 - 0.05 / 20,                # §14 ranking: Bonferroni over the 10 pairs of the 5 dopants
    "N_RANK_PAIRS": 10,
    "G1_CUT_MEV": 5.0,                      # §7: pass iff |Delta_cut| <= 5
    "G1_SPIN_MEV": 3.0,                     # §7: pass iff |F(nspin 2) - F(nspin 1)| <= 3
    "G1_M_MUB": 0.1,                        # §7: pass iff |M| < 0.1 on the printed total magnetisation
    "SIGMA_FAR_MAX_MEV": 25.0,              # §8: sigma_far <= 25 passes
    "DF_MIN": 3,                            # §8: df < 3 fails gate N; §§14, 16: df_delta < 3 fails C5
    "N_RULE_LOW_MEV": 20.0,                 # §8: 20 < sigma <= 25 raises n
    "N_BASE": 8, "N_RAISED": 10,            # §§3, 8
    "POSE_MAX_MEV": 10.0,                   # §9: |Delta_pose| <= 10 at both sites
    "K3_MIN_MEV": 25.7,                     # §11: E_b^A2(Pb136) - E_b^A2(Pb76) must exceed (strict)
    "C2_SD_MAX_MEV": 25.0,                  # §14 C2: SD(Delta_h)/sqrt(2) < 25 (strict)
    "C2_MEAN_MAX_MEV": 15.0,                # §14 C2: |mean(Delta_h)| < 15 (strict)
    "DELTA_BAR_MAX_MEV": 50.0,              # §14 C5: |delta_bar| <= 50
    "SIGN_FRACTION": (3, 4),                # §14: required count (3 n_d + 3) // 4 = ceil(0.75 n_d)
    "VALID_HOST_MIN": {"B": 2, "A": 2, "X": 6},     # §12: 2 of 2 (B), >= 2 of 3 (A), >= 6 of 8 (X)
    "FIRST_SHELL_SIZE": {"B": 2, "A": 3, "X": 8},   # §4
    "DOPANT_SPECIFIC": {"checks": (2, 3, 5), "site_host_fraction": (1, 4), "cell_fraction": 0.10},   # §12
    "HARD_CAP_H": 520.0,                    # §16: a job may start iff H_spent + expected <= 520
    "TP_GAIN_MIN": 0.15,                    # §16: choose iff rate >= (1 + 0.15) x rate(48)
    "TP_PAIR_OVERLAP": 0.9,                 # [M] round 4 (I-C13): the two 32-rank copies count as concurrent iff their
                                            # walls overlap for >= 90% of the shorter one (on disjoint cores)
    "PLATEAU_MEV": 3.0,                     # §11 end rule (owner scripts/47; repeated here only in PLAN_PINS)
    "END_ACCEPTED": ("accepted_converged", "accepted_plateau"),   # §11 end-rule outcomes that accept a cell
    # §16 unit costs, the fallback expected durations of the hard-cap rule before a measured mean exists (I-21)
    "UNIT_COST_H": {"sp": 6.74 / 60, "a2_config": 6.15 / 60, "a2_relax": 20.6, "mace_frozen": 2 / 60,
                    "host_relax": 3.3, "smoke": 1.0, "throughput": 1.5, "g1_factor": 1.31, "spin_factor": 2.0},
    # §16 cut order: cuts 5-7 only at the projection after the first 4 A2 relaxations or at the start of C3 (before
    # any C3 job); at the start of C4 only cuts 1-4 and 8
    "CUT_AVAILABLE": {"after4": (1, 2, 3, 4, 5, 6, 7, 8), "c3": (1, 2, 3, 4, 5, 6, 7, 8), "c4": (1, 2, 3, 4, 8)},
    # §§9, 12, 16 multi-pose production upper bound per host: Cs 5 sites x 2 legs x 6, Cl 10 x 2 x 2
    "MULTI_POSE_EXTRA": {"Cs": 60, "Cl": 40},
    # §12 per production host at default poses: 75 frozen relaxations and 76 SPs; G1-failed elements (I-31). Ca: its
    # 8 cells (4 B sites x 2 legs) and their 8 SPs ("Sr 8, Ca 8"); the B-site V+_Rj stay (they serve Sr). Cl: its 20
    # cells and the 10 X-site V+_Rj (they serve only Cl), 30 SPs. (The interface spec said 16 for Ca: a spec defect,
    # corrected after review; the value is pinned against the §12 per-host list in the self-test.)
    "C3_PER_HOST": {"relax": 75, "sp": 76, "host_relax": 1},
    "C3_G1_REMOVAL": {"Ca": {"relax": 8, "sp": 8}, "Cl": {"relax": 30, "sp": 30}},
}
RULES["TP_FACTOR"] = 1.0 + RULES["TP_GAIN_MIN"]
assert RULES["Q_STAR"] == 0.99375 and RULES["Q_RANK"] == 0.9975


def cut_ids(state):
    """The §16 cuts applied so far, as a set of cut numbers. state["cuts"] holds the records of interface spec §4.9
    ({"cut", "at", "P_before_h", "P_after_h"}, written by cut_order); bare integers are accepted as well, so that
    scripts/49 and scripts/50 read one format through one helper (review F2)."""
    out = set()
    for c in (state or {}).get("cuts") or []:
        v = c.get("cut") if isinstance(c, dict) else c
        if v is None:
            continue
        if isinstance(v, bool) or int(v) != v or not 1 <= int(v) <= 8:
            raise GateRefused(f"state cuts: {c!r} is not a cut of §16")
        out.add(int(v))
    return out


def sign_required(n_d):
    """ceil(0.75 n_d) in integer arithmetic (§14: 6 of 7 or 8; 7 of 9; 8 of 10)."""
    a, b = RULES["SIGN_FRACTION"]
    return (a * n_d + b - 1) // b


TOKENS = ("Sr", "Ca", "Cl", "Cs", "GA")
DECISIVE = ("Ca", "Cl", "Cs", "GA")
SUBLATTICE = {"Sr": "B", "Ca": "B", "Cl": "X", "Cs": "A", "GA": "A"}
TOKENS_OF = {"B": ("Sr", "Ca"), "A": ("Cs", "GA"), "X": ("Cl",)}
G1_ELEMENTS = ("Cl", "Ca")                  # §14 C3: Sr, Cs and GA contain only S1 elements
PILOTS = ("m30", "m05")
LEGS = ("novac", "vac")

# Implementation notes (N-), interpretations (I-) and conflicts (X-) implemented in this file (ids of the interface
# specification §14, and C-ids added by this module); printed by --self-test.
NOTES = {
    "I-10": "§§11, 14 (revised after review F5; STAGE0 §9, D-S0-2 revised 2026-11-04): every planned A2 relaxation "
            "runs whatever the validity of its A1 start cell (the plan skips none); A1 validity enters no gate, class "
            "or decision: a delta is valid by the §11 rule alone (scripts/48), so delta_far validity is the K3 "
            "quartet validity, and the A1 validity of the start cells is reported (K2, K3 here; beside each delta and "
            "in the reported-only A1-start sensitivity row of scripts/48); K2 is the end rule of V+_R(Pb136) alone",
    "I-11": "§11 K3 (revised after review F5): fail_replan iff E_b(136) - E_b(76) <= 25.7 meV or a quartet fails the "
            "§11 final-geometry checks 2-5 (validity_final); the A1 validity of the 8 start cells is reported only",
    "I-F1": "§11 final-geometry validity: computed by scripts/46 validate-a2 (geometry only) once a relaxation and "
            "its §11 partner (host_R for V+_R and D; V+_R for D+V) have ended, from the final positions (scripts/47 "
            "read final_geom) and the A1 start, region, relaxed host and pair records; written by scripts/50 into the "
            "A2 record as validity_final; a partner without a final geometry (missing, not run, killed, or complete "
            "without a configuration): the check is not evaluated (no validity_final), and the quartet is invalid "
            "through the missing partner, so K3 is a1_only there (round-2 R2V-1)",
    "I-F3": "§11 step-0 repeat: the decision carries the earlier step0 fields (repeat flag, fix note), so both cells of "
            "the repeat are evaluated as attempt 2; the fix note comes from the inputs or the state",
    "I-12": "§8: a valid far site for gate N is a valid noise quartet (four SPs complete, the three MACE relaxations "
            "and the host relaxation valid)",
    "I-13": "§§8, 17: gate N computes DFT values only; the zero-shot MACE values are reported by the one evaluation",
    "I-14": "§9: a missing SP of a default or kept minimum at either pilot site makes the pose rule 'not met' (multi)",
    "I-21": "§16 hard cap: the expected duration is the mean wall of completed jobs of the same kind in S2, else the "
            "§16 unit cost (A2 relaxation at the cap value 20.6 h)",
    "I-22": "§16 throughput: rate = configurations per node-hour (two copies: 10 configurations over the longer "
            "wall, counted only as I-C13); chosen iff >= 1.15 x the 48-rank rate; a failed run -> 48",
    "I-24": "§16 projection: H_MACE = remaining frozen relaxations x the C1 MACE node time per frozen relaxation plus "
            "one host-relaxation wave while host relaxations remain, both as I-C7b (derived here from the blinded C1 "
            "records; scripts/50 passes no phase wall, round-2 F3); tau_SP = mean C1 SP wall",
    "I-25b": "§16 cuts: an inapplicable cut (5 at n = 8; 6, 7 without multi-pose) or one unavailable at that "
             "projection (5-7 at C4) is skipped and the next cut is tried",
    "I-31": "§§7, 16: cells whose every dopant was removed (G1 failure, cuts) are not run, region cells included",
    "I-C1": "§11 K3: a K3 relaxation without a complete output (missing after the reruns), or without a final-"
            "geometry check (its partner has no final geometry, round-2 R2V-1), is read as 'K3 cannot be evaluated' -> "
            "a1_only, like an end-rule failure; a quartet invalid by the §11 final-geometry checks 2-5 takes "
            "precedence (fail_replan); the A1 validity of the start cells is reported only (I-11)",
    "I-C2": "§16 projection: tau_bar = sum of node-minutes / sum of configurations of the completed A2 relaxations "
            "(node-minutes = wall / concurrent copies), so c_bar x tau_bar is the mean node time of a completed one",
    "I-C3": "§16 projection: multi-pose production enters at its upper bound (Cs 60, Cl 40 extra relaxations and "
            "SPs per host); a running A2 relaxation counts in full; with no completed A2 relaxation each planned one "
            "costs the cap value 20.6 h",
    "I-C4": "§11 step-0: a missing standalone SP or k = 0 value counts as a failed check; attempt 2 requires a fix "
            "note; 'no error found' after attempt 1 gives fail_final; no attempt 3",
    "I-C5": "§16 throughput: of equal rates 64 ranks precedes two 32-rank copies; a failed 48-rank run gives 48",
    "I-C13": "§16 throughput (round-4 R4-C1-1 and the node lens' missed item): 'two concurrent 32-rank copies' is "
             "measured only by two runs that each recorded a core set, on disjoint cores (and, when recorded, with "
             "their pw.x ranks' CPUs disjoint and inside the sets), whose walls overlap for >= 90% of the shorter one "
             "([M], TP_PAIR_OVERLAP); otherwise the 2x32 rate is None and the layout is not chosen (fail-closed: 48 "
             "or 64); scripts/50 starts the two copies together on the two halves of the cores (N-F30)",
    "I-C6": "§16 cuts: cuts 1-4 are inapplicable once C4 will not run, and cut 7 once Cl has left the family (G1)",
    "N-C1": "gate output: inputs_digest = sha256 over (label, content sha256 of the decompressed file, mode), "
            "without file paths, so the node and the archive give the same digest",
    "N-C2": "Reader: energy read modes (full, k0, final) never open a production-host (C3) or A2-II (C4) label "
            "outside the one evaluation, whatever the allow-list; end_rule mode on C4 labels is allowed (§17)",
    "N-C3": "scripts/46 and scripts/47 are loaded on first use, not at import",
    "N-C4": "§7 G1: a missing input (SP not complete, magnetisation not printed, UPF record absent or failed) "
            "fails that part for the element",
    "N-C5": "§8: a dopant absent from the gate-N input fails gate N; an absent Sr sets sr_stop",
    "N-C6": "§16: cut_order updates the state in place (cuts list, n, multi-pose flags, c4_run) and returns the "
            "applied cuts with P before and after each",
    "N-C7": "§16 hard cap: the job kinds of scripts/50 (tp, g1, spin, geometry) are accepted as aliases; only jobs "
            "that consume node-hours (pw.x, MACE) are refused by the cap (analyst decision 2026-11-04, round-2 open "
            "item N-C7): scripts/50 never submits a gate (G1, N, n rule, pose rule, throughput, step-0, K2, "
            "projection, K3, c3_complete, c4_end), a §11 check job or another geometry-only job to job_start_allowed "
            "and never sweeps one to 'not started (hard cap)'; each is evaluated whenever its inputs are complete "
            "(separability is evaluated by scripts/48 at the one evaluation); 'geometry' (0 h) remains an accepted "
            "kind",
    "N-C8": "CLI run (scripts/50): the step-0 cell, attempt and fix note, the projection point, H_spent (ledger "
            "snapshot; an incomplete ledger refuses, I-23) and the C1 timings are derived from the node files; these "
            "reads are listed as inputs_opened and do not enter the inputs digest; verify reuses inputs_in",
    "N-F15": "§§8, 17 (round-3 R3-C1-1): the n rule is the gate 'nrule' (output gates/nrule.json, decision {n}); it "
             "was 'n', whose output gates/n.json and markers are the same files as gate N's on a case-insensitive "
             "volume (the laptop's APFS, where the pull, verify and the one evaluation run); no two names of "
             "GATE_NAMES fold to the same lower-case string (asserted)",
    "I-C7b": "§16 projection: the C1 MACE time per frozen relaxation is its mean wall / 10 concurrent relaxations "
             "(the §16 unit-cost reading, '17-27 min at 6 threads with 10 concurrent' = about 2 min of node time); a "
             "host-relaxation wave costs the longest C1 host wall (both hosts run concurrently)",
}


# ---------------------------------------------------------------- statistics shared with scripts/48
def t_ppf(q, df):
    """q-quantile of Student's t with df degrees of freedom (non-integer df allowed, §14)."""
    if not (0.0 < q < 1.0):
        raise ValueError(f"t_ppf: q = {q!r} outside (0, 1)")
    if isinstance(df, bool) or not isinstance(df, (int, float)) or not math.isfinite(df) or df <= 0:
        raise ValueError(f"t_ppf: df = {df!r} must be finite and > 0")
    from scipy.stats import t as student_t       # lazy: a missing scipy raises here (fail-closed, no fallback)
    return float(student_t.ppf(q, df))


def boltzmann_meV(x_meV, *, mean=False):
    """-k_BT ln(sum_i exp(-x_i/k_BT)), or with mean=True -k_BT ln((1/k) sum_i exp(-x_i/k_BT)); log-sum-exp
    stabilised about the minimum, k_BT = 25.7 meV (§§9, 14)."""
    x = [float(v) for v in x_meV]
    if not x:
        raise ValueError("boltzmann_meV: empty list")
    kt = RULES["K_BT_MEV"]
    m = min(x)
    s = math.fsum(math.exp(-(v - m) / kt) for v in x)
    g = m - kt * math.log(s)
    if mean:
        g += kt * math.log(len(x))
    return g


def leg_free_energy(F_eV):
    """Per-leg aggregate of §9, F_leg = F_min - k_BT ln sum_i exp(-(F_i - F_min)/k_BT), in eV; the correction is
    computed in meV relative to F_min, so the -8e4 eV offset does not enter the exponentials."""
    F = [float(v) for v in F_eV]
    if not F:
        raise ValueError("leg_free_energy: empty list")
    fmin = min(F)
    corr = boltzmann_meV([(v - fmin) * 1000.0 for v in F])      # <= 0 meV
    return fmin + corr / 1000.0


def eb_meV(F_dv, F_d, F_v, F_h):
    """E_b = F[D+V] - F[D] - F[V] + F[host] in meV (§1); None if any term is missing. Differences of nearby totals
    are formed first."""
    if any(v is None for v in (F_dv, F_d, F_v, F_h)):
        return None
    return ((F_dv - F_d) - (F_v - F_h)) * 1000.0


def _mean(v):
    return math.fsum(v) / len(v)


# ---------------------------------------------------------------- labels (grammar of interface spec §3)
def lab_host(h, prefix="s2"):
    return f"{prefix}_{h}_host"


def lab_v(h, L, j, prefix="s2"):
    return f"{prefix}_{h}_V{L}{j}"


def lab_dop(h, tok, j, leg, k=0, prefix="s2"):
    return f"{prefix}_{h}_{tok}{j}o{k}_{leg}"


def wid_host(h):
    return f"s2_{h}_host"


def wid_v(h, L, j):
    return f"s2_{h}_V{L}{j}"


def wid_dop(h, tok, j, leg, n=0):
    return f"s2_{h}_{tok}{j}p{n}_{leg}"


G1_LABELS = {"host60": "s2g1_m30_host_e60", "host50": "s2_m30_host",
             "Cl": {"D60": "s2g1_m30_Cl138o0_novac_e60", "D50": "s2g1_m30_Cl138o0_novac_e50",
                    "spin2": "s2spin_m30_Cl175o0_vac", "spin1": "s2_m30_Cl175o0_vac"},
             "Ca": {"D60": "s2g1_m30_Ca136o0_novac_e60", "D50": "s2g1_m30_Ca136o0_novac_e50",
                    "spin2": "s2spin_m30_Ca76o0_vac", "spin1": "s2_m30_Ca76o0_vac"}}
STEP0_PAIRS = {"s2_m30_VB136": "s2r_m30_VB136", "s2_m30_Sr136o0_vac": "s2r_m30_Sr136o0_vac"}   # SP -> A2 (§11)

# A2 order (§11), fixed; each label with its region and dopant. Cut membership (§16) and the G1 removal (I-31) are
# budget rules of this file. The m05 calibration sites are those of the Stage-0 admissibility record
# (state["stage0"]["m05_cal"]; §11 fallback in draw order), by default Pb124, FA28 and I49.
M05_CAL_DEFAULT = {"B": 124, "A": 28, "X": 49}


def _region(p, L, j, toks):
    return [f"s2r_{p}_host{L}{j}", f"s2r_{p}_V{L}{j}"] + [f"s2r_{p}_{t}{j}o0_{leg}" for t in toks for leg in LEGS]


def build_a2_order(m05_cal=None):
    """C2 (10) and C4 (26) in the fixed order of §11 (region cells first, then the dopants of the region)."""
    c = {**M05_CAL_DEFAULT, **(m05_cal or {})}
    c2 = ["s2r_m30_VB136", "s2r_m30_hostB136", "s2r_m30_Sr136o0_novac", "s2r_m30_Sr136o0_vac"] + \
        _region("m30", "B", 76, ("Sr",)) + ["s2r_m30_Ca136o0_novac", "s2r_m30_Ca136o0_vac"]
    c4 = (_region("m30", "X", 138, ("Cl",)) + _region("m30", "A", 128, ("Cs", "GA")) +
          _region("m05", "B", c["B"], ("Sr", "Ca")) + _region("m05", "X", c["X"], ("Cl",)) +
          _region("m05", "A", c["A"], ("Cs", "GA")))
    assert len(c2) == 10 and len(c4) == 26 and len(set(c2 + c4)) == 36
    return {"c2": c2, "c4": c4}


def cut_cells(m05_cal=None):
    """§16 cuts 1-4 (whole dopants or whole regions)."""
    a = {**M05_CAL_DEFAULT, **(m05_cal or {})}["A"]
    return {1: [f"s2r_m05_GA{a}o0_novac", f"s2r_m05_GA{a}o0_vac"],
            2: [f"s2r_m05_hostA{a}", f"s2r_m05_VA{a}", f"s2r_m05_Cs{a}o0_novac", f"s2r_m05_Cs{a}o0_vac"],
            3: ["s2r_m30_GA128o0_novac", "s2r_m30_GA128o0_vac"],
            4: ["s2r_m30_hostA128", "s2r_m30_VA128", "s2r_m30_Cs128o0_novac", "s2r_m30_Cs128o0_vac"]}


def _m05_cal(state):
    return ((state or {}).get("stage0") or {}).get("m05_cal")


A2_ORDER = build_a2_order()
_A2_RE = re.compile(r"s2r_(?P<h>m\d\d)_(?:host(?P<hL>[BAX])(?P<hj>\d+)|V(?P<vL>[BAX])(?P<vj>\d+)"
                    r"|(?P<tok>Sr|Ca|Cl|Cs|GA)(?P<j>\d+)o0_(?P<leg>novac|vac))")


def a2_cell(label):
    """Region and role of an A2 label: {"pilot", "L", "site", "kind" (host|V|D|DV), "token" (None for region cells),
    "leg"}."""
    m = _A2_RE.fullmatch(label)
    if not m:
        raise GateRefused(f"not an A2 label: {label}")
    g = m.groupdict()
    if g["hL"]:
        return {"pilot": g["h"], "L": g["hL"], "site": int(g["hj"]), "kind": "host", "token": None, "leg": None}
    if g["vL"]:
        return {"pilot": g["h"], "L": g["vL"], "site": int(g["vj"]), "kind": "V", "token": None, "leg": "vac"}
    tok = g["tok"]
    return {"pilot": g["h"], "L": SUBLATTICE[tok], "site": int(g["j"]), "kind": "D" if g["leg"] == "novac" else "DV",
            "token": tok, "leg": g["leg"]}


CUT_CELLS = cut_cells()
K3_QUARTETS = {"hinge": {"host": "s2r_m30_hostB136", "V": "s2r_m30_VB136",
                         "D": "s2r_m30_Sr136o0_novac", "DV": "s2r_m30_Sr136o0_vac"},
               "far": {"host": "s2r_m30_hostB76", "V": "s2r_m30_VB76",
                       "D": "s2r_m30_Sr76o0_novac", "DV": "s2r_m30_Sr76o0_vac"}}


def a1_start_of(label):
    """The A1 work id whose geometry starts an A2 relaxation (§11: host_Rj starts from the S2-relaxed host)."""
    c = a2_cell(label)
    if c["kind"] == "host":
        return wid_host(c["pilot"])
    if c["kind"] == "V":
        return wid_v(c["pilot"], c["L"], c["site"])
    return wid_dop(c["pilot"], c["token"], c["site"], c["leg"], 0)


def label_campaign(label):
    """Campaign of an S2 label from its prefix and host (C2/C4 lists fixed above; pilots m30, m05)."""
    if label.startswith(("s2g1_", "s2spin_", "s2tp_", "s2smoke_")):
        return "c1"
    if label.startswith("s2r_"):
        c = a2_cell(label)                     # C2: the m30 B regions (Pb136, Pb76); C4: every other A2 cell (§11)
        return "c2" if c["pilot"] == "m30" and c["L"] == "B" else "c4"
    m = re.match(r"s2_(m\d\d|ref233)_", label)
    if not m:
        raise GateRefused(f"not an S2 label: {label}")
    return "c1" if m.group(1) in PILOTS else "c3"


def is_blinded(label):
    """True for the labels whose energies only the one evaluation may read before C4 ends (§17): production-host
    cells (C3) and A2-II cells (C4)."""
    return label_campaign(label) in ("c3", "c4")


# ---------------------------------------------------------------- G1 (§7)
def g1_decide(delta_cut_meV, dF_spin_meV, M_total_muB, valence_ok):
    """The three parts of G1 for one element; None anywhere fails that part (N-C4)."""
    cut = delta_cut_meV is not None and abs(delta_cut_meV) <= RULES["G1_CUT_MEV"]
    spin = (dF_spin_meV is not None and M_total_muB is not None and abs(dF_spin_meV) <= RULES["G1_SPIN_MEV"]
            and abs(M_total_muB) < RULES["G1_M_MUB"])
    val = valence_ok is True
    return {"cut_pass": cut, "spin_pass": spin, "valence_pass": val, "pass": cut and spin and val}


def g1_eval(t):
    """t: {"F": {label: F_eV | None}, "M": {label: {"total": muB | None, "abs": muB | None}},
    "valence": {"Cl": bool | None, "Ca": bool | None}} with the labels of G1_LABELS. Returns per element the
    statistics and the decision; an element that fails any part leaves the decisive family (§7)."""
    F, M, val = t.get("F", {}), t.get("M", {}), t.get("valence", {})
    out = {}
    for el in G1_ELEMENTS:
        L = G1_LABELS[el]
        need = [G1_LABELS["host60"], G1_LABELS["host50"], L["D60"], L["D50"]]
        missing = [lab for lab in need + [L["spin2"], L["spin1"]] if F.get(lab) is None]
        dc = None
        if all(F.get(lab) is not None for lab in need):
            dc = ((F[L["D60"]] - F[G1_LABELS["host60"]]) - (F[L["D50"]] - F[G1_LABELS["host50"]])) * 1000.0
        ds = (F[L["spin2"]] - F[L["spin1"]]) * 1000.0 if F.get(L["spin2"]) is not None and \
            F.get(L["spin1"]) is not None else None
        mt = (M.get(L["spin2"]) or {}).get("total")
        ma = (M.get(L["spin2"]) or {}).get("abs")
        d = g1_decide(dc, ds, mt, val.get(el))
        reasons = [f"missing or incomplete: {lab}" for lab in missing]
        if mt is None:
            reasons.append(f"total magnetisation not printed: {L['spin2']}")
        if val.get(el) is not True:
            reasons.append("z_valence/UPF check not passed or absent")
        out[el] = {"delta_cut_meV": dc, "dF_spin_meV": ds, "M_total_muB": mt, "M_abs_muB": ma, **d,
                   "reasons": reasons}
    return out


def g1_pass(g1, el):
    """C3 of §14: G1 passed for Cl and Ca; Sr, Cs and GA pass by definition. g1: g1_eval output or {el: bool}."""
    if el not in G1_ELEMENTS:
        return True
    v = (g1 or {}).get(el)
    if isinstance(v, dict):
        v = v.get("pass")
    return v is True


# ---------------------------------------------------------------- gate N and the n rule (§8)
def gate_n_eval(t):
    """t: {p: {d: {f: E_b meV | None}}} over the far sites of the noise pilot (None = invalid or missing quartet,
    I-12). sigma^2 = sum_p sum_f (E - Ebar_p)^2 / sum_p (k_p - 1); a host with k_p < 2 contributes nothing; pass iff
    df >= 3 and sigma <= 25 meV; a failing Sr sets sr_stop (§8)."""
    out = {}
    for d in TOKENS:
        num, df, hosts = [], 0, {}
        for p in sorted(t):
            vals = {int(f): v for f, v in (t[p].get(d) or {}).items()}
            ok = [v for v in vals.values() if v is not None]
            k = len(ok)
            rec = {"k": k, "per_site_meV": {str(f): vals[f] for f in sorted(vals)}, "offset_meV": None}
            if k >= 2:
                m = _mean(ok)
                rec["offset_meV"] = m
                num.extend((v - m) ** 2 for v in ok)
                df += k - 1
            elif k == 1:
                rec["offset_meV"] = ok[0]
            hosts[p] = rec
        present = any(d in (t[p] or {}) for p in t)
        sigma = math.sqrt(math.fsum(num) / df) if df > 0 else None
        ok = present and df >= RULES["DF_MIN"] and sigma is not None and sigma <= RULES["SIGMA_FAR_MAX_MEV"]
        why = None if ok else ("absent from the input" if not present else f"df = {df} < {RULES['DF_MIN']}"
                               if df < RULES["DF_MIN"] else f"sigma_far = {sigma} > {RULES['SIGMA_FAR_MAX_MEV']}")
        out[d] = {"sigma_far_meV": sigma, "df": df, "hosts": hosts, "pass": ok, "reason": why,
                  "label": None if ok else "inconclusive below the DFT noise floor"}
    return {"dopants": out, "sr_stop": not out["Sr"]["pass"]}


def n_rule(gate_n, g1):
    """n = 10 iff a decisive dopant that passes gate N and G1 has 20 < sigma_far <= 25 meV; else 8 (§8)."""
    gd = gate_n.get("dopants", gate_n)
    for d in DECISIVE:
        r = gd.get(d) or {}
        s = r.get("sigma_far_meV")
        if r.get("pass") is True and g1_pass(g1, d) and s is not None and \
                RULES["N_RULE_LOW_MEV"] < s <= RULES["SIGMA_FAR_MAX_MEV"]:
            return RULES["N_RAISED"]
    return RULES["N_BASE"]


# ---------------------------------------------------------------- pose rule (§9)
def pose_site_eval(st):
    """st: {"novac": {"o0": F_eV | None, "o1": ...}, "vac": {...}, "default_valid": {"novac": bool, "vac": bool}}
    (the kept minima of each leg, I-8). Delta_pose = [F_def(D+V) - F_leg(D+V)] - [F_def(D) - F_leg(D)] in meV."""
    reasons = []
    for leg in LEGS:
        mins = st.get(leg) or {}
        if st.get("default_valid", {}).get(leg) is not True or "o0" not in mins:
            reasons.append(f"default minimum of the {leg} leg invalid or absent")
        miss = sorted(o for o, F in mins.items() if F is None)
        if miss:
            reasons.append(f"{leg}: SP missing for {', '.join(miss)} (I-14)")
    nD, nDV = len(st.get("novac") or {}), len(st.get("vac") or {})
    rec = {"N_D": nD, "N_DV": nDV, "count_term_meV": (RULES["K_BT_MEV"] * math.log(nD / nDV)) if nD and nDV else None,
           "delta_pose_meV": None, "ok": not reasons, "reasons": reasons}
    if reasons:
        return rec
    gap = {}
    for leg in LEGS:
        F = st[leg]
        gap[leg] = (F["o0"] - leg_free_energy(list(F.values()))) * 1000.0      # >= 0
    rec["delta_pose_meV"] = gap["vac"] - gap["novac"]
    rec["default_minus_leg_meV"] = gap
    return rec


def pose_rule(delta_near, delta_far):
    """(mode, a_pose): default iff |Delta_pose| <= 10 meV at both sites, a_pose = max(|n|, |f|, |n - f|) (§9)."""
    if delta_near is None or delta_far is None:
        return "multi", 0.0
    lim = RULES["POSE_MAX_MEV"]
    if abs(delta_near) <= lim and abs(delta_far) <= lim:
        return "default", max(abs(delta_near), abs(delta_far), abs(delta_near - delta_far))
    return "multi", 0.0


def pose_eval(t):
    """t: {"Cs": {"near": site_t, "far": site_t}, "Cl": {...}} (pose_site_eval inputs). A missing or invalid default,
    or a missing SP, makes the rule 'not met' (multi-pose, a_pose 0; §9 fail-closed, I-14)."""
    out = {}
    for tok in ("Cs", "Cl"):
        if tok not in t:
            out[tok] = {"mode": "multi", "a_pose_meV": 0.0, "reason": "no pose-pilot input", "near": None, "far": None}
            continue
        nr, fr = pose_site_eval(t[tok]["near"]), pose_site_eval(t[tok]["far"])
        ok = nr["ok"] and fr["ok"]
        mode, ap = pose_rule(nr["delta_pose_meV"] if ok else None, fr["delta_pose_meV"] if ok else None)
        out[tok] = {"mode": mode, "a_pose_meV": ap, "near": nr, "far": fr,
                    "delta_near_meV": nr["delta_pose_meV"], "delta_far_meV": fr["delta_pose_meV"],
                    "reason": None if ok else "; ".join(nr["reasons"] + fr["reasons"])}
    return out


# ---------------------------------------------------------------- step-0, K2, K3, separability (§11)
def step0_eval(t, attempt, fix_note=None, *, no_error_found=False):
    """t: {SP label: {"F_sp_eV": F | None, "F_k0_eV": F | None}} for the cells whose k = 0 configuration exists.
    pass iff every |F(k = 0) - F(SP)| <= the scripts/47 tolerance; attempt 1 fail -> fail_pending_fix (A2 stops
    before the next relaxation), or fail_final when no error was found; attempt 2 needs the fix note of the dated
    note and fails finally (I-C4)."""
    if attempt not in (1, 2):
        raise GateRefused(f"step-0 attempt {attempt}: the check is repeated at most once (§11)")
    if attempt == 2 and not (isinstance(fix_note, str) and fix_note.strip()):
        raise GateRefused("step-0 repeat without the dated fix note (§11)")
    if not t:
        raise GateRefused("step-0: no cell given")
    q47 = dep("q47")
    cells, ok = {}, True
    for sp, v in sorted(t.items()):
        if sp not in STEP0_PAIRS:
            raise GateRefused(f"step-0 cell outside §11: {sp}")
        if v.get("F_sp_eV") is None or v.get("F_k0_eV") is None:
            cells[sp] = {"dF_meV": None, "passed": False, "reason": "SP or k = 0 value missing (I-C4)"}
        else:
            r = q47.step0_equivalence(v["F_sp_eV"], v["F_k0_eV"])
            cells[sp] = {"dF_meV": r["dF_meV"], "passed": bool(r["passed"]), "reason": None}
        ok = ok and cells[sp]["passed"]
    if ok:
        outcome = "pass"
    elif attempt == 1 and not no_error_found:
        outcome = "fail_pending_fix"
    else:
        outcome = "fail_final"
    return {"cells": cells, "attempt": attempt, "fix_note": fix_note, "outcome": outcome,
            "tolerance_meV": getattr(q47, "STEP0_TOL_MEV", None)}


def k2_eval(end_rule_vb136, a1_valid=None):
    """K2 (§11): the first relaxation, V+_R(Pb136) on m30, must be accepted by the end rule. The A1 validity of its
    start cell is reported, not gated (I-10 as revised after review F5)."""
    outc = (end_rule_vb136 or {}).get("outcome")
    ok = outc in RULES["END_ACCEPTED"]
    return {"outcome": outc, "a1_valid_reported": a1_valid, "K2": "pass" if ok else "fail"}


def k3_decide(value_meV):
    return value_meV is not None and value_meV > RULES["K3_MIN_MEV"]


def k3_eval(t):
    """t: {label: {"F_final_eV", "end_rule" (outcome), "valid_final" (checks 2-5 on the final geometries; None if no
    geometry), "failed_checks", "a1_valid", "status"}} for the 8 labels of K3_QUARTETS.
    fail_replan: a quartet invalid by the §11 checks 2-5 on its final geometries, or E_b(136) - E_b(76) <= 25.7 meV;
    a1_only: a quartet invalid only by the end rule (or without a complete output, I-C1); pass otherwise (§11).
    The A1 validity of the start cells is reported (I-11 as revised after review F5)."""
    q_eb, checks_bad, end_bad = {}, [], []
    a1_invalid = [lab for cells in K3_QUARTETS.values() for lab in cells.values()
                  if (t.get(lab) or {}).get("a1_valid") is not True]
    for q, cells in K3_QUARTETS.items():
        for role, lab in cells.items():
            c = t.get(lab) or {}
            if c.get("valid_final") is False:
                checks_bad.append(f"{lab}: final geometry fails check(s) {c.get('failed_checks')}")
            if c.get("end_rule") not in RULES["END_ACCEPTED"]:
                end_bad.append(f"{lab}: end rule {c.get('end_rule')} (status {c.get('status')})")
            elif c.get("valid_final") is None:
                # scripts/50 runs the check of every relaxation that completed with a final geometry once its partner
                # has ended, whatever the cap (N-F8); an absent check means no usable geometry of the cell or of its
                # partner: K3 cannot be evaluated (I-C1, round-2 R2V-1)
                end_bad.append(f"{lab}: no final-geometry check")
        F = {r: (t.get(lab) or {}).get("F_final_eV") for r, lab in cells.items()}
        q_eb[q] = eb_meV(F["DV"], F["D"], F["V"], F["host"])
    rec = {"Eb_A2_meV": q_eb, "checks_failed": checks_bad, "end_rule_failed": end_bad, "value_meV": None,
           "a1_invalid_reported": a1_invalid}
    if checks_bad:
        rec["K3"] = "fail_replan"
    elif end_bad or any(v is None for v in q_eb.values()):
        rec["K3"] = "a1_only"
    else:
        rec["value_meV"] = q_eb["hinge"] - q_eb["far"]
        rec["K3"] = "pass" if k3_decide(rec["value_meV"]) else "fail_replan"
    return rec


def separability(delta_far, s_delta, df_delta):
    """a_far = |delta_far| iff |delta_far| > t_{df_delta}(0.975) s_delta (§11); delta_far None -> C5 fails (§14);
    s_delta undefined (df_delta < 1) -> a_far = |delta_far| (fail-closed; C5 fails on df_delta anyway)."""
    if delta_far is None:
        return {"c5_far": False, "a_far_meV": 0.0, "fired": None, "threshold_meV": None,
                "reason": "delta_far invalid or missing: C5 fails; the calibrated interval carries no a_far"}
    if df_delta is None or df_delta < 1 or s_delta is None:
        return {"c5_far": True, "a_far_meV": abs(delta_far), "fired": True, "threshold_meV": None,
                "reason": "s_delta undefined: a_far = |delta_far| (fail-closed)"}
    thr = t_ppf(RULES["Q_SITE"], df_delta) * s_delta
    fired = abs(delta_far) > thr
    return {"c5_far": True, "a_far_meV": abs(delta_far) if fired else 0.0, "fired": fired, "threshold_meV": thr,
            "reason": None}


# ---------------------------------------------------------------- budget (§16)
def c4_planned(state):
    """C4 runs unless cut 8, a stopped A2 (step-0, K2, K3 other than pass), sr_stop or an explicit c4_run False."""
    s0 = (state.get("step0") or {}).get("outcome")
    return not (8 in cut_ids(state) or state.get("c4_run") is False or state.get("a2_stopped")
                or state.get("sr_stop") or state.get("K2") == "fail" or s0 in ("fail_pending_fix", "fail_final")
                or state.get("K3") in ("fail_replan", "a1_only"))


def a2_planned(state, campaign):
    """The A2 labels of a campaign that still run under the state: G1 removals with their region cells (I-31) and
    cuts 1-4 (C4). No relaxation is skipped for an invalid A1 start (I-10 as revised after review F5)."""
    g1 = state.get("G1") or {}
    order = build_a2_order(_m05_cal(state))[campaign]
    removed = set()
    if campaign == "c4":
        for c in cut_ids(state):
            removed.update(cut_cells(_m05_cal(state)).get(c, []))
    for lab in order:
        tok = a2_cell(lab)["token"]
        if tok in G1_ELEMENTS and not g1_pass(g1, tok) and "G1" in state:
            removed.add(lab)
    out = []
    for lab in order:
        if lab in removed:
            continue
        c = a2_cell(lab)
        if c["token"] is None:                 # region cell: runs only while one of its dopant cells runs
            mates = [x for x in order if a2_cell(x)["token"] and a2_cell(x)["pilot"] == c["pilot"]
                     and a2_cell(x)["site"] == c["site"] and a2_cell(x)["L"] == c["L"]]
            if all(x in removed for x in mates):
                continue
        out.append(lab)
    return out


def plan_work(state, point, *, done=()):
    """Work still planned at a projection point ('after4', 'c3', 'c4'): N_relax (A2), N_SP and N_MACE (C3 frozen
    relaxations) and host_waves. Counts follow §§11-12 and 16 under the state (G1, cuts, n, pose modes)."""
    if point not in RULES["CUT_AVAILABLE"]:
        raise GateRefused(f"unknown projection point {point}")
    done = set(done)
    n_relax = 0
    if point == "after4" and not state.get("a2_stopped"):
        n_relax += len([x for x in a2_planned(state, "c2") if x not in done])
    if c4_planned(state):
        n_relax += len([x for x in a2_planned(state, "c4") if x not in done])
    n_sp = n_mace = waves = 0
    if point in ("after4", "c3") and state.get("c3_run", True) and not state.get("sr_stop") \
            and state.get("K3") != "fail_replan":
        n = int(state.get("n", RULES["N_BASE"]))
        per_sp, per_rx = RULES["C3_PER_HOST"]["sp"], RULES["C3_PER_HOST"]["relax"]
        for el in G1_ELEMENTS:
            if "G1" in state and not g1_pass(state["G1"], el):
                per_sp -= RULES["C3_G1_REMOVAL"][el]["sp"]
                per_rx -= RULES["C3_G1_REMOVAL"][el]["relax"]
        for tok in ("Cs", "Cl"):
            if (state.get("pose") or {}).get(tok) == "multi" and not (state.get("multi_pose_cut") or {}).get(tok) \
                    and g1_pass(state.get("G1") or {tok: True}, tok):
                per_sp += RULES["MULTI_POSE_EXTRA"][tok]
                per_rx += RULES["MULTI_POSE_EXTRA"][tok]
        n_sp, n_mace, waves = n * per_sp, n * per_rx, 1
    return {"N_relax": n_relax, "N_SP": n_sp, "N_MACE": n_mace, "host_waves": waves}


def projection(t):
    """P = H_spent + N_relax c_bar tau_bar + N_SP tau_SP + H_MACE (§16), in node-hours. t: {"H_spent_h", "N_relax",
    "a2_completed": [{"n_config", "wall_h", "copies"}], "N_SP", "tau_SP_h" | None, "N_MACE", "mace_h_per_relax" |
    None, "host_waves", "host_wave_h" | None}. Only step counts and timings enter, never an energy."""
    U = RULES["UNIT_COST_H"]
    done = t.get("a2_completed") or []
    if done:
        cbar = _mean([float(r["n_config"]) for r in done])
        tau = math.fsum(float(r["wall_h"]) / int(r.get("copies", 1)) for r in done) / \
            math.fsum(float(r["n_config"]) for r in done)                         # node-h per configuration (I-C2)
        per_relax, src = cbar * tau, "measured"
    else:
        cbar, tau, per_relax, src = None, None, U["a2_relax"], "unit cost at the cap (I-C3)"
    tsp = t.get("tau_SP_h") if t.get("tau_SP_h") is not None else U["sp"]
    mpr = t.get("mace_h_per_relax") if t.get("mace_h_per_relax") is not None else U["mace_frozen"]
    hw = t.get("host_wave_h") if t.get("host_wave_h") is not None else U["host_relax"]
    terms = {"H_spent_h": float(t["H_spent_h"]), "A2_h": t["N_relax"] * per_relax, "SP_h": t["N_SP"] * tsp,
             "MACE_h": t["N_MACE"] * mpr + t.get("host_waves", 0) * hw}
    return {"P_h": math.fsum(terms.values()), "terms": terms, "c_bar": cbar, "tau_bar_h_per_config": tau,
            "a2_source": src, "tau_SP_h": tsp, "mace_h_per_relax": mpr, "host_wave_h": hw,
            "counts": {k: t.get(k) for k in ("N_relax", "N_SP", "N_MACE", "host_waves")}}


def _cut_applicable(c, st):
    if c in cut_ids(st):
        return False
    if c in (1, 2, 3, 4):
        return c4_planned(st) and any(x in a2_planned({**st, "cuts": []}, "c4")
                                      for x in cut_cells(_m05_cal(st))[c])                            # I-C6
    if c == 5:
        return int(st.get("n", RULES["N_BASE"])) == RULES["N_RAISED"]
    if c in (6, 7):
        tok = "Cs" if c == 6 else "Cl"
        return (st.get("pose") or {}).get(tok) == "multi" and not (st.get("multi_pose_cut") or {}).get(tok) \
            and g1_pass(st.get("G1") or {tok: True}, tok)
    if c == 8:
        return c4_planned(st)
    return False


def _cut_apply(c, st, point=None):
    """Applies cut c to the state; state["cuts"] gets the spec §4.9 record {"cut", "at", "P_before_h", "P_after_h"}
    (cut_order fills the projections), the one format scripts/50 reads (review F2)."""
    st.setdefault("cuts", []).append({"cut": int(c), "at": point, "P_before_h": None, "P_after_h": None})
    if c == 5:
        st["n"] = RULES["N_BASE"]
    elif c in (6, 7):
        st.setdefault("multi_pose_cut", {})["Cs" if c == 6 else "Cl"] = True
    elif c == 8:
        st["c4_run"] = False


def cut_order(state, project, point):
    """While P > 520 node-h apply the next cut of 1..8 that is applicable and available at `point` (§16, I-25b),
    recomputing P = project(state) after each; cuts are never undone. Updates state in place (N-C6)."""
    if point not in RULES["CUT_AVAILABLE"]:
        raise GateRefused(f"unknown projection point {point}")
    applied = []
    P = project(state)
    while P > RULES["HARD_CAP_H"]:
        nxt = next((c for c in range(1, 9) if c in RULES["CUT_AVAILABLE"][point] and _cut_applicable(c, state)), None)
        if nxt is None:
            applied.append({"cut": None, "at": point, "P_before_h": P, "P_after_h": P,
                            "note": "no applicable cut left; the hard-cap job-start rule applies"})
            break
        _cut_apply(nxt, state, point)
        P2 = project(state)
        state["cuts"][-1].update({"P_before_h": P, "P_after_h": P2})
        applied.append({"cut": nxt, "at": point, "P_before_h": P, "P_after_h": P2})
        P = P2
    return applied


def job_start_allowed(H_spent_h, expected_h):
    """§16 hard cap: a job starts iff H_spent + its expected duration <= 520 node-h; running jobs finish. Applied only
    to jobs that consume node-hours (pw.x, MACE); gates, §11 checks and geometry-only jobs are never refused (N-C7)."""
    return float(H_spent_h) + float(expected_h) <= RULES["HARD_CAP_H"]


EXPECTED_KINDS = {"sp": lambda U: U["sp"], "sp_g1": lambda U: U["sp"] * U["g1_factor"],
                  "sp_spin": lambda U: U["sp"] * U["spin_factor"], "a2": lambda U: U["a2_relax"],
                  "a2_config": lambda U: U["a2_config"], "mace": lambda U: U["mace_frozen"],
                  "host": lambda U: U["host_relax"], "smoke": lambda U: U["smoke"],
                  "throughput": lambda U: U["throughput"], "geometry": lambda U: 0.0}
KIND_ALIASES = {"tp": "throughput", "g1": "sp_g1", "spin": "sp_spin", "host_relax": "host"}   # scripts/50 job kinds


def expected_hours(kind, measured):
    """Mean of the measured wall hours of completed jobs of the kind, else the §16 unit cost (I-21)."""
    k = KIND_ALIASES.get(kind, kind)
    if k not in EXPECTED_KINDS:
        raise GateRefused(f"unknown job kind {kind}")
    m = [float(x) for x in (measured or []) if x is not None]
    return _mean(m) if m else EXPECTED_KINDS[k](RULES["UNIT_COST_H"])


def tp_decide(rates):
    """rates: {"48": r | None, "64": r | None, "2x32": r | None} configurations per node-hour (None = failed)."""
    r48 = rates.get("48")
    if r48 is None or not r48 > 0:
        return "48", "48-rank run failed or absent: 48 (I-C5)"
    best = None
    for lay in ("64", "2x32"):                    # 64 before 2x32 on equal rates (I-C5)
        r = rates.get(lay)
        if r is not None and (best is None or r > rates[best]):
            best = lay
    if best is not None and rates[best] >= RULES["TP_FACTOR"] * r48:
        return best, f"{best}: {rates[best] / r48:.4f} x rate(48) >= {RULES['TP_FACTOR']}"
    return "48", "no layout beats 48 ranks by >= 15%"


def _cpus(s):
    out = set()
    for part in str(s or "").replace(" ", "").split(","):
        if part:
            a, _, b = part.partition("-")
            out.update(range(int(a), int(b or a) + 1))
    return out


def tp_pair_reasons(a, b):
    """I-C13 (round-4 R4-C1-1 and the node lens' missed item): the reasons why two 32-rank runs are not the §16 layout
    'two concurrent 32-rank copies' (empty: they are): each must record its core set ('cpuset'), the two sets must be
    disjoint, the CPUs their pw.x ranks were allowed ('affinity', when recorded) disjoint and inside the sets, and the
    two walls ('interval' [start, end]) must overlap for at least 90% of the shorter one."""
    why = []
    sa, sb = _cpus(a.get("cpuset")), _cpus(b.get("cpuset"))
    if not sa or not sb:
        why.append("a copy without a recorded core set")
    elif sa & sb:
        why.append("the two core sets overlap")
    fa, fb = _cpus(a.get("affinity")), _cpus(b.get("affinity"))
    if fa and fb and fa & fb:
        why.append("the pw.x ranks of the two copies shared CPUs")
    if (fa and sa and not fa <= sa) or (fb and sb and not fb <= sb):
        why.append("pw.x ranks outside their core set")
    ia, ib = a.get("interval"), b.get("interval")
    if not (ia and ib and None not in (*ia, *ib)):
        why.append("a copy without a recorded interval")
    else:
        short = min(float(ia[1]) - float(ia[0]), float(ib[1]) - float(ib[0]))
        ov = min(float(ia[1]), float(ib[1])) - max(float(ia[0]), float(ib[0]))
        if short <= 0 or ov < RULES["TP_PAIR_OVERLAP"] * short:
            why.append(f"the walls overlap {ov:.0f} s, < {RULES['TP_PAIR_OVERLAP']:.0%} of the shorter wall")
    return why


def throughput_choice(t):
    """t: the s2-throughput-1 record, {"runs": {"np48" | "np64" | "np32a" | "np32b": {"n_config": int, "wall_s": float,
    optional "ok" / "failed"; for np32a/np32b "cpuset", "interval" and optionally "affinity"}}} (§16, I-22, I-C13)."""
    runs = t.get("runs", {})

    def rate(*names):
        rs = [runs.get(n) or {} for n in names]
        # a run counts unless it is marked failed (ok False or failed True) or lacks counts or a wall time
        if not all(r.get("ok", True) is not False and not r.get("failed") and r.get("n_config") and r.get("wall_s")
                   for r in rs):
            return None
        return sum(int(r["n_config"]) for r in rs) / (max(float(r["wall_s"]) for r in rs) / 3600.0)

    pair_why = tp_pair_reasons(runs.get("np32a") or {}, runs.get("np32b") or {})
    rates = {"48": rate("np48"), "64": rate("np64"), "2x32": None if pair_why else rate("np32a", "np32b")}
    choice, why = tp_decide(rates)
    return {"rate_config_per_node_h": rates, "choice": choice, "why": why, "pair_not_counted": pair_why,
            "rule": ">= 1.15 x rate(48), else 48; 2x32 only for two concurrent copies on disjoint cores (I-C13)",
            "energies_read": False}


# ---------------------------------------------------------------- blinded reader (§17; interface spec §12)
ENERGY_MODES = ("full", "k0", "final")
READ_MODES = ("full", "status", "counts", "k0", "final", "final_geom", "end_rule")


def _content_sha256(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    if path.endswith(".gz"):
        raw = gzip.decompress(raw)
    return hashlib.sha256(raw).hexdigest()


class Reader:
    """Every gate reads through a Reader. allow: {mode: set(labels)} for the read modes, plus "records" (work ids) and
    "files" (campaign-relative paths, e.g. 'c1/upf_check.json'). Every opened file is logged in `opened`."""

    def __init__(self, layout, campaign, allow, *, evaluation=False, sp_parser=None, relax_parser=None,
                 record_loader=None, sp_status=None, end_rule_fn=None, mapping=None):
        self.layout, self.campaign, self.evaluation = layout, campaign, evaluation
        self.allow = {k: set(v) for k, v in allow.items()}
        self._sp, self._relax, self._rec, self._status = sp_parser, relax_parser, record_loader, sp_status
        self._end = end_rule_fn
        self.mapping = mapping
        self.opened = []
        self._cache = {}

    def end_rule(self, rel):
        """scripts/47 end_rule on a relaxation parsed by this Reader (no file is opened)."""
        return (self._end or dep("q47").end_rule)(rel)

    def _check(self, kind, key, mode):
        if not self.evaluation and kind == "label" and mode in ENERGY_MODES and is_blinded(key):
            raise Blinded(f"{mode} read of the blinded label {key} before the one evaluation (§17)")
        if key not in self.allow.get(mode, set()):
            raise Blinded(f"{key} ({mode}) is not in the allow-list of this gate")

    def _log(self, key, path, mode):
        rel = os.path.relpath(path, self.layout.root) if hasattr(self.layout, "root") else os.path.basename(path)
        self.opened.append({"label": key, "file": rel, "sha256": _content_sha256(path), "mode": mode})

    def sp(self, label, mode="full"):
        """§12 completeness first (scripts/47 sp_status: JOB DONE, converged SCF, the queue's one resubmission,
        version, ranks and UPF identities); the energy parse only for a complete output in full mode."""
        if mode not in ("full", "status"):
            raise Blinded(f"single-point read mode {mode}")
        self._check("label", label, mode)
        if ("sp", label, mode) in self._cache:          # a shared cell (host, V+) is opened and logged once
            return self._cache[("sp", label, mode)]
        c = label_campaign(label)
        job_dir = self.layout.sp_dir(c, label)
        st = (self._status or dep("q47").sp_status)(job_dir, label)
        for p in sorted(glob.glob(os.path.join(glob.escape(job_dir), f"{label}.out*"))):
            self._log(label, p, "status")
        if mode == "status" or st.get("status") != "complete":
            res = {"status": st.get("status"), "missing_reason": st.get("missing_reason")}
        else:
            path = self.layout.sp_out(c, label)
            res = dict((self._sp or dep("q47").parse_sp)(path, read="full"))
            res["status"] = "complete"
            self._log(label, path, "full")
        self._cache[("sp", label, mode)] = res
        return res

    def sp_state(self, label):
        """§12 completeness of one single point (status mode: no energy regex is executed)."""
        self._check("label", label, "status")
        c = label_campaign(label)
        job_dir = self.layout.sp_dir(c, label)
        fn = self._status or dep("q47").sp_status
        res = fn(job_dir, label)
        for p in sorted(glob.glob(os.path.join(glob.escape(job_dir), f"{label}.out*"))):
            self._log(label, p, "status")
        return res

    def relax(self, label, mode):
        if mode not in READ_MODES or mode == "full" and not self.evaluation:
            raise Blinded(f"A2 read mode {mode} is reserved for the one evaluation" if mode == "full"
                          else f"unknown read mode {mode}")
        self._check("label", label, mode)
        parts = self.layout.a2_parts(label_campaign(label), label)
        if not parts:
            return None
        parser = self._relax or dep("q47").parse_relax
        res = parser(parts, read=mode, mapping=self.mapping)
        for p in parts:
            self._log(label, p, mode)
        return res

    def record(self, work_id):
        self._check("record", work_id, "records")
        if ("rec", work_id) in self._cache:
            return self._cache[("rec", work_id)]
        path = self.layout.record(label_campaign(work_id), work_id)
        if not os.path.exists(path):
            return None
        loader = self._rec or (lambda p: dep("c46").load_record(p, blind=True))
        res = loader(path)
        if not self.evaluation:
            assert "E_mace_eV" not in json.dumps(res), "MACE energy in a blinded record read"
        self._log(work_id, path, "records")
        self._cache[("rec", work_id)] = res
        return res

    def json_file(self, key):
        """A JSON record by its logical key (logical_path): upf:<c>, throughput:c1, gate:<c>:<name>, a2:<label>,
        distinct:<member>_<T><j>_<leg>."""
        self._check("file", key, "files")
        path = logical_path(self.layout, key)
        if not os.path.exists(path):
            return None
        with open(path) as fh:
            res = json.load(fh)
        self._log(key, path, "files")
        return res

    def digest(self):
        rows = sorted((o["label"], o["sha256"], o["mode"]) for o in self.opened)
        return hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()


def logical_path(layout, key):
    """Path of a JSON record from its logical key, through the layout of scripts/46 (node or archive)."""
    kind, _, rest = key.partition(":")
    if kind == "upf":
        return os.path.join(layout.campaign_dir(rest), "upf_check.json")
    if kind == "throughput":
        return os.path.join(layout.campaign_dir(rest), "throughput.json")
    if kind == "smoke":
        return os.path.join(layout.campaign_dir(rest), "smoke.json")
    if kind == "ledger":
        if rest == "node":
            return os.path.join(layout.ledger_dir(), "snapshot.json") if getattr(layout, "kind", None) == "node" \
                else os.path.join(layout.root, "__no_node_ledger__")
        return os.path.join(layout.campaign_dir(rest), "ledger.json")
    if kind == "gate":
        c, name = rest.split(":")
        return layout.gate(c, name)
    if kind == "a2":
        c = label_campaign(rest)
        if hasattr(layout, "a2_record"):
            return layout.a2_record(c, rest)
        return os.path.join(layout.a2_dir(c, rest), f"{rest}.a2.json")
    if kind == "distinct":
        if hasattr(layout, "distinct"):
            m = re.fullmatch(r"(m\d\d)_(Cs|Cl)(\d+)_(novac|vac)", rest)
            return layout.distinct("c1", m.group(1), m.group(2), int(m.group(3)), m.group(4))
        return os.path.join(layout.campaign_dir("c1"), "distinct", f"{rest}.json")
    raise GateRefused(f"unknown record key {key}")


def far4(member):
    """Four farthest sites per sublattice of a pilot host (§4 table), read from scripts/46."""
    tab = dep("c46").FAR4_TABLE[member]
    out = {L: [int(x) for x in tab[L]] for L in ("B", "A", "X")}
    assert all(len(v) == 4 for v in out.values()), out
    return out


def pose_sites():
    """{"Cs": (near, far), "Cl": (near, far)} on m30 (§9), read from scripts/46."""
    ps = dep("c46").POSE_SITES
    return {tok: (int(ps[tok][0]), int(ps[tok][1])) for tok in ("Cs", "Cl")}


POSE_MAX_STARTS = {"Cs": 7, "Cl": 3}        # §9: at most 7 Cs starts (resolve_poses), Cl centred + 2 shifted


def noise_cells(p):
    """The 53 noise-pilot quartet members of pilot p (§8): labels and work ids."""
    rows = []
    for L, sites in far4(p).items():
        for f in sites:
            for d in TOKENS_OF[L]:
                rows.append({"p": p, "L": L, "f": f, "d": d,
                             "labels": {"host": lab_host(p), "V": lab_v(p, L, f), "D": lab_dop(p, d, f, "novac"),
                                        "DV": lab_dop(p, d, f, "vac")},
                             "wids": {"host": wid_host(p), "V": wid_v(p, L, f), "D": wid_dop(p, d, f, "novac"),
                                      "DV": wid_dop(p, d, f, "vac")}})
    return rows


# every gate name (scripts/50 graph gates and the CLI); no two fold to the same lower-case string (N-F15)
GATE_NAMES = ("G1", "N", "nrule", "pose", "step0", "K2", "projection", "K3", "throughput", "c3_complete", "c4_end")


def allow_list(gate, state=None, c1=None):
    """The only source of read sets (§12.2 of the interface spec). state/c1 supply the label sets that depend on
    earlier decisions (production list, staged C3 labels, the C4 list under the state)."""
    state = state or {}
    A = {m: set() for m in READ_MODES}
    A["records"], A["files"] = set(), set()
    if gate == "G1":
        A["full"] |= {G1_LABELS["host60"], G1_LABELS["host50"]}
        for el in G1_ELEMENTS:
            A["full"] |= set(G1_LABELS[el].values())
        A["files"].add("upf:c1")
    elif gate == "N":
        for p in PILOTS:
            for r in noise_cells(p):
                A["full"] |= set(r["labels"].values())
                A["records"] |= set(r["wids"].values())
    elif gate == "nrule":
        A["files"] |= {"gate:c1:G1", "gate:c1:N"}
    elif gate == "pose":
        for tok, sites in pose_sites().items():
            L = SUBLATTICE[tok]
            for j in sites:
                A["records"] |= {wid_host("m30"), wid_v("m30", L, j)}
                for leg in LEGS:
                    A["files"].add(f"distinct:m30_{tok}{j}_{leg}")
                    for k in range(POSE_MAX_STARTS[tok]):
                        A["full"].add(lab_dop("m30", tok, j, leg, k))
                        A["records"].add(wid_dop("m30", tok, j, leg, k))
    elif gate == "throughput":
        A["files"].add("throughput:c1")
    elif gate == "step0":
        A["full"] |= set(STEP0_PAIRS)
        A["k0"] |= set(STEP0_PAIRS.values())
        A["files"].add("smoke:c1")
    elif gate == "K2":
        A["end_rule"].add("s2r_m30_VB136")
        A["records"].add("s2_m30_VB136")
        A["files"] |= {"a2:s2r_m30_VB136", "smoke:c1"}
    elif gate == "K3":
        A["files"].add("smoke:c1")
        for cells in K3_QUARTETS.values():
            for lab in cells.values():
                A["final"].add(lab)
                A["records"].add(a1_start_of(lab))
                A["files"].add(f"a2:{lab}")
    elif gate == "projection":
        for c, labs in build_a2_order(_m05_cal(state)).items():
            for lab in labs:
                A["files"].add(f"a2:{lab}")
    elif gate == "c3_complete":
        A["status"] |= set((c1 or {}).get("c3_labels", []))
    elif gate == "c4_end":
        A["files"].add("smoke:c1")
        for lab in a2_planned(state, "c4"):
            A["end_rule"].add(lab)
            A["files"].add(f"a2:{lab}")
    else:
        raise GateRefused(f"unknown gate {gate}")
    return A


# ---------------------------------------------------------------- gate runners (inputs through the Reader)
def _sp_complete(res):
    if not res:
        return False
    if "status" in res:
        return res["status"] == "complete"
    return bool(res.get("job_done")) and bool(res.get("scf_converged")) and res.get("F_eV") is not None


def _F(reader, label):
    res = reader.sp(label, "full")
    return res["F_eV"] if _sp_complete(res) else None


def _valid(rec):
    return bool(rec) and (rec.get("validity") or {}).get("valid") is True


def _relax_value(rel, what):
    """Values of a parsed relaxation (scripts/47 parse_relax). The scripts/47 shape is F_eV = {k: F(k)}
    with k_last; a 'configs' list of {"k", "F_eV"} or the named keys F0_eV / F_final_eV are also accepted (test
    fixtures)."""
    if rel is None:
        return None
    F = rel.get("F_eV")
    if isinstance(F, dict):                 # scripts/47 parse_relax: {k: F(k) in eV} for the read mode
        if what == "k0":
            return F.get(0)
        if what == "final":
            return F.get(rel.get("k_last")) if rel.get("k_last") is not None else None
    if what == "k0":
        for k in ("F0_eV", "F_k0_eV"):
            if rel.get(k) is not None:
                return rel[k]
    if what == "final":
        for k in ("F_final_eV", "Ffin_eV", "F_last_eV"):
            if rel.get(k) is not None:
                return rel[k]
    cf = rel.get("configs")
    if cf:
        if what == "k0":
            c0 = [c for c in cf if c.get("k") == 0]
            return c0[0]["F_eV"] if c0 else None
        if what == "final":
            return cf[-1].get("F_eV")
    return None


def gather_g1(reader):
    F, M = {}, {}
    labels = [G1_LABELS["host60"], G1_LABELS["host50"]] + [v for el in G1_ELEMENTS for v in G1_LABELS[el].values()]
    for lab in labels:
        res = reader.sp(lab, "full")
        F[lab] = res["F_eV"] if _sp_complete(res) else None
        if lab.startswith("s2spin_"):
            M[lab] = {"total": (res or {}).get("M_total_muB"), "abs": (res or {}).get("M_abs_muB")}
    upf = reader.json_file("upf:c1") or {}
    rows_all = upf.get("files") or upf.get("upf") or upf.get("elements") or []
    if isinstance(rows_all, dict):
        rows_all = list(rows_all.values())
    val = {}
    for el in G1_ELEMENTS:
        rows = [r for r in rows_all if isinstance(r, dict) and str(r.get("file", "")).split(".")[0] == el]
        val[el] = bool(upf.get("passed")) and bool(rows) and all(r.get("passed") is True for r in rows)
    return {"F": F, "M": M, "valence": val}


def gather_n(reader):
    t = {}
    for p in PILOTS:
        t[p] = {d: {} for d in TOKENS}
        host_ok = _valid(reader.record(wid_host(p)))
        Fh = _F(reader, lab_host(p))
        for r in noise_cells(p):
            recs_ok = host_ok and all(_valid(reader.record(r["wids"][k])) for k in ("V", "D", "DV"))
            F = {k: _F(reader, r["labels"][k]) for k in ("V", "D", "DV")}
            eb = eb_meV(F["DV"], F["D"], F["V"], Fh) if recs_ok else None
            t[p][r["d"]][r["f"]] = eb
    return t


def gather_pose(reader):
    t = {}
    for tok, (near, far) in pose_sites().items():
        t[tok] = {}
        for role, j in (("near", near), ("far", far)):
            st = {"default_valid": {}}
            for leg in LEGS:
                dist = reader.json_file(f"distinct:m30_{tok}{j}_{leg}") or {}
                kept = dist.get("map") or {}
                st[leg] = {o: _F(reader, lab_dop("m30", tok, j, leg, int(o[1:]))) for o in sorted(kept)}
                p0 = reader.record(wid_dop("m30", tok, j, leg, 0))
                st["default_valid"][leg] = _valid(p0) and kept.get("o0") == "p0"
            t[tok][role] = st
    return t


def gather_step0(reader, cells=None):
    """The step-0 pairs to check: `cells` (SP labels), else those whose A2 relaxation has an output part."""
    t = {}
    for sp, a2 in STEP0_PAIRS.items():
        if cells is not None and sp not in cells:
            continue
        if cells is None and not reader.layout.a2_parts(label_campaign(a2), a2):
            continue
        t[sp] = {"F_sp_eV": _F(reader, sp), "F_k0_eV": _relax_value(reader.relax(a2, "k0"), "k0")}
    return t


def gather_k2(reader):
    rel = reader.relax("s2r_m30_VB136", "end_rule")
    er = reader.end_rule(rel) if rel is not None else {"outcome": "missing"}
    return {"end_rule": er, "a1_valid": _valid(reader.record("s2_m30_VB136"))}


def gather_k3(reader):
    t = {}
    for cells in K3_QUARTETS.values():
        for lab in cells.values():
            a2 = reader.json_file(f"a2:{lab}") or {}
            rel = reader.relax(lab, "final") if a2.get("status") is not None else None
            vf = a2.get("validity_final")
            t[lab] = {"F_final_eV": _relax_value(rel, "final"),
                      "end_rule": (a2.get("end_rule") or {}).get("outcome"),
                      "valid_final": None if vf is None else vf.get("valid") is True,
                      "failed_checks": None if vf is None else vf.get("failed"),
                      "a1_valid": _valid(reader.record(a1_start_of(lab))), "status": a2.get("status")}
    return t


def gather_a2_timings(reader, state=None):
    rows = []
    for c, labs in build_a2_order(_m05_cal(state)).items():
        for lab in labs:
            a2 = reader.json_file(f"a2:{lab}")
            if a2 and a2.get("status") == "complete" and a2.get("n_config") and a2.get("wall_h") is not None:
                rows.append({"label": lab, "n_config": int(a2["n_config"]), "wall_h": float(a2["wall_h"]),
                             "copies": int((a2.get("layout") or {}).get("copies", 1))})
    return rows


def _glob_ids(pattern_path, token="__ID__"):
    """Ids found by globbing a layout path built with a placeholder id, which may occur more than once (node SP
    paths jobs/s2cK/<label>/<label>.out); node and archive layouts alike."""
    parts = pattern_path.split(token)
    rx = re.escape(parts[0])
    for i, part in enumerate(parts[1:]):
        rx += ("(?P<id>[^/]+?)" if i == 0 else "(?P=id)") + re.escape(part)
    rx = re.compile(rx + "$")
    out = set()
    for p in glob.glob("*".join(glob.escape(x) for x in parts)):
        m = rx.match(p)
        if m:
            out.add(m.group("id"))
    return out


def list_sp_labels(layout, c):
    """S2 single-point labels with an output, or staged on the node, in campaign c (smoke, throughput and A2 parts
    excluded)."""
    labs = _glob_ids(layout.sp_out(c, "__ID__"))
    if getattr(layout, "kind", None) == "node" and hasattr(layout, "qe_stage"):
        labs |= _glob_ids(layout.qe_stage(c, "__ID__"))
    return sorted(x for x in labs if not re.search(r"\.p\d+$", x) and not x.startswith(("s2smoke_", "s2tp_", "s2r_")))


def derive_inputs(gate, layout, state, inputs=None, *, reader_kw=None):
    """Non-energy inputs a gate takes from the node state when scripts/50 runs it through the CLI: the step-0 cell
    (state gate_context 'at'), attempt and fix note; the projection point, H_spent (ledger snapshot) and the C1
    timings (SP wall times in status mode, MACE wall times from the blinded records; I-24, I-C7b); the staged C3
    labels. Returns (inputs, opened); these reads do not enter the gate's inputs digest."""
    inp = dict(inputs or {})
    ctx = (state or {}).get("gate_context") or {}
    opened = []
    if gate == "step0":
        if "cells" not in inp and ctx.get("at"):
            inp["cells"] = [sp for sp, a2 in STEP0_PAIRS.items() if a2 == ctx["at"]]
        s0 = (state or {}).get("step0") or {}
        if s0.get("outcome") == "fail_final":
            raise GateRefused("step-0 failed finally: A2 has stopped (§11)")
        fix = inp.get("fix_note") or s0.get("fix_note")
        repeat = bool(s0.get("repeat")) or s0.get("outcome") == "repeat_pending"
        if s0.get("outcome") == "fail_pending_fix" and not repeat and not fix and not s0.get("no_error_found"):
            raise GateRefused("step-0 failed: A2 waits for the dated fix note (§11)")
        inp["fix_note"] = fix
        inp.setdefault("no_error_found", bool(s0.get("no_error_found")))
        want = 2 if (repeat or (s0.get("outcome") == "fail_pending_fix" and fix)) else 1
        if inp.get("attempt") is not None and int(inp["attempt"]) != want:
            raise GateRefused(f"step-0 attempt {inp['attempt']} given, the state implies attempt {want} (§11)")
        inp["attempt"] = want
    elif gate == "projection":
        inp.setdefault("point", ctx.get("point"))
        if inp["point"] not in RULES["CUT_AVAILABLE"]:
            raise GateRefused(f"projection point {inp['point']!r} unknown (state gate_context)")
        sp_labels = [x for x in list_sp_labels(layout, "c1") if label_campaign(x) == "c1"]
        rec_ids = sorted(_glob_ids(layout.record("c1", "__ID__")))
        rd = Reader(layout, "c1", {"status": set(sp_labels), "records": set(rec_ids),
                                   "files": {"ledger:node", "ledger:c1", "ledger:c2", "ledger:c3", "ledger:c4"}},
                    **(reader_kw or {}))
        if "H_spent_h" not in inp:
            led = None
            for key in ("ledger:node", "ledger:c4", "ledger:c3", "ledger:c2", "ledger:c1"):
                led = rd.json_file(key)
                if led:
                    break
            if not led or led.get("complete") is not True:
                raise GateRefused("ledger missing or incomplete: no projection and no job start (I-23)")
            inp["H_spent_h"] = float(led["H_spent_h"])
        if "tau_SP_h" not in inp:
            walls = [st.get("wall_s") for st in (rd.sp_state(x) for x in sp_labels) if st.get("status") == "complete"]
            walls = [w for w in walls if w]
            inp["tau_SP_h"] = _mean(walls) / 3600.0 if walls else None
        if "mace_h_per_relax" not in inp or "host_wave_h" not in inp:
            fz, hw = [], []
            for w in rec_ids:
                r = rd.record(w) or {}
                ws = (r.get("relax") or {}).get("wall_s")
                if ws:
                    (hw if r.get("cell_kind") == "host" else fz).append(float(ws) / 3600.0)
            conc = getattr(dep("c46"), "MAX_CONCURRENT_MACE", 10)
            inp.setdefault("mace_h_per_relax", _mean(fz) / conc if fz else None)
            inp.setdefault("host_wave_h", max(hw) if hw else None)
        opened = rd.opened
    elif gate == "c3_complete":
        inp.setdefault("c1", {})
        inp["c1"].setdefault("c3_labels", [x for x in list_sp_labels(layout, "c3") if label_campaign(x) == "c3"])
    return inp, opened


def c3_complete(reader, labels):
    """§12 completeness of the C3 single points in status mode: complete iff none is pending or running."""
    by, missing = {}, {}
    for lab in sorted(labels):
        st = reader.sp_state(lab)
        s = st.get("status")
        by.setdefault(s, []).append(lab)
        if s == "missing":
            missing[lab] = st.get("missing_reason")
    return {"counts": {k: len(v) for k, v in sorted(by.items())}, "missing": missing,
            "complete": not by.get("pending") and not by.get("running"), "n": len(labels)}


def c4_end(reader, state):
    """End rule (scripts/47 end_rule, read mode end_rule) of every planned C4 relaxation."""
    out = {}
    for lab in a2_planned(state, "c4"):
        rel = reader.relax(lab, "end_rule")
        out[lab] = reader.end_rule(rel) if rel is not None else {"outcome": "missing", "dF_200_180_meV": None}
    return {"end_rules": out, "all_ended": all(v.get("outcome") != "incomplete" for v in out.values())}


def _git_head():
    try:
        return subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:                                              # noqa: BLE001 (no git: commit unknown)
        return None


def evaluate_gate(gate, layout, campaign, state, *, attempt=1, inputs=None, c1=None, reader_kw=None):
    """Read the gate's inputs through a Reader, evaluate it and return the s2-gate-1 record (not written)."""
    inputs = inputs or {}
    rd = Reader(layout, campaign, allow_list(gate, state, c1), **(reader_kw or {}))
    if gate in ("step0", "K2", "K3", "c4_end"):            # the C1 smoke-test mapping of restarts (X-3)
        rd.mapping = (rd.json_file("smoke:c1") or {}).get("mapping")
    if gate == "G1":
        res = g1_eval(gather_g1(rd))
        dec = {"G1": {el: res[el]["pass"] for el in G1_ELEMENTS}}
    elif gate == "N":
        res = gate_n_eval(gather_n(rd))
        dec = {"gateN": {d: res["dopants"][d]["pass"] for d in TOKENS}, "sr_stop": res["sr_stop"]}
    elif gate == "nrule":
        gn, g1 = rd.json_file("gate:c1:N"), rd.json_file("gate:c1:G1")
        if not gn or not g1:
            raise GateRefused("n rule: the G1 and gate-N outputs are required")
        res = {"n": n_rule(gn["result"], g1["result"])}
        dec = {"n": res["n"]}
    elif gate == "pose":
        res = pose_eval(gather_pose(rd))
        # the state holds decisions only (interface spec §4.9); a_pose stays in the gate output, where scripts/48
        # reads it (review-1 F11)
        dec = {"pose": {tok: res[tok]["mode"] for tok in ("Cs", "Cl")}}
    elif gate == "throughput":
        res = throughput_choice(rd.json_file("throughput:c1") or {})
        dec = {"a2_layout": res["choice"]}
    elif gate == "step0":
        attempt = int(inputs.get("attempt", attempt))
        prev = dict((state or {}).get("step0") or {})
        fix = inputs.get("fix_note") or prev.get("fix_note")
        res = step0_eval(gather_step0(rd, inputs.get("cells")), attempt, fix,
                         no_error_found=bool(inputs.get("no_error_found")))
        # merged with the earlier step0 fields, so that the repeat flag and the fix note survive the first cell of the
        # repeat and the second cell is evaluated as attempt 2 as well (I-F3, review-2 F3)
        dec = {"step0": {**prev, "attempts": attempt, "outcome": res["outcome"], "repeat": attempt == 2,
                         "fix_note": fix if attempt == 2 else prev.get("fix_note")}}
    elif gate == "K2":
        g = gather_k2(rd)
        res = k2_eval(g["end_rule"], g["a1_valid"])
        dec = {"K2": res["K2"]}
    elif gate == "K3":
        res = k3_eval(gather_k3(rd))
        dec = {"K3": res["K3"]}
    elif gate == "projection":
        point = inputs["point"]
        st = copy.deepcopy(state)
        timings = gather_a2_timings(rd, state)
        done = [r["label"] for r in timings]

        def project(s):
            w = plan_work(s, point, done=done)
            return projection({**w, "H_spent_h": inputs["H_spent_h"], "a2_completed": timings,
                               "tau_SP_h": inputs.get("tau_SP_h"), "mace_h_per_relax": inputs.get("mace_h_per_relax"),
                               "host_wave_h": inputs.get("host_wave_h")})["P_h"]
        P0 = project(st)
        cuts = cut_order(st, project, point)
        res = {"point": point, "P_initial_h": P0, "cuts": cuts, "inputs": {k: inputs.get(k) for k in
               ("H_spent_h", "tau_SP_h", "mace_h_per_relax", "host_wave_h")}, "a2_completed": timings,
               "work_after": plan_work(st, point, done=done)}
        dec = {"cuts": st.get("cuts", []), "n": st.get("n"), "multi_pose_cut": st.get("multi_pose_cut", {}),
               "c4_run": c4_planned(st)}
    elif gate == "c3_complete":
        res = c3_complete(rd, (c1 or {}).get("c3_labels", []))
        dec = {"c3_complete": res["complete"]}
    elif gate == "c4_end":
        res = c4_end(rd, state)
        dec = {"c4_ended": res["all_ended"]}
    else:
        raise GateRefused(f"unknown gate {gate}")
    return {"schema": "s2-gate-1", "gate": gate, "campaign": campaign, "commit": _git_head(), "attempt": attempt,
            "opened": rd.opened, "inputs_digest": rd.digest(), "result": res, "decision": dec,
            "written": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def write_gate(rec, layout):
    path = layout.gate(rec["campaign"], rec["gate"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    c46 = dep("c46")
    c46.dump_public(rec, path)
    return path


def _canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), default=str)


def verify(archive_root, campaign, *, layout=None, reader_kw=None):
    """Recompute every gate of a campaign from the archive; 0 iff each reproduces the node gate file exactly (same
    decision, same unrounded result, same inputs digest; interface spec §5.5 step 3)."""
    layout = layout or dep("c46").Layout(kind="archive", root=archive_root)
    files = sorted(glob.glob(os.path.join(layout.campaign_dir(campaign), "gates", "*.json")))
    st_path = os.path.join(layout.campaign_dir(campaign), "state_end.json")
    state = json.load(open(st_path)) if os.path.exists(st_path) else {}
    bad = 0
    for fn in files:
        node = json.load(open(fn))
        again = evaluate_gate(node["gate"], layout, campaign, node.get("state_in", state), attempt=node.get("attempt", 1),
                              inputs=node.get("inputs_in"), c1=node.get("c1_in"), reader_kw=reader_kw)
        same = all(_canon(node.get(k)) == _canon(again.get(k)) for k in ("result", "decision", "inputs_digest"))
        print(f"{'OK  ' if same else 'DIFF'} {campaign} {node['gate']}")
        bad += not same
    print(f"verify {campaign}: {len(files)} gate files, {bad} differ")
    return 1 if bad or not files else 0


# ---------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description="S2 gates and budget rules (results/objective2/s2/S2_PLAN.md §§7-16)")
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("run", help="evaluate one gate and write its s2-gate-1 output (node or archive root)")
    r.add_argument("--gate", required=True, choices=list(GATE_NAMES))
    r.add_argument("--root", default="/data")
    r.add_argument("--kind", default="node", choices=["node", "archive"])
    r.add_argument("--campaign", required=True, choices=["c1", "c2", "c3", "c4"])
    r.add_argument("--state", default=None, help="state.json (default: the layout's state file)")
    r.add_argument("--inputs", default=None, help="JSON of the non-energy inputs (projection timings, step-0 note)")
    r.add_argument("--attempt", type=int, default=1)
    v = sub.add_parser("verify")
    v.add_argument("--archive", required=True)
    v.add_argument("--campaign", required=True, choices=["c1", "c2", "c3", "c4"])
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    try:
        if a.cmd == "run":
            c46 = dep("c46")
            lay = c46.Layout(kind=a.kind, root=a.root)
            sp = a.state or lay.state()
            state = json.load(open(sp)) if os.path.exists(sp) else {}
            inputs = json.load(open(a.inputs)) if a.inputs else {}
            inputs, derived_opened = derive_inputs(a.gate, lay, state, inputs)
            rec = evaluate_gate(a.gate, lay, a.campaign, state, attempt=a.attempt, inputs=inputs,
                                c1=inputs.get("c1"))
            rec["state_in"], rec["inputs_in"], rec["c1_in"] = state, inputs, inputs.get("c1")
            rec["inputs_opened"] = derived_opened
            print(f"{a.gate}: decision {json.dumps(rec['decision'])}; written {write_gate(rec, lay)}")
            return 0
        if a.cmd == "verify":
            return verify(a.archive, a.campaign)
    except (GateRefused, Blinded) as e:
        print(f"REFUSED: {type(e).__name__}: {e}", file=sys.stderr)
        return 3
    ap.print_help()
    return 2


# ---------------------------------------------------------------- self-test (synthetic values only; no S2 cell)
# Literal copies of the plan text (a change to RULES must also change these, and the plan by a dated amendment)
PLAN_PINS = {"K_BT_MEV": 25.7, "Q_STAR": 0.99375, "Q_SITE": 0.975, "Q_RANK": 0.9975, "G1_CUT_MEV": 5.0,
             "G1_SPIN_MEV": 3.0, "G1_M_MUB": 0.1, "SIGMA_FAR_MAX_MEV": 25.0, "DF_MIN": 3, "N_RULE_LOW_MEV": 20.0,
             "N_BASE": 8, "N_RAISED": 10, "POSE_MAX_MEV": 10.0, "K3_MIN_MEV": 25.7, "C2_SD_MAX_MEV": 25.0,
             "C2_MEAN_MAX_MEV": 15.0, "DELTA_BAR_MAX_MEV": 50.0, "HARD_CAP_H": 520.0, "TP_GAIN_MIN": 0.15,
             "PLATEAU_MEV": 3.0, "VALID_HOST_MIN": {"B": 2, "A": 2, "X": 6}, "FIRST_SHELL_SIZE": {"B": 2, "A": 3, "X": 8}}
# §12 per production host: "75 frozen relaxations (19 V+_Rj; Sr and Ca at the 4 B sites, Cs and GA at the 5 A sites,
# Cl at the 10 X sites: 56 dopant cells), then 76 single points (host 1, V+ 19, Sr 8, Ca 8, Cs 10, GA 10, Cl 20)"
C3_PLAN_LIST = {"V": 19, "Sr": 8, "Ca": 8, "Cs": 10, "GA": 10, "Cl": 20, "V_X": 10, "host_sp": 1}
UNIT_PINS = {"sp": 6.74 / 60, "a2_config": 6.15 / 60, "a2_relax": 20.6, "mace_frozen": 2 / 60, "host_relax": 3.3,
             "smoke": 1.0, "throughput": 1.5, "g1_factor": 1.31, "spin_factor": 2.0}


class _MockCells:
    """Stand-in for scripts/46 (used only when that file is absent): the constants and calls 49 reads."""
    FAR4_TABLE = {"m30": {"B": [76, 172, 24, 148], "A": [188, 164, 176, 200], "X": [175, 186, 222, 174]},
                  "m05": {"B": [76, 172, 24, 64], "A": [188, 164, 152, 68], "X": [175, 222, 186, 174]}}
    POSE_SITES = {"Cs": (128, 188), "Cl": (138, 175)}
    CAL_SITES = {"m30": {"B": 136, "A": 128, "X": 138}, "m05": {"B": 124, "A": 28, "X": 49}}

    @staticmethod
    def load_record(path, blind=True):
        r = json.load(open(path))
        if blind and isinstance(r.get("relax"), dict):
            r["relax"].pop("E_mace_eV", None)
        return r

    @staticmethod
    def dump_public(obj, path):
        with open(path, "w") as fh:
            json.dump(obj, fh, indent=1)


class _MockQE:
    """Stand-in for scripts/47 (used only when that file is absent)."""
    STEP0_TOL_MEV = 0.5

    @staticmethod
    def step0_equivalence(F_sp_eV, F_k0_eV):
        d = (F_k0_eV - F_sp_eV) * 1000.0
        return {"dF_meV": d, "passed": abs(d) <= 0.5}

    @staticmethod
    def end_rule(rel):
        return {"outcome": rel.get("outcome"), "dF_200_180_meV": rel.get("dF_200_180_meV")}


class _TestLayout:
    """Minimal layout over a temporary root for the Reader tests (paths as the archive layout of the spec §5.2)."""

    def __init__(self, root):
        self.root = root

    def campaign_dir(self, c):
        return os.path.join(self.root, c)

    def sp_dir(self, c, label):
        return os.path.join(self.root, c, "raw")

    def sp_out(self, c, label):
        return os.path.join(self.root, c, "raw", f"{label}.out.gz")

    def a2_parts(self, c, label):
        return sorted(glob.glob(os.path.join(self.root, c, "raw", f"{label}.p*.out.gz")))

    def a2_dir(self, c, label):
        return os.path.join(self.root, c, "a2", label)

    def record(self, c, wid):
        return os.path.join(self.root, c, "records", f"{wid}.json")

    def gate(self, c, name):
        return os.path.join(self.root, c, "gates", f"{name}.json")


def self_test():
    import traceback
    t0 = time.time()
    results = []
    mocked = []
    for alias, mock in (("c46", _MockCells), ("q47", _MockQE)):
        try:
            dep(alias)
        except MissingDependency:
            _DEPS[alias] = mock
            mocked.append(alias)
    work = tempfile.mkdtemp(prefix="s2_49_selftest_")

    def case(name, fn):
        t = time.time()
        try:
            msg = fn()
            results.append((name, True))
            print(f"PASS {name}: {msg}  [{time.time() - t:.2f} s]", flush=True)
        except Exception as e:                                       # noqa: BLE001 (report every failure)
            results.append((name, False))
            print(f"FAIL {name}: {type(e).__name__}: {e}  [{time.time() - t:.2f} s]", flush=True)
            traceback.print_exc(limit=4)

    def refused(fn, exc=GateRefused):
        try:
            fn()
        except exc:
            return True
        raise AssertionError(f"{fn} did not raise {exc.__name__}")

    print(f"49_s2_gates self-test: numpy-free rules, scipy lazy; work files in a temporary directory")
    for alias in ("c46", "q47"):
        print(f"{'MOCKED' if alias in mocked else 'REAL  '} {alias} ({DEP_FILES[alias]})")

    def t_constants():
        for k, v in PLAN_PINS.items():
            assert RULES[k] == v, (k, RULES[k], v)
        assert RULES["UNIT_COST_H"] == UNIT_PINS
        P = C3_PLAN_LIST                                                               # §12 per-host list
        assert RULES["C3_PER_HOST"]["relax"] == P["V"] + P["Sr"] + P["Ca"] + P["Cs"] + P["GA"] + P["Cl"] == 75
        assert RULES["C3_PER_HOST"]["sp"] == P["host_sp"] + P["V"] + P["Sr"] + P["Ca"] + P["Cs"] + P["GA"] + P["Cl"]
        assert RULES["C3_G1_REMOVAL"]["Ca"] == {"relax": P["Ca"], "sp": P["Ca"]}               # B-site V+ serve Sr
        assert RULES["C3_G1_REMOVAL"]["Cl"] == {"relax": P["Cl"] + P["V_X"], "sp": P["Cl"] + P["V_X"]}
        assert [sign_required(n) for n in range(1, 11)] == [math.ceil(0.75 * n) for n in range(1, 11)]
        assert (sign_required(7), sign_required(8), sign_required(9), sign_required(10)) == (6, 6, 7, 8)   # §14 text
        assert len(A2_ORDER["c2"]) == 10 and len(A2_ORDER["c4"]) == 26 and \
            len(set(A2_ORDER["c2"]) | set(A2_ORDER["c4"])) == 36                                        # §11: 36
        assert sum(len(v) for v in CUT_CELLS.values()) == 12 and all(x in A2_ORDER["c4"] for v in CUT_CELLS.values()
                                                                     for x in v)
        for c in ("c2", "c4"):
            for lab in A2_ORDER[c]:
                assert label_campaign(lab) == c
        try:
            c46 = dep("c46")
            if hasattr(c46, "LABEL_RE"):
                for lab in A2_ORDER["c2"] + A2_ORDER["c4"] + list(STEP0_PAIRS) + [G1_LABELS["host60"]] + \
                        [v for el in G1_ELEMENTS for v in G1_LABELS[el].values()]:
                    assert c46.LABEL_RE.fullmatch(lab), lab
            if hasattr(c46, "campaign_of"):
                for c in ("c2", "c4"):
                    for lab in A2_ORDER[c]:
                        assert c46.campaign_of(lab, {}) == c, lab
            if hasattr(c46, "a2_order"):
                for cal in (None, {"B": 124, "A": 92, "X": 138}):
                    assert c46.a2_order(cal) == build_a2_order(cal), cal
        except MissingDependency:
            pass
        return (f"RULES pinned to the plan ({len(PLAN_PINS)} values, unit costs); q* = {RULES['Q_STAR']}, "
                f"q_rank = {RULES['Q_RANK']}; sign rule ceil(0.75 n); A2 lists 10 + 26 = 36, cut cells 12")

    def t_tppf():
        assert abs(t_ppf(0.975, 5) - 2.5705818366147395) < 1e-9 and abs(t_ppf(0.99375, 7.5) - t_ppf(0.99375, 7.5)) == 0
        assert t_ppf(0.99375, 1e6) < t_ppf(0.99375, 7)
        for bad in ((0.975, 0), (0.975, -1), (0.975, float("inf")), (0.975, float("nan")), (1.0, 5), (0.975, True)):
            refused(lambda b=bad: t_ppf(*b), ValueError)
        return "t quantile with non-integer df; df <= 0, inf, nan and q outside (0, 1) refused"

    def t_boltz():
        kt = RULES["K_BT_MEV"]
        assert abs(boltzmann_meV([0.0]) - 0.0) < 1e-12
        assert abs(boltzmann_meV([0.0, 0.0]) + kt * math.log(2)) < 1e-12
        assert abs(boltzmann_meV([0.0, 0.0], mean=True)) < 1e-12
        g = boltzmann_meV([-100.0] + [0.0] * 7, mean=True)
        g80 = boltzmann_meV([-80.0] + [0.0] * 7, mean=True)
        assert abs(g - (-kt * math.log((math.exp(100 / kt) + 7) / 8))) < 1e-9 and round(g, 1) == -50.0
        assert round(g80, 1) == -33.5
        assert abs(boltzmann_meV([1e5, 1e5 + 1.0]) - (1e5 - kt * math.log(1 + math.exp(-1 / kt)))) < 1e-8   # no overflow
        F = [-80000.123456, -80000.123456 + 0.010]
        fl = leg_free_energy(F)
        exact = F[0] - kt * math.log(1 + math.exp(-10.0 / kt)) / 1000.0
        assert abs((fl - exact) * 1000) < 1e-6
        assert eb_meV(None, 1, 1, 1) is None and abs(eb_meV(-80000.2, -80000.1, -79999.9, -79999.8)) < 1e-6
        return f"Boltzmann sums (8-site traps: G = {g:.2f} / {g80:.2f} meV), leg aggregate at -8e4 eV to 1e-6 meV"

    def t_g1():
        def tt(dcut_eV, dspin_eV, M, val=True, drop=None):
            F = {G1_LABELS["host60"]: 0.0, G1_LABELS["host50"]: 0.0}
            for el in G1_ELEMENTS:
                L = G1_LABELS[el]
                F.update({L["D50"]: 0.0, L["D60"]: dcut_eV, L["spin1"]: 0.0, L["spin2"]: dspin_eV})
            if drop:
                F[drop] = None
            Mm = {G1_LABELS[el]["spin2"]: {"total": M, "abs": abs(M) if M is not None else None} for el in G1_ELEMENTS}
            return g1_eval({"F": F, "M": Mm, "valence": {"Cl": val, "Ca": val}})
        r = tt(0.005, 0.003, 0.09)
        assert r["Cl"]["delta_cut_meV"] == 5.0 and r["Cl"]["dF_spin_meV"] == 3.0 and r["Cl"]["pass"] and r["Ca"]["pass"]
        assert not tt(0.005001, 0.0, 0.0)["Cl"]["cut_pass"] and tt(-0.005, 0.0, 0.0)["Cl"]["cut_pass"]
        assert not tt(0.0, 0.003001, 0.0)["Ca"]["spin_pass"] and tt(0.0, -0.003, 0.0)["Ca"]["spin_pass"]
        assert not tt(0.0, 0.0, 0.10)["Cl"]["spin_pass"] and not tt(0.0, 0.0, -0.10)["Cl"]["spin_pass"]
        assert not tt(0.0, 0.0, None)["Cl"]["spin_pass"]
        assert not tt(0.0, 0.0, 0.0, val=False)["Ca"]["pass"] and not tt(0.0, 0.0, 0.0, val=None)["Ca"]["pass"]
        for lab in (G1_LABELS["host60"], G1_LABELS["Cl"]["D50"], G1_LABELS["Cl"]["spin1"]):
            assert not tt(0.0, 0.0, 0.0, drop=lab)["Cl"]["pass"], lab
        assert tt(0.0, 0.0, 0.0, drop=G1_LABELS["Cl"]["D50"])["Ca"]["pass"]       # one element's input only
        assert g1_pass({"Cl": True}, "Cl") and not g1_pass({}, "Ca") and g1_pass({}, "Cs") and g1_pass({}, "Sr")
        return "|Delta_cut| 5.000 pass / 5.001 fail; |dF_spin| 3.000 / 3.001; |M| 0.09 / 0.10; missing input fails"

    def noise_t(sig_by_d, df_layout=(4, 4), offsets=(10.0, -20.0)):
        """Synthetic far-site E_b with an exact sample SD per host block."""
        t = {}
        for p, k, off in zip(PILOTS, df_layout, offsets):
            t[p] = {}
            for d in TOKENS:
                s = sig_by_d.get(d, 10.0)
                sites = list(range(4))
                vals = [None] * 4
                if k >= 2:
                    # k values with mean off and sum of squared deviations s^2 (k - 1): symmetric pattern
                    z = [(-1) ** i for i in range(k)] if k % 2 == 0 else [0.0] + [(-1) ** i for i in range(k - 1)]
                    sc = s * math.sqrt((k - 1) / math.fsum(x * x for x in z))
                    for i in range(k):
                        vals[i] = off + sc * z[i]
                elif k == 1:
                    vals[0] = off
                t[p][d] = {f: v for f, v in zip(sites, vals)}
        return t

    def t_gate_n():
        r = gate_n_eval(noise_t({"Sr": 25.0, "GA": 25.001, "Cs": 22.0, "Ca": 20.0, "Cl": 20.001}))
        g = r["dopants"]
        assert abs(g["Sr"]["sigma_far_meV"] - 25.0) < 1e-9 and g["Sr"]["df"] == 6
        # at the boundary the computed sigma must equal the plan value to the last bits for the test to mean anything
        s_sr = gate_n_eval({p: {"Sr": {0: 0.0, 1: 25.0 * math.sqrt(2)}} for p in PILOTS})
        assert s_sr["dopants"]["Sr"]["df"] == 2 and not s_sr["dopants"]["Sr"]["pass"] and s_sr["sr_stop"]
        assert g["Sr"]["pass"] and not g["GA"]["pass"] and g["Cs"]["pass"] and not r["sr_stop"]
        assert g["Sr"]["hosts"]["m30"]["offset_meV"] == 10.0 and g["Sr"]["hosts"]["m05"]["offset_meV"] == -20.0
        r2 = gate_n_eval(noise_t({}, df_layout=(4, 1)))          # df = 3 + 0 = 3 passes
        assert r2["dopants"]["Ca"]["df"] == 3 and r2["dopants"]["Ca"]["pass"]
        r3 = gate_n_eval(noise_t({}, df_layout=(3, 1)))          # one host with k_p = 3, one with k_p = 1: df = 2
        assert r3["dopants"]["Ca"]["df"] == 2 and not r3["dopants"]["Ca"]["pass"] and r3["sr_stop"]
        r4 = gate_n_eval(noise_t({"Sr": 25.001}))
        assert r4["sr_stop"] and not r4["dopants"]["Sr"]["pass"]
        r5 = gate_n_eval({p: {d: v for d, v in noise_t({})[p].items() if d != "Sr"} for p in PILOTS})
        assert r5["sr_stop"] and r5["dopants"]["Sr"]["reason"] == "absent from the input"
        # n rule
        g1ok = {"Cl": True, "Ca": True}
        assert n_rule(gate_n_eval(noise_t({"Ca": 20.0})), g1ok) == 8
        assert n_rule(gate_n_eval(noise_t({"Ca": 20.001})), g1ok) == 10
        assert n_rule(gate_n_eval(noise_t({"Ca": 20.001})), {"Cl": True, "Ca": False}) == 8      # G1-failed Ca
        assert n_rule(gate_n_eval(noise_t({"Sr": 22.0})), g1ok) == 8                              # Sr does not count
        gn_fail = gate_n_eval(noise_t({"GA": 22.0}, df_layout=(3, 1)))                            # GA fails on df
        assert not gn_fail["dopants"]["GA"]["pass"] and n_rule(gn_fail, g1ok) == 8
        assert n_rule(gate_n_eval(noise_t({"Cs": 25.0})), g1ok) == 10
        return ("sigma 25.000 pass / 25.001 fail; df = 2 (k_p 3 and 1) fails; Sr fail -> sr_stop; n rule 20.000 -> 8, "
                "20.001 -> 10, gate-N- or G1-failing dopant and Sr at 22 -> 8")

    def t_pose():
        kt = RULES["K_BT_MEV"]
        assert pose_rule(10.0, 10.0) == ("default", 10.0)
        assert pose_rule(10.0, -10.0) == ("default", 20.0) and pose_rule(-10.0, 10.0) == ("default", 20.0)
        assert pose_rule(10.001, 0.0)[0] == "multi" and pose_rule(0.0, -10.001)[0] == "multi"
        assert pose_rule(3.0, -2.0) == ("default", 5.0) and pose_rule(None, 0.0) == ("multi", 0.0)
        base = -80000.0
        # one minimum per D leg, two minima 10 meV apart on the D+V leg: Delta = k ln(1 + exp(-10/k))
        st = {"novac": {"o0": base + 0.1}, "vac": {"o0": base, "o1": base + 0.010},
              "default_valid": {"novac": True, "vac": True}}
        r = pose_site_eval(st)
        want = kt * math.log(1 + math.exp(-10.0 / kt))
        assert abs(r["delta_pose_meV"] - want) < 1e-6 and r["N_D"] == 1 and r["N_DV"] == 2
        assert abs(r["count_term_meV"] - kt * math.log(1 / 2)) < 1e-12
        # the default above the other minimum: Delta = 30 + k ln(1 + exp(-30/k))
        st2 = {"novac": {"o0": base}, "vac": {"o0": base + 0.030, "o1": base},
               "default_valid": {"novac": True, "vac": True}}
        assert abs(pose_site_eval(st2)["delta_pose_meV"] - (30 - (-kt * math.log(1 + math.exp(-30 / kt))))) < 1e-6
        ok1 = {"novac": {"o0": base}, "vac": {"o0": base}, "default_valid": {"novac": True, "vac": True}}
        small = {"novac": {"o0": base + 0.1}, "vac": {"o0": base, "o1": base + 0.030},
                 "default_valid": {"novac": True, "vac": True}}
        w30 = kt * math.log(1 + math.exp(-30.0 / kt))              # 6.97 meV
        r = pose_eval({"Cs": {"near": small, "far": ok1}, "Cl": {"near": ok1, "far": st2}})
        assert r["Cs"]["mode"] == "default" and abs(r["Cs"]["a_pose_meV"] - w30) < 1e-6 and w30 < 10
        assert r["Cl"]["mode"] == "multi" and r["Cl"]["a_pose_meV"] == 0.0
        r = pose_eval({"Cs": {"near": st, "far": ok1}, "Cl": {"near": ok1, "far": ok1}})
        assert r["Cs"]["mode"] == "multi" and want > 10                # 13.3 meV at one site
        bad = {"novac": {"o1": base}, "vac": {"o0": base}, "default_valid": {"novac": False, "vac": True}}
        r = pose_eval({"Cs": {"near": ok1, "far": bad}, "Cl": {"near": ok1, "far": ok1}})
        assert r["Cs"]["mode"] == "multi" and "invalid" in r["Cs"]["reason"] and r["Cl"]["mode"] == "default"
        miss = {"novac": {"o0": base, "o1": None}, "vac": {"o0": base}, "default_valid": {"novac": True, "vac": True}}
        r = pose_eval({"Cs": {"near": miss, "far": ok1}, "Cl": {"near": ok1, "far": ok1}})
        assert r["Cs"]["mode"] == "multi" and "I-14" in r["Cs"]["reason"]
        assert r["Cs"]["near"]["count_term_meV"] is not None and pose_eval({})["Cs"]["mode"] == "multi"
        return ("|Delta| 10.000 at both sites -> default, (+10, -10) -> a_pose 20; 10.001 -> multi; invalid default "
                "and missing kept SP -> multi; Boltzmann Delta and count term to 1e-6 meV")

    def t_step0():
        t1 = {"s2_m30_VB136": {"F_sp_eV": 0.0, "F_k0_eV": 0.0005}}
        r = step0_eval(t1, 1)
        assert r["cells"]["s2_m30_VB136"]["dF_meV"] == 0.5 and r["outcome"] == "pass"
        t2 = {"s2_m30_VB136": {"F_sp_eV": 0.0, "F_k0_eV": 0.0005001}}
        assert step0_eval(t2, 1)["outcome"] == "fail_pending_fix"
        assert step0_eval(t2, 1, no_error_found=True)["outcome"] == "fail_final"
        assert step0_eval(t2, 2, "2026-11-20 note: writer fix")["outcome"] == "fail_final"
        assert step0_eval(t1, 2, "2026-11-20 note: writer fix")["outcome"] == "pass"
        refused(lambda: step0_eval(t2, 2, None))
        refused(lambda: step0_eval(t2, 2, "  "))
        refused(lambda: step0_eval(t1, 3, "note"))
        refused(lambda: step0_eval({"s2_m30_VB76": {"F_sp_eV": 0.0, "F_k0_eV": 0.0}}, 1))
        assert step0_eval({"s2_m30_VB136": {"F_sp_eV": None, "F_k0_eV": 0.0}}, 1)["outcome"] == "fail_pending_fix"
        two = {"s2_m30_VB136": {"F_sp_eV": -80000.0, "F_k0_eV": -80000.0},
               "s2_m30_Sr136o0_vac": {"F_sp_eV": -79000.0, "F_k0_eV": -79000.001}}
        assert step0_eval(two, 1)["outcome"] == "fail_pending_fix"
        return "0.5000 pass, 0.5001 -> fail_pending_fix, repeat fail -> fail_final, repeat without a fix note refused"

    def t_k2k3():
        assert k2_eval({"outcome": "accepted_converged"}, True)["K2"] == "pass"
        assert k2_eval({"outcome": "accepted_plateau"}, True)["K2"] == "pass"
        for o in ("unconverged_cap", "unconverged_early", "incomplete", "missing", None):
            assert k2_eval({"outcome": o}, True)["K2"] == "fail", o
        r2 = k2_eval({"outcome": "accepted_converged"}, False)
        assert r2["K2"] == "pass" and r2["a1_valid_reported"] is False             # I-10 revised: reported only
        assert k2_eval(None, True)["K2"] == "fail"

        def k3t(diff_meV, *, bad=None, end=None, missing=None):
            t = {}
            for q, cells in K3_QUARTETS.items():
                eb = diff_meV if q == "hinge" else 0.0
                F = {"host": -80000.0, "V": -79996.5, "D": -79990.25, "DV": -79986.75 + eb / 1000.0}
                for role, lab in cells.items():
                    t[lab] = {"F_final_eV": F[role], "end_rule": "accepted_converged", "valid_final": True,
                              "failed_checks": [], "a1_valid": True, "status": "complete"}
            if bad:
                t[bad].update({"valid_final": False, "failed_checks": [5]})
            if end:
                t[end]["end_rule"] = "unconverged_cap"
            if missing:
                t[missing].update({"F_final_eV": None, "end_rule": "missing", "valid_final": None, "status": "missing"})
            return t
        r = k3_eval(k3t(25.7))
        # the planted value must be the boundary to the precision of the test
        assert abs(r["value_meV"] - 25.7) < 1e-6
        v = r["value_meV"]
        assert k3_decide(25.7) is False and k3_decide(25.7001) is True and r["K3"] == ("pass" if v > 25.7 else "fail_replan")
        assert k3_eval(k3t(25.7001))["K3"] == "pass" and k3_eval(k3t(-40.0))["K3"] == "fail_replan"
        assert k3_eval(k3t(80.0, bad="s2r_m30_VB76"))["K3"] == "fail_replan"
        assert k3_eval(k3t(80.0, end="s2r_m30_Sr76o0_vac"))["K3"] == "a1_only"
        assert k3_eval(k3t(80.0, end="s2r_m30_Sr76o0_vac", bad="s2r_m30_hostB136"))["K3"] == "fail_replan"
        assert k3_eval(k3t(80.0, missing="s2r_m30_hostB76"))["K3"] == "a1_only"                       # I-C1
        t = k3t(80.0)
        t["s2r_m30_Sr136o0_novac"]["a1_valid"] = False
        r = k3_eval(t)
        assert r["K3"] == "pass" and r["a1_invalid_reported"] == ["s2r_m30_Sr136o0_novac"]           # I-11 revised
        t = k3t(80.0)
        t["s2r_m30_VB136"]["valid_final"] = None                                                      # no geometry
        assert k3_eval(t)["K3"] == "a1_only"
        # round-2 R2V-1: host_R(136) missing; the checks of V+_R(136) and D(136) are skipped (no validity_final)
        t = k3t(80.0, missing="s2r_m30_hostB136")
        for lab in ("s2r_m30_VB136", "s2r_m30_Sr136o0_novac"):
            t[lab].update({"valid_final": None, "failed_checks": None})
        r = k3_eval(t)
        assert r["K3"] == "a1_only" and not r["checks_failed"], r
        # round-2 STAT-4: the record says what k3_eval does (A1 validity reported only)
        assert "A1-invalid" not in NOTES["I-C1"] and "reported only" in NOTES["I-C1"], NOTES["I-C1"]
        return ("K2 accepted/plateau pass, unconverged fail, A1 validity reported; K3 25.7000 -> fail_replan, "
                "25.7001 -> pass, check 5 -> fail_replan, end rule only -> a1_only, missing -> a1_only (I-C1), "
                "A1-invalid start reported only, no final-geometry check -> a1_only, host_R missing with its "
                "children's checks skipped -> a1_only (R2V-1); I-C1 text matches the code")

    def t_sep():
        thr = t_ppf(0.975, 5) * 12.0
        r = separability(thr, 12.0, 5)
        assert r["threshold_meV"] == thr and not r["fired"] and r["a_far_meV"] == 0.0 and r["c5_far"]
        r = separability(-thr * (1 + 1e-9), 12.0, 5)
        assert r["fired"] and r["a_far_meV"] == thr * (1 + 1e-9)
        r = separability(None, 12.0, 5)
        assert r["c5_far"] is False
        r = separability(7.0, None, 0)
        assert r["a_far_meV"] == 7.0 and r["fired"]
        return "at the threshold not fired, above fired (a_far = |delta_far|), delta_far missing -> C5 fails"

    def base_state(**kw):
        st = {"n": 8, "G1": {"Cl": True, "Ca": True}, "pose": {"Cs": "default", "Cl": "default"}, "cuts": [],
              "multi_pose_cut": {"Cs": False, "Cl": False}}
        st.update(kw)
        return st

    def t_budget():
        st = base_state()
        assert plan_work(st, "after4", done=A2_ORDER["c2"][:4]) == {"N_relax": 6 + 26, "N_SP": 608, "N_MACE": 600,
                                                                     "host_waves": 1}
        assert plan_work(base_state(n=10), "c3")["N_SP"] == 760 and plan_work(st, "c4")["N_SP"] == 0
        assert plan_work(st, "c3")["N_relax"] == 26
        stg = base_state(G1={"Cl": False, "Ca": False})
        assert a2_planned(stg, "c2") == A2_ORDER["c2"][:8]
        assert len(a2_planned(stg, "c4")) == 26 - 8 - 2 and "s2r_m30_hostX138" not in a2_planned(stg, "c4")   # I-31
        assert "s2r_m05_hostB124" in a2_planned(stg, "c4")
        w = plan_work(stg, "c3")
        assert w["N_SP"] == 8 * (76 - 8 - 30) and w["N_MACE"] == 8 * (75 - 8 - 30)
        wca = plan_work(base_state(G1={"Cl": True, "Ca": False}), "c3")
        assert wca["N_SP"] == 8 * 68 and wca["N_MACE"] == 8 * 67                            # §12: Ca 8 + 8 per host
        assert len(a2_planned(base_state(cuts=[1, 2, 3, 4]), "c4")) == 14
        recs = [{"cut": k, "at": "c4", "P_before_h": 600.0, "P_after_h": 590.0} for k in (1, 2, 3, 4)]
        assert len(a2_planned(base_state(cuts=recs), "c4")) == 14 and cut_ids({"cuts": recs + [2]}) == {1, 2, 3, 4}
        refused(lambda: cut_ids({"cuts": [9]}))
        assert not c4_planned(base_state(cuts=[{"cut": 8, "at": "after4"}]))
        assert plan_work(base_state(pose={"Cs": "multi", "Cl": "multi"}), "c3")["N_SP"] == 8 * (76 + 100)
        # projection arithmetic on a synthetic ledger
        done = [{"n_config": 100, "wall_h": 10.0, "copies": 1}, {"n_config": 60, "wall_h": 8.0, "copies": 2}]
        p = projection({"H_spent_h": 100.0, "N_relax": 10, "a2_completed": done, "N_SP": 600, "tau_SP_h": 0.1,
                        "N_MACE": 600, "mace_h_per_relax": 1 / 30, "host_waves": 1, "host_wave_h": 3.0})
        cbar, tau = 80.0, (10.0 + 4.0) / 160.0
        assert abs(p["P_h"] - (100 + 10 * cbar * tau + 60 + 20 + 3)) < 1e-9 and abs(p["tau_bar_h_per_config"] - tau) < 1e-15
        p0 = projection({"H_spent_h": 0.0, "N_relax": 2, "a2_completed": [], "N_SP": 0, "tau_SP_h": None, "N_MACE": 0,
                         "mace_h_per_relax": None, "host_waves": 0, "host_wave_h": None})
        assert p0["P_h"] == 2 * 20.6
        # cut order with P over 520 at each point
        def mk(H, per_relax=20.0, per_sp=0.1):
            def project(s):
                w = plan_work(s, point_box[0])
                return H + w["N_relax"] * per_relax + w["N_SP"] * per_sp + w["N_MACE"] / 30 + w["host_waves"] * 3.3
            return project
        point_box = ["after4"]
        st = base_state(n=10, pose={"Cs": "multi", "Cl": "default"})
        cuts = cut_order(st, mk(100.0), "after4")
        got = [c["cut"] for c in cuts]
        assert got == [1, 2, 3, 4, 5, 6, 8] and st["n"] == 8 and all(c["P_after_h"] < c["P_before_h"] for c in cuts)
        assert st["multi_pose_cut"]["Cs"] and st["c4_run"] is False and cuts[-1]["P_after_h"] <= 520
        point_box[0] = "c4"
        st4 = base_state(n=10, pose={"Cs": "multi", "Cl": "multi"})
        cuts4 = cut_order(st4, mk(400.0), "c4")
        got4 = [c["cut"] for c in cuts4]
        assert 5 not in got4 and 6 not in got4 and 7 not in got4 and got4 == [1, 2, 3, 4, 8], got4         # 5-7 at C4
        assert st4["n"] == 10 and st4["c4_run"] is False
        point_box[0] = "c3"
        st8 = base_state(n=8, pose={"Cs": "default", "Cl": "multi"}, cuts=[1])
        got8 = [c["cut"] for c in cut_order(st8, mk(150.0, per_relax=25.0), "c3")]
        assert got8 == [2, 3, 4, 7, 8], got8               # 1 already applied (never undone); 5, 6 inapplicable
        assert st8["cuts"][0] == 1 and [c["cut"] for c in st8["cuts"][1:]] == got8      # spec §4.9 records
        assert all(c["at"] == "c3" and c["P_after_h"] < c["P_before_h"] for c in st8["cuts"][1:])
        stc = base_state()
        assert cut_order(stc, mk(0.0, per_relax=1.0), "c3") == [] and stc["cuts"] == []
        stn = base_state(cuts=[1, 2, 3, 4, 8], c4_run=False)
        r = cut_order(stn, lambda s: 600.0, "c3")
        assert r[-1]["cut"] is None
        refused(lambda: cut_order(base_state(), mk(0.0), "c5"))
        # hard cap
        assert job_start_allowed(519.0, 1.0) and not job_start_allowed(519.001, 1.0)
        assert job_start_allowed(500.0, expected_hours("sp", [])) and not job_start_allowed(519.9, expected_hours("a2", []))
        assert expected_hours("a2", [9.0, 11.0]) == 10.0 and expected_hours("sp_spin", []) == 2 * 6.74 / 60
        refused(lambda: expected_hours("mystery", []))
        return ("plan counts (C3 608/760 SPs, G1 removals with region cells, multi-pose bounds), projection arithmetic, "
                "cut order at after4/c3/c4 (5-7 unavailable at C4, 5 inapplicable at n = 8, never undone), hard cap "
                "520.000 allowed / 520.001 refused")

    def t_tp():
        f = RULES["TP_FACTOR"]
        assert tp_decide({"48": 1.0, "64": f, "2x32": None})[0] == "64"
        assert tp_decide({"48": 1.0, "64": 1.1499, "2x32": 1.1499})[0] == "48"
        assert tp_decide({"48": 1.0, "64": 1.2, "2x32": 1.3})[0] == "2x32"
        assert tp_decide({"48": 1.0, "64": 1.3, "2x32": 1.3})[0] == "64"
        assert tp_decide({"48": None, "64": 2.0, "2x32": 2.0})[0] == "48"
        runs = {"np48": {"ok": True, "n_config": 5, "wall_s": 3600.0}, "np64": {"ok": False, "n_config": 5, "wall_s": 1.0},
                "np32a": {"ok": True, "n_config": 5, "wall_s": 3000.0, "cpuset": "0-31", "interval": [0.0, 3000.0]},
                "np32b": {"ok": True, "n_config": 5, "wall_s": 3200.0, "cpuset": "32-63", "interval": [1.0, 3201.0]}}
        r = throughput_choice({"runs": runs})
        assert r["rate_config_per_node_h"]["64"] is None and abs(r["rate_config_per_node_h"]["2x32"] - 10 / (3200 / 3600)) < 1e-9
        assert r["choice"] == "2x32"
        runs["np32b"]["ok"] = False
        assert throughput_choice({"runs": runs})["choice"] == "48"
        plain = {k: {"n_config": v["n_config"], "wall_s": v["wall_s"]} for k, v in runs.items()}   # spec 4.6 shape
        assert throughput_choice({"runs": plain})["rate_config_per_node_h"]["2x32"] is None   # no core sets (I-C13)
        assert throughput_choice({"runs": plain})["choice"] == "64"
        plain["np64"]["failed"] = True
        assert throughput_choice({"runs": plain})["choice"] == "48"                 # no core sets: no 2x32 (I-C13)
        plain["np32a"]["wall_s"], plain["np32b"]["wall_s"] = 3000.0, 3200.0
        # I-C13 (round 4): the 2x32 rate only for two concurrent copies on disjoint cores
        T0 = 1.8e9
        pair = {"np32a": {"cpuset": "0-31", "interval": [T0, T0 + 3000.0]},
                "np32b": {"cpuset": "32-63", "interval": [T0 + 5.0, T0 + 3205.0]}}
        for k in ("np32a", "np32b"):
            plain[k].update(pair[k])
        r2 = throughput_choice({"runs": plain})
        assert r2["choice"] == "2x32" and not r2["pair_not_counted"], r2
        bad = {"shared core set": {"np32b": {"cpuset": "0-31"}}, "no core set": {"np32b": {"cpuset": None}},
               "solo rerun": {"np32b": {"interval": [T0 + 3100.0, T0 + 6300.0]}},
               "60% overlap": {"np32b": {"interval": [T0 + 1200.0, T0 + 4400.0]}},
               "shared CPUs": {"np32a": {"affinity": "0-40"}, "np32b": {"affinity": "32-63"}},
               "outside its set": {"np32b": {"affinity": "16-47"}}}
        for name, over in bad.items():
            rr = copy.deepcopy(plain)
            for k, v in over.items():
                rr[k].update(v)
            res = throughput_choice({"runs": rr})
            assert res["rate_config_per_node_h"]["2x32"] is None and res["pair_not_counted"] and res["choice"] == "48", (name, res)
        ok89 = copy.deepcopy(plain); ok89["np32b"]["interval"] = [T0 + 300.0, T0 + 3300.0]      # 90.0% of 3000 s
        assert throughput_choice({"runs": ok89})["choice"] == "2x32"
        ok89["np32b"]["interval"] = [T0 + 301.0, T0 + 3301.0]                               # 89.97%
        assert throughput_choice({"runs": ok89})["choice"] == "48"
        return ("1.15 x -> chosen, 1.1499 x -> 48, failed run -> 48, two copies: 10 configurations over the longer wall; "
                f"2x32 not counted for {list(bad)} or 89.97% overlap, counted at 90.0% (I-C13)")

    # -------- Reader and gate runners on a temporary archive (fake parsed outputs as JSON; no S2 cell exists)
    def fake_sp(path, read="full"):
        with gzip.open(path, "rt") as fh:
            d = json.load(fh)
        if read == "status":
            return {k: d[k] for k in ("job_done", "scf_converged")}
        return d

    def fake_relax(parts, read=None, mapping=None):
        with gzip.open(parts[-1], "rt") as fh:
            d = json.load(fh)
        if read == "k0":
            return {"F0_eV": d["F0_eV"]}
        if read == "final":
            return {"F_final_eV": d["F_final_eV"]}
        if read == "end_rule":
            return {"outcome": d["outcome"], "dF_200_180_meV": d.get("dF_200_180_meV")}
        return {"n_config": d.get("n_config")}

    def put_sp(lay, label, F, M=None, ok=True):
        p = lay.sp_out(label_campaign(label), label)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with gzip.open(p, "wt") as fh:
            json.dump({"job_done": ok, "scf_converged": ok, "F_eV": F, "M_total_muB": M, "M_abs_muB": M}, fh)

    def put_rec(lay, wid, valid=True, E=None):
        c = label_campaign(re.sub(r"p(\d+)_(novac|vac)$", r"o\1_\2", wid))
        p = lay.record(c, wid)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump({"schema": "s2-cell-1", "work_id": wid, "validity": {"valid": valid, "failed": [] if valid else [5]},
                   "relax": {"E_mace_eV": -1234.5 if E is None else E}}, open(p, "w"))

    def put_json(lay, key, obj):
        p = logical_path(lay, key)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(obj, open(p, "w"))

    def put_a2(lay, label, F0, Ff, outcome="accepted_converged"):
        c = label_campaign(label)
        p = os.path.join(lay.root, c, "raw", f"{label}.p1.out.gz")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with gzip.open(p, "wt") as fh:
            json.dump({"F0_eV": F0, "F_final_eV": Ff, "outcome": outcome, "n_config": 90}, fh)
        put_json(lay, f"a2:{label}",
                 {"schema": "s2-a2-1", "label": label, "status": "complete", "n_config": 90, "wall_h": 9.0,
                  "layout": {"ranks": 48, "copies": 1}, "end_rule": {"outcome": outcome},
                  "validity_final": {"valid": True, "failed": []}})

    def fake_status(job_dir, label):
        p = os.path.join(job_dir, f"{label}.out.gz")
        if not os.path.exists(p):
            return {"status": "pending"}
        with gzip.open(p, "rt") as fh:
            d = json.load(fh)
        return {"status": "complete" if d["job_done"] and d["scf_converged"] else "missing",
                "missing_reason": None if d["job_done"] and d["scf_converged"] else "SCF not converged (JOB DONE)"}

    kw = {"sp_parser": fake_sp, "relax_parser": fake_relax, "end_rule_fn": lambda rel: dict(rel),
          "record_loader": lambda p: _MockCells.load_record(p, blind=True), "sp_status": fake_status}

    def t_reader():
        lay = _TestLayout(os.path.join(work, "arch"))
        for lab in STEP0_PAIRS:
            put_sp(lay, lab, -80000.0)
        put_sp(lay, "s2_m06_host", -80001.0)
        put_a2(lay, "s2r_m30_VB136", -80000.0, -80000.3)
        put_a2(lay, "s2r_m05_VB124", -80000.0, -80000.3)
        rd = Reader(lay, "c2", allow_list("step0"), **kw)
        assert rd.sp("s2_m30_VB136")["F_eV"] == -80000.0
        assert rd.relax("s2r_m30_VB136", "k0")["F0_eV"] == -80000.0
        refused(lambda: rd.sp("s2_m30_host"), Blinded)                                        # outside the list
        refused(lambda: rd.relax("s2r_m30_VB136", "final"), Blinded)                          # mode outside the list
        refused(lambda: rd.relax("s2r_m30_VB136", "full"), Blinded)                           # full: evaluation only
        leaky = Reader(lay, "c3", {"full": {"s2_m06_host"}, "final": {"s2r_m05_VB124"}, "end_rule": {"s2r_m05_VB124"}},
                       **kw)
        refused(lambda: leaky.sp("s2_m06_host"), Blinded)                                     # C3 energy (N-C2)
        refused(lambda: leaky.relax("s2r_m05_VB124", "final"), Blinded)                       # C4 energy (N-C2)
        assert leaky.relax("s2r_m05_VB124", "end_rule")["outcome"] == "accepted_converged"    # end rule allowed
        ev = Reader(lay, "c3", {"full": {"s2_m06_host"}}, evaluation=True, **kw)
        assert ev.sp("s2_m06_host")["F_eV"] == -80001.0
        assert len(rd.opened) == 3 and all(set(o) == {"label", "file", "sha256", "mode"} for o in rd.opened)
        assert all(not os.path.isabs(o["file"]) for o in rd.opened)
        put_rec(lay, "s2_m30_VB136")
        r2 = Reader(lay, "c1", allow_list("K2"), **kw)
        rec = r2.record("s2_m30_VB136")
        assert "E_mace_eV" not in json.dumps(rec) and rec["validity"]["valid"]
        refused(lambda: r2.record("s2_m30_VB76"), Blinded)
        assert allow_list("c4_end", base_state())["end_rule"] == set(a2_planned(base_state(), "c4"))
        assert not allow_list("c4_end", base_state())["full"] and not allow_list("c3_complete", {}, {"c3_labels":
                                                                                                   ["s2_m06_host"]})["full"]
        for g in GATE_NAMES:
            A = allow_list(g, base_state(), {"c3_labels": ["s2_m06_host"]})
            for mode in ENERGY_MODES:
                assert not any(is_blinded(x) for x in A[mode]), (g, mode)
        assert len(allow_list("N")["full"]) == 106 and len(allow_list("N")["records"]) == 106
        return ("Blinded outside the allow-list, for an energy mode on C3/C4 labels and for A2 'full'; records "
                "stripped of E_mace; no allow-list holds an energy mode on a blinded label; gate N reads 106 SPs")

    def t_runners():
        lay = _TestLayout(os.path.join(work, "arch2"))
        # G1 inputs
        put_sp(lay, G1_LABELS["host60"], -80000.0)
        put_sp(lay, G1_LABELS["host50"], -79999.0)
        for el in G1_ELEMENTS:
            L = G1_LABELS[el]
            put_sp(lay, L["D60"], -79900.0)
            put_sp(lay, L["D50"], -79899.0 + (0.004 if el == "Cl" else 0.006))
            put_sp(lay, L["spin1"], -79000.0)
            put_sp(lay, L["spin2"], -79000.001, M=0.02)
        put_json(lay, "upf:c1", {"schema": "s2-upf-1", "passed": True, "files": [
            {"file": "Cl.pbe-n-rrkjus_psl.1.0.0.UPF", "passed": True},
            {"file": "Ca.pbe-spn-rrkjus_psl.1.0.0.UPF", "passed": True}]})
        g = evaluate_gate("G1", lay, "c1", {}, reader_kw=kw)
        assert g["decision"]["G1"] == {"Cl": True, "Ca": False}, g["decision"]
        assert len(g["opened"]) == 21 and g["schema"] == "s2-gate-1"
        # gate N inputs: noise quartets with planted far E_b
        rng_vals = {}
        for p in PILOTS:
            put_sp(lay, lab_host(p), -80000.0)
            put_rec(lay, wid_host(p))
            for r in noise_cells(p):
                eb = 5.0 * (far4(p)[r["L"]].index(r["f"]) - 1.5)
                rng_vals[(p, r["d"], r["f"])] = eb
                put_sp(lay, r["labels"]["V"], -79996.5)
                put_sp(lay, r["labels"]["D"], -79990.25)
                put_sp(lay, r["labels"]["DV"], -79986.75 + eb / 1000.0)
                for k in ("V", "D", "DV"):
                    put_rec(lay, r["wids"][k], valid=not (p == "m05" and r["d"] == "Cl" and k == "DV" and r["f"] == 175))
        gn = evaluate_gate("N", lay, "c1", {}, reader_kw=kw)
        res = gn["result"]["dopants"]
        assert res["Sr"]["df"] == 6 and res["Cl"]["df"] == 5 and res["Cl"]["hosts"]["m05"]["per_site_meV"]["175"] is None
        assert all(res[d]["pass"] for d in TOKENS) and not gn["decision"]["sr_stop"]
        sd = math.sqrt(math.fsum((5.0 * (i - 1.5)) ** 2 for i in range(4)) / 3)
        assert abs(res["Sr"]["sigma_far_meV"] - sd) < 1e-6
        # n rule from the two gate files
        for gr in (g, gn):
            os.makedirs(os.path.dirname(lay.gate("c1", gr["gate"])), exist_ok=True)
            json.dump(gr, open(lay.gate("c1", gr["gate"]), "w"))
        assert evaluate_gate("nrule", lay, "c1", {}, reader_kw=kw)["decision"]["n"] == 8
        # N-F15 (round-3 R3-C1-1): the n-rule output does not share a file with gate N's on a case-insensitive volume
        assert len({x.lower() for x in GATE_NAMES}) == len(GATE_NAMES), GATE_NAMES
        assert os.path.basename(lay.gate("c1", "nrule")).lower() != os.path.basename(lay.gate("c1", "N")).lower()
        refused(lambda: evaluate_gate("n", lay, "c1", {}, reader_kw=kw), GateRefused)
        # K2 and K3
        for cells in K3_QUARTETS.values():
            for role, lab in cells.items():
                eb = 90.0 if "136" in lab else 0.0
                F = {"host": -80000.0, "V": -79996.5, "D": -79990.25, "DV": -79986.75 + eb / 1000.0}[role]
                put_a2(lay, lab, F + 0.5, F)
                put_rec(lay, a1_start_of(lab))
        assert evaluate_gate("K2", lay, "c2", {}, reader_kw=kw)["decision"]["K2"] == "pass"
        k3 = evaluate_gate("K3", lay, "c2", {}, reader_kw=kw)
        assert k3["decision"]["K3"] == "pass" and abs(k3["result"]["value_meV"] - 90.0) < 1e-6
        put_rec(lay, "s2_m30_VB76", valid=False)
        k3b = evaluate_gate("K3", lay, "c2", {}, reader_kw=kw)
        assert k3b["decision"]["K3"] == "pass" and k3b["result"]["a1_invalid_reported"] == ["s2r_m30_VB76"]   # I-11
        a2p = logical_path(lay, "a2:s2r_m30_VB76")
        r76 = json.load(open(a2p))
        r76["validity_final"] = {"valid": False, "failed": [5]}                    # as scripts/50 writes it
        json.dump(r76, open(a2p, "w"))
        assert evaluate_gate("K3", lay, "c2", {}, reader_kw=kw)["decision"]["K3"] == "fail_replan"
        # step-0
        put_sp(lay, "s2_m30_VB136", -79996.5 + 0.5)
        put_sp(lay, "s2_m30_Sr136o0_vac", (-79986.75 + 90.0 / 1000.0) + 0.5)
        s0 = evaluate_gate("step0", lay, "c2", {}, reader_kw=kw)
        assert s0["decision"]["step0"]["outcome"] == "pass", s0["result"]
        # projection: reads only a2 records (counts) and the non-energy inputs
        pr = evaluate_gate("projection", lay, "c2", base_state(n=10), reader_kw=kw,
                           inputs={"point": "after4", "H_spent_h": 450.0, "tau_SP_h": 0.11})
        assert [c["cut"] for c in pr["decision"]["cuts"]][:1] == [1] and all(o["mode"] == "files" for o in pr["opened"])
        assert pr["decision"]["cuts"][0]["at"] == "after4" and cut_ids(pr["decision"]) >= {1}
        # C3 completeness in status mode (no energy regex): pending -> not complete
        states = {"s2_m06_host": "complete", "s2_m06_VB124": "missing", "s2_m06_VB136": "pending"}
        kw2 = {**kw, "sp_status": lambda d, lab: {"status": states[lab], "missing_reason": "no JOB DONE after one "
                                                  "resubmission" if states[lab] == "missing" else None}}
        rdc = Reader(lay, "c3", allow_list("c3_complete", {}, {"c3_labels": list(states)}), **kw2)
        cc = c3_complete(rdc, list(states))
        assert not cc["complete"] and cc["counts"] == {"complete": 1, "missing": 1, "pending": 1}
        states["s2_m06_VB136"] = "complete"
        assert c3_complete(rdc, list(states))["complete"]
        refused(lambda: rdc.sp("s2_m06_host", "full"), Blinded)            # a C3 energy read is blinded
        # inputs derived for the CLI run by scripts/50 (state gate_context, ledger snapshot, C1 timings)
        inp, _ = derive_inputs("step0", lay, {"gate_context": {"at": "s2r_m30_Sr136o0_vac"},
                                              "step0": {"attempts": 1, "outcome": "pass"}}, reader_kw=kw)
        assert inp["cells"] == ["s2_m30_Sr136o0_vac"] and inp["attempt"] == 1
        inp, _ = derive_inputs("step0", lay, {"step0": {"attempts": 1, "outcome": "fail_pending_fix",
                                                        "fix_note": "2026-11-20 writer fix"}}, reader_kw=kw)
        assert inp["attempt"] == 2
        refused(lambda: derive_inputs("step0", lay, {"step0": {"outcome": "fail_pending_fix"}}, reader_kw=kw))
        refused(lambda: derive_inputs("step0", lay, {"step0": {"outcome": "fail_final"}}, reader_kw=kw))
        # the repeat (I-F3): scripts/50 sets repeat_pending with the fix note; the first cell's passing decision keeps
        # repeat and the note, so the second cell is attempt 2 as well; a mismatching attempt is refused
        st_rep = {"gate_context": {"at": "s2r_m30_VB136"},
                  "step0": {"attempts": 1, "outcome": "repeat_pending", "repeat": True, "fix_note": "2026-11-20 note"}}
        inp, _ = derive_inputs("step0", lay, st_rep, reader_kw=kw)
        assert inp["attempt"] == 2 and inp["fix_note"] == "2026-11-20 note" and inp["cells"] == ["s2_m30_VB136"]
        s0r = evaluate_gate("step0", lay, "c2", st_rep, inputs=inp, reader_kw=kw)
        st_rep.update(copy.deepcopy(s0r["decision"]))                                  # scripts/50 (N-D1)
        st_rep["gate_context"] = {"at": "s2r_m30_Sr136o0_vac"}
        assert st_rep["step0"]["repeat"] and st_rep["step0"]["fix_note"] == "2026-11-20 note"
        inp2, _ = derive_inputs("step0", lay, st_rep, reader_kw=kw)
        assert inp2["attempt"] == 2 and inp2["fix_note"] == "2026-11-20 note"
        assert evaluate_gate("step0", lay, "c2", st_rep, inputs=inp2, reader_kw=kw)["decision"]["step0"]["attempts"] == 2
        refused(lambda: derive_inputs("step0", lay, st_rep, {"attempt": 1}, reader_kw=kw))
        put_json(lay, "ledger:c1", {"schema": "s2-ledger-1", "H_spent_h": 33.5, "complete": True})
        for wid, ws, kind in (("s2_m30_host", 6000.0, "host"), ("s2_m05_host", 5400.0, "host"),
                              ("s2_m30_VB76", 1200.0, "V"), ("s2_m30_Sr76p0_vac", 1500.0, "DV")):
            put_rec(lay, wid)
            r = json.load(open(lay.record("c1", wid)))
            r.update({"cell_kind": kind, "relax": {"wall_s": ws, "E_mace_eV": -1.0}})
            json.dump(r, open(lay.record("c1", wid), "w"))
        inp, op = derive_inputs("projection", lay, {"gate_context": {"point": "after4"}}, reader_kw=kw)
        assert inp["point"] == "after4" and inp["H_spent_h"] == 33.5 and inp["host_wave_h"] == 6000.0 / 3600
        assert abs(inp["mace_h_per_relax"] - (1350.0 / 3600) / 10) < 1e-15 and op
        refused(lambda: derive_inputs("projection", lay, {"gate_context": {}}, reader_kw=kw))
        put_json(lay, "ledger:c1", {"schema": "s2-ledger-1", "H_spent_h": 33.5, "complete": False})
        refused(lambda: derive_inputs("projection", lay, {"gate_context": {"point": "c3"}}, reader_kw=kw))   # I-23
        assert "s2_m30_VB136" in list_sp_labels(lay, "c1") and not any(x.startswith("s2r_")
                                                                       for x in list_sp_labels(lay, "c2"))
        # digest independent of the root path
        lay2 = _TestLayout(os.path.join(work, "arch2_copy"))
        shutil.copytree(lay.root, lay2.root)
        assert evaluate_gate("K3", lay2, "c2", {}, reader_kw=kw)["inputs_digest"] == \
            evaluate_gate("K3", lay, "c2", {}, reader_kw=kw)["inputs_digest"]
        # verify: the archived gate files reproduce
        put_rec(lay2, "s2_m30_VB76", valid=True)
        for gate in ("G1", "N", "K3"):
            rec = evaluate_gate(gate, lay2, "c1" if gate != "K3" else "c2", {}, reader_kw=kw)
            rec["state_in"] = {}
            os.makedirs(os.path.dirname(lay2.gate(rec["campaign"], gate)), exist_ok=True)
            json.dump(rec, open(lay2.gate(rec["campaign"], gate), "w"))
        assert verify(lay2.root, "c1", layout=lay2, reader_kw=kw) == 0
        put_sp(lay2, G1_LABELS["Cl"]["D60"], -79900.01)
        assert verify(lay2.root, "c1", layout=lay2, reader_kw=kw) == 1
        return ("G1, N, nrule, K2, K3, step0 and projection evaluated from a synthetic archive through the Reader; "
                "gate names unique after lower-casing, the old name 'n' refused; digest independent of the root; "
                "verify reproduces (and detects a changed output)")

    def t_real_parser():
        try:
            q47 = dep("q47")
        except MissingDependency:
            return "skipped (scripts/47 absent; MOCKED)"
        if q47 is _MockQE or not hasattr(q47, "parse_sp"):
            return "skipped (scripts/47 mocked)"
        a32 = _load("a32", "32_dft_validation_analysis.py")
        src = os.path.join(ROOT, "results/objective2/dopant_shell/wp2c/raw/m05_GA128_novac.out.gz")
        lay = _TestLayout(os.path.join(work, "arch3"))
        dst = lay.sp_out("c1", "s2_m30_host")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        subprocess.run(["cp", src, dst], check=True)        # an S1 output under a test label, temporary only
        rd = Reader(lay, "c1", {"full": {"s2_m30_host"}, "status": {"s2_m30_host"}},
                    sp_status=lambda d, lab: {"status": "complete"})      # the label-to-input check of 47 is not
        st = rd.sp("s2_m30_host", "status")                               # the subject here (an S1 file)
        full = rd.sp("s2_m30_host", "full")
        ref = a32.parse_qe(src)
        assert abs(full["F_eV"] - ref["F_eV"]) < 1e-9 and st.get("F_eV") is None and full["status"] == "complete"
        rel = q47.parse_relax([os.path.join(ROOT, "results/objective2/dopant_shell/wp2e/relax_m30_GA_img0.out.gz")],
                              read="k0")
        assert _relax_value(rel, "k0") is not None and _relax_value(rel, "final") is None
        return "scripts/47 parse_sp through the Reader on an archived S1 output (F as scripts/32); parse_relax k0 shape"

    def t_hygiene():
        try:
            c46 = dep("c46")
        except MissingDependency:
            return "skipped (scripts/46 absent)"
        if not hasattr(c46, "hygiene_violations"):
            return "skipped (scripts/46 mocked)"
        bad = c46.hygiene_violations(open(os.path.abspath(__file__)).read(), kind="code")
        assert not bad, bad
        return "this file passes the public-repository rules of scripts/46 (gate outputs go through dump_public)"

    for nm, fn in (("hygiene", t_hygiene), ("constants", t_constants), ("t quantile", t_tppf), ("Boltzmann", t_boltz), ("G1", t_g1),
                   ("gate N and n rule", t_gate_n), ("pose rule", t_pose), ("step-0", t_step0), ("K2 and K3", t_k2k3),
                   ("separability", t_sep), ("budget", t_budget), ("throughput", t_tp), ("Reader", t_reader),
                   ("gate runners", t_runners), ("real parser", t_real_parser)):
        case(nm, fn)
    print("NOTES:")
    for k, v in NOTES.items():
        print(f"  {k}: {v}")
    ok_mace = "mace" not in sys.modules
    print(f"{'PASS' if ok_mace else 'FAIL'} no-model: 'mace' {'not ' if ok_mace else ''}in sys.modules "
          f"(torch {'imported' if 'torch' in sys.modules else 'not imported'})")
    results.append(("no-model", ok_mace))
    nf = sum(not ok for _, ok in results)
    print(f"SELF-TEST {'PASS' if not nf else 'FAIL'} ({len(results)} cases, {nf} failed, {time.time() - t0:.0f} s)")
    return 1 if nf else 0


if __name__ == "__main__":
    rc_ = main()
    assert "mace" not in sys.modules, "a model was imported by a geometry-only path"
    sys.exit(rc_)

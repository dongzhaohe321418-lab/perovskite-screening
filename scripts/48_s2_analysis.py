#!/usr/bin/env python
"""S2 analysis: the decisive statistics and classes of rule V (results/objective2/s2/S2_PLAN.md §14, binding from
commit ae6402e), the validity rules they rest on (§12: valid quartet, valid host per dopant, dopant-specific
failures), the calibration by delta (§11) and the reported-only items of §15, written to s2/s2_eval.json with
unrounded values (§14 "Output"). It is the one evaluation of §17 item 6: committed before C3, run once after C4 at a
recorded commit; a rerun needs a committed self-test case that fails on the first code and passes on the fixed one.

  evaluate(table)  a pure function of the evaluation table (schema s2-evaltable-1, below): per dopant d
      A1 tier      Y_h,d = mean_j e_h(j) over the valid first-shell sites, e_h(j) = E_b,h(j) - (E_b,h(f1) +
                   E_b,h(f2))/2; Ybar_d, s_Y,d (ddof 1); I^A1 = Ybar +- (t_{n_d-1}(q*) s_Y/sqrt(n_d) + a_pose,d).
      calibrated   delta_{d,p} = E_b^A2(j) - E_b^A1(j) (A1 from k = 0 of the same four relaxations), valid by the §11
                   rule (end rule and final-geometry checks 2-5; the A1-start condition only in a reported-only
                   sensitivity row, I-10); delta_bar_d,
                   s^2_delta pooled over the dopants with m_d >= 1 (df_delta = sum (m_d - 1)); theta = Ybar +
                   delta_bar; a = s_Y^2/n_d, b = s^2_delta/m_d, SE = sqrt(a + b), Welch-Satterthwaite nu, t* =
                   t_nu(q*); I = theta +- (t* SE + a_far + a_pose).
      classes      repels / binds (interval beyond +-k_BT and the ceil(0.75 n_d) sign rule on the tier's host
                   values), "no first-shell interaction beyond k_BT" (interval inside (-k_BT, +k_BT) and G_d >
                   -k_BT), otherwise "not resolved" with U_d; heterogeneity flag |G_d - mean_j Ebar_d(j)| > k_BT
                   at both tiers (k = sites with a valid host); controls C1-C5, the pose rule, the A1-tier controls,
                   the dopant-specific rule; ranking over the 10 pairs; required hosts; every §15 item computable
                   from the table.
  assemble(archive)  the ONLY full read of the C3 and C4 outputs (scripts/47 parsers in full mode, cell records
                   with MACE energies); builds the table from the archived campaigns.

The decision constants are those of scripts/49 (RULES); k_BT = 25.7 meV exactly; q* = 1 - 0.05/(2*4) = 0.99375.
No calculator is created or evaluated, and mace, torch and e3nn are never imported; scipy is imported lazily
(scripts/49 t_ppf).

    python scripts/48_s2_analysis.py --self-test
    python scripts/48_s2_analysis.py evaluate --archive results/objective2/s2 --out results/objective2/s2/s2_eval.json \\
        [--rerun-cause CASE]
"""
import argparse, copy, glob, gzip, hashlib, importlib.util, itertools, json, math, os, re, subprocess, sys, tarfile
import tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


g49 = _load("g49", "49_s2_gates.py")      # RULES, t_ppf, Boltzmann sums, separability, labels; 46/47 through g49.dep
RULES = g49.RULES
dep = g49.dep
TOKENS, DECISIVE, SUBLATTICE, PILOTS, LEGS = g49.TOKENS, g49.DECISIVE, g49.SUBLATTICE, g49.PILOTS, g49.LEGS
KT = RULES["K_BT_MEV"]
CLASSES = ("repels", "binds", "no first-shell interaction beyond k_BT")
NOT_RESOLVED = "not resolved"
TABLE_SCHEMA, EVAL_SCHEMA = "s2-evaltable-1", "s2-eval-1"

# Labels (S2_DECISION.md §7; S2_PLAN.md §§3, 9, 11, 14)
LABEL_VALIDATED = ("PBE (no D3, no SOC), V_I⁺ adjacent to the native Cs, first-shell mean relative to two far "
                   "sites in a 233-atom FA19Cs1Pb20I60 cell, frozen-far-field (6 Å) DFT-relaxed level estimated from "
                   "fixed-geometry DFT on zero-shot MACE geometries over n hosts with a two-host relaxation "
                   "calibration, calibrated at one first-shell site per sublattice on each of two chosen pilot hosts, "
                   "the sites differing between the two hosts; spans FA orientational disorder at one vacancy site.")
LABEL_MULTI_POSE = "calibration at the default pose"
LABEL_A1 = "fixed-geometry DFT; relaxation bias not bounded"
LABEL_SCOPE = "Cs-adjacent V_I⁺"                           # §3 scope statement
LABEL_GA_POSE = "S1 recipe; pose dependence not measured"
LABEL_GATE_N = "inconclusive below the DFT noise floor"
LABEL_DOPANT_SPECIFIC = "first shell not stable under the S2 protocol"
LABEL_POSE_CUT = "pose-dependent; not classified"
LABEL_MACE = "zero-shot MACE, not re-admitted"
LABEL_A1_START_SENS = ("reported only: rule V re-evaluated with the A1-start condition (sensitivity row, §15 style); "
                       "no class, gate or decision rests on it")

NOTES = {
    "I-10": "§§11, 14 (STAGE0 §9, D-S0-2 revised 2026-11-04): delta validity follows §11 literally: a quartet is "
            "valid iff its four A2 relaxations are accepted by the end rule and their final geometries pass the §11 "
            "checks 2-5 (validity_final written by scripts/50); m_d counts these deltas (§14), so delta_far validity "
            "is the K3 quartet validity. The A1 validity of every A2 start cell is reported beside each delta "
            "(a1_valid, a1_starts_valid), and rule V re-evaluated with the A1-start condition (a valid delta also "
            "needs valid A1 start cells) is a sensitivity row in the reported-only part (reported."
            "a1_start_sensitivity, §15 style); no class, gate or decision rests on it. The round-2 construction "
            "(a validated class only when both readings agree) is withdrawn; the runner runs every planned A2 "
            "relaxation",
    "I-16": "§12 dopant-specific rule: a first-shell cell (D_j or D_j+V of one start) fails if it fails check 2, 3 or "
            "5 while V+_Rj and the host are valid; a rejected default-start pair counts as one failed cell per leg "
            "(I-C10); 'more than a quarter of the production hosts' at site j counts a host with any failing cell at "
            "j, '> n/4' with n the production list size; 'more than 10% of d's first-shell cells' counts cells (one "
            "per default-pose leg, one per relaxed start of a multi-pose leg: round-2 STAT-3) over the cells with "
            "valid V+_Rj and host; the A2 cells (pilot calibration cells, host_R and V+_R valid) enter a second "
            "evaluation of the 10% rule; either trip removes every class of d",
    "I-17": "§14: per-site t intervals need n_j >= 2 (else null)",
    "I-18": "§14: the A1-tier class is shown only when the A1-tier controls pass; the rule-V outcome is always reported",
    "I-19": "§15 shared-region sensitivity: regions (B, A, X) with a dopant of two valid pilot-host quartets "
            "(m_d = 2) are counted; that count replaces df_delta in nu_d and in the a_far threshold; 0 -> null",
    "I-20": "§14: 'entirely above' is lo > 25.7; 'positive' > 0; 'inside (-25.7, +25.7)' is open; 'G_d above' > -25.7",
    "I-38": "§§9, 12: a multi-pose leg aggregates over its kept minima (all valid starts' distinct minima) and needs "
            "every kept-minimum SP complete and at least one minimum",
    "X-1": "§15 D3(BJ): no D3 implementation in the environment and no new dependency allowed; the row is reported "
           "as not computed (a dated amendment must fix an implementation before the one evaluation)",
    "I-C7": "§14 A1-tier controls: 'Sr repels at the A1 tier' is read as Sr's displayed A1 class being 'repels' "
            "(Sr's rule-V outcome with its own C2, C3, C4, no flag and no no-class condition)",
    "I-C8": "§14 C1: Sr's calibrated class counts after the no-class conditions (gate N, G1, dopant-specific rule)",
    "I-C9": "§14 C2: with fewer than two valid production hosts SD(Delta_h) is undefined and C2 fails",
    "I-C10": "§12: a rejected pair of the default start p0 (relaxed partners) counts as a failed unit in both legs "
             "(fail-closed); in multi-pose production a rejected non-default start is not a start (§9 'every "
             "admissible start') and does not count (review-1 F4)",
    "N-C13": "§§6, 11: A2 relaxations are parsed with the C1 smoke-test mapping (c1/smoke.json), as by the runner and "
             "the gates; a relaxation of more than one part without that record is refused (review-2 F8)",
    "N-C14": "§9: Cs or Cl without a recorded production pose mode counts as multi-pose (fail-closed), and the "
             "production modes must equal the pose gate under cuts 6/7 (review-1 F11)",
    "N-C15": "§9: a kept minimum o<k> (k >= 1) takes the MACE validity of the cell its distinct-minima record names "
             "(scripts/46 labels only the p0 record; review-2 F4)",
    "I-C11": "§12 with §11: the A2 dopant units count a failure of any of the §11 final-geometry checks 2-5 of D or "
             "D+V (fail-closed); the A1 units count checks 2, 3, 5 as written",
    "I-C12": "§14: the heterogeneity flag removes the class at the tier where it fires; Adding delta_bar shifts G_d "
             "and mean_j Ebar_d(j) equally, so the flag is evaluated once (A1) and used at both tiers; a calibrated-"
             "tier recomputation that differs by rounding at the threshold is recorded, never raised (round-2 STAT-6)",
    "N-C6": "§14: a + b = 0 (no spread at all) leaves the interval undefined: not computed, 'not resolved'",
    "N-C7": "§14 ranking: intervals carry no allowance (a_far, a_pose); reported only",
    "N-C8": "§17 item 6: a rerun is written beside the first output as s2_eval.rerun<k>.json; s2_eval.json is never "
            "overwritten",
    "N-C9": "§15 plateau-excluded intervals: delta values with a plateau-accepted relaxation (including delta_far) "
            "are dropped and delta_bar, s_delta, df_delta, a_far and every calibrated interval recomputed",
    "N-C10": "§§11, 14: an invalid delta_far fails C5; the reported calibrated interval then carries a_far = 0",
    "N-F26": "§9 (round-3 R3C-3 and missed item): N_D, N_D+V and the count term k_BT ln(N_D/N_D+V) are reported "
             "beside every aggregated (multi-pose) E_b of the per-site rows and beside Delta_pose (the pose gate's "
             "near and far records kept by assemble, the pose pilot and pose_note)",
    "N-F27": "§15 (round-3 R3C-4): the zero-shot MACE ledger covers every cell with MACE energies: the production "
             "quartets, the noise pilot, and (pilot section) the m30 and m05 calibration start-set quartets beside "
             "the A1 DFT E_b from k = 0 of their A2 cells and the m30 pose-pilot sites (default and kept-minima "
             "aggregate); all labelled zero-shot MACE, not re-admitted",
    "N-F28": "§15 (round-3 R3C-5): the residual forces of every A1 cell carry the per-atom norms of the free atoms "
             "(scripts/47 parse_sp 'free': norms_eVA with their indices) beside RMS and max",
    "N-F29": "§17 item 6 (round-3 R3C-6; revised in round 4, R4-C24-5): the one evaluation records the campaign commit "
             "(the latest state_end.json) beside HEAD with the git diff of scripts/46-49 between them (stat, sha256, "
             "and the diff itself beside s2_eval.json); a difference is refused unless --amendment names a committed, "
             "clean note outside scripts/ that was added or changed after the campaign commit and carries an ISO date "
             "on or after that commit's; a given amendment is checked alike and recorded also when the code is "
             "unchanged, and the D3(BJ) row cites it (D-S0-4)",
    "N-F39": "§§13, 17 item 6 (round-4 R4-C1-6): every commit change during the campaigns (state_end commit_history: "
             "c1/NODE_FIX, c2/STEP0_FIX) is reported in s2_eval.json analysis_identity with the diff stat of "
             "scripts/46-50 and ehpc/node between its two commits; report only, no refusal",
    "N-F40": "§16 'output discarded unread' (round-4 R4-C24-3): only a complete A2 relaxation is parsed; a killed, "
             "missing or not-run one has no energies read (its outputs were moved aside unread), and the reported A2 "
             "rows give a relaxation energy for complete cells only",
    "N-F41": "§§8, 11 (round-4 R4-C24-4): the Cs and Cl cells of the pilot hosts (noise pilot, start set) are "
             "default-pose cells: their pose mode is 'default', so their reported rows and MACE values use the o0 "
             "cells, as gate N does (the m30 pose pilot is reported apart); a pilot host without a Cs or Cl record "
             "cannot crash the evaluation",
    "N-C11": "§15 required hosts: the smallest n in 2..1000 with t_{n-1}(q*) s_Y/sqrt(n) below k_BT (and k_BT/2); "
             "null when s_Y is undefined or no n <= 1000 suffices",
    "N-C12": "§17: evaluate is a pure function of the table; assemble is the only reader of C3/C4 energies and of the "
             "MACE energies (records with blind=False)",
}


# ---------------------------------------------------------------- small statistics
def _mean(v):
    return math.fsum(v) / len(v)


def _sd(v):
    """Sample SD, ddof = 1 (§14)."""
    m = _mean(v)
    return math.sqrt(math.fsum((x - m) ** 2 for x in v) / (len(v) - 1))


def eb_meV(F, dv, d, v, h):
    """(F[dv] - F[d] - F[v] + F[h]) x 1000 from a label -> F dict (interface spec §8.4); None if a term is missing."""
    return g49.eb_meV(F.get(dv), F.get(d), F.get(v), F.get(h))


# ---------------------------------------------------------------- A1 quartets and host values (§§1, 12)
def _pose_mode(H, d):
    """Pose mode of d on a host record. Cs and Cl without a recorded mode count as multi-pose (fail-closed: their legs
    then need recorded kept minima; review-1 F11); Sr, Ca and GA have one start (§2)."""
    po = (H.get("pose") or {}).get(d) or {}
    if d in ("Cs", "Cl"):
        return po.get("mode") or "multi"
    return "default"


def _p0_rejected(H, d, j):
    """§§5, 9, 12 with I-C10: the pair of the default start p0 of (d, j) was rejected on relaxed partners. In
    multi-pose production an inadmissible non-default start is not a start ('every admissible start is relaxed', §9)
    and does not count (review-1 F4). A bare True (older tables) means p0."""
    v = (H.get("pair_rejected") or {}).get(f"{d}{j}")
    if v is True:
        return True
    return bool(v) and "p0" in v


def leg_F(table, h, d, j, leg):
    """(F_leg in eV | None, reasons, kept-minimum labels) for one leg of (h, d, j). Default pose: the o0 cell. Multi-pose:
    the per-leg Boltzmann aggregate over the kept minima (I-38)."""
    H = table["hosts"][h]
    if _pose_mode(H, d) == "multi":
        mins = (((((H.get("pose") or {}).get(d) or {}).get("minima") or {}).get(str(j)) or {}).get(leg)) or []
        labs = [g49.lab_dop(h, d, j, leg, int(o[1:])) for o in mins]
        if not labs:
            return None, [f"{d}{j} {leg}: no valid start (I-38)"], labs
    else:
        labs = [g49.lab_dop(h, d, j, leg, 0)]
    why = []
    for lab in labs:
        if H.get("cell_valid", {}).get(lab) is not True:
            why.append(f"{lab}: MACE cell invalid or absent")
        if H.get("F", {}).get(lab) is None:
            why.append(f"{lab}: SP missing")
    if why:
        return None, why, labs
    Fs = [H["F"][lab] for lab in labs]
    return (Fs[0] if len(Fs) == 1 else g49.leg_free_energy(Fs)), [], labs


def quartet_a1(table, h, d, j):
    """A1 quartet of (h, d, j): valid iff the four SPs are complete and the host relaxation and the three MACE
    relaxations are valid (§12; multi-pose legs as I-38). E_b in meV (positive = repulsion)."""
    H = table["hosts"][h]
    L = SUBLATTICE[d]
    why = []
    hl, vl = g49.lab_host(h), g49.lab_v(h, L, j)
    if H.get("host_valid") is not True:
        why.append("host relaxation invalid")
    if H.get("F", {}).get(hl) is None:
        why.append(f"{hl}: SP missing")
    if H.get("cell_valid", {}).get(vl) is not True:
        why.append(f"{vl}: MACE cell invalid or absent")
    if H.get("F", {}).get(vl) is None:
        why.append(f"{vl}: SP missing")
    FD, wD, lD = leg_F(table, h, d, j, "novac")
    FDV, wDV, lDV = leg_F(table, h, d, j, "vac")
    why += wD + wDV
    eb = None
    if not why:
        eb = g49.eb_meV(FDV, FD, H["F"][vl], H["F"][hl])
    return {"Eb_meV": eb, "valid": not why, "reasons": why, "labels": {"host": hl, "V": vl, "D": lD, "DV": lDV}}


def host_values(table, d):
    """Per production host: the quartets of d's sublattice, the valid-host decision (§12), e_h(j), Y_h and the far-pair
    difference Delta_h = E_b(f1) - E_b(f2)."""
    L = SUBLATTICE[d]
    need = RULES["VALID_HOST_MIN"][L]
    out = {}
    for h in table["production"]:
        S = table["sites"][h][L]
        first, far = [int(x) for x in S["first"]], [int(x) for x in S["far"]]
        assert len(first) == RULES["FIRST_SHELL_SIZE"][L] and len(far) == 2, (h, L, S)
        qf = {j: quartet_a1(table, h, d, j) for j in first}
        qr = {f: quartet_a1(table, h, d, f) for f in far}
        vfirst = [j for j in first if qf[j]["valid"]]
        far_ok = all(qr[f]["valid"] for f in far)
        valid = far_ok and len(vfirst) >= need
        rec = {"first": qf, "far": qr, "n_valid_first": len(vfirst), "far_valid": far_ok, "valid": valid,
               "e_meV": {}, "Y_h_meV": None, "Delta_h_meV": None, "far_mean_meV": None}
        if far_ok:
            fm = 0.5 * (qr[far[0]]["Eb_meV"] + qr[far[1]]["Eb_meV"])
            rec["far_mean_meV"] = fm
            rec["Delta_h_meV"] = qr[far[0]]["Eb_meV"] - qr[far[1]]["Eb_meV"]
            rec["e_meV"] = {j: qf[j]["Eb_meV"] - fm for j in vfirst}
        if valid:
            rec["Y_h_meV"] = _mean([rec["e_meV"][j] for j in vfirst])
        out[h] = rec
    return out


# ---------------------------------------------------------------- calibration (§11)
def _a2_quartet(table, p, d, L, j, *, a1_start_required=False):
    """One A2 calibration quartet (§11): valid iff its four relaxations are complete, accepted by the end rule and
    valid on their final geometries (§11 checks 2-5; I-10, D-S0-2 revised). The A1 validity of the four start cells
    is always reported (a1_valid per role, a1_starts_valid). a1_start_required=True adds the A1-start condition; it
    is used only for the reported-only sensitivity row (a1_start_sensitivity), never for a class, gate or decision."""
    A = (table.get("a2") or {}).get(p) or {}
    labs = {"host": f"s2r_{p}_host{L}{j}", "V": f"s2r_{p}_V{L}{j}", "D": g49.lab_dop(p, d, j, "novac", 0, "s2r"),
            "DV": g49.lab_dop(p, d, j, "vac", 0, "s2r")}
    why, plateau = [], False
    for role, lab in labs.items():
        c = A.get(lab)
        if c is None:
            why.append(f"{lab}: not run or absent")
            continue
        if c.get("status") != "complete":
            why.append(f"{lab}: status {c.get('status')}")
        if c.get("end_rule") not in RULES["END_ACCEPTED"]:
            why.append(f"{lab}: end rule {c.get('end_rule')}")
        if c.get("valid_final") is not True:
            why.append(f"{lab}: final geometry fails {c.get('failed_checks')}")
        if a1_start_required and c.get("a1_valid") is not True:
            why.append(f"{lab}: A1 start cell not valid (A1-start condition, sensitivity row only)")
        if c.get("F0_eV") is None or c.get("Ffin_eV") is None:
            why.append(f"{lab}: F(0) or F(final) missing")
        plateau = plateau or c.get("end_rule") == "accepted_plateau" or bool(c.get("plateau"))
    a1v = {r: (A.get(lab) or {}).get("a1_valid") for r, lab in labs.items()}
    rec = {"labels": labs, "valid": not why, "reasons": why, "plateau": plateau,
           "Eb_A1_meV": None, "Eb_A2_meV": None, "delta_meV": None, "a1_start_required": bool(a1_start_required),
           "a1_valid": a1v, "a1_starts_valid": all(v is True for v in a1v.values())}
    if not why:
        F0 = {r: A[lab]["F0_eV"] for r, lab in labs.items()}
        Ff = {r: A[lab]["Ffin_eV"] for r, lab in labs.items()}
        rec["Eb_A1_meV"] = g49.eb_meV(F0["DV"], F0["D"], F0["V"], F0["host"])
        rec["Eb_A2_meV"] = g49.eb_meV(Ff["DV"], Ff["D"], Ff["V"], Ff["host"])
        rec["delta_meV"] = rec["Eb_A2_meV"] - rec["Eb_A1_meV"]
    return rec


def deltas(table, d, *, a1_start_required=False):
    """delta_{d,p} at the calibration site of d's sublattice on each pilot host (§11)."""
    L = SUBLATTICE[d]
    return {p: {**_a2_quartet(table, p, d, L, int(table["a2_sites"][p][L]), a1_start_required=a1_start_required),
                "site": int(table["a2_sites"][p][L])} for p in PILOTS}


def delta_far(table, *, a1_start_required=False):
    """delta_far: the m30 Sr far quartet at Pb76 (§11); valid exactly when K3 counts the far quartet valid."""
    f = table["a2_sites"]["far"]
    return {**_a2_quartet(table, f["pilot"], f["token"], f["L"], int(f["site"]), a1_start_required=a1_start_required),
            "site": int(f["site"])}


def pooled_delta(deltas_by_d):
    """deltas_by_d: {d: [valid delta values]}. delta_bar_d, m_d, s^2_delta = sum_d sum_p (delta - delta_bar_d)^2 /
    df_delta, df_delta = sum_d (m_d - 1) over the dopants with m_d >= 1 (Sr included) (§14)."""
    m = {d: len(v) for d, v in deltas_by_d.items()}
    dbar = {d: (_mean(v) if v else None) for d, v in deltas_by_d.items()}
    ss = math.fsum((x - dbar[d]) ** 2 for d, v in deltas_by_d.items() for x in v)
    df = sum(m[d] - 1 for d in m if m[d] >= 1)
    s2 = ss / df if df > 0 else None
    return {"delta_bar_meV": dbar, "m": m, "ss": ss, "df_delta": df, "s2_delta": s2,
            "s_delta_meV": math.sqrt(s2) if s2 is not None else None}


# ---------------------------------------------------------------- tiers, classes, heterogeneity (§14)
def tier_a1(Y, a_pose):
    """Y: the valid-host values Y_h (meV). I^A1 = Ybar +- (t_{n-1}(q*) s_Y/sqrt(n) + a_pose); needs n_d >= 2."""
    n = len(Y)
    if n < 2:
        return {"available": False, "n_d": n, "reason": f"n_d = {n} < 2"}
    yb, sy = _mean(Y), _sd(Y)
    t = g49.t_ppf(RULES["Q_STAR"], n - 1)
    half = t * sy / math.sqrt(n) + a_pose
    return {"available": True, "n_d": n, "Ybar_meV": yb, "s_Y_meV": sy, "t": t, "a_pose_meV": a_pose,
            "half_width_meV": half, "interval_meV": [yb - half, yb + half], "U_meV": abs(yb) + half}


def tier_cal(Y, pool, d, a_far, a_pose, *, df_override=None):
    """theta = Ybar + delta_bar; SE^2 = s_Y^2/n_d + s^2_delta/m_d; Welch-Satterthwaite nu; I = theta +- (t_nu(q*) SE +
    a_far + a_pose). Needs n_d >= 2, m_d >= 1, df_delta >= 1. df_override replaces df_delta in nu (§15, I-19)."""
    n, m = len(Y), pool["m"].get(d, 0)
    df = pool["df_delta"] if df_override is None else df_override
    why = [r for r, bad in ((f"n_d = {n} < 2", n < 2), (f"m_d = {m} < 1", m < 1),
                            (f"df_delta = {df} < 1", df is None or df < 1)) if bad]
    if why:
        return {"available": False, "n_d": n, "m_d": m, "reason": "; ".join(why)}
    yb, sy, dbar, s2d = _mean(Y), _sd(Y), pool["delta_bar_meV"][d], pool["s2_delta"]
    a, b = sy * sy / n, s2d / m
    rec = {"available": True, "n_d": n, "m_d": m, "df_delta": df, "Ybar_meV": yb, "s_Y_meV": sy,
           "delta_bar_meV": dbar, "theta_meV": yb + dbar, "a": a, "b": b, "SE_meV": math.sqrt(a + b),
           "a_far_meV": a_far, "a_pose_meV": a_pose}
    if a + b == 0:
        return {**rec, "available": False, "reason": "a + b = 0: interval undefined (N-C6)"}
    nu = (a + b) ** 2 / (a * a / (n - 1) + b * b / df)
    ts = g49.t_ppf(RULES["Q_STAR"], nu)
    half = ts * rec["SE_meV"] + a_far + a_pose
    return {**rec, "nu": nu, "t_star": ts, "half_width_meV": half,
            "interval_meV": [rec["theta_meV"] - half, rec["theta_meV"] + half], "U_meV": abs(rec["theta_meV"]) + half}


def classify(lo, hi, host_vals, G):
    """Rule V (§14, I-20): repels, binds, 'no first-shell interaction beyond k_BT' (also G > -k_BT), else not resolved."""
    n = len(host_vals)
    need = g49.sign_required(n)
    if lo > KT and sum(1 for y in host_vals if y > 0) >= need:
        return "repels"
    if hi < -KT and sum(1 for y in host_vals if y < 0) >= need:
        return "binds"
    if lo > -KT and hi < KT and G is not None and G > -KT:
        return "no first-shell interaction beyond k_BT"
    return NOT_RESOLVED


def heterogeneity(Ebar_sites, shift):
    """Ebar_sites: {j: [e_h(j) over the valid hosts for d at which j is valid]}. Ebar_d(j) = mean + shift; k = sites
    with >= 1 host; G_d = -k_BT ln((1/k) sum_j exp(-Ebar(j)/k_BT)); flag iff |G_d - mean_j Ebar(j)| > k_BT; per-site
    t_{n_j-1}(0.975) intervals (null if n_j < 2, I-17)."""
    Eb, nj, iv = {}, {}, {}
    for j in sorted(Ebar_sites, key=int):
        v = Ebar_sites[j]
        nj[str(j)] = len(v)
        if not v:
            continue
        Eb[str(j)] = _mean(v) + shift
        if len(v) >= 2:
            hw = g49.t_ppf(RULES["Q_SITE"], len(v) - 1) * _sd(v) / math.sqrt(len(v))
            iv[str(j)] = [Eb[str(j)] - hw, Eb[str(j)] + hw]
        else:
            iv[str(j)] = None
    k = len(Eb)
    if k == 0:
        return {"Ebar_meV": {}, "n_j": nj, "k": 0, "G_meV": None, "mean_meV": None, "flag": None, "intervals": iv}
    G = g49.boltzmann_meV(list(Eb.values()), mean=True)
    mean = _mean(list(Eb.values()))
    return {"Ebar_meV": Eb, "n_j": nj, "k": k, "G_meV": G, "mean_meV": mean, "flag": abs(G - mean) > KT,
            "intervals": iv}


def a_pose_of(table, d):
    """a_pose,d (§9): Cs and Cl from the pose gate (0 when multi-pose); Sr, Ca, GA have one start: 0."""
    if d not in ("Cs", "Cl"):
        return 0.0
    g = ((table.get("gates") or {}).get("pose") or {}).get(d) or {}
    if g.get("mode") == "default":
        return float(g["a_pose_meV"])
    return 0.0


# ---------------------------------------------------------------- §12 dopant-specific failures
def _failed_specific(checks, which):
    return bool(set(int(c) for c in (checks or []) if str(c).isdigit()) & set(which))


def dopant_specific(table, d):
    """§12 rule (I-16, I-C10, I-C11): trips iff dopant-specific failures occur at one first-shell site on more than a
    quarter of the production hosts, or in more than 10% of d's first-shell cells (A1, then A1 + A2 cells). The
    (host, site, leg) units carry the site rule; the 10% rule counts cells: one per default-pose leg, one per relaxed
    start of a multi-pose leg (round-2 STAT-3)."""
    L = SUBLATTICE[d]
    which = RULES["DOPANT_SPECIFIC"]["checks"]
    prod = list(table["production"])
    nprod = len(prod)
    a, b = RULES["DOPANT_SPECIFIC"]["site_host_fraction"]
    units, failed = [], []
    n_cells, n_failed_cells = 0, 0
    hosts_at = {}
    for h in prod:
        H = table["hosts"][h]
        for j in [int(x) for x in table["sites"][h][L]["first"]]:
            vl = g49.lab_v(h, L, j)
            if H.get("host_valid") is not True or H.get("cell_valid", {}).get(vl) is not True:
                continue                                       # not dopant-specific: V+_Rj or the host invalid
            rej = _p0_rejected(H, d, j)
            for leg in LEGS:
                if _pose_mode(H, d) == "multi":                # every relaxed start is a cell (§9; STAT-3)
                    sf = ((((H["pose"][d].get("start_failed") or {}).get(str(j))) or {}).get(leg)) or {}
                    cells = len(sf) + int(rej)                 # I-C10: a rejected p0 is one failed cell of the leg
                    nbad = sum(1 for c in sf.values() if _failed_specific(c, which)) + int(rej)
                else:
                    cells = 1
                    nbad = int(rej or _failed_specific(H.get("failed_checks", {}).get(g49.lab_dop(h, d, j, leg, 0)),
                                                       which))
                bad = nbad > 0
                n_cells += cells
                n_failed_cells += nbad
                u = {"host": h, "site": j, "leg": leg, "failed": bad, "rejected": rej, "cells": cells,
                     "failed_cells": nbad}
                units.append(u)
                if u["failed"]:
                    failed.append(u)
                    hosts_at.setdefault(j, set()).add(h)
    site_trip = {str(j): len(hs) for j, hs in hosts_at.items() if len(hs) * b > nprod * a}     # > n/4
    frac = n_failed_cells / n_cells if n_cells else 0.0
    trip_cells = frac > RULES["DOPANT_SPECIFIC"]["cell_fraction"]
    # second evaluation of the 10% rule with the A2 units of the calibration sites (I-16)
    a2_units, a2_failed = [], []
    for p in PILOTS:
        A = (table.get("a2") or {}).get(p) or {}
        j = int(table["a2_sites"][p][L])
        hr, vr = A.get(f"s2r_{p}_host{L}{j}"), A.get(f"s2r_{p}_V{L}{j}")
        if not (hr and vr and hr.get("valid_final") is True and vr.get("valid_final") is True):
            continue
        for leg in LEGS:
            c = A.get(g49.lab_dop(p, d, j, leg, 0, "s2r"))
            if c is None or c.get("valid_final") is None:
                continue
            bad = c.get("valid_final") is False and _failed_specific(c.get("failed_checks"), (2, 3, 4, 5))
            a2_units.append({"pilot": p, "site": j, "leg": leg, "failed": bad})
            if bad:
                a2_failed.append(a2_units[-1])
    n2 = n_cells + len(a2_units)
    frac2 = (n_failed_cells + len(a2_failed)) / n2 if n2 else 0.0
    trip_a2 = frac2 > RULES["DOPANT_SPECIFIC"]["cell_fraction"]
    return {"applies": bool(site_trip) or trip_cells or trip_a2, "site_trip": site_trip, "n_units": len(units),
            "n_failed": len(failed), "n_cells": n_cells, "n_failed_cells": n_failed_cells, "fraction": frac,
            "fraction_with_a2": frac2, "n_a2_units": len(a2_units), "n_a2_failed": len(a2_failed),
            "failed_units": failed + a2_failed, "n_production": nprod}


# ---------------------------------------------------------------- controls, ranking, required hosts (§§14, 15)
def c2_noise(table, d, hv):
    """C2: gate N passed and, over the valid production hosts, SD(Delta_h)/sqrt(2) < 25 and |mean(Delta_h)| < 15."""
    gN = (((table.get("gates") or {}).get("N") or {}).get(d) or {}).get("pass") is True
    D = [r["Delta_h_meV"] for r in hv.values() if r["valid"]]
    if len(D) < 2:
        return {"pass": False, "gate_N": gN, "n": len(D), "sd_over_sqrt2_meV": None, "mean_meV": None,
                "reason": "fewer than 2 valid hosts (I-C9)"}
    sd2, mn = _sd(D) / math.sqrt(2), _mean(D)
    ok = gN and sd2 < RULES["C2_SD_MAX_MEV"] and abs(mn) < RULES["C2_MEAN_MAX_MEV"]
    return {"pass": ok, "gate_N": gN, "n": len(D), "sd_over_sqrt2_meV": sd2, "mean_meV": mn, "reason": None}


def required_hosts(s_Y):
    """Smallest n with t_{n-1}(q*) s_Y/sqrt(n) < k_BT and < k_BT/2 (§15; N-C11)."""
    if s_Y is None:
        return {"k_BT": None, "k_BT/2": None}
    out = {}
    for key, lim in (("k_BT", KT), ("k_BT/2", KT / 2)):
        out[key] = next((n for n in range(2, 1001) if g49.t_ppf(RULES["Q_STAR"], n - 1) * s_Y / math.sqrt(n) < lim),
                        None)
    return out


def ranking(table, results, hv_all, pool):
    """Host-paired differences D_h = Y_h,d - Y_h,d' over the hosts valid for both, t_{n'-1}(1 - 0.05/20) intervals;
    calibrated when both are: + delta_bar_d - delta_bar_d', variance s^2_delta (1/m_d + 1/m_d'), Welch-Satterthwaite
    (§14; N-C7)."""
    q = RULES["Q_RANK"]
    out = {"A1": {}, "calibrated": {}}
    for d1, d2 in itertools.combinations(TOKENS, 2):
        key = f"{d1}-{d2}"
        hs = [h for h in table["production"] if hv_all[d1][h]["valid"] and hv_all[d2][h]["valid"]]
        D = [hv_all[d1][h]["Y_h_meV"] - hv_all[d2][h]["Y_h_meV"] for h in hs]
        r = {"hosts": hs, "n": len(D), "mean_meV": _mean(D) if D else None, "sd_meV": _sd(D) if len(D) >= 2 else None,
             "interval_meV": None}
        if len(D) >= 2:
            hw = g49.t_ppf(q, len(D) - 1) * r["sd_meV"] / math.sqrt(len(D))
            r["half_width_meV"], r["interval_meV"] = hw, [r["mean_meV"] - hw, r["mean_meV"] + hw]
        out["A1"][key] = r
        c1, c2 = results[d1]["calibrated"], results[d2]["calibrated"]
        if len(D) >= 2 and c1.get("available") and c2.get("available"):
            m1, m2 = pool["m"][d1], pool["m"][d2]
            a = r["sd_meV"] ** 2 / len(D)
            b = pool["s2_delta"] * (1 / m1 + 1 / m2)
            th = r["mean_meV"] + pool["delta_bar_meV"][d1] - pool["delta_bar_meV"][d2]
            rc = {"n": len(D), "theta_meV": th, "a": a, "b": b, "SE_meV": math.sqrt(a + b)}
            if a + b > 0:
                nu = (a + b) ** 2 / (a * a / (len(D) - 1) + b * b / pool["df_delta"])
                hw = g49.t_ppf(q, nu) * rc["SE_meV"]
                rc.update({"nu": nu, "half_width_meV": hw, "interval_meV": [th - hw, th + hw]})
            out["calibrated"][key] = rc
    return out


# ---------------------------------------------------------------- evaluation (pure function of the table)
def _check_table(table):
    if table.get("schema") != TABLE_SCHEMA:
        raise ValueError(f"table schema {table.get('schema')!r} != {TABLE_SCHEMA}")
    if len(table["production"]) != int(table["n"]):
        raise ValueError(f"production list of {len(table['production'])} hosts for n = {table['n']}")
    for h in table["production"]:
        if h in PILOTS:
            raise ValueError(f"pilot host {h} in the production list (§3)")
    if set(table["dopants"]) != set(TOKENS):
        raise ValueError(f"dopants {table['dopants']} != {TOKENS}")
    g = table.get("gates") or {}
    for tok in ("Cs", "Cl"):                         # production pose modes = the pose gate under cuts 6/7 (F11)
        gm = ((g.get("pose") or {}).get(tok) or {}).get("mode")
        want = "default" if (g.get("multi_pose_cut") or {}).get(tok) else (gm or "multi")
        got = {_pose_mode(table["hosts"][h], tok) for h in table["production"]}
        if got != {want}:
            raise ValueError(f"{tok}: production pose modes {sorted(got)} differ from the pose gate and cuts ({want})")


def _no_class_reasons(table, d, ds):
    g = table.get("gates") or {}
    why = []
    if (((g.get("N") or {}).get(d)) or {}).get("pass") is not True:
        why.append(f"gate N failed: {LABEL_GATE_N}")
    if not g49.g1_pass(g.get("G1") or {}, d):
        why.append("G1 failed for the element (C3)")
    if ds["applies"]:
        why.append(f"dopant-specific failure rule: {LABEL_DOPANT_SPECIFIC}")
    if (g.get("multi_pose_cut") or {}).get(d):
        why.append(LABEL_POSE_CUT)
    return why


def cal_heterogeneity(sites, shift, het1):
    """§14 / I-C12: the calibrated-tier heterogeneity (G_d and Ebar shifted by delta_bar_d) with the flag of the A1 tier,
    which §14 states is the same at both tiers; a recomputed flag that differs (by rounding, within 1e-9 meV of the
    threshold) is recorded under flag_recomputed and never raised (round-2 STAT-6)."""
    h = heterogeneity(sites, shift)
    if h["flag"] is not None and het1["flag"] is not None and h["flag"] != het1["flag"]:
        gap = abs(h["G_meV"] - h["mean_meV"]) - KT
        h["flag_recomputed"] = {"flag": h["flag"], "gap_to_kT_meV": gap, "within_rounding": abs(gap) <= 1e-9}
    h["flag"] = het1["flag"]
    return h


def evaluate(table):
    """Rule V of §14 and the §15 items from an s2-evaltable-1 table; returns the s2-eval-1 body (unrounded).
    A delta is valid by the §11 rule (four relaxations accepted by the end rule, final geometries passing checks 2-5;
    I-10, STAGE0 §9 D-S0-2 revised); every class, control and reported number follows it. Rule V re-evaluated with the
    A1-start condition is added to the reported items as a sensitivity row (reported.a1_start_sensitivity), on which
    no class, gate or decision rests."""
    res = _evaluate(table)
    res["reported"]["a1_start_sensitivity"] = a1_start_sensitivity(table, res)
    return res


def a1_start_sensitivity(table, res):
    """§15-style sensitivity row, reported only (I-10, STAGE0 §9 D-S0-2 revised): the calibrated tier and rule V
    re-evaluated with the A1-start condition, i.e. a delta counts only if the A1 start cells of its four A2
    relaxations are valid (a1_valid True; False or unknown fails the condition). res is the decisive result (the §11
    rule); nothing here changes it."""
    sens = _evaluate(table, a1_start_required=True, reported_items=False)
    per, differs = {}, False
    for d in TOKENS:
        c, c0 = sens["per_dopant"][d]["calibrated"], res["per_dopant"][d]["calibrated"]
        row = {"m_d": sens["delta_pool"]["m"][d], "m_d_section11": res["delta_pool"]["m"][d],
               "delta_valid": {p: c["deltas"][p]["valid"] for p in PILOTS},
               "a1_starts_valid": {p: c["deltas"][p]["a1_starts_valid"] for p in PILOTS},
               "delta_bar_meV": sens["delta_pool"]["delta_bar_meV"][d], "theta_meV": c.get("theta_meV"),
               "interval_meV": c.get("interval_meV"), "U_meV": c.get("U_meV"), "class_rule_v": c.get("class_rule_v"),
               "class_with_controls": c.get("class_validated"),
               "controls_failed": [k for k in ("C1", "C2", "C3", "C4", "C5")
                                   if not _ctl_pass(sens["per_dopant"][d]["controls"][k])]}
        row["differs_from_section11"] = (row["m_d"] != row["m_d_section11"] or c.get("interval_meV") != c0.get("interval_meV")
                                         or c.get("class_rule_v") != c0.get("class_rule_v")
                                         or c.get("class_validated") != c0.get("class_validated"))
        differs = differs or row["differs_from_section11"]
        per[d] = row
    starts = sorted(f"{p}:{lab}" for p, A in sorted((table.get("a2") or {}).items()) for lab, x in A.items()
                    if x.get("a1_valid") is not True)
    return {"label": LABEL_A1_START_SENS, "condition": "a valid delta also needs valid A1 start cells of its four A2 "
            "relaxations (the round-2 reading of D-S0-2, withdrawn as a rule)",
            "a2_cells_with_A1_start_not_valid": starts, "df_delta": sens["delta_pool"]["df_delta"],
            "s_delta_meV": sens["delta_pool"]["s_delta_meV"], "delta_far_valid": sens["delta_far"]["valid"],
            "a_far_meV": sens["separability"]["a_far_meV"],
            "differs_from_section11": bool(differs or sens["delta_far"]["valid"] != res["delta_far"]["valid"]),
            "per_dopant": per}


def _ctl_pass(v):
    return v.get("pass") is True if isinstance(v, dict) else v is True


def _evaluate(table, *, a1_start_required=False, reported_items=True):
    _check_table(table)
    n = int(table["n"])
    hv = {d: host_values(table, d) for d in TOKENS}
    dl = {d: deltas(table, d, a1_start_required=a1_start_required) for d in TOKENS}
    pool = pooled_delta({d: [v["delta_meV"] for v in dl[d].values() if v["valid"]] for d in TOKENS})
    dfar = delta_far(table, a1_start_required=a1_start_required)
    sep = g49.separability(dfar["delta_meV"] if dfar["valid"] else None, pool["s_delta_meV"], pool["df_delta"])
    a_far = sep["a_far_meV"]
    out = {}
    for d in TOKENS:                                          # Sr first (C1 is read from Sr's result)
        L = SUBLATTICE[d]
        ap = a_pose_of(table, d)
        valid_hosts = [h for h in table["production"] if hv[d][h]["valid"]]
        Y = {h: hv[d][h]["Y_h_meV"] for h in valid_hosts}
        sites = {}
        for h in valid_hosts:
            for j, e in hv[d][h]["e_meV"].items():
                sites.setdefault(j, []).append(e)
        for j in table["sites"][table["production"][0]][L]["first"]:
            sites.setdefault(int(j), [])
        het1 = heterogeneity(sites, 0.0)
        ds = dopant_specific(table, d)
        noclass = _no_class_reasons(table, d, ds)
        flag = bool(het1["flag"])
        c2 = c2_noise(table, d, hv[d])
        c3 = g49.g1_pass((table.get("gates") or {}).get("G1") or {}, d)
        c4 = len(valid_hosts) >= n - 1
        # A1 tier
        a1 = tier_a1(list(Y.values()), ap)
        if a1["available"]:
            a1["class_rule_v"] = classify(*a1["interval_meV"], list(Y.values()), het1["G_meV"])
        a1["G_meV"] = het1["G_meV"]
        a1["hosts"], a1["Y_h_meV"], a1["label"] = valid_hosts, Y, LABEL_A1
        # calibrated tier
        cal = tier_cal(list(Y.values()), pool, d, a_far, ap)
        hetc = None
        if cal["available"]:
            hetc = cal_heterogeneity(sites, pool["delta_bar_meV"][d], het1)     # I-C12: the A1 flag at both tiers
            hv_cal = [y + pool["delta_bar_meV"][d] for y in Y.values()]
            cal["class_rule_v"] = classify(*cal["interval_meV"], hv_cal, hetc["G_meV"])
            cal["G_meV"] = hetc["G_meV"]
        cal["deltas"] = {p: dl[d][p] for p in PILOTS}
        c5 = (pool["m"][d] >= 1 and pool["df_delta"] >= RULES["DF_MIN"] and pool["delta_bar_meV"][d] is not None
              and abs(pool["delta_bar_meV"][d]) <= RULES["DELTA_BAR_MAX_MEV"] and sep["c5_far"])
        out[d] = {"sublattice": L, "a1": a1, "calibrated": cal, "heterogeneity": {"A1": het1, "calibrated": hetc},
                  "dopant_specific": ds, "no_class_reasons": noclass, "flag": flag,
                  "controls": {"C2": c2, "C3": c3, "C4": {"pass": c4, "n_d": len(valid_hosts), "n": n},
                               "C5": {"pass": c5, "m_d": pool["m"][d], "df_delta": pool["df_delta"],
                                      "delta_bar_meV": pool["delta_bar_meV"][d], "delta_far_valid": sep["c5_far"]}},
                  "hosts": hv[d], "a_pose_meV": ap, "required_hosts": required_hosts(a1.get("s_Y_meV"))}

    # Sr: C1 and the A1-tier control (I-C7, I-C8)
    sr = out["Sr"]
    sr_cal_repels = (sr["calibrated"].get("class_rule_v") == "repels" and not sr["flag"] and not sr["no_class_reasons"])
    C1 = (sr_cal_repels and sr["controls"]["C2"]["pass"] and sr["controls"]["C4"]["pass"]
          and sr["controls"]["C5"]["pass"])
    sr_a1_repels = (sr["a1"].get("class_rule_v") == "repels" and not sr["flag"] and not sr["no_class_reasons"]
                    and sr["controls"]["C2"]["pass"] and sr["controls"]["C3"] and sr["controls"]["C4"]["pass"])
    for d in TOKENS:
        r = out[d]
        ctl = r["controls"]
        ctl["C1"] = C1
        # validated class (calibrated tier)
        cv = r["calibrated"].get("class_rule_v")
        fails = [k for k, ok in (("C1", C1), ("C2", ctl["C2"]["pass"]), ("C3", ctl["C3"]), ("C4", ctl["C4"]["pass"]),
                                 ("C5", ctl["C5"]["pass"])) if not ok]
        why = list(r["no_class_reasons"]) + (["heterogeneous shell"] if r["flag"] else []) + \
            [f"control {k} failed" for k in fails]
        if not r["calibrated"].get("available"):
            why.append(f"calibrated tier not available ({r['calibrated'].get('reason')})")
        elif cv not in CLASSES:
            why.append(cv)
        r["calibrated"]["class_validated"] = cv if (cv in CLASSES and not why) else None
        r["calibrated"]["no_class_reasons"] = why
        multi = _pose_mode(table["hosts"][table["production"][0]], d) == "multi"
        lab = LABEL_VALIDATED + (f" {LABEL_MULTI_POSE}." if multi else "")
        r["calibrated"]["label"] = lab if r["calibrated"]["class_validated"] else None
        if ((table.get("gates") or {}).get("pose") or {}).get(d, {}).get("mode") == "multi" and d in ("Cs", "Cl"):
            near = table["gates"]["pose"][d].get("near") or {}
            r["calibrated"]["pose_note"] = {"label": LABEL_MULTI_POSE, "delta_pose_cal_site_meV":
                                            table["gates"]["pose"][d].get("delta_near_meV"),
                                            **{k: near.get(k) for k in ("N_D", "N_DV", "count_term_meV")}}   # N-F26
        # A1 tier class (I-18)
        a1c = r["a1"].get("class_rule_v")
        a1fail = [x for x, ok in (("Sr does not repel at the A1 tier", sr_a1_repels), ("C2", ctl["C2"]["pass"]),
                                  ("C3", ctl["C3"]), ("C4", ctl["C4"]["pass"])) if not ok]
        if not r["a1"]["available"]:
            r["a1"]["class"] = f"no class ({r['a1']['reason']})"
        elif r["no_class_reasons"]:
            r["a1"]["class"] = "no class (" + "; ".join(r["no_class_reasons"]) + ")"
        elif r["flag"]:
            r["a1"]["class"] = "no class (heterogeneous shell)"
        elif a1fail:
            r["a1"]["class"] = "no class (A1-tier control failed: " + "; ".join(a1fail) + ")"
        else:
            r["a1"]["class"] = a1c
        r["a1"]["controls"] = {"Sr_repels_A1": sr_a1_repels, "C2": ctl["C2"]["pass"], "C3": ctl["C3"],
                               "C4": ctl["C4"]["pass"], "no_flag": not r["flag"]}
        r["U_d"] = {"A1": r["a1"].get("U_meV"), "calibrated": r["calibrated"].get("U_meV")}
        if d == "GA":
            r["pose_label"] = LABEL_GA_POSE
    rank = ranking(table, {d: out[d] for d in TOKENS}, hv, pool)
    res = {"per_dopant": out, "delta_pool": pool, "delta_far": dfar, "separability": sep, "ranking": rank,
           "constants": copy.deepcopy(RULES), "scope_label": LABEL_SCOPE, "n": n, "production": table["production"]}
    if reported_items:
        res["reported"] = reported(table, res, hv, dl, pool, dfar)
    return res


# ---------------------------------------------------------------- §15 reported items
def _mace_eb(H, labels):
    E = H.get("E_mace") or {}

    def leg(labs):
        v = [E.get(x) for x in labs]
        if not v or any(x is None for x in v):
            return None
        return v[0] if len(v) == 1 else g49.leg_free_energy(v)
    return g49.eb_meV(leg(labels["DV"]), leg(labels["D"]), E.get(labels["V"]), E.get(labels["host"]))


def _counts(labels):
    """§9 (N-F26): the numbers of kept minima per leg and the count term k_BT ln(N_D/N_D+V) of an aggregated E_b."""
    nD, nDV = len(labels.get("D") or []), len(labels.get("DV") or [])
    return {"N_D": nD, "N_DV": nDV, "count_term_meV": KT * math.log(nD / nDV) if nD and nDV else None}


def _mace_pilot(table):
    """§15 (N-F27): zero-shot MACE E_b of the pilot cells: the calibration start-set quartets of m30 and m05 beside the
    A1 DFT E_b from k = 0 of their A2 cells, and the m30 pose-pilot sites (default pose and kept-minima aggregate)."""
    out = {"label": LABEL_MACE, "calibration": {}, "pose_pilot": {}}
    for p in PILOTS:
        H = table["hosts"].get(p)
        if not H or not H.get("E_mace"):
            continue
        A = (table.get("a2") or {}).get(p) or {}
        for L in ("B", "A", "X"):
            j = int(((table.get("a2_sites") or {}).get(p) or {}).get(L, 0) or 0)
            if not j:
                continue
            for d in g49.TOKENS_OF[L]:
                labs = {"host": g49.lab_host(p), "V": g49.lab_v(p, L, j), "D": [g49.lab_dop(p, d, j, "novac", 0)],
                        "DV": [g49.lab_dop(p, d, j, "vac", 0)]}
                a2l = {"host": f"s2r_{p}_host{L}{j}", "V": f"s2r_{p}_V{L}{j}", "D": g49.lab_dop(p, d, j, "novac", 0, "s2r"),
                       "DV": g49.lab_dop(p, d, j, "vac", 0, "s2r")}
                F0 = {k: (A.get(v) or {}).get("F0_eV") for k, v in a2l.items()}
                out["calibration"].setdefault(p, {})[f"{d}{j}"] = {
                    "Eb_mace_meV": _mace_eb(H, labs), "Eb_A1_dft_meV": g49.eb_meV(F0["DV"], F0["D"], F0["V"], F0["host"]),
                    "A1_dft_from": "k = 0 of the A2 cells (section 11)", "label": LABEL_MACE}
        for T, sites_ in (((H.get("pose_pilot") or {}).items()) if p == "m30" else ()):
            for j, legs in sites_.items():
                L = SUBLATTICE[T]
                kept = {"host": g49.lab_host(p), "V": g49.lab_v(p, L, int(j)),
                        "D": [g49.lab_dop(p, T, int(j), "novac", int(o[1:])) for o in legs.get("novac") or []],
                        "DV": [g49.lab_dop(p, T, int(j), "vac", int(o[1:])) for o in legs.get("vac") or []]}
                dflt = {**kept, "D": [g49.lab_dop(p, T, int(j), "novac", 0)], "DV": [g49.lab_dop(p, T, int(j), "vac", 0)]}
                out["pose_pilot"][f"{T}{j}"] = {"Eb_mace_default_meV": _mace_eb(H, dflt),
                                                "Eb_mace_aggregate_meV": _mace_eb(H, kept) if kept["D"] and kept["DV"]
                                                else None, **_counts(kept), "label": LABEL_MACE}
    return out


def reported(table, res, hv, dl, pool, dfar):
    """Every §15 item computable from the table (no decision rests on these)."""
    rep = {}
    # per-site values, raw E_b, far values, zero-shot MACE E_b (the per-chemistry ledger)
    per_site, mace = {}, {}
    for d in TOKENS:
        per_site[d], mace[d] = {}, {}
        for h in table["production"]:
            r = hv[d][h]
            multi = _pose_mode(table["hosts"][h], d) == "multi"
            per_site[d][h] = {"first": {str(j): {"Eb_meV": q["Eb_meV"], "valid": q["valid"], "e_meV": r["e_meV"].get(j),
                                                 **(_counts(q["labels"]) if multi else {})}
                                        for j, q in r["first"].items()},
                              "far": {str(f): {"Eb_meV": q["Eb_meV"], "valid": q["valid"],
                                               **(_counts(q["labels"]) if multi else {})} for f, q in r["far"].items()},
                              "Y_h_meV": r["Y_h_meV"], "Delta_h_meV": r["Delta_h_meV"], "host_valid": r["valid"]}
            mace[d][h] = {str(j): _mace_eb(table["hosts"][h], q["labels"])
                          for j, q in list(r["first"].items()) + list(r["far"].items())}
    rep["per_site"] = per_site
    rep["mace_ledger"] = {"label": LABEL_MACE, "Eb_meV": mace}
    # noise-pilot per-site values with the zero-shot MACE values (pilot hosts present in the table)
    noise = {}
    for p in PILOTS:
        H = table["hosts"].get(p)
        if not H or "far4" not in (table.get("sites", {}).get(p) or {}):
            continue
        noise[p] = {}
        for L, fs in table["sites"][p]["far4"].items():
            for f in fs:
                for d in g49.TOKENS_OF[L]:
                    q = quartet_a1(table, p, d, int(f))
                    noise[p][f"{d}{f}"] = {"Eb_meV": q["Eb_meV"], "valid": q["valid"],
                                           "Eb_mace_meV": _mace_eb(H, q["labels"]), "mace_label": LABEL_MACE,
                                           **(_counts(q["labels"]) if len(q["labels"]["D"]) + len(q["labels"]["DV"]) > 2
                                              else {})}
    rep["noise_pilot"] = noise
    rep["mace_ledger"]["pilot"] = _mace_pilot(table)                       # N-F27
    # shared-region sensitivity (I-19)
    regions = sum(1 for L, toks in g49.TOKENS_OF.items() if any(pool["m"][d] == 2 for d in toks))
    sens = {"regions": regions, "per_dopant": {}}
    if regions == 0:
        sens["per_dopant"] = None
    else:
        sep2 = g49.separability(dfar["delta_meV"] if dfar["valid"] else None, pool["s_delta_meV"], regions)
        for d in TOKENS:
            Y = [hv[d][h]["Y_h_meV"] for h in table["production"] if hv[d][h]["valid"]]
            c = tier_cal(Y, pool, d, sep2["a_far_meV"], a_pose_of(table, d), df_override=regions)
            sens["per_dopant"][d] = {k: c.get(k) for k in ("available", "nu", "t_star", "interval_meV", "reason")}
        sens["a_far_meV"] = sep2["a_far_meV"]
    rep["shared_region_sensitivity"] = sens
    # plateau-excluded intervals (N-C9)
    flagged = {d: [p for p in PILOTS if dl[d][p]["valid"] and dl[d][p]["plateau"]] for d in TOKENS}
    pool_np = pooled_delta({d: [dl[d][p]["delta_meV"] for p in PILOTS if dl[d][p]["valid"] and not dl[d][p]["plateau"]]
                            for d in TOKENS})
    far_np = dfar["delta_meV"] if dfar["valid"] and not dfar["plateau"] else None
    sep_np = g49.separability(far_np, pool_np["s_delta_meV"], pool_np["df_delta"])
    pex = {"flagged_deltas": flagged, "delta_far_plateau": bool(dfar.get("plateau")), "pool": pool_np,
           "separability": sep_np, "per_dopant": {}}
    for d in TOKENS:
        Y = [hv[d][h]["Y_h_meV"] for h in table["production"] if hv[d][h]["valid"]]
        c = tier_cal(Y, pool_np, d, sep_np["a_far_meV"], a_pose_of(table, d))
        pex["per_dopant"][d] = {k: c.get(k) for k in ("available", "theta_meV", "nu", "t_star", "interval_meV", "reason")}
    rep["plateau_excluded"] = pex
    # invalid-cell table (§§5, 11, 12)
    inv = []
    rx = re.compile(r"s2r?_m\d\d_(?:V(?P<L>[BAX])(?P<vj>\d+)|host(?P<hL>[BAX])(?P<hj>\d+)|(?P<T>Sr|Ca|Cl|Cs|GA)(?P<j>\d+)o\d+_"
                    r"(?:novac|vac))")

    def who(lab):
        m = rx.fullmatch(lab)
        if not m:
            return {"dopant": None, "site": None}
        return {"dopant": m.group("T"), "site": int(m.group("j") or m.group("vj") or m.group("hj"))}
    for h, H in sorted(table["hosts"].items()):
        for lab, ok in sorted((H.get("cell_valid") or {}).items()):
            if ok is not True:
                inv.append({"host": h, "label": lab, **who(lab), "failed_checks": (H.get("failed_checks") or {}).get(lab)})
        if H.get("host_valid") is not True:
            inv.append({"host": h, "label": g49.lab_host(h), "failed_checks": "host relaxation"})
    for p, A in sorted((table.get("a2") or {}).items()):
        for lab, c in sorted(A.items()):
            # an A2 cell is invalid by §11 (end rule, final-geometry checks 2-5); the A1 validity of its start cell is
            # reported beside it (an invalid A1 start cell is itself listed above, among the A1 cells of its host)
            if c.get("valid_final") is False or c.get("end_rule") not in RULES["END_ACCEPTED"]:
                inv.append({"host": p, "label": lab, **who(lab), "failed_checks": c.get("failed_checks"),
                            "end_rule": c.get("end_rule"), "a1_start_valid": c.get("a1_valid")})
    rep["invalid_cells"] = inv
    # DFT residual forces on the free atoms of every A1 cell
    rep["residual_forces"] = {h: H.get("forces") for h, H in sorted(table["hosts"].items()) if H.get("forces")}
    # per A2 cell: relaxation energy, configuration count, restarts, attribution
    a2r = {}
    for p, A in sorted((table.get("a2") or {}).items()):
        for lab, c in sorted(A.items()):
            dE = (c["Ffin_eV"] - c["F0_eV"]) * 1000.0 if c.get("F0_eV") is not None and c.get("Ffin_eV") is not None \
                and c.get("status", "complete") == "complete" else None                # R4-C24-3: complete cells only
            a2r[lab] = {"relaxation_energy_meV": dE, "n_config": c.get("n_config"), "restarts": c.get("restarts"),
                        "end_rule": c.get("end_rule"), "attribution": c.get("attribution")}
    rep["a2_cells"] = a2r
    # q = 0 link rows (§10) beside q = +1
    q0 = {}
    H = table["hosts"].get("m30") or {}
    F = H.get("F") or {}
    A30 = (table.get("a2") or {}).get("m30") or {}
    for L, j, toks in (("B", 136, ("Sr", "Ca")), ("B", 76, ("Sr",)), ("X", 138, ("Cl",)), ("A", 128, ("Cs", "GA"))):
        v0 = g49.lab_v("m30", L, j) + "_q0"
        for d in toks:
            dv0 = g49.lab_dop("m30", d, j, "vac") + "_q0"
            dl_, d_a2 = g49.lab_dop("m30", d, j, "novac"), g49.lab_dop("m30", d, j, "novac", 0, "s2r")
            FD = F.get(dl_) if F.get(dl_) is not None else (A30.get(d_a2) or {}).get("F0_eV")   # k = 0 of its A2 cell
            q0[f"{d}{j}"] = {"F_V_q0_eV": F.get(v0), "F_DV_q0_eV": F.get(dv0),
                             "Eb_q0_meV": g49.eb_meV(F.get(dv0), FD, F.get(v0), F.get(g49.lab_host("m30"))),
                             "D_source": "SP" if F.get(dl_) is not None else "k = 0 of the A2 relaxation",
                             "label": "q = 0 link row (§10), reported only"}
    rep["q0_rows"] = q0
    # WP2c comparison where the S2 calibration quartets exist (A1 = k = 0 of A2; different protocol)
    wp = (table.get("pilot_extra") or {}).get("wp2c") or {}
    cmp_ = {}
    for key, (p, d, j) in {"m30_Sr136": ("m30", "Sr", 136), "m30_GA128": ("m30", "GA", 128),
                           "m05_Sr124": ("m05", "Sr", 124)}.items():
        q = _a2_quartet(table, p, d, SUBLATTICE[d], j)
        cmp_[key] = {"wp2c": wp.get(key), "S2_Eb_A1_meV": q["Eb_A1_meV"], "S2_Eb_A2_meV": q["Eb_A2_meV"],
                     "S2_valid": q["valid"],
                     "label": "WP2c: whole-cell WP1 MACE geometry, q = 0, one far site (different protocol)"}
    rep["wp2c_comparison"] = cmp_
    rep["required_hosts"] = {d: res["per_dopant"][d]["required_hosts"] for d in TOKENS}
    rep["pose_pilot"] = ((table.get("gates") or {}).get("pose")) or None
    rep["determinism"] = (table.get("pilot_extra") or {}).get("determinism")
    rep["throughput"] = (table.get("pilot_extra") or {}).get("throughput")
    rep["D3BJ"] = {"status": "not computed", "reason": "X-1: " + NOTES["X-1"]}
    return rep


# ---------------------------------------------------------------- output
def write_eval(result, path, *, rerun=None, dumper=None):
    """Write s2-eval-1. Refuses an existing file unless this is a rerun (§17 item 6), which goes beside it as
    <stem>.rerun<k>.json; the first output is never overwritten (N-C8)."""
    dumper = dumper or dep("c46").dump_public
    if os.path.exists(path):
        if not rerun:
            raise FileExistsError(f"{path} exists: the one evaluation has been run (§17 item 6)")
        k = 1
        while os.path.exists(re.sub(r"\.json$", f".rerun{k}.json", path)):
            k += 1
        path = re.sub(r"\.json$", f".rerun{k}.json", path)
    elif rerun:
        raise FileNotFoundError(f"rerun requested but {path} (the first output) does not exist")
    body = {"schema": EVAL_SCHEMA, **result, "rerun": rerun}
    dumper(body, path)
    return path


# ---------------------------------------------------------------- assembly from the archive (the only full read)
def _git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True)


def _labels_in(raw_dir):
    out = set()
    for p in glob.glob(os.path.join(raw_dir, "*.out.gz")):
        b = os.path.basename(p)[:-len(".out.gz")]
        if not re.search(r"\.p\d+$", b):
            out.add(b)
    return out


def assemble(archive_root="results/objective2/s2", *, layout=None, sp_parser=None, sp_status=None, relax_parser=None,
             end_rule_fn=None, sites_fn=None, record_loader=None, cal_sites=None, wp1_dir=None):
    """Build the s2-evaltable-1 table from the archived campaigns (interface spec §5.2). Reads every SP in full mode
    (scripts/47 parse_sp after sp_status), every A2 relaxation in full mode (k <= 200), and the cell records with
    their MACE energies (scripts/46 load_record, blind=False). The parsers can be injected (self-test)."""
    q = None
    if not all((sp_parser, sp_status, relax_parser, end_rule_fn)):
        q = dep("q47")
    sp_parser = sp_parser or q.parse_sp
    sp_status = sp_status or q.sp_status
    relax_parser = relax_parser or q.parse_relax
    end_rule_fn = end_rule_fn or q.end_rule
    load = record_loader or (lambda p: dep("c46").load_record(p, blind=False))
    if layout is None:
        layout = dep("c46").Layout(kind="archive", root=archive_root)
    cdir = layout.campaign_dir
    state = {}
    for c in ("c1", "c2", "c3", "c4"):                       # the latest campaign's state holds every decision
        p = os.path.join(cdir(c), "state_end.json")
        if os.path.exists(p):
            state = json.load(open(p))
    n = int(state.get("n", RULES["N_BASE"]))
    st0 = state.get("stage0") or {}
    production = list(st0.get(f"production_n{n}") or [])[:n]
    if len(production) != n:
        raise ValueError(f"state_end: production list of {len(production)} hosts for n = {n}")
    if sites_fn is None:
        c46 = dep("c46")

        def sites_fn(member):
            s = c46.site_sets(c46.host_context(member))
            return {L: {"first": list(s[L]["first"]), "far": list(s[L]["far"]),
                        **({"far4": list(s[L]["far4"])} if member in PILOTS else {})} for L in ("B", "A", "X")}
    sites = {}
    for h in production + list(PILOTS):
        s = sites_fn(h)
        sites[h] = {L: {"first": [int(x) for x in s[L]["first"]], "far": [int(x) for x in s[L]["far"]]}
                    for L in ("B", "A", "X")}
        if h in PILOTS:
            sites[h]["far4"] = {L: [int(x) for x in s[L]["far4"]] for L in ("B", "A", "X") if "far4" in s[L]}
    hosts = {h: {"host_valid": False, "F": {}, "cell_valid": {}, "failed_checks": {}, "pair_rejected": {}, "pose": {},
                 "E_mace": {}, "forces": {}} for h in production + list(PILOTS)}

    def gate(c, name):
        p = layout.gate(c, name)
        return json.load(open(p)) if os.path.exists(p) else None
    pose_g = gate("c1", "pose")
    rec_by_label, rec_by_wid = {}, {}
    for c in ("c1", "c3"):
        for p in sorted(glob.glob(os.path.join(cdir(c), "records", "*.json"))):
            r = load(p)
            h = r.get("member")
            if h not in hosts:
                continue
            rec_by_wid[(c, r.get("work_id") or os.path.basename(p)[:-5])] = r
            val = r.get("validity") or {}
            if r.get("cell_kind") == "host":
                hosts[h]["host_valid"] = val.get("valid") is True
            for lab in r.get("labels") or []:
                rec_by_label[lab] = r
                hosts[h]["cell_valid"][lab] = val.get("valid") is True
                hosts[h]["failed_checks"][lab] = val.get("failed")
                hosts[h]["E_mace"][lab] = (r.get("relax") or {}).get("E_mace_eV")
            if r.get("cell_kind") in ("D", "DV") and r.get("token") in ("Cs", "Cl"):
                pf = hosts[h]["pose"].setdefault(r["token"], {"start_failed": {}})
                pf["start_failed"].setdefault(str(r["site"]), {}).setdefault(r["leg"], {})[r.get("start", "p0")] = \
                    val.get("failed") or []
        for p in sorted(glob.glob(os.path.join(cdir(c), "pairs", "*.json"))):
            r = json.load(open(p))
            if p.endswith(".distinct.json"):
                # kept minima o<k> of a multi-start leg (§9): scripts/46 labels only the p0 record, so each kept
                # minimum's label takes the validity of the cell record its work id names (review-2 F4)
                h = r.get("member")
                if h not in hosts:
                    continue
                for o, wid in (r.get("work_ids") or {}).items():
                    rr = rec_by_wid.get((c, wid))
                    lab = (r.get("labels") or {}).get(o) or g49.lab_dop(h, r["token"], int(r["site"]), r["leg"], int(o[1:]))
                    if rr is None:
                        continue
                    val = rr.get("validity") or {}
                    rec_by_label.setdefault(lab, rr)
                    hosts[h]["cell_valid"][lab] = val.get("valid") is True
                    hosts[h]["failed_checks"][lab] = val.get("failed")
                    hosts[h]["E_mace"][lab] = (rr.get("relax") or {}).get("E_mace_eV")
                if c == "c1" and h in PILOTS:                                   # the pose pilot's kept minima (N-F27)
                    hosts[h].setdefault("pose_pilot", {}).setdefault(r["token"], {}).setdefault(
                        str(r["site"]), {})[r["leg"]] = sorted(r.get("map") or {}, key=lambda o: int(o[1:]))
                continue
            if r.get("member") in hosts and r.get("status") == "rejected":
                hosts[r["member"]]["pair_rejected"].setdefault(f"{r['token']}{r['site']}", []).append(r.get("start", "p0"))
        raw = os.path.join(cdir(c), "raw")
        for lab in sorted(_labels_in(raw)):
            m = re.match(r"(?:s2|s2g1|s2spin)_(m\d\d)_", lab)
            if not m or m.group(1) not in hosts:
                continue
            h = m.group(1)
            st = sp_status(raw, lab)
            if st.get("status") != "complete":
                hosts[h]["F"][lab] = None
                continue
            free = (rec_by_label.get(lab) or {}).get("free")
            full = sp_parser(os.path.join(raw, f"{lab}.out.gz"), read="full", free=free)
            hosts[h]["F"][lab] = full["F_eV"]
            if full.get("forces") is not None:
                hosts[h]["forces"][lab] = full["forces"]
    # the pilot hosts' Cs and Cl cells (noise pilot, start set) are default-pose cells (§§8, 11; the m30 pose pilot is
    # kept apart in pose_pilot): mode 'default', so their rows use o0 as gate N does (round-4 R4-C24-4)
    for h in PILOTS:
        for tok in ("Cs", "Cl"):
            hosts[h]["pose"].setdefault(tok, {"start_failed": {}})["mode"] = "default"
    # pose modes of production (the pose gate, unless cut 6/7) and kept minima of multi-pose legs
    mp_cut = state.get("multi_pose_cut") or {}
    for tok in ("Cs", "Cl"):
        mode = ((pose_g or {}).get("decision") or {}).get("pose", {}).get(tok, "multi")
        prod_mode = "default" if mp_cut.get(tok) else mode
        L = SUBLATTICE[tok]
        for h in production:
            pf = hosts[h]["pose"].setdefault(tok, {"start_failed": {}})
            pf["mode"] = prod_mode
            if prod_mode == "multi":
                pf["minima"] = {}
                for j in sites[h][L]["first"] + sites[h][L]["far"]:
                    for leg in LEGS:
                        dp = layout.distinct("c3", h, tok, j, leg)
                        kept = (json.load(open(dp)).get("map") or {}) if os.path.exists(dp) else {}
                        pf["minima"].setdefault(str(j), {})[leg] = sorted(kept, key=lambda o: int(o[1:]))
    # A2 relaxations (C2, C4): F(0) and F(final) with k <= 200, end rule, final validity, A1 start validity
    m05 = st0.get("m05_cal")
    a2 = {p: {} for p in PILOTS}
    sm_path = os.path.join(cdir("c1"), "smoke.json")
    mapping = (json.load(open(sm_path)).get("mapping") if os.path.exists(sm_path) else None)
    for c, labs in g49.build_a2_order(m05).items():
        for lab in labs:
            rp = os.path.join(layout.a2_dir(c, lab), f"{lab}.a2.json")
            if not os.path.exists(rp):
                continue
            rec = json.load(open(rp))
            # only a complete relaxation is read: a killed, missing or not-run one had its outputs moved aside unread
            # (section 16), and none is parsed here even if a part output were left (round-4 R4-C24-3)
            parts = layout.a2_parts(c, lab) if rec.get("status") == "complete" else []
            if len(parts) > 1 and mapping is None:
                raise ValueError(f"{lab}: {len(parts)} parts but no c1/smoke.json mapping to join them (review-2 F8)")
            # the same C1 smoke-test mapping as the runner and the gates (exit marker, restart counters; X-3)
            rel = relax_parser(parts, read="full", mapping=mapping) if parts else None
            er = end_rule_fn(rel) if rel is not None else {"outcome": rec.get("status") if rec.get("status") not in
                                                           (None, "complete") else "missing"}
            F = (rel or {}).get("F_eV") or {}
            kl = (rel or {}).get("k_last")
            vf = rec.get("validity_final")
            a1 = rec_by_label.get(_a1_label(lab))
            a2[g49.a2_cell(lab)["pilot"]][lab] = {
                "F0_eV": F.get(0), "Ffin_eV": F.get(kl) if kl is not None else None, "end_rule": er.get("outcome"),
                "plateau": er.get("outcome") == "accepted_plateau",
                "valid_final": None if vf is None else vf.get("valid") is True,
                "failed_checks": None if vf is None else vf.get("failed"),
                "a1_valid": ((a1.get("validity") or {}).get("valid") is True) if a1 else _a1_host_valid(hosts, lab),
                "status": rec.get("status"), "n_config": (rel or {}).get("n_config", rec.get("n_config")),
                "restarts": rec.get("restarts"), "k_last": kl,
                "attribution": path_work(rel, _region_centres(layout, lab)) if rel else None}
    g1, gN, k2, k3 = gate("c1", "G1"), gate("c1", "N"), gate("c2", "K2"), gate("c2", "K3")
    s0 = gate("c2", "step0")
    gates = {"G1": (g1 or {}).get("decision", {}).get("G1", {}),
             "N": {d: {"pass": v["pass"], "sigma_far_meV": v["sigma_far_meV"], "df": v["df"]}
                   for d, v in ((gN or {}).get("result", {}).get("dopants", {})).items()},
             "pose": {tok: {**{k: v for k, v in r.items() if k in ("mode", "a_pose_meV", "delta_near_meV",
                                                                   "delta_far_meV")},
                            **{s: {k: (r.get(s) or {}).get(k) for k in ("N_D", "N_DV", "count_term_meV")}
                               for s in ("near", "far") if isinstance(r.get(s), dict)}}           # N-F26
                      for tok, r in ((pose_g or {}).get("result") or {}).items()},
             "cuts": state.get("cuts", []), "multi_pose_cut": mp_cut,
             "K2": (k2 or {}).get("decision"), "K3": (k3 or {}).get("decision"), "step0": (s0 or {}).get("decision")}
    extra = {"throughput": None, "wp2c": _wp2c_values(), "determinism": _determinism(hosts, cdir, wp1_dir)}
    tp = os.path.join(cdir("c1"), "throughput.json")
    if os.path.exists(tp):
        extra["throughput"] = json.load(open(tp))
    cal = cal_sites or {**(getattr(dep("c46"), "CAL_SITES", None) or {}),
                        **({"m05": {**g49.M05_CAL_DEFAULT, **m05}} if m05 else {})}
    return {"schema": TABLE_SCHEMA, "n": n, "production": production, "dopants": list(TOKENS), "sites": sites,
            "hosts": hosts, "a2": a2, "a2_sites": _a2_sites(cal), "gates": gates, "pilot_extra": extra,
            "state": state}


def _region_centres(layout, a2_label):
    """Centres (relaxed-host v and site j, A) of the region record of an A2 cell's site (§4), if archived."""
    c = g49.a2_cell(a2_label)
    if not hasattr(layout, "region"):
        return None
    p = layout.region("c1", c["pilot"], c["L"], c["site"])
    if not os.path.exists(p):
        return None
    cen = json.load(open(p)).get("centres") or {}
    return [cen[k] for k in ("v", "site") if k in cen] or None


def path_work(rel, centres=None, shells=(0.0, 4.0, 6.0, 8.0, 1e9)):
    """§15 per-A2 attribution in the scripts/38 style: the work on each atom along the path, W_i = -sum_k 1/2 (F_i^k +
    F_i^(k+1)) . (r_i^(k+1) - r_i^k) (trapezoid, eV), summed per distance shell from the nearest centre (A, start
    geometry; centres = list of [x, y, z] recorded by the driver) and closed against F(final) - F(0)."""
    import numpy as np
    X, Fo, F = rel.get("positions_A") or {}, rel.get("forces_eVA") or {}, rel.get("F_eV") or {}
    ks = sorted(k for k in X if k in Fo)
    if len(ks) < 2 or ks != list(range(len(ks))):
        return None
    W = np.zeros(len(X[ks[0]]))
    for a, b in zip(ks[:-1], ks[1:]):
        dr = np.asarray(X[b]) - np.asarray(X[a])
        W -= 0.5 * np.einsum("ij,ij->i", np.asarray(Fo[a]) + np.asarray(Fo[b]), dr)
    out = {"total_meV": float(W.sum()) * 1000.0,
           "closure_meV": float(W.sum() - (F[ks[-1]] - F[ks[0]])) * 1000.0 if ks[0] in F and ks[-1] in F else None}
    dr2 = ((np.asarray(X[ks[-1]]) - np.asarray(X[ks[0]])) ** 2).sum(axis=1)      # QE positions are not re-wrapped
    out["sum_dr2_A2"] = float(dr2.sum())
    if centres:
        d = np.min(np.linalg.norm(np.asarray(X[ks[0]])[:, None, :] - np.asarray(centres)[None, :, :], axis=2), axis=1)
        out["shells_meV"] = {f"{lo:g}-{hi:g}": float(W[(d >= lo) & (d < hi)].sum()) * 1000.0
                             for lo, hi in zip(shells[:-1], shells[1:])}
        out["shells_dr2_A2"] = {f"{lo:g}-{hi:g}": float(dr2[(d >= lo) & (d < hi)].sum())
                                for lo, hi in zip(shells[:-1], shells[1:])}
    return out


def _determinism(hosts, cdir, wp1_dir=None):
    """§5 determinism check (reported only): S2 pilot host MACE energy against the WP1 E_host and, when the archived
    structures are readable, the largest MIC displacement against the WP1 relaxed host."""
    wp1 = wp1_dir or os.path.join(ROOT, "results/objective2/dopant_shell/wp1_production")
    out = {}
    for p in PILOTS:
        r = {"E_S2_mace_eV": (hosts.get(p) or {}).get("E_mace", {}).get(g49.lab_host(p)), "E_WP1_eV": None,
             "dE_meV": None, "max_dr_A": None, "label": LABEL_MACE}
        sj = os.path.join(wp1, f"shell_{p}.json")
        if os.path.exists(sj):
            r["E_WP1_eV"] = json.load(open(sj))["E_host"]["E_eV"]
        if r["E_S2_mace_eV"] is not None and r["E_WP1_eV"] is not None:
            r["dE_meV"] = (r["E_S2_mace_eV"] - r["E_WP1_eV"]) * 1000.0
        try:
            import io
            from ase.io import read as aread
            from ase.geometry import find_mic
            with tarfile.open(os.path.join(wp1, "v2prod_structures.tar.gz")) as t:
                ref = aread(io.StringIO(t.extractfile(f"v2prod/{p}_host_relaxed.extxyz").read().decode()),
                            format="extxyz")
            with tarfile.open(os.path.join(cdir("c1"), "structures.tar.gz")) as t:
                mem = [m for m in t.getmembers() if m.name.endswith(f"s2_{p}_host/relaxed.extxyz")]
                s2 = aread(io.StringIO(t.extractfile(mem[0]).read().decode()), format="extxyz") if mem else None
            if s2 is not None and len(s2) == len(ref):
                r["max_dr_A"] = float(find_mic(s2.positions - ref.positions, ref.cell.array, pbc=True)[1].max())
        except (OSError, KeyError, IndexError, tarfile.TarError):
            pass
        out[p] = r
    return out


def _a1_label(a2_label):
    """The A1 label whose cell starts an A2 relaxation (host_R: the host SP label)."""
    c = g49.a2_cell(a2_label)
    if c["kind"] == "host":
        return g49.lab_host(c["pilot"])
    return a2_label.replace("s2r_", "s2_", 1)


def _a1_host_valid(hosts, a2_label):
    c = g49.a2_cell(a2_label)
    return c["kind"] == "host" and hosts[c["pilot"]]["host_valid"] is True


def _a2_sites(cal):
    """Calibration sites (§11) from scripts/46 CAL_SITES, and the Sr far quartet at Pb76 on m30."""
    cal = cal or {}
    out = {p: {L: int(cal[p][L]) for L in ("B", "A", "X")} for p in PILOTS if p in cal}
    out["far"] = {"pilot": "m30", "L": "B", "site": 76, "token": "Sr"}
    return out


def _wp2c_values():
    """WP2c raw and far-referenced DFT E_b at Pb136 (Sr) and FA128 (GA) on m30 and Pb124 (Sr) on m05 (§15)."""
    p = os.path.join(ROOT, "results/objective2/dopant_shell/wp2c/wp2cde_dft.json")
    if not os.path.exists(p):
        return None
    w = json.load(open(p))["wp2c"]
    pick = {"m30_Sr136": ("m30", "Sr", 136), "m30_GA128": ("m30", "GA", 128), "m05_Sr124": ("m05", "Sr", 124)}
    out = {}
    for key, (h, d, j) in pick.items():
        rows = [r for r in w[h][d]["rows"].values() if r.get("site") == j]
        out[key] = {k: rows[0].get(k) for k in ("Eb_dft_meV", "Eb_dft_farref_meV")} if rows else None
    return out


# ---------------------------------------------------------------- CLI guards (§17 item 6)
def _c4_ended(archive):
    p = os.path.join(archive, "c4", "campaign.json")
    if os.path.exists(p):
        c = json.load(open(p))
        if c.get("status") in ("done", "ended") or (c.get("campaigns") or {}).get("c4") == "done":
            return True, "c4/campaign.json: C4 ended"
    for c in ("c3", "c2", "c1"):
        sp = os.path.join(archive, c, "state_end.json")
        if os.path.exists(sp):
            st = json.load(open(sp))
            if not g49.c4_planned(st):
                return True, f"{c}/state_end.json: C4 not run (cuts {st.get('cuts')}, K2 {st.get('K2')}, " \
                             f"K3 {st.get('K3')}, step-0 {st.get('step0')})"
            return False, f"{c}/state_end.json plans C4 and no c4/campaign.json records its end"
    return False, "no campaign record"


def _clean_and_committed():
    if _git("rev-parse", "HEAD").returncode != 0:
        return None, "not a git checkout"
    if _git("status", "--porcelain").stdout.strip():
        return None, "working tree not clean"
    for fn in ("46_s2_cells.py", "47_s2_qe.py", "48_s2_analysis.py", "49_s2_gates.py"):
        if _git("ls-files", "--error-unmatch", f"scripts/{fn}").returncode != 0:
            return None, f"scripts/{fn} not committed"
    return _git("rev-parse", "HEAD").stdout.strip(), None


ANALYSIS_FILES = ("scripts/46_s2_cells.py", "scripts/47_s2_qe.py", "scripts/48_s2_analysis.py", "scripts/49_s2_gates.py")


def _campaign_state(archive):
    """The latest state_end.json (C4, then C3, C2, C1), or {}."""
    for c in ("c4", "c3", "c2", "c1"):
        p = os.path.join(archive, c, "state_end.json")
        if os.path.exists(p):
            return json.load(open(p))
    return {}


def _campaign_commit(archive):
    """The S2 campaign commit recorded in the latest state_end.json (C4, then C3, C2, C1), or None."""
    return _campaign_state(archive).get("commit")


def _commit_history(archive):
    """Every commit change during the campaigns (c1/NODE_FIX, c2/STEP0_FIX) from the latest state_end.json."""
    return list(_campaign_state(archive).get("commit_history") or [])


HISTORY_FILES = ANALYSIS_FILES + ("scripts/50_s2_campaign.py", "ehpc/node")


def analysis_guard(campaign_commit, head, amendment=None, root=ROOT, commit_history=None):
    """§17 item 6 (round-3 R3C-6, N-F29; round-4 R4-C24-5, R4-C1-6): the analysis code of scripts/46-49 at HEAD against
    the campaign commit. Returns (ok, record) for s2_eval.json analysis_identity: the diff's stat, its sha256 and its
    text (written beside s2_eval.json by cmd_evaluate). Equal code passes. A difference passes only with --amendment, a
    committed, clean note outside scripts/ that was added or changed after the campaign commit and carries an ISO date
    not earlier than that commit's date (D-S0-4 foresees such a dated amendment). A given amendment is checked by the
    same rules and recorded (path, sha256) also when the code is unchanged. Every commit change during the campaigns
    (commit_history: NODE_FIX, STEP0_FIX) is reported with the diff stat of scripts/46-50 and ehpc/node between its two
    commits (report only, no refusal)."""
    g = lambda *a: subprocess.run(["git", "-C", root, *a], capture_output=True, text=True)   # noqa: E731
    rec = {"campaign_commit": campaign_commit, "head": head, "files": list(ANALYSIS_FILES), "diff_stat": None,
           "diff_sha256": None, "diff_text": None, "amendment": None, "commit_history": []}
    for e in commit_history or []:
        a_, b_ = (e or {}).get("from"), (e or {}).get("to")
        st = g("diff", "--stat", str(a_), str(b_), "--", *HISTORY_FILES) if a_ and b_ else None
        rec["commit_history"].append({**{k: v for k, v in (e or {}).items() if k in ("from", "to", "note", "time", "via")},
                                      "diff_stat_46_50": st.stdout.strip() if st is not None and st.returncode == 0
                                      else "unavailable (a commit is not in this checkout)"})
    if not campaign_commit:
        return False, {**rec, "reason": "no campaign commit in state_end.json"}
    d = g("diff", "--stat", campaign_commit, head, "--", *ANALYSIS_FILES)
    full = g("diff", campaign_commit, head, "--", *ANALYSIS_FILES)
    if d.returncode != 0 or full.returncode != 0:
        return False, {**rec, "reason": f"git diff {campaign_commit[:12]} {head[:12]} failed: {d.stderr.strip()[:200]}"}
    rec["diff_stat"] = d.stdout.strip()
    if rec["diff_stat"]:
        rec["diff_sha256"] = hashlib.sha256(full.stdout.encode()).hexdigest()
        rec["diff_text"] = full.stdout
    if amendment:
        rel = os.path.relpath(os.path.abspath(amendment), root)
        why = None
        if rel.startswith("..") or rel.split(os.sep)[0] == "scripts":
            why = f"the amendment {rel} must be a note outside scripts/ (R4-C24-5)"
        elif g("ls-files", "--error-unmatch", rel).returncode != 0 or g("status", "--porcelain", "--", rel).stdout.strip():
            why = f"the amendment {rel} is not committed"
        elif rel not in g("diff", "--name-only", "--diff-filter=AM", campaign_commit, head).stdout.split("\n"):
            why = f"the amendment {rel} was not added or changed after the campaign commit {campaign_commit[:12]}"
        else:
            txt = open(os.path.join(root, rel)).read()
            day = g("show", "-s", "--format=%cs", campaign_commit).stdout.strip()
            dates = re.findall(r"\b20\d\d-\d\d-\d\d\b", txt)
            if not dates:
                why = f"the amendment {rel} carries no date"
            elif not any(x >= day for x in dates):
                why = f"the amendment {rel} carries no date on or after the campaign commit's ({day})"
            else:
                rec["amendment"] = {"path": rel, "sha256": hashlib.sha256(txt.encode()).hexdigest(), "dates": dates[:5]}
        if why:
            return False, {**rec, "reason": why}
    if rec["diff_stat"] and not rec["amendment"]:
        return False, {**rec, "reason": "scripts/46-49 differ from the campaign commit: --amendment <committed dated "
                                        "note> is required (N-F29)"}
    return True, rec


def _old_module(commit):
    """The analysis module at an earlier commit, exported with git archive into a temporary directory."""
    d = tempfile.mkdtemp(prefix="s2_48_first_")
    tar = os.path.join(d, "scripts.tar")
    r = subprocess.run(["git", "-C", ROOT, "archive", "-o", tar, commit, "scripts"], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git archive {commit}: {r.stderr.strip()}")
    with tarfile.open(tar) as t:
        t.extractall(d, filter="data")
    s = importlib.util.spec_from_file_location("a48_first", os.path.join(d, "scripts", "48_s2_analysis.py"))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def cmd_evaluate(a):
    ok, why = _c4_ended(a.archive)
    if not ok:
        print(f"REFUSED: {why} (§17 item 6: one evaluation after C4)", file=sys.stderr)
        return 3
    commit, err = _clean_and_committed()
    if err:
        print(f"REFUSED: {err} (the evaluation is run at a recorded commit)", file=sys.stderr)
        return 3
    ok, ident = analysis_guard(_campaign_commit(a.archive), commit, getattr(a, "amendment", None),
                               commit_history=_commit_history(a.archive))
    if not ok:
        print(f"REFUSED: {ident['reason']} (§17 item 6)", file=sys.stderr)
        return 3
    rerun = None
    if os.path.exists(a.out):
        if not a.rerun_cause:
            print(f"REFUSED: {a.out} exists; a rerun needs --rerun-cause (§17 item 6)", file=sys.stderr)
            return 3
        first = json.load(open(a.out))
        if a.rerun_cause not in CASES:
            print(f"REFUSED: {a.rerun_cause} is not a self-test case of this file", file=sys.stderr)
            return 3
        try:
            CASES[a.rerun_cause](_this_module())
        except Exception as e:                                     # noqa: BLE001
            print(f"REFUSED: case {a.rerun_cause} fails on the current code: {e}", file=sys.stderr)
            return 3
        try:
            CASES[a.rerun_cause](_old_module(first["commit"]))
            print(f"REFUSED: case {a.rerun_cause} passes on the first code ({first['commit']})", file=sys.stderr)
            return 3
        except Exception as e:                                     # noqa: BLE001 (the expected failure)
            rerun = {"cause": a.rerun_cause, "first_commit": first["commit"], "first_failure": f"{type(e).__name__}: {e}"}
    table = assemble(a.archive)
    res = evaluate(table)
    if ident.get("amendment") and "D3BJ" in (res.get("reported") or {}):
        res["reported"]["D3BJ"]["amendment"] = ident["amendment"]          # D-S0-4: the dated amendment it follows
    sha = {fn: hashlib.sha256(open(os.path.join(HERE, fn), "rb").read()).hexdigest()
           for fn in ("46_s2_cells.py", "47_s2_qe.py", "48_s2_analysis.py", "49_s2_gates.py")}
    diff_text = ident.pop("diff_text", None)
    if diff_text:                                                           # N-F29: the diff itself, beside s2_eval.json
        side = os.path.splitext(a.out)[0] + ".analysis_diff.patch"
        open(side, "w").write(diff_text)
        ident["diff_file"] = os.path.basename(side)
    body = {"commit": commit, "script_sha256": sha, "analysis_identity": ident,
            "inputs_digest": hashlib.sha256(json.dumps(table, sort_keys=True, default=str).encode()).hexdigest(), **res}
    print(f"written {write_eval(body, a.out, rerun=rerun)}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="S2 analysis (rule V, results/objective2/s2/S2_PLAN.md §§12, 14, 15)")
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    e = sub.add_parser("evaluate")
    e.add_argument("--archive", default="results/objective2/s2")
    e.add_argument("--out", default="results/objective2/s2/s2_eval.json")
    e.add_argument("--rerun-cause", default=None, help="self-test case that fails on the first code (§17 item 6)")
    e.add_argument("--amendment", default=None, help="committed dated note when scripts/46-49 differ from the campaign "
                                                      "commit (N-F29)")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if a.cmd == "evaluate":
        return cmd_evaluate(a)
    ap.print_help()
    return 2


# ---------------------------------------------------------------- self-test: synthetic tables only
PROD8 = ["m06", "m02", "m16", "m12", "m32", "m26", "m22", "m23"]
SITES = {"B": {"first": [124, 136], "far": [76, 172]}, "A": {"first": [28, 92, 128], "far": [188, 164]},
         "X": {"first": [49, 53, 90, 102, 125, 126, 137, 138], "far": [175, 186]}}
CAL = {"m30": {"B": 136, "A": 128, "X": 138}, "m05": {"B": 124, "A": 28, "X": 49}}
DCONST = {"Sr": -2.25, "Ca": -1.5, "Cl": 2.75, "Cs": 40.5, "GA": -27.25}     # F_D - F_host offsets (eV), arbitrary


def synth_table(*, seed=20261103, eb=None, far=None, noise=6.0, host_sd=8.0, delta=None, dfar=3.0, offset=-80000.0,
                prod=PROD8, pose=None, multi_cs=False, a_pose=None, gates=None, invalid=(), fail=(), missing_sp=(),
                a2_bad=(), plateau=(), rejected=(), delta_noise=None):
    """Synthetic s2-evaltable-1 with planted E_b: eb[d] = first-shell mean (scalar, or {site: mean}); far[d] = far
    mean; host offsets N(0, host_sd) shared by the 4 far + first sites of (h, d); per-site noise N(0, noise); raw F
    about `offset` eV. delta[d] = {p: planted delta}. invalid / fail / missing_sp hold (h, label) pairs."""
    import numpy as np
    rng = np.random.default_rng(seed)
    eb = eb or {"Sr": 120.0, "Ca": -75.0, "Cl": 0.0, "Cs": 0.0, "GA": 60.0}
    far = far or {d: 0.0 for d in TOKENS}
    delta = delta or {d: {"m30": 4.0, "m05": -6.0} for d in TOKENS}
    pose = pose or {"Cs": "default", "Cl": "default"}
    a_pose = a_pose or {"Cs": 6.0, "Cl": 4.0}
    hosts, sites = {}, {}
    for h in prod:
        sites[h] = copy.deepcopy(SITES)
        Fh = offset + float(rng.uniform(-3, 3))
        H = {"host_valid": True, "F": {g49.lab_host(h): Fh}, "cell_valid": {}, "failed_checks": {}, "pair_rejected": {},
             "pose": {}, "E_mace": {g49.lab_host(h): -1200.0 + float(rng.uniform(-1, 1))}}
        FV = {}
        for L, S in SITES.items():
            for j in S["first"] + S["far"]:
                lab = g49.lab_v(h, L, j)
                FV[(L, j)] = Fh + 3.5 + float(rng.uniform(-0.2, 0.2))
                H["F"][lab], H["cell_valid"][lab], H["failed_checks"][lab] = FV[(L, j)], True, []
                H["E_mace"][lab] = H["E_mace"][g49.lab_host(h)] + 3.0 + float(rng.uniform(-0.1, 0.1))
        for d in TOKENS:
            L = SUBLATTICE[d]
            off = float(rng.normal(0, host_sd))
            mode = "multi" if (d == "Cs" and multi_cs) else "default"
            if d in ("Cs", "Cl"):
                H["pose"][d] = {"mode": mode, "minima": {}, "start_failed": {}}
            for j in SITES[L]["first"] + SITES[L]["far"]:
                base = (eb[d][j] if isinstance(eb[d], dict) else eb[d]) if j in SITES[L]["first"] else far[d]
                e = off + base + float(rng.normal(0, noise))
                FD0 = Fh + DCONST[d] + float(rng.uniform(-0.2, 0.2))
                legs = {}
                for leg in LEGS:
                    K = int(rng.integers(1, 4)) if mode == "multi" else 1
                    x = [0.0] + [float(rng.uniform(0, 40)) for _ in range(K - 1)]      # meV above the leg minimum
                    rng.shuffle(x)
                    legs[leg] = x
                # F_leg(D) = FD0 + corr(D); F_leg(DV) = F_leg(D) + (F_V - F_h) + e/1000
                corr = {leg: g49.boltzmann_meV(legs[leg]) / 1000.0 for leg in LEGS}
                base_leg = {"novac": FD0, "vac": FD0 + corr["novac"] + (FV[(L, j)] - Fh) + e / 1000.0 - corr["vac"]}
                for leg in LEGS:
                    labs = []
                    for k, xk in enumerate(legs[leg]):
                        lab = g49.lab_dop(h, d, j, leg, k)
                        H["F"][lab] = base_leg[leg] + xk / 1000.0
                        H["cell_valid"][lab], H["failed_checks"][lab] = True, []
                        H["E_mace"][lab] = -1190.0 + float(rng.uniform(-1, 1))
                        labs.append(f"o{k}")
                    if mode == "multi":
                        H["pose"][d]["minima"].setdefault(str(j), {})[leg] = labs
                        H["pose"][d]["start_failed"].setdefault(str(j), {})[leg] = {f"p{k}": [] for k in range(len(labs))}
        hosts[h] = H
    for h, lab, checks in fail:
        hosts[h]["cell_valid"][lab], hosts[h]["failed_checks"][lab] = False, list(checks)
        m = re.fullmatch(rf"s2_{h}_(Cs|Cl)(\d+)o(\d+)_(novac|vac)", lab)
        if m and hosts[h]["pose"][m.group(1)]["mode"] == "multi":
            hosts[h]["pose"][m.group(1)]["start_failed"][m.group(2)][m.group(4)][f"p{m.group(3)}"] = list(checks)
    for h, lab in invalid:
        hosts[h]["cell_valid"][lab] = False
    for h, lab in missing_sp:
        hosts[h]["F"][lab] = None
    for h, tj in rejected:
        hosts[h]["pair_rejected"][tj] = True
        for leg in LEGS:
            for k in range(7):
                lab = f"s2_{h}_{tj}o{k}_{leg}"
                hosts[h]["F"].pop(lab, None); hosts[h]["cell_valid"].pop(lab, None)
    # A2 (§11): shared region cells per (pilot, sublattice); planted delta per (d, p)
    a2 = {p: {} for p in PILOTS}
    a2_sites = {p: dict(CAL[p]) for p in PILOTS}
    a2_sites["far"] = {"pilot": "m30", "L": "B", "site": 76, "token": "Sr"}

    def cell(F0, Ff):
        return {"F0_eV": F0, "Ffin_eV": Ff, "end_rule": "accepted_converged", "plateau": False, "valid_final": True,
                "failed_checks": [], "a1_valid": True, "status": "complete", "n_config": int(rng.integers(60, 150)),
                "restarts": 0}
    quartets = [(p, d, SUBLATTICE[d], CAL[p][SUBLATTICE[d]], delta[d][p]) for p in PILOTS for d in TOKENS]
    quartets.append(("m30", "Sr", "B", 76, dfar))
    region = {}
    for p, d, L, j, dl in quartets:
        if (p, L, j) not in region:
            F0h = offset + float(rng.uniform(-3, 3))
            F0v = F0h + 3.5 + float(rng.uniform(-0.2, 0.2))
            region[(p, L, j)] = (F0h, F0v, F0h - float(rng.uniform(0.1, 0.9)), F0v - float(rng.uniform(0.1, 0.9)))
            a2[p][f"s2r_{p}_host{L}{j}"] = cell(region[(p, L, j)][0], region[(p, L, j)][2])
            a2[p][f"s2r_{p}_V{L}{j}"] = cell(region[(p, L, j)][1], region[(p, L, j)][3])
        F0h, F0v, Ffh, Ffv = region[(p, L, j)]
        e1 = (eb[d] if not isinstance(eb[d], dict) else _mean(list(eb[d].values()))) + float(rng.normal(0, noise))
        F0d = F0h + DCONST[d] + float(rng.uniform(-0.2, 0.2))
        F0dv = F0d + (F0v - F0h) + e1 / 1000.0
        Ffd = F0d - float(rng.uniform(0.1, 0.9))
        # E_b^A2 = E_b^A1 + delta
        Ffdv = Ffd + (Ffv - Ffh) + (e1 + dl) / 1000.0
        a2[p][g49.lab_dop(p, d, j, "novac", 0, "s2r")] = cell(F0d, Ffd)
        a2[p][g49.lab_dop(p, d, j, "vac", 0, "s2r")] = cell(F0dv, Ffdv)
    for p, lab, what in a2_bad:
        a2[p][lab].update(what)
    for p, lab in plateau:
        a2[p][lab].update({"end_rule": "accepted_plateau", "plateau": True})
    g = {"G1": {"Cl": True, "Ca": True}, "N": {d: {"pass": True, "sigma_far_meV": 12.0, "df": 6} for d in TOKENS},
         "pose": {tok: {"mode": pose[tok], "a_pose_meV": a_pose[tok] if pose[tok] == "default" else 0.0,
                        "delta_near_meV": a_pose[tok] / 2, "delta_far_meV": -a_pose[tok] / 2} for tok in ("Cs", "Cl")},
         "cuts": [], "multi_pose_cut": {"Cs": False, "Cl": False}}
    if multi_cs:
        g["pose"]["Cs"].update({"mode": "multi", "a_pose_meV": 0.0})
    for k, v in (gates or {}).items():
        if isinstance(v, dict) and isinstance(g.get(k), dict):
            for kk, vv in v.items():
                g[k][kk] = vv if not isinstance(vv, dict) or not isinstance(g[k].get(kk), dict) else {**g[k][kk], **vv}
        else:
            g[k] = v
    return {"schema": TABLE_SCHEMA, "n": len(prod), "production": list(prod), "dopants": list(TOKENS), "sites": sites,
            "hosts": hosts, "a2": a2, "a2_sites": a2_sites, "gates": g, "pilot_extra": {}}


# ---- independent second implementation (§17 item 2): separate code, numpy arrays, t quantiles by bisection on the
# CDF from scipy.special.betainc; it calls none of the helpers above nor scipts/49's Boltzmann functions.
def _ind_tq(q, nu):
    from scipy.special import betainc

    def cdf(t):
        x = nu / (nu + t * t)
        return 1.0 - 0.5 * betainc(nu / 2.0, 0.5, x)
    lo, hi = 0.0, 1.0
    while cdf(hi) < q:
        hi *= 2.0
    while hi - lo > 1e-14 * max(1.0, hi):
        mid = 0.5 * (lo + hi)
        if cdf(mid) < q:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _ind_softmin(xs):
    import numpy as np
    x = np.asarray(xs, dtype=float)
    lo = x.min()
    return lo - 25.7 * np.log(np.exp(-(x - lo) / 25.7).sum())


def independent(table):
    """Recompute every §14 statistic of the table by a separate code path; returns a flat {key: value} dict."""
    import numpy as np
    kt, qs = 25.7, 1 - 0.05 / 8
    out = {}
    prod = table["production"]
    sub = {"Sr": "B", "Ca": "B", "Cl": "X", "Cs": "A", "GA": "A"}
    need = {"B": 2, "A": 2, "X": 6}

    def legF(H, h, d, j, leg):
        po = (H.get("pose") or {}).get(d) or {}
        if po.get("mode") == "multi":
            ks = [int(o[1:]) for o in ((po.get("minima") or {}).get(str(j)) or {}).get(leg, [])]
        else:
            ks = [0]
        if not ks:
            return None
        labs = ["s2_%s_%s%do%d_%s" % (h, d, j, k, leg) for k in ks]
        if any(H["cell_valid"].get(x) is not True or H["F"].get(x) is None for x in labs):
            return None
        F = np.array([H["F"][x] for x in labs])
        if len(F) == 1:
            return float(F[0])
        return float(F.min() + _ind_softmin((F - F.min()) * 1000.0) / 1000.0)

    def quart(h, d, j):
        H = table["hosts"][h]
        L = sub[d]
        hl, vl = "s2_%s_host" % h, "s2_%s_V%s%d" % (h, L, j)
        if not H["host_valid"] or H["F"].get(hl) is None or H["cell_valid"].get(vl) is not True or H["F"].get(vl) is None:
            return None
        a, b = legF(H, h, d, j, "novac"), legF(H, h, d, j, "vac")
        if a is None or b is None:
            return None
        return ((b - a) - (H["F"][vl] - H["F"][hl])) * 1000.0

    Yall, sites_all, Dh = {}, {}, {}
    for d in ("Sr", "Ca", "Cl", "Cs", "GA"):
        L = sub[d]
        Y, per = {}, {}
        Dh[d] = {}
        for h in prod:
            S = table["sites"][h][L]
            ef = {j: quart(h, d, j) for j in S["first"]}
            er = [quart(h, d, f) for f in S["far"]]
            if any(x is None for x in er):
                continue
            ok = [j for j in S["first"] if ef[j] is not None]
            if len(ok) < need[L]:
                continue
            ref = (er[0] + er[1]) / 2.0
            vals = np.array([ef[j] - ref for j in ok])
            Y[h] = float(vals.mean())
            Dh[d][h] = er[0] - er[1]
            for j, v in zip(ok, vals):
                per.setdefault(j, []).append(float(v))
            out[f"{d}.Y.{h}"] = Y[h]
        Yall[d], sites_all[d] = Y, per
    # deltas
    dels, dfar = {}, None
    for d in ("Sr", "Ca", "Cl", "Cs", "GA"):
        L = sub[d]
        dels[d] = []
        for p in ("m30", "m05"):
            j = int(table["a2_sites"][p][L])
            A = table["a2"][p]
            labs = ["s2r_%s_host%s%d" % (p, L, j), "s2r_%s_V%s%d" % (p, L, j), "s2r_%s_%s%do0_novac" % (p, d, j),
                    "s2r_%s_%s%do0_vac" % (p, d, j)]
            cs = [A.get(x) for x in labs]
            if any(c is None or c["status"] != "complete" or c["end_rule"] not in ("accepted_converged", "accepted_plateau")
                   or c["valid_final"] is not True for c in cs):             # §11 rule (I-10 revised)
                continue
            e0 = ((cs[3]["F0_eV"] - cs[2]["F0_eV"]) - (cs[1]["F0_eV"] - cs[0]["F0_eV"])) * 1000.0
            e2 = ((cs[3]["Ffin_eV"] - cs[2]["Ffin_eV"]) - (cs[1]["Ffin_eV"] - cs[0]["Ffin_eV"])) * 1000.0
            dels[d].append(e2 - e0)
            out[f"{d}.delta.{p}"] = e2 - e0
    A = table["a2"]["m30"]
    labs = ["s2r_m30_hostB76", "s2r_m30_VB76", "s2r_m30_Sr76o0_novac", "s2r_m30_Sr76o0_vac"]
    cs = [A.get(x) for x in labs]
    if all(c and c["status"] == "complete" and c["end_rule"] in ("accepted_converged", "accepted_plateau")
           and c["valid_final"] is True for c in cs):
        dfar = ((cs[3]["Ffin_eV"] - cs[2]["Ffin_eV"]) - (cs[1]["Ffin_eV"] - cs[0]["Ffin_eV"])) * 1000.0 - \
            ((cs[3]["F0_eV"] - cs[2]["F0_eV"]) - (cs[1]["F0_eV"] - cs[0]["F0_eV"])) * 1000.0
        out["delta_far"] = dfar
    groups = [np.array(v) for v in dels.values() if len(v) >= 1]
    df_d = int(sum(len(g) - 1 for g in groups))
    s2d = float(sum(((g - g.mean()) ** 2).sum() for g in groups) / df_d) if df_d > 0 else None
    out["df_delta"] = df_d
    if s2d is not None:
        out["s_delta"] = math.sqrt(s2d)
    afar = 0.0
    if dfar is not None and s2d is not None:
        thr = _ind_tq(0.975, df_d) * math.sqrt(s2d)
        afar = abs(dfar) if abs(dfar) > thr else 0.0
    elif dfar is not None:
        afar = abs(dfar)
    out["a_far"] = afar
    for d in ("Sr", "Ca", "Cl", "Cs", "GA"):
        y = np.array(list(Yall[d].values()))
        n = len(y)
        g = table["gates"]["pose"].get(d) if d in ("Cs", "Cl") else None
        ap = g["a_pose_meV"] if g and g["mode"] == "default" else 0.0
        if n >= 2:
            sy = float(y.std(ddof=1))
            t1 = _ind_tq(qs, n - 1)
            out[f"{d}.Ybar"], out[f"{d}.sY"] = float(y.mean()), sy
            out[f"{d}.A1.lo"] = float(y.mean()) - (t1 * sy / math.sqrt(n) + ap)
            out[f"{d}.A1.hi"] = float(y.mean()) + (t1 * sy / math.sqrt(n) + ap)
            out[f"{d}.A1.U"] = abs(float(y.mean())) + t1 * sy / math.sqrt(n) + ap
        per = sites_all[d]
        Eb = np.array([np.mean(v) for _, v in sorted(per.items())]) if per else np.array([])
        for j, v in sorted(per.items()):
            out[f"{d}.Ebar.{j}"] = float(np.mean(v))
        if len(Eb):
            G = -kt * math.log(float(np.mean(np.exp(-Eb / kt))))
            out[f"{d}.G.A1"] = G
            out[f"{d}.flag"] = abs(G - float(Eb.mean())) > kt
        m = len(dels[d])
        if n >= 2 and m >= 1 and df_d >= 1:
            db = float(np.mean(dels[d]))
            a, b = float(y.var(ddof=1)) / n, s2d / m
            nu = (a + b) ** 2 / (a ** 2 / (n - 1) + b ** 2 / df_d)
            ts = _ind_tq(qs, nu)
            th = float(y.mean()) + db
            half = ts * math.sqrt(a + b) + afar + ap
            out.update({f"{d}.delta_bar": db, f"{d}.theta": th, f"{d}.SE": math.sqrt(a + b), f"{d}.nu": nu,
                        f"{d}.tstar": ts, f"{d}.cal.lo": th - half, f"{d}.cal.hi": th + half,
                        f"{d}.cal.U": abs(th) + half})
            if len(Eb):
                out[f"{d}.G.cal"] = -kt * math.log(float(np.mean(np.exp(-(Eb + db) / kt))))

            def cls(lo, hi, vals, G):
                k = int(math.ceil(0.75 * len(vals) - 1e-12))
                if lo > kt and (vals > 0).sum() >= k:
                    return "repels"
                if hi < -kt and (vals < 0).sum() >= k:
                    return "binds"
                if -kt < lo and hi < kt and G > -kt:
                    return "no first-shell interaction beyond k_BT"
                return "not resolved"
            out[f"{d}.cal.class"] = cls(th - half, th + half, y + db, out[f"{d}.G.cal"])
        if n >= 2:
            k = int(math.ceil(0.75 * n - 1e-12))
            lo, hi = out[f"{d}.A1.lo"], out[f"{d}.A1.hi"]
            G = out[f"{d}.G.A1"]
            out[f"{d}.A1.class"] = ("repels" if lo > kt and (y > 0).sum() >= k else "binds" if hi < -kt and
                                    (y < 0).sum() >= k else "no first-shell interaction beyond k_BT" if
                                    -kt < lo and hi < kt and G > -kt else "not resolved")
    # controls C1-C5, the per-site t intervals and the validated class, coded separately (round-3 R3C-2)
    toks5 = ("Sr", "Ca", "Cl", "Cs", "GA")
    gts = table.get("gates") or {}

    def hit(checks, which):
        return any(int(c) in which for c in (checks or []) if str(c).isdigit())

    def specific(d):
        L = sub[d]
        cells = bad = 0
        at = {}
        for h in prod:
            H = table["hosts"][h]
            po = (H.get("pose") or {}).get(d) or {}
            multi = d in ("Cs", "Cl") and (po.get("mode") or "multi") == "multi"
            for j in table["sites"][h][L]["first"]:
                if H.get("host_valid") is not True or H["cell_valid"].get("s2_%s_V%s%d" % (h, L, j)) is not True:
                    continue
                pr = (H.get("pair_rejected") or {}).get("%s%d" % (d, j))
                rej = 1 if (pr is True or (bool(pr) and "p0" in pr)) else 0
                for leg in ("novac", "vac"):
                    if multi:
                        sf = ((po.get("start_failed") or {}).get(str(j)) or {}).get(leg) or {}
                        c, b = len(sf) + rej, sum(1 for v in sf.values() if hit(v, {2, 3, 5})) + rej
                    else:
                        c, b = 1, int(bool(rej or hit(H["failed_checks"].get("s2_%s_%s%do0_%s" % (h, d, j, leg)), {2, 3, 5})))
                    cells, bad = cells + c, bad + b
                    if b:
                        at.setdefault(j, set()).add(h)
        c2_, b2_ = cells, bad
        for p in ("m30", "m05"):
            A_ = table["a2"].get(p) or {}
            j = int(table["a2_sites"][p][L])
            hr, vr = A_.get("s2r_%s_host%s%d" % (p, L, j)), A_.get("s2r_%s_V%s%d" % (p, L, j))
            if not (hr and vr and hr.get("valid_final") is True and vr.get("valid_final") is True):
                continue
            for leg in ("novac", "vac"):
                c = A_.get("s2r_%s_%s%do0_%s" % (p, d, j, leg))
                if c is None or c.get("valid_final") is None:
                    continue
                c2_ += 1
                b2_ += int(c["valid_final"] is False and hit(c.get("failed_checks"), {2, 3, 4, 5}))
        return any(4 * len(s) > len(prod) for s in at.values()) or (cells and bad / cells > 0.10) or \
            (c2_ and b2_ / c2_ > 0.10)
    ctl = {}
    for d in toks5:
        gn = (((gts.get("N") or {}).get(d)) or {}).get("pass") is True
        D = [Dh[d][h] for h in Yall[d]]
        for h in Yall[d]:
            out[f"{d}.Dh.{h}"] = Dh[d][h]
        c2 = False
        if len(D) >= 2:
            sd2, mn = float(np.std(D, ddof=1)) / math.sqrt(2.0), float(np.mean(D))
            out[f"{d}.C2.sd2"], out[f"{d}.C2.mean"] = sd2, mn
            c2 = gn and sd2 < 25.0 and abs(mn) < 15.0
        g1v = (gts.get("G1") or {}).get(d)
        g1v = g1v.get("pass") if isinstance(g1v, dict) else g1v
        c3 = (g1v is True) if d in ("Cl", "Ca") else True
        nd = len(Yall[d])
        c4 = nd >= int(table["n"]) - 1
        m_ = len(dels[d])
        db = float(np.mean(dels[d])) if m_ else None
        c5 = m_ >= 1 and df_d >= 3 and db is not None and abs(db) <= 50.0 and dfar is not None
        noc = (not gn) or (not c3) or bool(specific(d)) or bool((gts.get("multi_pose_cut") or {}).get(d))
        ctl[d] = (c2, c3, c4, c5, noc)
        out.update({f"{d}.C2": c2, f"{d}.C3": c3, f"{d}.C4": c4, f"{d}.nd": nd, f"{d}.C5": c5})
        for j, v in sorted(sites_all[d].items()):
            if len(v) >= 2:
                hw = _ind_tq(0.975, len(v) - 1) * float(np.std(v, ddof=1)) / math.sqrt(len(v))
                out[f"{d}.site.{j}.lo"], out[f"{d}.site.{j}.hi"] = float(np.mean(v)) - hw, float(np.mean(v)) + hw
                if f"{d}.cal.class" in out:
                    out[f"{d}.sitec.{j}.lo"], out[f"{d}.sitec.{j}.hi"] = float(np.mean(v)) + db - hw, float(np.mean(v)) + db + hw
    fl = {d: bool(out.get(f"{d}.flag")) for d in toks5}
    s2, s3, s4, s5, snoc = ctl["Sr"]
    C1 = out.get("Sr.cal.class") == "repels" and not fl["Sr"] and not snoc and s2 and s4 and s5
    sr_a1 = out.get("Sr.A1.class") == "repels" and not fl["Sr"] and not snoc and s2 and s3 and s4
    out["C1"] = bool(C1)
    for d in toks5:
        c2, c3, c4, c5, noc = ctl[d]
        cv = out.get(f"{d}.cal.class")
        good = cv in ("repels", "binds", "no first-shell interaction beyond k_BT") and C1 and c2 and c3 and c4 and c5 \
            and not noc and not fl[d]
        out[f"{d}.class_validated"] = cv if good else "none"
        a1c = out.get(f"{d}.A1.class")
        out[f"{d}.A1.shown"] = a1c if (a1c is not None and not noc and not fl[d] and sr_a1 and c2 and c3 and c4) \
            else "no class"
    # ranking
    toks = ["Sr", "Ca", "Cl", "Cs", "GA"]
    for i in range(5):
        for k in range(i + 1, 5):
            d1, d2 = toks[i], toks[k]
            hs = [h for h in prod if h in Yall[d1] and h in Yall[d2]]
            D = np.array([Yall[d1][h] - Yall[d2][h] for h in hs])
            if len(D) >= 2:
                hw = _ind_tq(0.9975, len(D) - 1) * float(D.std(ddof=1)) / math.sqrt(len(D))
                out[f"rank.{d1}-{d2}.lo"], out[f"rank.{d1}-{d2}.hi"] = float(D.mean()) - hw, float(D.mean()) + hw
                m1, m2 = len(dels[d1]), len(dels[d2])
                if m1 >= 1 and m2 >= 1 and df_d >= 1 and len(Yall[d1]) >= 2 and len(Yall[d2]) >= 2:
                    a, b = float(D.var(ddof=1)) / len(D), s2d * (1 / m1 + 1 / m2)
                    nu = (a + b) ** 2 / (a ** 2 / (len(D) - 1) + b ** 2 / df_d)
                    th = float(D.mean()) + float(np.mean(dels[d1])) - float(np.mean(dels[d2]))
                    hw = _ind_tq(0.9975, nu) * math.sqrt(a + b)
                    out[f"rankc.{d1}-{d2}.lo"], out[f"rankc.{d1}-{d2}.hi"] = th - hw, th + hw
    return out


def flatten_eval(res):
    """The same keys as independent() from an evaluate() result."""
    out = {}
    for d, r in res["per_dopant"].items():
        for h, rec in r["hosts"].items():
            if rec["valid"]:
                out[f"{d}.Y.{h}"] = rec["Y_h_meV"]
                out[f"{d}.Dh.{h}"] = rec["Delta_h_meV"]
        ct = r["controls"]
        if ct["C2"]["sd_over_sqrt2_meV"] is not None:
            out[f"{d}.C2.sd2"], out[f"{d}.C2.mean"] = ct["C2"]["sd_over_sqrt2_meV"], ct["C2"]["mean_meV"]
        out.update({f"{d}.C2": ct["C2"]["pass"], f"{d}.C3": ct["C3"], f"{d}.C4": ct["C4"]["pass"],
                    f"{d}.nd": ct["C4"]["n_d"], f"{d}.C5": ct["C5"]["pass"]})
        for tag, hh in (("site", r["heterogeneity"]["A1"]), ("sitec", r["heterogeneity"]["calibrated"])):
            for j, iv in ((hh or {}).get("intervals") or {}).items():
                if iv:
                    out[f"{d}.{tag}.{j}.lo"], out[f"{d}.{tag}.{j}.hi"] = iv
        out[f"{d}.class_validated"] = r["calibrated"]["class_validated"] or "none"
        out[f"{d}.A1.shown"] = "no class" if str(r["a1"]["class"]).startswith("no class") else r["a1"]["class"]
        for p, v in r["calibrated"]["deltas"].items():
            if v["valid"]:
                out[f"{d}.delta.{p}"] = v["delta_meV"]
        a1 = r["a1"]
        if a1["available"]:
            out.update({f"{d}.Ybar": a1["Ybar_meV"], f"{d}.sY": a1["s_Y_meV"], f"{d}.A1.lo": a1["interval_meV"][0],
                        f"{d}.A1.hi": a1["interval_meV"][1], f"{d}.A1.U": a1["U_meV"], f"{d}.A1.class": a1["class_rule_v"]})
        het = r["heterogeneity"]["A1"]
        for j, v in het["Ebar_meV"].items():
            out[f"{d}.Ebar.{j}"] = v
        if het["G_meV"] is not None:
            out[f"{d}.G.A1"], out[f"{d}.flag"] = het["G_meV"], het["flag"]
        c = r["calibrated"]
        if c.get("available"):
            out.update({f"{d}.delta_bar": c["delta_bar_meV"], f"{d}.theta": c["theta_meV"], f"{d}.SE": c["SE_meV"],
                        f"{d}.nu": c["nu"], f"{d}.tstar": c["t_star"], f"{d}.cal.lo": c["interval_meV"][0],
                        f"{d}.cal.hi": c["interval_meV"][1], f"{d}.cal.U": c["U_meV"], f"{d}.cal.class": c["class_rule_v"],
                        f"{d}.G.cal": c["G_meV"]})
    out["C1"] = res["per_dopant"]["Sr"]["controls"]["C1"]
    out["df_delta"] = res["delta_pool"]["df_delta"]
    if res["delta_pool"]["s_delta_meV"] is not None:
        out["s_delta"] = res["delta_pool"]["s_delta_meV"]
    out["a_far"] = res["separability"]["a_far_meV"]
    if res["delta_far"]["valid"]:
        out["delta_far"] = res["delta_far"]["delta_meV"]
    for key, r in res["ranking"]["A1"].items():
        if r["interval_meV"]:
            out[f"rank.{key}.lo"], out[f"rank.{key}.hi"] = r["interval_meV"]
    for key, r in res["ranking"]["calibrated"].items():
        if r.get("interval_meV"):
            out[f"rankc.{key}.lo"], out[f"rankc.{key}.hi"] = r["interval_meV"]
    return out


def compare(a, b, tol=1e-6):
    """Keys equal; numbers within tol (meV); booleans and strings equal."""
    ka, kb = set(a), set(b)
    assert ka == kb, f"keys differ: only 48 {sorted(ka - kb)[:8]}, only independent {sorted(kb - ka)[:8]}"
    worst = 0.0
    for k in ka:
        x, y = a[k], b[k]
        if isinstance(x, (bool, str)) or isinstance(y, (bool, str)):
            assert x == y, (k, x, y)
        else:
            worst = max(worst, abs(x - y))
            assert abs(x - y) <= tol, (k, x, y)
    return worst


# ---- the §17 item 2 cases, each a function of the module under test (so that a rerun can run one on the first code)
def _cls(m, t, d, tier="calibrated"):
    r = m.evaluate(t)["per_dopant"][d]
    return r["calibrated"]["class_validated"] if tier == "calibrated" else r["a1"]["class"]


def case_independent(m):
    t = synth_table(multi_cs=True, fail=[("m22", "s2_m22_Cl90o0_novac", [3])],
                    missing_sp=[("m23", "s2_m23_GA28o0_vac")], invalid=[("m26", "s2_m26_Ca172o0_novac")],
                    plateau=[("m05", "s2r_m05_Cl49o0_vac")])
    res = m.evaluate(t)
    worst = compare(flatten_eval(res), independent(t))
    assert res["per_dopant"]["Ca"]["a1"]["n_d"] == 7 and res["per_dopant"]["GA"]["a1"]["n_d"] == 8
    assert res["per_dopant"]["Cl"]["hosts"]["m22"]["n_valid_first"] == 7
    assert abs(t["hosts"]["m06"]["F"]["s2_m06_host"] + 8e4) < 5
    t2 = synth_table(seed=7, prod=PROD8 + ["m33", "m13"], dfar=40.0, noise=9.0,
                     delta={d: {"m30": 11.0, "m05": -3.0} for d in TOKENS}, invalid=[("m13", "s2_m13_Sr76o0_vac")])
    res2 = m.evaluate(t2)
    worst2 = compare(flatten_eval(res2), independent(t2))
    assert res2["separability"]["fired"] and res2["separability"]["a_far_meV"] == abs(res2["delta_far"]["delta_meV"])
    assert res2["per_dopant"]["Sr"]["a1"]["n_d"] == 9 and res2["n"] == 10
    # round 3 (R3C-2): the controls C1-C5, Delta_h and its C2 statistics, the per-site intervals and the validated and
    # shown classes are compared too, on tables where they differ (classes, a dopant-specific trip, a C2 failure)
    more = [_planted(eb={"Sr": 120.0, "Ca": -75.0, "Cl": 0.0, "Cs": 0.0, "GA": 60.0}),
            synth_table(seed=5, fail=[(h, f"s2_{h}_Sr124o0_vac", [3]) for h in PROD8[:3]]),
            _planted(eb={"Sr": 120.0, "Ca": -75.0, "Cl": 0.0, "Cs": 0.0, "GA": 60.0}, far={**{d: 0.0 for d in TOKENS},
                                                                                         "Ca": 0.0}, host_sd=0.5)]
    for h in PROD8:                                                         # Ca: |mean Delta_h| 16 meV fails C2
        _shift_far_diff(more[2], "Ca", h, 16.0)
    nk, worst3 = 0, 0.0
    for t3 in more:
        a, b = flatten_eval(m.evaluate(t3)), independent(t3)
        worst3 = max(worst3, compare(a, b)); nk += len(a)
    v = [m.evaluate(t3)["per_dopant"]["Ca"]["calibrated"]["class_validated"] for t3 in more]
    assert v[0] == "binds" and v[2] is None and m.evaluate(more[1])["per_dopant"]["Sr"]["dopant_specific"]["applies"], v
    keys = set(flatten_eval(res))
    assert {"C1", "Ca.C2.sd2", "Ca.C2.mean", "Ca.C4", "Ca.C5", "Ca.class_validated", "Ca.A1.shown"} <= keys and \
        any(k.startswith("Ca.site.") for k in keys) and any(k.startswith("Ca.Dh.") for k in keys)
    return (f"{len(flatten_eval(res))} + {len(flatten_eval(res2))} + {nk} statistics and decisions agree, worst |diff| "
            f"{max(worst, worst2, worst3):.2e} meV (F about -8e4 eV; Cs multi-pose; n = 10 with a_far fired; C1-C5, "
            f"Delta_h, the C2 statistics, per-site intervals, validated and shown classes)")


def _shift_far_diff(t, d, h, target):
    """Shift F of the D+V cell at f1 so that Delta_h = E_b(f1) - E_b(f2) equals target (meV)."""
    hv = host_values(t, d)[h]
    f1, f2 = [int(x) for x in t["sites"][h][SUBLATTICE[d]]["far"]]
    cur = hv["far"][f1]["Eb_meV"] - hv["far"][f2]["Eb_meV"]
    t["hosts"][h]["F"][g49.lab_dop(h, d, f1, "vac", 0)] += (target - cur) / 1000.0


def _shift_Y(t, d, h, target):
    """Shift F of every first-shell D+V cell of (h, d) equally so that Y_h equals target (meV)."""
    hv = host_values(t, d)[h]
    for j in t["sites"][h][SUBLATTICE[d]]["first"]:
        t["hosts"][h]["F"][g49.lab_dop(h, d, int(j), "vac", 0)] += (target - hv["Y_h_meV"]) / 1000.0


def case_boundaries(m):
    """Round-3 R3C-10 (the coverage reviewer's tests A-F, committed): C2 at its bounds (and exactly at 25 and 15 meV,
    strict), C4 at n_d = n - 1, the valid-host thresholds, the sign rule where it binds (n = 10), C1 through Sr's C2,
    C4 and C5, and the required hosts against an independent loop; every table is also compared with the independent
    implementation."""
    from scipy.stats import t as st_t
    n_chk = 0
    base = lambda **kw: _planted(eb={"Sr": 120.0, "Ca": -75.0, "Cl": 0.0, "Cs": 0.0, "GA": 60.0}, **kw)  # noqa: E731
    lim = 25.0 * math.sqrt(7.0 / 4.0)                    # alternating +-a over 8 hosts: SD/sqrt(2) = a sqrt(4/7)
    for scale, want in ((1 - 1e-6, True), (1 + 1e-6, False)):
        t = base()
        for i, h in enumerate(PROD8):
            _shift_far_diff(t, "Ca", h, lim * scale * (1 if i % 2 else -1))
        r = m.evaluate(t); c2 = r["per_dopant"]["Ca"]["controls"]["C2"]
        assert c2["pass"] is want and (r["per_dopant"]["Ca"]["calibrated"]["class_validated"] is None) == (not want), c2
        compare(flatten_eval(r), independent(t)); n_chk += 1
    for mean, want in ((14.999, True), (15.001, False), (-15.001, False)):
        t = base()
        for i, h in enumerate(PROD8):
            _shift_far_diff(t, "Ca", h, mean + (0.5 if i % 2 else -0.5))
        r = m.evaluate(t)
        assert r["per_dopant"]["Ca"]["controls"]["C2"]["pass"] is want, (mean, r["per_dopant"]["Ca"]["controls"]["C2"])
        compare(flatten_eval(r), independent(t)); n_chk += 1
    gN = {"gates": {"N": {"Ca": {"pass": True}}}}
    for D, want in (([-25.0, 25.0], False), ([-25.0, 24.9999], True), ([15.0, 15.0], False),
                    ([14.9999] * 2, True)):                          # exactly 25 and 15 fail: the bounds are strict
        hv = {f"h{i}": {"valid": True, "Delta_h_meV": x} for i, x in enumerate(D)}
        assert m.c2_noise(gN, "Ca", hv)["pass"] is want, (D, m.c2_noise(gN, "Ca", hv)); n_chk += 1
    for k_bad, want in ((1, True), (2, False)):
        t = base(invalid=[(h, f"s2_{h}_Ca76o0_vac") for h in PROD8[:k_bad]])
        r = m.evaluate(t); c4 = r["per_dopant"]["Ca"]["controls"]["C4"]
        assert c4["pass"] is want and (r["per_dopant"]["Ca"]["calibrated"]["class_validated"] is None) == (not want)
        compare(flatten_eval(r), independent(t)); n_chk += 1
    X, A = SITES["X"]["first"], SITES["A"]["first"]
    for d, labs, want, nfirst in (("Cl", [f"s2_m06_Cl{j}o0_novac" for j in X[:2]], True, 6),
                                  ("Cl", [f"s2_m06_Cl{j}o0_novac" for j in X[:3]], False, 5),
                                  ("Cs", [f"s2_m06_Cs{A[0]}o0_vac"], True, 2),
                                  ("Cs", [f"s2_m06_Cs{j}o0_vac" for j in A[:2]], False, 1),
                                  ("Sr", ["s2_m06_Sr124o0_vac"], False, 1), ("Sr", ["s2_m06_Sr172o0_novac"], False, 2)):
        t = base(invalid=[("m06", x) for x in labs])
        r = m.evaluate(t); hv = r["per_dopant"][d]["hosts"]["m06"]
        assert hv["valid"] is want and hv["n_valid_first"] == nfirst, (d, labs, hv["valid"], hv["n_valid_first"])
        n_chk += 1
    P10 = PROD8 + ["m33", "m13"]
    for npos, want in ((7, "not resolved"), (8, "repels")):
        t = base(prod=P10)
        for i, h in enumerate(P10):
            _shift_Y(t, "Ca", h, (300.0 + 3.0 * i) if i < npos else (-1.0 - 0.5 * i))
        r = m.evaluate(t); a1, cal = r["per_dopant"]["Ca"]["a1"], r["per_dopant"]["Ca"]["calibrated"]
        assert a1["interval_meV"][0] > KT and a1["class_rule_v"] == want and cal["interval_meV"][0] > KT and \
            cal["class_rule_v"] == want, (npos, a1["class_rule_v"], cal["class_rule_v"])
        compare(flatten_eval(r), independent(t)); n_chk += 2
    r0 = m.evaluate(base())
    assert r0["per_dopant"]["Sr"]["controls"]["C1"] is True and r0["per_dopant"]["Ca"]["calibrated"]["class_validated"] == "binds"
    tC2 = base()
    for i, h in enumerate(PROD8):
        _shift_far_diff(tC2, "Sr", h, 16.0 + (0.5 if i % 2 else -0.5))
    tC4 = base(invalid=[(h, f"s2_{h}_Sr76o0_vac") for h in PROD8[:2]])
    tC5 = base(delta={**{d: {"m30": 2.0, "m05": -1.0} for d in TOKENS}, "Sr": {"m30": 60.0, "m05": 55.0}})
    for tag, t in (("C2", tC2), ("C4", tC4), ("C5", tC5)):
        r = m.evaluate(t); sr = r["per_dopant"]["Sr"]
        assert sr["controls"][tag]["pass"] is False and sr["controls"]["C1"] is False and \
            r["per_dopant"]["Ca"]["calibrated"]["class_validated"] is None, tag
        compare(flatten_eval(r), independent(t)); n_chk += 1
    q = 1 - 0.05 / 8
    for sY in (8.0, 13.0, 20.0, 30.0):
        want = {k: next(n for n in range(2, 1001) if st_t.ppf(q, n - 1) * sY / math.sqrt(n) < lim_)
                for k, lim_ in (("k_BT", 25.7), ("k_BT/2", 12.85))}
        assert m.required_hosts(sY) == want, (sY, m.required_hosts(sY), want); n_chk += 1
    return (f"{n_chk} checks: C2 SD/sqrt(2) 24.999975 pass / 25.000025 fail and exactly 25 fails, |mean| 14.999 / "
            f"15.001 / -15.001 and exactly 15 fails; C4 7 of 8 / 6 of 8; valid hosts B 2/2, A 2/3, X 6/8; sign rule at "
            f"n = 10 (7/10 not resolved, 8/10 repels, both tiers); Sr C2, C4, C5 -> C1 false; required hosts at s_Y "
            f"8/13/20/30 meV; independent implementation equal on every table")


def case_counts_ledger(m):
    """Round-3 R3C-3, R3C-4 (N-F26, N-F27): N_D, N_D+V and the count term beside every aggregated E_b of a multi-pose
    leg (3 and 2 kept minima: 25.7 ln(3/2) = 10.4205 meV), and the pilot section of the zero-shot MACE ledger (the
    calibration start-set quartets beside the A1 DFT E_b from k = 0 of A2, and the pose pilot)."""
    t = synth_table(multi_cs=True)
    H = t["hosts"]["m06"]
    for leg, ks in (("novac", 3), ("vac", 2)):
        o0 = g49.lab_dop("m06", "Cs", 28, leg, 0)
        for k in range(ks):
            lab = g49.lab_dop("m06", "Cs", 28, leg, k)
            H["F"].setdefault(lab, H["F"][o0] + 0.005 * k)
            H["cell_valid"][lab], H["failed_checks"][lab] = True, []
        H["pose"]["Cs"]["minima"]["28"][leg] = [f"o{k}" for k in range(ks)]
    rep = m.evaluate(t)["reported"]
    row = rep["per_site"]["Cs"]["m06"]["first"]["28"]
    assert row["N_D"] == 3 and row["N_DV"] == 2 and abs(row["count_term_meV"] - 25.7 * math.log(1.5)) < 1e-6, row
    assert "count_term_meV" not in rep["per_site"]["Sr"]["m06"]["first"]["124"]            # one start: no aggregate
    t2 = synth_table()
    P = {"host_valid": True, "F": {}, "cell_valid": {}, "failed_checks": {}, "pair_rejected": {}, "pose": {},
         "E_mace": {"s2_m30_host": -1200.0, "s2_m30_VB136": -1197.0, "s2_m30_Sr136o0_novac": -1190.0,
                    "s2_m30_Sr136o0_vac": -1186.9, "s2_m30_Cs128o0_novac": -1191.0, "s2_m30_Cs128o0_vac": -1188.0,
                    "s2_m30_Cs128o1_novac": -1191.01, "s2_m30_VA128": -1197.0},
         "pose_pilot": {"Cs": {"128": {"novac": ["o0", "o1"], "vac": ["o0"]}}}}
    t2["hosts"]["m30"] = P
    led = m.evaluate(t2)["reported"]["mace_ledger"]["pilot"]
    c = led["calibration"]["m30"]["Sr136"]
    assert abs(c["Eb_mace_meV"] - ((-1186.9 + 1190.0) - (-1197.0 + 1200.0)) * 1000.0) < 1e-6 and \
        c["Eb_A1_dft_meV"] is not None and led["label"] == LABEL_MACE, c
    pp = led["pose_pilot"]["Cs128"]
    assert pp["N_D"] == 2 and pp["N_DV"] == 1 and pp["Eb_mace_default_meV"] is not None and \
        pp["Eb_mace_aggregate_meV"] is not None, pp
    return (f"Cs FA28 on m06 with 3 and 2 kept minima: count term {row['count_term_meV']:.4f} meV beside the aggregated "
            f"E_b; MACE ledger pilot section: m30 Sr136 {c['Eb_mace_meV']:.1f} meV beside A1 DFT "
            f"{c['Eb_A1_dft_meV']:.1f} meV, pose pilot Cs128 (N_D 2, N_DV 1)")


def case_reported_rows(m):
    """Round-3 R3C-10: the reported-only rows no case computed before: the section 15 path-work attribution (an
    analytic path), the section 5 determinism row (a WP1-style shell file), the q = 0 link rows and the WP2c values."""
    import numpy as np
    X = {k: [[0.1 * k, 0.0, 0.0], [5.0, 0.0, 0.0], [0.0, 9.0, 0.0]] for k in range(3)}
    Fo = {k: [[1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]] for k in range(3)}
    rel = {"positions_A": X, "forces_eVA": Fo, "F_eV": {0: 0.0, 2: -0.2}}
    pw = path_work(rel, centres=[[0.0, 0.0, 0.0]])
    assert abs(pw["total_meV"] + 200.0) < 1e-9 and abs(pw["closure_meV"]) < 1e-9 and \
        abs(pw["shells_meV"]["0-4"] + 200.0) < 1e-9 and pw["shells_meV"]["4-6"] == 0.0 and \
        abs(pw["sum_dr2_A2"] - 0.04) < 1e-12, pw
    d = tempfile.mkdtemp(prefix="s2_48_wp1_")
    json.dump({"E_host": {"E_eV": -1200.5}}, open(os.path.join(d, "shell_m30.json"), "w"))
    det = _determinism({"m30": {"E_mace": {"s2_m30_host": -1200.0}}, "m05": {"E_mace": {}}}, lambda c: d, wp1_dir=d)
    assert abs(det["m30"]["dE_meV"] - 500.0) < 1e-9 and det["m30"]["max_dr_A"] is None and det["m05"]["dE_meV"] is None
    t = synth_table()
    H = {"host_valid": True, "cell_valid": {}, "failed_checks": {}, "pair_rejected": {}, "pose": {}, "E_mace": {},
         "F": {"s2_m30_host": -80000.0, "s2_m30_VB136_q0": -79996.0, "s2_m30_Sr136o0_vac_q0": -79998.2,
               "s2_m30_Sr136o0_novac": -80002.25}}
    t["hosts"]["m30"] = H
    q0 = m.evaluate(t)["reported"]["q0_rows"]["Sr136"]
    want = ((-79998.2 - -80002.25) - (-79996.0 - -80000.0)) * 1000.0
    assert abs(q0["Eb_q0_meV"] - want) < 1e-6 and q0["D_source"] == "SP", q0
    wp = _wp2c_values()
    assert wp and set(wp) == {"m30_Sr136", "m30_GA128", "m05_Sr124"} and all(v and "Eb_dft_meV" in v for v in wp.values())
    del np
    return (f"path work -200 meV on an analytic path (closure 0, all in the 0-4 A shell); determinism dE 500 meV from a "
            f"WP1-style shell file; q = 0 row E_b {q0['Eb_q0_meV']:.1f} meV from its single points; WP2c values for "
            f"{sorted(wp)}")


def case_eval_guard(m):
    """Round-3 R3C-6 (N-F29): in a temporary git repository, scripts/46-49 unchanged since the campaign commit pass;
    a change without --amendment is refused; with a committed dated note it is accepted and recorded."""
    d = tempfile.mkdtemp(prefix="s2_48_guard_")
    g = lambda *a: subprocess.run(["git", "-C", d, "-c", "user.name=s2-selftest", "-c", "user.email=s2-selftest",   # noqa: E731
                                   "-c", "commit.gpgsign=false", *a], capture_output=True, text=True, check=True)
    g("init", "-q")
    for fn in ANALYSIS_FILES:
        os.makedirs(os.path.join(d, os.path.dirname(fn)), exist_ok=True)
        open(os.path.join(d, fn), "w").write(f"# {fn}\n")
    g("add", "-A"); g("commit", "-qm", "campaign")
    c0 = g("rev-parse", "HEAD").stdout.strip()
    ok, rec = m.analysis_guard(c0, c0, root=d)
    assert ok and rec["diff_stat"] == "", rec
    open(os.path.join(d, "scripts/48_s2_analysis.py"), "a").write("# changed after the campaign\n")
    g("add", "-A"); g("commit", "-qm", "analysis change")
    c1 = g("rev-parse", "HEAD").stdout.strip()
    ok, rec = m.analysis_guard(c0, c1, root=d)
    assert not ok and "--amendment" in rec["reason"] and "48_s2_analysis.py" in rec["diff_stat"], rec
    note = os.path.join(d, "amendment.md")
    open(note, "w").write("Dated amendment 2026-11-20: the D3 row is not reported.\n")
    ok, rec = m.analysis_guard(c0, c1, note, root=d)
    assert not ok and "not committed" in rec["reason"], rec
    g("add", "-A"); g("commit", "-qm", "amendment")
    c2 = g("rev-parse", "HEAD").stdout.strip()
    ok, rec = m.analysis_guard(c0, c2, note, root=d)
    assert ok and rec["amendment"]["path"] == "amendment.md" and rec["campaign_commit"] == c0 and rec["head"] == c2, rec
    # round 4 (R4-C24-5): the note must be outside scripts/, added or changed after the campaign commit, with a date on
    # or after that commit's; a given note is recorded also when the code is unchanged; the diff's sha256 and text
    assert rec["diff_sha256"] and "changed after the campaign" in rec["diff_text"], rec
    sub = tempfile.mkdtemp(prefix="s2_48_guard2_")
    g2 = lambda *a: subprocess.run(["git", "-C", sub, "-c", "user.name=s2-selftest", "-c", "user.email=s2-selftest",  # noqa: E731
                                    "-c", "commit.gpgsign=false", *a], capture_output=True, text=True, check=True)
    g2("init", "-q")
    for fn in ANALYSIS_FILES:
        os.makedirs(os.path.join(sub, os.path.dirname(fn)), exist_ok=True)
        open(os.path.join(sub, fn), "w").write(f"# {fn}\n")
    os.makedirs(os.path.join(sub, "results"), exist_ok=True)
    open(os.path.join(sub, "results", "S2_PLAN.md"), "w").write("plan 2026-11-03\n")
    open(os.path.join(sub, "notes_before.md"), "w").write("an older note 2026-10-01\n")
    g2("add", "-A"); g2("commit", "-qm", "campaign")
    k0 = g2("rev-parse", "HEAD").stdout.strip()
    day0 = g2("show", "-s", "--format=%cs", k0).stdout.strip()
    open(os.path.join(sub, "scripts/48_s2_analysis.py"), "a").write(f"# changed {day0}\n")
    os.makedirs(os.path.join(sub, "amendments"), exist_ok=True)
    open(os.path.join(sub, "amendments", "late.md"), "w").write(f"amendment {day0}: the D3(BJ) row is not reported\n")
    open(os.path.join(sub, "amendments", "early.md"), "w").write("amendment dated 2020-01-01 only\n")
    g2("add", "-A"); g2("commit", "-qm", "change and amendments")
    k1 = g2("rev-parse", "HEAD").stdout.strip()
    refused = {}
    for nm in ("results/S2_PLAN.md", "scripts/48_s2_analysis.py", "notes_before.md", "amendments/early.md"):
        ok_, r_ = m.analysis_guard(k0, k1, os.path.join(sub, nm), root=sub)
        assert not ok_, (nm, r_)
        refused[nm] = r_["reason"][:60]
    ok_, r_ = m.analysis_guard(k0, k1, os.path.join(sub, "amendments", "late.md"), root=sub)
    assert ok_ and r_["amendment"]["path"] == os.path.join("amendments", "late.md") and r_["diff_sha256"], r_
    open(os.path.join(sub, "amendments", "d3bj.md"), "w").write(f"D-S0-4 amendment {day0}: D3(BJ) not reported\n")
    g2("add", "-A"); g2("commit", "-qm", "D3(BJ) amendment only")
    k2 = g2("rev-parse", "HEAD").stdout.strip()
    hist = [{"from": k0, "to": k1, "note": "2026-11-04 fix", "time": "t", "via": "c1/NODE_FIX"},
            {"from": "0" * 40, "to": "1" * 40, "note": "x", "time": "t", "via": "c2/STEP0_FIX"}]
    ok_, r_ = m.analysis_guard(k1, k2, os.path.join(sub, "amendments", "d3bj.md"), root=sub, commit_history=hist)
    assert ok_ and r_["diff_stat"] == "" and r_["amendment"]["path"].endswith("d3bj.md"), r_
    assert [{k: e[k] for k in ("from", "to", "note", "via")} for e in r_["commit_history"]] == \
        [{k: e[k] for k in ("from", "to", "note", "via")} for e in hist], r_["commit_history"]
    assert "48_s2_analysis.py" in r_["commit_history"][0]["diff_stat_46_50"] and \
        r_["commit_history"][1]["diff_stat_46_50"].startswith("unavailable"), r_["commit_history"]
    arch = tempfile.mkdtemp(prefix="s2_48_hist_")
    os.makedirs(os.path.join(arch, "c2"))
    json.dump({"commit": k1, "commit_history": hist}, open(os.path.join(arch, "c2", "state_end.json"), "w"))
    assert m._commit_history(arch) == hist and m._campaign_commit(arch) == k1
    return ("unchanged code passes; a changed scripts/48 is refused without --amendment and with an uncommitted note; "
            "a committed dated note is accepted and recorded with both commits and the diff; round 4: refused "
            f"{sorted(refused)} (outside scripts/, after the campaign commit, dated on or after it), a later dated note "
            "accepted with the diff's sha256; an amendment with unchanged code recorded; commit_history copied from "
            "state_end with the diff stat of each NODE_FIX step")


def _planted(**kw):
    base = dict(noise=2.0, host_sd=2.0, delta={d: {"m30": 2.0, "m05": -1.0} for d in TOKENS})
    base.update(kw)
    return synth_table(**base)


def case_planted(m):
    t = _planted(eb={"Sr": 120.0, "Ca": -75.0, "Cl": 0.0, "Cs": 0.0, "GA": 60.0})
    res = m.evaluate(t)
    got = {d: res["per_dopant"][d]["calibrated"]["class_validated"] for d in TOKENS}
    assert got == {"Sr": "repels", "Ca": "binds", "Cl": "no first-shell interaction beyond k_BT",
                   "Cs": "no first-shell interaction beyond k_BT", "GA": "repels"}, got
    assert res["per_dopant"]["Sr"]["controls"]["C1"] is True
    assert res["per_dopant"]["Ca"]["a1"]["class"] == "binds"
    return f"repelling control, -75 meV binder, null dopants and a +60 meV repeller recovered: {got}"


def case_heterogeneous(m):
    x100 = {j: (-100.0 if j == 138 else 0.0) for j in SITES["X"]["first"]}
    x80 = {j: (-80.0 if j == 138 else 0.0) for j in SITES["X"]["first"]}
    r100 = m.evaluate(_planted(noise=1.0, host_sd=1.0, eb={"Sr": 120.0, "Ca": -75.0, "Cl": x100, "Cs": 0.0, "GA": 60.0}))
    h = r100["per_dopant"]["Cl"]["heterogeneity"]["A1"]
    assert h["flag"] is True and abs(h["G_meV"] + 50.0) < 1.5 and abs(h["mean_meV"] + 12.5) < 1.5, h
    assert r100["per_dopant"]["Cl"]["calibrated"]["class_validated"] is None
    assert r100["per_dopant"]["Cl"]["a1"]["class"] == "no class (heterogeneous shell)"
    r80 = m.evaluate(_planted(noise=1.0, host_sd=1.0, eb={"Sr": 120.0, "Ca": -75.0, "Cl": x80, "Cs": 0.0, "GA": 60.0}))
    h = r80["per_dopant"]["Cl"]["heterogeneity"]["A1"]
    c = r80["per_dopant"]["Cl"]["calibrated"]
    assert h["flag"] is False and abs(h["G_meV"] + 33.5) < 1.5 and abs(h["mean_meV"] + 10.0) < 1.5, h
    assert -KT < c["interval_meV"][0] and c["interval_meV"][1] < KT, c["interval_meV"]   # inside: G decides
    assert c["class_rule_v"] == NOT_RESOLVED and c["class_validated"] is None and c["G_meV"] <= -KT
    return (f"-100 meV X site flagged (G {r100['per_dopant']['Cl']['heterogeneity']['A1']['G_meV']:.1f}, mean "
            f"{r100['per_dopant']['Cl']['heterogeneity']['A1']['mean_meV']:.1f}); -80 meV not flagged (G {h['G_meV']:.1f}, "
            f"mean {h['mean_meV']:.1f}), interval inside +-k_BT but not 'no interaction'")


def case_refusals(m):
    eb = {"Sr": 120.0, "Ca": -75.0, "Cl": 0.0, "Cs": 0.0, "GA": 60.0}
    # control does not repel -> no validated class for any dopant
    r = m.evaluate(_planted(eb={**eb, "Sr": 0.0}))
    assert r["per_dopant"]["Sr"]["controls"]["C1"] is False
    assert all(r["per_dopant"][d]["calibrated"]["class_validated"] is None for d in TOKENS)
    assert all("Sr does not repel" in r["per_dopant"][d]["a1"]["class"] for d in DECISIVE)
    # df_delta < 3 -> none (two dopants with m_d = 2, three with m_d = 0: df = 2)
    bad = [(p, f"s2r_{p}_{d}{CAL[p][SUBLATTICE[d]]}o0_vac", {"valid_final": False, "failed_checks": [5]})
           for p in PILOTS for d in ("Ca", "Cs", "GA")]
    r = m.evaluate(_planted(eb=eb, a2_bad=bad))
    assert r["delta_pool"]["df_delta"] == 2 and all(r["per_dopant"][d]["calibrated"]["class_validated"] is None
                                                    for d in TOKENS)
    assert r["per_dopant"]["Ca"]["a1"]["class"] == "binds"                       # the A1 tier is still reported
    return "C1 fails without a repelling control; df_delta = 2 gives no validated class (A1 tier still reported)"


def case_delta_bound(m):
    eb = {"Sr": 120.0, "Ca": -75.0, "Cl": 0.0, "Cs": 0.0, "GA": 60.0}

    def tab(dCa):
        t = _planted(eb=eb, offset=0.0)
        for p in PILOTS:                      # exact small-magnitude B-region values: delta_Ca = dCa to the last bit
            j = CAL[p]["B"]
            for lab in (f"s2r_{p}_hostB{j}", f"s2r_{p}_VB{j}", f"s2r_{p}_Ca{j}o0_novac", f"s2r_{p}_Ca{j}o0_vac",
                        f"s2r_{p}_Sr{j}o0_novac", f"s2r_{p}_Sr{j}o0_vac"):
                t["a2"][p][lab].update({"F0_eV": 0.0, "Ffin_eV": 0.0})
            t["a2"][p][f"s2r_{p}_Ca{j}o0_vac"]["Ffin_eV"] = dCa / 1000.0
            t["a2"][p][f"s2r_{p}_Sr{j}o0_vac"]["Ffin_eV"] = 0.002
        return t
    t50 = tab(50.0)
    r = m.evaluate(t50)
    c = r["per_dopant"]["Ca"]["calibrated"]
    assert c["delta_bar_meV"] == 50.0 and r["per_dopant"]["Ca"]["controls"]["C5"]["pass"]
    r = m.evaluate(tab(50.001))
    assert r["per_dopant"]["Ca"]["controls"]["C5"]["pass"] is False
    assert r["per_dopant"]["Ca"]["calibrated"]["class_validated"] is None
    return "|delta_bar| = 50.000 meV passes C5, 50.001 meV gives no validated class"


def case_dopant_specific(m):
    eb = {"Sr": 120.0, "Ca": -75.0, "Cl": 0.0, "Cs": 0.0, "GA": 60.0}
    # one first-shell site failing on 3 of 8 hosts (> 8/4) -> no class at either tier; 2 of 8 -> no trip at that rule
    f3 = [(h, f"s2_{h}_Sr136o0_vac", [3]) for h in PROD8[:3]]
    r = m.evaluate(_planted(eb=eb, fail=f3))
    ds = r["per_dopant"]["Sr"]["dopant_specific"]
    assert ds["site_trip"] == {"136": 3} and ds["applies"]
    assert r["per_dopant"]["Sr"]["calibrated"]["class_validated"] is None and "no class" in r["per_dopant"]["Sr"]["a1"]["class"]
    assert all(r["per_dopant"][d]["calibrated"]["class_validated"] is None for d in TOKENS)        # C1 then fails
    r = m.evaluate(_planted(eb=eb, fail=[(h, f"s2_{h}_Ca136o0_vac", [5]) for h in PROD8[:2]]))
    ds = r["per_dopant"]["Ca"]["dopant_specific"]
    assert ds["site_trip"] == {} and ds["n_failed"] == 2 and not ds["applies"]                  # 2/32 = 6.25%
    # 11% of the first-shell units of Cl (14 of 128, at most 2 hosts per site) -> no class; 12 of 128 (9.4%) -> none
    slots = [(PROD8[i % 8], SITES["X"]["first"][i // 2], "vac" if i % 2 else "novac") for i in range(16)]
    f14 = [(h, f"s2_{h}_Cl{j}o0_{leg}", [2]) for h, j, leg in slots[:14]]
    f12 = [(h, f"s2_{h}_Cl{j}o0_{leg}", [2]) for h, j, leg in slots[:12]]
    r14, r12 = m.evaluate(_planted(eb=eb, fail=f14)), m.evaluate(_planted(eb=eb, fail=f12))
    d14, d12 = r14["per_dopant"]["Cl"]["dopant_specific"], r12["per_dopant"]["Cl"]["dopant_specific"]
    assert d14["applies"] and not d14["site_trip"] and abs(d14["fraction"] - 14 / 128) < 1e-12
    assert not d12["applies"] and r14["per_dopant"]["Cl"]["calibrated"]["class_validated"] is None
    # failures of check 1 or 4 are not dopant-specific; a V+_Rj-invalid site does not count
    r = m.evaluate(_planted(eb=eb, fail=[(h, f"s2_{h}_Sr136o0_vac", [4]) for h in PROD8[:4]]))
    assert not r["per_dopant"]["Sr"]["dopant_specific"]["applies"]
    r = m.evaluate(_planted(eb=eb, fail=[(h, f"s2_{h}_Sr136o0_vac", [3]) for h in PROD8[:3]],
                            invalid=[(h, f"s2_{h}_VB136") for h in PROD8[:3]]))
    assert not r["per_dopant"]["Sr"]["dopant_specific"]["applies"]
    # a rejected pair counts in both legs (I-C10); A2 units enter the second 10% evaluation
    r = m.evaluate(_planted(eb=eb, rejected=[(h, "Ca124") for h in PROD8[:3]]))
    assert r["per_dopant"]["Ca"]["dopant_specific"]["site_trip"] == {"124": 3}
    f3x = [(h, f"s2_{h}_Cl{j}o0_novac", [2]) for h, j in list(zip(PROD8, (49, 53, 90, 102)))] + \
        [(h, f"s2_{h}_Cl{j}o0_vac", [2]) for h, j in zip(PROD8[4:], (49, 53, 90, 102))]
    a2b = [(p, f"s2r_{p}_Cl{CAL[p]['X']}o0_{leg}", {"valid_final": False, "failed_checks": [3]})
           for p in PILOTS for leg in LEGS]
    r = m.evaluate(_planted(eb=eb, fail=f3x + [(PROD8[0], "s2_m06_Cl137o0_vac", [2]),
                                                (PROD8[1], "s2_m02_Cl138o0_vac", [2]),
                                                (PROD8[2], "s2_m16_Cl137o0_novac", [2]),
                                                (PROD8[3], "s2_m12_Cl138o0_novac", [2])], a2_bad=a2b))
    dd = r["per_dopant"]["Cl"]["dopant_specific"]
    assert dd["n_failed"] == 12 and dd["fraction"] <= 0.10 and dd["fraction_with_a2"] > 0.10 and dd["applies"]
    # multi-pose production (review-1 F4): inadmissible displaced Cs starts at FA28 on 3 of 8 hosts are not starts
    # (section 9) and do not trip the rule; a rejected default start p0 on 3 of 8 hosts does
    tm = _planted(eb=eb, multi_cs=True)
    for h in PROD8[:3]:
        tm["hosts"][h]["pair_rejected"]["Cs28"] = ["p3", "p5"]
    dm = m.evaluate(tm)["per_dopant"]["Cs"]["dopant_specific"]
    assert not dm["applies"] and dm["n_failed"] == 0, dm
    for h in PROD8[:3]:
        tm["hosts"][h]["pair_rejected"]["Cs28"] = ["p0", "p3"]
    dm = m.evaluate(tm)["per_dopant"]["Cs"]["dopant_specific"]
    assert dm["applies"] and dm["site_trip"] == {"28": 3}, dm
    return ("one site on 3 of 8 hosts trips (2 does not); 14/128 Cl units trip, 12/128 do not; checks 1, 4 and "
            "V+-invalid sites excluded; rejected pairs; A2 units in the second 10% evaluation; multi-pose: rejected "
            "displaced starts do not count, a rejected p0 does")


def case_noclass(m):
    eb = {"Sr": 120.0, "Ca": -75.0, "Cl": 0.0, "Cs": 0.0, "GA": 60.0}
    r = m.evaluate(_planted(eb=eb, gates={"G1": {"Ca": False}}))
    assert r["per_dopant"]["Ca"]["calibrated"]["class_validated"] is None and "G1" in r["per_dopant"]["Ca"]["a1"]["class"]
    assert r["per_dopant"]["Sr"]["calibrated"]["class_validated"] == "repels"
    r = m.evaluate(_planted(eb=eb, gates={"N": {"GA": {"pass": False, "sigma_far_meV": 30.0, "df": 6}}}))
    assert r["per_dopant"]["GA"]["calibrated"]["class_validated"] is None and LABEL_GATE_N in r["per_dopant"]["GA"]["a1"]["class"]
    r = m.evaluate(_planted(eb=eb, gates={"multi_pose_cut": {"Cs": True}}))
    assert r["per_dopant"]["Cs"]["calibrated"]["class_validated"] is None and LABEL_POSE_CUT in r["per_dopant"]["Cs"]["a1"]["class"]
    assert r["per_dopant"]["Cl"]["calibrated"]["class_validated"] is not None
    return "G1 fail, gate-N fail and a pose-dependent cut give no class at either tier (others unaffected)"


def case_edges(m):
    eb = {"Sr": 120.0, "Ca": -75.0, "Cl": 0.0, "Cs": 0.0, "GA": 60.0}
    # n_d < 2: GA invalid on 7 of 8 hosts (far quartet invalid)
    r = m.evaluate(_planted(eb=eb, invalid=[(h, f"s2_{h}_GA188o0_vac") for h in PROD8[1:]]))
    g = r["per_dopant"]["GA"]
    assert g["a1"]["available"] is False and g["calibrated"]["available"] is False and g["controls"]["C4"]["pass"] is False
    assert g["controls"]["C2"]["pass"] is False                                              # I-C9
    # m_d = 0 for Cs (both A2 quartets invalid) -> calibrated unavailable; df_delta = 4 still >= 3
    bad = [(p, f"s2r_{p}_Cs{CAL[p]['A']}o0_novac", {"end_rule": "unconverged_cap"}) for p in PILOTS]
    r = m.evaluate(_planted(eb=eb, a2_bad=bad))
    assert r["delta_pool"]["m"]["Cs"] == 0 and r["delta_pool"]["df_delta"] == 4
    assert r["per_dopant"]["Cs"]["calibrated"]["available"] is False and r["per_dopant"]["Cs"]["a1"]["available"]
    # df_delta = 0: every dopant with m_d = 1
    bad = [("m05", f"s2r_m05_{d}{CAL['m05'][SUBLATTICE[d]]}o0_vac", {"valid_final": False}) for d in TOKENS]
    r = m.evaluate(_planted(eb=eb, a2_bad=bad))
    assert r["delta_pool"]["df_delta"] == 0 and r["delta_pool"]["s2_delta"] is None
    assert all(r["per_dopant"][d]["calibrated"]["available"] is False for d in TOKENS)
    assert r["separability"]["a_far_meV"] == abs(r["delta_far"]["delta_meV"])               # fail-closed
    # n_j = 1: a site valid on one host only has a null per-site interval
    inv = [(h, f"s2_{h}_Cl49o0_vac") for h in PROD8[1:]]
    r = m.evaluate(_planted(eb=eb, invalid=inv))
    het = r["per_dopant"]["Cl"]["heterogeneity"]["A1"]
    assert het["n_j"]["49"] == 1 and het["intervals"]["49"] is None and het["intervals"]["53"] is not None
    # plateau-excluded intervals and the shared-region sensitivity with 0-3 regions
    r = m.evaluate(_planted(eb=eb, plateau=[("m30", "s2r_m30_Sr136o0_vac")]))
    pe = r["reported"]["plateau_excluded"]
    assert pe["flagged_deltas"]["Sr"] == ["m30"] and pe["pool"]["m"]["Sr"] == 1 and pe["pool"]["df_delta"] == 4
    assert r["reported"]["shared_region_sensitivity"]["regions"] == 3
    for drop, want in (([], 3), (["X"], 2), (["X", "A"], 1), (["X", "A", "B"], 0)):
        bad = [("m05", f"s2r_m05_{d}{CAL['m05'][SUBLATTICE[d]]}o0_vac", {"valid_final": False})
               for d in TOKENS if SUBLATTICE[d] in drop]
        rr = m.evaluate(_planted(eb=eb, a2_bad=bad))
        sens = rr["reported"]["shared_region_sensitivity"]
        assert sens["regions"] == want, (drop, sens["regions"])
        assert (sens["per_dopant"] is None) == (want == 0)
    # the q = 0, WP2c, D3 and MACE ledger rows exist
    rep = r["reported"]
    assert rep["D3BJ"]["status"] == "not computed" and rep["mace_ledger"]["label"] == LABEL_MACE
    assert rep["mace_ledger"]["Eb_meV"]["Sr"]["m06"]["136"] is not None
    # write_eval refuses a second write; a rerun goes beside the first output
    d = tempfile.mkdtemp(prefix="s2_48_write_")
    p = os.path.join(d, "s2_eval.json")
    dump = lambda o, path: json.dump(o, open(path, "w"), default=str)         # noqa: E731
    m.write_eval({"x": 1}, p, dumper=dump)
    try:
        m.write_eval({"x": 2}, p, dumper=dump)
        raise AssertionError("second write accepted")
    except FileExistsError:
        pass
    p2 = m.write_eval({"x": 3}, p, rerun={"cause": "case_edges"}, dumper=dump)
    assert p2.endswith("s2_eval.rerun1.json") and json.load(open(p))["x"] == 1
    return ("n_d < 2, m_d = 0, df_delta = 0 (a_far fail-closed), n_j = 1, plateau-excluded intervals, shared-region "
            "sensitivity with 3/2/1/0 regions, write_eval refuses a second write")


class _ArchLayout:
    """Archive paths of the interface spec §5.2 (as scripts/46 Layout kind 'archive'), for the round-trip test."""

    def __init__(self, root):
        self.root = root

    def campaign_dir(self, c):
        return os.path.join(self.root, c)

    def record(self, c, wid):
        return os.path.join(self.root, c, "records", f"{wid}.json")

    def distinct(self, c, h, T, j, leg):
        return os.path.join(self.root, c, "pairs", f"{h}_{T}{int(j)}_{leg}.distinct.json")

    def sp_dir(self, c, label):
        return os.path.join(self.root, c, "raw")

    def a2_dir(self, c, label):
        return os.path.join(self.root, c, "raw")

    def a2_parts(self, c, label):
        return sorted(glob.glob(os.path.join(self.root, c, "raw", f"{label}.p*.out.gz")))

    def gate(self, c, name):
        return os.path.join(self.root, c, "gates", f"{name}.json")

    def region(self, c, member, L, j):
        return os.path.join(self.root, c, "regions", f"{member}_{L}{int(j)}.json")


def _archive_from_table(t, root):
    """Write a synthetic table as an archive (records, fake outputs as gzip JSON, A2 records and parts, gates,
    state) so that assemble() can be tested against the table it should reproduce."""
    lay = _ArchLayout(root)

    def dump(path, obj, gz=False):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if gz:
            with gzip.open(path, "wt") as fh:
                json.dump(obj, fh)
        else:
            json.dump(obj, open(path, "w"))
    for h, H in t["hosts"].items():
        c = "c1" if h in PILOTS else "c3"
        dump(lay.record(c, f"s2_{h}_host"), {"member": h, "cell_kind": "host", "labels": [f"s2_{h}_host"],
                                             "validity": {"valid": H["host_valid"], "failed": []},
                                             "relax": {"E_mace_eV": H["E_mace"].get(f"s2_{h}_host")}})
        for lab in set(H["F"]) | set(H["cell_valid"]):
            raw = os.path.join(lay.campaign_dir(c), "raw", f"{lab}.out.gz")
            F = H["F"].get(lab)
            if lab in H["F"]:
                dump(raw, {"job_done": True, "scf_converged": F is not None, "F_eV": F}, gz=True)
            if lab == f"s2_{h}_host" or lab not in H["cell_valid"]:
                continue
            m = re.fullmatch(rf"s2_{h}_(?:V(?P<L>[BAX])(?P<vj>\d+)|(?P<T>Sr|Ca|Cl|Cs|GA)(?P<j>\d+)o(?P<k>\d+)_(?P<leg>novac|vac))",
                             lab)
            rlab = lab
            if m.group("L"):
                wid, kind, rec = f"s2_{h}_V{m.group('L')}{m.group('vj')}", "V", {"site": int(m.group("vj"))}
            else:
                wid = f"s2_{h}_{m.group('T')}{m.group('j')}p{m.group('k')}_{m.group('leg')}"
                kind = "D" if m.group("leg") == "novac" else "DV"
                rec = {"token": m.group("T"), "site": int(m.group("j")), "leg": m.group("leg"), "start": f"p{m.group('k')}"}
                if m.group("k") != "0":
                    rlab = None                      # scripts/46 labels only the p0 record; o<k> via distinct
            dump(lay.record(c, wid), {"member": h, "cell_kind": kind, "labels": [rlab] if rlab else [], "work_id": wid, **rec,
                                      "validity": {"valid": H["cell_valid"][lab],
                                                   "failed": H["failed_checks"].get(lab) or []},
                                      "relax": {"E_mace_eV": H["E_mace"].get(lab)}})
        for tj, v in (H.get("pair_rejected") or {}).items():
            mm = re.fullmatch(r"(Sr|Ca|Cl|Cs|GA)(\d+)", tj)
            for st in (["p0"] if v is True else list(v)):
                dump(os.path.join(lay.campaign_dir(c), "pairs", f"{h}_{tj}{st}.json"),
                     {"member": h, "token": mm.group(1), "site": int(mm.group(2)), "start": st, "status": "rejected"})
        for tok, po in (H.get("pose") or {}).items():
            for j, legs in (po.get("minima") or {}).items():
                for leg, mins in legs.items():
                    dump(lay.distinct(c, h, tok, int(j), leg),
                         {"member": h, "token": tok, "site": int(j), "leg": leg, "map": {o: f"p{o[1:]}" for o in mins},
                          "work_ids": {o: f"s2_{h}_{tok}{j}p{o[1:]}_{leg}" for o in mins},
                          "labels": {o: f"s2_{h}_{tok}{j}{o}_{leg}" for o in mins}})
    for p, A in t["a2"].items():
        dump(lay.record("c1", f"s2_{p}_host"), {"member": p, "cell_kind": "host", "labels": [f"s2_{p}_host"],
                                                "validity": {"valid": True, "failed": []}, "relax": {}})
        for lab, cell in A.items():
            c = g49.label_campaign(lab)
            if g49.a2_cell(lab)["kind"] != "host":
                a1 = _a1_label(lab)
                dump(lay.record("c1", a1.replace("o0_", "p0_")), {"member": p, "cell_kind": "x", "labels": [a1],
                     "validity": {"valid": cell["a1_valid"], "failed": []}, "relax": {}})
            dump(os.path.join(lay.a2_dir(c, lab), f"{lab}.a2.json"),
                 {"status": cell["status"], "restarts": cell["restarts"], "n_config": cell["n_config"],
                  "validity_final": {"valid": cell["valid_final"], "failed": cell["failed_checks"]}})
            dump(os.path.join(lay.a2_dir(c, lab), f"{lab}.p1.out.gz"),
                 {"F0": cell["F0_eV"], "Ffin": cell["Ffin_eV"], "end": cell["end_rule"], "n": cell["n_config"]}, gz=True)
    g = t["gates"]
    dump(lay.gate("c1", "G1"), {"decision": {"G1": g["G1"]}})
    dump(lay.gate("c1", "N"), {"result": {"dopants": g["N"]}})
    dump(lay.gate("c1", "pose"), {"decision": {"pose": {k: v["mode"] for k, v in g["pose"].items()}},
                                  "result": g["pose"]})
    dump(os.path.join(lay.campaign_dir("c4"), "state_end.json"),
         {"n": t["n"], "stage0": {f"production_n{t['n']}": t["production"], "m05_cal": t["a2_sites"]["m05"]},
          "cuts": g["cuts"], "multi_pose_cut": g["multi_pose_cut"]})
    return lay


def _fake_parsers():
    def sp_status(raw, lab):
        p = os.path.join(raw, f"{lab}.out.gz")
        with gzip.open(p, "rt") as fh:
            d = json.load(fh)
        return {"status": "complete" if d["job_done"] and d["scf_converged"] else "missing"}

    def sp_parser(path, read="full", free=None):
        with gzip.open(path, "rt") as fh:
            return json.load(fh)

    def relax_parser(parts, read="full", mapping=None):
        with gzip.open(parts[-1], "rt") as fh:
            d = json.load(fh)
        k = d["n"] - 1
        return {"F_eV": {0: d["F0"], k: d["Ffin"]}, "k_last": k, "n_config": d["n"], "end": d["end"]}
    return {"sp_parser": sp_parser, "sp_status": sp_status, "relax_parser": relax_parser,
            "end_rule_fn": lambda rel: {"outcome": rel["end"]}, "record_loader": lambda p: json.load(open(p))}


def case_assemble(m):
    t = synth_table(multi_cs=True, fail=[("m22", "s2_m22_Cl90o0_novac", [3]), ("m02", "s2_m02_Cs28o1_vac", [5])],
                    missing_sp=[("m23", "s2_m23_GA28o0_vac")], invalid=[("m26", "s2_m26_Ca172o0_novac")],
                    plateau=[("m05", "s2r_m05_Cl49o0_vac")], rejected=[("m16", "Sr124")],
                    a2_bad=[("m30", "s2r_m30_GA128o0_vac", {"valid_final": False, "failed_checks": [3]})])
    root = tempfile.mkdtemp(prefix="s2_48_archive_")
    lay = _archive_from_table(t, root)
    # round 3: the four C1 gate files in one directory of this (laptop) volume, gate N first and then the n rule
    # under its name 'nrule' (N-F15); the pose gate's near/far records with N_D, N_D+V and the count term (N-F26);
    # an SP output with forces whose free-atom summary carries the per-atom norms (scripts/47 N-B18, N-F28)
    pg = json.load(open(lay.gate("c1", "pose")))
    cnt = {"N_D": 3, "N_DV": 2, "count_term_meV": 25.7 * math.log(1.5), "delta_pose_meV": 1.0}
    pg["result"]["Cs"].update({"near": dict(cnt), "far": dict(cnt)})
    json.dump(pg, open(lay.gate("c1", "pose"), "w"))
    json.dump({"gate": "nrule", "decision": {"n": t["n"]}, "result": {"n": t["n"]}}, open(lay.gate("c1", "nrule"), "w"))
    raw = os.path.join(lay.campaign_dir("c3"), "raw", "s2_m06_host.out.gz")
    with gzip.open(raw, "rt") as fh:
        o = json.load(fh)
    o["forces"] = {"all": {"rms_eVA": 0.01, "max_eVA": 0.02, "n": 3},
                   "free": {"rms_eVA": 0.01, "max_eVA": 0.02, "n": 2, "indices": [0, 2], "norms_eVA": [0.02, 0.004]}}
    with gzip.open(raw, "wt") as fh:
        json.dump(o, fh)
    sites = lambda h: copy.deepcopy(SITES)                                   # noqa: E731
    t2 = m.assemble(root, layout=lay, sites_fn=sites, cal_sites=CAL, wp1_dir=root, **_fake_parsers())
    a, b = flatten_eval(m.evaluate(t)), flatten_eval(m.evaluate(t2))
    worst = compare(a, b, tol=1e-9)
    r1, r2 = m.evaluate(t), m.evaluate(t2)
    for d in TOKENS:
        assert r1["per_dopant"][d]["dopant_specific"]["n_failed"] == r2["per_dopant"][d]["dopant_specific"]["n_failed"]
    assert t2["hosts"]["m16"]["pair_rejected"] == {"Sr124": ["p0"]}
    # multi-pose kept minima o<k> take their validity from the distinct record's work ids (review-2 F4)
    k1 = [lab for lab in t["hosts"]["m02"]["cell_valid"] if re.search(r"Cs\d+o[1-9]\d*_", lab)]
    assert k1 and all(t2["hosts"]["m02"]["cell_valid"].get(x) == t["hosts"]["m02"]["cell_valid"][x] for x in k1)
    assert t2["hosts"]["m02"]["cell_valid"]["s2_m02_Cs28o1_vac"] is False
    assert t2["a2"]["m30"]["s2r_m30_GA128o0_vac"]["valid_final"] is False
    assert sorted(os.listdir(os.path.dirname(lay.gate("c1", "N")))) == ["G1.json", "N.json", "nrule.json", "pose.json"]
    assert set(t2["gates"]["N"]) == set(TOKENS) and all("pass" in v for v in t2["gates"]["N"].values()), t2["gates"]["N"]
    assert json.load(open(lay.gate("c1", "nrule")))["decision"]["n"] == t["n"]
    rep2 = r2["reported"]
    assert abs(rep2["pose_pilot"]["Cs"]["near"]["count_term_meV"] - 25.7 * math.log(1.5)) < 1e-9
    assert r2["per_dopant"]["Cs"]["calibrated"]["pose_note"]["N_D"] == 3
    assert rep2["residual_forces"]["m06"]["s2_m06_host"]["free"]["norms_eVA"] == [0.02, 0.004]
    return (f"assemble() rebuilds the table from a synthetic archive: {len(a)} statistics equal (worst {worst:.1e} meV); "
            f"G1, N, nrule and pose gate files side by side keep gate N for all 5 dopants (N-F15); the pose gate's "
            f"count term and the free-atom force norms reach s2_eval.json")


def case_hygiene(m):
    try:
        c46 = dep("c46")
    except g49.MissingDependency:
        return "skipped (scripts/46 absent)"
    if not hasattr(c46, "hygiene_violations"):
        return "skipped (scripts/46 mocked)"
    bad = {fn: c46.hygiene_violations(open(os.path.join(HERE, fn)).read(), kind="code")
           for fn in ("48_s2_analysis.py", "49_s2_gates.py")}
    assert not any(bad.values()), bad
    t = synth_table()
    r = m.evaluate(t)
    txt = json.dumps({"schema": EVAL_SCHEMA, **r}, default=str)
    assert not c46.hygiene_violations(txt, kind="json"), c46.hygiene_violations(txt, kind="json")
    dec = open(os.path.join(ROOT, "results/objective2/s2/S2_DECISION.md"), encoding="utf-8").read()
    assert " ".join(LABEL_VALIDATED.split()) in " ".join(dec.replace('"', " ").split()), "label differs from S2_DECISION §7"
    return ("48 and 49 pass the public-repository rules of scripts/46; so does an s2-eval-1 body; the validated label "
            "is the S2_DECISION.md §7 text")


def _this_module():
    """The functions a case uses, from this file (a rerun runs the same case on the first code instead)."""
    import types
    return types.SimpleNamespace(evaluate=evaluate, write_eval=write_eval, assemble=assemble, c2_noise=c2_noise,
                                 required_hosts=required_hosts, analysis_guard=analysis_guard, classify=classify,
                                 _commit_history=_commit_history, _campaign_commit=_campaign_commit)


def _a1cond_table():
    """Round-2 STAT-1: Ca's two planted deltas differ by 50 meV (m30 -40, m05 +10), every other dopant's by a few;
    the far quartet carries about 0 meV, as K3 would pass on it."""
    delta = {"Sr": {"m30": 4.0, "m05": 2.0}, "Ca": {"m30": -40.0, "m05": 10.0}, "Cl": {"m30": 3.0, "m05": 1.0},
             "Cs": {"m30": -1.0, "m05": 1.0}, "GA": {"m30": 2.0, "m05": 0.5}}
    t = synth_table(seed=7, eb={"Sr": 120.0, "Ca": 30.0, "Cl": 0.0, "Cs": 0.0, "GA": 60.0}, delta=delta, noise=2.0,
                    host_sd=3.0, dfar=1.0)
    for k in ("F0_eV", "Ffin_eV"):
        t["a2"]["m30"]["s2r_m30_Sr76o0_vac"][k] -= 0.120
    return t


def case_a1_start(m):
    """Round-2 STAT-1 with D-S0-2 as revised (2026-11-04): delta validity follows §11 literally, so an A1-invalid start
    cell of an A2 relaxation changes no delta, class, control or interval; rule V with the A1-start condition is
    reported as a sensitivity row only, and equals the decisive result of a table in which that delta is dropped."""
    t = _a1cond_table()
    r0 = m.evaluate(copy.deepcopy(t))
    assert "a1_condition" not in r0, "the withdrawn dual-reading construction is still present"
    s0 = r0["reported"]["a1_start_sensitivity"]
    assert s0["label"].startswith("reported only") and s0["differs_from_section11"] is False, s0
    assert not s0["a2_cells_with_A1_start_not_valid"]
    assert r0["per_dopant"]["Ca"]["calibrated"]["class_validated"] is None
    # an A1-invalid start of Ca D(136): the §11 rule decides (Ca m_d 2, 'not resolved'), every decisive number unchanged
    tA = copy.deepcopy(t)
    tA["a2"]["m30"]["s2r_m30_Ca136o0_novac"]["a1_valid"] = False
    rA = m.evaluate(tA)
    compare(flatten_eval(rA), flatten_eval(r0), tol=0.0)
    ca = rA["per_dopant"]["Ca"]["calibrated"]
    assert ca["m_d"] == 2 and rA["delta_pool"]["m"]["Ca"] == 2 and ca["class_rule_v"] == "not resolved" and ca["class_validated"] is None
    assert not any("reading" in x for d in TOKENS for x in rA["per_dopant"][d]["calibrated"]["no_class_reasons"])
    q = ca["deltas"]["m30"]
    assert q["valid"] is True and q["a1_starts_valid"] is False and q["a1_valid"]["D"] is False, q
    sA = rA["reported"]["a1_start_sensitivity"]["per_dopant"]["Ca"]
    assert sA["m_d"] == 1 and sA["class_rule_v"] == "repels" and sA["class_with_controls"] == "repels", sA
    assert sA["differs_from_section11"] and rA["reported"]["a1_start_sensitivity"]["a2_cells_with_A1_start_not_valid"] \
        == ["m30:s2r_m30_Ca136o0_novac"]
    # the sensitivity row is the decisive result of the table with that delta dropped by the §11 rule instead
    tD = copy.deepcopy(t)
    tD["a2"]["m30"]["s2r_m30_Ca136o0_novac"]["valid_final"] = False
    cD = m.evaluate(tD)["per_dopant"]["Ca"]["calibrated"]
    assert cD["interval_meV"] == sA["interval_meV"] and cD["class_validated"] == sA["class_with_controls"], (cD, sA)
    # an A1-invalid start of the far quartet: delta_far stays valid (as for K3) and Sr keeps its validated 'repels'
    tB = copy.deepcopy(t)
    tB["a2"]["m30"]["s2r_m30_VB76"]["a1_valid"] = False
    rB = m.evaluate(tB)
    compare(flatten_eval(rB), flatten_eval(r0), tol=0.0)
    assert rB["delta_far"]["valid"] is True and rB["separability"]["c5_far"] is True
    assert rB["per_dopant"]["Sr"]["calibrated"]["class_validated"] == "repels"
    k3 = g49.k3_eval({lab: {"F_final_eV": c["Ffin_eV"], "end_rule": c["end_rule"], "valid_final": c["valid_final"],
                            "failed_checks": c["failed_checks"], "a1_valid": c["a1_valid"], "status": c["status"]}
                      for lab, c in tB["a2"]["m30"].items()})
    assert k3["K3"] == "pass" and k3["a1_invalid_reported"] == ["s2r_m30_VB76"], k3     # the same quartet validity
    sB = rB["reported"]["a1_start_sensitivity"]
    assert sB["delta_far_valid"] is False and sB["differs_from_section11"]
    assert all(sB["per_dopant"][d]["class_with_controls"] is None and "C5" in sB["per_dopant"][d]["controls_failed"]
               for d in TOKENS), sB["per_dopant"]
    assert not any(c["label"] == "s2r_m30_VB76" for c in rB["reported"]["invalid_cells"])
    return (f"an A1-invalid start of Ca D(136): Ca m_d 2, 'not resolved' I = [{ca['interval_meV'][0]:.1f}, "
            f"{ca['interval_meV'][1]:.1f}] meV, every decisive number equal to the all-valid table; sensitivity row "
            f"(reported only) m_d 1 'repels' I = [{sA['interval_meV'][0]:.1f}, {sA['interval_meV'][1]:.1f}] meV, equal "
            f"to dropping that delta; an A1-invalid far-quartet start: delta_far valid as K3 passes on it, Sr "
            f"validated 'repels', the sensitivity row gives no class (C5)")


def _multi_cs_table(seed, starts, failing):
    t = synth_table(seed=seed, eb={"Sr": 120.0, "Ca": -75.0, "Cl": 0.0, "Cs": -75.0, "GA": 60.0}, multi_cs=True)
    for h in t["production"]:
        H = t["hosts"][h]
        for j in t["sites"][h]["A"]["first"]:
            for leg in LEGS:
                k = starts(h, j, leg)
                sf = {f"p{i}": [] for i in range(k)}
                for i in failing.get((h, j, leg), []):
                    sf[f"p{i}"] = [3]
                H["pose"]["Cs"]["start_failed"].setdefault(str(j), {})[leg] = sf
                if len(failing.get((h, j, leg), [])) == k:                    # every start failed: no kept minimum
                    H["pose"]["Cs"]["minima"][str(j)][leg] = []
    return t


def case_dopant_specific_cells(m):
    """Round-2 STAT-3: in multi-pose production the 10% rule counts cells (every relaxed start), not legs."""
    P = PROD8
    fl = {(P[0], 28, "novac"): [3], (P[1], 28, "novac"): [3], (P[2], 92, "novac"): [3], (P[3], 92, "novac"): [3],
          (P[4], 128, "novac"): [3]}
    r = m.evaluate(_multi_cs_table(13, lambda h, j, leg: 7, fl))
    ds = r["per_dopant"]["Cs"]["dopant_specific"]
    assert not ds["applies"] and ds["n_cells"] == 336 and ds["n_failed_cells"] == 5 and not ds["site_trip"], ds
    fl2 = {(h, 28, leg): list(range(7)) for h in P[:2] for leg in LEGS}
    r = m.evaluate(_multi_cs_table(14, lambda h, j, leg: 7 if (h, j, leg) in fl2 else 3, fl2))
    ds = r["per_dopant"]["Cs"]["dopant_specific"]
    assert ds["applies"] and ds["n_cells"] == 160 and ds["n_failed_cells"] == 28 and not ds["site_trip"], ds
    assert r["per_dopant"]["Cs"]["calibrated"]["class_validated"] is None
    assert LABEL_DOPANT_SPECIFIC in r["per_dopant"]["Cs"]["a1"]["class"]
    return ("7 starts per leg, one failing start in 5 legs: 5/336 cells, no trip; all 7 starts failing in 4 legs at "
            "FA28 (3 starts elsewhere): 28/160 cells trips, Cs gets no class at either tier")


def case_flag_rounding(m):
    """Round-2 STAT-6: at the k = 2 flag threshold the shifted recomputation can flip by rounding; the calibrated
    tier uses the A1 flag (§14), records the flip and raises nothing."""
    x = 85.19315894346816
    sites = {124: [-x], 136: [0.0]}
    h0 = heterogeneity(sites, 0.0)
    flips = [s for s in (-0.4564912908059071, -43.87629070651185) if heterogeneity(sites, s)["flag"] != h0["flag"]]
    assert flips, "no rounding flip found at the threshold"
    hc = cal_heterogeneity(sites, flips[0], h0)
    assert hc["flag"] == h0["flag"] and hc["flag_recomputed"]["within_rounding"], hc
    return (f"threshold depth {x} meV: A1 flag {h0['flag']}, shifted recomputation flips at shift {flips[0]}; the "
            f"calibrated tier keeps the A1 flag and records the flip (gap {hc['flag_recomputed']['gap_to_kT_meV']:.1e} meV)")


def case_rule_v_r4(m):
    """Round-4 R4-C24-6 (coverage; the code was right): (a) the calibrated sign rule counts Y_h + delta_bar_d, not Y_h:
    10 hosts, delta_bar_Ca = -10 meV, 8 hosts positive at A1 (one at +5 meV) and 7 after the shift, both intervals above
    +25.7 meV: A1 'repels', calibrated 'not resolved', as the independent implementation; (b) 'entirely above +25.7'
    is strict (I-20): an interval whose lower bound is exactly 25.7 meV is not 'repels', nor one whose upper bound is
    exactly -25.7 meV 'binds', at either tier (classify is the one rule of both). A mutation of either rule makes this
    case fail."""
    P10 = PROD8 + ["m33", "m13"]
    t = _planted(eb={"Sr": 120.0, "Ca": -75.0, "Cl": 0.0, "Cs": 0.0, "GA": 60.0}, prod=P10,
                 delta={**{d: {"m30": 2.0, "m05": -1.0} for d in TOKENS}, "Ca": {"m30": -10.0, "m05": -10.0}})
    target = [400.0 + 3.0 * i for i in range(7)] + [5.0, -1.0, -1.5]
    for h, y in zip(P10, target):
        _shift_Y(t, "Ca", h, y)
    r = m.evaluate(t)
    a1, cal = r["per_dopant"]["Ca"]["a1"], r["per_dopant"]["Ca"]["calibrated"]
    dbar = r["per_dopant"]["Ca"]["controls"]["C5"]["delta_bar_meV"]
    assert abs(dbar + 10.0) < 1e-6, dbar
    assert a1["interval_meV"][0] > KT and cal["interval_meV"][0] > KT, (a1["interval_meV"], cal["interval_meV"])
    assert a1["class_rule_v"] == "repels" and cal["class_rule_v"] == NOT_RESOLVED, (a1["class_rule_v"], cal["class_rule_v"])
    compare(flatten_eval(r), independent(t))
    hv = [10.0] * 8
    for lo, hi, want in ((KT, KT + 50.0, False), (KT + 1e-9, KT + 50.0, True)):
        assert (m.classify(lo, hi, hv, 0.0) == "repels") is want, (lo, m.classify(lo, hi, hv, 0.0))
    hn = [-10.0] * 8
    for lo, hi, want in ((-KT - 50.0, -KT, False), (-KT - 50.0, -KT - 1e-9, True)):
        assert (m.classify(lo, hi, hn, 0.0) == "binds") is want, (hi, m.classify(lo, hi, hn, 0.0))
    return (f"calibrated sign rule on Y_h + delta_bar ({dbar:.1f} meV): A1 'repels' (8/10), calibrated 'not resolved' "
            f"(7/10), both intervals above k_BT, equal to the independent implementation; lo = 25.7 meV not 'repels', "
            f"25.7 + 1e-9 'repels'; hi = -25.7 meV not 'binds'")


def _pilot_noise_table(m):
    t = synth_table()
    far4 = {p: g49.far4(p) for p in PILOTS}
    truth = {}
    for p in PILOTS:
        P = {"host_valid": True, "F": {g49.lab_host(p): -80000.0}, "cell_valid": {}, "failed_checks": {},
             "pair_rejected": {}, "pose": {}, "E_mace": {g49.lab_host(p): -1200.0}}
        for k, row in enumerate(g49.noise_cells(p)):
            labs = row["labels"]
            P["F"][labs["V"]], P["cell_valid"][labs["V"]], P["failed_checks"][labs["V"]] = -79996.5, True, []
            P["E_mace"][labs["V"]] = -1197.0
            FD, FDV = -80002.0 + 0.001 * k, -79998.49 + 0.0013 * k
            for leg, F, E in (("D", FD, -1190.0), ("DV", FDV, -1186.98)):
                P["F"][labs[leg]], P["cell_valid"][labs[leg]], P["failed_checks"][labs[leg]] = F, True, []
                P["E_mace"][labs[leg]] = E
            truth[(p, f"{row['d']}{row['f']}")] = g49.eb_meV(FDV, FD, -79996.5, -80000.0)
        t["hosts"][p] = P
    return t, far4, truth


def case_pilot_rows_r4(m):
    """Round-4 R4-C24-4 and R4-C24-3: (a) an assemble round trip with default-pose noise-pilot cells on both pilots:
    every reported noise-pilot row, Cs and Cl included, is valid and equals the E_b gate N takes from the o0 cells,
    with its zero-shot MACE value; a pilot host without any Cs record does not crash the evaluation; (b) an A2 cell
    killed_by_gate whose part output was left in the archive is not parsed and has no relaxation energy."""
    t, far4, truth = _pilot_noise_table(m)
    root = tempfile.mkdtemp(prefix="s2_48_pilot_")
    lay = _archive_from_table(t, root)
    # the helper's A2 part rewrites the records of A2 start cells (the pilot hosts, V+ at Pb76 ...) without their MACE
    # values: put them back from the table
    for hp in glob.glob(os.path.join(lay.campaign_dir("c1"), "records", "*.json")):
        hr = json.load(open(hp))
        E = (t["hosts"].get(hr.get("member")) or {}).get("E_mace") or {}
        for lab in hr.get("labels") or []:
            if E.get(lab) is not None:
                hr["relax"] = {**(hr.get("relax") or {}), "E_mace_eV": E[lab]}
        json.dump(hr, open(hp, "w"))
    killed = "s2r_m30_Ca136o0_novac"
    rp = os.path.join(lay.a2_dir("c2", killed), f"{killed}.a2.json")
    rec = json.load(open(rp)); rec["status"] = "killed_by_gate"; json.dump(rec, open(rp, "w"))
    S = copy.deepcopy(SITES)
    sites = lambda h: ({L: {**S[L], "far4": far4[h][L]} for L in "BAX"} if h in PILOTS else copy.deepcopy(SITES))  # noqa: E731
    fp = _fake_parsers()
    seen = []
    rp_ = fp["relax_parser"]

    def relax_parser(parts, read="full", mapping=None):
        seen.extend(os.path.basename(x) for x in parts)
        return rp_(parts, read=read, mapping=mapping)
    fp["relax_parser"] = relax_parser
    t2 = m.assemble(root, layout=lay, sites_fn=sites, cal_sites=CAL, wp1_dir=root, **fp)
    rep = m.evaluate(t2)["reported"]
    bad = [(p, key, rep["noise_pilot"][p][key]) for (p, key), eb in sorted(truth.items())
           if not (rep["noise_pilot"][p][key]["valid"] and abs(rep["noise_pilot"][p][key]["Eb_meV"] - eb) < 1e-6
                   and rep["noise_pilot"][p][key]["Eb_mace_meV"] is not None)]
    assert not bad, bad[:3]
    ncs = sum(1 for (p, key) in truth if key[:2] in ("Cs", "Cl"))
    t3 = copy.deepcopy(t2); t3["hosts"]["m05"]["pose"].pop("Cs", None)
    m.evaluate(t3)
    assert not any(x.startswith(killed + ".") for x in seen), seen
    a2c = rep["a2_cells"][killed]
    assert a2c["relaxation_energy_meV"] is None and a2c["n_config"] is not None, a2c
    return (f"{len(truth)} noise-pilot rows on m30 and m05 equal gate N's E_b ({ncs} of Cs and Cl), each with its MACE "
            f"value; no Cs record on m05: no crash; a killed_by_gate A2 cell: not parsed, relaxation energy None")


CASES = {"independent implementation": case_independent, "planted classes": case_planted,
         "heterogeneous shell": case_heterogeneous, "refusals": case_refusals, "delta_bar bound": case_delta_bound,
         "dopant-specific rule": case_dopant_specific, "no class": case_noclass, "edge cases": case_edges,
         "assemble round trip": case_assemble, "hygiene": case_hygiene,
         "A1 start validity reported, section 11 decides (round-2 STAT-1, D-S0-2 revised)": case_a1_start,
         "dopant-specific 10% rule over cells (round-2 STAT-3)": case_dopant_specific_cells,
         "heterogeneity flag at the threshold (round-2 STAT-6)": case_flag_rounding,
         "rule-V and control boundaries (round-3 R3C-10)": case_boundaries,
         "count term and the MACE ledger's pilot section (round-3 R3C-3, R3C-4)": case_counts_ledger,
         "one-evaluation guard against the campaign commit (round-3 R3C-6)": case_eval_guard,
         "reported rows: path work, determinism, q = 0, WP2c (round-3 R3C-10)": case_reported_rows,
         "calibrated sign rule and strict class bounds (round-4 R4-C24-6)": case_rule_v_r4,
         "pilot noise rows and killed A2 cells (round-4 R4-C24-4, R4-C24-3)": case_pilot_rows_r4}


def self_test():
    import traceback
    t0 = time.time()
    results = []
    mocked = []
    for alias, mock in (("c46", g49._MockCells), ("q47", g49._MockQE)):
        try:
            dep(alias)
        except g49.MissingDependency:
            g49._DEPS[alias] = mock
            mocked.append(alias)
    print(f"48_s2_analysis self-test: synthetic tables only (no S2 cell); q* = {RULES['Q_STAR']}, k_BT = {KT} meV")
    for alias in ("c46", "q47"):
        print(f"{'MOCKED' if alias in mocked else 'REAL  '} {alias} ({g49.DEP_FILES[alias]})")
    me = _this_module()

    def case(name, fn):
        t = time.time()
        try:
            msg = fn(me)
            results.append((name, True))
            print(f"PASS {name}: {msg}  [{time.time() - t:.2f} s]", flush=True)
        except Exception as e:                                       # noqa: BLE001 (report every failure)
            results.append((name, False))
            print(f"FAIL {name}: {type(e).__name__}: {e}  [{time.time() - t:.2f} s]", flush=True)
            traceback.print_exc(limit=5)

    for nm, fn in CASES.items():
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

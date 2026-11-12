#!/usr/bin/env python
"""G2 of S2B_PLAN.md §6: the vector double difference at the Pb76 far pairs (geometry only; reported only).

For each of the 14 objects that check 5 gated in VB76 against hostB76 (part-d item 3), it compares the response of the
undoped pair, Δr_V = r(VB76) − r(hostB76), with that of the doped pair, Δr_D = r(Sr76o0_vac) − r(Sr76o0_novac). It does
so for the final geometries and again for the k = 0 geometries (the C1 A1 cells). E_b(Pb76) contains both responses with
opposite signs (S2_PLAN P:140). G2 bounds no energy.

Printed per object: |Δr_V|, |Δr_D| and |Δr_D − Δr_V| (0.001 Å); cos(Δr_V, Δr_D) when both lengths are at least 0.02 Å;
for FA, angle(R_V), angle(R_D) and the angle of R_D R_V⁻¹ (0.1°), where R are Horn rotations of the C-N-N skeleton
across each leg. Two nitrogen labellings are printed: the one carried from the host, and the one that minimises the
angle within each leg.

Inputs (closed list):
- the four C2 final geometries, members a2/<label>/<label>.final.extxyz of c2/structures.tar.gz, read in memory and
  checked against the guarded record leaf final_geometry.sha256;
- the four k = 0 geometries, which are the C1 A1 cells cells/<id>/relaxed.extxyz of c1/structures.tar.gz;
- c1/pairs/m30_Sr76p0.json (legs novac and vac) and c1/regions/m30_B76.json;
- the C2 graph job metadata, through part_d_read.Archive.

Maps (P §4): host j → V: j for j < 127, j − 1 for j > 127, j = 127 refused; D: novac old_to_new[j]; D+V: vac
old_to_new[V index]. Elements must agree, with the dopant member exempt. Minimum image in each leg, no alignment; the
fixed atoms of the four cells are asserted to agree within 1e-6 Å.

Anchors (asserted): D5's gated set equals the 14 objects; |Δr_V| and the FA rotations reproduce D5 (part-d item 3,
I 209 0.381 Å; FA 212 0.463 Å, 24.7° and 177.1°); the k = 0 values reproduce part-d item 4 (I 209 0.029 Å; FA 212
0.011 Å and 0.6°).

Geometry only: no energy, force or gate value is read, no calculator is loaded (asserted). It imports the part-d tools
unchanged.

    python g2_square.py --self-test     # synthetic legs from the public reference cell; no C2 file is read
    python g2_square.py --read          # the one read (S2B_PLAN §6); writes g2_output.txt and prints it
"""
import argparse, hashlib, importlib.util, json, os, subprocess, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
S2 = os.path.normpath(os.path.join(HERE, ".."))
REPO = os.path.normpath(os.path.join(S2, "..", "..", ".."))
OUT = os.path.join(HERE, "g2_output.txt")
VI = 127
P = "s2r_m30_"
LABELS = {"host": P + "hostB76", "V": P + "VB76", "D": P + "Sr76o0_novac", "DV": P + "Sr76o0_vac"}
K0_CELLS = {"host": "s2_m30_host", "V": "s2_m30_VB76", "D": "s2_m30_Sr76p0_novac", "DV": "s2_m30_Sr76p0_vac"}
GATED = [("FA", 4), ("FA", 16), ("FA", 68), ("FA", 152), ("FA", 176), ("FA", 200), ("FA", 212),
         ("I", 2), ("I", 77), ("I", 78), ("I", 79), ("I", 175), ("I", 209), ("Pb", 76)]
ANCHOR_FINAL = {("I", 209): (0.381, None, None), ("FA", 212): (0.463, 24.7, 177.1)}
ANCHOR_K0 = {("I", 209): (0.029, None), ("FA", 212): (0.011, 0.6)}
HEADER = ("S2 K3: fail (fail_replan); checks_failed: s2r_m30_VB76, check 5 (C2_RESULT.md). S2b FR: not yet run. "
          "Valid far references: 0 of 1 so far (FR not yet run).")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def tools():
    pdr = _load("part_d_read", os.path.join(HERE, "part_d_read.py"))
    cd, fig, q47, c46 = pdr.tools()
    return pdr, cd, fig, q47, c46


# ---- rotations ----------------------------------------------------------------------------------------------------

def horn_R(P_, Q_):
    """The proper rotation R minimising Σ|R p_i − q_i|² for the centred sets (Horn 1987, unit quaternion)."""
    P_ = np.asarray(P_, float) - np.mean(P_, axis=0)
    Q_ = np.asarray(Q_, float) - np.mean(Q_, axis=0)
    S = P_.T @ Q_
    xx, xy, xz, yx, yy, yz, zx, zy, zz = S.ravel()
    N = np.array([[xx + yy + zz, yz - zy, zx - xz, xy - yx],
                  [yz - zy, xx - yy - zz, xy + yx, zx + xz],
                  [zx - xz, xy + yx, -xx + yy - zz, yz + zy],
                  [xy - yx, zx + xz, yz + zy, -xx - yy + zz]])
    w, V = np.linalg.eigh(N)
    q0, q1, q2, q3 = V[:, np.argmax(w)]
    return np.array([[q0 * q0 + q1 * q1 - q2 * q2 - q3 * q3, 2 * (q1 * q2 - q0 * q3), 2 * (q1 * q3 + q0 * q2)],
                     [2 * (q1 * q2 + q0 * q3), q0 * q0 - q1 * q1 + q2 * q2 - q3 * q3, 2 * (q2 * q3 - q0 * q1)],
                     [2 * (q1 * q3 - q0 * q2), 2 * (q2 * q3 + q0 * q1), q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3]])


def angle_deg(R):
    """Rotation angle of R, stable near 0 and 180 degrees: atan2 of the axial vector of (R - R^T)/2 and (tr R - 1)/2."""
    s = 0.5 * np.linalg.norm([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    return float(np.degrees(np.arctan2(s, (np.trace(R) - 1.0) / 2.0)))


# ---- maps ---------------------------------------------------------------------------------------------------------

def h2v(j, vi=VI):
    if j == vi:
        raise ValueError("the vacancy iodide has no V index")
    return j if j < vi else j - 1


def make_maps(leg_novac, leg_vac, vi=VI):
    o_d = {int(k): int(v) for k, v in leg_novac["old_to_new"].items()}
    o_dv = {int(k): int(v) for k, v in leg_vac["old_to_new"].items()}
    members = {"D": {int(m) for m in leg_novac["members"]}, "DV": {int(m) for m in leg_vac["members"]}}
    return {"host": lambda j: j, "V": lambda j: h2v(j, vi), "D": lambda j: o_d[j], "DV": lambda j: o_dv[h2v(j, vi)]}, members


# ---- the double difference ----------------------------------------------------------------------------------------

def _rel(cd, at_pos, idx, cell):
    return np.vstack([np.zeros(3), cd.mic(at_pos[idx[1:]] - at_pos[idx[0]], cell)])


def _min_label_R(cd, pos_a, pos_b, ia, ib, cell):
    """R across one leg under the nitrogen labelling of b that gives the smaller angle."""
    Pa = _rel(cd, pos_a, ia, cell)
    Rs = [horn_R(Pa, _rel(cd, pos_b, ib, cell)), horn_R(Pa, _rel(cd, pos_b, [ib[0], ib[2], ib[1]], cell))]
    return min(Rs, key=angle_deg)


def double_difference(cd, cells, maps, members, objects, host_ref, check_elements=True):
    """cells: {"host","V","D","DV"} -> Atoms; objects: [(kind, host index)]; host_ref: Atoms used to find FA skeletons.
    Returns one row per object."""
    cell = cells["host"].cell.array
    sym = {k: np.array(a.get_chemical_symbols()) for k, a in cells.items()}
    rows = []
    for kind, j in objects:
        if kind == "FA":
            sk = [int(x) for x in _skeleton(cd, host_ref, j)]
        else:
            sk = [int(j)]
        idx = {k: [maps[k](x) for x in sk] for k in cells}
        if check_elements:
            for k in cells:
                for x, ix in zip(sk, idx[k]):
                    if sym[k][ix] != sym["host"][x] and not (k in members and ix in members[k]):
                        raise ValueError(f"element mismatch: {k} index {ix} against host {x}")
        pos = {k: cells[k].positions for k in cells}
        rV = cd.mic(pos["V"][idx["V"][0]] - pos["host"][idx["host"][0]], cell)[0]
        rD = cd.mic(pos["DV"][idx["DV"][0]] - pos["D"][idx["D"][0]], cell)[0]
        nV, nD = float(np.linalg.norm(rV)), float(np.linalg.norm(rD))
        row = {"kind": kind, "host": int(j), "dr_V": nV, "dr_D": nD, "dd": float(np.linalg.norm(rD - rV)),
               "cos": (float(rV @ rD / (nV * nD)) if min(nV, nD) >= 0.02 else None),
               "dopant_site": any(ix in members.get("D", set()) for ix in idx["D"])}
        if kind == "FA":
            RV = horn_R(_rel(cd, pos["host"], idx["host"], cell), _rel(cd, pos["V"], idx["V"], cell))
            RD = horn_R(_rel(cd, pos["D"], idx["D"], cell), _rel(cd, pos["DV"], idx["DV"], cell))
            RVm = _min_label_R(cd, pos["host"], pos["V"], idx["host"], idx["V"], cell)
            RDm = _min_label_R(cd, pos["D"], pos["DV"], idx["D"], idx["DV"], cell)
            row.update(rot_V=angle_deg(RV), rot_D=angle_deg(RD), rot_rel=angle_deg(RD @ RV.T),
                       rot_V_min=angle_deg(RVm), rot_D_min=angle_deg(RDm), rot_rel_min=angle_deg(RDm @ RVm.T))
        rows.append(row)
    return rows


def _skeleton(cd, at, c):
    s = np.array(at.get_chemical_symbols())
    Ns = np.flatnonzero(s == "N")
    d = np.linalg.norm(cd.mic(at.positions[Ns] - at.positions[c], at.cell.array), axis=1)
    ns = [int(x) for x in Ns[d < 1.6]]
    if s[c] != "C" or len(ns) != 2:
        raise ValueError(f"index {c} is not an FA carbon with two nitrogens")
    return [int(c)] + ns


def fixed_agree(cells, maps, region_free, n_host, vi=VI, tol=1e-6):
    """Max deviation, over the fixed host atoms, of each cell's fixed atom from the host's."""
    free = {int(i) for i in region_free}
    worst = 0.0
    for j in range(n_host):
        if j in free or j == vi:
            continue
        ref = cells["host"].positions[j]
        for k in ("V", "D", "DV"):
            worst = max(worst, float(np.abs(cells[k].positions[maps[k](j)] - ref).max()))
    return worst <= tol, worst


def fmt_rows(rows):
    out = ["    object  host  |dr_V| A  |dr_D| A  |dr_D - dr_V| A  cos  rot_V  rot_D  rot(R_D R_V^-1)  "
           "[min-labelling: rot_V  rot_D  rot_rel]"]
    for r in rows:
        name = r["kind"] + (" (dopant site)" if r["dopant_site"] else "")
        c = "n/a" if r["cos"] is None else f"{r['cos']:.3f}"
        line = f"    {name}  {r['host']}  {r['dr_V']:.3f}  {r['dr_D']:.3f}  {r['dd']:.3f}  {c}"
        if r["kind"] == "FA":
            line += (f"  {r['rot_V']:.1f}  {r['rot_D']:.1f}  {r['rot_rel']:.1f}  "
                     f"[{r['rot_V_min']:.1f}  {r['rot_D_min']:.1f}  {r['rot_rel_min']:.1f}]")
        out.append(line)
    return out


# ---- the read -----------------------------------------------------------------------------------------------------

def read():
    pdr, cd, fig, q47, c46 = tools()
    cd.assert_no_calculator()
    A = pdr.Archive(S2, cd, fig, c46)
    pair = c46.load_record(os.path.join(S2, "c1", "pairs", "m30_Sr76p0.json"))
    region = c46.load_record(os.path.join(S2, "c1", "regions", "m30_B76.json"))
    maps, members = make_maps(pair["legs"]["novac"], pair["legs"]["vac"])
    fin, k0 = {}, {}
    for k, lab in LABELS.items():
        fb = A.final_bytes(lab)
        sha = pdr.leaf(A.a2(lab), "final_geometry", "sha256")
        if hashlib.sha256(fb).hexdigest() != sha:
            raise SystemExit(f"integrity: final geometry sha256 differs from the record ({lab})")
        fin[k] = pdr.atoms_from_bytes(fb)
        k0[k] = A.c1_cell(K0_CELLS[k], "relaxed")
    n_host = len(fin["host"])
    checks = []
    for name, cells in (("final", fin), ("k = 0", k0)):
        ok, worst = fixed_agree(cells, maps, region["free"], n_host)
        if not ok:
            raise SystemExit(f"integrity: fixed atoms disagree beyond 1e-6 A ({name})")
        checks.append(f"fixed atoms of the four cells agree within 1e-6 A ({name})")
    # anchors: D5's gated set and values (part-d item 3); k = 0 values (part-d item 4)
    host_relaxed = A.c1_cell("s2_m30_host", "relaxed")
    d5 = cd.d5_check("V", fin["V"], fin["host"], host_relaxed, region)
    g = [r for r in d5["rows"] if r["gated"]]
    d5_set = sorted(((r["element"] if r["kind"] == "inorganic" else "FA"), r["host"]) for r in g)
    if d5_set != sorted(GATED):
        raise SystemExit("integrity: D5's gated set differs from the 14 objects of part-d item 3")
    rows_f = double_difference(cd, fin, maps, members, GATED, fin["host"])
    rows_0 = double_difference(cd, k0, maps, members, GATED, fin["host"])
    by = {((r["element"] if r["kind"] == "inorganic" else "FA"), r["host"]): r for r in g}
    for r in rows_f:
        d = by[(r["kind"], r["host"])]
        if abs(r["dr_V"] - d["dr_A"]) > 1e-9 or (r["kind"] == "FA" and abs(r["rot_V"] - d["rot_deg"]) > 1e-4):
            raise SystemExit(f"integrity: |dr_V| or rotation differs from D5 ({r['kind']} {r['host']})")
    for key, (dr, rot, rotx) in ANCHOR_FINAL.items():
        r = next(x for x in rows_f if (x["kind"], x["host"]) == key)
        d = by[key]
        if round(r["dr_V"], 3) != dr or (rot is not None and (round(r["rot_V"], 1) != rot
                                                              or round(d["rot_exchanged_deg"], 1) != rotx)):
            raise SystemExit(f"integrity: final anchor differs from part-d item 3 ({key})")
    for key, (dr, rot) in ANCHOR_K0.items():
        r = next(x for x in rows_0 if (x["kind"], x["host"]) == key)
        if round(r["dr_V"], 3) != dr or (rot is not None and round(r["rot_V"], 1) != rot):
            raise SystemExit(f"integrity: k = 0 anchor differs from part-d item 4 ({key})")
    checks += ["final geometries match their record sha256 (4)", "D5 gated set = the 14 objects of part-d item 3",
               "|dr_V| and FA rotations equal D5 at every object", "anchors of part-d items 3 and 4 reproduced"]
    cd.assert_no_calculator()
    for key in ("F", "TS", "forces", "fermi", "mag", "ase"):
        assert q47.READS.get(key, 0) == 0, "a value other than geometry was read"
    lines = [HEADER, "Integrity: " + "; ".join(checks),
             "G2. Vector double difference: undoped leg V = VB76 - hostB76; doped leg D = Sr76o0_vac - Sr76o0_novac",
             "  Final geometries"] + fmt_rows(rows_f) + ["  k = 0 geometries (the C1 A1 cells)"] + fmt_rows(rows_0) + \
            ["END: geometry only; no energy, force or gate value read; no calculator loaded"]
    return lines


# ---- self-test ----------------------------------------------------------------------------------------------------

def self_test():
    from ase.io import read as aread
    pdr, cd, fig, q47, c46 = tools()
    rng = np.random.default_rng(11)
    # quaternion: exact recovery, relative angles
    Pp = rng.normal(size=(5, 3))
    for deg in (0.0, 12.0, 30.0, 120.0, 179.0):
        ax = rng.normal(size=3)
        Q = cd._rotate_about(Pp, Pp.mean(axis=0), ax, deg)
        R = horn_R(Pp, Q)
        assert abs(angle_deg(R) - deg) < 1e-6 and abs(angle_deg(R) - cd.quat_angle_deg(Pp, Q)) < 1e-6, "Horn angle"
        assert np.allclose((Pp - Pp.mean(0)) @ R.T, Q - Q.mean(0), atol=1e-9), "Horn rotation"
    R1 = horn_R(Pp, cd._rotate_about(Pp, Pp.mean(0), (0, 0, 1), 30.0))
    R2 = horn_R(Pp, cd._rotate_about(Pp, Pp.mean(0), (1, 0, 0), 30.0))
    assert angle_deg(R1 @ R1.T) < 1e-6 and angle_deg(R2 @ R1.T) > 1.0, "relative angles"
    # synthetic legs from the public reference cell
    h = aread(os.path.join(REPO, "results", "fa_host", "fa19cs1_pb20i60_233.extxyz")); h.calc = None
    s = np.array(h.get_chemical_symbols())
    cell = h.cell.array
    pb = [int(x) for x in np.flatnonzero(s == "Pb") if x > VI][0]          # the dopant site, after I127
    fa = [int(x) for x in np.flatnonzero(s == "C") if x > VI][-1]           # an FA after I127
    io = [int(x) for x in np.flatnonzero(s == "I") if x > VI + 5][0]        # an iodide after I127
    io_lo = [int(x) for x in np.flatnonzero(s == "I") if x < VI][0]         # an iodide before I127

    def cells_from(host):
        V = host.copy(); del V[VI]; V.calc = None
        D = host.copy(); D.calc = None; D.symbols[pb] = "Sr"
        DV = V.copy(); DV.calc = None; DV.symbols[h2v(pb)] = "Sr"
        return {"host": host.copy(), "V": V, "D": D, "DV": DV}
    ident = lambda n: {str(i): i for i in range(n)}
    legs = ({"old_to_new": ident(len(h)), "members": [pb]}, {"old_to_new": ident(len(h) - 1), "members": [h2v(pb)]})
    maps, members = make_maps(*legs)
    objs = [("FA", fa), ("I", io), ("I", io_lo), ("Pb", pb)]
    sk = _skeleton(cd, h, fa)
    u = np.array([0.0, 0.0, 0.2])
    # 1. zero double difference: the same displacement in both legs
    c = cells_from(h)
    c["V"].positions[h2v(io)] += u; c["DV"].positions[h2v(io)] += u
    rows = {(r["kind"], r["host"]): r for r in double_difference(cd, c, maps, members, objs, h)}
    r = rows[("I", io)]
    assert abs(r["dr_V"] - 0.2) < 1e-9 and abs(r["dr_D"] - 0.2) < 1e-9 and r["dd"] < 1e-9 and abs(r["cos"] - 1) < 1e-9
    assert rows[("I", io_lo)]["dr_V"] < 1e-9 and rows[("I", io_lo)]["cos"] is None, "unmoved object"
    # 2. a pure common translation of the FA in both legs: zero double difference, zero rotations
    c = cells_from(h)
    for k in ("V", "DV"):
        c[k].positions[[h2v(x) for x in sk]] += u
    r = {(x["kind"], x["host"]): x for x in double_difference(cd, c, maps, members, objs, h)}[("FA", fa)]
    assert r["dd"] < 1e-9 and r["rot_V"] < 1e-6 and r["rot_D"] < 1e-6 and r["rot_rel"] < 1e-6, "common translation"
    # 3. a 30-degree FA turn in one leg only
    c = cells_from(h)
    iv = [h2v(x) for x in sk]
    unwrapped = c["V"].positions[iv[0]] + cd.mic(c["V"].positions[iv] - c["V"].positions[iv[0]], cell)   # FA may span the boundary
    c["V"].positions[iv] = cd._rotate_about(unwrapped, unwrapped[0], (0.2, 0.4, 0.89), 30.0)
    r = {(x["kind"], x["host"]): x for x in double_difference(cd, c, maps, members, objs, h)}[("FA", fa)]
    assert abs(r["rot_V"] - 30) < 1e-6 and r["rot_D"] < 1e-6 and abs(r["rot_rel"] - 30) < 1e-6, "one-leg turn"
    assert abs(r["rot_V_min"] - 30) < 1e-6, "minimising labelling"
    # the same 30-degree turn in both legs: zero relative rotation
    for k in ("DV",):
        ub = c[k].positions[iv[0]] + cd.mic(c[k].positions[iv] - c[k].positions[iv[0]], cell)
        c[k].positions[iv] = cd._rotate_about(ub, ub[0], (0.2, 0.4, 0.89), 30.0)
    r = {(x["kind"], x["host"]): x for x in double_difference(cd, c, maps, members, objs, h)}[("FA", fa)]
    assert abs(r["rot_D"] - 30) < 1e-6 and r["rot_rel"] < 1e-6, "equal turns in both legs"
    # 4. index after I127 and 5. displacement across the periodic boundary
    c = cells_from(h)
    c["V"].positions[h2v(io)] += cell[0] + np.array([0.05, 0.0, 0.0])
    r = {(x["kind"], x["host"]): x for x in double_difference(cd, c, maps, members, objs, h)}[("I", io)]
    assert abs(r["dr_V"] - 0.05) < 1e-9 and abs(r["dd"] - 0.05) < 1e-9, "after I127 / periodic image"
    try:
        h2v(VI); raise AssertionError("I127 not refused")
    except ValueError:
        pass
    # 6. the Pb-to-dopant member is exempt; any other element change is refused
    r = {(x["kind"], x["host"]): x for x in double_difference(cd, cells_from(h), maps, members, objs, h)}[("Pb", pb)]
    assert r["dopant_site"] and r["dd"] < 1e-9, "dopant member"
    c = cells_from(h); c["D"].symbols[io] = "Br"
    try:
        double_difference(cd, c, maps, members, objs, h); raise AssertionError("element mismatch not refused")
    except ValueError:
        pass
    # 7. a non-identity leg map: the doped cells reordered (dopant moved to the end); results unchanged
    c = cells_from(h)
    c["V"].positions[h2v(io)] += u
    base = double_difference(cd, c, maps, members, objs, h)
    perm_d = [i for i in range(len(h)) if i != pb] + [pb]
    perm_dv = [i for i in range(len(h) - 1) if i != h2v(pb)] + [h2v(pb)]
    c2 = dict(c); c2["D"] = c["D"][perm_d]; c2["DV"] = c["DV"][perm_dv]
    c2["D"].calc = c2["DV"].calc = None
    o_d = {str(old): new for new, old in enumerate(perm_d)}
    o_dv = {str(old): new for new, old in enumerate(perm_dv)}
    maps2, members2 = make_maps({"old_to_new": o_d, "members": [len(h) - 1]},
                                {"old_to_new": o_dv, "members": [len(h) - 2]})
    other = double_difference(cd, c2, maps2, members2, objs, h)
    for a, b in zip(base, other):
        assert all(abs(a[k] - b[k]) < 1e-9 for k in ("dr_V", "dr_D", "dd")), "non-identity map"
    # fixed-atom agreement
    region_free = [fa, io, io_lo, pb] + sk + [VI]
    ok, worst = fixed_agree(cells_from(h), maps, region_free, len(h))
    assert ok and worst == 0.0
    c = cells_from(h); j_fixed = [j for j in range(len(h)) if j not in region_free][0]
    c["DV"].positions[maps["DV"](j_fixed)] += 1e-5
    assert not fixed_agree(c, maps, region_free, len(h))[0], "fixed-atom disagreement not caught"
    cd.assert_no_calculator()
    print("G2 self-test passed: Horn rotations (5 angles, relative angles), zero double difference, common translation, "
          "a 30-degree turn in one leg, an index after I127 across the periodic boundary, I127 refused, the dopant "
          "member exempt and an element change refused, a non-identity leg map, fixed-atom agreement; no C2 file read")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--read", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
    elif a.read:
        dirty = subprocess.run(["git", "-C", REPO, "status", "--porcelain", "--", HERE], capture_output=True,
                               text=True).stdout.strip()
        if dirty:
            sys.exit("refused: c2_diagnostic/ has uncommitted changes (S2B_PLAN §6)")
        if os.path.exists(OUT):
            sys.exit("refused: g2_output.txt exists; G2 runs once (S2B_PLAN §6)")
        head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        sha = lambda f: hashlib.sha256(open(os.path.join(HERE, f), "rb").read()).hexdigest()[:12]
        try:
            lines = read()
        except SystemExit:
            raise
        except Exception as e:                                   # print only the stage and the exception type
            sys.exit(f"G2 failed before output: {type(e).__name__}")
        lines = [f"G2 read at {head}; tools sha256 g2_square {sha('g2_square.py')}, part_d_read {sha('part_d_read.py')}, "
                 f"check5_diag {sha('check5_diag.py')}"] + lines
        with open(OUT, "w") as fh:
            fh.write("\n".join(lines) + "\n")
        print("\n".join(lines))
    else:
        ap.print_help()

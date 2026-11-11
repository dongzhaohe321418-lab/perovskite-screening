#!/usr/bin/env python
"""Part-d tools of S2_PLAN.md amendment 2026-11-11a: a geometry-only diagnostic of the section-11 check 5.

Check 5 (S2_PLAN.md section 5, item 5): in a child-parent pair, every free child atom more than 6.0 A from the defect
added in that step (its relaxed-host position; an FA by its carbon) must stay near its parent position: inorganic
|dr| < 0.25 A; FA carbon |dr| < 0.25 A and Kabsch rotation of the C-N-N skeleton < 20 deg.

  D5   an independent recomputation. It uses none of the map, molecule, minimum-image or Kabsch functions of
       scripts/38, 46 or 50: the index maps of section 4 are written out here, the minimum image is a search over
       lattice translations, FA are found by a C-N distance cut, and the rotation angle comes from Horn's quaternion
       method instead of an SVD. It also reports the rotation with the two nitrogens exchanged (amendment, part e
       item 2: a permutation of identical atoms is the same configuration; reported only for C2 cells).
  R46  a copy of scripts/46 check_partner (commit 8bff03e) that also returns its per-object lists; its self-test
       asserts that its summary equals check_partner's.

Geometry only. No energy, force or gate value is read; no calculator is loaded (asserted); structures must carry no
calculator. The self-test uses the public reference cell results/fa_host/fa19cs1_pb20i60_233.extxyz only and a closed
list of cases whose expected results follow from section 5 by construction. No C2 file is read by the self-test.

    python check5_diag.py --self-test
"""
import argparse, importlib.util, json, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
SCRIPTS = os.path.join(ROOT, "scripts")
CUT_A, DR_A, ROT_DEG = 6.0, 0.25, 20.0            # section 5, item 5 (written out, not imported)
VI = 127                                          # section 4: the vacancy iodide of every member
ORGANIC = ("C", "N", "H")
CALC_ENGINES = ("mace", "torch", "e3nn", "ase.calculators.espresso", "ase.calculators.emt", "ase.calculators.lj")


def assert_no_calculator(*atoms):
    loaded = [m for m in CALC_ENGINES if m in sys.modules]
    assert not loaded, f"a calculator module is loaded: {loaded}"
    for a in atoms:
        assert a.calc is None, "a structure carries a calculator"


# ---- D5: independent implementation --------------------------------------------------------------------------------

def mic(v, cell):
    """Minimum-image vectors by search over lattice translations n in {-2..2}^3 after wrapping to [-0.5, 0.5)."""
    v = np.atleast_2d(np.asarray(v, float))
    A = np.asarray(cell, float)
    f = v @ np.linalg.inv(A)
    f -= np.round(f)
    base = f @ A
    n = np.array([(a, b, c) for a in range(-2, 3) for b in range(-2, 3) for c in range(-2, 3)], float) @ A
    cand = base[:, None, :] + n[None, :, :]
    k = np.argmin(np.einsum("ijk,ijk->ij", cand, cand), axis=1)
    return cand[np.arange(len(v)), k]


def quat_angle_deg(P, Q):
    """Rotation angle of the best proper rotation taking the centred set P onto the centred set Q (Horn 1987)."""
    P = np.asarray(P, float) - np.mean(P, axis=0)
    Q = np.asarray(Q, float) - np.mean(Q, axis=0)
    S = P.T @ Q
    xx, xy, xz, yx, yy, yz, zx, zy, zz = S.ravel()
    N = np.array([[xx + yy + zz, yz - zy, zx - xz, xy - yx],
                  [yz - zy, xx - yy - zz, xy + yx, zx + xz],
                  [zx - xz, xy + yx, -xx + yy - zz, yz + zy],
                  [xy - yx, zx + xz, yz + zy, -xx - yy + zz]])
    w, V = np.linalg.eigh(N)
    q = V[:, np.argmax(w)]
    return float(np.degrees(2.0 * np.arccos(np.clip(abs(q[0]), 0.0, 1.0))))


def maps_section4(kind, n_host, leg=None, vi=VI):
    """(child -> host, child -> parent) from section 4: V drops the host index vi and shifts later indices down by
    one; D maps through the host leg's old_to_new; D+V through the V leg's old_to_new and then V -> host."""
    v2h = lambda jv: jv if jv < vi else jv + 1
    if kind == "V":
        m = {jv: v2h(jv) for jv in range(n_host - 1)}
        return m, m
    inv = {int(new): int(old) for old, new in leg["old_to_new"].items()}
    if kind == "D":
        return inv, inv
    if kind == "DV":
        return {c: v2h(o) for c, o in inv.items()}, inv
    raise ValueError(kind)


def free_section4(kind, region_free, leg=None, vi=VI):
    """The region's free set in the child's numbering (section 4, 'Transfer')."""
    F = [int(i) for i in region_free]
    h2v = lambda j: j if j < vi else j - 1
    if kind == "V":
        return sorted(h2v(j) for j in F if j != vi)
    o2n = {int(k): int(x) for k, x in leg["old_to_new"].items()}
    src = F if kind == "D" else [h2v(j) for j in F if j != vi]
    return sorted({o2n[i] for i in src if i in o2n} | {int(m) for m in leg["members"]})


def d5_check(kind, child, parent, host, region, leg=None, vi=VI):
    """Check 5 recomputed independently. Returns per-object rows and the pass/fail of check 5 as written and under
    the exchange of the two FA nitrogens."""
    assert_no_calculator(child, parent, host)
    cell = child.cell.array
    cs, ps = np.array(child.get_chemical_symbols()), np.array(parent.get_chemical_symbols())
    c2h, c2p = maps_section4(kind, len(host), leg, vi)
    p2c = {p: c for c, p in c2p.items()}
    free = set(free_section4(kind, region["free"], leg, vi))
    members = set() if leg is None else {int(m) for m in leg["members"]}   # dopant atoms: their element differs by design
    centre = np.asarray(region["centres"]["v" if kind == "V" else "site"], float)
    dist_host = lambda i: float(np.linalg.norm(mic(host.positions[c2h[i]] - centre, cell)[0]))
    rows = []
    for i in sorted(free):
        if i not in c2p or cs[i] in ORGANIC:
            continue
        if cs[i] != ps[c2p[i]] and i not in members:
            raise ValueError(f"element mismatch: child {i} {cs[i]} against parent {c2p[i]} {ps[c2p[i]]}")
        dh = dist_host(i)
        dr = float(np.linalg.norm(mic(child.positions[i] - parent.positions[c2p[i]], cell)[0]))
        rows.append({"kind": "inorganic", "element": str(cs[i]), "child": i, "parent": c2p[i], "host": c2h[i],
                     "d_host_A": dh, "gated": dh > CUT_A, "dr_A": dr})
    Ns = np.flatnonzero(ps == "N")
    for cp in np.flatnonzero(ps == "C"):
        dN = np.linalg.norm(mic(parent.positions[Ns] - parent.positions[cp], cell), axis=1)
        ns = [int(x) for x in Ns[dN < 1.6]]
        if len(ns) != 2:
            continue
        sk = [int(cp)] + ns
        if any(x not in p2c for x in sk) or p2c[int(cp)] not in free:
            continue
        cc = [p2c[x] for x in sk]
        for a, b in zip(sk, cc):
            if ps[a] != cs[b]:
                raise ValueError(f"element mismatch in FA skeleton: parent {a} {ps[a]} against child {b} {cs[b]}")
        rel = lambda at, idx: np.vstack([np.zeros(3), mic(at.positions[idx[1:]] - at.positions[idx[0]], cell)])
        Pp, Qc = rel(parent, sk), rel(child, cc)
        rot = quat_angle_deg(Pp, Qc)
        rot_x = quat_angle_deg(Pp, Qc[[0, 2, 1]])
        dh = dist_host(cc[0])
        dr = float(np.linalg.norm(mic(child.positions[cc[0]] - parent.positions[sk[0]], cell)[0]))
        rows.append({"kind": "FA", "child": cc[0], "parent": sk[0], "host": c2h[cc[0]], "d_host_A": dh,
                     "gated": dh > CUT_A, "dr_A": dr, "rot_deg": rot, "rot_exchanged_deg": rot_x})

    def ok(r, exch):
        if not r["gated"]:
            return True
        if r["kind"] == "inorganic":
            return r["dr_A"] < DR_A
        return r["dr_A"] < DR_A and min(r["rot_deg"], r["rot_exchanged_deg"] if exch else r["rot_deg"]) < ROT_DEG
    for r in rows:
        r["pass"], r["pass_exchanged"] = ok(r, False), ok(r, True)
    return {"passed": all(r["pass"] for r in rows), "passed_exchanged": all(r["pass_exchanged"] for r in rows),
            "rows": rows}


# ---- R46: scripts/46 check_partner with its per-object lists (copy of 8bff03e lines 1400-1443) ----------------------

def load_c46():
    spec = importlib.util.spec_from_file_location("c46", os.path.join(SCRIPTS, "46_s2_cells.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def r46_check(c46, child, parent, child_to_parent, *, host_relaxed, child_to_host, centre_host, free_child):
    a38, mic_norm, dist_to = c46.a38, c46.mic_norm, c46.dist_to
    cell = child.cell.array
    cs, ps = c46._syms(child), c46._syms(parent)
    free = set(int(i) for i in free_child)
    p2c = {int(p): int(c) for c, p in child_to_parent.items()}
    dh = dist_to(host_relaxed, centre_host)
    acc = {"gated": {"inorganic": [], "fa": []}, "within_6A_reported": {"inorganic": [], "fa": []}}
    for i in sorted(free):
        if i not in child_to_parent or cs[i] in c46.ORGANIC:
            continue
        d_h = float(dh[child_to_host[i]])
        dr = mic_norm(child.positions[i] - parent.positions[child_to_parent[i]], cell)
        acc["gated" if d_h > c46.PARTNER_CUT_A else "within_6A_reported"]["inorganic"].append(
            {"index": i, "d_host_A": d_h, "dr_A": dr})
    for cp in np.flatnonzero(ps == "C"):
        mol, ns = a38.molecule(parent, int(cp), ps, cell)
        if len(ns) != 2:
            continue
        sk = [int(cp)] + [int(x) for x in ns]
        if any(x not in p2c for x in sk) or p2c[int(cp)] not in free:
            continue
        cc = [p2c[x] for x in sk]
        d_h = float(dh[child_to_host[cc[0]]])
        dr = mic_norm(child.positions[cc[0]] - parent.positions[sk[0]], cell)
        rot = a38.kabsch_deg(c46._rel_skeleton(parent.positions, sk, cell), c46._rel_skeleton(child.positions, cc, cell))
        acc["gated" if d_h > c46.PARTNER_CUT_A else "within_6A_reported"]["fa"].append(
            {"carbon": cc[0], "d_host_A": d_h, "dr_carbon_A": dr, "rot_deg": rot})

    def summary(g):
        mi = max(g["inorganic"], key=lambda r: r["dr_A"], default=None)
        mc = max(g["fa"], key=lambda r: r["dr_carbon_A"], default=None)
        mr = max(g["fa"], key=lambda r: r["rot_deg"], default=None)
        return {"n_inorganic": len(g["inorganic"]), "n_fa": len(g["fa"]),
                "max_dr_inorganic_A": None if mi is None else mi["dr_A"],
                "max_dr_fa_carbon_A": None if mc is None else mc["dr_carbon_A"],
                "max_rot_fa_deg": None if mr is None else mr["rot_deg"],
                "worst": {"inorganic": mi, "fa_carbon": mc, "fa_rotation": mr}}
    g = summary(acc["gated"])
    ok = (all(r["dr_A"] < c46.PARTNER_DR_A for r in acc["gated"]["inorganic"])
          and all(r["dr_carbon_A"] < c46.PARTNER_DR_A and r["rot_deg"] < c46.PARTNER_ROT_DEG for r in acc["gated"]["fa"]))
    return {"passed": bool(ok), "gated": g, "within_6A_reported": summary(acc["within_6A_reported"]), "lists": acc}


def r46_for(c46, kind, child, parent, host, region, leg=None):
    free = c46.free_in_cell(region, kind, built=leg)
    c2h, c2p = c46.cell_maps(kind, built=leg, n_host=len(host))
    centre = np.array(region["centres"]["v" if kind == "V" else "site"], float)
    kw = dict(host_relaxed=host, child_to_host=c2h, centre_host=centre, free_child=free)
    return r46_check(c46, child, parent, c2p, **kw), c46.check_partner(child, parent, c2p, **kw)


# ---- G: positions reader of raw A2 outputs --------------------------------------------------------------------------

def load_fig():
    """The C2 figure module (D-C2-12): its guarded reader and the scripts/47 object whose READS it counts."""
    spec = importlib.util.spec_from_file_location("fig_s2_c2_a2", os.path.join(HERE, "..", "figures", "fig_s2_c2_a2.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def g_positions(q47, parts, *, mapping, ranks=None, label=None):
    """{k: (symbols, positions A)} of every configuration of one A2 relaxation. k, the part boundaries, the restart
    mapping and the k = 200 cut come from scripts/47 parse_relax(read='counts') (markers only); the positions of each
    counted configuration are read by scripts/47's own rule (_positions: the last ATOMIC_POSITIONS block, or the
    header block at k = 0). No energy or force is read (asserted on the READS counter)."""
    f0, r0 = q47.READS["F"], q47.READS["forces"]
    pr = q47.parse_relax(parts, read="counts", mapping=mapping, ranks=ranks, label=label)
    if not pr["usable"]:
        raise ValueError(f"unusable relaxation: {pr['unusable_reason']}")
    rep = bool(mapping.get("restart_repeats_last", False))
    out, k_last = {}, None
    for p, path in enumerate(parts):
        if p >= len(pr["parts"]):
            break
        txt = q47.a32.read_text(path)
        hdr = q47._header(txt)
        cfg, _ = q47._segment(txt, hdr["nat"])
        kept = []
        for i, c in enumerate(cfg):
            k = i if p == 0 else (k_last + i if rep else k_last + 1 + i)
            kept.append((k, c))
            if k >= pr["k_cap"] or c["converged"]:
                break
        if p > 0 and rep and kept:
            kept = kept[1:]
        for k, c in kept:
            sym, pos, _ = q47._positions(txt, *c["window"], hdr)
            out[k] = (list(sym), np.asarray(pos, float))
        if kept:
            k_last = kept[-1][0]
    assert sorted(out) == list(pr["ks"]) and len(out) == pr["n_config"], "G's configurations differ from scripts/47"
    assert q47.READS["F"] == f0 and q47.READS["forces"] == r0, "an energy or a force was read"
    return pr, out


# ---- self-test ------------------------------------------------------------------------------------------------------

def self_test_g():
    import gzip, tempfile
    fig = load_fig()
    g49, q47, _ = fig.modules()
    wp = fig._WP2e(q47)
    mapping = json.load(open(os.path.join(HERE, "..", "c1", "smoke.json")))["mapping"]
    ref = q47.parse_relax  # positions of the last configuration by scripts/47's own final_geom read, for comparison
    tmp = tempfile.mkdtemp(prefix="check5_g_")
    n = 0
    for kind, last, splits in (("conv", 60, ()), ("conv", 120, (40, 90)), ("cap", None, (150,)), ("stopped", 75, (30,))):
        texts = wp.parts("s2r_m30_test", kind, last, splits)
        paths = []
        for i, t in enumerate(texts):
            p = os.path.join(tmp, f"s2r_m30_test.p{i + 1}.out.gz")
            with gzip.open(p, "wt") as fh:
                fh.write(t)
            paths.append(p)
        pr, pos = g_positions(q47, paths, mapping=mapping, ranks=64, label="s2r_m30_test")
        fg = ref(paths, read="final_geom", mapping=mapping, ranks=64, label="s2r_m30_test")
        kl = max(pos)
        assert np.abs(pos[kl][1] - fg["positions_A"][kl]).max() == 0.0, f"{kind}: last configuration differs"
        if kind == "cap":
            assert kl == 200 and pr["cap_reached"], "cap: k = 200 cut"
        if splits:                                    # the first configuration of a restart part continues k
            assert splits[0] in pos and splits[0] - 1 in pos
        assert pos[0][1].shape == (234, 3)
        n += 1
    assert q47.READS["F"] == 0 and q47.READS["forces"] == 0, "the G self-test read an energy or a force"
    print(f"G self-test passed: {n} synthetic relaxations from the public WP2e output (single part, two restarts, "
          f"k = 200 cut, stopped part); last configurations equal scripts/47 final_geom; no energy or force read")

def _rotate_about(P, centre, axis, deg):
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    t = np.radians(deg)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    R = np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * (K @ K)
    return (P - centre) @ R.T + centre


def self_test():
    from ase.io import read
    c46 = load_c46()
    # the section 4 maps at the I127 boundary, by hand: V drops host 127; host 128 is V 127; host 232 is V 231
    c2h, c2p = maps_section4("V", 233)
    assert (c2h[126], c2h[127], c2h[231]) == (126, 128, 232) and c2p == c2h and len(c2h) == 232, "V map"
    assert free_section4("V", [126, 127, 128, 232]) == [126, 127, 231], "V free set"
    lg = {"old_to_new": {"5": 7, "128": 3}, "members": [9]}
    assert maps_section4("D", 233, lg) == ({7: 5, 3: 128}, {7: 5, 3: 128}), "D map"
    assert maps_section4("DV", 233, lg) == ({7: 5, 3: 129}, {7: 5, 3: 128}), "D+V map (V 128 is host 129)"
    assert free_section4("D", [5, 128, 40], lg) == [3, 7, 9] and free_section4("DV", [5, 127, 129], lg) == [3, 7, 9]
    host = read(os.path.join(ROOT, "results", "fa_host", "fa19cs1_pb20i60_233.extxyz"))
    host.calc = None
    reg = c46.build_region(host, "ref233", 136)
    syms = np.array(host.get_chemical_symbols())
    child0 = host.copy(); del child0[VI]; child0.calc = None             # V+ cell: I127 removed
    cell = host.cell.array
    v = np.array(reg["centres"]["v"], float)
    dv = lambda j, c=v: float(np.linalg.norm(mic(host.positions[j] - c, cell)[0]))
    h2v = lambda j: j if j < VI else j - 1
    F = [int(i) for i in reg["free"]]
    inorg = [j for j in F if syms[j] not in ORGANIC and j != VI]
    gated_in = [j for j in inorg if dv(j) > CUT_A + 0.3]
    after = [j for j in gated_in if j > VI]
    fa_c = []
    for c in F:
        if syms[c] == "C":
            dN = np.linalg.norm(mic(host.positions[np.flatnonzero(syms == "N")] - host.positions[c], cell), axis=1)
            if (dN < 1.6).sum() == 2 and dv(c) > CUT_A + 0.3:
                fa_c.append(c)
    assert gated_in and fa_c and after, "the reference region lacks a gated inorganic atom or FA"
    j_in, j_after, c_fa = gated_in[0], after[0], fa_c[0]
    mol = lambda c: [int(x) for x in c46.a38.molecule(host, c, syms, cell)[0]]
    nsk = lambda c: [int(x) for x in c46.a38.molecule(host, c, syms, cell)[1]]
    cases, n = [], 0

    def run(name, child, expect, expect_x=None, region=reg, kind="V", parent=host, leg=None):
        nonlocal n
        d5 = d5_check(kind, child, parent, host, region, leg)
        r46, c46r = r46_for(c46, kind, child, parent, host, region, leg)
        assert d5["passed"] is expect, f"{name}: D5 passed={d5['passed']}, expected {expect}"
        if expect_x is not None:
            assert d5["passed_exchanged"] is expect_x, f"{name}: D5 exchanged={d5['passed_exchanged']}"
        assert r46["passed"] == c46r["passed"] and r46["gated"] == c46r["gated"] and \
            r46["within_6A_reported"] == c46r["within_6A_reported"], f"{name}: R46 summary differs from check_partner"
        cases.append((name, d5["passed"], c46r["passed"]))
        n += 1
        return d5

    def moved(j_host, vec):
        c = child0.copy(); c.calc = None
        c.positions[h2v(j_host)] += vec
        return c
    u = np.array([1.0, 0.0, 0.0])
    d = run("unperturbed", child0, True, True)
    assert max(r["dr_A"] for r in d["rows"]) < 1e-9, "unperturbed: a nonzero displacement (index map error)"
    run("inorganic 0.249 A", moved(j_in, 0.249 * u), True)
    run("inorganic 0.251 A", moved(j_in, 0.251 * u), False)
    r = run("index after I127, 0.30 A", moved(j_after, 0.30 * u), False)
    bad = [x for x in r["rows"] if not x["pass"]]
    assert len(bad) == 1 and bad[0]["child"] == j_after - 1 and bad[0]["host"] == j_after, "index after I127"
    run("periodic image + 0.10 A", moved(j_in, cell[0] + 0.10 * u), True)
    run("periodic image + 0.30 A", moved(j_in, cell[1] + 0.30 * u), False)
    # FA rotation about its carbon (rigid, carbon fixed)
    def rotated(c, deg, axis=(0.3, 0.5, 0.81)):
        ch = child0.copy(); ch.calc = None
        idx = [h2v(x) for x in mol(c)]
        ch.positions[idx] = _rotate_about(ch.positions[idx], ch.positions[h2v(c)], axis, deg)
        return ch
    d = run("FA rotation 19.9 deg", rotated(c_fa, 19.9), True)
    fa = next(x for x in d["rows"] if x["kind"] == "FA" and x["host"] == c_fa)
    assert abs(fa["rot_deg"] - 19.9) < 1e-6, f"rotation read {fa['rot_deg']}"
    run("FA rotation 20.1 deg", rotated(c_fa, 20.1), False)
    # exchanged nitrogens (with their hydrogens): a 180-degree turn under labels, the same configuration
    ch = child0.copy(); ch.calc = None
    n1, n2 = nsk(c_fa)
    hs = lambda nn: [x for x in mol(c_fa) if syms[x] == "H" and np.linalg.norm(mic(host.positions[x] - host.positions[nn], cell)[0]) < 1.25]
    a_ = [n1] + hs(n1); b_ = [n2] + hs(n2)
    assert len(a_) == len(b_) == 3, "FA amino groups"
    pa, pb = ch.positions[[h2v(x) for x in a_]].copy(), ch.positions[[h2v(x) for x in b_]].copy()
    ch.positions[[h2v(x) for x in a_]], ch.positions[[h2v(x) for x in b_]] = pb, pa
    d = run("two exchanged nitrogens", ch, False, True)
    fa = next(x for x in d["rows"] if x["kind"] == "FA" and x["host"] == c_fa)
    assert fa["rot_exchanged_deg"] < 1e-6 and fa["rot_deg"] > 90, "exchange reading"
    # distances 5.99 / 6.01: a synthetic centre placed at that distance from the moved atom
    def centred(j, dist):
        r_ = {**reg, "centres": {**reg["centres"], "v": list(host.positions[j] + dist * np.array([0.0, 0.0, 1.0]))}}
        return r_
    run("inorganic at 5.99 A, 0.30 A", moved(j_in, 0.30 * u), True, region=centred(j_in, 5.99))
    run("inorganic at 6.01 A, 0.30 A", moved(j_in, 0.30 * u), False, region=centred(j_in, 6.01))
    # an FA whose carbon lies inside 6.0 A and whose nitrogens lie outside: gated by its carbon
    mid = host.positions[nsk(c_fa)].mean(axis=0)
    w = host.positions[c_fa] - mid; w /= np.linalg.norm(w)
    for dist, exp in ((5.99, True), (6.01, False)):
        r_ = {**reg, "centres": {**reg["centres"], "v": list(host.positions[c_fa] + dist * w)}}
        nd = [float(np.linalg.norm(mic(host.positions[x] - np.array(r_["centres"]["v"]), cell)[0])) for x in nsk(c_fa)]
        assert min(nd) > CUT_A, "nitrogens not outside 6.0 A"
        run(f"FA carbon at {dist} A, nitrogens outside, 30 deg", rotated(c_fa, 30.0), exp, region=r_)
    # an appended dopant atom (D cell): no parent image, skipped
    leg = {"old_to_new": {str(i): i for i in range(len(host))}, "members": [136, len(host)]}
    dch = host.copy(); dch.calc = None
    dch.symbols[136] = "Sr"
    dch.append("H"); dch.positions[-1] = host.positions[136] + np.array([0.0, 0.0, 1.5])
    run("appended dopant atom (D)", dch, True, kind="D", leg=leg)
    dch2 = dch.copy(); dch2.calc = None; dch2.positions[-1] += np.array([0.0, 0.0, 3.0])
    run("appended dopant atom moved 3 A (D)", dch2, True, kind="D", leg=leg)
    # a D+V cell against its V+ parent: the V leg maps V indices; gated about the site; the parent is the V+ final
    s_v = h2v(136)
    legv = {"old_to_new": {str(i): i for i in range(len(child0))}, "members": [s_v]}
    dvc = child0.copy(); dvc.calc = None; dvc.symbols[s_v] = "Sr"
    run("D+V unperturbed", dvc, True, kind="DV", parent=child0, leg=legv)
    site = np.array(reg["centres"]["site"], float)
    far_site = sorted((j for j in inorg if dv(j, site) > CUT_A + 0.3), key=lambda j: -j)   # after I127 if any
    assert far_site, "no free inorganic atom beyond 6.3 A of the site"
    dvm = dvc.copy(); dvm.calc = None; dvm.positions[h2v(far_site[0])] += 0.30 * u
    r = run("D+V gated atom moved 0.30 A", dvm, False, kind="DV", parent=child0, leg=legv)
    bad = [x for x in r["rows"] if not x["pass"]]
    assert len(bad) == 1 and bad[0]["host"] == far_site[0] and bad[0]["parent"] == h2v(far_site[0]), "D+V maps"
    # an element mismatch is refused by D5
    mm = child0.copy(); mm.calc = None; mm.symbols[h2v(j_in)] = "Br"
    try:
        d5_check("V", mm, host, host, reg)
        raise AssertionError("element mismatch not refused")
    except ValueError:
        pass
    # the angle routine against an independent construction: a rigid rotation of a random set
    rng = np.random.default_rng(7)
    P = rng.normal(size=(5, 3))
    for deg in (0.0, 5.0, 19.9, 20.1, 90.0, 179.0):
        Q = _rotate_about(P, P.mean(axis=0), rng.normal(size=3), deg) + rng.normal(size=3)
        assert abs(quat_angle_deg(P, Q) - deg) < 1e-6, deg
    assert_no_calculator()
    print(f"self-test passed: {n} geometry cases (D5 against expectations, R46 against check_partner), the element "
          f"refusal and 6 angle cases; D5 and check_partner agree on {sum(a == b for _, a, b in cases)} of {len(cases)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        self_test_g()
        assert_no_calculator()

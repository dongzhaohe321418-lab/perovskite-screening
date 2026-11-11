#!/usr/bin/env python
"""Batch driver of the part-d read (S2_PLAN.md amendment 2026-11-11a, part d): items 1-5 over the C2 archive.

It runs the tools of check5_diag.py (D5, R46, G) on the archived C2 final geometries and raw A2 outputs and prints the
five items of part d, and nothing else:
  1  Integrity, for each of the eight C2 records: validity_final.valid, failed, parent, parent_final; the sha256 of each
     final geometry and validity file against the record; the geometry hashes of the validity record (start, final,
     parent final, relaxed host) against the files this driver loads; each final geometry against G's last
     configuration (1e-6 A). A mismatch is printed and ends the read.
  2  Agreement: pass or fail of check 5 for the six C2 pairs under the record, D5 and R46.
  3  Per-object table (D5 rows) for every far pair and for any pair on which the readings disagree; for such a pair also
     the R46 lists. Each gated object: kind, child and host index, relaxed-host distance from the step's defect
     (0.01 A), |dr| (0.001 A), FA rotation with and without the nitrogen exchange (0.1 deg), pass or fail as written
     and under the permutation-invariant reading (part e, item 2).
  4  Which cell moved: for each object failing under D5 or R46, |dr| and FA rotation of the child final and of the
     parent final against the reference, and between the two cells' k = 0 geometries. The reference is the S2-relaxed
     MACE host for the V and D children, and the A1 V+_R geometry of the same site for the D+V child (part d, item 4).
  5  Trajectory: for each far pair, the gated inorganic atom of largest |dr| and the gated FA of largest rotation (D5,
     as written), at every configuration of both cells read by G, against the item-4 reference.

Fixed before the read (this commit): the reference of items 4 and 5 is the parent's own numbering (host_R for V and D
children, V+_R for D+V children); an FA skeleton is its carbon and the two nitrogens within 1.6 A of it in the parent
final geometry, as in D5; the cell of every configuration is the cell of the final geometry (fixed-cell relaxation);
"largest" in item 5 is over the gated objects of D5 as written.

Blinding (OPS2 D-C2-10, D-C2-12; amendment part d). A2 records and validity records are read through the field guard
of figures/fig_s2_c2_a2.py; C1 records through the blinded loader of scripts/46; raw A2 outputs only through G, which
reads positions and asserts that no energy or force was read. No gate file is opened. No calculator is loaded
(asserted). Nothing is written: structures are read from the archives' tar files in memory.

    python part_d_read.py --self-test     # synthetic cases and the public C1 archive only; no C2 file is read
    python part_d_read.py --read          # the one read of part d
"""
import argparse, hashlib, importlib.util, io, json, os, subprocess, sys, tarfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
S2 = os.path.normpath(os.path.join(HERE, ".."))
REPO = os.path.normpath(os.path.join(S2, "..", "..", ".."))
P = "s2r_m30_"
LABELS = [P + x for x in ("VB136", "hostB136", "Sr136o0_novac", "Sr136o0_vac",
                          "hostB76", "VB76", "Sr76o0_novac", "Sr76o0_vac")]           # C2 order (OPS2 section 1)
PAIRS = [(P + c, P + p) for c, p in (("VB136", "hostB136"), ("Sr136o0_novac", "hostB136"), ("Sr136o0_vac", "VB136"),
                                     ("VB76", "hostB76"), ("Sr76o0_novac", "hostB76"), ("Sr76o0_vac", "VB76"))]
FAR = PAIRS[3:]
TOL_G_A = 1e-6                                     # part d, item 1


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def tools():
    cd = _load("check5_diag", os.path.join(HERE, "check5_diag.py"))
    fig = cd.load_fig()
    g49, q47, c46 = fig.modules()
    return cd, fig, q47, c46


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def atoms_from_bytes(b):
    from ase.io import read
    at = read(io.StringIO(b.decode()), format="extxyz")
    at.calc = None
    at.set_constraint()
    return at


def leaf(g, *keys):
    """A leaf of a guarded record, by name."""
    for k in keys:
        g = g.get(k)
    return g


class Archive:
    """The archive root results/objective2/s2: C1 records (blinded loader), C1 and C2 structures (tar, in memory), C2
    A2 and validity records (field guard), C2 raw parts (paths only, for G)."""

    def __init__(self, root, cd, fig, c46, *, c2=True):
        self.root, self.cd, self.fig, self.c46 = root, cd, fig, c46
        self.L = c46.Layout(kind="archive", root=root)
        self.t1 = tarfile.open(os.path.join(root, "c1", "structures.tar.gz"))
        self.t2 = tarfile.open(os.path.join(root, "c2", "structures.tar.gz")) if c2 else None
        self.mapping = json.load(open(os.path.join(root, "c1", "smoke.json")))["mapping"]
        if c2:
            jobs = json.load(open(os.path.join(root, "c2", "graph.json")))["jobs"]
            self.job = {j["label"]: j for j in jobs if j.get("kind") == "a2v"}
            assert sorted(self.job) == sorted(LABELS), "the C2 graph does not hold the eight a2v jobs"

    def _member(self, tf, name):
        return tf.extractfile(tf.getmember(name)).read()

    def c1_cell(self, work_id, which):
        return atoms_from_bytes(self._member(self.t1, f"cells/{work_id}/{which}.extxyz"))

    def final_bytes(self, label):
        return self._member(self.t2, f"a2/{label}/{label}.final.extxyz")

    def a2(self, label):
        return self.fig.guarded(os.path.join(self.root, "c2", "raw", f"{label}.a2.json"))

    def validity_path(self, label):
        return os.path.join(self.root, "c2", "raw", f"{label}.validity_final.json")

    def inputs(self, label):
        """The inputs of the runner's validate-a2 job (scripts/50 a2v_files), from the archive."""
        j = self.job[label]
        h = j["member"]
        region = self.c46.check_region_record(self.c46.load_record(self.L.region("c1", h, j["L"], j["j"])))
        host = self.c1_cell(f"s2_{h}_host", "relaxed")
        assert region["host_source"]["sha256"] == self.c46.sha256_atoms(host), f"{label}: region and host differ"
        leg = None
        if j["cell_kind"] in ("D", "DV"):
            pr = self.c46.load_record(self.L.pair("c1", h, j["token"], j["j"], 0))
            assert pr.get("status") == "built" and pr.get("region_id") in (None, region["region_id"]), f"{label}: pair"
            leg = pr["legs"][j["leg"]]
        return {"kind": j["cell_kind"], "parent": j["parent"], "a1": j["a1"], "region": region, "host": host,
                "leg": leg, "start": self.c1_cell(j["a1"], "start")}


# ---- items 4 and 5: displacement and rotation of one object against a reference --------------------------------------

def fa_skeleton(cd, at, c):
    """[carbon, N, N] of the FA whose carbon is c in at: the two nitrogens within 1.6 A (as D5)."""
    s = np.array(at.get_chemical_symbols())
    Ns = np.flatnonzero(s == "N")
    d = np.linalg.norm(cd.mic(at.positions[Ns] - at.positions[c], at.cell.array), axis=1)
    ns = [int(x) for x in Ns[d < 1.6]]
    assert s[c] == "C" and len(ns) == 2, "not an FA carbon"
    return [int(c)] + ns


def measure(cd, pos, ref, idx_cell, idx_ref, cell):
    """|dr| of the first index and, for an FA skeleton (three indices), the rotation with and without the exchange of
    the nitrogens, of pos[idx_cell] against ref[idx_ref]."""
    dr = float(np.linalg.norm(cd.mic(pos[idx_cell[0]] - ref[idx_ref[0]], cell)[0]))
    if len(idx_cell) == 1:
        return dr, None, None
    rel = lambda x, ii: np.vstack([np.zeros(3), cd.mic(x[ii[1:]] - x[ii[0]], cell)])
    Pr, Qc = rel(ref, idx_ref), rel(pos, idx_cell)
    return dr, cd.quat_angle_deg(Pr, Qc), cd.quat_angle_deg(Pr, Qc[[0, 2, 1]])


def obj_indices(cd, obj, parent_final, c2p):
    """(indices in the child, indices in the parent/reference) of a D5 row."""
    if obj["kind"] == "inorganic":
        return [obj["child"]], [obj["parent"]]
    sk = fa_skeleton(cd, parent_final, obj["parent"])
    p2c = {p: c for c, p in c2p.items()}
    return [p2c[x] for x in sk], sk


def fmt(dr, rot, rotx):
    s = f"|dr| {dr:.3f} A"
    return s if rot is None else s + f", rot {rot:.1f} deg (exchanged {rotx:.1f})"


def check_integrity_positions(pos_g, at, tol=TOL_G_A):
    """True if G's configuration equals the final geometry (symbols, and positions within tol A)."""
    sym, x = pos_g
    return list(sym) == at.get_chemical_symbols() and x.shape == at.positions.shape and \
        float(np.abs(x - at.positions).max()) <= tol


# ---- the read ----------------------------------------------------------------------------------------------------------

def read(root=S2, out=print, *, g_reader=None):
    """The read; returns (ok, summary). g_reader replaces G only in the synthetic self-test."""
    cd, fig, q47, c46 = tools()
    g_reader = g_reader or cd.g_positions
    summary = {"item2": {}, "item4": {}, "item5_lines": 0}
    A = Archive(root, cd, fig, c46)
    cd.assert_no_calculator()
    reads0 = dict(q47.READS)

    out("ITEM 1. Integrity")
    final, G, rec_k, inp = {}, {}, {}, {}
    ok_all = True
    for lab in LABELS:
        r = A.a2(lab)
        vf, fg = r.get("validity_final"), r.get("final_geometry")
        fb = A.final_bytes(lab)
        vb = open(A.validity_path(lab), "rb").read()
        final[lab] = atoms_from_bytes(fb)
        inp[lab] = A.inputs(lab)
        vr = fig.guarded(A.validity_path(lab))
        gs = vr.get("geometry_sha256")
        par = inp[lab]["parent"]
        par_at = None if par is None else atoms_from_bytes(A.final_bytes(par))
        checks = {
            "final file sha256 = record": sha256_bytes(fb) == fg.get("sha256"),
            "validity file sha256 = record": sha256_bytes(vb) == vf.get("sha256"),
            "validity label and parent = record": vr.get("label") == lab and vr.get("parent_label") == vf.get("parent")
                                                  == par,
            "validity final geometry = loaded": gs.get("final") == c46.sha256_atoms(final[lab]),
            "validity start = A1 start": gs.get("start") == c46.sha256_atoms(inp[lab]["start"]),
            "validity relaxed host = C1 host": gs.get("host_relaxed") == c46.sha256_atoms(inp[lab]["host"]),
            "validity parent final = loaded": gs.get("parent_final") == (None if par_at is None
                                                                         else c46.sha256_atoms(par_at)),
        }
        rk = leaf(r, "layout", "ranks")
        pr, pos = g_reader(q47, A.L.a2_parts("c2", lab), mapping=A.mapping, ranks=rk, label=lab)
        G[lab], rec_k[lab] = pos, fg.get("k")
        kl = max(pos)
        checks["G configurations = record n_config"] = len(pos) == r.get("n_config")
        checks["G last k = record final k"] = kl == fg.get("k")
        checks["final = G last configuration (1e-6 A)"] = check_integrity_positions(pos[kl], final[lab])
        checks["final cell = A1 start cell"] = np.allclose(final[lab].cell.array, inp[lab]["start"].cell.array,
                                                           rtol=0, atol=1e-9)
        bad = [k for k, v in checks.items() if not v]
        out(f"  {lab}: valid {vf.get('valid')}; failed {vf.get('failed')}; parent {vf.get('parent')}; "
            f"parent_final {vf.get('parent_final')}; {len(checks) - len(bad)}/{len(checks)} integrity checks equal"
            + ("" if not bad else "; MISMATCH: " + "; ".join(bad)))
        ok_all = ok_all and not bad
    if not ok_all:
        out("Integrity mismatch: the diagnostic ends here (part d, item 1).")
        return False, summary

    out("ITEM 2. Agreement on check 5 (record / D5 / R46)")
    res, disagree = {}, []
    for ch, pa in PAIRS:
        x = inp[ch]
        d5 = cd.d5_check(x["kind"], final[ch], final[pa], x["host"], x["region"], x["leg"])
        r46, cp = cd.r46_for(c46, x["kind"], final[ch], final[pa], x["host"], x["region"], x["leg"])
        assert r46["passed"] == cp["passed"] and r46["gated"] == cp["gated"], f"{ch}: R46 differs from check_partner"
        recp = leaf(fig.guarded(A.validity_path(ch)), "validity", "checks", "5", "passed")
        res[ch] = (d5, r46)
        three = (bool(recp), bool(d5["passed"]), bool(r46["passed"]))
        summary["item2"][ch] = three + (bool(d5["passed_exchanged"]),)
        if len(set(three)) > 1:
            disagree.append(ch)
        w = lambda b: "pass" if b else "FAIL"
        out(f"  {ch} against {pa}: record {w(three[0])}; D5 {w(three[1])}; R46 {w(three[2])}; "
            f"D5 permutation-invariant reading {w(d5['passed_exchanged'])}"
            + ("; READINGS DISAGREE" if len(set(three)) > 1 else ""))

    out("ITEM 3. Per-object table (gated objects; D5)")
    for ch, pa in PAIRS:
        if (ch, pa) not in FAR and ch not in disagree:
            continue
        d5, r46 = res[ch]
        rows = [r for r in d5["rows"] if r["gated"]]
        out(f"  {ch} against {pa}: {len(rows)} gated objects "
            f"({sum(r['kind'] == 'inorganic' for r in rows)} inorganic, {sum(r['kind'] == 'FA' for r in rows)} FA)")
        out("    kind  child  host  d_host_A  dr_A  rot_deg  rot_exchanged_deg  check5_as_written  permutation_invariant")
        for r in sorted(rows, key=lambda r: (r["kind"], r["host"])):
            k = r["element"] if r["kind"] == "inorganic" else "FA"
            rot = "" if r["kind"] == "inorganic" else f"{r['rot_deg']:.1f}  {r['rot_exchanged_deg']:.1f}"
            out(f"    {k}  {r['child']}  {r['host']}  {r['d_host_A']:.2f}  {r['dr_A']:.3f}  {rot or '-  -'}  "
                f"{'pass' if r['pass'] else 'FAIL'}  {'pass' if r['pass_exchanged'] else 'FAIL'}")
        if ch in disagree:
            L = r46["lists"]["gated"]
            out("    R46 gated inorganic (index, d_host_A, dr_A): " +
                "; ".join(f"{r['index']} {r['d_host_A']:.2f} {r['dr_A']:.3f}" for r in L["inorganic"]))
            out("    R46 gated FA (carbon, d_host_A, dr_carbon_A, rot_deg): " +
                "; ".join(f"{r['carbon']} {r['d_host_A']:.2f} {r['dr_carbon_A']:.3f} {r['rot_deg']:.1f}"
                          for r in L["fa"]))

    out("ITEM 4. Which cell moved (failing objects)")
    refs = {}
    for ch, pa in PAIRS:
        d5, r46 = res[ch]
        x = inp[ch]
        c2h, c2p = cd.maps_section4(x["kind"], len(x["host"]), x["leg"])
        ref = x["host"] if x["kind"] in ("V", "D") else A.c1_cell(inp[pa]["a1"], "relaxed")
        assert ref.get_chemical_symbols() == final[pa].get_chemical_symbols(), f"{ch}: reference numbering"
        refs[ch] = (ref, c2p)
        failing = {r["child"]: r for r in d5["rows"] if r["gated"] and not r["pass"]}
        L = r46["lists"]["gated"]
        p2c = {p: c for c, p in c2p.items()}
        for r in L["inorganic"]:
            if r["dr_A"] >= 0.25 and r["index"] not in failing:
                failing[r["index"]] = {"kind": "inorganic", "child": r["index"], "parent": c2p[r["index"]],
                                       "host": c2h[r["index"]], "element": final[ch].get_chemical_symbols()[r["index"]]}
        for r in L["fa"]:
            if (r["dr_carbon_A"] >= 0.25 or r["rot_deg"] >= 20.0) and r["carbon"] not in failing:
                failing[r["carbon"]] = {"kind": "FA", "child": r["carbon"], "parent": c2p[r["carbon"]],
                                        "host": c2h[r["carbon"]]}
        if not failing:
            continue
        rname = "S2-relaxed MACE host" if x["kind"] in ("V", "D") else f"A1 {inp[pa]['a1']} geometry"
        out(f"  {ch} against {pa}: {len(failing)} failing object(s); reference {rname}")
        cell = final[ch].cell.array
        k0c, k0p = G[ch][0][1], G[pa][0][1]
        for c in sorted(failing):
            o = failing[c]
            ic, ip = obj_indices(cd, o, final[pa], c2p)
            name = (o["element"] if o["kind"] == "inorganic" else "FA") + f" child {o['child']} host {o['host']}"
            m3 = (measure(cd, final[ch].positions, ref.positions, ic, ip, cell), measure(cd, final[pa].positions, ref.positions, ip, ip, cell), measure(cd, k0c, k0p, ic, ip, cell))
            summary["item4"].setdefault(ch, []).append((o["child"], o["host"]) + tuple(m[0] for m in m3))
            out(f"    {name}: child final vs reference {fmt(*measure(cd, final[ch].positions, ref.positions, ic, ip, cell))}; "
                f"parent final vs reference {fmt(*measure(cd, final[pa].positions, ref.positions, ip, ip, cell))}; "
                f"child k = 0 vs parent k = 0 {fmt(*measure(cd, k0c, k0p, ic, ip, cell))}")

    out("ITEM 5. Trajectory (far pairs; against the item-4 reference)")
    for ch, pa in FAR:
        d5, _ = res[ch]
        ref, c2p = refs[ch]
        cell = final[ch].cell.array
        g = [r for r in d5["rows"] if r["gated"]]
        objs = [max((r for r in g if r["kind"] == "inorganic"), key=lambda r: r["dr_A"], default=None),
                max((r for r in g if r["kind"] == "FA"), key=lambda r: r["rot_deg"], default=None)]
        for o in [o for o in objs if o is not None]:
            ic, ip = obj_indices(cd, o, final[pa], c2p)
            name = (o["element"] if o["kind"] == "inorganic" else "FA") + f" child {o['child']} host {o['host']}"
            for cellname, lab, ii in (("child", ch, ic), ("parent", pa, ip)):
                out(f"  {ch} against {pa}; {name}; {cellname} {lab}; k, |dr| A" +
                    ("" if len(ii) == 1 else ", rot deg, rot exchanged deg"))
                for k in sorted(G[lab]):
                    dr, rot, rotx = measure(cd, G[lab][k][1], ref.positions, ii, ip, cell)
                    out(f"    {k} {dr:.3f}" + ("" if rot is None else f" {rot:.1f} {rotx:.1f}"))
                    summary["item5_lines"] += 1

    for key in ("F", "TS", "forces", "fermi", "mag", "ase"):
        assert q47.READS.get(key, 0) == reads0.get(key, 0), "a value other than positions was read"
    cd.assert_no_calculator()
    out("END: items 1-5 printed; no energy, force or gate value read; no calculator loaded")
    return True, summary


# ---- self-test -----------------------------------------------------------------------------------------------------------

def self_test():
    import tempfile
    from ase.io import read as aread
    cd, fig, q47, c46 = tools()
    # guard: a withheld field raises; a guarded record is neither iterated nor printed
    g = fig.Guarded({"end_rule": {"outcome": "accepted_converged", "dF_200_180_meV": 1.0}, "value_meV": 2.0,
                     "result": {"Eb_A2_meV": {"hinge": 3.0}}}, "synthetic")
    for f in (lambda: g.get("value_meV"), lambda: g.get("end_rule").get("dF_200_180_meV"),
              lambda: g.get("result").get("Eb_A2_meV"), lambda: list(g), lambda: str(g), lambda: g.get("end_rule").open()):
        try:
            f()
            raise AssertionError("a withheld field or a whole record was readable")
        except fig.Blinded:
            pass
    assert leaf(g, "end_rule", "outcome") == "accepted_converged"
    # blinded loader of C1 records: E_mace_eV removed at any depth
    tmp = tempfile.mkdtemp(prefix="partd_")
    p = os.path.join(tmp, "rec.json")
    json.dump({"a": {"E_mace_eV": -1.0, "b": [{"E_mace_eV": -2.0, "c": 1}]}}, open(p, "w"))
    assert "E_mace_eV" not in json.dumps(c46.load_record(p)), "blinded loader"
    os.remove(p); os.rmdir(tmp)
    # C1 archive loaders (public; no C2 file): region and host as the runner checks them, legs, A1 cells
    A = Archive(S2, cd, fig, c46, c2=False)
    for site, tok in ((136, "Sr"), (76, "Sr")):
        reg = c46.check_region_record(c46.load_record(A.L.region("c1", "m30", "B", site)))
        host = A.c1_cell("s2_m30_host", "relaxed")
        assert host.calc is None and reg["host_source"]["sha256"] == c46.sha256_atoms(host), "region/host"
        pr = c46.load_record(A.L.pair("c1", "m30", tok, site, 0))
        for lg in ("novac", "vac"):
            assert {"old_to_new", "members"} <= set(pr["legs"][lg]), "leg keys"
            assert c46.free_in_cell(reg, "D" if lg == "novac" else "DV", built=pr["legs"][lg]) == \
                cd.free_section4("D" if lg == "novac" else "DV", reg["free"], pr["legs"][lg]), "free sets"
        v = A.c1_cell(f"s2_m30_VB{site}", "relaxed")
        assert len(v) == len(host) - 1 and v.calc is None
    # items 4-5 measure on the public reference cell: known displacements and a known FA rotation
    h = aread(os.path.join(REPO, "results", "fa_host", "fa19cs1_pb20i60_233.extxyz")); h.calc = None
    cell = h.cell.array
    s = np.array(h.get_chemical_symbols())
    c = int(np.flatnonzero(s == "C")[0])
    sk = fa_skeleton(cd, h, c)
    child = h.copy(); child.calc = None
    child.positions[sk] = cd._rotate_about(child.positions[sk], child.positions[c], (0.2, 0.3, 0.93), 33.0)
    child.positions[sk] += np.array([0.0, 0.0, 0.12])
    dr, rot, rotx = measure(cd, child.positions, h.positions, sk, sk, cell)
    assert abs(dr - 0.12) < 1e-9 and abs(rot - 33.0) < 1e-6 and rotx > rot, "FA measure"
    i = int(np.flatnonzero(s == "Pb")[0])
    moved = h.positions.copy(); moved[i] += cell[0] + np.array([0.05, 0.0, 0.0])        # across the boundary
    assert abs(measure(cd, moved, h.positions, [i], [i], cell)[0] - 0.05) < 1e-9, "periodic measure"
    # an exchanged FA: same configuration under the permutation-invariant reading
    ex = h.positions.copy(); ex[[sk[1], sk[2]]] = ex[[sk[2], sk[1]]]
    _, rot, rotx = measure(cd, ex, h.positions, sk, sk, cell)
    assert rot > 90 and rotx < 1e-6, "exchange"
    # obj_indices through a V map: an FA numbered after I127 is shifted down by one in the child
    c2h, c2p = cd.maps_section4("V", len(h))
    c9 = max(int(x) for x in np.flatnonzero(s == "C"))
    sk9 = fa_skeleton(cd, h, c9)
    assert min(sk9) > cd.VI, "the reference cell has no FA numbered after I127"
    ic, ip = obj_indices(cd, {"kind": "FA", "parent": c9, "child": c9 - 1}, h, c2p)
    assert ip == sk9 and ic == [x - 1 for x in sk9], "obj_indices V map"
    # item 1 position comparison at the 1e-6 A tolerance
    syms = h.get_chemical_symbols()
    assert check_integrity_positions((syms, h.positions + 0.9e-6), h)
    assert not check_integrity_positions((syms, h.positions + 1.1e-6), h)
    assert not check_integrity_positions((syms[::-1], h.positions), h)
    cd.assert_no_calculator()
    print("part-d driver self-test passed: guard (6 refusals), blinded loader, C1 archive loaders at Pb136 and Pb76 "
          "(region/host hash, legs, free sets equal to D5's), measures (FA rotation 33.0 deg, periodic 0.05 A, "
          "nitrogen exchange), V-map indices, 1e-6 A integrity tolerance; no C2 file read")


def self_test_read():
    """The whole read on a synthetic archive: c1 is the public C1 archive; c2 is built here from public C1 geometries
    (each label's 'final' is the A1 relaxed geometry of its A1 cell), with validity records written by scripts/46
    validity_a2 itself. One gated far inorganic atom of the VB76 'final' is moved by 0.35 A, so check 5 must fail for
    VB76 against hostB76 (the child moved) and for Sr76o0_vac against VB76 (the parent moved), and pass elsewhere. G is
    replaced by a stub that interpolates from the A1 start to the 'final' (G itself is tested in check5_diag.py)."""
    import shutil, tempfile
    cd, fig, q47, c46 = tools()
    tmp = tempfile.mkdtemp(prefix="partd_read_")
    try:
        os.symlink(os.path.join(S2, "c1"), os.path.join(tmp, "c1"))
        raw = os.path.join(tmp, "c2", "raw"); os.makedirs(raw)
        jobs = []
        for lab, a1, kind, par, j, tok, leg in (
                ("VB136", "s2_m30_VB136", "V", "hostB136", 136, None, None),
                ("hostB136", "s2_m30_host", "host", None, 136, None, None),
                ("Sr136o0_novac", "s2_m30_Sr136p0_novac", "D", "hostB136", 136, "Sr", "novac"),
                ("Sr136o0_vac", "s2_m30_Sr136p0_vac", "DV", "VB136", 136, "Sr", "vac"),
                ("hostB76", "s2_m30_host", "host", None, 76, None, None),
                ("VB76", "s2_m30_VB76", "V", "hostB76", 76, None, None),
                ("Sr76o0_novac", "s2_m30_Sr76p0_novac", "D", "hostB76", 76, "Sr", "novac"),
                ("Sr76o0_vac", "s2_m30_Sr76p0_vac", "DV", "VB76", 76, "Sr", "vac")):
            jobs.append({"id": f"a2v:{P}{lab}", "kind": "a2v", "label": P + lab, "parent": par and P + par,
                         "member": "m30", "cell_kind": kind, "L": "B", "j": j, "token": tok, "leg": leg, "a1": a1})
        json.dump({"jobs": jobs}, open(os.path.join(tmp, "c2", "graph.json"), "w"))
        A = Archive(tmp, cd, fig, c46, c2=False)
        A.job = {x["label"]: x for x in jobs}
        fdir = os.path.join(tmp, "finals")
        fin, starts = {}, {}
        fpath = lambda lab: os.path.join(fdir, "a2", lab, f"{lab}.final.extxyz")
        for x in jobs:
            fin[x["label"]] = c46.write_cell(fpath(x["label"]), A.c1_cell(x["a1"], "relaxed"))
            starts[x["label"]] = A.c1_cell(x["a1"], "start")
        # move A: the gated atom farthest from the vacancy in the V check (VB76 against hostB76: the child moves);
        # move B: the gated atom farthest from the site in the D+V check (Sr76o0_vac against VB76: the parent moves)
        V, H, DV = P + "VB76", P + "hostB76", P + "Sr76o0_vac"
        iv, idv = A.inputs(V), A.inputs(DV)
        gate_max = lambda rows: max((r for r in rows if r["gated"] and r["kind"] == "inorganic"),
                                    key=lambda r: r["d_host_A"])
        mA = gate_max(cd.d5_check("V", fin[V], fin[H], iv["host"], iv["region"])["rows"])
        mB = gate_max(cd.d5_check("DV", fin[DV], fin[V], idv["host"], idv["region"], idv["leg"])["rows"])
        assert mA["child"] != mB["parent"], "the two moved atoms coincide"
        at = fin[V].copy(); at.calc = None
        at.positions[mA["child"]] += np.array([0.35, 0.0, 0.0])
        at.positions[mB["parent"]] += np.array([0.0, 0.35, 0.0])
        fin[V] = c46.write_cell(fpath(V), at)
        with tarfile.open(os.path.join(tmp, "c2", "structures.tar.gz"), "w:gz") as tf:
            for lab in fin:
                tf.add(os.path.join(fdir, "a2", lab, f"{lab}.final.extxyz"), arcname=f"a2/{lab}/{lab}.final.extxyz")
        A2 = Archive(tmp, cd, fig, c46)
        n_cfg = 5
        for x in jobs:
            lab, par = x["label"], x["parent"]
            inp = A2.inputs(lab)
            val = c46.validity_a2(inp["kind"], start=inp["start"], final=fin[lab], region=inp["region"],
                                  host_relaxed=inp["host"], parent_final=par and fin[par], built=inp["leg"])
            vrec = {"label": lab, "kind": inp["kind"], "parent_label": par, "validity": val,
                    "geometry_sha256": {"start": c46.sha256_atoms(inp["start"]), "final": c46.sha256_atoms(fin[lab]),
                                        "parent_final": par and c46.sha256_atoms(fin[par]),
                                        "host_relaxed": c46.sha256_atoms(inp["host"])}}
            vp = c46.dump_public(vrec, A2.validity_path(lab))
            ff = os.path.join(fdir, "a2", lab, f"{lab}.final.extxyz")
            c46.dump_public({"label": lab, "n_config": n_cfg, "layout": {"name": "64", "ranks": 64, "copies": 1},
                             "end_rule": {"outcome": "accepted_converged", "dF_200_180_meV": None},
                             "final_geometry": {"file": os.path.basename(ff), "k": n_cfg - 1,
                                                "sha256": sha256_bytes(open(ff, "rb").read())},
                             "validity_final": {"valid": val["valid"], "failed": val["failed"],
                                                "file": os.path.basename(vp), "sha256": sha256_bytes(open(vp, "rb").read()),
                                                "parent": par, "parent_final": par is not None}},
                            os.path.join(raw, f"{lab}.a2.json"))

        def g_stub(q47_, parts, *, mapping, ranks, label):
            s0, f1 = starts[label], fin[label]
            pos = {k: (f1.get_chemical_symbols(), s0.positions + (f1.positions - s0.positions) * k / (n_cfg - 1))
                   for k in range(n_cfg)}
            pos[n_cfg - 1] = (f1.get_chemical_symbols(), f1.positions.copy())
            return {"n_config": n_cfg}, pos

        lines = []
        ok, sm = read(tmp, out=lines.append, g_reader=g_stub)
        assert ok, "synthetic read: integrity"
        expect_fail = {V, DV}
        for ch, three in sm["item2"].items():
            want = ch not in expect_fail
            assert three == (want, want, want, want), f"synthetic read: item 2 for {ch}"
        it4 = sm["item4"]
        assert set(it4) == expect_fail, "synthetic read: item 4 pairs"
        a = [t for t in it4[V] if t[1] == mA["host"]]
        assert len(a) == 1 and a[0][2] > 0.25 and a[0][3] < 1e-9, "item 4: the child moved (VB76 against hostB76)"
        b = [t for t in it4[DV] if t[1] == mB["host"]]
        assert len(b) == 1 and abs(b[0][3] - 0.35) < 1e-6 and b[0][2] < 0.25, \
            "item 4: the parent moved (Sr76o0_vac against VB76)"
        n5 = sm["item5_lines"]
        assert n5 % (2 * n_cfg) == 0 and 3 * 2 * n_cfg <= n5 <= 3 * 4 * n_cfg, "item 5 lines"
        assert any(l.startswith("ITEM 3") for l in lines) and lines[-1].startswith("END"), "printed items"
        # a changed validity file ends the read at item 1
        vb = A2.validity_path(P + "VB136")
        txt = open(vb).read(); open(vb, "w").write(txt.replace('"label"', '"label" ', 1))
        ok2, _ = read(tmp, out=lambda s: None, g_reader=g_stub)
        assert not ok2, "a changed validity file must end the read"
    finally:
        shutil.rmtree(tmp)
    cd.assert_no_calculator()
    print(f"part-d synthetic read passed: integrity on 8 synthetic records; after 0.35 A moves of two atoms of VB76 "
          f"(one gated about the vacancy, one gated about the site), item 2 fails exactly VB76 and Sr76o0_vac under "
          f"record, D5 and R46; item 4 finds the child moved for VB76 and the parent moved for Sr76o0_vac; item 5 "
          f"{n5} lines; a changed validity file ends the read; no C2 file read")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--read", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        self_test_read()
    elif a.read:
        head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", REPO, "status", "--porcelain", "--", HERE], capture_output=True,
                               text=True).stdout.strip()
        assert not dirty, "the part-d tools are not committed (part d, 'When')"
        print(f"part-d read at {head}; tools sha256 check5_diag "
              f"{sha256_bytes(open(os.path.join(HERE, 'check5_diag.py'), 'rb').read())[:12]}, part_d_read "
              f"{sha256_bytes(open(os.path.abspath(__file__), 'rb').read())[:12]}")
        sys.exit(0 if read()[0] else 1)
    else:
        ap.print_help()

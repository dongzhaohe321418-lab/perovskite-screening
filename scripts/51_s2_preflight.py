#!/usr/bin/env python
"""S2 pre-flight on the laptop, geometry only (results/objective2/s2/S2_PLAN.md section 17 item 4, with sections
5-11 and 16; the Stage-0 interface specification, section 9.4). Before the node is booted, every campaign-1 cell is
built as a dry run and checked, and every C1 input is written and checked; the dry-run outputs are never used (the
cells that are calculated are built on the node from the S2-relaxed host and V+_R, sections 5 and 7).

  cells     On the unrelaxed m30 and m05 members (the unrelaxed host stands in for the S2-relaxed host, the
            pp.build_pair vacancy cell for V+_R), every C1 cell of the scripts/50 C1 graph: the noise pilot (the four
            farthest sites per sublattice, section 8), the A2 start set (the calibration sites of section 11, the
            m05 sites from the Stage-0 admissibility record), every pose start of section 9 (Cs at FA128 and FA188:
            centred and the six +-0.30 A starts; Cl at I138 and I175: centred and the two shifted starts, which need
            the section 2 Pb-Cl record and, while it is provisional, --allow-provisional), the G1 host-leg cells
            (section 7), the spin, step-0 and q = 0 cells (sections 7, 10, 11). Pairs by scripts/46 pair_record
            (b42.build_paired, partners="unrelaxed"); regions and region ids by scripts/46 build_region on the
            stand-in host.
  inputs    Every C1 single point (the pose slots filled as if every start were a kept minimum: the 40 single-point
            upper bound), the C2 and C4 A2 inputs of the start set with a placeholder nstep (flagged "pending smoke
            tests", X-3), and the pw.x smoke-test and throughput-row inputs on the 232-atom reference cell with the
            Pb136-like region (section 16), all written by scripts/47 to a directory outside the repository.
  checks    Builder: every pair built, its V1-V10 passed and admissible (a default start rejected is a failure; a
            non-default start rejected is listed). Labels: grammar and semantic constraints (scripts/46
            check_label), uniqueness, the lists of the plan (G1, spin, q = 0, the C2 order, 26 C4 relaxations).
            Region ids: one per (host, site), deterministic, shared by every cell of the site, distinct between
            sites. Electrons: tot_charge and the valence count recomputed here from the X-unit count and z_valence
            (host 1070, vacancy cells 1062 after the charge, _q0 1063; Sr -4, Ca -4, Cl 0, Cs -10, GA +6) and
            compared with the writer's record. Writer output: each input re-parsed and every namelist value compared
            with scripts/47 settings_for and with the literal section-6 values below; the K point, the species
            files and, for relaxations, exactly the atoms outside R_j fixed (if_pos 0 0 0). Counts: the scripts/50
            C1 graph against the plan (assert_counts) and the inputs written.
  output    The path-free summary results/objective2/s2/stage0/preflight_c1.json (counts, region ids, failures,
            which must be empty) and the full log outside the repository. No calculator is created; the run ends
            asserting that "mace" is not in sys.modules.

    python scripts/51_s2_preflight.py --self-test [--work DIR]
    python scripts/51_s2_preflight.py run --out <dir outside the repository> [--allow-provisional] \\
        [--summary results/objective2/s2/stage0/preflight_c1.json] [--log <file outside the repository>]
"""
import argparse, collections, hashlib, importlib.util, json, os, re, shutil, sys, tempfile, time, traceback

from ase.io import read

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


k50 = _load("k50", "50_s2_campaign.py")            # graph, assert_counts, a1_of_a2, the C2/C4 orders
c46, q47, b42 = k50.c46, k50.q47, k50.b42          # one module object per file (scripts/50 loaded them)
MOCKED = list(k50.MOCKED)

PLACEHOLDER_NSTEP = 201                            # A2 inputs: nstep pending the C1 smoke tests (X-3)
SUMMARY = "results/objective2/s2/stage0/preflight_c1.json"
# Literal section 6 values (the writer is compared with these as well as with scripts/47 settings_for)
PLAN6 = {"ecutwfc": 50.0, "ecutrho": 400.0, "occupations": "smearing", "smearing": "gaussian", "degauss": 0.005,
         "nosym": True, "conv_thr": 1e-8, "mixing_beta": 0.3, "electron_maxstep": 200, "tprnfor": True,
         "tstress": False, "pseudo_dir": "/data/pseudo", "outdir": "./tmp"}
PLAN6_G1 = {"ecutwfc": 60.0, "ecutrho": 480.0}
PLAN6_RELAX = {"ion_dynamics": "bfgs", "forc_conv_thr": 7.8e-4, "etot_conv_thr": 1e-5, "disk_io": "low"}
ELECTRONS = {"host": 1070, "vac_q1": 1062, "vac_q0": 1063}
DVAL = {"Sr": -4, "Ca": -4, "Cl": 0, "Cs": -10, "GA": 6}
NOTES = {
    "N-P1": "the unrelaxed member stands in for the S2-relaxed host and the pp.build_pair vacancy cell for V+_R; the "
            "pairs use partners='unrelaxed' (section 17 item 4); nothing built here is used on the node",
    "N-P2": "pose slots: every start of a pose site is treated as a kept minimum (o<k> = p<k>), the 40 single-point "
            "upper bound of section 9; a non-default start that the builder rejects is listed, not a failure; a "
            "rejected default start is a failure",
    "N-P3": "A2 inputs of the C2 and C4 start set are written with nstep 201, flagged 'pending smoke tests' (X-3); "
            "their free sets come from the stand-in regions",
    "N-P4": "the m05 calibration sites and the Pb-Cl decision are read from the Stage-0 records (admissibility.json, "
            "pbcl_source.json); a provisional Pb-Cl record needs --allow-provisional, else the shifted Cl starts are "
            "refused and the pre-flight fails",
    "N-P5": "electron counts and namelists are recomputed here independently of the writer and compared with its "
            "record and with the literal section 6 values",
}


class Check:
    """Every check of the pre-flight: name, passed, detail; failures stop nothing until the end (all are listed)."""

    def __init__(self):
        self.rows, self.failures, self.counts = [], [], collections.Counter()

    def __call__(self, name, ok, detail=""):
        self.counts[name] += 1
        if not ok:
            self.failures.append({"check": name, "detail": str(detail)[:400]})
        return ok

    def fail(self, name, detail):
        return self(name, False, detail)


def stage0_state(allow_missing=False):
    """The S2 state the C1 graph needs, from the committed Stage-0 records (N-P4)."""
    adm = k50.read_json(os.path.join(ROOT, k50.ADMISSIBILITY_RECORD))
    pb = k50.read_json(os.path.join(ROOT, k50.PBCL_RECORD))
    st = k50.synthetic_state(a2_layout=None)
    src = "plan lists (Stage-0 records absent)"
    if adm is not None:
        cal = adm.get("m05_chosen") or {L: adm["m05_calibration"][L].get("chosen") for L in "BAX"}
        pr = adm["production"]
        st["stage0"].update({"production_n8": pr["n8"], "reserves_n8": pr["reserves_n8"], "production_n10": pr["n10"],
                             "reserves_n10": pr["reserves_n10"], "m05_cal": {L: int(cal[L]) for L in "BAX"}})
        src = "results/objective2/s2/stage0/admissibility.json"
    elif not allow_missing:
        raise c46.S2Error("no Stage-0 admissibility record: the m05 calibration sites are not fixed")
    if pb is not None:
        st["stage0"]["pbcl"] = {k: pb.get(k) for k in ("decision", "value_used_A", "tag_for_shifted_starts",
                                                       "allow_provisional_required")}
    st["stage0"]["source"] = src
    return st


def electrons_expected(label):
    """(tot_charge, valence electrons) from the label alone (sections 1, 6, 10)."""
    p = c46.parse_label(label)
    if p.get("ref"):
        return 1, ELECTRONS["vac_q1"]
    vac = p["kind"] in ("V", "DV")
    q = 0 if (not vac or p.get("q0")) else 1
    base = ELECTRONS["host"] if not vac else (ELECTRONS["vac_q0"] if p.get("q0") else ELECTRONS["vac_q1"])
    return q, base + (DVAL[p["token"]] if p.get("token") else 0)


def check_electrons(ck, label, atoms, meta):
    """Recomputed from the cell: X units (60 neutral, 59 vacancy), z_valence (b42.VALENCE), tot_charge."""
    s = atoms.get_chemical_symbols()
    nx = s.count("I") + s.count("Cl")
    q, exp = electrons_expected(label)
    z = sum(b42.VALENCE[e] for e in s)
    ok = nx in (59, 60) and (nx == 59) == (c46.parse_label(label).get("ref") or
                                           c46.parse_label(label)["kind"] in ("V", "DV"))
    n_el = z - q
    ok = ok and n_el == exp and (n_el % 2 == 1) == label.endswith("_q0")
    el = (meta or {}).get("electrons") or {}
    ok = ok and el.get("n_el") == n_el and el.get("tot_charge") == q
    return ck("electrons", ok, f"{label}: n_X {nx}, z {z}, q {q}, n_el {n_el}, expected {exp}, writer {el}")


def check_input(ck, path, label, kind, atoms, free=None, nstep=None):
    """Writer output line by line: namelists against scripts/47 settings_for and the literal section-6 values;
    species, K point, nat and the if_pos flags."""
    text = open(path).read()
    p = q47.parse_input_text(text)
    nl = p["namelists"]
    flat = {**nl.get("control", {}), **nl.get("system", {}), **nl.get("electrons", {}), **nl.get("ions", {})}
    s = q47.settings_for(label, kind)
    want = dict(PLAN6)
    if label.startswith("s2g1_") and label.endswith("_e60"):
        want.update(PLAN6_G1)
    want.update({"calculation": "relax" if kind == "relax" else "scf", "prefix": label,
                 "nspin": 2 if label.startswith("s2spin_") else 1, "tot_charge": electrons_expected(label)[0],
                 "disk_io": "low" if kind == "relax" else "none", "nat": len(atoms)})
    if kind == "relax":
        want.update(PLAN6_RELAX); want["nstep"] = int(nstep)
    bad = []
    for k, v in want.items():
        got = flat.get(k)
        if k in ("ecutwfc", "ecutrho", "degauss", "conv_thr", "mixing_beta", "forc_conv_thr", "etot_conv_thr",
                 "tot_charge"):
            if got is None or abs(float(got) - float(v)) > 1e-12 * max(1.0, abs(float(v))):
                bad.append((k, got, v))
        elif got != v:
            bad.append((k, got, v))
    for k in ("ecutwfc", "ecutrho", "degauss", "conv_thr", "mixing_beta", "electron_maxstep", "nspin", "disk_io",
              "calculation", "tot_charge"):
        if k in s and s[k] is not None and k in want and not (s[k] == want[k] or (isinstance(s[k], float) and
                                                                                  abs(s[k] - float(want[k])) < 1e-12)):
            bad.append(("settings_for", k, s[k], want[k]))
    if "restart_mode" in flat:
        bad.append(("restart_mode", flat["restart_mode"], "absent in a first part"))
    kp = p["cards"].get("K_POINTS", {})
    if kp.get("rows") != [["1", "1", "1", "1", "1", "1"]]:
        bad.append(("K_POINTS", kp.get("rows")))
    species = {r[0]: r[2] for r in p["cards"]["ATOMIC_SPECIES"]["rows"]}
    for el, f in species.items():
        sym = re.sub(r"\d+$", "", el)
        if q47.PSEUDO_S2.get(sym) != f:
            bad.append(("species", el, f))
    rows = p["cards"]["ATOMIC_POSITIONS"]["rows"]
    if len(rows) != len(atoms):
        bad.append(("nat rows", len(rows), len(atoms)))
    fixed = [i for i, r in enumerate(rows) if len(r) >= 7 and r[4:7] == ["0", "0", "0"]]
    if kind == "relax":
        want_fixed = sorted(set(range(len(atoms))) - set(int(i) for i in free))
        if fixed != want_fixed:
            bad.append(("if_pos", len(fixed), len(want_fixed)))
    elif fixed:
        bad.append(("if_pos in a single point", len(fixed)))
    return ck("writer output", not bad, f"{label}: {bad}")


def _write_sp(ck, out, label, atoms, *, dopant=None, cell=None):
    d = os.path.join(out, "c1_sp", label)
    di = None
    if dopant is not None:
        idx = [i for i, e in enumerate(atoms.get_chemical_symbols()) if e == dopant]
        di = idx[0] if len(idx) == 1 else None
    try:
        meta = q47.write_input(atoms, label, d, kind="sp", dopant_index=di, ranks=q47.RANKS_SP, campaign="c1", cell=cell)
    except Exception as e:                                              # noqa: BLE001 (every refusal is a failure)
        ck.fail("writer refused", f"{label}: {type(e).__name__}: {e}")
        return None
    check_electrons(ck, label, atoms, meta)
    check_input(ck, os.path.join(d, f"{label}.in"), label, "sp", atoms)
    return meta


def _write_relax(ck, out, sub, label, atoms, free, nstep, ranks, campaign):
    d = os.path.join(out, sub, label)
    try:
        meta = q47.write_input(atoms, label, d, kind="relax", free=free, nstep=nstep, ranks=ranks, campaign=campaign,
                               cell={"pending": "smoke tests (nstep placeholder)"} if sub != "ref" else None)
    except Exception as e:                                              # noqa: BLE001
        ck.fail("writer refused", f"{label}: {type(e).__name__}: {e}")
        return None
    check_electrons(ck, label, atoms, meta)
    check_input(ck, os.path.join(d, f"{label}.in"), label, "relax", atoms, free=free, nstep=nstep)
    return os.path.join(d, f"{label}.in")


def preflight(out_dir, *, members=("m30", "m05"), allow_provisional=False, pbcl_record=None, subset=None,
              plant=None, log=None):
    """The section 17 item 4 dry run (interface spec 9.4). subset: {member: [sites]} limits the cells (self-test);
    plant: one deliberate error the self-test plants and the checks must catch."""
    t0 = time.time()
    ck = Check()
    os.makedirs(out_dir, exist_ok=True)
    st = stage0_state(allow_missing=plant is not None)
    pbcl, pbcl_err = None, None
    try:
        pbcl = c46.pbcl_value(pbcl_record or c46.PBCL_RECORD, allow_provisional=allow_provisional)
    except Exception as e:                                              # noqa: BLE001 (refusal recorded below)
        pbcl_err = f"{type(e).__name__}: {e}"
    ctx, sets, regions, cells, pairs, rejected = {}, {}, {}, {}, {}, []
    for m in members:
        ctx[m] = c46.host_context(m)
        sets[m] = c46.site_sets(ctx[m])
        ck("site tables", bool(c46.assert_site_tables(m, sets[m])), m)
    g = k50.graph("c1", st, sites=lambda mm: sets[mm] if mm in sets else c46.site_sets(c46.host_context(mm)))
    if subset is None:
        exp, adj = k50.assert_counts(g, st)
        ck("graph counts", True, exp)
    keep = lambda m, j: m in members and (subset is None or (m in subset and int(j) in subset[m]))
    vac = {m: c46.make_vacancy(ctx[m].host, ctx[m])[0] for m in members}
    jobs = g["jobs"]
    # ---- cells
    for j in jobs:
        m = j.get("member")
        if m not in members:
            continue
        host = ctx[m].host
        if j["kind"] == "mace" and j.get("cell_kind") == "host":
            cells[j["work_id"]] = {"atoms": host, "kind": "host", "free": list(range(len(host))), "site": None}
        elif j["kind"] == "g46" and j["action"] == "region" and keep(m, j["site"]):
            roles = c46.site_roles(m, j["L"], j["site"], sets[m], c46.c1_sites(m, m05_cal=st["stage0"]["m05_cal"],
                                                                            sets=sets[m]))
            reg = c46.build_region(host, m, j["site"], roles=roles, host_work_id=k50.wid_of(m, "host"))
            again = c46.build_region(host, m, j["site"])
            ck("region id deterministic", reg["region_id"] == again["region_id"] == c46.region_id(m, j["site"], reg["free"]),
               f"{m} {j['L']}{j['site']}")
            regions[(m, int(j["site"]))] = reg
        elif j["kind"] == "g46" and j["action"] == "build-vac" and keep(m, j["site"]):
            reg = regions[(m, int(j["site"]))]
            cells[j["work_id"]] = {"atoms": vac[m], "kind": "V", "free": c46.free_in_cell(reg, "V"),
                                   "site": int(j["site"]), "region_id": reg["region_id"]}
        elif j["kind"] == "g46" and j["action"] == "build-pair" and keep(m, j["site"]):
            T, site, start = j["token"], int(j["site"]), j["start"]
            shifted = T == "Cl" and b42.sampled_names("Cl")[int(start[1:])].startswith("shift")
            if shifted and (pbcl is None or plant == "cl_without_record"):
                ck.fail("shifted Cl start", f"{m} Cl{site} {start}: no usable Pb-Cl record "
                        f"({pbcl_err or 'planted: record withheld'}); section 2 needs it before any shifted start")
                continue
            try:
                rec, bh, bv = c46.pair_record(host, vac[m], ctx[m], T, site, start, partners="unrelaxed",
                                              pbcl=pbcl if shifted else None,
                                              parents={"novac": k50.wid_of(m, "host"), "vac": k50.wid_of(m, "V", j["L"], site)})
            except Exception as e:                                      # noqa: BLE001 (BuildError, S2Error)
                ck.fail("builder", f"{m} {T}{site} {start}: {type(e).__name__}: {e}")
                continue
            pairs[j["id"]] = rec
            if rec["status"] != "built":
                (ck.fail("builder", f"default start rejected: {m} {T}{site}: {rec['rejection']}") if start == "p0"
                 else rejected.append({"member": m, "token": T, "site": site, "start": start,
                                       "reason": rec["rejection"]["reason"][:160]}))
                continue
            reg = regions[(m, site)]
            for leg, b, kind in (("novac", bh, "D"), ("vac", bv, "DV")):
                lr = rec["legs"][leg]
                br = lr["builder_report"]
                # V1-V10 valid and admissible (V7 is the clash filter; for GA it reports only, section 2)
                ck("builder", br["valid"] and br["admissible"] and all(v for k, v in br["checks_passed"].items() if k != "V7"),
                   f"{m} {T}{site} {start} {leg}: {br}")
                cells[lr["work_id"]] = {"atoms": b.atoms, "kind": kind, "free": c46.free_in_cell(reg, kind, built=lr),
                                        "site": site, "region_id": reg["region_id"], "pair": j["id"]}
    if plant == "region_id":
        w = next(w for w, c in cells.items() if c.get("region_id"))
        cells[w] = dict(cells[w], region_id="0" * 64)
    # ---- region ids: one per (host, site), shared by every cell of the site, distinct between sites
    ids = {}
    for (m, site), reg in regions.items():
        ids[f"{m}_{reg['sublattice']}{site}"] = reg["region_id"]
    ck("region ids distinct", len(set(ids.values())) == len(ids), ids)
    for w, c in cells.items():
        if c.get("site") is not None:
            m = c46.parse_work_id(w)["host"]
            ck("region id of the site", c["region_id"] == regions[(m, c["site"])]["region_id"], w)
    # ---- G1 cells (section 7)
    g1 = {}
    if "m30" in members:
        for T, L, site in k50.G1_SITES:
            if keep("m30", site):
                b = c46.build_host_leg(ctx["m30"].host, ctx["m30"], T, site)
                g1[f"{T}{site}"] = b.atoms
                ck("builder", b.report["valid"] and b.report["admissible"], f"G1 {T}{site}")
    # ---- single points
    labels, written = [], collections.Counter()
    sps = [j for j in jobs if j["kind"] == "sp"]
    for j in sps:
        lab = j["label"]
        if j["src"] == "g1":
            atoms = g1.get(j["g1"])
            wid = None
        elif j["src"] == "distinct":
            s = j["slot"]
            wid = k50.wid_of(s["member"], "D", T=s["token"], j=s["site"], n=s["k"], leg=s["leg"])   # o<k> = p<k> (N-P2)
            atoms = cells.get(wid, {}).get("atoms")
        else:
            wid = j["cell"]
            atoms = cells.get(wid, {}).get("atoms")
        if atoms is None:
            if subset is None and not (j["src"] == "distinct" and any(r["member"] == j["slot"]["member"] and
                                                                      r["token"] == j["slot"]["token"] and r["site"] ==
                                                                      j["slot"]["site"] and r["start"] == f"p{j['slot']['k']}"
                                                                      for r in rejected)):
                ck.fail("cell", f"{lab}: no cell built")
            continue
        if plant == "electrons" and lab == next((x["label"] for x in sps if x["src"] == "cell" and x["cell"] in cells), None):
            atoms = atoms.copy(); del atoms[[i for i, e in enumerate(atoms.get_chemical_symbols()) if e == "H"][0]]
        labels.append(lab)
        if _write_sp(ck, out_dir, lab, atoms, dopant=j.get("dopant"), cell={"work_id": wid, "dry_run": True}):
            written[j.get("cat")] += 1
    # ---- A2 inputs of the start set (C2, C4), nstep pending the smoke tests
    a2 = []
    for camp, labs in (("c2", k50.c2_labels(st)), ("c4", k50.c4_labels(st))):
        for lab in labs:
            a = k50.a1_of_a2(lab)
            if a["member"] not in members or not keep(a["member"], a["j"]):
                continue
            reg = regions[(a["member"], a["j"])]
            if a["cell_kind"] == "host":
                atoms, free = ctx[a["member"]].host, reg["free"]
            else:
                c = cells.get(a["a1"])
                if c is None:
                    ck.fail("cell", f"{lab}: its A1 start {a['a1']} was not built"); continue
                atoms, free = c["atoms"], c["free"]
            labels.append(lab)
            if _write_relax(ck, out_dir, camp + "_a2", lab, atoms, free, PLACEHOLDER_NSTEP, q47.RANKS_A2_DEFAULT, camp):
                a2.append(lab); written[f"a2_{camp}"] += 1
    # ---- reference inputs: smoke tests and throughput row (section 16)
    rc = c46.ref_context()
    rreg = c46.build_region(rc.host, "ref233", 136)
    ref = read(os.path.join(ROOT, c46.REF_VAC))
    rfree = c46.free_in_cell(rreg, "V")
    for lab, nstep, ranks in (("s2smoke_ref232_n1", 1, 48), ("s2smoke_ref232_n3", 3, 48), ("s2smoke_ref232_rst", 3, 48),
                              ("s2tp_ref232_np48", 5, 48), ("s2tp_ref232_np64", 5, 64), ("s2tp_ref232_np32a", 5, 32),
                              ("s2tp_ref232_np32b", 5, 32)):
        labels.append(lab)
        p1 = _write_relax(ck, out_dir, "ref", lab, ref, rfree, nstep, ranks, "c1")
        if p1:
            written["ref"] += 1
            if lab == "s2smoke_ref232_rst":
                r = q47.restart_input(p1, p1.replace(".in", ".p2.in"), 2)
                ck("restart input", r["restart_mode"] == "restart" and r["nstep"] == 2, r)
    if plant == "degauss":
        f = next(os.path.join(out_dir, "c1_sp", x, f"{x}.in") for x in labels if os.path.isdir(os.path.join(out_dir, "c1_sp", x)))
        t = re.sub(r"(degauss\s*=\s*)\S+", r"\g<1>0.01", open(f).read(), count=1)
        open(f, "w").write(t)
        check_input(ck, f, os.path.basename(os.path.dirname(f)), "sp", read_cell_for(cells, g1, jobs, os.path.basename(os.path.dirname(f))))
    if plant == "duplicate":
        labels.append(labels[0])
    # ---- labels
    for lab in labels:
        try:
            c46.check_label(lab); ok = True
        except Exception as e:                                          # noqa: BLE001
            ok = False; ck.fail("label", f"{lab}: {e}")
    dup = [x for x, n in collections.Counter(labels).items() if n > 1]
    ck("labels unique", not dup, dup)
    if subset is None:
        sl = set(labels)
        ck("plan label lists", set(c46.G1_LABELS) <= sl and set(c46.SPIN_LABELS) <= sl and set(k50.Q0_ROWS) <= sl
           and all(x in sl for x in k50.C2_ORDER) and len(k50.c4_labels(st)) == 26, "G1, spin, q = 0, C2, C4 lists")
        n_sp = sum(v for k, v in written.items() if k and k.startswith("sp_"))
        ck("inputs written", written["sp_g1"] == 5 and written["sp_spin"] == 2 and written["sp_noise"] == 106 and
           written["sp_step0"] == 2 and written["sp_q0"] == 10 and written["sp_pose"] <= 40 and
           written["a2_c2"] == 10 and written["a2_c4"] == 26 and written["ref"] == 7, dict(written))
    ok_mace = "mace" not in sys.modules
    ck("no model", ok_mace, "'mace' imported")
    summary = {"schema": "s2-preflight-1", "plan": "S2_PLAN.md section 17 item 4 (sections 5-11, 16)",
               "members": list(members), "subset": {k: sorted(v) for k, v in subset.items()} if subset else None,
               "partners": "unrelaxed", "stand_ins": NOTES["N-P1"],
               "stage0": {"source": st["stage0"]["source"], "m05_cal": st["stage0"]["m05_cal"],
                          "pbcl_decision": (st["stage0"].get("pbcl") or {}).get("decision"),
                          "allow_provisional": bool(allow_provisional),
                          "shifted_cl_tag": (pbcl or {}).get("tag"), "pbcl_refusal": pbcl_err},
               "builder": {"BUILDER_VERSION": b42.BUILDER_VERSION, "GEOM_SHA": b42.GEOM_SHA},
               "graph_counts": g["counts"], "inputs_written": dict(written),
               "single_points": sum(v for k, v in written.items() if k and k.startswith("sp_")),
               "a2_inputs": len(a2), "a2_nstep": {"value": PLACEHOLDER_NSTEP, "status": "pending smoke tests (X-3)"},
               "cells_built": len(cells), "pairs_built": sum(1 for r in pairs.values() if r["status"] == "built"),
               "pairs_rejected_nondefault": rejected, "region_ids": ids,
               "checks": dict(ck.counts), "failures": ck.failures, "passed": not ck.failures,
               "mocked": MOCKED, "notes": sorted(NOTES), "mace_imported": not ok_mace,
               "wall_s": round(time.time() - t0, 1), "date": time.strftime("%Y-%m-%d"), "written": k50.utc()}
    if log:
        k50.write_json({"summary": summary, "out_dir": os.path.abspath(out_dir), "labels": labels}, log)
    return summary


def read_cell_for(cells, g1, jobs, label):
    j = next(x for x in jobs if x["kind"] == "sp" and x["label"] == label)
    return g1[j["g1"]] if j["src"] == "g1" else cells[j["cell"]]["atoms"]


# ---------------------------------------------------------------- self-test (interface spec 9.6)
def self_test(work=None):
    t0 = time.time()
    results = []

    def case(name, fn):
        t = time.time()
        try:
            msg = fn()
            results.append((name, True)); print(f"PASS {name}: {msg}  [{time.time() - t:.1f} s]", flush=True)
        except Exception as e:                                          # noqa: BLE001
            results.append((name, False)); print(f"FAIL {name}: {type(e).__name__}: {e}  [{time.time() - t:.1f} s]", flush=True)
            traceback.print_exc(limit=5)

    for m in MOCKED:
        print(f"MOCKED {m}")
    print("NOTES: " + ", ".join(sorted(NOTES)))
    base = tempfile.mkdtemp(prefix="s2pre_", dir=work)
    S30 = c46.site_sets(c46.host_context("m30"))
    sub = {"m30": sorted(set(int(x) for x in S30["B"]["far4"]) | set(c46.CAL_SITES["m30"].values()))}
    runs = {}

    def run(name, **kw):
        if name not in runs:
            runs[name] = preflight(os.path.join(base, name), members=("m30",), subset=sub, allow_provisional=True,
                                   log=os.path.join(base, f"{name}.log.json"), **kw)
        return runs[name]

    def c_clean():
        s = run("clean")
        assert s["passed"], s["failures"]
        return (f"m30 B noise sites and the m30 start set: {s['cells_built']} cells, {s['single_points']} single points, "
                f"{s['a2_inputs']} A2 inputs, 7 reference inputs, checks {sum(s['checks'].values())}, no failure")

    def planted(name, key):
        s = run(name, plant=name)
        hit = [f for f in s["failures"] if f["check"] == key]
        assert hit, (key, s["failures"])
        return f"planted {name}: caught by '{key}' ({len(s['failures'])} failure(s))"

    case("pre-flight on a subset (no error planted)", c_clean)
    case("planted: wrong electron count", lambda: planted("electrons", "writer refused"))
    case("planted: duplicated label", lambda: planted("duplicate", "labels unique"))
    case("planted: region id differing from its site's", lambda: planted("region_id", "region id of the site"))
    case("planted: changed degauss", lambda: planted("degauss", "writer output"))
    case("planted: shifted Cl start without the Pb-Cl record", lambda: planted("cl_without_record", "shifted Cl start"))

    def c_electrons():
        got = {lab: electrons_expected(lab) for lab in ("s2_m30_host", "s2_m30_VB136", "s2_m30_VB136_q0",
                                                        "s2_m30_Cs128o0_novac", "s2_m30_GA128o0_vac",
                                                        "s2_m30_Cl138o0_vac_q0", "s2tp_ref232_np48")}
        want = {"s2_m30_host": (0, 1070), "s2_m30_VB136": (1, 1062), "s2_m30_VB136_q0": (0, 1063),
                "s2_m30_Cs128o0_novac": (0, 1060), "s2_m30_GA128o0_vac": (1, 1068), "s2_m30_Cl138o0_vac_q0": (0, 1063),
                "s2tp_ref232_np48": (1, 1062)}
        assert got == want, got
        return "the label rule of sections 6 and 10 (host 1070, V 1062, _q0 1063; Cs -10, GA +6, Cl 0)"
    case("electron rule", c_electrons)
    ok = "mace" not in sys.modules
    print(f"{'PASS' if ok else 'FAIL'} no-model: 'mace' {'not ' if ok else ''}in sys.modules; test files in {base}")
    results.append(("no-model", ok))
    nf = sum(not x for _, x in results)
    print(f"SELF-TEST {'PASS' if not nf else 'FAIL'} ({len(results)} cases, {nf} failed, {time.time() - t0:.0f} s)")
    return 1 if nf else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="S2 pre-flight (results/objective2/s2/S2_PLAN.md section 17 item 4)")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--work", default=None, help="self-test: parent of its temporary directory")
    sp = ap.add_subparsers(dest="cmd")
    r = sp.add_parser("run")
    r.add_argument("--out", required=True, help="directory for the dry-run inputs (outside the repository)")
    r.add_argument("--allow-provisional", action="store_true")
    r.add_argument("--summary", default=None, help=f"path-free summary (e.g. {SUMMARY})")
    r.add_argument("--log", default=None, help="full log (outside the repository)")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test(a.work)
    if a.cmd != "run":
        ap.print_help(); return 2
    out = os.path.abspath(a.out)
    if out == ROOT or out.startswith(ROOT + os.sep):
        ap.error("the dry-run inputs are written outside the repository")
    if a.log and os.path.abspath(a.log).startswith(ROOT + os.sep):
        ap.error("the full log is written outside the repository")
    s = preflight(out, allow_provisional=a.allow_provisional, log=a.log)
    if a.summary:
        c46.dump_public(s, a.summary)
    print(json.dumps({k: s[k] for k in ("passed", "graph_counts", "inputs_written", "single_points", "a2_inputs",
                                        "cells_built", "pairs_built", "failures", "wall_s")}, indent=1))
    assert "mace" not in sys.modules
    print("no-model: 'mace' not in sys.modules")
    return 0 if s["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

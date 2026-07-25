#!/usr/bin/env python3
"""Generate Quantum ESPRESSO pw.x inputs for the gamma-CsPbI3 V_I fixed-path benchmark.

This is the *reproducible* replacement for the ad-hoc inputs that produced the
first DFT benchmark (results/objective1/dft_benchmark.json). Given the frozen
MACE-relaxed NEB band (results/objective1/regression_saddle_path.extxyz, 7 images,
159 atoms Cs32Pb32I95), it writes single-point SCF inputs for any image, charge
state, and spin treatment, with all method parameters exposed as flags.

Physics of the two charge states (see EXECUTION_GUIDE Part 5.1):
  * q=0  -> 1401 valence electrons (Cs*9 + Pb*14 + I*7 = 288+448+665) -> ODD.
           This is the NEUTRAL iodine vacancy V_I^0 (a neutral I atom removed).
           An odd electron count is open-shell: nspin=1 (closed shell) is NOT the
           safe default -> the Stage 1.1 spin scan (Case A/B/C).
  * q=+1 -> 1400 electrons -> EVEN. The +1 vacancy V_I^+ (an I^- ion removed).
           QE adds a uniform neutralising background; the barrier E(saddle)-E(init)
           is background-independent (same cell+charge at both geometries).

Spin-scan cases for q=0 (EXECUTION_GUIDE 1.1):
  A  non-spin  : nspin=1 (the original benchmark reference)
  B  open-shell: nspin=2, tot_magnetization=1 (one unpaired electron, delocalised guess)
  C  localised : nspin=2, starting_magnetization seeded on the two under-coordinated
                 Pb atoms flanking the vacancy (Pb-Pb dimer polaron guess)

Pseudopotentials (pslibrary 1.0.0 US scalar-relativistic PBE), on ehpc in $HOME/pseudo:
  Cs.pbe-spn-rrkjus_psl.1.0.0.UPF (z=9)   <- spn, NOT spnl (spnl has corrupt z_valence)
  Pb.pbe-dn-rrkjus_psl.1.0.0.UPF  (z=14)
  I.pbe-n-rrkjus_psl.1.0.0.UPF    (z=7)

Usage:
  # reproduce the 8 original benchmark SCFs (img 0/2/3/4 x q=0/+1, non-spin):
  python scripts/05_generate_qe_inputs.py benchmark   --outdir ehpc/inputs
  # Stage 1.1 spin scan (img0/img3, q=0 cases A/B/C + q=+1 localisation check):
  python scripts/05_generate_qe_inputs.py spin_scan   --outdir ehpc/inputs
  # complete the fixed path (missing images 1,5,6 at q=0 and q=+1, non-spin):
  python scripts/05_generate_qe_inputs.py all_images  --outdir ehpc/inputs
  # single custom input:
  python scripts/05_generate_qe_inputs.py one --image 3 --charge 1 --nspin 2 \
      --tot-magnetization 1 --ecutwfc 60 --degauss 0.005 --outdir ehpc/inputs

Each input is self-describing: a header comment block records image, charge, spin
treatment, cutoffs, smearing, k-points and the geometry-source SHA256, so an input
file alone is enough to know exactly what it computes.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from ase.io import read

ROOT = Path(__file__).resolve().parent.parent
BAND = ROOT / "results" / "objective1" / "regression_saddle_path.extxyz"

# pslibrary 1.0.0 US scalar-relativistic PBE — filenames as staged on ehpc:$HOME/pseudo
PSEUDO = {
    "Cs": ("Cs.pbe-spn-rrkjus_psl.1.0.0.UPF", 132.90545, 9),
    "Pb": ("Pb.pbe-dn-rrkjus_psl.1.0.0.UPF", 207.2, 14),
    "I":  ("I.pbe-n-rrkjus_psl.1.0.0.UPF", 126.90447, 7),
}
DEFAULT_PSEUDO_DIR = "$HOME/pseudo"

# Original benchmark set (results/objective1/dft_benchmark.json)
BENCH_IMAGES = [0, 2, 3, 4]
ALL_IMAGES = [0, 1, 2, 3, 4, 5, 6]  # 7-image band; benchmark did 0/2/3/4 -> 1/5/6 missing


def band_sha256():
    return hashlib.sha256(BAND.read_bytes()).hexdigest()


def load_image(i):
    return read(str(BAND), index=i)


def under_coordinated_pb(atoms, cutoff=3.8):
    """Pb atoms with <6 iodine neighbours = the atoms flanking the V_I site.
    These carry the neutral-vacancy odd electron (Pb-Pb dimer polaron), so they
    are where Case C seeds the initial spin density."""
    sym = np.array(atoms.get_chemical_symbols())
    pb_idx = np.flatnonzero(sym == "Pb")
    i_idx = np.flatnonzero(sym == "I")
    out = []
    for p in pb_idx:
        if (atoms.get_distances(p, i_idx, mic=True) < cutoff).sum() < 6:
            out.append(int(p))
    return out


def compute_nelec(atoms, charge):
    from collections import Counter
    c = Counter(atoms.get_chemical_symbols())
    n = sum(c[el] * PSEUDO[el][2] for el in c)
    return n - charge


def write_pw_input(atoms, out_path, *, prefix, charge=0, nspin=1,
                   tot_magnetization=None, localize_pb=None, localize_mag=0.5,
                   ecutwfc=50.0, ecutrho=400.0, degauss=0.01, smearing="gaussian",
                   kpoints=(1, 1, 1), conv_thr=1e-6, pseudo_dir=DEFAULT_PSEUDO_DIR,
                   mixing_beta=0.3, electron_maxstep=200, case_label="",
                   calculation="scf", d3=False, dftd3_version=4, nosym=False,
                   forc_conv_thr=7.8e-4, nstep=200,
                   mixing_mode="plain", trust_radius_ini=0.1):
    """Write one pw.x input (scf or relax). Returns a metadata dict.

    localize_pb : list of atom indices to relabel as a distinct species 'Pb1' and
                  seed with starting_magnetization=localize_mag (Case C). Requires
                  nspin=2. Other species get starting_magnetization tiny/zero.
    calculation : 'scf' or 'relax' (fixed-cell ionic relaxation; NEVER vc-relax here).
    d3          : if True add Grimme-D3 via vdw_corr='dft-d3' with dftd3_version
                  (4 = D3-BJ Becke-Johnson damping; 3 = D3 zero-damping). This is a
                  post-SCF total-ENERGY + FORCE correction, not a change to the SCF
                  potential.
    nosym       : if True set nosym=.true. and noinv=.true. -- do NOT let QE's
                  auto-symmetry constrain a vacancy/charged/spin-polarized cell's
                  local distortion or spin density.
    forc_conv_thr: relax force threshold in Ry/Bohr (7.8e-4 = 0.0201 eV/A).
    """
    atoms = atoms.copy()
    symbols = list(atoms.get_chemical_symbols())

    # species table (ordered) — split Pb into Pb/Pb1 for localisation if requested
    localize_pb = set(localize_pb or [])
    if localize_pb:
        assert nspin == 2, "localised starting_magnetization needs nspin=2"
        labels = [("Pb1" if (s == "Pb" and idx in localize_pb) else s)
                  for idx, s in enumerate(symbols)]
    else:
        labels = symbols
    species_order = []
    for lab in labels:
        if lab not in species_order:
            species_order.append(lab)

    def base_el(lab):
        return "Pb" if lab == "Pb1" else lab

    ntyp = len(species_order)
    nat = len(atoms)
    nelec = compute_nelec(atoms, charge)

    # namelists
    sys_lines = [
        "    ibrav = 0",
        f"    nat = {nat}",
        f"    ntyp = {ntyp}",
        f"    ecutwfc = {ecutwfc}",
        f"    ecutrho = {ecutrho}",
        "    occupations = 'smearing'",
        f"    smearing = '{smearing}'",
        f"    degauss = {degauss}",
    ]
    if charge:
        sys_lines.append(f"    tot_charge = {charge}")
    if d3:
        sys_lines.append("    vdw_corr = 'dft-d3'")
        sys_lines.append(f"    dftd3_version = {dftd3_version}")
    if nosym:
        sys_lines.append("    nosym = .true.")
        sys_lines.append("    noinv = .true.")
    if nspin == 2:
        sys_lines.append("    nspin = 2")
        if tot_magnetization is not None:
            sys_lines.append(f"    tot_magnetization = {tot_magnetization}")
        # starting_magnetization per species index (1-based)
        for k, lab in enumerate(species_order, start=1):
            if lab == "Pb1":
                sys_lines.append(f"    starting_magnetization({k}) = {localize_mag}")
            else:
                sys_lines.append(f"    starting_magnetization({k}) = 0.0")

    header = [
        f"! gamma-CsPbI3 2x2x2 V_I fixed-path SCF  |  prefix={prefix}",
        f"! prefix={prefix}  charge=+{charge}  "
        f"nspin={nspin}  case={case_label or 'A'}  calc={calculation}{'  +D3(BJ)' if d3 else ''}",
        f"! nelec={nelec}  ({'ODD -> V_I^0 open-shell' if nelec % 2 else 'EVEN -> V_I^+ closed-shell'})",
        f"! ecutwfc={ecutwfc} ecutrho={ecutrho} degauss={degauss} smearing={smearing} "
        f"kpts={kpoints[0]}x{kpoints[1]}x{kpoints[2]}",
        f"! geometry: regression_saddle_path.extxyz  sha256={band_sha256()[:16]}...",
        f"! pseudo: pslibrary 1.0.0 US scalar-rel PBE",
        "",
    ]

    txt = "\n".join(header)
    txt += "&control\n"
    txt += f"    calculation = '{calculation}'\n"
    txt += f"    prefix = '{prefix}'\n"
    txt += "    verbosity = 'high'\n"
    txt += "    tprnfor = .true.\n"
    txt += "    tstress = .false.\n"
    if calculation == "relax":
        txt += f"    forc_conv_thr = {forc_conv_thr}\n"
        txt += f"    nstep = {nstep}\n"
    txt += f"    pseudo_dir = '{pseudo_dir}'\n"
    txt += "    outdir = './out'\n"
    txt += "/\n"
    txt += "&system\n" + "\n".join(sys_lines) + "\n/\n"
    txt += "&electrons\n"
    txt += f"    conv_thr = {conv_thr}\n"
    txt += f"    mixing_beta = {mixing_beta}\n"
    txt += f"    electron_maxstep = {electron_maxstep}\n"
    if mixing_mode != "plain":
        # local-TF (Thomas-Fermi screened) mixing suppresses charge-sloshing in large
        # inhomogeneous defect supercells — the odd-electron q0 cell was taking 30+ SCF
        # iterations/ionic-step with plain mixing; local-TF converges far faster.
        txt += f"    mixing_mode = '{mixing_mode}'\n"
    txt += "/\n"
    if calculation == "relax":
        txt += "&ions\n"
        txt += "    ion_dynamics = 'bfgs'\n"
        # larger initial trust radius so BFGS doesn't collapse to micro-steps from a
        # MACE-pre-relaxed start; bfgs_ndim=3 uses more history for a better step.
        txt += f"    trust_radius_ini = {trust_radius_ini}\n"
        txt += "    bfgs_ndim = 3\n"
        txt += "/\n"

    txt += "ATOMIC_SPECIES\n"
    for lab in species_order:
        el = base_el(lab)
        fname, mass, _ = PSEUDO[el]
        txt += f"  {lab:4s} {mass:10.5f}  {fname}\n"

    txt += "CELL_PARAMETERS angstrom\n"
    for v in atoms.cell.array:
        txt += f"  {v[0]:18.12f} {v[1]:18.12f} {v[2]:18.12f}\n"

    txt += "ATOMIC_POSITIONS angstrom\n"
    for lab, p in zip(labels, atoms.positions):
        txt += f"  {lab:4s} {p[0]:18.12f} {p[1]:18.12f} {p[2]:18.12f}\n"

    txt += "K_POINTS automatic\n"
    txt += f"  {kpoints[0]} {kpoints[1]} {kpoints[2]} 0 0 0\n"

    out_path = Path(out_path)
    out_path.write_text(txt)
    def _img_from_prefix(pfx):
        import re
        m = re.search(r"img(\d+)", pfx)
        if m:
            return int(m.group(1))
        # relax endpoints: initial->img0, final->img6 (the two path endpoints)
        if "initial" in pfx:
            return 0
        if "final" in pfx:
            return 6
        return -1
    meta = {"prefix": prefix, "file": out_path.name, "image": _img_from_prefix(prefix),
            "charge": charge, "nspin": nspin, "tot_magnetization": tot_magnetization,
            "localize_pb": sorted(localize_pb), "nelec": nelec, "ecutwfc": ecutwfc,
            "ecutrho": ecutrho, "degauss": degauss, "smearing": smearing,
            "kpoints": list(kpoints), "conv_thr": conv_thr, "case": case_label or "A",
            "calculation": calculation, "d3": bool(d3),
            "dftd3_version": (dftd3_version if d3 else None),
            "nosym": bool(nosym), "mixing_mode": mixing_mode, "mixing_beta": mixing_beta,
            "forc_conv_thr": (forc_conv_thr if calculation == "relax" else None),
            "trust_radius_ini": (trust_radius_ini if calculation == "relax" else None),
            "geometry_sha256": band_sha256()}
    return meta


def gen_benchmark(outdir, **kw):
    """The original 8 SCFs: img 0/2/3/4 x q=0/+1, non-spin (reproduce dft_benchmark.json)."""
    metas = []
    for img in BENCH_IMAGES:
        atoms = load_image(img)
        for q in (0, 1):
            prefix = f"img{img}_q{q}"
            m = write_pw_input(atoms, Path(outdir) / f"{prefix}.in", prefix=prefix,
                               charge=q, nspin=1, case_label="A", **kw)
            metas.append(m)
    return metas


def gen_spin_scan(outdir, **kw):
    """Stage 1.1: q=0 img0/img3 cases A/B/C + q=+1 img0/img3 localisation check."""
    metas = []
    for img in (0, 3):
        atoms = load_image(img)
        pb_loc = under_coordinated_pb(atoms)
        # q=0 Case A (non-spin), B (open-shell delocalised), C (localised)
        metas.append(write_pw_input(atoms, Path(outdir) / f"img{img}_q0_A.in",
                     prefix=f"img{img}_q0_A", charge=0, nspin=1, case_label="A", **kw))
        metas.append(write_pw_input(atoms, Path(outdir) / f"img{img}_q0_B.in",
                     prefix=f"img{img}_q0_B", charge=0, nspin=2, tot_magnetization=1,
                     case_label="B", **kw))
        metas.append(write_pw_input(atoms, Path(outdir) / f"img{img}_q0_C.in",
                     prefix=f"img{img}_q0_C", charge=0, nspin=2, tot_magnetization=1,
                     localize_pb=pb_loc, case_label="C", **kw))
        # q=+1 localisation check (even electrons; test spin-polarised vs non-spin)
        metas.append(write_pw_input(atoms, Path(outdir) / f"img{img}_q1_A.in",
                     prefix=f"img{img}_q1_A", charge=1, nspin=1, case_label="A", **kw))
        metas.append(write_pw_input(atoms, Path(outdir) / f"img{img}_q1_B.in",
                     prefix=f"img{img}_q1_B", charge=1, nspin=2, tot_magnetization=0,
                     case_label="B", **kw))
    return metas


def gen_all_images(outdir, **kw):
    """Complete the fixed path: the images the benchmark skipped (1,5,6), q=0 and q=+1."""
    metas = []
    missing = [i for i in ALL_IMAGES if i not in BENCH_IMAGES]
    for img in missing:
        atoms = load_image(img)
        for q in (0, 1):
            prefix = f"img{img}_q{q}"
            metas.append(write_pw_input(atoms, Path(outdir) / f"{prefix}.in", prefix=prefix,
                         charge=q, nspin=1, case_label="A", **kw))
    return metas


# Stage-2 production degauss LOCKED at 0.005 Ry (convergence gate: 0.01 shifted the q0
# barrier 15.8 meV — not converged; see CONVERGENCE_GATE.md). Relax/NEB modes use this.
PRODUCTION_DEGAUSS = 0.005


def _spin_kw(q):
    """Stage-1-locked spin/charge setting per charge state."""
    if q == 0:
        return dict(charge=0, nspin=2, tot_magnetization=1, case_label="B")  # odd e- open-shell
    return dict(charge=1, nspin=1, case_label="A")                            # even e- closed-shell


def gen_d3_baseline(outdir, **kw):
    """PBE+D3(BJ) single-points on img0+img3 for q=0 (spin) and q=+1 -- the NEW
    consistent baseline table to compare against old bare-PBE + simple-dftd3 estimate."""
    metas = []
    for q in (0, 1):
        sk = _spin_kw(q)
        for img in (0, 3):
            atoms = load_image(img)
            prefix = f"d3base_img{img}_q{q}"
            metas.append(write_pw_input(atoms, Path(outdir) / f"{prefix}.in", prefix=prefix,
                         calculation="scf", d3=True, nosym=True, **{k: v for k, v in sk.items() if k != "case_label"},
                         case_label=sk["case_label"], **kw))
    return metas


def gen_conv_gate(outdir, *, ecutwfc=50.0, ecutrho=400.0, degauss=0.01, kpoints=(1, 1, 1),
                  pseudo_dir=DEFAULT_PSEUDO_DIR):
    """Parameter-convergence sweep on img0+img3, q0 AND q1, all PBE+D3(BJ). One-variable
    perturbations from the baseline: ecutwfc 50->60, k Gamma->2x2x2, degauss 0.01->0.005.
    Barrier E(img3)-E(img0) per setting; any >~10 meV shift => baseline not converged."""
    variants = {
        "base":   dict(ecutwfc=50.0, ecutrho=400.0, degauss=0.01,  kpoints=(1, 1, 1)),
        "ecut60": dict(ecutwfc=60.0, ecutrho=480.0, degauss=0.01,  kpoints=(1, 1, 1)),
        "k222":   dict(ecutwfc=50.0, ecutrho=400.0, degauss=0.01,  kpoints=(2, 2, 2)),
        "dg005":  dict(ecutwfc=50.0, ecutrho=400.0, degauss=0.005, kpoints=(1, 1, 1)),
    }
    metas = []
    for vname, vk in variants.items():
        for q in (0, 1):
            sk = _spin_kw(q)
            for img in (0, 3):
                atoms = load_image(img)
                prefix = f"conv_{vname}_img{img}_q{q}"
                metas.append(write_pw_input(atoms, Path(outdir) / f"{prefix}.in", prefix=prefix,
                             calculation="scf", d3=True, nosym=True, pseudo_dir=pseudo_dir,
                             **{k: v for k, v in sk.items() if k != "case_label"},
                             case_label=sk["case_label"], **vk))
    return metas


def gen_relax_endpoints(outdir, tier="production", **kw):
    """Fixed-cell ionic relaxation of the 4 charge-state endpoints: q0/q1 x
    img0(initial)/img6(final). Stage-1-locked spin, PBE+D3(BJ), nosym.
    Production degauss=0.005 Ry (convergence-gate lock) unless overridden in kw.
    Uses local-TF mixing + mixing_beta=0.2 (charge-sloshing fix for the large
    odd-electron defect cell) and a 0.1 Bohr initial BFGS trust radius.

    Two tiers (the endpoint relaxation is a shallow, soft-mode surface — see
    CONVERGENCE_GATE / relaxation notes):
      * tier='explore'    : conv_thr=1e-6, fmax<=0.05 eV/A (1.945e-3 Ry/Bohr).
          Fast; endpoints good enough to seed the 3-image explore NEB + d_max check.
      * tier='production' : conv_thr=1e-8, fmax<=0.02 eV/A (7.8e-4 Ry/Bohr).
          Clean forces (QE flagged the 1e-6 noise floor); for the final CI-NEB endpoints.
    """
    kw.setdefault("degauss", PRODUCTION_DEGAUSS)
    if tier == "explore":
        # nstep=20 cap: this soft octahedral-tilt surface floors BFGS at fmax~0.04 eV/A
        # (energy-converged); it oscillates without formally hitting 0.05, so cap the ionic
        # steps and harvest the lowest-fmax geometry. 20 steps reaches the floor for all 4.
        conv_thr, forc_conv_thr, nstep = 1e-6, 1.945e-3, 20
        kw.setdefault("nstep", nstep)
    else:  # production
        conv_thr, forc_conv_thr = 1e-8, 7.8e-4
    metas = []
    for q in (0, 1):
        sk = _spin_kw(q)
        for img, role in ((0, "initial"), (6, "final")):
            atoms = load_image(img)
            prefix = f"relax_q{q}_{role}"
            metas.append(write_pw_input(atoms, Path(outdir) / f"{prefix}.in", prefix=prefix,
                         calculation="relax", d3=True, nosym=True,
                         mixing_mode="local-TF", mixing_beta=0.2, trust_radius_ini=0.1,
                         conv_thr=conv_thr, forc_conv_thr=forc_conv_thr,
                         **{k: v for k, v in sk.items() if k != "case_label"},
                         case_label=sk["case_label"], **kw))
    return metas


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["benchmark", "spin_scan", "all_images", "one",
                                    "d3_baseline", "conv_gate", "relax_endpoints"])
    p.add_argument("--outdir", default=str(ROOT / "ehpc" / "inputs"))
    p.add_argument("--ecutwfc", type=float, default=50.0)
    p.add_argument("--ecutrho", type=float, default=400.0)
    p.add_argument("--degauss", type=float, default=None,
                   help="Ry; default 0.005 for relax/neb production (conv-gate lock), 0.01 for legacy scf modes")
    p.add_argument("--kpoints", default="1,1,1")
    p.add_argument("--pseudo-dir", default=DEFAULT_PSEUDO_DIR)
    # 'one' mode
    p.add_argument("--image", type=int, default=0)
    p.add_argument("--charge", type=int, default=0)
    p.add_argument("--nspin", type=int, default=1)
    p.add_argument("--tot-magnetization", type=float, default=None)
    p.add_argument("--localize", action="store_true", help="Case C: localise on under-coord Pb")
    p.add_argument("--relax-tier", choices=["explore", "production"], default="production",
                   help="relax_endpoints tier: explore (1e-6, fmax<=0.05) or production (1e-8, fmax<=0.02)")
    args = p.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    kp = tuple(int(x) for x in args.kpoints.split(","))
    # degauss default: 0.005 Ry for production relax (conv-gate lock), 0.01 for legacy scf modes
    if args.degauss is not None:
        degauss = args.degauss
    elif args.mode == "relax_endpoints":
        degauss = PRODUCTION_DEGAUSS
    else:
        degauss = 0.01
    common = dict(ecutwfc=args.ecutwfc, ecutrho=args.ecutrho, degauss=degauss,
                  kpoints=kp, pseudo_dir=args.pseudo_dir)

    if args.mode == "benchmark":
        metas = gen_benchmark(outdir, **common)
    elif args.mode == "spin_scan":
        metas = gen_spin_scan(outdir, **common)
    elif args.mode == "all_images":
        metas = gen_all_images(outdir, **common)
    elif args.mode == "d3_baseline":
        metas = gen_d3_baseline(outdir, **common)
    elif args.mode == "conv_gate":
        metas = gen_conv_gate(outdir, pseudo_dir=args.pseudo_dir)  # sets its own ecut/k/degauss
    elif args.mode == "relax_endpoints":
        metas = gen_relax_endpoints(outdir, tier=args.relax_tier, **common)
    else:  # one
        atoms = load_image(args.image)
        loc = under_coordinated_pb(atoms) if args.localize else None
        prefix = f"img{args.image}_q{args.charge}_ns{args.nspin}"
        metas = [write_pw_input(atoms, outdir / f"{prefix}.in", prefix=prefix,
                 charge=args.charge, nspin=args.nspin,
                 tot_magnetization=args.tot_magnetization, localize_pb=loc, **common)]

    manifest = outdir / f"MANIFEST_{args.mode}.json"
    json.dump({"mode": args.mode, "geometry": str(BAND.relative_to(ROOT)),
               "geometry_sha256": band_sha256(), "n_inputs": len(metas),
               "inputs": metas}, open(manifest, "w"), indent=2)
    for m in metas:
        print(f"  wrote {m['file']:20s} img={m['image']} q=+{m['charge']} nspin={m['nspin']} "
              f"case={m['case']} nelec={m['nelec']}")
    print(f"[{args.mode}] {len(metas)} inputs -> {outdir}  (manifest: {manifest.name})")


if __name__ == "__main__":
    main()

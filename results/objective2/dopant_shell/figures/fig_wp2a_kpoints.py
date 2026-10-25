#!/usr/bin/env python
"""Figure WP2a: k-sampling for the det-20 FA host and the DFT residual force at a MACE minimum.

Claim: a single k-point at supercell (1/2,1/2,1/2) (the folded primitive R point) reproduces the
Gamma-centred 2x2x2 result for the path energy difference and the forces at ~1/6 of the cost,
while the MACE-relaxed endpoint is not a DFT stationary point; the residual force sits mainly
on the FA cation.

Data (all committed): QE outputs in ../wp2a_kpoints/*.out.gz (m30 undoped, MACE CI-NEB images 0
and 3, plain PBE, 50/400 Ry, Gaussian 0.005 Ry, nspin 1, 64 MPI ranks); frames from the corpus
band archive results/objective2/paired_pilot/corpus108/corpus108_new_bands.tar.gz; MACE-MP-0
medium (float64) for panel c. Each point is ONE deterministic DFT calculation (SCF conv_thr
1e-8 Ry): there is no replicate variability to show.

    python fig_wp2a_kpoints.py --build   # (re)extract source data; needs ase + mace
    python fig_wp2a_kpoints.py           # plot from source_data/*.csv
"""
import argparse, csv, gzip, io, os, re, sys, tarfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "wp2a_kpoints")
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SRC = os.path.join(HERE, "source_data")
RY, BOHR = 13.605693122994, 0.529177210903
MODES = [("gamma", "Γ only"), ("R", "R point (½,½,½)"), ("mp222", "2×2×2 (reference)")]


def parse(path):
    t = gzip.open(path, "rt").read()
    assert "JOB DONE" in t and "convergence has been achieved" in t, path
    F = float(re.findall(r"^!\s+total energy\s+=\s+([-\d.]+)\s+Ry", t, re.M)[-1]) * RY
    mts = float(re.findall(r"smearing contrib\. \(-TS\)\s+=\s+([-\d.]+)", t)[-1]) * RY
    blk = re.search(r"Forces acting on atoms.*?\n\n(.*?)\n\n", t, re.S).group(1)
    f = np.array(re.findall(r"force =\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)", blk), float) * RY / BOHR
    wall = re.search(r"PWSCF\s+:.*?CPU\s+(.*?)\s+WALL", t).group(1)
    mins = sum(float(x) * {"h": 60, "m": 1, "s": 1 / 60}[u] for x, u in re.findall(r"([\d.]+)([hms])", wall))
    nk = int(re.search(r"number of k points=\s+(\d+)", t).group(1))
    return F, mts, f, mins, nk


def build():
    from ase.io import read
    rows, atoms_rows = [], []
    R = {(i, k): parse(os.path.join(RAW, f"kconv_m30u_img{i}_{k}.out.gz")) for i in (0, 3) for k, _ in MODES}
    ref = {i: R[(i, "mp222")] for i in (0, 3)}
    for k, lab in MODES:
        dE = (R[(3, k)][0] - R[(0, k)][0]) * 1000
        frms = [float(np.sqrt(np.mean((R[(i, k)][2] - ref[i][2]) ** 2))) * 1000 for i in (0, 3)]
        rows.append({"sampling": k, "label": lab, "nk": R[(0, k)][4],
                     "E3_minus_E0_meV": round(dE, 2),
                     "dE_vs_mp222_meV": round(dE - (ref[3][0] - ref[0][0]) * 1000, 2),
                     "force_rms_dev_vs_mp222_img0_meV_per_A": round(frms[0], 2),
                     "force_rms_dev_vs_mp222_img3_meV_per_A": round(frms[1], 2),
                     "wall_min_img0": round(R[(0, k)][3], 2), "wall_min_img3": round(R[(3, k)][3], 2),
                     "mTS_img0_meV": round(R[(0, k)][1] * 1000, 1), "mTS_img3_meV": round(R[(3, k)][1] * 1000, 1)})
    # panel c: per-atom |F_DFT| (R point) at the MACE-relaxed endpoint (img0); |F_MACE| and
    # |F_MACE - F_DFT| are kept in the source data (MACE forces there are <= 0.017 eV/A)
    tf = tarfile.open(os.path.join(REPO, "results/objective2/paired_pilot/corpus108/corpus108_new_bands.tar.gz"))
    name = [m for m in tf.getnames() if m.endswith("band_undoped_m30.extxyz")][0]
    at = read(io.StringIO(tf.extractfile(name).read().decode()), index=0, format="extxyz")
    from mace.calculators import mace_mp
    at.calc = mace_mp(model="medium", device="cpu", default_dtype="float64")
    fm = at.get_forces()
    fd = R[(0, "R")][2]
    assert len(fd) == len(at)
    for i, (s, a, b) in enumerate(zip(at.get_chemical_symbols(), fm, fd)):
        atoms_rows.append({"atom": i, "element": s, "abs_dF_eV_per_A": round(float(np.linalg.norm(a - b)), 5),
                           "abs_F_DFT_eV_per_A": round(float(np.linalg.norm(b)), 5),
                           "abs_F_MACE_eV_per_A": round(float(np.linalg.norm(a)), 5)})
    os.makedirs(SRC, exist_ok=True)
    for fn, data in (("wp2a_kpoints.csv", rows), ("wp2a_atom_force_error.csv", atoms_rows)):
        with open(os.path.join(SRC, fn), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0])); w.writeheader(); w.writerows(data)
    print("source data written")


def plot():
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    sys.path.insert(0, os.path.expanduser("~/.claude/skills/nature-figure/scripts"))
    try:      # layout QA from the nature-figure toolkit; optional, it does not touch the data
        from audit_panel_alignment import require_matplotlib_panel_alignment
    except ImportError:
        require_matplotlib_panel_alignment = None
        print("note: panel-alignment audit unavailable; figure rendered without it")
    mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                         "svg.fonttype": "none", "pdf.fonttype": 42, "font.size": 7,
                         "axes.spines.right": False, "axes.spines.top": False, "axes.linewidth": 0.8,
                         "legend.frameon": False, "xtick.major.width": 0.8, "ytick.major.width": 0.8})
    K = list(csv.DictReader(open(os.path.join(SRC, "wp2a_kpoints.csv"))))
    A = list(csv.DictReader(open(os.path.join(SRC, "wp2a_atom_force_error.csv"))))
    NEU, SIG, ACC = "#9aa3ad", "#2f6db5", "#c4553a"           # neutral / chosen / reference
    col = {"gamma": NEU, "R": SIG, "mp222": "#4d4d4d"}

    fig, ax = plt.subplots(1, 3, figsize=(183 / 25.4, 58 / 25.4))
    fig.subplots_adjust(left=0.075, right=0.985, bottom=0.20, top=0.86, wspace=0.42)

    # (a) path energy difference E3 - E0: deviation from the 2x2x2 reference (dot plot, true zero)
    a = ax[0]
    for i, r in enumerate(K):
        d = float(r["dE_vs_mp222_meV"])
        a.plot([i, i], [0, d], color=col[r["sampling"]], lw=1.2, zorder=2)
        a.scatter(i, d, s=26, color=col[r["sampling"]], zorder=3, edgecolor="white", linewidth=0.4)
        a.text(i, d + (0.35 if d >= 0 else -0.35), f'{float(r["E3_minus_E0_meV"]):.1f} meV',
               ha="center", va="bottom" if d >= 0 else "top", fontsize=6, color=col[r["sampling"]])
    a.axhline(0, color="#4d4d4d", lw=0.6)
    a.set_xlim(-0.6, 2.6); a.set_ylim(-4, 2)
    a.set_xticks(range(len(K)), ["Γ", "R", "2×2×2"])
    a.set_ylabel("Δ[F(img 3) − F(img 0)] vs 2×2×2 (meV)")
    a.set_title("Path energy difference", fontsize=7, pad=4)

    # (b) force deviation from 2x2x2 versus wall time
    b = ax[1]
    for r in K[:2]:
        cc = col[r["sampling"]]
        b.scatter(float(r["wall_min_img0"]), float(r["force_rms_dev_vs_mp222_img0_meV_per_A"]), s=20, marker="o",
                  color=cc, zorder=3, edgecolor="white", linewidth=0.4)
        b.scatter(float(r["wall_min_img3"]), float(r["force_rms_dev_vs_mp222_img3_meV_per_A"]), s=34, marker="s",
                  facecolor="none", edgecolor=cc, linewidth=0.9, zorder=4)
        top = max(float(r["force_rms_dev_vs_mp222_img0_meV_per_A"]), float(r["force_rms_dev_vs_mp222_img3_meV_per_A"]))
        b.annotate(r["label"].split(" (")[0], (float(r["wall_min_img0"]), top), xytext=(7, 3),
                   textcoords="offset points", fontsize=6, color=cc)
    tref = (float(K[2]["wall_min_img0"]) + float(K[2]["wall_min_img3"])) / 2
    b.axvline(tref, color="#4d4d4d", lw=0.6, ls=(0, (3, 2)))
    b.text(tref * 0.93, 7.6, "2×2×2\nreference", ha="right", va="top", fontsize=6, color="#4d4d4d")
    assert all(float(r[k]) > 0 for r in K for k in ("wall_min_img0", "wall_min_img3"))  # log axis
    b.set_xscale("log"); b.set_xlim(2, 60); b.set_ylim(0, 8)
    b.xaxis.set_major_locator(mpl.ticker.FixedLocator([2, 5, 10, 20, 50]))
    b.xaxis.set_major_formatter(mpl.ticker.FixedFormatter(["2", "5", "10", "20", "50"]))
    b.xaxis.set_minor_formatter(mpl.ticker.NullFormatter())
    b.set_xlabel("Wall time per single point (min, 64 ranks)")
    b.set_ylabel("Force RMS deviation from 2×2×2 (meV/Å)")
    b.scatter([], [], marker="o", color="#777777", s=16, label="Image 0")
    b.scatter([], [], marker="s", facecolor="none", edgecolor="#777777", s=26, linewidth=0.9, label="Image 3")
    b.legend(loc="lower left", fontsize=6, handletextpad=0.2, borderaxespad=0.2)
    b.set_title("Force convergence vs cost", fontsize=7, pad=4)

    # (c) per-atom residual DFT force |F_DFT| at the MACE-relaxed endpoint (R point)
    c = ax[2]
    order = ["Pb", "I", "Cs", "C", "N", "H"]
    rng = np.random.default_rng(0)                             # horizontal jitter only; values untouched
    labels = []
    for i, el in enumerate(order):
        v = np.array([float(r["abs_F_DFT_eV_per_A"]) for r in A if r["element"] == el])
        c.scatter(i + rng.uniform(-0.22, 0.22, v.size), v, s=3, color=SIG if el in ("C", "N", "H") else NEU,
                  alpha=0.8, linewidth=0, zorder=2)
        rms = float(np.sqrt(np.mean(v ** 2)))
        c.plot([i - 0.32, i + 0.32], [rms, rms], color="#1a1a1a", lw=1.0, zorder=3)
        labels.append(f"{el}\n({v.size})")
    for yv in (0.2, 0.05):                                     # criterion 5: max < 0.2, RMS < 0.05 eV/A
        c.axhline(yv, color=ACC, lw=0.6, ls=(0, (3, 2)), zorder=1)
    allv = np.array([float(r["abs_F_DFT_eV_per_A"]) for r in A])
    c.text(0.02, 0.98, f"all {allv.size} atoms: RMS {np.sqrt(np.mean(allv ** 2)):.3f}, max {allv.max():.3f}",
           transform=c.transAxes, ha="left", va="top", fontsize=6)
    c.text(0.02, 0.905, "gate (dashed): RMS < 0.05, max < 0.2", transform=c.transAxes, ha="left", va="top",
           fontsize=6, color=ACC)
    c.set_xticks(range(len(order)), labels)
    c.set_xlim(-0.55, 5.55); c.set_ylim(0, 0.46)
    c.set_ylabel("Residual DFT force per atom (eV/Å)")
    c.set_title("DFT force at a MACE minimum", fontsize=7, pad=4)

    for lab, axx in zip("abc", ax):
        axx.text(-0.30, 1.13, lab, transform=axx.transAxes, fontsize=8, fontweight="bold", va="top")
    out = os.path.join(HERE, "fig_wp2a_kpoints")
    fig.canvas.draw()
    if require_matplotlib_panel_alignment is not None:
        require_matplotlib_panel_alignment(fig, json_out=out + ".alignment.json", overlay_svg=out + ".alignment.svg",
                                           tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True)
    fig.savefig(out + ".pdf"); fig.savefig(out + ".svg"); fig.savefig(out + ".png", dpi=600)
    fig.savefig(out + ".tiff", dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    print("written", out + ".{pdf,svg,png,tiff}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--build", action="store_true"); a = ap.parse_args()
    if a.build:
        build()
    plot()

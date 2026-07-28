#!/usr/bin/env python
"""q=0 NEB restart/archive/state-identification harness — gate condition 5.

Three functions, each mapped to a gate requirement:

  archive_iteration(jobdir, outdir)   snapshot neb.path + per-image geometries + energies
                                      after every NEB iteration, hashed, append-only
  verify_restartable(archive_dir)     prove the latest snapshot is a usable neb.x restart
                                      (parses it back, checks image count / atom count / format)
  identify_state(pw_out, ref_json)    match the defect state by per-atom weight cosine against
                                      the stored q0 reference — NEVER by band index (PI rule)

Exercised on the preserved q=+1 explore band archive (q1_explore_state.tar.gz) before any q=0
submission — the harness must demonstrably round-trip a REAL neb.x state file.

Archive layout (append-only; nothing is ever overwritten):
  <outdir>/iter_NNN/neb.path            the restart file as neb.x wrote it
  <outdir>/iter_NNN/images.extxyz       parsed per-image geometries+energies
  <outdir>/iter_NNN/META.json           iteration no., energies, forces, sha256 of both files
  <outdir>/INDEX.json                   one row per snapshot (append-only ledger)
"""
import argparse, glob, hashlib, json, os, re, shutil, sys, tarfile, time


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_neb_path(path_file):
    """Parse a neb.x .path restart file -> list of images [{energy_au, positions_bohr, forces}]."""
    t = open(path_file, errors="ignore").read()
    m = re.search(r"NUMBER OF IMAGES\s*\n\s*(\d+)", t)
    if not m:
        raise ValueError(f"{path_file}: no NUMBER OF IMAGES header -- not a neb.x path file")
    n_img = int(m.group(1))
    blocks = re.split(r"Image:\s*\d+", t)[1:]
    if len(blocks) != n_img:
        raise ValueError(f"{path_file}: header says {n_img} images, found {len(blocks)} blocks")
    images = []
    for blk in blocks:
        lines = [l for l in blk.strip().splitlines() if l.strip()]
        energy = float(lines[0])
        rows = []
        for l in lines[1:]:
            parts = l.split()
            if len(parts) >= 3:
                rows.append([float(x) for x in parts[:6]] + ([1] * 0))
        images.append({"energy_au": energy, "n_rows": len(rows),
                       "coords": [r[:3] for r in rows],
                       "gradients": [r[3:6] if len(r) >= 6 else None for r in rows]})
    return images


BOHR_A = 0.529177210903


def write_images_extxyz(images, ref_extxyz, out_path):
    """Write per-image geometries (neb.path is in bohr; symbols/cell from the reference)."""
    from ase import Atoms
    from ase.io import read, write
    ref = read(ref_extxyz)
    n = len(ref)
    frames = []
    for k, im in enumerate(images):
        if im["n_rows"] != n:
            raise ValueError(f"image {k}: {im['n_rows']} rows vs reference {n} atoms")
        at = Atoms(symbols=ref.get_chemical_symbols(),
                   positions=[[c * BOHR_A for c in row] for row in im["coords"]],
                   cell=ref.cell, pbc=True)
        at.info["neb_image"] = k
        at.info["energy_au"] = im["energy_au"]
        frames.append(at)
    write(out_path, frames)
    return len(frames)


def archive_iteration(jobdir, outdir, tag=None, ref_extxyz=None, state_id=None):
    """Snapshot the current neb.path + per-image structures + state-ID. Append-only."""
    pf = os.path.join(jobdir, "neb.path")
    cands = glob.glob(os.path.join(jobdir, "*.path")) if not os.path.exists(pf) else [pf]
    if not cands:
        raise FileNotFoundError(f"no .path file in {jobdir}")
    pf = cands[0]
    images = parse_neb_path(pf)          # parse FIRST: never archive an unreadable snapshot
    os.makedirs(outdir, exist_ok=True)
    idx_file = os.path.join(outdir, "INDEX.json")
    idx = json.load(open(idx_file)) if os.path.exists(idx_file) else {"snapshots": []}
    n = len(idx["snapshots"])
    snap = os.path.join(outdir, f"iter_{n:03d}")
    if os.path.exists(snap):
        raise FileExistsError(f"{snap} exists -- the archive is append-only")
    os.makedirs(snap)
    shutil.copy(pf, os.path.join(snap, "neb.path"))
    n_frames = None
    if ref_extxyz:
        n_frames = write_images_extxyz(images, ref_extxyz,
                                       os.path.join(snap, "images.extxyz"))
    meta = {"snapshot": n, "tag": tag, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "n_images": len(images),
            "energies_au": [im["energy_au"] for im in images],
            "rows_per_image": [im["n_rows"] for im in images],
            "sha256_neb_path": sha256(os.path.join(snap, "neb.path")),
            "images_extxyz_frames": n_frames,
            "sha256_images_extxyz": (sha256(os.path.join(snap, "images.extxyz"))
                                     if n_frames else None),
            "state_id": state_id}
    json.dump(meta, open(os.path.join(snap, "META.json"), "w"), indent=1)
    idx["snapshots"].append({"iter": n, "tag": tag, "sha256": meta["sha256_neb_path"],
                             "n_images": meta["n_images"], "utc": meta["utc"]})
    json.dump(idx, open(idx_file, "w"), indent=1)
    return meta


def read_istep(path_file):
    """Read the current step count from a neb.path RESTART INFORMATION header."""
    lines = open(path_file, errors="ignore").read().splitlines()
    if not lines or "RESTART INFORMATION" not in lines[0]:
        raise ValueError(f"{path_file}: no RESTART INFORMATION header")
    return int(lines[1].strip())


def prepare_restart(archive_dir, template_in, outdir, extra_steps=1, nstep_path=None):
    """Prepare a REAL neb.x continuation from the latest archived snapshot.

    Verifies the snapshot first, then writes <outdir>/ with (a) the archived neb.path under
    the prefix neb.x expects and (b) the input flipped to restart_mode='restart' with the
    given nstep_path. The caller submits this directory; neb.x continues the band from the
    archive, not from interpolation.
    """
    r = verify_restartable(archive_dir)
    if not r["restartable"]:
        raise ValueError("latest snapshot failed verification -- refusing to build a restart")
    snap = os.path.join(archive_dir, f"iter_{r['snapshot']:03d}")
    os.makedirs(outdir, exist_ok=True)
    # QE's nstep_path is CUMULATIVE across a restart: the archived band carries istep, and a
    # restart with nstep_path <= istep runs ZERO iterations while still printing JOB DONE.
    # (Found the hard way: the first trial's "restart" left the band hash unchanged.)
    istep = read_istep(os.path.join(snap, "neb.path"))
    if nstep_path is None:
        nstep_path = istep + extra_steps
    elif nstep_path <= istep:
        raise ValueError(f"nstep_path={nstep_path} <= archived istep={istep}: the restart "
                         f"would run zero iterations")
    t = open(template_in).read()
    if "restart_mode" in t:
        t = re.sub(r"restart_mode\s*=\s*'[^']*'", "restart_mode = 'restart'", t)
    else:
        t = t.replace("&PATH", "&PATH\n  restart_mode = 'restart'", 1)
    if "nstep_path" in t:
        t = re.sub(r"nstep_path\s*=\s*\d+", f"nstep_path = {nstep_path}", t)
    else:
        t = t.replace("&PATH", f"&PATH\n  nstep_path = {nstep_path}", 1)
    open(os.path.join(outdir, "restart.neb.in"), "w").write(t)
    shutil.copy(os.path.join(snap, "neb.path"), os.path.join(outdir, "neb.path"))
    return {"from_snapshot": r["snapshot"], "sha256_neb_path": r["sha256"],
            "restart_input": os.path.join(outdir, "restart.neb.in"),
            "archived_istep": istep, "nstep_path": nstep_path}


def verify_restartable(archive_dir):
    """The LATEST snapshot must parse back as a valid neb.x restart with consistent shape."""
    idx = json.load(open(os.path.join(archive_dir, "INDEX.json")))
    if not idx["snapshots"]:
        raise ValueError("empty archive")
    last = idx["snapshots"][-1]
    snap = os.path.join(archive_dir, f"iter_{last['iter']:03d}")
    pf = os.path.join(snap, "neb.path")
    if sha256(pf) != last["sha256"]:
        raise ValueError(f"{pf}: sha256 mismatch vs INDEX -- archive corrupted")
    images = parse_neb_path(pf)
    meta = json.load(open(os.path.join(snap, "META.json")))
    ok = (len(images) == meta["n_images"]
          and [im["n_rows"] for im in images] == meta["rows_per_image"]
          and len({im["n_rows"] for im in images}) == 1)
    return {"restartable": bool(ok), "snapshot": last["iter"], "n_images": len(images),
            "rows_per_image": images[0]["n_rows"], "sha256": last["sha256"]}


def identify_state(weights, ref_weights, threshold=0.90):
    """Cosine of per-atom weight vectors vs the stored q0 reference. Band index is NEVER used."""
    import math
    if len(weights) != len(ref_weights):
        raise ValueError(f"weight vectors differ in length: {len(weights)} vs {len(ref_weights)}")
    dot = sum(a * b for a, b in zip(weights, ref_weights))
    na = math.sqrt(sum(a * a for a in weights)); nb = math.sqrt(sum(b * b for b in ref_weights))
    cos = dot / (na * nb) if na and nb else 0.0
    return {"cosine": round(cos, 4), "same_state": cos >= threshold, "threshold": threshold}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["archive", "verify", "selftest"])
    ap.add_argument("--jobdir"); ap.add_argument("--outdir"); ap.add_argument("--tag")
    ap.add_argument("--ref-extxyz", default=None,
                    help="reference structure for symbols/cell when writing images.extxyz")
    ap.add_argument("--q1-band-archive", default=None,
                    help="selftest: tar.gz containing a real neb.path (the preserved q=+1 band)")
    a = ap.parse_args()
    if a.mode == "archive":
        meta = archive_iteration(a.jobdir, a.outdir, a.tag, ref_extxyz=a.ref_extxyz)
        print(json.dumps(meta, indent=1)); return 0
    if a.mode == "verify":
        r = verify_restartable(a.outdir)
        print(json.dumps(r, indent=1)); return 0 if r["restartable"] else 2
    # selftest: round-trip the REAL q=+1 band
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        with tarfile.open(a.q1_band_archive) as tf:
            # explicit filter: 3.14 changes the default and warns before then
            try:
                tf.extractall(td, filter="data")
            except TypeError:            # python < 3.12
                tf.extractall(td)
        pfs = glob.glob(os.path.join(td, "**", "*.path"), recursive=True)
        if not pfs:
            print("SELFTEST FAILED: no .path in archive"); return 2
        jd = os.path.dirname(pfs[0])
        if os.path.basename(pfs[0]) != "neb.path":
            shutil.copy(pfs[0], os.path.join(jd, "neb.path"))
        out = os.path.join(td, "arch")
        ref = a.ref_extxyz
        m1 = archive_iteration(jd, out, tag="selftest-1", ref_extxyz=ref,
                               state_id={"cosine": 1.0, "note": "selftest placeholder"})
        m2 = archive_iteration(jd, out, tag="selftest-2", ref_extxyz=ref)
        r = verify_restartable(out)
        rst = None
        neb_in = glob.glob(os.path.join(jd, "*.neb.in")) + glob.glob(os.path.join(jd, "*.in"))
        if neb_in:
            rst = prepare_restart(out, neb_in[0], os.path.join(td, "restart"), extra_steps=1)
        ok = (r["restartable"] and m1["n_images"] == r["n_images"] and m2["snapshot"] == 1
              and (ref is None or m1["images_extxyz_frames"] == m1["n_images"])
              and (not neb_in or (rst and "restart_mode = 'restart'"
                                  in open(rst["restart_input"]).read())))
        print(json.dumps({"selftest_pass": bool(ok), "n_images": r["n_images"],
                          "rows_per_image": r["rows_per_image"],
                          "images_extxyz_frames": m1["images_extxyz_frames"],
                          "restart_prepared": bool(rst), "snapshots_written": 2,
                          "verify": r}, indent=1))
        return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())

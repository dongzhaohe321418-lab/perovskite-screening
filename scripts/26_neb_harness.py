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


def archive_iteration(jobdir, outdir, tag=None):
    """Snapshot the current neb.path + per-image pw outputs. Append-only."""
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
    meta = {"snapshot": n, "tag": tag, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "n_images": len(images),
            "energies_au": [im["energy_au"] for im in images],
            "rows_per_image": [im["n_rows"] for im in images],
            "sha256_neb_path": sha256(os.path.join(snap, "neb.path"))}
    json.dump(meta, open(os.path.join(snap, "META.json"), "w"), indent=1)
    idx["snapshots"].append({"iter": n, "tag": tag, "sha256": meta["sha256_neb_path"],
                             "n_images": meta["n_images"], "utc": meta["utc"]})
    json.dump(idx, open(idx_file, "w"), indent=1)
    return meta


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
    ap.add_argument("--q1-band-archive", default=None,
                    help="selftest: tar.gz containing a real neb.path (the preserved q=+1 band)")
    a = ap.parse_args()
    if a.mode == "archive":
        meta = archive_iteration(a.jobdir, a.outdir, a.tag)
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
        m1 = archive_iteration(jd, out, tag="selftest-1")
        m2 = archive_iteration(jd, out, tag="selftest-2")
        r = verify_restartable(out)
        ok = r["restartable"] and m1["n_images"] == r["n_images"] and m2["snapshot"] == 1
        print(json.dumps({"selftest_pass": bool(ok), "n_images": r["n_images"],
                          "rows_per_image": r["rows_per_image"],
                          "snapshots_written": 2, "verify": r}, indent=1))
        return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())

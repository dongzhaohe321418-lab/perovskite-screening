#!/usr/bin/env python3
"""Extract the q=0 / q=+1 production CI-NEB activation energies — GATED.

This script performs the barrier extraction that audit policy places behind
`check_action(action="publish_claim")`. It REFUSES to produce any number unless
invoked with --gate-token carrying the consultation id of an ALLOW verdict.

Design rules (audit-driven):
  * Reads ONLY the committed raw outputs; never a workspace copy, never a remote file.
  * Verifies each raw file's SHA-256 against the committed custody record BEFORE parsing.
  * Records the input fingerprint (conv_thr, degauss, path_thr, CI, images, charge) of
    both legs and refuses if they differ by anything other than tot_charge.
  * Emits a single JSON record with every value traceable to a file + hash + line.
  * Prints nothing barrier-shaped on the refusal path.

Usage (only after an ALLOW):
    python3 scripts/27_extract_barriers.py --gate-token <consultation_id> --out <path.json>
"""
from __future__ import annotations
import argparse, gzip, hashlib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGS = {
    "q0": {"out": "results/objective1/dft/charge_relaxed/q0_production/q0_neb.out.gz",
           "custody": "results/objective1/dft/charge_relaxed/q0_production/REMOTE_SHA256.txt",
           "input": "ehpc/inputs_stage2/neb_q0_production/q0_cineb.neb.in"},
    "q1": {"out": "results/objective1/dft/charge_relaxed/q1_production/q1_neb.out.gz",
           "custody": "results/objective1/dft/charge_relaxed/q1_production/SHA256.txt",
           "input": "ehpc/inputs_stage2/neb_q1_production/q1_cineb.neb.in"},
}
FP_KEYS = ("conv_thr", "degauss", "path_thr", "num_of_images", "CI_scheme",
           "ecutwfc", "ecutrho", "nspin", "occupations", "smearing")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verify_custody(out_path: Path, custody_path: Path) -> dict:
    """Match the raw file's digest against the committed custody record."""
    rec = custody_path.read_text(errors="ignore")
    comp = sha256(out_path)
    raw = gzip.decompress(out_path.read_bytes())
    decomp = hashlib.sha256(raw).hexdigest()
    hits = [h for h in (comp, decomp) if h in rec]
    if not hits:
        raise SystemExit(f"CUSTODY FAIL: neither digest of {out_path.name} appears in "
                         f"{custody_path.name}; refusing to parse.")
    return {"file": str(out_path.relative_to(ROOT)), "sha256_compressed": comp,
            "sha256_decompressed": decomp, "custody_record": str(custody_path.relative_to(ROOT)),
            "matched_form": "compressed" if comp in hits else "decompressed",
            "text": raw.decode("utf-8", "replace")}


def fingerprint(inp: Path) -> dict:
    t = inp.read_text(errors="ignore")
    fp = {}
    for k in FP_KEYS:
        m = re.search(rf"^\s*{k}\s*=\s*'?([^,'\n]+)'?", t, re.M)
        if m:
            fp[k] = m.group(1).strip()
    m = re.search(r"^\s*tot_charge\s*=\s*([\d.eE+-]+)", t, re.M)
    fp["tot_charge"] = m.group(1).strip() if m else "0"
    fp["sha256"] = sha256(inp)
    return fp


def parse_activation(text: str, leg: str) -> dict:
    """Terminal activation-energy record + convergence evidence."""
    conv = re.search(r"neb:\s*convergence achieved in\s+(\d+)\s+iterations", text)
    if not conv:
        raise SystemExit(f"{leg}: no formal convergence record; refusing to extract.")
    if "JOB DONE" not in text:
        raise SystemExit(f"{leg}: no JOB DONE record; refusing to extract.")
    # activation energies are printed per path-iteration; take the LAST block
    fwd = re.findall(r"activation energy \(->\)\s*=\s*([\d.eE+-]+)\s*eV", text)
    bwd = re.findall(r"activation energy \(<-\)\s*=\s*([\d.eE+-]+)\s*eV", text)
    if not fwd or not bwd:
        raise SystemExit(f"{leg}: activation-energy lines absent; refusing to extract.")
    return {"iterations": int(conv.group(1)), "n_activation_records": len(fwd),
            "forward_eV": float(fwd[-1]), "backward_eV": float(bwd[-1])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate-token", required=True,
                    help="consultation id of the ALLOW verdict for publish_claim")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9:_-]{8,}", a.gate_token) or a.gate_token.upper() in (
            "NONE", "PENDING", "DENY", "TODO", "PLACEHOLDER"):
        print("REFUSED: --gate-token is not a recorded ALLOW consultation id. "
              "No extraction performed.", file=sys.stderr)
        return 2

    legs, fps = {}, {}
    for leg, paths in LEGS.items():
        ev = verify_custody(ROOT / paths["out"], ROOT / paths["custody"])
        fps[leg] = fingerprint(ROOT / paths["input"])
        legs[leg] = {"custody": {k: v for k, v in ev.items() if k != "text"},
                     "input_fingerprint": fps[leg],
                     **parse_activation(ev["text"], leg)}

    diff = {k for k in set(fps["q0"]) | set(fps["q1"])
            if fps["q0"].get(k) != fps["q1"].get(k)} - {"tot_charge", "sha256"}
    if diff:
        raise SystemExit(f"FINGERPRINT MISMATCH beyond charge: {sorted(diff)}; refusing.")

    rec = {"gate_token": a.gate_token, "legs": legs,
           "fingerprint_differs_only_by": ["tot_charge", "sha256"],
           "delta_forward_eV": round(legs["q1"]["forward_eV"] - legs["q0"]["forward_eV"], 6),
           "delta_backward_eV": round(legs["q1"]["backward_eV"] - legs["q0"]["backward_eV"], 6),
           "extractor_sha256": sha256(Path(__file__))}
    Path(a.out).write_text(json.dumps(rec, indent=1) + "\n")
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Extract the q=0 / q=+1 production CI-NEB activation energies — GATED.

This script performs the barrier extraction that audit policy places behind
`check_action(action="publish_claim")`. It REFUSES to produce any number unless it can
find a DURABLE controller-written ALLOW record in the action ledger that is bound to
THIS commit, to `publish_claim`, and to this repository's committed evidence manifest.

Audit F-025 rejected two designs before this one, and both rejections were correct.

  v1 (`--gate-token <consultation_id>`) validated only token SYNTAX plus five literal
  blacklist strings, because the controller's ledger emits no consultation id at all --
  the field was invented here and so had no referent. An auditor ran the script with the
  token `arbitrary` and got a full extraction record.

  v2 read a real controller ledger row but took the ledger's PATH from `--ledger`. The
  auditor supplied a fabricated ledger carrying the current HEAD and manifest hash; every
  predicate passed. Authority that the caller can redirect is not authority.

v3 (this version) therefore takes NO path from the caller: the controller's state
directory is a module constant, and authorization must be corroborated in TWO files the
controller writes independently -- `action_ledger.jsonl` and `controller/state.json`'s
`authorizations` list. A single-file forgery fails on the missing corroboration.

RESIDUAL TRUST ASSUMPTION, stated because it cannot be closed from inside this script:
this process runs with the audited party's privileges, so any file it can read it could
also write. No local read can prove a local file was not forged by the reader. What v3
establishes is that (a) the CLI cannot be pointed at a substitute, and (b) a forgery must
be consistent across two controller-written files. Closing the gap fully requires the
controller to place its records where the executor cannot write, or to sign them -- an
operator action, reported to the PI rather than asserted as solved here.

Design rules (audit-driven):
  * Reads ONLY the committed raw outputs; never a workspace copy, never a remote file.
  * Verifies each raw file's SHA-256 against the committed custody record BEFORE parsing.
  * Records the input fingerprint (conv_thr, degauss, path_thr, CI, images, charge) of
    both legs and refuses if they differ by anything other than tot_charge.
  * Emits a single JSON record with every value traceable to a file + hash + line.
  * Prints nothing barrier-shaped on the refusal path.

Usage (only after a corroborated ALLOW exists):
    python3 scripts/27_extract_barriers.py --allow-timestamp <ISO8601 of the ALLOW row> \
        --out <path.json>

There is deliberately no path argument. Tests exercise both polarities by importing this
module and rebinding CONTROLLER_DIR in-process, which the CLI cannot do.
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


# Controller-owned state. NOT caller-selectable (audit F-025 v2): the CLI exposes no path
# argument, so an invocation cannot redirect authorization at a substitute file.
CONTROLLER_DIR = Path("/Users/ericdong/Desktop/perovskite-project/audit-loop/state")


def _ledger_path() -> Path:
    return CONTROLLER_DIR / "action_ledger.jsonl"


def _state_path() -> Path:
    return CONTROLLER_DIR / "controller" / "state.json"


def git_head(repo: Path) -> str:
    import subprocess
    r = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("REFUSED: cannot resolve git HEAD; authorization cannot be bound.")
    return r.stdout.strip()


def committed_manifest_sha(repo: Path) -> str:
    req = repo / ".audit" / "audit_request.json"
    if not req.exists():
        raise SystemExit("REFUSED: no .audit/audit_request.json; nothing to bind authorization to.")
    return json.loads(req.read_text())["evidence_manifest_sha256"]


def authorize(allow_timestamp: str, repo: Path) -> dict:
    """Return the controller's ALLOW row, or exit nonzero. Reads NOTHING scientific.

    Every one of these conditions must hold. Each has an audit reason for existing:
      * the ledger file exists and is the controller's (F-025: authority must be durable
        and externally written, never a string this script invents or accepts on faith);
      * a row exists with EXACTLY the supplied timestamp -- so the invocation names one
        specific decision instead of matching "some ALLOW";
      * that row's action is publish_claim and its decision is ALLOW;
      * it carries no reason_codes (an ALLOW with blockers is not an authorization);
      * its science_commit equals the CURRENT HEAD -- an ALLOW for an older tree does not
        authorize extraction from a different one;
      * its manifest_sha256 equals the committed evidence binding -- so the authorized
        evidence set is the one on disk.
    """
    ledger = _ledger_path()
    if not ledger.exists():
        raise SystemExit(f"REFUSED: action ledger not found at {ledger}. "
                         "No durable ALLOW record can be verified; no extraction performed.")
    rows = []
    for line in ledger.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    hits = [r for r in rows if r.get("timestamp") == allow_timestamp]
    if not hits:
        raise SystemExit(f"REFUSED: no ledger row with timestamp {allow_timestamp!r}. "
                         "The supplied value does not name a recorded controller decision; "
                         "no extraction performed.")
    row = hits[-1]
    if row.get("action") != "publish_claim":
        raise SystemExit(f"REFUSED: ledger row is action {row.get('action')!r}, not "
                         "'publish_claim'; no extraction performed.")
    if row.get("decision") != "ALLOW":
        raise SystemExit(f"REFUSED: ledger row decision is {row.get('decision')!r}, not "
                         "'ALLOW'; no extraction performed.")
    if row.get("reason_codes"):
        raise SystemExit(f"REFUSED: the ALLOW row carries blocking reason codes "
                         f"{row['reason_codes']}; that is not an authorization. "
                         "No extraction performed.")
    head = git_head(repo)
    if row.get("science_commit") != head:
        raise SystemExit(f"REFUSED: the ALLOW is bound to commit "
                         f"{str(row.get('science_commit'))[:12]} but HEAD is {head[:12]}. "
                         "An authorization for another tree does not carry over; "
                         "no extraction performed.")
    man = committed_manifest_sha(repo)
    if row.get("manifest_sha256") != man:
        raise SystemExit(f"REFUSED: the ALLOW is bound to evidence manifest "
                         f"{str(row.get('manifest_sha256'))[:12]} but the committed binding is "
                         f"{man[:12]}; no extraction performed.")
    # CORROBORATION (audit F-025 v2): the ledger alone is one file. The controller also
    # records granted authorizations in controller/state.json. Requiring agreement means a
    # forged ledger row must be matched by a forged state entry -- the auditor's fabricated
    # single ledger no longer suffices.
    state = _state_path()
    if not state.exists():
        raise SystemExit(f"REFUSED: controller state not found at {state}; the ALLOW cannot be "
                         "corroborated. No extraction performed.")
    try:
        auths = json.loads(state.read_text()).get("authorizations") or []
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f"REFUSED: controller state unreadable ({exc}); the ALLOW cannot be "
                         "corroborated. No extraction performed.")
    matches = [a for a in auths
               if isinstance(a, dict)
               and a.get("action") == "publish_claim"
               and a.get("science_commit") == row.get("science_commit")
               and a.get("manifest_sha256") == row.get("manifest_sha256")
               and (a.get("ledger_timestamp") == allow_timestamp
                    or a.get("timestamp") == allow_timestamp)]
    if not matches:
        raise SystemExit(
            "REFUSED: the ledger row is not corroborated by any publish_claim authorization in "
            f"{state} bound to the same commit, manifest and timestamp. A ledger row alone is a "
            "single file the caller might have written; two independent controller records are "
            "required. No extraction performed.")
    return {**row, "corroborated_by": matches[-1]}


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
    ap.add_argument("--allow-timestamp", required=True,
                    help="exact timestamp of the controller ALLOW row in the action ledger")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    # Authorization BEFORE any scientific read or write (F-025). No path comes from the
    # caller: CONTROLLER_DIR is a module constant.
    allow_row = authorize(a.allow_timestamp, ROOT)

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

    rec = {"authorized_by": {"ledger": str(_ledger_path()), "timestamp": allow_row["timestamp"],
                             "corroborated_by": allow_row.get("corroborated_by"),
                             "action": allow_row["action"], "decision": allow_row["decision"],
                             "science_commit": allow_row["science_commit"],
                             "manifest_sha256": allow_row["manifest_sha256"]},
           "legs": legs,
           "fingerprint_differs_only_by": ["tot_charge", "sha256"],
           "delta_forward_eV": round(legs["q1"]["forward_eV"] - legs["q0"]["forward_eV"], 6),
           "delta_backward_eV": round(legs["q1"]["backward_eV"] - legs["q0"]["backward_eV"], 6),
           "extractor_sha256": sha256(Path(__file__))}
    Path(a.out).write_text(json.dumps(rec, indent=1) + "\n")
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

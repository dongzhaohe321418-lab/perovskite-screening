#!/usr/bin/env python
"""Preflight a remote job submission BEFORE spending compute on it.

Written after five consecutive failed submissions of one job, each with a different cause:
an invented CLI flag, a missing required argument, an unstaged local module that crashed
`--help` (so the flag guard misreported it as a flag problem), and two unstaged input paths.
Every one was discoverable from the driver's own source before submitting.

Checks, in order:
  1. every CLI flag you intend to pass is accepted by the driver
  2. every REQUIRED argument of the driver is present in your invocation
  3. every local module the driver imports exists and will be staged
  4. every path the driver reads -- explicit arguments, argparse defaults, AND filenames
     hardcoded inside a directory argument -- exists locally
  5. the driver's `--help` exits 0 (a crash here is an environment problem, never a flag one)

Usage:
  python 25_preflight.py --driver scripts/22_paired_pilot.py \
      --invocation "--pool pool --vac-ref vac_ref.extxyz --members 28 29 --systems undoped GA Sr" \
      --stage scripts/checks.py vac_ref.extxyz
"""
from __future__ import annotations
import argparse, ast, os, re, subprocess, sys, hashlib


def driver_help(path):
    r = subprocess.run([sys.executable, path, "--help"], capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def accepted_flags(help_text):
    return set(re.findall(r"(--[\w-]+)", help_text))


def required_args(help_text):
    """argparse prints required options in the usage line WITHOUT brackets."""
    usage = help_text.split("options:")[0]
    bare = set(re.findall(r"(?<!\[)(--[\w-]+)", usage))
    bracketed = set(re.findall(r"\[(--[\w-]+)", usage))
    return bare - bracketed


def local_imports(src, module_names):
    got = set()
    for m in re.finditer(r"^\s*from\s+(\w+)\s+import", src, re.M):
        if m.group(1) in module_names:
            got.add(m.group(1))
    for m in re.finditer(r"^\s*import\s+(\w+)\s*$", src, re.M):
        if m.group(1) in module_names:
            got.add(m.group(1))
    return sorted(got)


def path_defaults(src):
    """argparse defaults that look like filesystem paths."""
    out = []
    for m in re.finditer(r'add_argument\(\s*"(--[\w-]+)"[^)]*?default\s*=\s*"([^"]+)"', src):
        flag, dflt = m.group(1), m.group(2)
        if "/" in dflt or dflt.endswith((".extxyz", ".xyz", ".json", ".cif", ".traj")):
            out.append((flag, dflt))
    return out


def interpolated_reads(src):
    """Filenames the driver reads from INSIDE a directory argument -- invisible to flag checks.

    e.g. read(f"{args.pool}/fa19cs1_pb20i60_233.extxyz")
    """
    out = []
    # READS only. `open(f"{args.out}/x.json", "w")` is an OUTPUT the driver creates -- an
    # earlier version of this tool flagged those as missing inputs, a false positive that
    # would have blocked a correct submission.
    for m in re.finditer(r'(?:read|open)\(\s*f"([^"]*\{[^}]+\}[^"]*)"([^)]*)', src):
        pat, tail = m.group(1), m.group(2)
        if re.search(r'["\']\s*[wax]b?\+?["\']', tail):
            continue                      # write mode -> output, not input
        out.append(pat)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--driver", required=True)
    ap.add_argument("--invocation", default="", help="the exact flag string you will pass")
    ap.add_argument("--stage", nargs="*", default=[], help="files you will stage remotely")
    ap.add_argument("--pool-dir", default=None,
                    help="local dir that will become the --pool argument, for interpolated reads")
    a = ap.parse_args()

    fails, warns = [], []
    src = open(a.driver).read()

    rc, out, err = driver_help(a.driver)
    print(f"[1] driver --help exit code: {rc}")
    if rc != 0:
        fails.append(f"--help exits {rc}: the driver cannot import. This is an ENVIRONMENT "
                     f"problem, not a flag problem. stderr tail: {err.strip()[-300:]}")
        print("    ABORTING further flag checks -- they would be meaningless")
        for f in fails:
            print(f"  FAIL {f}")
        sys.exit(1)

    acc = accepted_flags(out)
    used = set(re.findall(r"(--[\w-]+)", a.invocation))
    print(f"[2] flags you pass: {sorted(used)}")
    for f in sorted(used - acc):
        fails.append(f"flag {f} is NOT accepted by {os.path.basename(a.driver)}")

    req = required_args(out)
    print(f"[3] driver REQUIRED args: {sorted(req) if req else '(none)'}")
    for f in sorted(req - used):
        fails.append(f"required arg {f} is missing from your invocation")

    modnames = set()
    sd = os.path.dirname(a.driver) or "."
    for fn in os.listdir(sd):
        if fn.endswith(".py"):
            modnames.add(fn[:-3])
    deps = local_imports(src, modnames)
    staged_base = {os.path.basename(s) for s in a.stage}
    print(f"[4] local modules imported: {deps if deps else '(none)'}")
    for d in deps:
        if f"{d}.py" not in staged_base:
            fails.append(f"driver imports local module '{d}' but {d}.py is not in --stage")

    pd = path_defaults(src)
    print(f"[5] path-valued defaults: {pd if pd else '(none)'}")
    for flag, dflt in pd:
        if flag not in used:
            if not os.path.exists(dflt):
                fails.append(f"{flag} not overridden and its default '{dflt}' does not exist")
            else:
                warns.append(f"{flag} not overridden -> default '{dflt}' must be staged remotely")

    ir = interpolated_reads(src)
    print(f"[6] reads from inside a directory argument: {ir if ir else '(none)'}")
    for pat in ir:
        fn = pat.split("/")[-1]
        if "{" in fn:
            continue
        if a.pool_dir:
            local = os.path.join(a.pool_dir, fn)
            if not os.path.exists(local):
                fails.append(f"driver reads '{pat}' but {local} does not exist -- staging the "
                             f"directory alone will NOT supply it")
            else:
                print(f"    OK  {local}")
        else:
            warns.append(f"driver reads '{pat}'; pass --pool-dir to verify {fn} is present")

    print(f"[7] staged files: {len(a.stage)}")
    for s in a.stage:
        if not os.path.exists(s):
            fails.append(f"staged file '{s}' does not exist locally")
        else:
            h = hashlib.sha256(open(s, "rb").read()).hexdigest()[:12]
            print(f"    OK  {s}  {os.path.getsize(s)} bytes  sha256:{h}")

    print()
    for w in warns:
        print(f"  WARN {w}")
    for f in fails:
        print(f"  FAIL {f}")
    if fails:
        print(f"\nPREFLIGHT FAILED ({len(fails)} problem(s)) -- do NOT submit")
        sys.exit(1)
    print("PREFLIGHT PASSED -- safe to submit")


if __name__ == "__main__":
    main()

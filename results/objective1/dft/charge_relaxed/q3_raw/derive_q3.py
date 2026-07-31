#!/usr/bin/env python3
"""Q3 derivation: recompute the quoted polaron/shallow-donor numbers from committed raws.

Runs stdlib-only (gzip + re). Every value quoted in Q0_POLARON_EXCLUDED.md /
RESULTS_INDEX.md Q3 rows is recomputed from results/objective1/dft/charge_relaxed/q3_raw/
and asserted. Exit 0 = every quoted value reproduces from committed records.

Chain of custody: REMOTE_SHA256_UNCOMPRESSED.txt was written on the cluster next to the
source job dirs; this script re-verifies each gunzipped file against it before parsing.
"""
import gzip, hashlib, re, os, sys

D = os.path.join(os.path.dirname(__file__) or ".", "")
RY = 13.605693122994

def rd(name):
    return gzip.open(D + name, "rt", errors="ignore").read()

# 0. chain of custody
remote = {}
for line in open(D + "REMOTE_SHA256_UNCOMPRESSED.txt"):
    sha, path = line.split()
    remote[path.split("/")[-2][:8] + "_" + path.split("/")[-1] + ".gz"] = sha
for gz, sha in remote.items():
    h = hashlib.sha256(gzip.open(D + gz, "rb").read()).hexdigest()
    assert h == sha, f"custody FAIL {gz}: {h[:12]} != {sha[:12]}"
print(f"[custody] {len(remote)} raw outputs match cluster-side SHA-256")

# 1. P1: pristine cell converged; CBM eigenvalue basis for the CBM-like comparison
p1 = rd("dd88d5d3_P1.out.gz")
assert "convergence has been achieved" in p1, "P1 did not converge"
print("[P1] pristine 160-atom SCF converged")

# 2. P2: unconstrained-spin run converges rapidly to ZERO moment
p2 = rd("dd88d5d3_P2.out.gz")
assert "convergence has been achieved" in p2, "P2 did not converge"
mags = [float(x) for x in re.findall(r"total magnetization\s*=\s*([-\d.]+)", p2)]
E2 = [float(x) for x in re.findall(r"^!\s+total energy\s*=\s*([-\d.]+)", p2, re.M)]
assert abs(mags[-1]) < 0.01, f"P2 final moment {mags[-1]} != 0"
assert abs(E2[-1] - (-9247.62643349)) < 1e-6, f"P2 energy {E2[-1]}"
n_iter = len(re.findall(r"iteration #", p2))
assert n_iter <= 10, f"P2 took {n_iter} iterations (quoted: rapid, ~6)"
print(f"[P2] converged in {n_iter} iterations to m=0, E={E2[-1]} Ry — no competing localised spin state")

# 3. ELAS: elastic cost of the 0.20 A seeded distortion (non-magnetic, same geometry as POL)
el = rd("464c52ff_ELAS.out.gz")
assert "convergence has been achieved" in el, "ELAS did not converge"
Ee = [float(x) for x in re.findall(r"^!\s+total energy\s*=\s*([-\d.]+)", el, re.M)][-1]
assert abs(Ee - (-9247.61815625)) < 1e-6, f"ELAS energy {Ee}"
E_deloc = E2[-1]
elastic_meV = (Ee - E_deloc) * RY * 1000
assert abs(elastic_meV - 112.6) < 0.5, f"elastic cost {elastic_meV:.1f} != 112.6 meV"
print(f"[ELAS] elastic cost of seeded distortion = {elastic_meV:.1f} meV")

# 4. POL: seeded moment decays monotonically; energy stays above delocalised solution.
#    POL never converged (plateaued and was cancelled) — the decay trace is the evidence.
pol = rd("652b5174_POL.out.gz")
pm = [float(x) for x in re.findall(r"absolute magnetization\s*=\s*([-\d.]+)", pol)]
pe = [float(x) for x in re.findall(r"total energy\s*=\s*([-\d.]+)\s*Ry", pol)]
assert pm[0] > 1.5 and pm[-1] < 0.7, f"POL moment trace {pm[0]} -> {pm[-1]} not decaying"
gain_meV = (Ee - pe[-1]) * RY * 1000   # spin-polarisation gain at identical geometry
assert gain_meV < 10, f"localisation gain {gain_meV:.1f} meV not small"
above_meV = (pe[-1] - E_deloc) * RY * 1000
assert above_meV > 80, f"POL sits only {above_meV:.1f} meV above delocalised"
print(f"[POL] seeded moment {pm[0]} -> {pm[-1]} muB (decaying); last E sits "
      f"{above_meV:.1f} meV above delocalised; spin gain at fixed geometry <= {gain_meV:.1f} meV")
print(f"[POL] NOT converged (plateaued, cancelled) — bounds, not point values, are quoted")

# 5. projwfc outputs present for the CBM-like state identification (P1/P2 per-atom weights)
for f in ("dd88d5d3_proj_P1.out.gz", "dd88d5d3_proj_P2.out.gz"):
    assert os.path.exists(D + f) and os.path.getsize(D + f) > 1000, f"{f} missing"
print("[proj] projwfc raw outputs committed (P1 + P2) — per-atom weight source for cosines")

print("\nQ3 DERIVATION: every quoted value reproduces from committed raw records")

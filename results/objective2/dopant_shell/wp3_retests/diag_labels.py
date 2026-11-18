"""D-V1c (post hoc): are band frames and binding frames near-duplicate structures with inconsistent energy labels?
For every pair (band frame, binding frame) on the same host with the same composition, report the per-atom RMS
displacement after removing the mean shift (same atom order assumed, checked by species) and the label difference."""
import numpy as np
from ase.io import read
D = "<repo>/results/objective2/dopant_shell/wp3/dataset/"
fr = [a for fn in ("train.xyz", "valid.xyz", "test.xyz") for a in read(D + fn, ":")]
band = [a for a in fr if a.info["config_type"].startswith("band_")]
bind = [a for a in fr if a.info["config_type"] == "binding"]
def comp(a): return tuple(sorted(a.get_chemical_symbols()))
rows = []
for b in bind:
    for n in band:
        if n.info["host"] != b.info["host"] or len(n) != len(b) or comp(n) != comp(b):
            continue
        if list(n.get_chemical_symbols()) != list(b.get_chemical_symbols()):
            rows.append((b.info["label"], n.info["label"], None, None, None)); continue
        d = n.get_positions() - b.get_positions()
        d = d - np.round(d @ np.linalg.inv(b.cell.array)) @ b.cell.array      # minimum image
        d = d - d.mean(0)
        rmsd = float(np.sqrt((d ** 2).sum(1).mean())); mx = float(np.sqrt((d ** 2).sum(1)).max())
        rows.append((b.info["label"], n.info["label"], rmsd, mx,
                     (n.info["REF_energy_raw"] - b.info["REF_energy_raw"]) * 1000))
rows.sort(key=lambda r: (r[0], 1e9 if r[2] is None else r[2]))
seen = set()
for r in rows:
    if r[0] in seen: continue
    seen.add(r[0])
    print(f"{r[0]:22s} nearest band {r[1]:20s}", "species order differs" if r[2] is None else
          f"RMSD {r[2]:.3f} A  max {r[3]:.2f} A  dF(band - binding) {r[4]:+9.1f} meV")

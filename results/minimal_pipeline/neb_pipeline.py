"""
Minimal viable pipeline: iodine-vacancy migration in cubic CsPbI3.
Zero-shot MACE-MP-0 + CI-NEB. Establishes the undoped baseline Ea.

Run:  python neb_pipeline.py     (env: torch, mace-torch, ase, pymatgen, scipy)
"""
import warnings, numpy as np
warnings.filterwarnings("ignore")
from ase.spacegroup import crystal
from ase.geometry import get_distances
from ase.optimize import FIRE
from ase.filters import FrechetCellFilter
from ase.mep import NEB, NEBTools
from ase.io import write
from mace.calculators import mace_mp

# ---- 0. calculator ----
calc = mace_mp(model="medium", device="cpu", default_dtype="float64", dispersion=False)

# ---- 1. cubic CsPbI3 2x2x2 (40 atoms), relax cell + positions ----
a0 = 6.289
prim = crystal(['Cs', 'Pb', 'I'],
               basis=[(0,0,0), (.5,.5,.5), (.5,.5,0)],
               spacegroup=221, cellpar=[a0]*3 + [90]*3)
sc = prim * (2, 2, 2)
sc.calc = calc
FIRE(FrechetCellFilter(sc), logfile=None).run(fmax=0.02, steps=300)
write("CsPbI3_222_relaxed.cif", sc)

# ---- 2. build symmetric V_I hop endpoints (octahedral-edge, nearest-I) ----
I_idx = [i for i, s in enumerate(sc.get_chemical_symbols()) if s == 'I']
iA = I_idx[0]; rA = sc.positions[iA]
others = [j for j in I_idx if j != iA]
D = get_distances(rA, sc.positions[others], cell=sc.cell, pbc=True)[1][0]
iB = others[int(np.argmin(D))]
rB = rA + get_distances(rA, sc.positions[iB], cell=sc.cell, pbc=True)[0][0, 0]
init = sc.copy(); del init[iB]                      # vacancy at B
iA2 = iA - (1 if iB < iA else 0)
final = init.copy(); final.positions[iA2] = rB      # atom hops A->B

def relax(a):
    a = a.copy(); a.calc = calc
    FIRE(a, logfile=None).run(fmax=0.02, steps=300)
    return a
init_r, final_r = relax(init), relax(final)
write("neb_initial.cif", init_r); write("neb_final.cif", final_r)

# ---- 3. CI-NEB, 7 images, IDPP interpolation ----
n = 7
images = [init_r.copy()] + [init_r.copy() for _ in range(n-2)] + [final_r.copy()]
neb = NEB(images, k=0.1, climb=True, method='improvedtangent', allow_shared_calculator=True)
neb.interpolate(method='idpp', mic=True)
for im in images:
    im.calc = calc
FIRE(neb, logfile=None).run(fmax=0.03, steps=400)
write("neb_path.xyz", images)

# ---- 4. barriers ----
E = np.array([im.get_potential_energy() for im in images])
si = int(np.argmax(E)); write("neb_saddle.cif", images[si])
print(f"E profile (eV, rel endpoint): {(E - E[0]).round(4)}")
print(f"Ea (saddle - endpoint)          = {E.max() - E[0]:.3f} eV")
print(f"Ea (saddle - metastable well)   = {E.max() - E.min():.3f} eV   <- quote this")

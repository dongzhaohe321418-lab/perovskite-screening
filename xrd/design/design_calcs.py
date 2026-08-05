#!/usr/bin/env python3
"""Design calculations for the FA0.95Cs0.05PbI3 amorphous-quantification study.

Reproduces every number in EXPERIMENT_DESIGN_amorphous_ML.md.
    python design_calcs.py
"""
import numpy as np, pandas as pd

LAM = 1.54184          # Cu Ka weighted mean, as declared by the instrument
kB  = 8.617e-5         # eV/K

def tth(d):
    return 2*np.degrees(np.arcsin(LAM/(2*d)))

def diagnostic_window():
    """Three-phase separation in the 11-15 deg window."""
    a_FA, a_Cs = 6.3620, 6.1800
    a_mix = 0.95*a_FA + 0.05*a_Cs                     # Vegard
    rows = [('alpha 100', a_mix/np.sqrt(1))]
    a_d, c_d = 8.6603, 7.9022                          # delta-FAPbI3 P63mc
    d_010 = 1/np.sqrt(4*(0+0+1)/(3*a_d**2) + 0/c_d**2)
    rows.insert(0, ('delta 010', d_010))
    rows.insert(1, ('PbI2 001', 6.979))                # 2H-PbI2, c = 6.979
    df = pd.DataFrame([(n, d, tth(d)) for n, d in rows], columns=['reflection','d_A','tth_deg'])
    df['gap_to_next_deg'] = df.tth_deg.diff().shift(-1)
    return a_mix, df

def t50_grid(Ea=0.75, m=2.0, T=(25,40,55,70,85), RH=(15,35,55,75,85),
             anchor=(85, 85, 100.0)):
    """Half-life grid. `anchor` = (T_C, RH_pct, t50_h) pins k0.
    Ea and m are NOT known for this system -- that is the point of Stage 1."""
    Ta, Ra, ta = anchor
    k0 = np.log(2)/(ta*np.exp(-Ea/(kB*(Ta+273.15)))*(Ra/100)**m)
    g = np.array([[np.log(2)/(k0*np.exp(-Ea/(kB*(t+273.15)))*(r/100)**m)
                   for r in RH] for t in T])
    return pd.DataFrame(g, index=[f'{t}C' for t in T], columns=[f'{r}%' for r in RH])

def feasibility_sensitivity(budget_h=576):
    """How many of 25 grid points finish inside the budget, vs unknown Ea and m."""
    out = []
    for Ea in (0.5, 0.6, 0.75, 0.9, 1.1):
        for m in (1.0, 2.0, 3.0):
            g = t50_grid(Ea=Ea, m=m).values
            out.append(dict(Ea=Ea, m=m, completable=int((g < budget_h).sum())))
    return pd.DataFrame(out)

def sample_size(n_params=4, films=(12, 24, 40, 60)):
    """Independent observations per parameter. One film = one independent sample;
    time points within a film are autocorrelated, not independent."""
    return pd.DataFrame([dict(films=n, obs_per_param=n/n_params) for n in films])


def literature_gap(csv_path='literature_index.csv'):
    """Exact-keyword counts over the paper titles.

    Counted with ONE keyword per row -- an earlier version of this table quoted
    the hits of a broadened alternation (amorphous|glass|disorder, and
    Rietveld|crystallinity|crystallite|texture|strain) against the narrow label,
    which inflated 'amorphous' 0 -> 2 and 'Rietveld/crystallinity' 1 -> 11.
    Both counts are reported here so the difference is visible.
    """
    import re
    lit = pd.read_csv(csv_path)
    narrow = {
        'amorphous':               r'amorphous',
        'PDF / total scattering':  r'\bPDF\b|pair distribution|total scattering',
        'Rietveld or crystallinity': r'rietveld|crystallinit',
        'machine learning':        r'machine learning|neural network|deep learning',
        'in situ / operando':      r'in.?situ|operando',
        'humidity':                r'humid',
    }
    broad = {
        'amorphous':               r'amorphous|glass|disorder',
        'Rietveld or crystallinity': r'rietveld|crystallinit|crystallite|texture|strain',
    }
    rows = []
    for label, pat in narrow.items():
        n = int(lit.title.str.contains(pat, case=False, regex=True, na=False).sum())
        b = broad.get(label)
        nb = int(lit.title.str.contains(b, case=False, regex=True, na=False).sum()) if b else n
        rows.append(dict(topic=label, exact=n, broadened=nb))
    return pd.DataFrame(rows)

if __name__ == '__main__':
    a_mix, win = diagnostic_window()
    print(f'Vegard a = {a_mix:.4f} A\n')
    print(win.round(4).to_string(index=False))
    print('\nt50 grid (h), Ea=0.75 eV, m=2:')
    g = t50_grid()
    print(g.round(0).to_string())
    print(f'\nspan = {g.values.max()/g.values.min():.0f}x')
    print(f'completable in 30 d: {int((g.values < 576).sum())} of {g.size}')
    print('\nfeasibility vs unknown kinetics:')
    print(feasibility_sensitivity().pivot(index='Ea', columns='m', values='completable').to_string())
    print('\nsample size:')
    print(sample_size().to_string(index=False))
    import os
    _csv = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'literature_index.csv')
    if os.path.exists(_csv):
        print('\nliterature gap (exact keyword in title):')
        print(literature_gap(_csv).to_string(index=False))

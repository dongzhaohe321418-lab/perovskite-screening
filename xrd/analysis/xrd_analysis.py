#!/usr/bin/env python3
"""
XRD analysis of a control perovskite thin film.
  * pseudo-Voigt profile fitting with Cu Ka1/Ka2 doublet, Poisson weights
  * cubic (pseudo-cubic) lattice refinement with zero-shift
  * crystallinity metrics (degree of crystallinity, peak/background, PbI2 fraction)
  * crystallite size: Scherrer, integral-breadth Voigt, Williamson-Hall
  * Monte-Carlo error propagation of statistical + systematic terms

Sample: perovskite#control##20260726-095651_100.txt
"""
import json
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit, least_squares
from scipy.signal import find_peaks
from scipy.special import erfc

LAM1, LAM2, R21 = 1.540598, 1.544426, 0.5     # Cu Ka1/Ka2, intensity ratio
S = 2 * np.sqrt(2 * np.log(2))
ETA_INST = 0.55                                # benchtop pseudo-Voigt mixing
K_SCHERRER = 0.9                               # spherical-ish crystallites

# Caglioti instrumental resolution, benchtop Cu Ka (assumed - see report)
_TT = np.array([14., 30., 45.]); _F = np.array([0.110, 0.120, 0.135])
_T = np.tan(np.radians(_TT / 2))
UVW = np.linalg.solve(np.column_stack([_T**2, _T, np.ones(3)]), _F**2)


def fwhm_inst(tt):
    t = np.tan(np.radians(np.asarray(tt) / 2))
    return np.sqrt(np.clip(UVW[0] * t**2 + UVW[1] * t + UVW[2], 1e-8, None))


# ---------- profile shapes ----------
def pv(x, x0, fw, eta):
    sg = fw / S
    G = np.exp(-0.5 * ((x - x0) / sg)**2) / (sg * np.sqrt(2 * np.pi))
    L = (fw / (2 * np.pi)) / ((x - x0)**2 + (fw / 2)**2)
    return eta * L + (1 - eta) * G


def doublet(x, x0, area, fw, eta):
    """Ka1+Ka2 pair; Ka2 offset from Bragg's law, fixed 1:2 intensity."""
    d2 = np.degrees(2 * np.tan(np.radians(x0 / 2)) * (LAM2 - LAM1) / LAM1)
    return area * (pv(x, x0, fw, eta) + R21 * pv(x, x0 + d2, fw, eta)) / (1 + R21)


def pv_to_GL(fw, eta):
    """Thompson-Cox-Hastings inverse: pseudo-Voigt -> Gaussian/Lorentzian FWHM."""
    fw = np.atleast_1d(np.asarray(fw, float)); eta = np.atleast_1d(np.asarray(eta, float))
    q = np.linspace(0, 1, 4001)
    et = 1.36603 * q - 0.47719 * q**2 + 0.11116 * q**3
    fL = np.interp(np.clip(eta, 0, 1), et, q) * fw
    c = [1., 2.69269, 2.42843, 4.47163, 0.07842]
    g = fw * np.linspace(0, 1, 2001)[:, None]
    tot = (g**5 + c[1]*g**4*fL + c[2]*g**3*fL**2 + c[3]*g**2*fL**3
           + c[4]*g*fL**4 + fL**5) ** 0.2
    fG = np.array([np.interp(fw[i], tot[:, i], g[:, i]) for i in range(len(fw))])
    return fG, fL


def beta_voigt(fG, fL):
    """Integral breadth of a Voigt from its G/L FWHM components."""
    fG = np.atleast_1d(fG); fL = np.atleast_1d(fL)
    out = np.empty_like(fG, dtype=float)
    bG = fG * np.sqrt(np.pi / (4 * np.log(2))); bL = fL * np.pi / 2
    small = fG <= 1e-9
    out[small] = bL[small]
    k = np.where(small, 0.0, bL / (np.sqrt(np.pi) * np.maximum(bG, 1e-12)))
    ok = (~small) & (k < 25); big = (~small) & (k >= 25)
    out[ok] = bG[ok] * np.exp(-k[ok]**2) / erfc(k[ok])
    out[big] = bL[big]
    return out


def beta_sample(fw, eta, tt, scale=1.0, eta_i=ETA_INST):
    """Sample-only integral breadth (rad) after deconvolving the instrument."""
    fG_o, fL_o = pv_to_GL(fw, eta)
    fwi = fwhm_inst(tt) * scale
    fG_i, fL_i = pv_to_GL(fwi, np.full(len(np.atleast_1d(fwi)), eta_i))
    return np.radians(beta_voigt(np.sqrt(np.clip(fG_o**2 - fG_i**2, 0, None)),
                                 np.clip(fL_o - fL_i, 0, None)))


def wfit(x, y, W):
    Sw, Sx, Sy = W.sum(), (W*x).sum(), (W*y).sum()
    Sxx, Sxy = (W*x*x).sum(), (W*x*y).sum()
    Dt = Sw*Sxx - Sx**2
    return ((Sw*Sxy - Sx*Sy)/Dt, (Sxx*Sy - Sx*Sxy)/Dt,
            np.sqrt(Sw/Dt), np.sqrt(Sxx/Dt))


# ---------- 1. load ----------
def load(path):
    raw = np.loadtxt(path)
    return raw[:, 0], raw[:, 1]


# ---------- 2. fit peaks ----------
def fit_peaks(tth, I, seeds):
    groups, cur = [], [seeds[0]]
    for a, b in zip(seeds, seeds[1:]):
        if b - a < 1.5:
            cur.append(b)
        else:
            groups.append(cur); cur = [b]
    groups.append(cur)

    rows, curves = [], []
    for g in groups:
        m = (tth >= g[0] - 1.0) & (tth <= g[-1] + 1.0)
        x, y = tth[m], I[m]
        sig = np.sqrt(np.maximum(y, 1.0))              # Poisson
        n, xm = len(g), x.mean()

        def model(x, *p, n=n, xm=xm):
            out = p[0] + p[1] * (x - xm)
            for k in range(n):
                x0, A, fw, eta = p[2 + 4*k: 6 + 4*k]
                out = out + doublet(x, x0, A, fw, eta)
            return out

        p0 = [np.percentile(y, 10), 0.0]; lo = [0, -50]; hi = [np.inf, 50]
        for c in g:
            h = y[np.argmin(abs(x - c))]
            p0 += [c, max(h * 0.25, 5), 0.22, 0.5]
            lo += [c - 0.35, 1e-3, 0.06, 0.0]; hi += [c + 0.35, 1e6, 1.2, 1.0]
        pf, cv = curve_fit(model, x, y, p0=p0, sigma=sig, absolute_sigma=True,
                           bounds=(lo, hi), maxfev=400000)
        err = np.sqrt(np.diag(cv))
        chi2 = np.sum(((y - model(x, *pf)) / sig)**2) / (len(x) - len(pf))
        curves.append(dict(x=x, y=y, fit=model(x, *pf), bg=pf[0] + pf[1]*(x - xm)))
        for k in range(n):
            x0, A, fw, eta = pf[2 + 4*k: 6 + 4*k]
            ex0, eA, efw, eeta = err[2 + 4*k: 6 + 4*k]
            rows.append(dict(tth=x0, e_tth=ex0, area=A, e_area=eA, fwhm=fw,
                             e_fwhm=efw, eta=eta, e_eta=eeta, chi2r=chi2,
                             snr=A / eA))
    pk = pd.DataFrame(rows).sort_values('tth').reset_index(drop=True)
    pk['d_A'] = LAM1 / (2 * np.sin(np.radians(pk.tth / 2)))
    return pk, curves


# ---------- 3. lattice ----------
def refine_cubic(pk):
    a0 = pk.d_A.iloc[0] if len(pk) else 6.31
    N = (a0 / pk.d_A.values)**2
    Nint = np.round(N).astype(int)

    def resid(p):
        a, z = p
        tc = 2*np.degrees(np.arcsin(LAM1*np.sqrt(Nint)/(2*a))) + z
        return (tc - pk.tth.values) / pk.e_tth.values

    ls = least_squares(resid, [a0, 0.0])
    J = ls.jac
    cov = np.linalg.inv(J.T @ J) * (ls.fun @ ls.fun) / (len(pk) - 2)
    ea, ez = np.sqrt(np.diag(cov))
    return dict(a=ls.x[0], e_a=ea, zero=ls.x[1], e_zero=ez,
                chi2r=float((ls.fun @ ls.fun) / (len(pk) - 2)),
                N=N, Nint=Nint, obs_minus_calc=(-ls.fun * pk.e_tth.values))


HKL = {1: (1,0,0), 2: (1,1,0), 3: (1,1,1), 4: (2,0,0),
       5: (2,1,0), 6: (2,1,1), 8: (2,2,0), 9: (3,0,0)}
MULT = {1: 6, 2: 12, 3: 8, 4: 6, 5: 24, 6: 24, 8: 12, 9: 6}


# ---------- 4. crystallinity ----------
def crystallinity(tth, I, pk, curves, perov_mask, minor_mask):
    """Crystallinity metrics.

    The absolute degree of crystallinity (DOC) is NOT well determined by a
    single thin-film scan: a very broad amorphous halo is mathematically
    degenerate with the flat instrumental background (air scatter, detector
    noise, fluorescence). We therefore fit an explicit physical background,
      bg(2th) = A*exp(-(2th-5)/tau) + c + halo,
    scan the allowed halo width, and report the DOC as a RANGE, plus
    background-independent relative indices that ARE transferable between
    identically-measured samples.
    """
    step = np.diff(tth).mean()
    y = I.astype(float)

    # background-only channels: mask +/-2.5 FWHM around every fitted peak
    pm = np.zeros(len(tth), bool)
    for _, r in pk.iterrows():
        pm |= np.abs(tth - r.tth) < 2.5 * max(r.fwhm, 0.15)
    free = ~pm
    xf, yf, sf = tth[free], y[free], np.sqrt(np.maximum(y[free], 1))

    def bg_decay(x, A, tau, c):
        return A * np.exp(-(x - tth[0]) / tau) + c

    def bg_halo(x, A, tau, c, H, xc, w):
        return bg_decay(x, A, tau, c) + H * np.exp(-0.5 * ((x - xc) / w)**2)

    p_dec, _ = curve_fit(bg_decay, xf, yf, p0=[20, 5, 25], sigma=sf,
                         absolute_sigma=True, maxfev=100000)
    chi2_dec = np.sum(((yf - bg_decay(xf, *p_dec)) / sf)**2) / (len(xf) - 3)

    halo_scan = []
    for wmax in (3.0, 4.0, 5.0, 6.0, 8.0):
        try:
            ph, _ = curve_fit(bg_halo, xf, yf, p0=[20, 4, 24, 10, 24, min(3, wmax)],
                              sigma=sf, absolute_sigma=True,
                              bounds=([0, .5, 0, 0, 18, 1.], [500, 60, 60, 200, 32, wmax]),
                              maxfev=200000)
            c2 = np.sum(((yf - bg_halo(xf, *ph)) / sf)**2) / (len(xf) - 6)
            ha = np.trapezoid(ph[3] * np.exp(-0.5 * ((tth - ph[4]) / ph[5])**2), tth)
            halo_scan.append(dict(w_max=wmax, chi2r=c2, H=ph[3], centre=ph[4],
                                  sigma=ph[5], halo_area=ha))
        except Exception:
            pass

    bragg_area = float(pk.area[pk.detected].sum())
    perov_area = float(pk.area[perov_mask].sum())
    minor_area = float(pk.area[minor_mask].sum())
    bg_inst = bg_decay(tth, *p_dec)
    above = float(np.trapezoid(np.clip(y - bg_inst, 0, None), tth))

    docs = [100 * bragg_area / (bragg_area + h['halo_area']) for h in halo_scan]
    return dict(
        bragg_area=bragg_area, perovskite_area=perov_area, minor_area=minor_area,
        integral_total=float(np.trapezoid(y, tth)),
        integral_above_inst_bg=above,
        DOC_range=(float(min(docs)), float(max(docs))) if docs else (np.nan, np.nan),
        DOC_lower_bound=float(100 * bragg_area / above) if above else np.nan,
        halo_scan=halo_scan, chi2_decay_only=float(chi2_dec),
        bg_decay_params=p_dec, background=bg_inst,
        bragg_over_total=float(bragg_area / np.trapezoid(y, tth)),
        minor_over_perovskite=float(minor_area / perov_area) if perov_area else np.nan,
        peak_to_background=float(pk.area.max() / (bg_decay(40.4, *p_dec) * step)),
    )


CROMER_MANN = {  # a1-4, b1-4, c  (International Tables for Crystallography C)
    'Pb': ([31.0617, 13.0637, 18.4420, 5.9696], [0.6902, 2.3576, 8.6180, 47.2579], 13.4118),
    'I':  ([20.1472, 18.9949, 7.5138, 2.2735], [4.3470, 0.3814, 27.7660, 66.8776], 4.0712),
    'C':  ([2.3100, 1.0200, 1.5886, 0.8650], [20.8439, 10.2075, 0.5687, 51.6512], 0.2156),
    'N':  ([12.2126, 3.1322, 2.0125, 1.1663], [0.0057, 9.8933, 28.9975, 0.5826], -11.529),
}


def f_atom(el, s):
    a, b, c = CROMER_MANN[el]
    return sum(ai * np.exp(-bi * s * s) for ai, bi in zip(a, b)) + c


def structure_factor(h, k, l, a_cell, B_Pb=1.5, B_I=3.5, B_MA=12.0):
    """|F| for a pseudo-cubic MAPbI3: Pb at origin, I at face centres,
    MA (approximated as C+N) at the body centre."""
    s = np.sqrt(h*h + k*k + l*l) / (2 * a_cell)
    F = f_atom('Pb', s) * np.exp(-B_Pb * s * s)
    F += f_atom('I', s) * np.exp(-B_I * s * s) * ((-1)**h + (-1)**k + (-1)**l)
    F += (f_atom('C', s) + f_atom('N', s)) * np.exp(-B_MA * s * s) * (-1)**(h + k + l)
    return F


def texture_sf(sub, N, a_cell):
    """Harris texture coefficients against a calculated random-powder
    reference: I_calc = multiplicity x Lorentz-polarisation x |F|^2."""
    th = np.radians(sub.tth.values / 2)
    LP = (1 + np.cos(2 * th)**2) / (np.sin(th)**2 * np.cos(th))
    mult = np.array([MULT[n] for n in N])
    Fc = np.array([structure_factor(*HKL[n], a_cell) for n in N])
    Icalc = mult * LP * Fc**2
    Icalc_n = 100 * Icalc / Icalc.max()
    Iobs_n = 100 * sub.area.values / sub.area.values.max()
    TC = Iobs_n / Icalc_n
    TC = TC / TC.mean()
    return pd.DataFrame(dict(hkl=[HKL[n] for n in N], tth=sub.tth.values.round(3),
                             I_obs=Iobs_n.round(1), I_calc=Icalc_n.round(1),
                             TC=TC.round(3)))


def texture(sub, N):
    """Harris texture coefficients vs an untextured powder reference.
    `sub` holds only the indexed perovskite reflections and `N` their h2+k2+l2.
    Reference intensities use multiplicity x Lorentz-polarisation only (no
    structure factors), so this flags RELATIVE preferred orientation."""
    th = np.radians(sub.tth.values / 2)
    LP = (1 + np.cos(2*th)**2) / (np.sin(th)**2 * np.cos(th))
    ref = np.array([MULT.get(n, 6) for n in N]) * LP
    ratio = sub.area.values / ref
    TC = ratio / ratio.mean() * 1.0
    return pd.DataFrame(dict(hkl=[HKL.get(n) for n in N], tth=sub.tth.values,
                             area=sub.area.values, TC=TC))


# ---------- 5. size / strain with Monte-Carlo errors ----------
def size_analysis(pk, nmc=8000, seed=7,
                  inst_scale_range=(0.75, 1.25), eta_i_range=(0.30, 0.80),
                  K_range=(0.89, 1.00)):
    tt, fw, efw, eta = (pk.tth.values, pk.fwhm.values,
                        pk.e_fwhm.values, pk.eta.values)
    th = np.radians(tt / 2)

    b0 = beta_sample(fw, eta, tt)
    db = (beta_sample(fw + efw, eta, tt) - beta_sample(fw - efw, eta, tt)) / 2
    x, y = 4 * np.sin(th), b0 * np.cos(th)
    W = 1 / np.maximum(np.abs(db * np.cos(th)), 1e-12)**2

    sl, ic, esl, eic = wfit(x, y, W)
    chi2_ss = (W * (y - (sl*x + ic))**2).sum() / (len(x) - 2)
    ybar = (W * y).sum() / W.sum()
    chi2_flat = (W * (y - ybar)**2).sum() / (len(x) - 1)

    point = dict(
        D_per_peak_nm=LAM1 / (b0 * np.cos(th)) / 10,
        fwhm_inst=fwhm_inst(tt),
        fwhm_sample_quad=np.sqrt(np.clip(fw**2 - fwhm_inst(tt)**2, 0, None)),
        wh_slope=sl, wh_slope_err=esl, wh_intercept=ic, wh_intercept_err=eic,
        wh_strain_sigma=sl / esl,
        wh_chi2r=chi2_ss, flat_chi2r=chi2_flat,
        D_flat_nm=LAM1 / ybar / 10,
    )
    point['D_scherrer_nm'] = (K_SCHERRER * LAM1 /
                              (np.radians(point['fwhm_sample_quad']) * np.cos(th)) / 10)

    rng = np.random.default_rng(seed)
    Dmc = np.full((nmc, len(tt)), np.nan)
    Dflat = np.full(nmc, np.nan); Dsch = np.full(nmc, np.nan)
    DWH = np.full(nmc, np.nan); EPS = np.full(nmc, np.nan)
    n_used = np.zeros(nmc, int)
    for i in range(nmc):
        fwi_ = fw + rng.normal(0, efw)
        eta_ = np.clip(eta + rng.normal(0, 0.15, len(eta)), 0, 1)
        s = rng.uniform(*inst_scale_range)
        ei = rng.uniform(*eta_i_range)
        K = rng.uniform(*K_range)
        fwi = fwhm_inst(tt) * s
        # A peak whose sampled width falls at/below the instrumental width
        # carries no size information in THIS draw. Dropping the whole draw
        # would truncate the large-D tail (the widths that go sub-instrumental
        # are exactly the ones implying large crystallites), so drop only the
        # affected peaks and keep the draw if >=3 reflections survive.
        keep = fwi_ > fwi * 1.02
        if keep.sum() < 3:
            continue
        n_used[i] = keep.sum()
        b = beta_sample(fwi_[keep], eta_[keep], tt[keep], scale=s, eta_i=ei)
        thk = th[keep]
        Dmc[i, keep] = LAM1 / (b * np.cos(thk)) / 10
        Dsch[i] = np.mean(K * LAM1 /
                          (np.radians(np.sqrt(np.clip(fwi_[keep]**2 - fwi[keep]**2,
                                                      1e-9, None)))
                           * np.cos(thk)) / 10)
        yy = b * np.cos(thk)
        Wi = 1 / np.maximum(np.abs(db[keep] * np.cos(thk)), 1e-12)**2
        Dflat[i] = LAM1 / ((Wi * yy).sum() / Wi.sum()) / 10
        s_, i_, _, _ = wfit(4 * np.sin(thk), yy, Wi)
        if i_ > 0:
            DWH[i] = K * LAM1 / i_ / 10
            EPS[i] = s_ / 4
    return point, dict(D_per_peak=Dmc, D_flat=Dflat, D_scherrer=Dsch,
                       D_WH=DWH, strain=EPS, n_used=n_used,
                       accept_rate=float(np.mean(n_used >= 3)))


def ci(v, lo=15.87, hi=84.13):
    v = np.asarray(v); v = v[np.isfinite(v)]
    if v.size == 0:
        return (np.nan, np.nan, np.nan)
    a, m, b = np.percentile(v, [lo, 50, hi])
    return float(m), float(a), float(b)


SEEDS = [12.600, 14.000, 19.850, 21.050, 22.750, 23.600, 24.400,
         26.350, 28.200, 30.050, 31.700, 34.800, 40.450, 43.000]
SNR_MIN = 4.5
PBI2_TTH = 12.6
# Perovskite reflections: seeds that index on the cubic cell.
PEROV_SEEDS = [14.000, 19.850, 24.400, 28.200, 31.700, 34.800, 40.450, 43.000]


def lrt_peak(tth, I, center, half=1.05):
    """Likelihood-ratio test for a peak at `center` against a local linear
    background. Returns (2th, area, area_err, fwhm, delta_chi2, p).

    This is the DETECTION criterion. The area/err ratio from the global
    multi-peak fit is NOT usable for detection: the peak area is strongly
    anti-correlated with the shared background parameters, which inflates
    the reported error and hides real weak reflections (this is exactly
    what happened to the PbI2 001 line at 12.6 deg).
    """
    from scipy.stats import chi2 as _chi2
    m = (tth > center - half) & (tth < center + half)
    x, y = tth[m], I[m].astype(float)
    s = np.sqrt(np.maximum(y, 1))

    def bg(x, c, sl):
        return c + sl * (x - x.mean())

    def bgpk(x, c, sl, x0, A, fw):
        return c + sl * (x - x.mean()) + doublet(x, x0, A, fw, 0.5)

    pa, _ = curve_fit(bg, x, y, p0=[np.median(y), 0], sigma=s, absolute_sigma=True)
    c2a = np.sum(((y - bg(x, *pa)) / s)**2)
    pb, cb = curve_fit(bgpk, x, y, p0=[np.median(y), 0, center, 15, 0.25],
                       sigma=s, absolute_sigma=True,
                       bounds=([0, -50, center - 0.3, 1e-3, 0.08],
                               [300, 50, center + 0.3, 1e5, 1.0]), maxfev=200000)
    c2b = np.sum(((y - bgpk(x, *pb)) / s)**2)
    dchi = c2a - c2b
    return (pb[2], pb[3], np.sqrt(np.diag(cb))[3], pb[4], dchi,
            float(_chi2.sf(max(dchi, 0.0), 3)))


def run(path, outdir='.'):
    tth, I = load(path)
    pk_all, curves = fit_peaks(tth, I, SEEDS)

    # detection by likelihood-ratio test, Bonferroni-corrected over all seeds
    alpha = 0.05 / len(SEEDS)
    det = [lrt_peak(tth, I, c) for c in SEEDS]
    pk_all['lrt_p'] = [d[5] for d in det]
    pk_all['lrt_dchi2'] = [d[4] for d in det]
    pk_all['detected'] = pk_all.lrt_p < alpha
    pk_all['significant'] = pk_all.detected          # back-compat

    perov = np.array([any(abs(t - s) < 0.4 for s in PEROV_SEEDS)
                      for t in pk_all.tth]) & pk_all.detected.values
    minor = pk_all.detected.values & ~perov
    pk_all['phase'] = np.where(perov, 'perovskite',
                               np.where(minor, 'minor', 'not detected'))
    pkp = pk_all[perov].reset_index(drop=True)

    lat = refine_cubic(pkp)
    pkp['hkl'] = [HKL.get(n) for n in lat['Nint']]
    pkp['N'] = lat['Nint']
    pkp['obs_minus_calc'] = lat['obs_minus_calc']

    cry = crystallinity(tth, I, pk_all, curves, perov, minor)
    tex = texture(pkp, lat['Nint'])
    tex_sf = texture_sf(pkp, lat['Nint'], lat['a'])

    point, mc = size_analysis(pkp)
    pkp['D_IB_nm'] = point['D_per_peak_nm']
    pkp['D_scherrer_nm'] = point['D_scherrer_nm']
    pkp['fwhm_inst'] = point['fwhm_inst']
    return dict(tth=tth, I=I, pk_all=pk_all, pk=pkp, curves=curves,
                lat=lat, cry=cry, tex=tex, tex_sf=tex_sf, point=point, mc=mc)


if __name__ == '__main__':
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else \
        'data/raw/perovskite#control##20260726-095651_100.txt'
    r = run(p)
    print(r['pk'][['tth', 'hkl', 'd_A', 'area', 'fwhm', 'e_fwhm',
                   'D_scherrer_nm', 'D_IB_nm']].round(4).to_string(index=False))
    print('\na = %.4f +/- %.4f A' % (r['lat']['a'], r['lat']['e_a']))
    print('DOC = %.1f %%' % r['cry']['DOC_percent'])
    print('D(flat, vol-wtd) = %.1f nm' % r['point']['D_flat_nm'])



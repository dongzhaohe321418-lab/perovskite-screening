"""Fixed-protocol XRD measurement layer for perovskite thin films.

Design rule: every reported quantity carries its uncertainty DECOMPOSED
(statistical vs systematic vs model-discrepancy) and a comparability status.
Nothing here returns a single "crystallinity" or "phase fraction" number whose
value is actually set by an unstated modelling assumption.
"""
import os
import re
import numpy as np
import pandas as pd

# ---- locked physical constants (Cu Ka; change only via explicit arguments) ----
LAM_KA1 = 1.540598
LAM_KA2 = 1.544426
KA2_RATIO = 0.5
ETA_INST_DEFAULT = 0.55
K_SCHERRER_DEFAULT = 0.9
FWHM_FLOOR = 0.06

# ---- locked texture convention (see SKILL.md "Texture conventions") ----
HKL_BY_N = {1: (1, 0, 0), 2: (1, 1, 0), 3: (1, 1, 1), 4: (2, 0, 0),
            5: (2, 1, 0), 6: (2, 1, 1), 8: (2, 2, 0), 9: (3, 0, 0)}
MULT_BY_N = {1: 6, 2: 12, 3: 8, 4: 6, 5: 24, 6: 24, 8: 12, 9: 6}
TEXTURE_FAMILY = (1, 2, 3, 4, 5, 6, 8, 9)
CROMER_MANN = {
    'Pb': ([31.0617, 13.0637, 18.4420, 5.9696], [0.6902, 2.3576, 8.6180, 47.2579], 13.4118),
    'I': ([20.1472, 18.9949, 7.5138, 2.2735], [4.3470, 0.3814, 27.7660, 66.8776], 4.0712),
    'C': ([2.3100, 1.0200, 1.5886, 0.8650], [20.8439, 10.2075, 0.5687, 51.6512], 0.2156),
    'N': ([12.2126, 3.1322, 2.0125, 1.1663], [0.0057, 9.8933, 28.9975, 0.5826], -11.529),
}
B_PB = 1.5
B_I = 3.5
B_MA = 12.0

# ---- default candidate positions (MAPbI3 pseudo-cubic + common impurities) ----
PEROVSKITE_SEEDS = (14.00, 19.85, 24.40, 28.20, 31.70, 34.80, 40.45, 43.00)
IMPURITY_SEEDS = (12.60, 21.05, 22.75, 23.60, 26.35, 30.05)
PBI2_2H_A = 4.557
PBI2_2H_C = 6.979

STATUS_VALID = "VALID"
STATUS_PROVISIONAL = "PROVISIONAL"
STATUS_NOT_COMPARABLE = "NOT_COMPARABLE"


# =====================  profile shapes  =====================
def pv_profile(x, x0, fw, eta):
    """Area-normalised pseudo-Voigt."""
    s2 = 2.0 * np.sqrt(2.0 * np.log(2.0))
    sg = fw / s2
    g = np.exp(-0.5 * ((x - x0) / sg) ** 2) / (sg * np.sqrt(2.0 * np.pi))
    lo = (fw / (2.0 * np.pi)) / ((x - x0) ** 2 + (fw / 2.0) ** 2)
    return eta * lo + (1.0 - eta) * g


def ka_doublet(x, x0, area, fw, eta, lam1=1.540598, lam2=1.544426, r21=0.5):
    """Ka1+Ka2 pair, Ka2 offset fixed by Bragg's law (NOT refined)."""
    d2 = np.degrees(2.0 * np.tan(np.radians(x0 / 2.0)) * (lam2 - lam1) / lam1)
    return area * (pv_profile(x, x0, fw, eta)
                   + r21 * pv_profile(x, x0 + d2, fw, eta)) / (1.0 + r21)


def pv_to_gl(fw, eta):
    """Thompson-Cox-Hastings inverse: pseudo-Voigt -> (Gaussian, Lorentzian) FWHM."""
    fw = np.atleast_1d(np.asarray(fw, float))
    eta = np.atleast_1d(np.asarray(eta, float))
    q = np.linspace(0.0, 1.0, 4001)
    et = 1.36603 * q - 0.47719 * q ** 2 + 0.11116 * q ** 3
    fl = np.interp(np.clip(eta, 0.0, 1.0), et, q) * fw
    c = (1.0, 2.69269, 2.42843, 4.47163, 0.07842)
    g = fw * np.linspace(0.0, 1.0, 2001)[:, None]
    tot = (g ** 5 + c[1] * g ** 4 * fl + c[2] * g ** 3 * fl ** 2
           + c[3] * g ** 2 * fl ** 3 + c[4] * g * fl ** 4 + fl ** 5) ** 0.2
    fg = np.array([np.interp(fw[i], tot[:, i], g[:, i]) for i in range(len(fw))])
    return fg, fl


def voigt_integral_breadth(fg, fl):
    """Integral breadth of a Voigt from its Gaussian/Lorentzian FWHM parts."""
    from scipy.special import erfc
    fg = np.atleast_1d(np.asarray(fg, float))
    fl = np.atleast_1d(np.asarray(fl, float))
    out = np.empty_like(fg)
    bg = fg * np.sqrt(np.pi / (4.0 * np.log(2.0)))
    bl = fl * np.pi / 2.0
    small = fg <= 1e-9
    out[small] = bl[small]
    k = np.where(small, 0.0, bl / (np.sqrt(np.pi) * np.maximum(bg, 1e-12)))
    ok = (~small) & (k < 25.0)
    big = (~small) & (k >= 25.0)
    out[ok] = bg[ok] * np.exp(-k[ok] ** 2) / erfc(k[ok])
    out[big] = bl[big]
    return out


def caglioti_uvw(anchors=None):
    """Solve Caglioti U,V,W from three (2theta, FWHM) anchor points."""
    if anchors is None:
        anchors = ((14.0, 0.110), (30.0, 0.120), (45.0, 0.135))
    tt = np.array([a[0] for a in anchors], float)
    fw = np.array([a[1] for a in anchors], float)
    t = np.tan(np.radians(tt / 2.0))
    return np.linalg.solve(np.column_stack([t ** 2, t, np.ones(len(t))]), fw ** 2)


def instrument_fwhm(tt, uvw=None):
    """Instrumental FWHM (deg) from a Caglioti curve."""
    if uvw is None:
        uvw = caglioti_uvw()
    t = np.tan(np.radians(np.asarray(tt, float) / 2.0))
    return np.sqrt(np.clip(uvw[0] * t ** 2 + uvw[1] * t + uvw[2], 1e-8, None))


def sample_breadth(fw, eta, tt, uvw=None, scale=1.0, eta_inst=0.55):
    """Sample-only integral breadth (radians) after TCH deconvolution.

    Gaussian parts subtract in quadrature, Lorentzian parts linearly.
    """
    fw = np.atleast_1d(np.asarray(fw, float))
    tt = np.atleast_1d(np.asarray(tt, float))
    fg_o, fl_o = pv_to_gl(fw, eta)
    fwi = instrument_fwhm(tt, uvw) * scale
    fg_i, fl_i = pv_to_gl(fwi, np.full(len(fwi), eta_inst))
    fg_s = np.sqrt(np.clip(fg_o ** 2 - fg_i ** 2, 0.0, None))
    fl_s = np.clip(fl_o - fl_i, 0.0, None)
    return np.radians(voigt_integral_breadth(fg_s, fl_s))


# =====================  metadata / gates  =====================
def scan_meta(wavelength=None, step=None, dwell=None, tth_range=None,
              instrument=None, optics=None, sample_area=None,
              normalisation=None, standard_scan=None, bare_substrate=None,
              label=None):
    """Declare acquisition conditions. Unset fields drive the quality gates."""
    return dict(wavelength=wavelength, step=step, dwell=dwell,
                tth_range=tth_range, instrument=instrument, optics=optics,
                sample_area=sample_area, normalisation=normalisation,
                standard_scan=standard_scan, bare_substrate=bare_substrate,
                label=label)


def protocol_key(meta):
    """Hashable acquisition fingerprint. Absolute intensities are comparable
    ONLY between scans whose protocol_key matches exactly."""
    fields = ('wavelength', 'step', 'dwell', 'tth_range', 'instrument',
              'optics', 'sample_area', 'normalisation')
    return "|".join("%s=%s" % (f, meta.get(f)) for f in fields)


def check_gates(meta):
    """Hard quality gates. Returns dict of allow-flags + human-readable notes."""
    notes = []
    have_lam = meta.get('wavelength') is not None
    have_step = meta.get('step') is not None
    allow_lattice = have_lam and have_step
    if not allow_lattice:
        notes.append("HALT lattice/size: wavelength and/or step size not declared.")
    allow_absolute_size = meta.get('standard_scan') is not None
    if not allow_absolute_size:
        notes.append("Scherrer/integral-breadth size is CONDITIONAL on the assumed "
                     "instrumental resolution (no standard scan supplied).")
    if meta.get('bare_substrate') is None:
        notes.append("Substrate-overlapping reflections stay PROVISIONAL "
                     "(no bare-substrate scan supplied).")
    return dict(allow_lattice=allow_lattice, allow_size=allow_lattice,
                allow_absolute_size=allow_absolute_size,
                substrate_confirmed=meta.get('bare_substrate') is not None,
                notes=notes)


# =====================  peak fitting  =====================
def fit_xrd_peaks(tth, inten, seeds, window=1.0, merge=1.5):
    """Poisson-weighted multi-peak pseudo-Voigt fit with Ka doublet.

    Peaks closer than `merge` degrees share one fit window and one linear
    background. Returns a DataFrame plus per-window fit curves.
    """
    from scipy.optimize import curve_fit
    seeds = sorted(float(s) for s in seeds)
    groups = []
    cur = [seeds[0]]
    for a, b in zip(seeds, seeds[1:]):
        if b - a < merge:
            cur.append(b)
        else:
            groups.append(cur)
            cur = [b]
    groups.append(cur)

    rows = []
    curves = []
    for g in groups:
        m = (tth >= g[0] - window) & (tth <= g[-1] + window)
        x = tth[m]
        y = inten[m].astype(float)
        sig = np.sqrt(np.maximum(y, 1.0))
        n = len(g)
        xm = float(x.mean())

        def model(xx, *p, n=n, xm=xm):
            out = p[0] + p[1] * (xx - xm)
            for k in range(n):
                x0, area, fw, eta = p[2 + 4 * k: 6 + 4 * k]
                out = out + ka_doublet(xx, x0, area, fw, eta)
            return out

        p0 = [float(np.percentile(y, 10)), 0.0]
        lo = [0.0, -50.0]
        hi = [np.inf, 50.0]
        for c in g:
            h = float(y[np.argmin(np.abs(x - c))])
            p0 += [c, max(h * 0.25, 5.0), 0.22, 0.5]
            lo += [c - 0.35, 1e-3, FWHM_FLOOR, 0.0]
            hi += [c + 0.35, 1e6, 1.2, 1.0]
        pf, cv = curve_fit(model, x, y, p0=p0, sigma=sig, absolute_sigma=True,
                           bounds=(lo, hi), maxfev=400000)
        err = np.sqrt(np.diag(cv))
        chi2r = float(np.sum(((y - model(x, *pf)) / sig) ** 2) / (len(x) - len(pf)))
        curves.append(dict(x=x, y=y, fit=model(x, *pf), bg=pf[0] + pf[1] * (x - xm)))
        for k in range(n):
            x0, area, fw, eta = pf[2 + 4 * k: 6 + 4 * k]
            ex0, earea, efw, eeta = err[2 + 4 * k: 6 + 4 * k]
            rows.append(dict(tth=x0, e_tth=ex0, area=area, e_area=earea,
                             fwhm=fw, e_fwhm=efw, eta=eta, e_eta=eeta,
                             window_chi2r=chi2r, at_fwhm_floor=bool(fw <= FWHM_FLOOR * 1.01)))
    pk = pd.DataFrame(rows).sort_values('tth').reset_index(drop=True)
    return pk, curves


# =====================  detection  =====================
def lrt_peak(tth, inten, center, half=1.05):
    """Likelihood-ratio test for one peak vs a local linear background.

    THE detection criterion. Never use area/sigma_area from a multi-peak fit:
    a weak peak's area is anti-correlated with the shared background, which
    inflates its error and hides real reflections.
    Returns (2theta, area, area_err, fwhm, delta_chi2, p_asymptotic).
    """
    from scipy.optimize import curve_fit
    from scipy.stats import chi2
    m = (tth > center - half) & (tth < center + half)
    x = tth[m]
    y = inten[m].astype(float)
    s = np.sqrt(np.maximum(y, 1.0))
    xm = float(x.mean())

    def bg(xx, c, sl):
        return c + sl * (xx - xm)

    def bgpk(xx, c, sl, x0, area, fw):
        return c + sl * (xx - xm) + ka_doublet(xx, x0, area, fw, 0.5)

    c0 = float(np.median(y))
    pa, _ = curve_fit(bg, x, y, p0=[c0, 0.0], sigma=s, absolute_sigma=True, maxfev=40000)
    c2a = float(np.sum(((y - bg(x, *pa)) / s) ** 2))
    pb, cb = curve_fit(bgpk, x, y, p0=[c0, 0.0, center, 15.0, 0.25],
                       sigma=s, absolute_sigma=True,
                       bounds=([0.0, -50.0, center - 0.3, 1e-3, 0.08],
                               [300.0, 50.0, center + 0.3, 1e5, 1.0]), maxfev=200000)
    c2b = float(np.sum(((y - bgpk(x, *pb)) / s) ** 2))
    dchi = c2a - c2b
    return (float(pb[2]), float(pb[3]), float(np.sqrt(np.diag(cb))[3]),
            float(pb[4]), float(dchi), float(chi2.sf(max(dchi, 0.0), 3)))


def lrt_bootstrap(tth, inten, center, n_boot=1200, seed=11, half=1.05):
    """Parametric-bootstrap calibration of `lrt_peak`.

    The added peak amplitude is bounded at A>=0 and its position is searched
    over a window, so the asymptotic chi2(3) null does NOT hold and is
    ANTI-CONSERVATIVE. This simulates Poisson data under the fitted local
    background and returns a calibrated p-value.
    """
    from scipy.optimize import curve_fit
    from scipy.stats import gamma
    m = (tth > center - half) & (tth < center + half)
    x = tth[m]
    y = inten[m].astype(float)
    xm = float(x.mean())
    obs = lrt_peak(tth, inten, center, half)
    dobs = obs[4]

    def bgpk(xx, c, sl, x0, area, fw):
        return c + sl * (xx - xm) + ka_doublet(xx, x0, area, fw, 0.5)

    s = np.sqrt(np.maximum(y, 1.0))
    pbf, _ = curve_fit(bgpk, x, y, p0=[float(np.median(y)), 0.0, center, 10.0, 0.25],
                       sigma=s, absolute_sigma=True,
                       bounds=([0.0, -50.0, center - 0.3, 1e-3, 0.08],
                               [300.0, 50.0, center + 0.3, 1e5, 1.0]), maxfev=200000)
    lam = np.clip(pbf[0] + pbf[1] * (x - xm), 0.05, None)
    rng = np.random.default_rng(seed)
    nulls = []
    for _ in range(int(n_boot)):
        yb = rng.poisson(lam).astype(float)
        try:
            sb = np.sqrt(np.maximum(yb, 1.0))

            def bg(xx, c, sl):
                return c + sl * (xx - xm)

            pa, _ = curve_fit(bg, x, yb, p0=[float(np.median(yb)), 0.0], sigma=sb,
                              absolute_sigma=True, maxfev=20000)
            ca = float(np.sum(((yb - bg(x, *pa)) / sb) ** 2))
            pb2, _ = curve_fit(bgpk, x, yb, p0=[float(np.median(yb)), 0.0, center, 10.0, 0.25],
                               sigma=sb, absolute_sigma=True,
                               bounds=([0.0, -50.0, center - 0.3, 1e-3, 0.08],
                                       [300.0, 50.0, center + 0.3, 1e5, 1.0]), maxfev=60000)
            cb2 = float(np.sum(((yb - bgpk(x, *pb2)) / sb) ** 2))
            nulls.append(max(ca - cb2, 0.0))
        except Exception:
            continue
    nulls = np.asarray(nulls, float)
    pos = nulls[nulls > 0]
    p_emp = float((np.sum(nulls >= dobs) + 1) / (len(nulls) + 1))
    p_gam = np.nan
    eff_dof = np.nan
    if len(pos) > 30:
        shape, _loc, scale = gamma.fit(pos, floc=0)
        p_gam = float(gamma.sf(dobs, shape, loc=0, scale=scale))
        eff_dof = float(2.0 * shape)
    return dict(tth=obs[0], area=obs[1], fwhm=obs[3], delta_chi2=dobs,
                p_asymptotic=obs[5], p_bootstrap=p_gam, p_empirical_floor=p_emp,
                effective_dof=eff_dof, n_null=int(len(nulls)),
                null_q95=float(np.percentile(nulls, 95)) if len(nulls) else np.nan)


def detect_phases(tth, inten, seeds=None, n_boot=1200, seed=11, calibrate=True):
    """Run the LRT over all candidate positions with Bonferroni correction."""
    if seeds is None:
        seeds = tuple(PEROVSKITE_SEEDS) + tuple(IMPURITY_SEEDS)
    seeds = sorted(float(s) for s in seeds)
    alpha = 0.05 / len(seeds)
    rows = []
    for c in seeds:
        if calibrate:
            r = lrt_bootstrap(tth, inten, c, n_boot=n_boot, seed=seed)
            p_use = r['p_bootstrap'] if np.isfinite(r['p_bootstrap']) else r['p_asymptotic']
        else:
            o = lrt_peak(tth, inten, c)
            r = dict(tth=o[0], area=o[1], fwhm=o[3], delta_chi2=o[4],
                     p_asymptotic=o[5], p_bootstrap=np.nan,
                     p_empirical_floor=np.nan, effective_dof=np.nan,
                     n_null=0, null_q95=np.nan)
            p_use = o[5]
        r['seed_tth'] = c
        r['p_used'] = p_use
        r['detected'] = bool(p_use < alpha)
        r['is_perovskite_seed'] = bool(any(abs(c - s) < 0.4 for s in PEROVSKITE_SEEDS))
        rows.append(r)
    out = pd.DataFrame(rows)
    out.attrs['alpha_bonferroni'] = alpha
    out.attrs['n_tested'] = len(seeds)
    return out


# =====================  lattice  =====================
def refine_pseudocubic(pk, wavelength=1.540598):
    """Refine an effective pseudo-cubic cell + zero-point shift.

    Returns BOTH uncertainties, which are different things:
      e_a_formal -- propagated fit errors, weights at face value
      e_a_model  -- formal x sqrt(chi2r) (Birge ratio), inflated for
                    model discrepancy (unresolved tetragonal splitting etc.)
    Report the model-scaled value. This NEVER determines a space group.
    """
    from scipy.optimize import least_squares
    d = wavelength / (2.0 * np.sin(np.radians(pk.tth.values / 2.0)))
    a0 = float(d[0])
    nint = np.round((a0 / d) ** 2).astype(int)
    e_tth = np.maximum(pk.e_tth.values, 1e-4)

    def resid(p):
        tc = 2.0 * np.degrees(np.arcsin(wavelength * np.sqrt(nint) / (2.0 * p[0]))) + p[1]
        return (tc - pk.tth.values) / e_tth

    ls = least_squares(resid, [a0, 0.0])
    dof = max(len(pk) - 2, 1)
    chi2r = float(ls.fun @ ls.fun) / dof
    cov_formal = np.linalg.inv(ls.jac.T @ ls.jac)
    ea_f, ez_f = np.sqrt(np.diag(cov_formal))
    corr = float(cov_formal[0, 1] / np.sqrt(cov_formal[0, 0] * cov_formal[1, 1]))
    birge = float(np.sqrt(chi2r))
    return dict(a=float(ls.x[0]), zero=float(ls.x[1]),
                e_a_formal=float(ea_f), e_a_model=float(ea_f * birge),
                e_zero_formal=float(ez_f), e_zero_model=float(ez_f * birge),
                chi2r=chi2r, birge_ratio=birge, corr_a_zero=corr,
                N=nint, obs_minus_calc=(-ls.fun * e_tth),
                d_spacing=d, wavelength=wavelength)


# =====================  crystallinity  =====================
def crystallinity_metrics(tth, inten, pk, halo_width_bounds=None):
    """Comparative crystallinity indices + a DOC RANGE (never a point value).

    A very broad amorphous halo is mathematically degenerate with the flat
    instrumental background, so the absolute degree of crystallinity is only
    bounded. The indices are `fixed-protocol comparative` -- valid across
    samples ONLY at identical protocol_key.
    """
    from scipy.optimize import curve_fit
    if halo_width_bounds is None:
        halo_width_bounds = (3.0, 4.0, 5.0, 6.0, 8.0)
    y = inten.astype(float)
    step = float(np.diff(tth).mean())
    pm = np.zeros(len(tth), bool)
    for _, r in pk.iterrows():
        pm |= np.abs(tth - r.tth) < 2.5 * max(r.fwhm, 0.15)
    free = ~pm
    xf, yf = tth[free], y[free]
    sf = np.sqrt(np.maximum(yf, 1.0))
    t0 = float(tth[0])

    def bg_decay(x, a, tau, c):
        return a * np.exp(-np.clip((x - t0) / max(tau, 1e-3), -50.0, 50.0)) + c

    def bg_halo(x, a, tau, c, h, xc, w):
        return bg_decay(x, a, tau, c) + h * np.exp(-0.5 * ((x - xc) / w) ** 2)

    p_dec, _ = curve_fit(bg_decay, xf, yf, p0=[20.0, 5.0, 25.0], sigma=sf,
                         absolute_sigma=True, maxfev=100000)
    chi2_dec = float(np.sum(((yf - bg_decay(xf, *p_dec)) / sf) ** 2) / (len(xf) - 3))

    bragg = float(pk.area.sum())
    scan = []
    for wmax in halo_width_bounds:
        try:
            ph, _ = curve_fit(bg_halo, xf, yf,
                              p0=[20.0, 4.0, 24.0, 10.0, 24.0, min(3.0, wmax)],
                              sigma=sf, absolute_sigma=True,
                              bounds=([0, .5, 0, 0, 18, 1.0], [500, 60, 60, 200, 32, wmax]),
                              maxfev=200000)
            c2 = float(np.sum(((yf - bg_halo(xf, *ph)) / sf) ** 2) / (len(xf) - 6))
            ha = float(np.trapezoid(ph[3] * np.exp(-0.5 * ((tth - ph[4]) / ph[5]) ** 2), tth))
            scan.append(dict(w_max=wmax, chi2r=c2, halo_H=float(ph[3]),
                             halo_centre=float(ph[4]), halo_sigma=float(ph[5]),
                             halo_area=ha, doc=100.0 * bragg / (bragg + ha)))
        except Exception:
            continue
    docs = [s['doc'] for s in scan]
    bg_inst = bg_decay(tth, *p_dec)
    total = float(np.trapezoid(y, tth))
    return dict(bragg_area=bragg,
                doc_range=(float(min(docs)), float(max(docs))) if docs else (np.nan, np.nan),
                doc_is_bounded_only=True,
                halo_scan=scan, chi2_decay_only=chi2_dec, halo_improves_fit=bool(
                    scan and min(s['chi2r'] for s in scan) < chi2_dec),
                comparative_index_bragg=bragg,
                comparative_index_bragg_over_total=float(bragg / total),
                comparative_index_peak_over_bg=float(
                    pk.area.max() / (bg_decay(40.4, *p_dec) * step)),
                background=bg_inst, bg_decay_params=p_dec, step=step)


# =====================  texture  =====================
def structure_factor(h, k, l, a_cell):
    """|F| for pseudo-cubic MAPbI3: Pb at origin, I at face centres,
    MA (approximated as C+N) at the body centre. Isotropic B factors."""
    s = np.sqrt(h * h + k * k + l * l) / (2.0 * a_cell)

    def fat(el):
        aa, bb, cc = CROMER_MANN[el]
        return sum(ai * np.exp(-bi * s * s) for ai, bi in zip(aa, bb)) + cc

    f = fat('Pb') * np.exp(-B_PB * s * s)
    f += fat('I') * np.exp(-B_I * s * s) * ((-1) ** h + (-1) ** k + (-1) ** l)
    f += (fat('C') + fat('N')) * np.exp(-B_MA * s * s) * (-1) ** (h + k + l)
    return f


def texture_coefficients(pk, nint, a_cell, exclude_tth=None, tol=0.4):
    """Harris texture coefficients against a CALCULATED random-powder reference.

    Locked conventions (do not vary between compared samples):
      * reference I_calc = multiplicity x Lorentz-polarisation x |F_hkl|^2
      * multiplicity from MULT_BY_N; |F| at the SAME wavelength/cell
      * reflection family fixed to TEXTURE_FAMILY (N = 1,2,3,4,5,6,8,9)
      * reflections within `tol` of any `exclude_tth` (substrate overlap) dropped
      * TC normalised so that mean(TC) = 1 over the reflections USED
    """
    keep = np.array([n in TEXTURE_FAMILY for n in nint])
    if exclude_tth:
        for xt in exclude_tth:
            keep &= np.abs(pk.tth.values - xt) >= tol
    sub = pk[keep]
    ns = np.asarray(nint)[keep]
    if len(sub) < 3:
        return pd.DataFrame(columns=['hkl', 'tth', 'I_obs', 'I_calc', 'TC'])
    th = np.radians(sub.tth.values / 2.0)
    lp = (1.0 + np.cos(2 * th) ** 2) / (np.sin(th) ** 2 * np.cos(th))
    mult = np.array([MULT_BY_N[n] for n in ns], float)
    fc = np.array([structure_factor(*HKL_BY_N[n], a_cell) for n in ns], float)
    icalc = mult * lp * fc ** 2
    icalc_n = 100.0 * icalc / icalc.max()
    iobs_n = 100.0 * sub.area.values / sub.area.values.max()
    tc = iobs_n / icalc_n
    tc = tc / tc.mean()
    return pd.DataFrame(dict(hkl=[HKL_BY_N[n] for n in ns], N=ns,
                             tth=sub.tth.values.round(4),
                             I_obs=iobs_n.round(2), I_calc=icalc_n.round(2),
                             TC=tc.round(4)))


# =====================  size / strain  =====================
def size_analysis(pk, wavelength=1.540598, uvw=None, nmc=6000, seed=7,
                  inst_scale_ci=None, inst_scale_sweep=None,
                  eta_inst_range=None, k_range=None):
    """Volume-weighted domain size with uncertainties kept SEPARATE.

    Returns
      D_nm                 adopted intensity-weighted integral-breadth size
      stat_ci68            counting statistics + profile shape ONLY
      syst_range           envelope over the instrumental-width sweep
      wh_*                 Williamson-Hall; strain reported only if significant
    Never combine stat_ci68 and syst_range into one interval.
    """
    if inst_scale_ci is None:
        inst_scale_ci = (0.75, 1.25)
    if inst_scale_sweep is None:
        inst_scale_sweep = (0.5, 0.7, 0.85, 1.0, 1.15, 1.3, 1.5)
    if eta_inst_range is None:
        eta_inst_range = (0.30, 0.80)
    if k_range is None:
        k_range = (0.89, 1.00)
    tt = pk.tth.values
    fw = pk.fwhm.values
    efw = np.maximum(pk.e_fwhm.values, 1e-4)
    eta = pk.eta.values
    th = np.radians(tt / 2.0)

    b0 = sample_breadth(fw, eta, tt, uvw)
    db = (sample_breadth(fw + efw, eta, tt, uvw)
          - sample_breadth(fw - efw, eta, tt, uvw)) / 2.0
    wts = 1.0 / np.maximum(np.abs(db * np.cos(th)), 1e-12) ** 2
    x = 4.0 * np.sin(th)
    y = b0 * np.cos(th)

    def wfit(xx, yy, ww):
        sw, sx, sy = ww.sum(), (ww * xx).sum(), (ww * yy).sum()
        sxx, sxy = (ww * xx * xx).sum(), (ww * xx * yy).sum()
        det = sw * sxx - sx ** 2
        return ((sw * sxy - sx * sy) / det, (sxx * sy - sx * sxy) / det,
                np.sqrt(sw / det), np.sqrt(sxx / det))

    sl, ic, esl, eic = wfit(x, y, wts)
    ybar = (wts * y).sum() / wts.sum()
    chi2_ss = float((wts * (y - (sl * x + ic)) ** 2).sum() / max(len(x) - 2, 1))
    chi2_flat = float((wts * (y - ybar) ** 2).sum() / max(len(x) - 1, 1))
    strain_sigma = float(sl / esl) if esl > 0 else np.nan
    strain_ok = bool(np.isfinite(strain_sigma) and abs(strain_sigma) > 3.0 and sl > 0)

    d_flat = float(wavelength / ybar / 10.0)

    # statistical-only Monte Carlo (instrument held fixed)
    rng = np.random.default_rng(seed)
    dstat = []
    for _ in range(int(nmc)):
        fwi = fw + rng.normal(0.0, efw)
        etai = np.clip(eta + rng.normal(0.0, 0.15, len(eta)), 0.0, 1.0)
        base = instrument_fwhm(tt, uvw)
        keep = fwi > base * 1.02
        if keep.sum() < 3:
            continue
        b = sample_breadth(fwi[keep], etai[keep], tt[keep], uvw)
        thk = th[keep]
        yy = b * np.cos(thk)
        wk = wts[keep]
        dstat.append(wavelength / ((wk * yy).sum() / wk.sum()) / 10.0)
    dstat = np.asarray(dstat, float)

    # full Monte Carlo (instrument scale + eta_inst + K sampled)
    rng2 = np.random.default_rng(seed + 1)
    dfull = []
    for _ in range(int(nmc)):
        fwi = fw + rng2.normal(0.0, efw)
        etai = np.clip(eta + rng2.normal(0.0, 0.15, len(eta)), 0.0, 1.0)
        sc = rng2.uniform(*inst_scale_ci)
        ei = rng2.uniform(*eta_inst_range)
        base = instrument_fwhm(tt, uvw) * sc
        keep = fwi > base * 1.02
        if keep.sum() < 3:
            continue
        b = sample_breadth(fwi[keep], etai[keep], tt[keep], uvw, scale=sc, eta_inst=ei)
        thk = th[keep]
        yy = b * np.cos(thk)
        wk = wts[keep]
        dfull.append(wavelength / ((wk * yy).sum() / wk.sum()) / 10.0)
    dfull = np.asarray(dfull, float)

    # deterministic systematic sweep
    sweep = []
    for sc in inst_scale_sweep:
        base = instrument_fwhm(tt, uvw) * sc
        keep = fw > base * 1.02
        if keep.sum() < 3:
            sweep.append(dict(scale=sc, D_nm=np.nan, n_used=int(keep.sum())))
            continue
        b = sample_breadth(fw[keep], eta[keep], tt[keep], uvw, scale=sc)
        thk = th[keep]
        wk = wts[keep]
        yy = b * np.cos(thk)
        sweep.append(dict(scale=sc, D_nm=float(wavelength / ((wk * yy).sum() / wk.sum()) / 10.0),
                          n_used=int(keep.sum())))
    sw_vals = [s['D_nm'] for s in sweep if np.isfinite(s['D_nm'])]

    def ci68(v):
        v = np.asarray(v, float)
        v = v[np.isfinite(v)]
        if v.size == 0:
            return (np.nan, np.nan)
        return (float(np.percentile(v, 15.87)), float(np.percentile(v, 84.13)))

    return dict(D_nm=d_flat, stat_ci68=ci68(dstat), stat_plus_inst_ci68=ci68(dfull),
                syst_range=(float(min(sw_vals)), float(max(sw_vals))) if sw_vals else (np.nan, np.nan),
                inst_sweep=sweep, per_peak_D_nm=(wavelength / (b0 * np.cos(th)) / 10.0),
                wh_slope=float(sl), wh_slope_err=float(esl), wh_strain_sigma=strain_sigma,
                wh_intercept=float(ic), wh_chi2r=chi2_ss, flat_chi2r=chi2_flat,
                strain_significant=strain_ok,
                microstrain_percent=(float(sl / 4.0 * 100.0) if strain_ok else None),
                beta_cos_theta=y, four_sin_theta=x, beta_err=np.abs(db * np.cos(th)))


# =====================  impurity quantification  =====================
def pbi2_d_spacing(h, k, l, a=4.557, c=6.979):
    """2H-PbI2 d-spacing (hexagonal)."""
    return 1.0 / np.sqrt((4.0 / 3.0) * (h * h + h * k + k * k) / a ** 2 + l * l / c ** 2)


def impurity_report(det, lat, perov_bragg_area, zero_shift=0.0, substrate_tth=None,
                    tol=0.4):
    """Relative impurity indices. Deliberately returns NO weight fraction:
    with a single observed reflection from a textured platelet phase an
    intensity ratio cannot be converted to wt%.

    Reflections matching `substrate_tth` are tagged `origin='substrate'` and
    EXCLUDED from the film-impurity total -- a substrate line is not a
    secondary phase of the film and must not inflate an impurity ratio.
    """
    rows = []
    lam = lat['wavelength']
    substrate_tth = list(substrate_tth) if substrate_tth else []
    for _, r in det[det.detected & ~det.is_perovskite_seed].iterrows():
        is_sub = any(abs(r.tth - s) < tol for s in substrate_tth)
        tc = r.tth - zero_shift
        d = lam / (2.0 * np.sin(np.radians(tc / 2.0)))
        cand = {'PbI2(001)': pbi2_d_spacing(0, 0, 1), 'PbI2(100)': pbi2_d_spacing(1, 0, 0),
                'PbI2(002)': pbi2_d_spacing(0, 0, 2), 'PbI2(011)': pbi2_d_spacing(0, 1, 1),
                'In2O3/ITO(222)': 2.9210, 'In2O3/ITO(400)': 2.5293,
                'SnO2:F(110)': 3.3500, 'SnO2:F(101)': 2.6440}
        best = sorted(cand.items(), key=lambda kv: abs(kv[1] - d))[:2]
        rows.append(dict(tth_obs=r.tth, tth_corr=tc, d_A=d, area=r.area, fwhm=r.fwhm,
                         p_used=r.p_used,
                         origin=('substrate' if is_sub else 'film'),
                         rel_to_perovskite_pct=100.0 * r.area / perov_bragg_area,
                         best_match=best[0][0], best_delta_d=d - best[0][1],
                         second_match=best[1][0],
                         wt_percent=None,
                         wt_percent_blocked_reason="single reflection + textured phase"))
    df = pd.DataFrame(rows)
    if len(df):
        df.attrs['film_impurity_pct'] = float(
            df.loc[df.origin == 'film', 'rel_to_perovskite_pct'].sum())
    else:
        df.attrs['film_impurity_pct'] = 0.0
    return df


def film_impurity_pct(imp):
    """Film-only impurity total (substrate reflections excluded)."""
    if imp is None or not len(imp):
        return 0.0
    if 'origin' in imp.columns:
        return float(imp.loc[imp.origin == 'film', 'rel_to_perovskite_pct'].sum())
    return float(imp.rel_to_perovskite_pct.sum())


# =====================  mode: single  =====================
def load_pattern(path):
    """Load a two-column 2theta/intensity ASCII scan."""
    raw = np.loadtxt(path)
    return raw[:, 0], raw[:, 1]


def analyse_single(path, meta=None, seeds=None, uvw=None, nmc=6000,
                   n_boot=1200, calibrate=True, substrate_tth=None,
                   allow_assumed_wavelength=False):
    """MODE `single`: phase ID, effective cell, size, impurities, texture.

    Honours the hard quality gates in `check_gates`: without a declared
    wavelength/step the lattice and size blocks are SKIPPED rather than
    silently computed on assumed values.
    """
    tth, inten = load_pattern(path)
    if meta is None:
        meta = scan_meta()
    # HARD GATE: an undeclared wavelength or step halts lattice/size outright.
    # Assuming Cu Ka silently would produce a confident-looking cell and size
    # from an unstated assumption -- exactly what this layer exists to prevent.
    # To proceed on an assumed wavelength the caller must say so explicitly.
    if meta.get('wavelength') is None and allow_assumed_wavelength:
        meta = dict(meta, wavelength=LAM_KA1, wavelength_assumed=True)
    if meta.get('step') is None and len(tth) > 1 and allow_assumed_wavelength:
        meta = dict(meta, step=float(np.diff(tth).mean()), step_assumed=True)
    gates = check_gates(meta)

    det = detect_phases(tth, inten, seeds=seeds, n_boot=n_boot,
                        seed=11, calibrate=calibrate)
    perov_seeds = [s for s in (seeds or PEROVSKITE_SEEDS)
                   if any(abs(s - p) < 0.4 for p in PEROVSKITE_SEEDS)]
    pk_all, curves = fit_xrd_peaks(tth, inten,
                                   sorted(set(list(seeds or (tuple(PEROVSKITE_SEEDS) + tuple(IMPURITY_SEEDS))))))
    # Nearest-seed join by TOLERANCE, never by a rounded key: a fitted centroid
    # can cross a rounding boundary relative to its seed (e.g. seed 30.05 ->
    # fit 30.199) and a round(n) key silently drops exactly those rows.
    pk_all = attach_detection(pk_all, det, tol=0.4)
    pk_all['is_perovskite'] = [bool(any(abs(t - s) < 0.4 for s in PEROVSKITE_SEEDS))
                               for t in pk_all.tth.values]
    pk_all['phase'] = np.where(pk_all.detected & pk_all.is_perovskite, 'perovskite',
                               np.where(pk_all.detected, 'minor', 'not detected'))
    pkp = pk_all[pk_all.detected & pk_all.is_perovskite].reset_index(drop=True)

    out = dict(path=path, meta=meta, gates=gates, tth=tth, intensity=inten,
               peaks=pk_all, perovskite_peaks=pkp, curves=curves, detection=det,
               status=STATUS_VALID if gates['allow_lattice'] else STATUS_NOT_COMPARABLE)

    if not gates['allow_lattice'] or len(pkp) < 3:
        out['status'] = STATUS_NOT_COMPARABLE
        out['halt_reason'] = ("wavelength/step undeclared" if not gates['allow_lattice']
                              else "fewer than 3 indexed perovskite reflections")
        return out

    lat = refine_pseudocubic(pkp, wavelength=meta['wavelength'])
    cry = crystallinity_metrics(tth, inten, pk_all[pk_all.detected], )
    siz = size_analysis(pkp, wavelength=meta['wavelength'], uvw=uvw, nmc=nmc)
    excl = list(substrate_tth) if substrate_tth else [
        float(r.tth) for _, r in pk_all.iterrows()
        if r.phase == 'minor' and r.fwhm > 1.8 * float(np.median(pkp.fwhm.values))]
    tex = texture_coefficients(pkp, lat['N'], lat['a'], exclude_tth=excl)
    imp = impurity_report(det, lat, float(pkp.area.sum()),
                          zero_shift=lat['zero'], substrate_tth=excl)
    out.update(lattice=lat, crystallinity=cry, size=siz, texture=tex,
               impurities=imp, substrate_excluded_tth=excl,
               protocol_key=protocol_key(meta),
               status=STATUS_VALID if gates['substrate_confirmed'] else STATUS_PROVISIONAL)
    return out


def attach_detection(pk, det, tol=0.4):
    """Join detection statistics onto fitted peaks by NEAREST SEED within `tol`.

    Never join on a rounded 2theta key: a fitted centroid may round differently
    from its candidate seed, which silently drops those rows and leaves blank
    detection columns in the exported table.
    """
    pk = pk.copy()
    seeds = np.asarray(det.seed_tth.values, float)
    cols = ['seed_tth', 'delta_chi2', 'p_asymptotic', 'p_bootstrap',
            'p_empirical_floor', 'effective_dof', 'detected']
    idx, gap = [], []
    for t in pk.tth.values:
        j = int(np.argmin(np.abs(seeds - t)))
        idx.append(j)
        gap.append(float(abs(seeds[j] - t)))
    sel = det.iloc[idx].reset_index(drop=True)
    for c in cols:
        if c in sel.columns:
            pk[c] = sel[c].values
    pk['seed_offset'] = gap
    pk['detection_unmatched'] = [g > tol for g in gap]
    if 'detected' in pk.columns:
        pk['detected'] = [bool(d) and g <= tol
                          for d, g in zip(pk['detected'].values, gap)]
    return pk


def write_peak_table(pk, path, float_format='%.10g'):
    """Export a peak table WITHOUT flattening small p-values.

    Rounding p-value columns (e.g. .round(6)) collapses 1e-16 to 0.0 and
    destroys the audit trail, so only well-conditioned columns are rounded.
    """
    safe = ['tth', 'e_tth', 'd_A', 'area', 'e_area', 'fwhm', 'e_fwhm', 'eta',
            'seed_tth', 'seed_offset', 'delta_chi2', 'effective_dof']
    out = pk.copy()
    for c in safe:
        if c in out.columns:
            out[c] = out[c].astype(float).round(6)
    out.to_csv(path, index=False, float_format=float_format)
    return path


# =====================  mode: compare  =====================
def compare_pair(control, treated, label_control='control', label_treated='treated'):
    """MODE `compare`: paired control-vs-treated deltas with split uncertainties.

    Absolute-intensity comparisons are BLOCKED unless protocol_key matches.
    """
    rows = []
    same_protocol = control.get('protocol_key') == treated.get('protocol_key')
    both_ok = (control.get('status') != STATUS_NOT_COMPARABLE
               and treated.get('status') != STATUS_NOT_COMPARABLE)
    if not both_ok:
        status = STATUS_NOT_COMPARABLE
    elif not same_protocol:
        status = STATUS_NOT_COMPARABLE
    elif (control.get('status') == STATUS_PROVISIONAL
          or treated.get('status') == STATUS_PROVISIONAL):
        status = STATUS_PROVISIONAL
    else:
        status = STATUS_VALID

    def add(q, cv, tv, stat=None, syst=None, note='', comparable=True):
        rows.append(dict(quantity=q, control=cv, treated=tv,
                         delta=(tv - cv) if (cv is not None and tv is not None
                                             and np.isscalar(cv) and np.isscalar(tv)) else None,
                         stat_uncertainty=stat, syst_uncertainty=syst,
                         status=(status if comparable else STATUS_NOT_COMPARABLE),
                         note=note))

    if both_ok:
        lc, lt = control['lattice'], treated['lattice']
        add('a_pseudocubic_A', lc['a'], lt['a'],
            stat=float(np.hypot(lc['e_a_formal'], lt['e_a_formal'])),
            syst=float(np.hypot(lc['e_a_model'], lt['e_a_model'])),
            note='effective pseudo-cubic cell; NOT a space-group result')
        add('zero_shift_deg', lc['zero'], lt['zero'],
            stat=float(np.hypot(lc['e_zero_formal'], lt['e_zero_formal'])),
            note='instrument/sample displacement -- separate this from real lattice shift')
        d_true = ((lt['a'] - lc['a']), )
        add('a_shift_beyond_zero_drift', None, None, note=(
            'delta_a = %+.4f A vs combined model uncertainty %.4f A -> %s'
            % (d_true[0], float(np.hypot(lc['e_a_model'], lt['e_a_model'])),
               'SIGNIFICANT' if abs(d_true[0]) > 2 * float(np.hypot(lc['e_a_model'], lt['e_a_model']))
               else 'within uncertainty')))

        sc, st = control['size'], treated['size']
        add('D_nm_instrument_corrected', sc['D_nm'], st['D_nm'],
            stat=float(np.hypot((sc['stat_ci68'][1] - sc['stat_ci68'][0]) / 2.0,
                                (st['stat_ci68'][1] - st['stat_ci68'][0]) / 2.0)),
            syst=float(max(abs(sc['syst_range'][1] - sc['syst_range'][0]),
                           abs(st['syst_range'][1] - st['syst_range'][0])) / 2.0),
            note='systematic largely COMMON-MODE on same instrument -> delta more '
                 'reliable than either absolute value')
        add('microstrain_percent', sc['microstrain_percent'], st['microstrain_percent'],
            note='None = WH slope not significant; reporting suppressed by gate')

        cc, ct = control['crystallinity'], treated['crystallinity']
        add('bragg_integrated', cc['comparative_index_bragg'], ct['comparative_index_bragg'],
            note='absolute intensity -- requires identical protocol',
            comparable=same_protocol)
        add('bragg_over_total', cc['comparative_index_bragg_over_total'],
            ct['comparative_index_bragg_over_total'],
            note='fixed-protocol comparative crystallinity index (NOT '
                 'background-independent: depends on range/dwell/thickness/flux)',
            comparable=same_protocol)
        add('peak_over_background', cc['comparative_index_peak_over_bg'],
            ct['comparative_index_peak_over_bg'], note='data-quality index',
            comparable=same_protocol)
        add('DOC_range_percent', cc['doc_range'], ct['doc_range'],
            note='RANGE not point value; halo width degenerate with flat background')

        ic, it = control['impurities'], treated['impurities']
        cp = film_impurity_pct(ic)
        tp = film_impurity_pct(it)
        add('film_impurity_over_perovskite_pct', cp, tp,
            note='film-only integrated Bragg ratio (substrate lines excluded); '
                 'NO wt% conversion (textured, few reflections)')

        tcc, tct = control['texture'], treated['texture']
        add('texture_TC_spread', (float(tcc.TC.min()), float(tcc.TC.max())) if len(tcc) else None,
            (float(tct.TC.min()), float(tct.TC.max())) if len(tct) else None,
            note='locked convention: mult x LP x |F|^2, fixed family, substrate peaks excluded')
        if len(tcc) and len(tct):
            merged = tcc[['hkl', 'TC']].merge(tct[['hkl', 'TC']], on='hkl',
                                              suffixes=('_c', '_t'), how='inner')
            for _, m in merged.iterrows():
                add('TC_%s' % ''.join(str(i) for i in m.hkl), float(m.TC_c), float(m.TC_t),
                    note='per-reflection texture change')

    df = pd.DataFrame(rows)
    df.attrs['status'] = status
    df.attrs['same_protocol'] = same_protocol
    df.attrs['label_control'] = label_control
    df.attrs['label_treated'] = label_treated
    df.attrs['gate_notes'] = ((control.get('gates', {}).get('notes', []) if both_ok else [])
                              + (treated.get('gates', {}).get('notes', []) if both_ok else []))
    return df


# =====================  mode: batch  =====================
def analyse_batch(entries, meta=None, reference_label=None, **kw):
    """MODE `batch`: run `single` over a series (additive / concentration sweep).

    `entries` is a list of dicts: {'label': str, 'path': str, 'meta': optional}.
    Returns (per-sample results dict, tidy summary DataFrame, comparison list).
    """
    results = {}
    for e in entries:
        m = e.get('meta', meta)
        results[e['label']] = analyse_single(e['path'], meta=m, **kw)
    rows = []
    for lab, r in results.items():
        if r.get('status') == STATUS_NOT_COMPARABLE and 'lattice' not in r:
            rows.append(dict(label=lab, status=r['status'],
                             halt_reason=r.get('halt_reason')))
            continue
        s, l, c = r['size'], r['lattice'], r['crystallinity']
        imp = r['impurities']
        rows.append(dict(label=lab, status=r['status'],
                         a_A=l['a'], e_a_formal=l['e_a_formal'], e_a_model=l['e_a_model'],
                         zero_deg=l['zero'], birge=l['birge_ratio'],
                         D_nm=s['D_nm'], D_stat_lo=s['stat_ci68'][0], D_stat_hi=s['stat_ci68'][1],
                         D_syst_lo=s['syst_range'][0], D_syst_hi=s['syst_range'][1],
                         microstrain_pct=s['microstrain_percent'],
                         bragg=c['comparative_index_bragg'],
                         bragg_over_total=c['comparative_index_bragg_over_total'],
                         peak_over_bg=c['comparative_index_peak_over_bg'],
                         doc_lo=c['doc_range'][0], doc_hi=c['doc_range'][1],
                         film_impurity_pct=film_impurity_pct(imp),
                         protocol_key=r.get('protocol_key')))
    summary = pd.DataFrame(rows)
    comparisons = []
    if reference_label and reference_label in results:
        for lab, r in results.items():
            if lab == reference_label:
                continue
            comparisons.append((lab, compare_pair(results[reference_label], r,
                                                  reference_label, lab)))
    return results, summary, comparisons


def report_lines(res):
    """Human-readable summary with uncertainties kept separate."""
    L = []
    if res.get('status') == STATUS_NOT_COMPARABLE and 'lattice' not in res:
        return ["STATUS: NOT_COMPARABLE -- %s" % res.get('halt_reason')]
    l, s, c = res['lattice'], res['size'], res['crystallinity']
    L.append("STATUS: %s" % res['status'])
    L.append("effective pseudo-cubic a = %.4f A | formal +/- %.4f | model/splitting +/- %.4f "
             "(Birge %.2f, chi2r %.2f)" % (l['a'], l['e_a_formal'], l['e_a_model'],
                                           l['birge_ratio'], l['chi2r']))
    L.append("  NOT a space-group determination; zero-shift %+.4f deg" % l['zero'])
    L.append("D = %.1f nm | statistical 68%% CI %.1f-%.1f nm | instrument-width sensitivity "
             "%.1f-%.1f nm (do NOT merge)" % (s['D_nm'], s['stat_ci68'][0], s['stat_ci68'][1],
                                              s['syst_range'][0], s['syst_range'][1]))
    L.append("microstrain: %s" % ("%.3f %%" % s['microstrain_percent']
                                  if s['microstrain_percent'] is not None
                                  else "not significant (%.1f sigma) -- reporting suppressed"
                                       % s['wh_strain_sigma']))
    L.append("DOC = %.0f-%.0f %% (bounded range, not a point value)" % c['doc_range'])
    L.append("fixed-protocol comparative indices: Bragg %.0f | Bragg/total %.3f | P/B %.0f"
             % (c['comparative_index_bragg'], c['comparative_index_bragg_over_total'],
                c['comparative_index_peak_over_bg']))
    for n in res.get('gates', {}).get('notes', []):
        L.append("  gate: %s" % n)
    return L


# =====================  instrument header + data integrity  =====================
def read_mdi_header(path):
    """Parse acquisition metadata from a .mdi sidecar.

    Line 1 is a free-text instrument string; line 2 is
      start  step  dwell  anode  wavelength  end  npoints

    The declared wavelength is authoritative. It is usually the Cu Ka WEIGHTED
    MEAN (1.54184 A), not Ka1 (1.540598 A) -- silently assuming Ka1 biases every
    d-spacing and hence the refined cell. Returns a dict suitable for
    `scan_meta(**hdr)`; raises ValueError if the numeric line will not parse.
    """
    raw = open(path, 'rb').read().decode('latin-1')
    lines = raw.split('\n')
    if len(lines) < 2:
        raise ValueError("%s: no numeric header line" % path)
    instr = lines[0].strip()
    f = lines[1].split()
    if len(f) < 7:
        raise ValueError("%s: header line has %d fields, need 7" % (path, len(f)))
    return dict(instrument=instr, start=float(f[0]), step=float(f[1]),
                dwell=float(f[2]), anode=f[3], wavelength=float(f[4]),
                end=float(f[5]), npoints=int(f[6]))


def verify_txt_against_mdi(txt_path, mdi_path):
    """Confirm the two-column .txt matches the counts embedded in its .mdi.

    The .mdi body carries trailing footer tokens after the data; only the first
    `npoints` values are counts. Returns (ok, detail).
    """
    hdr = read_mdi_header(mdi_path)
    n = hdr['npoints']
    raw = open(mdi_path, 'rb').read().decode('latin-1')
    body = raw.split('\n', 2)[2] if raw.count('\n') >= 2 else ''
    toks = re.findall(r'(\d+)\.', body)
    if len(toks) < n:
        return False, "mdi body has %d numeric tokens, header declares %d" % (len(toks), n)
    counts = np.array([int(t) for t in toks[:n]], float)
    arr = np.loadtxt(txt_path)
    inten = arr[:, 1]
    if len(inten) != n:
        return False, "txt has %d rows, mdi header declares %d" % (len(inten), n)
    if not np.array_equal(counts, inten):
        bad = int((counts != inten).sum())
        return False, "%d of %d intensity values differ between txt and mdi" % (bad, n)
    return True, "txt matches mdi for all %d points (footer tokens %s ignored)" % (n, toks[n:])


# =====================  substrate referencing + geometry diagnostics  ============
def fit_substrate_line(tth, inten, seed, half=1.1):
    """Fit the substrate reflection. Returns dict with position, area, FWHM."""
    out = lrt_peak(tth, inten, seed, half=half)
    return dict(tth=float(out[0]), area=float(out[1]), e_area=float(out[2]),
                fwhm=float(out[3]), delta_chi2=float(out[4]), p_asymptotic=float(out[5]))


def substrate_reference(patterns, substrate_seed, reference_label=None, half=1.1):
    """Measure the substrate reflection in every scan and reference to one sample.

    `patterns` maps label -> (tth, intensity). The substrate is physically the
    SAME under every film, so any change in its line is instrumental. The
    returned `zero_offset` is the per-sample angular offset to SUBTRACT before
    any lattice comparison.

    Deliberately relative: the observed substrate angle can sit a constant
    offset from its literature value (geometry, sample height, transparency),
    so it is a differential reference, not an absolute angle standard.
    """
    labels = list(patterns)
    ref = reference_label if reference_label in patterns else labels[0]
    rows = []
    for lab in labels:
        tt, ii = patterns[lab]
        f = fit_substrate_line(tt, ii, substrate_seed, half=half)
        f['sample'] = lab
        rows.append(f)
    df = pd.DataFrame(rows)
    ref_tth = float(df.loc[df['sample'] == ref, 'tth'].iloc[0])
    df['zero_offset'] = df.tth - ref_tth
    df['reference'] = ref
    return df


def geometry_diagnostics(patterns, sub_df, perov_peaks, reference_label=None,
                         slope_tol=0.30, r_pos_min=0.80, r_width_max=0.60):
    """Decide whether lattice and size differences between scans are real.

    Two tests, both anchored on the substrate reflection:

    POSITION -- regress each film's perovskite 100 shift on its substrate shift.
    A slope near 1 with high r means the film peaks move WITH the substrate,
    i.e. a common geometric offset (sample height / displacement), not a lattice
    change. Delta-a is then NOT COMPARABLE.

    WIDTH -- correlate film peak width with substrate peak width. The substrate
    cannot broaden, so a strong positive correlation means the instrumental
    contribution differed between scans and Delta-D is NOT COMPARABLE.

    Also reports whether the substrate line is BROADER than the film peaks. If
    it is, its width is dominated by the substrate's own grain size and it
    cannot serve as a resolution standard -- deconvolving it drives the apparent
    size to infinity.
    """
    labels = list(patterns)
    ref = reference_label if reference_label in patterns else labels[0]
    sub = sub_df.set_index('sample')
    shift_sub, shift_100, fwhm_film, fwhm_sub, dnm = [], [], [], [], []
    for lab in labels:
        pk = perov_peaks[lab]
        shift_sub.append(float(sub.loc[lab, 'zero_offset']))
        shift_100.append(float(pk.tth.iloc[0]) - float(perov_peaks[ref].tth.iloc[0]))
        fwhm_film.append(float(np.median(pk.fwhm)))
        fwhm_sub.append(float(sub.loc[lab, 'fwhm']))
    shift_sub = np.asarray(shift_sub); shift_100 = np.asarray(shift_100)
    fwhm_film = np.asarray(fwhm_film); fwhm_sub = np.asarray(fwhm_sub)

    def _fit(x, y):
        if np.ptp(x) < 1e-9:
            return np.nan, np.nan, np.nan
        s, i = np.polyfit(x, y, 1)
        r = float(np.corrcoef(x, y)[0, 1])
        return float(s), float(i), r

    slope_pos, icept_pos, r_pos = _fit(shift_sub, shift_100)
    _, _, r_width = _fit(fwhm_sub, fwhm_film)

    # Robustness of the position test to the reference sample.
    #
    # The reference film sits at (0, 0) by construction, which invites the
    # question of whether it is propping the fit up. It is not: subtracting a
    # reference is a rigid translation of both axes, and slope and r are
    # translation-invariant, so the fitted line is identical whether you work
    # in shifts or in absolute angles. The reference point is a real
    # measurement that happens to land on the origin, not a fabricated anchor.
    #
    # What IS worth reporting is leave-one-out: refit with each sample in turn
    # removed (re-referencing to another film), so a verdict that hangs on one
    # scan is visible. Both are returned rather than argued about.
    idx = np.arange(len(labels))
    loo = []
    for i, lab in enumerate(labels):
        m = idx != i
        xs = shift_sub - shift_sub[i]
        ys = shift_100 - shift_100[i]
        s_i, _, r_i = _fit(xs[m], ys[m])
        loo.append(dict(dropped=lab, n=int(m.sum()), slope=s_i, r=r_i))
    loo_slopes = np.array([d['slope'] for d in loo], float)
    loo_r = np.array([d['r'] for d in loo], float)
    loo_stable = bool(np.all(np.isfinite(loo_slopes))
                      and np.all(np.abs(loo_slopes - 1.0) <= slope_tol)
                      and np.all(np.abs(loo_r) >= r_pos_min))

    pos_contaminated = (np.isfinite(r_pos) and abs(r_pos) >= r_pos_min
                        and abs(slope_pos - 1.0) <= slope_tol)
    width_contaminated = np.isfinite(r_width) and r_width >= r_width_max
    sub_broader = {lab: bool(sub.loc[lab, 'fwhm'] > perov_peaks[lab].fwhm.max())
                   for lab in labels}
    usable_as_standard = not any(sub_broader.values())

    notes = []
    if pos_contaminated:
        notes.append("perovskite shift tracks substrate shift (slope %.2f, r %.3f): "
                     "Delta-a NOT COMPARABLE across these scans" % (slope_pos, r_pos))
    if width_contaminated:
        notes.append("film width tracks substrate width (r %+.3f): "
                     "Delta-D NOT COMPARABLE across these scans" % r_width)
    if not usable_as_standard:
        notes.append("substrate line is broader than the film peaks in %d/%d scans, so it is "
                     "grain-size limited and CANNOT be used as a resolution standard"
                     % (sum(sub_broader.values()), len(labels)))
    if pos_contaminated and not loo_stable:
        notes.append("position verdict is NOT stable to leave-one-out (slopes %.2f-%.2f): it "
                     "leans on a single scan and should be treated as provisional"
                     % (np.nanmin(loo_slopes), np.nanmax(loo_slopes)))
    if not notes:
        notes.append("no substrate-linked contamination detected at the configured thresholds")

    return dict(
        labels=labels, reference=ref,
        substrate_shift=shift_sub, perov_100_shift=shift_100,
        substrate_fwhm=fwhm_sub, perov_fwhm_median=fwhm_film,
        slope_position=slope_pos, r_position=r_pos, r_width=r_width,
        substrate_shift_span=float(np.ptp(shift_sub)),
        substrate_fwhm_span_pct=float(100 * np.ptp(fwhm_sub) / np.mean(fwhm_sub)),
        lattice_comparable=not pos_contaminated,
        size_comparable=not width_contaminated,
        substrate_usable_as_resolution_standard=usable_as_standard,
        substrate_broader_than_film=sub_broader,
        leave_one_out=pd.DataFrame(loo),
        leave_one_out_stable=loo_stable,
        notes=notes)


# =====================  the standing protocol: analyse_series  =====================
def analyse_series(files, substrate_seed, reference_label=None, perov_seeds=None,
                   extra_seeds=None, nmc=1500, n_boot=400, seed=11,
                   allow_assumed_wavelength=False):
    """MODE `series`: the full fixed protocol on a set of scans measured together.

    `files` maps label -> path to the two-column .txt. A sibling `.mdi` with the
    same stem is read when present, and its declared wavelength/step/dwell are
    used -- never assumed.

    Runs, in order:
      1. header parse + txt/mdi integrity check
      2. protocol-identity check across all scans (absolute-intensity gate)
      3. substrate referencing -> per-sample zero offset
      4. geometry diagnostics -> lattice_comparable / size_comparable verdicts
      5. per-sample peak fit, bootstrap-calibrated detection, lattice, size,
         texture, impurities, crystallinity
      6. within-scan ratios (immune to alignment/flux) and cross-sample indices

    Every comparative quantity comes back with a status. Quantities the
    diagnostics rule out are computed but flagged NOT_COMPARABLE rather than
    silently reported.
    """
    labels = list(files)
    ref = reference_label if reference_label in files else labels[0]
    perov_seeds = list(perov_seeds) if perov_seeds is not None else list(PEROVSKITE_SEEDS)
    extra_seeds = list(extra_seeds) if extra_seeds is not None else \
        [s for s in IMPURITY_SEEDS if abs(s - substrate_seed) > 0.5]

    # ---- 1. headers + integrity ----
    meta_by, integrity = {}, {}
    for lab, p in files.items():
        mdi = os.path.splitext(p)[0] + '.mdi'
        if os.path.exists(mdi):
            hdr = read_mdi_header(mdi)
            ok, detail = verify_txt_against_mdi(p, mdi)
            integrity[lab] = dict(checked=True, ok=bool(ok), detail=detail)
            meta_by[lab] = scan_meta(wavelength=hdr['wavelength'], step=hdr['step'],
                                     dwell=hdr['dwell'], tth_range=(hdr['start'], hdr['end']),
                                     instrument=hdr['instrument'], label=lab)
        else:
            integrity[lab] = dict(checked=False, ok=None,
                                  detail="no .mdi sidecar; metadata must be supplied by hand")
            meta_by[lab] = scan_meta(label=lab)

    missing = [l for l in labels if meta_by[l].get('wavelength') is None]
    if missing and not allow_assumed_wavelength:
        return dict(status='NOT_COMPARABLE', labels=labels, integrity=integrity,
                    gates=dict(notes=["wavelength/step undeclared for %s -- lattice and size "
                                      "HALTED. Supply metadata or pass "
                                      "allow_assumed_wavelength=True (which flags the "
                                      "assumption)." % ', '.join(missing)]),
                    meta=meta_by)

    # ---- 2. protocol identity ----
    keys = {l: protocol_key(meta_by[l]) for l in labels}
    same_protocol = len(set(keys.values())) == 1
    lam = float(meta_by[ref]['wavelength'])

    # ---- 3. substrate referencing ----
    patterns = {l: load_pattern(files[l]) for l in labels}
    sub_df = substrate_reference(patterns, substrate_seed, reference_label=ref)
    zoff = dict(zip(sub_df['sample'], sub_df['zero_offset']))

    # ---- 4/5. per-sample analysis on offset-tracked seeds ----
    per, perov_peaks = {}, {}
    for lab in labels:
        tt, ii = patterns[lab]
        z = float(zoff[lab])
        seeds = sorted([s + z for s in perov_seeds] +
                       [s + z for s in extra_seeds] + [substrate_seed + z])
        det = detect_phases(tt, ii, seeds=seeds, n_boot=n_boot, seed=seed, calibrate=True)
        pk, curves = fit_xrd_peaks(tt, ii, seeds)
        pk = attach_detection(pk, det, tol=0.45)
        shifted = [s + z for s in perov_seeds]
        pk['is_perovskite'] = [bool(any(abs(t - s) < 0.45 for s in shifted)) for t in pk.tth]
        pk['phase'] = np.where(pk.detected & pk.is_perovskite, 'perovskite',
                               np.where(pk.detected, 'minor', 'not detected'))
        pkp = pk[pk.detected & pk.is_perovskite].reset_index(drop=True)
        perov_peaks[lab] = pkp
        pkc = pkp.copy(); pkc['tth'] = pkc.tth - z          # substrate-referenced
        lat = refine_pseudocubic(pkc, wavelength=lam)
        sub_tth = float(sub_df.loc[sub_df['sample'] == lab, 'tth'].iloc[0])
        per[lab] = dict(
            tth=tt, intensity=ii, peaks=pk, perovskite_peaks=pkp, detection=det,
            curves=curves, lattice=lat, zero_offset=z, substrate_tth=sub_tth,
            crystallinity=crystallinity_metrics(tt, ii, pk[pk.detected]),
            size=size_analysis(pkp, wavelength=lam, nmc=nmc),
            texture=texture_coefficients(pkp, lat['N'], lat['a'], exclude_tth=[sub_tth]),
            impurities=impurity_report(det, lat, float(pkp.area.sum()),
                                       zero_shift=0.0, substrate_tth=[sub_tth]),
            meta=meta_by[lab], integrity=integrity[lab])

    geo = geometry_diagnostics(patterns, sub_df, perov_peaks, reference_label=ref)

    # ---- 6. comparative table with per-quantity status ----
    rows = []
    for lab in labels:
        r = per[lab]; imp = r['impurities']
        sub_area = float(imp.loc[imp.origin == 'substrate', 'area'].sum()) if len(imp) else np.nan
        perov_area = float(r['perovskite_peaks'].area.sum())
        rows.append(dict(
            sample=lab, is_reference=(lab == ref),
            a_A=r['lattice']['a'], e_a_formal=r['lattice']['e_a_formal'],
            e_a_model=r['lattice']['e_a_model'], birge=r['lattice']['birge_ratio'],
            D_nm=r['size']['D_nm'],
            D_stat_lo=r['size']['stat_ci68'][0], D_stat_hi=r['size']['stat_ci68'][1],
            D_syst_lo=r['size']['syst_range'][0], D_syst_hi=r['size']['syst_range'][1],
            perov_bragg=perov_area,
            perov_over_substrate=perov_area / sub_area if sub_area else np.nan,
            bragg_over_total=r['crystallinity']['comparative_index_bragg_over_total'],
            doc_lo=r['crystallinity']['doc_range'][0],
            doc_hi=r['crystallinity']['doc_range'][1],
            film_impurity_pct=film_impurity_pct(imp),
            substrate_tth=r['substrate_tth'], zero_offset=r['zero_offset'],
            substrate_fwhm=float(sub_df.loc[sub_df['sample'] == lab, 'fwhm'].iloc[0]),
            perov_fwhm_median=float(np.median(r['perovskite_peaks'].fwhm)),
            lattice_status='VALID' if geo['lattice_comparable'] else 'NOT_COMPARABLE',
            size_status='VALID' if geo['size_comparable'] else 'NOT_COMPARABLE',
            intensity_status='VALID' if same_protocol else 'NOT_COMPARABLE',
            protocol_key=keys[lab],
            integrity_ok=integrity[lab]['ok']))
    comp = pd.DataFrame(rows)

    status = 'VALID'
    if not same_protocol or not (geo['lattice_comparable'] and geo['size_comparable']):
        status = 'PROVISIONAL'
    if any(v['ok'] is False for v in integrity.values()):
        status = 'NOT_COMPARABLE'

    gate_notes = list(geo['notes'])
    if not same_protocol:
        gate_notes.append("acquisition protocol differs between scans: absolute-intensity "
                          "comparison FORBIDDEN; use within-scan ratios only")
    for lab, v in integrity.items():
        if v['ok'] is False:
            gate_notes.append("%s: data integrity FAILED -- %s" % (lab, v['detail']))
        elif v['checked'] is False:
            gate_notes.append("%s: no .mdi sidecar, metadata unverified" % lab)

    return dict(status=status, labels=labels, reference=ref, per_sample=per,
                substrate=sub_df, geometry=geo, comparison=comp,
                same_protocol=same_protocol, integrity=integrity,
                wavelength=lam, meta=meta_by, gates=dict(notes=gate_notes))


def series_report_lines(res):
    """Terse text summary of a `series` run -- what is usable and what is not."""
    L = ["status: %s   (reference sample: %s)" % (res['status'], res.get('reference'))]
    if 'comparison' not in res:
        return L + ["  gate: %s" % n for n in res.get('gates', {}).get('notes', [])]
    g = res['geometry']
    L.append("wavelength %.5f A (declared, not assumed)" % res['wavelength'])
    L.append("substrate line drifts %.3f deg; its FWHM varies %.0f%% across scans"
             % (g['substrate_shift_span'], g['substrate_fwhm_span_pct']))
    L.append("  position test: slope %.2f, r %.3f  -> lattice %s"
             % (g['slope_position'], g['r_position'],
                'comparable' if g['lattice_comparable'] else 'NOT COMPARABLE'))
    L.append("  width test:    r %+.3f            -> size %s"
             % (g['r_width'], 'comparable' if g['size_comparable'] else 'NOT COMPARABLE'))
    for n in res['gates']['notes']:
        L.append("  gate: %s" % n)
    return L

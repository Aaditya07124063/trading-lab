"""Statistical inference for ORB v1 (approved 2026-10-01).

Primary test: H0 mean daily net portfolio return <= 0 vs H1 > 0, one-sided,
alpha = 0.05, using a NULL-CENTRED stationary bootstrap (Politis & Romano
1994) of the daily series, which allows for day-to-day dependence.

    p = (1 + #{ mean*_b - xbar >= xbar }) / (B + 1)

i.e. the bootstrap distribution of (mean* - xbar) stands in for the sampling
distribution of (xbar - mu) under H0 (mu = 0). This is deliberately NOT the
construction of SSRN 5198458 (share of mean* >= xbar), which is ~0.5 for any
true effect - see docs/protocols/ORB_v1_verification_20261001.md.

The same bootstrap draws give the one-sided 95% lower bound
(xbar - q95(mean* - xbar)), so  p < alpha  <=>  lower bound > 0  (up to ties),
the one-sided 95% upper bound, and a two-sided 95% basic-bootstrap CI.

Block length: Politis & White (2004) automatic selection for the stationary
bootstrap, with the correction of Patton, Politis & White (2009).
"""

import math

import numpy as np
from scipy import stats

ALPHA = 0.05
B_DEFAULT = 10_000
SEED_DEFAULT = 20261001


# ------------------------------------------------------------- block length

def _flat_top(t):
    t = abs(t)
    return 1.0 if t <= 0.5 else (2.0 * (1.0 - t) if t <= 1.0 else 0.0)


def politis_white_block_length(x):
    """Expected block length for the STATIONARY bootstrap of the mean of x."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n < 8:
        raise ValueError("need at least 8 observations for block-length selection")
    x = x - x.mean()
    kn = max(5, math.ceil(math.sqrt(math.log10(n))))
    mmax = math.ceil(math.sqrt(n)) + kn
    bmax = math.ceil(min(3 * math.sqrt(n), n / 3))
    c = 2.0
    var = np.dot(x, x) / n
    if var == 0:
        return 1.0
    acv = np.array([np.dot(x[: n - k], x[k:]) / n for k in range(mmax + kn + 1)])
    rho = acv / acv[0]
    thresh = c * math.sqrt(math.log10(n) / n)
    mhat = None
    for m in range(1, mmax + 1):                      # first m after which kn lags are insignificant
        if all(abs(rho[m + j]) < thresh for j in range(1, kn + 1) if m + j < len(rho)):
            mhat = m
            break
    if mhat is None:
        mhat = mmax
    big_m = min(2 * mhat, mmax)
    lam = np.array([_flat_top(k / big_m) for k in range(big_m + 1)])
    ks = np.arange(big_m + 1)
    g = 2.0 * np.sum(lam[1:] * ks[1:] * acv[1:big_m + 1])
    g0 = acv[0] + 2.0 * np.sum(lam[1:] * acv[1:big_m + 1])
    d_sb = 2.0 * g0 ** 2
    if g == 0 or d_sb == 0:
        return 1.0
    b = (2.0 * g ** 2 / d_sb) ** (1.0 / 3.0) * n ** (1.0 / 3.0)
    return float(min(max(b, 1.0), bmax))


# ------------------------------------------------------- stationary bootstrap

def stationary_bootstrap_means(x, mean_block, b=B_DEFAULT, seed=SEED_DEFAULT, chunk=1000):
    """B means of stationary-bootstrap resamples (geometric blocks, mean length
    `mean_block`, circular wrap)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    p = 1.0 / max(float(mean_block), 1.0)
    rng = np.random.default_rng(seed)
    out = np.empty(b)
    done = 0
    while done < b:
        m = min(chunk, b - done)
        idx = np.empty((m, n), dtype=np.int64)
        idx[:, 0] = rng.integers(0, n, m)
        new = rng.random((m, n)) < p
        starts = rng.integers(0, n, (m, n))
        for t in range(1, n):
            idx[:, t] = np.where(new[:, t], starts[:, t], (idx[:, t - 1] + 1) % n)
        out[done:done + m] = x[idx].mean(axis=1)
        done += m
    return out


def mean_inference(x, mean_block=None, b=B_DEFAULT, seed=SEED_DEFAULT, alpha=ALPHA,
                   periods_per_year=252):
    """Primary-style inference on the mean of a daily series (one-sided H1: mu > 0)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    xbar = float(x.mean())
    sd = float(x.std(ddof=1)) if n > 1 else float("nan")
    block = politis_white_block_length(x) if mean_block is None else float(mean_block)
    dev = stationary_bootstrap_means(x, block, b, seed) - xbar       # ~ (xbar - mu)
    se = float(dev.std(ddof=1))
    p = (1 + int(np.sum(dev >= xbar))) / (b + 1)
    lower_1s = xbar - float(np.quantile(dev, 1 - alpha))
    upper_1s = xbar - float(np.quantile(dev, alpha))
    ci2 = (xbar - float(np.quantile(dev, 1 - alpha / 2)), xbar - float(np.quantile(dev, alpha / 2)))
    return {
        "n": n, "mean": xbar, "sd": sd, "se_bootstrap": se,
        "t_bootstrap": xbar / se if se > 0 else float("nan"),
        "p_one_sided": p, "alpha": alpha,
        "lower_1s_95": lower_1s, "upper_1s_95": upper_1s,
        "ci95_two_sided": ci2,
        "sharpe_annual": xbar / sd * math.sqrt(periods_per_year) if sd and sd > 0 else float("nan"),
        "long_run_sd": se * math.sqrt(n),
        "block_length": block, "B": b, "seed": seed,
        "method": "null-centred stationary bootstrap (Politis-Romano), one-sided",
    }


def verdict(res):
    """Reporting category ONLY (not an optimisation target):
    POSITIVE     one-sided p < alpha (equivalently 95% one-sided lower bound > 0)
    NEGATIVE     95% one-sided upper bound < 0 (mean net return credibly below zero)
    INCONCLUSIVE otherwise."""
    if res["p_one_sided"] < res["alpha"] and res["lower_1s_95"] > 0:
        return "POSITIVE"
    if res["upper_1s_95"] < 0:
        return "NEGATIVE"
    return "INCONCLUSIVE"


# ------------------------------------------------ randomisation p-values etc.

def randomisation_p(observed, draws):
    """One-sided: share of draws at least as large as observed (+1 smoothing)."""
    draws = np.asarray(draws)
    return (1 + int(np.sum(draws >= observed))) / (len(draws) + 1)


def holm(pvalues):
    """Holm step-down adjusted p-values. pvalues: dict name -> p."""
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    m, run, out = len(items), 0.0, {}
    for i, (k, p) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p))
        out[k] = run
    return out


def minimum_detectable_effect(long_run_sd, n, alpha=ALPHA, power=0.80):
    """Smallest true mean detectable with `power` by a one-sided level-alpha
    test, normal approximation with a dependence-adjusted (long-run) sd."""
    return (stats.norm.isf(alpha) + stats.norm.ppf(power)) * long_run_sd / math.sqrt(n)


# ------------------------------------------------- deflated Sharpe (REPORTING ONLY)

def deflated_sharpe(x, n_trials, sr_var=None):
    """Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014) - REPORTING ONLY,
    never part of the verdict.

    Question: given that the best of `n_trials` independent strategy
    configurations was selected, what is the probability that the true
    (per-period) Sharpe ratio of this one exceeds the Sharpe a lucky
    zero-skill selection would show? Assumptions: trials independent;
    returns i.i.d. (no autocorrelation) but possibly skewed/fat-tailed;
    `sr_var` = variance of Sharpe estimates across trials - unknown here, so
    by default the null sampling variance 1/(T-1) of a per-period Sharpe.
    n_trials = 1 reduces to the Probabilistic Sharpe Ratio against 0."""
    x = np.asarray(x, dtype=float)
    t = len(x)
    sd = x.std(ddof=1)
    if not sd > 0:
        return {"dsr": None, "n_trials": int(n_trials), "T": t, "note": "undefined: zero variance"}
    sr = x.mean() / sd
    z = (x - x.mean()) / x.std(ddof=0)
    skew, kurt = float(np.mean(z ** 3)), float(np.mean(z ** 4))
    v = 1.0 / (t - 1) if sr_var is None else sr_var
    g = 0.5772156649015329                                       # Euler-Mascheroni
    sr0 = 0.0 if n_trials <= 1 else math.sqrt(v) * (
        (1 - g) * stats.norm.ppf(1 - 1 / n_trials) + g * stats.norm.ppf(1 - 1 / (n_trials * math.e)))
    denom = math.sqrt(max(1 - skew * sr + (kurt - 1) / 4 * sr ** 2, 1e-12))
    return {"dsr": float(stats.norm.cdf((sr - sr0) * math.sqrt(t - 1) / denom)),
            "sr_per_period": float(sr), "sr0_per_period": float(sr0), "n_trials": int(n_trials),
            "sr_var": v, "skew": skew, "kurtosis": kurt, "T": t,
            "note": "reporting only; not used for the verdict"}

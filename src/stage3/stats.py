"""S2-MOM-v1 statistics (protocol §15): Newey-West test of a mean and stationary-bootstrap robustness.

Only what the frozen protocol needs. Block-length selection and the resampler are reused from
src/intraday/inference.py (imported, never modified). Unit-tested on synthetic series only.
"""

import math

import numpy as np
from scipy import stats

from src.intraday.inference import politis_white_block_length, stationary_bootstrap_means


def newey_west_lrv(x, lag):
    """Long-run variance of x: Bartlett kernel, `lag` lags, autocovariances divided by n."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n <= lag + 1:
        raise ValueError("series too short for the Newey-West lag")
    d = x - x.mean()
    lrv = np.dot(d, d) / n
    for k in range(1, lag + 1):
        lrv += 2.0 * (1.0 - k / (lag + 1.0)) * np.dot(d[k:], d[:-k]) / n
    return float(lrv)


def mean_test(x, lag):
    """Two-sided test of H0: mean = 0 with a Newey-West standard error; p-value and interval from
    the asymptotic standard normal distribution (reviewer decision 5; no t(n-1) variant)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    se = math.sqrt(newey_west_lrv(x, lag) / n)
    mean = float(x.mean())
    t = mean / se if se > 0 else float("nan")
    p, crit90 = 2 * stats.norm.sf(abs(t)), stats.norm.ppf(0.95)
    return {"n": n, "mean": mean, "se_nw": se, "t": t, "p_two_sided": float(p), "lag": lag,
            "ci90": (mean - crit90 * se, mean + crit90 * se), "distribution": "NORMAL"}


def bootstrap_test(x, seed, b):
    """Stationary bootstrap (Politis & Romano 1994), automatic block length (Politis & White 2004,
    corrected 2009), null-centred, two-sided: p = (1 + #{|mean* - xbar| >= |xbar|}) / (B + 1)."""
    x = np.asarray(x, dtype=float)
    block = politis_white_block_length(x)
    dev = stationary_bootstrap_means(x, block, b, seed) - x.mean()
    p = (1 + int(np.sum(np.abs(dev) >= abs(x.mean())))) / (b + 1)
    return {"n": len(x), "p_two_sided": p, "block_length": block, "B": b, "seed": seed,
            "se_bootstrap": float(dev.std(ddof=1))}


def blinded_precision(delta, lag, threshold):
    """Protocol §15 blinded precision step. Returns dispersion only - never the mean, a
    t-statistic, a p-value or any performance figure of `delta`."""
    x = np.asarray(delta, dtype=float)
    n = len(x)
    d = x - x.mean()                     # centred internally; the centre itself is not returned
    sd = float(d.std(ddof=1))
    lr_sd = math.sqrt(newey_west_lrv(x, lag))
    acf = [float(np.dot(d[k:], d[:-k]) / np.dot(d, d)) for k in range(1, lag + 1)]
    z = stats.norm.ppf
    se = lr_sd / math.sqrt(n)
    return {"n": n, "sd": sd, "long_run_sd_nw": lr_sd, "lag": lag, "autocorrelation": acf,
            "detectable_effect_80pct_two_sided_5pct": (z(0.975) + z(0.80)) * se,
            "equivalence_power_at_true_zero": float(max(0.0, 2 * stats.norm.cdf(threshold / se - z(0.95)) - 1)),
            "reference_threshold": threshold}

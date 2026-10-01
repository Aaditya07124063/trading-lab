"""Synthetic verification of the bootstrap p-value described in SSRN 5198458 §3.6.

SYNTHETIC DATA ONLY - no market data is read (holdout integrity).

Paper's procedure (as described): Diff_i = ORB_i - BH_i; resample {Diff} with
replacement; p = share of bootstrap means >= observed mean D_obs.

Compared with:
  * null-centred bootstrap, one-sided  p = P*(mean* - D_obs >= D_obs)
  * null-centred bootstrap, two-sided  p = P*(|mean* - D_obs| >= |D_obs|)
  * one-sided t-test (reference)
  * null-centred STATIONARY bootstrap (Politis-Romano), one-sided, for the
    serially dependent case

Run:  python3 scripts/verify_ssrn5198458_bootstrap.py  (seed fixed; ~1-2 min)
"""

import numpy as np
from scipy import stats

SEED = 20261001
N = 270            # ~ sessions in the paper's sample (figure axes 2023-12-20..2025-01-22)
B = 2000           # bootstrap resamples per test
R = 400            # Monte Carlo replications per scenario
SD = 1.8           # % per day, plausible daily sd of an open-to-close difference
rng = np.random.default_rng(SEED)


def gen(kind, mu, n):
    if kind == "normal":
        e = rng.normal(0, SD, n)
    elif kind == "t3":                                  # heavy tails, same sd
        e = rng.standard_t(3, n) * SD / np.sqrt(3.0)
    elif kind == "ar1":                                 # serial dependence, phi = 0.3, same marginal sd
        phi, e = 0.3, np.empty(n)
        u = rng.normal(0, SD * np.sqrt(1 - phi ** 2), n)
        e[0] = rng.normal(0, SD)
        for i in range(1, n):
            e[i] = phi * e[i - 1] + u[i]
    elif kind == "paperlike":                           # Diff = ORB - BH with 10% no-trade days (ORB=0)
        bh = rng.normal(-0.18, SD, n)                   # BH drift ~ -37%/yr as in the paper
        orb = rng.normal(0, SD, n) * (rng.random(n) < 0.9)
        return orb - bh - 0.18 + mu                     # E[orb - bh] = +0.18; shift to target mu
    return mu + e


def boot_means(x, b):
    return x[rng.integers(0, len(x), (b, len(x)))].mean(1)


def stationary_boot_means(x, b, mean_block=5):
    n, p = len(x), 1.0 / mean_block
    idx = np.empty((b, n), dtype=int)
    idx[:, 0] = rng.integers(0, n, b)
    new = rng.random((b, n)) < p
    starts = rng.integers(0, n, (b, n))
    for t in range(1, n):
        idx[:, t] = np.where(new[:, t], starts[:, t], (idx[:, t - 1] + 1) % n)
    return x[idx].mean(1)


def pvals(x, kind):
    d = x.mean()
    m = boot_means(x, B)
    out = {
        "paper": np.mean(m >= d),
        "centred_1s": np.mean(m - d >= d),
        "centred_2s": np.mean(np.abs(m - d) >= abs(d)),
        "t_1s": stats.ttest_1samp(x, 0, alternative="greater").pvalue,
    }
    if kind == "ar1":
        ms = stationary_boot_means(x, B)
        out["stat_boot_1s"] = np.mean(ms - d >= d)
    return out


def main():
    scen = [("A zero", 0.0), ("B +0.20%", 0.20), ("B +0.50%", 0.50), ("B +1.00%", 1.00),
            ("C -0.20%", -0.20), ("C -1.00%", -1.00)]
    print(f"seed={SEED} n={N} B={B} R={R} sd={SD}%/day\n")
    print("Each cell: mean p [5th-95th pct] | rejection rate at 0.05")
    for kind in ["normal", "t3", "ar1", "paperlike"]:
        print(f"\n=== DGP: {kind} ===")
        for name, mu in scen:
            ps = [pvals(gen(kind, mu, N), kind) for _ in range(R)]
            cells = []
            for k in ps[0]:
                v = np.array([p[k] for p in ps])
                cells.append(f"{k}: {v.mean():.3f} [{np.quantile(v, .05):.3f}-{np.quantile(v, .95):.3f}] | "
                             f"{(v < 0.05).mean():.2f}")
            print(f"{name:9s} " + "\n          ".join(cells))

    # Consistency check against the paper's reported numbers.
    print("\n=== What a VALID one-sided test would give for the paper's reported mean Diff ===")
    for dbar in (0.19, 0.24):
        for sd in (1.0, 1.5, 2.0, 2.5, 3.0):
            t = dbar / (sd / np.sqrt(N))
            print(f"mean {dbar:.2f}%/day, sd {sd:.1f}%: t = {t:.2f}, one-sided p = {stats.norm.sf(t):.3f}")
        sd_needed = dbar * np.sqrt(N) / stats.norm.isf(0.45)
        print(f"  sd needed for a valid p = 0.45: {sd_needed:.1f}%/day")


if __name__ == "__main__":
    main()

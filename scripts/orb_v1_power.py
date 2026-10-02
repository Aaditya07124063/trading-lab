"""ORB v1 power / minimum-detectable-effect (MDE) analysis - DEVELOPMENT DATA ONLY.

Input: results/orb_v1_dev/portfolio_daily_primary.csv (2026-08-03..09-30, 42
sessions, Z-5 net portfolio returns). Uses only the SPREAD and dependence of
that series, never its mean (the mean is removed before simulation).

Analytical MDE: (z_{1-alpha} + z_{power}) * sigma_LR / sqrt(n), alpha=0.05 one-sided.
Simulation check: the ACTUAL primary test (mean_inference, automatic block
length, B=999) on synthetic series with true mean = MDE, drawn (a) i.i.d.
normal with sd sigma, (b) i.i.d. resampled from the demeaned development
returns (keeps their skew/kurtosis).
    PYTHONPATH=. python3 scripts/orb_v1_power.py
"""

import numpy as np
import pandas as pd
from scipy import stats

from src.config import BASE_DIR
from src.intraday.inference import mean_inference, minimum_detectable_effect, politis_white_block_length

x = pd.read_csv(BASE_DIR / "results" / "orb_v1_dev" / "portfolio_daily_primary.csv")["net_ret"].to_numpy()
n0, sd = len(x), x.std(ddof=1)
b0 = politis_white_block_length(x)
lr = mean_inference(x, mean_block=b0, b=10_000, seed=20261001)["long_run_sd"]
lo, hi = sd * np.sqrt((n0 - 1) / stats.chi2.ppf([0.95, 0.05], n0 - 1))      # 90% CI for sd
print(f"dev: n={n0} sd={sd*1e4:.2f} bps, PW block={b0:.2f}, long-run sd={lr*1e4:.2f} bps, "
      f"sd 90% CI [{lo*1e4:.2f}, {hi*1e4:.2f}] bps, skew={stats.skew(x):.2f}, "
      f"kurtosis={stats.kurtosis(x, fisher=False):.2f}")
resid = x - x.mean()
rng = np.random.default_rng(7)
for n in (250, 500):
    mde = minimum_detectable_effect(lr, n)
    span = [minimum_detectable_effect(s, n) * 1e4 for s in (lo, hi)]
    for label, draw in (("normal", lambda m: rng.normal(m, sd, n)),
                        ("dev-resampled", lambda m: m + rng.choice(resid, n))):
        pw = np.mean([mean_inference(draw(mde), b=999, seed=i)["p_one_sided"] < 0.05 for i in range(300)])
        sz = np.mean([mean_inference(draw(0.0), b=999, seed=1000 + i)["p_one_sided"] < 0.05 for i in range(300)])
        print(f"n={n}: analytical MDE={mde*1e4:.2f} bps/day (sd-CI range {span[0]:.2f}-{span[1]:.2f}); "
              f"{label}: simulated power at MDE={pw:.2f}, size at 0={sz:.3f}")

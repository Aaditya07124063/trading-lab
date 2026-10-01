"""ORB v1 PRE-HOLDOUT implementation validation (NOT evidence, NOT tuning).

Runs the complete ORB v1 pipeline - engine (X2 exit), portfolio aggregation,
primary inference, baselines D/E, Holm, per-stock exploratory tests, cost grid,
break-even slippage, power/MDE, data completeness, regime counts - on
DEVELOPMENT data only, to verify that the implementation works end to end.

Hard guarantees:
  * load_intraday() drops every bar on/after HOLDOUT_START (protocol not FROZEN);
  * this script additionally asserts max(date) < HOLDOUT_START for every input;
  * nothing here feeds back into the protocol: outputs are descriptive.

    python3 run_orb_v1_dev_validation.py            # writes results/orb_v1_dev/
"""

import json
import time
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import optimize

from src.config import BASE_DIR, HOLDOUT_START
from src.intraday.costs import CostModel
from src.intraday.data import load_intraday
from src.intraday.engine import EngineConfig, run_intraday, run_open_to_close_benchmark
from src.intraday.inference import (holm, mean_inference, minimum_detectable_effect,
                                    politis_white_block_length, randomisation_p, verdict)
from src.intraday.orb import ORB
from src.intraday.portfolio import (entry_candidates, frozen_universe, portfolio_daily,
                                    random_entry_baseline, sign_flip_baseline, trade_net_pnl)
from src.intraday.regimes import regime_labels
from src.registry.experiments import log_trial

OUT = BASE_DIR / "results" / "orb_v1_dev"
K = 100_000
K_SENS = 1_000_000
B = 10_000
SEED_PRIMARY = 20261001
SEED_BASELINES = 20260930


def scenarios():
    cfg = json.load(open(BASE_DIR / "config" / "cost_scenarios.json"))
    out = {}
    for name, s in cfg["scenarios"].items():
        if s["schedule"] is None:
            out[name] = CostModel.zero()
        else:
            sched = json.load(open(BASE_DIR / "config" / "cost_schedules" / s["schedule"]))
            out[name] = CostModel(**{**sched, "slippage_bps": s["slippage_bps"]})
    return cfg["primary"], out


def load_universe():
    data, ranges = {}, {}
    for sym in frozen_universe():
        df, _ = load_intraday(f"{sym}m15.csv")                       # holdout dropped here
        assert df["date"].max() < pd.Timestamp(HOLDOUT_START), f"{sym}: holdout bar leaked"
        data[sym] = df
        ranges[sym] = (str(df["session"].min()), str(df["session"].max()))
    start = max(r[0] for r in ranges.values())                        # all 50 have data from here
    window = {s: d[d["session"].astype(str) >= start].reset_index(drop=True) for s, d in data.items()}
    sessions = sorted({str(x) for d in window.values() for x in d["session"].unique()})
    return window, sessions, start


def run_all(data, costs, cfg, short=True):
    return {s: run_intraday(d, ORB(30, 15, allow_short=short), costs, cfg) for s, d in data.items()}


def main():
    t0 = time.time()
    primary, scen = scenarios()
    data, sessions, start = load_universe()
    n_univ, n_sess = len(data), len(sessions)
    assert n_univ == 50
    cfg = EngineConfig(capital=K)
    print(f"dev window {sessions[0]} .. {sessions[-1]}: {n_sess} sessions x {n_univ} stocks "
          f"(all 50 have data from {start}); holdout {HOLDOUT_START} untouched")

    # ---- strategy C (primary) under every cost scenario
    port, res_by = {}, {}
    for name, c in scen.items():
        res = run_all(data, c, cfg)
        res_by[name] = res
        port[name] = portfolio_daily(res, sessions, n_univ, K)
    prim = port[primary]
    res_p = res_by[primary]
    trades = pd.concat([r["trades"].assign(symbol=s) for s, r in res_p.items() if len(r["trades"])],
                       ignore_index=True)

    # ---- data completeness (depends only on bar existence)
    missing = {s: r["missing_bars"] for s, r in res_p.items()}
    n_missing = sum(len(v) for v in missing.values())

    # ---- primary inference (sanity run on dev data)
    x = prim["net_ret"].to_numpy()
    b_dev = politis_white_block_length(x)
    inf = mean_inference(x, mean_block=b_dev, b=B, seed=SEED_PRIMARY)
    inf_half = mean_inference(x, mean_block=max(1.0, b_dev / 2), b=B, seed=SEED_PRIMARY)
    inf_double = mean_inference(x, mean_block=b_dev * 2, b=B, seed=SEED_PRIMARY)

    # ---- baselines (primary costs)
    obs = float(x.mean())
    e_draws = sign_flip_baseline(trades, n_sess, n_univ, K, B, SEED_BASELINES)
    cands, exits = [], []
    for s, r in res_p.items():
        if len(r["trades"]):
            c_, x_ = entry_candidates(data[s], r["trades"])
            cands.append(c_); exits.append(x_)
    d_draws = random_entry_baseline(np.vstack(cands), np.concatenate(exits), scen[primary],
                                    n_sess, n_univ, K, B, SEED_BASELINES)
    p_e, p_d = randomisation_p(obs, e_draws), randomisation_p(obs, d_draws)
    holm2 = holm({"E_sign_flip": p_e, "D_random_entry": p_d})

    # ---- engine-vs-vectorised consistency on every actual trade (implementation check)
    d_sign = np.where(trades["side"] == "LONG", 1.0, -1.0)
    vec = trade_net_pnl(trades["entry_price"], trades["exit_price"], d_sign, scen[primary], K)
    max_abs_diff = float(np.max(np.abs(vec - trades["net_pnl"].to_numpy()))) if len(trades) else 0.0

    # ---- break-even slippage (bps/side) for the dev sample, from actual trades
    def mean_at(bps):
        c = CostModel(**{**scen[primary].describe(), "slippage_bps": bps})
        return trade_net_pnl(trades["entry_price"], trades["exit_price"], d_sign, c, K).sum() / (n_univ * K * n_sess)
    try:
        be = optimize.brentq(mean_at, 0.0, 200.0) if mean_at(0.0) > 0 > mean_at(200.0) else None
    except ValueError:
        be = None

    # ---- descriptive comparators
    long_only = portfolio_daily(run_all(data, scen[primary], cfg, short=False), sessions, n_univ, K)
    bench = portfolio_daily({s: run_open_to_close_benchmark(d, scen[primary], cfg) for s, d in data.items()},
                            sessions, n_univ, K)
    sens10l = portfolio_daily(run_all(data, scen[primary], EngineConfig(capital=K_SENS)), sessions, n_univ, K_SENS)

    # ---- per-stock exploratory (Holm across 50)
    per = {}
    for s, r in res_p.items():
        t = r["trades"]
        daily = pd.Series(0.0, index=sessions)
        if len(t):
            g = t.groupby("session")["net_pnl"].sum() / K
            daily.loc[g.index] = g
        per[s] = mean_inference(daily.to_numpy(), mean_block=b_dev, b=2000, seed=SEED_PRIMARY)["p_one_sided"]
    per_holm = holm(per)

    # ---- power / MDE from development dependence-adjusted sd (no holdout)
    lr_sd = inf["long_run_sd"]
    mde = {n: minimum_detectable_effect(lr_sd, n) for n in (125, 250, 500)}

    # ---- regimes (provisional proxy: daily close = last 15-min NIFTY50 bar; see final review)
    idx, _ = load_intraday("NIFTY50m15.csv")
    close = idx.groupby("session")["close"].last()
    close.index = pd.to_datetime(close.index)
    reg = regime_labels(close)
    reg.index = reg.index.strftime("%Y-%m-%d")
    reg = reg.loc[reg.index.isin(sessions)]
    regime_counts = {"vol": reg["vol_regime"].value_counts(dropna=False).to_dict(),
                     "trend": reg["trend_regime"].value_counts(dropna=False).to_dict()}

    bps = lambda v: round(v * 1e4, 3)
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "purpose": "PRE-HOLDOUT IMPLEMENTATION VALIDATION - descriptive, not evidence, not used for tuning",
        "holdout_start": HOLDOUT_START, "window": [sessions[0], sessions[-1]],
        "sessions": n_sess, "universe_n": n_univ, "capital_per_stock": K,
        "primary_scenario": primary, "costs_primary": scen[primary].describe(),
        "data_completeness": {"non_tradable_stock_sessions": n_missing,
                              "stock_sessions": n_univ * n_sess,
                              "examples": {s: v[:3] for s, v in missing.items() if v}},
        "trades": {"n": int(len(trades)), "long": int((trades.side == "LONG").sum()),
                   "short": int((trades.side == "SHORT").sum()),
                   "stock_sessions_with_trade_pct": round(len(trades) / (n_univ * n_sess) * 100, 1),
                   "entry_time_counts": trades["entry_time"].str[11:16].value_counts().sort_index().to_dict()},
        "engine_vs_vectorised_max_abs_diff_rs": max_abs_diff,
        "primary_inference_bps": {k: (bps(v) if k in ("mean", "sd", "se_bootstrap", "lower_1s_95",
                                                       "upper_1s_95", "long_run_sd") else v)
                                  for k, v in inf.items() if k != "ci95_two_sided"}
                                 | {"ci95_two_sided": [bps(v) for v in inf["ci95_two_sided"]]},
        "reporting_label_on_dev_sample": verdict(inf),
        "block_length_dev_politis_white": b_dev,
        "block_sensitivity_p": {"half": inf_half["p_one_sided"], "double": inf_double["p_one_sided"]},
        "baselines": {"E_sign_flip": {"p": p_e, "draws_mean_bps": bps(e_draws.mean())},
                      "D_random_entry": {"p": p_d, "draws_mean_bps": bps(d_draws.mean())},
                      "holm": holm2},
        "cost_grid_mean_net_bps": {k: bps(v["net_ret"].mean()) for k, v in port.items()},
        "gross_mean_bps": bps(prim["gross_ret"].mean()),
        "cost_components_rs": {k: round(float(prim[k].sum()), 2) for k in
                               ["brokerage", "stt", "exchange", "sebi", "stamp", "gst", "slippage"]},
        "break_even_slippage_bps_per_side": be,
        "long_only_B_mean_net_bps": bps(long_only["net_ret"].mean()),
        "benchmark_A_mean_net_bps": bps(bench["net_ret"].mean()),
        "capital_10_lakh_mean_net_bps": bps(sens10l["net_ret"].mean()),
        "per_stock_exploratory": {"n_raw_p_lt_0.05": sum(p < 0.05 for p in per.values()),
                                  "n_holm_p_lt_0.05": sum(p < 0.05 for p in per_holm.values())},
        "power": {"long_run_sd_bps": bps(lr_sd), "mde_bps_per_day_80pct_power": {n: bps(v) for n, v in mde.items()}},
        "regimes_provisional_proxy": regime_counts,
        "runtime_s": round(time.time() - t0, 1),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(summary, open(OUT / "summary.json", "w"), indent=2, default=str)
    prim.to_csv(OUT / "portfolio_daily_primary.csv")
    trades.to_csv(OUT / "trades_primary.csv", index=False)
    log_trial("orb_v1_dev_validation",
              {"exit": "X2 15:00 open", "range_minutes": 30, "cutoff": "14:30", "short": True,
               "scenarios": list(scen), "capital": K, "B": B},
              f"frozen NIFTY50 m15 {sessions[0]}..{sessions[-1]} (pre-holdout)",
              {"mean_net_bps": summary["primary_inference_bps"]["mean"],
               "p_one_sided": inf["p_one_sided"], "label": summary["reporting_label_on_dev_sample"]},
              "run_orb_v1_dev_validation.py")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()

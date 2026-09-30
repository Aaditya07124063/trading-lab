"""ONE-TIME seed (2026-09-30): registers the pre-registry experiments with
their true status, reproduces what can be reproduced on the committed data,
and records the OOS exposure. Refuses to run twice."""

import json
import os

os.environ["TRADING_LAB_NO_TRIAL_LOG"] = "1"

from src.registry import experiments as reg          # noqa: E402
from src.research import run_daily                    # noqa: E402

if reg.EXPERIMENTS.exists() and "LEGACY-" in reg.EXPERIMENTS.read_text():
    raise SystemExit("legacy experiments already seeded")

DS = {d["file"].split("/")[-1]: d for d in json.load(open("registry/datasets.json"))}
ENV_NOW = reg.environment()
LEGACY_ENV = {"git_commit": "unknown - original run predates version control (before 6ce8592)",
              "python": "unknown", "packages": "unknown"}
NA = "not pre-specified (legacy exploratory run)"


def base(file, strategy, **kw):
    d = DS[file]
    e = {"research_question": f"Does {strategy} beat buy & hold on {d['instrument']}?",
         "hypothesis": NA, "null_hypothesis": NA, "strategy": strategy, "instrument": d["instrument"],
         "universe": "single instrument", "timeframe": "daily", "start": d["start"][:10], "end": d["end"][:10],
         "dataset_id": d["dataset_id"] + " (as committed; original run's dataset version NOT recorded)",
         "dataset_sha256": d["sha256"], "dataset_stage": "raw", "feature_set": "price only",
         "parameters": {}, "training_period": "none (no fitting)", "validation_period": "none",
         "test_period": "full sample", "oos_status": "none - full-sample backtest",
         "cost_model": "0.1% per side (flat)", "slippage": "none", "benchmark": "buy & hold from first open",
         "cash_treatment": "idle cash earns 0% (undocumented at the time)",
         "dividends": "excluded for strategy and benchmark (price series)", "random_seed": "n/a",
         "statistical_tests": "none", "viewed_before_finalization": "yes",
         "limitations": "no statistical inference; verdict label from raw return margin (rule withdrawn 2026-09-30)",
         "environment": LEGACY_ENV}
    e.update(kw)
    return e


def repro(file, kind, fast, slow, **kw):
    r = run_daily(file, kind, fast, slow, **kw)[2]
    keys = ("return_pct", "bh_pct", "max_dd", "bh_dd", "cagr", "sharpe", "exposure_pct", "trades")
    return {k: r[k] for k in keys} | {"reproduced_at_commit": ENV_NOW["git_commit"][:10]}


seed = []
for i, (file, kind, f, s, rep) in enumerate([
        ("NIFTY_10Y.csv", "ema", 20, 50, "+184.8% vs B&H +181.6%; DD -15.1% vs -38.4%; label WEAK EDGE"),
        ("NIFTY_10Y.csv", "ema", 9, 21, "+116.9% vs +181.6%; LOSES"),
        ("NIFTY_10Y.csv", "sma", 50, 200, "+34.4% vs +181.6%; LOSES"),
        ("XAUUSDd1.csv", "sma", 50, 200, "+24.6% vs +14.2%; label BEATS (regime-dependent)")], start=1):
    rr = repro(file, kind, f, s)
    ok = abs(rr["return_pct"] - float(rep.split("%")[0])) < 0.05
    lim = ("no statistical inference; one of ~8 ideas tried (selection); label withdrawn"
           + ("; gold source/timezone UNKNOWN (MetaTrader export)" if "XAU" in file else ""))
    seed.append(base(file, f"{kind.upper()} {f}/{s} crossover", experiment_id=f"LEGACY-{i:03d}",
                     parameters={"kind": kind, "fast": f, "slow": s},
                     results={"headline": rep, "reported_in": "README Key findings", "reproduced": rr},
                     status="REPRODUCED" if ok else "REQUIRES REVALIDATION", limitations=lim))

rr = repro("RELIANCEd1.csv", "ema", 20, 50)
seed.append(base("RELIANCEd1.csv", "EMA 20/50 crossover", experiment_id="LEGACY-005",
                 parameters={"kind": "ema", "fast": 20, "slow": 50},
                 results={"headline": "README: +667% vs B&H +17,703% (LOSES)", "reproduced": rr,
                          "discrepancy": "README B&H 17,703% is NOT reproducible from the committed data "
                                         "(gives 18,031.1%; no close in the file yields 17,703%). Strategy "
                                         "+667.0% reproduces (last trade exits 2026-05-14). The README figure "
                                         "came from an earlier, uncommitted data version."},
                 status="REQUIRES REVALIDATION",
                 limitations="raw data contains a vendor placeholder spike (2005-07-28) and a misplaced "
                             "bonus adjustment (1997-10-27..11-04); see data/metadata/exclusions.csv"))
tr = run_daily("NIFTY_10Y.csv", trailing_stop=0.05)[2]
seed.append(base("NIFTY_10Y.csv", "EMA 20/50 + 5% trailing stop", experiment_id="LEGACY-006",
                 parameters={"kind": "ema", "fast": 20, "slow": 50, "trailing_stop": 0.05},
                 results={"headline": "README: return halved, drawdown worse",
                          "reproduced": {k: tr[k] for k in ("return_pct", "max_dd", "trades")}},
                 status="REPRODUCED"))
seed.append(base("NIFTY_10Y.csv", "RandomForest next-day direction (run_ml.py)", experiment_id="LEGACY-007",
                 feature_set="ret_1, ret_5, ret_20, dist_ema20, dist_ema50, vol_20",
                 parameters={"n_estimators": 200, "min_samples_leaf": 20}, random_seed=42,
                 training_period="first 70% of rows", validation_period="none", test_period="last 30%",
                 oos_status="single chronological split",
                 results={"headline": "README: 53.6% acc vs 53.2% always-up; -3.0% vs +22.3% after costs"},
                 status="REQUIRES REBUILD — TARGET/EXECUTION ALIGNMENT ISSUE",
                 limitations="target = close[t+1] > close[t] but the position is filled at open[t+1] and held "
                             "to open[t+2]; single split; no significance test"))
seed.append(base("RELIANCEd1.csv", "Momentum top-2 of 4 mega-caps, monthly (run_momentum.py)",
                 experiment_id="LEGACY-008", instrument="RELIANCE, TCS, HDFCBANK, INFY",
                 universe="4 of today's surviving large-caps", start="2002-08-12 (first common date)", dataset_id="RELIANCEd1, TCSd1, HDFCBANKd1, INFYd1 (raw)",
                 dataset_sha256=", ".join(DS[f]["sha256"][:12] for f in ("RELIANCEd1.csv", "TCSd1.csv", "HDFCBANKd1.csv", "INFYd1.csv")),
                 parameters={"lookback": 126, "hold": 21, "top_n": 2}, benchmark="equal-weight buy & hold of the 4",
                 results={"headline": "README: lost by 1,450 pts to equal-weight"},
                 status="REQUIRES REBUILD — SURVIVORSHIP BIAS",
                 limitations="SURVIVORSHIP BIAS LIMITATION; common dates start 2002-08-12 because TCS raw data "
                             "contains ~531 pre-listing rows (not TCS); rebalance fills at the ranking close; "
                             "cost charged as 2x0.1% of total value on any change"))
for n, (file, trail) in enumerate([("NIFTY50d1.csv", None), ("HDFCBANKd1.csv", None), ("XAUUSDd1.csv", None),
                                   ("NIFTY50d1.csv", 0.10), ("HDFCBANKd1.csv", 0.10)], start=9):
    rr = repro(file, "ema", 20, 50, trailing_stop=trail)
    seed.append(base(file, "EMA 20/50 crossover" + (f" + {trail:.0%} trailing stop" if trail else ""),
                     experiment_id=f"LEGACY-{n:03d}", parameters={"kind": "ema", "fast": 20, "slow": 50,
                                                                  "trailing_stop": trail},
                     results={"headline": f"leaderboard: {rr['return_pct']}% vs B&H {rr['bh_pct']}%",
                              "reproduced": rr,
                              "note": "trail-10% rows were saved without the stop in their name until cd3743c" if trail else ""},
                     status="REQUIRES REVALIDATION" if "HDFC" in file else "EXPLORATORY",
                     limitations=("raw data has 123 placeholder bars on non-trading days (excluded in clean version)"
                                  if "HDFC" in file else "exploratory web-UI run; no inference")))
for n, (file, strat, rng) in enumerate([("RELIANCEm15.csv", "ORB 30m on 15m bars", 30),
                                        ("RELIANCEh1.csv", "ORB 60m on 60m bars", 60)], start=14):
    d = DS[file]
    seed.append(base(file, strat, experiment_id=f"LEGACY-{n:03d}", timeframe=file[-7:-4],
                     dataset_id=d["dataset_id"] + " (exact file used; commit ccf061e)",
                     research_question="engine plumbing check (not a research test)",
                     parameters={"range_minutes": rng, "cutoff": "14:30", "shorts": True, "max_entries_per_day": 1},
                     training_period="development = first 50% of sessions",
                     validation_period="next 25%", test_period="final 25%",
                     oos_status="EXPOSED — VIEWED FOR RESEARCH/DIAGNOSTIC PURPOSES; NO PARAMETER TUNING PERFORMED.",
                     cost_model="ZERO costs (GROSS)", slippage="none", benchmark="open-to-close long-only",
                     cash_treatment="flat between trades, earns 0%", dividends="n/a intraday",
                     results={"headline": "gross diagnostic run; numbers deliberately not used as findings"},
                     status="DIAGNOSTIC", viewed_before_finalization="yes - all three periods displayed 2026-09-30",
                     limitations="zero costs; small sample; long/short vs long-only benchmark mismatch",
                     environment=ENV_NOW | {"git_commit": "46624f7/f8aff70 (runner/dashboard at the time)"}))

for e in seed:
    reg.record(e, prefix="LEGACY", env=e.pop("environment"))

# clean-data re-runs of the affected daily experiments
for file, legacy in (("RELIANCEd1.csv", "LEGACY-005"), ("HDFCBANKd1.csv", "LEGACY-010")):
    d = DS[file]
    rr = repro(file, "ema", 20, 50, clean=True)
    reg.record(base(file, "EMA 20/50 crossover", dataset_id=d["clean"]["dataset_id"],
                    dataset_sha256=d["clean"]["sha256"], dataset_stage="clean (raw minus reviewed exclusions)",
                    parameters={"kind": "ema", "fast": 20, "slow": 50},
                    results={"headline": f"{rr['return_pct']}% vs B&H {rr['bh_pct']}% (clean)", "reproduced": rr,
                             "revalidates": legacy},
                    status="EXPLORATORY",
                    limitations="exclusions reviewed by agent, pending user review; still no inference; "
                                "cash earns 0%; dividends excluded",
                    research_question=f"Revalidation of {legacy} on clean data"), env=ENV_NOW)
reg.write_md()
print(len(reg.current()), "experiments registered")

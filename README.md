# Trading Lab

An honest backtesting, research and paper-trading platform for Indian markets,
built from scratch in Python. One question drives it: **does a trading idea
actually make money, after costs, against simply buying and holding?**

## Architecture

    data/ (36 CSVs: NIFTY, SENSEX, stocks, gold; 5 timeframes)
      -> data_loader.py   one clean format from 3 different CSV dialects
      -> indicators.py    SMA / EMA columns
      -> signals.py       rules -> position column (1 in / 0 out)
      -> backtest.py      day-by-day replay, next-open fills, costs, stops
      -> metrics.py       drawdown, win rate, benchmark, 3-level verdict
      -> results/         leaderboard.csv - every experiment ever run
    server.py + web/      FastAPI backend + hand-written Kite-style web UI
    paper_bot.py          daily paper-trading bot (state + diary)
    run_ml.py             RandomForest walk-forward experiment
    run_momentum.py       cross-sectional momentum portfolio experiment

## Methodology (industry practice, enforced in code)

- **No look-ahead:** signals form at close, execute at the NEXT day's open.
- **Transaction-cost model:** 0.1% per side on every fill; nothing trades free.
- **Explicit saves only:** running a backtest (CLI or web) never writes the
  leaderboard; the web UI's Save button / `POST /api/leaderboard/save` does.
  Experiment names encode every parameter (e.g. `· trail 10%`), one row each.
- **Benchmark-relative verdicts:** BEATS / WEAK EDGE / LOSES vs buy & hold -
  raw return is never reported alone.
- **Walk-forward ML validation:** chronological 70/30 split, no shuffling.
- **Research -> paper -> live pipeline:** real capital only after months of
  live paper-trading evidence (paper stage: in progress).

References: M. Lopez de Prado, *Advances in Financial Machine Learning* (2018);
Bailey et al., *The Probability of Backtest Overfitting* (2014).

## Key findings (all reproducible from this repo's data)

| Experiment | Result | Verdict |
|---|---|---|
| EMA 20/50, NIFTY 50, 2016-2026 | +184.8% vs B&H +181.6%; drawdown -15.1% vs -38.4% | WEAK EDGE (edge = safety, not return) |
| EMA 9/21, NIFTY 50 | +116.9% vs +181.6% | LOSES |
| SMA 50/200, NIFTY 50 | +34.4% vs +181.6% | LOSES |
| SMA 50/200, Gold 2012-22 | +24.6% vs +14.2% | BEATS (regime-dependent!) |
| EMA 20/50, RELIANCE 1996-2026 | +667% vs B&H +17,703% | LOSES (compounding beats timing) |
| 5% trailing stop on EMA 20/50 | return halved, drawdown WORSE | risk overlays must fit the strategy |
| RandomForest daily direction | 53.6% acc (baseline 53.2%); -3.0% vs +22.3% after costs | costs destroy small edges |
| Momentum top-2 of 4 mega-caps | lost by 1,450 pts to equal-weight | momentum needs a wide universe |

The most important output of this lab is the honest NO. Six of eight ideas
failed against buy & hold - and the lab proves it in seconds, before any
real money is at risk.

## Quick start

    pip3 install -r requirements.txt
    python3 -m pytest               # full test suite (must be green)
    python3 run_experiments.py      # re-run core experiments, upsert leaderboard
    python3 -m uvicorn server:app --reload   # web UI at http://localhost:8000
    python3 paper_bot.py            # daily paper-trading run

## Roadmap

- Search-any-stock with auto-download (Yahoo symbol search)
- Momentum re-test on a 50-stock NIFTY universe
- Broker API integration (Zerodha) - ONLY after paper-trading success

## Disclaimer

Educational research tool. Nothing here is investment advice; past
performance does not predict future results.
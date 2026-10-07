# Trading Lab

An honest backtesting, research and paper-trading platform for Indian markets,
built from scratch in Python. One question drives it: **does a trading idea
actually make money, after costs, against simply buying and holding?**

Research documentation: [METHODOLOGY](METHODOLOGY.md) · [DATA_REGISTRY](DATA_REGISTRY.md) ·
[EXPERIMENT_REGISTRY](EXPERIMENT_REGISTRY.md) · [RESEARCH_LOG](RESEARCH_LOG.md) ·
[REPRODUCIBILITY](REPRODUCIBILITY.md) · [CHANGELOG](CHANGELOG.md) ·
[master specification](Trading_Lab_Research_Master_Specification.md)

Registered study **S2-MOM-v1** (momentum bias ladder, NSE): how to verify and reproduce it is in
[REPRODUCIBILITY](REPRODUCIBILITY.md#s2-mom-v1-the-registered-momentum-bias-ladder-study); the release state is in
[docs/audit/FINAL_RELEASE_GATE.md](docs/audit/FINAL_RELEASE_GATE.md). One command: `python3 scripts/reproduce_s2_mom_v1.py`.

## Architecture

    data/ (36 CSVs: NIFTY, SENSEX, stocks, gold; 5 timeframes)
      -> data_loader.py   one clean format from 3 different CSV dialects
      -> indicators.py    SMA / EMA columns
      -> signals.py       rules -> position column (1 in / 0 out)
      -> backtest.py      day-by-day replay, next-open fills, costs, stops
      -> metrics.py       drawdown, win rate, benchmark, 3-level verdict
      -> results/         leaderboard.csv - every experiment ever run
    server.py + web/      FastAPI backend + research-terminal web UI (web/index.html, no build step;
                          demo data is labelled; the earlier Kite-style UI is kept at web/classic.html)
    paper_bot.py          daily paper-trading bot (state + diary)
    run_ml.py             RandomForest walk-forward experiment
    run_momentum.py       cross-sectional momentum portfolio experiment

## Methodology (industry practice, enforced in code)

- **No look-ahead:** signals form at close, execute at the NEXT day's open.
- **Transaction-cost model:** 0.1% per side on every fill; nothing trades free.
- **Explicit saves only:** running a backtest (CLI or web) never writes the
  leaderboard; the web UI's Save button / `POST /api/leaderboard/save` does.
  Experiment names encode every parameter (e.g. `· trail 10%`), one row each.
- **Benchmark-relative reporting:** raw return is never reported alone. (The
  BEATS / WEAK EDGE / LOSES labels are withdrawn - see Historical findings.)
- **Walk-forward ML validation:** chronological 70/30 split, no shuffling.
- **Research -> paper -> live pipeline:** real capital only after months of
  live paper-trading evidence (paper stage: in progress).

References: M. Lopez de Prado, *Advances in Financial Machine Learning* (2018);
Bailey et al., *The Probability of Backtest Overfitting* (2014).

## Historical findings (July 2026, pre-registry) - status as of 2026-09-30

These numbers are preserved as originally reported. Each is now tracked in
[EXPERIMENT_REGISTRY.md](EXPERIMENT_REGISTRY.md); the "status" column is
authoritative. Verdict labels (BEATS / WEAK EDGE / LOSES) came from a raw
return-margin rule with no statistical inference and are **withdrawn**.

| Experiment (as reported) | Reported result | Registry | Status |
|---|---|---|---|
| EMA 20/50, NIFTY 50, 2016-2026 | +184.8% vs B&H +181.6%; DD -15.1% vs -38.4% | LEGACY-001 | REPRODUCED on `NIFTY_10Y@5d2eccdd6733`; no inference - "edge" not established |
| EMA 9/21, NIFTY 50 | +116.9% vs +181.6% | LEGACY-002 | REPRODUCED |
| SMA 50/200, NIFTY 50 | +34.4% vs +181.6% | LEGACY-003 | REPRODUCED |
| SMA 50/200, Gold 2012-22 | +24.6% vs +14.2% | LEGACY-004 | REPRODUCED; gold source/timezone unknown |
| EMA 20/50, RELIANCE 1996-2026 | +667% vs B&H +17,703% | LEGACY-005 | **REQUIRES REVALIDATION** - see note 1 |
| 5% trailing stop on EMA 20/50 | return halved, drawdown worse | LEGACY-006 | REPRODUCED |
| RandomForest daily direction | 53.6% acc (baseline 53.2%) | LEGACY-007 | **REQUIRES REBUILD — TARGET/EXECUTION ALIGNMENT ISSUE** |
| Momentum top-2 of 4 mega-caps | lost by 1,450 pts | LEGACY-008 | **REQUIRES REBUILD — SURVIVORSHIP BIAS** (also used TCS pre-listing rows) |

**Note 1 (README vs leaderboard, traced 2026-09-30).** README said B&H
+17,703%; the leaderboard says +18,031.1%. The committed file
`RELIANCEd1@ded4fcf26b7d` (unchanged since the initial commit 6ce8592)
reproduces +18,031.1% and the strategy's +667.0%. No close in that file yields
+17,703% (it would need 1,303.18); the strategy figure is identical in both
because its last trade closed on 2026-05-14. Conclusion: the README B&H figure
was computed on an earlier, uncommitted data version (fetch_data.py refreshed
the file on 2026-07-18) and is **not reproducible**. In addition, the raw file
contains a vendor placeholder spike (2005-07-28) and a misplaced 1997 bonus
adjustment; on the clean dataset the strategy returns +822.2% (EXP-20260930-001).
The conclusion "loses to buy & hold" is unchanged, but neither figure is paper
evidence until the exclusions are reviewed.

The most important output of this lab remains the honest NO - now with the
provenance to back it.

## Quick start

    pip3 install -r requirements.txt
    python3 -m pytest               # full test suite (must be green)
    python3 run_experiments.py      # re-run core experiments, upsert leaderboard
    python3 -m uvicorn server:app --reload   # web UI at http://localhost:8000
    python3 paper_bot.py            # daily paper-trading run (replays missed days)
    python3 update_intraday.py      # grow m15/h1 history (run every few weeks!)
    python3 run_intraday.py RELIANCEm15.csv   # ORB vs open-to-close, dev/val/OOS

## Intraday research (src/intraday/)

- Strategy sees only bars up to the one that just closed; fills at the NEXT
  bar's open; square-off at the 15:15 close; nothing is held overnight.
- Costs: copy `config/intraday_costs.example.json` to
  `config/intraday_costs.json` and fill in your broker's charge sheet. No
  rates are hard-coded. Use `--gross` only as a labelled zero-cost reference.
- Benchmark: buy at each session's open, sell at the 15:15 close.
- Yahoo keeps only ~60 days of 15-min bars: anything not captured in time is
  lost, so run `update_intraday.py` regularly.
- The 1-hour data supports ORB-60 only. It is NOT the 15-min ORB-30 strategy.
- The m30/h4 files sit on a 09:00 grid, not the 09:15 NSE session grid. They
  are reported as misaligned and are not used for intraday research.

## Roadmap

- Search-any-stock with auto-download (Yahoo symbol search)
- Momentum re-test on a 50-stock NIFTY universe
- Broker API integration (Zerodha) - ONLY after paper-trading success

## Disclaimer

Educational research tool. Nothing here is investment advice; past
performance does not predict future results.
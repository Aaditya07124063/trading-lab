# Experiment registry

_Generated from `registry/experiments.jsonl` (append-only) by `python3 -m src.registry.experiments` - do not edit by hand._

Registered experiments: 17 · logged trials (every run, incl. casual): 0 (trials log started 2026-09-30; earlier casual runs were not logged).

| ID | status | strategy | data | period | OOS status | viewed before final | headline |
|---|---|---|---|---|---|---|---|
| LEGACY-001 | **REPRODUCED** | EMA 20/50 crossover | `NIFTY_10Y@5d2eccdd6733 (as committed; original run's dataset version NOT recorded)` | 2016-07-18 → 2026-07-16 | none - full-sample backtest | yes | +184.8% vs B&H +181.6%; DD -15.1% vs -38.4%; label WEAK EDGE |
| LEGACY-002 | **REPRODUCED** | EMA 9/21 crossover | `NIFTY_10Y@5d2eccdd6733 (as committed; original run's dataset version NOT recorded)` | 2016-07-18 → 2026-07-16 | none - full-sample backtest | yes | +116.9% vs +181.6%; LOSES |
| LEGACY-003 | **REPRODUCED** | SMA 50/200 crossover | `NIFTY_10Y@5d2eccdd6733 (as committed; original run's dataset version NOT recorded)` | 2016-07-18 → 2026-07-16 | none - full-sample backtest | yes | +34.4% vs +181.6%; LOSES |
| LEGACY-004 | **REPRODUCED** | SMA 50/200 crossover | `XAUUSDd1@d3da2122fded (as committed; original run's dataset version NOT recorded)` | 2012-11-14 → 2022-03-04 | none - full-sample backtest | yes | +24.6% vs +14.2%; label BEATS (regime-dependent) |
| LEGACY-005 | **REQUIRES REVALIDATION** | EMA 20/50 crossover | `RELIANCEd1@ded4fcf26b7d (as committed; original run's dataset version NOT recorded)` | 1996-01-01 → 2026-07-17 | none - full-sample backtest | yes | README: +667% vs B&H +17,703% (LOSES) |
| LEGACY-006 | **REPRODUCED** | EMA 20/50 + 5% trailing stop | `NIFTY_10Y@5d2eccdd6733 (as committed; original run's dataset version NOT recorded)` | 2016-07-18 → 2026-07-16 | none - full-sample backtest | yes | README: return halved, drawdown worse |
| LEGACY-007 | **REQUIRES REBUILD — TARGET/EXECUTION ALIGNMENT ISSUE** | RandomForest next-day direction (run_ml.py) | `NIFTY_10Y@5d2eccdd6733 (as committed; original run's dataset version NOT recorded)` | 2016-07-18 → 2026-07-16 | single chronological split | yes | README: 53.6% acc vs 53.2% always-up; -3.0% vs +22.3% after costs |
| LEGACY-008 | **REQUIRES REBUILD — SURVIVORSHIP BIAS** | Momentum top-2 of 4 mega-caps, monthly (run_momentum.py) | `RELIANCEd1, TCSd1, HDFCBANKd1, INFYd1 (raw)` | 2002-08-12 (first common date) → 2026-07-17 | none - full-sample backtest | yes | README: lost by 1,450 pts to equal-weight |
| LEGACY-009 | **EXPLORATORY** | EMA 20/50 crossover | `NIFTY50d1@16dbac2d1f3f (as committed; original run's dataset version NOT recorded)` | 2007-09-17 → 2026-07-17 | none - full-sample backtest | yes | leaderboard: 441.3% vs B&H 438.6% |
| LEGACY-010 | **REQUIRES REVALIDATION** | EMA 20/50 crossover | `HDFCBANKd1@abbe3f6fbf4c (as committed; original run's dataset version NOT recorded)` | 1996-01-01 → 2026-07-17 | none - full-sample backtest | yes | leaderboard: 2010.3% vs B&H 54178.1% |
| LEGACY-011 | **EXPLORATORY** | EMA 20/50 crossover | `XAUUSDd1@d3da2122fded (as committed; original run's dataset version NOT recorded)` | 2012-11-14 → 2022-03-04 | none - full-sample backtest | yes | leaderboard: 3.1% vs B&H 14.2% |
| LEGACY-012 | **EXPLORATORY** | EMA 20/50 crossover + 10% trailing stop | `NIFTY50d1@16dbac2d1f3f (as committed; original run's dataset version NOT recorded)` | 2007-09-17 → 2026-07-17 | none - full-sample backtest | yes | leaderboard: 359.1% vs B&H 438.6% |
| LEGACY-013 | **REQUIRES REVALIDATION** | EMA 20/50 crossover + 10% trailing stop | `HDFCBANKd1@abbe3f6fbf4c (as committed; original run's dataset version NOT recorded)` | 1996-01-01 → 2026-07-17 | none - full-sample backtest | yes | leaderboard: 606.6% vs B&H 54178.1% |
| LEGACY-014 | **DIAGNOSTIC** | ORB 30m on 15m bars | `RELIANCEm15@444f1c5e5adf (exact file used; commit ccf061e)` | 2026-04-23 → 2026-09-30 | EXPOSED — VIEWED FOR RESEARCH/DIAGNOSTIC PURPOSES; NO PARAMETER TUNING PERFORMED. | yes - all three periods displayed 2026-09-30 | gross diagnostic run; numbers deliberately not used as findings |
| LEGACY-015 | **DIAGNOSTIC** | ORB 60m on 60m bars | `RELIANCEh1@ed0cd3d253a3 (exact file used; commit ccf061e)` | 2023-08-02 → 2026-09-30 | EXPOSED — VIEWED FOR RESEARCH/DIAGNOSTIC PURPOSES; NO PARAMETER TUNING PERFORMED. | yes - all three periods displayed 2026-09-30 | gross diagnostic run; numbers deliberately not used as findings |
| EXP-20260930-001 | **EXPLORATORY** | EMA 20/50 crossover | `RELIANCEd1.clean@995b7a380080` | 1996-01-01 → 2026-07-17 | none - full-sample backtest | yes | 822.2% vs B&H 18031.1% (clean) |
| EXP-20260930-002 | **EXPLORATORY** | EMA 20/50 crossover | `HDFCBANKd1.clean@19cb6ee50f25` | 1996-01-01 → 2026-07-17 | none - full-sample backtest | yes | 2460.3% vs B&H 54178.1% (clean) |

## Details

### LEGACY-001 — EMA 20/50 crossover

- **research_question:** Does EMA 20/50 crossover beat buy & hold on NIFTY_10Y?
- **hypothesis:** not pre-specified (legacy exploratory run)
- **null_hypothesis:** not pre-specified (legacy exploratory run)
- **dataset_stage:** raw
- **parameters:** {'kind': 'ema', 'fast': 20, 'slow': 50}
- **cost_model:** 0.1% per side (flat)
- **slippage:** none
- **benchmark:** buy & hold from first open
- **cash_treatment:** idle cash earns 0% (undocumented at the time)
- **dividends:** excluded for strategy and benchmark (price series)
- **statistical_tests:** none
- **limitations:** no statistical inference; one of ~8 ideas tried (selection); label withdrawn
- **code:** `unknown - ` · python unknown
- **amended 2026-09-30T23:50:33:** registration/reproduction code committed in 9dcee96 (records were written from the uncommitted working tree)

### LEGACY-002 — EMA 9/21 crossover

- **research_question:** Does EMA 9/21 crossover beat buy & hold on NIFTY_10Y?
- **hypothesis:** not pre-specified (legacy exploratory run)
- **null_hypothesis:** not pre-specified (legacy exploratory run)
- **dataset_stage:** raw
- **parameters:** {'kind': 'ema', 'fast': 9, 'slow': 21}
- **cost_model:** 0.1% per side (flat)
- **slippage:** none
- **benchmark:** buy & hold from first open
- **cash_treatment:** idle cash earns 0% (undocumented at the time)
- **dividends:** excluded for strategy and benchmark (price series)
- **statistical_tests:** none
- **limitations:** no statistical inference; one of ~8 ideas tried (selection); label withdrawn
- **code:** `unknown - ` · python unknown
- **amended 2026-09-30T23:50:33:** registration/reproduction code committed in 9dcee96 (records were written from the uncommitted working tree)

### LEGACY-003 — SMA 50/200 crossover

- **research_question:** Does SMA 50/200 crossover beat buy & hold on NIFTY_10Y?
- **hypothesis:** not pre-specified (legacy exploratory run)
- **null_hypothesis:** not pre-specified (legacy exploratory run)
- **dataset_stage:** raw
- **parameters:** {'kind': 'sma', 'fast': 50, 'slow': 200}
- **cost_model:** 0.1% per side (flat)
- **slippage:** none
- **benchmark:** buy & hold from first open
- **cash_treatment:** idle cash earns 0% (undocumented at the time)
- **dividends:** excluded for strategy and benchmark (price series)
- **statistical_tests:** none
- **limitations:** no statistical inference; one of ~8 ideas tried (selection); label withdrawn
- **code:** `unknown - ` · python unknown
- **amended 2026-09-30T23:50:33:** registration/reproduction code committed in 9dcee96 (records were written from the uncommitted working tree)

### LEGACY-004 — SMA 50/200 crossover

- **research_question:** Does SMA 50/200 crossover beat buy & hold on XAUUSD?
- **hypothesis:** not pre-specified (legacy exploratory run)
- **null_hypothesis:** not pre-specified (legacy exploratory run)
- **dataset_stage:** raw
- **parameters:** {'kind': 'sma', 'fast': 50, 'slow': 200}
- **cost_model:** 0.1% per side (flat)
- **slippage:** none
- **benchmark:** buy & hold from first open
- **cash_treatment:** idle cash earns 0% (undocumented at the time)
- **dividends:** excluded for strategy and benchmark (price series)
- **statistical_tests:** none
- **limitations:** no statistical inference; one of ~8 ideas tried (selection); label withdrawn; gold source/timezone UNKNOWN (MetaTrader export)
- **code:** `unknown - ` · python unknown
- **amended 2026-09-30T23:50:33:** registration/reproduction code committed in 9dcee96 (records were written from the uncommitted working tree)

### LEGACY-005 — EMA 20/50 crossover

- **research_question:** Does EMA 20/50 crossover beat buy & hold on RELIANCE?
- **hypothesis:** not pre-specified (legacy exploratory run)
- **null_hypothesis:** not pre-specified (legacy exploratory run)
- **dataset_stage:** raw
- **parameters:** {'kind': 'ema', 'fast': 20, 'slow': 50}
- **cost_model:** 0.1% per side (flat)
- **slippage:** none
- **benchmark:** buy & hold from first open
- **cash_treatment:** idle cash earns 0% (undocumented at the time)
- **dividends:** excluded for strategy and benchmark (price series)
- **statistical_tests:** none
- **limitations:** raw data contains a vendor placeholder spike (2005-07-28) and a misplaced bonus adjustment (1997-10-27..11-04); see data/metadata/exclusions.csv
- **code:** `unknown - ` · python unknown
- **amended 2026-09-30T23:50:33:** registration/reproduction code committed in 9dcee96 (records were written from the uncommitted working tree)

### LEGACY-006 — EMA 20/50 + 5% trailing stop

- **research_question:** Does EMA 20/50 + 5% trailing stop beat buy & hold on NIFTY_10Y?
- **hypothesis:** not pre-specified (legacy exploratory run)
- **null_hypothesis:** not pre-specified (legacy exploratory run)
- **dataset_stage:** raw
- **parameters:** {'kind': 'ema', 'fast': 20, 'slow': 50, 'trailing_stop': 0.05}
- **cost_model:** 0.1% per side (flat)
- **slippage:** none
- **benchmark:** buy & hold from first open
- **cash_treatment:** idle cash earns 0% (undocumented at the time)
- **dividends:** excluded for strategy and benchmark (price series)
- **statistical_tests:** none
- **limitations:** no statistical inference; verdict label from raw return margin (rule withdrawn 2026-09-30)
- **code:** `unknown - ` · python unknown
- **amended 2026-09-30T23:50:33:** registration/reproduction code committed in 9dcee96 (records were written from the uncommitted working tree)

### LEGACY-007 — RandomForest next-day direction (run_ml.py)

- **research_question:** Does RandomForest next-day direction (run_ml.py) beat buy & hold on NIFTY_10Y?
- **hypothesis:** not pre-specified (legacy exploratory run)
- **null_hypothesis:** not pre-specified (legacy exploratory run)
- **dataset_stage:** raw
- **parameters:** {'n_estimators': 200, 'min_samples_leaf': 20}
- **cost_model:** 0.1% per side (flat)
- **slippage:** none
- **benchmark:** buy & hold from first open
- **cash_treatment:** idle cash earns 0% (undocumented at the time)
- **dividends:** excluded for strategy and benchmark (price series)
- **statistical_tests:** none
- **limitations:** target = close[t+1] > close[t] but the position is filled at open[t+1] and held to open[t+2]; single split; no significance test
- **code:** `unknown - ` · python unknown
- **amended 2026-09-30T23:50:33:** registration/reproduction code committed in 9dcee96 (records were written from the uncommitted working tree)

### LEGACY-008 — Momentum top-2 of 4 mega-caps, monthly (run_momentum.py)

- **research_question:** Does Momentum top-2 of 4 mega-caps, monthly (run_momentum.py) beat buy & hold on RELIANCE?
- **hypothesis:** not pre-specified (legacy exploratory run)
- **null_hypothesis:** not pre-specified (legacy exploratory run)
- **dataset_stage:** raw
- **parameters:** {'lookback': 126, 'hold': 21, 'top_n': 2}
- **cost_model:** 0.1% per side (flat)
- **slippage:** none
- **benchmark:** equal-weight buy & hold of the 4
- **cash_treatment:** idle cash earns 0% (undocumented at the time)
- **dividends:** excluded for strategy and benchmark (price series)
- **statistical_tests:** none
- **limitations:** SURVIVORSHIP BIAS LIMITATION; common dates start 2002-08-12 because TCS raw data contains ~531 pre-listing rows (not TCS); rebalance fills at the ranking close; cost charged as 2x0.1% of total value on any change
- **code:** `unknown - ` · python unknown
- **amended 2026-09-30T23:50:33:** registration/reproduction code committed in 9dcee96 (records were written from the uncommitted working tree)

### LEGACY-009 — EMA 20/50 crossover

- **research_question:** Does EMA 20/50 crossover beat buy & hold on NIFTY50?
- **hypothesis:** not pre-specified (legacy exploratory run)
- **null_hypothesis:** not pre-specified (legacy exploratory run)
- **dataset_stage:** raw
- **parameters:** {'kind': 'ema', 'fast': 20, 'slow': 50, 'trailing_stop': None}
- **cost_model:** 0.1% per side (flat)
- **slippage:** none
- **benchmark:** buy & hold from first open
- **cash_treatment:** idle cash earns 0% (undocumented at the time)
- **dividends:** excluded for strategy and benchmark (price series)
- **statistical_tests:** none
- **limitations:** exploratory web-UI run; no inference
- **code:** `unknown - ` · python unknown
- **amended 2026-09-30T23:50:33:** registration/reproduction code committed in 9dcee96 (records were written from the uncommitted working tree)

### LEGACY-010 — EMA 20/50 crossover

- **research_question:** Does EMA 20/50 crossover beat buy & hold on HDFCBANK?
- **hypothesis:** not pre-specified (legacy exploratory run)
- **null_hypothesis:** not pre-specified (legacy exploratory run)
- **dataset_stage:** raw
- **parameters:** {'kind': 'ema', 'fast': 20, 'slow': 50, 'trailing_stop': None}
- **cost_model:** 0.1% per side (flat)
- **slippage:** none
- **benchmark:** buy & hold from first open
- **cash_treatment:** idle cash earns 0% (undocumented at the time)
- **dividends:** excluded for strategy and benchmark (price series)
- **statistical_tests:** none
- **limitations:** raw data has 123 placeholder bars on non-trading days (excluded in clean version)
- **code:** `unknown - ` · python unknown
- **amended 2026-09-30T23:50:33:** registration/reproduction code committed in 9dcee96 (records were written from the uncommitted working tree)

### LEGACY-011 — EMA 20/50 crossover

- **research_question:** Does EMA 20/50 crossover beat buy & hold on XAUUSD?
- **hypothesis:** not pre-specified (legacy exploratory run)
- **null_hypothesis:** not pre-specified (legacy exploratory run)
- **dataset_stage:** raw
- **parameters:** {'kind': 'ema', 'fast': 20, 'slow': 50, 'trailing_stop': None}
- **cost_model:** 0.1% per side (flat)
- **slippage:** none
- **benchmark:** buy & hold from first open
- **cash_treatment:** idle cash earns 0% (undocumented at the time)
- **dividends:** excluded for strategy and benchmark (price series)
- **statistical_tests:** none
- **limitations:** exploratory web-UI run; no inference
- **code:** `unknown - ` · python unknown
- **amended 2026-09-30T23:50:33:** registration/reproduction code committed in 9dcee96 (records were written from the uncommitted working tree)

### LEGACY-012 — EMA 20/50 crossover + 10% trailing stop

- **research_question:** Does EMA 20/50 crossover + 10% trailing stop beat buy & hold on NIFTY50?
- **hypothesis:** not pre-specified (legacy exploratory run)
- **null_hypothesis:** not pre-specified (legacy exploratory run)
- **dataset_stage:** raw
- **parameters:** {'kind': 'ema', 'fast': 20, 'slow': 50, 'trailing_stop': 0.1}
- **cost_model:** 0.1% per side (flat)
- **slippage:** none
- **benchmark:** buy & hold from first open
- **cash_treatment:** idle cash earns 0% (undocumented at the time)
- **dividends:** excluded for strategy and benchmark (price series)
- **statistical_tests:** none
- **limitations:** exploratory web-UI run; no inference
- **code:** `unknown - ` · python unknown
- **amended 2026-09-30T23:50:33:** registration/reproduction code committed in 9dcee96 (records were written from the uncommitted working tree)

### LEGACY-013 — EMA 20/50 crossover + 10% trailing stop

- **research_question:** Does EMA 20/50 crossover + 10% trailing stop beat buy & hold on HDFCBANK?
- **hypothesis:** not pre-specified (legacy exploratory run)
- **null_hypothesis:** not pre-specified (legacy exploratory run)
- **dataset_stage:** raw
- **parameters:** {'kind': 'ema', 'fast': 20, 'slow': 50, 'trailing_stop': 0.1}
- **cost_model:** 0.1% per side (flat)
- **slippage:** none
- **benchmark:** buy & hold from first open
- **cash_treatment:** idle cash earns 0% (undocumented at the time)
- **dividends:** excluded for strategy and benchmark (price series)
- **statistical_tests:** none
- **limitations:** raw data has 123 placeholder bars on non-trading days (excluded in clean version)
- **code:** `unknown - ` · python unknown
- **amended 2026-09-30T23:50:33:** registration/reproduction code committed in 9dcee96 (records were written from the uncommitted working tree)

### LEGACY-014 — ORB 30m on 15m bars

- **research_question:** engine plumbing check (not a research test)
- **hypothesis:** not pre-specified (legacy exploratory run)
- **null_hypothesis:** not pre-specified (legacy exploratory run)
- **dataset_stage:** raw
- **parameters:** {'range_minutes': 30, 'cutoff': '14:30', 'shorts': True, 'max_entries_per_day': 1}
- **cost_model:** ZERO costs (GROSS)
- **slippage:** none
- **benchmark:** open-to-close long-only
- **cash_treatment:** flat between trades, earns 0%
- **dividends:** n/a intraday
- **statistical_tests:** none
- **limitations:** zero costs; small sample; long/short vs long-only benchmark mismatch
- **code:** `46624f7/f8` (dirty) · python 3.13.5
- **amended 2026-09-30T23:50:33:** registration/reproduction code committed in 9dcee96 (records were written from the uncommitted working tree)

### LEGACY-015 — ORB 60m on 60m bars

- **research_question:** engine plumbing check (not a research test)
- **hypothesis:** not pre-specified (legacy exploratory run)
- **null_hypothesis:** not pre-specified (legacy exploratory run)
- **dataset_stage:** raw
- **parameters:** {'range_minutes': 60, 'cutoff': '14:30', 'shorts': True, 'max_entries_per_day': 1}
- **cost_model:** ZERO costs (GROSS)
- **slippage:** none
- **benchmark:** open-to-close long-only
- **cash_treatment:** flat between trades, earns 0%
- **dividends:** n/a intraday
- **statistical_tests:** none
- **limitations:** zero costs; small sample; long/short vs long-only benchmark mismatch
- **code:** `46624f7/f8` (dirty) · python 3.13.5
- **amended 2026-09-30T23:50:33:** registration/reproduction code committed in 9dcee96 (records were written from the uncommitted working tree)

### EXP-20260930-001 — EMA 20/50 crossover

- **research_question:** Revalidation of LEGACY-005 on clean data
- **hypothesis:** not pre-specified (legacy exploratory run)
- **null_hypothesis:** not pre-specified (legacy exploratory run)
- **dataset_stage:** clean (raw minus reviewed exclusions)
- **parameters:** {'kind': 'ema', 'fast': 20, 'slow': 50}
- **cost_model:** 0.1% per side (flat)
- **slippage:** none
- **benchmark:** buy & hold from first open
- **cash_treatment:** idle cash earns 0% (undocumented at the time)
- **dividends:** excluded for strategy and benchmark (price series)
- **statistical_tests:** none
- **limitations:** exclusions reviewed by agent, pending user review; still no inference; cash earns 0%; dividends excluded
- **code:** `e1b82fee14` (dirty) · python 3.13.5
- **amended 2026-09-30T23:50:33:** registration/reproduction code committed in 9dcee96 (records were written from the uncommitted working tree)

### EXP-20260930-002 — EMA 20/50 crossover

- **research_question:** Revalidation of LEGACY-010 on clean data
- **hypothesis:** not pre-specified (legacy exploratory run)
- **null_hypothesis:** not pre-specified (legacy exploratory run)
- **dataset_stage:** clean (raw minus reviewed exclusions)
- **parameters:** {'kind': 'ema', 'fast': 20, 'slow': 50}
- **cost_model:** 0.1% per side (flat)
- **slippage:** none
- **benchmark:** buy & hold from first open
- **cash_treatment:** idle cash earns 0% (undocumented at the time)
- **dividends:** excluded for strategy and benchmark (price series)
- **statistical_tests:** none
- **limitations:** exclusions reviewed by agent, pending user review; still no inference; cash earns 0%; dividends excluded
- **code:** `e1b82fee14` (dirty) · python 3.13.5
- **amended 2026-09-30T23:50:33:** registration/reproduction code committed in 9dcee96 (records were written from the uncommitted working tree)

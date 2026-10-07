# Experiment registry

_Generated from `registry/experiments.jsonl` (append-only) by `python3 -m src.registry.experiments` - do not edit by hand._

Registered experiments: 21 · logged trials (every run, incl. casual): 10 (trials log started 2026-09-30; earlier casual runs were not logged).

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
| ORBV1-20261001-001 | **DIAGNOSTIC** | ORB 30m on 15m bars, long/short, exit 15:00 bar OPEN (X2) | `data/india/<SYMBOL>m15.csv x50, rows < 2026-10-01 only` | 2026-08-03 → 2026-09-30 | development data; holdout not loaded | yes - development data viewed during implementation validation; no parameter, cost, exit, test or rule changed in response | DEV SANITY ONLY: mean net -16.301 bps/day (Z-5), label NEGATIVE; gross -0.702 bps/day; not evidence |
| ORBV1-20261002-001 | **DIAGNOSTIC** | ORB 30m on 15m bars, long/short, exit 15:00 bar OPEN (X2) | `data/india/<SYMBOL>m15.csv x50` | 2026-08-03 → 2026-09-30 | development, dry run of locked pipeline | dry run on development data | NEGATIVE: mean -16.3006 bps/day, p=1.0000 |
| ORBV1-20261002-002 | **DIAGNOSTIC** | ORB 30m on 15m bars, long/short, exit 15:00 bar OPEN (X2) | `data/india/<SYMBOL>m15.csv x50` | 2026-08-03 → 2026-09-30 | development, dry run of locked pipeline | dry run on development data | NEGATIVE: mean -16.3006 bps/day, p=1.0000 |
| S2-MOM-v1 | **FINAL** | S2-MOM-v1 12-1 cross-sectional momentum, bias ladder A-E | `RET-1.1 + UNIV-1 + ID-1 (data/stage2), rebuilt by scripts/build_stage2.py` | 2012-07 (holding month) → 2026-08 (holding month) | confirmation run once on 2026-10-05, after the primary run was registered, with the same code hash | yes - all registered results viewed; C2 analyses executed late, after the main results were known (not blind, not confirmatory) | H1 primary delta -0.059%/mo (NW p 0.78): INCONCLUSIVE, NOT RELIABLE (R_SPAN); confirmation delta +0.675%/mo (p 0.014): NOT CONFIRMED (opposite sign). H2d (W_A - W_D, executed late) +0.577%/mo primary, +1.223%/mo confirmation: supported after Holm, confirmed. H3 supported in primary only; H4 (S0) supported in primary, not run in confirmation |

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

### ORBV1-20261001-001 — ORB 30m on 15m bars, long/short, exit 15:00 bar OPEN (X2)

- **research_question:** Implementation validation of the ORB v1 pipeline (X2 exit, portfolio aggregation, inference, baselines) - not a research test
- **hypothesis:** n/a (diagnostic); protocol H1 = mean daily net portfolio return > 0
- **null_hypothesis:** n/a (diagnostic); protocol H0 = mean daily net portfolio return <= 0
- **dataset_stage:** development (pre-holdout)
- **parameters:** {'range_minutes': 30, 'entry_cutoff': '14:30', 'max_entries_per_day': 1, 'exit': '15:00 open', 'sizing': 'fixed_notional Rs 1 lakh'}
- **cost_model:** Zerodha NSE equity intraday 2026-09-30 (grid GROSS,Z-0,Z-2,Z-5,Z-10,Z-20,U-5)
- **slippage:** primary 5 bps/side
- **benchmark:** A open-to-close long (09:15 open -> 15:00 open), context only
- **cash_treatment:** idle capital 0%
- **dividends:** n/a intraday
- **statistical_tests:** null-centred stationary bootstrap (PW block), sign-flip E, random-entry D, Holm
- **limitations:** 42 sessions; descriptive implementation check; results must not be used to modify the protocol
- **code:** `7cfad45b9c` (dirty) · python 3.13.5

### ORBV1-20261002-001 — ORB 30m on 15m bars, long/short, exit 15:00 bar OPEN (X2)

- **research_question:** ORB v1 primary question (see protocol)
- **hypothesis:** mu > 0
- **null_hypothesis:** mu <= 0
- **dataset_stage:** development (dry run)
- **parameters:** {'range': 30, 'cutoff': '14:30', 'exit': '15:00 open', 'K': 100000}
- **cost_model:** cost_scenarios.json (primary Z-5)
- **slippage:** 5 bps/side primary
- **benchmark:** A open-to-close (context); baselines D, E
- **cash_treatment:** 0%
- **dividends:** n/a
- **statistical_tests:** null-centred stationary bootstrap (PW auto block); E, D Holm; per-stock Holm; DSR reporting
- **limitations:** see protocol
- **code:** `6ba8045a5f` (dirty) · python 3.13.5

### ORBV1-20261002-002 — ORB 30m on 15m bars, long/short, exit 15:00 bar OPEN (X2)

- **research_question:** ORB v1 primary question (see protocol)
- **hypothesis:** mu > 0
- **null_hypothesis:** mu <= 0
- **dataset_stage:** development (dry run)
- **parameters:** {'range': 30, 'cutoff': '14:30', 'exit': '15:00 open', 'K': 100000}
- **cost_model:** cost_scenarios.json (primary Z-5)
- **slippage:** 5 bps/side primary
- **benchmark:** A open-to-close (context); baselines D, E
- **cash_treatment:** 0%
- **dividends:** n/a
- **statistical_tests:** null-centred stationary bootstrap (PW auto block); E, D Holm; per-stock Holm; DSR reporting
- **limitations:** see protocol
- **code:** `b4ff6a6e20` (dirty) · python 3.13.5

### S2-MOM-v1 — S2-MOM-v1 12-1 cross-sectional momentum, bias ladder A-E

- **research_question:** How much do common historical-data and backtesting shortcuts distort measured cross-sectional momentum in Indian equities? (protocol §1)
- **hypothesis:** H1: mean of delta != 0, two-sided, alpha 0.05 (protocol §2)
- **null_hypothesis:** mean of delta = 0
- **dataset_stage:** stage2 research-grade
- **parameters:** {'formation_months': 12, 'skip_months': 1, 'holding_months': 1, 'entry': 'close of first session after the selection date', 'breakpoint': 0.3, 'weights': 'equal', 'top_n': 200, 't_star': '2026-09-30'}
- **cost_model:** protocol §13 with Addendum 1 and Supplements 1-4: dated statutory/exchange/broker charges (config/cost_schedules/delivery_nse_eq_s2mom_v1_dated.json, SHA-256 47a9bad407b87b781c3584986b76b23216c2af33eb2b2f9986d23f710098a10f) + assumed slippage scenarios S0-S4
- **slippage:** {'S0': {'1-200': 0, '201-500': 0}, 'S1': {'1-200': 5, '201-500': 15}, 'S2': {'1-200': 10, '201-500': 30}, 'S3': {'1-200': 25, '201-500': 75}, 'S4': {'1-200': 50, '201-500': 150}}
- **benchmark:** equal weight of all rankable stocks in the same step (§24)
- **cash_treatment:** fully invested; missed exits per §22
- **dividends:** not included (price returns)
- **statistical_tests:** {'primary': 'mean of delta, Newey-West HAC, lag 4, two-sided 5%', 'robustness': 'stationary bootstrap, 10,000 resamples, automatic block length', 'reference_threshold_pct_per_month': 0.1}
- **limitations:** see protocol §30
- **code:** `7d4cb6d977` (dirty) · python 3.13.5
- **amended 2026-10-05T19:22:46:** second Phase 3B review (2026-10-05): reviewer decisions 1, 5, 6 recorded; decisions 2-4 left open because they conflict with frozen protocol §20(b) and §22
- **amended 2026-10-05T19:35:04:** third Phase 3B review (2026-10-05): reviewer chose to keep S2-MOM-v1 frozen (option 1). Interpretations recorded: §20(b) fill = simple mean of the other stocks' same-day returns; §22 applied literally in steps C and D (realised raw gap return booked; delisting 0% voluntary / -30% otherwise, as written in §22); 'trades again later' / 'never trades again' decided from all research data up to 2026-09-30. Earlier reviewer decisions 2-4 withdrawn. No protocol text changed.
- **amended 2026-10-05T20:51:33:** Stage 2 rebuild passed 150 of 150 checks (protocol §4, §25); registered after the pass
- **amended 2026-10-05T20:55:05:** blinded precision step generated
- **amended 2026-10-05T21:10:15:** primary run registered
- **amended 2026-10-05T21:17:09:** sensitivity run registered
- **amended 2026-10-05T21:28:57:** confirmation run registered
- **amended 2026-10-05T21:56:38:** Addendum 1 (cost specification for step E) approved and registered. Specified after the gross primary, sensitivity and confirmation results were known and before any cost, turnover or net return was computed. Changes no part of A-D. B2, B3 and B4 remain open.
- **amended 2026-10-06T01:35:55:** Supplement 1 to Addendum 1 (seven rulings on cost evidence) approved and registered. Specified after the cost evidence was archived and before any cost, turnover or net return was computed. Changes no part of A-D. Addendum 1 unchanged. B2, B3, B4 remain open.
- **amended 2026-10-06T21:56:27:** Supplement 2 to Addendum 1 (rulings 8-16 on the step E method) approved and registered. Specified after the gross A-D results and the H3 outcomes were known and before any real cost, turnover, net return, break-even or H4 result was computed. Changes no part of A-D. Frozen protocol, Addendum 1 and Supplement 1 unchanged. Step E not run. B3, B4 remain open.
- **amended 2026-10-06T22:03:58:** Supplement 3 to Addendum 1 (rulings 19-20: step E input boundary and identifier join) approved and registered. Input-boundary and implementation-methodology amendment only. Specified after a key-only identifier check and before any real cost, turnover, net return, break-even or H4 result was computed. Changes no part of A-D and no existing result. Frozen protocol, Addendum 1, Supplement 1 and Supplement 2 unchanged. Step E not run. B3, B4 remain open.
- **amended 2026-10-06T22:23:14:** Supplement 4 to Addendum 1 (ruling 21: formation-rank guard applies to W and L only, not to the benchmark) approved and registered. It formalises a ruling already approved during the step E implementation review and makes no other methodological change. Specified before any real cost, turnover, net return, break-even or H4 result was computed. Changes no part of A-D and no existing result. Frozen protocol, Addendum 1 and Supplements 1-3 unchanged. Step E not run. B3, B4 remain open.
- **amended 2026-10-06T22:29:16:** step E run registered
- **amended 2026-10-07T13:39:49:** C2 run registered: pre-registered analyses executed late, after the primary, sensitivity, confirmation and step E results were known (not blind, not confirmatory)
- **amended 2026-10-07T13:45:02:** metadata correction 1 of 6: status PLANNED -> FINAL. The experiment was executed and registered (blinded step, primary, sensitivity and confirmation on 2026-10-05; step E on 2026-10-06; C2 late analyses on 2026-10-07). The original record fields described the state at registration. No result changed.
- **amended 2026-10-07T13:45:02:** metadata correction 2 of 6: stale 'not run' wording. Step E was executed once on 2026-10-06 and H4 was run for the primary sample (step_e_results.json 67539848...39e0). The deviation log line 'Step E and H4 have not been run' described 2026-10-05; a dated status update is appended to that log and the original text is preserved. B2 closed 2026-10-06; B3 and B4 remain open.
- **amended 2026-10-07T13:45:02:** metadata correction 3 of 6: PENDING fields in the immutable result files are not edited. docs/research/s2_mom_v1_results_guide.md maps each stale field to the later registered artifact that supersedes it (step E fields -> step_e_results.json; sensitivity, reverse ladder and reliability -> sensitivity_results.json; H2d, adjustments, halves, pooled, skewness, worst month -> c2_results.json). The frozen protocol header 'Not yet registered' was true at the freeze (commit 7d4cb6d, 2026-10-05); this record was created afterwards and carries the frozen SHA-256 f1abd954...d838; the header is not edited.
- **amended 2026-10-07T13:45:02:** metadata correction 4 of 6: cost schedule reference. Step E used config/cost_schedules/delivery_nse_eq_s2mom_v1_dated.json, SHA-256 47a9bad407b87b781c3584986b76b23216c2af33eb2b2f9986d23f710098a10f. The file named in the original record (delivery_nse_eq_s2mom.json) is the earlier incomplete template of 2026-10-05; no cost was calculated from it.
- **amended 2026-10-07T13:45:02:** metadata correction 5 of 6: reliability scope. Frozen §25 criterion 3 was evaluated for H1 and H3 only. The label NOT RELIABLE stands for H1 through R_SPAN (sign change). The sensitivity of H4 is UNKNOWN: the sensitivity treatments were not executed for step E (DEV-2).
- **amended 2026-10-07T13:45:02:** metadata correction 6 of 6: scope note. 'MATERIAL' in confirmation_results.json (H1.decision) is a code-level application of the frozen §27 rule outside its stated primary-only scope and is NOT a registered conclusion. Registered status of H1: primary INCONCLUSIVE and NOT RELIABLE; confirmation NOT CONFIRMED (frozen B3 rule, opposite sign). DEV-2 (pre-registered analyses not executed; seven executed late) is recorded in docs/research/s2_mom_v1_deviation_log.md.
- **amended 2026-10-07T18:17:13+05:30:** Remediation of forensic audit findings F-02 and F-12 (2026-10-07), approved by the researcher: the Stage 3 input manifest, the two pre-run check files, the Stage 2 rebuild log, the cost schedules and the external data archive are anchored in the registry by SHA-256. Hashes were computed from the files as they stood before remediation (pre-remediation snapshot docs/audit/remediation/pre_remediation_snapshot.json). No protocol, result, input or code file was changed; no experiment was rerun.
- **amended 2026-10-07T18:36:04+05:30:** Remediation of forensic audit finding F-06 (2026-10-07), approved by the researcher: the pinned environment specification is anchored. It was OBSERVED AFTER THE FACT on the machine that produced the registered runs; the environment blocks written at run time did not record scipy or pyarrow. In this environment scripts/reproduce_s2_mom_v1.py reproduced the registered primary, confirmation, step E and C2 numbers from an independent implementation (largest absolute difference 6.7e-14). No protocol, result, input or frozen code file was changed; no experiment was rerun.
- **amended 2026-10-07T23:17:59+05:30:** Remediation, reproducibility contract (2026-10-07, requested by the researcher): environment_files_sha256_v2 SUPERSEDES environment_files_sha256 for verification; the earlier anchor stays in the registry. Reason: the header of requirements-lock.txt as first anchored implied that `pip install` rebuilds the research environment. That is not true: the registered runs used Conda builds, and on macOS 27 arm64 the PyPI wheel of scipy 1.15.3 cannot be loaded. The official environment is now stated as Conda osx-arm64 (environment.yml, conda-osx-arm64.lock); a clean Conda environment created from environment.yml reproduced the registered numbers (PASS, largest absolute difference 6.7e-14). No package version changed. No protocol, result, input or frozen code file was changed; no experiment was rerun.

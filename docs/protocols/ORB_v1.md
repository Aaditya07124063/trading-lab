# ORB research protocol — v1

**Status:** DRAFT
**Version:** 1.0-draft · created 2026-09-30 · code at commit shown in the git log for this file
**Freeze rule:** once the status line reads `FROZEN`, this file is never edited;
changes create `ORB_v2.md`. The loader only opens the prospective holdout for a
FROZEN protocol (`src/intraday/data.py`).

## 1. Question and hypotheses
- **RQ:** Does opening-range breakout on NSE large-cap stocks survive realistic
  Indian transaction costs?
- **H1:** The mean daily net return of long/short ORB (primary cost scenario) is
  > 0 and exceeds the open-to-close benchmark and the random-entry baseline.
- **H0:** Mean daily net return ≤ 0, and ORB is not better than random entry
  with identical exposure and costs.
- The answer may be negative; a negative result is reported as such.

## 2. Strategy (fixed)
- Bars: 15-minute, bar-start timestamps, IST, NSE session 09:15–15:30.
- Opening range: bars 09:15 and 09:30 (range 09:15–09:45). OR_HIGH/OR_LOW =
  max high / min low of those bars; day skipped if either bar is missing.
- Signal: first later **completed** bar whose close > OR_HIGH (long) or
  < OR_LOW (short). One entry per day.
- Execution: next bar's open. Entry fills after **14:30** are refused.
- Exit: close of the **15:15** bar. No overnight positions. No stops/targets.
- Sizing: 100% of the instrument sleeve's equity, integer shares, no leverage;
  each instrument is an independent sleeve with equal starting capital.
- Implementation: `src/intraday/orb.py`, `src/intraday/engine.py` (commit at freeze).

## 3. Costs (fixed grid; primary scenario marked)
- Schedules: `config/cost_schedules/*_20260930.json`, sources in
  `docs/evidence/cost_sources.md` (Zerodha & Upstox published pages; NSE
  circular NSE/FA/73061).
- Grid (`config/cost_scenarios.json`): GROSS (reference), Z-0, Z-2, **Z-5
  (primary, proposed)**, Z-10, Z-20 bps slippage per side, U-5.
- Capital per sleeve: **Rs 1,00,000 (primary, proposed)**; sensitivity at
  Rs 10,00,000 (fixed brokerage matters less).
- Report: gross P&L, each cost component, slippage, net P&L; **break-even
  slippage** (bps/side at which mean net daily return = 0).

## 4. Benchmarks / baselines (all on identical sessions and costs)
A. Open-to-close long-only (buy 09:15 open, sell 15:15 close).
B. Long-only ORB. C. Long/short ORB (primary).
D. Random-entry: per ORB trade day, random direction and random entry bar
   uniformly in [09:45, 14:30], exit 15:15, same costs; 10,000 draws, seed 20260930.
E. Sign-randomisation of ORB trade directions (tests directional content).
F. Buy-and-hold over the same dates (context only).

## 5. Samples
- **Development:** all intraday data before 2026-10-01 (15-min from
  2026-04-23; 1-hour from 2023-08-02). Status: EXPOSED — VIEWED FOR
  RESEARCH/DIAGNOSTIC PURPOSES; NO PARAMETER TUNING PERFORMED (RELIANCE).
  1-hour data may be used only for ORB-60 engine/robustness work and is NOT
  evidence for the 15-min ORB-30 rule.
- **Prospective clean holdout:** 15-min bars from **2026-10-01** until
  **≥ 250 sessions** are collected (target ≈ Oct 2027). Evaluated once, after
  freezing, never used for decisions.
- Instruments: see §8 (open question).

## 6. Metrics
Per sleeve and pooled: mean daily net return (bps), volatility, Sharpe,
CAGR, max drawdown, exposure, trades (long/short), win rate, profit factor,
average win/loss, cost breakdown, benchmark differences.

## 7. Statistical analysis (why each test)
- **Stationary bootstrap** (Politis–Romano) CIs for mean daily return, Sharpe
  and strategy−benchmark difference — daily P&L may be autocorrelated and
  non-normal; block length chosen by a stated rule before viewing holdout.
- **Random-entry (D) and sign-randomisation (E)** — distinguish ORB timing /
  direction from generic intraday exposure; p = share of draws ≥ observed.
- **Holm correction** across instruments; **deflated Sharpe ratio** using the
  trial count from `registry/trials.jsonl`.
- **Power:** minimum detectable mean daily return at 80% power given
  development-period volatility, computed and reported before the holdout.
- **Regimes** (defined from past data only): high/low volatility = prior
  20-session realised volatility above/below its expanding median; trend =
  sign of prior 20-session return.
- No test is reported without its assumption statement.

## 8. Open items before FREEZE (require user decision)
1. Primary slippage (proposed 5 bps/side) and capital (proposed Rs 1 lakh).
2. Instrument universe (currently only RELIANCE, TCS, HDFCBANK, INFY with
   15-min data; survivorship limitation).
3. Data source for the holdout collection (Yahoo exploratory vs licensed).
4. Completion of the literature review (#3 in the review must be read).

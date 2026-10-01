# ORB v1 — final protocol review (proposed text for freezing)

**Date:** 2026-10-01
**Status:** PROPOSED — NOT FROZEN.
- `docs/protocols/ORB_v1.md` is still the DRAFT of 2026-09-30.
- After Aaditya approves this review, its §1–27 replace the draft and the status line becomes FROZEN.
- Until then the data loader keeps the holdout locked.

**Approvals already given (2026-10-01):**
- X2 exit;
- primary H1/H0, one-sided α = 0.05;
- cost model;
- statistical framework;
- random baselines;
- unchanged ORB entry rules;
- complete missing-bar rules required.

Items still open are listed in §28 and marked **[OPEN]** where they occur.

**Labels:**
- **FROZEN RULE**: will be fixed at freeze. It may not change after holdout data is seen; a change means ORB v2.
- **SENSITIVITY / EXPLORATORY**: reported, never used to decide H1, never used to modify the protocol.

**Code implementing this text:** `a9a8f7f` (engine), `7cfad45` (inference, portfolio, baselines, regimes), `41a7a30` (validation driver). The exact commit at freeze is to be recorded on the status line.

---

## 1. Research question — FROZEN
Does the predefined ORB strategy generate positive mean daily net returns, after realistic transaction costs and slippage, when applied as an equal-weighted portfolio across the frozen NIFTY 50 universe?

## 2. Hypothesis — FROZEN
- **H1:** μ > 0. **H0:** μ ≤ 0.
- μ is the expected daily net portfolio return R_t (§12) under the primary cost scenario (§15–16).
- One-sided test, **α = 0.05**.
- One primary hypothesis only. Everything else is secondary or exploratory (§21).

## 3. Universe — FROZEN
- **Constituents:** NIFTY 50 as published by NSE.
  - File: `data/metadata/universe/NIFTY50_frozen_20261001.json`, from `ind_nifty50list.csv`.
  - Retrieved 2026-10-01 08:26 IST; SHA-256 `f5ba4027d935…`; commit `fc3b26d`.
- **N = 50**, fixed for the whole holdout.
- **Membership:** never updated for index changes; never substituted.
- **CAS status:** all 50 are F&O, i.e. Closing Auction Session (CAS), stocks (verification §1.2).

## 4. Data source — FROZEN
- **Source:** Yahoo Finance 15-min OHLCV via the logged, append-only collector (`update_intraday.py`, launchd 18:30 IST weekdays).
- **Raw snapshots:** checksummed in `data/raw/manifest.jsonl`.
- **Attempt log:** `data/raw/collection_log.jsonl`.
- **Timestamps:** bar-start, IST.
- **Integrity check (flag only, never used to correct prices):** per holdout session, compare against the NSE bhavcopy. The 15-min bars' 09:15 open and intraday high/low are checked against the bhavcopy open/high/low. Flags are reported.
- **SENSITIVITY:** excluding flagged stock-sessions.

## 5. Data period — FROZEN
- **Development:** all bars before 2026-10-01.
  - All 50 stocks have 15-min data from 2026-08-03.
  - RELIANCE, TCS, HDFCBANK and INFY have 15-min data from 2026-04-23.
  - Status: EXPOSED / DIAGNOSTIC (LEGACY-014/015, ORBV1-20261001-001).
- **Holdout:** from 2026-10-01 to **[OPEN-1: end point]**.

## 6. Holdout boundary — FROZEN
- **Start:** 2026-10-01, the first session.
- **Data lock:** no bar dated on or after that start is loaded until this protocol is FROZEN (`load_intraday`).
- **Single evaluation:** the holdout is evaluated **once**, after the end point.
- **Allowed in the meantime:** collector-health monitoring (row counts, rejections, missing-bar counts).
- **Not allowed:** returns, signals, trades or P&L from the holdout are not computed or viewed before the end point.

## 7. Opening range — FROZEN (unchanged from draft)
The 09:15 and 09:30 bars (09:15–09:45). OR_HIGH = max high; OR_LOW = min low.

## 8. Breakout definition — FROZEN (unchanged)
- **Signal:** the first **completed** bar after the range (09:45 or later) whose **close** is above OR_HIGH (long) or below OR_LOW (short).
- **One signal per stock per day.** Later opposite breaks are ignored.

## 9. Entry timing — FROZEN (unchanged)
- Fill at the **open of the next bar** after the signal bar, so the earliest fill is 10:00.
- **Entry cutoff 14:30:** no entry fill after the 14:30 bar open.
- One trade per stock per day.

## 10. Exit timing — FROZEN (X2, approved)
- **Rule:** square off every position at the **open of the 15:00 IST bar**, i.e. the first trade of the 15:00–15:15 interval.
- **Not used for the exit:**
  - the 15:00 bar's high, low or close;
  - the 15:15 bar;
  - the closing-auction price.
- **No overnight positions.**
- **Market-structure note** (verification Part 1):
  - For CAS stocks, continuous trading ends at 15:15; the closing auction runs 15:15–15:35 (SEBI circular, 16 Jan 2026, effective 2026-08-03).
  - X2 exits 15 min before the continuous-session boundary, with the same clock time and mechanism before and after CAS.
- **Implementation constraint (documented, NOT the research rule):** broker MIS auto-square-off for CAS stocks is 15:12 (Zerodha) and 15:10 (Upstox, since 2026-09-11).
  - X2 at 15:00 precedes both, so long and short trades are implementable with standard intraday products.
  - A broker's cut-off is a product constraint and does not define the strategy.
- **FUTURE SENSITIVITY (not ORB v1):** an exit in the closing auction (X3).

## 11. Position sizing — FROZEN
- **Fixed notional:** K = ₹1,00,000 per stock per session, every session.
- **Quantity:** qty = largest integer with qty × entry_fill + entry charges ≤ K.
- **No leverage, no compounding:** P&L is not reinvested.
- **SENSITIVITY:** K = ₹10,00,000.

## 12. Portfolio construction — FROZEN (one definition)

**R_t = Σ_{i=1..50} NetPnL_{i,t} / (50 × ₹1,00,000)**

- **NetPnL_{i,t}:** the rupee P&L of stock i's ORB trade in session t, after brokerage, STT, exchange charges, SEBI fee, stamp duty, GST and slippage.
- **Zero contributions:** NetPnL_{i,t} = 0 when stock i has no signal, has a refused entry, has a non-tradable session (§13), or has no data.
- **Unused capital:** stays in cash at 0 % interest.
- **Return basis:** R_t is the **return on total fixed portfolio capital (₹50 lakh)**, not the average return of stocks that traded.
- **Sessions:** t runs over every standard NSE session in the holdout (§13.6), including sessions with zero trades.
- **Statistic:** the primary statistic is the sample mean of R_t.

## 13. Missing-data rules — FROZEN (deterministic; depend only on bar existence, never on prices)

1. **Complete-session rule.** A stock-session is **tradable only if every 15-min bar from 09:15 through 15:00 (24 bars) exists**. Otherwise it is non-tradable: no trade, NetPnL = 0. It is recorded with the list of missing bar times (`missing_bars` in engine output).
   - This covers: a missing opening-range bar; a missing breakout-confirmation bar; any missing intermediate bar; a missing 15:00 (exit) bar.
   - **Rationale:** with a complete session the simulated decision sequence (first breakout, next-bar fill, exit) is exactly what a real-time trader would have seen. With a gap, the "first" breakout or the "next bar" is unknowable.
2. **15:15 bar.** Never required, never used. Since 2026-08-03 Yahoo omits it on about 22 % of stock-sessions (it carries the auction print).
3. **No synthetic prices.** No forward-fill, interpolation or substitution of any price.
4. **Entire stock-session missing:** non-tradable, NetPnL = 0, counted.
5. **Reporting:** count and list non-tradable stock-sessions per stock and per session.
   - If more than 10 % of holdout stock-sessions are non-tradable, the result is labelled **DATA-LIMITED** in addition to its verdict.
6. **Session calendar.** The holdout calendar is the NSE equity trading-day list for standard sessions (09:15–15:30).
   - Store the NSE holiday circular for 2026–27 in `docs/evidence/` at freeze **[OPEN-6]**.
   - **Special or non-standard sessions** (e.g. Muhurat trading, expected in Nov 2026; other sessions with non-standard hours) are **excluded from the calendar**.
   - A standard session with no data for a stock stays in the calendar and contributes 0 for that stock.
7. **Data integrity:** bhavcopy flags (§4) are reported; flagged data is not altered.
8. **Pre-holdout check:** all 2,100 development stock-sessions (2026-08-03..09-30) were complete under rule 1. This describes the data and was not used to choose the rule.
9. **SENSITIVITY:**
   - a looser "available-bar" rule (scan only existing bars; trade only if the next contiguous bar exists);
   - excluding bhavcopy-flagged sessions.

## 14. Corporate-event rules — FROZEN
- **Splits, bonuses, dividends:**
  - Returns are intraday (entry and exit on the same session), so they are unaffected by adjustments.
  - Stored bars are as-collected; existing bars always win in the append-only merge, and later vendor re-adjustments never overwrite them.
  - Ex-dates are traded normally.
- **Suspension or no trading:** non-tradable (§13), NetPnL = 0, counted.
- **Demerger, merger, delisting:** the frozen symbol stays in the universe. Sessions without data are non-tradable.
  - No replacement or successor entity is added; for example, a demerged entity is not added.
- **Symbol or ticker change:** map old to new only with NSE evidence stored in `docs/evidence/`, logged in `RESEARCH_LOG.md`.
- **Index reconstitution:** ignored (§3).

## 15. Transaction costs — FROZEN
- **Schedule:** Zerodha NSE equity-intraday schedule `config/cost_schedules/zerodha_nse_eq_intraday_20260930.json`.
  - Brokerage: min(₹20, 0.03 %) per order.
  - STT: 0.025 %, sell side.
  - Exchange: 0.00307 %. SEBI: ₹10/crore. Stamp: 0.003 %, buy side.
  - GST: 18 % on brokerage + exchange + SEBI.
  - Sources: `docs/evidence/cost_sources.md`, NSE circular FA/73061.
- **Changes:** any change in a published schedule before freeze is recorded as a dated amendment. No change after freeze.
- **SENSITIVITY:** the Upstox schedule (U-5). Identical to Zerodha at ₹1 lakh because both brokerages cap at ₹20; it differs at ₹10 lakh.

## 16. Slippage — FROZEN
- **Primary:** 5 bps per side, adverse (buys fill higher, sells lower), on entry and exit.
- **SENSITIVITY:** 0, 2, 10 and 20 bps per side, plus GROSS (zero cost, reference only).
- **Break-even slippage:** reported (the bps per side at which mean R_t = 0), or "none ≥ 0" if the mean is negative even at 0 bps.

## 17. Benchmarks — FROZEN as **descriptive context** (not part of H1)
- **A. Open-to-close long:** buy at 09:15 open, sell at **15:00 open (X2)**. Same tradable sessions, sizing, costs and aggregation.
- **B. Long-only ORB:** same rules, shorts disabled.
- **F. Buy-and-hold:** context only.
- Benchmarks are reported but do not enter the verdict. Comparing against the drift-exposed A would confound edge with market direction (the SSRN 5198458 lesson).

## 18. Random baselines — FROZEN (confirmatory secondary family, §21)

**E — random direction (sign-flip).**
- **Kept from each actual ORB trade:** stock, session, entry and exit times, and quantity.
- **Randomised:** each trade's direction becomes an independent fair coin, s_j = ±1. Gross P&L becomes s_j × gross_j.
- **Costs:** costs actually incurred (charges + slippage) are subtracted **unflipped**.
- **Approximation (documented):** a flipped trade's exact fill and charges would differ by second-order amounts.
- **Statistic:** mean R_t over all holdout sessions.
- **p-value:** p_E = (1 + #{draws ≥ observed}) / (B + 1).
- **Draws and seed:** B = 10,000, seed 20260930.
- **Tests:** whether ORB's *direction* beats chance at identical timing and exposure.

**D — random entry time + random direction.**
- **Kept:** for every actual ORB trade, the same stock and session (so the same number of trades per stock-session).
- **Randomised:**
  - entry bar drawn uniformly from the **ORB-feasible entry bars, 10:00–14:30 inclusive (19 bars)**;
  - fair-coin direction.
- **Fill and exit:** fill at that bar's open; exit at the 15:00 open.
- **Sizing and costs:** the same fixed-notional sizing, slippage and charges, computed exactly.
  - Verified equal to the engine: maximum difference ₹1e-12 over 1,810 development trades.
- **Statistic, p and seed:** as for E.
- **Tests:** whether ORB's *timing and direction* beat random intraday exposure on the same days.
- **[OPEN-4]:** the draft said 09:45–14:30. 09:45 is not a feasible ORB fill time (the earliest signal is the 09:45 close, which fills at 10:00), so 10:00–14:30 is implemented. Please confirm.

**Not done.** No baseline was designed or modified after seeing holdout data. None has been computed on holdout data.

## 19. Statistical tests — FROZEN

**Primary test** (`src/intraday/inference.py`):
- **Method:** null-centred **stationary bootstrap** (Politis & Romano 1994) of the daily series R_t.
- **p-value:** p = (1 + #{m\*_b − x̄ ≥ x̄}) / (B + 1).
- **Draws and seed:** B = 10,000, seed 20261001.
- **Mean block length:** Politis & White (2004), with the Patton, Politis & White (2009) correction. **[OPEN-2]:** whether it is fixed from development data or computed by the same rule on the evaluation series.
  - On the 42 development sessions the rule gives b = 1.0 (no detectable dependence).
  - A fixed b = 1 would be the i.i.d. bootstrap and gives no protection if the holdout is dependent.
  - **Recommendation:** apply the pre-specified automatic rule to the evaluation series. It is a deterministic algorithm fixed now, not a choice made after seeing results. Add sensitivity at ½× and 2×.

**Reported for the primary test:**
- n;
- mean (bps/day);
- sd;
- bootstrap SE;
- t_boot = mean/SE;
- one-sided p;
- one-sided 95 % lower and upper bounds;
- two-sided 95 % CI;
- annualised Sharpe (√252);
- the block length used.

**Guards** (`tests/test_orb_v1_stats.py`):
- p ≈ U(0,1) under the null;
- p → 0 under a strong effect;
- one-sided: never "positive" for negative effects;
- p < α ⇔ lower bound > 0;
- an explicit test that the SSRN 5198458 uncentred construction gives about 0.5 under a strong effect while ours does not.

## 20. Confidence intervals — FROZEN
- **Primary-test bounds:** basic-bootstrap intervals from the same draws as the primary test.
  - One-sided 95 % lower bound: x̄ − q95(m\* − x̄).
  - One-sided 95 % upper bound: x̄ − q05(m\* − x̄).
  - Two-sided 95 % CI.
- **Secondary quantities** (Sharpe, break-even slippage, cost components): point estimates, with bootstrap CIs where computed. Descriptive.

## 21. Multiple-testing methodology — FROZEN

| Family | Contents | Control | Role |
|---|---|---|---|
| 1 | Primary H1 (§2, §19) | none needed (single test) | **Confirmatory** |
| 2 | ORB vs E; ORB vs D (§18) | Holm, α = 0.05 | Confirmatory secondary |
| 3 | 50 per-stock tests (stationary bootstrap on stock i's NetPnL/K) | Holm (Romano–Wolf as sensitivity) | **Exploratory** |
| — | Cost grid, ₹10 lakh, long-only B, benchmark A, regimes, block-length sensitivity, missing-data sensitivity | none; no confirmatory claims | Descriptive |

- **Registry:** every run is logged in `registry/trials.jsonl`, and every experiment is in `registry/experiments.jsonl`. This includes LEGACY-014/015 and ORBV1-20261001-001.
- **No re-selection:** no variant (window, cutoff, exit, filter) may be selected after viewing holdout results. Any variant run on holdout data is exploratory, registered, and cannot replace H1.
- **FUTURE / supplementary:** a deflated Sharpe ratio using the registry trial count. Reporting only, not in the verdict. Not yet implemented **[OPEN-7]**.

## 22. Power analysis — FROZEN (computed from development data only)

| Item | Value |
|---|---|
| Development portfolio daily series | n = 42 |
| Long-run sd | **16.0 bps/day** (bootstrap SE × √n) |
| MDE, n = 125 sessions | 3.6 bps/day |
| **MDE, n = 250 sessions** | **2.5 bps/day** |
| MDE, n = 500 sessions | 1.8 bps/day |

- **Definition:** MDE = (z₀.₉₅ + z₀.₈₀) × sd_LR / √n, the smallest true mean detectable with 80 % power by the one-sided 5 % test.
- **Caveat:** the sd is estimated from only 42 sessions, in a period that was mostly low-volatility according to the proxy regime labels. The holdout variance may differ.
- **Interpretation:** a true net edge below about 2.5 bps/day on ₹50 lakh is likely to produce INCONCLUSIVE at n = 250.

## 23. Regime analysis — EXPLORATORY ONLY (definitions frozen)
- **Labels** (`src/intraday/regimes.py`) use data up to session t−1 only (tested):
  - **vol regime:** HIGH if the 20-day sd of NIFTY 50 daily returns, ending t−1, exceeds its expanding median; otherwise LOW;
  - **trend regime:** UP if the NIFTY 50 20-day return ending t−1 is > 0; otherwise DOWN.
- **Reporting:** mean R_t, n and SE per regime. Descriptive; no regime-conditional claims.
- **[OPEN-3]: source of the NIFTY 50 daily close.** The stored `NIFTY50d1.csv` ends 2026-07-17. Options:
  - (a) NSE / NSE Indices official daily close;
  - (b) Yahoo ^NSEI daily;
  - (c) the last 15-min bar of NIFTY50m15 (used provisionally in the development validation).

  The expanding-median start date must also be fixed.

## 24. Robustness analysis — SENSITIVITY ONLY
- Cost grid (§15–16) and ₹10 lakh capital;
- long-only B;
- block length ½× / 2×;
- missing-data sensitivities (§13.9);
- the per-stock family (§21);
- regimes (§23);
- **FUTURE (not v1):** X3 closing-auction exit, X1 continuous-session-close exit, other OR windows, volume filters.

None of these can change the verdict or the protocol.

## 25. Reporting requirements — FROZEN
Report all of the following, whatever the result:
1. The primary-test output (§19) and the verdict label (§27).
2. Family 2 p-values (raw and Holm).
3. Gross mean, each cost component in ₹ and bps, net mean, break-even slippage.
4. Trades: count, long/short split, entry-time distribution, stock-sessions traded.
5. Non-tradable counts and the DATA-LIMITED flag.
6. Benchmarks A, B and F (context).
7. Exploratory and sensitivity tables, each labelled.
8. Every deviation from this protocol.
9. Commit hashes, data checksums, seeds, and the registry IDs and trial count.
10. Explicit statements:
    - "single prospective period about [n] sessions";
    - "Yahoo 15-min data";
    - "NIFTY 50 large caps frozen 2026-10-01";
    - "slippage assumed, not measured".
11. Negative and inconclusive results are reported with the same prominence as positive ones.

## 26. Reproducibility requirements — FROZEN
- **Freeze record:** the commit is recorded on the FROZEN status line. Code, config, cost schedules and the universe file are pinned at that commit.
- **Seeds:** 20261001 (primary bootstrap) and 20260930 (baselines).
- **Software:** Python and package versions captured by `environment()` in the experiment record.
- **Data:** raw snapshots retained; manifest checksums; collection log.
- **Evaluation run:** one command (an evaluation driver mirroring `run_orb_v1_dev_validation.py` but loading the holdout through the FROZEN gate), registered as an experiment.
- **Determinism:** the development validation reproduces bit-for-bit, apart from timestamps.

## 27. Positive / negative / inconclusive — FROZEN reporting categories (not targets, no scoring)
- **POSITIVE:** one-sided p < 0.05 **and** the one-sided 95 % lower bound for μ > 0 at the primary scenario.
  - Net of the full cost model and 5 bps/side slippage, this is the economic criterion: the mean return after realistic costs is credibly above zero.
- **NEGATIVE:** the one-sided 95 % upper bound for μ < 0. The mean net return is credibly below zero, so the evidence is inconsistent with H1.
- **INCONCLUSIVE:** neither. The data cannot distinguish H1 from H0 at the predefined criteria.
  - Not to be described as "profitable enough" or "not profitable".
- **[OPEN-5]:** an alternative NEGATIVE criterion, upper bound < δ (a smallest effect of interest, e.g. 2 bps/day), would classify more results as NEGATIVE. The implemented rule uses 0, with no extra parameter.

---

## 28. Remaining decisions before freeze

| # | Item | Options | Recommendation |
|---|---|---|---|
| OPEN-1 | Holdout end point | Fixed number of standard NSE sessions (e.g. 250, about Oct 2027) or a fixed calendar date | 250 sessions; MDE 2.5 bps/day (§22) |
| OPEN-2 | Block length | Fixed from development data (= 1.0) or the automatic PW rule applied to the evaluation series | Automatic rule (pre-specified algorithm) + ½× / 2× sensitivity |
| OPEN-3 | Regime index close | NSE official / Yahoo daily / 15-min proxy; expanding-median start | NSE official daily close, stored as evidence |
| OPEN-4 | D entry window | 10:00–14:30 (implemented, ORB-feasible) or 09:45–14:30 (draft) | 10:00–14:30 |
| OPEN-5 | NEGATIVE threshold | 0 (implemented) or δ > 0 | 0 |
| OPEN-6 | NSE calendar and special sessions | Store the holiday circular; exclude non-standard sessions | Yes |
| OPEN-7 | Deflated Sharpe | Implement as supplementary reporting, or drop | Implement before freeze as reporting-only, or drop explicitly |
| OPEN-8 | E null | Fair coin (implemented) or a coin with ORB's realised long share | Fair coin (H0: direction uninformative) |
| OPEN-9 | Data registry | The 46 holdout-universe files are tracked via the collector manifest, not `registry/datasets.json`. Rebuilding the registry would checksum and validate files containing holdout rows. | Register them at freeze from the manifest (checksums only, no content read) |
| OPEN-10 | Text of `ORB_v1.md` | Replace with §1–27 at freeze | Yes, on approval |
| OPEN-11 | Bhavcopy integrity check (§4) | Specified but **not yet implemented** | Implement (flag-only) before freeze, tested on development data |
| OPEN-12 | Holdout evaluation driver (§26) | Not yet written. Development validation driver exists. | Write before freeze, gated on FROZEN; do not run before the end point |

**Tooling note.** The engine default is now X2.
- 1-hour files have no 15:00 bar, so `run_intraday.py` and the dashboard refuse them with an explicit error (HTTP 400 in the dashboard) that points to `EngineConfig.legacy_v0()`.
- They are not silently run with a non-v1 exit.
- LEGACY-014/015 remain reproducible with `EngineConfig.legacy_v0()`.

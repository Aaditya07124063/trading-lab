# ORB v1 — focused verification: exit timing and SSRN 5198458 statistics (2026-10-01)

**Status:** VERIFICATION ONLY.
- `docs/protocols/ORB_v1.md` is unchanged and DRAFT.
- No protocol change was made and no option is selected here.

**Data used:**
- Pre-holdout intraday rows only (every read filtered to `Date < 2026-10-01`).
- Public NSE/SEBI documents.
- Synthetic data.

**No ORB, benchmark or strategy return was computed.**

**Reproduce:**
- `python3 scripts/verify_exit_bar_semantics.py`. Output: `docs/evidence/cas_2026/verify_exit_bar_semantics_output.txt`.
- `python3 scripts/verify_ssrn5198458_bootstrap.py`. Output: `docs/literature/verification/ssrn5198458_bootstrap_check_output.txt`.
- Evidence and checksums: `docs/evidence/cas_2026/`.

---

## Part 1 — Exit timing

### 1.1 Timestamp semantics in our data (code + data)

- **Convention:** `fetch_yahoo` (`src/intraday/pipeline.py`) converts the yfinance index to Asia/Kolkata and drops the timezone. yfinance labels each intraday bar by its **start** time.
- A bar stamped `HH:MM` covers **[HH:MM, HH:MM+15)** IST. The session grid is 09:15 … 15:15, i.e. 25 bars.
  - `09:15` = 09:15–09:30. Its open is the first price after the pre-open call auction.
  - `15:00` = 15:00–15:15.
  - `15:15` = 15:15–15:30, plus whatever Yahoo assigns after that (see 1.3).
- **Engine:** `src/intraday/engine.py` squares off at the **close of the `15:15` bar** (`square_off = "15:15"`). Sessions without a `15:15` bar are **not traded** (`_tradable_sessions`). Benchmark A uses the same price and the same session filter.

### 1.2 Current NSE market structure (primary source)

**Source:** SEBI circular HO/47/11/11(3)2025-MRD-POD2/I/2765/2026, dated 16 Jan 2026 (stored in `docs/evidence/cas_2026/`).
- CAS applies to cash-segment stocks **on which derivative contracts are available** (para 4.1.1), effective **2026-08-03**. Other stocks keep a closing price based on the last-30-min VWAP (para 4.1.2).
- For CAS stocks, the continuous trading session (CTS) ends at **15:15**. CAS runs 15:15–15:35 (para 4.2.1):

  | Time | Phase |
  |---|---|
  | 15:15–15:20 | Reference price / transition |
  | 15:20–15:25 | Order entry, limit + market |
  | 15:25–15:30 | Order entry, limit only, **random close 15:28–15:30** |
  | 15:30–15:35 | Matching |

- **Reference price:** VWAP of 15:00–15:15 trades. **Band:** ±3 %. **No equilibrium price:** the reference price becomes the close (paras 4.3, 4.4, 4.6.6).
- Unexecuted CTS limit orders carry over into CAS (para 4.8).
- **Post-close session:** 15:50–16:00, trades at the closing price (para 4.2.4).
- Equity derivatives trade until **15:40** (para 4.2.3).
- **Pre-open** is modified from **2026-09-07**: order entry 09:00–09:10 (random close 09:08–09:10), matching 09:10–09:12, transition 09:12–09:15 (para 5). CTS still starts at 09:15.
- **Frozen universe:** **50/50** constituents appear in NSE's current F&O market-lot file (retrieved 2026-10-01, stored), so **every frozen holdout stock is a CAS stock**. F&O membership is a property that can change; the current file is used as evidence for the holdout start.

### 1.3 What the data shows (pre-holdout, reproducible)

**(a) Structural break on 2026-08-03.**

| Measure | Before 3 Aug 2026 | From 3 Aug 2026 |
|---|---|---|
| `15:15` bar present, 4 long-history stocks | 100 % of sessions | — |
| `15:15` bar present, all 50 stocks | — | **77.9 %** of stock-sessions (min 47.6 %, ULTRACEMCO) |
| Volume ratio `15:15` / `15:00` | 0.76–1.13 | 0.34–0.58 |
| `15:00` and opening-range bars present | 100 % | **100 %** |

After 3 Aug, **the only bar Yahoo ever omits is `15:15`**.

> **Correction to RESEARCH_LOG 2026-10-01:** the "isolated missing bars in ~4–15 of 42 sessions" were all missing `15:15` (closing-auction) bars, not random gaps.

**(b) Post-CAS, the `15:15` bar closes at the closing-auction price.**
- Sample: 14 post-CAS days, 700 stock-days.
- Wherever the bar exists, its close equals NSE's official closing price (bhavcopy `ClsPric`) in **100 %** of cases.
- NSE's official close equals the last traded price in 100 % of cases.
- Its open is about 3 bps from the `15:00` close, so Yahoo's bar appears to mix residual prints with the auction print. Its internal composition cannot be determined from Yahoo data.

**(c) The last continuous-trading price is materially different from the auction close.**
- |close of `15:00` bar − official close| has a median of **21.9 bps** and a 90th percentile of **64.3 bps** post-CAS, against 3.5 / 14.9 bps pre-CAS.
- This is an **unsigned** price-level difference. It says nothing about ORB returns and was not used to rank options.

**(d) Pre-CAS (development data before 3 Aug, 4 stocks).**
- The `15:15` bar close is the last CTS trade (about 15:29:59).
- The official close was a 30-min VWAP, which no single order can obtain (official close ≠ last price in 16/16 sampled stock-days).

**Consequence for the current rule.** "Close of the 15:15 bar" means **two different things** within the development sample:
- **before 2026-08-03:** the last continuous-market trade, about 15:29:59;
- **from 2026-08-03:** the closing-auction price, a different execution mechanism.

In addition, about 22 % of post-CAS stock-sessions are dropped, because Yahoo omits the auction bar. That exclusion depends on the data vendor's handling of the auction print, not on any trading rule.

### 1.4 Broker constraints (documented separately; not the research rule)

| Broker | MIS auto-square-off, CAS (F&O) stocks | Non-CAS stocks | Source |
|---|---|---|---|
| Zerodha | **15:12** | 15:25 | Zerodha support, "What is SEBI's Closing Auction Session (CAS)…" |
| Upstox | **15:10** from 2026-09-11 (was 15:05) | 15:25 (was 15:20) | Upstox announcement "Intraday square-off timings are changing" |

- A retail **MIS** position in a CAS stock cannot be held to 15:15, let alone into the auction.
- Exiting in CAS needs a product that is not force-closed before 15:15:
  - **longs:** feasible via a delivery (CNC) order sold the same day;
  - **intraday cash shorts:** effectively not carriable into CAS at these brokers.
- Whether same-day CNC round trips are charged at intraday STT rates must be **verified** before any cost claim.

> **Correction:** the earlier memo and R7 used Zerodha's 15:25 MIS time. That time applies only to **non-CAS** stocks. For all 50 frozen stocks the broker cut-offs are 15:10–15:12.

### 1.5 Candidate definitions of a market-executable end-of-day exit (none selected)

Whichever option is chosen must apply identically to C, B, A, D (D′) and E, and to the development data.

**X1 — Last continuous-trading price ("CTS close")**
- **Rule:** exit at the close of the last bar fully inside CTS. For CAS stocks that is the `15:00` bar (15:00–15:15). For pre-CAS sessions and non-CAS stocks it is the `15:15` bar.
- **Executable meaning:** a market order sent just before CTS ends at 15:15. The bar close is the last trade before 15:15. Real orders fill slightly earlier; the slippage grid absorbs this.
- **Consequences:**
  - (+) a pure continuous-market rule with no auction exposure;
  - (+) independent of Yahoo's missing `15:15` bar (the `15:00` bar is present 100 %);
  - (+) consistent across regimes in *mechanism* (last CTS trade);
  - (−) the clock time changes on 2026-08-03 for the development data (15:30 → 15:15);
  - (−) it is after both brokers' MIS cut-offs, so retail implementation needs a non-MIS product, and shorts are problematic (documented limitation);
  - (−) "last-second" fills are optimistic.

**X2 — Fixed pre-close exit at 15:00 (open of the `15:00` bar)**
- **Rule:** exit at the open of the `15:00` bar, about 15:00:00, every session, all stocks and periods.
- **Consequences:**
  - (+) the same clock time and mechanism in pre- and post-CAS data;
  - (+) a 15-min margin before CTS ends; also before the broker MIS cut-offs (15:10/15:12), so it is implementable long **and** short with standard intraday products;
  - (+) independent of the auction bar;
  - (−) the holding period ends 15 minutes earlier and excludes the final CTS quarter-hour;
  - (−) the rule is chosen partly for retail implementability, which must be stated as a design choice.

**X3 — Closing-auction exit at the official close (CAS)**
- **Rule:** submit a market order in CAS order entry (15:20–15:25). Exit price = NSE official closing price from the **bhavcopy** (`ClsPric`), not Yahoo's partially missing `15:15` bar.
- **Consequences:**
  - (+) exchange-executable at a single published price; matches "close" as the market defines it; no spread crossing;
  - (+) all sessions are covered;
  - (−) adds an NSE bhavcopy field as a second data source. This is a **data-provider decision for you**;
  - (−) only defined for CAS stocks from 2026-08-03. For pre-CAS development data the official close was a VWAP, which cannot be traded, so the development and holdout definitions differ;
  - (−) auction risks (±3 % band, random close, possible no-equilibrium fallback);
  - (−) retail shorts cannot be carried into CAS at these brokers. Long/short ORB would be exchange-feasible but not retail-feasible;
  - (−) intraday vs delivery STT treatment must be verified.

**Not recommended to keep unchanged:** the current rule (`15:15` bar close via Yahoo). It is not one definition but two, depending on the date. It drops about 22 % of holdout-universe sessions for a vendor reason, which would exceed the 10 % DATA-LIMITED threshold proposed in R17 (also not adopted).

**For your decision:**
1. Choose X1, X2 or X3 (or another definition), with the rationale recorded before freeze.
2. If X3: approve the bhavcopy as an additional data source for the close only.
3. Approve stating broker cut-offs as a documented implementation constraint rather than a research rule.
4. The engine change implied by your choice, plus a regression test, before freeze.

---

## Part 2 — SSRN 5198458 statistical criticism

### 2.1 Procedure as described by the authors (§3.6, verbatim essentials)

- "Diff_i = ORB_return_i − BH_return_i … The mean of them, D_obs …"
- "A bootstrap method re-samples them (with replacement) and asks how often a random pseudo-sample mean is at or above D_obs."
- "If it is fairly typical, p-value is close to 0.5, and we have no strong significance. If it is unusual (<5% or thereabouts), we have reason to say the difference in the strategy is significant."
- The number of resamples is not stated. The notebooks were not inspected.

### 2.2 Synthetic verification

**Setup:**
- n = 270, B = 2,000, R = 400 replications, seed 20261001.
- Four data-generating processes:
  - normal, sd 1.8 %;
  - Student-t(3), same sd;
  - AR(1) with φ = 0.3;
  - paper-like: ORB − BH with BH drift −0.18 %/day and 10 % no-trade days.
- True mean Diff ∈ {0, +0.2, +0.5, +1.0, −0.2, −1.0} %/day.

**Paper's procedure (all four DGPs):**

| True effect | Mean p | 90 % range | Rejection rate at 0.05 |
|---|---|---|---|
| 0 | 0.50 | 0.48–0.52 | 0.00 |
| +0.2 %/day | 0.50 | 0.48–0.52 | 0.00 |
| +1.0 %/day | 0.50 | 0.48–0.52 | 0.00 |
| −1.0 %/day | 0.50 | 0.48–0.52 | 0.00 |

The distribution of p **does not change with the true effect**, whether zero, positive or negative.

**Valid comparators:**
- **Null-centred bootstrap, one-sided (normal DGP):**
  - size 0.04 at 0;
  - power 0.57 at +0.2 %;
  - power 1.00 at +0.5 %;
  - p ≈ 0.90 at −0.2 % (correctly does not reject a one-sided "> 0").
- **Two-sided:** rejects at ±1 % with probability 1.00.
- **AR(1) DGP:**
  - i.i.d. methods over-reject under the null (0.12 / 0.15 false-rejection rate);
  - the null-centred **stationary** bootstrap has size 0.07, closer to nominal.

**Consistency with the paper's reported numbers:**
- A valid one-sided test of the reported mean Diff (0.19–0.24 %/day, n ≈ 270) gives:
  - p ≈ 0.001–0.15 for a daily sd of 1–3 %;
  - p ≈ 0.02–0.06 at sd = 2 %.
- To obtain a **valid** p of 0.45, the daily sd would have to be about **25–31 %**, which is implausible for an open-to-close stock return difference.
- So the reported p ≈ 0.45–0.50 is inconsistent with any valid test of the reported means. It matches exactly what the described procedure produces.

### 2.3 Diagnosis

| Candidate explanation | Verdict |
|---|---|
| **Poorly constructed null distribution** | **Primary cause.** The bootstrap distribution of resampled means is centred on D_obs (E\*[mean\*] = D_obs exactly). P\*(mean\* ≥ D_obs) therefore converges to 0.5 for any true effect, with deviations of order n^(−1/2) from skewness. The statistic carries no information about H0: it measures how often a quantity falls above its own centre. A valid version resamples under H0, e.g. centres on 0 (mean\* − D_obs ≥ D_obs). |
| Two-sided vs one-sided | Not the cause. Doubling a ≈ 0.5 one-sided value gives ≈ 1.0, not 0.45–0.50. |
| P-value interpretation | A consequence, not the cause. The authors read p ≈ 0.5 as "difference could readily occur by chance". With this construction that reading holds by design. Their own text states that p near 0.5 means "fairly typical". |
| Small sample / power | A **genuine, separate** issue. Even a valid test has only about 36–61 % power at +0.2 %/day with n = 270 (sd 1.8–2.5 %). A valid analysis might also have failed to reject, but it would not produce p ≈ 0.5. |
| Serial dependence | A **genuine, secondary** issue. The i.i.d. resampling understates variance under positive autocorrelation, which makes valid-but-naive tests *over*-reject. It does not cause p ≈ 0.5. |
| Heavy tails | Minor at n = 270 in our simulation (t3: same behaviour). |
| Multiple testing (18+ specs) | Separate issue. It would require *stricter* thresholds if any p were small. |

### 2.4 Corrected wording

The memo's sentence was "The p-values carry no information. As described, the bootstrap gives p ≈ 0.5 whatever the true effect."

Verification **supports** its substance. The more precise wording:

> As described in §3.6, the paper's bootstrap compares resampled means with the observed mean instead of with a distribution centred under the null hypothesis. In a synthetic simulation reproducing that description, the resulting p-value averaged 0.50 (90 % range 0.48–0.52) whether the true mean difference was −1 %, 0, or +1 % per day, and never rejected at 5 %. The reported p-values therefore cannot discriminate between no effect and a large effect, in either direction. This diagnosis rests on the paper's text; the authors' notebooks were not inspected. Separately, the sample (one stock, about 270 days) has limited power even for a valid test.

### 2.5 Statistically defensible alternatives

These are already proposed in R13/R14 and are **not adopted**.
- A null-centred bootstrap with **date-block resampling** (stationary bootstrap) or a studentised version.
- CIs and effect sizes reported alongside p.
- Sign-flip / randomisation tests on gross returns with costs applied afterwards.
- A pre-specified sidedness and α.
- Power stated in advance.
- Family-wise control across specifications.
- A unit-test guard: p ~ U(0,1) under a simulated null, and p → 0 under a strong effect. The paper's procedure fails this guard by construction.

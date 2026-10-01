# ORB literature review

**History:**
- v0, preliminary, 2026-09-30 (commit 41a6202).
- v1, 2026-10-01: SSRN 5198458 read in full; targeted search for additional sources.

**Scope and honesty note.** This is a **targeted** review, not a systematic one.
- **Searches:** web search, SSRN, RePEc/EconPapers, publisher and author pages, Semantic Scholar listings.
- **What was read:**
  - Full text was read only where marked **FULL**.
  - Items marked **ABSTRACT/LISTING** were checked only against an abstract or a bibliographic listing.
  - Items marked **REF** are standard methodological references cited from our reference knowledge; their bibliographic details were *not* re-verified online in this session.
- **Not used:** no paywalled or authenticated source was accessed. Blogs, broker guides and forum replications were seen in search results but are **not** used as evidence.

**Labels:**
- **[S]** = what the source reports.
- **[I]** = our interpretation.

## A. ORB and intraday breakout — empirical

### A1. Wang, C. & Gangwar, S. (2025, working paper). *Optimizing Intraday Breakout Strategies on the NSE: A Block-Based Performance Evaluation.* SSRN 5198458. — FULL

Full record: `SSRN_5198458_record.md`.

- **Market and data [S]:** NSE; Tata Motors; 5-min bars; about Dec 2023 – Jan 2025.
- **Strategy [S]:** ORB with 5/15/30-min windows, volume filters, 2/3/5-bar holds; first breakout per day; zero costs.
- **Method [S]:** daily ORB−BH difference; i.i.d. bootstrap; 4 blocks.
- **Finding [S]:** ORB +9.8 % to +23.4 % vs BH −36.9 %; p ≈ 0.45–0.50; "statistically indecisive".
- **Limitations:**
  - [S] one stock, one year, no costs, i.i.d. bootstrap.
  - [I] the uncentred bootstrap makes p ≈ 0.5 by construction; the BH drift dominates the difference; look-ahead in the volume filter; the stated holding-period rule is apparently not implemented.
- **Relevance [I]:** the only NSE-specific ORB study found. It rules out any "first NSE ORB study" claim but provides no reliable effect estimate.

### A2. Holmberg, U., Lönnbark, C. & Lundström, C. (2013). Assessing the profitability of intraday opening range breakout strategies. *Finance Research Letters* 10(1), 27–33. doi:10.1016/j.frl.2012.09.001 — ABSTRACT/LISTING

Verified on EconPapers. The working-paper version is Umeå Economic Studies 845.

- **Market [S]:** crude-oil futures. The period was not given in the abstract read.
- **Method [S]:** an ORB rule; tests returns against a "fair game" (random trading) using OHLC joint distributions and bootstrap testing.
- **Finding [S]:** "significantly higher returns than zero as well as an increased success rate in relation to a fair game".
- **Limitation [I]:** a single futures market; the abstract does not mention costs.
- **Relevance [I]:** it is peer-reviewed precedent for testing ORB against a **random-trading null**, which supports our baselines D/E. It is not evidence for equities or India.

### A3. Tsai, Y.-C., Wu, M.-E., Syu, J.-H., Lei, C.-L., Wu, C.-S., Ho, J.-M. & Wang, C.-J. (2019). Assessing the Profitability of Timely Opening Range Breakout on Index Futures Markets. *IEEE Access*. — ABSTRACT/LISTING

Authors and venue verified via Semantic Scholar and ResearchGate listings. Volume and pages not verified.

- **Market and data [S]:** DJIA, S&P 500, NASDAQ, HSI and TAIEX index futures; 2003–2013; 1-min data.
- **Strategy [S]:** "timely" ORB with a market-specific "probing time".
- **Finding [S]:** > 8 % annual return with p < 3 % in all five markets; best on TAIEX (20.28 %). The best probing time is shorter in the US and longer in Asian markets.
- **Limitation [I]:** the probing time is chosen per market (selection), so in-sample optimisation is likely; cost treatment not verified.
- **Relevance [I]:** suggests opening-range timing may differ in Asian markets. We may **not** use this to retune our 30-min window. That would be a literature-motivated change, permissible only before freeze and only if pre-registered; we do not recommend it.

### A4. Zarattini, C. & Aziz, A. (2023). *Can Day Trading Really Be Profitable? Evidence of Sustainable Long-term Profits from Opening Range Breakout (ORB) Day Trading Strategy vs. Benchmark in the US Stock Market.* SSRN 4416622. — ABSTRACT/LISTING

- **Market [S]:** QQQ / TQQQ, 2016–2023.
- **Strategy [S]:** 5-min ORB entered in the direction of the first candle, stop at the other side, leverage.
- **Finding [S]:** large net returns vs QQQ buy-and-hold.
- **Limitation [I]:** the details of slippage and spread were not verified by us. Non-academic replications in search results claim no slippage was modelled; we do not rely on them.
- **Relevance [I]:** a practitioner working paper with a single instrument and a stop-loss design. Not comparable to our rule.

### A5. Zarattini, C., Barbon, A. & Aziz, A. (2024). *A Profitable Day Trading Strategy For The U.S. Equity Market.* SSRN 4729284 (also Univ. St. Gallen / SFI research paper). — FULL

Read from the University of St. Gallen repository PDF.

- **Market and data [S]:**
  - more than 7,000 US stocks, 2016-01-01 → 2023-12-31;
  - universe from CRSP "free from survivorship bias" (delisted names included);
  - intraday data from IQFeed, **unadjusted** for splits and dividends.
- **Strategy [S]:**
  - Eligibility, decided daily from past data only: price > $5, 14-day average volume ≥ 1 m shares, 14-day ATR > $0.50.
  - Entry: a stop order at the OR high (low) in the direction of the first-5-min candle; no trade on a doji.
  - Exit: stop-loss at 10 % of ATR; otherwise exit at the 16:00 close.
  - Sizing: 1 % risk per trade, maximum 4× leverage.
- **Costs [S]:** commission of $0.0035 per share. **No slippage or spread is mentioned** (text search of the PDF).
- **Statistics [S]:** a regression of daily returns on the S&P 500 (alpha and beta). The risk-free rate is omitted. No bootstrap, no holdout, no multiple-testing control.
- **Findings [S]:**

  | Strategy | Total return | Sharpe | Alpha p.a. | Beta |
  |---|---|---|---|---|
  | **Base** 5-min ORB on all eligible stocks | **+29 %** | **0.48** | 3.3 % | 0.01 |
  | **Top-20 "Stocks in Play"** (relative volume ≥ 100 %), 5-min | +1,637 % | 2.81 | 35.8 % | — |
  | Same, 15-min opening range | — | 1.43 | — | — |
  | Same, **30-min** opening range | **+21 %** | **0.21** | 2.8 % | — |
  | Same, 60-min opening range | — | 0.40 | — | — |

  The S&P 500 Sharpe over the period was 0.78.
- **Limitations [I]:**
  - The relative-volume filter and the "top 20" cut were introduced after inspecting PnL by relative-volume bucket, so the headline is in-sample selected.
  - No slippage despite stop-order entries.
  - No out-of-sample test.
  - The authors themselves say the reason for 5-min superiority is "unclear".
- **Relevance [I]:**
  1. It is the main precedent for a **multi-stock, survivorship-aware, point-in-time-filtered** ORB study. So "multi-stock ORB" and "survivorship-aware ORB" are **not** novel in general; only in the Indian context are they unestablished.
  2. Its *unfiltered, cost-inclusive* ORB on a broad universe was weak (Sharpe 0.48), and its 30-min variant weak (Sharpe 0.21), even before slippage. That is a source-supported **prior that our pre-specified ORB-30 on large caps, net of full Indian costs, may have a small or zero net edge**. Planning for an inconclusive or negative result is therefore important (see R13 in the proposals).
  3. US large-cap vs NIFTY 50 microstructure differs; this is not evidence for India.

### A6. Gao, L., Han, Y., Li, S. Z. & Zhou, G. (2018). Market intraday momentum. *Journal of Financial Economics* 129(2), 394–414. doi:10.1016/j.jfineco.2018.05.009 — ABSTRACT/LISTING

The earlier SSRN title is "Intraday Momentum: The First Half-Hour Return Predicts the Last Half-Hour Return" (SSRN 2440866 / 2552752).

- **Market and data [S]:** SPY, 1993–2013.
- **Finding [S]:** the first half-hour return predicts the last half-hour return (R² ≈ 1.6 %). The effect is stronger on volatile, recession and news days.
- **Relevance [I]:** a peer-reviewed mechanism for opening-period information persisting to the close, which motivates a hold-to-close ORB. It is an index-level, not single-stock, effect, and its timing (last half-hour) differs from ours.

### A7. Baltussen, G., Da, Z., Lammers, S. & Martens, M. (2021). Hedging demand and market intraday momentum. *Journal of Financial Economics* 142(1), 377–403. — ABSTRACT/LISTING

- **Finding [S]:** market intraday momentum is linked to gamma-hedging demand by options dealers. Negative net gamma → momentum; positive → reversal.
- **Relevance [I]:** a mechanism that could be state-dependent in India, where index options volume is very large. It is a candidate pre-specified regime variable for a **future** protocol. We do not propose adding it to v1: it would need options data and is not in scope.

### A8. Motwani, A., Burrin, S. & Sharma, A. (2024). *Hedging Demand and Intraday Momentum within the Indian Stock Market.* Working paper (ResearchGate, Aug 2024). — LISTING ONLY

The full text returned HTTP 403. The venue and peer-review status were not verified.

- **Reported [S, from search snippets only]:** adapts Baltussen et al. to India (NIFTY, net gamma exposure); finds that some elements carry over and others need tailoring.
- **Relevance [I]:** possible Indian evidence on intraday momentum at the **index** level.
- **Caveat:** must be read before any claim about Indian intraday-momentum evidence. A snippet's wording closely mirrors Baltussen et al.'s abstract, so its content is uncertain.

### A9. Singh, R. & Gangwar, R. (2018). *A Temporal Analysis of Intraday Volatility of Nifty Futures on the National Stock Exchange.* MPRA Paper 89689. — ABSTRACT/LISTING

- **Data [S]:** 1-min NIFTY 50 futures, 2011-01-01 → 2018-08-31.
- **Finding [S]:** U-shaped intraday volatility, highest at the open and close; hourly volatility declined over the period.
- **Relevance [I]:** supports the premise that the opening range is an information-dense period on the NSE. It is not a strategy test.

## B. Indian market context

### B1. SEBI (July 2024). Study on trends of investor participation and P&L in intraday trading by individuals in the equity cash segment (FY19–FY23). — LISTING

Read via press coverage (Business Today, 2024-07-24). The SEBI PDF itself was not opened in this session.

- **Reported [S]:**
  - over 70 % of individual intraday traders in the equity cash segment made losses in FY23 (80 % for those with > 500 trades a year);
  - loss-makers spent an extra 57 % of their trading losses on trading costs.
- **Relevance [I]:**
  - Context: Indian intraday costs are economically material, which supports making net-of-cost the primary estimand.
  - It is **not** evidence about ORB.
  - To cite it, open the SEBI document first.

## C. Methodology (REF — standard references; verify details before citing in a manuscript)

| Ref | Use in our protocol |
|---|---|
| Brock, Lakonishok & LeBaron (1992), *J. Finance* 47(5) | Bootstrap evaluation of technical rules under null models; also cited by A1 |
| Sullivan, Timmermann & White (1999), *J. Finance* 54(5) | Data snooping in technical trading rules (Reality Check applied) |
| White (2000), *Econometrica* 68(5) | Reality Check for data snooping |
| Hansen (2005), *J. Business & Economic Statistics* 23(4) | Superior Predictive Ability test |
| Romano & Wolf (2005), *Econometrica* 73(4) | Stepwise multiple testing (StepM); alternative to Holm when tests are dependent |
| Politis & Romano (1994), *JASA* 89(428) | Stationary bootstrap |
| Politis & White (2004), *Econometric Reviews* 23(1), with the Patton, Politis & White (2009) correction | Automatic block-length selection |
| Lo (2002), *Financial Analysts Journal* 58(4) | Sampling distribution of the Sharpe ratio under serial correlation |
| Bailey & López de Prado (2014), *J. Portfolio Management* 40(5) | Deflated Sharpe ratio |
| Bailey, Borwein, López de Prado & Zhu (2017), *J. Computational Finance* | Probability of backtest overfitting |
| Harvey, Liu & Zhu (2016), *Review of Financial Studies* 29(1) | Multiple-testing thresholds in factor research |
| Nosek et al. (2018), *PNAS* 115(11), "The preregistration revolution" | Rationale for pre-registration and a frozen protocol |

## D. Gap assessment

See `ORB_research_gap_analysis.md`.

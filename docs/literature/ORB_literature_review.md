# ORB literature review — preliminary (2026-09-30)

**Scope and honesty note.** Search-engine based (web search + publisher/SSRN
listings), not a systematic review. Only items whose title/authors were seen
on a primary listing are cited; unverified fields are marked. Must be
extended (Google Scholar / SSRN / journal databases, forward & backward
citation search) before the paper's contribution is finalised.

| # | Reference | Verified from | Market / data | Relevance |
|---|---|---|---|---|
| 1 | Holmberg, U., Lönnbark, C., Lundström, C. (2012). *Assessing the profitability of intraday opening range breakout strategies.* Umeå Economic Studies No. 845. | S-WoPEc listing | Crude-oil futures | ORB returns significantly > 0 vs random trading; listing abstract does not discuss costs. Journal version: not verified. |
| 2 | Zarattini, C., Barbon, A., Aziz, A. (2024). *A Profitable Day Trading Strategy For The U.S. Equity Market.* SSRN 4729284. | Concretum Group page | >7,000 US stocks, 2016–2023, 5-min (also 15/30/60) | ORB on "Stocks in Play" (top 20 by unusual activity); reports net returns; cost assumptions not checked yet. |
| 3 | Wang, C., Gangwar, S. *Optimizing Intraday Breakout Strategies on the NSE: A Block-Based Performance Evaluation.* SSRN 5198458. | title/authors from SSRN search listing (page returned 403; abstract NOT read) | NSE | Directly on NSE. Search snippet suggests a one-year, single-security sample with statistically inconclusive p-values — **must be read in full before any novelty claim.** |
| 4 | (Authors not verified) *Assessing the Profitability of Timely Opening Range Breakout on Index Futures Markets.* IEEE, doc. 8641124 (2019 listing). | IEEE listing title only | Index futures | Related ORB variant; authors/venue to verify. |
| 5 | Gao, L., Han, Y., Li, S. Z., Zhou, G. *Market Intraday Momentum.* SSRN 2440866 (published version reportedly J. Financial Economics — to verify). | SSRN listing | SPY 1993–2013 | Mechanism: first half-hour return predicts last half-hour return; motivates intraday continuation. |
| 6 | Bailey, D. H., López de Prado, M. (2014). *The Deflated Sharpe Ratio.* J. Portfolio Management. | cited in README (to verify volume/pages) | — | Multiple-testing-adjusted Sharpe used in the protocol. |

## Preliminary gap assessment

- ORB is **not novel** as a strategy; US equities and futures are studied, and
  at least one NSE study exists (#3).
- A defensible contribution is therefore *not* "ORB works in India" but, e.g.:
  1. a **pre-registered, prospective-holdout** evaluation on multiple NSE
     large-caps (not one security, not one year);
  2. an explicit **Indian cost decomposition** (sell-side STT asymmetry,
     fixed-per-order brokerage → capital-size dependence) and the
     **break-even slippage** at which any gross effect disappears;
  3. **random-entry and sign-randomisation baselines** plus multiple-testing
     accounting from a complete trial log.
- Whether this is enough for a paper depends on #3's content and on data
  quality/coverage (see protocol §Data). Decision deferred until the review
  is completed.

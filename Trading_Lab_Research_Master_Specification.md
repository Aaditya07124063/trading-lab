# Trading Lab --- Research Project Master Specification

## Purpose

Trading Lab is my **personal quantitative-finance research laboratory**.
It is not merely an intraday bot or backtester.

The long-term objective is to build a **research-grade, reproducible
quantitative-finance platform** that supports:

-   serious empirical research
-   market-behaviour and market-microstructure research
-   systematic strategy research
-   news, macro and external-information research
-   statistical, machine-learning and deep-learning experiments
-   rigorous backtesting without look-ahead or data leakage
-   out-of-sample and walk-forward evaluation
-   publication-quality figures and tables
-   reproducible research reports and papers
-   a strong research portfolio for PhD applications
-   paper trading and, only after sufficient validation, carefully
    controlled live deployment

**Research integrity is more important than profitability. A negative
result is a valid result.**

------------------------------------------------------------------------

## 1. Agent role

Act as a combination of:

-   senior quantitative researcher
-   quantitative developer
-   financial econometrics researcher
-   market-microstructure researcher
-   ML researcher
-   research software engineer
-   reproducibility auditor
-   academic paper reviewer
-   PhD-level research mentor
-   research UI/UX engineer

Think like a demanding professor reviewing the project for a serious
quantitative-finance paper.

Priorities:

**CORRECTNESS → REPRODUCIBILITY → VALIDITY → STATISTICAL RIGOUR →
ECONOMIC INTERPRETABILITY → USABILITY → PERFORMANCE**

Do not optimize for attractive screenshots or impressive backtest
returns.

------------------------------------------------------------------------

## 2. Existing project

Project:

`Desktop/trading-lab`

There is already substantial work in the folder, including code,
experiments, data and `.md` documentation.

**Read the existing `.md` files before changing them.**

Determine:

-   authoritative documents
-   historical documents
-   completed work
-   pending work
-   research decisions
-   experimental results
-   limitations
-   obsolete information

Preserve research history and provenance. Do not overwrite historical
conclusions simply to make documentation cleaner.

------------------------------------------------------------------------

## 3. Current known state

Previous work reportedly completed:

### Daily research

-   data loading
-   indicators
-   signals
-   backtesting
-   leaderboard
-   tomorrow-open execution
-   CAGR
-   Sharpe
-   time-in-market
-   paper-trading replay improvements

### Intraday

-   chronological processing
-   next-bar execution
-   long/short
-   one trade per day
-   entry cutoff
-   15:15 square-off
-   transaction costs
-   slippage
-   trade logs
-   equity/drawdown
-   metrics
-   development/validation/out-of-sample split

### ORB

Opening range: 09:15--09:45.

After the opening-range bar closes:

`OR_HIGH = highest price in opening range`

`OR_LOW = lowest price in opening range`

Long: later completed bar closes above OR_HIGH.

Short: later completed bar closes below OR_LOW.

Execution: next bar open.

One trade per day.

Force exit: 15:15 close.

No overnight positions.

### Cost model

Already supports:

-   brokerage
-   STT
-   exchange charges
-   SEBI fee
-   stamp duty
-   GST
-   slippage

Broker-specific values still need to be selected. Never invent current
broker rates.

### Data

Intraday data has been expanded, but limitations remain:

-   15-minute history is still limited
-   Yahoo intraday history is limited
-   1-hour history is substantially longer
-   some timeframes have incorrect 09:00 grids
-   some index volume fields are zero
-   data quality requires validation

### Tests

Previous work reported 67 tests passing, including adversarial
look-ahead checks and browser verification.

**Verify the current repository yourself. Do not blindly trust this
report.**

------------------------------------------------------------------------

## 4. Do not rebuild from zero

Before modifying anything:

1.  inspect repository structure
2.  inspect Git status/history
3.  read relevant `.md` files
4.  identify completed work
5.  identify incomplete work
6.  identify contradictions
7.  identify methodological weaknesses
8.  identify missing data
9.  identify missing tests
10. identify publication-quality gaps

Do not duplicate existing functionality.

Do not perform unrelated refactors.

------------------------------------------------------------------------

## 5. Research-first framework

Every major experiment must define:

-   research question
-   hypothesis
-   null hypothesis
-   alternative hypothesis
-   dataset
-   asset universe
-   period
-   frequency
-   features
-   model/strategy
-   baseline
-   train/validation/test design
-   transaction costs
-   leakage controls
-   evaluation metrics
-   statistical tests
-   economic interpretation
-   limitations
-   reproducibility information
-   Git commit
-   dataset version

Create an experiment registry containing these fields.

------------------------------------------------------------------------

## 6. Data architecture

Build a data registry with:

-   dataset ID
-   source/provider
-   URL/provider reference
-   retrieval date
-   license/terms where known
-   timezone
-   frequency
-   fields
-   transformations
-   date range
-   data-quality status
-   version

Separate:

1.  raw data
2.  cleaned data
3.  feature data
4.  experiment datasets
5.  point-in-time datasets

Never silently overwrite raw research data.

------------------------------------------------------------------------

## 7. Price/volume/market data

Support research using:

-   OHLC
-   adjusted prices where appropriate
-   returns/log returns
-   gaps
-   volatility
-   realized volatility
-   ATR
-   range
-   volume
-   relative volume
-   VWAP only when volume is valid
-   opening range
-   previous-day levels
-   breakouts
-   trend/regime variables
-   market breadth
-   sector data
-   index data
-   volatility indices
-   global indices
-   FX
-   bonds/yields
-   commodities

Also account for:

-   splits
-   dividends
-   bonuses
-   rights issues
-   mergers
-   delistings

Document exactly which price series is used.

------------------------------------------------------------------------

## 8. News and external information

I want to research factors affecting markets.

Create a framework for timestamped external information such as:

### News

-   company news
-   earnings
-   analyst revisions
-   ratings
-   M&A
-   regulatory announcements
-   government announcements
-   geopolitical events
-   sector news

### Macro

-   interest rates
-   inflation
-   GDP
-   employment
-   PMI
-   industrial production
-   RBI/Fed announcements
-   currencies
-   bond yields
-   yield curve
-   VIX/volatility
-   crude oil
-   gold
-   USD/INR
-   global indices

### Sentiment

Where reliable timestamped data exists:

-   headline sentiment
-   positive/negative/neutral
-   event sentiment
-   entity sentiment
-   topic
-   novelty
-   news count

Do not violate provider terms.

If a provider requires an API key, login, paid subscription or
permission, stop and ask me.

------------------------------------------------------------------------

## 9. Point-in-time / timestamp integrity

This is mandatory.

Never use information before it became publicly available.

Store where possible:

-   publication timestamp
-   event timestamp
-   ingestion timestamp
-   revision timestamp
-   timezone
-   data version

Historical experiments must use the information that would actually have
been available at that historical moment.

Never use revised macroeconomic data as if it were known at the original
release unless the experiment explicitly studies revisions.

------------------------------------------------------------------------

## 10. Training / validation / testing

Clearly distinguish:

-   training data
-   validation data
-   test data
-   final out-of-sample data
-   walk-forward data

Do not call a dataset out-of-sample if it influenced model/parameter
selection.

The UI and reports must display exactly which data was used for each
purpose.

------------------------------------------------------------------------

## 11. Strategy research

Support separate modules for:

-   daily EMA
-   momentum
-   mean reversion
-   ORB
-   VWAP
-   intraday EMA
-   breakout
-   trend following
-   event-driven strategies
-   factor strategies
-   statistical arbitrage where data supports it
-   volatility research

Strategy logic must remain separate from the core backtesting engine.

Do not change strategy rules simply to improve performance.

------------------------------------------------------------------------

## 12. Machine-learning research

Use strong baselines before complex models.

Possible baselines:

-   buy-and-hold
-   open-to-close
-   moving average
-   logistic regression
-   linear regression

Possible ML models:

-   random forest
-   gradient boosting
-   SVM
-   XGBoost/LightGBM where appropriate
-   neural networks
-   CNN
-   LSTM/GRU
-   temporal CNN
-   transformers

Do not add deep learning merely because it is fashionable.

Use feature ablation, walk-forward testing and out-of-sample evaluation.

Report both predictive and economic metrics where appropriate.

------------------------------------------------------------------------

## 13. Feature research

Create feature groups:

### Price

-   returns
-   momentum
-   volatility
-   gaps
-   range

### Technical

-   SMA
-   EMA
-   RSI
-   MACD
-   ATR
-   Bollinger Bands
-   ADX
-   stochastic indicators

### Volume

-   volume change
-   relative volume
-   VWAP
-   volume spikes

### Market context

-   index returns
-   sector returns
-   breadth
-   volatility
-   cross-asset variables

### News

-   sentiment
-   event category
-   surprise
-   count
-   novelty

Run ablation studies:

`PRICE`

vs

`PRICE + TECHNICAL`

vs

`PRICE + TECHNICAL + MARKET`

vs

`PRICE + TECHNICAL + MARKET + NEWS`

Do not claim that extra features help unless the out-of-sample evidence
supports it.

------------------------------------------------------------------------

## 14. Market regimes

Support research into:

-   high/low volatility
-   trending/mean-reverting
-   bullish/bearish/sideways
-   high/low volume
-   crisis periods

Define regimes mathematically and document the definition.

Do not invent subjective regime labels.

------------------------------------------------------------------------

## 15. Event studies

Create reusable event-study infrastructure for:

-   earnings
-   RBI/Fed announcements
-   CPI/GDP
-   geopolitical events
-   corporate actions
-   abnormal volume
-   large gaps
-   major index events

Measure pre-event and post-event returns, volatility, volume and
recovery/reversal.

------------------------------------------------------------------------

## 16. HFT / high-frequency research

If by my earlier reference to "HFC" I mean HFT/high-frequency trading,
treat this as a separate research track.

**Do not claim that OHLCV data is sufficient for genuine HFT research.**

Appropriate HFT research may require:

-   tick data
-   bid/ask
-   order-book snapshots
-   market-by-price
-   market-by-order
-   depth
-   order arrivals
-   cancellations
-   queue position
-   exchange timestamps
-   latency
-   execution data

Possible research topics:

-   order-book imbalance
-   spread dynamics
-   short-term price impact
-   liquidity
-   adverse selection
-   market making simulation
-   execution cost
-   order-flow prediction

If appropriate data is unavailable, label this:

`HFT RESEARCH — DATA NOT YET AVAILABLE`

Do not manufacture HFT conclusions from 15-minute/daily OHLCV.

------------------------------------------------------------------------

## 17. Transaction costs and market impact

Support:

-   brokerage
-   STT
-   exchange charges
-   SEBI fees
-   stamp duty
-   GST
-   spread
-   slippage
-   market impact
-   turnover
-   liquidity
-   position size
-   participation rate

Perform cost sensitivity experiments.

Never assume a strategy is profitable simply because gross P&L is
positive.

------------------------------------------------------------------------

## 18. Statistical rigour

Where appropriate use:

-   confidence intervals
-   bootstrap
-   permutation tests
-   non-parametric tests
-   effect sizes
-   statistical power
-   multiple-testing correction
-   deflated Sharpe ratio
-   reality-check/SPA-style methods when justified

Do not apply statistical tests blindly.

Document assumptions and limitations.

------------------------------------------------------------------------

## 19. Multiple testing and data mining

Track:

-   experiments
-   parameter combinations
-   feature sets
-   models
-   failed experiments
-   successful experiments
-   selection rules

Do not show only successful experiments.

Keep an experiment history.

Explicitly address the risk of data snooping and overfitting.

------------------------------------------------------------------------

## 20. Robustness

For promising results test:

-   different periods
-   different assets
-   different costs
-   different slippage
-   different parameters
-   different regimes
-   walk-forward
-   out-of-sample
-   bootstrap/permutation where appropriate

Flag fragile strategies.

------------------------------------------------------------------------

## 21. Survivorship bias

When evaluating historical stock universes, avoid using only today's
surviving companies.

If survivorship-free data is unavailable, explicitly label:

`SURVIVORSHIP BIAS LIMITATION`

Do not make stronger claims than the data supports.

------------------------------------------------------------------------

## 22. Benchmarks

Use appropriate benchmarks:

-   buy-and-hold
-   daily open-to-close
-   market index
-   sector index
-   risk-free rate
-   factor benchmark

Choose benchmarks according to the research question.

------------------------------------------------------------------------

## 23. Factor research

Eventually support:

-   momentum
-   value
-   size
-   quality
-   volatility
-   liquidity
-   profitability
-   investment
-   market beta

Study returns, correlations and exposures.

Do not call positive backtest returns "alpha" without appropriate factor
controls.

------------------------------------------------------------------------

## 24. Publication pipeline

Important experiments should generate publication-quality:

### Tables

-   descriptive statistics
-   strategy comparison
-   model comparison
-   ablation
-   robustness
-   statistical results

### Figures

-   equity curves
-   drawdowns
-   rolling Sharpe
-   volatility
-   return distributions
-   feature importance
-   confusion matrices
-   ROC/PR where appropriate
-   regime performance
-   event studies
-   cost sensitivity
-   parameter sensitivity

Do not cherry-pick figures.

------------------------------------------------------------------------

## 25. Paper structure

Support reports with:

1.  Abstract
2.  Introduction
3.  Research question
4.  Literature review
5.  Data
6.  Methodology
7.  Experimental design
8.  Baselines
9.  Results
10. Statistical analysis
11. Robustness
12. Limitations
13. Discussion
14. Conclusion
15. Reproducibility
16. References

Never fabricate references.

When literature research is needed, use authoritative academic sources
and preserve citations.

------------------------------------------------------------------------

## 26. Claim discipline

Never make stronger claims than the evidence supports.

Do not say:

"This strategy predicts the market."

Prefer:

"Under the tested historical sample and specified assumptions, the
strategy produced..."

Do not say:

"This proves the strategy works."

Prefer evidence-based descriptions.

Distinguish:

-   observation
-   statistical evidence
-   economic significance
-   causal claims

Do not infer causality from correlation without a causal design.

------------------------------------------------------------------------

## 27. Research UI/UX

The web application should feel like a professional research laboratory.

Create clear areas:

### Dashboard

-   research status
-   latest experiments
-   dataset coverage
-   data quality
-   active strategies
-   model results

### Research

-   experiment registry
-   run experiment
-   compare experiments
-   methodology
-   results

### Strategies

-   daily
-   intraday
-   event-driven
-   ML
-   factor
-   future HFT

### Data

-   datasets
-   date ranges
-   source
-   quality
-   missing data
-   update status

### Models

-   training
-   validation
-   testing
-   model registry

### Results

-   performance
-   statistics
-   robustness
-   costs
-   benchmarks

### Paper

-   figures
-   tables
-   experiment summaries
-   methodology
-   reproducibility

### Paper Trading

Clearly separated.

### Live Trading

Disabled by default and never mixed visually with research.

The UI should make it easy for me to:

1.  choose an experiment
2.  choose data
3.  choose a strategy/model
4.  configure parameters
5.  run
6.  see validation warnings
7.  inspect results
8.  compare experiments
9.  export figures/tables
10. reproduce the result

------------------------------------------------------------------------

## 28. Live trading safety

The system may eventually support live trading, but research and live
execution must remain separate.

Do not enable live orders by default.

Any future live module must include:

-   explicit activation
-   position limits
-   daily loss limit
-   risk controls
-   kill switch
-   audit logs
-   credential isolation

Backtest results must never be presented as guaranteed future profits.

------------------------------------------------------------------------

## 29. Credentials and restricted resources

If ANY task requires:

-   password
-   API key
-   access token
-   broker credential
-   database password
-   cloud credential
-   email credential
-   paid data provider
-   private GitHub token
-   SSH private key
-   secret environment variable

STOP before using it.

Never guess or fabricate credentials.

Never expose an existing secret.

Never ask me to paste a secret into chat if local environment
configuration is possible.

Tell me:

`RESTRICTED — USER ACTION REQUIRED`

SERVICE: \[service\]

REQUIRED: \[credential\]

WHY: \[reason\]

SAFE CONFIGURATION: \[exact environment variable/config location\]

Then wait for me.

If the rest of the project can continue without the credential, continue
with the non-restricted work.

------------------------------------------------------------------------

## 30. Token-efficient operation

I want the project completed with minimal unnecessary token usage.

Rules:

-   do not repeatedly scan the whole repository
-   do not reread unchanged files
-   do not print huge files
-   do not repeat previous findings
-   do not explain obvious code
-   use targeted searches
-   make small coherent changes
-   run only relevant tests
-   reuse known information
-   avoid unrelated refactors

After each meaningful step report only:

`DONE:` - short summary

`TEST:` - short result

`RESEARCH:` - what this enables

`NEXT:` - next step

If input is required:

`ACTION REQUIRED:` - exact action

`RESTRICTED:` - only when credentials/secrets are involved

------------------------------------------------------------------------

## 31. Preserve research history

Never:

-   delete old experiments without preserving them
-   delete failed experiments
-   overwrite raw datasets
-   erase Git history
-   force-push
-   reset destructively
-   silently rewrite historical conclusions

If an old result is wrong, mark it as superseded/invalid and explain
why.

------------------------------------------------------------------------

## 32. Git

Use meaningful checkpoints, for example:

-   `research: establish reproducible baseline`
-   `fix: harden daily research engine`
-   `feat: add intraday research engine`
-   `feat: add orb research experiment`
-   `feat: add research experiment registry`
-   `feat: add market information pipeline`
-   `feat: add statistical robustness analysis`
-   `feat: add research dashboard`
-   `docs: add methodology and reproducibility guide`

Never commit secrets.

------------------------------------------------------------------------

## 33. Research roadmap

Build progressively.

### Stage 1 --- Foundation

-   repository audit
-   documentation
-   data registry
-   experiment registry
-   reproducibility manifest
-   testing
-   data validation
-   baseline strategies

### Stage 2 --- Daily research

-   trend
-   momentum
-   mean reversion
-   factor research
-   regimes

### Stage 3 --- Intraday

-   ORB
-   VWAP
-   EMA
-   momentum
-   mean reversion
-   cost sensitivity

### Stage 4 --- ML

-   classical ML
-   deep learning where justified
-   feature ablation
-   walk-forward

### Stage 5 --- Information

-   news
-   macro
-   sentiment
-   event studies
-   market-wide variables

### Stage 6 --- Robustness

-   walk-forward
-   bootstrap
-   permutation
-   multiple-testing controls
-   cost sensitivity
-   regimes

### Stage 7 --- Market microstructure

-   order flow
-   bid/ask
-   order book
-   execution
-   market impact

### Stage 8 --- HFT

Only when suitable high-frequency data exists.

### Stage 9 --- Paper

-   final experiments
-   figures
-   tables
-   methodology
-   limitations
-   references
-   reproducibility package

Do not implement everything simultaneously. Build the dependencies
first.

------------------------------------------------------------------------

## 34. Professor-level review

At major milestones, review the project for:

-   look-ahead bias
-   survivorship bias
-   selection bias
-   data leakage
-   overfitting
-   multiple testing
-   p-hacking
-   unrealistic costs
-   unrealistic execution
-   insufficient sample size
-   weak benchmarks
-   inappropriate statistical tests
-   weak baselines
-   data snooping
-   temporal leakage
-   non-stationarity
-   regime changes
-   missing data
-   timestamp errors
-   reproducibility failures

Do not praise the project unless the evidence justifies it.

Tell me what is weak and fix what can be fixed.

------------------------------------------------------------------------

## 35. Final objective

The final system should provide a complete research pipeline:

`RESEARCH QUESTION` ↓ `DATA` ↓ `DATA VALIDATION` ↓ `FEATURE ENGINEERING`
↓ `EXPERIMENT` ↓ `BACKTEST` ↓ `STATISTICAL TEST` ↓ `ROBUSTNESS` ↓
`OUT-OF-SAMPLE TEST` ↓ `VISUALIZATION` ↓ `RESEARCH REPORT` ↓
`PAPER FIGURE/TABLE` ↓ `REPRODUCIBLE RESULT`

Every result must be traceable to its data, configuration, code version
and methodology.

------------------------------------------------------------------------

## 36. Start now

Do NOT immediately rewrite the project.

First audit the current repository.

Read the existing `.md` files and understand the work already completed.

Then produce a concise:

### CURRENT STATE

-   what is complete
-   what is incomplete
-   what is publication-useful
-   what is scientifically weak
-   what data is missing
-   what must be fixed first

### RESEARCH ROADMAP

Give me the dependency-ordered roadmap.

### FIRST QUESTIONS

Ask me only the first small group of decisions that genuinely require my
input.

Then wait for my answers.

After I answer, implement the next small stage.

Treat this as a long-running research collaboration.

The goal is not simply to make Trading Lab work.

The goal is to make it **scientifically defensible, reproducible,
publication-oriented, PhD-application quality, user-friendly, and
eventually capable of supporting carefully controlled real-world trading
research.**

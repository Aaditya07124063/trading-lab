# Phase 3A — Research protocol S2-MOM-v1 (revision 4)

## How much do backtesting shortcuts distort measured momentum in Indian equities?

**Status:** FROZEN, revision 4. Approved and frozen by the reviewer on 2026-10-05. The SHA-256 of this file and the freeze commit are recorded in `RESEARCH_LOG.md`. Not yet registered in `registry/`; open items are listed in §32. Any change now requires a new version (S2-MOM-v2).
**Written:** 2026-10-05 on commit `d0b4a77`. Revision 4 applies the final wording corrections of the third review (§29).

**What was NOT done while writing this document:**
- No experiment was run. No strategy, portfolio, factor or benchmark return was computed.
- No performance result was inspected. No parameter was chosen from our own data.
- No source code or dataset was changed. UNIV-1, RET-1.1 and ORB v1 are untouched.
- No data after 2026-09-30 and no ORB holdout data or results were read.
- No ML, no news data, no macro data.

The only facts taken from our own data are **structural counts**: the number of selection dates, the number of eligible stocks per date, which columns exist, and the categories in the NSE delisting file. Every statement about the size of an effect comes from prior literature or is a labelled assumption.

**Before any return is computed (Phase 3B)** this protocol must be approved, frozen, hashed (SHA-256) and registered in `registry/` with status `PLANNED`. After the freeze, any change needs a new version with the reason recorded.

Three labels are used throughout:
- **PRIMARY** — the one specification that decides the headline conclusion.
- **FIXED ROBUSTNESS** — alternatives listed in this document. All are reported. None can replace the primary.
- **EXPLORATORY** — anything not listed here. It must be labelled exploratory and cannot carry a confirmatory p-value.

---

# Part A — Literature and positioning

## A1. Closest prior work, field by field

How each source was checked: **[F]** full text read; **[A]** abstract or publisher record only; **[S]** secondary summary only; **[R]** details supplied by the reviewer from the accessible text of the paper and recorded here as given, not re-read by the protocol author. "Unverified" means the detail could not be read in the full paper. Publisher pages for papers 2–7 refused access, so their methods are **not verified** and must be read in full before the freeze (blocker B3).

### Paper 1 — Agarwalla, Jacob & Varma (2013 IIMA W.P. 2013-09-05; published 2017 in *Vikalpa*) [F: working paper, revised 5 Sep 2014]
| Field | Record |
|---|---|
| Universe | All firms with price and shares-outstanding data in CMIE Prowess (6,943 firms) |
| Exchange | BSE |
| Sample | Oct 1993 → Dec 2013 in the paper. The public data library now runs to **Dec 2025** [A: library page] |
| Momentum definition | 11-month return from the end of month t−12 to t−1 (12-1), from daily total returns including dividends |
| Holding period | 1 month, monthly re-formation |
| Portfolio construction | Top 30% = winners, bottom 30% = losers, crossed with two size groups; WML = average of the small and big winner-minus-loser returns; value-weighted |
| Survivorship | Explicit correction for "vanishing" firms: 3,184 firms stopped trading, 439 confirmed mergers; adjusted and unadjusted series are both published |
| Liquidity | Firms traded on fewer than 50 days in the prior 12 months are excluded |
| Transaction costs | None |
| Inference | Descriptive factor statistics |
| Point-in-time membership | Yes in effect: the filter uses only the prior 12 months. No index list is used |
| Headline | Momentum factor about 21.9% per year (Jan 1994 – Dec 2014) |

### Paper 2 — Chui, Ranganathan, Rohit & Veeraraghavan (2023), *Pacific-Basin Finance Journal* 82, 102193 [A]
| Field | Record |
|---|---|
| Universe | 3,956 stocks |
| Exchange | BSE |
| Sample | 2000 → 2021 (months unverified) |
| Momentum definition | "Intermediate and long-term" price momentum. Formation and skip: **unverified** |
| Holding period | Unverified |
| Portfolio construction | Unverified |
| Survivorship | Unverified |
| Liquidity | Turnover ratio; finds liquidity strengthens momentum and illiquid stocks show reversals |
| Transaction costs | Unverified |
| Inference | Unverified |
| Point-in-time membership | Unverified |

### Paper 3 — Raju & Chandrasekaran (2019), SSRN 3510433 [A] + [R]
| Field | Record |
|---|---|
| Universe | NIFTY 100 constituents, taken at monthly month-end dates [R] |
| Exchange | NSE |
| Data source | Refinitiv [R] |
| Sample | UNVERIFIED |
| Momentum definition | "Off-the-shelf momentum criteria" [A]. Formation and skip: UNVERIFIED |
| Holding period | Monthly rebalance [A] |
| Portfolio construction | Long-only, top decile [A] |
| Survivorship | Delisted stocks are included, using the Refinitiv data available [R]. Its momentum-factor analysis uses the survivorship-bias-adjusted IIMA factor database (paper 1) [R] |
| Liquidity | Implicit: large-cap index members |
| Transaction costs | Considered; states the result survives at discount-broker rates [A]. Numbers UNVERIFIED |
| Inference | UNVERIFIED |
| Point-in-time membership | Month-end NIFTY 100 constituents are used [R]. **The exact construction of the historical constituent lists is NOT fully verified** and is not claimed here |
| Headline | +10.70% per year over the NIFTY 100; mean turnover 32.1% per month; notes momentum crashes [A] |

**Accurate position of paper 3:** it is a survivorship-aware momentum study on Indian large caps. It does not leave "survivorship-adjusted Indian momentum" open as a gap.

### Paper 4 — Das & Barai (2016), *Macroeconomics and Finance in Emerging Market Economies* 9(3), 284–302 [A]
| Field | Record |
|---|---|
| Purpose | Asset-pricing test: are size, value and momentum priced? |
| Finding | A conditional Carhart four-factor model describes Indian returns better than the unconditional one |
| Universe, exchange, sample, momentum definition, construction, survivorship, liquidity, costs, point-in-time | **All unverified** |

### Paper 5 — Garg & Varshney (2015), *Global Business Review* 16(3), 494–510 [A]
| Field | Record |
|---|---|
| Universe | CNX 500 firms in four sectors: automobile, banking, pharmaceutical, IT |
| Exchange | NSE (CNX index) |
| Sample | May 2000 → Apr 2013 |
| Momentum definition | Jegadeesh–Titman style; a range of ranking periods |
| Holding period | A range of holding periods |
| Portfolio construction | Long winners, short losers, zero investment |
| Survivorship, liquidity, costs, inference | Unverified. The abstract mentions none |
| Point-in-time membership | Unverified |

### Paper 6 — Nigam & Pandey (2023), *Algorithmic Finance* 10, 21–37 [A]
| Field | Record |
|---|---|
| Design | Long-only momentum; compares several formation windows and rebalance frequencies |
| Finding | Reports that 6-month formation with quarterly rebalancing gave the highest risk-adjusted performance; "accelerated" momentum did worse |
| Note | The reported best specification was chosen after comparing results. It is **not** used to set our primary |
| Other fields | Unverified |

### Paper 7 — Raju (2023), SSRN 4453680 [A]
| Field | Record |
|---|---|
| Design | Effect of number of holdings and universe size on Indian momentum portfolios, using mixed linear models |
| Finding | Concentrated portfolios have more factor exposure and more idiosyncratic risk; no risk-adjusted gain from high concentration |
| Relevance | Supports a wide breakpoint (§10). Other fields unverified |

### Paper 8 — Ranse (Nov 2025), "Survivorship bias in emerging market small-cap indices: evidence from India's NIFTY Smallcap 250", SSRN 5833162 / arXiv 2603.19380 [F]
| Field | Record |
|---|---|
| Universe | NIFTY Smallcap 250, reconstructed by a price-volume market-cap proxy ranking; 1,437 stocks ever in the index, 252 current |
| Exchange / data | NSE daily bhavcopy files, 2016 → 2025 |
| What is compared | **Two equal-weight portfolios with daily rebalancing:** current survivors versus all historical constituents |
| Momentum studied? | **No.** No return-sorted strategy. The paper lists "does survivorship bias affect momentum, value and quality strategies differently?" as future research |
| Bias decomposition? | Only by reason for leaving the index (delisted, graduated, demoted). **No** separation of look-ahead membership, corporate actions, identity or costs |
| Corporate actions / identity | Not adjusted; symbol-level tracking (stated as a limitation) |
| Transaction costs | None (stated) |
| Inference | Bootstrap on annualised returns |
| Headline | Survivor-only overstates annual return by 4.94 percentage points (26.17% vs 21.23%) |

### Paper 9 — Jain (July 2026), "Survivorship bias in Indian equities is not a number: vintage- and filter-dependence in point-in-time universes", SSRN 7099378 [A]
| Field | Record |
|---|---|
| Universe | Point-in-time top-500 Indian equities with dead names retained |
| What is compared | Paired "honest versus survivor" backtests in a 2 × 2 design: two universe vintages (2013, 2015) × two survivor definitions (alive in the panel; resolvable on a free data source) |
| Headline | Bias ranges from +0.8 to +3.3 percentage points per year; exits are not uniformly losers |
| What it directly studies | Survivor-versus-honest backtests on point-in-time Indian universes, and how the measured bias depends on vintage and survivor filter |
| Momentum studied? | **UNRESOLVED.** The accessible abstract does not mention momentum and does not name the strategy that is backtested. Whether the full text contains a momentum-specific experiment has not been verified (access refused, HTTP 403) |
| Bias decomposition comparable to ours? | **UNRESOLVED.** The abstract describes variation by vintage and survivor filter only. It does not mention corporate actions, identity, liquidity look-ahead or costs |

### Targeted checks of papers 4–6 for anything that touches the claimed contribution
- **Garg & Varshney (paper 5) [A]:** the abstract describes a formation/holding grid in four sectors. It mentions no survivorship treatment, no data-bias comparison and no costs. Full text: UNVERIFIED.
- **Nigam & Pandey (paper 6) [A]:** the abstract describes a comparison of long-only momentum variants. It mentions no survivorship or data-bias comparison. Full text: UNVERIFIED.
- **Das & Barai (paper 4) [A]:** an asset-pricing factor test. Publisher abstract was not retrievable on this attempt; no survivorship or data-bias decomposition is indicated in the record seen. Full text: UNVERIFIED.

## A2. What is new here? An honest answer

| Component | Status | Closest prior work |
|---|---|---|
| Momentum exists in Indian equities | **Replication. Not new** | Papers 1, 2, 5. The public IIMA factor already extends to Dec 2025, so even "more recent data" is not new |
| Liquidity-conditioned momentum | **Replication with a different measure. Not new** | Paper 2 |
| Long-only momentum after costs | **Replication on a wider universe. Not new** | Papers 3, 6 |
| Survivorship-adjusted momentum analysis | **Already exists. Not new** | Paper 1 (vanishing-firm correction); paper 3 (delisted stocks included; IIMA adjusted factors) [R] |
| Point-in-time, survivorship-aware universe | **Not new as an idea** | Paper 1 corrected survivorship in 1993–2013 |
| Public-source data pipeline with hashes | **Cleaner data. Not a finding** | — |
| Pre-registered single specification | **Methodological improvement. Not a finding** | None of papers 1–7 appears pre-registered (unverified for 2–7) |
| **Controlled sequential measurement of how several data and backtest corrections change one fixed momentum design** | **The claimed contribution** | Paper 8 (Ranse) [F]: survivorship only, equal-weight portfolios, no momentum. Paper 9 (Jain) [A]: survivor-versus-honest universes by vintage and filter; momentum UNRESOLVED |

**If the bias decomposition is removed, the honest description of this study is: "we replicated known results with cleaner data."** That alone is not a contribution.

**Why the decomposition can be a methodological contribution:**
1. Most Indian momentum evidence, academic and practitioner, comes from pipelines that use some mix of current constituents, vendor-adjusted prices and no costs. Readers cannot tell how much of a reported premium is produced by those choices.
2. Prior work on Indian survivorship bias measures it for a universe's average return. A momentum strategy is different: it sorts on past returns, and survivorship, look-ahead in membership, and corporate-action errors are all correlated with past returns. The bias in a sorted long-short return need not have the same size, or even the same sign, as the bias in an average return.
3. We hold everything else fixed (signal, dates, breakpoints, weights, timing, test) and change one correction at a time in a fixed order. This is a sequential decomposition, not an identification of independent causal effects (B1.5). That gives a paired comparison of the same months, which is far more precise than comparing two different studies.
4. The result is useful whatever its sign: it tells readers how much to discount existing Indian momentum backtests, and how the measured result moves as each correction is added in the stated order.

**Final positioning statement:**
- Momentum in Indian equities is already established.
- Survivorship-adjusted momentum analysis already exists (papers 1 and 3).
- Our proposed contribution is the **controlled sequential measurement of how multiple historical-data and backtest corrections alter the same momentum design.**

**Limits of the claim:**
- It is a measurement for one market, one period, one signal and one liquid universe.
- **Verified:** Ranse does not study momentum and names strategy-specific survivorship bias as open future work.
- **Unresolved:** Jain directly studies survivor-versus-honest point-in-time Indian universes and their vintage and filter dependence. The accessible abstract does not mention momentum. Whether the full text contains a momentum-specific experiment has not been verified. **Exclusive novelty against Jain is therefore not claimed.**
- **Not fully verified:** the exact historical-constituent construction in Raju & Chandrasekaran. This affects only how paper 3 is described, not our design.

---

# Part B — Design

## B1. The bias-decomposition ladder

The ladder is fixed now, before any result. Steps are cumulative. Each step changes exactly one thing.

### B1.1 Definitions shared by every step
- **Dates.** `T*` = 2026-09-30, the last UNIV-1 selection date and the last session of the data. `t`, `m(k)`, `s⁺`, `s⁺⁺` as in B2.
- **Full-sample entity.** The `entity_id` column of RET-1.1: segments joined by every ID-1 evidence link in the data.
- **Survivor pool `P`.** Every full-sample entity whose ID-1 `end_status` is `ACTIVE_AT_CUTOFF` in `data/stage2/identity/id1_entities.csv`.
- **Liquidity.** The UNIV-1 definition, unchanged: median daily traded value (₹) over the 63 market sessions ending on the evaluation date, sessions without an EQ row counting as zero; at least 50 valid sessions; fund units and non-equity ISINs excluded; `rank` 1 = most liquid, ties by `entity_id`.
- **`Top200(pool, d)`**, a deterministic function:
  1. take the UNIV-1 rows with `selection_date = d` and status `MEMBER` or `ELIGIBLE_NOT_SELECTED`;
  2. map each row to its full-sample entity through `segment_at_selection`;
  3. if `pool` is given, keep only entities in `pool`;
  4. if two rows map to the same entity, keep the smaller `rank`;
  5. sort by `rank` ascending and take the first 200.
- **Rankable at `t` (rule common to all steps).** The entity is in the step's universe at `t` and has an RET-1.1 row dated exactly `m(12)` and a row dated exactly `m(1)`. Step D adds one more condition (§6, §20).
- **Formation return.** Product of `(1 + r)` over the entity's rows with `m(12) < date ≤ m(1)`, minus 1, where `r` is the step's daily return.
- **Breakpoints.** Let `n` = number of rankable entities and `k = floor(0.30·n + 0.5)`. Sort by formation return descending, ties by `entity_id` ascending. W = first `k`; L = last `k`.
- **Holding return.** Equal weights at the close of `s⁺`. Each stock's return is the product of `(1 + r)` over its rows with `s⁺ < date ≤ s⁺⁺`, minus 1; a stock with no row in that window returns 0. Portfolio return = mean over its stocks.
- **Benchmark.** Equal weight of all `n` rankable entities, same holding rule.
- Dividends are not included in any step.

### B1.2 Step A — conventional survivor-style baseline (exact algorithm)
| Element | Rule |
|---|---|
| Survivor universe and date | `U_A = Top200(P, T*)`: the 200 most liquid surviving companies **as measured at 2026-09-30**. One fixed list, used for every month from 2012 to 2026 |
| Liquidity definition and lookback | As B1.1, evaluated once, on the 63 sessions ending `T*` |
| Ranking and breakpoints | As B1.1 |
| Symbol / identity | Full-sample entity: the whole earlier history of each listed company under any earlier symbol or ISIN is used, as a data vendor's current-ticker history would give |
| Dead / delisted companies | Excluded by construction. An entity not in `P` never enters. No delisting rule is needed, because every member trades at `T*` |
| Corporate actions | For each RET-1.1 row: if `event_factor` is present (a bonus/split factor parsed from an NSE record, **whatever its `event_status`**: validated, inconclusive or discrepant), `r = close ÷ (prev_close × event_factor) − 1`. No validation is applied. Rights, demergers, schemes, consolidations and unparsed events are not adjusted |
| Return construction | Otherwise `r = ret_raw` (= close ÷ previous close of the same entity − 1) |
| Gaps | A `MULTI_SESSION_GAP` row is used as it is: its return runs from the last traded close, over however many sessions were missed |
| Special-session spans | Used as they are (the two-session return) |
| Unexplained jumps, large residuals | Used as they are. No filter, no cap, no flag |
| Missing price | `r` undefined only if a close is missing or non-positive. RET-1.1 contains no such row; if one appears, the run stops |
| First observation | No return on an entity's first row |
| Costs | None |

Step A reads `return_status` and `research_grade` nowhere.

### B1.3 Step B — point-in-time liquidity selection (exact algorithm)
**The one change:** the date on which liquidity is evaluated moves from `T*` to `t`.

| Element | Step A | Step B |
|---|---|---|
| Survivor pool | `P` | `P` — **inherited unchanged** |
| Universe at `t` | `Top200(P, T*)` for every `t` | `Top200(P, t)` |
| Liquidity definition, lookback, exclusions | B1.1 | B1.1 — unchanged |
| Identity, corporate actions, returns, gaps, spans, jumps, costs, breakpoints, benchmark rule | B1.2 | **Identical to B1.2** |

So B still contains only companies that survive to 2026 and still uses hindsight identity. It removes only the choice of *which* survivors by their 2026 liquidity. Nothing else differs.

### B1.4 Steps C, D and E
| Step | The one change from the step before | Result |
|---|---|---|
| **C** Survivorship and identity | The pool restriction is dropped: `Top200(no pool, t)`, which is exactly UNIV-1 `MEMBER` at `t`. Identity is the UNIV-1 point-in-time identity (links effective on or before `t`). The delisting rule of §22 now applies | Dead and delisted companies enter. Returns and costs still as in B1.2 |
| **D** Corporate actions and data quality | The daily return becomes RET-1.1 `ret_research`; the rankable rule gains the research-grade condition; §20–21 apply | **The corrected gross specification** |
| **E** Costs | Costs of §13 are deducted | Step D net, under each scenario |

Note on step C, stated so it is not over-read: an ID-1 link takes effect on the first session of the later segment, so at any `t` the full-sample and point-in-time identities give the same history up to `t`. Identity therefore changes *which* entities count as survivors, not their past returns. Survivorship and identity cannot be separated in this data, and step C is reported as one correction.

### B1.5 What each difference measures — a sequential decomposition

**A → E is a sequential decomposition. It does not identify independent causal effects of the individual shortcuts.**

| Difference | What it measures |
|---|---|
| **A → B** | The incremental change from replacing the fixed survivor liquidity selection (evaluated at 2026-09-30) with point-in-time monthly liquidity selection, **holding the survivor pool fixed** |
| **B → C** | The incremental change from adding the point-in-time identity and universe correction (the survivor pool is dropped; dead and delisted companies enter) |
| **C → D** | The incremental change from applying the RET-1.1 research-grade return and data-quality rules (including the special-session exclusion) |
| **D → E** | The incremental effect of costs |
| **A → D** | The **total gross correction under the specified sequence** — the primary estimand (§2) |
| A → E | The total correction of the investable result under the specified sequence |

**What is and is not claimed:**
- The total A → D does not depend on the order of the intermediate steps. Each **incremental** contribution does: it depends on the order and on interactions between corrections.
- The individual steps are therefore **not** claimed to be order-invariant causal effects of each shortcut. They are reported as "the change when this correction is added at this point of the sequence".
- The order is fixed now and follows the natural build of a pipeline (choose the universe, then the returns, then the costs).
- **The reverse-order ladder is a robustness analysis only:** starting from D, one correction is switched back at a time (D with pool `P`; D with the step-A return rule). It shows how sensitive the step sizes are to order. It does not replace the primary sequence.
- No factorial design and no Shapley-type attribution is part of this protocol.

**Reported for every step,** for W, L, WML and the benchmark: mean monthly return, volatility, Sharpe-type ratio, Newey–West t-statistic, maximum drawdown, one-way turnover, number of stocks, and the **economic conclusion** under two rules fixed now:
- "momentum detected" = WML mean > 0 with one-sided p < 0.05;
- "long-only winners beat the universe" = W minus benchmark > 0 with one-sided p < 0.05.

A change of economic conclusion between two steps is reported as such.

**Guard.** Steps A, B and C are measurements of error. They deliberately contain look-ahead. They are never used as evidence about momentum, and every table that shows them is labelled "biased by construction".

**Scope of step A.** It is one precisely defined conventional pipeline, built from our own files. It is not a copy of any vendor's product; a real vendor series may err differently (§30).

## B2. Event-time timeline and information set

For one selection date `t` (a month-end session). `m(k)` = the month-end session k months before `t`. `s⁺` = the first session after `t`. `s⁺⁺` = the first session after the next selection date.

```
 m(12)                         m(1)              t      s⁺                      next t   s⁺⁺
  |------- formation ------------|----- skip ------|------|------- holding ---------|-------|
  |  11 months of daily returns  |   1 month       |      |                         |       |
  |  (first session after m(12)  |  not used in    |      | positions held          |       |
  |   ... m(1))                  |  the signal     |      |                         |       |
                                                   ^      ^                                 ^
                                        universe + signal  trade at close:          trade at close:
                                        fixed after close  enter, pay costs         exit / rebalance,
                                                                                    pay costs
```

| Item | Uses data dated | Latest date used | Why it cannot leak the future |
|---|---|---|---|
| Universe membership (UNIV-1 `MEMBER`) | 63 sessions ending `t` | `t` | UNIV-1 uses nothing after `t`; a later delisting never alters an earlier row |
| Liquidity rank | 63 sessions ending `t` | `t` | Same `rank` column; no later value is read |
| Identity (`entity_id` at `t`) | Links effective on or before `t` | `t` | UNIV-1 joins segments only by evidence already effective; the id is the earliest segment, so it never reveals a later symbol |
| Formation return | Sessions after `m(12)` up to `m(1)` | `m(1)`, one month before `t` | Ends a full month before the decision |
| Corporate-action status of formation rows | Ex-dates inside the formation window; validation uses the price on the ex-date row itself | `m(1)` | No event after `m(1)` can change a formation-window flag. The record is used to build historical returns, not as a signal (§21) |
| Data-quality eligibility | Flags on formation-window rows | `m(1)` | Known a month before `t` |
| Trade | Close of `s⁺` | `s⁺` | One full session after every input is fixed |
| Holding return | Sessions after `s⁺` up to `s⁺⁺` | — | Outcome only; never an input |
| Costs | Weights at `s⁺` against drifted weights | `s⁺` | Deducted at the rebalance session |

**Checks that must pass before any result is reported (§19, §25):**
1. **Perturbation test:** randomly change every price, flag, liquidity value and membership row dated after `t`; the portfolios chosen at `t` must be bit-identical.
2. **Shift test:** the signal series must be unchanged when the data are truncated at `t`.
3. **Placebo:** a random ranking must give a WML mean indistinguishable from zero.

Steps A and B break rows 1–3 of the table on purpose. That is their definition, and it is confined to those steps.

## B3. Temporal design

Boundaries are fixed now by rules that do not depend on performance.

| Period | Holding months | Length | Role |
|---|---|---|---|
| **Primary historical sample** | Jul 2012 → Dec 2021 | 114 | All primary and secondary tests |
| **Chronological OOS / confirmation period** | Jan 2022 → Aug 2026 | 56 | Later-period check of the primary and of each ladder step |
| Fixed chronological robustness, halves | Jul 2012 → Mar 2017; Apr 2017 → Dec 2021 | 57 + 57 | Stability inside the primary sample |
| Fixed pooled sample | Jul 2012 → Aug 2026 | 170 | Descriptive only; never called confirmatory |
| Prospective | After 2026-09-30 | — | Outside this protocol; behind the access boundary |

**Why the start is July 2012.** It is the first month with a full 12-1 formation window inside the verified data (which begins 2011-06-22).

**Why the boundary is December 2021.**
1. It is the last year of the sample of the most recent closest published paper (paper 2: 2000 → 2021 [A]). Every month from January 2022 lies after the samples of papers 1–5 as published.
2. It is a calendar-year end, set by a published fact, not by anything in our data.
3. It leaves 56 later months, about one third of the data.
4. It was fixed before any return was computed and cannot be moved.
- Limit of reason 1: the end month of paper 2's sample is known only from its abstract, and the public IIMA factor (paper 1) is updated to December 2025. The boundary is therefore a convention tied to the publication record. It is not a claim that nobody has seen later Indian momentum data.

**What the 2022–2026 period is, and is not.**
- It **is** a chronological out-of-sample period: later months, held back, run once, after the primary results are registered, with identical code.
- It is **not** an independently designed experiment. Same market, same data pipeline, same researcher, same specification, and data that already exist today.
- Its protection comes from the execution order below and the code hash, not from the data being unseen by the world.

**Execution order, enforced:**
1. Code is developed on synthetic data and on real data with returns permuted across stocks within each date. On real data only non-performance diagnostics may be printed (counts, coverage, turnover, missing-data counts).
2. Protocol and code are frozen and hashed.
3. The primary historical sample is run once and registered.
4. Only then is the confirmation period run, with the same code hash. No change is allowed between steps 3 and 4.

**Confirmation rule, fixed now**, for each tested quantity:
- **Confirmed:** same sign as in the primary sample and significant at the same level in the confirmation period.
- **Consistent, not confirmed:** same sign, not significant.
- **Not confirmed:** opposite sign.

Caveats stated in advance:
- The confirmation period is short and its precision is low (§15). "Consistent, not confirmed" is a likely outcome even if an effect is real.
- The step-A list is fixed at 2026, so its distance from each month, and therefore its bias, differs between the two periods **by construction**. A different size of `δ` in the two periods is expected and is not by itself a failure to confirm; the sign rule above is what is tested. The ladder is reported separately for the two periods and never averaged silently.
- We have not seen any result from this data. We do know the published record up to 2021 and general market history after it. This prior exposure cannot be removed.

---

# Part C — Protocol items

## 1. Research question
**Primary:** How much do common historical-data and backtesting shortcuts distort measured cross-sectional momentum in Indian equities?

**Underlying economic test:** does cross-sectional price momentum survive on a point-in-time, survivorship-aware Indian equity universe under trading frictions, and how does it vary with liquidity? (Regime-conditioned analysis is outside the primary study scope, §12.)

| Layer | Content | Status |
|---|---|---|
| Replication | Momentum exists; liquidity matters; long-only after costs | Established. Not claimed as new |
| Methodological extension | One pre-specified design; itemised costs with break-even; leakage tests; multiple-testing control | Improvement in rigour. Not a finding |
| Bias decomposition | Ladder A → E | The main contribution |
| Genuinely novel | Only the decomposition. Ranse is verified not to cover momentum; Jain is UNVERIFIED on this point | Conditional on the Jain full text |

## 2. Primary hypothesis and primary estimand
**Primary estimand.** For each holding month `t` of the primary historical sample,

`δ(t) = WML_A(t) − WML_D(t)`

the gross winner-minus-loser return under the conventional pipeline (step A, B1.2) minus the same under the corrected pipeline (step D). The quantity of interest is its mean, `Δ = E[δ(t)]`, in percent per month.

**H1 (total distortion).** `Δ ≠ 0`.
- H0: `Δ = 0`. Two-sided, α = 0.05.
- Two-sided because the direction is not obvious for a long-short return: survivorship inflates the winner leg, but it also removes losers that later die, which can flatter the loser leg.
- Practical significance is judged separately against the ex-ante bound of §27.

## 3. Secondary hypotheses
**Decomposition family (Holm, family α = 0.05), paired differences:**
- **H2a:** mean of `WML_A − WML_B` ≠ 0 (liquidity look-ahead). Two-sided.
- **H2b:** mean of `WML_B − WML_C` ≠ 0 (survivorship with identity). Two-sided.
- **H2c:** mean of `WML_C − WML_D` ≠ 0 (corporate actions and data quality). Two-sided.
- **H2d:** mean of `W_A − W_D` > 0. One-sided: the long-only winner return is inflated by the shortcuts, the standard survivorship prediction.

**Economic replication (fixed sequence, each at α = 0.05, steps D and E):**
- **H3 (existence):** mean `WML_D` > 0, one-sided.
- **H4 (survival), tested only if H3 is rejected:** mean of `W_E − Benchmark_E` > 0, one-sided, with **statutory costs only** (§13).

**Liquidity (single secondary test, α = 0.05), step D:**
- **H5:** `WML` differs between UNIV-1 rank 1–200 and rank 201–500. Two-sided.

**Market regime:** not part of this study (§12).

## 4. Exact data sources
| Data | Source | Location |
|---|---|---|
| Daily prices and returns | RET-1.1 | `data/stage2/datasets/ret1_1/`; hashes in `data/stage2/returns/ret1_1_manifest.json` |
| Universe and liquidity rank | UNIV-1 (frozen) | `data/stage2/universe/univ1_pit_universe.parquet`, SHA-256 `2abf457a06abf0e8a0b96c0b0ca0f75ccc07729c0166b1812d7af4646cba9c42` |
| Identity, links, end status | ID-1 | `data/stage2/identity/` |
| Corporate-action records and validation | CA-2 | `data/stage2/validation/` |
| Delisting type | NSE `delisted.csv` snapshot | raw archive, hash in `data/stage2/raw_manifest.jsonl` |
| Statutory and exchange cost rates | Official NSE, SEBI, government and broker schedules | Intraday schedule archived; **delivery schedule not yet archived** (blocker B2) |

`python3 scripts/build_stage2.py` must pass all 150 checks before the study runs.

## 5. Exact data-class restrictions
- NSE cash market, series **EQ** only.
- Verified period only: 2011-06-22 → 2026-09-30.
- Companies only (ISIN starting INE). UNIV-1 already excludes fund units.
- **Price returns only.** RET-1.1 has no dividends.
- **No market capitalisation.** So no value weighting, no size control, no factor-model alpha from our own data.
- No intraday data, no Yahoo data, no vendor-adjusted prices, no ORB data.

## 6. Point-in-time universe definition (step D, the corrected specification)
- **Selection dates** `t`: UNIV-1 month-end selection dates.
- **Universe at `t`:** UNIV-1 status `MEMBER` at `t`: the 200 most liquid eligible companies by 63-session median traded value.
- **Rankable at `t`**, decided with data up to `t`:
  1. `MEMBER` at `t`;
  2. has a price on month-end sessions `m(12)` and `m(1)`;
  3. every row in the formation window is research-grade, apart from market-wide special-session days (§20).
- Stocks failing 2 or 3 are not ranked that month. Counts are reported by month and by reason.
- **Less liquid band (H5 only):** UNIV-1 `ELIGIBLE_NOT_SELECTED`, rank 201–500 at `t`. UNIV-1 is read, not changed. Every selection date has at least 969 eligible entities, so the band is always full.

## 7. Formation horizons
- **PRIMARY: 12 months (12-1).**
- Justification from the literature, not from our data: Carhart (1997) defines the momentum factor on the eleven-month return lagged one month; Fama & French (2012) use the same window internationally; paper 1 uses exactly this window for India [F].
- FIXED ROBUSTNESS: 3, 6 and 9 months (Jegadeesh & Titman 1993).
- Paper 6's "6 months is best" is a result-selected choice and is not used.

## 8. Skip-period rule
- **PRIMARY: skip the most recent month.** Formation return = compounded research-grade daily return from the first session after `m(12)` through `m(1)`.
- Reason: one-month reversal (Jegadeesh 1990) and bid–ask bounce.
- FIXED ROBUSTNESS: no skip.

## 9. Holding-period definition
- **PRIMARY: one month, non-overlapping.** Enter at the close of `s⁺`; exit or rebalance at the close of `s⁺⁺`.
- First selection date 2012-06-29; last 2026-07-31; 170 holding months in total, split as in B3.
- FIXED ROBUSTNESS: K = 3, 6, 12 with the Jegadeesh–Titman overlapping-portfolio method (monthly return = average of the K live cohorts); entry at the close of `t`.

## 10. Portfolio construction
- Rank rankable stocks at `t` by formation return. Ties broken by `entity_id`, ascending.
- **PRIMARY breakpoints: top 30% = Winners (W), bottom 30% = Losers (L).**
- **PRIMARY weights: equal weight** at each rebalance; weights drift within the month.
- WML = W − L.

**Justification for 30% and equal weight:**
1. Carhart's (1997) momentum factor is the **equal-weighted** return of the top 30% minus the bottom 30% of stocks by eleven-month lagged return. Our primary is the same construction.
2. Fama & French (2012) use the 30th and 70th percentiles for international momentum factors.
3. Paper 1 uses top and bottom 30% for India [F].
4. Method: with about 200 stocks, 30% gives about 60 names per side. Deciles give about 20, where single-stock noise dominates; paper 7 reports that concentrated Indian momentum portfolios carry more idiosyncratic risk [A].
5. Equal weight is forced as well as justified: there is no market capitalisation in the data.

- FIXED ROBUSTNESS: quintiles; deciles (Jegadeesh & Titman 1993); weights proportional to UNIV-1 `liquidity_median_value`.

## 11. Liquidity conditioning
- Measure: UNIV-1 `rank` at `t`, from the 63 sessions ending `t`. No later liquidity is used.
- **PRIMARY (H5):** build step-D WML separately in rank 1–200 and rank 201–500; test the difference of the two monthly series.
- FIXED ROBUSTNESS: rank 1–100 versus 101–200.
- Difference from paper 2: it used turnover ratio. We cannot compute it. H5 is a related test, not an exact replication, and is not claimed as new.

## 12. Market-regime conditioning
**Outside the primary study scope.** This protocol contains no regime-conditioned analysis: no regime hypothesis, no regime table or figure, no regime data.

- It may be taken up later as a separate exploratory extension, under its own pre-specified note, with one classification fixed in advance and an archived, verified index source.
- No regime result may be added to this study after results are seen.
- The NSE index files are therefore not needed here, and their archival is not a blocker for this protocol.

## 13. Transaction-cost model
Delivery (overnight) trades. The intraday cost files frozen for ORB v1 do not apply and are not changed.

**Class 1 — statutory, exchange and broker charges. Must be backed by archived official sources.**

| Component | Expected rate | Side | Evidence status |
|---|---|---|---|
| Securities transaction tax (delivery) | 0.100% | buy and sell | Not archived. Reported cut from 0.125% on 2012-07-01, the first month of the sample. To verify |
| Exchange transaction charge + IPFT | 0.00307% | each side | Archived (`docs/evidence/cost_sources.md`, NSE circular FA/73061) |
| SEBI turnover fee | 0.0001% | each side | Archived (same file) |
| Stamp duty (delivery) | 0.015% | buy | Not archived. To verify |
| GST | 18% of (brokerage + exchange + SEBI) | each side | Archived (same file) |
| Depository charge | flat fee per stock sold | sell | Not archived |
| Brokerage (delivery) | 0 | each side | Not archived for delivery |

- A rate that cannot be evidenced by the freeze is a blocker (B2), not a guess.
- Where a historical rate cannot be evidenced, the current rate is applied to the whole sample and labelled as an assumption.

**Class 2 — execution cost (half-spread plus market impact). Assumed scenarios. None is called "realistic".**

We have no quote or order-book data. These are scenarios chosen in advance to span a wide range. They are not estimates.

| Scenario | One-way slippage, rank 1–200 | One-way slippage, rank 201–500 |
|---|---|---|
| S0 | 0 bps | 0 bps |
| S1 | 5 bps | 15 bps |
| S2 | 10 bps | 30 bps |
| S3 | 25 bps | 75 bps |
| S4 | 50 bps | 150 bps |

**Always reported, for W and for the benchmark:**
- gross return;
- net return under S0, S1, S2, S3 and S4 (statutory charges are included in every one);
- **break-even one-way cost:** the slippage at which the net excess return of W over the benchmark is zero.

**Rules:**
- The hypothesis test H4 uses S0, the only scenario with no assumption.
- No scenario is singled out as the answer. Conclusions about survival are stated as "survives up to a one-way cost of X bps".
- The benchmark pays costs on its own turnover.
- Notional ₹1 crore per portfolio (to convert the flat depository fee). Capacity is reported separately: portfolio size at which trades reach 1% and 5% of median daily traded value.
- A net WML is shown only as a hypothetical. The short leg cannot be held overnight in the cash market, and no point-in-time list of futures-eligible stocks is archived.
- FIXED ROBUSTNESS: brokerage 0.03%; stock-level spread estimated from daily high, low and close (Corwin & Schultz 2012; Abdi & Ranaldo 2017) using data up to `t` only.

## 14. Primary performance metric
- **H1 (primary):** mean of `δ(t) = WML_A(t) − WML_D(t)`, percent per month. **H2:** mean of the paired monthly difference between two adjacent ladder steps.
- **H3:** mean monthly gross `WML_D`. **H4:** mean monthly `W_E − Benchmark_E` under S0.
- Reported for every portfolio and step: mean, volatility, Sharpe-type ratio, Newey–West t-statistic, skewness, worst month, maximum drawdown, one-way turnover, share of positive months.
- Sharpe-type ratio: for WML, mean ÷ volatility (it is zero-investment). For long-only portfolios, the information ratio against that step's benchmark. No risk-free rate is used, because none is archived.

## 15. Primary statistical test
- **PRIMARY:** t-test of the mean of a monthly series (a return or a paired difference) with Newey–West (1987) standard errors. Lag fixed by `floor(4·(T/100)^(2/9))`: lag 4 for T = 114 and for T = 170, lag 3 for T = 56.
- FIXED ROBUSTNESS: stationary bootstrap (Politis & Romano 1994), 10,000 resamples, automatic block length, fixed seed. For paired differences the two series are resampled together.
- The primary holding period is one non-overlapping month, so the primary test has no overlapping-return problem. For K > 1 the overlapping-portfolio method removes it.

**Power and precision for the primary estimand `δ(t) = WML_A(t) − WML_D(t)`.**

| Item | Value |
|---|---|
| Null | `Δ = 0` |
| Alternative | `Δ ≠ 0`, two-sided |
| Effect size examined | `|Δ|` = **0.10% per month**, the ex-ante economically meaningful reference threshold (§27). It is not a forecast of our result and not a universal minimum |
| Sample size | T = 114 months (primary); 56 (confirmation); 170 (pooled, descriptive) |
| Dependence | Monthly, non-overlapping. Serial correlation is allowed for by Newey–West errors, lag 4. A bias series can be persistent, so power is also shown for AR(1) correlation ρ = 0.2 and 0.4, where the standard error is larger by √((1+ρ)/(1−ρ)) = 1.22 and 1.53 |
| α | 0.05, two-sided |
| Target power | 80% |

**The key unknown.** Power depends on the monthly standard deviation of `δ`. `δ` is the difference between two portfolios that share most of their stocks, so its standard deviation is far smaller than that of WML itself, but **its value cannot be known without computing returns**. No published figure for it exists. Therefore:

> **Power for H1 cannot be defensibly established from pre-result information.** The tables below are a precision and sensitivity calculation. This protocol does **not** claim that H1 is adequately powered.

Smallest `|Δ|` (% per month) detectable with 80% power, T = 114:

| SD of δ (% per month) | ρ = 0 | ρ = 0.2 | ρ = 0.4 |
|---|---|---|---|
| 0.25 | 0.066 | 0.080 | 0.100 |
| 0.50 | 0.131 | 0.161 | 0.200 |
| 1.00 | 0.262 | 0.321 | 0.401 |
| 1.50 | 0.394 | 0.482 | 0.601 |

Power to detect `|Δ|` = 0.10% per month, T = 114:

| SD of δ (% per month) | ρ = 0 | ρ = 0.2 | ρ = 0.4 |
|---|---|---|---|
| 0.25 | 99% | 94% | 80% |
| 0.50 | 57% | 41% | 29% |
| 1.00 | 19% | 14% | 11% |
| 1.50 | 11% | 9% | 8% |

Reading the tables:
- H1 reaches 80% power at the reference threshold only if the standard deviation of `δ` is at most about **0.38%** per month (ρ = 0), **0.31%** (ρ = 0.2) or **0.25%** (ρ = 0.4).
- To show that the distortion is *immaterial* (the equivalence statement of §27) with 80% power when the true `Δ` is zero, it must be at most about **0.36%**, **0.30%** or **0.24%**.
- For the 56-month confirmation period every detectable effect above is larger by a factor of 1.43; for the pooled 170 months it is smaller by a factor of 0.82.

**Blinded precision step (fixed now).** In Phase 3B, before any mean, t-statistic or p-value of `δ` is displayed, the code outputs only the standard deviation and the Newey–West long-run standard deviation of `δ`. The achieved detectable effect is computed from them and written to the registry. This step can change nothing: the sample, the test and the thresholds are already fixed. It only records, before unblinding, how precise the primary test is.

**If the test turns out imprecise,** the result is reported as an estimate with its confidence interval and labelled "inconclusive at the stated precision" under the rules of §27. It is not presented as evidence of no distortion.

**Secondary: the existence test H3.** Power depends on the standardised effect `d = mean ÷ monthly standard deviation` of `WML_D`. Smallest `d` detectable with 80% power, one-sided 5%: 0.233 (114 months), 0.332 (56), 0.191 (170); as an annualised Sharpe ratio 0.81, 1.15 and 0.66. Under an outside reference alternative of an annualised Sharpe ratio of 0.5 — an assumption about the order of magnitude reported for long US samples, to be checked against the original (blocker B4), and not a forecast — the power of H3 is about 46%, 29% and 59%. **H3 is underpowered** on that reference, which is one reason it is a secondary replication test and not the primary.

## 16. Robustness tests (all fixed now)
| ID | Robustness | Purpose |
|---|---|---|
| R-JK | J ∈ {3, 6, 9, 12} × K ∈ {1, 3, 6, 12}: 16 cells, step D | Standard grid |
| R-skip | No skip month | Short-term reversal |
| R-bp | Quintiles; deciles | Breakpoints |
| R-wt | Liquidity-proportional weights | Weighting |
| R-entry | Entry at the close of `t` | Timing |
| R-cost | Brokerage 0.03%; estimated spreads | Costs |
| R-half | Two halves of the primary sample (B3) | Stability |
| R-pool | Pooled 170 months | Descriptive |
| R-order | Reverse ladder: from D, undo one correction at a time (B1.5) | Order dependence |
| R-span | Special-session spans use the raw two-session return (§20) | Calendar sensitivity |
| R-gap | Multi-session gaps use the raw gap return when no event is on the row (§20) | Suspension sensitivity |
| R-miss | Holding-period missing days: raw return; zero | Missing-data sensitivity |
| R-delist | Delisting return 0% for all; −100% for all non-voluntary | Delisting sensitivity |
| R-mono | Monotonicity across formation groups, Patton & Timmermann (2010) | Shape |
| R-ext | Correlation of `WML_D` with the public IIMA momentum factor over common months | External check; only if the file can be archived with a hash |

## 17. Multiple-testing procedure
- **H1:** single primary test, α = 0.05.
- **H2a–H2d:** Holm step-down, family α = 0.05.
- **H3 → H4:** fixed sequence, each at 0.05; H4 only if H3 is rejected.
- **H5:** single secondary test, α = 0.05.
- Benjamini–Hochberg q-values are shown beside every secondary p-value.
- **R-JK grid:** Romano–Wolf step-down p-values and White's reality-check p-value for the best cell. The best cell is never presented as the result.
- Every specification that is run is written to `registry/trials.jsonl`. The deflated Sharpe ratio (Bailey & López de Prado 2014) of `WML_D` is reported with that trial count.
- For H3, the stricter t > 3 of Harvey, Liu & Zhu (2016) is reported beside the conventional threshold.

## 18. Development / validation / OOS design
Defined in **B3**. In short:
- **Development:** synthetic and permuted data only; no real performance.
- **Validation:** none, because nothing is tuned. The fixed robustness set takes its place.
- **Primary historical sample:** Jul 2012 – Dec 2021 (114 months), run once after the freeze.
- **OOS / confirmation:** Jan 2022 – Aug 2026 (56 months), run once, after the primary results are registered, with the same code hash.
- The pooled 170 months are descriptive and are never called confirmatory.

## 19. Leakage controls
| Bias | Control |
|---|---|
| Survivorship | Step C/D universe comes from daily exchange files that contain every stock that traded; dead names stay; delisting rule §22. Survivor-only universes exist only in steps A and B, as labelled treatments |
| Look-ahead | Timeline B2; one-session trade delay; perturbation and shift tests |
| Selection | One primary specification; frozen and hashed; every robustness reported, none promoted |
| Corporate-action leakage | Step D uses RET-1.1 only; adjustments only for validated events; flags in the formation window are dated a month before the decision |
| Future liquidity leakage | Liquidity is the UNIV-1 rank from the 63 sessions ending `t` |
| Future identity leakage | Step C/D identity uses only links effective at `t` |
| Data snooping | No tuning; §17; trial registry; deflated Sharpe ratio |
| Overlapping returns | Non-overlapping primary; overlapping-portfolio method for K > 1; Newey–West and bootstrap |
| Cost omission | Class 1 costs in every net figure; scenarios; break-even; benchmark charged |
| Arbitrary regimes | No regime analysis is part of this study (§12); none may be added after results |
| Holdout | Research loaders stop at 2026-09-30; no intraday or ORB file is read; access-boundary tests must pass |

## 20. Missing-data handling
**The primary analysis (step D) uses RET-1.1 research-grade returns only: `ret_research`.** RET-1.1 is not changed. A row that is not research-grade has no return in the primary analysis.

Two kinds of non-research-grade rows are handled differently because they are different problems.

**(a) Market-wide: `SPECIAL_SESSION_SPAN`** (19 dates; every stock at once).
- **PRIMARY: excluded.** That day is left out of every stock's formation return and of every portfolio's holding return. All stocks lose the same day, so the cross-sectional ranking still compares like with like.
- Consequence, stated in advance: in the months that contain such a date, monthly returns omit one two-session price move for all portfolios alike.
- These days do not make a stock unrankable; otherwise almost no formation window would qualify.
- FIXED ROBUSTNESS (R-span) only: use the raw two-session return. This is a sensitivity analysis, never the primary.

**(b) Stock-specific:** `MULTI_SESSION_GAP`, `MISSING_PRICE`, `EVENT_DISCREPANT`, `EVENT_INCONCLUSIVE`, `EVENT_UNADJUSTABLE`, `UNEXPLAINED_JUMP`, `VALIDATED_LARGE_RESIDUAL`.
- **In the formation window:** the stock is not ranked that month (§6). This is known a month before `t`; it is not look-ahead.
- **In the holding month:** a stock is never removed after the fact because its data turned bad. **PRIMARY:** on such a day its return is replaced by the same-day return of the other stocks in its portfolio (a neutral fill).
- FIXED ROBUSTNESS: R-gap and R-miss.
- `FIRST_OBSERVATION` rows have no return and need no rule.

Reported: the number of excluded stock-months and filled stock-days, by status, for each portfolio.

## 21. Corporate-action handling
**Three different things are kept apart:**
| Concept | What it is here | Status in our data |
|---|---|---|
| Economic event date | The ex-date of the bonus, split or other action: the session on which the price reflects it | Known. NSE field `exDate` |
| Source publication / availability date | When the record became public | The NSE record carries a broadcast-date field (`caBroadcastDate`), but its coverage and reliability have **not** been checked. Where it is absent or unchecked, **no availability date is assumed or invented** |
| Research use of the record | How this study uses it | Retrospectively, from an archive retrieved in October 2026, to build historical returns and data-quality classes |

**Corporate-action information is used only to construct historical returns and data-quality classifications. It is never a trading signal.**
- The momentum signal is built from past returns alone. No portfolio decision is conditioned on the announcement, type or size of a corporate action.
- An action enters a decision at `t` only through formation-window rows, whose ex-dates are on or before `m(1)`, a full month earlier. A bonus or split is in the price on its ex-date, so the return on that row is an observed past fact at `t`.
- **Stated limit:** the research-grade classification (for example "validated" or "large residual") is a retrospective data-quality construct. It is applied to past rows; it is not a claim about what an investor could have classified in real time. The record set is also today's archive, which may differ from what was published at the time. Step C → D measures the effect of this classification as a whole.

**Rules (step D):**
- Only RET-1.1 adjustments are used: validated bonuses and splits.
- Rights issues, demergers, schemes, consolidations, unparsed events, discrepant or inconclusive events, and validated events with a residual above the fixed 10% threshold are not research-grade. No factor is invented or altered. No raw price is changed.
- The 10% flag marks a data-quality exclusion. It is not treated as proof that the corporate action is wrong.
- No dividends (price returns). No adjusted price-level series is built.
- Steps A–C apply every recorded bonus/split factor without validation and ignore the flags, exactly as defined in B1.2. That is the correction being measured (C → D).

## 22. Delisting handling
A held stock may stop trading during the holding month.
- No price at the exit date → carried at its last price to the exit date.
- Trades again later → the realised gap return is booked in the month of the exit date. This values a position already held; it does not affect selection.
- Never trades again:
  - NSE `delisted.csv` type "Voluntary Delisting" → 0%;
  - "Compulsory Delisting", "Delisting - Liquidation", or no evidence (`ENDED_UNEXPLAINED`) → **−30%**, the Shumway (1997) convention, used as a stated assumption.
- A symbol or ISIN change with identity evidence is not a delisting.
- FIXED ROBUSTNESS: R-delist.
- The number of delisting events per portfolio is reported.

## 23. Turnover calculation
- `drift weight` = weight reached by each stock at the end of the holding month.
- **One-way turnover** = ½ × Σ |target weight − drift weight| over all stocks, including entries and exits.
- Buys and sells are costed separately (§13). Cost = Σ(buy value × buy rate) + Σ(sell value × sell rate), as a fraction of portfolio value, deducted at the rebalance session.
- Reported for W, L and the benchmark at every ladder step: mean and distribution of monthly one-way turnover; annualised turnover; average holding length.

## 24. Benchmark definition
- **PRIMARY benchmark:** equal-weighted portfolio of **all rankable stocks at `t`** in the same ladder step, with the same timing, return rules and cost model, rebalanced monthly.
- Reference only, in figures: NIFTY 50 price index. Not used in any test.
- An alpha against the public IIMA factors is EXPLORATORY.

## 25. Failure criteria
**Stop; report nothing:**
- the Stage 2 rebuild does not pass all 150 checks;
- an access-boundary test fails, or a file dated after 2026-09-30 is opened;
- the perturbation, shift or placebo test fails;
- the code hash changes between the primary run and the confirmation run.

**Report, labelled "not reliable":**
- any month with fewer than 100 rankable stocks in step D, or an average below 150;
- more than 5% of stock-days in W or L filled under §20(b);
- H1, H3 or H4 changes sign or significance under R-span, R-gap, R-miss or R-delist.

## 26. What would constitute a publishable contribution
1. **A measured, decomposed distortion (H1, H2), whatever its size or sign.** A large distortion warns readers about existing Indian backtests. A small one tells them the shortcuts are harmless in liquid stocks. Both are informative because the design was fixed first.
2. A change of **economic conclusion** along the ladder (for example momentum "detected" at A but not at D or E).
3. The replication results H3–H5, reported as replication.

The paper must **not** claim: that Indian momentum is new; that liquidity-conditioned or long-only momentum is new; that cleaner data is a discovery; that the best robustness cell is the result.

## 27. What would falsify the hypothesis, and the practical-significance threshold

**Ex-ante economically meaningful reference threshold: `|Δ|` = 0.10% per month (about 1.2 percentage points per year).**

What this threshold is:
- a reference level fixed **before** any return is computed, and not revisable after results;
- informed by the scale of transaction costs and by published Indian bias magnitudes (below);
- used only to describe a measured distortion as material, immaterial or uncertain.

What it is **not:**
- it is not claimed to be a universal minimum economically meaningful effect. Another investor, universe or holding period could reasonably use a different level;
- it is not a statistical threshold and was not chosen from our results.

Scales that informed it, none taken from our results:
1. **Cost scale.** Securities transaction tax on a delivery round trip is 0.20% of traded value (0.10% on each side; rate pending archived evidence, blocker B2). A monthly-rebalanced portfolio with one-way turnover `τ` pays `0.20% × τ` per month in this one tax. The one turnover figure documented for an Indian long-only momentum portfolio is 32.1% per month (paper 3 [A]), giving 0.064% per month; at 50% turnover it is 0.10%. So 0.10% per month is of the order of an unavoidable cost of running the strategy.
2. **Published bias scale.** The two Indian survivorship studies report 0.8–3.3 (paper 9 [A]) and 4.94 (paper 8 [F]) percentage points per year for equal-weight universes. 1.2 points per year sits at the low end of that range.
3. **Premium scale.** The Indian momentum factor is reported at about 21.9% per year (paper 1 [F]); 1.2 points is about one-twentieth of that.

Limits of these anchors, stated: anchor 1 depends on a tax rate not yet archived and on a turnover figure read from an abstract; anchor 2 concerns average universe returns, not a momentum spread; anchor 3 is a proportion, not an economic law. The threshold is a reasoned reference, fixed in advance.

**Decision rules for H1 (primary sample):**
| Outcome | Condition | Statement allowed |
|---|---|---|
| Distortion detected and material | H0 rejected **and** the 90% confidence interval for `Δ` lies wholly outside ±0.10% | "The shortcuts materially distort measured momentum" |
| Distortion detected, size uncertain | H0 rejected, interval overlaps ±0.10% | "A distortion exists; it may or may not be material" |
| **Hypothesis contradicted: distortion immaterial** | The 90% interval lies wholly inside ±0.10% (two one-sided tests at 5%) | "The shortcuts do not materially distort measured momentum in this universe" |
| Inconclusive | Anything else | Estimate and interval only, with the achieved precision from §15 |

**Other hypotheses:**
- **H3 is not supported** if one-sided p ≥ 0.05. It is **contradicted** only if the upper end of the 90% interval for the annualised Sharpe ratio of `WML_D` is below 0.25 (half the reference alternative of §15). Otherwise inconclusive.
- **H4:** "does not survive frictions" may be stated only if W fails to beat the benchmark under S0. If it passes S0, the claim is limited to "survives up to the break-even cost".
- H2a–H2d are supported only if rejected after Holm correction; each is also read against the ±0.10% bound.
- Confirmation status (B3) is reported for every one of these.

## 28. Tables and figures required for the paper
**Tables**
1. Literature comparison: the eleven fields of A1 for each prior paper and for this study.
2. Data and sample: selection dates; rankable stocks per month; exclusions by reason; non-research-grade rows by status.
3. **Bias ladder (main table):** steps A–E × {W, L, WML, benchmark}: mean, volatility, Sharpe-type ratio, t-statistic, maximum drawdown, turnover, stock count, economic conclusion.
4. **Step differences:** A−B, B−C, C−D, D−E, A−D, A−E: mean, t-statistic, raw and Holm p-values, confirmation status.
5. Reverse-order ladder (R-order).
6. Ladder by period: primary, confirmation, two halves, pooled.
7. Corrected momentum (step D): W, middle, L, WML, benchmark with full statistics.
8. Costs: gross; net under S0–S4; break-even one-way cost; turnover.
9. J × K grid with Romano–Wolf adjusted p-values.
10. Liquidity bands (H5).
11. Sensitivity: span, gap, missing-day and delisting rules.
12. Multiple-testing summary: every hypothesis, raw and adjusted p, decision, confirmation status; trial count; deflated Sharpe ratio.

**Figures**
1. Event-time timeline (B2).
2. Ladder diagram: what each step changes.
3. Rankable stocks and exclusions over time, by ladder step.
4. Waterfall of mean WML and mean W return from step A to step E.
5. Cumulative log return of WML at steps A and D.
6. Cumulative primary estimand `δ(t) = WML_A(t) − WML_D(t)` over time.
7. Net excess return of W against one-way cost, with the break-even marked.
8. Mean return by formation group (monotonicity).

## 29. Review history
**Revision 2** (first review, twelve points): research question reframed; ladder A–E; special-session spans excluded from the primary; 12-1 and 30% justified; temporal design with a later period; costs split into evidenced and assumed; event-time timeline; one regime classification; field-by-field literature; "what is new"; power from stated assumptions.

**Revision 3** (second review):
| Point | Where resolved | Status |
|---|---|---|
| 1. Power for the actual primary estimand `δ(t)` | §2, §15 | Done. Stated honestly as a precision calculation; power cannot be established before results |
| 2. Practical-significance threshold | §27 | Done. ±0.10% per month kept, with three independent anchors and their limits |
| 3. Step A reproducible | B1.1, B1.2 | Done |
| 4. Step B reproducible | B1.3 | Done |
| 5. Targeted literature verification | A1 papers 3, 8, 9 and the targeted checks | Ranse verified in full. Raju & Chandrasekaran and Jain remain UNVERIFIED on the key points (B3) |
| 6. Temporal design explained | B3 | Done |
| 7. Regimes | §12 | Superseded in revision 4: removed from the study |
| 8. Unchanged elements | — | Unchanged: research question, ladder concept, RET-1.1 primary returns, special-session exclusion, 12-1, one-month holding, 30%, equal weight, delayed entry, Newey–West and bootstrap, cost separation, leakage tests |
| 9. No experiment | — | None run |

**Revision 4** (third review, wording only): A → E stated as a sequential decomposition, not causal identification (B1.5); paper 3 updated from reviewer-supplied evidence and positioned accurately (A1, A2); Jain kept unresolved with no exclusive-novelty claim (A1, A2); ±0.10% per month reworded as an ex-ante reference threshold (§27); corporate-action event date, availability date and research use separated (§21); regime analysis removed from the study (§12). No design element changed.

## 30. Known threats to validity
1. **Short samples.** 114 and 56 months. The existence test is underpowered (§15).
2. **The survivor baseline is our own construction.** Step A imitates a common shortcut but is not a vendor's actual pipeline. A real vendor series may err differently.
3. **Sequential decomposition, not causal identification.** Step sizes depend on order and interactions (B1.5). R-order shows the sensitivity; it does not remove it.
4. **Bias is time-varying by construction.** The survivor list is fixed at 2026, so its distance from each month differs.
5. **Price returns, not total returns.** No dividends.
6. **No market capitalisation.** Equal weight only; no size control; no factor alphas.
7. **Liquid large-cap universe.** Survivorship and data-quality problems are smaller here than in small caps, so the measured distortion is likely a lower bound for the wider market.
8. **Execution cost is assumed.** Scenarios and a break-even, not measurement.
9. **Short leg not implementable.** WML is a factor return.
10. **Data-quality exclusions remove extreme movers** (jumps above 1.4×, unresolved events), which may weaken measured momentum at step D. This is part of what C − D measures, and it must be described as such, not as "truth".
11. **Corporate-action source incomplete.** Some real bonuses and splits have no NSE record.
12. **Delisting returns assumed.**
13. **Special-session days excluded** from the primary; weekday special sessions not separated (Phase 2.1 calendar limit).
14. **Prior exposure.** The published record to 2021 and market history after it are known to us.
15. **Literature not fully verified.** See blocker B3 in §32.

## 31. Decisions for the reviewer
- **D1.** Accept the December 2021 boundary and its stated limits (B3).
- **D2.** Accept the ±0.10% per month reference threshold as worded in §27.
- **D3.** Accept that H1 is reported as a precision calculation, with the blinded precision step, and no claim of adequate power (§15).
- **D4.** Accept the exact step-A and step-B algorithms (B1.2, B1.3).

## 32. Open items at the freeze (to be closed in Phase 3B before any return is computed)
| ID | Blocker | Affects | Needed to close it |
|---|---|---|---|
| **B2** | No archived source for delivery STT, delivery stamp duty, depository charge, delivery brokerage; historical STT rate unverified | Step E; H4; anchor 1 of §27. **Not** the primary estimand (A → D is gross) | Archive official sources; write a delivery cost-schedule file |
| **B3** | Full text not obtained for Jain (momentum-specific experiment?) and for papers 2, 4, 5, 6, 7; paper 3's exact constituent construction not fully verified | The wording of the positioning statement and the literature table. Already handled conservatively: no exclusive novelty is claimed against Jain | Library or author copies |
| **B4** | The reference Sharpe ratio of 0.5 (secondary test H3 only) and the standard international references are cited from memory | H3 power statement; reference list | Check against the originals |
| **B5** | Decisions D1–D4 and explicit approval to freeze | Freeze | **Closed:** revision 4 approved as written and frozen, 2026-10-05 |

Closed: B1 (NSE index archive) — no longer needed, because regime analysis is outside the study scope (§12). Also closed earlier: step-A and step-B definitions; power design for the primary estimand; reference threshold; Ranse verification.

Not blockers, but stated: slippage scenarios are assumptions by design; no risk-free rate is archived; the power of H1 is unknown until the blinded precision step; the coverage of the NSE broadcast-date field is unchecked.

## 33. References
- Abdi, F., & Ranaldo, A. (2017). A simple estimation of bid-ask spreads from daily close, high, and low prices. *Review of Financial Studies*.
- Agarwalla, S. K., Jacob, J., & Varma, J. R. (2013). Four factor model in Indian equities market. IIM Ahmedabad W.P. 2013-09-05 (revised 2014). Published as: Size, value, and momentum in Indian equities, *Vikalpa* (2017). Data library: faculty.iima.ac.in/iffm/Indian-Fama-French-Momentum/.
- Bailey, D., & López de Prado, M. (2014). The deflated Sharpe ratio. *Journal of Portfolio Management*.
- Barroso, P., & Santa-Clara, P. (2015). Momentum has its moments. *Journal of Financial Economics*.
- Carhart, M. (1997). On persistence in mutual fund performance. *Journal of Finance*.
- Chui, A., Ranganathan, K., Rohit, A., & Veeraraghavan, M. (2023). Momentum, reversals and liquidity: Indian evidence. *Pacific-Basin Finance Journal*, 82, 102193.
- Corwin, S., & Schultz, P. (2012). A simple way to estimate bid-ask spreads from daily high and low prices. *Journal of Finance*.
- Das, S., & Barai, P. (2016). Size, value and momentum in stock returns: evidence from India. *Macroeconomics and Finance in Emerging Market Economies*, 9(3), 284–302.
- Fama, E., & French, K. (2012). Size, value, and momentum in international stock returns. *Journal of Financial Economics*.
- Garg, A. K., & Varshney, P. (2015). Momentum effect in Indian stock market: a sectoral study. *Global Business Review*, 16(3), 494–510.
- Harvey, C., Liu, Y., & Zhu, H. (2016). …and the cross-section of expected returns. *Review of Financial Studies*.
- Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics*.
- Jain, A. (2026). Survivorship bias in Indian equities is not a number: vintage- and filter-dependence in point-in-time universes. SSRN 7099378.
- Jegadeesh, N. (1990). Evidence of predictable behavior of security returns. *Journal of Finance*.
- Jegadeesh, N., & Titman, S. (1993). Returns to buying winners and selling losers. *Journal of Finance*.
- Korajczyk, R., & Sadka, R. (2004). Are momentum profits robust to trading costs? *Journal of Finance*.
- Lesmond, D., Schill, M., & Zhou, C. (2004). The illusory nature of momentum profits. *Journal of Financial Economics*.
- McLean, R. D., & Pontiff, J. (2016). Does academic research destroy stock return predictability? *Journal of Finance*.
- Newey, W., & West, K. (1987). A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix. *Econometrica*.
- Nigam, A., & Pandey, P. (2023). How smart is a momentum strategy? An empirical study of Indian equities. *Algorithmic Finance*, 10, 21–37.
- Patton, A., & Timmermann, A. (2010). Monotonicity in asset returns. *Journal of Financial Economics*.
- Politis, D., & Romano, J. (1994). The stationary bootstrap. *Journal of the American Statistical Association*.
- Raju, R. (2023). An examination of number of holdings and universe size in momentum strategies: evidence from India. SSRN 4453680.
- Raju, R., & Chandrasekaran, A. (2019). Implementing a systematic long-only momentum strategy: evidence from India. SSRN 3510433.
- Ranse, H. S. (2025). Survivorship bias in emerging market small-cap indices: evidence from India's NIFTY Smallcap 250. SSRN 5833162; arXiv 2603.19380.
- Romano, J., & Wolf, M. (2005). Stepwise multiple testing as formalized data snooping. *Econometrica*.
- Shumway, T. (1997). The delisting bias in CRSP data. *Journal of Finance*.
- White, H. (2000). A reality check for data snooping. *Econometrica*.

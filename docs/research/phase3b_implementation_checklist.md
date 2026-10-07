# Phase 3B — implementation checklist for S2-MOM-v1 (2026-10-05)

**Frozen protocol:** `docs/research/phase3a_momentum_protocol.md`, SHA-256 `f1abd954f698307f7aafe234c5d5c9f1681ccc5aadb9cb21e9f8e34d47abd838`, freeze commit `7d4cb6d`. Section numbers below refer to it.

**Status of the experiment:** NOT RUN. No real mean, Sharpe ratio, p-value of a momentum portfolio, drawdown, turnover result or economic conclusion exists. Only the pre-run checks were executed on real data; they store pass/fail and counts. The runner still refuses the blinded, primary and confirmation modes for the reasons listed at the end.

**Updated after the third review (2026-10-05):** S2-MOM-v1 stays frozen (reviewer option 1); no protocol text changed.

**Verdict: not safe to run yet.** See "What blocks a run" at the end.

Legend: **DONE** = implemented and covered by synthetic tests. **PARTIAL** = some of it exists. **MISSING** = not implemented. **BLOCKED** = implemented but cannot be used yet.

## A. Required for the primary experiment

| # | Requirement | Protocol | Status | Note |
|---|---|---|---|---|
| A1 | Protocol hash check; registry record; fail-closed runner | header, B3 | DONE | `src/stage3/protocol.py`, `scripts/run_s2_mom.py` |
| A2 | Deterministic inputs with provenance and hashes | §4 | DONE | `scripts/build_stage3.py`; rebuild byte-identical. Code hashes in the manifest predate today's edits and refresh on the next build |
| A3 | Calendar: selection dates, 12-1 window, skip month, delayed entry, exit session | §7–§9, B2 | DONE | 170 months, 114 + 56 |
| A4 | Step A (fixed survivor list at 2026-09-30, unvalidated factors, no flags) | B1.2 | DONE | |
| A5 | Step B (same pool, liquidity at each date) | B1.3 | DONE | |
| A6 | Step C (UNIV-1 members; delisting rule) | B1.4, §22 | DONE | §22 applied literally (see interpretations below) |
| A7 | Step D (RET-1.1 research-grade; special-session days excluded; flagged-day rule) | §20–§21 | DONE | §20(b) fill = simple mean; stock stays a member; every fill is logged |
| A8 | Top/bottom 30%, equal weight, ties, benchmark | §10, §24 | DONE | |
| A9 | Paired estimand δ(t) = WML_A − WML_D, unpaired months kept with a reason | §2 | DONE | |
| A10 | H1: Newey–West lag 4, two-sided, standard normal | §15 | DONE | Reviewer decision 5 |
| A11 | Stationary bootstrap, 10,000 resamples, seed 20261005 | §15 | DONE | Reviewer decision 6 |
| A12 | H1 decision rules against ±0.10% per month | §27 | DONE | |
| A13 | Blinded precision step | §15 | DONE, not generated | Runs only after the checks pass; not generated in this pass |
| A14 | Pre-result checks **on the real pipeline**: perturbation, truncation, random-ranking placebo, A/D pairing, sample boundary, protocol hash, input and code hashes | B2, §25 | **DONE and PASSED** | `python3 scripts/run_s2_mom.py checks`; artifacts in `data/stage3/s2_mom_v1/checks/`. Results below |
| A14b | Audit trail of every fill, booked gap return and delisting return, with the RET-1.1 status as reason | reviewer | DONE | Written with each run as `*_events.csv` |
| A15 | Stage 2 rebuild passes all 150 checks before the study runs | §4, §25 | BLOCKED | Needs about 10 GB of memory; 1.4 GB of disk is free. Stage 3 loaders do hash-check every RET-1.1 file and UNIV-1 on each load |
| A16 | "Not reliable" labels: any month under 100 rankable stocks or average under 150; more than 5% filled stock-days; sign or significance change under span, gap, missing-day or delisting sensitivity | §25 | DONE | Six labelled sensitivity variants and the fixed labels; H4 part pending with cost evidence. See `phase3b_final_prerun_audit.md` §9 |
| A16b | Holdings and end-weights saved with each run | reviewer | DONE | `*_holdings.csv`; turnover reproduced from the saved file in a test |
| A17 | Ladder table for every step: mean, volatility, Sharpe-type ratio, t-statistic, maximum drawdown, turnover, stock count, economic conclusion | B1.5, §14 | PARTIAL | Turnover exists only for step D; information ratio against the benchmark for long-only portfolios is missing |
| A18 | Step E: evidenced charges + slippage S0–S4; gross, net, break-even | §13, §23 | PENDING, not blocking the gross primary run | Five rates have no archived evidence. The run writes `COST-EVIDENCE-PENDING`; cost functions still refuse any missing rate |
| A19 | Chronological OOS run with the same code hash; confirmation rule (confirmed / consistent / not confirmed) | B3 | PARTIAL | Run order and code-hash check exist; the three-way classification is missing |
| A20 | Trial log; deflated Sharpe ratio of WML_D with the trial count | §17 | PARTIAL | Trial log exists; deflated Sharpe ratio not wired in |

## B. Required secondary tests (explicitly in the frozen protocol)

| # | Requirement | Protocol | Status |
|---|---|---|---|
| B1 | H2a–H2c: step differences A−B, B−C, C−D, two-sided | §3 | PARTIAL — means and tests computed; Holm correction and reading against ±0.10% missing |
| B2 | H2d: W_A − W_D > 0, one-sided | §3 | MISSING |
| B3 | Holm step-down for H2a–H2d; Benjamini–Hochberg q-values beside every secondary p-value | §17 | MISSING |
| B4 | H3: mean WML_D > 0, one-sided; "contradicted" rule on the Sharpe interval; t > 3 reported | §3, §17, §27 | PARTIAL — series and t-statistic exist; the one-sided record and rules are missing |
| B5 | H4: W_E − Benchmark_E > 0 under S0, tested only if H3 is rejected | §3 | PARTIAL — net excess computed; gating and one-sided record missing; blocked by cost evidence |
| B6 | H5: WML in rank 1–200 versus rank 201–500 | §3, §11 | MISSING — the 201–500 universe is not built |
| B7 | A − E total distortion of the investable result | B1.5 | MISSING |
| B8 | Capacity: portfolio size at 1% and 5% of median daily traded value | §13 | MISSING |

## C. Required fixed robustness analyses (§16)

| ID | Analysis | Status |
|---|---|---|
| R-order | Reverse-order ladder | DONE |
| R-JK | J ∈ {3,6,9,12} × K ∈ {1,3,6,12}; Romano–Wolf and White reality-check p-values | MISSING |
| R-skip | No skip month | MISSING |
| R-bp | Quintiles; deciles | MISSING (the breakpoint is a parameter of the sort function; not wired) |
| R-wt | Liquidity-proportional weights | MISSING |
| R-entry | Entry at the close of the selection date | MISSING |
| R-cost | Brokerage 0.03%; spreads estimated from high, low and close | MISSING |
| R-half | Two halves of the primary sample | MISSING |
| R-pool | Pooled 170 months, descriptive | MISSING |
| R-span | Special-session spans with the raw two-session return | MISSING |
| R-gap | Multi-session gaps with the raw gap return | MISSING |
| R-miss | Holding-period missing days: raw return; zero | MISSING |
| R-delist | Delisting return 0% for all; −100% for non-voluntary | MISSING (the delisting return is already an input array) |
| R-mono | Monotonicity across formation groups (Patton & Timmermann) | MISSING |
| R-ext | Correlation with the public IIMA momentum factor | MISSING; the protocol makes it conditional on archiving that file |
| — | Tables 1–12 and figures 1–8 of §28 | MISSING |

## D. Optional future work (not required by the frozen protocol)

- Regime-conditioned analysis (§12 puts it outside the study).
- Prospective months after 2026-09-30.
- A futures-based short leg.
- Alpha against the public IIMA factors (labelled exploratory in §24).

## Interpretations of the frozen protocol (reviewer, 2026-10-05; recorded in the registry; no protocol text changed)

| Point | Interpretation in force |
|---|---|
| Sample boundary | Protocol exit sessions: primary ends 2022-01-03, OOS ends 2026-09-01; 114 + 56 months; nothing after 2026-09-30 |
| §20(b) flagged day in step D | The stock stays in the portfolio. Its return that day is the **simple arithmetic mean** of the same-day research-grade returns of the other stocks in that portfolio. Not value-weighted, never zero by default. If no other stock has a return that day there is nothing to average; the day adds nothing and is logged separately (`NEUTRAL_FILL_NO_OTHER_STOCKS`) |
| §22 missed exit | Literal, in steps C and D alike: carried at the last price to the exit session; if the stock trades again later, the realised gap return (last price to the next traded price) is booked in the month of the exit; if it never trades again, the delisting return applies |
| §22 delisting return | **Already specified by the frozen text**: "Voluntary Delisting" → 0%; "Compulsory Delisting", "Delisting - Liquidation", or no evidence (`ENDED_UNEXPLAINED`) → −30%. The ID-1 data contain exactly these three delisting types, so every case is covered |
| §22 horizon | "Trades again later" and "never trades again" are decided from all research data up to 2026-09-30. Only the one resumption row of the affected stock can reach past the exit session; a test shows every other later price is ignored |
| p-value | Standard normal for the Newey–West test, lag 4 |
| Bootstrap seed | 20261005 |

The earlier reviewer decisions 2–4 (drop the stock-month; never look past the exit session) are withdrawn: they would have amended §20(b) and §22.

**Consequences of the literal §22 reading — stated so they are not a surprise later (structural counts, no returns):**
- 70 member-months have no price at the exit session (51 primary, 19 OOS), 63 entities.
- 41 trade again later. Median wait 74 calendar days, longest 266. Two primary-sample cases resume after 2022-01-03, so the primary sample uses a later price for those two stocks, as §22 prescribes.
- All 41 resumption rows are `MULTI_SESSION_GAP`. None carries a parsed bonus/split factor (if one ever did, step D stops). 29 are clean. **12 are flagged: 2 carry a scheme/demerger record and 10 are beyond the 1.4× jump bound.** Literal §22 books their raw gap return in step D as well. They are counted and logged as `EXIT_GAP_BOOKED_FLAGGED_ROW`.
- 29 member-months (28 entities) never trade again: 26 entities are `ENDED_UNEXPLAINED` → −30%; 2 are voluntary delistings → 0%. A stock that stops shortly before 2026-09-30 is treated the same way.
- A booked gap return is not counted again if the same stock is held the following month. This follows from "booked in the month of the exit date".

## Real-data pre-run checks (run 2026-10-05; pass/fail and counts only)

| Check | Primary (114 months) | OOS (56 months) |
|---|---|---|
| Protocol SHA-256; registry record; input and code hashes | pass | pass |
| A/D pairing: every month computable for both | 114 of 114 | 56 of 56 |
| Boundary: last exit session; last session in memory | 2022-01-03; 2026-09-30 | 2026-09-01; 2026-09-30 |
| Perturbation of everything after 5 selection dates | pass | pass |
| Truncation at 5 selection dates | pass | pass |
| Random-ranking placebo (seed 20261005): p-value of the random WML mean | 0.4725, pass | **0.054, pass by a narrow margin** |
| Placebo ranks differ from momentum ranks | all 114 months | all 56 months |
| Rankable stocks in step D: minimum / mean | 180 / 187.8 | 180 / 187.3 |

- The placebo p-value is a statistic of **random** portfolios. It says nothing about momentum.
- The OOS placebo is close to the 5% line. One test in twenty lands there by chance; it is recorded, not explained away.

## Delivery cost evidence (§13 class 1)

No rate is invented. Each null rate makes every cost call refuse.

| Input | Rate expected by the protocol | Period needed | Authoritative source needed | Evidence status |
|---|---|---|---|---|
| Securities transaction tax, delivery buy | 0.100% | 2012-07 → 2026-09 (protocol notes a reported cut from 0.125% on 2012-07-01) | Finance Act provisions on STT with amendments, or the Income Tax Department / exchange circular stating the delivery rate and its effective date | **Missing** |
| Securities transaction tax, delivery sell | 0.100% | same | same | **Missing** |
| Stamp duty, delivery buy | 0.015% | protocol: uniform national rate from July 2020, state-wise before | Government notification of the uniform stamp-duty rates, or the exchange circular. For earlier years the frozen rule applies: current rate for the whole sample, labelled an assumption | **Missing** |
| Brokerage, delivery | 0 | whole sample (assumption) | Broker charge schedule page for delivery trades, archived with date | **Missing** |
| Depository charge per stock sold | flat rupee fee | whole sample (assumption) | Depository or broker tariff, archived with date | **Missing** |
| Exchange transaction charge + IPFT | 0.00307% | current rate, applied to the whole sample | NSE circular NSE/FA/73061 | Archived (`docs/evidence/`) |
| SEBI turnover fee | 0.0001% | current rate | Broker schedules | Archived (`docs/evidence/cost_sources.md`) |
| GST | 18% on brokerage + exchange + SEBI | current rate | Broker schedules | Archived (same file) |

Costs affect step E and H4 only. The primary estimand δ = WML_A − WML_D is gross and does not use them.

## What blocks a run

1. **Stage 2 rebuild check (A15).** Not run: about 1.3 GB of disk is free. Wait for the macOS update state to change, re-check disk read-only, then consider it.
2. **Delivery cost evidence** (five inputs above) for step E and H4.
3. **Primary-run items not finished:** A16 reliability labels and sensitivity comparison; A17 full ladder table (turnover for steps A–C, information ratio); A19 confirmation classification; A20 deflated Sharpe ratio.
4. **Secondary analyses** marked MISSING or PARTIAL in section B.
5. **Fixed robustness analyses** marked MISSING in section C (14 of 15), and the tables and figures.

No protocol ambiguity remains open. The consequences of the literal readings are listed above for the reviewer's information.

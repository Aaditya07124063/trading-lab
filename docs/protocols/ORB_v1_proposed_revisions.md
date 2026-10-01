# ORB v1 — proposed revisions for review (NOT APPLIED)

**Date:** 2026-10-01
**Status:** PROPOSAL. `docs/protocols/ORB_v1.md` is unchanged and remains DRAFT. Nothing here takes effect until Aaditya approves it item by item.

**Basis:**
- `docs/literature/SSRN_5198458_record.md`
- `docs/literature/ORB_literature_review.md`
- `docs/literature/SSRN_5198458_vs_ORB_v1.md`
- `docs/literature/ORB_research_gap_analysis.md`
- the current code (`src/intraday/orb.py`, `engine.py`, `data.py`)

**Holdout:** starts 2026-10-01 and is unchanged. **No holdout observation was opened.** See §3 for the leakage check.

**Decision codes:**
- **KEEP** — no change proposed.
- **CLARIFY** — wording only; behaviour unchanged.
- **CHANGE** — rule, test or benchmark change; needs approval.
- **ADD** — new pre-specified element; needs approval.

## 1. Item-by-item review

Every item follows the same five steps: current rule → evidence → proposal → scientific reason → consequence for interpretation.

### R1. ORB window — **KEEP**
- **Current:** 30 min (09:15 and 09:30 bars on 15-min data).
- **Evidence:**
  - A1 favours 5-min (in-sample, zero cost, single stock).
  - A5: 5-min ≫ 15 > 60 > 30-min (US, in-sample, filter selected ex post).
  - A3: the best probing time differs by market (selected in-sample).
- **Proposal:** keep ORB-30.
- **Reason:**
  - The literature preferences come from in-sample specification searches.
  - Our 15-min data cannot form a 5-min range.
  - Switching windows now would be performance-motivated selection.
- **Consequence:** the result is for ORB-30 only. A5 suggests ORB-30 is a comparatively weak variant in the US, so a null result for ORB-30 does **not** generalise to "ORB fails in India".

### R2. Breakout confirmation — **KEEP**
- **Current:** a completed-bar close beyond OR_HIGH / OR_LOW.
- **Evidence:** A1 uses the same confirmation. A5 uses stop orders at the level (intrabar).
- **Proposal:** keep.
- **Reason:** close-confirmation on completed bars is point-in-time safe and executable.
- **Consequence:** entries happen later than with stop orders. The estimate is for close-confirmed ORB.

### R3. Entry execution — **KEEP + CLARIFY**
- **Current:** the next bar's open plus slippage.
- **Evidence:** A1 fills at the signal close, which cannot actually be achieved.
- **Proposal:**
  - Keep.
  - **Clarify** that the open of the 15-min bar is the first trade in that bar on Yahoo data, not a quote.
  - **Clarify** that slippage is applied adversely on both sides.
- **Reason:** realistic timing.
- **Consequence:** this is the reason our estimate is executable; A1's is not.

### R4. Entry cutoff — **KEEP**
- **Current:** no fills after 14:30.
- **Proposal:** keep.
- **Reason:** it ensures a minimum holding window.
- **Consequence:** none.

### R5. One trade per day — **KEEP + CLARIFY**
- **Current:** the first signal only. Both A1 and the code do this.
- **Proposal:**
  - Keep.
  - **Clarify** that after a long signal, a later downside break is ignored, and vice versa. The code's `done` flag already does this.
- **Consequence:** none.

### R6. Long/short handling — **KEEP + CLARIFY**
- **Current:** C (long/short) is primary; B (long-only) is secondary.
- **Proposal:**
  - Keep.
  - **Clarify** that shorts are intraday cash-market (MIS) shorts, assumed always borrowable intraday.
  - Report long and short legs separately as **descriptive**, not confirmatory. A1's direction split shows how drift-dependent the legs are.
- **Consequence:** direction results are not used to accept or reject H1.

### R7. Forced exit — **CHANGE (needs approval)**
- **Current:** square off at the **close** of the 15:15 bar, about 15:29:59 (`engine.py`, `square_off="15:15"`). Benchmark A uses the same price.
- **Evidence:**
  - Zerodha's equity MIS auto-square-off is **15:25**, changed from 15:20. Source: Zerodha announcement on X and Threads; Trading Q&A "MIS Auto Square-off Timings Extended". The announcement date was not recorded; re-verify on the support page before freeze.
  - An MIS position, and in particular an intraday cash short, cannot be held to 15:29:59.
- **Proposal:** exit at the **open of the 15:15 bar** (≈ 15:15), for C, B, A, D, D′ and E alike. Sessions that have the 15:15 bar but not the 15:30 tail stay tradable.
- **Alternatives for your decision:**
  - (a) 15:15 open [recommended];
  - (b) close of the 15:00 bar (= 15:14:59, almost the same);
  - (c) keep 15:29:59 and justify it with a CNC/delivery long and a separate MIS short. Not recommended: it is asymmetric and complex.
- **Reason:** executability. This is not a performance argument; no ORB data was inspected to choose it.
- **Consequence:**
  - The holding period shortens by about 15 minutes, and the closing-auction period is excluded.
  - It requires a code change in `engine.py` before freeze, and a regression test.
  - The development-period exposure status is unchanged.

### R8. Transaction costs — **KEEP (re-verify)**
- **Current:** Zerodha/Upstox schedules dated 2026-09-30 and the NSE circular. Primary scenario Z-5 at Rs 1 lakh.
- **Evidence:** A1 uses zero cost. B1 shows costs are material for Indian intraday traders.
- **Proposal:**
  - Keep the schedules as they are.
  - **Add** a pre-freeze check that no published schedule changed between 2026-09-30 and the freeze date. If one did, record it as a dated amendment; do not silently update.
  - The R7 auto-square-off penalty (Rs 50 + GST) does not apply if exits are placed before 15:25. State this.
- **Consequence:** none.

### R9. Slippage — **KEEP + ADD a reporting rule**
- **Current:** a grid of 0/2/5/10/20 bps per side. Primary 5 bps (proposed, not yet approved).
- **Evidence:**
  - Neither A1 nor A5 models slippage.
  - No source calibrates NSE large-cap slippage for 15-min-bar market orders.
- **Proposal:**
  - Keep the grid.
  - **You still need to approve the primary 5 bps** (open item since 2026-09-30).
  - **Add** that break-even slippage is reported with its bootstrap CI.
- **Consequence:** headline conclusions are conditional on 5 bps. Break-even slippage lets readers re-scale the result.

### R10. Benchmark — **CHANGE (needs approval)**
- **Current:** H1 requires ORB > 0 **and** > A (open-to-close long) **and** > D.
- **Evidence:**
  - In A1, BH fell 37 %; the ORB−BH difference was mostly the benchmark's loss.
  - Comparing a mostly-flat long/short strategy with a long-only benchmark measures drift, not edge.
- **Proposal:**
  - **Primary H1:** mean net daily return of the portfolio > 0 (see R13).
  - **A becomes descriptive context**, still reported, with its exit aligned to R7.
  - F stays as context.
- **Reason:** to test the strategy's own edge, not the sign of market drift during the holdout.
- **Consequence:** H1 can no longer be "satisfied" or "failed" because of market direction.

### R11. Random baselines — **CHANGE/ADD (needs approval)**
- **Current:**
  - D: random direction and uniform random entry in [09:45, 14:30] on ORB trade days, exit 15:15, 10,000 draws, seed 20260930.
  - E: sign-randomisation.
- **Evidence:** A2 tests ORB against a fair-game / random-trading null. A1 has no random baseline.
- **Proposal:**
  - **D′ (ADD):** same days, random direction, **entry bar = the actual ORB entry bar of that stock-day**; same exit and costs. This isolates *direction* at matched exposure and time.
  - **D (KEEP, secondary):** it measures *timing plus direction* against generic intraday exposure.
  - **E (CLARIFY):** flip the signs of **gross** trade returns, then subtract costs (costs do not change sign). Flip whole dates jointly across stocks, so cross-sectional dependence is preserved. One-sided p = (1 + #{draws ≥ observed}) / (1 + B).
  - D′ is the permutation counterpart of E and may be dropped if you prefer one direction test. **Recommendation:** keep E, add D′ only if you want a simulation-based check of E.
- **Consequence:** the confirmatory secondary family is E (direction content) and D (vs generic exposure). D′ is descriptive.

### R12. Risk-free treatment — **CLARIFY**
- **Current:** not stated. Neither A1 nor our draft treats it.
- **Proposal:**
  - State that intraday sleeves earn **no interest on idle capital**, and that returns and Sharpe are computed on raw daily returns (rf = 0).
  - Report a sensitivity check of Sharpe with rf = the 91-day T-bill yield, from a source fixed now.
- **Reason:** intraday cash is idle overnight; this is conservative and transparent.
- **Consequence:** small effect on Sharpe; stated rather than implicit.

### R13. Statistical testing — **CHANGE (needs approval)**
- **Current:** stationary bootstrap CIs (block rule "stated before viewing holdout"); D and E; Holm across instruments; deflated Sharpe; power analysis. No α, no sidedness, no primary unit, no decision rule.
- **Evidence:**
  - A1's uncentred i.i.d. bootstrap returns p ≈ 0.5 whatever the effect (record §7.1).
  - A1 itself flags the dependence it ignores.
- **Proposal:**
  1. **Primary unit:** the equal-weight daily return across all 50 sleeves. A sleeve with no trade, or with no data, contributes 0 %. Net of costs, scenario Z-5.
  2. **Primary test:** H0: μ ≤ 0 vs H1: μ > 0. One-sided, α = 0.05.
  3. **Method:** stationary bootstrap of **dates** (cross-section kept intact), centred under H0. B = 10,000; seed fixed in the protocol. 95 % percentile CI. Studentised version as sensitivity.
  4. **Block length:** Politis–White (2004) automatic selection (with the Patton et al. 2009 correction) computed **on development data only** (pre-2026-10-01). The value is frozen in the protocol. Sensitivity at ½× and 2×.
  5. **Effect sizes:**
     - mean bps/day with CI;
     - annualised Sharpe with a Lo (2002)-adjusted SE;
     - break-even slippage with CI.
  6. **Pre-registered verdict:**
     - **POSITIVE:** CI lower bound > 0.
     - **NEGATIVE:** CI upper bound < δ, with δ fixed before freeze (proposal: δ = 2 bps/day).
     - **INCONCLUSIVE:** anything else.
  7. **Implementation guard:** a unit test that p is ≈ U(0,1) under a simulated null and → 0 under a strong simulated effect, plus a test that the bootstrap is null-centred.
  8. **Power:** minimum detectable effect at 80 % power for the portfolio endpoint, computed from development data and recorded before freeze. If the minimum detectable effect is > δ, state in advance that "INCONCLUSIVE" is the expected likely outcome under a small true edge.
- **Reason:** valid inference with one primary endpoint, so a significant result cannot be manufactured by choosing among endpoints.
- **Consequence:**
  - Per-stock results become secondary.
  - "Not significant" is distinguished from "evidence of no effect".
  - Given A5's weak ORB-30 results in the US, INCONCLUSIVE is a realistic outcome and should be presented as such.

### R14. Multiple testing — **CHANGE (needs approval)**
- **Current:** Holm across instruments; deflated Sharpe using `registry/trials.jsonl`.
- **Evidence:** A1 ran 18+ specifications without control. A5's filter was chosen ex post.
- **Proposal:**
  - **Family 1 (confirmatory):** the primary test alone; no adjustment.
  - **Family 2 (confirmatory secondary):** ORB vs E and ORB vs D. Holm at α = 0.05.
  - **Family 3 (exploratory):** 50 per-stock tests, Romano–Wolf StepM (or Holm) at α = 0.05. Labelled exploratory.
  - **Cost and slippage grid, long-only B, regimes:** descriptive, no p-values claimed as confirmatory.
  - **Deflated Sharpe:**
    - trial count = all ORB-family entries in `registry/experiments.jsonl` plus `registry/trials.jsonl`, which does not yet exist because no backtest has run since the trial logger was added;
    - count fixed at freeze;
    - the RELIANCE ORB-30 and ORB-60 exposures included.
- **Consequence:** a clear separation of confirmatory and exploratory claims.

### R15. Regime analysis — **CLARIFY**
- **Current:** volatility (prior 20-session realised vol vs expanding median) and trend (sign of prior 20-session return), from past data only.
- **Proposal:**
  - Keep the definitions.
  - Label the analysis **exploratory and descriptive**.
  - Fix the reference series: the NIFTY 50 index daily data for market regimes; the stock's own data for stock regimes.
  - The expanding median starts from development data, so no holdout data is used at the regime boundary on day 1.
  - Report the count of sessions per regime.
- **Reason:** about 250 sessions give few regime switches; confirmatory claims are not supportable (A1 makes the same point about one year).
- **Consequence:** no "robust across regimes" claim.

### R16. OOS methodology — **CHANGE (needs approval)**
- **Current:** "≥ 250 sessions … target ≈ Oct 2027"; evaluated once.
- **Proposal:**
  - **Exactly the first 250 NSE trading sessions on or after 2026-10-01**, by the NSE holiday calendar (not by data availability).
  - One evaluation after the last session's collection is complete.
  - No interim outcome looks.
  - Collector health (row counts, rejections) may be monitored. P&L, signals and returns may not.
- **Reason:** removes optional stopping.
- **Consequence:** the end date is fixed in advance; record it in the protocol at freeze.

### R17. Sample definition and missing-bar handling — **CLARIFY / ADD (needs approval)**
- **Current code behaviour (to be written into the protocol):**
  - **Opening-range bar missing:** day skipped (`orb.py`).
  - **15:15 bar missing:** session not traded, and reported (`engine.py` `_tradable_sessions`).
  - **Other missing bars:** the signal scan uses the bars present; the entry fills at the next *available* bar's open.
- **Evidence:** the collector log shows Yahoo omits isolated 15-min bars in about 4–15 of 42 sessions per stock (pre-holdout data).
- **Proposal:**
  - Write the three rules above into the protocol.
  - **ADD:** if the gap between the signal bar and the next available bar is > 15 min, no trade (a stale fill otherwise).
  - **ADD:** a tradable stock-session requires the two opening-range bars and the exit bar.
  - **ADD:** report affected stock-sessions per stock.
  - **ADD:** sensitivity check excluding all stock-sessions with any missing bar.
  - **ADD (data-integrity only):** compare each holdout stock-session's 15-min open/high/low/close against the NSE bhavcopy. Flag only, never correct. Sensitivity check excludes flagged sessions.
  - **ADD:** corporate and universe events:
    - a frozen name stays in the universe through suspension, demerger or symbol change;
    - symbol mappings are logged with evidence;
    - no-data sessions contribute 0 % to the portfolio and are counted;
    - index changes are ignored.
  - **ADD:** a pre-stated threshold: if > 10 % of stock-sessions in the holdout are untradable due to data gaps, the evaluation is still run but labelled DATA-LIMITED.
- **Reason:** gap handling must be fixed before outcomes exist. Otherwise it becomes a researcher degree of freedom.
- **Consequence:** results are conditional on Yahoo coverage; this is made explicit.

### R18. Sizing — **KEEP + CLARIFY**
- **Current:** 100 % of the Rs 1 lakh sleeve, integer shares, no leverage. **Capital still needs your approval** (open since 2026-09-30).
- **Proposal:**
  - Keep.
  - Report deployed notional per trade.
  - Returns are on sleeve capital (idle cash = 0 %).
  - A sensitivity check at Rs 10 lakh is already specified.
- **Consequence:** high-priced names deploy less than 100 % of the sleeve; reported, not adjusted.

### R19. Documentation fixes — **CLARIFY**
- §8 open items 2 and 3 are resolved:
  - universe: frozen NIFTY 50, commit fc3b26d;
  - provider: Yahoo via the logged collector, commits e998fc8 and 38c4da5.
- §8 item 4 (literature) is done to the extent recorded above.
- §5 should cite the frozen-universe file and checksum.
- §7 should name both registry files (R14).

## 2. Decisions required before ORB v1 can be frozen

| # | Decision | Recommendation |
|---|---|---|
| 1 | Primary slippage (R9) | 5 bps/side |
| 2 | Sleeve capital (R18) | Rs 1 lakh, with Rs 10 lakh sensitivity |
| 3 | Exit timing (R7) | 15:15 bar open, all strategies and benchmarks |
| 4 | Benchmark A demoted to context; H1 = net mean > 0 (R10) | Yes |
| 5 | Primary unit = equal-weight 50-sleeve daily return (R13.1) | Yes |
| 6 | α, sidedness, CI, 3-way verdict, δ (R13.2–6) | One-sided 0.05; 95 % CI; δ = 2 bps/day |
| 7 | Block-length rule (R13.4) | Politis–White on development data, with ½× and 2× sensitivity |
| 8 | Baselines: E clarified, D kept, D′ added or not (R11) | E + D confirmatory; D′ optional, descriptive |
| 9 | Multiple-testing families (R14) | As listed |
| 10 | Fixed 250-session holdout end (R16) | Yes |
| 11 | Missing-bar, stale-fill, DATA-LIMITED and corporate-event rules (R17) | As listed |
| 12 | Bhavcopy integrity check for holdout data (R17) | Yes (flag only) |
| 13 | Risk-free treatment (R12) | rf = 0 primary; T-bill sensitivity |
| 14 | Regime analysis exploratory (R15) | Yes |
| 15 | Approve the code changes these imply (R7 exit; statistics module with guard tests) before freeze | Required. Code at freeze must implement the protocol. |

After the approved changes are implemented and tested, a power analysis on development data (R13.8) must be run and recorded **before** freeze.

## 3. Holdout leakage check (Phase H)

| Check | Result |
|---|---|
| Did any proposal use data dated ≥ 2026-10-01? | **No.** No intraday file was opened in this session. The only numeric work was a synthetic simulation of A1's bootstrap. |
| Did any proposal use ORB performance at all (development or holdout)? | **No.** The proposals are justified by literature, executability (broker rules) and inference validity. |
| Was the collector log consulted? | Only the existing pre-holdout summary in `RESEARCH_LOG.md` (missing-bar frequency in 2026-08-03..09-30 data). It contains no returns. |
| Are any proposals favourable to ORB by construction? | R10 removes a benchmark that could make ORB look *better* (in falling markets) **or** *worse* (in rising markets). It is not directional. R7 changes the exit for every strategy and benchmark symmetrically. |
| Could later holdout viewing tempt changes? | R16 fixes the end date. R13 fixes the verdict rule. The data loader stays locked until FROZEN (`src/intraday/data.py`). |

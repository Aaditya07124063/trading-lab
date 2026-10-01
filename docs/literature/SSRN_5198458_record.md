# Research record — SSRN 5198458 (Wang & Gangwar)

**Read:** in full, 2026-10-01, from `docs/literature/SSRN 5198458.pdf`.
- **Local file:** kept locally, not committed (third-party copyright).
- **SHA-256:** `cfaa3f3681c73c16bf514f019dbc900908b5eb866c54a0c251e14e6069865379`.
- **Text:** all 13 pages: abstract, §1–7, references, author profile, acknowledgements.
- **Figures and equation:** all 5 figures and the one equation image were extracted and inspected.
- **Tables:** the paper has no numeric tables; results are reported in prose.
- **Notebooks:** the Google-Drive notebooks linked on p. 1 were **not** opened. They are an external, unauthenticated link, and the record relies only on the manuscript.

**Labels used:**
- **[A]** = stated by the authors.
- **[R]** = read off a figure by us.
- **[I]** = our inference or analysis, not a claim of the authors.

## 1. Bibliographic information

| Field | Content |
|---|---|
| Title | *Optimizing Intraday Breakout Strategies on the NSE: A Block-Based Performance Evaluation* [A] |
| Authors | Wang Chenxi; Siddhant Gangwar [A] |
| Affiliation | Both "MFE 2024, WorldQuant University" [A] |
| SSRN identifier | 5198458 |
| Publication / year | SSRN working paper. The PDF was created on 2025-03-01 (PDF metadata). No journal, conference or peer review is stated. The SSRN posting date has **not** been verified: the SSRN page returned HTTP 403 on 2026-09-30. |
| Manuscript | 13 pp., A4, written in MS Word. Link to Python notebooks on Google Drive. Acknowledges Tiberiu Stoica (guidance) and the "NSE Research Archive" (data support). |

## 2. Research design

| Field | Content |
|---|---|
| Research question | Whether ORB variants on an NSE stock outperform an open-to-close buy-and-hold by more than random variation, and how that varies with window, volume filter, holding period, sub-period and direction [A §1.1] |
| Hypotheses | **No formal hypotheses stated.** The implicit null is "mean daily ORB−BH difference is due to random luck" [A §3.6]. |
| Market / exchange | India, NSE cash equity [A] |
| Instrument / universe | Tata Motors only. No selection rationale is given [A §3.1]. |
| Sample period | "Approximately one year", "early 2024–early 2025" [A §4]. Figure axes span about **2023-12-20 → 2025-01-22** [R, all figures]. |
| Sampling frequency | 5-minute bars, [time, open, high, low, close, volume] [A §3.1] |
| Sample size | Number of sessions not reported; about 250–270 implied [I]. For the 5-min ORB: "approximately 141 short trades and 101 buy trades" [A §4.5]. Other variants: not reported. |
| Data source | Not stated in Methods. Acknowledgement: "NSE Research Archive for data support" [A]. |
| Preprocessing | Convert time to datetime, derive the date, group by date, sort, "remove duplicates or missing intervals if encountered" [A §3.1]. No rule for missing bars inside the opening range. No corporate-action treatment discussed. |

## 3. ORB methodology

| Field | Content |
|---|---|
| Opening range | ORB_High / ORB_Low = highest high / lowest low in the first X minutes, X ∈ {5, 15, 30} [A §3.2] |
| Breakout definition | A bar **close** above ORB_High (long) or below ORB_Low (short) [A §3.2] |
| Signal timing | At the close of the breakout bar [A] |
| Entry timing / price | **Not stated explicitly.** "On breakout, we look at returns for next N bars." [A]. The return is presumably measured from the breakout-bar close, i.e. a fill at the same price that generated the signal, with no delay [I]. |
| Exit timing / holding period | After N ∈ {2, 3, 5} bars (10–25 min) [A §3.2]. §3.8 instead treats "each daily return as the entire day's 'bullish trade'" [A]. **Fig 4.3 shows the N = 2, 3 and 5 curves exactly overlapping, and they equal the 5-min curve in Fig 4.1** [R]. So either N had no effect in the code or the stated exit rule was not what was implemented [I]. The exit rule as implemented cannot be determined from the manuscript. |
| Long rules | Close > ORB_High → long [A] |
| Short rules | Close < ORB_Low → short, symmetric [A]. Indian cash-market shorting constraints (intraday only, broker square-off) are not discussed. |
| Multiple breakouts | Only the first breakout of the day is used; later ones are ignored "to avoid excessive transactions" [A §3.2]. |
| No-trade days | ORB return set to **0 %** [A §3.5], so Diff = −BH on those days. |
| Volume filter | Optional: breakout-bar volume ≥ k × "average_volume_for_that_day", k ∈ {1.2, 1.5} [A §3.3]. The day's average volume is only known at the close, so the filter **uses future information** as written [I]. |
| Position sizing | Not stated. Returns-based, implicitly 1× notional, compounded daily [I from §3.4, figures]. |

## 4. Evaluation

| Field | Content |
|---|---|
| Benchmark | Daily open-to-close long: BH_daily = close_end / open_start − 1 (equation image p. 4), compounded [A] |
| Transaction costs, brokerage, taxes/fees | **None.** Acknowledged as "Zero Cost Factor" (§5.5) and as a limitation (§6.2) [A]. |
| Slippage | **None** [A] |
| Risk-free rate | Not mentioned [A] |
| Performance metrics | Daily mean difference, p-value, final cumulative return (ORB vs BH), "excess gain", days. Hit ratio only for the direction split (≈ 50–55 %). Sharpe, Sortino and drawdown are cited in §2.4 but **not reported**. [A] |
| Statistical test | Diff_i = ORB_i − BH_i. Resample {Diff} with replacement (ordinary i.i.d. bootstrap). p = "how often a random pseudo-sample mean is at or above D_obs" [A §3.6]. Number of resamples not stated. |
| Significance interpretation | p near 0.5 → "no strong significance"; < 5 % → "reason to say the difference is significant" [A §3.6] |
| Block analysis | 4 consecutive ~3-month blocks; ORB and p recomputed per block; called "pseudo-out-of-sample" [A §3.7] |
| Out-of-sample method | None beyond the blocks. A "separate holdout database or rolling forward-walk" is listed as future work [A §6.5]. |
| Robustness checks | 3 windows × (price-only, 2 volume filters) × 3 holding periods, plus 4 blocks and 2 directions. About 18+ specifications in total [A/I]. |
| Multiple testing | None [A] |

## 5. Results — as reported by the authors

| Analysis | Reported [A] | Figure reading [R] |
|---|---|---|
| Window (price-only) | Cumulative: 5-min +23.37 %, 15-min +15.81 %, 30-min +9.76 %; BH −36.88 %. Daily mean diff ≈ 0.19–0.24 %. p ≈ 0.49–0.50. | 5-min peaks ≈ 1.37 (Oct–Nov 2024), ends ≈ 1.23. 30-min is flat or falling from Sep 2024. |
| Volume filter (5-min) | 1.2× ≈ +18 %, 1.5× ≈ +8 %. Diff ≈ 0.19–0.22 %. p ≈ 0.48–0.50. | — |
| Holding period (5-min) | N = 2, 3, 5 all ≈ +23–24 %. Diff ≈ 0.24 %. p ≈ 0.46–0.50. | All three lines are identical. |
| Blocks (5-min) | "In each block, ORB surpasses BH by 8–25 %". p ≈ 0.45–0.49. | Block 1 ORB ≈ +15 %; block 2 ≈ +3 %; block 3 ≈ +16 %; **block 4 ORB ≈ −10 %** (BH ≈ −29 %). |
| Direction (5-min) | Bullish ≈ +7 %, bearish ≈ +15 %. p ≈ 0.48–0.49. About 141 short / 101 long trades; hit ≈ 50–55 %. | 1.07 × 1.153 ≈ 1.234, consistent with the combined 5-min line. |
| Conclusion | "Operationally appealing but … statistically indecisive in a one-year sample for one security" [A abstract, §7]. | — |

The authors' block statement is relative to BH. In absolute terms ORB **lost** money in block 4 [R]. The paper does not say this.

## 6. Limitations stated by the authors

- **§3.1:** single instrument, single year, may miss market cycles and cross-sectional diversity.
- **§5.1 / §5.5:** volatile daily differences; small sample; serial correlation not captured by the bootstrap; non-normal heavy tails; little regime diversity; zero costs.
- **§6:**
  - (1) one stock, one year;
  - (2) no transaction costs or slippage;
  - (3) no correlation-aware testing (suggests "randomization or sign-flip testing");
  - (4) fixed volume thresholds;
  - (5) blocks are only pseudo-OOS; needs a separate holdout or walk-forward.
- **§7.4 future work:** more NSE stocks, cost modelling, ML filters, stronger significance testing, longer samples.

## 7. Our methodological assessment [I]

This section is our analysis, not the authors' claims.

1. **The p-values are uninformative by construction.**
   - The procedure described in §3.6 resamples the observed Diff and counts resampled means ≥ D_obs. That distribution is centred on D_obs, so p ≈ 0.5 for any true effect.
   - A simulation confirms it (normal Diff, sd 1.8 %, n = 250, 10,000 resamples):

     | True mean / day | Paper-style p | Null-centred p |
     |---|---|---|
     | 0 % | 0.501 | 0.53 |
     | 0.2 % | 0.501 | 0.13 |
     | 1.0 % | 0.504 | < 0.0001 |

   - A correct test resamples the series centred under H0 (Diff − D_obs) and compares with D_obs, or uses a CI.
   - The uniform p ≈ 0.45–0.50 across all variants and blocks is the signature of this error.
   - **Caveat:** this is inferred from the prose; the notebooks were not checked.
   - The paper therefore provides **no evidence for or against** significance.
2. **The benchmark difference is dominated by BH drift.**
   - BH fell about 37 %, roughly −0.18 % per day (log).
   - The reported Diff of 0.19–0.24 %/day therefore leaves a stand-alone ORB mean of only about 0.0–0.06 %/day gross.
   - Compounded +23 % over about 270 days ≈ +0.08 %/day.
   - Diff also sets 0 − BH on no-trade days, which mechanically rewards being flat in a falling market.
   - The paper's "practical significance" (a 60-pp gap) is mainly the benchmark's loss, not an ORB edge.
3. **Economic significance after costs is unknown and probably small.**
   - Indian intraday round-trip costs at retail scale are about 8 bps plus slippage (`docs/evidence/cost_sources.md`).
   - That is comparable to the entire gross ORB mean.
4. **Execution is optimistic.**
   - Fill at the signal-bar close, no latency, no spread.
5. **The volume filter has look-ahead** (whole-day average volume).
6. **Specification search without control.**
   - 18+ variants are compared on one series. The text favours 5-min / 1.2× on in-sample results.
   - No family-wise, Reality-Check / SPA or deflated-Sharpe adjustment is used.
7. **Inference ignores dependence and heavy tails.**
   - The i.i.d. bootstrap is used even though the authors flag both issues.
8. **Selection and generality.**
   - A single, unexplained stock is chosen, so universe construction, survivorship and cross-sectional dependence are out of scope.
   - With one year and one stock, regime analysis is impossible (the authors acknowledge this).
9. **The implementation does not match the description.** Identical N = 2/3/5 curves suggest the holding-period variation was not implemented as described [R/I].
10. **Editorial quality is low.**
    - a placeholder reference, "Banerjee & Banerjee (Year)";
    - a template line, "(Additional references may be included as necessary.)";
    - figures labelled "Sec 5.X" in the text;
    - a misplaced figure caption fragment on p. 9.

    This is consistent with an unrefereed student working paper.

## 8. Authors' stated contribution and our view

- **Claimed [A §1.1, §2.6]:** to "close this research gap" of scarce peer-reviewed NSE ORB research testing significance versus buy-and-hold, by rigorously testing windows, volume filters, holding periods, block slicing and direction.
- **Our view [I]:** the paper shows that an NSE ORB study exists and lists the right open problems in its future work. Because of points 1, 2 and 9 above, it does not establish an NSE ORB effect, or its absence. The novelty claim ("scant serious research") is the authors' own and is not supported by any literature search in the paper.

## 9. How we cite it

> Prior NSE-specific ORB evidence we found consists of one single-stock, one-year, zero-cost working paper (Wang & Gangwar, SSRN 5198458), whose reported bootstrap p-values are uninformative as described.

Do **not** cite it as finding ORB "insignificant" on the NSE.

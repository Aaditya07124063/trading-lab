# SSRN 5198458 vs ORB v1 (DRAFT) — structured comparison

**Date:** 2026-10-01
**Inputs:**
- `SSRN_5198458_record.md`
- `docs/protocols/ORB_v1.md` (DRAFT, unchanged)
- `src/intraday/orb.py`, `src/intraday/engine.py`
- `data/metadata/universe/NIFTY50_frozen_20261001.json`
- `config/cost_scenarios.json`

**Data:** no holdout observation (≥ 2026-10-01) was opened.

## Classification key

| Code | Meaning |
|---|---|
| **SUB** | Substantive methodological difference: changes what is being estimated or the conditions under which it is estimated. |
| **RD** | Research-design improvement: changes what conclusions the design *can* support (inference validity, pre-registration, sampling). |
| **ROB** | Robustness improvement: same estimand, checked under more conditions. |
| **IMP** | Implementation improvement: better engineering or hygiene; expected practice, not a scientific contribution. |
| **≈** | Not meaningfully different. |

None of these codes implies novelty. Novelty is a claim about the literature and is assessed separately in `ORB_research_gap_analysis.md`.

## Comparison

| # | Dimension | SSRN 5198458 | ORB v1 draft | Class |
|---|---|---|---|---|
| 1 | Market | NSE cash equity | NSE cash equity | ≈ |
| 2 | Instrument universe | Tata Motors | NIFTY 50 constituents frozen from the NSE file at 08:26 IST on 2026-10-01; never updated, never substituted | SUB |
| 3 | Number of securities | 1 | 50 (prospective holdout). The development set is RELIANCE, TCS, HDFCBANK and INFY, plus 46 more from 2026-08-03. | SUB. Cross-sectional dependence means this is not 50× the evidence. |
| 4 | Historical period | About 2023-12 → 2025-01, in-sample | Development: 15-min data from 2026-04-23 (4 stocks) and 2026-08-03 (46 stocks). Holdout: from 2026-10-01, about 250 sessions. | SUB, because the holdout is prospective. The *length* is ≈ one year in both, so there is **no** gain in time-series length. |
| 5 | Intraday frequency | 5-min | 15-min | ≈. A data constraint, not an improvement; it prevents a 5-min opening range. |
| 6 | Opening range | First 5/15/30 min | First 30 min (09:15 and 09:30 bars); day skipped if either bar is missing | ≈. Same family; one window, pre-specified. |
| 7 | Breakout definition | Bar close beyond range | Completed-bar close beyond range | ≈ |
| 8 | Signal timing | Breakout-bar close | Breakout-bar close (completed bar) | ≈ |
| 9 | Entry execution | Implied fill at signal close | Next bar's open, plus slippage grid; no fills after 14:30 | SUB. It removes a same-price fill that cannot be achieved. |
| 10 | Exit execution | N bars (as written) / unclear (as implemented) | Close of the 15:15 bar (≈ 15:29:59) | SUB, a different holding horizon. **Problem:** after the broker MIS cut-off (see proposals R7). |
| 11 | Long/short | Both, symmetric; split reported | Both (C, primary); long-only (B) also reported | ≈ |
| 12 | Holding period | 10–25 min (stated) | Entry → about 15:30 | SUB. A different estimand (rest-of-day continuation). |
| 13 | Position sizing | Unstated; returns-based | 100 % of a Rs 1 lakh sleeve, integer shares, no leverage, independent sleeves | IMP, and partly SUB. Capital size matters under fixed per-order brokerage. |
| 14 | Transaction costs | None | Current Zerodha and Upstox schedules plus NSE circular; component breakdown | SUB. It changes the estimand to net return. |
| 15 | Slippage | None | Grid of 0/2/5/10/20 bps per side; break-even slippage | SUB / ROB |
| 16 | Benchmark | Open-to-close long | A: open-to-close long (same idea); F: buy-and-hold (context) | ≈. **The same drift confound**; see proposal R10. |
| 17 | Random-entry baseline | None | D: random direction and random entry bar in [09:45, 14:30] on ORB trade days, 10,000 draws | RD |
| 18 | Random-direction baseline | None | E: sign-randomisation of ORB directions | RD |
| 19 | Risk-free treatment | None | None stated | ≈. A gap in both; see R12. |
| 20 | Risk-adjusted metrics | Cited, not reported | Sharpe, max drawdown, volatility, profit factor, deflated Sharpe | IMP |
| 21 | Statistical inference | i.i.d. bootstrap; **uncentred p** (uninformative) | Stationary bootstrap (Politis–Romano); block rule "to be stated"; randomisation tests D/E | RD. **Valid inference** vs a test that cannot reject. |
| 22 | Confidence intervals | None | Bootstrap CIs for mean, Sharpe, difference | RD |
| 23 | Multiple testing | None, across 18+ specs | Holm across instruments; deflated Sharpe with trial count | RD |
| 24 | Regime analysis | 4 calendar blocks + direction | Volatility and trend regimes from past data only | ROB. With about 250 sessions it should be exploratory; see R14. |
| 25 | Data-quality validation | "Remove duplicates or missing intervals" | Validator, exclusion registry with evidence, NSE bhavcopy cross-checks (daily), collector rejections logged | IMP |
| 26 | Corporate actions | Not discussed | Daily: documented exclusions. Intraday: within-day returns are unaffected by adjustment; event rules for the holdout are **not yet specified** (R16). | IMP (partial) |
| 27 | Survivorship bias | N/A (1 stock, unexplained choice) | Holdout universe frozen point-in-time before the first session → no survivorship in the holdout. Development 4-stock set is survivor-selected (documented). | SUB for holdout inference |
| 28 | Point-in-time methodology | Not discussed; volume filter uses future info | Signal only on completed bars; regimes from past data; universe point-in-time; append-only collection | RD |
| 29 | Prospective holdout | None ("future work") | Live from 2026-10-01; locked in code until FROZEN | RD (the main design difference) |
| 30 | Reproducibility | Notebooks link | Git, checksums, raw snapshots, environment capture | IMP |
| 31 | Experiment registry | None | `registry/experiments.jsonl`, append-only, including the documented RELIANCE exposure | IMP. It enables RD #23 (trial counts). |
| 32 | Data registry | None | `registry/datasets.json` with checksums and validation status | IMP |
| 33 | Protocol freezing | None | DRAFT → FROZEN; never edited after freeze; v2 for changes | RD |

## Summary by class

- **SUB (#2, 3, 4, 9, 10, 12, 14, 15, 27):** what we estimate is different:
  - a net-of-cost, executable-timing, rest-of-day ORB effect;
  - on a point-in-time large-cap cross-section;
  - estimated prospectively.
- **RD (#17, 18, 21, 22, 23, 28, 29, 33):** what we can conclude is different. Notably, a valid test that can reject, and a pre-registered holdout.
- **ROB (#15 partly, 24):** sensitivity checks; supporting evidence only.
- **IMP (#13, 20, 25, 26, 30, 31, 32):** good practice a referee would expect. Not a contribution.
- **≈ (#1, 5, 6, 7, 8, 11, 16, 19):** same as the paper. Includes two **shared weaknesses**: the drift-confounded benchmark (#16) and no risk-free treatment (#19).

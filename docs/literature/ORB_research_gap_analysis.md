# ORB research-gap analysis (2026-10-01)

**Basis:**
- `SSRN_5198458_record.md` (FULL)
- `ORB_literature_review.md` (targeted, not systematic)
- `SSRN_5198458_vs_ORB_v1.md`

**Labels:**
- **[S]** = source-supported.
- **[I]** = our inference.

**Reading guide.** A "gap" is listed as *addressed* only if our design actually answers it. A gap being addressed does not make it novel: novelty depends on what the wider literature (not just A1) has done.

## 1. Gaps left by SSRN 5198458 (from its own future-work list) and our coverage

| Gap stated by A1 [S] | Does ORB v1 address it? | Novel in literature? |
|---|---|---|
| More NSE stocks (§6.1, §7.4) | **Yes.** 50 point-in-time NIFTY 50 names [I]. | Multi-stock ORB exists for the US (A5) [S]. For NSE, no multi-stock ORB study was found in a **targeted** search; absence is not established [I]. |
| More years / regime diversity (§5.5, §6.1) | **No.** The holdout is about 250 sessions, the same length as A1. Development 15-min history is about 2–5 months. [I] | — |
| Transaction costs and slippage (§6.2, §7.4) | **Yes.** Current Indian schedules, slippage grid, break-even slippage [I]. | Cost-inclusive ORB exists (A5 has commission only) [S]. A full Indian cost decomposition (STT asymmetry, per-order brokerage, capital dependence) for ORB was not found [I]. |
| Correlation-aware / sign-flip testing (§6.3, §7.4) | **Yes**, if R4–R6 are adopted. Stationary bootstrap (dates resampled jointly), sign-randomisation (E), random entry (D/D′). [I] | Standard methods (Politis–Romano; Holmberg et al. use a random-trading null) [S]. **Not a contribution in itself** [I]. |
| A separate holdout or walk-forward (§6.5) | **Yes.** A prospective holdout from 2026-10-01 under a frozen protocol [I]. | No ORB study read here uses a **prospective, pre-registered** holdout (A1, A5 and A3, as far as read, are fully historical) [S for those read]. Not established for the literature at large [I]. |
| Dynamic or ML filters (§6.4, §7.4) | **No, deliberately.** A canonical rule only. [I] | — |

## 2. Gaps not raised by A1 that matter for valid inference

| Issue | Status in A1 [S] | ORB v1 | Assessment [I] |
|---|---|---|---|
| Survivorship / universe construction | Single unexplained stock | Frozen point-in-time universe; missing names never substituted | A real design strength for **holdout** inference. A5 also handles survivorship (CRSP), so it is not novel in general. |
| Point-in-time signals | Volume filter uses whole-day volume | Completed-bar signals; regimes from past data | Necessary hygiene, not a contribution. |
| Execution timing | Same-bar fill | Next-bar open. The 15:30 exit is **not** executable under MIS (R7). | Partly addressed; needs fixing. |
| Benchmark drift confound | Present | **Also present** (benchmark A in H1) | Fix proposed (R10). |
| Multiple testing | None across 18+ specs | Holm, deflated Sharpe | Hygiene. Only meaningful if the primary hypothesis is single and pre-specified (R4). |
| Data quality | Minimal | Validation, logs, rejection, exclusions | Hygiene. Missing-bar rules must be written into the protocol (R17). |
| Economic vs statistical significance | Conflated ("practical significance" from drift) | Break-even slippage, cost decomposition | Real value for an applied reader. |

## 3. What the literature already establishes [S], independent of our study

1. ORB is an old, practitioner-originated rule (Crabel 1990, cited in A1 and A5).
2. ORB beat a random-trading null in crude-oil futures (A2), and timely ORB in five index-futures markets (A3). Both are futures, historical and in-sample-selected.
3. In US equities, an **unfiltered** 5-min ORB on a broad, survivorship-free universe earned about 29 % over 8 years (Sharpe 0.48), net of commission only. Strong results required an ex-post-selected relative-volume filter (A5).
4. Market-level intraday momentum exists in the US (A6), linked to hedging demand (A7). Indian evidence exists only as an unverified working paper (A8).
5. NSE intraday volatility is U-shaped (A9).
6. The single NSE ORB paper (A1) provides no valid significance evidence.

## 4. What our study could add, if executed as proposed [I]

- **A pre-registered, prospective, cost-inclusive estimate** of a canonical ORB-30 rule on a point-in-time NIFTY 50 cross-section, with randomisation baselines and dependence-aware inference.
- The likely value is **evidential, not methodological**: a credible estimate (including a credible null) for the Indian large-cap setting, where the only prior study is uninformative.
- **Break-even slippage under Indian costs** is directly useful to practitioners regardless of the sign of the result.

## 5. What it cannot add [I]

- **Time-series breadth.** One year, one regime path. The cross-section does not substitute for time: the stocks share market shocks.
- **Mechanism.** We do not test why ORB would work (no order flow, no options-gamma, no news data).
- **Generality** beyond NIFTY 50 large caps, the Yahoo 15-min data, Rs 1 lakh sleeves, and the 2026–27 period.
- **Methodological novelty.** Every statistical tool is standard.

## 6. Literature still needed before contribution claims (not all blocking the freeze)

| Item | Blocking freeze? | Reason |
|---|---|---|
| Read A8 in full (Indian intraday momentum) | No | Affects positioning, not rules |
| Systematic search for Indian ORB / breakout / intraday-momentum studies (Scopus/Google Scholar, Indian journals, NSE working papers, IIM/IGIDR) | No for the protocol; **yes before any "first" or "gap" claim** | A targeted search cannot establish absence |
| Verify A4 cost treatment from full text | No | Context only |
| Open the SEBI study PDF (B1) | No | Context only |
| Verify REF-section bibliographic details | No | Needed for a manuscript |

No literature item is expected to change ORB v1 **rules**. Items R4–R17 in the proposals are justified by inference validity and executability, not by any paper's results.

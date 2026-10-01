# ORB v1 — decision memo (literature stage), 2026-10-01

**For:** Aaditya.

**Status:**
- ORB v1 is **DRAFT** (unchanged).
- Stage 2 has **not started**.
- The holdout boundary is unchanged: 2026-10-01.

**Supporting documents:**
- `docs/literature/`: `SSRN_5198458_record.md`, `ORB_literature_review.md`, `SSRN_5198458_vs_ORB_v1.md`, `ORB_research_gap_analysis.md`
- `docs/protocols/ORB_v1_proposed_revisions.md`

## A. What the paper did

Wang & Gangwar, SSRN 5198458. WorldQuant University MFE students; an unrefereed working paper; PDF dated 2025-03-01.

- **Data:** Tata Motors only, 5-min bars, about Dec 2023 – Jan 2025.
- **Strategy:** ORB with 5/15/30-min windows, optional volume filters (1.2×/1.5× the *day's* average volume), 2/3/5-bar holds. First breakout per day, long and short. Zero costs and zero slippage.
- **Benchmark:** daily open-to-close long (BH).
- **Test:** an i.i.d. bootstrap of the daily ORB−BH difference (no-trade days = 0 − BH), plus four ~quarterly blocks and a bull/bear split.

## B. What it found (as reported)

- ORB +9.8 % to +23.4 % cumulative vs BH −36.9 %.
- Mean daily difference ≈ 0.19–0.24 %.
- p ≈ 0.45–0.50 everywhere.
- Authors' conclusion: "operationally appealing" but "statistically indecisive".
- From the figures: ORB lost about 10 % in absolute terms in block 4; the text reports only that it beat BH.

## C. Weaknesses

**Stated by the authors:**
- one stock, one year;
- no costs or slippage;
- the i.i.d. bootstrap ignores autocorrelation and heavy tails;
- fixed volume thresholds;
- only pseudo-out-of-sample.

**Our assessment:**
1. The bootstrap p-value as described is centred on the observed mean, so p ≈ 0.5 for any true effect. Simulation: p = 0.50 at a true 1 %/day edge, where a correct test gives p < 0.0001. **The paper gives no significance evidence in either direction.** This is inferred from the text; the notebooks were not checked.
2. The ORB−BH gap is mostly BH's drift. The stand-alone gross ORB is about 0.08 %/day, comparable to Indian round-trip costs.
3. The fill at the signal close cannot be achieved in practice.
4. The volume filter has look-ahead.
5. 18+ specifications are tested without multiple-testing control.
6. The N = 2/3/5 curves are identical, so the stated exit rule was apparently not implemented.

## D. Overlap with ORB v1

- NSE cash equity.
- First-breakout, close-confirmed ORB, long and short.
- **The same open-to-close benchmark (our A).**
- A bootstrap of daily returns.
- Sub-period and direction splits.

## E. Differences

All 33 dimensions are in `SSRN_5198458_vs_ORB_v1.md`.

- **Substantive:**
  - 50-stock point-in-time frozen universe;
  - prospective holdout;
  - next-bar-open execution;
  - hold to close;
  - Indian costs plus a slippage grid;
  - net-return estimand.
- **Research design:**
  - random-direction and random-entry baselines;
  - dependence-aware bootstrap with CIs;
  - multiple-testing control;
  - point-in-time signals and regimes;
  - protocol freezing.
- **Implementation:** data validation, registries, reproducibility.
- **Shared weaknesses:** the drift-confounded benchmark; no risk-free statement.

## F. Contribution assessment

- **Potentially substantive (evidential, not methodological):**
  - a pre-registered, prospective, cost-inclusive estimate of canonical ORB-30 on a point-in-time NIFTY 50 cross-section, where the only NSE study found is uninformative;
  - break-even slippage under Indian costs.
- **Not contributions:**
  - the statistical tools (all standard);
  - survivorship-aware or multi-stock ORB as such (done for the US by Zarattini, Barbon & Aziz 2024);
  - realistic fills;
  - registries.
- **Limits:**
  - about one year and one regime path;
  - cross-sectional dependence;
  - no mechanism tested;
  - 15-min Yahoo data.
- **Prior expectation (source-supported):**
  - In the US, an unfiltered 5-min ORB had Sharpe 0.48, and 30-min + relative-volume had Sharpe 0.21, net of commission only.
  - A small or zero net edge for ORB-30 here is plausible, and INCONCLUSIVE is a realistic outcome.

## G. Additional literature

All entries are in `ORB_literature_review.md`.

| Source | Read | Why it matters |
|---|---|---|
| Zarattini, Barbon & Aziz 2024, SSRN 4729284 | Full | Multi-stock, survivorship-free, point-in-time US precedent; weak unfiltered and 30-min results; no slippage, no holdout |
| Holmberg, Lönnbark & Lundström 2013, FRL 10(1) | Abstract | Peer-reviewed ORB vs a random-trading null (crude oil) |
| Tsai et al. 2019, IEEE Access | Abstract | ORB on 5 index futures; probing time selected per market |
| Zarattini & Aziz 2023, SSRN 4416622 | Listing | QQQ ORB |
| Gao et al. 2018, JFE 129(2) | Abstract | Mechanism: market intraday momentum |
| Baltussen et al. 2021, JFE 142(1) | Abstract | Mechanism: hedging demand |
| Motwani et al. 2024 | Listing only | India; full text blocked; must be read before any Indian-evidence claim |
| Singh & Gangwar 2018, MPRA | Abstract | NIFTY futures U-shaped volatility |
| SEBI 2024 | Press only | > 70 % of individual intraday traders lose money; costs are material |

Standard methodology references are listed, with details to be verified before any manuscript.

**Still needed before any "gap" or "first" claim:** a systematic search (Scopus/Scholar, Indian journals, NSE working papers). It is not needed for the freeze.

## H. Proposed ORB v1 changes (not applied)

Full detail in `ORB_v1_proposed_revisions.md`.

| Ref | Proposal |
|---|---|
| R7 | **Exit at the 15:15 bar open**, not the 15:15 bar close (≈ 15:29:59, after Zerodha's 15:25 MIS square-off). Applies to all strategies and benchmarks; needs a code change. |
| R10 | **H1 = mean net daily portfolio return > 0.** Benchmark A becomes context only. |
| R13 | **Primary unit:** equal-weight daily return of the 50 sleeves. **Test:** one-sided α = 0.05, null-centred stationary bootstrap over dates. **Block length:** Politis–White on development data. **Verdict:** 95 % CI with POSITIVE / NEGATIVE (δ = 2 bps/day) / INCONCLUSIVE. **Guard:** unit tests against the paper's error. **Power:** recorded before freeze. |
| R11 | **E:** flip gross returns by whole date, then apply costs. **D:** kept. **D′ (exposure-matched):** optional. |
| R14 | **Family 1:** primary test. **Family 2:** E and D (Holm). **Family 3:** per-stock tests (Romano–Wolf/Holm), exploratory. **Everything else:** descriptive. **Deflated-Sharpe trial count:** both registry files. |
| R16 | Holdout = exactly the first 250 NSE sessions from 2026-10-01; one evaluation; no interim looks. |
| R17 | Write the existing missing-bar rules into the protocol. **Add:** stale-fill rule; DATA-LIMITED threshold (10 %); corporate and symbol event rules; bhavcopy integrity flagging (no repair). |
| R12 | rf = 0 primary; T-bill sensitivity. |
| R15 | Regimes explicitly exploratory. |
| R8 | Re-verify cost schedules at freeze. |
| R19 | Update stale §8 open items. Name both registry files (`experiments.jsonl` exists; `trials.jsonl` does not yet exist). |

**Unchanged:** R1 (ORB-30 kept; no window switch from the literature), R2–R6 (wording clarified only), R18 (sizing).

## I. Decisions you must make before ORB v1 can be frozen

1. Primary slippage, 5 bps/side (R9).
2. Sleeve capital, Rs 1 lakh (R18).
3. Exit timing (R7), with options (a), (b) or (c).
4. H1 redefinition and demotion of A (R10).
5. Primary unit (R13.1).
6. α, sidedness, CI level, verdict rule and δ (R13.2–6).
7. Block-length rule (R13.4).
8. Baseline set: E, D, and whether to add D′ (R11).
9. Multiple-testing families (R14).
10. Fixed 250-session end (R16).
11. Missing-bar, stale-fill, DATA-LIMITED and corporate-event rules (R17).
12. Bhavcopy integrity check (R17).
13. Risk-free treatment (R12).
14. Regimes labelled exploratory (R15).
15. Authorise the code changes these imply: the exit in `engine.py`, and a statistics module with guard tests. Then run and record the power analysis on development data before freeze.

## J. Holdout integrity

- No observation dated on or after 2026-10-01 was opened, loaded or computed on in this work.
- No ORB performance, development or holdout, was used to motivate any proposal.
- The only numeric analysis was a synthetic simulation of the paper's bootstrap.
- The data loader's holdout lock is unchanged.
- The leakage checklist is in §3 of `ORB_v1_proposed_revisions.md`.

## K. Git state at memo time

- **Commits added:** 8165060, 09f405f, 7032894, plus this memo's commit. Documentation and `.gitignore` only.
- **Unchanged:** `docs/protocols/ORB_v1.md`, `src/`, `data/`, `config/`, `registry/`.
- **Tests:** `pytest`, 80 passed, 1 warning.
- **SSRN PDF:** kept locally, git-ignored (copyright), SHA-256 recorded.
- **Remote:** not pushed.

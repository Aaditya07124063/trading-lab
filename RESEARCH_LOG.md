# Research log

Chronological, append-only record of research decisions, findings and
corrections. Never edit past entries - add a new dated entry that supersedes.
Machine-readable detail lives in `registry/`; see [EXPERIMENT_REGISTRY.md](EXPERIMENT_REGISTRY.md)
and [DATA_REGISTRY.md](DATA_REGISTRY.md).

## 2026-07-17 / 2026-07-18 - original daily experiments (reconstructed)
- Daily EMA/SMA crossover, ML (RandomForest) and momentum experiments were run
  and summarised in README "Key findings". The dataset versions used were not
  recorded. See 2026-09-30 entries for their current status.

## 2026-09-30 - engine hardening (commits cd3743c..f8aff70)
- Leaderboard: two rows (`EMA 20/50 · NIFTY50d1`, `· HDFCBANKd1`) had been
  produced with a 10% trailing stop under names that omitted it; relabelled
  `· trail 10%` (commit cd3743c).
- Intraday engine, cost model (no rates), ORB, data pipeline, dashboard built.
- **OOS EXPOSURE:** during engine plumbing checks, ORB-30 on RELIANCEm15 and
  ORB-60 on RELIANCEh1 were run with ZERO costs and all three periods
  (development / validation / final_oos) were displayed. Status of those
  final_oos periods: **EXPOSED - VIEWED FOR RESEARCH/DIAGNOSTIC PURPOSES; NO
  PARAMETER TUNING PERFORMED.** They can no longer be called untouched
  holdouts. The clean prospective holdout is data from 2026-10-01 onward,
  evaluated only under a frozen protocol ([ORB protocol](docs/protocols/ORB_v1.md)).

## 2026-09-30 - Stage 1 foundation
- **Data validation (daily).** Flag-only validator; exclusions only after review
  with evidence. Cross-validated against NSE bhavcopy archive:
  - 2005-07-28: NSE did not trade; Yahoo placeholder bars (RELIANCE/TCS at an
    unadjusted price level) → excluded.
  - TCS rows 2002-08-12..2004-08-24 predate the NSE listing (2004-08-25) → excluded.
  - RELIANCE 1997-10-27..11-04: real 1:1 bonus (ex 1997-11-05) but vendor adjustment
    boundary misplaced → excluded, not corrected.
  - 123 placeholder dates verified as NSE non-trading days → excluded;
    3 were real trading days with missing vendor data (1996-04-01, 1996-07-17,
    2025-03-18) → excluded, not replaced.
  - Extreme moves 2003-04-10 (INFY), 2009-05-18 (RELIANCE), 2004-05-17/18 (HDFCBANK)
    kept as genuine; weekend special sessions kept.
- **Impact.** RELIANCE EMA 20/50: +667.0% raw → +822.2% clean (B&H unchanged);
  TCS B&H +5,760% raw → +1,414% clean. No qualitative conclusion changed; affected
  results marked REQUIRES REVALIDATION pending user review of exclusions.
- **README +17,703% vs leaderboard +18,031.1%:** README figure not reproducible
  from any committed data; computed on an earlier, uncommitted data version
  (details: README Note 1, LEGACY-005).
- **Costs.** Current published NSE equity-intraday schedules recorded
  (`docs/evidence/cost_sources.md`); round trip ≈ 8.3 bps + slippage at Rs 1 lakh.
- **Literature (preliminary).** ORB is not novel; an NSE-specific SSRN study
  exists and must be read before defining the contribution.
- **ORB protocol v1** drafted (`docs/protocols/ORB_v1.md`), status DRAFT; clean
  holdout = 15-min data from 2026-10-01, locked in code.

## 2026-10-01 - universe freeze, exclusion review, collector
- 08:26 IST (before the first holdout session): NIFTY 50 constituent file
  retrieved from NSE (last-modified 2026-09-30) and frozen as the prospective
  holdout universe (`data/metadata/universe/NIFTY50_frozen_20261001.json`,
  commit fc3b26d). All 50 available on Yahoo 15m at freeze. Historical
  research universe (RELIANCE, TCS, HDFCBANK, INFY, NIFTY50, SENSEX) is distinct.
- Six hand-written exclusions reviewed individually: wording corrected for the
  2005-07-28 RELIANCE/TCS placeholders (inconsistently adjusted, not
  unadjusted); RELIANCE 1997 block verified date by date; TCS listing-day volume
  flagged. No exclusion decision changed.
- Collector (`update_intraday.py`, `scripts/collect_intraday.sh`) run manually
  08:29 IST: 58 datasets OK, 46 new holdout-universe m15 files (2026-08-03 ..
  2026-09-30, pre-holdout). Yahoo omits isolated bars in ~4-15 of 42 sessions
  per stock - logged; affects tradable session counts.
- launchd schedule test FAILED (exit 126): macOS privacy protection blocks
  launchd from ~/Desktop. Job unloaded; awaiting user decision. Yahoo retains
  ~60 days of 15m bars, so no holdout data is lost if resolved before ~2026-11-28.

## 2026-10-01 - literature stage: SSRN 5198458 and ORB v1 review (documentation only)
- **SSRN 5198458 (Wang & Gangwar) read in full.** All text plus the 5 figures. Notebooks not opened.
  - Design: Tata Motors only, 5-min bars, about 2023-12 → 2025-01, zero costs.
  - Method: i.i.d. bootstrap of the daily ORB−BH difference.
  - Our assessment: the p-value procedure as described is centred on the observed mean, so p ≈ 0.5 by construction. A simulation confirms this: p = 0.50 even at a true 1 %/day edge.
  - The ORB−BH gap is mostly BH's −37 % drift.
  - The N = 2/3/5 holding-period curves are identical (the parameter is apparently not implemented).
  - The volume filter uses whole-day volume (look-ahead).
  - Record: `docs/literature/SSRN_5198458_record.md`.
- **Additional literature (targeted search):**
  - Holmberg et al. 2013 (FRL);
  - Tsai et al. 2019 (IEEE Access);
  - Zarattini & Aziz 2023;
  - Zarattini, Barbon & Aziz 2024 (read in full; unfiltered 5-min ORB Sharpe 0.48, 30-min + relative-volume Sharpe 0.21, commission only, no slippage);
  - Gao et al. 2018 (JFE); Baltussen et al. 2021 (JFE);
  - Motwani et al. 2024 (India, listing only); Singh & Gangwar 2018 (NIFTY futures volatility);
  - the SEBI 2024 intraday P&L study (press only).
  - Review: `docs/literature/ORB_literature_review.md`.
- **Comparison and gap analysis:** `docs/literature/SSRN_5198458_vs_ORB_v1.md` (33 dimensions, classified) and `docs/literature/ORB_research_gap_analysis.md`.
  - "Multi-stock" and "survivorship-aware" ORB are not novel in general (US: Zarattini et al.).
  - For the NSE, none was found in a targeted search, which does not establish absence.
- **Code/protocol issue found (not fixed):** the engine exits at the 15:15 bar close (≈ 15:29:59), which is after Zerodha's 15:25 MIS auto-square-off. Proposal R7.
- **Proposals (NOT applied):** `docs/protocols/ORB_v1_proposed_revisions.md`, items R1–R19 and 15 decisions for the user. ORB v1 remains DRAFT. Stage 2 not started.
- **Holdout:** no observation dated ≥ 2026-10-01 was opened. No ORB performance (development or holdout) was used to justify any proposal.
- The SSRN PDF is kept locally and not committed (copyright; repo has a GitHub remote). SHA-256 is in the record. `docs/literature/*.pdf` added to `.gitignore`.

## 2026-10-01 - focused verification: exit timing (CAS) and SSRN bootstrap (no protocol change)
- **NSE Closing Auction Session (SEBI circular 16 Jan 2026, effective 2026-08-03).**
  - For stocks with derivatives, continuous trading ends at 15:15; the auction runs 15:15–15:35 and sets the official close.
  - All 50 frozen constituents are F&O stocks, so all are CAS stocks.
  - The pre-open session changed from 2026-09-07; CTS still starts at 09:15.
- **Yahoo 15-min data, pre-holdout only:**
  - Since 2026-08-03 the `15:15` bar, when present, closes exactly at NSE's official close, i.e. the auction price (700 stock-days, 14 dates, 100 %).
  - The bar is missing in about 22 % of stock-sessions.
  - Every other bar is present 100 %.
  - **Correction** to the 2026-10-01 collector entry above: the "isolated missing bars" were all missing auction bars.
  - Last continuous price (`15:00` bar close) vs official close: median 22 bps.
- **Consequence:** the current engine rule ("15:15 bar close", sessions without it skipped) means a CTS trade at about 15:29:59 before 2026-08-03 and the auction price after it. It also drops about 22 % of post-CAS sessions for a vendor reason.
- **Correction to the decision memo / R7:** for CAS stocks the broker MIS cut-offs are 15:12 (Zerodha) and 15:10 (Upstox). The memo's 15:25 applies to non-CAS stocks only.
- Three candidate exit definitions (X1 CTS close, X2 fixed 15:00, X3 auction close via bhavcopy) were documented; **none selected**.
- **SSRN 5198458 bootstrap verified by synthetic simulation:** the described procedure yields p ≈ 0.50 (90 % range 0.48–0.52) for true effects of −1 % to +1 %/day under four data-generating processes. Cause: the bootstrap is centred on the observed mean, not under H0. The criticism stands, with precise wording in `docs/protocols/ORB_v1_verification_20261001.md`.
- No ORB or benchmark return was computed. The holdout was not read. Protocol, universe, collector and engine are unchanged.

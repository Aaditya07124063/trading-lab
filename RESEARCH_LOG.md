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

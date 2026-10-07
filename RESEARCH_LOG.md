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

## 2026-10-01 - ORB v1 approved decisions implemented; pre-holdout validation (protocol NOT frozen)
- **User approvals (2026-10-01):**
  - exit X2 (open of the 15:00 bar);
  - H1 = mean daily net portfolio return > 0, one-sided α = 0.05;
  - cost model unchanged (Rs 1 lakh, 5 bps/side; grid 0/2/5/10/20; Rs 10 lakh sensitivity);
  - dependence-aware null-centred inference;
  - random baselines retained;
  - ORB entry rules unchanged.
- **Engine (a9a8f7f):**
  - X2 exit; the 15:00 high/low/close and the 15:15 bar are never used;
  - complete-session rule (all 09:15..15:00 bars must exist, no synthetic prices);
  - fixed-notional sizing;
  - benchmark A uses the same exit;
  - `legacy_v0()` keeps LEGACY-014/015 reproducible.
- **Inference, portfolio, baselines, regimes (7cfad45):**
  - R_t = Σ net P&L / (50 × Rs 1 lakh);
  - stationary bootstrap with Politis–White block length;
  - guard test against the SSRN uncentred construction;
  - E sign-flip; D random entry in the ORB-feasible window 10:00–14:30 (draft said 09:45; flagged).
- **Pre-holdout validation (41a7a30, ORBV1-20261001-001, DIAGNOSTIC):**
  - Sample: 42 sessions × 50 stocks (2026-08-03..09-30). All 2,100 stock-sessions complete; 1,810 trades.
  - Invariants: all hold. Engine and vectorised P&L agree to 1e-12. Reproducible bit-for-bit.
  - Descriptive dev numbers (NOT evidence, NOT used for any decision):
    - gross −0.7 bps/day;
    - net −16.3 bps/day at Z-5 (label NEGATIVE on this dev sample);
    - E p = 0.68, D p = 0.70;
    - break-even slippage: none ≥ 0.
  - Power: long-run sd 16 bps/day; MDE 2.5 bps/day at n = 250.
  - No protocol element was changed in response.
- **Open items before freeze:** OPEN-1..12 in `docs/protocols/ORB_v1_final_review_20261001.md`.

## 2026-10-02 - ORB v1 pre-freeze audit (protocol NOT frozen)
- **Approved 2026-10-01:**
  - holdout = first 250 standard NSE sessions from 2026-10-01;
  - automatic Politis–White block length on the evaluated series;
  - random-entry window 10:00–14:30;
  - NEGATIVE = upper bound < 0;
  - deflated Sharpe reporting-only;
  - fair-coin E;
  - NSE calendar storage;
  - holdout-file registration at freeze;
  - bhavcopy check (validation only);
  - locked evaluation script.
- **Implemented (8d21e3e):**
  - `evaluate_orb_v1.py` (no tuning options; refuses unless FROZEN, the tree is clean and all 250 sessions are collected);
  - `calendar.py` (NSE CM holiday master 2026 stored; 61 sessions in 2026; the 2027 list must be stored when published);
  - `bhavcopy_check.py` (C1 range / C2 presence / C3 volume, flag-only; the 09:15 open is not compared because NSE's open is the pre-open auction price);
  - deflated Sharpe;
  - power script.
- **Dry run on development data** (ORBV1-20261002-001): identical to the previous validation; 0 bhavcopy flags; 120 tests pass.
- **Power:** MDE 2.52 bps/day at n = 250 (one-sided α = 0.05, 80 % target). The simulated power of the actual test is 0.78–0.82 under development-derived variance and no detected dependence.
- **Remaining for the user:** regime index source; 2027 calendar (procedural); rule for hard validation errors; bhavcopy tolerances. See `docs/protocols/ORB_v1_pre_freeze_audit_20261001.md` §I.
- The collector appended 2026-10-01/02 bars to the data files (uncommitted, not read by any analysis).

## 2026-10-02/03 - ORB v1 final pre-freeze audit: READY FOR EXPLICIT FREEZE APPROVAL (not frozen)
- **Approved 2026-10-02:**
  - official NSE NIFTY 50 close as the regime source;
  - 2027 holiday rule (store the list when published);
  - malformed data makes only the affected stock-session untradable;
  - bhavcopy tolerances 1 bp and 50–105 %, flags only.
- **Implemented (13e4664):**
  - Regime source: `ind_close_all` archive. 2026 history = 184 standard sessions, which match the stored calendar exactly; per-file SHA-256 stored.
  - `split_defective` for malformed data, with an opt-in `load_csv(coerce=True)`.
  - The bhavcopy exclusion sensitivity is removed.
  - Universe-level "collected" check, and usable stock-sessions reported with reasons.
  - Edge-case guards.
- **Dry run** ORBV1-20261002-002 (DIAGNOSTIC): primary numbers identical; regimes ran. 124 tests pass.
- **Audit** (`docs/protocols/ORB_v1_pre_freeze_audit_20261001.md`): 30 PASS, 0 FAIL, 0 UNRESOLVED. Two freeze actions are pending the user's approval (replace the `ORB_v1.md` body and set FROZEN; register the 46 files).
- The holdout is untouched. `ORB_v1.md` is still DRAFT.

## 2026-10-03 - Phase 1: data-access boundary + dashboard cutoff (no ORB change)
- `src/access.py`: research cutoff 2026-09-30 (`research_load_csv`, `research_load_clean`, `research_frame`).
  - The holdout gate now needs a FROZEN protocol **and** a committed, unmodified authorization artifact (`docs/protocols/ORB_v1_holdout_authorization.md`, created only when the user authorises the run). The artifact must carry the protocol SHA-256, "sessions: 250", authorized_by and date.
  - Single-use guard: the evaluator refuses if a holdout result directory exists or a FINAL ORB v1 record is registered.
- The FROZEN status alone no longer opens the holdout. The old test asserting that behaviour was updated.
- Collector (tier W) is unchanged and still reads and writes through the raw loader. Status (tier O) now has a fixed field list and restricted imports.
- Research tier routed through the cutoff:
  - `run_daily` (/api/backtest), `/api/watchlist`;
  - `/api/add`, which truncates at 2026-09-30 before saving;
  - `run_momentum.py`, `run_ml.py`;
  - intraday endpoints, which already used the cut loader.
- Tests (38 new):
  - gate tests on temporary git repositories;
  - single-use guard;
  - collector merge with October rows;
  - dashboard cutoff with poisoned October values (mutation-checked);
  - code scan blocking raw market-data reads outside the allowed modules;
  - only the evaluator may request holdout rows;
  - status field list and imports;
  - frozen-methodology SHA-256 pins (15 files).
- 162 tests pass. ORB_v1.md SHA-256 is unchanged (9c9cc1fc…). No holdout data read, no performance computed, Stage 2 not started.

## 2026-10-03..05 - Stage 2 Phase 2: historical data foundation (no experiments)
- **Source audit (2A):**
  - NSE legacy CM bhavcopy 1995 → 2024-07-05; UDiFF from 2024-01-01; ISIN from 2011-06-22.
  - Corporate-action API comprehensive only from 2006.
  - Index closes from 2012-02-21; India VIX from 2014-05.
- **Raw archive (2B):** 5,494 daily files (2005 → 2026-09-30) plus corporate actions and identity lists, outside git, append-only manifest.
- **PANEL-1 (2C/2I):** 7,824,095 EQ rows. QA clean apart from 3 ISIN-only legacy/UDiFF differences on split days (documented).
- **CA-2 (2D):**
  - 1,082 of 1,375 bonus/split events validated, plus 104 after identity resolution.
  - NSE PREVCLOSE is unadjusted on ex-dates (1,131 of 1,140).
  - **The NSE corporate-action source is incomplete** (HEG, TIPSINDLTD and others).
- **ID-1 (2E):**
  - 2,960 evidence-only identity links.
  - 89 unexplained ISIN changes and 1,892 pre-2011 gaps unresolved.
  - ETF/fund units identified by INF ISIN.
- **UNIV-1 (2F):** verified period from 2011-06-22; monthly top-200 by 63-session median traded value; at least 50 of 63 valid sessions. **Approved and frozen 2026-10-05.**
- **RET-1 (2G):**
  - 99.24% research-grade price-return rows.
  - Adjustments only for validated bonuses/splits.
  - No dividends (price returns only).
  - Rights and demergers flagged.
  - A universally reliable adjusted or total-return history **cannot** be claimed.
- **Disk cleanup (user-approved, outside the project):** npm cache and `brew cleanup -s`. Free space went from 5.5 GB to 10.85 GB. The uv prune was blocked by a running chroma-mcp server and skipped.
- No data after 2026-09-30 read; no holdout data read; ORB v1 unchanged; no ML; no experiments.

## 2026-10-05 - Stage 2 Phase 2.1: three review fixes (no experiments)
- **Special sessions (B1):** all 2,270 weekend days 2005 → 2026-09-30 requested; 27 NSE weekend sessions archived (19 in the verified period). PANEL-1.1 adds `session_type`. UNIV-1 keeps its standard-session definition and is unchanged.
- **RET-1.1:** 30,109 returns that span a special session are flagged `SPECIAL_SESSION_SPAN` and are not research-grade.
- **Large residuals (I1):** 106 validated bonus/split rows with an adjusted return beyond 10% are flagged `VALIDATED_LARGE_RESIDUAL` and are not research-grade. No new adjustments; raw prices unchanged.
- Research-grade share: 99.24% (RET-1) → 98.75% (RET-1.1).
- **Reproducibility (B2):** `scripts/build_stage2.py` rebuilds ID-1, CA-2, UNIV-1, RET-1 and the validation outputs from the raw archive and matches every Phase 2 hash.
- Not classified: weekday special sessions (Muhurat on a weekday holiday) stay `STANDARD`.
- **Review decisions (approved 2026-10-05):** 10% residual threshold fixed as a predefined diagnostic rule; span rows stay excluded; weekday special sessions left unclassified for lack of archived NSE calendar evidence; 2012-11-11 kept. "Research-grade" = passes predefined data-quality rules, not error-free history.
- Details: `docs/stage2/data/phase2_1_fixes_20261005.md`.
- No data after 2026-09-30 read; no holdout data read; ORB v1 unchanged; no ML; no experiments.

## 2026-10-05 - Phase 3A: momentum study protocol S2-MOM-v1 (DRAFT; no experiment run)
- Wrote `docs/research/phase3a_momentum_protocol.md`: literature-gap assessment and a 28-item protocol. Status DRAFT, not frozen, not registered.
- **No return was computed and no performance result was seen.** Only structural counts were read from UNIV-1 (selection dates, eligible-stock counts, rank coverage).
- Literature finding: Indian momentum is established (Agarwalla–Jacob–Varma 2013/2017; Chui et al. 2023; Raju & Chandrasekaran 2019; Das & Barai 2016; Garg & Varshney 2015). The study is framed as a pre-registered replication plus a backtest-shortcut bias decomposition, not as a new anomaly.
- Primary specification: 12-1 formation, one-month skip, one-month holding, top/bottom 30%, equal weight, UNIV-1 members, 170 months (Jul 2012 – Aug 2026), Newey–West t-test.
- Open decisions D1–D4 and four blockers (index history, delivery cost schedule, full-text reading of two papers, slippage source) are listed in §29 of the protocol.
- No code or dataset changed; UNIV-1 and ORB v1 unchanged; no data after 2026-09-30 read; no holdout data read.

## 2026-10-05 - Phase 3A revision 2: protocol reframed around bias decomposition (DRAFT; no experiment run)
- `docs/research/phase3a_momentum_protocol.md` rewritten after review (rated 8.6/10, not approved for freezing).
- **Primary question is now:** how much do backtesting shortcuts distort measured momentum in Indian equities. Momentum existence, liquidity and long-only results are treated as replication, not as new.
- **Bias ladder fixed in advance:** A survivor-style baseline → B point-in-time liquidity → C survivorship and identity → D corporate-action and data-quality (RET-1.1 research-grade) → E costs.
- **`SPECIAL_SESSION_SPAN` stays excluded from the primary analysis;** the raw two-session return is a sensitivity analysis only. RET-1.1 unchanged.
- **Temporal design:** primary historical sample Jul 2012 – Dec 2021 (114 months); confirmation Jan 2022 – Aug 2026 (56 months); pooled 170 months descriptive only.
- **Costs:** evidenced statutory charges separated from assumed slippage scenarios (0/5/10/25/50 bps); break-even always reported.
- **One primary regime:** NIFTY 50 24-month market state from the NSE index archive; regime analysis starts Mar 2014.
- **Not frozen.** Blockers: index files not archived; delivery cost schedule not evidenced; papers 2–7 verified at abstract level only; reference effect size to check; four reviewer decisions.
- No return computed; no performance seen; no code or dataset changed; UNIV-1 and ORB v1 unchanged; no data after 2026-09-30 and no holdout data read.

## 2026-10-05 - Phase 3A revision 3: statistical and reproducibility fixes (DRAFT; not frozen; no experiment run)
- **Primary estimand stated exactly:** δ(t) = WML_A(t) − WML_D(t); H1 is that its mean differs from zero (two-sided).
- **Power:** the earlier Sharpe-based figure was wrong for H1 and now applies only to the secondary existence test. For δ(t) the standard deviation is unknown before results, so the protocol gives a precision table and states that adequate power is **not** claimed. A blinded precision step (standard deviation only, before any mean) is fixed for Phase 3B.
- **Practical-significance bound:** ±0.10% per month kept as an ex-ante bound, with three independent anchors (transaction-tax scale, published Indian survivorship bias, share of the reported premium).
- **Steps A and B defined operationally:** survivor pool P, the function Top200(pool, date), exact return and corporate-action rules. B changes only the date on which liquidity is evaluated.
- **Temporal design explained:** Dec 2021 boundary; 2022–2026 is a chronological out-of-sample period, not an independently designed experiment.
- **Regimes:** now secondary and exploratory; the March 2014 start is conditional on the unarchived NSE index files.
- **Literature:** Ranse (2025) read in full — equal-weight survivor comparison, no momentum, names strategy-specific bias as future work. Jain (2026) and Raju & Chandrasekaran (2019) remain UNVERIFIED on the key points (access refused).
- No return computed; no performance seen; no code or dataset changed; UNIV-1, RET-1.1 and ORB v1 unchanged; no data after 2026-09-30 and no holdout data read.

## 2026-10-05 - Phase 3A revision 4: final wording corrections (DRAFT; not frozen; no experiment run)
- **Sequential decomposition:** A → E is stated as a sequential decomposition, not an identification of independent causal effects. Step sizes depend on order and interactions; the reverse-order ladder is robustness only; no factorial or Shapley analysis.
- **Raju & Chandrasekaran (2019):** literature table updated from reviewer-supplied evidence (Refinitiv data, delisted stocks included, month-end NIFTY 100 constituents, IIMA survivorship-adjusted factors). Exact historical-constituent construction not claimed as verified.
- **Jain (2026):** kept unresolved on whether it contains a momentum-specific experiment. No exclusive novelty is claimed against it.
- **Positioning:** Indian momentum is established; survivorship-adjusted momentum analysis exists; the contribution is the controlled sequential measurement of how several data and backtest corrections alter one fixed momentum design.
- **Threshold:** ±0.10% per month reworded as an ex-ante economically meaningful reference threshold, not a universal minimum.
- **Corporate actions:** event date, source availability date and research use separated; the information builds historical returns and data-quality classes and is never a trading signal; no availability date is invented.
- **Regime analysis removed** from the study; the NSE index archive is no longer a blocker.
- Unchanged: research question, δ = WML_A − WML_D, two-sided H1, sample dates, 12-1, skip month, one-month holding, delayed entry, 30%, equal weight, RET-1.1 returns, special-session exclusion, Newey–West lag 4, bootstrap, cost scenarios, leakage tests, A–E ladder.
- No return computed; no performance seen; no code or dataset changed; UNIV-1, RET-1.1 and ORB v1 unchanged; no data after 2026-09-30 and no holdout data read.

## 2026-10-05 - Phase 3A protocol S2-MOM-v1 FROZEN (revision 4; no experiment run)
- **Frozen file:** `docs/research/phase3a_momentum_protocol.md`, status FROZEN, approved by the reviewer as written.
- **Protocol SHA-256:** `f1abd954f698307f7aafe234c5d5c9f1681ccc5aadb9cb21e9f8e34d47abd838`
- **Freeze commit:** the commit that adds this entry, subject "freeze: Phase 3A protocol S2-MOM-v1 (revision 4)", parent `d0b4a77`. A commit cannot contain its own hash; find it with `git log --grep "freeze: Phase 3A protocol"`.
- The research design was not changed at the freeze. Only status wording changed (DRAFT → FROZEN; decisions marked approved).
- Open items carried into Phase 3B, to be closed before any return is computed: delivery cost evidence; full-text literature checks; references cited from memory; registration in `registry/`.
- No experiment run; no portfolio return, Sharpe ratio, p-value, drawdown, turnover or out-of-sample result computed.
- No dataset changed; UNIV-1, RET-1.1 and ORB v1 unchanged; collector-written files under `data/india/` and `data/raw/` not touched and not committed.

## 2026-10-05 - Phase 3B: S2-MOM-v1 execution infrastructure (implementation and validation only; experiment NOT run)
- **Registered** `S2-MOM-v1` in `registry/experiments.jsonl`, status PLANNED, referencing the frozen protocol (SHA-256 `f1abd954…bd838`, freeze commit `7d4cb6d`).
- **Code:** `src/stage3/` (protocol constants and guards, ladder A–D, costs for step E, statistics, data builder/loaders, analysis), `scripts/build_stage3.py`, `scripts/run_s2_mom.py`.
- **Inputs built** by `scripts/build_stage3.py` into `data/stage3/s2_mom_v1/` (calendar, universes A/B/C, daily study panel, identity, manifest). Rebuild is byte-identical. Structural checks passed: 170 months (114 primary, 56 OOS); step A list = UNIV-1 members at 2026-09-30; step C = UNIV-1 members at every date.
- **Tests:** 49 new, synthetic data only (ladder definitions, 12-1 formation, delayed entry, breakpoints, step D rules, delisting, paired estimand, leakage tests A–H, costs, statistics, guards). Suite: 290 passed.
- **No real result exists.** The runner was not executed. No portfolio return, mean, Sharpe ratio, p-value, drawdown or turnover result was computed on research data. Only structural counts were produced.
- **Runner is blocked by design** until six open decisions are closed in the registry (sample data end; neutral-fill weighting; exit-gap return in step D; exit-gap look-ahead; p-value distribution; bootstrap seed) and delivery cost evidence is archived.
- Not yet implemented: secondary analyses H2d, H3–H5 and the remaining fixed robustness set (J×K grid, breakpoints, weights, liquidity band 201–500, monotonicity).
- UNIV-1, RET-1.1, ORB v1 and the frozen protocol unchanged; collector files under `data/india/` and `data/raw/` not read and not touched.

## 2026-10-05 - Phase 3B second review: decisions 1, 5, 6 applied; 2-4 held; checklist written (experiment NOT run)
- **Applied:** (1) protocol exit sessions define the sample data end, 114 + 56 months, nothing after 2026-09-30; (5) standard normal p-value for the Newey–West test, no t(n−1) variant; (6) bootstrap seed 20261005. Recorded in the registry by amendment.
- **Not applied — conflict with the frozen protocol:** reviewer decisions 2–4 (drop a stock-month with a non-research-grade return or no exit price; never look past the exit session) contradict §20(b) ("never removed after the fact … neutral fill") and §22 (carry at last price; book the later gap return; delisting 0% / −30%). No code was changed for them; three registry decisions stay open. Options are set out in `docs/research/phase3b_implementation_checklist.md`.
- **Checklist:** `docs/research/phase3b_implementation_checklist.md` separates primary, secondary, fixed-robustness and optional items. Several required items are missing, so the experiment must not run yet.
- **Tests:** 294 passed (241 baseline + 53 Stage 3, synthetic data only). New: normal p-value determinism; A and D share one month structure; prices after the exit session cannot change a month that has an exit price; loader refuses month-end truncation.
- **Disk:** about 1.4 GB free. Read-only diagnosis: macOS is staging a system update (`/System/Volumes/Update` 16 GB, written today). Nothing was deleted. Stage 2 rebuild not run.
- No real experiment run; no real result computed; collector and ORB files untouched; frozen protocol, UNIV-1, RET-1.1 unchanged.

## 2026-10-05 - Phase 3B third review: frozen-protocol interpretation finalised; real-data pre-run checks passed (experiment NOT run)
- **S2-MOM-v1 stays frozen** (reviewer option 1). No protocol text changed; no v2.
- **§20(b):** a flagged day of a held stock in step D takes the simple mean of the other stocks' same-day returns; the stock stays a member; each fill is logged.
- **§22:** applied literally in steps C and D. The delisting return is already specified in the frozen text (voluntary 0%; compulsory, liquidation or unexplained −30%); the data contain only those three types.
- Earlier reviewer decisions 2–4 withdrawn. All six decisions are now recorded in the registry; none is open.
- **Real-data pre-run checks implemented and run** (`scripts/run_s2_mom.py checks`): protocol and input hashes, A/D pairing (114/114 and 56/56), boundary, perturbation, truncation, random-ranking placebo. All passed. The OOS placebo p-value is 0.054, a narrow pass, recorded as such. The checks store pass/fail and counts only.
- **Not run:** blinded precision step, primary run, confirmation run. No real mean, Sharpe ratio, momentum p-value, drawdown or economic conclusion exists.
- **Still blocking a run:** Stage 2 rebuild check (disk about 1.3 GB free; not attempted), delivery cost evidence (five inputs), unfinished primary-table items, and the secondary and fixed-robustness analyses listed in `docs/research/phase3b_implementation_checklist.md`.
- Collector and ORB files untouched; UNIV-1, RET-1.1 and the frozen protocol unchanged.

## 2026-10-05 - Phase 3B final pre-run audit (no code or data changed; experiment NOT run)
- Wrote `docs/research/phase3b_final_prerun_audit.md`: requirement-by-requirement table, classification of every remaining item, cost-evidence acquisition list, Stage 2 rebuild requirement.
- **Blocking the primary run:** (1) Stage 2 rebuild check — about 1.3 GB free, macOS update staging unchanged, rebuild not attempted; (2) sensitivity treatments R-span, R-gap, R-miss, R-delist, which §25 uses to label the primary result; (3) saving holdings at the primary run; (4) costs — archive five rates or take step E out of the primary run mode; (5) authorisation to generate the blinded precision artifact.
- **Not blocking:** the multiple-testing corrections, secondary tests, remaining robustness analyses, tables and figures. Constraint from B3 and §25: no change to the hashed pipeline files between the primary and confirmation runs.
- **Placebo, diagnostic metadata only:** random-ranking p-value 0.4725 (primary) and 0.054 (OOS); both pass the fixed 5% rule; threshold unchanged; not evidence about momentum.
- **§22 counts:** 70 missed exits; 41 resume later; 29 never resume (28 entities; 26 with no delisting evidence receive −30%, 2 voluntary receive 0%); 12 flagged resumption rows; 2 primary cases resume after 2022-01-03. No return of these cases was computed for the audit.
- Open point for the reviewer: frozen §13 allows a current rate as a labelled assumption where history cannot be evidenced; the reviewer's instruction of today forbids using current rates as historical.
- No real research result exists. Collector and ORB files untouched. Frozen protocol unchanged.

## 2026-10-05 - Phase 3B final implementation before primary authorisation (experiment NOT run)
- **Sensitivity treatments (§16, §25) implemented and tested:** `R_SPAN`, `R_GAP`, `R_MISS_RAW`, `R_MISS_ZERO`, `R_DELIST_ZERO`, `R_DELIST_MINUS100`, plus the fixed "not reliable" labels. Each treatment reruns step D only on a modified copy; the primary matrices are never altered.
- **Primary calculation unchanged:** fingerprint of the internal A–D output identical before and after the change, both samples (hash only inspected).
- **Holdings and end-weights** are saved with each run (`*_holdings.csv`); a test reproduces turnover from the saved file.
- **Cost mode:** the frozen text does not require step E in the same run as the gross estimand (§2, B1.4, §3, §32 B2). The primary mode no longer needs cost evidence; step E, H4 and H4 sensitivity are written as `COST-EVIDENCE-PENDING`. Cost functions still refuse any missing rate.
- **Frozen §13 fallback** made explicit: each cost input has a basis (`HISTORICAL_EVIDENCE` or `CURRENT_RATE_ASSUMPTION` with period and reason). Three archived current rates are labelled as assumptions; five delivery inputs remain null. No external search made.
- **Stage 3 manifest refreshed** (one new file `research/gap_rows.csv`; all existing files byte-identical). **Pre-run checks rerun under the final code hash: all passed** (pairing 114/114 and 56/56; boundary; perturbation; truncation; placebo).
- **Placebo diagnostics:** primary p = 0.4725, OOS p = 0.054. Both exceed the fixed 5% rejection threshold; the OOS placebo is close to the threshold and is treated only as a diagnostic. Neither is evidence for or against the primary momentum hypothesis.
- **Stage 2 rebuild NOT run:** about 1.3 GB free; macOS update staging unchanged. It remains the one blocker before the blinded precision artifact can be authorised.
- No real research result exists. Collector and ORB files untouched. Frozen protocol, UNIV-1, ORB v1 unchanged.

## 2026-10-05 - Phase 3B: reviewer rulings after the consistency audit; fill-threshold fix (experiment NOT run)
- **R-span kept:** class-based per frozen §16; every special-session span row takes the raw two-session return in the sensitivity variant; no 1.4× exception. One row beyond that bound (ZEETELE 2024-01-23) stays included. It does not affect the primary A–D result, where all span rows are excluded.
- **R-gap "event"** recorded as an implementation interpretation, not literal §16 wording: parsed bonus/split factor or unadjustable record; dividend-only is not an event; no 1.4× bound. Counts: 1,192 gap rows; 1,130 no-event (1,085 no record, 45 dividend-only); 62 event (3 parsed factors, 59 unadjustable records).
- **Fix:** §25 fill threshold now tests W and L separately; fails if either is above 5%; exactly 5% does not fail (`src/stage3/experiment.py`).
- Tests 317 passed. Pre-run checks rerun under the new code hash: all passed. Primary A–D fingerprints unchanged.
- Cost inputs unchanged: five delivery inputs missing; exchange charge, SEBI fee and GST provisional current-rate assumptions pending an evidence search.
- Stage 2 rebuild still not run (about 1.3 GB free). No research result exists. Collector and ORB files untouched.

## 2026-10-05 - Stage 2 rebuild passed 150 of 150; pre-run gates for S2-MOM-v1 satisfied (experiment NOT run)
- Disk freed by the user (9.53 GiB free). `python3 scripts/build_stage2.py` run at 20:44–20:51: **150 checks passed, 0 failed, 0 files written.** Duration 383 s. Peak memory footprint 10.8 GB (8 GB RAM); swap peaked at 6.5 GB used (7.2 GB allocated); free disk 9.53 → 5.35 (lowest) → 5.48 GiB.
- Inputs: raw manifest `7dea91c9…`, `PHASE2_MANIFEST.json` `016e04d1…`, build script `8437b205…`. Outputs match every recorded hash, including UNIV-1 `2abf457a…cba9c42` and the RET-1.1 manifest `e1915b73…`. Log kept at `data/stage3/s2_mom_v1/checks/stage2_rebuild_20261005.log`.
- The pass is registered in the registry record (`provenance.stage2_rebuild`), after the fact as required.
- Stage 3 inputs re-verified identical; real-data pre-run checks rerun and passed for both samples; primary A–D fingerprints unchanged; tests 317 passed.
- **All pre-run gates for the blinded precision step are now satisfied. It has NOT been generated; it awaits explicit authorisation.** The primary and confirmation runs remain unauthorised.
- No research result exists. Collector and ORB files untouched. Frozen protocols unchanged. Nothing committed.

## 2026-10-05 - S2-MOM-v1: blinded step, primary, sensitivity and confirmation runs registered; cost-evidence audit; sequencing deviation recorded
- **Runs (each once, same code hash `f57c9321…fa1d1` for primary, sensitivity and confirmation):** blinded precision artifact `1e263410…5c693`; primary `fe7e95ba…f857`; sensitivity `7d6081d8…c19b`; confirmation `38d1d0a9…4d92`. Results are in `results/s2_mom_v1/` and the registry; they are not restated here.
- **Status by the frozen rules:** primary H1 inconclusive; §25 label "not reliable" (the special-session span treatment changes the H1 sign); confirmation H1 significant but not confirmed (opposite sign to the primary).
- **Mode split before the primary run:** the runner's primary mode was separated from a new sensitivity mode at the reviewer's request; ladder and data code unchanged; A–D fingerprints unchanged.
- **Step E not run.** Cost-evidence acquisition audit written: `docs/evidence/s2mom_cost_evidence_audit_20261005.md`. No input has archived evidence for the whole period; five have none; several points need a reviewer ruling (broker, exchange-charge slab, service tax before 2017).
- **Deviation DEV-1 recorded** in `docs/research/s2_mom_v1_deviation_log.md`: frozen §32 asked for open items B2, B3, B4 to be closed before any return was computed; they were open when A–D returns were computed. None enters the A–D calculation; results preserved unchanged.
- No cost or cost-adjusted return calculated. No experiment rerun. Nothing committed. Collector and ORB files untouched.

## 2026-10-05 - S2-MOM-v1 Addendum 1 (cost specification for step E) approved and registered
- **File:** `docs/research/phase3a_momentum_protocol_addendum1_costs.md` — a separate file; the frozen protocol and its hash are unchanged.
- **Addendum SHA-256:** `d12ccaa6fa23143f808b429d75c757a57a853afa42e961a94157d3b772dffefe`
- **Timing:** specified after the gross primary, sensitivity and confirmation results were known, and before any cost, turnover or net-return figure was computed. It changes no part of steps A–D.
- **Six rules approved by the reviewer:** Zerodha's dated delivery schedule; lowest-turnover (highest-rate) NSE slab before 1 Oct 2024; dated indirect tax (service tax with cesses, then GST) on the frozen base; ₹1 crore per portfolio at every rebalance, one order per stock, order value = absolute weight change × ₹1 crore; dated schedules for all class 1 inputs with the frozen §13 fallback after a documented search; sell-side charge = total billed by Zerodha per stock per sell day, any weight reduction counting as a sale once per rebalance.
- **Disclosed:** a flat per-stock sell-side charge weighs more on the benchmark, which holds more stocks, than on the winner portfolio. Not quantified.
- **Open:** B2 (no evidence acquired; cost schedule incomplete), B3 and B4. Step E not implemented and not run. No cost, turnover or net return computed. Nothing committed.

## 2026-10-05 - S2-MOM-v1: cost evidence acquired and archived for Addendum 1 (no cost schedule; step E not run; B2 open)
- **Archive:** `docs/evidence/s2mom_costs/` — 39 source files (18 official, 21 broker primary), with `MANIFEST.csv` (URL, class, dates, SHA-256) and `SHA256SUMS`.
- **Audit:** `docs/evidence/s2mom_cost_evidence_audit_stage2_20261005.md`, with a dated evidence matrix for the eight inputs and the IPFT relationship.
- **Established from official documents:** NSE cash transaction charge (lowest slab) 2009–2026; IPFT stated separately, ₹10 per crore from 2023-04-01 to 2026-02-28 and ₹0.01 otherwise where stated; SEBI fee ₹15 from 2017-04-01 and ₹10 from 2019-04-01; uniform stamp duty from 2020-07-01 and no single rate before; delivery STT 0.1% at 2012-07-01 (proposal document), 2024 and 2026.
- **Established from the broker's own dated pages:** delivery brokerage (lower of 0.1% or ₹20 per order to 2015-11-30, zero from 2015-12-01 for retail individuals); depository charge wording from 2016-10.
- **Not evidenced:** depository charge before 2016-10; indirect tax before 2016-10 and for 2017-07 to 2018-08 from any primary source; SEBI fee change date in 2014–2016; IPFT amount before 2023-03; enacted Finance Act 2012; stamp-duty rate notification.
- **Circular reference resolved:** the archived NSE circular prints its own number as NSE/FA/64232; the earlier note was correct.
- **Seven points need a further methodological decision** (account type; dating of broker captures; the 2020–21 temporary exchange-charge scheme; tax in the 2016–2019 depository charge; the 2020–21 SEBI fee halving; IPFT before 2023; acknowledgement of the stamp-duty fallback).
- B2 remains open; B3 and B4 remain open. No cost, turnover or net return computed. No protocol, addendum, code or result file changed. Nothing committed.

## 2026-10-06 - S2-MOM-v1: Supplement 1 to Addendum 1 registered; evidence-closure attempt; B2 remains OPEN
- **Supplement 1** (seven approved rulings on cost evidence): `docs/research/phase3a_momentum_protocol_addendum1_supplement1.md`, SHA-256 `ab28fd1750db3e222819013ef70ff69c4b48d5d5757d51ec5c77e9b6232253b3`. Addendum 1 and the frozen protocol are byte-identical.
- **Newly archived:** three official service-tax notifications (commencement dates 1 June 2015 and 1 June 2016; they state dates, not rates) and a search log. The manifest now lists 43 files.
- **Not obtained:** any archived source for a service-tax or GST rate; the SEBI instrument for the ₹20 fee; the enacted Finance Act 2012. Official tax, statute and budget addresses did not respond or refused.
- **Searches incomplete:** the Internet Archive index was offline for every query about Zerodha pages before October 2016 and before 27 September 2012. An outage is not a failed search, so the §13 fallback is not invoked for those inputs.
- **B2 remains OPEN.** Closure report: `docs/evidence/s2mom_cost_evidence_closure_report_20261006.md`. B3 and B4 remain open and separate.
- No cost schedule created. No cost, turnover, net return or break-even calculated. Step E not implemented or run. No experiment run. Nothing committed.

## 2026-10-06 - S2-MOM-v1: evidence closure, second pass; B2 CLOSED on the evidence test, two readings awaiting reviewer confirmation
- **Why a second pass:** the Internet Archive index was offline in the first pass. It was reachable this time.
- **Newly archived (21 source files + a search log; archive now 65 files, all hashes verified):** SEBI gazette of 23 May 2014 (fee ₹20 per crore, in force that day) and its press release; GST notifications 8/2017-Integrated and 11/2017-Central (18% from 1 Jul 2017); official service-tax texts (12% from 1 Jul 2012; Finance Act 2015, 14%; Swachh Bharat Cess 0.5% from 15 Nov 2015); Zerodha charge lists and account forms of May 2012, Dec 2012, May 2014, Jul 2014 (delivery brokerage; depository debit schedules); NSDL fee files (₹4.50 per debit, 2010–2016).
- **Resolved by evidence:** delivery brokerage 2 Jul – 26 Sep 2012; depository charge before Oct 2016; SEBI fee 2012–2017; indirect tax 2012–2018.
- **Completed failed searches, §13 fallback applies:** enacted Finance Act 2012 (delivery STT → current 0.1% each side); IPFT amount before April 2023 (→ current ₹0.01 per crore, ruling 6). Stamp duty before July 2020 stays on ruling 7.
- **Two readings need reviewer confirmation:** the Krishi Kalyan Cess rate for 1 Jun – 8 Oct 2016 rests on ruling 2 (official date, broker capture for the 15% total); the 2% and 1% education-cess rates before June 2015 rest on broker lists.
- **Not attempted (optional):** 2020 stamp-duty notification; SEBI 2020–21 halving instrument.
- Report: `docs/evidence/s2mom_cost_evidence_closure_report_20261006_pass2.md`. Search log: `docs/evidence/s2mom_costs/SEARCH_LOG_20261006b.txt`.
- Supplement 1 not re-created; its hash and Addendum 1's hash unchanged. 82 protocol, code, config and result files byte-identical to the start of the pass; 13 registry-recorded hashes match. No cost schedule created or edited. No cost, turnover, net return or break-even calculated. Step E not implemented or run. Registry not written. Nothing committed. B3 and B4 remain open.

## 2026-10-06 - S2-MOM-v1: dated delivery cost schedule created and validated (step E NOT implemented, NOT run)
- **Reviewer approvals recorded:** the two readings of the second-pass closure report (Krishi Kalyan Cess bracket, 1 Jun – 8 Oct 2016, labelled an evidence-based bracket assumption; education-cess rates 2% + 1%, Jul 2012 – May 2015, from three agreeing Zerodha lists, distinguished from the official 12%).
- **B2 — Evidence closure: PASS, subject to the approved readings. Cost-schedule closure: PENDING until the schedule contains no empty rate.** The new schedule contains no empty rate; the reviewer has not yet ruled on the second half.
- **Schedule:** `config/cost_schedules/delivery_nse_eq_s2mom_v1_dated.json`, SHA-256 `47a9bad407b87b781c3584986b76b23216c2af33eb2b2f9986d23f710098a10f`. Nine components, each dated over 2012-07-02 to 2026-09-01 with no gap and no overlap; every period cites archived files with hashes; every fallback and assumption is flagged. The older single-rate file `delivery_nse_eq_s2mom.json` was not edited.
- **Fallbacks in it:** delivery STT (whole sample); IPFT before 2023-04-01; stamp duty before 2020-07-01.
- **Validation:** `tests/test_s2mom_cost_schedule.py`, 40 passed; whole suite 359 passed.
- **Audit report:** `docs/evidence/s2mom_cost_schedule_audit_20261006.md`. Open caveat for the reviewer: IPFT is inside the tax base, following the frozen "Exchange transaction charge + IPFT" line.
- No turnover, cost, net return or break-even calculated. No experiment run or rerun. Frozen protocol, Addendum 1, Supplement 1, registered code, registry and all result files byte-identical. Nothing committed. B3 and B4 remain open.

## 2026-10-06 - S2-MOM-v1: step E cost code implemented and tested (NOT run)
- **Reviewer decisions recorded:** B2 evidence closure PASS; cost-schedule closure PASS; IPFT stays in the tax base as the frozen line reads; the higher-cost depository treatment for 2 Jul – 24 Dec 2012 and 4 Jul 2014 – 8 Oct 2016 accepted with both caveats kept; B3 and B4 remain open and do not block step E.
- **New code:** `src/stage3/step_e.py`, SHA-256 `250951a20e2029b41ba835b87f39429a87144d51625c74c77e39a9d7856e49fe`. Separate from the registered code, which is unchanged. It loads only the approved schedule (`47a9bad4…a10f`), checks the protocol, addendum and supplement hashes, and produces a per-order cost ledger from a saved-holdings table.
- **Tests:** `tests/test_s2mom_step_e.py`, 40 passed, synthetic holdings only; whole suite 399 passed.
- **Not implemented:** a runner that reads the saved files (needs an allow-list line in the access-boundary test, a safety guard that was not edited); slippage S1–S4, break-even and H4.
- **Report:** `docs/research/s2_mom_v1_step_e_implementation_report_20261006.md`.
- Step E not run. No real cost, turnover, net return or break-even calculated. No result file, schedule, protocol, addendum or supplement changed. Nothing committed.

## 2026-10-06 - S2-MOM-v1: Supplement 2 to Addendum 1 registered (step E method, rulings 8-16; step E NOT run)
- **Supplement 2** (nine approved rulings on the step E method): `docs/research/phase3a_momentum_protocol_addendum1_supplement2.md`, SHA-256 `6c373c5ff0db321cb753fff7a08db078ff29ca2c3f2f0cfbe8c0fb1431e6a888`. The frozen protocol, Addendum 1 and Supplement 1 are byte-identical.
- **Rulings:** 8 first month bought from cash; 9 no terminal liquidation; 10 primary and confirmation costed independently, each from cash; 11 slippage S0-S4 one-way on traded value, both sides, outside the tax base; 12 break-even = x / d with two undefined cases; 13 H3 supported in the primary sample (H4 eligible there, one-sided Newey-West, lag 4) and not supported in confirmation (H4 not run there); 14 W and benchmark costed, L costed as a hypothetical long portfolio; 15 required outputs; 16 S1-S4 are pre-specified scenarios.
- **Amended by the reviewer before hashing, no result existing:** ruling 11 uses the UNIV-1 rank at the rebalance where the order trades, so exit sales of stocks that left the top 200 can take the 201-500 rate, and stocks above rank 500 or unranked take the 201-500 rate as an assumption; ruling 14's hypothetical net WML deducts the costs of both legs. Ruling 15 is kept: no confirmation break-even, disclosed as a narrowing of the frozen §13 "always reported" line.
- **Timing:** specified after the gross A-D results and the H3 outcomes were known and before any real cost, turnover, net return, break-even or H4 result was computed. It changes no A-D calculation.
- **Verification:** frozen protocol, Addendum 1, Supplement 1, the dated cost schedule, the registered code hash `f57c9321…fa1d1`, and every registered primary, sensitivity and confirmation result file match their recorded hashes.
- Step E not changed and not run. No runner built. No real data read for a calculation. No cost, turnover, net return or break-even calculated. `src/stage3/step_e.py` unchanged. Nothing committed. B3 and B4 remain open.

## 2026-10-06 - S2-MOM-v1: Supplement 3 to Addendum 1 registered (step E input boundary and identifier join, rulings 19-20; step E NOT run)
- **Supplement 3:** `docs/research/phase3a_momentum_protocol_addendum1_supplement3.md`, SHA-256 `682191de462bac3b5d2901995be8d20d355bb4d6146fd87a3f02ed8c6c2580ce`. Input-boundary and implementation-methodology amendment only; it changes no A-D calculation and no existing result. The frozen protocol, Addendum 1, Supplement 1 and Supplement 2 are byte-identical.
- **Ruling 19:** step E covers the primary and the confirmation sample. Exactly five read-only data inputs, each hash-checked before any read: `primary_holdings.csv` `38879957…93748`, `primary_monthly.csv` `f7c8d3ab…bb372`, `confirmation_holdings.csv` `96bb174e…825b0`, `confirmation_monthly.csv` `4d88f385…43ce3`, `data/stage2/universe/univ1_pit_universe.parquet` `2abf457a…a9c42`. One access-boundary entry for the runner. `id1_segments.csv` and the RET-1.1 return files are not required.
- **Ruling 20:** join is holdings `(t, entity)` -> UNIV-1 `(selection_date, entity_id)`; `segment_at_selection` is not the key; no other identifier or date is tried; a duplicate or null UNIV-1 key is a hard failure. Guard: every held stock's UNIV-1 rank must equal the saved `liquidity_rank`, or the run stops before any cost. Exit orders use the UNIV-1 rank at the exit rebalance; above 500 or unranked takes the 201-500 rate as a counted fallback; a missing or duplicate exit row is a hard failure.
- **Ruling numbers:** the reviewer's "Ruling 17" and "Ruling 18" are the two parts of ruling 11 as amended in Supplement 2 (rank at the trading rebalance; 201-500 fallback). Supplement 3 also clarifies that "no UNIV-1 rank" means a row with an empty rank, not a missing row.
- **Key-only compatibility check (identifiers only; no rank, weight, return or price read):** step D holdings of W, L and the benchmark match UNIV-1 `entity_id` directly: held pairs 21,405 of 21,405 (primary) and 10,491 of 10,491 (confirmation); exit pairs 3,120 of 3,120 and 1,667 of 1,667. The UNIV-1 key is unique with no null.
- **New code, separate from `step_e.py` and from the registered code:** `src/stage3/step_e_ranks.py`, SHA-256 `9579fcec85a3d9d2c8e51a02c4ce6fe0528b44684a631e5e896c6b67296008bb` (rank lookup, formation-rank guard, slippage band; pure functions, opens no file, calculates no cost). Tests: `tests/test_s2mom_step_e_ranks.py`, SHA-256 `9070294cf20415574a136b31a2374536dbfe51c768a11325df2e0289e708d869`, 9 passed, synthetic frames only.
- Step E not implemented further and not run. `src/stage3/step_e.py` unchanged. No runner and no access-boundary entry created. No cost, turnover, net return or break-even calculated. No result file changed. Nothing committed. B3 and B4 remain open.

## 2026-10-06 - S2-MOM-v1: step E rank-lookup module and its tests deleted at the reviewer's instruction
- **Deleted:** `src/stage3/step_e_ranks.py` (SHA-256 `9579fcec…008bb`) and `tests/test_s2mom_step_e_ranks.py` (SHA-256 `9070294c…8d869`), both created in the previous entry. The reviewer ruled that the module is step E implementation logic and that implementation is not yet authorised. The previous entry's line on "new code" no longer describes the repository.
- **Kept:** Supplement 3 (`682191de…580ce`) is unchanged and remains registered. Its sections 3.1 and 3.2 hold the specification the deleted tests expressed; the synthetic cases are to be recreated when step E implementation is authorised.
- No protocol, addendum, supplement, cost schedule, registered code, `step_e.py` or result file changed. No runner exists. No cost calculated. Step E not run. Nothing committed.

## 2026-10-06 - S2-MOM-v1: step E fully implemented and tested for Supplements 2 and 3 (NOT run)
- **Authorisation:** implementation authorised by the reviewer; execution not authorised.
- **Code:** `src/stage3/step_e.py` changed, SHA-256 `60f9dba07e047b7927cdff8f4bb3b7107f2a748f81eae79b044b77d027863c82` (UNIV-1 rank join and formation-rank guard, slippage S0-S4, net returns, hypothetical L and hypothetical net WML with both legs' costs deducted, H3 -> H4, break-even). New runner `scripts/run_s2_mom_step_e.py`, SHA-256 `d3107fbf566639e08cd40e30b7a1b893e158c8c8c49b7e47a8a4a5c47a681a3a`. Combined step E code hash `aeac592a…c7b33`. Registered experiment code unchanged (`f57c9321…fa1d1`).
- **Input boundary:** one allow-list line added to `tests/test_access_boundary.py` for the runner. Exactly the five inputs of Supplement 3, each hash-checked before any read; refusal on any difference; refusal if the output directory `results/s2_mom_v1_step_e/` exists.
- **Tests:** `tests/test_s2mom_step_e_scenarios.py`, 37 passed, synthetic data only; whole suite 436 passed. Independent hand calculation on made-up holdings: 42 checks pass.
- **For the reviewer:** H3 in the confirmation sample uses the registered lag 3 (frozen §15), H4 lag 4; H3 is recomputed from the approved monthly files and must equal the decision recorded in Supplement 2; outputs go to a new directory outside `results/s2_mom_v1/`; the formation-rank guard has not met real data.
- **Report:** `docs/research/s2_mom_v1_step_e_full_implementation_report_20261006.md`.
- Step E not run. No real cost, turnover, net return, break-even or H4 calculated. No step E result file exists. No protocol, addendum, supplement, cost schedule, registered code or result file changed. Nothing committed. B3 and B4 remain open.

## 2026-10-06 - S2-MOM-v1: ruling 21 (formation-rank guard scope) applied; runner registration made last and atomic (step E NOT run)
- **Ruling 21 (reviewer):** the formation-rank equality guard (UNIV-1 rank at the selection date == saved `liquidity_rank`) applies only to W and L. It is not applied to the benchmark, which is not a ranked W/L selection. The benchmark is still costed under the same rules; its slippage band comes from the same UNIV-1 lookup at the trading rebalance, and that lookup stays strict (missing row, duplicate or null key, invalid rank: hard failure). No other ruling changed.
- **Where recorded:** this log, the implementation report (section 3a) and the code (`RANK_GUARDED`). It narrows Supplement 3 §3.1 ("for every held stock"); Supplement 3 is registered and was not edited. Ruling 21 is not in a registered supplement.
- **Runner registration (approved with a requirement):** the registry and trials log are written only after a completely successful run with final output hashes; a refused, failed or interrupted run registers nothing; outputs are written to a `.partial` directory and renamed when complete; an existing output or partial directory is never overwritten or deleted.
- **Code:** `src/stage3/step_e.py` SHA-256 `17e1908270bf544878164ed6b0704af5ba74a7a440055684f78b0cc56c397554`; `scripts/run_s2_mom_step_e.py` SHA-256 `997d25ba88111eea113b0f52a8cc16f2948bc59cad689c085dd3e07d0508ae6d`; combined step E code hash `a6845d30…acc54`. These replace the hashes in the previous entry. Registered experiment code unchanged (`f57c9321…fa1d1`).
- **Tests:** `tests/test_s2mom_step_e_scenarios.py` 41 passed; whole suite 440 passed. Independent hand check of the guard: 9 checks pass.
- Step E not run. No real cost, turnover or net return calculated. No step E output or partial directory exists. The five inputs, the frozen protocol, Addendum 1, Supplements 1-3, the cost schedule and every existing result file are byte-identical. Nothing committed. B3 and B4 remain open.

## 2026-10-06 - S2-MOM-v1: Supplement 4 to Addendum 1 registered (formalises ruling 21; step E NOT run)
- **Supplement 4:** `docs/research/phase3a_momentum_protocol_addendum1_supplement4.md`, SHA-256 `e4617ccb6fa8713ea5a1f82843e5ee1d5fceda84432675c3ce081047b7508b87`. It formally registers ruling 21, already approved by the reviewer during the step E implementation review, and makes no other methodological change.
- **Ruling 21:** the formation-rank equality guard (saved `liquidity_rank` == UNIV-1 rank at the selection date) applies only to W and L; a missing or empty saved rank, a missing, duplicate, malformed or invalid UNIV-1 key or rank, or a mismatch is a hard failure before any cost. The benchmark is not subject to the guard and its saved rank is ignored for it; its slippage still needs the strict UNIV-1 lookup at the trading rebalance. Applied identically to both samples. It is a scope clarification of Supplement 3 §3.1.
- **Unchanged:** no step E formula, rate, cost convention, portfolio definition, slippage scenario, H3/H4 rule, break-even rule or A-D result. The frozen protocol, Addendum 1, Supplements 1-3, the five step E inputs, the cost schedule, every existing result file and the registered experiment code are byte-identical. The step E implementation and runner were not changed; they already apply ruling 21 (`step_e.py` `17e19082…97554`, runner `997d25ba…8ae6d`).
- **Note:** `step_e.py` checks the hashes of Supplements 2 and 3 on every load. Supplement 4 is not in that check, because the code was not to be changed in this step.
- Step E not run. No real cost, turnover, net return, break-even or H4 calculated. No step E output exists. Nothing committed. B3 and B4 remain open.

## 2026-10-06 - S2-MOM-v1: step E executed once and registered (execution record; no interpretation)
- **Authorisation:** explicit, separate authorisation by the reviewer for one real-data execution.
- **Command:** `python3 scripts/run_s2_mom_step_e.py execute`, run once. Started 2026-10-06T22:29:10, ended 2026-10-06T22:29:16 (+05:30). **Exit status 0.**
- **Pre-flight:** 18 of 18 checks passed before execution (frozen protocol, Addendum 1, Supplements 1-4, dated cost schedule, the five inputs, `step_e.py` `17e19082…97554`, runner `997d25ba…8ae6d`, combined step E code hash `a6845d30…acc54`, registered experiment code `f57c9321…fa1d1`, no existing output or partial directory).
- **Scope completed:** primary sample 114 months, 38,050 orders; confirmation sample 56 months, 18,841 orders; W, the benchmark and the hypothetical L portfolio under S0-S4.
- **Guards:** the W/L formation-rank guard passed for every W and L stock in both samples. No UNIV-1 lookup was missing for any benchmark order or exit order. No check failed and no break-even case was undefined. The runner's refusal conditions did not trigger.
- **Outputs (`results/s2_mom_v1_step_e/`, SHA-256):**
  - `primary_step_e_ledger.csv` `75d0fbb0ae2eedda5970836d66c6961f6203e0c3d4bf63134421371dc3397352`
  - `primary_step_e_monthly.csv` `3ec30ebdd256234c61bd82292dc01b3acbf582e94eec7f558f06f715b8b3dfd7`
  - `confirmation_step_e_ledger.csv` `547c7be5adfc82d6fc62b7517b698c14199032d8041a34b84de61ea9a5ac1037`
  - `confirmation_step_e_monthly.csv` `f43b4a4d9d9898a45ff2d46fa3e0381b1386ec35f4a8e3d92de898d5a2f10638`
  - `step_e_results.json` `675398488b4a9c11a3f25d70afd32ce3d6f62340e0d9a8a0d3c33df7f7b039e0`
- **Registration:** made by the runner only after the outputs were complete and hashed: one registry amendment ("step E run registered", `provenance.step_e_run`, 2026-10-06T22:29:16) and one trials-log line. No partial directory was left.
- **Tests carried out as frozen:** H3 recomputed from the approved monthly files equals the registered decision in both samples (primary supported, confirmation not supported). H4 was run for the primary sample only. The break-even was computed for the primary sample only. Neither was run for the confirmation sample. The figures are in `step_e_results.json` and are not restated here.
- **Unchanged:** every pre-existing file was byte-identical after the run except `registry/experiments.jsonl`, `registry/trials.jsonl` and the regenerated `EXPERIMENT_REGISTRY.md`; this includes the 12 files of `results/s2_mom_v1/` and the five inputs.
- **Housekeeping afterwards:** the pre-execution test that required the output directory to be absent was replaced by a post-execution integrity test of the five output hashes (`tests/test_s2mom_step_e_scenarios.py`). No result, code, runner, protocol, supplement or schedule was changed.
- This entry records execution facts only. It contains no scientific interpretation. Nothing committed. B3 and B4 remain open.

## 2026-10-07 - S2-MOM-v1: C2 late analyses specified, executed once and registered (execution record; no interpretation)
- **Decision (reviewer, 2026-10-07):** of the pre-registered analyses never executed, seven are computed from the saved registered files with no backtest: H2d, Holm, Benjamini-Hochberg, the two halves of the primary sample (lag 3 by the frozen formula), the pooled 170 months (gross A-D and delta only, descriptive), skewness, worst month. All others stay not executed (to be disclosed as DEV-2).
- **These analyses were pre-registered but executed late, after the primary, sensitivity, confirmation and step E results were known. They are not blind and not confirmatory.**
- **Specification, written and hashed before any calculation:** `docs/research/s2_mom_v1_c2_analysis_spec.md`, SHA-256 `78864a4f6fddad86a7b3273e8d8c1e7ab818ed318deb0fdb75cc99e2c5a0c0aa` (hashed 2026-10-07T13:37:35+05:30).
- **Code:** `scripts/run_s2_mom_c2.py`, SHA-256 `505b2e4ed9d4e1f34dc2e441f2ff73e8399998e4744a6f0b4b7d62e59668b3fa`; tests on made-up series in `tests/test_s2mom_c2.py`. It imports `src.stage3.stats.mean_test` only; no backtest, ladder, data or step E code.
- **Inputs (all six hash-checked before any read):** `primary_monthly.csv` `f7c8d3ab…b372`, `confirmation_monthly.csv` `4d88f385…3ce3`, `primary_delta.csv` `2efa0435…ecc9`, `confirmation_delta.csv` `a462455a…8b75`, `primary_results.json` `fe7e95ba…f857`, `step_e_results.json` `67539848…39e0`.
- **Command:** `python3 scripts/run_s2_mom_c2.py execute`, run once. Started 2026-10-07T13:39:46, ended 13:39:49 (+05:30). **Exit status 0.** Guards passed: recomputed delta equals both registered delta files; the primary block reproduces the registered primary means and t-statistics.
- **Output:** `results/s2_mom_v1_c2/c2_results.json`, SHA-256 `cf977e8a5efce7ba83ce91bf70ae247ed1aea96c7004f8d03162669097689513`.
- **Registration:** by the runner after the output was complete and hashed: one registry amendment (`provenance.c2_run`, with command, hashes and environment) and one trials-log line.
- **Environment:** python 3.13.5, pandas 2.2.3, numpy 2.1.3, scipy 1.15.3, macOS arm64; git `7d4cb6d977` (dirty).
- **Unchanged (hashed before and after):** the 12 files of `results/s2_mom_v1/`, the five of `results/s2_mom_v1_step_e/`, the frozen protocol, Addendum 1 and Supplements 1-4, the deviation log, the cost schedules, ORB v1, UNIV-1.
- **Also changed:** one allow-list line in `tests/test_access_boundary.py` for the new runner; `EXPERIMENT_REGISTRY.md` regenerated.
- The figures are in `c2_results.json` and are not restated here. Nothing committed. DEV-2 and the metadata amendments are proposed, not applied. B3 and B4 remain open.

## 2026-10-07 - S2-MOM-v1: metadata corrections and DEV-2 recorded (append-only; no result changed)
- **Registry:** six append-only amendments to record `S2-MOM-v1`: status PLANNED -> FINAL with the executed-run fields; stale "step E / H4 not run" wording; stale PENDING fields mapped by a results guide; cost schedule reference corrected to `delivery_nse_eq_s2mom_v1_dated.json` (`47a9bad4…a10f`); §25 criterion 3 evaluated for H1 and H3 only, H4 sensitivity unknown; the confirmation "MATERIAL" label is outside the primary-only scope of §27 and is not a registered conclusion. `EXPERIMENT_REGISTRY.md` regenerated.
- **New:** `docs/research/s2_mom_v1_results_guide.md` (presentation layer only).
- **Deviation log:** a dated status update to DEV-1 and **DEV-2** appended; the original text is preserved byte for byte.
- **Not edited:** the frozen protocol (its header "not yet registered" was true at the freeze), Addendum 1, Supplements 1-4, the C2 specification, every result file, the cost schedules, ORB v1.
- No analysis run. No backtest run. Nothing committed. B3 and B4 remain open.

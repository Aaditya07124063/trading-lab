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

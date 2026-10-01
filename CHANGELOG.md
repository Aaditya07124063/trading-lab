# Changelog

Code/infrastructure changes by commit. Research findings go in
[RESEARCH_LOG.md](RESEARCH_LOG.md).

- 678f0f9 checkpoint before hardening
- cd3743c fix: harden daily research engine (leaderboard schema, explicit saves, CAGR/Sharpe/exposure, paper-bot T+1 replay, pytest suite)
- 0869767 feat: intraday backtesting engine
- 2a976bf feat: intraday cost model (configurable, no rates in code)
- 29c1d17 feat: ORB strategy + adversarial look-ahead tests
- a569a94 feat: intraday data pipeline
- ccf061e data: extend m15/h1 intraday history to 2026-09-30
- 46624f7 feat: intraday research runner with dev/validation/OOS split
- f8aff70 feat: intraday research dashboard
- e1b82fe research: master specification, research log, NSE evidence
- 9dcee96 feat: data registry, experiment registry, daily validation, clean datasets, holdout lock, raw snapshots
- 6849ea8 research: registry entries linked to registering commit
- (next) research: cost sources, cost scenarios, literature review, ORB protocol v1 (DRAFT)
- (docs) literature stage: SSRN 5198458 record, ORB literature review v1, SSRN-vs-ORB v1 comparison, gap analysis, ORB v1 proposed revisions (not applied); literature PDFs git-ignored
- (docs/scripts) verification: CAS exit-bar semantics and SSRN bootstrap check (synthetic); evidence in docs/evidence/cas_2026; memo/proposal corrections
- a9a8f7f feat: ORB v1 exit X2 (15:00 bar open), complete-session rule, fixed-notional sizing; legacy_v0 for old runs
- 7cfad45 feat: ORB v1 inference (stationary bootstrap, PW block length), portfolio aggregation, baselines D/E, regime labels
- 41a7a30 research: ORB v1 pre-holdout implementation validation (DIAGNOSTIC)
- (docs) ORB v1 final protocol review (proposed, not frozen)

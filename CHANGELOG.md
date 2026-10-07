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
- 8d21e3e feat: locked evaluation pipeline, NSE calendar, bhavcopy check, deflated Sharpe (reporting), power script; (docs) pre-freeze audit
- 13e4664 feat: official NSE regime source, per-session malformed-data rule, flag-only bhavcopy; (docs) final pre-freeze audit
- (phase 1) feat: central access boundary (research cutoff 2026-09-30, holdout authorization artifact + single-use guard), dashboard cutoff, operational status field list, frozen-methodology hash tests
- (stage2 phase2) data foundation: NSE raw archive + manifest, PANEL-1, CA-2, ID-1, UNIV-1, RET-1, tests (233 pass), docs/stage2/data reports
- (stage2 phase2.1) fixes: weekend special sessions archived (27) with 5xx retries, session_type + weekend calendar QA (PANEL-1.1), RET-1.1 (SPECIAL_SESSION_SPAN, VALIDATED_LARGE_RESIDUAL), scripts/build_stage2.py deterministic rebuild/verify, UNIV-1 tracking statement corrected; UNIV-1, RET-1 and ORB v1 unchanged
- (stage3) S2-MOM-v1: Stage 3 inputs, ladder A-D, statistics, runners (blinded, primary, sensitivity, confirmation), step E costs, C2 late analyses, manuscript builder; registered results under results/s2_mom_v1*
- (remediation 2026-10-07, forensic audit F-01..F-06, F-11, F-12, F-28) registry: fail-closed hash-chained state machine with protected fields and anchors (src/registry/experiments.py); provenance chain registry -> Stage 3 manifest -> inputs and explicit input validation (src/registry/integrity.py); read-only reproduction with an independent implementation (scripts/reproduce_s2_mom_v1.py); external data archive manifest (scripts/release_archive.py, release/s2_mom_v1/); pinned environment (requirements-lock.txt); mutation campaign, failure injection and manuscript verification tooling; 461 new tests. No frozen code, protocol, input or registered result changed; registry gained two anchoring amendments

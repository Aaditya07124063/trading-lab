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

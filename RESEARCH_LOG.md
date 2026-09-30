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

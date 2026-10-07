# Trading Lab — documentation ↔ code consistency (2026-10-07)

Compared: `README.md`, `REPRODUCIBILITY.md`, `METHODOLOGY.md`, `CHANGELOG.md`, the frozen protocol (`docs/research/phase3a_momentum_protocol.md`), addendum and supplements, `s2_mom_v1_deviation_log.md`, `s2_mom_v1_results_guide.md`, runner docstrings and CLI text, the registry record, and the implementation.

No documentation was changed. For each contradiction the audit states which side is authoritative.

## 1. Protocol ↔ implementation: rules that match (VERIFIED BY INSPECTION and by the independent recomputation)

B1.1 Top200 (status filter, entity mapping, pool filter, smaller rank kept, first 200) · rankable rule (row dated exactly m(12) and m(1); step D adds "no flagged row in the window") · formation product over (m(12), m(1)] · k = floor(0.30n + 0.5), descending, ties by entity id · holding over (s⁺, s⁺⁺], equal weights, no row → 0 · benchmark = all rankable · step A list fixed at T\* · step B = same pool at t · step C = UNIV-1 MEMBER, delisting rule on · step D = `ret_research` · §20(a) span days left out · §20(b) neutral fill · §22 delisting 0 % / −30 % · §15 Newey-West with lag 4 / 3 and normal reference (registered decision) · bootstrap 10,000 resamples, fixed seed · §13 tax base, slippage table, S0 for H4, break-even · §23 turnover ½Σ|target − drift| · §25 count thresholds · B3 confirmation refused without a registered primary run of the same code.

## 2. Contradictions and gaps

| ID | Document says | Code / state does | Authoritative | Severity |
|---|---|---|---|---|
| D-01 | `REPRODUCIBILITY.md`: to reproduce a registered result, "check out its `environment.git_commit`" | For S2-MOM-v1 that commit (`7d4cb6d`) has no experiment code; README, REPRODUCIBILITY, METHODOLOGY and CHANGELOG never mention Stage 3 or S2-MOM-v1 | the registry is right about the commit; the documents are incomplete | P2 |
| D-02 | Registry `provenance.code`: "src/stage3/, scripts/build_stage3.py, scripts/run_s2_mom.py" and `freeze_commit` | none of those paths is in the freeze commit; `git_dirty: true` is recorded honestly | state of the repository (F-01) | P1 (same as F-01) |
| D-03 | Protocol B2 check 1: perturb "every price, flag, liquidity value and membership row dated after t" | `experiment._perturbed` changes returns and research-grade flags only | protocol; the code is narrower (F-13) | P2 |
| D-04 | Protocol §14: Sharpe-type ratio for long-only portfolios is "the information ratio against that step's benchmark" | `_describe` reports `mean_over_sd` for every portfolio; no information ratio is computed; not listed in DEV-2 | protocol; the output is honestly named, the metric is simply missing | P3 |
| D-05 | Protocol §27 table: interval wholly inside ±0.10 → "immaterial" | code tests "H0 rejected" first, so a significant estimate inside the band is `DETECTED_SIZE_UNCERTAIN` | protocol is ambiguous; needs a ruling. Not triggered | P3 |
| D-06 | Protocol §27: decision rules "for H1 (primary sample)" | `analyse` writes `H1.decision` for the confirmation sample too (`MATERIAL`) | protocol. Already disclosed: registry metadata correction 6 and the results guide | closed (disclosed) |
| D-07 | Protocol §6: "Counts are reported by month and by reason" | monthly file has `n_universe` and `n_rankable`; no count by reason | protocol; minor reporting gap | P3 |
| D-08 | `step_e.py` docstring: "No cost is ever assumed or set to zero" | `net_returns` uses `.fillna(0.0)` for a portfolio-month with no ledger row | docstring states the intent; the code is looser. Not triggered (F-17) | P2 |
| D-09 | `run_s2_mom.py` docstring: "Each mode runs once" | `checks` can be rerun and overwrites its files; the other modes are stopped only by file existence, after the whole calculation has already run in memory | docstring; behaviour is weaker (F-08) | P2 |
| D-10 | `experiment.analyse` docstring: "Called only by the runner" | importable and callable from anywhere, no gate (L-01) | documentation only | P2 |
| D-11 | `experiments.py` docstring: registry "never edited"; "EVERY backtest run … so the true number of tests is known" | nothing prevents an edit; a run that crashes before the end, or runs with `TRADING_LAB_NO_TRIAL_LOG`, is not logged | documentation only (F-03, F-08, F-11) | P1 / P2 |
| D-12 | Protocol B3 step 2: "Protocol and code are frozen and hashed" before the primary run | protocol frozen in a commit; code hashed at run time only, and changed once after the blinded step (recorded in RESEARCH_LOG line 357, δ hash unchanged) | acceptable with disclosure; not in the deviation log (R-4) | P3 |
| D-13 | README "Quick start" and architecture section | describe only the legacy daily engine; `data/ (36 CSVs…)` is out of date | README is stale | P3 |
| D-14 | Stage 2 doc: a gap row may mean "suspension/other series" | Protocol §30 threats list does not mention series changes being treated as non-trading (R-2) | research disclosure | for the researcher |
| D-15 | Results guide and registry say primary/confirmation result files contain stale `PENDING` fields that must not be edited | true, and handled correctly by the guide | consistent | — |

## 3. CLI help ↔ behaviour

1. `run_s2_mom.py` with no or an unknown mode prints the docstring and exits 1 — matches.
2. `run_s2_mom_step_e.py` and `run_s2_mom_c2.py` accept only the single word `execute`; anything else prints the docstring and exits non-zero — matches.
3. `evaluate_orb_v1.py` exposes only `--dry-run-dev` — matches "no tuning options".
4. `update_intraday.py --dry-run` writes nothing (log and files) — matches by inspection.

## 4. Manuscript

`build_manuscript.py` fills numbers from registered files, verifies 27 hashes, and its own log reports 699 checks passed. The audit did not re-read the manuscript text claim by claim. Label: **UNVERIFIED** for prose; SUPPORTED BY HASH for the numbers' sources.

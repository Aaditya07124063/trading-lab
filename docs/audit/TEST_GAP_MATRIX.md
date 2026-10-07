# Trading Lab — test gap matrix (2026-10-07)

Y = tested · P = partly · N = not tested. Derived from reading the 28 test files, the coverage run and the mutation run.

| Component | happy path | empty input | missing input | malformed input | boundary | adversarial input | failure | recovery | determinism | security | regression test |
|---|---|---|---|---|---|---|---|---|---|---|---|
| stage2.archive.fetch | Y | N | P | N | Y | N | Y | P | N | P | N |
| stage2.panel.parse/qa | Y | N | N | P | Y | P | Y | N | P | Y | N |
| stage2.corporate_actions | Y | P | N | Y | Y | Y | Y | N | P | Y | N |
| stage2.identity | Y | N | N | P | Y | Y | P | N | P | Y | N |
| stage2.universe.build | Y | N | N | N | P | Y | Y | N | Y | Y | N |
| stage2.returns.build | Y | N | N | P | P | Y | Y | N | P | Y | N |
| scripts/build_stage2.py | N | N | N | N | N | N | N | N | N | N | N |
| stage3.data.build/load_inputs | N | N | N | N | N | N | N | N | N | P | N |
| stage3.ladder (A-D) | Y | P | Y | N | Y | Y | P | N | Y | Y | P |
| stage3.stats | Y | N | N | N | P | N | P | N | Y | N | P |
| stage3.experiment.analyse | Y | N | N | N | N | Y | N | N | Y | N | N |
| stage3.step_e + runner | Y | P | Y | Y | Y | Y | Y | Y | Y | Y | Y |
| scripts/run_s2_mom.py | N | N | P | N | N | N | P | N | N | P | N |
| scripts/run_s2_mom_c2.py | Y | N | P | Y | P | N | Y | P | N | Y | Y |
| registry.experiments | P | N | N | N | N | N | N | N | N | N | N |
| access (cutoff, holdout gate) | Y | P | Y | Y | Y | Y | Y | N | N | Y | Y |
| evaluate_orb_v1.py | N | N | N | N | N | P | P | N | N | P | N |
| intraday engine / inference | Y | P | P | P | Y | Y | P | N | Y | N | Y |
| server.py | Y | N | P | N | P | N | P | N | N | P | N |
| update_intraday / pipeline | Y | P | N | Y | Y | P | Y | P | N | N | N |
| research_view | Y | N | P | N | N | P | Y | N | N | Y | N |

## Gaps to close (tests only; no source change)

| ID | Component | Surviving mutation(s) | Missing test | Priority |
|---|---|---|---|---|
| G-01 | ladder._hold (step D) | holding drops exit session (RG) | Step D holding return must include the exit-session return (give the last day a non-zero return) | HIGH |
| G-02 | ladder.wide / run_ladder (step D) | RG uses non-research-grade rows | Step D must use ret_research where it differs from ret_raw (validated bonus row) and must leave span days out of the FORMATION return | HIGH |
| G-03 | ladder.run_ladder | WML = W + L | Assert WML == W - L numerically for every month | HIGH |
| G-04 | ladder.wide | missing-price stop disabled | A missing naive return on a non-first row must raise | MEDIUM |
| G-05 | stats.bootstrap_test | bootstrap one-sided | Two-sided count: a series with a negative mean must give the same p as its mirror image | HIGH |
| G-06 | experiment.analyse | H1 decision threshold flipped; economic conclusion uses two-sided p | Table-driven test of the four section 27 labels and of the two one-sided economic conclusions | HIGH |
| G-07 | step_e.cost_ledger | rate date = exit not entry; STT sell uses buy rate key swapped | A schedule whose rate changes between entry and exit, and whose buy and sell STT differ | MEDIUM |
| G-08 | data.load_inputs / load_ret / load_univ | stage3 input hash check off; RET-1.1 hash check off; UNIV-1 hash check off | Temporary-directory tests: a changed file is refused by each loader | HIGH |
| G-09 | run_s2_mom._write and mode bodies | runner overwrite guard off; confirmation without same-code primary; blinded artifact gate off | Runner tests on a temporary tree: second run refused; confirmation refused when the primary code hash differs; blinded file with a wrong hash refused | HIGH |
| G-10 | universe.build | liquidity window 63->64; min valid 50->49; liquidity mean instead of median; identity links from the future | Boundary tests at exactly 63 sessions and 50 valid sessions; a skewed value series where mean and median rank differently; a later link that would merge two entities existing at t | MEDIUM (real data pinned by the UNIV-1 hash) |
| G-11 | returns.build | jump threshold 1.4->1.5; event attached to row before ex-date; ex-date boundary prev_date <= ex | Rows at ratio 1.45; an ex-date on a non-session day; an ex-date equal to the previous row's date | MEDIUM (real data pinned by the RET-1.1 hashes) |
| G-12 | corporate_actions.classify | validation band 1.25->2.0 | A residual of 1.5x must be DISCREPANT | MEDIUM |
| G-13 | registry.record / amend | registry unknown status allowed | record() with an unknown status raises; state-machine tests of F-03 | HIGH |
| G-14 | protocol constants | alpha, top_n, delist return (killed only by a constant-equality test) | Behavioural tests that fail when the constant changes (e.g. a -30 % delisting return in a ladder test already exists for OTHER; add alpha and top_n) | LOW |
| G-15 | whole pipeline | - | Golden reproduction test (F-05) | HIGH |
| G-16 | evaluate_orb_v1.run, build_stage2, data_registry, archive | - | End-to-end tests on synthetic inputs (0-40 % coverage today) | MEDIUM |

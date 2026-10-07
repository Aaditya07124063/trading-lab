# Trading Lab — mutation test report (2026-10-07)

Method: one deliberate change at a time, applied to a **scratch copy** of the repository (never to the project), then the full 451-test suite. The copy was restored after each run. No mutation was kept. No registered artifact was touched.

Mutations: 104. Killed by a behavioural test: 77. Killed only by a constant-equality test: 3. **Survived: 24.**
Kill rate: **80/104 = 77 %**.

| Group | Mutations | Killed | Survived | Kill rate |
|---|---|---|---|---|
| costs (step E) | 17 | 15 | 2 | 88 % |
| guards and registry | 17 | 11 | 6 | 65 % |
| research logic (ladder, protocol constants) | 34 | 30 | 4 | 88 % |
| stage 2 data | 18 | 10 | 8 | 56 % |
| statistics and decisions | 18 | 14 | 4 | 78 % |

## Survivors — each one is a change that keeps all 451 tests green

| Group | File | Mutation | Why it matters |
|---|---|---|---|
| statistics and decisions | src/stage3/experiment.py | economic conclusion uses two-sided p | 'momentum detected' / 'winners beat the universe' flags |
| costs (step E) | src/stage3/step_e.py | rate date = exit not entry | wrong rate in months where a rate changes during the holding period |
| research logic (ladder, protocol constants) | src/stage3/ladder.py | missing-price stop disabled | protocol B1.2 'the run stops' is not exercised |
| stage 2 data | src/stage2/universe.py | liquidity window 63->64 | universe definition; real data protected by the UNIV-1 hash only |
| guards and registry | scripts/run_s2_mom.py | confirmation without same-code primary | protocol section 25 stop rule is untested |
| stage 2 data | src/stage2/universe.py | min valid 50->49 | same |
| stage 2 data | src/stage2/returns.py | jump threshold 1.4->1.5 | research-grade classification; real data protected by the RET-1.1 hashes only |
| research logic (ladder, protocol constants) | src/stage3/ladder.py | holding drops exit session (RG) | one day of return missing from every step D month |
| statistics and decisions | src/stage3/stats.py | bootstrap one-sided | the robustness p-value would be roughly halved |
| costs (step E) | src/stage3/step_e.py | STT sell uses buy rate key swapped | equivalent only because both rates are 0.1 % in the schedule |
| guards and registry | src/stage3/data.py | stage3 input hash check off | the loader's integrity check is never executed by a test |
| guards and registry | scripts/run_s2_mom.py | blinded artifact gate off | a changed blinded file would not stop the primary run in any test |
| stage 2 data | src/stage2/universe.py | identity links from the future | future-identity leakage; real data protected by the UNIV-1 hash only |
| stage 2 data | src/stage2/returns.py | event attached to row before ex-date | same |
| research logic (ladder, protocol constants) | src/stage3/ladder.py | WML = W + L | the sign of the loser leg in every WML and in the primary estimand |
| research logic (ladder, protocol constants) | src/stage3/ladder.py | RG uses non-research-grade rows | step D would ignore validated corporate-action adjustments and count span days in formation |
| guards and registry | src/stage3/data.py | RET-1.1 hash check off | same |
| statistics and decisions | src/registry/experiments.py | registry unknown status allowed | first registration with an invalid status |
| stage 2 data | src/stage2/universe.py | liquidity mean instead of median | same |
| stage 2 data | src/stage2/returns.py | ex-date boundary prev_date <= ex | same |
| stage 2 data | src/stage2/corporate_actions.py | validation band 1.25->2.0 | corporate-action validation; real data protected by hashes only |
| statistics and decisions | src/stage3/experiment.py | H1 decision threshold flipped | the section 27 label of the primary result |
| guards and registry | src/stage3/data.py | UNIV-1 hash check off | same |
| guards and registry | scripts/run_s2_mom.py | runner overwrite guard off | 'each mode runs once' is untested for the main runner |

Three survivors (`WML = W + L`, `holding drops exit session (RG)`, `RG uses non-research-grade rows`) were re-applied by hand to a fresh copy: 451 passed each time.

What still protects the registered numbers against these changes today: the independent recomputation in this audit (all 680 step-months, both step E samples), the registered result hashes, and — for Stage 2 — the pinned UNIV-1 and RET-1.1 hashes checked by `scripts/build_stage2.py` (a 7-minute manual run, not part of the test suite).

## Killed only by a constant-equality test

| Mutation | Test |
|---|---|
| alpha .05->.10 | tests/test_stage3_infra.py::test_protocol_file_matches_the_frozen_hash_and_constants |
| top_n 200->201 | tests/test_stage3_infra.py::test_protocol_file_matches_the_frozen_hash_and_constants |
| delist OTHER -30%->-3% | tests/test_stage3_infra.py::test_protocol_file_matches_the_frozen_hash_and_constants |

These are caught because one test compares the constants with the protocol values. That is a valid golden test, but no behavioural test would notice.

## Killed

| Group | Mutation | Behavioural tests that failed |
|---|---|---|
| costs (step E) | dp charge on buys not sells | 7 |
| costs (step E) | break-even inverted | 2 |
| costs (step E) | step E schedule hash check off | 1 |
| costs (step E) | brokerage cap ignored (max) | 4 |
| costs (step E) | schedule period boundary exclusive | 15 |
| costs (step E) | hypothetical net WML ignores L cost | 1 |
| costs (step E) | net = gross + cost | 2 |
| costs (step E) | turnover not halved | 1 |
| costs (step E) | cost evidence gap -> usable | 3 |
| costs (step E) | slippage bps as percent | 7 |
| costs (step E) | band boundary rank<200 | 3 |
| costs (step E) | indirect tax also on STT | 4 |
| costs (step E) | stamp duty on sells too | 2 |
| costs (step E) | H4 p tail reversed | 8 |
| costs (step E) | drift ignored (full rebuy each month) | 19 |
| guards and registry | voluntary class mislabelled | 1 |
| guards and registry | runner provenance gate off | 1 |
| guards and registry | survivor pool = everyone | 1 |
| guards and registry | runner pre-run-check gate off | 1 |
| guards and registry | cutoff guard off | 1 |
| guards and registry | protocol hash check off | 1 |
| guards and registry | registry protocol hash check off | 1 |
| guards and registry | pending decisions ignored | 1 |
| guards and registry | step E input hash check off | 1 |
| guards and registry | step E overwrite guard off | 2 |
| guards and registry | research_frame includes holdout day | 3 |
| research logic (ladder, protocol constants) | breakpoint 0.30->0.31 | 1 |
| research logic (ladder, protocol constants) | formation reaches entry session (look-ahead) | 3 |
| research logic (ladder, protocol constants) | delisting rule also in steps A/B | 1 |
| research logic (ladder, protocol constants) | delta not in percent | 3 |
| research logic (ladder, protocol constants) | portfolio return = median | 8 |
| research logic (ladder, protocol constants) | skip month removed | 6 |
| research logic (ladder, protocol constants) | slippage S1 5->6 | 4 |
| research logic (ladder, protocol constants) | formation reaches selection date t (no skip) | 2 |
| research logic (ladder, protocol constants) | delisting rule off everywhere | 5 |
| research logic (ladder, protocol constants) | step A pool filter removed | 4 |
| research logic (ladder, protocol constants) | formation 12->11 | 2 |
| research logic (ladder, protocol constants) | entry same session (s > t -> >=) | 4 |
| research logic (ladder, protocol constants) | holding includes entry-session return (naive) | 31 |
| research logic (ladder, protocol constants) | RG formation ignores flagged rows | 2 |
| research logic (ladder, protocol constants) | top200 takes n+1 | 2 |
| research logic (ladder, protocol constants) | step D spec uses pool universe | 3 |
| research logic (ladder, protocol constants) | exit one session early (s > nxt -> >=) | 3 |
| research logic (ladder, protocol constants) | gap return counted twice (no consumed) | 1 |
| research logic (ladder, protocol constants) | naive factor inverted | 1 |
| research logic (ladder, protocol constants) | step A uses PIT date | 1 |
| research logic (ladder, protocol constants) | rank ascending (losers as winners) | 10 |
| research logic (ladder, protocol constants) | neutral fill -> zero | 2 |
| research logic (ladder, protocol constants) | NW lag primary 4->5 | 10 |
| research logic (ladder, protocol constants) | tie-break reversed | 1 |
| research logic (ladder, protocol constants) | delisting return sign | 1 |
| research logic (ladder, protocol constants) | delta sign flipped (D - A) | 3 |
| research logic (ladder, protocol constants) | rankable needs only m1 price | 1 |
| stage 2 data | liquidity window shifted 1 session into the future | 1 |
| stage 2 data | fund units admitted | 1 |
| stage 2 data | unvalidated factor applied | 2 |
| stage 2 data | universe cutoff guard off | 1 |
| stage 2 data | returns cutoff guard off | 1 |
| stage 2 data | large residual 10%->50% | 1 |
| stage 2 data | bonus factor inverted | 3 |
| stage 2 data | liquidity rank ascending | 4 |
| stage 2 data | gap rows research-grade | 1 |
| stage 2 data | post-cutoff corporate actions kept | 1 |
| statistics and decisions | p one-tailed reported as two-sided | 3 |
| statistics and decisions | PW block length forced 1 | 2 |
| statistics and decisions | ci90 uses 97.5% quantile | 1 |
| statistics and decisions | reliability fill W or L -> and | 4 |
| statistics and decisions | C2 input hash check off | 1 |
| statistics and decisions | bootstrap resampler not circular/blocks iid | 1 |
| statistics and decisions | bootstrap not null-centred | 1 |
| statistics and decisions | holm multiplier constant | 1 |
| statistics and decisions | BH divisor dropped | 1 |
| statistics and decisions | registry duplicate id allowed | 1 |
| statistics and decisions | NW Bartlett weight -> 1 | 15 |
| statistics and decisions | SE without sqrt(n) | 2 |
| statistics and decisions | C2 confirmation rule sign ignored | 1 |
| statistics and decisions | NW variance / (n-1) | 3 |

## Limits

1. 104 hand-chosen mutations, not an exhaustive mutation tool run (`mutmut` is not installed and was not added to the environment).
2. Mutations in `src/intraday/*` (ORB) other than the two bootstrap ones were not attempted; those files are pinned by `test_frozen_orb_methodology_unchanged`, which would kill any change by hash.
3. A survivor shows a missing test, not a defect in the code.

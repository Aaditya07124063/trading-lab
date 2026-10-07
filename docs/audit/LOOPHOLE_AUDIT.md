# Trading Lab — loophole, bypass and dead-code audit (2026-10-07)

Question: is there an easy alternate path that silently goes around the protections of the main runner?

Safe path, as designed:

```
run_s2_mom.py <mode>
  → verify_protocol()          protocol file hash + registry hash
  → require_ready()            every reviewed decision recorded
  → verify_provenance()        Stage 2 inputs and Stage 3 code == Stage 3 manifest
  → stage2_rebuild == 150      registry field
  → pre-run checks passed with this code
  → blinded artifact registered and intact
  → (confirmation / sensitivity) registered primary run with this exact code
  → load_inputs()              every Stage 3 file == manifest; cutoff
  → analyse → write once → trial log → registry amendment
```

All attacks below were run on a scratch copy of the repository, never on the project itself.

## Loopholes found

| ID | Path that goes around a safeguard | Demonstrated? | What stops it today | Severity |
|---|---|---|---|---|
| L-01 | **Direct import.** `from src.stage3 import data, experiment` then `experiment.analyse(data.load_inputs("OOS"), schedule)` or `experiment.run(...)`. `load_inputs` calls only `verify_protocol()`. No decision gate, no "primary first" order, no run-once, no trial log, nothing written | by inspection (the functions take no token and check no state) | nothing; the docstring says "called only by the runner" | P2 |
| L-02 | **Edit Stage 3 inputs and their manifest together.** `load_inputs` trusts `manifest.json`, and nothing trusts-checks the manifest | **yes** — a changed `primary/calendar.csv` was refused; after updating the hash inside `manifest.json` it was accepted | `verify_provenance` covers Stage 2 inputs and three code files, not the Stage 3 outputs | P1 (F-02) |
| L-03 | **Registry amendment.** `experiments.amend("S2-MOM-v1", "x", status="PLANNED")`, or `protocol_sha256=…`, or `provenance={…}` (replaces the whole block), or an empty reason | **yes** — all four accepted | only an unknown id or unknown status is refused | P1 (F-03) |
| L-04 | **Fake a gate by hand.** Write `checks/pre_run_checks_primary.json` with `{"all_passed": true, "code_sha256": <current>}`; add a registry amendment with `stage2_rebuild.checks_passed = 150` | by inspection; the amendment was accepted on the scratch copy | nothing ties either to an actual run | P2 (F-12) |
| L-05 | **Change code outside the hashed list.** Main `code_sha` = 7 files. Not covered: `src/intraday/inference.py` (bootstrap resampler and block length), `src/stage2/returns.py` (`JUMP`), `src/access.py`, `src/config.py`, `src/registry/experiments.py`. Step E `code_sha` = `step_e.py` + its runner; **not** `stats.py` (the Newey-West test) or `protocol.py` (α, lags, slippage table), both imported. C2 `code_sha` = the script only; it imports `stats.mean_test` | by inspection | `inference.py` is separately pinned by the ORB frozen-hash test; `stats.py` and `protocol.py` are in the main hash, which still matches today | P2 (F-09) |
| L-06 | **Delete and rerun.** "Runs once" is enforced by the existence of the output file or directory. Removing `results/s2_mom_v1/primary_results.json` re-opens the mode; the earlier look leaves a trace only if it reached the trial log | by inspection | registry would then hold two `primary_run` amendments (visible in history) | P2 (F-08) |
| L-07 | **Crash window.** In `primary` / `confirmation`: results JSON is written, then five CSVs, then the trial log, then the registry. A crash in between leaves a complete, readable result that is neither registered nor logged | by inspection of the order of statements | rerun is refused until someone deletes the file | P2 (F-08) |
| L-08 | **Environment switch.** `TRADING_LAB_NO_TRIAL_LOG=1` in the shell: `log_trial` returns `None`, the runner continues and registers | **yes** | nothing | P2 (F-11) |
| L-09 | **Optimised interpreter.** `python3 -O scripts/build_stage3.py`: the seven structural `assert` checks in `data.build()` do not run; same for the cutoff consistency `assert`s in `protocol.py` and `access.py`, and four in `evaluate_orb_v1.py` | **yes** (`__debug__` is False under `-O`; the checks are `assert` statements) | nothing | P2 (F-10) |
| L-10 | **Web endpoint overwrites a data file.** `GET /api/add?symbol=RELIANCE.NS` replaces `data/india/RELIANCEd1.csv` with today's Yahoo history | by inspection | cutoff filter only; S2-MOM does not read these files; legacy experiments do | P2 (F-14) |
| L-11 | **Duplicate registry line.** A second line with the same `experiment_id` makes `current()` discard all earlier amendments of that record | **yes** — status fell back to `PLANNED` | no code path writes such a line; a hand edit or a merge could | P1 (F-03) |

## Paths checked and found closed

1. Cutoff: `data._cut`, `load_ret`, `universe.build`, `returns.build`, `panel.parse`, `archive.fetch`, `identity.segments`, `corporate_actions.load_events` each refuse or drop anything after 2026-09-30 (tests + mutation).
2. Protocol edit: one byte changes the hash; every runner and loader refuses (test + mutation).
3. Cost schedule, addendum or supplement edit: `step_e.load_schedule` refuses (tests).
4. Step E / C2 input edit: each input is hashed before any read (tests + mutation).
5. Step E / C2 partial output: results are written into `<dir>.partial` and renamed only when complete; a leftover `.partial` blocks a rerun (tests).
6. ORB holdout: needs a git-committed, unmodified authorization artifact carrying the protocol hash; single-use guard; static scan that only `evaluate_orb_v1.py` asks for holdout rows (23 tests).
7. Unknown CLI words and extra arguments: exit non-zero, nothing written (audit attack script).
8. Research-tier code reading market CSVs directly: blocked by the AST scan in `tests/test_access_boundary.py`, with an explicit allow-list.

## Dead or stale code that touches a safeguard

| Item | Where | Risk |
|---|---|---|
| `src/stage3/costs.py`, `ladder.net_of_costs`, `experiment.step_e` — the first cost model; superseded by `src/stage3/step_e.py`; still imported by the runner only to print "pending" | `src/stage3` | a second, different cost implementation (flat schedule, GST on brokerage+exchange+SEBI, one band) stays callable; its schedule file `delivery_nse_eq_s2mom.json` is the incomplete template. Could be used by mistake (A-02) |
| `identical` variable in `data.build()` is set and returned but can never be False when the function returns | `src/stage3/data.py:141-185` | harmless |
| `require_ready(need_costs=True)` branch | `protocol.py:93-97` | never used by a runner |
| Legacy runners `run_ml.py`, `run_momentum.py`, `run_experiments.py`, `fetch_data.py`, `paper_bot.py` | root | unprotected by design; registry statuses already mark their results as exploratory / requiring rebuild |
| `Untitled.ipynb`, `.ipynb_checkpoints/`, `.virtual_documents/`, empty `strategies/` | root | clutter; a notebook is the natural place for L-01 |

# Trading Lab — trust model and threat model (after remediation, 2026-10-07)

The forensic version is kept unchanged in `docs/audit/forensic_20261007/THREAT_MODEL.md`. Its sections on command-line safety and on secrets (no credential found) still hold and are not repeated here.

## 1. Who the adversary is

The realistic adversary is **accident**: a tired researcher, a helper script, an AI assistant, a second terminal, a crashed run, a package upgrade, a lost laptop.

What local code can do: make an accident **loud**. A changed file, a rewritten manifest, a downgraded registry state or a missing input must stop the next verification with a message that names the broken link.

What local code cannot do: stop the owner of the repository from deliberately rewriting everything, including the verifier. Against that, the controls are outside this machine: the Git history once pushed, the archive copy once stored elsewhere, and the hashes printed in the manuscript. This is stated so that nobody reads "tamper-proof" into this document. The system is tamper-**evident** against accident and against any edit that does not also rewrite the pinned constants in code.

## 2. Roots of trust

| Root | What pins it | What it pins |
|---|---|---|
| `GENESIS_SHA256` in `src/registry/experiments.py` | Git | the first 58 registry lines |
| the registry file | genesis hash + per-line hash chain; Git | protocol, addenda, UNIV-1, Stage 2 rebuild, every result file, every code hash, all anchors |
| `anchors` of `S2-MOM-v1` | registry rules: may only gain keys | Stage 3 manifest, check files, rebuild log, cost schedules, archive manifest, environment files |
| independent pins in `scripts/reproduce_s2_mom_v1.py` | Git | protocol, UNIV-1, cost schedule, C2 specification, the six result hashes |
| hashes printed in the manuscript (Table A5) | the distributed document | 26 files |

An edit has to change several of these at once to pass unnoticed. A single-file edit cannot.

## 3. Threats and their state

| ID | Threat | Control now | Proof | Residual risk |
|---|---|---|---|---|
| T1 | The only copy of the code and results is lost (`git clean`, disk failure) | Everything research-critical is staged for one commit; large data has a hash-anchored archive manifest and a deterministic tar; guard test fails on any untracked or merely ignored research file | `tests/test_version_control.py`, `tests/test_release_archive.py` | **High until the researcher commits, pushes and stores the archive off this laptop.** The mechanism exists; the second copy does not yet. |
| T2 | Stage 3 inputs are edited or rebuilt and the manifest is rewritten to match | The manifest hash is anchored in the registry; the verifier checks registry → manifest → files | `tests/test_provenance_chain.py` (24); failure injection "rewrite the manifest" | Low |
| T3 | A registry line flips the state, replaces a hash, or duplicates a record | State machine, protected fields, hash chain, pinned history, validated on every read and write | `tests/test_registry_state_machine.py` (235) | Low. A line removed from the **end** of the file is caught only where something depends on it (anchors, status); the Git history is the full control. |
| T4 | A result is computed outside the runner (notebook, REPL) | None in frozen code. A result so computed cannot be registered on a FINAL experiment; an extra trial-log line fails the reproduction | registry tests; failure injection "unregistered rerun" | **Medium, accepted.** A private look that logs nothing cannot be prevented by code. Runbook rule. |
| T5 | A crashed run leaves a readable, unregistered result | Frozen runner unchanged. The reproduction rejects any unregistered file in a results folder and any registered file with other bytes | failure injection "add an unexpected file (results)", "truncate an output" | Low for the registered study (all modes have run). Design item for S2-MOM-v2. |
| T6 | A dependency upgrade changes numbers | Official environment = Conda osx-arm64 with exact builds, anchored; the reproduction states whether it runs in the tested environment, refuses a library that does not load, and compares at 1e-9 | `tests/test_environment.py`; clean Conda rebuild reproduced (PASS) | Medium for other platforms: one machine only. pip is not supported. The daily work still runs in the shared base environment. |
| T7 | Future data reaches a decision | Unchanged controls: cutoff in every loader, perturbation and truncation tests, real-data pre-run checks (now hash-anchored) | existing tests; golden boundary traps in `tests/test_s2mom_mutation_kills.py` | Low |
| T8 | Corrupt values behind valid hashes (NaN, inf, duplicate rows, wrong counts) | `validate_stage3`, `validate_monthly`, `validate_step_e` — explicit raises, not `assert` | 43 value attacks in `tests/test_failure_injection.py`, plus 16 on registered monthly and step E frames | Low |
| T9 | `python -O` removes the frozen `assert` guards | The reproduction refuses to run optimised; the same checks exist as explicit raises | `tests/test_environment.py::test_python_O_really_disables_the_frozen_asserts_and_the_explicit_checks_still_fire` | Low for verification. The frozen builder itself is still unguarded under `-O` (runbook rule; report-only). |
| T10 | Trial logging is switched off by an environment variable | Suppression works only inside pytest; anywhere else the variable raises | `tests/test_registry_state_machine.py::test_trial_log_cannot_be_silenced_outside_the_test_suite` | Low |
| T11 | A gate is faked by hand (check file, "150 of 150") | Check files and the rebuild log are anchored; the registry field is immutable in FINAL; the reproduction recounts the log | failure injection; `check_outputs` | Low |
| T12 | A module outside the hashed file list changes (bootstrap resampler, `stats.py` for step E / C2) | Not covered by the registered code hashes (frozen design). Behavioural tests and the independent recomputation would show a changed number | mutation campaign (resampler mutations killed) | **Medium, accepted (F-09).** |
| T13 | The web UI overwrites a legacy daily data file (`/api/add`) | None added (not on the S2-MOM path; the UI was out of scope) | — | **Medium for legacy datasets, none for S2-MOM. Open (F-14).** |
| T14 | The intraday collector dirties the tree and loses rejected bars | Not changed. The snapshot verifier and the reproduction now separate collector files from research files, so a collector run cannot be mistaken for a research change | `scripts/audit_snapshot.py` (EXTERNAL list) | **Open (F-15):** the 2026-10-07 18:30 run again exited 1. Needs the researcher's review before Yahoo's 60-day window closes. |
| T15 | The verifier itself is wrong or is weakened | 45 mutations of the release tooling; a second implementation must agree with the frozen one on synthetic data and with hand arithmetic on a golden fixture | `MUTATION_FINAL_REPORT.md` group "release tooling" | Low |

## 4. Rules that only a person can keep (runbook)

1. Commit, push, and copy the archive tar to a second location. Until then T1 is open.
2. Never run a runner or builder with `python -O` or `PYTHONOPTIMIZE`.
3. Never compute a sample outside the runners or the reproduction script.
4. Never delete a file under `results/`.
5. Never edit `registry/experiments.jsonl` by hand. Use `experiments.amend` / `experiments.anchor`; they refuse what is not allowed.
6. After any change to code or tests: `pytest`, then `python3 scripts/reproduce_s2_mom_v1.py`, then `python3 scripts/audit_snapshot.py verify docs/audit/remediation/pre_remediation_snapshot.json`.
7. A new study needs a new protocol version and a new experiment id (PLANNED → READY → EXECUTING → REGISTERED → FINAL). S2-MOM-v1 can only become SUPERSEDED, INVALID or REQUIRES REVALIDATION.

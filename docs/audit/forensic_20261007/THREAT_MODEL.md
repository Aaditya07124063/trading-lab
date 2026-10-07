# Trading Lab — trust model and threat model (audit 2026-10-07)

The realistic adversary here is not an outside attacker. It is **accident**: a tired researcher, a helper script, an AI assistant, a second terminal, a crashed run, a package upgrade. Deliberate tampering by the repository owner cannot be prevented by local code and is out of scope; the goal is that an accident cannot pass silently.

## Trust-boundary diagram

```
 UNTRUSTED                                   VALIDATION AT THE BOUNDARY                          TRUSTED
 ─────────                                   ──────────────────────────                          ───────
 NSE HTTP responses ───────────────▶ cutoff check, 404/5xx handling, SHA-256 recorded ─────▶ raw archive + manifest
        (content NOT validated as zip/JSON: F-16)

 raw archive files ────────────────▶ SHA-256 == manifest (build_stage2 step 1), row-date ──▶ PANEL / CA-2 / ID-1
                                      check, QA counts, overlap comparison

 Stage 2 datasets (git-ignored) ───▶ per-file SHA-256 == ret1_1_manifest; UNIV-1 == pinned ▶ RET-1.1, UNIV-1
                                      hash

 Stage 3 files (untracked) ────────▶ SHA-256 == data/stage3/.../manifest.json ─────────────▶ ladder inputs
        (the manifest itself has NO anchor: F-02)        (matrix builder does not validate values: F-07)

 protocol / addenda / schedule ────▶ SHA-256 pinned in code AND in registry ───────────────▶ frozen protocol

 result files ─────────────────────▶ SHA-256 == registry files_sha256 (sensitivity, step E, ▶ registered artifact
                                      C2, tests, API view, manuscript builder)

 registry/experiments.jsonl ───────▶ JSON parse; REQUIRED fields on first record only ─────▶ "current" record
        (no state machine, no protected fields, no chain: F-03)

 user CLI arguments ───────────────▶ fixed mode word / literal "execute"; no paths, no dates ▶ runner
 environment variables ────────────▶ one variable, disables trial logging (F-11);
                                      PYTHONOPTIMIZE strips assert guards (F-10)
 pre-run check JSON, rebuild flag ─▶ field equality only (F-12) ───────────────────────────▶ run gates
 Yahoo responses (collector) ──────▶ grid/overlap validation, raw snapshot, rejection log ──▶ data/india/*m15.csv
 Yahoo responses (/api/add) ───────▶ cutoff filter only; overwrites the target file (F-14) ─▶ data/india/*d1.csv
```

Every UNTRUSTED → TRUSTED transition has some validation. Four are weaker than the rest: F-02, F-03, F-07, F-12.

## Threats, ranked by how an accident could happen

| ID | Threat | Present control | Residual risk | Finding |
|---|---|---|---|---|
| T1 | The only copy of the experiment code and registered results is lost or silently altered (`git clean`, `git stash -u`, disk failure, an editor refactor) | registry hashes detect alteration of results; nothing detects loss | **High** — nothing is committed | F-01 |
| T2 | Stage 3 inputs are regenerated or edited and the manifest is rewritten with them | build-or-verify refuses to overwrite a differing file | medium — delete the folder, rebuild from changed Stage 2 state, and the runner accepts | F-02 |
| T3 | A registry line is added that flips status, replaces provenance hashes, or resets a record | append-only convention; tests pin today's registered values | medium | F-03 |
| T4 | A result is computed and looked at outside the runner (notebook, REPL) | docstring "called only by the runner" | medium — no gate, no trial log | L-01 |
| T5 | A crashed primary/confirmation run leaves a readable result that is not registered and not in the trial log; the researcher deletes it and reruns | rerun is refused while the file exists | medium | F-08 |
| T6 | A dependency upgrade changes a number in the last digits | byte-identity checks fail closed | low for integrity, medium for reproducibility | F-06, F-29 |
| T7 | Future data reaches a decision | cutoff refused in every loader; perturbation/truncation tests; pre-run checks on real data | low | see `RESEARCH_INTEGRITY_AUDIT.md` |
| T8 | ORB holdout rows are read early | `holdout_authorized` (git-committed artifact + protocol hash) and static scan | low | — |
| T9 | Web UI overwrites a research data file | none on `/api/add` | medium for legacy datasets, none for S2-MOM (does not read `data/india`) | F-14 |
| T10 | Two processes run the same mode | step E / C2: exclusive `.partial` directory. Main runner: check-then-write | low-medium | F-08 |
| T11 | Running the lab modifies another project | every path derives from `BASE_DIR`; no path argument on any research runner; no `shell=True`; subprocess calls are fixed `git` argument lists | low | — |

## Phase 11 results — CLI and configuration security

1. `shell=True`, `os.system`, `eval`, `exec`, `pickle`: **none** in the code base (grep, VERIFIED BY INSPECTION).
2. `subprocess` is used only with fixed argument lists for `git` (`access.py`, `experiments.py`, `universe.py`, `evaluate_orb_v1.py`) and for Chrome in the manuscript export.
3. No research runner takes a path, a date, a seed or a parameter from the command line. Unknown modes and extra arguments exit 1 without writing (PROVEN by the audit attack script on a scratch copy).
4. Writes outside the project root: not reachable from any runner. The one exception by construction is `server.py /api/add`: the symbol is cleaned of `.NS`, `.BO`, `^`, `&` only, so `/` and `..` are not rejected before the string is used in a file name. It is reachable only if Yahoo returns data for such a symbol, which is unlikely; the missing validation is still a defect (F-14).
5. `server.py` has no authentication and state-changing GET endpoints. Acceptable only when bound to localhost (the README command binds to 127.0.0.1 by default). DOCUMENTATION ONLY.
6. The launchd collector uses absolute paths to this project only, no sudo, no deletion (VERIFIED BY INSPECTION of `scripts/collect_intraday.sh` and the plist).
7. "Running Trading Lab cannot accidentally modify unrelated projects": **VERIFIED BY INSPECTION** for every entry point in `SYSTEM_ARCHITECTURE.md` table B, with the `/api/add` caveat above. Not proven by test.

## Phase 12 results — secrets and privacy

Search over `*.py, *.json, *.md, *.sh, *.plist, *.html, *.js, *.txt, *.env, *.cfg, *.toml, *.yml` for API keys, passwords, tokens, bearer strings, private keys, service-account and Firebase files, broker credentials.

| File | Line | Type | Severity |
|---|---|---|---|
| — | — | no credential, key, token or secret found in any code, configuration, log or generated artifact | — |

Keyword hits were only: archived third-party HTML pages under `docs/evidence/s2mom_costs/` (page markup), prose in two design documents, the comment "No sudo, no secrets" in `scripts/collect_intraday.sh`, and the sentence "not a secret" in `src/access.py`. No `.env`, `.pem`, `.key` or credential file exists. The registry and logs contain no personal data beyond the local user name inside absolute paths in the plist and collector script. Label: VERIFIED BY INSPECTION.

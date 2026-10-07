# Provenance verification report — findings F-02, F-12, F-01 (2026-10-07)

Code: `src/registry/integrity.py::verify_stage3`, `scripts/release_archive.py`, checks inside `scripts/reproduce_s2_mom_v1.py`.
Tests: `tests/test_provenance_chain.py` (24), `tests/test_release_archive.py` (11), `tests/test_version_control.py` (3).
Raw result list: `docs/audit/remediation/provenance_attacks_pytest.txt`.

## 1. The chain

```
registry record S2-MOM-v1  (root of trust)
  └─ anchors.stage3_manifest_sha256 = 6f08fd0fb389d36027e02bb06b9e8ff06ee1d7cb45c30c15c6c41dd79c711fe5
       └─ data/stage3/s2_mom_v1/manifest.json           (file SHA-256 must equal the anchor, before it is parsed)
            ├─ outputs_sha256  → the 8 Stage 3 input files     (exactly these 8 names; nothing else in the folder)
            ├─ inputs_sha256   → UNIV-1, ID-1 segments, ID-1 entities, RET-1.1 manifest, 16 RET-1.1 files
            ├─ code_sha256     → src/stage3/ladder.py, data.py, protocol.py
            └─ protocol_sha256 = registry protocol_sha256
  └─ anchors.stage3_check_files_sha256 → two pre-run check files, the Stage 2 rebuild log
```

The manifest is not trusted because it agrees with the files beside it. It is first compared with the hash held by the registry. Only then is it parsed.

## 2. Required failures — all demonstrated

| # | Required by the brief | Result | Message | Test |
|---|---|---|---|---|
| 1 | A rewritten manifest with modified inputs must fail | fails | "does not match the SHA-256 anchored in the registry" | `test_rewritten_manifest_with_modified_input_fails` |
| 2 | A modified input with an unchanged manifest must fail | fails | "… does not match its recorded SHA-256" | `test_modified_input_with_unchanged_manifest_fails` |
| 3 | A modified manifest with an unchanged registry hash must fail | fails | "anchored in the registry" | `test_modified_manifest_with_unchanged_registry_hash_fails` (3 variants) |
| 4 | A missing manifest must fail | fails | "manifest is missing" (also when it is a symlink) | `test_missing_manifest_and_missing_anchor_fail` |
| 5 | A duplicate manifest entry must fail | fails | "duplicate manifest entry" — **even when the registry anchor is re-pointed at that manifest** | `test_duplicate_manifest_entry_fails_even_when_the_registry_names_that_manifest` |
| 6 | A path traversal or unexpected file path must fail | fails | "not exactly the eight Stage 3 inputs" (`../`, absolute path, `a/../../b`, extra name, backslash, empty name) | `test_path_traversal_or_unexpected_path_fails` (6 variants) |

Further cases, all failing as they should: no anchor in the registry; a missing manifest entry; a deleted input; an extra file in the input folder; an input replaced by a symlink to identical bytes; a changed Stage 2 input; a changed RET-1.1 file; an extra RET-1.1 file; a changed code file; a changed check file; a registry record that names another protocol or another UNIV-1.

Tests 5 and 6 deliberately give the attacker control of the registry anchor too. They show that the later links hold on their own.

Provenance attacks in the test suite: 24 run, 24 pass. In the failure-injection suite (scratch copy of the real artifacts): 19 file attacks on inputs, manifest and code — 19 rejected.

## 3. The real chain

`tests/test_provenance_chain.py::test_the_real_chain_is_anchored_in_the_registry_and_verifies` and step 4 of the reproduction verify the real chain on every run: registry anchor → manifest → 8 Stage 3 inputs → 4 Stage 2 inputs → 16 RET-1.1 files → 3 code files → 3 check files. Result on 2026-10-07: PASS.

The anchored values equal the hashes in the pre-remediation snapshot, so the anchor describes the files as they were when the experiment was registered, not files touched during remediation.

## 4. Gate evidence (F-12)

1. The two pre-run check files are anchored. The reproduction also requires `all_passed` and the registered code hash inside them.
2. "Stage 2 rebuild passed 150 of 150" was a hand-entered registry field. The log it summarises is now anchored, and the reproduction recounts it: 150 lines `OK`, last line `RESULT: ALL CHECKS PASSED`, no `FAIL`.
3. Residual: the log is a text file written by the builder on 2026-10-05. Its hash proves it has not changed since it was anchored on 2026-10-07; it cannot prove what happened on 2026-10-05. A full proof would be a Stage 2 rebuild, which this remediation was told not to run.

## 5. Version control and the external archive (F-01)

1. **Git.** More than 220 files that were untracked or modified are staged for one commit: `src/stage3/`, the three runners, `build_stage3.py`, seven test files, the cost schedules, Addendum 1 and Supplements 1–4, the deviation log, `data/stage3/` (except the panel), all of `results/s2_mom_v1*/`, the manuscript, the registry, plus everything remediation added. **The commit itself is deferred by instruction.**
2. **Guard.** `tests/test_version_control.py` fails if any file under a research path is untracked, or is ignored without being listed in the archive manifest. It ran red twice during remediation (new files not yet staged) — the guard works.
3. **External archive.** `release/s2_mom_v1/ARCHIVE_MANIFEST.json`:

   | | |
   |---|---|
   | Archive identifier | `s2-mom-v1-data-baa0b47040101031` |
   | Files | 5,637 (5,560 raw NSE files, 76 Stage 2 dataset files, the Stage 3 panel) |
   | Archive SHA-256 (deterministic tar) | `bb4b9659da4d991bb99c32a5fa5ee4765ab0bde9bf5d498a70e1c4fded681ac2` |
   | Archive size | 1,552,240,640 bytes |
   | Manifest SHA-256 | `394df99cd6f0fde7ebb8198e996e355498e6977f19bc5125ef89c4144af7790e` (anchored in the registry) |
   | File-level hashes | one SHA-256 and byte count per file, in the manifest |
   | Provenance | stated per folder in the manifest; raw files cross-checked against `data/stage2/raw_manifest.jsonl` (5,560 of 5,560 equal), RET-1.1 files against `ret1_1_manifest.json`, the panel against the Stage 3 manifest |
   | Retrieval | `python3 scripts/release_archive.py materialize <tar>` — verifies the tar, then each file; never overwrites |

4. **Not done, and why.** The tar was not written and no copy was sent anywhere. The machine had 3 GB free and the brief forbids pushing. The tar hash was computed by streaming the deterministic archive through SHA-256 without writing it, so `pack` on any machine that has the files must produce exactly that hash (tested on synthetic files: two packs, identical bytes).
5. **Traceable code version for every registered result.** Each run's `code_sha256` is recomputed from the files by the reproduction (three hashes, all match). After the commit, the commit that contains those files is the code version. A tag and a registry anchor naming the commit can only be added after the commit exists.

## 6. Status

| Finding | Status |
|---|---|
| F-02 manifest not anchored | FIXED + REGRESSION PROTECTED |
| F-12 gate evidence unanchored | FIXED + REGRESSION PROTECTED (residual in 4.3) |
| F-01 experiment outside version control | **OPEN until the researcher commits, pushes and stores the archive.** Mechanism, staging and guard are complete. |

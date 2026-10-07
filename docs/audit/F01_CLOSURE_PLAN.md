# F-01 closure plan — "the experiment exists as one copy on one laptop"

**Status: CLOSED on 2026-10-08.** Executed with the researcher's authorisation; results in "Closure record" at the end. Deviations from the plan are listed there.

F-01 is closed when **all four** conditions hold and are verified:

| # | Condition | Evidence that closes it |
|---|---|---|
| 1 | The code, tests, registry, results, manifests and documents are in a Git commit | `git log`; the commit contains the files of `EXACT_COMMIT_CONTENTS.md` |
| 2 | That commit exists in a second place | `git ls-remote origin` shows the same commit id as the local branch and the tag |
| 3 | The external data (5,637 files, 1.55 GB) exists outside this laptop | a tar on an external disk whose SHA-256 equals `bb4b9659da4d991bb99c32a5fa5ee4765ab0bde9bf5d498a70e1c4fded681ac2` (anchored in the registry) |
| 4 | The copies work | a fresh clone from the remote, with the data restored from the external tar, passes the suite and `reproduce_s2_mom_v1.py` |

## Step 0 — decisions and prerequisites (researcher)

1. Confirm that `origin` (`https://github.com/Aaditya07124063/trading-lab.git`) may receive the manuscript, the results and the third-party evidence files (`PRE_RELEASE_CHECKLIST.md` section 5). If not: use a private remote, or a bare repository on the external disk (`git init --bare /Volumes/<disk>/trading-lab.git`, then use that as the second place).
2. Connect an external disk with at least **4 GB** free (1.55 GB tar + about 0.3 GB clone + 1.6 GB restored data for the verification in step 4).
3. Optional: free local disk (about 2 GB of stale scratch copies; see the checklist).

## Step 1 — commits (local, reversible until pushed)

Commit 1 — the experiment and its remediation (the staged set minus two UI files):

```
cd ~/Projects/trading-lab
git restore --staged src/research_view.py tests/test_ui_api.py
git diff --cached --name-only | wc -l          # expect the count in EXACT_COMMIT_CONTENTS.md minus 2
python3 -m pytest -q                            # in the working tree all tests pass (the two files are still on disk)
git commit -m "S2-MOM-v1: registered experiment, results and research-integrity remediation"
```

Commit 2 — the research-terminal UI (the researcher's earlier work, kept separate):

```
git add server.py web/ README.md src/research_view.py tests/test_ui_api.py
git commit -m "UI: research terminal, read-only research view"
python3 -m pytest -q                            # expect 0 failed
```

Not part of F-01 (leave for a separate decision): the collector's files `data/india/*`, `data/raw/collection_log.jsonl`, `data/raw/manifest.jsonl`.

Tag:

```
git tag -a s2-mom-v1-release-1 -m "S2-MOM-v1 registered results + remediation; see docs/audit/FINAL_RELEASE_GATE.md" <commit-1-id>
```

The tag points at commit 1: the state that contains the experiment and its verification and nothing else.

## Step 2 — second copy of the repository

```
git push origin main
git push origin s2-mom-v1-release-1
git ls-remote origin main refs/tags/s2-mom-v1-release-1    # ids must equal `git rev-parse main` and the tag
```

Size check (VERIFIED BY INSPECTION): the largest file is `results/s2_mom_v1_step_e/primary_step_e_ledger.csv` (27.8 MB). Nothing reaches GitHub's 100 MB per-file limit, and Git LFS is not needed. The staged set is about 93 MB on disk.

## Step 3 — the external data archive

```
python3 scripts/release_archive.py verify                       # local files == manifest
python3 scripts/release_archive.py pack /Volumes/<disk>/s2-mom-v1-data-baa0b47040101031.tar
shasum -a 256 /Volumes/<disk>/s2-mom-v1-data-baa0b47040101031.tar
```

`pack` streams the files into `<name>.partial` on the destination, fsyncs, checks the SHA-256 against the manifest, and only then renames. It never overwrites an existing file. The printed hash must be `bb4b9659da4d991bb99c32a5fa5ee4765ab0bde9bf5d498a70e1c4fded681ac2` and the size 1,552,240,640 bytes. Local disk use: none beyond reading.

Recommended, not required: a second copy of the tar in another place (cloud storage or a second disk), with the same hash check.

## Step 4 — verify the copies (this is what closes F-01)

On the external disk, so the laptop's disk is not used:

```
cd /Volumes/<disk>
git clone https://github.com/Aaditya07124063/trading-lab.git trading-lab-verify
cd trading-lab-verify
git checkout s2-mom-v1-release-1
python3 -m pytest -q                                            # data-free: expect 0 failed (about 50 skipped)
python3 scripts/release_archive.py materialize ../s2-mom-v1-data-baa0b47040101031.tar
python3 scripts/release_archive.py verify                       # 5,637 files identical
python3 -m pytest -q                                            # expect 0 failed, 0 skipped
python3 scripts/reproduce_s2_mom_v1.py                          # expect PASS, exit 0
```

Use the Conda environment of the contract (`conda create -n s2mom --file release/s2_mom_v1/conda-osx-arm64.lock`), or the registered interpreter. Expected results, from the scratch rehearsal of this review:

| Check | Expected | Rehearsed? |
|---|---|---|
| suite, data-free | 0 failed | yes: 910 passed, 50 skipped (staged set, scratch) |
| suite, with data | 0 failed, 0 skipped | yes: 960 passed (scratch git repository) |
| reproduction | PASS | yes (staged set, scratch) |
| `materialize` from a real tar | restores 5,637 files | **no** — only on synthetic files (`tests/test_release_archive.py`); the real tar has never been written |

## Step 5 — record and re-gate

1. Append the results of step 4 (commit id, tag, `ls-remote` output, tar hash and size, test and reproduction output) to `docs/audit/F01_CLOSURE_PLAN.md` under a new heading "Closure record", and set F-01 to FIXED in `docs/audit/remediation/build_tables.py`. Regenerate the reports. Commit that as a third commit and push it.
2. Optional: anchor the release commit id in the registry (`experiments.anchor("S2-MOM-v1", reason, _actor=..., release_commit=<id>, release_tag="s2-mom-v1-release-1")`). This appends registry line 62 and needs one more commit. It is not required to close F-01.
3. `FINAL_RELEASE_GATE.md` turns to PASS only after point 1, and only if every check of step 4 passed.

## What cannot go wrong silently

- A push that fails or is rejected leaves the local commits unchanged. Repeat it.
- A tar with other bytes is refused by `pack` before it gets its final name, and by `materialize` before any file is restored.
- A clone without the data cannot pass the reproduction; it fails with "missing input".

## What this plan does not do

It does not rerun any experiment, change any registered file, or change the protocol. Commit 2 contains no research code. The collector data stays uncommitted.

## Closure record (2026-10-08)

| Step | Result | Label |
|---|---|---|
| 0 — remote | `origin` = `https://github.com/Aaditya07124063/trading-lab.git`. Was public on the first check; the researcher made it private; re-checked before the push: unauthenticated API and web page return 404, `git ls-remote` works with the researcher's credentials | VERIFIED BY INSPECTION |
| 0 — external disk | `/Volumes/DON'T OPEN` (the plan's placeholder `/Volumes/<disk>`), FAT32, USB, 141 GB free | VERIFIED BY INSPECTION |
| 1 — commit 1 | `f5bfed89bc7b1bd258dbe81ff9da2be8f44acbdc`, 256 files; index equal to `EXACT_COMMIT_CONTENTS.md` path for path and hash for hash; secret scan: only third-party analytics markup inside three archived public web pages in `docs/evidence/s2mom_costs/` | SUPPORTED BY HASH |
| 1 — commit 2 | `29c15129143ea071816a5aca53376d26f8b997bd`: `server.py`, `README.md`, `src/research_view.py`, `tests/test_ui_api.py`, `web/` (16 files); after it the full suite: 964 passed | PROVEN BY TEST |
| 1 — tag | `s2-mom-v1-release-1`, annotated, object `0db0b0854bf62a44ee36d24bd3b1bcab4402e2cd`, target `f5bfed8` (commit 1) | VERIFIED BY INSPECTION |
| 2 — push | `git push origin main` (fast-forward `6ce8592..29c1512`, 44 commits) and the tag, no force. `ls-remote`: `main` = `29c1512`, tag peels to `f5bfed8` | VERIFIED BY INSPECTION |
| 3 — archive | written by `release_archive.py pack` onto `/Volumes/DON'T OPEN/trading-lab-release/s2-mom-v1-data-baa0b47040101031.tar`; source files verified against the manifest first; 1,552,240,640 bytes; SHA-256 `bb4b9659da4d991bb99c32a5fa5ee4765ab0bde9bf5d498a70e1c4fded681ac2` when written and on an independent `shasum` re-read; 5,637 members = manifest, sizes equal | SUPPORTED BY HASH |
| 4 — fresh clone | cloned from the private remote into a new temporary directory; checked out at the tag; HEAD = `f5bfed8`; clean working tree | VERIFIED BY INSPECTION |
| 4 — restore | `materialize` from the USB tar: 5,637 files restored and verified; `verify`: identical | PROVEN BY TEST |
| 4 — environment | `conda create --file release/s2_mom_v1/conda-osx-arm64.lock` (offline, from the package cache): Python 3.13.5, numpy 2.1.3, pandas 2.2.3, scipy 1.15.3, pyarrow 19.0.0; verifier: identical to the tested environment, nothing missing or unloadable | PROVEN BY TEST |
| 4 — reproduction | in that environment, empty process environment: PASS, exit 0, all 8 steps; 117 quantities / 8,257 numbers within tolerance; largest difference 6.7e-14 (`docs/audit/remediation/f01_closure/fresh_clone_reproduction.json`) | PROVEN BY TEST |
| 4 — manuscript | `verify_manuscript.py` in the clone: 59 PASS, 1 FLAG (N-02, accepted), 3 INFO | VERIFIED BY INSPECTION |
| 4 — tests | clone at the tag: 960 passed, 0 failed, 0 skipped; clone at `main`: 964 passed | PROVEN BY TEST |
| 4 — no rerun | trial log in the clone: 10 lines, 5 S2-MOM runs, identical to the working repository and to the pre-remediation snapshot | SUPPORTED BY HASH |

Deviations from the plan:

1. **No local copy of the tar.** The Mac had 2.9 GB free. The tar was packed directly onto the USB drive. The "original" hash is the one computed from the Mac source files and anchored in the registry; the USB copy matched it twice. The source data on the Mac is untouched.
2. **The clone ran on the Mac, not on the USB drive.** On FAT32, macOS writes `._` sidecar files for every file it creates, which the provenance verifier correctly rejects as unexpected files. (One such sidecar, `._s2-mom-v1-data-baa0b47040101031.tar`, exists next to the archive; it is a separate file and does not change the archive.) The temporary clone and Conda environment were removed after verification to restore free disk; their reports are kept in `docs/audit/remediation/f01_closure/`.
3. **Test packages.** The Conda contract pins the research runtime only. The full suite ran in the fresh clone with the registered interpreter (same research builds plus pytest and the test packages); the reproduction and the verifiers ran in the clean Conda environment.
4. **Step 1 note.** Between commit 1 and commit 2 the working-tree guard `test_no_research_critical_file_is_untracked` reported the two UI files, as expected; the plan's statement that "all tests pass" at that point was wrong. Commit 1 itself was tested as its own checkout (fresh clone at the tag: 960 passed).
5. **Step 5.** The closure is recorded in a third commit (this file, the regenerated gate, the N-06 manuscript sentence). The optional registry anchor of the release commit was not added.

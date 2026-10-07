# F-01 closure plan — "the experiment exists as one copy on one laptop"

**Status: NOT STARTED. Every step below needs the researcher's explicit authorisation.** Nothing here has been run.

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

# Reproducibility

    pip3 install -r requirements.txt
    python3 -m pytest                               # all tests must pass
    python3 -m src.registry.data_registry           # rebuild DATA_REGISTRY.md, check checksums
    python3 -m src.registry.experiments             # rebuild EXPERIMENT_REGISTRY.md

To reproduce a registered result: take its `experiment_id` from
[EXPERIMENT_REGISTRY.md](EXPERIMENT_REGISTRY.md), check out its
`environment.git_commit`, confirm the dataset checksum
(`dataset_sha256`) against `registry/datasets.json`, and run with the recorded
`parameters`. Clean datasets are regenerated from raw + `data/metadata/exclusions.csv`
at that commit; their checksum must equal the recorded one.

Legacy experiments (IDs `LEGACY-*`) predate version control of their inputs;
their registry entries state exactly what could and could not be reproduced.
Environment at registration: python and package versions are stored in each
record (`environment`).

## Stage 2 data foundation

    python3 scripts/build_stage2.py                 # ~7 min, ~10 GB RAM; exit 0 = every hash matches

Rebuilds PANEL-1, CA-2, ID-1, UNIV-1, RET-1, PANEL-1.1 and RET-1.1 from the raw NSE
archive (`data/raw/nse_archive`, checksums in `data/stage2/raw_manifest.jsonl`) and
compares SHA-256 hashes with `data/stage2/PHASE2_MANIFEST.json` and the per-dataset
manifests. The raw archive is outside git; refetch it with the `src.stage2.archive`
commands listed under `rebuild` in that manifest (resumes, never overwrites).

## S2-MOM-v1 (the registered momentum bias-ladder study)

Full description of the chain: [docs/audit/SYSTEM_ARCHITECTURE.md](docs/audit/SYSTEM_ARCHITECTURE.md),
[docs/audit/DATA_FLOW.md](docs/audit/DATA_FLOW.md). Release state: [docs/audit/FINAL_RELEASE_GATE.md](docs/audit/FINAL_RELEASE_GATE.md).

1. **Get the code and the registered results.** Clone the repository. Code, tests, protocol, registry,
   cost schedules, Stage 2 manifests, Stage 3 inputs (except the panel) and all 18 registered result
   files are in Git.
2. **Get the large data.** Three things are outside Git: the raw NSE archive, the Stage 2 datasets and
   the Stage 3 panel (5,637 files, 1.55 GB). They are listed, file by file with SHA-256, in
   `release/s2_mom_v1/ARCHIVE_MANIFEST.json` (archive id `s2-mom-v1-data-baa0b47040101031`,
   tar SHA-256 `bb4b9659da4d991bb99c32a5fa5ee4765ab0bde9bf5d498a70e1c4fded681ac2`).

       python3 scripts/release_archive.py materialize <path>/s2-mom-v1-data-baa0b47040101031.tar

   The command checks the tar hash and every file hash and never overwrites an existing file.
   To create the tar from a machine that has the files: `python3 scripts/release_archive.py pack <dest>.tar`
   (the bytes are deterministic, so the hash is the same on any machine).
3. **Build the environment.** The official environment is **Conda on macOS arm64** (Python 3.13.5,
   numpy 2.1.3, pandas 2.2.3, scipy 1.15.3, pyarrow 19.0.0 — the exact builds of the registered runs):

       conda create -n s2mom --file release/s2_mom_v1/conda-osx-arm64.lock      # every package, URL and MD5
       conda activate s2mom

   (or `conda env create -n s2mom -f release/s2_mom_v1/environment.yml`.)

   - **pip is not supported.** `requirements-lock.txt` lists the same version numbers for reference only.
     On macOS 27 arm64 the PyPI wheel of scipy 1.15.3 cannot be loaded; the reproduction then stops at
     step 1 ("installed but not loadable"). Details: `docs/audit/DEPENDENCY_FINAL_REPORT.md`.
   - Shown to work (2026-10-07): the registered interpreter, and a clean Conda environment created from
     `environment.yml`. Not tested: any other machine, OS or CPU.
   - Results are accepted at an absolute tolerance (1e-9; step E costs 1e-12; counts, labels and
     membership exact), not by byte equality. In another environment the command prints that the
     environment differs and applies the same tolerance.
4. **Reproduce.**

       python3 scripts/reproduce_s2_mom_v1.py            # exit 0 = PASS
       python3 scripts/reproduce_s2_mom_v1.py --verify   # hashes, registry and inputs only

   It verifies the environment, the protocol, the registry, the manifest chain and every input and
   output hash; recomputes the ladder A–D, delta, the Newey–West tests, the step E costs and the C2
   arithmetic with an independent implementation; compares with the registered files; and checks
   that it changed nothing. It registers nothing and never calls a registered runner.
5. **Do not** rerun `scripts/run_s2_mom.py`, `run_s2_mom_step_e.py` or `run_s2_mom_c2.py`. Each mode
   ran once and is registered; the registry now refuses a second registration.

Not recomputed by step 4, only hash- and consistency-checked: the six sensitivity treatments, the
reverse-order ladder and the bootstrap resampling stream.

Other checks:

    python3 -m pytest                                              # whole suite
    python3 scripts/release_archive.py verify                      # external files == archive manifest
    python3 scripts/verify_manuscript.py                           # manuscript claims vs registered artifacts
    python3 scripts/audit_snapshot.py verify docs/audit/remediation/pre_remediation_snapshot.json
    python3 scripts/mutation_campaign.py <scratch dir> <out dir>   # mutation testing on scratch clones

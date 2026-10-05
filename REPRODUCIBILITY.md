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

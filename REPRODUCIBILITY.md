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

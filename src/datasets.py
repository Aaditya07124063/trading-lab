"""RAW -> VALIDATION -> CLEAN -> EXPERIMENT dataset.

Raw files under data/ are never modified. A CLEAN dataset is the raw file
minus the reviewed exclusions in data/metadata/exclusions.csv - computed
deterministically at load time, so it can always be regenerated and its
checksum recorded. Validation flags alone never remove anything."""

import hashlib

import pandas as pd

from src.config import DATA_DIR
from src.data_loader import find_file, load_csv

EXCLUSIONS_FILE = DATA_DIR / "metadata" / "exclusions.csv"


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def frame_sha256(df):
    """Checksum of a loaded table's content (canonical CSV bytes)."""
    return hashlib.sha256(df.to_csv(index=False).encode()).hexdigest()


def exclusions_for(filename):
    if not EXCLUSIONS_FILE.exists():
        return pd.DataFrame()
    ex = pd.read_csv(EXCLUSIONS_FILE, dtype=str)
    return ex[ex["dataset_file"] == filename]


def load_clean(filename):
    """Returns (clean df, provenance dict)."""
    raw_path = find_file(filename)
    df = load_csv(filename)
    ex = exclusions_for(filename)
    drop = pd.Series(False, index=df.index)
    for _, e in ex.iterrows():
        d0 = pd.Timestamp(e["date_start"])
        d1 = pd.Timestamp(e["date_end"]) + pd.Timedelta(days=1)
        drop |= (df["date"] >= d0) & (df["date"] < d1)
    clean = df[~drop].reset_index(drop=True)
    prov = {
        "raw_file": str(raw_path.relative_to(DATA_DIR.parent)),
        "raw_sha256": file_sha256(raw_path),
        "clean_sha256": frame_sha256(clean),
        "exclusion_ids": list(ex["exclusion_id"]) if len(ex) else [],
        "rows_raw": len(df), "rows_excluded": int(drop.sum()), "rows_clean": len(clean),
    }
    return clean, prov

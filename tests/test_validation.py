"""Daily validation flags; clean datasets exclude only REVIEWED rows and
never touch raw files."""

import pandas as pd

from src.datasets import file_sha256, load_clean
from src.data_loader import find_file, load_csv
from src.validation.daily import validate_daily
from tests.conftest import make_daily


def flagged(df, name="X.csv"):
    df["volume"] = 1000
    return validate_daily(df, name)


def test_clean_series_has_no_flags():
    assert flagged(make_daily([100, 101, 102, 103, 104])).empty


def test_spike_and_revert_is_flagged_not_removed():
    df = make_daily([100, 100, 400, 101, 102])
    f = flagged(df)
    assert "V07" in set(f.rule) and len(df) == 5


def test_level_shift_block_flagged():
    closes = [100] * 5 + [200] * 6 + [100] * 5
    f = flagged(make_daily(closes))
    blk = f[f.rule == "V08"].iloc[0]
    assert blk.rows == 6


def test_placeholder_bar_flagged():
    df = make_daily([100, 101, 102])
    df["volume"] = [5, 0, 5]
    df.loc[1, ["open", "high", "low", "close"]] = 101.0
    assert "V06" in set(validate_daily(df, "X.csv").rule)


def test_pre_listing_rows_flagged_for_tcs():
    df = load_csv("TCSd1.csv", sort=False)
    f = validate_daily(df, "TCSd1.csv")
    v10 = f[f.rule == "V10"].iloc[0]
    assert v10.date_end == "2004-08-24"


def test_clean_load_excludes_reviewed_rows_and_leaves_raw_untouched():
    path = find_file("RELIANCEd1.csv")
    before = file_sha256(path)
    clean, prov = load_clean("RELIANCEd1.csv")
    assert file_sha256(path) == before == prov["raw_sha256"]
    assert pd.Timestamp("2005-07-28") not in set(clean["date"])
    assert not clean["date"].between("1997-10-27", "1997-11-04").any()
    ex = pd.read_csv("data/metadata/exclusions.csv", dtype=str)
    ex = ex[ex.dataset_file == "RELIANCEd1.csv"]
    assert set(prov["exclusion_ids"]) == set(ex.exclusion_id)
    raw = load_csv("RELIANCEd1.csv")
    hit = pd.Series(False, index=raw.index)
    for e in ex.itertuples():
        hit |= raw["date"].between(e.date_start, e.date_end)
    assert prov["rows_excluded"] == hit.sum()          # overlaps (e.g. 1997-10-31) counted once
    assert clean["close"].pct_change().abs().max() < 0.5      # remaining moves plausible


def test_clean_checksum_is_deterministic():
    assert load_clean("TCSd1.csv")[1]["clean_sha256"] == load_clean("TCSd1.csv")[1]["clean_sha256"]
    assert load_clean("TCSd1.csv")[0]["date"].min() == pd.Timestamp("2004-08-25")

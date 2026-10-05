"""Stage 2 normalised daily panel (Phase 2C) from the raw NSE archive.

One row per (date, symbol) for SERIES == EQ, columns:
  date symbol isin series open high low close last prevclose volume value trades
  source(legacy_cm|udiff_cm) source_sha256
Legacy is used through 2023-12-31, UDiFF from 2024-01-01 (both exist 2024-01-01..
2024-07-05; every overlap day is compared field by field and any difference is
reported, never silently resolved). ISIN/trades are NaN in legacy files before
2011-06-22 (not published then). Dates after RESEARCH_CUTOFF are refused.
"""

import io
import json
import zipfile
from datetime import date

import numpy as np
import pandas as pd

from src.access import RESEARCH_CUTOFF
from src.config import BASE_DIR
from src.stage2.archive import MANIFEST

COLS = ["date", "symbol", "isin", "series", "open", "high", "low", "close", "last", "prevclose",
        "volume", "value", "trades"]
LEGACY = {"SYMBOL": "symbol", "SERIES": "series", "OPEN": "open", "HIGH": "high", "LOW": "low",
          "CLOSE": "close", "LAST": "last", "PREVCLOSE": "prevclose", "TOTTRDQTY": "volume",
          "TOTTRDVAL": "value", "TOTALTRADES": "trades", "ISIN": "isin", "TIMESTAMP": "date"}
UDIFF = {"TckrSymb": "symbol", "SctySrs": "series", "OpnPric": "open", "HghPric": "high", "LwPric": "low",
         "ClsPric": "close", "LastPric": "last", "PrvsClsgPric": "prevclose", "TtlTradgVol": "volume",
         "TtlTrfVal": "value", "TtlNbOfTxsExctd": "trades", "ISIN": "isin", "TradDt": "date"}
UDIFF_FROM = date(2024, 1, 1)


def raw_files():
    """Manifest records of downloaded bhavcopies (status 200), by kind."""
    recs = [json.loads(l) for l in MANIFEST.read_text().splitlines() if l.strip()]
    return [r for r in recs if r["kind"] in ("legacy_cm", "udiff_cm") and r["status"] == 200]


def parse(blob, kind, session):
    """Raw zip bytes -> normalised EQ rows for one session (no repair)."""
    if pd.Timestamp(session) > pd.Timestamp(RESEARCH_CUTOFF):
        raise ValueError(f"{session} after research cutoff - refused")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        df = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), dtype=str)
    df.columns = [c.strip() for c in df.columns]
    if kind == "udiff_cm":
        df = df[df["FinInstrmTp"].str.strip() == "STK"]
    df = df.rename(columns=LEGACY if kind == "legacy_cm" else UDIFF)
    for c in COLS:
        if c not in df:
            df[c] = np.nan
    df = df[COLS].copy()
    for c in ("symbol", "series", "isin"):
        df[c] = df[c].astype("string").str.strip()
    df = df[df["series"] == "EQ"]
    for c in ("open", "high", "low", "close", "last", "prevclose", "volume", "value", "trades"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    file_date = pd.to_datetime(df["date"], format="mixed", dayfirst=kind == "legacy_cm", errors="coerce")
    if (file_date.dropna().dt.date != pd.Timestamp(session).date()).any():
        raise ValueError(f"{kind} {session}: row dates disagree with the file's session")
    df["date"] = pd.Timestamp(session)
    df["source"] = kind
    return df.reset_index(drop=True)


def build_year(year, files):
    """All EQ rows of one calendar year + overlap comparison records."""
    by = {}
    for r in files:
        s = date.fromisoformat(r["session"])
        if s.year == year:
            by.setdefault(s, {})[r["kind"]] = r
    out, overlap = [], []
    for s in sorted(by):
        k = by[s]
        use = "udiff_cm" if s >= UDIFF_FROM and "udiff_cm" in k else "legacy_cm"
        if use not in k:
            continue
        rec = k[use]
        df = parse((BASE_DIR / rec["path"]).read_bytes(), use, s)
        df["source_sha256"] = rec["sha256"]
        out.append(df)
        if len(k) == 2:                                    # overlap day: compare formats
            other = parse((BASE_DIR / k["legacy_cm"]["path"]).read_bytes(), "legacy_cm", s)
            a, b = df.set_index("symbol"), other.set_index("symbol")
            common = a.index.intersection(b.index)
            fields = ["open", "high", "low", "close", "last", "prevclose", "volume", "value", "trades", "isin"]
            diff = {f: int((a.loc[common, f].astype(str) != b.loc[common, f].astype(str)).sum()) for f in fields}
            overlap.append({"session": str(s), "udiff_rows": len(a), "legacy_rows": len(b),
                            "common": len(common), "field_mismatches": diff})
    return (pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=COLS)), overlap


def qa(df):
    """Data-quality counts for one panel chunk (flags only, nothing removed)."""
    px = df[["open", "high", "low", "close"]]
    return {
        "rows": len(df),
        "duplicate_symbol_date": int(df.duplicated(["date", "symbol"]).sum()),
        "impossible_ohlc": int(((df["high"] < px.max(axis=1)) | (df["low"] > px.min(axis=1))).sum()),
        "non_positive_price": int((px <= 0).any(axis=1).sum()),
        "missing_price": int(px.isna().any(axis=1).sum()),
        "negative_or_missing_volume": int(((df["volume"] < 0) | df["volume"].isna()).sum()),
        "negative_value": int((df["value"] < 0).sum()),
        "missing_isin_rows": int(df["isin"].isna().sum()),
    }


# ------------------------------------------------- data-quality and dataset build (PANEL-1)

METHOD_VERSION = "PANEL-1"


def qa_conflicts(df):
    """Identity conflicts inside one panel chunk (flags only)."""
    d = df[df["isin"].notna() & (df["isin"] != "")]
    return {
        "isin_on_two_symbols_same_day": int(d.groupby(["date", "isin"])["symbol"].nunique().gt(1).sum()),
        "symbol_with_two_isins_same_day": int(d.groupby(["date", "symbol"])["isin"].nunique().gt(1).sum()),
    }


def calendar_check(manifest_records, start, end, holidays=None):
    """Every weekday in [start, end] must be either a downloaded session (200) or a recorded
    404 (no NSE file = non-trading day). `holidays`: optional set of NSE holiday dates to
    cross-check 404 weekdays against (only years with a stored NSE holiday list)."""
    days = pd.bdate_range(start, end)
    ok = {r["session"] for r in manifest_records if r["status"] == 200 and r["kind"] in ("legacy_cm", "udiff_cm")}
    miss = {r["session"] for r in manifest_records if r["status"] == 404 and r["kind"] in ("legacy_cm", "udiff_cm")} - ok
    iso = [d.date().isoformat() for d in days]
    out = {"weekdays": len(iso), "sessions": sum(d in ok for d in iso),
           "non_trading_weekdays_404": sum(d in miss for d in iso),
           "never_attempted": [d for d in iso if d not in ok and d not in miss]}
    if holidays is not None:
        h = {d.isoformat() for d in holidays}
        n404 = {d for d in iso if d in miss}
        out["404_not_in_holiday_list"] = sorted(n404 - h)
        out["holiday_with_file"] = sorted({d for d in iso if d in h} & ok)
    return out


def build_dataset(out_dir, years=range(2005, 2027)):
    """Write one parquet per year (EQ rows, raw values) + return manifest entries."""
    import hashlib
    out_dir = BASE_DIR / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    files, entries, overlaps = raw_files(), [], []
    for y in years:
        df, ov = build_year(y, files)
        if df.empty:
            continue
        f = out_dir / f"panel1_{y}.parquet"
        if f.exists():
            raise FileExistsError(f"{f} exists - generated datasets are never overwritten")
        df.to_parquet(f, index=False)
        entries.append({"file": str(f.relative_to(BASE_DIR)), "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
                        "year": y, "sessions": int(df["date"].nunique()), "symbols": int(df["symbol"].nunique()),
                        "first": str(df["date"].min().date()), "last": str(df["date"].max().date()),
                        "qa": qa(df) | qa_conflicts(df)})
        overlaps += ov
    return entries, overlaps

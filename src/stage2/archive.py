"""Stage 2 raw NSE archive (Phase 2B). Append-only, never overwrites, checksummed.

Raw files live OUTSIDE git under data/raw/nse_archive/<kind>/...; every attempt
(including HTTP 404 = "no file for that weekday") is recorded once in the
committed manifest data/stage2/raw_manifest.jsonl. Datasets are always rebuilt
from these raw files. Nothing dated after src.access.RESEARCH_CUTOFF is fetched.

    python3 -m src.stage2.archive bhavcopy 2005-01-01 2026-09-30
    python3 -m src.stage2.archive corporate-actions 1995 2026
    python3 -m src.stage2.archive lists
"""

import hashlib
import http.cookiejar
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta

from src.access import RESEARCH_CUTOFF
from src.config import BASE_DIR, DATA_DIR

RAW = DATA_DIR / "raw" / "nse_archive"
MANIFEST = BASE_DIR / "data" / "stage2" / "raw_manifest.jsonl"
LEGACY_LAST = date(2024, 7, 5)              # verified last legacy file (source audit)
UDIFF_FIRST = date(2024, 1, 1)              # verified first UDiFF file
UA = {"User-Agent": "Mozilla/5.0"}
LISTS = {
    "symbolchange.csv": "https://nsearchives.nseindia.com/content/equities/symbolchange.csv",
    "namechange.csv": "https://nsearchives.nseindia.com/content/equities/namechange.csv",
    "delisted.csv": "https://nsearchives.nseindia.com/content/equities/delisted.csv",
    "EQUITY_L.csv": "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv",
}


def legacy_url(d):
    m = d.strftime("%b").upper()
    return f"https://nsearchives.nseindia.com/content/historical/EQUITIES/{d:%Y}/{m}/cm{d:%d}{m}{d:%Y}bhav.csv.zip"


def udiff_url(d):
    return f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{d:%Y%m%d}_F_0000.csv.zip"


def manifest():
    if not MANIFEST.exists():
        return {}
    return {r["url"]: r for r in map(json.loads, filter(str.strip, MANIFEST.read_text().splitlines()))}


def _append(rec):
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "a") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")


def fetch(url, rel, kind, session=None, opener=None, known=None):
    """Download url -> RAW/rel once. Returns the manifest record."""
    if session and session > date.fromisoformat(RESEARCH_CUTOFF):
        raise ValueError(f"{session} is after the research cutoff {RESEARCH_CUTOFF} - refused")
    known = manifest() if known is None else known
    if url in known:
        return known[url]
    path = RAW / rel
    rec = {"kind": kind, "url": url, "path": str(path.relative_to(BASE_DIR)),
           "session": str(session) if session else None,
           "retrieved_at": datetime.now().astimezone().isoformat(timespec="seconds")}
    if path.exists():                                   # pre-existing raw file: record, never overwrite
        blob = path.read_bytes()
        rec |= {"status": 200, "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
                "note": "already present before manifest entry"}
    else:
        try:
            blob = (opener or urllib.request.build_opener()).open(
                urllib.request.Request(url, headers=UA), timeout=60).read()
        except urllib.error.HTTPError as e:
            rec |= {"status": e.code}
            _append(rec)
            known[url] = rec
            return rec
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".part")
        tmp.write_bytes(blob)
        tmp.rename(path)                                # atomic; target did not exist
        rec |= {"status": 200, "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()}
    _append(rec)
    known[url] = rec
    return rec


def weekdays(start, end):
    d = start
    while d <= end:
        if d.weekday() < 5:
            yield d
        d += timedelta(days=1)


def archive_bhavcopy(start, end, pause=0.15):
    end = min(end, date.fromisoformat(RESEARCH_CUTOFF))
    known, n = manifest(), 0
    for d in weekdays(start, end):
        jobs = []
        if d <= LEGACY_LAST:
            jobs.append((legacy_url(d), f"legacy_cm/{d:%Y}/cm{d:%Y%m%d}bhav.csv.zip", "legacy_cm"))
        if d >= UDIFF_FIRST:
            jobs.append((udiff_url(d), f"udiff_cm/{d:%Y}/BhavCopy_NSE_CM_{d:%Y%m%d}.csv.zip", "udiff_cm"))
        for url, rel, kind in jobs:
            if url in known:
                continue
            for attempt in range(3):
                try:
                    fetch(url, rel, kind, d, known=known)
                    break
                except (urllib.error.URLError, TimeoutError, ConnectionError) as e:   # transient
                    if attempt == 2:
                        print(f"{d} {kind}: giving up this run ({e}); rerun resumes", flush=True)
                    time.sleep(5 * (attempt + 1))
            n += 1
            time.sleep(pause)
        if d.day == 1:
            print(f"... {d} ({n} requests)", flush=True)
    return n


def _nse_opener():
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    op.open(urllib.request.Request("https://www.nseindia.com/companies-listing/corporate-filings-actions",
                                   headers=UA), timeout=60).read()
    op.addheaders = [("User-Agent", UA["User-Agent"]),
                     ("Referer", "https://www.nseindia.com/companies-listing/corporate-filings-actions")]
    return op


def archive_corporate_actions(y0, y1):
    op = _nse_opener()
    for y in range(y0, y1 + 1):
        end = min(date(y, 12, 31), date.fromisoformat(RESEARCH_CUTOFF))
        url = ("https://www.nseindia.com/api/corporates-corporateActions?index=equities"
               f"&from_date=01-01-{y}&to_date={end:%d-%m-%Y}")
        fetch(url, f"corp_actions/corp_actions_{y}.json", "corp_actions", opener=op)
        time.sleep(1.5)


def archive_lists():
    for name, url in LISTS.items():
        fetch(url, f"equities_lists/{date.today():%Y%m%d}_{name}", "equities_list")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "bhavcopy":
        archive_bhavcopy(date.fromisoformat(sys.argv[2]), date.fromisoformat(sys.argv[3]))
    elif cmd == "corporate-actions":
        archive_corporate_actions(int(sys.argv[2]), int(sys.argv[3]))
    elif cmd == "lists":
        archive_lists()

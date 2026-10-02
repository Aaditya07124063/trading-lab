"""Bhavcopy cross-check - DATA-QUALITY VALIDATION ONLY (approved 2026-10-01).

For every (stock, standard session) compared with NSE's official CM bhavcopy
(EQ series) for that date:
  C1 RANGE       every Yahoo 15-min bar must lie inside the official day range:
                 bar high <= HghPric*(1+1e-4) and bar low >= LwPric*(1-1e-4).
                 (Development data 2026-07..09: 716/716 stock-days inside.)
  C2 PRESENCE    Yahoo bars exist but the stock has no EQ row / zero volume in
                 the bhavcopy, or vice versa.
  C3 VOLUME      Yahoo day volume / NSE TtlTradgVol outside [0.50, 1.05]
                 (development range 0.76-1.00).
NOT checked: the 09:15 open. NSE's OpnPric is the pre-open call-auction price
and legitimately differs from Yahoo's first-bar open (dev median 12 bps).

A discrepancy is LOGGED (one row: session, symbol, check, detail) and saved
with the evaluation artifacts; an unavailable bhavcopy is logged as
C0_UNAVAILABLE. Flags NEVER modify, exclude, repair or alter any observation
or any performance calculation (frozen 2026-10-01: tolerance 1 bp, volume
ratio 0.50-1.05).
"""

import io
import urllib.request
import zipfile

import pandas as pd

from src.config import BASE_DIR

RAW = BASE_DIR / "data" / "raw" / "nse_bhavcopy"
URL = "https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{d}_F_0000.csv.zip"
TOL = 1e-4
VOL_RANGE = (0.50, 1.05)


def load_bhavcopy(session):
    """EQ rows of NSE's CM bhavcopy for an ISO date; raw zip cached, never edited."""
    d = session.replace("-", "")
    f = RAW / f"BhavCopy_NSE_CM_0_0_0_{d}_F_0000.csv.zip"
    if not f.exists():
        req = urllib.request.Request(URL.format(d=d), headers={"User-Agent": "Mozilla/5.0"})
        blob = urllib.request.urlopen(req, timeout=60).read()
        RAW.mkdir(parents=True, exist_ok=True)
        f.write_bytes(blob)
    with zipfile.ZipFile(f) as z:
        b = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])))
    return b[b["SctySrs"].str.strip() == "EQ"].set_index("TckrSymb")


def check(bars, bhav, session, symbols):
    """bars: {symbol: that session's 15-min bars (may be empty)}; bhav: EQ rows.
    Returns a list of discrepancy dicts."""
    out = []
    for s in symbols:
        b = bars.get(s)
        have_y = b is not None and len(b) > 0
        have_n = s in bhav.index and bhav.at[s, "TtlTradgVol"] > 0
        if have_y != have_n:
            out.append({"session": session, "symbol": s, "check": "C2_PRESENCE",
                        "detail": f"yahoo={have_y} nse={have_n}"})
            continue
        if not have_y:
            continue
        hi, lo = bhav.at[s, "HghPric"], bhav.at[s, "LwPric"]
        if b["high"].max() > hi * (1 + TOL) or b["low"].min() < lo * (1 - TOL):
            out.append({"session": session, "symbol": s, "check": "C1_RANGE",
                        "detail": f"yahoo [{b['low'].min()}, {b['high'].max()}] vs nse [{lo}, {hi}]"})
        r = b["volume"].sum() / bhav.at[s, "TtlTradgVol"]
        if not VOL_RANGE[0] <= r <= VOL_RANGE[1]:
            out.append({"session": session, "symbol": s, "check": "C3_VOLUME", "detail": f"ratio={r:.3f}"})
    return out

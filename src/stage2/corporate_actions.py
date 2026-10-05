"""Stage 2 corporate-action evidence layer (Phase 2D). Methodology version CA-1.

SOURCE: NSE corporate-actions API, archived raw JSON per year (src/stage2/archive.py).
Comprehensive only from 2006 (source audit) - adjustments are applied 2006-01-01+.

PARSING (subject text, strict; anything else -> UNPARSED, never adjusted):
  equity bonus "Bonus a:b" (a new shares for every b held)   price factor f = b/(a+b)
  face-value split "from Rs X ... to Rs/Re Y"                 price factor f = Y/X
  bonus and split in one subject                              f = product
  debenture / preference / NCRPS "bonus", consolidation,
  rights, dividends                                           recorded, NOT adjusted

ADJUSTMENT (backward): adjusted_price(t) = raw_price(t) * prod{f_e : ex_date_e > t}
                      adjusted_volume(t) = raw_volume(t) / prod{f_e : ex_date_e > t}

VALIDATION of each (symbol, ex_date) against prices (no repair), all adjusting records
of that day combined (product of factors):
  t0 = last session before ex-date, t1 = first session on/after ex-date (<= 10 days)
  raw = close(t1)/close(t0); adj = raw / f
  VALIDATED    |log(adj)| < log(1.25) and |log(adj)| < |log(raw)|   (adjustment explains the move)
  INCONCLUSIVE |log f| < log(1.25): too small to separate from normal volatility
  DISCREPANT   otherwise (flagged; still listed with numbers)
  NO_PRICES:<reason>  no usable session around the ex-date
Also records whether NSE's PREVCLOSE on t1 equals close(t0) (unadjusted) or close(t0)*f (adjusted).
"""

import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.access import RESEARCH_CUTOFF
from src.config import BASE_DIR
from src.stage2.archive import MANIFEST

METHOD_VERSION = "CA-2"   # CA-1 -> CA-2: same-day factors combined, "Spl"/"Bon" parsing, INCONCLUSIVE status
ADJUST_FROM = pd.Timestamp("2006-01-01")
_BONUS = re.compile(r"(?:bonus|\bbon\b)(?:\s+issue|\s+shares\s+in\s+the\s+ratio\s+of)?\s*[-(:]?\s*(\d+)\s*:\s*(\d+)", re.I)
_SPLIT = re.compile(r"(?:split|\bspl\b|sub-?division)\D*?(?:r[se]\.?\s*)?(\d+(?:\.\d+)?)\D*?(?<!in)to\D*?(?:r[se]\.?\s*)?(\d+(?:\.\d+)?)", re.I)
# "Spl" means SPLIT ("Fv Spl-Rs10 To Rs2") or SPECIAL dividend ("Div fin-10% + spl-5%").
_SPECIAL_DIV = re.compile(r"\+\s*spl|\bspl\b[\s.\-]*(?:div|dividend|int|interim|&|@|\d+(?:\.\d+)?\s*%)", re.I)
_NON_EQUITY = re.compile(r"debenture|\bdeb|ncrps|preference|\bpref\b|\bdvr\b", re.I)


def parse_subject(subject):
    """-> (kind, factor, detail). kind in BONUS, SPLIT, BONUS+SPLIT, NON_EQUITY_BONUS,
    CONSOLIDATION, RIGHTS, DIVIDEND, UNPARSED_BONUS_SPLIT, OTHER."""
    s = " ".join(str(subject).split())
    low = s.lower()
    if "consolidat" in low:
        return "CONSOLIDATION", None, s
    if "bonus" in low and _NON_EQUITY.search(low):
        return "NON_EQUITY_BONUS", None, s
    f, kinds = 1.0, []
    b = _BONUS.search(s)
    if b:
        a, h = int(b.group(1)), int(b.group(2))
        if a > 0 and h > 0:
            f *= h / (a + h)
            kinds.append("BONUS")
    special = _SPECIAL_DIV.search(low)
    sp = _SPLIT.search(s)
    if sp and sp.group(0).lower().startswith("spl") and special:
        sp = None                                       # "spl" here is a special dividend
    if sp:
        x, y = float(sp.group(1)), float(sp.group(2))
        if x > 0 and y > 0 and y < x:
            f *= y / x
            kinds.append("SPLIT")
    split_mentioned = re.search(r"split|sub-?div", low) or (re.search(r"\bspl\b", low) and not special)
    bonus_mentioned = re.search(r"bonus|\bbon\b", low)
    if (split_mentioned and "SPLIT" not in kinds) or (bonus_mentioned and "BONUS" not in kinds):
        return "UNPARSED_BONUS_SPLIT", None, s          # mentioned but not parseable: never adjust
    if kinds:
        return "+".join(kinds), f, s
    if "right" in low:
        return "RIGHTS", None, s
    if "div" in low:
        return "DIVIDEND", None, s
    return "OTHER", None, s


def load_events():
    """All archived NSE corporate-action records (EQ series), parsed. Ex-dates
    after the research cutoff are dropped."""
    recs = [json.loads(l) for l in MANIFEST.read_text().splitlines() if l.strip()]
    rows = []
    for r in recs:
        if r["kind"] != "corp_actions" or r["status"] != 200:
            continue
        data = json.loads((BASE_DIR / r["path"]).read_text())
        for x in data if isinstance(data, list) else data.get("data", []):
            rows.append({**x, "source_sha256": r["sha256"]})
    ev = pd.DataFrame(rows)
    ev = ev[ev["series"] == "EQ"].copy()
    ev["ex_date"] = pd.to_datetime(ev["exDate"], format="%d-%b-%Y", errors="coerce")
    ev = ev[ev["ex_date"].notna() & (ev["ex_date"] <= pd.Timestamp(RESEARCH_CUTOFF))]
    parsed = ev["subject"].map(parse_subject)
    ev["kind"] = parsed.str[0]
    ev["factor"] = parsed.str[1]
    ev = ev.rename(columns={"symbol": "symbol", "isin": "isin"})
    keep = ["symbol", "isin", "comp", "subject", "ex_date", "recDate", "faceVal", "kind", "factor", "source_sha256"]
    return ev[keep].drop_duplicates(["symbol", "ex_date", "subject"]).sort_values(["ex_date", "symbol"]).reset_index(drop=True)


def combined_events(events):
    """One row per (symbol, ex_date): product of the factors of all adjusting
    records that day (NSE sometimes files a bonus and a split as separate rows).
    Identical subjects were already de-duplicated in load_events()."""
    adj = events[events["factor"].notna()]
    return (adj.groupby(["symbol", "ex_date"], as_index=False)
               .agg(factor=("factor", "prod"), kind=("kind", lambda k: "+".join(sorted(set(k)))),
                    subject=("subject", " | ".join), n_records=("subject", "size")))


def classify(raw, factor):
    """Price-continuity verdict for one event (no price is changed).
    VALIDATED    the factor explains the move: |log(raw/f)| < log 1.25 and smaller than |log raw|
    INCONCLUSIVE |log f| < log 1.25 - a move this small is indistinguishable from
                 normal daily volatility, so prices can neither confirm nor reject it
    DISCREPANT   otherwise"""
    if abs(math.log(factor)) < math.log(1.25):
        return "INCONCLUSIVE"
    adjr = raw / factor
    ok = abs(math.log(adjr)) < math.log(1.25) and abs(math.log(adjr)) < abs(math.log(raw))
    return "VALIDATED" if ok else "DISCREPANT"


def validate(events, panel, window_days=10):
    """Combined adjusting events (ex 2006+) vs EQ prices. panel: date, symbol, close, prevclose.
    NO_PRICES reasons: SYMBOL_NOT_IN_PANEL / NO_SESSION_BEFORE_EX (often a later symbol
    change - identity layer) / NO_SESSION_AFTER_EX (suspended, other series, delisted)."""
    ev = combined_events(events)
    ev = ev[ev["ex_date"] >= ADJUST_FROM]
    g = {s: d.sort_values("date") for s, d in panel[panel["symbol"].isin(ev["symbol"])].groupby("symbol")}
    out = []
    for e in ev.itertuples():
        d = g.get(e.symbol)
        status, raw, prev_conv, t0, t1 = "NO_PRICES:SYMBOL_NOT_IN_PANEL", None, None, None, None
        if d is not None:
            before = d[d["date"] < e.ex_date]
            after = d[(d["date"] >= e.ex_date) & (d["date"] <= e.ex_date + pd.Timedelta(days=window_days))]
            if not len(before):
                status = "NO_PRICES:NO_SESSION_BEFORE_EX"
            elif not len(after):
                status = "NO_PRICES:NO_SESSION_AFTER_EX"
            else:
                c0, c1 = before.iloc[-1], after.iloc[0]
                t0, t1 = c0["date"], c1["date"]
                raw = c1["close"] / c0["close"]
                status = classify(raw, e.factor)
                pc = c1["prevclose"]
                prev_conv = ("UNADJUSTED" if np.isclose(pc, c0["close"], rtol=1e-4) else
                             "ADJUSTED" if np.isclose(pc, c0["close"] * e.factor, rtol=2e-2) else "OTHER")
        out.append({"symbol": e.symbol, "ex_date": e.ex_date, "kind": e.kind, "factor": e.factor,
                    "n_records": e.n_records, "subject": e.subject, "t0": t0, "t1": t1,
                    "raw_ratio": raw, "status": status, "prevclose_convention": prev_conv})
    return pd.DataFrame(out)


def unexplained_jumps(panel, events, threshold=0.4, window_days=10):
    """Session-to-session close ratios outside [1/(1+t), 1+t]... reported as
    UNEXPLAINED unless an adjusting event for that symbol lies within the window."""
    p = panel.sort_values(["symbol", "date"]).reset_index(drop=True)
    prev = p.groupby("symbol")["close"].shift(1)
    r = p["close"] / prev
    big = p[(r > 1 + threshold) | (r < 1 / (1 + threshold))].assign(ratio=r)
    adj = events[events["factor"].notna()][["symbol", "ex_date"]]
    m = big.merge(adj, on="symbol", how="left")
    m["near"] = (m["ex_date"] - m["date"]).abs() <= pd.Timedelta(days=window_days)
    near = m.groupby(["symbol", "date"])["near"].any().rename("explained").reset_index()
    return big.merge(near, on=["symbol", "date"], how="left").fillna({"explained": False})

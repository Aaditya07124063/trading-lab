"""Trading Lab backend - serves the engine to the web UI.
Run with:  python3 -m uvicorn server:app"""

import re
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from src import leaderboard
from src.config import DATA_DIR, CAPITAL
from src.access import RESEARCH_CUTOFF, research_load_csv
from src.research import run_daily
from src import research_view
from src.registry.experiments import log_trial
from src.intraday.costs import CostModel
from src.intraday.data import load_intraday, timeframe_of
from src.intraday.engine import EngineConfig, run_intraday, run_open_to_close_benchmark
from src.intraday.metrics import daily_equity as intraday_daily_equity
from src.intraday.orb import ORB
from src.intraday.research import run_study

app = FastAPI()


@app.get("/api/watchlist")
def watchlist():
    """Real last close + daily change for every daily file in data/."""
    rows = []
    for p in sorted(DATA_DIR.rglob("*.csv")):
        if not (p.name.endswith("d1.csv") or "10Y" in p.name):
            continue
        try:
            df = research_load_csv(p.name)          # nothing after 2026-09-30
        except Exception:
            continue
        if len(df) < 2:
            continue
        last, prev = float(df.close.iloc[-1]), float(df.close.iloc[-2])
        stale = (pd.Timestamp.now() - df.date.iloc[-1]).days > 30
        sym = p.name.replace("d1.csv", "").replace(".csv", "")
        rows.append({
            "symbol": sym, "file": p.name,
            "exchange": "CSV" if stale else ("NSE INDEX" if "NIFTY" in sym or "SENSEX" in sym else "NSE"),
            "tag": f"HIST {df.date.iloc[-1].year}" if stale else "",
            "price": round(last, 2),
            "chg": round(last - prev, 2),
            "pct": round((last / prev - 1) * 100, 2),
            "years": round((df.date.iloc[-1] - df.date.iloc[0]).days / 365),
        })
    rows.sort(key=lambda r: (r["tag"] != "", r["symbol"]))
    return rows


@app.get("/api/leaderboard")
def get_leaderboard():
    df = leaderboard.load().sort_values("margin", ascending=False)
    return df.astype(object).where(df.notna(), "").to_dict(orient="records")


@app.get("/api/search")
def search(q: str):
    """Search every NSE/BSE listing through Yahoo Finance."""
    import requests
    try:
        r = requests.get("https://query2.finance.yahoo.com/v1/finance/search",
                         params={"q": q, "quotesCount": 15, "newsCount": 0},
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        quotes = r.json().get("quotes", [])
    except Exception:
        return []
    out = []
    for it in quotes:
        sym = it.get("symbol", "")
        if (sym.endswith(".NS") or sym.endswith(".BO")) and not sym.startswith("0P"):
            out.append({"symbol": sym,
                        "name": it.get("shortname") or it.get("longname") or "",
                        "exchange": "NSE" if sym.endswith(".NS") else "BSE"})
    return out


@app.get("/api/add")
def add_symbol(symbol: str):
    """Download full daily history of any Yahoo symbol into data/india/."""
    import yfinance as yf
    df = yf.Ticker(symbol).history(period="max", interval="1d", auto_adjust=False)
    if df is None or df.empty:
        return {"ok": False, "error": "Yahoo returned no data for " + symbol}
    if getattr(df.index, "tz", None) is not None:
        df.index = df.index.tz_localize(None)
    out = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    out.columns = ["open", "high", "low", "close", "tick_volume"]
    out = out.dropna(subset=["open", "close"]).round(2)
    out = out[out.index <= RESEARCH_CUTOFF]                # never save post-cutoff data
    out["tick_volume"] = out["tick_volume"].fillna(0).astype("int64")
    out.index = out.index.strftime("%Y-%m-%d")
    out.index.name = "Date"
    clean = symbol.replace(".NS", "").replace(".BO", "").replace("^", "").replace("&", "")
    (DATA_DIR / "india").mkdir(parents=True, exist_ok=True)
    out.to_csv(DATA_DIR / "india" / f"{clean}d1.csv")
    return {"ok": True, "file": f"{clean}d1.csv"}


def _backtest(file, kind, fast, slow, trailing):
    if "/" in file or "\\" in file or ".." in file:
        raise HTTPException(400, "bad file name")
    try:
        return run_daily(file, kind, fast, slow,
                         trailing_stop=trailing / 100 if trailing else None)
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(400, str(e))


@app.get("/api/backtest")
def backtest(file: str, kind: str = "ema", fast: int = 20, slow: int = 50,
             trailing: float = 0.0):
    """Runs a backtest. Read-only: it never touches the leaderboard."""
    df, trades, r = _backtest(file, kind, fast, slow, trailing)
    log_trial("daily_crossover", {"kind": kind, "fast": fast, "slow": slow, "trailing": trailing},
              file, {"return_pct": r["return_pct"], "bh_pct": r["bh_pct"]}, "web")

    step = max(1, len(df) // 300)
    bh = df["close"] / df["open"].iloc[0] * CAPITAL
    return {
        "metrics": r,
        "candles": len(df),
        "start": str(df.date.iloc[0].date()),
        "end": str(df.date.iloc[-1].date()),
        "dates": [d.strftime("%Y-%m-%d") for d in df["date"][::step]],
        "equity": [round(float(v)) for v in df["equity"][::step]],
        "bh": [round(float(v)) for v in bh[::step]],
        "trades": [
            {"entry_date": str(t["entry_date"].date()), "entry": round(t["entry"], 1),
             "exit_date": str(t["exit_date"].date()) if t["exit_date"] is not None else "open",
             "pnl_pct": round(t["pnl_pct"], 1), "reason": t["reason"]}
            for t in trades[-12:]
        ],
    }


@app.post("/api/leaderboard/save")
def save_to_leaderboard(file: str, kind: str = "ema", fast: int = 20, slow: int = 50,
                        trailing: float = 0.0):
    """Explicit save: re-runs the experiment and upserts it by name."""
    _, _, r = _backtest(file, kind, fast, slow, trailing)
    leaderboard.save([r])
    return {"ok": True, "name": r["name"]}


@app.get("/api/intraday/files")
def intraday_files():
    """Every m15/h1 file with its data-quality report."""
    out = []
    for p in sorted((DATA_DIR / "india").glob("*.csv")):
        if not re.search(r"(m15|h1)\.csv$", p.name):
            continue
        try:
            _, r = load_intraday(p.name)
            out.append({"file": p.name, **{k: r[k] for k in ("symbol", "timeframe_min", "sessions",
                        "start", "end", "warnings")}, "ok": True})
        except ValueError as e:
            out.append({"file": p.name, "ok": False, "warnings": [str(e)]})
    return out


@app.get("/api/intraday/run")
def intraday_run(file: str, range_minutes: int = 30, cutoff: str = "14:30",
                 short: bool = True, gross: bool = False):
    """ORB vs open-to-close benchmark. Read-only; nothing is saved."""
    if "/" in file or ".." in file:
        raise HTTPException(400, "bad file name")
    try:
        costs = CostModel.zero() if gross else CostModel.load()
    except (FileNotFoundError, TypeError, ValueError) as e:
        raise HTTPException(409, f"Cost schedule not configured: {e}")
    cfg = EngineConfig(entry_cutoff=cutoff, allow_short=short)
    try:
        st = run_study(file, costs, range_minutes, cfg, save=False)
        full = run_intraday(load_intraday(file)[0], ORB(range_minutes, timeframe_of(file)), costs, cfg)
        bench = run_open_to_close_benchmark(load_intraday(file)[0], costs, cfg)
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(400, str(e))
    log_trial("intraday_orb", {"range_minutes": range_minutes, "cutoff": cutoff, "short": short,
                               "costs": costs.name}, file,
              {"return_pct": st["summary"]["return_pct"], "vs_bench": st["vs"]["strategy_minus_benchmark"]}, "web")
    se = intraday_daily_equity(full["equity"])
    be = intraday_daily_equity(bench["equity"])
    dd = (se / se.cummax() - 1) * 100
    t = full["trades"]
    st["curve"] = {"dates": [str(d) for d in se.index], "equity": [round(float(v)) for v in se],
                   "bench": [round(float(v)) for v in be.reindex(se.index).ffill()],
                   "drawdown": [round(float(v), 2) for v in dd]}
    st["trade_list"] = [] if t.empty else t.round(2).tail(60).to_dict(orient="records")
    return st


@app.get("/api/prices")
def prices(file: str, n: int = 400):
    """Real daily OHLCV of one data file, nothing after the research cutoff. Read-only."""
    if "/" in file or "\\" in file or ".." in file:
        raise HTTPException(400, "bad file name")
    try:
        df = research_load_csv(file).tail(max(2, min(n, 6000)))
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(400, str(e))
    vol = next((c for c in ("tick_volume", "volume") if c in df.columns), None)
    return {"file": file, "cutoff": RESEARCH_CUTOFF, "dates": [d.strftime("%Y-%m-%d") for d in df["date"]],
            **{c: [round(float(v), 2) for v in df[c]] for c in ("open", "high", "low", "close")},
            "volume": [int(v) for v in df[vol].fillna(0)] if vol else None}


@app.get("/api/research")
def research():
    """Registered experiments, saved results and hash verification. Read-only; computes nothing new."""
    return research_view.snapshot()


app.mount("/", StaticFiles(directory=Path(__file__).parent / "web", html=True), name="web")
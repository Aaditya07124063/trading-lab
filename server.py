"""Trading Lab backend - serves the engine to the web UI.
Run with:  python3 -m uvicorn server:app"""

import pandas as pd
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.config import DATA_DIR, RESULTS_DIR, CAPITAL
from src.data_loader import load_csv
from src.indicators import add_ema, add_sma
from src.signals import crossover_signal
from src.backtest import run_backtest
from src.metrics import report

app = FastAPI()


@app.get("/api/watchlist")
def watchlist():
    """Real last close + daily change for every daily file in data/."""
    rows = []
    for p in sorted(DATA_DIR.rglob("*.csv")):
        if not (p.name.endswith("d1.csv") or "10Y" in p.name):
            continue
        try:
            df = load_csv(p.name)
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
def leaderboard():
    f = RESULTS_DIR / "leaderboard.csv"
    if not f.exists():
        return []
    df = pd.read_csv(f).sort_values("margin", ascending=False)
    return df.fillna("").to_dict(orient="records")


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
    out["tick_volume"] = out["tick_volume"].fillna(0).astype("int64")
    out.index = out.index.strftime("%Y-%m-%d")
    out.index.name = "Date"
    clean = symbol.replace(".NS", "").replace(".BO", "").replace("^", "").replace("&", "")
    (DATA_DIR / "india").mkdir(parents=True, exist_ok=True)
    out.to_csv(DATA_DIR / "india" / f"{clean}d1.csv")
    return {"ok": True, "file": f"{clean}d1.csv"}


@app.get("/api/backtest")
def backtest(file: str, kind: str = "ema", fast: int = 20, slow: int = 50,
             trailing: float = 0.0):
    df = load_csv(file)
    add = add_ema if kind == "ema" else add_sma
    df = add(df, fast)
    df = add(df, slow)
    df = crossover_signal(df, f"{kind}_{fast}", f"{kind}_{slow}")
    df, trades = run_backtest(df, trailing_stop=trailing / 100 if trailing else None)
    r = report(df, trades, name=f"{kind.upper()} {fast}/{slow} · {file.replace('.csv', '')}")

    # every run auto-saves to the leaderboard - the research diary grows itself
    board_file = RESULTS_DIR / "leaderboard.csv"
    row = pd.DataFrame([r])
    if board_file.exists():
        row = pd.concat([pd.read_csv(board_file), row])
    row.drop_duplicates(subset="name", keep="last").to_csv(board_file, index=False)

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


app.mount("/", StaticFiles(directory="web", html=True), name="web")
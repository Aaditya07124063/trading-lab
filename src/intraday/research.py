"""One intraday study = strategy vs open-to-close benchmark, on the full
sample AND on chronological dev / validation / final-OOS periods, with every
limitation stated. Parameters are fixed BEFORE running; nothing is tuned here."""

import json
import re

from src.config import RESULTS_DIR
from src.intraday.data import load_intraday, timeframe_of
from src.intraday.engine import EngineConfig, run_intraday, run_open_to_close_benchmark
from src.intraday.metrics import compare, summarize
from src.intraday.orb import ORB

SPLIT = (("development", 0.5), ("validation", 0.25), ("final_oos", 0.25))
MIN_SESSIONS = 250          # ~1 trading year: below this, a result is anecdotal


def split_sessions(df):
    sessions = sorted(df["session"].unique())
    out, start = {}, 0
    for i, (name, frac) in enumerate(SPLIT):
        end = len(sessions) if i == len(SPLIT) - 1 else start + round(len(sessions) * frac)
        keep = set(sessions[start:end])
        out[name] = df[df["session"].isin(keep)]
        start = end
    return out


def limitations(data_report, sessions, tf, range_minutes):
    notes = list(data_report["warnings"])
    if sessions < MIN_SESSIONS:
        notes.append(f"SMALL SAMPLE: {sessions} tradable sessions (< {MIN_SESSIONS}). "
                     "Treat results as anecdotal, not evidence.")
    if tf != 15 or range_minutes != 30:
        notes.append(f"This is ORB {range_minutes}m on {tf}m bars - NOT the 15m ORB-30 "
                     "strategy; do not transfer conclusions between them.")
    return notes


def run_study(file, costs, range_minutes=30, cfg=None, save=True):
    cfg = cfg or EngineConfig()
    tf = timeframe_of(file)
    df, data_report = load_intraday(file)

    def one(part):
        s = summarize(run_intraday(part, ORB(range_minutes, tf), costs, cfg), cfg.capital)
        b = summarize(run_open_to_close_benchmark(part, costs, cfg), cfg.capital)
        return s, b

    full = run_intraday(df, ORB(range_minutes, tf), costs, cfg)
    s = summarize(full, cfg.capital)
    b = summarize(run_open_to_close_benchmark(df, costs, cfg), cfg.capital)
    periods = {}
    for name, part in split_sessions(df).items():
        ps, pb = one(part)
        periods[name] = {"start": ps["start"], "end": ps["end"], "sessions": ps["sessions"],
                         "strategy": ps, "benchmark": pb, "vs": compare(ps, pb)}

    study = {
        "file": file, "strategy": full["strategy"], "timeframe_min": tf,
        "range_minutes": range_minutes, "config": full["config"], "costs": full["costs"],
        "data": {k: data_report[k] for k in ("symbol", "bars", "sessions", "start", "end",
                                               "incomplete_sessions")},
        "skipped_sessions": full["skipped_sessions"],
        "summary": s, "benchmark": b, "vs": compare(s, b), "periods": periods,
        "limitations": limitations(data_report, s["sessions"], tf, range_minutes),
    }
    if save:
        slug = re.sub(r"[^A-Za-z0-9]+", "_", f"{file[:-4]}_orb{range_minutes}_{costs.name}")[:80]
        out = RESULTS_DIR / "intraday" / slug.strip("_")
        out.mkdir(parents=True, exist_ok=True)
        full["trades"].to_csv(out / "trades.csv", index=False)
        full["equity"].to_csv(out / "equity.csv", index=False)
        json.dump(study, open(out / "metrics.json", "w"), indent=2, default=str)
        (out / "summary.txt").write_text(format_study(study))
        study["output_dir"] = str(out)
    return study


def format_study(st):
    s, b, v = st["summary"], st["benchmark"], st["vs"]
    lines = [f"{st['strategy']} · {st['file']} · {s['start']} -> {s['end']}",
             f"Costs: {st['costs']['name']}",
             f"Capital {s['initial_capital']:,.0f} -> {s['final_capital']:,.0f}",
             f"Gross P&L {s['gross_pnl']:+,.0f} | costs {s['total_costs']:,.0f} "
             f"(brokerage {s['brokerage']:,.0f}, STT {s['stt']:,.0f}, exch {s['exchange']:,.0f}, "
             f"SEBI {s['sebi']:,.0f}, stamp {s['stamp']:,.0f}, GST {s['gst']:,.0f}, "
             f"slippage {s['total_slippage']:,.0f}) | NET {s['net_pnl']:+,.0f}",
             f"Return {s['return_pct']:+.2f}% vs open-to-close benchmark {b['return_pct']:+.2f}% "
             f"-> {v['strategy_minus_benchmark']:+.2f} pts",
             f"CAGR {s['cagr']:+.1f}% | Sharpe {s['sharpe']:.2f} (bench {b['sharpe']:.2f}) | "
             f"max DD {s['max_dd']:.1f}% (bench {b['max_dd']:.1f}%) | exposure {s['exposure_pct']}%",
             f"Trades {s['trades']} ({s['long_trades']}L/{s['short_trades']}S) | win {s['win_rate']}% | "
             f"PF {s['profit_factor']} | avg {s['avg_trade']:+,.0f} | best {s['largest_win']:+,.0f} "
             f"| worst {s['largest_loss']:+,.0f}",
             "", "Period            sessions  strategy  benchmark   diff"]
    for name, p in st["periods"].items():
        lines.append(f"{name:17s} {p['sessions']:8d} {p['strategy']['return_pct']:+8.2f}% "
                     f"{p['benchmark']['return_pct']:+9.2f}% {p['vs']['strategy_minus_benchmark']:+7.2f}")
    lines += ["", "LIMITATIONS:"] + [f"  - {n}" for n in st["limitations"]]
    return "\n".join(lines)

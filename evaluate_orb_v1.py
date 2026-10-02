"""ORB v1 LOCKED evaluation pipeline. Not an optimisation tool: every rule and
parameter below is the frozen protocol; there are no tuning options.

    python3 evaluate_orb_v1.py               # THE holdout evaluation (once, after session 250;
                                             # refuses unless ORB_v1.md is FROZEN, the tree is
                                             # clean and all 250 sessions are collected)
    python3 evaluate_orb_v1.py --dry-run-dev # same pipeline on pre-holdout development data

Steps: protocol -> universe -> sessions -> data + validation -> strategy -> costs
-> benchmarks -> random baselines -> statistics -> outputs (read-only) -> manifest
with checksums, protocol hash, git commit, environment -> registry.
"""

import argparse
import hashlib
import json
import os
import stat
import subprocess
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import optimize

from src.config import BASE_DIR, HOLDOUT_START
from src.datasets import file_sha256
from src.intraday.bhavcopy_check import check as bhav_check, load_bhavcopy
from src.intraday.calendar import CAL_DIR, standard_sessions
from src.intraday.costs import CostModel
from src.intraday.data import load_intraday
from src.intraday.engine import EngineConfig, run_intraday, run_open_to_close_benchmark, tradable_sessions
from src.intraday.inference import (deflated_sharpe, holm, mean_inference, randomisation_p, verdict)
from src.intraday.orb import ORB
from src.intraday.regimes import official_closes, regime_labels
from src.intraday.portfolio import (UNIVERSE_FILE, entry_candidates, portfolio_daily,
                                    random_entry_baseline, sign_flip_baseline, trade_net_pnl)
from src.registry.experiments import EXPERIMENTS, environment, log_trial, record

PROTOCOL_FILE = "docs/protocols/ORB_v1.md"
# ---- frozen parameters (mirror docs/protocols/ORB_v1_pre_freeze_audit_20261001.md) ----
HOLDOUT_SESSIONS = 250
DEV_START, DEV_SESSIONS = "2026-08-03", 42          # dry run: all 50 stocks have data from here
K, K_SENS, N_UNIVERSE = 100_000, 1_000_000, 50
PRIMARY = "Z-5"
B, SEED_PRIMARY, SEED_BASELINES = 10_000, 20261001, 20260930
DATA_LIMITED_SHARE = 0.10
CFG = EngineConfig(capital=K)                       # X2 exit, cutoff 14:30, 1 entry/day, shorts on


def sha(path):
    return file_sha256(path) if os.path.exists(path) else None


def scenarios():
    cfg = json.load(open(BASE_DIR / "config" / "cost_scenarios.json"))
    assert cfg["primary"] == PRIMARY
    out = {}
    for name, s in cfg["scenarios"].items():
        out[name] = CostModel.zero() if s["schedule"] is None else CostModel(
            **{**json.load(open(BASE_DIR / "config" / "cost_schedules" / s["schedule"])),
               "slippage_bps": s["slippage_bps"]})
    return out


def universe():
    u = json.load(open(UNIVERSE_FILE))
    assert sha(BASE_DIR / u["raw_file"]) == u["raw_sha256"], "frozen universe file altered"
    syms = [c["symbol"] for c in u["constituents"]]
    assert len(syms) == N_UNIVERSE
    return syms


def git(*a):
    return subprocess.check_output(["git", *a], cwd=BASE_DIR, text=True).strip()


def orb_trial_count():
    """N for the deflated Sharpe: distinct ORB strategy definitions registered."""
    rows = [json.loads(l) for l in open(EXPERIMENTS) if l.strip()]
    return len({r["strategy"] for r in rows if str(r.get("strategy", "")).startswith("ORB")})


def run(mode):
    dry = mode == "dry-run-dev"
    proto_text = (BASE_DIR / PROTOCOL_FILE).read_text()
    if not dry:
        if "**Status:** FROZEN" not in proto_text:
            raise SystemExit(f"{PROTOCOL_FILE} is not FROZEN - holdout evaluation refused")
        if git("status", "--porcelain", "--", "src", "*.py", "config", "docs/protocols", "docs/evidence"):
            raise SystemExit("working tree has uncommitted code/config/protocol changes - refused")
    sessions = (standard_sessions(DEV_START, DEV_SESSIONS) if dry
                else standard_sessions(HOLDOUT_START, HOLDOUT_SESSIONS))
    assert (sessions[-1] < HOLDOUT_START) if dry else (sessions[0] == HOLDOUT_START)
    syms, scen = universe(), scenarios()
    sset = set(sessions)

    data, data_sha, defects, unparseable = {}, {}, {}, {}
    for s in syms:
        f = f"{s}m15.csv"
        df, rep_ = (load_intraday(f, session_errors=True) if dry else
                    load_intraday(f, holdout_protocol=PROTOCOL_FILE, session_errors=True))
        data[s] = df[df["session"].astype(str).isin(sset)].reset_index(drop=True)
        defects[s] = {k: v for k, v in rep_["defective_sessions"].items() if k in sset}
        unparseable[s] = rep_["unparseable_timestamp_rows"]
        data_sha[f] = sha(BASE_DIR / "data" / "india" / f)
    # "250 sessions collected" is a UNIVERSE-level condition (the collector reached
    # session 250); individual stock-sessions may still be untradable (rules below).
    last = max((d["session"].astype(str).max() for d in data.values() if len(d)), default="")
    collected = max(last, max((max(v) for v in defects.values() if v), default=""))
    if not dry and collected < sessions[-1]:
        raise SystemExit(f"collection has not reached session {HOLDOUT_SESSIONS} ({sessions[-1]}) - too early")

    bps = lambda v: None if v is None else round(float(v) * 1e4, 4)

    # ---- strategy (primary) + cost grid + capital sensitivity
    def strat(c, cfg=CFG, short=True):
        return {s: run_intraday(d, ORB(30, 15, allow_short=short), c, cfg) for s, d in data.items()}
    res = {name: strat(c) for name, c in scen.items()}
    port = {name: portfolio_daily(r, sessions, N_UNIVERSE, K) for name, r in res.items()}
    rp, pp = res[PRIMARY], port[PRIMARY]
    trades = pd.concat([r["trades"].assign(symbol=s) for s, r in rp.items() if len(r["trades"])],
                       ignore_index=True)
    x = pp["net_ret"].to_numpy()

    # ---- missing data (bar existence only)
    non_trad = []
    for s, d in data.items():
        ok, miss = tradable_sessions(d, CFG) if len(d) else (set(), [])
        ok, miss = {str(x) for x in ok}, dict(miss)
        for ss in sessions:
            if ss in ok:
                continue
            why = ("malformed data: " + "; ".join(defects[s][ss]) if ss in defects[s] else
                   "missing bars: " + " ".join(miss[ss]) if ss in miss else "no data")
            non_trad.append((s, ss, why))
    share_nt = len(non_trad) / (N_UNIVERSE * len(sessions))

    # ---- primary + secondary statistics
    prim = mean_inference(x, mean_block=None, b=B, seed=SEED_PRIMARY)       # automatic block length
    obs = float(x.mean())
    if len(trades):
        e = sign_flip_baseline(trades, len(sessions), N_UNIVERSE, K, B, SEED_BASELINES)
        cands, exits = zip(*[entry_candidates(data[s], r["trades"]) for s, r in rp.items() if len(r["trades"])])
        d = random_entry_baseline(np.vstack(cands), np.concatenate(exits), scen[PRIMARY],
                                  len(sessions), N_UNIVERSE, K, B, SEED_BASELINES)
        fam2 = {"E_random_direction": randomisation_p(obs, e), "D_random_entry": randomisation_p(obs, d)}
    else:                                                     # no ORB trade at all: baselines undefined
        e = d = np.array([np.nan])
        fam2 = {"E_random_direction": 1.0, "D_random_entry": 1.0}
    per = {}
    for s, r in rp.items():
        daily = pd.Series(0.0, index=sessions)
        if len(r["trades"]):
            g = r["trades"].groupby("session")["net_pnl"].sum() / K
            daily.loc[g.index] = g
        per[s] = mean_inference(daily.to_numpy(), mean_block=None, b=2000, seed=SEED_PRIMARY)["p_one_sided"]

    # ---- economic + descriptive
    sign = np.where(trades["side"] == "LONG", 1.0, -1.0)
    def mean_at(bps):
        c = CostModel(**{**scen[PRIMARY].describe(), "slippage_bps": bps})
        return trade_net_pnl(trades["entry_price"], trades["exit_price"], sign, c, K).sum() / (N_UNIVERSE * K * len(sessions))
    be = optimize.brentq(mean_at, 0.0, 500.0) if len(trades) and mean_at(0.0) > 0 > mean_at(500.0) else None
    long_only = portfolio_daily(strat(scen[PRIMARY], short=False), sessions, N_UNIVERSE, K)
    bench = portfolio_daily({s: run_open_to_close_benchmark(dd, scen[PRIMARY], CFG) for s, dd in data.items()},
                            sessions, N_UNIVERSE, K)
    cap10 = portfolio_daily(strat(scen[PRIMARY], EngineConfig(capital=K_SENS)), sessions, N_UNIVERSE, K_SENS)
    half = mean_inference(x, mean_block=max(1.0, prim["block_length"] / 2), b=B, seed=SEED_PRIMARY)
    double = mean_inference(x, mean_block=prim["block_length"] * 2, b=B, seed=SEED_PRIMARY)

    # ---- bhavcopy data-quality check (flags only) + its sensitivity
    flags, bhav_sha = [], {}
    for ss in sessions:
        try:
            bh = load_bhavcopy(ss)
        except Exception as ex:                                               # check unavailable -> flag, never block
            flags += [{"session": ss, "symbol": s, "check": "C0_UNAVAILABLE", "detail": repr(ex)[:120]} for s in syms]
            continue
        bhav_sha[ss] = sha(BASE_DIR / "data" / "raw" / "nse_bhavcopy" /
                           f"BhavCopy_NSE_CM_0_0_0_{ss.replace('-', '')}_F_0000.csv.zip")
        bars = {s: dd[dd["session"].astype(str) == ss] for s, dd in data.items()}
        flags += bhav_check(bars, bh, ss, syms)

    # ---- regimes: EXPLORATORY, official NSE close only, labels use data up to t-1
    try:
        closes, close_sha = official_closes(sessions)
        lab = regime_labels(closes)
        lab.index = lab.index.strftime("%Y-%m-%d")
        lab = lab.reindex(sessions)
        regimes = {}
        for col in ("vol_regime", "trend_regime"):
            for k, g in pp["net_ret"].groupby(lab[col].fillna("UNLABELLED")):
                regimes[f"{col}={k}"] = {"n": int(len(g)), "mean_bps": bps(g.mean()),
                                         "se_bps": bps(g.std(ddof=1) / np.sqrt(len(g))) if len(g) > 1 else None}
    except Exception as ex:                                                   # no substitute source
        regimes, close_sha = f"NOT RUN - official NSE close unavailable: {repr(ex)[:120]}", {}

    summary = {
        "mode": "DRY RUN on pre-holdout development data - NOT the holdout evaluation" if dry
                else "PROSPECTIVE HOLDOUT EVALUATION (single, pre-registered)",
        "protocol_file": PROTOCOL_FILE, "protocol_sha256": hashlib.sha256(proto_text.encode()).hexdigest(),
        "sessions": {"n": len(sessions), "first": sessions[0], "last": sessions[-1]},
        "primary": {"label": verdict(prim), "mean_bps": bps(prim["mean"]), "se_bps": bps(prim["se_bootstrap"]),
                    "t_bootstrap": prim["t_bootstrap"], "p_one_sided": prim["p_one_sided"],
                    "lower_1s_95_bps": bps(prim["lower_1s_95"]), "upper_1s_95_bps": bps(prim["upper_1s_95"]),
                    "ci95_two_sided_bps": [bps(v) for v in prim["ci95_two_sided"]], "sd_bps": bps(prim["sd"]),
                    "sharpe_annual": prim["sharpe_annual"], "block_length": prim["block_length"],
                    "n": prim["n"], "B": B, "seed": SEED_PRIMARY, "method": prim["method"]},
        "data_limited": share_nt > DATA_LIMITED_SHARE,
        "non_tradable": {"stock_sessions": len(non_trad), "share": round(share_nt, 4),
                         "of_which_malformed": sum(r[2].startswith("malformed") for r in non_trad),
                         "unparseable_timestamp_rows_by_stock": {k: v for k, v in unparseable.items() if v}},
        "usable_stock_sessions": N_UNIVERSE * len(sessions) - len(non_trad),
        "family2_random_baselines": {"raw": fam2, "holm": holm(fam2),
                                     "draw_means_bps": {"E": bps(e.mean()), "D": bps(d.mean())}},
        "family3_per_stock_exploratory": {"raw_lt_0.05": sum(p < .05 for p in per.values()),
                                          "holm_lt_0.05": sum(p < .05 for p in holm(per).values())},
        "economic": {"gross_mean_bps": bps(pp["gross_ret"].mean()), "net_mean_bps": bps(obs),
                     "break_even_slippage_bps_per_side": be,
                     "cost_components_rs": {k: round(float(pp[k].sum()), 2) for k in
                                            ["brokerage", "stt", "exchange", "sebi", "stamp", "gst", "slippage"]}},
        "deflated_sharpe_reporting_only": deflated_sharpe(x, orb_trial_count()),
        "sensitivity": {"cost_grid_net_bps": {k: bps(v["net_ret"].mean()) for k, v in port.items()},
                        "capital_10_lakh_net_bps": bps(cap10["net_ret"].mean()),
                        "block_half_p": half["p_one_sided"], "block_double_p": double["p_one_sided"]},
        "context": {"long_only_B_net_bps": bps(long_only["net_ret"].mean()),
                    "open_to_close_A_net_bps": bps(bench["net_ret"].mean())},
        "trades": {"n": len(trades), "long": int((trades.side == "LONG").sum()),
                   "short": int((trades.side == "SHORT").sum())},
        "bhavcopy_flags_data_quality_only": {"n": len(flags),
                                             "by_check": pd.Series([f["check"] for f in flags]).value_counts().to_dict()},
        "regimes_exploratory": regimes,
    }

    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    out = BASE_DIR / "results" / ("orb_v1_dryrun" if dry else "orb_v1_holdout") / stamp
    out.mkdir(parents=True, exist_ok=False)                                   # never overwrite
    files = {"summary.json": json.dumps(summary, indent=2, default=str),
             "portfolio_daily.csv": pp.to_csv(), "trades.csv": trades.to_csv(index=False),
             "non_tradable.csv": pd.DataFrame(non_trad, columns=["symbol", "session", "reason"]).to_csv(index=False),
             "bhavcopy_flags.csv": pd.DataFrame(flags, columns=["session", "symbol", "check", "detail"]).to_csv(index=False)}
    for name, text in files.items():
        (out / name).write_text(text)
    manifest = {
        "created": stamp, "mode": summary["mode"], "git_commit": git("rev-parse", "HEAD"),
        "git_dirty": bool(git("status", "--porcelain", "--", "src", "*.py", "config", "docs/protocols", "docs/evidence")),
        "environment": environment(), "protocol_sha256": summary["protocol_sha256"],
        "inputs": {"universe": sha(UNIVERSE_FILE), "cost_scenarios": sha(BASE_DIR / "config" / "cost_scenarios.json"),
                   **{f"cost_schedule/{p.name}": sha(p) for p in (BASE_DIR / "config" / "cost_schedules").glob("*.json")},
                   **{f"calendar/{p.name}": sha(p) for p in CAL_DIR.glob("*.json")},
                   **{f"data/{k}": v for k, v in data_sha.items()},
                   **{f"bhavcopy/{k}": v for k, v in bhav_sha.items()},
                   "nse_index_history": sha(BASE_DIR / "docs" / "evidence" / "nse_index" / "nifty50_official_close_2026.csv"),
                   **{f"nse_index/{k}": v for k, v in close_sha.items()}},
        "outputs": {n: hashlib.sha256((out / n).read_bytes()).hexdigest() for n in files},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    for p in out.iterdir():
        p.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)                    # read-only artifacts

    rec = record({
        "research_question": "ORB v1 primary question (see protocol)", "hypothesis": "mu > 0",
        "null_hypothesis": "mu <= 0", "strategy": "ORB 30m on 15m bars, long/short, exit 15:00 bar OPEN (X2)",
        "instrument": "frozen NIFTY 50", "universe": "NIFTY50-frozen-20261001", "timeframe": "m15",
        "start": sessions[0], "end": sessions[-1], "dataset_id": "data/india/<SYMBOL>m15.csv x50",
        "dataset_sha256": f"see {out.relative_to(BASE_DIR)}/manifest.json",
        "dataset_stage": "development (dry run)" if dry else "prospective holdout",
        "feature_set": "OHLC 15m", "parameters": {"range": 30, "cutoff": "14:30", "exit": "15:00 open", "K": K},
        "training_period": "none", "validation_period": "none",
        "test_period": f"{sessions[0]}..{sessions[-1]}",
        "oos_status": "development, dry run of locked pipeline" if dry else "prospective holdout, evaluated once",
        "cost_model": "cost_scenarios.json (primary Z-5)", "slippage": "5 bps/side primary",
        "benchmark": "A open-to-close (context); baselines D, E", "cash_treatment": "0%",
        "dividends": "n/a", "random_seed": f"{SEED_PRIMARY}/{SEED_BASELINES}",
        "results": {"headline": f"{summary['primary']['label']}: mean {summary['primary']['mean_bps']} bps/day, "
                                f"p={summary['primary']['p_one_sided']:.4f}", "artifacts": str(out.relative_to(BASE_DIR))},
        "statistical_tests": "null-centred stationary bootstrap (PW auto block); E, D Holm; per-stock Holm; DSR reporting",
        "limitations": "see protocol",
        "viewed_before_finalization": "dry run on development data" if dry else "no",
        "status": "DIAGNOSTIC" if dry else "FINAL"}, prefix="ORBV1")
    log_trial("orb_v1_evaluation", {"mode": mode}, f"{sessions[0]}..{sessions[-1]}",
              {"label": summary["primary"]["label"], "mean_bps": summary["primary"]["mean_bps"]}, "evaluate_orb_v1.py")
    print(json.dumps(summary, indent=2, default=str))
    print(f"\nartifacts (read-only): {out}\nexperiment: {rec['experiment_id']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="ORB v1 locked evaluation (no tuning options)")
    ap.add_argument("--dry-run-dev", action="store_true", help="run on pre-holdout development data")
    run("dry-run-dev" if ap.parse_args().dry_run_dev else "holdout")

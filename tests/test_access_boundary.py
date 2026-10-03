"""Phase 1 access boundary (src/access.py). SYNTHETIC / TEMP DATA ONLY - no test
here reads real holdout rows or calls the real holdout evaluation path."""

import ast
import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd
import pytest

import src.access as access
from src.config import BASE_DIR

ROOT = Path(BASE_DIR)
GRID = [f"{h:02d}:{m:02d}" for h in range(9, 16) for m in (0, 15, 30, 45)
        if "09:15" <= f"{h:02d}:{m:02d}" <= "15:15"]


# ------------------------------------------------------------ helpers

def _git(repo, *a):
    subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)


def _repo(tmp_path, status="FROZEN"):
    proto_dir = tmp_path / "docs" / "protocols"
    proto_dir.mkdir(parents=True)
    proto = proto_dir / "ORB_v1.md"
    proto.write_text(f"# ORB v1\n\n**Status:** {status}\n")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "protocol")
    return proto


def _auth(proto, sha=None, commit=True, **over):
    f = {"protocol_sha256": sha or hashlib.sha256(proto.read_bytes()).hexdigest(),
         "sessions": "250", "authorized_by": "Test Person", "date": "2027-10-10", **over}
    a = proto.parent / access.AUTH_NAME
    a.write_text(access.AUTH_LINE + "\n" + "".join(f"{k}: {v}\n" for k, v in f.items()))
    if commit:
        _git(proto.parent, "add", str(a))
        _git(proto.parent, "commit", "-qm", "authorize")
    return a


def bars(*days):
    rows = [(pd.Timestamp(f"{d} {t}"), 100.0, 101.0, 99.0, 100.0, 10) for d in days for t in GRID]
    return pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume"])


# ------------------------------------------------- authorization gate

def test_frozen_without_artifact_is_locked(tmp_path):
    with pytest.raises(access.HoldoutLocked, match="no authorization artifact"):
        access.holdout_authorized(_repo(tmp_path))


def test_draft_protocol_is_locked_even_with_artifact(tmp_path):
    proto = _repo(tmp_path, status="DRAFT")
    _auth(proto)
    with pytest.raises(access.HoldoutLocked, match="not FROZEN"):
        access.holdout_authorized(proto)


def test_wrong_protocol_hash_is_locked(tmp_path):
    proto = _repo(tmp_path)
    _auth(proto, sha="0" * 64)
    with pytest.raises(access.HoldoutLocked, match="does not match"):
        access.holdout_authorized(proto)


def test_untracked_artifact_is_locked(tmp_path):
    proto = _repo(tmp_path)
    _auth(proto, commit=False)
    with pytest.raises(access.HoldoutLocked, match="not committed"):
        access.holdout_authorized(proto)


def test_modified_artifact_is_locked(tmp_path):
    proto = _repo(tmp_path)
    a = _auth(proto)
    a.write_text(a.read_text() + "note: edited\n")
    with pytest.raises(access.HoldoutLocked, match="uncommitted modifications"):
        access.holdout_authorized(proto)


def test_protocol_edited_after_authorization_is_locked(tmp_path):
    proto = _repo(tmp_path)
    _auth(proto)
    proto.write_text(proto.read_text() + "changed\n")
    with pytest.raises(access.HoldoutLocked, match="does not match"):
        access.holdout_authorized(proto)


@pytest.mark.parametrize("over", [{"sessions": "200"}, {"authorized_by": ""}])
def test_incomplete_artifact_is_locked(tmp_path, over):
    proto = _repo(tmp_path)
    _auth(proto, **over)
    with pytest.raises(access.HoldoutLocked):
        access.holdout_authorized(proto)


def test_valid_artifact_authorizes(tmp_path):
    proto = _repo(tmp_path)
    _auth(proto)
    assert access.holdout_authorized(proto)["authorized_by"] == "Test Person"


def test_load_intraday_holdout_branch_requires_authorization(tmp_path, monkeypatch):
    import src.intraday.data as d
    proto = _repo(tmp_path)
    monkeypatch.setattr(d, "load_csv", lambda f, sort=True, coerce=False: bars("2026-09-30", "2026-10-01"))
    monkeypatch.setattr("src.config.BASE_DIR", tmp_path)
    rel = "docs/protocols/ORB_v1.md"
    assert d.load_intraday("XYZm15.csv")[0]["date"].max() < pd.Timestamp("2026-10-01")
    with pytest.raises(access.HoldoutLocked):
        d.load_intraday("XYZm15.csv", holdout_protocol=rel)          # FROZEN alone: refused
    _auth(proto)
    assert d.load_intraday("XYZm15.csv", holdout_protocol=rel)[0]["date"].max() >= pd.Timestamp("2026-10-01")


def test_single_use_guard(tmp_path):
    res, exp = tmp_path / "results", tmp_path / "experiments.jsonl"
    exp.write_text(json.dumps({"experiment_id": "A", "strategy": access.ORB_V1_STRATEGY,
                               "status": "DIAGNOSTIC"}) + "\n")
    access.final_evaluation_unused(res, exp)                          # clean: allowed
    res.mkdir()
    access.final_evaluation_unused(res, exp)                          # empty dir: allowed
    (res / "20271010T000000").mkdir()
    with pytest.raises(access.HoldoutLocked, match="already contains"):
        access.final_evaluation_unused(res, exp)
    exp.write_text(exp.read_text() + json.dumps({"experiment_id": "B", "strategy": access.ORB_V1_STRATEGY,
                                                 "status": "FINAL"}) + "\n")
    with pytest.raises(access.HoldoutLocked, match="FINAL"):
        access.final_evaluation_unused(tmp_path / "none", exp)
    exp.write_text(json.dumps({"experiment_id": "A", "strategy": access.ORB_V1_STRATEGY, "status": "DIAGNOSTIC"})
                   + "\n" + json.dumps({"amends": "A", "status": "FINAL"}) + "\n")
    with pytest.raises(access.HoldoutLocked, match="FINAL"):
        access.final_evaluation_unused(tmp_path / "none", exp)


def test_evaluator_refuses_frozen_protocol_without_authorization(tmp_path, monkeypatch):
    """Points the evaluator at a TEMP frozen protocol; refusal happens before any data load."""
    import evaluate_orb_v1 as ev
    proto = _repo(tmp_path)
    monkeypatch.setattr(ev, "PROTOCOL_FILE", str(proto))
    monkeypatch.setattr(ev, "git", lambda *a: "")                    # treat tree as clean
    with pytest.raises(SystemExit, match="authorization"):
        ev.run("holdout")


# ------------------------------------------------ collector unaffected

def test_collector_still_merges_into_files_with_holdout_rows():
    from src.intraday.pipeline import merge_bars
    old = bars("2026-09-30", "2026-10-01")
    new = bars("2026-10-01", "2026-10-05")
    merged, rep = merge_bars(old, new, 15, "XYZ", now=pd.Timestamp("2026-10-05 20:00"))
    assert rep["added"] == len(GRID) and rep["overlap_checked"] == len(GRID)
    assert merged["date"].max() == pd.Timestamp("2026-10-05 15:15")
    pd.testing.assert_frame_equal(merged.iloc[:len(old)].reset_index(drop=True), old)


def test_collector_and_status_do_not_route_through_research_loaders():
    for f in ("update_intraday.py", "src/intraday/pipeline.py"):
        assert "src.access" not in (ROOT / f).read_text()


# ------------------------------------------------------ dashboard cutoff

@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    import server
    import src.data_loader as dl
    india = tmp_path / "india"
    india.mkdir()
    days = pd.bdate_range("2026-06-01", "2026-10-09")
    d1 = pd.DataFrame({"Date": days.strftime("%Y-%m-%d"), "open": 100.0, "high": 101.0, "low": 99.0,
                       "close": [100.0 + i for i in range(len(days))], "tick_volume": 1})
    d1.loc[d1["Date"] >= "2026-10-01", "close"] = 999999.0           # poison: must never surface
    d1.loc[d1["Date"] >= "2026-10-01", "high"] = 999999.0
    d1.to_csv(india / "XYZd1.csv", index=False)
    m = bars(*pd.bdate_range("2026-09-08", "2026-10-02").strftime("%Y-%m-%d"))
    m.loc[m["date"] >= "2026-10-01", ["open", "high", "close"]] = 999999.0
    m.rename(columns={"volume": "tick_volume"}).assign(
        Date=lambda x: x["date"].dt.strftime("%Y-%m-%d %H:%M"))[
        ["Date", "open", "high", "low", "close", "tick_volume"]].to_csv(india / "XYZm15.csv", index=False)
    monkeypatch.setattr(dl, "DATA_DIR", tmp_path)
    monkeypatch.setattr(server, "DATA_DIR", tmp_path)
    return india


@pytest.fixture
def client(data_dir):
    from fastapi.testclient import TestClient
    import server
    return TestClient(server.app)


def test_watchlist_never_shows_october(client):
    row = [r for r in client.get("/api/watchlist").json() if r["symbol"] == "XYZ"][0]
    assert row["price"] < 999999 and row["price"] == 100.0 + len(pd.bdate_range("2026-06-01", "2026-09-30")) - 1


def test_backtest_never_uses_october(client, tmp_board):
    r = client.get("/api/backtest", params={"file": "XYZd1.csv", "kind": "ema", "fast": 2, "slow": 5}).json()
    assert r["end"] <= "2026-09-30" and max(r["dates"]) <= "2026-09-30"
    assert all(t["entry_date"] <= "2026-09-30" for t in r["trades"])


def test_add_never_saves_post_cutoff_data(client, data_dir, monkeypatch):
    import yfinance
    idx = pd.bdate_range("2026-09-24", "2026-10-07")

    class T:
        def __init__(self, s): pass
        def history(self, **k):
            return pd.DataFrame({"Open": 1.0, "High": 1.0, "Low": 1.0, "Close": 1.0, "Volume": 5}, index=idx)
    monkeypatch.setattr(yfinance, "Ticker", T)
    assert client.get("/api/add", params={"symbol": "ABC.NS"}).json()["ok"]
    saved = pd.read_csv(data_dir / "ABCd1.csv")
    assert saved["Date"].max() == "2026-09-30"


def test_intraday_endpoints_never_expose_october(client):
    files = {f["file"]: f for f in client.get("/api/intraday/files").json()}
    assert files["XYZm15.csv"]["end"] < "2026-10-01"
    resp = client.get("/api/intraday/run", params={"file": "XYZm15.csv", "gross": True})
    assert resp.status_code == 200, resp.text
    r = resp.json()
    assert max(r["curve"]["dates"]) <= "2026-09-30"
    assert all(str(t["exit_time"]) < "2026-10-01" for t in r["trade_list"])


def test_research_loaders_cut_at_cutoff(data_dir):
    df = access.research_load_csv("XYZd1.csv")
    assert df["date"].max() == pd.Timestamp("2026-09-30") and df["close"].max() < 999999


# -------------------------------------- research-tier static code scan

RAW_ACCESS_ALLOWED = {
    "src/data_loader.py": "primitive loader (tier W/O)",
    "src/datasets.py": "load_clean primitive + exclusions file",
    "src/access.py": "the boundary itself",
    "src/intraday/data.py": "load_intraday: cut by default, holdout only via access gate",
    "update_intraday.py": "collector (tier W)",
    "src/intraday/pipeline.py": "collector (tier W)",
    "scripts/holdout_status.py": "operational status (tier O, fixed fields)",
    "src/registry/data_registry.py": "registry checksums/validation (tier O)",
    "src/leaderboard.py": "reads results/leaderboard.csv, not market data",
    "src/intraday/bhavcopy_check.py": "NSE bhavcopy data-quality flags (tier O)",
    "src/intraday/regimes.py": "stored pre-cutoff official index closes (evidence)",
    "scripts/orb_v1_power.py": "reads pre-holdout development results",
    "scripts/verify_exit_bar_semantics.py": "filters Date < HOLDOUT_START itself",
}
FORBIDDEN_CALLS = {"load_csv", "read_csv", "load_clean"}


def _py_files():
    for p in sorted(ROOT.rglob("*.py")):
        rel = p.relative_to(ROOT).as_posix()
        if not rel.startswith(("tests/", ".", "__pycache__")) and "/." not in rel:
            yield rel, ast.parse(p.read_text())


def test_research_tier_cannot_read_market_data_directly():
    bad = []
    for rel, tree in _py_files():
        if rel in RAW_ACCESS_ALLOWED:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                name = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
                if name in FORBIDDEN_CALLS:
                    bad.append(f"{rel}:{n.lineno} {name}()")
    assert not bad, "research-tier raw data access (use src.access.research_*): " + ", ".join(bad)


def test_only_the_evaluator_requests_holdout_rows():
    users = [rel for rel, tree in _py_files() for n in ast.walk(tree)
             if isinstance(n, ast.keyword) and n.arg == "holdout_protocol"]
    assert set(users) == {"evaluate_orb_v1.py"}
    for rel, tree in _py_files():
        if rel in ("evaluate_orb_v1.py", "src/access.py"):
            continue
        consts = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        assert not any(("orb_v1_holdout" in c or "holdout_mirror" in c) for c in consts), rel


# -------------------------------------------------- operational status

STATUS_IMPORTS_ALLOWED = {
    "json": None, "collections": {"Counter"}, "pandas": None, "src.config": {"BASE_DIR", "HOLDOUT_START"},
    "src.data_loader": {"load_csv"}, "src.intraday.calendar": {"CAL_DIR", "standard_sessions"},
    "src.intraday.data": {"split_defective"}, "src.intraday.engine": {"EngineConfig", "tradable_sessions"},
    "src.intraday.portfolio": {"frozen_universe"},
}


def test_status_imports_no_outcome_code():
    tree = ast.parse((ROOT / "scripts/holdout_status.py").read_text())
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            assert all(a.name in STATUS_IMPORTS_ALLOWED for a in n.names)
        if isinstance(n, ast.ImportFrom):
            allowed = STATUS_IMPORTS_ALLOWED.get(n.module, set())
            assert allowed is not None and {a.name for a in n.names} <= allowed, n.module


def test_status_fields_fixed_and_ready_logic(tmp_path, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location("hs", ROOT / "scripts/holdout_status.py")
    hs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hs)
    proto = tmp_path / "p.md"
    proto.write_text("**Status:** FROZEN")
    log = tmp_path / "log.jsonl"
    log.write_text(json.dumps({"run_id": "r", "at": "2026-10-02T18:30", "summary": True,
                               "failed_or_rejected": 0, "dry_run": False}) + "\n")
    data = bars("2026-10-01", "2026-10-05")
    monkeypatch.setattr(hs, "PROTOCOL", proto)
    monkeypatch.setattr(hs, "LOG", log)
    monkeypatch.setattr(hs, "frozen_universe", lambda: ["AAA", "BBB"])
    monkeypatch.setattr(hs, "load_csv", lambda f, **k: data if f.startswith("AAA") else data.iloc[:-3])
    monkeypatch.setattr(hs, "_known_sessions", lambda: ["2026-10-01", "2026-10-05"])
    monkeypatch.setattr(hs, "N", 2)
    s = hs.build_status(now="2026-10-06 09:00")
    assert tuple(s) == hs.STATUS_FIELDS
    banned = ("return", "pnl", "sharpe", "p_value", "signal", "trade", "profit")
    assert not any(b in k.lower() for k in s for b in banned)
    assert s["sessions_collected"] == 2 and s["ready_for_final_evaluation"] == "READY FOR EXPLICIT FINAL EVALUATION"
    assert s["untradable_by_reason"] == {"missing bars": 1} and s["performance_computed"] is False
    monkeypatch.setattr(hs, "load_csv", lambda f, **k: bars("2026-10-01"))
    s = hs.build_status(now="2026-10-06 09:00")
    assert s["stale"] and s["data_health"] == "STALE" and s["ready_for_final_evaluation"] == "NOT READY"


# ---------------------------------------------- frozen methodology hashes

FROZEN_SHA256 = {   # values at freeze (d655644 / status-line annotation 6a57a7e); NEVER update
    "docs/protocols/ORB_v1.md": "9c9cc1fc20c18df557bce7cbcda917a236d75077ccbcc6e28b8a3f8172121c78",
    "src/intraday/orb.py": "708c4394f21e2744939809b6272334aa1c87ff12a155739356845be7d6fee7d5",
    "src/intraday/engine.py": "7367f97ee2200db37a7f0f432e0443c3d50724f06fb264389d897b55aabfa2a8",
    "src/intraday/inference.py": "002c0745ab6aa62f6401dab758f51512c104a16b66142dc479a6993d9e751852",
    "src/intraday/portfolio.py": "2735f8794ceb77af9122fb2cf02d13e8f74770bba28436ff60f9a3b5976df970",
    "src/intraday/calendar.py": "7e547e25fb2b3520fb39eb47cd009fc334b7f28a163c065b329dc1fea55aed42",
    "src/intraday/regimes.py": "71a8dfe2296a5707c8bfab97da7cc40969a82f2aac34a7b25447649958ae63b1",
    "src/intraday/bhavcopy_check.py": "0d90ec56689af0fd4169b85702e80e7be96ae56f15f2085260229a6c67c0ccdc",
    "src/intraday/costs.py": "b73e0f471ccc03810426946279d9a4b80ca45e3d7b7a19047a917470c0e6a0f7",
    "data/metadata/universe/NIFTY50_frozen_20261001.json": "56d4bc8b85d044ebe9488a30708067ed416ded1a8dc18fbbc6d9da0a7a09d43a",
    "config/cost_scenarios.json": "88bca51d0ce53cca86421661ac29ab56277380ee983cc73378b37b392d8379e6",
    "config/cost_schedules/zerodha_nse_eq_intraday_20260930.json": "64222d2f39e1501c06361e79cbd3ffdad23bf7f6f54f16e62606486d51afe842",
    "config/cost_schedules/upstox_nse_eq_intraday_20260930.json": "3a441ccadeaf6ee62e3594a4b4d36076378fadf0d895b27635d9a4e423fddf10",
    "docs/evidence/nse_calendar/nse_cm_trading_holidays_2026.json": "a96c0d9874e5ec4de882ad407e4775acfeb5b7fb747f3586638dd8908c236945",
    "docs/evidence/nse_index/nifty50_official_close_2026.csv": "5051c4f060665d93f433ccfcfb1097aef4dae888f11c886c5a83ab77d7253528",
}


@pytest.mark.parametrize("path", sorted(FROZEN_SHA256))
def test_frozen_orb_methodology_unchanged(path):
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == FROZEN_SHA256[path], \
        f"{path} differs from its frozen ORB v1 version - changes require ORB_v2"

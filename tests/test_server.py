"""API: running a backtest must never write the leaderboard; saving must."""

from fastapi.testclient import TestClient

import server

client = TestClient(server.app)
Q = {"file": "NIFTY_10Y.csv", "kind": "ema", "fast": 20, "slow": 50}


def test_backtest_is_read_only(tmp_board):
    r = client.get("/api/backtest", params=Q)
    assert r.status_code == 200
    assert r.json()["metrics"]["return_pct"] == 184.8
    assert not tmp_board.exists()


def test_explicit_save_writes_once(tmp_board):
    for _ in range(2):
        assert client.post("/api/leaderboard/save", params=Q).json()["ok"]
    rows = client.get("/api/leaderboard").json()
    assert [r["name"] for r in rows] == ["EMA 20/50 · NIFTY_10Y"]


def test_bad_requests_are_400(tmp_board):
    assert client.get("/api/backtest", params={**Q, "fast": 60}).status_code == 400
    assert client.get("/api/backtest", params={**Q, "file": "../server.py"}).status_code == 400
    assert client.get("/api/backtest", params={**Q, "file": "NOPE.csv"}).status_code == 400


def test_intraday_files_report_quality():
    rows = client.get("/api/intraday/files").json()
    names = {r["file"] for r in rows}
    assert "RELIANCEm15.csv" in names and "RELIANCEh1.csv" in names
    assert all("warnings" in r for r in rows)


def test_intraday_run_requires_cost_schedule_unless_gross(monkeypatch, tmp_path):
    from src.intraday import costs
    monkeypatch.setattr(costs, "COST_FILE", tmp_path / "missing.json")
    assert client.get("/api/intraday/run", params={"file": "RELIANCEm15.csv"}).status_code == 409
    r = client.get("/api/intraday/run", params={"file": "RELIANCEm15.csv", "gross": True})
    assert r.status_code == 200
    d = r.json()
    assert "GROSS" in d["costs"]["name"] and d["limitations"]
    assert len(d["curve"]["dates"]) == len(d["curve"]["bench"]) == d["summary"]["sessions"]

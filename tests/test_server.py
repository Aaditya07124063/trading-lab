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

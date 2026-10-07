"""Read-only endpoints added for the web UI: /api/prices and /api/research."""

import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

import server
from src import research_view

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(server.app)


def test_prices_are_real_bars_cut_at_the_research_cutoff():
    r = client.get("/api/prices", params={"file": "NIFTY50d1.csv", "n": 30}).json()
    assert len(r["dates"]) == len(r["close"]) == 30 and r["dates"] == sorted(r["dates"])
    assert max(r["dates"]) <= r["cutoff"] == server.RESEARCH_CUTOFF
    assert all(lo <= c <= hi for lo, c, hi in zip(r["low"], r["close"], r["high"]))
    for bad in ("../server.py", "NOPE.csv"):
        assert client.get("/api/prices", params={"file": bad}).status_code == 400


def test_research_view_is_read_only_and_reports_registered_facts():
    watched = [ROOT / "registry" / "experiments.jsonl", ROOT / "registry" / "trials.jsonl", ROOT / "EXPERIMENT_REGISTRY.md",
               *sorted((ROOT / "results" / "s2_mom_v1").iterdir()), *sorted((ROOT / "results" / "s2_mom_v1_step_e").iterdir())]
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in watched}
    r = client.get("/api/research").json()
    assert before == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in watched}       # nothing written
    s = r["s2_mom"]
    assert all(run["registered"] and run["verified"] for run in s["runs"].values()) and len(s["runs"]) == 5
    assert all(d["verified"] for d in s["documents"]) and len(s["documents"]) == 6          # protocol, addendum, 4 supplements
    assert s["primary"]["H1"]["n"] == 114 and s["confirmation"]["H1"]["n"] == 56
    assert s["step_e"]["samples"]["confirmation"]["H4"]["status"].startswith("NOT RUN")
    assert r["orb"]["protocol_status"] == "FROZEN" and r["orb"]["final_evaluation_registered"] is False
    assert r["research_cutoff"] == server.RESEARCH_CUTOFF and len(r["experiments"]) >= 21


def test_research_view_flags_a_changed_file(tmp_path, monkeypatch):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "f.json").write_text("changed")
    monkeypatch.setattr(research_view, "BASE_DIR", tmp_path)
    assert research_view._verify("a", {"f.json": "0" * 64}) == {"registered": True, "files": 1, "verified": False, "mismatch": ["f.json"]}
    assert research_view._verify("a", {}) == {"registered": False, "files": 0, "verified": False, "mismatch": []}


def test_ui_code_cannot_run_or_write_research():
    src = (ROOT / "src" / "research_view.py").read_text().split('"""', 2)[2]
    for banned in ("write_text", "write_bytes", "to_csv", "amend(", "record(", "log_trial", "read_csv", "open(", "stage3", "intraday"):
        assert banned not in src, banned
    demo = (ROOT / "web" / "mock" / "news.json").read_text()
    assert '"_notice": "DEMO DATA' in demo and "Demo Wire" in demo                          # demo news says it is demo

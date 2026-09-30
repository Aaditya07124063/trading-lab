from src import leaderboard
from src.research import experiment_name


def row(name, margin):
    return {"name": name, "return_pct": 1, "bh_pct": 1, "margin": margin, "verdict": "x"}


def test_upsert_by_name_no_duplicates(tmp_board):
    leaderboard.save([row("A", 1), row("B", 5)])
    b = leaderboard.save([row("A", 9)])
    assert b["name"].tolist() == ["A", "B"]           # sorted by margin, A updated
    assert b.loc[b.name == "A", "margin"].item() == 9
    assert list(b.columns) == leaderboard.COLUMNS


def test_names_encode_every_parameter():
    assert experiment_name("X.csv", "ema", 20, 50) != experiment_name("X.csv", "ema", 20, 50, trailing_stop=0.1)
    assert experiment_name("X.csv", "ema", 20, 50) != experiment_name("X.csv", "ema", 20, 50, stop_loss=0.1)
    assert experiment_name("X.csv", "ema", 20, 50) == "EMA 20/50 · X"


def test_registry_rejects_incomplete_and_duplicate_records(tmp_path, monkeypatch):
    import pytest
    from src.registry import experiments as reg
    monkeypatch.setattr(reg, "EXPERIMENTS", tmp_path / "e.jsonl")
    with pytest.raises(ValueError, match="missing"):
        reg.record({"strategy": "x"})
    full = {k: "n/a" for k in reg.REQUIRED} | {"status": "EXPLORATORY", "experiment_id": "EXP-T-001"}
    reg.record(full, env={"git_commit": "abc"})
    with pytest.raises(ValueError, match="already registered"):
        reg.record(full, env={"git_commit": "abc"})
    reg.amend("EXP-T-001", "data issue found", status="REQUIRES REVALIDATION")
    cur = reg.current()["EXP-T-001"]
    assert cur["status"] == "REQUIRES REVALIDATION" and cur["history"][0]["status"] == "EXPLORATORY"
    assert len((tmp_path / "e.jsonl").read_text().splitlines()) == 2      # append-only

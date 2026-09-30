"""Paper bot: an order signalled at day T fills at T+1's open - never later,
even if the bot skipped days."""

import pandas as pd
import pytest

import paper_bot as pb
from src.config import COST_PER_SIDE


def hist(closes, start="2025-01-01"):
    idx = pd.bdate_range(start, periods=len(closes))
    return pd.DataFrame({"Open": [c - 0.5 for c in closes], "Close": closes}, index=idx)


def rising(n=80):
    return [100.0 + i for i in range(n)]      # ema20 > ema50 -> BUY signal


def test_skipped_days_still_fill_at_t_plus_1_open():
    h = hist(rising())
    state = pb.new_state(["X"])
    state["last_candle"] = str(h.index[60].date())
    state["pending"]["X"] = {"action": "BUY", "signal_date": str(h.index[60].date())}
    rows = pb.step(state, {"X": h})                     # bot was off for days 61..79
    buy = [r for r in rows if r["action"] == "BUY"]
    assert len(buy) == 1
    assert buy[0]["date"] == str(h.index[61].date())
    assert buy[0]["price"] == h["Open"].iloc[61]
    assert state["accounts"]["X"]["units"] == pytest.approx(
        pb.START_CASH_EACH * (1 - COST_PER_SIDE) / h["Open"].iloc[61])
    assert state["last_candle"] == str(h.index[-1].date())


def test_legacy_string_pending_is_migrated(tmp_path, monkeypatch):
    f = tmp_path / "s.json"
    f.write_text('{"accounts": {}, "pending": {"X": "BUY"}, "last_candle": "2025-03-03"}')
    monkeypatch.setattr(pb, "STATE_FILE", f)
    assert pb.load_state()["pending"]["X"] == {"action": "BUY", "signal_date": "2025-03-03"}


def test_order_whose_signal_day_is_not_in_data_expires_instead_of_filling_late():
    """A holiday and a missing bar look identical, so the next bar in the data
    after T counts as T+1. But if T itself is absent (history fetched too
    short), we cannot prove the fill day is T+1 -> expire, don't guess."""
    h = hist(rising())
    state = pb.new_state(["X"])
    state["last_candle"] = str(h.index[60].date())
    state["pending"]["X"] = {"action": "BUY", "signal_date": str(h.index[60].date())}
    rows = pb.step(state, {"X": h.iloc[61:].copy()})
    assert rows[0]["action"] == "EXPIRED"
    buys = [r for r in rows if r["action"] == "BUY"]
    assert buys[0]["date"] == str(h.index[63].date())   # fresh signal on 62 -> fill 63


def test_decision_uses_only_closes_up_to_today():
    h = hist(rising())
    crash = h.copy()
    crash.iloc[72:, :] = 1.0                           # future collapse after day 71
    rows = {}
    for label, data in (("normal", h), ("crash", crash)):
        state = pb.new_state(["X"])
        state["last_candle"] = str(h.index[60].date())
        rows[label] = [r for r in pb.step(state, {"X": data})
                       if r["date"] <= str(h.index[71].date())]
    assert rows["normal"] == rows["crash"]


def test_no_new_candle_means_no_rows():
    h = hist(rising())
    state = pb.new_state(["X"])
    state["last_candle"] = str(h.index[-1].date())
    assert pb.step(state, {"X": h}) == []

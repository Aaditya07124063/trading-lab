"""ORB v1 exit rule "X2" (approved 2026-10-01): square off at the OPEN of the
15:00 IST bar. Each test names the rule it protects and must FAIL if that rule
is broken. Synthetic data only."""

import pandas as pd
import pytest

from src.intraday.costs import CostModel
from src.intraday.engine import EngineConfig, run_intraday, run_open_to_close_benchmark
from src.intraday.orb import ORB
from tests.test_intraday import GRID, RANGE, ZERO, day, frame

CFG = EngineConfig(capital=100_000)
SIGNAL = {**RANGE, "09:45": (100, 102, 100, 101.5), "10:00": (101, 101, 101, 101)}
# a 15:00 bar whose OPEN differs from its high/low/close, and a 15:15 "auction" bar
EXIT_BARS = {"15:00": (104, 109, 96, 107), "15:15": (120, 121, 119, 120.5)}


def run(df, cfg=CFG, costs=ZERO):
    return run_intraday(df, ORB(30, 15), costs, cfg)


def test_default_config_is_x2():
    c = EngineConfig()
    assert (c.square_off, c.square_off_price) == ("15:00", "open")
    assert c.sizing == "fixed_notional" and c.require_complete_session


def test_exit_is_1500_open_not_1515_close():
    """REGRESSION GUARD: fails if the exit drifts back to the 15:15 bar close
    (or to any other price of the 15:00/15:15 bars)."""
    t = run(frame(day("2026-01-05", {**SIGNAL, **EXIT_BARS})))["trades"]
    assert len(t) == 1
    assert t.exit_time[0] == "2026-01-05 15:00:00"
    assert t.exit_price[0] == 104                      # 15:00 OPEN
    assert t.exit_price[0] not in (109, 96, 107, 120, 121, 119, 120.5)
    assert t.gross_pnl[0] == pytest.approx(t.qty[0] * (104 - 101))


def test_1500_high_low_close_and_whole_1515_bar_are_ignored():
    a = frame(day("2026-01-05", {**SIGNAL, **EXIT_BARS}))
    b = a.copy()
    m = b.time == "15:00"
    b.loc[m, ["high", "low", "close"]] = [500, 1, 2]
    b.loc[b.time == "15:15", ["open", "high", "low", "close"]] = 7.0
    pd.testing.assert_frame_equal(run(a)["trades"], run(b)["trades"])
    c = a[a.time != "15:15"].reset_index(drop=True)       # auction bar absent
    pd.testing.assert_frame_equal(run(a)["trades"], run(c)["trades"])


def test_missing_1500_bar_makes_session_non_tradable_no_invented_price():
    df = frame(day("2026-01-05", {**SIGNAL, **EXIT_BARS}, drop=("15:00",)))
    r = run(df)
    assert r["trades"].empty
    assert r["missing_bars"] == [("2026-01-05", ["15:00"])]
    assert r["skipped_sessions"] == ["2026-01-05"]
    b = run_open_to_close_benchmark(df, ZERO, CFG)
    assert b["trades"].empty and b["skipped_sessions"] == ["2026-01-05"]


@pytest.mark.parametrize("gone", ["09:15", "09:30", "09:45", "11:00", "14:45"])
def test_any_missing_bar_up_to_exit_makes_session_non_tradable(gone):
    r = run(frame(day("2026-01-05", {**SIGNAL, **EXIT_BARS}, drop=(gone,))))
    assert r["trades"].empty and r["missing_bars"] == [("2026-01-05", [gone])]


def test_tradability_depends_on_bar_existence_not_prices():
    full = frame(day("2026-01-05", {**SIGNAL, **EXIT_BARS}))
    crazy = full.assign(open=1.0, high=1.0, low=1.0, close=1.0)
    assert run(full)["missing_bars"] == run(crazy)["missing_bars"] == []


def test_entry_still_next_bar_open_after_close_confirmation():
    t = run(frame(day("2026-01-05", {**SIGNAL, **EXIT_BARS})))["trades"]
    assert t.entry_time[0] == "2026-01-05 10:00:00" and t.entry_price[0] == 101


def test_no_entry_fill_at_or_after_exit_bar():
    late = {**RANGE, "14:45": (100, 102, 100, 101.5), **EXIT_BARS}   # signal 14:45 -> would fill 15:00
    assert run(frame(day("2026-01-05", late)))["trades"].empty
    with pytest.raises(ValueError):
        EngineConfig(entry_cutoff="15:00")


def test_no_overnight_position_and_flat_at_exit():
    df = frame(day("2026-01-05", {**SIGNAL, **EXIT_BARS}), day("2026-01-06", {**SIGNAL, **EXIT_BARS}))
    r = run(df)
    t, eq = r["trades"], r["equity"]
    assert len(t) == 2
    assert (pd.to_datetime(t.entry_time).dt.date == pd.to_datetime(t.exit_time).dt.date).all()
    last = eq.groupby(eq.date.dt.date).tail(1)
    assert (last.position == 0).all() and (last.date.dt.strftime("%H:%M") == "15:00").all()


def test_costs_correct_at_x2_exit():
    sched = CostModel("test", 20, 0.0003, "min", 0.00025, 0.00003, 0.000001, 0.00003, 0.18, 10)
    t = run(frame(day("2026-01-05", {**SIGNAL, **EXIT_BARS})), costs=sched)["trades"].iloc[0]
    assert t.entry_fill == pytest.approx(101 * 1.001) and t.exit_fill == pytest.approx(104 * 0.999)
    sell = sched.charges("sell", t.qty * t.exit_fill)
    buy = sched.charges("buy", t.qty * t.entry_fill)
    assert t.total_charges == pytest.approx(sum(sell.values()) + sum(buy.values()))
    assert t.net_pnl == pytest.approx(t.gross_pnl - t.slippage - t.total_charges)


def test_pre_cas_and_cas_sessions_follow_identical_x2_rule():
    pre = day("2026-07-15", {**SIGNAL, **EXIT_BARS})                       # 15:15 = CTS trade
    cas = day("2026-08-14", {**SIGNAL, **EXIT_BARS}, drop=("15:15",))     # auction bar missing
    t = run(frame(pre, cas))["trades"]
    assert list(t.exit_time) == ["2026-07-15 15:00:00", "2026-08-14 15:00:00"]
    assert list(t.exit_price) == [104, 104]
    assert t.gross_pnl.iloc[0] == t.gross_pnl.iloc[1]


def test_benchmark_uses_same_exit_and_sessions_as_strategy():
    df = frame(day("2026-01-05", {**SIGNAL, **EXIT_BARS}),
               day("2026-01-06", {**SIGNAL, **EXIT_BARS}, drop=("12:00",)))
    s, b = run(df), run_open_to_close_benchmark(df, ZERO, CFG)
    assert s["missing_bars"] == b["missing_bars"] == [("2026-01-06", ["12:00"])]
    assert list(b["trades"].exit_time) == ["2026-01-05 15:00:00"]
    assert list(b["trades"].exit_price) == [104]


def test_fixed_notional_sizing_does_not_compound():
    win = {**SIGNAL, "15:00": (200, 200, 200, 200)}                      # doubles the sleeve
    df = frame(day("2026-01-05", win), day("2026-01-06", {**SIGNAL, **EXIT_BARS}))
    t = run(df)["trades"]
    assert list(t.qty) == [990, 990]                                       # floor(1e5 / 101) both days
    t2 = run(df, cfg=EngineConfig(capital=100_000, sizing="compound"))["trades"]
    assert t2.qty.iloc[1] > t2.qty.iloc[0]


def test_x2_refuses_a_grid_without_a_1500_bar():
    hourly = pd.DataFrame({"date": pd.to_datetime([f"2026-01-05 {h}" for h in
                                                   ("09:15", "10:15", "11:15", "12:15", "13:15", "14:15", "15:15")]),
                           "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1})
    hourly["session"], hourly["time"] = hourly.date.dt.date, hourly.date.dt.strftime("%H:%M")
    with pytest.raises(ValueError, match="not on this data"):
        run_intraday(hourly, ORB(60, 60), ZERO, CFG)
    run_intraday(hourly, ORB(60, 60), ZERO, EngineConfig.legacy_v0())    # legacy still reproducible

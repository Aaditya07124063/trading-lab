"""Intraday engine + ORB. Every test here must FAIL if the rule it names
is broken - including adversarial look-ahead cases."""

import pandas as pd
import pytest

from src.intraday.costs import CostModel
from src.intraday.data import expected_times, validate
from src.intraday.engine import EngineConfig, run_intraday, run_open_to_close_benchmark
from src.intraday.metrics import summarize
from src.intraday.orb import ORB

GRID = expected_times(15)                    # 09:15 ... 15:15 (25 bars)
ZERO = CostModel.zero()
CFG = EngineConfig(capital=100_000)


def day(date, over=None, base=100.0, drop=()):
    """One 15-min session, flat at `base`; over = {time: (o, h, l, c)}."""
    rows = []
    for t in GRID:
        if t in drop:
            continue
        o, h, l, c = (over or {}).get(t, (base, base + 0.5, base - 0.5, base))
        rows.append({"date": pd.Timestamp(f"{date} {t}"), "open": o, "high": h,
                     "low": l, "close": c, "volume": 1})
    return rows


def frame(*days):
    df = pd.DataFrame([r for d in days for r in d])
    df["session"] = df["date"].dt.date
    df["time"] = df["date"].dt.strftime("%H:%M")
    return df


def orb_run(df, costs=ZERO, cfg=CFG, **kw):
    return run_intraday(df, ORB(30, 15, **kw), costs, cfg)


# range bars 09:15/09:30 -> OR_HIGH 101, OR_LOW 99
RANGE = {"09:15": (100, 101, 99.5, 100), "09:30": (100, 100.5, 99, 100)}


# ---------------- data validation ----------------

def test_validation_flags_duplicates_disorder_nans_and_bad_ohlc():
    df = frame(day("2026-01-05"))
    assert validate(df, 15)["ok"]
    assert "duplicate" in validate(pd.concat([df, df.iloc[[3]]]), 15)["errors"][0]
    assert any("out-of-order" in e for e in validate(df.iloc[::-1].reset_index(drop=True), 15)["errors"])
    bad = df.copy(); bad.loc[4, "close"] = None
    assert any("missing" in e for e in validate(bad, 15)["errors"])
    bad = df.copy(); bad.loc[4, "high"] = 50
    assert any("impossible OHLC" in e for e in validate(bad, 15)["errors"])


def test_validation_warns_on_missing_bars_offgrid_and_zero_volume():
    df = frame(day("2026-01-05", drop=("11:00",)))
    df["volume"] = 0
    w = " ".join(validate(df, 15)["warnings"])
    assert "missing bars" in w and "volume is zero" in w
    shifted = df.assign(date=df["date"] - pd.Timedelta(minutes=15))
    assert "off the" in " ".join(validate(shifted, 15)["warnings"])


# ---------------- ORB rules ----------------

def test_long_breakout_fills_next_bar_open():
    df = frame(day("2026-01-05", {**RANGE, "09:45": (100, 102, 100, 101.5),
                                  "10:00": (101.7, 102, 101, 101.8)}))
    t = orb_run(df)["trades"]
    assert len(t) == 1 and t.side[0] == "LONG"
    assert t.entry_time[0] == "2026-01-05 10:00:00"      # not the 09:45 signal bar
    assert t.entry_price[0] == 101.7                     # 10:00 OPEN, not 09:45 close


def test_short_breakout():
    df = frame(day("2026-01-05", {**RANGE, "10:15": (99.2, 99.3, 98, 98.5),
                                  "10:30": (98.4, 98.6, 98, 98.2)}))
    t = orb_run(df)["trades"]
    assert t.side[0] == "SHORT" and t.entry_price[0] == 98.4


def test_shorts_can_be_disabled():
    df = frame(day("2026-01-05", {**RANGE, "10:15": (99.2, 99.3, 98, 98.5)}))
    assert orb_run(df, allow_short=False)["trades"].empty


def test_breakout_requires_close_not_wick():
    df = frame(day("2026-01-05", {**RANGE, "09:45": (100, 105, 99.8, 100.8)}))
    assert orb_run(df)["trades"].empty


def test_opening_range_uses_only_range_bars():
    # a huge wick AFTER 09:45 must not widen the range
    df = frame(day("2026-01-05", {**RANGE, "10:00": (100, 110, 90, 100),
                                  "10:15": (100, 101.5, 100, 101.2)}))
    t = orb_run(df)["trades"]
    assert t.entry_time[0] == "2026-01-05 10:30:00"


def test_range_bar_missing_means_no_trade():
    df = frame(day("2026-01-05", {**RANGE, "09:45": (100, 102, 100, 101.5)}, drop=("09:30",)))
    assert orb_run(df)["trades"].empty


def test_one_trade_per_day():
    df = frame(day("2026-01-05", {**RANGE, "09:45": (100, 102, 100, 101.5),
                                  "11:00": (100, 100, 97, 97.5), "12:00": (97, 102, 97, 102)}))
    assert len(orb_run(df)["trades"]) == 1


def test_entry_cutoff_blocks_late_fills():
    over = {**RANGE, "14:15": (100, 102, 100, 101.5)}     # signal 14:15 -> fill 14:30 (allowed)
    assert len(orb_run(frame(day("2026-01-05", over)))["trades"]) == 1
    over = {**RANGE, "14:30": (100, 102, 100, 101.5)}     # fill 14:45 > cutoff 14:30
    assert orb_run(frame(day("2026-01-05", over)))["trades"].empty


def test_square_off_at_1515_close_and_never_overnight():
    over = {**RANGE, "09:45": (100, 102, 100, 101.5), "15:15": (103, 104, 102.5, 103.3)}
    df = frame(day("2026-01-05", over), day("2026-01-06", RANGE))
    r = orb_run(df)
    t = r["trades"]
    assert t.exit_time[0] == "2026-01-05 15:15:00"
    assert t.exit_price[0] == 103.3 and t.reason[0] == "square_off"
    assert (pd.to_datetime(t.entry_time).dt.date == pd.to_datetime(t.exit_time).dt.date).all()
    eq = r["equity"]
    assert (eq.loc[eq.date.dt.strftime("%H:%M") == "15:15", "position"] == 0).all()


def test_session_without_1515_bar_is_skipped_not_force_closed():
    partial = day("2026-01-06", {**RANGE, "09:45": (100, 102, 100, 101.5)})[:10]
    r = orb_run(frame(day("2026-01-05"), partial))
    assert r["trades"].empty and r["skipped_sessions"] == ["2026-01-06"]


# ---------------- look-ahead (adversarial) ----------------

def test_strategy_never_sees_a_future_bar():
    class Spy:
        name = "spy"
        seen = []
        def start_session(self, s): pass
        def on_bar(self, bars, pos):
            self.seen.append((len(bars), bars["time"].iloc[-1]))
            return None
    spy = Spy()
    run_intraday(frame(day("2026-01-05")), spy, ZERO, CFG)
    assert spy.seen == [(i + 1, t) for i, t in enumerate(GRID[:-1])]


def test_gap_after_signal_gives_no_free_profit():
    # signal at 09:45 close 101.5, but 10:00 gaps to 150 and stays there.
    # a look-ahead (fill at signal close) engine would book ~+48%.
    over = {**RANGE, "09:45": (100, 102, 100, 101.5)}
    over.update({t: (150, 150, 150, 150) for t in GRID[3:]})
    s = summarize(orb_run(frame(day("2026-01-05", over))), 100_000)
    assert s["gross_pnl"] == 0 and s["trades"] == 1


def test_future_bars_cannot_change_past_decisions():
    over = {**RANGE, "09:45": (100, 102, 100, 101.5)}
    a = frame(day("2026-01-05", over))
    b = a.copy()
    b.loc[b.time > "10:00", ["open", "high", "low", "close"]] = 5.0
    ta, tb = orb_run(a)["trades"], orb_run(b)["trades"]
    assert (ta.entry_time[0], ta.entry_price[0], ta.side[0]) == \
           (tb.entry_time[0], tb.entry_price[0], tb.side[0])


def test_next_day_information_never_used():
    over = {**RANGE, "09:45": (100, 102, 100, 101.5)}
    one = orb_run(frame(day("2026-01-05", over)))["trades"]
    two = orb_run(frame(day("2026-01-05", over), day("2026-01-06", base=1000)))["trades"]
    pd.testing.assert_frame_equal(one, two.iloc[:1])


# ---------------- costs & slippage ----------------

SCHED = CostModel("test schedule (made-up rates)", brokerage_flat=20, brokerage_pct=0.0003,
                  brokerage_mode="min", stt_sell_pct=0.00025, exchange_pct=0.00003,
                  sebi_pct=0.000001, stamp_buy_pct=0.00003, gst_pct=0.18, slippage_bps=0)


def test_charges_by_hand():
    buy = SCHED.charges("buy", 100_000)
    assert buy["brokerage"] == 20                       # min(20, 30)
    assert buy["stt"] == 0 and buy["stamp"] == pytest.approx(3)
    sell = SCHED.charges("sell", 10_000)
    assert sell["brokerage"] == pytest.approx(3)        # min(20, 3)
    assert sell["stt"] == pytest.approx(2.5) and sell["stamp"] == 0
    assert sell["gst"] == pytest.approx(0.18 * (3 + 0.3 + 0.01))


def test_trade_net_equals_gross_minus_all_costs():
    over = {**RANGE, "09:45": (100, 102, 100, 101.5), "10:00": (102, 102, 102, 102),
            "15:15": (104, 104, 104, 104)}
    slipped = CostModel(**{**SCHED.describe(), "slippage_bps": 10})
    r = orb_run(frame(day("2026-01-05", over)), costs=slipped)
    t = r["trades"].iloc[0]
    qty = t.qty
    assert t.entry_fill == pytest.approx(102 * 1.001) and t.exit_fill == pytest.approx(104 * 0.999)
    assert t.gross_pnl == pytest.approx(qty * 2)
    assert t.slippage == pytest.approx(qty * (0.102 + 0.104))
    assert t.net_pnl == pytest.approx(t.gross_pnl - t.slippage - t.total_charges)
    s = summarize(r, 100_000)
    assert s["net_pnl"] == pytest.approx(t.net_pnl, abs=0.01)
    assert s["total_costs"] == pytest.approx(t.slippage + t.total_charges, abs=0.01)


def test_cost_model_refuses_unset_rates():
    with pytest.raises(ValueError):
        CostModel(**{**SCHED.describe(), "stt_sell_pct": None})


def test_sizing_never_spends_more_than_equity():
    over = {**RANGE, "09:45": (100, 102, 100, 101.5), "10:00": (102, 102, 102, 102)}
    t = orb_run(frame(day("2026-01-05", over)), costs=SCHED)["trades"].iloc[0]
    assert t.qty * t.entry_fill + t.brokerage / 2 <= 100_000


# ---------------- benchmark & metrics ----------------

def test_open_to_close_benchmark():
    df = frame(day("2026-01-05", {"09:15": (100, 100, 100, 100), "15:15": (110, 110, 110, 110)}),
               day("2026-01-06", {"09:15": (110, 110, 110, 110), "15:15": (99, 99, 99, 99)}))
    s = summarize(run_open_to_close_benchmark(df, ZERO, CFG), 100_000)
    assert s["trades"] == 2
    assert s["return_pct"] == pytest.approx(-1.0, abs=0.01)     # 1000 shares: +10k, then -11k


def test_summary_profit_factor_and_extremes():
    over_w = {**RANGE, "09:45": (100, 102, 100, 101.5), "10:00": (100, 100, 100, 100),
              "15:15": (110, 110, 110, 110)}
    over_l = {**RANGE, "09:45": (100, 102, 100, 101.5), "10:00": (100, 100, 100, 100),
              "15:15": (95, 95, 95, 95)}
    s = summarize(orb_run(frame(day("2026-01-05", over_w), day("2026-01-06", over_l))), 100_000)
    assert s["trades"] == 2 and s["win_rate"] == 50
    assert s["largest_win"] == pytest.approx(10_000) and s["largest_loss"] == pytest.approx(-5_500)
    assert s["profit_factor"] == pytest.approx(10_000 / 5_500, abs=0.01)


# ---------------- research split ----------------

def test_split_is_chronological_disjoint_and_complete():
    from src.intraday.research import split_sessions
    df = frame(*[day(str(d.date())) for d in pd.bdate_range("2026-01-05", periods=20)])
    parts = split_sessions(df)
    assert list(parts) == ["development", "validation", "final_oos"]
    sess = [sorted(p["session"].unique()) for p in parts.values()]
    assert [len(s) for s in sess] == [10, 5, 5]
    assert sess[0][-1] < sess[1][0] and sess[1][-1] < sess[2][0]
    assert sum(len(p) for p in parts.values()) == len(df)

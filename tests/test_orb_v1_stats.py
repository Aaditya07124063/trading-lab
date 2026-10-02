"""ORB v1 statistics, portfolio aggregation, baselines and regimes.
Synthetic data only. Each test must FAIL if the property it names breaks."""

import numpy as np
import pandas as pd
import pytest

from src.intraday.costs import CostModel
from src.intraday.engine import EngineConfig, run_intraday
from src.intraday.inference import (holm, mean_inference, minimum_detectable_effect,
                                    politis_white_block_length, randomisation_p, verdict)
from src.intraday.orb import ORB
from src.intraday.portfolio import (entry_candidates, portfolio_daily, random_entry_baseline,
                                    sign_flip_baseline, trade_net_pnl)
from src.intraday.regimes import regime_labels
from tests.test_intraday import RANGE, day, frame

SCHED = CostModel("test", 20, 0.0003, "min", 0.00025, 0.00003, 0.000001, 0.00003, 0.18, 5)


# ---------------------------------------------------------------- inference

def _ps(mu, reps=200, n=150, b=400, seed=0):
    rng = np.random.default_rng(seed)
    return np.array([mean_inference(rng.normal(mu, 1, n), mean_block=1.0, b=b, seed=i)["p_one_sided"]
                     for i in range(reps)])


def test_p_value_has_correct_size_under_null():
    p = _ps(0.0)
    assert 0.01 <= (p < 0.05).mean() <= 0.10
    assert 0.40 <= p.mean() <= 0.60


def test_p_value_detects_a_strong_effect_and_ignores_negative_ones():
    assert (_ps(0.5, reps=60) < 0.01).mean() >= 0.95
    assert (_ps(-0.5, reps=60) > 0.9).mean() >= 0.95          # one-sided: never "positive"


def test_guard_against_ssrn_uncentred_bootstrap():
    """The SSRN 5198458 construction gives p ~ 0.5 under a strong effect; ours must not."""
    rng = np.random.default_rng(1)
    x = rng.normal(0.5, 1, 150)
    r = mean_inference(x, mean_block=1.0, b=2000, seed=2)
    boot = r["mean"] + np.random.default_rng(3).choice(x - x.mean(), (2000, 150)).mean(1)
    paper_style = (boot >= r["mean"]).mean()
    assert 0.4 < paper_style < 0.6
    assert r["p_one_sided"] < 0.001


def test_p_value_and_confidence_bound_agree():
    rng = np.random.default_rng(5)
    for i in range(40):
        r = mean_inference(rng.normal(0.12, 1, 120), mean_block=2.0, b=1000, seed=i)
        assert (r["p_one_sided"] < 0.05) == (r["lower_1s_95"] > 0) or \
            abs(r["lower_1s_95"]) < 1e-3                       # ties at the boundary only


def test_verdict_categories():
    rng = np.random.default_rng(7)
    assert verdict(mean_inference(rng.normal(0.6, 1, 150), mean_block=1, b=1000)) == "POSITIVE"
    assert verdict(mean_inference(rng.normal(-0.6, 1, 150), mean_block=1, b=1000)) == "NEGATIVE"
    assert verdict(mean_inference(rng.normal(0.0, 1, 30), mean_block=1, b=1000, seed=3)) == "INCONCLUSIVE"


def test_inference_is_deterministic_given_seed():
    x = np.random.default_rng(9).normal(0, 1, 80)
    assert mean_inference(x, b=500, seed=4) == mean_inference(x, b=500, seed=4)


def test_block_length_grows_with_dependence():
    rng = np.random.default_rng(11)
    iid = rng.normal(0, 1, 500)
    ar = np.empty(500); ar[0] = 0
    for t in range(1, 500):
        ar[t] = 0.8 * ar[t - 1] + rng.normal()
    b_iid, b_ar = politis_white_block_length(iid), politis_white_block_length(ar)
    assert b_iid <= 3 and b_ar >= 5 and b_ar > b_iid


def test_stationary_bootstrap_se_reflects_autocorrelation():
    """AR(1) phi=0.6, n=400: true long-run/naive SE ratio = sqrt(1.6/0.4) = 2 and
    the Politis-White optimal stationary-bootstrap block is ~11. Averaged over
    seeds, the automatic method must get most of the way there."""
    bs, ratios = [], []
    for s in range(10):
        rng = np.random.default_rng(100 + s)
        ar = np.empty(400); ar[0] = 0
        for t in range(1, 400):
            ar[t] = 0.6 * ar[t - 1] + rng.normal()
        r = mean_inference(ar, b=1000, seed=1)
        bs.append(r["block_length"])
        ratios.append(r["se_bootstrap"] / (ar.std(ddof=1) / np.sqrt(400)))
    assert 6 <= np.mean(bs) <= 16
    assert np.mean(ratios) > 1.5


def test_holm_by_hand():
    adj = holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert adj["a"] == pytest.approx(0.03) and adj["c"] == pytest.approx(0.06)
    assert adj["b"] == pytest.approx(0.06)                     # monotone step-down


def test_randomisation_p_and_mde():
    assert randomisation_p(1.0, [0, 0, 0, 2]) == pytest.approx(2 / 5)
    assert minimum_detectable_effect(1.0, 100) == pytest.approx((1.6449 + 0.8416) / 10, abs=1e-3)


# --------------------------------------------------------- portfolio return

def _trades(rows):
    return pd.DataFrame(rows, columns=["session", "gross_pnl", "slippage", "total_charges", "net_pnl",
                                       "brokerage", "stt", "exchange", "sebi", "stamp", "gst"])


def test_portfolio_return_is_on_fixed_total_capital():
    res = {"A": {"trades": _trades([["2026-08-03", 1100, 50, 50, 1000, 0, 0, 0, 0, 0, 50]]),
                 "missing_bars": []},
           "B": {"trades": _trades([["2026-08-03", -400, 50, 50, -500, 0, 0, 0, 0, 0, 50]]),
                 "missing_bars": [("2026-08-04", ["15:00"])]},
           "C": {"trades": _trades([]), "missing_bars": []}}
    p = portfolio_daily(res, ["2026-08-03", "2026-08-04", "2026-08-05"], n_universe=50, capital=100_000)
    assert p.loc["2026-08-03", "net_ret"] == pytest.approx(500 / 5_000_000)   # not 500/2 / 1e5
    assert p.loc["2026-08-04", "net_ret"] == 0 and p.loc["2026-08-05", "net_ret"] == 0
    assert p.loc["2026-08-04", "n_non_tradable"] == 1
    assert list(p.n_trades) == [2, 0, 0]
    assert p.net_ret.mean() == pytest.approx(500 / 5_000_000 / 3)          # zero days count


# -------------------------------------------------------------- baselines

SIG = {**RANGE, "09:45": (100, 102, 100, 101.5), "10:00": (101, 101, 101, 101),
       "15:00": (104, 104, 104, 104)}


def test_vectorised_trade_pnl_matches_engine_exactly():
    for side_over, d in [(SIG, 1), ({**RANGE, "10:15": (99.2, 99.3, 98, 98.5), "10:30": (98, 98, 98, 98),
                                     "15:00": (97, 97, 97, 97)}, -1)]:
        t = run_intraday(frame(day("2026-01-05", side_over)), ORB(30, 15), SCHED,
                         EngineConfig(capital=100_000))["trades"].iloc[0]
        v = trade_net_pnl(t.entry_price, t.exit_price, d, SCHED, 100_000)
        assert float(v) == pytest.approx(t.net_pnl, abs=1e-6)


def test_sign_flip_null_is_centred_and_detects_perfect_direction():
    rng = np.random.default_rng(0)
    g = rng.normal(0, 100, 400)
    tr = pd.DataFrame({"gross_pnl": np.abs(g), "slippage": 0.0, "total_charges": 0.0})  # always right
    draws = sign_flip_baseline(tr, n_sessions=100, n_universe=50, capital=100_000, b=2000, seed=1)
    obs = tr.gross_pnl.sum() / (50 * 100_000 * 100)
    assert randomisation_p(obs, draws) < 0.001
    assert abs(draws.mean()) < 3 * draws.std() / np.sqrt(len(draws)) + 1e-12
    tr2 = pd.DataFrame({"gross_pnl": g, "slippage": 0.0, "total_charges": 0.0})       # random direction
    p = randomisation_p(tr2.gross_pnl.sum() / (50 * 100_000 * 100), draws * 0 +
                        sign_flip_baseline(tr2, 100, 50, 100_000, 2000, 2))
    assert 0.01 < p < 0.99


def test_sign_flip_charges_costs_unflipped():
    tr = pd.DataFrame({"gross_pnl": [0.0, 0.0], "slippage": [10.0, 10.0], "total_charges": [40.0, 40.0]})
    draws = sign_flip_baseline(tr, 1, 1, 1.0, 50, 0)
    assert np.allclose(draws, -100.0)


def test_random_entry_uses_feasible_window_and_x2_exit():
    df = frame(day("2026-01-05", SIG))
    t = run_intraday(df, ORB(30, 15), SCHED, EngineConfig(capital=100_000))["trades"]
    c, x = entry_candidates(df, t)
    assert c.shape == (1, 19)                                  # opens 10:00..14:30
    assert x[0] == 104                                         # 15:00 OPEN
    flat = frame(day("2026-01-05", {**SIG, **{tm: (100, 100, 100, 100) for tm in
                                               ["10:00", "10:15", "14:30", "15:00"]}}))
    c2, x2 = entry_candidates(flat, t)
    draws = random_entry_baseline(c2, x2, CostModel.zero(), 1, 1, 100_000, 300, 0)
    assert draws.shape == (300,)


def test_random_entry_is_reproducible():
    c = np.array([[100.0 + k for k in range(19)]] * 3)
    x = np.array([110.0, 90.0, 100.0])
    a = random_entry_baseline(c, x, SCHED, 10, 50, 100_000, 200, 7)
    b = random_entry_baseline(c, x, SCHED, 10, 50, 100_000, 200, 7)
    assert np.array_equal(a, b)


# ---------------------------------------------------------------- regimes

def test_regime_labels_use_only_past_data():
    rng = np.random.default_rng(3)
    idx = pd.bdate_range("2020-01-01", periods=300)
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, 300))), index=idx)
    a = regime_labels(close)
    shocked = close.copy(); shocked.iloc[200:] *= np.exp(rng.normal(0, 0.2, 100))
    b = regime_labels(shocked)
    pd.testing.assert_frame_equal(a.iloc[:201], b.iloc[:201])   # label at t ignores t and later
    assert a.vol_regime.iloc[:21].isna().all()


# ------------------------------------------------- calendar, bhavcopy, DSR, lock

def test_calendar_counts_standard_sessions_only():
    from src.intraday.calendar import standard_sessions
    s = standard_sessions("2026-10-01", 61)
    assert s[0] == "2026-10-01" and s[-1] == "2026-12-31"
    for holiday in ("2026-10-02", "2026-10-20", "2026-11-10", "2026-11-24", "2026-12-25"):
        assert holiday not in s
    assert "2026-11-08" not in s                         # Muhurat (Sunday) excluded
    assert all(pd.Timestamp(d).dayofweek < 5 for d in s)
    with pytest.raises(FileNotFoundError):               # 2027 list not stored -> no guessing
        standard_sessions("2026-10-01", 62)


def test_bhavcopy_check_flags_but_never_alters():
    from src.intraday.bhavcopy_check import check
    bh = pd.DataFrame({"HghPric": [110.0, 110.0, 50.0], "LwPric": [90.0, 90.0, 40.0],
                       "TtlTradgVol": [1000, 1000, 0]}, index=["OK", "BAD", "GONE"])
    ok = pd.DataFrame({"high": [105.0], "low": [95.0], "volume": [900]})
    bad = pd.DataFrame({"high": [111.0], "low": [95.0], "volume": [100]})
    before = bad.copy()
    f = check({"OK": ok, "BAD": bad, "GONE": ok, "NONE": None}, bh, "2026-08-03", ["OK", "BAD", "GONE", "NONE"])
    got = {(r["symbol"], r["check"]) for r in f}
    assert got == {("BAD", "C1_RANGE"), ("BAD", "C3_VOLUME"), ("GONE", "C2_PRESENCE")}
    pd.testing.assert_frame_equal(bad, before)


def test_deflated_sharpe_is_psr_for_one_trial_and_penalises_more_trials():
    from src.intraday.inference import deflated_sharpe
    x = np.random.default_rng(4).normal(0.08, 1, 250)
    one, many = deflated_sharpe(x, 1), deflated_sharpe(x, 20)
    assert one["sr0_per_period"] == 0 and 0 < many["dsr"] < one["dsr"] < 1


def test_holdout_evaluation_refuses_unfrozen_protocol_and_has_no_tuning_options(tmp_path, monkeypatch):
    """Never launches the real holdout path: points the evaluator at a temporary
    DRAFT protocol (safe even after ORB_v1.md is frozen)."""
    import subprocess, sys
    import evaluate_orb_v1 as ev
    from src.config import BASE_DIR
    draft = tmp_path / "protocol.md"
    draft.write_text("**Status:** DRAFT\n")
    monkeypatch.setattr(ev, "PROTOCOL_FILE", str(draft))
    with pytest.raises(SystemExit, match="not FROZEN"):
        ev.run("holdout")
    h = subprocess.run([sys.executable, "evaluate_orb_v1.py", "--help"], cwd=BASE_DIR,
                       capture_output=True, text=True).stdout
    assert {w for w in h.split() if w.startswith("--")} == {"--help", "--dry-run-dev"}

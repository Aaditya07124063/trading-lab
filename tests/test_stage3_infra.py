"""S2-MOM-v1 statistics, costs, protocol guards, access boundary and analysis plumbing.
SYNTHETIC DATA ONLY: statistical functions are never exercised on real research returns."""

import ast
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

import src.stage3.protocol as P
from src.stage3 import costs, data, experiment, ladder, stats
from tests.test_stage3_ladder import DAYS, ME, make_world

ROOT = Path(__file__).resolve().parents[1]
FULL_DEC = dict(P.RESOLVED_DECISIONS)


def schedule(**override):
    rates = {"stt_buy": 0.001, "stt_sell": 0.001, "exchange_txn": 0.0000307, "sebi_fee": 0.000001,
             "stamp_duty_buy": 0.00015, "gst_rate": 0.18, "brokerage": 0.0, "dp_charge_rs_per_scrip_sold": 15.0}
    rates.update(override)
    return {"components": {k: {"rate": v, "evidence_archived": True, "basis": "HISTORICAL_EVIDENCE"} for k, v in rates.items()}}


def inputs(sample="PRIMARY"):
    wd = make_world()
    u = ladder.universes(wd["univ"], wd["seg2ent"], wd["pool"], wd["cal"], wd["top"], ME["2014-06"])
    w = ladder.wide(wd["panel"], wd["ents"], DAYS)
    return SimpleNamespace(sample=sample, cal=wd["cal"], w=w, univ=u, data_end=wd["cal"]["s_pp"].max(), cutoff=DAYS[-1],
                           delist_ret=np.full(len(w.ents), -0.30), status=wd["panel"].set_index(["entity", "date"])["status"])


# ------------------------------------------------------------------ statistics (§15)
def test_newey_west_matches_statsmodels():
    import statsmodels.api as sm
    x = np.random.default_rng(3).normal(0.2, 1.0, 114)
    x[1:] += 0.5 * x[:-1]
    ref = sm.OLS(x, np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": 4, "use_correction": False})
    r = stats.mean_test(x, 4)
    assert r["se_nw"] == pytest.approx(float(ref.bse[0]), rel=1e-10)
    assert r["t"] == pytest.approx(float(ref.tvalues[0]), rel=1e-10)
    assert r["p_two_sided"] == pytest.approx(float(ref.pvalues[0]), rel=1e-8)     # statsmodels HAC p is normal too


def test_primary_p_value_is_standard_normal_and_deterministic():
    from scipy.stats import norm, t as student
    x = np.arange(1.0, 9.0)                                   # mean 4.5, population variance 5.25
    r = stats.mean_test(x, 0)
    se = (5.25 / 8) ** 0.5
    assert r["mean"] == 4.5 and r["se_nw"] == pytest.approx(se) and r["t"] == pytest.approx(4.5 / se)
    assert r["p_two_sided"] == pytest.approx(2 * norm.sf(4.5 / se), rel=1e-12) and r["distribution"] == "NORMAL"
    assert r["p_two_sided"] != pytest.approx(2 * student.sf(4.5 / se, 7), rel=1e-3)   # not a t(n-1) test
    assert r["ci90"] == pytest.approx((4.5 - norm.ppf(0.95) * se, 4.5 + norm.ppf(0.95) * se))
    assert stats.mean_test(x, 0) == r and stats.mean_test(-x, 0)["p_two_sided"] == r["p_two_sided"]
    import inspect
    assert list(inspect.signature(stats.mean_test).parameters) == ["x", "lag"]       # no distribution switch


def test_newey_west_lag_zero_is_the_plain_variance():
    x = np.array([1.0, 2.0, 4.0, 8.0, 16.0])
    assert stats.newey_west_lrv(x, 0) == pytest.approx(x.var())
    with pytest.raises(ValueError):
        stats.newey_west_lrv(x, 4)


def test_bootstrap_is_seeded_two_sided_and_null_centred():
    rng = np.random.default_rng(5)
    null, shifted = rng.normal(0, 1, 120), rng.normal(0, 1, 120) + 1.0
    a = stats.bootstrap_test(null, 7, 2000)
    assert a == stats.bootstrap_test(null, 7, 2000) and a != stats.bootstrap_test(null, 8, 2000)
    assert stats.bootstrap_test(shifted, 7, 2000)["p_two_sided"] < 0.01 < a["p_two_sided"]
    assert stats.bootstrap_test(-shifted, 7, 2000)["p_two_sided"] < 0.01          # two-sided
    assert P.BOOTSTRAP_RESAMPLES == 10_000 and P.NW_LAG == {"PRIMARY": 4, "OOS": 3, "POOLED": 4}


def test_blinded_precision_reveals_no_location():
    x = np.random.default_rng(9).normal(0.3, 0.6, 114)
    b = stats.blinded_precision(x, 4, 0.10)
    shifted = stats.blinded_precision(x + 5.0, 4, 0.10)
    assert all(b[k] == pytest.approx(shifted[k]) for k in b)                     # identical whatever the mean
    assert stats.blinded_precision(-x, 4, 0.10)["sd"] == pytest.approx(b["sd"])   # and whatever its sign
    banned = ("mean", "t", "p", "p_two_sided", "sharpe", "ci90", "drawdown")
    assert not set(b) & set(banned)
    assert b["detectable_effect_80pct_two_sided_5pct"] == pytest.approx(2.8016 * b["long_run_sd_nw"] / 114 ** 0.5, rel=1e-4)


# ------------------------------------------------------------------ costs (§13, §23)
def test_real_schedule_has_explicit_gaps_that_can_never_become_zero():
    s = costs.load_schedule()
    gaps = costs.missing_evidence(s)
    assert {"stt_buy", "stt_sell", "stamp_duty_buy", "brokerage", "dp_charge_rs_per_scrip_sold"} <= set(gaps) or not gaps
    for c in gaps:
        assert s["components"][c]["rate"] is None or not s["components"][c]["evidence_archived"]
    if gaps:
        with pytest.raises(costs.CostEvidenceMissing):
            costs.side_rates(s, "S0")
        with pytest.raises(costs.CostEvidenceMissing):
            costs.rebalance_cost({"bought": 1.0, "sold": 0.0, "n_sold": 0}, s, "S0")


def test_missing_component_or_rate_is_refused(tmp_path):
    s = schedule()
    del s["components"]["stt_buy"]
    (tmp_path / "s.json").write_text(json.dumps(s))
    with pytest.raises(costs.CostEvidenceMissing, match="lacks components"):
        costs.load_schedule(tmp_path / "s.json")
    with pytest.raises(costs.CostEvidenceMissing):
        costs.side_rates(schedule(stt_sell=None), "S0")
    unarchived = schedule()
    unarchived["components"]["brokerage"]["evidence_archived"] = False
    with pytest.raises(costs.CostEvidenceMissing):
        costs.side_rates(unarchived, "S0")


def test_side_rates_and_frozen_slippage_scenarios():
    buy, sell = costs.side_rates(schedule(), "S0")
    taxed = (0.0000307 + 0.000001) * 1.18
    assert buy == pytest.approx(0.001 + 0.00015 + taxed) and sell == pytest.approx(0.001 + taxed)
    assert costs.side_rates(schedule(), "S2")[0] == pytest.approx(buy + 0.0010)
    assert costs.side_rates(schedule(), "S3", "201-500")[1] == pytest.approx(sell + 0.0075)
    assert P.SLIPPAGE_BPS == {"S0": {"1-200": 0, "201-500": 0}, "S1": {"1-200": 5, "201-500": 15},
                              "S2": {"1-200": 10, "201-500": 30}, "S3": {"1-200": 25, "201-500": 75},
                              "S4": {"1-200": 50, "201-500": 150}}


def test_turnover_and_rebalance_cost():
    t = costs.rebalance({"a": 0.5, "b": 0.5}, {"a": 0.6, "c": 0.4})
    assert t["bought"] == pytest.approx(0.5) and t["sold"] == pytest.approx(0.5) and t["n_sold"] == 2
    assert t["turnover_one_way"] == pytest.approx(0.5)
    first = costs.rebalance({"a": 0.5, "b": 0.5}, {})
    assert first["bought"] == pytest.approx(1.0) and first["sold"] == 0 and first["turnover_one_way"] == pytest.approx(0.5)
    buy, sell = costs.side_rates(schedule(), "S1")
    assert costs.rebalance_cost(t, schedule(), "S1") == pytest.approx(0.5 * buy + 0.5 * sell + 15.0 * 2 / 1e7)
    assert costs.breakeven_one_way(0.004, 0.9, 0.5) == pytest.approx(0.01) and costs.breakeven_one_way(0.004, 0.5, 0.5) is None


# ------------------------------------------------------------------ protocol hash and fail-closed guards
def test_protocol_file_matches_the_frozen_hash_and_constants():
    assert P.file_sha256(P.PROTOCOL_FILE) == P.PROTOCOL_SHA256
    assert (P.FIRST_T, P.LAST_T, P.PRIMARY_LAST_T, P.T_STAR) == tuple(
        pd.Timestamp(x) for x in ("2012-06-29", "2026-07-31", "2021-11-30", "2026-09-30"))
    assert (P.FORMATION_MONTHS, P.SKIP_MONTHS, P.BREAKPOINT, P.TOP_N, P.ALPHA, P.REFERENCE_THRESHOLD) == (12, 1, 0.30, 200, 0.05, 0.10)
    assert P.DELIST_RETURN == {"VOLUNTARY": 0.0, "OTHER": -0.30}


def test_h_runner_refuses_a_changed_protocol_or_registry_record(tmp_path):
    good = {"protocol_sha256": P.PROTOCOL_SHA256}
    assert P.verify_protocol(record=good) is good
    edited = tmp_path / "protocol.md"
    edited.write_text((ROOT / P.PROTOCOL_FILE).read_text() + " ")
    with pytest.raises(P.ProtocolMismatch, match="protocol file"):
        P.verify_protocol(path=edited, record=good)
    with pytest.raises(P.ProtocolMismatch, match="registry"):
        P.verify_protocol(record={"protocol_sha256": "0" * 64})


def test_registry_entry_references_the_protocol_and_is_complete():
    e = P.registry_entry()
    from src.registry.experiments import REQUIRED, STATUSES
    assert not [k for k in REQUIRED if k not in e] and e["status"] == "PLANNED" and e["status"] in STATUSES
    assert e["protocol_sha256"] == P.PROTOCOL_SHA256 and e["freeze_commit"].startswith("7d4cb6d")
    assert e["primary_sample"]["months"] == 114 and e["oos_sample"]["months"] == 56
    assert "none" in e["results"] and e["pending_decisions"] == {} == P.PENDING_DECISIONS
    assert e["decisions"] == {"sample_data_end": "PROTOCOL_EXIT_SESSION", "p_value_distribution": "NORMAL",
                              "bootstrap_seed": 20261005, "neutral_fill": "EQUAL_MEAN",
                              "exit_gap_return_step_d": "REALISED_RAW_GAP_RETURN", "exit_gap_lookahead": "TO_RESEARCH_CUTOFF"}
    assert e["random_seed"] == 20261005 == P.BOOTSTRAP_SEED and set(P.DECISION_KEYS) == set(e["decisions"])
    assert len(json.dumps(e)) < 12_000                                      # a reference, not a copy of the protocol


def test_require_ready_fails_closed():
    rec = {"pending_decisions": {"neutral_fill": "open"}, "decisions": {}}
    with pytest.raises(P.NotReady, match="neutral_fill"):
        P.require_ready(rec)
    with pytest.raises(P.NotReady, match="lacks decisions"):
        P.require_ready({"pending_decisions": {}, "decisions": {"neutral_fill": "EQUAL_MEAN"}})
    ok = {"pending_decisions": {}, "decisions": dict(FULL_DEC)}
    assert P.require_ready(ok) == FULL_DEC
    for key, bad in (("bootstrap_seed", 1), ("p_value_distribution", "T_DOF_N_MINUS_1"), ("sample_data_end", "CALENDAR_MONTH_END"),
                     ("neutral_fill", "DRIFT_WEIGHTED"), ("exit_gap_return_step_d", "NEUTRAL"), ("exit_gap_lookahead", "WITHIN_SAMPLE_DATA_END")):
        with pytest.raises(P.NotReady, match="reviewed values"):
            P.require_ready({"pending_decisions": {}, "decisions": {**FULL_DEC, key: bad}})
    if costs.missing_evidence(costs.load_schedule()):
        with pytest.raises(P.NotReady, match="cost evidence"):
            P.require_ready(ok, need_costs=True)


def test_runner_stops_before_reading_any_data_until_every_gate_has_passed(monkeypatch, tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("run_s2_mom", ROOT / "scripts" / "run_s2_mom.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    monkeypatch.setattr(runner, "OUT", tmp_path / "results")
    monkeypatch.setattr(runner, "CHECKS", tmp_path / "checks")

    def boom(*a, **k):
        raise AssertionError("data was read before the guards passed")
    monkeypatch.setattr(runner.data, "load_inputs", boom)
    rec = {"protocol_sha256": P.PROTOCOL_SHA256, "pending_decisions": {"x": "open"}, "decisions": {}, "provenance": {}}
    monkeypatch.setattr(runner, "verify_protocol", lambda: rec)
    for mode in ("checks", "blinded", "primary", "confirmation"):           # an open decision blocks everything
        with pytest.raises(P.NotReady, match="open decisions"):
            runner.main(mode)
    ready = {**rec, "pending_decisions": {}, "decisions": dict(FULL_DEC)}
    monkeypatch.setattr(runner, "verify_protocol", lambda: ready)
    monkeypatch.setattr(runner, "require_ready", lambda r, need_costs=False: r["decisions"])
    monkeypatch.setattr(runner.data, "verify_provenance", lambda: ["src/stage3/ladder.py"])
    with pytest.raises(P.NotReady, match="manifest"):                        # stale inputs or code block everything
        runner.main("checks")
    monkeypatch.setattr(runner.data, "verify_provenance", lambda: [])
    for mode in ("blinded", "primary", "confirmation"):                      # Stage 2 rebuild not registered as passed
        with pytest.raises(P.NotReady, match="Stage 2 rebuild"):
            runner.main(mode)
    ready["provenance"] = {"stage2_rebuild": {"checks_passed": 149}}
    with pytest.raises(P.NotReady, match="Stage 2 rebuild"):                 # 149 of 150 is not a pass
        runner.main("blinded")
    ready["provenance"] = {"stage2_rebuild": {"checks_passed": 150}}
    for mode in ("blinded", "primary", "confirmation"):                      # no passed pre-run checks
        with pytest.raises(P.NotReady, match="pre-run checks"):
            runner.main(mode)
    (tmp_path / "checks").mkdir()
    for sample in ("primary", "oos"):
        (tmp_path / "checks" / f"pre_run_checks_{sample}.json").write_text(json.dumps({"all_passed": True, "code_sha256": "stale"}))
    with pytest.raises(P.NotReady, match="pre-run checks"):                  # checks from different code do not count
        runner.main("primary")
    for sample in ("primary", "oos"):
        (tmp_path / "checks" / f"pre_run_checks_{sample}.json").write_text(json.dumps({"all_passed": True, "code_sha256": runner.code_sha()}))
    for mode in ("primary", "confirmation"):                                 # no registered blinded artifact
        with pytest.raises(P.NotReady, match="blinded"):
            runner.main(mode)
    with pytest.raises(P.NotReady, match="sensitivity refused"):             # sensitivity needs a registered primary run
        runner.main("sensitivity")
    ready["provenance"]["primary_run"] = {"code_sha256": "other-code", "files_sha256": {}}
    with pytest.raises(P.NotReady, match="sensitivity refused"):             # ... made with exactly this code
        runner.main("sensitivity")
    ready["provenance"]["primary_run"] = {"code_sha256": runner.code_sha(), "files_sha256": {"primary_results.json": "x"}}
    with pytest.raises(P.NotReady, match="missing or changed"):              # ... whose files are intact
        runner.main("sensitivity")
    assert not (tmp_path / "results").exists()                               # nothing was written


# ------------------------------------------------------------------ G. access boundary
def test_g_cutoffs_are_explicit_and_refuse_anything_after_the_research_cutoff():
    from src.access import RESEARCH_CUTOFF
    assert data._cut("2021-12-31") == pd.Timestamp("2021-12-31") and data._cut(RESEARCH_CUTOFF) == pd.Timestamp(RESEARCH_CUTOFF)
    for late in ("2026-10-01", "2027-01-01"):
        with pytest.raises(ValueError, match="research cutoff"):
            data._cut(late)
        with pytest.raises(ValueError, match="research cutoff"):
            data.load_ret(late)
    assert P.T_STAR <= pd.Timestamp(RESEARCH_CUTOFF)


def test_g_samples_end_at_protocol_exit_sessions_inside_the_research_cutoff():
    from src.access import RESEARCH_CUTOFF
    import inspect
    c = ladder.calendar(pd.bdate_range("2011-06-22", "2026-09-30"))
    assert c.loc[c["sample"] == "PRIMARY", "s_pp"].max() > pd.Timestamp("2021-12-31")   # exit is the next session
    assert pd.Timestamp("2026-08-31") < c["s_pp"].max() <= pd.Timestamp(RESEARCH_CUTOFF)
    assert list(inspect.signature(data.load_inputs).parameters) == ["sample", "out"]    # no switch can move a cutoff
    src = inspect.getsource(data.load_inputs)
    assert "_cut(T_STAR)" in src and "research cutoff - refused" in src


def test_g_stage3_code_cannot_reach_collector_intraday_or_orb_files():
    allowed = {"src.access", "src.config", "src.registry", "src.registry.experiments", "src.stage2.returns",
               "src.intraday.inference", "src.stage3", "src.stage3.protocol", "src.stage3.ladder", "src.stage3.costs",
               "src.stage3.data", "src.stage3.stats", "src.stage3.experiment"}
    banned = ("data/india", "data/gold", "raw/yahoo", "collection_log", "raw/manifest", "orb_v1", "holdout", "intraday/",
              "m15")
    files = sorted((ROOT / "src" / "stage3").glob("*.py")) + [ROOT / "scripts" / "build_stage3.py", ROOT / "scripts" / "run_s2_mom.py"]
    assert len(files) >= 8
    for f in files:
        tree = ast.parse(f.read_text())
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and (n.module or "").startswith("src"):
                assert n.module in allowed, f"{f.name} imports {n.module}"
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and n is not ast.get_docstring(tree, clean=False):
                if len(n.value) < 200:
                    assert not any(b in n.value for b in banned), f"{f.name}: {n.value!r}"
            if isinstance(n, ast.Attribute) and n.attr in ("environ", "getenv"):
                raise AssertionError(f"{f.name} reads the environment - no switch may relax the cutoff")


# ------------------------------------------------------------------ analysis plumbing (synthetic world)
def test_blinded_step_outputs_dispersion_and_counts_only():
    b = experiment.blinded(inputs())
    assert b["paired_months"] == b["months_in_calendar"] == 16 and b["sd"] > 0 and len(b["delta_series_sha256"]) == 64
    flat = json.dumps(b, default=str).lower()
    for word in ("mean", "sharpe", "drawdown", "p_two_sided", "wml", "\"t\"", "ci90", "decision", "conclusion"):
        assert word not in flat, word
    assert b == experiment.blinded(inputs())                                   # deterministic


def test_analyse_and_reverse_ladder_run_end_to_end_on_synthetic_data():
    inp = inputs()
    r = experiment.analyse(inp, schedule())
    assert r["H1"]["n"] == 16 and r["H1"]["lag"] == 4 and r["H1_bootstrap"]["B"] == 10_000
    assert r["H1_bootstrap"]["seed"] == 20261005 and r["H1"]["distribution"] == "NORMAL"
    assert r["H1"]["decision"] in ("MATERIAL", "DETECTED_SIZE_UNCERTAIN", "IMMATERIAL", "INCONCLUSIVE")
    assert set(r["ladder"]) == set("ABCD") and set(r["step_differences_pct"]) == {"A-B", "B-C", "C-D"}
    assert r["step_E"]["status"] == "COST-EVIDENCE-PENDING" and r["step_E"]["missing_cost_evidence"] == []   # never run here
    e = experiment.step_e(r["monthly"], experiment.run(inp)[1], schedule(), 4)        # the cost code itself, called directly
    assert set(e) == {"status", "assumptions_under_frozen_section_13", "S0", "S1", "S2", "S3", "S4", "breakeven_one_way_bps"}
    net = [e[s]["W_net"]["mean_pct"] for s in ("S0", "S1", "S2", "S3", "S4")]
    assert net == sorted(net, reverse=True) and net[0] < r["ladder"]["D"]["W"]["mean_pct"]   # costs only reduce
    d = r["delta"]
    wml = r["monthly"].pivot(index="t", columns="step", values="WML")
    assert r["H1"]["mean"] == pytest.approx(((wml["A"] - wml["D"]) * 100).mean()) and d["paired"].all()
    rev = experiment.reverse_ladder(inp)
    assert set(rev) == set(ladder.REVERSE_SPECS)
    ev = r["events"]
    assert set(ev.columns) == {"t", "step", "portfolio", "kind", "entity", "date", "ret1_1_status"}
    assert set(ev["kind"]) <= {"NEUTRAL_FILL", "NEUTRAL_FILL_NO_OTHER_STOCKS", "EXIT_GAP_BOOKED",
                               "EXIT_GAP_BOOKED_FLAGGED_ROW", "DELISTING_RETURN"} and "DELISTING_RETURN" in set(ev["kind"])


def test_net_of_costs_first_month_buys_everything_then_trades_the_drift():
    inp = inputs()
    monthly, hold = experiment.run(inp)
    n = ladder.net_of_costs(monthly, hold, "D", "W", schedule(), "S0")
    assert n["turnover_one_way"].iloc[0] == pytest.approx(0.5) and (n["turnover_one_way"].iloc[1:] <= 1.0).all()
    assert (n["net"] < n["gross"]).all() and len(n) == 16
    assert n["cost"].iloc[0] == pytest.approx(costs.side_rates(schedule(), "S0")[0])   # full purchase, no sale


def test_identity_refuses_a_grouping_mismatch(tmp_path, monkeypatch):
    (tmp_path / "identity").mkdir()
    pd.DataFrame({"segment_id": ["s1", "s2"], "entity_id": ["I1", "I2"]}).to_csv(tmp_path / "identity" / "id1_segments.csv", index=False)
    pd.DataFrame({"entity_id": ["I1", "I2"], "end_status": ["ACTIVE_AT_CUTOFF", "DELISTED_EVIDENCED"],
                  "end_evidence": [None, "X 2020-01-01 Voluntary Delisting"]}).to_csv(tmp_path / "identity" / "id1_entities.csv", index=False)
    monkeypatch.setattr(data, "D2", tmp_path)
    seg2ent, ident = data.identity(pd.DataFrame({"segment_id": ["s1", "s2"], "entity_id": ["R1", "R2"]}))
    ident = ident.set_index("entity_id")
    assert seg2ent == {"s1": "R1", "s2": "R2"} and ident.loc["R1", "in_pool"] and not ident.loc["R2", "in_pool"]
    assert ident["delist_class"].to_dict() == {"R1": "OTHER", "R2": "VOLUNTARY"}
    with pytest.raises(ValueError, match="same entities"):
        data.identity(pd.DataFrame({"segment_id": ["s1", "s2"], "entity_id": ["R1", "R1"]}))


# ------------------------------------------------------------------ real-data pre-run checks (run here on synthetic data)
def test_pre_run_checks_pass_on_a_clean_pipeline_and_disclose_no_momentum_result():
    r = experiment.pre_run_checks(inputs())
    assert set(r) == {"sample", "months_in_calendar", "pairing", "boundary", "perturbation", "truncation", "placebo",
                      "data_quality_counts", "all_passed"}
    assert all(r[k]["pass"] for k in ("pairing", "boundary", "perturbation", "truncation")), r
    assert r["pairing"]["paired_months"] == 16 and len(r["perturbation"]["dates"]) == 5
    assert r["placebo"]["seed"] == 20261005 and r["placebo"]["same_rankable_stocks"]
    assert r["all_passed"] == r["placebo"]["pass"]
    flat = json.dumps(r, default=str).lower()
    for word in ("sharpe", "drawdown", "wml_a", "wml_d", "delta", "ci90", "decision", "conclusion", "mean_pct"):
        assert word not in flat, word
    assert r == experiment.pre_run_checks(inputs())                              # deterministic


def test_pre_run_checks_catch_a_pipeline_that_uses_the_future():
    leaky = inputs()
    leaky.cal = leaky.cal.assign(m1=leaky.cal["s_pp"])                           # formation window runs past t
    r = experiment.pre_run_checks(leaky)
    assert not r["perturbation"]["pass"] and not r["truncation"]["pass"] and not r["boundary"]["pass"]
    assert r["all_passed"] is False


def test_pre_run_checks_catch_an_unpaired_month():
    short = inputs()
    short.data_end = short.cal["s_pp"].iloc[-2]                                  # last month cannot be computed
    r = experiment.pre_run_checks(short)
    assert not r["pairing"]["pass"] and r["pairing"]["paired_months"] == 15 and r["all_passed"] is False


# ------------------------------------------------------------------ gross primary run; costs pending (§13)
def test_primary_result_is_gross_and_identical_whether_or_not_cost_evidence_exists():
    inp = inputs()
    full, pending = experiment.analyse(inp, schedule()), experiment.analyse(inp, schedule(stt_buy=None))
    assert pending["H1"] == full["H1"] and pending["H1_bootstrap"] == full["H1_bootstrap"]      # delta needs no cost
    pd.testing.assert_frame_equal(pending["monthly"], full["monthly"])
    pd.testing.assert_frame_equal(pending["delta"], full["delta"])
    e = pending["step_E"]
    assert e["status"] == "COST-EVIDENCE-PENDING" and e["missing_cost_evidence"] == ["stt_buy"]
    assert not set(e) & {"S0", "S1", "S2", "S3", "S4", "breakeven_one_way_bps"}                 # nothing fabricated
    assert full["step_E"]["status"] == "COST-EVIDENCE-PENDING" and full["step_E"]["missing_cost_evidence"] == []
    sens = experiment.sensitivity_analysis(inp, pending["monthly"], pending["H1"], schedule(stt_buy=None))
    assert all(v["H4"] == "COST-EVIDENCE-PENDING" for v in sens["sensitivity"].values())
    assert sens["reliability"]["H4_under_sensitivity"] == "COST-EVIDENCE-PENDING"
    with pytest.raises(costs.CostEvidenceMissing):                                               # cost code stays fail-closed
        ladder.net_of_costs(pending["monthly"], experiment.run(inp)[1], "D", "W", schedule(stt_buy=None), "S0")


def test_frozen_section_13_fallback_is_explicit_and_never_silent():
    ok = schedule()
    ok["components"]["exchange_txn"].update(basis="CURRENT_RATE_ASSUMPTION", assumed_for_period="2012-07-02..2026-09-01",
                                            why_history_unavailable="no dated history archived")
    assert costs.missing_evidence(ok) == [] and [a["component"] for a in costs.assumptions(ok)] == ["exchange_txn"]
    assert costs.assumptions(schedule()) == []
    for broken in ({"basis": "CURRENT_RATE_ASSUMPTION"},                                    # no period, no reason
                   {"basis": "CURRENT_RATE_ASSUMPTION", "assumed_for_period": "x"},          # no reason
                   {"basis": None}, {"basis": "GUESS"}, {"rate": None}, {"evidence_archived": False}):
        s = schedule()
        s["components"]["stamp_duty_buy"].update(broken)
        assert costs.missing_evidence(s) == ["stamp_duty_buy"], broken
        with pytest.raises(costs.CostEvidenceMissing):
            costs.side_rates(s, "S0")
    real = costs.load_schedule()
    assert {a["component"] for a in costs.assumptions(real)} <= {"exchange_txn", "sebi_fee", "gst_rate"}
    for c in costs.missing_evidence(real):
        assert real["components"][c]["rate"] is None                                         # missing means null, never 0


# ------------------------------------------------------------------ §25 sensitivity treatments and labels
def test_sensitivity_block_has_the_four_frozen_treatments_and_the_fixed_labels():
    inp = inputs()
    primary = experiment.analyse(inp, schedule())
    r = {**primary, **experiment.sensitivity_analysis(inp, primary["monthly"], primary["H1"], schedule())}
    assert set(r["sensitivity"]) == {"R_SPAN", "R_GAP", "R_MISS_RAW", "R_MISS_ZERO", "R_DELIST_ZERO", "R_DELIST_MINUS100"}
    for name, v in r["sensitivity"].items():
        assert v["paired_months"] == 16 and v["unpaired_months"] == 0 and v["treatment"] == experiment.SENSITIVITY[name]
        assert {"H1", "H1_sign_changed", "H1_significance_changed", "H3_sign_changed", "H3_significance_changed", "H4"} <= set(v)
    rel = r["reliability"]
    assert (experiment.RANKABLE_MIN, experiment.RANKABLE_MEAN, experiment.FILL_SHARE_MAX) == (100, 150, 0.05)
    assert rel["rankable_below_minimum"] is True and rel["not_reliable"] is True            # the toy world has ~10 stocks
    assert rel["filled_share_above_5pct"] is False
    assert 0.0 <= rel["filled_share_of_W_stock_days"] < 0.05 and 0.0 <= rel["filled_share_of_L_stock_days"] < 0.05
    assert "filled_share_of_W_and_L_stock_days" not in rel                                   # never one combined denominator
    assert rel["changes_under_sensitivity"] == bool(rel["sensitivity_treatments_that_change_H1_or_H3"])
    untouched = experiment.analyse(inp, schedule())                                          # deterministic, primary unaffected
    assert untouched["H1"] == r["H1"]
    assert experiment.sensitivity_analysis(inp, untouched["monthly"], untouched["H1"], schedule())["sensitivity"] == r["sensitivity"]
    # the delisting treatments really reach step D: the toy world has delisted names
    same = lambda name: r["sensitivity"][name]["H1"]["mean"] == pytest.approx(r["H1"]["mean"], abs=1e-12)
    ev = r["events"]
    hit = bool(len(ev[(ev["step"] == "D") & ev["portfolio"].isin(["W", "L"]) & (ev["kind"] == "DELISTING_RETURN")]))
    assert same("R_DELIST_ZERO") != hit and same("R_DELIST_MINUS100") != hit      # moves H1 exactly when W or L held a delisted stock
    assert same("R_MISS_ZERO") and same("R_MISS_RAW") and same("R_SPAN") and same("R_GAP")   # no flagged row in the toy world


def test_delisting_treatments():
    inp = SimpleNamespace(delist_ret=np.array([0.0, -0.30, -0.30]))
    assert experiment._delist(inp, "ZERO").tolist() == [0.0, 0.0, 0.0]
    assert experiment._delist(inp, "MINUS100").tolist() == [0.0, -1.0, -1.0]                 # voluntary stays 0%
    with pytest.raises(ValueError):
        experiment._delist(inp, "OTHER")


# ------------------------------------------------------------------ saved holdings and end weights
def test_saved_holdings_reproduce_membership_weights_and_turnover_without_a_second_run():
    inp = inputs()
    r = experiment.analyse(inp, schedule())
    h, monthly = r["holdings"], r["monthly"]
    _, hold = experiment.run(inp)
    pd.testing.assert_frame_equal(h, experiment.analyse(inputs(), schedule())["holdings"])   # deterministic
    assert set(h["step"]) == set("ABCD") and set(h["portfolio"]) == {"W", "L", "BM"} and set(h["sample"]) == {"PRIMARY"}
    assert set(h.columns) >= {"t", "holding_month", "s_plus", "s_pp", "formation_rank", "n_rankable", "liquidity_rank",
                              "begin_weight", "end_weight", "month_status"}
    for (step, t, p), g in h.groupby(["step", "t", "portfolio"]):
        assert g["entity"].tolist() == [e for e in hold[(step, t)]["order"] if e in set(hold[(step, t)][p])]   # = in-memory holdings
        assert set(g["entity"]) == set(hold[(step, t)][p])
        assert g["begin_weight"].tolist() == pytest.approx([1.0 / len(g)] * len(g))          # the intended equal weights
        assert g["end_weight"].sum() == pytest.approx(1.0)
        assert dict(zip(g["entity"], g["end_weight"])) == pytest.approx(hold[(step, t)][p + "_end"])
        k = len(hold[(step, t)]["W"])
        if p == "W":
            assert g["formation_rank"].tolist() == list(range(1, k + 1))
        if p == "L":
            assert g["formation_rank"].tolist() == list(range(g["n_rankable"].iloc[0] - k + 1, g["n_rankable"].iloc[0] + 1))
    # turnover from the SAVED file equals turnover from the in-memory run
    saved = h[(h["step"] == "D") & (h["portfolio"] == "W")]
    ts, prev, turn = sorted(saved["t"].unique()), {}, []
    for t in ts:
        g = saved[saved["t"] == t]
        turn.append(costs.rebalance(dict(zip(g["entity"], g["begin_weight"])), prev)["turnover_one_way"])
        prev = dict(zip(g["entity"], g["end_weight"]))
    assert turn == pytest.approx(ladder.net_of_costs(monthly, hold, "D", "W", schedule(), "S0")["turnover_one_way"].tolist())
    d = ladder.paired_delta(monthly, inp.cal)                                                # pairing unchanged
    assert d["paired"].all() and len(d) == 16


@pytest.mark.parametrize("w_filled,l_filled,fails", [
    (4, 4, False),        # W 4%, L 4%            -> passes
    (6, 4, True),         # W above, L below      -> fails
    (4, 6, True),         # W below, L above      -> fails
    (6, 6, True),         # both above            -> fails
    (5, 5, False),        # exactly 5%            -> does not fail ("more than 5%")
    (5, 0, False),
    (9, 0, True),         # W 9%, L 0%: a combined denominator would give 4.5% and wrongly pass
    (0, 9, True),
])
def test_fill_threshold_is_applied_to_w_and_l_separately(w_filled, l_filled, fails):
    # two months, k = 5 stocks, 10 sessions each -> 100 stock-days per portfolio
    monthly = pd.DataFrame({"step": "D", "status": "OK", "k": [5, 5], "holding_sessions": [10, 10], "n_rankable": [200, 200],
                            "W_filled_stock_days": [w_filled, 0], "L_filled_stock_days": [np.nan, l_filled]})
    share = experiment.fill_shares(monthly)
    assert share == {"W": pytest.approx(w_filled / 100), "L": pytest.approx(l_filled / 100)}
    rel = experiment.reliability(monthly, {})
    assert rel["filled_share_above_5pct"] is fails and rel["not_reliable"] is fails           # nothing else is triggered
    assert rel["rankable_below_minimum"] is False and rel["changes_under_sensitivity"] is False


# ------------------------------------------------------------------ primary mode and sensitivity mode are separate
def test_primary_analysis_runs_no_sensitivity_no_reverse_ladder_and_no_cost_code(monkeypatch):
    inp = inputs()
    before = experiment.analyse(inp, schedule())

    def forbidden(*a, **k):
        raise AssertionError("the primary analysis called sensitivity, reverse-ladder or cost code")
    for target, name in ((experiment, "sensitivity"), (experiment, "reverse_ladder"), (experiment, "step_e"),
                         (experiment, "_delist"), (ladder, "treated"), (ladder, "net_of_costs"),
                         (costs, "side_rates"), (costs, "rebalance_cost")):
        monkeypatch.setattr(target, name, forbidden)
    r = experiment.analyse(inp, schedule())                                    # still works: none of them is used
    assert r["H1"] == before["H1"] and r["H1_bootstrap"] == before["H1_bootstrap"]
    pd.testing.assert_frame_equal(r["monthly"], before["monthly"])
    assert r["sensitivity"] == "SENSITIVITY-PENDING" == r["reverse_ladder"] and r["step_E"]["status"] == "COST-EVIDENCE-PENDING"
    assert set(r["monthly"]["step"]) == set("ABCD")                            # no sensitivity or reverse-order step rows
    rel = r["reliability"]
    assert rel["changes_under_sensitivity"] == "SENSITIVITY-PENDING" and rel["status"].startswith("PARTIAL")
    assert rel["not_reliable"] is True                                         # toy world: rankable count already fails
    clean = pd.DataFrame({"step": "D", "status": "OK", "k": [60], "holding_sessions": [21], "n_rankable": [190]})
    assert experiment.reliability(clean)["not_reliable"] is None               # counts pass, sensitivity unknown: not decided
    assert experiment.reliability(clean, {})["not_reliable"] is False          # decided only once sensitivity has run


def test_sensitivity_mode_reads_the_registered_primary_outputs_and_cannot_alter_them(tmp_path):
    inp = inputs()
    primary = experiment.analyse(inp, schedule())
    primary["monthly"].to_csv(tmp_path / "primary_monthly.csv", index=False)                 # as the runner saves them
    (tmp_path / "primary_results.json").write_text(json.dumps({"H1": primary["H1"]}, default=str))
    before = (tmp_path / "primary_monthly.csv").read_bytes()
    assert experiment.run(inp)[0].to_csv(index=False).encode() == before          # the runner's identity check: recompute == file
    monthly = pd.read_csv(tmp_path / "primary_monthly.csv", parse_dates=["t"])               # as the runner reads them
    h1 = json.loads((tmp_path / "primary_results.json").read_text())["H1"]
    from_disk = experiment.sensitivity_analysis(inp, monthly, h1, schedule())
    in_memory = experiment.sensitivity_analysis(inp, primary["monthly"], primary["H1"], schedule())
    assert set(from_disk) == {"sample", "sensitivity", "reliability", "reverse_ladder"}
    assert set(from_disk["reverse_ladder"]) == set(ladder.REVERSE_SPECS) and from_disk["reliability"]["status"].startswith("COMPLETE")
    for name in experiment.SENSITIVITY:
        a, b = from_disk["sensitivity"][name], in_memory["sensitivity"][name]
        assert a["H1"]["mean"] == pytest.approx(b["H1"]["mean"], abs=1e-9)
        assert {k: a[k] for k in a if k.endswith("_changed")} == {k: b[k] for k in b if k.endswith("_changed")}
    assert (tmp_path / "primary_monthly.csv").read_bytes() == before                         # primary outputs untouched
    pd.testing.assert_frame_equal(experiment.analyse(inp, schedule())["monthly"], primary["monthly"])

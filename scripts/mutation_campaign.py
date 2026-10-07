"""Deterministic mutation campaign on SCRATCH CLONES of the repository (never on the project itself).

    python3 scripts/mutation_campaign.py SCRATCH_DIR OUT_DIR [--shards 6] [--only TEXT]

One deliberate change at a time is applied to a clone (APFS copy-on-write, `cp -cR`), the full test
suite runs there, and the file is restored. Each shard is one recorded batch: OUT_DIR/batch_<k>.jsonl
is appended after every mutation, so a crash or a timeout loses nothing; a crashed mutation is recorded
as ERROR and the batch continues. OUT_DIR/mutation_results.json is the merged result.

A mutation is KILLED only when a BEHAVIOURAL test fails (`killed_by` = the first such test). A test that merely compares file hashes
(PIN below) would fail for any edit of a hashed file and proves nothing about the rule, so a mutation
caught only by such tests is reported separately as KILLED_BY_HASH_PIN_ONLY.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
L, P, S, E, D = "src/stage3/ladder.py", "src/stage3/protocol.py", "src/stage3/stats.py", "src/stage3/experiment.py", "src/stage3/data.py"
SE, C, U, RT, CA, AC = ("src/stage3/step_e.py", "src/stage3/costs.py", "src/stage2/universe.py", "src/stage2/returns.py",
                        "src/stage2/corporate_actions.py", "src/access.py")
RUN, RUNE, C2, REG, INF = ("scripts/run_s2_mom.py", "scripts/run_s2_mom_step_e.py", "scripts/run_s2_mom_c2.py",
                           "src/registry/experiments.py", "src/intraday/inference.py")
INT, REPRO, ARCH = "src/registry/integrity.py", "scripts/reproduce_s2_mom_v1.py", "scripts/release_archive.py"

# (group, name, file, old, new). The first 104 are the 2026-10-07 forensic set (two registry ones re-targeted
# at the rewritten registry code); the rest were added by the remediation.
M = [
 ("research logic", "breakpoint 0.30->0.31", P, "BREAKPOINT = 0.30 ", "BREAKPOINT = 0.31 "),
 ("research logic", "skip month removed", P, "SKIP_MONTHS = 1 ", "SKIP_MONTHS = 0 "),
 ("research logic", "formation 12->11", P, "FORMATION_MONTHS = 12 ", "FORMATION_MONTHS = 11 "),
 ("research logic", "top_n 200->201", P, "TOP_N = 200 ", "TOP_N = 201 "),
 ("research logic", "delist OTHER -30%->-3%", P, '"OTHER": -0.30}', '"OTHER": -0.03}'),
 ("research logic", "NW lag primary 4->5", P, '"PRIMARY": 4,', '"PRIMARY": 5,'),
 ("research logic", "alpha .05->.10", P, "ALPHA = 0.05 ", "ALPHA = 0.10 "),
 ("research logic", "slippage S1 5->6", P, '"S1": {"1-200": 5,', '"S1": {"1-200": 6,'),
 ("research logic", "entry same session (s > t -> >=)", L, "after_t, after_n = s[s > t],", "after_t, after_n = s[s >= t],"),
 ("research logic", "exit one session early (s > nxt -> >=)", L, "(s[s > nxt] if nxt", "(s[s >= nxt] if nxt"),
 ("research logic", "rank ascending (losers as winners)", L, "ascending=[False, True], kind", "ascending=[True, True], kind"),
 ("research logic", "tie-break reversed", L, "ascending=[False, True], kind", "ascending=[False, False], kind"),
 ("research logic", "formation reaches entry session (look-ahead)", L, "np.expm1(cs[a1, j] - cs[a12, j])[ok]", "np.expm1(cs[sp, j] - cs[a12, j])[ok]"),
 ("research logic", "formation reaches selection date t (no skip)", L, "np.expm1(cs[a1, j] - cs[a12, j])[ok]", "np.expm1(cs[pos[c.t], j] - cs[a12, j])[ok]"),
 ("research logic", "holding includes entry-session return (naive)", L, "w.ln[a + 1:b + 1][:, j]).sum(0)", "w.ln[a:b + 1][:, j]).sum(0)"),
 ("research logic", "holding drops exit session (RG)", L, "enumerate(range(a + 1, b + 1)):", "enumerate(range(a + 1, b)):"),
 ("research logic", "neutral fill -> zero", L, "f = r[ok].mean() if ok.any() else 0.0", "f = 0.0"),
 ("research logic", "delisting return sign", L, "v[q] *= 1 + delist_ret[e]", "v[q] *= 1 - delist_ret[e]"),
 ("research logic", "delisting rule also in steps A/B", L, 'rule, ukey == "C", consumed', "rule, True, consumed"),
 ("research logic", "delisting rule off everywhere", L, 'rule, ukey == "C", consumed', "rule, False, consumed"),
 ("research logic", "RG formation ignores flagged rows", L, "ok &= (w.c_bad[a1, j] - w.c_bad[a12, j]) == 0", "pass"),
 ("research logic", "gap return counted twice (no consumed)", L, "consumed.add((e, i))", "pass"),
 ("research logic", "WML = W + L", L, 'rec["WML"] = rec["W"] - rec["L"]', 'rec["WML"] = rec["W"] + rec["L"]'),
 ("research logic", "delta sign flipped (D - A)", L, '(out["t"].map(wml.get("A", pd.Series(dtype=float)))\n                                   - out["t"].map(wml.get("D", pd.Series(dtype=float)))) * 100',
  '(out["t"].map(wml.get("D", pd.Series(dtype=float)))\n                                   - out["t"].map(wml.get("A", pd.Series(dtype=float)))) * 100'),
 ("research logic", "delta not in percent", L, 'pd.Series(dtype=float)))) * 100, np.nan)', 'pd.Series(dtype=float)))) * 1, np.nan)'),
 ("research logic", "step A pool filter removed", L, "if pool is not None:\n        u = u[u[\"entity\"].isin(pool)]", "if False:\n        u = u[u[\"entity\"].isin(pool)]"),
 ("research logic", "top200 takes n+1", L, 'drop_duplicates("entity").head(n)', 'drop_duplicates("entity").head(n + 1)'),
 ("research logic", "naive factor inverted", L, 'ret["close"] / (ret["prev_close"] * f) - 1', 'ret["close"] / ret["prev_close"] * f - 1'),
 ("research logic", "RG uses non-research-grade rows", L, 'lr=mat(np.where(cls == "OK", np.log1p(p["r_rg"].fillna(0.0)), 0.0), 0.0, float)', 'lr=mat(np.log1p(p["r_raw"].fillna(0.0)), 0.0, float)'),
 ("research logic", "rankable needs only m1 price", L, "ok = w.present[a12, j] & w.present[a1, j]", "ok = w.present[a1, j]"),
 ("research logic", "portfolio return = median", L, 'rec[p] = float(v.mean() - 1)', 'rec[p] = float(np.median(v) - 1)'),
 ("research logic", "missing-price stop disabled", L, 'if p["r_naive"].isna().to_numpy()[~first].any():', "if False:"),
 ("research logic", "step D spec uses pool universe", L, '"D": ("C", "RG")}', '"D": ("B", "RG")}'),
 ("research logic", "step A uses PIT date", L, 'out[("A", t)] = fixed', 'out[("A", t)] = top200(by_date[t], seg2ent, pool, n)'),
 ("statistics and decisions", "NW Bartlett weight -> 1", S, "2.0 * (1.0 - k / (lag + 1.0)) *", "2.0 * 1.0 *"),
 ("statistics and decisions", "NW variance / (n-1)", S, "lrv = np.dot(d, d) / n", "lrv = np.dot(d, d) / (n - 1)"),
 ("statistics and decisions", "p one-tailed reported as two-sided", S, "2 * stats.norm.sf(abs(t)), stats.norm.ppf(0.95)", "stats.norm.sf(abs(t)), stats.norm.ppf(0.95)"),
 ("statistics and decisions", "ci90 uses 97.5% quantile", S, "stats.norm.ppf(0.95)\n", "stats.norm.ppf(0.975)\n"),
 ("statistics and decisions", "bootstrap not null-centred", S, "stationary_bootstrap_means(x, block, b, seed) - x.mean()", "stationary_bootstrap_means(x, block, b, seed)"),
 ("statistics and decisions", "bootstrap one-sided", S, "np.sum(np.abs(dev) >= abs(x.mean()))", "np.sum(dev >= abs(x.mean()))"),
 ("statistics and decisions", "SE without sqrt(n)", S, "se = math.sqrt(newey_west_lrv(x, lag) / n)", "se = math.sqrt(newey_west_lrv(x, lag))"),
 ("statistics and decisions", "H1 decision threshold flipped", E, 'else "DETECTED_SIZE_UNCERTAIN" if h1["p_two_sided"] < ALPHA', 'else "DETECTED_SIZE_UNCERTAIN" if h1["p_two_sided"] > ALPHA'),
 ("statistics and decisions", "economic conclusion uses two-sided p", E, 'table[s]["WML"]["p_two_sided"] / 2 < ALPHA),', 'table[s]["WML"]["p_two_sided"] < ALPHA),'),
 ("statistics and decisions", "reliability fill W or L -> and", E, 'share["W"] > FILL_SHARE_MAX or share["L"] > FILL_SHARE_MAX', 'share["W"] > FILL_SHARE_MAX and share["L"] > FILL_SHARE_MAX'),
 ("statistics and decisions", "holm multiplier constant", C2, "min(1.0, (len(p) - j) * v)", "min(1.0, len(p) * v)"),
 ("statistics and decisions", "BH divisor dropped", C2, "len(p) * ranked[j - 1][1] / j", "len(p) * ranked[j - 1][1]"),
 ("statistics and decisions", "C2 confirmation rule sign ignored", C2, "if primary_mean * conf[\"mean\"] <= 0:", "if False:"),
 ("costs (step E)", "stamp duty on sells too", SE, 'value * p["stamp_duty_buy"]["rate"] if buy else 0.0', 'value * p["stamp_duty_buy"]["rate"]'),
 ("costs (step E)", "dp charge on buys not sells", SE, '0.0 if buy else float(p["dp_charge"]["billed_rs"])', 'float(p["dp_charge"]["billed_rs"]) if buy else 0.0'),
 ("costs (step E)", "brokerage cap ignored (max)", SE, 'min(value * p["brokerage"]["rate"], p["brokerage"]["cap_rs_per_order"])', 'max(value * p["brokerage"]["rate"], p["brokerage"]["cap_rs_per_order"])'),
 ("costs (step E)", "net = gross + cost", SE, 'out[name[p].format("net") + f"_{s}"] = m[p] - c[(f"cost_fraction_{s}", p)]', 'out[name[p].format("net") + f"_{s}"] = m[p] + c[(f"cost_fraction_{s}", p)]'),
 ("costs (step E)", "slippage bps as percent", SE, 'out["slippage_band"].map(bps) / 1e4', 'out["slippage_band"].map(bps) / 1e2'),
 ("costs (step E)", "band boundary rank<200", SE, "(BAND_TOP, False) if rank <= 200 else", "(BAND_TOP, False) if rank < 200 else"),
 ("costs (step E)", "H4 p tail reversed", SE, 'p = float(norm.sf(r["t"]))', 'p = float(norm.cdf(r["t"]))'),
 ("costs (step E)", "break-even inverted", SE, "None if why else x / d * 1e4", "None if why else d / x * 1e4"),
 ("costs (step E)", "schedule period boundary exclusive", SE, 'if _day(p["from"]) <= d <= _day(p["to"])]', 'if _day(p["from"]) < d <= _day(p["to"])]'),
 ("costs (step E)", "turnover not halved", SE, 'c[("traded_fraction", p)] / 2 ', 'c[("traded_fraction", p)] / 1 '),
 ("costs (step E)", "STT sell uses buy rate key swapped", SE, 'p["stt_buy" if buy else "stt_sell"]["rate"]', 'p["stt_sell" if buy else "stt_buy"]["rate"]'),
 ("costs (step E)", "indirect tax also on STT", SE, 'c["tax_base_rs"] = sum(c[k + "_rs"] for k in TAX_BASE)', 'c["tax_base_rs"] = sum(c[k + "_rs"] for k in TAX_BASE) + c["stt_rs"]'),
 ("costs (step E)", "drift ignored (full rebuy each month)", SE, 'drift, prev_exit = dict(zip(g["entity"], g["end_weight"])), s_pp', 'drift, prev_exit = {}, s_pp'),
 ("costs (step E)", "rate date = exit not entry", SE, 'target, p = dict(zip(g["entity"], g["begin_weight"])), periods_on(schedule, s_plus)', 'target, p = dict(zip(g["entity"], g["begin_weight"])), periods_on(schedule, s_pp)'),
 ("costs (step E)", "hypothetical net WML ignores L cost", SE, '- c[(f"cost_fraction_{s}", "W")] - c[(f"cost_fraction_{s}", "L")]', '- c[(f"cost_fraction_{s}", "W")]'),
 ("guards and registry", "cutoff guard off", D, "if ts > pd.Timestamp(RESEARCH_CUTOFF):", "if False:"),
 ("guards and registry", "stage3 input hash check off", D, "if _sha(out / rel) != want:", "if False:"),
 ("guards and registry", "RET-1.1 hash check off", D, "if _sha(BASE_DIR / rel) != want:", "if False:"),
 ("guards and registry", "UNIV-1 hash check off", D, "if _sha(f) != UNIV1_SHA256:", "if False:"),
 ("guards and registry", "voluntary class mislabelled", D, 'str.contains("Voluntary")', 'str.contains("Compulsory")'),
 ("guards and registry", "survivor pool = everyone", D, 'e["in_pool"] = e["end_status"] == "ACTIVE_AT_CUTOFF"', 'e["in_pool"] = True'),
 ("guards and registry", "protocol hash check off", P, "if got != PROTOCOL_SHA256:", "if False:"),
 ("guards and registry", "registry protocol hash check off", P, 'if rec.get("protocol_sha256") != PROTOCOL_SHA256:', "if False:"),
 ("guards and registry", "pending decisions ignored", P, "if pending:", "if False:"),
 ("guards and registry", "runner overwrite guard off", RUN, "if f.exists():\n        raise NotReady(f\"{f.relative_to(BASE_DIR)} already exists", "if False:\n        raise NotReady(f\"{f.relative_to(BASE_DIR)} already exists"),
 ("guards and registry", "runner provenance gate off", RUN, "if stale:", "if False:"),
 ("guards and registry", "runner pre-run-check gate off", RUN, 'and json.loads(f.read_text()).get("code_sha256") == code_sha()', ""),
 ("guards and registry", "confirmation without same-code primary", RUN, 'if mode == "confirmation" and (prov.get("primary_run") or {}).get("code_sha256") != code_sha():', "if False:"),
 ("guards and registry", "blinded artifact gate off", RUN, 'or _sha(f) != prov["blinded_precision_artifact_sha256"]:', "or False:"),
 ("guards and registry", "step E input hash check off", RUNE, "if _sha(root / rel) != sha:", "if False:"),
 ("guards and registry", "step E overwrite guard off", RUNE, "if out.exists() or partial.exists():", "if False:"),
 ("costs (step E)", "step E schedule hash check off", SE, "if _sha(path) != expected_sha256:", "if False:"),
 ("statistics and decisions", "C2 input hash check off", C2, "if _sha(root / rel) != sha:", "if False:"),
 ("costs (step E)", "cost evidence gap -> usable", C, 'if c.get("rate") is None or not c.get("evidence_archived") or c.get("basis") not in BASES:', "if False:"),
 ("statistics and decisions", "registry duplicate id allowed", REG, 'if rec["experiment_id"] in state:', "if False:"),
 ("statistics and decisions", "registry unknown status allowed", REG, 'if rec["status"] not in STATUSES:', "if False:"),
 ("guards and registry", "research_frame includes holdout day", AC, "df[col] < pd.Timestamp(HOLDOUT_START)", "df[col] <= pd.Timestamp(HOLDOUT_START)"),
 ("stage 2 data", "liquidity window shifted 1 session into the future", U, "win = sessions[i - WINDOW + 1:i + 1]", "win = sessions[i - WINDOW + 2:i + 2]"),
 ("stage 2 data", "liquidity window 63->64", U, "WINDOW = 63", "WINDOW = 64"),
 ("stage 2 data", "min valid 50->49", U, "MIN_VALID = 50", "MIN_VALID = 49"),
 ("stage 2 data", "identity links from the future", U, 'eff = links[links["effective"] <= t]', "eff = links"),
 ("stage 2 data", "liquidity mean instead of median", U, "mat.fillna(0.0).median(axis=1)", "mat.fillna(0.0).mean(axis=1)"),
 ("stage 2 data", "liquidity rank ascending", U, "ascending=[True, False, True])", "ascending=[True, True, True])"),
 ("stage 2 data", "fund units admitted", U, '"FUND_UNIT" if isin.startswith("INF") else', '"FUND_UNIT" if False else'),
 ("stage 2 data", "universe cutoff guard off", U, 'if pd.to_datetime(panel["date"]).max() > CUT:', "if False:"),
 ("stage 2 data", "jump threshold 1.4->1.5", RT, "JUMP = 1.4", "JUMP = 1.5"),
 ("stage 2 data", "event attached to row before ex-date", RT, 'direction="forward")', 'direction="backward")'),
 ("stage 2 data", "ex-date boundary prev_date <= ex", RT, 'm["prev_date"] < m["ex_date"])]', 'm["prev_date"] <= m["ex_date"])]'),
 ("stage 2 data", "gap rows research-grade", RT, 'p["gap_sessions"] > 0,', 'p["gap_sessions"] > 99999,'),
 ("stage 2 data", "unvalidated factor applied", RT, 'p["ret_adj"] = np.where(validated,', 'p["ret_adj"] = np.where(p["event_factor"].notna(),'),
 ("stage 2 data", "returns cutoff guard off", RT, 'if p["date"].max() > CUT:', "if False:"),
 ("stage 2 data", "large residual 10%->50%", RT, "LARGE_RESIDUAL = 0.10", "LARGE_RESIDUAL = 0.50"),
 ("stage 2 data", "bonus factor inverted", CA, "f *= h / (a + h)", "f *= a / (a + h)"),
 ("stage 2 data", "validation band 1.25->2.0", CA, "ok = abs(math.log(adjr)) < math.log(1.25)", "ok = abs(math.log(adjr)) < math.log(2.0)"),
 ("stage 2 data", "post-cutoff corporate actions kept", CA, '(ev["ex_date"] <= pd.Timestamp(RESEARCH_CUTOFF))]', '(ev["ex_date"] <= pd.Timestamp("2100-01-01"))]'),
 ("statistics and decisions", "PW block length forced 1", INF, "return float(min(max(b, 1.0), bmax))", "return 1.0"),
 ("statistics and decisions", "bootstrap resampler not circular/blocks iid", INF, "idx[:, t] = np.where(new[:, t], starts[:, t], (idx[:, t - 1] + 1) % n)", "idx[:, t] = starts[:, t]"),
 # ------------------------------------------------------------------ added by the remediation
 ("research logic", "+ equal weight -> value weight", L, 'rec[p] = float(v.mean() - 1)', 'rec[p] = float((v * v).sum() / v.sum() - 1)'),
 ("research logic", "+ benchmark = whole universe, not the rankable stocks", L, '"BM": sorted(form.index)}', '"BM": sorted(ents)}'),
 ("research logic", "+ holding drops exit session (naive)", L, "w.ln[a + 1:b + 1][:, j]).sum(0)", "w.ln[a + 1:b][:, j]).sum(0)"),
 ("research logic", "+ step D holding uses raw returns", L, "r = np.expm1(w.lr[i, j])", "r = np.expm1(w.lraw[i, j])"),
 ("research logic", "+ span rows counted as research-grade", L, 'ok=mat(cls == "OK", False, bool),', 'ok=mat(np.isin(cls, ["OK", "SPAN"]), False, bool),'),
 ("research logic", "+ flagged holding day not filled", L, "ok, bad = w.ok[i, j] & ~skip[n], w.bad[i, j] & ~skip[n]", "ok, bad = w.ok[i, j] & ~skip[n], w.bad[i, j] & False"),
 ("research logic", "+ k = floor(0.30 n) (no rounding)", L, "k = int(math.floor(breakpoint * len(names) + 0.5))", "k = int(math.floor(breakpoint * len(names)))"),
 ("research logic", "+ delta paired on step A only", L, 'both = (sa == "OK") & (sd == "OK")', 'both = (sa == "OK")'),
 ("research logic", "+ voluntary delisting -30%", P, '"VOLUNTARY": 0.0,', '"VOLUNTARY": -0.30,'),
 ("research logic", "+ formation window includes m(12) session", L, "np.expm1(cs[a1, j] - cs[a12, j])[ok]", "np.expm1(cs[a1, j] - cs[a12 - 1, j])[ok]"),
 ("statistics and decisions", "+ bootstrap seed changed", P, "BOOTSTRAP_SEED = 20261005", "BOOTSTRAP_SEED = 20261006"),
 ("statistics and decisions", "+ bootstrap resamples 10000->1000", P, "BOOTSTRAP_RESAMPLES = 10_000 ", "BOOTSTRAP_RESAMPLES = 1_000 "),
 ("statistics and decisions", "+ NW lag OOS 3->4", P, '"OOS": 3,', '"OOS": 4,'),
 ("statistics and decisions", "+ reference threshold 0.10->0.20", P, "REFERENCE_THRESHOLD = 0.10 ", "REFERENCE_THRESHOLD = 0.20 "),
 ("statistics and decisions", "+ MATERIAL without the size condition", E, "(lo > REFERENCE_THRESHOLD or hi < -REFERENCE_THRESHOLD)", "True"),
 ("statistics and decisions", "+ IMMATERIAL without the interval condition", E, 'else "IMMATERIAL" if -REFERENCE_THRESHOLD < lo and hi < REFERENCE_THRESHOLD else', 'else "IMMATERIAL" if True else'),
 ("statistics and decisions", "+ winners-beat-universe uses two-sided p", E, 'stats.mean_test(g["W"] - g["BM"], lag)["p_two_sided"] / 2 < ALPHA)}', 'stats.mean_test(g["W"] - g["BM"], lag)["p_two_sided"] < ALPHA)}'),
 ("guards and registry", "+ registry: duplicate id accepted on read", REG, 'if rec.get("experiment_id") in out:', "if False:"),
 ("guards and registry", "+ registry: non-initial start state accepted", REG, 'if rec["status"] not in INITIAL_STATUSES:', "if False:"),
 ("guards and registry", "+ registry: FINAL -> PLANNED allowed", REG, '"FINAL": set(_END),', '"FINAL": set(_END) | {"PLANNED"},'),
 ("guards and registry", "+ registry: transition check off", REG, "if new != prev and new not in TRANSITIONS[prev]:", "if False:"),
 ("guards and registry", "+ registry: frozen-state protection off", REG, "if prev not in MUTABLE_STATES:", "if False:"),
 ("guards and registry", "+ registry: empty reason accepted", REG, 'if not isinstance(rec["reason"], str) or not rec["reason"].strip():', "if False:"),
 ("guards and registry", "+ registry: recorded hashes replaceable", REG, 'if x is not None and any("sha256" in str(p) for p in (k, *path)) and _at(v, path) != x:', "if False:"),
 ("guards and registry", "+ registry: identity fields replaceable", REG, "if k in IDENTITY and old != v:", "if False:"),
 ("guards and registry", "+ registry: anchors replaceable", REG, "if not isinstance(v, dict) or any(_at(v, p) != x for p, x in _leaves({} if old is _MISSING else old)):", "if False:"),
 ("guards and registry", "+ registry: hash chain not checked", REG, 'if n >= n0 and rec.get("chain_prev_sha256") != before:', "if False:"),
 ("guards and registry", "+ registry: history pin not checked", REG, "if n0 and (len(lines) < n0 or", "if False and (len(lines) < n0 or"),
 ("guards and registry", "+ registry: duplicate line accepted", REG, "if line in seen:", "if False:"),
 ("guards and registry", "+ registry: truncated last line tolerated", REG, 'if raw and not raw.endswith(b"\\n"):\n        raise RegistryError("registry ends', 'if False:\n        raise RegistryError("registry ends'),
 ("guards and registry", "+ registry: amendments not validated on read", REG, "if n >= n0:\n                _check_amendment(", "if False:\n                _check_amendment("),
 ("guards and registry", "+ registry: revalidation gate off", REG, 'if (prev, new) == ("REQUIRES REVALIDATION", "FINAL") and not reval:', "if False:"),
 ("guards and registry", "+ registry: revalidation allowed from any state", REG, "if reval and not (protected_ok or new == \"REQUIRES REVALIDATION\"):", "if False:"),
 ("guards and registry", "+ registry: revalidation unlocks without the state", REG, 'protected_ok = reval and prev == "REQUIRES REVALIDATION"', "protected_ok = reval"),
 ("guards and registry", "+ registry: misstated previous state accepted", REG, 'if rec["previous_state"] != prev or rec["new_state"] != new:', "if False:"),
 ("guards and registry", "+ registry: orphan amendment accepted", REG, 'if rec["amends"] not in out:\n                raise', 'if False:\n                raise'),
 ("guards and registry", "+ trial log silenced outside pytest", REG, 'if "pytest" in sys.modules:', "if True:"),
 ("guards and registry", "+ provenance: manifest anchor not checked", INT, "if hashlib.sha256(raw).hexdigest() != want:", "if False:"),
 ("guards and registry", "+ provenance: missing anchor tolerated", INT, "if not isinstance(want, str) or len(want) != 64:", "if False:"),
 ("guards and registry", "+ provenance: file hashes not checked", INT, "if not isinstance(want, str) or sha256(_file(root, rel, inside)) != want:", "if False:"),
 ("guards and registry", "+ provenance: output set not exact", INT, "if not isinstance(outs, dict) or set(outs) != set(OUTPUTS):", "if False:"),
 ("guards and registry", "+ provenance: duplicate manifest key accepted", INT, "if len(keys) != len(set(keys)):\n        raise ProvenanceError", "if False:\n        raise ProvenanceError"),
 ("guards and registry", "+ provenance: unexpected file accepted", INT, "    if extra:", "    if False:"),
 ("guards and registry", "+ provenance: symlinked input accepted", INT, "if f.is_symlink() or not f.is_file():", "if not f.is_file():"),
 ("guards and registry", "+ provenance: protocol link not checked", INT, 'if content.get("protocol_sha256") != rec.get("protocol_sha256"):', "if False:"),
 ("guards and registry", "+ provenance: RET-1.1 folder not compared", INT, "if on_disk != sorted(datasets):", "if False:"),
 ("guards and registry", "+ archive: tar hash not checked on restore", ARCH, 'if sha256(archive) != man["tar_sha256"]:', "if False:"),
 ("guards and registry", "+ archive: unknown member accepted", ARCH, 'if rel not in man["files"] or not info.isfile():', "if False:"),
 ("guards and registry", "+ archive: existing file overwritten", ARCH, 'if sha256(target) != man["files"][rel]["sha256"]:\n                    raise', 'if False:\n                    raise'),
]
MIN_FREE_BYTES = 700 << 20
EXTRA = [       # the release tooling itself: a verifier that cannot fail verifies nothing
 ("release tooling", "+ repro: independent WML = W + L", REPRO, 'row["WML"] = row["W"] - row["L"]', 'row["WML"] = row["W"] + row["L"]'),
 ("release tooling", "+ repro: tolerance 1e-9 -> 1", REPRO, "TOL = 1e-9", "TOL = 1.0"),
 ("release tooling", "+ repro: comparison never fails", REPRO, "if diff > tol:", "if False:"),
 ("release tooling", "+ repro: NaN accepted in the comparison", REPRO, "if not (np.isfinite(got).all() and np.isfinite(want).all()):", "if False:"),
 ("release tooling", "+ repro: label comparison never fails", REPRO, "if got != want:\n            raise Fail(f\"{name}: recomputed", "if False:\n            raise Fail(f\"{name}: recomputed"),
 ("release tooling", "+ repro: registry state not checked", REPRO, 'if rec["status"] != "FINAL":', "if False:"),
 ("release tooling", "+ repro: trial log not checked", REPRO, 'if [t["params"]["mode"] for t in mine] != TRIALS:', "if False:"),
 ("release tooling", "+ repro: result file hashes not checked", REPRO, "if sha(root / folder / name) != want:", "if False:"),
 ("release tooling", "+ repro: unregistered result file accepted", REPRO, '        if extra:\n            raise Fail(f"unregistered', '        if False:\n            raise Fail(f"unregistered'),
 ("release tooling", "+ repro: registered code hash not checked", REPRO, 'if got != prov[run]["code_sha256"]:', "if False:"),
 ("release tooling", "+ repro: pinned protocol hash not checked", REPRO, 'if sha(root / rel) != want:\n            raise Fail(f"{rel} does not have its pinned', 'if False:\n            raise Fail(f"{rel} does not have its pinned'),
 ("release tooling", "+ repro: addenda hashes not checked", REPRO, 'if sha(root / a["file"]) != a["sha256"]:', "if False:"),
 ("release tooling", "+ repro: python -O accepted", REPRO, 'if rep["optimized"]:', "if False:"),
 ("release tooling", "+ repro: environment anchor not checked", REPRO, "if not (root / rel).is_file() or sha(root / rel) != want:", "if False:"),
 ("release tooling", "+ repro: missing dependency accepted", REPRO, 'if rep["missing"]:', "if False:"),
 ("release tooling", "+ repro: independent ladder ignores the delisting return", REPRO, "v[n] *= 1 + M.delist[e]", "pass"),
 ("release tooling", "+ repro: independent ladder drops the exit session", REPRO, "for i in range(sp + 1, spp + 1):", "for i in range(sp + 1, spp):"),
 ("release tooling", "+ repro: independent ladder ranks ascending", REPRO, "order = sorted(zip(-score[rankable], names[rankable]))", "order = sorted(zip(score[rankable], names[rankable]))"),
 ("release tooling", "+ repro: independent step E ignores drift", REPRO, 'drift = dict(zip(g["entity"], g["end_weight"]))\n    return out', 'drift = {}\n    return out'),
 ("release tooling", "+ repro: independent step E taxes STT", REPRO, 'cost = taxed * (1 + r["indirect_tax"]["rate"]) + value * r["stt_buy" if buy else "stt_sell"]["rate"]', 'cost = (taxed + value * r["stt_buy" if buy else "stt_sell"]["rate"]) * (1 + r["indirect_tax"]["rate"])'),
 ("release tooling", "+ repro: one-sided p tail reversed", REPRO, '"p_one": 0.5 * math.erfc(t / math.sqrt(2))}', '"p_one": 0.5 * math.erfc(-t / math.sqrt(2))}'),
 ("release tooling", "+ repro: Newey-West without Bartlett weights", REPRO, "2 * (1 - k / (lag + 1)) * (d[k:] @ d[:-k]) / n", "2 * (d[k:] @ d[:-k]) / n"),
 ("release tooling", "+ repro: report may be written inside the repository", REPRO, "if root.resolve() == report.parent or root.resolve() in report.parents:", "if False:"),
 ("release tooling", "+ repro: a failed step still ends in PASS", REPRO, 'out["verdict"] = "PASS" if ok else "FAIL"', 'out["verdict"] = "PASS"'),
 ("release tooling", "+ repro: repository change not detected", REPRO, "        if changed:\n            raise Fail(f\"the run changed", "        if False:\n            raise Fail(f\"the run changed"),
 ("release tooling", "+ validation: missing naive return accepted", INT, '_need(not p.loc[~first, "r_naive"].isna().any(), ', "_need(True, "),
 ("release tooling", "+ validation: infinite value accepted", INT, "_need(not np.isinf(p[c].to_numpy()).any(), ", "_need(True, "),
 ("release tooling", "+ validation: return of -100% accepted", INT, "_need((p[c].dropna() > -1).all(), ", "_need(True, "),
 ("release tooling", "+ validation: duplicate panel row accepted", INT, '_need(not p.duplicated(["date", "entity"]).any(), ', "_need(True, "),
 ("release tooling", "+ validation: unknown row class accepted", INT, '_need(set(p["cls"].unique()) <= CLASSES, ', "_need(True, "),
 ("release tooling", "+ validation: last session need not be T*", INT, "_need(sessions.iloc[-1] == pd.Timestamp(T_STAR), ", "_need(True, "),
 ("release tooling", "+ validation: month count not checked", INT, "_need(len(cal) == months, ", "_need(True, "),
 ("release tooling", "+ validation: universe size not checked", INT, "_need(len(sizes) == 3 * months and (sizes == TOP_N).all(), ", "_need(True, "),
 ("release tooling", "+ validation: step A list may change", INT, "_need(frozenset(grp[\"entity\"]) == fixed, ", "_need(True, "),
 ("release tooling", "+ validation: calendar order not checked", INT, '_need(((c["m12"] < c["m1"]) & (c["m1"] < c["t"]) & (c["t"] < c["s_plus"]) & (c["s_plus"] < c["s_pp"])).all(),', "_need(True,"),
 ("release tooling", "+ validation: non-OK month accepted", INT, '_need((m["status"] == "OK").all(), ', "_need(True, "),
 ("release tooling", "+ validation: zero cost accepted", INT, "_need((e[cost] > 0).all().all(), ", "_need(True, "),
 ("release tooling", "+ validation: NaN in registered returns accepted", INT, "_need(np.isfinite(s.to_numpy(dtype=float)).all(), ", "_need(True, "),
 ("release tooling", "+ validation: cutoff consistency not checked", INT, "_need(pd.Timestamp(RESEARCH_CUTOFF) + pd.Timedelta(days=1) == pd.Timestamp(HOLDOUT_START),", "_need(True,"),
 ("release tooling", "+ validation: T* after the cutoff accepted", INT, "_need(pd.Timestamp(T_STAR) <= pd.Timestamp(RESEARCH_CUTOFF), ", "_need(True, "),
 ("release tooling", "+ validation: cutoff other than the registered T* accepted", INT, "_need(str(RESEARCH_CUTOFF) == T_STAR, ", "_need(True, "),
 ("release tooling", "+ environment: version mismatch not reported", INT, "if have[name] != version:", "if False:"),
 ("release tooling", "+ environment: unloadable library not reported", INT, 'broken[module] = f"{type(e).__name__}: {str(e)[:160]}"', "pass"),
 ("release tooling", "+ repro: unloadable dependency accepted", REPRO, 'if rep["broken"]:', "if False:"),
 ("release tooling", "+ environment: missing package not reported", INT, "            missing.append(name)", "            pass"),
]
# Tests that compare a file hash (or a registered code hash) and therefore fail for ANY edit of a hashed file.
PIN = re.compile(r"::(" + "|".join((
    "test_frozen_orb_methodology_unchanged", "test_protocol_file_matches_the_frozen_hash_and_constants",
    "test_registered_c2_output_is_intact", "test_runner_is_isolated_from_the_backtest_and_pins_the_frozen_inputs",
    "test_schedule_is_the_audited_file", "test_module_is_separate_from_the_registered_code_and_writes_nothing",
    "test_registered_result_files_are_byte_identical", "test_registered_step_e_outputs_are_intact_and_outside_the_registered_results",
    "test_the_real_chain_is_anchored_in_the_registry_and_verifies", "test_the_untouched_scratch_copy_verifies",
    "test_reproduction_command_in_a_clean_process",
    "test_frozen_loader_and_independent_loader_build_the_same_matrices_from_the_registered_inputs",
    "test_frozen_code_is_byte_identical_to_the_pre_remediation_snapshot")) + r")(\[|$)")


def worker(repo, out, shard, nshard, only):
    if out.exists():                                                 # resume: keep finished rows, retry errors
        keep = [x for x in out.read_text().splitlines() if json.loads(x)["status"] != "ERROR"]
        out.write_text("".join(x + "\n" for x in keep))
    done = {json.loads(x)["mutation"] for x in out.read_text().splitlines()} if out.exists() else set()
    base = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=no", "-o", "addopts="]
    ids = [x for x in subprocess.run(base + ["--collect-only"], cwd=repo, capture_output=True, text=True).stdout.splitlines() if "::" in x]
    pins = [x for x in ids if PIN.search(x)]
    if len(ids) < 900 or not pins:
        raise SystemExit(f"[batch {shard}] test collection failed in the clone ({len(ids)} tests)")
    deselect = [a for x in pins for a in ("--deselect", x)]
    for n, (group, name, f, old, new) in enumerate(M + EXTRA):
        if n % nshard != shard or name in done or (only and only not in name):
            continue
        res = {"mutation": name, "group": group, "file": f}
        path = repo / f
        if shutil.disk_usage(repo).free < MIN_FREE_BYTES:               # never fill the disk: stop this batch, keep what is recorded
            print(f"[batch {shard}] ABORTED: less than {MIN_FREE_BYTES >> 20} MB free - rerun to resume", flush=True)
            return
        try:
            src = path.read_text()
            if src.count(old) < 1:
                res["status"] = "NOT_APPLIED"
            else:
                path.write_text(src.replace(old, new, 1))
                try:
                    # pass 1: behavioural tests only, stop at the first failure (a killed mutant ends early)
                    r = subprocess.run(base + ["-x"] + deselect, cwd=repo, capture_output=True, text=True, timeout=900)
                    failed = re.findall(r"^(?:FAILED|ERROR) (\S+)", r.stdout, re.M)
                    if not failed and r.returncode != 0:
                        failed = [f"PYTEST_EXIT_{r.returncode}"]              # collection error or crash: the suite did not pass
                    if failed:
                        res.update(status="KILLED", killed_by=failed[0])
                    else:                                                    # pass 2: would only a hash-pin test notice?
                        r = subprocess.run(base + pins, cwd=repo, capture_output=True, text=True, timeout=900)
                        pinned = re.findall(r"^(?:FAILED|ERROR) (\S+)", r.stdout, re.M)
                        res.update(status="KILLED_BY_HASH_PIN_ONLY" if pinned or r.returncode != 0 else "SURVIVED", killed_by=(pinned or [None])[0])
                except subprocess.TimeoutExpired:
                    res.update(status="KILLED", killed_by="TIMEOUT (suite did not finish in 900 s)")
                finally:
                    path.write_text(src)
        except Exception as e:                                               # never stop the batch
            res.update(status="ERROR", error=repr(e))
        with open(out, "a") as fh:
            fh.write(json.dumps(res) + "\n")
        print(f"[batch {shard}] {res['status']:24s} {name}", flush=True)


def main(scratch, outdir, shards, only):
    scratch, outdir = Path(scratch).resolve(), Path(outdir).resolve()
    if BASE == scratch or BASE in scratch.parents:
        raise SystemExit("the scratch directory must be outside the repository")
    outdir.mkdir(parents=True, exist_ok=True)
    scratch.mkdir(parents=True, exist_ok=True)
    procs = []
    for k in range(shards):
        repo = scratch / f"mrepo{k}"
        if repo.exists():
            shutil.rmtree(repo)
        subprocess.run(["cp", "-cR", str(BASE), str(repo)], check=True)      # APFS clone: no extra disk until a file changes
        shutil.rmtree(repo / ".git", ignore_errors=True)
        procs.append(subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--worker", str(repo),
                                       str(outdir / f"batch_{k}.jsonl"), str(k), str(shards), only or ""]))
    codes = [p.wait() for p in procs]
    rows = [json.loads(x) for k in range(shards) if (outdir / f"batch_{k}.jsonl").exists()
            for x in (outdir / f"batch_{k}.jsonl").read_text().splitlines()]
    order = {m[1]: n for n, m in enumerate(M + EXTRA)}
    rows.sort(key=lambda r: order[r["mutation"]])
    (outdir / "mutation_results.json").write_text(json.dumps(rows, indent=1) + "\n")
    import hashlib                                               # which code and which tests this campaign measured
    state = {f: hashlib.sha256((BASE / f).read_bytes()).hexdigest() for f in sorted({m[2] for m in M + EXTRA})}
    state["tests/ (all test files, one hash)"] = hashlib.sha256(b"".join(p.read_bytes() for p in sorted((BASE / "tests").glob("*.py")))).hexdigest()
    (outdir / "code_state.json").write_text(json.dumps(state, indent=1) + "\n")
    for k in range(shards):
        shutil.rmtree(scratch / f"mrepo{k}", ignore_errors=True)
    count = lambda s: sum(r["status"] == s for r in rows)
    print(f"\nmutations {len(rows)} of {len(M + EXTRA)} | killed {count('KILLED')} | hash-pin only {count('KILLED_BY_HASH_PIN_ONLY')} | "
          f"survived {count('SURVIVED')} | not applied {count('NOT_APPLIED')} | error {count('ERROR')} | batch exit codes {codes}")
    for r in rows:
        if r["status"] not in ("KILLED",):
            print(f"  {r['status']:24s} {r['file']:34s} {r['mutation']}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--worker"]:
        worker(Path(a[1]), Path(a[2]), int(a[3]), int(a[4]), a[5])
    elif len(a) >= 2:
        main(a[0], a[1], int(a[a.index("--shards") + 1]) if "--shards" in a else 6,
             a[a.index("--only") + 1] if "--only" in a else None)
    else:
        raise SystemExit(__doc__)

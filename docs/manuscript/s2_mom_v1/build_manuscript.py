"""Build the S2-MOM-v1 manuscript from its template and the registered result files.

Presentation layer only. Read-only on every registered artifact: no backtest, no
return, no cost and no test statistic is computed here. Every number in the
manuscript is either typed in the template as a design constant or filled from a
registered result file by a {{placeholder}}, and each fill is logged in
number_audit.csv.

    python3 docs/manuscript/s2_mom_v1/build_manuscript.py          # md, figures, audit, checks
    python3 docs/manuscript/s2_mom_v1/build_manuscript.py export   # also html, pdf, docx

Export needs: python `markdown`, `lxml`, `python-docx` (on PYTHONPATH) and Google Chrome.
"""
import csv
import hashlib
import json
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FIG = HERE / "figures"

SRC = {
    "P": "results/s2_mom_v1/primary_results.json",
    "C": "results/s2_mom_v1/confirmation_results.json",
    "S": "results/s2_mom_v1/sensitivity_results.json",
    "B": "results/s2_mom_v1/blinded_precision.json",
    "E": "results/s2_mom_v1_step_e/step_e_results.json",
    "K": "results/s2_mom_v1_c2/c2_results.json",
    "QP": "data/stage3/s2_mom_v1/checks/pre_run_checks_primary.json",
    "QC": "data/stage3/s2_mom_v1/checks/pre_run_checks_oos.json",
}
DATA = {k: json.loads((ROOT / v).read_text()) for k, v in SRC.items()}

# SHA-256 values as registered (results guide, C2 specification, deviation log, RESEARCH_LOG.md).
REGISTERED = {
    "docs/research/phase3a_momentum_protocol.md": "f1abd954f698307f7aafe234c5d5c9f1681ccc5aadb9cb21e9f8e34d47abd838",
    "docs/research/phase3a_momentum_protocol_addendum1_costs.md": "d12ccaa6fa23143f808b429d75c757a57a853afa42e961a94157d3b772dffefe",
    "docs/research/phase3a_momentum_protocol_addendum1_supplement1.md": "ab28fd1750db3e222819013ef70ff69c4b48d5d5757d51ec5c77e9b6232253b3",
    "docs/research/phase3a_momentum_protocol_addendum1_supplement4.md": "e4617ccb6fa8713ea5a1f82843e5ee1d5fceda84432675c3ce081047b7508b87",
    "docs/research/s2_mom_v1_c2_analysis_spec.md": "78864a4f6fddad86a7b3273e8d8c1e7ab818ed318deb0fdb75cc99e2c5a0c0aa",
    "config/cost_schedules/delivery_nse_eq_s2mom_v1_dated.json": "47a9bad407b87b781c3584986b76b23216c2af33eb2b2f9986d23f710098a10f",
    "data/stage2/universe/univ1_pit_universe.parquet": "2abf457a06abf0e8a0b96c0b0ca0f75ccc07729c0166b1812d7af4646cba9c42",
    "results/s2_mom_v1/blinded_precision.json": "1e26341044f3e46052fdcda53a56721124412e26d5b93156bf274a9a4de5c693",
    "results/s2_mom_v1/primary_results.json": "fe7e95ba97482d6d53faba543d860e4f0d1e50cfa0312d669e910346d41ef857",
    "results/s2_mom_v1/primary_monthly.csv": "f7c8d3ab5a0ef7a08b6a0ca8a12bf26a1f901006c21637cf7886e297b97bb372",
    "results/s2_mom_v1/primary_delta.csv": "2efa04351a6bca10fbf1e6a96d6c5240fb0f2570420185250750b77d5c4fecc9",
    "results/s2_mom_v1/primary_holdings.csv": "3887995763861a2ed17e280f1f975c6fd716dab4923c954d3ca70b91c2d93748",
    "results/s2_mom_v1/sensitivity_results.json": "7d6081d8c4a099f7cd1d7d688791c23180d6977536ae4c7860a08b429ff0c19b",
    "results/s2_mom_v1/confirmation_results.json": "38d1d0a9fbb1d22a19b7912ec4e6285d1dbcb920ffd0e6d99ea19e096c304d92",
    "results/s2_mom_v1/confirmation_monthly.csv": "4d88f385375ad681f85be739b292097e2e898acb6acb71013230c67415a43ce3",
    "results/s2_mom_v1/confirmation_delta.csv": "a462455acb343910a02206ab6af50582eaedef20b0ed6cec81a88f73cbc58b75",
    "results/s2_mom_v1/confirmation_holdings.csv": "96bb174ed2942e7b93630ae445d11817551a44e15b90e5454272ddb79aa825b0",
    "results/s2_mom_v1_step_e/step_e_results.json": "675398488b4a9c11a3f25d70afd32ce3d6f62340e0d9a8a0d3c33df7f7b039e0",
    "results/s2_mom_v1_step_e/primary_step_e_monthly.csv": "3ec30ebdd256234c61bd82292dc01b3acbf582e94eec7f558f06f715b8b3dfd7",
    "results/s2_mom_v1_step_e/primary_step_e_ledger.csv": "75d0fbb0ae2eedda5970836d66c6961f6203e0c3d4bf63134421371dc3397352",
    "results/s2_mom_v1_step_e/confirmation_step_e_monthly.csv": "f43b4a4d9d9898a45ff2d46fa3e0381b1386ec35f4a8e3d92de898d5a2f10638",
    "results/s2_mom_v1_step_e/confirmation_step_e_ledger.csv": "547c7be5adfc82d6fc62b7517b698c14199032d8041a34b84de61ea9a5ac1037",
    "results/s2_mom_v1_c2/c2_results.json": "cf977e8a5efce7ba83ce91bf70ae247ed1aea96c7004f8d03162669097689513",
    "scripts/run_s2_mom_c2.py": "505b2e4ed9d4e1f34dc2e441f2ff73e8399998e4744a6f0b4b7d62e59668b3fa",
    "scripts/run_s2_mom_step_e.py": "997d25ba88111eea113b0f52a8cc16f2948bc59cad689c085dd3e07d0508ae6d",
    "src/stage3/step_e.py": "17e1908270bf544878164ed6b0704af5ba74a7a440055684f78b0cc56c397554",
}

AUDIT = []      # one row per number filled from an artifact
LOC = ["text"]  # where the number currently being filled appears


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def get(path):
    key, *parts = path.strip().split("/")
    o = DATA[key]
    for p in parts:
        o = o[int(p)] if isinstance(o, list) else o[p]
    return o


def fmt(x, f):
    if f == "p3":  # as "p", with 3 significant digits below 0.001
        s = f"{x:.4f}" if x >= 0.001 else format(Decimal(f"{x:.3g}"), "f")
    elif f == "p":  # p-value: 4 decimals, or 2 significant digits when below 0.001
        s = f"{x:.4f}" if x >= 0.001 else format(Decimal(f"{x:.2g}"), "f")
    elif f == "s":
        return str(x)
    else:
        s = format(x, f)
    return s.replace("-", "−")


def val(expr, f, scale=1.0):
    """Format one registered value (or the difference of two) and log it."""
    terms = [t.strip() for t in expr.split(" - ")]
    raw = [get(t) for t in terms]
    x = raw[0] if len(raw) == 1 else raw[0] - raw[1]
    if scale != 1.0:
        x = x * scale
    out = fmt(x, f)
    AUDIT.append({
        "n": len(AUDIT) + 1, "location": LOC[0], "reported": out,
        "kind": "REGISTERED" if len(terms) == 1 else "DERIVED (difference of two registered means; no inference)",
        "source_file": "; ".join(dict.fromkeys(SRC[t.split("/")[0]] for t in terms)),
        "json_path": " - ".join("/".join(t.split("/")[1:]) for t in terms),
        "raw_value": " - ".join(repr(r) for r in raw),
        "scale": scale if f != "s" else "",
    })
    return out


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def ci(base, f="+.3f"):
    return f"{val(base + '/ci90/0', f)} to {val(base + '/ci90/1', f)}"


# ------------------------------------------------------------------ tables

STEPS, PORTS = "ABCD", ("W", "L", "WML", "BM")


def t_ladder(key):
    rows = []
    for s in STEPS:
        r = [s]
        for p in PORTS:
            b = f"{key}/ladder/{s}/{p}"
            r.append(f"{val(b + '/mean_pct', '.3f')} ({val(b + '/t_nw', '.2f')})")
        b = f"{key}/ladder/{s}"
        r += [val(f"{b}/WML/sd_pct", ".2f"), val(f"{b}/WML/max_drawdown_pct", ".1f"),
              "yes" if get(f"{b}/economic_conclusion/momentum_detected") else "no"]
        rows.append(r)
    return table(["Step", "W", "L", "WML", "Benchmark", "WML SD", "WML max. drawdown (%)", "Momentum detected (frozen rule)"], rows)


def test_row(name, what, b, sided, decision, mean="mean", se="se_nw"):
    p = val(f"{b}/p_one_sided" if sided == "one" else f"{b}/p_two_sided", "p")
    c = ci(b) if "ci90" in get(b) else "n/r"
    return [name, what, val(f"{b}/{mean}", "+.4f"), val(f"{b}/{se}", ".4f"), val(f"{b}/t", ".3f"),
            f"{p} ({sided}-sided)", c, decision]


TEST_HEAD = ["Test", "Series", "Mean (% per month)", "NW SE", "t", "p", "90% CI", "Status"]


def t_tests_primary():
    h = "K/holm"
    hd = lambda k: "rejected after Holm" if get(f"{h}/{k}/rejected") else "not rejected after Holm"
    return table(TEST_HEAD, [
        test_row("H1", "δ = WML<sub>A</sub> − WML<sub>D</sub>", "P/H1", "two", "INCONCLUSIVE; NOT RELIABLE (§25, R-span)"),
        test_row("H2a", "WML<sub>A</sub> − WML<sub>B</sub>", "P/step_differences_pct/A-B", "two", hd("H2a")),
        test_row("H2b", "WML<sub>B</sub> − WML<sub>C</sub>", "P/step_differences_pct/B-C", "two", hd("H2b")),
        test_row("H2c", "WML<sub>C</sub> − WML<sub>D</sub>", "P/step_differences_pct/C-D", "two", hd("H2c")),
        test_row("H2d (late)", "W<sub>A</sub> − W<sub>D</sub>", "K/H2d/primary", "one", hd("H2d")),
        test_row("H3", "WML<sub>D</sub>, gross", "E/samples/primary/H3", "one", "supported", "mean_pct", "se_nw_pct"),
        test_row("H4", "W<sub>E</sub> − BM<sub>E</sub>, net, S0", "E/samples/primary/H4", "one", "supported under S0; sensitivity unknown", "mean_pct", "se_nw_pct"),
    ])


def t_tests_confirmation():
    return table(TEST_HEAD, [
        test_row("H1", "δ = WML<sub>A</sub> − WML<sub>D</sub>", "C/H1", "two", "NOT CONFIRMED (opposite sign to primary)"),
        test_row("H2a", "WML<sub>A</sub> − WML<sub>B</sub>", "C/step_differences_pct/A-B", "two", "descriptive; no Holm family in this sample"),
        test_row("H2b", "WML<sub>B</sub> − WML<sub>C</sub>", "C/step_differences_pct/B-C", "two", "descriptive"),
        test_row("H2c", "WML<sub>C</sub> − WML<sub>D</sub>", "C/step_differences_pct/C-D", "two", "descriptive"),
        test_row("H2d (late)", "W<sub>A</sub> − W<sub>D</sub>", "K/H2d/confirmation", "one", val("K/H2d/confirmation_status", "s")),
        test_row("H3", "WML<sub>D</sub>, gross", "E/samples/confirmation/H3", "one", "not supported", "mean_pct", "se_nw_pct"),
        ["H4", "W<sub>E</sub> − BM<sub>E</sub>, net, S0", "not run", "", "", "", "", "not run: H3 not supported in this sample"],
    ])


def t_multiple():
    names = {"H2a": "WML<sub>A</sub> − WML<sub>B</sub>", "H2b": "WML<sub>B</sub> − WML<sub>C</sub>",
             "H2c": "WML<sub>C</sub> − WML<sub>D</sub>", "H2d": "W<sub>A</sub> − W<sub>D</sub>",
             "H3": "WML<sub>D</sub> > 0", "H4": "W<sub>E</sub> − BM<sub>E</sub> > 0 (S0)"}
    order = sorted(names, key=lambda k: get(f"K/benjamini_hochberg/{k}/p"))
    rows = []
    for k in order:
        in_holm = k in DATA["K"]["holm"]
        rows.append([k, names[k], val(f"K/benjamini_hochberg/{k}/sided", "s"), val(f"K/benjamini_hochberg/{k}/p", "p3"),
                     val(f"K/holm/{k}/p_holm", "p3") if in_holm else "not in family",
                     ("yes" if get(f"K/holm/{k}/rejected") else "no") if in_holm else "fixed sequence",
                     val(f"K/benjamini_hochberg/{k}/q", "p3")])
    return table(["Hypothesis", "Series", "Sided", "Raw p", "Holm-adjusted p (m = 4)", "Rejected at family α = 0.05", "BH q (m = 6)"], rows)


def t_costs():
    rows = []
    for smp, lab in (("primary", "Primary"), ("confirmation", "Confirmation")):
        for sc in ("S0", "S1", "S2", "S3", "S4"):
            b = f"E/samples/{smp}/scenarios/{sc}"
            x = lambda k: val(f"{b}/{k}", ".3f", 100)
            rows.append([lab, sc, f"{get(b + '/slippage_bps/1-200')} / {get(b + '/slippage_bps/201-500')}",
                         x("cost_W"), x("cost_BM"), x("net_W"), x("net_BM"), x("net_excess_W_over_BM"),
                         x("hypothetical_net_WML")])
    return table(["Sample", "Scenario", "One-way slippage, rank 1–200 / 201–500 (bps)", "Cost of W", "Cost of BM",
                  "Net W", "Net BM", "Net excess W − BM", "Hypothetical net WML"], rows)


def t_halves():
    rows = []
    for hb, lab in (("primary_half_1", "First half (Jul 2012 – Mar 2017)"), ("primary_half_2", "Second half (Apr 2017 – Dec 2021)")):
        for s, p in (("A", "W"), ("D", "W"), ("A", "WML"), ("D", "WML"), ("D", "BM")):
            b = f"K/blocks/{hb}/ladder/{s}/{p}"
            rows.append([lab, f"{p}<sub>{s}</sub>", val(f"K/blocks/{hb}/n", "d"), val(b + "/mean_pct", ".3f"),
                         val(b + "/t_nw", ".2f"), val(b + "/p_two_sided", "p"), val(b + "/worst_month_pct", ".2f")])
        b = f"K/blocks/{hb}/delta"
        rows.append([lab, "δ = WML<sub>A</sub> − WML<sub>D</sub>", val(b + "/n", "d"), val(b + "/mean", "+.3f"),
                     val(b + "/t", ".2f"), val(b + "/p_two_sided", "p"), "—"])
    return table(["Block", "Series", "Months", "Mean (% per month)", "NW t (lag 3)", "Two-sided p", "Worst month (%)"], rows)


def t_sensitivity():
    labs = {"R_SPAN": "R-span: special-session spans use the raw two-session return",
            "R_GAP": "R-gap: raw multi-session gap return", "R_MISS_RAW": "R-miss: missing holding days, raw return",
            "R_MISS_ZERO": "R-miss: missing holding days, zero return", "R_DELIST_ZERO": "R-delist: 0% for all delistings",
            "R_DELIST_MINUS100": "R-delist: −100% for non-voluntary delistings"}
    yn = lambda v: "yes" if v else "no"
    rows = [["Primary specification", val("P/H1/mean", "+.4f"), val("P/H1/se_nw", ".4f"), val("P/H1/t", ".3f"), val("P/H1/p_two_sided", "p"), "—", "—"]]
    for k, lab in labs.items():
        b = f"S/sensitivity/{k}"
        rows.append([lab, val(b + "/H1/mean", "+.4f"), val(b + "/H1/se_nw", ".4f"), val(b + "/H1/t", ".3f"),
                     val(b + "/H1/p_two_sided", "p"), yn(get(b + "/H1_sign_changed")),
                     yn(get(b + "/H3_sign_changed") or get(b + "/H3_significance_changed"))])
    return table(["Treatment", "Mean δ (% per month)", "NW SE", "t", "Two-sided p", "H1 sign changed", "H3 sign or significance changed"], rows)


def t_reverse():
    rows = []
    for k, lab in (("R_POOL", "Step D with the survivor pool restored"), ("R_RETURNS", "Step D with the step-A return rule restored")):
        b = f"S/reverse_ladder/{k}"
        rows.append([lab, val(b + "/mean", "+.4f"), val(b + "/se_nw", ".4f"), val(b + "/t", ".3f"), val(b + "/p_two_sided", "p"), ci(b)])
    return table(["Reverse-ladder variant (primary sample)", "Mean difference in WML (% per month)", "NW SE", "t", "Two-sided p", "90% CI"], rows)


def t_pooled():
    rows = []
    for s in STEPS:
        r = [s]
        for p in PORTS:
            b = f"K/blocks/pooled/ladder/{s}/{p}"
            r.append(f"{val(b + '/mean_pct', '.3f')} ({val(b + '/t_nw', '.2f')})")
        rows.append(r)
    b = "K/blocks/pooled/delta"
    tail = (f"\n\nPooled δ: mean {val(b + '/mean', '+.4f')}% per month, NW SE {val(b + '/se_nw', '.4f')}, "
            f"t = {val(b + '/t', '.3f')}, two-sided p = {val(b + '/p_two_sided', 'p')}, 90% CI {ci(b)} "
            f"({val(b + '/n', 'd')} months, lag {val('K/blocks/pooled/lag', 'd')}).")
    return table(["Step", "W", "L", "WML", "Benchmark"], rows) + tail


def t_shape():
    rows = []
    for blk, lab in (("primary", "Primary"), ("confirmation", "Confirmation")):
        for s in ("A", "D"):
            for p in PORTS:
                b = f"K/blocks/{blk}/ladder/{s}/{p}"
                rows.append([lab, s, p, val(b + "/mean_pct", ".3f"), val(b + "/sd_pct", ".2f"), val(b + "/skewness", ".2f"),
                             val(b + "/worst_month_pct", ".2f"), val(b + "/worst_month", "s")])
    return table(["Sample", "Step", "Portfolio", "Mean (% per month)", "SD", "Skewness", "Worst month (%)", "Month"], rows)


def t_hashes():
    rows = []
    for rel, reg in REGISTERED.items():
        actual = sha(rel)
        assert actual == reg, f"hash differs from the registered value: {rel}"
        rows.append([f"`{rel}`", f"`{reg}`"])
    return table(["File", "SHA-256 (registered; re-computed and matched when this manuscript was built)"], rows)


TABLES = {
    "LADDER_P": lambda: t_ladder("P"), "TESTS_P": t_tests_primary,
    "LADDER_C": lambda: t_ladder("C"), "TESTS_C": t_tests_confirmation,
    "MULTIPLE": t_multiple, "COSTS": t_costs, "HALVES": t_halves, "SENS": t_sensitivity,
    "REVERSE": t_reverse, "POOLED": t_pooled, "SHAPE": t_shape, "HASHES": t_hashes,
}


def render():
    def sub(m):
        parts = [p.strip() for p in m.group(1).split("|")]
        if parts[0].startswith("@"):
            LOC[0] = "table " + parts[0][1:]
            out = TABLES[parts[0][1:]]()
            LOC[0] = "text"
            return out
        scale = 1.0
        if len(parts) == 3:
            scale = float(parts[1][1:])
        return val(parts[0], parts[-1], scale)
    return re.sub(r"\{\{(.+?)\}\}", sub, (HERE / "manuscript.template.md").read_text())


# ------------------------------------------------------------------ figures

def rows_of(rel):
    with open(ROOT / rel, newline="") as fh:
        return list(csv.DictReader(fh))


def figures():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    BLUE, ORANGE, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#0b0b0b", "#898781", "#e4e3df"
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                         "xtick.color": INK, "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.6,
                         "axes.axisbelow": True, "legend.frameon": False, "savefig.dpi": 300, "savefig.bbox": "tight"})
    FIG.mkdir(exist_ok=True)
    P, C, E, K = DATA["P"], DATA["C"], DATA["E"], DATA["K"]
    xs = range(4)

    def bars(ax, a, b, la, lb, labels):
        w = 0.36
        for off, v, col, lab in ((-w / 2 - 0.01, a, BLUE, la), (w / 2 + 0.01, b, ORANGE, lb)):
            r = ax.bar([x + off for x in range(len(v))], v, w, color=col, label=lab)
            ax.bar_label(r, fmt="%.2f", padding=2, fontsize=7.5, color=INK)
        ax.set_xticks(range(len(labels)), labels)
        ax.axhline(0, color=MUTED, lw=0.8)

    # Figure 1: gross WML and W across the ladder
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.1), sharey=True)
    for ax, port, title in ((axs[0], "WML", "(a) Winner-minus-loser, gross"), (axs[1], "W", "(b) Winner portfolio, gross")):
        bars(ax, [P["ladder"][s][port]["mean_pct"] for s in STEPS], [C["ladder"][s][port]["mean_pct"] for s in STEPS],
             "Primary (Jul 2012 – Dec 2021)", "Confirmation (Jan 2022 – Aug 2026)", [f"Step {s}" for s in STEPS])
        ax.set_title(title, fontsize=9, loc="left")
    axs[0].set_ylabel("Mean return (% per month)")
    axs[0].set_ylim(0, 3.2)
    axs[0].legend(loc="upper right", fontsize=7.5)
    fig.savefig(FIG / "fig1_ladder_gross.png"); plt.close(fig)

    # Figure 2: delta and H2d, primary against confirmation, 90% intervals
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
    for ax, title, pr, cf in ((axs[0], "(a) δ = WML$_A$ − WML$_D$ (H1)", P["H1"], C["H1"]),
                              (axs[1], "(b) W$_A$ − W$_D$ (H2d, executed late)", K["H2d"]["primary"], K["H2d"]["confirmation"])):
        for x, d, col in ((0, pr, BLUE), (1, cf, ORANGE)):
            ax.plot([x, x], d["ci90"], color=col, lw=2, solid_capstyle="round")
            ax.plot(x, d["mean"], "o", ms=8, color=col, mec="white", mew=1.5)
            ax.annotate(f"{d['mean']:+.3f}".replace("-", "\u2212"), (x, d["mean"]), xytext=(10, 0), textcoords="offset points", va="center", fontsize=8)
        ax.axhspan(-0.10, 0.10, color=MUTED, alpha=0.18, lw=0)
        ax.axhline(0, color=MUTED, lw=0.8)
        ax.set_xticks([0, 1], ["Primary", "Confirmation"]); ax.set_xlim(-0.6, 1.6)
        ax.set_title(title, fontsize=9, loc="left")
    axs[0].set_ylabel("Mean difference (% per month)")
    axs[1].text(-0.55, 0.13, "±0.10 reference band", fontsize=7, color="#52514e")
    fig.savefig(FIG / "fig3_delta_primary_vs_confirmation.png"); plt.close(fig)

    # Figure 3: net excess return of W over the benchmark under S0-S4
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    sc = ["S0", "S1", "S2", "S3", "S4"]
    for smp, col, lab in (("primary", BLUE, "Primary"), ("confirmation", ORANGE, "Confirmation (descriptive; H4 not run)")):
        s = E["samples"][smp]["scenarios"]
        x = [s[k]["slippage_bps"]["1-200"] for k in sc]
        y = [100 * s[k]["net_excess_W_over_BM"] for k in sc]
        ax.plot(x, y, "-o", color=col, lw=2, ms=6, mec="white", mew=1.2, label=lab)
        for xi, yi in zip(x, y):
            ax.annotate(f"{yi:.2f}", (xi, yi), xytext=(0, 7), textcoords="offset points", ha="center", fontsize=7.5)
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_xticks([0, 5, 10, 25, 50], ["S0\n0", "S1\n5", "S2\n10", "S3\n25", "S4\n50"])
    ax.set_xlabel("Scenario and one-way slippage, rank 1–200 (bps)")
    ax.set_ylabel("Net excess return, W − benchmark\n(% per month)")
    ax.set_ylim(-0.08, 0.68); ax.legend(loc="upper right", fontsize=7.5)
    fig.savefig(FIG / "fig2_cost_sensitivity.png"); plt.close(fig)

    # Figure 4: halves of the primary sample
    fig, ax = plt.subplots(figsize=(5.2, 3.1))
    h = [K["blocks"]["primary_half_1"]["ladder"], K["blocks"]["primary_half_2"]["ladder"]]
    bars(ax, [x["A"]["WML"]["mean_pct"] for x in h], [x["D"]["WML"]["mean_pct"] for x in h],
         "Step A (shortcut pipeline)", "Step D (corrected pipeline)",
         ["First half\nJul 2012 – Mar 2017", "Second half\nApr 2017 – Dec 2021"])
    ax.set_ylabel("Mean gross WML (% per month)"); ax.set_ylim(0, 1.9); ax.legend(loc="upper left", fontsize=7.5)
    fig.savefig(FIG / "fig4_primary_halves.png"); plt.close(fig)

    # Figure 5: cumulative sums of the registered monthly differences (descriptive)
    months, delta, h2d = [], [], []
    for smp in ("primary", "confirmation"):
        d = rows_of(f"results/s2_mom_v1/{smp}_delta.csv")
        m = {(r["holding_month"], r["step"]): float(r["W"]) for r in rows_of(f"results/s2_mom_v1/{smp}_monthly.csv")}
        for r in d:
            months.append(r["holding_month"]); delta.append(float(r["delta"]))
            h2d.append(100 * (m[(r["holding_month"], "A")] - m[(r["holding_month"], "D")]))
    cum = lambda v: [sum(v[: i + 1]) for i in range(len(v))]
    fig, ax = plt.subplots(figsize=(7.0, 3.2))
    x = list(range(len(months)))
    for y, col, lab in ((cum(h2d), ORANGE, "W$_A$ − W$_D$"), (cum(delta), BLUE, "δ = WML$_A$ − WML$_D$")):
        ax.plot(x, y, color=col, lw=2, label=lab)
        ax.annotate(lab, (x[-1], y[-1]), xytext=(5, 0), textcoords="offset points", va="center", fontsize=8)
    b = months.index("2022-01")
    ax.axvline(b - 0.5, color=MUTED, lw=0.8, ls="--")
    ax.text(b + 1, ax.get_ylim()[1] * 0.93, "confirmation sample →", fontsize=7.5, color="#52514e")
    ax.axhline(0, color=MUTED, lw=0.8)
    tk = [i for i, m in enumerate(months) if m.endswith("-01") and int(m[:4]) % 2 == 0]
    ax.set_xticks(tk, [months[i][:4] for i in tk]); ax.set_xlim(0, len(x) + 22)
    ax.set_ylabel("Cumulative sum of monthly differences\n(percentage points)")
    fig.savefig(FIG / "fig5_cumulative_differences.png"); plt.close(fig)


# ------------------------------------------------------------------ checks

MINUS = "−"
# Values stated in the manuscript brief; each must appear exactly as rendered from the artifacts.
EXPECTED = ["+0.5769", "0.1457", "3.959", "0.000038", "+0.337 to +0.817", "+1.2233", "0.2785", "4.393", "0.0000056",
            "+0.765 to +1.681", MINUS + "0.0587", "0.7806", "+0.6750", "0.0138", "0.345", "0.636", "1.504", "0.010",
            "CONFIRMED", "INCONCLUSIVE", "NOT RELIABLE", "DEV-2", "DEV-1", "not blind", "not confirmatory",
            "not a claim of exhaustive uniqueness", "biased by construction", "executed after the main results were known"]
# Claim audit: wording that must not appear at all, as whole words or phrases.
FORBIDDEN = ["proves", "proven", "proof", "always", "universal", "universally", "definitive", "definitively",
             "momentum is an artifact", "is an artifact", "momentum does not exist", "does not exist", "is fake",
             "survivorship bias explains momentum", "explains momentum", "explains everything", "no previous study",
             "no prior study", "first study", "first to", "novel", "novelty", "groundbreaking", "unique", "TODO"]
# "never" is allowed only in these factual descriptions of a rule or of file handling.
NEVER_ALLOWED = ["if it never trades again", "were never filled in afterwards"]
REQUIRED = ["H2d is the strongest methodological finding", "inflation of measured winner-portfolio returns caused by the tested shortcuts",
            "it is not evidence that momentum is produced by the shortcuts", "temporally unstable",
            "we make no general profitability claim from it", "They are not blind and not confirmatory",
            "No result was computed or seen for any analysis marked \"Not executed\"",
            "H3 is supported in the primary sample, but the confirmation sample does not provide significant evidence for the same effect",
            "Within the literature reviewed for this study, we did not identify a directly comparable design combining the specific A–D correction ladder, the separate transaction-cost layer, and an untouched chronological confirmation sample.",
            "remains unresolved", "Methodological reference added during manuscript preparation"]


def claim_audit(md):
    """Every occurrence of the audited wording, with its sentence. Returns (lines for the report, problems)."""
    lines, bad = [], []
    for term in FORBIDDEN + ["never"]:
        hits = [m.start() for m in re.finditer(r"(?<![\w])" + re.escape(term) + r"(?![\w])", md, re.I)]
        if term == "never":
            for h in hits:
                ctx = re.sub(r"\s+", " ", md[max(0, h - 90):h + 60])
                okay = any(a in md[max(0, h - 40):h + 60] for a in NEVER_ALLOWED)
                lines.append(f"| never | 1 | {'kept: factual description of a rule or of file handling' if okay else 'PROBLEM'} | …{ctx}… |")
                if not okay:
                    bad.append(("never", ctx))
        else:
            lines.append(f"| {term} | {len(hits)} | {'absent' if not hits else 'PROBLEM'} | |")
            bad += [(term, md[max(0, h - 60):h + 40]) for h in hits]
    return lines, bad


def crossrefs(md):
    """Tables and figures are numbered in order of first appearance; every reference points at something that exists."""
    body = md.split("\n## References")[0] + md.split("\n## Appendix")[1]
    problems = []
    for kind, pat in (("Table", r"Table (\d+)"), ("Appendix Table", r"Table (A\d+)"), ("Figure", r"Figure (\d+)")):
        caps = re.findall(r"\*\*" + pat + r"\.", md)
        want = [(f"A{i}" if kind.startswith("App") else str(i)) for i in range(1, len(caps) + 1)]
        if caps != want:
            problems.append(f"{kind} captions out of order: {caps}")
        first = []
        for m in re.finditer(r"(?:Tables?|Figures?) ((?:A?\d+)(?:(?:, | and )A?\d+)*)" if kind != "Figure" else r"Figures? (\d+)", md):
            if (kind == "Figure") != m.group(0).startswith("Figure"):
                continue
            for n in re.findall(r"A?\d+", m.group(1)):
                if n.startswith("A") != kind.startswith("App"):
                    continue
                if n not in caps:
                    problems.append(f"reference to missing {kind} {n}")
                if n not in first:
                    first.append(n)
        if first != want:
            problems.append(f"{kind} first mentions out of order: {first}")
    heads = set(re.findall(r"^#{2,3} (\d+(?:\.\d+)?)\.? ", md, re.M))
    for n in re.findall(r"Sections? (\d+(?:\.\d+)?)", md):
        if n not in heads:
            problems.append(f"reference to missing Section {n}")
    for f in re.findall(r"\]\((figures/[^)]+)\)", md):
        if not (HERE / f).exists():
            problems.append(f"missing figure file {f}")
    return problems


def checks(md):
    done = []

    def ok(name, cond, detail=""):
        assert cond, f"CHECK FAILED: {name} {detail}"
        done.append(name)

    low = md.lower()
    for e in EXPECTED:
        ok(f"expected text present: {e}", e in md)
    lines, bad = claim_audit(md)
    ok("claim audit: no unsupported wording", not bad, str(bad))
    (HERE / "claim_audit.md").write_text(
        "# S2-MOM-v1 manuscript — claim audit\n\nGenerated by `build_manuscript.py` from `manuscript.md`. "
        "Whole-word, case-insensitive search of the complete manuscript.\n\n| Term | Occurrences | Result | Context |\n|---|---|---|---|\n"
        + "\n".join(lines) + "\n\nRequired statements, each found verbatim:\n\n" + "\n".join(f"- {r}" for r in REQUIRED) + "\n")
    for r in REQUIRED:
        ok(f"required statement present: {r[:60]}", r in md)
    xr = crossrefs(md)
    ok("cross-references: numbering in order of first appearance, all targets exist", not xr, str(xr))
    ok("no derived numbers in the manuscript", all(a["kind"] == "REGISTERED" for a in AUDIT))
    ok("no unfilled placeholder", "{{" not in md)
    for rel, reg in REGISTERED.items():
        ok(f"hash matches registered: {rel}", sha(rel) == reg)
    for k in ("P", "C", "S", "B", "E", "K"):
        ok(f"source hash in manuscript: {SRC[k]}", REGISTERED[SRC[k]] in md)

    P, C, K, E = DATA["P"], DATA["C"], DATA["K"], DATA["E"]
    ok("months: 114 + 56 = 170", P["H1"]["n"] + C["H1"]["n"] == K["blocks"]["pooled"]["n"] == 170)
    ok("halves: 57 + 57 = 114", K["blocks"]["primary_half_1"]["n"] + K["blocks"]["primary_half_2"]["n"] == P["H1"]["n"])
    ok("Holm family has 4 tests", K["holm"]["m"] == 4 == sum(k.startswith("H") for k in K["holm"]))
    ok("BH family has 6 tests", K["benjamini_hochberg"]["m"] == 6 == sum(k.startswith("H") for k in K["benjamini_hochberg"]))
    ok("H2d rejected after Holm", K["holm"]["H2d"]["rejected"] and K["holm"]["H2d"]["p_holm"] < 0.05)
    ok("H2d BH q below 0.05", K["benjamini_hochberg"]["H2d"]["q"] < 0.05)
    ok("H2d confirmation status", K["H2d"]["confirmation_status"] == "CONFIRMED")
    ok("H1 primary inconclusive", P["H1"]["decision"] == "INCONCLUSIVE")
    ok("H1 opposite signs", P["H1"]["mean"] < 0 < C["H1"]["mean"])
    ok("H1 not reliable via R-span only", DATA["S"]["reliability"]["sensitivity_treatments_that_change_H1_or_H3"] == ["R_SPAN"])
    ok("H4 not run in confirmation", "NOT RUN" in E["samples"]["confirmation"]["H4"]["status"])
    t7 = re.search(r"\*\*Table 7\.(.+?)\n\n(?=[^|])", md, re.S).group(1)
    n = lambda tag: sum(1 for line in t7.splitlines() if line.startswith("|") and f"| {tag} |" in line)
    ok("Table 7: 17 not executed", n("Not executed") == 17, str(n("Not executed")))
    ok("Table 7: 7 executed late", n("Executed late") == 7, str(n("Executed late")))
    ok("Table 7 totals stated", f"{n('Executed as planned')} executed as planned, 7 executed late and 17 not executed" in md)

    # independent recomputation of plain means from the registered monthly files
    for smp, res in (("primary", P), ("confirmation", C)):
        m = rows_of(f"results/s2_mom_v1/{smp}_monthly.csv")
        col = lambda s, p: [float(r[p]) for r in m if r["step"] == s]
        mean = lambda v: sum(v) / len(v)
        h2d = 100 * mean([a - d for a, d in zip(col("A", "W"), col("D", "W"))])
        dl = 100 * mean([a - d for a, d in zip(col("A", "WML"), col("D", "WML"))])
        ok(f"{smp}: mean W_A - W_D recomputed", abs(h2d - K["H2d"][smp]["mean"]) < 1e-9)
        ok(f"{smp}: mean delta recomputed", abs(dl - res["H1"]["mean"]) < 1e-9)
        ok(f"{smp}: delta file agrees", abs(mean([float(r["delta"]) for r in rows_of(f'results/s2_mom_v1/{smp}_delta.csv')]) - dl) < 1e-9)
        for s in STEPS:
            for p in PORTS:
                ok(f"{smp}: mean {p}_{s} recomputed", abs(100 * mean(col(s, p)) - res["ladder"][s][p]["mean_pct"]) < 1e-9)
    m = rows_of("results/s2_mom_v1/primary_monthly.csv")
    d = [100 * float(r["WML"]) for r in m if r["step"] == "D"]
    ok("half 1 D WML recomputed", abs(sum(d[:57]) / 57 - K["blocks"]["primary_half_1"]["ladder"]["D"]["WML"]["mean_pct"]) < 1e-9)
    ok("half 2 D WML recomputed", abs(sum(d[57:]) / 57 - K["blocks"]["primary_half_2"]["ladder"]["D"]["WML"]["mean_pct"]) < 1e-9)
    for a in AUDIT:
        ok(f"audited value #{a['n']} present", a["reported"] in md)
    for f in sorted(FIG.glob("*.png")):
        ok(f"figure referenced: {f.name}", f.name in md)
    return done


def word_count(md):
    body = md.split("\n## References")[0]
    body = "\n".join(l for l in body.splitlines() if not l.startswith("|") and not l.startswith("!["))
    return len(re.findall(r"[A-Za-z0-9α-ω][\w'’.%\-]*", re.sub(r"<[^>]+>", "", body)))


# ------------------------------------------------------------------ export

CSS = """
@page { size: A4; margin: 22mm 20mm; }
body { font-family: Georgia, 'Times New Roman', serif; font-size: 10.5pt; line-height: 1.42; color: #111; max-width: 170mm; margin: auto; }
h1 { font-size: 17pt; line-height: 1.25; margin-bottom: 4pt; } h2 { font-size: 13pt; margin-top: 20pt; } h3 { font-size: 11pt; }
table { border-collapse: collapse; width: 100%; font-size: 8pt; margin: 8pt 0 12pt; font-family: Helvetica, Arial, sans-serif; }
th { border-top: 1.2pt solid #111; border-bottom: 0.8pt solid #111; text-align: left; padding: 3pt 4pt; vertical-align: bottom; }
td { border-bottom: 0.3pt solid #bbb; padding: 2.5pt 4pt; vertical-align: top; } tr { page-break-inside: avoid; }
code { font-size: 7.6pt; word-break: break-all; } pre { background: #f5f5f3; padding: 6pt; font-size: 8pt; white-space: pre-wrap; }
img { max-width: 100%; display: block; margin: 10pt auto 4pt; } blockquote { margin-left: 12pt; color: #333; }
h2, h3 { page-break-after: avoid; }
"""


def export(md):
    import markdown
    html = markdown.markdown(md, extensions=["tables", "fenced_code"])
    (HERE / "manuscript.html").write_text(
        f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>S2-MOM-v1 manuscript</title><style>{CSS}</style></head><body>{html}</body></html>")
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={HERE / 'manuscript.pdf'}", (HERE / "manuscript.html").as_uri()],
                   check=True, capture_output=True, timeout=180)

    import docx
    import lxml.html
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Mm, Pt
    doc = docx.Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(210), Mm(297)
    sec.left_margin = sec.right_margin = Mm(22); sec.top_margin = sec.bottom_margin = Mm(22)
    doc.styles["Normal"].font.name = "Times New Roman"; doc.styles["Normal"].font.size = Pt(11)

    def runs(par, node, bold=False, italic=False, code=False, sub=False, size=None):
        def add(text):
            if text:
                r = par.add_run(re.sub(r"\s*\n\s*", " ", text))
                r.bold, r.italic, r.font.subscript = bold or None, italic or None, sub or None
                if code:
                    r.font.name, r.font.size = "Courier New", Pt(8 if size is None else size)
                elif size:
                    r.font.size = Pt(size)
        add(node.text)
        for ch in node:
            if ch.tag == "br":
                par.add_run().add_break()
            else:
                runs(par, ch, bold or ch.tag in ("strong", "b"), italic or ch.tag in ("em", "i"),
                     code or ch.tag == "code", sub or ch.tag == "sub", size)
            add(ch.tail)

    for el in lxml.html.fromstring(html if html.lstrip().startswith("<div") else f"<div>{html}</div>"):
        if el.tag in ("h1", "h2", "h3", "h4"):
            runs(doc.add_heading(level=int(el.tag[1]) - 1), el)
        elif el.tag == "p":
            img = el.find("img")
            if img is not None:
                doc.add_picture(str(HERE / img.get("src")), width=Mm(160))
                doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                runs(doc.add_paragraph(), el)
        elif el.tag in ("ul", "ol"):
            for li in el.iter("li"):
                runs(doc.add_paragraph(style="List Bullet" if el.tag == "ul" else "List Number"), li)
        elif el.tag == "blockquote":
            for p in el.iter("p"):
                par = doc.add_paragraph(); par.paragraph_format.left_indent = Mm(8); runs(par, p, italic=True)
        elif el.tag == "pre":
            par = doc.add_paragraph()
            r = par.add_run(el.text_content().rstrip()); r.font.name, r.font.size = "Courier New", Pt(8)
        elif el.tag == "table":
            trs = list(el.iter("tr"))
            t = doc.add_table(rows=len(trs), cols=max(len(tr) for tr in trs)); t.style = "Table Grid"
            for i, tr in enumerate(trs):
                for j, c in enumerate(tr):
                    par = t.cell(i, j).paragraphs[0]
                    runs(par, c, bold=c.tag == "th", size=7.5)
            doc.add_paragraph()
    doc.save(HERE / "manuscript.docx")


if __name__ == "__main__":
    md = render()
    (HERE / "manuscript.md").write_text(md)
    figures()
    with open(HERE / "number_audit.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(AUDIT[0]))
        w.writeheader(); w.writerows(AUDIT)
    passed = checks(md)
    (HERE / "consistency_check_log.txt").write_text("\n".join(f"PASS  {c}" for c in passed) + f"\n\n{len(passed)} checks passed\n")
    print(f"numbers filled from artifacts: {len(AUDIT)} "
          f"({sum(a['kind'] == 'REGISTERED' for a in AUDIT)} registered, {sum(a['kind'] != 'REGISTERED' for a in AUDIT)} derived)")
    print(f"checks passed: {len(passed)}")
    print(f"words (title to conclusion, tables excluded): {word_count(md)}")
    if sys.argv[1:] == ["export"]:
        export(md)
        print("exported: manuscript.html, manuscript.pdf, manuscript.docx")

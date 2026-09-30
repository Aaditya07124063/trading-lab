"""Intraday research run: ORB vs open-to-close benchmark with a
dev / validation / final-OOS split. Costs come from config/intraday_costs.json.
    python3 run_intraday.py RELIANCEm15.csv            # ORB-30 on 15m, real costs
    python3 run_intraday.py RELIANCEh1.csv --range 60  # engine check on 1h data
    python3 run_intraday.py RELIANCEm15.csv --gross    # zero costs, labelled GROSS"""

import argparse

from src.intraday.costs import CostModel
from src.intraday.engine import EngineConfig
from src.intraday.research import format_study, run_study
from src.registry.experiments import log_trial

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--range", type=int, default=30, help="opening range minutes")
    ap.add_argument("--cutoff", default="14:30", help="no entry fills after this time")
    ap.add_argument("--no-short", action="store_true")
    ap.add_argument("--gross", action="store_true", help="zero costs (NOT a realistic result)")
    a = ap.parse_args()

    costs = CostModel.zero() if a.gross else CostModel.load()
    cfg = EngineConfig(entry_cutoff=a.cutoff, allow_short=not a.no_short)
    st = run_study(a.file, costs, a.range, cfg)
    log_trial("intraday_orb", {"range_minutes": a.range, "cutoff": a.cutoff, "short": not a.no_short,
                               "costs": costs.name}, a.file,
              {"return_pct": st["summary"]["return_pct"], "vs_bench": st["vs"]["strategy_minus_benchmark"]}, "cli")
    print(format_study(st))
    print(f"\nSaved -> {st['output_dir']}")

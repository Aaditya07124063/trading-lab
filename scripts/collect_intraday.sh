#!/bin/bash
# Trading Lab intraday collector - invoked by launchd (com.tradinglab.intraday-collector).
# Scope: ONLY this project directory. No sudo, no secrets, no deletions.
# Collection is append-only; every attempt is logged to data/raw/collection_log.jsonl.
set -u
PROJECT="/Users/aadityaadhikari/Desktop/trading-lab"
PY="/opt/anaconda3/bin/python3"
cd "$PROJECT" || exit 2
mkdir -p logs
{
  echo "=== $(date '+%Y-%m-%d %H:%M:%S %z') collector start"
  "$PY" update_intraday.py
  rc=$?
  echo "=== $(date '+%Y-%m-%d %H:%M:%S %z') collector exit code $rc (0 = all OK, 1 = some dataset failed/rejected - see collection_log.jsonl)"
} >> logs/collector.log 2>&1
exit $rc

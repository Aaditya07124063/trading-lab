"""One place for every setting. Change here, applies everywhere."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"

CAPITAL = 100_000        # starting fake money (Rs 1 lakh)
COST_PER_SIDE = 0.001    # 0.1% broker cost on every buy and every sell
# Yahoo tickers for the Indian instruments the lab tracks (no API key needed)
YAHOO_SYMBOLS = {
    "NIFTY50":  "^NSEI",
    "SENSEX":   "^BSESN",
    "RELIANCE": "RELIANCE.NS",
    "TCS":      "TCS.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "INFY":     "INFY.NS",
}

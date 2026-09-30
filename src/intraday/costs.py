"""Configurable intraday cost model. NO broker's real rates live in code:
a schedule is loaded from config/intraday_costs.json (fill it from your
broker's published charge sheet). All pct fields are FRACTIONS of turnover
(0.00025 = 0.025%)."""

import json
from dataclasses import dataclass, fields, asdict

from src.config import BASE_DIR

COST_FILE = BASE_DIR / "config" / "intraday_costs.json"


@dataclass(frozen=True)
class CostModel:
    name: str
    brokerage_flat: float        # Rs per executed order
    brokerage_pct: float         # fraction of order turnover
    brokerage_mode: str          # "min" (lower of flat/pct), "flat", or "pct"
    stt_sell_pct: float          # STT, charged on the SELL side only
    exchange_pct: float          # exchange transaction charge, both sides
    sebi_pct: float              # SEBI turnover fee, both sides
    stamp_buy_pct: float         # stamp duty, BUY side only
    gst_pct: float               # GST on (brokerage + exchange + sebi)
    slippage_bps: float          # adverse fill slippage per side, basis points

    def __post_init__(self):
        if self.brokerage_mode not in ("min", "flat", "pct"):
            raise ValueError(f"brokerage_mode must be min/flat/pct, got {self.brokerage_mode}")
        for f in fields(self):
            v = getattr(self, f.name)
            if f.type is float and (v is None or v < 0):
                raise ValueError(f"cost field '{f.name}' must be set and >= 0 (got {v})")

    @classmethod
    def zero(cls):
        """Explicitly cost-free - for engine tests and GROSS reference runs only."""
        return cls("zero-cost (GROSS - not realistic)", 0, 0, "flat", 0, 0, 0, 0, 0, 0)

    @classmethod
    def load(cls, path=None):
        path = path or COST_FILE
        if not path.exists():
            raise FileNotFoundError(
                f"{path} missing. Copy config/intraday_costs.example.json to "
                f"{path.name} and fill every rate from your broker's charge sheet.")
        return cls(**json.load(open(path)))

    def slip(self, price, side):
        """Adverse fill: buys pay more, sells receive less."""
        s = self.slippage_bps / 10_000
        return price * (1 + s) if side == "buy" else price * (1 - s)

    def charges(self, side, turnover):
        """Rs charges for one executed order of `turnover` Rs on `side`."""
        flat, pct = self.brokerage_flat, self.brokerage_pct * turnover
        brokerage = {"flat": flat, "pct": pct, "min": min(flat, pct)}[self.brokerage_mode]
        stt = self.stt_sell_pct * turnover if side == "sell" else 0.0
        exchange = self.exchange_pct * turnover
        sebi = self.sebi_pct * turnover
        stamp = self.stamp_buy_pct * turnover if side == "buy" else 0.0
        gst = self.gst_pct * (brokerage + exchange + sebi)
        return {"brokerage": brokerage, "stt": stt, "exchange": exchange, "sebi": sebi,
                "stamp": stamp, "gst": gst}

    def describe(self):
        return asdict(self)

"""Opening Range Breakout.

Range = every bar whose start time lies in [session_open, session_open +
range_minutes). It is only known once the LAST range bar has closed; bars
must tile the window exactly (else the day is skipped - no partial ranges).
Signal: the first later bar that CLOSES above OR_HIGH -> long (+1), below
OR_LOW -> short (-1). One signal per day; the engine fills it at the next
bar's open and squares off at 15:15."""

import pandas as pd


class ORB:
    def __init__(self, range_minutes=30, timeframe_minutes=15, session_open="09:15",
                 allow_short=True):
        if range_minutes % timeframe_minutes:
            raise ValueError(f"{range_minutes}-min range cannot be built from "
                             f"{timeframe_minutes}-min bars")
        self.range_minutes = range_minutes
        self.tf = timeframe_minutes
        self.allow_short = allow_short
        t0 = pd.Timestamp(f"2000-01-01 {session_open}")
        self.range_times = [(t0 + pd.Timedelta(minutes=m)).strftime("%H:%M")
                            for m in range(0, range_minutes, timeframe_minutes)]
        self.name = f"ORB {range_minutes}m on {timeframe_minutes}m bars"

    def start_session(self, session):
        self.or_high = self.or_low = None
        self.valid = True
        self.done = False

    def on_bar(self, bars, position):
        if self.done or not self.valid:
            return None
        bar = bars.iloc[-1]
        if self.or_high is None:
            if bar["time"] != self.range_times[-1]:
                if bar["time"] > self.range_times[-1]:
                    self.valid = False          # range bars missing -> skip day
                return None
            rng = bars[bars["time"].isin(self.range_times)]
            if list(rng["time"]) != self.range_times:
                self.valid = False
                return None
            self.or_high, self.or_low = rng["high"].max(), rng["low"].min()
            return None                         # range just formed; next bars test it
        if bar["close"] > self.or_high:
            self.done = True
            return 1
        if bar["close"] < self.or_low and self.allow_short:
            self.done = True
            return -1
        return None

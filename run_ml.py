"""Stage 8: train a scikit-learn model to predict tomorrow's direction,
then let OUR OWN engine judge it honestly.
Golden rule of ML on markets: train on the PAST, test on the FUTURE - never shuffle."""

import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from src.access import research_load_csv   # cutoff 2026-09-30
from src.indicators import add_ema
from src.backtest import run_backtest
from src.metrics import report

df = research_load_csv("NIFTY_10Y.csv")
df = add_ema(df, 20)
df = add_ema(df, 50)

# ---------- features: what the model is allowed to see (past only) ----------
df["ret_1"] = df["close"].pct_change()
df["ret_5"] = df["close"].pct_change(5)
df["ret_20"] = df["close"].pct_change(20)
df["dist_ema20"] = df["close"] / df["ema_20"] - 1
df["dist_ema50"] = df["close"] / df["ema_50"] - 1
df["vol_20"] = df["ret_1"].rolling(20).std()

FEATURES = ["ret_1", "ret_5", "ret_20", "dist_ema20", "dist_ema50", "vol_20"]

# ---------- target: will TOMORROW's close be higher than today's? ----------
df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)

df = df.dropna(subset=FEATURES).reset_index(drop=True)

# ---------- honest split: first 70% = training, last 30% = unseen future ----------
split = int(len(df) * 0.7)
train, test = df.iloc[:split], df.iloc[split:].copy()
print(f"Training: {len(train):,} days ({train.date.iloc[0].date()} -> {train.date.iloc[-1].date()})")
print(f"Testing : {len(test):,} days ({test.date.iloc[0].date()} -> {test.date.iloc[-1].date()})\n")

model = RandomForestClassifier(n_estimators=200, min_samples_leaf=20, random_state=42)
model.fit(train[FEATURES], train["target"])

# ---------- accuracy vs the dumbest possible baseline ----------
pred = model.predict(test[FEATURES])
accuracy = (pred == test["target"]).mean() * 100
always_up = test["target"].mean() * 100
print(f"Model accuracy on unseen days : {accuracy:.1f}%")
print(f"Dumb baseline ('always up')   : {always_up:.1f}%   <- must beat this to matter\n")

# ---------- the real judge: your backtest engine ----------
test["position"] = pred            # model says up -> be in, else out
test = test.reset_index(drop=True)
test, trades = run_backtest(test)
report(test, trades, name="RandomForest ML on NIFTY (unseen years only)")

print("\nWhat the model relied on:")
for feat, imp in sorted(zip(FEATURES, model.feature_importances_), key=lambda x: -x[1]):
    print(f"  {feat:12s} {imp * 100:5.1f}%")
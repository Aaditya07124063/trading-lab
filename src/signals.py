"""Turns indicator columns into a position column:
1 = be IN the market, 0 = be OUT."""


def crossover_signal(df, fast_col, slow_col):
    """IN whenever the fast line is above the slow line."""
    df["position"] = (df[fast_col] > df[slow_col]).astype(int)
    return df
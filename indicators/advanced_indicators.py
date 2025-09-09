# indicators/advanced_indicators.py
import numpy as np
import pandas as pd
import ta

def _supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.Series:
    hl2 = (df["high"] + df["low"]) / 2.0
    atr = ta.volatility.AverageTrueRange(high=df["high"], low=df["low"], close=df["close"], window=period).average_true_range()
    upperband = hl2 + multiplier * atr
    lowerband = hl2 - multiplier * atr

    st = pd.Series(index=df.index, dtype=float)
    trend_up = pd.Series(index=df.index, dtype=float)
    trend_down = pd.Series(index=df.index, dtype=float)

    trend_up.iloc[0] = upperband.iloc[0]
    trend_down.iloc[0] = lowerband.iloc[0]
    st.iloc[0] = upperband.iloc[0]

    for i in range(1, len(df)):
        trend_up.iloc[i] = upperband.iloc[i] if (upperband.iloc[i] < trend_up.iloc[i - 1]) or (df["close"].iloc[i - 1] > trend_up.iloc[i - 1]) else trend_up.iloc[i - 1]
        trend_down.iloc[i] = lowerband.iloc[i] if (lowerband.iloc[i] > trend_down.iloc[i - 1]) or (df["close"].iloc[i - 1] < trend_down.iloc[i - 1]) else trend_down.iloc[i - 1]
        if st.iloc[i - 1] == trend_up.iloc[i - 1]:
            st.iloc[i] = trend_up.iloc[i] if df["close"].iloc[i] <= trend_up.iloc[i] else trend_down.iloc[i]
        else:
            st.iloc[i] = trend_down.iloc[i] if df["close"].iloc[i] >= trend_down.iloc[i] else trend_up.iloc[i]

    return st

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Ensure floats
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)

    # EMA
    df["ema_20"] = ta.trend.EMAIndicator(df["close"], window=20).ema_indicator()
    df["ema_50"] = ta.trend.EMAIndicator(df["close"], window=50).ema_indicator()
    # RSI
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()
    # MACD
    macd = ta.trend.MACD(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    # Bollinger
    bb = ta.volatility.BollingerBands(close=df["close"], window=20, window_dev=2)
    df["bb_high"] = bb.bollinger_hband()
    df["bb_low"] = bb.bollinger_lband()
    # Stochastic
    stoch = ta.momentum.StochasticOscillator(high=df["high"], low=df["low"], close=df["close"], window=14, smooth_window=3)
    df["stoch_k"] = stoch.stoch()
    df["stoch_d"] = stoch.stoch_signal()
    # ADX
    adx = ta.trend.ADXIndicator(high=df["high"], low=df["low"], close=df["close"], window=14)
    df["adx"] = adx.adx()
    # Ichimoku
    ichi = ta.trend.IchimokuIndicator(high=df["high"], low=df["low"])
    df["ichimoku_a"] = ichi.ichimoku_a()
    df["ichimoku_b"] = ichi.ichimoku_b()
    # ATR
    df["atr"] = ta.volatility.AverageTrueRange(high=df["high"], low=df["low"], close=df["close"], window=14).average_true_range()
    # SuperTrend
    df["supertrend"] = _supertrend(df, period=10, multiplier=3.0)

    return df.dropna().reset_index(drop=True)

# strategy/strategy_engine.py
import pandas as pd
import numpy as np
from data.data_fetcher import fetch_ohlcv_bitstamp
from indicators.advanced_indicators import add_indicators
from typing import List

def score_row(last: pd.Series) -> float:
    score = 0.5
    if last["ema_20"] > last["ema_50"]:
        score += 0.08
    if last["macd"] > last["macd_signal"]:
        score += 0.06
    else:
        score -= 0.03
    if last["rsi"] < 30:
        score += 0.07
    elif last["rsi"] > 70:
        score -= 0.05
    if last["stoch_k"] > last["stoch_d"]:
        score += 0.04
    if (last["bb_high"] - last["close"]) / max(last["close"], 1e-9) < 0.01:
        score += 0.03
    if last["adx"] >= 20:
        score += 0.04
    if last["close"] > last["supertrend"]:
        score += 0.05
    else:
        score -= 0.03
    score += np.random.uniform(-0.02, 0.02)
    return float(min(max(score, 0.0), 1.0))

def generate_signal_table(symbols: List[str]):
    rows = []
    for s in symbols:
        df = fetch_ohlcv_bitstamp(symbol=s, timeframe="5m", limit=300)
        df_ind = add_indicators(df)
        last = df_ind.iloc[-1]
        conf = score_row(last)
        atr_pct = float(last["atr"] / max(last["close"], 1e-9))
        rows.append({"symbol": s, "confidence": conf, "atr_pct": atr_pct, "close": float(last["close"])})
    return pd.DataFrame(rows).sort_values(by=["confidence", "atr_pct"], ascending=[False, False]).reset_index(drop=True)

# data/data_fetcher.py
import ccxt
import pandas as pd
from config.settings import MODE
import time

def fetch_ohlcv_bitstamp(symbol="BTC/USD", timeframe="1m", limit=200):
    exchange = ccxt.bitstamp({
        "enableRateLimit": True
    })
    # ccxt uses ms for timestamps; returns list of [ts, open, high, low, close, volume]
    data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(data, columns=["time", "open", "high", "low", "close", "volume"])
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    return df

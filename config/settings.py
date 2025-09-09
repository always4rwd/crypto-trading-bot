# config/settings.py
import os
from dotenv import load_dotenv
load_dotenv()

MODE = os.getenv("MODE", "PAPER").upper()  # PAPER or LIVE

SETTINGS = {
    "min_confidence": 0.65,
    "risk_per_trade": 0.02,
    "max_daily_trades": 200,
    "micro_trade_min_usd": 2.0,
    "micro_trade_max_usd": 25.0,
    "daily_risk_budget_fraction": 0.20,
    "trailing_stop_pct_default": 0.15,
    "stop_loss_pct": 0.02,
    "take_profit_pct": 0.04,
    "starting_balance_usd": 1000.0,
    "symbols": ["BTC/USD", "ETH/USD", "XRP/USD", "SOL/USD", "DOGE/USD", "XLM/USD", "MATIC/USD", "SHIB/USD"],
}

TRADE_SYMBOLS = SETTINGS["symbols"]

BITSTAMP_API_KEY = os.getenv("BITSTAMP_API_KEY", "")
BITSTAMP_API_SECRET = os.getenv("BITSTAMP_API_SECRET", "")

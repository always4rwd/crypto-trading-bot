# trading/broker.py
from config.settings import MODE, BITSTAMP_API_KEY, BITSTAMP_API_SECRET
import ccxt
import math

class Broker:
    def __init__(self, mode="PAPER"):
        self.mode = mode
        self.exchange = None
        if self.mode == "LIVE":
            # authenticated client for live orders
            self.exchange = ccxt.bitstamp({
                "apiKey": BITSTAMP_API_KEY,
                "secret": BITSTAMP_API_SECRET,
                "enableRateLimit": True
            })
        else:
            # PAPER: no trading client needed; we only read market data via data_fetcher
            self.exchange = None

    def supports_amount_conversion(self):
        # We will use an approximate conversion (size USD -> amount) using last price.
        return False

    def usd_to_amount(self, symbol, usd):
        # Conservative fallback: return None (we store qty=None); UI shows USD
        return None

    def execute_trade(self, symbol, side, amount):
        """
        For PAPER mode this only logs; for LIVE it places orders.
        amount: for LIVE expected to be base currency amount; in PAPER we use USD sizes elsewhere.
        """
        if self.mode != "LIVE":
            # PAPER: printing only, actual trade simulated by main loop
            print(f"[PAPER] Simulated {side} {symbol} amount={amount}")
            return True
        try:
            if side.upper() == "BUY":
                order = self.exchange.create_market_buy_order(symbol, amount)
                print(f"[LIVE ORDER] BUY {symbol} -> {order}")
                return True
            elif side.upper() == "SELL":
                order = self.exchange.create_market_sell_order(symbol, amount)
                print(f"[LIVE ORDER] SELL {symbol} -> {order}")
                return True
            else:
                return False
        except Exception as e:
            print("Live order failed:", e)
            return False

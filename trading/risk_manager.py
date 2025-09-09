# trading/risk_manager.py
import math
import numpy as np
from typing import Dict
from config.settings import SETTINGS
from datetime import datetime, timedelta
from pathlib import Path
import json

LOG_DIR = Path("logs")
PAPER_STATE = LOG_DIR / "paper_state.json"

class RiskManager:
    def __init__(self, settings: Dict):
        self.settings = settings
        self.daily_budget_fraction = float(settings.get("daily_risk_budget_fraction", 0.2))
        self.max_daily_trades = int(settings.get("max_daily_trades", 200))
        self.min_usd = float(settings.get("micro_trade_min_usd", 2.0))
        self.max_usd = float(settings.get("micro_trade_max_usd", 25.0))
        self.risk_per_trade = float(settings.get("risk_per_trade", 0.02))
        self.paper_state = self._load_paper_state()
        # reset daily allocation tracker
        self.daily_allocated = 0.0
        self.last_reset = datetime.utcnow().date()

    def _load_paper_state(self):
        try:
            if PAPER_STATE.exists():
                return json.loads(PAPER_STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {"balance_usd": self.settings.get("starting_balance_usd", 1000.0)}

    def _save_paper_state(self):
        PAPER_STATE.write_text(json.dumps(self.paper_state, indent=2), encoding="utf-8")

    def reset_daily_if_needed(self):
        today = datetime.utcnow().date()
        if today != self.last_reset:
            self.daily_allocated = 0.0
            self.last_reset = today

    def dynamic_trade_plan(self, signals_df):
        self.reset_daily_if_needed()
        max_trades = self.max_daily_trades
        high_conf = signals_df[signals_df["confidence"] >= self.settings.get("min_confidence", 0.65)]
        if high_conf.empty:
            return 0
        base = len(high_conf)
        vol_factor = np.clip(high_conf["atr_pct"].mean() * 100.0 / 2.0, 0.5, 2.0)
        planned = int(np.clip(base * vol_factor, 1, max_trades))
        return planned

    def position_size_usd(self, confidence, atr_pct):
        balance = float(self.paper_state.get("balance_usd", self.settings.get("starting_balance_usd", 1000.0)))
        base = max(balance * self.risk_per_trade, 1.0)
        edge = max(0.0, 2.0 * confidence - 1.0)
        vol_penalty = 1.0 / max(0.5, (atr_pct * 100.0))
        raw = base * (0.5 + edge) * vol_penalty
        size = float(np.clip(raw, self.min_usd, self.max_usd))
        return round(size, 2)

    def can_allocate(self, size_usd):
        self.reset_daily_if_needed()
        daily_budget = float(self.paper_state.get("balance_usd", 0.0)) * self.daily_budget_fraction
        if (self.daily_allocated + size_usd) > daily_budget:
            return False
        return True

    def allocate(self, size_usd):
        self.daily_allocated += size_usd

    def simulate_result(self, confidence):
        # Probabilistic win based on confidence
        p_win = 0.45 + 0.5 * max(0.0, confidence - 0.5)
        return np.random.random() < p_win

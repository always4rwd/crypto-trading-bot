# dry_run_check.py — single cycle dry run for verification (save this file and run)
import json
from datetime import datetime
from pathlib import Path

from config.settings import SETTINGS, MODE, TRADE_SYMBOLS
from strategy.strategy_engine import generate_signal_table
from strategy.auto_learn import AutoLearner
from trading.risk_manager import RiskManager
from trading.broker import Broker

ROOT = Path(__file__).parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
TRADE_LOG = LOG_DIR / "trade_logs.json"
PAPER_STATE = LOG_DIR / "paper_state.json"

def ensure_files():
    if not TRADE_LOG.exists(): TRADE_LOG.write_text("[]", encoding="utf-8")
    if not PAPER_STATE.exists(): PAPER_STATE.write_text(json.dumps({"balance_usd": SETTINGS["starting_balance_usd"]}), encoding="utf-8")

def load_logs(): return json.loads(TRADE_LOG.read_text(encoding="utf-8") or "[]")
def save_log(entry):
    logs = load_logs(); logs.append(entry); TRADE_LOG.write_text(json.dumps(logs[-2000:], indent=2), encoding="utf-8")

ensure_files()
learner = AutoLearner(log_file=str(TRADE_LOG))
runtime_cfg = learner.apply_learning(dict(SETTINGS))
rm = RiskManager(runtime_cfg)
broker = Broker(mode=MODE)

signals = generate_signal_table(TRADE_SYMBOLS)
planned = rm.dynamic_trade_plan(signals)
print(f"Planned trades: {planned}")

candidates = signals.sort_values(by=["confidence","atr_pct"], ascending=[False,False]).reset_index(drop=True)
executed = 0
for i, row in candidates.iterrows():
    if executed >= planned:
        break
    symbol = row["symbol"]
    conf = float(row["confidence"])
    atr = float(row["atr_pct"])
    size_usd = rm.position_size_usd(conf, atr)
    if not rm.can_allocate(size_usd):
        continue
    # Simulate
    qty = None
    ok = broker.execute_trade(symbol, "BUY", qty)
    win = rm.simulate_result(conf)
    pnl = size_usd * (runtime_cfg["take_profit_pct"] if win else -runtime_cfg["stop_loss_pct"])
    rm.paper_state["balance_usd"] += pnl
    rm.allocate(size_usd)
    entry = {"timestamp": datetime.utcnow().isoformat(), "symbol": symbol, "confidence": round(conf,4), "size_usd": size_usd, "result": "win" if win else "loss", "pnl_usd": round(pnl,2), "balance_after_usd": round(rm.paper_state["balance_usd"],2)}
    save_log(entry)
    print("Executed:", entry)
    executed += 1

# save paper state
PAPER_STATE.write_text(json.dumps(rm.paper_state, indent=2), encoding="utf-8")
print("Dry run complete. New balance:", rm.paper_state["balance_usd"])

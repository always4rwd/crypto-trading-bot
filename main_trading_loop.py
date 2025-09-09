# main_trading_loop.py
import time
from datetime import datetime
from pathlib import Path
import json

from config.settings import SETTINGS, MODE, TRADE_SYMBOLS
from strategy.strategy_engine import generate_signal_table
from strategy.auto_learn import AutoLearner
from trading.risk_manager import RiskManager
from trading.broker import Broker

ROOT = Path(__file__).parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
TRADE_LOG = LOG_DIR / "trade_logs.json"
PAPER_STATE = LOG_DIR / "paper_state.json"

# Ensure log files exist
if not TRADE_LOG.exists():
    TRADE_LOG.write_text("[]", encoding="utf-8")
if not PAPER_STATE.exists():
    # starting paper state
    PAPER_STATE.write_text(json.dumps({"balance_usd": SETTINGS["starting_balance_usd"]}, indent=2), encoding="utf-8")

def load_logs():
    try:
        return json.loads(TRADE_LOG.read_text(encoding="utf-8") or "[]")
    except Exception:
        return []

def save_log(entry):
    logs = load_logs()
    logs.append(entry)
    TRADE_LOG.write_text(json.dumps(logs[-2000:], indent=2), encoding="utf-8")

def load_paper_state():
    try:
        return json.loads(PAPER_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"balance_usd": SETTINGS["starting_balance_usd"]}

def save_paper_state(state):
    PAPER_STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")

def main_loop(poll_interval=60):
    print(f"[START] MODE={MODE} symbols={TRADE_SYMBOLS}")
    # Components
    learner = AutoLearner(log_file=str(TRADE_LOG))
    runtime_cfg = learner.apply_learning(dict(SETTINGS))
    risk_mgr = RiskManager(runtime_cfg)
    broker = Broker(mode=MODE)

    while True:
        start = time.time()
        signals = generate_signal_table(TRADE_SYMBOLS)  # Data + indicators + confidence, atr_pct, close

        # Determine planned trades
        planned = risk_mgr.dynamic_trade_plan(signals)
        print(f"[{datetime.utcnow().isoformat()}] Planned trades this cycle: {planned} (balance ${risk_mgr.paper_state['balance_usd']:.2f})")

        # Sort candidates by confidence desc then atr_pct desc
        candidates = signals.sort_values(by=["confidence", "atr_pct"], ascending=[False, False]).reset_index(drop=True)

        executed = 0
        for idx, row in candidates.iterrows():
            if executed >= planned:
                break

            symbol = row["symbol"]
            confidence = float(row["confidence"])
            atr_pct = float(row["atr_pct"])
            size_usd = risk_mgr.position_size_usd(confidence, atr_pct)

            if not risk_mgr.can_allocate(size_usd):
                continue

            # Execute (paper or live)
            qty = broker.usd_to_amount(symbol, size_usd) if broker and broker.supports_amount_conversion() else size_usd
            ok = broker.execute_trade(symbol, "BUY", qty) if confidence >= runtime_cfg["min_confidence"] else False

            # For PAPER mode simulate PnL using stop/tp percentages
            win = False
            if MODE == "PAPER":
                # Simulated outcome biased by confidence
                win = risk_mgr.simulate_result(confidence)
                pnl = size_usd * (runtime_cfg["take_profit_pct"] if win else -runtime_cfg["stop_loss_pct"])
                # update paper state
                risk_mgr.paper_state["balance_usd"] += pnl
                risk_mgr.allocate(size_usd)
            else:
                # In LIVE mode we would need to query order status & compute actual PnL later.
                pnl = 0.0

            # Log trade (paper & live)
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": symbol,
                "confidence": round(confidence, 4),
                "size_usd": round(size_usd, 2),
                "qty": qty if isinstance(qty, (int, float)) else None,
                "result": "win" if win else "loss",
                "pnl_usd": round(pnl, 2),
                "balance_after_usd": round(risk_mgr.paper_state["balance_usd"], 2),
                "mode": MODE
            }
            save_log(entry)
            print(f"[TRADE] {symbol} conf={confidence:.2f} size=${size_usd:.2f} result={entry['result']} pnl=${entry['pnl_usd']:.2f}")
            executed += 1

        # persist paper state
        save_paper_state(risk_mgr.paper_state)
        elapsed = time.time() - start
        sleep_for = max(1, poll_interval - elapsed)
        time.sleep(sleep_for)

if __name__ == "__main__":
    try:
        main_loop(poll_interval=60)
    except KeyboardInterrupt:
        print("Stopping main loop.")

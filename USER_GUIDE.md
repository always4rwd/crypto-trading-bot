# User Guide (Quick Start)

1. Copy files into the folder structure.
2. Create virtualenv:
   python -m venv venv
   source venv/bin/activate
3. Install:
   pip install -r requirements.txt
4. Copy `.env.example` to `.env`.
   - Leave .env blank for paper mode (MODE=PAPER).
   - For LIVE mode: set BITSTAMP_API_KEY and BITSTAMP_API_SECRET then MODE=LIVE.
5. Ensure `logs/` exists with `trade_logs.json` and `paper_state.json` (empty JSON arrays or objects provided).
6. Run:
   python main_trading_loop.py
7. Open dashboard:
   python -m dashboard.app
   (or `python dashboard/app.py`) then visit http://127.0.0.1:5000

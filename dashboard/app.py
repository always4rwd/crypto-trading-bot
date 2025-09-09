# dashboard/app.py
from flask import Flask, render_template
from flask_socketio import SocketIO
from pathlib import Path
import json
import time
from threading import Thread

BASE = Path(__file__).resolve().parents[1]
LOG_PATH = BASE / "logs" / "trade_logs.json"

app = Flask(__name__, static_folder=str(Path(__file__).resolve().parent / "static"),
            template_folder=str(Path(__file__).resolve().parent / "templates"))
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def index():
    return render_template("index.html")

def emitter():
    last_len = 0
    while True:
        try:
            if LOG_PATH.exists():
                raw = LOG_PATH.read_text(encoding="utf-8")
                if raw.strip():
                    data = json.loads(raw)
                    if isinstance(data, list) and len(data) > last_len:
                        socketio.emit("trade_data", data[-1])
                        last_len = len(data)
        except Exception as e:
            socketio.emit("trade_data", {"error": str(e)})
        time.sleep(2)

@socketio.on("connect")
def on_connect():
    try:
        if LOG_PATH.exists():
            raw = LOG_PATH.read_text(encoding="utf-8")
            data = json.loads(raw) if raw.strip() else []
            socketio.emit("bootstrap", data[-50:])
    except Exception:
        socketio.emit("bootstrap", [])

if __name__ == "__main__":
    Thread(target=emitter, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000)

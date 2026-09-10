import os
from flask import Flask, render_template, jsonify, request
from data_provider import get_candles
from scanner import MarketScanner

app = Flask(__name__)

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

@app.get("/api/scan")
def scan():
    symbol = request.args.get("symbol", "BTCUSDT").upper().strip()
    try:
        result = MarketScanner(symbol, get_candles).scan_all()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.get("/api/history")
def history():
    symbol = request.args.get("symbol", "BTCUSDT").upper().strip()
    interval = request.args.get("interval", "1m")
    try:
        df = get_candles(symbol, interval, 300)
        rows = []
        for _, r in df.tail(20).iterrows():
            rows.append({"time": str(r["timestamp"]), "open": r["open"],
                         "high": r["high"], "low": r["low"], "close": r["close"]})
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)

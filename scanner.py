import numpy as np
from indicators import add_indicators, fibonacci_levels

def _safe(v, default=0.0):
    try:
        v = float(v)
        return default if not np.isfinite(v) else v
    except Exception:
        return default

def score_frame(df):
    df = add_indicators(df.copy())
    r = df.iloc[-1]
    up = down = 0
    reasons_up, reasons_down = [], []

    close = _safe(r.get("close"))
    ema9, ema21, ema50 = _safe(r.get("ema9")), _safe(r.get("ema21")), _safe(r.get("ema50"))
    rsi = _safe(r.get("rsi"), 50)
    stoch_k, stoch_d = _safe(r.get("stoch_k"), 50), _safe(r.get("stoch_d"), 50)
    macd, macd_sig = _safe(r.get("macd")), _safe(r.get("macd_signal"))
    adx = _safe(r.get("adx"))
    di_plus, di_minus = _safe(r.get("plus_di")), _safe(r.get("minus_di"))
    sar = _safe(r.get("sar"), close)
    bb_mid = _safe(r.get("bb_mid"), close)
    atr = max(_safe(r.get("atr"), 0), 1e-12)

    if ema9 > ema21 > ema50:
        up += 2; reasons_up.append("EMA trend UP")
    elif ema9 < ema21 < ema50:
        down += 2; reasons_down.append("EMA trend DOWN")

    if close > ema21:
        up += 1; reasons_up.append("Price above EMA21")
    elif close < ema21:
        down += 1; reasons_down.append("Price below EMA21")

    if 52 <= rsi <= 72:
        up += 1; reasons_up.append("RSI supports UP")
    elif 28 <= rsi <= 48:
        down += 1; reasons_down.append("RSI supports DOWN")

    if stoch_k > stoch_d and stoch_k < 85:
        up += 1; reasons_up.append("Stochastic UP")
    elif stoch_k < stoch_d and stoch_k > 15:
        down += 1; reasons_down.append("Stochastic DOWN")

    if macd > macd_sig:
        up += 1; reasons_up.append("MACD UP")
    elif macd < macd_sig:
        down += 1; reasons_down.append("MACD DOWN")

    if adx >= 18:
        if di_plus > di_minus:
            up += 1; reasons_up.append("DMI/ADX UP")
        elif di_minus > di_plus:
            down += 1; reasons_down.append("DMI/ADX DOWN")

    if close > sar:
        up += 1; reasons_up.append("SAR UP")
    elif close < sar:
        down += 1; reasons_down.append("SAR DOWN")

    body = abs(_safe(r.get("body"), 0))
    rng = max(_safe(r.get("range"), 0), 1e-12)
    upper = _safe(r.get("upper_wick"), 0)
    lower = _safe(r.get("lower_wick"), 0)
    bullish = bool(r.get("bullish_engulfing", False))
    bearish = bool(r.get("bearish_engulfing", False))

    if bullish or (lower > body * 1.5 and close > bb_mid):
        up += 1; reasons_up.append("Bullish price action")
    if bearish or (upper > body * 1.5 and close < bb_mid):
        down += 1; reasons_down.append("Bearish price action")

    if close > bb_mid:
        up += 1; reasons_up.append("Bollinger bias UP")
    elif close < bb_mid:
        down += 1; reasons_down.append("Bollinger bias DOWN")

    recent = df.tail(6)
    highs, lows = recent["high"].astype(float).values, recent["low"].astype(float).values
    if len(highs) >= 4:
        if highs[-1] > highs[-3] and lows[-1] > lows[-3]:
            up += 1; reasons_up.append("Higher-high / higher-low")
        elif highs[-1] < highs[-3] and lows[-1] < lows[-3]:
            down += 1; reasons_down.append("Lower-high / lower-low")

    if rng > 2.8 * atr:
        return {"direction":"NO TRADE","confidence":0,"up":up,"down":down,
                "reasons_up":reasons_up,"reasons_down":reasons_down,
                "reason":"Abnormal candle/volatility spike"}

    dominant = max(up, down)
    gap = abs(up - down)
    if dominant >= 7 and gap >= 3:
        direction = "UP" if up > down else "DOWN"
        confidence = min(99, int(70 + dominant * 3 + gap * 2))
    else:
        direction = "NO TRADE"
        confidence = min(69, int(50 + dominant * 2))

    fib = fibonacci_levels(df, min(100, len(df)))
    return {
        "direction": direction, "confidence": confidence,
        "up": up, "down": down, "reasons_up": reasons_up,
        "reasons_down": reasons_down, "total_confirmations": up + down,
        "price": round(close, 8), "rsi": round(rsi, 2), "adx": round(adx, 2),
        "support": round(float(df["low"].tail(20).min()), 8),
        "resistance": round(float(df["high"].tail(20).max()), 8),
        "pivot": round(_safe(r.get("pivot"), close), 8),
        "fib_61_8": round(fib["61.8"], 8)
    }

class MarketScanner:
    def __init__(self, symbol, get_candles_func):
        self.symbol = symbol
        self.get_candles = get_candles_func

    def scan_all(self):
        frames = {
            "1m": self.get_candles(self.symbol, "1m", 500),
            "5m": self.get_candles(self.symbol, "5m", 500),
            "15m": self.get_candles(self.symbol, "15m", 500),
        }
        results = {tf: score_frame(df) for tf, df in frames.items()}
        r1, r5, r15 = results["1m"], results["5m"], results["15m"]

        if r5["direction"] == "UP" and r15["direction"] == "UP" and r1["direction"] in ("UP", "NO TRADE"):
            final, reason = "UP", "5m + 15m confirmed UP"
            conf = int((r5["confidence"] + r15["confidence"]) / 2)
        elif r5["direction"] == "DOWN" and r15["direction"] == "DOWN" and r1["direction"] in ("DOWN", "NO TRADE"):
            final, reason = "DOWN", "5m + 15m confirmed DOWN"
            conf = int((r5["confidence"] + r15["confidence"]) / 2)
        else:
            final, reason = "NO TRADE", "Indicators are not aligned across timeframes"
            conf = max(r1["confidence"], r5["confidence"], r15["confidence"])

        return {
            "final_signal": final,
            "confidence": conf,
            "message": reason,
            "symbol": self.symbol,
            "timeframes": [
                {"interval": tf, "signal": r["direction"], "up_score": r["up"],
                 "down_score": r["down"], "score_confidence": r["confidence"],
                 "rsi": r["rsi"], "adx": r["adx"], "support": r["support"],
                 "resistance": r["resistance"], "pivot": r["pivot"],
                 "reasons": (r["reasons_up"] if r["direction"] == "UP"
                             else r["reasons_down"] if r["direction"] == "DOWN"
                             else r["reasons_up"][:3] + r["reasons_down"][:3]),
                 "price": r["price"]}
                for tf, r in results.items()
            ]
        }

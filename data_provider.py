import requests
import pandas as pd

BINANCE_BASE = "https://api.binance.com/api/v3/klines"
YAHOO_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"

VALID_INTERVALS = {"1m", "3m", "5m", "15m"}


def get_binance_candles(symbol="BTCUSDT", interval="1m", limit=500):
    r = requests.get(
        BINANCE_BASE,
        params={
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit
        },
        timeout=15
    )
    r.raise_for_status()

    raw = r.json()

    if not isinstance(raw, list) or len(raw) < 50:
        raise ValueError("Binance سے Market data کافی نہیں ملا۔")

    return pd.DataFrame([
        {
            "timestamp": pd.to_datetime(k[0], unit="ms"),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5])
        }
        for k in raw
    ])


def get_yahoo_candles(symbol="EURUSD", interval="1m", limit=500):

    # فاریکس symbols کو Yahoo Finance format میں تبدیل کریں
    yahoo_symbol = symbol.upper()

    if yahoo_symbol == "EURUSD":
        yahoo_symbol = "EURUSD=X"

    if yahoo_symbol == "GBPUSD":
        yahoo_symbol = "GBPUSD=X"

    if yahoo_symbol == "USDJPY":
        yahoo_symbol = "USDJPY=X"

    if yahoo_symbol == "AUDUSD":
        yahoo_symbol = "AUDUSD=X"

    if yahoo_symbol == "USDCAD":
        yahoo_symbol = "USDCAD=X"

    if yahoo_symbol == "USDCHF":
        yahoo_symbol = "USDCHF=X"

    # Yahoo 3m کو براہِ راست نہیں دیتا،
    # اس لیے پہلے 1m ڈیٹا لیا جائے گا۔
    yahoo_interval = "1m" if interval == "3m" else interval

    url = f"{YAHOO_BASE}/{yahoo_symbol}"

    r = requests.get(
        url,
        params={
            "range": "7d",
            "interval": yahoo_interval,
            "includePrePost": "false",
            "events": "div,splits"
        },
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=20
    )

    r.raise_for_status()

    data = r.json()

    result = data.get("chart", {}).get("result")

    if not result:
        raise ValueError("Yahoo Finance سے Market data نہیں ملا۔")

    result = result[0]

    timestamps = result.get("timestamp", [])
    quote = result.get("indicators", {}).get("quote", [{}])[0]

    if not timestamps:
        raise ValueError("Market candles دستیاب نہیں ہیں۔")

    df = pd.DataFrame({
        "timestamp": pd.to_datetime(timestamps, unit="s"),
        "open": quote.get("open", []),
        "high": quote.get("high", []),
        "low": quote.get("low", []),
        "close": quote.get("close", []),
        "volume": quote.get("volume", [])
    })

    df = df.dropna(subset=["open", "high", "low", "close"])

    # 3 منٹ کی کینڈل بنانے کے لیے 1m data کو resample کریں
    if interval == "3m":
        df = (
            df.set_index("timestamp")
            .resample("3min")
            .agg({
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum"
            })
            .dropna()
            .reset_index()
        )

    if len(df) < 50:
        raise ValueError("Market data کافی نہیں ملا۔")

    return df.tail(limit).reset_index(drop=True)


def get_candles(symbol="BTCUSDT", interval="1m", limit=500):

    if interval not in VALID_INTERVALS:
        raise ValueError(
            "صرف 1m, 3m, 5m, 15m سپورٹ ہیں۔"
        )

    symbol = symbol.upper()

    # Forex
    forex_symbols = {
        "EURUSD",
        "GBPUSD",
        "USDJPY",
        "AUDUSD",
        "USDCAD",
        "USDCHF"
    }

    if symbol in forex_symbols:
        return get_yahoo_candles(
            symbol=symbol,
            interval=interval,
            limit=limit
        )

    # Crypto
    return get_binance_candles(
        symbol=symbol,
        interval=interval,
        limit=limit
    )

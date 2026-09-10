import requests
import pandas as pd

BASE="https://api.binance.com/api/v3/klines"

VALID_INTERVALS={"1m","3m","5m","15m"}

def get_candles(symbol="BTCUSDT", interval="1m", limit=500):
    if interval not in VALID_INTERVALS:
        raise ValueError("صرف 1m, 3m, 5m, 15m سپورٹ ہیں۔")
    r=requests.get(BASE,params={"symbol":symbol,"interval":interval,"limit":limit},timeout=15)
    r.raise_for_status()
    raw=r.json()
    if not isinstance(raw,list) or len(raw)<250:
        raise ValueError("Market data کافی نہیں ملا۔")
    return pd.DataFrame([{
        "timestamp":pd.to_datetime(k[0],unit="ms"),
        "open":float(k[1]),"high":float(k[2]),"low":float(k[3]),
        "close":float(k[4]),"volume":float(k[5])
    } for k in raw])

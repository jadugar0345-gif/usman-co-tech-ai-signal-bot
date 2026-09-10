import numpy as np
import pandas as pd

def add_indicators(df):
    x=df.copy()
    o,h,l,c,v=[x[k].astype(float) for k in ["open","high","low","close","volume"]]

    for n in [9,21,50,200]:
        x[f"ema{n}"]=c.ewm(span=n,adjust=False).mean()
    for n in [20,50,200]:
        x[f"sma{n}"]=c.rolling(n).mean()

    d=c.diff()
    gain=d.clip(lower=0).rolling(14).mean()
    loss=(-d.clip(upper=0)).rolling(14).mean()
    rs=gain/loss.replace(0,np.nan)
    x["rsi"]=100-(100/(1+rs))

    low14=l.rolling(14).min(); high14=h.rolling(14).max()
    x["stoch_k"]=100*(c-low14)/(high14-low14).replace(0,np.nan)
    x["stoch_d"]=x["stoch_k"].rolling(3).mean()

    tp=(h+l+c)/3
    x["cci"]=(tp-tp.rolling(20).mean())/(0.015*tp.rolling(20).apply(lambda z: np.mean(np.abs(z-z.mean())),raw=True))

    x["willr"]=-100*(high14-c)/(high14-low14).replace(0,np.nan)
    x["roc"]=c.pct_change(12)*100

    e12=c.ewm(span=12,adjust=False).mean()
    e26=c.ewm(span=26,adjust=False).mean()
    x["macd"]=e12-e26
    x["macd_signal"]=x["macd"].ewm(span=9,adjust=False).mean()
    x["macd_hist"]=x["macd"]-x["macd_signal"]

    pc=c.shift(1)
    tr=pd.concat([(h-l),(h-pc).abs(),(l-pc).abs()],axis=1).max(axis=1)
    x["tr"]=tr
    x["atr"]=tr.rolling(14).mean()

    mid=c.rolling(20).mean(); std=c.rolling(20).std()
    x["bb_mid"]=mid; x["bb_upper"]=mid+2*std; x["bb_lower"]=mid-2*std
    x["bb_width"]=(x["bb_upper"]-x["bb_lower"])/mid.replace(0,np.nan)

    # Keltner-style channel
    x["kc_mid"]=c.ewm(span=20,adjust=False).mean()
    x["kc_upper"]=x["kc_mid"]+2*x["atr"]
    x["kc_lower"]=x["kc_mid"]-2*x["atr"]

    # ADX
    up=h.diff(); dn=-l.diff()
    plus_dm=np.where((up>dn)&(up>0),up,0.0)
    minus_dm=np.where((dn>up)&(dn>0),dn,0.0)
    atr=x["atr"].replace(0,np.nan)
    plus_di=100*pd.Series(plus_dm,index=x.index).rolling(14).mean()/atr
    minus_di=100*pd.Series(minus_dm,index=x.index).rolling(14).mean()/atr
    dx=100*(plus_di-minus_di).abs()/(plus_di+minus_di).replace(0,np.nan)
    x["adx"]=dx.rolling(14).mean()
    x["plus_di"]=plus_di; x["minus_di"]=minus_di

    # OBV
    direction=np.sign(c.diff()).fillna(0)
    x["obv"]=(direction*v).cumsum()
    x["obv_ema"]=x["obv"].ewm(span=20,adjust=False).mean()

    # MFI
    raw_mf=tp*v
    pos=np.where(tp>tp.shift(1),raw_mf,0)
    neg=np.where(tp<tp.shift(1),raw_mf,0)
    money_ratio=pd.Series(pos,index=x.index).rolling(14).sum()/pd.Series(neg,index=x.index).rolling(14).sum().replace(0,np.nan)
    x["mfi"]=100-(100/(1+money_ratio))

    # VWAP
    day=x["timestamp"].dt.date if "timestamp" in x else pd.Series(0,index=x.index)
    x["vwap"]=(tp*v).groupby(day).cumsum()/v.groupby(day).cumsum()

    # pivots from previous candle
    x["pivot"]=(h.shift(1)+l.shift(1)+c.shift(1))/3
    x["r1"]=2*x["pivot"]-l.shift(1); x["s1"]=2*x["pivot"]-h.shift(1)
    x["r2"]=x["pivot"]+(h.shift(1)-l.shift(1)); x["s2"]=x["pivot"]-(h.shift(1)-l.shift(1))

    # recent swing levels
    x["swing_high"]=h.rolling(20).max().shift(1)
    x["swing_low"]=l.rolling(20).min().shift(1)

    # candle anatomy
    x["body"]=c-o; x["body_abs"]=(c-o).abs()
    x["upper_wick"]=h-np.maximum(o,c)
    x["lower_wick"]=np.minimum(o,c)-l
    x["range"]=h-l

    # candle patterns
    prev_o=o.shift(1); prev_c=c.shift(1)
    x["bull_engulf"]=((c>o)&(prev_c<prev_o)&(c>=prev_o)&(o<=prev_c))
    x["bear_engulf"]=((c<o)&(prev_c>prev_o)&(c<=prev_o)&(o>=prev_c))
    x["bullish_engulfing"] = x["bull_engulf"]
    x["bearish_engulfing"] = x["bear_engulf"]
    x["doji"]=x["body_abs"] <= x["range"]*0.12

    # Lightweight Parabolic SAR implementation (no extra dependency).
    step, max_step = 0.02, 0.20
    sar_vals = [float(l.iloc[0])]
    bull = True
    ep = float(h.iloc[0])
    af = step
    for i in range(1, len(x)):
        prev_sar = sar_vals[-1]
        hi, lo = float(h.iloc[i]), float(l.iloc[i])
        new_sar = prev_sar + af * (ep - prev_sar)
        if bull:
            prior_l1 = float(l.iloc[i-1])
            prior_l2 = float(l.iloc[i-2]) if i >= 2 else prior_l1
            new_sar = min(new_sar, prior_l1, prior_l2)
            if lo < new_sar:
                bull = False
                new_sar = ep
                ep = lo
                af = step
            elif hi > ep:
                ep = hi
                af = min(max_step, af + step)
        else:
            prior_h1 = float(h.iloc[i-1])
            prior_h2 = float(h.iloc[i-2]) if i >= 2 else prior_h1
            new_sar = max(new_sar, prior_h1, prior_h2)
            if hi > new_sar:
                bull = True
                new_sar = ep
                ep = hi
                af = step
            elif lo < ep:
                ep = lo
                af = min(max_step, af + step)
        sar_vals.append(new_sar)
    x["sar"] = pd.Series(sar_vals, index=x.index)
    x["bull_pin"]=(x["lower_wick"]>=x["body_abs"]*2)&(x["upper_wick"]<=x["body_abs"]*0.8)
    x["bear_pin"]=(x["upper_wick"]>=x["body_abs"]*2)&(x["lower_wick"]<=x["body_abs"]*0.8)

    return x

def fibonacci_levels(df, lookback=100):
    h=float(df["high"].tail(lookback).max())
    l=float(df["low"].tail(lookback).min())
    diff=h-l
    return {
        "high":h,"low":l,
        "23.6":h-diff*.236,
        "38.2":h-diff*.382,
        "50":h-diff*.5,
        "61.8":h-diff*.618,
        "78.6":h-diff*.786
    }

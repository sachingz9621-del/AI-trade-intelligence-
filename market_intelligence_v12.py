"""V12 OHLCV market-structure, volume and relative-sector research helpers.
These are price/volume proxies, not exchange order-flow or institutional-position data.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

REQ = {"Open", "High", "Low", "Close", "Volume"}

def _clean(df: pd.DataFrame) -> pd.DataFrame:
    if not REQ.issubset(df.columns):
        raise ValueError("OHLCV data must contain Open, High, Low, Close and Volume")
    x = df.copy().sort_index()
    for c in REQ:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    return x.dropna(subset=["Open", "High", "Low", "Close"])

def volume_intelligence(df: pd.DataFrame, window: int = 20) -> dict:
    x = _clean(df)
    if len(x) < window + 2:
        return {"status": "Insufficient history", "relative_volume": np.nan, "obv": np.nan, "obv_trend": "Unknown", "cmf": np.nan, "volume_label": "Unknown"}
    avg = x.Volume.shift(1).rolling(window).mean().iloc[-1]
    rv = float(x.Volume.iloc[-1] / avg) if pd.notna(avg) and avg > 0 else np.nan
    direction = np.sign(x.Close.diff()).fillna(0)
    obv = (direction * x.Volume).cumsum()
    obv_delta = float(obv.iloc[-1] - obv.iloc[-min(6, len(obv))])
    obv_trend = "Rising" if obv_delta > 0 else "Falling" if obv_delta < 0 else "Flat"
    spread = (x.High - x.Low).replace(0, np.nan)
    mfm = ((x.Close - x.Low) - (x.High - x.Close)) / spread
    mfv = (mfm.fillna(0) * x.Volume)
    vol_sum = x.Volume.rolling(window).sum().iloc[-1]
    cmf = float(mfv.rolling(window).sum().iloc[-1] / vol_sum) if pd.notna(vol_sum) and vol_sum else np.nan
    label = "High activity" if pd.notna(rv) and rv >= 1.5 else "Low activity" if pd.notna(rv) and rv <= 0.7 else "Normal activity"
    return {"status": "OK", "relative_volume": rv, "obv": float(obv.iloc[-1]), "obv_trend": obv_trend, "cmf": cmf, "volume_label": label}

def _pivots(series: pd.Series, side: str, left: int, right: int) -> list[tuple[int, float]]:
    vals = series.to_numpy(dtype=float); out=[]
    for i in range(left, len(vals)-right):
        window = vals[i-left:i+right+1]
        if side == "high" and vals[i] == np.max(window) and np.sum(window == vals[i]) == 1:
            out.append((i, float(vals[i])))
        if side == "low" and vals[i] == np.min(window) and np.sum(window == vals[i]) == 1:
            out.append((i, float(vals[i])))
    return out

def market_structure(df: pd.DataFrame, left: int = 3, right: int = 3) -> dict:
    x = _clean(df)
    if len(x) < left + right + 10:
        return {"status": "Insufficient history", "bias": "Unknown", "event": "None", "swing_high": np.nan, "swing_low": np.nan}
    highs = _pivots(x.High, "high", left, right); lows = _pivots(x.Low, "low", left, right)
    sh = highs[-1][1] if highs else np.nan; sl = lows[-1][1] if lows else np.nan
    close = float(x.Close.iloc[-1]); bias = "Bullish structure" if len(highs)>=2 and len(lows)>=2 and highs[-1][1]>highs[-2][1] and lows[-1][1]>lows[-2][1] else "Bearish structure" if len(highs)>=2 and len(lows)>=2 and highs[-1][1]<highs[-2][1] and lows[-1][1]<lows[-2][1] else "Mixed / range"
    event = "Upside structure break" if pd.notna(sh) and close > sh else "Downside structure break" if pd.notna(sl) and close < sl else "No confirmed close break"
    return {"status": "OK", "bias": bias, "event": event, "swing_high": sh, "swing_low": sl, "confirmed_swing_highs": len(highs), "confirmed_swing_lows": len(lows)}

def supply_demand_zones(df: pd.DataFrame, lookback: int = 150, left: int = 3, right: int = 3, max_zones: int = 5) -> pd.DataFrame:
    x = _clean(df).tail(lookback)
    rows=[]
    if len(x) < left + right + 10:
        return pd.DataFrame(columns=["Type", "Low", "High", "Touches", "Distance %"])
    atr = (pd.concat([x.High-x.Low, (x.High-x.Close.shift()).abs(), (x.Low-x.Close.shift()).abs()], axis=1).max(axis=1).rolling(14).mean().iloc[-1])
    if not pd.notna(atr) or atr <= 0: atr = float((x.High-x.Low).median())
    # Pivot candle body-to-wick range forms a candidate zone; merge nearby levels by ATR.
    candidates=[]
    for idx, price in _pivots(x.Low, "low", left, right):
        row=x.iloc[idx]; candidates.append(("Demand", float(row.Low), float(min(row.Open,row.Close)), price))
    for idx, price in _pivots(x.High, "high", left, right):
        row=x.iloc[idx]; candidates.append(("Supply", float(max(row.Open,row.Close)), float(row.High), price))
    last=float(x.Close.iloc[-1])
    for typ in ("Demand", "Supply"):
        group=sorted([z for z in candidates if z[0]==typ], key=lambda z:z[3])
        clusters=[]
        for z in group:
            if clusters and abs(z[3]-np.mean([q[3] for q in clusters[-1]])) <= atr*0.6: clusters[-1].append(z)
            else: clusters.append([z])
        for cl in clusters:
            lo=min(z[1] for z in cl); hi=max(z[2] for z in cl)
            if (typ=="Demand" and hi <= last*1.03) or (typ=="Supply" and lo >= last*0.97):
                rows.append({"Type":typ,"Low":lo,"High":hi,"Touches":len(cl),"Distance %":((lo+hi)/2/last-1)*100})
    out=pd.DataFrame(rows)
    if out.empty: return pd.DataFrame(columns=["Type", "Low", "High", "Touches", "Distance %"])
    out["_dist"] = out["Distance %"].abs()
    return out.sort_values(["_dist","Touches"],ascending=[True,False]).drop(columns="_dist").head(max_zones).reset_index(drop=True)

def sector_rotation(sector_data: pd.DataFrame, benchmark_return: float = 0.0) -> pd.DataFrame:
    """Ranks sector/index returns against a supplied benchmark return, in percentage points."""
    if sector_data is None or sector_data.empty:
        return pd.DataFrame(columns=["Name","Symbol","Day %","5D %","Relative 5D %","Leadership"])
    x=sector_data.copy()
    required={"Name","Symbol","Day %","5D %"}
    if not required.issubset(x.columns):
        raise ValueError("Sector data must contain Name, Symbol, Day % and 5D %")
    x["Relative 5D %"] = pd.to_numeric(x["5D %"],errors="coerce")-float(benchmark_return)
    x["Leadership"] = np.where(x["Relative 5D %"]>0.25,"Leading",np.where(x["Relative 5D %"] < -0.25,"Lagging","In line"))
    return x.sort_values("Relative 5D %",ascending=False).reset_index(drop=True)

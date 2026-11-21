"""Transparent technical decision-support engine; deliberately not marketed as ML."""
from __future__ import annotations
import numpy as np
import pandas as pd


def enrich_indicators(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    if x.empty or not {"High", "Low", "Close", "Volume"}.issubset(x.columns):
        return x
    close, high, low, volume = x.Close.astype(float), x.High.astype(float), x.Low.astype(float), x.Volume.astype(float)
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    x["RSI"] = 100 - 100 / (1 + rs)
    x["EMA20"] = close.ewm(span=20, adjust=False).mean()
    x["EMA50"] = close.ewm(span=50, adjust=False).mean()
    x["EMA200"] = close.ewm(span=200, adjust=False).mean()
    x["MACD"] = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
    x["MACD_Signal"] = x.MACD.ewm(span=9, adjust=False).mean()
    x["MACD_Hist"] = x.MACD - x.MACD_Signal
    prev = close.shift(1)
    tr = pd.concat([(high-low), (high-prev).abs(), (low-prev).abs()], axis=1).max(axis=1)
    x["ATR"] = tr.ewm(alpha=1/14, adjust=False).mean()
    up, down = high.diff(), -low.diff()
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    atr = tr.ewm(alpha=1/14, adjust=False).mean().replace(0, np.nan)
    pdi = 100 * plus_dm.ewm(alpha=1/14, adjust=False).mean() / atr
    mdi = 100 * minus_dm.ewm(alpha=1/14, adjust=False).mean() / atr
    dx = 100 * (pdi-mdi).abs() / (pdi+mdi).replace(0, np.nan)
    x["ADX"] = dx.ewm(alpha=1/14, adjust=False).mean()
    x["Volume_Avg20"] = volume.rolling(20).mean()
    x["Relative_Volume"] = volume / x.Volume_Avg20.replace(0, np.nan)
    return x


def evaluate_signal(df: pd.DataFrame) -> dict:
    if df is None or len(df) < 35:
        return {"ready": False, "message": "At least 35 candles are required for this analysis."}
    x = enrich_indicators(df).dropna(subset=["Close", "EMA20", "EMA50", "MACD_Hist"])
    if x.empty:
        return {"ready": False, "message": "Not enough valid indicator data."}
    r = x.iloc[-1]
    score, reasons = 0, []
    tests = [
        (r.Close > r.EMA20, "Price above EMA20", "Price below EMA20", 1),
        (r.EMA20 > r.EMA50, "EMA20 above EMA50", "EMA20 below EMA50", 1),
        (r.Close > r.EMA200, "Price above EMA200", "Price below EMA200", 1),
        (r.MACD_Hist > 0, "MACD histogram positive", "MACD histogram negative", 1),
    ]
    for ok, pos, neg, weight in tests:
        score += weight if bool(ok) else -weight
        reasons.append(pos if ok else neg)
    rsi = float(r.RSI) if pd.notna(r.RSI) else np.nan
    if np.isfinite(rsi):
        if 52 <= rsi <= 68: score += 1; reasons.append("RSI supports bullish momentum")
        elif 32 <= rsi <= 48: score -= 1; reasons.append("RSI supports bearish momentum")
        elif rsi >= 75: reasons.append("RSI is overbought; chasing risk is elevated")
        elif rsi <= 25: reasons.append("RSI is oversold; rebound risk is elevated")
        else: reasons.append("RSI is in a mixed momentum zone")
    adx = float(r.ADX) if pd.notna(r.ADX) else np.nan
    if np.isfinite(adx) and adx >= 25:
        score += 1 if r.Close > r.EMA20 else -1
        reasons.append(f"ADX {adx:.1f}: trend strength elevated")
    else:
        reasons.append("ADX below 25 or unavailable: trend strength is limited")
    rv = float(r.Relative_Volume) if pd.notna(r.Relative_Volume) else np.nan
    if np.isfinite(rv): reasons.append(f"Relative volume: {rv:.2f}x 20-candle average")
    bias = "BULLISH" if score >= 3 else "BEARISH" if score <= -3 else "NEUTRAL / WAIT"
    confidence = min(95, round(50 + abs(score) * 6 + (5 if np.isfinite(adx) and adx >= 25 else 0)))
    close, atr = float(r.Close), float(r.ATR) if pd.notna(r.ATR) else np.nan
    direction = 1 if bias == "BULLISH" else -1 if bias == "BEARISH" else 0
    levels = None
    if direction and np.isfinite(atr) and atr > 0:
        levels = {"entry": close, "stop": close - direction*1.5*atr,
                  "target_1": close + direction*2*atr, "target_2": close + direction*3*atr,
                  "atr": atr}
    return {"ready": True, "bias": bias, "score": int(score), "confidence": confidence,
            "close": close, "rsi": rsi, "adx": adx, "relative_volume": rv,
            "reasons": reasons, "levels": levels,
            "warning": "Heuristic technical score, not a trained machine-learning prediction. Not investment advice."}

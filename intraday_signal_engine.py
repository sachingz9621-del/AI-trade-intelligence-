"""Read-only intraday confluence engine. Scores are heuristic, not forecasts."""
from __future__ import annotations
import pandas as pd
import numpy as np


def timeframe_snapshot(df: pd.DataFrame, label: str) -> dict:
    required = {"Open", "High", "Low", "Close", "Volume"}
    if df is None or df.empty or not required.issubset(df.columns) or len(df) < 30:
        return {"timeframe": label, "bias": "INSUFFICIENT DATA", "score": 0,
                "reasons": ["At least 30 valid OHLCV candles are required"], "close": None,
                "rsi": None, "relative_volume": None}
    x = df[list(required)].copy().sort_index()
    for c in required:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    x = x.dropna(subset=["Open", "High", "Low", "Close"])
    if len(x) < 30:
        return {"timeframe": label, "bias": "INSUFFICIENT DATA", "score": 0,
                "reasons": ["Not enough clean candles"], "close": None, "rsi": None,
                "relative_volume": None}
    close, high, low = x.Close, x.High, x.Low
    ema9, ema20, ema50 = close.ewm(span=9, adjust=False).mean(), close.ewm(span=20, adjust=False).mean(), close.ewm(span=50, adjust=False).mean()
    delta = close.diff(); gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = float((100 - 100/(1+rs)).iloc[-1]) if pd.notna(rs.iloc[-1]) else (100.0 if gain.iloc[-1] > 0 else 50.0)
    vol_avg = x.Volume.rolling(20).mean().iloc[-1]
    relvol = float(x.Volume.iloc[-1] / vol_avg) if pd.notna(vol_avg) and vol_avg > 0 else None
    score, reasons = 0, []
    checks = [(close.iloc[-1] > ema9.iloc[-1], 1, "Price above EMA 9", "Price below EMA 9"),
              (ema9.iloc[-1] > ema20.iloc[-1], 1, "EMA 9 above EMA 20", "EMA 9 below EMA 20"),
              (ema20.iloc[-1] > ema50.iloc[-1], 1, "EMA 20 above EMA 50", "EMA 20 below EMA 50")]
    for ok, pts, positive, negative in checks:
        score += pts if ok else -pts; reasons.append(positive if ok else negative)
    if rsi >= 55: score += 1; reasons.append("RSI momentum positive")
    elif rsi <= 45: score -= 1; reasons.append("RSI momentum negative")
    else: reasons.append("RSI neutral")
    if relvol is not None and relvol >= 1.5: score += 1 if close.iloc[-1] >= x.Close.iloc[-2] else -1; reasons.append("Relative volume elevated")
    bias = "BULLISH" if score >= 2 else ("BEARISH" if score <= -2 else "NEUTRAL")
    return {"timeframe": label, "bias": bias, "score": int(score), "reasons": reasons,
            "close": float(close.iloc[-1]), "rsi": round(rsi, 2),
            "relative_volume": round(relvol, 2) if relvol is not None else None}


def combine_timeframes(five_minute: pd.DataFrame, fifteen_minute: pd.DataFrame) -> dict:
    a = timeframe_snapshot(five_minute, "5-minute")
    b = timeframe_snapshot(fifteen_minute, "15-minute")
    if "INSUFFICIENT DATA" in (a["bias"], b["bias"]):
        return {"bias": "INSUFFICIENT DATA", "score": 0, "agreement": "—", "snapshots": [a, b],
                "note": "Fetch enough valid candles for both timeframes."}
    total = a["score"] + b["score"]
    if a["bias"] == b["bias"] and a["bias"] in ("BULLISH", "BEARISH"):
        bias, agreement = a["bias"], "Aligned"
    elif a["bias"] == "NEUTRAL" or b["bias"] == "NEUTRAL":
        bias, agreement = "WAIT", "Partial / neutral"
    else:
        bias, agreement = "WAIT", "Timeframes conflict"
    return {"bias": bias, "score": total, "agreement": agreement, "snapshots": [a, b],
            "note": "A confluence screen only; not an entry signal or probability."}

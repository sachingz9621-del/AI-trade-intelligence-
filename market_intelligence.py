"""Rule-based market structure and breakout analysis; not a predictive ML model."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ai_engine import enrich_indicators


def analyze_market_structure(df: pd.DataFrame, lookback: int = 20) -> dict:
    required = {"Open", "High", "Low", "Close", "Volume"}
    if df is None or len(df) < max(35, lookback + 2) or not required.issubset(df.columns):
        return {"ready": False, "message": f"At least {max(35, lookback + 2)} OHLCV candles are required."}
    x = enrich_indicators(df).copy()
    x = x.replace([np.inf, -np.inf], np.nan)
    r = x.iloc[-1]
    prior = x.iloc[-lookback-1:-1]
    if prior.empty or not np.isfinite(float(r.Close)):
        return {"ready": False, "message": "Insufficient valid OHLCV data."}
    resistance = float(prior.High.max())
    support = float(prior.Low.min())
    close = float(r.Close)
    atr = float(r.ATR) if pd.notna(r.ATR) else np.nan
    rv = float(r.Relative_Volume) if pd.notna(r.Relative_Volume) else np.nan
    buffer = max(0.0, atr * 0.10) if np.isfinite(atr) else 0.0
    breakout = "BREAKOUT ABOVE" if close > resistance + buffer else "BREAKDOWN BELOW" if close < support - buffer else "INSIDE RANGE"
    # Count conditions transparently; these are descriptive confluences, not probabilities.
    bull, bear, reasons = 0, 0, []
    if close > float(r.EMA20): bull += 1; reasons.append("Close above EMA20")
    else: bear += 1; reasons.append("Close below EMA20")
    if float(r.EMA20) > float(r.EMA50): bull += 1; reasons.append("EMA20 above EMA50")
    else: bear += 1; reasons.append("EMA20 below EMA50")
    if pd.notna(r.MACD_Hist) and float(r.MACD_Hist) > 0: bull += 1; reasons.append("MACD histogram positive")
    else: bear += 1; reasons.append("MACD histogram non-positive")
    if breakout == "BREAKOUT ABOVE": bull += 2; reasons.append("Close cleared prior range high")
    elif breakout == "BREAKDOWN BELOW": bear += 2; reasons.append("Close broke prior range low")
    if np.isfinite(rv) and rv >= 1.5:
        if close >= float(r.Open): bull += 1; reasons.append(f"Elevated relative volume ({rv:.2f}x) with positive candle")
        else: bear += 1; reasons.append(f"Elevated relative volume ({rv:.2f}x) with negative candle")
    bias = "BULLISH" if bull >= bear + 2 else "BEARISH" if bear >= bull + 2 else "MIXED / WAIT"
    levels = None
    if np.isfinite(atr) and atr > 0:
        levels = {"bullish_entry_reference": resistance + buffer,
                  "bearish_entry_reference": support - buffer,
                  "atr": atr,
                  "bullish_invalidation": resistance - atr,
                  "bearish_invalidation": support + atr}
    return {"ready": True, "close": close, "support": support, "resistance": resistance,
            "breakout": breakout, "bias": bias, "bull_points": bull, "bear_points": bear,
            "relative_volume": rv, "rsi": float(r.RSI) if pd.notna(r.RSI) else np.nan,
            "adx": float(r.ADX) if pd.notna(r.ADX) else np.nan,
            "levels": levels, "reasons": reasons,
            "warning": "Rule-based technical context, not a trained AI probability or a trade instruction. Confirm with live broker data and your own risk plan."}

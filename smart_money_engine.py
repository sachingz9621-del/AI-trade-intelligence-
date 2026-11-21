"""OHLCV-derived market-structure heuristics (not institutional order-flow data)."""
from __future__ import annotations
import numpy as np
import pandas as pd

REQUIRED = {"Open", "High", "Low", "Close", "Volume"}


def _clean(frame: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or not REQUIRED.issubset(frame.columns):
        raise ValueError(f"Data must contain columns: {', '.join(sorted(REQUIRED))}")
    out = frame.copy()
    for col in REQUIRED:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=list(REQUIRED)).sort_index()
    if len(out) < 10:
        raise ValueError("At least 10 valid OHLCV candles are required.")
    return out


def detect_liquidity_sweeps(frame: pd.DataFrame, lookback: int = 20) -> dict:
    """Detect a close-back-inside sweep of prior rolling highs/lows."""
    d = _clean(frame)
    if lookback < 3 or lookback >= len(d):
        raise ValueError("lookback must be >= 3 and smaller than candle count")
    prior_high = d.High.shift(1).rolling(lookback).max().iloc[-1]
    prior_low = d.Low.shift(1).rolling(lookback).min().iloc[-1]
    last = d.iloc[-1]
    high_sweep = bool(pd.notna(prior_high) and last.High > prior_high and last.Close < prior_high)
    low_sweep = bool(pd.notna(prior_low) and last.Low < prior_low and last.Close > prior_low)
    return {"high_sweep": high_sweep, "low_sweep": low_sweep,
            "reference_high": float(prior_high) if pd.notna(prior_high) else None,
            "reference_low": float(prior_low) if pd.notna(prior_low) else None,
            "latest_close": float(last.Close),
            "interpretation": "Potential buy-side liquidity sweep" if high_sweep else "Potential sell-side liquidity sweep" if low_sweep else "No sweep on latest candle"}


def detect_fair_value_gaps(frame: pd.DataFrame, max_items: int = 10) -> pd.DataFrame:
    """Three-candle imbalance heuristic: current low > high two bars back, or vice versa."""
    d = _clean(frame)
    rows = []
    for i in range(2, len(d)):
        left, right = d.iloc[i-2], d.iloc[i]
        if right.Low > left.High:
            rows.append({"Time": d.index[i], "Type": "Bullish FVG", "Lower": float(left.High), "Upper": float(right.Low), "Midpoint": float((left.High + right.Low)/2)})
        elif right.High < left.Low:
            rows.append({"Time": d.index[i], "Type": "Bearish FVG", "Lower": float(right.High), "Upper": float(left.Low), "Midpoint": float((right.High + left.Low)/2)})
    return pd.DataFrame(rows).tail(max_items).reset_index(drop=True)


def detect_order_blocks(frame: pd.DataFrame, lookback: int = 30) -> pd.DataFrame:
    """Approximate last opposite-colour candle before a close beyond recent swing range."""
    d = _clean(frame)
    rows = []
    start = max(5, len(d)-lookback)
    for i in range(start, len(d)):
        prior = d.iloc[max(0, i-5):i]
        if len(prior) < 3:
            continue
        candle = d.iloc[i]
        swing_high, swing_low = float(prior.High.max()), float(prior.Low.min())
        if candle.Close > swing_high and candle.Close > candle.Open:
            candidates = d.iloc[max(0, i-3):i]
            opposite = candidates[candidates.Close < candidates.Open]
            if not opposite.empty:
                ob = opposite.iloc[-1]
                rows.append({"Time": opposite.index[-1], "Type": "Bullish order-block candidate", "Lower": float(ob.Low), "Upper": float(ob.High)})
        elif candle.Close < swing_low and candle.Close < candle.Open:
            candidates = d.iloc[max(0, i-3):i]
            opposite = candidates[candidates.Close > candidates.Open]
            if not opposite.empty:
                ob = opposite.iloc[-1]
                rows.append({"Time": opposite.index[-1], "Type": "Bearish order-block candidate", "Lower": float(ob.Low), "Upper": float(ob.High)})
    return pd.DataFrame(rows).drop_duplicates(subset=["Time", "Type"]).tail(10).reset_index(drop=True)


def calculate_volume_profile(frame: pd.DataFrame, bins: int = 24) -> pd.DataFrame:
    """Approximate volume-at-price by assigning each candle's volume to its typical price."""
    d = _clean(frame)
    if bins < 5 or bins > 100:
        raise ValueError("bins must be between 5 and 100")
    typical = (d.High + d.Low + d.Close) / 3
    if float(typical.max()) == float(typical.min()):
        return pd.DataFrame({"Price": [float(typical.iloc[-1])], "Volume": [float(d.Volume.sum())]})
    edges = np.linspace(float(typical.min()), float(typical.max()), bins+1)
    idx = np.clip(np.digitize(typical, edges[1:-1]), 0, bins-1)
    volume = np.bincount(idx, weights=d.Volume.to_numpy(dtype=float), minlength=bins)
    centers = (edges[:-1] + edges[1:]) / 2
    result = pd.DataFrame({"Price": centers, "Volume": volume})
    return result.sort_values("Price").reset_index(drop=True)


def summarize_structure(frame: pd.DataFrame) -> dict:
    d = _clean(frame)
    sweep = detect_liquidity_sweeps(d)
    gaps = detect_fair_value_gaps(d)
    blocks = detect_order_blocks(d)
    profile = calculate_volume_profile(d)
    poc = profile.loc[profile.Volume.idxmax()]
    return {"sweep": sweep, "fvg_count": len(gaps), "order_block_count": len(blocks),
            "poc_price": float(poc.Price), "total_volume": float(d.Volume.sum()),
            "warning": "Heuristic OHLCV patterns only. These are not verified institutional orders, exchange order-book liquidity, or guaranteed trade signals."}

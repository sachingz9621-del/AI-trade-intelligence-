"""Rule-based trade confluence and ATR risk-plan helpers.

Uses OHLCV-derived indicators and heuristic structure checks only. It is not
machine learning, broker order flow, a probability estimate, or trade advice.
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from ai_engine import evaluate_signal
from smart_money_engine import detect_liquidity_sweeps, detect_fair_value_gaps, detect_order_blocks

_REQUIRED = {"Open", "High", "Low", "Close", "Volume"}


def _validate(frame: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or not _REQUIRED.issubset(frame.columns):
        raise ValueError("Data must contain Open, High, Low, Close and Volume columns.")
    d = frame.copy()
    for c in _REQUIRED:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=list(_REQUIRED)).sort_index()
    if len(d) < 35:
        raise ValueError("At least 35 valid OHLCV candles are required.")
    if (d[["High", "Low", "Open", "Close"]] <= 0).any().any():
        raise ValueError("OHLC prices must be positive.")
    return d


def _latest_context(d: pd.DataFrame) -> dict:
    close = d.Close
    ema20 = close.ewm(span=20, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    tr = pd.concat([d.High-d.Low, (d.High-close.shift()).abs(), (d.Low-close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean()
    vol_avg = d.Volume.rolling(20).mean()
    last = d.iloc[-1]
    return {"close": float(last.Close), "ema20": float(ema20.iloc[-1]), "ema50": float(ema50.iloc[-1]),
            "rsi": float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else 50.0,
            "atr": float(atr.iloc[-1]), "volume_ratio": float(last.Volume / vol_avg.iloc[-1]) if pd.notna(vol_avg.iloc[-1]) and vol_avg.iloc[-1] > 0 else 0.0}


def evaluate_trade_confluence(frames: dict[str, pd.DataFrame]) -> dict:
    """Combine available timeframe bias with latest OHLCV structure clues."""
    if not frames:
        raise ValueError("Provide at least one timeframe frame.")
    valid = {str(k): _validate(v) for k, v in frames.items() if isinstance(v, pd.DataFrame) and not v.empty}
    if not valid:
        raise ValueError("No usable timeframe data was provided.")
    tf_results = {k: evaluate_signal(v) for k, v in valid.items()}
    ready = {k: v for k, v in tf_results.items() if v.get("ready")}
    if not ready:
        raise ValueError("No timeframe has enough candles for signal analysis.")
    bull = sum(x.get("bias") == "BULLISH" for x in ready.values())
    bear = sum(x.get("bias") == "BEARISH" for x in ready.values())
    primary_key = "1D" if "1D" in valid else next(reversed(valid))
    d = valid[primary_key]
    ctx = _latest_context(d)
    sweep = detect_liquidity_sweeps(d)
    gaps = detect_fair_value_gaps(d)
    blocks = detect_order_blocks(d)
    last_gap = gaps.iloc[-1].to_dict() if not gaps.empty else None
    last_block = blocks.iloc[-1].to_dict() if not blocks.empty else None

    long_score = 0
    short_score = 0
    reasons = []
    if bull > bear: long_score += 2; reasons.append("More supplied timeframes are bullish")
    elif bear > bull: short_score += 2; reasons.append("More supplied timeframes are bearish")
    else: reasons.append("Timeframes are tied or mixed")
    if ctx["close"] > ctx["ema20"] > ctx["ema50"]: long_score += 2; reasons.append("Price > EMA20 > EMA50")
    elif ctx["close"] < ctx["ema20"] < ctx["ema50"]: short_score += 2; reasons.append("Price < EMA20 < EMA50")
    if ctx["rsi"] >= 55: long_score += 1; reasons.append("RSI supports positive momentum")
    elif ctx["rsi"] <= 45: short_score += 1; reasons.append("RSI supports negative momentum")
    if ctx["volume_ratio"] >= 1.5:
        if ctx["close"] >= float(d.iloc[-1].Open): long_score += 1
        else: short_score += 1
        reasons.append("Latest volume is at least 1.5x its 20-candle average")
    if sweep["low_sweep"]: long_score += 2; reasons.append("Latest candle shows a potential sell-side sweep")
    if sweep["high_sweep"]: short_score += 2; reasons.append("Latest candle shows a potential buy-side sweep")
    if last_gap:
        if last_gap["Type"] == "Bullish FVG": long_score += 1
        else: short_score += 1
        reasons.append("Most recent three-candle gap added directional context")
    if last_block:
        if last_block["Type"].startswith("Bullish"): long_score += 1
        else: short_score += 1
        reasons.append("Most recent opposite-candle breakout candidate added context")

    if long_score >= 5 and long_score - short_score >= 2:
        bias = "BULLISH SETUP CANDIDATE"
    elif short_score >= 5 and short_score - long_score >= 2:
        bias = "BEARISH SETUP CANDIDATE"
    else:
        bias = "NO CONFIRMED SETUP / WAIT"
    max_score = max(long_score, short_score)
    rank = "A" if max_score >= 8 and abs(long_score-short_score) >= 4 else "B" if max_score >= 6 and abs(long_score-short_score) >= 3 else "C — WEAK / MIXED"
    return {"bias": bias, "rank": rank, "long_score": long_score, "short_score": short_score,
            "timeframes": tf_results, "context": ctx, "reasons": reasons, "sweep": sweep,
            "latest_fvg": last_gap, "latest_order_block": last_block,
            "warning": "Rule-based confluence only. OHLCV patterns do not verify institutional orders or predict outcomes. Confirm live quotes, liquidity, spread, news and execution risk."}


def build_atr_trade_plan(entry: float, atr: float, direction: str, risk_budget: float,
                         stop_atr: float = 1.5, reward_risk: float = 2.0) -> dict:
    """Reference cash-equity plan; quantity is risk-budget limited, before costs."""
    vals = [entry, atr, risk_budget, stop_atr, reward_risk]
    if not all(math.isfinite(float(x)) for x in vals):
        raise ValueError("All plan inputs must be finite numbers.")
    entry, atr, risk_budget, stop_atr, reward_risk = map(float, vals)
    direction = direction.upper()
    if entry <= 0 or atr <= 0 or risk_budget <= 0 or stop_atr <= 0 or reward_risk <= 0:
        raise ValueError("Entry, ATR, risk budget and multipliers must be greater than zero.")
    if direction not in {"LONG", "SHORT"}:
        raise ValueError("Direction must be LONG or SHORT.")
    distance = atr * stop_atr
    stop = entry - distance if direction == "LONG" else entry + distance
    target = entry + distance * reward_risk if direction == "LONG" else entry - distance * reward_risk
    qty = math.floor(risk_budget / distance)
    return {"direction": direction, "entry_reference": entry, "stop_loss": stop,
            "target": target, "risk_per_share": distance, "reward_risk": reward_risk,
            "quantity": qty, "estimated_risk_before_costs": qty * distance,
            "estimated_position_value": qty * entry}

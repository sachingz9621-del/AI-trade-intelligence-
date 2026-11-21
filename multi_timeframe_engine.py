"""Transparent multi-timeframe trend alignment and cash-equity risk sizing."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from ai_engine import evaluate_signal


def analyze_alignment(frames: dict[str, pd.DataFrame]) -> dict:
    """Score supplied OHLCV frames independently, then summarize agreement."""
    results = {}
    for label, frame in frames.items():
        results[label] = evaluate_signal(frame)
    ready = {k: v for k, v in results.items() if v.get("ready")}
    if not ready:
        return {"ready": False, "message": "No timeframe has enough valid OHLCV candles." , "timeframes": results}
    bull = sum(v["bias"] == "BULLISH" for v in ready.values())
    bear = sum(v["bias"] == "BEARISH" for v in ready.values())
    neutral = len(ready) - bull - bear
    if bull == len(ready): overall = "BULLISH ALIGNMENT"
    elif bear == len(ready): overall = "BEARISH ALIGNMENT"
    elif bull > bear: overall = "BULLISH LEAN — NOT FULLY ALIGNED"
    elif bear > bull: overall = "BEARISH LEAN — NOT FULLY ALIGNED"
    else: overall = "MIXED / WAIT"
    return {"ready": True, "overall": overall, "bullish_count": bull,
            "bearish_count": bear, "neutral_count": neutral,
            "timeframes": results,
            "warning": "Timeframe agreement is a rule-based filter, not a probability or a trade instruction. Prices can be delayed; verify live quotes and execution conditions with your broker."}


def calculate_cash_risk(entry: float, stop: float, capital: float,
                        risk_percent: float) -> dict:
    """Position sizing for cash-equity units; excludes fees, slippage and leverage."""
    values = [entry, stop, capital, risk_percent]
    if not all(np.isfinite(float(x)) for x in values):
        raise ValueError("All inputs must be finite numbers.")
    entry, stop, capital, risk_percent = map(float, values)
    if entry <= 0 or stop <= 0 or capital <= 0:
        raise ValueError("Entry, stop and capital must be greater than zero.")
    if risk_percent <= 0 or risk_percent > 5:
        raise ValueError("Risk percentage must be greater than 0 and no more than 5%.")
    per_share = abs(entry - stop)
    if per_share <= 0:
        raise ValueError("Entry and stop must be different.")
    risk_budget = capital * risk_percent / 100
    quantity = math.floor(risk_budget / per_share)
    return {"risk_budget": risk_budget, "risk_per_share": per_share,
            "quantity": quantity, "estimated_position_value": quantity * entry,
            "estimated_max_loss_before_costs": quantity * per_share,
            "capital_limited": quantity * entry > capital}

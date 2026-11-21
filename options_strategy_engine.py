"""Transparent, read-only options setup scoring from an Upstox option-chain snapshot.
Scores are heuristic filters, not predictions or trade recommendations.
"""
from __future__ import annotations
import math
import pandas as pd


def _num(row, key):
    try:
        value = float(row.get(key))
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def analyze_option_opportunities(chain: pd.DataFrame, spot: float, max_distance_pct: float = 3.0,
                                 min_volume: int = 1, min_oi: int = 1) -> pd.DataFrame:
    required = {"Strike", "CE LTP", "CE OI", "CE OI Change", "CE Volume", "CE IV", "CE Delta",
                "PE LTP", "PE OI", "PE OI Change", "PE Volume", "PE IV", "PE Delta"}
    missing = required.difference(chain.columns)
    if missing:
        raise ValueError("Option chain is missing columns: " + ", ".join(sorted(missing)))
    if chain.empty or not math.isfinite(float(spot)) or float(spot) <= 0:
        return pd.DataFrame()
    rows = []
    for _, row in chain.iterrows():
        strike = _num(row, "Strike")
        if strike is None or abs(strike - spot) / spot * 100 > max_distance_pct:
            continue
        for side, prefix, ideal_delta in (("CE", "CE", (0.35, 0.65)), ("PE", "PE", (-0.65, -0.35))):
            ltp, oi, oi_change, volume = (_num(row, f"{prefix} {col}") for col in ("LTP", "OI", "OI Change", "Volume"))
            iv, delta = _num(row, f"{prefix} IV"), _num(row, f"{prefix} Delta")
            if not ltp or ltp <= 0 or oi is None or oi < min_oi or volume is None or volume < min_volume:
                continue
            score, reasons = 0, []
            if oi_change is not None and oi_change > 0:
                score += 25; reasons.append("Open interest increased")
            elif oi_change is not None and oi_change < 0:
                score -= 10; reasons.append("Open interest decreased")
            if volume > 0 and oi > 0 and volume / oi >= 0.10:
                score += 15; reasons.append("Volume/OI activity elevated")
            if delta is not None and ideal_delta[0] <= delta <= ideal_delta[1]:
                score += 25; reasons.append("Delta in moderate-moneyness band")
            if iv is not None and 0 < iv <= 60:
                score += 10; reasons.append("IV at or below 60")
            elif iv is not None and iv > 80:
                score -= 15; reasons.append("High IV premium risk")
            distance = abs(strike - spot) / spot * 100
            if distance <= 1.0:
                score += 15; reasons.append("Strike within 1% of spot")
            elif distance <= 2.0:
                score += 8; reasons.append("Strike within 2% of spot")
            label = "WATCH" if score >= 50 else ("WEAK" if score >= 25 else "AVOID FILTER")
            rows.append({"Side": side, "Strike": strike, "LTP": ltp, "OI": oi,
                         "OI Change": oi_change, "Volume": volume, "IV": iv, "Delta": delta,
                         "Distance from spot %": round(distance, 2), "Score / 100": max(0, min(100, score)),
                         "Screening status": label, "Why": "; ".join(reasons) or "No positive filters"})
    if not rows:
        return pd.DataFrame(columns=["Side", "Strike", "LTP", "OI", "OI Change", "Volume", "IV", "Delta", "Distance from spot %", "Score / 100", "Screening status", "Why"])
    return pd.DataFrame(rows).sort_values(["Score / 100", "Volume"], ascending=False).reset_index(drop=True)


def premium_risk_plan(premium: float, stop_pct: float, target_multiple: float, lot_size: int, lots: int = 1) -> dict:
    """Illustrative premium-only risk plan; excludes charges, slippage and gap risk."""
    if premium <= 0 or not 0 < stop_pct < 100 or target_multiple <= 0 or lot_size <= 0 or lots <= 0:
        raise ValueError("Premium, lot size, lots and target must be positive; stop percentage must be between 0 and 100.")
    stop = premium * (1 - stop_pct / 100)
    risk_per_unit = premium - stop
    target = premium + risk_per_unit * target_multiple
    qty = lot_size * lots
    return {"entry_premium": premium, "stop_premium": round(stop, 2), "target_premium": round(target, 2),
            "quantity": qty, "maximum_planned_loss": round(risk_per_unit * qty, 2),
            "planned_profit_at_target": round((target - premium) * qty, 2),
            "risk_reward": target_multiple}

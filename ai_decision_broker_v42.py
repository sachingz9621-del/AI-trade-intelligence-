"""V42 explainable AI trade decision support and read-only Upstox broker gateway.

All recommendations are evidence-based heuristics. Broker functions are read-only;
real-money order submission is deliberately not implemented in this release.
"""
from __future__ import annotations
import math
import requests
import numpy as np
import pandas as pd

STRATEGY_PROFILES = {
    "Scalping": {"stop_atr": 0.8, "target_atr": 1.6, "min_bars": 40, "allowed_intervals": {"1m", "2m", "5m"}, "horizon": "1–5 minutes"},
    "Intraday": {"stop_atr": 1.2, "target_atr": 2.0, "min_bars": 40, "allowed_intervals": {"5m", "15m", "30m", "1h"}, "horizon": "Intraday; review before session close"},
    "Hedging": {"stop_atr": 1.0, "target_atr": 1.5, "min_bars": 40, "allowed_intervals": {"5m", "15m", "30m", "1h", "1d"}, "horizon": "Portfolio protection; align with holding horizon"},
}


def _clean_ohlcv(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"Open", "High", "Low", "Close", "Volume"}
    if not isinstance(frame, pd.DataFrame) or not required.issubset(frame.columns):
        return pd.DataFrame()
    x = frame[list(required)].copy()
    for c in required:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    return x.dropna().sort_index()


def evaluate_strategy(frame: pd.DataFrame, mode: str, interval: str = "1d", risk_pct: float = 1.0,
                      capital: float | None = None, multi_timeframe: dict | None = None) -> dict:
    mode = str(mode).title()
    if mode not in STRATEGY_PROFILES:
        raise ValueError("mode must be Scalping, Intraday or Hedging")
    p = STRATEGY_PROFILES[mode]
    x = _clean_ohlcv(frame)
    warnings, evidence = [], []
    if len(x) < p["min_bars"]:
        return {"mode": mode, "status": "INSUFFICIENT_DATA", "bias": "WAIT", "score": 0,
                "summary": f"At least {p['min_bars']} clean OHLCV candles are required.", "evidence": [],
                "warnings": ["No trade levels are generated from insufficient history."], "entry_zone": None}
    if interval not in p["allowed_intervals"]:
        warnings.append(f"Selected interval {interval} is not a preferred interval for {mode}; treat this as context only.")
    close, high, low, vol = x.Close, x.High, x.Low, x.Volume
    ema9 = close.ewm(span=9, adjust=False).mean(); ema20 = close.ewm(span=20, adjust=False).mean(); ema50 = close.ewm(span=50, adjust=False).mean()
    delta = close.diff(); gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean(); loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rsi_s = 100 - 100/(1 + gain/loss.replace(0, np.nan))
    macd = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean(); macd_sig = macd.ewm(span=9, adjust=False).mean()
    tr = pd.concat([high-low, (high-close.shift()).abs(), (low-close.shift()).abs()], axis=1).max(axis=1)
    atr_s = tr.ewm(alpha=1/14, adjust=False).mean()
    last, atr, rsi = float(close.iloc[-1]), float(atr_s.iloc[-1]), float(rsi_s.iloc[-1]) if pd.notna(rsi_s.iloc[-1]) else 50.0
    score = 0
    fast = ema9.iloc[-1]; medium = ema20.iloc[-1]; slow = ema50.iloc[-1]
    if last > fast > medium > slow: score += 2; evidence.append("Bullish price/EMA 9-20-50 alignment")
    elif last < fast < medium < slow: score -= 2; evidence.append("Bearish price/EMA 9-20-50 alignment")
    else: warnings.append("EMA alignment is mixed; trend confirmation is incomplete.")
    if rsi >= 55: score += 1; evidence.append(f"RSI momentum positive ({rsi:.1f})")
    elif rsi <= 45: score -= 1; evidence.append(f"RSI momentum negative ({rsi:.1f})")
    else: warnings.append(f"RSI is neutral ({rsi:.1f}).")
    if macd.iloc[-1] > macd_sig.iloc[-1]: score += 1; evidence.append("MACD above signal")
    else: score -= 1; evidence.append("MACD below signal")
    avg_vol = float(vol.rolling(20).mean().iloc[-1]) if vol.notna().sum() >= 20 else 0
    relvol = float(vol.iloc[-1]/avg_vol) if avg_vol > 0 else None
    if relvol is not None and relvol >= 1.25: evidence.append(f"Relative volume {relvol:.2f}x")
    else: warnings.append("Volume expansion is not confirmed or volume data is unavailable.")
    if multi_timeframe:
        vals = [str(v).upper() for v in multi_timeframe.values() if v]
        aligned = sum(1 for v in vals if (v.startswith("BULL") and score > 0) or (v.startswith("BEAR") and score < 0))
        if vals:
            evidence.append(f"Multi-timeframe inputs: {aligned}/{len(vals)} supplied summaries align with this bias")
            if aligned < math.ceil(len(vals)*0.6): warnings.append("Higher/lower timeframe confirmation is weak or conflicting.")
    else:
        warnings.append("No independently loaded higher/lower timeframe data supplied; multi-timeframe confirmation is pending.")
    bias = "LONG" if score >= 3 else "SHORT" if score <= -3 else "WAIT"
    if mode == "Scalping" and interval not in {"1m", "2m", "5m"}:
        bias = "WAIT"; warnings.append("Scalping signal gated off: load genuine 1m/2m/5m candles before considering a setup.")
    if not np.isfinite(atr) or atr <= 0:
        bias = "WAIT"; warnings.append("ATR unavailable; trade levels withheld.")
    entry = stop = target = rr = None
    if bias in {"LONG", "SHORT"}:
        pad = 0.10*atr
        entry = [last-pad, last+pad]
        stop = last-p["stop_atr"]*atr if bias == "LONG" else last+p["stop_atr"]*atr
        target = last+p["target_atr"]*atr if bias == "LONG" else last-p["target_atr"]*atr
        rr = abs(target-last)/abs(last-stop)
    if mode == "Hedging":
        warnings.append("Hedge decision requires verified portfolio exposure, option expiry, bid/ask, OI and Greeks. This candle-only result is directional context, not a hedge recommendation.")
    if capital is not None and entry and risk_pct > 0:
        risk_cash = float(capital)*float(risk_pct)/100
        per_unit = abs(last-stop)
        quantity = int(risk_cash/per_unit) if per_unit > 0 else 0
    else:
        risk_cash = quantity = None
    return {"mode": mode, "status": "OK", "bias": bias, "score": score, "last_price": last, "rsi": rsi,
            "atr": atr, "relative_volume": relvol, "entry_zone": entry, "stop": stop, "target": target,
            "risk_reward": rr, "risk_budget": risk_cash, "illustrative_quantity": quantity,
            "horizon": p["horizon"], "evidence": evidence, "warnings": warnings,
            "summary": (f"{bias} candidate based on {score:+d} rule-based evidence score." if bias != "WAIT" else "WAIT: confirmation is insufficient or the timeframe gate is not satisfied.")}


def analyze_hedge_candidates(chain: pd.DataFrame, spot: float, side: str = "PROTECT_LONG", min_oi: int = 0) -> pd.DataFrame:
    """Rank real supplied option rows only; no theoretical contracts or premiums are generated."""
    if not isinstance(chain, pd.DataFrame) or chain.empty or not spot or spot <= 0:
        return pd.DataFrame()
    x = chain.copy()
    side = side.upper()
    if side == "PROTECT_LONG":
        needed = ["Strike", "PE LTP", "PE OI"]
        if not set(needed).issubset(x.columns): return pd.DataFrame()
        out = x[needed + [c for c in ["PE IV", "PE Delta", "Expiry", "PE Instrument"] if c in x]].copy()
        out = out.rename(columns={"PE LTP":"Premium", "PE OI":"OI", "PE IV":"IV", "PE Delta":"Delta", "PE Instrument":"Instrument"})
        out["Option"] = "PUT"
    elif side == "PROTECT_SHORT":
        needed = ["Strike", "CE LTP", "CE OI"]
        if not set(needed).issubset(x.columns): return pd.DataFrame()
        out = x[needed + [c for c in ["CE IV", "CE Delta", "Expiry", "CE Instrument"] if c in x]].copy()
        out = out.rename(columns={"CE LTP":"Premium", "CE OI":"OI", "CE IV":"IV", "CE Delta":"Delta", "CE Instrument":"Instrument"})
        out["Option"] = "CALL"
    else:
        raise ValueError("side must be PROTECT_LONG or PROTECT_SHORT")
    for col in ["Strike", "Premium", "OI"]: out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["Strike", "Premium", "OI"])
    out = out[(out.Premium > 0) & (out.OI >= int(min_oi))]
    out["DistancePct"] = (out.Strike.astype(float)-float(spot)).abs()/float(spot)*100
    out["LiquidityOK"] = out.OI >= max(int(min_oi), 1)
    return out.sort_values(["DistancePct", "OI"], ascending=[True, False]).reset_index(drop=True)


def position_size(capital: float, risk_pct: float, entry: float, stop: float, lot_size: int = 1) -> dict:
    vals = [capital, risk_pct, entry, stop, lot_size]
    if any(not np.isfinite(float(v)) for v in vals): raise ValueError("All sizing inputs must be finite numbers")
    if capital <= 0 or not 0 < risk_pct <= 5 or entry <= 0 or stop <= 0 or entry == stop or int(lot_size) < 1:
        raise ValueError("Require positive capital/prices, risk 0–5%, different entry/stop and lot size >= 1")
    budget = float(capital)*float(risk_pct)/100
    units = int(budget/abs(float(entry)-float(stop)))
    qty = (units//int(lot_size))*int(lot_size)
    return {"risk_budget": budget, "risk_per_unit": abs(float(entry)-float(stop)), "quantity": qty,
            "estimated_stop_risk": qty*abs(float(entry)-float(stop)), "notional": qty*float(entry),
            "warning": "Illustrative sizing only; excludes gap risk, slippage, fees, liquidity and margin."}


def upstox_profile(token: str, timeout: int = 15) -> dict:
    """Read-only broker connection check; token is never returned or logged."""
    if not token or not str(token).strip(): return {"ok": False, "status": "TOKEN_MISSING", "message": "Add UPSTOX_ACCESS_TOKEN to local Streamlit secrets."}
    try:
        r = requests.get("https://api.upstox.com/v2/user/profile", headers={"Accept":"application/json", "Authorization":f"Bearer {str(token).strip()}"}, timeout=timeout)
        if r.status_code == 401: return {"ok":False,"status":"UNAUTHORIZED","message":"Upstox rejected the token. Refresh it in your local secrets file."}
        if r.status_code == 403: return {"ok":False,"status":"FORBIDDEN","message":"Upstox denied profile access; check API permissions."}
        if not r.ok: return {"ok":False,"status":f"HTTP_{r.status_code}","message":f"Upstox profile request failed (HTTP {r.status_code})."}
        body = r.json(); data = body.get("data") or {}
        return {"ok":True,"status":"CONNECTED_READ_ONLY","message":"Upstox profile endpoint responded successfully.",
                "user_name":data.get("user_name") or data.get("user_name"), "email":data.get("email"), "broker":"Upstox"}
    except requests.RequestException as exc:
        return {"ok":False,"status":"NETWORK_ERROR","message":f"Network error: {exc.__class__.__name__}"}
    except ValueError:
        return {"ok":False,"status":"INVALID_RESPONSE","message":"Upstox returned an unreadable profile response."}


def broker_order_preview(symbol: str, side: str, quantity: int, order_type: str, price: float | None = None) -> dict:
    """Validate and create a review-only payload; never sends it to a broker."""
    side, order_type = str(side).upper(), str(order_type).upper()
    if not symbol or side not in {"BUY", "SELL"} or order_type not in {"MARKET", "LIMIT", "SL", "SL-M"} or int(quantity) < 1:
        raise ValueError("Invalid symbol, side, order type or quantity")
    if order_type in {"LIMIT", "SL"} and (price is None or not np.isfinite(float(price)) or float(price) <= 0):
        raise ValueError("A positive price is required for LIMIT and SL preview")
    return {"instrument_token":str(symbol),"transaction_type":side,"quantity":int(quantity),"order_type":order_type,
            "price":float(price or 0),"validity":"DAY","product":"D","disclosed_quantity":0,
            "tag":"AI_TRADE_REVIEW_ONLY","execution_enabled":False,
            "notice":"Preview only. No broker API order endpoint is called by V42."}

"""Read-only multi-asset scanner. Yahoo symbols are indicative proxies, not exchange-grade feeds."""
from __future__ import annotations
import pandas as pd
from intraday_signal_engine import timeframe_snapshot

ASSET_UNIVERSE = {
    "India Indices": ["^NSEI", "^NSEBANK", "^BSESN", "^CNXIT", "^INDIAVIX"],
    "NSE Large Caps": ["RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "INFY.NS", "TCS.NS", "LT.NS", "AXISBANK.NS", "ITC.NS", "BHARTIARTL.NS", "MARUTI.NS", "TATAMOTORS.NS", "KOTAKBANK.NS", "HINDUNILVR.NS", "BAJFINANCE.NS", "ADANIENT.NS", "SUNPHARMA.NS", "NTPC.NS", "ONGC.NS", "TATASTEEL.NS"],
    "Commodities": ["GC=F", "SI=F", "CL=F", "NG=F", "HG=F"],
    "Forex": ["USDINR=X", "EURINR=X", "GBPINR=X", "JPYINR=X", "EURUSD=X", "GBPUSD=X", "USDJPY=X", "DXY"],
    "Crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "BNB-USD", "ADA-USD", "DOGE-USD", "AVAX-USD", "LINK-USD", "LTC-USD"],
}

def _safe_fetch(fetcher, symbol, period, interval):
    try:
        frame = fetcher(symbol, period, interval)
        if frame is None or frame.empty:
            return pd.DataFrame()
        frame = frame.copy()
        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = frame.columns.get_level_values(0)
        frame.columns = [str(c).title() for c in frame.columns]
        needed = ["Open", "High", "Low", "Close", "Volume"]
        if not set(needed).issubset(frame.columns):
            return pd.DataFrame()
        for col in needed:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
        return frame[needed].dropna(subset=["Open", "High", "Low", "Close"]).sort_index()
    except Exception:
        return pd.DataFrame()

def scan_multi_asset(fetcher, categories=None, max_per_category=10, min_abs_score=2):
    """Fetch hourly and daily OHLCV, score aligned directional evidence, and return rows + coverage."""
    selected = categories or list(ASSET_UNIVERSE)
    rows, coverage = [], []
    for category in selected:
        symbols = ASSET_UNIVERSE.get(category, [])[:max(1, int(max_per_category))]
        for ticker in symbols:
            hourly = _safe_fetch(fetcher, ticker, "3mo", "1h")
            daily = _safe_fetch(fetcher, ticker, "6mo", "1d")
            h = timeframe_snapshot(hourly, "1-hour")
            d = timeframe_snapshot(daily, "1-day")
            valid = h["bias"] != "INSUFFICIENT DATA" and d["bias"] != "INSUFFICIENT DATA"
            aligned = valid and h["bias"] == d["bias"] and h["bias"] in ("BULLISH", "BEARISH")
            score = int(h["score"] + d["score"]) if valid else 0
            if not valid:
                status, bias = "INSUFFICIENT DATA", "UNAVAILABLE"
            elif aligned and abs(score) >= int(min_abs_score):
                status, bias = "ALIGNED", h["bias"]
            elif h["bias"] == "NEUTRAL" or d["bias"] == "NEUTRAL":
                status, bias = "WAIT", "NEUTRAL / MIXED"
            else:
                status, bias = "CONFLICT", "TIMEFRAME CONFLICT"
            rows.append({"Asset class": category, "Symbol": ticker, "Bias": bias, "Status": status,
                         "Score": score, "1h bias": h["bias"], "1d bias": d["bias"],
                         "Last price (1h)": h["close"], "RSI (1h)": h["rsi"],
                         "Rel. volume (1h)": h["relative_volume"],
                         "Evidence": " | ".join(h.get("reasons", []) + d.get("reasons", []))})
        coverage.append({"Asset class": category, "Requested": len(symbols),
                         "Hourly data": sum(1 for r in rows if r["Asset class"] == category and r["1h bias"] != "INSUFFICIENT DATA"),
                         "Daily data": sum(1 for r in rows if r["Asset class"] == category and r["1d bias"] != "INSUFFICIENT DATA")})
    result = pd.DataFrame(rows)
    if not result.empty:
        rank = result.Status.map({"ALIGNED": 0, "CONFLICT": 1, "WAIT": 2, "INSUFFICIENT DATA": 3}).fillna(4)
        result = result.assign(_rank=rank, _strength=result.Score.abs()).sort_values(["_rank", "_strength"], ascending=[True, False]).drop(columns=["_rank", "_strength"]).reset_index(drop=True)
    return result, pd.DataFrame(coverage)

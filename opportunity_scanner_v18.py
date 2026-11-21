"""Read-only multi-symbol intraday opportunity scanner; scores are heuristic, not probabilities."""
from __future__ import annotations
import pandas as pd
from intraday_signal_engine import combine_timeframes


def scan_symbols(symbols, fetcher, min_score: int = 2) -> pd.DataFrame:
    """Scan symbols using fetcher(symbol, period, interval) -> OHLCV DataFrame."""
    rows = []
    for symbol in symbols:
        ticker = str(symbol).strip().upper()
        if not ticker:
            continue
        try:
            five = fetcher(ticker, "5d", "5m")
            fifteen = fetcher(ticker, "1mo", "15m")
            result = combine_timeframes(five, fifteen)
            snaps = result["snapshots"]
            s5, s15 = snaps[0], snaps[1]
            score = int(result["score"])
            bias = result["bias"]
            if bias in ("BULLISH", "BEARISH") and abs(score) >= min_score:
                status = "ALIGNED"
            elif bias == "INSUFFICIENT DATA":
                status = "INSUFFICIENT DATA"
            else:
                status = "WAIT"
            rows.append({"Symbol": ticker, "Bias": bias, "Status": status,
                         "Combined score": score, "5m bias": s5["bias"],
                         "15m bias": s15["bias"], "5m close": s5["close"],
                         "15m close": s15["close"], "5m RSI": s5["rsi"],
                         "15m RSI": s15["rsi"], "5m rel. volume": s5["relative_volume"],
                         "15m rel. volume": s15["relative_volume"],
                         "Evidence": " | ".join(s5["reasons"] + s15["reasons"])})
        except Exception as exc:
            rows.append({"Symbol": ticker, "Bias": "UNAVAILABLE", "Status": "FETCH ERROR",
                         "Combined score": 0, "5m bias": "—", "15m bias": "—",
                         "5m close": None, "15m close": None, "5m RSI": None,
                         "15m RSI": None, "5m rel. volume": None,
                         "15m rel. volume": None, "Evidence": str(exc)[:180]})
    if not rows:
        return pd.DataFrame(columns=["Symbol", "Bias", "Status", "Combined score"])
    out = pd.DataFrame(rows)
    out["_rank"] = out["Combined score"].abs()
    return out.sort_values(["Status", "_rank"], ascending=[True, False]).drop(columns="_rank").reset_index(drop=True)

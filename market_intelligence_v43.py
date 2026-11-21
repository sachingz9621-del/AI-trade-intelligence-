"""V43 live market intelligence, feed health and persistent alert utilities.

Read-only market monitoring. Uses the existing Upstox V3 feed when configured;
never fabricates quotes, starts background daemons outside Streamlit, or places orders.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Any
import pandas as pd

DB_PATH = Path(__file__).resolve().parent / "ati_v43_monitor.sqlite3"


def data_quality_report(frame: pd.DataFrame | None, symbol: str = "") -> dict:
    if frame is None or not isinstance(frame, pd.DataFrame) or frame.empty:
        return {"status": "NO_DATA", "symbol": symbol, "rows": 0, "missing": [], "warnings": ["No historical candles are available."]}
    required = ["Open", "High", "Low", "Close", "Volume"]
    missing = [c for c in required if c not in frame.columns]
    if missing:
        return {"status": "INVALID_SCHEMA", "symbol": symbol, "rows": len(frame), "missing": missing,
                "warnings": ["Required OHLCV columns are missing; scanner must not run."]}
    clean = frame[required].apply(pd.to_numeric, errors="coerce")
    nulls = int(clean.isna().sum().sum())
    bad_ohlc = int(((clean.High < clean.Low) | (clean.High < clean.Open) | (clean.High < clean.Close) |
                    (clean.Low > clean.Open) | (clean.Low > clean.Close)).fillna(False).sum())
    warnings = []
    if nulls: warnings.append(f"{nulls} missing/non-numeric OHLCV values found.")
    if bad_ohlc: warnings.append(f"{bad_ohlc} candles have inconsistent OHLC ranges.")
    if len(clean) < 40: warnings.append("Fewer than 40 candles: strategy confirmation may be unavailable.")
    return {"status": "CHECK" if warnings else "OK", "symbol": symbol, "rows": len(clean),
            "missing": [], "null_cells": nulls, "invalid_ohlc_rows": bad_ohlc, "warnings": warnings}


def scan_market_frame(frame: pd.DataFrame | None, symbol: str = "", interval: str = "1d") -> dict:
    """A compact, explainable trend/momentum scan from supplied candles only."""
    quality = data_quality_report(frame, symbol)
    if quality["status"] in {"NO_DATA", "INVALID_SCHEMA"} or quality.get("invalid_ohlc_rows", 0):
        return {"symbol": symbol, "signal": "WAIT", "score": 0, "quality": quality,
                "evidence": [], "warnings": quality["warnings"] + ["Signal suppressed by data-quality gate."]}
    x = frame[["Open", "High", "Low", "Close", "Volume"]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(x) < 40:
        return {"symbol": symbol, "signal": "WAIT", "score": 0, "quality": quality,
                "evidence": [], "warnings": quality["warnings"] + ["At least 40 clean candles are required."]}
    c = x.Close
    e9, e20, e50 = (c.ewm(span=n, adjust=False).mean().iloc[-1] for n in (9, 20, 50))
    delta = c.diff(); gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean(); loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rsi_series = 100 - 100/(1 + gain/loss.replace(0, pd.NA))
    rsi = float(rsi_series.iloc[-1]) if pd.notna(rsi_series.iloc[-1]) else 50.0
    macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    macd_sig = macd.ewm(span=9, adjust=False).mean()
    score, evidence, warnings = 0, [], list(quality["warnings"])
    last = float(c.iloc[-1])
    if last > e9 > e20 > e50: score += 2; evidence.append("Bullish price/EMA 9-20-50 alignment")
    elif last < e9 < e20 < e50: score -= 2; evidence.append("Bearish price/EMA 9-20-50 alignment")
    else: warnings.append("EMA structure is mixed.")
    if rsi >= 55: score += 1; evidence.append(f"RSI momentum positive ({rsi:.1f})")
    elif rsi <= 45: score -= 1; evidence.append(f"RSI momentum negative ({rsi:.1f})")
    else: warnings.append(f"RSI is neutral ({rsi:.1f}).")
    if macd.iloc[-1] > macd_sig.iloc[-1]: score += 1; evidence.append("MACD above signal")
    else: score -= 1; evidence.append("MACD below signal")
    signal = "LONG BIAS" if score >= 3 else "SHORT BIAS" if score <= -3 else "WAIT"
    return {"symbol": symbol, "interval": interval, "signal": signal, "score": score, "last_close": last,
            "rsi": rsi, "quality": quality, "evidence": evidence, "warnings": warnings,
            "disclaimer": "Historical-candle heuristic, not a live prediction or trade instruction."}


def _connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE IF NOT EXISTS alert_rules (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, instrument_key TEXT NOT NULL, direction TEXT NOT NULL CHECK(direction IN ('above','below')), threshold REAL NOT NULL, active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL)")
    con.execute("CREATE TABLE IF NOT EXISTS alert_events (id INTEGER PRIMARY KEY AUTOINCREMENT, rule_id INTEGER NOT NULL, ltp REAL NOT NULL, triggered_at TEXT NOT NULL, FOREIGN KEY(rule_id) REFERENCES alert_rules(id))")
    con.commit()
    return con


def add_alert_rule(name: str, instrument_key: str, direction: str, threshold: float) -> int:
    direction = str(direction).lower(); threshold = float(threshold)
    if not str(name).strip() or not str(instrument_key).strip() or direction not in {"above", "below"} or threshold <= 0:
        raise ValueError("Provide a name, instrument key, above/below direction and positive threshold.")
    with _connect() as con:
        cur = con.execute("INSERT INTO alert_rules(name,instrument_key,direction,threshold,active,created_at) VALUES(?,?,?,?,1,?)",
                          (str(name).strip(), str(instrument_key).strip(), direction, threshold, datetime.now(timezone.utc).isoformat()))
        return int(cur.lastrowid)


def list_alert_rules() -> pd.DataFrame:
    with _connect() as con:
        rows = con.execute("SELECT * FROM alert_rules ORDER BY id DESC").fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def deactivate_alert_rule(rule_id: int) -> None:
    with _connect() as con:
        con.execute("UPDATE alert_rules SET active=0 WHERE id=?", (int(rule_id),))


def evaluate_feed_alerts(instruments: dict[str, dict]) -> list[dict]:
    fired = []
    with _connect() as con:
        rules = con.execute("SELECT * FROM alert_rules WHERE active=1").fetchall()
        for rule in rules:
            quote = instruments.get(rule["instrument_key"], {}) or {}
            ltp = quote.get("ltp")
            if ltp is None: continue
            hit = float(ltp) >= float(rule["threshold"]) if rule["direction"] == "above" else float(ltp) <= float(rule["threshold"])
            if hit:
                con.execute("INSERT INTO alert_events(rule_id,ltp,triggered_at) VALUES(?,?,?)",
                            (rule["id"], float(ltp), datetime.now(timezone.utc).isoformat()))
                fired.append({"id": rule["id"], "name": rule["name"], "instrument_key": rule["instrument_key"],
                              "ltp": float(ltp), "threshold": float(rule["threshold"]), "direction": rule["direction"]})
    return fired


def list_alert_events(limit: int = 100) -> pd.DataFrame:
    with _connect() as con:
        rows = con.execute("SELECT e.id,e.rule_id,r.name,r.instrument_key,e.ltp,e.triggered_at FROM alert_events e JOIN alert_rules r ON r.id=e.rule_id ORDER BY e.id DESC LIMIT ?", (int(limit),)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])

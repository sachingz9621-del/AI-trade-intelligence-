"""V36 live-feed operations, quote normalization and rule-based alert checks.

Read-only diagnostics for the existing Upstox V3 websocket payload. This module
never places orders and never labels OHLCV-derived patterns as institutional flow.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any


def _dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _first_dict_path(root: dict, paths: tuple[tuple[str, ...], ...]) -> dict:
    for path in paths:
        node: Any = root
        for key in path:
            node = _dict(node).get(key)
        if isinstance(node, dict) and node:
            return node
    return {}


def normalize_upstox_feed(feed: dict) -> dict:
    """Extract common Upstox V3 full-feed/ltpc fields without assuming all exist."""
    root = _dict(feed)
    ltpc = _first_dict_path(root, (
        ("fullFeed", "marketFF", "ltpc"),
        ("fullFeed", "indexFF", "ltpc"),
        ("ltpc",),
    ))
    market = _first_dict_path(root, (("fullFeed", "marketFF"), ("fullFeed", "indexFF")))
    ohlc = _dict(market.get("marketOHLC"))
    if not ohlc:
        ohlc = _dict(market.get("ohlc"))
    def number(value):
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None
    ltp = number(ltpc.get("ltp"))
    close = number(ltpc.get("cp"))
    change_pct = ((ltp-close)/close*100) if ltp is not None and close not in (None, 0) else None
    return {
        "ltp": ltp, "previous_close": close, "change_pct": change_pct,
        "last_trade_time": ltpc.get("ltt"),
        "volume": number(ltpc.get("vtt") or market.get("vtt")),
        "oi": number(ltpc.get("oi") or market.get("oi")),
        "open": number(ohlc.get("open")), "high": number(ohlc.get("high")),
        "low": number(ohlc.get("low")),
        "has_price": ltp is not None,
    }


def build_operations_report(market_data: dict, status: dict, stale_after_seconds: int = 30) -> dict:
    """Summarize feed health and normalized instrument quotes."""
    market_data = _dict(market_data)
    status = _dict(status)
    feeds = _dict(market_data.get("feeds")) or {k: v for k, v in market_data.items()
                                               if k not in {"last_update", "message_type"}}
    instruments = {str(key): normalize_upstox_feed(_dict(value)) for key, value in feeds.items()}
    instruments = {k: v for k, v in instruments.items() if v.get("has_price") or v.get("volume") is not None or v.get("oi") is not None}
    updated = market_data.get("last_update")
    state = status.get("state", "unknown")
    connected = bool(status.get("connected")) and state == "connected"
    msg_count = int(status.get("message_count") or 0)
    warnings = []
    if not connected:
        warnings.append("WebSocket is not confirmed connected.")
    if not instruments:
        warnings.append("No recognizable instrument quotes are present in the latest feed snapshot.")
    if msg_count == 0:
        warnings.append("No websocket messages have been received in this session.")
    if status.get("last_error"):
        warnings.append(f"Last feed error: {status['last_error']}")
    freshness = "Unknown"
    if updated:
        freshness = "Timestamp present; age not independently verified"
    if connected and msg_count > 0 and instruments:
        health = "Receiving data"
    elif state in {"error", "disconnected", "stopped"}:
        health = "Offline / needs attention"
    else:
        health = "Connecting / awaiting valid ticks"
    return {
        "health": health, "state": state, "connected": connected,
        "message_count": msg_count, "last_message_at": status.get("last_message_at"),
        "last_update": updated, "freshness": freshness,
        "instrument_count": len(instruments), "instruments": instruments,
        "warnings": warnings,
        "limitations": [
            "The feed's last-update label is not a per-instrument exchange timestamp.",
            "Missing fields are shown as unavailable; no prices or institutional flows are inferred.",
            "This monitor is read-only and does not submit broker orders.",
        ],
    }


def evaluate_price_alerts(instruments: dict, rules: list[dict]) -> list[dict]:
    """Evaluate simple LTP threshold rules; caller owns persistence/deduplication."""
    results = []
    for rule in rules:
        key = str(rule.get("instrument_key", ""))
        quote = _dict(instruments.get(key))
        ltp = quote.get("ltp")
        threshold = rule.get("threshold")
        direction = str(rule.get("direction", "above")).lower()
        try:
            threshold = float(threshold)
        except (TypeError, ValueError):
            continue
        if ltp is None or direction not in {"above", "below"}:
            continue
        triggered = float(ltp) >= threshold if direction == "above" else float(ltp) <= threshold
        results.append({"name": rule.get("name") or key, "instrument_key": key,
                        "ltp": float(ltp), "direction": direction,
                        "threshold": threshold, "triggered": triggered})
    return results

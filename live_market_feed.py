"""Read-only Upstox V3 websocket feed with thread-safe status diagnostics.

This module never places orders. Token is read from .streamlit/secrets.toml.
"""
from __future__ import annotations
import threading
import tomllib
from pathlib import Path
from datetime import datetime
from typing import Any

_lock = threading.RLock()
_market_data: dict[str, Any] = {}
_streamer = None
_thread = None
_status = {
    "state": "stopped", "message": "Feed has not been started",
    "connected": False, "started_at": None, "last_message_at": None,
    "last_error": None, "message_count": 0,
}


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _set_status(**kwargs):
    with _lock:
        _status.update(kwargs)


def get_feed_status() -> dict:
    with _lock:
        return dict(_status)


def get_market_data() -> dict:
    with _lock:
        return dict(_market_data)


def start_live_feed(instrument_keys=None) -> str:
    """Start one websocket connection. Returns a human-readable status."""
    global _streamer, _thread
    with _lock:
        if _status["state"] in {"starting", "connected"}:
            return "Live feed is already running or connecting."
        _status.update(state="starting", message="Connecting to Upstox...",
                       connected=False, started_at=_now(), last_error=None,
                       message_count=0)
    try:
        secrets_path = Path(__file__).resolve().parent / ".streamlit" / "secrets.toml"
        if not secrets_path.exists():
            raise FileNotFoundError(".streamlit/secrets.toml not found. Create it from secrets.toml.example.")
        with secrets_path.open("rb") as handle:
            secrets = tomllib.load(handle)
        token = str(secrets.get("UPSTOX_ACCESS_TOKEN", "")).strip()
        if not token or "PASTE_YOUR" in token:
            raise ValueError("A valid UPSTOX_ACCESS_TOKEN is missing from .streamlit/secrets.toml.")

        import upstox_client
        configuration = upstox_client.Configuration()
        configuration.access_token = token
        api_client = upstox_client.ApiClient(configuration)
        keys = instrument_keys or ["NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank", "NSE_INDEX|India VIX"]
        _streamer = upstox_client.MarketDataStreamerV3(api_client, keys, "full")

        def on_open(*_args):
            _set_status(state="connected", connected=True, message="WebSocket connected", last_error=None)

        def on_message(message, *_args):
            global _market_data
            payload = message
            if isinstance(payload, str):
                import json
                try: payload = json.loads(payload)
                except Exception: payload = {"raw_message": payload}
            if isinstance(payload, dict):
                feeds = payload.get("feeds")
                with _lock:
                    if isinstance(feeds, dict):
                        _market_data.update(feeds)
                    _market_data["last_update"] = datetime.now().astimezone().strftime("%H:%M:%S %Z")
                    _market_data["message_type"] = payload.get("type", "unknown")
                    _status.update(last_message_at=_now(), message_count=_status["message_count"] + 1,
                                   message="Receiving market messages")

        def on_error(error, *_args):
            _set_status(state="error", connected=False, message="WebSocket error", last_error=str(error))

        def on_close(*_args):
            _set_status(state="disconnected", connected=False, message="WebSocket connection closed")

        _streamer.on("open", on_open)
        _streamer.on("message", on_message)
        _streamer.on("error", on_error)
        _streamer.on("close", on_close)
        _thread = threading.Thread(target=_streamer.connect, name="upstox-market-feed", daemon=True)
        _thread.start()
        return "Upstox connection is starting. Wait for the connection status to update."
    except Exception as exc:
        _set_status(state="error", connected=False, message="Could not start live feed", last_error=str(exc))
        return f"Connection error: {exc}"


def stop_live_feed() -> str:
    global _streamer
    if _streamer is None:
        _set_status(state="stopped", connected=False, message="Feed is not running")
        return "Feed is not running."
    try:
        disconnect = getattr(_streamer, "disconnect", None)
        if callable(disconnect): disconnect()
        _set_status(state="stopped", connected=False, message="Feed stopped by user")
        return "Disconnect requested."
    except Exception as exc:
        _set_status(state="error", connected=False, message="Error stopping feed", last_error=str(exc))
        return f"Could not stop feed: {exc}"

"""Read-only Upstox option-chain client. Uses official v2 REST endpoints."""
from __future__ import annotations
import requests

BASE = "https://api.upstox.com/v2"
UNDERLYINGS = {
    "NIFTY 50": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "FINNIFTY": "NSE_INDEX|Nifty Fin Service",
    "SENSEX": "BSE_INDEX|SENSEX",
}

class UpstoxOptionsError(RuntimeError):
    pass

def _get(path: str, token: str, params: dict | None = None):
    if not token or not token.strip():
        raise UpstoxOptionsError("Upstox access token is missing. Add UPSTOX_ACCESS_TOKEN to .streamlit/secrets.toml.")
    try:
        response = requests.get(BASE + path, params=params or {}, headers={
            "Accept": "application/json", "Authorization": f"Bearer {token.strip()}"
        }, timeout=20)
    except requests.RequestException as exc:
        raise UpstoxOptionsError(f"Network error contacting Upstox: {exc}") from exc
    if response.status_code == 401:
        raise UpstoxOptionsError("Upstox rejected the token (401). Generate/refresh your access token.")
    if response.status_code == 403:
        raise UpstoxOptionsError("Upstox denied this API request (403). Check API permissions and subscription.")
    try:
        body = response.json()
    except ValueError:
        body = {}
    if not response.ok or body.get("status") == "error":
        raise UpstoxOptionsError(f"Upstox API error ({response.status_code}): {body.get('errors') or body.get('message') or response.text[:300]}")
    return body.get("data", [])

def get_expiries(token: str, underlying_key: str) -> list[str]:
    contracts = _get("/option/contract", token, {"instrument_key": underlying_key})
    expiries = sorted({str(row.get("expiry")) for row in contracts if row.get("expiry")})
    if not expiries:
        raise UpstoxOptionsError("No option expiries returned for this underlying. Verify the instrument key and market availability.")
    return expiries

def get_option_chain(token: str, underlying_key: str, expiry: str) -> list[dict]:
    rows = _get("/option/chain", token, {"instrument_key": underlying_key, "expiry_date": expiry})
    if not rows:
        raise UpstoxOptionsError("Upstox returned an empty option chain for this expiry.")
    return rows

def flatten_chain(rows: list[dict]):
    import pandas as pd
    output = []
    for row in rows:
        call = row.get("call_options") or {}
        put = row.get("put_options") or {}
        cm = call.get("market_data") or {}; pm = put.get("market_data") or {}
        cg = call.get("option_greeks") or {}; pg = put.get("option_greeks") or {}
        output.append({
            "Expiry": row.get("expiry"), "Strike": row.get("strike_price"),
            "Spot": row.get("underlying_spot_price"), "PCR": row.get("pcr"),
            "CE LTP": cm.get("ltp"), "CE OI": cm.get("oi"), "CE Prev OI": cm.get("prev_oi"),
            "CE OI Change": (float(cm.get("oi") or 0)-float(cm.get("prev_oi") or 0)),
            "CE Volume": cm.get("volume"), "CE IV": cg.get("iv"), "CE Delta": cg.get("delta"),
            "CE Gamma": cg.get("gamma"), "CE Theta": cg.get("theta"), "CE Vega": cg.get("vega"),
            "PE LTP": pm.get("ltp"), "PE OI": pm.get("oi"), "PE Prev OI": pm.get("prev_oi"),
            "PE OI Change": (float(pm.get("oi") or 0)-float(pm.get("prev_oi") or 0)),
            "PE Volume": pm.get("volume"), "PE IV": pg.get("iv"), "PE Delta": pg.get("delta"),
            "PE Gamma": pg.get("gamma"), "PE Theta": pg.get("theta"), "PE Vega": pg.get("vega"),
            "CE Instrument": call.get("instrument_key"), "PE Instrument": put.get("instrument_key"),
        })
    frame = pd.DataFrame(output)
    if frame.empty:
        return frame
    return frame.sort_values("Strike").reset_index(drop=True)

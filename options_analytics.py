"""CSV-based option-chain analytics. No live quotes are fabricated."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd

ALIASES = {
    "strike": ["strike", "strikeprice", "strike_price"],
    "ce_oi": ["ce_oi", "call_oi", "callopeninterest", "ceopeninterest"],
    "pe_oi": ["pe_oi", "put_oi", "putopeninterest", "peopeninterest"],
    "ce_change": ["ce_change_oi", "ce_oi_change", "callchangeoi", "cechangeinopeninterest"],
    "pe_change": ["pe_change_oi", "pe_oi_change", "putchangeoi", "pechangeinopeninterest"],
    "ce_ltp": ["ce_ltp", "call_ltp", "callltp", "ce_lastprice"],
    "pe_ltp": ["pe_ltp", "put_ltp", "putltp", "pe_lastprice"],
    "ce_iv": ["ce_iv", "call_iv", "calliv", "ceimpliedvolatility"],
    "pe_iv": ["pe_iv", "put_iv", "putiv", "peimpliedvolatility"],
}

def _norm(value: object) -> str:
    return "".join(ch for ch in str(value).lower() if ch.isalnum())

def parse_chain(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str | None]]:
    df = frame.copy()
    lookup = {_norm(c): c for c in df.columns}
    cols: dict[str, str | None] = {}
    for key, aliases in ALIASES.items():
        cols[key] = next((lookup[_norm(a)] for a in aliases if _norm(a) in lookup), None)
    if not cols["strike"] or not cols["ce_oi"] or not cols["pe_oi"]:
        raise ValueError("CSV must include Strike, CE_OI and PE_OI (or equivalent Call/Put OI columns).")
    for col in filter(None, cols.values()):
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "", regex=False), errors="coerce")
    df = df.dropna(subset=[cols["strike"]]).sort_values(cols["strike"]).reset_index(drop=True)
    for key in ("ce_oi", "pe_oi", "ce_change", "pe_change"):
        if cols[key]: df[cols[key]] = df[cols[key]].fillna(0).clip(lower=0) if key.endswith("oi") else df[cols[key]].fillna(0)
    return df, cols

def max_pain(df: pd.DataFrame, strike_col: str, call_oi_col: str, put_oi_col: str) -> tuple[float, pd.DataFrame]:
    clean = df[[strike_col, call_oi_col, put_oi_col]].dropna().copy()
    if clean.empty: raise ValueError("No valid strike/OI rows available for Max Pain.")
    strikes = clean[strike_col].to_numpy(float)
    calls = clean[call_oi_col].fillna(0).to_numpy(float)
    puts = clean[put_oi_col].fillna(0).to_numpy(float)
    payouts = []
    for settlement in strikes:
        payouts.append(float((np.maximum(settlement-strikes, 0)*calls + np.maximum(strikes-settlement, 0)*puts).sum()))
    out = pd.DataFrame({"Settlement": strikes, "Estimated payout": payouts})
    return float(out.loc[out["Estimated payout"].idxmin(), "Settlement"]), out

def _cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def bs_greeks(spot: float, strike: float, days: float, rate_pct: float, iv_pct: float, option_type: str) -> dict[str, float]:
    """European Black-Scholes Greeks; IV/rate are entered as percentages."""
    if min(spot, strike, days, iv_pct) <= 0:
        return {k: float("nan") for k in ("Delta", "Gamma", "Theta/day", "Vega/1%")}
    t, sigma, rate = days / 365.0, iv_pct / 100.0, rate_pct / 100.0
    root_t = math.sqrt(t)
    d1 = (math.log(spot/strike) + (rate + 0.5*sigma*sigma)*t)/(sigma*root_t)
    d2 = d1 - sigma*root_t
    pdf = math.exp(-0.5*d1*d1)/math.sqrt(2*math.pi)
    call = option_type.upper() == "CE"
    delta = _cdf(d1) if call else _cdf(d1)-1
    gamma = pdf/(spot*sigma*root_t)
    theta_year = -(spot*pdf*sigma)/(2*root_t) + (-1 if call else 1)*rate*strike*math.exp(-rate*t)*(_cdf(d2) if call else _cdf(-d2))
    vega = spot*pdf*root_t/100.0
    return {"Delta": delta, "Gamma": gamma, "Theta/day": theta_year/365.0, "Vega/1%": vega}

def add_greeks(df: pd.DataFrame, cols: dict[str, str | None], spot: float, days: float, rate_pct: float) -> pd.DataFrame:
    out = df.copy()
    strike_col = cols["strike"]
    for side in ("CE", "PE"):
        iv_col = cols[f"{side.lower()}_iv"]
        if not iv_col: continue
        for greek in ("Delta", "Gamma", "Theta/day", "Vega/1%"):
            out[f"{side} {greek}"] = [bs_greeks(spot, float(k), days, rate_pct, float(iv), side)[greek]
                if pd.notna(k) and pd.notna(iv) else np.nan for k, iv in zip(out[strike_col], out[iv_col])]
    return out

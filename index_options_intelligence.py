"""Transparent index/options context from user-supplied option-chain CSV data."""
from __future__ import annotations
import numpy as np
import pandas as pd
from options_analytics import parse_chain, max_pain


def analyze_option_context(frame: pd.DataFrame, spot: float) -> dict:
    if not np.isfinite(spot) or spot <= 0:
        raise ValueError("Underlying spot must be a positive number.")
    df, cols = parse_chain(frame)
    strike, ce, pe = cols["strike"], cols["ce_oi"], cols["pe_oi"]
    calls = pd.to_numeric(df[ce], errors="coerce").fillna(0).clip(lower=0)
    puts = pd.to_numeric(df[pe], errors="coerce").fillna(0).clip(lower=0)
    call_total, put_total = float(calls.sum()), float(puts.sum())
    pcr = put_total / call_total if call_total > 0 else np.nan
    call_wall = float(df.loc[calls.idxmax(), strike]) if len(df) and calls.max() > 0 else np.nan
    put_wall = float(df.loc[puts.idxmax(), strike]) if len(df) and puts.max() > 0 else np.nan
    pain, curve = max_pain(df, strike, ce, pe)
    atm_idx = (df[strike] - spot).abs().idxmin()
    atm = float(df.loc[atm_idx, strike])

    call_add = put_add = None
    if cols["ce_change"]:
        call_add = float(pd.to_numeric(df[cols["ce_change"]], errors="coerce").fillna(0).sum())
    if cols["pe_change"]:
        put_add = float(pd.to_numeric(df[cols["pe_change"]], errors="coerce").fillna(0).sum())

    bull, bear, notes = 0, 0, []
    if np.isfinite(pcr):
        if pcr >= 1.2: bull += 1; notes.append("Aggregate PCR is elevated (put OI exceeds call OI).")
        elif pcr <= 0.8: bear += 1; notes.append("Aggregate PCR is low (call OI exceeds put OI).")
        else: notes.append("Aggregate PCR is between 0.8 and 1.2: broadly balanced.")
    if np.isfinite(put_wall) and put_wall >= spot: bull += 1; notes.append("Largest put-OI strike is at/above spot.")
    if np.isfinite(call_wall) and call_wall <= spot: bear += 1; notes.append("Largest call-OI strike is at/below spot.")
    if put_add is not None and call_add is not None:
        if put_add > 0 and call_add < 0: bull += 1; notes.append("Net put OI addition with call OI reduction.")
        elif call_add > 0 and put_add < 0: bear += 1; notes.append("Net call OI addition with put OI reduction.")
        else: notes.append("OI-change totals do not show a clear one-sided build-up.")
    bias = "BULLISH OI CONTEXT" if bull >= bear + 2 else "BEARISH OI CONTEXT" if bear >= bull + 2 else "MIXED / WAIT"
    return {
        "spot": float(spot), "atm_strike": atm, "call_oi_total": call_total,
        "put_oi_total": put_total, "pcr": pcr, "call_wall": call_wall,
        "put_wall": put_wall, "max_pain": float(pain), "bias": bias,
        "bull_points": bull, "bear_points": bear, "notes": notes,
        "call_oi_change": call_add, "put_oi_change": put_add,
        "curve": curve, "chain": df, "columns": cols,
        "warning": "OI-based context only, not a trade signal. OI walls and PCR can change quickly; verify expiry, timestamps, lot conventions and live quotes with your broker."
    }

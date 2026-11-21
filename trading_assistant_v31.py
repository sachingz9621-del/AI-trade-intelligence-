"""V31 context-aware trading Q&A assistant. Local deterministic explanations; no external LLM."""
from __future__ import annotations
import re
import pandas as pd

EDUCATION = {
    "rsi": "RSI measures momentum on a 0–100 scale. Above 70 is often called overbought and below 30 oversold, but strong trends can remain extreme. Use it with price structure and volume, not alone.",
    "macd": "MACD compares faster and slower exponential moving averages. A MACD line above its signal line is commonly read as positive momentum; crossovers can lag and work poorly in sideways markets.",
    "ema": "An EMA gives more weight to recent prices. EMA20/50/200 are commonly used to inspect short-, medium- and long-term trend alignment. They are dynamic references, not guaranteed support or resistance.",
    "pcr": "Put–Call Ratio (PCR) compares put open interest with call open interest. Its interpretation depends on market, expiry, strike distribution and participant positioning; it is not a standalone bullish/bearish signal.",
    "max pain": "Max Pain is the expiry underlying level at which the aggregate intrinsic payout to option holders is lowest under the selected open-interest snapshot. It is descriptive, changes with OI and does not predict settlement.",
    "open interest": "Open interest is the number of outstanding option/futures contracts. Changes can help describe participation, but OI alone cannot identify who opened a position or guarantee direction.",
    "iv": "Implied volatility is the volatility embedded in option prices. Higher IV generally means more expensive option premiums, all else equal. IV is not a forecast of direction.",
    "atr": "ATR estimates recent trading range/volatility. It can help scale illustrative stops and position size, but does not predict direction or protect against gaps/slippage.",
    "vwap": "VWAP is the volume-weighted average price for a session or chosen period. Traders often compare price with VWAP for intraday context; it is not a guaranteed support/resistance level.",
}


def _latest(frame):
    if not isinstance(frame, pd.DataFrame) or frame.empty or 'Close' not in frame: return None
    row=frame.iloc[-1]
    def val(k):
        try:
            x=float(row[k]); return round(x, 2) if pd.notna(x) else None
        except Exception: return None
    return {k:val(k) for k in ['Close','RSI','MACD','MACD_Signal','EMA20','EMA50','EMA200','ATR','Volume']}


def build_context(symbol, frames=None, v30_result=None, option_chain=None, chain_meta=None):
    frames=frames or {}
    out=[f"Instrument selected in the terminal: {symbol}."]
    available=[]
    for tf, df in frames.items():
        snap=_latest(df)
        if snap:
            available.append(tf)
            out.append(f"{tf} latest candle snapshot: {snap}.")
    if v30_result:
        t=v30_result.get('technical',{})
        out.append(f"V30 verdict: {v30_result.get('verdict')}; confluence score: {v30_result.get('confluence_score')}; technical direction: {t.get('direction')}; quality: {t.get('quality')}; news risk: {v30_result.get('news_risk')}.")
        if v30_result.get('evidence'): out.append("V30 evidence: " + "; ".join(v30_result['evidence']) + ".")
        if v30_result.get('warnings'): out.append("V30 warnings: " + "; ".join(v30_result['warnings']) + ".")
    if isinstance(option_chain,pd.DataFrame) and not option_chain.empty:
        try:
            from options_intelligence_v28 import analyze_option_chain
            opt=analyze_option_chain(option_chain)
            out.append(f"Options snapshot ({(chain_meta or {}).get('underlying','underlying unknown')}, expiry {(chain_meta or {}).get('expiry','unknown')}): PCR {opt.get('pcr')}, Max Pain {opt.get('max_pain')}, call OI wall {opt.get('max_call_oi_strike')}, put OI wall {opt.get('max_put_oi_strike')}, positioning {opt.get('positioning')}.")
        except Exception: out.append("An options chain is loaded, but its summary could not be calculated.")
    else: out.append("No options-chain snapshot is currently loaded in this session.")
    if not available: out.append("No timeframe candle snapshots are currently loaded. Refresh V30 evidence or load market data first.")
    return "\n".join(out)


def answer_question(question, symbol='UNKNOWN', frames=None, v30_result=None, option_chain=None, chain_meta=None):
    q=(question or '').strip()
    if not q: return "Enter a question about the selected instrument, indicators, options context or risk."
    low=q.lower()
    context=build_context(symbol,frames,v30_result,option_chain,chain_meta)
    for term, explanation in EDUCATION.items():
        if term in low:
            return explanation + "\n\nCurrent terminal context:\n" + context + "\n\nUse the displayed timestamp/source status to check freshness before relying on any reading."
    if any(x in low for x in ['what is the bias','current bias','trend','bullish or bearish','direction']):
        if not v30_result:
            return "I cannot determine a current confluence verdict yet because V30 evidence has not been refreshed. Open V30 Trade Confirmation and refresh the timeframe/news evidence.\n\n"+context
        t=v30_result.get('technical',{})
        return (f"For {symbol}, the latest V30 rule-based assessment is **{v30_result.get('verdict')}**. Technical direction: {t.get('direction','not available')}; quality: {t.get('quality','not available')}; confluence score: {v30_result.get('confluence_score')}; news risk: {v30_result.get('news_risk')}.\n\n"
                + "Evidence: " + ("; ".join(v30_result.get('evidence',[])) or "No additional confluence evidence recorded.") + "\n\n"
                + "Warnings: " + ("; ".join(v30_result.get('warnings',[])) or "No additional rule-based warnings flagged.") + "\n\nThis is a rules-based review label, not a probability, forecast or trade recommendation.")
    if any(x in low for x in ['option','strategy','call','put','spread','straddle','strangle']):
        return "I can explain option concepts and summarize the currently loaded chain, but this assistant does not invent missing premiums or select a guaranteed profitable strategy. Fetch the desired expiry in V15 Live Options Intelligence, then review V28 Options Intelligence and V29 Strategy Generator.\n\n"+context
    if any(x in low for x in ['risk','quantity','position size','stop loss','stop-loss','target']):
        return "For risk review, define the maximum rupee amount you are willing to lose first. Position size is generally derived from risk budget divided by per-unit loss to the invalidation level; then account for lot size, costs, slippage, gaps and liquidity. V30's ATR ticket is an illustrative cash-equity calculation, not an options lot-size or broker-ready order.\n\n"+context
    if any(x in low for x in ['news','headline','event']):
        if v30_result:
            return f"V30 currently labels the news context **{v30_result.get('news_risk','not available')}**. Review original headlines, publication times and the relevant event calendar; keyword/priority labels are a screening aid, not a verified directional sentiment signal.\n\n"+context
        return "No refreshed V30 news assessment is available in this session. Refresh V30 evidence, then inspect the original headlines and timestamps.\n\n"+context
    return ("I can answer indicator questions (RSI, MACD, EMA, VWAP, ATR), explain PCR/Max Pain/OI/IV, summarize the V30 bias, discuss options workflow, or explain risk sizing. I only use data currently loaded in this app session; I do not have independent live-market access or an external language-model connection here.\n\n"
            + "Current terminal context:\n"+context)

"""V21 explainable news, priority, sector and cross-asset intelligence helpers.
All headline scoring is rules-based and must not be interpreted as a forecast.
"""
from __future__ import annotations
import re
from datetime import datetime, timezone
import pandas as pd

POSITIVE = ["beats estimates", "profit rises", "profit growth", "strong demand", "raises guidance", "upgrade", "record profit", "growth accelerates", "rate cut"]
NEGATIVE = ["misses estimates", "profit falls", "profit decline", "weak demand", "cuts guidance", "downgrade", "loss widens", "default", "fraud", "war", "attack", "sanctions", "rate hike"]
HIGH_RISK = ["rbi", "federal reserve", "fomc", "inflation", "cpi", "repo rate", "rate decision", "sebi", "ban", "sanction", "war", "attack", "default", "crisis", "emergency", "opec", "crude oil"]
SECTORS = {
    "Banking": ["bank", "rbi", "repo rate", "credit growth", "npa", "loan", "lender", "deposit"],
    "IT": ["information technology", "software", "it services", "ai", "cloud", "tcs", "infosys", "wipro"],
    "Pharma": ["pharma", "drug", "fda", "clinical trial", "medicine", "healthcare"],
    "Auto": ["auto", "automobile", "car sales", "ev", "vehicle", "maruti", "tata motors"],
    "FMCG": ["fmcg", "consumer goods", "rural demand", "food prices", "consumer staples"],
    "Energy": ["crude", "oil", "gas", "opec", "petroleum", "renewable", "power"],
    "Metals": ["steel", "copper", "aluminium", "metal", "iron ore", "china", "mining"],
}
ASSETS = {
    "NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC", "Nikkei 225": "^N225", "Hang Seng": "^HSI",
    "Crude Oil": "CL=F", "Gold": "GC=F", "USD/INR": "INR=X",
}

def score_headline(headline: str, source: str = "", published: str = "") -> dict:
    text = re.sub(r"\s+", " ", str(headline or "")).strip().lower()
    pos = sum(1 for x in POSITIVE if x in text)
    neg = sum(1 for x in NEGATIVE if x in text)
    sentiment = "Positive" if pos > neg else "Negative" if neg > pos else "Neutral / unclear"
    strength = min(1.0, abs(pos-neg) / max(1, pos+neg))
    age_hours = None
    try:
        dt = pd.to_datetime(published, utc=True, errors="coerce")
        if pd.notna(dt): age_hours = max(0.0, (pd.Timestamp.now(tz="UTC")-dt).total_seconds()/3600)
    except Exception: pass
    freshness = 1.0 if age_hours is None else max(0.0, 1.0-age_hours/72)
    risk_hits = [x for x in HIGH_RISK if x in text]
    source_weight = 1.0 if any(x in str(source).lower() for x in ["rbi", "federal reserve", "cnbc", "bloomberg", "business standard", "economic times"]) else 0.75
    priority = round(min(100, (25 + 14*len(risk_hits) + 12*min(pos+neg, 2))*freshness*source_weight), 1)
    if priority >= 65: level = "High"
    elif priority >= 35: level = "Medium"
    else: level = "Low"
    sector_hits = [sector for sector, terms in SECTORS.items() if any(t in text for t in terms)]
    return {"Sentiment": sentiment, "Sentiment strength": round(strength,2), "Priority score": priority,
            "Priority": level, "Matched risk terms": ", ".join(risk_hits) or "None",
            "Potential sectors": ", ".join(sector_hits) or "General / review manually",
            "Headline age (hours)": round(age_hours,1) if age_hours is not None else None}

def enrich_news(news: pd.DataFrame) -> pd.DataFrame:
    if news is None or news.empty: return pd.DataFrame()
    base = news.copy().reset_index(drop=True)
    scored = [score_headline(r.get("Headline", ""), r.get("Source", ""), r.get("Published (UTC)", "")) for r in base.to_dict("records")]
    return pd.concat([base, pd.DataFrame(scored)], axis=1).sort_values(["Priority score", "Published (UTC)"], ascending=[False, False], na_position="last").reset_index(drop=True)

def fetch_cross_asset_snapshot(period="3mo") -> pd.DataFrame:
    """Yahoo Finance is used only as a secondary cross-asset price feed, not as news."""
    try:
        import yfinance as yf
        raw = yf.download(list(ASSETS.values()), period=period, interval="1d", auto_adjust=True, progress=False, threads=False)
        if raw is None or raw.empty: return pd.DataFrame()
        close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
        rows=[]
        for label, ticker in ASSETS.items():
            try:
                series = close[ticker].dropna() if ticker in close.columns else pd.Series(dtype=float)
                if len(series) < 2: continue
                last=float(series.iloc[-1]); prev=float(series.iloc[-2])
                rows.append({"Market / Asset":label,"Last":last,"Daily change %":(last/prev-1)*100 if prev else None,"Data date":str(series.index[-1].date()),"Ticker":ticker})
            except Exception: continue
        return pd.DataFrame(rows)
    except Exception: return pd.DataFrame()

def correlation_matrix(period="6mo") -> pd.DataFrame:
    try:
        import yfinance as yf
        tickers=list(ASSETS.values())
        raw=yf.download(tickers, period=period, interval="1d", auto_adjust=True, progress=False, threads=False)
        if raw is None or raw.empty: return pd.DataFrame()
        close=raw["Close"] if isinstance(raw.columns,pd.MultiIndex) else raw[["Close"]]
        close=close.dropna(axis=1, how="all")
        returns=close.pct_change().dropna()
        if returns.empty: return pd.DataFrame()
        reverse={v:k for k,v in ASSETS.items()}
        returns=returns.rename(columns=reverse)
        return returns.corr().round(2)
    except Exception: return pd.DataFrame()

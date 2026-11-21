"""V13 transparent market-regime and index-confluence research helpers.
All scores are OHLCV-derived heuristics, not probabilities or institutional flow data.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

REQ = {"Open", "High", "Low", "Close", "Volume"}

def _clean(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or not REQ.issubset(df.columns):
        raise ValueError("OHLCV data must contain Open, High, Low, Close and Volume")
    x=df.copy().sort_index()
    for c in REQ: x[c]=pd.to_numeric(x[c],errors="coerce")
    return x.dropna(subset=["High","Low","Close"])

def regime_intelligence(df: pd.DataFrame, window: int = 20) -> dict:
    x=_clean(df)
    if len(x)<max(50,window+5):
        return {"status":"Insufficient history","regime":"Unknown","trend":"Unknown","volatility":"Unknown","trend_score":0.0,"atr_pct":np.nan,"efficiency_ratio":np.nan}
    close=x.Close; ema_fast=close.ewm(span=20,adjust=False).mean(); ema_slow=close.ewm(span=50,adjust=False).mean()
    delta=close.diff().abs(); net=(close-close.shift(window)).abs().iloc[-1]; path=delta.rolling(window).sum().iloc[-1]
    er=float(net/path) if pd.notna(path) and path>0 else 0.0
    tr=pd.concat([x.High-x.Low,(x.High-close.shift()).abs(),(x.Low-close.shift()).abs()],axis=1).max(axis=1)
    atr=float(tr.rolling(14).mean().iloc[-1]); last=float(close.iloc[-1]); atr_pct=atr/last*100 if last else np.nan
    hist_atr=(tr.rolling(14).mean()/close*100).dropna().tail(120)
    vol_rank=float((hist_atr<=atr_pct).mean()*100) if len(hist_atr) else 50.0
    spread=float((ema_fast.iloc[-1]/ema_slow.iloc[-1]-1)*100) if ema_slow.iloc[-1] else 0.0
    if spread>0.25: trend="Bullish"
    elif spread < -0.25: trend="Bearish"
    else: trend="Neutral"
    if er>=0.40 and trend!="Neutral": regime="Trending"
    elif er<0.20: regime="Range-bound"
    else: regime="Transitioning"
    volatility="High" if vol_rank>=80 else "Low" if vol_rank<=20 else "Normal"
    score=float(np.clip(spread*18,-50,50) + np.clip((er-0.25)*40,-10,20))
    return {"status":"OK","regime":regime,"trend":trend,"volatility":volatility,"trend_score":round(score,2),"atr_pct":round(atr_pct,3),"efficiency_ratio":round(er,3),"volatility_percentile":round(vol_rank,1),"ema_spread_pct":round(spread,3)}

def index_confluence(index_frames: dict[str,pd.DataFrame]) -> dict:
    results={}
    for name,frame in index_frames.items():
        if frame is None or frame.empty: continue
        results[name]=regime_intelligence(frame)
    valid={k:v for k,v in results.items() if v.get("status")=="OK"}
    if not valid: return {"status":"Insufficient index data","bias":"Unknown","score":0,"agreement":0,"components":results}
    scores=[v["trend_score"] for v in valid.values()]
    score=float(np.mean(scores)); signs=[1 if v["trend"]=="Bullish" else -1 if v["trend"]=="Bearish" else 0 for v in valid.values()]
    agreement=abs(sum(signs))/len(signs)
    bias="Bullish" if score>8 else "Bearish" if score < -8 else "Mixed / neutral"
    if len(signs)>=2 and len(set(signs))>1: bias="Mixed / divergent"
    return {"status":"OK","bias":bias,"score":round(score,2),"agreement":round(agreement*100,1),"components":results}

def rank_intraday_opportunities(frames: dict[str,pd.DataFrame]) -> pd.DataFrame:
    rows=[]
    for symbol,frame in frames.items():
        if frame is None or frame.empty: continue
        r=regime_intelligence(frame)
        if r["status"]!="OK": continue
        x=_clean(frame); avg=x.Volume.shift(1).rolling(20).mean().iloc[-1]
        rv=float(x.Volume.iloc[-1]/avg) if pd.notna(avg) and avg>0 else 0.0
        direction=1 if r["trend"]=="Bullish" else -1 if r["trend"]=="Bearish" else 0
        volume_points=min(max(rv-1,0)*12,20)
        score=float(np.clip(abs(r["trend_score"])*0.8+volume_points+(10 if r["regime"]=="Trending" else 0),0,100))
        rows.append({"Symbol":symbol,"Bias":r["trend"],"Regime":r["regime"],"Relative Volume":round(rv,2),"ATR %":r["atr_pct"],"Score":round(score,1),"Volatility":r["volatility"]})
    return pd.DataFrame(rows).sort_values("Score",ascending=False).reset_index(drop=True) if rows else pd.DataFrame(columns=["Symbol","Bias","Regime","Relative Volume","ATR %","Score","Volatility"])

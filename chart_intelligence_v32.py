"""V32 OHLCV chart-pattern and entry-zone research. Deterministic, non-predictive heuristics."""
from __future__ import annotations
import numpy as np
import pandas as pd

REQUIRED = {"Open", "High", "Low", "Close", "Volume"}

def analyze_chart_v32(frame: pd.DataFrame, lookback: int = 20) -> dict:
    if not isinstance(frame, pd.DataFrame) or not REQUIRED.issubset(frame.columns):
        raise ValueError("Chart analysis requires Open, High, Low, Close and Volume columns")
    x=frame.copy().sort_index()
    for col in REQUIRED: x[col]=pd.to_numeric(x[col], errors="coerce")
    x=x.dropna(subset=["Open","High","Low","Close"])
    if len(x)<30: return {"status":"Insufficient history", "patterns":[], "setups":[], "support":None,"resistance":None,"entry":None,"stop":None,"target":None,"warnings":["At least 30 valid candles are required."]}
    o,h,l,c,v=(x[k] for k in ["Open","High","Low","Close","Volume"])
    last=float(c.iloc[-1]); prev_high=float(h.shift(1).rolling(lookback).max().iloc[-1]); prev_low=float(l.shift(1).rolling(lookback).min().iloc[-1])
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    atr=float(tr.ewm(alpha=1/14,adjust=False).mean().iloc[-1])
    vol_avg=float(v.shift(1).rolling(20).mean().iloc[-1]) if v.notna().sum()>=21 else np.nan
    vol_ratio=float(v.iloc[-1]/vol_avg) if pd.notna(vol_avg) and vol_avg>0 and pd.notna(v.iloc[-1]) else np.nan
    body=abs(float(c.iloc[-1]-o.iloc[-1])); rng=max(float(h.iloc[-1]-l.iloc[-1]),1e-12)
    upper=float(h.iloc[-1]-max(o.iloc[-1],c.iloc[-1])); lower=float(min(o.iloc[-1],c.iloc[-1])-l.iloc[-1])
    patterns=[]
    if body/rng<=.10: patterns.append("Doji")
    if lower>=body*2 and upper<=body*.5 and body/rng<=.35: patterns.append("Hammer-like candle")
    if upper>=body*2 and lower<=body*.5 and body/rng<=.35: patterns.append("Shooting-star-like candle")
    if len(x)>=2:
        po,pc=float(o.iloc[-2]),float(c.iloc[-2]); co,cc=float(o.iloc[-1]),float(c.iloc[-1])
        if pc<po and cc>co and co<=pc and cc>=po: patterns.append("Bullish engulfing")
        if pc>po and cc<co and co>=pc and cc<=po: patterns.append("Bearish engulfing")
        if float(h.iloc[-1])<float(h.iloc[-2]) and float(l.iloc[-1])>float(l.iloc[-2]): patterns.append("Inside bar")
    setups=[]; direction="Wait / no confirmed setup"; entry=stop=target=None; status="Inside prior range"
    if last>prev_high:
        status="Confirmed close above prior range"; direction="Bullish breakout candidate"; setups.append("20-candle range breakout")
        entry=(prev_high, prev_high+max(atr*.15,0)); stop=prev_high-atr; target=last+2*atr
    elif last<prev_low:
        status="Confirmed close below prior range"; direction="Bearish breakdown candidate"; setups.append("20-candle range breakdown")
        entry=(prev_low-max(atr*.15,0),prev_low); stop=prev_low+atr; target=last-2*atr
    elif last>=prev_high-0.30*atr:
        status="Near range resistance"; direction="Watch for upside confirmation"; setups.append("Potential resistance breakout; close confirmation required")
        entry=(prev_high,prev_high+0.15*atr); stop=prev_high-atr; target=prev_high+2*atr
    elif last<=prev_low+0.30*atr:
        status="Near range support"; direction="Watch for downside confirmation"; setups.append("Potential support breakdown; close confirmation required")
        entry=(prev_low-0.15*atr,prev_low); stop=prev_low+atr; target=prev_low-2*atr
    else: setups.append("No range breakout; price remains within prior range")
    if patterns: setups.extend(patterns)
    if pd.notna(vol_ratio) and vol_ratio>=1.5: setups.append("Elevated volume (>=1.5x prior 20-candle average)")
    elif pd.notna(vol_ratio) and vol_ratio<0.8: setups.append("Below-average volume; breakout participation is weak")
    # Rolling levels are references, not guaranteed support/resistance.
    support=float(l.tail(lookback).min()); resistance=float(h.tail(lookback).max())
    warnings=["Pattern labels are OHLCV heuristics and require visual/context confirmation.","Entry zones and ATR levels are illustrative research references, not orders or recommendations.","A candle-close breakout can fail; account for spreads, slippage, gaps and data delay."]
    if not np.isfinite(vol_ratio): warnings.append("Volume comparison unavailable for this dataset.")
    return {"status":status,"direction":direction,"last":last,"atr":atr,"volume_ratio":vol_ratio,"prior_high":prev_high,"prior_low":prev_low,"support":support,"resistance":resistance,"patterns":patterns,"setups":setups,"entry":entry,"stop":stop,"target":target,"warnings":warnings,"candles":len(x)}

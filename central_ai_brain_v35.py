"""V35 Central AI Brain: transparent, rule-based analysis across 25 specialist tools.
No broker execution, no invented quotes, and no predictive guarantees.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

TOOL_CATALOG = [
 (1,"AI Market Scanner","Ranks supplied symbols by trend, momentum and volume."),
 (2,"AI Technical Analyst","EMA, RSI, MACD and ATR diagnostics."),
 (3,"AI Chart Pattern Recognition","Detects common candle patterns from OHLCV."),
 (4,"AI Support & Resistance","Rolling support/resistance reference levels."),
 (5,"AI Breakout Detector","Checks close against prior rolling range."),
 (6,"AI Multi-Timeframe Analyst","Compares supplied timeframe summaries."),
 (7,"AI Market Sentiment","Combines observable momentum and optional manual sentiment input."),
 (8,"AI Option Chain Analyst","Summarises supplied CE/PE open interest and PCR."),
 (9,"AI Max Pain & OI Analyst","Uses the existing option-chain Max Pain engine when chain data is supplied."),
 (10,"AI Options Strategy Builder","Uses V29 listed-strike strategy generator."),
 (11,"AI Greeks Analyst","Explains supplied option Greeks; requires valid chain Greeks."),
 (12,"AI Expiry Risk Analyst","Highlights expiry proximity and IV/event risk when supplied."),
 (13,"AI Trade Confirmation","Combines available technical, options and news evidence."),
 (14,"AI Smart Entry & Exit","ATR-based illustrative levels, not orders."),
 (15,"AI Risk Management","Position sizing and risk/reward calculations."),
 (16,"AI Setup Quality Model","Evidence score; not a calibrated win probability."),
 (17,"AI Trade Journal","Uses existing journal/portfolio ledger for review."),
 (18,"AI Global News Analyst","Uses available multi-source news feed; source availability varies."),
 (19,"AI Economic Calendar","Uses available Forex Factory calendar and manual event context."),
 (20,"AI FII/DII Analyst","Requires verified institutional flow data or manual input."),
 (21,"AI Sector Rotation","Uses existing sector breadth/rotation data where available."),
 (22,"AI Correlation Analyst","Correlation matrix from aligned asset price histories."),
 (23,"AI Portfolio Manager","Uses V34 local positions and watchlists."),
 (24,"AI Backtesting Engine","Uses existing historical backtesting module."),
 (25,"AI Trading Copilot","Explains evidence from the integrated tools; not an autonomous model."),
]

def _series(df, col):
    if col not in df: raise ValueError(f"Missing required column: {col}")
    return pd.to_numeric(df[col], errors="coerce")

def analyze_market(df: pd.DataFrame, *, option_pcr=None, fii_net=None, news_score=None, timeframes=None):
    """Return explainable evidence from OHLCV and optional externally verified inputs."""
    if df is None or df.empty or len(df) < 30:
        return {"status":"INSUFFICIENT_DATA","warnings":["At least 30 OHLCV candles are required."],"tool_count":25}
    x=df.copy()
    close=_series(x,"Close"); high=_series(x,"High"); low=_series(x,"Low"); volume=_series(x,"Volume")
    ema20=close.ewm(span=20,adjust=False).mean(); ema50=close.ewm(span=50,adjust=False).mean()
    delta=close.diff(); gain=delta.clip(lower=0).ewm(alpha=1/14,adjust=False).mean(); loss=(-delta.clip(upper=0)).ewm(alpha=1/14,adjust=False).mean()
    rsi=100-100/(1+gain/loss.replace(0,np.nan))
    macd=close.ewm(span=12,adjust=False).mean()-close.ewm(span=26,adjust=False).mean()
    macd_signal=macd.ewm(span=9,adjust=False).mean()
    tr=pd.concat([high-low,(high-close.shift()).abs(),(low-close.shift()).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/14,adjust=False).mean()
    latest=float(close.iloc[-1]); prev=float(close.iloc[-2]); a=float(atr.iloc[-1])
    avgvol=float(volume.rolling(20).mean().iloc[-1]) if volume.notna().sum()>=20 else np.nan
    relvol=float(volume.iloc[-1]/avgvol) if avgvol and np.isfinite(avgvol) and avgvol>0 else None
    prior_high=float(high.iloc[-21:-1].max()); prior_low=float(low.iloc[-21:-1].min())
    support=float(low.tail(20).min()); resistance=float(high.tail(20).max())
    score=0; evidence=[]; warnings=[]
    if latest>float(ema20.iloc[-1])>float(ema50.iloc[-1]): score+=2; evidence.append("Close > EMA20 > EMA50")
    elif latest<float(ema20.iloc[-1])<float(ema50.iloc[-1]): score-=2; evidence.append("Close < EMA20 < EMA50")
    else: warnings.append("EMA trend is mixed.")
    rv=float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else None
    if rv is not None:
        if rv>=55: score+=1; evidence.append(f"RSI bullish momentum ({rv:.1f})")
        elif rv<=45: score-=1; evidence.append(f"RSI bearish momentum ({rv:.1f})")
        else: warnings.append(f"RSI is neutral ({rv:.1f}).")
    if macd.iloc[-1]>macd_signal.iloc[-1]: score+=1; evidence.append("MACD above signal")
    else: score-=1; evidence.append("MACD below signal")
    breakout="NONE"
    if latest>prior_high: score+=2; breakout="UPSIDE_BREAKOUT"; evidence.append("Close broke above previous 20-candle high")
    elif latest<prior_low: score-=2; breakout="DOWNSIDE_BREAKDOWN"; evidence.append("Close broke below previous 20-candle low")
    if relvol is not None and relvol>=1.5: evidence.append(f"Volume expansion: {relvol:.2f}x 20-candle average")
    else: warnings.append("No strong relative-volume confirmation.")
    if option_pcr is not None:
        try:
            pcr=float(option_pcr)
            if pcr>=1.2: score+=1; evidence.append(f"Supplied PCR supports bullish positioning ({pcr:.2f})")
            elif pcr<=0.8: score-=1; evidence.append(f"Supplied PCR supports bearish positioning ({pcr:.2f})")
            else: warnings.append("Supplied PCR is in a neutral range.")
        except (TypeError,ValueError): warnings.append("PCR input was invalid and ignored.")
    else: warnings.append("Options positioning not supplied; PCR/OI tools are waiting for option-chain data.")
    if fii_net is not None:
        try:
            f=float(fii_net); score += 1 if f>0 else (-1 if f<0 else 0); evidence.append(f"Manual FII/DII net-flow input: {f:,.2f}")
        except (TypeError,ValueError): warnings.append("Institutional flow input invalid; ignored.")
    else: warnings.append("Verified FII/DII flow not supplied; institutional-flow tool is not scored.")
    if news_score is not None:
        try:
            ns=max(-2,min(2,int(news_score))); score+=ns; evidence.append(f"Manual/news-engine sentiment contribution: {ns:+d}")
        except (TypeError,ValueError): warnings.append("News score invalid; ignored.")
    else: warnings.append("News context not supplied; news tools are not scored.")
    direction="BULLISH_CANDIDATE" if score>=3 else "BEARISH_CANDIDATE" if score<=-3 else "WAIT / MIXED"
    quality="STRONGER_EVIDENCE" if abs(score)>=5 else "MODERATE_EVIDENCE" if abs(score)>=3 else "WEAK_OR_MIXED_EVIDENCE"
    entry_low=latest-0.25*a; entry_high=latest+0.25*a
    return {"status":"OK","symbol":"","last_close":latest,"change_pct":(latest/prev-1)*100 if prev else None,
      "ema20":float(ema20.iloc[-1]),"ema50":float(ema50.iloc[-1]),"rsi":rv,"macd":float(macd.iloc[-1]),
      "macd_signal":float(macd_signal.iloc[-1]),"atr":a,"relative_volume":relvol,"support":support,"resistance":resistance,
      "prior_20_high":prior_high,"prior_20_low":prior_low,"breakout":breakout,"score":score,"direction":direction,"quality":quality,
      "entry_reference":[entry_low,entry_high],"stop_long":latest-1.5*a,"target_long":latest+2*a,
      "stop_short":latest+1.5*a,"target_short":latest-2*a,"evidence":evidence,"warnings":warnings,
      "tool_count":25,"timeframes_supplied":list((timeframes or {}).keys())}

def rank_symbols(frames: dict[str,pd.DataFrame]):
    rows=[]
    for symbol, frame in (frames or {}).items():
        result=analyze_market(frame)
        rows.append({"Symbol":symbol,"Status":result["status"],"Bias":result.get("direction","N/A"),"Score":result.get("score"),
                     "RSI":result.get("rsi"),"Relative Volume":result.get("relative_volume"),"Breakout":result.get("breakout")})
    return pd.DataFrame(rows).sort_values("Score",ascending=False,na_position="last") if rows else pd.DataFrame()

def correlation_matrix(price_history: dict[str,pd.Series], min_periods=20):
    if not price_history: return pd.DataFrame()
    prices=pd.DataFrame(price_history).apply(pd.to_numeric,errors="coerce")
    returns=prices.pct_change().dropna(how="all")
    return returns.corr(min_periods=min_periods)

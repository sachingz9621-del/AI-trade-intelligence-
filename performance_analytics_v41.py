"""V41 performance analytics and transparent strategy-plan helpers."""
from __future__ import annotations
import numpy as np
import pandas as pd


def summarize_closed_positions(positions: pd.DataFrame) -> dict:
    x = positions.copy() if isinstance(positions, pd.DataFrame) else pd.DataFrame()
    if x.empty or 'status' not in x:
        x = pd.DataFrame()
    else:
        x = x[x.status.astype(str).str.upper() == 'CLOSED'].copy()
    if x.empty:
        return {'closed_trades': 0, 'wins': 0, 'losses': 0, 'win_rate_pct': None,
                'net_pnl': 0.0, 'gross_pnl': 0.0, 'fees': 0.0,
                'profit_factor': None, 'avg_win': None, 'avg_loss': None,
                'best_trade': None, 'worst_trade': None}
    pnl = pd.to_numeric(x.get('net_pnl', 0), errors='coerce').fillna(0.0)
    wins, losses = pnl[pnl > 0], pnl[pnl < 0]
    gross_profit, gross_loss = float(wins.sum()), float(-losses.sum())
    fees = pd.to_numeric(x.get('entry_fees', 0), errors='coerce').fillna(0).sum() + pd.to_numeric(x.get('exit_fees', 0), errors='coerce').fillna(0).sum()
    return {'closed_trades': int(len(x)), 'wins': int((pnl > 0).sum()), 'losses': int((pnl < 0).sum()),
            'win_rate_pct': float((pnl > 0).mean() * 100), 'net_pnl': float(pnl.sum()),
            'gross_pnl': float(pd.to_numeric(x.get('gross_pnl', 0), errors='coerce').fillna(0).sum()),
            'fees': float(fees), 'profit_factor': gross_profit / gross_loss if gross_loss else (float('inf') if gross_profit else None),
            'avg_win': float(wins.mean()) if len(wins) else None, 'avg_loss': float(losses.mean()) if len(losses) else None,
            'best_trade': float(pnl.max()), 'worst_trade': float(pnl.min())}


def daily_pnl(positions: pd.DataFrame) -> pd.DataFrame:
    x = positions.copy() if isinstance(positions, pd.DataFrame) else pd.DataFrame()
    if x.empty or 'closed_at' not in x or 'net_pnl' not in x:
        return pd.DataFrame(columns=['Date', 'Net P&L', 'Cumulative P&L'])
    x = x[x.status.astype(str).str.upper() == 'CLOSED'].copy()
    if x.empty:
        return pd.DataFrame(columns=['Date', 'Net P&L', 'Cumulative P&L'])
    x['Date'] = pd.to_datetime(x['closed_at'], errors='coerce').dt.date
    x['Net P&L'] = pd.to_numeric(x['net_pnl'], errors='coerce').fillna(0)
    out = x.dropna(subset=['Date']).groupby('Date', as_index=False)['Net P&L'].sum().sort_values('Date')
    out['Cumulative P&L'] = out['Net P&L'].cumsum()
    return out


def strategy_advice(frame: pd.DataFrame, mode: str = 'Intraday') -> dict:
    """Rule-based educational setup; requires OHLCV candles and never invents option contracts."""
    mode = str(mode).title()
    if not isinstance(frame, pd.DataFrame) or not {'High','Low','Close'}.issubset(frame.columns) or len(frame) < 30:
        return {'mode': mode, 'status': 'INSUFFICIENT_DATA', 'bias': 'WAIT',
                'summary': 'At least 30 clean OHLC candles are required. No trade levels are generated.',
                'evidence': [], 'warnings': ['Load a supported symbol and sufficient candle history.']}
    x = frame.copy().sort_index()
    close = pd.to_numeric(x.Close, errors='coerce'); high = pd.to_numeric(x.High, errors='coerce'); low = pd.to_numeric(x.Low, errors='coerce')
    tr = pd.concat([high-low, (high-close.shift()).abs(), (low-close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean()
    ema9 = close.ewm(span=9, adjust=False).mean(); ema20 = close.ewm(span=20, adjust=False).mean(); ema50 = close.ewm(span=50, adjust=False).mean()
    delta=close.diff(); gain=delta.clip(lower=0).ewm(alpha=1/14,adjust=False).mean(); loss=(-delta.clip(upper=0)).ewm(alpha=1/14,adjust=False).mean()
    rsi=100-100/(1+gain/loss.replace(0,np.nan))
    macd=close.ewm(span=12,adjust=False).mean()-close.ewm(span=26,adjust=False).mean(); sig=macd.ewm(span=9,adjust=False).mean()
    last=float(close.iloc[-1]); a=float(atr.iloc[-1]); rv=float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else 50.0
    score=0; evidence=[]; warnings=[]
    if last > float(ema20.iloc[-1]) > float(ema50.iloc[-1]): score+=2; evidence.append('Price > EMA20 > EMA50: bullish trend alignment')
    elif last < float(ema20.iloc[-1]) < float(ema50.iloc[-1]): score-=2; evidence.append('Price < EMA20 < EMA50: bearish trend alignment')
    else: warnings.append('EMA trend is mixed; avoid forcing a directional trade.')
    if rv >= 55: score+=1; evidence.append(f'RSI {rv:.1f}: positive momentum')
    elif rv <= 45: score-=1; evidence.append(f'RSI {rv:.1f}: negative momentum')
    else: warnings.append(f'RSI {rv:.1f}: neutral momentum')
    if float(macd.iloc[-1]) > float(sig.iloc[-1]): score+=1; evidence.append('MACD above signal')
    else: score-=1; evidence.append('MACD below signal')
    bias='LONG' if score>=3 else 'SHORT' if score<=-3 else 'WAIT'
    if a <= 0 or not np.isfinite(a):
        return {'mode':mode,'status':'INVALID_VOLATILITY','bias':'WAIT','summary':'ATR is unavailable; no levels generated.','evidence':evidence,'warnings':warnings}
    if mode == 'Scalping': stop_mult, target_mult, horizon = 0.8, 1.6, '1–5 minute setup; confirm on an actual 1m/5m feed'
    elif mode == 'Intraday': stop_mult, target_mult, horizon = 1.2, 2.0, 'Intraday; review before session close'
    else: stop_mult, target_mult, horizon = 1.0, 1.5, 'Hedge overlay; size from portfolio exposure and option-chain liquidity'
    if bias == 'LONG': entry=(last-0.15*a,last+0.10*a); stop=last-stop_mult*a; target=last+target_mult*a
    elif bias == 'SHORT': entry=(last-0.10*a,last+0.15*a); stop=last+stop_mult*a; target=last-target_mult*a
    else: entry=None; stop=None; target=None
    rr=abs(target-last)/abs(last-stop) if bias!='WAIT' and stop!=last else None
    summary = (f'{bias} candidate from rule-based candle evidence. Levels are ATR reference levels, not guaranteed fills.' if bias!='WAIT'
               else 'WAIT: evidence is mixed. No entry, stop or target is recommended.')
    if mode=='Hedging':
        warnings.append('No verified option chain, expiry, Greeks, bid/ask or portfolio exposure was supplied. No strike, premium or hedge ratio is fabricated.')
        summary += ' Use a defined-risk hedge only after checking live option liquidity, Greeks, expiry and total portfolio delta.'
    return {'mode':mode,'status':'OK','bias':bias,'score':score,'last_price':last,'rsi':rv,'atr':a,
            'entry_zone':entry,'stop':stop,'target':target,'risk_reward':rr,'horizon':horizon,
            'summary':summary,'evidence':evidence,'warnings':warnings}

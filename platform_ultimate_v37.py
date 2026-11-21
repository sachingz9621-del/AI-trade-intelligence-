"""V37 platform integration utilities: additive SQLite paper ledger, risk and validation.

No broker order routes are implemented. All prices must be supplied by a caller and
must carry their own source/freshness metadata in the UI.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Iterable
import pandas as pd

DB_PATH = Path(__file__).with_name('ati_v37_workspace.sqlite3')

# The 25 specialist tools and 15 platform capabilities are catalogued separately
# from implementation maturity; a directory entry is not a claim of full automation.
SPECIALIST_TOOLS = [
('AI Market Scanner','Scan supported equities, indices, commodities, FX and crypto.'),
('AI Technical Analyst','EMA, RSI, MACD, VWAP, ATR and volume context.'),
('AI Chart Pattern Recognition','Rule-based candle and chart-pattern checks.'),
('AI Support & Resistance','Rolling and swing-based price levels.'),
('AI Breakout Detector','Range break and breakdown conditions.'),
('AI Multi-Timeframe Analyst','Compare available timeframe trends.'),
('AI Market Sentiment','Combine available sentiment evidence with source labels.'),
('AI Option Chain Analyst','CE/PE OI, volume, IV and PCR when chain data exists.'),
('AI Max Pain & OI Analyst','Descriptive OI concentration and expiry payout curve.'),
('AI Options Strategy Builder','Defined option structures from available listed contracts.'),
('AI Greeks Analyst','Interpret supplied option Greeks.'),
('AI Expiry Predictor','Expiry positioning scenarios; not a price prediction.'),
('AI Trade Confirmation','Confluence and conflict assessment.'),
('AI Smart Entry & Exit','Illustrative entry, stop and target zones.'),
('AI Risk Management','Position sizing, exposure and stop-risk estimates.'),
('AI Trade Probability Model','Requires calibrated historical dataset; no unvalidated probability claims.'),
('AI Trade Journal','Trade records and post-trade review.'),
('AI Global News Analyst','News summaries and impact classification when sourced.'),
('AI Economic Calendar','Event schedule and event-risk flags when connected.'),
('AI FII/DII Analyst','Institutional flow analysis only from verified published data.'),
('AI Sector Rotation','Relative sector strength from available price histories.'),
('AI Correlation Analyst','Correlation from aligned historical returns.'),
('AI Portfolio Manager','Portfolio exposure, P&L and risk monitoring.'),
('AI Backtesting Engine','Historical rule testing with explicit assumptions.'),
('AI Trading Copilot','Conversational explanations grounded in loaded platform data.'),
]
PLATFORM_CAPABILITIES = [
('Central AI Brain','Shared evidence and decision orchestration.'),
('Live Data Infrastructure','Broker feed adapters, freshness and source diagnostics.'),
('Autonomous Market Monitoring','Session-running monitor; requires host process to remain active.'),
('Smart Alert Centre','Persistent alert rules and deduplicated trigger records.'),
('Paper Trading Simulator','Local simulated trade ledger; no real orders.'),
('Broker API Integration','Read-only feed supported; order API requires separate approval and safeguards.'),
('Advanced Order Management','Order lifecycle design; real order submission disabled.'),
('Strategy Backtesting Lab','Chronological historical strategy simulation.'),
('Walk-Forward Testing','Chronological train/test windows to reduce look-ahead bias.'),
('Performance Analytics','Win rate, expectancy, profit factor and drawdown.'),
('Portfolio Risk Engine','Risk budget, stop distance and aggregate exposure checks.'),
('AI Trade Journal & Review','Persistent paper-trade outcomes and notes.'),
('Multi-User Login & Security','Single-user local deployment; production multi-user auth not enabled.'),
('Mobile-Optimised Trading Terminal','Responsive Streamlit layout; mobile usability should be verified on device.'),
('Institutional Intelligence Dashboard','Unified view; institutional flow claims require verified source feeds.'),
]

def _connect(db_path=None):
    p=Path(db_path) if db_path else DB_PATH
    p.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(p); c.row_factory=sqlite3.Row
    return c

def init_db(db_path=None):
    with _connect(db_path) as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS paper_trades(
          id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL,
          side TEXT NOT NULL CHECK(side IN ('LONG','SHORT')),
          quantity REAL NOT NULL CHECK(quantity>0), entry REAL NOT NULL CHECK(entry>0),
          stop REAL, target REAL, status TEXT NOT NULL DEFAULT 'OPEN' CHECK(status IN ('OPEN','CLOSED')),
          exit_price REAL, notes TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, closed_at TEXT);
        CREATE TABLE IF NOT EXISTS v37_events(
          id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL,
          payload TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        ''')

def risk_position_size(capital: float, risk_pct: float, entry: float, stop: float, lot_size: int=1):
    capital,risk_pct,entry,stop=float(capital),float(risk_pct),float(entry),float(stop)
    if capital<=0 or not 0<risk_pct<=5 or entry<=0 or stop<=0 or lot_size<1:
        raise ValueError('Capital/entry/stop must be positive, risk must be >0 and <=5%, lot size >=1.')
    distance=abs(entry-stop)
    if distance==0: raise ValueError('Entry and stop must differ.')
    risk_budget=capital*risk_pct/100
    raw=int(risk_budget//distance)
    qty=(raw//int(lot_size))*int(lot_size)
    return {'risk_budget':risk_budget,'risk_per_unit':distance,'quantity':qty,
            'estimated_stop_risk':qty*distance,'notional':qty*entry,
            'warning':'Illustrative sizing only; gaps, slippage, fees, taxes and margin are excluded.'}

def add_paper_trade(symbol,side,quantity,entry,stop=None,target=None,notes='',db_path=None):
    symbol=str(symbol).strip().upper(); side=str(side).upper(); quantity=float(quantity); entry=float(entry)
    if not symbol or side not in ('LONG','SHORT') or quantity<=0 or entry<=0: raise ValueError('Invalid paper trade inputs.')
    init_db(db_path)
    with _connect(db_path) as c:
        cur=c.execute('INSERT INTO paper_trades(symbol,side,quantity,entry,stop,target,notes) VALUES(?,?,?,?,?,?,?)',
                      (symbol,side,quantity,entry,stop,target,str(notes)))
        return cur.lastrowid

def list_paper_trades(db_path=None):
    init_db(db_path)
    with _connect(db_path) as c: return pd.read_sql_query('SELECT * FROM paper_trades ORDER BY id DESC',c)

def close_paper_trade(trade_id,exit_price,db_path=None):
    exit_price=float(exit_price)
    if exit_price<=0: raise ValueError('Exit price must be positive.')
    init_db(db_path)
    with _connect(db_path) as c:
        cur=c.execute("UPDATE paper_trades SET status='CLOSED',exit_price=?,closed_at=CURRENT_TIMESTAMP WHERE id=? AND status='OPEN'",(exit_price,int(trade_id)))
        return cur.rowcount==1

def paper_trade_metrics(trades: pd.DataFrame):
    if trades is None or trades.empty: return {'trades':0,'closed':0,'win_rate_pct':None,'net_pnl':0.0,'profit_factor':None,'max_drawdown':0.0}
    x=trades[trades.status=='CLOSED'].copy()
    if x.empty: return {'trades':len(trades),'closed':0,'win_rate_pct':None,'net_pnl':0.0,'profit_factor':None,'max_drawdown':0.0}
    mult=x.side.map({'LONG':1.0,'SHORT':-1.0})
    pnl=(x.exit_price-x.entry)*x.quantity*mult
    wins=float(pnl[pnl>0].sum()); losses=float(-pnl[pnl<0].sum())
    equity=pnl.cumsum(); dd=equity-equity.cummax()
    return {'trades':len(trades),'closed':len(x),'win_rate_pct':float((pnl>0).mean()*100),
            'net_pnl':float(pnl.sum()),'profit_factor':(wins/losses if losses>0 else (float('inf') if wins>0 else None)),
            'max_drawdown':float(abs(dd.min()))}

def walk_forward_ema_test(close: pd.Series, fast:int=10, slow:int=30, train_fraction:float=.6):
    """Simple long/flat EMA crossover, chronologically split; returns test-only stats."""
    s=pd.to_numeric(close,errors='coerce').dropna()
    if fast<2 or slow<=fast or len(s)<max(slow*3,40) or not .5<=train_fraction<=.85:
        raise ValueError('Need sufficient clean closes, fast < slow, and train fraction 0.50–0.85.')
    split=int(len(s)*train_fraction)
    # Indicators are causal; performance is evaluated only after the chronological split.
    f=s.ewm(span=fast,adjust=False).mean(); sl=s.ewm(span=slow,adjust=False).mean()
    signal=(f>sl).astype(float).shift(1).fillna(0)
    returns=s.pct_change().fillna(0)
    test=signal.iloc[split:]*returns.iloc[split:]
    equity=(1+test).cumprod()
    peak=equity.cummax(); drawdown=equity/peak-1
    total=float(equity.iloc[-1]-1) if len(equity) else 0.0
    vol=float(test.std())
    return {'train_rows':split,'test_rows':len(test),'test_return_pct':total*100,
            'test_max_drawdown_pct':float(drawdown.min()*100),
            'test_sharpe_approx':float((test.mean()/vol)*(252**.5)) if vol>0 else None,
            'assumptions':'Long/flat EMA crossover; close-to-close returns; no fees, slippage, taxes, latency or market impact.'}

def catalog():
    return {'specialist_tools':[{'name':n,'purpose':p} for n,p in SPECIALIST_TOOLS],
            'platform_capabilities':[{'name':n,'purpose':p} for n,p in PLATFORM_CAPABILITIES]}

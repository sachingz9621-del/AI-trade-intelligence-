"""Market breadth and sector-strength helpers for the V9 dashboard.
Data is sourced from Yahoo Finance and may be delayed; this is not exchange-grade feed."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd

DB_PATH = Path(__file__).with_name("ati_v9_data.sqlite3")

SECTOR_SYMBOLS = {
    "NIFTY Bank": "^NSEBANK", "NIFTY IT": "^CNXIT", "NIFTY Auto": "^CNXAUTO",
    "NIFTY FMCG": "^CNXFMCG", "NIFTY Pharma": "^CNXPHARMA", "NIFTY Metal": "^CNXMETAL",
    "NIFTY Realty": "^CNXREALTY", "NIFTY Energy": "^CNXENERGY", "NIFTY PSU Bank": "^CNXPSUBANK",
}
BREADTH_SYMBOLS = {
    "RELIANCE": "RELIANCE.NS", "HDFC Bank": "HDFCBANK.NS", "ICICI Bank": "ICICIBANK.NS",
    "Bharti Airtel": "BHARTIARTL.NS", "TCS": "TCS.NS", "Infosys": "INFY.NS",
    "Larsen & Toubro": "LT.NS", "ITC": "ITC.NS", "SBI": "SBIN.NS", "Axis Bank": "AXISBANK.NS",
    "Kotak Bank": "KOTAKBANK.NS", "HUL": "HINDUNILVR.NS", "Maruti": "MARUTI.NS",
    "Sun Pharma": "SUNPHARMA.NS", "Tata Motors": "TMPV.NS", "ONGC": "ONGC.NS",
}

def _connect():
    con = sqlite3.connect(DB_PATH)
    con.execute("CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY, symbol TEXT NOT NULL, condition TEXT NOT NULL, target REAL NOT NULL, active INTEGER NOT NULL DEFAULT 1, created TEXT NOT NULL, triggered TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY, date TEXT, symbol TEXT, side TEXT, quantity INTEGER, entry REAL, exit REAL, charges REAL, gross REAL, net REAL, notes TEXT)")
    con.commit()
    return con

def fetch_change(symbols: dict[str, str], period="1mo") -> pd.DataFrame:
    import yfinance as yf
    rows=[]
    for name, ticker in symbols.items():
        try:
            d=yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False, threads=False)
            if d is None or d.empty: continue
            close=d["Close"]
            if isinstance(close, pd.DataFrame): close=close.iloc[:,0]
            close=close.dropna()
            if len(close)<2: continue
            last=float(close.iloc[-1]); prev=float(close.iloc[-2])
            week=float(close.iloc[-6]) if len(close)>=6 else float(close.iloc[0])
            rows.append({"Name":name,"Symbol":ticker,"Last":last,"Day %":(last/prev-1)*100,"5D %":(last/week-1)*100})
        except Exception:
            continue
    return pd.DataFrame(rows)

def add_alert(symbol, condition, target):
    with _connect() as con:
        con.execute("INSERT INTO alerts(symbol,condition,target,active,created) VALUES(?,?,?,?,?)",(symbol.upper(),condition,float(target),1,datetime.now().isoformat(timespec="seconds")))

def list_alerts():
    with _connect() as con:
        return pd.read_sql_query("SELECT * FROM alerts ORDER BY id DESC",con)

def remove_alert(alert_id):
    with _connect() as con:
        con.execute("UPDATE alerts SET active=0 WHERE id=?",(int(alert_id),))

def check_alerts():
    import yfinance as yf
    alerts=list_alerts(); fired=[]
    if alerts.empty: return fired
    for sym in alerts.loc[alerts.active==1,"symbol"].unique():
        try:
            d=yf.download(sym,period="5d",interval="1d",auto_adjust=True,progress=False,threads=False)
            if d.empty: continue
            close=d["Close"]
            price=float(close.iloc[-1] if getattr(close,"ndim",1)==1 else close.iloc[-1,0])
            for a in alerts[(alerts.symbol==sym)&(alerts.active==1)].itertuples():
                hit=(a.condition=="Above" and price>=a.target) or (a.condition=="Below" and price<=a.target)
                if hit:
                    with _connect() as con:
                        con.execute("UPDATE alerts SET active=0,triggered=? WHERE id=?",(datetime.now().isoformat(timespec="seconds"),a.id))
                    fired.append({"Symbol":sym,"Condition":a.condition,"Target":a.target,"Price":price})
        except Exception: pass
    return fired

def save_trade(row):
    with _connect() as con:
        con.execute("INSERT INTO trades(date,symbol,side,quantity,entry,exit,charges,gross,net,notes) VALUES(?,?,?,?,?,?,?,?,?,?)",tuple(row[k] for k in ["Date","Symbol","Side","Quantity","Entry","Exit","Charges","Gross P&L","Net P&L","Notes"]))

def load_trades():
    with _connect() as con:
        return pd.read_sql_query("SELECT date AS 'Date',symbol AS 'Symbol',side AS 'Side',quantity AS 'Quantity',entry AS 'Entry',exit AS 'Exit',charges AS 'Charges',gross AS 'Gross P&L',net AS 'Net P&L',notes AS 'Notes' FROM trades ORDER BY id DESC",con)

def clear_trades():
    with _connect() as con: con.execute("DELETE FROM trades")

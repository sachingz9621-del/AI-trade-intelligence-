"""V38 terminal workspace: persistent local watchlist and price-alert rules.

Quotes are supplied by the host app's selected data adapter; this module does not
claim exchange-grade streaming or background alert delivery.
"""
from pathlib import Path
import sqlite3
import pandas as pd

DB_PATH = Path(__file__).with_name('ati_v38_terminal.sqlite3')

def _connect(db_path=None):
    p=Path(db_path) if db_path else DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    c=sqlite3.connect(p); c.row_factory=sqlite3.Row
    return c

def init_db(db_path=None):
    with _connect(db_path) as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS watchlist(
          symbol TEXT PRIMARY KEY, asset_class TEXT NOT NULL DEFAULT 'Equity',
          note TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS alerts(
          id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL,
          condition TEXT NOT NULL CHECK(condition IN ('ABOVE','BELOW')),
          trigger_price REAL NOT NULL CHECK(trigger_price>0), active INTEGER NOT NULL DEFAULT 1,
          last_state TEXT NOT NULL DEFAULT 'WAITING', last_checked TEXT,
          triggered_at TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        ''')

def add_symbol(symbol, asset_class='Equity', note='', db_path=None):
    symbol=str(symbol).strip().upper()
    if not symbol: raise ValueError('Enter a symbol.')
    init_db(db_path)
    with _connect(db_path) as c:
        c.execute('INSERT OR REPLACE INTO watchlist(symbol,asset_class,note) VALUES(?,?,?)',(symbol,asset_class,str(note)))
    return symbol

def remove_symbol(symbol, db_path=None):
    init_db(db_path)
    with _connect(db_path) as c: return c.execute('DELETE FROM watchlist WHERE symbol=?',(str(symbol).upper(),)).rowcount>0

def get_watchlist(db_path=None):
    init_db(db_path)
    with _connect(db_path) as c: return pd.read_sql_query('SELECT * FROM watchlist ORDER BY symbol',c)

def add_alert(symbol, condition, trigger_price, db_path=None):
    symbol=str(symbol).strip().upper(); condition=str(condition).upper(); trigger_price=float(trigger_price)
    if not symbol or condition not in ('ABOVE','BELOW') or trigger_price<=0: raise ValueError('Invalid alert rule.')
    init_db(db_path)
    with _connect(db_path) as c:
        cur=c.execute('INSERT INTO alerts(symbol,condition,trigger_price) VALUES(?,?,?)',(symbol,condition,trigger_price))
        return cur.lastrowid

def get_alerts(db_path=None):
    init_db(db_path)
    with _connect(db_path) as c: return pd.read_sql_query('SELECT * FROM alerts ORDER BY id DESC',c)

def evaluate_alerts(prices: dict, db_path=None):
    """Evaluate explicitly supplied latest prices; no polling/background process."""
    init_db(db_path); events=[]
    with _connect(db_path) as c:
        rows=c.execute('SELECT * FROM alerts WHERE active=1').fetchall()
        for row in rows:
            px=prices.get(row['symbol'])
            if px is None: continue
            px=float(px)
            hit=(px>=row['trigger_price']) if row['condition']=='ABOVE' else (px<=row['trigger_price'])
            state='TRIGGERED' if hit else 'WAITING'
            c.execute('UPDATE alerts SET last_state=?,last_checked=CURRENT_TIMESTAMP,triggered_at=CASE WHEN ?=1 AND triggered_at IS NULL THEN CURRENT_TIMESTAMP ELSE triggered_at END WHERE id=?',(state,int(hit),row['id']))
            if hit: events.append({'id':row['id'],'symbol':row['symbol'],'condition':row['condition'],'trigger_price':row['trigger_price'],'observed_price':px})
    return events

def deactivate_alert(alert_id, db_path=None):
    init_db(db_path)
    with _connect(db_path) as c: return c.execute('UPDATE alerts SET active=0 WHERE id=?',(int(alert_id),)).rowcount>0

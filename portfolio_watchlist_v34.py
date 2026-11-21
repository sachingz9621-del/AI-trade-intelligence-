"""Local portfolio, watchlist and price-alert utilities for V34.

Data is stored in a project-local SQLite database. Quotes are supplied by the
caller; this module never claims they are exchange-live or places orders.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Iterable
import pandas as pd

DB_PATH = Path(__file__).with_name("ati_portfolio_v34.sqlite3")


def _connect(db_path=None):
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def init_db(db_path=None):
    with _connect(db_path) as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL UNIQUE,
            asset_class TEXT NOT NULL DEFAULT 'Equity', note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL,
            side TEXT NOT NULL CHECK(side IN ('LONG','SHORT')),
            quantity REAL NOT NULL CHECK(quantity > 0), entry_price REAL NOT NULL CHECK(entry_price > 0),
            stop_loss REAL, target REAL, note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS price_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL,
            condition TEXT NOT NULL CHECK(condition IN ('ABOVE','BELOW')),
            trigger_price REAL NOT NULL CHECK(trigger_price > 0), active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        """)


def add_watchlist(symbol, asset_class='Equity', note='', db_path=None):
    symbol = str(symbol).strip().upper()
    if not symbol: raise ValueError('Symbol is required')
    init_db(db_path)
    with _connect(db_path) as con:
        con.execute('INSERT OR IGNORE INTO watchlist(symbol,asset_class,note) VALUES(?,?,?)', (symbol, asset_class, str(note)))
    return symbol


def remove_watchlist(symbol, db_path=None):
    init_db(db_path)
    with _connect(db_path) as con:
        cur = con.execute('DELETE FROM watchlist WHERE symbol=?', (str(symbol).strip().upper(),))
        return cur.rowcount > 0


def list_watchlist(db_path=None):
    init_db(db_path)
    with _connect(db_path) as con:
        return pd.read_sql_query('SELECT id,symbol,asset_class,note,created_at FROM watchlist ORDER BY symbol', con)


def add_position(symbol, side, quantity, entry_price, stop_loss=None, target=None, note='', db_path=None):
    symbol, side = str(symbol).strip().upper(), str(side).strip().upper()
    quantity, entry_price = float(quantity), float(entry_price)
    if not symbol or side not in ('LONG','SHORT') or quantity <= 0 or entry_price <= 0:
        raise ValueError('Valid symbol, LONG/SHORT side, positive quantity and entry price are required')
    sl = None if stop_loss in (None, 0, '') else float(stop_loss)
    tp = None if target in (None, 0, '') else float(target)
    init_db(db_path)
    with _connect(db_path) as con:
        cur = con.execute('INSERT INTO positions(symbol,side,quantity,entry_price,stop_loss,target,note) VALUES(?,?,?,?,?,?,?)',
                          (symbol,side,quantity,entry_price,sl,tp,str(note)))
        return cur.lastrowid


def remove_position(position_id, db_path=None):
    init_db(db_path)
    with _connect(db_path) as con:
        cur = con.execute('DELETE FROM positions WHERE id=?', (int(position_id),))
        return cur.rowcount > 0


def list_positions(db_path=None):
    init_db(db_path)
    with _connect(db_path) as con:
        return pd.read_sql_query('SELECT * FROM positions ORDER BY id DESC', con)


def add_price_alert(symbol, condition, trigger_price, db_path=None):
    symbol, condition = str(symbol).strip().upper(), str(condition).strip().upper()
    price = float(trigger_price)
    if not symbol or condition not in ('ABOVE','BELOW') or price <= 0:
        raise ValueError('Valid symbol, ABOVE/BELOW condition and positive trigger price are required')
    init_db(db_path)
    with _connect(db_path) as con:
        cur = con.execute('INSERT INTO price_alerts(symbol,condition,trigger_price) VALUES(?,?,?)', (symbol,condition,price))
        return cur.lastrowid


def list_price_alerts(db_path=None, active_only=False):
    init_db(db_path)
    sql = 'SELECT * FROM price_alerts' + (' WHERE active=1' if active_only else '') + ' ORDER BY id DESC'
    with _connect(db_path) as con:
        return pd.read_sql_query(sql, con)


def evaluate_alerts(quotes: dict[str, float], db_path=None):
    """Return newly triggered alerts and deactivate them to avoid repeat firing."""
    triggered = []
    init_db(db_path)
    with _connect(db_path) as con:
        rows = con.execute('SELECT * FROM price_alerts WHERE active=1').fetchall()
        for row in rows:
            px = quotes.get(row['symbol'])
            if px is None: continue
            px = float(px)
            hit = px >= row['trigger_price'] if row['condition'] == 'ABOVE' else px <= row['trigger_price']
            if hit:
                item = dict(row); item['observed_price'] = px; triggered.append(item)
                con.execute('UPDATE price_alerts SET active=0 WHERE id=?', (row['id'],))
    return triggered


def mark_to_market(positions: pd.DataFrame, quotes: dict[str, float]):
    """Calculate marked value and risk using caller-provided latest prices."""
    if positions is None or positions.empty:
        return pd.DataFrame(), {'positions':0,'market_value':0.0,'unrealized_pnl':0.0,'risk_to_stops':0.0}
    rows=[]
    for _, p in positions.iterrows():
        px = quotes.get(str(p['symbol']).upper())
        side_mult = 1.0 if p['side']=='LONG' else -1.0
        pnl = (float(px)-float(p['entry_price']))*float(p['quantity'])*side_mult if px is not None else None
        market_value = float(px)*float(p['quantity']) if px is not None else None
        sl = p.get('stop_loss')
        risk = max(0.0, (float(p['entry_price'])-float(sl))*float(p['quantity'])*side_mult) if pd.notna(sl) else None
        rows.append({**p.to_dict(),'last_price':float(px) if px is not None else None,'market_value':market_value,'unrealized_pnl':pnl,'risk_to_stop':risk})
    out=pd.DataFrame(rows)
    return out, {'positions':len(out),'market_value':float(out.market_value.sum(min_count=1) or 0),'unrealized_pnl':float(out.unrealized_pnl.sum(min_count=1) or 0),'risk_to_stops':float(out.risk_to_stop.sum(min_count=1) or 0)}

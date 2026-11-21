"""V39 deterministic paper execution simulator. No broker/network order routing."""
from pathlib import Path
import sqlite3
import json
import pandas as pd

DB_PATH = Path(__file__).with_name('ati_v39_paper_execution.sqlite3')
ORDER_TYPES = ('MARKET', 'LIMIT', 'STOP_MARKET', 'STOP_LIMIT')


def _connect(db_path=None):
    p = Path(db_path) if db_path else DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(p)
    c.row_factory = sqlite3.Row
    return c


def init_db(db_path=None):
    with _connect(db_path) as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS sim_orders (
          id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL,
          side TEXT NOT NULL CHECK(side IN ('BUY','SELL')),
          order_type TEXT NOT NULL CHECK(order_type IN ('MARKET','LIMIT','STOP_MARKET','STOP_LIMIT')),
          quantity REAL NOT NULL CHECK(quantity > 0), limit_price REAL, stop_price REAL,
          status TEXT NOT NULL DEFAULT 'PENDING', reference_price REAL, fill_price REAL,
          slippage_cost REAL DEFAULT 0, fees REAL DEFAULT 0, position_id INTEGER,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT,
          notes TEXT NOT NULL DEFAULT '',
          CHECK((order_type IN ('LIMIT','STOP_LIMIT') AND limit_price IS NOT NULL) OR order_type NOT IN ('LIMIT','STOP_LIMIT')),
          CHECK((order_type IN ('STOP_MARKET','STOP_LIMIT') AND stop_price IS NOT NULL) OR order_type NOT IN ('STOP_MARKET','STOP_LIMIT'))
        );
        CREATE TABLE IF NOT EXISTS sim_positions (
          id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL,
          direction TEXT NOT NULL CHECK(direction IN ('LONG','SHORT')),
          quantity REAL NOT NULL CHECK(quantity > 0), entry_price REAL NOT NULL,
          entry_fees REAL NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'OPEN',
          exit_price REAL, exit_fees REAL DEFAULT 0, gross_pnl REAL, net_pnl REAL,
          opened_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, closed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS sim_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER, event TEXT NOT NULL,
          detail TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        ''')


def estimate_costs(price, quantity, *, brokerage_bps=3.0, exchange_bps=3.0,
                   regulatory_bps=0.1, tax_bps=0.0, slippage_bps=2.0):
    """Illustrative configurable bps model, not a statutory broker tax calculator."""
    vals = [float(price), float(quantity), float(brokerage_bps), float(exchange_bps),
            float(regulatory_bps), float(tax_bps), float(slippage_bps)]
    price, quantity, brokerage_bps, exchange_bps, regulatory_bps, tax_bps, slippage_bps = vals
    if price <= 0 or quantity <= 0 or min(brokerage_bps, exchange_bps, regulatory_bps, tax_bps, slippage_bps) < 0:
        raise ValueError('Price and quantity must be positive; cost rates cannot be negative.')
    turnover = price * quantity
    brokerage = turnover * brokerage_bps / 10000
    exchange = turnover * exchange_bps / 10000
    regulatory = turnover * regulatory_bps / 10000
    tax = turnover * tax_bps / 10000
    slippage = turnover * slippage_bps / 10000
    return {'turnover': turnover, 'brokerage': brokerage, 'exchange': exchange,
            'regulatory': regulatory, 'tax_estimate': tax, 'fees': brokerage + exchange + regulatory + tax,
            'slippage_estimate': slippage, 'total_estimated_cost': brokerage + exchange + regulatory + tax + slippage,
            'assumption': 'User-configurable basis-point estimates; not actual broker charges or statutory tax advice.'}


def _event(c, order_id, event, detail=''):
    c.execute('INSERT INTO sim_events(order_id,event,detail) VALUES(?,?,?)',
              (order_id, event, str(detail)))


def create_order(symbol, side, order_type, quantity, *, limit_price=None, stop_price=None,
                 reference_price=None, notes='', db_path=None, cost_config=None):
    symbol, side, order_type = str(symbol).strip().upper(), str(side).upper(), str(order_type).upper()
    quantity = float(quantity)
    if not symbol or side not in ('BUY', 'SELL') or order_type not in ORDER_TYPES or quantity <= 0:
        raise ValueError('Enter a symbol, BUY/SELL side, supported order type and positive quantity.')
    if order_type in ('LIMIT', 'STOP_LIMIT') and (limit_price is None or float(limit_price) <= 0):
        raise ValueError('Limit orders require a positive limit price.')
    if order_type in ('STOP_MARKET', 'STOP_LIMIT') and (stop_price is None or float(stop_price) <= 0):
        raise ValueError('Stop orders require a positive stop price.')
    if order_type == 'MARKET' and (reference_price is None or float(reference_price) <= 0):
        raise ValueError('Market paper orders require a positive reference price.')
    init_db(db_path)
    with _connect(db_path) as c:
        cur = c.execute('''INSERT INTO sim_orders(symbol,side,order_type,quantity,limit_price,stop_price,status,notes)
                           VALUES(?,?,?,?,?,?,?,?)''',
                        (symbol, side, order_type, quantity, limit_price, stop_price,
                         'PENDING', str(notes)))
        oid = cur.lastrowid
        _event(c, oid, 'CREATED', f'{side} {quantity:g} {symbol} {order_type}')
    if order_type == 'MARKET':
        process_market_data({symbol: float(reference_price)}, db_path=db_path, cost_config=cost_config)
    return oid


def _is_triggered(row, px):
    side, typ = row['side'], row['order_type']
    if typ in ('MARKET', 'LIMIT'):
        return True
    if side == 'BUY':
        return px >= row['stop_price']
    return px <= row['stop_price']


def _limit_marketable(row, px):
    if row['order_type'] not in ('LIMIT', 'STOP_LIMIT'):
        return True
    return px <= row['limit_price'] if row['side'] == 'BUY' else px >= row['limit_price']


def process_market_data(prices: dict, *, db_path=None, cost_config=None):
    """Evaluate pending orders against explicitly supplied prices; one fill per order."""
    init_db(db_path)
    cfg = dict(cost_config or {})
    events = []
    with _connect(db_path) as c:
        rows = c.execute("SELECT * FROM sim_orders WHERE status IN ('PENDING','TRIGGERED') ORDER BY id").fetchall()
        for row in rows:
            if row['symbol'] not in prices or prices[row['symbol']] is None:
                continue
            px = float(prices[row['symbol']])
            if px <= 0:
                continue
            if row['status'] == 'PENDING' and not _is_triggered(row, px):
                continue
            if row['order_type'] in ('STOP_MARKET', 'STOP_LIMIT') and row['status'] == 'PENDING':
                c.execute("UPDATE sim_orders SET status='TRIGGERED',reference_price=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (px, row['id']))
                _event(c, row['id'], 'TRIGGERED', f'Stop condition observed at {px:g}')
                events.append({'order_id': row['id'], 'event': 'TRIGGERED', 'symbol': row['symbol'], 'observed_price': px})
                row = c.execute('SELECT * FROM sim_orders WHERE id=?', (row['id'],)).fetchone()
            if not _limit_marketable(row, px):
                continue
            # Adverse slippage: buy fills higher; sell fills lower.
            slip_bps = float(cfg.get('slippage_bps', 2.0))
            if slip_bps < 0:
                raise ValueError('Slippage cannot be negative.')
            fill = px * (1 + slip_bps / 10000 if row['side'] == 'BUY' else 1 - slip_bps / 10000)
            costs = estimate_costs(fill, row['quantity'], **cfg)
            direction = 'LONG' if row['side'] == 'BUY' else 'SHORT'
            cur = c.execute('''INSERT INTO sim_positions(symbol,direction,quantity,entry_price,entry_fees)
                               VALUES(?,?,?,?,?)''', (row['symbol'], direction, row['quantity'], fill, costs['fees']))
            pid = cur.lastrowid
            c.execute("UPDATE sim_orders SET status='FILLED',reference_price=?,fill_price=?,slippage_cost=?,fees=?,position_id=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                      (px, fill, costs['slippage_estimate'], costs['fees'], pid, row['id']))
            _event(c, row['id'], 'FILLED', f'Fill {fill:.6f}; fees {costs["fees"]:.4f}; position {pid}')
            events.append({'order_id': row['id'], 'event': 'FILLED', 'symbol': row['symbol'],
                           'reference_price': px, 'fill_price': fill, 'position_id': pid,
                           'fees': costs['fees'], 'slippage_estimate': costs['slippage_estimate']})
    return events


def cancel_order(order_id, db_path=None):
    init_db(db_path)
    with _connect(db_path) as c:
        cur = c.execute("UPDATE sim_orders SET status='CANCELLED',updated_at=CURRENT_TIMESTAMP WHERE id=? AND status IN ('PENDING','TRIGGERED')", (int(order_id),))
        if cur.rowcount:
            _event(c, order_id, 'CANCELLED', 'Cancelled by user')
        return cur.rowcount == 1


def close_position(position_id, exit_reference_price, *, db_path=None, cost_config=None):
    exit_reference_price = float(exit_reference_price)
    if exit_reference_price <= 0:
        raise ValueError('Exit price must be positive.')
    cfg = dict(cost_config or {})
    init_db(db_path)
    with _connect(db_path) as c:
        p = c.execute("SELECT * FROM sim_positions WHERE id=? AND status='OPEN'", (int(position_id),)).fetchone()
        if p is None:
            return False
        slip = float(cfg.get('slippage_bps', 2.0))
        exit_fill = exit_reference_price * (1 - slip / 10000 if p['direction'] == 'LONG' else 1 + slip / 10000)
        costs = estimate_costs(exit_fill, p['quantity'], **cfg)
        gross = ((exit_fill - p['entry_price']) * p['quantity'] if p['direction'] == 'LONG'
                 else (p['entry_price'] - exit_fill) * p['quantity'])
        net = gross - float(p['entry_fees']) - costs['fees']
        c.execute("UPDATE sim_positions SET status='CLOSED',exit_price=?,exit_fees=?,gross_pnl=?,net_pnl=?,closed_at=CURRENT_TIMESTAMP WHERE id=? AND status='OPEN'",
                  (exit_fill, costs['fees'], gross, net, int(position_id)))
        _event(c, None, 'POSITION_CLOSED', f'Position {position_id}; gross {gross:.4f}; net {net:.4f}')
        return {'position_id': int(position_id), 'exit_reference_price': exit_reference_price,
                'exit_fill_price': exit_fill, 'gross_pnl': gross, 'net_pnl': net,
                'exit_fees': costs['fees'], 'slippage_estimate': costs['slippage_estimate']}


def list_orders(db_path=None):
    init_db(db_path)
    with _connect(db_path) as c:
        return pd.read_sql_query('SELECT * FROM sim_orders ORDER BY id DESC', c)


def list_positions(db_path=None, status=None):
    init_db(db_path)
    with _connect(db_path) as c:
        if status:
            return pd.read_sql_query('SELECT * FROM sim_positions WHERE status=? ORDER BY id DESC', c, params=(status.upper(),))
        return pd.read_sql_query('SELECT * FROM sim_positions ORDER BY id DESC', c)


def list_events(db_path=None, limit=100):
    init_db(db_path)
    with _connect(db_path) as c:
        return pd.read_sql_query('SELECT * FROM sim_events ORDER BY id DESC LIMIT ?', c, params=(int(limit),))


def performance_summary(positions: pd.DataFrame):
    closed = positions[positions.status == 'CLOSED'].copy() if positions is not None and not positions.empty else pd.DataFrame()
    if closed.empty:
        return {'closed_positions': 0, 'win_rate_pct': None, 'gross_pnl': 0.0, 'net_pnl': 0.0,
                'total_fees': 0.0, 'profit_factor': None}
    pnl = pd.to_numeric(closed.net_pnl, errors='coerce').fillna(0)
    wins, losses = float(pnl[pnl > 0].sum()), float(-pnl[pnl < 0].sum())
    return {'closed_positions': len(closed), 'win_rate_pct': float((pnl > 0).mean() * 100),
            'gross_pnl': float(closed.gross_pnl.sum()), 'net_pnl': float(pnl.sum()),
            'total_fees': float(closed.entry_fees.sum() + closed.exit_fees.sum()),
            'profit_factor': wins / losses if losses else (float('inf') if wins else None)}

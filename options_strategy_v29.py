"""V29 option strategy builder using a supplied option-chain snapshot.
All P&L values are expiry intrinsic payoff less/plus quoted premiums; no execution.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def _clean(chain: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(chain, pd.DataFrame) or chain.empty:
        raise ValueError('Option chain is empty.')
    required = {'Strike', 'CE LTP', 'PE LTP'}
    missing = required - set(chain.columns)
    if missing:
        raise ValueError('Option chain missing: ' + ', '.join(sorted(missing)))
    x = chain.copy()
    for c in required:
        x[c] = pd.to_numeric(x[c], errors='coerce')
    x = x.dropna(subset=['Strike']).sort_values('Strike').drop_duplicates('Strike')
    if x.empty:
        raise ValueError('No valid strikes in option chain.')
    return x


def _pick(x, side, strike):
    col = f'{side} LTP'
    row = x.iloc[(x.Strike - strike).abs().argsort()[:1]]
    if row.empty:
        raise ValueError('Could not select a contract.')
    r = row.iloc[0]
    premium = float(r[col]) if pd.notna(r[col]) else 0.0
    if premium <= 0:
        raise ValueError(f'{side} premium unavailable at strike {r.Strike:g}.')
    return {'side': side, 'strike': float(r.Strike), 'premium': premium}


def _leg_payoff(leg, terminal):
    intrinsic = np.maximum(terminal-leg['strike'], 0) if leg['side'] == 'CE' else np.maximum(leg['strike']-terminal, 0)
    return leg['qty'] * (intrinsic - leg['premium'])


def _evaluate(name, legs, spot, lot_size, iv, iv_note):
    # Grid is broad enough to show meaningful expiry outcomes, but is not a bound on market prices.
    low, high = max(0.0, spot * .65), spot * 1.35
    grid = np.linspace(low, high, 301)
    unit = np.zeros_like(grid)
    for leg in legs:
        unit += _leg_payoff(leg, grid)
    pnl = unit * lot_size
    debit = sum(l['qty'] * l['premium'] for l in legs) * lot_size
    breakevens = []
    for i in range(len(grid)-1):
        if pnl[i] == 0 or pnl[i] * pnl[i+1] < 0:
            if pnl[i] == 0: breakevens.append(float(grid[i]))
            else:
                breakevens.append(float(grid[i] - pnl[i]*(grid[i+1]-grid[i])/(pnl[i+1]-pnl[i])))
    max_profit = float(np.max(pnl)); max_loss = float(np.min(pnl))
    # Mark unbounded long-option upside explicitly rather than treating grid max as a true cap.
    unbounded = name in ('Long Straddle', 'Long Strangle')
    if unbounded: max_profit = None
    return {'name': name, 'legs': legs, 'net_premium_per_unit': float(sum(l['qty']*l['premium'] for l in legs)),
            'net_debit_or_credit': float(debit), 'max_profit_grid': max_profit,
            'max_loss_grid': max_loss, 'breakevens': breakevens,
            'unlimited_profit': unbounded,
            'payoff': pd.DataFrame({'Underlying at expiry': grid, 'Estimated P&L': pnl}),
            'iv_context': iv_note}


def generate_strategies(chain: pd.DataFrame, lot_size: int = 1, iv_high: float = 25.0) -> list[dict]:
    if int(lot_size) < 1: raise ValueError('Lot size must be at least 1.')
    x = _clean(chain)
    spot_vals = pd.to_numeric(x.get('Spot', pd.Series(dtype=float)), errors='coerce').dropna()
    if spot_vals.empty or float(spot_vals.iloc[0]) <= 0:
        raise ValueError('Underlying spot is not available in this chain snapshot.')
    spot = float(spot_vals.iloc[0])
    atm_idx = int((x.Strike-spot).abs().argmin())
    atm = float(x.iloc[atm_idx].Strike)
    strikes = x.Strike.to_numpy(float)
    step = float(np.median(np.diff(strikes))) if len(strikes)>1 else max(spot*.01, 1)
    step = max(step, 1e-6)
    def opt(side, k, qty):
        z = _pick(x, side, k); z['qty'] = qty; return z
    # Use strikes actually present in the returned expiry snapshot.
    def at(offset): return float(strikes[np.argmin(np.abs(strikes-(atm+offset*step)))])
    candidates = []
    def add(name, legs):
        ivs=[]
        for l in legs:
            col=f"{l['side']} IV"
            if col in x:
                row=x.iloc[(x.Strike-l['strike']).abs().argmin()]
                v=pd.to_numeric(pd.Series([row.get(col)]),errors='coerce').iloc[0]
                if pd.notna(v) and v>0: ivs.append(float(v))
        avg=float(np.mean(ivs)) if ivs else None
        context = ('IV elevated vs selected threshold; compare premium-selling risk carefully.' if avg is not None and avg>=iv_high
                   else 'IV below selected threshold; long-premium cost may still be material.' if avg is not None
                   else 'IV unavailable; no volatility-regime filter applied.')
        candidates.append(_evaluate(name, legs, spot, int(lot_size), avg, context))
    try:
        add('Bull Call Spread',[opt('CE',at(0),1),opt('CE',at(2),-1)])
        add('Bear Put Spread',[opt('PE',at(0),1),opt('PE',at(-2),-1)])
        add('Long Straddle',[opt('CE',at(0),1),opt('PE',at(0),1)])
        add('Long Strangle',[opt('PE',at(-1),1),opt('CE',at(1),1)])
        add('Iron Condor',[opt('PE',at(-2),1),opt('PE',at(-1),-1),opt('CE',at(1),-1),opt('CE',at(2),1)])
    except ValueError as exc:
        # A strategy is omitted if one of its selected contract premiums is missing/zero.
        pass
    if not candidates:
        raise ValueError('No complete strategy could be built. Check available CE/PE premiums and strike coverage.')
    return candidates

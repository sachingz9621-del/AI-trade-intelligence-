"""V28 option-chain positioning analytics; descriptive, not predictive."""
from __future__ import annotations
import numpy as np
import pandas as pd


def _num(s):
    return pd.to_numeric(s, errors='coerce').fillna(0.0)


def analyze_option_chain(chain: pd.DataFrame) -> dict:
    required = {'Strike','CE OI','PE OI'}
    missing = required - set(chain.columns)
    if missing:
        raise ValueError('Option chain missing required columns: ' + ', '.join(sorted(missing)))
    if chain.empty:
        raise ValueError('Option chain is empty.')
    x=chain.copy()
    for c in ('Strike','CE OI','PE OI','CE OI Change','PE OI Change','CE IV','PE IV','CE Volume','PE Volume'):
        if c in x: x[c]=pd.to_numeric(x[c],errors='coerce')
    x=x.dropna(subset=['Strike']).sort_values('Strike').reset_index(drop=True)
    if x.empty: raise ValueError('No valid strike prices in chain.')
    ce=_num(x['CE OI']); pe=_num(x['PE OI']); total_ce=float(ce.sum()); total_pe=float(pe.sum())
    pcr=total_pe/total_ce if total_ce else None
    maxpain=None; curve=[]
    strikes=x['Strike'].to_numpy(float); c=ce.to_numpy(float); p=pe.to_numpy(float)
    payouts=[]
    for settle in strikes:
        payouts.append(float((np.maximum(settle-strikes,0)*c + np.maximum(strikes-settle,0)*p).sum()))
    if payouts:
        idx=int(np.argmin(payouts)); maxpain=float(strikes[idx])
        curve=[{'Settlement':float(k),'Estimated payout':float(v)} for k,v in zip(strikes,payouts)]
    call_wall=float(x.loc[ce.idxmax(),'Strike']) if ce.sum()>0 else None
    put_wall=float(x.loc[pe.idxmax(),'Strike']) if pe.sum()>0 else None
    spot_vals=pd.to_numeric(x.get('Spot',pd.Series(dtype=float)),errors='coerce').dropna()
    spot=float(spot_vals.iloc[0]) if not spot_vals.empty else None
    atm=float(x.loc[(x['Strike']-spot).abs().idxmin(),'Strike']) if spot else None
    ce_ch=_num(x['CE OI Change']) if 'CE OI Change' in x else pd.Series(np.zeros(len(x)))
    pe_ch=_num(x['PE OI Change']) if 'PE OI Change' in x else pd.Series(np.zeros(len(x)))
    ce_iv=pd.to_numeric(x['CE IV'],errors='coerce').replace(0,np.nan) if 'CE IV' in x else pd.Series(dtype=float)
    pe_iv=pd.to_numeric(x['PE IV'],errors='coerce').replace(0,np.nan) if 'PE IV' in x else pd.Series(dtype=float)
    avg_ce_iv=float(ce_iv.mean()) if ce_iv.notna().any() else None
    avg_pe_iv=float(pe_iv.mean()) if pe_iv.notna().any() else None
    # Positioning descriptor deliberately avoids inferring price direction from OI alone.
    if pcr is None: positioning='UNAVAILABLE'
    elif pcr >= 1.25: positioning='PUT OI HEAVIER'
    elif pcr <= .75: positioning='CALL OI HEAVIER'
    else: positioning='BALANCED OI'
    total_change_ce=float(ce_ch.sum()); total_change_pe=float(pe_ch.sum())
    return {'strikes':x,'spot':spot,'atm':atm,'total_ce_oi':total_ce,'total_pe_oi':total_pe,'pcr':pcr,
            'max_pain':maxpain,'max_call_oi_strike':call_wall,'max_put_oi_strike':put_wall,
            'ce_oi_change':total_change_ce,'pe_oi_change':total_change_pe,'positioning':positioning,
            'avg_ce_iv':avg_ce_iv,'avg_pe_iv':avg_pe_iv,'payout_curve':pd.DataFrame(curve),
            'notes':['PCR is total Put OI divided by total Call OI for the returned chain.','Max Pain is an OI-weighted intrinsic-expiry-payout estimate across listed strikes, not a forecast.','Largest OI strikes are descriptive concentration points, not guaranteed support/resistance.','OI change alone cannot distinguish opening, closing, hedging or multi-leg positioning.']}


def strike_activity(chain: pd.DataFrame) -> pd.DataFrame:
    cols=['Strike','CE OI','CE OI Change','CE Volume','PE OI','PE OI Change','PE Volume']
    out=chain[[c for c in cols if c in chain.columns]].copy()
    for c in out.columns:
        if c!='Strike': out[c]=pd.to_numeric(out[c],errors='coerce').fillna(0)
    if 'CE OI Change' in out and 'CE Volume' in out:
        out['Call activity']='Fresh OI build' 
        out.loc[out['CE OI Change']<0,'Call activity']='OI reduction'
        out.loc[out['CE OI Change']==0,'Call activity']='No net OI change'
    if 'PE OI Change' in out and 'PE Volume' in out:
        out['Put activity']='Fresh OI build'
        out.loc[out['PE OI Change']<0,'Put activity']='OI reduction'
        out.loc[out['PE OI Change']==0,'Put activity']='No net OI change'
    return out

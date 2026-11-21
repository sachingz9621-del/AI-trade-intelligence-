# AI Trade Intelligence V11 — Patterns & Opportunity Lab

V11 builds on V10 and retains the existing dashboard, Upstox configuration, options analytics, smart-money research, ML model and historical backtest.

## New V11 research tools
- Candlestick pattern flags: doji, hammer, shooting star, bullish/bearish engulfing and inside bar.
- Possible double-top / double-bottom candidates using confirmed swing pivots.
- Historical forward-return summaries for each candlestick pattern.
- Breakout context using prior 20-candle range, rolling compression and relative volume, with historical analog frequencies.
- Market regime classification using EMA structure and realized volatility.
- Small EMA parameter grid search selected on the first 70% of history and reported on the later untouched 30% holdout.
- Multi-symbol opportunity ranking using trend score, range break and relative volume.

## Run
```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open **AI Patterns & Opportunity Lab** in the sidebar. Select a symbol, history and interval in the sidebar first.

## Important limitations
All V11 tools use OHLCV data from the selected data source. Chart setups are candidates, not confirmed formations. Historical pattern frequencies use overlapping forward windows and are descriptive. Breakout rates are historical analog frequencies, not calibrated probabilities. Opportunity ranking is a heuristic score. EMA optimization is a small research grid and may overfit; the holdout is historical, not future validation. This project does not execute trades or guarantee results.

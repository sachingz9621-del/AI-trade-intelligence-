# AI Trade Intelligence V10 – ML Research & Backtesting

V10 adds an experimental next-candle direction model and a chronological out-of-sample backtest to the V9 project.

## New page

Open **ML Prediction & Backtesting** from the Streamlit sidebar. Select a symbol, history period, and interval in the sidebar, then run the model.

The model uses a deterministic logistic-regression implementation with OHLCV-derived features (returns, candle range, EMA gaps, RSI, rolling volatility, relative volume, MACD and ATR). It uses a chronological train/test split and fits feature scaling only on the training partition. The final candle is excluded because its forward return is unknown.

Backtest assumptions:

- Signal is computed from the current candle and evaluated against the following candle return.
- Long-only is the default; optional short exposure is available for research.
- Transaction cost is a user-configurable basis-point deduction each time exposure changes.
- Strategy and buy-and-hold curves are shown for the same out-of-sample period.
- No parameter optimization, broker orders, or live execution is performed.

## Install and run

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Important limitations

- The model is experimental and is not evidence of a durable trading edge. Accuracy alone does not imply profitability.
- The simple next-candle target ignores spread, market impact, taxes, liquidity, lot sizes, circuit limits, overnight gaps and instrument-specific shorting constraints.
- Cost modelling is simplified and may materially understate real Indian-market charges/slippage.
- Yahoo Finance data may be delayed, incomplete, adjusted, rate-limited or unavailable. Validate with trusted broker/exchange data before relying on results.
- A chronological holdout reduces look-ahead leakage but does not eliminate regime shift, survivorship bias, data errors or repeated experimentation/overfitting.
- No prediction is guaranteed. This is research/educational software, not investment advice or automated trading.

V9 pages, local SQLite journal and alerts remain in the project. Back up `ati_v9_data.sqlite3` before replacing an older project folder.

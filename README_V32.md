# V32 – Chart Pattern Recognition & Smart Entry

Adds an OHLCV-only chart research page to the existing V31 application.

## Features
- Latest-candle doji, hammer-like, shooting-star-like, engulfing and inside-bar labels.
- Prior 20-candle range breakout/breakdown and near-boundary watch states.
- Rolling support/resistance references, ATR, relative-volume context.
- Illustrative entry zone, ATR invalidation and 2-ATR objective for qualifying range contexts.
- Candlestick chart with levels and zones.

## Use
Run the existing app with `streamlit run app.py`, choose a symbol/history/interval in the sidebar, then open **V32 Chart Pattern & Smart Entry**.

## Limitations
This is deterministic heuristic screening, not a trained vision model or predictive AI. Candlestick names are approximate OHLCV rules; rolling extrema are not validated institutional levels. Entry/stop/target values are illustrative, not recommendations or broker orders. The analysis uses the currently selected sidebar data and inherits its source freshness, coverage and delays. No new market-data provider or API key is added.

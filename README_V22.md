# V22 — Advanced Trading Signal Intelligence

V22 adds a separate **Trading Signal Intelligence** page while retaining the existing V21 dashboard, news aggregation, scanners, options tools, Upstox integration and all previous modules.

## What it adds
- Compares 5-minute, 15-minute, 1-hour and daily OHLCV readings.
- Displays each timeframe's directional bias, indicator score, RSI and relative volume.
- Shows candle timestamp age and flags potentially stale data.
- Optionally refreshes news from the existing multi-source aggregator (Indian, international and official publishers) and surfaces high-priority headline context.
- Calculates an ATR-based reference stop, target and cash-equity quantity using the existing risk-plan helper.

## Important limitations
- Technical readings and news priority are transparent keyword/indicator heuristics, not trained AI predictions or calibrated probabilities.
- Yahoo Finance is used for OHLCV history on this page, not as the news source. Intraday history may be delayed, incomplete or unavailable.
- News feeds are best-effort; a failed feed is shown in the feed-availability panel. A missing headline is not proof that no event risk exists.
- ATR levels and quantities are reference calculations for cash-equity shares only, before brokerage, taxes, slippage, gaps and liquidity effects. They are not options lot sizing.
- No broker orders are placed.

## Run
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Select **V22 Trading Signal Intelligence** from the sidebar. Keep your existing `.streamlit/secrets.toml` locally to preserve Upstox access; it is intentionally not included in this ZIP.

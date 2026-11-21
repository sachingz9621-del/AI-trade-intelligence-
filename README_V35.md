# V35 – Central AI Brain & 25 Specialist Trading Tools

V35 adds one unified decision-support workspace over the existing V28–V34 modules. It includes a 25-tool directory, a central OHLCV evidence assessment, a multi-asset quick scanner, an illustrative risk calculator and historical correlation analysis.

## Run

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

Open **V35 Central AI Brain – 25 Tools** in the sidebar. Select a symbol and load candles in the normal sidebar, then run the Central AI Brain. The quick scanner accepts Yahoo Finance tickers (up to 30 at a time). Correlation uses aligned daily closes for symbols with available history.

## What is integrated

The catalog maps 25 specialist roles across market scanning, technical analysis, patterns, support/resistance, breakout checks, multi-timeframe analysis, sentiment, options chain/OI/Max Pain/strategy/Greeks/expiry, trade confirmation, entry/exit, risk, setup quality, journaling, news, economic calendar, FII/DII, sector rotation, correlation, portfolio, backtesting and the trading copilot.

Existing V28–V34 pages and engines remain in the app. V35 adds a central coordination surface and reuses the currently selected symbol's OHLCV history. Some specialist roles are provided by existing pages/modules rather than independently reimplemented in V35. Tools that require options-chain, news, event, institutional-flow or broker data will report missing inputs or require the relevant module/source; the dashboard does not invent these values.

## Evidence model

The central score uses EMA20/EMA50 alignment, RSI, MACD, 20-candle range breakouts, relative volume and optional user-supplied PCR, institutional-flow and news contributions. Labels are `BULLISH_CANDIDATE`, `BEARISH_CANDIDATE` or `WAIT / MIXED`. The score is a transparent heuristic, **not a calibrated win probability**. ATR-based levels are illustrative only.

## Data and safety limits

- Historical data is loaded through the existing Yahoo Finance integration and may be delayed, incomplete or unavailable.
- Commodity, FX and crypto tickers may be indicative Yahoo Finance proxies, not exchange-certified live feeds.
- Manual PCR/FII-DII/news fields are only as reliable as the data entered by the operator.
- V35 does not place orders, connect to a broker for execution, guarantee outcomes or provide personalized investment advice.
- Risk sizing is for cash-equity units and excludes fees, slippage, gaps and leverage; do not use it as an options lot-size calculation.

## Tests

Focused V35 and V28–V34 tests are included. Run `pytest -q` for the full suite; some pre-existing optional integrations/tests may require the `upstox_client` dependency and configured external credentials.

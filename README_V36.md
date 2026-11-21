# V36 – Live Operations & Institutional Monitor

V36 adds a read-only operations page for the existing Upstox V3 websocket integration.

## Features
- Start/stop the existing read-only Upstox V3 stream from the app.
- Configure multiple exact Upstox instrument keys.
- Show connection state, message count, last-message metadata and diagnostics.
- Normalize common `fullFeed.marketFF.ltpc` and `fullFeed.indexFF.ltpc` quote shapes.
- Show LTP, previous close, percentage change, volume, OI and OHLC fields when the feed provides them.
- Evaluate a manual LTP-above/below rule against the latest received tick.

## Setup
1. Install project dependencies from `requirements.txt`.
2. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
3. Add your Upstox access token locally. Never paste tokens into chat or commit secrets.
4. Start with `streamlit run app.py` and open **V36 Live Operations & Institutional Monitor**.
5. Enter exact instrument keys from the current Upstox instrument master and start the feed.

## Limitations
- Read-only only; no broker orders.
- This page displays only fields present in the incoming websocket payload.
- The feed's global last-update label is not an independently verified per-instrument exchange timestamp.
- A threshold is evaluated only when the user presses the button; this version does not run a background alert scheduler or push notifications.
- It does not derive verified FII/DII activity, institutional trades, or order-book liquidity from OHLCV candles.
- Broker entitlements, token validity, instrument keys, API availability and network conditions determine whether live ticks arrive.

## V37 — Ultimate Platform Integration

V37 adds a unified 40-module directory (25 specialist tools + 15 platform capabilities), a persistent local paper-trade ledger in `ati_v37_workspace.sqlite3`, risk-budget position sizing, paper-trade metrics, and a chronological EMA walk-forward baseline. Existing V28–V36 modules and the V34 database are left intact; V37 uses a separate database file and additive app navigation.

### Important maturity and safety notes
- The 40-module catalogue describes the intended integrated platform scope; it does not claim every item is autonomous or production complete.
- Existing specialist modules remain available in their existing navigation pages and data-source requirements.
- V37 paper trades are simulated and stored locally. They are not broker-synced.
- Walk-forward test is a simple long/flat EMA baseline, not a validated production strategy. It excludes costs, slippage, taxes, latency and market impact.
- Position sizing is illustrative and excludes gap risk, fees, taxes and margin. Derivative lot sizes must be checked against current contract specifications.
- Live monitoring depends on the app process, broker feed, network, token and supported instrument keys. This package does not install a persistent cloud daemon or mobile push service.
- Broker order placement remains disabled. Multi-user production authentication and permission management require deployment-specific security hardening.
- Keep `.streamlit/secrets.toml` local and private. Never include real credentials in shared ZIPs.

## V38 Professional Trading Terminal
- Adds a dedicated professional terminal page without removing earlier navigation pages.
- Adds a separate local SQLite watchlist and price-alert rule store (`ati_v38_terminal.sqlite3`).
- Provides multi-symbol daily-close snapshot, the existing candlestick/EMA/RSI/MACD chart, uploaded option-chain CSV inspection, and manual alert evaluation.
- Uses the existing Yahoo Finance history adapter for this page's watchlist snapshots unless a separate broker feed is connected; this is not guaranteed real-time exchange data.
- Alert rules are evaluated only when the user presses the evaluation button; no background daemon, push delivery, or broker order execution is enabled.
- Existing V34 portfolio storage and V37 paper-trade storage are separate and are not modified by V38.

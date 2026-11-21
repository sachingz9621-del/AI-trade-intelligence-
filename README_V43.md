# V43 – Live Market Intelligence & Monitoring

V43 is an additive upgrade on V42. It adds a dedicated Live Market Intelligence page with four workspaces:

1. **Live Feed Monitor** – starts/stops the existing read-only Upstox V3 websocket, displays connection health, received message count and quotes normalised by the existing V36 adapter.
2. **Opportunity Scanner** – performs explainable EMA/RSI/MACD trend screening on the currently loaded Yahoo Finance OHLCV history, with data-quality gates.
3. **Smart Alert Centre** – stores price threshold rules and trigger history in a new local `ati_v43_monitor.sqlite3` database. Rules are evaluated only against recognised Upstox feed quotes when this page is run/refreshed; this is not a 24/7 push service.
4. **Data Quality** – checks OHLCV schema, missing values and inconsistent candle ranges before scanner output.

The Main Command Center includes a shortcut to V43. All previous pages and modules are retained. V43 does not change the V34, V37, V38 or V39 databases; it creates its own V43 database at runtime. No broker order endpoint is called.

## Important limitations
- Live streaming requires the Upstox SDK, valid local `.streamlit/secrets.toml` token and valid instrument keys.
- The websocket runs inside the Streamlit process and is not a managed always-on daemon. Keep the app open; reconnect/refresh behavior depends on the broker SDK and network.
- Historical scanner data comes from the app's configured Yahoo Finance loader and may be delayed/limited. It is not a multi-symbol exchange-wide live scanner.
- Alerts are evaluated from recognised feed snapshots, not delivered as guaranteed mobile push notifications.
- Signal logic is deterministic and rule-based, not an autonomous predictive AI model.
- No real-money order placement is implemented.

## Run
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Keep credentials in local `.streamlit/secrets.toml`; never put broker tokens in source code or chat.

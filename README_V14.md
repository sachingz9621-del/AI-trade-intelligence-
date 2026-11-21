# AI Trade Intelligence V14 — Live Feed Monitor

V14 builds on the V13 project and adds a read-only Upstox WebSocket monitor with connection state, message count, last-message timestamp, error reporting, start/stop controls, and a latest-index snapshot. Existing dashboard pages and engines are retained.

## Install / run

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Configure Upstox locally

1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
2. Put your own valid access token in `UPSTOX_ACCESS_TOKEN`.
3. Never share `secrets.toml`, screenshots containing the token, or the token itself.
4. Restart Streamlit and open **V14 Live Feed Monitor**.
5. Select **Start / Connect feed**, then use **Refresh status** to inspect connection and incoming-message diagnostics.

The default instruments are `NSE_INDEX|Nifty 50`, `NSE_INDEX|Nifty Bank`, and `NSE_INDEX|India VIX`. The feed is read-only; no order placement or automated trading is included. Market-data access depends on Upstox account permissions, valid token, connectivity, SDK compatibility, and market availability. A connected socket is not proof that prices are updating; check message count and last-message time.

## Tests

```powershell
python -m pytest -q
```

Tests validate local analytics and feed-state helpers. They do not authenticate with Upstox or prove a live market connection; that must be verified with the user's own token.

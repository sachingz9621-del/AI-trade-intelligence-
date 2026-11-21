# V42 – AI Trade Decision & Broker Hub

V42 is an additive upgrade to V41. It introduces a unified decision workspace with separate Scalping, Intraday and Hedging assessments, explicit risk gates, option-chain hedge candidate ranking, paper execution hand-off and an Upstox read-only profile check.

## What's new
- **AI Decision Centre:** explainable rule-based assessments from loaded OHLCV candles using EMA 9/20/50 alignment, RSI, MACD, relative volume and optional manually supplied multi-timeframe context.
- **Scalping safety gate:** scalp decisions are forced to WAIT unless the selected chart interval is 1m, 2m or 5m. The application does not fabricate granular candles.
- **Intraday assessment:** trend/momentum candidate with ATR-based reference entry, stop and target, plus R:R and illustrative position size.
- **Hedging context:** candle-only bias is not treated as a hedge. Upload a real option-chain CSV to rank existing PUT or CALL contracts by distance and OI. No strike, premium, expiry or Greeks are invented.
- **Risk sizing:** quantity rounds down to the supplied lot size; risk budget is capped at 5% in the helper and warns about gap/slippage/fees/margin.
- **Paper execution:** explicit user action creates a MARKET paper order in the existing V39 simulator ledger. It does not send broker orders.
- **Upstox read-only broker gateway:** tests the authenticated `/v2/user/profile` endpoint using `UPSTOX_ACCESS_TOKEN` from local `.streamlit/secrets.toml`. The token is never shown or logged.
- **Broker order preview:** validates and displays a non-executable order payload. V42 does not call any broker order endpoint and real-money execution is disabled.

## Limitations and data integrity
- The decision engine is deterministic/rule-based, not 25 independent autonomous AI models.
- Higher/lower timeframe context shown in the UI is manually selected by the user; it is not presented as independently fetched live candles.
- Option-chain analysis requires a CSV containing real provider data. Required columns: `Strike`, `PE LTP`, `PE OI` for long protection or `Strike`, `CE LTP`, `CE OI` for short protection. Optional columns include IV, Delta, Expiry and instrument key.
- Hedge candidates are not a personalised hedge ratio or execution recommendation. Confirm expiry, lot size, bid/ask, Greeks, liquidity and portfolio exposure separately.
- Yahoo Finance history may be delayed, limited or unavailable. A daily candle is never silently converted into a scalping feed.
- No real-money order endpoint is implemented or called. Human approval is required even for paper order creation.
- Existing SQLite ledgers and credentials are local runtime files and are not bundled in the ZIP. Back them up separately.

## Run
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Local Upstox configuration
Create `.streamlit/secrets.toml` locally:
```toml
UPSTOX_ACCESS_TOKEN = "your_access_token"
```
Do not commit this file or share tokens in chat. The ZIP includes only `.streamlit/secrets.toml.example`.

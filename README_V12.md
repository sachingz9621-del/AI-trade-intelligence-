# AI Trade Intelligence V12 — Market Intelligence

V12 builds on the V11 project and preserves its existing dashboard pages and engines.

## New module

Open **V12 Market Intelligence** in the sidebar.

- **Volume intelligence:** relative volume versus the prior 20-candle average, On-Balance Volume (OBV) direction, and Chaikin Money Flow (CMF).
- **Market structure:** confirmed swing highs/lows and close-based structure-break context. Swings require candles to the right, so the latest unconfirmed extreme is not treated as a pivot.
- **Candidate supply/demand zones:** ATR-proximity clusters built from confirmed pivot candles.
- **Sector rotation:** five-session sector-index returns compared with NIFTY 50, with a downloadable CSV.

## Install and run (Windows PowerShell)

From the extracted `AI_Trade_Intelligence` folder:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Use `python -m streamlit` so the command works even when the Scripts folder is not on PATH.

## Data and limitations

- The app's historical chart data is sourced from Yahoo Finance; availability, symbol coverage and delays are outside this project's control.
- Sector rotation uses Yahoo Finance index price returns, not sector fund flows.
- OBV and CMF are OHLCV-derived estimates. They do not identify actual institutional trades, FII/DII positions, order-book liquidity or participant identity.
- Supply/demand areas and swing structure are technical heuristics, not guaranteed support/resistance or trading instructions.
- The V12 sector table requires internet access and may be empty when the upstream source is unavailable.
- Existing Upstox features still require a valid access token and compatible SDK/API access. This build does not claim the live feed has been verified against your account.

## Tests

The V12 module has unit tests for volume metrics, swing structure, zone output and relative sector ranking. Run:

```powershell
python -m pytest -q --ignore=test_market_stream.py
```

The project tests in the build environment passed: **27 passed**. This is not a guarantee that every external data feed or broker integration works on every machine.

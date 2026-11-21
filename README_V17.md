# AI Trade Intelligence V17 — Intraday Signal & Confluence Desk

V17 adds a read-only 5-minute / 15-minute technical confluence page to the V16 project.

## Run

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Use

1. Select a Yahoo Finance symbol in the sidebar (for example `RELIANCE.NS`, `SBIN.NS`, or `^NSEI`).
2. Open **V17 Intraday Signal Engine**.
3. Click **Fetch 5-minute and 15-minute candles**.
4. Review the combined bias and the separate timeframe evidence.

## Method

Each timeframe evaluates EMA 9/20/50 alignment, price relative to EMA 9, RSI momentum, and elevated relative volume. Each check contributes a transparent heuristic score. A directional bias is shown only when both timeframes agree; conflicting or neutral timeframes produce `WAIT`.

## Limitations and safety

- Yahoo Finance intraday data is not a guaranteed real-time feed; it can be delayed, incomplete, rate-limited, or unavailable.
- This page does not consume Upstox WebSocket ticks, does not generate a statistically calibrated probability, and does not place orders.
- The score is a technical screening heuristic, not a buy/sell recommendation. Verify prices, liquidity, spreads, event risk, and position sizing independently.
- The existing V16 options modules and their limitations remain unchanged.

## Tests

Run `python -m pytest -q --ignore=test_market_stream.py` from this folder. The live Upstox stream test is excluded because it requires the SDK and credentials and is not a live connectivity test.

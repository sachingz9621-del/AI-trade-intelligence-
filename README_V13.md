# AI Trade Intelligence V13 — AI Market Command Centre

V13 continues from the V12 project and retains its existing pages and engines.

## New page: V13 AI Market Command Centre

- **Market regime:** classifies the selected OHLCV series as Trending, Range-bound or Transitioning; reports bullish/bearish/neutral EMA context, ATR percentage, efficiency ratio and a historical volatility percentile.
- **NIFTY + BANKNIFTY confluence:** fetches six months of daily Yahoo Finance history for `^NSEI` and `^NSEBANK`, then compares each index's technical regime. The result can be mixed/divergent when the two indices disagree.
- **Opportunity ranking:** fetches daily history for comma-separated Yahoo Finance symbols and ranks usable series using trend context, regime and relative volume. Results can be exported as CSV.

## Install and run (Windows PowerShell)

From the extracted `AI_Trade_Intelligence` folder:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open **V13 AI Market Command Centre** in the sidebar.

## Data limitations and risk

Yahoo Finance data availability, symbol coverage and delays are outside this project's control. The index analysis and opportunity score are transparent OHLCV heuristics, not ML probabilities, guaranteed predictions, verified institutional flows or broker order-book data. The scanner ranks research candidates only; it does not place orders. Check live prices, liquidity, spreads, events and risk independently.

## Tests

Run the local analytical tests (excluding the separate Upstox stream integration test):

```powershell
python -m pytest -q --ignore=test_market_stream.py
```

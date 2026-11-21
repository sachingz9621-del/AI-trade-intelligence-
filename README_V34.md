# V34 – Portfolio & Watchlist Intelligence

Adds a local SQLite-based portfolio ledger, watchlist, manual one-shot price alerts, and marked-to-market position/risk summary.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open **V34 Portfolio & Watchlist Intelligence** in the sidebar.

## Capabilities

- Add/remove symbols in a persistent local watchlist, with asset class and notes.
- Record LONG/SHORT open positions, quantity, average entry, stop reference and target reference.
- Manually refresh latest available daily candle prices and calculate illustrative market value, unrealized P&L and risk to entered stops.
- Create ABOVE/BELOW one-shot price alerts and manually check them against the latest available candle.
- Export the position ledger as CSV.

## Storage and limitations

Records are stored in `ati_portfolio_v34.sqlite3` beside the app. Back up this file if you need to preserve records. The data is not broker-connected, not cloud-synced and not encrypted by this module. Yahoo Finance daily candles can be delayed, stale or unavailable. Alerts are evaluated only when the user presses the check button; they are not background notifications. Risk-to-stop is a simple estimate before fees, slippage, gaps, margin and derivatives contract multipliers. No order placement or investment recommendation is provided.

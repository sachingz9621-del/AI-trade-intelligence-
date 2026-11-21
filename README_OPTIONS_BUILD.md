# AI Trade Intelligence – Options Analytics Build

## Added in this build
- More tolerant option-chain CSV column detection and numeric cleanup.
- Call/Put OI totals and Put-Call Ratio (PCR).
- Estimated Max Pain plus an OI-weighted intrinsic payout curve.
- Optional OI-change summary when change columns are present.
- Optional European Black–Scholes Delta, Gamma, Theta/day and Vega/1% when CE_IV and/or PE_IV columns are supplied.
- Downloadable analyzed CSV.

## Run
`python -m pip install -r requirements.txt`
`python -m streamlit run app.py`

## CSV format
Required: `Strike`, `CE_OI`, `PE_OI`.
Optional: `CE_change_OI`, `PE_change_OI`, `CE_IV`, `PE_IV`.
IV must be expressed in percent (e.g. 18.5). All rows must refer to the same underlying and expiry.

## Limitations
This is CSV-driven analysis, not a live NSE option-chain feed. Max Pain is an OI-weighted intrinsic payout estimate, not a prediction. Greeks are theoretical European Black–Scholes estimates and omit dividends, early exercise, volatility skew and market microstructure. Verify all values with your broker; this tool does not place orders or provide guaranteed signals.

## V4 — AI Market Intelligence
- Added a new **AI Market Intelligence** page for range breakout/breakdown context.
- Calculates prior-candle support/resistance, EMA and MACD confluence, RSI, ADX and relative volume.
- Displays ATR-based reference/invalidation levels where data is available.
- Includes transparent rule explanations and explicit limitations; it is not a trained ML model or an execution signal.
- Test with: `python test_market_intelligence.py`

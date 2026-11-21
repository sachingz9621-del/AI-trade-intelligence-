# AI Trade Intelligence V5 — Index & Options Signal Desk

This build continues from the V4 project and adds a transparent, CSV-driven NIFTY/BANKNIFTY options context page.

## New in V5
- Index selector for NIFTY 50, BANKNIFTY, FINNIFTY and SENSEX.
- User-entered current spot and uploaded one-expiry option-chain CSV.
- Aggregate call/put OI and PCR.
- Largest call-OI and put-OI strikes (OI walls).
- ATM strike, estimated Max Pain and expiry payout curve.
- Optional net call/put OI-change context.
- Clear rule-based OI context label and explanation notes.
- Download normalized option-chain data.

## Run
Use Python 3.11 or 3.12. From the `AI_Trade_Intelligence` folder:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Option-chain CSV
Required columns: `Strike`, `CE_OI`, `PE_OI`. Optional columns: `CE_change_OI`, `PE_change_OI`, `CE_LTP`, `PE_LTP`, `CE_IV`, `PE_IV`. Common equivalent column names are also accepted by the existing parser. Upload data for a single underlying and a single expiry only. Enter a current spot price from your broker.

## Important limitations
- This page does **not** connect to a live NSE option-chain endpoint. Data is only as current as the uploaded CSV and manually entered spot.
- PCR, OI walls and Max Pain are descriptive context, not reliable standalone predictors or trade instructions.
- OI change meaning depends on the provider's CSV convention. Verify whether values are net changes.
- No automatic strike recommendation, order placement or guaranteed signal is provided.
- Keep your real Upstox token only in `.streamlit/secrets.toml`; never include it in a shared ZIP.

## Validation
Run:

```bash
python -m unittest -v test_index_options_intelligence.py test_market_intelligence.py
```

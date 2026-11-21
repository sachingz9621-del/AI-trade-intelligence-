# AI Trade Intelligence V15 — Live Options Intelligence

V15 builds on V14 and adds a **read-only** Upstox live options-chain page.

## New features
- Underlying selector: NIFTY 50, BANKNIFTY, FINNIFTY and SENSEX (subject to Upstox instrument/API availability).
- Fetches available option expiries from Upstox `/v2/option/contract`.
- Fetches the selected chain from `/v2/option/chain`.
- Displays spot, ATM strike, aggregate OI PCR, highest Call OI/Put OI strikes, estimated Max Pain, strike-wise OI chart, LTP, volume, OI change and Greeks returned by Upstox.
- CSV export of the retrieved chain.
- Clear API/auth/network error messages. No orders are placed and no live values are fabricated.

## Setup
1. Install dependencies in the project folder:
   `python -m pip install -r requirements.txt`
2. Create `.streamlit/secrets.toml` from `.streamlit/secrets.toml.example` if it does not exist.
3. Add your own valid Upstox access token locally:
   `UPSTOX_ACCESS_TOKEN = "your_token_here"`
4. Start the app:
   `python -m streamlit run app.py`
5. Open **V15 Live Options Intelligence**. Select an underlying, click **Load available expiries**, choose an expiry, then click **Fetch live option chain**.

Never share your access token in chat, screenshots, source code, or ZIP files. If a token is exposed, revoke/rotate it through Upstox.

## Important limitations
- Data access depends on Upstox token validity, API permissions/subscription, exchange availability and market status.
- The option-chain endpoint returns a snapshot when requested; this page is not a continuously streaming options feed. Click Fetch again to refresh.
- OI PCR, OI concentration and Max Pain are descriptive analytics, not reliable standalone trade signals.
- No order placement or automated trading is implemented.

## Official API references
- Option contracts: https://upstox.com/developer/api-documentation/get-option-contracts/
- Put/Call option chain: https://upstox.com/developer/api-documentation/get-pc-option-chain/

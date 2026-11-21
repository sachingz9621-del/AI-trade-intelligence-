# AI Trade Intelligence – next development build

## New in this build
- Added `ai_engine.py`, an explainable technical signal engine using EMA alignment, RSI, MACD histogram, ADX, ATR and relative volume.
- Reworked the AI Prediction Engine page to show signal reasoning, a heuristic confidence indicator and illustrative ATR-based levels.
- News tone and optional option-chain PCR are displayed as context only; they do not silently alter the technical score.

## Run
1. Extract the ZIP.
2. Open a terminal in the `AI_Trade_Intelligence` folder.
3. Install dependencies: `python -m pip install -r requirements.txt`
4. If using Upstox features, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and add your own access token. Never share the real token or upload it in a ZIP.
5. Start: `python -m streamlit run app.py`

## Important limitations
- The signal engine is a transparent rules-based technical scoring model, **not** trained machine learning and not a guaranteed forecast.
- Yahoo Finance data may be delayed, incomplete or unavailable. Verify prices and orders with your broker.
- ATR levels are illustrative reference levels, not personalized trade recommendations.
- Options analysis requires a correctly formatted, current option-chain CSV. Verify expiry, lot size and contract specifications.
- Live Upstox features require a valid token and a supported instrument key. This build has not been authenticated against your account.

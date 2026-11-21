## V11 update
See `README_V11.md` for the new AI Patterns & Opportunity Lab, pattern research, breakout context, regime classification, chronological EMA optimization and multi-symbol ranking.

# AI Trade Intelligence

A Streamlit-based, read-only market analysis dashboard. The existing dashboard features have been retained; this package is a first stabilization pass, not a claim that every live-data integration has been production-validated.

## 1. Install

Python 3.11 or 3.12 is recommended.

```bash
python -m venv .venv
```

Activate the environment:

- Windows: `.venv\\Scripts\\activate`
- macOS/Linux: `source .venv/bin/activate`

Then install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Configure Upstox (optional)

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and replace the placeholder with your own valid Upstox access token. Keep the real `secrets.toml` private. Do not paste your token into chat or share it in a ZIP.

Some dashboard pages use Yahoo Finance data and can work without an Upstox token. Upstox quote, history, and streaming features require valid credentials and the required API permissions.

## 3. Run

Run from the `AI_Trade_Intelligence` project folder:

```bash
python -m streamlit run app.py
```

## 4. Safety and data notes

- The application is intended for analysis and education. It does not place orders.
- Yahoo Finance data may be delayed, incomplete, or unavailable.
- Broker data availability depends on token validity, API permissions, instrument keys, and market hours.
- Signals are rule-based decision support, not guaranteed predictions or investment advice.
- The trade journal currently uses Streamlit session state; export it regularly. Durable database storage is a planned enhancement.

## 5. Current known limitations

- Live WebSocket behaviour must be validated against the installed Upstox SDK version and a valid token.
- Option-chain analytics currently depend on user-provided CSV input in relevant pages.
- FII/DII analysis depends on data supplied by the user where applicable.
- No automated order execution is implemented.


## V10 additions

See `README_V10.md` for the experimental machine-learning prediction and chronological backtesting page.


## V14 update
See `README_V14.md` for the Upstox live-feed monitor, local token setup, and validation notes.

## V17 addition

See `README_V17.md` for the Intraday Signal & Confluence Desk instructions and limitations.

## V28 · Advanced Options Intelligence

V28 adds `options_intelligence_v28.py` and a **V28 Options Intelligence** page. It analyzes the most recently fetched Upstox V15 option-chain snapshot and displays total Call/Put OI, PCR, ATM strike, largest Call/Put OI concentrations, net OI changes, simple available-strike IV averages, strike-wise OI activity and an estimated expiry intrinsic-payout curve (Max Pain calculation).

### Use
1. Configure a valid `UPSTOX_ACCESS_TOKEN` in `.streamlit/secrets.toml`.
2. Open **V15 Live Options Intelligence**, load expiries, select the required expiry and fetch the option chain.
3. Open **V28 Options Intelligence** to inspect the fetched snapshot. The page shows the source and fetch timestamp and does not fabricate data if no chain is loaded.

### Limitations
- V28 uses the last successful V15 Upstox snapshot; it is not a continuously streaming option-chain feed.
- PCR, OI walls, OI changes and Max Pain are descriptive positioning metrics, not directional forecasts or guaranteed support/resistance.
- IV averages are simple averages of available strike IV values, not ATM IV or an implied-volatility surface.
- No strategy execution, order placement, margin calculation or guaranteed trade signal is provided.

Run focused tests:

```bash
pytest -q test_options_intelligence_v28.py test_live_options_chain.py test_index_options_intelligence.py
```

## V29 — Advanced Options Strategy Generator

1. Start the app and open **V15 Live Options Intelligence**.
2. Load the Upstox expiry list and fetch an option chain.
3. Open **V29 Strategy Generator**. It reuses the last successfully fetched V15 snapshot.
4. Enter the applicable lot size manually (verify it against the current exchange/broker contract specification), choose a strategy and inspect its legs, expiry payoff and comparison table.

V29 builds Bull Call Spread, Bear Put Spread, Long Straddle, Long Strangle and Iron Condor structures where all required premiums are present. The strategy engine uses chain LTPs and actual listed strikes; it does not invent missing quotes. IV context is descriptive and uses the available leg IV values. Payoff is a simplified expiry-intrinsic calculation, not a live valuation or execution quote. The risk-budget helper is based on the displayed price range and is not a margin calculation. No orders are placed.

## V39 — Paper Execution Simulator

See `README_V39.md` for the V39 paper-order lifecycle, supported order types, configurable cost/slippage assumptions, position accounting, limitations and run instructions. V39 is local simulation only; it does not send orders to a broker.

## V40 update
See `README_V40.md` for the Advanced Backtesting Lab, chronological signal handling, out-of-sample metrics, strategy comparisons, CSV exports, and the new main Command Center shortcut to the existing Central AI Brain.

## V41 update
See `README_V41.md` for the V41 Performance Analytics page, dedicated Central AI Command Centre, and the separate AI Market & Option Chain Assistant dashboard.

## V42 – AI Trade Decision & Broker Hub
See `README_V42.md` for the new Scalping/Intraday/Hedging decision workspace, option-chain hedge candidate analysis, risk sizing, paper execution hand-off and Upstox read-only broker connectivity. Real-money broker order placement is disabled.

## V43 Live Market Intelligence
See `README_V43.md` for the read-only Upstox streaming monitor, historical OHLCV scanner, persistent threshold alerts and data-quality gates.

## Responsive website deployment
See `README_WEBSITE_DEPLOYMENT.md` for desktop/mobile styling, optional account login configuration, local run steps and hosting instructions.

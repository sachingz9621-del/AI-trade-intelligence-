# AI Trade Intelligence V8 — Trade Confirmation Engine

V8 adds a rule-based confluence module to the V7 dashboard. It combines the selected timeframe signal readings with EMA alignment, RSI momentum, relative volume, liquidity-sweep heuristics, recent fair-value-gap candidates and order-block candidates. It provides a transparent point score and an ATR-based reference stop/target/position-size calculator.

## Run

1. Extract the ZIP.
2. Open a terminal in `AI_Trade_Intelligence`.
3. Install dependencies: `python -m pip install -r requirements.txt`
4. Start: `python -m streamlit run app.py`

The new page is **AI Trade Confirmation Engine**. Choose one or more timeframes and click **Evaluate trade confluence**. The selected symbol comes from the sidebar.

## Test

`python -m pytest -q`

## Important limitations

- This is a transparent rule-based scoring model, not machine learning and not a calibrated probability.
- FVG and order-block labels are OHLCV heuristics; they do not prove institutional activity or exchange order-book liquidity.
- Data availability and delay depend on Yahoo Finance. Verify prices, timestamps, spreads and execution with your broker.
- ATR stop and target values are reference calculations, not guaranteed fills. Quantity is for cash-equity shares, not options/futures lots. Fees, taxes, slippage, gaps and leverage are excluded.
- No trades are placed and no broker credentials are required for this module.

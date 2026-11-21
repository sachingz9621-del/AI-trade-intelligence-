# V31 AI Trading Assistant

Run with `python -m streamlit run app.py`, then open **V31 AI Trading Assistant**.

V31 adds a conversational, session-aware assistant for indicator education, V30 trade-bias explanations, options workflow/context and risk-sizing concepts. It uses a local deterministic response engine and the data already loaded in the Streamlit session. It does not call an external LLM, independently fetch live prices, predict returns, or place orders.

For current bias, refresh **V30 Trade Confirmation** first. For PCR/OI/Max Pain context, fetch the expiry chain in **V15 Live Options Intelligence** first. Missing context is reported instead of fabricated.

Test: `pytest -q test_trading_assistant_v31.py test_trade_confirmation_v30.py test_options_strategy_v29.py test_options_intelligence_v28.py`

All responses are educational decision support, not personalized financial advice or a guarantee of outcomes.

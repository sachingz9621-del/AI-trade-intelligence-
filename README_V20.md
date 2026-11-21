# AI Trade Intelligence V20 — Multi-source News + Explainable Market Impact

V20 builds on V19 and adds a transparent headline-impact layer to the Multi-Source News & Forex Factory page.

## New in V20
- Tags headlines into market topics such as RBI/policy, inflation, Fed/rates, crude, gold, FX, SEBI/regulation, banks, China, geopolitics and corporate earnings.
- Shows potentially affected Indian/global assets and sectors, a cautious heuristic bias, match-strength confidence and a short rationale.
- Keeps the original source, publication time and article link visible.
- Includes tests for topic mapping, cautious fallback behaviour and dataframe integration.

## Important limitations
- The impact engine is keyword/rule-based and explainable. It is **not** a trained AI model, real-time market-impact predictor, or trading signal.
- A headline alone cannot establish whether an asset will rise or fall. Market reaction depends on expectations, details, positioning and live prices.
- News feeds and the Forex Factory public calendar are best-effort public endpoints. Availability and publisher feed terms can change. Check the publisher's original page.
- This software is for research/education. Verify all information and use broker-confirmed data before trading.

## Run on Windows
1. Extract the ZIP.
2. Open the extracted folder in VS Code.
3. In the VS Code terminal run:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Tests included

```powershell
python -m unittest test_news_intelligence_v19.py test_news_impact_engine_v20.py -v
python -m py_compile app.py news_intelligence_v19.py news_impact_engine_v20.py
```

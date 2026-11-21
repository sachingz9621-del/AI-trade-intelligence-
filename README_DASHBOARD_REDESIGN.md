# Dashboard Redesign — AI Trade Intelligence

This update introduces a redesigned **Command Center Dashboard** as the default landing page.

## Preservation guarantee
- Only `app.py` was edited for the dashboard redesign; the existing analysis engines, data modules, page implementations, tests, and requirements were retained.
- Existing sidebar modules remain available. The dashboard provides shortcut buttons to the main modules.
- No broker credentials or access tokens are included. Keep your existing `.streamlit/secrets.toml` locally; do not share it.

## Run
From this project folder:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Choose **Command Center Dashboard** in the sidebar. All prior modules remain accessible from the same navigation list.

## Dashboard features
- Market pulse cards for NIFTY 50, BANK NIFTY, SENSEX and S&P 500 (when data is available).
- Quick navigation to AI intelligence, Trading Terminal, Opportunity Scanner and Risk Planner.
- Selected-symbol price chart with EMA, RSI, MACD and volume panels.
- Multi-publisher latest-news table with V21 headline sentiment and priority labels.
- Expandable module directory grouped by workflow.

Market and news feeds are best-effort and may be delayed or unavailable. Headline scoring is rules-based decision support, not a guaranteed forecast or trade instruction.

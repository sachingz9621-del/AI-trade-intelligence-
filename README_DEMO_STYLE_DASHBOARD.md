# Demo-style dashboard redesign

This update reorganises the Command Center Dashboard to follow the uploaded Trading Assistant Demo's six-section navigation:

1. Brief
2. Option Chain
3. Chart
4. News
5. Ask
6. Learn

The dashboard uses existing platform data and modules. It does not copy the demo's generated sample market values. The Option Chain tab links to the existing option-chain/OI modules; the News tab uses the existing multi-publisher news aggregator; the Chart tab uses the selected symbol/history/interval controls; and Ask is a transparent rule-based explainer, not a claim of a connected LLM.

All other pages and engines are retained. No broker order execution was added. Keep your old project folder as a backup and copy your own `.streamlit/secrets.toml` into this project's `.streamlit` folder if you use Upstox.

Run:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

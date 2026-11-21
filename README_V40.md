# V40 — Advanced Backtesting Lab + Central AI Brain Command-Centre Shortcut

V40 is an additive update to the V39 project.

## Advanced Backtesting Lab
- Three transparent rule-based strategies: EMA crossover, RSI mean reversion and Donchian breakout.
- Chronological OHLCV simulation with completed-candle signals shifted forward before returns are applied.
- Configurable starting capital, estimated turnover cost, strategy parameters and long/short mode.
- Equity curve, buy-and-hold benchmark, drawdown, trade segments, win rate, profit factor and approximate Sharpe statistic.
- Chronological out-of-sample segment reporting and strategy comparison.
- CSV export for trade log and full equity curve.

## Central AI Brain shortcut
- Added a prominent one-click **Open Central AI Brain** button to the main Command Center Dashboard.
- Added Central AI Brain as the first tile in the dashboard Quick Access row.
- Shortcut opens the existing V35 Central AI Brain page; it does not duplicate or replace the Brain implementation.
- Uses the currently selected sidebar symbol and loaded chart history after navigation.

## Backtest assumptions and limitations
- Signals are formed using completed candle data and applied to the next candle's close-to-close return.
- Estimated costs are charged on changes in exposure. They are user-configurable assumptions, not a statutory tax/brokerage calculator.
- Intrabar order fills, gaps, spread, liquidity, partial fills, latency, market impact, margin, corporate actions and survivorship bias are not fully modelled.
- Out-of-sample results are historical validation, not a guarantee of future performance. Strategy comparison can still overfit if repeatedly tuned against the same history.
- No live broker orders are sent.

## Data and preservation
V40 preserves existing source modules and prior navigation pages. It adds `backtesting_lab_v40.py` and does not modify V34, V37, V38 or V39 runtime databases. Runtime databases are not bundled in the source ZIP; retain separate backups when moving installations.

## Run
`python -m pip install -r requirements.txt`
`python -m streamlit run app.py`

## Test
`pytest -q test_backtesting_lab_v40.py test_platform_ultimate_v37.py test_terminal_v38.py test_sim_execution_v39.py`

# V29 Advanced Options Strategy Generator

- Uses the most recently fetched V15 Upstox option-chain snapshot.
- Generates Bull Call Spread, Bear Put Spread, Long Straddle, Long Strangle and Iron Condor when all legs have positive LTPs.
- Shows selected legs, net premium, breakeven estimates, expiry payoff curve and strategy comparison CSV.
- User enters lot size; verify current contract specifications independently.
- IV context is descriptive, not a predictive strategy selector.
- LTP is not bid/ask. Payoff excludes fees, slippage, margin and early assignment/exercise effects. No order execution.

Run checks: `pytest -q test_options_strategy_v29.py test_options_intelligence_v28.py test_live_options_chain.py`

## V30 — Trade Confirmation & Execution Preparation
- Adds a unified review desk combining the existing V22 multi-timeframe OHLCV assessment, optional V28 option-chain statistics, and keyword-based high-priority news context.
- Adds a transparent confluence score, WAIT/manual-review gates, evidence and warnings, a manual pre-trade checklist, and an illustrative ATR-based cash-equity risk ticket.
- Refresh market evidence from the V30 page. The optional option-chain context uses the latest fetched V15 Upstox snapshot; fetch it from V15 first.
- Scores are heuristic context, not probabilities. OI/Max Pain are descriptive. The checklist is not automated broker validation. No orders are placed.

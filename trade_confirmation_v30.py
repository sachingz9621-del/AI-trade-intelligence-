"""V30 transparent trade-confirmation and review-ticket engine.
Combines existing OHLCV multi-timeframe assessment, descriptive option positioning,
and keyword-based news risk. Not a probability model or execution system.
"""
from __future__ import annotations
import pandas as pd
from signal_intelligence_v22 import assess_signal_quality
from options_intelligence_v28 import analyze_option_chain


def evaluate_v30(frames: dict[str, pd.DataFrame], news: pd.DataFrame | None = None,
                 option_chain: pd.DataFrame | None = None) -> dict:
    technical = assess_signal_quality(frames, news)
    bull = technical['bullish_count']
    bear = technical['bearish_count']
    score = 0
    evidence = []
    if technical['direction'].startswith('BULLISH'):
        score += 2; evidence.append('Multi-timeframe OHLCV bias leans bullish (+2)')
    elif technical['direction'].startswith('BEARISH'):
        score -= 2; evidence.append('Multi-timeframe OHLCV bias leans bearish (-2)')
    if technical['quality'] == 'STRONG ALIGNMENT':
        score += 1 if bull > bear else -1 if bear > bull else 0
        evidence.append('Strong alignment quality modifier applied')
    options = None
    if isinstance(option_chain, pd.DataFrame) and not option_chain.empty:
        try:
            options = analyze_option_chain(option_chain)
            # OI is deliberately a low-weight context clue, never a standalone directional trigger.
            if options['positioning'] == 'PUT OI HEAVIER':
                score += 1; evidence.append('Put OI heavier: mild contextual bullish lean (+1), not directional proof')
            elif options['positioning'] == 'CALL OI HEAVIER':
                score -= 1; evidence.append('Call OI heavier: mild contextual bearish lean (-1), not directional proof')
        except (ValueError, KeyError, TypeError):
            options = None
    high_news = technical['high_priority_news']
    news_risk = 'HIGH' if len(high_news) >= 3 else 'ELEVATED' if len(high_news) else 'NO HIGH-PRIORITY HEADLINES FLAGGED'
    # Headlines are treated as a risk gate, not a directional vote.
    warnings = list(technical['warnings'])
    if news_risk in ('HIGH', 'ELEVATED'):
        warnings.append(f'{news_risk} news-event context: review original headlines and timing before any trade.')
    if options is None:
        warnings.append('Options positioning unavailable: no valid V15/V28 chain snapshot supplied.')
    if technical['available_count'] < 2:
        warnings.append('Insufficient timeframe breadth: do not treat this as a confirmed setup.')
    if technical['direction'].startswith('BULLISH') and score >= 2:
        verdict = 'BULLISH REVIEW CANDIDATE'
    elif technical['direction'].startswith('BEARISH') and score <= -2:
        verdict = 'BEARISH REVIEW CANDIDATE'
    else:
        verdict = 'WAIT / NO CONFIRMED TRADE'
    if news_risk == 'HIGH' or technical['quality'] == 'LOW / INCOMPLETE':
        verdict = 'WAIT / MANUAL REVIEW REQUIRED'
    return {'verdict': verdict, 'confluence_score': score, 'technical': technical,
            'options': options, 'news_risk': news_risk, 'evidence': evidence,
            'warnings': list(dict.fromkeys(warnings)),
            'review_checklist': [
                'Verify the latest broker quote and candle timestamps.',
                'Check bid/ask spread, liquidity, lot size and available margin.',
                'Read original news and check scheduled event timing.',
                'Confirm option expiry, contract multiplier and all strategy legs.',
                'Set a predefined invalidation level and risk budget.',
                'Review brokerage, taxes, slippage and overnight/gap risk.'
            ],
            'disclaimer': 'Rule-based decision support only. Scores are not probabilities, forecasts or recommendations. No order is placed.'}

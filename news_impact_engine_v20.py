"""Explainable, keyword-based market impact tagging for V20 news headlines.

This is a transparent heuristic, not a trained AI model or a trading signal.
"""
from __future__ import annotations
import re
import pandas as pd

RULES = [
    {"topic":"RBI / Indian monetary policy", "terms":["reserve bank of india", "rbi", "repo rate", "monetary policy", "liquidity", "cash reserve ratio", "crr", "slr"], "assets":"NIFTY Bank, NIFTY Financial Services, INR, government bonds", "bias":"Depends on policy surprise", "why":"Rate and liquidity changes can affect bank margins, credit demand, bond yields and the rupee."},
    {"topic":"Inflation / prices", "terms":["inflation", "cpi", "consumer price", "wpi", "wholesale price", "price pressure"], "assets":"NIFTY, rate-sensitive stocks, INR, bond yields", "bias":"Higher-than-expected inflation may pressure risk assets", "why":"Inflation surprises can change expectations for interest rates and purchasing power."},
    {"topic":"US Federal Reserve / rates", "terms":["federal reserve", "fed rate", "fomc", "interest rate", "rate cut", "rate hike", "treasury yield"], "assets":"USD/INR, global equities, IT exporters, gold, bond yields", "bias":"Depends on rate surprise and guidance", "why":"US rates influence global liquidity, dollar strength and valuation discount rates."},
    {"topic":"Crude oil / energy", "terms":["crude oil", "brent", "wti", "opec", "oil prices", "petroleum"], "assets":"ONGC, Oil India, OMCs, aviation, paints, tyres, USD/INR", "bias":"Higher crude can pressure oil importers; producers may benefit", "why":"India imports substantial crude; price changes can affect inflation, margins and the current account."},
    {"topic":"Gold / precious metals", "terms":["gold", "bullion", "silver", "precious metal"], "assets":"Gold, silver, MCX-linked names, jewellery stocks, USD", "bias":"Depends on real yields, USD and risk demand", "why":"Precious metals respond to real rates, currency moves and safe-haven demand."},
    {"topic":"INR / foreign exchange", "terms":["rupee", "inr", "usd/inr", "currency", "forex", "dollar"], "assets":"USD/INR, importers, IT exporters, oil marketing companies", "bias":"Rupee weakness can help exporters but raise import costs", "why":"Currency moves redistribute costs and revenues across importers and exporters."},
    {"topic":"SEBI / regulation", "terms":["sebi", "regulator", "regulation", "circular", "derivatives", "f&o", "futures and options"], "assets":"Brokerages, exchanges, derivatives-active stocks", "bias":"Policy-specific; assess affected business model", "why":"Regulatory changes may alter market access, costs, leverage or trading activity."},
    {"topic":"Banks / financial sector", "terms":["bank", "banks", "lender", "loan", "credit growth", "npas", "bad loan"], "assets":"NIFTY Bank, private banks, PSU banks, NBFCs", "bias":"Depends on asset quality, growth and funding costs", "why":"Credit growth, deposit costs and asset quality influence financial-sector earnings."},
    {"topic":"China / global demand", "terms":["china", "beijing", "chinese economy", "stimulus", "manufacturing pmi"], "assets":"Metals, commodities, chemicals, autos, global cyclicals", "bias":"Stronger demand may support cyclicals; weak data may weigh", "why":"China's demand and policy can affect commodity prices and global supply chains."},
    {"topic":"Geopolitical / risk event", "terms":["war", "sanctions", "attack", "conflict", "ceasefire", "geopolitical", "missile", "shipping disruption"], "assets":"Crude oil, gold, defence, shipping, global risk assets", "bias":"Risk-off potential; direction is event-dependent", "why":"Escalation or disruption can raise volatility, safe-haven demand and commodity risk premiums."},
    {"topic":"Corporate earnings / guidance", "terms":["earnings", "results", "quarterly profit", "revenue", "guidance", "profit warning", "dividend"], "assets":"Named company and its sector peers", "bias":"Company-specific; compare results with expectations", "why":"Earnings and guidance can change expectations for cash flows and valuation."},
]

POSITIVE = ["beats estimates", "profit rises", "upgrade", "record profit", "strong demand", "raises guidance", "rate cut"]
NEGATIVE = ["misses estimates", "profit falls", "downgrade", "loss widens", "weak demand", "cuts guidance", "rate hike"]


def analyze_headline(headline: str) -> dict:
    text = re.sub(r"\s+", " ", str(headline or "")).strip()
    low = text.lower()
    matches = []
    for rule in RULES:
        found = [term for term in rule["terms"] if re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", low)]
        if found:
            matches.append((rule, found))
    if not matches:
        return {"Impact Topic":"General / unclassified", "Potentially Affected Assets":"Needs manual review", "Heuristic Bias":"Not assessed", "Confidence":"Low", "Rationale":"No configured topic keywords matched. Read the original article before drawing conclusions."}
    rule, found = matches[0]
    sentiment = "Mixed / unclear"
    pos = any(term in low for term in POSITIVE)
    neg = any(term in low for term in NEGATIVE)
    if pos and not neg: sentiment = "Positive wording detected"
    elif neg and not pos: sentiment = "Negative wording detected"
    confidence = "Medium" if len(found) >= 2 else "Low"
    if len(matches) > 1: confidence = "Medium"
    rationale = rule["why"] + " Matched: " + ", ".join(found[:4]) + "."
    if sentiment != "Mixed / unclear":
        rationale += " Headline wording: " + sentiment.lower() + "; this does not establish the market's actual reaction."
    return {"Impact Topic":rule["topic"], "Potentially Affected Assets":rule["assets"], "Heuristic Bias":rule["bias"] + " | " + sentiment, "Confidence":confidence, "Rationale":rationale}


def analyze_news_frame(news: pd.DataFrame) -> pd.DataFrame:
    if news is None or news.empty:
        return pd.DataFrame()
    out = news.copy()
    tags = out["Headline"].apply(analyze_headline).apply(pd.Series)
    return pd.concat([out.reset_index(drop=True), tags.reset_index(drop=True)], axis=1)

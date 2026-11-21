# AI Trade Intelligence — V21 Advanced Market Intelligence

V21 builds on V20 and keeps the existing trading pages and multi-source news feeds.

## What's new

- **Headline sentiment:** Positive, negative or neutral/unclear wording classification using a transparent phrase dictionary.
- **News priority:** 0–100 attention score based on matched risk terms, source weighting and publication freshness. It is a sorting aid, not a probability of market movement.
- **Sector intelligence:** Keyword-based mapping to Banking, IT, Pharma, Auto, FMCG, Energy and Metals.
- **Breaking headline comparison:** Highlights newly seen high-priority article links between manual refreshes in the current browser session.
- **Cross-asset snapshot:** Optional daily observations for NIFTY, BANK NIFTY, S&P 500, NASDAQ, Nikkei, Hang Seng, crude, gold and USD/INR.
- **Correlation matrix:** Optional correlation of daily percentage returns for the selected lookback.

## Data-source approach

News continues to come from the independent India and international RSS/XML publishers and official policy feeds in V19/V20, plus Forex Factory's public economic calendar and its separately linked curated News page. **Yahoo Finance is used only for the optional cross-asset price snapshot/correlation panel**, not as the sole news source. Cross-asset prices may be delayed, incomplete or unavailable.

## Run on Windows

1. Extract the ZIP file.
2. Open the extracted project folder in VS Code.
3. Open Terminal → New Terminal.
4. Run:

   ```bash
   python -m pip install -r requirements.txt
   python -m streamlit run app.py
   ```

5. In the left navigation, select **V21 Advanced Market Intelligence**.
6. Press **Refresh V21 intelligence** to refresh the publisher headlines. Press **Load cross-asset prices** or **Calculate correlation matrix** only when you want those optional panels.

Your existing Upstox token setup remains separate and is not changed by V21.

## Important limitations

- Sentiment, priority and sector labels are rules-based headline analysis, not a trained language model or calibrated forecast.
- Headlines are not the full article; sarcasm, context, expectations and market reaction may differ.
- New-high-priority detection compares manual refreshes in the current browser session; it is not a background push-notification service.
- Yahoo Finance cross-asset observations are a secondary data source and are not guaranteed real-time.
- No trades or broker orders are placed by this module.

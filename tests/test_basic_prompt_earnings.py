#!/usr/bin/env python3
"""Quick test: Verify earnings appear in basic prompt"""

from src.data import DataManager
from src.llm.prompts import PromptTemplate

dm = DataManager()

# Get earnings
earnings = dm.get_earnings_for_symbol('JCI', use_cache=True)
print("✓ Fetched earnings for JCI")

# Format earnings
earnings_summary = PromptTemplate.format_earnings_for_prompt(earnings)
print("\nFormatted earnings:")
print(earnings_summary)

# Get news
news_data = dm.get_news(['JCI'], lookback_days=5, use_cache=True)
news_articles = news_data.get('JCI', [])
news_summary = PromptTemplate.format_news_for_prompt(news_articles, max_articles=5)

# Generate basic prompt WITH earnings
prompt = PromptTemplate.basic_prompt(
    symbol='JCI',
    news_summary=news_summary,
    momentum_return=0.4114,
    earnings_summary=earnings_summary,
    forecast_days=21
)

print("\n" + "="*70)
print("BASIC PROMPT WITH EARNINGS")
print("="*70)
print(prompt)
print("="*70)

# Check if earnings are included
if "📊 LATEST EARNINGS" in prompt:
    print("\n✅ SUCCESS: Earnings data IS included in basic prompt!")
else:
    print("\n❌ FAIL: Earnings data NOT found in prompt")

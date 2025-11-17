#!/usr/bin/env python3
"""Verify earnings appear in LLM prompts for top holdings"""

from src.data import DataManager
from src.llm import LLMScorer
from src.llm.prompts import PromptTemplate

dm = DataManager()
scorer = LLMScorer()  # Uses basic prompt from config

# Test with one of the top holdings from the recent portfolio
test_symbol = 'IDXX'  # Top holding

print(f"Testing {test_symbol}...")
print("="*70)

# Get data
earnings = dm.get_earnings_for_symbol(test_symbol, use_cache=True)
news_data = dm.get_news([test_symbol], lookback_days=5, use_cache=True)
news_articles = news_data.get(test_symbol, [])
news_summary = PromptTemplate.format_news_for_prompt(news_articles, max_articles=5)

# Score with earnings (and get prompt)
result = scorer.score_stock(
    symbol=test_symbol,
    news_summary=news_summary,
    momentum_return=0.32,
    earnings_data=earnings,
    return_prompt=True
)

if result and len(result) == 3:
    raw_score, normalized_score, prompt = result

    print(f"✅ Score: {normalized_score:.3f}")
    print("\n" + "="*70)
    print("PROMPT PREVIEW:")
    print("="*70)

    # Show first 1500 chars of prompt
    print(prompt[:1500])
    print("\n... [truncated]\n")

    # Check for earnings
    if "📊 LATEST EARNINGS" in prompt:
        print("✅ EARNINGS DATA IS INCLUDED IN PROMPT")

        # Extract and show earnings section
        earnings_start = prompt.find("📊 LATEST EARNINGS")
        earnings_end = prompt.find("\nRecent News:", earnings_start)
        if earnings_end > earnings_start:
            print("\nEarnings section:")
            print("="*70)
            print(prompt[earnings_start:earnings_end])
            print("="*70)
    else:
        print("❌ EARNINGS DATA NOT FOUND IN PROMPT")
else:
    print("❌ Failed to get prompt")

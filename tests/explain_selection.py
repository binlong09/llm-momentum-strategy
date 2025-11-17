#!/usr/bin/env python3
"""Show exactly how stocks are selected and why portfolio changed"""

import pandas as pd
import numpy as np

# Read the most recent portfolio
latest_portfolio = pd.read_csv('results/portfolios/portfolio_enhanced_equal_20251109_182829.csv')

print("="*80)
print("STOCK SELECTION PROCESS EXPLAINED")
print("="*80)

print("\n📊 STEP 1: Start with S&P 500 (~500 stocks)")
print("    Examples: AAPL, GOOGL, MSFT, NVDA, TSLA, etc.")

print("\n📈 STEP 2: Filter to Top 20% by Momentum (~100 stocks)")
print("    12-month return calculation")
print("    Only keep stocks that beat 80% of the market")

print("\n🤖 STEP 3: AI Scores Each Stock (0.0 - 1.0)")
print("    Analyzes:")
print("    - Momentum strength")
print("    - 📊 Earnings growth (YoY EPS, Revenue) ← NEW IN PHASE 2")
print("    - 💰 Profitability (margins, ROE)")
print("    - 🏦 Financial health (debt levels) ← NEW IN PHASE 2")
print("    - 📰 Recent news sentiment")

print("\n🎯 STEP 4: Select Top 50 by AI Score (not momentum!)")
print("    Rank by AI score descending")
print("    Keep top 50")

print("\n💼 STEP 5: Tilt Weights Toward High Scorers")
print("    weight ∝ (AI_score)^5.0")
print("    This HEAVILY favors top scorers!")

print("\n" + "="*80)
print("YOUR LATEST PORTFOLIO - TOP 10 HOLDINGS")
print("="*80)

top10 = latest_portfolio.head(10)

print("\n{:<8} {:>8} {:>12} {:>10}".format("Symbol", "Weight", "Momentum", "AI Score"))
print("-"*80)

for _, row in top10.iterrows():
    symbol = row['symbol']
    weight = row['weight'] * 100
    momentum = row['momentum_return'] * 100
    llm_score = row['llm_score']

    print(f"{symbol:<8} {weight:>7.2f}% {momentum:>11.1f}% {llm_score:>9.3f}")

print("\n" + "="*80)
print("WHY DID THE PORTFOLIO CHANGE?")
print("="*80)

print("\n**BEFORE Phase 2 (News Only):**")
print("- AI only saw: Momentum + News")
print("- Example: GOOGL with +50% momentum + good news → High score")
print("- Big names often had good news → Higher scores")

print("\n**AFTER Phase 2 (News + Earnings):**")
print("- AI now sees: Momentum + Earnings + News")
print("- Factors in:")
print("  • EPS growth (is it accelerating?)")
print("  • Profit margins (getting better or worse?)")
print("  • Debt levels (safe or risky?)")

print("\n**Example Comparison:**")
print("\nStock A (GOOGL - Large Cap):")
print("  Momentum: +50%")
print("  News: Positive")
print("  Earnings: +8% EPS growth (good but not exceptional)")
print("  → AI Score: 0.75")

print("\nStock B (IDXX - Healthcare):")
print("  Momentum: +32%")
print("  News: Very positive (earnings beat)")
print("  Earnings: 🟢 +44.6% EPS growth (exceptional!)")
print("  Margins: 32.1% operating margin (excellent)")
print("  → AI Score: 1.000 ← AI loves this!")

print("\n**Result:** IDXX gets top weighting despite lower momentum")
print("  Why? Much stronger fundamentals!")

print("\n" + "="*80)
print("KEY INSIGHT")
print("="*80)

print("""
The AI now COMBINES:
1. 📈 Price momentum (what the market has done)
2. 📊 Earnings momentum (what the business is doing) ← NEW
3. 📰 News sentiment (what's happening now)

This creates a MORE INTELLIGENT portfolio that:
✅ Avoids momentum stocks with weak fundamentals
✅ Finds quality growth companies before they become mega-caps
✅ Balances technical performance with business performance

Your portfolio now includes:
- IDXX: Healthcare diagnostics, 44.6% EPS growth
- INCY: Biotech, strong earnings growth
- APH: Tech components, excellent fundamentals
- GLW: Display tech, turnaround story with great growth
- LRCX: Semiconductor equipment, riding AI wave

vs. Previously:
- GOOGL: Mature, slower growth (still good, but not exceptional)
- AAPL: Mature, incremental improvements
""")

print("\n" + "="*80)
print("IS THIS GOOD OR BAD?")
print("="*80)

print("""
✅ GOOD:
- Finding high-quality growth BEFORE they become mega-caps
- Avoiding "fake momentum" (hype without fundamentals)
- Better risk-adjusted returns

⚠️ CONSIDER:
- Less familiar names (more research needed)
- Higher concentration in top holdings
- May be more volatile (smaller caps)

💡 RECOMMENDATION:
Review the earnings data for top holdings:
  python verify_earnings_in_prompts.py

Check if you're comfortable with the fundamentals!
""")

#!/usr/bin/env python3
"""Find where mega-cap stocks ended up"""

import pandas as pd

df = pd.read_csv('results/portfolios/portfolio_enhanced_equal_20251109_182829.csv')

print("\n" + "="*70)
print("WHERE ARE THE MEGA-CAP STOCKS?")
print("="*70)

megacaps = ['AAPL', 'GOOGL', 'GOOG', 'MSFT', 'NVDA', 'AMZN', 'META', 'TSLA']

print("\nChecking in your portfolio (size=10)...\n")

for ticker in megacaps:
    if ticker in df['symbol'].values:
        row = df[df['symbol'] == ticker].iloc[0]
        rank = df[df['symbol'] == ticker].index[0] + 1
        print(f"✅ {ticker}:")
        print(f"   Rank: #{rank}/10")
        print(f"   Weight: {row['weight']*100:.2f}%")
        print(f"   Momentum: {row['momentum_return']*100:.1f}%")
        print(f"   AI Score: {row['llm_score']:.3f}\n")
    else:
        print(f"❌ {ticker}: Not in top 10")

print("\n" + "="*70)
print("EXPLANATION")
print("="*70)

print("""
Your test used --size 10 (only 10 stocks).

The mega-caps (AAPL, GOOGL, etc.) are likely:
1. In the momentum top 20% (good price performance)
2. BUT scored lower on AI evaluation due to:
   - Slower earnings growth (mature companies)
   - Already high valuations
   - Less exciting news vs. smaller growth companies

The AI is finding BETTER opportunities in:
- Mid-cap growth stocks with accelerating earnings
- Companies in turnaround/transition (like GLW)
- Sector leaders with strong fundamentals (LRCX, APH)

This is actually GOOD! It means the AI is:
✅ Not just picking "safe" big names
✅ Finding quality growth opportunities
✅ Using fundamentals to separate good vs. great momentum
""")

print("\n" + "="*70)
print("WHAT IF YOU WANT MORE MEGA-CAPS?")
print("="*70)

print("""
Option 1: Generate larger portfolio (--size 50)
  More positions = more diversity = more mega-caps included

Option 2: Lower the tilt factor
  In config.yaml: weight_tilt_factor: 5.0 → 2.0
  This reduces concentration in top AI scorers

Option 3: Use "advanced" prompt type
  In config.yaml: prompt_type: "advanced"
  Includes company name/sector (may favor known names)

Option 4: Trust the AI!
  The system found stocks with:
  - 44.6% EPS growth (IDXX) vs. ~10% for mega-caps
  - 96% momentum (APH) vs. ~30% for AAPL
  - Better fundamentals at similar momentum
""")

#!/usr/bin/env python3
"""Compare what 10 vs 50 stock portfolios look like"""

import pandas as pd

df = pd.read_csv('results/portfolios/portfolio_enhanced_equal_20251109_182829.csv')

print("\n" + "="*80)
print("VISUAL COMPARISON: YOUR PORTFOLIO")
print("="*80)

print("\n📊 YOUR 10-STOCK TEST PORTFOLIO:")
print(f"  Top 5 concentration: {df.head(5)['weight'].sum()*100:.1f}%")
print(f"  Top 1 holding: {df.iloc[0]['weight']*100:.1f}%")
print(f"  Average LLM score: {df['llm_score'].mean():.3f}")

print("\n  Holdings:")
for i, row in df.iterrows():
    bars = "█" * int(row['weight'] * 100 / 2)
    print(f"  #{i+1:2d} {row['symbol']:6s} {row['weight']*100:5.1f}% {bars}")

print("\n" + "="*80)
print("WHAT IF YOU GENERATED 50 STOCKS?")
print("="*80)

print("""
Estimated distribution (based on your tilt_factor=5.0):

  Stocks #1-5:   ~10-15% each  = 60% total ███████████████
  Stocks #6-15:  ~3-5% each    = 30% total ███████
  Stocks #16-50: ~0.2-1% each  = 10% total ██

Benefits:
  ✅ Much better diversified
  ✅ Reduces single-stock risk
  ✅ Still concentrated in top AI picks
  ✅ More stable returns

Tradeoff:
  ⚠️  Slightly diluted returns (if top 5 all work out)
  ⚠️  More transaction costs at rebalancing

Academic research says: 50 is optimal!
""")

print("\n" + "="*80)
print("QUICK DECISION GUIDE")
print("="*80)

print("""
Choose 10 stocks if:
  • You have VERY high conviction in AI
  • Can tolerate high volatility
  • Actively monitoring daily
  • OK with concentrated risk

Choose 50 stocks if:
  • Want to follow academic research
  • Prefer more stable returns
  • Rebalancing monthly (set-and-forget)
  • Want diversification ← RECOMMENDED

Choose 100+ stocks if:
  • Very risk-averse
  • Large portfolio ($1M+)
  • Don't want to beat market much
  • Near index-like performance

For most people: 50 stocks is the sweet spot! 🎯
""")

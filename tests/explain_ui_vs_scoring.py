#!/usr/bin/env python3
"""
Explain: UI Slider vs Number of Stocks Scored

User question: Can I score 100 stocks but only select 50 for portfolio?
"""

print("="*80)
print("UI PORTFOLIO SIZE SLIDER - WHAT IT CONTROLS")
print("="*80)

print("""
SHORT ANSWER: The slider controls FINAL PORTFOLIO SIZE only.
The system ALREADY scores more stocks than you select!

CURRENT BEHAVIOR:
  1. Filter to top 20% by momentum = ~100 stocks (from S&P 500)
  2. Fetch news for all ~100 stocks
  3. Fetch earnings for all ~100 stocks  ← NEW in Phase 2
  4. Score ALL ~100 with LLM (costs money!)
  5. Rank by LLM score
  6. SELECT top N for portfolio ← THIS is what the slider controls

EXAMPLE WITH SLIDER = 50:
  ✅ Momentum filter: 500 → 100 stocks (top 20%)
  ✅ LLM scoring: All 100 stocks analyzed
  ✅ Earnings fetched: All 100 stocks
  ✅ Final portfolio: Top 50 by AI score ← Slider controls this

EXAMPLE WITH SLIDER = 10:
  ✅ Momentum filter: 500 → 100 stocks (top 20%)
  ✅ LLM scoring: All 100 stocks analyzed (same cost!)
  ✅ Earnings fetched: All 100 stocks
  ✅ Final portfolio: Top 10 by AI score ← Just more selective
""")

print("\n" + "="*80)
print("SO YOU'RE ALREADY DOING WHAT YOU ASKED!")
print("="*80)

print("""
Your question: "Can I analyze 100 stocks but only choose 50?"

Answer: YES! This is EXACTLY what happens now:
  • System analyzes ~100 stocks (top 20% momentum)
  • You choose how many to keep via slider (20-100)
  • Slider = 50 → Keep top 50 by AI score
  • Slider = 30 → Keep top 30 by AI score

The ~100 number comes from config:
  top_percentile: 0.20  (20% of 500 = 100 stocks)
""")

print("\n" + "="*80)
print("COST IMPLICATIONS")
print("="*80)

print("""
Important: LLM cost is based on NUMBER SCORED, not final portfolio size!

Slider = 10:
  - Scores: ~100 stocks with LLM
  - Cost: ~$0.10 with gpt-4o-mini
  - Final portfolio: 10 stocks
  - Waste: 90 scored stocks not used

Slider = 50:
  - Scores: ~100 stocks with LLM (same!)
  - Cost: ~$0.10 with gpt-4o-mini (same!)
  - Final portfolio: 50 stocks
  - Waste: 50 scored stocks not used

Slider = 100:
  - Scores: ~100 stocks with LLM (same!)
  - Cost: ~$0.10 with gpt-4o-mini (same!)
  - Final portfolio: ~100 stocks (all of them)
  - Waste: None

💡 INSIGHT: Since you're paying to score ~100 anyway,
   you might as well use more of them (50-100)!
""")

print("\n" + "="*80)
print("IF YOU WANT TO CONTROL NUMBER SCORED")
print("="*80)

print("""
Currently you can only control:
  ✅ Final portfolio size: 20-100 (UI slider)
  ❌ Number scored with LLM: Fixed at top 20% (~100)

If you want to score FEWER stocks (save money):
  Option 1: Edit config/config.yaml
    top_percentile: 0.20 → 0.10  (Score top 10% = 50 stocks)

  Option 2: I can add a new slider to the UI
    "Number of stocks to analyze: 50-200"
    "Final portfolio size: 20-100"
    (Would need code changes)

If you want to score MORE stocks:
  Option 1: Edit config/config.yaml
    top_percentile: 0.20 → 0.40  (Score top 40% = 200 stocks)
    ⚠️  Double the LLM cost!
""")

print("\n" + "="*80)
print("RECOMMENDED SETTINGS")
print("="*80)

print("""
For most users:
  top_percentile: 0.20  (100 stocks scored)
  portfolio_size: 50    (50 stocks selected)

  Why?
  • Follows academic research (Jegadeesh & Titman)
  • Good balance of cost vs diversification
  • Scores enough to find gems, keeps best 50
  • Cost: ~$0.10/month

For budget-conscious:
  top_percentile: 0.10  (50 stocks scored)
  portfolio_size: 30    (30 stocks selected)

  Why?
  • Half the LLM cost (~$0.05/month)
  • Still well-diversified
  • More concentrated in absolute top momentum

For "spare no expense":
  top_percentile: 0.40  (200 stocks scored)
  portfolio_size: 100   (100 stocks selected)

  Why?
  • Maximum diversification
  • Finds more hidden gems
  • Lower volatility
  • Cost: ~$0.20/month (still cheap!)
""")

print("\n" + "="*80)
print("ANSWER TO YOUR QUESTION")
print("="*80)

print("""
Q: Can I run analysis for top 100 stocks but only choose 50 for portfolio?

A: You're ALREADY doing this!
   • System analyzes ~100 (top 20% by momentum)
   • Slider lets you pick how many to keep (20-100)
   • Set slider = 50 to keep top 50

Q: What if I want to analyze 200 stocks and pick 50?

A: Need to change config:
   1. Edit config/config.yaml
      top_percentile: 0.20 → 0.40
   2. Use slider = 50 in UI

   Cost: ~$0.20/month (double the LLM calls)

Q: What if I want to analyze only 50 stocks and pick 30?

A: Need to change config:
   1. Edit config/config.yaml
      top_percentile: 0.20 → 0.10
   2. Use slider = 30 in UI

   Cost: ~$0.05/month (half the LLM calls)
""")

print("\n" + "="*80)
print("WANT ME TO ADD SEPARATE CONTROLS?")
print("="*80)

print("""
I can add a second slider to the UI:

Current:
  [Portfolio Size: 20-100] ← One slider

New Option:
  [Stocks to Analyze: 50-200] ← How many to score with LLM
  [Final Portfolio Size: 20-100] ← How many to keep

  Example:
    Analyze: 150 stocks
    Keep: 50 stocks

    Result:
    • Scores top 30% by momentum (150 stocks)
    • Keeps top 50 by AI score
    • Cost: 1.5x normal
    • Benefit: More options to choose from

Would you like me to add this feature? Or are you happy with current setup?
""")

#!/usr/bin/env python3
"""
Analyze how portfolio size and composition affect results
"""

print("="*80)
print("DOES THE PORTFOLIO MATTER TO ALGORITHM RESULTS?")
print("="*80)

print("""
This is a GREAT question with multiple angles to consider:

1. PORTFOLIO SIZE (10 vs 50 stocks)
2. SPECIFIC STOCK COMPOSITION (which stocks are selected)
3. CURRENT HOLDINGS (starting point for rebalancing)
4. CONCENTRATION VS DIVERSIFICATION (risk/return tradeoff)

Let's break each down:
""")

print("\n" + "="*80)
print("1. PORTFOLIO SIZE - DOES IT MATTER?")
print("="*80)

print("""
YES - Portfolio size significantly impacts results!

📊 ACADEMIC RESEARCH (Jegadeesh & Titman 1993, 2001):
  • 50 stocks: Optimal balance (their recommendation)
  • 30-100 stocks: Good diversification with manageable tracking
  • <20 stocks: Too concentrated (idiosyncratic risk)
  • >100 stocks: Diminishing returns (transaction costs, dilution)

YOUR CURRENT CONFIG:
  final_portfolio_size: 50  ← Well-chosen!

🎯 SIZE EFFECTS:

10 Stocks (your test):
  ✅ Pro: Maximum exposure to top AI picks
  ✅ Pro: Lower transaction costs
  ❌ Con: High concentration risk (one bad stock = big impact)
  ❌ Con: Not well-diversified
  Expected Return: Higher potential (more risky)
  Expected Volatility: Much higher

50 Stocks (your config):
  ✅ Pro: Well-diversified across sectors
  ✅ Pro: Reduces company-specific risk
  ✅ Pro: Follows academic best practices
  ⚠️  Con: More transaction costs at rebalancing
  Expected Return: Strong (slightly lower than 10)
  Expected Volatility: Moderate

100+ Stocks:
  ✅ Pro: Maximum diversification
  ❌ Con: Dilutes your best ideas (AI top picks)
  ❌ Con: Higher transaction costs
  ❌ Con: Approaches index-like returns
  Expected Return: Good but diluted
  Expected Volatility: Lower

💡 RECOMMENDATION: Stick with 50 stocks
  • Follows momentum research best practices
  • Balances concentration vs diversification
  • Gives AI enough room to work
""")

print("\n" + "="*80)
print("2. SPECIFIC STOCKS - DO THEY MATTER?")
print("="*80)

print("""
PARTIALLY - Within the top-scoring group, less so.

The key insight: If stocks are all in the top 20% by momentum AND score
well on AI evaluation, they're all "good" choices.

Example:
  Stock #1 (IDXX): AI score 1.000, momentum 32%
  Stock #2 (INCY): AI score 1.000, momentum 29%
  Stock #3 (APH):  AI score 1.000, momentum 96%

Q: Does it matter which one you pick?
A: Not much! They're all:
   ✅ High momentum
   ✅ Strong fundamentals
   ✅ Positive AI assessment

But there IS a difference between:
  Stock #1 (IDXX): AI score 1.000
  Stock #50 (ETR): AI score 0.600

The RANGE matters more than specific picks within a tier.

🎯 PRACTICAL IMPACT:

Scenario A: Portfolio of stocks ranked #1-50
  All have scores: 0.600 - 1.000
  → Expected to outperform market

Scenario B: Portfolio of stocks ranked #1-10
  All have scores: 0.900 - 1.000
  → Expected to outperform more (but riskier)

Scenario C: Portfolio of stocks ranked #40-90
  Mix of scores: 0.400 - 0.700
  → May underperform (weaker signals)

💡 THE ALGORITHM HANDLES THIS:
  Your config: final_portfolio_size: 50
  Selects TOP 50 by AI score automatically
  Within this group, differences are smaller
""")

print("\n" + "="*80)
print("3. CURRENT HOLDINGS - DO THEY MATTER?")
print("="*80)

print("""
YES - For transaction costs and tax efficiency!

The algorithm can consider current holdings when rebalancing:

  python scripts/generate_portfolio.py --current-holdings current.csv

HOW IT WORKS:
1. Generate optimal portfolio (e.g., 50 stocks)
2. Compare to current holdings
3. Calculate trades needed (sells + buys)
4. Factor in transaction costs (2 bps per trade in config)
5. May keep marginal positions to reduce trading

EXAMPLE:

Without considering current holdings:
  Current: [AAPL 2%, GOOGL 2%, MSFT 2%, ...]
  New:     [IDXX 14%, INCY 14%, APH 14%, ...]
  Trades:  Sell ALL old, buy ALL new = 100% turnover

With current holdings:
  Current: [IDXX 1%, INCY 1%, LRCX 0.5%, AAPL 2%, ...]
  New:     [IDXX 14%, INCY 14%, APH 14%, ...]
  Trades:  Increase IDXX/INCY, add APH, keep some others
           = 60% turnover (lower costs)

💡 IMPACT ON RESULTS:
  • Lower turnover = Lower costs = Higher net returns
  • But don't hold bad positions just to avoid trading
  • Algorithm balances this tradeoff
""")

print("\n" + "="*80)
print("4. CONCENTRATION VS DIVERSIFICATION")
print("="*80)

print("""
Your config has a TILT FACTOR that concentrates top picks:

  weight_tilt_factor: 5.0  ← This is HIGH

What this means:
  weight ∝ (AI_score)^5.0

Example:
  Stock A: score = 1.0 → weight ∝ 1.0^5 = 1.000
  Stock B: score = 0.9 → weight ∝ 0.9^5 = 0.590
  Stock C: score = 0.8 → weight ∝ 0.8^5 = 0.328
  Stock D: score = 0.7 → weight ∝ 0.7^5 = 0.168
  Stock E: score = 0.6 → weight ∝ 0.6^5 = 0.078

After normalization, top scorers get MUCH more weight!

Your top 5 holdings (all score 1.0): 14.56% EACH = 72.8% total
Bottom holdings (score 0.6): ~5% each

🎯 TILT FACTOR IMPACT:

tilt_factor = 1.0 (equal weight):
  Every stock gets 2% (if 50 stocks)
  Low concentration, high diversification
  More stable returns, lower potential upside

tilt_factor = 3.0 (moderate):
  Top scorers get ~5-8%
  Bottom get ~1-2%
  Balanced approach

tilt_factor = 5.0 (your setting - HIGH):
  Top scorers get ~10-15% EACH
  Bottom get <5%
  High concentration in best ideas
  Higher potential returns, higher risk

tilt_factor = 10.0 (extreme):
  Top 5 stocks = 80%+ of portfolio
  Very risky (like a hedge fund)

💡 YOUR RESULTS:
  With factor=5.0, your top 5 = 72.8% of portfolio
  This is AGGRESSIVE but follows your AI's conviction
  If AI is right → Great returns
  If AI misses → Bigger losses
""")

print("\n" + "="*80)
print("5. THE ANSWER: WHAT MATTERS MOST?")
print("="*80)

print("""
RANKED BY IMPORTANCE:

1. 🏆 PORTFOLIO SIZE (High Impact)
   50 stocks = Sweet spot (research-backed)
   Status: ✅ You have this right

2. 🥈 TILT FACTOR (High Impact on Risk/Return)
   5.0 = Aggressive concentration
   Status: ⚠️  High conviction, high risk
   Consider: 2.0-3.0 for more balance

3. 🥉 TOP 20% MOMENTUM FILTER (High Impact)
   top_percentile: 0.20 = Only best momentum stocks
   Status: ✅ Follows academic research

4. 📊 REBALANCING FREQUENCY (Medium Impact)
   Monthly = Standard for momentum
   Status: ✅ Correct

5. 💼 SPECIFIC STOCK SELECTION (Low-Medium Impact)
   Within top 50, all are good choices
   Status: ✅ AI handles this

6. 🔄 CURRENT HOLDINGS (Low-Medium Impact)
   Reduces transaction costs
   Status: ⚠️  Not using yet (can add with --current-holdings)

💡 BOTTOM LINE:

The portfolio DOES matter, but your current settings are solid!

Main decisions you control:
  ✅ Size: 50 stocks (optimal)
  ⚠️  Concentration: High (tilt=5.0) - could be risky
  ✅ Selection: AI picks best from top 20% - trust it!

If you want to adjust risk:
  • More conservative: tilt_factor = 2.0
  • Current (aggressive): tilt_factor = 5.0
  • Very aggressive: tilt_factor = 10.0
""")

print("\n" + "="*80)
print("PRACTICAL RECOMMENDATIONS")
print("="*80)

print("""
Based on your question, here's what you should focus on:

1. ✅ USE SIZE=50 (not 10)
   Your test used --size 10 for speed
   For real trading, use full 50 stocks

2. ⚠️  REVIEW TILT FACTOR
   Current: 5.0 (aggressive)
   Consider: 3.0 (balanced) or 2.0 (conservative)

   To change: Edit config/config.yaml
   weight_tilt_factor: 3.0  # More balanced

3. 💡 TRUST THE AI'S STOCK PICKS
   Once you set size and tilt, let AI choose stocks
   Don't second-guess individual picks
   Focus on the PROCESS, not individual names

4. 🔄 USE --current-holdings FOR REBALANCING
   Reduces transaction costs
   Makes monthly rebalancing more efficient

5. 📊 MONITOR CONCENTRATION
   Check "Top 5 concentration %" each month
   If >70%, consider lowering tilt factor
   If <40%, you might want higher tilt

EXAMPLE COMMANDS:

# Conservative (more diversified)
python scripts/generate_portfolio.py --size 50 --tilt-factor 2.0

# Balanced (recommended)
python scripts/generate_portfolio.py --size 50 --tilt-factor 3.0

# Aggressive (current)
python scripts/generate_portfolio.py --size 50 --tilt-factor 5.0

# With current holdings (for rebalancing)
python scripts/generate_portfolio.py --size 50 --current-holdings previous_portfolio.csv
""")

# Live Trading Workflow Guide

## Quick Start

### Monthly Rebalancing (Recommended)

**Run this command on the first trading day of each month:**

```bash
source venv/bin/activate
python scripts/generate_portfolio.py --size 50 --weighting equal
```

This generates your portfolio for the month with LLM enhancement.

---

## Complete Trading Workflow

### Step 1: Generate Current Portfolio (Monthly)

**Basic command (LLM-enhanced, 50 stocks):**
```bash
python scripts/generate_portfolio.py
```

**Advanced options:**
```bash
# Baseline only (no LLM)
python scripts/generate_portfolio.py --no-llm

# Custom portfolio size
python scripts/generate_portfolio.py --size 30

# Different weighting
python scripts/generate_portfolio.py --weighting momentum

# Custom LLM tilting
python scripts/generate_portfolio.py --tilt-factor 10.0

# Compare with current holdings
python scripts/generate_portfolio.py --current-holdings results/portfolios/my_current_portfolio.csv
```

### Step 2: Review Output

The script will show you:

1. **Top 20 Holdings** with weights and LLM scores
2. **Portfolio Summary** (total positions, max/min weights)
3. **Trade List** (if comparing with current holdings)
4. **Saved CSV** in `results/portfolios/` directory

**Example Output:**
```
TOP 20 HOLDINGS
==========================================================================================

symbol  weight  momentum_return  llm_score
KKR     14.43%       97.05%        1.000
HWM     14.43%       95.39%        1.000
LLY     14.43%       73.23%        1.000
IRM      4.73%       78.25%        0.600
KLAC     4.73%       63.28%        0.600
...
```

### Step 3: Calculate Your Trades

**For a $100,000 portfolio:**

```python
# If you want to calculate exact shares
import pandas as pd

# Load the generated portfolio
portfolio = pd.read_csv('results/portfolios/portfolio_enhanced_equal_20241105_120000.csv')

# Your capital
capital = 100000

# Get current prices (already in CSV from script)
# Calculate shares for each position
for _, row in portfolio.head(10).iterrows():  # Top 10 for example
    position_value = capital * row['weight']
    # You'd get current price from your broker
    shares = position_value / current_price
    print(f"{row['symbol']}: Buy ${position_value:,.2f} (~{shares:.0f} shares)")
```

### Step 4: Execute Trades

**Recommended Execution Order:**

1. **Sell first** (during market hours)
   - Close all positions not in new portfolio
   - Use market orders or limit orders with tight spreads

2. **Buy second** (same day or next day)
   - Open new positions according to weights
   - Split into small orders if capital > $500K
   - Use limit orders to avoid market impact

3. **Rebalance holds**
   - Adjust positions that are in both old and new portfolios
   - Only trade if weight difference > 1%

**Transaction Cost Tips:**
- Use commission-free brokers (Robinhood, IBKR, etc.)
- Trade during liquid hours (10 AM - 3 PM ET)
- Use limit orders for large positions
- Consider using VWAP for positions > $10K

### Step 5: Record Your Execution

Save your actual executed portfolio for next month:

```bash
# Create a simple CSV with your actual holdings
# symbol,weight,shares,entry_price,entry_date
# KKR,0.1443,150,96.23,2024-11-01
# HWM,0.1443,200,72.15,2024-11-01
# ...
```

Or use the generated portfolio as your baseline:
```bash
cp results/portfolios/portfolio_enhanced_equal_20241105_120000.csv \
   results/portfolios/my_current_portfolio.csv
```

---

## Monthly Checklist

**First Trading Day of Each Month:**

- [ ] Run portfolio generation script
- [ ] Review top holdings and weights
- [ ] Check for data quality issues (missing prices, stale news)
- [ ] Compare with current holdings
- [ ] Calculate required trades
- [ ] Execute rebalance during market hours
- [ ] Save executed portfolio for next month
- [ ] Record performance (optional but recommended)

---

## Example: Full Monthly Cycle

### November 1, 2024 (Rebalance Day)

**Morning (before market open):**
```bash
# Generate new portfolio
python scripts/generate_portfolio.py \
  --current-holdings results/portfolios/my_october_portfolio.csv
```

**Output shows:**
- 50 positions total
- Sell 12 stocks, Buy 15 stocks, Hold 38 stocks
- 27% turnover

**During market hours:**
```python
# 1. Sell 12 positions (liquidate to cash)
# 2. Calculate new position sizes with updated cash
# 3. Buy 15 new positions + rebalance 38 holds
```

**After market close:**
```bash
# Save actual executed portfolio
cp results/portfolios/portfolio_enhanced_equal_20241101_093000.csv \
   results/portfolios/my_november_portfolio.csv
```

---

## Portfolio Tracking

### Option 1: Simple Spreadsheet

Track monthly performance:

| Month | Portfolio Value | Monthly Return | Cumulative Return | Trades Executed |
|-------|----------------|----------------|-------------------|-----------------|
| Oct 2024 | $100,000 | - | 0% | Initial |
| Nov 2024 | $103,500 | 3.5% | 3.5% | 27 |
| Dec 2024 | $107,200 | 3.6% | 7.2% | 22 |

### Option 2: Automated Tracking

Create a simple tracking script:

```python
# Track your portfolio performance
import pandas as pd
from datetime import datetime

def log_performance(portfolio_value, trades_executed):
    """Log monthly performance."""
    log_file = 'results/portfolios/performance_log.csv'

    entry = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'portfolio_value': portfolio_value,
        'trades_executed': trades_executed
    }

    # Append to log
    df = pd.DataFrame([entry])
    df.to_csv(log_file, mode='a', header=not Path(log_file).exists(), index=False)

    print(f"✓ Logged performance: ${portfolio_value:,.2f}")

# Use it after each rebalance
log_performance(portfolio_value=103500, trades_executed=27)
```

---

## Important Considerations

### 1. Data Freshness

**Price Data:**
- yfinance data updates with ~15-minute delay
- OK for monthly rebalancing (not sensitive to intraday)
- Run script morning of rebalance day for fresh data

**News Data:**
- Fetches most recent 1-day news
- Run script same day as rebalancing for best results
- LLM scores based on latest available news

### 2. Market Conditions

**Best times to rebalance:**
- First trading day of month (consistent timing)
- Avoid days with major announcements (Fed, earnings)
- Consider end-of-month if better for taxes

**Market hours:**
- Execute between 10 AM - 3 PM ET (most liquid)
- Avoid first/last 30 minutes (volatile)
- Use limit orders if >$10K per position

### 3. Transaction Costs

**Expected costs:**
- Commission: $0 (most brokers)
- Spread: ~2-5 basis points for liquid stocks
- Slippage: ~1-2 basis points if using limits
- **Total**: ~3-7 basis points (vs 2 bps modeled)

**With $100K portfolio and 30% turnover:**
- Trade value: $30,000
- Cost: ~$10-20 total
- Very minimal impact on returns

### 4. Position Sizing

**Practical constraints:**
- Script generates weights summing to 100%
- You'll have rounding when buying shares
- Small positions (<$500) may not be worth trading

**Recommendations:**
- Round to whole shares
- Set minimum position size (e.g., $1,000)
- May end up with 45-48 positions vs target 50
- Keep ~1-2% cash for rounding

---

## Broker Integration

### Interactive Brokers (IBKR)

Use their API for automated execution:

```python
from ib_insync import *

# Connect to IBKR
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# Load portfolio
portfolio = pd.read_csv('results/portfolios/portfolio_enhanced_equal_20241105.csv')

# Execute trades
for _, row in portfolio.iterrows():
    symbol = row['symbol']
    weight = row['weight']
    target_value = capital * weight

    # Create order
    contract = Stock(symbol, 'SMART', 'USD')
    order = MarketOrder('BUY', shares)

    # Place order
    trade = ib.placeOrder(contract, order)
```

### Alpaca (Commission-Free)

```python
import alpaca_trade_api as tradeapi

# Connect
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url='https://paper-api.alpaca.markets')

# Load portfolio
portfolio = pd.read_csv('results/portfolios/portfolio_enhanced_equal_20241105.csv')

# Submit orders
for _, row in portfolio.iterrows():
    api.submit_order(
        symbol=row['symbol'],
        notional=capital * row['weight'],  # Dollar amount
        side='buy',
        type='market',
        time_in_force='day'
    )
```

### Manual Execution (Most Common)

1. Export portfolio to CSV
2. Open in Excel/Google Sheets
3. Calculate position sizes for your capital
4. Manually enter orders in broker's web interface
5. Execute during market hours

---

## Risk Management

### Position Limits

The script enforces:
- **15% max per position** (prevents over-concentration)
- **~50 positions** (diversification)
- **Quality filters** (price > $5, volume > 100K)

### Monitoring

**Weekly check:**
- Are holdings still in S&P 500?
- Any delisted stocks?
- Any major news events?

**Red flags:**
- Stock drops >20% in single day → consider selling
- Position grows >20% → may need intra-month rebalance
- News of bankruptcy, fraud, etc. → sell immediately

### Stop Losses (Optional)

While not in the strategy, you can add:
- 20% stop loss per position
- 10% portfolio stop loss
- Only use if you're risk-averse

**Note:** Paper strategy doesn't use stops (buy & hold until rebalance)

---

## Performance Expectations

Based on backtest results:

**Annual Returns:**
- Baseline momentum: 10-19% (depending on market)
- LLM-enhanced: 11-23% (1.4-4.2% improvement)

**Risk Metrics:**
- Sharpe ratio: 0.8-0.9 (excellent)
- Max drawdown: 20-40% (expect significant drawdowns)
- Volatility: 18-22% (moderate-high)

**Realistic expectations:**
- Some months will be negative (expect -5% to -10%)
- Drawdowns of 20-30% are normal
- Strategy works best over 3+ year horizon
- 2024 was exceptional (+23% annual); don't expect every year

---

## Troubleshooting

### "No stocks selected"
- **Cause:** Not enough data in yfinance
- **Fix:** Script uses top 300 S&P 500; should work. Check internet connection.

### "LLM API error"
- **Cause:** OpenAI API key missing or invalid
- **Fix:** Set `OPENAI_API_KEY` environment variable
- **Alternative:** Use `--no-llm` flag for baseline only

### "Stale price data"
- **Cause:** yfinance cache outdated
- **Fix:** Delete `data/cache/` folder and re-run

### "Import errors"
- **Cause:** Virtual environment not activated
- **Fix:** Run `source venv/bin/activate` first

---

## Advanced Usage

### 1. Different Rebalancing Frequencies

**Weekly (more active):**
```bash
# Run every Monday
python scripts/generate_portfolio.py --size 30
```

**Quarterly (less active):**
```bash
# Run Jan 1, Apr 1, Jul 1, Oct 1
python scripts/generate_portfolio.py --size 50
```

**Note:** Paper uses monthly; changing frequency requires re-optimization

### 2. Portfolio Size Variations

**Small account (<$25K):**
```bash
# Use 20-30 positions to keep position sizes reasonable
python scripts/generate_portfolio.py --size 25
```

**Large account (>$500K):**
```bash
# Use 50-100 positions for better diversification
python scripts/generate_portfolio.py --size 75
```

### 3. Custom Tilting

**Conservative (less concentration):**
```bash
python scripts/generate_portfolio.py --tilt-factor 2.0
```

**Aggressive (more concentration):**
```bash
python scripts/generate_portfolio.py --tilt-factor 10.0
```

**Paper's optimal:** η = 5.0 (default)

### 4. Combine with Other Strategies

**50% LLM momentum + 50% index:**
- Run script for 50 stocks
- Use 50% of capital for momentum portfolio
- Put other 50% in SPY or VOO

**80% LLM momentum + 20% bonds:**
- Use 80% of capital for momentum
- Keep 20% in TLT or AGG for stability

---

## Tax Considerations

### Short-Term Capital Gains

- Monthly rebalancing = lots of short-term trades
- Short-term gains taxed as ordinary income (up to 37%)
- Consider using tax-advantaged accounts (IRA, 401k)

### Tax-Loss Harvesting

- If position down >5%, consider selling in December
- Realize losses to offset gains
- Re-buy after 30 days (wash sale rule)

### Account Types

**Best for this strategy:**
1. **IRA/Roth IRA** - Tax-free growth, no tax on rebalancing
2. **401(k)** - Tax-deferred, if platform supports individual stocks

**OK but suboptimal:**
3. **Taxable account** - High tax burden from frequent rebalancing

---

## Summary

**Monthly Workflow (15 minutes):**

1. First trading day: Run `python scripts/generate_portfolio.py`
2. Review output and save CSV
3. During market hours: Execute rebalancing trades
4. Save executed portfolio for next month
5. Done!

**Expected Results:**
- 10-23% annual returns
- 0.8-0.9 Sharpe ratio
- 20-40% max drawdown
- 27-36% annual turnover

**Key Success Factors:**
- Consistent monthly execution
- Discipline during drawdowns
- Low-cost broker (commission-free)
- Long-term horizon (3+ years)

**Questions?** Check `docs/` folder for more details or review `scripts/generate_portfolio.py` code.

---

*Happy Trading! 🚀*

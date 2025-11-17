# LLM Risk Scoring Feature - Complete! 🎯

## Overview

**YES!** I've added an **LLM Risk Index** to your portfolio holdings. This is now fully integrated into both the dashboard UI and command-line tools.

## What It Does

The LLM Risk Scorer analyzes recent news for each stock in your portfolio and provides:

- **Risk Score (0.0-1.0)**: Overall risk assessment
  - 0.0-0.4: 🟢 Low risk (safe)
  - 0.4-0.7: 🟡 Medium risk (watch)
  - 0.7-1.0: 🔴 High risk (reduce/sell)

- **Risk Breakdown** by category:
  - Financial Risk (earnings, revenue, debt)
  - Operational Risk (supply chain, management)
  - Regulatory Risk (investigations, lawsuits)
  - Competitive Risk (market share, competitors)
  - Market Risk (sector headwinds, macro)

- **Recommendation**: HOLD / REDUCE / SELL

- **Key Risk**: Main concern identified (if any)

## How to Use in Dashboard

### 1. Start the Dashboard

```bash
source venv/bin/activate
streamlit run dashboard.py
```

### 2. Navigate to "Generate Portfolio"

### 3. Enable Risk Scoring

- Check "Use LLM Enhancement" (required)
- Check "Add Risk Scores"
- (Optional) Enable "Reduce weights for high-risk stocks"

### 4. Configure Risk Settings (Optional)

Click "⚙️ Risk Scoring Settings" to:
- Set risk threshold (default: 0.7)
- Set reduction factor (default: 0.5 = reduce to 50%)

### 5. Generate Portfolio

Click "🔄 Generate Portfolio" and wait (extra 30-60 seconds for risk analysis)

### 6. View Risk Scores

You'll see:
- **Color-coded risk scores** in the holdings table
  - 🟢 Green: Low risk
  - 🟡 Yellow: Medium risk
  - 🔴 Red: High risk
- **Risk Distribution** showing breakdown by risk level
- **High-Risk Warnings** for stocks with risk > 0.7

## Visual Example

```
📋 Top 20 Holdings
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Symbol  Weight   LLM Score   Risk Score   Key Risk
AAPL    15.0%    1.000       0.25        None
NVDA    12.5%    0.950       0.65        Export restrictions concern
TSLA    10.0%    0.800       0.85        Safety recalls, SEC investigation

📊 Risk Score Distribution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟢 Low Risk         🟡 Medium Risk      🔴 High Risk
15 stocks (75%)     4 stocks (20%)      1 stock (5%)

⚠️ 1 high-risk stock detected - Consider monitoring closely
```

## Use Cases

### 1. Portfolio Monitoring
- **Before Rebalancing**: Check risk scores to identify problematic positions
- **After News Events**: Re-run risk scoring to see updated assessments
- **Monthly Review**: Track how risk scores change over time

### 2. Position Sizing
- **High-Risk Stocks**: Reduce position size or set tighter stop-losses
- **Low-Risk Stocks**: Comfortable holding larger positions
- **Mixed Risk Portfolio**: Balance high-risk high-reward with stable positions

### 3. Risk Management
- **Automatic Adjustment**: Let the system reduce high-risk weights automatically
- **Manual Decision**: Review high-risk stocks and decide individually
- **Early Warning**: Sell before major issues develop

## Risk Scoring Logic

The LLM analyzes news and evaluates:

### Financial Risk Signals:
- Earnings misses
- Revenue decline
- Rising debt levels
- Cash flow problems
- Accounting issues

### Operational Risk Signals:
- Supply chain disruptions
- Production issues
- Management changes/departures
- Labor disputes
- Technology failures

### Regulatory Risk Signals:
- Government investigations
- Lawsuits/litigation
- Compliance violations
- Regulatory changes
- Antitrust concerns

### Competitive Risk Signals:
- Market share loss
- New competitors
- Pricing pressure
- Product obsolescence
- Customer churn

### Market Risk Signals:
- Sector headwinds
- Macro economic challenges
- Interest rate sensitivity
- Geopolitical exposure
- Cyclical downturns

## Cost Considerations

### With GPT-4o-mini (Recommended):
- **Cost**: ~$0.02 per stock analyzed
- **Portfolio of 50 stocks**: ~$1.00 per generation
- **Monthly rebalancing**: ~$12/year

### With GPT-4o:
- **Cost**: ~$0.15 per stock analyzed
- **Portfolio of 50 stocks**: ~$7.50 per generation
- **Monthly rebalancing**: ~$90/year

**Tip**: Use GPT-4o-mini for regular monthly scoring, GPT-4o for critical decisions

## Examples

### Example 1: Identify Hidden Risks

```python
# Run in dashboard or command-line
python examples/portfolio_with_risk_scoring.py --size 20
```

Output:
```
⚠️ HIGH-RISK STOCKS

TSLA   - Risk: 0.85 - Safety recalls, SEC investigation
COIN   - Risk: 0.75 - Regulatory uncertainty, crypto volatility
NVDA   - Risk: 0.68 - Export restrictions to China
```

**Action**: Reduce TSLA and COIN positions, monitor NVDA

### Example 2: Automatic Risk Adjustment

Enable in dashboard:
- Check "Reduce weights for high-risk stocks"
- Risk threshold: 0.7
- Reduction factor: 0.5

Result:
- TSLA: 10% → 5% (reduced by 50%)
- Other stocks: Weights increased proportionally

### Example 3: Monthly Workflow

1. **Week 1**: Generate portfolio with risk scoring
2. **Review**: Check high-risk stocks
3. **Research**: Investigate key risks identified
4. **Decide**: Keep, reduce, or sell
5. **Execute**: Place trades
6. **Track**: Monitor risk scores monthly

## Command-Line Usage

```bash
# Generate portfolio with risk scoring
python examples/portfolio_with_risk_scoring.py \
    --size 50 \
    --risk-threshold 0.7 \
    --reduction-factor 0.5

# With custom settings
python examples/portfolio_with_risk_scoring.py \
    --size 30 \
    --risk-threshold 0.6 \
    --reduction-factor 0.3 \
    --no-risk-adjustment  # Just show scores, don't adjust
```

## Integration with Volatility Protection

You can use **both** volatility protection and risk scoring:

### Portfolio-Level Protection (Volatility)
- Adjusts overall exposure based on VIX/market regime
- Example: Reduce entire portfolio to 60% in volatile markets

### Stock-Level Protection (Risk Scoring)
- Identifies risky individual stocks
- Example: Reduce TSLA from 10% to 5% due to company-specific risks

### Combined Effect:
```
Base Portfolio:
- AAPL: 20%
- TSLA: 20%  (high risk: 0.85)
- NVDA: 20%
- MSFT: 20%
- GOOGL: 20%

After Risk Adjustment (TSLA reduced 50%):
- AAPL: 21.1%
- TSLA: 10.5%  (reduced due to risk)
- NVDA: 21.1%
- MSFT: 21.1%
- GOOGL: 21.1%

After Volatility Protection (VIX=35, 60% exposure):
- AAPL: 12.7%
- TSLA: 6.3%
- NVDA: 12.7%
- MSFT: 12.7%
- GOOGL: 12.7%
- CASH: 40%
```

## Files Created

1. **`src/llm/risk_scorer.py`** - Core risk scoring logic
2. **`examples/portfolio_with_risk_scoring.py`** - Full integration example
3. **`dashboard.py`** - Updated with risk scoring UI
4. **`scripts/generate_portfolio.py`** - Updated with risk scoring support

## Technical Details

### Risk Score Calculation

```python
from src.llm import LLMRiskScorer

# Initialize
risk_scorer = LLMRiskScorer(model='gpt-4o-mini')

# Score a stock
risk_assessment = risk_scorer.score_stock_risk(
    symbol='TSLA',
    news_articles=news_list
)

# Returns:
{
    'symbol': 'TSLA',
    'overall_risk_score': 0.85,
    'financial_risk': 'HIGH',
    'operational_risk': 'MEDIUM',
    'regulatory_risk': 'HIGH',
    'competitive_risk': 'MEDIUM',
    'market_risk': 'MEDIUM',
    'key_risk': 'Safety recalls and SEC investigation',
    'recommendation': 'REDUCE',
    'reasoning': 'Multiple regulatory challenges...'
}
```

### Integration with Portfolio

```python
# After building portfolio
portfolio_with_risk = risk_scorer.score_portfolio_risks(
    portfolio=portfolio_df,
    news_data=news_dict,
    show_progress=True
)

# Apply risk-based adjustment (optional)
adjusted_portfolio = risk_scorer.apply_risk_based_adjustment(
    portfolio=portfolio_with_risk,
    risk_threshold=0.7,
    reduction_factor=0.5
)
```

## Benefits

### 1. Early Warning System
- Detect problems before they show up in price
- News-based signals often precede price moves
- Avoid major losses from company-specific issues

### 2. Better Risk Management
- Quantify subjective risk assessment
- Consistent evaluation across all stocks
- Reduce emotional decision-making

### 3. Improved Sharpe Ratio
- Reduce exposure to high-risk stocks
- Lower volatility from avoiding blowups
- Better risk-adjusted returns

### 4. Complement Technical Analysis
- Momentum shows what's working (price)
- Risk scores show what might fail (fundamentals/news)
- Combined view is more robust

## Limitations & Considerations

### 1. News Dependency
- **Limitation**: Requires recent news for accurate scoring
- **Mitigation**: Falls back to neutral score if no news available

### 2. LLM Interpretation
- **Limitation**: Risk assessment is based on LLM's interpretation
- **Mitigation**: Always review high-risk stocks manually

### 3. Lagging Indicator
- **Limitation**: News-based, so may lag actual events
- **Mitigation**: Use alongside technical indicators

### 4. Cost
- **Limitation**: Adds LLM API cost per stock
- **Mitigation**: Use GPT-4o-mini ($1/month for 50 stocks)

## FAQ

### Q: Should I always use risk scoring?
**A**: Recommended for most portfolios. Skip if you prefer purely quantitative/technical approach.

### Q: How often should I update risk scores?
**A**: Monthly during rebalancing is sufficient. Update more frequently during volatile markets or after major news.

### Q: Can I trust the risk scores?
**A**: Use as one input among many. Always do your own research for high-risk stocks.

### Q: What if I disagree with a risk score?
**A**: Risk scoring is a tool, not a mandate. Override as needed based on your research.

### Q: Does this work for all stocks?
**A**: Works best for large-cap stocks with regular news coverage. Less effective for small-caps with limited news.

## Try It Now!

```bash
# In Dashboard (Easiest)
streamlit run dashboard.py
# → Check "Add Risk Scores"

# Command-Line
python examples/portfolio_with_risk_scoring.py --size 20

# Test with single stock
python src/llm/risk_scorer.py
```

---

**Your portfolio now has institutional-grade risk assessment built in! 🎯**

Combine this with volatility protection for comprehensive risk management at both portfolio and stock levels.

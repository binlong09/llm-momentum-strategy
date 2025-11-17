# Individual Stock Analyzer Feature 🔍

## What It Does

Analyze any stock (not just the top 50 momentum stocks) using the same AI-powered analysis that powers the portfolio generator.

## How to Use

### 1. Access the Feature

In the dashboard, select **"🔍 Analyze Individual Stock"** from the navigation menu.

### 2. Enter Stock Ticker

Type any valid stock ticker (e.g., AAPL, TSLA, NVDA, etc.)

### 3. Choose Analysis Options

**🤖 Run LLM Sentiment Analysis:**
- Analyzes recent news (last 3-7 days)
- Predicts momentum continuation probability
- Score: 0.0 = bearish, 1.0 = very bullish

**🔍 Run Risk Assessment:**
- Evaluates 5 risk categories from news
- Identifies company-specific concerns
- Score: 0.0 = very safe, 1.0 = very risky

**📝 Store Prompts:**
- View exactly what news was analyzed
- See the prompts sent to AI
- Verify and validate all decisions

### 4. Click "🚀 Analyze Stock"

The system will:
1. Fetch price data and calculate 12-month momentum
2. Compare to SPY performance
3. Fetch recent news (last 5 days)
4. Run AI sentiment analysis (if enabled)
5. Run risk assessment (if enabled)
6. Display results and prompts

---

## What You Get

### Basic Metrics

**📈 12-Month Momentum**
- Shows the stock's performance over the past year
- Example: +73.20%

**vs SPY**
- Shows relative performance vs market
- Example: +15.30% (beat market by 15.3%)

**📰 News Articles**
- Number of recent articles found
- Expandable to view full list

### LLM Sentiment Analysis

**Sentiment Score (0.0 - 1.0)**
- 🟢 **0.7-1.0**: Bullish (momentum likely continues)
- 🟡 **0.5-0.7**: Neutral (mixed signals)
- 🔴 **0.0-0.5**: Cautious/Bearish (momentum may reverse)

**Interpretation**
- Clear explanation of what the score means
- Based on AI analysis of recent news

**View Prompt**
- See exactly what was sent to AI
- Verify the news articles analyzed
- Check prompt length and quality

### Risk Assessment

**Risk Score (0.0 - 1.0)**
- 🟢 **0.0-0.4**: Low Risk (no significant concerns)
- 🟡 **0.4-0.7**: Medium Risk (some concerns to monitor)
- 🔴 **0.7-1.0**: High Risk (significant concerns)

**Key Risk**
- Primary concern identified by AI
- Example: "Supply chain constraints"

**Recommendation**
- HOLD (safe to keep position)
- REDUCE (consider reducing exposure)
- SELL (exit recommended)

**Risk Category Breakdown**
- 💰 **Financial**: earnings, debt, cash flow
- ⚙️ **Operational**: supply chain, production
- ⚖️ **Regulatory**: legal, compliance
- 🏁 **Competitive**: market share, rivals
- 📊 **Market**: sector trends, macro

Each category shows:
- 🟢 LOW / 🟡 MEDIUM / 🔴 HIGH
- Quick description

**View Risk Prompt**
- See the full risk analysis prompt
- Verify risk assessment reasoning

---

## Use Cases

### 1. Research Before Adding to Portfolio

**Scenario:** You want to manually add a stock that didn't make the top 50.

**How to use:**
1. Analyze the stock
2. Check momentum vs SPY
3. Review AI sentiment and risk
4. Decide if it's worth adding

### 2. Verify Portfolio Decisions

**Scenario:** A stock ranked #1 but you're skeptical.

**How to use:**
1. Analyze it individually
2. Review the prompts
3. Check what news influenced the score
4. Verify the AI's reasoning

### 3. Track Specific Holdings

**Scenario:** You hold TSLA and want to monitor it weekly.

**How to use:**
1. Analyze TSLA every week
2. Watch for sentiment changes
3. Track risk score evolution
4. Make informed hold/sell decisions

### 4. Compare Alternative Stocks

**Scenario:** Choosing between NVDA and AMD.

**How to use:**
1. Analyze NVDA
2. Analyze AMD
3. Compare:
   - Momentum returns
   - AI sentiment scores
   - Risk scores
   - Risk category breakdowns
4. Choose the better option

### 5. Understand Why Stock Wasn't Selected

**Scenario:** Your favorite stock isn't in the portfolio.

**How to use:**
1. Analyze it
2. Check momentum (might be < top 20%)
3. Check AI sentiment (might be bearish)
4. Check risk (might be too high)
5. Understand why it was filtered out

---

## Example Analysis

### Input
```
Ticker: TSLA
LLM Sentiment: ✅ Enabled
Risk Assessment: ✅ Enabled
Store Prompts: ✅ Enabled
```

### Output

**Basic Metrics:**
```
12-Month Momentum: +156.30%
vs SPY: +120.40%
News Articles: 45
```

**LLM Sentiment:**
```
🟡 Score: 0.65 Neutral

Interpretation: Neutral - Mixed signals in recent news

Prompt shows:
- Article 1: Tesla Q3 earnings beat expectations
- Article 2: Cybertruck production delays continue
- Article 3: Competition intensifies from legacy auto
- Article 4: Regulatory scrutiny over Autopilot
- Article 5: Strong China sales growth
```

**Risk Assessment:**
```
🟡 Risk Score: 0.68 Medium Risk

Key Risk: Regulatory scrutiny and production delays
Recommendation: REDUCE

Risk Breakdown:
💰 Financial:    🟢 LOW       (strong earnings, good cash flow)
⚙️ Operational:  🔴 HIGH      (production delays, quality issues)
⚖️ Regulatory:   🔴 HIGH      (Autopilot investigation, SEC probe)
🏁 Competitive:  🟡 MEDIUM    (legacy auto ramping EV production)
📊 Market:       🟢 LOW       (EV sector growth continues)
```

**Decision:**
- ✅ Strong momentum (156% vs 20% SPY)
- 🟡 Mixed AI sentiment (0.65)
- 🔴 Elevated risk (0.68 with regulatory/operational concerns)
- **Conclusion:** High reward but high risk. Consider smaller position.

---

## Tips

### Best Practices

1. **Always enable "Store Prompts"**
   - Lets you verify AI reasoning
   - Critical for catching errors
   - Helps you learn what matters

2. **Check vs SPY**
   - Relative performance matters more than absolute
   - Stock up 20% but SPY up 25% = underperforming

3. **Read the prompts**
   - Don't blindly trust AI scores
   - Verify the news makes sense
   - Check if important events were captured

4. **Compare risk categories**
   - Financial + Operational issues = serious
   - Just Market risk = sector-wide (less concerning)
   - Regulatory risk = unpredictable (be cautious)

5. **Use for portfolio stocks**
   - Analyze your top holdings regularly
   - Watch for sentiment/risk changes
   - Exit before scores deteriorate

### Common Pitfalls

❌ **Don't analyze too frequently**
- News changes slowly (3-7 days)
- Analyzing daily wastes API costs
- Weekly or monthly is sufficient

❌ **Don't ignore momentum**
- AI sentiment is useless if momentum is weak
- Need both momentum AND positive sentiment

❌ **Don't trust single scores**
- Look at all factors together
- High momentum + low risk + bullish sentiment = best
- High momentum + high risk + bearish sentiment = avoid

❌ **Don't skip prompt review**
- Scores can be wrong
- Always verify with prompts
- Catch data quality issues early

---

## Cost

**LLM Sentiment (gpt-4o-mini):**
- ~$0.001-0.002 per analysis
- Very cheap for occasional use

**Risk Assessment (gpt-4o-mini):**
- ~$0.001-0.002 per analysis
- Combined: ~$0.002-0.004 per full analysis

**Example usage:**
- Analyze 10 stocks/month: ~$0.04/month
- Analyze 50 stocks/month: ~$0.20/month

Negligible cost for the insights gained!

---

## Comparison to Portfolio Generator

| Feature | Portfolio Generator | Individual Stock Analyzer |
|---------|-------------------|--------------------------|
| **Stocks Analyzed** | Top 20% by momentum (200 stocks) | Any stock you specify |
| **Filtering** | Yes (momentum + liquidity) | No (you choose) |
| **Selection** | Top 50 for portfolio | Single stock deep-dive |
| **Use Case** | Monthly rebalancing | Research, verification |
| **Batch Mode** | Yes (analyzes 50 at once) | No (one at a time) |
| **Prompts** | Stored for all 50 | Stored for analyzed stock |

**When to use each:**

**Portfolio Generator:**
- Monthly portfolio construction
- Systematic approach
- Full diversification
- Batch processing

**Individual Stock Analyzer:**
- Research specific stocks
- Verify portfolio holdings
- Compare alternatives
- Deep-dive analysis

---

## Summary

The Individual Stock Analyzer lets you:

✅ Analyze **any stock** (not just top 50)
✅ Get **AI sentiment** and **risk scores**
✅ View **exact prompts** used
✅ Compare **momentum vs SPY**
✅ Make **informed decisions**

**Perfect for:**
- Research before buying
- Verifying portfolio decisions
- Monitoring holdings
- Comparing alternatives
- Understanding AI reasoning

**Access it:** Dashboard → 🔍 Analyze Individual Stock

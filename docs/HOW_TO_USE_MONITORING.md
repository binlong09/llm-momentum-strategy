# 📊 How to Use the Daily Portfolio Monitor

## Quick Start

### 1. Launch Dashboard
```bash
streamlit run dashboard.py
```

### 2. Go to "📊 Daily Monitor" Page
Click "📊 Daily Monitor" in the sidebar

### 3. Load Your Portfolio
**Option A:** Upload Robinhood CSV
- Click "📁 Upload Robinhood CSV"
- Select your latest export from Robinhood

**Option B:** Use Latest Snapshot
- Click "💾 Use Latest Snapshot"
- System loads your most recent portfolio data

### 4. Scan for News
Click **"🔍 Scan News for All Holdings"**

The system will:
- Fetch latest news from Yahoo Finance, CNBC, MarketWatch, WSJ
- Analyze sentiment using keyword detection
- Generate alerts based on severity

### 5. Review Alerts

Alerts are color-coded by severity:

#### 🚨 Critical (Red)
**What it means:**
- 2+ high-relevance red flags (fraud, bankruptcy, scandal)
- Company specifically mentioned near keywords

**What to do:**
1. Click to expand evidence section
2. Read article title and URL
3. Review context snippet
4. Click "🔗 Read full article"
5. Make decision (usually SELL)

**Example:**
```
🚨 CRITICAL: ACME Corp
Red flags: fraud, investigation

🚨 Red Flag Evidence (2 items)
  [1] Keyword: 'fraud' (Relevance: high)
      Article: ACME Corp Under SEC Investigation for Fraud
      Context: ...acme corp under sec investigation for fraud allegations...
      Published: 2025-11-09
      🔗 Read full article
```

#### ⚠️ Warning (Yellow)
**What it means:**
- 1 red flag OR 3+ warning keywords
- Earnings miss, downgrade, layoffs

**What to do:**
1. Read the evidence
2. Monitor closely
3. Usually HOLD until monthly rebalance
4. Reassess at month-end

#### ℹ️ Info (Blue)
**What it means:**
- Positive news or normal volatility
- No action needed

**What to do:**
- Feel good, continue holding
- Let winners run

### 6. View Evidence

For each alert, expand the evidence section to see:

- **Keyword**: Which red flag triggered (fraud, investigation, etc.)
- **Relevance**: High (company near keyword) vs Medium (general article)
- **Article Title**: Full headline
- **Context**: 50-char snippet around keyword
- **URL**: Direct link to article
- **Date**: Publication timestamp

### 7. Take Action

Based on `ALERT_INTERPRETATION_GUIDE.md`:

**SELL IMMEDIATELY:**
- Fraud allegations (company-specific)
- Bankruptcy filing
- Criminal charges against executives
- Stock down >20% on bad news

**MONITOR & RESEARCH:**
- Earnings miss (still growing)
- Single analyst downgrade
- CEO departure (planned)
- Stock down 10-15%

**NO ACTION:**
- Normal volatility (<10%)
- Positive news
- Sector-wide moves

## Understanding Evidence

### High-Relevance Evidence
Company name appears within 50 characters of the keyword:

```
Context: ...acme corp under sec investigation for fraud...
         ^^^^^^^^^           ^^^^^^^^^^      ^^^^^
         company            keyword
```

This is **likely accurate** - act on it.

### Medium-Relevance Evidence
Company mentioned in article, but keyword is general:

```
Article about ACME Corp mentions "industry fraud concerns"
```

This is **less urgent** - research further.

### No Evidence
If an article has keywords but no company mention → **Ignored** (not shown)

## Tips for Daily Use

### Morning Routine (5 minutes)
1. Open dashboard
2. Update prices (automatic)
3. Scan news
4. Check for critical alerts
5. Review if any, otherwise close

### Weekly Review (15 minutes)
1. Check performance vs S&P 500
2. Review all warnings
3. Note any patterns
4. Prepare for monthly rebalance

### Monthly Rebalance (30 minutes)
1. Review full portfolio
2. Check momentum rankings
3. Sell underperformers
4. Buy top-ranked replacements
5. Rebalance position sizes

## Common Questions

### "I see a critical alert, what do I do?"

**Step 1:** Read the evidence
- Is it really about this company?
- Is the keyword near the company name?
- Check the relevance score

**Step 2:** Click the article URL
- Read the full story
- Verify facts
- Check other sources

**Step 3:** Make decision
- If true fraud/bankruptcy → SELL immediately
- If overreaction → HOLD and monitor
- If unclear → See `ALERT_INTERPRETATION_GUIDE.md`

### "Should I sell on every warning?"

**No!** Warnings are for monitoring, not automatic selling.

- 1 warning = Note it, continue
- Multiple warnings over days = Research deeply
- Warnings + momentum drop = Consider selling at rebalance

### "What if there are no alerts?"

**Perfect!** This means:
- No concerning news
- Portfolio is healthy
- Continue normal operations

Most days should have zero critical alerts.

### "Can I trust the evidence URLs?"

**Yes!** Sources include:
- Yahoo Finance RSS
- CNBC RSS
- MarketWatch RSS
- Wall Street Journal RSS

All major financial news outlets.

### "What if the alert seems wrong?"

**Verify:**
1. Check the context snippet
2. Read the full article via URL
3. Look at the relevance score
4. If still unclear, ignore and monitor

The system is designed to **reduce false positives**, but you should always verify critical alerts before taking action.

## Advanced Features

### Performance Tracking
- View 7-day, 30-day, 90-day returns
- Compare vs S&P 500 benchmark
- See Sharpe ratio, max drawdown
- Track daily changes

### Historical Snapshots
- Daily portfolio value tracking
- Holdings history
- Performance over time
- Contribution analysis

### Export Options
- Save alerts to CSV
- Generate daily reports
- Track action history

## Troubleshooting

### "No news found for my stock"
- Stock might not be in RSS feeds
- Try again in a few hours
- Less coverage = less urgent anyway

### "Scan is slow"
- First scan takes 30-60 seconds (fetching RSS)
- Subsequent scans use cache (faster)
- 25 stocks = ~15 seconds

### "Alert seems like false positive"
- Check the evidence URL
- Read context snippet
- Verify company name near keyword
- Report if consistently wrong

## Getting Help

- **Alert interpretation**: See `ALERT_INTERPRETATION_GUIDE.md`
- **System improvements**: See `MONITORING_IMPROVEMENTS.md`
- **Questions**: Check these docs first

## Summary

✅ **Daily**: Scan news (5 min)
✅ **Critical alerts**: Act immediately
✅ **Warnings**: Monitor, usually hold
✅ **Info**: Ignore, feel good
✅ **Monthly**: Rebalance based on momentum

The system is designed to **alert you to real problems** while **minimizing false alarms**. Trust the evidence, verify with URLs, and make informed decisions.

Happy monitoring! 📊✨

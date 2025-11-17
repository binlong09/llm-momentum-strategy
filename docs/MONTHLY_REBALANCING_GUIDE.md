# 📅 Monthly Rebalancing Guide

Your quick reference for maintaining your LLM-enhanced momentum portfolio.

---

## ⏰ When to Rebalance

**Frequency:** Once per month on the same day
- **Recommended:** First Monday of each month
- **Your schedule:** Choose a consistent day that works for you
- **Time required:** 15-30 minutes

**Next rebalancing date:** ~December 2-9, 2025

---

## 📋 Monthly Checklist

### Week Before Rebalancing

- [ ] Check if any holdings had major news (earnings, scandals, regulatory issues)
- [ ] Note any stocks that dropped >15% (may indicate early momentum breakdown)
- [ ] Review overall market conditions (bull/bear/volatile)

### Rebalancing Day

#### Step 1: Generate Fresh Portfolio (5 min)

```bash
# In your project directory
streamlit run dashboard.py
```

1. Go to **"💼 Generate Portfolio"** page
2. Settings:
   - Portfolio size: **25 stocks**
   - LLM scoring: **Enabled** ✓
   - Phase 1 (News): **Enabled** ✓
   - Phase 2 (Earnings): **Enabled** ✓
   - Phase 3 (Analyst): **Enabled** ✓
   - Research mode: **Optional** (10 stocks for explanations)
3. Click **"Generate Portfolio"**
4. Wait ~2-3 minutes for completion
5. Review top 25 stocks - portfolio auto-saved

#### Step 2: Export Current Holdings (2 min)

**From Robinhood:**

**Mobile App:**
1. Open Robinhood app
2. Tap **Account** (bottom right)
3. Tap **Menu** (☰ top right)
4. Tap **Statements & History**
5. Tap **Account Statements**
6. Tap **Export**
7. Select **Stocks** data
8. Download CSV

**Website:**
1. Go to robinhood.com
2. Click **Account** → **History**
3. Click **Download** or **Export**
4. Save CSV file

#### Step 3: Calculate Rebalancing (5 min)

1. In dashboard, go to **"🔄 Monthly Rebalancing"**
2. Upload your Robinhood CSV (from Step 2)
3. Select **"Load Saved Portfolio"** → choose latest
4. Settings:
   - Target stocks: **25**
   - Rebalancing threshold: **5%**
5. Click **"Calculate Rebalancing Trades"**
6. Review summary:
   - How many sells/buys?
   - Turnover rate? (expect 20-40% monthly)
   - Total amounts?

#### Step 4: Review & Download (3 min)

1. Review the trades table (color-coded):
   - 🔴 **Red** = SELL completely
   - 🟢 **Green** = BUY new position
   - 🟠 **Orange** = REDUCE (sell partial)
   - 🔵 **Blue** = ADD (buy partial)

2. Check for any red flags:
   - Selling recent winners? (could trigger taxes)
   - Buying stocks you don't recognize? (research them)
   - Unusually high turnover >60%? (market regime shift?)

3. Download files:
   - Click **"Download Trades CSV"**
   - Click **"Download Instructions"**

#### Step 5: Execute Trades on Robinhood (10-20 min)

**IMPORTANT ORDER:**
1. Execute SELLS first (frees up cash)
2. Then execute BUYS (uses freed cash)

**For each SELL:**
1. Search ticker symbol in Robinhood
2. Click **Trade** → **Sell**
3. Select **Shares** → enter amount (or "All" for complete sells)
4. Order type: **Market Order**
5. Time in force: **Good for day**
6. Review and confirm

**For each BUY:**
1. Search ticker symbol
2. Click **Trade** → **Buy**
3. Select **Dollars** → enter target amount from CSV
4. Order type: **Market Order**
5. Time in force: **Good for day**
6. Review and confirm

**Pro tips:**
- Execute during market hours (9:30 AM - 4:00 PM ET)
- Use **dollar amounts** for buys (easier and more accurate)
- Double-check symbols before confirming
- Take a 5-minute break halfway through if doing 15+ trades

#### Step 6: Verify & Track (2 min)

1. In Robinhood, check final portfolio:
   - Should have ~25 positions
   - Total value should match pre-rebalance ±1%
2. Save files for records:
   - Trades CSV with date
   - Instructions file
   - Screenshot of final portfolio

---

## 📊 What to Expect

### Typical Monthly Changes

**Low turnover (10-20%):**
- Market steady
- 2-5 stocks change
- Most positions stay

**Medium turnover (20-40%):**
- Normal momentum rotation
- 5-10 stocks change
- Expected monthly pattern

**High turnover (40-60%):**
- Market regime shift
- 10-15 stocks change
- Review carefully before executing

**Very high turnover (>60%):**
- Major market change
- Consider waiting a week to confirm
- May want to adjust strategy

### Performance Tracking

**Good signs:**
- Portfolio outperforming S&P 500
- Winners staying in top 25 for 2-3 months
- Turnover stable at 20-40%

**Warning signs:**
- Underperforming S&P 500 for 3+ months straight
- Turnover >60% multiple months in a row
- Many stocks dropping -15%+ within days of buying

---

## 🚨 Emergency Actions (Between Rebalances)

**Only act mid-month if:**

1. **Fraud/Scandal:** Company accused of fraud, CEO arrested
   - → SELL immediately

2. **Bankruptcy Risk:** Company announces liquidity crisis
   - → SELL immediately

3. **Catastrophic Drop:** Stock drops >20% in one day on bad news
   - → Review news, consider selling
   - → Don't panic sell on market-wide drops

4. **All other situations:**
   - → HOLD until next monthly rebalance
   - → Momentum strategies need time to work

---

## 💰 Tax Considerations

**Keep in mind:**
- Selling winners = **capital gains taxes**
- Holding >1 year = **long-term gains** (lower tax rate)
- Selling losers = **tax loss harvesting** (offset gains)

**Tax-smart tips:**
1. Track your purchase dates
2. If possible, hold winners >1 year
3. Harvest losses in December (tax year end)
4. Set aside ~20-30% of gains for taxes
5. Consider consulting a tax advisor

---

## 📈 Performance Review (Quarterly)

**Every 3 months, review:**

1. **Returns:**
   - Your portfolio return vs S&P 500
   - Best/worst performing stocks
   - Contribution of LLM scoring

2. **Costs:**
   - Trading frequency and costs
   - Tax impact
   - LLM API costs (~$1-2/month)

3. **Strategy:**
   - Is momentum working in current market?
   - Should you adjust portfolio size?
   - Are LLM predictions helping?

---

## 🛠️ Troubleshooting

### "Portfolio generation failed"
- Check internet connection (needs API access)
- Verify API keys in `.env` file
- Try running with fewer data sources first

### "Can't parse Robinhood CSV"
- Make sure it's the stocks export (not options/crypto)
- Check file has headers: name, symbol, shares, price, equity
- Try re-exporting from Robinhood

### "Turnover seems too high"
- Market may be in transition period
- Check if momentum landscape actually changed
- Consider waiting 1 week and regenerating portfolio

### "LLM scoring taking too long"
- Reduce portfolio size temporarily
- Disable research mode
- Check LLM API status

---

## 📞 Quick Reference

**Dashboard:**
```bash
cd /Users/nghiadang/AIProjects/llm_momentum_strategy
source venv/bin/activate
streamlit run dashboard.py
```

**Test rebalancing:**
```bash
python test_rebalancing.py
```

**Files:**
- Portfolios: `results/portfolios/`
- Exports: `results/exports/`
- Holdings: Download from Robinhood monthly

**Key metrics:**
- Target: 25 stocks
- Rebalance: Monthly
- Threshold: 5% weight difference
- Expected turnover: 20-40%

---

## 🎯 Success Metrics

**You're doing well if:**
- ✅ Rebalancing consistently every month
- ✅ Turnover in healthy range (20-40%)
- ✅ Outperforming S&P 500 over 6-12 months
- ✅ Following the system without panic selling

**Red flags:**
- ❌ Missing multiple monthly rebalances
- ❌ Manually buying stocks outside the system
- ❌ Panic selling on every -5% dip
- ❌ Constantly tweaking parameters mid-month

---

## 📚 Additional Resources

- **Backtest results:** Check `results/backtests/` for historical performance
- **Individual stock analysis:** Use "🔍 Analyze Individual Stock" page
- **Trading guide:** See "📚 Trading Guide" in dashboard
- **Code:** All source in `src/` directory

---

**Good luck with your momentum investing journey! 🚀**

**Next rebalance:** First week of December 2025

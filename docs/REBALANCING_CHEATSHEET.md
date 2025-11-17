# 🚀 Monthly Rebalancing Cheat Sheet

**Quick reference card - Print and keep handy!**

---

## ⏰ Schedule
- **When:** First Monday of each month
- **Time:** 15-30 minutes
- **Next:** ~December 2-9, 2025

---

## ✅ 6-Step Checklist

### 1️⃣ Generate Portfolio (5 min)
```bash
streamlit run dashboard.py
```
→ "💼 Generate Portfolio" → Settings: 25 stocks, all phases ON → Generate

### 2️⃣ Export Holdings (2 min)
**Robinhood App:** Account → Menu → Statements → Export → Stocks
**Robinhood Web:** Account → History → Download

### 3️⃣ Calculate Rebalancing (5 min)
Dashboard → "🔄 Monthly Rebalancing" → Upload CSV → Select portfolio → Calculate

### 4️⃣ Review Trades (3 min)
- Check turnover (expect 20-40%)
- Review sells/buys
- Download CSV + Instructions

### 5️⃣ Execute on Robinhood (10-20 min)
**ORDER MATTERS:**
1. SELL all red trades first 🔴
2. THEN BUY all green trades 🟢

**Tips:**
- Use **Market Orders**
- Buy with **Dollars** (not shares)
- Trade during market hours (9:30 AM - 4 PM ET)

### 6️⃣ Verify (2 min)
- Check final portfolio (~25 stocks)
- Save CSV + screenshots

---

## 🚨 Emergency Rules

**ONLY sell between rebalances if:**
- Fraud/scandal announced
- Bankruptcy risk
- Stock drops >20% in one day on bad news

**Otherwise:** HOLD until next month!

---

## 📊 What's Normal?

| Metric | Healthy Range |
|--------|---------------|
| Turnover | 20-40% monthly |
| Stocks changed | 5-10 per month |
| Portfolio size | 25 stocks |
| Trading time | 15-30 min |

---

## 💰 Tax Reminders

- Selling = capital gains taxes
- Holding >1 year = lower tax rate
- Set aside 20-30% of profits for taxes

---

## 🛠️ Quick Commands

**Start dashboard:**
```bash
cd /Users/nghiadang/AIProjects/llm_momentum_strategy
source venv/bin/activate
streamlit run dashboard.py
```

**Test system:**
```bash
python test_rebalancing.py
```

---

## 📁 File Locations

- Portfolios: `results/portfolios/`
- Exports: `results/exports/`
- Full guide: `MONTHLY_REBALANCING_GUIDE.md`

---

**Questions?** Check the full guide or review backtest results in dashboard.

**Track your performance:** Compare to S&P 500 every quarter.

---

*Created: Nov 10, 2025 | Your next rebalance: ~Dec 2-9, 2025*

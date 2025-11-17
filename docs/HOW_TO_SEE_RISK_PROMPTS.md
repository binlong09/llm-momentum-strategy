# How to See Risk Prompts 🔍

## Quick Answer

To see risk prompts, you need to enable **TWO** checkboxes when generating:

```
✅ Use LLM Enhancement
✅ 📝 Store LLM Prompts
✅ Add Risk Scores        ← REQUIRED for risk prompts!
```

---

## Why You're Not Seeing Risk Prompts

### Current Setup (Missing Risk Prompts)

```
✅ Use LLM Enhancement
✅ 📝 Store LLM Prompts
❌ Add Risk Scores        ← This is OFF

Result: You see LLM scoring prompts but NO risk prompts
```

**Why?**
- Risk scoring only happens if "Add Risk Scores" is checked
- No risk scoring = no risk prompts to store
- Prompt storage can only save prompts that were generated

### Correct Setup (All Prompts Visible)

```
✅ Use LLM Enhancement
✅ 📝 Store LLM Prompts
✅ Add Risk Scores        ← Turn this ON!

Result: You see BOTH LLM scoring AND risk scoring prompts
```

---

## Step-by-Step Guide

### Step 1: Start Dashboard

```bash
streamlit run dashboard.py
```

### Step 2: Configure Portfolio Generation

In the "Generate Portfolio" tab:

1. **Check "Use LLM Enhancement"**
   - This enables AI-powered scoring

2. **Check "Add Risk Scores"**
   - This enables risk assessment
   - WITHOUT this, no risk prompts are generated

3. **Check "📝 Store LLM Prompts"**
   - This stores all prompts for viewing
   - Will capture both LLM and risk prompts

**You should see this message:**
```
✅ Both LLM scoring and risk scoring prompts will be stored
```

**If you see this instead:**
```
ℹ️ Only LLM scoring prompts will be stored
   (enable 'Add Risk Scores' to see risk prompts too)
```
→ You need to check "Add Risk Scores"!

### Step 3: Generate Portfolio

Click "🔄 Generate Portfolio"

Wait for completion (may take 2-3 minutes with both LLM and risk scoring)

### Step 4: View Prompts

1. Scroll to "Top 20 Holdings"
2. Click "📊 View detailed analysis" for any stock
3. You should now see:
   - ✅ "📝 View LLM Scoring Prompt"
   - ✅ "🔍 View Risk Scoring Prompt"

---

## What Each Prompt Shows

### LLM Scoring Prompt (Momentum Analysis)

```
You are a financial analyst evaluating stock: AAPL

Recent News (Last 3-7 Days):
1. 📊 Apple Reports Record Earnings...
2. 💼 Apple Announces AI Partnership...

12-Month Momentum Return: 73.20%

Based on the information above, predict the stock's
performance over the next 21 trading days...
```

**Purpose:** Decides if momentum will continue

### Risk Scoring Prompt (Risk Analysis)

```
You are a financial risk analyst. Analyze the
following recent news for AAPL and assess risk signals.

Recent News:
Article 1: Apple Reports Record Earnings...
Article 2: Apple Announces AI Partnership...

Evaluate the stock on these risk factors:
1. Financial Risk (earnings, revenue, debt)
2. Operational Risk (supply chain, management)
3. Regulatory Risk (legal, compliance)
4. Competitive Risk (market share, competitors)
5. Market Risk (sector headwinds)

For each risk factor, rate as: LOW, MEDIUM, or HIGH
Then provide overall risk score (0.0 to 1.0)...
```

**Purpose:** Identifies company-specific risks

---

## Cost Implications

### With LLM Only

```
✅ Use LLM Enhancement
❌ Add Risk Scores

Cost: ~$0.67/month (gpt-4o-mini, 50 stocks)
```

### With LLM + Risk Scoring

```
✅ Use LLM Enhancement
✅ Add Risk Scores

Cost: ~$1.34/month (gpt-4o-mini, 50 stocks)
      = $0.67 (LLM) + $0.67 (Risk)
```

**Trade-off:**
- Double the LLM cost
- But you get risk assessment + prompts
- Worth it for quality control

---

## Troubleshooting

### Q: I checked all boxes but still don't see risk prompts

**Check:**
1. Did you regenerate the portfolio AFTER checking the boxes?
2. Are you looking at the correct stock details?
3. Try expanding the section labeled "🔍 View Risk Scoring Prompt"

**If you see:**
```
🔍 Risk Scoring Prompt not available

💡 To see risk prompts: Enable both '📝 Store LLM
   Prompts' AND 'Add Risk Scores' when generating
```

→ The portfolio was generated WITHOUT risk scoring enabled.
   You need to regenerate with the checkbox ON.

### Q: Risk scoring is too slow/expensive

**Options:**

1. **Disable for monthly use, enable for verification:**
   ```
   Week 1: Generate with risk scoring (verify quality)
   Week 2-4: Generate without (faster, cheaper)
   ```

2. **Use for final candidates only:**
   - Generate baseline portfolio
   - Enable risk scoring only for top 10-20 stocks

3. **Reduce portfolio size:**
   - 20 stocks instead of 50
   - Cuts cost and time by 60%

---

## What You Get With Risk Prompts

### Before (No Risk Prompts)

```
Stock: TSLA
Rank: #5
Weight: 8.5%
LLM Score: 0.85 (bullish)
Risk Score: 0.75 (high risk)

❓ Why is risk high?
❓ What risks were identified?
❓ Is the AI analysis correct?
```

### After (With Risk Prompts)

```
Stock: TSLA
Rank: #5
Weight: 8.5%
LLM Score: 0.85 (bullish)
Risk Score: 0.75 (high risk)

🔍 View Risk Scoring Prompt:

Recent News analyzed:
1. Tesla recalls 2M vehicles (autopilot)
2. SEC investigation announced
3. Delivery numbers miss estimates
4. CEO controversy continues

Risk Assessment:
- Financial Risk: MEDIUM (revenue concerns)
- Operational Risk: HIGH (recalls, production)
- Regulatory Risk: HIGH (SEC, safety)
- Competitive Risk: MEDIUM (EV competition)
- Market Risk: LOW (sector strong)

Overall Risk Score: 0.75
Recommendation: REDUCE position

✅ Now you understand WHY it's high risk!
```

---

## Recommended Workflow

### Option 1: Always Enable (Best Quality)

```
Every month:
✅ Use LLM Enhancement
✅ Add Risk Scores
✅ Store LLM Prompts

Cost: ~$1.34/month
Benefit: Complete transparency, best decisions
```

### Option 2: Selective Enable (Cost-Conscious)

```
First portfolio of month:
✅ Use LLM Enhancement
✅ Add Risk Scores
✅ Store LLM Prompts
→ Review all prompts, verify quality

Rest of month:
✅ Use LLM Enhancement
❌ Add Risk Scores (skip to save cost)
❌ Store LLM Prompts (skip to save time)

Cost: ~$0.67/month average
Benefit: Quality control when it matters
```

### Option 3: Verification Only (Minimal Cost)

```
Use when you need to verify:
- New stock appears in top 10
- Unexpected ranking
- Want to understand a decision
- Debugging an issue

Otherwise: Skip risk scoring

Cost: ~$0.10-0.20/month (occasional use)
Benefit: Use it as a debugging tool
```

---

## Summary

**To see risk prompts, you MUST:**
1. ✅ Check "Add Risk Scores"
2. ✅ Check "📝 Store LLM Prompts"
3. ✅ Generate portfolio
4. ✅ View stock details

**What you'll see:**
- 📝 LLM Scoring Prompt (momentum analysis)
- 🔍 Risk Scoring Prompt (risk analysis)

**Cost:**
- ~$1.34/month for both (gpt-4o-mini)
- Worth it for transparency and quality control

**Benefit:**
- Complete visibility into AI decisions
- Verify risk assessments
- Make informed choices
- Catch issues early

---

## Quick Checklist

Before generating portfolio:

- [ ] "Use LLM Enhancement" checked
- [ ] "Add Risk Scores" checked ← Most important!
- [ ] "📝 Store LLM Prompts" checked
- [ ] See message: "Both LLM and risk prompts will be stored"

After generation:

- [ ] Click "View detailed analysis" for any stock
- [ ] See "📝 View LLM Scoring Prompt" - click to expand
- [ ] See "🔍 View Risk Scoring Prompt" - click to expand
- [ ] Both prompts visible and complete

If missing:

- [ ] Check if "Add Risk Scores" was enabled
- [ ] Regenerate portfolio with checkbox ON
- [ ] Try again

---

**🎯 Bottom line: Check "Add Risk Scores" to see risk prompts!**

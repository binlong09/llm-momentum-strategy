# LLM Prompt Viewing Feature 📝

## Overview

You can now **see exactly what the LLM analyzed** when scoring each stock! This transparency feature lets you verify the quality of the input data and understand how the AI made its decisions.

---

## What This Feature Does

When generating a portfolio with LLM enhancement, you can optionally **store the prompts** sent to the AI. Then, for each stock in your portfolio, you can:

1. ✅ View the exact prompt sent to the LLM
2. ✅ See all the news articles that were included
3. ✅ Review the momentum data provided
4. ✅ Verify the instructions given to the AI
5. ✅ Double-check that important information wasn't missed

---

## How to Use

### Step 1: Enable Prompt Storage

When generating a portfolio in the dashboard:

```
1. Check "Use LLM Enhancement"
2. Check "📝 Store LLM Prompts"  ← NEW!
3. Click "Generate Portfolio"
```

**What happens:**
- Prompts are stored during LLM scoring
- Available for review immediately
- Persists in session state

### Step 2: View Prompts

After portfolio generation:

```
1. Click "📊 View detailed analysis" for any stock
2. Look for "📝 View LLM Prompt (what the AI analyzed)"
3. Click to expand and see the full prompt
```

**What you'll see:**
- Complete prompt text
- News articles included (5-day enhanced analysis)
- Momentum metrics
- LLM instructions
- Prompt length (character count)

---

## Example

### What You'll See in the UI

```
📊 View detailed analysis for AAPL

  🚀 Exceptional momentum: +73.2% (12 months)
  🤖 Very Bullish AI assessment: 1.000/1.000
  🟢 Low Risk: 0.25/1.00

  ─────────────────────────────────────

  📝 View LLM Prompt (what the AI analyzed)

    This is exactly what was sent to the LLM:

    ┌──────────────────────────────────────┐
    │ You are a financial analyst          │
    │ evaluating stock: AAPL               │
    │                                      │
    │ Recent News:                         │
    │ 1. 📊 Apple Reports Record Earnings  │
    │    Revenue up 15% YoY...             │
    │                                      │
    │ 2. 💼 Apple Announces AI Partnership │
    │    New features for iOS 18...        │
    │                                      │
    │ 12-Month Momentum Return: 73.20%     │
    │                                      │
    │ Based on the information above...    │
    └──────────────────────────────────────┘

    📏 Prompt length: 2,847 characters
```

---

## What's in a Prompt?

### Basic Prompt Structure

```
You are a financial analyst evaluating stock: [SYMBOL]

Recent News:
[News articles from last 5 days with priority sorting]

12-Month Momentum Return: [PERCENTAGE]

Based on the information above, predict the stock's
performance over the next 21 trading days (~1 month).

Provide a score from 0 to 1 where:
- 0 = Very negative outlook
- 0.5 = Neutral outlook
- 1 = Very positive outlook

Respond with ONLY a single number between 0 and 1.
```

### Advanced Prompt (with company info)

Includes additional context:
- Company name
- Sector classification
- More detailed instructions
- Earnings/revenue prioritization

---

## Why This is Useful

### 1. **Quality Control**

**Verify the LLM has good data:**
- Are the news articles relevant?
- Is the 5-day lookback capturing important events?
- Are earnings reports included?
- Is the momentum metric correct?

**Example issues you might catch:**
- "No earnings news for AAPL" → Might want to check manually
- "Only general market news" → Not stock-specific enough
- "Old news from 2 weeks ago" → Cache issue?

### 2. **Understanding Decisions**

**See why the LLM scored a stock high/low:**
- "Oh, it saw the earnings beat announcement!"
- "It noticed the regulatory investigation"
- "It captured the CEO departure news"

### 3. **Debugging**

**If a score seems wrong:**
- Check what news was included
- Verify momentum calculation
- See if important events were missed
- Confirm prompt instructions are correct

### 4. **Learning**

**Improve your own analysis:**
- See what information matters most
- Learn how to weight different factors
- Understand news importance priorities
- Develop better investment intuition

---

## Technical Details

### Storage

**Where prompts are stored:**
- In-memory: Session state (during dashboard session)
- On-disk: `data/llm_prompts/` (optional)

**What's stored:**
- Full prompt text
- Timestamp
- Model used (gpt-4o-mini, etc.)
- Raw and normalized LLM scores

**Storage size:**
- ~2-3 KB per stock
- 50 stocks = ~100-150 KB
- Negligible storage impact

### Performance

**No performance impact:**
- Prompts generated anyway for LLM scoring
- Storing them is instantaneous
- Retrieval is instant (hash map lookup)
- No API calls needed

**Cost:**
- Zero additional cost
- Same LLM API usage as before

---

## Configuration

### Enable/Disable

**In Dashboard:**
- Checkbox: "📝 Store LLM Prompts"
- Default: OFF (opt-in)

**Why opt-in?**
- Some users may not need this
- Keeps UI simpler by default
- You decide when to enable

### Persistence

**Automatic in-session:**
- Prompts stored when you generate portfolio
- Available until you close dashboard

**Manual save (optional):**
```python
from src.llm import get_prompt_store

prompt_store = get_prompt_store()
prompt_store.save_session("my_portfolio_2024_11_08")
```

**Load later:**
```python
prompt_store.load_session("my_portfolio_2024_11_08")
```

---

## Use Cases

### Monthly Rebalancing

```
Week 1: Generate portfolio with prompt storage enabled
Week 2: Review high-conviction picks
        → Check prompts for top 10 stocks
        → Verify AI saw important news
Week 3: Make final decisions
Week 4: Execute trades
```

### Research & Due Diligence

```
1. Generate portfolio
2. Filter to high LLM scores (0.8+)
3. For each high-scorer:
   - View prompt
   - Verify news quality
   - Do additional research
   - Confirm or reject
```

### Debugging Low Scores

```
Stock A: High momentum (+60%) but low LLM score (0.3)
→ View prompt
→ See: "Earnings miss, guidance reduced, CEO investigation"
→ Understand: Momentum may be reversing
→ Decision: Avoid or reduce position
```

### Learning & Improvement

```
Month 1: Generate with prompts, track results
Month 2: Review which prompts led to good predictions
Month 3: Identify patterns (what news matters most?)
Month 4: Apply learnings to manual analysis
```

---

## Limitations

### What This Does NOT Do

❌ **Does not show LLM's reasoning**
- LLM only returns a number (0-1)
- No explanation of "why"
- Just shows input, not thought process

❌ **Does not modify prompts**
- Read-only view
- Cannot edit prompts
- Cannot re-score with different prompts

❌ **Does not store risk scoring prompts (yet)**
- Currently only LLM scoring prompts
- Risk scoring prompts coming in future update

### Workarounds

**Want to see LLM reasoning?**
- Use "research prompt" mode (manual)
- Ask LLM to explain in separate query

**Want to modify prompts?**
- Edit `src/llm/prompts.py`
- Create custom prompt templates

---

## Troubleshooting

### Q: Checkbox doesn't appear

**A:** Make sure "Use LLM Enhancement" is checked first.
Prompt storage only works with LLM mode enabled.

### Q: "No prompt stored for this stock"

**A:** Possible causes:
1. Generated portfolio without checkbox enabled
2. Stock was not scored by LLM (baseline momentum only)
3. Session state was cleared

**Fix:** Regenerate portfolio with checkbox enabled.

### Q: Prompt looks incomplete

**A:** Prompts might be long (2000-3000 chars).
The code view is scrollable - scroll to see full content.

### Q: Where are prompts saved?

**A:**
- In-session: Streamlit session state
- On-disk (if manually saved): `data/llm_prompts/`

---

## API Reference

### PromptStore Class

```python
from src.llm import get_prompt_store

# Get global instance
prompt_store = get_prompt_store()

# Store a prompt
prompt_store.store_prompt(
    symbol='AAPL',
    prompt='Your prompt text here...',
    prompt_type='llm_scoring',
    metadata={'model': 'gpt-4o-mini'}
)

# Retrieve a prompt
prompt = prompt_store.get_prompt('AAPL', 'llm_scoring')

# Get all prompts for a symbol
all_prompts = prompt_store.get_all_prompts('AAPL')

# Session management
prompt_store.save_session('session_name')
prompt_store.load_session('session_name')
prompt_store.clear_session()

# Get summary
summary = prompt_store.get_session_summary()
# Returns: {'stock_count': 50, 'prompt_types': [...], 'symbols': [...]}
```

---

## Examples

### Example 1: Basic Usage

```python
# In dashboard, after generating portfolio:
if st.session_state.get('prompt_store'):
    prompt_store = st.session_state.prompt_store

    # Get prompt for a stock
    aapl_prompt = prompt_store.get_prompt('AAPL', 'llm_scoring')

    print(f"Prompt length: {len(aapl_prompt)}")
    print(aapl_prompt)
```

### Example 2: Analyzing All Prompts

```python
# Get all stocks that were scored
summary = prompt_store.get_session_summary()
symbols = summary['symbols']

for symbol in symbols:
    prompt = prompt_store.get_prompt(symbol, 'llm_scoring')

    # Check if earnings mentioned
    if 'earnings' in prompt.lower():
        print(f"{symbol}: Has earnings news")

    # Check prompt length
    if len(prompt) < 1000:
        print(f"{symbol}: Warning - short prompt")
```

### Example 3: Save for Later Review

```python
# After generating portfolio
prompt_store = st.session_state.prompt_store

# Save to disk with descriptive name
from datetime import datetime
session_name = f"portfolio_{datetime.now().strftime('%Y%m%d')}"
prompt_store.save_session(session_name)

# Later, load and review
prompt_store.load_session(session_name)
prompts = {
    symbol: prompt_store.get_prompt(symbol, 'llm_scoring')
    for symbol in prompt_store.get_session_summary()['symbols']
}
```

---

## Testing

### Test Prompt Storage

```bash
python scripts/test_prompt_viewer.py
```

**Output:**
```
✅ All prompt storage tests passed!

Features verified:
  1. Prompt storage working
  2. Prompt retrieval working
  3. Session summary working
  4. Session persistence working
```

### Manual Test in Dashboard

1. Start dashboard: `streamlit run dashboard.py`
2. Enable "Use LLM Enhancement"
3. Enable "📝 Store LLM Prompts"
4. Generate portfolio
5. Click "View detailed analysis" for top stock
6. Expand "📝 View LLM Prompt"
7. Verify prompt appears correctly

---

## Future Enhancements

### Planned Features

1. **Risk Scoring Prompts**
   - Store risk assessment prompts
   - View side-by-side with LLM scoring prompts

2. **Prompt Comparison**
   - Compare prompts across multiple portfolio generations
   - Track how news changes over time

3. **Prompt Analytics**
   - Average prompt length statistics
   - News coverage metrics
   - News category distribution

4. **Export Prompts**
   - Download all prompts as JSON
   - Export to CSV for analysis

5. **Prompt Search**
   - Search prompts for keywords
   - Filter by news categories
   - Find stocks with specific events

---

## Summary

### What You Get

✅ **Transparency** - See exactly what the LLM analyzed
✅ **Quality Control** - Verify input data quality
✅ **Debugging** - Understand unexpected scores
✅ **Learning** - Improve your investment process
✅ **Confidence** - Trust the AI recommendations more

### How to Use It

1. Check "📝 Store LLM Prompts" when generating
2. View prompts in stock detail expandable sections
3. Review news quality and coverage
4. Verify AI has good information
5. Make better-informed decisions

### Zero Downsides

- No performance impact
- No cost increase
- Opt-in (not forced on you)
- Simple to use
- Powerful for verification

---

## Quick Start

```bash
# 1. Test the feature
python scripts/test_prompt_viewer.py

# 2. Use in dashboard
streamlit run dashboard.py

# 3. In UI:
#    ✓ Use LLM Enhancement
#    ✓ 📝 Store LLM Prompts
#    Generate Portfolio

# 4. View any stock's prompt
#    → Click "View detailed analysis"
#    → Expand "📝 View LLM Prompt"
#    → Review the content
```

---

**🎉 Prompt viewing is live! You can now see inside the AI's decision-making process.**

**Questions?** Check the code in `src/llm/prompt_store.py` or ask! 😊

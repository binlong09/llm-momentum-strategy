# Troubleshooting: Risk Prompts Not Showing 🔧

## Quick Diagnosis

I've added **debug panels** to the dashboard to help diagnose the issue. Here's how to use them:

### Step 1: Check Checkbox States BEFORE Generating

After checking the boxes, look for:

```
🔧 Debug: Checkbox States

Use LLM: True
Store Prompts: True
Enable Risk Scoring: True  ← Should be True!
Apply Risk Adjustment: True/False (doesn't matter)
```

**If "Enable Risk Scoring" shows False:**
- The checkbox isn't being checked properly
- Try unchecking and rechecking it
- Try refreshing the page

### Step 2: Check Generation Details AFTER Generating

After generating portfolio, expand:

```
🔍 Generation Details

LLM Enabled: True
Prompts Stored: True
Risk Scoring Enabled: True  ← Should be True!
Stocks in prompt store: 50
Prompt types stored: ['llm_scoring', 'risk_scoring']  ← Should have BOTH!
```

**If "Prompt types stored" only shows ['llm_scoring']:**
- Risk scoring didn't run
- Even though checkbox was checked
- This indicates a bug

---

## Common Issues & Fixes

### Issue 1: Old Portfolio in Session

**Symptom:**
- You enabled checkboxes
- Generated NEW portfolio
- Still seeing message: "enable both checkboxes"
- But you DID enable both!

**Cause:**
- Browser cached old portfolio
- Session state not cleared

**Fix:**
```
1. Refresh the browser page (F5 or Cmd+R)
2. Re-check all checkboxes
3. Generate portfolio again
4. Check debug panels
```

### Issue 2: Checkbox Not Registering

**Symptom:**
- You check "Add Risk Scores"
- Debug panel shows: "Enable Risk Scoring: False"

**Cause:**
- Streamlit state issue
- Checkbox not updating

**Fix:**
```
1. Uncheck the box
2. Wait 1 second
3. Check it again
4. Verify debug panel shows True
5. Then generate
```

### Issue 3: Risk Scoring Skipped

**Symptom:**
- Debug shows "Risk Scoring Enabled: True" BEFORE generating
- But "Prompt types stored: ['llm_scoring']" AFTER (missing risk_scoring)

**Cause:**
- Bug in code
- Risk scoring not being called despite checkbox

**Fix:**
- This is a code bug
- Check logs for errors
- May need code fix

### Issue 4: Prompt Store Not Passed

**Symptom:**
- Debug shows "Prompt types stored: ['llm_scoring']"
- Logs show risk scoring ran
- But prompts not stored

**Cause:**
- prompt_store not being passed to risk scorer

**Fix:**
- Check generate_portfolio.py line 253-254
- Should have: store_prompts=store_prompts, prompt_store=prompt_store

---

## Step-by-Step Diagnostic Process

### 1. Start Fresh

```bash
# Close dashboard
# Clear browser cache (Ctrl+Shift+Delete or Cmd+Shift+Delete)
# Restart dashboard
streamlit run dashboard.py
```

### 2. Enable Checkboxes Carefully

```
1. Check "Use LLM Enhancement"
   → Wait for UI to update

2. Check "Add Risk Scores"
   → Wait for UI to update
   → Look for risk settings expander

3. Check "📝 Store LLM Prompts"
   → Wait for UI to update
   → Should see caption about both prompts

4. Expand "🔧 Debug: Checkbox States"
   → Verify all three show True
```

### 3. Generate and Monitor

```
1. Click "Generate Portfolio"
2. Wait for completion
3. Expand "🔍 Generation Details"
4. Check "Prompt types stored"
```

### 4. Verify in Stock Details

```
1. Scroll to "Top 20 Holdings"
2. Click "View detailed analysis" for rank #1
3. Look for:
   - "📝 View LLM Scoring Prompt" (should exist)
   - "🔍 View Risk Scoring Prompt" (should exist)
```

---

## What Debug Output Tells You

### Good Output ✅

**Before Generation:**
```
🔧 Debug: Checkbox States
Use LLM: True
Store Prompts: True
Enable Risk Scoring: True
```

**After Generation:**
```
🔍 Generation Details
LLM Enabled: True
Prompts Stored: True
Risk Scoring Enabled: True
Stocks in prompt store: 50
Prompt types stored: ['llm_scoring', 'risk_scoring']
```

**Result:** Risk prompts should be visible ✅

### Bad Output #1 ❌

**Before Generation:**
```
🔧 Debug: Checkbox States
Use LLM: True
Store Prompts: True
Enable Risk Scoring: False  ← PROBLEM!
```

**Diagnosis:** Checkbox not being checked
**Fix:** Uncheck/recheck, or refresh page

### Bad Output #2 ❌

**After Generation:**
```
🔍 Generation Details
Risk Scoring Enabled: True
Prompt types stored: ['llm_scoring']  ← PROBLEM! Missing risk_scoring
```

**Diagnosis:** Risk scoring didn't run or prompts weren't stored
**Fix:** Check logs, may be code bug

### Bad Output #3 ❌

**After Generation:**
```
🔍 Generation Details
Prompt store: Not available  ← PROBLEM!
```

**Diagnosis:** Prompt store wasn't created/returned
**Fix:** Code bug in return value handling

---

## Manual Test: Verify Code Works

Run this to test risk prompt storage directly:

```bash
python scripts/test_risk_prompt_storage.py
```

**Expected output:**
```
✅ Correct number of stocks stored
✅ Risk scoring prompt type present
✅ AAPL prompt valid
✅ NVDA prompt valid
✅ TSLA prompt valid

🎉 ALL TESTS PASSED!
```

**If tests pass:**
- Code is working correctly
- Issue is in dashboard checkbox handling
- Or session state management

**If tests fail:**
- Code has a bug
- Risk prompt storage broken
- Need to fix code

---

## Known Issues

### Issue: Streamlit Session State

**Problem:**
- Streamlit caches widgets in session state
- Unchecking/rechecking might not update immediately
- Old values stick around

**Workaround:**
1. Refresh page completely
2. Don't rely on session state
3. Check debug panels to verify

### Issue: Checkbox Rendering Order

**Problem:**
- `enable_risk_scoring` defined inside column
- `store_llm_prompts` defined outside columns
- Order might matter

**Potential Fix:**
- Move all checkboxes to same scope
- Or move risk checkbox outside column

---

## If All Else Fails

### Nuclear Option: Clear Everything

```bash
# 1. Stop dashboard
# 2. Clear Streamlit cache
rm -rf ~/.streamlit/cache/

# 3. Clear data cache
rm -rf data/raw/news/*
rm -rf data/llm_prompts/*

# 4. Restart dashboard
streamlit run dashboard.py --server.port 8502

# 5. Use different port to force fresh session
```

### Report Issue

If nothing works, collect this info:

```
1. Screenshot of "🔧 Debug: Checkbox States" BEFORE generating
2. Screenshot of "🔍 Generation Details" AFTER generating
3. Output of: python scripts/test_risk_prompt_storage.py
4. Any error messages in console/logs
```

Then we can diagnose the exact issue.

---

## Most Likely Cause

Based on your description: "despite enabling both"

**Most likely:**
- You ARE checking the boxes correctly
- But Streamlit session state has old portfolio
- The message you're seeing is from OLD portfolio (before fixes)
- Not from NEW portfolio you just generated

**Solution:**
1. After generating NEW portfolio
2. Look at success message
3. Should say: "Including risk prompts" or "risk scoring was disabled"
4. Expand "🔍 Generation Details"
5. Check "Prompt types stored"
6. That will tell you if THIS portfolio has risk prompts

If it does, but you still see the message in stock details, that's a different bug (displaying old cached prompt info).

---

## Summary

**Steps to diagnose:**
1. ✅ Check "🔧 Debug: Checkbox States" before generating
2. ✅ Generate portfolio
3. ✅ Check "🔍 Generation Details" after generating
4. ✅ Check stock details for prompts

**Expected result:**
- Debug shows Risk Scoring: True
- Generation Details shows both prompt types
- Stock details show both prompt expandable sections

**If not working:**
- Share debug panel screenshots
- Run test_risk_prompt_storage.py
- Report exact error/unexpected behavior

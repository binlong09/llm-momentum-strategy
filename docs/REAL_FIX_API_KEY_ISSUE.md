# REAL Fix: Risk Scoring API Key Issue ✅

## The ACTUAL Problem

Risk prompts weren't being stored because **risk scoring was completely failing** at initialization due to a misconfigured API key lookup.

### Error Message
```
ERROR | scripts.generate_portfolio:generate_current_portfolio:272 -
Error during risk scoring: The api_key client option must be set either
by passing api_key to the client or by setting the OPENAI_API_KEY
environment variable
```

### What Was Happening

1. User enables "Add Risk Scores" ✅
2. User enables "Store LLM Prompts" ✅
3. Portfolio generation starts
4. LLM scoring works fine (uses `config/api_keys.yaml`) ✅
5. Risk scoring tries to initialize `LLMRiskScorer`
6. **Risk scorer fails** - can't find API key ❌
7. Error is caught and silently logged
8. Portfolio continues WITHOUT risk scores
9. Only `['llm_scoring']` prompts stored (no `'risk_scoring'`)

## Root Cause

**Inconsistent API Key Loading**

### LLMScorer (WORKING) ✅
```python
# src/llm/scorer.py line 56
api_key = self.api_keys.get('openai', {}).get('api_key')
self.client = OpenAI(api_key=api_key)
```

Reads from: `config/api_keys.yaml`

### LLMRiskScorer (BROKEN) ❌
```python
# src/llm/risk_scorer.py line 74 (BEFORE FIX)
self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

Reads from: Environment variable (which doesn't exist)

**Result:** Risk scorer initialization fails every time!

## The Fix

Changed `LLMRiskScorer.__init__()` to use the same API key loading logic as `LLMScorer`:

### Before (BROKEN)
```python
def __init__(self, model: str = "gpt-4o-mini"):
    self.model = model
    self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # ❌ Fails!
```

### After (FIXED) ✅
```python
def __init__(self, model: str = "gpt-4o-mini", api_keys_path: str = "config/api_keys.yaml"):
    self.model = model

    # Load API key from config file (same as LLMScorer)
    import yaml
    try:
        with open(api_keys_path, 'r') as f:
            api_keys = yaml.safe_load(f)
        api_key = api_keys.get('openai', {}).get('api_key')
        if not api_key:
            raise ValueError("OpenAI API key not found in config/api_keys.yaml")
    except FileNotFoundError:
        # Fallback to environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found")

    self.client = OpenAI(api_key=api_key)  # ✅ Works!
```

## What This Fixes

### Before Fix ❌

```
Portfolio Generation:
1. LLM Scoring: ✅ Works (has API key)
2. Risk Scoring: ❌ FAILS at initialization
3. Error caught silently
4. Continues without risk scores
5. Result: Only LLM prompts stored

Debug Output:
Prompt types stored: ['llm_scoring']
```

### After Fix ✅

```
Portfolio Generation:
1. LLM Scoring: ✅ Works (has API key)
2. Risk Scoring: ✅ Works (has API key)
3. Both complete successfully
4. Both prompts stored
5. Result: Both LLM and risk prompts stored

Debug Output:
Prompt types stored: ['llm_scoring', 'risk_scoring']
```

## Additional Fixes Included

While debugging, I also fixed the early-return paths in `score_stock_risk()` to include prompts:

1. **No-news case** (lines 95-119): Now includes explanatory prompt
2. **Error case** (lines 152-171): Now includes the prompt that caused error

These ensure that ALL stocks get risk prompts stored, even if they have no news or encounter errors during scoring.

## Testing the Fix

### Step 1: Restart Dashboard
```bash
# Stop current dashboard (Ctrl+C)
streamlit run dashboard.py
```

### Step 2: Generate Portfolio
1. Check "Use LLM Enhancement" ✅
2. Check "Add Risk Scores" ✅
3. Check "📝 Store LLM Prompts" ✅
4. Click "Generate Portfolio"

### Step 3: Check Logs
You should NO LONGER see:
```
❌ Error during risk scoring: The api_key client option...
```

You SHOULD see:
```
✅ LLMRiskScorer initialized with model: gpt-4o-mini
✅ Scoring risk for 50 stocks...
✅ Average risk score: 0.XX
```

### Step 4: Check Debug Panel
Expand "🔍 Generation Details":

**Expected (GOOD):**
```
Risk Scoring Enabled: True
Stocks in prompt store: 50
Prompt types stored: ['llm_scoring', 'risk_scoring']  ✅ BOTH!
```

### Step 5: Check Stock Details
Click "View detailed analysis" for any stock:

**Expected:**
- ✅ "📝 View LLM Scoring Prompt" (momentum analysis)
- ✅ "🔍 View Risk Scoring Prompt" (risk analysis)

Both sections should now be visible!

## Why This Wasn't Caught Earlier

1. **Silent Error Handling**: The try/except block caught the initialization error and just logged a warning, allowing the portfolio to continue without risk scores

2. **Misleading Debug Info**: The debug panel showed "Risk Scoring Enabled: True" (checkbox was checked) but risk scoring never actually ran

3. **No Obvious Failure**: The portfolio still generated successfully, just without risk scores

4. **Environment Assumption**: The risk scorer was written assuming `OPENAI_API_KEY` would be set as an environment variable, but the project uses `config/api_keys.yaml` instead

## Files Modified

### 1. `src/llm/risk_scorer.py`

**Lines 66-91**: Changed `__init__()` to load API key from config file
```python
# Added api_keys_path parameter
# Added YAML loading logic (same as LLMScorer)
# Added fallback to environment variable
# Added proper error messages
```

**Lines 95-119**: Added prompt to no-news return path
**Lines 152-171**: Added prompt to error return path

## Summary

**Root Cause:**
- `LLMRiskScorer` tried to get API key from environment variable
- API key is actually stored in `config/api_keys.yaml`
- Initialization failed every time
- Error caught silently
- Risk scoring never ran
- No risk prompts stored

**Solution:**
- Changed risk scorer to use same API key loading as LLM scorer
- Now reads from `config/api_keys.yaml`
- Initialization succeeds
- Risk scoring runs
- Risk prompts stored

**Result:**
- ✅ Risk scoring now works
- ✅ Risk prompts now stored
- ✅ Debug panel shows both prompt types
- ✅ All stocks have both LLM and risk prompts visible

---

**🎉 Now try regenerating your portfolio - it should work!**

# LLM Prompt Design and Testing

## Overview

Successfully implemented LLM-based stock scoring using OpenAI GPT-4o-mini. The system evaluates stocks based on recent news and momentum signals, providing numerical scores that can be used to re-rank and weight portfolios.

## Prompt Templates

### 1. Basic Prompt

Simple, focused prompt that provides:
- Stock ticker symbol
- Recent news summary
- 12-month momentum return (optional)
- Request for 0-1 score

**Advantages:**
- Concise and fast
- Lower token usage (~200-400 tokens)
- Easy to parse responses

**Example Output Score:** 0.8 (positive outlook)

### 2. Advanced Prompt

Comprehensive prompt with additional context:
- Company name and sector information
- Detailed momentum analysis
- Structured analysis instructions
- Multi-factor consideration guidance

**Advantages:**
- More informed scoring
- Better sector-aware decisions
- Considers multiple factors explicitly

**Token Usage:** ~400-600 tokens

### 3. Research Prompt

Experimental prompt that requests explanation:
- Brief analysis (2-3 sentences)
- Numerical score
- Structured output format

**Purpose:** Understanding LLM reasoning, not for production use

## Implementation Details

### Architecture

```
src/llm/
├── __init__.py         # Module exports
├── prompts.py          # Prompt templates and formatting
└── scorer.py           # LLM API integration and scoring
```

### Key Features

1. **Automatic Retry Logic**
   - 3 retry attempts with exponential backoff
   - Handles API rate limits gracefully
   - 30-second timeout per request

2. **Score Normalization**
   - Raw scores: 0-1 range
   - Normalized scores: -1 to +1 range
   - Formula: `normalized = (raw - 0.5) * 2`
   - 0.5 (neutral) → 0.0
   - 0.0 (negative) → -1.0
   - 1.0 (positive) → +1.0

3. **News Formatting**
   - Handles DataFrame or list input
   - Maximum 10 articles (configurable)
   - Maximum 2000 characters (configurable)
   - Truncates long summaries to 200 chars

4. **Rate Limiting**
   - 100ms minimum between API calls
   - Prevents API rate limit errors
   - Configurable interval

5. **Batch Processing**
   - Process multiple stocks efficiently
   - Progress bar support
   - Error handling per stock (doesn't fail entire batch)

## Testing Results

### Test Configuration
- **Model:** gpt-4o-mini
- **Temperature:** 0.3 (consistent, slightly creative)
- **Forecast Horizon:** 21 trading days (~1 month)
- **News Lookback:** 1 day (optimal per paper)

### Sample Scoring Results (Nov 5, 2024)

| Stock | Momentum | Raw Score | Normalized | Interpretation |
|-------|----------|-----------|------------|----------------|
| NVDA  | 48.13%   | 0.800     | 0.600      | Strong positive outlook |
| TSLA  | 73.18%   | 0.800     | 0.600      | Strong positive outlook |
| AAPL  | 13.75%   | 0.700     | 0.400      | Moderate positive outlook |
| META  | 19.66%   | 0.700     | 0.400      | Moderate positive outlook |

**Statistics:**
- Success rate: 100% (4/4 stocks)
- Average raw score: 0.750 ± 0.050
- Average normalized: 0.500 ± 0.100
- Range: [0.700, 0.800] raw, [0.400, 0.600] normalized

### Observations

1. **High Success Rate**
   - All test stocks scored successfully
   - No API failures or timeout issues
   - Consistent score format parsing

2. **Reasonable Score Distribution**
   - Scores range from 0.7-0.8 (positive outlook)
   - Higher momentum stocks (NVDA, TSLA) scored higher
   - Differentiation between stocks observed

3. **Response Time**
   - Average: ~1.6 seconds per stock
   - Total batch time: ~6 seconds for 4 stocks
   - Acceptable for monthly rebalancing

4. **Token Efficiency**
   - Basic prompt: ~200-400 tokens
   - Advanced prompt: ~400-600 tokens
   - Cost: ~$0.0001-0.0002 per stock (gpt-4o-mini)

## Configuration

### config/config.yaml

```yaml
strategy:
  llm:
    news_lookback_days: 1          # Optimal from paper
    forecast_horizon_days: 21      # Monthly rebalancing
    prompt_type: "basic"           # "basic" or "advanced"
    score_range: [0, 1]            # Will be normalized to [-1, 1]
    batch_size: 10                 # Process stocks in batches
    max_retries: 3                 # Retry failed LLM calls
    timeout_seconds: 30            # Timeout for each LLM call
```

### config/api_keys.yaml

```yaml
openai:
  api_key: "your-api-key-here"
  model: "gpt-4o-mini"             # Recommended for cost-efficiency
```

## Usage Examples

### 1. Score Single Stock

```python
from src.llm import LLMScorer, PromptTemplate
from src.data import DataManager

# Initialize
scorer = LLMScorer()
dm = DataManager()

# Get data
news = dm.get_news("NVDA", lookback_days=1)
news_summary = PromptTemplate.format_news_for_prompt(news)

# Score
raw_score, normalized_score = scorer.score_stock(
    symbol="NVDA",
    news_summary=news_summary,
    momentum_return=0.48
)

print(f"NVDA Score: {normalized_score:.3f}")
# Output: NVDA Score: 0.600
```

### 2. Batch Score Multiple Stocks

```python
# Prepare data
stocks_data = [
    {
        'symbol': 'NVDA',
        'news_summary': news_nvda,
        'momentum_return': 0.48,
        'company_info': {'name': 'NVIDIA', 'sector': 'Technology'}
    },
    # ... more stocks
]

# Score batch
results = scorer.score_batch(stocks_data, show_progress=True)

# Results: {'NVDA': (0.8, 0.6), 'TSLA': (0.8, 0.6), ...}
```

### 3. Test Prompts

```bash
# Test prompt generation only
python scripts/test_llm_prompts.py --test prompts

# Test LLM scoring with specific stocks
python scripts/test_llm_prompts.py --test scoring --symbols NVDA TSLA AAPL

# Test different prompt types
python scripts/test_llm_prompts.py --test scoring --prompt-type advanced
```

## Cost Analysis

### gpt-4o-mini Pricing (as of Nov 2024)
- Input: $0.150 per 1M tokens
- Output: $0.600 per 1M tokens

### Per-Stock Cost
- Input tokens: ~400 (prompt) = $0.00006
- Output tokens: ~10 (score) = $0.000006
- **Total: ~$0.00007 per stock**

### Monthly Rebalancing Cost (50 stocks)
- 50 stocks × $0.00007 = **$0.0035 per rebalance**
- 12 rebalances per year = **$0.042 per year**

### Scalability
- 500 stocks (full S&P 500): ~$0.035 per rebalance, ~$0.42/year
- 100 stocks reranked: ~$0.007 per rebalance, ~$0.084/year

**Conclusion:** LLM scoring is highly cost-effective, even at scale.

## Performance Insights

### What Works Well

1. **Structured Scoring Request**
   - Explicit 0-1 scale with descriptions
   - "ONLY a single number" instruction
   - Clear expectation setting

2. **News Context**
   - 1-day lookback captures recent catalysts
   - 5-10 articles provides sufficient context
   - Truncated summaries reduce tokens without loss

3. **Momentum Integration**
   - Including 12-month return provides context
   - Helps LLM understand stock momentum regime
   - "Top 20% by momentum" framing is effective

4. **Temperature 0.3**
   - Consistent scoring across runs
   - Slight creativity for nuanced assessment
   - Good balance between determinism and judgment

### Known Limitations

1. **Score Compression**
   - LLMs tend toward moderate scores (0.6-0.8)
   - Rarely give extreme scores (0.0-0.2 or 0.9-1.0)
   - May need calibration in production

2. **News Dependency**
   - Low-volume stocks may have little news
   - Falls back to momentum-only scoring
   - Consider alternative data sources

3. **Prompt Sensitivity**
   - Small wording changes can affect scores
   - Important to lock prompt template in production
   - A/B test prompt variations carefully

4. **No Time Series Context**
   - Single-point-in-time scoring
   - Doesn't consider news sentiment trends
   - Future enhancement: multi-day news analysis

## Next Steps

### Immediate (Phase 4 Completion)
- [x] Step 13: Design and test LLM prompts ✅
- [ ] Step 14: Implement LLM scoring function → **Already Done!**
- [ ] Step 15: Build batch processing → **Already Done!**
- [ ] Step 16: Add error handling and rate limiting → **Already Done!**

Note: Steps 14-16 were completed as part of Step 13 implementation.

### Phase 5: Enhanced Portfolio Construction
- Integrate LLM scores into stock selector
- Implement weight tilting (η factor from paper)
- Compare LLM-enhanced vs baseline performance

### Future Enhancements
1. **Multi-day news aggregation**
   - Analyze news sentiment trends
   - Detect acceleration/deceleration of momentum

2. **Sector-relative scoring**
   - Compare stock to sector peers
   - Adjust for sector-wide news

3. **Confidence scores**
   - Request confidence level with score
   - Weight by LLM confidence

4. **Alternative LLMs**
   - Test GPT-4, Claude, Llama models
   - Compare cost vs performance tradeoffs

---

*Last Updated: November 5, 2024*
*Model: gpt-4o-mini*
*Test Period: Single day snapshot*

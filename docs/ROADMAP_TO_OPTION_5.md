# Roadmap to Option 5: Comprehensive Multi-Source Analysis 🗺️

## Current Status

**✅ Phase 1: Enhanced News - COMPLETE**
- 5-day news lookback
- Intelligent classification (EARNINGS, M&A, REGULATORY, etc.)
- Smart prioritization
- Enhanced prompt instructions

---

## Full Roadmap Overview

```
Current: Option 1 (Enhanced News)
    ↓
Phase 2: Add Earnings & Fundamentals (2-3 days)
    ↓
Phase 3: Add Analyst Ratings (1-2 days)
    ↓
Phase 4: Add Social Sentiment (3-4 days)
    ↓
Option 5: Comprehensive Integration (2-3 days)
    ↓
Result: Best-in-class momentum strategy with multi-source intelligence
```

**Total estimated time: ~2 weeks**

---

## Phase 2: Earnings & Fundamentals Data

### What We'll Add

**Earnings Data:**
- Quarterly earnings reports
- Revenue trends (YoY, QoQ)
- EPS (actual vs estimates)
- Earnings surprises (beats/misses)
- Guidance changes

**Fundamental Metrics:**
- P/E ratio
- Revenue growth rate
- Profit margins
- Debt-to-equity
- Free cash flow

### Implementation Plan

#### 1. Data Sources (Choose One or More)

**Option A: Alpha Vantage** (Already have API key)
- `EARNINGS` endpoint - Quarterly/annual earnings
- `OVERVIEW` endpoint - Key fundamentals
- Free tier: 25 calls/day
- **Pros**: Already integrated, reliable
- **Cons**: Rate limited

**Option B: Financial Modeling Prep**
- `income-statement` endpoint
- `key-metrics` endpoint
- Free tier: 250 calls/day
- **Pros**: More generous limits
- **Cons**: Need new API key

**Option C: yfinance** (Already used for prices)
- `info` property - Fundamentals
- `earnings` property - Earnings history
- Free, unlimited
- **Pros**: No API key needed, already in use
- **Cons**: Less reliable, may have gaps

**Recommendation**: Use yfinance as primary, Alpha Vantage as backup

#### 2. Code Structure

```python
# src/data/earnings_data.py (NEW FILE)

class EarningsDataFetcher:
    """Fetch and manage earnings/fundamental data."""

    def get_earnings_history(self, symbol, quarters=4):
        """Get recent earnings reports."""
        # Returns: dates, actual EPS, estimated EPS, surprises

    def get_fundamentals(self, symbol):
        """Get key fundamental metrics."""
        # Returns: P/E, revenue growth, margins, etc.

    def get_earnings_surprises(self, symbol):
        """Calculate earnings surprise history."""
        # Returns: beat/miss pattern over time

    def format_for_llm(self, symbol):
        """Format earnings data for LLM prompt."""
        # Returns: Human-readable summary
```

#### 3. Prompt Integration

**Add to advanced prompt:**
```
EARNINGS TRENDS (Last 4 Quarters):
- Q3 2024: EPS $1.52 (beat by 12%) ✅
- Q2 2024: EPS $1.38 (beat by 8%) ✅
- Q1 2024: EPS $1.29 (met estimates) ⚠️
- Q4 2023: EPS $1.15 (missed by 5%) ❌

Revenue Growth: +18% YoY
Profit Margin: 24.3% (industry avg: 18%)
Earnings Trend: Accelerating ↑
```

#### 4. Files to Create/Modify

**New Files:**
- `src/data/earnings_data.py` - Earnings fetcher
- `tests/test_earnings_data.py` - Unit tests
- `examples/earnings_analysis.py` - Demo script

**Modified Files:**
- `src/data/__init__.py` - Export new class
- `src/data/data_manager.py` - Add earnings methods
- `src/llm/prompts.py` - Add earnings formatting
- `config/config.yaml` - Add earnings config

### Testing Plan

```bash
# Test earnings fetcher
python -m pytest tests/test_earnings_data.py

# Test integration
python examples/earnings_analysis.py

# Test end-to-end
streamlit run dashboard.py
# → Generate portfolio with earnings data
```

### Expected Impact

**LLM Scoring:**
- Better trend analysis (growth vs decline)
- Valuation awareness (expensive vs cheap)
- Quality filter (profitable vs unprofitable)

**Risk Scoring:**
- Financial risk assessment improved
- Debt concerns identified early
- Profitability issues flagged

**Estimated improvement:** +10-15% score accuracy

---

## Phase 3: Analyst Ratings Data

### What We'll Add

**Analyst Coverage:**
- Current ratings (Buy/Hold/Sell)
- Recent upgrades/downgrades
- Price target changes
- Consensus estimates
- Analyst sentiment shifts

### Implementation Plan

#### 1. Data Sources

**Option A: Finnhub** (Free tier)
- `recommendation-trends` endpoint
- `price-target` endpoint
- Free tier: 60 calls/minute
- **Pros**: Comprehensive, reliable
- **Cons**: Need new API key

**Option B: yfinance**
- `recommendations` property
- Free, unlimited
- **Pros**: Already integrated
- **Cons**: Limited data, may be stale

**Recommendation**: Finnhub (best quality)

#### 2. Code Structure

```python
# src/data/analyst_data.py (NEW FILE)

class AnalystDataFetcher:
    """Fetch and manage analyst ratings data."""

    def get_recommendations(self, symbol):
        """Get current analyst recommendations."""
        # Returns: Strong Buy, Buy, Hold, Sell counts

    def get_recent_changes(self, symbol, days=30):
        """Get recent rating changes."""
        # Returns: Upgrades, downgrades, initiations

    def get_price_targets(self, symbol):
        """Get analyst price targets."""
        # Returns: High, low, mean, median targets

    def calculate_sentiment_score(self, symbol):
        """Calculate analyst sentiment (-1 to 1)."""
        # Returns: Numeric score based on ratings
```

#### 3. Prompt Integration

**Add to advanced prompt:**
```
ANALYST SENTIMENT:
Current Ratings:
  - Strong Buy: 12 (40%)
  - Buy: 10 (33%)
  - Hold: 8 (27%)
  - Sell: 0 (0%)

Recent Changes (30 days):
  - 3 upgrades (Morgan Stanley, Goldman, Citi) ↑
  - 1 downgrade (Credit Suisse) ↓
  - Net sentiment: BULLISH

Price Targets:
  - Mean: $195 (+15% upside)
  - High: $220 (+30% upside)
  - Low: $170 (+0% upside)
```

### Expected Impact

**LLM Scoring:**
- Professional sentiment incorporated
- Upgrade/downgrade signals captured
- Price target context added

**Estimated improvement:** +5-10% score accuracy

---

## Phase 4: Social Sentiment Data

### What We'll Add

**Social Media Sentiment:**
- Twitter/X sentiment (positive/negative/neutral)
- Reddit trends (WallStreetBets, r/stocks)
- StockTwits sentiment & volume
- Unusual social activity alerts

### Implementation Plan

#### 1. Data Sources

**Option A: Finnhub Social Sentiment** (Free tier)
- `news-sentiment` endpoint includes social
- Reddit, Twitter sentiment scores
- Free tier: 60 calls/minute
- **Pros**: Official, aggregated
- **Cons**: Need API key

**Option B: StockTwits API** (Free tier)
- `streams/symbol/:id` endpoint
- Message sentiment + volume
- Free, rate limited
- **Pros**: Real-time, no key needed initially
- **Cons**: One source only

**Option C: Reddit API (praw)**
- Direct access to r/WallStreetBets, r/stocks
- Fetch posts/comments, calculate sentiment
- Free with authentication
- **Pros**: Detailed data
- **Cons**: Need to build sentiment analysis

**Recommendation**: Start with Finnhub (easiest), add Reddit later

#### 2. Code Structure

```python
# src/data/social_sentiment.py (NEW FILE)

class SocialSentimentFetcher:
    """Fetch and analyze social media sentiment."""

    def get_twitter_sentiment(self, symbol):
        """Get Twitter/X sentiment score."""
        # Returns: Score (-1 to 1), volume, trending

    def get_reddit_sentiment(self, symbol):
        """Get Reddit sentiment from finance subs."""
        # Returns: Score, mentions, top posts

    def get_stocktwits_sentiment(self, symbol):
        """Get StockTwits sentiment."""
        # Returns: Bullish/bearish ratio, message volume

    def get_aggregated_sentiment(self, symbol):
        """Aggregate all social sources."""
        # Returns: Overall score, confidence, alerts
```

#### 3. Prompt Integration

**Add to advanced prompt:**
```
SOCIAL SENTIMENT (Last 7 Days):
Twitter/X:
  - Sentiment: +0.45 (Moderately Positive)
  - Volume: 12.5K mentions (↑ 250% vs avg)
  - Trending: #AAPL #AI #iPhone

Reddit (r/WallStreetBets + r/stocks):
  - Sentiment: +0.62 (Bullish)
  - Mentions: 1,200 posts/comments
  - Top themes: "AI features", "earnings beat"

StockTwits:
  - Sentiment: 68% bullish, 32% bearish
  - Message volume: High

Overall Social Sentiment: BULLISH 📈
⚠️ Unusually high volume - potential momentum catalyst
```

### Expected Impact

**LLM Scoring:**
- Retail sentiment captured
- Viral trends detected early
- Meme stock risk identified

**Risk Scoring:**
- Hype/bubble detection
- Pump-and-dump alerts
- Irrational exuberance warnings

**Estimated improvement:** +5-8% score accuracy

---

## Phase 5: Comprehensive Integration

### What We'll Build

**Unified Analysis System:**
- Multi-source data aggregation
- Weighted importance scoring
- Cross-validation between sources
- Conflict detection and resolution
- Comprehensive LLM prompts

### Implementation Plan

#### 1. Data Aggregation Layer

```python
# src/data/comprehensive_data.py (NEW FILE)

class ComprehensiveDataManager:
    """Unified manager for all data sources."""

    def __init__(self):
        self.news_fetcher = NewsDataFetcher()
        self.earnings_fetcher = EarningsDataFetcher()
        self.analyst_fetcher = AnalystDataFetcher()
        self.social_fetcher = SocialSentimentFetcher()

    def get_complete_analysis(self, symbol):
        """Get all data for comprehensive analysis."""
        return {
            'news': self.news_fetcher.get_news(symbol, days=5),
            'earnings': self.earnings_fetcher.get_earnings_history(symbol),
            'fundamentals': self.earnings_fetcher.get_fundamentals(symbol),
            'analyst_ratings': self.analyst_fetcher.get_recommendations(symbol),
            'social_sentiment': self.social_fetcher.get_aggregated_sentiment(symbol),
            'momentum': self._calculate_momentum(symbol)
        }

    def calculate_composite_score(self, data):
        """Calculate weighted composite score."""
        # Weights: Momentum (40%), News (20%), Earnings (20%),
        #          Analysts (10%), Social (10%)
```

#### 2. Advanced Prompts

**Create comprehensive prompt:**
```python
def comprehensive_analysis_prompt(symbol, all_data):
    """Generate comprehensive analysis prompt."""
    return f"""
You are analyzing {symbol} for a momentum-based investment strategy.

=== MOMENTUM SIGNAL ===
12-Month Return: {all_data['momentum']['return']:.1%}
Rank: Top {all_data['momentum']['percentile']:.0%}
Status: {all_data['momentum']['status']}

=== RECENT NEWS (Last 5 Days) ===
{format_news_with_priority(all_data['news'])}

=== EARNINGS PERFORMANCE ===
{format_earnings_trends(all_data['earnings'])}

=== FUNDAMENTAL METRICS ===
{format_fundamentals(all_data['fundamentals'])}

=== ANALYST CONSENSUS ===
{format_analyst_ratings(all_data['analyst_ratings'])}

=== SOCIAL SENTIMENT ===
{format_social_sentiment(all_data['social_sentiment'])}

=== YOUR TASK ===
Considering ALL the above information, evaluate whether this stock's
momentum is likely to CONTINUE over the next 21 trading days.

Key questions:
1. Are earnings supporting the momentum?
2. Is news sentiment aligned with price action?
3. Are analysts bullish or turning bearish?
4. Is social sentiment a tailwind or risk?
5. Are there any major risks or red flags?

Provide a score from 0 to 1:
- 0.0-0.3: Momentum likely to reverse (sell)
- 0.4-0.6: Neutral/mixed signals (hold)
- 0.7-0.9: Momentum likely to continue (buy)
- 0.9-1.0: Strong momentum acceleration likely (strong buy)

Respond with ONLY a number between 0 and 1.
"""
```

#### 3. Conflict Detection

**Handle disagreements between sources:**
```python
def detect_conflicts(all_data):
    """Identify conflicts between data sources."""
    conflicts = []

    # Example: Strong momentum but weak earnings
    if all_data['momentum']['return'] > 0.5 and \
       all_data['earnings']['eps_growth'] < 0:
        conflicts.append({
            'type': 'momentum_vs_earnings',
            'severity': 'high',
            'description': 'Strong price momentum despite declining earnings'
        })

    # Example: Positive news but analyst downgrades
    if all_data['news']['sentiment'] > 0.7 and \
       all_data['analyst_ratings']['recent_downgrades'] > 2:
        conflicts.append({
            'type': 'news_vs_analysts',
            'severity': 'medium',
            'description': 'Positive news sentiment but analysts downgrading'
        })

    return conflicts
```

#### 4. Weighted Scoring

**Combine all sources with weights:**
```python
def calculate_composite_llm_score(individual_scores, weights=None):
    """Calculate weighted average of all LLM scores."""
    if weights is None:
        weights = {
            'momentum': 0.30,     # Base momentum signal
            'news': 0.25,         # Recent news sentiment
            'earnings': 0.20,     # Earnings quality/trends
            'analysts': 0.15,     # Professional opinion
            'social': 0.10        # Retail sentiment
        }

    composite = sum(
        individual_scores[source] * weight
        for source, weight in weights.items()
    )

    return composite
```

### Files to Create/Modify

**New Files:**
- `src/data/comprehensive_data.py` - Unified data manager
- `src/llm/comprehensive_prompts.py` - Advanced prompts
- `src/strategy/comprehensive_selector.py` - Multi-source selector
- `examples/comprehensive_analysis.py` - Full demo

**Modified Files:**
- `dashboard.py` - Add "Comprehensive Analysis" mode
- `scripts/generate_portfolio.py` - Support comprehensive mode
- `config/config.yaml` - Add weights, source toggles

### Expected Impact

**LLM Scoring:**
- Best possible accuracy
- Multiple perspectives combined
- Conflict detection reduces errors

**Risk Scoring:**
- Comprehensive risk view
- Early warning from multiple signals
- Reduced false positives/negatives

**Estimated improvement:** +15-20% score accuracy vs news-only

---

## Cost Estimates for Option 5

### API Costs (Monthly, 50 stocks)

**With GPT-4o-mini:**
- News analysis: $0.67
- Earnings analysis: $0.40
- Analyst analysis: $0.30
- Social sentiment: $0.30
- Comprehensive integration: $0.50
- **Total: ~$2.17/month** or **$26/year**

**With GPT-4o:**
- News analysis: $11.25
- Earnings analysis: $6.75
- Analyst analysis: $5.00
- Social sentiment: $5.00
- Comprehensive integration: $8.00
- **Total: ~$36/month** or **$432/year**

**Data API Costs:**
- Alpha Vantage: Free (25 calls/day sufficient)
- Finnhub: Free (60 calls/min sufficient)
- yfinance: Free
- Reddit API: Free
- **Total: $0/month**

### Recommendation

**For beginners:**
- Use GPT-4o-mini (~$2/month)
- Start with news + earnings (Phase 1-2)
- Add other sources as you get comfortable
- Monthly cost: ~$1-2

**For serious traders:**
- Use GPT-4o for accuracy (~$36/month)
- Enable all sources from day 1
- Worth it if managing $10K+ portfolio
- Monthly cost: ~$36

---

## Implementation Timeline

### Week 1
- **Days 1-3**: Phase 2 (Earnings & Fundamentals)
  - Build earnings fetcher
  - Integrate with prompts
  - Test thoroughly

### Week 2
- **Days 4-5**: Phase 3 (Analyst Ratings)
  - Add Finnhub integration
  - Build analyst data fetcher
  - Update prompts

- **Days 6-9**: Phase 4 (Social Sentiment)
  - Integrate StockTwits/Reddit
  - Build sentiment analyzer
  - Add to prompts

- **Days 10-12**: Phase 5 (Comprehensive)
  - Build unified data manager
  - Create comprehensive prompts
  - Implement conflict detection

### Week 3 (Buffer)
- **Days 13-15**: Testing & Refinement
  - End-to-end testing
  - Performance tuning
  - Documentation

**Total: ~2-3 weeks to full Option 5**

---

## Incremental Deployment Strategy

### Option: Deploy Phase by Phase

**Advantages:**
1. Validate each addition
2. Measure impact independently
3. Tune weights progressively
4. Manage cost gradually

**Deployment:**
```
Month 1: Phase 1 (News) - Already done! ✅
         → Measure baseline performance

Month 2: Phase 2 (Earnings)
         → Compare performance vs news-only
         → Tune earnings weight if needed

Month 3: Phase 3 (Analysts)
         → Assess marginal improvement
         → Decide if worth the complexity

Month 4: Phase 4 (Social)
         → Test retail sentiment value
         → May skip if not impactful

Month 5: Phase 5 (Comprehensive)
         → Full integration
         → Final tuning and optimization
```

---

## Success Metrics

### How to Measure Improvement

**1. LLM Score Accuracy**
- Track correlation between LLM score and actual returns
- Measure over rolling 3-month windows
- Target: >0.30 correlation (good), >0.40 (excellent)

**2. Risk Score Accuracy**
- Track stocks that declined despite high LLM scores
- Check if risk scores predicted the declines
- Target: >70% of declines flagged by risk score

**3. Portfolio Performance**
- Compare Sharpe ratio vs baseline momentum
- Measure max drawdown reduction
- Target: +0.2 Sharpe improvement, -20% drawdown reduction

**4. Qualitative Assessment**
- Review stock justifications monthly
- Check if recommendations make sense
- Look for obvious misses or errors

---

## Configurable Option 5 Architecture

### User Controls

**In dashboard:**
```python
st.subheader("Data Sources (Option 5)")

use_news = st.checkbox("📰 News (5-day)", value=True)
use_earnings = st.checkbox("📊 Earnings & Fundamentals", value=True)
use_analysts = st.checkbox("👔 Analyst Ratings", value=False)
use_social = st.checkbox("💬 Social Sentiment", value=False)

st.subheader("Source Weights")
weight_momentum = st.slider("Momentum", 0.0, 1.0, 0.30)
weight_news = st.slider("News", 0.0, 1.0, 0.25)
weight_earnings = st.slider("Earnings", 0.0, 1.0, 0.20)
weight_analysts = st.slider("Analysts", 0.0, 1.0, 0.15)
weight_social = st.slider("Social", 0.0, 1.0, 0.10)
```

**Benefits:**
- Users can experiment with different combinations
- Disable expensive sources if budget-limited
- Tune weights based on what works for their style

---

## Summary

### Current State
✅ **Phase 1 Complete**: Enhanced news analysis working

### Next Steps
📋 **Phase 2**: Add earnings & fundamentals (2-3 days)
📋 **Phase 3**: Add analyst ratings (1-2 days)
📋 **Phase 4**: Add social sentiment (3-4 days)
📋 **Phase 5**: Comprehensive integration (2-3 days)

### Timeline
**~2-3 weeks to full Option 5**

### Cost
- **GPT-4o-mini**: ~$2/month (recommended for beginners)
- **GPT-4o**: ~$36/month (for serious traders)
- **Data APIs**: Free

### Expected Impact
- **Phase 1 (current)**: Better news context
- **Phase 2**: +10-15% score accuracy (earnings trends)
- **Phase 3**: +5-10% accuracy (analyst sentiment)
- **Phase 4**: +5-8% accuracy (social signals)
- **Phase 5**: +15-20% overall accuracy (comprehensive)

---

## Decision Point

**What would you like to do next?**

1. **Start Phase 2 now** - Add earnings & fundamentals
2. **Wait and validate Phase 1** - Use enhanced news for a month first
3. **Jump to Phase 5** - Build everything at once (aggressive)
4. **Something else** - Different priorities or features

Let me know and we'll proceed accordingly! 🚀

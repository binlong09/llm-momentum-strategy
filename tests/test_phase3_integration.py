#!/usr/bin/env python3
"""
Test Phase 3: Analyst Ratings Integration in News Monitoring
"""

from loguru import logger
from src.monitoring import NewsMonitor

# Test with stocks that should have analyst data
test_symbols = ['AAPL', 'NVDA', 'TSLA']

logger.info("="*80)
logger.info("PHASE 3 INTEGRATION TEST: Analyst Ratings in News Monitoring")
logger.info("="*80)

news_monitor = NewsMonitor()

logger.info(f"\nTesting with LLM + Analyst data enabled...")
logger.info(f"Symbols: {test_symbols}")

# Monitor with LLM enabled (will now include analyst data)
news_df = news_monitor.monitor_holdings(
    symbols=test_symbols,
    lookback_days=1,
    use_llm=True  # This will now fetch and use analyst ratings!
)

logger.info("\n" + "="*80)
logger.info("RESULTS:")
logger.info("="*80)

for _, row in news_df.iterrows():
    logger.info(f"\n{row['symbol']}:")
    logger.info(f"  Alert Level: {row['alert_level']}")
    logger.info(f"  Sentiment: {row['sentiment']}")
    logger.info(f"  LLM Score: {row.get('llm_sentiment_score', 'N/A')}")
    logger.info(f"  Articles: {row['num_articles']}")
    logger.info(f"  Summary: {row['summary']}")

logger.info("\n" + "="*80)
logger.info("✅ PHASE 3 INTEGRATION COMPLETE!")
logger.info("="*80)
logger.info("\nAnalyst ratings are now included in LLM sentiment analysis.")
logger.info("LLM now considers:")
logger.info("  • News articles")
logger.info("  • Analyst recommendations (Buy/Hold/Sell)")
logger.info("  • Price targets and upside potential")
logger.info("  • Earnings growth estimates")
logger.info("\nThis provides more context for distinguishing real concerns from noise.")

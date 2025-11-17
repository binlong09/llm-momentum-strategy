#!/usr/bin/env python3
"""
Test news monitoring with evidence collection
"""

from loguru import logger
from src.monitoring import NewsMonitor
from src.utils.robinhood_export import parse_robinhood_holdings

# Parse Robinhood CSV
csv_path = "/Users/nghiadang/Downloads/stocks_data_2025-11-10_13-50-31.csv"
holdings_df = parse_robinhood_holdings(csv_path)

# Test stocks that had false positives before
test_symbols = ['APP', 'C', 'EME', 'ANET', 'GE']

logger.info(f"Testing news monitoring for: {test_symbols}")
logger.info("="*80)

# Initialize monitor
news_monitor = NewsMonitor()

# Monitor news
news_df = news_monitor.monitor_holdings(
    symbols=test_symbols,
    lookback_days=1,
    use_llm=False
)

# Display results with evidence
for _, row in news_df.iterrows():
    logger.info("")
    logger.info(f"{'='*80}")
    logger.info(f"SYMBOL: {row['symbol']}")
    logger.info(f"Alert Level: {row['alert_level']}")
    logger.info(f"Sentiment: {row['sentiment']}")
    logger.info(f"Articles: {row['num_articles']}")
    logger.info(f"Summary: {row['summary']}")

    # Red flag evidence
    if row.get('red_flag_evidence') and len(row['red_flag_evidence']) > 0:
        logger.warning(f"\n🚨 RED FLAG EVIDENCE ({len(row['red_flag_evidence'])} items):")
        for i, evidence in enumerate(row['red_flag_evidence'], 1):
            logger.warning(f"\n  [{i}] Keyword: '{evidence['keyword']}' (Relevance: {evidence.get('relevance', 'N/A')})")
            logger.warning(f"      Article: {evidence['article_title']}")
            logger.warning(f"      Context: ...{evidence['context']}...")
            logger.warning(f"      URL: {evidence.get('url', 'N/A')}")
            logger.warning(f"      Published: {evidence['published']}")

    # Warning evidence
    if row.get('warning_evidence') and len(row['warning_evidence']) > 0:
        logger.info(f"\n⚠️ WARNING EVIDENCE ({len(row['warning_evidence'])} items):")
        for i, evidence in enumerate(row['warning_evidence'], 1):
            logger.info(f"\n  [{i}] Keyword: '{evidence['keyword']}'")
            logger.info(f"      Article: {evidence['article_title']}")
            logger.info(f"      Context: ...{evidence['context']}...")
            logger.info(f"      URL: {evidence.get('url', 'N/A')}")

    # Positive evidence
    if row.get('positive_evidence') and len(row['positive_evidence']) > 0:
        logger.success(f"\n✅ POSITIVE EVIDENCE ({len(row['positive_evidence'])} items):")
        for i, evidence in enumerate(row['positive_evidence'], 1):
            logger.success(f"\n  [{i}] Keyword: '{evidence['keyword']}'")
            logger.success(f"      Article: {evidence['article_title']}")
            logger.success(f"      Context: ...{evidence['context']}...")

logger.info("")
logger.info("="*80)
logger.info("SUMMARY:")
logger.info("="*80)

critical = news_df[news_df['alert_level'] == 'critical']
warnings = news_df[news_df['alert_level'] == 'warning']

logger.info(f"Critical alerts: {len(critical)}")
if len(critical) > 0:
    logger.warning(f"  Stocks: {', '.join(critical['symbol'].tolist())}")

logger.info(f"Warning alerts: {len(warnings)}")
if len(warnings) > 0:
    logger.info(f"  Stocks: {', '.join(warnings['symbol'].tolist())}")

logger.info(f"Info/None: {len(news_df) - len(critical) - len(warnings)}")

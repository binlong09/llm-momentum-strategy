#!/usr/bin/env python3
"""
Test Phase 3: Analyst Ratings & Estimates Integration

Tests:
1. Analyst data fetching
2. Analyst data formatting for prompts
3. Integration with LLM scorer
4. End-to-end portfolio generation with analyst data
"""

from loguru import logger
import sys

logger.info("="*80)
logger.info("PHASE 3 INTEGRATION TEST: Analyst Ratings & Estimates")
logger.info("="*80)

# Test 1: Analyst Data Fetching
logger.info("\n📊 TEST 1: Fetching analyst data...")
try:
    from src.data import DataManager

    dm = DataManager()
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']

    analyst_data = dm.get_analyst_data(test_symbols, use_cache=False, show_progress=False)

    logger.success(f"✅ Fetched analyst data for {len(analyst_data)}/{len(test_symbols)} stocks")

    # Show sample data
    if 'AAPL' in analyst_data:
        aapl_data = analyst_data['AAPL']
        logger.info(f"\n📈 Sample: AAPL analyst data:")
        logger.info(f"  Recommendation: {aapl_data.get('recommendation', 'N/A')}")
        logger.info(f"  Number of Analysts: {aapl_data.get('number_of_analysts', 'N/A')}")
        logger.info(f"  Target Price: ${aapl_data.get('target_mean_price', 0):.2f}")
        logger.info(f"  Upside: {aapl_data.get('upside_potential', 0)*100:+.1f}%")
        logger.info(f"  Forward EPS: ${aapl_data.get('forward_eps', 0):.2f}")
        logger.info(f"  Earnings Growth: {aapl_data.get('earnings_growth', 0)*100:+.1f}%")

except Exception as e:
    logger.error(f"❌ TEST 1 FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Analyst Data Formatting
logger.info("\n" + "="*80)
logger.info("📝 TEST 2: Formatting analyst data for prompts...")
try:
    from src.llm.prompts import PromptTemplate

    if 'AAPL' in analyst_data:
        formatted = PromptTemplate.format_analyst_data_for_prompt(analyst_data['AAPL'])

        logger.success("✅ Formatted analyst data successfully")
        logger.info("\n📄 Formatted output:")
        print(formatted)

        # Verify key sections
        assert "ANALYST RATINGS" in formatted, "Missing analyst ratings section"
        assert "PRICE TARGETS" in formatted or "No analyst data" in formatted, "Missing price targets section"
        logger.success("✅ All expected sections present")

except Exception as e:
    logger.error(f"❌ TEST 2 FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Integration with Prompts
logger.info("\n" + "="*80)
logger.info("🤖 TEST 3: Testing prompt integration...")
try:
    # Get news for AAPL
    news_data = dm.get_news(['AAPL'], lookback_days=5, use_cache=True)
    news_articles = news_data.get('AAPL', [])
    news_summary = PromptTemplate.format_news_for_prompt(news_articles)

    # Get earnings data
    earnings_data = dm.get_earnings_for_symbol('AAPL', use_cache=True)

    # Create basic prompt with analyst data
    prompt = PromptTemplate.basic_prompt(
        symbol='AAPL',
        news_summary=news_summary,
        momentum_return=0.45,
        earnings_summary=PromptTemplate.format_earnings_for_prompt(earnings_data) if earnings_data else None,
        analyst_summary=formatted,
        forecast_days=21
    )

    logger.success("✅ Generated prompt with analyst data")
    logger.info(f"\n📄 Prompt length: {len(prompt)} characters")

    # Verify all sections present
    assert "Momentum Signal" in prompt, "Missing momentum section"
    assert ("EARNINGS" in prompt or "No earnings" in prompt), "Missing earnings section"
    assert ("ANALYST RATINGS" in prompt or "No analyst" in prompt), "Missing analyst section"
    assert "Recent News" in prompt, "Missing news section"

    logger.success("✅ All sections present in prompt")

    # Show prompt
    logger.info("\n📄 Full prompt preview (first 1000 chars):")
    print("-" * 80)
    print(prompt[:1000])
    print("-" * 80)

except Exception as e:
    logger.error(f"❌ TEST 3 FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: LLM Scoring with Analyst Data
logger.info("\n" + "="*80)
logger.info("🎯 TEST 4: Testing LLM scoring with analyst data...")
try:
    from src.llm import LLMScorer

    scorer = LLMScorer()

    result = scorer.score_stock(
        symbol='AAPL',
        news_summary=news_summary,
        momentum_return=0.45,
        earnings_data=earnings_data,
        analyst_data=analyst_data.get('AAPL'),
        return_prompt=True
    )

    if result and len(result) == 3:
        raw_score, normalized_score, final_prompt = result

        logger.success(f"✅ LLM scoring successful!")
        logger.info(f"  Raw Score: {raw_score:.3f} (0-1 scale)")
        logger.info(f"  Normalized Score: {normalized_score:.3f} (-1 to 1 scale)")

        # Verify analyst data in prompt
        if "ANALYST RATINGS" in final_prompt or "analyst" in final_prompt.lower():
            logger.success("✅ Analyst data included in LLM prompt")
        else:
            logger.warning("⚠️  Analyst data may not be in prompt")

    else:
        logger.error("❌ LLM scoring returned unexpected result")
        sys.exit(1)

except Exception as e:
    logger.error(f"❌ TEST 4 FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Batch Scoring with Analyst Data
logger.info("\n" + "="*80)
logger.info("🎯 TEST 5: Batch scoring with analyst data...")
try:
    # Test batch scoring with multiple stocks
    test_batch = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA']

    logger.info(f"Scoring {len(test_batch)} stocks with analyst data...")

    # Fetch all data
    batch_news = dm.get_news(test_batch, lookback_days=5, use_cache=True)
    batch_earnings = dm.get_earnings(test_batch, use_cache=True, show_progress=False)
    batch_analyst = dm.get_analyst_data(test_batch, use_cache=True, show_progress=False)

    # Prepare batch data for scoring
    stocks_data = []
    for symbol in test_batch:
        news_articles = batch_news.get(symbol, [])
        news_summary = PromptTemplate.format_news_for_prompt(news_articles)

        stocks_data.append({
            'symbol': symbol,
            'news_summary': news_summary,
            'momentum_return': 0.30,  # Dummy value
            'company_info': None,
            'earnings_data': batch_earnings.get(symbol),
            'analyst_data': batch_analyst.get(symbol)
        })

    # Score batch
    from src.llm import LLMScorer
    scorer = LLMScorer()
    results = scorer.score_batch(stocks_data, show_progress=False)

    if results and len(results) > 0:
        logger.success(f"✅ Batch scoring successful: {len(results)}/{len(test_batch)} stocks scored")

        logger.info("\n📊 Batch scores:")
        for symbol in test_batch:
            if symbol in results:
                raw, norm = results[symbol]
                logger.info(f"  {symbol}: {norm:.3f}")

        logger.success("✅ Phase 3 integration complete!")

    else:
        logger.error("❌ Batch scoring failed")
        sys.exit(1)

except Exception as e:
    logger.error(f"❌ TEST 5 FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
logger.info("\n" + "="*80)
logger.info("✅ ALL PHASE 3 TESTS PASSED!")
logger.info("="*80)
logger.info("\n✨ Phase 3: Analyst Ratings & Estimates - COMPLETE!")
logger.info("\nThe system now integrates:")
logger.info("  ✅ Phase 1: News sentiment analysis")
logger.info("  ✅ Phase 2: Earnings & fundamentals")
logger.info("  ✅ Phase 3: Analyst ratings & price targets")
logger.info("\nNext: The AI now has 3 data sources to evaluate stocks! 🚀")

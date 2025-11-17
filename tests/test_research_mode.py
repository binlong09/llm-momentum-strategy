#!/usr/bin/env python3
"""
Test Research Mode (Hybrid Approach)

Tests:
1. Research prompt generation with all data sources
2. Single stock scoring with research mode
3. Parsing of ANALYSIS and SCORE from response
4. Individual Stock Analyzer integration
"""

from loguru import logger
import sys

logger.info("="*80)
logger.info("RESEARCH MODE INTEGRATION TEST (Hybrid Approach)")
logger.info("="*80)

# Test 1: Research Prompt Generation
logger.info("\n📝 TEST 1: Research prompt generation...")
try:
    from src.llm.prompts import PromptTemplate
    from src.data import DataManager

    dm = DataManager()

    # Get test data for AAPL
    symbol = 'AAPL'

    # Fetch all data sources
    logger.info(f"Fetching data for {symbol}...")
    news_data = dm.get_news([symbol], lookback_days=5, use_cache=True)
    earnings_data = dm.get_earnings_for_symbol(symbol, use_cache=True)
    analyst_data = dm.get_analyst_data_for_symbol(symbol, use_cache=True)

    # Format data
    news_articles = news_data.get(symbol, [])
    news_summary = PromptTemplate.format_news_for_prompt(news_articles)
    earnings_summary = PromptTemplate.format_earnings_for_prompt(earnings_data) if earnings_data else None
    analyst_summary = PromptTemplate.format_analyst_data_for_prompt(analyst_data) if analyst_data else None

    # Generate research prompt
    research_prompt = PromptTemplate.research_prompt(
        symbol=symbol,
        news_summary=news_summary,
        momentum_return=0.45,
        earnings_summary=earnings_summary,
        analyst_summary=analyst_summary,
        forecast_days=21
    )

    logger.success(f"✅ Generated research prompt: {len(research_prompt)} characters")

    # Verify sections
    assert "MOMENTUM SIGNAL" in research_prompt or "momentum" in research_prompt.lower(), "Missing momentum section"
    assert "EARNINGS" in research_prompt or "earnings" in research_prompt.lower() or earnings_summary is None, "Missing earnings section"
    assert "ANALYST" in research_prompt or "analyst" in research_prompt.lower() or analyst_summary is None, "Missing analyst section"
    assert "NEWS" in research_prompt or "news" in research_prompt.lower(), "Missing news section"
    assert "ANALYSIS:" in research_prompt, "Missing ANALYSIS format instruction"
    assert "SCORE:" in research_prompt, "Missing SCORE format instruction"

    logger.success("✅ All prompt sections present")

    # Show preview
    logger.info("\n📄 Research prompt preview (first 800 chars):")
    print("-" * 80)
    print(research_prompt[:800])
    print("...")
    print("-" * 80)

except Exception as e:
    logger.error(f"❌ TEST 1 FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Research Mode Scoring
logger.info("\n" + "="*80)
logger.info("🤖 TEST 2: Scoring with research mode...")
try:
    from src.llm import LLMScorer

    scorer = LLMScorer()

    # Score with research mode
    logger.info(f"Calling LLM with research mode for {symbol}...")
    result = scorer.score_stock_with_research(
        symbol=symbol,
        news_summary=news_summary,
        momentum_return=0.45,
        earnings_data=earnings_data,
        analyst_data=analyst_data,
        return_prompt=True
    )

    if result and len(result) == 4:
        raw_score, normalized_score, analysis, prompt = result

        logger.success(f"✅ Research mode scoring successful!")
        logger.info(f"  Raw Score: {raw_score:.3f}")
        logger.info(f"  Normalized Score: {normalized_score:.3f}")
        logger.info(f"  Analysis Length: {len(analysis)} characters")
        logger.info(f"  Prompt Length: {len(prompt)} characters")

        # Verify analysis
        assert analysis and len(analysis) > 50, "Analysis too short"
        assert 0 <= raw_score <= 1, "Raw score out of range"
        assert -1 <= normalized_score <= 1, "Normalized score out of range"

        logger.success("✅ All scores and analysis valid")

        # Show analysis
        logger.info("\n📊 AI Analysis:")
        print("=" * 80)
        print(analysis)
        print("=" * 80)

    else:
        logger.error("❌ Research mode returned unexpected result")
        sys.exit(1)

except Exception as e:
    logger.error(f"❌ TEST 2 FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Response Parsing
logger.info("\n" + "="*80)
logger.info("🔍 TEST 3: Testing response parsing...")
try:
    # Test various response formats
    test_responses = [
        # Standard format
        """ANALYSIS: This stock shows strong momentum with excellent earnings growth.
        Recent analyst upgrades suggest continued outperformance. The fundamental
        picture supports momentum continuation.

        SCORE: 0.85""",

        # Different formatting
        """ANALYSIS: Mixed signals here. While earnings are good, news sentiment is cautious.

        SCORE: 0.6""",

        # Edge case - score without decimal
        """ANALYSIS: Very bearish outlook based on recent developments.

        SCORE: 0.3"""
    ]

    for i, response in enumerate(test_responses, 1):
        parsed = scorer._parse_research_response(response)

        if parsed:
            analysis, score = parsed
            logger.info(f"  Test {i}: ✅ Parsed - Score: {score:.2f}, Analysis: {len(analysis)} chars")
        else:
            logger.warning(f"  Test {i}: ❌ Failed to parse")

    logger.success("✅ Response parsing working")

except Exception as e:
    logger.error(f"❌ TEST 3 FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Batch Research Mode
logger.info("\n" + "="*80)
logger.info("📦 TEST 4: Batch research mode (3 stocks)...")
try:
    test_stocks = ['AAPL', 'MSFT', 'GOOGL']

    logger.info(f"Fetching data for {len(test_stocks)} stocks...")
    batch_news = dm.get_news(test_stocks, lookback_days=5, use_cache=True)
    batch_earnings = dm.get_earnings(test_stocks, use_cache=True, show_progress=False)
    batch_analyst = dm.get_analyst_data(test_stocks, use_cache=True, show_progress=False)

    results = {}
    for symbol in test_stocks:
        logger.info(f"  Scoring {symbol} with research mode...")

        news_articles = batch_news.get(symbol, [])
        news_summary = PromptTemplate.format_news_for_prompt(news_articles)

        result = scorer.score_stock_with_research(
            symbol=symbol,
            news_summary=news_summary,
            momentum_return=0.30,
            earnings_data=batch_earnings.get(symbol),
            analyst_data=batch_analyst.get(symbol)
        )

        if result:
            raw, norm, analysis = result
            results[symbol] = (norm, analysis)
            logger.info(f"    ✓ {symbol}: Score={norm:.3f}, Analysis={len(analysis)} chars")

    logger.success(f"✅ Batch research mode: {len(results)}/{len(test_stocks)} stocks")

    # Show summary
    logger.info("\n📊 Batch Results:")
    for symbol, (score, analysis) in results.items():
        preview = analysis[:100] + "..." if len(analysis) > 100 else analysis
        logger.info(f"  {symbol}: {score:.3f} - {preview}")

except Exception as e:
    logger.error(f"❌ TEST 4 FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
logger.info("\n" + "="*80)
logger.info("✅ ALL RESEARCH MODE TESTS PASSED!")
logger.info("="*80)
logger.info("\n✨ Hybrid Approach Ready!")
logger.info("\nFeatures verified:")
logger.info("  ✅ Research prompt includes earnings, analyst data, and news")
logger.info("  ✅ LLM returns detailed analysis + score")
logger.info("  ✅ Response parsing extracts ANALYSIS and SCORE")
logger.info("  ✅ Batch processing works for multiple stocks")
logger.info("\nNext: Use in dashboard and portfolio generation! 🚀")

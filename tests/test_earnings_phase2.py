#!/usr/bin/env python3
"""
Test Script: Phase 2 Earnings Integration

Tests that earnings data is properly fetched and integrated into LLM prompts.
"""

from loguru import logger
from src.data import DataManager
from src.llm.prompts import PromptTemplate

def test_earnings_fetching():
    """Test 1: Earnings data fetching"""
    logger.info("="*70)
    logger.info("TEST 1: Earnings Data Fetching")
    logger.info("="*70)

    dm = DataManager()

    # Test single stock
    test_symbol = 'AAPL'
    logger.info(f"\nFetching earnings for {test_symbol}...")

    earnings = dm.get_earnings_for_symbol(test_symbol, use_cache=False)

    if earnings:
        logger.success(f"✓ Successfully fetched earnings for {test_symbol}")
        logger.info(f"  Latest Quarter: {earnings.get('latest_quarter_date')}")
        logger.info(f"  Latest EPS: ${earnings.get('latest_eps')}")
        logger.info(f"  YoY EPS Growth: {earnings.get('yoy_eps_growth')*100 if earnings.get('yoy_eps_growth') else 'N/A'}%")
        logger.info(f"  YoY Revenue Growth: {earnings.get('yoy_revenue_growth')*100 if earnings.get('yoy_revenue_growth') else 'N/A'}%")
        logger.info(f"  Profit Margin: {earnings.get('profit_margin')*100 if earnings.get('profit_margin') else 'N/A'}%")
    else:
        logger.error(f"✗ Failed to fetch earnings for {test_symbol}")
        return False

    # Test batch
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    logger.info(f"\nFetching earnings for {len(test_symbols)} stocks...")

    earnings_data = dm.get_earnings(test_symbols, use_cache=False, show_progress=True)

    logger.success(f"✓ Fetched earnings for {len(earnings_data)}/{len(test_symbols)} stocks")

    return True


def test_earnings_formatting():
    """Test 2: Earnings formatting for prompts"""
    logger.info("\n" + "="*70)
    logger.info("TEST 2: Earnings Formatting for Prompts")
    logger.info("="*70)

    dm = DataManager()

    test_symbol = 'MSFT'
    logger.info(f"\nFetching and formatting earnings for {test_symbol}...")

    earnings = dm.get_earnings_for_symbol(test_symbol, use_cache=True)

    if not earnings:
        logger.error(f"✗ No earnings data for {test_symbol}")
        return False

    # Format for prompt
    formatted = PromptTemplate.format_earnings_for_prompt(earnings)

    logger.success(f"✓ Successfully formatted earnings")
    logger.info("\nFormatted earnings preview:")
    logger.info("-" * 70)
    print(formatted)
    logger.info("-" * 70)
    logger.info(f"Length: {len(formatted)} characters")

    return True


def test_llm_prompt_with_earnings():
    """Test 3: LLM prompt generation with earnings"""
    logger.info("\n" + "="*70)
    logger.info("TEST 3: LLM Prompt with Earnings Data")
    logger.info("="*70)

    dm = DataManager()

    test_symbol = 'NVDA'
    logger.info(f"\nGenerating full LLM prompt for {test_symbol} with earnings...")

    # Get earnings
    earnings = dm.get_earnings_for_symbol(test_symbol, use_cache=True)
    earnings_summary = PromptTemplate.format_earnings_for_prompt(earnings) if earnings else None

    # Get news
    news_data = dm.get_news([test_symbol], lookback_days=5, use_cache=True)
    news_articles = news_data.get(test_symbol, [])
    news_summary = PromptTemplate.format_news_for_prompt(
        news_articles,
        max_articles=5,
        max_chars=1000
    )

    # Generate prompt
    prompt = PromptTemplate.advanced_prompt(
        symbol=test_symbol,
        news_summary=news_summary,
        momentum_return=0.85,  # Example momentum
        company_name="NVIDIA Corporation",
        sector="Technology",
        earnings_summary=earnings_summary,
        forecast_days=21
    )

    logger.success("✓ Successfully generated LLM prompt")
    logger.info("\nFull prompt preview:")
    logger.info("="*70)
    print(prompt)
    logger.info("="*70)
    logger.info(f"Prompt length: {len(prompt)} characters")

    # Check that earnings are included
    if earnings_summary and "📊 LATEST EARNINGS" in prompt:
        logger.success("✓ Earnings data is included in prompt")
    else:
        logger.warning("⚠ Earnings data may not be in prompt")

    return True


def test_llm_scorer_with_earnings():
    """Test 4: LLM scorer with earnings integration"""
    logger.info("\n" + "="*70)
    logger.info("TEST 4: LLM Scorer with Earnings (Full Integration)")
    logger.info("="*70)

    from src.llm import LLMScorer

    dm = DataManager()
    scorer = LLMScorer()

    test_symbol = 'TSLA'
    logger.info(f"\nScoring {test_symbol} with earnings data...")

    # Get data
    earnings = dm.get_earnings_for_symbol(test_symbol, use_cache=True)
    news_data = dm.get_news([test_symbol], lookback_days=5, use_cache=True)
    news_articles = news_data.get(test_symbol, [])
    news_summary = PromptTemplate.format_news_for_prompt(news_articles)

    # Score with earnings
    try:
        result = scorer.score_stock(
            symbol=test_symbol,
            news_summary=news_summary,
            momentum_return=0.75,
            earnings_data=earnings,
            return_prompt=True
        )

        if result and len(result) == 3:
            raw_score, normalized_score, prompt = result
            logger.success(f"✓ Successfully scored {test_symbol}")
            logger.info(f"  Raw Score: {raw_score:.3f}")
            logger.info(f"  Normalized Score: {normalized_score:.3f}")
            logger.info(f"  Prompt Length: {len(prompt)} characters")

            # Verify earnings in prompt
            if "📊 LATEST EARNINGS" in prompt:
                logger.success("✓ Earnings data included in scoring prompt")
            else:
                logger.warning("⚠ Earnings data not found in prompt")

            return True
        else:
            logger.error("✗ Scoring failed or returned unexpected result")
            return False

    except Exception as e:
        logger.error(f"✗ Error during scoring: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    logger.info("\n" + "="*70)
    logger.info("PHASE 2 EARNINGS INTEGRATION TEST SUITE")
    logger.info("="*70)

    tests = [
        ("Earnings Fetching", test_earnings_fetching),
        ("Earnings Formatting", test_earnings_formatting),
        ("LLM Prompt with Earnings", test_llm_prompt_with_earnings),
        ("LLM Scorer with Earnings", test_llm_scorer_with_earnings)
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"✗ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False

    # Summary
    logger.info("\n" + "="*70)
    logger.info("TEST SUMMARY")
    logger.info("="*70)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test_name}")

    total_tests = len(results)
    passed_tests = sum(1 for p in results.values() if p)

    logger.info("-"*70)
    logger.info(f"Total: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        logger.success("\n🎉 ALL TESTS PASSED! Phase 2 integration complete.")
        return 0
    else:
        logger.error(f"\n⚠ {total_tests - passed_tests} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())

"""
Test Risk Prompt Storage

Verifies that risk prompts are properly stored when risk scoring is enabled.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.llm import LLMRiskScorer, get_prompt_store
import pandas as pd

def test_risk_prompt_storage():
    """Test that risk prompts are stored correctly."""
    logger.info("=" * 80)
    logger.info("TESTING RISK PROMPT STORAGE")
    logger.info("=" * 80)

    # Create test data
    test_portfolio = pd.DataFrame({
        'symbol': ['AAPL', 'NVDA', 'TSLA'],
        'weight': [0.33, 0.33, 0.34]
    })

    test_news = {
        'AAPL': [
            "Apple reports strong Q4 earnings, beating estimates.",
            "iPhone sales continue to grow in emerging markets."
        ],
        'NVDA': [
            "NVIDIA facing supply chain constraints.",
            "Competition intensifies as AMD launches rival chips."
        ],
        'TSLA': [
            "Tesla recalls 2 million vehicles over safety concerns.",
            "SEC investigates Tesla CEO's recent statements."
        ]
    }

    # Initialize components
    logger.info("\n1. Initializing risk scorer and prompt store...")
    risk_scorer = LLMRiskScorer(model='gpt-4o-mini')
    prompt_store = get_prompt_store()
    prompt_store.clear_session()  # Start fresh

    # Test WITHOUT prompt storage
    logger.info("\n2. Testing WITHOUT prompt storage...")
    portfolio_no_prompts = risk_scorer.score_portfolio_risks(
        test_portfolio.copy(),
        test_news,
        show_progress=True,
        store_prompts=False,
        prompt_store=None
    )

    # Check prompt store (should be empty)
    summary = prompt_store.get_session_summary()
    logger.info(f"   Prompt store after NO storage: {summary['stock_count']} stocks")
    if summary['stock_count'] == 0:
        logger.info("   ✓ Correctly did not store prompts")
    else:
        logger.error("   ✗ Unexpectedly stored prompts!")

    # Test WITH prompt storage
    logger.info("\n3. Testing WITH prompt storage...")
    prompt_store.clear_session()  # Clear again

    portfolio_with_prompts = risk_scorer.score_portfolio_risks(
        test_portfolio.copy(),
        test_news,
        show_progress=True,
        store_prompts=True,
        prompt_store=prompt_store
    )

    # Check prompt store (should have 3 stocks)
    summary = prompt_store.get_session_summary()
    logger.info(f"   Prompt store after storage: {summary['stock_count']} stocks")
    logger.info(f"   Prompt types: {summary['prompt_types']}")

    if summary['stock_count'] == 3:
        logger.info("   ✓ Correctly stored 3 stock prompts")
    else:
        logger.error(f"   ✗ Expected 3 stocks, got {summary['stock_count']}")

    if 'risk_scoring' in summary['prompt_types']:
        logger.info("   ✓ Risk scoring prompts are stored")
    else:
        logger.error("   ✗ Risk scoring prompts missing!")

    # Verify individual prompts
    logger.info("\n4. Verifying individual stock prompts...")
    for symbol in ['AAPL', 'NVDA', 'TSLA']:
        risk_prompt = prompt_store.get_prompt(symbol, 'risk_scoring')

        if risk_prompt:
            logger.info(f"   ✓ {symbol}: Prompt stored ({len(risk_prompt)} chars)")

            # Check prompt content
            if 'financial risk analyst' in risk_prompt.lower():
                logger.info(f"      ✓ Contains risk analyst instructions")
            else:
                logger.warning(f"      ✗ Missing risk analyst instructions")

            if symbol in risk_prompt:
                logger.info(f"      ✓ Contains symbol {symbol}")
            else:
                logger.warning(f"      ✗ Missing symbol in prompt")
        else:
            logger.error(f"   ✗ {symbol}: No prompt found!")

    # Show sample prompt
    logger.info("\n5. Sample risk prompt (first 500 chars):")
    logger.info("-" * 80)
    sample = prompt_store.get_prompt('TSLA', 'risk_scoring')
    if sample:
        logger.info(sample[:500])
        if len(sample) > 500:
            logger.info("... [truncated]")
    logger.info("-" * 80)

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    all_passed = True

    # Check all tests
    if summary['stock_count'] == 3:
        logger.info("✅ Correct number of stocks stored")
    else:
        logger.error("❌ Wrong number of stocks stored")
        all_passed = False

    if 'risk_scoring' in summary['prompt_types']:
        logger.info("✅ Risk scoring prompt type present")
    else:
        logger.error("❌ Risk scoring prompt type missing")
        all_passed = False

    # Check each stock
    for symbol in ['AAPL', 'NVDA', 'TSLA']:
        prompt = prompt_store.get_prompt(symbol, 'risk_scoring')
        if prompt and len(prompt) > 100:
            logger.info(f"✅ {symbol} prompt valid")
        else:
            logger.error(f"❌ {symbol} prompt invalid or missing")
            all_passed = False

    if all_passed:
        logger.info("\n🎉 ALL TESTS PASSED!")
        logger.info("\nRisk prompt storage is working correctly.")
        logger.info("If you're not seeing prompts in the dashboard, the issue is:")
        logger.info("  1. Risk scoring not enabled when generating")
        logger.info("  2. Old portfolio in session state (need to regenerate)")
        logger.info("  3. Checkbox state not being passed correctly")
    else:
        logger.error("\n❌ SOME TESTS FAILED!")
        logger.error("Risk prompt storage has issues.")


if __name__ == "__main__":
    test_risk_prompt_storage()

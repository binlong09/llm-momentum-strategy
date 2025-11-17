"""
Test LLM Prompts and Scoring
Validates prompt templates and LLM scoring functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import argparse
from loguru import logger

from src.llm import PromptTemplate, LLMScorer
from src.data import DataManager
from src.strategy import MomentumCalculator


def test_prompt_generation():
    """Test prompt template generation."""
    logger.info("\n" + "="*70)
    logger.info("TEST 1: Prompt Template Generation")
    logger.info("="*70)

    # Sample data
    symbol = "NVDA"
    momentum = 0.856
    news = """
1. NVIDIA Announces New AI Chip Architecture (Nov 4, 2024)
   NVIDIA unveiled its next-generation Blackwell GPU architecture, promising 4x performance
   improvement for AI workloads. Pre-orders from cloud providers exceed expectations.

2. Data Center Revenue Surges 200% Year-Over-Year (Nov 3, 2024)
   NVIDIA reported Q3 data center revenue of $14.5 billion, driven by strong demand for
   AI training and inference chips from major tech companies.

3. Stock Hits New All-Time High (Nov 2, 2024)
   NVIDIA shares reached $500, continuing their 2024 rally on AI infrastructure boom.
"""

    # Test basic prompt
    logger.info("\n--- Basic Prompt ---")
    basic = PromptTemplate.basic_prompt(symbol, news, momentum)
    print(basic)

    # Test advanced prompt
    logger.info("\n\n--- Advanced Prompt ---")
    advanced = PromptTemplate.advanced_prompt(
        symbol, news, momentum,
        company_name="NVIDIA Corporation",
        sector="Technology - Semiconductors"
    )
    print(advanced)

    # Test research prompt
    logger.info("\n\n--- Research Prompt (with explanation) ---")
    research = PromptTemplate.research_prompt(symbol, news, momentum)
    print(research)

    logger.success("✓ Prompt generation test passed")


def test_llm_scoring(symbols: list = None, prompt_type: str = 'basic'):
    """
    Test LLM scoring with real stocks.

    Args:
        symbols: List of stock symbols to test
        prompt_type: 'basic' or 'advanced'
    """
    logger.info("\n" + "="*70)
    logger.info(f"TEST 2: LLM Scoring ({prompt_type.upper()} prompts)")
    logger.info("="*70)

    if symbols is None:
        symbols = ['NVDA', 'TSLA', 'AAPL']

    # Initialize
    try:
        scorer = LLMScorer()
        scorer.prompt_type = prompt_type
    except ValueError as e:
        logger.error(f"Failed to initialize LLM scorer: {e}")
        logger.error("Please ensure OpenAI API key is configured in config/api_keys.yaml")
        return

    dm = DataManager()
    momentum_calc = MomentumCalculator()

    # Get universe info for company names and sectors
    universe_info = dm.get_universe_info()

    # Prepare stocks data
    logger.info(f"\nPreparing data for {len(symbols)} stocks...")
    stocks_data = []

    for symbol in symbols:
        logger.info(f"\n  Fetching data for {symbol}...")

        # Get news
        news_articles = dm.get_news(symbol, lookback_days=1)
        news_summary = PromptTemplate.format_news_for_prompt(
            news_articles,
            max_articles=5,
            max_chars=1500
        )

        logger.info(f"    - Found {len(news_articles)} news articles")

        # Get momentum
        price_data = dm.get_prices([symbol], use_cache=True, show_progress=False)
        momentum = None

        if symbol in price_data and price_data[symbol] is not None:
            momentum = momentum_calc.calculate_momentum(price_data[symbol])
            if momentum:
                logger.info(f"    - 12-month momentum: {momentum:.2%}")

        # Get company info
        company_info = None
        if symbol in universe_info.index:
            row = universe_info.loc[symbol]
            company_info = {
                'name': row.get('name', symbol),
                'sector': row.get('sector', 'Unknown')
            }
            logger.info(f"    - Company: {company_info.get('name')}")
            logger.info(f"    - Sector: {company_info.get('sector')}")

        stocks_data.append({
            'symbol': symbol,
            'news_summary': news_summary,
            'momentum_return': momentum,
            'company_info': company_info
        })

    # Score stocks
    logger.info("\n" + "-"*70)
    logger.info("Scoring stocks with LLM...")
    logger.info("-"*70)

    results = scorer.score_batch(stocks_data, show_progress=True)

    # Display results
    logger.info("\n" + "="*70)
    logger.info("SCORING RESULTS")
    logger.info("="*70)

    print("\n{:<8} {:<12} {:<15} {:<15}".format(
        "Symbol", "Momentum", "Raw Score", "Normalized"
    ))
    print("-" * 70)

    for stock in stocks_data:
        symbol = stock['symbol']
        momentum = stock.get('momentum_return')
        momentum_str = f"{momentum:.2%}" if momentum else "N/A"

        if symbol in results:
            raw, normalized = results[symbol]
            print("{:<8} {:<12} {:<15.3f} {:<15.3f}".format(
                symbol, momentum_str, raw, normalized
            ))
        else:
            print("{:<8} {:<12} {:<15} {:<15}".format(
                symbol, momentum_str, "FAILED", "FAILED"
            ))

    # Statistics
    if results:
        stats = scorer.get_score_statistics(results)

        logger.info("\n" + "-"*70)
        logger.info("Score Statistics:")
        logger.info(f"  Successfully scored: {stats['count']}/{len(symbols)} stocks")
        logger.info(f"  Raw scores (0-1): {stats['raw_mean']:.3f} ± {stats['raw_std']:.3f}")
        logger.info(f"    Range: [{stats['raw_min']:.3f}, {stats['raw_max']:.3f}]")
        logger.info(f"  Normalized (-1 to 1): {stats['normalized_mean']:.3f} ± {stats['normalized_std']:.3f}")
        logger.info(f"    Range: [{stats['normalized_min']:.3f}, {stats['normalized_max']:.3f}]")

        logger.success("✓ LLM scoring test passed")
    else:
        logger.error("✗ LLM scoring test failed - no successful scores")


def test_prompt_variations():
    """Test how different prompt types affect scores."""
    logger.info("\n" + "="*70)
    logger.info("TEST 3: Prompt Type Comparison")
    logger.info("="*70)

    symbol = "TSLA"

    logger.info(f"\nScoring {symbol} with different prompt types...")

    for prompt_type in ['basic', 'advanced']:
        logger.info(f"\n--- Testing {prompt_type.upper()} prompt ---")
        test_llm_scoring(symbols=[symbol], prompt_type=prompt_type)


def main():
    parser = argparse.ArgumentParser(description="Test LLM prompts and scoring")

    parser.add_argument(
        '--test',
        type=str,
        choices=['prompts', 'scoring', 'variations', 'all'],
        default='all',
        help='Which test to run'
    )

    parser.add_argument(
        '--symbols',
        nargs='+',
        default=['NVDA', 'TSLA', 'AAPL'],
        help='Stock symbols to test'
    )

    parser.add_argument(
        '--prompt-type',
        type=str,
        choices=['basic', 'advanced'],
        default='basic',
        help='Prompt type to use'
    )

    args = parser.parse_args()

    logger.info("="*70)
    logger.info("LLM PROMPT & SCORING TESTS")
    logger.info("="*70)

    if args.test in ['prompts', 'all']:
        test_prompt_generation()

    if args.test in ['scoring', 'all']:
        test_llm_scoring(symbols=args.symbols, prompt_type=args.prompt_type)

    if args.test in ['variations', 'all']:
        test_prompt_variations()

    logger.info("\n" + "="*70)
    logger.success("All tests completed!")
    logger.info("="*70)


if __name__ == "__main__":
    main()

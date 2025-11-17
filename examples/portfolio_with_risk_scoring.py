#!/usr/bin/env python3
"""
Example: Generate Portfolio with LLM Risk Scoring

This script demonstrates how to add stock-level risk assessment
to your portfolio using LLM-based news analysis.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from datetime import datetime
from loguru import logger

from src.data import DataManager
from src.strategy import EnhancedSelector, EnhancedPortfolioConstructor
from src.llm import LLMRiskScorer


def generate_portfolio_with_risk_scoring(
    portfolio_size: int = 20,
    apply_risk_adjustment: bool = True,
    risk_threshold: float = 0.7,
    reduction_factor: float = 0.5
):
    """
    Generate portfolio with LLM risk scoring for each holding.

    Args:
        portfolio_size: Number of stocks to hold
        apply_risk_adjustment: Whether to reduce weights for high-risk stocks
        risk_threshold: Risk score above which to reduce weights
        reduction_factor: How much to reduce (0.5 = reduce to 50%)

    Returns:
        Portfolio DataFrame with risk scores
    """
    logger.info("="*70)
    logger.info("PORTFOLIO GENERATION WITH LLM RISK SCORING")
    logger.info("="*70)
    logger.info(f"Portfolio size: {portfolio_size}")
    logger.info(f"Risk adjustment: {apply_risk_adjustment}")
    if apply_risk_adjustment:
        logger.info(f"Risk threshold: {risk_threshold}")
        logger.info(f"Reduction factor: {reduction_factor}")
    logger.info("="*70 + "\n")

    # Initialize components
    logger.info("Initializing components...")
    dm = DataManager()
    selector = EnhancedSelector()
    constructor = EnhancedPortfolioConstructor()
    risk_scorer = LLMRiskScorer()

    # Get universe
    logger.info("\nFetching S&P 500 universe...")
    universe = dm.get_universe()[:100]  # Smaller for faster demo
    logger.info(f"Universe: {len(universe)} stocks")

    # Fetch price data
    logger.info("\nFetching price data...")
    price_data = dm.get_prices(
        universe,
        use_cache=True,
        show_progress=True
    )

    today = datetime.now().strftime('%Y-%m-%d')

    # Enhanced selection with LLM
    logger.info("\n" + "="*70)
    logger.info("STEP 1: ENHANCED STOCK SELECTION")
    logger.info("="*70)

    selected_stocks, metadata = selector.select_for_portfolio_enhanced(
        price_data,
        end_date=today,
        final_count=portfolio_size,
        rerank_method='llm_only',
        apply_quality_filter=True
    )

    if selected_stocks.empty:
        logger.error("No stocks selected. Check data availability.")
        return None

    logger.info(f"\nSelected {len(selected_stocks)} stocks with LLM scores")
    logger.info(f"Average LLM score: {selected_stocks['llm_score'].mean():.3f}")

    # Construct enhanced portfolio
    logger.info("\n" + "="*70)
    logger.info("STEP 2: PORTFOLIO CONSTRUCTION")
    logger.info("="*70)

    portfolio = constructor.construct_portfolio_enhanced(
        selected_stocks,
        base_weighting='equal',
        use_llm_tilting=True,
        tilt_factor=5.0,
        price_data=price_data,
        end_date=today
    )

    # Fetch news for risk scoring
    logger.info("\n" + "="*70)
    logger.info("STEP 3: FETCH NEWS FOR RISK ASSESSMENT")
    logger.info("="*70)

    symbols = portfolio['symbol'].tolist()
    logger.info(f"Fetching news for {len(symbols)} stocks...")

    news_data = dm.get_news(
        symbols,
        days_back=1,
        use_cache=True
    )

    logger.info(f"News fetched for {len(news_data)} stocks")

    # Score risk for each stock
    logger.info("\n" + "="*70)
    logger.info("STEP 4: LLM RISK SCORING")
    logger.info("="*70)

    portfolio_with_risk = risk_scorer.score_portfolio_risks(
        portfolio,
        news_data,
        show_progress=True
    )

    # Apply risk-based adjustment if enabled
    if apply_risk_adjustment:
        logger.info("\n" + "="*70)
        logger.info("STEP 5: RISK-BASED WEIGHT ADJUSTMENT")
        logger.info("="*70)

        portfolio_with_risk = risk_scorer.apply_risk_based_adjustment(
            portfolio_with_risk,
            risk_threshold=risk_threshold,
            reduction_factor=reduction_factor
        )

    # Sort by weight
    portfolio_with_risk = portfolio_with_risk.sort_values('weight', ascending=False)

    # Display results
    print("\n" + "="*90)
    print(f"PORTFOLIO WITH RISK SCORES - {today}")
    print("="*90 + "\n")

    # Summary stats
    print(f"Total positions: {len(portfolio_with_risk)}")
    print(f"Portfolio weights sum: {portfolio_with_risk['weight'].sum():.2%}")
    print(f"Average risk score: {portfolio_with_risk['risk_score'].mean():.2f}")
    print(f"High-risk stocks (>0.7): {(portfolio_with_risk['risk_score'] > 0.7).sum()}")

    # Display top 15 holdings with risk scores
    print(f"\n{'='*90}")
    print("TOP 15 HOLDINGS WITH RISK ASSESSMENT")
    print(f"{'='*90}\n")

    display_cols = ['symbol', 'weight', 'llm_score', 'risk_score', 'risk_recommendation', 'key_risk']
    top_15 = portfolio_with_risk.head(15)[display_cols].copy()

    # Format for display
    top_15['weight'] = top_15['weight'].apply(lambda x: f"{x:.2%}")
    top_15['llm_score'] = top_15['llm_score'].apply(lambda x: f"{x:.3f}")
    top_15['risk_score'] = top_15['risk_score'].apply(lambda x: f"{x:.2f}")

    print(top_15.to_string(index=False))

    # Risk distribution
    print(f"\n{'='*90}")
    print("RISK DISTRIBUTION")
    print(f"{'='*90}\n")

    low_risk = (portfolio_with_risk['risk_score'] <= 0.4).sum()
    medium_risk = ((portfolio_with_risk['risk_score'] > 0.4) & (portfolio_with_risk['risk_score'] <= 0.7)).sum()
    high_risk = (portfolio_with_risk['risk_score'] > 0.7).sum()

    print(f"Low Risk (0.0-0.4):    {low_risk:2d} stocks ({low_risk/len(portfolio_with_risk)*100:.1f}%)")
    print(f"Medium Risk (0.4-0.7): {medium_risk:2d} stocks ({medium_risk/len(portfolio_with_risk)*100:.1f}%)")
    print(f"High Risk (0.7-1.0):   {high_risk:2d} stocks ({high_risk/len(portfolio_with_risk)*100:.1f}%)")

    # High-risk warnings
    if high_risk > 0:
        print(f"\n{'='*90}")
        print("⚠️  HIGH-RISK STOCKS")
        print(f"{'='*90}\n")

        high_risk_stocks = portfolio_with_risk[portfolio_with_risk['risk_score'] > 0.7]
        for _, stock in high_risk_stocks.iterrows():
            print(f"{stock['symbol']:6} - Risk: {stock['risk_score']:.2f} - {stock['key_risk']}")

    # Export to CSV
    output_dir = Path("results/portfolios")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = output_dir / f"portfolio_with_risk_{timestamp}.csv"

    portfolio_with_risk.to_csv(filename, index=False)
    logger.info(f"\n✓ Portfolio saved to: {filename}")

    # Action items
    print(f"\n{'='*90}")
    print("NEXT STEPS")
    print(f"{'='*90}\n")

    print("1. Review high-risk stocks and consider:")
    print("   - Reducing position sizes")
    print("   - Setting tighter stop-losses")
    print("   - Monitoring news closely")
    print("2. Compare risk scores with your own research")
    print("3. Use risk scores to prioritize which stocks to track")
    print("4. Rebalance monthly and update risk assessments")

    return portfolio_with_risk


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate portfolio with LLM risk scoring"
    )
    parser.add_argument(
        '--size',
        type=int,
        default=20,
        help='Portfolio size (default: 20)'
    )
    parser.add_argument(
        '--no-risk-adjustment',
        action='store_true',
        help='Disable risk-based weight adjustment'
    )
    parser.add_argument(
        '--risk-threshold',
        type=float,
        default=0.7,
        help='Risk score threshold for weight reduction (default: 0.7)'
    )
    parser.add_argument(
        '--reduction-factor',
        type=float,
        default=0.5,
        help='Weight reduction factor for high-risk stocks (default: 0.5)'
    )

    args = parser.parse_args()

    # Generate portfolio
    portfolio = generate_portfolio_with_risk_scoring(
        portfolio_size=args.size,
        apply_risk_adjustment=not args.no_risk_adjustment,
        risk_threshold=args.risk_threshold,
        reduction_factor=args.reduction_factor
    )

    if portfolio is None:
        logger.error("Failed to generate portfolio")
        return

    logger.info("\n" + "="*70)
    logger.info("PORTFOLIO GENERATION COMPLETE")
    logger.info("="*70)


if __name__ == "__main__":
    main()

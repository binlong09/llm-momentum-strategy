#!/usr/bin/env python3
"""
Example: Generate Portfolio with Volatility Protection

This script demonstrates how to integrate volatility protection
into your LLM momentum strategy portfolio generation.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from datetime import datetime, timedelta
from loguru import logger

from src.data import DataManager
from src.strategy import EnhancedSelector, EnhancedPortfolioConstructor, VolatilityProtection


def generate_protected_portfolio(
    portfolio_size: int = 50,
    base_weighting: str = 'equal',
    tilt_factor: float = 5.0,
    enable_protection: bool = True,
    vix_threshold_high: float = 30.0,
    vix_threshold_panic: float = 40.0,
    target_volatility: float = 0.15
):
    """
    Generate portfolio with volatility protection.

    Args:
        portfolio_size: Number of stocks to hold
        base_weighting: 'equal', 'value', or 'momentum'
        tilt_factor: η parameter for LLM weight tilting
        enable_protection: Whether to enable volatility protection
        vix_threshold_high: VIX level indicating high volatility
        vix_threshold_panic: VIX level indicating panic state
        target_volatility: Target portfolio volatility for scaling

    Returns:
        Tuple of (portfolio DataFrame, protection adjustments dict)
    """
    logger.info("="*70)
    logger.info("PORTFOLIO GENERATION WITH VOLATILITY PROTECTION")
    logger.info("="*70)
    logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Portfolio size: {portfolio_size}")
    logger.info(f"Base weighting: {base_weighting}")
    logger.info(f"Volatility protection: {enable_protection}")
    logger.info("="*70 + "\n")

    # Initialize components
    logger.info("Initializing data manager and strategy components...")
    dm = DataManager()
    selector = EnhancedSelector()
    constructor = EnhancedPortfolioConstructor(enable_volatility_protection=enable_protection)

    # Initialize volatility protection with custom parameters
    if enable_protection:
        constructor.vol_protect = VolatilityProtection(
            vix_threshold_high=vix_threshold_high,
            vix_threshold_panic=vix_threshold_panic,
            target_volatility=target_volatility
        )
        logger.info(
            f"Volatility protection configured: "
            f"VIX_high={vix_threshold_high}, VIX_panic={vix_threshold_panic}, "
            f"target_vol={target_volatility:.1%}"
        )

    # Get universe
    logger.info("\nFetching S&P 500 universe...")
    universe = dm.get_universe()[:300]
    logger.info(f"Universe: {len(universe)} stocks")

    # Fetch price data
    logger.info("\nFetching price data (this may take a minute)...")
    price_data = dm.get_prices(
        universe,
        use_cache=True,
        show_progress=True
    )

    today = datetime.now().strftime('%Y-%m-%d')

    # Enhanced selection with LLM
    logger.info("\n" + "="*70)
    logger.info("ENHANCED SELECTION (with LLM)")
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
        return None, None

    logger.info(f"\nSelected {len(selected_stocks)} stocks with LLM scores")
    logger.info(f"Average LLM score: {selected_stocks['llm_score'].mean():.3f}")

    # Construct enhanced portfolio
    portfolio = constructor.construct_portfolio_enhanced(
        selected_stocks,
        base_weighting=base_weighting,
        use_llm_tilting=True,
        tilt_factor=tilt_factor,
        price_data=price_data,
        end_date=today
    )

    # Apply volatility protection if enabled
    protection_adjustments = None
    if enable_protection and constructor.vol_protect:
        logger.info("\n" + "="*70)
        logger.info("APPLYING VOLATILITY PROTECTION")
        logger.info("="*70)

        # Get SPY data for market regime detection
        try:
            spy_data = dm.get_prices(['SPY'], use_cache=True, show_progress=False)
            if 'SPY' in spy_data and not spy_data['SPY'].empty:
                spy_prices = spy_data['SPY']['close']
                spy_returns = spy_prices.pct_change().fillna(0)

                # Get VIX data (simplified - in production, fetch from data source)
                # For now, we'll estimate VIX from SPY volatility
                recent_vol = spy_returns.tail(21).std() * np.sqrt(252)
                estimated_vix = min(recent_vol * 100, 80)  # Scale to VIX-like range

                logger.info(f"Estimated VIX: {estimated_vix:.1f}")

                # Calculate strategy returns (simplified)
                momentum_returns = spy_returns.copy()  # Use SPY as proxy

                current_date = pd.Timestamp(today)

                # Apply protection
                portfolio, protection_adjustments = constructor.apply_volatility_protection(
                    portfolio=portfolio,
                    spy_prices=spy_prices,
                    spy_returns=spy_returns,
                    vix_level=estimated_vix,
                    momentum_returns=momentum_returns,
                    current_date=current_date,
                    enable_hedging=False
                )

                # Display protection status
                print_protection_dashboard(protection_adjustments)

            else:
                logger.warning("Could not fetch SPY data for volatility protection")
        except Exception as e:
            logger.error(f"Error applying volatility protection: {e}")

    # Sort by weight
    portfolio = portfolio.sort_values('weight', ascending=False)

    # Display results
    logger.info("\n" + "="*70)
    logger.info("PORTFOLIO RECOMMENDATIONS")
    logger.info("="*70)

    print(f"\n{'='*90}")
    print(f"PORTFOLIO FOR {today}")
    print(f"{'='*90}\n")

    # Summary stats
    print(f"Total positions: {len(portfolio)}")
    print(f"Portfolio weights sum: {portfolio['weight'].sum():.2%}")
    print(f"Max position: {portfolio['weight'].max():.2%}")
    print(f"Min position: {portfolio['weight'].min():.2%}")

    if 'llm_score' in portfolio.columns:
        print(f"Average LLM score: {portfolio['llm_score'].mean():.3f}")

    if 'protection_exposure' in portfolio.columns:
        print(f"Protection exposure: {portfolio['protection_exposure'].iloc[0]:.1%}")
        print(f"Market regime: {portfolio['protection_regime'].iloc[0]}")

    # Display top 20 holdings
    print(f"\n{'='*90}")
    print("TOP 20 HOLDINGS")
    print(f"{'='*90}\n")

    display_cols = ['symbol', 'weight', 'momentum_return']
    if 'llm_score' in portfolio.columns:
        display_cols.append('llm_score')
    if 'original_weight' in portfolio.columns:
        display_cols.append('original_weight')

    top_20 = portfolio.head(20)[display_cols].copy()

    # Format for display
    top_20['weight'] = top_20['weight'].apply(lambda x: f"{x:.2%}")
    top_20['momentum_return'] = top_20['momentum_return'].apply(lambda x: f"{x:.2%}")
    if 'llm_score' in top_20.columns:
        top_20['llm_score'] = top_20['llm_score'].apply(lambda x: f"{x:.3f}")
    if 'original_weight' in top_20.columns:
        top_20['original_weight'] = top_20['original_weight'].apply(lambda x: f"{x:.2%}")

    print(top_20.to_string(index=False))

    # Export to CSV
    output_dir = Path("results/portfolios")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    strategy_name = f"enhanced_{base_weighting}_{'protected' if enable_protection else 'unprotected'}"
    filename = output_dir / f"portfolio_{strategy_name}_{timestamp}.csv"

    portfolio.to_csv(filename, index=False)
    logger.info(f"\n✓ Portfolio saved to: {filename}")

    return portfolio, protection_adjustments


def print_protection_dashboard(adjustments: dict):
    """Print a dashboard of current protection status"""

    print("\n" + "="*70)
    print("VOLATILITY PROTECTION DASHBOARD")
    print("="*70)

    # Market Regime
    regime = adjustments['regime']
    print(f"\nMarket Regime: {regime.state.upper()}")
    print(f"  VIX Level: {regime.vix_level:.1f}")
    print(f"  Volatility: {regime.volatility:.1%}")
    print(f"  Trend: {regime.market_trend}")

    # Protection Levels
    print(f"\nProtection Adjustments:")
    print(f"  Volatility Scalar: {adjustments['volatility_scalar']:.2f}x")
    print(f"  Regime Multiplier: {adjustments['regime_multiplier']:.1%}")
    print(f"  Crash Adjustment: {adjustments['crash_adjustment']:.1%}")

    # Risk Assessment
    print(f"\nRisk Assessment:")
    print(f"  Crash Risk: {'YES' if adjustments['crash_risk'] else 'NO'}")
    print(f"  Risk Score: {adjustments['crash_risk_score']:.2f}/1.00")

    # Actions
    print(f"\nRecommendations:")
    print(f"  Portfolio Exposure: {adjustments['final_exposure']:.1%}")
    print(f"  Rebalancing: {adjustments['rebalancing_frequency'].upper()}")
    print(f"  Hedge Ratio: {adjustments['hedge_ratio']:.1%}")

    print(f"\n{adjustments['recommendation']}")
    print("="*70 + "\n")


def main():
    """Main entry point."""
    import argparse
    import numpy as np

    parser = argparse.ArgumentParser(
        description="Generate portfolio with volatility protection"
    )
    parser.add_argument(
        '--size',
        type=int,
        default=50,
        help='Portfolio size (default: 50)'
    )
    parser.add_argument(
        '--weighting',
        type=str,
        default='equal',
        choices=['equal', 'value', 'momentum'],
        help='Base weighting scheme (default: equal)'
    )
    parser.add_argument(
        '--tilt-factor',
        type=float,
        default=5.0,
        help='LLM weight tilting factor (default: 5.0)'
    )
    parser.add_argument(
        '--no-protection',
        action='store_true',
        help='Disable volatility protection'
    )
    parser.add_argument(
        '--vix-high',
        type=float,
        default=30.0,
        help='VIX threshold for high volatility (default: 30.0)'
    )
    parser.add_argument(
        '--vix-panic',
        type=float,
        default=40.0,
        help='VIX threshold for panic (default: 40.0)'
    )
    parser.add_argument(
        '--target-vol',
        type=float,
        default=0.15,
        help='Target portfolio volatility (default: 0.15 = 15%%)'
    )

    args = parser.parse_args()

    # Generate portfolio
    portfolio, adjustments = generate_protected_portfolio(
        portfolio_size=args.size,
        base_weighting=args.weighting,
        tilt_factor=args.tilt_factor,
        enable_protection=not args.no_protection,
        vix_threshold_high=args.vix_high,
        vix_threshold_panic=args.vix_panic,
        target_volatility=args.target_vol
    )

    if portfolio is None:
        logger.error("Failed to generate portfolio")
        return

    # Summary
    print(f"\n{'='*90}")
    print("NEXT STEPS")
    print(f"{'='*90}\n")

    print("1. Review the portfolio recommendations above")
    print("2. Check the volatility protection status")
    print("3. Compare with your current holdings")
    if adjustments and adjustments['final_exposure'] < 0.8:
        print("4. ⚠️  IMPORTANT: Protection reduced exposure - consider holding more cash")
    print("5. Execute rebalance during market hours")

    logger.info("\n" + "="*70)
    logger.info("PORTFOLIO GENERATION COMPLETE")
    logger.info("="*70)


if __name__ == "__main__":
    main()

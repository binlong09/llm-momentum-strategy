"""
Generate Current Portfolio Recommendations
Run this script monthly to get your next rebalancing portfolio.
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
from src.strategy import EnhancedSelector, EnhancedPortfolioConstructor, VolatilityProtection
from src.llm import LLMRiskScorer


def generate_current_portfolio(
    portfolio_size: int = 50,
    base_weighting: str = 'equal',
    use_llm: bool = True,
    tilt_factor: float = 5.0,
    export_csv: bool = True,
    model: str = None,
    enable_protection: bool = False,
    vix_high: float = None,
    vix_panic: float = None,
    target_vol: float = None,
    enable_risk_scoring: bool = False,
    apply_risk_adjustment: bool = False,
    risk_threshold: float = 0.7,
    risk_reduction_factor: float = 0.5,
    store_prompts: bool = False,
    enable_research_mode: bool = False,
    num_research_stocks: int = 10
):
    """
    Generate portfolio recommendations for current date.

    Args:
        portfolio_size: Number of stocks to hold
        base_weighting: 'equal', 'value', or 'momentum'
        use_llm: Whether to use LLM enhancement
        tilt_factor: η parameter for LLM weight tilting
        export_csv: Save results to CSV
        model: LLM model to use ('gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo')
               If None, uses default from config
        enable_protection: Whether to enable volatility protection
        vix_high: VIX threshold for high volatility (None = use default)
        vix_panic: VIX threshold for panic (None = use default)
        target_vol: Target portfolio volatility (None = use default)
        enable_risk_scoring: Whether to add LLM risk scores for each stock
        apply_risk_adjustment: Whether to reduce weights for high-risk stocks
        risk_threshold: Risk score above which to reduce weights
        risk_reduction_factor: How much to reduce high-risk weights

    Returns:
        DataFrame with portfolio recommendations
    """
    logger.info("="*70)
    logger.info("PORTFOLIO GENERATION")
    logger.info("="*70)
    logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Portfolio size: {portfolio_size}")
    logger.info(f"Base weighting: {base_weighting}")
    logger.info(f"LLM enhancement: {use_llm}")
    if use_llm:
        logger.info(f"LLM model: {model or 'default (gpt-4o-mini)'}")
        logger.info(f"Tilt factor (η): {tilt_factor}")
    logger.info("="*70 + "\n")

    # Initialize components
    logger.info("Initializing data manager and strategy components...")
    dm = DataManager()
    selector = EnhancedSelector(model=model) if use_llm else None
    constructor = EnhancedPortfolioConstructor(enable_volatility_protection=enable_protection)

    # Initialize prompt store if needed
    prompt_store = None
    if store_prompts:
        from src.llm import get_prompt_store
        prompt_store = get_prompt_store()
        logger.info("Prompt storage enabled - prompts will be saved for review")

    # Configure volatility protection if enabled
    if enable_protection:
        vol_protect_kwargs = {}
        if vix_high is not None:
            vol_protect_kwargs['vix_threshold_high'] = vix_high
        if vix_panic is not None:
            vol_protect_kwargs['vix_threshold_panic'] = vix_panic
        if target_vol is not None:
            vol_protect_kwargs['target_volatility'] = target_vol

        if vol_protect_kwargs:
            constructor.vol_protect = VolatilityProtection(**vol_protect_kwargs)
            logger.info(f"Volatility protection configured with custom parameters: {vol_protect_kwargs}")

    # Get universe
    logger.info("Fetching S&P 500 universe...")
    universe = dm.get_universe()[:300]  # Top 300 for coverage
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
    if use_llm and selector:
        logger.info("\n" + "="*70)
        logger.info("ENHANCED SELECTION (with LLM)")
        logger.info("="*70)

        selected_stocks, metadata = selector.select_for_portfolio_enhanced(
            price_data,
            end_date=today,
            final_count=portfolio_size,
            rerank_method='llm_only',
            apply_quality_filter=True,
            store_prompts=store_prompts,
            prompt_store=prompt_store
        )

        if selected_stocks.empty:
            logger.error("No stocks selected. Check data availability.")
            return None

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
    else:
        # Baseline selection (no LLM)
        logger.info("\n" + "="*70)
        logger.info("BASELINE SELECTION (no LLM)")
        logger.info("="*70)

        from src.strategy import StockSelector
        baseline_selector = StockSelector()

        selected_stocks, metadata = baseline_selector.select_for_portfolio(
            price_data,
            end_date=today,
            final_count=portfolio_size
        )

        if selected_stocks.empty:
            logger.error("No stocks selected. Check data availability.")
            return None

        logger.info(f"\nSelected {len(selected_stocks)} stocks by momentum")

        # Construct baseline portfolio
        portfolio = constructor.construct_portfolio(
            selected_stocks,
            price_data=price_data,
            weighting_scheme=base_weighting,
            end_date=today
        )

    # Apply volatility protection if enabled
    if enable_protection and constructor.vol_protect:
        logger.info("\n" + "="*70)
        logger.info("APPLYING VOLATILITY PROTECTION")
        logger.info("="*70)

        try:
            import numpy as np
            # Get SPY data for market regime detection
            spy_data = dm.get_prices(['SPY'], use_cache=True, show_progress=False)
            if 'SPY' in spy_data and not spy_data['SPY'].empty:
                spy_prices = spy_data['SPY']['close']
                spy_returns = spy_prices.pct_change().fillna(0)

                # Estimate VIX from SPY volatility (simplified)
                recent_vol = spy_returns.tail(21).std() * np.sqrt(252)
                estimated_vix = min(recent_vol * 100, 80)  # Scale to VIX-like range

                logger.info(f"Estimated VIX: {estimated_vix:.1f}")

                # Calculate strategy returns (use SPY as proxy)
                momentum_returns = spy_returns.copy()

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

                # Log protection status
                logger.info(f"Market regime: {protection_adjustments['regime'].state}")
                logger.info(f"Portfolio exposure: {protection_adjustments['final_exposure']:.1%}")
                logger.info(f"Cash position: {1.0 - portfolio['weight'].sum():.1%}")
                logger.info(f"Recommendation: {protection_adjustments['recommendation']}")

            else:
                logger.warning("Could not fetch SPY data for volatility protection")
        except Exception as e:
            logger.error(f"Error applying volatility protection: {e}")
            import traceback
            traceback.print_exc()

    # Apply LLM risk scoring if enabled
    if enable_risk_scoring and use_llm:
        logger.info("\n" + "="*70)
        logger.info("APPLYING LLM RISK SCORING")
        logger.info("="*70)

        try:
            # Initialize risk scorer
            risk_scorer = LLMRiskScorer(model=model or 'gpt-4o-mini')

            # Fetch news for selected stocks
            symbols = portfolio['symbol'].tolist()
            logger.info(f"Fetching news for {len(symbols)} stocks...")

            news_data = dm.get_news(
                symbols,
                lookback_days=5,  # Enhanced: 3-7 days for better risk assessment
                use_cache=True
            )

            logger.info(f"News fetched for {len(news_data)} stocks")

            # Score risk for each stock
            portfolio = risk_scorer.score_portfolio_risks(
                portfolio,
                news_data,
                show_progress=False,
                store_prompts=store_prompts,
                prompt_store=prompt_store
            )

            logger.info(f"Average risk score: {portfolio['risk_score'].mean():.2f}")

            # Apply risk-based adjustment if enabled
            if apply_risk_adjustment:
                logger.info(f"\nApplying risk-based weight adjustment...")
                logger.info(f"Risk threshold: {risk_threshold}")
                logger.info(f"Reduction factor: {risk_reduction_factor}")

                portfolio = risk_scorer.apply_risk_based_adjustment(
                    portfolio,
                    risk_threshold=risk_threshold,
                    reduction_factor=risk_reduction_factor
                )

        except Exception as e:
            logger.error(f"Error during risk scoring: {e}")
            import traceback
            traceback.print_exc()
            logger.warning("Continuing without risk scores...")

    # Generate research mode explanations for top holdings (Hybrid Approach)
    if enable_research_mode and use_llm:
        logger.info("\n" + "="*70)
        logger.info("GENERATING DETAILED EXPLANATIONS (Research Mode)")
        logger.info("="*70)
        logger.info(f"Generating AI analysis for top {num_research_stocks} holdings...")

        try:
            # Sort to get current top holdings
            portfolio_sorted = portfolio.sort_values('weight', ascending=False)
            top_holdings = portfolio_sorted.head(num_research_stocks)

            # Import scorer
            from src.llm import LLMScorer

            research_scorer = LLMScorer(model=model or 'gpt-4o-mini')

            # Fetch data for top holdings
            symbols = top_holdings['symbol'].tolist()

            # Get news
            logger.info(f"Fetching news for {len(symbols)} stocks...")
            news_data = dm.get_news(symbols, lookback_days=5, use_cache=True)

            # Get earnings
            logger.info(f"Fetching earnings for {len(symbols)} stocks...")
            earnings_dict = dm.get_earnings(symbols, use_cache=True, show_progress=False)

            # Get analyst data
            logger.info(f"Fetching analyst data for {len(symbols)} stocks...")
            analyst_dict = dm.get_analyst_data(symbols, use_cache=True, show_progress=False)

            # Score with research mode
            logger.info(f"Scoring with research mode (this may take 30-60 seconds)...")

            analyses = {}
            for symbol in symbols:
                try:
                    # Get news summary
                    from src.llm.prompts import PromptTemplate
                    news_articles = news_data.get(symbol, [])
                    news_summary = PromptTemplate.format_news_for_prompt(news_articles)

                    # Get momentum
                    momentum = portfolio_sorted[portfolio_sorted['symbol'] == symbol]['momentum_return'].iloc[0]

                    # Score with research mode
                    result = research_scorer.score_stock_with_research(
                        symbol=symbol,
                        news_summary=news_summary,
                        momentum_return=momentum,
                        earnings_data=earnings_dict.get(symbol),
                        analyst_data=analyst_dict.get(symbol),
                        return_prompt=store_prompts
                    )

                    if result:
                        if store_prompts and len(result) == 4:
                            raw_score, norm_score, analysis, prompt = result
                            if prompt_store:
                                prompt_store.store_prompt(
                                    symbol=symbol,
                                    prompt=prompt,
                                    prompt_type='research_mode',
                                    metadata={
                                        'model': model or 'gpt-4o-mini',
                                        'analysis': analysis,
                                        'score': norm_score
                                    }
                                )
                        else:
                            raw_score, norm_score, analysis = result

                        analyses[symbol] = analysis
                        logger.info(f"  ✓ {symbol}: {len(analysis)} chars")

                except Exception as e:
                    logger.warning(f"Failed to generate analysis for {symbol}: {e}")
                    continue

            # Add analyses to portfolio
            portfolio['ai_analysis'] = portfolio['symbol'].map(lambda s: analyses.get(s, None))

            logger.success(f"Generated {len(analyses)}/{len(symbols)} detailed analyses")

        except Exception as e:
            logger.error(f"Error during research mode: {e}")
            import traceback
            traceback.print_exc()
            logger.warning("Continuing without research analyses...")

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

    # Display top 20 holdings
    print(f"\n{'='*90}")
    print("TOP 20 HOLDINGS")
    print(f"{'='*90}\n")

    display_cols = ['symbol', 'weight', 'momentum_return']
    if 'llm_score' in portfolio.columns:
        display_cols.append('llm_score')

    top_20 = portfolio.head(20)[display_cols].copy()

    # Format for display
    top_20['weight'] = top_20['weight'].apply(lambda x: f"{x:.2%}")
    top_20['momentum_return'] = top_20['momentum_return'].apply(lambda x: f"{x:.2%}")
    if 'llm_score' in top_20.columns:
        top_20['llm_score'] = top_20['llm_score'].apply(lambda x: f"{x:.3f}")

    print(top_20.to_string(index=False))

    # Export to CSV
    if export_csv:
        output_dir = Path("results/portfolios")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        strategy_name = f"{'enhanced' if use_llm else 'baseline'}_{base_weighting}"
        filename = output_dir / f"portfolio_{strategy_name}_{timestamp}.csv"

        portfolio.to_csv(filename, index=False)
        logger.info(f"\n✓ Portfolio saved to: {filename}")

    # Action items
    print(f"\n{'='*90}")
    print("NEXT STEPS FOR TRADING")
    print(f"{'='*90}\n")

    print("1. Review the portfolio recommendations above")
    print("2. Compare with your current holdings")
    print("3. Calculate trades needed (sells and buys)")
    print("4. Execute rebalance during market hours")
    print("5. Save this portfolio for next month's comparison")

    # Example calculation
    print(f"\n{'='*90}")
    print("EXAMPLE: For $100,000 portfolio")
    print(f"{'='*90}\n")

    example_capital = 100000
    print(f"Top 5 positions:\n")
    for idx, row in portfolio.head(5).iterrows():
        position_value = example_capital * row['weight']
        print(f"  {row['symbol']:6} - {row['weight']:>6.2%} = ${position_value:>10,.2f}")

    # Return portfolio and optional prompt store
    if store_prompts and prompt_store:
        return portfolio, prompt_store
    else:
        return portfolio


def compare_with_current(
    new_portfolio: pd.DataFrame,
    current_holdings_csv: str = None
):
    """
    Compare new portfolio with current holdings and show required trades.

    Args:
        new_portfolio: New portfolio DataFrame
        current_holdings_csv: Path to CSV with current holdings
    """
    if current_holdings_csv is None:
        logger.info("\nNo current holdings file provided. Skipping trade comparison.")
        logger.info("To compare with current holdings, pass current_holdings_csv parameter")
        return

    try:
        current = pd.read_csv(current_holdings_csv)

        print(f"\n{'='*90}")
        print("TRADE COMPARISON")
        print(f"{'='*90}\n")

        # Get symbols
        current_symbols = set(current['symbol'].values)
        new_symbols = set(new_portfolio['symbol'].values)

        # Calculate changes
        sells = current_symbols - new_symbols
        buys = new_symbols - current_symbols
        holds = current_symbols & new_symbols

        print(f"Current positions: {len(current_symbols)}")
        print(f"New positions: {len(new_symbols)}")
        print(f"\nTrades required:")
        print(f"  Sells: {len(sells)} positions")
        print(f"  Buys: {len(buys)} positions")
        print(f"  Holds (rebalance): {len(holds)} positions")

        if sells:
            print(f"\nPositions to SELL:")
            for symbol in sorted(sells):
                print(f"  - {symbol}")

        if buys:
            print(f"\nPositions to BUY:")
            for symbol in sorted(buys):
                weight = new_portfolio[new_portfolio['symbol'] == symbol]['weight'].values[0]
                print(f"  + {symbol} ({weight:.2%})")

        # Turnover calculation
        turnover = (len(sells) + len(buys)) / len(current_symbols)
        print(f"\nPortfolio turnover: {turnover:.1%}")

    except FileNotFoundError:
        logger.error(f"Current holdings file not found: {current_holdings_csv}")
    except Exception as e:
        logger.error(f"Error comparing portfolios: {e}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate portfolio recommendations for live trading"
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
        '--no-llm',
        action='store_true',
        help='Disable LLM enhancement (baseline only)'
    )
    parser.add_argument(
        '--tilt-factor',
        type=float,
        default=5.0,
        help='LLM weight tilting factor (default: 5.0)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default=None,
        choices=['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo', 'gpt-4o-2024-11-20', 'o1-mini'],
        help='LLM model to use (default: gpt-4o-mini from config)'
    )
    parser.add_argument(
        '--current-holdings',
        type=str,
        default=None,
        help='Path to CSV with current holdings for trade comparison'
    )

    args = parser.parse_args()

    # Generate portfolio
    portfolio = generate_current_portfolio(
        portfolio_size=args.size,
        base_weighting=args.weighting,
        use_llm=not args.no_llm,
        tilt_factor=args.tilt_factor,
        model=args.model,
        export_csv=True
    )

    if portfolio is None:
        logger.error("Failed to generate portfolio")
        return

    # Compare with current holdings if provided
    if args.current_holdings:
        compare_with_current(portfolio, args.current_holdings)

    logger.info("\n" + "="*70)
    logger.info("PORTFOLIO GENERATION COMPLETE")
    logger.info("="*70)


if __name__ == "__main__":
    main()

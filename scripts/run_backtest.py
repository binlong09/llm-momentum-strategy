"""
Run Backtest Script
Executes backtests with various configurations.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import argparse
from datetime import datetime
from loguru import logger

from src.backtesting import Backtester


def main():
    parser = argparse.ArgumentParser(description="Run momentum strategy backtest")

    parser.add_argument(
        '--start-date',
        type=str,
        default='2023-01-01',
        help='Backtest start date (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--end-date',
        type=str,
        default='2023-12-31',
        help='Backtest end date (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--weighting',
        type=str,
        default='all',
        choices=['equal', 'value', 'momentum', 'all'],
        help='Weighting scheme to test'
    )

    parser.add_argument(
        '--capital',
        type=float,
        default=1000000,
        help='Initial capital ($)'
    )

    parser.add_argument(
        '--frequency',
        type=str,
        default='monthly',
        choices=['daily', 'weekly', 'monthly'],
        help='Rebalancing frequency'
    )

    parser.add_argument(
        '--validation',
        action='store_true',
        help='Use validation period from config'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Use test period from config'
    )

    parser.add_argument(
        '--export',
        type=str,
        help='Export results to CSV file'
    )

    args = parser.parse_args()

    # Initialize backtester
    backtester = Backtester()

    # Set date range
    if args.validation:
        start_date = backtester.validation_start
        end_date = backtester.validation_end
        logger.info("Using VALIDATION period from config")
    elif args.test:
        start_date = backtester.test_start
        end_date = backtester.test_end
        logger.info("Using TEST period from config")
    else:
        start_date = args.start_date
        end_date = args.end_date

    logger.info(f"Backtest period: {start_date} to {end_date}")
    logger.info(f"Initial capital: ${args.capital:,.0f}")
    logger.info(f"Rebalancing: {args.frequency}")

    # Run backtest(s)
    if args.weighting == 'all':
        # Compare all strategies
        logger.info("\nComparing all weighting schemes...")
        results = backtester.compare_strategies(
            start_date,
            end_date,
            weighting_schemes=['equal', 'value', 'momentum']
        )

        # Export if requested
        if args.export:
            logger.info(f"\nExporting results to {args.export}...")
            export_comparison(results, args.export)

    else:
        # Single strategy
        logger.info(f"\nRunning {args.weighting.upper()} weighting backtest...")
        result = backtester.run_backtest(
            start_date,
            end_date,
            weighting_scheme=args.weighting,
            initial_capital=args.capital,
            rebalance_freq=args.frequency
        )

        # Display results
        display_result(result)

        # Export if requested
        if args.export:
            logger.info(f"\nExporting results to {args.export}...")
            export_result(result, args.export)


def display_result(result):
    """Display detailed backtest result."""
    from src.backtesting.metrics import PerformanceMetrics

    metrics_calc = PerformanceMetrics()

    print("\n" + "="*70)
    print(f"BACKTEST RESULTS: {result.strategy_name.upper()}")
    print("="*70)

    print(f"\nPeriod: {result.start_date} to {result.end_date}")
    print(f"Number of Rebalances: {len(result.rebalance_dates)}")

    if result.turnover_history:
        avg_turnover = sum(result.turnover_history) / len(result.turnover_history)
        print(f"Average Turnover: {avg_turnover:.2%}")

    print(f"Total Transaction Costs: ${result.total_transaction_costs:,.2f}")
    print(f"\nFinal Portfolio Value: ${result.portfolio_value.iloc[-1]:,.2f}")

    # Print metrics report
    report = metrics_calc.format_metrics_report(result.metrics)
    print("\n" + report)

    # Show final holdings
    if result.holdings_history:
        print("\nFinal Holdings (Top 10):")
        final_holdings = result.holdings_history[-1].nlargest(10, 'weight')
        print(final_holdings[['symbol', 'weight', 'momentum_return']].to_string(index=False))


def export_result(result, filename):
    """Export single result to CSV."""
    import pandas as pd

    # Create results DataFrame
    export_df = pd.DataFrame({
        'date': result.portfolio_value.index,
        'portfolio_value': result.portfolio_value.values,
        'daily_return': result.daily_returns.values
    })

    export_df.to_csv(filename, index=False)
    logger.success(f"Exported results to {filename}")


def export_comparison(results, filename):
    """Export comparison results to CSV."""
    import pandas as pd

    # Combine portfolio values from all strategies
    combined = pd.DataFrame()

    for strategy, result in results.items():
        combined[f'{strategy}_value'] = result.portfolio_value
        combined[f'{strategy}_return'] = result.daily_returns

    combined.to_csv(filename)
    logger.success(f"Exported comparison to {filename}")


if __name__ == "__main__":
    main()

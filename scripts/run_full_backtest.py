"""
Full Backtest Runner
Runs validation (2019-2023) and test (2024+) backtests for baseline and enhanced strategies.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from datetime import datetime
from loguru import logger
import json

from src.backtesting import EnhancedBacktester, BacktestResult


def save_results(results: dict, period_name: str, output_dir: Path):
    """Save backtest results to disk."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save summary metrics
    summary = {}
    for strategy_name, result in results.items():
        summary[strategy_name] = {
            'final_value': float(result.portfolio_value.iloc[-1]),
            'total_return': float(result.metrics.get('total_return', 0)),
            'annual_return': float(result.metrics.get('annual_return', 0)),
            'sharpe_ratio': float(result.metrics.get('sharpe_ratio', 0)),
            'sortino_ratio': float(result.metrics.get('sortino_ratio', 0)),
            'max_drawdown': float(result.metrics.get('max_drawdown', 0)),
            'calmar_ratio': float(result.metrics.get('calmar_ratio', 0)),
            'annual_volatility': float(result.metrics.get('annual_volatility', 0)),
            'avg_turnover': float(np.mean(result.turnover_history)) if result.turnover_history else 0,
            'total_transaction_costs': float(result.total_transaction_costs),
            'num_rebalances': len(result.rebalance_dates)
        }

    summary_file = output_dir / f"{period_name}_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved summary to {summary_file}")

    # Save detailed results for each strategy
    for strategy_name, result in results.items():
        strategy_dir = output_dir / strategy_name
        strategy_dir.mkdir(exist_ok=True)

        # Portfolio values over time
        result.portfolio_value.to_csv(strategy_dir / f"{period_name}_portfolio_value.csv")

        # Daily returns
        result.daily_returns.to_csv(strategy_dir / f"{period_name}_daily_returns.csv")

        # Holdings history (last rebalance only to save space)
        if result.holdings_history:
            final_holdings = result.holdings_history[-1]
            final_holdings.to_csv(strategy_dir / f"{period_name}_final_holdings.csv", index=False)

        logger.info(f"Saved {strategy_name} results to {strategy_dir}")


def print_comparison(results: dict, period_name: str):
    """Print detailed comparison of baseline vs enhanced."""
    if 'baseline' not in results or 'enhanced' not in results:
        logger.warning("Cannot compare: missing baseline or enhanced results")
        return

    baseline = results['baseline']
    enhanced = results['enhanced']

    print(f"\n{'='*80}")
    print(f"PERIOD: {period_name}")
    print(f"{'='*80}\n")

    # Performance table
    comparison_data = []
    for name, result in [('Baseline', baseline), ('Enhanced', enhanced)]:
        metrics = result.metrics
        comparison_data.append({
            'Strategy': name,
            'Total Return': f"{metrics.get('total_return', 0):.2%}",
            'Annual Return': f"{metrics.get('annual_return', 0):.2%}",
            'Volatility': f"{metrics.get('annual_volatility', 0):.2%}",
            'Sharpe Ratio': f"{metrics.get('sharpe_ratio', 0):.2f}",
            'Sortino Ratio': f"{metrics.get('sortino_ratio', 0):.2f}",
            'Max Drawdown': f"{metrics.get('max_drawdown', 0):.2%}",
            'Calmar Ratio': f"{metrics.get('calmar_ratio', 0):.2f}",
            'Avg Turnover': f"{np.mean(result.turnover_history):.2%}" if result.turnover_history else "N/A"
        })

    comparison_df = pd.DataFrame(comparison_data)
    print(comparison_df.to_string(index=False))

    # Calculate improvement
    baseline_metrics = baseline.metrics
    enhanced_metrics = enhanced.metrics

    improvement = {
        'Annual Return': enhanced_metrics.get('annual_return', 0) - baseline_metrics.get('annual_return', 0),
        'Sharpe Ratio': enhanced_metrics.get('sharpe_ratio', 0) - baseline_metrics.get('sharpe_ratio', 0),
        'Sortino Ratio': enhanced_metrics.get('sortino_ratio', 0) - baseline_metrics.get('sortino_ratio', 0),
        'Max Drawdown': enhanced_metrics.get('max_drawdown', 0) - baseline_metrics.get('max_drawdown', 0),
        'Calmar Ratio': enhanced_metrics.get('calmar_ratio', 0) - baseline_metrics.get('calmar_ratio', 0)
    }

    print(f"\n{'='*80}")
    print("IMPROVEMENT (Enhanced - Baseline):")
    print(f"  Annual Return:    {improvement['Annual Return']:>+8.2%}")
    print(f"  Sharpe Ratio:     {improvement['Sharpe Ratio']:>+8.2f}")
    print(f"  Sortino Ratio:    {improvement['Sortino Ratio']:>+8.2f}")
    print(f"  Max Drawdown:     {improvement['Max Drawdown']:>+8.2%} (lower is better)")
    print(f"  Calmar Ratio:     {improvement['Calmar Ratio']:>+8.2f}")
    print(f"{'='*80}\n")

    # Statistical significance
    try:
        from scipy import stats

        baseline_returns = baseline.daily_returns.values
        enhanced_returns = enhanced.daily_returns.values

        # T-test
        t_stat, p_value = stats.ttest_ind(enhanced_returns, baseline_returns)

        print("Statistical Significance (t-test):")
        print(f"  t-statistic: {t_stat:.4f}")
        print(f"  p-value: {p_value:.4f}")

        if p_value < 0.01:
            print(f"  ✓✓ Highly significant at 99% confidence level")
        elif p_value < 0.05:
            print(f"  ✓ Significant at 95% confidence level")
        elif p_value < 0.10:
            print(f"  ~ Marginally significant at 90% confidence level")
        else:
            print(f"  → Not statistically significant (p > 0.10)")

        # Information Ratio (excess return / tracking error)
        excess_returns = enhanced_returns - baseline_returns
        ir = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252) if excess_returns.std() > 0 else 0
        print(f"\nInformation Ratio: {ir:.2f}")
        print(f"  (Measures risk-adjusted excess return vs baseline)")

    except ImportError:
        logger.warning("scipy not installed, skipping statistical tests")
    except Exception as e:
        logger.warning(f"Error in significance test: {e}")


def run_validation_backtest(backtester: EnhancedBacktester):
    """Run validation period backtest (2019-2023)."""
    logger.info("\n" + "="*80)
    logger.info("VALIDATION PERIOD BACKTEST: 2019-2023")
    logger.info("="*80 + "\n")

    start_date = "2019-01-01"
    end_date = "2023-12-31"

    results = backtester.compare_baseline_vs_enhanced(
        start_date=start_date,
        end_date=end_date,
        base_weighting='equal',
        tilt_factor=5.0
    )

    return results


def run_test_backtest(backtester: EnhancedBacktester):
    """Run test period backtest (2024+)."""
    logger.info("\n" + "="*80)
    logger.info("TEST PERIOD BACKTEST: 2024-Present")
    logger.info("="*80 + "\n")

    start_date = "2024-01-01"
    end_date = datetime.now().strftime('%Y-%m-%d')

    results = backtester.compare_baseline_vs_enhanced(
        start_date=start_date,
        end_date=end_date,
        base_weighting='equal',
        tilt_factor=5.0
    )

    return results


def main():
    """Run full backtest suite."""
    logger.info("="*80)
    logger.info("FULL BACKTEST SUITE")
    logger.info("="*80)
    logger.info("Testing LLM-Enhanced Momentum Strategy")
    logger.info("Following 'ChatGPT in Systematic Investing' paper methodology\n")

    # Initialize backtester
    logger.info("Initializing EnhancedBacktester...")
    backtester = EnhancedBacktester()

    if not backtester.llm_enabled:
        logger.error("LLM not enabled, cannot run enhanced backtest")
        logger.info("Please set OPENAI_API_KEY environment variable")
        return

    # Create output directory
    output_dir = Path("results/backtests") / datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Results will be saved to: {output_dir}\n")

    # Run validation backtest (2019-2023)
    try:
        logger.info("Starting validation period backtest...")
        validation_results = run_validation_backtest(backtester)

        print_comparison(validation_results, "VALIDATION (2019-2023)")
        save_results(validation_results, "validation", output_dir)

    except Exception as e:
        logger.error(f"Validation backtest failed: {e}")
        import traceback
        traceback.print_exc()

    # Run test backtest (2024+)
    try:
        logger.info("\nStarting test period backtest...")
        test_results = run_test_backtest(backtester)

        print_comparison(test_results, "TEST (2024-Present)")
        save_results(test_results, "test", output_dir)

    except Exception as e:
        logger.error(f"Test backtest failed: {e}")
        import traceback
        traceback.print_exc()

    # Final summary
    logger.info("\n" + "="*80)
    logger.info("BACKTEST SUITE COMPLETE")
    logger.info("="*80)
    logger.info(f"Results saved to: {output_dir}")
    logger.info("\nNext steps:")
    logger.info("  1. Review performance metrics")
    logger.info("  2. Analyze holdings history")
    logger.info("  3. Compare with paper's results")
    logger.info("  4. Tune hyperparameters if needed")


if __name__ == "__main__":
    main()

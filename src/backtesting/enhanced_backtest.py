"""
Enhanced Backtesting Engine with LLM Support
Extends baseline backtester to support LLM-enhanced strategies.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import Dict, List, Optional, Tuple
import yaml

from .backtest import Backtester, BacktestResult
from .metrics import PerformanceMetrics
from src.strategy import EnhancedSelector, EnhancedPortfolioConstructor


class EnhancedBacktester(Backtester):
    """
    Enhanced backtester with LLM support.

    Features:
    - LLM-based stock re-ranking
    - Weight tilting with η factor
    - Baseline vs enhanced comparison
    - All baseline features (transaction costs, rebalancing, etc.)
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize enhanced backtester.

        Args:
            config_path: Path to strategy configuration
        """
        super().__init__(config_path)

        # Initialize enhanced components
        try:
            self.enhanced_selector = EnhancedSelector(config_path)
            self.enhanced_constructor = EnhancedPortfolioConstructor(config_path)
            self.llm_enabled = self.enhanced_selector.llm_enabled
            logger.info(f"EnhancedBacktester initialized: LLM enabled = {self.llm_enabled}")
        except Exception as e:
            logger.error(f"Failed to initialize enhanced components: {e}")
            self.llm_enabled = False
            raise

        # Extract LLM parameters
        strategy_config = self.config.get('strategy', {})
        self.weight_tilt_factor = strategy_config.get('weight_tilt_factor', 5.0)
        self.final_portfolio_size = strategy_config.get('final_portfolio_size', 50)
        self.rerank_method = 'llm_only'  # Default re-ranking method

    def run_backtest_enhanced(
        self,
        start_date: str,
        end_date: str,
        base_weighting: str = 'equal',
        use_llm_tilting: bool = True,
        tilt_factor: Optional[float] = None,
        rerank_method: Optional[str] = None,
        initial_capital: Optional[float] = None,
        rebalance_freq: Optional[str] = None,
        final_portfolio_size: Optional[int] = None
    ) -> BacktestResult:
        """
        Run backtest with LLM-enhanced strategy.

        Args:
            start_date: Backtest start date (YYYY-MM-DD)
            end_date: Backtest end date (YYYY-MM-DD)
            base_weighting: Base weighting scheme ('equal', 'value', 'momentum')
            use_llm_tilting: Whether to apply LLM weight tilting
            tilt_factor: η parameter for tilting
            rerank_method: LLM re-ranking method
            initial_capital: Starting capital
            rebalance_freq: Rebalancing frequency
            final_portfolio_size: Number of stocks in final portfolio

        Returns:
            BacktestResult with performance data
        """
        if not self.llm_enabled:
            logger.warning("LLM not enabled, falling back to baseline backtest")
            return self.run_backtest(
                start_date, end_date,
                weighting_scheme=base_weighting,
                initial_capital=initial_capital,
                rebalance_freq=rebalance_freq
            )

        if tilt_factor is None:
            tilt_factor = self.weight_tilt_factor
        if rerank_method is None:
            rerank_method = self.rerank_method
        if initial_capital is None:
            initial_capital = self.initial_capital
        if rebalance_freq is None:
            rebalance_freq = self.rebalance_freq
        if final_portfolio_size is None:
            final_portfolio_size = self.final_portfolio_size

        strategy_name = f"{base_weighting}_llm"
        if use_llm_tilting:
            strategy_name += f"_eta{tilt_factor}"

        logger.info(
            f"Running ENHANCED backtest: {start_date} to {end_date}\n"
            f"  Base weighting: {base_weighting}\n"
            f"  LLM tilting: {use_llm_tilting}\n"
            f"  Tilt factor η: {tilt_factor}\n"
            f"  Re-rank method: {rerank_method}\n"
            f"  Portfolio size: {final_portfolio_size}\n"
            f"  Capital: ${initial_capital:,.0f}"
        )

        # Get rebalance dates
        rebalance_dates = self.get_rebalance_dates(start_date, end_date, rebalance_freq)

        if not rebalance_dates:
            logger.error("No rebalance dates generated")
            return BacktestResult(
                strategy_name=strategy_name,
                start_date=start_date,
                end_date=end_date
            )

        # Fetch universe data
        logger.info("Fetching universe data...")
        universe = self.data_manager.get_universe()[:300]  # Use top 300 for coverage

        logger.info(f"Fetching price data for {len(universe)} stocks...")
        all_price_data = self.data_manager.get_prices(
            universe,
            use_cache=True,
            show_progress=True
        )

        # Initialize tracking variables
        portfolio_value = initial_capital
        current_holdings = pd.DataFrame()
        current_weights = pd.Series(dtype=float)

        portfolio_values = []
        holdings_history = []
        turnover_history = []
        total_transaction_costs = 0.0

        # Simulate each rebalance period
        for i, rebal_date in enumerate(rebalance_dates):
            rebal_date_str = rebal_date.strftime('%Y-%m-%d')
            logger.info(f"\n{'='*60}")
            logger.info(f"Rebalance {i+1}/{len(rebalance_dates)}: {rebal_date_str}")
            logger.info(f"{'='*60}")

            # Enhanced selection with LLM
            selected_stocks, metadata = self.enhanced_selector.select_for_portfolio_enhanced(
                all_price_data,
                end_date=rebal_date_str,
                apply_quality_filter=True,
                final_count=final_portfolio_size,
                rerank_method=rerank_method
            )

            if selected_stocks.empty:
                logger.warning(f"No stocks selected for {rebal_date_str}, holding cash")
                portfolio_values.append({
                    'date': rebal_date,
                    'portfolio_value': portfolio_value
                })
                continue

            # Construct enhanced portfolio with LLM tilting
            new_portfolio = self.enhanced_constructor.construct_portfolio_enhanced(
                selected_stocks,
                price_data=all_price_data,
                base_weighting=base_weighting,
                use_llm_tilting=use_llm_tilting,
                tilt_factor=tilt_factor,
                end_date=rebal_date_str
            )

            if new_portfolio.empty:
                logger.warning(f"Portfolio construction failed for {rebal_date_str}")
                portfolio_values.append({
                    'date': rebal_date,
                    'portfolio_value': portfolio_value
                })
                continue

            # Calculate turnover
            new_weights = new_portfolio.set_index('symbol')['weight']

            if not current_weights.empty:
                turnover = self.calculate_turnover(current_weights, new_weights)
                turnover_history.append(turnover)

                # Transaction costs
                txn_cost = self.calculate_transaction_costs(turnover, portfolio_value)
                total_transaction_costs += txn_cost
                portfolio_value -= txn_cost

                logger.info(
                    f"Turnover: {turnover:.2%}, Transaction cost: ${txn_cost:,.2f}, "
                    f"New value: ${portfolio_value:,.2f}"
                )
            else:
                # First rebalance
                turnover = 1.0
                turnover_history.append(turnover)
                txn_cost = self.calculate_transaction_costs(turnover, portfolio_value)
                total_transaction_costs += txn_cost
                portfolio_value -= txn_cost
                logger.info(f"Initial investment, Transaction cost: ${txn_cost:,.2f}")

            # Update holdings
            current_holdings = new_portfolio.copy()
            current_holdings['portfolio_value'] = portfolio_value
            current_holdings['position_value'] = current_holdings['weight'] * portfolio_value
            current_weights = new_weights

            holdings_history.append(current_holdings)

            # Track portfolio value at rebalance
            portfolio_values.append({
                'date': rebal_date,
                'portfolio_value': portfolio_value
            })

            # Calculate returns until next rebalance
            if i < len(rebalance_dates) - 1:
                next_rebal_date = rebalance_dates[i + 1]
            else:
                next_rebal_date = pd.to_datetime(end_date)

            # Get daily returns for holding period
            period_returns = self._calculate_holding_period_returns(
                current_holdings,
                all_price_data,
                rebal_date,
                next_rebal_date
            )

            if period_returns is not None and not period_returns.empty:
                for date, ret in period_returns.items():
                    portfolio_value *= (1 + ret)
                    portfolio_values.append({
                        'date': date,
                        'portfolio_value': portfolio_value
                    })

            logger.info(f"End of period value: ${portfolio_value:,.2f}")

        # Create results DataFrame
        portfolio_df = pd.DataFrame(portfolio_values)
        portfolio_df['date'] = pd.to_datetime(portfolio_df['date'], utc=True)
        portfolio_df['date'] = portfolio_df['date'].dt.tz_localize(None)
        portfolio_df = portfolio_df.set_index('date').sort_index()

        # Calculate daily returns
        daily_returns = portfolio_df['portfolio_value'].pct_change().fillna(0)

        # Calculate metrics
        metrics = self.metrics_calculator.calculate_all_metrics(
            daily_returns,
            portfolio_df['portfolio_value']
        )

        # Create result
        result = BacktestResult(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            portfolio_value=portfolio_df['portfolio_value'],
            daily_returns=daily_returns,
            holdings_history=holdings_history,
            rebalance_dates=[d.strftime('%Y-%m-%d') for d in rebalance_dates],
            turnover_history=turnover_history,
            metrics=metrics,
            total_transaction_costs=total_transaction_costs
        )

        logger.success(
            f"Enhanced backtest complete: Final value ${portfolio_value:,.2f}, "
            f"Total return {metrics.get('total_return', 0):.2%}, "
            f"Sharpe ratio {metrics.get('sharpe_ratio', 0):.2f}"
        )

        return result

    def compare_baseline_vs_enhanced(
        self,
        start_date: str,
        end_date: str,
        base_weighting: str = 'equal',
        tilt_factor: float = 5.0
    ) -> Dict[str, BacktestResult]:
        """
        Compare baseline vs LLM-enhanced strategy.

        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            base_weighting: Base weighting scheme
            tilt_factor: η parameter for tilting

        Returns:
            Dictionary with 'baseline' and 'enhanced' results
        """
        logger.info(f"\n{'='*70}")
        logger.info("BASELINE vs ENHANCED COMPARISON")
        logger.info(f"{'='*70}")

        results = {}

        # Run baseline
        logger.info(f"\nRunning BASELINE {base_weighting} strategy...")
        baseline_result = self.run_backtest(
            start_date,
            end_date,
            weighting_scheme=base_weighting
        )
        results['baseline'] = baseline_result

        # Run enhanced
        if self.llm_enabled:
            logger.info(f"\nRunning ENHANCED {base_weighting} + LLM strategy...")
            enhanced_result = self.run_backtest_enhanced(
                start_date,
                end_date,
                base_weighting=base_weighting,
                use_llm_tilting=True,
                tilt_factor=tilt_factor
            )
            results['enhanced'] = enhanced_result
        else:
            logger.warning("LLM not enabled, skipping enhanced backtest")

        # Display comparison
        self._display_baseline_enhanced_comparison(results)

        return results

    def _display_baseline_enhanced_comparison(
        self,
        results: Dict[str, BacktestResult]
    ):
        """Display comparison of baseline vs enhanced results."""
        if 'baseline' not in results or 'enhanced' not in results:
            logger.warning("Cannot compare: missing baseline or enhanced results")
            return

        baseline = results['baseline']
        enhanced = results['enhanced']

        logger.info(f"\n{'='*70}")
        logger.info("PERFORMANCE COMPARISON")
        logger.info(f"{'='*70}\n")

        # Create comparison table
        comparison_data = []

        for name, result in [('Baseline', baseline), ('Enhanced', enhanced)]:
            metrics = result.metrics
            comparison_data.append({
                'Strategy': name,
                'Total Return': f"{metrics.get('total_return', 0):.2%}",
                'Annual Return': f"{metrics.get('annual_return', 0):.2%}",
                'Volatility': f"{metrics.get('annual_volatility', 0):.2%}",
                'Sharpe Ratio': f"{metrics.get('sharpe_ratio', 0):.2f}",
                'Max Drawdown': f"{metrics.get('max_drawdown', 0):.2%}",
                'Avg Turnover': f"{np.mean(result.turnover_history):.2%}" if result.turnover_history else "N/A"
            })

        comparison_df = pd.DataFrame(comparison_data)
        print("\n" + comparison_df.to_string(index=False))

        # Calculate improvement
        baseline_metrics = baseline.metrics
        enhanced_metrics = enhanced.metrics

        improvement = {
            'Return': (enhanced_metrics.get('annual_return', 0) -
                      baseline_metrics.get('annual_return', 0)),
            'Sharpe': (enhanced_metrics.get('sharpe_ratio', 0) -
                      baseline_metrics.get('sharpe_ratio', 0)),
            'Drawdown': (enhanced_metrics.get('max_drawdown', 0) -
                        baseline_metrics.get('max_drawdown', 0))
        }

        print(f"\n{'='*70}")
        print("IMPROVEMENT (Enhanced - Baseline):")
        print(f"  Annual Return:  {improvement['Return']:>+7.2%}")
        print(f"  Sharpe Ratio:   {improvement['Sharpe']:>+7.2f}")
        print(f"  Max Drawdown:   {improvement['Drawdown']:>+7.2%} (lower is better)")
        print(f"{'='*70}")

        # Statistical significance (simple t-test)
        try:
            from scipy import stats

            baseline_returns = baseline.daily_returns.values
            enhanced_returns = enhanced.daily_returns.values

            t_stat, p_value = stats.ttest_ind(enhanced_returns, baseline_returns)

            print(f"\nStatistical Significance:")
            print(f"  t-statistic: {t_stat:.4f}")
            print(f"  p-value: {p_value:.4f}")

            if p_value < 0.05:
                print(f"  ✓ Significant improvement at 95% confidence level")
            else:
                print(f"  → Not statistically significant (p > 0.05)")

        except ImportError:
            logger.warning("scipy not installed, skipping statistical significance test")
        except Exception as e:
            logger.warning(f"Error in significance test: {e}")


def main():
    """Test enhanced backtester."""
    logger.info("Testing Enhanced Backtester")
    logger.info("="*70)

    # Initialize
    backtester = EnhancedBacktester()

    # Test period (shorter for testing)
    start_date = "2024-01-01"
    end_date = "2024-10-31"

    # Compare baseline vs enhanced
    logger.info(f"\nRunning comparison: {start_date} to {end_date}")

    results = backtester.compare_baseline_vs_enhanced(
        start_date,
        end_date,
        base_weighting='equal',
        tilt_factor=5.0
    )

    # Show detailed results
    if 'enhanced' in results:
        enhanced = results['enhanced']

        logger.info(f"\n{'='*70}")
        logger.info("ENHANCED STRATEGY DETAILS")
        logger.info(f"{'='*70}")

        print(f"\nFinal Portfolio Value: ${enhanced.portfolio_value.iloc[-1]:,.2f}")
        print(f"Total Transaction Costs: ${enhanced.total_transaction_costs:,.2f}")
        print(f"Number of Rebalances: {len(enhanced.rebalance_dates)}")

        if enhanced.holdings_history:
            print(f"\nFinal Holdings ({len(enhanced.holdings_history[-1])} positions):")
            final_holdings = enhanced.holdings_history[-1].nlargest(10, 'weight')

            # Display with LLM scores if available
            if 'llm_score' in final_holdings.columns:
                print(final_holdings[['symbol', 'weight', 'llm_score', 'momentum_return']].to_string(index=False))
            else:
                print(final_holdings[['symbol', 'weight', 'momentum_return']].to_string(index=False))


if __name__ == "__main__":
    main()

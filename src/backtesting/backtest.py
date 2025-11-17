"""
Backtesting Engine
Simulates momentum strategy performance on historical data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import yaml

from src.data import DataManager
from src.strategy import StockSelector, PortfolioConstructor
from .metrics import PerformanceMetrics


@dataclass
class BacktestResult:
    """Container for backtest results."""

    strategy_name: str
    start_date: str
    end_date: str

    # Portfolio time series
    portfolio_value: pd.Series = field(default_factory=pd.Series)
    daily_returns: pd.Series = field(default_factory=pd.Series)
    holdings_history: List[pd.DataFrame] = field(default_factory=list)

    # Rebalancing info
    rebalance_dates: List[str] = field(default_factory=list)
    turnover_history: List[float] = field(default_factory=list)

    # Performance metrics
    metrics: Dict = field(default_factory=dict)

    # Transaction costs
    total_transaction_costs: float = 0.0

    def __repr__(self):
        return (
            f"BacktestResult(strategy='{self.strategy_name}', "
            f"period={self.start_date} to {self.end_date}, "
            f"final_value={self.portfolio_value.iloc[-1]:.2f})"
        )


class Backtester:
    """
    Backtesting engine for momentum strategies.

    Features:
    - Monthly rebalancing
    - Transaction cost modeling
    - Multiple weighting schemes
    - Performance metrics calculation
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize backtester.

        Args:
            config_path: Path to strategy configuration
        """
        self.config = self._load_config(config_path)

        # Initialize components
        self.data_manager = DataManager(config_path)
        self.selector = StockSelector(config_path)
        self.portfolio_constructor = PortfolioConstructor(config_path)
        self.metrics_calculator = PerformanceMetrics()

        # Extract backtest parameters
        backtest_config = self.config.get('backtesting', {})
        self.validation_start = backtest_config.get('validation_start', '2019-10-01')
        self.validation_end = backtest_config.get('validation_end', '2023-12-31')
        self.test_start = backtest_config.get('test_start', '2024-01-01')
        self.test_end = backtest_config.get('test_end', '2025-03-31')

        # Strategy parameters
        strategy_config = self.config.get('strategy', {})
        self.rebalance_freq = strategy_config.get('rebalancing_frequency', 'monthly')
        self.transaction_cost_bps = strategy_config.get('transaction_cost_bps', 2)

        # Initial capital
        self.initial_capital = 1000000  # $1M default

        logger.info(
            f"Backtester initialized: {self.rebalance_freq} rebalancing, "
            f"{self.transaction_cost_bps} bps transaction costs"
        )

    def _load_config(self, path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def get_rebalance_dates(
        self,
        start_date: str,
        end_date: str,
        frequency: str = 'monthly'
    ) -> List[pd.Timestamp]:
        """
        Generate rebalancing dates.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            frequency: 'daily', 'weekly', or 'monthly'

        Returns:
            List of rebalance dates
        """
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)

        if frequency == 'monthly':
            # First business day of each month
            dates = pd.date_range(start, end, freq='MS')  # Month start
        elif frequency == 'weekly':
            # Every Monday
            dates = pd.date_range(start, end, freq='W-MON')
        elif frequency == 'daily':
            # Every business day
            dates = pd.date_range(start, end, freq='B')
        else:
            raise ValueError(f"Unknown frequency: {frequency}")

        # Convert to list
        rebalance_dates = [d for d in dates if start <= d <= end]

        logger.info(f"Generated {len(rebalance_dates)} rebalance dates ({frequency})")
        return rebalance_dates

    def calculate_turnover(
        self,
        old_weights: pd.Series,
        new_weights: pd.Series
    ) -> float:
        """
        Calculate portfolio turnover.

        Turnover = sum(|new_weight - old_weight|) / 2

        Args:
            old_weights: Previous portfolio weights (symbol -> weight)
            new_weights: New portfolio weights (symbol -> weight)

        Returns:
            Turnover as fraction (0 to 1)
        """
        # Align symbols
        all_symbols = set(old_weights.index) | set(new_weights.index)

        old_aligned = pd.Series(0.0, index=all_symbols)
        old_aligned.update(old_weights)

        new_aligned = pd.Series(0.0, index=all_symbols)
        new_aligned.update(new_weights)

        # Calculate turnover
        turnover = (new_aligned - old_aligned).abs().sum() / 2.0

        return turnover

    def calculate_transaction_costs(
        self,
        turnover: float,
        portfolio_value: float,
        cost_bps: Optional[int] = None
    ) -> float:
        """
        Calculate transaction costs.

        Args:
            turnover: Portfolio turnover (0 to 1)
            portfolio_value: Current portfolio value
            cost_bps: Cost in basis points (default: from config)

        Returns:
            Transaction cost in dollars
        """
        if cost_bps is None:
            cost_bps = self.transaction_cost_bps

        # Cost = turnover * portfolio_value * (bps / 10000)
        cost = turnover * portfolio_value * (cost_bps / 10000.0)

        return cost

    def run_backtest(
        self,
        start_date: str,
        end_date: str,
        weighting_scheme: str = 'equal',
        initial_capital: Optional[float] = None,
        rebalance_freq: Optional[str] = None
    ) -> BacktestResult:
        """
        Run backtest for baseline momentum strategy.

        Args:
            start_date: Backtest start date (YYYY-MM-DD)
            end_date: Backtest end date (YYYY-MM-DD)
            weighting_scheme: 'equal', 'value', or 'momentum'
            initial_capital: Starting capital (default: $1M)
            rebalance_freq: Rebalancing frequency (default: from config)

        Returns:
            BacktestResult with performance data
        """
        if initial_capital is None:
            initial_capital = self.initial_capital
        if rebalance_freq is None:
            rebalance_freq = self.rebalance_freq

        logger.info(
            f"Running backtest: {start_date} to {end_date}, "
            f"weighting={weighting_scheme}, capital=${initial_capital:,.0f}"
        )

        # Get rebalance dates
        rebalance_dates = self.get_rebalance_dates(start_date, end_date, rebalance_freq)

        if not rebalance_dates:
            logger.error("No rebalance dates generated")
            return BacktestResult(
                strategy_name=f"{weighting_scheme}_momentum",
                start_date=start_date,
                end_date=end_date
            )

        # Fetch universe data once
        logger.info("Fetching universe data...")
        universe = self.data_manager.get_universe()[:300]  # Use top 300 for better coverage

        # Fetch all price data
        logger.info(f"Fetching price data for {len(universe)} stocks...")
        all_price_data = self.data_manager.get_prices(
            universe,
            use_cache=True,
            show_progress=True
        )

        # Initialize tracking variables
        portfolio_value = initial_capital
        current_holdings = pd.DataFrame()  # Empty initially
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

            # Select stocks based on momentum
            selected_stocks, metadata = self.selector.select_for_portfolio(
                all_price_data,
                end_date=rebal_date_str,
                apply_quality_filter=True
            )

            if selected_stocks.empty:
                logger.warning(f"No stocks selected for {rebal_date_str}, holding cash")
                portfolio_values.append({
                    'date': rebal_date,
                    'portfolio_value': portfolio_value
                })
                continue

            # Construct portfolio with specified weighting
            new_portfolio = self.portfolio_constructor.construct_portfolio(
                selected_stocks,
                price_data=all_price_data,
                weighting_scheme=weighting_scheme,
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

                # Calculate transaction costs
                txn_cost = self.calculate_transaction_costs(turnover, portfolio_value)
                total_transaction_costs += txn_cost
                portfolio_value -= txn_cost

                logger.info(
                    f"Turnover: {turnover:.2%}, Transaction cost: ${txn_cost:,.2f}, "
                    f"New portfolio value: ${portfolio_value:,.2f}"
                )
            else:
                # First rebalance - 100% turnover (going from cash to fully invested)
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
                # Last period - go to end_date
                next_rebal_date = pd.to_datetime(end_date)

            # Get daily returns for holding period
            period_returns = self._calculate_holding_period_returns(
                current_holdings,
                all_price_data,
                rebal_date,
                next_rebal_date
            )

            if period_returns is not None and not period_returns.empty:
                # Update portfolio value based on returns
                for date, ret in period_returns.items():
                    portfolio_value *= (1 + ret)
                    portfolio_values.append({
                        'date': date,
                        'portfolio_value': portfolio_value
                    })

            logger.info(f"End of period portfolio value: ${portfolio_value:,.2f}")

        # Create results DataFrame
        portfolio_df = pd.DataFrame(portfolio_values)
        portfolio_df['date'] = pd.to_datetime(portfolio_df['date'], utc=True)
        # Convert to timezone-naive for simpler handling
        portfolio_df['date'] = portfolio_df['date'].dt.tz_localize(None)
        portfolio_df = portfolio_df.set_index('date').sort_index()

        # Calculate daily returns
        daily_returns = portfolio_df['portfolio_value'].pct_change().fillna(0)

        # Calculate metrics
        metrics = self.metrics_calculator.calculate_all_metrics(
            daily_returns,
            portfolio_df['portfolio_value']
        )

        # Create result object
        result = BacktestResult(
            strategy_name=f"{weighting_scheme}_momentum",
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
            f"Backtest complete: Final value ${portfolio_value:,.2f}, "
            f"Total return {metrics.get('total_return', 0):.2%}, "
            f"Sharpe ratio {metrics.get('sharpe_ratio', 0):.2f}"
        )

        return result

    def _calculate_holding_period_returns(
        self,
        holdings: pd.DataFrame,
        price_data: Dict[str, pd.DataFrame],
        start_date: pd.Timestamp,
        end_date: pd.Timestamp
    ) -> Optional[pd.Series]:
        """
        Calculate daily portfolio returns during holding period.

        Args:
            holdings: Current portfolio holdings with weights
            price_data: Dictionary of price DataFrames
            start_date: Holding period start
            end_date: Holding period end

        Returns:
            Series of daily portfolio returns (date -> return)
        """
        if holdings.empty or 'symbol' not in holdings.columns or 'weight' not in holdings.columns:
            return None

        # Get daily returns for each holding
        stock_returns = {}

        for _, row in holdings.iterrows():
            symbol = row['symbol']
            weight = row['weight']

            if symbol not in price_data or price_data[symbol] is None:
                continue

            df = price_data[symbol]

            # Ensure date comparisons handle timezones
            start_date_cmp = start_date
            end_date_cmp = end_date

            if df.index.tz is not None:
                # Make dates timezone-aware to match df.index
                if not hasattr(start_date, 'tz') or start_date.tz is None:
                    start_date_cmp = start_date.tz_localize(df.index.tz)
                if not hasattr(end_date, 'tz') or end_date.tz is None:
                    end_date_cmp = end_date.tz_localize(df.index.tz)

            # Filter date range
            mask = (df.index > start_date_cmp) & (df.index <= end_date_cmp)
            period_data = df[mask]

            if period_data.empty or 'adjusted_close' not in period_data.columns:
                continue

            # Calculate daily returns
            daily_rets = period_data['adjusted_close'].pct_change().fillna(0)
            stock_returns[symbol] = daily_rets * weight

        if not stock_returns:
            return None

        # Combine into DataFrame
        returns_df = pd.DataFrame(stock_returns)

        # Portfolio return = sum of weighted stock returns
        portfolio_returns = returns_df.sum(axis=1)

        return portfolio_returns

    def compare_strategies(
        self,
        start_date: str,
        end_date: str,
        weighting_schemes: List[str] = None
    ) -> Dict[str, BacktestResult]:
        """
        Compare multiple weighting schemes.

        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            weighting_schemes: List of schemes to compare

        Returns:
            Dictionary mapping scheme name to BacktestResult
        """
        if weighting_schemes is None:
            weighting_schemes = ['equal', 'value', 'momentum']

        logger.info(f"\n{'='*70}")
        logger.info("STRATEGY COMPARISON")
        logger.info(f"{'='*70}")

        results = {}

        for scheme in weighting_schemes:
            logger.info(f"\nRunning {scheme.upper()} weighting...")
            result = self.run_backtest(
                start_date,
                end_date,
                weighting_scheme=scheme
            )
            results[scheme] = result

        # Display comparison
        self._display_comparison(results)

        return results

    def _display_comparison(self, results: Dict[str, BacktestResult]):
        """Display comparison of strategy results."""
        logger.info(f"\n{'='*70}")
        logger.info("STRATEGY COMPARISON RESULTS")
        logger.info(f"{'='*70}\n")

        comparison_data = []

        for scheme, result in results.items():
            metrics = result.metrics
            comparison_data.append({
                'Strategy': scheme.capitalize(),
                'Total Return': f"{metrics.get('total_return', 0):.2%}",
                'Annual Return': f"{metrics.get('annual_return', 0):.2%}",
                'Volatility': f"{metrics.get('annual_volatility', 0):.2%}",
                'Sharpe Ratio': f"{metrics.get('sharpe_ratio', 0):.2f}",
                'Max Drawdown': f"{metrics.get('max_drawdown', 0):.2%}",
                'Avg Turnover': f"{np.mean(result.turnover_history):.2%}" if result.turnover_history else "N/A"
            })

        comparison_df = pd.DataFrame(comparison_data)
        print("\n" + comparison_df.to_string(index=False))
        print("\n" + "="*70)


def main():
    """Test backtester."""
    # Initialize
    backtester = Backtester()

    # Run backtest for validation period (shorter for testing)
    logger.info("Running validation backtest...")

    # Use shorter period for testing (1 year)
    start_date = "2023-01-01"
    end_date = "2023-12-31"

    # Compare strategies
    results = backtester.compare_strategies(
        start_date,
        end_date,
        weighting_schemes=['equal', 'value', 'momentum']
    )

    # Show detailed results for best strategy
    best_strategy = max(
        results.items(),
        key=lambda x: x[1].metrics.get('sharpe_ratio', -999)
    )

    logger.info(f"\n{'='*70}")
    logger.info(f"BEST STRATEGY: {best_strategy[0].upper()}")
    logger.info(f"{'='*70}")

    result = best_strategy[1]
    print(f"\nFinal Portfolio Value: ${result.portfolio_value.iloc[-1]:,.2f}")
    print(f"Total Transaction Costs: ${result.total_transaction_costs:,.2f}")
    print(f"Number of Rebalances: {len(result.rebalance_dates)}")

    if result.holdings_history:
        print(f"\nFinal Holdings ({len(result.holdings_history[-1])} positions):")
        final_holdings = result.holdings_history[-1].nlargest(10, 'weight')
        print(final_holdings[['symbol', 'weight', 'momentum_return']].to_string(index=False))


if __name__ == "__main__":
    main()

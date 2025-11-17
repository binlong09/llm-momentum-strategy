"""
Momentum Strategy Signals
Calculates momentum signals and ranks stocks for the baseline strategy.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger
from typing import List, Dict, Optional, Tuple
import yaml


class MomentumCalculator:
    """
    Calculates momentum signals for stock selection.

    Based on the paper's optimal parameters:
    - 12-month lookback period
    - Exclude most recent month to avoid short-term reversal
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize momentum calculator.

        Args:
            config_path: Path to strategy configuration
        """
        self.config = self._load_config(config_path)

        # Extract momentum parameters
        strategy_config = self.config.get('strategy', {})
        self.lookback_months = strategy_config.get('momentum_lookback_months', 12)
        self.exclude_recent = strategy_config.get('momentum_exclude_recent_month', True)
        self.top_percentile = strategy_config.get('top_percentile', 0.20)

        logger.info(
            f"MomentumCalculator initialized: {self.lookback_months}-month lookback, "
            f"exclude_recent={self.exclude_recent}, top_percentile={self.top_percentile}"
        )

    def _load_config(self, path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def calculate_momentum(
        self,
        price_df: pd.DataFrame,
        end_date: Optional[datetime] = None,
        lookback_months: Optional[int] = None,
        exclude_recent_month: Optional[bool] = None
    ) -> Optional[float]:
        """
        Calculate momentum return for a single stock.

        Args:
            price_df: DataFrame with price data (must have 'adjusted_close' and datetime index)
            end_date: End date for calculation (default: last date in data)
            lookback_months: Override default lookback period
            exclude_recent_month: Override default recent month exclusion

        Returns:
            Momentum return (as decimal) or None if insufficient data
        """
        if price_df is None or price_df.empty:
            return None

        if 'adjusted_close' not in price_df.columns:
            logger.warning("Price data missing 'adjusted_close' column")
            return None

        # Use config defaults if not specified
        if lookback_months is None:
            lookback_months = self.lookback_months
        if exclude_recent_month is None:
            exclude_recent_month = self.exclude_recent

        try:
            # Ensure index is datetime
            if not isinstance(price_df.index, pd.DatetimeIndex):
                price_df.index = pd.to_datetime(price_df.index)

            # Sort by date
            price_df = price_df.sort_index()

            # Determine end date
            if end_date is None:
                end_date = price_df.index[-1]
            else:
                # Ensure end_date is timezone-aware if price_df.index is timezone-aware
                if price_df.index.tz is not None:
                    # Make end_date timezone-aware to match price_df.index
                    if not hasattr(end_date, 'tz') or end_date.tz is None:
                        end_date = pd.to_datetime(end_date).tz_localize(price_df.index.tz)
                    else:
                        end_date = end_date.tz_convert(price_df.index.tz)

                # Get data up to end_date
                price_df = price_df[price_df.index <= end_date]

            if len(price_df) == 0:
                return None

            # Calculate momentum end date (exclude recent month if configured)
            if exclude_recent_month:
                # Skip most recent month (~21 trading days)
                # Get the date 21 trading days before end_date
                if len(price_df) < 22:
                    return None
                momentum_end_idx = -22
                momentum_end = price_df.index[momentum_end_idx]
            else:
                momentum_end = price_df.index[-1]

            # Calculate momentum start date (lookback_months before momentum_end)
            # Approximate: 21 trading days per month
            lookback_days = lookback_months * 21

            # Get data before momentum_end
            data_before_end = price_df[price_df.index <= momentum_end]

            if len(data_before_end) < lookback_days:
                # Not enough history, use what we have
                if len(data_before_end) < 21:  # Need at least 1 month
                    return None
                start_price = data_before_end['adjusted_close'].iloc[0]
            else:
                # Get price from lookback_days ago
                start_idx = len(data_before_end) - lookback_days
                start_price = data_before_end['adjusted_close'].iloc[start_idx]

            end_price = data_before_end['adjusted_close'].iloc[-1]

            # Calculate return
            if start_price <= 0 or end_price <= 0:
                return None

            momentum_return = (end_price / start_price) - 1

            return momentum_return

        except Exception as e:
            logger.debug(f"Error calculating momentum: {e}")
            return None

    def calculate_momentum_universe(
        self,
        price_data: Dict[str, pd.DataFrame],
        end_date: Optional[str] = None,
        min_data_days: int = 252
    ) -> pd.DataFrame:
        """
        Calculate momentum for all stocks in universe.

        Args:
            price_data: Dictionary mapping symbols to price DataFrames
            end_date: End date for calculation (YYYY-MM-DD)
            min_data_days: Minimum days of data required

        Returns:
            DataFrame with columns: symbol, momentum_return, rank, percentile
        """
        # Convert end_date to datetime
        if end_date:
            end_dt = pd.to_datetime(end_date)
        else:
            end_dt = None

        momentum_results = []

        for symbol, price_df in price_data.items():
            if price_df is None or price_df.empty:
                continue

            # Check minimum data requirement
            if len(price_df) < min_data_days:
                logger.debug(f"{symbol}: Insufficient data ({len(price_df)} < {min_data_days} days)")
                continue

            # Calculate momentum
            momentum = self.calculate_momentum(price_df, end_date=end_dt)

            if momentum is not None:
                momentum_results.append({
                    'symbol': symbol,
                    'momentum_return': momentum
                })

        # Create DataFrame
        if not momentum_results:
            logger.warning("No momentum results calculated")
            return pd.DataFrame()

        momentum_df = pd.DataFrame(momentum_results)

        # Sort by momentum (descending)
        momentum_df = momentum_df.sort_values('momentum_return', ascending=False)

        # Add ranking
        momentum_df['rank'] = range(1, len(momentum_df) + 1)
        momentum_df['percentile'] = momentum_df['rank'] / len(momentum_df)

        # Reset index
        momentum_df = momentum_df.reset_index(drop=True)

        logger.success(f"Calculated momentum for {len(momentum_df)} stocks")

        return momentum_df

    def select_top_momentum(
        self,
        momentum_df: pd.DataFrame,
        top_percentile: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Select top momentum stocks by percentile.

        Args:
            momentum_df: DataFrame from calculate_momentum_universe
            top_percentile: Percentile threshold (default from config)

        Returns:
            Filtered DataFrame with top stocks
        """
        if momentum_df.empty:
            return momentum_df

        if top_percentile is None:
            top_percentile = self.top_percentile

        # Select stocks in top percentile
        selected = momentum_df[momentum_df['percentile'] <= top_percentile].copy()

        logger.info(
            f"Selected {len(selected)} stocks from top {top_percentile*100:.0f}% "
            f"(out of {len(momentum_df)} total)"
        )

        return selected

    def get_momentum_summary(self, momentum_df: pd.DataFrame) -> Dict:
        """
        Get summary statistics for momentum distribution.

        Args:
            momentum_df: DataFrame from calculate_momentum_universe

        Returns:
            Dictionary with summary statistics
        """
        if momentum_df.empty:
            return {
                'count': 0,
                'mean': None,
                'median': None,
                'std': None,
                'min': None,
                'max': None
            }

        returns = momentum_df['momentum_return']

        return {
            'count': len(momentum_df),
            'mean': returns.mean(),
            'median': returns.median(),
            'std': returns.std(),
            'min': returns.min(),
            'max': returns.max(),
            'top_decile_mean': momentum_df[momentum_df['percentile'] <= 0.1]['momentum_return'].mean(),
            'bottom_decile_mean': momentum_df[momentum_df['percentile'] >= 0.9]['momentum_return'].mean()
        }

    def analyze_momentum_spread(
        self,
        momentum_df: pd.DataFrame,
        num_quantiles: int = 10
    ) -> pd.DataFrame:
        """
        Analyze momentum spread across quantiles.

        Args:
            momentum_df: DataFrame from calculate_momentum_universe
            num_quantiles: Number of quantiles (default: 10 for deciles)

        Returns:
            DataFrame with quantile analysis
        """
        if momentum_df.empty:
            return pd.DataFrame()

        # Create quantiles
        momentum_df['quantile'] = pd.qcut(
            momentum_df['rank'],
            q=num_quantiles,
            labels=range(1, num_quantiles + 1)
        )

        # Calculate statistics per quantile
        quantile_stats = momentum_df.groupby('quantile').agg({
            'momentum_return': ['mean', 'median', 'std', 'count'],
            'symbol': lambda x: list(x)[:5]  # Sample symbols
        }).round(4)

        quantile_stats.columns = ['mean_return', 'median_return', 'std_return', 'count', 'sample_symbols']

        return quantile_stats

    def get_momentum_winners_losers(
        self,
        momentum_df: pd.DataFrame,
        n: int = 10
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get top winners and losers by momentum.

        Args:
            momentum_df: DataFrame from calculate_momentum_universe
            n: Number of stocks to return

        Returns:
            Tuple of (winners_df, losers_df)
        """
        if momentum_df.empty:
            return pd.DataFrame(), pd.DataFrame()

        winners = momentum_df.head(n)[['symbol', 'momentum_return', 'rank']].copy()
        losers = momentum_df.tail(n)[['symbol', 'momentum_return', 'rank']].copy()

        return winners, losers


def main():
    """Test momentum calculator."""
    from src.data import DataManager

    # Initialize
    dm = DataManager()
    calc = MomentumCalculator()

    # Get sample stocks
    logger.info("Fetching data for sample stocks...")
    symbols = dm.get_universe()[:20]  # First 20 stocks
    price_data = dm.get_prices(symbols, use_cache=True, show_progress=False)

    # Calculate momentum
    logger.info("\nCalculating momentum...")
    momentum_df = calc.calculate_momentum_universe(price_data)

    # Show results
    if not momentum_df.empty:
        logger.info(f"\nMomentum calculated for {len(momentum_df)} stocks")

        # Summary stats
        summary = calc.get_momentum_summary(momentum_df)
        logger.info(f"\nSummary Statistics:")
        logger.info(f"  Mean return: {summary['mean']:.2%}")
        logger.info(f"  Median return: {summary['median']:.2%}")
        logger.info(f"  Std dev: {summary['std']:.2%}")
        logger.info(f"  Range: {summary['min']:.2%} to {summary['max']:.2%}")

        # Top winners and losers
        winners, losers = calc.get_momentum_winners_losers(momentum_df, n=5)

        logger.info("\nTop 5 Winners:")
        print(winners.to_string(index=False))

        logger.info("\nTop 5 Losers:")
        print(losers.to_string(index=False))

        # Select top percentile
        top_stocks = calc.select_top_momentum(momentum_df)
        logger.info(f"\nTop {calc.top_percentile*100:.0f}% ({len(top_stocks)} stocks):")
        print(top_stocks.head(10)[['symbol', 'momentum_return', 'rank']].to_string(index=False))

    else:
        logger.warning("No momentum data calculated")


if __name__ == "__main__":
    main()

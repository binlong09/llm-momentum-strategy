"""
Stock Selection Module
Implements stock ranking and selection for portfolio construction.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import List, Dict, Optional, Tuple
import yaml

from .momentum import MomentumCalculator


class StockSelector:
    """
    Selects stocks for portfolio based on momentum signals.

    Pipeline:
    1. Calculate momentum for universe
    2. Filter by data quality
    3. Rank by momentum
    4. Select top percentile
    5. Return selected stocks with metadata
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize stock selector.

        Args:
            config_path: Path to strategy configuration
        """
        self.config = self._load_config(config_path)

        # Initialize momentum calculator
        self.momentum_calc = MomentumCalculator(config_path)

        # Extract selection parameters
        strategy_config = self.config.get('strategy', {})
        self.top_percentile = strategy_config.get('top_percentile', 0.20)
        self.final_portfolio_size = strategy_config.get('final_portfolio_size', 50)

        # Data quality thresholds
        self.min_price = 5.0  # Minimum stock price to avoid penny stocks
        self.min_volume = 100000  # Minimum daily volume
        self.min_data_days = 252  # Minimum 1 year of data

        logger.info(
            f"StockSelector initialized: top_percentile={self.top_percentile}, "
            f"final_portfolio_size={self.final_portfolio_size}"
        )

    def _load_config(self, path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def filter_by_data_quality(
        self,
        price_data: Dict[str, pd.DataFrame],
        min_price: Optional[float] = None,
        min_volume: Optional[int] = None,
        min_days: Optional[int] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Filter stocks by data quality criteria.

        Args:
            price_data: Dictionary mapping symbols to price DataFrames
            min_price: Minimum stock price (default: self.min_price)
            min_volume: Minimum average daily volume (default: self.min_volume)
            min_days: Minimum days of data (default: self.min_data_days)

        Returns:
            Filtered dictionary of price data
        """
        if min_price is None:
            min_price = self.min_price
        if min_volume is None:
            min_volume = self.min_volume
        if min_days is None:
            min_days = self.min_data_days

        filtered = {}
        filtered_out = {
            'price': [],
            'volume': [],
            'data': [],
            'missing': []
        }

        for symbol, df in price_data.items():
            if df is None or df.empty:
                filtered_out['missing'].append(symbol)
                continue

            # Check data length
            if len(df) < min_days:
                filtered_out['data'].append(symbol)
                logger.debug(f"{symbol}: Insufficient data ({len(df)} < {min_days} days)")
                continue

            # Check price
            if 'adjusted_close' in df.columns:
                recent_price = df['adjusted_close'].iloc[-1]
                if recent_price < min_price:
                    filtered_out['price'].append(symbol)
                    logger.debug(f"{symbol}: Price too low (${recent_price:.2f} < ${min_price})")
                    continue

            # Check volume
            if 'volume' in df.columns:
                avg_volume = df['volume'].tail(21).mean()  # Last month average
                if avg_volume < min_volume:
                    filtered_out['volume'].append(symbol)
                    logger.debug(f"{symbol}: Volume too low ({avg_volume:.0f} < {min_volume})")
                    continue

            # Passed all filters
            filtered[symbol] = df

        # Log summary
        total_filtered = sum(len(v) for v in filtered_out.values())
        logger.info(
            f"Data quality filter: {len(filtered)} passed, {total_filtered} filtered out "
            f"(price: {len(filtered_out['price'])}, volume: {len(filtered_out['volume'])}, "
            f"data: {len(filtered_out['data'])}, missing: {len(filtered_out['missing'])})"
        )

        return filtered

    def rank_by_momentum(
        self,
        price_data: Dict[str, pd.DataFrame],
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Calculate momentum and rank stocks.

        Args:
            price_data: Dictionary mapping symbols to price DataFrames
            end_date: End date for momentum calculation (YYYY-MM-DD)

        Returns:
            DataFrame with momentum rankings
        """
        logger.info(f"Calculating momentum for {len(price_data)} stocks...")

        momentum_df = self.momentum_calc.calculate_momentum_universe(
            price_data,
            end_date=end_date,
            min_data_days=self.min_data_days
        )

        if momentum_df.empty:
            logger.warning("No momentum data calculated")
            return momentum_df

        logger.success(
            f"Calculated momentum for {len(momentum_df)} stocks "
            f"(range: {momentum_df['momentum_return'].min():.2%} to "
            f"{momentum_df['momentum_return'].max():.2%})"
        )

        return momentum_df

    def select_top_stocks(
        self,
        momentum_df: pd.DataFrame,
        top_percentile: Optional[float] = None,
        max_stocks: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Select top stocks by momentum.

        Args:
            momentum_df: DataFrame with momentum rankings
            top_percentile: Percentile threshold (default: self.top_percentile)
            max_stocks: Maximum number of stocks to select (optional)

        Returns:
            DataFrame with selected stocks
        """
        if momentum_df.empty:
            return momentum_df

        if top_percentile is None:
            top_percentile = self.top_percentile

        # Select top percentile
        selected = momentum_df[momentum_df['percentile'] <= top_percentile].copy()

        # Limit to max_stocks if specified
        if max_stocks and len(selected) > max_stocks:
            selected = selected.head(max_stocks)

        logger.info(
            f"Selected {len(selected)} stocks from top {top_percentile*100:.0f}% "
            f"(out of {len(momentum_df)} total)"
        )

        return selected

    def select_for_portfolio(
        self,
        price_data: Dict[str, pd.DataFrame],
        end_date: Optional[str] = None,
        apply_quality_filter: bool = True
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Complete selection pipeline for portfolio construction.

        Args:
            price_data: Dictionary mapping symbols to price DataFrames
            end_date: End date for calculations (YYYY-MM-DD)
            apply_quality_filter: Whether to apply data quality filters

        Returns:
            Tuple of (selected_stocks_df, metadata_dict)
        """
        metadata = {
            'selection_date': end_date or datetime.now().strftime('%Y-%m-%d'),
            'initial_universe': len(price_data),
            'after_quality_filter': 0,
            'after_momentum_calc': 0,
            'final_selected': 0
        }

        # Step 1: Data quality filter
        if apply_quality_filter:
            logger.info("Step 1: Applying data quality filters...")
            filtered_data = self.filter_by_data_quality(price_data)
            metadata['after_quality_filter'] = len(filtered_data)
        else:
            filtered_data = price_data
            metadata['after_quality_filter'] = len(price_data)

        if not filtered_data:
            logger.error("No stocks passed quality filter")
            return pd.DataFrame(), metadata

        # Step 2: Calculate momentum and rank
        logger.info("Step 2: Calculating momentum and ranking...")
        momentum_df = self.rank_by_momentum(filtered_data, end_date)
        metadata['after_momentum_calc'] = len(momentum_df)

        if momentum_df.empty:
            logger.error("No momentum data calculated")
            return pd.DataFrame(), metadata

        # Step 3: Select top stocks
        logger.info("Step 3: Selecting top momentum stocks...")
        selected = self.select_top_stocks(
            momentum_df,
            top_percentile=self.top_percentile
        )
        metadata['final_selected'] = len(selected)

        # Add selection metadata to DataFrame
        selected['selection_date'] = metadata['selection_date']

        logger.success(
            f"Selection complete: {metadata['final_selected']} stocks selected "
            f"from {metadata['initial_universe']} initial universe"
        )

        return selected, metadata

    def get_selection_summary(
        self,
        selected_df: pd.DataFrame,
        metadata: Dict
    ) -> str:
        """
        Generate human-readable selection summary.

        Args:
            selected_df: DataFrame with selected stocks
            metadata: Selection metadata

        Returns:
            Formatted summary string
        """
        if selected_df.empty:
            return "No stocks selected"

        summary_parts = [
            "=" * 60,
            "Stock Selection Summary",
            "=" * 60,
            f"Selection Date: {metadata['selection_date']}",
            "",
            "Pipeline Results:",
            f"  Initial Universe:      {metadata['initial_universe']:>6} stocks",
            f"  After Quality Filter:  {metadata['after_quality_filter']:>6} stocks",
            f"  After Momentum Calc:   {metadata['after_momentum_calc']:>6} stocks",
            f"  Final Selected:        {metadata['final_selected']:>6} stocks",
            "",
            "Momentum Statistics:",
            f"  Mean Return:   {selected_df['momentum_return'].mean():>7.2%}",
            f"  Median Return: {selected_df['momentum_return'].median():>7.2%}",
            f"  Min Return:    {selected_df['momentum_return'].min():>7.2%}",
            f"  Max Return:    {selected_df['momentum_return'].max():>7.2%}",
            "",
            f"Top 10 Selected Stocks:",
        ]

        # Add top 10 stocks
        top_10 = selected_df.head(10)[['symbol', 'momentum_return', 'rank']]
        for _, row in top_10.iterrows():
            summary_parts.append(
                f"  {row['rank']:>3}. {row['symbol']:<6s}  {row['momentum_return']:>7.2%}"
            )

        summary_parts.append("=" * 60)

        return "\n".join(summary_parts)

    def export_selection(
        self,
        selected_df: pd.DataFrame,
        output_path: str,
        include_metadata: bool = True
    ):
        """
        Export selected stocks to CSV.

        Args:
            selected_df: DataFrame with selected stocks
            output_path: Path to save CSV
            include_metadata: Whether to include all columns
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if include_metadata:
            selected_df.to_csv(output_file, index=False)
        else:
            # Export minimal columns
            selected_df[['symbol', 'momentum_return', 'rank']].to_csv(
                output_file, index=False
            )

        logger.info(f"Exported {len(selected_df)} selected stocks to {output_file}")


def main():
    """Test stock selector."""
    from src.data import DataManager

    # Initialize
    dm = DataManager()
    selector = StockSelector()

    # Get universe (use subset for testing)
    logger.info("Fetching universe...")
    universe = dm.get_universe()[:50]  # First 50 stocks for testing

    logger.info(f"Fetching price data for {len(universe)} stocks...")
    price_data = dm.get_prices(universe, use_cache=True, show_progress=False)

    # Run selection pipeline
    logger.info("\n" + "="*60)
    logger.info("Running Stock Selection Pipeline")
    logger.info("="*60)

    selected_df, metadata = selector.select_for_portfolio(
        price_data,
        apply_quality_filter=True
    )

    # Display results
    if not selected_df.empty:
        summary = selector.get_selection_summary(selected_df, metadata)
        print("\n" + summary)

        # Show sector distribution if available
        logger.info("\nFetching sector information...")
        universe_info = dm.get_universe_info()
        if 'sector' in universe_info.columns:
            # Add sector info to selected stocks
            selected_with_sector = selected_df.merge(
                universe_info[['symbol', 'sector']],
                on='symbol',
                how='left'
            )

            sector_dist = selected_with_sector['sector'].value_counts()
            logger.info("\nSector Distribution:")
            print(sector_dist.to_string())

    else:
        logger.warning("No stocks selected")


if __name__ == "__main__":
    main()
